"""test_provenance_v80.py — BASKIN KUSUR SINIFININ YAPISAL ÖLÇÜMÜ (2026-07-22).

Operatör: "bu kod tabanının baskın hata deseni her yerde karşımıza çıkıyor ... bunu bir şekilde
çözmemiz lazım." Desen tek cümle: **aynı yasanın iki uygulaması, sessizce ayrışmış.**

Neden 1257 test bunu göremiyor: her test KENDİ fikstürünü kurar. Üreticinin ne yazdığı ile
tüketicinin ne beklediğini AYNI EL yazar, dolayısıyla ayrışamazlar. Sınıfı tek tek yakalamak
(her alan için bir parite testi) çözüm değil — unutulan ilk alanda sınıf geri döner.

`meridian/provenance.py` sınıfı yapısal ölçer: uygulamanın GERÇEK okuma yolları sarılır ve
"okunan ama hiçbir satırda olmayan anahtar" doğrudan sürüklenmedir. Ölçüm aracı testlerin
kendisidir (MERIDIAN_PROVENANCE=1).

Bu dosya dedektörün KENDİSİNİ sınar. Bir dedektöre güvenmenin şartı, körlüğünün ve kurt masalı
eğiliminin ölçülmüş olmasıdır — burada ikisi de ölçülür.
"""
from __future__ import annotations

import pytest

from meridian import provenance as pv, store


@pytest.fixture
def izle(sandbox_state):
    # `pv.oturum()` YENİDEN-GİRİŞLİ: paket genelinde MERIDIAN_PROVENANCE=1 ile biriken ölçümü
    # ezmez, çıkışta aynen geri verir. Düz `basla()/dur()` kullanıldığında bu dosya oturum
    # ölçümünü sıfırlıyor ve paket sonu raporu "1 artefakt" diyordu.
    with pv.oturum():
        yield


# ---------------- 1) SINIFI GERÇEKTEN YAKALIYOR MU (körlük ölçümü) ----------------
def test_a_consumer_reading_a_key_no_producer_writes_is_caught(izle):
    """Sınıfın canlı biçimi: counterfactual.collect `dormant_setup` yazıyordu, tüketici `dormant`
    okuyordu; 7139 satırın hepsi yanlış etiketlendi ve hiçbir istisna oluşmadı."""
    store.write_jsonl("counterfactuals.jsonl",
                      [{"id": f"CF-{i}", "dormant_setup": "episodic_pivot"} for i in range(40)])
    for r in store.read_jsonl("counterfactuals.jsonl"):
        r.get("dormant")                       # ← üreticinin YAZMADIĞI alan

    rep = pv.rapor()
    hit = [d for d in rep["drift"] if d["artifact"] == "counterfactuals.jsonl" and d["key"] == "dormant"]
    assert hit, f"sürüklenme YAKALANMADI — dedektör kör: {rep['drift']}"
    assert not rep["ok"]
    assert hit[0]["rows"] == 40


def test_a_key_the_producer_does_write_is_not_flagged(izle):
    """POZİTİF KONTROL: doğru okuma sessiz kalmalı, yoksa dedektör her turda gürültü üretir."""
    store.write_jsonl("counterfactuals.jsonl", [{"id": "CF-1", "dormant": True}] * 12)
    for r in store.read_jsonl("counterfactuals.jsonl"):
        r.get("dormant")
    assert pv.rapor()["ok"], "doğru okuma ihlal sayıldı — kurt masalı"


def test_a_field_written_but_never_read_is_reported_as_dead(izle):
    """Sınıfın ikinci yüzü: üretilip tüketilmeyen kanıt. Sessizdir ama boşuna hesaplanır ve
    'ölçüyoruz' yanılsaması yaratır."""
    store.write_json("portfolio.json", {"equity": 1.0, "hic_okunmayan_alan": 42})
    store.read_json("portfolio.json", {}).get("equity")
    olu = {(d["artifact"], d["key"]) for d in pv.rapor()["dead_fields"]}
    assert ("portfolio.json", "hic_okunmayan_alan") in olu
    assert ("portfolio.json", "equity") not in olu


# ---------------- 2) KURT MASALI ANLATMIYOR MU (üç koruma) ----------------
def test_an_empty_ledger_is_never_judged(izle):
    """KORUMA 1: boş defterde her anahtar 'yok'tur. Bu kanıt yokluğudur, ayrışma değil."""
    store.write_jsonl("counterfactuals.jsonl", [])
    for r in store.read_jsonl("counterfactuals.jsonl"):
        r.get("dormant")
    store.read_json("regime.json", {}).get("regime")        # hiç yazılmamış dosya
    assert pv.rapor()["ok"], "boş defter üzerinden ihlal uyduruldu"


def test_a_read_with_an_explicit_default_is_optional_by_design(izle):
    """KORUMA 2: `.get(k, x)` çağıranın yokluğu tasarımca karşıladığını söyler."""
    store.write_jsonl("trades.jsonl", [{"id": f"T{i}", "r_multiple": 0.4} for i in range(20)])
    for r in store.read_jsonl("trades.jsonl"):
        r.get("alpaca_fill_price", 0.0)                     # varsayılanlı → isteğe bağlı
    assert pv.rapor()["ok"], "varsayılanlı okuma ihlal sayıldı"


def test_a_polymorphic_ledger_yields_inconclusive_not_a_violation(izle):
    """KORUMA 3 — dedektörün KENDİ kurt masalı, canlıda yakalandı: events.jsonl'de `plan_id`
    sürüklenmesi bildirmişti. Oysa üretici (loop.py:114) alanı doğru yazıyor; o alanı taşıyan beş
    olay türünden dördü bu defterde henüz hiç ateşlememişti. Çok-biçimli bir defterde YOKLUK
    hüküm vermez. Kanıtlanamayan şey 'ihlal' değil 'belirsiz' yazılır."""
    satir = []
    for i in range(60):                                     # her tür farklı alan taşır
        satir.append({"ts": "t", "event": "a", "ticker": "X"} if i % 3 == 0 else
                     {"ts": "t", "event": "b", "pinned": 1} if i % 3 == 1 else
                     {"ts": "t", "event": "c", "model": "m", "cooling_s": 1, "reason": "r"})
    store.write_jsonl("events.jsonl", satir)
    for r in store.read_jsonl("events.jsonl"):
        r.get("plan_id")

    rep = pv.rapor()
    assert not [d for d in rep["drift"] if d["key"] == "plan_id"], "çok-biçimli defterde ihlal uyduruldu"
    assert [d for d in rep["inconclusive"] if d["key"] == "plan_id"], "belirsizlik SESSİZCE yutuldu"
    assert rep["ok"], "belirsizlik hükmü kırmızıya çevirdi"


def test_a_map_shaped_artifact_is_declared_not_silenced(izle):
    """Haritada anahtar ŞEMA değil VERİdir: brain_cooldown.json yalnız DİNLENMEDEKİ beyni taşır,
    `nous` okuyup None almak tasarımın kendisidir. Muafiyet susturma değil BEYANdır."""
    store.write_json("brain_cooldown.json", {"gemini": {"until": 1.0}})
    d = store.read_json("brain_cooldown.json", {})
    d.get("nous"); d.get("claude")
    assert pv.rapor()["ok"]
    assert "brain_cooldown.json" in pv.HARITA
    assert all(str(v).strip() for v in pv.HARITA.values()), "gerekçesiz beyan, beyan değildir"


def test_every_optional_exemption_carries_a_reason():
    """Gerekçesiz istisna, istisnanın kendisi değil sessizliğidir — watchdog.grant_amnesty ile
    aynı disiplin."""
    assert pv.OPSIYONEL, "muafiyet tablosu boş — kural yaşamıyor demektir"
    for (art, key), sebep in pv.OPSIYONEL.items():
        assert str(sebep).strip(), f"gerekçesiz muafiyet: {art}.{key}"


# ---------------- 3) DEDEKTÖR ÖLÇTÜĞÜ ŞEYİ BOZMUYOR MU ----------------
def test_tracking_does_not_change_what_the_app_sees(izle):
    """Bir bekçi ölçtüğü şeyi PERTURBE ETMEMELİ. İzlenen sözlük, dict ile birebir aynı davranmalı:
    eşitlik, json, kopyalama, üyelik. Aksi hâlde dedektör kendi hatalarını doğurur."""
    import json
    ham = {"a": 1, "b": [1, 2], "c": {"d": 3}}
    store.write_json("portfolio.json", ham)
    okunan = store.read_json("portfolio.json", {})
    assert okunan == ham and dict(okunan) == ham
    assert json.loads(json.dumps(okunan)) == ham
    assert "a" in okunan and sorted(okunan.keys()) == ["a", "b", "c"]
    assert okunan["c"]["d"] == 3


def test_tracking_is_off_by_default_and_returns_the_object_untouched():
    """Üretim yolunda sıfır maliyet ve sıfır davranış farkı: kapalıyken sarmalayıcı NESNENİN
    KENDİSİNİ döndürür (kopya bile değil)."""
    pv.dur()
    assert not pv.aktif()
    obj = {"x": 1}
    assert pv.sar("her.json", obj) is obj
    satirlar = [{"x": 1}]
    assert pv.sar("her.jsonl", satirlar) is satirlar


def test_the_report_writes_nothing_to_disk(izle):
    """Dedektör KENDİ tabanını yazmamalı — bu kod tabanında bir kez yaşandı: /api/diagnostics her
    pano yenilemesinde bütünlük tabanını yeniden yazıyordu, yani PANOYU AÇIK TUTMAK gerilemeleri
    yeni tabana emiyordu."""
    from meridian import config
    once = {p.name: p.stat().st_mtime_ns for p in config.STATE.glob("*") if p.is_file()}
    store.write_jsonl("trades.jsonl", [{"id": "T1"}])
    store.read_jsonl("trades.jsonl")[0].get("yok_boyle_alan")
    pv.rapor(); pv.rapor()
    sonra = {p.name: p.stat().st_mtime_ns for p in config.STATE.glob("*") if p.is_file()}
    assert once.keys() | {"trades.jsonl"} == sonra.keys(), "rapor yeni dosya yarattı"
    for k in once:
        assert once[k] == sonra[k], f"rapor {k} dosyasını yazdı — okuma yolu taban yazıyor"
