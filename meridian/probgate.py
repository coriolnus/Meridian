"""probgate.py — eşleştirilmiş olasılıksal kapı: nokta-eşik yerine blok-bootstrap ile P(ΔS>0)
ölçer.

Ne yapar: incumbent ve adayı AYNI yeniden-örneklenmiş takvim bloklarında skorlar — ortak
işlemlerin gürültüsü farkta birbirini söndürür, testin gücü noktasal karşılaştırmanın (+0.02
marjı) çok üstüne çıkar. Ölçülmüş bir dersin kurumsallaşması: arama +0.059 gösterip canlıda
−0.036 gerçekleşmişti; kazananın-laneti artık K-sonda cezası ve teyit yürüyüşüyle
(oos_pipeline) yapısal olarak bastırılır. ΔS PARA ölçeğindedir: `shadowlaw.ret_c_v3` farkı,
yalnız para terimi, çarpıtmasız. Eski bileşik skorun varyansının %82'si düşüşten, %17,7'si
Sharpe'tan geliyordu ve ikisi AYNI ANDA ayrı sert vetolarda da sayılıyordu — çift sayım
skordan çıkarıldı; düşüş ve kuyruk `reflect`teki vetolarda güçlenerek durur (tam ölçüm kaydı:
`shadowlaw` modül beyanı). Eski yasanın hükmü gölge alan olarak kayda girer ama karara girmez.

Kilit girişler: `PairedProbabilisticGate` (sınıf — `evaluate` ana ölçüm; `p_required_for`
K-sonda cezasının GERÇEK Bonferroni eşiği; `block_days_for` dinamik blok boyu, medyan tutuş
süresi [5, 21] güne kıstırılır), `GateResult` (dataclass — JSON-güvenli sonuç, `as_gate_fields`
ile kapı kaydına yazılır), `refresh_meta_calibration` (meta-kalibrasyon: öngörülen/gerçekleşen
çiftlerinden `extra_p` türetir — yalnız SIKILAŞTIRIR, gevşeme operatör kararıdır). Eşikler:
P_BASE=0.80 (tek adayda ship alt sınırı), P_CONFIRM=0.70 (teyit dilimi), P_CEIL=0.999.

Değişmezler: bu modül YALNIZCA ölçer — ship kararının sahibi reflect.submit'tir; fold-çoğunluğu
ve kuyruk vetosu orada aynen yürürlüktedir; K arttıkça eşik gerçek Bonferroni ile yükselir;
ölçülemeyen kalibrasyon çifti SAYILMAZ ve `extra_p` yer-tutucuyla doldurulmaz (birim
varsayılmaz, atlanan sayaçta adıyla görünür).

Okur/yazar: gate_calibration.json (meta-kalibrasyon durumu, store üzerinden); uyarıları
events.jsonl'a (obs) düşer."""
from __future__ import annotations
from dataclasses import dataclass, field
import datetime as dt

import numpy as np

from . import score as score_mod

N_BOOT_DEFAULT = 2000
SEED_DEFAULT = 42          # deterministik testler ve tekrarlanabilir kapı kararları için sabit
# EZER: 32 bounds ekseni + 172 modül sabiti + Hermes arama makinesinin TAMAMI — 25d zinciri c-3
# (canlı defter: 52 hipotez → 0 ship; 16 ret doğrudan bu eşikten "P(ΔS>0) < 0.80", 20'si tek
# değerin kara-listesi; ikincil ezilme: aylık kabul kotası ship olmadığı için hiç bağlamadı),
# 2026-08-23
P_BASE = 0.80              # ship için P(ΔS>0) alt sınırı (tek aday)
# Sayısal güvenlik sınırı: p_req tam 1.0 olursa HİÇBİR aday geçemez ve kapı sessizce ölür.
# 0.999, K=200'e kadar gerçek Bonferroni ile aynı; ötesinde "pratikte imkânsız" der.
P_CEIL: float = 0.999
P_CONFIRM = 0.70           # teyit dilimi alt sınırı
BLOCK_MIN_D, BLOCK_MAX_D = 5, 21

# ---- META-KALİBRASYON — kapı kendi iyimserliğini ölçüp kendini SIKILAŞTIRIR ----
# Tek tek her öneri sağlam test edilir, ama aylar içinde biriken önerilerle aile-çapı hata sessizce
# büyür. Panzehir: her ship'in (deflate edilmiş) predicted_delta'sı ile writeback'te ölçülen
# realized_delta'sı karşılaştırılır. Son META_MIN_N ship'te medyan(gerçekleşen/öngörülen) sistematik
# 1'in altındaysa taban eşik OTOMATİK yükselir. Yalnız SIKILAŞTIRIR — asla gevşetmez (gevşeme,
# operatörün bilinçli kararı olmalı). Durum dosyası yoksa davranış birebir eski hal (P_BASE).
META_FILE = "gate_calibration.json"
META_MIN_N = 5             # bunun altında kanıt → ayar yok (gürültüyle eşik oynatılmaz)
META_LOOKBACK = 8          # son bu kadar ölçülmüş ship'e bakılır

# BİLEŞİK OLDUĞU **BİLİNEN** DAMGALAR — BEYAZ LİSTE.
# ESKİSİ: "damga GÜNCEL yasaya EŞİTSE atla" (`_law == shadowlaw.YASA_SURUMU`). O ölçüt yalnız
# BUGÜNKÜ etiket için doğruydu: yasa etiketi bir gün `para_v4` olsaydı, `para_v3` damgalı bütün
# satırlar sessizce yeniden BİLEŞİK gerçekleşmeyle bölünmeye başlardı — birim karışımı, hiçbir test
# kırılmadan, tam olarak kapatıldığı biçimde geri gelirdi (dirilme-hatası sınıfı).
# YENİSİ: ölçüt TERSİNE çevrildi. Sayılabilmek için damganın BİLEŞİK olduğu BİLİNMELİ. Bilinmeyen
# bir damga "herhâlde bileşiktir" diye okunmaz; atlanır ve sayaçta ADIYLA görünür. Yeni bir yasa
# sürümü geldiğinde varsayılan davranış SESSİZ KABUL değil, GÖRÜNÜR RET olur.
#   None                — geçiş öncesi kayıt (damga alanı doğmamıştı) → bileşik
#   "eski_bilesik_marj"  — açıkça eski yasa damgası → bileşik
BILESIK_DAMGALAR: frozenset = frozenset({None, "eski_bilesik_marj"})

# ÜÇ DURUM, ÜÇ FARKLI CÜMLE. `extra_p = 0.0` bugüne kadar ÜÇ ayrı gerçeği aynı sayıyla
# anlatıyordu: "ölçtüm, düzeltme gerekmedi" · "yeterli çift yok" · "çiftler var ama birim borcu
# yüzünden sayılamıyor". Bir bekçi (watchdog.production_report) ilkini sağlık, ikincisini sabır,
# üçüncüsünü ARIZA saymalı — ama üçü de aynı görünüyordu.
DURUM_OLCULDU = "olculdu"                  # n ≥ META_MIN_N → extra_p gerçekten ölçüldü
DURUM_KURAK = "kurak"                      # çift yetersiz ama mekanizma CANLI (atlanan yok)
DURUM_ASKIDA = "askida_olcek_borcu"        # sayılamayan çift VAR — mekanizma askıda, kurak değil


_META_WARNED = False


def _meta_extra_p() -> float:
    """Meta-kalibrasyonun ölçtüğü ek sıkılaştırma ofsetini (`extra_p`) durum dosyasından okur.

    Emniyet olarak [0, +0.10] bandına kıstırılır — ofset yalnız SIKILAŞTIRIR (p_required'ı yükseltir).
    Dosya okunamazsa FAIL-OPEN'dır ve öyle olduğu burada açıkça yazılıdır: ofset tek yönlü bir
    sıkılaştırma olduğu için 0.0 dönmek "düzeltme yok" demektir, yani kapı ölçülmüş iyimserlik
    düzeltmesi olmadan, kalibrasyonsuz hâlinden daha GEVŞEK koşar. Fail-closed seçilmedi çünkü
    okunamayan bir kalibrasyon dosyası tüm adayları reddetmeyi haklı çıkarmaz; bedeli uyarıyla
    görünür kılınır (süreç başına tek uyarı, YASA 4)."""
    from . import store
    global _META_WARNED
    try:
        x = float(store.read_json(META_FILE, {}).get("extra_p", 0.0))
        return min(max(x, 0.0), 0.10)          # emniyet: ayar [0, +0.10] bandında kalır
    except Exception as e:
        # YASA 4: dosya bozuksa/şema kaydıysa ayar SESSİZCE 0'a düşer ve kapı, ölçülmüş
        # iyimserlik düzeltmesi olmadan koşar. Tam olarak "hata değil, miktar değişimi" sınıfı: hiçbir
        # test kırılmaz, yalnız kapı biraz gevşer. Süreç başına BİR kez uyarılır (her aday için değil).
        if not _META_WARNED:
            _META_WARNED = True
            from . import obs
            obs.warn("gate_calibration_unreadable", file=META_FILE, error=f"{type(e).__name__}: {e}")
        return 0.0


def refresh_meta_calibration() -> dict:
    """P5'te her döngü çağrılır. writeback_outcome'un ölçtüğü (predicted, realized) çiftlerinden
    medyan gerçekleşme oranını çıkarır; sistematik iyimserlikte extra_p yazar ve obs'a haber verir.

    ÖLÇEK KARIŞIMI YASAĞI (PARA-v3). Oran `realized/predicted`'dır ve İKİ TARAFIN AYNI
    BİRİMDE olmasına bağlıdır. Yasa geçişinden sonra bu kendiliğinden doğru DEĞİL:
        predicted_delta ← teyit diliminin ΔS'i, artık **PARA** ölçeğinde (`ret_c_v3`)
        realized_delta  ← `rollback`ın canlı/ebeveyn skor farkı, **BİLEŞİK** ölçekte (ve öyle KALIR:
                          geri-alma eşiği o birimde kalibre edildi)
    İkisini bölmek, birimleri farklı iki sayının oranını "gerçekleşme oranı" sanmaktı — "hata değil,
    MİKTAR DEĞİŞİMİ" sınıfı: hiçbir test kırılmaz, hiçbir istisna atılmaz, kapı yalnız YANLIŞ yerde
    sıkışır ya da gevşer. σ(ΔS_v3)/σ(S_eski) ≈ 0,19 olduğundan oran ~5× ŞİŞERDİ.

    PARA İKİZİ MEKANİZMAYI DİRİLTTİ. Önceki çözüm "para damgalı
    çifti ATLA"ydı ve mekanizmayı muhafazakâr değil ÖLÜ yapıyordu: para_v3 altında hiçbir YENİ çift
    sayılamıyor, `n_measured` META_MIN_N'e ulaşamıyor, `extra_p` sonsuza dek 0 kalıyordu — yani
    sistematik iyimserliği cezalandıran emniyet sessizce kapalıydı. Artık `rollback` gerçekleşmenin
    PARA ölçeğindeki ikizini de ölçüp `realized_detail.delta_para`ya yazıyor (hükme GİRMEZ) ve bu
    fonksiyon her satırı KENDİ birimiyle eşleştiriyor:

        damga ∈ BILESIK_DAMGALAR      → bileşik öngörü ÷ BİLEŞİK `realized_delta`
        damga == shadowlaw.YASA_SURUMU → para öngörüsü ÷ PARA `realized_detail.delta_para`
        damga BİLİNMİYOR               → SAYILMAZ (birim varsayılmaz), sayaçta adıyla görünür

    Para ikizi ölçülemeyen satır (like-for-like replay yolu, ebeveyn yedekten geldi, min_sample
    altı) da SAYILMAZ ve `atlama_dagilimi`nda görünür — ölçülemeyen bir sayı sıfır sayılmaz.
    `extra_p` askıda/kurak durumda 0,0 KALIR; yer-tutucu bir ofset, ölçülmemiş bir eşik olurdu."""
    from . import store, obs, shadowlaw
    pairs, atlanan = [], 0
    dagilim = {"para_ikizi_yok": 0, "bilinmeyen_damga": 0}
    for h in store.read_jsonl("hypotheses.jsonl"):
        pd_, rd_ = h.get("predicted_delta"), h.get("realized_delta")
        if pd_ is None or rd_ is None or abs(float(pd_)) < 1e-9 or float(pd_) <= 0:
            continue
        # predicted tarafının yasası: teyit diliminin damgası (yoksa geçiş öncesi = bileşik)
        _law = (h.get("backtest") or {}).get("confirm_yasa_surumu")
        if _law in BILESIK_DAMGALAR:
            pairs.append(float(rd_) / float(pd_))         # bileşik ÷ bileşik
            continue
        if _law != shadowlaw.YASA_SURUMU:
            # BİLİNMEYEN DAMGA: öngörünün birimi BİLİNMİYOR. "Herhâlde paradır" demek, yeni bir
            # yasa sürümünün ilk gününde birim karışımını sessizce geri getirirdi.
            atlanan += 1
            dagilim["bilinmeyen_damga"] += 1
            continue
        _dp = (h.get("realized_detail") or {}).get("delta_para")
        if _dp is None:
            # PARA damgalı ama ikiz ÖLÇÜLEMEMİŞ (geçiş öncesi writeback ya da ölçülemez yol).
            # `realized_delta` ile bölmek tam olarak yasaklanan karışım olurdu.
            atlanan += 1
            dagilim["para_ikizi_yok"] += 1
            continue
        pairs.append(float(_dp) / float(pd_))             # para ÷ para
    pairs = pairs[-META_LOOKBACK:]
    n = len(pairs)
    med = float(np.median(pairs)) if n else None
    extra = 0.0
    if n >= META_MIN_N and med is not None:
        if med < 0.25:                          # öngörülerin dörtte biri bile gerçekleşmiyor
            extra = 0.05
        elif med < 0.5:
            extra = 0.02
    # DURUM: "ölçtüm" · "kanıt birikmedi" · "birim borcu yüzünden sayamıyorum" AYRI cümlelerdir.
    # EZER: (ezen kod değil KANIT KURAKLIĞI — kaynağı c-3'ün ship kapısı) META_MIN_N/META_LOOKBACK
    # meta-ayarı ezilen taraf — 25d zinciri c-7 (canlı: n_measured=1, durum="kurak", extra_p=0.0;
    # kapı kendi eşiğini ayarlayamıyor çünkü ayarlayacak ship kanıtı hiç birikmiyor), 2026-08-23
    durum = (DURUM_OLCULDU if n >= META_MIN_N else (DURUM_ASKIDA if atlanan else DURUM_KURAK))
    prev = store.read_json(META_FILE, {})
    out = {"extra_p": extra, "median_ratio": round(med, 4) if med is not None else None,
           "n_measured": n, "rule": f"son {META_LOOKBACK} ship, medyan<0.25→+0.05, <0.5→+0.02",
           "olcek_karisimi_atlanan": atlanan,
           "atlama_dagilimi": dagilim,
           "durum": durum,
           "durum_beyan": {
               DURUM_OLCULDU: (f"ÖLÇÜLDÜ — {n} çift (≥{META_MIN_N}); extra_p bu medyandan türedi"),
               DURUM_KURAK: (f"KURAK — {n} çift var, eşik {META_MIN_N}. Mekanizma CANLI ve birim "
                             f"borcu yüzünden atlanan satır YOK; eksik olan yalnız kanıt birikimi. "
                             f"extra_p=0,0 'düzeltme gerekmedi' DEĞİL 'henüz ölçülemedi' demektir"),
               DURUM_ASKIDA: (f"ASKIDA — {atlanan} çift birim borcu yüzünden SAYILAMADI "
                              f"({dagilim}). Bu KURAKLIK DEĞİLDİR: çift üretiliyor ama "
                              f"eşleştirilemiyor; extra_p=0,0 bir ölçüm sonucu değil, ölçümün "
                              f"YAPILAMADIĞININ kaydıdır"),
           }[durum],
           "olcek_borcu": ("bu satırlarda öngörü tarafı PARA-v3 ölçeğinde ama gerçekleşmenin para "
                           "ikizi (realized_detail.delta_para) YOK ya da damganın birimi bilinmiyor "
                           "— bileşik `realized_delta` ile bölmek birim karışımı olurdu; "
                           "ikizi rollback._para_ikizi yazar ve ölçülemediğinde nedenini beyan eder"
                           if atlanan else None)}
    store.write_json(META_FILE, out)
    if extra != float(prev.get("extra_p", 0.0)) or durum != prev.get("durum"):
        obs.log("gate_meta_calibration", extra_p=extra, median_ratio=out["median_ratio"], n=n,
                durum=durum, atlanan=atlanan)
    return out


# ---- `p = 0,000` İKİ AYRI GERÇEĞİ AYNI SAYIYLA SÖYLÜYORDU -------------------------------
# `p = float(np.mean(arr > 0))` KESİN eşitsizliktir: aday ebeveynle bit-bit AYNIYSA ΔS her
# replikasyonda tam 0 olur, `arr > 0` hep False, p = 0,000 — yani "aday ebeveynden AYIRT EDİLEMİYOR"
# ile "aday ebeveynden KÖTÜ" tek sayıya çöküyordu. ÖLÇÜLDÜ (defter tam sayımı): `P=0,000` yazan BEŞ satırın DÖRDÜ no-op (H00046/49/50/51, mean_delta = 0,0), yalnız
# biri gerçek felaket (H00031, mean_delta = −0,0921). Dördü de YAPISAL OLARAK ATIL bir düğmeden
# geliyordu (`scale_out_r` frac=0 iken · `early_kill_bars` pivot=0 iken · `entry.w_tight`
# None→0,3 = kodun varsayılanının AYNISI). "Düğme atıl" bir RET değil, kendi başına bir HÜKÜMdür.
#
# EŞİK UYDURULMADI — AYRIM KODUN KENDİ KAYAN-NOKTA GERÇEĞİNDEN TÜRETİLDİ. İki taraf aynı işlem
# listesinden aynı deterministik `score_detail` ile skorlanır; girdiler özdeşse çıktılar BİT-BİT
# özdeştir ve fark tam 0,0 çıkar. Ayrım ölçütü bu yüzden bir tolerans değil, IEEE-754'ün o
# büyüklükte temsil edebildiği EN KÜÇÜK farktır: `np.spacing(max(|si|,|sc|))` (tek ULP). Ölçüldü:
# no-op kurgusunda 600/600 replikasyon `ΔS == 0,0` (ULP ≈ 5,6e−17), felaket kurgusunda 0/600 ve
# medyan |ΔS| = 0,383 — iki sınıf 16 büyüklük mertebesi ayrık, ara bölge YOK. Yani seçilecek bir
# eşik yok; sınır kayan-noktanın kendisi.
#
# `p`nin ANLAMI DEĞİŞMEDİ (tüketiciler var: pano, arming, defter, meta-kalibrasyon): ayrım EK
# alandır ve `passes` hükmüne GİRMEZ. Bir no-op zaten geçemez (p=0 < p_req); değişen tek şey,
# defterin ARTIK ikisini ayrı cümleyle yazması.
AYRIM_AYNI = "ayirt_edilemez"          # replikasyonların TAMAMINDA |ΔS| ≤ 1 ULP → fiilen no-op
AYRIM_KISMEN = "kismen_ayirt_edilemez"  # bir kısmında → düğme yalnız bazı bloklarda iş yapıyor
AYRIM_FARKLI = "ayrisiyor"             # hiçbirinde → gerçek bir davranış farkı ölçüldü


@dataclass
class GateResult:
    """Olasılıksal kapının tek ölçüm sonucu — JSON-güvenli, defter-hazır."""
    passes: bool
    p: float | None                 # P(ΔS>0)
    p_required: float
    mean_delta: float | None        # bootstrap ortalama farkı (kalibrasyon için)
    n_boot: int = 0
    n_valid: int = 0                # her iki tarafın da skorlanabildiği replikasyon sayısı
    block_days: int = BLOCK_MIN_D
    k_probes: int = 1
    law: str = "probabilistic"      # "probabilistic" | "legacy" (fallback sinyali)
    why: str = ""
    # "aday ebeveynden AYIRT EDİLEMİYOR" ile "aday ebeveynden KÖTÜ" AYRI hükümlerdir.
    # None = ölçülemedi (legacy yol / replikasyon yok) — "ayrışıyor" DEĞİL.
    ayrim: str | None = None
    ayrim_n: int | None = None      # |ΔS| ≤ 1 ULP olan replikasyon sayısı
    extra: dict = field(default_factory=dict)

    def as_gate_fields(self, prefix: str) -> dict:
        """Sonucu `prefix` ön ekli düz kapı-kaydı alanlarına çevirir (defter/pano tüketir).

        Payda da yazılır (`n_boot` + `n_valid`): P yalnız ayakta kalan replikasyonlardan
        hesaplanır, okuyucu seçilmiş altkümeyi ayırt edebilmelidir. Gölge yasa alanları
        (`_eski_yasa`, `_yasa_surumu`) yalnız varsa eklenir ve karara GİRMEZ."""
        # n_boot DA yazılır: n_valid tek başına PAYDASIZ bir sayıdır. Skorlanamayan
        # replikasyonlar sessizce düşüyor (evaluate: si/sc None → continue) ve P yalnız AYAKTA KALAN
        # replikasyonlar üzerinden hesaplanıyor. Defterde 1200 görüp bunun 1200/1200 mü yoksa
        # 1200/2000 (=%40 düşmüş, seçilmiş bir altküme) mü olduğunu kimse ayırt edemiyordu —
        # GateResult nesnesinde n_boot vardı ama kapı kaydına HİÇ girmiyordu.
        out = {f"{prefix}_p": self.p, f"{prefix}_p_required": self.p_required,
               f"{prefix}_mean_delta": self.mean_delta, f"{prefix}_n_valid": self.n_valid,
               f"{prefix}_n_boot": self.n_boot,
               f"{prefix}_block_days": self.block_days,
               # AYRIM: `p` alanının anlamı DEĞİŞMEDİ; bu EK alan `p=0,000`ın hangi gerçeği
               # anlattığını söyler. None = ölçülemedi (legacy yol), "ayrisiyor" DEĞİL.
               f"{prefix}_ayrim": self.ayrim, f"{prefix}_ayrim_n": self.ayrim_n}
        if self.extra.get("hist"):
            out[f"{prefix}_hist"] = self.extra["hist"]   # Faz 4: çan eğrisi hipotez kaydında taşınır
        # GÖLGE YASA (PARA-v3, ters gölgeleme): "ESKİ YASA ne derdi" hükmü kapı kaydına GİRER ama
        # kararı VERMEZ. Alan adı bilerek `_eski_yasa` — `_p`/`_passes` ailesinden ayrı kalsın,
        # hiçbir tüketici karıştırmasın. DAMGA (`_yasa_surumu`) her kayda basılır: bir kaydı sonradan
        # okuyan, o p'nin HANGİ yasanın p'si olduğunu tahmin etmek zorunda kalmasın (geçiş öncesi
        # kayıtlarda alan YOKTUR ve yokluğu "eski yasa" demektir — retro damga yasağı).
        if self.extra.get("eski_yasa"):
            out[f"{prefix}_eski_yasa"] = self.extra["eski_yasa"]
        if self.extra.get("yasa_surumu"):
            out[f"{prefix}_yasa_surumu"] = self.extra["yasa_surumu"]
        return out


class PairedProbabilisticGate:
    """Blok-bootstrap fark testi. Bloklar takvim günü pencereleridir (dinamik boy: birleşik kümenin
    medyan tutuş süresi, [5, 21] güne kıstırılır — zaman-serisi bağımlılığı blok içinde korunur).
    min_sample filtresi YALNIZCA bootstrap replikasyonlarının içinde bypass edilir (küçük yeniden-
    örneklemler gücü düşürmesin); dilimin kendisine taban reflect katmanında uygulanır."""

    def __init__(self, goal: dict, n_boot: int = N_BOOT_DEFAULT, seed: int = SEED_DEFAULT):
        """Kapıyı hedef sözleşmesi, replikasyon sayısı ve RNG tohumuyla kurar.

        Tohum sabittir (varsayılan SEED_DEFAULT) — aynı girdi aynı kapı kararını verir."""
        self.goal = goal
        self.n_boot = int(n_boot)
        self.seed = int(seed)

    # ---- yardımcılar ----
    @staticmethod
    def _day(t: dict) -> str:
        """İşlemin açılış gününü ISO tarih önekine (YYYY-MM-DD) indirger; alan yoksa boş dizge."""
        return str(t.get("ts_open", ""))[:10]

    @staticmethod
    def block_days_for(trades: list) -> int:
        """Dinamik blok boyu: medyan tutuş süresi (takvim günü); veri yoksa 5."""
        spans = []
        for t in trades:
            try:
                o = dt.date.fromisoformat(str(t.get("ts_open", ""))[:10])
                c = dt.date.fromisoformat(str(t.get("ts_close", ""))[:10])
                spans.append(max(1, (c - o).days))
            except (ValueError, TypeError):  # sessiz-yutma: ağ/sağlayıcı hatası bu yolun NORMAL hâli; çağıran boş sonuç üzerinden yedek kaynağa düşer ve kaynak seçimi ayrıca kaydedilir
                continue
        if not spans:
            return BLOCK_MIN_D
        return int(min(BLOCK_MAX_D, max(BLOCK_MIN_D, float(np.median(spans)))))

    def _score(self, trades: list, span_days: float) -> float | None:
        """KARAR skoru (PARA-v3), min_sample BYPASS'lı (yalnız bootstrap içi kullanım). Payda
        DİLİMİN takvim uzunluğuyla sabitlenir ki replikasyonlar karşılaştırılabilir kalsın."""
        return self._score_pair(trades, span_days)[0]

    def _score_pair(self, trades: list, span_days: float) -> tuple[float | None, float | None]:
        """(karar_skoru_PARA_v3, gölge_skoru_ESKİ_YASA) — TEK `score_detail` çağrısıyla.

        TERS GÖLGELEME (PARA-v3). Eskiden bu satır tersiydi: karar eski bileşikteydi, v2
        gölgeydi. Artık KARAR yalnız PARA terimindedir (`shadowlaw.ret_c_v3`) ve ESKİ BİLEŞİK
        gölgeye geçmiştir — `score_detail`in DÖNDÜRDÜĞÜ `score` alanı zaten eski yasanın ta
        kendisidir, yani gölge hesap BEDAVAdır (ek çağrı yok, ek üs alma bile yok).

        NEDEN TEK ÇAĞRI: replikasyon başına ikinci bir `score_detail` çağrısı 2000 × 2 taraf = 4000
        fazla tam hesap demek olurdu. İki yasa AYNI çıktıdan türetilir; böylece gölge hüküm, karar
        hükmüyle BİREBİR AYNI replikasyonlar üzerinde okunur (farklı örneklemler kıyaslanamazdı).

        ESKİ YASA KARARA GİRMEZ: dönen ikinci değer yalnız `extra["eski_yasa"]` alanına gider."""
        if not trades:
            return None, None
        g = {**self.goal, "min_sample": 1}
        d = score_mod.score_detail(trades, g, span_days=span_days)
        s_eski = d.get("score")
        if s_eski is None:
            return None, None
        from . import shadowlaw
        # KARAR: yalnız para terimi — dd_c ve sharpe_c bu sayıya GİRMEZ (çift-sayım bitti).
        # YUVARLAMA YOK (bilinçli): karar değişkeni 4 haneye yuvarlanırsa iki tarafın AYNI değere
        # yuvarlandığı replikasyonlar ΔS = 0 üretir ve `p = ort(ΔS > 0)` bu yapay beraberlikleri
        # KAYIP sayar — yani kapı, ölçüm hassasiyeti yüzünden sistematik olarak biraz daha sıkı
        # olurdu. σ(ΔS_v3) ≈ 0,036 olduğundan 1e-4'lük ızgara σ'nın %0,3'ü kadar; küçük ama
        # tek yönlü bir yanlılığı bedavaya almanın sebebi yok. Rapor alanları zaten uçta yuvarlanır.
        return shadowlaw.ret_c_v3(d["total_return"], span_days), s_eski

    @staticmethod
    def p_required_for(k_probes: int, p_base: float = P_BASE) -> float:
        """Aile-bazlı hata kontrolü — GERÇEK Bonferroni.

        ESKİSİ: `min(0.95, p_base + 0.01·(K−1))`. Doğrusal artış 0.95 TAVANINA K=16'da çarpıyordu ve
        ORADA KALIYORDU: K=16 da, K=40 da, K=400 de aynı 0.95'i istiyordu. Ölçüldü — üretim araması
        40 sondaya kadar planlıyor ve 40 NULL adayda (gerçek edge yok) p neredeyse düzgün dağılıyor,
        %5'i 0.95'i geçiyor. Aile-bazlı en az bir yanlış geçiş olasılığı: 1 − 0.95⁴⁰ = **%87**.
        K=100'de %99. Yani "Holm-Bonferroni ruhu" etiketi, fiilen HİÇ düzeltme yapmayan bir formülü
        anlatıyordu. Meta-kalibrasyon ofseti de aynı tavanın altında ölüydü (extra_p 0.00 ile 0.10
        K=40'ta aynı sonucu veriyordu).

        YENİSİ: aile hata bütçesi α_family = 1 − p_base (varsayılan 0.20) K'ya BÖLÜNÜR:
            p_req = 1 − (α_family − meta_ofset) / K
        K=1'de eski davranışa birebir eşit (0.80). K=40'ta 0.995 ister — 40 null adayda beklenen
        yanlış geçiş 40 × 0.005 = 0.2, yani aile bütçesinin tam kendisi. Tavan yok: K büyüdükçe
        eşik büyümeye DEVAM eder, çünkü matematik öyle. `P_CEIL` yalnız sayısal güvenlik sınırıdır
        (p tam 1.0 istenirse hiçbir aday geçemezdi ve kapı sessizce ölü bir kapıya dönerdi)."""
        k = max(1, int(k_probes))
        alpha_family = max(1e-6, (1.0 - p_base) - _meta_extra_p())
        return min(P_CEIL, 1.0 - alpha_family / k)

    # ---- çekirdek ----
    def evaluate(self, inc_trades: list, cand_trades: list, seg_start: str, seg_end: str,
                 k_probes: int = 1, p_base: float = P_BASE) -> GateResult:
        """Ana ölçüm: incumbent ile adayı AYNI yeniden-örneklenmiş takvim bloklarında skorlayıp
        P(ΔS>0)'ı ve K-sonda cezalı gerekli eşiği döndürür.

        Fail-closed: dilim sınırları çözülemez, taraflardan biri boş ya da geçerli replikasyon
        sayısı eşiğin (`max(200, n_boot // 10)` — İKİSİNİN BÜYÜĞÜ) altındaysa `passes=False` + `law="legacy"` ile döner
        — çağıran legacy marj yasasına düşer. Ek olarak ULP tabanlı AYRIM hükmü ("aday ayırt
        edilemiyor" ≠ "aday kötü") ve eski yasanın gölge hükmü kayda basılır; gölge karara GİRMEZ."""
        p_req = self.p_required_for(k_probes, p_base)
        try:
            d0 = dt.date.fromisoformat(seg_start[:10])
            d1 = dt.date.fromisoformat(seg_end[:10])
        except (ValueError, TypeError):  # sessiz-yutma: biçimsiz/eksik tek alan; yalnız bu değer düşer, satır başına uyarı asıl sinyali log seline gömerdi
            return GateResult(False, None, p_req, None, law="legacy",
                              why="dilim sınırları çözülemedi — legacy marj yasasına düş")
        span = max(1, (d1 - d0).days)
        if not inc_trades or not cand_trades:
            return GateResult(False, None, p_req, None, law="legacy",
                              why="işlem dilimi boş — legacy marj yasasına düş")
        union = list(inc_trades) + list(cand_trades)
        bdays = self.block_days_for(union)
        n_blocks = max(2, -(-span // bdays))          # tavan bölme — span'i örten blok sayısı

        # blok -> işlem indeksleri (her iki taraf için önceden kovala; replikasyonlar O(blok) olur)
        def _bucketize(trades):
            """İşlemleri açılış gününe göre `n_blocks` takvim bloğuna kovalar (replikasyon O(blok)
            olsun diye önceden). Tarihi çözülemeyen ya da dilim dışına düşen işlem alınmaz."""
            buckets = [[] for _ in range(n_blocks)]
            for t in trades:
                try:
                    off = (dt.date.fromisoformat(self._day(t)) - d0).days
                except (ValueError, TypeError):  # sessiz-yutma: yardımcı/telemetri yolu; başarısızlığı karara girmez ve çağıran yedek değerle aynen devam eder
                    continue
                if 0 <= off <= span:
                    buckets[min(n_blocks - 1, off // bdays)].append(t)
            return buckets
        b_inc, b_cand = _bucketize(inc_trades), _bucketize(cand_trades)

        rng = np.random.default_rng(self.seed)
        deltas = []
        deltas_eski = []         # ESKİ YASA (gölge) — aynı replikasyonlarda, karara GİRMEZ
        olcekler = []            # replikasyon başına skor BÜYÜKLÜĞÜ — ULP ayrımının paydası
        for _ in range(self.n_boot):
            picks = rng.integers(0, n_blocks, size=n_blocks)
            ri = [t for i in picks for t in b_inc[i]]
            rc = [t for i in picks for t in b_cand[i]]
            si, si_e = self._score_pair(ri, span)
            sc, sc_e = self._score_pair(rc, span)
            if si is None or sc is None:
                continue
            deltas.append(sc - si)
            olcekler.append(max(abs(si), abs(sc)))
            if si_e is not None and sc_e is not None:
                deltas_eski.append(sc_e - si_e)
        n_valid = len(deltas)
        if n_valid < max(200, self.n_boot // 10):
            return GateResult(False, None, p_req, None, n_boot=self.n_boot, n_valid=n_valid,
                              block_days=bdays, k_probes=k_probes, law="legacy",
                              why=f"geçerli replikasyon yetersiz ({n_valid}) — legacy marj yasasına düş")
        arr = np.asarray(deltas, dtype=float)
        p = float(np.mean(arr > 0))
        mean_d = float(np.mean(arr))
        passes = bool(p >= p_req)
        # ---- AYRIM: no-op mu, kayıp mı? (modül başındaki gerekçeye bak) ------------------------
        # `np.spacing(x)` = x'ten bir SONRAKİ temsil edilebilir kayan noktaya olan uzaklık, yani o
        # büyüklükte kodun ifade edebildiği EN KÜÇÜK fark. `|ΔS| ≤ 1 ULP` demek "iki skor ya aynı
        # ya da komşu float" demektir; bundan daha ince bir "aynı" tanımı YOKTUR. Eşik değil, sınır.
        # `np.spacing(0.0)` en küçük normal-altı sayıdır, yani iki taraf da tam 0 ise ayrım DOĞRU
        # biçimde "aynı" der (0 ≤ 5e−324) — sıfır skorlu bir dilim yanlışlıkla "ayrışıyor" olmaz.
        ulp = np.spacing(np.asarray(olcekler, dtype=float))
        n_ayni = int(np.sum(np.abs(arr) <= ulp))
        ayrim = (AYRIM_AYNI if n_ayni == n_valid else
                 AYRIM_KISMEN if n_ayni else AYRIM_FARKLI)
        # GÖLGE HÜKÜM (TERS GÖLGELEME): aynı p_required, ESKİ yasanın bileşik ΔS'iyle. `passes` ile
        # HİÇBİR ilişkisi yoktur — kayda geçer, panoda "eski hüküm" alanı olur ve geçişin
        # SÜREKLİLİĞİNİ sağlar: yeni yasa altında reddedilen/geçen her aday için eski yasanın ne
        # diyeceği ölçülmüş olarak durur, yani iki yasa aynı adaylar üzerinde kıyaslanabilir kalır.
        from . import shadowlaw
        shadow = None
        if len(deltas_eski) >= max(200, self.n_boot // 10):
            a2 = np.asarray(deltas_eski, dtype=float)
            p2 = float(np.mean(a2 > 0))
            shadow = {"p": round(p2, 4), "mean_delta": round(float(np.mean(a2)), 4),
                      "n_valid": len(deltas_eski), "would_pass": bool(p2 >= p_req),
                      "agrees_with_law": bool((p2 >= p_req) == passes),
                      "law": "eski_yasa", "yasa_metni": shadowlaw.OLD_LAW_METNI,
                      "decides": False}
        why = "" if passes else f"P(ΔS>0)={p:.3f} < gerekli {p_req:.2f} (K={k_probes} aday cezası dahil)"
        # NO-OP BİR RET DEĞİL, AYRI BİR HÜKÜMDÜR. Gerekçe dizgesi deftere `reject_reasons`
        # olarak düşüyor; bugüne kadar atıl bir düğme ile zararlı bir aday ORADA da aynı cümleyi
        # alıyordu. "P(ΔS>0)=..." parçası KORUNUR (tüketiciler o dizgeyi arıyor), önüne hükmün
        # kendisi yazılır — ve okuyucu atıl-düğme-ayıklama adayını doğrudan görür.
        if not passes and ayrim == AYRIM_AYNI:
            why = (f"AYIRT EDİLEMEZ: aday ebeveynden ölçülebilir biçimde FARKLI DEĞİL — "
                   f"{n_ayni}/{n_valid} replikasyonda |ΔS| ≤ 1 ULP (bit-bit aynı skor). Bu bir "
                   f"kalite reddi DEĞİL, değişikliğin FİİLEN HİÇBİR ŞEY YAPMADIĞININ ölçümüdür "
                   f"(atıl düğme adayı). {why}")
        elif not passes and ayrim == AYRIM_KISMEN:
            why = (f"KISMEN AYIRT EDİLEMEZ: {n_ayni}/{n_valid} replikasyonda aday ebeveynle "
                   f"bit-bit aynı skoru üretti — düğme yalnız bazı bloklarda iş yapıyor. {why}")
        # Faz 4: 40-kutu histogram — panodaki çan eğrisi + K-ceza eşik çizgisi buradan çizilir.
        # Ham 2000 replikasyonu saklamak şişkinlik olur; histogram deterministik ve yeterli.
        counts, edges = np.histogram(arr, bins=40)
        hist = {"counts": [int(c) for c in counts],
                "lo": round(float(edges[0]), 4), "hi": round(float(edges[-1]), 4),
                "mean": round(mean_d, 4), "p": round(p, 4), "p_required": p_req}
        return GateResult(passes, round(p, 4), p_req, round(mean_d, 4), n_boot=self.n_boot,
                          n_valid=n_valid, block_days=bdays, k_probes=k_probes, law="probabilistic",
                          why=why, ayrim=ayrim, ayrim_n=n_ayni,
                          extra={"delta_p05": round(float(np.percentile(arr, 5)), 4),
                                 "delta_p95": round(float(np.percentile(arr, 95)), 4),
                                 "hist": hist, "eski_yasa": shadow,
                                 "yasa_surumu": shadowlaw.YASA_SURUMU,
                                 # AYRIM ÖLÇÜTÜNÜN KENDİSİ DE KAYDA GİRER: bir kaydı altı ay sonra
                                 # okuyan, "ayirt_edilemez" hükmünün hangi tanımdan çıktığını
                                 # tahmin etmek zorunda kalmasın (eşik yok, ULP var — beyanı da
                                 # burada dursun).
                                 "ayrim_olcut": ("|ΔS| ≤ np.spacing(max(|s_inc|,|s_cand|)) — IEEE-754'ün "
                                                 "o büyüklükte temsil edebildiği TEK ULP; eşik değil sınır"),
                                 "ayrim_p": round(n_ayni / n_valid, 4)})
