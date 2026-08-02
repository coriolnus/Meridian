"""test_diag_performans_v181.py — CANLI PERFORMANS: teşhis ucu 8,8-10,4 saniye (2026-08-03).

Operatör şikâyeti "pano çok yavaşlamış" ölçüldü: `/api/diagnostics` canlıda 8,8-10,4 sn. Kök TEK
bir hata değil, aynı ailenin üç örneği — **maliyeti hiç ölçülmemiş bir doğruluk düzeltmesi**:

1. C6 (2026-08-02) pencereleri satır-limitliden TARİH tabanlıya çevirdi ve bu DOĞRUYDU; ama
   `store.read_jsonl` dosyanın tamamını okuyup sonra dilimlediği için her dedektör 31 bin satırı
   BAŞTAN ayrıştırır oldu. `integrity_report` olay defterini YEDİ KEZ okuyordu (parity 4×, korunum
   1×, monotonluk 1×, defter sözleşmesi 1×). Düzeltme: tur başına TEK okuma, dedektörler paylaşır.
2. `/api/diagnostics` rotasının kendisinde HİÇ önbellek yoktu; içeride iki parçanın vardı
   (`integrity_report_cached` 20 sn, `alarm_budget_cached` 30 sn), yükün geri kalanı korumasızdı.
   Düzeltme: 45 sn TTL — bayatlığı `hesaplama_ts` + `onbellekten` ile BEYAN ederek.
3. `reflect` süreç havuzu iki işçiyle iki saat %99,9 CPU'da koştu ve pano API'sini boğdu (operatör
   elle `renice` attı). Düzeltme: işçiler `os.nice(15)` ile doğar, işçi sayısı `max(1, cpu-2)`.

ÜÇÜNÜN ORTAK ÇİVİSİ: hız düzeltmesi HÜKMÜ DEĞİŞTİRMEZ. Paylaşımlı okuma bit-bit aynı raporu verir,
önbellek yaşını gizlemez, kibarlaştırma arama sonucunu değiştirmez (yalnız zamanlama).
"""
from __future__ import annotations

import datetime as dt
import inspect
import os
import threading

import pytest

from meridian import api, config, obs, reflect, store, watchdog as wd


# =================================================================================================
# Yardımcılar
# =================================================================================================
def _defter(n: int = 3000) -> list[dict]:
    """Canlı defterin ŞEKLİ: %60 tek gürültü olayı (`hotstate_down` — K1'in ölçtüğü sel), kalanı
    döngü/red/düşüş karışımı. Damgalar geriye doğru dağıtılır ki 1/2/30 günlük pencerelerin üçü de
    FARKLI dilimler görsün — hepsi aynı dilimi görseydi paylaşım çivisi hiçbir şey kanıtlamazdı."""
    simdi = dt.datetime.now(dt.timezone.utc)
    out = []
    for i in range(n):
        ts = (simdi - dt.timedelta(minutes=(n - i) * 20)).isoformat(timespec="seconds")
        if i % 10 < 6:
            out.append({"ts": ts, "level": "warn", "event": "hotstate_down", "error": "redis"})
        elif i % 10 < 8:
            out.append({"ts": ts, "level": "info", "event": "daily_cycle",
                        "date": ts[:10], "candidates": i % 3})
        elif i % 10 == 8:
            out.append({"ts": ts, "level": "alarm", "alarm": "BROKER_REJECT",
                        "event": "BROKER_REJECT stop_vs_current", "plan_id": f"P{i}"})
        else:
            out.append({"ts": ts, "level": "warn", "event": "armed_expired_no_bar",
                        "plan_id": f"P{i}"})
    return out


@pytest.fixture
def sentetik_defter(sandbox_state):
    """Ölçüm zemini: olay defteri + plan defteri + portföy. Plan defteri PENCEREYİ belirler (C6)."""
    store.write_jsonl("events.jsonl", _defter())
    plans = [{"id": f"P{i}", "date": (dt.date.today() - dt.timedelta(days=40 - i % 40)).isoformat(),
              "ticker": "AAA", "gate_verdict": "GO", "size_r": 1.0} for i in range(40)]
    store.write_jsonl("trade_plans.jsonl", plans)
    store.write_jsonl("trades.jsonl", [])
    store.write_jsonl("counterfactuals.jsonl", [])
    store.write_json("portfolio.json", {"last_date": dt.date.today().isoformat(),
                                        "positions": {}, "armed": []})
    return sandbox_state


@pytest.fixture
def olay_okuma_sayaci(monkeypatch):
    """`events.jsonl` okumalarını (limit'iyle birlikte) sayar. LİMİTE GÖRE AYIRIR: bu turun
    kapsamı TAM okumalardır (limit=None); `ledgers.validate_live`in limit=200'lük okuması başka
    bir modülün işidir ve bilerek dışarıda bırakıldı."""
    cagrilar: list[int | None] = []
    _orig = store.read_jsonl

    def _sayan(name, limit=None):
        if str(name) == "events.jsonl":
            cagrilar.append(limit)
        return _orig(name, limit=limit)

    monkeypatch.setattr(store, "read_jsonl", _sayan)
    return cagrilar


@pytest.fixture
def yakala_uyari(monkeypatch):
    uyarilar: list[tuple[str, dict]] = []
    _w = obs.warn

    def _warn(event, **f):
        uyarilar.append((event, f))
        return _w(event, **f)

    monkeypatch.setattr(obs, "warn", _warn)
    return uyarilar


# =================================================================================================
# 1) TEK OKUMA PAYLAŞIMI — yedi okuma bire indi, hüküm değişmedi
# =================================================================================================
def test_integrity_report_olay_defterini_BIR_KEZ_tam_okur(sentetik_defter, olay_okuma_sayaci):
    """KUSURUN ÖLÇÜSÜ: düzeltmeden önce beş TAM okuma (korunum 1, parite 3, monotonluk 1) + iki
    limitli okuma vardı. Artık tam okuma BİR tanedir: turun başındaki paylaşılan okuma."""
    wd.integrity_report()
    tam = [l for l in olay_okuma_sayaci if l is None]
    assert len(tam) == 1, f"olay defteri {len(tam)} kez baştan okundu (paylaşım kırıldı): {olay_okuma_sayaci}"
    # 4000'lik dilim de artık paylaşılan listeden alınır — diske ikinci kez gidilmez.
    assert 4000 not in olay_okuma_sayaci, "parite 4000-satırlık dilimi yine diskten okuyor"


def test_paylasimli_ve_bagimsiz_okuma_BIT_BIT_ayni_hukum_verir(sentetik_defter, monkeypatch):
    """ÇİVİ: paylaşım bir HIZ değişikliğidir, bir DAVRANIŞ değişikliği değil. Karşılaştırma
    yönteminin kendisi de dürüst olmalı — 'bağımsız' kol, paylaşımı KAPATIP her dedektörü kendi
    okumasına düşürerek (yani düzeltme öncesi yol) üretiliyor."""
    paylasimli = wd.integrity_report()
    monkeypatch.setattr(wd, "_olay_satirlari",
                        lambda limit=None, olaylar=None: store.read_jsonl("events.jsonl", limit=limit))
    bagimsiz = wd.integrity_report()
    assert paylasimli == bagimsiz, "paylaşımlı okuma hükmü değiştirdi — bu bir hız düzeltmesi değil"


def test_dedektorler_BAGIMSIZ_cagrilabilir_KALIR(sentetik_defter):
    """GERİYE UYUMLULUK: üç dedektörün de tek başına çağrılan tüketicileri var (testler,
    `mutation.py`, ölçüm turları). Paylaşım opsiyoneldir: elden liste verilmiş hâli ile kendi
    okuyan hâli AYNI sonucu verir."""
    ham = store.read_jsonl("events.jsonl")
    assert wd.parity_report() == wd.parity_report(olaylar=ham)
    assert wd.conservation_report() == wd.conservation_report(olaylar=ham)
    assert wd.monotonicity_report() == wd.monotonicity_report(olaylar=ham)
    # events_since penceresi de aynı: liste elden verilince filtre değişmez, yalnız okuma tekrarlanmaz
    assert wd.events_since(2) == wd.events_since(2, olaylar=ham)


def test_C6_PENCERE_YASASI_paylasimda_korunur(sandbox_state):
    """C6'nın kalbi: korunum penceresi PLAN DEFTERİNDEN türer (sabit gün sayısı değil). Paylaşılan
    okuma pencereyi DARALTMAMALI — 40 gün önceki bir düşüş kaydı, plan 40 gün öncesine aitse hâlâ
    görülmeli. Daraltılsaydı bu plan sessizce 'AÇIKLANAMAYAN' sayılırdı: C6'nın ta kendisi."""
    eski = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=40)).isoformat(timespec="seconds")
    store.write_json("portfolio.json", {"last_date": dt.date.today().isoformat()})
    store.write_jsonl("trade_plans.jsonl", [
        {"id": "P-ESKI", "date": (dt.date.today() - dt.timedelta(days=40)).isoformat(),
         "ticker": "GS", "gate_verdict": "GO"}])
    store.write_jsonl("trades.jsonl", [])
    store.write_jsonl("counterfactuals.jsonl", [])
    store.write_jsonl("events.jsonl", [
        {"ts": eski, "level": "info", "event": "daily_cycle",
         "date": (dt.date.today() - dt.timedelta(days=41)).isoformat()},
        {"ts": eski, "level": "warn", "event": "armed_expired_no_bar", "plan_id": "P-ESKI"},
    ] + _defter(600))

    rep = wd.integrity_report()["conservation"]      # PAYLAŞIMLI yol
    assert rep["unexplained"] == 0, f"40 gün önceki düşüş kaydı pencere dışında kaldı: {rep}"
    assert rep["ok"] is True


def test_monotonluk_sayaci_TAM_defterden_gelir_penceresinden_DEGIL(sentetik_defter):
    """SESSİZ FELAKET ADAYI: monotonluk dedektörü defter UZUNLUĞUNUN gerilemesini arar ve tabanı
    tam defterle yazılmıştır. Paylaşım pencerelenmiş bir liste taşısaydı sayaç her turda küçülür,
    dedektör HER TUR sahte 'defter kısaldı' gerilemesi üretirdi. Paylaşım bu yüzden HAM satırlarla
    yapılır — bu test o kararın çivisidir."""
    tam = len(store.read_jsonl("events.jsonl"))
    store.write_json(wd.MONOTONIC_FILE, {"events": tam})        # taban: tam defter uzunluğu
    rep = wd.integrity_report()["monotonicity"]
    assert not [r for r in rep.get("regressions", []) if r["field"] == "events"], \
        f"paylaşılan liste pencerelenmiş — sahte defter-kısalması alarmı doğdu: {rep}"


def test_paylasilan_okuma_DUSERSE_dedektor_yalitimi_YASAR(sentetik_defter, monkeypatch,
                                                          yakala_uyari):
    """C21 SÖZLEŞMESİ PAYLAŞIMDAN SONRA DA GEÇERLİ: tek okumanın arızası YEDİ dedektörü birden
    düşüremez. Okuma düşerse rapor yine yedi desenle döner, olay defterini okumayan dedektörler
    hükmünü verir, okuyanlar TEK TEK düşer (ve düşüşleri adıyla görünür)."""
    _orig = store.read_jsonl

    def _patlayan(name, limit=None):
        if str(name) == "events.jsonl":
            raise OSError("defter okunamadı")
        return _orig(name, limit=limit)

    monkeypatch.setattr(store, "read_jsonl", _patlayan)
    rep = wd.integrity_report()

    assert {"production", "conservation", "determinism", "coherence",
            "monotonicity", "ownership", "parity"} == set(rep), "şekil sözleşmesi bozuldu"
    assert any(e == "integrity_shared_events_read_failed" for e, _ in yakala_uyari), \
        "paylaşılan okumanın düşüşü SESSİZ kaldı — yavaş yola düşüldüğü ölçülemez"
    assert rep["conservation"].get("dedektor_dustu") is True
    assert not rep["production"].get("dedektor_dustu"), "olay defterini okumayan dedektör de düştü"
    assert not rep["ownership"].get("dedektor_dustu")


def test_paylasim_kutusu_tur_bitince_BOSALIR_ve_iplik_yereldir(sentetik_defter):
    """Paylaşılan liste turun FOTOĞRAFIDIR. Bırakılsaydı bir sonraki bağımsız `parity_report()`
    çağrısı yaşı beyansız eski bir defteri okurdu. Ve kutu İPLİK-YEREL: canlıda scheduler, hermes
    ve API iplikleri aynı süreçte koşuyor — global bir kutu bir ipliğin okumasını diğerinin turuna
    sızdırırdı."""
    wd.integrity_report()
    assert getattr(wd._PAYLASIM, "olaylar", None) is None, "tur bitti, kutu hâlâ dolu"

    gorulen: list = []
    wd._PAYLASIM.olaylar = [{"event": "ana-iplik"}]
    try:
        t = threading.Thread(target=lambda: gorulen.append(getattr(wd._PAYLASIM, "olaylar", None)))
        t.start()
        t.join()
    finally:
        wd._PAYLASIM.olaylar = None
    assert gorulen == [None], "paylaşım ipliği aştı — başka bir ipliğin turu bayat defter görebilir"


# =================================================================================================
# 2) /api/diagnostics TTL ÖNBELLEĞİ — bayatlık SINIRLI ve BEYANLI
# =================================================================================================
@pytest.fixture
def istemci(sentetik_defter, monkeypatch):
    from fastapi.testclient import TestClient
    monkeypatch.setattr(api, "DASH_TOKEN", "")
    api._DIAG_CACHE.clear()          # süreç-içi kutu testler arası taşınmasın
    with TestClient(api.app) as c:
        yield c
    api._DIAG_CACHE.clear()


@pytest.fixture
def hesap_sayaci(monkeypatch):
    """Gövdenin KAÇ KEZ sonuna kadar koştuğunu sayar (önbelleğe yazan tek nokta)."""
    n = {"k": 0}
    _orig = api._diag_onbellege_yaz

    def _sayan(yuk):
        n["k"] += 1
        return _orig(yuk)

    monkeypatch.setattr(api, "_diag_onbellege_yaz", _sayan)
    return n


def test_iki_ardisik_istek_TEK_hesap_yapar(istemci, hesap_sayaci):
    """Panonun `refreshStatus` turu bu ucu 15 sn'de bir çağırıyor. İki ardışık istek tek hesap."""
    a = istemci.get("/api/diagnostics")
    b = istemci.get("/api/diagnostics")
    assert a.status_code == 200 and b.status_code == 200, (a.text[:200], b.text[:200])
    assert hesap_sayaci["k"] == 1, "ikinci istek de tam teşhisi yeniden hesapladı"
    assert a.json()["hud"] == b.json()["hud"], "önbellekten gelen yük ilkiyle aynı değil"


def test_yanit_BAYATLIGINI_beyan_eder(istemci):
    """Önbellekli bir sayıyı taze gibi göstermek bu deponun kovaladığı kusur sınıfıdır: yanıt
    hesabın ANINI (`hesaplama_ts`) ve bu isteğin hesaplayıp hesaplamadığını (`onbellekten`) söyler."""
    ilk = istemci.get("/api/diagnostics").json()
    assert ilk["onbellekten"] is False and isinstance(ilk["hesaplama_ts"], str)
    assert ilk["hesaplama_ts"].endswith("+00:00"), "damga UTC değil — pano yaşı yanlış hesaplar"

    ikinci = istemci.get("/api/diagnostics").json()
    assert ikinci["onbellekten"] is True
    assert ikinci["hesaplama_ts"] == ilk["hesaplama_ts"], \
        "önbellekten gelen yanıt YENİ bir hesap anı iddia ediyor"


def test_ic_yas_alanlari_ZARFLA_birlikte_yaslanir(istemci):
    """HİÇBİR ALAN, İÇİNDE BULUNDUĞU ZARFTAN TAZE OLDUĞUNU İDDİA EDEMEZ. `integrity_age_s` ve
    `alarm_butcesi.yas_s` hesaplandıkları anın yaşını taşır; 30 saniyelik bir kopyada bu sayılar
    30 saniye BÜYÜMÜŞ olmalı — yoksa pano 40 saniyelik bir raporu 'bu istekte hesaplandı' okur."""
    ilk = istemci.get("/api/diagnostics").json()
    anahtar = str(config.STATE)
    yuk, at = api._DIAG_CACHE[anahtar]
    api._DIAG_CACHE[anahtar] = (yuk, at - 30.0)          # kutuyu 30 saniye geriye al

    bayat = istemci.get("/api/diagnostics").json()
    assert bayat["onbellekten"] is True, "30 sn TTL içindedir, yeniden hesaplanmamalıydı"
    assert bayat["integrity_age_s"] >= ilk["integrity_age_s"] + 29.5, \
        f"bütünlük yaşı zarfla yaşlanmadı ({ilk['integrity_age_s']} → {bayat['integrity_age_s']})"
    assert bayat["alarm_butcesi"]["yas_s"] >= ilk["alarm_butcesi"]["yas_s"] + 29.5, \
        "alarm bütçesi yaşı zarfla yaşlanmadı"


def test_TTL_dolunca_YENIDEN_hesaplanir(istemci, hesap_sayaci):
    istemci.get("/api/diagnostics")
    anahtar = str(config.STATE)
    yuk, at = api._DIAG_CACHE[anahtar]
    api._DIAG_CACHE[anahtar] = (yuk, at - (api.DIAG_TTL_S + 1))

    taze = istemci.get("/api/diagnostics").json()
    assert hesap_sayaci["k"] == 2, "TTL dolduğu hâlde bayat kopya servis edildi"
    assert taze["onbellekten"] is False


def test_ZORLA_TAZELE_yolu_onbellegi_atlar(istemci, hesap_sayaci):
    """Önbellek, teşhis ucunu teşhis edilemez yapmamalı: operatör bir düzeltmenin canlıya
    değdiğini 45 saniye beklemeden görebilmeli."""
    istemci.get("/api/diagnostics")
    zorla = istemci.get("/api/diagnostics?taze=1").json()
    assert hesap_sayaci["k"] == 2 and zorla["onbellekten"] is False, "?taze=1 önbelleği atlamadı"


def test_onbellek_anahtari_STATE_icerir(istemci):
    """`alarm_budget_cached` emsali ve aynı gerekçe: ölçüm/test yolları kum havuzuna yönleniyor.
    Anahtarsız bir süreç-içi kutu, kum havuzuna CANLI defterin sayılarını servis ederdi."""
    istemci.get("/api/diagnostics")
    assert list(api._DIAG_CACHE) == [str(config.STATE)], \
        f"önbellek anahtarı state yönlendirmesini görmüyor: {list(api._DIAG_CACHE)}"


def test_TTL_pano_kadansiyla_ve_TESPIT_penceresiyle_uyumlu():
    """TTL keyfi bir sayı değil, iki ölçülmüş kadansın arasındaki aralıktır:
      * ALT SINIR — pano bu ucu 15 sn'de bir çağırıyor (app.js `refreshStatus`); TTL en az iki
        anketi kurtaracak kadar uzun olmalı, yoksa düzeltme neredeyse hiçbir şey kazandırmaz.
      * ÜST SINIR — bu uçtan okunan en dar tespit penceresi `watchdog.EXPECTED`in en küçüğüdür
        (30 dk). TTL onun %10'unu geçemez: geçseydi önbellek bir mekanizma durmasını gizleyebilirdi.
    """
    assert 30.0 <= api.DIAG_TTL_S <= 60.0, "TTL beyan edilen pencerenin dışında"
    en_dar = min(wd.EXPECTED.values())
    assert api.DIAG_TTL_S <= 0.10 * en_dar, \
        f"TTL en dar tespit penceresinin ({en_dar} sn) %10'unu aşıyor — bayatlık teşhisi gizler"
    # İçerideki iki TTL'i de aşmalı, yoksa zarf onlardan önce dolar ve düzeltme etkisiz kalır.
    assert api.DIAG_TTL_S >= wd.INTEGRITY_TTL_S and api.DIAG_TTL_S >= wd.ALARM_TTL_S


# =================================================================================================
# 2b) KONTROL EYLEMLERİ ZARFI DÜŞÜRÜR — ama YALNIZ başarılı olanlar
# =================================================================================================
def test_HALT_sonrasi_ilk_teshis_ONBELLEKTEN_gelmez(istemci, hesap_sayaci):
    """ÖNBELLEĞİN EN PAHALI HATASI: operatör HALT'a basar, Operasyon sayfası 45 saniye boyunca
    `hud.halted: false` gösterir, operatör düğmenin çalışmadığını sanıp ikinci kez basar. Kontrol
    eylemi zarfı düşürür; DEVAM (resume) da aynı yoldan geçer."""
    ilk = istemci.get("/api/diagnostics").json()
    assert ilk["hud"]["halted"] is False and hesap_sayaci["k"] == 1

    r = istemci.post("/api/halt")
    assert r.status_code == 200, r.text[:200]
    sonraki = istemci.get("/api/diagnostics").json()
    assert sonraki["onbellekten"] is False, "HALT'tan sonra bayat zarf servis edildi"
    assert sonraki["hud"]["halted"] is True, "pano operatörün KENDİ eylemini göremiyor"
    assert hesap_sayaci["k"] == 2

    istemci.post("/api/resume")
    devam = istemci.get("/api/diagnostics").json()
    assert devam["onbellekten"] is False and devam["hud"]["halted"] is False


def test_BASARISIZ_kontrol_istegi_onbellegi_DUSURMEZ(istemci, hesap_sayaci):
    """Geçersizleştirme kendi çözdüğü sorunu geri getirmemeli: reddedilen her tıklama zarfı
    düşürseydi, her başarısız istek bir TAM teşhis hesabı tetiklerdi. İki başarısızlık biçimi de
    sınanır — 200 + `{"ok": false}` (kanal yok) ve 4xx (L0'da onay yasağı)."""
    istemci.get("/api/diagnostics")
    assert hesap_sayaci["k"] == 1

    r = istemci.post("/api/notify/test")           # kanal yapılandırılmamış → ok:false, yan etki YOK
    assert r.status_code == 200 and r.json()["ok"] is False, r.text[:200]
    assert istemci.get("/api/diagnostics").json()["onbellekten"] is True, \
        "başarısız (ok:false) istek zarfı düşürdü — gereksiz tam hesap tetiklenir"

    r = istemci.post("/api/approvals/YOK", json={"decision": "approve"})
    assert r.status_code == 403, f"L0'da onay ucu açık kalmış: {r.status_code}"
    assert istemci.get("/api/diagnostics").json()["onbellekten"] is True, "4xx istek zarfı düşürdü"
    assert hesap_sayaci["k"] == 1, "hiçbir başarılı eylem yokken yeniden hesap yapıldı"


def _mutasyon_rotalari() -> list[tuple[str, str, str]]:
    """(yol, fonksiyon adı, gövde kaynağı) — api.py'deki her POST/DELETE ucu, kaynaktan türetilir."""
    import ast
    import pathlib
    kok = pathlib.Path(__file__).resolve().parent.parent
    src = (kok / "meridian" / "api.py").read_text()
    agac = ast.parse(src)
    out = []
    for n in ast.walk(agac):
        if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for d in n.decorator_list:
            f = getattr(d, "func", None)
            if (isinstance(f, ast.Attribute) and f.attr in ("post", "delete")
                    and isinstance(getattr(f, "value", None), ast.Name) and f.value.id == "app"
                    and d.args and isinstance(d.args[0], ast.Constant)):
                out.append((str(d.args[0].value), n.name, ast.get_source_segment(src, n) or ""))
    return out


def test_ENVANTER_EKSIKSIZ_her_mutasyon_rotasi_ya_cagirir_ya_BEYANLI_disaridadir():
    """Envanter bir YORUM olarak kalırsa yarın eklenen bir kontrol ucu sessizce dışarıda kalır ve
    pano o eylemi 45 saniye görmez — bu turun kapattığı kusurun aynısı, yeni bir kapıdan. Nail:
    her POST/DELETE ucu YA yardımcıyı çağırır YA da muafiyeti yardımcının envanterinde YAZILIDIR."""
    muaf = {"/api/login", "/api/logout", "/api/setup-password",   # oturum kimliği: teşhis yükünde yok
            "/api/hermes/pool_key",                               # anahtar hermes CLI havuzuna gider
            "/api/control/halt"}                                  # /api/halt-/api/resume'a DELEGE eder
    envanter = inspect.getdoc(api._diag_onbellek_bosalt) or ""
    assert "ENVANTER" in envanter and "ENVANTER DIŞI" in envanter, "envanter yorumu kaybolmuş"

    rotalar = _mutasyon_rotalari()
    assert len(rotalar) >= 20, f"rota tarayıcısı bozuk, yalnız {len(rotalar)} uç buldu"
    eksik = [yol for yol, _ad, govde in rotalar
             if "_diag_onbellek_bosalt(" not in govde and yol not in muaf]
    assert not eksik, f"bu kontrol uçları teşhis zarfını düşürmüyor ve muafiyetleri beyanlı değil: {eksik}"
    for yol in muaf:
        assert yol in envanter, f"{yol} muafiyeti envanterde GEREKÇESİZ — sessiz muafiyet yok"


# =================================================================================================
# 3) SÜREÇ HAVUZU KİBARLIĞI — canlıda pano API'sini boğan yükün kalıcı çözümü
# =================================================================================================
def test_havuz_iscileri_NICE_ile_dogar():
    """Canlı olay: iki işçi iki saat %99,9 CPU'da koştu, `/api/diagnostics` 8,8-10,4 sn'ye çıktı,
    operatör elle `renice` attı. Kalıcısı: işçi AĞIR işe (dataset yüklemesi) başlamadan ÖNCE
    nice'lanır — sonra nice'lansaydı en pahalı ilk görev yine tam öncelikle koşardı."""
    src = inspect.getsource(reflect._pool_worker_init)
    assert "os.nice(15)" in src, "havuz işçileri hâlâ ebeveynle aynı öncelikte doğuyor"
    assert src.index("os.nice(15)") < src.index("load_cached"), \
        "nice, dataset yüklemesinden SONRA atanıyor — en pahalı ilk görev kibarlaşmıyor"


@pytest.mark.parametrize("cpu,beklenen4,beklenen3", [(1, 1, 1), (2, 1, 1), (3, 1, 1),
                                                     (4, 2, 2), (6, 4, 3), (16, 4, 3)])
def test_isci_tavani_cpu_eksi_iki(monkeypatch, cpu, beklenen4, beklenen3):
    """`max(1, cpu-2)`: bir çekirdek uvicorn'a, bir çekirdek işlem döngüsü/hermes ipliğine kalır.
    ESKİ HÂL `max(2, ...)` tabanı 2'ye çiviliyordu — 2 çekirdekli bir makinede tavan HİÇ YOKTU.
    Çağıranın kendi tavanı (incumbent kolunda 3) korunur: kibarlaştırma yükü ARTIRMAZ."""
    monkeypatch.setattr(os, "cpu_count", lambda: cpu)
    assert reflect._havuz_tavani(4) == beklenen4
    assert reflect._havuz_tavani(3) == beklenen3
    assert reflect._havuz_tavani(4) >= 1, "sıfır işçili havuz açılamaz"


def test_IKI_havuz_da_tavani_kullanir():
    """Sonda havuzu ile incumbent ön-hesap havuzu AYNI çekirdekleri paylaşıyor; biri kibarlaşıp
    diğeri kibarlaşmasaydı boğulma yalnız yer değiştirirdi."""
    for fn in (reflect._parallel_prefill_probes, reflect.prefill_incumbents):
        src = inspect.getsource(fn)
        assert "_havuz_tavani(" in src, f"{fn.__name__} işçi tavanını kullanmıyor"
        assert "max(2, min(4," not in src, f"{fn.__name__} eski 2'lik tabanı geri getirmiş"
        assert "initializer=_pool_worker_init" in src, f"{fn.__name__} işçileri nice'sız doğuyor"
