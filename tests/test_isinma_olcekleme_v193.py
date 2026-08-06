"""test_isinma_olcekleme_v193.py — ISINMA SPRİNTİ OTO-ÖLÇEKLEMESİ (operatör ops-kuralı, 2026-08-06).

CANLI OLGU. `warmup_sprint` her ~4,4 saatte bir koşuyor ve serisi `evaluated 10→20→30,
cleared: 0, best: null`. Bütçe SABİTTİ (`hermes_runtime._warmup_sprint` içinde
`HERMES_WARMUP_BUDGET` varsayılanı 10) — yani "hiçbir aday kapıyı geçemedi" olgusu bir sonraki
koşumun HİÇBİR ŞEYİNİ değiştirmiyordu: mekanizma aynı duvara aynı hızla, süresiz çarpıyordu.

YASA (deterministik ops kuralı — ÖLÇÜM DEĞİL, kart gerekmez):
    cleared == 0  → çarpan ×2 (tavana kadar) + k_max bir kademe
    cleared  > 0  → çarpan TABANA döner + k_max tabana döner
    kesildi       → çarpan BÜYÜMEZ; bir kademe geri iner ve o seviye DUVAR olur

TAVAN NEDEN ÖLÇÜLÜR, YAZILMAZ: brief'in tavanı "H11 süre-tavanı içinde kalan maksimum"dur ve o
sayı makineye/veri boyutuna/önbellek sıcaklığına bağlıdır. Buraya bir sayı yazmak, düzeltmeye
çalıştığımız "sabit sihirli tavan" sınıfını geri getirirdi. Süre tavanına takılan koşumun KENDİSİ
o makinede "fazla"nın ölçümüdür; `WARMUP_SCALE_MAX` yalnız mutlak emniyet bandıdır.

DÜRÜST BEYAN (ölçüldü, yerel defter n=353 sonda): sondaların %36'sı incumbent'tan yüksek OOS
üretti ama yalnız 6'sı TAM kapıyı geçti — `cleared: 0`ın bağlayıcı kısıtı "aday yok" DEĞİL kapıdır,
üstelik K = planlanan toplam sonda olduğu için bütçeyi büyütmek kapıyı SIKAR. Bu kuralın ölçülmüş
faydası `cleared` değil KAPSAMA'dır (UCB öncelikleri + sonda önbelleği; ısınma hiçbir şey ship etmez).
"""
import pytest

from meridian import hermes, hermes_runtime, reflect, store


def _sc(cleared=0, evaluated=10, kesildi=False):
    return {"cleared": cleared, "evaluated": evaluated, "kesildi": kesildi}


def _events(event: str) -> list:
    return [r for r in store.read_jsonl("events.jsonl") if r.get("event") == event]


@pytest.fixture(autouse=True)
def _temiz_kol(monkeypatch):
    """Env kolları HER testte bilinen hâlde: taban ölçümü operatörün kabuğundan miras alınamaz."""
    monkeypatch.delenv("HERMES_WARMUP_BUDGET", raising=False)


# --------------------------------------------------------------------- 1) TABAN DAVRANIŞI KORUNUR
def test_taban_bugunku_davranisla_birebir(sandbox_state):
    """REGRESYON KAPISI: temiz durumda bütçe 10, k_max 2 — yani `_warmup_sprint`in bugüne kadarki
    sabitleri. Merdiven bir DAVRANIŞ DEĞİŞİKLİĞİYLE değil, bir olguyla (cleared=0) açılır."""
    wb = hermes.warmup_budget()
    assert (wb["budget"], wb["k_max"], wb["carpan"]) == (10, 2, 1)
    assert wb["taban_kaynagi"] == "varsayılan" and wb["duvar"] is None


def test_env_kolu_artik_taban_sabit_degil(sandbox_state, monkeypatch):
    """`HERMES_WARMUP_BUDGET` operatörün TABANI'dır: merdiven onun ÜSTÜNE çıkar, onu ezmez."""
    monkeypatch.setenv("HERMES_WARMUP_BUDGET", "4")
    assert hermes.warmup_budget()["budget"] == 4
    hermes.warmup_budget_feedback(_sc(cleared=0))
    wb = hermes.warmup_budget()
    assert wb["budget"] == 8 and wb["taban"] == 4 and wb["taban_kaynagi"] == "env:HERMES_WARMUP_BUDGET"


def test_search_budget_kolu_isinmaya_sizmaz(sandbox_state, monkeypatch):
    """AYRIKLIK ÇİVİSİ. Canlı birim `HERMES_SEARCH_BUDGET=8` taşır ve o değişken GERÇEK yansımanın
    (ship yetkili) arama tavanını besler. İkisini birleştirmek, ısınmanın tabanını bir dağıtım notu
    olmadan 10→8 kaydırırdı — davranışın sessizce değişmesi tam da avladığımız sınıf."""
    monkeypatch.setenv("HERMES_SEARCH_BUDGET", "8")
    assert hermes.warmup_budget()["budget"] == 10


# ------------------------------------------------------------------- 2) MERDİVEN: YUKARI VE GERİ
def test_cleared_sifir_butceyi_ve_kmaxi_bir_kademe_acar(sandbox_state):
    hermes.warmup_budget_feedback(_sc(cleared=0, evaluated=30))
    wb = hermes.warmup_budget()
    assert (wb["budget"], wb["k_max"], wb["carpan"]) == (20, 3, 2)
    ev = _events("warmup_budget_scaled")
    assert len(ev) == 1 and ev[0]["sebep"] == "cleared=0"
    assert ev[0]["butce_onceki"] == 10 and ev[0]["butce_yeni"] == 20
    assert ev[0]["k_max_onceki"] == 2 and ev[0]["k_max_yeni"] == 3
    assert len(ev[0]["detail"]) >= 20                                   # YASA 4


def test_merdiven_tavanda_durur(sandbox_state):
    """Sınırsız büyüme yok: ×8 mutlak emniyet bandıdır ve orada olay TEKRARLANMAZ (alarm hijyeni —
    değişmeyen bir durumu her turda yeniden ilan etmek defteri gürültüyle doldururdu)."""
    for _ in range(6):
        hermes.warmup_budget_feedback(_sc(cleared=0))
    wb = hermes.warmup_budget()
    assert wb["carpan"] == hermes.WARMUP_SCALE_MAX == 8 and wb["budget"] == 80
    assert wb["k_max"] == hermes.WARMUP_KMAX_MAX == 4, "k_max kendi tavanında durur"
    assert len(_events("warmup_budget_scaled")) == 3, "×2, ×4, ×8 — tavanda sessiz"


def test_ilk_clearing_tabana_dondurur(sandbox_state):
    """Geri dönüş ŞARTTIR: geniş tarama bir maliyettir ve gerekçesi ortadan kalktığı anda biter.
    Ayrıca K = planlanan sonda olduğu için geniş bir bütçe, temizleyen bir gecede kapıyı SIKARDI."""
    hermes.warmup_budget_feedback(_sc(cleared=0))
    hermes.warmup_budget_feedback(_sc(cleared=0))
    assert hermes.warmup_budget()["budget"] == 40
    hermes.warmup_budget_feedback(_sc(cleared=2))
    wb = hermes.warmup_budget()
    assert (wb["budget"], wb["k_max"], wb["carpan"]) == (10, 2, 1)
    assert _events("warmup_budget_scaled")[-1]["sebep"] == "cleared>0"


# ------------------------------------------------------------------------ 3) DUVAR: TAVAN ÖLÇÜLÜR
def test_sure_tavanina_takilan_kosum_duvari_civiler(sandbox_state):
    """H11 süre tavanına takılmak bir ÖLÇÜMDÜR: bu genişlik bu makinede pencereye sığmıyor.
    Merdiven bir kademe geri iner ve seviye DUVAR olur — sonraki cleared=0'lar onu AŞAMAZ."""
    hermes.warmup_budget_feedback(_sc(cleared=0))          # sonraki koşum ×2
    hermes.warmup_budget_feedback(_sc(cleared=0))          # sonraki koşum ×4
    hermes.warmup_budget_feedback(_sc(cleared=0, kesildi=True))   # ×4 koştu ve SIĞMADI
    wb = hermes.warmup_budget()
    # DUVAR, SIĞMAYAN SEVİYENİN BİR ALTIDIR: kesilen koşum ×4'tü, yani ölçüm "×4 fazla" der —
    # "×4 tam" değil. Duvarı sığmayan seviyeye koymak, her turda yarım ölçüm üretmek olurdu.
    assert wb["carpan"] == 2 and wb["duvar"] == 2
    assert _events("warmup_budget_scaled")[-1]["sebep"] == "sure_tavani"
    for _ in range(4):
        hermes.warmup_budget_feedback(_sc(cleared=0))
    assert hermes.warmup_budget()["carpan"] == 2, "duvar sonraki cleared=0 turlarında da tutar"


def test_olculemeyen_kosum_merdivene_dokunmaz(sandbox_state):
    """UYDURMA YASAĞI'nın bütçe tarafı: `_warmup_sprint` bir istisnayla düştüyse `cleared` YOKTUR —
    onu 0 sayıp bütçeyi büyütmek, bir arızayı bir bütçe kararına çevirmek olurdu."""
    hermes.warmup_budget_feedback(_sc(cleared=0))
    onceki = hermes.warmup_budget()["carpan"]
    for bozuk in (None, "hata", 42):
        hermes.warmup_budget_feedback(bozuk)
    assert hermes.warmup_budget()["carpan"] == onceki
    assert len(_events("warmup_budget_scaled")) == 1


# ---------------------------------------------------------------- 4) ISINMA GERÇEKTEN KOLU ÇEVİRİR
def test_isinma_sprinti_butceyi_merdivenden_alir_ve_sonucu_geri_isler(sandbox_state, monkeypatch):
    """YASA 6 (okuyucusuz yazım yok) ve zincir bütünlüğü: kural `hermes.py`de yaşıyor olabilir ama
    ısınma onu ÇAĞIRMIYORSA hiçbir şey değişmez. Bu test dikişi ölçer — hangi bütçe/k_max aramaya
    gitti ve koşumun sonucu merdivene işlendi mi."""
    gorulen: list = []

    def _sahte_arama(bars, index, *a, **kw):
        gorulen.append({"budget": kw.get("budget"), "k_max": kw.get("k_max")})
        return {"evaluated": 30, "cleared": 0, "best": None, "kesildi": False, "kalan_sonda": 0}

    monkeypatch.setattr(reflect, "coordinate_descent_search", _sahte_arama)
    monkeypatch.setattr(reflect.dataset, "load", lambda **k: (None, None))
    monkeypatch.setattr(reflect, "prefill_incumbents", lambda *a, **k: {"computed": 0, "cached": 0})
    monkeypatch.setattr(hermes_runtime.store, "read_jsonl", lambda *a, **k: [])

    hermes_runtime._warmup_sprint()
    assert gorulen == [{"budget": 10, "k_max": 2}], "ilk koşum TABANDAN başlar"
    assert hermes.warmup_budget()["budget"] == 20, "cleared=0 sonucu merdivene İŞLENMELİ"

    hermes_runtime._warmup_sprint()
    assert gorulen[-1] == {"budget": 20, "k_max": 3}, "ikinci koşum genişlemiş bütçeyle koşar"
    lw = hermes_runtime._state.get("last_warmup") or {}
    assert lw["butce"] == 20 and lw["butce_carpani"] == 2 and lw["k_max"] == 3, \
        "merdivenin hâli PANOYA taşınmalı — 'kural koşuyor mu' sorusu dosyaya bakmadan cevaplanmalı"
