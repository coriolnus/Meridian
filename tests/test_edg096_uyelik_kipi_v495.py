"""tests/test_edg096_uyelik_kipi_v495.py — EDG-2026-096 ÜYELİK KİPLERİ (k093 `--uyelik-kipi`)
ve karşılaştırma betiği çivileri.

vNNN KİMLİK KAYDI: v495 kartın kendi `notlar` alanında ("tests v495") ön-kayıtlıdır; ölçüm anında
(2026-09-15) `grep -rl v495 tests/ ops/ meridian/ research/ docs/` YALNIZ o kart satırını verdi —
`tests/` altında v495 BOŞ, çakışma yok, taşıma yok (CLAUDE.md §2 vNNN kimlik kuralı).

NE ÇİVİLER. EDG-2026-096 kartı EDG-016'nın ii katmanındaki CI-0-dışılığın EVREN SEÇİMİNDEN mi
geldiğini soruyor ve aynı kodu (EDG-093 ölçüm betiği) ÜÇ üyelik kipinde koşuyor:
  A `asof`   — as-of PIT adım fonksiyonu (EDG-093'ün DAVRANIŞI; VARSAYILAN, DEĞİŞMEZ),
  B `guncel` — kohort defterinin SON etkin satırındaki küme BÜTÜN pencereye geriye uygulanır,
  C `sabit`  — verilen liste (EDG-016'nın sabit evreni) her güne uygulanır.
Ölçülen şey SAYILAR DEĞİL (onlar gerçek veriyle A1'de doğar), SÖZLEŞMELERDİR:
  (1) REGRESYON — `kip` verilmeden çağrı `asof`tur ve `asof` haritası eski davranışla BİREBİR
      aynıdır; `--uyelik-kipi asof` koşumunun çıktı dosya adları ESKİ desendedir;
  (2) B kipi her güne SON satırın kümesini verir (belirsiz düşürme UYGULANIR);
  (3) C kipi her güne verilen kümeyi verir (belirsiz düşürme UYGULANMAZ — sabit liste kohort
      defterinden gelmez, defterin belirsiz tablosu onun üzerinde tanımsızdır);
  (4) PK (3) — kohort defteri TEK satıra indirgenince ÜÇ KİP AYNI haritayı verir;
  (5) sabit listenin bar/shares kapsamı DIŞINDA kalan isimleri ÖLÇÜLEMEDİ sayılır ve künyede
      sayı + oran + örnekle durur (uydurma yasağı; kart eşiği yüzde 20);
  (6) bilinmeyen kip kullanım hatasıdır (çıkış 2) ve sabit liste künyesinin sha256'sı sıralı
      sembollerin satır-sonuyla birleşiminin sha256'sıdır;
  (7) karşılaştırma betiği eşikleri KARTTAN okur (kopya eşik YOK), A kipini PK-1 detayına karşı
      sınar, kart kill-list metinlerini tetikler ve HÜKÜM YAZMAZ.

NEDEN ALT SÜREÇ (CLI çivileri). Ölçüm betiği wp2 altyapısını `sys.modules` içine kaydeder ve
`meridian.config` STATE'ini çıktı dizinine çevirir; bunu pytest sürecinde yapmak komşu testlerin
ortamını kirletirdi (emsal v488/v489/v490 aynı gerekçeyle alt süreç kullanır). Saf sözleşme
çivileri (harita kipleri) modülü ithal ederek koşar — ölçüm betiğinin MODÜL DÜZEYİ TEMİZDİR.

FİKSTÜR TEK KAYNAKTAN: sentetik bar/shares/kohort üreticileri v490'dan İTHAL EDİLİR, buraya
KOPYALANMAZ — kopya, üreticinin sabitleri (asgari seri uzunluğu, asgari kesit) değiştiğinde
sessizce ayrışır ve bu dosya "temiz" derdi (tek-kaynak yasası, CLAUDE.md §4).

AĞ YOK. Kart dosyasına YAZILMAZ (yalnız OKUNUR — eşik ve kill-list metni oradan gelir).

MUTASYON KANITI (bu dosyada KOŞMAZ, rapora yazılır — CLAUDE.md §6): her çivinin ısırdığı dal
rapor tablosundadır (kip dalları, künye kapsam sayımı, dosya adı eki, eşik okuma).
"""
from __future__ import annotations

import datetime as dt
import gzip
import hashlib
import json
import os
import pathlib
import subprocess
import sys

import pytest

from tests.conftest import betikten_modul_yukle
from tests.test_edg093_olcum_v490 import (
    _bar_csv, _seanslar, _shares_satirlari, _wp2_sabitleri)

REPO = pathlib.Path(__file__).resolve().parents[1]
OLCUM = REPO / "research" / "olcumler" / "edg093_midcap_pit"
K093 = OLCUM / "k093.py"
KARSILASTIR = OLCUM / "karsilastir096.py"
KART096 = REPO / "research" / "cards" / "EDG-2026-096-edg016-katman-ii-sagkalan-yanliligi.yaml"

#: Sentetik kohort defteri — ÜÇ as-of satırı. Kipler arasındaki farkı ancak satırlar FARKLI
#: kümeler taşıdığında görürüz: `guncel` SON satırı, `asof` gözlem gününün satırını verir.
G1, G2, G3 = "2020-01-02", "2020-02-03", "2020-03-02"
S1 = frozenset({"AAA", "BBB"})
S2 = frozenset({"AAA", "BBB", "CCC"})
S3 = frozenset({"BBB", "CCC"})

#: Gözlem günleri: ilk satırdan ÖNCE bir gün BİLEREK vardır — `asof` orada ÜYE YOK demeli
#: (geriye taşımama kuralı), `guncel`/`sabit` ise kendi kümesini vermeli.
GUNLER = ["2019-12-31", G1, "2020-01-20", G2, "2020-02-20", G3, "2020-03-20"]

#: Sabit liste fikstüründe bar/shares kapsamının DIŞINDA kalacak iki isim. Kohortta ve bars
#: dizininde YOKTURLAR: kapsam sayımı bunları ÖLÇÜLEMEDİ saymalı.
HAYALET = ("ZZA", "ZZB")


def _etkin():
    """(tarih, küme) as-of satırları — ölçüm betiğinin kohort okuyucusunun döndürdüğü biçim."""
    return [(dt.date.fromisoformat(G1), S1), (dt.date.fromisoformat(G2), S2),
            (dt.date.fromisoformat(G3), S3)]


@pytest.fixture(scope="module")
def k093_modul():
    """Ölçüm betiği İTHAL EDİLİR (modül düzeyi temiz: argparse ana akışın içinde, G/Ç yok).
    Yükleme şasi yükleyicisiyledir — ham exec_module `__pycache__`e bakar ve boyut-koruyan bir
    düzenlemede BAYAT bytecode koşar (v334 sınıfı)."""
    return betikten_modul_yukle(K093, "v495_k093_modul")


@pytest.fixture(scope="module")
def k096_modul():
    """Karşılaştırma betiği — aynı yükleme disiplini."""
    return betikten_modul_yukle(KARSILASTIR, "v495_karsilastir096_modul")


# =================================================================================================
# A. ÜYELİK HARİTASI — ÜÇ KİP (saf fonksiyon, alt süreç gerekmez)
# =================================================================================================
def test_T1_ASOF_REGRESYONU_kip_verilmeden_cagri_ASOFtur(k093_modul, sandbox_state):
    """REGRESYON ÇİVİSİ: `kip` verilmeyen çağrı EDG-093'ün davranışını BİREBİR korur ve
    `kip="asof"` ile AYNI haritayı verir. Beklenen harita burada DONMUŞ sözlüktür — üretilmiş
    değil, elle yazılmış: kendi kendini doğrulayan bir beklenti hiçbir şey ölçmez."""
    beklenen = {
        "2019-12-31": frozenset(),          # ilk satırdan ÖNCE: ÜYE YOK (geriye taşınmaz)
        G1: S1, "2020-01-20": S1,
        G2: S2, "2020-02-20": S2,
        G3: S3, "2020-03-20": S3,
    }
    eski = k093_modul.uyelik_haritasi(_etkin(), GUNLER)
    assert eski == beklenen, "as-of harita EDG-093 davranışından AYRIŞTI (regresyon)"
    assert eski == k093_modul.uyelik_haritasi(_etkin(), GUNLER, kip="asof")
    assert k093_modul.VARSAYILAN_UYELIK_KIPI == "asof"


def test_T1b_ASOF_BELIRSIZ_DUSURME_KORUNUR(k093_modul, sandbox_state):
    """`dusur` kümesi as-of kipinde HER günden çıkarılır (EDG-093 `haric` duyarlılığı) — üye
    olmayan gün BOŞ KALIR, sessizce dolmaz."""
    h = k093_modul.uyelik_haritasi(_etkin(), GUNLER, frozenset({"BBB"}))
    assert h["2019-12-31"] == frozenset()
    assert h[G1] == frozenset({"AAA"})
    assert h[G3] == frozenset({"CCC"})


def test_T2_GUNCEL_KIPI_HER_GUNE_SON_SATIRIN_KUMESI(k093_modul, sandbox_state):
    """B kipi: defterin SON etkin satırındaki küme BÜTÜN pencereye geriye uygulanır — "bugünün
    listesiyle geçmişi ölçmek", yani sağkalan yanlılığının kendisi. `dusur` UYGULANIR."""
    h = k093_modul.uyelik_haritasi(_etkin(), GUNLER, kip="guncel")
    assert set(h) == set(GUNLER)
    assert all(v == S3 for v in h.values()), f"guncel kipi son kümeyi vermiyor: {h}"
    d = k093_modul.uyelik_haritasi(_etkin(), GUNLER, frozenset({"CCC"}), kip="guncel")
    assert all(v == frozenset({"BBB"}) for v in d.values())


def test_T3_SABIT_KIPI_HER_GUNE_VERILEN_KUME(k093_modul, sandbox_state):
    """C kipi: verilen liste her güne uygulanır ve `dusur` UYGULANMAZ — sabit liste kohort
    defterinden gelmez, defterin belirsiz-isim tablosu onun üzerinde TANIMSIZDIR (kesişim varsa
    künyede SAYILIR, sessizce düşürülmez)."""
    sabit = ["MMM", "NNN", "BBB"]
    h = k093_modul.uyelik_haritasi(_etkin(), GUNLER, kip="sabit", sabit=sabit)
    assert all(v == frozenset(sabit) for v in h.values())
    d = k093_modul.uyelik_haritasi(_etkin(), GUNLER, frozenset({"BBB"}), kip="sabit", sabit=sabit)
    assert all(v == frozenset(sabit) for v in d.values()), "sabit kipinde `dusur` uygulanmış"


def test_T3b_SABIT_LISTESIZ_KULLANIM_HATASI(k093_modul, sandbox_state):
    """Sabit kip için liste YOKSA küme UYDURULMAZ: kullanım hatası (çıkış 2)."""
    with pytest.raises(SystemExit) as e:
        k093_modul.uyelik_haritasi(_etkin(), GUNLER, kip="sabit")
    assert e.value.code == 2


def test_T3c_BILINMEYEN_KIP_KULLANIM_HATASI(k093_modul, sandbox_state):
    """Bilinmeyen kip sessizce as-of'a DÜŞMEZ — düşseydi yanlış evrenle ölçülen bir koşum
    "başarılı" görünürdü."""
    with pytest.raises(SystemExit) as e:
        k093_modul.uyelik_haritasi(_etkin(), GUNLER, kip="gunce")
    assert e.value.code == 2


def test_T4_PK3_TEK_SATIRLIK_KOHORTTA_UC_KIP_AYNI(k093_modul, sandbox_state):
    """KARTIN PK (3)'ü: kohort defteri TEK satıra indirgenince `asof` ≡ `guncel` ≡ `sabit(o küme)`.

    Gözlem günleri BİLEREK o satırın tarihinden İTİBAREN seçilir: daha erken bir gün `asof`ta
    ÜYE YOK demektir (doğru davranış) ve üçlü özdeşlik o gün için TANIMSIZ olurdu — sınav
    kendi tanımının dışına çıkmaz."""
    tek = [(dt.date.fromisoformat(G2), S2)]
    gunler = [G2, "2020-02-20", G3, "2020-03-20"]
    a = k093_modul.uyelik_haritasi(tek, gunler)
    b = k093_modul.uyelik_haritasi(tek, gunler, kip="guncel")
    c = k093_modul.uyelik_haritasi(tek, gunler, kip="sabit", sabit=S2)
    assert a == b == c, f"üç kip ayrıştı:\nasof={a}\nguncel={b}\nsabit={c}"
    assert all(v == S2 for v in a.values())


# =================================================================================================
# B. SABİT LİSTE KÜNYESİ — sha ve kapsam sayımı (saf fonksiyon)
# =================================================================================================
def test_T5b_KUNYE_SHA_SIRALI_BIRLESIMIN_SHA256I(k093_modul, sandbox_state):
    """Künye sha'sı SIRALI sembollerin satır-sonuyla birleşiminin sha256'sıdır — liste sırası
    değişince sha DEĞİŞMEZ, içerik değişince DEĞİŞİR (aynı listenin iki yazımı aynı künyeyi
    vermeli, yoksa künye kaynağı değil dosya biçimini damgalardı)."""
    kunye = k093_modul.sabit_liste_kunyesi(["CCC", "AAA", "BBB"], "sınav", {"AAA"}, frozenset())
    beklenen = hashlib.sha256("AAA\nBBB\nCCC".encode("utf-8")).hexdigest()
    assert kunye["sha256"] == beklenen
    assert k093_modul.sabit_liste_kunyesi(
        ["AAA", "BBB", "CCC"], "sınav", {"AAA"}, frozenset())["sha256"] == beklenen
    assert kunye["n"] == 3 and kunye["kaynak"] == "sınav"


def test_T5c_KUNYE_KAPSAM_DISI_OLCULEMEDI_SAYILIR(k093_modul, sandbox_state):
    """Kapsam dışı isimler ÖLÇÜLEMEDİ'dir: sayı, oran ve örnek yazılır; değer UYDURULMAZ ve
    geriye taşınmaz. Kart eşiği (`olculemeyen_sabit_liste_ust_oran`) tam bu oranı okur."""
    kunye = k093_modul.sabit_liste_kunyesi(
        ["AAA", "BBB", "CCC", "DDD"], "sınav", {"AAA", "BBB"}, frozenset({"CCC"}))
    assert kunye["kapsam_disi_n"] == 2
    assert kunye["kapsam_disi_ornek"] == ["CCC", "DDD"]
    assert abs(kunye["kapsam_disi_oran"] - 0.5) < 1e-12
    assert kunye["belirsiz_kesisim_n"] == 1 and kunye["belirsiz_kesisim"] == ["CCC"]
    assert "ÖLÇÜLEMEDİ" in kunye["tanim"]


def test_T5d_KUNYE_KAPSAM_OLCULEMEYINCE_SAYI_UYDURULMAZ(k093_modul, sandbox_state):
    """Kapsam kümesi ÖLÇÜLEMEDİYSE (panel kurulamadı) sayı SIFIR yazılmaz — None + neden.
    Sıfır ile "bilmiyorum" aynı şey değildir (uydurma yasağı)."""
    kunye = k093_modul.sabit_liste_kunyesi(["AAA"], "sınav", None, frozenset())
    assert kunye["kapsam_disi_n"] is None and kunye["kapsam_disi_oran"] is None
    assert kunye["neden"]


# =================================================================================================
# C. CLI — sentetik depo üzerinde GERÇEK koşum (alt süreç)
# =================================================================================================
@pytest.fixture(scope="module")
def sentetik_girdiler(tmp_path_factory):
    """Sentetik bar/shares/kohort girdileri — üreticiler v490'dan İTHAL (kopya yok).

    NEDEN `sandbox_state` YOK: bu fikstür MODÜL kapsamlıdır (iki alt-süreç koşumu ~1 dk sürer,
    test başına yeniden kurmak bedeli ikiye katlardı) ve `sandbox_state` fonksiyon kapsamlıdır.
    İzolasyon ALT SÜREÇTEDİR: ölçüm betiği kendi STATE'ini `--cikti` altına çevirir, bu süreçte
    hiçbir modül ithal edilmez (v490 fikstürünün aynı gerekçesi)."""
    bar_min, min_kesit = _wp2_sabitleri()
    n_seans = bar_min + 200
    n_sembol = min_kesit + 3
    seanslar = _seanslar(n_seans)

    kok = tmp_path_factory.mktemp("edg096_v495")
    bars = kok / "bars"
    bars.mkdir()
    semboller = [f"N{chr(65 + i // 26)}{chr(65 + i % 26)}" for i in range(n_sembol)]
    assert len(set(semboller)) == n_sembol and not (set(semboller) & set(HAYALET))
    for i, s in enumerate(semboller):
        (bars / f"{s.lower()}.csv").write_text(_bar_csv(s, seanslar, 9000 + i), encoding="utf-8")

    kolonlar = ["symbol", "cik", "taxonomy", "tag", "unit", "start", "end", "filed", "val",
                "form", "fy", "fp", "donem_gun", "donem_turu", "accn", "frame"]
    shares = kok / "shares_sentetik.csv.gz"
    with gzip.open(shares, "wt", encoding="utf-8", newline="") as fh:
        fh.write(",".join(kolonlar) + "\n")
        for s in semboller:
            for r in _shares_satirlari(s, seanslar, None):
                fh.write(",".join(str(r[k]) for k in kolonlar) + "\n")

    # Kohort defteri İKİ satır: son satır ilk sembolü DÜŞÜRÜR — `guncel`/`sabit` kiplerinin
    # `asof`tan farkı ancak defter değişirse görünür.
    kohort = kok / "kohort_sentetik.csv"
    kohort.write_text(
        "date,tickers\n"
        f'{seanslar[0]},"{",".join(sorted(semboller))}"\n'
        f'{seanslar[300]},"{",".join(sorted(semboller[1:]))}"\n', encoding="utf-8")

    kart = kok / "kart_sentetik.yaml"
    kart.write_text("card_id: EDG-2026-093\n"
                    f'veri_penceresi: "{seanslar[0]} (sentetik) → ölçüm günü"\n', encoding="utf-8")
    kart092 = kok / "kart092_sentetik.yaml"
    kart092.write_text("card_id: EDG-2026-092\nbilinen_olaylar: []\n", encoding="utf-8")

    # Sabit liste: kohortun TAMAMI + bar/shares kapsamında OLMAYAN iki isim.
    sabit_liste = kok / "sabit_liste.txt"
    sabit_semboller = sorted(semboller) + list(HAYALET)
    sabit_liste.write_text(
        "# EDG-096 sentetik sabit liste (satır başına sembol)\n"
        + "\n".join(sabit_semboller) + "\n", encoding="utf-8")
    return {"kok": kok, "bars": bars, "shares": shares, "kohort": kohort, "kart": kart,
            "kart092": kart092, "seanslar": seanslar, "semboller": semboller,
            "sabit_liste": sabit_liste, "sabit_semboller": sabit_semboller}


def _kosur(g, cikti, *ek):
    env = dict(os.environ, PYTHONPATH=str(REPO), PYTHONDONTWRITEBYTECODE="1")
    return subprocess.run(
        [sys.executable, str(K093), "--repo", str(REPO), "--kohort", str(g["kohort"]),
         "--bars-dir", str(g["bars"]), "--shares", str(g["shares"]), "--cikti", str(cikti),
         "--kart", str(g["kart"]), "--kart092", str(g["kart092"]),
         "--bitis", g["seanslar"][-1], "--belirsiz", "dahil", *ek],
        cwd=str(REPO), env=env, capture_output=True, text=True, timeout=1800)


@pytest.fixture(scope="module")
def asof_kosumu(sentetik_girdiler):
    """AÇIK `--uyelik-kipi asof` koşumu — dosya adı regresyonunun ölçüldüğü yer."""
    cikti = sentetik_girdiler["kok"] / "cikti_asof"
    p = _kosur(sentetik_girdiler, cikti, "--uyelik-kipi", "asof")
    assert p.returncode == 0, f"çıkış {p.returncode}\nSTDOUT:\n{p.stdout}\nSTDERR:\n{p.stderr}"
    return {"cikti": cikti}


@pytest.fixture(scope="module")
def sabit_kosumu(sentetik_girdiler):
    """`--uyelik-kipi sabit --sabit-liste <dosya>` koşumu — künye ve kapsam sayımının ölçüldüğü
    yer. Ops aracı teslim edilmeden önce OPERATÖRÜN KOŞACAĞI BİÇİMDE bir kez koşar (CLAUDE.md
    §6: 18 çivi yeşilken bir bayrak sessizce yok sayılıyordu)."""
    g = sentetik_girdiler
    cikti = g["kok"] / "cikti_sabit"
    p = _kosur(g, cikti, "--uyelik-kipi", "sabit", "--sabit-liste", str(g["sabit_liste"]))
    assert p.returncode == 0, f"çıkış {p.returncode}\nSTDOUT:\n{p.stdout}\nSTDERR:\n{p.stderr}"
    jsonlar = sorted(cikti.glob("sonuc_093_*.json"))
    assert len(jsonlar) == 1, f"tek sonuç json beklendi: {jsonlar}"
    return {"cikti": cikti, "json_yolu": jsonlar[0],
            "sonuc": json.loads(jsonlar[0].read_text(encoding="utf-8"))}


def test_T8_ASOF_KIPINDE_DOSYA_ADI_ESKI_DESEN(asof_kosumu):
    """REGRESYON: `asof` kipinde çıktı adları EDG-093'ün desenindedir (kip EKİ YOK) — ad
    değişseydi EDG-093'ün okuyucuları (Rol-1 hüküm akışı, rapor üreteci) sessizce dosya
    bulamazdı."""
    cikti = asof_kosumu["cikti"]
    jsonlar = sorted(p.name for p in cikti.glob("sonuc_093_*.json"))
    raporlar = sorted(p.name for p in cikti.glob("RAPOR_093_*.md"))
    assert len(jsonlar) == 1 and len(raporlar) == 1
    sonuc = json.loads((cikti / jsonlar[0]).read_text(encoding="utf-8"))
    damga = sonuc["damga_utc"]
    assert jsonlar[0] == f"sonuc_093_{damga}.json", f"asof kipinde ad değişti: {jsonlar[0]}"
    assert raporlar[0] == f"RAPOR_093_{damga}.md"
    assert sonuc["uyelik_kipi"] == "asof"
    assert (sonuc.get("sabit_liste_kunyesi") or {}).get("neden"), (
        "asof kipinde sabit liste KULLANILMADI — bu bir beyandır, sessiz boşluk değil")


def test_T6_SABIT_KIPINDE_DOSYA_ADI_KIP_EKI_TASIR(sabit_kosumu):
    """Kip eki olmasaydı üç koşum AYNI dizinde birbirinin adını taşır ve hangi sayının hangi
    evrenden geldiği KAYBOLURDU (kartın K defteri tam bunu ayırt eder)."""
    damga = sabit_kosumu["sonuc"]["damga_utc"]
    assert sabit_kosumu["json_yolu"].name == f"sonuc_093_sabit_{damga}.json"
    assert (sabit_kosumu["cikti"] / f"RAPOR_093_sabit_{damga}.md").exists()
    assert sabit_kosumu["sonuc"]["uyelik_kipi"] == "sabit"


def test_T6b_SABIT_LISTE_DOSYADAN_OKUNUR_ve_SHA_KUNYELENIR(sabit_kosumu, sentetik_girdiler):
    """Sabit liste DOSYADAN okunur, künye sha'sı sıralı birleşimin sha256'sıdır ve kaynak ADIYLA
    yazılır — sha olmadan "hangi 251 isim" sorusu sonradan cevaplanamaz."""
    k = sabit_kosumu["sonuc"]["sabit_liste_kunyesi"]
    beklenen = hashlib.sha256(
        "\n".join(sorted(sentetik_girdiler["sabit_semboller"])).encode("utf-8")).hexdigest()
    assert k["sha256"] == beklenen, "künye sha'sı sıralı birleşimin sha256'sı değil"
    assert k["n"] == len(sentetik_girdiler["sabit_semboller"])
    assert str(sentetik_girdiler["sabit_liste"]) in (k["kaynak"] or "")
    assert k["neden"] is None


def test_T5_SABIT_LISTE_KAPSAM_DISI_ISIMLER_SAYILIR(sabit_kosumu, sentetik_girdiler):
    """Sabit listede bar/shares kapsamı DIŞINDA kalan iki isim ÖLÇÜLEMEDİ sayılır: sayı 2, oran
    2/n ve örnekte ADLARI durur. Sayılmasaydı C kipi "tam evren ölçüldü" diye görünür ve kartın
    yüzde 20 eşiği kör kalırdı."""
    k = sabit_kosumu["sonuc"]["sabit_liste_kunyesi"]
    n = len(sentetik_girdiler["sabit_semboller"])
    assert k["kapsam_disi_n"] == 2, f"kapsam dışı sayısı {k['kapsam_disi_n']} (beklenen 2)"
    assert sorted(k["kapsam_disi_ornek"]) == sorted(HAYALET)
    # oran kayda 6 haneye YUVARLANMIŞ yazılır — tolerans o yuvarlamanındır (v490 emsali)
    assert abs(k["kapsam_disi_oran"] - 2.0 / n) < 1e-6
    assert len(k["kapsam_disi_ornek"]) <= 10


def test_T6c_SABIT_KIPINDE_UYELIK_HER_GUN_AYNI_KUME(sabit_kosumu, sentetik_girdiler):
    """C kipinin ısırdığı yer: kohort defteri son satırda bir ismi DÜŞÜRÜR, ama sabit kipte o
    isim pencere sonuna kadar ölçülmeye devam eder (as-of kipinde etmezdi)."""
    u = sabit_kosumu["sonuc"]["kosumlar"]["dahil"]["uyelik_suzgeci"]
    dusen = sentetik_girdiler["semboller"][0]
    ara = u["sembol_uye_gun_araligi"][dusen]
    assert ara["son"] == sabit_kosumu["sonuc"]["evren_muhasebesi"]["pencere_bitis"] or \
        ara["son"] >= sentetik_girdiler["seanslar"][300], (
        f"{dusen} sabit kipte defter düşüşünden sonra ölçülmüyor: {ara}")


@pytest.fixture(scope="module")
def sabit_varsayilan_kosumu(sentetik_girdiler):
    """`--sabit-liste` VERİLMEDEN `sabit` koşumu — A1'de kart bu biçimi kullanacak (sabit evren
    kaynağı EDG-016'nın REPLAY_UNIVERSE listesidir). Ops aracı teslim edilmeden önce OPERATÖRÜN
    KOŞACAĞI BİÇİMDE bir kez koşar (CLAUDE.md §6)."""
    cikti = sentetik_girdiler["kok"] / "cikti_sabit_varsayilan"
    p = _kosur(sentetik_girdiler, cikti, "--uyelik-kipi", "sabit")
    assert p.returncode == 0, f"çıkış {p.returncode}\nSTDOUT:\n{p.stdout}\nSTDERR:\n{p.stderr}"
    jsonlar = sorted(cikti.glob("sonuc_093_sabit_*.json"))
    assert len(jsonlar) == 1, f"tek sonuç json beklendi: {jsonlar}"
    return json.loads(jsonlar[0].read_text(encoding="utf-8"))


def test_T6g_SABIT_LISTESIZ_KOSUM_REPLAY_UNIVERSEU_KUNYELER(sabit_varsayilan_kosumu):
    """Dosya verilmeyince evren ithal yüzeyindeki REPLAY_UNIVERSE'tür, kaynak ADIYLA yazılır ve
    künye sha'sı o listenin sıralı birleşiminden gelir. Sembol sayısı motordan OKUNUR, buraya
    KOPYALANMAZ (tek-kaynak: liste büyürse çivi kendiliğinden yeni sayıyı ölçer)."""
    from meridian.adapters.data import REPLAY_UNIVERSE
    k = sabit_varsayilan_kosumu["sabit_liste_kunyesi"]
    benzersiz = sorted({s.upper() for s in REPLAY_UNIVERSE})
    assert "REPLAY_UNIVERSE" in (k["kaynak"] or ""), k["kaynak"]
    assert k["n"] == len(benzersiz)
    assert k["sha256"] == hashlib.sha256("\n".join(benzersiz).encode("utf-8")).hexdigest()
    # Sentetik kohortun hiçbir ismi bu listede YOKTUR — kapsam dışı pay %100 olmalı ve bu
    # ÖLÇÜLMÜŞ bir sayıdır, hata değil (kartın %20 eşiği tam bu durumu bilgisiz sayar).
    assert k["kapsam_disi_n"] == len(benzersiz) and k["kapsam_disi_oran"] == 1.0


def test_T6d_BILINMEYEN_KIP_CLI_CIKIS_2(sentetik_girdiler):
    """CLI'da bilinmeyen kip ÇIKIŞ 2'dir (kullanım hatasıyla AYNI kod) — sessizce varsayılana
    düşseydi yanlış evrenle koşan bir ölçüm "başarılı" görünürdü."""
    p = _kosur(sentetik_girdiler, sentetik_girdiler["kok"] / "cikti_bogus",
               "--uyelik-kipi", "bogus")
    assert p.returncode == 2, f"çıkış {p.returncode}\nSTDERR:\n{p.stderr}"


def test_T6e_SABIT_LISTE_YANLIS_KIPTE_SESSIZCE_YOK_SAYILMAZ(sentetik_girdiler):
    """`--sabit-liste` verilip kip `sabit` değilse bayrak SESSİZCE YOK SAYILMAZ: çıkış 2.
    (Emsal: 18 çivi yeşilken bir bayrağın sessizce yok sayılması, CLAUDE.md §6.)"""
    g = sentetik_girdiler
    p = _kosur(g, g["kok"] / "cikti_bayrak", "--uyelik-kipi", "asof",
               "--sabit-liste", str(g["sabit_liste"]))
    assert p.returncode == 2, f"çıkış {p.returncode}\nSTDERR:\n{p.stderr}"


def test_T6f_RAPOR_KIP_ve_KUNYE_SATIRI_TASIR(sabit_kosumu):
    """RAPOR okuyanı (Rol-1 / operatör masası) kipi ve künyeyi RAPORDA görmeli — JSON'a bakmak
    zorunda kalırsa iki kaynak ayrışır."""
    damga = sabit_kosumu["sonuc"]["damga_utc"]
    metin = (sabit_kosumu["cikti"] / f"RAPOR_093_sabit_{damga}.md").read_text(encoding="utf-8")
    assert "Üyelik kipi" in metin and "sabit" in metin
    assert "Sabit liste" in metin and sabit_kosumu["sonuc"]["sabit_liste_kunyesi"]["sha256"][:12] \
        in metin


# =================================================================================================
# D. KARŞILAŞTIRMA BETİĞİ (T7)
# =================================================================================================
def _bacak(deger, anlamli, alan="ort"):
    ci = {"lo": deger - 0.001, "hi": deger + 0.001, "seviye": 0.95} if anlamli else \
         {"lo": deger - 0.05, "hi": deger + 0.05, "seviye": 0.95}
    return {"n": 1000, alan: deger, "ci": ci, "anlamli": anlamli,
            "pozitif_anlamli": bool(anlamli and deger > 0), "negatif_anlamli": False}


def _sonuc(kip, i20, a1_20, iib_20, iib_anlamli=False, kunye=None, i20_anlamli=True):
    """Kart bacaklarını taşıyan ASGARİ sonuç sözlüğü (karşılaştırma betiğinin okuduğu alanlar)."""
    return {
        "kart": "EDG-2026-093", "hukum": "YOK — Rol-1", "damga_utc": "20260915T000000Z",
        "uyelik_kipi": kip, "DURUM": "OLCULDU",
        "sabit_liste_kunyesi": kunye or {"kaynak": None, "n": None, "sha256": None,
                                         "kapsam_disi_n": None, "kapsam_disi_oran": None,
                                         "kapsam_disi_ornek": [], "neden": "kip sabit değil"},
        "kosumlar": {"dahil": {"DURUM": "OLCULDU", "bacaklar": {
            "i_ust20_kohort_fazlasi": {"10": _bacak(i20 / 2, i20_anlamli),
                                       "20": _bacak(i20, i20_anlamli)},
            "ii_a1_kova_tabanli_fazla": {"10": _bacak(a1_20 / 2, False),
                                         "20": _bacak(a1_20, False)},
            "ii_b_artik_ic_fazla": {"10": _bacak(iib_20 / 2, iib_anlamli, "ic"),
                                    "20": _bacak(iib_20, iib_anlamli, "ic")},
        }}},
    }


def _pk1_referans(i20, a1_20, iib_20):
    """EDG-093 sonucunun PK-1 detay bloğu — A kipinin karşılaştırıldığı ALTI bacak."""
    detay = []
    for bacak, d20 in (("i_ust20_kohort_fazlasi", i20),
                       ("ii_a1_kova_tabanli_fazla", a1_20),
                       ("ii_b_artik_ic_fazla", iib_20)):
        for h, v in (("10", d20 / 2), ("20", d20)):
            detay.append({"bacak": bacak, "ufuk": h, "pk1_deger": v, "edg016_deger": v,
                          "yon_esit": True, "pk1_anlamli": True, "edg016_anlamli": True,
                          "ci0_disi_esit": True})
    return {"kart": "EDG-2026-093", "damga_utc": "20260914T191231Z",
            "pk": {"pk1": {"kosdu": True, "detay": detay}}}


@pytest.fixture
def kiyas_cikti(tmp_path, sandbox_state):
    """Üç kip sonucu + PK-1 referansı; A kipi PK-1'den 1e-5 AYRIŞIR (kill-list tetiği)."""
    ref_i, ref_a1, ref_iib = 0.006211, 0.004406, 0.0084
    yollar = {}
    (tmp_path / "asof.json").write_text(json.dumps(
        _sonuc("asof", ref_i + 1e-5, ref_a1, ref_iib), ensure_ascii=False), encoding="utf-8")
    (tmp_path / "guncel.json").write_text(json.dumps(
        _sonuc("guncel", 0.0062, 0.0055, 0.02, True), ensure_ascii=False), encoding="utf-8")
    # C kipi BİLEREK B ile AYNI büyüklükte (0,02) ama CI-0-İÇİ: eşiğin İKİ koşulu (büyüklük VE
    # CI-0-dışılık) ancak böyle ayrı ayrı ısırılır — yalnız büyüklüğe bakan bir mutasyon C'yi
    # "geçti" sayar ve T7e kırılır.
    (tmp_path / "sabit.json").write_text(json.dumps(
        _sonuc("sabit", 0.0061, 0.0051, 0.02, False,
               kunye={"kaynak": "sınav", "n": 20, "sha256": "0" * 64, "kapsam_disi_n": 1,
                      "kapsam_disi_oran": 0.05, "kapsam_disi_ornek": ["ZZA"], "neden": None}),
        ensure_ascii=False), encoding="utf-8")
    (tmp_path / "pk1.json").write_text(json.dumps(
        _pk1_referans(ref_i, ref_a1, ref_iib), ensure_ascii=False), encoding="utf-8")
    for ad in ("asof", "guncel", "sabit", "pk1"):
        yollar[ad] = tmp_path / f"{ad}.json"
    yollar["cikti"] = tmp_path / "cikti096"
    return yollar


@pytest.fixture
def kiyas_sonucu(kiyas_cikti, k096_modul):
    rc = k096_modul.main([
        "--asof", str(kiyas_cikti["asof"]), "--guncel", str(kiyas_cikti["guncel"]),
        "--sabit", str(kiyas_cikti["sabit"]), "--pk1-referans", str(kiyas_cikti["pk1"]),
        "--kart", str(KART096), "--cikti", str(kiyas_cikti["cikti"])])
    assert rc == 0
    jsonlar = sorted(kiyas_cikti["cikti"].glob("sonuc_096_*.json"))
    assert len(jsonlar) == 1, f"tek sonuç json beklendi: {jsonlar}"
    return json.loads(jsonlar[0].read_text(encoding="utf-8"))


def test_T7a_ESIKLER_KARTTAN_OKUNUR_KOPYA_YOK(kiyas_sonucu):
    """Eşikler KARTIN `esikler` bloğundan okunur — betiğe GÖMÜLÜ eşik olsaydı kart değiştiğinde
    iki kaynak sessizce ayrışırdı (tek-kaynak yasası). Kıyas kartın KENDİSİNDEN yapılır."""
    import yaml
    kart = yaml.safe_load(KART096.read_text(encoding="utf-8"))
    e = kiyas_sonucu["esikler"]
    assert set(e) == set(kart["esikler"]), f"eşik kümesi ayrıştı: {sorted(e)}"
    for ad, deger in kart["esikler"].items():
        assert e[ad]["esik"] == deger, f"{ad} eşiği karttan okunmamış: {e[ad]['esik']}"
    assert e["ii_b_artik_ic_20g_alt"]["esik"] == 0.015
    assert e["a_kipi_pk1_tutarlilik_tol"]["esik"] == 0.000001
    assert e["katman_i_pk_20g_alt"]["esik"] == 0.003
    assert e["olculemeyen_sabit_liste_ust_oran"]["esik"] == 0.20


def test_T7b_TABLO_UC_KIP_UC_BACAK_IKI_UFUK(kiyas_sonucu):
    """Tablo kip × bacak × ufuk = 3 × 3 × 2 = 18 satır ve her satır değer + CI + CI-0-dışılık
    taşır — Rol-1 hükmü bu tablodan okur."""
    t = kiyas_sonucu["tablo"]
    assert len(t) == 18, f"tablo {len(t)} satır"
    assert {r["kip"] for r in t} == {"asof", "guncel", "sabit"}
    assert {r["bacak"] for r in t} == {"i_ust20_kohort_fazlasi", "ii_a1_kova_tabanli_fazla",
                                       "ii_b_artik_ic_fazla"}
    for r in t:
        assert set(r) >= {"kip", "bacak", "ufuk", "deger", "ci", "ci0_disi"}
        assert r["ufuk"] in ("10", "20")


def test_T7c_A_KIPI_PK1_KAPISI_AYRISMAYI_YAKALAR(kiyas_sonucu):
    """A kipi PK-1 detayıyla ALTI bacakta karşılaştırılır; fikstürde 1e-5 fark vardır ve
    tolerans 1e-6'dır → kapı DÜŞER. Düşmeseydi bozuk bir kod yolundan sayı yayılırdı."""
    kapi = kiyas_sonucu["a_kipi_pk1_kapisi"]
    assert kapi["kiyaslanan_bacak_n"] == 6
    assert kapi["maks_mutlak_fark"] > 1e-6
    assert kapi["gecti"] is False
    assert kiyas_sonucu["esikler"]["a_kipi_pk1_tutarlilik_tol"]["gecti"] is False


def test_T7d_KILL_LIST_TETIGI_KARTIN_METNIYLE(kiyas_sonucu):
    """Tetiklenen kill-list kalemleri KARTIN KENDİ METNİYLE yazılır (kopya metin yok). A kipi
    ayrıştığı için "kod yolu bozuk" kalemi tetiklenmeli."""
    import yaml
    kart_kill = yaml.safe_load(KART096.read_text(encoding="utf-8"))["kill_list"]
    tetik = kiyas_sonucu["kill_list_tetik"]
    assert tetik, "A kipi ayrıştı ama hiçbir kill-list kalemi tetiklenmedi"
    metinler = [t["kalem"] for t in tetik]
    assert any("kod yolu bozuk" in m for m in metinler), metinler
    for m in metinler:
        assert m in kart_kill, f"kill-list metni kartta YOK (kopya yazılmış): {m}"


def test_T7e_B_KIPINDE_IIB_ESIGI_GECER(kiyas_sonucu):
    """B kipinde ii_b artık-IC @20 = 0,02 ve CI-0-dışı → kart eşiği (0,015) GEÇER. C kipi AYNI
    büyüklüktedir ama CI-0-İÇİdir ve GEÇMEMELİDİR — eşiğin iki koşulu (büyüklük VE CI-0-dışılık)
    böyle ayrı ayrı ölçülür; yalnız büyüklüğe bakan bir mutasyon burada kırılır."""
    e = kiyas_sonucu["esikler"]["ii_b_artik_ic_20g_alt"]
    assert e["gecti"] is True, e
    assert e["deger"] == 0.02
    detay = {d["kip"]: d for d in e["detay"]}
    assert detay["guncel"]["gecti"] is True
    assert detay["sabit"]["ic"] == 0.02 and detay["sabit"]["ci0_disi"] is False
    assert detay["sabit"]["gecti"] is False, "C kipi CI-0-içi — geçmemeli"


def test_T7f_OLCULEMEYEN_SABIT_LISTE_ORANI_KUNYEDEN(kiyas_sonucu):
    """Ölçülemeyen pay künyeden OKUNUR, yeniden hesaplanmaz (sayının kaynağı C koşumudur)."""
    e = kiyas_sonucu["esikler"]["olculemeyen_sabit_liste_ust_oran"]
    assert e["deger"] == 0.05 and e["gecti"] is True


def test_T7g_HUKUM_YOK_ve_RAPOR_YAZILIR(kiyas_sonucu, kiyas_cikti):
    """Ajan HÜKÜM VERMEZ: `hukum` alanı sabittir ve çıktıda hüküm sözcüğü kalıntısı olmaz.
    RAPOR okunabilir (okuyan: Rol-1 masası — Yasa 6)."""
    assert kiyas_sonucu["hukum"] == "YOK — Rol-1"
    assert "hukum_onerisi" not in kiyas_sonucu
    ham = json.dumps(kiyas_sonucu, ensure_ascii=False)
    for yasak in ("\"oneri\"", "SUCCESS —", "ARŞİV —"):
        assert yasak not in ham, f"çıktıda hüküm kalıntısı: {yasak}"
    raporlar = sorted(kiyas_cikti["cikti"].glob("RAPOR_096_*.md"))
    assert len(raporlar) == 1
    metin = raporlar[0].read_text(encoding="utf-8")
    for parca in ("**Hüküm:** YOK — Rol-1", "## Kip × bacak tablosu", "## Kart eşikleri",
                  "## Kill-list tetikleri"):
        assert parca in metin, f"RAPOR'da eksik bölüm: {parca}"


def test_T7h_GIRDI_SHA_ve_EKSIK_GIRDI_UYDURULMAZ(k096_modul, kiyas_cikti):
    """Girdi damgası sha taşır; EKSİK kip sessizce "ölçüldü" sayılmaz — değer None + neden."""
    rc = k096_modul.main([
        "--asof", str(kiyas_cikti["asof"]), "--pk1-referans", str(kiyas_cikti["pk1"]),
        "--kart", str(KART096), "--cikti", str(kiyas_cikti["cikti"])])
    assert rc == 0
    sonuc = json.loads(sorted(kiyas_cikti["cikti"].glob("sonuc_096_*.json"))[-1]
                       .read_text(encoding="utf-8"))
    assert sonuc["kipler"]["guncel"]["okundu"] is False
    assert sonuc["kipler"]["guncel"]["neden"]
    assert sonuc["esikler"]["ii_b_artik_ic_20g_alt"]["gecti"] is None
    assert sonuc["esikler"]["olculemeyen_sabit_liste_ust_oran"]["deger"] is None
    assert sonuc["girdi_damgasi"]["asof"]["sha256"]
    assert len(sonuc["girdi_damgasi"]["asof"]["sha256"]) == 64
    assert sonuc["girdi_damgasi"]["guncel"]["sha256"] is None
    assert sonuc["girdi_damgasi"]["guncel"]["neden"]
    # OKUNMAYAN KİP TABLODAN DÜŞMEZ: satırı None + NEDEN ile durur. Düşseydi tablo "iki kip
    # ölçüldü" demek yerine "üçüncü kip hiç yoktu" der ve eksiklik sessizleşirdi (bedel yasası).
    assert len(sonuc["tablo"]) == 18, f"okunmayan kip tablodan düşmüş: {len(sonuc['tablo'])}"
    bos = [r for r in sonuc["tablo"] if r["kip"] == "sabit"]
    assert len(bos) == 6 and all(r["deger"] is None and r["neden"] for r in bos)


def test_T7i_MERIDIAN_ITHAL_EDILMEZ(k096_modul):
    """Karşılaştırma betiği yalnız stdlib + yaml kullanır: `meridian` ithal etseydi canlı
    yapılandırmayı (ve `obs` yolunu) bir ölçüm aracına bağlardı (CLAUDE.md §2)."""
    import ast
    agac = ast.parse(KARSILASTIR.read_text(encoding="utf-8"), str(KARSILASTIR))
    ithal = set()
    for d in ast.walk(agac):
        if isinstance(d, ast.Import):
            ithal |= {a.name.split(".")[0] for a in d.names}
        elif isinstance(d, ast.ImportFrom) and d.module:
            ithal.add(d.module.split(".")[0])
    assert "meridian" not in ithal, f"meridian ithal edilmiş: {sorted(ithal)}"
    assert ithal <= {"argparse", "datetime", "hashlib", "json", "pathlib", "sys", "yaml",
                     "__future__"}, f"beklenmedik ithal: {sorted(ithal)}"
