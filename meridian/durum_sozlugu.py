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


# ---- PANO KELİMELERİ (TSK-070 A8 · tasarım §4b + §9.1 eki, 2026-09-15) ----------------------
# TEK KAYNAK: operatörün gördüğü HER kelime burada üretilir. UI ham kod (`stale`, `no_bars`,
# `lock_busy`, `damga_ilerledi_icerik_ayni`…) ÇEVİRMEZ — çeviri iki yerde yaşarsa sessizce
# ayrışır (tek-kaynak yasası; eski `app.js` bugün satır-içi çeviriyor ve o yüzeyin emekliliği
# ayrı kalemdir, deseni TEKRARLANMAZ). Küme tasarım belgesiyle BİREBİRDİR ve çivi belgeyi
# dosyadan okur: `tests/test_durum_sozlugu_aileler_v503.py::test_a_pano_kelime_kumesi_belgeyle_birebir`.
# YASA 6 — okuyucular ADIYLA: `api._durum_sozlugu` → /api/diagnostics.durum_sozlugu.satirlar →
# Vite pano yüzeyi `DurumSozlugu.tsx` (TSK-070 Task 2) + yukarıdaki çivi.
# "BOŞTA" BİLEREK YOK: §4b listesinde geçer ama hiçbir ÜRETİCİ onu ölçmüyor — ölçülmeyen kelime
# basılmaz (uydurma yasağı, §9.1 canlılık hükmü).
PANO_KELIME = {
    "kadans:ok": "PENCEREDE", "kadans:stale": "GECİKTİ", "kadans:never": "HİÇ KOŞMADI",
    "kadans:askida": "ASKIDA", "kadans:bastirilan": "BASTIRILDI",
    "dedektor:ok": "TEMİZ", "dedektor:ihlal": "İHLAL", "dedektor:olculemedi": "ÖLÇÜLEMEDİ",
    "dedektor:kapsam_disi": "KAPSAM DIŞI", "dedektor:dustu": "DEDEKTÖR DÜŞTÜ",
    "canlilik:ok": "KOŞUYOR", "canlilik:orphan": "DURDU (orphan)",
    "canlilik:stall": "DURDU (stall)",
    "kitap:degisim_yok": "DEĞİŞİM YOK", "kitap:damgali_degisim": "DAMGALI DEĞİŞİM",
    "kitap:damga_ilerledi_icerik_ayni": "İÇERİK-AYNI YENİDEN YAZIM",
    "kitap:damgasiz_yazim": "DAMGASIZ YAZIM", "kitap:taban_yok": "İLK GÖZLEM",
    "kilit:kapali": "KAPALI", "kilit:cekili": "ÇEKİLİ",
    "mandal:ilk": "İLK ALARM", "mandal:mandalli": "MANDALLI", "mandal:yeniden": "YENİDEN",
    "mandal:dustu": "DÜŞTÜ",
    "intraday:session": "SEANS DIŞI", "intraday:pencere": "PENCERE ÖNCESİ",
    "intraday:halt": "HALT", "intraday:stale": "BAYAT", "intraday:no_bars": "BAR YOK",
}

#: Panonun aileleri basma SIRASI (tasarım §9.2). Sıra bir sunum kararıdır, hüküm değildir.
AILE_SIRASI = ("kadans", "dedektor", "canlilik", "bekci", "kitap", "kilit", "mandal",
               "hermes", "intraday")

#: Durdurma kollarının insan-okur etiketi. `devre_kesici` KADEME NUMARASI TAŞIMAZ: kademe
#: ölçülmedi, uydurulmaz (tasarım §9.1 hükmü — "Kademe 3" yazmak sahte bir mertebe olurdu).
KILIT_BEYAN = {
    "soft_halt": "Kademe 1 · Soft Halt (yeni giriş durur)",
    "halt_learning": "Kademe 4 · Öğrenme durdurma (hipotez/antrenman kolu)",
    "devre_kesici": "Devre kesici (günlük zarar) — mertebesi ölçülmedi",
}

#: Kitap damgası sınıfı → kanonik kelime anahtarı (üretici `watchdog.kitap_damga_report`).
KITAP_SINIF = {"degisim_yok": "kitap:degisim_yok", "damgali_degisim": "kitap:damgali_degisim",
               "damga_ilerledi_icerik_ayni": "kitap:damga_ilerledi_icerik_ayni",
               "damgasiz_yazim": "kitap:damgasiz_yazim", "taban_yok": "kitap:taban_yok"}

#: Kitap sınıfının HÜKMÜ — yalnız `damgasiz_yazim` ihlaldir (üreticinin kendi hükmüyle aynı:
#: `ok = not damgasiz`); `taban_yok`/`olculemedi` hükümsüzdür ("temiz" DEĞİL).
KITAP_HUKUM = {"degisim_yok": True, "damgali_degisim": True,
               "damga_ilerledi_icerik_ayni": True, "damgasiz_yazim": False,
               "taban_yok": None, "olculemedi": None}

#: Canlılık bacağının DURMA kelimesi bacağa göre ayrışır (orphan ≠ stall; §9.1).
CANLILIK_DURDU = {"sprint": "canlilik:orphan", "learning": "canlilik:stall"}

#: Intraday atlama sayaçlarının kanonik anahtarları (üretici `intraday_cycle` `skipped`).
INTRADAY_ATLAMA = ("session", "pencere", "halt", "stale", "no_bars")

#: Mandal defterleri — SIRA kimliktir. `koruma_alarmed` BİLEREK dosyasızdır: koruma/mutabakat
#: bekçilerinin mandalı SÜREÇ-İÇİdir (worker belleğinde) ve api AYRI bir süreçtir; deftere
#: yazılmadığı sürece bu satır ölçülemez kalır ve o boşluk panoda ADIYLA görünür (uydurma yerine
#: beyan — Yasa 6'nın açık kalemi).
MANDAL_DEFTERLERI = ("alarm_mandal", "watchdog_alarmed", "integrity_alarmed", "koruma_alarmed")
_MANDAL_BEYAN = {
    "alarm_mandal": "obs imza mandalı — tekrar eden bilinen-aktif durumlar (satırsız sayılır)",
    "watchdog_alarmed": "kadans bekçisi mandalı — penceresini aşmış ve HÂLÂ aşmakta olanlar",
    "integrity_alarmed": "bütünlük dedektörü mandalı — düzelen jeton düşer, bozulan YENİDEN alarmlanır",
    "koruma_alarmed": ("koruma/mutabakat mandalı SÜREÇ-İÇİdir (defter yok) — api süreci onu "
                       "okuyamaz; 'mandal yok' DEĞİL, 'ölçülemedi'"),
}
#: Her mandal defterinin YÜZEYİNDE öğe listesini taşıyan alan adı — YEDEK AD DEĞİL, SÖZLEŞME.
#: İki defter sınıfı iki AYRI şekil üretir ve şekiller birbirinin yerine geçmez:
#:   · `alarm_mandal`  → `alarm_mandal.json` imza sözlüğüdür (imza → {token, n, yeniden, …});
#:     yüzey ondan JETON kümesi türetir (`jetonlar`), yani bir ALARM KİMLİĞİdir.
#:   · ötekiler        → defterin kendisi düpedüz bir AD listesidir (`adlar`): kadans kontrol adı
#:     / bütünlük jetonu. Sayım `n` iki şekilde de vardır ama SAYDIĞI ŞEY farklıdır (imza vs ad).
#: Tek alana indirmek ya da iki alanı `or` ile birbirine yedekletmek ikisini ayırt edilemez
#: kılardı: öyle bir ifade "hangisi doluysa" demektir ve bir defter yanlış şekli taşısa da SESSİZ
#: geçerdi (v56 şema-takası dedektörü tam o deseni kovalar — beyan değil, kaynakta giderilir).
#: Yasak deseni bu şerh de LİTERAL YAZAMAZ: dedektör dosya metnini ham tarar, açıklama niyetiyle
#: yazılan örnek de ihlal olarak öter (aynı sınıf: çapa yasağının yorumlarda da geçerli olması).
#: Sözlük `MANDAL_DEFTERLERI` üzerinde TAMdır ve `[]` ile okunur: yeni bir defter alanını BEYAN
#: ETMEDEN eklenirse satır üretimi KeyError ile düşer, sessizce nedensiz satır basmaz.
_MANDAL_OGE_ALANI = {"alarm_mandal": "jetonlar", "watchdog_alarmed": "adlar",
                     "integrity_alarmed": "adlar", "koruma_alarmed": "adlar"}


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


def normalize_satir(kimlik: str, rapor, aile: str = "bekci") -> dict:
    """Tasarım §6 kanonik okuyucu satırı: {kimlik, aile, kelime, n, ok, kaynak_alan, olculemedi,
    kapsam_disi, askida, neden, neden_kaynak, beyan}. SENTEZ YOK, UYDURMA YOK: her hüküm/neden
    kaynak alanın ADINI taşır (geçiş haritası canlıda görünür olur); raporda beyan edilmemiş bir
    bayrak (olculemedi/kapsam_disi/askida) None kalır — False'a çevrilmez ("beyan yok" ≠ "hayır").

    `aile`/`kelime`/`n` 2026-09-15'te EKLENDİ (TSK-070 A8, tasarım §9.1): pano artık ham kod
    çevirmez, kelimeyi BURADAN alır. `n` kanonik sayaçtan (`n_ok_oku`) okunur — eski sayı-taşıyan
    `ok` okunursa SAYILIR, yani okuyucu-ölümü ölçümü bu yoldan da işler. Okuyucular ADIYLA:
    `api._durum_sozlugu` → /api/diagnostics.durum_sozlugu.satirlar → pano `DurumSozlugu.tsx`."""
    ok, kaynak = hukum_oku(rapor)
    neden, neden_kaynak = neden_oku(rapor)
    n, _ = n_ok_oku(rapor)
    r = rapor if isinstance(rapor, dict) else {}
    return {"kimlik": kimlik, "aile": aile, "kelime": _hukum_kelimesi(ok, r), "n": n,
            "ok": ok, "kaynak_alan": kaynak,
            "olculemedi": r.get("olculemedi"), "kapsam_disi": r.get("kapsam_disi"),
            "askida": r.get("askida"), "neden": neden, "neden_kaynak": neden_kaynak,
            "beyan": r.get(BEYAN_KANONIK)}


# =============================================================================================
# AİLE ADAPTÖRLERİ (TSK-070 A8 · tasarım §9.1) — hepsi SAF: dosya okuyan tek fonksiyon
# `mandal_yuzeyi`dir, kalanı çağıranın verdiği gövdeyi okur.
#
# ORTAK SÖZLEŞME (§4a + iki alan): her satır
# {aile, kimlik, kelime, ok, olculemedi, kapsam_disi, askida, neden, beyan, kaynak_alan, n}.
# `kelime` YALNIZ `PANO_KELIME`den gelir; `ok` ÜÇ değerlidir; ölçülemeyen sayı `None`dır ve
# pano onu "ÖLÇÜLEMEDİ (0 DEĞİL)" diye basar (v196 kuralı).
# YASA 6 — okuyucular ADIYLA: `api._durum_sozlugu` → /api/diagnostics.durum_sozlugu.satirlar →
# pano `DurumSozlugu.tsx` (TSK-070 Task 2) ve çivi `test_durum_sozlugu_aileler_v503`.
# =============================================================================================

def _satir(aile: str, kimlik: str, kelime: str, ok: bool | None, *, neden=None, beyan="",
           kaynak_alan="", n=None, olculemedi=False, kapsam_disi=False, askida=False) -> dict:
    """Aile adaptörlerinin ortak satır iskeleti (alan adları `normalize_satir` ile AYNI)."""
    return {"aile": aile, "kimlik": kimlik, "kelime": kelime, "ok": ok,
            "olculemedi": olculemedi, "kapsam_disi": kapsam_disi, "askida": askida,
            "neden": neden, "beyan": beyan, "kaynak_alan": kaynak_alan, "n": n}


def _hukum_kelimesi(ok: bool | None, rapor) -> str:
    """Hüküm çekirdeğinden (§4a) kanonik kelime — bekçi/dedektör ailelerinin ortak türetimi.

    SIRA HÜKÜMDÜR: düşen dedektör "İHLAL" değildir (ölçüm arızası ile ihlal aynı kelimeye
    düşerse teşhis yanlış yöne gider); hükümsüzlüğün SEBEBİ kelimeyi ayırır — yapılandırma
    (KAPSAM DIŞI) · beyanlı bekleme (ASKIDA) · kalanı ÖLÇÜLEMEDİ."""
    r = rapor if isinstance(rapor, dict) else {}
    if r.get("dedektor_dustu"):
        return PANO_KELIME["dedektor:dustu"]
    if ok is True:
        return PANO_KELIME["dedektor:ok"]
    if ok is False:
        return PANO_KELIME["dedektor:ihlal"]
    if r.get("kapsam_disi"):
        return PANO_KELIME["dedektor:kapsam_disi"]
    if r.get("askida"):
        return PANO_KELIME["kadans:askida"]
    return PANO_KELIME["dedektor:olculemedi"]


def _sayi(v) -> int | None:
    """Sayı mı? bool bir SAYI DEĞİLDİR (True == 1 tuzağı — `n_ok_oku`nun ayna emniyeti)."""
    return v if isinstance(v, int) and not isinstance(v, bool) else None


def _ad(x) -> str:
    """Bekçi listeleri ya satır SÖZLÜĞÜ (`{name, gap_h…}`, canlı `watchdog.report`) ya düz ad
    taşır; ikisi de okunur — yoksa canlı yük sessizce "17/17 PENCEREDE" görünürdü."""
    return str(x.get("name")) if isinstance(x, dict) else str(x)


def _kadans_beyan(x) -> str:
    """Gecikme satırının insan-okur cümlesi; düz ad şeklinde ölçülecek bir şey yoktur."""
    if not isinstance(x, dict):
        return ""
    g, e = x.get("gap_h"), x.get("expected_h")
    if g is None or e is None:
        return str(x.get(BEYAN_KANONIK) or x.get(NEDEN_KANONIK) or "")
    return f"{g} sa sessiz (pencere {e} sa)"


def kadans_satirlari(rapor, expected, bastirilan=None) -> list[dict]:
    """17 mekanizmanın kadans satırı (§9.1) — `watchdog.report()` + `watchdog.EXPECTED`.

    ÖLÇÜLMEMİŞ RAPOR YEŞİLE BOYANMAZ: bekçi raporu gelmediyse (şekli yok) her mekanizma
    ÖLÇÜLEMEDİ'dir — boş listeleri "hiçbiri gecikmemiş" diye okumak 17 sahte yeşil üretirdi.
    `bastirilan` (mekanizma → günlük tavana takılmış alarm sayısı, `api._alarm_gunluk`
    defterinden) verildiğinde ihlalli satır BASTIRILDI kelimesini taşır ve sayı `n`de durur:
    bastırılan alarm SAYILIR ve GÖRÜNÜR — hüküm (`ok`) bundan etkilenmez."""
    r = rapor if isinstance(rapor, dict) else {}
    olctu = ("total" in r) or ("n_ok" in r)
    stale = {_ad(x): x for x in (r.get("stale") or [])}
    never = {_ad(x): x for x in (r.get("never") or [])}
    askida = {_ad(x): x for x in (r.get("askida") or [])}
    bast = bastirilan if isinstance(bastirilan, dict) else {}
    out = []
    for ad in sorted(expected or ()):
        nb = _sayi(bast.get(ad))
        if not olctu:
            out.append(_satir("kadans", ad, PANO_KELIME["dedektor:olculemedi"], None,
                              olculemedi=True, kaynak_alan="watchdog.report",
                              beyan="bekçi raporu bu yanıtta ölçülmedi — 'penceresinde' DEĞİL"))
            continue
        if ad in never:
            kelime, ok, kod, kaynak, x = (PANO_KELIME["kadans:never"], False, "never",
                                          "watchdog.never", never[ad])
        elif ad in stale:
            kelime, ok, kod, kaynak, x = (PANO_KELIME["kadans:stale"], False, "stale",
                                          "watchdog.stale", stale[ad])
        elif ad in askida:
            x = askida[ad]
            kelime, ok, kod, kaynak = (PANO_KELIME["kadans:askida"], None,
                                       (x.get(NEDEN_KANONIK) if isinstance(x, dict) else None)
                                       or "askida", "watchdog.askida")
        else:
            kelime, ok, kod, kaynak, x = (PANO_KELIME["kadans:ok"], True, None,
                                          "watchdog.n_ok", None)
        if ok is False and nb:
            kelime = PANO_KELIME["kadans:bastirilan"]
        out.append(_satir("kadans", ad, kelime, ok, neden=kod, beyan=_kadans_beyan(x),
                          kaynak_alan=kaynak, n=nb, askida=(ad in askida)))
    return out


def dedektor_satirlari(integrity) -> list[dict]:
    """Sekiz bütünlük dedektörü — şekilleri `normalize_satir` ile UYUMLU (her biri `ok` taşır),
    tek eklenen aile adıdır. Ad-hoc metinler `neden`/`beyan`a iner, kelime TEKtir (§9.1)."""
    r = integrity if isinstance(integrity, dict) else {}
    return [normalize_satir(ad, rapor, aile="dedektor") for ad, rapor in r.items()]


def canlilik_satirlari(liveness) -> list[dict]:
    """Sprint çocuğu + öğrenme döngüsü (§9.1). ÖLÇÜLMEYEN BACAK SATIR AÇMAZ: üretici "BOŞTA"
    diye bir hâl ölçmüyor, dolayısıyla pano onu UYDURMAZ (bacak yoksa satır da yok)."""
    lv = liveness if isinstance(liveness, dict) else {}
    out = []
    for kimlik in ("sprint", "learning"):
        rapor = lv.get(kimlik)
        if not isinstance(rapor, dict):
            continue
        ok, kaynak = hukum_oku(rapor)
        if ok is True:
            kelime = PANO_KELIME["canlilik:ok"]
        elif ok is False:
            kelime = PANO_KELIME[CANLILIK_DURDU[kimlik]]
        else:
            kelime = _hukum_kelimesi(ok, rapor)
        neden, _ = neden_oku(rapor)
        out.append(_satir("canlilik", kimlik, kelime, ok, neden=neden,
                          beyan=rapor.get(BEYAN_KANONIK) or "",
                          kaynak_alan=(f"liveness.{kimlik}.{kaynak}" if kaynak
                                       else f"liveness.{kimlik}"),
                          n=_sayi(rapor.get("n")),
                          olculemedi=bool(rapor.get("olculemedi"))))
    return out


def kitap_satirlari(rapor) -> list[dict]:
    """Damgalı varlık başına bir satır — sınıf → kelime (§9.1). Tanınmayan sınıf ÖLÇÜLEMEDİ'dir
    (sessizce "değişim yok" sayılmaz: silinmiş bir kitabı temiz raporlamanın ta kendisi olurdu)."""
    r = rapor if isinstance(rapor, dict) else {}
    out = []
    for satir in (r.get("rows") or []):
        if not isinstance(satir, dict):
            continue
        sinif = str(satir.get("sinif") or "")
        anahtar = KITAP_SINIF.get(sinif)
        neden, _ = neden_oku(satir)
        out.append(_satir("kitap", str(satir.get("ad") or "?"),
                          PANO_KELIME[anahtar] if anahtar else PANO_KELIME["dedektor:olculemedi"],
                          KITAP_HUKUM.get(sinif), neden=neden or sinif or None,
                          beyan=str(satir.get(BEYAN_KANONIK) or neden or ""),
                          kaynak_alan="kitap_damga.rows.sinif",
                          olculemedi=(anahtar is None)))
    return out


def kilit_satirlari(hud, heartbeat) -> list[dict]:
    """Üç durdurma kolu (§9.1). TERS İŞARET: kolun NORMAL konumu KAPALIdır ve `ok=True` odur;
    çekili kol `ok=False`tır. Ölçülemeyen kol "kapalı" sayılmaz (fail-open uydurması olurdu)."""
    h = hud if isinstance(hud, dict) else {}
    hb = heartbeat if isinstance(heartbeat, dict) else {}
    kollar = (("soft_halt", h.get("halted"), "hud.halted"),
              ("halt_learning", h.get("learn_halted"), "hud.learn_halted"),
              ("devre_kesici", hb.get("breaker_tripped"), "heartbeat.breaker_tripped"))
    out = []
    for kimlik, deger, kaynak in kollar:
        if deger is None:
            kelime, ok, olc = PANO_KELIME["dedektor:olculemedi"], None, True
        elif bool(deger):
            kelime, ok, olc = PANO_KELIME["kilit:cekili"], False, False
        else:
            kelime, ok, olc = PANO_KELIME["kilit:kapali"], True, False
        out.append(_satir("kilit", kimlik, kelime, ok, neden=kimlik,
                          beyan=KILIT_BEYAN[kimlik], kaynak_alan=kaynak, olculemedi=olc))
    return out


def mandal_yuzeyi() -> dict:
    """Mandal defterlerinin SERVİS YÜZEYİ (§9.1 T2 sınıfı — bugün hiçbir uç bunu taşımıyordu).

    YALNIZ DOSYA OKUR, HESAP YAPMAZ: /api/diagnostics 300 sn poll'da koşar ve yüzey üç küçük
    `store.read_json`dan ibarettir. Defter YOKSA `None` döner — "0 mandal" DEĞİL: hiç yazılmamış
    defter ile boş defter aynı şey değildir (uydurma yasağı). Okuyucular ADIYLA:
    `api._durum_sozlugu` (satır üretimi) + /api/diagnostics `mandallar` alanı → pano
    `DurumSozlugu.tsx`; çivi `test_durum_sozlugu_aileler_v503`.

    DOSYA ADLARI LİTERAL YAZILIR (sabitten/sözlükten türetilmez): `codelaw.artifact_graph` statik
    bir graftır ve değişkenden gelen adı ÇÖZEMEZ — türetilseydi bu okuma grafikte GÖRÜNMEZ ve üç
    defter "yazılıyor ama okuyucusu yok" sayılmaya devam ederdi. Yani literal ad burada bir üslup
    değil, YASA 6'nın ölçülebilirlik şartıdır: `watchdog_alarmed.json` + `integrity_alarmed.json`
    2026-09-15'te `codelaw.DECLARED_SINKS`ten tam da bu okuma doğduğu için DÜŞTÜ (muafiyet beyanı
    gerçek okuyucuyla değiştirildi).

    İKİ ŞEKİL, İKİ ALAN ADI: imza sözlüğünden türeyen `alarm_mandal` öğelerini `jetonlar`da, ad
    listesi olan defterler `adlar`da taşır. Hangi defterin hangi alanı taşıdığı TEK KAYNAKTA
    yazılıdır (`_MANDAL_OGE_ALANI`) ve `mandal_satirlari` onu oradan okur — iki adı `or` ile
    yedekleyen bir ifade şekil hatasını sessizce yutardı."""
    from . import store

    def _kume(d):
        """Ad listesi defterleri (`watchdog_alarmed` · `integrity_alarmed`) → `{n, adlar}`."""
        if not isinstance(d, (dict, list, tuple, set)):
            return None
        adlar = sorted(str(x) for x in d)
        return {"n": len(adlar), "adlar": adlar}

    ham = store.read_json("alarm_mandal.json", None)
    alarm = None
    if isinstance(ham, dict):
        satirlar = [v for v in ham.values() if isinstance(v, dict)]
        alarm = {"n": len(satirlar),
                 "jetonlar": sorted({str(v.get("token")) for v in satirlar if v.get("token")}),
                 "yeniden_n": sum(1 for v in satirlar if v.get("yeniden")),
                 "ilk_n": sum(1 for v in satirlar if (_sayi(v.get("n")) or 1) <= 1),
                 "bastirilan_n": sum(_sayi(v.get("bastirilan")) or 0 for v in satirlar)}
    return {"alarm_mandal": alarm,
            "watchdog_alarmed": _kume(store.read_json("watchdog_alarmed.json", None)),
            "integrity_alarmed": _kume(store.read_json("integrity_alarmed.json", None)),
            # süreç-içi mandal: defter yok → ölçülemez (beyan `_MANDAL_BEYAN`de)
            "koruma_alarmed": None}


def mandal_satirlari(yuzey) -> list[dict]:
    """Defter başına bir satır (§9.1 dört kelimesi). HÜKÜM ENVANTERDİR, ALARM DEĞİL: `ok`
    mandallı defterde de True kalır — mandallı her durum İLK görüşte zaten alarmlandı ve bu satır
    gürültü-kısma mekanizmasının kendisini ikinci kez kırmızıya boyasaydı, bekçinin kendi
    `alarm_mandal` satırının kaçındığı döngüselliği üretirdi. Defter okunamadıysa ÖLÇÜLEMEDİ."""
    y = yuzey if isinstance(yuzey, dict) else {}
    out = []
    for kimlik in MANDAL_DEFTERLERI:
        d = y.get(kimlik)
        if not isinstance(d, dict):
            out.append(_satir("mandal", kimlik, PANO_KELIME["dedektor:olculemedi"], None,
                              olculemedi=True, beyan=_MANDAL_BEYAN[kimlik],
                              kaynak_alan=f"mandallar.{kimlik}"))
            continue
        n = _sayi(d.get("n")) or 0
        if not n:
            kelime = PANO_KELIME["mandal:dustu"]
        elif d.get("yeniden_n"):
            kelime = PANO_KELIME["mandal:yeniden"]
        elif _sayi(d.get("ilk_n")) == n:
            kelime = PANO_KELIME["mandal:ilk"]
        else:
            kelime = PANO_KELIME["mandal:mandalli"]
        # Öğe listesi defterin BEYAN EDİLMİŞ alanından okunur (`_MANDAL_OGE_ALANI`) — iki şekil
        # AYRI AYRI okunur, "hangisi doluysa" takası yapılmaz. Alan yoksa/şekil bozuksa `neden`
        # None kalır: sayı (`n`) ölçülmüştür ama öğe adları ölçülmemiştir (uydurma yasağı).
        ogeler = d.get(_MANDAL_OGE_ALANI[kimlik])
        neden = (", ".join(str(x) for x in ogeler)[:160] or None) if isinstance(ogeler, list) else None
        out.append(_satir("mandal", kimlik, kelime, True, n=n,
                          beyan=_MANDAL_BEYAN[kimlik], kaynak_alan=f"mandallar.{kimlik}",
                          neden=neden))
    return out


def hermes_satiri(warmup) -> dict:
    """hermes ısınma sprintinin TEK satırı (§9.1).

    SIRA HÜKÜMDÜR: `skip` kodu varsa koşum HİÇ denenmemiştir (meşru bekleme) ve `last_result`
    önceki turun kalıntısıdır — atlama sebebi hükmü belirler. Atlama kodu KANONİK `neden`
    ailesine `isinma:` önekiyle girer; bir KOL ADI DEĞİLDİR (`kol_adi` çağrılmaz — `lock_busy`
    bir durdurma kolu değil, bir kilit meşguliyetidir)."""
    w = warmup if isinstance(warmup, dict) else {}
    skip = w.get("skip")
    son = w.get("last_result")
    if skip:
        return _satir("hermes", "isinma", PANO_KELIME["kadans:askida"], None, askida=True,
                      neden=f"isinma:{skip}", kaynak_alan="mlops.warmup.skip",
                      beyan=f"ısınma sprinti koşmadı — atlama sebebi: {skip}")
    if isinstance(son, str) and son.strip().lower().startswith("error"):
        sinif = son.split(":", 1)[1].strip() if ":" in son else son
        return _satir("hermes", "isinma", PANO_KELIME["dedektor:ihlal"], False, neden=sinif,
                      kaynak_alan="mlops.warmup.last_result",
                      beyan=f"son ısınma koşumu hata ile bitti: {son}")
    if son is None:
        return _satir("hermes", "isinma", PANO_KELIME["dedektor:olculemedi"], None,
                      olculemedi=True, kaynak_alan="mlops.warmup.last_result",
                      beyan="hermes durumu okunamadı — 'koşmadı' DEĞİL, ölçülemedi")
    return _satir("hermes", "isinma", PANO_KELIME["canlilik:ok"], True, neden=str(son),
                  kaynak_alan="mlops.warmup.last_result",
                  beyan=f"ısınma sprinti koştu — son sonuç: {son}")


def intraday_satirlari(skipped) -> list[dict]:
    """Intraday atlama sayaçları (§9.1 yeni ailesi) — anahtar başına sayılı satır.

    HÜKÜM DEĞİL ENVANTER: atlama bir arıza değildir (seans dışı olmak ihlal değildir), bu yüzden
    ölçülmüş satır `ok=True`dur; ölçülmemiş anahtar `n=None` + ÖLÇÜLEMEDİ'dir ve pano onu
    "ÖLÇÜLEMEDİ (0 DEĞİL)" diye basar. 0 ile None arasındaki fark bu ailenin bütün değeridir."""
    s = skipped if isinstance(skipped, dict) else {}
    out = []
    for kimlik in INTRADAY_ATLAMA:
        n = _sayi(s.get(kimlik))
        if n is None:
            out.append(_satir("intraday", kimlik, PANO_KELIME["dedektor:olculemedi"], None,
                              olculemedi=True, kaynak_alan=f"intraday.skipped.{kimlik}",
                              beyan="sayaç ölçülmedi (0 DEĞİL)"))
        else:
            out.append(_satir("intraday", kimlik, PANO_KELIME[f"intraday:{kimlik}"], True, n=n,
                              kaynak_alan=f"intraday.skipped.{kimlik}",
                              beyan=f"{n} karar anı bu sebeple atlandı"))
    return out


def aile_sayimi(satirlar) -> dict[str, int]:
    """Aile → satır sayısı (§9.1 tablosunun canlı karşılığı). Pano grupları buradan sayar ve
    kanıt penceresi (dağıtım sonrası A1 ölçümü) bu sözlüğü okur."""
    out: dict[str, int] = {}
    for s in satirlar or ():
        ad = (s or {}).get("aile")
        if ad:
            out[ad] = out.get(ad, 0) + 1
    return out
