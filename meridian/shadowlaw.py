"""shadowlaw.py — BÜYÜKLÜK YASASI **PARA-v3**: yeni yasanın tanımı + ESKİ YASANIN GÖLGESİ.

TERS GÖLGELEME (2026-07-30, operatör onayı "1 numaradan başla"). Bu dosya 3b'de "v2 gölge yasası"
idi: karar eski bileşik skordaydı, v2 kayda geçiyordu. Yasa yeniden tasarlandıktan sonra yön TERSİNE
döndü — **karar PARA-v3'te, ESKİ YASA kayda geçiyor.** Modülün makinesi aynı makinedir (tek
`score_detail` çağrısından iki yasa türetmek); yalnız hangisinin hüküm verdiği değişti.

NEDEN DEĞİŞTİ — ÖLÇÜLMÜŞ ZİNCİR (uydurma yok, üçü de bu depoda ölçüldü):

  (1) 3a E RAPORU: kapının gerçek karar değişkeni `P(ΔS>0) ≥ 1 − 0,20/K` ve ΔS varyansının
      **%82'si düşüş, %17,7'si Sharpe, %0,3'ü PARA** terimiydi. Yani "büyüklük kapısı" fiilen bir
      düşüş+düzgünlük kapısıydı; kârın kapı kararına katkısı üç binde üçtü.
  (2) 3b GÖLGE-YASA ÖLÇÜMÜ (v2 rötuşu): ret_c'nin ÖLÇEĞİNİ düzeltmek PARA payını %0,3 → %3,2
      yaptı; hedef ≥%40 TUTMADI, üç ağırlık denemesi de tutmadı (bkz. `MEASURED_V2`,
      `V2_WEIGHT_TRIALS`, `WHY_40_UNREACHABLE` — o ölçüm kaydı SİLİNMEDİ, v3'ün GEREKÇESİDİR).
  (3) KÖK NEDEN: ölçek değil ÇİFT-SAYIM. σ(dd_c)=0,4182 ve σ(sharpe_c)=0,2917, σ(ret_c)≈0,015-0,050
      iken — çünkü dd ve Sharpe'ın PAYDALARI (maks düşüş %8, 2·min_sharpe=2,4) kendi gerçekleşen
      dağılımlarına göre DAR. Ve bu iki bacak HEM skorun varyansında HEM ayrı sert kapılarda
      sayılıyordu (kuyruk vetosu + 3A kuyruk ölçütü + maks düşüş ölçütü). PARA tek uygulanan bacaktı.

YENİ YASA — TEK TERİM, ÇARPITMASIZ:

    ΔS_v3 = ret_c_v3(aday) − ret_c_v3(incumbent)        ← kapının KARAR değişkeni

    ret_c_v3 = kıs( pencere_bileşik_getirisi / hedef_pencere )
    hedef_pencere = (1 + %25)^(span/365) − 1            ← yıllık %25'in pencere-eşlenik karşılığı

30-GÜNE İNDİRGEME YOK. Eski yasa payı `(1+R)^(30/span) − 1` yazıyordu; 1274 günlük bir defterde üs
30/1274 = 0,0235'tir, yani yeniden-örneklemenin ürettiği getiri oynaklığının ~%98'ini SÖNDÜRÜR
(ölçüldü: σ(ret_c_eski) = 0,0151). v3'te pay HAM bileşik getiridir ve payda sabittir, dolayısıyla
ret_c_v3 getiride DOĞRUSALDIR — ölçülen σ 0,0356, yani eski terimin 2,36 katı oynaklık. Aynı
ölçek ailesinden (`ANNUAL_TARGET_RETURN`) ama çarpıtmasız.

dd_c ve sharpe_c SKORDAN ÇIKTI. Kaybolmadılar — GÜÇLENEREK vetolara taşındılar (`reflect`):
fold-çoğunluğu + VaR/CVaR kuyruk vetosu (`TAIL_MARGIN_R`) + **düşüş vetosu** (`DD_VETO_MARGIN`,
bu turda EKLENDİ) + aşınma marjı + 3A kuyruk ölçütü. Sharpe hiçbir yerde AYRICA sayılmaz: fold
çoğunluğu (pencere-pencere tutarlılık), kuyruk vetosu (dağılımın sol ucu) ve DSR (deneme-düzeltmeli
Sharpe) onu üç ayrı açıdan zaten kapsıyor. Çift-sayım biter, koruma bitmez.

ANNUAL_TARGET_RETURN = %25 NEDEN: literatürdeki en iyi belgelenmiş uzun-vadeli momentum/kırılım
programlarının net bandı yıllık %15-30'dur; bu depoda ayrıca 3A kuyruk ölçütü (maks düşüş ≤ %8) ve
ısı tavanı gibi risk kısıtları AYNI ANDA yürürlüktedir, yani hedef yalnız getiriyle değil
düşüş-bütçesiyle de tutarlı olmak zorundadır. %25/yıl, %8 düşüş bütçesiyle Calmar ≈ 3 demektir —
iddialı ama uydurma değil. Eski yasanın aylık %7 hedefi yılda %125'e denk geliyordu (gerçekçi bir
programın 2-3 katı): payda şişince pay küçülür ve terim ikinci kez ezilirdi.

BU MODÜL HÜKÜM VERMEZ. Hükmü `reflect.submit` verir, ölçümü `probgate` yapar; burada yasanın
TANIMI, ölçülmüş sabitleri ve eski yasanın gölge hesabı durur."""
from __future__ import annotations

import datetime as dt

import numpy as np

from . import score as score_mod

# ---- PARA-v3'ün adlandırılmış sabitleri (docstring'de gerekçeli) --------------------------------
ANNUAL_TARGET_RETURN: float = 0.25     # gerçekçi YILLIK getiri hedefi (bkz. modül beyanı)
YASA_SURUMU: str = "para_v3"           # kapı kayıtlarına basılan damga
YASA_GECIS_TARIHI: str = "2026-07-30"  # geçiş tarihi — kayıtlarda hangi yasanın koştuğu okunabilsin
YASA_METNI: str = ("ΔS = ret_c_v3(aday) − ret_c_v3(incumbent); "
                   "ret_c_v3 = kıs(pencere_bileşik_getirisi / ((1+%25)^(span/365) − 1))")

# ---- ESKİ YASA (artık GÖLGE) --------------------------------------------------------------------
# (ret, dd, sharpe) — `score.score_detail`de RAPOR metriği olarak yürürlükte; kapı KARARINDA değil.
# NOT: eski `V2_WEIGHTS` adı KALDIRILDI (takma ad bırakmak ölü kod olurdu — hiçbir tüketicisi yok).
OLD_LAW_WEIGHTS: tuple[float, float, float] = (0.5, 0.3, 0.2)
OLD_LAW_METNI: str = "kıs(0,5·ret_c + 0,3·dd_c + 0,2·sharpe_c)  [30-güne indirgemeli, aylık %7 hedef]"

# ---- MARJ ÇEVRİMİ: bileşik-ölçek → para-ölçek ---------------------------------------------------
# `reflect.GATE_MARGIN = 0.02` BİLEŞİK ölçekte tanımlanmıştı. Para ölçeğinde aynı SERTLİKTE kalması
# için marj, karar değişkeninin KENDİ gürültüsünde aynı yerde durmalıdır:
#     0,02 / σ(S_eski) = 0,02 / 0,18644 = 0,107 σ        → eski marj yalnız 0,11 σ'ydı
#     yeni marj = 0,107 σ × σ(ΔS_v3) = 0,02 × 0,1908 = 0,00382  → adlandırılmış sabit 0,004
# ÇARPAN = σ(ret_c_v3)/σ(S_eski), canlı defterde ÖLÇÜLDÜ (aşağıdaki MEASURED_V3).
#
# NEDEN σ-EŞDEĞERLİĞİ, "PARA-BACAĞI OKUMASI" DEĞİL: ikinci bir çevrim daha vardı — "0,02 bileşik
# birimi SALT parayla kazanılsa ne gerekirdi?" (Δret_c_eski = 0,02/0,5 = 0,04 → para ölçeğinde
# 0,0945, yani 25 KAT daha sert bir marj). O okuma REDDEDİLDİ çünkü eski yasada o para HİÇ
# TOPLANMIYORDU: bir aday 0,02'yi tek başına düşüşle de aşabiliyordu (varyansın %82'si oradaydı).
# Nominal olarak fiyatlanan ama hiç tahsil edilmeyen bir bedeli yeni yasada tahsil etmek, yasayı
# "ΔS tanımı değişir" sınırının çok dışına taşırdı — ve turun beyanı bu değildi.
MARGIN_MONEY_SCALE: float = 0.1908     # σ(ΔS_v3)/σ(S_eski) — ÖLÇÜLDÜ (0,03558/0,18644)
MONEY_GATE_MARGIN: float = 0.004       # 0,02 × 0,1908 = 0,00382 → 0,004 (para ölçeğinde taban marj)

# ---- DÜŞÜŞ VETOSU: skordan çıkan bacak, sert kapıya taşındı -------------------------------------
# Adayın Search-dilim maks düşüşü incumbent'ınkini bu marjdan fazla aşarsa RET. TEK YÖNLÜ:
# kötüleşmeyi cezalandırır, iyileşmeyi ÖDÜLLENDİRMEZ (ödüllendirse skora geri sızar ve çift-sayım
# arka kapıdan geri gelirdi).
# MARJ NEDEN 0,04 — İKİ BAĞIMSIZ TÜRETİM AYNI SAYIYA ÇIKTI:
#   (1) KENDİ GÜRÜLTÜSÜNÜN DIŞINDA: canlı defterde blok-yeniden-örneklemeyle ölçülen σ(düşüş) =
#       0,0343 (2000 replikasyon; ortalama düşüş %6,9, %5-%95 bandı %2,4-%13,4). Vetonun karar
#       sınırı kendi ölçüm gürültüsünün İÇİNDE olamaz — `TAIL_SIMS`in dersi (marjın yarısı kadar
#       gürültü kabul edilemezdi). 0,04 > 0,0343.
#   (2) BÜTÇENİN YARISI: `goal.max_drawdown` = %8 tüm düşüş bütçesidir; 0,04 onun tam yarısıdır —
#       "aday, incumbent'ın üstüne bütçenin yarısını daha yakamaz" okunabilir bir kuraldır.
DD_VETO_MARGIN: float = 0.04

# ---- CANLI DEFTERDE ÖLÇÜLEN (2026-07-30, seed=42, n_boot=2000, block_days=15, span=1274g) ------
# Sabit DEĞİL, ÖLÇÜM KAYDIDIR: `variance_attribution()` her çağrıda yeniden ölçer ve `--olc` CLI'ı
# ikisini karşılaştırır. Burada durmalarının sebebi marj çevriminin ve pano satırının 2000
# replikasyonluk bir yeniden ölçüm yapmadan okunabilir olması gerektiğidir.
MEASURED_V3: dict = {
    "ts": "2026-07-30", "n_trades": 95, "span_days": 1274, "block_days": 15, "n_boot": 2000,
    "seed": 42, "n_valid": 2000,
    "hedef_pencere": 1.178993,          # (1,25)^(1274/365) − 1
    "eski_paylar": {"para": 0.0029, "dusus": 0.8198, "sharpe": 0.1772},   # E raporuyla BİREBİR
    "v3_paylar": {"para": 1.0, "dusus": 0.0, "sharpe": 0.0},              # yapı gereği — ÖLÇÜLDÜ
    "sd_ret_c_eski": 0.01505, "sd_ret_c_v3": 0.03558,
    "sd_dd_c": 0.41822, "sd_sharpe_c": 0.29165, "sd_score_eski": 0.18644,
    "sd_dusus": 0.03425, "ort_dusus": 0.06896,       # düşüş vetosu marjının türetim tabanı
    "dusus_p05": 0.0242, "dusus_p95": 0.13371,
    "ret_scale_k": 2.364,               # σ(ret_c_v3)/σ(ret_c_eski) — para terimi 2,36× canlandı
    "margin_scale": 0.1908,             # σ(ret_c_v3)/σ(S_eski) — marj çevriminin çarpanı
    "para_payi_eski": 0.0029, "para_payi_v3": 1.0,
}

# ---- v2 RÖTUŞUNUN ÖLÇÜM KAYDI (SİLİNMEDİ — v3'ün GEREKÇESİ) ------------------------------------
# v2, yasayı ölçek düzeltmesiyle kurtarma denemesiydi ve ÖLÇÜLDÜ, TUTMADI. Ölçülmüş bir olumsuz
# sonucu silmek, aynı denemeyi altı ay sonra yeniden yapmak demektir.
V2_MONEY_SHARE_TARGET: float = 0.40   # v2'nin hedefi; ÖLÇÜLDÜ ve TUTMADI
V2_WEIGHT_TRIALS: tuple[tuple[str, tuple[float, float, float], float], ...] = (
    ("deneme1 (v1 ağırlıkları)", (0.5, 0.3, 0.2), 0.032),
    ("deneme2 (dd↔sharpe yer değişti)", (0.5, 0.2, 0.3), 0.041),
    ("deneme3 (dd=sharpe eşitlendi)", (0.5, 0.25, 0.25), 0.038),
)
MEASURED_V2: dict = {
    "ts": "2026-07-30", "n_trades": 95, "span_days": 1274, "block_days": 15, "n_boot": 2000,
    "seed": 42,
    "v1_shares": {"para": 0.003, "dusus": 0.820, "sharpe": 0.177},
    "v2_shares": {"para": 0.032, "dusus": 0.796, "sharpe": 0.172},
    "sd_ret_c_v1": 0.0151, "sd_ret_c_v2": 0.0504,
    "sd_dd_c": 0.4182, "sd_sharpe_c": 0.2917,
    "sd_score_v1": 0.1864, "sd_score_v2": 0.2038,
    "ret_scale_k": 3.34, "sigma_inflation": 1.093,
    "target_met": False, "trials": 3,
    "hukum": "v2 RÖTUŞU YETMEDİ — ölçek düzeltmesi PARA payını %3,2'de bıraktı; v3'e geçildi",
}

WHY_40_UNREACHABLE = (
    "PARA payı ≥ %40 hedefi v2 RÖTUŞUYLA ölçüldü ve TUTMADI (en iyi deneme %4,1). Sebep ölçek "
    "DEĞİL: getiri/hedef ailesinden HANGİ ölçek seçilirse seçilsin σ(ret_c) ≈ 0,036-0,050'de "
    "kalıyor. Buna karşılık σ(dd_c) = 0,4182 ve σ(sharpe_c) = 0,2917. Fark ölçekten değil "
    "PAYDALARDAN geliyor: max_drawdown = %8 ve 2·min_sharpe = 2,4, kendi gerçekleşen dağılımlarına "
    "göre DAR paydalardır (defterin düşüşü replikasyonlar arasında %2,4-%13,4 bandında geziyor → "
    "dd_c ±0,9 salınıyor), target_return ise GENİŞ bir paydadır. %40'a çıkarmak için dd/sharpe "
    "paydalarının 4,5× genişletilmesi (maks düşüş %8→%36) gerekirdi — anlamsız. YAPISAL ÇÖZÜM "
    "UYGULANDI (PARA-v3, 2026-07-30): düşüş ve Sharpe bacakları skordan ÇIKARILDI ve sert vetolara "
    "bırakıldı (fold çoğunluğu + kuyruk vetosu + DÜŞÜŞ VETOSU + DSR); PARA payı %100 ÖLÇÜLDÜ. "
    "Eski yasada ikisi HEM skorun varyansında HEM ayrı kapıda sayılıyordu — çift-sayım bitti."
)


def _clip(x: float) -> float:
    return max(-1.0, min(1.0, x))


# ---- PARA-v3'ün terimi ---------------------------------------------------------------------------
def hedef_pencere(span_days: float, annual_target: float = ANNUAL_TARGET_RETURN) -> float:
    """Yıllık hedefin PENCERE-EŞLENİK karşılığı: (1+hedef)^(span/365) − 1.

    Payda pencereyle büyür, pay ham getiri olarak kalır — böylece uzun bir pencerede biriken getiri
    ne şişirilir (30-güne indirgemenin tersi) ne de sönümlenir; yalnız DOĞRU hedefe bölünür."""
    span = float(span_days) if span_days and span_days > 0 else 30.0
    return (1.0 + float(annual_target)) ** (span / 365.0) - 1.0


def ret_c_v3(total_return: float, span_days: float,
             annual_target: float = ANNUAL_TARGET_RETURN) -> float:
    """PARA-v3'ün TEK terimi: pencere bileşik getirisi / pencere-eşlenik hedef, [-1,+1]'e kıstırılmış.

    Getiride DOĞRUSAL (üs alma YOK): yeniden-örneklemenin ürettiği getiri oynaklığı sönümlenmez.
    Eski `ret_c` ile kıyas (canlı defter, span=1274g): σ 0,0151 → 0,0356 (2,36×)."""
    h = hedef_pencere(span_days, annual_target)
    if h <= 0:
        return 0.0
    if float(total_return) <= -1.0:
        return -1.0
    return _clip(float(total_return) / h)


# ---- ① PARA ÖLÇEĞİ: R-KATI DEĞİL, GERÇEKLEŞEN DOLAR (WP-M borcu, 2026-08-01) --------------------
# NEDEN VAR. PARA-v3'ün karar sayısı `ret_c_v3` [-1,+1]'e KISTIRILMIŞ bir orandır ve iki yerde
# parayı GÖRÜNMEZ kılar:
#   (1) KIRPILMA BÖLGESİ: |pencere_getirisi| hedefi aştığı anda skor 1,0'da (ya da −1,0'da) DONAR.
#       O bölgede defter iki katına da çıksa yarıya da inse skor AYNI sayıyı yazar — "skor arttı ama
#       para azaldı" (ve tersi) çelişkisinin doğduğu yer tam burasıdır.
#   (2) ÖLÇEK KARIŞIMI: rollback'ın yazdığı `realized_delta` HÂLÂ bileşik ölçektedir
#       (`probgate.refresh_meta_calibration`in `olcek_borcu` alanı bunu adıyla beyan ediyor).
#       Bileşik bir gerçekleşmeyi para ölçeğinde bir öngörüyle kıyaslamak birim karışımıdır; ikisini
#       de bağlayabilecek TEK ortak cetvel, kırpılmamış DOLAR'dır.
# Bu blok o cetveli üretir. HÜKÜM VERMEZ, hiçbir kapıya girmez, mevcut hiçbir alanı değiştirmez —
# `money_score_detail` çıktısına EK bir anahtar olarak durur (geriye-uyum: eski alanların değerleri
# bit-bit aynı kalır, çünkü hesabın hiçbiri onlara dokunmaz).
#
# YAPISAL ÖZDEŞLİK (ve bu bir hata değil, KANITTIR): `skor_usd` = kıs(pnl_usd / hedef_usd) ve
# `pnl_usd/hedef_usd` = (Σpnl/başlangıç_sermayesi) / hedef_pencere = `ret_c_v3`in ta kendisidir.
# Yani normalize edilmiş ikiz, karar skoruyla ÖZDEŞ ÇIKMAK ZORUNDADIR (testte çivili). Bloğun
# bilgi katkısı normalize edilmiş sayıda DEĞİL, `pnl_usd` + `ham_oran` + `kirpildi` üçlüsündedir:
# kırpılma bayrağı, "bu skorun ötesinde para hareket ediyor ama karar değişkeni kör" der.
#
# UYDURMA YASAĞI: `pnl_dollars` taşımayan bir defterde dolar ÖLÇÜLEMEZ — sıfır yazılmaz, None +
# neden döner. Satırların BİR KISMI eksikse ölçüm yapılır ama `tam_kapsam=False` ve kaç satırın
# düştüğü ADIYLA beyan edilir (score.equity_curve eksik alanı sessizce 0 sayıyor; burada sessiz
# değil).
def realized_usd(trades: list[dict], span_days: float | None = None,
                 start_equity: float = score_mod.START_EQUITY,
                 annual_target: float = ANNUAL_TARGET_RETURN) -> dict:
    """Gerçekleşen dolar PnL'in PARA-v3'e paralel ölçeği. Hüküm vermez; ölçüm/karne yolu okur."""
    rows = list(trades or [])
    pnls: list[float] = []
    n_eksik = 0
    for t in rows:
        v = t.get("pnl_dollars")
        if v is None:
            n_eksik += 1
            continue
        try:
            pnls.append(float(v))
        except (TypeError, ValueError):  # sessiz-yutma: biçimsiz tek satır dolar toplamına GİREMEZ ama KAYBOLMAZ — `n_eksik` sayacına yazılır, `tam_kapsam=False` olur ve `neden` alanı kaç satırın düştüğünü söyler; uydurma bir dolar toplamak alternatifti
            n_eksik += 1
    span = float(span_days) if span_days and span_days > 0 else score_mod._span_days(rows)
    hedef_usd = hedef_pencere(span, annual_target) * float(start_equity)
    ortak = {"n_islem": len(rows), "n_pnl": len(pnls), "n_eksik": n_eksik,
             "tam_kapsam": bool(rows) and n_eksik == 0,
             "start_equity": float(start_equity), "span_days": round(span, 1),
             "hedef_usd": round(hedef_usd, 2) if hedef_usd > 0 else None,
             "annual_target": annual_target, "birim": "USD",
             "hukum_verir": False,
             "kapsam": ("PARA-v3'ün KIRPILMAMIŞ ikizi — karar skoru kıs([-1,+1]) olduğu için "
                        "kırpılma bölgesinde paraya kördür; bu blok o körlüğü görünür kılar. "
                        "Hiçbir kapı kararına girmez.")}
    if not pnls:
        return {**ortak, "olculdu": False, "pnl_usd": None, "ham_oran": None,
                "skor_usd": None, "kirpildi": None,
                "neden": ("defterde `pnl_dollars` taşıyan satır YOK — dolar ölçeği ÖLÇÜLEMEDİ "
                          "(sıfır değil, bilinmiyor)" if rows else
                          "defter boş — dolar ölçeği ÖLÇÜLEMEDİ (sıfır değil, bilinmiyor)")}
    if not hedef_usd > 0:
        return {**ortak, "olculdu": False, "pnl_usd": round(sum(pnls), 2), "ham_oran": None,
                "skor_usd": None, "kirpildi": None,
                "neden": ("pencere-eşlenik hedef sıfır/negatif çıktı — oran ölçülemedi "
                          "(pnl_usd yine de ham olarak raporlanır)")}
    pnl_usd = sum(pnls)
    ham = pnl_usd / hedef_usd
    return {**ortak, "olculdu": True, "pnl_usd": round(pnl_usd, 2),
            "ham_oran": round(ham, 6), "skor_usd": round(_clip(ham), 4),
            # KIRPILDI = karar skoru doydu: bu noktadan sonra para hareket eder, skor ETMEZ.
            "kirpildi": bool(abs(ham) > 1.0),
            "neden": (None if n_eksik == 0 else
                      f"{n_eksik}/{len(rows)} satırda `pnl_dollars` yok/biçimsiz — dolar toplamı "
                      f"EKSİK (score.equity_curve bu satırları sessizce 0 sayar; burada beyanlı)")}


def money_score_detail(trades: list[dict], goal: dict, span_days: float | None = None,
                       mtm_equity: list | None = None,
                       annual_target: float = ANNUAL_TARGET_RETURN) -> dict:
    """PARA-v3 karar skoru + yanında ESKİ YASANIN bileşiği (gölge). TEK `score_detail` çağrısı.

    `score_detail` DEĞİŞMEDİ ve değişmeyecek: bileşik skor RAPOR metriği olarak yerinde kalır
    (karne/tarih kırılmasın). Burada yalnız KAPININ okuduğu sayı yeniden türetilir.

    v1 None dönerse (min_sample altı) v3 de None döner: bilinmeyen skor, vasat skor gibi
    okunamaz (§4).

    `realized_usd` (WP-M ①, 2026-08-01) EK bir anahtardır ve İKİ DALDA DA döner — bilerek: skor
    min_sample altında ÖLÇÜLEMEZ ama para ölçülebilir. "Skor yok" ile "para yok" aynı cümle
    değildir ve rollback meta-kalibrasyonunun okumak istediği tam olarak bu ayrımdır. Mevcut
    alanların DEĞERLERİ bu turda değişmedi (geriye-uyum çivisi testte)."""
    d = score_mod.score_detail(trades, goal, span_days=span_days, mtm_equity=mtm_equity)
    if d.get("score") is None:
        return {"score": None, "reason": d.get("reason"), "n": d.get("n"),
                "law": YASA_SURUMU, "decides": True,
                "realized_usd": realized_usd(trades, span_days, annual_target=annual_target)}
    span = float(span_days) if span_days and span_days > 0 else score_mod._span_days(trades)
    rv3 = ret_c_v3(d["total_return"], span, annual_target)
    return {"score": round(rv3, 4), "score_eski_yasa": d["score"], "n": d["n"],
            "realized_usd": realized_usd(trades, span, annual_target=annual_target),
            "total_return": d["total_return"], "span_days": round(span, 1),
            "hedef_pencere": round(hedef_pencere(span, annual_target), 5),
            "annual_target": annual_target,
            "max_drawdown": d["max_drawdown"],        # düşüş vetosunun okuduğu alan
            "components": {"para": round(rv3, 4)},    # TEK terim — yasa metniyle birebir
            "components_eski_yasa": dict(d["components"]),
            "law": YASA_SURUMU, "yasa_metni": YASA_METNI, "decides": True}


def money_score(trades: list[dict], goal: dict, span_days: float | None = None) -> float | None:
    """PARA-v3 karar skoru. None = ölçülemedi (min_sample altı), 0.0 DEĞİL."""
    return money_score_detail(trades, goal, span_days=span_days).get("score")


# ---- ESKİ YASANIN GÖLGESİ (ters gölgeleme) ------------------------------------------------------
# ÇIKARILDI 2026-07-30 (temizlik turu): `score_eski_yasa(trades, goal, …)` — `score.score_detail`
# üzerine "bu çağrı gölge hesabıdır" demek için konmuş ince bir sarmalayıcı.
# ÇAĞIRAN TARAMASI (meridian/ + tests/): tek eşleşme tanımın kendisi ve `money_score_detail`in
# döndürdüğü `"score_eski_yasa"` ANAHTARIYDI — o anahtar bir fonksiyon çağrısı değil, sözlük alanı.
# NEDEN EMEKLİ, "kayıt kaybolmuyor" GEREKÇESİYLE: eski yasanın hükmü ZATEN her karar anında
# `money_score_detail` içinde ölçülüp `score_eski_yasa` + `components_eski_yasa` alanlarıyla
# kayda geçiyor (ters gölgeleme oradan besleniyor, `analytics.shadow_law_row` onu panoya taşıyor).
# Ayrı sarmalayıcı, aynı gölgeyi ikinci bir yoldan üretebilen bir kapıydı.
# GERİ-AL: `return score_mod.score_detail(trades, goal, span_days=span_days,
#                                         mtm_equity=mtm_equity).get("score")` — bu yorumun yerine.


# ---- VARYANS ATAMASI: yeni yasanın kendi çivisi -------------------------------------------------
def _blocks(trades: list[dict]) -> tuple[list[list[dict]], int, int, str]:
    days = sorted(str(t.get("ts_open", ""))[:10] for t in trades if t.get("ts_open"))
    closes = sorted(str(t.get("ts_close", ""))[:10] for t in trades if t.get("ts_close"))
    if not days or not closes:
        return [], 0, 0, ""
    d0 = dt.date.fromisoformat(days[0])
    d1 = dt.date.fromisoformat(closes[-1])
    span = max(1, (d1 - d0).days)
    spans = []
    for t in trades:
        try:
            o = dt.date.fromisoformat(str(t["ts_open"])[:10])
            c = dt.date.fromisoformat(str(t["ts_close"])[:10])
            spans.append(max(1, (c - o).days))
        except (KeyError, ValueError, TypeError):  # sessiz-yutma: biçimsiz/eksik tek işlem satırı; blok boyu MEDYANDAN gelir ve tek satırın düşmesi ölçümü kaydırmaz
            continue
    bdays = int(min(21, max(5, float(np.median(spans))))) if spans else 5
    n_blocks = max(2, -(-span // bdays))
    buckets: list[list[dict]] = [[] for _ in range(n_blocks)]
    for t in trades:
        try:
            off = (dt.date.fromisoformat(str(t["ts_open"])[:10]) - d0).days
        except (KeyError, ValueError, TypeError):  # sessiz-yutma: tarihi çözülemeyen satır hiçbir bloğa giremez; sayılması yanlış bloğa yazmak olurdu
            continue
        if 0 <= off <= span:
            buckets[min(n_blocks - 1, off // bdays)].append(t)
    return buckets, span, bdays, days[0]


def variance_attribution(trades: list[dict], goal: dict, n_boot: int = 2000, seed: int = 42,
                         weights: tuple[float, float, float] = OLD_LAW_WEIGHTS) -> dict | None:
    """AYNI defterde, AYNI blok replikasyonlarında İKİ yasanın varyans atamasını ölçer.

    Atama `Var(w_i·c_i) / Σ_j Var(w_j·c_j)` biçimindedir — E raporunun kullandığı tanım. PARA-v3'te
    skor TEK terimdir, dolayısıyla PARA payı **1,0 çıkmak ZORUNDADIR**: bu bir hedef değil YAPISAL
    ÖZDEŞLİKTİR ve testin çivilediği şey tam olarak "yasa gerçekten tek terimli mi" sorusudur
    (bir gün skora ikinci bir bacak sızarsa pay 1,0'ın altına düşer ve çivi kırılır).

    Ayrıca düşüş vetosunun türetim tabanını da ölçer: σ(düşüş) ve düşüşün %5-%95 bandı.

    None: defter blok kurulamayacak kadar boş/biçimsiz (ölçülemedi, sıfır değil)."""
    buckets, span, bdays, _ = _blocks(trades)
    if not buckets:
        return None
    g = {**goal, "min_sample": 1}
    rng = np.random.default_rng(int(seed))
    rows = []
    for _ in range(int(n_boot)):
        picks = rng.integers(0, len(buckets), size=len(buckets))
        tr = [t for i in picks for t in buckets[i]]
        if not tr:
            continue
        d = score_mod.score_detail(tr, g, span_days=span)
        if d.get("score") is None:
            continue
        rows.append((d["components"]["ret"], ret_c_v3(d["total_return"], span),
                     d["components"]["dd"], d["components"]["sharpe"], d["score"],
                     d["max_drawdown"]))
    if len(rows) < max(200, int(n_boot) // 10):
        return None
    A = np.asarray(rows, dtype=float)
    w_r, w_d, w_s = weights

    def _paylar(parts: np.ndarray) -> dict:
        pv = parts.var(axis=0)
        tot = float(pv.sum())
        share = (pv / tot) if tot > 0 else pv * 0.0
        return {"para": round(float(share[0]), 4), "dusus": round(float(share[1]), 4),
                "sharpe": round(float(share[2]), 4),
                "sd_score": round(float(parts.sum(axis=1).std()), 4)}

    zero = np.zeros(len(A))
    eski = _paylar(np.column_stack([w_r * A[:, 0], w_d * A[:, 2], w_s * A[:, 3]]))
    # v3: skor = ret_c_v3 TEK BAŞINA. Diğer iki kolon SIFIRDIR — "yasada yok"un sayısal ifadesi.
    v3 = _paylar(np.column_stack([A[:, 1], zero, zero]))
    sd = A.std(axis=0)
    sd_ret_eski, sd_ret_v3, sd_score_eski, sd_dusus = (float(sd[0]), float(sd[1]),
                                                       float(A[:, 4].std()), float(sd[5]))
    return {
        "n_trades": len(trades), "span_days": span, "block_days": bdays,
        "n_blocks": len(buckets), "n_valid": len(rows), "n_boot": int(n_boot), "seed": int(seed),
        "annual_target": ANNUAL_TARGET_RETURN, "hedef_pencere": round(hedef_pencere(span), 5),
        "yasa_surumu": YASA_SURUMU, "yasa_metni": YASA_METNI,
        "eski_paylar": {k: eski[k] for k in ("para", "dusus", "sharpe")},
        "v3_paylar": {k: v3[k] for k in ("para", "dusus", "sharpe")},
        "eski_detay": eski, "v3_detay": v3,
        "sd_ret_c_eski": round(sd_ret_eski, 4), "sd_ret_c_v3": round(sd_ret_v3, 4),
        "sd_dd_c": round(float(sd[2]), 4), "sd_sharpe_c": round(float(sd[3]), 4),
        "sd_score_eski": round(sd_score_eski, 4),
        # düşüş vetosunun türetim tabanı — marj bu gürültünün DIŞINDA olmak zorunda
        "sd_dusus": round(sd_dusus, 4), "ort_dusus": round(float(A[:, 5].mean()), 4),
        "dusus_p05": round(float(np.percentile(A[:, 5], 5)), 4),
        "dusus_p95": round(float(np.percentile(A[:, 5], 95)), 4),
        "dd_veto_margin": DD_VETO_MARGIN,
        "dd_veto_gurultunun_disinda": bool(DD_VETO_MARGIN > sd_dusus),
        "ret_scale_k": round(sd_ret_v3 / sd_ret_eski, 3) if sd_ret_eski > 0 else None,
        "margin_scale": round(sd_ret_v3 / sd_score_eski, 4) if sd_score_eski > 0 else None,
        "money_gate_margin": MONEY_GATE_MARGIN,
        "para_payi_tek_terim": bool(v3["para"] >= 0.999),
        "gerekce": WHY_40_UNREACHABLE,
    }


# ---- MEASURED_V3 KAYMA BEKÇİSİ (temizlik turu, 2026-07-30) --------------------------------------
# NEDEN VAR: `MEASURED_V3` bir SABİT değil bir ÖLÇÜM KAYDIDIR (kendi yorumu böyle diyor) ve iki
# yürürlükteki sabit ONDAN TÜRETİLMİŞTİR: `MONEY_GATE_MARGIN` (0,02 × margin_scale) ve
# `DD_VETO_MARGIN` (σ(düşüş)in dışında olmak zorunda). Defter büyüdükçe ölçüm kayar; kayarsa
# türetilmiş sabitler sessizce YANLIŞ SERTLİKTE kalır — kapı ne gevşediğini ne sıkıldığını söyler.
# `variance_attribution` her çağrıda yeniden ölçüyordu ama yalnız `--olc` CLI'ı ve testler
# çağırıyordu: ölçüm vardı, BEKÇİ yoktu.
#
# TOLERANSLAR UYDURULMADI — HER BİRİ KODDA YAZILI BİR GEREKÇEDEN TÜRETİLDİ:
#   1) margin_scale: `MONEY_GATE_MARGIN` yorumu çevrimi "0,02 × 0,1908 = 0,00382 → 0,004" diye
#      yazıyor. Yani sabit, çevrimin ÜÇ BASAMAĞA YUVARLANMIŞ hâlidir ve ölçüm 0,02×scale hâlâ
#      0,004'e yuvarlandığı sürece DOĞRUDUR. Tolerans bandı bu yuvarlamanın kendisidir.
#   2) dd_veto: `DD_VETO_MARGIN` yorumu "Vetonun karar sınırı kendi ölçüm gürültüsünün İÇİNDE
#      olamaz — 0,04 > 0,0343" diyor. `variance_attribution` bunu zaten `dd_veto_gurultunun_disinda`
#      alanında hesaplıyor; kayma = o bayrağın False'a dönmesi.
#   3) para payı: `variance_attribution` docstring'i "PARA payı 1,0 çıkmak ZORUNDADIR: bu bir hedef
#      değil YAPISAL ÖZDEŞLİK" diyor ve eşiği (0,999) `para_payi_tek_terim` alanında yazılı.
# BEKÇİ SABİT GÜNCELLEMEZ. Yeni ölçümü MEASURED_V3'e YAZMAZ, marjları DEĞİŞTİRMEZ — yalnız
# "kayıtlı ölçüm artık defteri anlatmıyor" der. Sabit güncellemesi operatör + Rol 1 kararıdır.
DRIFT_ROUND_NDIGITS = 3        # MONEY_GATE_MARGIN'in yazılı yuvarlama basamağı (0,00382 → 0,004)


def variance_drift(trades: list[dict], goal: dict, n_boot: int = 2000, seed: int = 42) -> dict:
    """MEASURED_V3'ü canlı defterde YENİDEN ölç ve üç yazılı değişmezi sına.

    `n_boot`/`seed` VARSAYILANLARI MEASURED_V3'ünkiyle AYNI olmak zorundadır (2000/42) — başka bir
    replikasyon sayısıyla ölçüp kayıtlı değerle kıyaslamak, kaymayı yöntem farkıyla karıştırmaktır.

    Dönüş: {"olculdu": bool, "kayma": [ {ad, kayitli, olculen, gerekce} ], "olcum": {...}}.
    `olculdu=False` = defter blok kurulamayacak kadar boş (ÖLÇÜLEMEDİ; kayma YOK demek DEĞİL)."""
    r = variance_attribution(trades, goal, n_boot=n_boot, seed=seed)
    if r is None:
        return {"olculdu": False, "kayma": [], "olcum": None,
                "sebep": "defter blok kurulamayacak kadar küçük/biçimsiz — ölçülemedi (sıfır değil)"}
    kayma: list[dict] = []

    # 1) MARJ ÇEVRİMİ hâlâ aynı sabite mi yuvarlanıyor?
    ms = r.get("margin_scale")
    if ms is None:
        kayma.append({"ad": "margin_scale", "kayitli": MEASURED_V3["margin_scale"], "olculen": None,
                      "gerekce": "σ(S_eski) sıfır çıktı — çevrim ölçülemedi"})
    else:
        yeni_marj = round(0.02 * float(ms), DRIFT_ROUND_NDIGITS)
        if abs(yeni_marj - MONEY_GATE_MARGIN) > 1e-12:
            kayma.append({"ad": "margin_scale", "kayitli": MEASURED_V3["margin_scale"],
                          "olculen": ms, "turetilen_marj": yeni_marj,
                          "yururlukteki_marj": MONEY_GATE_MARGIN,
                          "gerekce": ("0,02 × margin_scale artık MONEY_GATE_MARGIN'e yuvarlanmıyor "
                                      "— para ölçeğindeki taban marj yazılı çevrimden koptu")})

    # 2) DÜŞÜŞ VETOSU hâlâ kendi gürültüsünün dışında mı?
    if not r.get("dd_veto_gurultunun_disinda"):
        kayma.append({"ad": "dd_veto_gurultunun_disinda", "kayitli": MEASURED_V3["sd_dusus"],
                      "olculen": r.get("sd_dusus"), "yururlukteki_marj": DD_VETO_MARGIN,
                      "gerekce": ("σ(düşüş) DD_VETO_MARGIN'i yakaladı — vetonun karar sınırı kendi "
                                  "ölçüm gürültüsünün İÇİNE düştü (yazılı türetim koşulu bozuldu)")})

    # 3) PARA payı hâlâ tek terim mi? (yapısal özdeşlik — skora ikinci bacak sızdıysa kırılır)
    if not r.get("para_payi_tek_terim"):
        kayma.append({"ad": "para_payi_tek_terim", "kayitli": MEASURED_V3["v3_paylar"]["para"],
                      "olculen": (r.get("v3_paylar") or {}).get("para"),
                      "gerekce": ("PARA payı 1,0'ın altına düştü — yasa artık TEK TERİMLİ değil; "
                                  "skora ikinci bir bacak sızmış olabilir")})
    return {"olculdu": True, "kayma": kayma,
            "olcum": {k: r.get(k) for k in ("n_trades", "span_days", "n_valid", "margin_scale",
                                            "ret_scale_k", "sd_dusus", "ort_dusus",
                                            "dd_veto_gurultunun_disinda", "para_payi_tek_terim")},
            "kayitli_ts": MEASURED_V3["ts"], "kayitli_n_trades": MEASURED_V3["n_trades"]}


# ---- YASA GEÇİŞ TABLOSU: "eski yasa ne derdi" --------------------------------------------------
def gecis_satiri(etiket: str, p_v3: float | None, p_eski: float | None,
                 p_required: float, *, mean_v3: float | None = None,
                 mean_eski: float | None = None, note: str = "") -> dict:
    """Bir kapı kaydının İKİ yasa altındaki hükmü — İKİSİ DE ÖLÇÜLMÜŞ, hiçbiri türetilmemiş.

    3b'nin `divergence_row`u TERS ÇEVRİM yapıyordu: kaydedilen p ve mean'den σ'yı geri çıkarıp
    v2 hükmünü MODELLE tahmin ediyordu. v3 için o yol KAPALI ve kapatılması bir dürüstlük
    kararıdır: v2, v1'in tek terimini ölçekleyen bir PERTÜRBASYONdu (ΔS_v2 = ΔS_v1 + w·(k−1)·Δret_c
    — doğrusal, dolayısıyla ters çevrilebilir). v3 ise üç terimden İKİSİNİ ATIYOR; ΔS_v3, ΔS_v1'in
    hiçbir doğrusal dönüşümü değildir ve tek bir bileşik sayıdan ÇIKARILAMAZ. Ters çevrim denemek
    uydurma olurdu. Bu yüzden tablo YALNIZ ÇİFT ÖLÇÜLMÜŞ kayıtları puanlar; ölçülmemiş olan
    `basis="olculemedi"` ile ve EKSİKLİĞİYLE görünür (eksikliğin kendisi bulgudur)."""
    out = {"etiket": etiket, "p_v3": p_v3, "p_eski_yasa": p_eski, "p_required": p_required,
           "mean_delta_v3": mean_v3, "mean_delta_eski_yasa": mean_eski, "note": note}
    if p_v3 is None or p_eski is None:
        out.update({"verdict_v3": None if p_v3 is None else bool(p_v3 >= p_required),
                    "verdict_eski": None if p_eski is None else bool(p_eski >= p_required),
                    "flip": None, "basis": "olculemedi",
                    "note": (note + " | iki yasadan biri ÖLÇÜLMEMİŞ — ters çevrim v3 için "
                                    "TANIMSIZ (üç terimden ikisi atıldı), uydurulmaz").strip(" |")})
        return out
    v3_ok, eski_ok = bool(p_v3 >= p_required), bool(p_eski >= p_required)
    out.update({"verdict_v3": v3_ok, "verdict_eski": eski_ok, "basis": "olculdu_cift_hesap",
                "flip": ("YOK" if v3_ok == eski_ok else ("RET→GEÇER" if v3_ok else "GEÇER→RET"))})
    return out


def divergence_table(limit_hyp: int | None = None) -> dict:
    """İki yasanın hüküm karşılaştırması — geçişin karnesi.

    kaynak 1: `hypotheses.jsonl`ın `backtest` bloğu — `*_p` (v3, KARAR) + `*_eski_yasa` (gölge)
    kaynak 2: `validation_ledger.jsonl` (p/mean taşımıyor — DSR/PBO yolu; eksikliği yazılı)

    GEÇİŞ ÖNCESİ KAYITLAR: `*_eski_yasa` alanı YOKTUR (geçiş 2026-07-30) ve o kayıtların v3 hükmü
    ters çevrimle ÜRETİLEMEZ (bkz. `gecis_satiri`). Tabloda `basis="gecis_oncesi"` ile sayılırlar;
    retro damga yasağı gereği geriye dönük doldurulmaz."""
    from . import store
    rows: list[dict] = []
    onceki = 0
    hyps = store.read_jsonl("hypotheses.jsonl")
    if limit_hyp:
        hyps = hyps[-int(limit_hyp):]
    for h in hyps:
        b = h.get("backtest") or {}
        for pref in ("search", "confirm"):
            p = b.get(f"{pref}_p")
            sh = b.get(f"{pref}_eski_yasa")
            if p is None and not isinstance(sh, dict):
                continue
            if not isinstance(sh, dict):
                onceki += 1
                rows.append({"etiket": f"{h.get('id')} {h.get('variable')} [{pref}]",
                             "p_v3": None, "p_eski_yasa": p, "basis": "gecis_oncesi",
                             "verdict_v3": None, "verdict_eski": None, "flip": None,
                             "note": (f"yasa geçişinden ({YASA_GECIS_TARIHI}) ÖNCE ölçüldü — "
                                      f"kaydın p'si ESKİ yasanın; v3 hükmü ters çevrilemez"),
                             "yasa_surumu": b.get("yasa_surumu")})
                continue
            rows.append(gecis_satiri(
                f"{h.get('id')} {h.get('variable')} {h.get('old')}→{h.get('new')} [{pref}]",
                p, sh.get("p"), float(b.get(f"{pref}_p_required") or 0.8),
                mean_v3=b.get(f"{pref}_mean_delta"), mean_eski=sh.get("mean_delta"),
                note=f"durum={h.get('status')} K={b.get('k_probes')}"))
    vl = [{"etiket": r.get("etiket"), "passes": r.get("passes"), "dsr": r.get("dsr"),
           "n_trials": r.get("n_trials"), "yasa_surumu": r.get("yasa_surumu"),
           "note": "hüküm kıyası YOK — doğrulama defteri p/mean_delta taşımıyor (DSR/PBO yolu)"}
          for r in store.read_jsonl("validation_ledger.jsonl")]
    scored = [r for r in rows if r.get("flip") not in (None,)]
    flips = [r for r in scored if r.get("flip") != "YOK"]
    return {
        "ts": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "yasa_surumu": YASA_SURUMU, "gecis_tarihi": YASA_GECIS_TARIHI,
        "aktif_yasa": YASA_METNI, "golge_yasa": OLD_LAW_METNI,
        "model": ("ÇİFT ÖLÇÜM — iki yasa AYNI blok replikasyonlarında ayrı ayrı hesaplanır. "
                  "Ters çevrim YOK: v3, eski bileşiğin doğrusal dönüşümü değildir."),
        "law_transition": True, "decides": True,
        "gate_records": rows, "validation_ledger": vl,
        "n_scored": len(scored), "n_flip": len(flips), "n_gecis_oncesi": onceki,
        "flips": [r["etiket"] for r in flips],
        "gerekce": WHY_40_UNREACHABLE,
    }


# E raporunun beş adayı — ÖLÇÜM KAYDI (kabul sınavının anlatısı buradan okunur). p/mean_delta
# değerleri KAPI KAYITLARINDAN gelir; kaydı bulunamayan aday için sayı UYDURULMAZ.
E_SIGMA: float = 0.19        # E raporunun canlı defterde ölçtüğü σ(ΔS_eski)

E_REPORT_CANDIDATES: tuple[dict, ...] = (
    {"etiket": "S1 yeni-çekirdek skor (G2)", "p": None, "mean_delta": -0.169, "p_required": 0.90,
     "sigma_declared": E_SIGMA,
     "note": "E raporu: ΔS −0,169 + kuyruk kötü → LİYAKATLE reddedildi (yasa revizyonu bunu "
             "kurtarmamalı — kontrol adayı)"},
    {"etiket": "S2 eski+min_rvol 1.5 (G2)", "p": None, "mean_delta": 0.062, "p_required": 0.90,
     "sigma_declared": E_SIGMA,
     "note": "E raporu: P(ΔS>0) değişkeninde incumbent'tan ortalama +0,062 DAHA İYİ; ret sebebi "
             "ulaşılamaz çıta (K=2'de gereken ΔS≈0,24)"},
    {"etiket": "G3a P1 erken-itlaf paketi", "p": None, "mean_delta": None, "p_required": 0.80,
     "basis": "veri_yok", "note": "prescreen ölçümü; p/mean_delta hypotheses defterinde YOK"},
    {"etiket": "G3a P2 yapı-tabanlı stop", "p": None, "mean_delta": None, "p_required": 0.80,
     "basis": "veri_yok", "note": "prescreen ölçümü; p/mean_delta hypotheses defterinde YOK"},
    {"etiket": "G3a P3 time_stop kalibrasyonu", "p": None, "mean_delta": None, "p_required": 0.80,
     "basis": "veri_yok", "note": "prescreen ölçümü; p/mean_delta hypotheses defterinde YOK"},
)


# ---- CLI (YASA 6 tüketicisi) --------------------------------------------------------------------
def _cli() -> int:
    import argparse
    import json
    from . import config, store
    ap = argparse.ArgumentParser(description="Büyüklük yasası PARA-v3 — tanım, ölçüm, geçiş tablosu")
    ap.add_argument("--olc", action="store_true", help="varyans atamasını canlı defterde ölç")
    ap.add_argument("--iraksama", action="store_true", help="iki yasanın hüküm kıyası tablosu")
    ap.add_argument("--n-boot", type=int, default=2000)
    a = ap.parse_args()
    if a.olc:
        tr = store.read_jsonl("trades.jsonl")
        r = variance_attribution(tr, config.goal(), n_boot=a.n_boot)
        if r is None:
            print("ÖLÇÜLEMEDİ — defter blok kurulamayacak kadar küçük/biçimsiz (sıfır değil).")
            return 1
        print(json.dumps(r, ensure_ascii=False, indent=1))
        print(f"\nPARA payı: eski {r['eski_paylar']['para']:.1%} → v3 "
              f"{r['v3_paylar']['para']:.1%} (tek terim mi: "
              f"{'EVET' if r['para_payi_tek_terim'] else 'HAYIR'})")
        print(f"düşüş vetosu marjı {DD_VETO_MARGIN} vs σ(düşüş) {r['sd_dusus']} — gürültünün "
              f"dışında mı: {'EVET' if r['dd_veto_gurultunun_disinda'] else 'HAYIR'}")
    if a.iraksama:
        t = divergence_table()
        print(json.dumps(t, ensure_ascii=False, indent=1))
        print(f"\nhüküm değişen aday: {t['n_flip']}/{t['n_scored']} "
              f"(geçiş öncesi kayıt: {t['n_gecis_oncesi']})")
    if not (a.olc or a.iraksama):
        ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
