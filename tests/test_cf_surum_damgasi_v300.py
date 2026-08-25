"""KARŞI-OLGUSAL SATIRDA SÜRÜM DAMGASI · v300 (2026-08-25)

OPERATÖR SORUSU: "sistem son seed'den beri çok gelişti, yeniden bütün planları
değerlendirmek gerekmez mi?" — ve o soru DEFTERDEN CEVAPLANAMIYORDU. Ölçüldü (canlı,
2026-08-25): `counterfactuals.jsonl` 7260 satır, **7260'ında `strategy_version: None`**.
Yani hangi kanıtın hangi strateji sürümüyle üretildiği hiçbir yerde yazmıyor.

BEDELİ SOMUT. Aynı defterde:
    breakout_vcp       n=6079   2022-01-03 → 2026-08-13   (tarih yürütülmüş)
    exhaustion_hammer  n=  15   2026-07-27 → 2026-08-14   (2026-08-11'de SİLAHLANDI)
    episodic_pivot     n=   2   2026-07-21 → 2026-07-30
Fark yetenek farkı değil, geri dolumun O KURULUMLAR VARKEN KOŞULMAMIŞ olması. Damga
olmadan bu ayrım yalnız tarih aralığına bakan bir insan sezgisiyle kuruluyor.

`cf_backfill.run()` sürümü ZATEN OKUYOR (`version = int(strat_cfg.get("version", 1))`)
ama satıra basmıyordu — bilgi elde, bir adım ötede kayboluyordu.

YASA 6: damga bir OKUYUCUYLA birlikte gelir. Okuyucu `counterfactual.surum_dokumu()` —
defterin sürüm kırılımı; "kanıt bugünün stratejisini mi yansıtıyor" sorusunun cevabı.
"""
from __future__ import annotations

from meridian import counterfactual as cf
from meridian import store


def test_collect_SURUM_damgasi_basiyor(sandbox_state):
    plan = {"id": "P-2026-08-25-AAA", "ticker": "AAA", "setup": "breakout_vcp", "score": 80,
            "entry_trigger": 10.0, "stop": 9.0, "profit_target": 12.0,
            "r_multiple_expected": 2.0}
    cf.collect("2026-08-25", [plan], set(), [], 15, regime="trend_up", strategy_version=5)
    satirlar = store.read_json(cf.OPEN_FILE, [])
    assert satirlar, "satır açılmadı — fikstür bozuk"
    assert satirlar[0].get("strategy_version") == 5, (
        f"satır sürüm damgası taşımıyor: {satirlar[0].get('strategy_version')!r}")


def test_surum_OLCULEMEDIYSE_None_ve_uydurulmuyor(sandbox_state):
    """Sürüm verilmediyse damga `None` olur — 1 varsayıp yazmak UYDURMA olurdu."""
    plan = {"id": "P-2026-08-25-BBB", "ticker": "BBB", "setup": "breakout_vcp", "score": 80,
            "entry_trigger": 10.0, "stop": 9.0, "profit_target": 12.0,
            "r_multiple_expected": 2.0}
    cf.collect("2026-08-25", [plan], set(), [], 15, regime="chop")
    s = store.read_json(cf.OPEN_FILE, [])[0]
    assert "strategy_version" in s, "alan hiç yok — okuyucu 'ölçülemedi' ile 'alan yok'u ayırt edemez"
    assert s["strategy_version"] is None, f"sürüm uydurulmuş: {s['strategy_version']!r}"


def test_OKUYUCU_var_surum_dokumu(sandbox_state):
    """YASA 6: okuyucusuz damga yazılmaz. Döküm, operatörün asıl sorusunu cevaplar."""
    for i, (sym, sur) in enumerate((("AAA", 5), ("BBB", 5), ("CCC", 3), ("DDD", None))):
        cf.collect(f"2026-08-{10+i:02d}", [{"id": f"P-{sym}", "ticker": sym,
                                            "setup": "breakout_vcp", "score": 80,
                                            "entry_trigger": 10.0, "stop": 9.0,
                                            "profit_target": 12.0, "r_multiple_expected": 2.0}],
                   set(), [], 15, regime="trend_up", strategy_version=sur)
    d = cf.surum_dokumu()
    assert d["dokum"].get("5") == 2 and d["dokum"].get("3") == 1, f"döküm yanlış: {d}"
    assert d["damgasiz"] == 1, f"damgasız satır sayılmıyor: {d}"
    assert d["n"] == 4, f"toplam yanlış: {d}"


def test_damga_COZULUNCE_de_yasiyor(sandbox_state):
    """DAMGA YAŞAM DÖNGÜSÜNÜN TAMAMINDA DURMALI — sonda bunu ölçtü ve İLK sürüm DÜŞTÜ.

    `_resolve` alanları AÇIK BİR İZİN LİSTESİNDEN kopyalıyor (doğru tasarım) ve
    `strategy_version` o listede yoktu: damga açık satırda vardı, çözülünce KAYBOLUYORDU.
    Kum havuzu sondası bunu sayıyla gösterdi — açık 106 satır damgalı, çözülmüş 282 satır
    damgasız. Çivinin ilk sürümü yalnız `collect`i sınadığı için görmedi.

    ÖNEMİ: ölçümlerin ÇOĞU çözülmüş satırları okur (`resolved_rows`). Damga yalnız açık
    satırda yaşasaydı, `surum_dokumu()` defterin tazeliğini SÜREKLİ olduğundan kötü
    gösterirdi ve "kanıt bugünün stratejisini yansıtıyor mu" sorusu yine cevapsız kalırdı.
    """
    from meridian import counterfactual as _cf
    satir = {"id": "CF-2026-08-25-ZZZ-breakout_vcp", "date": "2026-08-25",
             "strategy_version": 7, "ticker": "ZZZ", "setup": "breakout_vcp", "score": 80,
             "entry_trigger": 10.0, "entry": 10.0, "stop": 9.0, "target": 12.0, "rr_expected": 2.0,
             "r_multiple_expected": 2.0, "regime": "trend_up", "verdict": "GO",
             "taken": False, "dormant": False}
    # GİRİLMEMİŞ satır bilerek: damga izin listesinden kopyalanıyor ve o kopya `entered`
    # dalından ÖNCE oluyor, yani iddia aynı — fikstür ise giriş mekaniğinin (hi/lo/entry)
    # alanlarını taşımak zorunda kalmıyor. Testi kırılgan yapan şey, sınadığı iddiadan
    # fazlasını kurmaktır.
    cikti = _cf._resolve(satir, "2026-08-26", "no_fill")
    assert cikti.get("strategy_version") == 7, (
        f"çözülmüş satır damgayı kaybetti: {cikti.get('strategy_version')!r} — "
        "`_resolve`ın izin listesine `strategy_version` eklenmemiş")
