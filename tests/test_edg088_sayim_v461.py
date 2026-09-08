"""test_edg088_sayim_v461.py — EDG-2026-088 gölge pilot B1 / Task 3: SAYAÇ ÇİVİSİ.

NE ÇİVİLENİR (plan `docs/superpowers/plans/2026-09-08-golge-pilot-b1.md` Task 3):
`research/olcumler/edg088_golge_pilot/sayim.py` — kartın K=2 birincil ölçüsünü ve üç pozitif
kontrolünü `state/golge_icra.jsonl` şemasından sayar, HÜKÜM VERMEZ.

TEST NUMARASI — v458 DEĞİL v461. Task 1 ve Task 2 raporları Task 3'e **v458** devretmişti; o
numara bu tur açılmadan ÖNCE ana checkout'ta doldu (`test_roadmap_arsiv_sayimi_v458.py`), v459 ve
v460 da paralel worktree'lerde alındı (`test_arama_api_v459.py`, `test_arama_ui_v460.py`).
Ölçüm ana checkout + TÜM worktree'ler üzerinde yapıldı; ilk boş numara **v461**di. Numara
KİMLİKTİR ve tek worktree'de ölçülürse KÖRDÜR — Task 1 raporunun §2 dersi bu turda TEKRARLANDI.

PK (1) SENARYOSU İTHAL EDİLİR, KOPYALANMAZ (tek-kaynak yasası). Beş yolun barları, planları ve
koşum düzeni motorun kendi çivisinde (`tests/test_golge_icra_v456.py`) yaşıyor; ikinci bir kopya
yazmak "aynı gerçeğin iki kopyası sessizce ayrışır" sınıfının ta kendisi olurdu. Buradaki çivi o
senaryoyu ÇAĞIRIR ve sayacın onun ÜRETTİĞİ defterden aynı sayıyı çıkarmasını ister — yani ölçüm
zinciri motor → defter → sayaç boyunca UÇTAN UCA sınanır, sayacın kendi sentetik defteri üzerinde
değil.

AYRIŞMA ÇİVİSİ (K paydası). Payda kuralı (`R` ölçülmüş ∧ `kaynak_bar_hash` dolu) HEM motorun
`golge_icra.ozet` fonksiyonunda HEM sayaçta yazılı — motora yeni bir yüzey eklemek bu turun dosya
kapsamı dışındaydı. Kaçınılmaz kopyanın bedeli ayrışmadır ve
`test_AYRISMA_motorun_ozeti_ile_sayac_AYNI_defterde_AYNI_sayiyi_verir` onu kapatır (CLAUDE.md §4:
"kopya kaçınılmazsa türetme + ayrışma çivisi").

EŞİK SAYILARI BU DOSYADA DA YAZILMAZ. 30 / 0,0 / 0,40 / 120 / 0,05 hiçbir iddiada literal olarak
geçmez; hepsi `golge_icra` sabitlerinden ve kart YAML'ından OKUNUR. Literal yazsaydım kartın
donuk eşiği ÜÇÜNCÜ bir kopya kazanırdı.

KAPILAR: `sandbox_state` motoru koşturan çivilerde AÇIKÇA istenir (autouse DEĞİL, ölçüldü);
sayacın kendisi `config.STATE`e hiç dokunmaz ve yalnız `tmp_path` altında, `subprocess` ile,
operatörün koşacağı BİÇİMDE koşulur.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import subprocess
import sys

import pytest
import yaml

from meridian import golge_icra as gi
from tests.conftest import betikten_modul_yukle
# PK (1) SENARYOSUNUN TEK KAYNAĞI motorun çivisidir (docstring'deki gerekçe).
from tests.test_golge_icra_v456 import _pk1_kosusu

KOK = pathlib.Path(__file__).resolve().parents[1]
BETIK_YOLU = KOK / "research" / "olcumler" / "edg088_golge_pilot" / "sayim.py"
KART_YOLU = KOK / "research" / "cards" / "EDG-2026-088-uyuyan-kurulum-golge-pilot.yaml"
GOAL_YOLU = KOK / "state" / "goal.yaml"
PK3_ARTEFAKT = (KOK / "research" / "olcumler" / "edg049_dormant_2026-08-23"
                / "islemler_tam_dormant_acik.json")

#: PK (1)'in EL HESABI — motorun çivisiyle AYNI aritmetik, sayı olarak DEĞİL İFADE olarak yazılı:
#: AAA −1 · BBB +1,5 · CCC −0,5/6 · DDD +1/6 · EEE R=None. Toplam = 0,5 + 0,5/6.
PK1_TOPLAM_R = 0.5 + 0.5 / 6.0
PK1_N = 4


def _sayim():
    return betikten_modul_yukle(BETIK_YOLU, "edg088_sayim")


def _kart() -> dict:
    return yaml.safe_load(KART_YOLU.read_text(encoding="utf-8")) or {}


def _defter_yaz(yol: pathlib.Path, satirlar: list[dict]) -> pathlib.Path:
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in satirlar),
                   encoding="utf-8")
    return yol


def _satir(plan_id, *, r, kol="dormant", kurulum="pullback", hukum="REVIEW",
           hash_="a" * 64, gun_once=1, cikis="2026-09-10", giris=101.0, stop=95.0,
           cikis_neden="stop", ticker=None):
    """Şemanın TAMAMINI taşıyan sentetik defter satırı — alan adları motordan OKUNUR.

    `gi.SATIR_ALANLARI` üzerinden kurulur: motora yeni bir alan eklenirse bu kurucu onu `None`
    ile taşır ve sayaç eksik anahtarla karşılaşmaz (şema kayması sessizce testin içinde ölmez).
    """
    ts = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=gun_once)).isoformat()
    dolu = {"ts": ts, "plan_id": plan_id, "ticker": (ticker or plan_id), "kurulum": kurulum,
            "hukum": hukum, "kol": kol, "ts_plan": "2026-09-09",
            "giris_ts": "2026-09-09", "giris_fiyat": giris, "stop": stop, "hedef": 110.0,
            "cikis_ts": cikis, "cikis_fiyat": 95.0,
            "cikis_neden": (gi.GIRIS_YOK if r is None else cikis_neden), "R": r, "bar_n": 3,
            "kaynak_bar_hash": hash_, "bar_kaynak": gi.BAR_KAYNAKLARI[0],
            "strategy_version": 3, "giris_reddi": (None if r is not None else "tetik_gelmedi"),
            "olculemedi": None}
    return {ad: dolu.get(ad) for ad in gi.SATIR_ALANLARI}


def _dolu_pencere(n: int | None = None) -> list[dict]:
    """Pencereyi DOLDURAN defter: n = kartın alt sınırı, hepsi taze (geçen gün ≪ üst sınır).

    Alternatif R'ler kazanma oranını 0,5'e sabitler; sayı ELLE değil kuralla doğar.
    """
    n = n or gi.N_ALT
    return [_satir(f"P-{i:03d}", r=(1.0 if i % 2 == 0 else -0.5), gun_once=1)
            for i in range(n)]


def _kosum(tmp_path, satirlar, **kw):
    s = _sayim()
    defter = _defter_yaz(tmp_path / "state" / "golge_icra.jsonl", satirlar)
    kw.setdefault("kart", KART_YOLU)
    kw.setdefault("goal", GOAL_YOLU)
    return s, s.calistir(defter=defter, **kw), defter


# =================================================================================================
# ÇİVİ 1 — PK (1) KİMLİK KONTROLÜ: motorun ÜRETTİĞİ defterden el hesabı BİREBİR çıkar
# =================================================================================================
def test_civi1_PK1_motorun_defterinden_toplam_R_EL_HESABIYLA_birebir(sandbox_state, tmp_path):
    """Beş sentetik yol motorda koşar, defter sayaca verilir: toplam R = 0,5 + 0,5/6.

    `EEE` (tetik gelmedi, R=None) paydada DEĞİLDİR — n dörttür, beş değil.
    """
    _pk1_kosusu()
    from meridian import store
    satirlar = store.read_jsonl(gi.DEFTER)
    assert len(satirlar) == 5, "motor beş satır yazmadı — senaryo kaydı"

    s, sonuc, _ = _kosum(tmp_path, satirlar)
    assert sonuc["n"] == PK1_N, sonuc["n"]
    assert sonuc["toplam_r"] == pytest.approx(PK1_TOPLAM_R, abs=1e-6), sonuc["toplam_r"]
    assert sonuc["kazanma_orani"] == pytest.approx(0.5)
    # R'si ölçülmeyen satır TANIdır ve ADIYLA görünür (uydurma yasağı: 0 ile 'bilmiyorum' ayrı).
    assert any("P-e" in x and "tetik_gelmedi" in x for x in sonuc["olculemeyen"]), \
        sonuc["olculemeyen"]
    assert sonuc["cikis_neden_dagilimi"] == {"regime_flip": 1, "stop": 1, "target": 1,
                                             "time_stop": 1}, sonuc["cikis_neden_dagilimi"]


def test_civi1_MUTASYON_altinci_satir_toplami_DEGISTIRIR(sandbox_state, tmp_path):
    """Sayaç ölü değil: bir satır daha eklenince toplam R ve n DEĞİŞİR."""
    _pk1_kosusu()
    from meridian import store
    satirlar = store.read_jsonl(gi.DEFTER)
    _, once, _ = _kosum(tmp_path / "a", satirlar)
    _, sonra, _ = _kosum(tmp_path / "b", satirlar + [_satir("P-f", r=1.5)])
    assert sonra["n"] == once["n"] + 1
    assert sonra["toplam_r"] == pytest.approx(once["toplam_r"] + 1.5, abs=1e-6)


def test_AYRISMA_motorun_ozeti_ile_sayac_AYNI_defterde_AYNI_sayiyi_verir(sandbox_state, tmp_path):
    """K paydası kuralı İKİ YERDE yazılı (motor `ozet` + sayaç `sayilir`) — ayrışırlarsa öter."""
    _pk1_kosusu()
    from meridian import store
    satirlar = store.read_jsonl(gi.DEFTER)
    ozet = gi.ozet()
    _, sonuc, _ = _kosum(tmp_path, satirlar)
    assert sonuc["n"] == ozet["n"]
    assert sonuc["toplam_r"] == pytest.approx(ozet["toplam_r"], abs=1e-6)
    assert sonuc["kazanma_orani"] == pytest.approx(ozet["kazanma_orani"], abs=1e-4)
    assert (sonuc["pf"] is None) == (ozet["pf"] is None)
    for alan in ("hukum_dagilimi", "kurulum_kirilimi", "kol_kirilimi", "cikis_neden_dagilimi"):
        assert sonuc[alan] == ozet[alan], (alan, sonuc[alan], ozet[alan])


# =================================================================================================
# ÇİVİ 2 — PK (2) KONTROL KOLU + KILL#5 (düşerse HİÇBİR SAYI YAYILMAZ)
# =================================================================================================
def _kontrol_defteri(fark: float):
    """Bir kontrol çifti: gölge R = gerçek R + `fark`. Giriş/stop friksiyon payını belirler."""
    golge = [_satir("P-k1", r=1.0 + fark, kol="kontrol", giris=101.0, stop=95.0),
             _satir("P-d1", r=0.5, kol="dormant")]
    gercek = [{"id": "T1", "ts_open": "2026-09-09", "ts_close": "2026-09-10", "ticker": "P-k1",
               "r_multiple": 1.0, "pnl_dollars": 100.0, "plan_id": "P-k1", "regime": "trend_up",
               "score": 80, "setup": "pullback", "strategy_version": 3}]
    return golge, gercek


def _pk2_kosum(tmp_path, fark, ek_golge=()):
    golge, gercek = _kontrol_defteri(fark)
    golge = list(golge) + list(ek_golge)
    s = _sayim()
    defter = _defter_yaz(tmp_path / "state" / "golge_icra.jsonl", golge)
    _defter_yaz(tmp_path / "state" / "trades.jsonl", gercek)
    return s, s.calistir(defter=defter, kart=KART_YOLU, goal=GOAL_YOLU)


def test_civi2_PK2_fark_esigin_ALTINDA_ise_gecti_True_ve_sayilar_yayilir(tmp_path):
    """Fark eşiğin ALTINDA ve komisyon+kayma payının İÇİNDE → `gecti=True`, sayılar durur."""
    goal = yaml.safe_load(GOAL_YOLU.read_text(encoding="utf-8"))
    # Payın kendisi ÖLÇÜLÜR, sabit yazılmaz: 2 bacak kayma + 2 bacak komisyon, R birimine bölünür.
    pay = (2 * (float(goal["slippage_bps"]) / 1e4) * 101.0
           + 2 * float(goal["commission_per_share"])) / (101.0 - 95.0)
    fark = min(gi.FARK_R_UST, pay) / 2.0
    _, sonuc = _pk2_kosum(tmp_path, fark)
    assert sonuc["kontrol"]["n_cift"] == 1, sonuc["kontrol"]
    assert sonuc["kontrol"]["gecti"] is True, sonuc["kontrol"]
    assert sonuc["kontrol"]["komisyon_kayma_payi"] == pytest.approx(pay, abs=1e-6)
    assert sonuc["yayin_engeli"] == [] and sonuc["bastirilan"] == []
    assert sonuc["n"] == 2 and sonuc["toplam_r"] is not None


def test_civi2_PK2_DUSERSE_hicbir_sayi_yayilmaz(tmp_path):
    """Kill#5: fark eşiğin ÜSTÜNE itilince `gecti=False` VE K blokunun tamamı BASTIRILIR."""
    _, sonuc = _pk2_kosum(tmp_path, gi.FARK_R_UST * 1.2)
    assert sonuc["kontrol"]["gecti"] is False, sonuc["kontrol"]
    for alan in ("n", "toplam_r", "kazanma_orani", "pf", "ci", "ci_toplam",
                 "kurulum_kirilimi", "hukum_dagilimi", "cikis_neden_dagilimi"):
        assert sonuc[alan] is None, f"{alan} bastırılmadı: {sonuc[alan]}"
    assert set(sonuc["bastirilan"]) >= {"n", "toplam_r", "kazanma_orani", "ci"}
    assert any("kill#5" in x for x in sonuc["yayin_engeli"]), sonuc["yayin_engeli"]


def test_civi2_PK2_dusunce_MARKDOWN_da_sayi_tasimaz(tmp_path):
    """Markdown "PK DÜŞTÜ — SAYI YAYILMAZ" başlığıyla çıkar ve K bölümlerini HİÇ üretmez."""
    s, sonuc = _pk2_kosum(tmp_path, gi.FARK_R_UST * 1.2)
    md = s.markdown_uret(sonuc)
    assert md.startswith("# EDG-2026-088") and "## PK DÜŞTÜ — SAYI YAYILMAZ" in md
    for baslik in ("## K ölçüleri", "## Tanı", "## Eşik karşılaştırması", "## Bedel"):
        assert baslik not in md, f"{baslik} bastırılmış raporda basıldı"
    assert "toplam R" not in md


def test_civi2_PK2_OLCULEMEDIYSE_None_dir_ve_sayilari_BASTIRMAZ(tmp_path):
    """`gecti is None` (defter yok / çift yok) BASTIRMAZ — ölçülmemiş ile düşmüş aynı şey değil."""
    _, sonuc, _ = _kosum(tmp_path, _dolu_pencere())
    assert sonuc["kontrol"]["gecti"] is None
    assert sonuc["kontrol"]["neden"], "PK (2) ölçülemedi ama nedeni yazılmadı"
    assert sonuc["yayin_engeli"] == [] and sonuc["n"] == gi.N_ALT
    assert any("PK (2)" in x for x in sonuc["olculemeyen"]), sonuc["olculemeyen"]


# =================================================================================================
# ÇİVİ 3 — PK (3) SELEF (EDG-2026-049): referans + eşleşme, ayrışırsa "HARNESS KÖR"
# =================================================================================================
def _pk3_plan_idler() -> list[str]:
    ham = json.loads(PK3_ARTEFAKT.read_text(encoding="utf-8"))
    return sorted(str(r["plan_id"]) for r in ham if r.get("setup") == "pullback")


def test_civi3_PK3_referans_ARTEFAKTTAN_okunur_6_plan_6_kayip(tmp_path):
    """049'un uyuyan dilimi: TAM 6 satır, 6/6 kayıp, toplam R < 0 — sayı artefaktan TÜRER."""
    _, sonuc, _ = _kosum(tmp_path, _dolu_pencere(), pk3=PK3_ARTEFAKT)
    p = sonuc["pk3"]
    ham = json.loads(PK3_ARTEFAKT.read_text(encoding="utf-8"))
    beklenen = [r for r in ham if r.get("setup") == "pullback"]
    assert p["n"] == len(beklenen) == 6
    assert p["kayip"] == 6
    assert p["toplam_r"] == pytest.approx(sum(r["r_multiple"] for r in beklenen), abs=1e-6)
    assert p["toplam_r"] < 0


def test_civi3_PK3_golge_tarafi_YOKSA_esles_None_ve_HARNESS_KOR(tmp_path):
    """Yeniden doğum koşulmadıysa PK (3) ÖLÇÜLEMEZ — `esles=False` DEĞİL `None`."""
    _, sonuc, _ = _kosum(tmp_path, _dolu_pencere(), pk3=PK3_ARTEFAKT)
    p = sonuc["pk3"]
    assert p["esles"] is None, p
    assert "HARNESS KÖR" in (p["neden"] or ""), p["neden"]
    assert sorted(p["golge"]["eksik_plan_idler"]) == _pk3_plan_idler()
    assert any("PK (3)" in x for x in sonuc["olculemeyen"])


def test_civi3_PK3_golge_ISARETI_TUTARSA_esles_True(tmp_path):
    """Altı planın gölge eşleniği 6/6 kayıpsa işaret TUTAR (eşitlik değil, İŞARET ölçütü)."""
    idler = _pk3_plan_idler()
    golge = [_satir(pid, r=-0.7 - i * 0.1) for i, pid in enumerate(idler)]
    _, sonuc, _ = _kosum(tmp_path, golge + _dolu_pencere(), pk3=PK3_ARTEFAKT)
    p = sonuc["pk3"]
    assert p["golge"]["n"] == 6 and p["golge"]["kayip"] == 6
    assert p["esles"] is True, p
    assert p["fark_r"] is not None


def test_civi3_PK3_ISARET_AYRISIRSA_esles_False(tmp_path):
    """Gölge tarafı kâr yazarsa 049 ile AYRIŞMA vardır — `esles=False` (kartın 'harness kör'ü)."""
    idler = _pk3_plan_idler()
    golge = [_satir(pid, r=+1.0) for pid in idler]
    _, sonuc, _ = _kosum(tmp_path, golge + _dolu_pencere(), pk3=PK3_ARTEFAKT)
    assert sonuc["pk3"]["esles"] is False, sonuc["pk3"]


def test_civi3_PK3_EKSIK_dilim_KISMI_sayilir_uydurulmaz(tmp_path):
    """6'nın 3'ü varsa eşleşme ölçülmez: `esles=None` + eksik kimlikler ADIYLA."""
    idler = _pk3_plan_idler()
    golge = [_satir(pid, r=-1.0) for pid in idler[:3]]
    _, sonuc, _ = _kosum(tmp_path, golge + _dolu_pencere(), pk3=PK3_ARTEFAKT)
    p = sonuc["pk3"]
    assert p["esles"] is None and p["golge"]["n"] == 3
    assert sorted(p["golge"]["eksik_plan_idler"]) == idler[3:]
    assert "KISMİ" in (p["neden"] or ""), p["neden"]


def test_civi3_PK3_artefakt_dilimi_6_DEGILSE_olculemez(tmp_path):
    """Artefakt değişip dilim 6 olmazsa BAŞKA bir şey ölçülmez — PK ölçülemedi damgası."""
    sahte = tmp_path / "sahte_049.json"
    sahte.write_text(json.dumps([{"setup": "pullback", "plan_id": "X", "r_multiple": -1.0}]),
                     encoding="utf-8")
    _, sonuc, _ = _kosum(tmp_path, _dolu_pencere(), pk3=sahte)
    assert sonuc["pk3"]["n"] == 1 and sonuc["pk3"]["esles"] is None
    assert "ÖLÇÜLEMEDİ" in (sonuc["pk3"]["neden"] or "")


# =================================================================================================
# ÇİVİ 4 — PENCERE KAPISI: n<alt sınır ile HİÇBİR EŞİK CÜMLESİ YAZILMAZ
# =================================================================================================
def test_civi4_pencere_dolmadan_markdown_HUKUM_YOK_basligi_tasir(tmp_path):
    s, sonuc, _ = _kosum(tmp_path, _dolu_pencere(gi.N_ALT - 1))
    assert sonuc["pencere"]["doldu"] is False, sonuc["pencere"]
    md = s.markdown_uret(sonuc)
    assert "## HÜKÜM YOK (betimleyici ara-rapor)" in md
    assert "## Eşik karşılaştırması" not in md, "n<alt sınır iken eşik bölümü basıldı"
    # Betimleyici sayılar YİNE basılır (körlük üretmemek için) — yasak olan EŞİK KARŞILAŞTIRMASI.
    assert "## K ölçüleri" in md and str(sonuc["n"]) in md


def test_civi4_pencere_DOLUNCA_esik_bolumu_dogar_ve_HUKUM_KELIMESI_yoktur(tmp_path):
    s, sonuc, _ = _kosum(tmp_path, _dolu_pencere())
    assert sonuc["pencere"]["doldu"] is True, sonuc["pencere"]
    md = s.markdown_uret(sonuc)
    assert "## Eşik karşılaştırması" in md and "## HÜKÜM YOK" not in md
    # SAYAÇ HÜKÜM VERMEZ: geçti/kaldı sözcükleri hiçbir çıktıda YOKTUR.
    for kelime in ("GEÇER", "KALIR", "geçti", "kaldı", "GEÇTİ", "KALDI"):
        assert kelime not in md, f"sayaç hüküm cümlesi yazdı: {kelime}"


def test_civi4_pencere_SURESI_dolunca_doldu_False_kalir(tmp_path):
    """n yeterli ama geçen gün üst sınırı AŞTIYSA pencere dolmuş SAYILMAZ (kart eşiği donuk)."""
    eski = [_satir(f"P-{i:03d}", r=1.0, gun_once=gi.PENCERE_GUN + 5) for i in range(gi.N_ALT)]
    _, sonuc, _ = _kosum(tmp_path, eski)
    assert sonuc["pencere"]["gecen_gun"] > gi.PENCERE_GUN
    assert sonuc["pencere"]["doldu"] is False and sonuc["pencere"]["suresi_doldu"] is True


# =================================================================================================
# ÇİVİ 5 — PIT ÇAPASI: hash'siz satır K paydasına GİRMEZ, `olculemeyen`e ADIYLA düşer
# =================================================================================================
def test_civi5_hashsiz_satir_paydaya_girmez_ve_ADIYLA_gorunur(tmp_path):
    saglam = _dolu_pencere()
    capasiz = _satir("P-capasiz", r=99.0, hash_=None)
    capasiz["olculemedi"] = "bar_eksik:2"
    _, sonuc, _ = _kosum(tmp_path, saglam + [capasiz])
    assert sonuc["n"] == gi.N_ALT, "PIT çapası yarım satır paydaya girdi"
    assert sonuc["toplam_r"] == pytest.approx(sum(r["R"] for r in saglam), abs=1e-6)
    assert any("P-capasiz" in x and "bar_eksik:2" in x for x in sonuc["olculemeyen"]), \
        sonuc["olculemeyen"]


def test_civi5_bos_hash_dizgesi_de_capa_SAYILMAZ(tmp_path):
    """Boş dizge bir çapa DEĞİLDİR — `""` ile `None` aynı hükmü alır."""
    _, sonuc, _ = _kosum(tmp_path, _dolu_pencere() + [_satir("P-bos", r=99.0, hash_="")])
    assert sonuc["n"] == gi.N_ALT and any("P-bos" in x for x in sonuc["olculemeyen"])


# =================================================================================================
# ÇİVİ 6 — BOOTSTRAP DONUK: tohum/B/blok ADIYLA çıktıda; IID REDDEDİLİR
# =================================================================================================
def test_civi6_bootstrap_tohum_B_blok_ciktida_ADIYLA_yazilidir(tmp_path):
    from meridian.olcum_araclari import BOOTSTRAP_N, BOOTSTRAP_TOHUM
    _, sonuc, _ = _kosum(tmp_path, _dolu_pencere())
    ci = sonuc["ci"]
    assert ci["tohum"] == BOOTSTRAP_TOHUM and ci["B"] == BOOTSTRAP_N
    assert ci["blok"] >= 2 and ci["blok_kaynagi"] == "n^(1/3) kuralı"
    assert "moving" in ci["yontem"] and str(ci["tohum"]) in ci["yontem"]
    assert sonuc["ci_kabul"] is True and ci["iid"] is False


def test_civi6_IID_bootstrap_REDDEDILIR(tmp_path):
    """n çok küçükken blok 1'e düşer: aralık IID'dir ve kartın donuk yöntemini SINAMAZ."""
    _, sonuc, _ = _kosum(tmp_path, _dolu_pencere(3))
    assert sonuc["ci"]["blok"] == 1 and sonuc["ci"]["iid"] is True
    assert sonuc["ci_kabul"] is False
    assert any("IID" in x and "REDDEDİLDİ" in x for x in sonuc["olculemeyen"]), \
        sonuc["olculemeyen"]


def test_civi6_CI_ayni_defterde_AYNI_araligi_verir_tekrarlanabilir(tmp_path):
    _, a, _ = _kosum(tmp_path / "a", _dolu_pencere())
    _, b, _ = _kosum(tmp_path / "b", _dolu_pencere())
    assert (a["ci"]["lo"], a["ci"]["hi"]) == (b["ci"]["lo"], b["ci"]["hi"])


def test_civi6_ci_toplam_bir_TURETMEDIR_ve_oyle_ADLANDIRILIR(tmp_path):
    _, sonuc, _ = _kosum(tmp_path, _dolu_pencere())
    t = sonuc["ci_toplam"]
    assert t["lo"] == pytest.approx(sonuc["ci"]["lo"] * sonuc["n"], abs=1e-6)
    assert "TÜRETİLMİŞ" in t["turetme"] and "ÖLÇÜLMEMİŞTİR" in t["turetme"]


def test_civi6_kartin_ci_yontemi_KULLANILAN_fonksiyonu_ADIYLA_soyler():
    """Kartın donuk `ci_yontem` alanı gerçekten çağrılan fonksiyonun adını taşımalı."""
    yontem = str(_kart()["esikler"]["ci_yontem"])
    assert "blok_bootstrap_ci" in yontem and "olcum_araclari" in yontem, yontem


# =================================================================================================
# EŞİK KAYNAĞI — kart ↔ motor sabitleri; kopya YOK, AYRIŞMA ölçülür
# =================================================================================================
def test_esikler_KART_ve_MOTOR_sabitlerinden_okunur_ayrisma_YOK(tmp_path):
    _, sonuc, _ = _kosum(tmp_path, _dolu_pencere())
    kart_esik = _kart()["esikler"]
    assert sonuc["esik_ayrismasi"] == [], sonuc["esik_ayrismasi"]
    assert sonuc["modul_sabitleri"]["N_ALT"] == gi.N_ALT == kart_esik["n_alt_plan"]
    assert sonuc["modul_sabitleri"]["PENCERE_GUN"] == gi.PENCERE_GUN \
        == kart_esik["pencere_gun_ust"]
    assert sonuc["esikler"] == kart_esik, "kart eşik bloğu olduğu gibi taşınmadı"


def test_kart_MOTORDAN_ayrisirsa_yayin_ENGELLENIR(tmp_path):
    """Sahte kartta eşik oynatılınca ayrışma ölçülür ve K bloğu BASTIRILIR (tek-kaynak yasası)."""
    kart = _kart()
    kart["esikler"]["kazanma_alt"] = float(gi.KAZANMA_ALT) + 0.1
    sahte = tmp_path / "sahte_kart.yaml"
    sahte.write_text(yaml.safe_dump(kart, allow_unicode=True), encoding="utf-8")
    _, sonuc, _ = _kosum(tmp_path, _dolu_pencere(), kart=sahte)
    assert any("kazanma_alt" in x for x in sonuc["esik_ayrismasi"]), sonuc["esik_ayrismasi"]
    assert sonuc["n"] is None and any("ayrışması" in x for x in sonuc["yayin_engeli"])


def test_sayacta_esik_SAYISI_literal_olarak_YAZILI_DEGIL():
    """Donuk eşikler sayaçta ÜÇÜNCÜ bir kopya kazanmaz — kaynakta literal olarak geçmezler."""
    src = BETIK_YOLU.read_text(encoding="utf-8")
    kod = "\n".join(s for s in src.splitlines() if not s.lstrip().startswith("#"))
    govde = kod.split('"""', 2)[-1]           # modül başlığı BEYANdır, sayı anabilir
    for sabit in (str(gi.N_ALT), str(gi.KAZANMA_ALT), str(gi.PENCERE_GUN), str(gi.FARK_R_UST)):
        assert sabit not in govde, f"eşik sayısı sayaç GÖVDESİNE kopyalanmış: {sabit}"


# =================================================================================================
# ÇİVİ 7 — KOMUT SATIRI (ops sözleşmesi KOMUT SATIRIdır) + SALT OKUNURLUK
# =================================================================================================
def test_civi7_komut_satiri_operatorun_kosacagi_BICIMDE_kosar_ve_state_e_YAZMAZ(tmp_path):
    defter = _defter_yaz(tmp_path / "girdi" / "golge_icra.jsonl", _dolu_pencere())
    onceki = defter.read_bytes()
    cikti, md = tmp_path / "out" / "sonuc.json", tmp_path / "out" / "sonuc.md"
    ortam = dict(os.environ, MERIDIAN_ROOT=str(tmp_path), PYTHONPATH=str(KOK))
    r = subprocess.run([sys.executable, str(BETIK_YOLU), "--defter", str(defter),
                        "--cikti", str(cikti), "--markdown", str(md),
                        "--kart", str(KART_YOLU), "--goal", str(GOAL_YOLU),
                        "--pk3", str(PK3_ARTEFAKT)],
                       capture_output=True, text=True, cwd=str(tmp_path), env=ortam)
    assert r.returncode == 0, (r.returncode, r.stdout, r.stderr)
    sonuc = json.loads(cikti.read_text(encoding="utf-8"))
    assert sonuc["n"] == gi.N_ALT and sonuc["kart"] == gi.KART
    assert md.exists() and "## Eşik karşılaştırması" in md.read_text(encoding="utf-8")
    assert defter.read_bytes() == onceki, "sayaç girdi defterini değiştirdi"
    assert not (tmp_path / "state").exists(), "sayaç state/ altına yazdı"
    # OPERATÖR PENCEREYİ VE PK DURUMUNU TERMİNALDE GÖRMELİ (sessiz sıfır rapor sınıfı).
    for parca in ("pencere_doldu=", "pencere_disi=", "pk2=", "pk3=", "yayin_engeli="):
        assert parca in r.stdout, r.stdout


def test_ithal_meridian_obs_u_TETIKLEMEZ_ve_state_ACMAZ(tmp_path):
    """Brief'in ölçüm kalemi: sabitleri ithal etmek canlı deftere yazan modülü YÜKLEMİYOR mu?"""
    ortam = dict(os.environ, MERIDIAN_ROOT=str(tmp_path), PYTHONPATH=str(KOK))
    kod = ("import sys, json, importlib.util;"
           f"spec=importlib.util.spec_from_file_location('s', r'{BETIK_YOLU}');"
           "m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m);"
           "print(json.dumps({'obs': 'meridian.obs' in sys.modules,"
           " 'loop': 'meridian.loop' in sys.modules,"
           " 'alpaca': 'meridian.adapters.alpaca' in sys.modules}))")
    r = subprocess.run([sys.executable, "-c", kod], capture_output=True, text=True,
                       cwd=str(tmp_path), env=ortam)
    assert r.returncode == 0, (r.stdout, r.stderr)
    olculen = json.loads(r.stdout.strip().splitlines()[-1])
    assert olculen == {"obs": False, "loop": False, "alpaca": False}, olculen
    assert not (tmp_path / "state").exists(), "ithal `state/` açtı"


def test_defter_verilmezse_hata(tmp_path):
    ortam = dict(os.environ, MERIDIAN_ROOT=str(tmp_path), PYTHONPATH=str(KOK))
    r = subprocess.run([sys.executable, str(BETIK_YOLU), "--cikti", str(tmp_path / "o.json")],
                       capture_output=True, text=True, cwd=str(tmp_path), env=ortam)
    assert r.returncode != 0
    assert "--defter" in (r.stderr or ""), r.stderr


def test_olmayan_defter_yolu_HATA_verir_bos_rapor_URETMEZ(tmp_path):
    s = _sayim()
    with pytest.raises(FileNotFoundError):
        s.calistir(defter=tmp_path / "yok.jsonl", kart=KART_YOLU, goal=GOAL_YOLU)


def test_bozuk_baslangic_DURDURUR_sessizce_bosaltmaz(tmp_path):
    s = _sayim()
    defter = _defter_yaz(tmp_path / "d.jsonl", _dolu_pencere())
    with pytest.raises(SystemExit):
        s.calistir(defter=defter, kart=KART_YOLU, goal=GOAL_YOLU, baslangic="dun")


# =================================================================================================
# PENCERE SÜZGECİ + BOZUK GİRDİ
# =================================================================================================
def test_baslangic_penceresi_ESKI_satirlari_disarida_birakir(tmp_path):
    taze = _dolu_pencere()
    eski = [_satir(f"E-{i}", r=5.0, gun_once=400) for i in range(3)]
    sinir = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=30)).isoformat()
    _, sonuc, _ = _kosum(tmp_path, eski + taze, baslangic=sinir)
    assert sonuc["girdi"]["n_pencere_disi"] == 3
    assert sonuc["n"] == gi.N_ALT and sonuc["toplam_r"] == pytest.approx(
        sum(r["R"] for r in taze), abs=1e-6)


def test_AYNI_ANI_gosteren_iki_damga_bicimi_AYNI_pencereyi_verir(tmp_path):
    an = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=30)
    _, a, _ = _kosum(tmp_path / "a", _dolu_pencere(), baslangic=an.isoformat())
    _, b, _ = _kosum(tmp_path / "b", _dolu_pencere(),
                     baslangic=an.isoformat().replace("+00:00", "Z"))
    assert a["girdi"]["n_pencere_disi"] == b["girdi"]["n_pencere_disi"] and a["n"] == b["n"]


def test_bozuk_satir_SAYILIR_ve_sayimi_dusurmez(tmp_path):
    defter = tmp_path / "state" / "golge_icra.jsonl"
    _defter_yaz(defter, _dolu_pencere())
    with defter.open("a", encoding="utf-8") as f:
        f.write("{bu json degil\n[1,2,3]\n")
    s = _sayim()
    sonuc = s.calistir(defter=defter, kart=KART_YOLU, goal=GOAL_YOLU)
    assert sonuc["girdi"]["n_bozuk_satir"] == 2 and sonuc["n"] == gi.N_ALT
    assert any("bozuk_satir" in x for x in sonuc["olculemeyen"])


def test_bos_defterde_sayilar_None_ve_NEDEN_sifir_DEGIL(tmp_path):
    """Kanıt yokken 'her şey yolunda' gösterilmez: toplam R 0 değil None."""
    _, sonuc, _ = _kosum(tmp_path, [])
    assert sonuc["n"] == 0 and sonuc["toplam_r"] is None and sonuc["kazanma_orani"] is None
    assert sonuc["pencere"]["doldu"] is None and sonuc["pencere"]["gecen_gun"] is None
    assert sonuc["ci"]["lo"] is None and sonuc["ci"]["neden"]
    assert any("pencere" in x for x in sonuc["olculemeyen"])


def test_bedel_satir_gun_ve_bayt_raporlanir(tmp_path):
    _, sonuc, defter = _kosum(tmp_path, _dolu_pencere())
    assert sonuc["bedel"]["bayt"] == defter.stat().st_size
    assert sonuc["bedel"]["n_ham_satir"] == gi.N_ALT
