"""test_score_calibration_split_v95.py — SKOR KALİBRASYONUNUN AYRIŞTIRILMIŞ ÖLÇÜMÜ (2026-07-26).

Canlı defterde raporlanan "skor IC'si" fiilen KARŞI-OLGUSAL satırların IC'siydi: 2102 cf, 95 gerçek
işlemi 22:1 oranında boğuyordu ve havuzlanmış tek sayı, iki AYRI popülasyonun harmanıydı (gerçekler
kapıdan geçmiş girişler, cf satırları alınmamış hipotetikler). `analytics.score_calibration` artık
dilimleri ayrı ölçüyor; bu dosya o ayrımın uçtan uca TUTTUĞUNU kilitler:

  1. İKİ DİLİM DE ÖLÇÜLÜR — 40 gerçek + 40 cf satırla `real`/`cf`/`verdict`/`anlamli` gerçekten üretilir
     (fikstür değil, ÜRETİM fonksiyonu hesaplar).
  2. TÜKETİCİ DOĞRU DİLİME BAKAR — `selfreview._score_ic` üç şema durumunu (yeni+dolu, yeni+ölçülmedi,
     eski şema) birbirine karıştırmadan ayırır; "ölçemedim" cevabı havuzlanmış sayıyla DOLDURULMAZ.
  3. ESKİ ŞEMA KIRMAZ — `real` anahtarı hiç olmayan bir defterle `_attention` çökmeden koşar.
"""
from __future__ import annotations

import pytest

from meridian import analytics, counterfactual, selfreview, store


def _rows(n: int, *, sign: float, seed: int = 0):
    """Skor↔R ilişkisi TAŞIYAN satırlar. Beraberlikler bilerek var (skor 0-100 tam sayı, R sık sık
    aynı) — rütbeleme onları ortalama rütbeyle kırmak zorunda; sıraya duyarlı bir ölçüm burada
    defterin yazılma sırasına göre farklı sayı üretirdi."""
    out = []
    for i in range(n):
        sc = 50 + (i % 10) * 5                       # 50..95, her değer tekrar eder (beraberlik)
        r = sign * ((i % 10) - 4.5) / 4.5            # skorla monoton, ±1R bandında
        out.append({"score": sc, "r_multiple": round(r + (seed * 0.0), 4)})
    return out


@pytest.fixture
def kirk_kirk(sandbox_state):
    """40 GERÇEK + 40 cf satır: her iki dilim de 30 eşiğini geçer, yani ikisi de ÖLÇÜLEBİLİR."""
    store.write_jsonl("trades.jsonl", [dict(r, plan_id=f"P-2026-01-01-A{i}")
                                       for i, r in enumerate(_rows(40, sign=1.0))])
    store.write_jsonl(counterfactual.LEDGER,
                      [dict(r, entered=True, id=f"C{i}")
                       for i, r in enumerate(_rows(40, sign=-1.0))])
    return sandbox_state


# ---------------------------------------------------------------------------------------------
# (a) İKİ DİLİM DE GERÇEKTEN ÖLÇÜLÜR
# ---------------------------------------------------------------------------------------------
def test_forty_real_and_forty_cf_rows_produce_both_slices(kirk_kirk):
    cal = analytics.score_calibration()
    assert cal is not None, "80 çift var ama kalibrasyon hiç üretilmedi"
    assert cal["n"] == 80 and cal["n_real"] == 40 and cal["n_cf"] == 40

    assert isinstance(cal["real"], dict) and cal["real"]["n"] == 40, "gerçek dilim ölçülmedi"
    assert isinstance(cal["cf"], dict) and cal["cf"]["n"] == 40, "cf dilimi ölçülmedi"
    # İKİ DİLİM ZIT YÖNDE KURULDU: havuzlanmış tek sayı bu ayrımı GÖREMEZ — ayrıştırmanın sebebi bu.
    assert cal["real"]["rank_ic"] > 0 > cal["cf"]["rank_ic"], \
        f"dilimler ayrışmadı: gerçek={cal['real']['rank_ic']} cf={cal['cf']['rank_ic']}"

    assert cal["real"]["anlamli"] in (True, False), "gerçek dilimde anlamlılık ÖLÇÜLMEDİ"
    assert cal["real"].get("se_yontem"), "anlamlılık iddiasının dayanağı (se_yontem) yazılmadı"
    # cf gözlemleri güne/ticker'a kümelenmiş → i.i.d. değil; anlamlılık burada UYDURULMAZ.
    assert cal["cf"]["anlamli"] is None, "cf dilimine ölçülmemiş bir anlamlılık yazıldı"
    assert "gerçek dilim" in cal["verdict"], f"hüküm gerçek dilimi konuşmuyor: {cal['verdict']}"


def test_tied_scores_are_ranked_by_average_not_by_row_order(kirk_kirk):
    """BERABERLİK KIRMA SIRAYA DUYARLI OLAMAZ: aynı satırlar TERS sırada yazıldığında IC değişmemeli.
    Eski `argsort(argsort(x))` beraberleri defterdeki sıralarına göre dağıtıyordu — ölçüm, verinin
    değil defterin yazılma sırasının fonksiyonuydu ve bunun hiçbir izi yoktu."""
    ilk = analytics.score_calibration()["real"]["rank_ic"]
    store.write_jsonl("trades.jsonl", list(reversed(store.read_jsonl("trades.jsonl"))))
    assert analytics.score_calibration()["real"]["rank_ic"] == ilk, \
        "satır sırası IC'yi değiştirdi — beraberlikler ortalama rütbeyle kırılmıyor"


# ---------------------------------------------------------------------------------------------
# (b) TÜKETİCİ ÜÇ ŞEMA DURUMUNU AYIRIR
# ---------------------------------------------------------------------------------------------
def test_score_ic_new_schema_with_a_measured_real_slice():
    ic, n, kaynak = selfreview._score_ic(
        {"rank_ic": 0.40, "n": 200, "real": {"rank_ic": -0.11, "n": 45, "anlamli": True}})
    assert (ic, n) == (-0.11, 45) and kaynak == "gerçek dilim", \
        "gerçek dilim ölçülmüşken havuzlanmış (cf ağırlıklı) sayı okundu"


def test_score_ic_new_schema_with_an_unmeasured_real_slice_does_not_fall_back_to_the_pool():
    """ASIL KUSUR. `real` anahtarı VAR ama None: gerçek dilim <30, yani ÖLÇÜLEMEDİ. Eski kod havuza
    düşüyor ve fiilen cf'in IC'sini "skorun tahmin gücü" diye döndürüyordu — ölçülmemiş bir cevabı,
    yerine geçmemesi gereken sayıyla doldurmak."""
    ic, n, kaynak = selfreview._score_ic({"rank_ic": 0.40, "n": 200, "real": None, "cf": {"n": 200}})
    assert ic is None and n == 0, f"havuza düştü: ic={ic} n={n}"
    assert "ölçülmedi" in kaynak, f"düşüşün SEBEBİ adıyla raporlanmadı: {kaynak!r}"


def test_score_ic_legacy_schema_still_reads_the_pool_and_says_so():
    """Geriye dönük düşüş KORUNUR ama ETİKETLİ: `real` anahtarı HİÇ olmayan eski defterlerde elde
    yalnız havuzlanmış değer var; onu sessizce düşürmek de kanıt kaybı olurdu."""
    ic, n, kaynak = selfreview._score_ic({"rank_ic": -0.22, "n": 44})
    assert (ic, n) == (-0.22, 44) and kaynak == "havuzlanmış (eski şema)"


def test_score_ic_on_an_empty_or_missing_report():
    assert selfreview._score_ic(None) == (None, 0, "")
    assert selfreview._score_ic({}) == (None, 0, "")


# ---------------------------------------------------------------------------------------------
# (c) ESKİ ŞEMA DİKKAT LİSTESİNİ KIRMAZ
# ---------------------------------------------------------------------------------------------
def test_attention_runs_over_a_legacy_schema_report_without_breaking(sandbox_state):
    """Eski şemayla yazılmış bir `score_calibration.json` diskte durabilir (defterler yeniden
    hesaplanana kadar). O dosya `_attention`ı ÇÖKERTMEMELİ — ve negatif havuzlanmış IC, artık
    yüksek önemli bir dikkat satırı DOĞURMAMALI (kaynak gerçek dilim değil)."""
    store.write_json("score_calibration.json", {"rank_ic": -0.42, "n": 90, "monotone_hint": False})
    rep = selfreview.build()
    whys = " | ".join(a["why"] for a in rep["attention"])
    assert "NEGATİF" not in whys, \
        "havuzlanmış (cf ağırlıklı) IC yine dikkat satırı doğurdu — ölçülmemiş sinyalle uyarı"
    # POZİTİF KONTROL: yeni şemada ÖLÇÜLMÜŞ ve anlamlı negatif dilim satırı ÜRETİR (kural ölmedi).
    store.write_json("score_calibration.json",
                     {"rank_ic": -0.42, "n": 90, "n_real": 90, "n_cf": 0, "monotone_hint": False,
                      "real": {"rank_ic": -0.42, "n": 90, "anlamli": True,
                               "se_yontem": "i.i.d._varsayimi"}, "cf": None})
    whys2 = " | ".join(a["why"] for a in selfreview.build()["attention"])
    assert "NEGATİF" in whys2, "ölçülmüş ve anlamlı negatif IC sessiz kaldı — kural tümden öldü"


def test_measured_but_insignificant_ic_stays_silent(sandbox_state):
    """`anlamli=False` bir ÖLÇÜM SONUCUDUR: baktık, gürültüden ayrılmıyor. Operatörü strateji
    ağırlıklarını değiştirmeye çağırmak için yeterli değildir."""
    store.write_json("score_calibration.json",
                     {"rank_ic": -0.09, "n": 40, "n_real": 40, "n_cf": 0,
                      "real": {"rank_ic": -0.09, "n": 40, "anlamli": False,
                               "se_yontem": "i.i.d._varsayimi"}, "cf": None})
    whys = " | ".join(a["why"] for a in selfreview.build()["attention"])
    assert "NEGATİF" not in whys, "anlamsız (gürültü içi) IC dikkat satırı doğurdu"
