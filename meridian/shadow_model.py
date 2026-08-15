"""shadow_model.py — plan özelliklerinden P(kazanç) tahmin eden, yetkisiz gölge sonuç-modeli.

NE YAPAR. Saf-numpy, rejim-koşullu lojistik regresyon: kapanmış işlemlerden (eğitim setini
büyütmek için karşı-olgusal defterle birlikte) "bu plan kazanır mı?" olasılığını öğrenir.
Üretilen olasılık plana `p_win_shadow` olarak damgalanır ve Adaylar yüzeyine yalnızca KANIT
olarak basılır; canlı Brier'i kalibre olduğunu kanıtlayana kadar model gölgede kalır
(skill-gölgeleme felsefesinin aynısı). scikit-learn bilinçli olarak YOK: küçük örneklemde
basitlik = dürüstlük.

KİLİT GİRİŞLER. `ShadowTradeOutcomeModel` (fit / predict_proba / brier / save / load),
`refit_and_save` (fit denemesinin kendisi — deneme/başarı damgalarını da o atar),
`maybe_refit` (seans-sonrası antrenman kadansı; `dataset_fingerprint` değişmedikçe koşmaz),
`evaluate_promotion` (yazılı terfi kuralı), `training_status` (karne satırı — analytics +
/api/diagnostics okur), `is_promoted`.

YASALAR — GÖLGE KATMANI: SIFIR YETKİ. Kapı kararlarını kesemez/reddedemez, canlı GO/NO_GO'ya
dokunamaz. Tek istisna yazılı terfi kuralıdır: son taze kapanışlarda canlı Brier naif taban-oran
tahmincisini yenerse model 'promoted' olur — o zaman bile tek yetkisi REVIEW eşiğinde vetodur
(REVIEW_VETO_P). Simüle (cf) satırlar YALNIZ eğitime girer; terfi kanıtı tanımı gereği yalnız
gerçek işlemlerden gelir. Ölçülemeyen değer None + neden — uydurma tahmin/sayı yok; eğitim
setinin gerçek/simüle kırılımı (n_real/n_cf) künyeyle yayınlanır.

TARİHÇE (sızıntı dersi): şartname özellik olarak 'r_multiple' diyordu — o GERÇEKLEŞEN sonuçtur
ve etiket (win = r_multiple>0) ondan türetilir; özellik olarak kullanmak modele cevabı göstermek
olurdu. Doğrusu plandaki `r_multiple_expected` ve burada o kullanılır; eski işlem satırları plan
özelliklerini plan_id→trade_plans join'iyle alır, broker yeni kapanışlara özellikleri damgalar.

OKUR: trades.jsonl, trade_plans.jsonl, counterfactuals.jsonl (sieve eleme muhasebesiyle).
YAZAR: yalnız kendi defteri `state/shadow_model.json` (katsayılar + kadans damgaları + terfi)."""
from __future__ import annotations
import datetime as dt
import json

import numpy as np

from . import config, store, obs, sieve

STATE_FILE = "shadow_model.json"

# `_dataset` üç sayıyı birden döndüremiyor (imzası fit() tarafından bağlı), ama "gerçek 0 / simüle 241"
# tam olarak bu kırılımın YAYINLANMAMASI yüzünden görünmezdi. Son veri seti kurulumunun paydası
# burada tutulur ve save() künyeye basar.
_LAST_SPLIT: dict = {"n_real": None, "n_cf": None}
MIN_FIT_N = 40                      # bunun altında model kurulmaz — gürültü ezberi olur
FEATURES_NOTE = "score/100, r_multiple_expected, regime one-hot (VALID_REGIMES)"

# ==================================================================================================
# ANTRENMAN DAMGALARI — İKİ AYRI OLGU, İKİ AYRI DAMGA
# ==================================================================================================
# ÖLÇÜLEN KUSUR (Rol-1, canlı): `scheduler_status.last_learn.antrenman` =
# {fitted: True, n_fit: 2217, brier_train: 0.2428, ts: 2026-08-06T20:13:37} — kadans DÜN KOŞTU VE
# EĞİTTİ. Aynı anda `shadow_model.json` → fit_attempt_ts=None, fit_ts=None, n_fit=2219. Pano da
# (haklı olarak, çünkü damgayı okuyor) kırmızı "HİÇ KOŞMADI" basıyordu. Yani v192'nin teşhisi
# ("kadans gerçekten hiç koşmadı, rozet DOĞRU") ÖLÇÜMLE ÇÜRÜDÜ: kadans koştu, damgası SİLİNDİ.
#
# KÖK NEDEN — `save()` bir ÜSTÜNE-YAZMAYDI. `store.write_json` dosyayı tümüyle değiştirir; `save()`
# ona sıfırdan kurulmuş bir sözlük veriyordu ve o sözlükte dört damganın hiçbiri yoktu. Sıralama:
#     maybe_refit()  → damgaları yazar (fit_attempt_ts, fit_ts, fit_fingerprint)
#     loop.P5_LEARN  → refit_and_save() → save() → DÖRDÜNÜ DE SİLER
# İki n_fit'in farkı (2217 ↔ 2219) bunun doğrudan kanıtıdır: dosyayı EN SON yazan taraf kadans
# değil, iki satır daha görmüş olan P5_LEARN kolu ve o kol damgasızdı.
#
# İKİNCİL ZARAR: silinen `fit_fingerprint` yüzünden `maybe_refit`in "veri_seti_degismedi" kapısı
# HİÇ kapanmıyordu — kadans her seans yeniden fit ediyordu. Damgayı düzeltmek o kapıyı da geri
# açar; bu bir yan etki değil, damganın asıl işlevidir.
#
# SÖZLEŞME:
#   fit_attempt_ts  — HER DENEME. Fit edilsin ya da edilmesin: "veri_seti_degismedi" dalı da,
#                     eşik-altı dalı da, yarıda kalan bir fit de damga bırakır.
#   fit_ts          — YALNIZ BAŞARILI FİT (model kuruldu, katsayı yazıldı).
# İkisi AYRI olgudur ve panoda ayrı okunur: "kadans koştu ama gerek yoktu" ile "model taze" aynı
# cümle değildir, "kadans hiç koşmadı" ile hiç değildir.
_DAMGA_ALANLARI = ("fit_attempt_ts", "fit_ts", "fit_fingerprint", "fit_skip_reason")


def _simdi() -> str:
    """Şu anki UTC zamanını saniye çözünürlüklü ISO-8601 metni olarak verir (damga alanlarının ortak zaman kaynağı)."""
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def _damga_yaz(**alanlar) -> None:
    """Durum defterine OKU-BİRLEŞTİR-YAZ. Tek kapı: damga yazan her yol buradan geçer, yoksa
    `save()`in eski kusuru (üstüne-yazma) başka bir çağrı yolunda yeniden doğar."""
    st = store.read_json(STATE_FILE, {}) or {}
    if not isinstance(st, dict):        # bozuk defter: damga yazımı sessizce YUTULMAZ
        obs.warn("shadow_state_bozuk", tip=type(st).__name__,
                 detail="shadow_model.json sözlük değil — damga taze bir sözlüğe yazıldı")
        st = {}
    store.write_json(STATE_FILE, {**st, **alanlar})


class ShadowTradeOutcomeModel:
    """fit → predict_proba → brier → save/load. Katsayılar + standardizasyon durumu tek JSON'da."""

    def __init__(self):
        """Boş model kurar: katsayı/standardizasyon yok, sayaçlar sıfır. Eğitim seti künyesi (n_real/n_cf)
        fit'e kadar None kalır — kaynak kırılımı asla uydurulmaz."""
        self.w: np.ndarray | None = None
        self.mu: np.ndarray | None = None
        self.sd: np.ndarray | None = None
        self.n_fit = 0
        self.brier_train: float | None = None
        self.n_real: int | None = None      # KÜNYE: eğitim setinin gerçek/simüle kırılımı —
        self.n_cf: int | None = None        # tek bir n_fit yayınlamak "gerçek 0"ı gizlerdi

    # ---- özellik mühendisliği ----
    @staticmethod
    def _plan_index() -> dict:
        """`trade_plans.jsonl`i plan id → plan sözlüğü haritasına çevirir (işlem↔plan birleştirmesi için)."""
        return {p.get("id"): p for p in store.read_jsonl("trade_plans.jsonl")}

    @classmethod
    def _features_of(cls, row: dict, plan: dict | None, sv=None) -> list | None:
        """Tek satırın özellik vektörü. score/rr plan'dan (yoksa satırın kendi damgasından);
        rejim satırdan. Eksik zorunlu özellik → None (satır atlanır — asla uydurma yok).

        `sv`: eleme muhasebesi (sieve.Sieve). Bu `return None` yolu, canlıda "gerçek 0 / simüle 241"i
        üreten SESSİZ elemenin ta kendisiydi: eski şemalı 90 işlemin hiçbirinde `score` yoktu, üçü de
        None döndü ve model gerçek veri görmediğini hiçbir yerde söylemedi. `sv` verilirse her None
        dönüşü SINIFLANDIRILMIŞ bir eleme olarak sayılır. Verilmezse davranış birebir eskisi gibi
        (predict_proba tek bir plan için çağırır — orada muhasebe yapılacak bir akış yoktur)."""
        src = {**(plan or {}), **{k: v for k, v in row.items() if v is not None}}
        score = src.get("score") if src.get("score") is not None else src.get("plan_score")
        rr = src.get("r_multiple_expected") if src.get("r_multiple_expected") is not None else src.get("rr_expected")
        regime = row.get("regime") or src.get("regime_at_plan")
        if score is None:
            if sv is not None:
                sv.drop("sema:eksik_alan:score")
            return None
        if rr is None:
            # takma ad uyuşmazlığı sınıfı: plan `r_multiple_expected`, cf `rr_expected` yazıyordu
            if sv is not None:
                sv.drop("sema:eksik_alan:r_multiple_expected")
            return None
        if regime not in config.VALID_REGIMES:
            if sv is not None:
                sv.drop("sema:rejim_damgasız" if regime in (None, "", "?")
                        else "sema:rejim_bilinmeyen")
            return None
        onehot = [1.0 if regime == r else 0.0 for r in config.VALID_REGIMES]
        return [float(score) / 100.0, float(rr)] + onehot

    @classmethod
    def _dataset(cls) -> tuple[np.ndarray, np.ndarray, int]:
        """Eğitim matrisini (X, y, n) kurar: gerçek işlemler (`trades.jsonl` × plan birleşimi) + karşı-olgusal
        defterin çözülmüş satırları. Etiket `r_multiple > 0`. Her iki aşama AYRI `sieve.Sieve` ile sayılır ve
        gerçek/simüle kırılımı `_LAST_SPLIT`e yazılır — "gerçek 0, simüle 241" gizlenemez."""
        plans = cls._plan_index()
        X, y = [], []
        n_real = 0
        # AYRI AŞAMA (gerçek / cf): tek sayaçta toplansaydı "gerçek 0, simüle 241" hâlâ görünmezdi —
        # toplam çıktı 241>0 olduğu için "hiç çıkmadı" kuralı susardı. Payda ayrı tutulur.
        with sieve.Sieve("shadow_model.gercek") as sv:
            for t in store.read_jsonl("trades.jsonl"):
                plan = plans.get(t.get("plan_id"))
                # plan birleşmediyse KÖK NEDENİ o say: canlıda backtest `P00140` ↔ döngü
                # `P-YYYY-MM-DD-TICKER` çatışması bütün birleştirmeyi düşürmüştü.
                f = cls._features_of(t, plan, sv if plan is not None else None)
                if f is None:
                    if plan is None:
                        sv.drop("sema:plan_join_yok")
                    continue
                if t.get("r_multiple") is None:
                    sv.drop("sema:eksik_alan:r_multiple"); continue
                sv.keep()
                X.append(f)
                y.append(1.0 if float(t["r_multiple"]) > 0 else 0.0)
                n_real += 1
        # öneri #1: karşı-olgusal defter eğitim setini büyütür (90 → binler). Simüle sonuçlar yalnız
        # EĞİTİME girer; terfi kararı (evaluate_promotion) GERÇEK işlemlerdeki canlı çiftlerde kalır —
        # model gerçeklikte kendini kanıtlamadan hiçbir yetki kazanmaz.
        with sieve.Sieve("shadow_model.cf") as sv:
            try:
                from . import counterfactual
                for r in counterfactual.resolved_rows(entered_only=True):
                    f = cls._features_of({"regime": r.get("regime"),
                                          "score": r.get("score"),
                                          "r_multiple_expected": r.get("rr_expected")}, None, sv)
                    if f is None:
                        continue
                    if r.get("r_multiple") is None:
                        sv.drop("sema:eksik_alan:r_multiple"); continue
                    sv.keep()
                    X.append(f)
                    y.append(1.0 if float(r["r_multiple"]) > 0 else 0.0)
            except Exception as e:
                # BULGU: burası `except Exception: pass` idi. cf defteri okunamazsa (bozuk satır,
                # şema kazası, import hatası) model SESSİZCE yalnız gerçek işlemlerle eğitilir ya da
                # MIN_FIT_N altında kalıp hiç kurulmaz — ve nedeni hiçbir yerde yazmaz. Artık hem
                # olay kaydı hem sayılı bir şema elemesi düşüyor.
                obs.warn("shadow_dataset_cf_source_failed", error=f"{type(e).__name__}: {e}")
                sv.drop("sema:kaynak_okunamadı:counterfactual")
        _LAST_SPLIT.update(n_real=n_real, n_cf=len(y) - n_real)
        return np.asarray(X, float), np.asarray(y, float), len(y)

    # ---- çekirdek matematik (saf numpy) ----
    @staticmethod
    def _sigmoid(z):
        """Sayısal taşmaya karşı ±30'a kırpılmış lojistik sigmoid."""
        return 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))

    def fit(self, X: np.ndarray | None = None, y: np.ndarray | None = None,
            iters: int = 600, lr: float = 0.3, l2: float = 1e-2) -> "ShadowTradeOutcomeModel":
        """Lojistik regresyonu tam-batch gradyan inişi + L2 (bias hariç) ile eğitir; `self`i döndürür.
        X/y verilmezse `_dataset()` kullanılır ve kaynak kırılımı künyeye işlenir; dışarıdan matris
        gelirse künye None bırakılır. n < MIN_FIT_N ise model KURULMAZ (olay kaydı düşer, katsayı yazılmaz)."""
        if X is None or y is None:
            X, y, n = self._dataset()
            self.n_real, self.n_cf = _LAST_SPLIT["n_real"], _LAST_SPLIT["n_cf"]
        else:
            self.n_real = self.n_cf = None      # dışarıdan matris geldi — kaynak UYDURULMAZ
        n = len(y)
        if n < MIN_FIT_N:
            obs.log("shadow_model_skip", n=n, min_n=MIN_FIT_N)
            return self
        # standardize sürekli sütunlar (ilk 2); one-hot'lar olduğu gibi
        self.mu = X.mean(axis=0); self.sd = X.std(axis=0)
        self.sd[self.sd == 0] = 1.0
        self.mu[2:] = 0.0; self.sd[2:] = 1.0
        Z = (X - self.mu) / self.sd
        Z = np.hstack([np.ones((n, 1)), Z])                      # bias
        w = np.zeros(Z.shape[1])
        for _ in range(iters):                                    # tam-batch GD + L2 (bias hariç)
            p = self._sigmoid(Z @ w)
            g = Z.T @ (p - y) / n
            g[1:] += l2 * w[1:]
            w -= lr * g
        self.w, self.n_fit = w, n
        self.brier_train = round(float(np.mean((self._sigmoid(Z @ w) - y) ** 2)), 4)
        return self

    def predict_proba(self, plan: dict) -> float | None:
        """Plan-benzeri sözlükten P(kazanç). Model yoksa/özellik eksikse None — asla tahmin uydurmaz."""
        if self.w is None:
            return None
        row = {"regime": plan.get("regime_at_plan") or plan.get("regime")}
        f = self._features_of(row, plan)
        if f is None:
            return None
        z = (np.asarray(f, float) - self.mu) / self.sd
        return round(float(self._sigmoid(np.concatenate([[1.0], z]) @ self.w)), 3)

    @staticmethod
    def brier(pairs: list) -> float | None:
        """[(p, win01), ...] → Brier. Canlı kalibrasyon izleme için."""
        if not pairs:
            return None
        a = np.asarray(pairs, float)
        return round(float(np.mean((a[:, 0] - a[:, 1]) ** 2)), 4)

    # ---- kalıcılık ----
    def save(self) -> None:
        """Model katsayılarını + eğitim künyesini durum defterine OKU-BİRLEŞTİR-YAZ ile kaydeder.
        Model yoksa hiçbir şey yazmaz. Defterin diğer sahibinin alanları (kadans damgaları, `promotion`)
        korunur; kaynak künyesi bu fit'inkiyle bilerek ezilir."""
        if self.w is None:
            return
        # OKU-BİRLEŞTİR-YAZ — ÜSTÜNE-YAZ DEĞİL (yukarıdaki damga sözleşmesi). Eski hâl
        # `write_json`e SIFIRDAN kurulmuş bir sözlük veriyordu; `write_json` tam bir üstüne-yazma
        # olduğu için bu çağrı dört kadans damgasını (`_DAMGA_ALANLARI`) birden siliyordu. Model
        # alanları yine TAM yazılır — korunan yalnız bu defterin DİĞER sahibinin (kadans damgaları
        # + `promotion`) yazdıklarıdır. Kaynak künyesi (`PROV_KEY`) bu fit'inkiyle EZİLİR: onu
        # korumak, yeni bir eğitim setini eski künyeyle etiketlemek olurdu.
        mevcut = store.read_json(STATE_FILE, {}) or {}
        if not isinstance(mevcut, dict):
            obs.warn("shadow_state_bozuk", tip=type(mevcut).__name__,
                     detail="shadow_model.json sözlük değil — model taze bir sözlüğe kaydedildi")
            mevcut = {}
        store.write_json(STATE_FILE, {**mevcut,
            "w": self.w.tolist(), "mu": self.mu.tolist(), "sd": self.sd.tolist(),
            "n_fit": self.n_fit, "brier_train": self.brier_train,
            "features": FEATURES_NOTE, "mode": "shadow",
            "note": "yetkisiz kanıt katmanı — kapı kararlarını değiştirmez",
            # "n_fit=241" tek başına bir yalandı: 241'in kaçı GERÇEK işlemdi? Canlıda sıfırdı.
            sieve.PROV_KEY: (sieve.provenance(self.n_fit, self.n_real, self.n_cf,
                                              stages_=("shadow_model.gercek", "shadow_model.cf"))
                             if self.n_real is not None
                             else sieve.provenance(self.n_fit, source=sieve.SRC_UNKNOWN_INPUT))})

    @classmethod
    def load(cls) -> "ShadowTradeOutcomeModel":
        """Durum defterinden katsayı/standardizasyon/sayaçları okuyup model nesnesi kurar.
        Defter yoksa ya da katsayı boşsa boş (tahmin üretmeyen) model döner."""
        m = cls()
        st = store.read_json(STATE_FILE, None)
        if st and st.get("w"):
            m.w = np.asarray(st["w"], float)
            m.mu = np.asarray(st["mu"], float)
            m.sd = np.asarray(st["sd"], float)
            m.n_fit = st.get("n_fit", 0)
            m.brier_train = st.get("brier_train")
        return m

    # ---- TERFİ KRİTERİ (öneri #3): keyfîlik yok, kural ŞİMDİDEN yazılı ----
    PROMOTE_MIN_N = 30      # en az bu kadar TAZE kapanışta canlı tahmin ölçülmüş olmalı
    REVIEW_VETO_P = 0.35    # terfi SONRASI tek yetki: REVIEW + P(kazanç) < bu → NO_GO (GO/NO_GO'ya asla dokunmaz)

    @classmethod
    def evaluate_promotion(cls) -> dict:
        """Plan anında damgalanan p_win_shadow tahminlerini gerçekleşen sonuçlarla eşler (plan_id join).
        Son PROMOTE_MIN_N taze çiftte yuvarlanan canlı Brier, NAİF taban-oran tahmincisinin Brier'ini
        YENERSE model 'promoted' olur — o zaman bile tek yetkisi REVIEW eşiğinde veto. Yenemezse gölgede
        kalır ve bu da dürüstçe kayda geçer."""
        plans = cls._plan_index()
        pairs = []
        # `plans.get(...) or {}` iki farklı sessiz elemeyi tek satırda birleştiriyordu: plan hiç
        # BİRLEŞMEDİ (şema hatası) ile plan birleşti ama gölge damgası YOK (meşru — model o gün
        # kurulmamıştı). Ayrımı görmeden "n_live=0" hep "henüz veri yok" diye okunuyordu.
        with sieve.Sieve("shadow_model.terfi") as sv:
            for t in store.read_jsonl("trades.jsonl"):
                pid = t.get("plan_id")
                p = plans.get(pid)
                if p is None:
                    sv.drop("sema:eksik_alan:plan_id" if not pid else "sema:plan_join_yok"); continue
                pw = p.get("p_win_shadow")
                if pw is None:
                    sv.drop("piyasa:gölge_tahmini_damgalanmamış"); continue
                if t.get("r_multiple") is None:
                    sv.drop("sema:eksik_alan:r_multiple"); continue
                sv.keep()
                pairs.append((float(pw), 1.0 if float(t["r_multiple"]) > 0 else 0.0))
            if len(pairs) > cls.PROMOTE_MIN_N:
                sv.drop("piyasa:taze_pencere_dışı", n=len(pairs) - cls.PROMOTE_MIN_N, from_kept=True)
        pairs = pairs[-cls.PROMOTE_MIN_N:]
        n = len(pairs)
        live = cls.brier(pairs)
        base_rate = round(sum(y for _, y in pairs) / n, 4) if n else None
        baseline = cls.brier([(base_rate, y) for _, y in pairs]) if n else None
        promoted = bool(n >= cls.PROMOTE_MIN_N and live is not None and baseline is not None
                        and live < baseline)
        return {"n_live": n, "live_brier": live, "baseline_brier": baseline,
                "base_rate": base_rate, "promoted": promoted,
                "rule": f">={cls.PROMOTE_MIN_N} taze çiftte canlı Brier < taban-oran Brier → yalnız "
                        f"REVIEW vetosu (P<{cls.REVIEW_VETO_P})",
                # terfi kanıtı TANIMI GEREĞİ yalnız gerçek işlemlerden gelir — cf buraya asla girmez
                sieve.PROV_KEY: sieve.provenance(n, n, 0, source=sieve.SRC_REAL_ONLY,
                                                 stages_=("shadow_model.terfi",))}

    @classmethod
    def refit_and_save(cls) -> "ShadowTradeOutcomeModel":
        """FİT DENEMESİNİN TA KENDİSİ — ve bu yüzden DAMGAYI ATAN YER BURASI.

        Damga eskiden yalnız `maybe_refit`te yazılıyordu; oysa canlıda fit'i atan iki yol var
        (kadans + `loop.P5_LEARN`) ve ikincisi damgasızdı. Damgayı çağıranın değil FİİLİN yanına
        koymak, üçüncü bir çağıran doğduğunda da damgayı garanti eder — bu tur zaten "damga
        çağırana asılıydı" kusurunun ikinci nüksüdür.

        Deneme damgası fit'ten ÖNCE atılır: fit yarıda kalırsa (bozuk defter, bellek) defterde
        "denendi ama bitmedi" yazar. Sessiz bir yarım fit, hiç denenmemiş gibi okunamaz (YASA 4)."""
        now = _simdi()
        # Parmak izi fit'ten ÖNCE alınır: kaydedilen izin, FİİLEN eğitilen veri setinin izi olması
        # gerekir. Fit bittikten sonra almak, o sırada düşmüş yeni bir satırı "görüldü" saymak olurdu.
        fp = dataset_fingerprint()
        _damga_yaz(fit_attempt_ts=now, fit_skip_reason="fit_basladi_bitmedi")
        m = cls().fit()
        if m.w is not None:
            m.save()
            promo = cls.evaluate_promotion()
            st = store.read_json(STATE_FILE, {})
            was = bool((st.get("promotion") or {}).get("promoted"))
            # BAŞARILI FİT: `fit_ts` AYRICA basılır. `fit_attempt_ts` zaten yukarıda basıldı ve
            # burada aynı ana eşitlenir — ikisinin AYRI alan olması, bir sonraki başarısız
            # denemede `fit_attempt_ts`in ilerleyip `fit_ts`in yerinde kalmasını sağlar.
            store.write_json(STATE_FILE, {**st, "promotion": promo, "fit_ts": now,
                                          "fit_attempt_ts": now, "fit_fingerprint": fp,
                                          "fit_skip_reason": None})
            obs.log("shadow_model_fit", n=m.n_fit, brier_train=m.brier_train,
                    live_brier=promo["live_brier"], promoted=promo["promoted"])
            if promo["promoted"] and not was:
                obs.log("shadow_model_promoted", detail="canlı Brier taban-oranı yendi — REVIEW vetosu aktif")
        else:
            # DENENDİ, KURULAMADI. `fit_ts` DOKUNULMAZ (önceki başarılı fit hâlâ geçerli bir
            # olgudur); ilerleyen tek şey deneme damgası ve atlama nedeni. Parmak izi de
            # yazılmaz — yoksa kurulamamış bir fit veri setini "işlendi" ilan ederdi.
            _damga_yaz(fit_attempt_ts=now, fit_skip_reason=f"esik_alti(min_n={MIN_FIT_N})")
        return m

    @classmethod
    def is_promoted(cls) -> bool:
        """Modelin terfi etmiş olup olmadığını durum defterinden okur (terfi yoksa False)."""
        return bool(store.read_json(STATE_FILE, {}).get("promotion", {}).get("promoted"))


# ==================================================================================================
# OTOMATİK ANTRENMAN KADANSI
# ==================================================================================================
# ÖLÇÜLMÜŞ KUSUR — ve o kusurun GERÇEK adı. `refit_and_save` "hiç çağrılmıyor" DEĞİLDİ: `loop.py`nin
# P5_LEARN bloğu onu her döngüde çağırıyor ve canlı `shadow_model.json` bunun kanıtı (n_fit=2201,
# brier_train=0,2431, 2026-07-29T21:10Z). Kusur bir EKSİK ÇAĞRI değil, bir REHİNELİKTİR:
#
#   `refit_and_save` ⊂ `loop.daily_cycle` ⊂ "yeni seansın barı geldi"
#
# Canlı ölçüm (aynı gün): `scheduler_status.json` → last_summary="noop",
# last_refetch_coverage=0,172, portfolio.last_date=2026-07-28. Yani veri hattı takıldığı GECE
# antrenman da durur — ve durduğu hiçbir yerde YAZMAZ. Model günlerce bayat oturur, kimse görmez.
#
# ÇÖZÜM: antrenmanı bar varışından AYIR. Kadans zamanlayıcının seans-sonrası kancasına taşınır ve
# `daily_cycle` koşsun ya da koşmasın seans başına BİR kez değerlendirilir. Yetki DEĞİŞMEZ — terfi
# kararı hâlâ `evaluate_promotion`ın yazılı kuralıdır ve tek sonucu `shadow_veto`dur.
#
# NEDEN PARMAK İZİ. Fit ucuz ama bedava değil (2.201 satır × 600 iterasyon + üç defterin okunması).
# Daha önemlisi: veri seti DEĞİŞMEDEN yapılan bir fit, defterde "antrenman koştu" diye görünür ve
# "model taze" yanılsaması üretir. Parmak izi kaynak defterlerin (boyut, mtime) demetidir: defter
# değişmediyse veri seti de değişemez — bu bir varsayım değil, dosya sisteminin garantisi.
FIT_SOURCES = ("trades.jsonl", "trade_plans.jsonl", "counterfactuals.jsonl")


def dataset_fingerprint() -> dict:
    """Eğitim setini besleyen defterlerin (boyut, mtime_ns) parmak izi. Okunamayan/olmayan dosya
    `None` olarak GEÇER (0 değil): "dosya yok" ile "dosya boş" ayrı hâllerdir ve ikincisi bir
    seferlik bir kaza, birincisi kalıcı bir kurulum eksiğidir."""
    # DAMGA ARTIK `store.stamp`: iki kaynak defter (`trades.jsonl`,
    # `trade_plans.jsonl`) SQLite'a taşındığında dosyaları `.migrated` ekiyle DONAR — (boyut,
    # mtime) çifti bir daha değişmez ve "veri seti değişmedi" parmak izi SONSUZA kadar taze
    # görünürdü. `store.stamp` iki arka uçta da yalnız İÇERİK değişince değişir.
    from . import store as _st
    out: dict = {}
    for name in FIT_SOURCES:
        s = _st.stamp(name)
        # (0, 0) = defter YOK. `None` olarak geçer (0 değil): "dosya yok" ile "dosya boş" ayrı
        # hâllerdir ve bu ayrım fonksiyonun kendi sözleşmesidir.
        # BEKLENEN TEK SEFERLİK SİNYAL: demetin sırası eskiden [boyut, mtime_ns] idi, şimdi
        # [damga, boyut/rev]. Bu değişiklikten SONRAKİ İLK koşuda parmak izi kaçınılmaz olarak
        # farklı çıkar ve `taze=False` bir kez raporlanır (bir yeniden-fit tetikler). Uydurup
        # eski sırayı taklit etmek, DB arka ucunda anlamsız bir demet üretirdi.
        out[name] = None if s == (0, 0) else list(s)
    return out


def training_status() -> dict:
    """Antrenmanın KARNE satırı (YASA 6 tüketicisi: analytics + /api/diagnostics).

    Ölçülemeyen alan None döner — model hiç kurulmadıysa `n_fit`/`brier` UYDURULMAZ. `taze` üç
    değerlidir: True/False/None ve None "parmak izi hiç yazılmamış" demektir (bu kadans eklenmeden
    önce kurulmuş bir modelde beklenen hâl — geriye-uyumluluk)."""
    st = store.read_json(STATE_FILE, {}) or {}
    promo = st.get("promotion") or {}
    fp_kayit = st.get("fit_fingerprint")
    taze = None if fp_kayit is None else bool(fp_kayit == dataset_fingerprint())
    return {
        "kuruldu": bool(st.get("w")),
        "n_fit": st.get("n_fit"),
        "n_real": (st.get(sieve.PROV_KEY) or {}).get("n_real"),
        "n_cf": (st.get(sieve.PROV_KEY) or {}).get("n_cf"),
        "brier_train": st.get("brier_train"),
        "son_fit_ts": st.get("fit_ts") or (st.get(sieve.PROV_KEY) or {}).get("generated"),
        # DAMGA MI, ÇIKARIM MI? `son_fit_ts` iki kaynaktan gelebiliyor ve ikisi aynı güvende
        # DEĞİL: `fit_ts` fit'in kendi damgasıdır, künyedeki `generated` ise kaydın yazıldığı
        # andır (damga silinmişse tek kalan iz — v207 öncesi canlıda tam olarak bu oluyordu).
        # Kaynağı yazmadan ikisini tek alanda sunmak, çıkarımı damga gibi göstermek olurdu.
        "son_fit_kaynak": ("damga" if st.get("fit_ts")
                           else ("kunye" if (st.get(sieve.PROV_KEY) or {}).get("generated") else None)),
        "son_deneme_ts": st.get("fit_attempt_ts"),
        "son_atlama_nedeni": st.get("fit_skip_reason"),
        "veri_seti_taze": taze,
        "min_fit_n": MIN_FIT_N,
        "terfi": {"promoted": promo.get("promoted"), "n_live": promo.get("n_live"),
                  "live_brier": promo.get("live_brier"), "baseline_brier": promo.get("baseline_brier"),
                  "promote_min_n": ShadowTradeOutcomeModel.PROMOTE_MIN_N,
                  "kural": promo.get("rule")},
    }


def maybe_refit(*, force: bool = False) -> dict:
    """SEANS-SONRASI ANTRENMAN KADANSI — veri seti değiştiyse fit + terfi değerlendirmesi.

    TETİK KOŞULU (üçünden biri yeterli):
      (1) model hiç kurulmamış (`w` yok) — ilk antrenman,
      (2) kaynak defterlerin parmak izi değişmiş — yeni kapanış/karşı-olgusal satır girdi,
      (3) `force=True` — operatörün elle hızlandırması.
    Üçü de yoksa HİÇBİR ŞEY yapılmaz ve nedeni döner; bu bir başarısızlık değil, kadansın
    kendini kısmasıdır.

    BÜTÇE: fit saf-numpy'dir (LLM kotası HARCAMAZ) — bu yüzden ajan bütçesine bağlanmadı. Onun
    bütçesi CPU'dur ve tavanı parmak izidir: veri seti değişmedikçe koşmaz.

    YETKİ: hiçbiri yeni. `refit_and_save` neyi yapıyorsa o yapılır (kaydet + `evaluate_promotion`);
    terfinin tek sonucu bugün de `shadow_veto`dur."""
    now = _simdi()
    fp = dataset_fingerprint()
    st = store.read_json(STATE_FILE, {}) or {}
    kurulu = bool(st.get("w"))
    onceki = st.get("fit_fingerprint")
    if not force and kurulu and onceki == fp:
        # DENEME DAMGASI YİNE YAZILIR: "kadans koştu ama gerek yoktu" ile "kadans hiç koşmadı"
        # ayrı hâllerdir ve karne ikisini ayırt edemezse sessiz bir duruş taze görünür.
        # BU DAL FİT ÇAĞIRMAZ, dolayısıyla damgayı `refit_and_save` atamaz — kadansın kendi
        # damgasını attığı TEK yer burasıdır (diğer iki dal fiilin yanına taşındı).
        _damga_yaz(fit_attempt_ts=now, fit_skip_reason="veri_seti_degismedi")
        return {"fitted": False, "reason": "veri_seti_degismedi", "n_fit": st.get("n_fit"),
                "promoted": (st.get("promotion") or {}).get("promoted"), "ts": now}
    # DAMGALARI ARTIK `refit_and_save` ATAR: fit'i o yapıyor, deneme onun denemesi. Burada
    # ikinci kez yazmak iki `now` arasında sahte bir fark üretir ve — daha kötüsü — damganın
    # KADANSA ait olduğu izlenimini sürdürürdü; oysa canlıdaki kusur tam olarak buydu (fit'i atan
    # ikinci çağıran, `loop.P5_LEARN`, damgasızdı ve `save()` kadansınkini siliyordu).
    m = ShadowTradeOutcomeModel.refit_and_save()
    if m.w is None:
        obs.log("shadow_fit_cadence", fitted=False, reason="esik_alti", min_n=MIN_FIT_N)
        return {"fitted": False, "reason": "esik_alti", "min_fit_n": MIN_FIT_N, "ts": now}
    promo = (store.read_json(STATE_FILE, {}) or {}).get("promotion") or {}
    obs.log("shadow_fit_cadence", fitted=True, n=m.n_fit, brier_train=m.brier_train,
            n_live=promo.get("n_live"), promoted=promo.get("promoted"),
            detail="seans-sonrası antrenman kadansı — bar varışından BAĞIMSIZ koştu")
    return {"fitted": True, "n_fit": m.n_fit, "brier_train": m.brier_train,
            "n_live": promo.get("n_live"), "promoted": promo.get("promoted"), "ts": now}
