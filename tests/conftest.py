import pathlib

import pandas as pd
import numpy as np
import pytest

from meridian import config

# ---- CANLI STATE SIZINTI BEKÇİSİ (2026-07-22) ---------------------------------------------------
# Bulgu: tekil test dosyaları canlı `state/`e dokunmuyordu ama TAM SUITE dokunuyordu — canlı nabzı
# (regime/equity/last_bar) siliyor, pano "rejim yok" gösteriyordu. Sebep sınıfı: bir test arka plan
# döngüsü/iş parçacığı başlatıyor ya da fikstür dışında yazıyor; sandbox söküldükten SONRA yazım
# canlı dizine düşüyor. Hiçbir test kırılmıyor, kimse fark etmiyor — bugünün baskın hata deseninin
# ta kendisi. Bekçi her testten sonra canlı dizini karşılaştırır ve sızıntıyı ADIYLA düşürür.
_LIVE = pathlib.Path(__file__).resolve().parent.parent / "state"


def _live_fingerprint() -> dict:
    # ALT DİZİNLER DE TARANIR (2026-07-29, C2 turu): eski glob("*.json*") yalnız köke bakıyordu —
    # state/bars_intraday/ altına düşen 16 MB'lık sızıntı bu katmana da görünmezdi. os.scandir
    # yığını ölçüldü: 650 dosyada ~4-5ms (rglob ~50ms); katman zaten yalnız uygulama kapalıyken
    # koşar, suite başına maliyet kabul edilebilir. Anahtar `_LIVE`e GÖRELİ yoldur: iki farklı
    # alt dizindeki aynı adlı dosya (ör. bars/AAPL.json ve bars_intraday/AAPL.json) `p.name` ile
    # birbirini eziyordu — sızıntı sayısı eksik, adı yanıltıcı olurdu.
    import os as _os
    out: dict = {}
    stack = [str(_LIVE)]
    base = str(_LIVE) + _os.sep
    while stack:
        d = stack.pop()
        try:
            with _os.scandir(d) as it:
                for e in it:
                    if e.is_dir(follow_symlinks=False):
                        stack.append(e.path)
                    elif e.is_file(follow_symlinks=False):
                        out[e.path.removeprefix(base)] = e.stat(follow_symlinks=False).st_mtime_ns
        except OSError:  # sessiz-yutma: canlı dizin yoksa (taze klon/CI) karşılaştıracak bir şey de yoktur
            pass
    return out


def _app_is_running() -> bool:
    """Canlı Meridian süreci var mı? Artık bekçiyi KAPATMAZ — yalnız İKİNCİ katmanı sınırlar."""
    import subprocess
    try:
        r = subprocess.run(["pgrep", "-f", "uvicorn meridian.api"],
                           capture_output=True, text=True, timeout=5)
        return bool(r.stdout.strip())
    except (OSError, subprocess.SubprocessError):  # sessiz-yutma: pgrep yoksa/başarısızsa 'uygulama koşmuyor' varsayılır — bekçi AÇIK kalır, yani muhafazakâr taraf
        return False


_APP_RUNNING = _app_is_running()

# ---- NEDEN İKİ KATMAN (2026-07-22) --------------------------------------------------------------
# Bekçi eskiden uygulama koşarken TAMAMEN kapanıyordu, çünkü mtime karşılaştırması "bu testin
# yazımı" ile "koşan uygulamanın yazımı"nı ayırt edemiyordu. Ama operatörün test koşturmasının en
# olası olduğu an, uygulamanın açık olduğu andır — yani bekçi tam da en çok gerektiği zaman kapalıydı.
#
# BEDELİ ÖLÇÜLDÜ: `test_url_is_a_resolvable_wss_paper_url` endpoint'i şemasız bir değere yamalayıp
# `_url()` çağırıyordu ama `sandbox_state` almıyordu; `obs.warn` CANLI events.jsonl'a düşüyordu.
# Defterde günde 32 `mirror_stream_bad_base` biriktir ve bir üretim arızası gibi okundu — saatler
# yanlış yerde arandı. Testin canlı deftere yazması, operatöre sunulan kanıtı kirletmektir.
#
# Çözüm ayrım noktasını değiştirmek: mtime "kim yazdı"yı bilemez, ama YAZIM ÇAĞRISINI bu süreçte
# yakalarsak fail zaten bizimdir — uygulamanın eşzamanlı yazımları hiç görünmez.
#   Katman 1 (HER ZAMAN AÇIK): süreç-içi yazım kancaları. Uygulama açıkken de çalışır.
#   Katman 2 (yalnız uygulama KAPALIYKEN): eski mtime parmak izi — kancaların göremediği yazımları
#            yakalar (örn. testin başlattığı ALT SÜREÇ ya da fikstür söküldükten sonra yazan iplik).
# İkisi birbirinin yerine değil, tamamlayıcısıdır.
_LIVE_ROOT = _LIVE.resolve()


class _CanliYazimKaydi:
    """Bu SÜREÇTEKİ yazımlardan canlı dizine düşenleri adıyla toplar.

    KAYIT GÖRELİ YOLDUR, `p.name` DEĞİL (2026-07-29): katman 1 artık alt dizinlere yazan ham
    `open()` çağrılarını da görüyor (bkz. 4. blok), ama sızıntı `2026-07-29.jsonl (open)` diye
    raporlanırsa operatör hangi dizine düşüldüğünü BİLEMEZ — `bars/` ile `bars_intraday/` aynı
    ada sahip dosyalar barındırır. Bekçinin değeri sızıntıyı ADIYLA düşürmesindeyse, ad tam olmalı."""

    def __init__(self):
        self.hits: list[str] = []

    def note(self, path, nasil: str) -> None:
        try:
            # YOL HER ZAMAN ÇÖZÜLÜR (2026-07-29): eskiden yalnız GÖRELİ yollar `resolve()` ediliyordu,
            # absolute yollar olduğu gibi karşılaştırılıyordu — ama `_LIVE_ROOT` ÇÖZÜLMÜŞ bir yoldur.
            # Normalize edilmemiş bir absolute yol `relative_to`dan ValueError alır ve sızıntı SESSİZCE
            # elenirdi: bekçiyi atlatmanın ÜÇÜNCÜ yolu. Ölçüldü — tmp'de kurulan sahte canlı dizine
            # yazan ham `open()` yalnız bu yüzden kaydedilmedi (/var→/private/var bağı).
            # VE BU DEPODA GERÇEK BİR VAKA: `~/Documents/Claude/AI-Trading` bu deponun kendisine giden
            # bir SEMBOLİK BAĞ (test_kimlik_v114 satır ~218'de belgeli). O yol üzerinden gelen bir
            # yazım canlı state'e düşer ama çözülmemiş hâliyle canlı köke göreli DEĞİLDİR — bekçi
            # kördü. Sızıntıyı ADIYLA düşürmesi beklenen bir bekçinin sessiz kaldığı yer, tam olarak
            # bu turda kapatılan delik sınıfının kendisidir.
            # Bedeli çözülmüş yol başına bir realpath; `note` yalnız yazım boğazlarından çağrılır.
            p = pathlib.Path(path).resolve()
            rel = p.relative_to(_LIVE_ROOT)    # canlı dizinin DIŞINDAYSA ValueError → sessizce çık
        except (ValueError, OSError, TypeError):  # sessiz-yutma: yol canlı dizinde değil ya da çözümlenemedi — bekçinin ilgi alanı dışı, testi düşürmez
            return
        kayit = f"{rel} ({nasil})"
        if kayit not in self.hits:
            self.hits.append(kayit)


# ---- ÜRETİM GLOBALLERİ SIZINTI BEKÇİSİ (2026-07-22) ---------------------------------------------
# Bulgu: `tests/test_cf_backfill_v14.py` `backtest.SECTORS.setdefault(...)` ile ÜRETİM sözlüğüne
# yazıyor ve geri almıyordu. SECTORS modül düzeyinde, değiştirilebilir ve `loop.SECTORS` ile AYNI
# nesne — yani sektör-tavanı kapısının okuduğu harita. Alfabetik sırada zehirleme SONRA geldiği için
# hiç görünmedi; suite ters sırada koşturulunca `test_b3_sector_map_covers_the_universe_exactly`
# düştü. Sıra bağımlı bir suite, geçtiğinde bile bir şey KANITLAMAZ: yarın bir dosya adı değişince
# yeşil kalır ya da kırmızıya döner, ikisi de aynı koda karşılık gelir.
_MUTABLE_GLOBALS = (("meridian.backtest", "SECTORS"),)


def _globals_snapshot() -> dict:
    import importlib
    snap = {}
    for mod, attr in _MUTABLE_GLOBALS:
        try:
            obj = getattr(importlib.import_module(mod), attr)
            snap[f"{mod}.{attr}"] = dict(obj) if isinstance(obj, dict) else set(obj)
        except Exception:  # sessiz-yutma: modül yoksa/okunamıyorsa karşılaştıracak bir şey de yoktur — bekçi sessizce devre dışı, testi düşürmez
            pass
    return snap


@pytest.fixture(autouse=True)
def _no_production_global_mutation():
    """Bir test üretim modülündeki değiştirilebilir bir globali kirletirse ADIYLA düşsün.
    `monkeypatch.setitem/setattr` kullanan testler etkilenmez (fikstür sökümünde geri alınır)."""
    before = _globals_snapshot()
    yield
    after = _globals_snapshot()
    for key, prev in before.items():
        now = after.get(key)
        if now != prev:
            eklenen = sorted(set(now) - set(prev))
            silinen = sorted(set(prev) - set(now))
            pytest.fail(f"ÜRETİM globali kirletildi: {key} (eklenen={eklenen[:8]} silinen={silinen[:8]}) "
                        f"— `monkeypatch.setitem/setattr` kullan; kalıcı yazım sonraki testleri "
                        f"sessizce etkiler ve suite'i SIRA BAĞIMLI yapar")


def _kancalari_kur(kayit) -> list:
    """Yazım BOĞAZLARINI sarar; geri alma listesi döndürür. Hepsi ÇAĞRI ANINDA yolu çözer:
    `sandbox_state` config.STATE'i tmp'ye çevirdiği için sandbox'lı testlerin yazımları canlı
    dizine düşmez ve hiç kaydedilmez.

    NEDEN `monkeypatch` FİKSTÜRÜ DEĞİL (2026-07-22): bekçi paylaşılan monkeypatch'e bağlanınca
    fikstür SÖKÜM SIRASINA giriyor ve komşu bekçiyi bozdu — `_no_production_global_mutation`,
    testin `monkeypatch.setitem` ile yaptığı geçici SECTORS değişikliği HENÜZ GERİ ALINMADAN
    ölçüm yapıp doğru testleri suçladı. Bir bekçinin ölçtüğü şeyi kendi varlığı değiştiriyorsa,
    o bekçi kanıt değil gürültü üretir. Kendi kancalarını kendi kurup kendi söker."""
    import os as _os
    from meridian import store
    geri: list = []

    # 1) store ilkelleri — kodun yazım sözleşmesi. `append_jsonl` ÖZELLİKLE önemli: obs.warn
    #    buradan geçer, yani defter kirlenmesinin tam yolu (canlıda yaşanan sızıntı buydu).
    for ad in ("write_json", "write_jsonl", "append_jsonl"):
        _asil = getattr(store, ad)

        def _sar(name, *a, _asil=_asil, _ad=ad, **k):
            try:
                yol = pathlib.Path(name) if _os.path.isabs(str(name)) else store._state() / str(name)
                kayit.note(yol, f"store.{_ad}")
            except Exception:  # sessiz-yutma: kancanın kendi muhasebesi düştü — ASIL yazım her hâlükârda yapılır, bekçi testi bozamaz
                pass
            return _asil(name, *a, **k)

        setattr(store, ad, _sar)
        geri.append(lambda ad=ad, _asil=_asil: setattr(store, ad, _asil))

    # 2) os.replace — ATOMİK yazarların ortak son adımı (store, config.yaml, secrets.json).
    #    mkstemp+replace deseni store dışında da kullanıldığı için boğaz burada yakalanır.
    _asil_replace = _os.replace

    def _replace(src, dst, *a, **k):
        kayit.note(dst, "os.replace")
        return _asil_replace(src, dst, *a, **k)

    _os.replace = _replace
    geri.append(lambda: setattr(_os, "replace", _asil_replace))

    # 3) Path.write_text/write_bytes/touch — store'u atlayan doğrudan yazarlar (memory.py lessons,
    #    health.py HALT bayrakları, run.py scoreboard). HALT bayrağı özellikle kritik: sandbox'sız
    #    bir test canlı sistemi DURDURABİLİR ve eski bekçi bunu uygulama açıkken hiç görmezdi.
    for ad in ("write_text", "write_bytes", "touch"):
        _asil_m = getattr(pathlib.Path, ad)

        def _sar_m(self, *a, _asil_m=_asil_m, _ad=ad, **k):
            kayit.note(self, f"Path.{_ad}")
            return _asil_m(self, *a, **k)

        setattr(pathlib.Path, ad, _sar_m)
        geri.append(lambda ad=ad, _asil_m=_asil_m: setattr(pathlib.Path, ad, _asil_m))

    # 4) builtins.open / io.open — boğazları ATLAYAN ham yazarlar (2026-07-29, C2 turu bulgusu):
    #    `barsarchive` dayanıklılık için `open()`+`fsync` kullanır; bir testin `monkeypatch.undo()`
    #    kazası paylaşılan fikstürün TÜM yamalarını söktü ve arşivci canlı `state/bars_intraday/`
    #    altına 16 MB yazdı — yukarıdaki üç boğazın HİÇBİRİ görmedi. Bu blok o sınıfı kapatır.
    #    PERFORMANS: derin yol çözümü (resolve+relative_to) yalnız write-modlu ('w'/'a'/'x'/'+')
    #    VE str'inde 'state' geçen açılışlarda; okuma açılışları tek küme kesişimiyle geçer.
    #    Python 3.12'de `io.open` builtins.open'ın TA KENDİSİDİR ve `Path.open`/`Path.write_text`
    #    modül-global `io.open`u çağırır — iki adı da AYNI sarmalayıcıya bağla, ikisini de geri al.
    #    int fd'ler ('os.fdopen') str'inde 'state' içermez, doğal elenir.
    import builtins as _bi
    import io as _io
    _asil_open = _bi.open

    def _open_sar(file, mode="r", *a, **k):
        try:
            if isinstance(mode, str) and (set(mode) & set("wax+")) and "state" in str(file):
                kayit.note(file, "open")
        except Exception:  # sessiz-yutma: kancanın kendi muhasebesi düştü — ASIL açılış her hâlükârda yapılır, bekçi testi bozamaz
            pass
        return _asil_open(file, mode, *a, **k)

    _bi.open = _open_sar
    _io.open = _open_sar
    geri.append(lambda: (setattr(_bi, "open", _asil_open), setattr(_io, "open", _asil_open)))

    return geri


@pytest.fixture(autouse=True)
def _no_live_state_writes(request):
    """KATMAN 1 her zaman açık; KATMAN 2 yalnız uygulama kapalıyken anlamlı (yukarıdaki gerekçe)."""
    kayit = _CanliYazimKaydi()
    geri = _kancalari_kur(kayit)
    before = None if _APP_RUNNING else _live_fingerprint()
    try:
        yield
    finally:
        for f in reversed(geri):        # kancalar HER hâlükârda sökülür — test düşse de, hata atsa da
            f()
    if kayit.hits:
        pytest.fail(f"CANLI state'e YAZILDI ({request.node.name}): {sorted(kayit.hits)} — testler "
                    f"yalnız `sandbox_state` içinde yazabilir. Canlı defter operatöre sunulan "
                    f"kanıttır; test artefaktı oraya düşerse üretim arızası gibi okunur.")
    if before is not None:
        after = _live_fingerprint()
        changed = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
        if changed:
            pytest.fail(f"CANLI state DEĞİŞTİ ({request.node.name}): {changed} — yazım kancalara "
                        f"görünmedi, yani ALT SÜREÇ ya da fikstür söküldükten sonra yazan bir iplik "
                        f"var. Bu sınıf, uygulama açıkken taranamaz — worker'ı `./ops/stop-worker.sh` "
                        f"ile durdur (çıplak pkill probe havuzunu yetim bırakır; 2026-07-26 vakası) "
                        f"ve keepalive diriltmesin diye `state/keepalive.pid` dosyasını sil.")


# ---- HERMES ARKA PLAN İPLİĞİ SIZINTISI (2026-07-29) ---------------------------------------------
# Yukarıdaki KATMAN 2 uyarısı "fikstür söküldükten sonra yazan bir iplik" diyordu ve tam olarak bu
# oluyordu. Danışma katmanı iki yerde AYRIK bir daemon thread'i başlatır:
#   loop.daily_cycle  → hermes.review_candidates_async()  (iplik: "candidate-review")
#   /api/...          → hermes.backfill_opinions_async()  (iplik: "opinion-backfill")
# İkisi de `hermes._agent_call`e iner: GERÇEK bir alt süreç (yerel hermes CLI) çalıştırır ve
# `obs.log("agent_call", ...)` ile deftere yazar. Yazım anında hangi dizine düşeceğini
# `config.STATE` belirler — ve `sandbox_state` monkeypatch'i test BİTİNCE geri alınır. Yani iplik
# testten uzun yaşadığında yazımı CANLI `state/events.jsonl`a düşer: operatörün defterinde, hiçbir
# testi kırmadan, gerçek bir `agent_call` kaydı gibi görünen bir test artefaktı. Sıra bağımlıdır
# (ipliğin bitiş anı ile fikstür sökümü yarışır), yani "bugün geçti" hiçbir şey kanıtlamaz.
#
# İKİ KATLI ÇÖZÜM — önlemek ve yakalamak aynı şey değildir:
#   ÖNLE : iki spawner varsayılan olarak NO-OP'a çevrilir. Hiçbir test bu ipliği İSTEMİYORDU;
#          danışma katmanı kapıyı değiştirmez, dolayısıyla hiçbir testin beklentisi ona bağlı
#          değil (depoda `*_async` çağrısını doğrulayan tek bir test yok — arandı). Çağrılar
#          KAYDEDİLİR: bir test "danışma katmanı tetiklendi mi" diye sormak isterse
#          `hermes_async_cagrilari` fikstürüyle sorabilir — yeteneği kaldırmıyoruz, ipliği.
#   YAKALA: teardown'da hâlâ yaşayan bir hermes ipliği varsa test ADIYLA düşer. Yarın eklenecek
#          ÜÇÜNCÜ bir async yol bu muhafazadan sessizce geçemez; önlem listesi eskir, dedektör
#          eskimez.
_HERMES_IPLIK_ADLARI = ("candidate-review", "opinion-backfill",
                        "hermes-standby", "hermes-reflect-now")


class _SahteIplik:
    """`review_candidates_async` çağırana Thread DÖNDÜRÜR ve sözleşmesi 'gerekirse join et'tir.
    No-op yerine None dönmek o sözleşmeyi kırardı (`AttributeError: 'NoneType' has no 'join'`),
    yani testi gerçek bir kusur yokken düşürürdü. Zaten bitmiş bir iplik gibi davranır."""

    name = "hermes-async-noop"

    def join(self, timeout=None):
        return None

    def is_alive(self):
        return False


@pytest.fixture(autouse=True)
def hermes_async_cagrilari(request):
    """Hermes danışma ipliklerini VARSAYILAN olarak başlatma; çağrıları kaydet; sızıntıyı yakala.

    Gerçek ipliği isteyen test `@pytest.mark.hermes_gercek_iplik` işaretini koyar ve ipliği KENDİ
    join etmekle yükümlü olur (aksi halde aşağıdaki dedektör onu adıyla düşürür).

    KENDİ YAMASINI KENDİ KURAR/SÖKER — `monkeypatch` FİKSTÜRÜNÜ PAYLAŞMAZ: bu dosyada aynı ders
    iki kez yazılı (bkz. `_kancalari_kur` ve `_hotstate_off_by_default` gerekçeleri). Paylaşılan
    monkeypatch'e bağlanan bir bekçi, fikstür SÖKÜM SIRASINA girer; komşu bekçi (`_no_production_
    global_mutation`) ölçümünü henüz geri alınmamış bir yamanın üstünde yapıp MASUM bir testi
    suçlamıştı. Bir bekçinin ölçtüğü şeyi kendi varlığı değiştiriyorsa, o bekçi kanıt değil
    gürültü üretir."""
    import meridian.hermes as _hm
    cagrilar: list[tuple[str, tuple, dict]] = []
    geri: list = []
    if "hermes_gercek_iplik" not in request.keywords:
        for ad in ("review_candidates_async", "backfill_opinions_async"):
            _asil = getattr(_hm, ad)
            setattr(_hm, ad,
                    lambda *a, _ad=ad, **k: (cagrilar.append((_ad, a, k)), _SahteIplik())[1])
            geri.append(lambda ad=ad, _asil=_asil: setattr(_hm, ad, _asil))
    try:
        yield cagrilar
    finally:
        for f in reversed(geri):    # yamalar HER hâlükârda sökülür — test düşse de, hata atsa da
            f()
    import threading
    kalan = sorted({t.name for t in threading.enumerate()
                    if any(t.name.startswith(p) for p in _HERMES_IPLIK_ADLARI)})
    if kalan:
        pytest.fail(
            f"HERMES ARKA PLAN İPLİĞİ SIZDI ({request.node.name}): {kalan} — iplik testten uzun "
            f"yaşıyor. `config.STATE` sandbox'tan geri alındıktan sonra yazarsa kayıt CANLI "
            f"state/events.jsonl'a düşer ve operatörün defterinde gerçek bir `agent_call` gibi "
            f"okunur. İpliği başlatan çağrıyı taklit et ya da testte join et.")


def _clear_module_caches():
    """Süreç-içi modül önbellekleri testler ARASI taşınır (2026-07-23, tarama bulgusu): bir test
    canlı skills/ ya da earnings verisinden okuyup dolan önbelleği bir sonrakine sızdırıyordu ve o
    test kendi kurmadığı veriyle 'geçiyor' görünüyordu. sandbox'a giriş/çıkışta hepsi sıfırlanır."""
    import meridian.earnings as _ea
    import meridian.skills as _sk
    import meridian.reflect as _rf
    import meridian.adapters.fmp as _fmp
    import meridian.secrets as _se
    # SIR ÖNBELLEĞİ DE SIZIYORDU (2026-07-26): `secrets.get` değerleri süreç-içi bir sözlükte
    # (TTL'li) tutuyor. Bir test `NOUS_MODEL`/`FMP_API_KEY` yamalayıp okuduğunda değer önbelleğe
    # düşüyor ve SONRAKİ test, kendi kurmadığı bir sırla "geçiyor" görünüyordu — ya da tersi:
    # gerçek makinedeki bir anahtar suite'e sızıp beyin zinciri ölçümünü değiştiriyordu.
    _se.clear_cache()
    # FMP KOTA BLOĞU DA SIZIYORDU (2026-07-26): `_KEY_BLOCKED` modül-global ve 429 gören bir test
    # anahtarı 1 saatliğine blokluyor; sonraki testler o bloğu MİRAS alıyordu. Bugüne kadar
    # görünmüyordu çünkü `_get`, tüm anahtarlar bloklu olsa bile birincil anahtarla YİNE DE bir
    # istek atıyordu — yani blok test-arası sızıyor ama sonucu maskeleniyordu. O fall-through
    # kaldırılınca sızıntı ortaya çıktı (test_data_audit_v17: tek başına geçiyor, paket içinde düşüyor).
    _fmp._KEY_BLOCKED.clear()
    # SAĞLIK KAYDI DA SIZIYORDU (2026-07-26): `_HEALTH` modül-global ve her çağrı onu günceller.
    # Sandbox'sız bir test mock 429 ile ok=False & calls>0 bırakınca SONRAKİ watchdog testi kendi
    # kurmadığı bir 'fmp_source starved' bulgusunu görüyordu — testin geçmesi ya da düşmesi
    # sırasına bağlı hâle gelir ve o an dedektör değil, sızıntı ölçülüyor demektir. Sözlük YERİNDE
    # sıfırlanır (clear+update): yeni bir dict atamak `fmp.health()` dışındaki modül referanslarını
    # koparır ve reset hiçbir şeye dokunmamış olurdu. Literal fmp.py'deki başlangıç değeridir.
    _fmp._HEALTH.clear()
    _fmp._HEALTH.update({"ok": None, "calls": 0, "fails": 0, "last_status": None,
                         "last_error": "", "at": None, "last_key": None, "last_body": ""})
    # KABA-KUVVET SAYACI DA SIZIYORDU (2026-07-29): `auth._FAILS` modül-global ve IP başına
    # başarısız giriş zaman damgası tutar. TestClient'ın istemci IP'si HER testte aynıdır
    # ("testclient"), yani başarısız girişi ölçen bir test 8 deneme biriktirince SONRAKİ testin
    # ilk `POST /api/login` çağrısı 429 (kilitli) alıyordu — kendi kurmadığı bir durumdan. Klasik
    # sıra bağımlılığı: tek başına yeşil, paket içinde kırmızı. Sayaç yerinde temizlenir (clear),
    # yeni bir dict ATANMAZ: `auth` modülündeki diğer referanslar kopardı ve sıfırlama hiçbir
    # şeye dokunmamış olurdu — `_fmp._HEALTH` ile aynı ders.
    import meridian.auth as _auth_mod
    _auth_mod._FAILS.clear()
    _ea._CACHE.clear()
    _sk._DESC_CACHE = None            # dict|None: yeniden okumaya zorla
    for c in (_rf._CACHE_WARNED,):
        c.clear()
    for c in (_rf._INC_CACHE, _rf._PROBE_CACHE):
        c.clear()


@pytest.fixture(autouse=True)
def _hotstate_off_by_default(request):
    """Redis SICAK KATMANI testlerde varsayılan KAPALI (2026-07-23). Canlı döngü hook'ları
    (loop._save_broker → hotstate.cache_positions, daily_cycle → set_prices) test-arası CANLI
    Redis'e yazmamalı: (a) test izolasyonu bozulur, (b) her _save_broker'da bağlantı+ping suite'i
    yavaşlatır, (c) kirlenmiş bir _client kapalı-porta soket-timeout'la suite'i ASAR (bu bulundu).
    `_redis`'i None'a sabitlemek tüm hotstate okuma/yazmalarını no-op yapar — hook'lar canlıdaki
    graceful-degradation yolunu izler. hotstate KENDİ testleri (nodeid'de 'hotstate') gerçek Redis.

    KENDİ HOOK'UNU try/finally ile KUR/KALDIR — `monkeypatch` PAYLAŞMA: monkeypatch fikstürüne
    bağlanmak teardown sırasını değiştirir ve komşu SECTORS-guard'ı MASUM bir testi suçlar
    (2026-07-23 bunu yeniden yaşadım; ders zaten kayıtlıydı)."""
    if "hotstate" in request.node.nodeid:
        yield
        return
    from meridian import hotstate
    _orig = hotstate._redis
    hotstate._redis = lambda: None
    try:
        yield
    finally:
        hotstate._redis = _orig


@pytest.fixture
def sandbox_state(tmp_path, monkeypatch):
    """Redirect all state I/O to a temp dir. Clears config + module caches so nothing leaks between tests."""
    state = tmp_path / "state"
    (state / "history").mkdir(parents=True)
    (state / "bars").mkdir(parents=True)
    monkeypatch.setattr(config, "STATE", state)
    monkeypatch.setattr(config, "HISTORY", state / "history")
    monkeypatch.setattr(config, "BARS", state / "bars")
    # YEREL AJAN YAPILANDIRMASI SUITE'E SIZIYORDU (2026-07-26): `hermes.AGENT_CONFIG` GERÇEK
    # `~/.hermes/config.yaml` yolunu gösteriyor ve `_agent_provider()` onu okuyor. Yani beyin
    # zinciri ölçümü (paylaşılan üst-akış tespiti) operatörün MAKİNESİNDEKİ dosyaya bağlıydı:
    # aynı test farklı makinede farklı sonuç verirdi ve geçtiğinde bir şey KANITLAMAZDI. Testler
    # kendi yapılandırmalarını bu yola yazar; dosya yoksa okuma dürüstçe None döner.
    import meridian.hermes as _hermes
    monkeypatch.setattr(_hermes, "AGENT_CONFIG", str(tmp_path / "hermes_config.yaml"))
    # goal/bounds ZORUNLU yapılandırmadır: yoksa config.goal() FileNotFoundError atar. Her test
    # dosyası bunu kendi `seeded` fikstüründe ayrı ayrı kopyalıyordu; kaynağa taşındı (2026-07-22)
    # ki sandbox'a alınan her test, ek fikstür yazmadan gerçek yapılandırmayla koşabilsin.
    import shutil
    repo = pathlib.Path(__file__).resolve().parent.parent / "state"
    for f in ("goal.yaml", "bounds.yaml"):
        src = repo / f
        if src.exists():
            shutil.copy2(src, state / f)
    config.goal.cache_clear()
    config.bounds.cache_clear()
    _clear_module_caches()
    yield state
    config.goal.cache_clear()
    config.bounds.cache_clear()
    _clear_module_caches()


def make_bars(n=320, seed=7, trend=0.0006, breakout_at=None):
    """Deterministic OHLCV with an optional clean breakout near the end."""
    rng = np.random.default_rng(seed)
    close = [100.0]
    for i in range(1, n):
        close.append(close[-1] * (1 + trend + rng.normal(0, 0.01)))
    close = np.array(close)
    if breakout_at:
        close[breakout_at:] *= 1.06  # step up to force a fresh high
    openp = close * (1 + rng.normal(0, 0.002, n))
    # OHLC TUTARLILIĞI (2026-07-23, tarama bulgusu): high/low YALNIZ close etrafında üretiliyordu,
    # open bağımsızdı — open bazen high'ı aşıyor ya da low'un altına düşüyordu ve `validate_bars`
    # bunu 'hard' (ohlc_inconsistent) reddediyordu. Yani make_bars kullanan HER test, üretimin veri
    # kapısının REDDEDECEĞİ barlarla koşuyordu. high >= max(o,c) ve low <= min(o,c) GARANTİ: fitili
    # gövdenin İKİ ucundan genişlet, tek uçtan değil.
    hi_base = np.maximum(openp, close)
    lo_base = np.minimum(openp, close)
    high = hi_base * (1 + np.abs(rng.normal(0, 0.004, n)))
    low = lo_base * (1 - np.abs(rng.normal(0, 0.004, n)))
    vol = rng.integers(1_000_000, 3_000_000, n).astype(float)
    if breakout_at:
        vol[breakout_at:] *= 2.0
    dates = pd.bdate_range("2022-01-03", periods=n)
    return pd.DataFrame({"date": dates, "open": openp, "high": high, "low": low,
                         "close": close, "volume": vol})


# ---- KÖKEN TAKİBİ: paketin kendisi sonda olur (2026-07-22) ----
# Baskın kusur sınıfı ("üretici X yazar, tüketici Y okur") hiçbir testte görünmez, çünkü her test
# KENDİ fikstürünü kurar: iki tarafın beklentisini aynı el yazar, ayrışamazlar. Çözüm tek tek
# parite testi yazmak DEĞİL — 1257 testin GERÇEK okuma yollarını ölçüm aracı olarak kullanmak.
# MERIDIAN_PROVENANCE=1 ile açılır; varsayılan kapalıdır (üretim yolunda sıfır maliyet).
def pytest_sessionstart(session):
    import os
    if os.environ.get("MERIDIAN_PROVENANCE") == "1":
        from meridian import provenance
        provenance.basla()


def pytest_sessionfinish(session, exitstatus):
    import os
    if os.environ.get("MERIDIAN_PROVENANCE") != "1":
        return
    import json
    from meridian import provenance
    rep = provenance.rapor()
    provenance.dur()
    # ÇIKTI ARTIK docs/ ALTINDA (K1, 2026-07-30): rapor depo KÖKÜNE yazılıyordu ve orada 8 gün
    # bayat, okuyucusuz ve `ok:false` diye durdu — okunmayan bir "sorun var" raporu yanlış güven
    # kaynağıdır. Daha kötüsü: `recompute` orphan taraması yalnız `state/*.json*` gezdiği için
    # kökteki bu dosyayı HİÇ göremiyordu (K1'de o kesit de genişletildi). docs/ altında olması
    # onu bir BELGE yapar: üretimi elle (MERIDIAN_PROVENANCE=1) tetiklenen, tarihli bir ölçüm.
    out = os.environ.get("MERIDIAN_PROVENANCE_OUT") or "docs/provenance_report.json"
    with open(out, "w") as f:
        json.dump(rep, f, ensure_ascii=False, indent=1)
    print(f"\n[köken] artefakt={rep['artifacts']} satır={rep['rows_seen']} "
          f"sürüklenme={len(rep['drift'])} belirsiz={len(rep['inconclusive'])} "
          f"ölü_alan={len(rep['dead_fields'])} → {out}")
