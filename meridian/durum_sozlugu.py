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
watchdog'a gömülseydi kanonik küme 3400+ satırlık dosyaya çivilenirdi. Bu dosya BİLEREK hiçbir
meridian modülünü import etmez — döngüsel import riski sıfır, testte tek başına yüklenebilir.

SAYAÇ REJİMİ SÜREÇ-İÇİDİR (bekçi süreç-içi mandallarının beyanlı kararıyla aynı gerekçe,
watchdog.py :2657 civarı): diske yazmak `artifact_unread` yüzeyi doğururdu ve canlı worker
koşarken state'e yazma yasağıyla çelişirdi. Kabul edilen bedel: restart sayaçları sıfırlar —
"eski ad hâlâ okunuyor" hükmü için TEK artış yeter, sıfırlanma o hükmü çürütmez.
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
# hermes `last_result="learning_halted"` değerinin ÜRETİCİDE kanonikleştirilmesi Açık Soru A3
# (operatör kararı) — o karara dek pano okuyucu tarafında çevirir (app.js `f8KolAd`).
KOL_KANONIK = {
    "soft_halt": ("HALT", "halted", "HALT_ACTIVE", "meridian_halted", "halt"),
    "halt_learning": ("LEARN_HALT", "learn_halted", "learning_halted"),
}
_KOL_TERS = {eski: kanonik for kanonik, eskiler in KOL_KANONIK.items() for eski in eskiler}

# ---- EŞANLAMLI-OKUMA SAYAÇLARI (ölüm tarihi ölçümü) -----------------------------------------
# Anahtar biçimi "<sinif>:<eski_ad>" (örn. "hukum:failed", "neden:detail", "kol:learning_halted",
# "sayac:ok").
# Süreç-içi (gerekçe modül başlığında). Dış okuyucu: api._durum_sozlugu → /api/diagnostics →
# app.js `f8SozlukSatiri` (YASA 6 — sayacın kendisi okuyucusuz kalamaz).
_ESANLAMLI_OKUMA: dict[str, int] = {}


def _say(anahtar: str) -> None:
    _ESANLAMLI_OKUMA[anahtar] = _ESANLAMLI_OKUMA.get(anahtar, 0) + 1


def esanlamli_okumalar() -> dict[str, int]:
    """Sayaçların KOPYASI — dış okuyucu iç sözlüğü mutasyona uğratamaz."""
    return dict(_ESANLAMLI_OKUMA)


def _sifirla_test_icin() -> None:
    """YALNIZ TEST hijyeni (v271): testler arası sayaç sızıntısını keser. Üretim yolunda
    ÇAĞRILMAZ — canlıda sayaç sıfırlamak, ölçmeye çalıştığımız ölüm tarihini silmek olurdu."""
    _ESANLAMLI_OKUMA.clear()


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
