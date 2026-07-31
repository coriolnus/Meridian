"""adapters/alpaca.py — Alpaca broker adapter. PAPER by default. The LIVE path is refused unless
BOTH env flags are hand-set (MERIDIAN_MODE=live AND MERIDIAN_I_ACCEPT_RISK=true) AND goal.limits
.autonomy_level >= 1 (enforced in guard.py). alpaca-py is imported lazily so the engine runs at L0
without it installed. PnL/fills that count are ALWAYS the internal broker.py simulator's; this module
is the MIRROR. But note: with MERIDIAN_BROKER=alpaca_paper (serve.sh's default, and what runs today)
the mirror path IS live every cycle — submit_plan() is called from loop.py on every armed plan. The
old docstring claimed this module "is only reached once the live path is enabled"; that was false and
hid the fact that a mirror failure can drop a real armed plan (audit 2026-07-21).

YAZILI VARSAYIMLAR (denetim 2026-07-21 — her biri artık bir kontrol ya da testle bağlı):
  A1 read-only uçlar (account/positions/orders) HİÇBİR ZAMAN istisna fırlatmaz; hata durumunda
     None/[] döner. Bu yüzden çağıranın try/except'i ÖLÜ KOD'dur ve "broker ulaşılamıyor" ile
     "hiç emir yok" ayırt edilemez → `transport()` sağlık kaydı bu ayrımı taşır. Çağıran, boş
     listeye bakıp mutabakat kararı vermeden ÖNCE transport()["ok"] kontrol etmelidir.
  A2 client_order_id == iç plan kimliği ve ENGINE_COID_PREFIX ile başlar. Mutabakat "motor yetimi"
     tespitini bu önekle yapar; önek kayarsa yetimler sessizce 'external' altında saklanır.
  A3 Bu hesap YALNIZ motora ait DEĞİL — operatörün kendi pozisyonları (bugün: NVDA) ve elle
     girdiği emirler aynı kağıt hesapta. Motor SAHİBİ OLMADIĞI emri iptal edemez / pozisyonu
     düzleştiremez (cancel_open_entries önek süzgeci + close_all onay jetonu).
  A4 Koruma (stop) asla gevşetilmez: replace_order_stop yalnız YUKARI. Eskiden bunu yalnız çağıran
     katman garanti ediyordu; artık sınırın kendisi reddediyor.
"""
from __future__ import annotations
import datetime as _dt
import httpx
from .. import secrets, config

PAPER_BASE = "https://paper-api.alpaca.markets"
_SCHEME_WARNED = False   # taşıma yükseltmesi süreç başına BİR kez duyurulur (gürültü değil sinyal)

# ===== MARKET-DATA STREAM (Faz 2) — TRADING host'tan AYRI, SABİT host =====
# Piyasa verisi WS'i trading host'uyla KARIŞTIRILMAZ: bu SABİT bir data host'udur, operatör-ayarlı
# uç nokta YOKTUR → kilitlenecek girdi ve audit-#51 kimlik-sızıntı vektörü de yoktur (o, dashboard-
# ayarlı trading host'una özgü). READ-ONLY veri; bu yoldan gerçek-para emri geçemez.
DATA_STREAM_HOST = "stream.data.alpaca.markets"
_DATA_FEEDS = ("iex", "sip", "test")   # iex ücretsiz/varsayılan · sip entitlement ister · test = FAKEPACA


def data_ws_url(feed: str = "iex") -> str:
    """wss://stream.data.alpaca.markets/v2/{feed}. Bilinmeyen feed → iex + `marketstream_bad_feed`."""
    if feed not in _DATA_FEEDS:
        try:
            from .. import obs
            obs.warn("marketstream_bad_feed", gorulen=str(feed)[:20],
                     detail=f"bilinmeyen feed — güvenli varsayılan iex'e dönüldü ({'/'.join(_DATA_FEEDS)})")
        except Exception:  # sessiz-yutma: uyarı kanalı düştü — güvenli varsayılana dönüş kararını düşürmez
            pass
        feed = "iex"
    return f"wss://{DATA_STREAM_HOST}/v2/{feed}"

# A2: iç plan kimliklerinin ön eki (loop.py `P-{tarih}-{ticker}`). Mutabakattaki "motor yetimi"
# tespiti ve aşağıdaki sahiplik süzgeci AYNI sabiti kullanır — iki yerde elle yazılırsa kayarlar.
ENGINE_COID_PREFIX = "P-"

# close_all() için açık onay jetonu — kaza/otomasyon ile düzleştirmeyi imkânsız kılar (A3).
CLOSE_ALL_CONFIRM = "FLATTEN-PAPER"


def is_engine_order(o: dict) -> bool:
    """Bu emri MOTOR mu gönderdi? (A3 sahiplik sınırı) Operatörün elle girdiği emirlerde
    client_order_id ya yoktur ya da Alpaca'nın kendi ürettiği UUID'dir — önek tutmaz."""
    return str((o or {}).get("client_order_id") or "").startswith(ENGINE_COID_PREFIX)


# --- A1: taşıma (transport) sağlık kaydı ------------------------------------------------------
# Bu modülün okuma uçları istisnayı YUTAR (çağıranların hepsi liste/None bekliyor). Yutulan hata
# görünmez olursa "API çöktü" ile "hiç emir yok" aynı şeye benzer ve mutabakat, canlı pozisyonları
# 'Alpaca'da kayıp' diye alarma boğar. Kayıt, yutulan hatayı çağırana taşır.
_TRANSPORT = {"ok": True, "error": "", "at": None, "calls": 0, "fails": 0, "consecutive_fails": 0}


def _note(ok: bool, err: str = "") -> None:
    _TRANSPORT["calls"] += 1
    _TRANSPORT["at"] = _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")
    if ok:
        _TRANSPORT["ok"], _TRANSPORT["error"], _TRANSPORT["consecutive_fails"] = True, "", 0
    else:
        _TRANSPORT["ok"], _TRANSPORT["error"] = False, err[:200]
        _TRANSPORT["fails"] += 1
        _TRANSPORT["consecutive_fails"] += 1


def transport() -> dict:
    """Son REST çağrısının taşıma sağlığı. `ok=False` → dönen [] / None VERİ DEĞİL, ARIZADIR."""
    return dict(_TRANSPORT)


def endpoint() -> str:
    """Operatörün girdiği taban — ŞEMASI NORMALLEŞTİRİLMİŞ olarak.

    Panodaki alan şemasız bir örnek gösteriyor ("Boş bırakılırsa paper-api.alpaca.markets
    kullanılır", web/app.js), yani ŞEMASIZ DEĞER BEKLENEN operatör girdisidir — hata değil. Ham
    haliyle döndürmek iki yolu birden bozuyordu: httpx `_account_url()`u protokolsüz reddeder ve
    mirror_stream'in https→wss dönüşümü tutmayıp her bağlantı denemesinde `mirror_stream_bad_base`
    yedeğine düşer (güvenlik ağı NORMAL yol hâline gelir ve gerçekten yanlış bir hostu gizler).

    Yalnız EKSİK şema tamamlanır. Açıkça yazılmış bir şema — yanlış olsa bile — KORUNUR, ki gerçek
    yanlış-yapılandırma sessizce 'düzeltilmiş' gibi görünmesin ve yedek/uyarı yolu canlı kalsın.
    Host DENETİMİ burada DEĞİL: kilit `_paper_base()`te durur, buradaki normalleştirme onu
    zayıflatmaz (kilit zaten aynı normalleştirmeyi yaparak host okuyordu; artık DÖNEN değer de
    doğrulanan değerle aynı biçimde)."""
    raw = (secrets.get("ALPACA_PAPER_ENDPOINT") or PAPER_BASE).strip().rstrip("/")
    if not raw:                       # yalnız boşluk/"/" girilmiş — yok sayılır, varsayılana dönülür
        return PAPER_BASE
    return raw if "://" in raw else f"https://{raw}"


def _account_url() -> str:
    """/v2/account, tolerating an endpoint the operator entered either as the host root or already
    including the /v2 version segment (so we never double it → /v2/v2/account)."""
    base = endpoint()
    if base.endswith("/v2"):
        base = base[:-3]
    return f"{base.rstrip('/')}/v2/account"


def paper_available() -> bool:
    """Key is required; secret is optional (some setups expose only an endpoint + key)."""
    return secrets.present("ALPACA_PAPER_KEY")


def ping() -> dict:
    """Live reachability + auth check against the PAPER account endpoint. A read-only GET /v2/account —
    does NOT place, enable, or arm any order (that path stays gated behind the two live flags). Sends the
    key+secret headers when both are present, else a Bearer token with the key alone. Returns only
    {ok, detail}; never a secret. 401/403 => wrong/insufficient credentials."""
    if not paper_available():
        return {"ok": False, "detail": "Alpaca Key girilmemiş"}
    key = secrets.get("ALPACA_PAPER_KEY") or ""
    sec = secrets.get("ALPACA_PAPER_SECRET")
    headers = ({"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": sec} if sec
               else {"Authorization": f"Bearer {key}"})
    try:
        r = httpx.get(_account_url(), timeout=12.0, headers=headers)
        if r.status_code in (401, 403):
            hint = "anahtar geçersiz/yetkisiz" if sec else "anahtar reddedildi — Alpaca genelde Secret de ister"
            return {"ok": False, "detail": hint}
        r.raise_for_status()
        acct = r.json()
        return {"ok": True, "detail": f"bağlandı · kağıt hesap {acct.get('status', '?')}"}
    except httpx.HTTPStatusError as e:
        return {"ok": False, "detail": f"HTTP {e.response.status_code}"}
    except Exception as e:
        return {"ok": False, "detail": f"bağlanılamadı ({type(e).__name__})"}


def _client(paper: bool):
    try:
        from alpaca.trading.client import TradingClient  # optional 'live'/paper extra
    except ImportError as e:
        raise RuntimeError("alpaca-py not installed — `uv sync --extra live` to enable Alpaca fills") from e
    key = secrets.get("ALPACA_PAPER_KEY")
    sec = secrets.get("ALPACA_PAPER_SECRET")
    if not key or not sec:
        raise RuntimeError("Alpaca paper keys absent")
    return TradingClient(key, sec, paper=paper)


def live_guard() -> None:
    """Hard refusal of the live path unless every gate is satisfied. Called before any live client."""
    if not config.live_enabled():
        raise RuntimeError("LIVE refused: set MERIDIAN_MODE=live AND MERIDIAN_I_ACCEPT_RISK=true by hand")
    if config.limits()["autonomy_level"] < 1:
        raise RuntimeError("LIVE refused: goal.limits.autonomy_level < 1 (promotion gates unmet, §8)")


# ÇIKARILDI 2026-07-30 (temizlik turu): `paper_client()` — `_client(paper=True)` sarmalayıcısı.
# ÇAĞIRAN TARAMASI: repo genelinde (meridian/ + tests/ + ops/ + deploy/ + skills/) TEK eşleşme
# tanımın kendisiydi. Kağıt yürütme bu modülde SDK'yı hiç kullanmıyor — REST/httpx yolundan gidiyor
# (bkz. aşağıdaki "PAPER execution (REST, httpx, no SDK)" bölümü), yani sarmalayıcının üretimde
# doldurduğu bir boşluk yoktu. `_client` KORUNDU: `live_client`ın tek dayanağı odur ve o yol
# operatör-kalemidir (ROADMAP §6).
# GERİ-AL: `def paper_client(): return _client(paper=True)` — bu yorumun yerine.


def live_client():
    """LIVE client — guarded. Only reachable when the human has flipped both flags and passed §8."""
    live_guard()
    return _client(paper=False)


def status() -> dict:
    return {"provider": "Alpaca", "paper_available": paper_available(),
            "live_enabled": config.live_enabled(), "autonomy_level": config.limits()["autonomy_level"],
            "reason": "" if paper_available() else "Alpaca paper keys absent — engine uses internal broker"}


# ================= PAPER execution (REST, httpx, no SDK) — HARD-LOCKED to the paper endpoint =================
def _paper_base() -> str:
    """ALWAYS a paper endpoint. Hard safety lock: even if the operator's ALPACA_PAPER_ENDPOINT somehow
    pointed at a live URL, this forces paper-api.alpaca.markets, so this module can NEVER place a
    real-money order. Real-money trading lives on a SEPARATE, flag-gated path (live_client), not here."""
    base = endpoint()
    # HOSTNAME check, not substring: 'paper-api.alpaca.markets.evil.example.com' or a path segment
    # containing the string passed the old `in` test and would receive the operator's API key headers
    # (audit #51 credential-leak vector via the dashboard-settable endpoint).
    semali = "://" in base
    try:
        from urllib.parse import urlparse
        _p = urlparse(base if semali else f"https://{base}")
        host, sema, yol = _p.hostname or "", _p.scheme, _p.path
    except Exception:  # sessiz-yutma: host boş kalırsa BİR SONRAKİ satır uçnoktayı güvenli PAPER_BASE'e geri düşürür — sessizlik burada güvenli tarafa kapanıyor, kimlik başlıkları yabancı hosta gitmiyor
        host, sema, yol = "", "", ""
    if host != "paper-api.alpaca.markets":
        base = PAPER_BASE
    elif not semali or sema not in ("https", "wss"):
        # TAŞIMA SIKILAŞTIRMASI — host kilidinin ikizi. Kilit "hangi makineye" sorusunu yanıtlar;
        # bu satır "hangi taşımayla" sorusunu: `http://paper-api.alpaca.markets` doğru hosttur ama
        # AÇIK METİNDİR ve `_headers()` API anahtarlarını o bağlantıya koyar. Doğru makineye açık
        # metinle anahtar göndermek, yanlış makineye göndermenin daha sessiz hâlidir.
        #
        # Şema EKSİKLİĞİ artık yukarıda `endpoint()`te tamamlanıyor; burası savunmanın ikinci katı
        # (o normalleştirme değişir/atlanırsa kilit yine de sızdırmaz). Kilit ZAYIFLAMAZ: yabancı
        # host hâlâ PAPER_BASE'e zorlanır, burada yalnız taşıma yükseltilir.
        #
        # SESSİZCE DÜZELTMEZ: `endpoint()` açık yazılmış yanlış şemayı bilerek KORUYOR ki gerçek bir
        # yanlış-yapılandırma görünür kalsın. O karara saygı, düzeltmeyi geri almakla değil, SESLİ
        # yapmakla gösterilir — süreç başına bir kez (her REST çağrısında değil: 32/gün'lük gürültü
        # tam da bu denetimin kovaladığı şeydi).
        global _SCHEME_WARNED
        if not _SCHEME_WARNED:
            _SCHEME_WARNED = True
            try:
                from .. import obs
                obs.warn("alpaca_endpoint_scheme_upgraded", gorulen=f"{sema or 'ŞEMA-YOK'}://{host}",
                         detail="uç nokta https değildi — anahtarlar açık metne çıkmasın diye "
                                "https'e yükseltildi; yapılandırmayı düzeltin")
            except Exception:  # sessiz-yutma: kayıt kanalı düştü — ikinci kanal yok; uyarı denemesi taşıma kararını düşüremez
                pass
        base = f"https://{host}{yol}"
    if base.endswith("/v2"):
        base = base[:-3]
    return base.rstrip("/")


def _headers() -> dict:
    return {"APCA-API-KEY-ID": secrets.get("ALPACA_PAPER_KEY") or "",
            "APCA-API-SECRET-KEY": secrets.get("ALPACA_PAPER_SECRET") or "",
            "Content-Type": "application/json"}


def account() -> dict | None:
    """None => hesap OKUNAMADI. Bu 'öz sermaye 0' demek DEĞİLDİR; çağıran varsayılan bir sermayeye
    düşmeden önce transport()["ok"]'e bakmalı (aksi halde hayali 100k üzerinden boyutlandırır)."""
    try:
        r = httpx.get(f"{_paper_base()}/v2/account", headers=_headers(), timeout=15)
        r.raise_for_status()
        _note(True)
        return r.json()
    except Exception as e:
        _note(False, f"account: {type(e).__name__}: {e}")
        return None


def positions() -> list:
    """[] => ya gerçekten pozisyon yok YA DA API ulaşılamadı; ayrımı transport() taşır (A1)."""
    try:
        r = httpx.get(f"{_paper_base()}/v2/positions", headers=_headers(), timeout=15)
        r.raise_for_status()
        _note(True)
        return r.json()
    except Exception as e:
        _note(False, f"positions: {type(e).__name__}: {e}")
        return []


def orders(status: str = "open", limit: int = 50, nested: bool = False) -> list:
    """List orders. nested=True asks Alpaca to return each bracket as ONE parent order carrying its
    take-profit/stop-loss children in a `legs[]` array. WITHOUT it, the list endpoint flattens a bracket
    into 3 separate top-level orders (parent + 2 children), each with legs=[] — so exit_fill_price(), which
    reads the parent's legs, would find nothing and the reconciler's divergence audit would silently no-op.
    The reconciler MUST pass nested=True (verified against the live paper account: flat→3 rows/legs=0,
    nested→1 parent/legs=2)."""
    try:
        params = {"status": status, "limit": limit, "direction": "desc"}
        if nested:
            params["nested"] = "true"
        r = httpx.get(f"{_paper_base()}/v2/orders", headers=_headers(), params=params, timeout=15)
        r.raise_for_status()
        _note(True)
        return r.json()
    except Exception as e:
        # A1: [] dönüyoruz ama SESSİZ değil — mutabakat bunu 'emir yok' sanıp her açık pozisyonu
        # 'Alpaca'da kayıp' diye alarma boğuyordu (denetim 2026-07-21).
        _note(False, f"orders: {type(e).__name__}: {e}")
        return []


def submit_bracket(symbol: str, qty: int, entry_stop: float, take_profit: float, stop_loss: float,
                   client_order_id: str | None = None, entry_limit: float | None = None,
                   entry_type: str = "stop_limit", tif: str | None = None) -> dict:
    """Submit a PAPER bracket BUY with an attached take-profit + stop-loss so Alpaca manages the whole
    trade. Returns {ok, order|detail}. Never places a real-money order. client_order_id (the local plan
    id) is the JOIN KEY the reconciler uses to match this order back to the internal plan/trade and
    audit divergence.

    E1 (WP-E, 2026-07-31) — GİRİŞ BACAĞI ARTIK MARKETABLE STOP-LIMIT / LIMIT (yasa: `broker.entry_law`):
      * `stop_limit` : stop=entry_stop, limit=entry_limit  → tetik teyidi KORUNUR, ödenen fiyat TAVANLI.
      * `limit`      : yalnız limit=entry_limit            → gap dalı (gönderim anında fiyat zaten
                       tetiğin üstünde; buy-stop bu durumda GEÇERSİZ ve Alpaca "stop price must be
                       greater than current price" ile reddediyordu — 95/95 satırın kökü).
      * `stop`       : ESKİ davranış. Yalnız `entry_limit` verilmediğinde kalır (geriye dönük yol);
                       yeni çağıran bu dala girmez.
    TIF varsayılanı DAY (GTC'den değişim, kart EXE-2026-001): GTC emri bir sonraki seansa sinyal barına
    sabitlenmiş BAYAT bir tetik taşır."""
    if qty <= 0:
        return {"ok": False, "detail": "qty<=0"}
    from ..broker import ENTRY_TIF
    body = {"symbol": symbol, "qty": str(int(qty)), "side": "buy",
            "time_in_force": str(tif or ENTRY_TIF).lower(), "order_class": "bracket",
            "take_profit": {"limit_price": round(float(take_profit), 2)},
            "stop_loss": {"stop_price": round(float(stop_loss), 2)}}
    if entry_limit is not None and str(entry_type) == "limit":
        body.update({"type": "limit", "limit_price": round(float(entry_limit), 2)})
    elif entry_limit is not None:
        body.update({"type": "stop_limit", "stop_price": round(float(entry_stop), 2),
                     "limit_price": round(float(entry_limit), 2)})
    else:
        body.update({"type": "stop", "stop_price": round(float(entry_stop), 2)})
    if client_order_id:
        body["client_order_id"] = str(client_order_id)
    # A2: birleştirme anahtarı olmadan gönderilen emir, mutabakat için GÖRÜNMEZDİR — dolarsa
    # 'motor yetimi' bile sayılmaz, operatörün kendi pozisyonu gibi 'external' altına düşer.
    coid_ok = str(body.get("client_order_id", "")).startswith(ENGINE_COID_PREFIX)
    try:
        r = httpx.post(f"{_paper_base()}/v2/orders", headers=_headers(), json=body, timeout=15)
        if not coid_ok:
            from .. import obs
            obs.warn("alpaca_coid_unjoinable", symbol=symbol, coid=str(body.get("client_order_id", "")))
        _note(True)                      # cevap geldi: 4xx bile olsa broker ULAŞILABİLİR
        if r.status_code >= 400:
            try:
                return {"ok": False, "detail": r.json().get("message", f"HTTP {r.status_code}"),
                        "reachable": True}
            except Exception:  # sessiz-yutma: ağ/sağlayıcı hatası bu yolun NORMAL hâli; çağıran boş sonuç üzerinden yedek kaynağa düşer ve kaynak seçimi ayrıca kaydedilir
                return {"ok": False, "detail": f"HTTP {r.status_code}", "reachable": True}
        return {"ok": True, "order": r.json()}
    except Exception as e:
        # ULAŞILAMADI ≠ REDDEDİLDİ. Çağıran bu ayrımı yapamazsa geçici bir ağ hatası, geçerli bir
        # silahlı planı kalıcı olarak 'broker reddi' diye düşürür (denetim 2026-07-21).
        _note(False, f"submit_bracket: {type(e).__name__}: {e}")
        return {"ok": False, "detail": f"{type(e).__name__}: {e}", "reachable": False}


def cancel_order(order_id: str) -> dict:
    """Tek emri iptal et (DELETE /v2/orders/{id}). Faz 3 kademe-2'nin yapı taşı."""
    try:
        r = httpx.delete(f"{_paper_base()}/v2/orders/{order_id}", headers=_headers(), timeout=15)
        return {"ok": r.status_code in (200, 204, 207), "status": r.status_code}
    except Exception as e:
        return {"ok": False, "detail": f"{type(e).__name__}: {e}"}


def cancel_open_entries() -> dict:
    """Faz 3 (5a-2) Cancel-Open: YALNIZ henüz DOLMAMIŞ giriş emirlerini (filled_qty=0, canlı parent)
    iptal eder. Kısmen/tam dolmuş parent'lara DOKUNULMAZ — onların koruyucu bacakları (stop/hedef)
    canlı pozisyonu koruyor; onları iptal etmek pozisyonu çıplak bırakır (yasak, mirror_stream ile
    aynı ilke). Dönen: {cancelled:[...], kept:[...], foreign:[...]}.

    SAHİPLİK (A3, denetim 2026-07-21): bu kağıt hesap yalnız motorun değil — operatörün kendi
    emirleri de burada. Eskiden bu fonksiyon AÇIK olan HER dolmamış emri iptal ediyordu; panodaki
    tek tuş operatörün elle girdiği emri de sessizce siliyordu. Artık yalnız ENGINE_COID_PREFIX
    taşıyan (motorun gönderdiği) emirlere dokunur; yabancılar `foreign` altında sayılır."""
    out = {"ok": True, "cancelled": [], "kept": [], "foreign": []}
    try:
        for o in orders(status="open", limit=100, nested=True):
            st = str(o.get("status", "")).lower()
            filled = float(o.get("filled_qty") or 0)
            sym = o.get("symbol")
            if not is_engine_order(o):
                out["foreign"].append({"symbol": sym, "status": st})   # operatörün emri — DOKUNMA
                continue
            if filled <= 0 and st in ("new", "accepted", "pending_new", "held"):
                res = cancel_order(o.get("id"))
                out["cancelled"].append({"symbol": sym, "coid": o.get("client_order_id"),
                                         "ok": res.get("ok")})
            else:
                out["kept"].append({"symbol": sym, "status": st, "filled_qty": filled})
    except Exception as e:
        out = {"ok": False, "detail": f"{type(e).__name__}: {e}", "cancelled": [], "kept": [],
               "foreign": []}
    return out


def asset_tradable(symbol: str) -> bool | None:
    """Faz 3 LULD vekili: emir göndermeden önce varlık işleme açık mı? Alpaca assets ucu tradable ve
    status taşır (halted/delist → tradable=false). Ulaşılamazsa None → FAIL-OPEN (emri Alpaca'nın
    kendi reddine bırak; ağ hatası işlem engeli değildir)."""
    try:
        r = httpx.get(f"{_paper_base()}/v2/assets/{symbol}", headers=_headers(), timeout=10)
        if r.status_code >= 400:
            return None
        a = r.json()
        return bool(a.get("tradable")) and str(a.get("status", "active")) == "active"
    except Exception:  # sessiz-yutma: ağ/sağlayıcı hatası bu yolun NORMAL hâli; çağıran boş sonuç üzerinden yedek kaynağa düşer ve kaynak seçimi ayrıca kaydedilir
        return None


def submit_plan(plan: dict, equity: float, size_mult: float = 1.0,
                atr: float | None = None, ref_price: float | None = None) -> dict:
    """Size a plan against the Alpaca paper account equity (same 1R=1% rule as the internal broker) and
    submit it as a paper bracket order. size_mult: the internal broker's drawdown de-risk multiplier —
    without it the mirror over-sized ~2x in every drawdown and tripped spurious qty-drift alarms
    (audit #50).

    E1 (WP-E, 2026-07-31): emir tipi/limiti/TIF'i ARTIK `broker.entry_order_decision` söyler — İÇ
    MOTORLA AYNI YASA, ikinci bir kopya YOK. `atr` sinyal barının ATR14'ü (None = ölçülemedi),
    `ref_price` gönderim anında bilinen son fiyat. Dönen sözlük `law` altında kararın TAMAMINI
    taşır: çağıran (loop) onu E2 defterine yazar, böylece "hangi yasayla, hangi limitle gönderdik"
    sorusu kayıttan cevaplanır."""
    from ..broker import RISK_PCT_PER_R, MAX_NOTIONAL_PCT, entry_order_decision
    trigger, stop = float(plan["entry_trigger"]), float(plan["stop"])
    per_share = trigger - stop
    if per_share <= 0 or equity <= 0:
        return {"ok": False, "detail": "bad stop/equity"}
    dec = entry_order_decision(trigger, ref_price=ref_price, atr=atr)
    risk = float(plan.get("size_r", 1.0)) * RISK_PCT_PER_R * equity * max(0.0, min(1.0, size_mult))
    qty = int(risk / per_share)
    qty = min(qty, int(MAX_NOTIONAL_PCT * equity / trigger))   # same notional cap as the internal broker
    if qty <= 0:
        return {"ok": False, "detail": "qty rounds to 0", "law": dec}
    # GAP-RİSK VETOSU (kart grid'inin 2. noktası): emir HİÇ gönderilmez. `reachable` BİLEREK True —
    # bu bir broker arızası değil BİZİM kararımızdır; çağıran onu 'ulaşılamadı' diye planı silahlı
    # bırakmamalı, ama 'broker reddi' diye de saymamalı (ret dağılımını kirletirdi).
    if dec["mode"] == "veto":
        return {"ok": False, "detail": "gap_veto (E1: gönderim anında fiyat tetiğin üstünde)",
                "veto": True, "reachable": True, "law": dec}
    if asset_tradable(plan["ticker"]) is False:      # LULD vekili — yalnız KESİN 'kapalı' cevabı engeller
        return {"ok": False, "detail": "asset not tradable (halted/inactive)", "law": dec}
    res = submit_bracket(plan["ticker"], qty, trigger, plan.get("profit_target", trigger * 1.1), stop,
                         client_order_id=plan.get("id"), entry_limit=dec["limit"],
                         entry_type=("limit" if dec["mode"] == "marketable_limit" else "stop_limit"),
                         tif=dec["tif"])
    return {**res, "law": dec, "qty": qty}


def exit_fill_price(order: dict) -> float | None:
    """Best-effort: the actual EXIT fill price of a filled bracket order (the take-profit OR stop-loss leg
    that filled). Alpaca returns the parent order with a `legs` array; the exit is the filled non-entry leg.
    Returns None if nothing filled (order still open / rejected). Used by the reconciler to measure the
    real-world execution price against the internal simulator's gap-aware fill."""
    if not isinstance(order, dict):
        return None
    for leg in (order.get("legs") or []):
        # partially_filled carries a real filled_avg_price too — skipping it made the divergence audit
        # silently no-op exactly when execution got messy (audit #54)
        if str(leg.get("status")) in ("filled", "partially_filled") and leg.get("filled_avg_price") not in (None, ""):
            try:
                return float(leg["filled_avg_price"])
            except (TypeError, ValueError):  # sessiz-yutma: biçimsiz/eksik tek alan; yalnız bu değer düşer, satır başına uyarı asıl sinyali log seline gömerdi
                return None
    return None


def replace_order_stop(order_id: str, new_stop: float, cur_stop: float | None = None) -> dict:
    """Bir emrin (bracket stop bacağının) stop fiyatını DEĞİŞTİR (PATCH /v2/orders/{id}). Dinamik
    trailing-stop ayna senkronu için: iç defterin iz süren stop'u yükseldikçe aynadaki koruma da
    yükselir. Paper-kilitli.

    MONOTONLUK (A4, denetim 2026-07-21): koruma ASLA gevşetilmez. Bunu eskiden yalnız çağıran
    katmanın `ts > cur_stop*1.001` kontrolü sağlıyordu — yani kural koddaydı ama SINIRDA değildi;
    ikinci bir çağıran (elle senkron, gelecekteki bir yol) sessizce stop'u aşağı çekebilirdi.
    cur_stop verilirse sınırın kendisi reddeder."""
    if cur_stop is not None and float(new_stop) <= float(cur_stop):
        return {"ok": False, "detail": f"refused_stop_loosening {new_stop} <= {cur_stop}"}
    try:
        r = httpx.patch(f"{_paper_base()}/v2/orders/{order_id}", headers=_headers(),
                        json={"stop_price": round(float(new_stop), 2)}, timeout=15)
        if r.status_code >= 400:
            try:
                return {"ok": False, "detail": r.json().get("message", f"HTTP {r.status_code}")}
            except Exception:  # sessiz-yutma: ağ/sağlayıcı hatası bu yolun NORMAL hâli; çağıran boş sonuç üzerinden yedek kaynağa düşer ve kaynak seçimi ayrıca kaydedilir
                return {"ok": False, "detail": f"HTTP {r.status_code}"}
        return {"ok": True, "order": r.json()}
    except Exception as e:
        return {"ok": False, "detail": f"{type(e).__name__}: {e}"}


def close_all(confirm: str = "") -> dict:
    """Cancel open orders + flatten all PAPER positions. Operator panic control for the mirror account.

    SAHİPLİK + KAZA KORUMASI (A3, denetim 2026-07-21): bu çağrı motorun SAHİBİ OLMADIĞI pozisyonları
    da düzleştirir — operatörün kendi NVDA'sı bugün bu hesapta duruyor. Yani bu, ajanın kendi
    defterini toplaması değil, İNSANIN varlığına dokunmasıdır. O yüzden artık açık bir onay jetonu
    ister: hiçbir otomatik yol (döngü, ajan, bekçi) yanlışlıkla çağıramaz; yalnız operatörün
    panodaki tuşu jetonu taşır. Jetonsuz çağrı NE YAPAR: hiçbir şey — yalnız neyi düzleştireceğini
    (özellikle YABANCI sembolleri) rapor eder."""
    if confirm != CLOSE_ALL_CONFIRM:
        owned = {str(o.get("symbol")) for o in orders(status="open", limit=100) if is_engine_order(o)}
        syms = [str(p.get("symbol")) for p in positions()]
        return {"ok": False, "detail": "confirm token required", "dry_run": True,
                "would_flatten": syms, "foreign": sorted(s for s in syms if s not in owned)}
    try:
        httpx.delete(f"{_paper_base()}/v2/orders", headers=_headers(), timeout=15)
        r = httpx.delete(f"{_paper_base()}/v2/positions", headers=_headers(),
                         params={"cancel_orders": "true"}, timeout=25)
        return {"ok": r.status_code < 400, "status": r.status_code}
    except Exception as e:
        return {"ok": False, "detail": str(e)}


# ==================================================================================================
# AYNI-AKŞAM GÜNLÜK BAR BACAĞI — VERİ UCU (data.alpaca.markets), TİCARET UCUNDAN AYRI (2026-07-30)
# ==================================================================================================
# NEDEN VAR (Rol 1'in kanıtlı teşhisi): bar zincirinin birincisi (Massive ücretsiz katmanı) grouped
# günlük barı T+1 yayınlıyor — canlı kanıt state/massive_grouped_last.json: date 07-28, fetched_at
# 07-29 21:15Z. Kapanış sonrası 40 dakikalık pencerede yalnız cboe/nasdaq kısmileri geliyor ve
# 07-29 barı ertesi gün hâlâ 259 sembolün 44'ünde. Yani sistem fiilen T+1 ritminde koşuyor ve her
# seans için sahte "SEANS ATLANDI" üretiyor. Bu bacağın işi DAR: yalnız GÜNCEL seansın barını aynı
# akşam getirmek. Tarih derinliği gerektiren HER ŞEY mevcut zincirde kalır.
#
# HOST AYRIMI — `_paper_base()` KİLİDİNE DOKUNULMADI: o kilit TİCARET ucu içindir (gerçek-para emri
# imkânsız olsun diye). Veri ucu AYRI bir hosttur ve operatör-ayarlı DEĞİLDİR (DATA_STREAM_HOST ile
# aynı ilke): kilitlenecek girdi yok, audit-#51 kimlik-sızıntı vektörü yok. Bu yoldan emir geçemez.
#
# UÇ SEÇİMİ (Rol 1 eki, resmi dokümandan teyitli): aynı-akşam için `/v2/stocks/snapshots` —
# sembol başına `dailyBar` TEK çağrıda gelir, sayfalama yok. `/v2/stocks/bars` (sayfalamalı) yalnız
# HACİM KALİBRASYONU bootstrap'ı için kullanılır (aşağıdaki gerekçe).
# İKİ KATMAN (Rol 1 eki 2 — operatörün abonelik tablosu): Basic planın tarihsel-veri kısıtı
# "latest 15 minutes"tır. O kısıttan "KAPANIŞTAN 16 DAKİKA SONRA aynı seansın konsolide barı
# sorgulanabilir" SONUCU ÇIKARILMIŞTI — ve bu sonuç ÖLÇÜMLE ÇÜRÜTÜLDÜ (2026-07-30 21:14Z, aşağıda):
# kısıt bir saat penceresi değil bir TAKVİM GÜNÜ penceresidir. Yürürlükteki katmanlar:
#   AYNI AKŞAM : /v2/stocks/snapshots?feed=iex → temsilî bar; hacim ÖLÇEKLENİR (damga alpaca_iex)
#   ERTESİ GÜN : /v2/stocks/bars?feed=sip     → konsolide OHLCV; ölçekleme GEREKMEZ (alpaca_sip)
# Hangi katmanın servis ettiği KAYNAK DAMGASINDAN okunur — "sip çalışıyor olmalı" cümlesi koda
# gömülmez, defterde görünür. Abonelik reddi ham hata metniyle kaydedilir (alpaca_sip_rejected).
DATA_BASE = "https://data.alpaca.markets"
DATA_FEED = "iex"                # yedek katman — AÇIKÇA geçilir, sağlayıcı varsayılanına yaslanılmaz
DATA_FEED_SIP = "sip"                    # KONSOLİDE feed — YALNIZ GEÇMİŞ seanslar için (aşağı bkz.)
SIP_SOURCE = "alpaca_sip"                # kaynak damgaları: data.py bunları defterde ve zincirde kullanır
IEX_SOURCE = "alpaca_iex"
# ÖLÇÜM, VARSAYIM DEĞİL (Rol 1, 2026-07-29 seansı, gerçek ücretsiz paper anahtarıyla):
#   feed=sip          → HTTP 200, KONSOLİDE (AAPL v=56.298.904 — gerçek bant hacmi).
#   feed=delayed_sip  → HTTP 400 {"message":"invalid feed: delayed_sip"} — bu UÇTA geçerli bir feed
#                       DEĞİL. Merdivenden ÇIKARILDI: var olmayan bir basamağı denemek her turda bir
#                       boşa çağrı ve defterde sahte bir "reddedildi" satırı üretirdi.
#   IEX hacmi konsolidenin medyan %2,2-2,5'i → yedek katmanın kalibrasyonu ZORUNLU (canlı teyitli).
#
# ⚠ YUKARIDAKİ 200 NEYİ KANITLADI, NEYİ KANITLAMADI (Rol 2 düzeltmesi, canlı 2026-07-30 21:14Z):
#   feed=sip + session=BUGÜN → HTTP 403 {"subscription does not permit querying recent SIP data"}
#   feed=sip + session=DÜN   → HTTP 200, konsolide
# Rol 1'in öğleden-sonra sondası DÜNÜ sorduğu için 200 aldı; yani o ölçüm "kapanış+16 dk'da BUGÜNÜN
# konsolide barı gelir" iddiasını HİÇ SINAMAMIŞTI. Gerçek sınır bir SAAT penceresi değil bir TAKVİM
# GÜNÜ penceresidir: bugünün günlük barı, takvim günü bitene kadar "recent" sayılır (geç basımlar ve
# düzeltmeler onu gün boyu güncel tutar). Eski kod bunu bilmediği için her akşam bir boşa 403 yakıyor,
# 6 saatlik abonelik soğumasına giriyor ve o akşam sip'i fiilen ÖLDÜRÜYORDU (yedek IEX doğru şekilde
# devreye giriyordu — canlı akşamda kalibre hacimlerle çalıştığı görüldü).
# İKİ TASARIM KURALI BURADAN DOĞAR:
#   1. AYNI AKŞAM (hedef seans = BUGÜNÜN takvim günü) → sip basamağı HİÇ DENENMEZ; doğrudan iex.
#      Atlama SESSİZ DEĞİLDİR (`alpaca_sip_skipped_current_session`) ama bir ARIZA da değildir:
#      KOŞULDUR, bu yüzden SOĞUMA YAZMAZ (bkz. `_data_fail` yalnız gerçek istek arızasında çağrılır).
#   2. ERTESİ GÜN (hedef seans GEÇMİŞ) → sip BİRİNCİLDİR: hem gecikmeli kovalama/onarım yolunda,
#      hem de İKİNCİ KONSOLİDE KAYNAK olarak T+1 düzeltme koşusunda (data.sip_correct_provisional).
#      Massive grouped NİHAİ otorite kalır — sıra sip→massive'dir, sahiplik değişmez.
# GERÇEK ABONELİK REDDİ (geçmiş seansta 403) 6 saatlik soğuma olarak AYNEN durur: o bir koşul değil,
# gerçekten bir yetki arızasıdır ve geri çekilmeyle çözülmez.
DATA_CHUNK = 100                 # virgüllü sembol listesi: belgelenmiş üst sınır yok → URL uzunluğu için
DATA_MAX_PAGES = 20              # sayfalama güvenlik freni; token hâlâ varsa SESSİZ kırpma YOK, uyarı var
DATA_FAIL_COOLDOWN_S = 300.0     # başarısız deneme bu süre boyunca TEKRARLANMAZ (massive.FAIL_COOLDOWN ikizi)
# ABONELİK REDDİ GEÇİCİ DEĞİLDİR: 401/403 beş dakikada düzelmez. Kısa soğuma, her turda bir boşa
# çağrı + bir yedek çağrı demek olurdu; uzun soğuma abonelik gerçekten açılırsa aynı gün içinde
# yeniden dener (SIP damgası defterde göründüğü an operatör farkı görür).
SIP_REJECT_COOLDOWN_S = 21600.0  # 6 saat

_DATA_FAIL_AT: dict[str, float] = {}
_DATA_COOLDOWN: dict[str, float] = {}   # anahtar başına soğuma SÜRESİ (abonelik reddi ≠ geçici arıza)
_DATA_LAST_FAIL: dict = {}       # son başarısızlığın HAM ayrıntısı (katman seçimi buna bakar)
# TİCARET TAŞIMA KAYDINDAN AYRI (A1): `_TRANSPORT` mutabakatın "broker ulaşılabilir mi" kararını
# taşıyor — bir veri isteğinin 429'u oraya yazılsaydı, mutabakat açık pozisyonları "Alpaca'da kayıp"
# saymamak için baktığı bayrağı VERİ arızası yüzünden kirlenmiş bulurdu. İki gerçek, iki kayıt.
_DATA_TRANSPORT = {"ok": None, "calls": 0, "fails": 0, "last_status": None, "last_error": "", "at": None}


class AlpacaDataError(RuntimeError):
    """Veri İSTEĞİ başarısız oldu — 'veri yok' ile KARIŞTIRILMAMALI (data.FetchError ile aynı ayrım).
    `.reason` kısa ve makine-okunur; URL/anahtar ASLA taşınmaz.

    `.body`: sağlayıcının HAM hata metni (kırpılmış). Neden taşınıyor: "abonelik izin vermiyor" ile
    "geçici 5xx" ayrımı YALNIZ o metinde yaşıyor ve katman seçimi (sip→iex düşüşü) bu ayrımı
    yapmak zorunda. Alpaca hata gövdesi anahtar taşımaz (anahtar BAŞLIKTA gider — bkz. _data_headers)."""

    def __init__(self, reason: str, status: int | None = None, body: str = ""):
        super().__init__(f"alpaca veri isteği başarısız: {reason}")
        self.reason = reason
        self.status = status
        self.body = (body or "")[:300]


def data_available() -> bool:
    """Veri ucu HEM anahtar HEM sır ister (ticaret ucunun aksine — orada sır opsiyoneldi)."""
    return secrets.present("ALPACA_PAPER_KEY") and secrets.present("ALPACA_PAPER_SECRET")


def data_transport() -> dict:
    """Veri ucunun taşıma sağlığı. `ok=False` → dönen {} VERİ DEĞİL, ARIZADIR."""
    return dict(_DATA_TRANSPORT)


def _data_headers() -> dict:
    return {"APCA-API-KEY-ID": secrets.get("ALPACA_PAPER_KEY") or "",
            "APCA-API-SECRET-KEY": secrets.get("ALPACA_PAPER_SECRET") or "",
            "Accept": "application/json"}


def _mono() -> float:
    import time as _t
    return _t.monotonic()


def _data_cooled(key: str) -> bool:
    at = _DATA_FAIL_AT.get(key)
    return at is not None and (_mono() - at) < _DATA_COOLDOWN.get(key, DATA_FAIL_COOLDOWN_S)


def is_subscription_error(e: "AlpacaDataError") -> bool:
    """Bu hata ABONELİK sınıfı mı (geri çekilmeyle çözülmez) yoksa geçici mi? Katman seçimi buna
    bakar. Durum koduna VE gövdeye birlikte bakılır: 403 tek başına başka sebeplerden de gelebilir."""
    return bool(e.status in (401, 403) or "subscription" in (e.body or "").lower())


def _data_fail(key: str, e: "AlpacaDataError", **fields) -> None:
    """Soğuma penceresini kur ve SESSİZ KALMA (yasa 4). 259 sembollük bir turda aynı düşmüş ucu
    259 kez denemek sağlayıcıyı dövmek olurdu; sessizce pes etmek ise arızayı görünmez yapardı."""
    _DATA_FAIL_AT[key] = _mono()
    _DATA_COOLDOWN[key] = SIP_REJECT_COOLDOWN_S if is_subscription_error(e) else DATA_FAIL_COOLDOWN_S
    _DATA_LAST_FAIL.clear()
    _DATA_LAST_FAIL.update({"leg": key, "reason": e.reason, "status": e.status, "body": e.body,
                            "subscription": is_subscription_error(e)})
    try:
        from .. import obs
        obs.warn("alpaca_data_failed", leg=key, reason=e.reason, status=e.status,
                 body=e.body[:160], **fields,
                 detail=f"veri ucu soğumaya alındı — zincir mevcut kaynaklarla devam eder")
    except Exception:  # sessiz-yutma: kayıt kanalının kendisi düştü — ikinci kanal yok; telemetri denemesi veri kararını düşüremez
        pass


def _chunks(seq: list, n: int):
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


def _get_data(path: str, params: dict, timeout: float = 20.0) -> dict:
    """Veri ucuna TEK GET. Yeniden deneme YOK (soğuma penceresi var): oran limiti belgelenmemiş,
    deneme başına ≤4 çağrı zaten mütevazı — bir arızada üstel geri çekilmeyle ısrar etmek, sınırı
    bilmediğimiz bir sağlayıcıyı dövmenin en hızlı yolu olurdu."""
    if not data_available():
        raise AlpacaDataError("anahtar/sır yok")
    _DATA_TRANSPORT["calls"] += 1
    _DATA_TRANSPORT["at"] = _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")
    try:
        r = httpx.get(f"{DATA_BASE}{path}", params=params, headers=_data_headers(), timeout=timeout)
    except Exception as e:
        _DATA_TRANSPORT.update({"ok": False, "last_error": type(e).__name__, "last_status": None})
        _DATA_TRANSPORT["fails"] += 1
        raise AlpacaDataError(type(e).__name__) from e
    _DATA_TRANSPORT["last_status"] = r.status_code
    if r.status_code >= 400:
        try:
            body = (r.text or "")[:300]
        except Exception:  # sessiz-yutma: gövde okunamadıysa yalnız TEŞHİS zayıflar; hata yine fırlatılır
            body = ""
        _DATA_TRANSPORT.update({"ok": False, "last_error": f"HTTP {r.status_code} {body[:120]}"})
        _DATA_TRANSPORT["fails"] += 1
        raise AlpacaDataError(f"HTTP {r.status_code}", r.status_code, body)
    try:
        d = r.json()
    except Exception as e:
        _DATA_TRANSPORT.update({"ok": False, "last_error": "bozuk JSON"})
        _DATA_TRANSPORT["fails"] += 1
        raise AlpacaDataError("bozuk JSON") from e
    _DATA_TRANSPORT.update({"ok": True, "last_error": ""})
    return d if isinstance(d, dict) else {"results": d}


def bar_session_date(t) -> str | None:
    """Alpaca zaman damgası → SEANS TARİHİ (ET). Günlük bar 04:00Z (= 00:00 ET) damgalıdır; kışın
    05:00Z. Ham UTC tarihi almak ikisinde de tesadüfen doğrudur, ama sağlayıcı damgayı bir gün
    kaydırırsa gün KAYAR — açık çeviri o riski kapatır (massive.bar_date ile aynı ders)."""
    if not t:
        return None
    try:
        s = str(t).strip().replace("Z", "+00:00")
        if "." in s:                       # nanosaniyeli damga: fromisoformat 3/6 hane ister
            head, _, tail = s.partition(".")
            frac = "".join(ch for ch in tail if ch.isdigit())[:6]
            rest = tail[len(frac):].lstrip("0123456789")
            s = f"{head}.{frac or '0'}{rest}"
        d = _dt.datetime.fromisoformat(s)
        if d.tzinfo is None:
            d = d.replace(tzinfo=_dt.timezone.utc)
        from zoneinfo import ZoneInfo
        return str(d.astimezone(ZoneInfo("America/New_York")).date())
    except Exception:  # sessiz-yutma: sağlayıcının biçimsiz TEK damgası; tarihi çözülemeyen bar "gelmedi" sayılır (çağıran onu atar) — uydurma tarih yazmaktansa eksik kalmak doğrudur
        return None


_SIP_DAY_WARNED = False


def market_calendar_day() -> str:
    """BUGÜNÜN takvim günü (ET) — "recent SIP" penceresinin bittiği sınır TAM OLARAK bu gündür.

    ET SEÇİMİ KEYFİ DEĞİL: seans tarihleri ET'dir (bkz. `bar_session_date`) ve UTC kullanmak
    20:00 ET'den sonra (= ertesi gün UTC) bugünün seansını "geçmiş" sayardı — yani kaçınmak için
    yazdığımız 403'ü akşamın ikinci yarısında geri getirirdi.
    Çözülemezse BOŞ DİZGİ döner (uydurma tarih yok) ve `sip_allowed` kapalı tarafta kalır."""
    global _SIP_DAY_WARNED
    try:
        from zoneinfo import ZoneInfo
        return str(_dt.datetime.now(ZoneInfo("America/New_York")).date())
    except Exception as e:
        if not _SIP_DAY_WARNED:
            _SIP_DAY_WARNED = True
            try:
                from .. import obs
                obs.warn("alpaca_calendar_day_unavailable", error=f"{type(e).__name__}: {e}",
                         detail="ET takvim günü çözülemedi — sip basamağı KAPALI kalır (sormamak, "
                                "garantili 403 + 6 saatlik yanlış soğuma yakmaktan ucuzdur)")
            except Exception:  # sessiz-yutma: kayıt kanalının kendisi düştü; karar (kapalı taraf) değişmez
                pass
        return ""


def sip_allowed(session: str | None) -> bool:
    """Bu seans için konsolide (sip) feed'i SORULABİLİR Mİ? YALNIZ GEÇMİŞ takvim günleri için.

    Ölçülmüş sınır (2026-07-30 21:14Z): bugünün günlük barı takvim günü bitene kadar "recent SIP"
    sayılır ve 403 döner. Kapalı taraf GÜVENLİ taraftır (scheduler._leg_ready'nin aynı disiplini):
    takvim günü bilinmiyorsa da sorulmaz."""
    d = str(session or "")[:10]
    today = market_calendar_day()
    return bool(d and today and d < today)


def _note_sip_skip(session: str, asked: int, caller: str) -> None:
    """BİLİNÇLİ ATLAMA — SESSİZ DEĞİL ama UYARI DA DEĞİL. `obs.warn` basmak, her akşam tekrarlayan
    ve kimsenin yapabileceği bir şey olmayan bir uyarı üretirdi (gerçek uyarıları okunmaz yapan tam
    olarak budur); `obs.log` basmamak ise bacağın bir basamağını sessizce yok sayardı."""
    try:
        from .. import obs
        obs.log("alpaca_sip_skipped_current_session", session=str(session)[:10],
                today_et=market_calendar_day(), feed=DATA_FEED_SIP, asked=int(asked or 0),
                caller=caller, cooldown_written=False,
                detail="hedef seans BUGÜNÜN takvim günü — konsolide bar bu pencerede 'recent SIP' "
                       "sayılıp 403 döner (ölçüldü 2026-07-30 21:14Z). Basamak BİLİNÇLİ atlandı: "
                       "bu bir ARIZA DEĞİL KOŞULDUR, soğuma YAZILMAZ. Aynı akşam yedek katman "
                       "(iex + hacim kalibrasyonu) servis eder; konsolide değer ertesi gün "
                       "sip düzelticisiyle gelir")
    except Exception:  # sessiz-yutma: kayıt kanalı düştü; atlama kararı zaten uygulandı
        pass


def _note_sip_rejected(session: str) -> bool:
    """Son sip arızası GERÇEKTEN abonelik sınıfı mıydı? Öyleyse HAM metniyle duyur ve True dön.

    YALNIZ ABONELİK SINIFI DÜŞÜŞÜ RAPORLAR: 400 "invalid feed" ya da geçici 5xx buraya girmez
    (girseydi defterde sahte bir "abonelik reddetti" satırı ve 6 saatlik yanlış soğuma olurdu).
    Artık bu satır GERÇEKTEN bir yetki bulgusudur: geçmiş seansta 403 almak, "recent SIP" koşulu
    ile açıklanamaz."""
    if not (_DATA_LAST_FAIL.get("leg") == f"bars:{DATA_FEED_SIP}"
            and _DATA_LAST_FAIL.get("subscription")):
        return False
    try:
        from .. import obs
        obs.warn("alpaca_sip_rejected", session=str(session)[:10], feed=DATA_FEED_SIP,
                 status=_DATA_LAST_FAIL.get("status"),
                 body=str(_DATA_LAST_FAIL.get("body"))[:200],
                 cooldown_s=int(SIP_REJECT_COOLDOWN_S),
                 detail="konsolide (sip) bar GEÇMİŞ bir seans için abonelik tarafından reddedildi — "
                        "'recent SIP' koşuluyla açıklanamaz, gerçek yetki arızasıdır; YEDEK katmana "
                        "(iex snapshot + hacim kalibrasyonu) düşülüyor, damga alpaca_iex")
    except Exception:  # sessiz-yutma: kayıt kanalı düştü; düşüş kararı yine de uygulanır
        pass
    return True


def _to_bar(row: dict, date: str | None) -> dict | None:
    """Ham bar (o/h/l/c/v) → bizim şemamız. Kapanışsız satır bar değildir; eksik alan None kalır."""
    if not isinstance(row, dict) or not date:
        return None
    out: dict = {"date": date}
    for src, dst in (("o", "open"), ("h", "high"), ("l", "low"), ("c", "close"), ("v", "volume")):
        v = row.get(src)
        try:
            out[dst] = float(v) if v is not None else None
        except (TypeError, ValueError):  # sessiz-yutma: tek ALANIN biçimi bozuk; None kalır ve kapanışsız satır zaten düşer
            out[dst] = None
    return out if out.get("close") else None


def snapshots(symbols: list[str], feed: str = DATA_FEED, timeout: float = 20.0) -> dict | None:
    """`/v2/stocks/snapshots` — sembol başına dailyBar/prevDailyBar/latestTrade TEK çağrıda.
    None = istek atılamadı/patladı (HÜKÜM YOK); {} = cevap geldi ama satır yok."""
    syms = sorted({str(s).upper().strip() for s in (symbols or []) if str(s or "").strip()})
    if not syms:
        return {}
    if not data_available() or _data_cooled(f"snapshots:{feed}"):
        return None
    out: dict = {}
    for chunk in _chunks(syms, DATA_CHUNK):
        try:
            d = _get_data("/v2/stocks/snapshots",
                          {"symbols": ",".join(chunk), "feed": feed}, timeout)
        except AlpacaDataError as e:
            _data_fail(f"snapshots:{feed}", e, symbols=len(chunk))
            return out or None          # KISMİ sonuç dürüsttür; hiç yoksa "hüküm yok" (None)
        rows = d.get("snapshots") if isinstance(d.get("snapshots"), dict) else d
        for k, v in (rows or {}).items():
            if isinstance(v, dict):
                out[str(k).upper()] = v
    return out


def session_bars(symbols: list[str], session: str, feed: str = DATA_FEED) -> dict | None:
    """`session` gününün günlük barları: {TICKER: {date,open,high,low,close,volume}}.

    TARİH DOĞRULANIR, VARSAYILMAZ: seans İÇİNDE çağrılırsa `dailyBar` KISMİ barı taşır ve tarihi
    yine bugündür — bu yüzden bacak yalnız kapanmış bir seans için çağrılır (çağıran `session`
    olarak GERÇEKTEN KAPANMIŞ seansı verir; scheduler._last_closed_session tek yasa). Tarihi
    tutmayan sembol "gelmedi" sayılır: uydurma yok, eksik kalır.
    None = istek patladı; {} = cevap geldi, eşleşen bar yok."""
    snaps = snapshots(symbols, feed=feed)
    if snaps is None:
        return None
    want = str(session)[:10]
    out, stale = {}, 0
    for sym, snap in snaps.items():
        b = (snap or {}).get("dailyBar") or {}
        d = bar_session_date(b.get("t"))
        if d is None:
            continue
        if d != want:
            stale += 1
            continue
        bar = _to_bar(b, d)
        if bar:
            out[sym] = bar
    try:
        from .. import obs
        obs.log("alpaca_session_bars", session=want, feed=feed, asked=len(symbols or []),
                answered=len(snaps), matched=len(out), other_session=stale,
                detail="aynı-akşam bacağı: snapshots dailyBar'ları hedef seansa göre süzüldü")
    except Exception:  # sessiz-yutma: kayıt kanalı düştü; barların kendisi geçerli
        pass
    return out


def daily_bars(symbols: list[str], start: str, end: str, feed: str = DATA_FEED,
               limit: int = 10000, timeout: float = 30.0) -> dict | None:
    """`/v2/stocks/bars` (timeframe=1Day) — ÇOKLU SEMBOL + SAYFALAMA. {TICKER: [bar,...]}.

    Aynı-akşam yolunda KULLANILMAZ (snapshot tek çağrıda yeter); bunun tek işi HACİM
    KALİBRASYONU bootstrap'ıdır: son ~30 seansın IEX hacimleriyle diskteki konsolide hacimleri
    eşleştirip sembol başına oran çıkarmak (bkz. adapters/data.calibrate_volume).
    adjustment=split: zincirin geri kalanı (FMP /full, Cboe) BÖLÜNME düzeltmelidir — ham ölçekte
    bar almak, iki ayrı ayarlama ölçeğini birbirine eklemek olurdu (D1 dikiş dersi)."""
    syms = sorted({str(s).upper().strip() for s in (symbols or []) if str(s or "").strip()})
    if not syms:
        return {}
    if not data_available() or _data_cooled(f"bars:{feed}"):
        return None
    out: dict = {}
    for chunk in _chunks(syms, DATA_CHUNK):
        token, pages = None, 0
        while True:
            params = {"symbols": ",".join(chunk), "timeframe": "1Day", "start": start, "end": end,
                      "limit": int(limit), "feed": feed, "adjustment": "split", "sort": "asc"}
            if token:
                params["page_token"] = token
            try:
                d = _get_data("/v2/stocks/bars", params, timeout)
            except AlpacaDataError as e:
                _data_fail(f"bars:{feed}", e, symbols=len(chunk), page=pages, feed=feed)
                return out or None
            for sym, rows in (d.get("bars") or {}).items():
                for r in (rows or []):
                    bar = _to_bar(r, bar_session_date(r.get("t")))
                    if bar:
                        out.setdefault(str(sym).upper(), []).append(bar)
            token = d.get("next_page_token")
            pages += 1
            if not token:
                break
            if pages >= DATA_MAX_PAGES:
                # SESSİZ KIRPMA YOK: yarım seri, boş seriden çok daha kötüdür (massive.covers dersi).
                try:
                    from .. import obs
                    obs.warn("alpaca_bars_pagination_truncated", pages=pages, symbols=len(chunk),
                             start=start, end=end,
                             detail="sayfa freni doldu ve sağlayıcıda hâlâ sayfa var — kalibrasyon "
                                    "örneklemi EKSİK sayılmalı")
                except Exception:  # sessiz-yutma: kayıt kanalı düştü; kırpma kararı değişmez
                    pass
                break
    return out


def sip_session_bars(symbols: list[str], session: str, timeout: float = 30.0) -> dict | None:
    """GEÇMİŞ bir seansın KONSOLİDE (sip) günlük barları: {TICKER: bar}.

    `same_evening_bars`ın İKİZİ DEĞİL, TAMAMLAYICISIDIR: o BUGÜNÜN seansını ister ve tam da bu
    yüzden sip'i atlar; bu ise YALNIZ takvim günü kapanmış bir seans için çağrılır — T+1 düzeltme
    koşusunun İKİNCİ konsolide kaynağı (bkz. data.sip_correct_provisional).

    None = SORULMADI ya da istek patladı (HÜKÜM YOK); {} = soruldu, hedef seansı tutan bar yok."""
    want = str(session)[:10]
    if not sip_allowed(want):
        _note_sip_skip(want, len(symbols or []), "sip_correction")
        return None
    rows = daily_bars(symbols, want, want, feed=DATA_FEED_SIP, timeout=timeout)
    if rows is None:
        _note_sip_rejected(want)
        return None
    out = {str(s).upper(): r[-1] for s, r in rows.items() if r and r[-1].get("date") == want}
    try:
        from .. import obs
        obs.log("alpaca_sip_session", session=want, feed=DATA_FEED_SIP, source=SIP_SOURCE,
                asked=len(symbols or []), matched=len(out),
                detail="GEÇMİŞ seansın konsolide günlük barı — 'recent SIP' penceresi kapandığı "
                       "için 200 beklenir; hacim GERÇEK (ölçekleme sorusu yok)")
    except Exception:  # sessiz-yutma: kayıt kanalı düştü; barların kendisi geçerli
        pass
    return out


def same_evening_bars(symbols: list[str], session: str, timeout: float = 30.0) -> dict:
    """AYNI-AKŞAM BACAĞININ TEK GİRİŞİ — iki katman, TEK cevap, AÇIK damga.

    Dönen: {"source": "alpaca_sip"|"alpaca_iex"|None, "bars": {TICKER: bar}, "detail": str}
      alpaca_sip → KONSOLİDE günlük bar (tüm piyasa hacmi). Ölçekleme GEREKMEZ.
      alpaca_iex → tek borsanın temsilî barı. Hacim ÖLÇEKLENMEDEN kullanılamaz (bkz. data.py).
      None       → hiçbir katman veremedi (HÜKÜM YOK; zincir mevcut kaynaklarla devam eder).

    ⚠ SIP BASAMAĞI HEDEF SEANSA GÖRE KOŞULLUDUR (Rol 2 düzeltmesi, 2026-07-30 canlı ölçümü):
      * hedef seans = BUGÜNÜN takvim günü → sip HİÇ DENENMEZ. Ölçüldü: o pencerede istek garantili
        403 "subscription does not permit querying recent SIP data" döner. Eski davranış her akşam
        bir boşa çağrı yakıp 6 saatlik abonelik soğumasına giriyordu — yani o akşam sip fiilen
        ölüydü ve defterde SAHTE bir "abonelik reddetti" satırı birikiyordu. Atlama duyurulur
        (`alpaca_sip_skipped_current_session`, bilgi düzeyi) ve SOĞUMA YAZMAZ: koşul ≠ arıza.
      * hedef seans GEÇMİŞ (gecikmeli kovalama / onarım geçidi) → sip BİRİNCİL kalır ve gerçek bir
        403 hâlâ `alpaca_sip_rejected` + 6 saatlik soğuma üretir (o artık gerçekten yetki arızasıdır).

    ZAMANLAMA ÇAĞIRANDA: bacak kapanış +16 dakikadan önce ÇAĞRILMAZ (kapı: scheduler._leg_ready —
    takvim yasası tek yerde durur). Seans içinde çağrılırsa iex KISMİ bar verir; o bar burada tarih
    doğrulamasından geçer, yani yanlış zamanda çağrı 'veri yok' üretir, uydurma bar değil."""
    want = str(session)[:10]
    if sip_allowed(want):
        rows = daily_bars(symbols, want, want, feed=DATA_FEED_SIP, timeout=timeout)
        if rows:
            bars = {s: r[-1] for s, r in rows.items() if r and r[-1].get("date") == want}
            if bars:
                try:
                    from .. import obs
                    obs.log("alpaca_same_evening", session=want, source=SIP_SOURCE,
                            feed=DATA_FEED_SIP, symbols=len(bars), asked=len(symbols or []),
                            detail="KONSOLİDE günlük bar (sip) — hacim ölçeklemesi gerekmez")
                except Exception:  # sessiz-yutma: kayıt kanalı düştü; barların kendisi geçerli
                    pass
                return {"source": SIP_SOURCE, "bars": bars, "detail": "sip konsolide"}
        _note_sip_rejected(want)
        _detail = "iex temsilî (hacim ölçeklenecek)"
    else:
        _note_sip_skip(want, len(symbols or []), "same_evening")
        _detail = "iex temsilî (hacim ölçeklenecek; sip bugünün seansı için atlandı)"
    iex = session_bars(symbols, want, feed=DATA_FEED)
    if iex:
        return {"source": IEX_SOURCE, "bars": iex, "detail": _detail}
    return {"source": None, "bars": {}, "detail": "hiçbir katman veremedi"}


def dashboard_view() -> dict:
    """Everything the dashboard needs about the paper account — masked-safe (no keys)."""
    acct = account()
    pos = positions()
    return {"connected": acct is not None,
            "equity": float(acct["equity"]) if acct and "equity" in acct else None,
            "cash": float(acct["cash"]) if acct and "cash" in acct else None,
            "status": acct.get("status") if acct else None,
            "buying_power": float(acct["buying_power"]) if acct and "buying_power" in acct else None,
            "positions": [{"symbol": p.get("symbol"), "qty": p.get("qty"),
                           "avg_entry": p.get("avg_entry_price"), "current": p.get("current_price"),
                           "upl": p.get("unrealized_pl")} for p in pos],
            "open_orders": [{"symbol": o.get("symbol"), "side": o.get("side"), "type": o.get("type"),
                             "qty": o.get("qty"), "status": o.get("status"),
                             "stop": o.get("stop_price"), "limit": o.get("limit_price")}
                            for o in orders("open", 20)],
            "endpoint": _paper_base()}
