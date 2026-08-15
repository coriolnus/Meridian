"""adapters/alpaca.py — Alpaca broker adaptörü: varsayılan olarak PAPER; iç broker simülatörünün
dışa bakan AYNASI + salt-okuma piyasa verisi düzlemi.

(a) Ne yapar: kağıt (paper) yürütme SDK'sız, doğrudan REST/httpx ile gider (bracket gönderimi, emir
listeleme/iptal, motor pozisyonu kapatma, koruyucu OCO); PnL/dolumların hükmü HER ZAMAN iç
broker.py simülatörünündür, burası aynadır. AMA ayna yolu MERIDIAN_BROKER=alpaca_paper iken HER
döngüde canlıdır — submit_plan() her silahlı planda çağrılır. Eski docstring "bu modüle yalnız canlı
yol açılınca girilir" diyordu; bu YANLIŞLANDI: ayna arızası gerçek bir silahlı planı düşürebilir.
Ayrıca AYRI bir piyasa-verisi düzlemi taşır (data.alpaca.markets REST + stream host; iex/sip
feed'leri, seans/günlük barlar, aynı-akşam bacağı) — o yol salt-okumadır, emir geçemez.
(b) Kilit girişler: submit_plan()/submit_bracket(), orders(nested=True)/order_by_id(), account()/
positions()/transport(), cancel_open_entries(), close_engine_position(), submit_protective_oco()/
koruma_coid(), replace_order_stop(), close_all(CLOSE_ALL_CONFIRM), ping(); veri düzlemi:
session_bars()/daily_bars()/snapshots()/sip_session_bars()/same_evening_bars()/data_ws_url().
(c) Değişmezler — PAPER KİLİDİ: LIVE yolu bayraksız REDDEDİLİR (live_guard: MERIDIAN_MODE=live VE
MERIDIAN_I_ACCEPT_RISK=true elle kurulmadan VE goal.limits.autonomy_level >= 1 olmadan live_client
fırlatır); REST yolu _paper_base() ile paper-api.alpaca.markets HOSTNAME'ine sert kilitlidir (yabancı
host anahtar başlığı alamaz, şema https'e yükseltilir) — bu modülden gerçek-para emri ÇIKAMAZ.
Yazılı varsayımlar: A1 salt-okuma uçlar istisna fırlatmaz, None/[] döner — "ulaşılamadı" ile "emir
yok" ayrımını transport() taşır, çağıran karar ÖNCESİ ona bakar; A2 client_order_id iç plan kimliği
= ENGINE_COID_PREFIX ("P-") öneki, mutabakatın birleştirme anahtarı; A3 hesap yalnız motorun değil —
sahibi olunmayan emir/pozisyona dokunulmaz (süpürücü hükmü coid_sinifi'nin aile/grup/yön
kemerlerinden okur; close_all onay jetonlu); A4 koruma stop'u asla gevşetilmez, replace_order_stop
yalnız YUKARI taşır. alpaca-py tembel import edilir (L0 kurulumsuz koşar).
(d) Okur/yazar: state'e dosya yazmaz; sırlar secrets'tan okunur ve asla loglanmaz; taşıma sağlığı ve
süpürme/sınıf dökümü süreç-içi sayaç + olay defteri (obs) üzerinden görünür kılınır."""
from __future__ import annotations
import datetime as _dt
import httpx
from .. import secrets, config

PAPER_BASE = "https://paper-api.alpaca.markets"
_SCHEME_WARNED = False   # taşıma yükseltmesi süreç başına BİR kez duyurulur (gürültü değil sinyal)

# ===== MARKET-DATA STREAM — TRADING host'tan AYRI, SABİT host =====
# Piyasa verisi WS'i trading host'uyla KARIŞTIRILMAZ: bu SABİT bir data host'udur, operatör-ayarlı
# uç nokta YOKTUR → kilitlenecek girdi ve kimlik-sızıntı vektörü de yoktur (o, dashboard-
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
# operatör-kalemidir.
# GERİ-AL: `def paper_client(): return _client(paper=True)` — bu yorumun yerine.


def live_client():
    """LIVE client — guarded. Only reachable when the human has flipped both flags and passed the promotion gates."""
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
    # (credential-leak vector via the dashboard-settable endpoint).
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


def orders(status: str = "open", limit: int = 50, nested: bool = False,
           after: str | None = None, until: str | None = None) -> list:
    """List orders. nested=True asks Alpaca to return each bracket as ONE parent order carrying its
    take-profit/stop-loss children in a `legs[]` array. WITHOUT it, the list endpoint flattens a bracket
    into 3 separate top-level orders (parent + 2 children), each with legs=[] — so exit_fill_price(), which
    reads the parent's legs, would find nothing and the reconciler's divergence audit would silently no-op.
    The reconciler MUST pass nested=True (verified against the live paper account: flat→3 rows/legs=0,
    nested→1 parent/legs=2).

    B7a: `after`/`until` Alpaca'nın `submitted_at` süzgeçleridir ve SAYFALAMANIN
    yapı taşıdır — `until=<önceki sayfanın en eski submitted_at'i>` ile geriye doğru sayfalanır.
    Bu fonksiyon TEK sayfa döndürür; sayfalayan (ve pencere kapsamını BEYAN eden) katman
    `loop._alpaca_emir_penceresi`dir — hüküm orada, burada yalnız geçirgen parametre."""
    try:
        params = {"status": status, "limit": limit, "direction": "desc"}
        if nested:
            params["nested"] = "true"
        if after:
            params["after"] = str(after)
        if until:
            params["until"] = str(until)
        r = httpx.get(f"{_paper_base()}/v2/orders", headers=_headers(), params=params, timeout=15)
        r.raise_for_status()
        _note(True)
        return r.json()
    except Exception as e:
        # A1: [] dönüyoruz ama SESSİZ değil — mutabakat bunu 'emir yok' sanıp her açık pozisyonu
        # 'Alpaca'da kayıp' diye alarma boğuyordu.
        _note(False, f"orders: {type(e).__name__}: {e}")
        return []


def order_by_id(order_id: str) -> dict | None:
    """Tek emri KİMLİĞİYLE oku (GET /v2/orders/{id}) — karar-çıkışı dolum körlüğünün okuma ucu.

    NEDEN VAR: `DELETE /v2/positions` kapatması coid'i Alpaca-üretimi olan YENİ bir market emri
    doğurur; o emir `by_coid[plan_id]` ile ASLA eşleşmez ve liste penceresinden (limit/kesinti)
    taşmış olabilir. Kimlikle doğrudan okuma pencere boşluğundan bağımsızdır. SALT-OKUMA: emir
    üretmez/değiştirmez. None => okunamadı (arıza ayrımı A1 deseniyle transport()'ta)."""
    oid = str(order_id or "").strip()
    if not oid:
        return None
    try:
        r = httpx.get(f"{_paper_base()}/v2/orders/{oid}", headers=_headers(), timeout=15)
        if r.status_code >= 400:
            _note(True)                  # cevap geldi: 404 dahi olsa broker ULAŞILABİLİR
            return None
        _note(True)
        body = r.json()
        return body if isinstance(body, dict) else None
    except Exception as e:
        _note(False, f"order_by_id: {type(e).__name__}: {e}")
        return None


def submit_bracket(symbol: str, qty: int, entry_stop: float, take_profit: float, stop_loss: float,
                   client_order_id: str | None = None, entry_limit: float | None = None,
                   entry_type: str = "stop_limit", tif: str | None = None) -> dict:
    """Submit a PAPER bracket BUY with an attached take-profit + stop-loss so Alpaca manages the whole
    trade. Returns {ok, order|detail}. Never places a real-money order. client_order_id (the local plan
    id) is the JOIN KEY the reconciler uses to match this order back to the internal plan/trade and
    audit divergence.

    E1 — GİRİŞ BACAĞI ARTIK MARKETABLE STOP-LIMIT / LIMIT (yasa: `broker.entry_law`):
      * `stop_limit` : stop=entry_stop, limit=entry_limit  → tetik teyidi KORUNUR, ödenen fiyat TAVANLI.
      * `limit`      : yalnız limit=entry_limit            → gap dalı (gönderim anında fiyat zaten
                       tetiğin üstünde; buy-stop bu durumda GEÇERSİZ ve Alpaca "stop price must be
                       greater than current price" ile reddediyordu — 95/95 satırın kökü).
      * `stop`       : ESKİ davranış. Yalnız `entry_limit` verilmediğinde kalır (geriye dönük yol);
                       yeni çağıran bu dala girmez.
    TIF varsayılanı DAY (GTC'den değişim): GTC emri bir sonraki seansa sinyal barına
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
        # silahlı planı kalıcı olarak 'broker reddi' diye düşürür.
        _note(False, f"submit_bracket: {type(e).__name__}: {e}")
        return {"ok": False, "detail": f"{type(e).__name__}: {e}", "reachable": False}


def cancel_order(order_id: str) -> dict:
    """Tek emri iptal et (DELETE /v2/orders/{id})."""
    try:
        r = httpx.delete(f"{_paper_base()}/v2/orders/{order_id}", headers=_headers(), timeout=15)
        return {"ok": r.status_code in (200, 204, 207), "status": r.status_code}
    except Exception as e:
        return {"ok": False, "detail": f"{type(e).__name__}: {e}"}


# ==================================================================================================
# SÜPÜRÜCÜNÜN SINIF SÖZLÜĞÜ — "DOLMAMIŞ MOTOR EMRİ" ≠ "GİRİŞ EMRİ"
# ==================================================================================================
# VAKA (canlı A1, 2026-08-07 20:32:39Z): operatörün kurduğu DÖRT bağımsız koruma
# OCO'su (`P-KORUMA-20260807-1623-{AMGN,BKNG,EMR,NUE}`) günlük kadansın süpürmesinde iptal edildi;
# olay defteri `cancelled:4, kept:0, foreign:0` yazdı ve aynı satırın metni "Koruma bacakları YAŞAR"
# diyordu. Katil bu fonksiyondu: koruma OCO'su A2/A3 gereği `P-` önekini TAŞIR (sahiplik kanıtı —
# bilinçli) ve doğası gereği DOLMAMIŞtır, yani eski iki ölçütün (önek + `filled_qty=0`) ikisini de
# sağlıyordu. Fonksiyonun "dolmuş parent'ın koruma bacaklarına DOKUNULMAZ" güvencesi ise yalnız
# BRACKET'A BAĞLI bacakları (`legs[]`) tanıyordu; BAĞIMSIZ koruma OCO'su bu fonksiyon
# yazılırken YOKTU. Sonuç bir kaza değil YAPISAL bir çarpışmaydı: koruma her kurulduğunda bir
# sonraki süpürmede ölüyordu.
#
# İKİ KEMER, İKİSİ DE — biri ötekinin yedeği DEĞİL, ikisi iki AYRI olguyu tutuyor (sonradan ÜÇÜNCÜ
# bir GRUP KEMERİ eklendi — `coid_sinifi` üstündeki bloğa bakın; OCO stop bacağının kör noktası):
#   YÖN KEMERİ  : bu motorun GİRİŞ emri BUY'dur. VARSAYILMADI, ÖLÇÜLDÜ — emir üreten tek giriş
#                 yolu `submit_bracket`tir (`"side": "buy"`, gövde sabiti) ve `submit_plan` ondan
#                 geçer; bu modülde ikinci bir giriş göndericisi yoktur (kaynak-düzeyi
#                 çivisi). SELL bir emir bu sistemde giriş OLAMAZ → süpürülemez.
#   AİLE KEMERİ : `koruma_coid()` ailesi (`P-KORUMA-`) AÇIK DIŞLAMADIR. Yön kemeri tek başına
#                 yetmez: yarın kısa tarafa koruma kurulursa koruyucu bacak BUY-stop olur ve yön
#                 kemerinden GEÇER; aile kemeri onu yine tutar. Tersi de doğru: koruma coid'i
#                 taşımayan (ör. gelecekteki bir çıkış/scale-out) bir SELL emrini yön kemeri tutar.
# YÖNÜ OKUNAMAYAN EMİR (alan yok/boş) BEYANLI ÜÇÜNCÜ HÂLDİR: yön kemeri onu tutmaz, `giris`
# sayılır ve eski ölçütlere (dolmamış + açık statü) düşer. Gerekçe: Alpaca her emirde `side`
# döndürür — alanın yokluğu üretimde bir olgu değil, fikstür/kısmi-cevap hâlidir; orada
# fail-closed davranmak süpürücüyü sessizce ÖLÜ hâle getirirdi (bayat tetik bir daha hiç
# kesilmezdi). Sahiplik ve koruma kanıtı bu dalda AİLE kemerine ve `filled_qty`ye kalır.
KORUMA_COID_ONEK = f"{ENGINE_COID_PREFIX}KORUMA-"   # `koruma_coid()` ile TEK kaynak (aşağıda kullanılır)
GIRIS_EMRI_YONU = "buy"                             # long-only motor: giriş = alış (submit_bracket gövdesi)
SINIF_GIRIS, SINIF_KORUMA, SINIF_YABANCI = "giris", "koruma", "yabanci"
# Süpürmenin SINIF DÖKÜMÜ olayı. NEDEN AYRI BİR SATIR: iptalin olayını çağıran yazıyor
# (`loop._cancel_mirror_entries` → `mirror_stale_entries_cancelled`) ve o satır yalnız SAYI taşıyor
# — 08-07'de "cancelled:4" derken NEYİ iptal ettiğini söylemiyordu (devir tatbikatı bu boşluğu
# "ölçülemedi" diye kayda geçirdi: `cancelled[]` içeriği olaya yazılmalı). Çağıranlar bu turda
# dokunulmaz kapsamda; dürüstlük bu yüzden İPTALİ YAPAN katmanda yaşıyor — hangi uç çağırırsa
# çağırsın (döngü, pano tuşu, kopuş devre kesicisi) döküm aynı yerden düşer.
EV_SUPURME_SINIFLARI = "mirror_cancel_sinif_dokumu"


def is_koruma_order(o: dict) -> bool:
    """Bu emir KORUMA ailesinden mi? (`koruma_coid()` üretimi — önek İKİ yerde yazılmaz, kayar)"""
    return str((o or {}).get("client_order_id") or "").startswith(KORUMA_COID_ONEK)


# ==================================================================================================
# ÜÇÜNCÜ KEMER — OCO/BRACKET GRUBUNUN BİR BACAĞI KORUMA İSE GRUBUN TAMAMI KORUMA
# ==================================================================================================
# ÖLÇÜM (canlı A1 paper, salt-okuma GET, 2026-08-09; VARSAYILMADI): `koruma_kur` dört OCO gönderdi
# ve her biri `orders(status="open", nested=True)` yanıtında ŞÖYLE görünüyor —
#   ÜST DÜZEY (primary): LİMİT bacağı · coid `P-KORUMA-20260809-0835-{SYM}` · side=sell · type=limit
#                        · order_class=oco · status=accepted
#   legs[0] (nested)   : STOP bacağı · coid = Alpaca UUID'si · side=sell · type=stop
#                        · order_class=oco · status=held
# BAĞ YAPISI = SALT `legs[]` İÇERME BAĞI (+ paylaşılan `order_class=oco`). `parent_order_id` alanı
# yanıtta BOŞ; stop bacağının parent'a geri-referansı YOK. `nested=False` (düz) çekimde stop bacağı
# HİÇ görünmüyor (bracket'ın aksine — o düzde 3 satıra bölünür); yani stop bacağı YALNIZ primary'nin
# `legs[]`'i altından erişilebilir. Kemer bu ölçülen yapıya dayanır — "aynı sembolde iki sell" gibi
# KIRILGAN bir çıkarıma DEĞİL (yarın aynı sembolde iki ayrı koruma olabilirdi; içerme bağı yapısaldır).
#
# KÖK NEDEN — STOP BACAĞI NEDEN `yabanci` DÜŞÜYORDU (hüküm sırası, ölçüldü): eski `coid_sinifi`
# SAHİPLİK KAPISINI (`is_engine_order`) EN BAŞA koyuyordu. Stop bacağının coid'i Alpaca UUID'si →
# `is_engine_order` False → fonksiyon YÖN KEMERİNE ULAŞMADAN `yabanci` dönüyordu. Oysa stop bacağı
# SELL'dir ve yön kemeri ("SELL giriş olamaz → koruma") onu tutmalıydı; kapı sırası buna izin
# vermiyordu. Sonuç bugün ZARARSIZ (stop bacağı `legs` altında, süpürücüye ÜST DÜZEY aday olarak hiç
# çıkmaz; ayrıca `yabanci` de süpürülmez) AMA iki bacak İKİ FARKLI SEBEPLE korunuyordu ve stop bacağı
# "operatörün emri" (A3) diye YANLIŞ etiketleniyordu — bir dürüstlük/kör-nokta kusuru.
#
# NEDEN GRUP KEMERİ, NEDEN KÖR HÜKÜM-SIRASI DEĞİL: yön kemerini sahiplik kapısından ÖNCE almak
# (kaba çözüm) stop bacağını düzeltirdi AMA operatörün KENDİ satış emrini (P- öneksiz, ör. kendi
# NVDA'sını satması) da `koruma` sayardı — A3'ün TERS yönden ihlali (bizim olmayanı 'bizim koruma'
# etiketlemek). Yön kemeri bu yüzden BİLİNÇLİ olarak motor-emrine-kapsamlıdır. Doğru sebep bacağın
# YÖNÜ değil GRUP ÜYELİĞİdir: kardeşi (`P-KORUMA-` limit bacağı) korumadır. Bu yüzden ÜÇÜNCÜ kemer
# grup-farkındalığıdır; grup kemeri sahiplik kapısından ÖNCE gelir AMA YALNIZ doğrulanmış bir koruma
# kardeşi varken — koruma kardeşi olmayan gerçek operatör emri yine `yabanci` düşer (A3 KORUNUR).
def coid_sinifi(o: dict, grup_koruma: bool = False) -> tuple[str, str]:
    """Bir emrin SINIFI + gerekçesi: (`giris` | `koruma` | `yabanci`, neden).

    Süpürücünün bir emir hakkındaki hükmü TEK yerde verilir: hem iptal kararı hem olay defterindeki
    döküm bu fonksiyondan okur. İki ayrı yerde iki ayrı hüküm, tam da 08-07'de yaşanan "kod bir şey
    yapıyor, olay başka bir şey anlatıyor" ayrışmasını üretirdi.

    ÜÇ KEMER, ÖNCELİK SIRASIYLA (her biri AYRI bir olguyu tutar — biri ötekinin yedeği değil):
      1. AİLE KEMERİ : `is_koruma_order(o)` — `P-KORUMA-` coid'i taşıyan emir (açık dışlama).
      2. GRUP KEMERİ : emir bir OCO/bracket grubunun üyesi VE grubun bir bacağı koruma ailesinden.
                       Emrin KENDİ coid'i Alpaca UUID'si olsa BİLE grup koruma sayılır.
                       Sinyal iki yoldan gelir: (a) emrin KENDİ `legs[]`'inde bir koruma bacağı varsa
                       (üst düzey emir kendi kendine yeter — hangi bacağın damgayı taşıdığını
                       VARSAYMAZ); (b) `grup_koruma=True` — bir bacağı TEK BAŞINA sınıflarken çağıran
                       bunu geçirir, çünkü bacağın parent'a geri-referansı YOKTUR (bkz. yukarıdaki
                       ölçüm) ve grup sinyalini kardeşi elinde tutan çağıran taşır.
      3. YÖN KEMERİ  : MOTOR emri ve side != buy → long-only motorda giriş BUY'dur; giriş OLAMAZ.

    Grup kemeri SAHİPLİK KAPISINDAN (motor öneki) ÖNCE gelir ama YALNIZ doğrulanmış bir koruma
    kardeşi varken: OCO'nun UUID'li stop bacağı böyle korunur (kimliği Alpaca'nındır, operatörün
    DEĞİL); koruma kardeşi OLMAYAN gerçek bir operatör emri yine `yabanci` düşer (A3 KORUNUR)."""
    o = o or {}
    # GRUP SİNYALİ: emrin KENDİ legs[]'inde bir koruma bacağı mı var (üst düzey emir kendi kendine
    # yeter) YA DA çağıran doğrulanmış bir koruma kardeşi olduğunu mu söyledi (bacağı tek başına
    # sınıflarken). Yalnız BİR düzey içerme okunur — Alpaca OCO/bracket'ı tek düzey yuvalar.
    grup_koruma = bool(grup_koruma) or any(is_koruma_order(l) for l in (o.get("legs") or []))
    if is_koruma_order(o):
        return SINIF_KORUMA, f"koruma ailesi ({KORUMA_COID_ONEK}…) — aile kemeri: süpürülmez"
    if grup_koruma:
        return SINIF_KORUMA, ("OCO/bracket grubunun bir bacağı koruma ailesinden — grup kemeri "
                              "(v221): bu bacağın coid'i Alpaca UUID'si olsa da grubun TAMAMI koruma")
    if not is_engine_order(o):
        return SINIF_YABANCI, "motor öneki YOK — operatörün kendi emri (A3): dokunulmaz"
    yon = str(o.get("side") or "").lower()
    if yon and yon != GIRIS_EMRI_YONU:
        return SINIF_KORUMA, (f"yön '{yon}' — long-only motorda giriş emri '{GIRIS_EMRI_YONU}'dur; "
                              f"bu emir giriş OLAMAZ (yön kemeri)")
    return SINIF_GIRIS, ""


def _supurme_dokumunu_yaz(out: dict) -> None:
    """Süpürmenin SINIF DÖKÜMÜNÜ olay defterine yaz — 08-07'nin okunamayan satırının panzehiri.

    NE ZAMAN YAZILIR: süpürme bir KORUMA sınıfı emirle KARŞILAŞTIĞINDA. Koşulun gerekçesi
    ölçülebilir: satırın taşıdığı yeni bilgi ("dokunmadım ve şunlara dokunmadım") ancak koruma
    sınıfı defterde varken doğar; koruma yokken çağıranın kendi satırı (cancelled/kept/foreign
    sayıları) ile bu satır aynı şeyi iki kez söylerdi. 08-07 şekli — koruma defterde, süpürücü
    çalışıyor — TAM olarak bu koşulun içidir.

    İÇERİK: üç sınıfın sayımı + İPTAL EDİLENLERİN coid'leri. Coid listesi bilerek var: devir
    tatbikatı "iptal edilen 4 emir tam olarak o dört koruma bacağıydı" cümlesinin bir ÇIKARIM
    olduğunu, çünkü olayda liste bulunmadığını yazdı. Liste 12 ile sınırlı — defter satırı
    şişirmeden kimliği taşır."""
    siniflar = out.get("siniflar") or {}
    if not siniflar.get(SINIF_KORUMA):
        return
    try:
        from .. import obs
        obs.log(EV_SUPURME_SINIFLARI,
                giris=int(siniflar.get(SINIF_GIRIS, 0)),
                koruma=int(siniflar.get(SINIF_KORUMA, 0)),
                yabanci=int(siniflar.get(SINIF_YABANCI, 0)),
                cancelled=len(out.get("cancelled") or []),
                iptal_coidler=[str(c.get("coid") or "?")[:48]
                               for c in (out.get("cancelled") or [])][:12],
                korunan_coidler=[str(k.get("coid") or "?")[:48]
                                 for k in (out.get("kept") or [])
                                 if k.get("sinif") == SINIF_KORUMA][:12],
                detail="süpürücü koruma sınıfı emirlerle karşılaştı ve DOKUNMADI — iptal edilenler "
                       "yalnız `giris` sınıfıdır (yön + aile kemeri, v220)")
    except Exception:  # sessiz-yutma: defter kanalı düştü — ikinci kanal yok ve İPTAL KARARI zaten verilmiş durumda; kayıt denemesi süpürmenin sonucunu düşüremez (obs._emit'in kendi yasasıyla aynı)
        pass


def cancel_open_entries() -> dict:
    """Cancel-Open: YALNIZ henüz DOLMAMIŞ GİRİŞ emirlerini (filled_qty=0, canlı parent)
    iptal eder. Kısmen/tam dolmuş parent'lara DOKUNULMAZ — onların koruyucu bacakları (stop/hedef)
    canlı pozisyonu koruyor; onları iptal etmek pozisyonu çıplak bırakır (yasak, mirror_stream ile
    aynı ilke). Dönen: {cancelled:[...], kept:[...], foreign:[...], siniflar:{...}}.

    SAHİPLİK (A3): bu kağıt hesap yalnız motorun değil — operatörün kendi
    emirleri de burada. Eskiden bu fonksiyon AÇIK olan HER dolmamış emri iptal ediyordu; panodaki
    tek tuş operatörün elle girdiği emri de sessizce siliyordu. Artık yalnız ENGINE_COID_PREFIX
    taşıyan (motorun gönderdiği) emirlere dokunur; yabancılar `foreign` altında sayılır.

    KORUMA (canlı vaka 2026-08-07 — yukarıdaki blok): sahiplik ve terminallik ölçütleri bir
    emrin GİRİŞ olduğunu KANITLAMAZ. Süpürme adayı olabilmek için emir ayrıca `giris` SINIFINDAN
    olmalıdır (yön kemeri + aile kemeri, `coid_sinifi`). Koruma sınıfı emirler `kept` altına
    `sinif: koruma` etiketiyle düşer — sayılırlar, GÖRÜNÜRLER, ama süpürülmezler.

    YALNIZ TOPLU SÜPÜRÜCÜ BAĞLANIR: `cancel_order` tek-emir ucudur ve operatörün elle iptal hakkı
    oradan geçer — koruma kemeri oraya KONULMADI, konsaydı operatör kendi kurduğu korumayı panodan/
    CLI'den kaldıramazdı (A3'ün ters yönden ihlali)."""
    out = {"ok": True, "cancelled": [], "kept": [], "foreign": [],
           "siniflar": {SINIF_GIRIS: 0, SINIF_KORUMA: 0, SINIF_YABANCI: 0}}
    try:
        for o in orders(status="open", limit=100, nested=True):
            st = str(o.get("status", "")).lower()
            filled = float(o.get("filled_qty") or 0)
            sym = o.get("symbol")
            # GRUP KEMERİ: `nested=True` her OCO/bracket'ın bacaklarını `o["legs"]` altında
            # getirir (ZORUNLU — düz çekimde OCO stop bacağı hiç görünmez, ölçüm 2026-08-09) ve
            # `coid_sinifi` üst düzey emri KENDİ bacaklarına bakarak sınıflar: grubun bir bacağı
            # `P-KORUMA-` ise üst düzey emir, coid'i aile öneki taşımasa da `koruma` düşer, süpürülmez.
            # Süpürücü YALNIZ ÜST DÜZEYDE işlem/sayım yapar (bacaklar `legs` altında; sınıf
            # dökümü sayıları KORUNUR) — grup-farkındalığı hükmü bozmayan, kör noktayı kapatan katman.
            sinif, gerekce = coid_sinifi(o)
            out["siniflar"][sinif] = out["siniflar"].get(sinif, 0) + 1
            if sinif == SINIF_YABANCI:
                out["foreign"].append({"symbol": sym, "status": st,
                                       "sinif": sinif})            # operatörün emri — DOKUNMA
                continue
            if sinif == SINIF_KORUMA:
                # KORUMA: dolmamış olması onu giriş YAPMAZ. `kept`e gerekçesiyle düşer ki olay
                # defterini okuyan "neden iptal edilmedi" sorusunu satırdan cevaplayabilsin.
                out["kept"].append({"symbol": sym, "status": st, "filled_qty": filled,
                                    "coid": o.get("client_order_id"), "sinif": sinif,
                                    "neden": gerekce})
                continue
            if filled <= 0 and st in ("new", "accepted", "pending_new", "held"):
                res = cancel_order(o.get("id"))
                out["cancelled"].append({"symbol": sym, "coid": o.get("client_order_id"),
                                         "ok": res.get("ok"), "sinif": sinif})
            else:
                out["kept"].append({"symbol": sym, "status": st, "filled_qty": filled,
                                    "coid": o.get("client_order_id"), "sinif": sinif,
                                    "neden": "dolmuş/kısmi parent — koruma bacakları canlı"})
    except Exception as e:
        return {"ok": False, "detail": f"{type(e).__name__}: {e}", "cancelled": [], "kept": [],
                "foreign": [], "siniflar": {SINIF_GIRIS: 0, SINIF_KORUMA: 0, SINIF_YABANCI: 0}}
    _supurme_dokumunu_yaz(out)
    return out


def _filled_qty(o: dict) -> float:
    """Bir emrin dolmuş adedi; okunamayan/biçimsiz alan 0 sayılır (sahiplik KANITI olarak asla
    yukarı yuvarlanmaz — ölçülemeyen adet, sahip olunan adet değildir)."""
    try:
        return abs(float((o or {}).get("filled_qty") or 0.0))
    except (TypeError, ValueError):  # sessiz-yutma: biçimsiz tek alan; 0 dönmek FAIL-CLOSED yöndür — sahiplik kanıtı zayıflar, kapatma adedi BÜYÜMEZ
        return 0.0


_LIVE_ORDER_STATES = ("new", "accepted", "pending_new", "held", "open", "accepted_for_bidding",
                      "partially_filled")


def close_engine_position(symbol: str, plan_id: str | None = None) -> dict:
    """İÇ MOTORUN ÇIKIŞ KARARINI AYNAYA TAŞI: yalnız MOTORUN KENDİ bracket'ını kapatır.

    NEDEN VAR: time_stop / regime_flip / giveback / erken-itlaf çıkışları
    iç defteri kapatıyor ama aynadaki bracket AÇIK kalıyordu. Sonuç mutabakatta "motor yetimi"
    olarak HER TURDA alarm basıyor ve sembol `loop._mirror_busy` üzerinden kalıcı olarak karar
    dışında kalıyordu (huninin kendi kendini aç bırakması). Bu depoda pozisyon kapatan tek yol
    `close_all` idi — operatör jetonlu ve SAHİPSİZ (herkesin pozisyonunu düzleştirir), yani iç
    motorun dar çıkış kararı için kullanılamazdı.

    SAHİPLİK — `close_all`DAN DAHA DAR, ONAY JETONU YOK, GEREKÇESİ ŞU: bu çağrı insanın varlığına
    değil MOTORUN KENDİ pozisyonuna dokunur ve dokunacağı her şeyi ENGINE_COID_PREFIX taşıyan bir
    PARENT emirden TÜRETİR:
      * Koruma bacaklarının (TP/SL) client_order_id'si Alpaca üretimidir — `is_engine_order` onlarda
        HER ZAMAN False döner. O yüzden sahiplik BACAKTA değil PARENT'ta doğrulanır ve yalnız sahip
        olduğumuz parent'ın bacakları iptal edilir.
      * Sahiplik KANITI "bir P- emri var" değil "bir P- emri DOLDU"dur: dolmamış/iptal olmuş tarihsel
        emirler pozisyonun bizim olduğunu göstermez. Kanıt yoksa hiçbir pozisyon kapatılmaz
        (`owned=False`) — operatörün aynı sembolü elde tutması bu yüzden güvenlidir.
      * Kapatma DELETE /v2/positions/{sym}?qty=<sahip olunan adet> ile YAPILIR: aynı sembolde
        operatörün kendi hisseleri varsa onlar düşmez. Adet, parent'ın `filled_qty`si ile GERÇEK
        pozisyon adedinin KÜÇÜĞÜDÜR (ikisinden büyüğü asla).

    ÇIPLAK PENCERE — BEYANLI: koruma bacakları kapatmadan ÖNCE iptal edilmek zorundadır (aksi hâlde
    hisseler açık satış emirlerince tutulur ve kapatma "insufficient qty" ile reddedilir). İptal
    başarılı olup kapatma düşerse pozisyon o an KORUMASIZDIR — dönüşte `naked: True` gelir; çağıran
    (loop._mirror_exit_sync) bunu ALARM'a çevirir ve bir sonraki döngüde yeniden dener. Bu pencere
    sessiz DEĞİLDİR.

    KORUMA AİLESİ (08-07 süpürücü çarpışmasının İCRA-bacağı ikizi): plan_id
    süzgeci BAĞIMSIZ koruma OCO'sunu (coid `P-KORUMA-…`, plan_id DEĞİL) görmüyordu; canlı
    satış bacakları hisseleri rehin tutarken DELETE her turda reddediliyor ve çıkış sonsuz
    `cikis_yetimi` dönüyordu. Artık kapatmadan önce AYNI SEMBOLÜN koruma-sınıfı emirleri de iptal
    edilir. Sınıf hükmü TEK yerden okunur (`coid_sinifi` — aile+yön ve grup kemerleri;
    ikinci bir süzgeç YAZILMAZ) ve `yabanci` sınıfı yine dokunulmazdır (A3).

    İPTAL→KAPAT SIRASI (davranış sözleşmesi — Alpaca'nın redd semantiğinden BAĞIMSIZ doğru sıra):
    bir iptal denemesi başarısız görünürse kapatma DENENMEZ. Önce açık-emir listesinden doğrulanır
    (iptali düşen emir gerçekten hâlâ canlı mı — 422 "zaten dolmuş/iptal" yarışı burada aklanır);
    hâlâ canlıysa `cancel_failed: True` ile dönülür, DELETE hiç yapılmaz: yarım-durum (rehinli
    hisseyle redd turu ya da yarı-sökülmüş koruma) üretmek yerine alarm + bir sonraki tur yeniden
    dener (kuyruk zaten yeniden dener, loop._mirror_exit_sync).

    KAPATMA EMRİNİN KİMLİĞİ: DELETE cevabının gövdesi, kapatmayı yapan
    YENİ market emrinin kendisidir (coid Alpaca-üretimi — plan_id ile ASLA eşleşmez). Emrin `id`si
    dönüşte `close_order_id` olarak taşınır ki reconcile o emrin `filled_avg_price`ını sonraki
    turda okuyup trades satırına yamayabilsin (E2 giriş-yamasının çıkış simetriği). Gövde/id
    OKUNAMAZSA UYDURULMAZ: `close_order_id=None` + `close_order_neden` (çağıran yamayı beyanla
    kapatır — dolum fiyatı 0/varsayım olamaz).

    Dönüş: {ok, owned, cancelled[], closed_qty, naked, cancel_failed, reachable, detail,
            close_order_id, close_order_neden}."""
    out = {"ok": False, "owned": False, "cancelled": [], "closed_qty": 0.0,
           "naked": False, "cancel_failed": False, "reachable": True, "detail": "",
           "close_order_id": None, "close_order_neden": None}
    sym = str(symbol or "").strip()
    if not sym:
        return {**out, "detail": "sembol verilmedi"}
    ords = orders(status="all", limit=200, nested=True)
    if not transport()["ok"]:
        # A1 deseni: [] burada "emir yok" DEĞİL, arıza. Arızada sahiplik doğrulanamaz → dokunma.
        return {**out, "reachable": False,
                "detail": transport().get("error") or "alpaca transport down"}
    # SAHİPLİK ADAYLARI: koruma-sınıfı emirler parents'a GİRMEZ. İki gerekçe: (a) plan_id=None
    # çağrıda dolmuş bir koruma SATIŞI `filled` listesine düşüp owned_qty'yi şişirirdi — satış dolumu
    # uzun pozisyonun sahiplik KANITI değildir (kanıt = dolmuş GİRİŞ, aşağıdaki docstring yasası);
    # (b) koruma iptali kendi adımında (1b) kendi `kind` etiketiyle yapılır ki `naked` hesabı ve olay
    # dökümü dürüst kalsın.
    parents = [o for o in (ords or [])
               if str(o.get("symbol")) == sym and is_engine_order(o)
               and (plan_id is None or str(o.get("client_order_id")) == str(plan_id))
               and coid_sinifi(o)[0] != SINIF_KORUMA]
    filled = [o for o in parents
              if _filled_qty(o) > 0 or str(o.get("status", "")).lower() in ("filled", "partially_filled")]
    if not parents:
        return {**out, "detail": f"sahiplik doğrulanamadı: {sym} için '{ENGINE_COID_PREFIX}' önekli "
                                 f"motor emri bulunamadı (plan_id={plan_id})"}
    out["owned"] = True

    # 1) BİZİM emirlerimiz: canlı parent + sahip olduğumuz parent'ın canlı bacakları.
    for p in parents:
        if str(p.get("status", "")).lower() in _LIVE_ORDER_STATES and p.get("id"):
            res = cancel_order(str(p["id"]))
            out["cancelled"].append({"id": str(p["id"]), "kind": "parent", "ok": bool(res.get("ok"))})
        for leg in (p.get("legs") or []):
            if str(leg.get("status", "")).lower() in _LIVE_ORDER_STATES and leg.get("id"):
                res = cancel_order(str(leg["id"]))
                out["cancelled"].append({"id": str(leg["id"]), "kind": "leg", "ok": bool(res.get("ok"))})

    # 1b) KORUMA AİLESİ: aynı sembolün koruma-SINIFI emirleri — bağımsız OCO da dahil.
    # Hüküm `coid_sinifi`den (aile/grup kemerleri): `P-KORUMA-` ailesi + koruma-kardeşli OCO grubu +
    # motor SELL. Yalnız kapatılacak pozisyonu rehin tutan CANLI kayıtlar iptal edilir; `yabanci`
    # (operatörün kendi emri) bu süzgece hiç girmez — A3 korunur.
    for o in (ords or []):
        if str(o.get("symbol")) != sym or coid_sinifi(o)[0] != SINIF_KORUMA:
            continue
        if str(o.get("status", "")).lower() in _LIVE_ORDER_STATES and o.get("id"):
            res = cancel_order(str(o["id"]))
            out["cancelled"].append({"id": str(o["id"]), "kind": "koruma",
                                     "coid": o.get("client_order_id"), "ok": bool(res.get("ok"))})
        for leg in (o.get("legs") or []):
            if str(leg.get("status", "")).lower() in _LIVE_ORDER_STATES and leg.get("id"):
                res = cancel_order(str(leg["id"]))
                out["cancelled"].append({"id": str(leg["id"]), "kind": "koruma_leg",
                                        "ok": bool(res.get("ok"))})

    # 1c) İPTAL→KAPAT KAPISI: iptali düşen emir varsa, kapatmayı denemeden ÖNCE açık-emir
    # listesinden doğrula. "İptal düştü" iki ayrı olguyu örter: (a) emir gerçekten canlı kaldı —
    # kapatma rehin yüzünden reddedilir ve pozisyon yarı-sökülmüş korumayla kalır → DENEME;
    # (b) emir aradan dolmuş/iptal olmuş (422 yarışı) — artık rehin yok → kapatma güvenle sürer.
    _dusen = [c["id"] for c in out["cancelled"] if not c.get("ok")]
    if _dusen:
        acik = orders(status="open", limit=200, nested=True)
        if not transport()["ok"]:
            return {**out, "reachable": False, "cancel_failed": True, "naked": _naked(out),
                    "detail": "iptal sonucu doğrulanamadı (açık emir listesi okunamadı) — "
                              "kapatma DENENMEDİ; sonraki tur yeniden dener"}
        _canli_ids: set = set()
        for o in (acik or []):
            for kayit in [o] + list(o.get("legs") or []):
                if str(kayit.get("status", "")).lower() in _LIVE_ORDER_STATES and kayit.get("id"):
                    _canli_ids.add(str(kayit["id"]))
        _hala = sorted(set(_dusen) & _canli_ids)
        if _hala:
            return {**out, "cancel_failed": True, "naked": _naked(out),
                    "detail": f"{len(_hala)} emir iptali başarısız ve emir hâlâ CANLI — kapatma "
                              f"DENENMEDİ (iptal→kapat sırası, B4: yarım-durum üretilmez); "
                              f"sonraki tur yeniden dener"}

    # 2) Pozisyon: gerçekten var mı, ve kaçı BİZİM?
    apos = positions()
    if not transport()["ok"]:
        return {**out, "reachable": False, "naked": _naked(out),
                "detail": transport().get("error") or "pozisyon listesi okunamadı"}
    pos_qty = 0.0
    for p in (apos or []):
        if str(p.get("symbol")) == sym:
            try:
                pos_qty = abs(float(p.get("qty") or 0.0))
            except (TypeError, ValueError):  # sessiz-yutma: biçimsiz adet alanı; 0 sayılır — kapatma adedi BÜYÜMEZ, çağıran yeniden dener
                pos_qty = 0.0
            break
    owned_qty = sum(_filled_qty(o) for o in filled)
    close_qty = min(owned_qty, pos_qty)
    if close_qty <= 0:
        # Ayna pozisyonu YOK (emir hiç dolmadı / zaten kapandı) ya da sahiplik kanıtı sıfır adet.
        # İptaller yapıldı; kapatılacak bir şey kalmadı — bu bir BAŞARIDIR, sessiz bir arıza değil.
        return {**out, "ok": True,
                "detail": (f"kapatılacak motor pozisyonu yok (aynada {pos_qty:g}, "
                           f"sahip olunan {owned_qty:g})")}
    try:
        q = int(close_qty) if float(close_qty).is_integer() else close_qty
        r = httpx.delete(f"{_paper_base()}/v2/positions/{sym}", headers=_headers(),
                         params={"qty": str(q)}, timeout=25)
        _note(True)                      # cevap geldi: 4xx bile olsa broker ULAŞILABİLİR
        if r.status_code >= 400:
            try:
                det = r.json().get("message", f"HTTP {r.status_code}")
            except Exception:  # sessiz-yutma: gövde JSON değil (sağlayıcı HTML/boş dönebilir); durum kodu tek başına yeterli kanıttır
                det = f"HTTP {r.status_code}"
            return {**out, "ok": False, "naked": _naked(out), "detail": str(det)[:200]}
        # Kapatma emrinin kimliği cevaptan okunur — okunamazsa None + NEDEN (uydurma yasağı).
        oid, oneden = None, None
        try:
            govde = r.json()
            if isinstance(govde, dict) and govde.get("id"):
                oid = str(govde["id"])
            else:
                oneden = "DELETE cevabında emir gövdesi/id yok"
        except Exception as e:  # sessiz-yutma DEĞİL: neden dönüşte taşınır, çağıran beyanla kapatır
            oneden = f"DELETE cevap gövdesi okunamadı: {type(e).__name__}"
        return {**out, "ok": True, "closed_qty": float(close_qty), "detail": "",
                "close_order_id": oid, "close_order_neden": oneden}
    except Exception as e:
        _note(False, f"close_engine_position: {type(e).__name__}: {e}")
        return {**out, "ok": False, "reachable": False, "naked": _naked(out),
                "detail": f"{type(e).__name__}: {e}"}


def _naked(out: dict) -> bool:
    """Koruma bacağı BAŞARIYLA iptal edildi mi? (kapatma düşerse pozisyon çıplak kalır)
    `koruma`/`koruma_leg` de sayılır: bağımsız koruma OCO'sunun iptali de pozisyonu aynı şekilde
    soyar."""
    return any(c.get("kind") in ("leg", "koruma", "koruma_leg") and c.get("ok")
               for c in (out.get("cancelled") or []))


def asset_tradable(symbol: str) -> bool | None:
    """LULD vekili: emir göndermeden önce varlık işleme açık mı? Alpaca assets ucu tradable ve
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
    without it the mirror over-sized ~2x in every drawdown and tripped spurious qty-drift alarms.

    E1: emir tipi/limiti/TIF'i ARTIK `broker.entry_order_decision` söyler — İÇ
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
    # GAP-RİSK VETOSU: emir HİÇ gönderilmez. `reachable` BİLEREK True —
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
        # silently no-op exactly when execution got messy
        if str(leg.get("status")) in ("filled", "partially_filled") and leg.get("filled_avg_price") not in (None, ""):
            try:
                return float(leg["filled_avg_price"])
            except (TypeError, ValueError):  # sessiz-yutma: biçimsiz/eksik tek alan; yalnız bu değer düşer, satır başına uyarı asıl sinyali log seline gömerdi
                return None
    return None


def koruma_fill(order: dict) -> dict | None:
    """Koruma emrinde DOLMUŞ bacağı bul — okuma ucu (`exit_fill_price`in koruma kardeşi).

    `exit_fill_price` YETMEZ, çünkü o yalnız `legs[]`e bakar; koruma OCO'sunda ise (ölçüm,
    canlı 2026-08-09) HEDEF bacağı primary'nin KENDİSİDİR (limit, coid `P-KORUMA-…`) ve stop bacağı
    `legs[0]`dadır. İki dolum şekli iki ayrı yerde yaşar:
      * hedef doldu → primary `filled`, fiyat primary'nin `filled_avg_price`ında;
      * stop doldu  → primary OCO gereği `canceled`a düşer, dolum `legs[0]`da.
    Ayrıca `canceled` + `filled_qty>0` hâli (kısmi dolum sonrası OCO artığının iptali) de bir
    DOLUMDUR — yalnız statüye bakmak onu kaçırırdı.

    SINIF HÜKMÜ BURADA VERİLMEZ: emrin koruma olup olduğuna `coid_sinifi` karar verir (tek hüküm
    noktası); bu fonksiyon yalnız verilen emrin İÇİNDEN dolumu okur.

    Dönüş: dolum yoksa None; varsa
      {"bacak": "stop"|"hedef"|None, "price": float|None, "neden": str, "filled_qty": float,
       "status": str}
    UYDURMA YASAĞI: fiyat okunamıyorsa `price=None` + `neden` (0 DEĞİL); bacak tipi okunamıyorsa
    `bacak=None` + neden — çağıran ikisinde de kitaba İŞLEMEZ, alarmda nedeni taşır."""
    if not isinstance(order, dict):
        return None
    for kayit in [order] + list(order.get("legs") or []):
        st = str(kayit.get("status", "")).lower()
        dolan = _filled_qty(kayit)
        if st not in ("filled", "partially_filled") and dolan <= 0:
            continue
        typ = str(kayit.get("type") or "").lower()
        bacak = "stop" if typ.startswith("stop") else ("hedef" if typ == "limit" else None)
        ham = kayit.get("filled_avg_price")
        try:
            price = float(ham) if ham not in (None, "") else None
        except (TypeError, ValueError):  # sessiz-yutma: fiyat parse edilemedi -> None + `neden` alanı; çağıran alarmda taşır, kitaba İŞLENMEZ (uydurma yasağı: 0 yazılmaz)
            price = None
        nedenler = []
        if price is None:
            nedenler.append(f"filled_avg_price okunamadı (ham={str(ham)[:24]!r})")
        if bacak is None:
            nedenler.append(f"bacak tipi okunamadı (type={typ!r})")
        return {"bacak": bacak, "price": price, "neden": "; ".join(nedenler),
                "filled_qty": dolan, "status": st}
    return None


def replace_order_stop(order_id: str, new_stop: float, cur_stop: float | None = None) -> dict:
    """Bir emrin (bracket stop bacağının) stop fiyatını DEĞİŞTİR (PATCH /v2/orders/{id}). Dinamik
    trailing-stop ayna senkronu için: iç defterin iz süren stop'u yükseldikçe aynadaki koruma da
    yükselir. Paper-kilitli.

    MONOTONLUK (A4): koruma ASLA gevşetilmez. Bunu eskiden yalnız çağıran
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


# ==================================================================================================
# KORUMANIN YENİDEN KURULMASI — ÇIPLAK KALAN POZİSYONA **OCO**
# ==================================================================================================
# NEDEN VAR (canlı vaka, A1 2026-08-07): dört motor pozisyonu broker'da KORUMASIZ duruyor ve açık
# emir SIFIR. Kök neden ölçüldü — bracket TIF'i emrin TAMAMINA uygulanır, `day` koruma bacaklarını
# her seans kapanışında öldürüyordu. E1-v2 TIF'i `gtc`ye çekti ama o düzeltme YALNIZ
# BUNDAN SONRA gönderilen bracket'ları bağlar; hâlihazırda çıplak duran pozisyonlar için bu depoda
# hiçbir yol yoktu. `watchdog.koruma_report()` onları GÖRÜYOR ama görmek düzeltmek değildir:
# bekçi haber verir, dokunmaz. Bu fonksiyon o boşluğun İCRA ucudur.
#
# ⚠ NEDEN OCO, NEDEN "İKİ AYRI EMİR" DEĞİL — BU BİR TASARIM TERCİHİ DEĞİL, BİR RİSK YASASI:
# hesapta `shorting_enabled=true`. Bağsız bir stop + bağsız bir limit gönderilirse hedef dolduğu an
# pozisyon kapanır ama stop CANLI kalır; fiyat sonradan stop'a inince o stop TETİKLENİR ve elde
# olmayan hisseyi satar — yani AÇIĞA SATIŞ açar. Ortaya çıkan hâl "korumasız"dan farklı ve daha
# kötü bir risktir: koruma diye kurulan mekanizmanın kendisi ters yönde bir pozisyon üretir.
# OCO (one-cancels-other) iki bacağı broker tarafında birbirine bağlar: biri dolduğunda öteki
# İPTAL edilir. Bu yüzden aşağıdaki gövde `order_class="oco"` ile TEK istek gönderir ve bu modülde
# iki bacağı ayrı ayrı gönderen bir yol BİLEREK yoktur.
#
# TIF `gtc` (E1-v2 yasası): `day` tam da bu vakanın kök nedeniydi. Sabit burada TEKRAR yazılmaz —
# `broker.PROTECTIVE_TIF` yok, ama `ENTRY_TIF`ten de TÜRETİLMEZ: giriş bacağının TIF'i bilinçli
# olarak `day` olabilir (bayat tetik yasası) ve koruma onu MİRAS ALMAMALIDIR.
# İki ayrı gerçek, iki ayrı sabit.
KORUMA_TIF = "gtc"
# ONAY JETONU — `CLOSE_ALL_CONFIRM` ile aynı gerekçe (A3): hiçbir otomatik yol (döngü, ajan, bekçi)
# bu kapıdan kazayla geçemez. Jetonu YALNIZ operatörün panodaki tuşu taşır.
KORUMA_ONAY_JETONU = "KORUMA-KUR"


def koruma_coid(symbol: str, when=None) -> str:
    """Koruma OCO'sunun birleştirme anahtarı — A2 önekini TAŞIR (sahiplik kanıtı, A3).

    DAKİKA ÇÖZÜNÜRLÜĞÜ BİLİNÇLİ ve iki yönlü tartıldı. Alpaca aynı `client_order_id`yi ikinci kez
    kabul etmez; yani anahtar ne kadar kaba olursa broker tarafında o kadar güçlü bir İKİNCİ
    idempotans katmanı doğar. Gün çözünürlüğü seçilseydi o katman en güçlü hâline gelirdi — ama
    aynı gün içinde koruma bir kez iptal edilip yeniden kurulmak istendiğinde yol KAPANIRDI ve bu,
    tam da "korumayı yeniden kuran yol" diye yazılan mekanizmanın kendi amacını yemesi olurdu.
    Dakika, çift-tıklamayı (asıl kaza sınıfı) yakalar, meşru yeniden kurmayı engellemez.
    BİRİNCİL idempotans bu değildir: o, gönderim öncesi canlı koruma denetimidir (api katmanı).

    ÖNEK BİR SÖZLEŞMEDİR: `KORUMA_COID_ONEK` aynı zamanda toplu süpürücünün AİLE KEMERİdir
    (`cancel_open_entries` → `coid_sinifi`). Bu yüzden burada elle yazılmaz, sabitten türetilir —
    iki yerde iki metin, 08-07'de dört korumayı öldüren çarpışmanın sessizce geri gelmesi olurdu."""
    stamp = (when or _dt.datetime.now(_dt.timezone.utc)).strftime("%Y%m%d-%H%M")
    return f"{KORUMA_COID_ONEK}{stamp}-{str(symbol).upper()}"


def submit_protective_oco(symbol: str, qty: float, stop_loss: float, take_profit: float,
                          client_order_id: str | None = None) -> dict:
    """Çıplak bir UZUN pozisyona koruma kur: TEK OCO satış emri (stop bacağı + hedef bacağı).

    ÇAĞIRANIN GETİRMESİ GEREKENLER ve bu sınırın KENDİ reddettikleri (kural çağıranda değil
    SINIRDA yaşasın diye — `replace_order_stop`un A4 dersi):
      * `qty` > 0 ve BROKER'ın söylediği adet olmalı. Bu fonksiyon adedi kendisi ölçmez, ama
        0/negatif/biçimsiz bir adedi de göndermez.
      * `stop_loss` < `take_profit`. Ters ya da eşit seviyeler bir koruma değil, anında dolacak
        bir emirdir; Alpaca da reddederdi — ama reddi burada ÖLÇÜLÜ bir gerekçeyle almak, ağa
        çıkıp sağlayıcı diliyle bir hata metni toplamaktan iyidir.
      * `client_order_id` A2 önekini TAŞIMAK ZORUNDA. Öneksiz bir emir mutabakat için GÖRÜNMEZDİR:
        dolduğunda 'motor yetimi' bile sayılmaz, operatörün kendi emri gibi 'external' altına
        düşer (A3 sahipliği kaybolur). `submit_bracket` bu durumda yalnız UYARIYOR; burada
        REDDEDİLİR, çünkü bu yol operatör onayıyla tek seferlik çalışır ve bir sonraki turda
        "kim gönderdi?" sorusunun cevabı yalnız bu önektir.

    Dönüş: {ok, order|detail, reachable}. `reachable=False` YALNIZ taşıma düştüğünde — 4xx bir
    REDdir ve broker ULAŞILABİLİRdir (`submit_bracket` ile aynı ayrım; çağıran bunları farklı
    raporlar, biri "gitmedi", öteki "reddedildi")."""
    sym = str(symbol or "").strip().upper()
    if not sym:
        return {"ok": False, "detail": "sembol verilmedi", "reachable": True}
    try:
        q = abs(float(qty))
        sl, tp = float(stop_loss), float(take_profit)
    except (TypeError, ValueError):  # sessiz-yutma: istisna SESSİZCE yutulmaz, REDDE çevrilir — üç ham değer gerekçede aynen döner ve emir GİTMEZ; ikinci bir uyarı kanalı, çağıranın zaten okuduğu `detail`i tekrarlardı
        return {"ok": False, "detail": f"biçimsiz sayı (qty={qty!r} stop={stop_loss!r} "
                                       f"hedef={take_profit!r})", "reachable": True}
    if q <= 0:
        return {"ok": False, "detail": "qty<=0 — BROKER adedi okunamadı; uydurma adet gönderilmez",
                "reachable": True}
    if not (sl > 0 and tp > 0):
        return {"ok": False, "detail": f"seviye ≤0 (stop={sl} hedef={tp})", "reachable": True}
    if sl >= tp:
        return {"ok": False, "detail": f"stop hedefin ÜSTÜNDE/EŞİT (stop={sl} hedef={tp}) — bu bir "
                                       f"koruma değil, anında dolacak bir emir", "reachable": True}
    coid = str(client_order_id or koruma_coid(sym))
    if not coid.startswith(ENGINE_COID_PREFIX):
        return {"ok": False, "reachable": True,
                "detail": f"client_order_id '{ENGINE_COID_PREFIX}' önekini taşımıyor ({coid[:40]}) — "
                          f"sahipliği kanıtlanamayan emir gönderilmez (A2/A3)"}
    body = {"symbol": sym, "qty": str(int(q) if float(q).is_integer() else q), "side": "sell",
            "type": "limit", "time_in_force": KORUMA_TIF, "order_class": "oco",
            "take_profit": {"limit_price": round(tp, 2)},
            "stop_loss": {"stop_price": round(sl, 2)},
            "client_order_id": coid}
    try:
        r = httpx.post(f"{_paper_base()}/v2/orders", headers=_headers(), json=body, timeout=15)
        _note(True)                      # cevap geldi: 4xx bile olsa broker ULAŞILABİLİR
        if r.status_code >= 400:
            try:
                det = r.json().get("message", f"HTTP {r.status_code}")
            except Exception:  # sessiz-yutma: gövde JSON değil (sağlayıcı HTML/boş dönebilir); durum kodu tek başına yeterli kanıttır
                det = f"HTTP {r.status_code}"
            return {"ok": False, "detail": str(det)[:200], "reachable": True, "coid": coid}
        return {"ok": True, "order": r.json(), "coid": coid, "reachable": True}
    except Exception as e:
        # ULAŞILAMADI ≠ REDDEDİLDİ: emir uca varmış ve kabul edilmiş DE olabilir. Çağıran bu satırı
        # "gönderilmedi" diye raporlarsa sessizce yalan söyler — ölçülen tek şey CEVABIN alınamadığı.
        _note(False, f"submit_protective_oco: {type(e).__name__}: {e}")
        return {"ok": False, "detail": f"{type(e).__name__}: {e}", "reachable": False, "coid": coid}


def close_all(confirm: str = "") -> dict:
    """Cancel open orders + flatten all PAPER positions. Operator panic control for the mirror account.

    SAHİPLİK + KAZA KORUMASI (A3): bu çağrı motorun SAHİBİ OLMADIĞI pozisyonları
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
# AYNI-AKŞAM GÜNLÜK BAR BACAĞI — VERİ UCU (data.alpaca.markets), TİCARET UCUNDAN AYRI
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
# aynı ilke): kilitlenecek girdi yok, kimlik-sızıntı vektörü yok. Bu yoldan emir geçemez.
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
