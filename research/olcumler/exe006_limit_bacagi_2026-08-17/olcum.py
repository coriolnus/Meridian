"""EXE-2026-006 — limit bacağı hüküm sınaması · ölçüm koşumu.

╔══════════════════════════════════════════════════════════════════════════════════════════╗
║  ⛔ BU BETİK EKSİKTİR — KOŞMA. 2026-08-17'de yarıda bırakıldı, GEREKÇESİYLE.              ║
║                                                                                          ║
║  KUSUR: `hucre_kos` `replay`i `replay(bars, index, start=…, end=…)` diye çağırıyor.       ║
║  GERÇEK imza (`backtest.py:194`):                                                        ║
║      replay(params, bars, index_bars, goal, start, end,                                  ║
║             strategy_version=…, params_by_regime=…, with_gate_detail=…)                  ║
║  Ayrıca referans koşum (`edg032b_tamsatir_2026-08-13/olcum.py:486-493`) `replay`den ÖNCE  ║
║  ÜÇ KANCA takıyor: `brk.max_positions_at` · `backtest.regime_mod.build_regime_json` ·     ║
║  `backtest.strat.scan_entry`. Bu betik hiçbirini takmıyor.                                ║
║                                                                                          ║
║  NEDEN TAHMİNLE TAMAMLANMADI: kartın kill kriteri "şasi kapısı YENİDEN koşulmazsa         ║
║  geçersiz" diyor. Yanlış kurulmuş bir şasi SESSİZCE farklı sonuç üretir; K=8'lik grid'in  ║
║  tamamı geçersiz olur ve bu ancak SEKİZ hücre koştuktan sonra, özdeşlik kapısında         ║
║  görünürdü. Yarım koşum, hiç koşmamaktan pahalıdır.                                       ║
║                                                                                          ║
║  DOĞRU YOL (sonraki tur): bu betik `replay`i YENİDEN KURMAMALI — referans koşumun         ║
║  `kontrol` yolunu YENİDEN KULLANMALI ve tek eklediği şey `yasa_silahli()` yaması ile      ║
║  `MERIDIAN_DINLENEN_LIMIT` bayrağı olmalı. Aşağıdaki `yasa_silahli` ve KOL KİMLİĞİ        ║
║  KAPISI mantığı SAĞLAMDIR ve devralınabilir; `hucre_kos`un replay çağrısı DEĞİLDİR.       ║
║                                                                                          ║
║  Ayrıca: referans dizine yazan her koşum sonrası `git checkout` ile geri yüklenmeli       ║
║  (tamamlanmış ölçümün artefaktı ezilmez — 2026-08-17'de iki kez yaşandı).                 ║
╚══════════════════════════════════════════════════════════════════════════════════════════╝


KART: research/cards/EXE-2026-006-limit-bacagi-hukum-sinamasi.yaml (OKU-DOKUNMA).
Ölçüm ajanı karta DOKUNMAZ; hükmü Rol-1 işler.

NE YAPAR: E1'in limit bacağını ÖLÇÜM KOLUNDA silahlandırıp (canlı yasa onu etkisizleştirmiş)
K=8 hücreyi tarar — 4 tavan × 2 dolum kuralı — ve kartın üç ürününü üretir.

CANLI DOKUNULMAZ (kartın kill kriteri): `state/goal.yaml` DEĞİŞMEZ. Yasa yalnız BU SÜREÇTE,
`broker.entry_law` yamasıyla değiştirilir. Yama ölçüm betiğine aittir; üretim koduna bir "mod
bayrağı" eklenmez — bayrak iki davranışı motora gömer ve hangisinin koştuğu çağrı yığınına
bağlı olurdu (`EXE-2026-005`in aynı gerekçesi).

KOL KİMLİĞİ HER HÜCREDE DAMGALANIR (`BacktestResult.dolum_kurali`): 2026-08-17 incelemesinin
Kritik 1 bulgusu — damgasız bir koşumda "bayrak açıktı ama vaka yoktu" ile "bayrak hiç
uygulanmadı" AYIRT EDİLEMEZ. Bu betik her hücrede damgayı OKUR ve beklenenle KIYASLAR; tutmazsa
hücre ölçüm sayılmaz, koşum DURUR.
"""
import contextlib
import json
import os
import pathlib
import sys

KOK = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(KOK))
BURASI = pathlib.Path(__file__).resolve().parent

TAVANLAR = [0.005, 0.01, 0.02, 0.03]        # kartın parameter_grid'i — DEĞİŞTİRİLEMEZ
DOLUM_KURALLARI = ["yalniz_acilis", "dinlenen_limit"]


@contextlib.contextmanager
def yasa_silahli(cap: float):
    """Limit bacağını `cap` tavanıyla silahlandırır — YALNIZ bu süreçte, yalnız bu blok boyunca.

    `limit_atr_mult` da kod varsayılanına (0.5) çekilir: canlıdaki 100.0 ATR bacağını yapısal
    olarak devre dışı bırakıyor ve o hâlde `cap` tek bağlayıcı olurdu — yani grid'in ATR ekseni
    sessizce ölürdü. Kart bacağı SİLAHLI istiyor, kırpılmış değil."""
    from meridian import broker as B
    asil = B.entry_law
    yeni = {**asil(), "limit_atr_mult": B.ENTRY_LIMIT_ATR_MULT, "limit_pct_cap": cap}
    B.entry_law = lambda *a, **k: yeni
    try:
        yield yeni
    finally:
        B.entry_law = asil


def hucre_kos(cap: float, kural: str, smoke: bool) -> dict:
    """Tek hücre. Dolum kuralı ENV ile seçilir (backtest modül düzeyinde okur) → modül yeniden yüklenir."""
    import importlib
    os.environ["MERIDIAN_DINLENEN_LIMIT"] = "1" if kural == "dinlenen_limit" else "0"
    from meridian import backtest as BT
    importlib.reload(BT)
    if BT.DINLENEN_LIMIT != (kural == "dinlenen_limit"):
        raise AssertionError(f"bayrak kola uymadı: istenen={kural} DINLENEN_LIMIT={BT.DINLENEN_LIMIT}")

    from meridian import dataset
    bars, index = dataset.load_cached()
    bas, bit = ("2022-01-01", "2022-06-30") if smoke else ("2022-01-01", "2026-07-30")
    with yasa_silahli(cap) as yasa:
        res = BT.replay(bars, index, start=bas, end=bit)

    # KOL KİMLİĞİ KAPISI (inceleme Kritik 1): damga beklenene UYMAZSA hücre ölçüm DEĞİLDİR.
    damga = getattr(res, "dolum_kurali", None)
    if damga != kural:
        raise AssertionError(f"KOL KİMLİĞİ TUTMADI: beklenen={kural} damga={damga} — hücre geçersiz")

    rejects = dict(res.entry_rejects or {})
    return {"limit_pct_cap": cap, "dolum_kurali": kural, "dolum_kurali_damgasi": damga,
            "yasa": {k: yasa[k] for k in ("limit_atr_mult", "limit_pct_cap", "version")},
            "pencere": [bas, bit], "islem_n": len(res.trades or []),
            "net_pnl": getattr(res, "net_pnl", None),
            "entry_rejects": rejects,
            "entry_missed_limit": int(rejects.get("entry_missed_limit", 0))}


def main() -> int:
    smoke = "--smoke" in sys.argv
    out, hucreler = [], 0
    for cap in TAVANLAR:
        for kural in DOLUM_KURALLARI:
            h = hucre_kos(cap, kural, smoke)
            hucreler += 1
            out.append(h)
            print(f"  cap={cap:<6} {kural:<15} n={h['islem_n']:<4} "
                  f"missed_limit={h['entry_missed_limit']:<4} pnl={h['net_pnl']}")
    yol = BURASI / (f"sonuc_grid{'_smoke' if smoke else ''}.json")
    json.dump({"kart": "EXE-2026-006", "smoke": smoke, "K_hucre": hucreler, "hucreler": out},
              open(yol, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"yazıldı: {yol} · K={hucreler}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
