"""probgate.py — Eşleştirilmiş Olasılıksal Kapı (karar mekanizması v3, Component 1).

Nokta-eşik (+0.02) yerine BLOK-BOOTSTRAP ile P(ΔS>0): incumbent ve aday, AYNI yeniden-örneklenmiş
takvim bloklarında skorlanır — ortak işlemlerin gürültüsü farkta birbirini söndürür, testin gücü
noktasal karşılaştırmanın çok üstüne çıkar. v2 dersinin kurumsallaşması: arama +0.059 gösterip canlı
−0.036 gerçekleşmişti; kazananın-laneti (winner's curse) artık K-probe cezası ve teyit yürüyüşüyle
(oos_pipeline) yapısal olarak bastırılır.

ΔS ARTIK PARADIR (**PARA-v3**, 2026-07-30 — yasanın yeniden tasarımı). Bu modülün MEKANİZMASI
değişmedi (blok-bootstrap, P(ΔS>0), K-cezası, aşınma marjı, teyit yürüyüşü aynen); değişen tek şey
ΔS'in TANIMIdır:

    ESKİ:  ΔS = bileşik skor farkı  (0,5·ret_c + 0,3·dd_c + 0,2·sharpe_c)
    YENİ:  ΔS = `shadowlaw.ret_c_v3` farkı — YALNIZ para terimi, çarpıtmasız

Gerekçe ÖLÇÜLDÜ (3a E raporu + 3b gölge ölçümü): eski ΔS'in varyansının %82'si düşüş, %17,7'si
Sharpe, %0,3'ü paraydı ve düşüş/Sharpe HEM burada HEM ayrı sert vetolarda sayılıyordu — ÇİFT SAYIM.
Şimdi skorda yalnız para var; düşüş ve kuyruk `reflect`teki vetolarda (biri bu turda EKLENDİ:
düşüş vetosu) GÜÇLENEREK duruyor. Tam gerekçe ve ölçüm kaydı: `shadowlaw` modül beyanı.

Yasa değişmez: bu modül YALNIZCA ölçer; ship kararının sahibi reflect.submit'tir ve fold-çoğunluğu +
kuyruk vetosu aynen yürürlüktedir."""
from __future__ import annotations
from dataclasses import dataclass, field
import datetime as dt

import numpy as np

from . import score as score_mod

N_BOOT_DEFAULT = 2000
SEED_DEFAULT = 42          # deterministik testler ve tekrarlanabilir kapı kararları için sabit
P_BASE = 0.80              # ship için P(ΔS>0) alt sınırı (tek aday)
# Sayısal güvenlik sınırı: p_req tam 1.0 olursa HİÇBİR aday geçemez ve kapı sessizce ölür.
# 0.999, K=200'e kadar gerçek Bonferroni ile aynı; ötesinde "pratikte imkânsız" der.
P_CEIL: float = 0.999
P_CONFIRM = 0.70           # teyit dilimi alt sınırı
BLOCK_MIN_D, BLOCK_MAX_D = 5, 21

# ---- öneri #4: META-KALİBRASYON — kapı kendi iyimserliğini ölçüp kendini SIKILAŞTIRIR ----
# Tek tek her öneri sağlam test edilir, ama aylar içinde biriken önerilerle aile-çapı hata sessizce
# büyür. Panzehir: her ship'in (deflate edilmiş) predicted_delta'sı ile writeback'te ölçülen
# realized_delta'sı karşılaştırılır. Son META_MIN_N ship'te medyan(gerçekleşen/öngörülen) sistematik
# 1'in altındaysa taban eşik OTOMATİK yükselir. Yalnız SIKILAŞTIRIR — asla gevşetmez (gevşeme,
# operatörün bilinçli kararı olmalı). Durum dosyası yoksa davranış birebir eski hal (P_BASE).
META_FILE = "gate_calibration.json"
META_MIN_N = 5             # bunun altında kanıt → ayar yok (gürültüyle eşik oynatılmaz)
META_LOOKBACK = 8          # son bu kadar ölçülmüş ship'e bakılır


_META_WARNED = False


def _meta_extra_p() -> float:
    from . import store
    global _META_WARNED
    try:
        x = float(store.read_json(META_FILE, {}).get("extra_p", 0.0))
        return min(max(x, 0.0), 0.10)          # emniyet: ayar [0, +0.10] bandında kalır
    except Exception as e:
        # YASA 4 (2026-07-21): dosya bozuksa/şema kaydıysa ayar SESSİZCE 0'a düşer ve kapı, ölçülmüş
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

    ÖLÇEK KARIŞIMI YASAĞI (PARA-v3, 2026-07-30 — bu tur eklendi). Oran `realized/predicted`'dır ve
    İKİ TARAFIN AYNI BİRİMDE olmasına bağlıdır. Yasa geçişinden sonra bu artık kendiliğinden doğru
    DEĞİL:
        predicted_delta ← teyit diliminin ΔS'i, artık **PARA** ölçeğinde (`ret_c_v3`)
        realized_delta  ← `rollback`ın canlı/ebeveyn skor farkı, HÂLÂ **BİLEŞİK** ölçekte
    İkisini bölmek, birimleri farklı iki sayının oranını "gerçekleşme oranı" sanmaktı — ve bu tam
    olarak "hata değil, MİKTAR DEĞİŞİMİ" sınıfı: hiçbir test kırılmaz, hiçbir istisna atılmaz, kapı
    yalnız YANLIŞ yerde sıkışır ya da gevşer. σ(ΔS_v3)/σ(S_eski) ≈ 0,19 olduğundan oran sistematik
    olarak ~5× ŞİŞERDİ → sahte bir "öngörüler fazlasıyla gerçekleşiyor" sinyali.
    Bu yüzden çift, YALNIZ predicted tarafı realized tarafıyla AYNI ölçekteyse sayılır. Bugün bu,
    geçiş ÖNCESİ kayıtlar demektir (damgası olmayan/`eski_bilesik_marj` olanlar). Mekanizmanın
    PARA-v3 altında yeniden çalışması için `realized_delta`nın da para ölçeğinde ölçülmesi gerekir —
    AÇIK ÖLÇÜM BORCU olarak çıktıda (`olcek_borcu`) ve ROADMAP'te yazılıdır. Bu arada davranış
    MUHAFAZAKÂR: sayılabilir çift azalır, `extra_p` 0'a düşer, kapı taban çıtada (P_BASE) koşar."""
    from . import store, obs, shadowlaw
    pairs, atlanan = [], 0
    for h in store.read_jsonl("hypotheses.jsonl"):
        pd_, rd_ = h.get("predicted_delta"), h.get("realized_delta")
        if pd_ is None or rd_ is None or abs(float(pd_)) < 1e-9 or float(pd_) <= 0:
            continue
        # predicted tarafının yasası: teyit diliminin damgası (yoksa geçiş öncesi = bileşik)
        _law = (h.get("backtest") or {}).get("confirm_yasa_surumu")
        if _law == shadowlaw.YASA_SURUMU:
            atlanan += 1          # PARA öngörüsü ÷ BİLEŞİK gerçekleşme = birim karışımı → sayılmaz
            continue
        pairs.append(float(rd_) / float(pd_))
    pairs = pairs[-META_LOOKBACK:]
    n = len(pairs)
    med = float(np.median(pairs)) if n else None
    extra = 0.0
    if n >= META_MIN_N and med is not None:
        if med < 0.25:                          # öngörülerin dörtte biri bile gerçekleşmiyor
            extra = 0.05
        elif med < 0.5:
            extra = 0.02
    prev = store.read_json(META_FILE, {})
    out = {"extra_p": extra, "median_ratio": round(med, 4) if med is not None else None,
           "n_measured": n, "rule": f"son {META_LOOKBACK} ship, medyan<0.25→+0.05, <0.5→+0.02",
           "olcek_karisimi_atlanan": atlanan,
           "olcek_borcu": ("realized_delta BİLEŞİK ölçekte ölçülüyor (rollback), predicted_delta ise "
                           "PARA-v3 ölçeğinde — para ölçeğinde öngörüler bu mekanizmaya ANCAK "
                           "realized tarafı da para ölçeğinde ölçüldüğünde girebilir"
                           if atlanan else None)}
    store.write_json(META_FILE, out)
    if extra != float(prev.get("extra_p", 0.0)):
        obs.log("gate_meta_calibration", extra_p=extra, median_ratio=out["median_ratio"], n=n)
    return out


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
    extra: dict = field(default_factory=dict)

    def as_gate_fields(self, prefix: str) -> dict:
        # n_boot DA yazılır (2026-07-22): n_valid tek başına PAYDASIZ bir sayıdır. Skorlanamayan
        # replikasyonlar sessizce düşüyor (evaluate: si/sc None → continue) ve P yalnız AYAKTA KALAN
        # replikasyonlar üzerinden hesaplanıyor. Defterde 1200 görüp bunun 1200/1200 mü yoksa
        # 1200/2000 (=%40 düşmüş, seçilmiş bir altküme) mü olduğunu kimse ayırt edemiyordu —
        # GateResult nesnesinde n_boot vardı ama kapı kaydına HİÇ girmiyordu.
        out = {f"{prefix}_p": self.p, f"{prefix}_p_required": self.p_required,
               f"{prefix}_mean_delta": self.mean_delta, f"{prefix}_n_valid": self.n_valid,
               f"{prefix}_n_boot": self.n_boot,
               f"{prefix}_block_days": self.block_days}
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
        self.goal = goal
        self.n_boot = int(n_boot)
        self.seed = int(seed)

    # ---- yardımcılar ----
    @staticmethod
    def _day(t: dict) -> str:
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

        TERS GÖLGELEME (PARA-v3, 2026-07-30). 3b'de bu satır tersiydi: karar eski bileşikteydi, v2
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
        """Aile-bazlı hata kontrolü — GERÇEK Bonferroni (2026-07-22'de düzeltildi).

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
        for _ in range(self.n_boot):
            picks = rng.integers(0, n_blocks, size=n_blocks)
            ri = [t for i in picks for t in b_inc[i]]
            rc = [t for i in picks for t in b_cand[i]]
            si, si_e = self._score_pair(ri, span)
            sc, sc_e = self._score_pair(rc, span)
            if si is None or sc is None:
                continue
            deltas.append(sc - si)
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
        # Faz 4 (3b): 40-kutu histogram — panodaki çan eğrisi + K-ceza eşik çizgisi buradan çizilir.
        # Ham 2000 replikasyonu saklamak şişkinlik olur; histogram deterministik ve yeterli.
        counts, edges = np.histogram(arr, bins=40)
        hist = {"counts": [int(c) for c in counts],
                "lo": round(float(edges[0]), 4), "hi": round(float(edges[-1]), 4),
                "mean": round(mean_d, 4), "p": round(p, 4), "p_required": p_req}
        return GateResult(passes, round(p, 4), p_req, round(mean_d, 4), n_boot=self.n_boot,
                          n_valid=n_valid, block_days=bdays, k_probes=k_probes, law="probabilistic",
                          why=why, extra={"delta_p05": round(float(np.percentile(arr, 5)), 4),
                                          "delta_p95": round(float(np.percentile(arr, 95)), 4),
                                          "hist": hist, "eski_yasa": shadow,
                                          "yasa_surumu": shadowlaw.YASA_SURUMU})
