"""test_koruma_tif_v210.py — KORUMA ÖMÜRLÜ OLMAYACAK: bracket TIF'i GTC + bayat-tetik kadansı.

VAKA (canlı A1, 2026-08-06 20:00-20:02Z; v209 koruma dedektörünün doğduğu olay): dört motor
pozisyonunun koruma bacakları öldü — `limit sell` EXPIRED + OCO kardeşi `stop sell` CANCELED.
Hiçbir motor çağrısı iptal etmedi; Alpaca'nın gün-sonu sona-ermesi öldürdü. KÖK: Alpaca
bracket'ında `time_in_force` alanı TEKTİR ve emrin TAMAMINA uygulanır — `broker.ENTRY_TIF="day"`
yalnız GİRİŞ bacağı düşünülerek seçilmişti, ama korumanın da ömrü oydu.

BU DOSYA İKİ PARÇAYI BİRLİKTE ÇİVİLER (biri eksik olursa regresyon):
  1) TIF=GTC — koruma bacağı seans kapanışında ölmez; "day" beyaz-listeden ÇIKARILDI, yani
     `execution_v2.tif: day` yazan bir yapılandırma bile korumayı geri öldüremez.
  2) BAYAT TETİK TIF'e HAVALE EDİLEMEZ — `loop.daily_cycle` her turda, silahlanmadan ÖNCE
     dolmamış motor girişlerini KENDİ eliyle iptal eder; dolmuş parent'ın koruma bacaklarına
     DOKUNMAZ. Olay adı HALT yolununkinden AYRIdır (aynı adla yazılsaydı defteri okuyan her gece
     "HALT oldu" sanardı — UYDURMA sınırı).

YÖNTEM: hiçbir test ağa çıkmaz ve hiçbir test GERÇEK istemciye emir gönderip iptal ettirmez —
adaptörün OKUMA ucu (`orders`) ile `cancel_order` saplanır, `httpx` hiç kullanılmaz. Her iddianın
yanında POZİTİF KONTROL vardır: sınır bilerek delinir ve iddianın gerçekten düştüğü gösterilir.
"""
from __future__ import annotations

import inspect
import pathlib
import shutil

import pytest
import yaml

from meridian import broker as BR
from meridian import config, health, loop, store
from meridian.adapters import alpaca
from tests.conftest import make_bars

REPO = pathlib.Path(config.__file__).resolve().parent.parent
KART = REPO / "research" / "cards" / "EXE-2026-001-entry-execution.yaml"

FAKE_KEY = "PKKORUMATIFFAKEKEY7788990011"
FAKE_SECRET = "SKKORUMATIFFAKESECRET2233445566"


# =================================================================================================
# FİKSTÜRLER
# =================================================================================================
@pytest.fixture
def paper(sandbox_state, monkeypatch):
    """Sahte kimlik + `alpaca_paper` arka ucu; taşıma SAĞLIKLI. Gerçek istemci hiç kurulmaz."""
    from meridian import secrets as secrets_mod
    monkeypatch.setenv("ALPACA_PAPER_KEY", FAKE_KEY)
    monkeypatch.setenv("ALPACA_PAPER_SECRET", FAKE_SECRET)
    monkeypatch.delenv("MERIDIAN_GCP_PROJECT", raising=False)
    secrets_mod.clear_cache()
    monkeypatch.setattr(config, "BROKER", "alpaca_paper")
    monkeypatch.setattr(alpaca, "paper_available", lambda: True)
    monkeypatch.setattr(alpaca, "transport", lambda: {"ok": True, "error": ""})
    yield sandbox_state
    secrets_mod.clear_cache()


def _events(ad: str) -> list:
    """TAM AD eşleşmesi — bu dosyanın çekirdek iddiası iki olayın AYRI adlar taşıması."""
    return [e for e in store.read_jsonl("events.jsonl") if e.get("event") == ad]


# Aynanın emir defteri: motorun DOLMUŞ bracket'ı (koruma bacaklarıyla), motorun DOLMAMIŞ girişi,
# ve operatörün kendi emri. Üçü de aynı hesapta — sahiplik/koruma sınırları burada ölçülür.
_DOLMUS_PARENT = {"id": "parent-dolmus", "symbol": "NVDA", "client_order_id": "P-2026-08-05-NVDA",
                  "status": "filled", "filled_qty": "40", "side": "buy",
                  "legs": [{"id": "leg-tp", "type": "limit", "status": "new", "side": "sell"},
                           {"id": "leg-sl", "type": "stop", "status": "held", "side": "sell"}]}
_DOLMAMIS_GIRIS = {"id": "parent-bayat", "symbol": "AMD", "client_order_id": "P-2026-08-06-AMD",
                   "status": "new", "filled_qty": "0", "side": "buy", "legs": []}
_OPERATOR_EMRI = {"id": "op-1", "symbol": "TSLA", "client_order_id": "9f1c-uuid-operator",
                  "status": "new", "filled_qty": "0", "side": "buy", "legs": []}


def _ayna_defteri(monkeypatch) -> list:
    """`cancel_open_entries`in GERÇEK gövdesi koşsun diye yalnız okuma ucu + iptal ucu saplanır."""
    iptal: list = []
    monkeypatch.setattr(alpaca, "orders",
                        lambda **k: [dict(_DOLMUS_PARENT), dict(_DOLMAMIS_GIRIS),
                                     dict(_OPERATOR_EMRI)])
    monkeypatch.setattr(alpaca, "cancel_order",
                        lambda oid: iptal.append(oid) or {"ok": True})
    return iptal


# =================================================================================================
# A — YASA: TIF ARTIK GTC VE "day" BİR DÜĞME DEĞİL
# =================================================================================================
def test_a1_entry_tif_gtc_ve_yasa_surumu_yukseldi():
    """Sabit + sürüm birlikte değişmeli: yasa değiştiyse sürüm de değişir, yoksa E2 defterinde
    aynı `law` damgasıyla İKİ FARKLI yasa yaşar ve hangi emrin hangi yasayla gittiği okunamaz."""
    assert BR.ENTRY_TIF == "gtc"
    assert BR.ENTRY_LAW_VERSION == "E1-v2"
    assert BR.ENTRY_LAW_VERSION != "E1-v1", "yasa değişti ama sürüm eski kaldı"


def test_a2_entry_law_gtc_dondurur_konfig_bosken():
    law = BR.entry_law({})
    assert law["tif"] == "gtc" and law["version"] == "E1-v2"


def test_a3_konfig_day_derse_yasa_KABUL_ETMEZ(monkeypatch):
    """KELEPÇE: `execution_v2.tif: day` korumayı seans-ömürlü yapardı — beyaz-liste onu almaz.

    POZİTİF KONTROL: aynı yolda 'gtc' KABUL EDİLİR, yani config bacağı ölü değil; reddedilen
    yalnız korumayı öldüren değerdir."""
    assert BR.entry_law({"tif": "day"})["tif"] == "gtc"
    assert BR.entry_law({"tif": " DAY "})["tif"] == "gtc"
    monkeypatch.setattr(config, "goal", lambda: {"execution_v2": {"tif": "day"}})
    assert BR.entry_law()["tif"] == "gtc", "goal.yaml korumayı seans-ömürlü yapabiliyor"
    monkeypatch.setattr(config, "goal", lambda: {"execution_v2": {"tif": "gtc"}})
    assert BR.entry_law()["tif"] == "gtc"                     # pozitif kontrol: yol açık
    assert BR.ENTRY_TIF_ALLOWED == ("gtc",), "beyaz-liste tek uçlu olmalı"


def test_a4_yururlukteki_goal_yaml_ile_de_gtc(paper, monkeypatch):
    """DEPODAKİ GERÇEK `state/goal.yaml` ile ölçüm: dosyada hâlâ `tif: day` yazıyor olabilir
    (2026-08-07 itibarıyla yazıyor) — yasa yine GTC vermeli. Bu testin varlık sebebi, sabitin
    tek başına değiştirilmesinin CANLIDA SESSİZ NO-OP olmasıydı."""
    shutil.copy2(REPO / "state" / "goal.yaml", paper / "goal.yaml")
    config.reload_config()
    try:
        assert BR.entry_law()["tif"] == "gtc"
    finally:
        config.reload_config()


def test_a5_karar_sozlugu_ve_ayna_govdesi_gtc_tasir():
    """İki motorun ORTAK karar sözlüğü TIF'i taşır ve E2 defterine o yazılır."""
    dec = BR.entry_order_decision(100.0, ref_price=99.0, atr=1.0)
    assert dec["tif"] == "gtc" and dec["law"] == "E1-v2"


# =================================================================================================
# B — İPTAL YOLU: DOLMAMIŞ GİRİŞ GİDER, KORUMA BACAĞI YAŞAR
# =================================================================================================
def test_b1_gunluk_iptal_yalnizca_dolmamis_motor_girisine_dokunur(paper, monkeypatch):
    """ÇEKİRDEK GÜVENLİK: dolmuş parent'ın koruma bacakları İPTAL EDİLMEZ (pozisyon çıplak kalırdı),
    operatörün emrine DOKUNULMAZ, yalnız motorun dolmamış girişi geri çekilir."""
    iptal = _ayna_defteri(monkeypatch)

    res = loop._cancel_stale_entry_orders("2026-08-07")

    assert iptal == ["parent-bayat"], f"yanlış emirler iptal edildi: {iptal}"
    assert "leg-tp" not in iptal and "leg-sl" not in iptal, \
        "KORUMA BACAĞI İPTAL EDİLDİ — pozisyon çıplak bırakıldı"
    assert [k["symbol"] for k in res["kept"]] == ["NVDA"], \
        "dolmuş parent `kept` altında değil — koruma sınırı ölçülmüyor"
    assert [f["symbol"] for f in res["foreign"]] == ["TSLA"]
    assert [c["symbol"] for c in res["cancelled"]] == ["AMD"]


def test_b2_gunluk_iptalin_olayi_HALT_olayindan_AYRI(paper, monkeypatch):
    """İKİ ANLATI, İKİ AD. Aynı adla yazılsaydı olay defterini okuyan (pano, teşhis, operatör) her
    gece 'HALT oldu' sanardı — ölçülmemiş bir olguyu iddia etmek olurdu."""
    _ayna_defteri(monkeypatch)
    assert loop.EV_STALE_ENTRIES_CANCELLED != loop.EV_MIRROR_ENTRIES_CANCELLED

    loop._armed_dropped_by_gate({"armed": []}, "2026-08-07", "halt")
    loop._cancel_stale_entry_orders("2026-08-07")

    halt_olay = _events(loop.EV_MIRROR_ENTRIES_CANCELLED)
    gun_olay = _events(loop.EV_STALE_ENTRIES_CANCELLED)
    assert len(halt_olay) == 1 and len(gun_olay) == 1, \
        f"iki yol tek olayda birleşti: halt={len(halt_olay)} gunluk={len(gun_olay)}"
    assert halt_olay[0]["gate"] == "halt" and gun_olay[0]["gate"] == "gunluk_kadans"
    assert "HALT" not in str(gun_olay[0].get("detail", "")), \
        "günlük kadans kendini HALT diye anlatıyor"


def test_b3_iptal_adaptorun_denetlenmis_yolundan_gecer():
    """Yetki sınırı (v161'in C23 çivisinin bu tur için tekrarı): döngü kendi çıplak iptalini
    kurmamalı — sahiplik süzgeci ve koruma-bacağı yasağı adaptörün İÇİNDE yaşıyor."""
    for fn in (loop._cancel_mirror_entries, loop._cancel_stale_entry_orders):
        src = inspect.getsource(fn)
        for yasak in ("httpx", "close_all", "close_engine_position", "submit_"):
            assert yasak not in src, f"{fn.__name__} denetlenmemiş bir emir yolu kurdu: {yasak}"
    assert "alpaca.cancel_open_entries()" in inspect.getsource(loop._cancel_mirror_entries)


def test_b4_broker_alpaca_degilse_iptal_denenmez(sandbox_state, monkeypatch):
    """Yetki sınırı: ayna kapalıyken hiçbir iptal çağrısı doğmaz (POZİTİF KONTROL: sayaç 0)."""
    cagri = []
    monkeypatch.setattr(config, "BROKER", "paper")
    monkeypatch.setattr(alpaca, "cancel_open_entries", lambda: cagri.append(1) or {})
    out = loop._cancel_stale_entry_orders("2026-08-07")
    assert cagri == [] and "skipped" in out


# =================================================================================================
# C — KADANS: GÜNLÜK DÖNGÜ, SİLAHLANMADAN ÖNCE
# =================================================================================================
def test_c1_cagri_silahlanmadan_ONCE_ve_dolum_kararindan_SONRA():
    """SIRA SÖZLEŞMESİ (kaynak düzeyinde, v161'in emsali): daha erken çağrılsaydı bugünün dolum
    kararı verilmeden emir iptal edilirdi; daha geç çağrılsaydı BU AKŞAM gönderilen taze emirler
    kesilirdi. İkisi de sessiz bir icra hatası olurdu, testi olmayan bir sıra ise sözleşme değil."""
    src = inspect.getsource(loop.daily_cycle)
    i_iptal = src.index("_cancel_stale_entry_orders(dstr)")
    assert src.index("b.fill_entry(plan") < i_iptal, "iptal, dolum kararından ÖNCE koşuyor"
    assert i_iptal < src.index('meta["armed"].append(plan)'), \
        "iptal, yeni planlar silahlandıktan SONRA koşuyor"
    assert i_iptal < src.index("mirror_submit_armed(meta, dstr"), \
        "iptal, taze emirler aynaya gönderildikten SONRA koşuyor — kendi emrimizi keseriz"


def test_c2_gunluk_dongu_iptali_gercekten_cagiriyor(paper, monkeypatch):
    """UÇTAN UCA (sahte adaptör): tam bir `daily_cycle` turu bayat girişi geri çeker, koruma
    bacağına dokunmaz ve olayı kendi adıyla yazar. GERÇEK istemciye tek bir çağrı gitmez."""
    for f in ("goal.yaml", "bounds.yaml"):
        shutil.copy2(REPO / "state" / f, paper / f)
    config.reload_config()
    (paper / "strategy.yaml").write_text(yaml.safe_dump(config.default_strategy()))
    iptal = _ayna_defteri(monkeypatch)
    monkeypatch.setattr(alpaca, "positions", lambda: [])
    monkeypatch.setattr(alpaca, "account", lambda: {"equity": "100000"})
    gonderim = []
    monkeypatch.setattr(alpaca, "submit_plan",
                        lambda *a, **k: gonderim.append(1) or {"ok": True, "qty": 1, "law": {}})
    idx = make_bars(300, seed=1, trend=0.0009)
    bars = {"AAA": make_bars(300, seed=2, breakout_at=200),
            "BBB": make_bars(300, seed=3, breakout_at=150)}
    try:
        out = loop.daily_cycle(bars, idx, on_date=str(idx["date"].iloc[-1].date()))
    finally:
        config.reload_config()

    assert out.get("date"), f"döngü hiç koşmadı: {out}"
    assert iptal == ["parent-bayat"], f"günlük iptal koşmadı ya da fazlasına dokundu: {iptal}"
    assert _events(loop.EV_STALE_ENTRIES_CANCELLED), "günlük iptal olay defterine geçmedi"


def test_c3_kapi_kapaliyken_de_kosar_ve_HALT_ile_karismaz(paper, monkeypatch):
    """HALT günü: kapı dalı kendi iptalini yapar, günlük kadans YİNE koşar (o gün 0 bulur) — ve
    iki satır AYRI adlarla defterde durur. Kapı kapalıyken silahlı planlar KALICI düşürüldüğü için
    ayna emrinin yaşamaya devam etmesi split-brain olurdu; bu yüzden kadans kapı-koşulsuzdur."""
    for f in ("goal.yaml", "bounds.yaml"):
        shutil.copy2(REPO / "state" / f, paper / f)
    config.reload_config()
    (paper / "strategy.yaml").write_text(yaml.safe_dump(config.default_strategy()))
    _ayna_defteri(monkeypatch)
    monkeypatch.setattr(alpaca, "positions", lambda: [])
    monkeypatch.setattr(alpaca, "account", lambda: {"equity": "100000"})
    health.set_halt(True)
    idx = make_bars(300, seed=1, trend=0.0009)
    bars = {"AAA": make_bars(300, seed=2, breakout_at=200)}
    try:
        loop.daily_cycle(bars, idx, on_date=str(idx["date"].iloc[-1].date()))
    finally:
        health.set_halt(False)
        config.reload_config()

    assert _events(loop.EV_STALE_ENTRIES_CANCELLED), "HALT gününde günlük kadans hiç koşmadı"
    assert _events(loop.EV_MIRROR_ENTRIES_CANCELLED), "HALT kapısının kendi iptali kayboldu"


# =================================================================================================
# D — KART: REVİZYON KAYITLI (CLAUDE.md §3 — eşik sonradan değişmez, hüküm silinmez)
# =================================================================================================
def test_d1_kart_revizyonu_mevcut_ve_eski_hukum_silinmemis():
    kart = yaml.safe_load(KART.read_text())
    revs = kart.get("revizyonlar") or []
    r = next((x for x in revs if str(x.get("alan", "")).endswith("TIF")), None)
    assert r is not None, "kartta TIF revizyon girdisi yok — yasa kartsız değişti"
    assert "E1-v2" in str(r.get("degisim")) and "GTC" in str(r.get("degisim")).upper()
    for zorunlu in ("ne_olculdu", "kok_neden", "eski_gerekce_hukmu", "yeni_mekanizma"):
        assert len(str(r.get(zorunlu, ""))) > 80, f"revizyon '{zorunlu}' alanı boş/yüzeysel"
    # ESKİ HÜKÜM SİLİNMEDİ: ön-kayıt metni yerinde durur.
    assert "TIF=DAY" in kart["horizon"], "ön-kayıt hükmü ÜZERİNE YAZILMIŞ (silinmemeliydi)"
    # KILL-LIST + K-GRİD DOKUNULMAZ.
    assert len(kart["kill_criteria"]) == 2
    assert set(kart["parameter_grid"]) == {"limit_offset", "gap_davranisi"}
    assert "YOK" in str(r.get("k_etkisi", "")), "K etkisi beyan edilmemiş"


def test_d2_kart_cikis_bacagi_borcunu_adiyla_kayda_geciyor():
    """Kartın kendi körlüğü kayda geçmeli: çıkış bacağının TIF'i ön-kayıtta HİÇ konuşulmamıştı."""
    r = next(x for x in (yaml.safe_load(KART.read_text()).get("revizyonlar") or [])
             if str(x.get("alan", "")).endswith("TIF"))
    # `.lower()` KULLANILMAZ: Python 'I'yı 'i'ye çevirir, Türkçe'de 'ı'ya — "ÇIKIŞ".lower() bu
    # dosyadaki iddiayı sessizce kaçırırdı (aynı sınıf: dizge karşılaştırmasında yerel varsayımı).
    metin = str(r.get("kok_neden", "")) + str(r.get("eski_gerekce_hukmu", ""))
    assert ("ÇIKIŞ" in metin or "çıkış" in metin) and "kart" in metin, \
        "kart, çıkış bacağının hiç tartışılmamış olduğunu kayda geçirmiyor"
    beyan = str(r.get("kapsam_disi_beyan", ""))
    assert "OPERATÖR" in beyan or "operatör" in beyan, \
        "çıplak pozisyonların operatör kalemi olduğu beyanı eksik"
