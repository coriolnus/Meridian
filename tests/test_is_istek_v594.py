"""v594 — 'şimdi çalıştır' (spec 2026-09-29 §3.6): kadrodan türeyen iş listesi, 15 dk tavanı, istek dosyası, .path birimleri.

Brief'in dokuz çivisine ek (Görev 2 uygulayıcısı, 2026-09-29):
  * SÜREÇLER ARASI KİLİT (brief: "iki süreç aynı anda `is_iste('karne')` → tam bir kabul, bir tavan").
    Yarış penceresi ZAMANLAMAYA bırakılmaz: iki `spawn` süreci önce bir başlangıç bariyerinde buluşur,
    sonra `_son_kabul` okumasından HEMEN SONRA ikinci bir bariyerde bekler. Kilit YOKSA ikisi de "önceki
    kabul yok" okuyup bariyeri birlikte geçer → iki kabul (deterministik kırmızı). Kilit VARSA ikincisi
    flock'ta bekler, bariyer zaman aşımıyla kırılır, ilki yazar; ikincisi ilkinin kabulünü okur → tavan.
  * Kilidin YERİ (`state/istek/.kilit`): çocuk süreç, ebeveynin tuttuğu flock'ta bloklanmalı.
  * Kadro enjeksiyonu: `aktif` süzgeci gerçek kadroda ısırmaz (aktif olmayan her botun `zamanli_is`i
    null) — sentetik kadroyla ölçülür. `.path` ↔ iş listesi İKİ YÖNLÜ eşitlik (yetim birim yok).
  * Geçersiz girdi sessiz varsayılana düşmez (`bot_kanal` değişmezi): bilinmeyen kanal ve saat dilimsiz
    `simdi` → `ValueError`, hiçbir şey yazılmaz. Defter yazımı düşerse kabul DÖNER (iş zaten tetiklendi)
    ama olay SİNYALLİDİR (`is_istek_defter_yazim_hatasi`).
"""
import datetime as dt
import fcntl
import json
import multiprocessing as mp
import os
import queue
import re
import stat
import threading
from pathlib import Path

import pytest
import yaml

from meridian import config, is_istek as ii, kadro, store

ROOT = config.ROOT
SIMDI = dt.datetime(2026, 9, 29, 12, 0, tzinfo=dt.timezone.utc)


def test_is_listesi_kadrodan_turer():
    assert ii.is_listesi() == {"sef": "meridian-brifing", "bekci": "meridian-bekci", "karne": "meridian-karne"}


@pytest.mark.parametrize("ad,bot", [("karne", "karne"), ("BEKÇİ", "bekci"), ("brifing", "sef"), ("şef", "sef")])
def test_kabul_istek_dosyasini_yazar(sandbox_state, ad, bot):
    s = ii.is_iste(ad, "telegram", simdi=SIMDI)
    assert (s.kabul, s.bot, s.neden) == (True, bot, "kabul")
    govde = json.loads((config.STATE / ii.ISTEK_DIZINI / f"{bot}.istek").read_text())
    assert govde["kanal"] == "telegram" and govde["ts"].startswith("2026-09-29T12:00")


def test_bilinmeyen_ve_zamanli_isi_olmayan_bot(sandbox_state):
    assert ii.is_iste("yokboyle", "pano", simdi=SIMDI).neden == "bilinmeyen_is"
    assert ii.is_iste("kod", "pano", simdi=SIMDI).neden == "bilinmeyen_is"


def test_tavan_15_dakika(sandbox_state):
    assert ii.is_iste("karne", "pano", simdi=SIMDI).kabul
    s = ii.is_iste("karne", "telegram", simdi=SIMDI + dt.timedelta(minutes=14))
    assert (s.kabul, s.neden) == (False, "tavan") and s.sonraki_uygun.startswith("2026-09-29T12:15")
    assert ii.is_iste("karne", "telegram", simdi=SIMDI + dt.timedelta(minutes=15)).kabul


def test_tavan_bot_basina(sandbox_state):
    assert ii.is_iste("karne", "pano", simdi=SIMDI).kabul
    assert ii.is_iste("bekci", "pano", simdi=SIMDI).kabul


def test_red_istek_dosyasina_dokunmaz(sandbox_state):
    ii.is_iste("karne", "pano", simdi=SIMDI)
    p = config.STATE / ii.ISTEK_DIZINI / "karne.istek"
    once = p.read_text()
    ii.is_iste("karne", "pano", simdi=SIMDI + dt.timedelta(minutes=1))
    assert p.read_text() == once


@pytest.mark.parametrize("bot,birim", [("sef", "meridian-brifing"), ("bekci", "meridian-bekci"), ("karne", "meridian-karne")])
def test_path_birimi_dogru_servisi_ve_dosyayi_izler(bot, birim):
    metin = (ROOT / "deploy/oracle-a1" / f"meridian-istek-{bot}.path").read_text(encoding="utf-8")
    assert re.search(rf"^PathChanged=/opt/meridian/state/istek/{bot}\.istek$", metin, re.M)
    assert re.search(rf"^Unit={birim}\.service$", metin, re.M)
    assert "PathExists=" not in metin  # dosya silinmediği için PathExists sonsuz yeniden tetikler
    assert (ROOT / "deploy/oracle-a1" / f"{birim}.service").is_file()


def test_path_birimleri_kopyalanir_ama_etkin_degil():
    d = yaml.safe_load((ROOT / "deploy/ansible/roles/meridian_a1/defaults/main.yml").read_text(encoding="utf-8"))
    kaynaklar = json.dumps(d.get("birim_kaynaklari"))
    etkin = json.dumps(d.get("etkin_birimler"))
    for bot in ("sef", "bekci", "karne"):
        assert f"meridian-istek-{bot}.path" in kaynaklar and f"meridian-istek-{bot}.path" not in etkin


def test_her_zamanli_is_icin_path_birimi_var():
    for bot in ii.is_listesi():
        assert (ROOT / "deploy/oracle-a1" / f"meridian-istek-{bot}.path").is_file(), bot


# ------------------------------------------------------------------------------------------------
# Ek çiviler (bkz. modül başlığı)
# ------------------------------------------------------------------------------------------------

def test_yetim_path_birimi_yok_iki_yonlu_esitlik():
    """Kadrodan bir botun `zamanli_is`i kalkarsa onun `.path` birimi de kalkmalı: yetim birim, var
    olmayan bir isteği izler ve 'şimdi çalıştır' yüzeyinin donuk listesi iki yerde ayrışır."""
    birimler = {p.name.removeprefix("meridian-istek-").removesuffix(".path")
                for p in (ROOT / "deploy/oracle-a1").glob("meridian-istek-*.path")}
    assert birimler == set(ii.is_listesi())


def _bot(ad: str, durum: str, zamanli_is: str | None) -> kadro.Bot:
    return kadro.Bot(ad=ad, rol="", dalga="1", durum=durum, araclar=("pano_ozeti",), zamanli_is=zamanli_is,
                     imza=None, hafiza="kendi", gunluk_tavan=None, gunluk_tavan_neden="sentetik")


def test_is_listesi_yalniz_aktif_ve_zamanli_isi_dolu_botlar():
    sentetik = (_bot("alfa", "aktif", "meridian-alfa"), _bot("beta", "sirada", "meridian-beta"),
                _bot("gama", "aktif", None), _bot("delta", "kilitli", "meridian-delta"))
    assert ii.is_listesi(sentetik) == {"alfa": "meridian-alfa"}


def test_kadro_enjeksiyonu_is_iste_ye_gecer(sandbox_state):
    sentetik = (_bot("alfa", "aktif", "meridian-alfa"),)
    s = ii.is_iste("alfa", "pano", simdi=SIMDI, kadro=sentetik)
    assert (s.kabul, s.bot, s.birim) == (True, "alfa", "meridian-alfa")
    assert ii.is_iste("karne", "pano", simdi=SIMDI, kadro=sentetik).neden == "bilinmeyen_is"


def test_sonuc_alanlari_ve_defter_satiri(sandbox_state):
    s = ii.is_iste("brifing", "pano", simdi=SIMDI)
    assert s == ii.IsSonuc(kabul=True, bot="sef", birim="meridian-brifing", neden="kabul", sonraki_uygun=None)
    satirlar = store.read_jsonl(ii.DEFTER)
    assert [(r["bot"], r["birim"], r["kanal"], r["neden"]) for r in satirlar] == [("sef", "meridian-brifing", "pano", "kabul")]
    assert satirlar[0]["ts"].startswith("2026-09-29T12:00")
    red = ii.is_iste("yokboyle", "pano", simdi=SIMDI)
    assert (red.kabul, red.bot, red.birim, red.sonraki_uygun) == (False, None, None, None)
    tavan = ii.is_iste("sef", "pano", simdi=SIMDI)
    assert (tavan.bot, tavan.birim) == ("sef", "meridian-brifing")
    assert len(store.read_jsonl(ii.DEFTER)) == 1, "red satırı deftere düşmemeli (tavan yalnız kabulleri sayar)"


def test_gecersiz_kanal_ve_dilimsiz_an_hicbir_sey_yazmaz(sandbox_state):
    with pytest.raises(ValueError):
        ii.is_iste("karne", "sms", simdi=SIMDI)
    with pytest.raises(ValueError):
        ii.is_iste("karne", "pano", simdi=dt.datetime(2026, 9, 29, 12, 0))
    assert not (config.STATE / ii.ISTEK_DIZINI / "karne.istek").exists()
    assert store.read_jsonl(ii.DEFTER) == []


def test_istek_dizini_750_ile_kurulur(sandbox_state):
    maske = os.umask(0)
    os.umask(maske)
    ii.is_iste("karne", "pano", simdi=SIMDI)
    kip = stat.S_IMODE((config.STATE / ii.ISTEK_DIZINI).stat().st_mode)
    assert kip == 0o750 & ~maske


def test_defter_yazimi_duserse_kabul_doner_ve_olay_sinyallidir(sandbox_state, monkeypatch):
    asil = store.append_jsonl

    def bozuk(ad, satir):
        if ad == ii.DEFTER:
            raise OSError("disk dolu (sentetik)")
        return asil(ad, satir)

    monkeypatch.setattr(store, "append_jsonl", bozuk)
    s = ii.is_iste("karne", "pano", simdi=SIMDI)
    assert s.kabul and (config.STATE / ii.ISTEK_DIZINI / "karne.istek").exists()
    olaylar = [r for r in store.read_jsonl("events.jsonl") if r.get("event") == "is_istek_defter_yazim_hatasi"]
    assert len(olaylar) == 1 and olaylar[0]["bot"] == "karne" and olaylar[0]["sinif"] == "OSError"


# ---- süreçler arası kilit ----------------------------------------------------------------------
# `spawn` bilerek: ebeveynin monkeypatch'i çocuğa GEÇMEZ, çocuk `config.STATE`i argümandan kurar —
# yani çocuk canlı `state/`e hiçbir koşulda yazamaz (ilk iş STATE atamasıdır).

def _isci_yaris(state: str, baslangic, okuma_sonrasi, kuyruk) -> None:
    from meridian import config as _config, is_istek as _ii
    _config.STATE = Path(state)
    asil = _ii._son_kabul

    def okuduktan_sonra_bekle(bot):
        sonuc = asil(bot)
        try:
            okuma_sonrasi.wait(timeout=3)
        except threading.BrokenBarrierError:  # sessiz-yutma: kilit ÇALIŞIYOR demektir — öteki süreç flock'ta, bariyere hiç gelmedi
            pass
        return sonuc

    _ii._son_kabul = okuduktan_sonra_bekle
    baslangic.wait(timeout=60)
    s = _ii.is_iste("karne", "pano", simdi=SIMDI)
    kuyruk.put((s.kabul, s.neden))


def test_iki_surec_ayni_anda_tam_bir_kabul_bir_tavan(sandbox_state):
    ctx = mp.get_context("spawn")
    baslangic, okuma_sonrasi, kuyruk = ctx.Barrier(2), ctx.Barrier(2), ctx.Queue()
    surecler = [ctx.Process(target=_isci_yaris, args=(str(config.STATE), baslangic, okuma_sonrasi, kuyruk))
                for _ in range(2)]
    for p in surecler:
        p.start()
    sonuclar = sorted(kuyruk.get(timeout=120) for _ in surecler)
    for p in surecler:
        p.join(timeout=60)
        assert p.exitcode == 0
    assert sonuclar == [(False, "tavan"), (True, "kabul")]
    assert [r["neden"] for r in store.read_jsonl(ii.DEFTER)] == ["kabul"]


def _isci_tek(state: str, kuyruk) -> None:
    from meridian import config as _config, is_istek as _ii
    _config.STATE = Path(state)
    kuyruk.put("basladi")
    s = _ii.is_iste("karne", "pano", simdi=SIMDI)
    kuyruk.put((s.kabul, s.neden))


def test_kilit_istek_dizinindeki_kilit_dosyasidir(sandbox_state):
    dizin = config.STATE / ii.ISTEK_DIZINI
    dizin.mkdir(parents=True)
    ctx = mp.get_context("spawn")
    kuyruk = ctx.Queue()
    with open(dizin / ".kilit", "a+") as kilit:
        fcntl.flock(kilit, fcntl.LOCK_EX)
        p = ctx.Process(target=_isci_tek, args=(str(config.STATE), kuyruk))
        p.start()
        assert kuyruk.get(timeout=120) == "basladi"
        with pytest.raises(queue.Empty):
            kuyruk.get(timeout=2)  # çocuk ebeveynin flock'unda BLOKLU olmalı
        fcntl.flock(kilit, fcntl.LOCK_UN)
    assert kuyruk.get(timeout=60) == (True, "kabul")
    p.join(timeout=60)
    assert p.exitcode == 0
