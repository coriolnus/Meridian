"""test_kapsama_sayaci_v206 — `universe_coverage`: ŞU AN ile GEÇMİŞİN AYRILMASI (2026-08-07).

ÖLÇÜLEN ÇELİŞKİ (canlı A1, bütünlük dökümü D5). Dedektör şunu diyordu:

    universe_coverage · ok:false · "165 seans evren kapsaması yetersiz olduğu için ATLANDI
    (son: 2026-07-29 %17) — kaynak yayınlamıyor"

Aynı deftere bakan ölçüm ise şunu söylüyordu:

  * 165 bir SEANS sayısı değil, OLAY sayısıdır. Yerel defter kopyasında (state/events.jsonl,
    27.593 satır) o 165 olay YEDİ ayrık seansa aitti ve **159'u tek seansa** (2026-07-15).
    O 159 satır, scheduler'ın `_rehydrate` düzeltmesinden (2026-07-22) önceki tavan-unutma
    fırtınasıdır: bir sayaç kusurunun kalıntısı, ikinci bir sayaç kusuru tarafından
    "165 seans" diye okunmuştur.
  * Son atlanan seans 2026-07-29 — hükmün verildiği günden DOKUZ gün önce. Aradaki seansların
    ölçülen kapsaması 1,0 · 1,0 · 1,0 · 1,0 · 1,0 · 1,0 · 0,996 (canlı
    `session_deferred_for_coverage` olayları). Yani BUGÜN kapsama sorunu YOK.

SINIF: KALICI KIRMIZI. Depoda tedavisi zaten yazılıydı — `alarm_delivery`, 2026-07-26:
"Kalıcı kırmızı bir dedektör, hiç olmayan bir dedektörle aynıdır: operatör ona bakmayı bırakır."
Reçete: HÜKÜM güncel pencereye bakar, KÜMÜLATİF SAYI ayrı alanda GÖRÜNÜR kalır ve ihlal üretmez.

BU DOSYANIN ÇİVİLEDİĞİ SÖZLEŞMELER
  1. Güncel pencere temizken İHLAL YOK — ama tarihsel sayı GÖRÜNÜR (iyileşme "hiç olmadı"ya
     dönüşmez).
  2. BEKÇİ ZAYIFLAMAZ: güncel pencerede gerçek bir kapsama düşüşü hâlâ ok=False üretir
     (regresyon çivisi — bu düzeltmenin bedeli asla körlük olmamalı).
  3. ÖLÇÜLEMEDİ ≠ 0 ≠ TEMİZ: kanıt yoksa sayılar None ve metin "ÖLÇÜLEMEDİ" der.
  4. Pencere ve eşik KODDA BEYANLI ve motorun kendi sabitlerinden türer (sihirli sayı yok).
  5. OLAY ≠ SEANS: 159 olaylık tek fırtına, seans ekseninde bir (1) seanstır.

HİÇBİR TEST CANLI `state/`E YAZMAZ: hepsi `sandbox_state` fikstürüyle koşar.
"""
from __future__ import annotations

import datetime as dt

from meridian import store, watchdog as wd


def _simdi(gun_once: int = 0) -> str:
    return (dt.datetime.now(dt.timezone.utc)
            - dt.timedelta(days=gun_once)).isoformat(timespec="seconds")


def _ev(event: str, ts: str | None = None, **f) -> None:
    store.append_jsonl("events.jsonl", {"ts": ts or _simdi(), "level": "warn",
                                        "event": event, **f})


def _satir(rep=None) -> dict:
    rep = rep if rep is not None else wd.parity_report()
    return next(r for r in rep["rows"] if r["check"] == "universe_coverage")


def _saglikli_seanslar(seanslar, kapsama: float = 1.0) -> None:
    """Motorun o seansta TAM kapsamayla çalıştığının kanıtı (canlıdaki imzanın aynısı)."""
    for s in seanslar:
        _ev("session_deferred_for_coverage", index_session=s, chosen=s, coverage=kapsama)


# =================================================================================================
# 1) İYİLEŞMİŞ DURUM KALICI İHLAL GİBİ GÖRÜNMEZ — ama tarih de silinmez
# =================================================================================================
def test_gecmis_firtina_guncel_pencere_temizken_IHLAL_URETMEZ(sandbox_state):
    """Canlı vakanın birebir kurulumu: eski bir atlama fırtınası + ondan SONRA gelen sağlıklı
    seanslar. Eski hüküm `not skipped` idi ve 30 günlük okuma penceresi boyunca kırmızı kalıyordu.
    Yeni hüküm yalnız son N SEANSA bakar; fırtına pencerenin dışına düşer."""
    _ev("session_bar_never_published", ts=_simdi(9), session="2026-07-29",
        universe_coverage=0.172, required=0.9)
    _saglikli_seanslar(["2026-07-30", "2026-07-31", "2026-08-03", "2026-08-04",
                        "2026-08-05", "2026-08-06"])
    r = _satir()
    assert r["ok"] is True, f"iyileşmiş durum hâlâ ihlal üretiyor — kalıcı kırmızı sürüyor: {r}"
    assert r["guncel_ihlal_seans"] == 0
    # DÜRÜSTLÜK: iyileşme "hiç olmadı"ya dönüşmedi — tarih hâlâ satırda.
    assert r["tarihsel_ihlal_seans"] == 1 and r["tarihsel_son_seans"] == "2026-07-29", r
    assert "2026-07-29" in r["detail"] and "TARİHSEL" in r["detail"], \
        f"geçmiş görünmez oldu — iyileşme 'hiç olmadı'ya çevrildi: {r['detail']}"


def test_olay_sayisi_SEANS_sayisi_diye_okunmaz(sandbox_state):
    """Kusurun ikinci yarısı: 165 olay "165 seans" diye yazılıyordu. Canlıda 159 olay TEK seansa
    (2026-07-15) aitti. Seans ekseninde bu bir (1) seanstır ve metin bunu böyle söylemelidir."""
    for _ in range(159):
        _ev("session_bar_never_published", ts=_simdi(20), session="2026-07-15",
            universe_coverage=0.18, required=0.9)
    _saglikli_seanslar(["2026-08-03", "2026-08-04", "2026-08-05", "2026-08-06", "2026-08-07"])
    r = _satir()
    assert r["tarihsel_ihlal_seans"] == 1, f"159 olay hâlâ 159 seans sayılıyor: {r}"
    assert r["tarihsel_ihlal_olay"] == 159, r
    assert "1 ayrık seans / 159 alarm satırı" in r["detail"], r["detail"]
    assert r["ok"] is True


# =================================================================================================
# 2) REGRESYON ÇİVİSİ — bekçi ZAYIFLATILMADI
# =================================================================================================
def test_guncel_pencerede_GERCEK_dusus_hala_ihlal_uretir(sandbox_state):
    """Bu düzeltmenin bedeli asla körlük olmamalı: son N seansın içindeki bir atlama kırmızıdır."""
    _saglikli_seanslar(["2026-08-03", "2026-08-04", "2026-08-05"])
    _ev("session_bar_never_published", session="2026-08-06",
        universe_coverage=0.17, required=0.9)
    r = _satir()
    assert r["ok"] is False, f"güncel pencerede atlama var ama bekçi susuyor — ZAYIFLADI: {r}"
    assert "ATLANDI" in r["detail"] and "2026-08-06" in r["detail"], r["detail"]
    assert r["guncel_ihlal_seans"] == 1 and r["tarihsel_ihlal_seans"] == 1, r


def test_guncel_pencerede_kapsama_dususu_universe_coverage_low_ile_de_ihlaldir(sandbox_state):
    """İkinci ihlal imzası: motor hiçbir yakın seansta yeterli kapsama bulamadığında."""
    _saglikli_seanslar(["2026-08-04", "2026-08-05"])
    _ev("universe_coverage_low", date="2026-08-06", coverage=0.18, min_required=0.9)
    r = _satir()
    assert r["ok"] is False and "%18" in r["detail"], r


def test_alarma_yukseltilmis_imza_kind_alanindan_da_SAYILIR(sandbox_state):
    """İmza kayması tuzağı (K1 dersi): `_declare_terminal_skip` olayı DATA_QUALITY alarmı olarak
    yayınlar ve makine-okunur adı `kind` alanında taşır. Yalnız `event` adına bakan bir süzgeç
    yeni satırlara kör olurdu."""
    _saglikli_seanslar(["2026-08-04", "2026-08-05"])
    store.append_jsonl("events.jsonl", {
        "ts": _simdi(), "level": "alarm", "event": "DATA_QUALITY SEANS ATLANDI: 2026-08-06",
        "alarm": "DATA_QUALITY", "kind": "session_bar_never_published",
        "session": "2026-08-06", "universe_coverage": 0.18, "required": 0.9})
    r = _satir()
    assert r["ok"] is False, f"yükseltilmiş imza sayılmıyor — dedektör yeni olaylara kör: {r}"


def test_seans_kimligi_TASIMAYAN_ihlal_GUNCEL_sayilir(sandbox_state):
    """Tarihlendiremediğimiz bir ihlali "geçmiş" saymak, ölçemediğimiz şeyi kendi lehimize
    yorumlamak olurdu — pencere mekanizması bir kaçış yoluna dönüşemez."""
    _saglikli_seanslar(["2026-08-03", "2026-08-04", "2026-08-05", "2026-08-06", "2026-08-07"])
    _ev("session_bar_never_published", universe_coverage=0.18)      # `session` YOK
    r = _satir()
    assert r["ok"] is False, f"seans kimliği olmayan ihlal sessizce geçmişe atıldı: {r}"
    assert "seans kimliği YOK" in r["detail"], r["detail"]


# =================================================================================================
# 3) ÖLÇÜLEMEDİ ≠ 0 ≠ TEMİZ
# =================================================================================================
def test_kanit_yoksa_OLCULEMEDI_denir_temiz_denmez(sandbox_state):
    """Boş defterde eski metin "işlenen seanslar tam evreni gördü" diyordu — kanıtsız bir iddia.
    Sayılar 0 değil None döner: ölçülemeyen bir şeyi sıfır yazmak UYDURMA YASAĞInın ihlalidir."""
    r = _satir()
    assert r["olculemedi"] is True, r
    assert r["guncel_ihlal_seans"] is None and r["tarihsel_ihlal_seans"] is None, \
        f"ölçülemeyen sayı 0 diye yazılmış: {r}"
    assert "ÖLÇÜLEMEDİ" in r["detail"], r["detail"]
    assert "tam evreni gördü" not in r["detail"], \
        f"kanıtsız TEMİZLİK iddiası hâlâ kuruluyor: {r['detail']}"
    # Kurt masalı yasağı: ölçüm YOKLUĞU tek başına ihlal ilan edilmez (taze kurulum / mutasyon
    # temeli). Hüküm "ihlal yok" değil, "hüküm verilemedi"dir ve metin bunu söyler.
    assert r["ok"] is True, r


def test_ayristirilamayan_kapsama_olcusu_UYDURULMAZ(sandbox_state):
    """Ölçü alanı bozuksa metin sayı uydurmaz (eski kod `float(... or 0)` ile %0 yazıyordu —
    ölçülemeyen bir kapsamayı 'sıfır kapsama' diye raporlamak)."""
    _saglikli_seanslar(["2026-08-04", "2026-08-05"])
    _ev("session_bar_never_published", session="2026-08-06", universe_coverage="bozuk")
    r = _satir()
    assert r["ok"] is False and "%0" not in r["detail"], r["detail"]
    assert r.get("son_olculen_kapsama") in (None, 1.0), r


# =================================================================================================
# 4) EŞİK ve PENCERE KODDA BEYANLI — ve motorun kendi yasasından türer
# =================================================================================================
def test_pencere_ve_esik_motorun_sabitlerinden_OKUNUR(sandbox_state):
    """Sihirli sayı yasağı: bekçi kendi eşiğini icat edemez. Pencere motorun kovalama ufkudur
    (`loop.UNIVERSE_LAG_MAX_D`), eşik motorun kapsama yasasıdır (`loop.UNIVERSE_MIN_COVERAGE`) —
    scheduler.py:890'daki "tek yasa, tek ölçüm" ile aynı gerekçe."""
    from meridian import loop

    pencere, esik = wd._kapsama_penceresi()
    assert pencere == loop.UNIVERSE_LAG_MAX_D, \
        "hüküm penceresi motorun kovalama ufkundan KOPMUŞ — iki yasa, iki ölçüm"
    assert esik == loop.UNIVERSE_MIN_COVERAGE, \
        "bekçinin eşiği motorunkinden KOPMUŞ — kapı≠canlı ayrışmasının bekçi hâli"
    _saglikli_seanslar(["2026-08-05", "2026-08-06"])
    r = _satir()
    assert r["pencere_seans"] == pencere and r["kapsama_esigi"] == esik, r
    assert f"son {pencere} seans" in r["detail"], r["detail"]


def test_motor_sabitleri_okunamazsa_SESSIZ_kalinmaz(sandbox_state, monkeypatch):
    """YASA 4: penceresini ölçemeyen bir bekçi, sessizce başka bir yasaya göre hüküm verirdi.
    Kurgu: motorun sabiti okunabiliyor ama SAYIYA çevrilemiyor (yeniden adlandırma/bozulma)."""
    from meridian import loop

    monkeypatch.setattr(loop, "UNIVERSE_LAG_MAX_D", "beş")
    pencere, esik = wd._kapsama_penceresi()
    assert (pencere, esik) == (wd.KAPSAMA_PENCERE_SEANS, wd.KAPSAMA_ESIK)
    olaylar = [e for e in store.read_jsonl("events.jsonl")
               if e.get("event") == "kapsama_penceresi_okunamadi"]
    assert olaylar, "motor sabitleri okunamadı ve bekçi bunu HİÇ söylemedi (sessiz-yutma)"


# =================================================================================================
# 5) "KAYNAK YAYINLAMIYOR" İDDİASI ÖLÇÜMDEN TÜRER
# =================================================================================================
def test_kaynak_yayinlamiyor_iddiasi_olcumsuz_KURULMAZ(sandbox_state):
    """Eski metin bu cümleyi KOŞULSUZ yazıyordu: pencere temiz olsa, kaynak dün de bugün de
    yayınlasa, cümle orada duruyordu. İddia artık yalnız GÜNCEL penceredeki atlamadan doğar."""
    _saglikli_seanslar(["2026-08-03", "2026-08-04", "2026-08-05", "2026-08-06", "2026-08-07"])
    _ev("session_bar_never_published", ts=_simdi(15), session="2026-07-15",
        universe_coverage=0.18)
    r = _satir()
    assert r["ok"] is True
    assert "yayınlamadı" not in r["detail"], \
        f"kaynak bugün yayınlıyor ama satır hâlâ 'yayınlamıyor' diyor: {r['detail']}"
    assert "kaynak YAYINLIYOR" in r["detail"] and "%100" in r["detail"], r["detail"]
