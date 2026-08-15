"""validation.py — doğrulama üçlüsü: aday getiri defteri + DSR/PSR + PBO/CSCV ve ship hükümleri.

Kapı "bu aday incumbent'ı geçti mi?" diye sorar; sormadığı soru şudur: **kaç aday denedik de bu
geçti?** Çok sorgulanmış bir pencerede en iyi görüneni seçmek kenar bulmak değil maksimum
seçmektir. ÜÇ PARÇA: (1) ADAY GETİRİ DEFTERİ (`validation_ledger.jsonl`; `record_candidate`/
`ledger`, tavan LEDGER_CAP) — her RESMÎ kapı değerlendirmesinin işlem-getiri serisi kalıcıdır,
PBO'nun ham maddesi; (2) `deflated_sharpe`/`psr`/`expected_max_sharpe` (Bailey & López de Prado)
— Sharpe, deneme sayısına ve çarpıklık/basıklığa göre düzeltilir; ÖLÇER, hüküm vermez;
(3) `pbo_cscv` — "bu SEÇİM YÖNTEMİ in-sample'da en iyiyi seçtiğinde OOS'ta medyanın altına düşme
olasılığı" (aday değil SÜREÇ testi).

SHIP HÜKMÜ TEK YERDE: `dsr_kapi`/`pbo_kapi` saf fonksiyonlardır ve eşikleri (DSR_HARD_MIN,
PBO_HARD_MAX) buradaki sabitlerdir — ship yolu (reflect) ve silahlanma kilit zinciri (health)
AYNI eşiği buradan okur; bir eşiğin iki kopyası, sessizce ayrışan iki kapı demektir. Kural
matrisi: KÂĞIT modunda DSR bloklamaz (yalnız damga: `dsr_dusuk`/`dsr_durum` — kâğıt evrimi ölçüm
aracıdır, öğrenme hızı kanıtsız kısılmaz), PBO ise ÖLÇÜLEBİLİYORSA kâğıtta da SERTTİR;
GERÇEK-PARA bağlamında ikisi de SERT ve FAIL-CLOSED — ölçülemeyen kontrol de RETtir (kanıt yoksa
kapı kapalı). Simetrik kural: UYGULANAMAYAN KONTROL VETO OLAMAZ — taban dolmadan PBO kâğıtta
hükümsüzdür.

UYDURMA YASAĞI her katmanda: taban dolmadan (DSR_MIN_N, PBO_MIN_ADAY) sayı üretilmez, dürüstçe
None/olculemedi döner; deneme-varyansının kaynağı çıktıda beyanlıdır (`varyans_kaynagi`:
deneme_defteri | sifir_beceri_null); iki farklı pencere/parmak izi tek havuzda karıştırılamaz;
geçmiş kayıtlara retro seri üretilmez (defter bugünden sayar); sandbox ölçümleri kendi kopyasına
yazar, resmî defter yalnız resmî değerlendirmeleri görür. Okur/yazar: yalnız
validation_ledger.jsonl (yazım kapıyı asla düşürmez; başarısızlık uyarıyla kayda geçer).
"""
from __future__ import annotations

import itertools
import math
from statistics import NormalDist

from . import obs, store

LEDGER_FILE = "validation_ledger.jsonl"

# Defter tavanı: PBO en fazla son N adaya bakar. Tavan yok denilse defter sonsuza büyür ve PBO
# 2026'nın adayını 2029'un adayıyla aynı ızgaraya oturtmaya çalışırdı — o ızgara artık aynı
# piyasa DEĞİL. 200, C(8,4)=70 kombinasyonun rahatça beslendiği ve bir yılın kapı trafiğini
# (canlı defterde ~40 resmî değerlendirme/ay değil, ~19 kayıt/2 ay) örten bir pencere.
LEDGER_CAP = 200

_NORM = NormalDist()

# Euler-Mascheroni sabiti — Bailey & López de Prado'nun E[max SR] yaklaşımında Gumbel
# (uç-değer) dağılımının konum terimi buradan gelir.
EULER_GAMMA = 0.5772156649015329

# DSR'nin ölçülebilmesi için asgari GÖZLEM sayısı (işlem). PSR'nin payında √(n−1) var; n=5'te bu
# çarpan 2 ve çarpıklık/basıklık tahminleri kendi standart hatalarından küçük olur — yani düzeltme,
# düzelttiğinden fazla gürültü ekler. 20, `score.TAIL_MIN_SAMPLE` (12) ile `goal.min_sample` (30)
# arasında bilinçli bir orta yer: kapı serilerinin çoğu 70-110 işlem taşıyor, 20 yalnız fikstür ve
# çok ince dilimleri eler.
DSR_MIN_N = 20

# Deneme-Sharpe varyansının ÖLÇÜLEBİLMESİ için defterde gereken asgari kayıt. 5'in altında bir
# örneklem varyansı, varyansın kendisinden daha gürültülüdür → null yaklaşımı DAHA dürüsttür
# (bilinen bir varsayım, ölçülmüş gibi sunulan bir gürültüden iyidir).
DSR_TRIAL_VAR_MIN_N = 5

# PBO/CSCV: defterde en az kaç AYRI aday olmalı. CSCV, S bloklu bir ızgarada C(S,S/2) kombinasyon
# üretir ve her kombinasyonda ADAYLAR ARASINDA en iyiyi seçer — 2-3 adayla "en iyinin OOS sırası"
# neredeyse hep 1. veya 2. çıkar, yani ölçüt bilgi taşımaz. 8, önceden yazılmış taban.
PBO_MIN_ADAY = 8

# Zaman ızgarasının kaç bloğa bölüneceği. Bailey ve arkadaşları örneklerinde S=16 kullanır
# (C(16,8)=12.870 kombinasyon); o ızgara en az 16 sütun ister ve blok başına yeterli gözlem
# bırakmak için uzun bir tarih ekseni gerektirir. S=8 → C(8,4)=70 kombinasyon: hesap ucuz kalır,
# bloklar kalın kalır ve defterin ilk dolduğu haftalarda ölçüt fiilen ulaşılabilir olur.
PBO_BLOCKS = 8

# ---- SERT KAPI EŞİKLERİ — TEK YER ----------------------------
# Y1 hard-gate kalemi bu iki sayıdır. Sabit olarak durmaları ŞART: ship yolu ve
# Faz-6 kilit zinciri ikisi de bunları okur ve bir eşiğin iki kopyası, sessizce ayrışan iki kapı
# demektir (`min_sample` dersi birebir aynıydı — olasılıksal yasa kendi tabanını
# icat etmişti). Eşiği DEĞİŞTİRMEK bir operatör kararıdır; iki tüketici de aynı anda değişir.
DSR_HARD_MIN = 0.95            # geçmek için DSR > 0.95 (kesin eşitsizlik: tam 0.95 GEÇMEZ)
PBO_HARD_MAX = 0.20            # geçmek için PBO < %20 (tam %20 GEÇMEZ)


def dsr_kapi(dsr_deger: float | None, live: bool) -> dict:
    """DSR'nin SHIP HÜKMÜ — mod-farkındalıklı. Saf fonksiyon: dosya okumaz, hiçbir şey yazmaz.

    `dsr_deger`: `deflated_sharpe(...)["dsr"]` (None = ÖLÇÜLEMEDİ, 0.0 DEĞİL).
    `live`: gerçek-para bağlamı mı (`config.live_enabled()` — iki elle-set env bayrağı zinciri).

    ÜÇ ÇIKTI ALANI VE NEDEN ÜÇ:
      * `deger`      — sayının kendisi (damga; okuyucu kendi eşiğini uygulayabilsin)
      * `dsr_durum`  — "olculdu" | "olculemedi" (ölçüm VARLIĞI, değeri değil)
      * `dsr_dusuk`  — True/False/**None**. None YALNIZ `dsr_durum == "olculemedi"` iken gelir ve
        bu bilinçlidir: ölçülmemiş bir DSR'ye `False` yazmak "düşük değil" demek olurdu, yani hiç
        yapılmamış bir ölçümün sonucunu uydurmak. Üçüncü hâl UYDURMA YASAĞI'nın alan düzeyindeki
        karşılığıdır ve tüketici (pano) onu "ölçülemedi" diye çizer.

    HÜKÜM: kâğıtta ASLA ret (yalnız damga) · gerçek-parada düşük DSR RET **ve** ölçülemeyen DSR de
    RET (fail-closed)."""
    olculdu = dsr_deger is not None
    dusuk = None if not olculdu else bool(float(dsr_deger) <= DSR_HARD_MIN)
    mod = "gercek_para" if live else "paper"
    if not live:
        return {"esik": DSR_HARD_MIN, "deger": dsr_deger,
                "dsr_durum": "olculdu" if olculdu else "olculemedi", "dsr_dusuk": dusuk,
                "mod": mod, "hukum": "PAPER-ADVISORY — bloklamaz, YALNIZ damga", "ret": False,
                "neden": None,
                "beyan": ("kâğıt evrimi ölçüm aracıdır; ana defterin öğrenme hızı istatistiksel "
                          "bir uyarıyla kısılmaz — uyarı KAYDEDİLİR (dsr_dusuk damgası)")}
    if not olculdu:
        return {"esik": DSR_HARD_MIN, "deger": None, "dsr_durum": "olculemedi", "dsr_dusuk": None,
                "mod": mod, "hukum": "SERT — FAIL-CLOSED", "ret": True,
                "neden": ("gerçek-para bağlamı: DSR ÖLÇÜLEMEDİ (seri DSR_MIN_N altında ya da "
                          "varyansı sıfır) — kanıt yoksa gerçek para kapısı KAPALI"),
                "beyan": "ölçülemeyen kontrolü 'geçti' saymak, yapılmamış bir testi uydurmaktır"}
    return {"esik": DSR_HARD_MIN, "deger": dsr_deger, "dsr_durum": "olculdu", "dsr_dusuk": dusuk,
            "mod": mod, "hukum": "SERT — FAIL-CLOSED", "ret": bool(dusuk),
            "neden": (f"gerçek-para bağlamı: DSR {dsr_deger} <= {DSR_HARD_MIN} — deneme sayısına "
                      f"göre düzeltilmiş Sharpe eşiği geçmiyor" if dusuk else None),
            "beyan": "ölçülemeyen kontrolü 'geçti' saymak, yapılmamış bir testi uydurmaktır"}


def pbo_kapi(pbo: dict | None, live: bool) -> dict:
    """PBO'nun SHIP HÜKMÜ — İKİ MODDA DA SERT (ölçülebilir olduğunda). Saf fonksiyon.

    `pbo`: `pbo_cscv(...)` dönüşü — TEK pencere-ızgarasından hesaplanmış olmalı (havuzlama yasağı;
    çağıranın sorumluluğu, burada doğrulanamaz çünkü bu fonksiyon defteri görmez).

    NEDEN PAPER'DA DA SERT: bu bir ADAY testi değil SÜREÇ testidir. DSR "bu aday şaşırtıcı mı?"
    diye sorar (aday hakkında); PBO "bu SEÇİM YÖNTEMİ, en iyiyi seçtiğinde OOS medyanının altına
    düşüyor mu?" diye sorar (yöntem hakkında). Aşırı-uydurulmuş bir SÜREÇTEN çıkan aday kâğıda bile
    inmemeli: kâğıt defter o adayın kanıtı olarak birikir ve süreç bozuksa biriken şey kanıt değil
    gürültüdür — yani kâğıt gevşekliği ölçüm aracının KENDİSİNİ bozar (DSR'de bozmuyordu).

    UYGULANAMAYAN KONTROL VETO OLAMAZ: taban dolmadan (`durum != "olculdu"`) kâğıtta ret YOKTUR.
    Gerçek-para bağlamında aynı hâl FAIL-CLOSED'dır (ölçülemeyen PBO = RET)."""
    p = pbo or {}
    durum = p.get("durum") or "olculemedi"
    deger = p.get("pbo")
    olculdu = durum == "olculdu" and deger is not None
    kotu = bool(olculdu and float(deger) >= PBO_HARD_MAX)
    mod = "gercek_para" if live else "paper"
    taban = {"esik": PBO_HARD_MAX, "deger": deger, "durum": durum,
             "n_aday": p.get("n_aday"), "min_aday": PBO_MIN_ADAY,
             "n_kombinasyon": p.get("n_kombinasyon"), "olcum_nedeni": p.get("neden"), "mod": mod,
             "hukum": "SERT — iki modda da (ölçülebilir olduğunda)",
             "beyan": ("süreç testi: aşırı-uydurulmuş bir SEÇİM SÜRECİNDEN çıkan aday kâğıda bile "
                       "inmez. Ölçülemezken veto YOK (uygulanamayan kontrol veto olamaz) — ama "
                       "gerçek-para bağlamında ölçülemeyen PBO da RET (fail-closed)")}
    if kotu:
        return {**taban, "ret": True,
                "neden": (f"PBO {deger} >= {PBO_HARD_MAX} ({p.get('n_aday')} aday, "
                          f"{p.get('n_kombinasyon')} kombinasyon) — SEÇİM SÜRECİ aşırı-uydurma "
                          f"eşiğinin üstünde; aday kâğıda bile inmez")}
    if not olculdu and live:
        return {**taban, "ret": True,
                "neden": (f"gerçek-para bağlamı: PBO ÖLÇÜLEMEDİ ({p.get('neden') or 'taban yok'}) "
                          f"— kanıt yoksa gerçek para kapısı KAPALI")}
    return {**taban, "ret": False, "neden": None}


def _isaret(x) -> float | None:
    """Sayıya çevir ya da None. Bir seride tek bozuk hücrenin tüm ölçümü None yapması, bozuk
    hücreyi 0.0 saymaktan daha dürüsttür — ama ölçüm hiç yapılmasın demek de değil: çağıran
    None'ları eler ve elediği sayıyı raporlar."""
    try:
        v = float(x)
    except (TypeError, ValueError):  # sessiz-yutma: dönüş None'ın KENDİSİ cevaptır — çağıran eleme sayısını ayrıca raporlar
        return None
    return None if math.isnan(v) or math.isinf(v) else v


def _moments(xs: list) -> dict | None:
    """Ortalama, örneklem std (ddof=1), çarpıklık ve BASIKLIK (fisher DEĞİL: normalde 3).

    scipy YOK (bilinçli — depo bağımlılığı): momentler elle hesaplanır. `bias=False` düzeltmesi
    UYGULANMAZ ve bu bir tercih değil BEYANDIR: Bailey-López de Prado'nun PSR formülü ham
    (yanlı) momentlerle yazılmıştır; düzeltilmiş momentleri aynı formüle koymak, kaynağın
    kalibrasyonundan sapmak olurdu."""
    v = [x for x in (_isaret(x) for x in xs) if x is not None]
    n = len(v)
    if n < 3:
        return None
    m = sum(v) / n
    var = sum((x - m) ** 2 for x in v) / (n - 1)
    if var <= 0:
        return None
    s = math.sqrt(var)
    g3 = sum((x - m) ** 3 for x in v) / n / s ** 3
    g4 = sum((x - m) ** 4 for x in v) / n / s ** 4
    return {"n": n, "mean": m, "std": s, "skew": g3, "kurtosis": g4, "n_elenen": len(xs) - n}


def expected_max_sharpe(n_trials: int, trial_var: float) -> float | None:
    """N bağımsız denemenin BEKLENEN EN BÜYÜK Sharpe'ı (sıfır gerçek beceri altında).

    E[max SR_n] ≈ √V · [ (1−γ)·Φ⁻¹(1 − 1/N) + γ·Φ⁻¹(1 − 1/(N·e)) ]

    N < 2 → 0.0 DEĞİL None DEĞİL, 0.0: tek deneme yapıldıysa seçilecek bir maksimum yoktur ve
    deflasyon sıfırdır — bu bir ölçüm boşluğu değil, formülün tanımlı sınır hâlidir. (N=1'de
    Φ⁻¹(1−1/1)=Φ⁻¹(0) tanımsızdır; sınır 0'dır.)"""
    if trial_var is None or trial_var < 0:
        return None
    if int(n_trials or 0) < 2:
        return 0.0
    N = float(n_trials)
    try:
        a = _NORM.inv_cdf(1.0 - 1.0 / N)
        b = _NORM.inv_cdf(1.0 - 1.0 / (N * math.e))
    except Exception as e:
        # YASA 4: N çok büyükse 1−1/N kayan noktada 1.0'a yuvarlanır ve inv_cdf tanımsız olur.
        # Sessizce 0 dönmek "deflasyon yok" demek olurdu — yani en çok denenmiş pencerede en
        # gevşek hüküm. Ölçülemedi olarak dışarı verilir.
        obs.warn("dsr_expected_max_undefined", n_trials=int(n_trials or 0),
                 error=f"{type(e).__name__}: {e}",
                 detail="beklenen-maksimum Sharpe hesaplanamadı — DSR ölçülemedi kalır")
        return None
    return math.sqrt(trial_var) * ((1.0 - EULER_GAMMA) * a + EULER_GAMMA * b)


def psr(sharpe: float, n: int, skew: float, kurtosis: float, sharpe_ref: float = 0.0) -> float | None:
    """PROBABILISTIC SHARPE RATIO: P(gerçek SR > sharpe_ref), çarpıklık/basıklık düzeltmeli.

    PSR = Φ[ (SR̂ − SR*)·√(n−1) / √(1 − γ3·SR̂ + ((γ4−1)/4)·SR̂²) ]

    Payda NEDEN ÖNEMLİ: Sharpe tahmincisinin standart hatası normal dağılımda √(1/(n−1))'dir, ama
    NEGATİF çarpıklık ve KALIN kuyruk onu BÜYÜTÜR — yani aynı Sharpe, kuyruklu bir dağılımda daha
    az kanıt taşır. Bu depoda kuyruk gerçek: canlı defterin işlem-getiri basıklığı 3.83 (normal 3)
    ve çarpıklığı −0.26. Düzeltmeyi atlamak, kalın kuyruklu bir seriye normal-dağılım güveni
    yazmak olurdu.

    Payda karekökünün içi ≤ 0 olabilir (aşırı çarpıklık × büyük Sharpe): o hâlde formül tanımsızdır
    ve None döner — küçük bir tabana kıstırmak, tanımsız bir hesaba sayı uydurmak olurdu."""
    if n is None or n < 2:
        return None
    sr = _isaret(sharpe)
    if sr is None:
        return None
    ic = 1.0 - float(skew) * sr + (float(kurtosis) - 1.0) / 4.0 * sr * sr
    if ic <= 0:
        return None
    return _NORM.cdf((sr - float(sharpe_ref)) * math.sqrt(n - 1) / math.sqrt(ic))


def deflated_sharpe(returns: list, n_trials: int, trial_sharpes: list | None = None) -> dict | None:
    """DEFLATED SHARPE RATIO — bir adayın Sharpe'ı, KAÇ DENEMEDEN seçildiğine göre düzeltilir.

    `returns`: adayın gözlem başına getiri serisi (bu depoda işlem başına $ getirisi /
    başlangıç sermayesi — `score.score_detail`in Sharpe'ıyla AYNI tanım, yoksa iki farklı Sharpe
    iki farklı gerçek olurdu). Sharpe burada YILLIKLANDIRILMAZ: PSR/DSR gözlem-başına Sharpe ile
    yazılmıştır ve √(n−1) çarpanı zaten örneklem büyüklüğünü taşır.

    `n_trials`: bu adayın seçildiği deneme sayısı (kapı yolunda: aşınma defteri sorgu sayısı +
    oturum içi k_probes). `trial_sharpes`: varsa GEÇMİŞ adayların Sharpe'ları — deneme-Sharpe
    varyansı onlardan ÖLÇÜLÜR; yoksa null yaklaşımına düşülür (bkz. modül beyanı (3)).

    None: seri DSR_MIN_N (20) gözlemin altındaysa ya da varyansı sıfırsa — ölçülemedi, sıfır değil."""
    mom = _moments(returns or [])
    if not mom or mom["n"] < DSR_MIN_N:
        return None
    sr = mom["mean"] / mom["std"]
    n = mom["n"]
    tv = [x for x in (_isaret(s) for s in (trial_sharpes or [])) if x is not None]
    if len(tv) >= DSR_TRIAL_VAR_MIN_N:
        mt = sum(tv) / len(tv)
        trial_var = sum((x - mt) ** 2 for x in tv) / (len(tv) - 1)
        kaynak = "deneme_defteri"
    else:
        # SIFIR-BECERİ NULL YAKLAŞIMI: Sharpe tahmincisinin örnekleme varyansı ≈ (1 + SR̂²/2)/n
        # (delta yöntemi). Denemelerin gerçek dağılımı ölçülmediği için VARSAYIMDIR ve alan adıyla
        # söylenir. SR̂'yi içine koymak muhafazakâr taraftır: pozitif Sharpe varyansı büyütür,
        # beklenen maksimumu yükseltir, yani çıtayı SERTLEŞTİRİR.
        trial_var = (1.0 + 0.5 * sr * sr) / n
        kaynak = "sifir_beceri_null"
    sr_max = expected_max_sharpe(n_trials, trial_var)
    psr0 = psr(sr, n, mom["skew"], mom["kurtosis"], 0.0)
    dsr = None if sr_max is None else psr(sr, n, mom["skew"], mom["kurtosis"], sr_max)
    return {"dsr": None if dsr is None else round(dsr, 6),
            "psr_sifir": None if psr0 is None else round(psr0, 6),
            "sharpe_gozlem": round(sr, 6), "n": n,
            "skew": round(mom["skew"], 4), "kurtosis": round(mom["kurtosis"], 4),
            "n_trials": int(n_trials or 0),
            "beklenen_maks_sharpe": None if sr_max is None else round(sr_max, 6),
            "deneme_varyansi": round(trial_var, 10), "varyans_kaynagi": kaynak,
            "deneme_sharpe_n": len(tv),
            "yontem": "Bailey & López de Prado (2014) — PSR(E[max SR]); çarpıklık/basıklık düzeltmeli",
            # ROL GÜNCELLENDİ (v130): bu fonksiyon hâlâ yalnız ÖLÇER — `_gate_eval.passes` ona
            # dokunmaz. Ama ölçüm artık bir HÜKMÜN girdisidir ve hükmü `dsr_kapi` verir; "advisory"
            # demeye devam etmek, sertleşmiş bir kapıyı yumuşak göstermek olurdu.
            "rol": ("ÖLÇÜM — kapı `passes` hükmüne girmez; SHIP hükmünü `dsr_kapi` verir "
                    "(paper=damga · gerçek-para=SERT fail-closed)")}


# ---- D1: ADAY GETİRİ DEFTERİ (PBO'nun ham maddesi) --------------------------------------------
def record_candidate(row: dict) -> dict | None:
    """Bir RESMÎ kapı değerlendirmesinin adayını deftere işler. Yazım kapıyı ASLA düşürmez
    (YASA 4: ama sessiz de kalmaz) — bir doğrulama defteri, ship kararını durdurma yetkisine
    sahip değildir.

    Çağıran (`reflect._gate_eval`) yalnız `record_erosion=True` yolunda çağırır: arama döngüsü
    binlerce kez `_gate_eval` çağırıyor ve her çağrıda yazan bir defter "kaç aday değerlendirildi"
    değil "kaç kez fonksiyon çağrıldı" ölçerdi (oos_erosion'ın birebir aynı dersi)."""
    try:
        store.append_jsonl(LEDGER_FILE, row)
        return row
    except Exception as e:
        obs.warn("validation_ledger_write_failed", error=f"{type(e).__name__}: {e}",
                 detail="aday getiri serisi kaydedilemedi — PBO tabanı EKSİK kalır")
        return None


def ledger(limit: int | None = LEDGER_CAP) -> list[dict]:
    """Defterin son `limit` satırı. Ayrı fonksiyon: dosya adı TEK yerde durur."""
    return store.read_jsonl(LEDGER_FILE, limit=limit)


def _matris(rows: list) -> tuple[list, list, list]:
    """Aday serilerini ORTAK TAKVİM IZGARASINA oturt: (tarihler, adaylar, matris[aday][tarih]).

    IZGARA BİRLEŞİMDİR, KESİŞİM DEĞİL: iki aday hiçbir zaman aynı günlerde işlem yapmaz ve
    kesişim alınsa ızgara birkaç güne çökerdi. İşlem yapılmayan gün 0.0'dır — ve bu bir uydurma
    DEĞİL, o günün gerçekleşen getirisidir (pozisyon yoksa getiri sıfırdır). AYNI GÜNDE çok
    işlem varsa R'ler TOPLANIR (o günün toplam getirisi)."""
    seriler = []
    for i, r in enumerate(rows):
        # `etiket` SÖZLEŞMEDE ZORUNLU (ledgers.CONTRACTS) ve BAŞKA BİR ALANA DÜŞÜLMEZ: "iki ad da
        # olabilir" yaması yedi hatadan birinin ta kendisiydi (aynı olgunun iki
        # şeması → yaması olan tüketici çalışır, olmayan satırı sessizce eler). Etiketsiz bir satır
        # PBO'ya YİNE girer (düşürmek bir adayı paydadan sessizce silmek olurdu) ama adı eksikliği
        # SÖYLER — başka bir alandan ad uydurmak sözleşmeyi ikinci bir isimle çoğaltmaktı.
        ad = r.get("etiket") if r.get("etiket") else f"etiketsiz#{i}"
        per: dict = {}
        for cell in (r.get("seri") or []):
            if not isinstance(cell, (list, tuple)) or len(cell) < 2:
                continue
            d, v = str(cell[0])[:10], _isaret(cell[1])
            if d and v is not None:
                per[d] = per.get(d, 0.0) + v
        if per:
            seriler.append((str(ad), per))
    if not seriler:
        return [], [], []
    tarihler = sorted({d for _, per in seriler for d in per})
    adaylar = [ad for ad, _ in seriler]
    mat = [[per.get(d, 0.0) for d in tarihler] for _, per in seriler]
    return tarihler, adaylar, mat


def _sharpe(xs: list) -> float:
    n = len(xs)
    if n < 2:
        return 0.0
    m = sum(xs) / n
    var = sum((x - m) ** 2 for x in xs) / (n - 1)
    return 0.0 if var <= 0 else m / math.sqrt(var)


def pbo_cscv(rows: list | None = None, blocks: int = PBO_BLOCKS) -> dict:
    """PROBABILITY OF BACKTEST OVERFITTING (Bailey, Borwein, López de Prado, Zhu 2015 — CSCV).

    SORDUĞU SORU KAPININ SORDUĞUNDAN FARKLIDIR. Kapı "bu aday geçti mi?" der; PBO **seçim
    yönteminin kendisini** yargılar: "in-sample'da en iyiyi seçtiğimde, out-of-sample'da
    adayların medyanının ALTINA düşme olasılığım nedir?" %50 = yöntem yazı-tura; yazılı
    kapı önerisi <%20.

    YÖNTEM: ortak takvim ızgarası S bloğa bölünür, C(S, S/2) kombinasyonun her birinde bloklar
    yarı in-sample / yarı out-of-sample ayrılır; IS'te Sharpe'ı en yüksek aday seçilir, o adayın
    OOS Sharpe SIRALAMASI bakılır. PBO = OOS sırası medyanın altında kalan kombinasyon oranı.

    OLCULEMEDI ÜÇ HÂLDE (uydurma yasağı — hiçbirinde sayı üretilmez):
      * defterde < PBO_MIN_ADAY (8) aday,
      * ızgara S sütundan kısa (blok başına en az bir gözlem düşmeli),
      * hiçbir kombinasyonda geçerli Sharpe çıkmadı (tüm seriler sabit)."""
    rows = ledger() if rows is None else rows
    tarihler, adaylar, mat = _matris(rows or [])
    taban = {"durum": "olculemedi", "pbo": None, "n_aday": len(adaylar),
             "n_gozlem": len(tarihler), "blocks": blocks,
             "min_aday": PBO_MIN_ADAY,
             "yontem": "CSCV (Bailey/Borwein/López de Prado/Zhu 2015) — blok kombinasyonları",
             "rol": ("ÖLÇÜM — kapı `passes` hükmüne girmez; SHIP hükmünü `pbo_kapi` verir "
                     "(İKİ MODDA DA SERT, ölçülebilir olduğunda)")}
    if len(adaylar) < PBO_MIN_ADAY:
        return {**taban, "neden": f"defterde {len(adaylar)}/{PBO_MIN_ADAY} aday — PBO tabanı dolmadı"}
    if len(tarihler) < blocks:
        return {**taban, "neden": f"ızgara {len(tarihler)} gözlem < {blocks} blok — bölünemez"}
    # Blok sınırları: eşit-sayı kesim (son blok kalanı alır). Takvim değil GÖZLEM sayısı
    # dengelenir — `backtest.balanced_fold_bounds`ın aynı gerekçesi (takvim eşit pencere üretir,
    # piyasa eşit gözlem üretmez).
    kes = [round(i * len(tarihler) / blocks) for i in range(blocks + 1)]
    dilimler = [list(range(kes[i], kes[i + 1])) for i in range(blocks)]
    yarim = blocks // 2
    n_alt, n_toplam, siralar = 0, 0, []
    for combo in itertools.combinations(range(blocks), yarim):
        isx = [i for b in combo for i in dilimler[b]]
        oosx = [i for b in range(blocks) if b not in combo for i in dilimler[b]]
        if len(isx) < 2 or len(oosx) < 2:
            continue
        is_sr = [_sharpe([mat[a][i] for i in isx]) for a in range(len(adaylar))]
        oos_sr = [_sharpe([mat[a][i] for i in oosx]) for a in range(len(adaylar))]
        if all(abs(x) < 1e-12 for x in is_sr):
            continue
        en_iyi = max(range(len(adaylar)), key=lambda a: is_sr[a])
        # OOS GÖRELİ SIRA: kaç aday seçilenden KÖTÜ? (0 = en kötü, 1 = en iyi). Medyan altı =
        # sıra < 0.5. Beraberlikte "kötü" tarafa yazılır (muhafazakâr: overfit iddiasını
        # zayıflatmak değil güçlendirmek gerekir).
        kotu = sum(1 for a in range(len(adaylar)) if a != en_iyi and oos_sr[a] < oos_sr[en_iyi])
        sira = kotu / max(1, len(adaylar) - 1)
        siralar.append(sira)
        n_toplam += 1
        n_alt += 1 if sira < 0.5 else 0
    if not n_toplam:
        return {**taban, "neden": "hiçbir blok kombinasyonunda geçerli Sharpe üretilemedi"}
    return {**taban, "durum": "olculdu", "pbo": round(n_alt / n_toplam, 4),
            "n_kombinasyon": n_toplam,
            "ort_oos_sira": round(sum(siralar) / len(siralar), 4),
            "adaylar": adaylar,
            "neden": None}
