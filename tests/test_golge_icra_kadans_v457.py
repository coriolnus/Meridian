"""test_golge_icra_kadans_v457.py — EDG-2026-088 B1 / Task 2: worker kadansı + `/api` okuyucusu.

NUMARA KAYDI (v331×2 sınıfı, CLAUDE.md §2). Plan bu dosyaya v456 diyordu; Task 1 raporu §2 ölçtü:
v455 ana checkout'ta ZATEN çift doluydu (`test_roadmap_arsiv_sayimi_v455`, `test_soul_denetimi_rota_v455`)
ve bir paralel worktree'de üçüncü bir v455 uçuyordu. Task 1 v456'ya kaydı, bu dosya **v457**tir.
Ölçüm ana checkout + TÜM worktree'ler taranarak yapıldı (tek worktree'de sayım KÖRDÜR).

NE ÖLÇER. Task 1 motoru (`meridian/golge_icra.py`) doğurdu ama ne ÇAĞIRANI ne OKUYUCUSU vardı:
iki artefakt (`golge_icra.jsonl`, `golge_icra_acik.json`) `codelaw.artifact_graph`ta `unread`tı ve
`tests/test_codelaw_v59.py` ile `tests/test_golge_v2_yasam_dongusu_v132.py` KIRMIZIydı. Bu görev üç
şeyi bağlar ve altı çivi onları ölçer:
  1) KADANS  — `loop.daily_cycle` seans başına TAM BİR `adim`; ikinci poll yeni satır yazmaz.
  2) ARIZA GÖLGEDE KALIR — `adim` patlarsa canlı tur AYNEN tamamlanır + `golge_icra_failed`.
  3) BEDEL   — gölge katmanı hiçbir ağ/LLM yüzeyine dokunmaz (`ag_cagri`/`llm_cagri` = 0).
  4) YASA 6  — dış okuyucu `meridian/api.py`; `DECLARED_SINKS`e SATIR YOK (okuyucu GERÇEK).
  5) UÇ      — `_auth` zorunlu (401); boş defter "kanıt yok" der, sahte "yolunda" göstermez;
               `pencere.doldu` False iken HİÇBİR eşik hükmü metni yok.
  6) TEK EKLEME — `loop.py` diff'i tek çağrı bloğudur; uyuyan plan ÜRETİMİNİN yüklemleri
               baytı baytına aynıdır (kart kill#2: "dormant üretimine dokunulmaz").

ÖLÇÜM BAĞLAMI UYARISI (bu dosyanın kendi dersi). Task 1'in Yasa 6 çivisi SENTETİK bir ağaçta
(`tmp_path` + iki dosya) `store.read_jsonl(golge_icra.DEFTER)` yazınca `violations`ı boşaltıyordu.
CANLI ağaçta o okuma ÇÖZÜLMEZ: `codelaw._global_consts` çakışan sabit adlarını DÜŞÜRÜR ve `DEFTER`
adı `meridian/mukerrerlik.py::DEFTER`de ("oneri_akibet.jsonl") ikinci kez tanımlıdır — yani
`store.read_jsonl(golge_icra.DEFTER)` canlı graf için `ad_cozulemedi`dir. Bu yüzden `api.py`
LİTERAL ad okur (emsal: `earnings_pit`, `nous_fisler` — aynı gerekçe yazılı) ve aşağıdaki AYRIŞMA
çivisi literalin sabitle aynı kalmasını mühürler. Çivi 4 sentetik ağaçta DEĞİL, CANLI `meridian/`
kökünde ölçer.
"""
from __future__ import annotations

import inspect
import pathlib
import shutil
import sys
import types

import pytest
import yaml

from meridian import codelaw, config, golge_icra as gi, loop, store
from tests.conftest import make_bars

REPO = pathlib.Path(__file__).resolve().parents[1]
API_KAYNAK = (REPO / "meridian" / "api.py").read_text(encoding="utf-8")
LOOP_KAYNAK = (REPO / "meridian" / "loop.py").read_text(encoding="utf-8")


# ==================================================================================================
# ORTAK ZEMİN
# ==================================================================================================
@pytest.fixture
def seeded(sandbox_state):
    """`test_loop_gaps_v48::seeded` ile AYNI zemin: gerçek hedef/sınır dosyaları + varsayılan
    strateji. Kadans çivisi `daily_cycle`ın TAMAMINI koşturur; eksik yapılandırma turu erken
    keserdi ve çivi "kanca çağrılmadı" derken aslında turu ölçmemiş olurdu."""
    repo_state = REPO / "state"
    for f in ("goal.yaml", "bounds.yaml"):
        shutil.copy2(repo_state / f, sandbox_state / f)
    config.reload_config()
    (sandbox_state / "strategy.yaml").write_text(yaml.safe_dump(config.default_strategy()))
    yield sandbox_state
    config.reload_config()


def _universe():
    idx = make_bars(300, seed=1, trend=0.0009)
    bars = {"AAA": make_bars(300, seed=2, breakout_at=200),
            "BBB": make_bars(300, seed=3, breakout_at=150),
            "CCC": make_bars(300, seed=4, trend=0.001)}
    return bars, idx


def _son_tarih(idx) -> str:
    return str(idx["date"].iloc[-1].date())


def _olaylar(ad: str) -> list[dict]:
    return [e for e in store.read_jsonl("events.jsonl") if e.get("event") == ad]


class _Casus:
    """`golge_icra.adim` yerine geçen sayaç — çağrı sayısını ve kwargs'ı tutar."""

    def __init__(self, sonuc=None):
        self.cagri: list[dict] = []
        self._sonuc = sonuc or {}

    def __call__(self, dstr, **kw):
        self.cagri.append({"dstr": dstr, **kw})
        return dict(self._sonuc)


# ==================================================================================================
# ÇİVİ 1 — KADANS: seans başına TAM BİR `adim`
# ==================================================================================================
def test_civi1_kanca_SEANS_BASINA_BIR_KEZ_ve_ELDEKI_girdilerle_cagirir(seeded, monkeypatch):
    """Kapanan seans başına TAM BİR `adim` — ve girdilerin HEPSİ zaten bellektedir.

    `bars_of` ikinci bir bar yükleyici DEĞİL, `per`in kendisine bakan bir çağrılabilirdir: kanca
    diske gitmez. `params` motorun `eff`i (rejime çözülmüş), `regime_ok` turun kendi bayrağı.
    Bu çivi olmasaydı "gölge koşuyor" iddiası kancanın varlığından türetilirdi, çağrısından değil.
    """
    casus = _Casus()
    monkeypatch.setattr(gi, "adim", casus)
    bars, idx = _universe()
    d = _son_tarih(idx)

    loop.daily_cycle(bars, idx, on_date=d)

    assert len(casus.cagri) == 1, f"seans başına bir adım değil: {len(casus.cagri)}"
    c = casus.cagri[0]
    assert c["dstr"] == d
    assert isinstance(c["planlar"], list)
    assert callable(c["bars_of"]) and isinstance(c["regime_ok"], bool)
    assert isinstance(c["params"], dict) and c["params"], "boş parametre — `eff` geçirilmemiş"
    # BAR KAYNAĞI ELDEKİ SÖZLÜKTÜR: çağrılabilir `per`e bakar, ikinci bir yükleyici kurmaz.
    assert c["bars_of"]("AAA") is not None, "kanca barları geçirmiyor"
    assert c["bars_of"]("YOK_BOYLE_BIR_SEMBOL") is None, "eksik sembolde patlıyor (KeyError yolu)"


def test_civi1_IKINCI_POLL_ayni_seansta_YENI_SATIR_yazmaz(seeded):
    """Zamanlayıcı 300 sn'de bir yokluyor; aynı seansın ikinci turu gölge defterine DOKUNMAZ.

    Bu MOTORUN idempotensinin değil KANCANIN idempotensinin ölçümüdür: gerçek `adim` çağrılır,
    `son_seans` kapısı ikinci turda satırı ve belgeyi olduğu gibi bırakır."""
    bars, idx = _universe()
    d = _son_tarih(idx)

    loop.daily_cycle(bars, idx, on_date=d)
    ilk_satir, ilk_doc = gi.kayit_al(), gi.acik_kayit()
    assert ilk_doc["son_seans"] == d, "gölge belgesi ilk turda yazılmadı"

    loop.daily_cycle(bars, idx, on_date=d)
    assert gi.kayit_al() == ilk_satir, "ikinci poll defterе satır ekledi"
    ikinci_doc = gi.acik_kayit()
    for k in ("son_seans", "bekleyen_giris", "acik", "islenen"):
        assert ikinci_doc[k] == ilk_doc[k], f"ikinci poll `{k}` alanını değiştirdi"


#: Kancanın kol süzgeci — kaynaktan BİREBİR. Testin hem varlığını hem DAVRANIŞINI ölçmesi için
#: burada metin olarak durur: aşağıdaki çivi onu önce kaynakta arar, sonra sentetik planlar
#: üzerinde KOŞTURUR. Yalnız adı ("_golge_planlar" var mı) aramak yetmez — mutasyon turunda
#: `_golge_planlar = list(plans)` ad kontrolünü yeşil geçti (M-c ISIRMADI, 2026-09-08).
_KOL_SUZGECI = ('[p for p in plans\n'
                '                              if p.get("dormant_setup") '
                'or (p.get("ticker") in _silahli_tk)]')


def test_civi1_KANCA_uyuyan_ve_GERCEK_ISLEM_kollarini_ayirir():
    """KOL KAPSAMI (Rol-1 hükmü 7): gölgeye giren küme uyuyan planlar + O SEANS SİLAHLANAN
    planlardır — "tüm normal planların sürekli gölgelenmesi" (bedel ~50×) DEĞİL.

    Silahlanan plan gerçek işlem olur; kontrol kolunun (PK 2) gölge eşleniği ancak plan DOĞDUĞU
    seansta yakalanırsa üretilebilir — `adim` ileri yürür, geriye saramaz (`son_seans` tektir).

    ÇİVİ İKİ AYAKLIDIR: (a) ifade kaynakta BİREBİR duruyor mu, (b) o ifade GERÇEKTEN eliyor mu.
    (b) olmadan süzgeci `list(plans)`a çevirmek çiviyi yeşil bırakıyordu."""
    src = inspect.getsource(loop.daily_cycle)
    assert _KOL_SUZGECI in src, "kol süzgeci kancada BİREBİR durmuyor — kapsam sessizce kaymış"
    assert 'a["ticker"] for a in meta["armed"]' in src, \
        "silahlı küme `meta[\"armed\"]`den TÜRETİLMİYOR — ikinci bir silahlanma yasası doğmuş"
    assert src.count("girise_uygun(") == 2, \
        "kanca `girise_uygun`u yeniden çağırmış (üretim yüklemi ikinci kez yorumlanıyor) — " \
        "silahlanma yasası TEK yerdedir ve gölge onu OKUR, yeniden UYGULAMAZ"

    # POZİTİF KONTROL: ÜRETİMİN KENDİ İFADESİ sentetik planlar üzerinde koşturulur.
    ns = {"plans": [{"ticker": "AAA", "dormant_setup": True},    # uyuyan       → GİRER
                    {"ticker": "BBB", "dormant_setup": False},   # silahlandı   → GİRER (kontrol)
                    {"ticker": "CCC", "dormant_setup": False}],  # ne uyuyan ne silahlı → ELENİR
          "_silahli_tk": {"BBB"}}
    secilen = eval(" ".join(_KOL_SUZGECI.split()), {"__builtins__": {}}, ns)  # noqa: S307
    assert [p["ticker"] for p in secilen] == ["AAA", "BBB"], \
        f"süzgeç ELEMİYOR — normal planların TAMAMI gölgeye giriyor (bedel ~50×): {secilen}"


# ==================================================================================================
# ÇİVİ 2 — ARIZA GÖLGEDE KALIR
# ==================================================================================================
def test_civi2_ADIM_PATLARSA_canli_tur_TAMAMLANIR_ve_uyari_duser(seeded, monkeypatch):
    """Ölçüm katmanının arızası canlı turu BLOKLAYAMAZ: planlar diske yazılır, özet döner,
    `golge_icra_failed` deftere düşer. Sessiz `pass` DEĞİL — Yasa 4: arıza ADIYLA görünür."""
    def _patla(*a, **kw):
        raise RuntimeError("gölge motoru düştü")

    monkeypatch.setattr(gi, "adim", _patla)
    bars, idx = _universe()
    d = _son_tarih(idx)

    ozet = loop.daily_cycle(bars, idx, on_date=d)

    assert isinstance(ozet, dict) and ozet.get("date") == d, "gölge arızası canlı turu kesti"
    assert store.read_json(loop.PORTFOLIO, {}).get("last_date") == d, "portföy yazılmadı"
    for anahtar in ("candidates", "plans", "armed", "open_positions"):
        assert anahtar in ozet, f"özet '{anahtar}' alanını kaybetti"
    uyari = _olaylar("golge_icra_failed")
    assert uyari, "arıza SESSİZ yutuldu — `golge_icra_failed` deftere düşmedi"
    assert "RuntimeError" in str(uyari[-1].get("error")), uyari[-1]


def test_civi2_KANCA_kendi_try_except_ini_TASIR_ve_P3_acikligina_YAZMAZ():
    """Yapısal: gölge çağrısı `skills.pipeline_run("P3_PLAN"...)` bloğunun İÇİNDE değildir —
    ölçüm katmanının süresi/arızası denetlenen P3 açıklığının karnesine karışmaz."""
    src = inspect.getsource(loop.daily_cycle)
    p3 = src.index('pipeline_run("P3_PLAN"')
    kanca = src.index("_gi.adim(")
    assert kanca > p3, "kanca P3'ten ÖNCE — sıra bozuk"
    # P3 açıklığı 2.4 bloğundan önce kapanır; kanca 2.4'ün yanındadır.
    assert src.index("shadow_variants_failed") < kanca, \
        "kanca 2.4 GÖLGE-VARYANT bloğunun yanına DEĞİL, daha yukarı konmuş"
    assert 'obs.warn("golge_icra_failed"' in src, "kancanın kendi uyarısı yok"


# ==================================================================================================
# ÇİVİ 3 — BEDEL: SIFIR ağ / LLM
# ==================================================================================================
def test_civi3_GOLGE_ADIMI_hicbir_AG_veya_LLM_yuzeyine_DOKUNMAZ(sandbox_state, monkeypatch):
    """PATLAYICI SAHTELER: `hermes`, `spend`, `httpx`, `requests` modülleri erişildiği ANDA patlar.
    Gölge adımı tam bir seans koşar ve hiçbirine dokunmaz; `ozet` bedeli 0 olarak RAPORLAR.

    "Ölçtüm, sıfır" ile "hiç bakmadım" ayrı olgulardır: bedel alanları özet sözleşmesinde durur."""
    class _Bomba(types.ModuleType):
        def __getattr__(self, ad):
            raise AssertionError(f"GÖLGE KATMANI AĞ/LLM YÜZEYİNE DOKUNDU: {self.__name__}.{ad}")

    for ad in ("meridian.hermes", "meridian.spend", "httpx", "requests"):
        monkeypatch.setitem(sys.modules, ad, _Bomba(ad))

    bars = {"AAA": _bar_yolu()}
    plan = {"id": "P-1", "ticker": "AAA", "setup": "pullback", "gate_verdict": "REVIEW",
            "dormant_setup": True, "date": "2026-01-02", "entry_trigger": 100.0,
            "stop": 95.0, "targets": [110.0], "strategy_version": 3}
    gi.adim("2026-01-02", planlar=[plan], bars_of=bars.get, regime_ok=True, params={})
    gi.adim("2026-01-05", planlar=[], bars_of=bars.get, regime_ok=True, params={})

    bedel = gi.ozet()["bedel"]
    assert bedel["ag_cagri"] == 0 and bedel["llm_cagri"] == 0, bedel


def test_civi3_KANCA_kaynaginda_ag_LLM_harcama_adi_GECMEZ():
    """Kaynak taraması: kancanın gövdesi yalnız `golge_icra`ya bakar. Davranış çivisi bir turu
    ölçer, bu çivi YARIN eklenecek bir çağrıyı da yakalar (ikisi ayrı sınıflardır)."""
    src = inspect.getsource(loop.daily_cycle)
    bas = src.index("2.5 GÖLGE İCRA")
    blok = src[bas:src.index("golge_icra_failed", bas) + 200]
    for yasak in ("hermes", "spend", "httpx", "requests", "notify", "llm"):
        assert yasak not in blok, f"gölge kancası `{yasak}` yüzeyine uzanıyor"


# ==================================================================================================
# ÇİVİ 4 — YASA 6: dış okuyucu GERÇEK, beyan YOK
# ==================================================================================================
def test_civi4_IKI_ARTEFAKTIN_DIS_OKUYUCUSU_api_py_dir():
    """CANLI `meridian/` kökünde ölçülür (sentetik ağaç bu soruya körDÜR — dosya başlığındaki
    `DEFTER` çakışması dersi). `unread is False` + `violations` boş + beyan YOK."""
    g = codelaw.artifact_graph()
    assert g["violations"] == [], g["violations"]
    for ad in (gi.DEFTER, gi.ACIK):
        a = g["artifacts"][ad]
        assert a["writers"] == ["golge_icra.py"], a["writers"]
        assert "api.py" in a["external_readers"], a
        assert a["unread"] is False, a
        assert ad not in codelaw.DECLARED_SINKS, \
            "gerçek okuyucusu OLAN artefakt lağım listesine yazılmış (stale_sinks sınıfı)"
        assert ad not in codelaw.HUMAN_INVOKED_SINKS, "beyan gerekmiyor — okuyucu üretimde"


def test_civi4_api_LITERALLERI_sabitlerle_AYRISMAZ():
    """TEK-KAYNAK YASASI. `codelaw.artifact_graph` statik bir graftır ve
    `store.read_jsonl(golge_icra.DEFTER)` biçimini CANLI ağaçta ÇÖZEMEZ (`_global_consts` çakışan
    `DEFTER` adını düşürür — `mukerrerlik.py` aynı adı taşıyor). Bu yüzden `api.py` literal yazar;
    kopya kaçınılmaz olduğu için AYRIŞMA çivisi burada durur."""
    for ad in (gi.DEFTER, gi.ACIK):
        assert f'"{ad}"' in API_KAYNAK, f"api.py `{ad}` literalini kaybetti — Yasa 6 sessizce düşer"
    # Ölçümün kendisi: çakışma GERÇEKTEN var mı? Yoksa yukarıdaki gerekçe bayatlamıştır.
    assert codelaw._global_consts("meridian").get("DEFTER") is None, \
        "`DEFTER` artık tekil — literal gerekçesi bayatladı, attribute okumaya dönülebilir"


# ==================================================================================================
# ÇİVİ 5 — UÇ: yetki, boş defter, hükümsüzlük
# ==================================================================================================
def _istemci(monkeypatch, token="GOLGE-TOKEN-457"):
    from fastapi.testclient import TestClient
    from meridian import api
    monkeypatch.setattr(api, "DASH_TOKEN", token)
    return TestClient(api.app, raise_server_exceptions=True), api, token


def test_civi5_KIMLIKSIZ_istek_401(sandbox_state, monkeypatch):
    """`_auth` ZORUNLU: gölge defteri strateji davranışını taşır, kimliksiz çağrıya açılmaz."""
    c, _api, token = _istemci(monkeypatch)
    assert c.get("/api/golge-icra").status_code == 401
    r = c.get("/api/golge-icra", headers={"x-meridian-token": token})
    assert r.status_code == 200, r.text          # POZİTİF KONTROL: kapı her şeyi reddetmiyor


def test_civi5_BOS_DEFTER_kanit_yok_der_sifir_uydurmaz(sandbox_state, monkeypatch):
    """Boş defterde `n=0` ama toplam R / kazanma oranı / PF `None`dır — 0 yazmak "ölçtüm ve sıfır
    çıktı" demektir ve YALANDIR. Pencere de açılmamıştır."""
    c, _api, token = _istemci(monkeypatch)
    j = c.get("/api/golge-icra", headers={"x-meridian-token": token}).json()

    assert j["kart"] == gi.KART and j["n"] == 0
    for alan in ("toplam_r", "kazanma_orani", "pf"):
        assert j[alan] is None, f"boş defterde `{alan}` uydurulmuş: {j[alan]!r}"
    assert j["pencere"]["baslangic"] is None and j["pencere"]["doldu"] is False
    assert j["bedel"]["ag_cagri"] == 0 and j["bedel"]["llm_cagri"] == 0
    assert j["olculemeyen"] == []
    # Ham okuyucular yükte ADIYLA durur — Yasa 6 zincirinin görünen ucu.
    assert j["satirlar"] == [] and isinstance(j["acik"], dict)


def test_civi5_PENCERE_DOLMADAN_hicbir_ESIK_HUKMU_metni_YOK(sandbox_state, monkeypatch):
    """n<30 iken hüküm cümlesi yazmak, 049'un ikinci düşme sebebiydi. Uç BETİMLEYİCİDİR.

    YASAKLI SÖZCÜK LİSTESİ DAR TUTULDU (bilinçli): `NO_GO`/`REVIEW` gibi değerler `hukum_dagilimi`
    kovasında MEŞRU VERİdir — onları yasaklamak, dolu bir defterde çiviyi yalancı kırmızıya
    çevirirdi. Yasaklanan şey KARARIN KENDİSİdir: eşiği yorumlayan sözcükler + karar alan adları."""
    c, _api, token = _istemci(monkeypatch)
    r = c.get("/api/golge-icra", headers={"x-meridian-token": token})
    j = r.json()
    assert j["pencere"]["doldu"] is False
    assert not (set(j) & {"hukum", "verdict", "gecti", "sonuc", "karar", "esik_hukmu"}), \
        f"uç bir KARAR alanı taşıyor: {sorted(set(j) & {'hukum', 'verdict', 'gecti', 'sonuc', 'karar', 'esik_hukmu'})}"
    ham = r.text.upper()
    for yasak in ("GEÇER", "GECER", "KALIR", "EŞİK", "BAŞARILI", "BASARILI", "GEÇTİ"):
        assert yasak not in ham, f"pencere dolmadan hüküm metni sızdı: {yasak}"


def test_civi5_DIAGNOSTICS_mlops_blogu_pano_kartinin_EVIDIR(sandbox_state, monkeypatch):
    """Rol-1 hükmü 6: backend özeti BU planda, UI kutusu B2'de. Kartın evi `mlops` bloğudur —
    `shadow_variants` komşusu; ikisi de gölge ailesidir."""
    c, _api, token = _istemci(monkeypatch)
    j = c.get("/api/diagnostics", headers={"x-meridian-token": token}).json()
    blok = j["mlops"]["golge_icra"]
    assert blok["kart"] == gi.KART and blok["n"] == 0
    assert "shadow_variants" in j["mlops"], "komşu kayboldu — blok yanlış yere taşınmış"


# ==================================================================================================
# ÇİVİ 6 — TEK EKLEME: uyuyan plan ÜRETİMİ baytı baytına aynı
# ==================================================================================================
#: Uyuyan kurulum ÜRETİMİNİN iki yüklemi — kaynaktan BİREBİR alınmıştır (kart kill#2). Bir
#: karakteri bile kayarsa bu çivi kırılır: gölge katmanı üretime dokunamaz.
_URETIM_TARAMA = (
    '                for _s2 in _all.values():              # uyuyan kurulum ateşlemeleri karşı-olgusala\n'
    '                    if _s2.setup not in strat.ARMED_SETUPS:\n'
    '                        dormant_sigs.append(_s2)\n'
)
_URETIM_PLAN = (
    '                if plan["dormant_setup"]:\n'
)


def test_civi6_uyuyan_URETIM_yuklemleri_BAYTI_BAYTINA_ayni():
    """Kill#2: `arming._dormant_setups` / `strategy.scan_all` / `guard.classify_gate` /
    `loop.girise_uygun` ve plan doğum bloğu DEĞİŞMEZ. Metin karşılaştırması bilinçlidir —
    davranış çivisi bir yeniden yazımı 'aynı sonuç' diye geçirebilirdi."""
    for parca in (_URETIM_TARAMA, _URETIM_PLAN):
        assert parca in LOOP_KAYNAK, f"uyuyan üretim bloğu değişmiş:\n{parca}"
    assert '"dormant_setup": True, **_s2.as_row()}' in LOOP_KAYNAK


def test_civi6_LOOP_diffi_TEK_CAGRI_BLOGUDUR():
    """`loop.py`de gölge motorunun adı YALNIZ kancada geçer; ikinci bir çağrı yeri yoktur."""
    assert LOOP_KAYNAK.count("golge_icra") == 3, \
        "gölge adı loop.py'de beklenenden farklı sayıda geçiyor (import + adim + uyarı adı)"
    assert LOOP_KAYNAK.count("_gi.adim(") == 1, "ikinci bir gölge çağrısı doğmuş"
    src = inspect.getsource(loop.daily_cycle)
    assert src.count("_scan_tail(") == 2, "kanca üçüncü bir tarama dilimi reçetesi ekledi"


def test_civi6_MOTOR_KAPI_YUZEYI_olmadi_ve_pitlaw_KAYITSIZ_gormedi():
    """Kanca bir kapı yüzeyi doğurmadı: `golge_icra` GO/REVIEW/NO_GO döndürmez, plandaki
    `gate_verdict`i TÜKETİR. Doğsaydı `pitlaw` orada KÖR kalırdı."""
    from meridian import pitlaw
    kayitsiz = pitlaw.kapi_sozlesme_denetimi()["kayitsiz"]
    assert not [k for k in kayitsiz if k["yer"].startswith(("golge_icra.py", "api.py"))], kayitsiz


# ==================================================================================================
# ÖLÇÜLEN KÖR NOKTA — kancanın koştuğu seans kümesi (uydurma yasağı)
# ==================================================================================================
def test_OLCULEN_KOR_NOKTA_kanca_P2_kapisinin_ICINDEDIR(seeded, monkeypatch):
    """DÜRÜST BEYAN, GİZLİ VARSAYIM DEĞİL. Kanca (gölge-v2 emsalinin yanında) `halted` /
    `data_bad` / bütçe / KİTAP DOLU kapısının İÇİNDEDİR: o turlarda `adim` HİÇ çağrılmaz ve
    açık gölge pozisyonları o seans yönetilmez.

    Etkisi ÖLÇÜLEBİLİR bir taraflılıktır (atlanan seansta dokunulan stop görülmez, `bars_held`
    eksik sayılır) ve Rol-1'in kararı gerekir (rapor kaygı 1). Çivi bunu ADIYLA sabitler: kapı
    değişirse test kırılır ve karar YENİDEN sorulur — sessizce kaymaz."""
    casus = _Casus()
    monkeypatch.setattr(gi, "adim", casus)
    bars, idx = _universe()
    monkeypatch.setattr(loop.health, "halted", lambda: True)

    loop.daily_cycle(bars, idx, on_date=_son_tarih(idx))

    assert casus.cagri == [], \
        "HALT turunda gölge koştu — kanca kapının DIŞINA taşınmış; kaygı 1 çözülmüş olabilir, " \
        "raporu ve bu çiviyi güncelle"


# ==================================================================================================
# YARDIMCI — sentetik bar yolu (bedel çivisi için; motor testi Task 1'de)
# ==================================================================================================
def _bar_yolu():
    """Dört seanslık basit bir yol: tetik gelir, ertesi açılışta girilir, hedefe dokunur."""
    import pandas as pd
    gunler = pd.to_datetime(["2026-01-02", "2026-01-05", "2026-01-06", "2026-01-07"])
    satir = [(99.0, 101.0, 98.0, 100.5), (101.0, 103.0, 100.0, 102.0),
             (102.0, 111.0, 101.5, 110.0), (110.0, 112.0, 109.0, 111.0)]
    return pd.DataFrame(
        {"open": [r[0] for r in satir], "high": [r[1] for r in satir],
         "low": [r[2] for r in satir], "close": [r[3] for r in satir],
         "volume": [1_000_000.0] * 4}, index=gunler)
