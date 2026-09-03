"""KARNE HESABI — `goal.yaml`ın dört sorusuna deterministik cevap, LLM'siz — v337 (2026-08-30)

NEDEN BU ÇİVİLER VAR. `state/goal.yaml` dört soru soruyor (`target_return_30d`, `min_sharpe`,
`max_drawdown`, `failure_below`) ve bugüne dek hiçbir PERİYODİK teslimat onları cevaplamıyor.
`goal_failure` olayı defterde SIFIR kez düşmüş; sessizlik iki ayrı şey demektir — "deney hiç
başarısız olmadı" ve "hüküm hiç ölçülmedi" — ve bugün ikisi AYIRT EDİLEMİYOR. Bu dosyanın
taşıyıcı çivisi tam olarak o ayrımı yapısal kılar: ölçülemeyen hüküm `OLCULEMEDI` + neden döner,
iyi huylu bir sayı DEĞİL.

BU DOSYA CANLI DEFTERİ GÖREMEZ (ölçülen ≠ çıkarılan, açıkça). Buradaki hiçbir sayı A1'de
gözlenmiş değildir; fikstürler canlı defterin ŞEKLİNİ (`trades.jsonl` satır alanları — `ts_open`,
`ts_close`, `pnl_dollars`, `r_multiple` — `meridian.score` KAYNAK KODUNDAN okunarak) taklit eder,
DEĞERLERİNİ değil. Yani bu çiviler kuralı sınar, canlı davranışı DEĞİL. Yerel `state/` bu
oturumda test artefaktlarıyla kirlendiği ölçülmüştür; "canlıda kaç işlem var" sorusu A1'de
sorulur, burada değil.

DÖRT YAPISAL BULGU ve karşılıklarındaki çiviler:

  1. TEK-KAYNAK. `failure_below` hükmünün sahibi `meridian.watchdog.goal_failure_report`tır;
     karne onu ÇAĞIRIR, mantığını KOPYALAMAZ. Sharpe/drawdown/30g-getiri tanımı
     `meridian.score.score_detail`indir; karne oradan AYNEN alır. İki okumadan aynı gerçek
     (30 günlük getiri) iki farklı sayı çıkarsa ayrışma ÖLÇÜLÜR.

  2. PENCERE İŞLEM GÜNÜDÜR. `score.score_detail`in `realized_30d`si defterin KENDİ süresinden
     30 güne ÖLÇEKLENMİŞ bir orandır; defter 30 işlem gününden kısaysa o sayı bir ölçüm değil
     ekstrapolasyondur. Mesafe TAKVİM GÜNÜYLE ölçülemez — deponun kendi dersi
     (`loop._mutabakat_bayatligi`): cuma→pazartesi 3 takvim günü ama 1 işlem günüdür ve takvimle
     ölçen eşik her pazartesi öter. Takvim yoksa cevap YOKTUR (`trend_shadow.ay_sonu_mu`
     emsali: fail-closed None).

  3. TAZELİK (düzeltme dalgası, denetim MEDIUM-4). Motor üç ay önce durmuş olsa karne aynı
     hükmü her hafta GÜNCEL bir cevap gibi basardı — kardeş profilin (`@bekci`) avladığı
     "duran iş" sınıfının ta kendisi. Bayat defter hüküm doğurmaz; eşik YUVARLAK BİR SAYI
     DEĞİL, defterin KENDİ kadansından ve 30 günlük hüküm penceresinden türetilir.

  4. META-KAPILAR HÜKMÜ ANCAK CEVABI DEĞİŞTİREBİLECEKLERİ ZAMAN YUTAR (denetim MEDIUM-1).
     Ayrışma/bayatlık/kısa pencere `failed=False`u hükümsüz kılar; `failed=True`yu ASLA. Rapor
     katmanı alarm katmanından sessiz olamaz — modülün kendi beyanı buydu, kod bir turda onun
     tersini yapıyordu ve hiçbir çivi ısırmıyordu.

vNNN: v334 (bytecode) · v335/v336 (pencere) alınmıştı; bu dosya v337. Çakışma kontrolü koşuldu.


SÜRÜM NUMARASI v337 → v339 (2026-08-31): dosya v337 olarak yazıldı; aynı pencerede
PR #21 `tests/test_tahta_hijyeni_v337.py`yi main'e getirdi. vNNN bu depoda KİMLİKTİR;
çakışmada az-çapalı taraf taşınır (CLAUDE.md §2) — onlarınki push'lu ve PR+denetim
belgesiyle çapalı, bu yerel commit'ti. Bu oturumda İKİNCİ vNNN çakışması (ilki v331).
"""

import datetime as dt
import pathlib
import re

import pytest

from tests.conftest import betikten_modul_yukle

KOK = pathlib.Path(__file__).resolve().parent.parent
BETIK = KOK / "ops/karne_hesap.py"


# ---- SENTETİK TAKVİM ve SAAT -------------------------------------------------------------------
# Gerçek XNYS takvimi `meridian.adapters.data._sessions()`tir (depodaki TEK seans kümesi). Burada
# onun YERİNE geçen bir küme kullanılır ki çiviler `pandas_market_calendars`ın tatil tablosuna ve
# gerçek "bugün"e bağlı olmasın — tatilsiz iş günleri, deterministik. Gerçek kaynağın kullanıldığı
# ayrı bir çiviyle ölçülür (`test_TAKVIM_TEK_KAYNAKTAN_GELIR`).
#
# UZUNLUK BİLİNÇLİ (~1400 seans ≈ 5,5 yıl): tazelik eşiğinin DEFTERİN KENDİ KADANSINDAN türediğini
# gösteren çivi, aralıkları 30 işlem gününden UZUN olan bir defter kurmak zorunda — kısa bir
# takvimde o defter hiç kurulamaz ve çivi sessizce kör kalırdı.
def _isgunleri(baslangic: str = "2021-01-04", adet: int = 1400) -> tuple:
    g = dt.date.fromisoformat(baslangic)
    out: list[str] = []
    while len(out) < adet:
        if g.weekday() < 5:
            out.append(g.isoformat())
        g += dt.timedelta(days=1)
    return tuple(out)


SEANSLAR = _isgunleri()
BUGUN = SEANSLAR[-1]          # `takvim` fikstürü saati buraya sabitler


def _seans_dilimi(adet: int, geri: int = 0) -> tuple:
    """Sondan `geri` seans geriye kaydırılmış, `adet` uzunluğunda seans dilimi.
    Fikstürlerin varsayılanı BUGÜNDE biter: tazelik kapısı böylece yalnız onu SINAYAN
    çivilerde ateşler, ötekilerin arka planında sessizce durmaz."""
    son = len(SEANSLAR) - geri
    return SEANSLAR[son - adet:son]


@pytest.fixture
def mod():
    """`ops/karne_hesap.py` — KAYNAKTAN derlenir (`__pycache__` tuzağı: bkz. ops/sasi_yukleyici)."""
    assert BETIK.exists(), f"{BETIK} YOK — Görev 1 teslim edilmemiş"
    return betikten_modul_yukle(BETIK, "karne_hesap_v337")


@pytest.fixture
def takvim(monkeypatch):
    """Sentetik XNYS seans kümesi + sabitlenmiş ŞİMDİ.

    Takvimi yamamak, karnenin KENDİ takvimini kurmadığının da ölçüsüdür. Saat `barclock`tan
    gelir (deponun tek saati) ve `_now_fn` enjeksiyon noktası barclock'un KENDİ sözleşmesidir —
    ikinci bir saat kaynağı açmak, deponun belgeli "aynı zaman iki kaynak" kusuru olurdu."""
    from meridian import barclock
    from meridian.adapters import data as _veri
    monkeypatch.setattr(_veri, "_sessions", lambda: frozenset(SEANSLAR))
    monkeypatch.setattr(barclock, "_now_fn",
                        lambda: dt.datetime.fromisoformat(BUGUN + "T20:00:00+00:00"))
    return SEANSLAR


def _islem(gun: str, pnl: float, r: float = 1.0) -> dict:
    """`trades.jsonl` satırının score.py'nin OKUDUĞU alanları — alan adları kaynak koddan."""
    return {"ticker": "AAA", "ts_open": f"{gun}T14:30:00Z", "ts_close": f"{gun}T20:00:00Z",
            "pnl_dollars": float(pnl), "r_multiple": float(r)}


def _defter_yaz(satirlar: list[dict]) -> None:
    """Fikstür DEPOLAMA KATMANINDAN geçer (`store.write_jsonl`), ham dosya yolundan DEĞİL:
    karne/sermaye defterleri SQLite'a göçtü (`*.migrated`) ve ham yol yanlış katmanı ölçer."""
    from meridian import store
    store.write_jsonl("trades.jsonl", satirlar)


def _saglikli_defter(adet: int = 40, geri: int = 0) -> list[dict]:
    """Tek yönlü artan, 30 işlem gününden UZUN, varyansı SIFIR OLMAYAN, TAZE defter."""
    gunler = _seans_dilimi(adet, geri)
    return [_islem(gunler[i], 400.0 if i % 2 else 300.0, r=1.0 if i % 2 else 0.8)
            for i in range(adet)]


def _kisa_pencere_defteri(gun_sayisi: int = 10, adet: int = 35, pnl: float = 400.0,
                          geri: int = 0) -> list[dict]:
    """`adet` işlem, yalnız `gun_sayisi` seansa sıkışmış: örneklem YETERLİ, pencere KISA."""
    gunler = _seans_dilimi(gun_sayisi, geri)
    return [_islem(gunler[i % gun_sayisi], pnl if i % 2 else pnl * 0.5, r=1.0 if i % 2 else 0.4)
            for i in range(adet)]


def _seyrek_defter(aralik: int = 35, adet: int = 30, geri: int = 0) -> list[dict]:
    """Kadansı SEYREK defter: ardışık kapanışlar arasında `aralik` işlem günü var.
    Tazelik eşiğinin defterin KENDİ geçmişinden türediğini gösteren fikstür."""
    gunler = _seans_dilimi(aralik * (adet - 1) + 1, geri)
    return [_islem(gunler[i * aralik], 400.0 if i % 2 else 300.0, r=1.0 if i % 2 else 0.8)
            for i in range(adet)]


def _kod_govdesi() -> str:
    """Docstring'ler DIŞINDAKİ kaynak — sözü anlatan metin, sözün mekanik ölçümüne girmemeli."""
    kaynak = BETIK.read_text(encoding="utf-8")
    return "\n".join(s for s in kaynak.split('"""')[2::2])


def _sahte_gf(mod, **ustler) -> dict:
    """`watchdog.goal_failure_report`un GERÇEK dönüş şekli (kaynaktan okundu), üzerine yama."""
    d = {"failed": False, "threshold": -0.04, "realized_30d": 0.05, "n": 40,
         "ok": True, "olculemedi": False, "kapsam_disi": False,
         "detail": "sentetik", "neden": "sentetik watchdog cevabı"}
    d.update(ustler)
    return d


# ---- ARAYÜZ (Görev 2 bu şekle bağlanacak) ------------------------------------------------------

def test_ARAYUZ_DORT_HUKUM_DORT_ALAN(sandbox_state, takvim, mod):
    _defter_yaz(_saglikli_defter())
    s = mod.hesapla()
    assert set(s["hukumler"]) == set(mod.SORULAR) == {
        "target_return_30d", "min_sharpe", "max_drawdown", "failure_below"}, (
        f"dört soru sözleşmesi bozuldu: {sorted(s['hukumler'])}")
    for ad, h in s["hukumler"].items():
        assert set(h) == {"deger", "esik", "hukum", "neden"}, f"{ad} alan sözleşmesi: {sorted(h)}"
        assert h["hukum"] in mod.HUKUMLER, f"{ad}: {h['hukum']}"
        assert isinstance(h["neden"], str) and h["neden"].strip(), f"{ad}: gerekçesiz hüküm"


def test_HUKUM_ADLARI_SABITTEN_GELIR(mod):
    """YASA 6 (denetim LOW-11): `HUKUMLER` demetini Görev 2 okuyor ama BU modülde okuyucusu
    yoktu — hüküm dizgeleri `_hukum` gövdesine gömülüydü. Okunmayan bir arayüz sabiti,
    sessizce ayrışabilen ikinci bir gerçektir."""
    assert mod.HUKUMLER == ("GECTI", "KALDI", "OLCULEMEDI")
    assert mod._hukum(1.0, 0.5, True, "x")["hukum"] == mod.HUKUMLER[0]
    assert mod._hukum(1.0, 0.5, False, "x")["hukum"] == mod.HUKUMLER[1]
    assert mod._hukum(None, 0.5, None, "x")["hukum"] == mod.HUKUMLER[2]
    # SABİTİN KENDİ TANIMI hariç: kaynak odur, aranan şey MANTIKTA gömülü ikinci bir kopyadır.
    kod = "\n".join(s for s in _kod_govdesi().splitlines() if not s.startswith("HUKUMLER = "))
    for ad in ('"GECTI"', '"KALDI"', '"OLCULEMEDI"'):
        assert ad not in kod, f"hüküm adı mantığa gömülü, sabitten türemiyor: {ad}"


def test_HUKUM_KURULDUYSA_DEGER_ZORUNLUDUR(mod):
    """Denetim LOW-8: değişmez BELGEDEYDİ, KODDA DEĞİLDİ. `_hukum(None, esik, True, …)` bugünkü
    watchdog sözleşmesinde erişilemez ama watchdog `failed=False` + `realized_30d=None` dönmeye
    başlarsa karne `{"hukum": "GECTI", "deger": None}` üretirdi — hem değişmezin hem uydurma
    yasağının ihlali, tek satırda. Kapı artık YAPISAL."""
    h = mod._hukum(None, 0.5, True, "sayısız geçti")
    assert h["hukum"] == "OLCULEMEDI" and h["deger"] is None, h
    assert "SÖZLEŞME İHLALİ" in h["neden"], h["neden"]
    assert "sayısız geçti" in h["neden"], "özgün gerekçe kayboldu"


def test_DEGER_YOKSA_OLCULEMEDI_VARSA_HUKUM(sandbox_state, takvim, mod):
    """DEĞİŞMEZ (iki yönlü): `hukum == "OLCULEMEDI"` ⟺ `deger is None`. Bu çivi olmadan
    "ölçemedim" diyen bir satır yine de bir sayı taşıyabilir ve o sayı panoda ÖLÇÜM gibi okunur —
    bu botun kapatmak için var olduğu boşluğun ta kendisi."""
    for defter in ([], [_islem(SEANSLAR[-1], 10.0)] * 5, _saglikli_defter(),
                   _kisa_pencere_defteri(), _saglikli_defter(geri=400)):
        _defter_yaz(defter)
        for ad, h in mod.hesapla()["hukumler"].items():
            olculemedi = h["hukum"] == "OLCULEMEDI"
            assert olculemedi == (h["deger"] is None), (
                f"{ad}: hukum={h['hukum']} ama deger={h['deger']!r} — 'ölçemedim' bir sayı taşıyor")


def test_YETERLI_VERIDE_DORT_HUKUM_DE_KURULUR(sandbox_state, takvim, mod):
    """Pozitif kontrol: çiviler her şeye OLCULEMEDI dedirtiyor olabilir — kör bir kural da
    yeşil görünür. 40 işlem / 40 seanslık TAZE defterde DÖRT hüküm de kurulmalı."""
    _defter_yaz(_saglikli_defter())
    h = mod.hesapla()["hukumler"]
    olcemeyen = {a: v["neden"] for a, v in h.items() if v["hukum"] == "OLCULEMEDI"}
    assert not olcemeyen, f"sağlıklı defterde hüküm kurulamadı: {olcemeyen}"


# ---- TEK-KAYNAK YASASI -------------------------------------------------------------------------

def test_FAILURE_BELOW_WATCHDOGDAN_GELIR(sandbox_state, takvim, mod, monkeypatch):
    """`failure_below` hükmünün SAHİBİ `watchdog.goal_failure_report`tır. Bu çivi çağrının
    gerçekten yapıldığını ısırır: watchdog'un cevabı değişince karnenin hükmü de değişmeli.
    Kopyalanmış bir pencere mantığı bu mutasyonda YEŞİL kalırdı."""
    from meridian import watchdog
    _defter_yaz(_saglikli_defter())
    temiz = mod.hesapla()["hukumler"]["failure_below"]
    assert temiz["hukum"] == "GECTI", temiz

    sahte = _sahte_gf(mod, failed=True, realized_30d=temiz["deger"], ok=False,
                      neden="watchdog BAŞARISIZ dedi (sentetik)")
    monkeypatch.setattr(watchdog, "goal_failure_report", lambda: sahte)
    h = mod.hesapla()["hukumler"]["failure_below"]
    assert h["hukum"] == "KALDI", f"watchdog BAŞARISIZ dedi, karne {h['hukum']} dedi: {h}"
    assert "sentetik" in h["neden"], f"watchdog'un gerekçesi taşınmadı: {h['neden']}"


def test_TARGET_SAYIYI_SCORE_DETAILDEN_ALIR(sandbox_state, takvim, mod, monkeypatch):
    """Denetim MEDIUM-2: hedef hükmü sayıyı `gf`den alıyordu, yani `failure_below`un
    YAPILANDIRMASINA bağlıydı. Artık elindeki `sd`den alır; ayrışma çivisi iki okumanın
    eşitliğini zaten garanti ettiği için tek-kaynak kaygısı bu bağı GEREKTİRMİYOR."""
    from meridian import score
    _defter_yaz(_saglikli_defter())
    gercek = score.score_detail
    monkeypatch.setattr(score, "score_detail",
                        lambda *a, **k: dict(gercek(*a, **k), realized_30d=0.4242))
    h = mod.hesapla()["hukumler"]["target_return_30d"]
    assert h["deger"] == 0.4242, f"hedef sayısı score_detail'den gelmiyor: {h}"


def test_TARGET_FAILURE_BELOW_YOKKEN_DE_HUKUM_VERIR(sandbox_state, takvim, mod):
    """Denetim MEDIUM-2'nin ısırığı: `goal.yaml`dan `failure_below` düşerse watchdog
    `kapsam_disi` döner. HEDEF hükmünün eşiği yerinde, sayısı `sd`de HAZIR — o hâlde hüküm
    verilebilmeli. Eskiden "failure_below tanımlı değil" gerekçesiyle OLCULEMEDI oluyordu."""
    from meridian import config
    (sandbox_state / "goal.yaml").write_text(
        "target_return_30d: 0.07\nmin_sharpe: 1.2\nmax_drawdown: 0.16\nmin_sample: 30\n",
        encoding="utf-8")
    config.goal.cache_clear()
    _defter_yaz(_saglikli_defter())
    h = mod.hesapla()["hukumler"]
    assert h["target_return_30d"]["hukum"] in ("GECTI", "KALDI"), (
        f"hedef, failure_below'un yokluğuna takıldı: {h['target_return_30d']}")
    assert h["min_sharpe"]["hukum"] in ("GECTI", "KALDI"), h["min_sharpe"]
    assert h["failure_below"]["hukum"] == "OLCULEMEDI", h["failure_below"]


def test_TARGET_WATCHDOG_DUSERSE_CAPRAZ_KONTROLU_BEYAN_EDER(sandbox_state, takvim, mod,
                                                            monkeypatch):
    """Denetim MEDIUM-7 (çivisiz kapı): watchdog düşünce hedef hükmü YİNE KURULUR (sayı `sd`de),
    ama çapraz doğrulamanın KOŞAMADIĞI ve istisnanın ADI gerekçede durmalı. Eskiden dal silinse
    hüküm yine OLCULEMEDI çıkıyor ve istisna adı sessizce "kaynak gerekçe bildirmedi" yedeğine
    iniyordu — hiçbir çivinin ısırmadığı bir YASA 4 regresyonu."""
    from meridian import watchdog

    def _patla():
        raise RuntimeError("sentetik watchdog arızası")

    monkeypatch.setattr(watchdog, "goal_failure_report", _patla)
    _defter_yaz(_saglikli_defter())
    h = mod.hesapla()["hukumler"]["target_return_30d"]
    assert h["hukum"] in ("GECTI", "KALDI"), f"hedef watchdog'a bağımlı kalmış: {h}"
    assert "sentetik watchdog arızası" in h["neden"], (
        f"istisnanın ADI gerekçeden düştü (YASA 4 regresyonu): {h['neden']}")


def test_SHARPE_VE_DD_SCORE_DETAILDEN_AYNEN_ALINIR(sandbox_state, takvim, mod, monkeypatch):
    """Sharpe/drawdown TANIMI bu dosyada YENİDEN YAZILAMAZ: sistemin kendi kapı skorlayıcısından
    (`score.score_detail`) farklı hesaplayan bir karne, kalıcı ve makul görünen bir yalan üretir.
    Mutasyon: skorlayıcının döndürdüğü sayıları değiştir — karnenin `deger`leri BİREBİR izlemeli."""
    from meridian import score
    _defter_yaz(_saglikli_defter())
    gercek = score.score_detail
    monkeypatch.setattr(score, "score_detail", lambda *a, **k: dict(
        gercek(*a, **k), sharpe=0.111, max_drawdown=0.222))
    h = mod.hesapla()["hukumler"]
    assert h["min_sharpe"]["deger"] == 0.111, f"sharpe kendi hesabından geliyor: {h['min_sharpe']}"
    assert h["max_drawdown"]["deger"] == 0.222, f"dd kendi hesabından geliyor: {h['max_drawdown']}"


def test_ESIKLER_GOAL_YAMLDAN_OKUNUR(sandbox_state, takvim, mod):
    """Eşikler `state/goal.yaml`ındır (SSoT, izli dosya). Koda gömülü bir eşik, dosya değişince
    sessizce ayrışır ve karne yanlış çizgiye göre hüküm verir."""
    from meridian import config
    (sandbox_state / "goal.yaml").write_text(
        "target_return_30d: 0.99\nmin_sharpe: 9.9\nmax_drawdown: 0.01\n"
        "failure_below: -0.99\nmin_sample: 5\n", encoding="utf-8")
    config.goal.cache_clear()
    _defter_yaz(_saglikli_defter())
    h = mod.hesapla()["hukumler"]
    assert h["target_return_30d"]["esik"] == 0.99, h["target_return_30d"]
    assert h["min_sharpe"]["esik"] == 9.9, h["min_sharpe"]
    assert h["max_drawdown"]["esik"] == 0.01, h["max_drawdown"]
    assert h["failure_below"]["esik"] == -0.99, h["failure_below"]


def test_ESIK_SAYILARI_KAYNAKTA_GOMULU_DEGIL():
    """Yukarıdaki çivinin ikinci yarısı: yürürlükteki dört eşik kaynak GÖVDESİNDE geçmemeli
    (şerhte geçebilir — belge açıklamaktır, hüküm vermez)."""
    kod = _kod_govdesi()
    for sayi in ("0.07", "1.2", "0.16", "-0.04"):
        assert sayi not in kod, f"goal.yaml eşiği koda gömülmüş: {sayi}"


def test_EKSIK_ESIK_KEYERROR_YERINE_HUKUM_URETIR(sandbox_state, takvim, mod):
    """Denetim LOW-9: `score.score_detail` üç eşiği KÖŞELİ PARANTEZLE okuyor ve `hesapla()` onu
    hükümlerden ÖNCE çağırıyordu — eksik bir eşik hesabı KeyError ile düşürüyor, "eşik yok"
    dalları hiç koşmuyordu. Artık eksik anahtar hükme çevrilir, çökmeye değil."""
    from meridian import config
    (sandbox_state / "goal.yaml").write_text(
        "target_return_30d: 0.07\nmax_drawdown: 0.16\nfailure_below: -0.04\nmin_sample: 30\n",
        encoding="utf-8")
    config.goal.cache_clear()
    _defter_yaz(_saglikli_defter())
    s = mod.hesapla()                                   # KeyError ATMAMALI
    h = s["hukumler"]["min_sharpe"]
    assert h["hukum"] == "OLCULEMEDI" and h["esik"] is None, h
    assert "min_sharpe" in h["neden"], f"eksik anahtar ADIYLA söylenmiyor: {h['neden']}"
    for ad in ("target_return_30d", "max_drawdown"):
        assert "min_sharpe" in s["hukumler"][ad]["neden"], (
            f"{ad}: skorlayıcının neden koşamadığı söylenmiyor — {s['hukumler'][ad]['neden']}")


# ---- AYRIŞMA: ANNOTE EDER, BAŞARISIZLIĞI YUTMAZ ------------------------------------------------

def test_IKI_KAYNAK_AYRISIRSA_BASARISIZ_DEGIL_HUKUMSUZ(sandbox_state, takvim, mod, monkeypatch):
    """Aynı gerçeğin (30g getiri) iki okuması ayrışırsa hangisinin doğru olduğunu bilmiyoruz —
    ve "birini seç" sessiz bir yalandır. Kopya kaçınılmazsa AYRIŞMA ÇİVİSİ gerekir (tek-kaynak
    yasasının kendi reçetesi). BU DAL: cevap değişebilir (`failed=False`), o yüzden yutulur."""
    from meridian import watchdog
    _defter_yaz(_saglikli_defter())
    gercek = watchdog.goal_failure_report()
    bozuk = dict(gercek, realized_30d=float(gercek["realized_30d"]) + 0.5)
    monkeypatch.setattr(watchdog, "goal_failure_report", lambda: bozuk)

    s = mod.hesapla()
    for ad in mod.SORULAR:
        h = s["hukumler"][ad]
        assert h["hukum"] == "OLCULEMEDI", f"{ad}: ayrışmaya rağmen hüküm verdi ({h})"
        assert "AYRIŞ" in h["neden"].upper(), f"{ad}: ayrışma adıyla söylenmedi — {h['neden']}"
    assert s["kapsam"]["ayrisma"], "ayrışma kapsam beyanına düşmedi"


def test_AYRISMA_BASARISIZLIK_HUKMUNU_YUTMAZ(sandbox_state, takvim, mod, monkeypatch):
    """DENETİM MEDIUM-1 — beyanla kodun TEK MUTLAK çelişkisiydi. Modül başlığı "BAŞARISIZ hükmünü
    SUSTURMAZ" diyordu, ama `_failure` `ayrisma`yı `failed`den ÖNCE sınıyordu: ayrışma günü
    watchdog'un `failed=True`si OLCULEMEDI'ye çevriliyordu ve hiçbir çivi bunu görmüyordu.

    İLKE: meta-kapı (ayrışma) bir hükmü ancak CEVABI DEĞİŞTİREBİLECEKSE hükümsüz kılar.
    `failed=True` iken cevap değişmez — şüpheli olan taraf karnenin kendi İKİNCİ okumasıdır,
    hükmün SAHİBİ (watchdog) değil."""
    from meridian import watchdog
    _defter_yaz(_saglikli_defter())
    gercek = watchdog.goal_failure_report()
    bozuk = dict(gercek, failed=True, ok=False,
                 realized_30d=float(gercek["realized_30d"]) + 0.5,
                 neden="watchdog BAŞARISIZ dedi (sentetik)")
    monkeypatch.setattr(watchdog, "goal_failure_report", lambda: bozuk)

    h = mod.hesapla()["hukumler"]["failure_below"]
    assert h["hukum"] == "KALDI", (
        f"ayrışma BAŞARISIZLIK hükmünü yuttu — rapor katmanı alarm katmanından sessiz oldu: {h}")
    assert h["deger"] is not None, h
    assert "sentetik" in h["neden"], f"sahibin gerekçesi taşınmadı: {h['neden']}"
    assert "AYRIŞ" in h["neden"].upper(), (
        f"ayrışma yutulmadı ama ŞERH de düşmedi — okuyucu şüpheyi göremez: {h['neden']}")


def test_SHARPE_AYRISMADA_SUSAR(sandbox_state, takvim, mod, monkeypatch):
    """Denetim MEDIUM-6 (çivisiz kapı): eski çivi yalnız hedef+failure'ı sınıyordu, `_sharpe`ten
    `if ayrisma:` silinse suite YEŞİL kalıyordu."""
    from meridian import watchdog
    _defter_yaz(_saglikli_defter())
    gercek = watchdog.goal_failure_report()
    monkeypatch.setattr(watchdog, "goal_failure_report",
                        lambda: dict(gercek, realized_30d=float(gercek["realized_30d"]) + 0.5))
    h = mod.hesapla()["hukumler"]["min_sharpe"]
    assert h["hukum"] == "OLCULEMEDI" and "AYRIŞ" in h["neden"].upper(), h


def test_DRAWDOWN_AYRISMADA_SUSAR(sandbox_state, takvim, mod, monkeypatch):
    """Denetim MEDIUM-6'nın ikinci yarısı: kapı TUTARSIZ dağıtılmıştı — `_sharpe` ayrışmada
    susuyor, `_drawdown` parametreyi HİÇ almıyordu. Nedensel okuma tutarsızlığı çözüyor:
    ayrışmanın tek makul sebebi iki okumanın DEFTERİNİN farklı olmasıdır (araya ekleme girdi),
    ve o hâlde `sd`den gelen HER sayı şüphelidir — drawdown dâhil."""
    from meridian import watchdog
    _defter_yaz(_saglikli_defter())
    gercek = watchdog.goal_failure_report()
    monkeypatch.setattr(watchdog, "goal_failure_report",
                        lambda: dict(gercek, realized_30d=float(gercek["realized_30d"]) + 0.5))
    h = mod.hesapla()["hukumler"]["max_drawdown"]
    assert h["hukum"] == "OLCULEMEDI" and "AYRIŞ" in h["neden"].upper(), h


# ---- PENCERE: İŞLEM GÜNÜ, TAKVİM GÜNÜ DEĞİL ----------------------------------------------------

def test_KISA_PENCERE_30G_HUKMUNU_OLCULEMEDI_YAPAR(sandbox_state, takvim, mod):
    _defter_yaz(_kisa_pencere_defteri())
    s = mod.hesapla()
    assert s["kapsam"]["pencere_islem_gunu"] == 10, s["kapsam"]
    h = s["hukumler"]["target_return_30d"]
    assert h["hukum"] == "OLCULEMEDI", f"10 işlem günlük defterden 30g hükmü verildi: {h}"
    assert "10" in h["neden"] and "30" in h["neden"], (
        f"neden ELİMDEKİ ile GEREKENİ söylemiyor: {h['neden']}")


def test_KISA_PENCERE_GEREKCESI_YON_IDDIA_ETMEZ(sandbox_state, takvim, mod):
    """Denetim LOW-10: gerekçe "30 güne GERİLMİŞ" diyordu. Kapı 30 İŞLEM günü ister (~42 takvim
    günü) ama `score` ölçeklemeyi TAKVİM günüyle yapar (`30/span`); 30-42 takvim günü bandında
    sayı gerilmez SIKIŞIR. Hüküm doğruydu, cümle o bantta olguyu yanlış anlatıyordu."""
    _defter_yaz(_kisa_pencere_defteri())
    neden = mod.hesapla()["hukumler"]["target_return_30d"]["neden"].lower()
    assert "ölçeklen" in neden, f"gerekçe ölçeklemeden söz etmiyor: {neden}"
    assert not re.search(r"\bgerilmiş\b(?!.*sıkış)", neden), (
        f"gerekçe tek yönlü 'gerilmiş' iddia ediyor: {neden}")


def test_TAKVIM_YOKSA_HICBIR_HUKUM_VERILMEZ(sandbox_state, mod, monkeypatch):
    """`trend_shadow.ay_sonu_mu` emsali: takvim yoksa cevap YOKTUR. Sessizce takvim gününe
    düşmek, her pazartesi öten bir eşik üretir (`loop._mutabakat_bayatligi` dersi).

    DÖRDÜ BİRDEN (düzeltme dalgası): drawdown eskiden takvimsiz de hüküm veriyordu, çünkü
    tek kapısı PENCERE UZUNLUĞUYDU ve o bir yol istatistiği için gereksiz. Tazelik kapısı
    eklenince durum değişti: takvim olmadan defterin GÜNCEL olup olmadığı bilinemez, ve bayat
    bir yol istatistiği de güncel bir hüküm değildir."""
    from meridian import barclock
    from meridian.adapters import data as _veri
    monkeypatch.setattr(_veri, "_sessions", lambda: frozenset())
    monkeypatch.setattr(barclock, "_now_fn",
                        lambda: dt.datetime.fromisoformat(BUGUN + "T20:00:00+00:00"))
    _defter_yaz(_saglikli_defter())
    s = mod.hesapla()
    assert s["kapsam"]["pencere_islem_gunu"] is None, s["kapsam"]
    assert "takvim" in (s["kapsam"]["pencere_neden"] or "").lower(), s["kapsam"]
    for ad in mod.SORULAR:
        assert s["hukumler"][ad]["hukum"] == "OLCULEMEDI", (
            f"{ad}: takvim yokken hüküm verildi — mesafe/tazelik takvim günüyle ölçülmüş olabilir "
            f"({s['hukumler'][ad]})")


def test_TAKVIM_DISI_DAMGA_HUKUM_VERDIRMEZ(sandbox_state, takvim, mod):
    """Defterin uçları takvimde yoksa mesafe ölçülemez — `_mutabakat_bayatligi` birebir aynı
    hâlde `(None, neden)` döner. Buradaki damga hafta sonudur (sentetik takvimde yok)."""
    _defter_yaz([_islem("2021-01-02", 100.0)] + _saglikli_defter())
    s = mod.hesapla()
    assert s["kapsam"]["pencere_islem_gunu"] is None, s["kapsam"]
    assert "2021-01-02" in (s["kapsam"]["pencere_neden"] or ""), s["kapsam"]["pencere_neden"]


def test_TAKVIM_TEK_KAYNAKTAN_GELIR():
    """Karne KENDİ takvimini kurmaz: XNYS seansları deponun tek kümesinden
    (`adapters.data._sessions`) gelir. İkinci bir takvim kaynağı, sessizce ayrışan iki gerçektir.
    Saat için de aynı kural: tek saat `barclock`tur."""
    kod = _kod_govdesi()
    assert "_sessions()" in kod, "seans kümesi tek kaynaktan alınmıyor"
    assert "barclock" in kod, "şimdi ikinci bir saat kaynağından geliyor"
    for kacak in ("pandas_market_calendars", "mcal.", "bdate_range", "weekday()", "isoweekday",
                  "date.today", "datetime.now", "utcnow"):
        assert kacak not in kod, f"karne kendi takvimini/saatini kuruyor: {kacak}"


def test_PENCERE_TAM_ESIKTE_HUKUM_VERILIR(sandbox_state, takvim, mod):
    """Sınır: tam 30 işlem günü YETERLİDİR (eşiğin kendisi geçer). `<` ile `<=` karışırsa
    sınırdaki her defter sessizce hükümsüz kalır."""
    gunler = _seans_dilimi(mod.PENCERE_ISLEM_GUNU)
    _defter_yaz([_islem(gunler[i % mod.PENCERE_ISLEM_GUNU], 400.0 if i % 2 else 300.0)
                 for i in range(40)])
    s = mod.hesapla()
    assert s["kapsam"]["pencere_islem_gunu"] == mod.PENCERE_ISLEM_GUNU, s["kapsam"]
    assert s["hukumler"]["target_return_30d"]["hukum"] != "OLCULEMEDI", (
        f"tam eşikteki pencere hükümsüz sayıldı: {s['hukumler']['target_return_30d']}")


# ---- TAZELİK (denetim MEDIUM-4) ----------------------------------------------------------------

def test_BAYAT_DEFTER_GUNCEL_HUKUM_DOGURMAZ(sandbox_state, takvim, mod):
    """Motor durmuş olsa karne aynı GECTI'yi her hafta GÜNCEL bir cevap gibi basardı — kardeş
    profilin (`@bekci`) avladığı "duran iş" sınıfı, ve botun kendi gerekçesinin ("hiç başarısız
    olmadı" ≠ "hiç ölçülmedi") yeni bir kılığı. Modülde `datetime` ithali bile yoktu."""
    _defter_yaz(_saglikli_defter(geri=200))
    s = mod.hesapla()
    assert s["kapsam"]["bayat"] is True, s["kapsam"]
    assert s["kapsam"]["sessizlik_islem_gunu"] == 200, s["kapsam"]
    for ad in mod.SORULAR:
        h = s["hukumler"][ad]
        assert h["hukum"] == "OLCULEMEDI", f"{ad}: bayat defterden güncel hüküm verildi ({h})"
        assert "200" in h["neden"], f"{ad}: sessizliğin YAŞI gerekçede yok — {h['neden']}"


def test_BAYAT_DEFTER_BASARISIZLIGI_YUTMAZ(sandbox_state, takvim, mod, monkeypatch):
    """Tazelik de bir META-KAPIDIR ve aynı ilkeye tabidir: `failed=True`yu yutmaz. Bayat bir
    defterde bile sözleşmenin BAŞARISIZLIK hükmü görünür kalır, yaşı şerh olarak düşer."""
    from meridian import watchdog
    _defter_yaz(_saglikli_defter(geri=200))
    gercek = watchdog.goal_failure_report()
    monkeypatch.setattr(watchdog, "goal_failure_report",
                        lambda: dict(gercek, failed=True, ok=False,
                                     neden="watchdog BAŞARISIZ dedi (sentetik)"))
    h = mod.hesapla()["hukumler"]["failure_below"]
    assert h["hukum"] == "KALDI", f"bayatlık BAŞARISIZLIK hükmünü yuttu: {h}"
    assert "sentetik" in h["neden"] and "200" in h["neden"], h["neden"]


def test_TAZE_DEFTER_HUKUM_VERIR(sandbox_state, takvim, mod):
    """Pozitif kontrol: tazelik kapısı her şeye OLCULEMEDI dedirtmemeli."""
    _defter_yaz(_saglikli_defter(geri=3))
    s = mod.hesapla()
    assert s["kapsam"]["bayat"] is False and s["kapsam"]["sessizlik_islem_gunu"] == 3, s["kapsam"]
    assert all(s["hukumler"][a]["hukum"] != "OLCULEMEDI" for a in mod.SORULAR), s["hukumler"]


def test_BAYATLIK_ESIGI_DEFTERIN_KENDI_KADANSINDAN_TURETILIR(sandbox_state, takvim, mod):
    """EŞİK YUVARLAK BİR SAYI DEĞİL. İki defter AYNI sessizliği (33 işlem günü) yaşıyor:

      · kadansı SIK olan (her seans işlem) → eşik 30 (hüküm penceresi bağlıyor) → BAYAT
      · kadansı SEYREK olan (35 seansta bir) → eşik 35 (defterin kendi geçmişi bağlıyor) → TAZE

    Sabit bir 30'la ikisi de bayat sayılırdı ve seyrek işleyen bir strateji her hafta yanlış
    alarm üretirdi — operatör onu susturur, sonra gerçek durma görünmez olur."""
    _defter_yaz(_saglikli_defter(geri=33))
    sik = mod.hesapla()["kapsam"]
    assert sik["gecmis_en_uzun_sessizlik"] == 1, sik
    assert sik["bayat_esik_gun"] == mod.PENCERE_ISLEM_GUNU and sik["bayat"] is True, sik

    _defter_yaz(_seyrek_defter(aralik=35, geri=33))
    seyrek = mod.hesapla()["kapsam"]
    assert seyrek["gecmis_en_uzun_sessizlik"] == 35, seyrek
    assert seyrek["bayat_esik_gun"] == 35 and seyrek["bayat"] is False, seyrek


def test_GELECEK_DAMGA_TAZELIK_UYDURTMAZ(sandbox_state, takvim, mod, monkeypatch):
    """Son kapanış BUGÜNDEN sonraysa damga ya da saat tutarsızdır. "0 gün sessizlik" demek,
    ölçülemeyen bir şeyi en iyi hâliyle uydurmak olurdu."""
    from meridian import barclock
    _defter_yaz(_saglikli_defter())
    monkeypatch.setattr(barclock, "_now_fn",
                        lambda: dt.datetime.fromisoformat(SEANSLAR[-300] + "T20:00:00+00:00"))
    s = mod.hesapla()
    assert s["kapsam"]["bayat"] is None, s["kapsam"]
    assert "sonra" in (s["kapsam"]["bayat_neden"] or "").lower(), s["kapsam"]["bayat_neden"]
    assert all(s["hukumler"][a]["hukum"] == "OLCULEMEDI" for a in mod.SORULAR), s["hukumler"]


# ---- ÖLÇEK ŞERHİ (denetim MEDIUM-3) ------------------------------------------------------------

def test_OLCEK_SERHI_HUKMUN_YANINDA_DURUR(sandbox_state, takvim, mod):
    """`realized_30d = (1+total_return)**(30/span) - 1` — DEFTERİN TAMAMINDAN türeyen bir HIZ,
    "son 30 gün" DEĞİL. 500 işlem günlük bir defterde son 30 gün düz geçse bile hüküm GECTI
    çıkabilir. Modül başlığı bunu doğru anlatıyordu ama hükmün KENDİ gerekçesinde yoktu — ve
    Görev 2'nin LLM'i başlığı değil, TAM O CÜMLEYİ okuyacak; orada yoksa uyduramaz, susar."""
    _defter_yaz(_saglikli_defter())
    s = mod.hesapla()
    for ad in ("target_return_30d", "failure_below"):
        neden = s["hukumler"][ad]["neden"]
        assert mod.OLCEK_SERHI in neden, f"{ad}: ölçek şerhi hükmün yanında değil — {neden}"
    kor = " ".join(s["kapsam"]["goremedigim"])
    assert "SON 30 GÜN" in kor, f"ölçek kısıtı körlük listesinde yok: {kor}"


def test_OLCEK_SERHI_TEK_KAYNAK():
    """Şerh İKİ hükümde görünüyor; iki yere elle yazılırsa biri güncellenip öteki kalır."""
    kod = _kod_govdesi()
    assert kod.count("OLCEK_SERHI") >= 3, "şerh tek sabitten türemiyor"


# ---- SHARPE ------------------------------------------------------------------------------------

def test_SHARPE_OLCULEMEDIGINDE_SIFIR_KALDI_DEMEZ(sandbox_state, takvim, mod):
    """`score.score_detail` ölçülemeyen sharpe'ı muhafazakâr 0.0 döndürür ve gerçeği ayrı bir
    bayrakta (`sharpe_measurable`) taşır. Karne bayrağı okumazsa "0.0 < 1.2 → KALDI" der; bu,
    ölçülmemiş bir şeyi ÖLÇÜLMÜŞ VE BAŞARISIZ gibi raporlamaktır."""
    gunler = _seans_dilimi(40)
    _defter_yaz([_islem(gunler[i], 250.0) for i in range(40)])   # varyans SIFIR
    from meridian import score, config, store
    sd = score.score_detail(store.read_jsonl("trades.jsonl"), config.goal())
    assert sd["sharpe_measurable"] is False and sd["sharpe"] == 0.0, sd
    h = mod.hesapla()["hukumler"]["min_sharpe"]
    assert h["hukum"] == "OLCULEMEDI", f"ölçülemeyen sharpe hüküm doğurdu: {h}"
    assert h["deger"] is None, h


def test_SHARPE_TAM_ESIKTE_GECER(sandbox_state, takvim, mod, monkeypatch):
    """Sınır vakası: `sharpe == min_sharpe` GEÇER. `>` ile `>=` karışması tam eşikteki bir
    stratejiyi sessizce kaldırır."""
    from meridian import score, config
    esik = float(config.goal()["min_sharpe"])
    _defter_yaz(_saglikli_defter())
    gercek = score.score_detail
    monkeypatch.setattr(score, "score_detail",
                        lambda *a, **k: dict(gercek(*a, **k), sharpe=esik))
    h = mod.hesapla()["hukumler"]["min_sharpe"]
    assert h["hukum"] == "GECTI" and h["deger"] == esik, h

    monkeypatch.setattr(score, "score_detail",
                        lambda *a, **k: dict(gercek(*a, **k), sharpe=esik - 0.0001))
    assert mod.hesapla()["hukumler"]["min_sharpe"]["hukum"] == "KALDI"


# ---- DRAWDOWN ----------------------------------------------------------------------------------

def _dd_defteri(ilk_zarar: float) -> list[dict]:
    """Eğri 100.000'den başlar (score.START_EQUITY) ve ilk işlemde düşer: dd = zarar/100.000.
    Kalan işlemler sıfır P&L — tepe ilk noktadır, dd sabit kalır."""
    gunler = _seans_dilimi(40)
    return [_islem(gunler[0], -abs(ilk_zarar), r=-1.0)] + [
        _islem(gunler[i], 0.0, r=0.0) for i in range(1, 40)]


def test_DD_YONU_TERSTIR_TAM_ESIKTE_GECER(sandbox_state, takvim, mod):
    """Diğer üç sorunun aksine drawdown'da KÜÇÜK iyidir. Yön çevrilirse karne, tavanı AŞAN her
    defteri "geçti" diye raporlar — ve bu tam da alarmın sustuğu yerde olur."""
    from meridian import config, score
    esik = float(config.goal()["max_drawdown"])
    _defter_yaz(_dd_defteri(score.START_EQUITY * esik))
    h = mod.hesapla()["hukumler"]["max_drawdown"]
    assert h["deger"] == pytest.approx(esik, abs=1e-6), h
    assert h["hukum"] == "GECTI", f"tavana TAM EŞİT drawdown kaldı sayıldı: {h}"

    _defter_yaz(_dd_defteri(score.START_EQUITY * esik + 200.0))
    h2 = mod.hesapla()["hukumler"]["max_drawdown"]
    assert h2["hukum"] == "KALDI", f"tavanı AŞAN drawdown geçti sayıldı: {h2}"


def test_DD_PENCERE_UZUNLUGUNA_BAGLI_DEGIL(sandbox_state, takvim, mod):
    """BİLİNÇLİ AYRIM: drawdown bir YOL istatistiğidir, 30 güne ölçeklenmiş bir oran değil — kısa
    pencere onu hükümsüz KILMAZ (tazelik kapısı ayrı bir sorudur ve o BAĞLAR). Aynı deftere 30g
    hükmü verilemezken dd hükmü verilebilir."""
    _defter_yaz(_kisa_pencere_defteri(pnl=-900.0))
    h = mod.hesapla()["hukumler"]
    assert h["target_return_30d"]["hukum"] == "OLCULEMEDI", h["target_return_30d"]
    assert h["max_drawdown"]["hukum"] in ("GECTI", "KALDI"), (
        f"yol istatistiği pencere UZUNLUĞUNA bağlandı: {h['max_drawdown']}")


def test_DD_ACIK_POZISYON_KORLUGU_BEYAN_EDILIR(sandbox_state, takvim, mod):
    """Bedel yasası: dd yalnız KAPANMIŞ işlem eğrisinden ölçülür (`score.score_detail`in
    `mtm_equity` girdisi bu katmanda yok). Açıkken oluşan çekilme GÖRÜNMEZ ve bu körlük
    beyansız kalırsa karne, göremediği şey hakkında "geçti" demiş olur.

    ÇİVİ İLK YAZILIŞINDA YANLIŞ SEBEPLE YEŞİLDİ (mutasyon turu, 2026-08-30): koşul tüm körlük
    listesini TEK DİZEYE eritip `"açık pozisyon" in metin` diyordu, ve listedeki BAŞKA bir
    kalem ("açık planlar… açık pozisyonların") o alt dizeyi zaten taşıyordu. Yani drawdown
    körlüğü listeden tamamen silinse bile çivi geçerdi. Artık kalem TEKİL olarak aranır ve
    hükmün KENDİ gerekçesi ayrıca sınanır — iki ayrı yüzey, iki ayrı iddia."""
    _defter_yaz(_saglikli_defter())
    s = mod.hesapla()

    kalem = [x for x in s["kapsam"]["goremedigim"] if "mtm_equity" in x]
    assert len(kalem) == 1, f"drawdown körlüğü kalemi tekil değil: {kalem}"
    assert "drawdown" in kalem[0].lower() and "kapanmiş" in kalem[0].lower().replace("ı", "i"), (
        f"kalem neyi göremediğini söylemiyor: {kalem[0]}")

    neden = s["hukumler"]["max_drawdown"]["neden"].lower()
    assert "kapanmiş" in neden.replace("ı", "i") and "açık pozisyon" in neden, (
        f"hükmün KENDİ gerekçesi kapalı-eğri kısıtını söylemiyor: {neden}")


# ---- ÖRNEKLEM / BOŞ DEFTER ---------------------------------------------------------------------

def test_ORNEKLEM_ALTINDA_DORT_HUKUM_DE_SAYI_UYDURMAZ(sandbox_state, takvim, mod):
    gunler = _seans_dilimi(5)
    _defter_yaz([_islem(gunler[i], 400.0) for i in range(5)])
    s = mod.hesapla()
    for ad, h in s["hukumler"].items():
        assert h["hukum"] == "OLCULEMEDI" and h["deger"] is None, f"{ad}: {h}"
    birlesik = " ".join(h["neden"] for h in s["hukumler"].values())
    assert "5" in birlesik and "30" in birlesik, (
        f"neden ELİMDEKİ (5) ile GEREKENİ (30) söylemiyor: {birlesik}")


def test_BOS_DEFTER_SIFIR_DEMEZ(sandbox_state, takvim, mod):
    """Defter hiç yoksa `store.read_jsonl` boş liste döner — sıfır işlem "getiri %0" DEĞİLDİR."""
    s = mod.hesapla()
    assert s["kapsam"]["islem_sayisi"] == 0, s["kapsam"]
    for ad, h in s["hukumler"].items():
        assert h["hukum"] == "OLCULEMEDI" and h["deger"] is None, f"{ad}: {h}"


def test_WATCHDOG_DUSERSE_SESSIZ_KALINMAZ(sandbox_state, takvim, mod, monkeypatch):
    """YASA 4: tek kaynağın kendisi düşerse "başarısız değil" DENMEZ; "ölçemedim" denir ve
    istisna gerekçeye taşınır."""
    from meridian import watchdog

    def _patla():
        raise RuntimeError("sentetik watchdog arızası")

    monkeypatch.setattr(watchdog, "goal_failure_report", _patla)
    _defter_yaz(_saglikli_defter())
    h = mod.hesapla()["hukumler"]["failure_below"]
    assert h["hukum"] == "OLCULEMEDI", h
    assert "sentetik watchdog arızası" in h["neden"], f"arıza gerekçeye taşınmadı: {h['neden']}"


# ---- KAPSAM BEYANI -----------------------------------------------------------------------------

def test_KAPSAM_BEYANI_NE_GORDUGUNU_VE_NE_GOREMEDIGINI_SOYLER(sandbox_state, takvim, mod):
    _defter_yaz(_saglikli_defter())
    s = mod.hesapla()
    metin = mod.kapsam_beyani(s)
    for parca in ("trades.jsonl", "40", "işlem günü", "GÖRÜLMEDİ", "sessizlik"):
        assert parca in metin, f"kapsam beyanında eksik: {parca!r} — {metin}"


def test_KAPSAM_ORNEK_YETERLILIGININ_OKUYUCUSU_VAR(sandbox_state, takvim, mod):
    """YASA 6 (denetim LOW-11): `kapsam["ornek_yeterli"]`nin hiçbir okuyucusu yoktu — ne
    `kapsam_beyani`, ne çiviler. Okunmayan alan üretilmemişten farksızdır."""
    _defter_yaz(_saglikli_defter())
    assert "örneklem YETERLİ" in mod.kapsam_beyani(mod.hesapla())
    gunler = _seans_dilimi(5)
    _defter_yaz([_islem(gunler[i], 400.0) for i in range(5)])
    assert "örneklem YETERSİZ" in mod.kapsam_beyani(mod.hesapla())


def test_KAPSAM_SATIR_SAYISI_KENDINI_YALANLAMAZ(sandbox_state, takvim, mod):
    """Denetim LOW-13: `islem_sayisi` defterin BÜTÜN satırlarıydı ama cümlede "kapanan işlem"
    diye etiketleniyor, hemen ardından aynı toplamın içindeki damgasız satırlar ayrıca
    sayılıyordu — aynı cümlede iki iddia birbirini yalanlıyordu."""
    _defter_yaz(_saglikli_defter(39) + [{"ticker": "AAA", "pnl_dollars": 10.0, "r_multiple": 0.1}])
    s = mod.hesapla()
    assert s["kapsam"]["islem_sayisi"] == 40 and s["kapsam"]["damgasiz_satir"] == 1, s["kapsam"]
    metin = mod.kapsam_beyani(s)
    assert "40 defter satırı" in metin, metin
    assert "kapanan işlem" not in metin.split("damgasız")[0], (
        f"damgasız satırlar hâlâ 'kapanan işlem' diye sayılıyor: {metin}")


# ---- CLI ---------------------------------------------------------------------------------------

def test_CLI_TEK_BULGU_BASARISIZLIK_DEGILDIR_CIKIS_SIFIR(sandbox_state, takvim, mod, capsys):
    """Çıkış kodunu Görev 3'ün birimi okuyacak. RAPOR aracında KALDI bir BULGUdur, koşum
    hatası değil — aksi hâlde deneyin kötü geçen her haftası "birim arızası" diye görünür."""
    _defter_yaz(_kisa_pencere_defteri(pnl=-900.0))
    assert mod.main([]) == 0
    cikti = capsys.readouterr().out
    assert "KALDI" in cikti, cikti


def test_CLI_TAM_OLCUM_KESINTISINDE_IKI_DONER(sandbox_state, takvim, mod, capsys):
    """Denetim LOW-12: substrat (`ops/bekci_tarama.py`) ÖLÇÜM KOŞAMADIĞINDA 2 döner; karne
    yalnız istisnada 2 dönüyordu, yani DÖRT hüküm birden ölçülemediğinde (takvim düştü, defter
    boş) Görev 3'ün birimi SONSUZA DEK yeşil kalırdı. Tam ölçüm kesintisi bir MEKANİZMA
    ARIZASIDIR; tek bir KALDI hâlâ bir bulgudur ve 0 döner."""
    _defter_yaz([])
    assert mod.main([]) == 2
    assert "4/4" in capsys.readouterr().out


def test_CLI_HER_KOSUMDA_KAPSAM_BASAR(sandbox_state, takvim, mod, capsys):
    _defter_yaz(_saglikli_defter())
    assert mod.main([]) == 0
    cikti = capsys.readouterr().out
    assert "# kapsam:" in cikti, cikti
    for ad in mod.SORULAR:
        assert ad in cikti, f"{ad} basılmadı"


def test_CLI_HESAP_DUSERSE_IKI_DONER(mod, monkeypatch, capsys):
    """0 = ölçüm YAPILDI (bulgu olsun olmasın), 2 = ölçüm YAPILAMADI. İkisi karışırsa birim ya
    her hafta kırmızı olur ya da hiç konuşmaz."""
    def _patla():
        raise RuntimeError("sentetik hesap arızası")

    monkeypatch.setattr(mod, "hesapla", _patla)
    assert mod.main([]) == 2
    assert "sentetik hesap arızası" in capsys.readouterr().err


def test_CLI_JSON_HAM_SONUCU_BASAR(sandbox_state, takvim, mod, capsys):
    """JSON kipi AYRIŞTIRILABİLİR olmalı — ve kapsam yine de HER koşumda gitmeli. İkisi
    çelişmez: kapsam metin satırı olarak değil, YÜKÜN İÇİNDE taşınır."""
    import json
    _defter_yaz(_saglikli_defter())
    assert mod.main(["--json"]) == 0
    ham = json.loads(capsys.readouterr().out)          # tek bayt fazlası ayrıştırmayı düşürür
    assert set(ham["hukumler"]) == set(mod.SORULAR), ham
    assert "GÖRÜLMEDİ" in ham["kapsam_beyani"], (
        "JSON kipinde kapsam beyanı düştü — dosyaya yazan operatör körlüğü göremez")


def test_CLI_YAZMA_KIPI_YOKTUR(mod):
    """Kuru koşum bu aracın TEK kipidir; `--uygula` bilerek yoktur (bekci emsali)."""
    with pytest.raises(SystemExit):
        mod.main(["--uygula"])


# ---- DİSİPLİN ----------------------------------------------------------------------------------

def test_KARNE_HESABINDA_MODEL_YOK():
    """Global Constraint: DÖRT HÜKMÜN DÖRDÜ Python'da hesaplanır. Model sayı ÜRETEMEZ ve bir
    hükmü SUSTURAMAZ; sunum katmanı (Görev 2) ayrı dosyadır."""
    kod = _kod_govdesi().lower()
    for jeton in ("hermes", "llm", "gemini", "anthropic", "openai", "_agent_call", "notify"):
        assert jeton not in kod, f"hesap katmanına model/teslimat sızmış: {jeton}"


def test_SESSIZ_YUTMA_DEPONUN_KENDI_DENETCISIYLE_OLCULUR():
    """YASA 4 — kural KOPYALANMAZ, `meridian.codelaw` çağrılır (ikinci bir regex uygulaması,
    yasadan sessizce ayrışan ikinci bir gerçek olurdu)."""
    from meridian import codelaw
    kaynak = BETIK.read_text(encoding="utf-8")
    for h in codelaw.scan_source(kaynak, str(BETIK)):
        assert h["marker"], f"işaretsiz sessiz yakalayıcı (satır {h['line']}): {h['note']}"
        assert len(h["marker"].strip()) >= 20, f"gerekçe kısa (satır {h['line']}): {h['marker']!r}"


# ---- YAZMA MUHASEBESİ: BEYAN ↔ ÇAĞRI GRAFİĞİ ---------------------------------------------------
# TARANAN MODÜL KÜMESİ BEYANLIDIR (dal denetimi M4): `hesapla()`nın doğrudan çağırdığı katmanlar
# ve onların bu küme İÇİNDE kalan çağrıları. Kümenin DIŞINA çıkan bir dal taranmaz — bu bir
# eksiklik değil bir KAPSAM BEYANIDIR ve çivi onu ADIYLA söyler.
_TARANAN_MODULLER = {
    "score": "meridian/score.py",
    "store": "meridian/store.py",
    "storage": "meridian/storage.py",
    "config": "meridian/config.py",
    "barclock": "meridian/barclock.py",
    "watchdog": "meridian/watchdog.py",
    "data": "meridian/adapters/data.py",
}
# `hesapla()`nın GİRİŞ NOKTALARI — kaynaktan okundu, elle seçilmedi (aşağıdaki çivi kaynakta
# gerçekten çağrıldıklarını ayrıca ölçer).
_GIRIS_NOKTALARI = (
    ("config", "goal"), ("store", "read_jsonl"), ("store", "db_backed"),
    ("score", "score_detail"), ("watchdog", "goal_failure_report"),
    ("barclock", "session_date"), ("data", "_sessions"),
)


def _obs_yazan_fonksiyonlar() -> dict:
    """`{(modül, fonksiyon): [olay adları]}` — giriş noktalarından AST ile ERİŞİLEBİLEN
    `obs.warn/log/alarm/error` çağrıları. Hiçbir modül İTHAL EDİLMEZ, yalnız kaynak okunur."""
    import ast
    agaclar = {ad: ast.parse((KOK / y).read_text(encoding="utf-8"))
               for ad, y in _TARANAN_MODULLER.items()}
    fnler = {ad: {d.name: d for d in ast.walk(a)
                  if isinstance(d, (ast.FunctionDef, ast.AsyncFunctionDef))}
             for ad, a in agaclar.items()}

    def _cagrilar(dugum):
        for n in ast.walk(dugum):
            if isinstance(n, ast.Call):
                f = n.func
                if isinstance(f, ast.Name):
                    yield None, f.id
                elif isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name):
                    yield f.value.id, f.attr

    def _obs(dugum):
        return [(n.args[0].value if n.args and isinstance(n.args[0], ast.Constant) else None)
                for n in ast.walk(dugum)
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and isinstance(n.func.value, ast.Name) and n.func.value.id == "obs"
                and n.func.attr in ("warn", "log", "alarm", "error")]

    gorulen, kuyruk, bulunan = set(), list(_GIRIS_NOKTALARI), {}
    while kuyruk:
        mod, fn = kuyruk.pop()
        if (mod, fn) in gorulen or mod not in fnler or fn not in fnler[mod]:
            continue
        gorulen.add((mod, fn))
        olaylar = _obs(fnler[mod][fn])
        if olaylar:
            bulunan[(mod, fn)] = olaylar
        for hedef_mod, hedef_fn in _cagrilar(fnler[mod][fn]):
            if hedef_mod is None:
                kuyruk.append((mod, hedef_fn))
            elif hedef_mod in fnler:
                kuyruk.append((hedef_mod, hedef_fn))
            elif hedef_mod == "_veri":              # `karne_hesap`ın `adapters.data` takma adı
                kuyruk.append(("data", hedef_fn))
    return bulunan


def test_YAZMA_ISTISNALARI_TAM_SAYILIR():
    """Denetim MEDIUM-5 + DAL DENETİMİ M4 — ve bu ikincisi ÇİVİNİN KENDİSİNİ değiştirdi.

    ESKİ ÇİVİ BEYANI KENDİSİYLE KARŞILAŞTIRIYORDU: dört adın ve "DÖRT İSTİSNA" dizgesinin
    docstring'de GEÇTİĞİNİ ölçüyordu, çağrı grafiğiyle değil. Yani MEDIUM-5'in doğurduğu
    düzeltme, kendi sınıfının İKİNCİ örneğini (eksik iki istisna) yapısal olarak göremeyen bir
    çiviyle geldi. Eksik olanlar: `storage._yerel_defter_beyani`
    (`obs.warn("yerel_donmus_defter")`) ve `storage._acil_anahtar_beyani`
    (`obs.warn("db_off_kaynaklar_arsivde")`) — ikisi de `store.db_backed() → storage.active()`
    üzerinden erişilebilir ve `hesapla()` `db_backed`i kapsam beyanı için DOĞRUDAN çağırıyor.

    BUGÜN ÖLÇÜ DIŞARIDADIR: beyan, kaynak METNİNDEN AST ile yürünen çağrı grafiğiyle
    karşılaştırılır. Beyan ile grafik ayrışırsa çivi kırmızıdır — hangi yönde olursa olsun
    (eksik sayım da, ölmüş bir beyan da).

    KAPSAM DÜRÜSTÇE DARDIR ve dosyanın kendisi de bunu yazar: yalnız `_TARANAN_MODULLER` ve
    yalnız STATİK çözülebilen çağrılar yürünür (dinamik gönderim, `getattr`, geri çağırma yok).
    Bu bir "hiçbir yazım yok" kanıtı DEĞİL, beyanın taranabilir yüzeyde TAM olduğunun kanıtıdır.
    """
    bulunan = _obs_yazan_fonksiyonlar()
    bas = BETIK.read_text(encoding="utf-8").split('"""')[1]

    assert bulunan, "tarama HİÇBİR obs yazımı bulmadı — muhtemelen tarayıcı bozuldu, kod değil"
    for (mod, fn), olaylar in sorted(bulunan.items()):
        assert fn in bas, (
            f"çağrı grafiğinde `{mod}.{fn}` obs'a yazıyor ({olaylar}) ama BAŞLIK onu saymıyor — "
            f"'bu araç yazmaz' sözü o kadar eksik")
        for olay in olaylar:
            if olay is not None:
                assert olay in bas, (
                    f"`{mod}.{fn}` `{olay}` olayını basıyor ama beyan onu anmıyor")

    _SAYI_ADI = {3: "ÜÇ", 4: "DÖRT", 5: "BEŞ", 6: "ALTI", 7: "YEDİ", 8: "SEKİZ"}
    assert f"{_SAYI_ADI[len(bulunan)]} İSTİSNA" in bas, (
        f"çağrı grafiğinde {len(bulunan)} yazan fonksiyon var "
        f"({sorted(f'{m}.{f}' for m, f in bulunan)}); başlık bu sayıyı yazmıyor")
    yanlis = [a for n, a in _SAYI_ADI.items() if n != len(bulunan) and f"{a} İSTİSNA" in bas]
    assert not yanlis, f"başlık BAŞKA bir istisna sayısı da anıyor: {yanlis}"
    assert "TARAMANIN KAPSAMI" in bas, (
        "beyan, taramanın DAR olduğunu söylemiyor — kapsamsız bir 'tam sayım' iddiası, "
        "ölçülmemiş bir güvencedir")


def test_YAZMA_MUHASEBESI_GIRIS_NOKTALARI_KAYNAKTA_GERCEKTEN_CAGRILIYOR():
    """Yukarıdaki taramanın GİRİŞ NOKTALARI da elle yazılmış bir listedir — ve elle yazılmış
    liste sürüklenir. `hesapla()` bir gün yeni bir katman çağırırsa tarama onu görmez ve
    muhasebe SESSİZCE eksilir; kapsamı ölçen çivinin kendi kapsamı ölçülmelidir."""
    import ast
    agac = ast.parse(BETIK.read_text(encoding="utf-8"))
    fn = next(d for d in ast.walk(agac)
              if isinstance(d, ast.FunctionDef) and d.name == "hesapla")
    cagrilar = {(n.func.value.id, n.func.attr) for n in ast.walk(fn)
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and isinstance(n.func.value, ast.Name)}
    takma = {"_veri": "data"}
    disarida = {f"{takma.get(m, m)}.{f}" for m, f in cagrilar
                if takma.get(m, m) in _TARANAN_MODULLER
                and (takma.get(m, m), f) not in _GIRIS_NOKTALARI}
    assert not disarida, (
        f"`hesapla()` taranan modüllerden şu fonksiyonları da çağırıyor ama giriş noktası "
        f"listesinde YOKLAR: {sorted(disarida)} — yazma muhasebesi bu dalları hiç görmüyor")


def test_SATIR_CAPASI_YOK():
    """`dosya-adı:satır-numarası` biçimi CI'da sessizce çürür — çapa SATIR değil SEMBOL olmalı."""
    capa = re.findall(r"\b[\w/]+\.py:\d+", BETIK.read_text(encoding="utf-8"))
    assert not capa, f"satır çapası: {capa}"


def test_OLCULEN_ILE_CIKARILAN_AYRILMIS():
    """Bu makine canlı defteri GÖREMEZ. Dosya bunu söylemezse okuyucu, buradaki her cümleyi
    canlıda gözlenmiş sanar (`ops/bekci_tarama.py` künye emsali)."""
    bas = BETIK.read_text(encoding="utf-8").split('"""')[1]
    assert "GÖREMEZ" in bas.upper() or "GÖRMEDİ" in bas.upper(), (
        "başlık, canlı defteri göremediğini beyan etmiyor")


def test_ESZAMANLI_EKLEME_YARISI_BEYANLI():
    """INFO-14: defter iki kez okunuyor (karne bir, watchdog bir) ve aradaki bir ekleme ayrışma
    çivisini tetikler. Fail-closed ve bugün kaçınılmaz (`goal_failure_report` argüman almıyor) —
    ama beyansız bir 'kaçınılmaz', ölçülmemiş bir kusurdan ayırt edilemez."""
    bas = BETIK.read_text(encoding="utf-8").split('"""')[1]
    assert "İKİ KEZ" in bas.upper(), "defterin iki kez okunduğu beyan edilmemiş"
    assert "kaçınılmaz" in bas.lower(), "yarışın bugün kaçınılmaz olduğu söylenmemiş"


# ---- DAL DÜZELTME DALGASI (2026-08-31) ---------------------------------------------------------

def test_SAYISIZ_BASARISIZLIK_HUKMU_DUSMEZ(sandbox_state, takvim, mod, monkeypatch):
    """DENETİM L1 — META-KAPI İLKESİNİN SÖZLEŞME KAPISINDAKİ AYAĞI.

    `_failure`ın `failed=True` dalı `r30`un None olabileceğini AÇIKÇA hesaba katıyor
    (`None if r30 is None else float(r30)`). Ama tam o kombinasyon (`gecti=False`,
    `deger=None`) `_hukum`un sözleşme kapısına düşüyor ve `OLCULEMEDI` dönüyordu — yani bir
    `failed=True` HÜKÜMSÜZ kılınıyordu. Modül başlığı bunu MUTLAK biçimde reddediyor
    (META-KAPI İLKESİ): meta-kapıların yapmasını yasakladığımız şeyi sözleşme kapısı yapardı.

    "BUGÜN ERİŞİLEMEZ" BİR GEREKÇE DEĞİLDİR: `watchdog.goal_failure_report` `failed=True`yu
    bugün yalnız `realized_30d` bir float'ken döndürüyor. Ama SÖZLEŞMELER DEĞİŞİR ve iki
    beyanın (META-KAPI ile `_hukum` değişmezi) çakıştığı yerde hangisinin kazandığı YAZILI
    olmalıdır. Cevap: hüküm kazanır, eksik sayı ŞERH olur."""
    from meridian import watchdog
    _defter_yaz(_saglikli_defter())
    sahte = _sahte_gf(mod, failed=True, realized_30d=None, ok=False,
                      neden="watchdog BAŞARISIZ dedi ama oranı bildirmedi (sentetik)")
    monkeypatch.setattr(watchdog, "goal_failure_report", lambda: sahte)
    h = mod.hesapla()["hukumler"]["failure_below"]
    assert h["hukum"] == "KALDI", (
        f"sayısız bir BAŞARISIZLIK hükmü sözleşme kapısında düştü — rapor katmanı alarm "
        f"katmanını susturdu: {h}")
    assert h["deger"] is None, f"olmayan sayı uyduruldu: {h}"
    assert "sentetik" in h["neden"], f"sahibin gerekçesi taşınmadı: {h['neden']}"
    assert "DEĞER ÖLÇÜLEMEDİ" in h["neden"], (
        f"eksik sayı ŞERH olarak beyan edilmedi — okuyucu `deger: —`yı bir hüküm boşluğu "
        f"sanar: {h['neden']}")
    assert "SÖZLEŞME İHLALİ" not in h["neden"], (
        f"hüküm geçti ama gerekçe hâlâ ihlal cümlesi taşıyor: {h['neden']}")


def test_SAYISIZ_GECTI_HALA_SOZLESME_IHLALIDIR(mod):
    """İSTİSNANIN SINIRI. `deger_zorunlu=False` YALNIZ başarısızlık dalınadır: "başarısız DEĞİL"
    hükmü sayısız verilirse o gerçekten ölçülmemiş bir İYİ HABERDİR ve uydurma yasağına girer.
    İstisnayı genelleştiren bir mutasyon burada kırmızı olmalı."""
    h = mod._hukum(None, 0.5, True, "sayısız geçti")
    assert h["hukum"] == "OLCULEMEDI" and h["deger"] is None, h
    assert "SÖZLEŞME İHLALİ" in h["neden"], h["neden"]


def test_KAPSAM_EKSIK_ESIGI_ORNEKLEM_KITLIGI_DIYE_SUCLAMAZ(sandbox_state, takvim, mod):
    """DENETİM L7. `SKOR_ZORUNLU_ESIKLER`den biri düşerse `sd = {}` olur, `min_ornek` None kalır
    ve `ornek_yeterli` False olur — kapsam cümlesi o hâlde "örneklem YETERSİZ (asgari None)"
    basıyordu. Oysa örneklem BOL olabilir; eksik olan `goal.yaml` anahtarıdır ve
    `score.score_detail` HİÇ KOŞMAMIŞTIR. Hükümlerin `neden`i doğruyu söylüyordu
    (`test_EKSIK_ESIK_KEYERROR_YERINE_HUKUM_URETIR`), kapsam cümlesi nedeni yanlış yere
    yazıyordu — ve bu dosyanın tamamı "hangi boşluk, hangi sebeple" ayrımı üstüne kurulu."""
    import yaml
    _defter_yaz(_saglikli_defter())
    yol = sandbox_state / "goal.yaml"
    g = yaml.safe_load(yol.read_text(encoding="utf-8"))
    g.pop("min_sharpe", None)
    yol.write_text(yaml.safe_dump(g, allow_unicode=True), encoding="utf-8")
    from meridian import config
    config.goal.cache_clear()

    metin = mod.kapsam_beyani(mod.hesapla())
    assert "asgari None" not in metin, f"olmayan bir eşik sayı gibi basıldı: {metin}"
    assert "örneklem YETERSİZ" not in metin, (
        f"eksik EŞİK, örneklem kıtlığı diye suçlanıyor (defterde 40 satır var): {metin}")
    assert "min_sharpe" in metin, f"eksik anahtarın ADI kapsam cümlesinde yok: {metin}"


def test_PENCERE_YETERSIZ_DOCSTRINGI_KODU_ANLATIR(mod):
    """DENETİM L8. Docstring "`<` değil `<=` karşılaştırması" diyordu; kodda `<=` YOKTU
    (`if gun < PENCERE_ISLEM_GUNU`). Davranış DOĞRUYDU (30 yeterlidir, çivisi
    `test_PENCERE_TAM_ESIKTE_HUKUM_VERILIR`), yanlış olan CÜMLEYDİ — bir sonraki okuyucuyu kodu
    "düzeltmeye" davet eden sınıf."""
    import inspect
    doc = inspect.getdoc(mod._pencere_yetersiz) or ""
    kaynak = inspect.getsource(mod._pencere_yetersiz)
    govde = kaynak.split('"""')[2]
    assert "<=" not in govde, "kod artık `<=` kullanıyor — docstring yeniden yazılmalı"
    assert "`<` değil `<=`" not in doc, "docstring hâlâ kodda olmayan bir operatörü tarif ediyor"
    assert "gun < PENCERE_ISLEM_GUNU" in doc, (
        f"docstring kodun GERÇEK karşılaştırmasını yazmıyor: {doc!r}")
    # Davranış da burada bir kez daha ısırılır: sınırın DAHİL olduğu iddiası cümlede var,
    # kodda da olmalı.
    assert mod._pencere_yetersiz(mod.PENCERE_ISLEM_GUNU, None) is None
    assert mod._pencere_yetersiz(mod.PENCERE_ISLEM_GUNU - 1, None) is not None
