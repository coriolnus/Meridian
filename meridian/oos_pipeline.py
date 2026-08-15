"""oos_pipeline.py — OOS penceresinin 70/30 Search/Confirm bölümlemesi ve teyit yürüyüşü.

Ne yapar: Out-of-sample penceresini KRONOLOJİK ikiye böler: Search-OOS (%70) arama adaylarının
yarıştığı dilim, Confirm-OOS (%30) aramanın ASLA dokunmadığı teyit dilimidir. Arama kazananı ne
kadar parlarsa parlasın, teyit diliminde P(ΔS>0) çıtasını veremezse REDDEDİLİR — kazananın-laneti
burada ölür. Deftere yazılan predicted_delta, arama dilimindeki şişkin sayı değil, teyit dilimindeki
sapmasız ortalama farktır (dürüst kalibrasyon).

Kilit girişler: `split_date(oos_start, oos_end)` bölünme tarihi (SEARCH_FRACTION = 0.70, takvim
günü hassasiyetinde); `OutOfSamplePipeline.evaluate_search(inc_wf, cand_wf, k_probes)` arama dilimi
kararı — K aday cezası (probgate.p_required_for) burada uygulanır; `.confirm(inc_wf, cand_wf)` TEK
kazananı, K cezasız ama daha alçak olmayan p_confirm çıtasıyla ve max(10, 0.7·min_sample) taban
örneklemiyle sınar — teyit, ship yetkisinin son kapısıdır ve aramadan gevşek olamaz.

Değişmezler: walk_forward'ın hazır dilimleri (`_trades_search`/`_trades_confirm` + `oos_split`)
üzerinde çalışır, dilimleri kendisi KESMEZ; dilimler yoksa (eski fixture/sandbox) GateResult
law='legacy' döner ve çağıran katman eski marj yasasına güvenle düşer; ince teyit dilimi ship
yetkisi VERMEZ (taban altı → red, gerekçesiyle). Buradaki Confirm-OOS, insana-raporlanan donmuş
HOLDOUT penceresinden AYRI şeydir — o pencere hâlâ hiçbir kararı etkilemez.
Okumaz/yazmaz: saf değerlendirme katmanı; olasılıksal hükmü probgate'e devreder."""
from __future__ import annotations
import datetime as dt

from .probgate import PairedProbabilisticGate, GateResult, P_BASE, P_CONFIRM

SEARCH_FRACTION = 0.70


def split_date(oos_start: str, oos_end: str, frac: float = SEARCH_FRACTION) -> str:
    """Bölünme noktası: OOS_START + frac·(OOS_END − OOS_START), takvim günü hassasiyetinde."""
    d0 = dt.date.fromisoformat(oos_start[:10])
    d1 = dt.date.fromisoformat(oos_end[:10])
    return (d0 + dt.timedelta(days=int(round((d1 - d0).days * frac)))).isoformat()


class OutOfSamplePipeline:
    """walk_forward çıktılarındaki hazır dilimler (_trades_search/_trades_confirm + oos_split)
    üzerinde olasılıksal kapıyı işletir. Dilimler yoksa (eski fixture/sandbox) GateResult
    law='legacy' döner ve çağıran katman eski marj yasasına güvenle düşer."""

    def __init__(self, goal: dict, p_base: float = P_BASE, p_confirm: float = P_CONFIRM,
                 n_boot: int = 2000, seed: int = 42):
        """Kapıyı hedef sözleşmesi ve olasılık eşikleriyle kurar; eşleştirilmiş olasılıksal kapı nesnesini
        (bootstrap sayısı + tohumla, yani deterministik) hazırlar."""
        self.goal = goal
        self.p_base = p_base
        self.p_confirm = p_confirm
        self.gate = PairedProbabilisticGate(goal, n_boot=n_boot, seed=seed)

    @staticmethod
    def has_slices(wf: dict) -> bool:
        """Walk-forward çıktısı kapının okuyabileceği dilimleri (oos_split + arama/teyit işlem listeleri)
        taşıyor mu? Taşımıyorsa çağıran legacy yasaya düşer."""
        return isinstance(wf, dict) and isinstance(wf.get("oos_split"), dict) \
            and "_trades_search" in wf and "_trades_confirm" in wf

    def evaluate_search(self, inc_wf: dict, cand_wf: dict, k_probes: int = 1) -> GateResult:
        """Arama dilimi kararı — K aday cezası burada uygulanır."""
        if not (self.has_slices(inc_wf) and self.has_slices(cand_wf)):
            return GateResult(False, None, PairedProbabilisticGate.p_required_for(k_probes, self.p_base),
                              None, k_probes=k_probes, law="legacy", why="dilimler yok — legacy yasa")
        sp = cand_wf["oos_split"]
        return self.gate.evaluate(inc_wf["_trades_search"], cand_wf["_trades_search"],
                                  sp["search_start"], sp["search_end"],
                                  k_probes=k_probes, p_base=self.p_base)

    def confirm(self, inc_wf: dict, cand_wf: dict) -> GateResult:
        """Teyit yürüyüşü — TEK kazanan aday, dokunulmamış %30 dilimde, K cezasız ama daha alçak
        olmayan bir dürüstlük çıtasıyla (p_confirm) sınanır."""
        if not (self.has_slices(inc_wf) and self.has_slices(cand_wf)):
            return GateResult(False, None, self.p_confirm, None, law="legacy",
                              why="teyit dilimi yok — legacy yasa")
        sp = cand_wf["oos_split"]
        # TABAN ÖRNEKLEM: arama diliminin tabanı vardı
        # (`max(10, 0.7·min_sample)`), teyit yürüyüşünün HİÇ YOKTU. Bootstrap'ın iç `min_sample: 1`
        # baypası bunu erişilebilir kılıyordu: taraf başına 6 işlemle kapı `passes=True, p=0.886`
        # diyordu — ve o 6 işlemden türeyen `predicted_delta` deftere "yansız" diye yazılıyordu.
        # Teyit, ship yetkisinin SON kapısı; arama diliminden daha gevşek olamaz.
        _floor = max(10, int(0.7 * int(self.goal.get("min_sample", 30))))
        _n = min(len(inc_wf["_trades_confirm"]), len(cand_wf["_trades_confirm"]))
        if _n < _floor:
            return GateResult(False, None, self.p_confirm, None, law="legacy",
                              why=f"teyit dilimi ince ({_n} < {_floor} işlem) — ship yetkisi "
                                  f"bu kanıtla verilemez")
        return self.gate.evaluate(inc_wf["_trades_confirm"], cand_wf["_trades_confirm"],
                                  sp["confirm_start"], sp["confirm_end"],
                                  k_probes=1, p_base=self.p_confirm)
