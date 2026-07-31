"""test_alarm_delivery_v71.py — ALARM YAZILDI ≠ ALARM ULAŞTI (2026-07-22).

`hermes doctor` çıktısındaki uyarıları tararken bulundu ve doctor'ın kendisiyle ilgisi yoktu:
canlı defterde **23 `MECHANISM_STALE` alarmı** vardı, `notify.configured()` False'tu (Telegram
token'ı yok, webhook yok) ve `obs._maybe_notify` bu durumda **sessizce `return`** ediyordu.

Yani bütün gün kurulan dedektörler alarm üretiyor, alarm kanalı bağlı değil, ve bu boşluk hiçbir
yerde görünmüyordu. Günün baskın hata deseninin en dış katmandaki hâli: **üretilen kanıt
tüketilmiyor** — burada "tüketici" operatörün kendisi.

Susturmak yerine SAYIYORUZ: kanal yokken log'a ikinci bir satır basmak yalnız gürültü olurdu
(alarm zaten deftere yazıldı). Sayaç makullük dedektöründe tek satır olarak görünür.
"""
from __future__ import annotations

import pytest

from meridian import notify, obs, store, watchdog as wd


def _row(name: str):
    return next((r for r in wd.parity_report()["rows"] if r["check"] == name), None)


def test_undelivered_alarms_are_counted(sandbox_state, monkeypatch):
    """CANLI OLAY: kanal yok → alarm hiçbir yere gitmiyor. Artık sayılıyor."""
    monkeypatch.setattr(notify, "configured", lambda: False)
    obs.alarm("MECHANISM_STALE", "mekanizma gecikti")
    obs.alarm("DATA_QUALITY", "veri kapısı")
    obs.alarm("MECHANISM_STALE", "ikinci kez")
    d = store.read_json("notify_undelivered.json", {})
    assert d["_toplam"] == 3 and d["MECHANISM_STALE"] == 2 and d["DATA_QUALITY"] == 1


def test_the_gap_is_surfaced_by_the_detector(sandbox_state, monkeypatch):
    """Sayılıp gösterilmezse yine 'üretilip tüketilmeyen kanıt' olurdu."""
    monkeypatch.setattr(notify, "configured", lambda: False)
    obs.alarm("MECHANISM_STALE", "x")
    r = _row("alarm_delivery")
    assert r and r["ok"] is False
    assert "TESLİM EDİLEMEDİ" in r["detail"] and "kimse duymuyor" in r["detail"]


def test_a_configured_channel_produces_no_violation(sandbox_state, monkeypatch):
    """KURT MASALI YASAĞI: kanal varken bu satır HİÇ çıkmamalı."""
    monkeypatch.setattr(notify, "configured", lambda: True)
    monkeypatch.setattr(notify, "send", lambda msg: True)
    obs.alarm("MECHANISM_STALE", "x")
    assert store.read_json("notify_undelivered.json", {}) == {}
    assert _row("alarm_delivery") is None


def test_non_notifying_tokens_are_not_counted(sandbox_state, monkeypatch):
    """Bildirim beyaz-listesinde OLMAYAN bir alarm zaten telefona gitmez — onu 'teslim edilemedi'
    diye saymak sayacı şişirir ve dedektörü değersizleştirir."""
    monkeypatch.setattr(notify, "configured", lambda: False)
    obs.alarm("BİLİNMEYEN_TOKEN", "beyaz-listede değil")
    assert store.read_json("notify_undelivered.json", {}) == {}


def test_the_alarm_itself_is_still_written(sandbox_state, monkeypatch):
    """Sayaç bir YAN kayıttır: alarmın deftere yazılmasını hiçbir koşulda engelleyemez."""
    monkeypatch.setattr(notify, "configured", lambda: False)
    obs.alarm("MECHANISM_STALE", "kritik")
    blob = "".join(str(e) for e in store.read_jsonl("events.jsonl"))
    assert "MECHANISM_STALE" in blob and "kritik" in blob


def test_counter_failure_never_drops_the_alarm(sandbox_state, monkeypatch):
    """Sayaç yazılamasa bile alarm yazılmalı — yan kayıt asıl kaydı düşüremez."""
    monkeypatch.setattr(notify, "configured", lambda: False)
    monkeypatch.setattr(store, "update_json",
                        lambda *a, **k: (_ for _ in ()).throw(OSError("disk dolu")))
    obs.alarm("MECHANISM_STALE", "sayaç bozukken")
    blob = "".join(str(e) for e in store.read_jsonl("events.jsonl"))
    assert "sayaç bozukken" in blob


def test_the_local_inbox_keeps_alarms_that_no_channel_delivered(sandbox_state, monkeypatch):
    """SAYILMAK YETMEZ (2026-07-26): sayaç 46'ya çıkmıştı ve İÇERİĞİ hiçbir yerde yoktu — hangi
    mekanizmanın kaç kez bağırdığı görünmüyordu. Gelen kutusu kaynağı KOPYALAMAZ, `events.jsonl`
    üzerinden görünüm kurar."""
    monkeypatch.setattr(notify, "configured", lambda: False)
    obs.alarm("MECHANISM_STALE", "mekanizma ÜRETMİYOR: fmp_source", mechanism="fmp_source")
    obs.alarm("MECHANISM_STALE", "mekanizma ÜRETMİYOR: fmp_source", mechanism="fmp_source")
    obs.alarm("DATA_QUALITY", "bar mutasyonu", kind="determinism")

    box = notify.inbox()
    assert box["pending"] == 3 and box["channel_configured"] is False
    sigs = {g["token"]: g["n"] for g in box["groups"]}
    assert sigs["MECHANISM_STALE"] == 2, "aynı mekanizmanın tekrarı tek satırda toplanmalı"
    assert sigs["DATA_QUALITY"] == 1


def test_ack_advances_the_boundary_without_deleting_any_alarm(sandbox_state, monkeypatch):
    """ACK bir OKUMA işaretidir, bir silme değil. Alarmın kendisi defterde kalmak zorunda."""
    monkeypatch.setattr(notify, "configured", lambda: False)
    obs.alarm("MECHANISM_STALE", "eski", mechanism="a")
    store.write_json(notify.ACK_FILE, {"ack_ts": "2099-01-01T00:00:00+00:00"})

    assert notify.inbox()["pending"] == 0, "ACK sınırı ilerlemedi"
    blob = "".join(str(e) for e in store.read_jsonl("events.jsonl"))
    assert "eski" in blob, "ACK alarmı SİLDİ — gelen kutusu bir görünüm olmalı, kaynak değil"


def test_the_missing_channel_is_a_fact_that_ack_cannot_close(sandbox_state, monkeypatch):
    """YAPISAL BOŞLUK 'okudum' ile kapanamaz: operatörün onayı bir bildirim kanalını var etmez.
    Kümülatif sayaçtan da bağımsızdır — sayaç sıfırlansa bile kanalın yokluğu görünür kalır."""
    monkeypatch.setattr(notify, "configured", lambda: False)
    obs.alarm("MECHANISM_STALE", "x", mechanism="a")            # teslim edilecek bir şey VAR
    store.write_json(notify.ACK_FILE, {"ack_ts": "2099-01-01T00:00:00+00:00"})   # hepsi "okundu"
    assert notify.inbox()["pending"] == 0, "ön koşul: gelen kutusu okunmuş olmalı"

    r = _row("notify_channel")
    assert r and r["ok"] is False and "kanalı YOK" in r["detail"], \
        "ACK gelen kutusunu kapattı diye YAPISAL boşluk da kapandı — 'okudum' kanal yaratmaz"

    monkeypatch.setattr(notify, "configured", lambda: True)
    assert _row("notify_channel")["ok"] is True, "kanal bağlıyken satır kurt masalı anlatmamalı"


def test_no_backlog_means_no_channel_complaint(sandbox_state, monkeypatch):
    """KURT MASALI YASAĞI + mutasyon bataryası: teslim edilecek hiçbir şey yokken 'kanal yok'
    demek boş bir alarmdır ve temel durumu kirletir — kirli temelde her mutasyon 'yakalandı'
    görünür ve kapsama sayısı yalan söyler (mutation.py bunu reddediyor)."""
    monkeypatch.setattr(notify, "configured", lambda: False)
    assert _row("notify_channel") is None and _row("alarm_delivery") is None


def test_the_missing_channel_never_alarms_through_the_missing_channel(sandbox_state, monkeypatch):
    """DÖNGÜSELLİK: 'kanal yok' bulgusu alarm kanalından duyurulursa teslim edilemeyen alarm
    sayacını kendi kendine besler. Bulgu makullük satırında durur, alarma dönüşmez."""
    monkeypatch.setattr(notify, "configured", lambda: False)
    obs.alarm("MECHANISM_STALE", "x", mechanism="a")      # satırın ÇIKMASI için yığın gerekli
    wd.check_integrity_and_alarm()
    latched = store.read_json("integrity_alarmed.json", [])
    assert _row("notify_channel") is not None, "ön koşul: satır gerçekten üretilmiş olmalı"
    assert "parity:notify_channel" not in latched, \
        "kanal yokluğu mandala yapıştı — kanal sonradan bozulursa bir daha hiç alarm veremez"


def test_ack_absorbs_the_backlog_so_the_row_can_turn_green(sandbox_state, monkeypatch):
    """KALICI KIRMIZI = HİÇ KIRMIZI (2026-07-26). `notify_undelivered.json` kümülatiftir ve asla
    azalmaz; satır bir kez kırmızıya döndüğünde sonsuza dek kırmızı kalıyordu ve operatör ona
    bakmayı bırakırdı. ACK 'gördüm' der: soğurulan yığın düşülür, KALINTI raporlanır. Sayacın
    kendisi sıfırlanmaz — yapısal boşluğun tarihi kaybolmaz."""
    monkeypatch.setattr(notify, "configured", lambda: False)
    obs.alarm("MECHANISM_STALE", "x", mechanism="a")
    obs.alarm("DATA_QUALITY", "y", kind="determinism")
    assert _row("alarm_delivery")["ok"] is False, "ön koşul: kalıntı varken satır kırmızı olmalı"

    store.write_json(notify.ACK_FILE, {"ack_ts": "2099-01-01T00:00:00+00:00", "absorbed": 2})
    r = _row("alarm_delivery")
    assert r is not None and r["ok"] is True, "soğurulan yığından sonra satır yeşile dönmedi"
    assert "soğuruldu" in r["detail"]
    assert store.read_json("notify_undelivered.json", {})["_toplam"] == 2, \
        "ACK sayacı SIFIRLADI — yapısal boşluğun tarihi silinemez"


def test_the_backlog_text_tells_the_truth_about_the_channel(sandbox_state, monkeypatch):
    """Metin `notify.configured()` GERÇEĞİNDEN üretilmeli: kanal bağlıyken 'kanal yapılandırılmamış'
    demek bugünün durumunu yanlış anlatır ve yanlış teşhis yanlış müdahaleyi doğurur."""
    monkeypatch.setattr(notify, "configured", lambda: False)
    obs.alarm("MECHANISM_STALE", "x", mechanism="a")          # yığın kanal YOKKEN toplandı
    monkeypatch.setattr(notify, "configured", lambda: True)   # sonra kanal bağlandı
    r = _row("alarm_delivery")
    assert r and "kanal bağlı" in r["detail"] and "yapılandırılmamış" not in r["detail"]


def test_suppression_is_logged_once_per_window_not_once_per_alarm(sandbox_state, monkeypatch):
    """GÜRÜLTÜYE KARŞI KURULAN MEKANİZMA GÜRÜLTÜ ÜRETEMEZ (2026-07-26). Susturma penceresi 6 saatte
    bir mesaj demek; ama kayıt HER bastırmada düşüyordu. Aynı pencerede 200 kez alarmlayan bir
    dedektör 200 `notify_suppressed` satırı yazıp olay defterini — gelen kutusunun ve tüm makullük
    dedektörlerinin okuduğu kaynağı — boğuyordu."""
    import time

    monkeypatch.setattr(obs, "_SUPPRESS_LOGGED", {})          # süreç-içi kayıt testler arası sızmasın
    monkeypatch.setattr(notify, "configured", lambda: True)
    monkeypatch.setattr(notify, "send", lambda msg: True)
    store.write_json("notify_sent.json", {"MECHANISM_STALE": time.time()})   # pencere AÇIK

    obs.alarm("MECHANISM_STALE", "birinci")
    n1 = sum(1 for e in store.read_jsonl("events.jsonl") if e.get("event") == "notify_suppressed")
    assert n1 == 1, "ilk bastırma kaydedilmedi — susturma yine görünmez"

    obs.alarm("MECHANISM_STALE", "ikinci")
    obs.alarm("MECHANISM_STALE", "üçüncü")
    n2 = sum(1 for e in store.read_jsonl("events.jsonl") if e.get("event") == "notify_suppressed")
    assert n2 == 1, f"aynı pencerede {n2} susturma satırı — pencere başına BİR olmalı"
    blob = "".join(str(e) for e in store.read_jsonl("events.jsonl"))
    assert "ikinci" in blob and "üçüncü" in blob, "alarmların kendisi düştü — susturma alarmı yutamaz"


def test_update_json_contract_is_honoured(sandbox_state, monkeypatch):
    """İLK DENEMEDE YAPTIĞIM HATA, kilitleniyor: `store.update_json` belgeyi YERİNDE değiştirip
    True dönmeyi bekler. Yeni bir sözlük döndürmek hiçbir şey yazmaz — dosya oluşur ama BOŞ kalır
    ve sayaç sessizce hep sıfır görünür. Sözleşmeyi yanlış okumanın cezası yine sessizlikti."""
    monkeypatch.setattr(notify, "configured", lambda: False)
    obs.alarm("MECHANISM_STALE", "x")
    d = store.read_json("notify_undelivered.json", {})
    assert d != {}, "sayaç dosyası boş — update_json sözleşmesi yine yanlış kullanılmış"
