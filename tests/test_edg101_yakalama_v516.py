"""v516 — EDG-2026-101 / TSK-200: brifing denetimi girdisinin İLERİYE DÖNÜK yakalanması (2026-09-17).

NEDEN (kart `research/cards/EDG-2026-101-denetci-muhakeme-uydurma-yakalama.yaml`,
`rol1_notu_2026_09_16`): denetçiye giden VERİ hiçbir yerde saklanmıyor ve bekçi VERİ'si geçmişe dönük
kurulamıyor — ölçüm seti ancak İLERİYE DÖNÜK yakalanarak kurulur. Tek yakalama noktası üç botun ortak
geçidi `soul_denetimi.gecir`dir: `ilk_metin` (denetlenen metin) ile `ilk_istem` (VERİ bloklarını
taşıyan üretici istemi) yalnız orada birlikte bulunur.

Numara v516: Rol-1 rezervi; ana checkout + worktree'lerde çakışma yok (ölçüldü 2026-09-17).

ÇİVİLER
  K0. Ölçülen modül BU ağacın modülüdür (worktree PYTHONPATH tuzağı: yanlış ağaçta yeşil kanıt değil).
  1.  Değişken yok/boş → hiçbir `edg101_*` yazımı denenmez, `edg101_yakalama_dustu` olayı yok.
  2.  Değişken dolu → tek satır; alan kümesi TAM; `ilk_istem` TAM (kırpılmamış) ve sır süzgecinden
      geçmiş (ham anahtar dosyada YOK); `veri_sha256` süzgeç SONRASI istemin çıkarıcı çıktısından.
  3.  Dönüş değeri ve `brifing_kural_denetimi` olayı yakalama açıkken ve kapalıyken EŞİT — her dalda.
  4.  Her dönüş dalında TAM BİR satır (dokuz dal, `test_soul_denetimi_v385` sahteleriyle); satırın
      `ilk_hukum`u yakalanan `ilk_metin`in hükmüdür, teslim hükmü değil.
  5.  Yazım (ya da satır kurulumu) düşerse `gecir` normal döner + `edg101_yakalama_dustu` uyarısı;
      olayda metin/istem YOK.
  5b. Göreli dizin reddedilir (canlı `state/` altına bağlanırdı) — uyarı adıyla, yazım yok.
  6.  Üç `60-edg101-yakalama.conf` birebir eşit; `Environment` dizini = `ReadWritePaths` yolu; `-` önekli;
      birim `ProtectSystem=strict` ve kendi `ReadWritePaths`i dizini KAPSAMIYOR (izin gerekli).
  7.  `dizinler.yml` yolu drop-in yoluyla eşit; sahip `meridian_kullanici`, mod 0700.
  8.  `edg101_` öneki f-string İÇİNDE literal: `codelaw._joined_glob` çağrı yerinden `*/edg101_*.jsonl`
      türetir ve modülde bu tek `store` yazımıdır. (Brief'in `DECLARED_SINK_PATTERNS` beyanı çivisi
      YAZILMADI: `codelaw.artifact_graph` yalnız `meridian/` kökünü tarar, `ops/` yazımı orada görünmez ve
      beyan `desen_kodda_yok` ile çürük sayılırdı — ölçüm ve karar Rol-1 devir raporunda.)
  9.  `gecir` gövdesinde TEK `return` var ve hemen önünde yakalama çağrısı durur — erken bir `return`
      eklenirse yakalama sessizce atlanırdı; dinamik çiviler yalnız bugünkü dalları görür.

Testler gerçek `state/`e yazmaz (`sandbox_state`); `monkeypatch.undo()` KULLANILMAZ.
"""
from __future__ import annotations

import ast
import datetime as dt
import hashlib
import importlib
import json
import pathlib

import pytest
import yaml

from tests.test_soul_denetimi_v385 import (  # tek-kaynak: sahte profil/kuyruk/cevaplar v385'te
    _ihlalli_cevap, _Kuyruk, _olaylar, _profil_evi, _temiz_cevap)

KOK = pathlib.Path(__file__).resolve().parent.parent
BIRIMLER = ("meridian-bekci", "meridian-brifing", "meridian-karne")
CONF_ADI = "60-edg101-yakalama.conf"
DUSUS_OLAYI = "edg101_yakalama_dustu"

# Sahte OpenRouter anahtarı — `notify.scrub` desen katmanının birebir biçimi (önek + 64 onaltılık).
SAHTE_ANAHTAR = "sk-or-v1-" + "ab12" * 16
ISTEM_IZI = "ZIMBIRTI_ISTEM_IZI"
METIN_IZI = "ZIMBIRTI_METIN_IZI"


@pytest.fixture
def sd():
    return importlib.import_module("ops.soul_denetimi")


def _istem(sd, dolgu: int = 0) -> str:
    """VERİ bloklu sahte üretici istemi. `dolgu` > 0 ise istem uzatılır (kırpma çivisi)."""
    parcalar = [
        "## Bugünün kaynakları — HAZIR HESAPLANMIŞ VERİ",
        "### alarm\n" + sd._veri_bloku("alarm", f"MECHANISM_STALE 5 kez · {ISTEM_IZI} · "
                                                 f"anahtar={SAHTE_ANAHTAR}"),
    ]
    if dolgu:
        parcalar.append("### uzun\n" + sd._veri_bloku("uzun", "satır verisi 12345 " * dolgu))
    parcalar.append("## Talimat\nbrifingi yaz")
    return "\n\n".join(parcalar)


def _gecir(sd, tmp_path, *, cagir, ilk=f"ilk metin {METIN_IZI}", terimler=(), istem=None, **kw):
    return sd.gecir(profil_evi=_profil_evi(tmp_path), ilk_metin=ilk,
                    ilk_istem=_istem(sd) if istem is None else istem,
                    veri_terimleri=list(terimler), cagir=cagir, bot="sef", **kw)


def _satirlar(dizin: pathlib.Path) -> list[dict]:
    satirlar: list[dict] = []
    for p in sorted(dizin.glob("edg101_*.jsonl")):
        satirlar += [json.loads(s) for s in p.read_text(encoding="utf-8").splitlines() if s.strip()]
    return satirlar


class _PatlayanDenetci:
    """Verilen cevapları sırayla döner; cevaplar tükenince her çağrıda patlar."""

    def __init__(self, *cevaplar):
        self.cevaplar = list(cevaplar)

    def __call__(self, _istem):
        if not self.cevaplar:
            raise RuntimeError("denetçi profili 150 sn'de bitmedi")
        return self.cevaplar.pop(0)


# DOKUZ DÖNÜŞ DALI — `gecir` docstring'indeki DALLAR + `_yeniden`in ret dalları. Her giriş TAZE sahte
# üretir (kuyruklar durumludur). `ilk_kaynak`: yakalanan `ilk_metin`in hükmünü kimin verdiği.
DALLAR = {
    "temiz": (lambda: dict(cagir=_Kuyruk(_temiz_cevap())), "llm"),
    "mekanik_hukum": (lambda: dict(cagir=_Kuyruk("düzeltilmiş: MECHANISM_STALE 5 kez oldu",
                                                 _temiz_cevap()),
                                   ilk="terim yok burada", terimler=["MECHANISM_STALE"]), "mekanik"),
    "llm_dustu": (lambda: dict(cagir=_PatlayanDenetci()), "llm_dustu"),
    "yeniden_uretim_temiz": (lambda: dict(cagir=_Kuyruk(
        _ihlalli_cevap(), "düzeltilmiş metin ve gerekçesi", _temiz_cevap())), "llm"),
    "iki_kez_ihlal_ham": (lambda: dict(cagir=_Kuyruk(
        _ihlalli_cevap(), "yine bozuk metin", _ihlalli_cevap(("tetti", "zıpzıp")))), "llm"),
    "yeniden_uretim_reddedildi": (lambda: dict(
        cagir=_Kuyruk(_ihlalli_cevap(), "..."),
        dogrula=lambda c: "çok kısa" if len(c) < 20 else None), "llm"),
    "yeniden_uretim_cagrisi_patladi": (lambda: dict(cagir=_PatlayanDenetci(_ihlalli_cevap())), "llm"),
    "cagri_tavani": (lambda: dict(cagir=_Kuyruk(_temiz_cevap()), baslangic_cagri=4), "llm_dustu"),
    "yeniden_uretim_denetlenemedi": (lambda: dict(cagir=_Kuyruk(
        _ihlalli_cevap(), "düzeltilmiş metin ve gerekçesi", "json değil, düz metin")), "llm"),
}


# ================================================================================================
# K0 — ölçülen modül bu ağacın modülü
# ================================================================================================

def test_K0_olculen_modul_BU_agactan_yuklenir(sd):
    from meridian import store
    for mod in (sd, store):
        assert pathlib.Path(mod.__file__).resolve().is_relative_to(KOK), (
            f"{mod.__name__} başka bir ağaçtan yüklendi ({mod.__file__}) — yeşil bu ağacı ölçmez")


# ================================================================================================
# 1 — değişken yok/boş → yakalama KAPALI
# ================================================================================================

@pytest.mark.parametrize("deger", [None, "", "   "], ids=["yok", "bos", "bosluk"])
def test_1_degisken_yok_ya_da_bos_YAKALAMA_KAPALI(sd, tmp_path, monkeypatch, sandbox_state, deger):
    from meridian import store
    if deger is None:
        monkeypatch.delenv(sd.EDG101_YAKALAMA_ENV, raising=False)
    else:
        monkeypatch.setenv(sd.EDG101_YAKALAMA_ENV, deger)
    asil = store.append_jsonl
    denenen: list[str] = []

    def _casus(name, row):
        denenen.append(str(name))
        return asil(name, row)

    monkeypatch.setattr(store, "append_jsonl", _casus)
    g = _gecir(sd, tmp_path, cagir=_Kuyruk(_temiz_cevap()))
    assert g.metin == f"ilk metin {METIN_IZI}", f"teslim bozuldu: {g!r}"
    assert not [n for n in denenen if "edg101_" in n], f"kapalı yakalama yazım denedi: {denenen}"
    assert _olaylar(DUSUS_OLAYI) == [], "kapalı yakalama düşüş olayı üretti"


# ================================================================================================
# 2 — değişken dolu → tek satır, TAM + süzgeçten geçmiş girdi
# ================================================================================================

def test_2_dolu_degisken_TEK_SATIR_tam_ve_suzulmus_girdi(sd, tmp_path, monkeypatch, sandbox_state):
    from meridian import notify
    dizin = tmp_path / "yakalama"
    monkeypatch.setenv(sd.EDG101_YAKALAMA_ENV, str(dizin))
    istem = _istem(sd, dolgu=3000)
    ilk = f"ilk metin {METIN_IZI} anahtar={SAHTE_ANAHTAR}"
    assert len(istem) > 50_000, "kırpma çivisi kör: istem yeterince uzun değil"
    g = _gecir(sd, tmp_path, cagir=_Kuyruk(_temiz_cevap()), ilk=ilk, istem=istem)

    dosyalar = sorted(dizin.glob("edg101_*.jsonl"))
    assert len(dosyalar) == 1, f"gün defteri tek değil: {dosyalar}"
    ham = dosyalar[0].read_text(encoding="utf-8")
    assert SAHTE_ANAHTAR not in ham, "HAM anahtar yakalama dosyasına düştü — süzgeç uygulanmadı"
    satirlar = _satirlar(dizin)
    assert len(satirlar) == 1, f"tek çağrı, {len(satirlar)} satır"
    s = satirlar[0]
    assert set(s) == {"ts", "bot", "ilk_metin", "ilk_istem", "veri_sha256", "teslim_karari",
                      "yeniden_uretim", "ilk_hukum", "teslim_hukum"}, f"alan kümesi: {sorted(s)}"
    ts = dt.datetime.fromisoformat(s["ts"])
    assert ts.utcoffset() == dt.timedelta(0), f"ts UTC değil: {s['ts']}"
    assert dosyalar[0].name == f"edg101_{ts.strftime('%Y-%m-%d')}.jsonl", "dosya günü ts günü değil"
    assert s["bot"] == "sef"
    assert s["ilk_istem"] == notify.scrub(istem), "istem TAM ve süzgeçten geçmiş hâliyle yazılmadı"
    assert s["ilk_metin"] == notify.scrub(ilk), "metin süzgeçten geçmiş hâliyle yazılmadı"
    assert ISTEM_IZI in s["ilk_istem"] and s["ilk_istem"].endswith("brifingi yaz"), "istem kırpıldı"

    beklenen = hashlib.sha256(
        sd._ilk_istemden_veri_cikar(notify.scrub(istem)).encode("utf-8")).hexdigest()
    ham_sha = hashlib.sha256(sd._ilk_istemden_veri_cikar(istem).encode("utf-8")).hexdigest()
    assert beklenen != ham_sha, "ön koşul: süzgeç VERİ'yi değiştirmeli (çivi ayırt edici olsun)"
    assert s["veri_sha256"] == beklenen, "veri_sha256 süzgeç SONRASI istemin çıkarıcı çıktısı değil"

    assert s["teslim_karari"] == g.hukum_adi == "temiz" and s["yeniden_uretim"] is False
    assert s["ilk_hukum"] == {"kaynak": "llm", "uydurma": [], "terim_ihlal": [], "suzulen": []}
    assert s["teslim_hukum"] == s["ilk_hukum"]
    from meridian import store
    olaylar_metni = json.dumps(store.read_jsonl("events.jsonl"), ensure_ascii=False)
    assert ISTEM_IZI not in olaylar_metni, "istem içeriği olay defterine sızdı"


# ================================================================================================
# 3 — dönüş değeri ve olay, yakalama açık/kapalı EŞİT
# ================================================================================================

def _son_denetim_olayi() -> dict:
    olay = _olaylar()
    assert olay, "kural denetimi olayı yazılmadı"
    return {k: v for k, v in olay[-1].items() if k != "ts"}


@pytest.mark.parametrize("dal", sorted(DALLAR))
def test_3_donus_ve_olay_ACIK_KAPALI_ESIT(sd, tmp_path, monkeypatch, sandbox_state, dal):
    kur, _ = DALLAR[dal]
    monkeypatch.delenv(sd.EDG101_YAKALAMA_ENV, raising=False)
    g_kapali = _gecir(sd, tmp_path, **kur())
    olay_kapali = _son_denetim_olayi()
    monkeypatch.setenv(sd.EDG101_YAKALAMA_ENV, str(tmp_path / "yakalama"))
    g_acik = _gecir(sd, tmp_path, **kur())
    olay_acik = _son_denetim_olayi()
    assert g_acik == g_kapali, f"yakalama dönüş değerini değiştirdi:\n{g_acik!r}\n{g_kapali!r}"
    assert olay_acik == olay_kapali, "yakalama `brifing_kural_denetimi` olayını değiştirdi"
    assert len(_satirlar(tmp_path / "yakalama")) == 1


# ================================================================================================
# 4 — her dönüş dalında TAM BİR satır
# ================================================================================================

@pytest.mark.parametrize("dal", sorted(DALLAR))
def test_4_her_donus_dalinda_TAM_BIR_satir(sd, tmp_path, monkeypatch, sandbox_state, dal):
    kur, ilk_kaynak = DALLAR[dal]
    dizin = tmp_path / "yakalama"
    monkeypatch.setenv(sd.EDG101_YAKALAMA_ENV, str(dizin))
    g = _gecir(sd, tmp_path, **kur())
    satirlar = _satirlar(dizin)
    assert len(satirlar) == 1, f"{dal}: {len(satirlar)} satır (beklenen TAM bir)"
    s = satirlar[0]
    assert s["teslim_karari"] == g.hukum_adi and s["yeniden_uretim"] is g.yeniden_uretim, (dal, s)
    assert s["teslim_hukum"]["kaynak"] == g.hukum.kaynak, (dal, s["teslim_hukum"])
    assert s["ilk_hukum"]["kaynak"] == ilk_kaynak, (dal, s["ilk_hukum"])


def test_4b_ilk_hukum_YAKALANAN_METNIN_hukmudur_teslim_hukmu_degil(sd, tmp_path, monkeypatch,
                                                                    sandbox_state):
    """Yeniden-üretim DENETLENEMEYİNCE ikinci metin gider ve teslim hükmü `llm_dustu`dur — ilk turun
    `uydurma` listesi yalnız `ilk_hukum`da yaşar. Satır yalnız teslim hükmünü taşısaydı, ölçüm
    canlının yakalanan metin hakkındaki gerçek hükmünü kaybederdi.

    SENARYO DEĞİŞTİ (TSK-196, 2026-09-17): çivi eskiden yeniden-üretim ÇAĞRISININ patladığı dalı
    sürüyordu; o dal artık ilk hükmü KORUR (teslim hükmü = ilk hüküm, `teslim_karari` =
    `ihlal_duzeltilemedi` — `tests/test_ihlal_duzeltilemedi_v519.py` çivi 5) ve iki hükmü AYIRT
    ETMEZ. Ayrımı ölçmeye devam etmek için iki hükmün hâlâ ayrıştığı dal sürülür: yeniden-DENETİM
    patlar."""
    dizin = tmp_path / "yakalama"
    monkeypatch.setenv(sd.EDG101_YAKALAMA_ENV, str(dizin))
    g = _gecir(sd, tmp_path, cagir=_PatlayanDenetci(_ihlalli_cevap(("tetti", "kritikisi")),
                                                    "düzeltilmiş metin ve gerekçesi"))
    assert g.hukum.kaynak == "llm_dustu" and g.metin == "düzeltilmiş metin ve gerekçesi", (
        f"ön koşul: {g!r}")
    s = _satirlar(dizin)[0]
    assert s["ilk_hukum"] == {"kaynak": "llm", "uydurma": ["tetti", "kritikisi"],
                              "terim_ihlal": [], "suzulen": []}, s["ilk_hukum"]
    assert s["teslim_hukum"]["kaynak"] == "llm_dustu" and s["teslim_hukum"]["uydurma"] == []


# ================================================================================================
# 5 — yakalama düşerse teslim düşmez, olayda metin yok
# ================================================================================================

@pytest.mark.parametrize("ariza", ["yazim_oserror", "satir_kurulumu_valueerror"])
def test_5_yakalama_duserse_gecir_NORMAL_doner_ve_uyarir(sd, tmp_path, monkeypatch, sandbox_state,
                                                         ariza):
    from meridian import notify, store
    monkeypatch.delenv(sd.EDG101_YAKALAMA_ENV, raising=False)
    g_ref = _gecir(sd, tmp_path, cagir=_Kuyruk(_temiz_cevap()))

    dizin = tmp_path / "yakalama"
    monkeypatch.setenv(sd.EDG101_YAKALAMA_ENV, str(dizin))
    if ariza == "yazim_oserror":
        asil = store.append_jsonl

        def _secici(name, row):
            if "edg101_" in str(name):
                raise OSError(30, "Read-only file system")
            return asil(name, row)

        monkeypatch.setattr(store, "append_jsonl", _secici)
        beklenen_hata = "OSError"
    else:
        asil_scrub = notify.scrub

        def _patlayan_scrub(text):
            if ISTEM_IZI in str(text):
                raise ValueError("süzgeç patladı")
            return asil_scrub(text)

        monkeypatch.setattr(notify, "scrub", _patlayan_scrub)
        beklenen_hata = "ValueError"

    g = _gecir(sd, tmp_path, cagir=_Kuyruk(_temiz_cevap()))
    assert g == g_ref, f"yakalama arızası dönüş değerini değiştirdi: {g!r}"
    assert _satirlar(dizin) == [], "düşen yakalama yine de satır bıraktı"
    dusus = _olaylar(DUSUS_OLAYI)
    assert len(dusus) == 1, f"düşüş olayı tek değil: {dusus}"
    o = dusus[0]
    assert o.get("level") == "warn" and o.get("hata") == beklenen_hata, o
    assert str(o.get("yol", "")).startswith(str(dizin) + "/edg101_"), o
    assert str(o.get("yol", "")).endswith(".jsonl"), o
    metin = json.dumps(o, ensure_ascii=False)
    assert ISTEM_IZI not in metin and METIN_IZI not in metin, f"olaya metin/istem sızdı: {o}"


def test_5b_GORELI_dizin_reddedilir_state_altina_yazilmaz(sd, tmp_path, monkeypatch, sandbox_state):
    from meridian import config
    monkeypatch.setenv(sd.EDG101_YAKALAMA_ENV, "olcum/edg101")
    g = _gecir(sd, tmp_path, cagir=_Kuyruk(_temiz_cevap()))
    assert g.metin == f"ilk metin {METIN_IZI}"
    assert not list(pathlib.Path(config.STATE).rglob("edg101_*.jsonl")), (
        "göreli dizin canlı state/ altına bağlandı (kart kill-list: ölçüm canlı deftere yazamaz)")
    dusus = _olaylar(DUSUS_OLAYI)
    assert len(dusus) == 1 and dusus[0].get("hata") == "dizin_goreli", dusus


# ================================================================================================
# 6 — üç drop-in: birebir eşit, tek dizin, `-` önekli izin, izin GEREKLİ
# ================================================================================================

def _yonergeler(metin: str) -> list[str]:
    return [s.strip() for s in metin.splitlines() if s.strip() and not s.strip().startswith(("#", ";"))]


def _birim_dizini(sd) -> str:
    metin = (KOK / "deploy" / "oracle-a1" / f"{BIRIMLER[0]}.service.d" / CONF_ADI).read_text(
        encoding="utf-8")
    env = [s for s in _yonergeler(metin) if s.startswith(f"Environment={sd.EDG101_YAKALAMA_ENV}=")]
    assert len(env) == 1, f"Environment satırı tek değil: {env}"
    return env[0].split("=", 2)[2]


def test_6_uc_dropin_BIREBIR_esit_ve_tek_dizini_gosterir(sd):
    import posixpath
    metinler = {b: (KOK / "deploy" / "oracle-a1" / f"{b}.service.d" / CONF_ADI).read_text(
        encoding="utf-8") for b in BIRIMLER}
    assert len(set(metinler.values())) == 1, "üç drop-in içerik olarak ayrıştı"
    yon = _yonergeler(metinler[BIRIMLER[0]])
    dizin = _birim_dizini(sd)
    rwp = [s for s in yon if s.startswith("ReadWritePaths=")]
    assert len(rwp) == 1, f"ReadWritePaths tek değil: {rwp}"
    yollar = rwp[0].split("=", 1)[1].split()
    assert yollar == [f"-{dizin}"], (
        f"ReadWritePaths `-` önekli TEK yol olarak Environment dizinini göstermiyor: {yollar} ↔ {dizin}")
    assert set(yon) == {"[Service]", f"Environment={sd.EDG101_YAKALAMA_ENV}={dizin}", rwp[0]}, yon
    assert posixpath.isabs(dizin) and dizin.startswith("/opt/veri/"), dizin
    assert "/state" not in dizin and not dizin.startswith("/opt/meridian"), dizin

    for b in BIRIMLER:
        birim = _yonergeler((KOK / "deploy" / "oracle-a1" / f"{b}.service").read_text(encoding="utf-8"))
        assert "ProtectSystem=strict" in birim, f"{b}: ön koşul — strict değilse izin gerekçesi çürür"
        kendi = [p.lstrip("-") for s in birim if s.startswith("ReadWritePaths=")
                 for p in s.split("=", 1)[1].split()]
        kapsayan = [p for p in kendi if dizin == p or dizin.startswith(p.rstrip("/") + "/")]
        assert not kapsayan, f"{b}: birim zaten {kapsayan} yazabiliyor — drop-in izni gereksiz olurdu"


def test_6b_dropin_dizinleri_A0_listesinde(sd):
    defaults = yaml.safe_load((KOK / "deploy" / "ansible" / "roles" / "meridian_a1" / "defaults" /
                               "main.yml").read_text(encoding="utf-8"))
    for b in BIRIMLER:
        assert f"{b}.service.d" in defaults["dropin_dizinleri"], f"{b}.service.d A0 listesinde yok"


# ================================================================================================
# 7 — A0 dizin görevi drop-in ile aynı yolu kurar
# ================================================================================================

def test_7_dizinler_yml_yolu_dropin_ile_esit_ve_0700(sd):
    gorevler = yaml.safe_load((KOK / "deploy" / "ansible" / "roles" / "meridian_a1" / "tasks" /
                               "dizinler.yml").read_text(encoding="utf-8"))
    dizin = _birim_dizini(sd)
    eslesen = [g["ansible.builtin.file"] for g in gorevler
               if "edg101" in str(g.get("ansible.builtin.file", {}).get("path", ""))]
    assert len(eslesen) == 1, f"edg101 dizin görevi tek değil: {eslesen}"
    a = eslesen[0]
    assert a["path"] == dizin, f"A0 yolu ({a['path']}) drop-in dizininden ({dizin}) AYRIŞTI"
    assert a["state"] == "directory" and str(a["mode"]) == "0700", a
    assert a["owner"] == a["group"] == "{{ meridian_kullanici }}", a


# ================================================================================================
# 8 — `edg101_` öneki f-string içinde LİTERAL; modüldeki tek `store` yazımı
# ================================================================================================

def test_8_edg101_oneki_LITERAL_ve_tek_store_yazimi(sd):
    from meridian import codelaw
    agac = ast.parse(pathlib.Path(sd.__file__).read_text(encoding="utf-8"))
    yazimlar: list[tuple[str, ast.Call]] = []
    for fn in ast.walk(agac):
        if not isinstance(fn, ast.FunctionDef):
            continue
        for n in ast.walk(fn):
            if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                    and isinstance(n.func.value, ast.Name) and n.func.value.id == "store"
                    and n.func.attr in codelaw.WRITE_CALLS):
                yazimlar.append((fn.name, n))
    assert [ad for ad, _ in yazimlar] == ["_edg101_yakala"], (
        f"modülde beklenen TEK store yazımı yakalama fonksiyonunda değil: {[a for a, _ in yazimlar]}")
    cagri = yazimlar[0][1]
    assert cagri.func.attr == "append_jsonl", ast.dump(cagri)[:120]
    glob = codelaw._joined_glob(cagri.args[0], codelaw._module_consts(agac), {})
    assert glob == "*/edg101_*.jsonl", (
        f"türetilen şekil `{glob}` — `edg101_` öneki f-string içinde literal değil (desen genişledi)")


# ================================================================================================
# 9 — `gecir` TEK dönüş noktası, yakalama hemen önünde
# ================================================================================================

def test_9_gecir_TEK_return_ve_yakalama_hemen_onunde(sd):
    agac = ast.parse(pathlib.Path(sd.__file__).read_text(encoding="utf-8"))
    gecir = next(n for n in agac.body if isinstance(n, ast.FunctionDef) and n.name == "gecir")

    def _donusler(dugum) -> list[ast.Return]:
        bulunan: list[ast.Return] = []
        for cocuk in ast.iter_child_nodes(dugum):
            if isinstance(cocuk, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
                continue          # iç fonksiyonların dönüşleri `gecir`in dönüşü değildir
            if isinstance(cocuk, ast.Return):
                bulunan.append(cocuk)
            bulunan += _donusler(cocuk)
        return bulunan

    donusler = _donusler(gecir)
    assert len(donusler) == 1, f"`gecir`de {len(donusler)} return — yakalamayı atlayan dal doğabilir"
    assert gecir.body[-1] is donusler[0], "tek return gövdenin SON deyimi değil"
    once = gecir.body[-2]
    assert (isinstance(once, ast.Expr) and isinstance(once.value, ast.Call)
            and isinstance(once.value.func, ast.Name) and once.value.func.id == "_edg101_yakala"), (
        f"return'ün hemen önünde yakalama çağrısı yok: {ast.dump(once)[:160]}")
