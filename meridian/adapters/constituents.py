"""adapters/constituents.py — point-in-time S&P 500 üyeliği: FMP birincil, Wikipedia en iyi-çaba
ikincil; makullük kapılı önbellek ve evren-sapma raporu.

(a) Ne yapar: güncel S&P 500 üyelik listesini kaynak zincirinden kurar (FMP sp500-constituent —
anahtarlı ve zaten kullanımda olduğu için BİRİNCİL; Wikipedia List_of_S%26P_500_companies sayfası
en iyi-çaba İKİNCİL) ve değişiklik günlüğünü geriye sararak `as_of(date)` ile tarihsel üyeliği
yeniden kurar. Gerçek üretim tüketicisi `universe_drift()`tir: elle bakımlı REPLAY_UNIVERSE'ü
güncel üyelik + verisiz-sembol defteri + emeklilik defteriyle karşılaştırıp ölü/geri-sızmış
isimleri söyler. Wikipedia yolu bu kurulumda fiilen kapalıdır: sayfa bu User-Agent'a HTTP 403
döner; health() nedeni ADIYLA yazar (UA/kaynak değişirse yol kendiliğinden çalışır).
(b) Kilit girişler: current(use_cache=...), as_of(date), as_of_pit_durumu(date), universe_drift(),
health(); MIN_MEMBERS makullük tabanı, CACHE (sp500_constituents.json).
(c) Değişmezler — MAKULLUK KAPISI: 400'den az sembol S&P 500 DEĞİLDİR; hem çekim hem önbellek
okuma bu kapıdan geçer (canlı önbelleğe bir test fikstürünün — 3 sembol, gelecek tarihli damga —
sızdığı yaşandı; kapı tam onu reddeder, gelecek tarihli `as_of` da bozuk sayılır). Başarısızlık
sessiz değildir: bayat/uydurma liste asla servis edilmez, hiçbir kaynak makul liste veremezse []
döner ve çağıran elle bakımlı evrene düşer. `as_of()`un [] dönüşü "o tarihte kimse yoktu" değil
"BİLMİYORUZ"dur. YANLIŞLANDI dersleri korunur: pandas 3'te read_html ham HTML dizgesini dosya-yolu
sanır ve FileNotFoundError üretir (2026-08-13 ölçümü) — girdi io.StringIO ile sarılır ve flavor="lxml" sabitlenir ki tablosuz 403 gövdesi "paket
eksik" gibi YANLIŞ sınıf yerine dürüst "No tables found" üretsin; değişiklik-günlüğü tarihleri
sözlüksel değil ISO'ya çevrilerek karşılaştırılır (aksi PIT kurulumunu tersine çevirmişti) ve
'nan' hücreleri temizlenir (hayalet 'NAN' sembolü üretmişti).
(d) Okur/yazar, önbellek: state/sp500_constituents.json — günlük önbellek (as_of=bugün ise ağa
gidilmez); yazım yalnız makul listeyle olur, kaynak etiketi (fmp|wikipedia) birlikte saklanır.
DÜRÜST SINIR: bu modül üyelik survivorship'ini düzeltir; yanlılıksız backtest delisted isimlerin
BARLARINI da ister ve ücretsiz kaynaklar onu taşımaz — PIT iskelesi, bias-free evren değil.
(e) TSK-154 (2026-09-05): Wikipedia sayfasındaki 'Selected changes' tablosu (eskiden `tables[1]`)
KALKTI — canlı önbellek 11 hayalet satır ({date:'',added:'',removed:''}) yazmıştı, uyarısız.
İki düzeltme: (1) `_fetch_tables` artık ÜÇ değer döner (`cur, changes, changes_kaynak`); tablo
gerçekten değişiklik sütunlarını taşımıyorsa (sütun eşleşmesi yok / IndexError) `changes=[]` +
`changes_kaynak=None` + `obs.warn("sp500_degisiklik_tablosu_yok", ...)` — Yasa 4: sessiz değil.
Üç alanı da boş olan satır (hayalet) hiçbir zaman `changes`e yazılmaz. (2) `as_of_pit_durumu(date)`
değişiklik günlüğü boşken `as_of()`un GERÇEK tarihsel yeniden kurulum değil bugünkü listeye eşit
survivorship döndüğünü BEYAN eder (`{"pit": False, "neden": "..."}`); `as_of()`un kendi dönüş
biçimi (`list[str]`) DEĞİŞMEDİ — üretim çağıranı bugün yok (test_constituents_audit_v18.py'nin
iki PIT testi + gerçek tüketici yok), pitlaw sınıfı `PIT_SOZLESMELI_BESLEYENI_KAPALI` AYNEN kalır."""
from __future__ import annotations
import datetime as dt

from .. import store

WIKI_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
CACHE = "sp500_constituents.json"
MIN_MEMBERS = 400          # S&P 500 ~503 isim; bunun altı "üyelik listesi" DEĞİLDİR (fixture/kırpık)
_HEALTH = {"ok": None, "source": None, "n": 0, "at": None, "error": ""}


def health() -> dict:
    """Kaynak gerçekten üretti mi? 'except: return []' ile yutulan her hata burada görünür kalır."""
    return dict(_HEALTH)


def _note(ok: bool, source: str | None = None, n: int = 0, error: str = "") -> None:
    """Son çekim denemesinin sonucunu (başarı, kaynak etiketi, sembol sayısı, kırpılmış hata metni)
    UTC damgasıyla `_HEALTH`e yazar; health() bunu okur. HATA≠BOŞ: yutulan hata burada görünür kalır."""
    _HEALTH.update({"ok": ok, "source": source, "n": int(n), "error": error[:200],
                    "at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")})


def _plausible(members) -> bool:
    """MAKULLUK KAPISI: bir üyelik listesi ancak yeterince büyük ve sembol-şeklindeyse kabul edilir.
    Diskteki sahte önbellek (3 sembol) tam da buradan geçemezdi (denetim turu 3)."""
    if not isinstance(members, list) or len(members) < MIN_MEMBERS:
        return False
    good = [m for m in members if isinstance(m, str) and 1 <= len(m.strip()) <= 6
            and _tick(m) and all(ch.isalnum() or ch == "-" for ch in m.strip())]
    return len(good) >= MIN_MEMBERS


def _cached() -> dict:
    """Önbelleği OKU ve makullükten geçir. Geçemezse boş — bayat/uydurma veri asla servis edilmez."""
    d = store.read_json(CACHE, {}) or {}
    if d.get("current") and not _plausible(d.get("current")):
        try:
            from .. import obs
            obs.warn("constituents_cache_invalid", n=len(d.get("current") or []),
                     as_of=str(d.get("as_of"))[:10])
        except Exception:  # sessiz-yutma: kayıt kanalının kendisi düştü — ikinci bir kanal yok; kayıt denemesi çağıranı düşüremez
            pass
        return {}
    # gelecek tarihli damga = bozuk yazım (fixture'da "2099-01-01" vardı); tazelik kontrolü anlamsızlaşır
    try:
        if d.get("as_of") and dt.date.fromisoformat(str(d["as_of"])[:10]) > dt.date.today():
            return {}
    except ValueError:  # sessiz-yutma: ağ/sağlayıcı hatası bu yolun NORMAL hâli; çağıran boş sonuç üzerinden yedek kaynağa düşer ve kaynak seçimi ayrıca kaydedilir
        return {}
    return d


def _fetch_tables():
    """(current_symbols, changes, changes_kaynak) — Wikipedia'dan. Başarısızlıkta (None, None, None)
    AMA sebebi kaydederek. NOT: Wikipedia botlara 403 dönebilir (2026-08-13'te bu UA ile hâlâ
    dönüyor) ve ayrıştırıcı eksikliği de olabilir; ikisi de `health()`te AYRI nedenlerle görünür.

    TSK-154 (2026-09-05): `tables[1]` eskiden 'Selected changes' değişiklik günlüğüydü; sayfa bu
    tabloyu KALDIRDI (bugün section 1 tek tablo taşıyor, section 2 'See also'). Eski kod sütun
    eşleşmesi olmasa da BOŞ satırlar üretip yazıyordu (`{date:'',added:'',removed:''}` × 11, canlı
    önbellekte bulundu) — hiç uyarı yok. Artık: (a) sütunlardan biri (tarih/eklenen/çıkan) hiç
    eşleşmezse tablo 'değişiklik günlüğü DEĞİL' sayılır → `changes=[]`, `changes_kaynak=None`,
    `obs.warn` (Yasa 4); (b) üç alanı da boş olan satır (hayalet) hiç `changes`e yazılmaz."""
    try:
        import io
        import pandas as pd
        import httpx
        r = httpx.get(WIKI_URL, timeout=20, headers={"User-Agent": "Meridian/1.0"},
                      follow_redirects=True)
        if r.status_code >= 400:
            _note(False, "wikipedia", 0, f"HTTP {r.status_code}")
            return None, None, None
        # `pd.read_html(r.text)` — HAM DİZGE — pandas 3'te DOSYA YOLU sanılıyor.
        # Canlı kanıt: universe_drift.json `reason: "FileNotFoundError: ... <!DOCTYPE html>..."`;
        # yani evren denetimi survivorship kanıtı üretmiyordu ve neden diye YANLIŞ bir sınıf
        # (dosya yok) yazıyordu. `io.StringIO` pandas'ın KENDİ geçiş yolu (2.1'de uyarı, 3.0'da
        # hata) — davranışı değiştirmez, yalnız girdiyi "bu bir yol değil, içerik" diye işaretler.
        #
        # `flavor="lxml"` DE BİLEREK: varsayılan zincir lxml TABLO BULAMAZSA bs4+
        # html5lib'e düşer ve html5lib kurulu olmadığı için hata `ImportError: Import html5lib
        # failed` olur. Ölçüldü: 403 gövdesi (141 bayt, tablosuz) tam bunu üretiyor — yani gerçek
        # sebep "tablo yok" iken `health()` "paket eksik" diye YANLIŞ sınıf yazardı ve bu, bu
        # dosyanın başlığındaki (a) beyanını çürüten aynı yanlış-teşhis döngüsünü yeniden kurardı.
        # lxml sabitlenince tablosuz gövde dürüstçe `ValueError: No tables found` verir.
        tables = pd.read_html(io.StringIO(r.text), flavor="lxml")
    except Exception as e:
        _note(False, "wikipedia", 0, f"{type(e).__name__}: {e}")
        return None, None, None
    cur = None
    try:
        cur = [str(s).strip().upper().replace(".", "-") for s in tables[0]["Symbol"].tolist()]
    except Exception:  # sessiz-yutma: yardımcı/telemetri yolu; başarısızlığı karara girmez ve çağıran yedek değerle aynen devam eder
        cur = None
    changes, changes_kaynak = [], None
    try:
        ch = tables[1]
        ch.columns = ["_".join(str(x) for x in c) if isinstance(c, tuple) else str(c) for c in ch.columns]
        dcol = next((c for c in ch.columns if "Date" in c), None)
        acol = next((c for c in ch.columns if "Added" in c and "Ticker" in c), None)
        rcol = next((c for c in ch.columns if "Removed" in c and "Ticker" in c), None)
        if dcol is None or acol is None or rcol is None:
            # TSK-154: tablo VAR ama değişiklik günlüğü SÜTUNLARI yok — Wikipedia'nın
            # kaldırdığı 'Selected changes' tablosu değil, başka bir tablo (`tables[1]` artık
            # 'See also' ya da benzeri). Sessizce boş `changes` yazmak yerine adıyla uyarılır.
            raise ValueError(f"değişiklik günlüğü sütunları eşleşmedi: {list(ch.columns)[:6]}")
        # NaN-safe cell read (L3): pandas reads an empty change-log cell as float('nan'), and bool(nan) is
        # True, so `nan or ""` returned nan and str(nan)=='nan' — as_of() then added a fabricated 'NAN'
        # ticker to point-in-time membership. Coalesce NaN/None to "" explicitly.
        def _cell(v):
            """Wikipedia değişiklik-günlüğü hücresini NaN-güvenli dizgeye çevirir: None/NaN → ""
            (aksi hâlde str(nan)=='nan' PIT üyeliğine uydurma 'NAN' sembolü sokuyordu), yoksa kırpılmış str."""
            return "" if v is None or (isinstance(v, float) and pd.isna(v)) else str(v).strip()
        rows = []
        for _, row in ch.iterrows():
            d, a, rm = _cell(row.get(dcol)), _cell(row.get(acol)), _cell(row.get(rcol))
            if not (d or a or rm):
                continue  # TSK-154: hayalet boş satır (üç alan da "") — asla yazılmaz
            rows.append({"date": d, "added": a, "removed": rm})
        changes, changes_kaynak = rows, "wikipedia_selected_changes"
    except Exception as e:
        changes, changes_kaynak = [], None
        try:
            from .. import obs
            obs.warn("sp500_degisiklik_tablosu_yok", url=WIKI_URL,
                     tablo_n=len(tables) if isinstance(tables, list) else 0,
                     neden=f"{type(e).__name__}: {e}"[:200])
        except Exception:  # sessiz-yutma: kayıt kanalının kendisi düştü — ikinci bir kanal yok; kayıt denemesi çağıranı düşüremez
            pass
    return cur, changes, changes_kaynak


def current(use_cache: bool = True) -> list[str]:
    """Güncel S&P 500 sembolleri. Zincir: FMP (anahtarlı, zaten kullanımda) → Wikipedia (en iyi çaba).
    Günlük önbellek; hiçbir kaynak MAKUL liste veremezse [] — çağıran elle bakımlı evrene düşer.

    ÖNEMLİ: eskiden başarısızlıkta 'dünün listesi'ni döndürüyordu; o liste sahte olduğunda (canlıda
    öyleydi) sahtelik sonsuza kadar servis ediliyordu. Artık önbellek de makullük kapısından geçer."""
    today = dt.date.today().isoformat()
    cached = _cached()
    if use_cache and cached.get("as_of") == today and cached.get("current"):
        _note(True, "cache", len(cached["current"]))
        return cached["current"]

    from . import fmp
    if fmp.available() and not fmp.quota_blocked():
        syms = [str(s).strip().upper().replace(".", "-") for s in (fmp.sp500_constituents() or [])]
        if _plausible(syms):
            store.write_json(CACHE, {"as_of": today, "current": syms,
                                     "changes": cached.get("changes", []),
                                     "changes_kaynak": cached.get("changes_kaynak"),
                                     "source": "fmp"})
            _note(True, "fmp", len(syms))
            return syms
        _note(False, "fmp", len(syms), "makul olmayan/boş liste (kota?)")

    cur, changes, changes_kaynak = _fetch_tables()
    if _plausible(cur):
        store.write_json(CACHE, {"as_of": today, "current": cur, "changes": changes,
                                 "changes_kaynak": changes_kaynak, "source": "wikipedia"})
        _note(True, "wikipedia", len(cur))
        return cur
    if not _HEALTH.get("error"):
        _note(False, None, 0, "hiçbir kaynak makul üyelik listesi vermedi")
    return cached.get("current", []) if _plausible(cached.get("current")) else []


def _iso(d) -> str | None:
    """Normalize a change-log date to ISO YYYY-MM-DD. Wikipedia's column is human-readable ('October 1,
    2024'); the old code sliced [:10] and compared LEXICALLY, so every letter-leading date read as
    'after any query date' and the PIT reconstruction INVERTED. None if unparseable."""
    s = str(d or "").strip()
    if not s:
        return None
    import datetime as dt
    try:
        return dt.date.fromisoformat(s[:10]).isoformat()
    except ValueError:  # sessiz-yutma: biçimsiz/eksik tek alan; yalnız bu değer düşer, satır başına uyarı asıl sinyali log seline gömerdi
        try:
            import pandas as pd
            ts = pd.to_datetime(s, errors="coerce")
            return None if ts is None or ts is pd.NaT else str(ts.date())
        except Exception:  # sessiz-yutma: pandas ile İKİNCİ deneme de tarihi çözemedi; alan None kalır ve çağıran None'ı zaten 'tarih yok' diye ele alıyor
            return None


def _tick(v) -> str:
    """Ticker cell → clean symbol; '' for NaN-ish junk. The fetch path sanitizes, but PERSISTED caches
    written before that fix still carry literal 'nan' strings that fabricated a phantom 'NAN' instrument
    in PIT membership (live on disk)."""
    s = str(v or "").strip().upper()
    return "" if s in ("", "NAN", "NONE", "N/A", "-", "—") else s


def as_of(date: str) -> list[str]:
    """Reconstruct membership on `date` by walking the change-log back from the current list. Best-effort
    (Wikipedia's change table only spans recent years); [] if unavailable. Honest scaffold for PIT.

    [] dönmesi 'o tarihte kimse yoktu' DEĞİL 'BİLMİYORUZ' demektir — çağıran bunu üyelik gibi
    kullanmamalı (denetim turu 3: sessiz boş liste, survivorship'i 'düzeltildi' sanmaya yol açar)."""
    data = _cached()
    members = set(data.get("current", []))
    if not members:
        members = set(current())
        data = _cached()                     # current() just wrote the cache — re-read so the change-log
        if not members:                      # is actually applied instead of iterating the stale pre-fetch
            return []                        # snapshot (cold cache returned CURRENT membership
                                             # for any historical date — survivorship bias)
    for ch in data.get("changes", []):
        d = _iso(ch.get("date"))
        if d and d > date:                                # undo changes that happened AFTER `date`
            add, rem = _tick(ch.get("added")), _tick(ch.get("removed"))
            if add:
                members.discard(add)                      # it was added after `date` → not a member then
            if rem:
                members.add(rem)                          # it was removed after `date` → was a member then
    return sorted(m for m in members if _tick(m))


def as_of_pit_durumu(date: str) -> dict:
    """BEYAN (TSK-154, D2): `as_of(date)`in dönüşü GERÇEK tarihsel yeniden kurulum mu, yoksa
    değişiklik günlüğü boş/kapsam-dışı olduğu için bugünkü listeye eşit survivorship mi? `as_of()`
    kendisi bunu TAŞIMAZ — dönüş biçimi (`list[str]`) DEĞİŞMEDİ, çünkü üretim çağıranı bugün yok
    (modül başlığı (e); iki kalıcı test `as_of()`u düz liste olarak okuyor). Okuyucu eklenirse
    (`universe_drift`/`loop`/`pitlaw`) bu fonksiyon gerçek karara bağlanır; o güne kadar
    `pitlaw.PIT_SOZLESMELI_BESLEYENI_KAPALI` sınıfı AYNEN kalır — bu fonksiyonun var oluşu o
    sınıflandırmayı değiştirmez, yalnız beyanı koda taşır.

    Döner: {"pit": bool, "neden": str|None, "changes_kaynak": str|None}. `changes_kaynak` cache
    dosyasından AYNEN okunur (D1'de yazılan alan — `_fetch_tables` tablo bulamazsa None yazar; bu
    fonksiyon o alanın OKUYUCUSUdur). `pit=False` iki durumda: (a) önbellekte `changes` yok/boş
    (tablo kaldırılmış — TSK-154 kök neden); (b) günlük var ama `date`ten SONRAKİ geçerli (tarih
    ayrıştırılabilir VE eklenen/çıkan dolu) hiçbir satır yok — geriye doğru hiçbir değişiklik
    uygulanmaz, yine survivorship. `pit=True` yalnız `date`ten sonraki en az bir geçerli satır
    varsa, yani `as_of()` gerçekten bir üyeyi ekleyip/çıkarmıştır."""
    data = _cached()
    changes = data.get("changes") or []
    changes_kaynak = data.get("changes_kaynak")
    if not changes:
        return {"pit": False, "neden": "değişiklik tablosu yok — as_of bugünkü listeye eşit",
                "changes_kaynak": changes_kaynak}
    for ch in changes:
        d = _iso(ch.get("date"))
        if d and d > date and (_tick(ch.get("added")) or _tick(ch.get("removed"))):
            return {"pit": True, "neden": None, "changes_kaynak": changes_kaynak}
    return {"pit": False,
            "neden": "değişiklik günlüğü `date` kapsamının dışında — as_of bugünkü listeye eşit",
            "changes_kaynak": changes_kaynak}


def universe_drift() -> dict:
    """GERÇEK TÜKETİCİ (denetim turu 3): elle bakımlı REPLAY_UNIVERSE ile güncel endeks üyeliğini
    karşılaştır. 2026-07-21'de 7 ölü sembol (DFS, FI, HES, IPG, PARA, K, WBA) ELLE bulunmuştu —
    tam da bu modülün söylemesi gereken şey. Kaynak yoksa 'unknown' döner: 'sapma yok' DEMEZ.

    `stale` SEMANTİĞİ TSK-143'te (2026-09-05) DEĞİŞTİ: eskiden "REPLAY_UNIVERSE'de olup güncel
    S&P 500'de olmayan" idi ve bu, EVREN_DISI_BEYANLI'daki 10 sembolü (hiç üye olmadı/S&P 400/
    yabancı/geçmiş çıkış — bkz. data.py şerhi) her gün "sapma" diye işaretleyip 24 gündür aynı
    yanlış-pozitif DATA_QUALITY alarmını üretiyordu. Artık `stale` = REPLAY_UNIVERSE ∖ (güncel S&P
    500 ∪ EVREN_DISI_BEYANLI ∪ RETIRED_SYMBOLS) — yani BEYANSIZ sapma. Beyanlı sapma ayrı alanda
    (`beyanli_disi`) GÖRÜNÜR kalır, sessizce yutulmaz.

    BEDEL BEYANI (Yasa 6 / bedel yasası): `beyanli_disi`deki 10 sembolden biri gelecekte GERÇEKTEN
    delist olursa bu fonksiyon onu `stale`de GÖSTERMEZ — beyanlı olmak bu alarmı kalıcı olarak
    susturur. Bu kör nokta bilerek kabul edildi (aksi hâlde alarm eskisi gibi her gün geri gelir);
    delist tespiti `data._record_no_data`e (TSK-153, bu turun kapsamı DIŞINDA) devredildi. O
    gelene kadar EVREN_DISI_BEYANLI'nin doğruluğu yalnız ELLE (bu defterin bakımıyla) korunur."""
    from . import data as _data
    REPLAY_UNIVERSE = _data.REPLAY_UNIVERSE
    # İKİNCİ, BAĞIMSIZ KANIT: üyelik kaynağı bu kurulumda ÇALIŞMIYOR (Wikipedia 403,
    # FMP kotası) ve rapor haklı olarak "unknown" diyor — ama o zaman ölü sembol sorusu CEVAPSIZ
    # kalıyordu. Bar hattının verisiz-sembol defteri tam bu soruyu başka bir yerden cevaplıyor:
    # "her kaynak DÜZGÜN cevap verip sıfır satır döndü" hükmünün ARDIŞIK tekrarı. Üyelik listesi
    # olmasa da bu kanıt taşınır; olay defterinde üretilip tüketilmeyen bir sayaç bırakmıyoruz.
    _nd = store.read_json(_data.NO_DATA_FILE, {}) or {}
    no_data = sorted(t for t, v in _nd.items()
                     if int((v or {}).get("streak") or 0) >= _data.NO_DATA_CONFIRM_STREAK)
    # ÜÇÜNCÜ KANIT — EMEKLİLİK DEFTERİ VE ONUN BEKÇİSİ. ELLE bulunan
    # ölü isimler artık `data.RETIRED_SYMBOLS`ta hükümle yazılı ve evrenden çıkarılmış. Rapor iki
    # şeyi söyler: kaç isme emeklilik hükmü verildiği (bakımın YAPILDIĞININ kanıtı), ve o isimlerden
    # herhangi biri evrene GERİ girmiş mi. `retired_in_universe` normalde BOŞTUR; boş değilse biri
    # (elle düzenleme, birleşme sonrası kopyala-yapıştır) delist olmuş bir sembolü tarama evrenine
    # geri koymuş demektir — sessiz kalırsa motor günlerce ölü bir isim hakkında karar üretirdi.
    retired_in_universe = sorted(t for t in REPLAY_UNIVERSE if _data.is_retired(t))
    # DÖRDÜNCÜ KANIT — EVREN-DIŞI BEYAN BEKÇİSİ (TSK-116, 2026-09-03; TSK-143, 2026-09-05 revizyonu
    # — ad ve sayı değişti: INDEX_EXITED→EVREN_DISI_BEYANLI, 13→10, üçü RETIRED_SYMBOLS'a taşındı).
    # `retired_in_universe`nin kardeşi ama FARKLI evrende ölçülür: 10 beyanlı sembol BİLEREK
    # REPLAY_UNIVERSE'de KALIR (sağkalan yanlılığı artırmamak için — bkz. data.py EVREN_DISI_BEYANLI
    # şerhi), o yüzden onu REPLAY_UNIVERSE'e karşı ölçmek HER ZAMAN doğru-pozitif üretirdi. Bekçi
    # LIVE_UNIVERSE'e karşı ölçer: LIVE_UNIVERSE'in KENDİ TANIMI bu 10'u zaten süzdüğü için normalde
    # BOŞ döner; boş DEĞİLSE biri LIVE_UNIVERSE türetmesini (elle düzenleme, monkeypatch) bozmuş
    # demektir. Alan adları (`index_exited_n`/`index_exited_in_live`) KORUNDU — okuyucular (pano,
    # testler) değişmedi; `data.INDEX_EXITED` artık `EVREN_DISI_BEYANLI`nin AYNI nesnesi (tek kaynak).
    index_exited_in_live = sorted(t for t in _data.LIVE_UNIVERSE if _data.is_index_exited(t))
    # BEŞİNCİ KANIT — BEYANLI SAPMA, AYRI ALANDA GÖRÜNÜR (TSK-143, K3). REPLAY_UNIVERSE içindeki 10
    # EVREN_DISI_BEYANLI sembolü `stale`den SESSİZCE çıkarmak yetmez — nereye gittiklerini görmek
    # (Yasa 6) için ayrı taşınırlar. Üyelik kaynağı olmasa da (aşağıdaki 'unknown' dalı) bu liste
    # REPLAY_UNIVERSE'e karşı statik ölçülür, üyelik gerektirmez.
    beyanli_disi = sorted(t for t in REPLAY_UNIVERSE if _data.is_index_exited(t))
    members = current()
    if not _plausible(members):
        return {"status": "unknown", "reason": _HEALTH.get("error") or "üyelik kaynağı yok",
                "universe": len(REPLAY_UNIVERSE), "stale": [], "n_stale": 0,
                "beyanli_disi": beyanli_disi, "n_beyanli_disi": len(beyanli_disi),
                "no_data": no_data, "n_no_data": len(no_data),
                "retired_n": len(_data.RETIRED_SYMBOLS), "retired_in_universe": retired_in_universe,
                "index_exited_n": len(_data.INDEX_EXITED), "index_exited_in_live": index_exited_in_live}
    mset = {m.upper() for m in members}
    # BEYANSIZ sapma: güncel S&P 500'de YOK ve EVREN_DISI_BEYANLI/RETIRED'da da beyan edilmemiş.
    # RETIRED_SYMBOLS yapısal olarak REPLAY_UNIVERSE'de bulunmaz (yukarıdaki kesişmezlik hükmü),
    # ama formül tek-kaynak yasasına uysun diye üç kümenin BİRLEŞİMİ açıkça yazılır.
    _beyanli_ve_emekli = set(_data.EVREN_DISI_BEYANLI) | set(_data.RETIRED_SYMBOLS)
    stale = sorted(t for t in REPLAY_UNIVERSE
                   if t.upper() not in mset and t.upper() not in _beyanli_ve_emekli)
    return {"status": "ok", "source": _HEALTH.get("source"), "universe": len(REPLAY_UNIVERSE),
            "members": len(mset), "stale": stale, "n_stale": len(stale),
            "beyanli_disi": beyanli_disi, "n_beyanli_disi": len(beyanli_disi),
            "no_data": no_data, "n_no_data": len(no_data),
            "retired_n": len(_data.RETIRED_SYMBOLS), "retired_in_universe": retired_in_universe,
            "index_exited_n": len(_data.INDEX_EXITED), "index_exited_in_live": index_exited_in_live}
