"""FAZ-5 ÇIKIŞ ÖLÇÜMÜ — kart EXE-2026-002'nin kodu (v212, 2026-08-07).

NE ÇİVİLİYOR. `health.faz6_kilitleri`nin ③ kilidi (`faz5_cikisi`) bugüne kadar SABİT
`False`/`olculemedi` yazıyordu; gerekçesi "ölçümü ÜRETEN kod yok"tu. Bu tur o ölçümü yazdı
(`meridian/faz5_cikis.py`). Testlerin görevi ölçümün DOĞRU olduğunu değil — o kalibrasyon
testlerinin işi — HÜKMÜN kartla birebir aynı olduğunu ve hiçbir yerde gevşemediğini kanıtlamaktır:

  * n < n_min → "ÖLÇÜLDÜ + örneklem yetersiz" (kilit KAPALI, ama gerekçesi artık ölçülmüş)
  * kill#1 (CI sıfırı içeriyor) / kill#3 (CI pozitif ama band altı) / kill#4 (eşleşmeme > %20)
  * TARİH-KÜMELEME gerçekten kümeliyor mu (düz IID bootstrap'a karşı AYRIŞTIRICI test)
  * defter boşsa None + neden (ÖLÇÜLEMEDİ ≠ 0)
  * diğer DÖRT kilit bu turdan HABERSİZ (byte-eş)

EŞİKLER KARTTAN GELİR VE BU DOSYA ONLARI DEĞİŞTİREMEZ (n_min=20 · %95 · B=10.000 · E3 bandı).
"""
from __future__ import annotations

import json
import pathlib

import numpy as np
import pytest

from meridian import analytics, config, faz5_cikis as f5, health, store
from meridian.olcum_araclari import blok_bootstrap_ci

SRC = pathlib.Path(__file__).resolve().parent.parent / "meridian"


# =================================================================================================
# fikstür yardımcıları — canlı satır ŞEKLİYLE aynı (intraday_shadow.record çıktısı)
# =================================================================================================
def _golge(pid: str, date: str, sim_fill: float, qty: int = 10, risk: float = 100.0,
           status: str = "would_submit") -> dict:
    return {"plan_id": pid, "ticker": pid.split("-")[-1], "date": date,
            "sim_fill": sim_fill, "qty": qty, "risk_dollars": risk, "status": status,
            "entry_trigger": sim_fill, "bar_open": sim_fill,
            "sim_price_rule": "max(bar_open, entry_trigger)"}


def _eod_yaz(pairs: list) -> None:
    """`trades.jsonl` = iç EOD defteri (kapanmış işlem). (plan_id, entry, side)."""
    for pid, entry, side in pairs:
        store.append_jsonl("trades.jsonl", {"plan_id": pid, "entry": entry, "side": side,
                                            "ticker": pid.split("-")[-1]})


def _defter(rows: list) -> None:
    for r in rows:
        store.append_jsonl("intraday_shadow_orders.jsonl", r)


def _kazanc_seti(n_gun: int, gun_basi: int, bps: float, baslangic: str = "2026-08-0") -> tuple:
    """Her çiftin kazancı TAM `bps` olacak şekilde gölge+EOD satırları. eod_fill=100.0 sabit,
    sim_fill = 100 − bps/100 (uzun taraf: EOD'den ucuza girmek KAZANÇtır)."""
    golge, eod = [], []
    for g in range(n_gun):
        tarih = f"{baslangic}{g + 1}" if g < 9 else f"2026-08-{g + 1}"
        for i in range(gun_basi):
            pid = f"P-{tarih}-{chr(65 + i)}{g}"
            golge.append(_golge(pid, tarih, 100.0 - bps / 100.0))
            eod.append((pid, 100.0, "long"))
    return golge, eod


# =================================================================================================
# A) TARİH-KÜMELİ BOOTSTRAP — kümeleme GERÇEKTEN kümeliyor mu?
# =================================================================================================
def _kumeli_seri(rng, g: int = 12, gun_basi: int = 10, gun_sd: float = 1.0, ic_sd: float = 0.1):
    """BİLİNEN GERÇEK: gerçek ortalama TAM 0. Gün etkisi güne özgüdür ve o günün BÜTÜN
    gözlemlerine aynı anda vurur — 4b defterindeki "aynı açılışı paylaşan planlar"ın birebir
    kurgusu. Gün içi gürültü kasten KÜÇÜK: kümelenme baskın olsun."""
    deg, tar = [], []
    for i in range(g):
        etki = rng.normal(0.0, gun_sd)
        for _ in range(gun_basi):
            deg.append(etki + rng.normal(0.0, ic_sd))
            tar.append(f"g{i}")
    return deg, tar


def _kapsama(M: int = 120, B: int = 400) -> tuple[float, float]:
    """M bağımsız kolda, aralığın GERÇEK ortalamayı (0) kapsama oranı: (kümeli, düz IID)."""
    k = d = 0
    for m in range(M):
        rng = np.random.default_rng(9000 + m)
        deg, tar = _kumeli_seri(rng)
        c = f5.tarih_kumeli_bootstrap(deg, tar, n_ornek=B)
        if c["lo"] <= 0.0 <= c["hi"]:
            k += 1
        i = blok_bootstrap_ci(deg, blok=1, n_ornek=B)      # DÜZ (IID) bootstrap
        if i["lo"] <= 0.0 <= i["hi"]:
            d += 1
    return k / M, d / M


def test_A_kumeli_bootstrap_KAPSAR_duz_bootstrap_COKER():
    """BU TESTİN VAR OLUŞ SEBEBİ. Aynı gün dolan planlar aynı açılışı paylaşır; düz bootstrap
    onları BAĞIMSIZ sayar, aralığı daraltır ve hükmü kilidi AÇMA yönünde kaydırır — hata TEK
    YÖNLÜDÜR. Kart bu yüzden yöntemi ölçümden ÖNCE dondurdu. Burada kanıt kalibrasyondur:
    gerçeği (ortalama = 0) BİLDİĞİMİZ sentetik veride kümeli aralık kapsar, düz aralık ÇÖKER."""
    kumeli, duz = _kapsama()
    assert kumeli >= 0.85, f"tarih-kümeli aralık gerçek ortalamayı kapsamıyor: {kumeli:.2f}"
    assert duz <= 0.55, (f"düz IID bootstrap bu kurguda ÇÖKMELİYDİ ({duz:.2f}) — çökmüyorsa "
                         "sentetik veri kümelenmiyor demektir ve test bir şey kanıtlamaz")
    assert kumeli - duz >= 0.30, f"iki yöntem ayrışmıyor (kümeli {kumeli:.2f} vs düz {duz:.2f})"


def test_A_AYNI_GUNDE_iki_dolum_BAGIMSIZ_sayilmiyor():
    """AYRIŞTIRICI ÇİVİ, Monte Carlo'suz. Her gözlemi KENDİ GÜNÜ İÇİNDE ikizle: örneklem iki
    katına çıkar ama YENİ BİLGİ GELMEZ. Kümeli aralık bunu bilir (genişlik ~aynı kalır); düz
    bootstrap ikizleri bağımsız sanır ve aralığı ~1/√2 daraltır. Fark tam olarak bu testin
    ölçtüğü şeydir."""
    deg = [12.0, -4.0, 7.0, -9.0, 3.0, 15.0]
    tar = [f"2026-08-0{i + 1}" for i in range(6)]
    tek = f5.tarih_kumeli_bootstrap(deg, tar)
    ikiz = f5.tarih_kumeli_bootstrap(deg + deg, tar + tar)          # aynı günde İKİNCİ dolum
    g_tek, g_ikiz = tek["hi"] - tek["lo"], ikiz["hi"] - ikiz["lo"]
    assert tek["n"] == 6 and ikiz["n"] == 12 and ikiz["n_kume"] == 6, "küme sayısı artmamalı"
    assert abs(g_ikiz - g_tek) / g_tek < 0.10, (
        f"aynı gün ikizlenince kümeli aralık daraldı ({g_tek:.3f} → {g_ikiz:.3f}) — "
        "kümeleme çalışmıyor, gözlemler bağımsız sayılıyor")

    d_tek = blok_bootstrap_ci(deg, blok=1)
    d_ikiz = blok_bootstrap_ci(deg + deg, blok=1)
    daralma = 1.0 - (d_ikiz["hi"] - d_ikiz["lo"]) / (d_tek["hi"] - d_tek["lo"])
    assert daralma > 0.20, (f"düz bootstrap ikizlemede daralmadı ({daralma:.2f}) — negatif "
                            "kontrol tutmuyorsa yukarıdaki pozitif kontrol de bir şey söylemez")


def test_A_tek_tarih_kumesinde_ARALIK_YOK_ve_NEDENLI():
    """UYDURMA YASAĞI'nın en tehlikeli hâli: tek kümede her replikasyon AYNI havuzu üretir,
    genişliği SIFIR bir aralık çıkar ve o aralık "sıfırı dışlıyor" der — yani kilidi HAK ETMEDEN
    açardı. `lo/hi` None, `sifiri_disliyor` da None (False DEĞİL)."""
    c = f5.tarih_kumeli_bootstrap([5.0, 6.0, 7.0], ["2026-08-06"] * 3)
    assert c["lo"] is None and c["hi"] is None and c["sifiri_disliyor"] is None
    assert c["n_kume"] == 1 and c["neden"] and "tek tarih kümesi" in c["neden"]
    assert c["ort"] == pytest.approx(6.0), "ortalama ÖLÇÜLDÜ — aralık yok diye o da silinmez"


def test_A_ayni_girdi_AYNI_araligi_verir_ve_hiza_bozuksa_HATA():
    a = f5.tarih_kumeli_bootstrap([1.0, 2.0, 9.0, -3.0], ["g1", "g1", "g2", "g3"])
    b = f5.tarih_kumeli_bootstrap([1.0, 2.0, 9.0, -3.0], ["g1", "g1", "g2", "g3"])
    assert (a["lo"], a["hi"]) == (b["lo"], b["hi"]), "sabit tohum: aynı defter aynı aralık"
    with pytest.raises(ValueError, match="hiza"):
        f5.tarih_kumeli_bootstrap([1.0, 2.0], ["g1"])


def test_A_sabit_deger_serisinde_ARALIK_NOKTAYA_COKER():
    """CI HESABININ ELLE DOĞRULANABİLİR HÂLİ: her gözlem 10 bps ise ortalamanın örnekleme
    dağılımı da tek noktadır — aralık [10, 10] olmak ZORUNDA."""
    c = f5.tarih_kumeli_bootstrap([10.0] * 9, [f"g{i // 3}" for i in range(9)])
    assert c["ort"] == pytest.approx(10.0) and c["lo"] == pytest.approx(10.0)
    assert c["hi"] == pytest.approx(10.0) and c["sifiri_disliyor"] is True
    assert c["B"] == f5.BOOTSTRAP_N == 10_000, "kart B=10.000 dondurdu"


# =================================================================================================
# B) HÜKÜM — kartın kill listesi
# =================================================================================================
def test_B_defter_BOSSA_olculemedi_None_ve_NEDEN(sandbox_state):
    """ÖLÇÜLEMEDİ ≠ 0. Sıfır çiftten "kazanç 0 bps" üretmek, ölçülmemiş bir sonucu ölçülmüş
    göstermek olurdu; kilit fail-closed kapalı ve `durum` hâlâ `olculemedi`."""
    h = f5.cikis_olcumu()
    assert h["gecer"] is False and h["durum"] == "olculemedi"
    assert h["olcum"]["n_eslesen"] is None and h["olcum"]["ortalama_bps"] is None
    assert h["olcum"]["ci"] is None and h["olcum"]["n_evren"] == 0
    assert "DOLUM ÜRETMİŞ satır YOK" in h["neden"]


def test_B_bloklanan_satir_EVRENE_girmez_kill4_paydasini_sismez(sandbox_state):
    """Kartın evreni "DOLUM ÜRETMİŞ her plan"dır. Kapıda bloklanmış satır dolum üretmemiştir —
    EŞLEŞMEYEN değil, EVREN DIŞIdır. İkisini karıştırmak kill#4'ün paydasını şişirir ve bütünlük
    sorunu olmadığı hâlde hükmü sildirirdi."""
    _defter([_golge("P-1-A", "2026-08-06", 99.0),
             {**_golge("P-2-B", "2026-08-06", 0.0, status="blocked:halt"), "sim_fill": None}])
    _eod_yaz([("P-1-A", 100.0, "long")])
    h = f5.cikis_olcumu()
    assert h["olcum"]["n_defter"] == 2 and h["olcum"]["n_evren"] == 1
    assert h["olcum"]["eslesmeyen"]["n"] == 0, "bloklanan satır eşleşmeyen SAYILMAZ"


def test_B_n_kucukse_OLCULDU_ama_ORNEKLEM_YETERSIZ(sandbox_state):
    """KARTIN ÖNGÖRDÜĞÜ BUGÜNKÜ SONUÇ (canlı 4b defteri n=4). Kilit kapalı KALIR ama `durum`
    `olculemedi`den `olculdu`ya geçer: gerekçe "üreten kod yok"tan "örneklem 4/20"ye döner ve
    ikincisi zamanla kendiliğinden dolar."""
    golge, eod = _kazanc_seti(n_gun=2, gun_basi=2, bps=30.0)
    _defter(golge)
    _eod_yaz(eod)
    h = f5.cikis_olcumu()
    assert h["durum"] == "olculdu", "ölçüm KOŞTU — bu bir başarısızlık değil ölçülmüş yetersizlik"
    assert h["gecer"] is False, "FAIL-CLOSED: n dolmadan kilit açılmaz"
    assert h["olcum"]["n_eslesen"] == 4 and h["olcum"]["n_min"] == 20
    assert "ÖRNEKLEM YETERSİZ (4/20)" in h["neden"]
    assert h["olcum"]["ortalama_bps"] == pytest.approx(30.0), "ölçüm yine de RAPORLANIR"
    assert h["olcum"]["ci"]["n_kume"] == 2 and h["olcum"]["ci"]["B"] == 10_000


def test_B_kill4_BOZULMA_yuzde_20_ustunde_HUKUM_YOK(sandbox_state):
    """KILL#4 — kart: "defter bütünlüğü sorunu; ölçüm hükmü VERİLMEZ, önce eşleştirme kırılması
    kök-neden turuna gider". `durum` bu yüzden `olculemedi` KALIR: kırık bir eşleştirmenin üstüne
    kurulan "örneklem yetersiz" cümlesi de yanlış olurdu.

    R1 DARALTMASI (EXE-2026-002-R1): kill#4 artık YALNIZ BOZULMA'da (golge_bozuk/bps_yok) tetikler;
    `eod_yok` MEŞRU dolmamadır ve n_min'e havale edilir — o hâl artık kill#4'ü TETİKLEMEZ ve ayrı
    çivilenir (`tests/test_kill4_daraltma_v228.py`). Bu yüzden fikstür `eod_yok`tan BOZULMA'ya
    çevrildi: testin AMACI (%20 ÜSTÜNDE hüküm YOK) DEĞİŞMEDİ, yalnız DOĞRU sınıf kullanılıyor.
    Sınıf `golge_bozuk`: `sim_fill` biçimsiz (None DEĞİL → evrene girer ama float() reddeder)."""
    golge, eod = _kazanc_seti(n_gun=2, gun_basi=2, bps=30.0)
    golge.append(_golge("P-BOZUK-X", "2026-08-02", "BOZUK-BICIM"))  # 5 satırın 1'i BOZULMA = %20
    _defter(golge)
    _eod_yaz(eod)
    h = f5.cikis_olcumu()
    assert h["olcum"]["eslesmeyen"]["n"] == 1
    assert h["olcum"]["eslesmeyen"]["oran"] == pytest.approx(0.2), "1/5 = %20 — eşiği AŞMIYOR"
    assert h["olcum"]["eslesmeyen"]["bozulma"]["oran"] == pytest.approx(0.2), \
        "kill#4 oranı BOZULMA'dan gelir: 1/(4+1) = %20 — eşiği AŞMIYOR (kart: > %20)"
    assert h["olcum"]["eslesmeyen"]["sinif_dagilimi"] == {"golge_bozuk": 1}
    assert h["durum"] == "olculdu", "%20 eşiği AŞILMADIKÇA hüküm verilir (kart: > %20)"

    golge.append(_golge("P-BOZUK-Y", "2026-08-02", "BOZUK-BICIM"))  # 6 satırın 2'si BOZULMA = %33
    _defter([golge[-1]])
    h2 = f5.cikis_olcumu()
    assert h2["durum"] == "olculemedi" and h2["gecer"] is False
    assert "KILL#4" in h2["neden"] and "kök-neden" in h2["neden"].lower()
    assert h2["olcum"]["eslesmeyen"]["bozulma"]["oran"] == pytest.approx(round(2 / 6, 4)), \
        "2/(4+2) = %33 > %20 — BOZULMA eşiği AŞIYOR"
    assert set(h2["olcum"]["eslesmeyen"]["adlar"]) == {"P-BOZUK-X·2026-08-02",
                                                       "P-BOZUK-Y·2026-08-02"}, \
        "kart: eşleşmeyen satır SESSİZCE DÜŞÜRÜLMEZ — sayısı ve ADI birlikte raporlanır"
    assert all(e["neden"] for e in h2["olcum"]["eslesmeyen"]["nedenler"])


def test_B_n_yeterli_CI_SIFIRI_iceriyorsa_kilit_KAPALI(sandbox_state):
    """KILL#1 — n >= 20 ile CI sıfırı içeriyorsa dakika-hassas icranın ölçülebilir kazancı YOK."""
    golge, eod = [], []
    # GÜN ETKİSİ değişken, gün İÇİ sabit: kümeler arası yayılım gerçek, ortalama 0 → CI sıfırı
    # İÇERİR. (Her günün ortalaması 0 olsaydı aralık [0, 0]'a çökerdi ve test hiçbir şey
    # kanıtlamazdı — dejenere bir aralık "sıfırı içeriyor"u bedavaya geçer.)
    for g, gun_bps in enumerate([30.0, -30.0, 25.0, -25.0, 20.0, -20.0]):
        tarih = f"2026-08-0{g + 1}"
        for i in range(4):
            pid = f"P-{tarih}-{i}"
            golge.append(_golge(pid, tarih, 100.0 - gun_bps / 100.0))
            eod.append((pid, 100.0, "long"))
    _defter(golge)
    _eod_yaz(eod)
    h = f5.cikis_olcumu()
    assert h["olcum"]["n_eslesen"] == 24 >= f5.N_MIN
    assert h["durum"] == "olculdu" and h["gecer"] is False
    assert h["olcum"]["ci"]["sifiri_disliyor"] is False
    assert "KILL#1" in h["neden"] and "SIFIRI İÇERİYOR" in h["neden"]


def test_B_kill3_CI_pozitif_ama_MALIYET_BANDI_altinda_KAPALI(sandbox_state):
    """KILL#3 — "anlamlı ama işe yaramaz". Kazanç 2 bps: sıfırdan ayrışıyor ama E3 kötümser
    bandını (yürürlükte 5 bps) AŞMIYOR."""
    band = analytics.pessimistic_band()["ek_bps_giris"]
    assert band > 0, f"bu test bandın pozitif olmasına dayanır (goal.yaml E3): {band}"
    golge, eod = _kazanc_seti(n_gun=7, gun_basi=3, bps=band / 2.5)
    _defter(golge)
    _eod_yaz(eod)
    h = f5.cikis_olcumu()
    assert h["olcum"]["n_eslesen"] == 21 >= f5.N_MIN
    assert h["olcum"]["ci"]["alt"] > 0, "CI pozitif olmalı (aksi hâlde kill#1'i sınıyor olurduk)"
    assert h["gecer"] is False and h["durum"] == "olculdu"
    assert "KILL#3" in h["neden"] and str(band) in h["neden"]
    assert h["olcum"]["maliyet_bandi"]["ek_bps_giris"] == band


def test_B_kill2_CI_tamamen_NEGATIFSE_4b_bir_MALIYETTIR(sandbox_state):
    golge, eod = _kazanc_seti(n_gun=7, gun_basi=3, bps=-25.0)
    _defter(golge)
    _eod_yaz(eod)
    h = f5.cikis_olcumu()
    assert h["gecer"] is False and h["durum"] == "olculdu"
    assert "KILL#2" in h["neden"] and h["olcum"]["ci"]["ust"] < 0


def test_B_esik_ASILINCA_kilit_ACILIR(sandbox_state):
    """POZİTİF KONTROL — hükmün tek yönlü olmadığının kanıtı: bant AŞILDIĞINDA kilit gerçekten
    açılır. Bu test olmadan yukarıdaki dört kill'in hepsi "her zaman False döndür" ile geçerdi."""
    band = analytics.pessimistic_band()["ek_bps_giris"]
    golge, eod = _kazanc_seti(n_gun=7, gun_basi=3, bps=band * 12.0)
    _defter(golge)
    _eod_yaz(eod)
    h = f5.cikis_olcumu()
    assert h["gecer"] is True and h["durum"] == "olculdu" and h["neden"] is None
    assert h["olcum"]["ci"]["alt"] > band


def test_B_esik_TEK_KAYNAK_band_oynayinca_hukum_de_oynar(sandbox_state, monkeypatch):
    """DAVRANIŞSAL TEK-KAYNAK ÇİVİSİ (metin taraması değil, v130 §6e deseni): maliyet bandı
    `analytics.pessimistic_band`den okunur. Modül kendi kopyasını taşısaydı burada ayrışırdı."""
    golge, eod = _kazanc_seti(n_gun=7, gun_basi=3, bps=8.0)
    _defter(golge)
    _eod_yaz(eod)
    monkeypatch.setattr(analytics, "pessimistic_band",
                        lambda goal=None: {"ek_bps_giris": 4.0, "taban": "test"})
    assert f5.cikis_olcumu()["gecer"] is True, "8 bps > 4 bps bandı — açılmalıydı"
    monkeypatch.setattr(analytics, "pessimistic_band",
                        lambda goal=None: {"ek_bps_giris": 40.0, "taban": "test"})
    kapali = f5.cikis_olcumu()
    assert kapali["gecer"] is False and "KILL#3" in kapali["neden"]


def test_B_KISA_taraf_isareti_TERS_ve_yonsuz_satir_UYDURULMAZ(sandbox_state):
    """Kartın formülü kısa tarafta işareti ters çevirir. Yön gölge satırında YOKTUR ve iç EOD
    defterinden okunur; okunamıyorsa "long" VARSAYILMAZ — satır adıyla eşleşmez sayılır."""
    _defter([_golge("P-U", "2026-08-06", 99.0), _golge("P-K", "2026-08-06", 99.0),
             _golge("P-Y", "2026-08-06", 99.0)])
    _eod_yaz([("P-U", 100.0, "long"), ("P-K", 100.0, "short"), ("P-Y", 100.0, None)])
    h = f5.cikis_olcumu()
    ciftler = {c["plan_id"]: c["kazanc_bps"] for c in h["olcum"]["ciftler"]}
    assert ciftler["P-U"] == pytest.approx(100.0) and ciftler["P-K"] == pytest.approx(-100.0)
    assert "P-Y·2026-08-06" in h["olcum"]["eslesmeyen"]["adlar"]
    assert any("yön ölçülemedi" in e["neden"] for e in h["olcum"]["eslesmeyen"]["nedenler"])


def test_B_R_bacagi_olculemezse_BPS_bacagi_ATILMAZ(sandbox_state):
    """İKİ BACAK, İKİ CEVAP. `risk_dollars` yoksa R ölçülemez ama bps ölçülmüştür; ikisini tek
    "ölçülemedi"ye katlamak ölçülmüş olanı da atmak olurdu."""
    _defter([_golge("P-A", "2026-08-06", 99.0, risk=0.0),
             _golge("P-B", "2026-08-07", 99.0, qty=10, risk=50.0)])
    _eod_yaz([("P-A", 100.0, "long"), ("P-B", 100.0, "long")])
    h = f5.cikis_olcumu()
    assert h["olcum"]["n_eslesen"] == 2 and h["olcum"]["n_R_olculemeyen"] == 1
    assert h["olcum"]["R_olculemeyen_adlar"] == ["P-A·2026-08-06"]
    assert h["olcum"]["ortalama_R"] == pytest.approx(0.2), "(100−99)×10/50 = 0,2R"


def test_B_gerceklik_capasi_AYRI_ve_HUKME_GIRMEZ(sandbox_state):
    """Kartın metodolojik sınırı: gerçek Alpaca dolumuyla kıyas AYRI satırdır ve hükmü VERMEZ —
    bir modeli gerçekle kıyaslamak modeli KAYIRIR. Ölçülemediğinde 0 değil None + neden."""
    golge, eod = _kazanc_seti(n_gun=2, gun_basi=2, bps=30.0)
    _defter(golge)
    _eod_yaz(eod)
    bos = f5.cikis_olcumu()["olcum"]["gerceklik_capasi"]
    assert bos["n"] == 0 and bos["ort_bps"] is None and bos["hukme_girmez"] is True
    assert bos["neden"] and "0 bps yazmak" in bos["neden"]

    for r in golge:
        store.append_jsonl("entry_execution.jsonl",
                           {"plan_id": r["plan_id"], "motor": "ayna", "fill": 99.5})
    dolu = f5.cikis_olcumu()
    capa = dolu["olcum"]["gerceklik_capasi"]
    assert capa["n"] == 4 and capa["hukme_girmez"] is True and capa["ort_bps"] is not None
    assert dolu["gecer"] is False and "ÖRNEKLEM YETERSİZ" in dolu["neden"], \
        "çapa hükmü DEĞİŞTİREMEZ — hüküm hâlâ n_min'den geliyor"


def test_B_olcum_HICBIR_DOSYAYA_yazmaz(sandbox_state):
    """SAF OKUMA. Bir ön-koşul ölçümünün yan etkisi olması, denetlediği kapıyı kendisinin açması
    riskini doğurur (v130 §6f ile aynı yasa)."""
    golge, eod = _kazanc_seti(n_gun=2, gun_basi=2, bps=30.0)
    _defter(golge)
    _eod_yaz(eod)
    once = {str(p): p.stat().st_mtime_ns for p in pathlib.Path(sandbox_state).rglob("*")
            if p.is_file()}
    f5.cikis_olcumu()
    sonra = {str(p): p.stat().st_mtime_ns for p in pathlib.Path(sandbox_state).rglob("*")
             if p.is_file()}
    assert sonra == once, f"ölçüm diske yazdı: {set(sonra) ^ set(once) or 'mtime değişti'}"


# =================================================================================================
# C) KİLİT — health.faz6_kilitleri'ye bağlanma
# =================================================================================================
def _hukum(passed: int, n: int) -> dict:
    return {"criteria": {f"o{i}": {"status": "gecti"} for i in range(n)},
            "passed": passed, "failed": n - passed, "unmeasured": 0, "verdict": f"{passed}/{n}"}


def _trio() -> dict:
    return {"dsr_canli": {"dsr": 0.99, "n": 40}, "n_trials": 461, "pencere_id": "R1"}


def test_C_kilit_artik_SABIT_False_degil_GERCEK_hesaba_bagli(sandbox_state):
    """③ KİLİDİN VAR OLUŞ SEBEBİ. Önce: `_kilit(False, "olculemedi", …, "…ÜRETEN kod yok")`.
    Sonra: hüküm ölçümden gelir. Kaynakta sabitin kalmadığını da çiviliyoruz — bir gün biri
    hesabı kaldırıp `False` yazarsa test kırılsın."""
    golge, eod = _kazanc_seti(n_gun=2, gun_basi=2, bps=30.0)
    _defter(golge)
    _eod_yaz(eod)
    f = health.faz6_kilitleri(edge=_hukum(5, 5), sonuc=_hukum(4, 4), trio=_trio())
    k = f["kilitler"]["faz5_cikisi"]
    assert k["durum"] == "olculdu" and k["gecer"] is False
    assert "ÖRNEKLEM YETERSİZ (4/20)" in k["neden"]
    assert k["olcum"]["cikis_olcumu"]["n_eslesen"] == 4
    assert k["olcum"]["intraday_shadow_orders_n"] == 4
    assert "EXE-2026-002" in k["esik"] and "tarih-kümeli" in k["esik"]

    src = (SRC / "health.py").read_text()
    assert "ÜRETEN kod yok" not in src, "kilidin eski eksiklik beyanı kaynakta kalmış"
    assert "faz5_cikis" in src, "kilit ölçüm modülüne bağlı değil"


def test_C_kilit_ACILABILIR_ve_zincir_sayaci_takip_eder(sandbox_state):
    """Kilit gerçekten AÇILABİLİR olmalı; aksi hâlde "bağlandı" iddiası boştur."""
    band = analytics.pessimistic_band()["ek_bps_giris"]
    golge, eod = _kazanc_seti(n_gun=7, gun_basi=3, bps=band * 12.0)
    _defter(golge)
    _eod_yaz(eod)
    f = health.faz6_kilitleri(edge=_hukum(5, 5), sonuc=_hukum(4, 4), trio=_trio())
    assert f["kilitler"]["faz5_cikisi"]["gecer"] is True
    assert f["n_acik"] == 4 and f["hepsi_acik"] is False, "operatör bayrağı hâlâ kapalı"


def test_C_DIGER_DORT_kilit_bu_turdan_HABERSIZ(sandbox_state):
    """YAN ETKİ ÇİVİSİ. Aynı zincir iki farklı 4b defteriyle koşulur (biri boş, biri kilidi
    AÇAN 21 çift); ③ dışındaki dört kilit BYTE-EŞ olmak zorunda. Brief: "diğer dört kilide
    DOKUNMA" — bu, o cümlenin ölçülmüş hâlidir."""
    bos = health.faz6_kilitleri(edge=_hukum(5, 5), sonuc=_hukum(4, 4), trio=_trio())
    band = analytics.pessimistic_band()["ek_bps_giris"]
    golge, eod = _kazanc_seti(n_gun=7, gun_basi=3, bps=band * 12.0)
    _defter(golge)
    _eod_yaz(eod)
    dolu = health.faz6_kilitleri(edge=_hukum(5, 5), sonuc=_hukum(4, 4), trio=_trio())

    for ad in ("edge_kaniti", "sonuc_hukmu", "operator_onayi", "dsr_gecer"):
        assert json.dumps(bos["kilitler"][ad], sort_keys=True, default=str) == \
               json.dumps(dolu["kilitler"][ad], sort_keys=True, default=str), \
            f"{ad} kilidi Faz-5 turundan etkilendi"
    assert bos["kilitler"]["faz5_cikisi"]["durum"] == "olculemedi"
    assert dolu["kilitler"]["faz5_cikisi"]["gecer"] is True
    assert list(health.FAZ6_KILITLERI) == ["edge_kaniti", "sonuc_hukmu", "faz5_cikisi",
                                           "operator_onayi", "dsr_gecer"]
    assert bos["n_kilit"] == dolu["n_kilit"] == 5


def test_C_olcum_COKERSE_kilit_FAIL_CLOSED_ve_ISTISNA_gorunur(sandbox_state, monkeypatch):
    """`/api/diagnostics` bu zinciri TEK `return {...}` içinde KORUMASIZ çağırıyor
    (SISTEM-DENETIMI-2026-08-02 §891): buradan sızan bir istisna Operasyon sayfasının TAMAMINI
    karartırdı — yani bir şey bozukken operatörün bakacağı satırlar da onunla giderdi. Yakalayıcı
    SESSİZ DEĞİL: istisna sınıfı `neden`e taşınır ve kilit KAPALI kalır."""
    def _patlat(rows=None):
        raise RuntimeError("defter okunamadı")

    monkeypatch.setattr(f5, "cikis_olcumu", _patlat)
    f = health.faz6_kilitleri(edge=_hukum(5, 5), sonuc=_hukum(4, 4), trio=_trio())
    k = f["kilitler"]["faz5_cikisi"]
    assert k["gecer"] is False and k["durum"] == "olculemedi"
    assert "RuntimeError" in k["neden"] and "defter okunamadı" in k["neden"]
    assert k["olcum"]["cikis_olcumu"] is None, "ölçüm düştü — sayı UYDURULMAZ"
    assert f["n_acik"] == 3, "diğer kilitler istisnadan etkilenmemeli"


def test_C_liste_KIRPMASI_beyanli_sayaclar_TAM(sandbox_state):
    """Defter süresiz büyür ve bu sözlük /api/diagnostics yükünün içine girer. Kırpma meşrudur
    ama BEYANLI olmak zorundadır: `n` her zaman TAM, kırpılan ad sayısı ayrı alanda."""
    golge, eod = _kazanc_seti(n_gun=8, gun_basi=9, bps=30.0)   # 72 çift > AD_TAVANI
    _defter(golge)
    _eod_yaz(eod)
    o = f5.cikis_olcumu()["olcum"]
    assert o["n_eslesen"] == 72, "sayaç TAM"
    assert len(o["ciftler"]) == f5.AD_TAVANI and o["ciftler_kirpildi"] == 72 - f5.AD_TAVANI
    assert o["ci"]["n"] == 72, "aralık KIRPILMAMIŞ seriden kuruldu"

    kayip = [_golge(f"P-KAYIP-{i}", "2026-08-01", 99.0) for i in range(60)]
    _defter(kayip)
    e = f5.cikis_olcumu()["olcum"]["eslesmeyen"]
    assert e["n"] == 60 and len(e["adlar"]) == f5.AD_TAVANI
    assert e["adlar_kirpildi"] == 10 and e["sinif_dagilimi"] == {"eod_yok": 60}


def test_C_YASA6_pano_olcum_sozlugunu_GERCEKTEN_ciziyor(sandbox_state):
    """YASA 6 — OKUYUCUSUZ YAZIM YOK, ÖLÇÜLEREK.

    ESKİ BEYAN (v212, 2026-08-07): "pano kilit çipinde YALNIZ `esik`+`neden` çiziyor; `olcum`
    sözlüğünün hiçbir pano okuyucusu YOK". Çivi bilerek TERS kurulmuştu (`"k.olcum" not in
    appjs`) — "pano okumaya başladığı gün kırılsın, beyan bayatlamasın" diye.

    v219 (DALGA W4-N5) onu kırdı ve çivi YÖN DEĞİŞTİRDİ: `faz6Satiri` artık beş kilidin her
    birinin `olcum` sözlüğünü dört hücrelik bir özet şeridine çiziyor (`kilitOlcumHucreleri`).
    Yeni hüküm: ölçüm GERÇEKTEN çiziliyor mu — ve `neden`/`esik` metni ikinci okuyucu geldi
    diye SAYIYI BIRAKMIYOR mu? İkincisi hâlâ gerekli: çipin `title=` ipucu ile katmanı açmayan
    operatörün gördüğü tek metin odur.

    (Davranış tarafı — hücrelerin ÖLÇÜLEMEDİ≠0 ve payda-beyanı kuralları — Node'da
    `tests/test_gorunurluk_v219.py`de koşturulur; burada YALNIZ okuyucunun VARLIĞI çivilenir.)"""
    appjs = (SRC / "web" / "app.js").read_text()
    assert "k.esik" in appjs and "k.neden" in appjs, "pano kilit çipi esik/neden okumuyor"
    # (1) OKUYUCU VAR ve kilit sözlüğünden besleniyor.
    assert "function kilitOlcumHucreleri(" in appjs, "kilit ölçümünün pano okuyucusu YOK"
    govde = appjs[appjs.index("function kilitOlcumHucreleri("):appjs.index("function faz6Satiri(")]
    assert "(k || {}).olcum" in govde, "okuyucu kilidin `olcum` sözlüğünü almıyor"
    # (2) BU MODÜLÜN ürettiği alanlar gerçekten okunuyor (hayalet alan değil).
    for alan in ("cikis_olcumu", "n_eslesen", "n_min", "ortalama_bps", "eslesmeyen", "kill_esigi"):
        assert alan in govde, f"pano `{alan}` alanını okumuyor — ölçüm yarım çiziliyor"
    # (3) ÖLÇÜLEMEDİ ≠ 0: değeri olmayan hücre gerekçe yazar, sıfır yazmaz.
    assert "deger: null" in govde and "0 DEĞİL" in govde, "ölçülemeyen dal sıfıra çöküyor"
    # (4) ÜRETİCİ ÇAĞRILIYOR — çizilmeyen bir üretici, okumamakla aynı şeydir.
    assert "kilitOlcumHucreleri(ad, k)" in appjs, "üretici kilit zincirinde çağrılmıyor"

    golge, eod = _kazanc_seti(n_gun=2, gun_basi=2, bps=30.0)
    _defter(golge)
    _eod_yaz(eod)
    k = health.faz6_kilitleri(edge=_hukum(5, 5), sonuc=_hukum(4, 4),
                              trio=_trio())["kilitler"]["faz5_cikisi"]
    assert "4/20" in k["neden"], "panoda görünen tek metin karar sayısını taşımıyor"
    assert str(f5.N_MIN) in k["esik"] and str(f5.BOOTSTRAP_N) in k["esik"]


def test_C_kart_esikleri_KODDA_da_donmus():
    """Eşikler ölçümden ÖNCE donduruldu ve DEĞİŞTİRİLEMEZ. Kart YAML'ı ile modül sabitleri
    ayrışırsa ölçüm artık ön-kayıtlı değildir — sessiz kayma tam olarak K disiplininin
    engellemek için var olduğu şey."""
    kart = (pathlib.Path(__file__).resolve().parent.parent / "research" / "cards" /
            "EXE-2026-002-faz5-cikis-olcumu.yaml").read_text()
    assert "n_min = 20" in kart and "10.000 yeniden örnekleme" in kart
    assert (f5.N_MIN, f5.BOOTSTRAP_N, f5.CI_SEVIYE, f5.KILL_ESLESMEME_ORANI) == \
           (20, 10_000, 0.95, 0.20)
    assert f5.KART == "EXE-2026-002" and "card_id: EXE-2026-002" in kart
    assert "pessimistic_band_v2" in kart, "kartın maliyet modeli E3 bandıdır"
    assert "pessimistic_band" in (SRC / "faz5_cikis.py").read_text(), \
        "modül maliyet bandını E3'ün TEK kaynağından okumuyor"
    assert "> %20" in kart, "kill#4 eşiği kartta yazılı"


def test_C_canli_yerel_defterle_kilidin_TAM_cikitisi(sandbox_state):
    """CANLI YÜK ALTINDA DAVRANIŞ (yerel state anlık görüntüsü boş 4b defteri taşır): kilit
    `olculemedi` + neden döner ve zincir ÇÖKMEZ. Kilit zincirinin canlı bir istekte istisna
    fırlatması, /api/diagnostics'in TAMAMINI karartırdı (SISTEM-DENETIMI-2026-08-02 §891)."""
    f = health.faz6_kilitleri(edge=_hukum(5, 5), sonuc=_hukum(4, 4), trio=_trio())
    k = f["kilitler"]["faz5_cikisi"]
    assert k["gecer"] is False and k["durum"] == "olculemedi" and k["neden"]
    assert k["olcum"]["cikis_olcumu"]["n_evren"] == 0
    assert f["n_acik"] == 3 and "faz5_cikisi" in f["hukum"]
