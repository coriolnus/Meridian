"""v607 — EXE-2026-012 B dilimi: HÜKÜM BETİĞİ + uçtan uca POZİTİF KONTROLLER (TSK-020 UYGULA-9 Faz C, 2026-10-01).

KART-ÖNCE: kart `research/cards/EXE-2026-012-kill1-canli-capa.yaml` 2e00cf2d'de ön-kayıtlı; betik
`research/olcumler/exe012_kill1_canli/hukum.py` ve bu dosya ondan SONRA yazıldı. Kartın eşik/kill/hüküm alanlarına bu
dosya dokunmaz; eşikleri betik KARTTAN okur (I bölümü bunu çiviler).

BÖLÜMLER:
  A  ortak yardımcılar (`meridian.olcum_araclari`): p95 v217 `_p95` ile BAYT-EŞİT ve TEK tanım (v217 artık onu
     içe aktarır); küme bootstrap çekirdeği `faz5_cikis.tarih_kumeli_bootstrap` ile PAYLAŞIMLI (altın değerler
     değişmedi); betikte ikinci gövde yok.
  B  defter okuma: (seans, surec_baslangic, pid) birleştirmesi, bozuk (yarım) satır, şema ihlali → GEÇERSİZ.
  C  temiz seans süzgeci: seans içi yeniden başlatma (eşik saati KARTTA YOK → Rol-1 parametresi, iki aday raporlanır),
     seans ortası `kapanis` = kısmi seans, defteri olmayan seans günü, pencere = ilk N temiz seans.
  D  üçlü hüküm: tavan tam 1,10 / CI tam 1,10 sınırları; n alt sınırları (pencere, yazım) → ÖLÇÜLEMEDİ; evren yalnız
     processed; geçerlilik katmanı üçlünün ÜSTÜNDE; bootstrap SEANS-kümeli (olay düzeyi değil).
  E  seans tanığı: le kuralı (motorun kendi `gecikme.Histogram`ı — bisect_left), tanıksız / kusurlu ayrımı, sayaç
     sıfırlanması, kusurlu seansın hükmü durdurması.
  F  tanılar t1–t6 (hüküm üretmez).
  G  PK-1 / PK-2 / NK / PK-3 — gerçek `IntradayConsumer.on_barfeed_event` → gerçek planli dal → gerçek alet → gerçek
     seans sonu defter yazımı → betiğin KENDİSİ (CLI `main`) → hüküm; tanık eşi (DONGU_SURESI kesitlerinden dışa aktarım).
  H  betik `meridian.obs`a ULAŞMAZ: statik içe-aktarma kapanışı + operatörün koşacağı biçimde alt süreç (`-X importtime`).
  I  kart ve alet bağı: eşikler karttan; alan / boşaltma sözlüğü / şema aletle ayrışmaz; Yasa 6 beyanı okuyucuyu adlandırır.
  J  ADIM-0 a/b/c hesapları + tanık planı (DST).

SAHTE SAAT (G) — kart netleştirmesi 2026-10-01b (`netlestirme_2026_10_01b`, Rol-1; dal sonu inceleme I-3(a)): kartın
"meşgul-bekleme" deseni yerine `gecikme._saat` her okumada `ADIM_S` ilerleyen SANAL saattir; süreler yalnız enjekte edilen gecikmelerden
ve okuma adımlarından oluşur → PK hükümleri makine yükünden BAĞIMSIZ ve deterministiktir (gerçek uyku YOK). Canlıda var
olan Redis okuması testte yoktur; sembol başına tohumlu bir sanal okuma süresi eklenir (Y'ye gerçekçi bir dağılım verir).
Aletin GERÇEK saat maliyeti v606 G1'dedir.

BAĞIMLILIK BEYANI: v217 sahne yardımcıları (`_kapilar_olculebilir`, `_plan`, `_bar`) ve v606'nın kilit yoklaması
(`kilit_yeniden_girisli_yoklamasi`) bilerek içe aktarılır — kopya ikinci kaynak olurdu.

TUR 2 (dal sonu inceleme 0C/3I/3M, 2026-10-01; kart netleştirmeleri 2026-10-01 + 2026-10-01b):
  I-1  hüküm yolunda yeniden başlatma eşiği SABİT `acilis` (09:30 ET, kart netleştirme (1)); `pencere` REDDEDİLİR (rc 2,
       açık ileti), yalnız `esik_duyarliligi` TANISINDA kalır (C1, C2, I4).
  I-2  hüküm yolunda tanık ZORUNLU; bilinçli kaçış `--taniksiz` çıktının BAŞINDA `taniksiz` + `tanik_ozeti` ile (E4, E2).
  I-3  PK-1 gecikmesi olay başına planli giriş sayısına BÖLÜNÜR (olay başı toplam %20 → R ≈ 1,20, "tavanın iki katı");
       PK-2 aynı TOPLAMI dal dışına (silahlı dal, olay başına bir kez) (G1, G2).
  M-1  RLock → Lock gerilemesinde PK'ler ASILMAZ: v606'nın yoklaması bu dosyada da autouse.
  M-3  şema denetimi negatif `z_s`'yi ve `planli_yazim > planli_giris`'i reddeder (B3).

Bu dosya `state/`e yalnız `sandbox_state` üzerinden dokunur, ağa çıkmaz. Numara v607: ana checkout + beş worktree'de boş
(ölçüldü 2026-10-01; v606 alet).
"""
from __future__ import annotations

import ast
import datetime as dt
import json
import os
import pathlib
import random
import re
import subprocess
import sys

import pytest
import yaml

from meridian import barclock as bc, codelaw, faz5_cikis as f5, gecikme, intraday_cycle as ic, \
    intraday_shadow as ish, olcum_araclari as oa, store
from tests.conftest import betikten_modul_yukle
from tests.test_exe012_alet_v606 import kilit_yeniden_girisli_yoklamasi
from tests.test_golge_planli_kol_v217 import _bar, _kapilar_olculebilir, _plan
import tests.test_golge_planli_kol_v217 as v217

KOK = pathlib.Path(__file__).resolve().parent.parent
BETIK = KOK / "research" / "olcumler" / "exe012_kill1_canli" / "hukum.py"
KART = KOK / "research" / "cards" / "EXE-2026-012-kill1-canli-capa.yaml"
UTC = dt.timezone.utc
SUREC_ONCESI = "2026-07-31T20:00:00+00:00"          # bütün test seanslarının açılışından ÖNCE başlamış süreç
PID = 4242


@pytest.fixture(autouse=True)
def _temiz():
    """Tüketici tekil, saat ve tekilleştirme modül-genelidir — testler arasına sızmasın (v217/v606 deseni)."""
    ic._CONSUMER = None
    ic.reset_plans_cache()
    ish.reset_dedup()
    yield
    bc.reset_clock()
    ic._CONSUMER = None
    ic.reset_plans_cache()
    ish.reset_dedup()


@pytest.fixture(autouse=True)
def _kilit_yeniden_girisli():
    """Dal sonu inceleme M-1: PK'ler her seans sonunda `_atif_kaydet` → `_atif_bosalt` (aynı kilit) yolunu koşar; RLock → Lock
    gerilemesinde ana iş parçacığı ölü kilide girerdi (pytest-timeout yok). v606'nın bloklamayan yoklaması burada da
    her testten ÖNCE koşar — gerileme varsa test asılmadan düşer."""
    kilit_yeniden_girisli_yoklamasi()
    yield


@pytest.fixture(scope="module")
def m():
    """Betiğin KENDİSİ — kaynaktan derlenir (bayat pyc tuzağı yok, v334)."""
    return betikten_modul_yukle(BETIK)


# ---- yardımcılar -------------------------------------------------------------------------------------------------

def _et(gun: str, saat: int, dakika: int = 0, saniye: int = 0) -> dt.datetime:
    """ET duvar saati → UTC (DST zoneinfo'dan)."""
    y, a, g = (int(p) for p in gun.split("-"))
    return dt.datetime(y, a, g, saat, dakika, saniye, tzinfo=bc.NY).astimezone(UTC)


def _seans_gunleri(bas: str, n: int) -> list[str]:
    """XNYS seans günleri (barclock takvimi — tek takvim yolu)."""
    out, d = [], dt.date.fromisoformat(bas)
    while len(out) < n:
        if bc.seans_araligi(d.isoformat())[0] == "ok":
            out.append(d.isoformat())
        d += dt.timedelta(days=1)
    return out


GUNLER = _seans_gunleri("2026-08-03", 24)            # Ağustos 2026: tatil yok


def _olay(outcome="processed", x=1.0, z=0.0, ofset=0.0, giris=0, yazim=0) -> list:
    """Defter olayı — alan sırası ALETİN tek kaynağından (`ic.ATIF_ALANLARI`)."""
    d = {"outcome": outcome, "x_s": x, "z_s": z, "ofset_s": ofset, "planli_giris": giris, "planli_yazim": yazim}
    return [d[a] for a in ic.ATIF_ALANLARI]


def _satir(seans: str, olaylar: list, *, surec: str = SUREC_ONCESI, pid: int = PID, bosaltma: str = "seans_kapandi",
           yazim_ts: str | None = None) -> dict:
    """Aletin yazdığı satırın biçimi (`IntradayConsumer._atif_bosalt`) — elle kurulmuş girdi için."""
    return {"kart": "EXE-2026-012", "sema": 1, "seans": seans, "surec_baslangic": surec, "pid": pid,
            "bosaltma": bosaltma, "yazim_ts": yazim_ts or _et(seans, 16, 30).isoformat(),
            "alanlar": list(ic.ATIF_ALANLARI), "n": len(olaylar), "olaylar": olaylar}


def _defter_yaz(yol: pathlib.Path, satirlar: list, ham: tuple = ()) -> pathlib.Path:
    with open(yol, "w", encoding="utf-8") as f:
        for s in satirlar:
            f.write(json.dumps(s) + "\n")
        for h in ham:
            f.write(h)
    return yol


def _duz_seans(seans: str, *, n: int = 20, x: float = 1.0, y: float = 1.0, yazim_ilk: int = 1, **kw) -> dict:
    """n olaylı düz seans: hepsi X=x, Y=y (Z = x − y TAM: Sterbenz), ilk olay `yazim_ilk` planli satır yazar."""
    z = x - y
    olaylar = [_olay(x=x, z=z, ofset=60.0 * i, giris=1, yazim=(yazim_ilk if i == 0 else 0)) for i in range(n)]
    return _satir(seans, olaylar, **kw)


def _hukum(m, tmp_path, satirlar, *, ham=(), baslangic=None, **kw) -> dict:
    """Tanık verilmeyen birim çivilerinde bilinçli kaçış `taniksiz=True` (I-2: hüküm yolunda tanık zorunlu)."""
    if kw.get("tanik_yolu") is None:
        kw["taniksiz"] = True
    yol = _defter_yaz(tmp_path / "defter.jsonl", satirlar, ham)
    return m.hukum(yol, baslangic=baslangic or GUNLER[0], **kw)


def _seans(sonuc: dict, gun: str) -> dict:
    return next(s for s in sonuc["seanslar"] if s["seans"] == gun)


def _kodlar(sonuc: dict) -> set:
    return {n["kod"] for n in sonuc["hukum"]["nedenler"]}


# =================================================================================================================
# A — ortak yardımcılar: p95 TEK tanım, küme bootstrap TEK gövde
# =================================================================================================================

def _v217_eski_p95(vals):
    """v217'nin 2026-10-01 ÖNCESİ gövdesi — DONUK KIYAS REFERANSI (yalnız bayt-eşitlik kanıtı; üretimde kullanılmaz)."""
    s = sorted(vals)
    return s[min(len(s) - 1, int(round(0.95 * (len(s) - 1))))]


def test_A1_p95_v217_ile_BAYT_ESIT_ve_TEK_tanim(m):
    rng = random.Random(607)
    for n in range(1, 420):
        vals = [rng.choice((rng.random(), 0.5, 1e-3)) for _ in range(n)]       # eşitler (bağlar) dahil
        assert oa.p95(vals) is _v217_eski_p95(vals), f"n={n}: ortak p95 v217 tanımından AYRIŞTI"
        assert oa.sirali_kantil(vals, 0.95) is _v217_eski_p95(vals)
    assert v217._p95 is oa.p95, "v217 p95'i kendi kopyasıyla tanımlıyor — tek tanım ortak yardımcıda"
    assert m.p95 is oa.p95 and m.sirali_kantil is oa.sirali_kantil, "betik p95'i ortak yardımcıdan almıyor"
    # İKİNCİ GÖVDE YOK: betikte kantil indeksi hesaplanmaz (round çağrısı yok), p95/kantil fonksiyonu tanımlanmaz.
    agac = ast.parse(BETIK.read_text(encoding="utf-8"))
    tanimlar = {d.name for d in ast.walk(agac) if isinstance(d, ast.FunctionDef)}
    assert not tanimlar & {"p95", "_p95", "sirali_kantil", "kantil_indeksi", "kantil"}, tanimlar
    roundlar = [d for d in ast.walk(agac) if isinstance(d, ast.Call) and isinstance(d.func, ast.Name)
                and d.func.id == "round"]
    assert roundlar == [], "betik kantil indeksini kendisi hesaplıyor (round) — kopya"
    assert oa.kantil_indeksi(1, 0.95) == 0 and oa.kantil_indeksi(400, 0.95) == 379


def _altin_girdiler():
    """faz5 altın değerlerinin girdileri — paylaşımdan ÖNCE yakalandı (scratchpad b_altin, 2026-10-01)."""
    out = [("ikiz6", [12.0, -4.0, 7.0, -9.0, 3.0, 15.0], [f"2026-08-0{i + 1}" for i in range(6)], {})]
    r = random.Random(20261001)
    deg, tar = [], []
    for g in range(12):
        etki = r.gauss(0.0, 1.0)
        for _ in range(10):
            deg.append(etki + r.gauss(0.0, 0.1))
            tar.append(f"g{g:02d}")
    out.append(("kume12", deg, tar, {}))
    out.append(("kume12_b400", deg, tar, {"n_ornek": 400, "seviye": 0.9, "tohum": 7}))
    deg2, tar2 = [], []
    for g in range(7):
        for _ in range(1 + 3 * g):
            deg2.append(r.uniform(-50, 80))
            tar2.append(f"2026-09-{10 + g}")
    deg2.append(None)
    tar2.append("2026-09-10")
    out.append(("dengesiz7", deg2, tar2, {}))
    return out


ALTIN = {"dengesiz7": {"B": 10000, "hi": "20.536265904459288", "lo": "6.775725270078893", "n": 70,
                       "ort": "12.371496394672754"},
         "ikiz6": {"B": 10000, "hi": "10.666666666666666", "lo": "-2.8333333333333335", "n": 6, "ort": "4.0"},
         "kume12": {"B": 10000, "hi": "0.19657357810027035", "lo": "-0.9320639953172288", "n": 120,
                    "ort": "-0.39726025351734756"},
         "kume12_b400": {"B": 400, "hi": "0.10992601508973357", "lo": "-0.8584888155336996", "n": 120,
                         "ort": "-0.39726025351734756"}}


def test_A2_faz5_kume_bootstrap_ALTIN_degerleri_paylasimdan_sonra_DEGISMEDI():
    """Çekirdek ortak yardımcıya taşındı; faz5'in (dolayısıyla intraday_shadow ikincil hattı, skill_gorus, EDG-019
    betiği) yayımladığı aralık BAYT-EŞİT kalmalı."""
    for ad, d, t, kw in _altin_girdiler():
        c = f5.tarih_kumeli_bootstrap(d, t, **kw)
        bulunan = {"lo": repr(c["lo"]), "hi": repr(c["hi"]), "ort": repr(c["ort"]), "B": c["B"], "n": c["n"]}
        assert bulunan == ALTIN[ad], f"{ad}: faz5 bootstrap çıktısı değişti {bulunan} ≠ {ALTIN[ad]}"


def test_A3_bootstrap_GOVDESI_tek_kopya_yok(m, monkeypatch):
    f5_src = (KOK / "meridian" / "faz5_cikis.py").read_text(encoding="utf-8")
    assert "kume_bootstrap(" in f5_src and "default_rng" not in f5_src and "np.percentile" not in f5_src, \
        "faz5 yeniden örnekleme gövdesini kendisi taşıyor — çekirdek ortak yardımcıda"
    betik_src = BETIK.read_text(encoding="utf-8")
    for yasak in ("default_rng", "np.percentile", ".integers(", "def tarih_kumeli_bootstrap", "def kume_bootstrap"):
        assert yasak not in betik_src, f"betikte ikinci bootstrap gövdesi: {yasak}"
    # Çağrı ÇALIŞMA ANINDA da ortak çekirdeğe gider (faz5 ve betik aynı nesneyi çağırır).
    cagrilar = []
    ozgun = oa.kume_bootstrap

    def casus(g, istatistik, **kw):
        cagrilar.append((g, kw))
        return ozgun(g, istatistik, **kw)

    monkeypatch.setattr(oa, "kume_bootstrap", casus)
    f5.tarih_kumeli_bootstrap([1.0, 2.0, 3.0], ["a", "b", "c"], n_ornek=50)
    assert cagrilar and cagrilar[-1][0] == 3
    assert "kume_bootstrap" in oa.ARAC_SURUMLERI and "p95" in oa.ARAC_SURUMLERI


# =================================================================================================================
# B — defter okuma
# =================================================================================================================

def test_B1_birlestirme_anahtari_SEANS_SUREC_PID(m, tmp_path):
    """Aynı süreç bir seansa birden çok satır yazabilir (takvim fail-closed ara `seans_kapandi`, kapanış kuyruğu): satırlar
    (seans, surec_baslangic, pid) ile BİRLEŞİR. Başka süreç (aynı seans) ayrı süreç kaydıdır."""
    g = GUNLER[0]
    s1 = _satir(g, [_olay(x=1.0, ofset=1.0), _olay(x=1.0, ofset=2.0)], yazim_ts=_et(g, 12, 0).isoformat())
    s2 = _satir(g, [_olay(x=1.0, ofset=3.0)])
    s3 = _satir(g, [_olay(outcome="error", x=0.5, ofset=0.5)], pid=999, surec="2026-07-30T10:00:00+00:00")
    satirlar = m.defter_oku(_defter_yaz(tmp_path / "d.jsonl", [s1, s2, s3]))
    kayitlar = m.surec_seanslari(satirlar["satirlar"])
    assert set(kayitlar) == {(g, SUREC_ONCESI, PID), (g, "2026-07-30T10:00:00+00:00", 999)}
    k = kayitlar[(g, SUREC_ONCESI, PID)]
    assert len(k["olaylar"]) == 3 and k["bosaltmalar"] == ["seans_kapandi", "seans_kapandi"]
    sonuc = _hukum(m, tmp_path, [s1, s2, s3])
    s = _seans(sonuc, g)
    assert len(s["surecler"]) == 2 and s["n_processed"] == 3 and s["n_error"] == 1


def test_B2_bozuk_YARIM_satir_ayiklanir_seansi_EKSIK_sayilir(m, tmp_path):
    """SIGKILL yazımın ortasında keserse son satır yarım kalır (beyan): okuyucu onu ayıklar, seansı EKSİK sayar (adıyla),
    bütün ölçümü düşürmez."""
    g0, g1 = GUNLER[0], GUNLER[1]
    yarim = json.dumps(_duz_seans(g1))[:180] + "\n"
    sonuc = _hukum(m, tmp_path, [_duz_seans(g0)], ham=(yarim,))
    assert sonuc["girdi"]["defter"]["bozuk_satir"] == [{"satir_no": 2, "seans": g1}]
    assert _seans(sonuc, g1)["sinif"] == "eksik" and not _seans(sonuc, g1)["temiz"]
    assert _seans(sonuc, g0)["temiz"]
    assert sonuc["hukum"]["karar"] != m.GECERSIZ


def test_B3_sema_disi_satir_HUKMU_GECERSIZ_kilar(m, tmp_path):
    """Okuyucu ile yazar ayrışmışsa (kart kimliği, şema sürümü, alan adları, n ≠ olay sayısı) hiçbir sayı yorumlanmaz."""
    for bozma in ({"kart": "EXE-2026-099"}, {"sema": 2}, {"alanlar": ["outcome", "x_s"]}, {"n": 99},
                  {"bosaltma": "bilinmeyen"}):
        satirlar = [_duz_seans(g) for g in GUNLER[:20]]
        satirlar[3] = {**satirlar[3], **bozma}
        sonuc = _hukum(m, tmp_path, satirlar)
        assert sonuc["hukum"]["karar"] == m.GECERSIZ and "defter_semasi" in _kodlar(sonuc), bozma
    # Dal sonu inceleme M-3: aletin DEĞİŞMEZLERİ (monoton saat → Z ≥ 0; yazım sayacı girişin alt kümesi) de şemadır.
    # Z < 0 → Y > X → R aşağı (YEŞİL yönü) — "Tek kaynak" GEÇERSİZ maddesine Y ≤ 0 sınaması yakalamaz.
    for olay, parca in ((_olay(x=1.0, z=-0.001, giris=1), "z_s"), (_olay(x=1.0, z=0.1, giris=1, yazim=2), "planli_yazim")):
        satirlar = [_duz_seans(g) for g in GUNLER[:20]]
        satirlar[5]["olaylar"][7] = olay
        sonuc = _hukum(m, tmp_path, satirlar)
        assert sonuc["hukum"]["karar"] == m.GECERSIZ and "defter_semasi" in _kodlar(sonuc), parca
        assert sonuc["girdi"]["defter"]["sema_ihlali"][0]["neden"].startswith(parca), sonuc["girdi"]["defter"]


# =================================================================================================================
# C — temiz seans süzgeci
# =================================================================================================================

def test_C1_seans_ici_YENIDEN_BASLATMA_esigi_ACILIS_pencere_yalniz_TANI(m, tmp_path):
    """Kart netleştirme (1): süreç başlangıcı seans AÇILIŞINDAN (09:30 ET) sonra ise seans temiz DEĞİL. 09:45 giriş
    penceresi yorumu daha gevşek (09:30–09:45 arası yeniden başlatılan seansı temiz sayar → pencere geçme yönünde dolar)
    ve SEÇİLMEDİ; hükümde eşik sabittir. İki adayın karşılaştırması yalnız TANIDIR (`esik_duyarliligi`)."""
    g0, g1, g2 = GUNLER[:3]
    satirlar = [_duz_seans(g0, surec=_et(g0, 9, 40).isoformat()),             # 09:30–09:45 arası: adaylar ayrışır
                _duz_seans(g1, surec=_et(g1, 11, 0).isoformat()),             # pencere içi: iki adayda da yeniden başlatma
                _duz_seans(g2, surec=(_et(g2, 9, 30) - dt.timedelta(hours=14)).isoformat())]   # önceki akşam: temiz
    sonuc = _hukum(m, tmp_path, satirlar)
    assert _seans(sonuc, g0)["sinif"] == "yeniden_baslatma" and not _seans(sonuc, g0)["temiz"], \
        "09:40'ta başlamış süreç: kartın açılış eşiğiyle seans temiz DEĞİL"
    assert _seans(sonuc, g1)["sinif"] == "yeniden_baslatma" and _seans(sonuc, g2)["temiz"]
    assert _seans(sonuc, g0)["yeniden_baslatma"] == {"acilis": True, "pencere": False}
    assert sonuc["parametreler"]["yeniden_baslatma_esigi"] == "acilis" == m.YENIDEN_BASLATMA_ESIGI
    tani = sonuc["esik_duyarliligi"]
    assert tani["hukum_esigi"] == "acilis" and tani["ayrisan_seanslar"] == [g0] and "TANI" in tani["not"]


def test_C2_hukumde_PENCERE_esigi_REDDEDILIR_acik_ileti(m, tmp_path, capsys):
    yol = _defter_yaz(tmp_path / "d.jsonl", [_duz_seans(GUNLER[0])])
    temel = ["hukum", "--defter", str(yol), "--baslangic", GUNLER[0], "--taniksiz"]
    assert m.main(temel + ["--yeniden-baslatma-esigi", "pencere"]) == 2
    hata = capsys.readouterr().err
    assert "acilis" in hata and "netleştirme" in hata and "pencere" in hata, hata
    assert m.main(temel + ["--yeniden-baslatma-esigi", "acilis", "--cikti", str(tmp_path / "a.json")]) == 0
    assert m.main(temel + ["--cikti", str(tmp_path / "b.json")]) == 0, "eşik verilmezse kartın eşiği (acilis)"
    with pytest.raises(TypeError):
        m.hukum(yol, baslangic=GUNLER[0], taniksiz=True, esik_adi="pencere")     # API'de eşik parametresi YOK


def test_C3_seans_ortasi_KAPANIS_kismi_seanstir_kapanis_sonrasi_degil(m, tmp_path):
    g0, g1 = GUNLER[:2]
    satirlar = [_duz_seans(g0, bosaltma="kapanis", yazim_ts=_et(g0, 13, 0).isoformat()),
                _duz_seans(g1, bosaltma="kapanis", yazim_ts=_et(g1, 18, 0).isoformat())]
    sonuc = _hukum(m, tmp_path, satirlar)
    assert _seans(sonuc, g0)["sinif"] == "kismi" and not _seans(sonuc, g0)["temiz"]
    assert _seans(sonuc, g1)["temiz"], "akşam dağıtımının kapanış satırı tam seanstır"


def test_C4_defteri_olmayan_SEANS_GUNU_adiyla_duser_ve_pencere_ILK_N_temiz(m, tmp_path):
    satirlar = [_duz_seans(g) for g in GUNLER[:23] if g != GUNLER[2]]
    satirlar[5] = _duz_seans(GUNLER[6], surec=_et(GUNLER[6], 12, 0).isoformat())   # yeniden başlatma
    sonuc = _hukum(m, tmp_path, satirlar)
    assert _seans(sonuc, GUNLER[2])["sinif"] == "defter_yok"
    p = sonuc["pencere"]
    assert p["dolu"] and p["hedef"] == 20 and p["n_temiz"] == 20
    assert p["seanslar"] == [g for g in GUNLER[:22] if g not in (GUNLER[2], GUNLER[6])]
    assert {(d["seans"], d["sinif"]) for d in p["dusenler"]} == {(GUNLER[2], "defter_yok"),
                                                                  (GUNLER[6], "yeniden_baslatma")}
    assert p["sonrasi_n"] == 1
    iki = _hukum(m, tmp_path, satirlar, bakis=2)
    assert iki["pencere"]["hedef"] == 40 and not iki["pencere"]["dolu"]
    assert "pencere_dolmadi" in _kodlar(iki)


def test_C5_pencere_baslangictan_ONCEKI_seansi_saymaz(m, tmp_path):
    satirlar = [_duz_seans(g) for g in GUNLER[:21]]
    sonuc = _hukum(m, tmp_path, satirlar, baslangic=GUNLER[1])
    assert sonuc["pencere"]["seanslar"] == GUNLER[1:21] and _seans(sonuc, GUNLER[0])["konum"] == "pencere_oncesi"


# =================================================================================================================
# D — üçlü hüküm
# =================================================================================================================

def test_D1_uclu_hukum_SINIRLARI_pay_YOK(m):
    t = 1.10
    yukari = 1.1000000000000003
    assert m.uclu_hukum(t, t, t) == m.YESIL, "R tam tavan ∧ CI tam tavan → YEŞİL (≤)"
    assert m.uclu_hukum(yukari, 1.0, t) == m.KILL, "R tavanı en küçük farkla aşar → KILL (CI'ya bakılmaz)"
    assert m.uclu_hukum(t, yukari, t) == m.OLCULEMEDI, "CI üstü tavanı en küçük farkla aşar → ÖLÇÜLEMEDİ"
    assert m.uclu_hukum(1.5, None, t) == m.KILL
    assert m.uclu_hukum(1.0, None, t) == m.OLCULEMEDI, "CI yoksa YEŞİL denmez"


def test_D2_R_TAM_tavan_ve_CI_TAM_tavan_entegre_YESIL(m, tmp_path):
    satirlar = [_duz_seans(g, x=1.1, y=1.0) for g in GUNLER[:20]]
    h = _hukum(m, tmp_path, satirlar)["hukum"]
    assert h["r_nokta"] == 1.1 and h["ci"]["hi"] == 1.1 and h["tavan"] == 1.1
    assert h["karar"] == m.YESIL == h["uclu"] and h["nedenler"] == []
    assert h["ci"]["B"] == 10_000 and h["ci"]["n_kume"] == 20


def _yavas_seanslar(m_yavas: int = 10) -> list:
    """20 seans × 20 olay, Y hep 1,0; YALNIZ ilk seansta `m_yavas` olay X=1,12. Havuzda yavaş pay %2,5 < %5 → R = 1,0.
    SEANS-kümeli bootstrap ilk seansı ≥ 3 kez çektiğinde (≈ %7,5) havuzun p95'i 1,12'ye çıkar → CI üstü 1,12; olay
    düzeyinde (IID) yeniden örnekleme 21+ yavaş olayı neredeyse hiç toplamaz → CI üstü 1,0."""
    out = []
    for i, g in enumerate(GUNLER[:20]):
        olaylar = [_olay(x=(1.12 if (i == 0 and j < m_yavas) else 1.0), z=(1.12 - 1.0 if (i == 0 and j < m_yavas)
                                                                           else 0.0),
                         ofset=60.0 * j, giris=1, yazim=(1 if j == 0 else 0)) for j in range(20)]
        out.append(_satir(g, olaylar))
    return out


def test_D3_CI_genisse_OLCULEMEDI_ve_bootstrap_SEANS_kumeli(m, tmp_path, monkeypatch):
    cagrilar = []
    ozgun = oa.kume_bootstrap

    def casus(g, istatistik, **kw):
        cagrilar.append(g)
        return ozgun(g, istatistik, **kw)

    monkeypatch.setattr(oa, "kume_bootstrap", casus)
    h = _hukum(m, tmp_path, _yavas_seanslar())["hukum"]
    assert h["r_nokta"] == 1.0 and h["ci"]["hi"] == pytest.approx(1.12)
    assert h["karar"] == m.OLCULEMEDI == h["uclu"] and "ci_genis" in {n["kod"] for n in h["nedenler"]}
    assert cagrilar == [20], f"bootstrap birimi seans değil: küme sayısı {cagrilar}"


def test_D4_n_ALT_SINIRLARI_OLCULEMEDI(m, tmp_path):
    az = _hukum(m, tmp_path, [_duz_seans(g) for g in GUNLER[:19]])
    assert az["hukum"]["karar"] == m.OLCULEMEDI and "pencere_dolmadi" in _kodlar(az)
    yazim9 = [_duz_seans(g, yazim_ilk=(1 if i < 9 else 0)) for i, g in enumerate(GUNLER[:20])]
    s9 = _hukum(m, tmp_path, yazim9)
    assert s9["hukum"]["n_yazim_satir"] == 9 and "yazim_az" in _kodlar(s9) and s9["hukum"]["karar"] == m.OLCULEMEDI
    yazim10 = [_duz_seans(g, yazim_ilk=(1 if i < 10 else 0)) for i, g in enumerate(GUNLER[:20])]
    s10 = _hukum(m, tmp_path, yazim10)
    assert s10["hukum"]["n_yazim_satir"] == 10 and "yazim_az" not in _kodlar(s10)
    assert s10["hukum"]["karar"] == m.YESIL


def test_D5_evren_YALNIZ_processed(m, tmp_path):
    """`error` ve (alet yazmasa da) `skipped` olaylar havuza GİRMEZ: biri tavanı aşırır, öteki p95'i oynatır."""
    satirlar = []
    for g in GUNLER[:20]:
        olaylar = [_olay(x=1.0, z=0.0, ofset=60.0 * j, giris=1, yazim=(1 if j == 0 else 0)) for j in range(20)]
        olaylar += [_olay(outcome="error", x=3.0, z=1.5, ofset=2000.0 + j) for j in range(5)]
        olaylar += [_olay(outcome="skipped", x=2.0, z=1.0, ofset=3000.0 + j) for j in range(5)]
        satirlar.append(_satir(g, olaylar))
    h = _hukum(m, tmp_path, satirlar)["hukum"]
    assert h["r_nokta"] == 1.0 and h["n_olay"] == 400 and h["n_error"] == 100
    assert h["karar"] == m.YESIL


def test_D6_gecerlilik_UCLUNUN_USTUNDE(m, tmp_path):
    """Y ≤ 0 (Z, X'in dışına taşmış) → GEÇERSİZ. Yazım < 10 iken R tavanı aşsa da nihai ÖLÇÜLEMEDİ — ama üçlü KILL ve
    `tavan_asildi` adıyla görünür (kartın iki maddesinin çakışması Rol-1'e sayıyla gider)."""
    satirlar = [_duz_seans(g) for g in GUNLER[:20]]
    satirlar[4]["olaylar"][3] = _olay(x=1.0, z=1.0000001)
    g = _hukum(m, tmp_path, satirlar)["hukum"]
    assert g["karar"] == m.GECERSIZ and "z_x_disinda" in {n["kod"] for n in g["nedenler"]}
    kill = [_duz_seans(gg, x=1.5, y=1.0, yazim_ilk=0) for gg in GUNLER[:20]]
    k = _hukum(m, tmp_path, kill)["hukum"]
    assert k["uclu"] == m.KILL and k["tavan_asildi"] is True
    assert k["karar"] == m.OLCULEMEDI and {n["kod"] for n in k["nedenler"]} == {"yazim_az"}


# =================================================================================================================
# E — seans tanığı
# =================================================================================================================

LE = [*ic.DONGU_SURESI.kovalar, None]                  # None = +Inf


def _le_metni(le) -> str:
    return "+Inf" if le is None else repr(float(le))


def _tanik_yaniti(ornekler: dict, *, outcome="processed", ek_seriler=()) -> dict:
    """Prometheus `/api/v1/query_range` yanıtı (matrix). `ornekler`: {ts: [x listesi]} — sayım `x <= le` (BİRİKİMLİ)
    tanımından testte BAĞIMSIZ hesaplanır (bisect kullanılmaz)."""
    sonuc = []
    for le in LE:
        degerler = [[ts, str(sum(1 for x in xs if le is None or x <= le))] for ts, xs in sorted(ornekler.items())]
        sonuc.append({"metric": {"__name__": "meridian_intraday_cycle_seconds_bucket", "job": "meridian",
                                 "instance": "127.0.0.1:8080", "outcome": outcome, "le": _le_metni(le)},
                      "values": degerler})
    sonuc.extend(ek_seriler)
    return {"status": "success", "data": {"resultType": "matrix", "result": sonuc}}


def _tanik_yaz(yol, yanitlar) -> pathlib.Path:
    yol.write_text("".join(json.dumps(y) + "\n" for y in yanitlar), encoding="utf-8")
    return yol


SINIR_X = [0.002, 0.0025, 0.001, 0.005, 0.0075]        # üçü TAM kova sınırında (le kuralının sınandığı yer)


def _tanikli_satirlar():
    out = []
    for g in GUNLER[:20]:
        olaylar = [_olay(x=x, z=0.0, ofset=60.0 * j, giris=1, yazim=(1 if j == 0 else 0)) for j, x in enumerate(SINIR_X)]
        out.append(_satir(g, olaylar))
    return out


def _gun_ornekleri(g, xs, *, once=None, sonra=None, ara=None) -> dict:
    """Sınır örnekleri: 09:40 ET (önce, 0 olay) ve 16:01 ET (sonra, xs)."""
    d = {(once or _et(g, 9, 40)).timestamp(): [], (sonra or _et(g, 16, 1)).timestamp(): list(xs)}
    if ara:
        d.update({ts: v for ts, v in ara.items()})
    return d


def test_E1_tanik_LE_kurali_sinirdaki_X_kendi_kovasinda(m, tmp_path):
    satirlar = _tanikli_satirlar()
    yanitlar = [_tanik_yaniti(_gun_ornekleri(g, SINIR_X)) for g in GUNLER[:20]]
    sonuc = _hukum(m, tmp_path, satirlar, tanik_yolu=_tanik_yaz(tmp_path / "t.jsonl", yanitlar))
    assert {s["tanik"]["durum"] for s in sonuc["seanslar"]} == {"eşit"}, [s["tanik"] for s in sonuc["seanslar"]]
    # Aynı X'ler sağ-açık ([a, b)) kovalarla sayılsaydı sınırdaki üç olay bir üst kovaya düşerdi → KUSURLU.
    sag_acik = []
    for g in GUNLER[:20]:
        y = _tanik_yaniti(_gun_ornekleri(g, SINIR_X))
        for seri in y["data"]["result"]:
            le = None if seri["metric"]["le"] == "+Inf" else float(seri["metric"]["le"])
            seri["values"][-1][1] = str(sum(1 for x in SINIR_X if le is None or x < le))
        sag_acik.append(y)
    yanlis = _hukum(m, tmp_path, satirlar, tanik_yolu=_tanik_yaz(tmp_path / "t2.jsonl", sag_acik))
    assert _seans(yanlis, GUNLER[0])["tanik"]["durum"] == "kusurlu"


def test_E2_TANIKSIZ_ile_KUSURLU_ayrimi_ve_kusurlunun_HUKMU_durdurmasi(m, tmp_path):
    satirlar = _tanikli_satirlar()
    yok = _hukum(m, tmp_path, satirlar)
    assert {s["tanik"]["durum"] for s in yok["seanslar"]} == {"tanıksız"} and yok["pencere"]["dolu"], \
        "tanıksız seans DIŞLANMAZ (adıyla)"
    g0, g1, g2, g3 = GUNLER[:4]
    yanitlar = [_tanik_yaniti(_gun_ornekleri(g, SINIR_X)) for g in GUNLER[4:20]]
    yanitlar.append(_tanik_yaniti({_et(g0, 16, 1).timestamp(): SINIR_X}))                 # önce-sınır örneği YOK
    yanitlar.append(_tanik_yaniti(_gun_ornekleri(g1, SINIR_X, ara={_et(g1, 12, 0).timestamp(): SINIR_X * 3})))
    yanitlar.append(_tanik_yaniti(_gun_ornekleri(g2, SINIR_X[:-1])))                      # bir olay EKSİK → kusurlu
    yanitlar.append(_tanik_yaniti(_gun_ornekleri(g3, SINIR_X)))
    yol = _tanik_yaz(tmp_path / "t.jsonl", yanitlar)
    sonuc = _hukum(m, tmp_path, satirlar + [_satir(GUNLER[20], [_olay(x=0.002, giris=1, yazim=1)])], tanik_yolu=yol)
    assert _seans(sonuc, g0)["tanik"]["durum"] == "tanıksız" and "önce" in _seans(sonuc, g0)["tanik"]["neden"]
    assert _seans(sonuc, g1)["tanik"]["durum"] == "tanıksız" and "sıfırlan" in _seans(sonuc, g1)["tanik"]["neden"]
    assert _seans(sonuc, g2)["tanik"]["durum"] == "kusurlu" and _seans(sonuc, g2)["sinif"] == "kusurlu"
    assert _seans(sonuc, g0)["temiz"] and _seans(sonuc, g1)["temiz"] and _seans(sonuc, g3)["temiz"]
    assert sonuc["hukum"]["karar"] == m.OLCULEMEDI and "kusurlu_kok_neden" in _kodlar(sonuc)
    assert g2 not in sonuc["pencere"]["seanslar"] and GUNLER[20] in sonuc["pencere"]["seanslar"], "pencere uzar"
    oz = sonuc["tanik_ozeti"]
    assert sonuc["taniksiz"] is False and oz["tanik_dosyasi"] is True
    assert (oz["eşit"], oz["tanıksız"], oz["kusurlu"]) == (17, 3, 1), oz           # aralık G0…G20
    assert oz["pencerede"] == {"eşit": 17, "tanıksız": 3, "kusurlu": 0}
    kabul = _hukum(m, tmp_path, satirlar + [_satir(GUNLER[20], [_olay(x=0.002, giris=1, yazim=1)])],
                   tanik_yolu=yol, kusurlu_kabul=(g2,))
    assert "kusurlu_kok_neden" not in _kodlar(kabul) and g2 not in kabul["pencere"]["seanslar"]
    assert kabul["parametreler"]["kusurlu_kok_neden_kartta"] == [g2]


def test_E3_error_FARKI_raporlanir_karsilastirilmaz(m, tmp_path):
    g = GUNLER[0]
    satirlar = [_satir(g, [_olay(x=x, giris=1, yazim=1) for x in SINIR_X] + [_olay(outcome="error", x=0.3)])]
    err = _tanik_yaniti({_et(g, 9, 40).timestamp(): [0.1] * 4, _et(g, 16, 1).timestamp(): [0.1] * 6},
                        outcome="error")["data"]["result"]
    yol = _tanik_yaz(tmp_path / "t.jsonl", [_tanik_yaniti(_gun_ornekleri(g, SINIR_X), ek_seriler=err)])
    t = _seans(_hukum(m, tmp_path, satirlar, tanik_yolu=yol), g)["tanik"]
    assert t["durum"] == "eşit" and t["error_farki"] == 2 and t["defter_error"] == 1


def test_E4_TANIK_zorunlu_TANIKSIZ_bilincli_kacis_cikti_BASINDA(m, tmp_path, capsys):
    """Dal sonu inceleme I-2: tanık verilmeden tam hüküm çıkıyordu ve "kusurlu → hüküm durur" bekçisi sessizce devre
    dışıydı (her seans 'tanıksız', üst düzeyde görünmüyordu). Hüküm yolunda `--tanik` ZORUNLU; bilinçli kaçış
    `--taniksiz` hükmü ÖLÇÜLEMEDİ'ye ÇEVİRMEZ ama çıktının BAŞINDA `taniksiz: true` + `tanik_ozeti` sayılarıyla görünür."""
    yol = _defter_yaz(tmp_path / "d.jsonl", [_duz_seans(g) for g in GUNLER[:20]])
    with pytest.raises(ValueError, match="tanık"):
        m.hukum(yol, baslangic=GUNLER[0])
    t = _tanik_yaz(tmp_path / "t.jsonl", [_tanik_yaniti(_gun_ornekleri(GUNLER[0], [1.0] * 20))])
    with pytest.raises(ValueError, match="birlikte"):
        m.hukum(yol, baslangic=GUNLER[0], tanik_yolu=t, taniksiz=True)
    assert m.main(["hukum", "--defter", str(yol), "--baslangic", GUNLER[0]]) == 2
    assert "--taniksiz" in capsys.readouterr().err
    cikti = tmp_path / "s.json"
    assert m.main(["hukum", "--defter", str(yol), "--baslangic", GUNLER[0], "--taniksiz", "--cikti", str(cikti)]) == 0
    satir = capsys.readouterr().out
    assert satir.startswith("TANIKSIZ"), satir
    s = json.loads(cikti.read_text(encoding="utf-8"))
    assert list(s)[:3] == ["kart", "taniksiz", "tanik_ozeti"], list(s)[:5]
    assert s["taniksiz"] is True and s["parametreler"]["taniksiz"] is True
    assert (s["tanik_ozeti"]["eşit"], s["tanik_ozeti"]["tanıksız"], s["tanik_ozeti"]["kusurlu"]) == (0, 20, 0)
    assert s["tanik_ozeti"]["tanik_dosyasi"] is False
    assert s["hukum"]["karar"] == m.YESIL, "kaçış hükmü ÖLÇÜLEMEDİ'ye çevirmez — yalnız adıyla görünür kılar"


# =================================================================================================================
# F — tanılar t1–t6
# =================================================================================================================

def test_F1_tanilar_t1_t6_SAYIYLA(m, tmp_path):
    """20 seans × 20 olay, Y hep 1,0. Her seansta j=10 yazım olayı (Z=0,25); tek j'ler planli giriş (Z=0,0625); seans 7'de
    j=16..19 Z=0,5 (en kötü seans). Her seansta bir `error` olayı (Z=0,125)."""
    satirlar = []
    for i, g in enumerate(GUNLER[:20]):
        olaylar = []
        for j in range(20):
            yazim = 1 if j == 10 else 0
            z = 0.25 if yazim else (0.5 if (i == 7 and j > 15) else (0.0625 if j % 2 else 0.0))
            olaylar.append(_olay(x=1.0 + z, z=z, ofset=30.0 * j, giris=(1 if z > 0 else 0), yazim=yazim))
        olaylar.append(_olay(outcome="error", x=0.5, z=0.125, ofset=999.0, giris=1))
        satirlar.append(_satir(g, olaylar))
    t = _hukum(m, tmp_path, satirlar)["tanilar"]
    assert t["t1"]["en_kotu"]["seans"] == GUNLER[7] and t["t1"]["en_kotu"]["r_s"] == 1.5
    assert len(t["t1"]["seanslar"]) == 20 and t["t1"]["seanslar"][0]["r_s"] == 1.0625
    assert t["t2"]["n_yazim_olay"] == 20 and t["t2"]["n_yazim_satir"] == 20
    assert t["t2"]["z_medyan"] == 0.25 == t["t2"]["z_maks"] and t["t2"]["en_kotu_olay"]["x_s"] == 1.25
    assert t["t3"]["maks_orani"] == 1.5 and {"p99_orani", "r_q94", "r_q96", "y_q94", "y_q95", "y_q96"} <= set(t["t3"])
    assert t["t4"]["p95_z_bolu_y"] == 0.25
    assert t["t5"]["pencere_s"] == 60.0 and t["t5"]["n_yazim_olay"] == 20
    assert t["t5"]["onceki"]["n"] == 20 * 2 and t["t5"]["sonraki"]["n"] == 20 * 2
    assert t["t6"]["f_yazim"] == 20 / 400 and t["t6"]["f_giris"] == (20 * 11 + 2) / 400
    assert t["t6"]["n_error"] == 20 and t["t6"]["n_error_z_pozitif"] == 20


# =================================================================================================================
# G — POZİTİF KONTROLLER uçtan uca (kart `pozitif_kontrol`)
# =================================================================================================================

ADIM_S = 2.0 ** -20            # sanal saatin okuma başına adımı (~0,95 µs) — "kronometre" bedelinin simgesi
TABAN_OKUMA_S = 0.002          # canlıdaki Redis okumasının sanal karşılığı (sembol başına), tohumlu ±%50 dağılım
OLAY_ARALIGI_S = 30.0
PK_GUNLER = GUNLER[:20]
PK_OLAY_N = 50                 # seans başına işlenen olay; yazım olayı payı 1/50 = %2 (< %5 — PK-3 koşulu)
PK_SYMS = "MSFT,T0,T1,T2,POS,ZZZ"   # silahlı + 3 planli + plansız pozisyon + ilgi dışı (v217/v606 bileşimi, ≥ 5)


class _SanalSaat:
    """Her okumada `ADIM_S` ilerleyen sanal saat; `ilerle` enjekte edilen gecikmedir."""

    def __init__(self, t0: float):
        self.t = t0

    def __call__(self) -> float:
        simdi = self.t
        self.t += ADIM_S
        return simdi

    def ilerle(self, s: float) -> None:
        self.t += s


def _tanik_kesiti(kesit: dict, ts: float) -> dict:
    return {"ts": ts, "kesit": {o: list(kesit[o]["kova_sayilari"]) for o in ("processed", "skipped", "error")}}


def _tanik_dok(kesitler: list) -> dict:
    """Süreç-içi `DONGU_SURESI.anlik()` kesitlerinden Prometheus query_range yanıtı (TANIK EŞİ)."""
    sonuc = []
    for o in ("processed", "skipped", "error"):
        for i, le in enumerate(LE):
            sonuc.append({"metric": {"__name__": "meridian_intraday_cycle_seconds_bucket", "job": "meridian",
                                     "instance": "127.0.0.1:8080", "outcome": o, "le": _le_metni(le)},
                          "values": [[k["ts"], str(sum(k["kesit"][o][: i + 1]))] for k in kesitler]})
    return {"status": "success", "data": {"resultType": "matrix", "result": sonuc}}


def _pk_kos(sandbox_state, monkeypatch, tmp_path, ad, *, enjeksiyon=None, d=0.0, planli_acik=True):
    """Bir PK senaryosu: 20 seans × 50 olay GERÇEK tüketiciden, seans sonu kapı olayı GERÇEK boşaltmayı tetikler."""
    for f in (ic.DECISIONS_FILE, ish.ORDERS_FILE, ish.PLANLI_ORDERS_FILE, ic.ATIF_DEFTERI, "trade_plans.jsonl"):
        (sandbox_state / f).unlink(missing_ok=True)
    ic._CONSUMER = None
    ic.reset_plans_cache()
    ish.reset_dedup()
    saat = _SanalSaat(ic._SUREC_SAAT0 + 1000.0)
    monkeypatch.setattr(gecikme, "_saat", saat)
    monkeypatch.setattr(ic, "_SUREC_BASLANGIC", SUREC_ONCESI)
    monkeypatch.setattr(ish, "PLANLI_ENABLED", planli_acik)
    poz = {"plan_id": "P-ESKI", "ticker": "POS", "side": "long", "entry": 100.0, "stop": 95.0, "trail_stop": 95.0,
           "target": 130.0, "qty": 10, "r_per_share": 5.0, "risk_dollars": 50.0, "size_r": 1.0, "ts_open": "2026-07-20"}
    _kapilar_olculebilir(armed=[_plan("MSFT", 50.0)], positions={"POS": poz})
    for i in range(3):
        store.append_jsonl("trade_plans.jsonl", _plan(f"T{i}", 100.0))
    rng = random.Random(607)

    def okuma(tk, n):
        saat.ilerle(TABAN_OKUMA_S * (1.0 + 0.5 * rng.random()))
        dakika = bc.now().replace(second=0, microsecond=0) - dt.timedelta(minutes=1)
        return [_bar(t=dakika.strftime("%Y-%m-%dT%H:%M:%SZ"), o=50.0, h=200.0, c=150.0)]

    monkeypatch.setattr(ic.hotstate, "read_bars", okuma)
    if enjeksiyon == "planli":                         # PK-1: planli dal GÖVDESİNE her girişte d
        ozgun_ps = ish.planli_satir

        def planli(*a, **k):
            saat.ilerle(d)
            return ozgun_ps(*a, **k)

        monkeypatch.setattr(ish, "planli_satir", planli)
    elif enjeksiyon in ("karar_defteri", "yazim"):
        # PK-2: planli sembolün KARAR DEFTERİ yazımı — dal sınırının hemen DIŞI (aynı sembol, aynı giriş başına d; Z'yi
        # dal dışına genişleten bir alet onu soğurur → KILL). PK-3: YALNIZ planli satırın diske yazımı (seyrek olay).
        ozgun_aj = store.append_jsonl

        def yaz(name, row):
            if ((enjeksiyon == "karar_defteri" and name == ic.DECISIONS_FILE and row.get("plan_source") == "planned")
                    or (enjeksiyon == "yazim" and name == ish.PLANLI_ORDERS_FILE)):
                saat.ilerle(d)
            return ozgun_aj(name, row)

        monkeypatch.setattr(store, "append_jsonl", yaz)
    t = ic.consumer()
    yanitlar = []
    for gun in PK_GUNLER:
        once = _tanik_kesiti(ic.DONGU_SURESI.anlik(), _et(gun, 9, 40).timestamp())
        for i in range(PK_OLAY_N):
            an = _et(gun, 10, 0) + dt.timedelta(seconds=OLAY_ARALIGI_S * i)
            bc.set_clock(lambda an=an: an)
            saat.ilerle(OLAY_ARALIGI_S)
            t.on_barfeed_event({"syms": PK_SYMS})
        bc.set_clock(lambda gun=gun: _et(gun, 16, 30))
        t.on_barfeed_event({"syms": PK_SYMS})          # seans kapısı → GERÇEK `seans_kapandi` boşaltması
        sonra = _tanik_kesiti(ic.DONGU_SURESI.anlik(), _et(gun, 16, 31).timestamp())
        yanitlar.append(_tanik_dok([once, sonra]))
    tanik = _tanik_yaz(tmp_path / f"{ad}_tanik.jsonl", yanitlar)
    return sandbox_state / ic.ATIF_DEFTERI, tanik


def _betik_kos(m, tmp_path, ad, defter, tanik) -> dict:
    """Betiğin KENDİSİ, operatörün çağırdığı komut satırıyla (`main`)."""
    cikti = tmp_path / f"{ad}_sonuc.json"
    rc = m.main(["hukum", "--defter", str(defter), "--tanik", str(tanik), "--baslangic", PK_GUNLER[0],
                 "--yeniden-baslatma-esigi", "acilis", "--cikti", str(cikti)])
    assert rc == 0
    return json.loads(cikti.read_text(encoding="utf-8"))


def _olay_basi_planli_giris(defter: pathlib.Path) -> int:
    """Tabanın defterinden ÖLÇÜLÜR: işlenen her olayda planli dala kaç giriş var (bileşimde T0–T2 → 3; tek değer şart)."""
    degerler = set()
    for satir in (json.loads(x) for x in defter.read_text(encoding="utf-8").splitlines() if x.strip()):
        ix = satir["alanlar"]
        degerler |= {o[ix.index("planli_giris")] for o in satir["olaylar"] if o[ix.index("outcome")] == "processed"}
    assert len(degerler) == 1 and min(degerler) > 0, degerler
    return degerler.pop()


def _taban(m, sandbox_state, monkeypatch, tmp_path) -> dict:
    defter, tanik = _pk_kos(sandbox_state, monkeypatch, tmp_path, "taban")
    s = _betik_kos(m, tmp_path, "taban", defter, tanik)
    s["_olay_basi_giris"] = _olay_basi_planli_giris(defter)
    h = s["hukum"]
    # Taban sağlıklı mı (PK'ların ön koşulu): 20 temiz seans, tanık EŞİT (tanık eşi), her seansta 3 planli yazım.
    assert {x["tanik"]["durum"] for x in s["seanslar"]} == {"eşit"}, "TANIK EŞİ: defter kova sayımı ≠ DONGU_SURESI"
    assert s["pencere"]["dolu"] and h["n_olay"] == 20 * PK_OLAY_N and h["n_yazim_satir"] == 60
    assert h["karar"] == m.YESIL, h
    return s


def test_G1_PK1_DUYARLILIK_planli_dala_olay_basi_yuzde20_KILL(m, sandbox_state, monkeypatch, tmp_path):
    """Kart PK-1 + netleştirme 2026-10-01b: "+%20" olay başına planli dalın TOPLAM ekidir — giriş sayısına BÖLÜNÜR; hedef
    R ≈ 1,20 (tavanın iki katı aşım). Olayların tamamında planli giriş var."""
    taban_s = _taban(m, sandbox_state, monkeypatch, tmp_path)
    taban, k = taban_s["hukum"], taban_s["_olay_basi_giris"]
    d = 0.2 * taban["p95_y"] / k
    defter, tanik = _pk_kos(sandbox_state, monkeypatch, tmp_path, "pk1", enjeksiyon="planli", d=d)
    s = _betik_kos(m, tmp_path, "pk1", defter, tanik)
    h = s["hukum"]
    assert s["tanilar"]["t6"]["f_giris"] == 1.0, "olayların TAMAMINDA planli giriş olmalı (kart PK-1)"
    assert h["r_nokta"] == pytest.approx(1.20, abs=0.005), f"PK-1 büyüklüğü kartın niyeti değil: R={h['r_nokta']}"
    assert h["karar"] == m.KILL == h["uclu"] and h["r_nokta"] > h["tavan"], h
    assert h["p95_y"] == pytest.approx(taban["p95_y"], rel=1e-6), "gecikme Y'ye sızdı — Z onu soğurmadı"


def test_G2_PK2_OZGULLUK_ayni_TOPLAM_gecikme_dal_DISINDA_YESIL(m, sandbox_state, monkeypatch, tmp_path):
    """Kart PK-2: AYNI gecikme planli dalın DIŞINA (kartın seçeneklerinden "karar defteri yazımı"): PK-1 ile aynı giriş başı
    d ve aynı olay başı toplam (p95(Y)'nin %20'si), YALNIZ yer farklı — planli sembolün karar satırı, dalın hemen önünde.
    p95(X) o toplam kadar artar, Z soğurmaz → YEŞİL. Z'yi dal dışına genişleten alet bu gecikmeyi soğurur → KILL (kart
    MUTASYON "Z'yi dal dışına genişletmek (PK-2)")."""
    taban_s = _taban(m, sandbox_state, monkeypatch, tmp_path)
    taban, k = taban_s["hukum"], taban_s["_olay_basi_giris"]
    toplam = 0.2 * taban["p95_y"]
    defter, tanik = _pk_kos(sandbox_state, monkeypatch, tmp_path, "pk2", enjeksiyon="karar_defteri", d=toplam / k)
    h = _betik_kos(m, tmp_path, "pk2", defter, tanik)["hukum"]
    assert h["p95_x"] - taban["p95_x"] == pytest.approx(toplam, rel=1e-6), \
        "enjeksiyon p95(X)'i olay başına p95(Y)'nin %20'si kadar artırmadı"
    assert h["karar"] == m.YESIL == h["uclu"] and h["r_nokta"] <= h["tavan"] and h["ci"]["hi"] <= h["tavan"], h


def test_G3_NK_kol_KAPALI_oran_bire_esit_EPSILON_raporlanir(m, sandbox_state, monkeypatch, tmp_path):
    defter, tanik = _pk_kos(sandbox_state, monkeypatch, tmp_path, "nk", planli_acik=False)
    s = _betik_kos(m, tmp_path, "nk", defter, tanik)
    h = s["hukum"]
    assert 0.0 < h["r_eksi_1"] < 1e-3, f"ε = {h['r_eksi_1']} (dal erken-dönüşü + kronometre)"
    assert h["uclu"] == m.YESIL, "kart NK: üçlü hüküm YEŞİL"
    # Kol kapalıyken yazım 0 → kill_list 'yazım < 10 → ÖLÇÜLEMEDİ' geçerlilik maddesi nihai kararı ÖLÇÜLEMEDİ yapar.
    assert h["n_yazim_satir"] == 0 and h["karar"] == m.OLCULEMEDI and _kodlar(s) == {"yazim_az"}


def test_G4_PK3_KORLUK_seyrek_yazima_10x_gecikme_YESIL_tani_GOSTERIR(m, sandbox_state, monkeypatch, tmp_path):
    taban = _taban(m, sandbox_state, monkeypatch, tmp_path)["hukum"]
    d = 10.0 * taban["p95_y"]
    defter, tanik = _pk_kos(sandbox_state, monkeypatch, tmp_path, "pk3", enjeksiyon="yazim", d=d)
    s = _betik_kos(m, tmp_path, "pk3", defter, tanik)
    h, t = s["hukum"], s["tanilar"]
    assert t["t6"]["f_yazim"] < 0.05, "yazım olayı payı ≥ %5 — PK-3 kurgusu değil"
    assert h["karar"] == m.YESIL == h["uclu"], "nadir-ağır gecikme p95'i aşmamalı (kartın beyanlı körlüğü)"
    assert t["t2"]["z_maks"] >= d and t["t2"]["en_kotu_olay"]["x_s"] >= 10.0 * taban["p95_y"], t["t2"]
    assert t["t3"]["maks_orani"] >= 10.0, "t3 kuyruk oranı gecikmeyi göstermiyor"


# =================================================================================================================
# H — betik `meridian.obs`a ULAŞMAZ
# =================================================================================================================

def _meridian_ithalleri(yol: pathlib.Path) -> set:
    """Kaynaktaki (fonksiyon içleri DAHİL) bütün `meridian` içe aktarmaları — tam nitelikli modül adı."""
    out = set()
    agac = ast.parse(yol.read_text(encoding="utf-8"))
    for d in ast.walk(agac):
        if isinstance(d, ast.Import):
            out |= {a.name for a in d.names if a.name.split(".")[0] == "meridian"}
        elif isinstance(d, ast.ImportFrom):
            if d.level:
                out.add("meridian." + (d.module or "*"))
            elif d.module and d.module.split(".")[0] == "meridian":
                out |= ({f"{d.module}.{a.name}" for a in d.names} if d.module == "meridian" else {d.module})
    return out


def test_H1_STATIK_ithal_kapanisi_yalniz_SAF_YAPRAKLAR(m):
    izinli = {f"meridian.{a}" for a in m.IZINLI_MERIDIAN_MODULLERI}
    assert izinli == {"meridian.barclock", "meridian.gecikme", "meridian.olcum_araclari"}
    assert _meridian_ithalleri(BETIK) == izinli
    for ad in m.IZINLI_MERIDIAN_MODULLERI:
        assert _meridian_ithalleri(KOK / "meridian" / f"{ad}.py") == set(), f"{ad} saf yaprak değil"
    src = BETIK.read_text(encoding="utf-8")
    for yasak in ("importlib", "__import__", "exec(", "eval(", "subprocess"):
        assert yasak not in src, f"betikte dinamik yükleme/alt süreç: {yasak}"


def test_H2_OPERATOR_BICIMINDE_alt_surec_obs_YUKLENMEZ(tmp_path):
    """Rol-1'in A1'de koşacağı biçim: `python research/olcumler/exe012_kill1_canli/hukum.py hukum …` — ayrı süreçte,
    `-X importtime` ile YÜKLENEN her modül sayılır. obs/store/config yüklenmez; çıktı yalnız `--cikti`ye gider."""
    defter = _defter_yaz(tmp_path / "defter.jsonl", [_duz_seans(g) for g in GUNLER[:3]])
    cikti = tmp_path / "cikti" / "sonuc.json"
    cikti.parent.mkdir()
    ortam = dict(os.environ)
    ortam["MERIDIAN_ROOT"] = str(tmp_path)              # savunma derinliği: yine de obs'a ulaşsa yazım tmp'ye düşer
    ortam.pop("PYTHONPATH", None)                       # betik kendi ağacını sys.path'e koyar (worktree tuzağı yok)
    p = subprocess.run([sys.executable, "-X", "importtime", str(BETIK), "hukum", "--defter", str(defter),
                        "--baslangic", GUNLER[0], "--taniksiz", "--cikti", str(cikti)],
                       cwd=tmp_path, env=ortam, capture_output=True, text=True, timeout=300)
    assert p.returncode == 0, p.stderr[-2000:]
    yuklenen = {s.rsplit("|", 1)[-1].strip() for s in p.stderr.splitlines() if s.startswith("import time:")}
    meridyen = {a for a in yuklenen if a == "meridian" or a.startswith("meridian.")}
    assert meridyen == {"meridian", "meridian.barclock", "meridian.gecikme", "meridian.olcum_araclari"}, meridyen
    assert not {"meridian.obs", "meridian.store", "meridian.config"} & yuklenen
    sonuc = json.loads(cikti.read_text(encoding="utf-8"))
    assert sonuc["kart"] == "EXE-2026-012" and sonuc["hukum"]["karar"] == "ÖLÇÜLEMEDİ"
    assert sorted(x.name for x in tmp_path.iterdir()) == ["cikti", "defter.jsonl"], "betik --cikti dışına yazdı"
    # Betik KENDİ ağacının meridian'ını yükler (venv ana checkout'a kurulu — worktree tuzağı yok).
    assert sonuc["kod"]["meridian_yolu"] == str(KOK / "meridian")


# =================================================================================================================
# I — kart ve alet bağı
# =================================================================================================================

def test_I1_esikler_KARTTAN_okunur(m):
    kart = yaml.safe_load(KART.read_text(encoding="utf-8"))
    e = m.kart_esikleri()
    for ad in ("tavan_R", "ci_seviye", "bootstrap_B", "pencere_seans", "n_yazim_min"):
        assert e[ad] == kart["esikler"][ad], ad
    assert (e["tavan_R"], e["ci_seviye"], e["bootstrap_B"], e["pencere_seans"], e["n_yazim_min"]) == \
        (1.10, 0.95, 10_000, 20, 10)
    assert e["tohum"] == oa.BOOTSTRAP_TOHUM == f5.BOOTSTRAP_TOHUM == 11, "kart: tohum faz5_cikis.BOOTSTRAP_TOHUM"
    assert "v217 `_p95` ile özdeş" in kart["esikler"]["p95_tanimi"]
    # Kart başka bir yoldan okunursa (ör. eşik değiştirilmiş kopya) değer ORADAN gelir — kodda gömülü eşik yok.
    src = BETIK.read_text(encoding="utf-8")
    assert "1.10" not in src and "1.1)" not in src and "10_000" not in src and "10000" not in src


def test_I2_alan_bosaltma_sema_ALETLE_ayrismaz(m, sandbox_state):
    assert set(m.GEREKLI_ALANLAR) == set(ic.ATIF_ALANLARI)
    assert tuple(m.BOSALTMA_SOZLUGU) == ic.ATIF_BOSALTMA and m.BOSALTMA_KAPANIS in ic.ATIF_BOSALTMA
    assert m.KART_KIMLIGI == ic.ATIF_KART and m.HUKUM_EVRENI == ("processed",)
    # Şema: aletin GERÇEK yazdığı satır (gerçek yol) betiğin şema denetiminden geçer.
    store.write_json("portfolio.json", {"positions": {}, "armed": []})
    bc.set_clock(lambda: v217.RTH)
    t = ic.consumer()
    t.on_barfeed_event({"syms": ""})
    t.kapanista_bosalt()
    oku = m.defter_oku(sandbox_state / ic.ATIF_DEFTERI)
    assert oku["sema_ihlali"] == [] and len(oku["satirlar"]) == 1 and oku["satirlar"][0]["veri"]["sema"] == m.SEMA


def test_I3_Yasa6_beyani_OKUYUCUYU_adlandirir_motor_ici_okuyucu_iddiasi_KORUNUR():
    gerekce = codelaw.DECLARED_SINKS[ic.ATIF_DEFTERI]
    assert "research/olcumler/exe012_kill1_canli/hukum.py" in gerekce and BETIK.exists()
    assert "HENÜZ YAZILMADI" not in gerekce
    iddia = next(c for c in codelaw.declared_claims() if c["artifact"] == ic.ATIF_DEFTERI)
    assert iddia["claims_no_prod_reader"] is True and iddia["stale_claim"] is False, \
        "OTOMATİK KAPI YASAĞI'nın mekanik katmanı (motor içi okuyucu yok iddiası) düştü"


def test_I4_kart_NETLESTIRMELERI_betik_ve_PK_ile_UYUMLU():
    """Kartın netleştirmeleri (Rol-1, ADIM-0 öncesi) betiğin sabitine ve PK düzeneğine bağlı: (1) yeniden başlatma eşiği
    açılış; 2026-10-01b sanal saat + PK-1'in olay başı toplamı."""
    kart = yaml.safe_load(KART.read_text(encoding="utf-8"))
    n1, n1b = kart["netlestirme_2026_10_01"], kart["netlestirme_2026_10_01b"]
    assert "--yeniden-baslatma-esigi acilis" in n1 and "09:30 ET" in n1
    assert "SANAL SAAT" in n1b and "giriş sayısına bölünür" in n1b


# =================================================================================================================
# J — ADIM-0 a/b/c + tanık planı
# =================================================================================================================

def test_J1_ADIM0a_seans_basi_SAYIM_p95_KOVASI_ve_50ms_payi(m, tmp_path):
    g = GUNLER[0]
    xs = [0.0012] * 90 + [0.004] * 6 + [0.07] * 3 + [0.3]
    skp = _tanik_yaniti({_et(g, 9, 40).timestamp(): [0.0001] * 10, _et(g, 16, 1).timestamp(): [0.0001] * 25},
                        outcome="skipped")["data"]["result"]
    err = _tanik_yaniti({_et(g, 9, 40).timestamp(): [], _et(g, 16, 1).timestamp(): [0.2]},
                        outcome="error")["data"]["result"]
    yol = _tanik_yaz(tmp_path / "t.jsonl", [_tanik_yaniti(_gun_ornekleri(g, xs), ek_seriler=skp + err)])
    a = m.adim0a(yol)
    s = next(x for x in a["seanslar"] if x["seans"] == g)
    assert (s["processed"], s["skipped"], s["error"]) == (100, 15, 1)
    assert s["p95_kovasi_le"] == "0.005", "k = round(0,95·99) = 94 → 95. olay 0,004 → le=0.005 kovası"
    assert s["pay_50ms_ustu"]["deger"] == 0.04 and s["pay_le_50ms_ve_ustu"]["deger"] == 0.04


def test_J2_ADIM0b_f_giris_f_yazim_ve_BEKLENEN_yazim(m, tmp_path):
    g0, g1 = GUNLER[:2]
    planli = tmp_path / "planli.jsonl"
    planli.write_text("".join(json.dumps(r) + "\n" for r in [
        {"plan_id": "P1", "date": g0, "decision_as_of": _et(g0, 10, 0).isoformat()},
        {"plan_id": "P2", "date": g0, "decision_as_of": _et(g0, 10, 0).isoformat()},
        {"plan_id": "P3", "date": g1, "decision_as_of": _et(g1, 11, 0).isoformat()}]), encoding="utf-8")
    karar = tmp_path / "karar.jsonl"
    satirlar = []
    for g in (g0, g1):
        for k in range(5):
            an = _et(g, 10, k).isoformat()
            satirlar.append({"decision_as_of": an, "fired": True, "plan_source": "planned", "ticker": "A"})
            satirlar.append({"decision_as_of": an, "fired": True, "plan_source": "planned", "ticker": "B"})
            satirlar.append({"decision_as_of": an, "fired": False, "plan_source": "planned", "ticker": "C"})
            satirlar.append({"decision_as_of": an, "fired": True, "plan_source": "armed", "ticker": "D"})
    karar.write_text("".join(json.dumps(r) + "\n" for r in satirlar), encoding="utf-8")
    a0 = tmp_path / "a0.json"
    a0.write_text(json.dumps({"seanslar": [{"seans": g0, "durum": "olculdu", "processed": 100},
                                           {"seans": g1, "durum": "olculdu", "processed": 100}]}), encoding="utf-8")
    b = m.adim0b(planli, karar, a0, baslangic=g0)
    assert b["f_giris"] == 10 / 200 and b["f_yazim"] == 2 / 200
    assert b["seans_n"] == 2 and b["beklenen_yazim_20_seans"] == 3 / 2 * 20 and b["n_yazim_min"] == 10
    assert b["f_yazim_duzeltme_esigi_asildi"] is False


def test_J3_ADIM0c_ilk_seans_BETIMLEMESI_hukum_degil(m, tmp_path):
    g = GUNLER[0]
    satirlar = [_satir(g, [_olay(x=1.25, z=0.25, giris=1, yazim=1)] + [_olay(x=1.0, z=0.0) for _ in range(19)])]
    c = m.adim0c(_defter_yaz(tmp_path / "d.jsonl", satirlar), g)
    assert c["seans"] == g and c["r_0"] == 1.0 and c["z"]["maks"] == 0.25 and c["z"]["n_pozitif"] == 1
    assert c["satir_kb"][0] > 0 and c["tanik"]["durum"] == "tanıksız" and "GİRMEZ" in c["not"]
    assert c["yeniden_baslatma"] == {"acilis": False, "pencere": False}, "betimlemede iki eşik de raporlanır (tanı)"


def test_J4_tanik_PLANI_sinirlari_ET_den_turetir_DST(m):
    p = {x["seans"]: x for x in m.tanik_plani(["2026-10-30", "2026-11-02"])}
    assert p["2026-10-30"]["once_bitis"] == "2026-10-30T13:45:00+00:00", "EDT: 09:45 ET = 13:45Z"
    assert p["2026-11-02"]["once_bitis"] == "2026-11-02T14:45:00+00:00", "EST: 09:45 ET = 14:45Z"
    assert p["2026-11-02"]["sonra_baslangic"] == "2026-11-02T21:00:00+00:00"
    assert "meridian_intraday_cycle_seconds_bucket" in p["2026-11-02"]["sorgu"]["query"]
