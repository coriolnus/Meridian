"""adapters/constituents.py — point-in-time S&P 500 üyeliği: FMP birincil, Wikipedia en iyi-çaba
ikincil; makullük kapılı önbellek ve evren-sapma raporu.

(a) Ne yapar: güncel S&P 500 üyelik listesini kaynak zincirinden kurar (FMP sp500-constituent —
anahtarlı ve zaten kullanımda olduğu için BİRİNCİL; Wikipedia List_of_S%26P_500_companies sayfası
en iyi-çaba İKİNCİL) ve değişiklik günlüğünü geriye sararak `as_of(date)` ile tarihsel üyeliği
yeniden kurar. Gerçek üretim tüketicisi `universe_drift()`tir: elle bakımlı REPLAY_UNIVERSE'ü
güncel üyelik + verisiz-sembol defteri + emeklilik defteriyle karşılaştırıp ölü/geri-sızmış
isimleri söyler. ESKİ NOT BAYATTI, ÖLÇÜMLE DÜZELTİLDİ (TSK-156, 2026-09-05, EDG-2026-075/076):
"Wikipedia yolu bu kurulumda fiilen kapalıdır" iddiası A1'den (canlı sunucu) httpx ile bu
User-Agent'a HER İKİ sayfaya (üyelik + tarihsel değişiklik) 200 döndüğü ölçülünce yanlışlandı;
yalnız BU geliştirme makinesinden (istemci parmak izi farkı) 403 alınabiliyor. health() nedeni
yine de ADIYLA yazılır — kaynak/UA/ağ tekrar bozulursa bu not bir daha sessizce bayatlamaz.
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
iki PIT testi + gerçek tüketici yok), pitlaw sınıfı `PIT_SOZLESMELI_BESLEYENI_KAPALI` AYNEN kalır.
(f) TSK-156 dilim-1 (2026-09-05, kart EDG-2026-075/076,
research/olcumler/edg075_sp500_tarihsel/sonuc_edg076_2026-09-05.json): `changes`in BİRİNCİL
kaynağı artık AYRI bir sayfa, `HIST_URL` ("Historical_components_of_the_S%26P_500") —
`_fetch_hist_changes()` bu sayfadaki değişiklik tablosunu İNDEKSTEN değil SÜTUNLARDAN
(`Effective Date`/`Added Ticker`/`Removed Ticker`) seçer. Ölçüm: 407 satır, 2020→bugün 136
değişiklik, 0 hayalet, 0 tarih hatası, 28/28 S&P DJI bülten olgusu tarih+yön doğru; as_of yeniden
kurulumu güncel listeyle fark 0. Her çekim `oldid`/`sha256`/`n_satir`/`n_tarih_yok`/`cekim_ts`
damgası taşır (modül-düzeyi `_SON_HIST_META`, önbelleğe `changes_meta` olarak yazılır —
`as_of_pit_durumu` bunu AYNEN okur, alanların okuyucusu odur). Bu sayfa başarısızsa (403/
ayrıştırma hatası) eski `tables[1]` yolu (TSK-154) AYNEN çalışmaya devam eder
(`changes_kaynak="wikipedia_selected_changes"`); ikisi de boşsa FMP/Wikipedia dalları
önbellekteki `changes`i KORUR, boşla EZMEZ.
TEK KAYNAK SINIRI (aynı kart, ölçüldü): bu tablo ÜYELİK olaylarını (ekleme/çıkarma) taşır, saf
ticker yeniden-adlandırmasını (şirket S&P 500'de KALIRKEN sembol değiştirmesi) satır olarak
TAŞIMAZ — o olay yalnız BAŞKA bir satırın `reason` metninde iz bırakır (EQR→VMRK 2026-08-18:
AvalonBay'in kaldırılma satırının reason'ı "now Vivmark Residential" der; EQR/VMRK'nin KENDİ
satırı yoktur). `as_of()` bu yüzden AYRICA modül-düzeyi donuk `SEMBOL_YENIDEN_ADLANDIRMA`
defterini geriye uygular (`tarih > date` ise `yeni`→`eski`). Defter ELLE bakımlıdır: kod şirket
adından ticker UYDURMAZ — `rename_adaylari()` `reason`de "(now X)" kalıbı taşıyan ama kayıtlı
`tarih`iyle eşleşmeyen bir aday bulursa `obs.warn("sp500_rename_adayi", ...)` yazar, kayıt
operatör tarafından ELLE açılır.
PIT SINIFI DOKUNULMADI: `("constituents", "as_of")` bu turda da `PIT_SOZLESMELI_BESLEYENI_KAPALI`
sınıfında KALDI. `pitlaw.sinif_turet` yalnız `PIT_DISI_KAYNAKLAR` kaydını ve YALNIZ karar/tarihsel
modüllerdeki GERÇEK çağrı yerlerini kaynaktan tarar; `as_of`in üretimde HİÇBİR çağıranı yok (bu
paragrafın (e) bendi hâlâ doğru), yani türetim mekanik olarak `None` (ölçülemedi) döner — beyaz
listeye taşımayı DOĞRULAYACAK bir mekanik onay bu turda YOK, taşıma yapılmadı (rapor: Rol-1)."""
from __future__ import annotations
import datetime as dt

from .. import store

WIKI_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
#: TSK-156 (2026-09-05): AYRI bir sayfa — üyelik listesi DEĞİL, değişiklik (`changes`) günlüğünün
#: BİRİNCİL kaynağı. Bkz. modül başlığı (f).
HIST_URL = "https://en.wikipedia.org/wiki/Historical_components_of_the_S%26P_500"
CACHE = "sp500_constituents.json"
MIN_MEMBERS = 400          # S&P 500 ~503 isim; bunun altı "üyelik listesi" DEĞİLDİR (fixture/kırpık)
_HEALTH = {"ok": None, "source": None, "n": 0, "at": None, "error": ""}
#: SON `_fetch_hist_changes()` DENEMESİNİN META'SI (oldid/sha256/n_satir/n_tarih_yok/cekim_ts) —
#: `_HEALTH` ile AYNI desen. `_fetch_tables`in kendi imzası (üç değer) bu alanı TAŞIMAZ; `current()`
#: bu modül-düzeyi değişkenden okuyup önbelleğe `changes_meta` olarak yazar (modül başlığı (f)).
_SON_HIST_META: dict | None = None

# SEMBOL YENİDEN ADLANDIRMA DEFTERİ — TEK KAYNAK SINIRININ ELLE bakımlı düzeltmesi (TSK-156,
# 2026-09-05, kart EDG-2026-075/076). `HIST_URL` tablosu ÜYELİK olaylarını taşır, saf ticker
# yeniden-adlandırmasını (şirket S&P 500'de KALIRKEN sembol değiştirmesi) satır olarak TAŞIMAZ.
# ÖLÇÜLEN TEK VAKA: Equity Residential 2026-08-18'de Vivmark Residential'a yeniden adlandı (ticker
# EQR→VMRK) ve S&P 500 ÜYELİĞİ HİÇ KESİLMEDİ — tablo bu olayı bir satır olarak YAZMAZ; olay yalnız
# AvalonBay'in (AVB) kaldırılma satırının `reason` metninde "(now Vivmark Residential)" olarak
# görünür. Kod şirket adından ticker UYDURMAZ (`rename_adaylari()`), bu defter ELLE açılır.
# `as_of(date)` her kayıt için `tarih > date` ise `yeni`yi çıkarıp `eski`yi ekler (o tarihte GEÇERLİ
# ticker) — `list[str]` dönüş biçimi DEĞİŞMEZ.
SEMBOL_YENIDEN_ADLANDIRMA: tuple[dict, ...] = (
    {"eski": "EQR", "yeni": "VMRK", "tarih": "2026-08-18",
     "kaynak": "SEC 8-K Vivmark Residential 2026-08-18; S&P DJI 2026-08-13 "
               "'will remain in the S&P 500'"},
)


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


def _duz_sutunlar(cols) -> list[str]:
    """Pandas MultiIndex/Index sütunlarını tek dizgeye düzleştirir: tuple ise `"_".join`, değilse
    `str`. TEK KAYNAK YASASI: hem TSK-154'ün eski `tables[1]` yolu hem TSK-156'nın yeni
    `_fetch_hist_changes` tablo seçimi AYNI düzleştirmeyi kullanır — iki kopya sessizce ayrışmasın."""
    return ["_".join(str(x) for x in c) if isinstance(c, tuple) else str(c) for c in cols]


def _cell(v) -> str:
    """Wikipedia değişiklik-günlüğü hücresini NaN-güvenli dizgeye çevirir: None/NaN → "" (aksi
    hâlde `str(nan)=='nan'` PIT üyeliğine uydurma 'NAN' sembolü sokuyordu), yoksa kırpılmış str.
    MODÜL DÜZEYİNE TAŞINDI (TSK-156): eskiden yalnız `_fetch_tables` içinde nested tanımlıydı;
    `_fetch_hist_changes` da AYNI okuyucuyu ister — iki kopya tek-kaynak yasasını çiğnerdi."""
    if v is None:
        return ""
    if isinstance(v, float):
        import pandas as pd
        if pd.isna(v):
            return ""
    return str(v).strip()


def rename_adaylari(changes: list[dict]) -> list[dict]:
    """`changes` satırlarının `reason` alanında "(now X)" kalıbı taşıyanlar — MUHTEMEL ticker/şirket
    adı yeniden-adlandırma olayları (`{"date", "added", "removed", "reason_ad"}`).

    KOD KENDİ KENDİNE `SEMBOL_YENIDEN_ADLANDIRMA`YA EKLEMEZ: şirket adı ("Vivmark Residential")
    TICKER DEĞİLDİR — "VMRK" metinden UYDURULAMAZ (uydurma yasağı). Bu yalnız OPERATÖRE gösterilecek
    aday listesidir; `_fetch_hist_changes` bunu sayar ve kayıtlı deftere GÖRE eşleşmeyen bir aday
    varsa `obs.warn("sp500_rename_adayi", ...)` yazar."""
    import re
    desen = re.compile(r"\(now ([^)]+)\)")
    out: list[dict] = []
    for ch in changes:
        m = desen.search(ch.get("reason") or "")
        if m:
            out.append({"date": ch.get("date"), "added": ch.get("added"),
                       "removed": ch.get("removed"), "reason_ad": m.group(1).strip()})
    return out


def _fetch_hist_changes() -> tuple[list[dict], dict | None]:
    """`(satırlar, meta)` — `HIST_URL` ("Historical components of the S&P 500") sayfasından
    `changes`in BİRİNCİL kaynağı (TSK-156, 2026-09-05, kart EDG-2026-075/076). Modül başlığı (f).

    Tablo İNDEKSTEN değil SÜTUNLARDAN seçilir (`Effective Date` + `Added`∧`Ticker` +
    `Removed`∧`Ticker` içeren İLK tablo) — sayfa düzeni değişirse sabit bir indeks sessizce YANLIŞ
    tabloyu seçerdi (TSK-154'ün kök nedeniyle AYNI sınıf risk). Başarısızlık (HTTP≥400, hiç tablo
    yok, eşleşen sütun yok, herhangi bir istisna) → `([], None)` + `obs.warn(
    "sp500_tarihsel_tablo_yok", url=HIST_URL, neden=...)` (Yasa 4 — sessiz değil).

    Üç alanı (`date`/`added`/`removed`) da boş satır (hayalet) hiçbir zaman yazılmaz; `_iso` ile
    ayrıştırılamayan tarihli satır da yazılmaz ama `meta["n_tarih_yok"]`de SAYILIR (uydurma yasağı:
    "yoktu" ile "ayrıştıramadım" karışmasın). `reason` `rename_adaylari()`e geçirilir — kayıtlı
    `SEMBOL_YENIDEN_ADLANDIRMA` tarihiyle eşleşmeyen bir aday varsa TEK
    `obs.warn("sp500_rename_adayi", ...)` yazılır (operatör defteri elle genişler).

    Meta modül-düzeyi `_SON_HIST_META`ya yazılır (yan etki) — `_fetch_tables`in kendisi ÜÇLÜ
    imzasını korur, `current()` meta'yı bu değişkenden okur."""
    global _SON_HIST_META
    try:
        import hashlib
        import io
        import re as _re
        import pandas as pd
        import httpx
        r = httpx.get(HIST_URL, timeout=20, headers={"User-Agent": "Meridian/1.0"},
                      follow_redirects=True)
        if r.status_code >= 400:
            raise ValueError(f"HTTP {r.status_code}")
        text = r.text
        tables = pd.read_html(io.StringIO(text), flavor="lxml")
        secili = None
        for t in tables:
            cols = _duz_sutunlar(t.columns)
            if (any("Effective Date" in c for c in cols)
                    and any("Added" in c and "Ticker" in c for c in cols)
                    and any("Removed" in c and "Ticker" in c for c in cols)):
                secili = t.copy()
                secili.columns = cols
                break
        if secili is None:
            raise ValueError(f"tarihsel değişiklik tablosu sütunları eşleşmedi (tablo n={len(tables)})")
        dcol = next(c for c in secili.columns if "Effective Date" in c)
        acol = next(c for c in secili.columns if "Added" in c and "Ticker" in c)
        rcol = next(c for c in secili.columns if "Removed" in c and "Ticker" in c)
        rcol_reason = next((c for c in secili.columns if "Reason" in c), None)
        rows: list[dict] = []
        n_tarih_yok = 0
        for _, satir in secili.iterrows():
            d_raw = _cell(satir.get(dcol))
            a_raw = _cell(satir.get(acol))
            rm_raw = _cell(satir.get(rcol))
            reason_raw = _cell(satir.get(rcol_reason)) if rcol_reason else ""
            if not (d_raw or a_raw or rm_raw):
                continue                            # hayalet satır: hiçbir zaman yazılmaz
            iso = _iso(d_raw)
            if iso is None:
                n_tarih_yok += 1
                continue                            # tarih ayrışmadı: yazılmaz ama SAYILIR
            rows.append({"date": iso, "added": _tick(a_raw), "removed": _tick(rm_raw),
                        "reason": reason_raw})
        adaylar = rename_adaylari(rows)
        if adaylar:
            kayitli_tarihler = {rn["tarih"] for rn in SEMBOL_YENIDEN_ADLANDIRMA}
            eslesmeyen = [a for a in adaylar if a["date"] not in kayitli_tarihler]
            if eslesmeyen:
                en_yeni = sorted(eslesmeyen, key=lambda a: a["date"] or "", reverse=True)[:3]
                try:
                    from .. import obs
                    obs.warn("sp500_rename_adayi", n=len(eslesmeyen), ornek=en_yeni)
                except Exception:  # sessiz-yutma: kayıt kanalının kendisi düştü — ikinci bir kanal yok; kayıt denemesi çağıranı düşüremez
                    pass
        m = _re.search(r'"wgRevisionId":(\d+)', text)
        meta = {"oldid": int(m.group(1)) if m else None,
                "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "n_satir": len(rows), "n_tarih_yok": n_tarih_yok,
                "cekim_ts": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}
        _SON_HIST_META = meta
        return rows, meta
    except Exception as e:
        _SON_HIST_META = None
        try:
            from .. import obs
            obs.warn("sp500_tarihsel_tablo_yok", url=HIST_URL,
                     neden=f"{type(e).__name__}: {e}"[:200])
        except Exception:  # sessiz-yutma: kayıt kanalının kendisi düştü — ikinci bir kanal yok; kayıt denemesi çağıranı düşüremez
            pass
        return [], None


def _fetch_tables():
    """(current_symbols, changes, changes_kaynak) — Wikipedia'dan. Başarısızlıkta (None, None, None)
    AMA sebebi kaydederek. NOT: Wikipedia botlara 403 dönebilir ve ayrıştırıcı eksikliği de olabilir;
    ikisi de `health()`te AYRI nedenlerle görünür.

    TSK-154 (2026-09-05): `tables[1]` eskiden 'Selected changes' değişiklik günlüğüydü; sayfa bu
    tabloyu KALDIRDI (bugün section 1 tek tablo taşıyor, section 2 'See also'). Eski kod sütun
    eşleşmesi olmasa da BOŞ satırlar üretip yazıyordu (`{date:'',added:'',removed:''}` × 11, canlı
    önbellekte bulundu) — hiç uyarı yok. Artık: (a) sütunlardan biri (tarih/eklenen/çıkan) hiç
    eşleşmezse tablo 'değişiklik günlüğü DEĞİL' sayılır → `changes=[]`, `changes_kaynak=None`,
    `obs.warn` (Yasa 4); (b) üç alanı da boş olan satır (hayalet) hiç `changes`e yazılmaz.

    TSK-156 (2026-09-05): `changes` artık ÖNCE `_fetch_hist_changes()`ten (AYRI sayfa, `HIST_URL`)
    denenir; doluysa `changes_kaynak="wikipedia_historical_components"` ve YUKARIDAKİ eski
    `tables[1]` yolu HİÇ ÇALIŞTIRILMAZ. `_fetch_hist_changes` boş dönerse (403/ayrıştırma hatası)
    eski yol AYNEN devam eder — üçlü imza (`cur, changes, changes_kaynak`) DEĞİŞMEDİ."""
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

    hist_rows, _hist_meta = _fetch_hist_changes()
    if hist_rows:
        return cur, hist_rows, "wikipedia_historical_components"

    changes, changes_kaynak = [], None
    try:
        ch = tables[1]
        ch.columns = _duz_sutunlar(ch.columns)
        dcol = next((c for c in ch.columns if "Date" in c), None)
        acol = next((c for c in ch.columns if "Added" in c and "Ticker" in c), None)
        rcol = next((c for c in ch.columns if "Removed" in c and "Ticker" in c), None)
        if dcol is None or acol is None or rcol is None:
            # TSK-154: tablo VAR ama değişiklik günlüğü SÜTUNLARI yok — Wikipedia'nın
            # kaldırdığı 'Selected changes' tablosu değil, başka bir tablo (`tables[1]` artık
            # 'See also' ya da benzeri). Sessizce boş `changes` yazmak yerine adıyla uyarılır.
            raise ValueError(f"değişiklik günlüğü sütunları eşleşmedi: {list(ch.columns)[:6]}")
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
    öyleydi) sahtelik sonsuza kadar servis ediliyordu. Artık önbellek de makullük kapısından geçer.

    TSK-156 (2026-09-05): FMP dalında `cur` FMP'den gelse bile `changes` AYRICA `HIST_URL`den
    tazelenir (FMP hiç değişiklik günlüğü ÜRETMEZ) — hist başarısızsa önbellekteki
    `changes`/`changes_kaynak`/`changes_meta` KORUNUR, boşla EZİLMEZ (eski davranışla AYNI:
    FMP dalı zaten hep önbellekten devralıyordu, tek fark artık ÖNCE tazeleme DENENİYOR)."""
    today = dt.date.today().isoformat()
    cached = _cached()
    if use_cache and cached.get("as_of") == today and cached.get("current"):
        _note(True, "cache", len(cached["current"]))
        return cached["current"]

    from . import fmp
    if fmp.available() and not fmp.quota_blocked():
        syms = [str(s).strip().upper().replace(".", "-") for s in (fmp.sp500_constituents() or [])]
        if _plausible(syms):
            hist_rows, hist_meta = _fetch_hist_changes()
            if hist_rows:
                changes, changes_kaynak, changes_meta = (hist_rows,
                                                          "wikipedia_historical_components",
                                                          hist_meta)
            else:
                changes = cached.get("changes", [])
                changes_kaynak = cached.get("changes_kaynak")
                changes_meta = cached.get("changes_meta")
            store.write_json(CACHE, {"as_of": today, "current": syms,
                                     "changes": changes,
                                     "changes_kaynak": changes_kaynak,
                                     "changes_meta": changes_meta,
                                     "source": "fmp"})
            _note(True, "fmp", len(syms))
            return syms
        _note(False, "fmp", len(syms), "makul olmayan/boş liste (kota?)")

    cur, changes, changes_kaynak = _fetch_tables()
    if _plausible(cur):
        store.write_json(CACHE, {"as_of": today, "current": cur, "changes": changes,
                                 "changes_kaynak": changes_kaynak, "changes_meta": _SON_HIST_META,
                                 "source": "wikipedia"})
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
    kullanmamalı (denetim turu 3: sessiz boş liste, survivorship'i 'düzeltildi' sanmaya yol açar).

    TSK-156 (2026-09-05): değişiklik günlüğü geri-sarıldıktan SONRA modül-düzeyi donuk
    `SEMBOL_YENIDEN_ADLANDIRMA` defteri AYRICA uygulanır — `changes` tablosu saf ticker
    yeniden-adlandırmasını (şirket üyelikte KALIRKEN sembol değiştirmesi) satır olarak TAŞIMAZ
    (tek kaynak sınırı, modül başlığı (f))."""
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
    for rn in SEMBOL_YENIDEN_ADLANDIRMA:
        # rename `tarih`inden SONRAKİ bir `date` sorgusu için `yeni` doğru — geri alınmaz.
        # `tarih`ten ÖNCEKİ bir sorgu için o tarihte GEÇERLİ olan `eski` ile değiştirilir.
        if rn["tarih"] > date and rn["yeni"] in members:
            members.discard(rn["yeni"])
            members.add(rn["eski"])
    return sorted(m for m in members if _tick(m))


def as_of_pit_durumu(date: str) -> dict:
    """BEYAN (TSK-154, D2): `as_of(date)`in dönüşü GERÇEK tarihsel yeniden kurulum mu, yoksa
    değişiklik günlüğü boş/kapsam-dışı olduğu için bugünkü listeye eşit survivorship mi? `as_of()`
    kendisi bunu TAŞIMAZ — dönüş biçimi (`list[str]`) DEĞİŞMEDİ, çünkü üretim çağıranı bugün yok
    (modül başlığı (e); iki kalıcı test `as_of()`u düz liste olarak okuyor). Okuyucu eklenirse
    (`universe_drift`/`loop`/`pitlaw`) bu fonksiyon gerçek karara bağlanır; o güne kadar
    `pitlaw.PIT_SOZLESMELI_BESLEYENI_KAPALI` sınıfı AYNEN kalır — bu fonksiyonun var oluşu o
    sınıflandırmayı değiştirmez, yalnız beyanı koda taşır.

    Döner: {"pit": bool, "neden": str|None, "changes_kaynak": str|None, "kaynak_sinifi": str|None,
    "changes_meta": dict|None}. `changes_kaynak` cache dosyasından AYNEN okunur (D1'de yazılan alan
    — `_fetch_tables` tablo bulamazsa None yazar; bu fonksiyon o alanın OKUYUCUSUdur). `pit=False`
    iki durumda: (a) önbellekte `changes` yok/boş (tablo kaldırılmış — TSK-154 kök neden); (b)
    günlük var ama `date`ten SONRAKİ geçerli (tarih ayrıştırılabilir VE eklenen/çıkan dolu) hiçbir
    satır yok — geriye doğru hiçbir değişiklik uygulanmaz, yine survivorship. `pit=True` yalnız
    `date`ten sonraki en az bir geçerli satır varsa, yani `as_of()` gerçekten bir üyeyi
    ekleyip/çıkarmıştır.

    TSK-156 (2026-09-05) İKİ YENİ ALAN: `kaynak_sinifi` — `changes_kaynak` DEĞERİNDEN türetilen
    okunabilir etiket (`"tarihsel_tablo"` ↔ `HIST_URL`, `"secilmis_degisiklikler"` ↔ eski TSK-154
    `tables[1]` yolu, `None` kaynak yoksa) — iki KAYNAK KALİTESİ birbirine karışmasın diye. VE
    `changes_meta` — cache'teki `changes_meta` alanı AYNEN (bu fonksiyon o alanın OKUYUCUSUdur,
    modül başlığı (f))."""
    data = _cached()
    changes = data.get("changes") or []
    changes_kaynak = data.get("changes_kaynak")
    kaynak_sinifi = ("tarihsel_tablo" if changes_kaynak == "wikipedia_historical_components"
                     else "secilmis_degisiklikler" if changes_kaynak else None)
    changes_meta = data.get("changes_meta")
    if not changes:
        return {"pit": False, "neden": "değişiklik tablosu yok — as_of bugünkü listeye eşit",
                "changes_kaynak": changes_kaynak, "kaynak_sinifi": kaynak_sinifi,
                "changes_meta": changes_meta}
    for ch in changes:
        d = _iso(ch.get("date"))
        if d and d > date and (_tick(ch.get("added")) or _tick(ch.get("removed"))):
            return {"pit": True, "neden": None, "changes_kaynak": changes_kaynak,
                    "kaynak_sinifi": kaynak_sinifi, "changes_meta": changes_meta}
    return {"pit": False,
            "neden": "değişiklik günlüğü `date` kapsamının dışında — as_of bugünkü listeye eşit",
            "changes_kaynak": changes_kaynak, "kaynak_sinifi": kaynak_sinifi,
            "changes_meta": changes_meta}


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
