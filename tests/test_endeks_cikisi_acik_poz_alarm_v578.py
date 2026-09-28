"""v578 — TSK-207 (b): AÇIK POZİSYONLU ENDEKS ÇIKIŞI OPERATÖRE ULAŞIR (2026-09-28).

OPERATÖR KARARI (2026-09-28, AskUserQuestion): açık pozisyonlu bir sembol S&P 500'den çıkarsa
(beyanlı endeks çıkışı) sistem pozisyona, bar çekimine ve evrene DOKUNMAZ; operatöre HABER
VERİR, kararı operatör verir ("sadece uyar, kararı ben veririm").

ÖLÇÜLEN BOŞLUK (Rol-1): TSK-207 (a) bu kesişimi günde bir kez
`obs.warn("SEMBOL_ENDEKS_CIKISI_ACIK_POZISYON", ...)` ile yazıyordu — ama `warn` bir ALARM
değildir (`obs.warn` docstring'i: "bildirim zincirini tetiklemez"), jeton `NOTIFY_TOKENS`ta
yoktu, bekçi/brifing/Telegram yolunda geçmiyordu. Yani kayıt vardı, operatöre ULAŞMIYORDU.

SÖZLEŞME (bu dosya çiviler):
  * Kesişim ≠ ∅ → `obs.ALARM_ENDEKS_CIKISI_ACIK_POZISYON` jetonuyla günde EN ÇOK BİR alarm
    (aynı gün ikinci çağrı yeni alarm ÜRETMEZ; bastırılan tekrar defterde SAYILIR — YASA 6).
  * Kesişim = ∅ → alarm YOK. Kesişim ÖLÇÜLEMEZ (defter yok / `positions` yok) → alarm YOK,
    `acik_pozisyon_neden` KORUNUR (UYDURMA YASAĞI — ölçülemeyen kesişim "var" sayılmaz).
  * Mesaj sade Türkçe: sembol, pozisyon (adet/yön — okunamazsa `None` + neden), "bar akışı
    durdu, stop/çıkış bu sembolde fiyatsız kalabilir" ve İKİ karar seçeneği ("veri çekmeye
    devam" / "zorla kapat"). Sistem kendisi hiçbir şey yapmaz.
  * TEK KAYIT: eski `SEMBOL_ENDEKS_CIKISI_ACIK_POZISYON` warn'ı alarmla BİRLEŞTİ — aynı olgu
    için iki satır yok.
  * Jeton `NOTIFY_TOKENS`ta (türetme, v98) ve alarm UÇTAN UCA kanala gider (`notify.send`).
  * DAVRANIŞ DEĞİŞMEDİ: pozisyon defteri, bar arşivi ve evren kümeleri çağrıdan sonra AYNI;
    bar çekimi (`data.load_bars`) HİÇ çağrılmaz.

Fikstür/yardımcılar v416 + v525 + v414'ten İTHAL EDİLİR (tek-kaynak yasası: sentetik evren ve
beyanlı-küme düzeneği KOPYALANMAZ — `_beyanli_kur`un üçlü yama TUZAĞI v525 docstring'inde).
`monkeypatch.undo()` YASAK (autouse fikstürleri de geri alır).
"""
from __future__ import annotations

import hashlib

from meridian import config, obs, store, watchdog
from tests.test_olu_isim_adayi_v416 import (  # noqa: F401 — fikstür ithali pytest'e görünürlük içindir
    _arsiv_yaz,
    _bugun_ayarla,
    evren,
    takvim,
    warnlar,
)
from tests.test_olu_isim_endeks_cikisi_v525 import (  # noqa: F401 — fikstür ithali pytest'e görünürlük içindir
    CIKIS_BEYAN,
    _beyanli_kur,
    loglar,
)
from tests.test_veri_disk_esigi_v414 import alarmlar  # noqa: F401 — fikstür ithali pytest'e görünürlük içindir

JETON = "ENDEKS_CIKISI_ACIK_POZISYON"
ESKI_WARN_ADI = "SEMBOL_ENDEKS_CIKISI_ACIK_POZISYON"


def _sahne(monkeypatch, positions: dict | None) -> None:
    """Tek beyanlı çıkış (CIK, 8 seans geride) + pozisyonsuz ikinci çıkış (CIK2). `positions`
    None ise `portfolio.json` HİÇ yazılmaz (ölçülemez dal)."""
    from meridian.adapters import data
    _beyanli_kur(monkeypatch, {"CIK": CIKIS_BEYAN, "CIK2": CIKIS_BEYAN})
    monkeypatch.setattr(data, "LIVE_UNIVERSE", [])
    monkeypatch.setattr(data, "REPLAY_UNIVERSE", [])
    _arsiv_yaz("CIK", "2026-08-20")
    _arsiv_yaz("CIK2", "2026-08-20")
    if positions is not None:
        store.write_json("portfolio.json", {"last_date": "2026-09-01", "positions": positions})
    _bugun_ayarla(monkeypatch, "2026-09-01")


def _bu_alarm(alarmlar: list[dict]) -> list[dict]:
    return [a for a in alarmlar if a["token"] == JETON]


# ---- (1) kesişim var → alarm BİR kez; aynı gün ikinci çağrıda YOK ---------------------------

def test_kesisim_varken_alarm_gunde_bir_kez(takvim, monkeypatch, alarmlar, warnlar, loglar):
    _sahne(monkeypatch, {"CIK": {"qty": 10, "side": "long"}, "BASKA": {"qty": 3, "side": "long"}})

    rep = watchdog.check_olu_isim_and_alarm()

    assert rep["acik_pozisyon_kesisim"] == ["CIK"] and rep["acik_pozisyon_neden"] is None
    assert obs.ALARM_ENDEKS_CIKISI_ACIK_POZISYON == JETON
    bu = _bu_alarm(alarmlar)
    assert len(bu) == 1, "kesişim ALARM sınıfıdır (TSK-207 (b), operatör kararı 2026-09-28)"
    assert bu[0]["semboller"] == ["CIK"], "yalnız KESİŞEN sembol — CIK2 pozisyonsuz"
    assert "BASKA" not in str(bu[0]), "pozisyon defterinin tamamı satıra dökülmez"
    assert ESKI_WARN_ADI not in [w["event"] for w in warnlar], \
        "TEK KAYIT: eski warn alarmla birleşti — aynı olgu için iki satır YOK"

    watchdog.check_olu_isim_and_alarm()        # AYNI gün — mandal

    assert len(_bu_alarm(alarmlar)) == 1, "günlük mandal: aynı gün İKİNCİ alarm ÜRETİLMEZ"
    satir = store.read_json(watchdog.ALARM_GUNLUK_FILE, {})["mekanizmalar"][
        watchdog._OLU_ISIM_ENDEKS_POZ_MEK_ADI]
    assert satir["alarm"] == 1 and satir["bastirilan"] == 1, \
        "bastırılan tekrar SESSİZ DEĞİL, defterde SAYILIR (YASA 6)"
    assert satir["son_semboller"] == ["CIK"]


# ---- (2) kesişim yok → alarm YOK ---------------------------------------------------------------

def test_kesisim_yokken_alarm_yok(takvim, monkeypatch, alarmlar, warnlar, loglar):
    """POZİTİF KONTROL: (1) ile TEK farkı pozisyon defterinin içeriği. Bu test olmasaydı "her
    beyanlı çıkışta alarm basan" bir uygulama da (1)'i geçerdi."""
    _sahne(monkeypatch, {"BASKA": {"qty": 3, "side": "long"}})

    rep = watchdog.check_olu_isim_and_alarm()

    assert rep["acik_pozisyon_kesisim"] == [] and rep["acik_pozisyon_neden"] is None
    assert _bu_alarm(alarmlar) == [], "kesişim boşken alarm ÜRETİLMEZ"
    assert [g["event"] for g in loglar] == ["SEMBOL_ENDEKS_CIKISI"], \
        "beyanlı çıkışın BİLGİ satırı yerinde kalır (TSK-207 (a) davranışı)"


# ---- (3) kesişim ÖLÇÜLEMEZ → alarm YOK + neden korunur ----------------------------------------

def test_kesisim_olculemezse_alarm_yok_neden_korunur(takvim, monkeypatch, alarmlar, warnlar, loglar):
    """UYDURMA YASAĞI: defter yokken "kesişim var" ya da "yok" DENMEZ. Bugünkü davranış
    (hükümsüzlük BİLGİ satırında `acik_pozisyon_neden` alanıyla görünür) KORUNUR."""
    _sahne(monkeypatch, None)                  # portfolio.json HİÇ yazılmadı

    rep = watchdog.check_olu_isim_and_alarm()

    assert rep["acik_pozisyon_kesisim"] is None, "ölçülemeyen kesişim SIFIR DEĞİLDİR"
    assert rep["acik_pozisyon_neden"], "UYDURMA YASAĞI: neden BOŞ olamaz"
    assert alarmlar == [], "ölçülemeyen kesişim alarm ÜRETMEZ"
    cikis = [g for g in loglar if g["event"] == "SEMBOL_ENDEKS_CIKISI"]
    assert len(cikis) == 1
    assert cikis[0]["acik_pozisyon_neden"] == rep["acik_pozisyon_neden"], \
        "hükümsüzlük SESSİZ GEÇMEZ: bilgi satırı nedeni taşır"


# ---- (4) mesaj: sembol + pozisyon + risk cümlesi + İKİ seçenek -------------------------------

def test_mesaj_sembol_pozisyon_ve_secenekleri_tasir(takvim, monkeypatch, alarmlar, warnlar, loglar):
    _sahne(monkeypatch, {"CIK": {"qty": 10, "side": "long"}})

    watchdog.check_olu_isim_and_alarm()

    a = _bu_alarm(alarmlar)[0]
    m = a["message"]
    assert "CIK" in m and "10 adet" in m and "long" in m, "sembol + adet + yön mesajda"
    assert "S&P 500" in m
    assert "bar akışı durdu" in m and "fiyatsız" in m, \
        "risk cümlesi: bar akışı durdu, stop/çıkış bu sembolde fiyatsız kalabilir"
    assert "veri çekmeye devam" in m and "zorla kapat" in m, "iki karar seçeneği ADIYLA"
    assert "hiçbir şey yapmaz" in m.lower(), "sistem kendisi eylem YAPMAZ — karar operatörün"
    assert a["secenekler"] == ["veri çekmeye devam", "zorla kapat"]
    # AYRIŞMA ÇİVİSİ: mesaj şablonu çağrı yerinde LİTERAL durur (RUNBOOK onu gösterir); seçenek
    # sabiti ile metin sessizce ayrışmasın — sabitteki her seçenek mesajda ADIYLA geçmeli.
    assert all(s in m for s in watchdog.ENDEKS_CIKISI_SECENEKLERI)
    assert a["pozisyonlar"] == {"CIK": {"adet": 10, "yon": "long", "neden": None}}
    assert a["beyanlar"] == {"CIK": CIKIS_BEYAN}, "gerekçe metni sözlükten TAŞINIR (tek kaynak)"


# ---- (5) pozisyon alanları okunamazsa: None + neden (uydurma YOK) ------------------------------

def test_pozisyon_alanlari_okunamazsa_none_ve_neden(takvim, monkeypatch, alarmlar, warnlar, loglar):
    """Kesişim ÖLÇÜLDÜ (sembol defterde) ama kaydın `qty`/`side` alanı yok: alarm YİNE atılır
    (risk gerçek), adet/yön UYDURULMAZ — `None` + neden. `.get` None ≠ anahtar yok: neden,
    alanın YOKLUĞUNU adıyla söyler."""
    _sahne(monkeypatch, {"CIK": {"entry": 5.0}})

    watchdog.check_olu_isim_and_alarm()

    bu = _bu_alarm(alarmlar)
    assert len(bu) == 1, "kesişim ölçüldü — adet/yön okunamasa da alarm atılır"
    poz = bu[0]["pozisyonlar"]["CIK"]
    assert poz["adet"] is None and poz["yon"] is None, "UYDURMA YASAĞI: değer yoksa None"
    assert poz["neden"] and "qty" in poz["neden"] and "side" in poz["neden"], \
        "neden hangi alanın OLMADIĞINI adıyla söyler"
    assert "okunamadı" in bu[0]["message"], "mesaj eksik değeri SESSİZCE atlamaz"


# ---- (6) jeton NOTIFY_TOKENS'ta (türetme) -------------------------------------------------------

def test_jeton_notify_tokens_icinde():
    assert obs.ALARM_ENDEKS_CIKISI_ACIK_POZISYON == JETON
    assert JETON in obs.NOTIFY_TOKENS, "jeton bildirim kapsamında DEĞİL — operatöre ulaşmaz"


# ---- (7) uçtan uca: alarm kanala GİDER, gelen kutusunda GÖRÜNÜR, tek kayıt -------------------

def test_alarm_operatore_ulasir_uctan_uca(takvim, monkeypatch):
    """`obs.alarm` YAMANMAZ: gerçek zincir koşar — `_maybe_notify` jetonu `NOTIFY_TOKENS`
    kapısından geçirir, `notify.send` çağrılır, `notify.inbox` alarmı gösterir. Eski warn
    yolu burada kırmızıydı: kayıt `level=warn` idi ve iki kapıya da hiç ulaşmıyordu."""
    from meridian import notify
    giden: list[str] = []
    monkeypatch.setattr(notify, "configured", lambda: True)
    monkeypatch.setattr(notify, "send", lambda t: giden.append(t) or True)
    _sahne(monkeypatch, {"CIK": {"qty": 10, "side": "long"}})

    watchdog.check_olu_isim_and_alarm()

    assert len(giden) == 1, "alarm kanala TEK mesaj olarak gitmeli"
    assert JETON in giden[0] and "CIK" in giden[0] and "zorla kapat" in giden[0]
    kutu = notify.inbox()
    assert any(g["token"] == JETON for g in kutu["groups"]), "gelen kutusunda GÖRÜNMELİ"
    olaylar = store.read_jsonl("events.jsonl")
    assert len([e for e in olaylar if e.get("alarm") == JETON]) == 1
    assert not [e for e in olaylar if e.get("event") == ESKI_WARN_ADI], \
        "TEK KAYIT: eski warn satırı artık yazılmaz"


# ---- (8) DAVRANIŞ DEĞİŞMEDİ: pozisyon / bar / evren dokunulmadı -------------------------------

def _durum_ozeti() -> dict[str, str]:
    kok = config.STATE
    return {str(p.relative_to(kok)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(kok.rglob("*")) if p.is_file()}


def test_pozisyon_bar_evren_dokunulmadi(takvim, monkeypatch):
    """Operatör kararı "sadece uyar": alarm yolu HİÇBİR karar yüzeyine yazmaz. Çağrı öncesi/
    sonrası `state/` özeti kıyaslanır — değişebilecek dosyalar YALNIZ gözlem defterleridir
    (günlük mandal, olay defteri, teslim sayaçları). Evren kümeleri aynı kalır, bar çekimi
    (`data.load_bars`) hiç çağrılmaz."""
    from meridian.adapters import data
    cagri: list[tuple] = []
    monkeypatch.setattr(data, "load_bars", lambda *a, **k: cagri.append(a) or None)
    _sahne(monkeypatch, {"CIK": {"qty": 10, "side": "long"}})
    evren_once = {ad: repr(sorted(getattr(data, ad))) for ad in (
        "LIVE_UNIVERSE", "REPLAY_UNIVERSE", "RETIRED_SYMBOLS", "ENDEKS_CIKISI_BEYANLI",
        "EVREN_DISI_BEYANLI")}
    once = _durum_ozeti()

    watchdog.check_olu_isim_and_alarm()

    sonra = _durum_ozeti()
    # `store` kilitli yazımı `.locks/<ad>.lock` bırakır — kilidin kendisi yazılan dosyanın
    # İZİDİR, ayrı bir yüzey değil; o dosyanın adına indirgenir (izin kümesi GENİŞLEMEZ).
    degisen = {k.removeprefix(".locks/").removesuffix(".lock")
               for k in set(once) | set(sonra) if once.get(k) != sonra.get(k)}
    izinli = {watchdog.ALARM_GUNLUK_FILE, "events.jsonl", "notify_undelivered.json",
              "notify_sent.json"}
    assert degisen <= izinli, f"alarm yolu gözlem dışı bir dosyaya yazdı: {sorted(degisen - izinli)}"
    assert "portfolio.json" not in degisen and not any(k.startswith("bars") for k in degisen)
    assert cagri == [], "bar çekimi TETİKLENMEMELİ — sensör yalnız diskteki arşivi okur"
    for ad, deger in evren_once.items():
        assert repr(sorted(getattr(data, ad))) == deger, f"evren kümesi değişti: {ad}"
