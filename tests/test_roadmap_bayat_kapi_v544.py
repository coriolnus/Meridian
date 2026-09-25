"""test_roadmap_bayat_kapi_v544.py — tetik raporunun BEŞİNCİ sınıfı: BAYAT KAPI (TSK-220, 2026-09-25).

VAKA: TSK-217 raporu GATED kalemleri yalnız tetikleri SAYAÇ desenli (`n≥N`/`≥N`) ise gösteriyordu.
Düz metin tetikli kapılı kalem hiçbir bölüme girmiyordu:
  · 2026-09-25 — TSK-062'nin kapısı "geri-dolum programının tamamlanması" ~2026-09-12'de ateşledi
    (geri dolum 120 GB tavanında durdu); 13 gün kimse fark etmedi. Kalemin en yeni notu 2026-09-01.
  · 2026-09-24 — TSK-196 tetiği ateşlemişti, elle bulundu (TSK-217'yi doğuran vaka).
BAYAT KAPI: status'u GATED olan ve en yeni tarihli notu `BAYAT_KAPI_GUN` günden eski kalemler, en
eski önce, GATED(...) içindeki tetik metniyle — vardiya her tetiği elle yeniden ölçer ve tarihli not
yazar (not yazılınca kalem listeden düşer). Rapor tetiği ÖLÇMEZ (ölçülemez); yalnız sessizliği ölçer.

Canlı belge çivileri (f) çalışma ağacındaki ROADMAP'e değil git BLOB'una bağlıdır (CLAUDE.md §5:
ağaç değişir, çivi sessizce ölür) — Rol-1 TSK-062'ye bugün not düşünce ağaç çivisi kırılırdı.
"""
from __future__ import annotations

import datetime as dt
import pathlib
import subprocess

import pytest

from tests.conftest import betikten_modul_yukle

KOK = pathlib.Path(__file__).resolve().parents[1]
BETIK = KOK / "ops" / "roadmap_cephe_ozeti.py"
BUGUN = dt.date(2026, 9, 25)

#: `a210c5d6:ROADMAP.md` (main, 2026-09-25 06:41Z — TSK-220'nin taban ucu) — içerik-adresli blob.
BLOB_2026_09_25 = "25ee69b2aeb6c488fef0785e7baacb08a9b8b7e5"
#: `efae56cb:ROADMAP.md` (main, 2026-09-14 23:58Z — o günün son ROADMAP hali) — içerik-adresli blob.
BLOB_2026_09_14 = "247b49d17408a9440970d7d302b1bac3d6c26304"


def _mod():
    return betikten_modul_yukle(BETIK, "roadmap_cephe_ozeti_v544")


def _eski(gun: int) -> str:
    return (BUGUN - dt.timedelta(days=gun)).isoformat()


def _fikstur(n: int) -> str:
    uzun_kapi = "uzun kapı metni " + "ç" * 200
    uzun_tetik = "sayaç n≥30 ∧ " + "ş" * 200
    return f"""\
## §2 TAHTA

| id | ad | durum | owner | size | trigger |
|---|---|---|---|---|---|
| TSK-901 | tahta kapılı, iç içe parantezli kapı (WP: WP3) | GATED(EDG-062(b) inişinden sonra — program boyunca KAPALI) | rol1 | M | EDG-062(b) inişi |
  Not (TSK-901): ({_eski(20)} ölçüm: kapı kapalı.)
| TSK-902 | tahta aktif bayat (WP: WP3) | ACTIVE | rol1 | M | — |
  Not (TSK-902): ({_eski(30)} not.)
| TSK-903 | tahta kapılı tarihsiz (WP: WP3) | GATED(dış olay) | rol1 | S | dış olay |

## §4 ÖNERİ HAVUZU

- **[TSK-910] eski notlu kapılı** — status: GATED(geri-dolum programının tamamlanması — learn KAPALI) · born: {_eski(40)} · owner: rol1 · size: M · trigger: programın kapanışı
  What: ({_eski(n + 1)} son ölçüm: kapı kapalı.)
  Ref: PRG-03 · kaynak
- **[TSK-911] tam eşikte kapılı** — status: GATED(operatör kararı) · born: {_eski(40)} · owner: rol1 · size: S · trigger: operatör kararı
  What: ({_eski(n)} not.)
  Ref: PRG-03 · kaynak
- **[TSK-912] taze kapılı** — status: GATED(kapı) · born: {_eski(2)} · owner: rol1 · size: S · trigger: kapı
  Ref: PRG-03 · kaynak
- **[TSK-913] bayat sırada** — status: QUEUED · born: {_eski(40)} · owner: rol1 · size: S · trigger: —
  Ref: PRG-03 · kaynak
- **[TSK-914] bayat operatörde** — status: OPERATOR · born: {_eski(40)} · owner: rol1 · size: S · trigger: —
  Ref: PRG-03 · kaynak
- **[TSK-915] uzun kapı metinli** — status: GATED({uzun_kapi}) · born: {_eski(40)} · owner: rol1 · size: S · trigger: {uzun_tetik}
  Ref: PRG-03 · kaynak
- **[TSK-916] kapanmış kapılı** — status: DONE(2026-09-01) · born: {_eski(40)} · owner: rol1 · size: S · trigger: —
  Ref: PRG-03 · kaynak

## §8 ARŞİV

Tahta satırı (aynen): | TSK-901 | tahta kapılı (WP: WP3) | GATED(EDG-062(b) inişinden sonra) | rol1 | M | — |
  Not (TSK-901): ({_eski(1)} arşiv alıntısı — açık kaleme SIZMAMALI)
"""


def _rapor():
    m = _mod()
    return m, m.tetik_raporu(_fikstur(m.BAYAT_KAPI_GUN), BUGUN)


def _kapi(rapor) -> dict[str, dict]:
    return {r["tsk"]: r for r in rapor["bayat_kapi"]}


def _blob(sha: str) -> str:
    """İçerik-adresli ROADMAP sürümü. KOŞUL YALNIZ NESNENİN VARLIĞIDIR (conftest beyanlı atlama ilkesi):
    nesne varsa çivi normal koşar ve düşerse DÜŞER; yoksa (sığ klon) ölçülemedi diye ADIYLA atlanır."""
    r = subprocess.run(["git", "-C", str(KOK), "show", sha], capture_output=True, text=True)
    if r.returncode != 0:
        pytest.skip(f"ÖLÇÜLEMEDİ: git blob {sha} bu klonda yok (sığ klon?) — {r.stderr.strip()[:200]}")
    return r.stdout


# ---- (a) eşikten eski notlu GATED kalem listelenir, GATED(...) tetik metniyle -----------------------

def test_K1_esikten_eski_gated_kalem_tetik_metniyle_listelenir():
    m, r = _rapor()
    n = m.BAYAT_KAPI_GUN
    assert _kapi(r)["TSK-910"] == {"tsk": "TSK-910", "en_yeni_not": _eski(n + 1), "gun": n + 1,
                                   "tetik": "geri-dolum programının tamamlanması — learn KAPALI"}, \
        "tetik GATED(...) içinden gelmeli, `trigger:` alanından değil"


# ---- (b) eşikten taze olan listelenmez (tam eşik dahil) ------------------------------------------

def test_K2_esikte_ve_taze_gated_kalem_listelenmez():
    _, r = _rapor()
    k = _kapi(r)
    assert "TSK-911" not in k, "tam BAYAT_KAPI_GUN gün: eşik '>' — listelenmemeli"
    assert "TSK-912" not in k


# ---- (c) ACTIVE/QUEUED/OPERATOR/DONE kalem bu bölüme girmez ------------------------------------

def test_K3_gated_olmayan_kalem_bayat_kapiya_girmez():
    m, r = _rapor()
    k = _kapi(r)
    for tsk in ("TSK-902", "TSK-913", "TSK-914", "TSK-916"):
        assert tsk not in k, (tsk, r["bayat_kapi"])
    durum = {x["tsk"]: x["durum"] for x in m.acik_kalemler(_fikstur(m.BAYAT_KAPI_GUN))}
    assert all(durum[x["tsk"]] == "GATED" for x in r["bayat_kapi"])


# ---- (d) tahta satırı GATED kalem de kapsanır (§2 notları, iç içe parantez, §8 sızmaz) ---------

def test_K4_tahta_satiri_gated_kalem_kapsanir_ic_ice_parantezle():
    _, r = _rapor()
    k = _kapi(r)
    assert k["TSK-901"] == {"tsk": "TSK-901", "en_yeni_not": _eski(20), "gun": 20,
                            "tetik": "EDG-062(b) inişinden sonra — program boyunca KAPALI"}, \
        "tahta notu §2'den; §8 alıntısı (1 günlük) sızmamalı; iç içe parantez kırpılmamalı"


# ---- (e) en eski önce sıralanır (tarihsiz = yaşı bilinmeyen, en başta) --------------------------

def test_K5_en_eski_once_siralanir():
    _, r = _rapor()
    assert [x["tsk"] for x in r["bayat_kapi"]] == ["TSK-903", "TSK-915", "TSK-901", "TSK-910"]


# ---- (g) sessiz düşme ve sessiz kırpma yok -------------------------------------------------------

def test_K6_tarihsiz_gated_kalem_sessizce_dusmez():
    _, r = _rapor()
    assert _kapi(r)["TSK-903"] == {"tsk": "TSK-903", "en_yeni_not": None, "gun": None, "tetik": "dış olay"}


def test_K7_uzun_tetik_kisaltildigi_adiyla_belli_kirpilir():
    m, r = _rapor()
    a = m.TETIK_AZAMI
    kapi = "uzun kapı metni " + "ç" * 200
    assert _kapi(r)["TSK-915"]["tetik"] == f"{kapi[:a]}… [kısaltıldı: {len(kapi)}→{a} karakter]"
    tetik = "sayaç n≥30 ∧ " + "ş" * 200
    sayac = {x["tsk"]: x for x in r["sayac_tetikleri"]}
    assert sayac["TSK-915"]["tetik"] == f"{tetik[:a]}… [kısaltıldı: {len(tetik)}→{a} karakter]", \
        "sayaç bölümü de aynı kısaltıcıyı kullanır (tek kaynak)"
    assert m._kisalt("  kısa  ") == "kısa"


# ---- CLI: bölüm boşken de ADIYLA basılır; doluyken satır tetik metnini taşır ---------------------

def test_K8_cli_bayat_kapi_bolumunu_basar(tmp_path, capsys):
    m = _mod()
    bos = tmp_path / "BOS.md"
    bos.write_text("## §4 BOŞ\n", encoding="utf-8")
    assert m.main(["--tetikler", "--dosya", str(bos), "--bugun", BUGUN.isoformat()]) == 0
    assert f"== BAYAT KAPI (GATED, > {m.BAYAT_KAPI_GUN} gün notsuz" in capsys.readouterr().out
    dolu = tmp_path / "ROADMAP.md"
    dolu.write_text(_fikstur(m.BAYAT_KAPI_GUN), encoding="utf-8")
    assert m.main(["--tetikler", "--dosya", str(dolu), "--bugun", BUGUN.isoformat()]) == 0
    cikti = capsys.readouterr().out
    assert "BAYAT KAPI (GATED" in cikti and ": 4" in cikti.split("BAYAT KAPI", 1)[1].splitlines()[0]
    assert "tsk=TSK-910 · en_yeni_not=" in cikti and "tetik=geri-dolum programının tamamlanması" in cikti


# ---- (f) gerçek ROADMAP (git blob'una bağlı): TSK-062 bugün listelenir ve vakada yakalanırdı -----

def test_K9_gercek_roadmap_2026_09_25_tsk062_listelenir():
    m = _mod()
    r = m.tetik_raporu(_blob(BLOB_2026_09_25), BUGUN)
    assert _kapi(r).get("TSK-062") == {
        "tsk": "TSK-062", "en_yeni_not": "2026-09-01", "gun": 24,
        "tetik": "geri-dolum programının tamamlanması — learn program boyunca KAPALI"}, r["bayat_kapi"]


def test_K10_esik_vakayi_yakalar_2026_09_14_te_tsk062_listelenirdi():
    """Tetik ~2026-09-12'de ateşledi, 13 gün fark edilmedi. Eşik bu sessizliği yakalamalı: 09-14'ün
    ROADMAP'inde (en yeni not 09-01, 13 gün) TSK-062 listede olurdu. Eşiği ≥13'e gevşetmek bunu kırar."""
    m = _mod()
    r = m.tetik_raporu(_blob(BLOB_2026_09_14), dt.date(2026, 9, 14))
    assert _kapi(r).get("TSK-062", {}).get("gun") == 13, r["bayat_kapi"]


def test_K11_calisma_agaci_roadmap_bayat_kapi_degismezleri():
    """Canlı belge (ağaç): her kayıt açık bir GATED kalemdir, tetiği boş değildir, yaşı eşiği aşar ya da
    tarihsizdir ve liste en eski önce sıralıdır. Kalem kimliği sabitlenmez — belge değişir."""
    m = _mod()
    metin = (KOK / "ROADMAP.md").read_text(encoding="utf-8")
    r = m.tetik_raporu(metin, BUGUN)
    durum = {x["tsk"]: x["durum"] for x in m.acik_kalemler(metin)}
    for x in r["bayat_kapi"]:
        assert durum.get(x["tsk"]) == "GATED", x
        assert x["tetik"].strip(), x
        assert x["gun"] is None or x["gun"] > m.BAYAT_KAPI_GUN, x
    tarihli = [x["en_yeni_not"] for x in r["bayat_kapi"] if x["en_yeni_not"] is not None]
    assert tarihli == sorted(tarihli)
