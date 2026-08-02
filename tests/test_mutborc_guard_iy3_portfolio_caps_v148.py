"""test_mutborc_guard_iy3_portfolio_caps_v148.py — H5 TEST BORCU: `guard._y3_portfolio_caps`.

NEDEN BU DOSYA VAR
  Mutasyon koşumunda `meridian/guard.py::_y3_portfolio_caps` kümesinin 178 mutantından 172'si
  HAYATTA KALDI (yalnız 1-4 ve 97-98 öldü; onlar da `p = None` / `float(None)` gibi ANINDA patlayan
  varyantlar). Yani iki portföy tavanının davranışı pratikte HİÇ ölçülmüyordu: knob açıldığı gün
  eşik yönü, sınır eşitliği, hangi alanın okunduğu ve "ölçülemedi" beyanının SESSİZ KALMAMASI —
  hepsi test edilmemiş varsayımdı. Bu dosya o borcu DAVRANIŞ testiyle kapatır; kapının hükmünü
  `classify_gate` üzerinden (gerçek tüketici yüzey) ve karar ağacı satırından (`detail_out`, Faz 3)
  ölçer. Hiçbir test iç değişkene ya da kaynak metnine bakmaz.

MUTASYON SINIFLARI (hedeflenen)
  A. KNOB OKUMA        (5-13, 99-107)  : anahtar adı, varsayılan, `or/and` kısa devresi
  B. KAPALILIK KAPISI  (14-15, 108-109): `> 0` yönü ve sınırı — default-off sözleşmesinin kendisi
  C. ALAN ADLARI       (16-23, 27-29, 33, 38-40, 45-47, 110-113, 137-139, 144-146): plan/portföy
                         sözlüğünden HANGİ alanın okunduğu (equity/sector_notional/notional/
                         heat_pct/risk_dollars) ve eksik alan varsayılanları
  D. ARİTMETİK         (51-55, 148-153): yüzde formülü, işaret, aday planın DAHİL edilmesi
  E. SINIR EŞİTLİĞİ    (70, 171)       : `>` mü `>=` mi — tavana EŞİT pay/ısı GEÇER
  F. NAV=0 DALI        (30, 49-50, 78-96, 147, 154-156): ölçülemeyen NAV'da tavan UYGULANMAZ ve
                         SESSİZ KALMAZ; sıfıra bölme yok
  G. _chk SÖZLEŞMESİ   (56-69, 71-77, 115-133, 157-170, 172-178): kontrol adı, şiddet ("hard"/
                         "soft" → NO_GO/REVIEW ayrımı), value/threshold alanları, yuvarlama basamağı

EŞDEĞER — ÖLDÜRÜLEMEZ (YASA 4 ruhu: ölçülemeyen şey uydurulmaz, kayda geçer)
  Aşağıdaki 16 mutant gerçek kodda GÖZLENEBİLİR bir davranış değişikliği üretmez; test yazmaya
  çalışmak yanlış-yeşil bir "kapsam" iddiası olurdu:
    7, 9        `p.get("portfolio.sector_cap", None|<eksik>) or 0` — anahtar varsa değer aynı,
                yoksa `None or 0` == `0 or 0` == 0. float() ikisini de 0.0 yapar.
    101, 103    aynı sınıf, `portfolio.heat_cap` için.
    79          `_chk(..., None, ...)` yerine `False`: `not None` == `not False` == True ve
                `if failed:` ikisinde de yanlış. Karar ağacı satırı BİREBİR aynı.
    116         aynı sınıf, `y3_heat_cap` "ölçülemedi" dalı için.
    80, 117     `why=None`: bu iki çağrıda `failed` SABİT False, `_chk` ise `why`yi yalnız
                `note = why if failed else None` içinde kullanır → dize hiçbir yolda gözlenmez.
    92, 93, 94  aynı iki çağrıdaki "ölçülemedi" DİZESİNİN kendisinin mutasyonları (XX.., küçük/büyük
                harf) — yukarıdaki gerekçeyle ölü metin; ancak `failed` True'ya dönerse görünür
                (mutant 91/128 tam olarak bu ve onlar ÖLDÜRÜLÜYOR).
    129, 130, 131  aynı sınıf, ısı dalı dizesi.
    87, 124     `value=None` argümanının DÜŞÜRÜLMESİ — `_chk` imzasındaki varsayılan zaten None.
  TOPLAM: 16 eşdeğer → öldürülebilir hedef 172 − 16 = 156.

ÖLÇÜLDÜ, TAHMİN EDİLMEDİ (2026-08-01)
  Kapsam iddiası mutant gövdeleri `guard._y3_portfolio_caps`e tek tek bağlanıp bu dosyanın 18 testi
  süreç içinde koşturularak ÖLÇÜLDÜ: 172 hayatta-kalandan 156'sı ÖLÜYOR; hayatta kalan 16'nın
  kümesi yukarıdaki eşdeğer listesiyle BİREBİR aynı (fark: boş küme). Yani "eşdeğer" iddiası
  ölçümle uyumludur, gerekçesi de her satırın yanında yazılıdır.

  UYARI (okuyucusu olan bir kayıt): bu dosya `pyproject.toml`daki
  `[tool.mutmut] pytest_add_cli_args_test_selection` listesinde DEĞİLDİR. Liste POZİTİF seçimdir;
  dosya oraya eklenmedikçe haftalık mutasyon koşumu bu 156 kill'i GÖRMEZ ve skor olduğu yerde
  kalır. Ekleme Rol-1/operatör kalemidir (ajanlar yapılandırmaya dokunmaz).

Deterministik: ağ yok, dosya yok, canlı state'e yazım yok; `guard.classify_gate` saf bir fonksiyon.
"""
from __future__ import annotations

from meridian import guard


# ---- FİKSTÜR: Y3 DIŞINDA HER KONTROLÜ GEÇEN TEMEL PLAN ------------------------------------------
# Kasıtlı olarak "temiz" seçildi: böylece bir Y3 tavanı tetiklendiğinde NO_GO'nun tek nedeni odur ve
# testler komşu kuralların gürültüsüyle değil, ölçmek istedikleri davranışla yeşil/kırmızı olur.
TEMEL_PLAN = {"sector": "Tech", "r_multiple_expected": 3.0, "size_r": 1.0, "score": 90}
TEMEL_PF = {"open_positions": 0, "sector_counts": {}, "day_pnl_pct": 0.0,
            "open_risk_r": 0.0, "max_corr": 0.0}
TEMEL_REJIM = {"exposure_budget_pct": 80, "leading_sectors": []}


def _hedef():
    return {"limits": {"max_open_positions": 10, "max_sector_exposure_pct": 30,
                       "max_daily_loss_pct": 5, "max_position_r": 2.0, "autonomy_level": 0}}


def _kapi(plan_ek=None, pf_ek=None, params=None, plan_sil=(), pf_sil=()):
    """(hüküm, nedenler, {kontrol_adı: karar_ağacı_satırı}) döndürür."""
    plan = {**TEMEL_PLAN, **(plan_ek or {})}
    pf = {**TEMEL_PF, **(pf_ek or {})}
    for k in plan_sil:
        plan.pop(k, None)
    for k in pf_sil:
        pf.pop(k, None)
    detay: list = []
    hukum, nedenler = guard.classify_gate(plan, pf, dict(TEMEL_REJIM), _hedef(),
                                          params=params, detail_out=detay)
    return hukum, list(nedenler), {d["check"]: d for d in detay}


# =================================================================================================
# ÇAPA — fikstür gerçekten temiz mi? (bu düşerse aşağıdaki her testin anlamı kayar)
# =================================================================================================
def test_temel_fikstur_Y3_disinda_hicbir_bayrak_uretmez():
    hukum, nedenler, satirlar = _kapi(params={})
    assert (hukum, nedenler) == ("GO", []), f"temel fikstür kirli: {nedenler}"
    assert all(s["passed"] for s in satirlar.values())


# =================================================================================================
# B. DEFAULT-OFF: knob yok/0 iken İKİ TAVAN DA KARAR AĞACINDA GÖRÜNMEZ
#    (mutant 12, 13, 14, 106, 107, 108 — varsayılanı 1 yapan, `or 1` düşüren ve `>0`ı `>=0` yapan
#     varyantlar bloğu SESSİZCE açar. "Hüküm değişmedi" demek YETMEZ: kapalı bir knobun karar
#     ağacında satır üretmesi, panoya ve denetime AÇIKMIŞ gibi görünür.)
# =================================================================================================
def test_knoblar_kapaliyken_iki_tavan_da_karar_agacinda_HIC_gorunmez():
    # Portföy KASITLI olarak "tavanı patlatacak" verilerle dolu: blok yanlışlıkla açılırsa
    # sessiz kalamaz, hem satır üretir hem hükmü NO_GO'ya çevirir.
    pf = {"equity": 100_000.0, "sector_notional": {"Tech": 90_000.0}, "heat_pct": 20.0}
    plan = {"notional": 90_000.0, "risk_dollars": 5_000.0}
    for params in ({}, None, {"entry.min_score": 60}):
        hukum, nedenler, satirlar = _kapi(plan, pf, params=params)
        assert hukum == "GO" and nedenler == [], f"params={params} → {hukum}/{nedenler}"
        assert "y3_sector_cap" not in satirlar, f"KAPALI sektör knobu satır üretti (params={params})"
        assert "y3_heat_cap" not in satirlar, f"KAPALI ısı knobu satır üretti (params={params})"


# =================================================================================================
# ① SEKTÖR NOTIONAL TAVANI
# =================================================================================================
def test_sektor_payi_tavani_asinca_SERT_veto_ve_pay_iki_ondalikla_kaydedilir():
    """Ana yol. `value` iki ondalıkla ölçülür: yuvarlama basamağını kaydıran/silen varyantlar
    (round(pay), round(pay,3), round(2), value=None) burada ayrışır — pay 33.333… seçildi."""
    hukum, nedenler, satirlar = _kapi({"notional": 100.0},
                                      {"equity": 900.0, "sector_notional": {"Tech": 200.0}},
                                      params={"portfolio.sector_cap": 25.0})
    assert hukum == "NO_GO", "tavanı %8 aşan pay SERT veto üretmedi"
    assert nedenler == ["Y3 sektör tavanı: 'Tech' payı %33.3 > %25"], nedenler
    s = satirlar["y3_sector_cap"]
    assert s["passed"] is False and s["severity"] == "hard"
    assert s["value"] == 33.33, f"pay iki ondalıkla kaydedilmedi: {s['value']}"
    assert s["threshold"] == "<=25%"
    assert s["note"] == nedenler[0]


def test_sektor_payi_tavana_ESITken_gecer_asinca_duser():
    """Sınır eşitliği: kural `>` — tavana TAM oturan pay GEÇER. `>=` varyantı (70) ve %100 yerine
    %101 ölçen varyant (54) yalnız burada ayrışır."""
    hukum, nedenler, satirlar = _kapi({"notional": 100.0},
                                      {"equity": 1000.0, "sector_notional": {"Tech": 150.0}},
                                      params={"portfolio.sector_cap": 25.0})
    assert (hukum, nedenler) == ("GO", []), "tavana EŞİT pay veto edildi (sınır kayması)"
    s = satirlar["y3_sector_cap"]
    assert s["passed"] is True and s["value"] == 25.0 and s["note"] is None

    # bir kuruş üstü düşer — kuralın gerçekten sınırda olduğunun kanıtı
    hukum2, nedenler2, _ = _kapi({"notional": 100.01},
                                 {"equity": 1000.0, "sector_notional": {"Tech": 150.0}},
                                 params={"portfolio.sector_cap": 25.0})
    assert hukum2 == "NO_GO" and nedenler2, "sınırın bir kuruş üstü geçti"


def test_aday_planin_notionali_tavana_ONCEDEN_eklenir():
    """Tavan ÖNCEDEN bakar: sektör tek başına altta kalsa bile aday planla birlikte aşıyorsa veto.
    (Planı düşüren/çıkaran varyantlar 44-47 ve toplamı FARKA çeviren 55 burada ölür.)"""
    pf = {"equity": 1000.0, "sector_notional": {"Tech": 240.0}}
    prm = {"portfolio.sector_cap": 25.0}

    hukum_plansiz, _, s0 = _kapi({}, pf, params=prm, plan_sil=("notional",))
    assert hukum_plansiz == "GO" and s0["y3_sector_cap"]["value"] == 24.0

    hukum_planli, nedenler, s1 = _kapi({"notional": 20.0}, pf, params=prm)
    assert hukum_planli == "NO_GO" and nedenler, "aday planın notionali tavana girmedi"
    assert s1["y3_sector_cap"]["value"] == 26.0


def test_plan_sektorsuzse_soru_isareti_kovasi_okunur():
    """`sector` yoksa varsayılan '?' — hem sektör notional kovası hem gerekçe metni onu kullanır."""
    hukum, nedenler, _ = _kapi({"notional": 100.0},
                               {"equity": 900.0, "sector_notional": {"?": 200.0}},
                               params={"portfolio.sector_cap": 25.0},
                               plan_sil=("sector",))
    assert hukum == "NO_GO"
    assert nedenler == ["Y3 sektör tavanı: '?' payı %33.3 > %25"], nedenler


def test_sektor_notional_haritasi_yoksa_SIFIR_sayilir_uydurulmaz():
    """Harita eksikken sektör payı 0 kabul edilir (1.0 gibi bir varsayılan icat EDİLMEZ) ve
    hesap patlamaz."""
    hukum, nedenler, satirlar = _kapi({"notional": 4.0}, {"equity": 100.0},
                                      params={"portfolio.sector_cap": 4.0},
                                      pf_sil=("sector_notional",))
    assert (hukum, nedenler) == ("GO", [])
    assert satirlar["y3_sector_cap"]["value"] == 4.0
    assert satirlar["y3_sector_cap"]["threshold"] == "<=4%"


def test_plan_notionali_yoksa_SIFIR_sayilir_uydurulmaz():
    hukum, nedenler, satirlar = _kapi({}, {"equity": 100.0, "sector_notional": {"Tech": 4.0}},
                                      params={"portfolio.sector_cap": 4.0},
                                      plan_sil=("notional",))
    assert (hukum, nedenler) == ("GO", [])
    assert satirlar["y3_sector_cap"]["value"] == 4.0


def test_NAV_olculemezse_sektor_tavani_UYGULANMAZ_ve_SESSIZ_KALMAZ():
    """NAV=0: tavan uygulanmaz (hüküm değişmez, sıfıra bölme yok) AMA karar ağacında SOFT bir
    satırla beyan edilir — 'tavan tuttu' diye okunamaz. `value` None'dır: ölçülemeyen sayı
    uydurulmaz (UYDURMA YASAĞI).

    ÇİVİ GÜNCELLENDİ (2026-08-02, Rol-1 hükmü — C12 ek bulgusu). Eskiden burada `note is None`
    yazıyordu ve o çivi, guard'ın KENDİ beyanını ("bu SESSİZ KALMAZ") test yeşilken ihlal
    ediyordu: `passed=True, note=None` bir satır, denetimde "tavan çalıştı ve geçti"den AYIRT
    EDİLEMEZ. Yeni yasa: `passed` DEĞİŞMEZ (fail-open bilinçli — Y3 alanlarını hâlâ göndermeyen
    üreticiler var, `False` onların TÜM planlarını keserdi), ama satır EKSİK ALANI adıyla taşır.
    ÖLÇÜLEMEDİ ≠ HÜKÜM."""
    pf = {"equity": 0.0, "sector_notional": {"Tech": 5000.0}}
    hukum, nedenler, satirlar = _kapi({"notional": 1000.0}, pf,
                                      params={"portfolio.sector_cap": 25.0})
    assert (hukum, nedenler) == ("GO", []), "ölçülemeyen NAV bir vetoya dönüştü"
    s = satirlar["y3_sector_cap"]
    assert s["passed"] is True, "ölçüm yapılamadığı tur 'tavan çalıştı' diye kaydedildi"
    assert s["severity"] == "soft"
    assert s["value"] is None and s["threshold"] == "<=25%"
    assert s["note"] and "ölçülemedi" in s["note"], \
        "geçen satır sebebini taşımıyor — 'tavan tuttu'dan ayırt edilemez"
    assert "equity" in s["note"], "EKSİK ALAN adıyla yazılmalı (hangi kablo bağlanacak?)"
    assert "fail-open" in s["note"], "hükmün YOK olduğu beyan edilmeli"

    # equity ALANI HİÇ YOKKEN de aynı dal: eksik alan ile 0.0 aynı anlama gelir
    _, _, satirlar2 = _kapi({"notional": 1000.0}, pf, params={"portfolio.sector_cap": 25.0},
                            pf_sil=("equity",))
    assert satirlar2["y3_sector_cap"]["severity"] == "soft"
    assert satirlar2["y3_sector_cap"]["value"] is None
    assert satirlar2["y3_sector_cap"]["note"] == s["note"], "iki eksik-alan yolu farklı beyan veriyor"


def test_NAV_bir_dolarken_bile_sektor_tavani_OLCULUR():
    """`nav > 0` sınırı 1'e kaymamalı: 1 dolarlık NAV ölçülebilir bir NAV'dır."""
    hukum, nedenler, satirlar = _kapi({"notional": 1.0},
                                      {"equity": 1.0, "sector_notional": {"Tech": 0.0}},
                                      params={"portfolio.sector_cap": 10.0})
    assert hukum == "NO_GO" and nedenler
    assert satirlar["y3_sector_cap"]["severity"] == "hard"
    assert satirlar["y3_sector_cap"]["value"] == 100.0


def test_sektor_knobu_yuzde_bir_iken_de_ACIK_sayilir():
    """Açıklık sınırı `> 0`; `> 1` olsaydı bandın en sıkı ucu (%1) SESSİZCE kapalı kalırdı."""
    hukum, nedenler, satirlar = _kapi({"notional": 50.0},
                                      {"equity": 1000.0, "sector_notional": {"Tech": 0.0}},
                                      params={"portfolio.sector_cap": 1.0})
    assert hukum == "NO_GO" and nedenler
    assert satirlar["y3_sector_cap"]["threshold"] == "<=1%"


# =================================================================================================
# ② PORTFÖY ISI TAVANI (NAV %)
# =================================================================================================
def test_isi_tavani_asilinca_SERT_veto_ve_toplam_uc_ondalikla_kaydedilir():
    """Ana yol. `value` ÜÇ ondalıkla ölçülür (sektör payından farklı basamak — karıştırılamaz);
    toplam 4.23456 seçildi ki round(x), round(x,4) ve %101 varyantı burada ayrışsın."""
    hukum, nedenler, satirlar = _kapi({"risk_dollars": 12_345.6},
                                      {"heat_pct": 3.0, "equity": 1_000_000.0},
                                      params={"portfolio.heat_cap": 4.0})
    assert hukum == "NO_GO", "tavanı aşan ısı SERT veto üretmedi"
    assert nedenler == ["Y3 ısı tavanı: açık risk %4.23 NAV > %4.0"], nedenler
    s = satirlar["y3_heat_cap"]
    assert s["passed"] is False and s["severity"] == "hard"
    assert s["value"] == 4.235, f"toplam üç ondalıkla kaydedilmedi: {s['value']}"
    assert s["threshold"] == "<=4.0%"
    assert s["note"] == nedenler[0]


def test_isi_toplami_tavana_ESITken_gecer_ve_risksiz_plan_SIFIR_ekler():
    """İki hüküm bir arada: sınır `>` (eşit geçer) ve `risk_dollars` yoksa katkı 0'dır (1.0 gibi
    bir varsayılan icat edilmez — edilseydi bu senaryo NO_GO olurdu)."""
    hukum, nedenler, satirlar = _kapi({}, {"heat_pct": 6.0, "equity": 100.0},
                                      params={"portfolio.heat_cap": 6.0},
                                      plan_sil=("risk_dollars",))
    assert (hukum, nedenler) == ("GO", []), "tavana EŞİT ısı veto edildi (sınır kayması)"
    s = satirlar["y3_heat_cap"]
    assert s["passed"] is True and s["value"] == 6.0 and s["note"] is None

    hukum2, nedenler2, _ = _kapi({"risk_dollars": 0.01}, {"heat_pct": 6.0, "equity": 100.0},
                                 params={"portfolio.heat_cap": 6.0})
    assert hukum2 == "NO_GO" and nedenler2, "sınırın üstü geçti"


def test_isi_olculemezse_tavan_UYGULANMAZ_ve_SESSIZ_KALMAZ():
    """`heat_pct` yok/None: 3a beyanı ('yalnız gösterge') knob açıkken de korunur ama SOFT satır
    zorunludur — açık bir knobun ölçüm yapamadığı tur denetimde görünmelidir.

    ÇİVİ GÜNCELLENDİ (2026-08-02, Rol-1 hükmü): `note is None` yerine BEYAN. Gerekçe kardeş
    testte (sektör tavanı) yazılı; `passed` değişmedi, satır artık eksik alanı adıyla taşıyor."""
    for pf, sil in (({"equity": 100_000.0}, ("heat_pct",)),
                    ({"equity": 100_000.0, "heat_pct": None}, ())):
        hukum, nedenler, satirlar = _kapi({"risk_dollars": 50_000.0}, pf,
                                          params={"portfolio.heat_cap": 6.0}, pf_sil=sil)
        assert (hukum, nedenler) == ("GO", []), "ölçülemeyen ısı bir vetoya dönüştü"
        s = satirlar["y3_heat_cap"]
        assert s["passed"] is True, "ısı ölçülemediği tur 'tavan çalıştı' diye kaydedildi"
        assert s["severity"] == "soft"
        assert s["value"] is None and s["threshold"] == "<=6.0%"
        assert s["note"] and "ölçülemedi: heat_pct" in s["note"] and "fail-open" in s["note"], s
        assert "equity" not in s["note"], \
            "NAV ÖLÇÜLMÜŞKEN eksik alan listesine yazılmış — beyan hangi kablonun eksik " \
            "olduğunu yanlış söylerse okuyucuyu yanlış yere baktırır"

    # İKİ alan birden eksikse İKİSİ de yazılır (hangi kabloyu bağlayınca tavan ayağa kalkar?)
    _, _, satirlar3 = _kapi({"risk_dollars": 50_000.0}, {"equity": 0.0, "heat_pct": None},
                            params={"portfolio.heat_cap": 6.0})
    n3 = satirlar3["y3_heat_cap"]["note"]
    assert "heat_pct" in n3 and "equity" in n3, n3


def test_NAV_yokken_plan_riski_isiya_EKLENMEZ_ve_sifira_bolunmez():
    """NAV ölçülemezse aday planın risk katkısı 0'dır (1.0 değil) ve bölme HİÇ yapılmaz."""
    hukum, nedenler, satirlar = _kapi({"risk_dollars": 1000.0},
                                      {"heat_pct": 5.5, "equity": 0.0},
                                      params={"portfolio.heat_cap": 6.0})
    assert (hukum, nedenler) == ("GO", [])
    assert satirlar["y3_heat_cap"]["value"] == 5.5
    assert satirlar["y3_heat_cap"]["severity"] == "hard", \
        "ısı ÖLÇÜLDÜ; NAV'ın yokluğu bu satırı 'ölçülemedi'ye çeviremez"


def test_NAV_bir_dolarken_plan_riski_TAM_olcekle_isiya_girer():
    """`nav > 0` sınırı burada da 1'e kaymamalı: 1 dolar NAV'da 10 sentlik risk %10'dur."""
    hukum, nedenler, satirlar = _kapi({"risk_dollars": 0.1},
                                      {"heat_pct": 1.0, "equity": 1.0},
                                      params={"portfolio.heat_cap": 6.0})
    assert hukum == "NO_GO" and nedenler
    assert satirlar["y3_heat_cap"]["value"] == 11.0


def test_isi_knobu_yuzde_bir_iken_de_ACIK_sayilir():
    hukum, nedenler, satirlar = _kapi({"risk_dollars": 0.0},
                                      {"heat_pct": 2.0, "equity": 100_000.0},
                                      params={"portfolio.heat_cap": 1.0})
    assert hukum == "NO_GO" and nedenler
    assert satirlar["y3_heat_cap"]["threshold"] == "<=1.0%"


# =================================================================================================
# İKİ TAVANIN BAĞIMSIZLIĞI
# =================================================================================================
def test_iki_tavan_birbirinin_hukmunu_TASIMAZ():
    """Sektör tavanı patlarken ısı tavanı rahat: NO_GO'nun TEK nedeni sektör olmalı ve ısı satırı
    ayrıca GEÇMİŞ olarak kaydedilmeli (tek bir tavanın diğerinin adına hüküm vermesi, panoda
    yanlış kök-neden okunmasına yol açar)."""
    hukum, nedenler, satirlar = _kapi(
        {"notional": 100.0, "risk_dollars": 0.0},
        {"equity": 900.0, "sector_notional": {"Tech": 200.0}, "heat_pct": 1.0},
        params={"portfolio.sector_cap": 25.0, "portfolio.heat_cap": 10.0})
    assert hukum == "NO_GO"
    assert nedenler == ["Y3 sektör tavanı: 'Tech' payı %33.3 > %25"], nedenler
    assert satirlar["y3_sector_cap"]["passed"] is False
    assert satirlar["y3_heat_cap"]["passed"] is True
    assert satirlar["y3_heat_cap"]["value"] == 1.0
