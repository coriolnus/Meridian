"""test_sektor_tavani_ayristirma_v245.py — WP-15g: slot↔sektör-tavanı YAPIŞIKLIĞININ ayrıştırılması.

NEDEN BU DOSYA VAR
  `guard.classify_gate`in `sector_cap` kontrolü sektör oranının PAYDASI olarak
  `max_open_positions`ı kullanıyordu:

      (sektörde_n + 1) / max(1, max_open_positions) > max_sector_exposure_pct / 100

  Yani KAPASİTE knob'u sessizce ÇEŞİTLENDİRME politikasını da belirliyordu: `max_open=20, %40` →
  sektör başına 8 isim; `max_open=15, %40` → 6 isim. EDG-2026-035 bunu CANLI ÖLÇTÜ
  (`yapisal_bulgu`): slot15 hücresinin farkı slottan DEĞİL bu yan kanaldan geldi (`sector_cap`
  NO_GO 8→33) — ve aynı kart slot tavanının KAPASİTE olarak ÖLÜ olduğunu kanıtladı (eşzamanlı
  pozisyon tepesi 13 < 20; slot25 defteri tabanla BAYT-ÖZDEŞ, ΔCI=[0,0]). Yani o gün
  `max_open_positions`ın TEK CANLI ETKİSİ bu paydaydı.

BU TURUN KAPSAMI — YALNIZ AYRIŞTIRMA, SAYI DEĞİŞMEZ
  Sektör tavanı artık KENDİ paydasını taşıyor (`limits.sector_cap_basis`, `guard.LIMIT_KEYS`
  operatör kalemi). Varsayılan goal.yaml'a ELLE YAZILMADI — anahtar yoksa payda bugünkü formülden
  TÜRETİLİR. Bu yüzden bu dosyanın ASIL ÇİVİSİ bir EŞDEĞERLİK ÇİVİSİDİR (Ç1): eski formül ile yeni
  yolun hükmü geniş bir girdi matrisinde BİREBİR aynı olmalı; TEK bir hücrede ayrışırsa değişiklik
  GEÇERSİZDİR. Eşiği "iyileştirmek" (ör. sektör başına 8 yerine 10 isim) bu turun İŞİ DEĞİLDİR —
  o bir ölçüm işidir, kart-önce.

ÇİVİLER
  Ç1  eşdeğerlik matrisi: eski formül ↔ yeni yol, TÜM hücrelerde aynı hüküm  (31 × 4 × 5 = 620)
  Ç2  AYRIŞTIRMA: payda AÇIKÇA verildiğinde `max_open_positions` sektör tavanını ARTIK OYNATMAZ
      (+ POZİTİF KONTROL: payda verilmezken OYNATIYOR — yani çivi gerçekten bir şey ölçüyor)
  Ç3  AKTARIM + CANLILIK: `basis=X` (max_open ne olursa olsun) ≡ eski `max_open=X` — yani yeni
      parametre ölü bir düğme değil, eski davranışın taşıyıcısı  (620 × 4 = 2.480 hücre)
  Ç4  payda yok/bozuk → TÜRETİLMİŞ davranış (fail-safe) + İŞARETLİ düşüş (sessiz varsayılan YOK)
  Ç5  `sector_cap` gerekçe metni ve `_chk` sözleşmesi (ad, sertlik, value/threshold) DEĞİŞMEDİ
  Ç6  diğer limit kapıları — `max_open_positions` SERT kapısı dahil — etkilenmedi
  Ç7  yetki: `sector_cap_basis` operatör kalemidir (LIMIT_KEYS; Hermes öneremez) ve canlı zarfta
      BUGÜN satırı YOKTUR (canlı davranış = türetilmiş)

Fikstürler tamamen SENTETİK (test_mutborc_guard_classify_gate_v148 emsali): `config.goal()` karar
yollarında OKUNMAZ, disk yok, ağ yok, state yazımı yok. `classify_gate` saf bir fonksiyondur ve
burada saf olarak sınanır. Tek istisna Ç7'nin canlı-zarf beyanıdır ve o da YALNIZ OKUR.
"""
from __future__ import annotations

import math
from pathlib import Path

import pytest

from meridian import config, guard


# ================================================================================================
# Fikstürler — sektör tavanı DIŞINDA her kapı bilerek BOL: tek ateşleyebilen sert kural sector_cap.
# ================================================================================================
def _limits(**over):
    return {"autonomy_level": 1, "max_position_r": 1.0, "max_open_positions": 20,
            "max_daily_loss_pct": 3.0, "max_sector_exposure_pct": 40.0,
            "no_trade_before_bars": 3, "kill_switch_file": "state/HALT",
            "heat_hard_r": 5.0, "heat_review_r": 3.5, "corr_review": 0.85, **over}


PLAN = {"ticker": "AAA", "sector": "tech", "size_r": 0.5, "r_multiple_expected": 3.0, "score": 90}
REG = {"exposure_budget_pct": 60, "leading_sectors": ["tech"]}


def _port(sayac: int, acik: int = 0):
    return {"open_positions": acik, "sector_counts": {"tech": sayac}, "day_pnl_pct": 0.0,
            "open_risk_r": 0.0, "max_corr": 0.0}


def _kapi(sayac: int, *, plan=None, acik: int = 0, **limit_over):
    """(hüküm, gerekçeler, sector_cap satırı) — karar ağacı HER ZAMAN istenir."""
    detail: list = []
    hukum, gerekceler = guard.classify_gate(plan or PLAN, _port(sayac, acik), REG,
                                            {"limits": _limits(**limit_over)},
                                            None, detail_out=detail)
    satir = [d for d in detail if d["check"] == "sector_cap"]
    assert len(satir) == 1, f"sector_cap karar ağacında tam bir kez olmalı, {len(satir)} bulundu"
    return hukum, gerekceler, satir[0]


def _eski_kural(sayac: int, max_open, pct) -> bool:
    """AYRIŞTIRMA ÖNCESİ `guard.py:359-360` satırının BİREBİR KOPYASI (çapa-mezar-taşı: TARİHÎ).
    Satır numarası ayrıştırma GÜNÜNÜN dosyasına işaret eder, bugünkü guard.py'ye değil — K5
    kayması (2026-08-23) yasayı tetikledi, çapa bilinçli donuk. REFERANS UYGULAMA.

    Bu fonksiyon bilerek guard'ı ÇAĞIRMAZ ve guard'dan hiçbir şey import etmez: eşdeğerlik ancak
    bağımsız bir referansa karşı ölçülürse eşdeğerliktir (guard'ın kendi paydasını kullanan bir
    "referans" her değişikliği onaylardı)."""
    return (sayac + 1) / max(1, max_open) > pct / 100.0


# Matris eksenleri — brief'te ADIYLA verilen küme.
SAYACLAR = tuple(range(0, 31))              # sektör sayacı 0..30 (en gevşek tavan 25×%50 = 12,5)
MAX_OPENLAR = (5, 15, 20, 25)
PCTLER = (10, 25, 30, 40, 50)


# ================================================================================================
# Ç1 — EŞDEĞERLİK MATRİSİ: eski formül ↔ yeni yol, TÜM hücrelerde aynı hüküm
# ================================================================================================
def test_c1_esdegerlik_matrisi_eski_formul_ile_yeni_yol_tum_hucrelerde_ayni_hukmu_verir():
    """BİRİNCİL ŞART: bugünkü davranış ZERRE değişmeyecek.

    Payda anahtarı goal.yaml'da YOKTUR (ve olmaması doğrudur) → `sector_cap_basis` türetilmiş
    paydayı döndürür → kapı eski ifadeyle BİREBİR aynı hükmü vermelidir. Tek hücre ayrışırsa
    değişiklik GEÇERSİZ: ayrışan hücrelerin TAMAMI adıyla raporlanır (ilk hatada durmaz)."""
    ayrisan, hucre = [], 0
    for max_open in MAX_OPENLAR:
        for pct in PCTLER:
            for sayac in SAYACLAR:
                hucre += 1
                bekle_dussun = _eski_kural(sayac, max_open, pct)
                hukum, gerekceler, s = _kapi(sayac, max_open_positions=max_open,
                                             max_sector_exposure_pct=float(pct))
                metin = f"'tech' sektör tavanı %{pct:.0f} aşılıyor"
                gercek = (s["passed"] is not True, hukum == "NO_GO", metin in gerekceler,
                          s["note"] == metin)
                beklenen = (bekle_dussun, bekle_dussun, bekle_dussun, bekle_dussun)
                if gercek != beklenen:
                    ayrisan.append(f"(sayac={sayac}, max_open={max_open}, pct={pct}): "
                                   f"eski={'DÜŞER' if bekle_dussun else 'geçer'} yeni={gercek}")
                # `value`/`threshold` de matrisin parçası: hüküm aynı kalıp sayı kaysaydı karar
                # ağacı (pano + defter) yalan söylerdi.
                if s["value"] != sayac + 1 or s["threshold"] != f"%{pct:.0f}":
                    ayrisan.append(f"(sayac={sayac}, max_open={max_open}, pct={pct}): "
                                   f"alanlar kaydı value={s['value']!r} threshold={s['threshold']!r}")
    assert hucre == len(SAYACLAR) * len(MAX_OPENLAR) * len(PCTLER) == 620, f"matris boyutu {hucre}"
    assert ayrisan == [], f"{len(ayrisan)}/620 hücrede ayrışma:\n" + "\n".join(ayrisan[:25])


def test_c1_matris_gercekten_iki_hukmu_de_iceriyor_pozitif_kontrol():
    """DEJENERE MATRİS KORUMASI: 620 hücrenin hepsi 'geçer' olsaydı Ç1 hiçbir şey ölçmezdi."""
    dusen = sum(_eski_kural(s, m, p) for m in MAX_OPENLAR for p in PCTLER for s in SAYACLAR)
    assert 0 < dusen < 620, f"matris tek hükümde toplanmış (düşen={dusen})"


# ================================================================================================
# Ç2 — AYRIŞTIRMA: payda AÇIKÇA verildiğinde max_open_positions sektör tavanını OYNATMAZ
# ================================================================================================
def test_c2_POZITIF_KONTROL_payda_verilmezken_max_open_sektor_tavanini_OYNATIR():
    """Ayrıştırmanın ölçüldüğü yer burasıdır: önce yapışıklığın HÂLÂ görülebilir olduğunu göster.

    %40 tavanda payda 20 → sektör başına 8 isim (n=6 geçer); payda 15 → 6 isim (n=6 DÜŞER).
    Bu test yeşilse Ç2'nin asıl çivisi anlamlıdır; kırmızıysa çivi trivial olarak geçiyordur."""
    assert _kapi(6, max_open_positions=20)[0] != "NO_GO"
    assert _kapi(6, max_open_positions=15)[0] == "NO_GO"


def test_c2_payda_acikken_max_open_20den_15e_dusunce_sektor_tavani_SABIT_kalir():
    """AYRIŞTIRMANIN TA KENDİSİ — brief'in ikinci çivisi.

    `sector_cap_basis=20` açıkça verildiğinde `max_open_positions` 20→15 sektör tavanını ARTIK
    kaydırmaz: sayaç ekseninin TAMAMINDA hüküm ve karar-ağacı satırı BİREBİR aynı kalır."""
    for sayac in SAYACLAR:
        a = _kapi(sayac, max_open_positions=20, sector_cap_basis=20)
        b = _kapi(sayac, max_open_positions=15, sector_cap_basis=20)
        assert a[0] == b[0], f"sayac={sayac}: hüküm max_open ile kaydı ({a[0]} → {b[0]})"
        assert a[2] == b[2], f"sayac={sayac}: sector_cap satırı max_open ile kaydı"


def test_c2_paydanin_kendisi_CANLI_bir_dugmedir_olu_degil():
    """Ç2 tek başına ÖLÜ bir parametreyle de geçerdi (hiçbir şey yapmayan knob hiçbir şeyi
    oynatmaz). Payda DEĞİŞİNCE tavan oynamalı — aksi hâlde ayrıştırma değil, gömme olurdu."""
    assert _kapi(6, max_open_positions=20, sector_cap_basis=20)[0] != "NO_GO"
    assert _kapi(6, max_open_positions=20, sector_cap_basis=15)[0] == "NO_GO"


# ================================================================================================
# Ç3 — AKTARIM: `basis=X` ≡ eski `max_open=X` (max_open ne olursa olsun)
# ================================================================================================
def test_c3_acik_payda_eski_max_open_paydasinin_BIREBIR_ayni_semantigini_tasir():
    """Ayrıştırma bir SEMANTİK TAŞIMADIR: `basis=X` yeni bir politika icat etmez, eski paydanın
    tam olarak aynısını yapar. Matrisin her hücresi 4 farklı `max_open` altında yeniden koşulur —
    sector_cap satırı hepsinde türetilmiş `max_open=X` hücresiyle AYNI olmalı."""
    ayrisan, hucre = [], 0
    for basis in MAX_OPENLAR:
        for pct in PCTLER:
            for sayac in SAYACLAR:
                _, _, ref = _kapi(sayac, max_open_positions=basis,
                                  max_sector_exposure_pct=float(pct))          # türetilmiş yol
                for max_open in MAX_OPENLAR:
                    hucre += 1
                    _, _, s = _kapi(sayac, max_open_positions=max_open, sector_cap_basis=basis,
                                    max_sector_exposure_pct=float(pct))
                    if s != ref:
                        ayrisan.append(f"(sayac={sayac}, basis={basis}, max_open={max_open}, "
                                       f"pct={pct}): {s} != {ref}")
    assert hucre == 620 * len(MAX_OPENLAR) == 2480, f"aktarım matrisi boyutu {hucre}"
    assert ayrisan == [], f"{len(ayrisan)}/2480 hücrede aktarım bozuk:\n" + "\n".join(ayrisan[:25])


# ================================================================================================
# Ç4 — FAIL-SAFE: payda yok/bozuk → TÜRETİLMİŞ davranış + İŞARETLİ düşüş
# ================================================================================================
BOZUK_PAYDALAR = [
    ("anahtar_yok", ...),                 # `...` = anahtarı HİÇ koyma (aşağıda özel işlenir)
    ("none", None),
    ("bool_true", True),                  # YAML `true` → float() 1.0 verirdi: HER planı keserdi
    ("bool_false", False),
    ("dizge", "yirmi"),
    ("bos_dizge", ""),
    ("liste", [20]),
    ("sozluk", {"x": 20}),
    ("sifir", 0),
    ("sifir_float", 0.0),
    ("negatif", -5),
    ("nan", float("nan")),
]


@pytest.mark.parametrize("ad,deger", BOZUK_PAYDALAR, ids=[a for a, _ in BOZUK_PAYDALAR])
def test_c4_bozuk_payda_turetilmis_davranisa_duser_ve_dusus_ISARETLIDIR(ad, deger):
    """CANLI RİSK KAPISI KURALI: payda okunamıyorsa tahmin YOK — bugünkü davranışa düşülür.

    Yanlış bir payda ya `sector_cap`i HİÇ ateşlemez (çeşitlendirme sessizce kaybolur) ya da HER
    planı bloklar (payda 1 → (0+1)/1 > %40). İkisi de sessiz canlı kaymasıdır. Ayrıca düşüş
    SESSİZ DEĞİLDİR: `sector_cap_basis()` nedeni okunabilir bir dizge olarak GERİ VERİR."""
    limits = _limits() if deger is ... else _limits(sector_cap_basis=deger)
    payda, neden = guard.sector_cap_basis(limits)

    assert payda == limits["max_open_positions"], f"{ad}: türetilmiş paydaya düşmedi ({payda!r})"
    assert isinstance(neden, str) and len(neden) >= 20, f"{ad}: düşüş İŞARETSİZ ({neden!r})"

    # ...ve düşüş kapının HÜKMÜNDE de bugünkü davranıştır (sayaç ekseninin tamamında).
    for sayac in SAYACLAR:
        bozuk = (_kapi(sayac) if deger is ... else _kapi(sayac, sector_cap_basis=deger))
        temiz = _kapi(sayac)
        assert bozuk[0] == temiz[0] and bozuk[2] == temiz[2], \
            f"{ad}: sayac={sayac} bozuk payda davranışı KAYDIRDI"


def test_c4_gecerli_payda_dusus_nedeni_TASIMAZ():
    """Karşı-kutup: geçerli bir payda düşüş nedeni üretirse "işaretli düşüş" sinyali anlamsızlaşır."""
    for gecerli in (1, 5, 15, 20, 25, 20.0, 12.5, "20"):
        payda, neden = guard.sector_cap_basis(_limits(sector_cap_basis=gecerli))
        assert neden is None, f"{gecerli!r} geçerli paydaydı ama düşüş nedeni yazıldı: {neden!r}"
        assert payda == float(gecerli) and not isinstance(payda, bool)


def test_c4_turetme_yolu_HAM_degeri_dondurur_yuvarlama_tip_farki_dogmaz():
    """Bit-özdeşlik koşulu: türetilmiş payda `limits["max_open_positions"]`ın TA KENDİSİDİR
    (float()/int() dönüşümü yok) — aksi hâlde eski/yeni bölme sessizce ayrışabilirdi."""
    limits = _limits(max_open_positions=20)
    payda, _ = guard.sector_cap_basis(limits)
    assert payda is limits["max_open_positions"]


def test_c4_max_open_anahtari_hic_yoksa_eskisi_gibi_KeyError_yukselir():
    """Türetme yolu istisna davranışını da korur: eski satır da `limits["max_open_positions"]`
    yazıyordu ve eksik anahtarda KeyError veriyordu."""
    with pytest.raises(KeyError):
        guard.sector_cap_basis({"max_sector_exposure_pct": 40.0})


def test_c4_YASA4_damgasi_kaynak_dosyada_duruyor():
    """Sessiz-yutma damgası bir YORUM DEĞİL SÖZLEŞMEDİR (YASA 4): istisna dalı gerekçesiz yutulamaz."""
    kaynak = Path(guard.__file__).read_text(encoding="utf-8")
    govde = kaynak.split("def sector_cap_basis(", 1)[1].split("\ndef ", 1)[0].splitlines()
    yakalar = [ln for ln in govde if ln.lstrip().startswith("except ")]
    assert yakalar, "payda çözümleyicisinde istisna dalı bulunamadı (test kaynakla ayrıştı)"
    for ln in yakalar:
        assert "# sessiz-yutma:" in ln, f"YASA-4 damgası YOK: {ln.strip()!r}"
        gerekce = ln.split("# sessiz-yutma:", 1)[1].strip()
        assert len(gerekce) >= 20, f"YASA-4 gerekçesi 20 karakterden kısa: {gerekce!r}"


def test_c4_paydada_MODUL_SABITI_bir_sayi_yok_varsayilan_TURETILMIS():
    """"Varsayılan elle yazılmayacak" şartının yapısal kanıtı: fonksiyonun düşüş dallarının HİÇBİRİ
    sabit bir sayı döndürmez — hepsi `max_open_positions`ı okur."""
    for max_open in MAX_OPENLAR:
        payda, neden = guard.sector_cap_basis(_limits(max_open_positions=max_open,
                                                      sector_cap_basis="bozuk"))
        assert payda == max_open and neden is not None, \
            f"düşüş dalı max_open={max_open} yerine sabit bir sayı döndürdü: {payda!r}"


# ================================================================================================
# Ç5 — `_chk` SÖZLEŞMESİ: ad, sertlik, value/threshold, gerekçe metni DEĞİŞMEDİ
# ================================================================================================
KARAR_AGACI_ADLARI = ["exposure_budget", "max_open_positions", "sector_cap", "daily_loss_breaker",
                      "position_size", "rr_floor", "heat_hard",
                      "sector_stacking", "heat_review", "correlation", "leading_sector",
                      "rr_marginal"]


@pytest.mark.parametrize("basis", [None, 20, 15])
def test_c5_karar_agacinin_ad_listesi_ve_uzunlugu_paydadan_BAGIMSIZ_olarak_sabittir(basis):
    """Ayrıştırma karar ağacına YENİ SATIR EKLEMEZ: `test_mutborc_guard_classify_gate_v148`in
    dondurduğu 12'li ad listesi (ve sırası) aynen durur — payda verilse de verilmese de."""
    detail: list = []
    over = {} if basis is None else {"sector_cap_basis": basis}
    guard.classify_gate(PLAN, _port(0), REG, {"limits": _limits(**over)}, None, detail_out=detail)
    assert [d["check"] for d in detail] == KARAR_AGACI_ADLARI
    assert len(detail) == 12
    for d in detail:
        assert set(d) == {"check", "passed", "severity", "value", "threshold", "note"}
        assert d["note"] is None, "geçen kontrol not YAZMAZ (payda düşüşü bu yüzeye SIZMAZ)"


def test_c5_sector_cap_satirinin_sertligi_ve_alan_TIPLERI_korundu():
    hukum, gerekceler, s = _kapi(8, max_open_positions=20, max_sector_exposure_pct=40.0)
    assert hukum == "NO_GO"
    assert s["check"] == "sector_cap" and s["severity"] == "hard" and s["passed"] is False
    assert s["value"] == 9 and type(s["value"]) is int          # sc.get(sec,0) + 1, HAM sayı
    assert s["threshold"] == "%40" and s["note"] == "'tech' sektör tavanı %40 aşılıyor"
    assert gerekceler == ["'tech' sektör tavanı %40 aşılıyor"]


def test_c5_tam_esitlikte_gecer_kural_hala_KESIN_BUYUKTUR():
    """(7+1)/20 = 0,400 ve tavan 0,400 → SERT kural ATEŞLEMEZ. `>` → `>=` kayması burada ölür;
    ayrıştırma sırasında karşılaştırmanın yönü/sınırı en kolay kayan şeydir."""
    hukum, gerekceler, s = _kapi(7, max_open_positions=20, max_sector_exposure_pct=40.0)
    assert s["passed"] is True and hukum == "REVIEW"
    assert gerekceler == ["'tech' sektöründe korelasyon yığılması"]
    # ...ve açık paydayla da aynı sınırda: eşitlik AKTARILDI.
    assert _kapi(7, max_open_positions=5, sector_cap_basis=20,
                 max_sector_exposure_pct=40.0)[2]["passed"] is True


def test_c5_max_1_tabani_korundu_payda_birden_kucukken_de():
    """`max(1, payda)` katmanı eskisi gibi durur: sıfıra bölme yok, hüküm tanımlı."""
    for payda in (0.5, 1):
        hukum, _, s = _kapi(0, sector_cap_basis=payda, max_sector_exposure_pct=40.0)
        assert hukum == "NO_GO" and s["passed"] is False       # (0+1)/1 = 1,0 > 0,40
    hukum, _, _ = _kapi(0, max_open_positions=0, max_sector_exposure_pct=40.0)
    assert hukum == "NO_GO"                                     # türetilmiş yolda da aynı taban


# ================================================================================================
# Ç6 — DİĞER LİMİT KAPILARI ETKİLENMEDİ (`max_open_positions` SERT kapısı dahil)
# ================================================================================================
def test_c6_max_open_positions_SERT_kapisi_paydadan_etkilenmez():
    """En kritik yan etki riski: payda ayrılırken `max_open_positions`ın KAPASİTE işi de sessizce
    kaymasın. Payda 100 olsa bile 5 slot 5 slottur."""
    hukum, gerekceler, _ = _kapi(0, acik=5, max_open_positions=5, sector_cap_basis=100)
    assert hukum == "NO_GO" and gerekceler == ["max 5 pozisyon dolu"]
    # ...ve payda kapasite kapısının EŞİĞİNİ de değiştirmez (4 < 5 hâlâ geçer).
    assert _kapi(0, acik=4, max_open_positions=5, sector_cap_basis=100)[0] != "NO_GO"


def test_c6_max_open_satiri_paydayi_DEGIL_kendi_tavanini_raporlar():
    detail: list = []
    guard.classify_gate(PLAN, _port(0, acik=3), REG,
                        {"limits": _limits(max_open_positions=5, sector_cap_basis=100)},
                        None, detail_out=detail)
    s = [d for d in detail if d["check"] == "max_open_positions"][0]
    assert s["value"] == 3 and s["threshold"] == "<5", "kapasite satırı paydayı raporluyor"


def test_c6_sector_cap_disindaki_TUM_satirlar_payda_degisiminden_etkilenmez():
    """Bütünsel çivi: payda ekseni boyunca sector_cap DIŞINDA hiçbir satır kımıldamamalı."""
    def _satirlar(over):
        detail: list = []
        guard.classify_gate(PLAN, _port(3), REG, {"limits": _limits(**over)}, None,
                            detail_out=detail)
        return {d["check"]: d for d in detail if d["check"] != "sector_cap"}

    taban = _satirlar({})
    for over in ({"sector_cap_basis": 5}, {"sector_cap_basis": 25}, {"sector_cap_basis": "bozuk"},
                 {"sector_cap_basis": None}):
        assert _satirlar(over) == taban, f"{over} sector_cap dışındaki satırları oynattı"


def test_c6_max_open_eksikken_KeyError_AYNI_NOKTADA_yukselir_yarim_karar_agaci_korunur():
    """DEĞERLENDİRME SIRASI da davranıştır — kolay kaçırılan ayrışma sınıfı.

    Payda `classify_gate`in BAŞINDA okunsaydı, `max_open_positions`ı eksik bir goal sözlüğünde
    istisna DAHA ERKEN düşerdi ve çağıranın `detail_out` listesi `exposure_budget` satırını hiç
    almadan boş kalırdı. Eski kod KeyError'ı `max_open_positions` `_chk` satırında yükseltiyordu,
    yani o ana kadarki ağaç YAZILMIŞ oluyordu. Payda bu yüzden sector_cap satırının HEMEN ÖNÜNDE
    hesaplanır; bu çivi onu orada tutar."""
    limits = _limits()
    limits.pop("max_open_positions")
    detail: list = []
    with pytest.raises(KeyError):
        guard.classify_gate(PLAN, _port(0), REG, {"limits": limits}, None, detail_out=detail)
    assert [d["check"] for d in detail] == ["exposure_budget"], \
        "payda erken okunuyor — bozuk goal sözlüğünde karar ağacı eskisinden farklı kalıyor"

    # Açık payda VARKEN de aynı: payda okunabilse bile kapasite kapısı kendi anahtarını ister.
    detail2: list = []
    with pytest.raises(KeyError):
        guard.classify_gate(PLAN, _port(0), REG, {"limits": {**limits, "sector_cap_basis": 20}},
                            None, detail_out=detail2)
    assert [d["check"] for d in detail2] == ["exposure_budget"]


def test_c6_isi_ve_korelasyon_esikleri_hala_kendi_anahtarlarindan_okunur():
    """C24 kalemleri ayrıştırmadan etkilenmedi (aynı `limits` sözlüğünü paylaşıyorlar)."""
    plan = {**PLAN, "size_r": 0.5}
    port = {**_port(0), "open_risk_r": 4.9}
    detail: list = []
    guard.classify_gate(plan, port, REG, {"limits": _limits(heat_hard_r=5.0, sector_cap_basis=20)},
                        None, detail_out=detail)
    s = [d for d in detail if d["check"] == "heat_hard"][0]
    assert s["value"] == 5.4 and s["threshold"] == "<=5.0R" and s["passed"] is False


# ================================================================================================
# Ç7 — YETKİ: operatör kalemi, arama uzayı dışı, canlı zarfta bugün SATIRI YOK
# ================================================================================================
def test_c7_payda_operator_kalemidir_hermes_oneremez():
    """C24/de-risk deseni: LIMIT_KEYS üyeliği + `validate_change`in her öneri şeklini reddetmesi."""
    assert guard.SECTOR_CAP_BASIS_KEY == "sector_cap_basis"
    assert guard.SECTOR_CAP_BASIS_KEY in guard.LIMIT_KEYS, "LIMIT_KEYS'te yok — Hermes'e açık düğme"
    bounds, goal = config.bounds(), config.goal()
    params = config.default_strategy()["params"]
    for oneri in ({"variable": "sector_cap_basis", "new": 40},
                  {"variable": "sector_cap_basis@chop", "new": 40},
                  {"variable": "limits.sector_cap_basis", "new": 40},
                  {"changes": {"sector_cap_basis": 40}}):
        assert guard.validate_change(oneri, params, bounds, goal, [], 0).ok is False, \
            f"{oneri} guard'ı geçti — çeşitlendirme vanası arama uzayına sızdı"


def test_c7_payda_arama_uzayinda_YOK_ve_canli_zarfta_bugun_satiri_YOK():
    """BU TURUN "davranış değişmedi" KANITININ CANLI AYAĞI (yalnız OKUR, yazmaz).

    Payda `bounds.yaml`da olmamalı (risk/çeşitlendirme vanası aranmaz) ve `goal.yaml`da da BUGÜN
    olmamalı — canlı davranış TÜRETİLMİŞ paydadır, yani ayrıştırma canlıda no-op'tur. Bu satır bir
    gün kırmızı yanarsa bu bir HATA DEĞİL, bir KARAR bildirimidir: payda artık elle yazılmıştır ve
    o an ölçüm kartı + karar penceresi gerekir (eşik değiştirmek bu turun kapsamı DIŞIDIR)."""
    assert "sector_cap_basis" not in config.bounds(), "payda arama uzayına düştü"
    limits = config.goal()["limits"]
    assert "sector_cap_basis" not in limits, (
        "canlı goal.yaml'a AÇIK payda yazılmış — canlı sektör tavanı artık türetilmiş değil; "
        "değişikliğin ölçüm kartı ve karar penceresi olmalı")
    # ...ve türetilmiş payda gerçekten canlı kapasite knob'udur (bugünkü yapışıklığın beyanı).
    payda, neden = guard.sector_cap_basis(limits)
    assert payda == limits["max_open_positions"] and isinstance(neden, str)


def test_c7_canli_zarfta_turetilmis_paydanin_isim_tavani_beyan_edilir():
    """Belgeleme çivisi (YASA 6 — okuyucusuz yazım yok): canlı sektör tavanı bir ORAN değil bir
    İSİM SAYISIDIR ve o sayı bugün kapasite knob'undan türer. Sayı burada ÖLÇÜLÜR, ezberlenmez."""
    limits = config.goal()["limits"]
    payda, _ = guard.sector_cap_basis(limits)
    pct = float(limits["max_sector_exposure_pct"])
    isim_tavani = math.floor(max(1, payda) * pct / 100.0)
    # Kapının kendisiyle çapraz doğrulama: tavan kadar isim GEÇER, bir fazlası DÜŞER.
    assert _kapi(isim_tavani - 1, max_open_positions=limits["max_open_positions"],
                 max_sector_exposure_pct=pct)[0] != "NO_GO"
    assert _kapi(isim_tavani, max_open_positions=limits["max_open_positions"],
                 max_sector_exposure_pct=pct)[0] == "NO_GO"
