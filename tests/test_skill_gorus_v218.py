"""DALGA W3 (N2b+Ç3) — skill yaşam-döngüsü dürüstlüğü + görüş defteri v1 (kart EDG-2026-019).

DÖRT SINIF, HEPSİ ÖLÇÜLMÜŞ BİR KUSURDAN DOĞDU:
  Ç3  `skills.catalog()` kayıt defterinin BİLDİĞİ `retired` alanını düşürüyordu → katalog 67 satırı
      DÜZ döküyor, arşiv canlı skill sanılıyordu (sayı doğru, etiket yanlış).
  Ç3b Eksen-2 teşhis kovaları arşivi `gercek_katman_olculmemis` sayıyordu (57'nin 36'sı arşivdi).
  v207 pano paydası 67 (kayıt TOPLAMI) idi; ölçülen gerçek "31 AKTİF skillin ..."tir.
  EDG-2026-019 görüş defteri: skill katmanının kanıtı hiç birikmiyordu.

TESTLERİN ÇİVİLEDİĞİ ŞEY EŞİK DEĞİL DAVRANIŞTIR: eşikler kartta donmuş, burada yalnız OKUNUR.
"""
import json
import pathlib
import re

import pytest

from meridian import api, codelaw, skill_gorus as sg, skills, store

# YAZIM FİİLLERİNİN TEK KAYNAĞI: `codelaw.WRITE_CALLS` — artefakt grafiğini kuran denetçinin
# KENDİ tanımı. Buradaki desen ondan TÜRETİLİR; ikinci bir elle liste, denetçi yeni bir yazım
# fiili öğrendiği gün sessizce kör kalırdı (tek-kaynak yasası). `test_skill_gorus_llm_v357.py`
# de aynı kaynaktan besleniyor.
WRITE_CALL_RE = r"store\.(?:" + "|".join(sorted(codelaw.WRITE_CALLS)) + r")\(\s*([A-Z_]+)"


# EDG-2026-019 KILL#1 (Rol-1 hükmü 2026-08-23): katman canlıda KAPALI (config.SKILL_GORUS_URETIM_ACIK
# = False). Bu dosyanın çivileri MEKANİZMAYI ölçer (toplama/çözücü/p95 düzeneği) — kapanış hükmünün
# kendi çivisi tests/test_e_partisi_v278.py'dedir. Mekanizma testleri bayrağı süreç-yerel AÇAR;
# üretim varsayılanına dokunulmaz.
@pytest.fixture(autouse=True)
def _gorus_uretimi_test_icin_acik(monkeypatch):
    from meridian import config as _cfg
    monkeypatch.setattr(_cfg, "SKILL_GORUS_URETIM_ACIK", True)


# =================================================================================================
# FİKSTÜRLER — kayıt defteri: aktif / arşiv / korumalı / LLM-bağlamlı dördü de temsil edilir
# =================================================================================================
def _seed_reg():
    reg = {"skills": {
        # aktif + korumasız + DETERMİNİSTİK (motor koşturur) → görüş evreni
        "vcp-screener": {"category": "swing", "enabled": True, "mode": "active",
                         "pipeline": "P2_SCREEN"},
        "pullback-screener": {"category": "swing", "enabled": True, "mode": "active",
                              "pipeline": "P2_SCREEN"},
        # aktif + KORUMALI → evren dışı, teşhiste `korumali`
        "position-sizer": {"category": "meta", "enabled": True, "mode": "active",
                           "pipeline": "P3_PLAN"},
        # aktif + korumasız ama LLM-bağlamlı (ENGINE_IMPLEMENTED değil) → evren dışı
        "theme-detector": {"category": "research", "enabled": True, "mode": "active",
                           "pipeline": "P2_SCREEN"},
        # ARŞİV (2026-07-30 denetimi) → hiçbir kolun adayı değil
        "sector-analyst": {"category": "research", "enabled": False, "mode": "disabled",
                           "retired": True, "retired_folder": "skills/_emekli/sector-analyst"},
        "ftd-detector": {"category": "research", "enabled": False, "mode": "disabled",
                         "retired": True, "retired_folder": "skills/_emekli/ftd-detector"},
    }}
    store.write_json("skills_registry.json", reg)
    return reg


def _seed_klasor(tmp_path):
    """Kütüphane klasörünü de KURAR — ve 38↔37↔36 desenini KÜÇÜK ÖLÇEKTE tekrar eder:
    arşiv altında 2 gerçek skill + 1 README.md dosyası + 1 BOŞ mezar taşı dizini (`shadow`).
    Canlıda üç sayının farkı tam olarak buydu; fikstür onu yeniden üretmezse test o farkı
    bir daha yakalayamaz."""
    kok = tmp_path / "skills"
    for ad in ("vcp-screener", "pullback-screener", "position-sizer", "theme-detector"):
        (kok / ad).mkdir(parents=True)
        (kok / ad / "SKILL.md").write_text(f"---\nname: {ad}\ndescription: {ad} amacı.\n---\n")
    ars = kok / "_emekli"
    for ad in ("sector-analyst", "ftd-detector"):
        (ars / ad).mkdir(parents=True)
        (ars / ad / "SKILL.md").write_text(f"---\nname: {ad}\ndescription: arşiv.\n---\n")
    (ars / "shadow").mkdir()                       # SKILL.md'siz boş mezar taşı (canlıdaki hâli)
    (ars / "README.md").write_text("# arşiv\n")    # dizin değil DOSYA — `ls` sayar, envanter saymaz
    return kok


@pytest.fixture
def kayit(sandbox_state, tmp_path, monkeypatch):
    from meridian import analytics, config
    monkeypatch.setattr(analytics, "skill_attribution", lambda: {"skills": []})
    # KÜTÜPHANE KLASÖRÜ DE SANDBOX'LANIR: `catalog()` kayıt defterini KLASÖRLE birleştirir, yani
    # gerçek `skills/` dizini sızarsa sayımlar operatörün diskine bağlı olur (ve test bir şey
    # KANITLAMAZ — `hermes.AGENT_CONFIG` dersiyle aynı sınıf).
    monkeypatch.setattr(config, "SKILLS", _seed_klasor(tmp_path))
    monkeypatch.setattr(skills, "_DESC_CACHE", None)
    _seed_reg()
    yield sandbox_state
    skills._DESC_CACHE = None


# =================================================================================================
# Ç3 — `retired` ALANI KATALOGTAN GEÇİYOR
# =================================================================================================
def test_katalog_retired_alanini_TASIR(kayit):
    """Kusurun kendisi: kayıt `retired: true` diyor, katalog söylemiyordu."""
    cat = {c["name"]: c for c in skills.catalog()}
    assert cat["sector-analyst"]["retired"] is True
    assert cat["sector-analyst"]["yasam_dongusu"] == skills.ARSIV
    assert cat["vcp-screener"]["retired"] is False
    assert cat["vcp-screener"]["yasam_dongusu"] == skills.AKTIF


def test_aktif_katalog_arsivi_DISLAR_ve_tek_yerden_turer(kayit):
    aktif = {c["name"] for c in skills.aktif_katalog()}
    assert "sector-analyst" not in aktif and "ftd-detector" not in aktif
    assert {"vcp-screener", "pullback-screener", "position-sizer", "theme-detector"} <= aktif
    # TEK YER: ayrım `yasam_dongusu()`ndan gelir; çağıranların kendi `retired` sınamasını
    # yazması, aynı ayrımın altı yerde altı farklı biçimde bozulması demekti.
    assert skills.yasam_dongusu({"retired": True}) == skills.ARSIV
    assert skills.yasam_dongusu({}) == skills.AKTIF
    assert skills.yasam_dongusu(None) == skills.AKTIF     # kayıtsız ad ARŞİV DEĞİLDİR


def test_envanter_klasor_ve_kayit_paydalarini_AYRI_olcer(kayit):
    """38↔37↔36 üçlemesi KÜÇÜK ÖLÇEKTE: `ls` DOSYA sayar (4), dizin sayımı mezar taşını da sayar
    (3), kayıt gerçek arşiv KAYITLARINI sayar (2). Üçü de doğru; PAYDALARI farklı."""
    e = skills.envanter()
    assert e["kayit"] == {"toplam": 6, "aktif": 4, "arsiv": 2}
    assert e["klasor"] == {"aktif_dizin": 4, "aktif_skill_md": 4,
                           "arsiv_girdi": 4, "arsiv_dizin": 3, "arsiv_skill_md": 2}
    # FARK ADIYLA ÇIKAR: mezar taşı hem "kayıtsız" hem "SKILL.md'siz" olarak görünür, README ise
    # dizin-olmayan girdi sayacında. Hiçbiri sessizce "bir skill" sayılmaz.
    assert e["fark"]["arsiv_dizin_ama_kayitsiz"] == ["shadow"]
    assert e["fark"]["arsiv_dizin_skill_md_yok"] == ["shadow"]
    assert e["fark"]["arsiv_disi_girdi"] == 1                      # README.md
    assert e["fark"]["kayitsiz_klasor"] == [] and e["fark"]["kayitli_aktif_klasorsuz"] == []
    # DOĞRU ENVANTER = KAYIT ∩ KLASÖR: aktif tarafta iki sayı ÖRTÜŞÜR.
    assert e["kayit"]["aktif"] == e["klasor"]["aktif_skill_md"]
    assert e["kayit"]["arsiv"] == e["klasor"]["arsiv_skill_md"]
    assert "hukum" in e


# =================================================================================================
# Ç3b — TEŞHİS KOVASI: `arsiv` AYRI, `gercek_katman_olculmemis` YALNIZ AKTİFLER
# =================================================================================================
def test_arsiv_kovasi_AYRI_ve_olculmemis_YALNIZ_aktifleri_kapsar(kayit):
    d = skills.axis2_diagnosis()
    assert d["sayim"].get("arsiv") == 2
    arsivdekiler = {r["skill"] for r in d["kovalar"]["arsiv"]}
    assert arsivdekiler == {"sector-analyst", "ftd-detector"}
    # ÖLÇÜLMEMİŞ kovalarının HİÇBİRİNDE arşiv kaydı olamaz — sınıfın kapanışı budur.
    for ad, satirlar in d["kovalar"].items():
        if ad.startswith("gercek_katman_olculmemis"):
            assert not ({r["skill"] for r in satirlar} & arsivdekiler), \
                f"{ad} kovasına arşiv kaydı sızdı — sayı doğru, etiket yanlış sınıfı geri döndü"
    assert d["aktif_payda"] == 4 == sum(len(v) for k, v in d["kovalar"].items() if k != "arsiv")


def test_arsiv_ONERI_ve_OTOMATIK_kollarin_adayi_DEGIL(kayit, monkeypatch):
    """Arşiv kaydı `enabled=False` olduğu için zaten eleniyordu; ELEME ile TANIM ayrı şeydir."""
    from meridian import analytics
    monkeypatch.setattr(analytics, "skill_attribution", lambda: {"skills": [
        {"skill": "sector-analyst", "n": 40, "avg_r": -0.9, "n_cf": 500, "cf_avg_r": -0.9},
        {"skill": "vcp-screener", "n": 40, "avg_r": -0.9},
    ]})
    adlar = {r["skill"] for r in skills.recommend_from_attribution()}
    assert "vcp-screener" in adlar and "sector-analyst" not in adlar
    kuru = skills.auto_shadow_from_evidence(apply=False)
    hepsi = {r["skill"] for kova in ("uygulanan", "advisory", "atlanan", "esik_dogrulamasi",
                                     "motor_ici_esik_asan") for r in (kuru.get(kova) or [])}
    assert "sector-analyst" not in hepsi


# =================================================================================================
# v207 PANO PAYDASI — AKTİF KÜMEDEN, SABİT SAYI YOK (C10)
# =================================================================================================
def _ozet():
    """Panonun GERÇEK yolu: `analytics.learning_automation` `eksen2.kovalar` alanına teşhisin
    SAYIM haritasını koyar (liste değil) — test o sözleşmeyi taklit eder, kendi şemasını değil."""
    return api._eksen2_ozeti({"kovalar": skills.axis2_diagnosis()["sayim"]})


def test_pano_paydasi_AKTIF_kumeden_gelir_arsiv_HARIC(kayit):
    ozet = _ozet()
    assert ozet["durum"] == "dolu"
    assert ozet["toplam_skill"] == 4          # AKTİF küme
    assert ozet["arsiv"] == 2
    assert ozet["kayit_toplam"] == 6          # kayıt TOPLAMI ayrı sayı olarak durur
    assert ozet["olculen"] + ozet["olculmemis"] + ozet["korumali"] == ozet["toplam_skill"]
    assert "4" in ozet["payda"] and "arşiv" in ozet["payda"].lower()
    assert "67" not in ozet["payda"]          # eski payda (kayıt toplamı) geri gelmesin


def test_payda_KAYNAKTAN_turer_kayit_degisince_KAYAR(kayit):
    """Aynı fonksiyon, değişen kaynak: payda sabitse bu test iki koşuda aynı sayıyı görürdü."""
    once = _ozet()["toplam_skill"]
    reg = store.read_json("skills_registry.json", {})
    reg["skills"]["yeni-aktif-skill"] = {"category": "x", "enabled": True, "mode": "active"}
    reg["skills"]["vcp-screener"]["retired"] = True        # biri emekliye ayrıldı
    store.write_json("skills_registry.json", reg)
    sonra = _ozet()
    assert sonra["toplam_skill"] == once            # +1 aktif, −1 aktif → net aynı
    assert sonra["arsiv"] == 3 and sonra["kayit_toplam"] == 7
    reg["skills"]["ikinci-aktif"] = {"category": "x", "enabled": True, "mode": "active"}
    store.write_json("skills_registry.json", reg)
    assert _ozet()["toplam_skill"] == once + 1      # payda kaynağı GERÇEKTEN takip ediyor


def test_ozet_koduna_SABIT_SKILL_SAYISI_yazilmamis():
    """C10 çivisi: payda kodda LİTERAL olamaz. 2026-07-30 arşivi 'toplam 66 skill' yazısını bir
    gecede yalana çevirmişti; aynı sınıf api'de tekrarlanmasın diye kaynak AST ile taranır
    (yorum ve docstring BEYANDIR — orada sayı yazmak serbest; ÇALIŞAN kodda değil)."""
    import ast
    agac = ast.parse(pathlib.Path(api.__file__).read_text())
    fn = next(n for n in ast.walk(agac)
              if isinstance(n, ast.FunctionDef) and n.name == "_eksen2_ozeti")
    govde = fn.body[1:] if (fn.body and isinstance(fn.body[0], ast.Expr)
                            and isinstance(fn.body[0].value, ast.Constant)
                            and isinstance(fn.body[0].value.value, str)) else fn.body
    sayilar = {n.value for g in govde for n in ast.walk(g)
               if isinstance(n, ast.Constant) and isinstance(n.value, int)
               and not isinstance(n.value, bool)}
    assert not {n for n in sayilar if n >= 10}, \
        f"_eksen2_ozeti gövdesinde iki basamaklı literal var {sayilar} — payda türetilmeli, yazılmamalı"


def test_ozetin_OLCULEMEDI_dali_SIFIR_uydurmaz(kayit):
    bos = api._eksen2_ozeti({"kovalar": {}})
    assert bos["durum"] == "ÖLÇÜLEMEDİ"
    for alan in ("toplam_skill", "olculen", "olculmemis", "korumali", "arsiv", "oran", "payda"):
        assert bos[alan] is None, f"{alan} ölçülemediğinde 0 değil None olmalı"


# =================================================================================================
# GÖRÜŞ DEFTERİ — EVREN
# =================================================================================================
def test_evren_AKTIF_KORUMASIZ_DETERMINISTIK_ucunu_birden_uygular(kayit):
    ev = sg.evren()
    assert ev["evren"] == ["pullback-screener", "vcp-screener"]
    assert ev["disarida"]["position-sizer"] == "korumali"
    assert ev["disarida"]["sector-analyst"] == "arsiv"
    # LLM-BAĞLAMLI SKILL DIŞLANIR: motor onu koşturmuyor, dolayısıyla ürettiği bir görüş de yok.
    assert ev["disarida"]["theme-detector"] == "llm_baglamli_motor_kosturmuyor"
    assert ev["sayim"]["evren"] == 2 and ev["sayim"]["arsiv"] == 2


# =================================================================================================
# GÖRÜŞ SATIRI ŞEMASI
# =================================================================================================
def test_gorus_satiri_semasi_ve_RET_kosullari():
    s = sg.gorus_satiri("vcp-screener", "aday-siralayici", "CF-1", tarih="2026-08-01",
                        skor=71.0, gerekce_ozeti="aday skoru")
    assert set(s) == set(sg._ALANLAR)
    assert s["skill"] == "vcp-screener" and s["yuzey"] == "aday-siralayici"
    assert s["hedef"] == "CF-1" and s["skor"] == 71.0 and s["tarih"] == "2026-08-01"
    assert s["ts"] and s["karar"] is None
    with pytest.raises(ValueError):                       # şemada olmayan yüzey
        sg.gorus_satiri("vcp-screener", "yok-boyle-yuzey", "CF-1", tarih="d", skor=1)
    with pytest.raises(ValueError):                       # şemada VAR ama ÇÖZÜCÜSÜ yok (YASA 6)
        sg.gorus_satiri("vcp-screener", "rejim", "CF-1", tarih="d", skor=1)
    with pytest.raises(ValueError):                       # görüşsüz görüş satırı
        sg.gorus_satiri("vcp-screener", "cikis", "CF-1", tarih="d")
    with pytest.raises(ValueError):                       # tarihsiz → küme kurulamaz
        sg.gorus_satiri("vcp-screener", "cikis", "CF-1", tarih="", karar="stop")


def test_gorus_satirinda_SONUC_alani_YOK_ileri_bakis_kapali():
    """Satır yalnız t ve öncesini taşır: sonuç alanı olsaydı görüşün içine cevabı yazmış olurduk."""
    yasak = {"r", "r_multiple", "sonuc", "mfe_r", "pnl", "kazanc"}
    assert not (set(sg._ALANLAR) & yasak)


# =================================================================================================
# ÇÖZÜCÜLER — SENTETİK VERİYLE (ikisi de)
# =================================================================================================
def _sentetik(skill, yuzey, n, *, skor_fn=None, r_fn=None, mfe_fn=None, gun_basi=4):
    """n gözlem, `gun_basi` gözlem/gün → tarih kümesi gerçekten ÇOKLU olur (MIN_KUME şartı)."""
    gorusler, sonuclar = [], {}
    for i in range(n):
        hedef = f"{skill}-{yuzey}-{i}"
        gun = f"2026-06-{(i // gun_basi) % 28 + 1:02d}"
        skor = skor_fn(i) if skor_fn else None
        gorusler.append(sg.gorus_satiri(skill, yuzey, hedef, tarih=gun, skor=skor,
                                        karar=(None if skor is not None else "stop"),
                                        gerekce_ozeti="sentetik"))
        sonuclar[hedef] = {"r": r_fn(i), "mfe_r": (mfe_fn(i) if mfe_fn else None)}
    return gorusler, sonuclar


def test_cozucu_siralayici_MONOTON_iliskiyi_yakalar_ve_GURULTUYU_yakalamaz():
    import numpy as np
    karisik = list(np.random.default_rng(7).permutation(200))          # deterministik karıştırma
    g1, s1 = _sentetik("iyi", "aday-siralayici", 200, skor_fn=lambda i: float(i),
                       r_fn=lambda i: float(i) * 0.01)                 # kusursuz monoton
    g2, s2 = _sentetik("kotu", "aday-siralayici", 200, skor_fn=lambda i: float(i),
                       r_fn=lambda i: float(karisik[i]) * 0.01)        # ilişkisiz
    c = sg.cozucu_siralayici(g1 + g2, {**s1, **s2})
    iyi, kotu = c["skiller"]["iyi"], c["skiller"]["kotu"]
    assert iyi["kova"] == "OLCULDU" and iyi["olcum"]["rank_ic"] == pytest.approx(1.0)
    assert iyi["etki_esigi_gecti"] is True and iyi["yon"] == 1 and iyi["p"] < 0.05
    assert iyi["olcum"]["lo"] is not None and iyi["olcum"]["n_kume"] >= 2
    # GÜRÜLTÜ ETKİ EŞİĞİYLE ELENMEZ — VE BU BİR KUSUR DEĞİL, KARTIN TASARIMIDIR. n=200'de
    # rank-IC'nin örnekleme saçılımı ≈ 1/√n ≈ 0,07'dir; yani saf gürültü |IC| >= 0,05 eşiğini
    # rutin olarak AŞAR. Kart bu yüzden İKİ kapı ister: etki eşiği BÜYÜKLÜK sorusunu, FDR ise
    # TESADÜF sorusunu yanıtlar. Tek kapıya güvenen bir katman, her turda birkaç yanlış terfi
    # adayı üretirdi. Testin çivilediği şey budur: gürültü İKİNCİ kapıda ölür.
    assert kotu["p"] > sg.KART_FDR_Q, "ilişkisiz seri FDR kapısını geçmemeli"
    f = sg.bh_fdr({k: v.get("p") for k, v in c["skiller"].items()})
    assert f["aile"]["iyi"]["sagkalan"] is True and f["aile"]["kotu"]["sagkalan"] is False


def test_cozucu_siralayici_TERS_iliskide_YON_negatif():
    g, s = _sentetik("ters", "aday-siralayici", 60, skor_fn=lambda i: float(i),
                     r_fn=lambda i: -float(i) * 0.01)
    v = sg.cozucu_siralayici(g, s)["skiller"]["ters"]
    assert v["olcum"]["rank_ic"] == pytest.approx(-1.0)
    assert v["etki_esigi_gecti"] is True and v["yon"] == -1


def test_cozucu_cikis_havuza_gore_katkiyi_olcer_ve_YONU_ayirir():
    # "iyi" masada AZ bırakır (left_r=0,2), "kotu" ÇOK bırakır (left_r=2,0) → havuz ort ≈ 1,1
    g1, s1 = _sentetik("iyi", "cikis", 60, r_fn=lambda i: 1.0, mfe_fn=lambda i: 1.2)
    g2, s2 = _sentetik("kotu", "cikis", 60, r_fn=lambda i: 1.0, mfe_fn=lambda i: 3.0)
    c = sg.cozucu_cikis(g1 + g2, {**s1, **s2})
    assert c["havuz_ort_left_r"] == pytest.approx(1.1, abs=1e-6)
    iyi, kotu = c["skiller"]["iyi"], c["skiller"]["kotu"]
    assert iyi["olcum"]["left_r"] == pytest.approx(0.2) and iyi["olcum"]["katki"] == pytest.approx(0.9)
    assert iyi["etki_esigi_gecti"] is True and iyi["yon"] == 1
    assert kotu["olcum"]["katki"] == pytest.approx(-0.9)
    assert kotu["etki_esigi_gecti"] is False and kotu["yon"] == -1     # emeklilik yönü


def test_n_altinda_OLCULDU_denmez_ORNEKLEM_YETERSIZ_kovasina_duser():
    n = sg.KART_N_MIN - 1
    g, s = _sentetik("az", "aday-siralayici", n, skor_fn=lambda i: float(i),
                     r_fn=lambda i: float(i))
    v = sg.cozucu_siralayici(g, s)["skiller"]["az"]
    assert v["kova"] == f"ÖRNEKLEM YETERSİZ {n}/{sg.KART_N_MIN}"
    assert v["olcum"] is None and v["p"] is None       # kusursuz monoton olsa BİLE hüküm yok
    g2, s2 = _sentetik("az2", "cikis", n, r_fn=lambda i: 1.0, mfe_fn=lambda i: 1.1)
    assert sg.cozucu_cikis(g2, s2)["skiller"]["az2"]["olcum"] is None


# =================================================================================================
# FDR AİLESİ (BH, q = kart)
# =================================================================================================
def test_bh_fdr_ailesi_kart_q_ile_ve_OLCULEMEYEN_paydayi_SISIRMEZ():
    f = sg.bh_fdr({"a": 0.001, "b": 0.04, "c": 0.9, "d": None})
    assert f["m"] == 3 and f["q"] == sg.KART_FDR_Q       # d aileye GİRMEZ
    assert f["aile"]["a"]["sagkalan"] is True            # 0,001 <= 0,10·1/3
    assert f["aile"]["c"]["sagkalan"] is False
    assert f["aile"]["d"]["sagkalan"] is None and f["aile"]["d"]["neden"]


def test_bh_ARA_p_de_gecer_step_up_kurali():
    """BH step-up: en büyük geçen p'nin ALTINDAKİ hepsi geçer — Bonferroni değil."""
    f = sg.bh_fdr({"a": 0.03, "b": 0.04})                # 0,04 <= 0,10·2/2 → ikisi de geçer
    assert f["aile"]["a"]["sagkalan"] and f["aile"]["b"]["sagkalan"]
    assert f["kritik_p"] == 0.04


def test_bootstrap_p_kart_bootstrapini_YENIDEN_KULLANIR(monkeypatch):
    """p, ikinci bir yeniden-örnekleme uygulamasından değil, KARTIN bootstrap'ından gelir."""
    from meridian import faz5_cikis
    cagri = {"n": 0}
    asil = faz5_cikis.tarih_kumeli_bootstrap
    monkeypatch.setattr(faz5_cikis, "tarih_kumeli_bootstrap",
                        lambda *a, **k: (cagri.__setitem__("n", cagri["n"] + 1), asil(*a, **k))[1])
    d = [0.5] * 20 + [0.6] * 20
    t = [f"2026-06-{i % 20 + 1:02d}" for i in range(40)]
    p = sg.bootstrap_p(d, t)
    assert cagri["n"] >= 2                              # ilkel gerçekten çağrıldı
    assert p["p"] is not None and p["p"] <= 0.01        # sıfırdan açıkça uzak ortalama
    assert p["cozunurluk"] is not None                  # çözünürlük BEYANLI
    bos = sg.bootstrap_p([], [])
    assert bos["p"] is None and bos["neden"]            # ölçülemedi → None + neden


# =================================================================================================
# KADANS — L0-NÖTR, p95 ÖLÇÜLÜ
# =================================================================================================
def _mini_defterler(ters: bool = False):
    """Küçük ama GERÇEK şemalı cf defteri (çözücülerin canlı yolu koşsun).

    `ters=True`: skor ile sonuç TERS orantılı — skill'in sıralama görüşü yanlış yönde, yani
    kartın iki yönlü kesiminin NEGATİF kolu."""
    rows = []
    for i in range(40):
        r = (-float(i) if ters else float(i)) * 0.01
        rows.append({"id": f"CF-x-{i}", "date": f"2026-06-{i % 10 + 1:02d}", "ticker": "AAA",
                     "setup": "breakout_vcp", "score": float(i), "screener": "vcp-screener",
                     "entered": True, "status": "closed", "exit_reason": "target",
                     "r_multiple": r, "mfe_r": r + 0.2})
    store.write_jsonl("counterfactuals.jsonl", rows)
    store.write_json("exit_efficiency.json", {"n": len(rows), "avg_left_r": 0.2})


def test_kadans_L0_NOTR_yalnizca_kendi_iki_defterine_yazar(kayit):
    _mini_defterler()
    kok = pathlib.Path(kayit)
    _dosyalar = lambda: {p.name for p in kok.rglob("*")
                         if p.is_file() and p.suffix != ".lock"}   # kilit dosyası store'un işi
    once = _dosyalar()
    reg_once = json.dumps(store.read_json("skills_registry.json", {}), sort_keys=True)
    sg.kadans(apply=True, oncesi_ms=1000.0)
    sonra = _dosyalar()
    assert sonra - once == {sg.GORUS_DEFTERI, sg.DURUM_DEFTERI}, \
        "görüş kadansı kendi iki defteri DIŞINDA bir dosyaya dokundu — gözlem katmanı icraya karışamaz"
    # KAYIT DEFTERİ BİT BİT AYNI: gölge/etkin/emeklilik bayrakları bu katmandan yazılmaz.
    assert json.dumps(store.read_json("skills_registry.json", {}), sort_keys=True) == reg_once
    assert store.read_jsonl("skill_recommendations.jsonl") == []


def test_kadans_p95_OLCULUR_ve_tek_ornekten_KILL_vermez(kayit):
    _mini_defterler()
    k = sg.kadans(apply=True, oncesi_ms=1000.0)
    assert isinstance(k["sure_ms"], float) and k["sure_ms"] >= 0
    assert k["pay"] == pytest.approx(k["sure_ms"] / 1000.0, abs=1e-4)   # pay 4 haneye yuvarlı
    assert k["kill_p95"]["durum"] == "ÖLÇÜLÜYOR" and k["kill_p95"]["n_ornek"] == 1
    assert k["kill_p95"]["tavan"] == sg.KART_P95_TAVAN
    for _ in range(sg.P95_MIN_ORNEK):
        k = sg.kadans(apply=True, oncesi_ms=1000.0)
    assert k["kill_p95"]["durum"] in ("temiz", "KILL")            # örneklem doldu, hüküm verilir
    assert k["kill_p95"]["n_ornek"] >= sg.P95_MIN_ORNEK


def test_kadans_sure_OLCULEMEDIGINDE_pay_SIFIR_SAYILMAZ(kayit):
    _mini_defterler()
    k = sg.kadans(apply=True, oncesi_ms=None)
    assert k["pay"] is None and k["kill_p95"]["durum"] == "ÖLÇÜLEMEDİ"
    assert "0 SAYILMAZ" in k["kill_p95"]["neden"]


def test_topla_TEKRARDA_yeniden_yazmaz_ve_TAVANA_uyar(kayit):
    _mini_defterler()
    ilk = sg.topla(apply=True, tavan=10)
    assert ilk["yazilan"] == 10 and ilk["kirpilan"] > 0
    ikinci = sg.topla(apply=True, tavan=None)
    assert ikinci["atlanan"]["zaten_var"] == 10          # yazılmış görüş İKİNCİ kez yazılmaz
    ucuncu = sg.topla(apply=True, tavan=None)
    assert ucuncu["yazilan"] == 0


def test_evren_disi_skill_deftere_YAZILMAZ(kayit):
    _mini_defterler()
    rows = store.read_jsonl("counterfactuals.jsonl")
    rows.append({**rows[0], "id": "CF-llm-1", "screener": "theme-detector"})
    rows.append({**rows[0], "id": "CF-ars-1", "screener": "sector-analyst"})
    store.write_jsonl("counterfactuals.jsonl", rows)
    t = sg.topla(apply=True, tavan=None)
    yazilanlar = {g["skill"] for g in sg.defter()}
    assert yazilanlar == {"vcp-screener"} and t["atlanan"]["evren_disi"] == 2


# =================================================================================================
# KILL#4 — ÇÖP GİRDİ, ÇÖP HÜKÜM ZİNCİRİ KAPALI
# =================================================================================================
def test_cikis_girdisi_yoksa_HUKUM_VERILMEZ(kayit):
    _mini_defterler()
    store.write_json("exit_efficiency.json", {"n": 0})      # bekçisinde ÜRETMEMİŞ işaretli
    sg.topla(apply=True, tavan=None)
    r = sg.rapor()
    assert r["yuzeyler"]["cikis"]["durum"] == "HÜKÜM YOK" and r["yuzeyler"]["cikis"]["neden"]
    assert r["yuzeyler"]["aday-siralayici"]["durum"] == "ölçüldü"   # öteki yüzey YAŞAR


# =================================================================================================
# HİÇBİR TERFİ OTOMATİK DEĞİL — ÇİVİ
# =================================================================================================
def test_FDR_sagkalan_bile_olsa_HICBIR_TERFI_UYGULANMAZ(kayit):
    """Kusursuz monoton sentetikte skill FDR'yi de etki eşiğini de geçer — ve HİÇBİR ŞEY olmaz."""
    _mini_defterler()
    sg.topla(apply=True, tavan=None)
    reg_once = json.dumps(store.read_json("skills_registry.json", {}), sort_keys=True)
    r = sg.rapor()
    v = r["yuzeyler"]["aday-siralayici"]["skiller"]["vcp-screener"]
    assert v["fdr"]["sagkalan"] is True and v["terfi_adayi"] is True
    assert r["terfi_adaylari"] and r["terfi_adaylari"][0]["skill"] == "vcp-screener"
    # ...ve kayıt defteri kılını kıpırdatmadı; öneri defteri de boş.
    assert json.dumps(store.read_json("skills_registry.json", {}), sort_keys=True) == reg_once
    assert store.read_jsonl("skill_recommendations.jsonl") == []
    assert store.read_json("skill_auto_shadow.json", None) is None
    assert "OTOMATİK DEĞİL" in r["beyan"]


def test_gorus_modulu_KARAR_YAZAN_hicbir_cagriyi_ICERMEZ(kod_govdesi):
    """Kaynak çivisi: yarın biri 'küçük bir kolaylık' diye terfi yazarsa test düşsün."""
    kod = kod_govdesi(sg.__file__)
    for yasak in ("apply_skill_action", "record_recommendation", "reconcile_enablement",
                  "auto_shadow_from_evidence", "skills_registry"):
        assert yasak not in kod, f"görüş katmanı karar yazan bir yola bağlanmış: {yasak}"
    # Yazdığı dosyalar SAYILIDIR ve ÜÇÜ DE kendi defteri.
    # KUYRUK_DEFTERI 2026-09-01'de EKLENDİ (EDG-2026-019 kill#1 kök çözümü): görüş üretimi öğrenme
    # kadansından çıkarıldı ve kadansta kalan iş, t-anı kesitini `skill_gorus_kuyruk.jsonl`e
    # eklemek oldu. Çivinin SÖZÜ değişmedi — "bu katman yalnız KENDİ defterlerine yazar, hiçbir
    # karar yüzeyine dokunmaz"; genişleyen şey katmanın kendi defter sayısıdır. Liste kapalıdır:
    # dördüncü bir ad eklenirse bu çivi yine öter.
    #
    # YAZIM FİİLLERİ `codelaw.WRITE_CALLS`TAN TÜRETİLİR (tek-kaynak, 2026-09-01). Elle yazılmış
    # liste `update_json`/`update_jsonl`/`merge_dated_jsonl`i KAÇIRIYORDU: `store.update_jsonl`
    # ile yazan bir yol bu çiviye GÖRÜNMEZDİ, yani "yazım hedefleri sayılıdır" iddiası eksik
    # ölçülüyordu. Denetçinin kendi tanımını kullanmak, iki listenin sessizce ayrışmasını da bitirir.
    yazimlar = set(re.findall(WRITE_CALL_RE, kod))
    assert yazimlar <= {"GORUS_DEFTERI", "DURUM_DEFTERI", "KUYRUK_DEFTERI"}, \
        f"beklenmeyen yazım hedefi: {yazimlar}"


def test_katman_IKI_YONLU_keser_negatif_kanit_EMEKLILIK_isaretine_duser(kayit):
    """Kartın "değeri terfi kadar EMEKLİLİK" cümlesinin kodda karşılığı. Tek yön kodlanmış olsaydı
    negatif kanıt sessizce düşer, katman yalnız iyi haberi görürdü.

    Ve İŞARET ÖNERİ DEĞİLDİR: kart 3 ARDIŞIK pencere ister, pencere sayacı bu turda YOK — satır
    bunu kendi üstünde beyan etmeli, yoksa bir işaret bir karar gibi okunur."""
    _mini_defterler(ters=True)              # skor YÜKSEK olan DÜŞÜK R getiriyor
    sg.topla(apply=True, tavan=None)
    reg_once = json.dumps(store.read_json("skills_registry.json", {}), sort_keys=True)
    r = sg.rapor()
    v = r["yuzeyler"]["aday-siralayici"]["skiller"]["vcp-screener"]
    assert v["fdr"]["sagkalan"] is True and v["yon"] == -1
    assert v["terfi_adayi"] is False and v["emeklilik_isareti"] is True
    assert not r["terfi_adaylari"]
    isaret = r["emeklilik_isaretleri"][0]
    assert isaret["skill"] == "vcp-screener" and isaret["etki"] < 0
    assert "3 ARDIŞIK" in isaret["beyan"] and "ÖNERİSİ değildir" in isaret["beyan"]
    # ...ve negatif kanıt da HİÇBİR ŞEY UYGULAMAZ: emeklilik de bir karardır, operatörün.
    assert json.dumps(store.read_json("skills_registry.json", {}), sort_keys=True) == reg_once
    assert store.read_jsonl("skill_recommendations.jsonl") == []


# =================================================================================================
# TÜKETİCİ — DEFTERİN OKUYUCUSU İLK GÜNDEN BAĞLI (uyuyan-yol dersi)
# =================================================================================================
def test_api_gorus_okuma_alani_defteri_OKUR(kayit):
    _mini_defterler()
    sg.kadans(apply=True, oncesi_ms=1000.0)
    y = api._eksen2_gorus()
    assert y["durum"] == "dolu" and y["kart"] == sg.KART
    assert y["defter_n"] == len(sg.defter()) > 0
    assert y["kill_p95"] is not None and y["esikler"]["fdr_q"] == sg.KART_FDR_Q
    assert "aday-siralayici" in y["yuzeyler"]
    assert y["son_kadans"]["sure_ms"] is not None
    # HAM SATIR TAŞIMAZ: defter süresiz büyür, uç yükü onunla birlikte büyüyemez.
    assert "gorusler" not in y and "satirlar" not in y


def test_api_gorus_alani_OKUNAMAYINCA_bos_rapor_DEMEZ(kayit, monkeypatch):
    _mini_defterler()
    sg.topla(apply=True, tavan=None)
    monkeypatch.setattr(sg, "rapor", lambda: (_ for _ in ()).throw(RuntimeError("defter bozuk")))
    y = api._eksen2_gorus()
    assert y["durum"] == "ÖLÇÜLEMEDİ" and "defter bozuk" in y["neden"]
    assert y["defter_n"] is None and y["kova_sayimi"] is None
    # ...ama HACİM SAYACI ayrı bir okumadır ve ayakta kalır: "hüküm kurulamadı" ile
    # "hiç görüş yok" ekranda ayrılabilsin.
    assert y["hacim"]["n"] == len(sg.defter()) > 0


def test_hacim_sayaci_HUKUMDEN_bagimsiz_defteri_olcer(kayit):
    _mini_defterler()
    sg.topla(apply=True, tavan=None)
    h = api._gorus_defter_hacmi()
    assert h["n"] == len(sg.defter())
    assert set(h["yuzey_skill"]) == set(sg.OLCULEN_YUZEYLER)
    assert h["yuzey_skill"]["aday-siralayici"] == {"vcp-screener": 40}
    assert h["ilk_tarih"] <= h["son_tarih"]


def test_YASA_6_her_iki_defterin_DIS_okuyucusu_VAR():
    """Okuyucusuz yazım yok. Ölçüm `codelaw.artifact_graph`in kendisiyle yapılır — 'bağladım'
    demek yetmez; grafın DIŞ okuyucu görmesi gerekir (aynı modülün kendi okuması sayılmaz)."""
    from meridian import codelaw
    g = codelaw.artifact_graph()
    for ad in (sg.GORUS_DEFTERI, sg.DURUM_DEFTERI):
        kayit_ = g["artifacts"].get(ad)
        assert kayit_, f"{ad} artefakt grafında ÇÖZÜLEMEDİ"
        assert kayit_["writers"] == ["skill_gorus.py"]
        assert "api.py" in kayit_["external_readers"], f"{ad} dış okuyucusuz — YASA 6"
        assert kayit_["unread"] is False
    assert g["violations"] == [] and g["stale_sinks"] == []


_KARTLAR = pathlib.Path(__file__).resolve().parent.parent / "research" / "cards"


def _kart_kimlikleri() -> dict:
    """kart dosyası → `card_id` (ilk satır). Ayrıştırıcı değil TARAYICI: kimlik satırı kartın
    ilk satırıdır ve yaml yüklemek bu sınama için gereksiz bir kırılganlık olurdu."""
    out = {}
    for f in sorted(_KARTLAR.glob("*.yaml")):
        m = re.search(r"^card_id:\s*(\S+)", f.read_text(), flags=re.M)
        if m:
            out[f.name] = m.group(1)
    return out


def test_KART_sabiti_TEK_karta_cozulur_kimlik_cakismasi_YOK():
    """KİMLİK PROVENANSI ÇİVİSİ (2026-08-09, W3 turunda İKİ KEZ ateşlendi).

    `KART` sabiti bir ÖN-KAYIT KARTINA işaret eder ve K defteri kart kimliğinden okunur. Kimlik
    iki karta birden çözülüyorsa iki AYRI deneme tek K'ya katlanır — yani çokluk düzeltmesi
    sessizce eksik sayar ve bu, eşiği HAK ETMEDEN geçme yönünde yanlıdır (kartın kendi
    `parameter_grid` kuralı: "K += 1", "K grid'de ÇARPILARAK sayılır").

    NEDEN BU TEST VAR — KUSUR ÜST ÜSTE İKİ KEZ TEKRARLANDI (2026-08-09, hepsi aynı gün):
      1. kart EDG-2026-012 olarak doğdu; o kimlik `EDG-2026-012-net-issuance.yaml`da ZATEN vardı,
      2. elle düzeltme EDG-2026-013'e taşıdı; o da `EDG-2026-013-mom-turnover.yaml`da ZATEN vardı
         — üstelik o kart ARŞİVLENMİŞ olmasına rağmen K HARCAMIŞTI (iki `trial_id`), yani çakışma
         boş bir numarayla değil, ödenmiş bir K'yla oluyordu,
      3. üçüncü seferde kayıt defteri grep'lendi → EDG-2026-019 (o an gerçekten boş).
    İki elle kontrol, iki kaçırma. Bu testin varlık sebebi tam olarak budur: kimlik tekilliği bir
    DİKKAT meselesi değil bir ÖLÇÜM meselesidir ve ölçüm her koşuda tekrarlanır.

    KAPSAM BEYANI: bu bekçi YALNIZ `skill_gorus.KART`ın çözünürlüğünü sınar, kart dizininin
    tamamının tekilliğini DEĞİL — kart kaydı Rol-1'in defteridir, bu testin sahibi değil."""
    kimlikler = _kart_kimlikleri()
    assert kimlikler, f"kart dizini okunamadı: {_KARTLAR}"
    sahipler = sorted(f for f, k in kimlikler.items() if k == sg.KART)
    assert len(sahipler) == 1, (
        f"`skill_gorus.KART` ({sg.KART}) {len(sahipler)} karta birden çözülüyor: {sahipler}. "
        f"K defteri kart kimliğinden okunur — çakışan kimlik iki denemeyi tek K'ya katlar. "
        f"Boştaki kimlikler: {_bos_kimlikler(kimlikler)}")
    assert "gorus" in sahipler[0], f"KART başka bir kartın dosyasına çözülüyor: {sahipler[0]}"


def _bos_kimlikler(kimlikler: dict, n: int = 4) -> list:
    """Sıradaki KULLANILMAYAN EDG numaraları — hata mesajı bir sonraki adımı da söylesin."""
    kullanilan = {int(m.group(1)) for k in kimlikler.values()
                  if (m := re.match(r"EDG-2026-(\d+)$", k))}
    return [f"EDG-2026-{i:03d}" for i in range(1, max(kullanilan or [0]) + n + 1)
            if i not in kullanilan][:n]


def test_kadans_ADIMI_ogrenme_kadansinda_BEYANLI():
    """Yazan scheduler, okuyan analytics/api (YASA 6) — adım kadansın kendi listesinde durmalı."""
    from meridian import scheduler
    assert "gorus" in scheduler.LEARN_STEPS
    src = pathlib.Path(scheduler.__file__).read_text()
    govde = src[src.index("def _learning_cadence"):src.index("def _y4_collect")]
    assert "skill_gorus" in govde and "oncesi_ms" in govde
    # SIRA GEREKÇESİ: görüş, tek kota tüketicisi olan dolgunun ÖNÜNDE koşar.
    assert govde.index("skill_gorus") < govde.index("_dolgu_kadansi(session)")
