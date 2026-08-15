"""adapters/finviz.py — Finviz momentum/kırılım ekranını OTONOM ADAY KAYNAĞI yapan keşif adaptörü.

(a) Ne yapar: Finviz screener'ından "bugün momentum/kırılım ekranında olanlar"ın ticker listesini
döndürür — rolü EVRENİ GENİŞLETMEK, karar vermek DEĞİL. Bu ticker'ların barları bar zincirinden
çekilir ve Meridian'ın kendi vcp/pullback/momentum yasası + kapısı yine karar verir; Finviz'in
kırılganlığı (public scraping, kısa Elite trial) karar mantığına SIZAMAZ, yalnız evrenin genişliğini
etkiler. İki kaynak yolu: Elite CSV export (elite.finviz.com/export/screener — kanonik yol; eski
.ashx uçları 301 döner ve follow_redirects olmadan gövde BOŞ gelir, geçerli token 'çalışmıyor'
sanılırdı) ve public HTML (finviz.com/screener.ashx, httpx + regex, bs4 yok).
(b) Kilit girişler: discover() (kaynak etiketli sonuç), discover_universe() (dataset.load_live'ın
çağırdığı günlük-önbellekli otonom yol), export_rows() (yalnız skill yüzeyi — tam CSV satırları;
sağlık karnesini bilerek kirletmez), ping(), health(), status(); PRESETS/DEFAULT_PRESET,
MAX_TICKERS, MERIDIAN_FINVIZ_PUBLIC ortam değişkeni.
(c) Değişmezler — DÜRÜST BOZUNMA: discover() HER ZAMAN kaynak etiketiyle döner
(elite | public | none + reason); boş dönüş sessiz değildir — evren REPLAY_UNIVERSE'e düşer, olay
kaydedilir. "Aday bulunamadı" ile "Finviz'e ulaşılamadı" asla aynı görünmez. Public scraping
ToS-riskli olduğundan otonom döngüde VARSAYILAN KAPALIDIR (yalnız MERIDIAN_FINVIZ_PUBLIC=1 ya da
elle çağrı). elite() = token VAR demektir, çalışıyor demek değil. Makullük bandı (_plausible) hem
kurt-masalını hem parse patlamasını (tüm sayfayı ticker sanmak) reddeder. GİZLİLİK: token yalnız
`auth` sorgu parametresinde gider; httpx hata metni tam URL taşıdığından mesajlar KAYNAĞINDA
maskelenir — token asla loglanmaz, panoya son-4 dışında çıkmaz.
(d) Okur/yazar, önbellek: state/finviz_universe.json — günlük evren önbelleği (aynı gün ikinci çağrı
ağa gitmez; anahtar sunucunun yerel takvim günü) + "none" hâlinde uyarı-kadansı mandalı (durum
değişmedikçe günde en fazla 1 uyarı; bastırılan tekrarlar sayılır ve status()'ta görünür)."""
from __future__ import annotations

import csv as _csv
import io as _io
import re as _re
import time as _time

import httpx

from .. import secrets

# OPERATÖR FINVIZ NOTU: kanonik export yolu artık `/export/screener`. Eski `.ashx`
# uçları ÇALIŞIR ama 301 REDIRECT döner — httpx (curl gibi) varsayılan olarak yönlendirmeyi İZLEMEZ
# ve BOŞ gövde alır. Eski değer `export.ashx` idi: geçerli bir token'la bile CSV boş gelir, 0 satır
# parse edilir ve `_plausible([])` False olduğu için token SESSİZCE "çalışmıyor" sanılırdı. İki kat
# koruma: (1) kanonik yolu kullan, (2) `_fetch_elite`te follow_redirects=True (Finviz yeniden
# yönlendirse de gövde gelsin). Bu, bu kod tabanının "sessiz boş ≠ başarısızlık" yasasının ta kendisi.
ELITE_EXPORT = "https://elite.finviz.com/export/screener"
PUBLIC_SCREENER = "https://finviz.com/screener.ashx"
_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"

# MOMENTUM/KIRILIM KEŞİF PRESETİ. Bilinçli olarak Meridian'ın giriş kapısından GEVŞEK: amaç kapıyı
# taklit etmek (çift-filtre) değil, kapıya bakmaya değer likit + trendde + güçlü bir EVREN vermek.
# Kendi vcp/pullback/momentum yasası sonra karar verir.
#   sh_avgvol_o500  ortalama hacim > 500K (likidite)
#   sh_price_o10    fiyat > $10 (mikro-cap gürültüsü hariç)
#   ta_sma50_pa     fiyat 50-günlük ortalama ÜSTÜNDE (yukarı trend)
#   ta_perf_13w10o  son 13 hafta performans > +10% (momentum)
PRESETS: dict[str, str] = {
    "momentum": "sh_avgvol_o500,sh_price_o10,ta_sma50_pa,ta_perf_13w10o",
    "breakout": "sh_avgvol_o750,sh_price_o10,ta_highlow52w_b0to10h,ta_sma200_pa",
}
DEFAULT_PRESET = "momentum"
MAX_TICKERS = 150            # tavan: Finviz evreni FMP bar çekimini şişirmesin (kota + süre)
CACHE_FILE = "finviz_universe.json"
_TICKER_RE = _re.compile(r"quote\.ashx\?t=([A-Z][A-Z.\-]{0,9})")

_HEALTH: dict = {"ok": None, "source": None, "n": 0, "calls": 0, "fails": 0,
                 "last_status": None, "last_error": "", "at": None}


def elite() -> bool:
    """Elite token VAR demektir — çalışıyor demek DEĞİL (fmp.available'ın öğrettiği ayrım). Süresi
    dolmuş bir trial token'ı da present=True'dur; gerçek durumu health() ve discover().source söyler."""
    return secrets.present("FINVIZ_API_KEY")


def health() -> dict:
    """Finviz screener yolunun son durumunun kopyası (ok/kaynak/n, çağrı-hata sayaçları, son HTTP
    kodu ve maskelenmiş hata). Token'ın VARLIĞI değil, çağrının GERÇEKTEN üretip üretmediğini söyler."""
    return dict(_HEALTH)


def _mask_url(msg: str) -> str:
    """httpx hata metni tam URL taşır; auth token'ı orada olabilir. Kaynağında maskele."""
    return _re.sub(r"(auth=)[^&\s]+", r"\1***", str(msg))


def _note(ok: bool, source: str | None, n: int, status=None, error: str = "") -> None:
    """Bir çekim denemesini `_HEALTH`e işler: çağrı/başarısızlık sayaçlarını artırır, kaynak-sonuç-
    HTTP kodunu ve _mask_url'den geçirilmiş (auth token'ı gizlenmiş) hata metnini damgayla saklar."""
    _HEALTH["calls"] += 1
    if not ok:
        _HEALTH["fails"] += 1
    _HEALTH.update({"ok": ok, "source": source, "n": int(n), "last_status": status,
                    "last_error": _mask_url(error)[:200], "at": _now_iso()})


def _now_iso() -> str:
    """Şu anın UTC ISO-8601 damgası (saniye çözünürlüğünde, mikrosaniyesiz) — sağlık kayıtları için."""
    import datetime as _dt
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat()


def _plausible(tickers: list[str]) -> bool:
    """Kurt masalı yasağı + zehirli veri koruması: bir avuç sembol screener'ın koştuğunu kanıtlamaz,
    ama 5000 sembol de bir parse hatası (tüm sayfayı ticker sanmak) demektir. Makul bant."""
    return 1 <= len(tickers) <= 3000 and all(1 <= len(t) <= 10 for t in tickers)


def export_rows(filters: str, timeout: float = 20.0, view: str = "111") -> list[dict]:
    """Elite CSV export — TAM SATIRLAR (CSV başlıklarıyla dict listesi).

    TÜKETİCİ: skill yüzeyi (skills/finviz-screener). news.py'deki "skill-surface only" emsali:
    bu fonksiyonun ÜRETİM/karar tüketicisi YOKTUR — otonom döngü `discover()` üzerinden yalnız
    ticker listesi alır. Burası operatörün terminalden tam tabloyu görmesi içindir; bu yüzden
    `_note`/`_plausible` (sağlık sayacı ve makullük bandı) bilinçli olarak ÇAĞRILMAZ: skill
    çağrıları otonom kaynağın sağlık karnesini kirletmemeli.

    Kanonik uç TEK KAYNAKTA: ELITE_EXPORT (yukarıdaki 2026-07-23 notu — `.ashx` bayat, 301 döner).
    Skill kendi URL'ini KURMAZ, buraya gelir.

    KOLON SETİNİ FINVIZ BELİRLER: hangi sütunların geleceği `v=` (view) parametresine bağlıdır
    (111 overview, 121 valuation, 171 technical…). Bu fonksiyon CSV başlıklarını OLDUĞU GİBİ
    geçirir — sütun adı normalleştirilmez, türetilmez, UYDURULMAZ. Çağıran ne geldiyse onu görür.

    `filters` yalnız `f=` değeridir (ham filtre kodları, virgüllü) — `_fetch_elite`'in ilk günden
    beri taşıdığı sözleşme; `v=`/`f=`/`auth=` ayrımını URL'i kuran BURASI yapar.
    """
    token = secrets.get("FINVIZ_API_KEY")
    if not token:
        raise RuntimeError("FINVIZ_API_KEY absent")
    params = {"v": view, "f": filters, "auth": token}
    # follow_redirects=True ZORUNLU: Finviz eski/alternatif yolları 301'le kanonik export'a taşır;
    # izlenmezse gövde BOŞ gelir ve geçerli token 'çalışmıyor' sanılır (operatör notu).
    r = httpx.get(ELITE_EXPORT, params=params, timeout=timeout,
                  headers={"User-Agent": _UA}, follow_redirects=True)
    # 401/403 = token geçersiz/süresi dolmuş (1 haftalık trial bitti). Bu bir OLAY, sessizlik değil.
    try:
        r.raise_for_status()
    except httpx.HTTPStatusError as e:
        # GİZLİLİK: httpx'in hata metni TAM URL taşır, yani `auth=<token>`. Skill yolunda bu metin
        # doğrudan terminale basılıyor — KAYNAĞINDA maskele. TÜR ve `.response` korunur, çünkü
        # discover()/ping() bu istisnadan `status_code` okuyup 401/403'ü ağ hatasından ayırıyor.
        # `from None`: zincirlenen özgün istisnanın MASKESİZ metni traceback'e düşmesin.
        raise httpx.HTTPStatusError(_mask_url(str(e)), request=e.request,
                                    response=e.response) from None
    return list(_csv.DictReader(_io.StringIO(r.text)))


def _fetch_elite(filters: str, timeout: float) -> list[str]:
    """Elite CSV export → yalnız ticker listesi (otonom keşif yolunun ihtiyacı bu kadar).
    Ağ/parse/maskeleme işi export_rows'ta — kanonik uç tek yerde kalsın. Burada kalan tek iş
    'Ticker' sütununu sırayı koruyarak tekilleştirmek."""
    out, seen = [], set()
    for row in export_rows(filters, timeout):
        t = (row.get("Ticker") or row.get("ticker") or "").strip().upper()
        if t and t not in seen:
            seen.add(t)
            out.append(t)
    return out


def _fetch_public(filters: str, timeout: float, pages: int = 5) -> list[str]:
    """Public HTML fallback — Elite token yok/ölü. bs4 bu ortamda yok; httpx + regex ile ticker
    linklerini çıkar (`quote.ashx?t=TICKER`). KIRILGAN: Finviz HTML'i değişirse ya da bot koruması
    devreye girerse boş döner — bu yüzden yalnız fallback, ve dürüst bozunmayla sarılı."""
    out, seen = [], set()
    with httpx.Client(timeout=timeout, headers={"User-Agent": _UA},
                      follow_redirects=True) as cli:
        for p in range(pages):
            r = cli.get(PUBLIC_SCREENER, params={"v": "111", "f": filters, "r": str(1 + p * 20)})
            r.raise_for_status()
            found = _TICKER_RE.findall(r.text)
            fresh = [t for t in found if t not in seen]
            for t in fresh:
                seen.add(t)
                out.append(t)
            if not fresh:                        # bu sayfa yeni sembol getirmedi → son sayfa
                break
            _time.sleep(0.5)                     # nazik hız sınırı (public erişim)
    return out


def discover(preset: str = DEFAULT_PRESET, limit: int = MAX_TICKERS,
             timeout: float = 20.0, allow_public: bool = True) -> dict:
    """Finviz momentum/kırılım evrenini döndür. HER ZAMAN kaynak etiketiyle:
        {"tickers": [...], "source": "elite"|"public"|"none", "reason": str, "preset": str}
    Sıra: Elite (token varsa) → public (izinliyse) → boş. Hiçbir dal sessizce boş dönmez.

    allow_public: public HTML scraping ToS-riskli ve ban getirebilir. Otonom günlük döngü onu
    VARSAYILAN OLARAK KULLANMAZ (bkz. discover_universe): token yoksa Finviz dürüstçe devre dışı
    kalır, sürekli scraping yapılmaz. Public yalnız operatör açıkça açtığında (MERIDIAN_FINVIZ_PUBLIC=1)
    ya da manuel/test çağrısında denenir."""
    filters = PRESETS.get(preset) or PRESETS[DEFAULT_PRESET]

    # 1) Elite — token varsa ilk tercih (kararlı, ToS-uygun)
    if elite():
        try:
            tk = _fetch_elite(filters, timeout)
            if _plausible(tk):
                _note(True, "elite", len(tk))
                return {"tickers": tk[:limit], "source": "elite", "reason": "", "preset": preset}
            _note(False, "elite", len(tk), error=f"makul dışı sayı: {len(tk)}")
        except httpx.HTTPStatusError as e:
            code = e.response.status_code
            # 401/403 = trial süresi dolmuş / token geçersiz → public'e düş (sessiz değil)
            _note(False, "elite", 0, status=code, error=_mask_url(str(e)))
        except Exception as e:  # ağ/parse — public'e düş
            _note(False, "elite", 0, error=f"{type(e).__name__}: {_mask_url(str(e))}")

    if not allow_public:
        return {"tickers": [], "source": "none", "preset": preset,
                "reason": ("Elite token yok/çalışmadı; public scraping otonom döngüde kapalı "
                           "(ToS/ban koruması — MERIDIAN_FINVIZ_PUBLIC=1 ile açılır)")}

    # 2) Public HTML fallback (yalnız izinliyse buraya gelinir)
    try:
        tk = _fetch_public(filters, timeout)
        if _plausible(tk):
            _note(True, "public", len(tk))
            return {"tickers": tk[:limit], "source": "public", "reason": "", "preset": preset}
        _note(False, "public", len(tk), error=f"makul dışı sayı: {len(tk)}")
        return {"tickers": [], "source": "none", "preset": preset,
                "reason": f"public parse makul dışı ({len(tk)} sembol) — HTML değişmiş olabilir"}
    except Exception as e:
        _note(False, "public", 0, error=f"{type(e).__name__}: {_mask_url(str(e))}")
        return {"tickers": [], "source": "none", "preset": preset,
                "reason": f"Finviz'e ulaşılamadı: {type(e).__name__}"}


def discover_universe(preset: str = DEFAULT_PRESET, limit: int = MAX_TICKERS,
                      use_cache: bool = True, allow_public: bool | None = None) -> list[str]:
    """dataset.load_live()'ın çağırdığı OTONOM yol: günlük önbellekli ticker listesi. Aynı gün ikinci
    çağrı ağa gitmez. Finviz düşükse BOŞ liste döner — çağıran evreni REPLAY_UNIVERSE ile kurar (dürüst
    bozunma). Kaynak/olay her hâlde `finviz_universe.json`'a ve olay defterine yazılır; boş ≠ sessizlik.

    allow_public None ise MERIDIAN_FINVIZ_PUBLIC ortam değişkeninden okunur (varsayılan KAPALI): token
    yoksa otonom döngü sürekli public scraping yapıp ban riski almaz — Finviz dürüstçe devre dışı kalır.

    ---- ÖRTÜK ZAMAN VARSAYIMI, ARTIK YAZILI ----------------
    T+1 kusurunun sınıfı "kodda örtük yayın-zamanı/TTL varsayımı"ydı. Bu fonksiyonun da BİR TANE
    var ve bugüne dek hiçbir yerde yazmıyordu. ÖLÇÜLDÜ, DEĞİŞTİRİLMEDİ (bugün DOĞRU çalışıyor):

    ÖNBELLEK ANAHTARI SUNUCUNUN YEREL TAKVİM GÜNÜDÜR (`date.today()`), seans değil. Zincir şöyle
    işliyor — `scheduler.advance_once` her poll'de `dataset.load_live(use_cache=not fresh)` çağırır:
      * `fresh=True` (seans kapandı, bar kovalanıyor) → `use_cache=False` → ZORUNLU ağ çekimi.
        Bu KAPANIŞ SONRASIDIR ve doğru olan da budur: seans İÇİNDE çekilseydi `ta_perf_13w10o` /
        `ta_sma50_pa` gibi filtreler GÜN İÇİ değerlerle eşleşir, yani kapanmamış bir günün ekranı
        kapanmış gibi okunurdu.
      * `use_cache=True` iken bile önbellek TARİHİ TUTMUYORSA aşağıdaki `if` bloğu return ETMEZ ve
        akış `discover()`a düşer — yani gün dönümünden sonraki İLK poll de ağa çıkar. Günde iki
        çekim olmasının sebebi budur (biri kovalamada, biri yerel gece yarısında).
    VARSAYIM: "sunucunun yerel gün sınırı NY seansının (13:30-20:00 UTC) DIŞINA düşer." UTC'de,
    Amerika'da ve Avrupa'da doğru. UTC+10:30…+14 (Avustralya/Yeni Zelanda/Pasifik) bir kutuda
    yerel gece yarısı seansın İÇİNE düşer ve o gün-dönümü çekimi GÜN İÇİ değerleri önbelleğe yazar.
    Bugünkü koşum yerleri bu bantta DEĞİL (geliştirme makinesi UTC+3; A1 sunucusunun TZ'si bu
    depodan doğrulanamadı — systemd birimi TZ ayarlamıyor, sistem varsayılanını miras alıyor).
    UCUZ ÇÖZÜM (uygulanmadı — bugün bir kusur yok, yalnız yazısız bir varsayım vardı): anahtarı
    `date.today()` yerine SON KAPANMIŞ SEANSA bağlamak. Hem varsayımı ortadan kaldırır hem günde
    iki olan çekimi bire indirir. Saat dilimi kararı ve keşif ritmi Rol 1'e aittir."""
    from .. import store, obs
    import datetime as _dt
    import os as _os
    if allow_public is None:
        allow_public = _os.environ.get("MERIDIAN_FINVIZ_PUBLIC") == "1"
    today = _dt.date.today().isoformat()
    if use_cache:
        c = store.read_json(CACHE_FILE, {}) or {}
        if c.get("date") == today and c.get("source") in ("elite", "public"):
            return list(c.get("tickers") or [])

    res = discover(preset=preset, limit=limit, allow_public=allow_public)
    rec = {"date": today, "source": res["source"], "preset": res["preset"],
           "reason": res.get("reason", ""), "n": len(res["tickers"]),
           "tickers": res["tickers"], "at": _now_iso()}
    if res["source"] == "none":
        # DÜRÜST BOZUNMA: Finviz katkısı bu tur sıfır; NEDENİ söyle, sessiz kalma.
        #
        # UYARI KADANSI ≠ KEŞİF KADANSI (gelen-kutusu hijyeni). "none" kaydı yukarıdaki
        # önbellek kapısını ASLA geçemez (source ∈ {elite, public} şartı), yani token yokken HER
        # keşif turu buraya düşüyordu → canlıda ~5 dakikada bir `finviz_unavailable` (~200+/gün).
        # Yürürlükteki hüküm FINVIZ alınmayacak diyor; değişmeyen bir yokluğu günde 200 kez anlatmak
        # gerçek alarmları okunmaz yapar. KEŞİF DENEMESİ AYNEN SÜRÜYOR (token gelirse davranış bu
        # satırlara dokunmadan kendiliğinden canlanır); yalnız UYARI kadansı düşer:
        #   * durum (source=none + AYNI reason) değişmedikçe günde EN FAZLA 1 uyarı,
        #   * reason DEĞİŞİRSE (başka bir arıza sınıfı) aynı gün bile ANINDA yeni uyarı,
        #   * bastırılan her tekrar SAYILIR — sayaç bu kayıtta (`bastirilan`) durur,
        #     `status()["last"]` onu panoya taşır; günlük uyarı satırı da toplamı üstünde taşır.
        onceki = store.read_json(CACHE_FILE, {}) or {}
        ayni_durum = (onceki.get("source") == "none"
                      and onceki.get("reason") == rec["reason"])
        rec["ilk_gorulme"] = ((onceki.get("ilk_gorulme") if ayni_durum else None)
                             or rec["at"])
        rec["bastirilan"] = int(onceki.get("bastirilan") or 0) if ayni_durum else 0
        rec["uyarildi_gun"] = today
        if ayni_durum and onceki.get("uyarildi_gun") == today:
            rec["bastirilan"] += 1        # bugün zaten uyarıldı → satır yok, sayaç var
            store.write_json(CACHE_FILE, rec)
        else:
            store.write_json(CACHE_FILE, rec)
            obs.warn("finviz_unavailable", reason=res.get("reason", ""), preset=preset,
                     detail="evren yalnız REPLAY_UNIVERSE ile kuruldu — Finviz keşfi bu tur devre "
                            "dışı. Tekrarlar günde 1'e mandallı (EDG-2026-022; durum değişirse "
                            "anında yeniden uyarılır) — sayaç: state/" + CACHE_FILE,
                     ilk_gorulme=rec["ilk_gorulme"], bastirilan_toplam=rec["bastirilan"])
    else:
        store.write_json(CACHE_FILE, rec)
        obs.log("finviz_universe", source=res["source"], n=len(res["tickers"]), preset=preset)
    return list(res["tickers"])


def ping() -> dict:
    """Canlı token doğrulaması — Ayarlar'daki 'Test et' düğmesi bunu çağırır. Elite export'a GERÇEK bir
    istek atıp {ok, detail} döner; token'ı ASLA döndürmez, hata metnini maskeler.

    fmp.ping / alpaca.ping ile aynı sözleşme: ok=False iken 'detail' NEDENİ söyler (token yok / süresi
    dolmuş / ulaşılamadı) ki operatör 401'i (yanlış token) geçici ağ hatasından ayırabilsin. Boş/301
    gövdesi de ayrı bir 'detail' verir — az önce düzelttiğimiz sessiz-boş tuzağı görünür olsun."""
    if not elite():
        return {"ok": False, "detail": "Finviz Elite token girilmemiş"}
    try:
        tk = _fetch_elite(PRESETS[DEFAULT_PRESET], timeout=15.0)
    except httpx.HTTPStatusError as e:
        code = e.response.status_code
        _note(False, "elite", 0, status=code, error=_mask_url(str(e)))
        if code in (401, 403):
            return {"ok": False, "detail": f"token geçersiz/süresi dolmuş (HTTP {code})"}
        return {"ok": False, "detail": f"HTTP {code}"}
    except Exception as e:
        _note(False, "elite", 0, error=f"{type(e).__name__}: {_mask_url(str(e))}")
        return {"ok": False, "detail": f"bağlanılamadı ({type(e).__name__})"}
    if not _plausible(tk):
        _note(False, "elite", len(tk), error=f"makul dışı sayı: {len(tk)}")
        return {"ok": False, "detail": f"beklenmedik yanıt ({len(tk)} sembol) — boş gövde/301 ya da erişim sorunu"}
    _note(True, "elite", len(tk))
    return {"ok": True, "detail": f"bağlandı · {len(tk)} aday ({DEFAULT_PRESET} preset)"}


def status() -> dict:
    """Pano/API görünürlüğü: kaynak, sayı, token durumu (son-4 maskeli), son çekim."""
    from .. import store
    c = store.read_json(CACHE_FILE, {}) or {}
    # `uyarildi_gun`/`bastirilan`/`ilk_gorulme`: uyarı-kadansı mandalının DIŞ okuyucusu (YASA-6) —
    # "bugün kaç deneme bastırıldı" pano/API'de görünür kalır, susturmak yok saymak değildir.
    return {"elite_token": secrets.mask(secrets.get("FINVIZ_API_KEY")),
            "health": health(),
            "last": {k: c.get(k) for k in ("date", "source", "n", "reason", "at",
                                           "uyarildi_gun", "bastirilan", "ilk_gorulme")},
            "presets": sorted(PRESETS)}
