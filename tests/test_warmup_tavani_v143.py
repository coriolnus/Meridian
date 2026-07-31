"""test_warmup_tavani_v143.py — ISINMA SPRİNTİ SÜRE TAVANI + POLL AÇLIĞI (WP-H/H11, 2026-07-31).

VAKA (ölçülmüş, uydurulmamış). `hermes_runtime._warmup_sprint`, `reflect.coordinate_descent_search`i
hermes bekleme döngüsünün KENDİ iş parçacığında koşturur ve nominal süresi 1-5 SAATtir. Bu süre
boyunca iki şey birden bozuluyordu:

  AÇLIK  — döngü bir sonraki tura dönemediği için `watchdog.beat("hermes_poll")` atılmıyordu.
           Bekçinin `hermes_poll` penceresi 30 DAKİKA. Yani ısınma her koştuğunda MECHANISM_STALE
           doğuyordu: mekanizma ölü değil MEŞGULdü. Sahte alarmın maliyeti gerçek alarmdan yüksektir
           — operatörü alarm okumamaya eğitir.
  ÇARESİZLİK — 8 saati aşan bir ısınmada bekçinin elinde ALARM'dan başka araç yoktu; İPTAL edemiyordu.

BU DOSYA ÜÇ ŞEYİ KİLİTLER:
  1. Tavan tetiklenir ve arama KİBARCA kesilir (biten sondalarla döner, kesinti damgalanır, olay
     YASA 4 gerekçesiyle yazılır).
  2. Isınma her sondada İKİ nabız atar (`warmup_sprint` + `hermes_poll`) — açlık biter.
  3. TAVANSIZ yol DAVRANIŞ-DEĞİŞMEZ: tavan verilmeyen her çağrı bugünkü sonucu birebir üretir
     (yeni bir varsayılan tavan SESSİZCE devreye girmez — sessiz bir varsayılan, aramayı hiç
     kimsenin istemediği bir yerde keserdi).
"""
from __future__ import annotations

import shutil
import time
from pathlib import Path

import pytest

from meridian import config, hermes_runtime, reflect, store, watchdog
from tests import wf_fixtures as wf


@pytest.fixture
def seeded_sandbox(sandbox_state):
    """sandbox_state + goal.yaml/bounds.yaml (test_sprint.py ile AYNI desen)."""
    repo_state = Path(__file__).resolve().parent.parent / "state"
    for f in ("goal.yaml", "bounds.yaml"):
        shutil.copy2(repo_state / f, sandbox_state / f)
    config.goal.cache_clear()
    config.bounds.cache_clear()
    return sandbox_state


def _wf(oos, folds):
    return wf.wf_from_scores(oos, folds=folds, holdout=oos)


_DUZ = [(30, 0.2), (30, 0.2), (30, 0.2)]


def _arama_stub(monkeypatch, *, sonda_saniye: float = 0.0):
    """incumbent + her sonda için sahte walk_forward. `sonda_saniye` YAVAŞ SONDA taklididir:
    gerçek bir walk-forward dakikalar sürer; tavanı ölçmek için o dakikaları BEKLEMEYİZ, aynı
    şekli çok daha kısa bir uyku ile üretiriz (bekleme betiği YASAĞInın test karşılığı: süreyi
    beklemek yerine süreyi TAKLİT et)."""
    def fake_wf(params, bars, index, goal, *a, **kw):
        if sonda_saniye and int(kw.get("strategy_version", 1)) != 1:
            time.sleep(sonda_saniye)
        return _wf(0.10, _DUZ)

    monkeypatch.setattr(reflect.backtest, "walk_forward", fake_wf)
    monkeypatch.setattr(reflect.dataset, "load", lambda **k: (None, None))
    monkeypatch.delenv("MERIDIAN_PARALLEL_PROBES", raising=False)
    reflect.clear_wf_caches()
    reflect._PROBE_CACHE.clear()


# =================================================================================================
# 1) TAVAN TETİKLENİR → KİBAR-İPTAL
# =================================================================================================
def test_tavan_asilinca_arama_kibarca_kesilir(seeded_sandbox, monkeypatch):
    """Tavan aşıldığında arama DURUR, biten sondalarla döner ve kesintiyi DAMGALAR.

    Beklenti üç parçalı ve üçü de ayrı bir kusur sınıfını kapatır:
      * `kesildi/sebep` — kesinti GÖRÜNÜR (sessiz kesinti, kısa aramadan ayırt edilemez).
      * `evaluated < planlanan_sonda` — gerçekten erken çıkıldı (tavan bir süsleme değil).
      * istisna YOK — "kibar" iptalin anlamı budur: çağıran normal bir sonuç sözlüğü alır."""
    _arama_stub(monkeypatch, sonda_saniye=0.12)
    res = reflect.coordinate_descent_search(None, None, config.goal(), windows=None,
                                            k_max=2, budget=8, max_minutes=0.25 / 60.0)
    assert res["kesildi"] is True
    assert res["sebep"] == "sure_tavani"
    assert res["planlanan_sonda"] > res["evaluated"] >= 0
    # `kalan_sonda` = döngünün HİÇ ULAŞMADIĞI sonda. `planlanan - evaluated` ile aynı OLMAK ZORUNDA
    # DEĞİL: aradaki fark `skipped_wallclock`tur (ulaşıldı ama taze hesap atlandı). Muhasebe bu üç
    # sayının TOPLAMI üzerinden kurulur — ikisini eşitleyen bir iddia, atlama yolunun devreye
    # girdiği ilk gün sahte bir kırmızı verirdi.
    assert res["kalan_sonda"] + res["evaluated"] + res["skipped_wallclock"] == res["planlanan_sonda"]
    assert res["gecen_dk"] is not None and res["tavan_dk"] is not None


def test_kesinti_yasa4_gerekcesiyle_deftere_yazilir(seeded_sandbox, monkeypatch):
    """YASA 4: kesinti SESSİZ olamaz. Olay `events.jsonl`e düşer ve ≥20 karakter gerekçe taşır.

    Neden gerekçe zorunlu: "search_sure_tavani_kesildi" tek başına NE olduğunu söyler, NEDEN
    önemli olduğunu söylemez. Altı ay sonra defteri okuyan (belki de aynı kişi) 'bu kesinti
    sonucu bozdu mu?' diye soracak; cevabın olay satırının İÇİNDE olması gerekir."""
    _arama_stub(monkeypatch, sonda_saniye=0.12)
    reflect.coordinate_descent_search(None, None, config.goal(), windows=None,
                                      k_max=2, budget=8, max_minutes=0.25 / 60.0)
    olaylar = [e for e in store.read_jsonl("events.jsonl")
               if e.get("event") == "search_sure_tavani_kesildi"]
    assert olaylar, "kesinti olayı defterde YOK — sessiz kesinti YASA 4 ihlalidir"
    o = olaylar[-1]
    assert len(str(o.get("detail", ""))) >= 20
    assert o.get("kalan_sonda", 0) >= 1 and o.get("gecen_dk") is not None


def test_deadline_ts_de_ayni_tavani_kurar(seeded_sandbox, monkeypatch):
    """İki kol AYNI yasayı sürer: `max_minutes` (göreli) ve `deadline_ts` (mutlak). Çağıranın
    zaten bir son-tarihi varsa (ör. bakım penceresi) onu dakikaya çevirip geri çevirmek zorunda
    kalmamalı — yuvarlama, tavanın ne yana kaydığını belirsizleştirirdi."""
    _arama_stub(monkeypatch, sonda_saniye=0.12)
    res = reflect.coordinate_descent_search(None, None, config.goal(), windows=None,
                                            k_max=2, budget=8, deadline_ts=time.time() + 0.25)
    assert res["kesildi"] is True and res["sebep"] == "sure_tavani"


def test_kesilen_arama_kapiyi_gecen_adayi_COPE_ATMAZ(seeded_sandbox, monkeypatch):
    """Kibar-iptal, o ana dek KAZANILMIŞ bilgiyi korur: kapıyı geçmiş bir aday varsa `best`
    dolu döner. Kesintinin aramayı sıfırlaması, saatlerce koşan bir hesabı çöpe atmak olurdu."""
    def fake_wf(params, bars, index, goal, *a, **kw):
        if int(kw.get("strategy_version", 1)) == 1:
            return _wf(0.10, _DUZ)
        time.sleep(0.12)
        return _wf(0.30, [(30, 0.5), (30, 0.5), (30, 0.5)])     # gerçek kenar → kapıyı geçer

    monkeypatch.setattr(reflect.backtest, "walk_forward", fake_wf)
    monkeypatch.setattr(reflect.dataset, "load", lambda **k: (None, None))
    monkeypatch.delenv("MERIDIAN_PARALLEL_PROBES", raising=False)
    reflect.clear_wf_caches()
    reflect._PROBE_CACHE.clear()
    res = reflect.coordinate_descent_search(None, None, config.goal(), windows=None,
                                            k_max=2, budget=8, max_minutes=0.30 / 60.0)
    assert res["kesildi"] is True
    assert res["evaluated"] >= 1 and res["best"] is not None


# =================================================================================================
# 2) TAVANSIZ YOL DAVRANIŞ-DEĞİŞMEZ
# =================================================================================================
def test_tavansiz_yol_davranis_degismez(seeded_sandbox, monkeypatch):
    """Tavan VERİLMEZSE hiçbir tavan yoktur — sessiz bir varsayılan devreye GİRMEZ.

    Bu, geriye dönük uyumun kendisi: `search_and_submit`, sprint ve mevcut testler bu fonksiyonu
    tavansız çağırır ve hepsi bugünkü davranışı bekler. Sessiz bir varsayılan tavan, canlı bir
    yansımayı hiç kimsenin istemediği bir noktada keserdi ve bunu yalnız defter söylerdi."""
    _arama_stub(monkeypatch)
    res = reflect.coordinate_descent_search(None, None, config.goal(), windows=None,
                                            k_max=1, budget=3)
    assert res["kesildi"] is False
    assert "sebep" not in res and "kalan_sonda" not in res
    assert res["evaluated"] == res["planlanan_sonda"] == 3


def test_bol_tavan_hicbir_seyi_kesmez(seeded_sandbox, monkeypatch):
    """Tavan VAR ama bol: sonuç tavansız koşumla BİREBİR aynı olmalı. Tavanın yalnız varlığının
    bile sonucu değiştirdiği bir uygulama, ölçümü koşum ayarına bağımlı yapardı."""
    _arama_stub(monkeypatch)
    tavansiz = reflect.coordinate_descent_search(None, None, config.goal(), windows=None,
                                                 k_max=1, budget=3)
    reflect.clear_wf_caches()
    reflect._PROBE_CACHE.clear()
    bol = reflect.coordinate_descent_search(None, None, config.goal(), windows=None,
                                            k_max=1, budget=3, max_minutes=60)
    assert bol["kesildi"] is False
    for alan in ("evaluated", "cleared", "planlanan_sonda", "incumbent_oos"):
        assert bol[alan] == tavansiz[alan], f"bol tavan {alan} alanını değiştirdi"


# =================================================================================================
# 3) POLL AÇLIĞI: ISINMA SONDADAN SONDAYA NABIZ ATAR
# =================================================================================================
def test_isinma_her_sondada_iki_nabiz_atar(seeded_sandbox, monkeypatch):
    """AÇLIĞIN KAPANIŞI: ısınma koşarken `hermes_poll` nabzı da atılır.

    Düzeltmeden önce nabız YALNIZ ısınma bittikten sonra atılıyordu ve 1-5 saatlik bir boşluk
    30 dk'lık pencereyi kaçınılmaz olarak deliyordu. Test, nabzın ısınmanın İÇİNDEN — yani sondalar
    sürerken — atıldığını ölçer: sonda sayısı kadar (artı tur sonu) nabız beklenir."""
    _arama_stub(monkeypatch)
    nabizlar: list[str] = []
    monkeypatch.setattr(watchdog, "beat", lambda ad: nabizlar.append(ad))
    monkeypatch.setattr(hermes_runtime.store, "read_jsonl", lambda *a, **k: [])
    monkeypatch.setattr(reflect, "prefill_incumbents", lambda *a, **k: {"computed": 0, "cached": 0})
    monkeypatch.setenv("HERMES_WARMUP_BUDGET", "3")

    hermes_runtime._warmup_sprint()

    n_sonda = int((hermes_runtime._state.get("last_warmup") or {})["evaluated"])
    assert n_sonda >= 2, "stub yeterli sonda üretmedi — testin kendisi ölçüm yapamaz"
    # SAYIM TAM: plan olayı (i=0) + her sonda + tur sonu = sonda + 2. Ölçüm ">= 2" gibi gevşek
    # bırakılsaydı yalnız tur sonunda atılan ESKİ davranış da geçerdi (1 nabız + 1 plan = 2) —
    # yani test, kapatmak için yazıldığı kusura kör olurdu.
    assert nabizlar.count("hermes_poll") == n_sonda + 2, \
        f"nabız sondalarla İLERLEMİYOR — poll açlığı sürüyor ({nabizlar})"
    assert nabizlar.count("warmup_sprint") == n_sonda + 2
    assert set(nabizlar) == {"hermes_poll", "warmup_sprint"}


def test_isinma_kesintisi_panoya_tasinir(seeded_sandbox, monkeypatch):
    """Kesinti hermes_status'a YAZILIR: "3 sonda değerlendi" ile "10 sondanın 3'ü değerlendi,
    kalanı kesildi" aynı karta yazılamaz — ikincisi eksik bir ölçümdür ve okuyucu bunu bilmeli."""
    _arama_stub(monkeypatch, sonda_saniye=0.12)
    monkeypatch.setattr(hermes_runtime.store, "read_jsonl", lambda *a, **k: [])
    monkeypatch.setattr(reflect, "prefill_incumbents", lambda *a, **k: {"computed": 0, "cached": 0})
    monkeypatch.setenv("HERMES_WARMUP_BUDGET", "8")
    monkeypatch.setenv("HERMES_WARMUP_MAX_MIN", str(0.25 / 60.0))

    hermes_runtime._warmup_sprint()

    lw = hermes_runtime._state.get("last_warmup") or {}
    assert lw.get("kesildi") is True and lw.get("sebep") == "sure_tavani"
    assert lw.get("kalan_sonda", 0) >= 1
    assert "error" not in lw, f"kibar iptal İSTİSNA gibi kaydedildi: {lw}"


def test_isinma_asla_dongu_kirmaz(seeded_sandbox, monkeypatch):
    """Isınma sözleşmesi değişmedi: veri/ağ hatası döngüyü ASLA kırmaz — istisna yutulur ve
    `last_warmup.error` olarak kaydedilir (sessiz değil, ama ölümcül de değil)."""
    monkeypatch.setattr(reflect.dataset, "load",
                        lambda **k: (_ for _ in ()).throw(RuntimeError("veri yok")))
    hermes_runtime._warmup_sprint()
    assert (hermes_runtime._state.get("last_warmup") or {}).get("error") == "RuntimeError"


# =================================================================================================
# 4) TAVAN KOLU: BOZUK/SIFIR DEĞER SESSİZCE KADANSI ÖLDÜRMEZ
# =================================================================================================
def test_tavan_kolu_varsayilani_5_saattir(monkeypatch):
    """Varsayılan 300 dk = 5 sa — ısınmanın NOMİNAL üst bandı. Tavan bir kısıtlama değil anomali
    sınırıdır: nominal bandın içindeki hiçbir koşum kesilmez."""
    monkeypatch.delenv("HERMES_WARMUP_MAX_MIN", raising=False)
    assert hermes_runtime._warmup_tavan_dk() == 300.0


@pytest.mark.parametrize("ham", ["abc", "", "   ", "0", "-5"])
def test_bozuk_veya_sifir_tavan_varsayilana_doner_ve_uyarir(seeded_sandbox, monkeypatch, ham):
    """SESSİZCE 0'A DÜŞMEK EN TEHLİKELİ HÂL: 0 tavan HER ısınmayı anında keserdi, ısınma kadansı
    ölürdü ve bekçi bile göremezdi (nabız atılmaya devam ederdi). Bozuk/sıfır değer varsayılana
    döner VE adıyla uyarılır — 'tavan yok' istemenin doğru kolu MERIDIAN_WARMUP_SPRINTS=0'dır."""
    monkeypatch.setenv("HERMES_WARMUP_MAX_MIN", ham)
    assert hermes_runtime._warmup_tavan_dk() == 300.0
    if ham.strip():                      # boş dizge yapılandırılmamışla aynıdır — uyarı gerekmez
        uyari = [e for e in store.read_jsonl("events.jsonl")
                 if e.get("event") == "hermes_warmup_max_min_gecersiz"]
        assert uyari, f"bozuk tavan değeri ({ham!r}) sessizce yutuldu"


def test_env_kolu_calisma_aninda_okunur(monkeypatch):
    """Modül YÜKLENİRKEN dondurulmuş bir env, operatör kolunu sahte yapardı: değer değişir, davranış
    değişmez, kimse nedenini bulamaz. Kol her çağrıda okunur."""
    monkeypatch.setenv("HERMES_WARMUP_MAX_MIN", "42")
    assert hermes_runtime._warmup_tavan_dk() == 42.0
    monkeypatch.setenv("HERMES_WARMUP_MAX_MIN", "7.5")
    assert hermes_runtime._warmup_tavan_dk() == 7.5


# =================================================================================================
# 5) BEKÇİ EŞİĞİ 8 SAATTE KALIR — VE ARTIK GERÇEK ANOMALİ ÖLÇER
# =================================================================================================
def test_bekci_esikleri_degismedi():
    """H11 eşikleri DEĞİŞTİRMEZ, ANLAMLARINI değiştirir. `warmup_sprint` 8 sa kalır: tavan 5 saatte
    kestiğine göre 8 saatlik sessizlik artık 'uzun sürdü' olamaz, yalnız 'tavan çalışmadı' olabilir.
    `hermes_poll` 30 dk kalır: ısınma artık nabız attığına göre pencereyi genişletmek gerekmez —
    genişletmek gerçekten ölmüş bir ipliği saatlerce görünmez kılardı."""
    assert watchdog.EXPECTED["warmup_sprint"] == 8 * 3600
    assert watchdog.EXPECTED["hermes_poll"] == 30 * 60
    # Tavan (dk) bekçi eşiğinin (sa) ALTINDA olmalı — üstünde olsaydı tavan hiç iş görmeden bekçi
    # alarm verirdi ve H11'in tüm gerekçesi ortadan kalkardı.
    assert hermes_runtime.WARMUP_MAX_MIN_DEFAULT * 60 < watchdog.EXPECTED["warmup_sprint"]
