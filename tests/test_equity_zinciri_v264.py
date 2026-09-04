"""test_equity_zinciri_v264.py — WP2-D ARTIĞI: TOHUM PENCERESİ PANO BEYANI (v264).

ÖLÇÜLEN BORÇ (2026-08-22; ROADMAP H0 "equity_curve zinciri / seed_boundary kadanslı yazar —
pano reset-penceresi dahil" kaleminin v245/v246 SONRASI kalan gövdesi):

  Üç bacak kapanmıştı: bacak-1 `ledgerstamp.seed_boundary` onarımı (v245-D), bacak-2
  `loop.daily_cycle` kadanslı yazar (v245), bacak-3 pano pencere beyanı — donukluk, delikler,
  reset işaretleri, yazım makbuzu (v246, `test_wp2d_pano_beyani_v246`). AÇIK KALAN ÜÇ ŞEY:

  1. Eğri beyanı DÖRDÜNCÜ pencereyi söylemiyordu: serinin hangi kısmı ANTRENMAN TOHUMU
     (`replay_seed`, survivorship'li training) ve hangi kısmı kadanslı yazarın CANLI noktaları.
     882 tohum noktası + canlı noktalar TEK çizgide, sınır beyansız — operatör "P&L eğrisi" diye
     baktığı şeklin çoğunun training artefaktı olduğunu grafikten öğrenemiyordu.
  2. `/api/hermes → learning.defter.sinir` (seed_boundary çıktısı: kaynak/güven/yollar) v245'ten
     beri SERVİS EDİLİYOR (`test_wp2d_egri_kadansli_yazar_v245::test_D_karne_sinirin_KAYNAGINI_tasir`
     analytics'e kadar iniyor) ama app.js'te OKUYUCUSU YOKTU — YASA 6 ihlali sürüyordu.
  3. ROADMAP §2-37'nin ölçtüğü ayrışma (`yollar_ayrisik`: reset işareti 2026-07-20 ↔ damga
     2026-07-24) yalnız veri/CLI'da görünürdü; panoda hiçbir yüzeye çıkmıyordu. Otorite kararı
     Rol-1'de BEKLİYOR — bu tur karar VERMEZ, ayrışmayı GÖRÜNÜR kılar.
     KARAR VERİLDİ (TSK-035, 2026-09-04): sıra YOL-2 (damga, DOĞRUDAN ölçüm) > YOL-1 (reset
     işareti, çapraz-sağlama) — `tests/test_seed_boundary_sira_v411.py`.

BU TURUN ÇÖZÜMÜ (v246 ile aynı mimari yasa): hesap SUNUCUDA, pano yalnız ÇİZER.
  · `ledgerstamp.seed_boundary(rows, eq=…)` — çağıran elindeki zarfı verebilir (ikinci okuma yok);
    sınır yasası TEK yerde kalır, api ikinci bir sınır hesabı KURMAZ.
  · `api._egri_beyani(ec, pf, sinir=…)` — beyana `tohum_siniri` bloğu eklenir (replay_end,
    kaynak, güven, yollar, yollar_ayrisik, grafik indisi `i`, konumlanamıyorsa `konum_neden`).
  · app.js: eğri şeridi ⑤ tohum-sınırı satırı + grafikte "tohum → canlı" işareti (indis
    SUNUCUDAN; null ise yer uydurulmaz) + karne kartında ölçüm-zemini satırı (`learning.defter`
    nihayet okunur — YASA 6 kapanır).

HİÇBİR TEST CANLI STATE'E YAZMAZ: durum yazan her test `sandbox_state` üzerinden koşar.
null=ölçülemedi≠0 (v196): sınır ölçülemediyse beyan None taşır, pano "ölçülemedi" yazar — 0 ya da
bugünün tarihi UYDURULMAZ. Renk yasası (v197): sınır satırı NÖTRDÜR (tohum bilinçli kurulum, arıza
değil); `warn` YALNIZ ayrışma kapısının içinde basılır.
"""
from __future__ import annotations

import ast
import json
import pathlib
import re

import pytest
from fastapi.testclient import TestClient

from meridian import api, ledgerstamp, sermaye, store

SRC = pathlib.Path(__file__).resolve().parent.parent
APPJS = (SRC / "meridian" / "web" / "app.js").read_text()
# YORUM SATIRLARI SAYILMAZ (repo deseni: test_wp2d_pano_beyani_v246): gerekçe kaynakta durmalı
# ama BİLDİRİM sanılmamalı.
APPJS_KOD = "\n".join(l for l in APPJS.splitlines() if not l.lstrip().startswith("//"))


# =================================================================================================
# YARDIMCILAR (şekiller v245/v246 fikstürleriyle BİREBİR — aynı yazarın izini ölçüyoruz)
# =================================================================================================
def _isaret(egri_son="2026-07-20", id_="SR-20260801T151429+0000"):
    """`sermaye.uygula`nın zarfa bastığı işaretin şekli."""
    return {"id": id_, "tarih": "2026-08-01T15:14:29+00:00", "tip": "paper_equity_reset",
            "onceki_deger": 94457.91, "yeni_deger": 100000.0,
            "egri_son_nokta": [egri_son, 94457.91], "gerekce": "fikstür"}


def _zarf(points, isaretler=None):
    eq = {"version": 4, "points": list(points)}
    if isaretler is not None:
        eq[sermaye.CURVE_MARK_KEY] = list(isaretler)
    return eq


def _tohum_satiri(ts_close="2026-07-24"):
    """`replay_seed` damgalı tek defter satırı — YOL-2'nin (damga) okuduğu kanıt."""
    return {"id": "T00001", "ts_open": "2026-07-01", "ts_close": ts_close, "ticker": "AAA",
            "side": "long", "entry": 100.0, "exit": 101.0, "qty": 10, "r_multiple": 0.5,
            "pnl_pct": 0.01, "pnl_dollars": 10.0, "costs": 5.0, "exit_reason": "target",
            "strategy_version": 4, "regime": "trend_up", "setup": "breakout_vcp",
            "bars_held": 5, ledgerstamp.FIELD: ledgerstamp.REPLAY_SEED}


# =================================================================================================
# §A — LEDGERSTAMP: sınır hesabı ELDEN VERİLEN zarfla da koşar (ikinci okuma yok)
# =================================================================================================
def test_A_seed_boundary_verilen_ZARFTAN_okur(sandbox_state):
    """`eq` verilirse eğri zarfı diskten YENİDEN okunmaz: /api/performance beyanı elindeki tek
    okumayı verir. Disk ile parametre BİLEREK farklı — hangisinin konuştuğu ölçülür."""
    store.write_json(ledgerstamp.EQUITY, _zarf([["2026-07-20", 1.0]], [_isaret("2026-07-20")]))
    elden = _zarf([["2026-06-30", 1.0]], [_isaret("2026-06-30", id_="SR-ELDEN")])
    b = ledgerstamp.seed_boundary([], eq=elden)
    assert b["replay_end"] == "2026-06-30", "verilen zarf değil disk okunmuş (ikinci okuma)"
    assert b["reset_isareti"]["isaret_id"] == "SR-ELDEN"


def test_A_seed_boundary_eq_VERILMEZSE_eski_davranis(sandbox_state):
    """Geri uyum: `eq=None` → diskten okunur; mevcut tüm çağıranlar (analytics, recompute,
    migrate) davranış değiştirmez."""
    store.write_json(ledgerstamp.EQUITY, _zarf([["2026-07-20", 1.0]], [_isaret("2026-07-20")]))
    assert ledgerstamp.seed_boundary([])["replay_end"] == "2026-07-20"


# =================================================================================================
# §B — `_egri_beyani` TOHUM SINIRINI taşır (dördüncü pencere)
# =================================================================================================
def test_B_beyan_TOHUM_SINIRINI_tasir_ve_KONUMLANDIRIR():
    """Sınır beyanda: tarih + kaynak + güven + grafik indisi. İndis SUNUCUDA hesaplanır
    (reset işaretleriyle aynı mekanik) — pano tarihleri yeniden eşleştirmez."""
    zarf = _zarf([["2026-07-17", 1.0], ["2026-07-20", 2.0], ["2026-08-14", 3.0]],
                 [_isaret("2026-07-20")])
    sinir = ledgerstamp.seed_boundary([], eq=zarf)
    b = api._egri_beyani(zarf, {}, sinir=sinir)
    t = b["tohum_siniri"]
    assert t is not None, "sınır verildi ama beyan taşımıyor"
    assert t["replay_end"] == "2026-07-20"
    assert t["kaynak"] == ledgerstamp.KAYNAK_RESET and t["guven"] == "yuksek"
    assert t["i"] == 1 and t["konum_neden"] is None
    assert t["yollar_ayrisik"] is False


def test_B_sinir_VERILMEZSE_beyan_yok_uydurulmaz():
    """`sinir` verilmedi ≠ "sınır sağlam": beyan None taşır ve pano onu "beyan yok" diye çizer.
    Eski imzayla çağıran hiçbir tüketici kırılmaz (geri uyum)."""
    b = api._egri_beyani(_zarf([["2026-07-17", 1.0], ["2026-07-20", 2.0]]), {})
    assert b["tohum_siniri"] is None


def test_B_sinir_OLCULEMEDIYSE_konum_uydurulmaz():
    """Kaynak yoksa (işaret yok + damga yok) replay_end None'dır: beyan 0 ya da bugünün tarihini
    YAZMAZ; indis None kalır ve nedeni yazılıdır (v196 çırçırı)."""
    zarf = _zarf([["2026-07-17", 1.0], ["2026-07-20", 2.0]])
    sinir = ledgerstamp.seed_boundary([], eq=zarf)
    assert sinir["replay_end"] is None                    # ön koşul: gerçekten ölçülemedi
    t = api._egri_beyani(zarf, {}, sinir=sinir)["tohum_siniri"]
    assert t["replay_end"] is None and t["i"] is None
    assert t["kaynak"] == ledgerstamp.KAYNAK_YOK
    assert "ölçülemedi" in (t["konum_neden"] or "")


def test_B_sinir_tarihi_SERIDE_YOKSA_listelenir_konumlanmaz():
    """YOL-2 (damga) vakası — canlıda ÖLÇÜLEN hâl: damga 2026-07-24 diyor ama eğride o tarihli
    nokta yok. Sınır LİSTELENİR (gizlemek beyanı yutmak olurdu), grafiğe KONMAZ (yer uydurulmaz)
    — reset işaretlerinin `konum_neden` sözleşmesinin aynısı."""
    zarf = _zarf([["2026-07-17", 1.0], ["2026-07-20", 2.0], ["2026-08-14", 3.0]])
    sinir = ledgerstamp.seed_boundary([_tohum_satiri("2026-07-24")], eq=zarf)
    assert sinir["kaynak"] == ledgerstamp.KAYNAK_DAMGA    # ön koşul: yedek yol konuştu
    t = api._egri_beyani(zarf, {}, sinir=sinir)["tohum_siniri"]
    assert t["replay_end"] == "2026-07-24" and t["i"] is None
    assert "seride" in (t["konum_neden"] or "")


def test_B_yollar_AYRISIRSA_bayrak_ve_iki_deger_beyanda():
    """ROADMAP §2-37'nin ölçtüğü ayrışma panoya makine-okunur çıkar: bayrak + İKİ yolun değeri.
    Tek tarih basmak, iki kanıtın anlaştığı yanılsamasını üretirdi.

    KARAR VERİLDİ (TSK-035, 2026-09-04 — bu satır o zaman "Karar VERİLMEZ (Rol-1'de)" diyordu,
    tarihçe için üstte durur): sıra YOL-2 (`trades.kaynak`, DOĞRUDAN ölçüm) > YOL-1 (donmuş reset
    işareti, çapraz-sağlama). Bayrak ve İKİ yolun değeri AYNEN duruyor — değişen HANGİSİNİN
    `replay_end`i KAZANDIĞI (`tests/test_seed_boundary_sira_v411.py::test_B_ayrisik_YENI_SIRA_YOL2yi_secer`)."""
    zarf = _zarf([["2026-07-17", 1.0], ["2026-07-20", 2.0], ["2026-08-14", 3.0]],
                 [_isaret("2026-07-20")])
    sinir = ledgerstamp.seed_boundary([_tohum_satiri("2026-07-24")], eq=zarf)
    t = api._egri_beyani(zarf, {}, sinir=sinir)["tohum_siniri"]
    assert t["yollar_ayrisik"] is True
    assert t["yollar"][ledgerstamp.KAYNAK_RESET] == "2026-07-20"
    assert t["yollar"][ledgerstamp.KAYNAK_DAMGA] == "2026-07-24"
    assert t["replay_end"] == "2026-07-24", "DOĞRUDAN ölçüm esas kalmalı (TSK-035: YOL-2 > YOL-1)"


# =================================================================================================
# §C — /api/performance SERVİSİ: tek hesap, elden zarf
# =================================================================================================
def test_C_api_performance_TOHUM_SINIRINI_servis_eder(sandbox_state):
    """TSK-035 (2026-09-04) SONRASI: fikstürün damgalı satırı (`2026-07-18`) BİLEREK equity
    serisinde YOK (aynı hâl v245/v264 fikstürlerinde hep böyleydi — o zaman önemsizdi çünkü RESET
    kazanıyordu). Artık DOĞRUDAN yol (damga) kazandığı için bu tarih seride yoksa `i` KONUMLANAMAZ
    — `test_B_sinir_tarihi_SERIDE_YOKSA_listelenir_konumlanmaz`nın AYNI sözleşmesi burada da geçer:
    sınır yine LİSTELENİR (gizlenmez), grafiğe KONMAZ (yer uydurulmaz)."""
    store.write_json("equity_curve.json",
                     _zarf([["2023-01-12", 100000.0], ["2026-07-20", 94457.91],
                            ["2026-08-14", 100100.0]], [_isaret("2026-07-20")]))
    store.write_json("portfolio.json", {"cash": 100000.0, "last_date": "2026-08-14",
                                        "positions": {}, "armed": []})
    (sandbox_state / "trades.jsonl").write_text(json.dumps(_tohum_satiri("2026-07-18")) + "\n")
    with TestClient(api.app) as c:
        r = c.get("/api/performance")
    assert r.status_code == 200
    b = r.json()["equity_curve_beyani"]
    t = b["tohum_siniri"]
    assert t and t["replay_end"] == "2026-07-18" and t["kaynak"] == ledgerstamp.KAYNAK_DAMGA
    assert t["i"] is None and "seride" in (t["konum_neden"] or "")
    # ESKİ BEYAN ALANLARI AYNEN DURUYOR: yeni pencere eskilerin YERİNE geçmez, YANINA gelir.
    assert b["n_isaret"] == 1 and b["gecikme_gun"] == 0


def test_C_CIVI_sinir_hesabi_TEK_kaynaktan_ve_ELDEN_zarfla():
    """AST çivisi (metin değil): `api_performance` sınırı `ledgerstamp.seed_boundary`den alır ve
    elindeki zarfı `eq=` ile verir. İkisi de düşerse ya ikinci bir sınır yasası doğmuş ya da
    eğri aynı istekte İKİNCİ kez okunuyor demektir."""
    tree = ast.parse((SRC / "meridian" / "api.py").read_text())
    fn = next(n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "api_performance")
    calls = [n for n in ast.walk(fn) if isinstance(n, ast.Call)
             and isinstance(n.func, ast.Attribute) and n.func.attr == "seed_boundary"]
    assert calls, "api_performance sınırı ledgerstamp.seed_boundary'den almıyor"
    kw = {k.arg for c in calls for k in c.keywords}
    assert "eq" in kw, "seed_boundary'ye elden zarf (eq=) verilmiyor — eğri ikinci kez okunur"


def test_C_CIVI_beyan_siniri_PARAMETRE_olarak_alir():
    """`_egri_beyani` kendi sözleşmesini korur ("hiçbir dosyayı ikinci kez okumaz"): sınır İÇERİDE
    hesaplanmaz, parametreyle gelir."""
    tree = ast.parse((SRC / "meridian" / "api.py").read_text())
    fn = next(n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "_egri_beyani")
    adlar = [a.arg for a in fn.args.args + fn.args.kwonlyargs]
    assert "sinir" in adlar, "_egri_beyani `sinir` parametresi almıyor"
    icerde = [n for n in ast.walk(fn) if isinstance(n, ast.Call)
              and isinstance(n.func, ast.Attribute) and n.func.attr == "seed_boundary"]
    assert not icerde, "_egri_beyani sınırı kendi hesaplıyor — dosyalar ikinci kez okunur"


# =================================================================================================
# §D — PANO ÇİVİLERİ (kaynak): alan uçta VAR olmak, panoda OKUNUYOR demek DEĞİLDİR
#      (JS için AST altyapısı yok — v246 deseniyle bilerek metin çivisi + node --check)
# =================================================================================================
def test_D_CIVI_serit_tohum_sinirinin_HER_alanini_okur():
    """YASA 6 alan alan: `tohum_siniri` bloğunun her alanının app.js'te okuyucusu var."""
    assert "b.tohum_siniri" in APPJS_KOD, "beyanın `tohum_siniri` alanı panoda hiç okunmuyor"
    zarf = _zarf([["2026-07-17", 1.0], ["2026-07-20", 2.0], ["2026-08-14", 3.0]],
                 [_isaret("2026-07-20")])
    t = api._egri_beyani(zarf, {}, sinir=ledgerstamp.seed_boundary([], eq=zarf))["tohum_siniri"]
    for alan in t:
        assert f"sin.{alan}" in APPJS_KOD or f"sinB.{alan}" in APPJS_KOD, \
            f"`tohum_siniri.{alan}` üretiliyor ama panoda okuyucusu YOK (YASA 6)"


def test_D_CIVI_uc_hal_AYRI_beyan_yoksa_susulmaz():
    """Beyan yok (uç vermedi) ≠ ölçülemedi (kaynak yok) ≠ ölçüldü — üç hâl ayrı cümle."""
    assert "tohum sınırı beyanı yok" in APPJS, "beyansız hâl susuyor"
    assert "tohum sınırı ölçülemedi" in APPJS, "ölçülemedi hâli susuyor"
    assert "tohum (antrenman) penceresi" in APPJS, "ölçülen sınır şeritte yazılmıyor"


def test_D_CIVI_grafik_siniri_isaretler_yer_UYDURMAZ():
    """Grafikte "tohum → canlı" işareti: indis sunucudan; null ise ÇİZİLMEZ; sınır son noktadaysa
    (sağında canlı nokta yok) çizgi eğri dışına düşer ve çizilmez — şerit o hâli söyler."""
    assert "tohum → canlı" in APPJS, "grafikte sınır işareti yok"
    assert re.search(r"sinB\.i != null && sinB\.i < pts\.length - 1", APPJS_KOD), \
        "sınır işareti konum kapısız çiziliyor (yer uydurma riski)"


def test_D_CIVI_ayrisma_uyarisi_KAPILI_sinir_satiri_NOTR():
    """Renk yasası (v197): `warn` YALNIZ ayrışma kapısının içinde; sınırın kendisi nötr.
    Tohum bilinçli bir kurulumdur, arıza değil — reset satırının nötrlük gerekçesinin aynısı."""
    m = re.search(r"if \(sin && sin\.yollar_ayrisik\) \{[^}]*warn", APPJS_KOD, re.S)
    assert m, "ayrışma uyarısı kapısız (ya da hiç yok) — renk anomali dışında basılıyor olabilir"
    # Sınır satırının ÖLÇÜLEN dalında şiddet rengi yok (nötr <b> serbest):
    olcum_dali = re.search(r'tohum \(antrenman\) penceresi[^`]*?`\)', APPJS)
    assert olcum_dali and 'class="warn"' not in olcum_dali.group(0) \
        and 'class="neg"' not in olcum_dali.group(0), "sınır satırı şiddet rengi taşıyor"


def test_D_CIVI_karne_olcum_zeminini_OKUR():
    """YASA 6 kapanışı: `/api/hermes → learning.defter` (v245'ten beri servis ediliyordu,
    okuyucusu yoktu) karne kartında nihayet okunur — canlı/tohum/belirsiz sayıları + sınır."""
    assert "L.defter" in APPJS_KOD, "karne `learning.defter`i hâlâ okumuyor (YASA 6 ihlali sürer)"
    for alan in ("gercek_canli_n", "replay_seed_n", "belirsiz_n"):
        assert f"df.{alan}" in APPJS_KOD, f"karne zemin sayısı `{alan}` okunmuyor"
    assert "sn.replay_end" in APPJS_KOD and "sn.kaynak" in APPJS_KOD, \
        "karne tohum sınırını (defter.sinir) okumuyor"
    assert "ölçüm zemini beyanı yok" in APPJS, "defter alanı yokken karne susuyor"
