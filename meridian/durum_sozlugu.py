"""F8 KANONİK DURUM SÖZLÜĞÜ — dört ad-tutarsızlığı sınıfının TEK bağlama noktası (WP8-C).

ÖLÇÜM TABANI: docs/TASARIM-F8-DURUM-SOZLUGU-2026-08-22.md (§4 tutarsızlık envanteri, §5 kanonik
sözlük, §6 geçiş haritası). Bu modül o envanterin koda dökülmüş hâlidir: dört sınıfın —
öğrenme mandalı (T1.1) · acil durdurma (T1.2) · hüküm alanı (T1.3) · açıklama alanı (T1.4) —
her eski adı burada TEK kanonik ada bağlanır.

GEÇİŞ REJİMİ (toptan yeniden-adlandırma YOK — canlı state'te eski adlı kayıtlar yaşıyor):
  * ÜRETİCİ tarafı kanonik adı EK alan olarak taşır (çift-alan; eski ad silinmez).
  * OKUYUCU tarafı önce kanonik adı arar, yoksa eski (eşanlamlı) adı okur — ve HER eşanlamlı
    okuma sayaçlıdır. Sayaç uzun süre 0 kalırsa eski adın okuyucu-ölümü KANITLANMIŞ olur;
    düşürme kararını Rol-1 verir (bu modül hiçbir adı silmez, silinmesini önermekle yetinir).
  * KALIR-şerhli adlar (API `halted`/`learn_halted` yüzeyleri, sessiz_hat `saglikli`,
    universe `status`, alarm_gunluk `durum`) yeniden adlandırılMAZ — sözlük onları kanonik
    kimliğe EŞLEME KAYDI olarak bağlar (tasarım §6: "ad değiştirme değil, eşleme kaydı").

NEDEN AYRI MODÜL: sözlüğü hem watchdog (üretici) hem api (servis) hem testler (çivi) okur;
watchdog'a gömülseydi kanonik küme 3400+ satırlık dosyaya çivilenirdi. Kanonik KÜME ve OKUYUCU
yolu hiçbir meridian modülüne bağlı değildir (döngüsel import riski sıfır, testte tek başına
yüklenebilir); yalnız KALICI SAYAÇ katmanı `store`/`obs`/`config`e dokunur ve o ithaller
fonksiyon İÇİNDEdir — modül yüklenirken hâlâ hiçbir meridian modülü çekilmez.

SAYAÇ REJİMİ KALICIDIR (TSK-070, 2026-09-15 — önceki rejim SÜREÇ-İÇİYDİ ve şöyle düştü:
worker restart'ı sayaçları sıfırlıyordu, dağıtımlar ise günlüktü; "eski adın okuyucusu öldü"
hükmü ≥30 günlük restart'sız bir pencere istediği için ASLA verilemiyordu — yani ölçüm
yapılıyor, hüküm yapısal olarak imkânsız kalıyordu). Sayaçlar artık `SAYAC_DEFTERI` adlı
kalıcı deftere işlenir; defter süreçler-arasıdır (worker ve api AYRI süreçlerdir, artış kilit
altında oku-artır-yaz ile biner) ve PENCERE META taşır (ilk kayıt · son kayıt · son yazım) ki
"kaç gündür ölçülüyor" sorusu uydurma olmadan cevaplanabilsin. Bedel AÇIK: defterin dış
okuyucusu statik grafikte GÖRÜNMEZ (yazan da okuyan da bu modül) — muafiyet `codelaw`
DECLARED_SINKS kaydında gerekçesiyle beyanlıdır; gerçek tüketici zinciri
`durum_sozlugu.esanlamli_okumalar` + `durum_sozlugu.esanlamli_pencere` → `api._durum_sozlugu`
→ /api/diagnostics → pano f8SozlukSatiri'dir.
"""
from __future__ import annotations

# ---- T1.3 — HÜKÜM ALANI (5 ad → `ok`) -------------------------------------------------------
# Kanonik hüküm ÜÇ değerlidir: True (temiz) · False (ihlal) · None (HÜKÜM YOK — asla "temiz"
# sayılmaz). `failed` işaret TERSİYLE eşlenir (tasarım §4a). `saglikli` sessiz_hat'ın BEYANLI
# iki-değerli (fail-closed) alanıdır — kalır, şerhle okunur. `status`/`durum` birer durum
# ENUM'udur, hüküm değil: onlardan hüküm TÜRETİLMEZ (uydurma yasağı; tek istisna `status=="ok"`
# ki o zaten hükmün kendisidir). Sıralama envanter sırasıdır ve DONUKTUR (v271 çivisi).
HUKUM_KANONIK = "ok"
HUKUM_ESANLAMLI = ("failed", "saglikli", "status", "durum")

# ---- T1.4 — AÇIKLAMA ALANI (7 ad / 2 dil → `neden` + `beyan`) -------------------------------
# `neden` makine-yakın kısa neden; `beyan` insan-okur tam cümle (pano BUNU basar, ikinci metin
# kurmaz). Eşanlamlı sırası okuma önceliğidir: `detail` → `detay` → `note` → `reason` → `error`.
# `error` YALNIZ dedektör-düşüş iskeletinde meşrudur (tasarım §4a) — bu yüzden listenin sonunda.
NEDEN_KANONIK = "neden"
BEYAN_KANONIK = "beyan"
NEDEN_ESANLAMLI = ("detail", "detay", "note", "reason", "error")

# ---- T3.1 — SAYAÇ ALANI (`watchdog.report().ok` sayı-taşıma vakası → `n_ok`) ----------------
# A4 KARARI (Rol-1, 2026-08-23): üretici ayrıştı — `report()` sayacı `n_ok`ta, hükmü `ok`ta
# taşır. Eski sayı-taşıyan `ok` bir dönem EŞANLAMLI okunur (`n_ok_oku`, sayaçlı) ki dağıtım-arası
# eski-şekilli bir yük panoyu boş bırakmasın; düşürme kararı Rol-1'de. `hukum_oku`nun "sayı-ok
# hüküm sayılmaz" emniyeti KALIR — eski-şekilli yükler için hâlâ gerekli.
SAYAC_KANONIK = "n_ok"
SAYAC_ESANLAMLI = ("ok",)

# ---- T1.1 + T1.2 — DURDURMA KOLLARI (kanonik KOL ADI → eski/eşanlamlı yazımlar) -------------
# Kanonik kol adları sessiz_hat'ın bugünkü adlarıdır (tasarım §6 kararı): `soft_halt` ve
# `halt_learning`. API alan adları (`halted` ×4 yüzey, `learn_halted`) ve dosya adları
# (`state/HALT`, `state/LEARN_HALT`) KIRILMAZ — buradaki liste onları kanonik kimliğe bağlayan
# eşleme kaydıdır; okuyucu `kol_adi()` eşanlamlıyı kanonik ada çevirir (sayarak).
# Açık Soru A3 KAPANDI (operatör kararı 2026-08-23, E-kod partisi [1]): hermes ÜRETİCİSİ artık
# kanonik `halt_learning` yazar (hermes_runtime.py ısınma dalı + reflect.submit LEARN_HALT dalı).
# Eski "learning_halted" DÖNEM SONUNA DEK eşanlamlı-okunur: diskte restart-öncesi persist edilmiş
# değerler için hermes_runtime.status() `kol_adi()` üzerinden sayaçlı çevirir; pano (app.js
# `f8KolAd`) ikinci emniyet olarak kalır. Ad listeden SİLİNMEDİ — düşürme kararı sayaçla Rol-1'de.
KOL_KANONIK = {
    "soft_halt": ("HALT", "halted", "HALT_ACTIVE", "meridian_halted", "halt"),
    "halt_learning": ("LEARN_HALT", "learn_halted", "learning_halted"),
}
_KOL_TERS = {eski: kanonik for kanonik, eskiler in KOL_KANONIK.items() for eski in eskiler}

# ---- EŞANLAMLI-OKUMA SAYAÇLARI (ölüm tarihi ölçümü) -----------------------------------------
# Anahtar biçimi "<sinif>:<eski_ad>" (örn. "hukum:failed", "neden:detail", "kol:learning_halted",
# "sayac:ok").
# KALICI (TSK-070, 2026-09-15 — gerekçe modül başlığında). Dış okuyucu: api._durum_sozlugu →
# /api/diagnostics → app.js f8SozlukSatiri (YASA 6 — sayacın kendisi okuyucusuz kalamaz).
SAYAC_DEFTERI = "durum_sozlugu_sayac.json"
SAYAC_SEMA = 1

#: Defterin BELLEK nüshası. Diskten YÜKLENMİŞ hâldir (tek kaynak diskteki defterdir; bellek onun
#: kopyasıdır, ayrı bir gerçek değil) — yazım düşerse bellek ileride kalabilir ve o fark
#: `esanlamli_pencere` çıktısında son kayıt ile son yazım damgasının ayrışmasıyla GÖRÜNÜR olur.
_ESANLAMLI_OKUMA: dict[str, int] = {}
_PENCERE: dict[str, str | None] = {"ilk_kayit_utc": None, "son_kayit_utc": None,
                                   "son_yazim_utc": None}
#: Belleğin hangi disk sürümünden geldiği (`store.stamp`). None = bu süreçte HİÇ yüklenmedi.
_YUKLU_DAMGA: tuple | None = None
#: Yazım uyarısı süreç başına BİR kez — arızalı diskte her eşanlamlı okuma bir satır basmasın.
_YAZIM_UYARILDI = False


def _simdi() -> str:
    """UTC damgası (saniye çözünürlüğü) — depo deseni: mikro saniye kırpılmış ISO-8601."""
    import datetime as _dt
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat()


def _bos_defter() -> dict:
    """Hiç eşanlamlı okuma yapılmamış defterin ŞEKLİ. Sayaçlar boş, pencere alanları None —
    0 DEĞİL: "hiç okunmadı" ile "sıfır gündür ölçülüyor" aynı şey değildir (uydurma yasağı)."""
    return {"schema": SAYAC_SEMA, "sayaclar": {},
            "ilk_kayit_utc": None, "son_kayit_utc": None, "son_yazim_utc": None}


def _gecerli(doc) -> bool:
    """Defterin ŞEKLİ sözleşmeye uyuyor mu? (İçeriğin doğruluğu değil — şekli.) bool int'in alt
    sınıfı olduğu için ayrıca elenir: True bir sayaç değeri DEĞİLDİR."""
    return (isinstance(doc, dict) and doc.get("schema") == SAYAC_SEMA
            and isinstance(doc.get("sayaclar"), dict)
            and all(isinstance(k, str) and isinstance(v, int) and not isinstance(v, bool)
                    for k, v in doc["sayaclar"].items()))


def _uyar(olay: str, **alanlar) -> None:
    """Gözlem kanalına uyarı. Kanal düşerse SAYAÇ YOLU DÜŞMEZ — ölçümün kendisi, ölçümün
    raporlanmasından daha kritiktir."""
    try:
        from . import obs
        obs.warn(olay, **alanlar)
    except Exception:  # sessiz-yutma: gözlem kanalı (obs) kurulamadı ya da düştü; uyarı kaybı sayacın kendisini düşürmekten UCUZDUR ve çağıran yolun davranışı değişmez
        pass


def _defter_yolu():
    """Kalıcı defterin MUTLAK yolu — `config.STATE` her çağrıda okunur (ölçüm sandbox'ları onu
    değiştirir; yolu modül yüklenirken dondurmak sandbox'ları canlı deftere yazdırırdı)."""
    from . import config
    return config.STATE / SAYAC_DEFTERI


def _bozugu_yedekle(neden: str) -> None:
    """Şekli bozulmuş defteri `.bozuk-<ts>` adına TAŞIR (SİLMEZ — kanıt kaybolmaz) ve olayı
    ADIYLA raporlar; sayım sıfırdan devam eder. Sessizce ezmek, sayacın neden geri saydığını
    kayıtsız bırakırdı."""
    import datetime as _dt
    import os
    yol = _defter_yolu()
    damga = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    hedef = yol.with_name(f"{yol.name}.bozuk-{damga}")
    yedek = None
    try:
        os.replace(yol, hedef)
        yedek = hedef.name
    except OSError:  # sessiz-yutma: yedekleme EN İYİ ÇABAdır (dosya kaybolmuş/izin yok); başarısızlığı aşağıdaki uyarıda `yedek: None` olarak GÖRÜNÜR, sayaç yolu yine de yaşar
        yedek = None
    _uyar("f8_sayac_defteri_bozuk", defter=SAYAC_DEFTERI, neden=neden, yedek=yedek)


def _belleye_al(doc: dict) -> None:
    """Disk nüshasını belleğe yazar (tek kaynak disktir; bellek onun kopyasıdır)."""
    _ESANLAMLI_OKUMA.clear()
    _ESANLAMLI_OKUMA.update({k: int(v) for k, v in (doc.get("sayaclar") or {}).items()})
    for alan in _PENCERE:
        _PENCERE[alan] = doc.get(alan)


def _yukle() -> None:
    """Defteri diskten belleğe alır — İLK temasta ve dosya DEĞİŞTİĞİNDE (damga kıyası).

    Tazeleme şart: worker eşanlamlı okumayı SAYAR, api onu SERVİS EDER ve ikisi ayrı süreçtir;
    bir kez yükleyip donsaydı pano restart'a kadar bayat bir sayı gösterirdi. Dosya yoksa defter
    boştur (bu bir ihlal değil, ölçümün beklenen hâlidir: eski adı kimse okumamış)."""
    global _YUKLU_DAMGA
    from . import store
    damga = store.stamp(SAYAC_DEFTERI)
    if _YUKLU_DAMGA == damga:
        return
    doc = store.read_json(SAYAC_DEFTERI, None)
    if doc is None and not _defter_yolu().exists():
        _belleye_al(_bos_defter())
        _YUKLU_DAMGA = damga
        return
    if not _gecerli(doc):
        # DOSYA VAR AMA ŞEKLİ YOK: `store.read_json` çözülemeyen JSON'u zaten varsayılana düşürür
        # (ve kendi uyarısını basar); buradaki ayrım "dosya yok" ile "dosya bozuk" arasındadır.
        _bozugu_yedekle("cozulemedi" if doc is None else "sema_uyusmadi")
        _belleye_al(_bos_defter())
        _YUKLU_DAMGA = store.stamp(SAYAC_DEFTERI)
        return
    _belleye_al(doc)
    _YUKLU_DAMGA = damga


def _artir(doc, anahtar: str, simdi: str) -> bool:
    """`store.update_json` geri çağrısı — KİLİT ALTINDA oku-artır-yaz. Artış DİSKTEKİ değerin
    üstüne biner: iki süreç aynı defteri paylaşır, kayıp-güncelleme yapısal olarak imkânsızdır."""
    if not isinstance(doc, dict):
        raise ValueError(f"{SAYAC_DEFTERI}: defter sözlük değil ({type(doc).__name__})")
    if not _gecerli(doc):
        doc.clear()
        doc.update(_bos_defter())
    sayaclar = doc["sayaclar"]
    sayaclar[anahtar] = int(sayaclar.get(anahtar, 0)) + 1
    if not doc.get("ilk_kayit_utc"):
        doc["ilk_kayit_utc"] = simdi        # İLK kayıt bir kez çivilenir, sonra DEĞİŞMEZ
    doc["son_kayit_utc"] = simdi
    doc["son_yazim_utc"] = simdi
    return True


def _say(anahtar: str) -> None:
    """Bir eşanlamlı okumayı SAYAR: bellekte artırır, kalıcı deftere işler."""
    global _YUKLU_DAMGA, _YAZIM_UYARILDI
    _yukle()
    simdi = _simdi()
    # BELLEK HER HÂLÜKÂRDA ARTAR: disk yazımı düşse bile bu süreçteki sayım yaşar. Sayaç bir
    # ÖLÇÜMDÜR; kalıcılık onun dayanıklılığıdır, koşulu değil.
    _ESANLAMLI_OKUMA[anahtar] = _ESANLAMLI_OKUMA.get(anahtar, 0) + 1
    if _PENCERE["ilk_kayit_utc"] is None:
        _PENCERE["ilk_kayit_utc"] = simdi
    _PENCERE["son_kayit_utc"] = simdi
    from . import store
    try:
        doc = store.update_json(SAYAC_DEFTERI, lambda d: _artir(d, anahtar, simdi), _bos_defter())
    except (OSError, ValueError, TypeError):  # sessiz-yutma: kalıcı defter YAZILAMADI (izin/disk dolu/şekilsiz nüsha) — okuma yolu düşmez, bellek sayımı ayakta kalır ve kayıp aşağıdaki uyarıyla ADIYLA görünür
        if not _YAZIM_UYARILDI:
            _YAZIM_UYARILDI = True
            _uyar("f8_sayac_yazilamadi", defter=SAYAC_DEFTERI, anahtar=anahtar)
        return
    _belleye_al(doc)
    _YUKLU_DAMGA = store.stamp(SAYAC_DEFTERI)


def esanlamli_okumalar() -> dict[str, int]:
    """Sayaçların KOPYASI — dış okuyucu iç sözlüğü mutasyona uğratamaz. Defter diskten tazelenir
    (damga değiştiyse): panonun gördüğü sayı, worker'ın yazdığı sayıdır."""
    _yukle()
    return dict(_ESANLAMLI_OKUMA)


def esanlamli_pencere() -> dict:
    """Sayaçların ÖLÇÜM PENCERESİ — "eski adın okuyucusu öldü" hükmünün ZAMAN eksenidir.

    Sayaç tek başına hüküm vermez: "0" ancak bir PENCEREYLE birlikte anlamlıdır (bir saatlik
    sıfır ile otuz günlük sıfır aynı şey değildir). `gun` ilk kayıttan bugüne TAM gündür; hiç
    kayıt yoksa None — 0 DEĞİL (uydurma yasağı). `son_kayit_utc` ile `son_yazim_utc` ayrışırsa
    kalıcı yazım düşmüş demektir (bellek ilerde, disk geride)."""
    _yukle()
    ilk = _PENCERE["ilk_kayit_utc"]
    return {"ilk_kayit_utc": ilk,
            "son_kayit_utc": _PENCERE["son_kayit_utc"],
            "son_yazim_utc": _PENCERE["son_yazim_utc"],
            "gun": _gun_farki(ilk),
            "kaynak_dosya": SAYAC_DEFTERI}


def _gun_farki(ilk: str | None) -> int | None:
    """İlk kayıttan BUGÜNE tam gün; damga yoksa ya da çözülemiyorsa None (gün UYDURULMAZ)."""
    if not isinstance(ilk, str) or not ilk:
        return None
    import datetime as _dt
    try:
        t0 = _dt.datetime.fromisoformat(ilk)
    except ValueError:  # sessiz-yutma: damga çözülemedi (elle düzenlenmiş/eski biçim) — gün UYDURULMAZ, çağıran None'ı "ölçülemedi" diye okur
        return None
    if t0.tzinfo is None:
        t0 = t0.replace(tzinfo=_dt.timezone.utc)
    return max(0, (_dt.datetime.now(_dt.timezone.utc) - t0).days)


def _sifirla_test_icin() -> None:
    """YALNIZ TEST hijyeni (v271/v499): belleği VE kalıcı defteri siler, böylece testler arası
    sayaç sızıntısı kesilir. Üretim yolunda ÇAĞRILMAZ — canlıda sayaç sıfırlamak, ölçmeye
    çalıştığımız ölüm tarihini silmek olurdu (bu yüzden sözleşme testlerin `config.STATE`i
    sandbox'a almasıdır: silinen defter HER ZAMAN sandbox defteridir)."""
    global _YUKLU_DAMGA, _YAZIM_UYARILDI
    _ESANLAMLI_OKUMA.clear()
    for alan in _PENCERE:
        _PENCERE[alan] = None
    _YUKLU_DAMGA = None
    _YAZIM_UYARILDI = False
    try:
        _defter_yolu().unlink()
    except (OSError, ImportError):  # sessiz-yutma: defter zaten yok ya da state dizini kurulu değil — test hijyeninin işi bitmiştir, silinecek bir şey kalmadı
        pass


# ---- OKUYUCULAR -----------------------------------------------------------------------------
def hukum_oku(rapor) -> tuple[bool | None, str | None]:
    """Bir rapor sözlüğünden ÜÇ değerli hüküm okur: (ok, kaynak_alan).

    Önce kanonik `ok`; alan varsa ama DEĞERİ hüküm değilse (SAYI — eski-şekilli `report().ok`
    yükü, T3.1; A4 kararıyla üretici 2026-08-23'te ayrıştı, emniyet ESKİ yükler için kalır)
    hüküm UYDURULMAZ, eşanlamlılara da düşülmez: (None, None) döner. Eşanlamlı okuma sayaçlıdır.
    Hiçbir ad yoksa (None, None) — "hüküm yok" dürüst cevaptır, "temiz" değildir."""
    if not isinstance(rapor, dict):
        return None, None
    if HUKUM_KANONIK in rapor:
        v = rapor[HUKUM_KANONIK]
        if v is None or isinstance(v, bool):
            return v, HUKUM_KANONIK
        return None, None          # sayı-ok: hüküm alanı değil sayaç (T3.1) — hüküm türetilmez
    if "failed" in rapor:
        _say("hukum:failed")
        f = rapor["failed"]
        return (None if f is None else (not bool(f))), "failed"   # işaret TERS (tasarım §4a)
    if "saglikli" in rapor:
        _say("hukum:saglikli")
        s = rapor["saglikli"]
        # BEYANLI iki değerli (fail-closed): ölçülemeyen segment SAĞLIKSIZDIR — sözleşme
        # api._sessiz_hat docstring'inde; sözlük onu değiştirmez, olduğu gibi taşır.
        return (None if s is None else bool(s)), "saglikli"
    if "status" in rapor:
        _say("hukum:status")
        # ENUM'dan hüküm türetilmez; tek istisna "ok" (hükmün kendisi). "unknown"/"yok"/diğerleri
        # → hüküm YOK (ihlal de değil, temiz de değil — o ayrımı raporun kendi alanları taşır).
        return (True if rapor["status"] == "ok" else None), "status"
    if "durum" in rapor:
        _say("hukum:durum")
        # `durum` (defter_yok/dolu/bos…) bir DOLULUK durumudur, hüküm değil: hiçbir değeri
        # True/False'a çevrilmez (uydurma yasağı). Ad yine de sayılır — okunduğu ölçülür.
        return None, "durum"
    return None, None


def n_ok_oku(rapor) -> tuple[int | None, str | None]:
    """Penceresinde-mekanizma SAYACINI okur: (n, kaynak_alan). Önce kanonik `n_ok`; yoksa eski
    sayı-taşıyan `ok` (sayaçlı — "sayac:ok"). İKİ YÖNDE DE TİP EMNİYETİ: bool bir sayaç DEĞİLDİR —
    `hukum_oku`nun "sayı-ok hüküm sayılmaz" kuralının ayna görüntüsü ("hüküm-ok sayaç sayılmaz");
    bool int'in alt sınıfı olduğundan (True == 1) emniyetsiz okuma yeni-şekilli bir hükmü sessizce
    "1 mekanizma" diye uydururdu. Hiçbir alan sayı taşımıyorsa (None, None) — 0 DEĞİL."""
    if not isinstance(rapor, dict):
        return None, None
    v = rapor.get(SAYAC_KANONIK)
    if isinstance(v, int) and not isinstance(v, bool):
        return v, SAYAC_KANONIK
    v = rapor.get("ok")
    if isinstance(v, int) and not isinstance(v, bool):
        _say("sayac:ok")
        return v, "ok"
    return None, None


def neden_oku(rapor) -> tuple[str | None, str | None]:
    """Makine-yakın kısa nedeni okur: (metin, kaynak_alan). Önce kanonik `neden`; yoksa
    eşanlamlılar envanter sırasıyla (her biri sayaçlı). Boş dizge "neden var" sayılmaz."""
    if not isinstance(rapor, dict):
        return None, None
    v = rapor.get(NEDEN_KANONIK)
    if v:
        return str(v), NEDEN_KANONIK
    for ad in NEDEN_ESANLAMLI:
        v = rapor.get(ad)
        if v:
            _say(f"neden:{ad}")
            return str(v), ad
    return None, None


def kol_adi(ad: str) -> str:
    """Durdurma kolunun kanonik adı. Eşanlamlı → kanonik (sayaçlı). TANINMAYAN ad DEĞİŞTİRİLMEZ
    ve sayılmaz — pano kuralının modül hâli: tanımadığını sessizce düşürmez, sessizce de
    "düzeltmez" (örn. hermes `last_result="rejected_by_backtest"` bir kol adı değildir)."""
    if ad in KOL_KANONIK:
        return ad
    kanonik = _KOL_TERS.get(ad)
    if kanonik is not None:
        _say(f"kol:{ad}")
        return kanonik
    return ad


def normalize_satir(kimlik: str, rapor) -> dict:
    """Tasarım §6 kanonik okuyucu satırı: {kimlik, ok, kaynak_alan, olculemedi, kapsam_disi,
    askida, neden, neden_kaynak, beyan}. SENTEZ YOK, UYDURMA YOK: her hüküm/neden kaynak alanın
    ADINI taşır (geçiş haritası canlıda görünür olur); raporda beyan edilmemiş bir bayrak
    (olculemedi/kapsam_disi/askida) None kalır — False'a çevrilmez ("beyan yok" ≠ "hayır")."""
    ok, kaynak = hukum_oku(rapor)
    neden, neden_kaynak = neden_oku(rapor)
    r = rapor if isinstance(rapor, dict) else {}
    return {"kimlik": kimlik, "ok": ok, "kaynak_alan": kaynak,
            "olculemedi": r.get("olculemedi"), "kapsam_disi": r.get("kapsam_disi"),
            "askida": r.get("askida"), "neden": neden, "neden_kaynak": neden_kaynak,
            "beyan": r.get(BEYAN_KANONIK)}
