"""tests/test_golge_siralama_kolu_v425.py — EDG-2026-078 Aşama A: GÖLGE SIRALAMA KOLU + PENCERE
SAYACI (TSK-126, 2026-09-05).

NE ÖLÇER — kart `research/cards/EDG-2026-078-skill-gorus-golge-siralama-kolu.yaml`, tasarım
`docs/TASARIM-SKILL-GORUS-TERFISI-2026-09-05.md` §4 Aşama A:

  (1) KANCA `skill_gorus.golge_siralama_kancasi` — P3'ün ZATEN sıraladığı aday kesitine in-memory
      ikinci (görüşlü) bir sıralama üretir ve `state/golge_siralama.jsonl`e yazar. Formül
      (z_skill/score_golge), N≤0 ⇒ N=0, defter üst sınırı (max(2N,20)) ve `sure_ms` doluluğu
      ölçülür. MUTASYON 1 çivisi: `candidates` listesi hiçbir koşulda (w=0 iken de w=0,5 iken de)
      mutasyona uğramaz — kanca sıralamayı YERİNDE değiştirirse bu test kırmızı olur.
  (2) ÇÖZÜCÜ `skill_gorus.golge_kol_raporu` — saf okuma; defter + `_gozlemler()` eşleşmesinden
      seans başına rank-IC(mevcut/gölge) ve Δ. PK (a): rastgele (karıştırılmış) gölge sıralaması →
      Δ CI'ı sıfırı İÇERMELİ (alet gürültüyü anlamlı göstermemeli). PK (b): SONUCU BİLEN sentetik
      sıralama (yalnız bu testte; deftere böyle yazılmaz) → Δ belirgin pozitif. MUTASYON 2 çivisi:
      çözücüde `sira_golge` yerine `sira_mevcut` kullanılırsa Δ→0 ve PK (b) testi kırmızı olur.
  (3) PENCERE SAYACI `skill_gorus.pencere_yaz`/`_pencere_ozeti` — EDG-2026-019 kill#3'ün "3 ARDIŞIK
      pencere" borcunu kapatır: gün başına idempotent yazım, ardışıklık hesap YÖNÜ değişince
      YENİDEN başlar (eski seri taşınmaz).
  (4) KART EŞİTLİĞİ — `KART_GOLGE_AGIRLIKLARI`/`KART_N_MIN_SEANS`/`KART_GOLGE_USTN_KESISIM_MIN`
      kart YAML'ının serbest metniyle AYRIŞMAZ (tek-kaynak yasası çivisi).
  (5) API — `api._eksen2_gorus()` boş defterde `golge_kol.durum` "ÖLÇÜLEMEDİ" + `neden` (UYDURMA
      YOK: "hiç ölçüm yok" ile "sayı 0" karışmaz).

KAPSAM DIŞI: kartın hükmü (Δrank-IC CI-altı>0 ∧ n_seans≥30 ∧ kesişim≥0,50) — bu dosya YÖNTEMİN
doğru ölçtüğünü kanıtlar, bir terfi/kaldı kararı vermez (CLAUDE.md §3: hüküm Rol-1'de).
"""
from __future__ import annotations

import copy
import pathlib
import random

import numpy as np
import pytest

from meridian import api, codelaw, skill_gorus as sg, store

KOK = pathlib.Path(__file__).resolve().parents[1]
KART_YOLU = KOK / "research" / "cards" / "EDG-2026-078-skill-gorus-golge-siralama-kolu.yaml"
SETUP = "breakout_vcp"


# =================================================================================================
# YARDIMCILAR
# =================================================================================================
def _cf_satiri(tarih: str, ticker: str, r_multiple: float, *, skor: float = 50.0,
              screener: str = "test-skill") -> dict:
    """`counterfactual.collect`in içindeki yerel id-üreticiyle ŞEMASI birebir — `golge_siralama_
    kancasi`nin `hedef` biçimiyle (CF-{tarih}-{ticker}-{setup}) eşleşmesi BİLEREK budur (modül
    başlığı BEYANI)."""
    return {"id": f"CF-{tarih}-{ticker}-{SETUP}", "date": tarih, "ticker": ticker, "setup": SETUP,
            "score": skor, "screener": screener, "entered": True, "status": "closed",
            "exit_reason": "target", "r_multiple": r_multiple, "mfe_r": r_multiple + 0.2}


def _golge_satiri(tarih: str, ticker: str, sira_mevcut: int, sira_golge: int, n_gun: int, *,
                  sure_ms: float = 5.0, source_skill: str = "test-skill") -> dict:
    """`golge_siralama_kancasi`nin YAZDIĞI şemayla birebir — çözücü testleri kancayı ÇAĞIRMADAN,
    defteri doğrudan doldurur (çözücü saf okumadır, kancadan BAĞIMSIZ sınanabilir olmalı)."""
    return {"date": tarih, "ticker": ticker, "source_skill": source_skill,
            "hedef": f"CF-{tarih}-{ticker}-{SETUP}", "score": 50.0, "z_skill": 0.0,
            "score_golge": 50.0, "sira_mevcut": sira_mevcut, "sira_golge": sira_golge, "N": n_gun,
            "ustN_mevcut": bool(n_gun > 0 and sira_mevcut <= n_gun),
            "ustN_golge": bool(n_gun > 0 and sira_golge <= n_gun), "sure_ms": sure_ms}


def _sekiz_aday() -> list[dict]:
    """8 aday, 3 skill — SKOR AZALAN sırada (P3'ün `candidates.sort` SONRASI hâli). exhaustion-hammer
    3 aday (n>=3, KART ağırlığı VAR), vcp-screener 3 aday (n>=3, w=0), pullback-screener 2 aday
    (n<3 → z=0 kuralı — ama w zaten 0, bkz. ayrı `test_golge_kanca_n_altinda_z_sifir_zorlanir`)."""
    veri = [
        ("CCC", "stockbee-exhaustion-hammer-screener", 90.0),
        ("BBB", "stockbee-exhaustion-hammer-screener", 80.0),
        ("FFF", "vcp-screener", 75.0),
        ("AAA", "stockbee-exhaustion-hammer-screener", 70.0),
        ("EEE", "vcp-screener", 65.0),
        ("DDD", "vcp-screener", 60.0),
        ("HHH", "pullback-screener", 55.0),
        ("GGG", "pullback-screener", 50.0),
    ]
    return [{"date": "2026-09-08", "ticker": t, "source_skill": sk, "score": sc, "setup": SETUP}
            for t, sk, sc in veri]


def _beklenen_z_ve_golge(adaylar: list[dict]) -> tuple[dict, dict]:
    """Kartın formülünü BAĞIMSIZ olarak (SUT'un iç kodunu ÇAĞIRMADAN) yeniden hesaplar —
    beklenen değer SUT'tan değil SPESİFİKASYONDAN türer."""
    skorlar = np.asarray([c["score"] for c in adaylar], dtype=float)
    sd_kesit = float(skorlar.std())
    per: dict[str, list[float]] = {}
    for c in adaylar:
        per.setdefault(c["source_skill"], []).append(c["score"])
    istat = {}
    for sk, vals in per.items():
        arr = np.asarray(vals, dtype=float)
        istat[sk] = (float(arr.mean()), float(arr.std())) if len(arr) >= 3 and arr.std() > 0 else None
    z, golge = {}, {}
    for c in adaylar:
        i = istat.get(c["source_skill"])
        zc = 0.0 if i is None else (c["score"] - i[0]) / i[1]
        w = sg.KART_GOLGE_AGIRLIKLARI.get(c["source_skill"], 0.0)
        z[c["ticker"]] = zc
        golge[c["ticker"]] = c["score"] + w * zc * sd_kesit
    return z, golge


# =================================================================================================
# (1) KANCA — FORMÜL + MUTASYON 1 (candidates asla mutasyona uğramaz)
# =================================================================================================
def test_golge_kanca_z_score_golge_ve_siralar_dogru(sandbox_state):
    adaylar = _sekiz_aday()
    z_bekl, golge_bekl = _beklenen_z_ve_golge(adaylar)
    sonuc = sg.golge_siralama_kancasi(adaylar, N=2, dstr="2026-09-08")

    satirlar = {r["ticker"]: r for r in store.read_jsonl(sg.GOLGE_SIRALAMA_DEFTERI)}
    assert len(satirlar) == 8, "8 adayın hiçbiri esikte (max(2*2,20)=20) düşmemeliydi"
    assert sonuc["yazilan"] == 8 and sonuc["N"] == 2 and sonuc["n_aday"] == 8
    assert isinstance(sonuc["sure_ms"], float) and sonuc["sure_ms"] >= 0.0   # "sure_ms dolu"

    # sira_mevcut = girdi listesindeki POZİSYON (P3 ZATEN score-desc sıraladı, burada TEKRAR
    # sıralanmaz) — MUTASYON 1'in dayanağı: fonksiyon `candidates`i asla yeniden sıralamaz.
    for i, c in enumerate(adaylar, start=1):
        r = satirlar[c["ticker"]]
        assert r["sira_mevcut"] == i
        assert r["score"] == pytest.approx(c["score"])
        assert r["z_skill"] == pytest.approx(z_bekl[c["ticker"]], abs=1e-6)
        assert r["score_golge"] == pytest.approx(golge_bekl[c["ticker"]], abs=1e-6)
        assert r["sure_ms"] == sonuc["sure_ms"], "sure_ms o seansın TÜM satırlarında AYNI olmalı"

    # w=0 SKİLLERDE score_golge == score (BUGÜNKÜ DAVRANIŞ BİREBİR — kart formülü)
    for t in ("FFF", "EEE", "DDD", "HHH", "GGG"):
        assert satirlar[t]["score_golge"] == pytest.approx(satirlar[t]["score"])

    # sira_golge BAĞIMSIZ olarak score_golge'un AZALAN sırasıdır (rank hesaplaması da doğrulanır)
    golge_sira_bekl = {t: i for i, (t, _) in enumerate(
        sorted(golge_bekl.items(), key=lambda kv: kv[1], reverse=True), start=1)}
    for t, r in satirlar.items():
        assert r["sira_golge"] == golge_sira_bekl[t]

    # N=2 → ustN alanları yalnız sira<=2 için True
    for t, r in satirlar.items():
        assert r["ustN_mevcut"] == (r["sira_mevcut"] <= 2)
        assert r["ustN_golge"] == (r["sira_golge"] <= 2)


def test_golge_kanca_n_altinda_z_sifir_zorlanir(sandbox_state, monkeypatch):
    """Kart formülü: kesitte skill'in <3 adayı varsa z=0 — AĞIRLIK sıfır olsa bile ayırt edilemez
    olurdu, o yüzden burada GEÇİCİ olarak ağırlık verilip (yalnız bu testte; kart eşitliği testi
    AYRI ve gerçek karttan okur) kural bağımsız sınanır."""
    monkeypatch.setattr(sg, "KART_GOLGE_AGIRLIKLARI", {"az-uyeli": 0.5})
    adaylar = [
        {"date": "2026-09-08", "ticker": "X1", "source_skill": "az-uyeli", "score": 10.0, "setup": SETUP},
        {"date": "2026-09-08", "ticker": "X2", "source_skill": "az-uyeli", "score": 90.0, "setup": SETUP},
    ]
    sg.golge_siralama_kancasi(adaylar, N=1, dstr="2026-09-08")
    satirlar = {r["ticker"]: r for r in store.read_jsonl(sg.GOLGE_SIRALAMA_DEFTERI)}
    assert satirlar["X1"]["z_skill"] == 0.0 and satirlar["X2"]["z_skill"] == 0.0
    # z=0 olduğu için score_golge = score + w*0*sd = score (AĞIRLIK VARKEN BİLE)
    assert satirlar["X1"]["score_golge"] == pytest.approx(10.0)
    assert satirlar["X2"]["score_golge"] == pytest.approx(90.0)


def test_golge_kanca_N_sifir_veya_negatifte_sifira_cekilir_ve_satir_yine_yazilir(sandbox_state):
    adaylar = [{"date": "2026-09-08", "ticker": t, "source_skill": "vcp-screener", "score": float(i),
               "setup": SETUP} for i, t in enumerate(["A", "B", "C"])]
    sonuc = sg.golge_siralama_kancasi(adaylar, N=-5, dstr="2026-09-08")
    assert sonuc["N"] == 0 and sonuc["yazilan"] == 3        # negatif slot → 0, satır YİNE yazılır
    satirlar = store.read_jsonl(sg.GOLGE_SIRALAMA_DEFTERI)
    assert len(satirlar) == 3
    assert all(r["N"] == 0 and r["ustN_mevcut"] is False and r["ustN_golge"] is False
              for r in satirlar)


def test_golge_kanca_defter_esigi_max_2N_20_ile_sinirli(sandbox_state):
    """30 aday, TEK skill (w=0 → sira_golge == sira_mevcut, sıralamalar AYNI): N=5 → esik
    max(10,20)=20, yani skor sırasının İLK 20'si yazılır, kalan 10 (rank 21..30) düşer."""
    adaylar = [{"date": "2026-09-08", "ticker": f"T{i:02d}", "source_skill": "vcp-screener",
               "score": float(30 - i), "setup": SETUP} for i in range(30)]   # zaten score-desc
    sonuc = sg.golge_siralama_kancasi(adaylar, N=5, dstr="2026-09-08")
    satirlar = store.read_jsonl(sg.GOLGE_SIRALAMA_DEFTERI)
    assert sonuc["yazilan"] == 20 and len(satirlar) == 20
    assert max(r["sira_mevcut"] for r in satirlar) == 20


def test_golge_kanca_candidates_MUTASYONA_UGRAMAZ(sandbox_state, monkeypatch):
    """MUTASYON 1: kanca P3'ün `candidates`/`plans` çıktısını DEĞİŞTİRMEZ — kaldırılsa ya da
    ağırlık sıfırlansa/büyütülse davranış (candidates'in KENDİSİ) BAYT-EŞİT kalır. Kanca
    sıralamayı YERİNDE değiştirirse (`candidates.sort(...)` gibi) bu test KIRMIZI olur — manuel
    doğrulama raporda (geçici mutasyon + revert)."""
    adaylar = _sekiz_aday()
    once = copy.deepcopy(adaylar)
    sg.golge_siralama_kancasi(adaylar, N=2, dstr="2026-09-08")
    assert adaylar == once, "kanca candidates listesini DEĞİŞTİRDİ (w=0.169 varsayılan ağırlıkla)"

    # AYNI liste, AĞIRLIK 0.5'e büyütülmüş — daha güçlü bir gölge sıralaması bile candidates'i
    # DEĞİŞTİRMEMELİ (kanca yalnız YAN deftere yazar, girdiye asla dokunmaz).
    monkeypatch.setattr(sg, "KART_GOLGE_AGIRLIKLARI",
                        {sk: 0.5 for sk in {c["source_skill"] for c in adaylar}})
    sg.golge_siralama_kancasi(adaylar, N=2, dstr="2026-09-09")
    assert adaylar == once, "kanca candidates listesini DEĞİŞTİRDİ (w=0.5 ile)"


# =================================================================================================
# (2) ÇÖZÜCÜ — Δrank-IC + POZİTİF KONTROL (a)/(b)
# =================================================================================================
def _yaz_seans(tarih: str, mevcut_sira: list[int], golge_sira: list[int], R: list[float], *,
              n_gun: int = 2, tickerler=("T1", "T2", "T3", "T4")) -> None:
    for j, tick in enumerate(tickerler):
        store.append_jsonl(sg.GOLGE_SIRALAMA_DEFTERI,
                           _golge_satiri(tarih, tick, mevcut_sira[j], golge_sira[j], n_gun))
        store.append_jsonl("counterfactuals.jsonl", _cf_satiri(tarih, tick, R[j]))


def test_cozucu_delta_rank_ic_isareti_beklenen_ve_ustN_kesisimi_olculur(sandbox_state):
    """Sentetik: gölge sıralaması R'yi TAM (rho=1) yakalar, mevcut sıralaması SEANS BAŞINA
    karıştırılmış (rho'su 0/±0,8/±0,6 arası döner) — Δrank-IC ortalaması BELİRGİN pozitif olmalı
    (kartın "gölge daha iyi eşlenmiş" hipotezinin sentetik karşılığı). Sayılar bu dosyanın
    başlığında ELLE türetilip (bkz. brief teslim raporu) `tarih_kumeli_bootstrap`in kendi
    tohumuyla DOĞRULANDI — burada sabit noktalar olarak sınanıyor (regresyon çivisi)."""
    R = [0.30, 0.20, 0.10, 0.00]
    golge_sira = [1, 2, 3, 4]
    mevcut_varyant = [
        [2, 4, 1, 3], [3, 1, 4, 2], [4, 2, 3, 1], [1, 3, 2, 4], [2, 1, 4, 3],
    ]
    for i, mv in enumerate(mevcut_varyant):
        _yaz_seans(f"2026-09-{i + 8:02d}", mv, golge_sira, R, n_gun=2)

    r = sg.golge_kol_raporu()
    assert r["n_seans"] == 5
    assert r["durum"] == "ÖLÇÜLDÜ — ÖRNEKLEM YETERSİZ"        # n_seans(5) < KART_N_MIN_SEANS(30)
    assert r["n_min_seans"] == sg.KART_N_MIN_SEANS
    assert r["eslesmeyen_n"] == 0
    assert r["delta_rank_ic"]["ort"] == pytest.approx(0.88, abs=1e-6)
    assert r["delta_rank_ic"]["lo"] == pytest.approx(0.40, abs=1e-6)
    assert r["ustN_kesisim_ort"] == pytest.approx(0.6, abs=1e-6)
    assert r["sure_p95_ms"] == pytest.approx(5.0)
    assert r["ustN_kesisim_esigi_gecti"] is True              # 0,6 >= KART_GOLGE_USTN_KESISIM_MIN(0,5)


def test_pozitif_kontrol_a_karistirilmis_golge_CI_sifiri_icerir(sandbox_state):
    """PK (a) — kart `pozitif_kontrol`: RASTGELE görüş (mevcut VE gölge ikisi de karıştırılmış,
    R'den bağımsız) → Δrank-IC CI'ı sıfırı İÇERMELİ. Tohum sabit (42) — reprodüktif."""
    R = [0.30, 0.20, 0.10, 0.00]
    rnd = random.Random(42)
    for i in range(20):
        mevcut = rnd.sample([1, 2, 3, 4], 4)
        golge = rnd.sample([1, 2, 3, 4], 4)
        _yaz_seans(f"2026-09-{i + 1:02d}", mevcut, golge, R, n_gun=2)

    r = sg.golge_kol_raporu()
    assert r["n_seans"] == 20
    lo, hi = r["delta_rank_ic"]["lo"], r["delta_rank_ic"]["hi"]
    assert lo is not None and hi is not None
    assert lo <= 0.0 <= hi, (
        f"alet RASTGELE gölge sıralamasını anlamlı gösterdi (çözücü KÖR değil): CI=[{lo};{hi}]")


def test_pozitif_kontrol_b_sonucu_bilen_siralama_delta_belirgin_pozitif(sandbox_state):
    """PK (b) — kart `pozitif_kontrol`: gerçekleşen R'yi TAM bilen sentetik gölge sıralaması
    (YALNIZ bu testte; canlı deftere böyle bir sıra ASLA yazılmaz) → Δ belirgin pozitif
    (CI-altı > 0). Ayrışmıyorsa (PK a ile aynı sonucu verirse) çözücü KÖRDÜR (kart notu)."""
    R = [0.30, 0.20, 0.10, 0.00]
    golge_bilen = [1, 2, 3, 4]                # R azalan → sıra artan: rho=1 GARANTİ
    rnd = random.Random(7)
    for i in range(20):
        mevcut = rnd.sample([1, 2, 3, 4], 4)
        _yaz_seans(f"2026-09-{i + 1:02d}", mevcut, golge_bilen, R, n_gun=2)

    r = sg.golge_kol_raporu()
    assert r["delta_rank_ic"]["ort"] > 0.5
    lo = r["delta_rank_ic"]["lo"]
    assert lo is not None and lo > 0.0, (
        f"MUTASYON 2 ŞÜPHESİ: çözücü sonucu-bilen sıralamayı bile ayırt edemedi — {r['delta_rank_ic']}")


def test_cozucu_eslesmeyen_hedef_sayilir_ve_hukum_bozulmaz(sandbox_state):
    """Bir seansın adaylarından biri hiç CF çözülmemişse (rps<=0/tavan/hiç girmemiş) —
    `eslesmeyen_n`de SAYILIR, sessizce düşmez; kalan eşleşenlerle hüküm YİNE kurulur."""
    for j, tick in enumerate(["T1", "T2", "T3"]):
        store.append_jsonl(sg.GOLGE_SIRALAMA_DEFTERI,
                           _golge_satiri("2026-09-08", tick, j + 1, j + 1, 2))
        if tick != "T3":                       # T3'ün cf'i HİÇ yazılmadı — eşleşmeyen
            store.append_jsonl("counterfactuals.jsonl", _cf_satiri("2026-09-08", tick, 0.1 * (3 - j)))
    r = sg.golge_kol_raporu()
    assert r["eslesmeyen_n"] == 1
    assert r["n_seans"] == 1                    # kalan 2 eşleşmeyle rank-IC yine kurulabildi


def test_cozucu_bos_defterde_OLCULEMEDI_ve_neden_dolu(sandbox_state):
    r = sg.golge_kol_raporu()
    assert r["durum"] == "ÖLÇÜLEMEDİ" and r["neden"]
    assert r["n_seans"] == 0 and r["delta_rank_ic"] is None


# =================================================================================================
# (3) PENCERE SAYACI — GÜN-ANAHTARLI İDEMPOTENS + ARDIŞIKLIK
# =================================================================================================
def _sahte_rapor(skill: str, yuzey: str, yon: int, sagkalan: bool, n: int = 40) -> dict:
    return {"yuzeyler": {yuzey: {"durum": "ölçüldü", "skiller": {
        skill: {"yon": yon, "n": n, "fdr": {"sagkalan": sagkalan}}}}}}


def test_pencere_yaz_ayni_gun_ikinci_kosum_tekrar_yazmaz(sandbox_state):
    rs = _sahte_rapor("test-skill", "aday-siralayici", 1, True)
    once = sg.pencere_yaz(rs, kosum_tarihi="2026-09-08")
    assert once["yazilan"] == 1 and once["atlandi"] is False
    ikinci = sg.pencere_yaz(rs, kosum_tarihi="2026-09-08")
    assert ikinci["yazilan"] == 0 and ikinci["atlandi"] is True
    assert len(store.read_jsonl(sg.PENCERE_DEFTERI)) == 1


def test_pencere_yaz_olculmeyen_yuzeyi_atlar_ama_olculeni_yazar(sandbox_state):
    rs = {"yuzeyler": {
        "aday-siralayici": {"durum": "ölçüldü", "skiller": {"a": {"yon": 1, "n": 40, "fdr": {"sagkalan": True}}}},
        "cikis": {"durum": "HÜKÜM YOK", "neden": "girdi bekçisi", "skiller": {}},
    }}
    sonuc = sg.pencere_yaz(rs, kosum_tarihi="2026-09-08")
    assert sonuc["yazilan"] == 1
    satirlar = store.read_jsonl(sg.PENCERE_DEFTERI)
    assert len(satirlar) == 1 and satirlar[0]["yuzey"] == "aday-siralayici"


def test_ardisik_pencere_uc_farkli_gun_ayni_yon(sandbox_state):
    for gun in ["2026-09-08", "2026-09-09", "2026-09-10"]:
        store.append_jsonl(sg.PENCERE_DEFTERI, {"kosum_tarihi": gun, "skill": "test-skill",
                                                "yuzey": "aday-siralayici", "yon": 1,
                                                "sagkalan": True, "n": 40})
    ozet = sg._pencere_ozeti()[("test-skill", "aday-siralayici")]
    assert ozet["ardisik_pencere"] == 3 and ozet["pencere_n"] == 3


def test_ardisik_pencere_yon_degisince_ESKI_SERI_TASINMAZ(sandbox_state):
    for gun in ["2026-09-08", "2026-09-09", "2026-09-10"]:
        store.append_jsonl(sg.PENCERE_DEFTERI, {"kosum_tarihi": gun, "skill": "test-skill",
                                                "yuzey": "aday-siralayici", "yon": 1,
                                                "sagkalan": True, "n": 40})
    store.append_jsonl(sg.PENCERE_DEFTERI, {"kosum_tarihi": "2026-09-11", "skill": "test-skill",
                                            "yuzey": "aday-siralayici", "yon": -1,
                                            "sagkalan": True, "n": 40})
    ozet = sg._pencere_ozeti()[("test-skill", "aday-siralayici")]
    # YÖN DEĞİŞTİ: 3'lük eski seri TAŞINMAZ (asla 4 dönmez) — sayaç YENİ yönle 1'den başlar
    # (bugünkü tek pencere kendi başına sağkalmışsa).
    assert ozet["ardisik_pencere"] == 1
    assert ozet["pencere_n"] == 4


def test_ardisik_pencere_sagkalmayan_pencere_seriyi_kirar(sandbox_state):
    for gun, sagkalan in [("2026-09-08", True), ("2026-09-09", False), ("2026-09-10", True)]:
        store.append_jsonl(sg.PENCERE_DEFTERI, {"kosum_tarihi": gun, "skill": "test-skill",
                                                "yuzey": "aday-siralayici", "yon": 1,
                                                "sagkalan": sagkalan, "n": 40})
    ozet = sg._pencere_ozeti()[("test-skill", "aday-siralayici")]
    assert ozet["ardisik_pencere"] == 1        # yalnız EN SON (sağkalan) pencere sayılır
    assert ozet["pencere_n"] == 3


def test_rapor_terfi_satirinda_ardisik_pencere_alani_VAR(sandbox_state, monkeypatch, tmp_path):
    """Uçtan uca: `ops/skill_gorus_uret.py`nin yazdığı pencere defteri `rapor()`ın terfi
    satırlarına AKAR mı? (`_mini_defterler` deseninin AYNISI, tek skill, EDG-2026-078 dilimi.)"""
    from meridian import analytics, config as _cfg, skills

    monkeypatch.setattr(_cfg, "SKILL_GORUS_URETIM_ACIK", True)
    monkeypatch.setattr(analytics, "skill_attribution", lambda: {"skills": []})
    kok = tmp_path / "skills"
    (kok / "vcp-screener").mkdir(parents=True)
    (kok / "vcp-screener" / "SKILL.md").write_text("---\nname: vcp-screener\ndescription: x.\n---\n")
    monkeypatch.setattr(_cfg, "SKILLS", kok)
    monkeypatch.setattr(skills, "_DESC_CACHE", None)
    store.write_json("skills_registry.json", {"skills": {
        "vcp-screener": {"category": "swing", "enabled": True, "mode": "active",
                         "pipeline": "P2_SCREEN"}}})

    rows = [{"id": f"CF-x-{i}", "date": f"2026-06-{i % 10 + 1:02d}", "ticker": "AAA",
            "setup": "breakout_vcp", "score": float(i), "screener": "vcp-screener",
            "entered": True, "status": "closed", "exit_reason": "target",
            "r_multiple": float(i) * 0.01, "mfe_r": float(i) * 0.01 + 0.2} for i in range(40)]
    store.write_jsonl("counterfactuals.jsonl", rows)
    store.write_json("exit_efficiency.json", {"n": len(rows), "avg_left_r": 0.2})
    sg.topla(apply=True, tavan=None)

    for gun in ["2026-08-01", "2026-08-02"]:
        store.append_jsonl(sg.PENCERE_DEFTERI, {"kosum_tarihi": gun, "skill": "vcp-screener",
                                                "yuzey": "aday-siralayici", "yon": 1,
                                                "sagkalan": True, "n": 40})

    r = sg.rapor()
    terfi = [t for t in r["terfi_adaylari"]
            if t["skill"] == "vcp-screener" and t["yuzey"] == "aday-siralayici"]
    assert terfi, "sentetik kusursuz monoton seri terfi adayı üretmedi — fikstür bozuk olabilir"
    assert terfi[0]["ardisik_pencere"] == 2 and terfi[0]["pencere_n"] == 2
    assert "golge_kol" in r
    skills._DESC_CACHE = None


# =================================================================================================
# (4) KART EŞİTLİĞİ — sabitler koddan DEĞİL karttan gelir, kod onları DEĞİŞTİREMEZ
# =================================================================================================
def test_kart_sabitleri_YAML_ile_AYRISMAZ():
    kart = KART_YOLU.read_text(encoding="utf-8")
    assert "card_id: EDG-2026-078" in kart and sg.KART_GOLGE_ID == "EDG-2026-078"
    assert "stockbee-exhaustion-hammer-screener: 0.169" in kart
    assert sg.KART_GOLGE_AGIRLIKLARI == {"stockbee-exhaustion-hammer-screener": 0.169}
    assert "n_min 30 seans" in kart and sg.KART_N_MIN_SEANS == 30
    assert "üst-N kesişimi ort ≥ 0,50" in kart and sg.KART_GOLGE_USTN_KESISIM_MIN == pytest.approx(0.50)


def test_kart_dosyasi_registered_ve_agirliklar_alani_kodla_TEK_KAYNAK():
    kart = KART_YOLU.read_text(encoding="utf-8")
    assert "status: registered" in kart
    # `agirliklar:` satırı kartta TEK yerdedir; kodun okuduğu değer o satırdan TÜRER (uydurulmaz).
    satir = next(s for s in kart.splitlines() if s.strip().startswith("agirliklar:"))
    assert "0.169" in satir


# EVREN GERÇEK `skills/` KLASÖRÜNE DOKUNMASIN (izolasyon): `rapor()`ın YOLU golge_kol'a hiç
# bakmadan `evren()` → `skills.catalog()` → gerçek `config.SKILLS` okur (`kayit` fikstürünün
# test_skill_gorus_v218.py'de sandboxladığı TAM O şey). `golge_kol_raporu` bunu ÇAĞIRMAZ (yalnız
# defter + `_gozlemler()`), ama `rapor()`/`api._eksen2_gorus()` üstünden geçen testler için evren()
# sahte bir sabitle DEĞİŞTİRİLİR — testin sonucu operatörün diskindeki skill sayısına bağlı olmasın.
def _evren_sahte() -> dict:
    return {"evren": [], "disarida": {}, "sayim": {"evren": 0}, "beyan": "test-sahte evren"}


# =================================================================================================
# (5) API — golge_kol boş defterde ÖLÇÜLEMEDİ + neden (uydurma yok)
# =================================================================================================
def test_api_eksen2_gorus_bos_defterde_golge_kol_OLCULEMEDI_ve_neden_dolu(sandbox_state, monkeypatch):
    monkeypatch.setattr(sg, "evren", _evren_sahte)
    r = api._eksen2_gorus()
    assert "golge_kol" in r
    gk = r["golge_kol"]
    assert gk is not None and gk["durum"] == "ÖLÇÜLEMEDİ" and gk["neden"]


def test_api_eksen2_gorus_golge_kol_alani_defterle_DOLAR(sandbox_state, monkeypatch):
    monkeypatch.setattr(sg, "evren", _evren_sahte)
    R = [0.30, 0.20, 0.10, 0.00]
    for i in range(5):
        _yaz_seans(f"2026-09-{i + 8:02d}", [2, 4, 1, 3], [1, 2, 3, 4], R, n_gun=2)
    r = api._eksen2_gorus()
    gk = r["golge_kol"]
    assert gk["n_seans"] == 5 and gk["delta_rank_ic"] is not None


def test_api_gorus_okumasi_dusunce_golge_kol_da_OLCULEMEDI_kalir(sandbox_state, monkeypatch):
    """Rapor()'ın TAMAMI düşerse (girdi bozuk) `golge_kol` de ÖLÇÜLEMEDİ olur — ama bu ayrı bir
    dal (`_golge_kol_guvenli`), yani golge_kol_raporu'nun KENDİSİ düşerse rapor()'un GERİSİ
    ETKİLENMEZ (ayrı test aşağıda)."""
    def _patlar():
        raise RuntimeError("sentetik bozulma")
    monkeypatch.setattr(sg, "rapor", _patlar)
    r = api._eksen2_gorus()
    assert r["durum"] == "ÖLÇÜLEMEDİ" and r["golge_kol"] is None


def test_golge_kol_dusunce_raporun_KALANI_etkilenmez(sandbox_state, monkeypatch):
    """`rapor()`ın kalanı (terfi/emeklilik/kova_sayimi) `golge_kol_raporu` düşse bile YAŞAR —
    yeni (2026-09-05) YAN ölçüm, EDG-2026-019'un üç aylık ana yüzeyini düşüremez."""
    monkeypatch.setattr(sg, "evren", _evren_sahte)

    def _patlar():
        raise RuntimeError("sentetik golge_kol arızası")
    monkeypatch.setattr(sg, "golge_kol_raporu", _patlar)
    r = sg.rapor()
    assert r["golge_kol"]["durum"] == "ÖLÇÜLEMEDİ" and r["golge_kol"]["neden"]
    assert r["terfi_adaylari"] == [] and r["kova_sayimi"] == {}    # boş ama VAR — düşmedi


# =================================================================================================
# CODELAW — yeni iki defter DECLARED_SINKS'te doğru beyanlı (mekanik Yasa 6 kapısı)
# =================================================================================================
def test_yeni_defterler_codelaw_ihlali_URETMEZ():
    g = codelaw.artifact_graph()
    assert "golge_siralama.jsonl" not in g["violations"]
    assert "skill_gorus_pencereler.jsonl" not in g["violations"]
    assert g["artifacts"]["golge_siralama.jsonl"]["unread"] is True     # statik graf göremez
    assert "golge_siralama.jsonl" in codelaw.DECLARED_SINKS
    assert "skill_gorus_pencereler.jsonl" in codelaw.DECLARED_SINKS
    assert len(codelaw.DECLARED_SINKS["golge_siralama.jsonl"]) >= 30
    assert len(codelaw.DECLARED_SINKS["skill_gorus_pencereler.jsonl"]) >= 30
