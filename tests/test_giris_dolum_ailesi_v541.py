"""test_giris_dolum_ailesi_v541.py — TSK-218: canlı kapanan işlemlerin `trades` satırına GİRİŞ
dolum ailesi (`giris_dolum_ts` + `giris_dolum_fiyat`) MOTORUN KENDİSİ tarafından yazılır.

ÖLÇÜLEN SORUN (Rol-1, A1 salt-okur 2026-09-24 20:59Z): `trades` tablosunda `kaynak='live_paper'`
28 satır; 09-13 TSK-182 TEK SEFERLİK geri dolumu (`ops/dolum_geri_dolum.py --uygula`) 22 satıra
giriş ailesini yazdı. O günden sonra kapanan 4 işlemin (SWKS·PANW·CRM·AMD) HİÇBİRİNDE giriş
ailesi yok — yalnız motorun çıkış yaması (`dolum_ts`, `alpaca_fill_price`). Bilgi motorda VAR
(bracket parent'ının kendi gövdesi, E2 `entry_execution.jsonl` de taşıyor) ama `trades` satırına
akmıyordu → EDG-2026-069 ADIM-0 kapısının `n_uygun`u canlı birikimle HİÇ dolmazdı.

SÖZLEŞME (bu dosya çiviler):
  G1  canlı kapanış yolunda (`reconcile_broker_state`) giriş ailesi yazılır; değerler bracket
      PARENT'ının KENDİ dolumundan (`loop._entry_fill_price` + parent `filled_at`) gelir — kapatma
      emrinden ya da TP/SL bacağından DEĞİL. Çıkış yaması zaten geçmiş satır da (canlıdaki 4
      satırın biçimi) iyileşir: yama çıkış kuyruğuna BAĞLI DEĞİLDİR.
  G2  dolu alan ASLA ezilmez (geri dolum aracının yasası); `dolum_kaynak` damgası korunur ve
      motor bu damgayı YAZMAZ (damga RETROAKTİF geri dolumun as-of kanıtıdır).
  G3  dolum bulunamazsa değer UYDURULMAZ: alan AÇILMAZ; neden tur özetinde ADIYLA sayılır.
  G4  tek-kaynak: alan adları `meridian/loop.py`de TEK kez tanımlıdır; `ops/dolum_geri_dolum.py`
      onları İTHAL eder (kaynak metin çivisi — AST, yorum/docstring değil).
  G5  çıkış ailesi davranışı DEĞİŞMEDİ (değerler + anahtar adları sözleşme sabitleriyle aynı).
  G6  kapsam: yalnız `live_paper` damgalı satır; tohum/damgasız satıra dokunulmaz, `kaynak`
      kolonu değişmez.
  G7  bedel: yama EK AĞ ÇAĞRISI yapmaz (reconcile'ın zaten çektiği emir penceresini okur).

YÖNTEM: ağa çıkılmaz — okuma uçları saplanır (v234 `ayna` fikstür deseni); her iddianın yanında
POZİTİF KONTROL vardır.
"""
from __future__ import annotations

import ast
import copy
import inspect
import pathlib

import pytest

from meridian import config, ledgerstamp, loop, store
from meridian.adapters import alpaca

REPO = pathlib.Path(__file__).resolve().parents[1]
BETIK = REPO / "ops" / "dolum_geri_dolum.py"

FAKE_KEY = "PKGIRISDOLUMV541FAKEKEY11"
FAKE_SECRET = "SKGIRISDOLUMV541FAKESECRET22"
D = "2026-09-15"
PID = "P-2026-09-14-SWKS"
GIRIS_TS = "2026-09-14T13:45:02.361641Z"     # canlı SWKS E2 satırının dolum_ts biçimi
CIKIS_TS = "2026-09-14T19:58:11.004Z"


@pytest.fixture
def ayna(sandbox_state, monkeypatch):
    """Sahte kimlik + `alpaca_paper`; taşıma SAĞLIKLI. Gerçek istemci hiç kurulmaz (v234 deseni)."""
    from meridian import secrets as secrets_mod
    monkeypatch.setenv("ALPACA_PAPER_KEY", FAKE_KEY)
    monkeypatch.setenv("ALPACA_PAPER_SECRET", FAKE_SECRET)
    secrets_mod.clear_cache()
    monkeypatch.setattr(config, "BROKER", "alpaca_paper")
    monkeypatch.setattr(alpaca, "paper_available", lambda: True)
    monkeypatch.setattr(alpaca, "transport", lambda: {"ok": True, "error": ""})
    yield sandbox_state
    secrets_mod.clear_cache()


def _events(token: str) -> list:
    return [e for e in store.read_jsonl("events.jsonl") if token in str(e)]


def _wire(monkeypatch, orders=(), positions=()):
    """Emir penceresi + pozisyonlar. Çağrı sayacı döner (G7 bedel ölçümü)."""
    sayac = {"orders": 0, "order_by_id": 0}

    def _orders(**k):
        sayac["orders"] += 1
        return [copy.deepcopy(o) for o in orders]

    def _order_by_id(oid):
        sayac["order_by_id"] += 1
        return None

    monkeypatch.setattr(alpaca, "orders", _orders)
    monkeypatch.setattr(alpaca, "positions", lambda: [dict(p) for p in positions])
    monkeypatch.setattr(alpaca, "order_by_id", _order_by_id)
    return sayac


def _satir(pid=PID, sym="SWKS", kaynak=ledgerstamp.LIVE_PAPER, **ek):
    """Canlı kapanmış işlem satırı (defterin İLERİ yolu `_persist_trade` gibi damgalı)."""
    row = {"id": "T00868", "plan_id": pid, "ticker": sym, "entry": 101.0, "exit": 99.0,
           "exit_reason": "stop", "ts_open": "2026-09-14", "ts_close": "2026-09-14", "qty": 25}
    if kaynak is not None:
        row[ledgerstamp.FIELD] = kaynak
    row.update(ek)
    store.append_jsonl("trades.jsonl", dict(row))
    return row


def _parent(pid=PID, sym="SWKS", status="filled", avg="101.5", filled_at=GIRIS_TS,
            leg_status="filled", leg_avg="99.2", leg_filled_at=CIKIS_TS):
    """Motor bracket PARENT'ı: kendi gövdesinde GİRİŞ dolumu, `legs[]`te dolan stop bacağı."""
    legs = [{"id": f"leg-sl-{sym}", "client_order_id": "alpaca-uuid-leg", "symbol": sym,
             "side": "sell", "type": "stop", "status": leg_status, "qty": "25",
             "filled_qty": "25" if leg_status == "filled" else "0",
             "filled_avg_price": leg_avg if leg_status == "filled" else None,
             "filled_at": leg_filled_at if leg_status == "filled" else None}]
    return {"id": f"id-giris-{sym}", "client_order_id": pid, "symbol": sym, "side": "buy",
            "type": "limit", "order_class": "bracket", "status": status, "qty": "25",
            "filled_qty": "25" if status == "filled" else "0",
            "filled_avg_price": avg, "filled_at": filled_at,
            "submitted_at": "2026-09-14T13:30:00Z", "legs": legs}


def _kapatma_emri(oid="close-ord-1", sym="SWKS", price="98.7", filled_at="2026-09-15T14:02:00Z"):
    """DELETE /positions'ın doğurduğu market SELL — coid Alpaca-üretimi (plan_id DEĞİL)."""
    return {"id": oid, "client_order_id": "9af1-alpaca-uuid", "symbol": sym, "side": "sell",
            "type": "market", "status": "filled", "qty": "25", "filled_qty": "25",
            "filled_avg_price": price, "filled_at": filled_at, "legs": [],
            "submitted_at": "2026-09-15T14:01:59Z"}


def _satiri_oku(pid=PID) -> dict:
    return [r for r in store.read_jsonl("trades.jsonl") if r.get("plan_id") == pid][-1]


def _reconcile(meta=None, kapananlar=()):
    meta = {"armed": []} if meta is None else meta
    out = loop.reconcile_broker_state(meta, D, [dict(k) for k in kapananlar],
                                      open_positions={}, fill_eq_now=100000.0)
    return out, meta


# =================================================================================================
# G1 · CANLI KAPANIŞ YOLUNDA GİRİŞ AİLESİ YAZILIR — değer emrin KENDİ dolumundan
# =================================================================================================
def test_G1_bacak_kapanisi_giris_ailesini_parent_dolumundan_yazar(ayna, monkeypatch):
    """UÇTAN UCA (dokunuş çıkışı, `bacak` kolu): bu turda kapanan işlem → reconcile sonrası satırda
    giriş ailesi PARENT'ın kendi `filled_avg_price`/`filled_at`inden; çıkış ailesi dolan bacaktan.
    İki aile AYRI değer taşır (bacak 99.2 @ CIKIS_TS ≠ giriş 101.5 @ GIRIS_TS) — adların
    karışmadığının pozitif kontrolü."""
    row = _satir()
    _wire(monkeypatch, orders=[_parent()])
    out, meta = _reconcile(kapananlar=[row])
    s = _satiri_oku()
    assert s.get(loop.DOLUM_ALAN_GIRIS_FIYAT) == 101.5, "giriş dolum fiyatı satıra akmadı (TSK-218 özü)"
    assert s.get(loop.DOLUM_ALAN_GIRIS_TS) == GIRIS_TS, "giriş dolum zamanı parent filled_at'i değil"
    assert s.get(loop.DOLUM_ALAN_CIKIS_FIYAT) == 99.2 and s.get(loop.DOLUM_ALAN_CIKIS_TS) == CIKIS_TS
    assert out["giris_dolum"]["yazilan"] == 1 and out["giris_dolum"]["n_alan"] == 2
    ev = _events("giris_dolum_yamalandi")
    assert ev and ev[-1].get("plan_id") == PID, "yazım olaysız — denetim izi yok"


def test_G1_karar_kapanisinda_giris_KAPATMA_EMRINDEN_okunmaz(ayna, monkeypatch):
    """`karar` kolu (DELETE kapatması): çıkış dolumu kapatma emrinden (98.7) gelir; GİRİŞ ailesi
    yine PARENT'tan (101.5). Kapatma emri de `_entry_fill_price`in okuyabildiği düz bir emirdir —
    yanlış emir seçilirse giriş 98.7 olurdu (pozitif kontrol)."""
    _satir()
    _wire(monkeypatch, orders=[_parent(leg_status="canceled"), _kapatma_emri()])
    meta = {"armed": [], loop.EXIT_FILL_KEY: {PID: {"ticker": "SWKS", "kaynak": "karar",
                                                    "order_id": "close-ord-1", "reason": "time_stop",
                                                    "since": D, "tries": 0}}}
    _reconcile(meta)
    s = _satiri_oku()
    assert s.get(loop.DOLUM_ALAN_CIKIS_FIYAT) == 98.7, "kurgu: karar çıkışı yamalanmalıydı"
    assert s.get(loop.DOLUM_ALAN_GIRIS_FIYAT) == 101.5, "giriş fiyatı kapatma emrinden okundu"
    assert s.get(loop.DOLUM_ALAN_GIRIS_TS) == GIRIS_TS


def test_G1_cikis_yamasi_zaten_gecmis_satir_da_iyilesir(ayna, monkeypatch):
    """CANLIDAKİ 4 SATIRIN BİÇİMİ (seq 868-871): çıkış yaması koşmuş (`alpaca_fill_price` +
    `dolum_ts` dolu), kuyruk BOŞ, giriş ailesi YOK. Yama çıkış kuyruğuna bağlı olsaydı bu satırlar
    asla iyileşmezdi; parent pencerede durduğu sürece HER tur yeniden denenir (kendi kendini
    iyileştiren desen, `_defter_teyit_yamasi` emsali)."""
    _satir(alpaca_fill_price=99.2, dolum_ts=CIKIS_TS, mirror_divergence=0.00202)
    _wire(monkeypatch, orders=[_parent()])
    out, meta = _reconcile()
    s = _satiri_oku()
    assert meta.get(loop.EXIT_FILL_KEY, {}) == {}, "kurgu: çıkış kuyruğu boş olmalıydı"
    assert s.get(loop.DOLUM_ALAN_GIRIS_FIYAT) == 101.5
    assert s.get(loop.DOLUM_ALAN_GIRIS_TS) == GIRIS_TS
    assert s.get(loop.DOLUM_ALAN_CIKIS_FIYAT) == 99.2 and s.get(loop.DOLUM_ALAN_CIKIS_TS) == CIKIS_TS


def test_G1_ozet_broker_reconcile_artefaktina_duser(ayna, monkeypatch):
    """YASA 6: tur özeti `broker_reconcile.json`a yazılır — okuyucu /api/alpaca `reconcile`
    passthrough'u (rc'nin tamamını yayar), `exit_fill`/`entry_slippage` ile aynı kablo."""
    _satir()
    _wire(monkeypatch, orders=[_parent()])
    _reconcile()
    rc = store.read_json("broker_reconcile.json", {})
    assert rc.get("giris_dolum", {}).get("yazilan") == 1


def test_G1_idempotent_ikinci_tur_yazmaz_olay_basmaz(ayna, monkeypatch):
    """Dolu satır ikinci turda aday DEĞİL: yazım yok, ikinci olay yok."""
    _satir()
    _wire(monkeypatch, orders=[_parent()])
    _reconcile()
    out2, _ = _reconcile()
    assert out2["giris_dolum"]["yazilan"] == 0
    assert len(_events("giris_dolum_yamalandi")) == 1


# =================================================================================================
# G2 · DOLU ALAN EZİLMEZ · `dolum_kaynak` KORUNUR ve MOTOR YAZMAZ
# =================================================================================================
def test_G2_dolu_giris_alanlari_EZILMEZ_damga_korunur(ayna, monkeypatch):
    """TSK-182 geri dolumunun yazdığı satır: broker farklı değer verse bile iki alan ve as-of
    damgası AYNEN kalır (geri dolum aracının yasası — ilk ölçüm kanıttır)."""
    damga = "alpaca_orders_geri_dolum_2026-09-13T21:18:59+00:00"
    _satir(**{loop.DOLUM_ALAN_GIRIS_TS: "2026-09-14T13:44:00Z",
              loop.DOLUM_ALAN_GIRIS_FIYAT: 100.0, loop.DOLUM_ALAN_DAMGA: damga})
    _wire(monkeypatch, orders=[_parent()])
    out, _ = _reconcile()
    s = _satiri_oku()
    assert s[loop.DOLUM_ALAN_GIRIS_TS] == "2026-09-14T13:44:00Z", "dolu giriş zamanı EZİLDİ"
    assert s[loop.DOLUM_ALAN_GIRIS_FIYAT] == 100.0, "dolu giriş fiyatı EZİLDİ"
    assert s[loop.DOLUM_ALAN_DAMGA] == damga, "geri dolum damgası değişti"
    assert out["giris_dolum"]["yazilan"] == 0 and not _events("giris_dolum_yamalandi")


def test_G2_yarim_dolu_satirda_yalniz_BOS_alan_yazilir(ayna, monkeypatch):
    """Fiyat dolu (farklı değerle), zaman boş: YALNIZ zaman yazılır, fiyat ezilmez; damga korunur."""
    damga = "alpaca_orders_geri_dolum_2026-09-13T21:18:59+00:00"
    _satir(**{loop.DOLUM_ALAN_GIRIS_FIYAT: 100.0, loop.DOLUM_ALAN_DAMGA: damga})
    _wire(monkeypatch, orders=[_parent()])
    out, _ = _reconcile()
    s = _satiri_oku()
    assert s[loop.DOLUM_ALAN_GIRIS_FIYAT] == 100.0, "dolu fiyat EZİLDİ"
    assert s.get(loop.DOLUM_ALAN_GIRIS_TS) == GIRIS_TS, "BOŞ zaman alanı doldurulmadı"
    assert s[loop.DOLUM_ALAN_DAMGA] == damga
    assert out["giris_dolum"]["n_alan"] == 1


def test_G2_motor_dolum_kaynak_damgasi_YAZMAZ(ayna, monkeypatch):
    """`dolum_kaynak` RETROAKTİF geri dolumun as-of kanıtıdır (önek `alpaca_orders_geri_dolum_`).
    Motor canlı yazımda onu basarsa, sonradan çıkış alanlarını dolduran geri dolum "var olan damga
    korunur" kuralıyla motor damgasını taşır ve geri doldurulan alanlar motor yazımı gibi görünür."""
    _satir()
    _wire(monkeypatch, orders=[_parent()])
    _reconcile()
    assert loop.DOLUM_ALAN_DAMGA not in _satiri_oku(), "motor geri dolum damgası bastı"


# =================================================================================================
# G3 · DOLUM YOKSA UYDURULMAZ — alan AÇILMAZ, neden özet sayacında ADIYLA
# =================================================================================================
def test_G3_parent_pencerede_yoksa_alan_ACILMAZ(ayna, monkeypatch):
    """Parent emir penceresinde yok (eski satır / kırpık pencere): iki anahtar da AÇILMAZ — `None`
    yazmak "taşıyan" sayımında sahte doluluk üretirdi (`.get` None ≠ anahtar yok)."""
    _satir()
    _wire(monkeypatch, orders=[])
    out, _ = _reconcile()
    s = _satiri_oku()
    assert loop.DOLUM_ALAN_GIRIS_TS not in s and loop.DOLUM_ALAN_GIRIS_FIYAT not in s
    assert out["giris_dolum"]["pencerede_yok"] == 1 and out["giris_dolum"]["yazilan"] == 0


def test_G3_dolmamis_parent_fiyat_ve_zaman_UYDURMAZ(ayna, monkeypatch):
    """Parent görünür ama dolum yok (`canceled`, fiyat/zaman boş): iki alan da AÇILMAZ, satırın
    `entry`si ikame EDİLMEZ (iç simülasyon fiyatı broker olgusu değildir)."""
    _satir()
    _wire(monkeypatch, orders=[_parent(status="canceled", avg=None, filled_at=None,
                                       leg_status="canceled")])
    out, _ = _reconcile()
    s = _satiri_oku()
    assert loop.DOLUM_ALAN_GIRIS_FIYAT not in s and loop.DOLUM_ALAN_GIRIS_TS not in s
    assert out["giris_dolum"]["fiyat_okunamadi"] == 1 and out["giris_dolum"]["zaman_bos"] == 1


def test_G3_filled_at_bossa_zaman_ACILMAZ_fiyat_yazilir(ayna, monkeypatch):
    """Fiyat okunur ama `filled_at` boş: fiyat yazılır, zaman anahtarı AÇILMAZ (geri dolum aracı
    ile aynı: alanlar bağımsız, zaman `ts_open`/`ts`ten İKAME EDİLMEZ)."""
    _satir()
    _wire(monkeypatch, orders=[_parent(filled_at=None)])
    out, _ = _reconcile()
    s = _satiri_oku()
    assert s.get(loop.DOLUM_ALAN_GIRIS_FIYAT) == 101.5
    assert loop.DOLUM_ALAN_GIRIS_TS not in s, "zaman uyduruldu / None anahtarı açıldı"
    assert out["giris_dolum"]["zaman_bos"] == 1


def test_G3_defter_yazimi_duserse_reconcile_ayakta_ve_sesli(ayna, monkeypatch):
    """YASA 4: yama yazımı istisna fırlatırsa reconcile'ın kalanı ayakta kalır ve düşüş OLAYLIDIR."""
    _satir()
    _wire(monkeypatch, orders=[_parent()])
    gercek = store.update_jsonl

    def _patlayan(name, fn):
        if getattr(fn, "__qualname__", "").startswith("_giris_dolum_yamasi"):
            raise OSError("disk dolu (sahte)")
        return gercek(name, fn)

    monkeypatch.setattr(store, "update_jsonl", _patlayan)
    out, _ = _reconcile()
    assert out["checked"] is True, "yama düşüşü reconcile'ı düşürdü"
    ev = _events("giris_dolum_yamasi_dustu")
    assert ev and "OSError" in str(ev[-1].get("hata")), "düşüş sessiz"


# =================================================================================================
# G4 · TEK-KAYNAK — alan adları motorda TEK kez; ops aracı İTHAL eder
# =================================================================================================
_ADLAR = ("giris_dolum_ts", "giris_dolum_fiyat", "dolum_kaynak")


def _sabit_dizgeler(yol: pathlib.Path) -> list[str]:
    """Modüldeki TAM-EŞİT dizge sabitleri (docstring/yorum içindeki ANMA sayılmaz: docstring
    tek bir uzun sabittir, adla TAM eşit olmaz)."""
    agac = ast.parse(yol.read_text(encoding="utf-8"))
    return [n.value for n in ast.walk(agac) if isinstance(n, ast.Constant) and isinstance(n.value, str)]


def test_G4_ops_araci_alan_adlarini_ELLE_yazmaz():
    """`ops/dolum_geri_dolum.py` beş dolum alan adını ve fiyat ondalığını motordan ithal eder;
    kaynakta ad dizgesi TAM-EŞİT sabit olarak GEÇMEZ (ikinci kopya = sessiz ayrışma adayı)."""
    sabitler = _sabit_dizgeler(BETIK)
    for ad in _ADLAR + ("dolum_ts", "alpaca_fill_price"):
        assert ad not in sabitler, f"ops aracı `{ad}` adını ELLE yazıyor — motordan ithal etmeli"
    from tests.conftest import betikten_modul_yukle
    m = betikten_modul_yukle(BETIK, "dolum_geri_dolum_v541")
    assert (m.ALAN_GIRIS_TS, m.ALAN_GIRIS_FIYAT, m.ALAN_CIKIS_TS, m.ALAN_CIKIS_FIYAT, m.ALAN_DAMGA) == \
        (loop.DOLUM_ALAN_GIRIS_TS, loop.DOLUM_ALAN_GIRIS_FIYAT, loop.DOLUM_ALAN_CIKIS_TS,
         loop.DOLUM_ALAN_CIKIS_FIYAT, loop.DOLUM_ALAN_DAMGA)
    assert m.FIYAT_ONDALIK == loop.DOLUM_FIYAT_ONDALIK


def test_G4_motor_kaynaginda_giris_adlari_TEK_tanim():
    """Motorda giriş ailesi + damga adı TAM BİR kez (sabit tanımı) geçer — yama kodu sabiti kullanır,
    ikinci bir dizge kopyası yok. Tanımın değerleri geri dolum aracının 22 satırlık defteriyle AYNI."""
    sabitler = _sabit_dizgeler(REPO / "meridian" / "loop.py")
    for ad in _ADLAR:
        assert sabitler.count(ad) == 1, f"`{ad}` loop.py'de {sabitler.count(ad)} kez (beklenen 1)"
    assert (loop.DOLUM_ALAN_GIRIS_TS, loop.DOLUM_ALAN_GIRIS_FIYAT, loop.DOLUM_ALAN_DAMGA) == _ADLAR


# =================================================================================================
# G5 · ÇIKIŞ AİLESİ DAVRANIŞI DEĞİŞMEDİ
# =================================================================================================
def test_G5_cikis_yamasi_ayni_degerleri_ayni_anahtarlara_yazar(ayna, monkeypatch):
    """Çıkış yaması (`bacak`) önceki sözleşmesiyle: fiyat 4, sapma 5 ondalık; zaman dolan bacaktan;
    anahtarlar `DOLUM_ALAN_CIKIS_*` sabitleriyle AYNI (türetme + ayrışma çivisi); kuyruk/özet aynı."""
    row = _satir(exit=99.0)
    _wire(monkeypatch, orders=[_parent(leg_avg="99.21")])
    out, meta = _reconcile(kapananlar=[row])
    s = _satiri_oku()
    assert s[loop.DOLUM_ALAN_CIKIS_FIYAT] == 99.21 == s["alpaca_fill_price"]
    assert s[loop.DOLUM_ALAN_CIKIS_TS] == CIKIS_TS == s["dolum_ts"]
    assert s["mirror_divergence"] == round(abs(99.21 - 99.0) / 99.0, 5)
    assert out["exit_fill"] == {"bekleyen": 0, "yamalanan": 1, "vazgecilen": 0}
    assert meta[loop.EXIT_FILL_KEY] == {}


def test_G5_giris_yamasi_cikis_alanlarina_DOKUNMAZ(ayna, monkeypatch):
    """Çıkış alanları BOŞ ve kuyruk boş bir satırda giriş yaması yalnız GİRİŞ ailesini açar —
    çıkış alanları çıkış yamasının işidir (iki aile karışmaz)."""
    _satir()
    _wire(monkeypatch, orders=[_parent()])
    _reconcile()
    s = _satiri_oku()
    assert s.get(loop.DOLUM_ALAN_GIRIS_FIYAT) == 101.5, "kurgu: giriş yazılmalıydı"
    assert loop.DOLUM_ALAN_CIKIS_FIYAT not in s and loop.DOLUM_ALAN_CIKIS_TS not in s


# =================================================================================================
# G6 · KAPSAM — yalnız live_paper; `kaynak` kolonu değişmez
# =================================================================================================
@pytest.mark.parametrize("kaynak", [ledgerstamp.REPLAY_SEED, None])
def test_G6_tohum_ve_damgasiz_satira_DOKUNULMAZ(ayna, monkeypatch, kaynak):
    """Tohum/damgasız satır canlı kanıt değildir — plan kimliği emirle eşleşse bile yazılmaz."""
    _satir(kaynak=kaynak)
    _wire(monkeypatch, orders=[_parent()])
    _reconcile()
    s = _satiri_oku()
    assert loop.DOLUM_ALAN_GIRIS_FIYAT not in s and loop.DOLUM_ALAN_GIRIS_TS not in s


def test_G6_kaynak_damgasi_DEGISMEZ(ayna, monkeypatch):
    _satir()
    _wire(monkeypatch, orders=[_parent()])
    _reconcile()
    s = _satiri_oku()
    assert s[ledgerstamp.FIELD] == ledgerstamp.LIVE_PAPER
    assert s.get(loop.DOLUM_ALAN_GIRIS_FIYAT) == 101.5, "kurgu: yazım olmalıydı"


# =================================================================================================
# G7 · BEDEL — EK AĞ ÇAĞRISI YOK
# =================================================================================================
def test_G7_yama_ek_ag_cagrisi_YAPMAZ(ayna, monkeypatch):
    """Reconcile'ın emir çekme sayısı değişmez (1 sayfa) ve tekil GET açılmaz — yama yalnız
    zaten çekilmiş `by_coid`i okur. Kaynak da hiçbir broker ucuna dokunmaz."""
    _satir()
    sayac = _wire(monkeypatch, orders=[_parent()])
    _reconcile()
    assert _satiri_oku().get(loop.DOLUM_ALAN_GIRIS_FIYAT) == 101.5, "kurgu: yazım olmalıydı"
    assert sayac == {"orders": 1, "order_by_id": 0}
    src = inspect.getsource(loop._giris_dolum_yamasi)
    for yasak in ("alpaca", "httpx", "submit", "cancel", ".delete(", ".post("):
        assert yasak not in src, f"giriş yaması broker ucuna dokunuyor: {yasak}"
