"""test_composite_uc_durum_olayi_v534.py — bileşik ölçümün UÇ DURUM geçişleri OLAY olur
(TSK-215, ölçülmüş vaka 2026-09-21/23).

NUMARA KİMLİKTİR: `v534` ölçüldü (2026-09-23, `ls tests/`) — `v53x` aralığında `v530`, `v531`,
`v532` var; `v533` TSK-214'e (paralel dilim) ayrıldı, `v534` boştu. Çakışma YOK.

ÖLÇÜLMÜŞ VAKA — "VERİ VAR, OLAY YOK". C00005 bileşik ön-elemesi 2026-09-21 20:39Z'de ÇOCUK
süreçte düştü (`prescreen._sandbox` → `shutil.copytree` → sır yedeği dosyasında EACCES). Çocuk
`prescreen.kuyruk_geri_yaz` üzerinden `hermes_composite.mark(id, "measure_failed", neden=…)`
çağırdı ve KUYRUK SATIRI doğru damgalandı (A1'de ölçüldü: `status=measure_failed` + `neden`).
Ama OLAY DEFTERİNDE (`events.jsonl`) `composite_measure_failed` sayısı TÜM DEFTERDE 0'dı —
çünkü o olayı yalnız `reap_measuring`in ÖLÜ PİD dalı basıyordu ve satır hiçbir zaman
"measuring + ölü pid" hâline gelmedi (çocuk damgayı kendisi attı, reap görecek bir şey bulamadı).
Yani arıza bir DURUM defterinde vardı, bir OLAY defterinde yoktu: brifing/bekçi triyajı ve
`obs.recent` okuyucuları onu HİÇ göremezdi.

İDDİA (tek cümle): **geçiş nerede YAZILIYORSA olay orada basılır.** Damgayı `mark()` yazar →
olayı da `mark()` basar; `reap_measuring` kendi kopyasını taşımaz. İki üretici, aynı olgunun iki
sayımı demekti (tek-kaynak yasası, CLAUDE.md §4) ve hangi yolun sessiz kaldığı ancak canlıda
ölçülerek anlaşılırdı.

KAPSAM — BEŞ + BİR ÇİVİ:
  T1  `measure_failed` geçişi → TAM 1 `composite_measure_failed`; `neden` 200 karaktere KIRPILIR
      (kuyruk satırının `neden` alanıyla aynı tavan — olay defteri bir traceback arşivi değildir),
      `kaynak="mark"` alanı olayın ÜRETİCİSİNİ söyler (reap'ten mi mark'tan mı — vaka tam bu
      ayrımdan doğdu).
  T2  `measured` geçişi → TAM 1 `composite_measured` (`n_aday`/`sure_s` ÖZETTEN okunur, yoksa
      None — uydurma yasağı: "0 aday" ile "bilmiyorum" aynı şey değildir). ARA geçişler
      (`measuring`, `pending`) olay BASMAZ: spawn zaten `composite_prescreen_spawned` basıyor,
      ikincisi yalnız gürültü olurdu.
  T3  `reap_measuring` ölü-pid dalı: satır `measure_failed` OLUR ve olay TAM 1 — reap'in kendi
      kopyası geri gelirse bu çivi 2 sayar (TEKİLLEŞTİRME).
  T4  TEK KAYNAK, AST İLE: `composite_measure_failed` jetonunu taşıyan tek fonksiyon `mark`.
      Dizge araması DEĞİL — bir yorum satırındaki jeton çiviyi yanıltmasın, ve jeton başka bir
      fonksiyona kopyalandığı an (dizge eşitliği hâlâ "bir kez geçiyor" derken) kırmızı olsun.
  T5  DAĞITIM: `logs/` canlı-yalnızdır (çocuğun stdout/stderr'i oraya düşer, depoda yoktur) ve
      `rsync --delete` onu SİLERDİ — 2026-09-23 kuru koşumu `logs/composite-prescreen.log` ile
      `logs/`ü silinecekler arasında saydı. Çökmenin TEK kanıtı dağıtımla yok olurdu. Çivi
      dışlamanın varlığını ve `SPAWN_LOG` ile tek-kaynaklılığını ölçer: log yolu taşınırsa
      dışlama sessizce boşa düşmesin.
  T6  (EK ÇİVİ, beyan) OLAY = YAZILMIŞ GEÇİŞ: kuyrukta KARŞILIĞI OLMAYAN bir kimliğe basılan
      `mark` hiçbir şey yazmaz — o yüzden olay da basmaz. Olmamış bir geçişi haber vermek,
      uydurma yasağının olay-defteri hâli olurdu.

BU DOSYA CANLIYA DOKUNMAZ: her davranış çivisi `sandbox_state` altındadır (`config.STATE` tmp'ye
çevrilir), kaynak çivileri yalnız dosya OKUR.
"""
from __future__ import annotations

import ast
import pathlib

import pytest
import yaml

from meridian import config, hermes_composite, store

REPO = pathlib.Path(__file__).resolve().parent.parent
KAYNAK = REPO / "meridian" / "hermes_composite.py"
VARS_YML = REPO / "deploy" / "ansible" / "vars" / "dagit_vars.yml"

#: Olay jetonları — testin kendi sözlüğü DEĞİL, modülün bastığı adların birebir kopyası.
#: (Jeton bir KİMLİKTİR: `events.jsonl` satırının `event` alanı ve panonun olay yüzeyi onu
#: ALT-DİZGE değil TAM EŞİTLİK ile arar; adı değiştirmek okuyucuyu sessizce kör eder.)
JETON_DUSEN = "composite_measure_failed"
JETON_OLCULEN = "composite_measured"


# =================================================================================================
# ORTAK YARDIMCILAR
# =================================================================================================
def _kuyruga_yaz() -> str:
    """Kuyruğa bir satır koy, kimliğini dön. (Durum `enqueue`un verdiği hâlde kalır.)"""
    res = hermes_composite.enqueue({"stop_mode": 1, "stop_buffer_atr": 0.4},
                                   bounds=config.bounds())
    return res["row"]["id"]


def _olaylar(event: str | None = None) -> list[dict]:
    """`events.jsonl` satırları (isteğe bağlı olarak tek bir olay adına süzülmüş)."""
    satirlar = store.read_jsonl("events.jsonl")
    return [e for e in satirlar if event is None or e.get("event") == event]


def _satir(rid: str) -> dict:
    for r in store.read_jsonl(hermes_composite.QUEUE_FILE):
        if r.get("id") == rid:
            return r
    raise AssertionError(f"kuyruk satırı bulunamadı: {rid}")


def _cagri_adi(dugum: ast.Call) -> str:
    """`obs.warn(...)` → "obs.warn"; nokta zinciri olmayan çağrılarda "" döner."""
    f = dugum.func
    if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name):
        return f"{f.value.id}.{f.attr}"
    if isinstance(f, ast.Name):
        return f.id
    return ""


def _jetonu_tasiyan_fonksiyonlar(jeton: str) -> tuple[set[str], int]:
    """Kaynakta `jeton` DİZGESİNİ taşıyan fonksiyonların adları + toplam geçiş sayısı (AST).

    NEDEN AST, NEDEN DİZGE DEĞİL (CLAUDE.md §6 "çivi yeşili kanıt değildir"): `"jeton" in metin`
    çivisi iki yönden de kördür — (a) bir GEREKÇE YORUMUNDA geçen jeton onu "var" sayar,
    (b) jeton ikinci bir fonksiyona kopyalandığında dizge hâlâ "geçiyor" der ve tekilleştirme
    ihlali görünmez kalır. Burada ölçülen şey jetonun HANGİ FONKSİYONUN GÖVDESİNDE durduğudur;
    yorumlar ayrıştırıcı tarafından zaten atılır."""
    agac = ast.parse(KAYNAK.read_text(encoding="utf-8"))
    adlar: set[str] = set()
    toplam = 0
    for dugum in ast.walk(agac):
        if isinstance(dugum, ast.Constant) and dugum.value == jeton:
            toplam += 1
    for fn in ast.walk(agac):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if any(isinstance(alt, ast.Constant) and alt.value == jeton for alt in ast.walk(fn)):
            adlar.add(fn.name)
    return adlar, toplam


# =================================================================================================
# T1 — DÜŞEN ÖLÇÜM GEÇİŞİ OLAY BASAR (kaynak: mark)
# =================================================================================================
def test_T1_dusen_olcum_gecisi_olay_basar_ve_neden_kirpilir(sandbox_state):
    """`measure_failed` damgası artık SESSİZ DEĞİL: geçişi yazan yer olayı da basar.

    C00005 vakasının tam kapattığı delik: damga kuyrukta vardı, olay defterinde yoktu. `neden`
    200 karaktere kırpılır — çocuğun gönderdiği metin bir traceback başıdır ve olay defteri bir
    arşiv değil bir TRİYAJ yüzeyidir; kırpma olmadan tek satır defteri kilitler."""
    rid = _kuyruga_yaz()
    hermes_composite.mark(rid, "measure_failed", neden="x" * 500, pid=1)

    olaylar = _olaylar(JETON_DUSEN)
    assert len(olaylar) == 1, f"TAM 1 `{JETON_DUSEN}` bekleniyordu, {len(olaylar)} bulundu"
    e = olaylar[0]
    assert e["id"] == rid, f"olay yanlış satırı gösteriyor: {e.get('id')!r} ≠ {rid!r}"
    assert e["pid"] == 1
    assert e["kaynak"] == "mark", (
        "olayın ÜRETİCİSİ yazılmıyor — vaka tam bu ayrımdan doğdu (reap mı, mark mı?)")
    assert len(str(e["neden"])) == 200, (
        f"`neden` kırpılmadı ({len(str(e['neden']))} karakter) — olay defteri traceback arşivi "
        "değildir ve kuyruk satırının 200 karakter tavanıyla aynı dili konuşmalı")
    assert str(e["neden"]) == "x" * 200
    assert len(str(e["detail"])) >= 20, "YASA 4: uyarının gerekçesi ≥20 karakter"
    assert "iade edilmez" in str(e["detail"]), (
        "reap'in taşıdığı BÜTÇE cümlesi kaybolmuş — olay tek kaynağa taşınırken bilgi düşmemeli")
    assert _satir(rid)["status"] == "measure_failed", "damganın kendisi de yazılmış olmalı"


def test_T1b_neden_YOKSA_uydurulmaz(sandbox_state):
    """`neden` verilmemişse alan None'dır. Boş dizge yazmak "gerekçe yok"u "gerekçe boş"a
    çevirirdi; ölçülemeyen değer None + neden kuralı (uydurma yasağı) olay alanları için de
    geçerlidir."""
    rid = _kuyruga_yaz()
    hermes_composite.mark(rid, "measure_failed")
    e = _olaylar(JETON_DUSEN)[-1]
    assert e["neden"] is None and e["pid"] is None


# =================================================================================================
# T2 — ÖLÇÜLEN GEÇİŞ OLAY BASAR · ARA GEÇİŞLER SESSİZ
# =================================================================================================
def test_T2_olculen_gecis_olay_basar_ozetten_okur(sandbox_state):
    """`measured` de bir UÇ DURUMDUR ve görünür olmalı: halkanın KAPANDIĞI an, açıldığı an kadar
    kayda değerdir (`composite_prescreen_spawned` başlangıcı zaten basıyor, bitişin karşılığı
    yoktu). `n_aday`/`sure_s` `result` ÖZETİNDEN okunur — özetin kendisi kuyruk satırında durur,
    olay yalnız triyajın ihtiyacı kadarını taşır."""
    rid = _kuyruga_yaz()
    hermes_composite.mark(rid, "measured",
                          result={"n_aday": 2, "sure_s": 12.5, "k_probes": 1})
    olaylar = _olaylar(JETON_OLCULEN)
    assert len(olaylar) == 1, f"TAM 1 `{JETON_OLCULEN}` bekleniyordu, {len(olaylar)} bulundu"
    e = olaylar[0]
    assert e["id"] == rid and e["n_aday"] == 2 and e["sure_s"] == 12.5
    assert e["kaynak"] == "mark"


def test_T2b_ozet_yoksa_alanlar_None_KALIR(sandbox_state):
    """Özet yoksa `n_aday` 0 DEĞİL None'dır: "hiç aday yoktu" ile "kaç aday olduğunu bilmiyorum"
    ayrı cümlelerdir ve ikincisini birincisi gibi yazmak uydurmadır."""
    rid = _kuyruga_yaz()
    hermes_composite.mark(rid, "measured")
    e = _olaylar(JETON_OLCULEN)[-1]
    assert e["n_aday"] is None and e["sure_s"] is None


def test_T2c_ara_gecisler_olay_BASMAZ(sandbox_state):
    """`measuring`/`pending` UÇ DURUM DEĞİLDİR. `measuring` geçişini `spawn_pending` zaten
    `composite_prescreen_spawned` ile duyuruyor; ikinci bir satır BEDEL YASASInın ters yönüdür —
    gürültü, okuyucunun uç durumları görmesini zorlaştırır."""
    rid = _kuyruga_yaz()
    once = len(_olaylar())
    hermes_composite.mark(rid, "measuring", pid=4242)
    hermes_composite.mark(rid, "pending")
    assert len(_olaylar()) == once, (
        "ara geçiş olay bastı — `measuring`/`pending` uç durum değildir")
    assert _satir(rid)["status"] == "pending", "damgalar yine de yazılmış olmalı"


# =================================================================================================
# T3 — REAP ÖLÜ-PİD DALI: TEK OLAY (tekilleştirme)
# =================================================================================================
def test_T3_reap_olu_pid_dalinda_olay_TEK_kopya(sandbox_state, monkeypatch):
    """Ölü süreç yolu DA `mark`tan geçer, dolayısıyla olayı `mark` basar — reap ikinci bir kopya
    BASMAZ. İki üretici olsaydı aynı olgu defterde iki kez sayılır ve "kaç bileşik ölçüm düştü?"
    sorusu üreticiye göre farklı cevap verirdi (tek-kaynak yasası)."""
    rid = _kuyruga_yaz()
    hermes_composite.mark(rid, "measuring", pid=4242)
    monkeypatch.setattr(hermes_composite, "_pid_canli", lambda pid: False)

    out = hermes_composite.reap_measuring()
    assert out["olu"] == [rid]
    assert _satir(rid)["status"] == "measure_failed"
    olaylar = _olaylar(JETON_DUSEN)
    assert len(olaylar) == 1, (
        f"`{JETON_DUSEN}` {len(olaylar)} kez basıldı — reap kendi kopyasını geri mi aldı? "
        "Geçişi YAZAN yer (mark) tek üreticidir")
    assert olaylar[0]["kaynak"] == "mark" and olaylar[0]["id"] == rid


# =================================================================================================
# T4 — TEK KAYNAK (AST): jetonu yalnız `mark` taşır
# =================================================================================================
def test_T4_olay_jetonu_YALNIZ_mark_govdesinde(sandbox_state):
    """Yapısal tekillik: jeton kaynakta BİR kez ve yalnız `mark`ın gövdesinde geçer.

    T3 davranışı ölçer ("defterde iki satır yok"), bu çivi YAPIYI ölçer: ikinci üretici, henüz
    hiç koşmamışken bile kırmızı olsun. Davranış çivisi tek başına, hiç tetiklenmeyen bir dala
    kopyalanmış jetona kördür."""
    adlar, toplam = _jetonu_tasiyan_fonksiyonlar(JETON_DUSEN)
    assert adlar == {"mark"}, (
        f"`{JETON_DUSEN}` jetonunu taşıyan fonksiyon(lar): {sorted(adlar)} — tek üretici `mark` "
        "olmalı (geçiş nerede yazılıyorsa olay orada)")
    assert toplam == 1, f"jeton kaynakta {toplam} kez geçiyor, 1 bekleniyordu"

    adlar_olculen, toplam_olculen = _jetonu_tasiyan_fonksiyonlar(JETON_OLCULEN)
    assert adlar_olculen == {"mark"} and toplam_olculen == 1, (
        f"`{JETON_OLCULEN}` tek kaynak değil: {sorted(adlar_olculen)} / {toplam_olculen}")


# =================================================================================================
# T5 — DAĞITIM: canlı-yalnız `logs/` silinme listesinden çıktı
# =================================================================================================
def test_T5_dagit_disla_logs_ve_SPAWN_LOG_ayni_kaynaktan(sandbox_state):
    """Çökmenin TEK kanıtı bir sonraki dağıtımda yok olurdu.

    `SPAWN_LOG` çocuğun stdout/stderr'idir ve depo KÖKÜ altında (`logs/`) doğar — A1'de VAR,
    depoda YOK. `rsync --delete` ile koşan dağıtım, listede olmayan her canlı-sahipli yolu SİLER:
    2026-09-23 kuru koşumu `logs/composite-prescreen.log` ile `logs/`ü tam da bu yüzden
    silinecekler arasında saydı. Çivi iki şeyi birden tutar: dışlama VAR, ve dışlama `SPAWN_LOG`un
    kök dizininden TÜRER — log yolu yarın `veri/…`ye taşınırsa dışlama sessizce boşa düşmesin."""
    veri = yaml.safe_load(VARS_YML.read_text(encoding="utf-8"))
    disla = veri["rsync_disla"]
    assert isinstance(disla, list) and disla

    kok = pathlib.PurePosixPath(hermes_composite.SPAWN_LOG).parts[0]
    assert kok, "`SPAWN_LOG` bir dizin altında değil — dışlama neyi koruyacak?"
    beklenen = f"/{kok}"
    assert beklenen in disla, (
        f"`rsync_disla` içinde {beklenen!r} YOK — `SPAWN_LOG`un ({hermes_composite.SPAWN_LOG}) "
        "kök dizini dağıtımın `--delete` listesine düşer ve çökme kanıtı silinir")


# =================================================================================================
# T6 — OLAY = YAZILMIŞ GEÇİŞ (ek çivi, beyan)
# =================================================================================================
def test_T6_eslesmeyen_kimlik_icin_olay_BASILMAZ(sandbox_state):
    """Kuyrukta karşılığı olmayan kimlik bir GEÇİŞ DEĞİLDİR: `mark` hiçbir satır yazmaz, olay da
    basmaz. Aksi hâlde defter, hiç olmamış bir ölçüm düşüşünü haber verirdi — uydurma yasağının
    olay-defteri hâli."""
    _kuyruga_yaz()                                   # kuyrukta BAŞKA bir satır var
    hermes_composite.mark("C99999", "measure_failed", neden="olmayan satır")
    assert _olaylar(JETON_DUSEN) == [], (
        "yazılmamış bir geçiş için olay basıldı — olay, defterdeki damganın habercisidir")


@pytest.mark.parametrize("durum", ["measure_failed", "measured"])
def test_T6b_bos_kuyrukta_olay_BASILMAZ(sandbox_state, durum):
    """Aynı iddianın boş-kuyruk hâli: hiç satır yokken de sessizdir."""
    hermes_composite.mark("C00001", durum, neden="kuyruk boş")
    assert _olaylar() == [] or all(
        e.get("event") not in (JETON_DUSEN, JETON_OLCULEN) for e in _olaylar())
