"""WP-H / H9 Kademe B — store.py'nin TEK YAZIM KAPISI.

Kademe B'nin sözleşmesi: "kalan TÜM JSON yazımlarına merkezî atomik-rename + flock (store.py'de
tek kapı)". Bu dosya o cümlenin ÖLÇÜLEBİLİR hâlidir — üç iddia, üçü de davranış düzeyinde:

  1. İÇERİK KORUNUR: kapıdan geçen yazım, geçmeyen yazımla BİREBİR aynı baytları bırakır
     (migrasyon davranışı değiştirmemeli — yoksa "sertleştirme" adı altında sessiz bir regresyon).
  2. ATOMİKLİK: yazım ortasında düşülürse HEDEF dosya dokunulmamış kalır; yarım içerik geçici
     dosyada ölür, deftere HİÇ girmez. (Kapının varlık sebebi budur: okuyucu ya eskiyi ya yeniyi
     görür, asla yarısını.)
  3. FLOCK SÜREÇLER ARASINDA GERÇEKTEN TUTULUR: aynı adı kilitleyen BAŞKA BİR SÜREÇ varken yazım
     BEKLER. Süreç-içi bir testle bunu kanıtlamak İMKÂNSIZDIR — `flock` aynı süreçte ikinci kez
     anında geçer — bu yüzden gerçek bir alt süreç kullanılır.

events.jsonl'a DOKUNULMAZ: append-only JSONL doğru biçimdir ve `append_jsonl` bilerek kapının
dışındadır (O_APPEND yazımı zaten sıralıdır; oraya flock koymak sıcak olay yolunu serileştirirdi).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
import threading
import time

import pytest

from meridian import store


# =================================================================================================
# 1) DAVRANIŞ KORUMA — kapıdan geçen içerik, doğrudan yazımla BİREBİR
# =================================================================================================
def test_write_text_icerik_birebir(sandbox_state):
    """`store.write_text` ile `Path.write_text` aynı baytları bırakır (davranış migrasyonu YOK)."""
    metin = "# Dersler\n- ölçülmeyen None kalır\n- ünicode: ıöüşğç ✓\n"
    store.write_text("lessons.md", metin)
    beklenen = sandbox_state / "beklenen.md"
    beklenen.write_text(metin)
    assert (sandbox_state / "lessons.md").read_bytes() == beklenen.read_bytes()


def test_write_text_ustune_yazar_ve_kirpar(sandbox_state):
    """İkinci yazım birincinin ARTIĞINI bırakmaz — kısa içerik uzun içeriği tamamen değiştirir."""
    store.write_text("defter.txt", "A" * 5000)
    store.write_text("defter.txt", "kısa")
    assert (sandbox_state / "defter.txt").read_text() == "kısa"


def test_write_json_icerik_ve_bicim_korunur(sandbox_state):
    """JSON kapısı indent=2 biçimini ve sanitize davranışını korur (kilit eklenmesi biçimi bozmaz)."""
    obj = {"b": 1, "a": [1, 2, {"c": None}]}
    store.write_json("k.json", obj)
    ham = (sandbox_state / "k.json").read_text()
    assert json.loads(ham) == obj
    assert ham == json.dumps(obj, indent=2)          # biçim BİREBİR — indent kayması yok


def test_write_jsonl_satir_basina_bir_kayit(sandbox_state):
    rows = [{"i": 1}, {"i": 2}, {"i": 3}]
    store.write_jsonl("d.jsonl", rows)
    satirlar = (sandbox_state / "d.jsonl").read_text().splitlines()
    assert [json.loads(s) for s in satirlar] == rows


def test_kapidan_gecen_yazim_gecici_dosya_birakmaz(sandbox_state):
    """BAŞARILI yazımdan sonra dizinde `.tmp` artığı KALMAZ (mkstemp sızıntısı sessiz disk yer)."""
    store.write_text("a.md", "x")
    store.write_json("b.json", {"y": 1})
    store.write_jsonl("c.jsonl", [{"z": 1}])
    assert [p.name for p in sandbox_state.iterdir() if p.name.endswith(".tmp")] == []


# =================================================================================================
# 2) ATOMİKLİK — yarım yazım HEDEFE ULAŞMAZ
# =================================================================================================
@pytest.mark.parametrize("yazan,yuk", [
    ("write_text", "YENİ" * 100),
    ("write_json", {"yeni": True}),
])
def test_replace_duserse_hedef_DOKUNULMAMIŞ_kalir(sandbox_state, monkeypatch, yazan, yuk):
    """`os.replace` anında düşülürse eski defter AYNEN durur — yarım içerik görünmez.

    Bu, kapının tek satırlık gerekçesidir: düz `open(path,'w')` olsaydı dosya bu noktada çoktan
    KIRPILMIŞ olurdu ve okuyucu boş/yarım bir defter görürdü."""
    ad = "defter.json"
    store.write_text(ad, "ESKİ İÇERİK")
    onceki = (sandbox_state / ad).read_bytes()

    def patlat(src, dst):
        raise OSError("simüle: replace düştü")

    monkeypatch.setattr(store.os, "replace", patlat)
    with pytest.raises(OSError):
        getattr(store, yazan)(ad, yuk)

    assert (sandbox_state / ad).read_bytes() == onceki          # hedef DOKUNULMADI
    assert [p.name for p in sandbox_state.iterdir() if p.name.endswith(".tmp")] == []  # tmp temizlendi


def test_yazim_ortasinda_dusme_hedefi_bozmaz(sandbox_state, monkeypatch):
    """Yazımın KENDİSİ (fdopen/write) düşerse de hedef eski hâlinde kalır — yarım bayt sızmaz."""
    ad = "yarim.txt"
    store.write_text(ad, "TAM")
    gercek_fdopen = store.os.fdopen

    def yarim_yaz(fd, *a, **kw):
        fh = gercek_fdopen(fd, *a, **kw)
        fh.write("YARIM-")
        raise OSError("simüle: disk doldu")

    monkeypatch.setattr(store.os, "fdopen", yarim_yaz)
    with pytest.raises(OSError):
        store.write_text(ad, "YENİ TAM İÇERİK")
    assert (sandbox_state / ad).read_text() == "TAM"


def test_gecici_dosya_hedefle_AYNI_dizinde_acilir(sandbox_state, monkeypatch):
    """`os.replace` yalnız AYNI dosya sisteminde atomiktir — tmp hedefin dizininde doğmalı.

    /tmp'de açılıp taşınsaydı yeniden adlandırma sessizce KOPYALA+SİL'e dönerdi (farklı aygıt) ve
    atomiklik iddiası, tam da güvenilmesi gereken yerde, ölçülmeden çökerdi."""
    gorulen: list[str] = []
    gercek = store.tempfile.mkstemp

    def izle(*a, **kw):
        gorulen.append(kw.get("dir") or (a[2] if len(a) > 2 else None))
        return gercek(*a, **kw)

    monkeypatch.setattr(store.tempfile, "mkstemp", izle)
    hedef = sandbox_state / "altdizin" / "x.json"
    store.write_json(str(hedef), {"a": 1})
    assert gorulen and os.path.realpath(gorulen[0]) == os.path.realpath(str(hedef.parent))


# =================================================================================================
# 3) FLOCK — kilit KAPININ İÇİNDE ve SÜREÇLER ARASINDA
# =================================================================================================
def test_yazarlar_kilidi_kapinin_icinde_alir(sandbox_state, monkeypatch):
    """`write_json`/`write_jsonl`/`write_text` yazım anında ADIN kilidini TUTUYOR olmalı.

    Ölçüm noktası `_atomic_write`tır: oraya varıldığında kilit derinliği >0 olmalı. Çağıranın
    kilit alması ARTIK GEREKMİYOR — Kademe B'nin tam iddiası bu."""
    derinlikler: dict[str, int] = {}
    gercek = store._atomic_write

    def izle(path, data):
        derinlikler[os.path.basename(str(path))] = store.file_lock(ad_of[str(path)])._depth
        return gercek(path, data)

    ad_of = {}
    for ad, cagri in (("a.json", lambda: store.write_json("a.json", {"x": 1})),
                      ("b.jsonl", lambda: store.write_jsonl("b.jsonl", [{"x": 1}])),
                      ("c.md", lambda: store.write_text("c.md", "x"))):
        ad_of[str(sandbox_state / ad)] = ad
        monkeypatch.setattr(store, "_atomic_write", izle)
        cagri()
    assert derinlikler == {"a.json": 1, "b.jsonl": 1, "c.md": 1}


def test_update_json_zinciri_yeniden_girisli(sandbox_state):
    """`update_json` (kilidi ALMIŞ) → `write_json` (aynı adı yeniden alır) KİLİTLENMEZ.

    Kilidi kapıya indirmenin tek gerçek riski buydu: sıcak yol zaten kilitli çağırıyor. RLock+
    derinlik sayacı olmasaydı bu test SONSUZA KADAR asılırdı."""
    store.write_json("p.json", {"n": 0})
    store.update_json("p.json", lambda d: (d.__setitem__("n", d["n"] + 1), True)[1])
    assert store.read_json("p.json") == {"n": 1}
    assert store.file_lock("p.json")._depth == 0            # kilit bırakıldı, sızmadı


@pytest.mark.parametrize("yazan,yuk", [
    ("write_json", {"a": 1}),
    ("write_text", "metin"),
])
def test_flock_SURECLER_ARASI_gercekten_bekletir(sandbox_state, yazan, yuk):
    """BAŞKA BİR SÜREÇ adı kilitliyken yazım BEKLER; kilit bırakılınca tamamlanır.

    Kademe B'nin çekirdek iddiası budur ve süreç-içi bir testle KANITLANAMAZ: `flock` aynı süreçte
    ikinci kez anında geçer. Bu yüzden kilidi gerçek bir alt süreç tutar."""
    ad = "yaris.json"
    kilit_dosyasi = sandbox_state / ".locks" / (ad + ".lock")
    kilit_dosyasi.parent.mkdir(parents=True, exist_ok=True)
    hazir = sandbox_state / "hazir.flag"

    cocuk = subprocess.Popen([sys.executable, "-c", textwrap.dedent(f"""
        import fcntl, os, time
        fd = os.open({str(kilit_dosyasi)!r}, os.O_RDWR | os.O_CREAT, 0o644)
        fcntl.flock(fd, fcntl.LOCK_EX)
        open({str(hazir)!r}, "w").close()
        time.sleep(1.5)                 # kilidi TUT
        fcntl.flock(fd, fcntl.LOCK_UN)
    """)])
    try:
        son = time.monotonic() + 10
        while not hazir.exists() and time.monotonic() < son:
            time.sleep(0.01)
        assert hazir.exists(), "alt süreç kilidi alamadı — ölçüm yapılamadı"

        bitti = threading.Event()
        hata: list[BaseException] = []

        def yaz():
            try:
                getattr(store, yazan)(ad, yuk)
            except BaseException as e:      # noqa: BLE001 — iplik hatası ana teste taşınır
                hata.append(e)
            finally:
                bitti.set()

        t = threading.Thread(target=yaz, daemon=True)
        t.start()
        # KİLİT TUTULURKEN: yazım tamamlanmamalı. 0.5 sn, 1.5 sn'lik tutuşun İÇİNDE kalır.
        assert not bitti.wait(0.5), "kilit tutulurken yazım tamamlandı — flock ETKİSİZ"
        # KİLİT BIRAKILINCA: tamamlanmalı.
        assert bitti.wait(10), "kilit bırakıldıktan sonra yazım tamamlanmadı"
        assert not hata, f"yazım iplikte düştü: {hata}"
        assert (sandbox_state / ad).exists()
    finally:
        cocuk.wait(timeout=15)


def test_append_jsonl_kapinin_DISINDA_kalir(sandbox_state):
    """events.jsonl sınıfı: `append_jsonl` append-only KALIR ve dosyayı BAŞTAN yazmaz.

    Mezar taşı testi — biri 'tutarlılık' adına append'i de `write_jsonl`e çevirirse olay defteri
    her yazımda tamamen yeniden yazılır (O(n) sıcak yol + çökmede TÜM defterin riski)."""
    store.append_jsonl("events.jsonl", {"i": 1})
    inode1 = (sandbox_state / "events.jsonl").stat().st_ino
    store.append_jsonl("events.jsonl", {"i": 2})
    st = (sandbox_state / "events.jsonl").stat()
    assert st.st_ino == inode1, "append yolu dosyayı YER DEĞİŞTİRDİ — artık append-only değil"
    assert [json.loads(s) for s in (sandbox_state / "events.jsonl").read_text().splitlines()] \
        == [{"i": 1}, {"i": 2}]
