"""KILL#4 DARALTMASI — kart EXE-2026-002-R1'in uygulama borcu (v228, 2026-08-09).

R1 kill#4'ün TANIM KUSURUNU düzeltir: eski geniş ölçüt ("eşleşmeyen oranı > %20 → hüküm YOK")
İKİ AYRI OLGUYU tek kovaya atıyordu ve ayırt edemiyordu.
  (a) BOZULMA — defter güvenilmez, hüküm verilemez: `golge_bozuk` (gölge satırı biçimsiz) +
      `bps_yok` (eşleşti ama fark hesaplanamadı). kill#4 bunlarda DOĞRU tetiklenir.
  (b) MEŞRU DOLMAMA — `eod_yok`: gölge sağlam ama iç EOD motoru doldurmamayı SEÇTİ (limit kaçtı,
      kapı düşürdü, gap vetosu). Bozulma DEĞİL, motorun kararıdır; eşleşme YAPISAL olarak oluşmaz.
      `kapsam_disi` olarak ADIYLA sayılır, hükmü GEÇERSİZ KILMAZ — yalnız eşleşen çift sayısını
      düşürür ve n_min kapısına havale edilir.

Bu dosya YALNIZ daraltmayı çiviler. Eşikler (n_min=20, %20, B=10.000, E3 bandı) DEĞİŞMEDİ ve bu
tur onlara DOKUNMAZ — kart dokunulmazdır, hükmü Rol-1 işler. Bugün canlı etki %0'dır (eşleşmeme
oranı 0) ve bu dosya bunu da çiviler: hüküm DEĞİŞMEDİ.

NOT (v212 uyumlandı): `tests/test_faz5_cikis_v212.py::test_B_kill4_BOZULMA_yuzde_20_ustunde_HUKUM_YOK`
eskiden kill#4'ü `eod_yok` satırlarıyla (P-KAYIP-X/Y) tetikliyordu; R1 bu satırları `kapsam_disi`ye
taşıyınca o fikstür BOZULMA sınıfına (golge_bozuk) çevrildi ve testin AMACI (%20 ÜSTÜNDE hüküm YOK)
korundu. `eod_yok`un artık kill#4'ü TETİKLEMEDİĞİ burada çivilidir (`test_b_eod_yok_...` +
`test_ab_AYNI_ORANDA_...`), o yüzden v212'de tekrarlanmadı.
"""
from __future__ import annotations

import pytest

from meridian import faz5_cikis as f5, intraday_shadow as ish, store


# =================================================================================================
# fikstür yardımcıları — canlı satır ŞEKLİYLE aynı (intraday_shadow.record çıktısı)
# =================================================================================================
def _golge(pid: str, date: str, sim_fill, qty: int = 10, risk: float = 100.0) -> dict:
    return {"plan_id": pid, "ticker": pid.split("-")[-1], "date": date, "sim_fill": sim_fill,
            "qty": qty, "risk_dollars": risk, "status": "would_submit",
            "entry_trigger": 99.0, "bar_open": 99.0, "sim_price_rule": "max(bar_open, entry_trigger)"}


def _defter(rows: list) -> None:
    for r in rows:
        store.append_jsonl(ish.ORDERS_FILE, r)


def _eod_yaz(pairs: list) -> None:
    for pid, entry, side in pairs:
        store.append_jsonl("trades.jsonl", {"plan_id": pid, "entry": entry, "side": side,
                                            "ticker": pid.split("-")[-1]})


def _tarih(i: int) -> str:
    return f"2026-08-{(i % 27) + 1:02d}"


def _eslesti(n: int, pre: str = "E") -> tuple[list, list]:
    """n EŞLEŞEN çift (gölge + geçerli EOD, long). Günlere yayılır ki tek-küme uç hâline düşmesin."""
    golge, eod = [], []
    for i in range(n):
        pid = f"P-{pre}-{i}"
        golge.append(_golge(pid, _tarih(i), 99.0))
        eod.append((pid, 100.0, "long"))
    return golge, eod


def _eod_yok(n: int, pre: str = "Y") -> list:
    """n MEŞRU DOLMAMA: gölge sağlam, EOD karşılığı YOK → `sinif == eod_yok` (b)."""
    return [_golge(f"P-{pre}-{i}", _tarih(i), 99.0) for i in range(n)]


def _golge_bozuk(n: int, pre: str = "B") -> list:
    """n BOZULMA: `sim_fill` sayıya çevrilemez ama None DEĞİL → evrene girer, `golge_bozuk` (a)."""
    return [_golge(f"P-{pre}-{i}", _tarih(i), "BOZUK-BICIM") for i in range(n)]


def _bps_yok(n: int, pre: str = "Q") -> tuple[list, list]:
    """n BOZULMA: eşleşti ama yön ölçülemedi (EOD `side=None`) → bps hesaplanamaz → `bps_yok` (a)."""
    golge, eod = [], []
    for i in range(n):
        pid = f"P-{pre}-{i}"
        golge.append(_golge(pid, _tarih(i), 99.0))
        eod.append((pid, 100.0, None))
    return golge, eod


# =================================================================================================
# (a) BOZULMA → kill#4 TETİKLENİR
# =================================================================================================
def test_a_golge_bozuk_kill4_TETIKLER(sandbox_state):
    """5 golge_bozuk / (5+15) = %25 > %20 → defter bütünlüğü sorunu, HÜKÜM YOK."""
    golge_e, eod = _eslesti(15)
    _defter(golge_e + _golge_bozuk(5))
    _eod_yaz(eod)
    h = f5.cikis_olcumu()

    assert h["durum"] == "olculemedi" and h["gecer"] is False
    assert "KILL#4" in h["neden"] and "kök-neden" in h["neden"].lower()
    assert "BOZULMUŞ" in h["neden"]
    b = h["olcum"]["eslesmeyen"]["bozulma"]
    assert b["n"] == 5 and b["oran"] == pytest.approx(0.25) and b["payda"] == 20
    assert h["olcum"]["eslesmeyen"]["kapsam_disi"]["n"] == 0
    assert h["olcum"]["eslesmeyen"]["sinif_dagilimi"] == {"golge_bozuk": 5}
    assert h["olcum"]["n_eslesen"] == 15, "15 geçerli çift VARDI ama defter bütünlüğü düştü"
    assert h["olcum"]["ortalama_bps"] is None and h["olcum"]["ci"] is None


def test_a_bps_yok_da_BOZULMA_kill4_TETIKLER(sandbox_state):
    """bps_yok da (a) bozulmadır: eşleşti ama fark hesaplanamadı. 5/(5+15) = %25 → tetikler."""
    golge_e, eod_e = _eslesti(15)
    golge_q, eod_q = _bps_yok(5)
    _defter(golge_e + golge_q)
    _eod_yaz(eod_e + eod_q)
    h = f5.cikis_olcumu()

    assert h["durum"] == "olculemedi" and "KILL#4" in h["neden"]
    assert h["olcum"]["eslesmeyen"]["sinif_dagilimi"] == {"bps_yok": 5}
    b = h["olcum"]["eslesmeyen"]["bozulma"]
    assert b["n"] == 5 and b["oran"] == pytest.approx(0.25)
    assert any("yön ölçülemedi" in e["neden"] for e in b["nedenler"])


# =================================================================================================
# (b) MEŞRU DOLMAMA → kill#4 TETİKLENMEZ, kapsam_disi, n_min'e havale
# =================================================================================================
def test_b_eod_yok_kill4_TETIKLEMEZ_kapsam_disi_n_min_e_havale(sandbox_state):
    """5 eod_yok + 15 eşleşen. Eski ölçüt %25 der ve susardı; YENİ ölçüt bozulma=0 görür,
    kill#4 tetiklenmez. eod_yok'un TEK etkisi n'i düşürmektir → 'ÖRNEKLEM YETERSİZ (15/20)'."""
    golge_e, eod = _eslesti(15)
    _defter(golge_e + _eod_yok(5))
    _eod_yaz(eod)
    h = f5.cikis_olcumu()

    assert h["durum"] == "olculdu", "eod_yok bozulma DEĞİL — hüküm GEÇERSİZ KILINMAZ"
    assert "KILL#4" not in (h["neden"] or "")
    assert "ÖRNEKLEM YETERSİZ (15/20)" in h["neden"], "eod_yok yalnız n'i düşürdü → n_min kapısı"
    e = h["olcum"]["eslesmeyen"]
    assert e["bozulma"]["n"] == 0 and e["bozulma"]["oran"] == pytest.approx(0.0)
    assert e["kapsam_disi"]["n"] == 5 and e["kapsam_disi"]["siniflar"] == ["eod_yok"]
    assert len(e["kapsam_disi"]["adlar"]) == 5, "kart: sessizce düşürülmez — ADIYLA raporlanır"
    assert e["sinif_dagilimi"] == {"eod_yok": 5}
    assert h["olcum"]["n_eslesen"] == 15


def test_ab_AYNI_ORANDA_bozulma_TETIKLER_eod_yok_TETIKLEMEZ(sandbox_state):
    """(a)/(b) AYRIM KANITI, AYNI eşleşmeme oranında (2/6 ≈ %33). İki fikstür bit bit aynı
    şekilde (4 eşleşen + 2 eşleşmeyen), fark yalnız eşleşmeyenin SINIFI. Bu, v212'nin eod_yok
    ile kill#4 tetikleyen senaryosunun DÜZELTİLMİŞ hâlidir: doğru sınıf bozulmadır."""
    # (a) BOZULMA: 4 eşleşen + 2 golge_bozuk → tetikler
    golge_e, eod = _eslesti(4)
    _defter(golge_e + _golge_bozuk(2))
    _eod_yaz(eod)
    ha = f5.cikis_olcumu()
    assert ha["durum"] == "olculemedi" and "KILL#4" in ha["neden"]
    assert ha["olcum"]["eslesmeyen"]["bozulma"]["oran"] == pytest.approx(round(2 / 6, 4))

    # (b) MEŞRU DOLMAMA: aynı 4 eşleşen + 2 eod_yok → TETİKLEMEZ (kapsam_disi)
    store.write_jsonl(ish.ORDERS_FILE, [])          # defteri temizle, aynı evreni yeniden kur
    store.write_jsonl("trades.jsonl", [])
    golge_e, eod = _eslesti(4)
    _defter(golge_e + _eod_yok(2))
    _eod_yaz(eod)
    hb = f5.cikis_olcumu()
    assert hb["durum"] == "olculdu" and "KILL#4" not in (hb["neden"] or "")
    assert "ÖRNEKLEM YETERSİZ (4/20)" in hb["neden"]
    assert hb["olcum"]["eslesmeyen"]["bozulma"]["n"] == 0
    assert hb["olcum"]["eslesmeyen"]["kapsam_disi"]["n"] == 2


def test_c_eod_yok_PAYDAYA_girmez_SEYRELTMEZ(sandbox_state):
    """PAYDA KANITI: eod_yok kill#4 paydasından DIŞLANIR (kartın 'yalnız n'i düşürür' beyanı).
    3 golge_bozuk + 10 eod_yok + 5 eşleşen → oran 3/(3+5) = %37,5 > %20 → TETİKLER.
    eod_yok paydada OLSAYDI 3/18 = %16,7 < %20 çıkar ve tetiklemezdi — yani seyreltme etkisi
    kartın yasakladığı İKİNCİ etkidir. Bu test o etkinin OLMADIĞINI çiviler."""
    golge_e, eod = _eslesti(5)
    _defter(golge_e + _golge_bozuk(3) + _eod_yok(10))
    _eod_yaz(eod)
    h = f5.cikis_olcumu()

    assert h["durum"] == "olculemedi" and "KILL#4" in h["neden"]
    b = h["olcum"]["eslesmeyen"]["bozulma"]
    assert b["n"] == 3 and b["payda"] == 8 and b["oran"] == pytest.approx(0.375)
    assert h["olcum"]["eslesmeyen"]["kapsam_disi"]["n"] == 10
    # RAPOR oranı (evren paydalı) kill oranından FARKLIDIR ve karıştırılmamalıdır.
    assert h["olcum"]["eslesmeyen"]["oran"] == pytest.approx(round(13 / 18, 4))
    assert "10 eod_yok kapsam DIŞI" in h["neden"]


def test_b_eod_yok_HUKMU_GECERSIZ_KILMAZ_n_yeterince(sandbox_state):
    """n_min DOLDUĞUNDA eod_yok'un varlığı ölçümü DURDURMAZ: 20 eşleşen + 5 eod_yok → kill#4
    yok, ölçüm CI aşamasına geçer (durum 'olculdu'). eod_yok yalnız bir kenarda ADIYLA durur."""
    golge_e, eod = _eslesti(20)
    _defter(golge_e + _eod_yok(5))
    _eod_yaz(eod)
    h = f5.cikis_olcumu()

    assert h["durum"] == "olculdu"
    assert "KILL#4" not in (h["neden"] or ""), "eod_yok kill#4'ü tetiklememeli"
    assert h["olcum"]["n_eslesen"] == 20 and h["olcum"]["ci"] is not None
    assert h["olcum"]["eslesmeyen"]["kapsam_disi"]["n"] == 5
    assert h["olcum"]["eslesmeyen"]["bozulma"]["n"] == 0


# =================================================================================================
# BUGÜNKÜ CANLI YÜK — hüküm DEĞİŞMEDİ (daraltma %0 etkilidir)
# =================================================================================================
def test_d_bugunku_canli_yuk_n4_oran0_HUKUM_DEGISMEDI(sandbox_state):
    """Canlı 4b defteri (2026-08-07): n=4, tek gün kümesi, eşleşmeme oranı %0. Eşleşmeyen HİÇ
    yokken daraltma tanım gereği NO-OP'tur (bozulma=0, kapsam_disi=0) — hüküm eskisiyle bit bit
    aynı: 'ÖRNEKLEM YETERSİZ (4/20)', kilit FAIL-CLOSED kapalı, CI tek kümede None."""
    golge, eod = [], []
    for i in range(4):                                   # DÖRDÜ DE aynı gün (canlı: n_kume=1)
        pid = f"P-CANLI-{i}"
        golge.append(_golge(pid, "2026-08-06", 99.0))
        eod.append((pid, 100.0, "long"))
    _defter(golge)
    _eod_yaz(eod)
    h = f5.cikis_olcumu()

    assert h["durum"] == "olculdu" and h["gecer"] is False
    assert "ÖRNEKLEM YETERSİZ (4/20)" in h["neden"]
    assert h["olcum"]["n_eslesen"] == 4
    assert h["olcum"]["ci"]["n_kume"] == 1 and h["olcum"]["ci"]["alt"] is None
    e = h["olcum"]["eslesmeyen"]
    assert e["n"] == 0 and e["oran"] == pytest.approx(0.0)
    assert e["bozulma"]["n"] == 0 and e["bozulma"]["oran"] == pytest.approx(0.0)
    assert e["kapsam_disi"]["n"] == 0


# =================================================================================================
# RAPOR YAPISI — ADIYLA + geriye dönük uyumluluk (pano okuyucuları)
# =================================================================================================
def test_e_rapor_yapisi_ADIYLA_ve_geriye_donuk_uyumlu(sandbox_state):
    """Karışık yük (1 golge_bozuk + 3 eod_yok + 10 eşleşen; oran 1/11 → tetiklemez). Hem YENİ
    alt-yapılar (`bozulma`, `kapsam_disi`) hem de pano okuyucusunun beklediği ESKİ alanlar
    (`n`, `oran`, `kill_esigi`, `sinif_dagilimi`) yerinde olmalı; iki ad kümesi AYRIK ve birleşimi
    tüm eşleşmeyeni vermeli."""
    golge_e, eod = _eslesti(10)
    _defter(golge_e + _golge_bozuk(1) + _eod_yok(3))
    _eod_yaz(eod)
    h = f5.cikis_olcumu()

    assert h["durum"] == "olculdu" and "ÖRNEKLEM YETERSİZ (10/20)" in h["neden"]
    e = h["olcum"]["eslesmeyen"]
    # geriye dönük uyumluluk (v219 pano fikstürü + statik okuyucu)
    for alan in ("n", "oran", "kill_esigi", "adlar", "adlar_kirpildi", "nedenler",
                 "sinif_dagilimi", "bozulma", "kapsam_disi"):
        assert alan in e, f"eslesmeyen `{alan}` alanını kaybetti"
    assert e["kill_esigi"] == f5.KILL_ESLESMEME_ORANI == 0.20
    assert e["n"] == 4 and e["oran"] == pytest.approx(round(4 / 14, 4))
    assert e["sinif_dagilimi"] == {"eod_yok": 3, "golge_bozuk": 1}
    # ADIYLA + AYRIK
    bozulma_adlari, kapsam_adlari = set(e["bozulma"]["adlar"]), set(e["kapsam_disi"]["adlar"])
    assert len(bozulma_adlari) == 1 and len(kapsam_adlari) == 3
    assert bozulma_adlari.isdisjoint(kapsam_adlari)
    assert bozulma_adlari | kapsam_adlari == set(e["adlar"])


def test_f_esikler_ve_kapsam_disi_sinifi_DONMUS():
    """Bu tur EŞİĞE DOKUNMAZ: %20, n_min, B kartta donmuştur. Değişen yalnız ölçütün UYGULANDIĞI
    KÜMEdir. Kapsam dışı sınıf açıkça `eod_yok`tur; başka her eşleşmeme bozulma sayılır (fail-closed)."""
    assert f5.KILL_ESLESMEME_ORANI == 0.20
    assert (f5.N_MIN, f5.BOOTSTRAP_N, f5.CI_SEVIYE) == (20, 10_000, 0.95)
    assert f5.KAPSAM_DISI_SINIFLARI == ("eod_yok",)
