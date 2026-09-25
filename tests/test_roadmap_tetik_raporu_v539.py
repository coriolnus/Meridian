"""test_roadmap_tetik_raporu_v539.py — ROADMAP tetik raporu (TSK-217): vadesi geçen okuma, bayat aktif,
operatörde bekleyen, sayaç tetikleri.

VAKA (2026-09-24): iki "2 hafta sonra oku" okuması (TSK-162 vade 09-21, TSK-074 vade 09-18), bir sayaç
tetiği (TSK-196 ≥5 → 7) ve 9 gün kapanış yazımsız bir ACTIVE kalem (TSK-070) elle bulundu. Rapor
`ops/roadmap_cephe_ozeti.py`nin AYNI ayrıştırıcısını kullanır (tek kaynak).
"""
from __future__ import annotations

import datetime as dt
import pathlib

from tests.conftest import betikten_modul_yukle

KOK = pathlib.Path(__file__).resolve().parents[1]
BETIK = KOK / "ops" / "roadmap_cephe_ozeti.py"
BUGUN = dt.date(2026, 9, 24)


def _mod():
    return betikten_modul_yukle(BETIK, "roadmap_cephe_ozeti_v539")


SENTETIK = """\
## §2 TAHTA

| id | ad | durum | owner | size | trigger |
|---|---|---|---|---|---|
| TSK-801 | tahta kalemi (WP: WP3) | ACTIVE | rol1 | M | — |
  Not (TSK-801): (2026-09-04 kablolandı; operatör: sayacı 2 hafta sonra oku)

## §4 ÖNERİ HAVUZU

- **[TSK-810] okuması vadesi geçmiş** — status: ACTIVE · born: 2026-09-07 · owner: rol1 · size: S · trigger: —
  What: (13:5xZ SAYIM BAŞLADI 2026-09-07: 2 hafta sonra sayım → ölçüt.)
  Ref: PRG-06 · kaynak
- **[TSK-811] okuması yapılmış** — status: ACTIVE · born: 2026-09-01 · owner: rol1 · size: S · trigger: —
  What: (2026-09-22 OKUMA yapıldı: sonuç yazıldı.) (2026-09-01 başladı: 10 gün sonra oku.)
  Ref: PRG-06 · kaynak
- **[TSK-812] ileri tarihli öngörü taşıyan bayat aktif** — status: ACTIVE · born: 2026-09-01 · owner: rol1 · size: S · trigger: —
  What: (2026-09-10 ölçüm: hız yavaş, eşiğe ≈2026-10-22.)
  Ref: PRG-06 · kaynak
- **[TSK-813] operatör kararı** — status: OPERATOR · born: 2026-09-01 · owner: rol1 · size: S · trigger: —
  What: (2026-09-15 karar bekliyor.)
  Ref: PRG-04 · kaynak
- **[TSK-814] sayaç kapılı** — status: GATED(n≥30 — 2026-09-15 n=1) · born: 2026-09-01 · owner: rol1 · size: S · trigger: gölge defteri n≥30 ∧ CI-alt>0
  Ref: PRG-11 · kaynak
- **[TSK-815] tarih bağlamlı kapı (sayaç değil)** — status: GATED(operatör kararı) · born: 2026-09-01 · owner: rol1 · size: S · trigger: TSK-060 operatör kararı (EDG hükmü 2026-09-21)
  Ref: PRG-13 · kaynak
- **[TSK-816] kapanmış** — status: DONE(2026-09-20) · born: 2026-09-01 · owner: rol1 · size: S · trigger: —
  What: (2026-09-01 başladı: 3 gün sonra oku.)
  Ref: PRG-06 · kaynak
"""


def _anahtarli(rapor, sinif):
    return {r["tsk"]: r for r in rapor[sinif]}


def test_T1_vadesi_gecen_okuma_isaretlenir_ve_gecikme_olculur():
    r = _mod().tetik_raporu(SENTETIK, BUGUN)
    v = _anahtarli(r, "vadesi_gecen_okuma")
    assert set(v) == {"TSK-801", "TSK-810"}, r["vadesi_gecen_okuma"]
    assert (v["TSK-810"]["vade"], v["TSK-810"]["gecikme_gun"]) == ("2026-09-21", 3)
    assert (v["TSK-801"]["vade"], v["TSK-801"]["gecikme_gun"]) == ("2026-09-18", 6)


def test_T2_vadeden_sonra_not_varsa_okuma_yapilmis_sayilir():
    r = _mod().tetik_raporu(SENTETIK, BUGUN)
    assert "TSK-811" not in _anahtarli(r, "vadesi_gecen_okuma")


def test_T3_kapali_kalem_raporlanmaz():
    r = _mod().tetik_raporu(SENTETIK, BUGUN)
    assert all(x["tsk"] != "TSK-816" for sinif in r.values() for x in sinif)


def test_T4_bayat_aktif_ileri_tarihi_saymaz():
    """TSK-812'nin metnindeki ≈2026-10-22 bir öngörüdür; en yeni not 2026-09-10 → 14 gün → bayat."""
    r = _mod().tetik_raporu(SENTETIK, BUGUN)
    b = _anahtarli(r, "bayat_aktif")
    assert b["TSK-812"] == {"tsk": "TSK-812", "en_yeni_not": "2026-09-10", "gun": 14}
    assert "TSK-811" not in b, "2026-09-22 notu 2 günlük — bayat değil"


def test_T5_operatorde_bekleyen_ve_sayac_tetikleri():
    r = _mod().tetik_raporu(SENTETIK, BUGUN)
    assert _anahtarli(r, "operatorde_bekleyen")["TSK-813"]["gun"] == 9
    s = _anahtarli(r, "sayac_tetikleri")
    assert set(s) == {"TSK-814"}, "tarih BAĞLAMLI tetik (TSK-815) sayaç sayılmamalı"


def test_T6_gecerli_olmayan_tarih_elenir():
    m = _mod()
    assert m._gecmis_tarihler("2026-13-40 ve 2026-09-01 ve 2026-12-01", BUGUN) == [dt.date(2026, 9, 1)]


def test_T7_cli_tetikler_bos_siniflari_da_adiyla_basar(tmp_path, capsys):
    m = _mod()
    p = tmp_path / "ROADMAP.md"
    p.write_text("## §4 BOŞ\n", encoding="utf-8")
    assert m.main(["--tetikler", "--dosya", str(p), "--bugun", "2026-09-24"]) == 0
    cikti = capsys.readouterr().out
    for baslik in ("VADESİ GEÇEN OKUMA: 0", "BAYAT AKTİF", "OPERATÖRDE BEKLEYEN: 0", "SAYAÇ TETİKLERİ"):
        assert baslik in cikti, cikti


def test_T8_gercek_roadmap_rapor_kosar_bes_sinif():
    """Beşinci sınıf BAYAT KAPI 2026-09-25'te eklendi (TSK-220; çivileri v544)."""
    m = _mod()
    r = m.tetik_raporu((KOK / "ROADMAP.md").read_text(encoding="utf-8"), BUGUN)
    assert set(r) == {"vadesi_gecen_okuma", "bayat_aktif", "bayat_kapi", "operatorde_bekleyen", "sayac_tetikleri"}
    assert r["sayac_tetikleri"], "gerçek dosyada en az bir sayaç tetiği bekleniyordu (2026-09-24: 4)"


# ---------------------------------------------------------------------------------------------
# TUR 2 (inceleme engelleyicileri): tekil vade kaydı + tahta notları yalnız §2'den
# ---------------------------------------------------------------------------------------------

TUR2 = """\
## §2 TAHTA

| id | ad | durum | owner | size | trigger |
|---|---|---|---|---|---|
| TSK-821 | alıntılı taahhüt (WP: WP3) | ACTIVE | rol1 | M | — |
  Not (TSK-821): (2026-09-04 kablolandı; operatör: 2 hafta sonra oku) — şart hatırlatması: '2 hafta sonra oku' yerinde.
| TSK-822 | arşivde alıntılanan (WP: WP8) | ACTIVE | rol1 | M | — |
  Not (TSK-822): (2026-09-05 pano bacağı; 2 hafta sonra oku)

## §8 ARŞİV

Tahta satırı (aynen): | TSK-822 | arşivde alıntılanan (WP: WP8) | DONE(2026-09-23) | rol1 | M | — |
  Not (TSK-822): (2026-09-23 KAPANDI — okuma yapıldı, arşive alındı)
"""


def test_T9_ayni_taahhudun_alintisi_TEK_kayit_uretir():
    r = _mod().tetik_raporu(TUR2, BUGUN)
    kayitlar = [x for x in r["vadesi_gecen_okuma"] if x["tsk"] == "TSK-821"]
    assert len(kayitlar) == 1, kayitlar
    assert kayitlar[0]["vade"] == "2026-09-18"


def test_T10_arsivdeki_ayni_bicimli_not_acik_kaleme_SIZMAZ():
    """§8'deki `  Not (TSK-822):` alıntısı (09-23) açık kalemin 'okuma yapıldı' kanıtı sayılmamalı."""
    r = _mod().tetik_raporu(TUR2, BUGUN)
    v = {x["tsk"]: x for x in r["vadesi_gecen_okuma"]}
    assert "TSK-822" in v and v["TSK-822"]["vade"] == "2026-09-19", r["vadesi_gecen_okuma"]
    b = {x["tsk"]: x for x in r["bayat_aktif"]}
    assert b["TSK-822"]["en_yeni_not"] == "2026-09-05", r["bayat_aktif"]
