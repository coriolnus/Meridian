"""v577 — metin/çapraz-biçim çapa dünyasının hedef kökünde `deploy/` (TSK-245, 2026-09-28).

BOŞLUK (TSK-244(b) kaygı K1 → inceleme ORTA → TSK-245): TSK-244(b) `deploy`u altı çapa dünyasının çözücü ağacına
(`codelaw._EK_CAPA_KOKLERI` → `report()`in `capa_kokleri`) kattı; dördüncü dünya (düz-metin/çapraz-biçim,
`codelaw.stale_text_anchors`) ise hedeflerini ELLE YAZILMIŞ ayrı bir listeden (`codelaw._TEXT_HEDEF_KOKLERI`:
meridian·tests·ops·docs·state) arıyordu ve `report()` ona kök geçmiyordu. `docs/RUNBOOK.md`deki bakim_h9.sh
satır-59 çapası (hedef `deploy/oracle-a1/` altında VAR) bu yüzden kalıcı `hedef_yok` idi — bayatlasa da ötmezdi.

DEĞİŞİKLİK (motor): `codelaw._TEXT_HEDEF_KOKLERI` artık TÜRETİLİR — Python kısmı `report()`in çözücü ağacıyla aynı
kaynaktan (`codelaw.URETIM_KOKLERI` + `codelaw._EK_CAPA_KOKLERI`), üstüne yalnız metin dünyasına ait `docs`+`state`.
Çözücü ağacına ileride eklenen bir kök metin dünyasına kendiliğinden girer; elle ikinci bir liste yok (v576 deseni).

ADIM-0 ÖLÇÜMÜ (2026-09-28, taban e67c64ec; pytest içi karşı-olgusal yoklama, kod değişmeden; `stale_text_anchors`
döngüsünün replikası iki defterde de gerçek çıktıyla birebir doğrulandı — depo dışı `scratchpad/tsk245/adim0.json`):
  * Taranan 14 metin çapası: 10 çözülen → çözülen (hedef AYNI), 1 hedef_yok → çözülen (bakim_h9; hedef satırı içerik
    olarak da doğru — openssl token satırı), 2 hedef_yok → hedef_yok, 1 dosya_belirtilmemis. YANLIŞ HEDEFE geçen 0.
    Çürük 0 → 0, çözülemeyen 4 → 3. `report()["ok"]` True → True (bu dünya `ok`u yapısal olarak etkilemez).
  * AD ÇAKIŞMASI: deploy 63 dosya / 51 ad ekler; 49 ad yeni, 2 ad mevcut bir adla ÇAKIŞIR — `RUNBOOK.md`
    (`docs/` ↔ `deploy/oracle-a1/`) ve `README.md` (depo kökü ↔ `deploy/ansible/`). Ana checkout'un dolu `state/`i
    de sayıldığında aynı iki ad (yalnız dosya adı listesi). Bugün bu iki ada giden metin çapası 0.
  * Çakışma YANLIŞ HEDEFE ÇÖZÜM ÜRETMEZ: aday > 1 ise hüküm kurulmaz (`ikircikli` → çözülemeyen, sayılır). Bedel:
    `docs/`a ileride yazılacak YOLSUZ bir RUNBOOK/README çapası ölçülemez olur; yol önekli çapa tekil çözülür.
  * Süre: metin dünyası 73 → 82 ms (süreç içi medyan, n=7, dönüşümlü).

ÇİVİLER: A) sentetik bayat çapa — `deploy/` altındaki bir dosyaya iki biçimde (bitişik ve "satır NNN") bayat çapa
çürük raporlanır, geçerli çapa temiz çözülür; aynı ağaç `report()` yolundan da. B) yol-tutarlı pozitif kontrol —
gerçek depoda `report()` bakim_h9 çapasını çözer. C) tek çözücü ağacı — `report()` sırasında metin dünyasının
hedef kökleri diğer dünyaların çözücü köklerini KAPSAR. D) ad çakışması — iki kökte aynı adlı dosya: yolsuz çapa
`ikircikli` (hüküm yok), yol önekli çapa kendi dosyasına çözülür.
Çapa dizgeleri KODDA birleştirilir: bitişik yazılsaydı satır çapası tarayıcıları (v571) onları gerçek çapa sayardı.
"""
from __future__ import annotations

import pathlib

import pytest

from meridian import codelaw

REPO = pathlib.Path(__file__).resolve().parents[1]
_ORNEK = "tsk245_ornek.sh"
_GERCEK_KAYNAK = "docs/RUNBOOK.md"
_GERCEK_HEDEF = "deploy/oracle-a1/bakim_h9.sh"


def _capa(ad: str, n: int | str) -> str:
    return f"{ad}:{n}"


_GERCEK_CAPA = _capa(pathlib.PurePosixPath(_GERCEK_HEDEF).name, 59)


def _gercek_kok_mu() -> None:
    assert pathlib.Path.cwd().resolve() == REPO and (REPO / _GERCEK_HEDEF).is_file(), (
        "report() göreli köklerle çalışır — çivi depo kökünden koşmalı ve deploy hedefi var olmalı")


def _deploy_agaci(kok: pathlib.Path, notlar: str) -> None:
    (kok / "deploy" / "oracle-a1").mkdir(parents=True)
    (kok / "deploy" / "oracle-a1" / _ORNEK).write_text("#!/bin/sh\necho bir\necho iki\n", encoding="utf-8")
    (kok / "docs").mkdir()
    (kok / "docs" / "notlar.md").write_text(notlar, encoding="utf-8")


# =================================================================================================
# A) SENTETİK BAYAT ÇAPA — `deploy/` altındaki hedef metin dünyasında ölçülür
# =================================================================================================

@pytest.mark.parametrize("satir,capa", [
    (f"token deseni `{_capa(_ORNEK, 99)}`de\n", _capa(_ORNEK, 99)),
    (f"`{_ORNEK}` başlığı (satır 99) desenini taşır\n", "satır 99"),
], ids=["bitisik", "satir-NNN"])
def test_SENTETIK_deploy_hedefli_BAYAT_capa_CURUK_raporlanir(tmp_path, monkeypatch, satir, capa):
    """Varsayılan kökle (`report()`in kullandığı) çağrılır. `deploy` kökte değilse çapa `hedef_yok` → çözülemeyen
    kovasına düşer, çürükte görünmez → KIRMIZI."""
    _deploy_agaci(tmp_path, satir)
    monkeypatch.chdir(tmp_path)
    kor: list = []
    curuk = codelaw.stale_text_anchors(codelaw.DOCS_CAPA_KOKU, cozulemeyen_out=kor)
    assert [(c["capa"], c["neden"]) for c in curuk] == [(capa, "menzil_disi")], (curuk, kor)
    assert kor == [], kor


def test_SENTETIK_deploy_hedefli_GECERLI_capa_TEMIZ_cozulur(tmp_path, monkeypatch):
    """NEGATİF KONTROL: menzil içi, boş/yorum olmayan satır → ne çürük ne çözülemeyen (yani ÇÖZÜLDÜ)."""
    _deploy_agaci(tmp_path, f"token deseni `{_capa(_ORNEK, 2)}` ve `{_ORNEK}` (satır 3)\n")
    monkeypatch.chdir(tmp_path)
    kor: list = []
    curuk = codelaw.stale_text_anchors(codelaw.DOCS_CAPA_KOKU, cozulemeyen_out=kor)
    assert curuk == [] and kor == [], (curuk, kor)


def test_SENTETIK_deploy_hedefli_BAYAT_capa_REPORT_yolundan_gorunur(tmp_path, monkeypatch):
    """YOL TUTARLILIĞI: aynı sentetik çürük `report()` üzerinden `text_anchor_stale`e düşer (report metin dünyasına
    kök geçerse ya da geçmezse — hangi yoldan olursa olsun `deploy` görülmeli). `root="meridian"` üretim kapısını
    açar (v391 emsali); diğer yasaların sentetik ağaçtaki kırmızısı bu çivinin konusu değil."""
    capa = _capa(_ORNEK, 99)
    _deploy_agaci(tmp_path, f"token deseni `{capa}`de\n")
    for d in ("meridian", "tests", "ops", "ui/src"):
        (tmp_path / d).mkdir(parents=True)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(codelaw, "UNSCANNED", [])
    r = codelaw.report(root="meridian")
    assert [(c["capa"], c["neden"]) for c in r["text_anchor_stale"]] == [(capa, "menzil_disi")], (
        r["text_anchor_stale"], r["text_anchor_unresolved"])


# =================================================================================================
# B + C) GERÇEK DEPO — tek `report()` koşumu, iki casus
# =================================================================================================

@pytest.fixture(scope="module")
def gercek_rapor():
    """Gerçek ağaçta TEK `report()`: metin dünyasının adres defteri çağrısı ve diğer dünyaların çözücü defteri
    çağrıları casuslanır. Yorum beslemesinin sonuç önbelleği boşaltılır ki o da defterini kursun (v576 C emsali)."""
    _gercek_kok_mu()
    metin: list[dict] = []
    capa: list[tuple[str, ...]] = []
    asil_metin, asil_capa = codelaw._text_hedef_dosyalari, codelaw._capa_adres_defteri

    def metin_casusu(kokler=codelaw._TEXT_HEDEF_KOKLERI):
        adres = asil_metin(kokler)
        metin.append({"kokler": tuple(kokler), "adres": adres})
        return adres

    def capa_casusu(kokler):
        capa.append(codelaw._kokler(kokler))
        return asil_capa(kokler)

    with pytest.MonkeyPatch.context() as m:
        m.setattr(codelaw, "UNSCANNED", [])
        m.setattr(codelaw, "_YORUM_SEMBOL_CACHE", {})
        m.setattr(codelaw, "_text_hedef_dosyalari", metin_casusu)
        m.setattr(codelaw, "_capa_adres_defteri", capa_casusu)
        r = codelaw.report()
    return {"rapor": r, "metin": metin, "capa": capa}


def test_GERCEK_bakim_h9_capasi_REPORT_yolunda_COZULUR(gercek_rapor):
    """YOL-TUTARLI POZİTİF KONTROL: gerçek `docs/RUNBOOK.md`deki bakim_h9 çapası `report()`un metin dünyasında
    tekil hedefe çözülür (çözülemeyen kovasında DEĞİL). Tabanı ayrıca sınanır: kaynak satır hâlâ taranan bir belgede
    ve muafiyetsiz — yoksa çivi boşa yeşil olurdu (RUNBOOK üretilmiş; excerpt değişirse burası güncellenir)."""
    kaynak = REPO / _GERCEK_KAYNAK
    satirlar = [s for s in kaynak.read_text(encoding="utf-8").splitlines() if _GERCEK_CAPA in s]
    assert satirlar and not codelaw._docs_capa_disi(pathlib.Path(_GERCEK_KAYNAK)), "pozitif kontrol tabanını yitirdi"
    assert all(codelaw._CAPA_MUAFIYETI not in s for s in satirlar), "taban satırı muaf — çapa taranmıyor"
    r, metin = gercek_rapor["rapor"], gercek_rapor["metin"]
    assert len(metin) == 1, len(metin)
    adaylar = [str(p) for p in metin[0]["adres"].get(pathlib.PurePosixPath(_GERCEK_HEDEF).name, [])]
    assert adaylar == [_GERCEK_HEDEF], (adaylar, metin[0]["kokler"])
    cozulemeyen = [k for k in r["text_anchor_unresolved"] if k["capa"] == _GERCEK_CAPA]
    assert cozulemeyen == [], cozulemeyen


def test_METIN_DUNYASI_hedef_kokleri_COZUCU_AGACINI_kapsar(gercek_rapor):
    """TEK ÇÖZÜCÜ AĞACI: `report()` sırasında diğer çapa dünyalarının adres defterine giden her kök, metin
    dünyasının hedef köklerinde de bulunur (deploy dahil) ve metin kökleri tekildir (aynı kök iki kez gezilirse her
    ad `ikircikli` olurdu). Metin dünyası kendi elle yazılmış listesine dönerse ya da `report()` ona deploy'suz bir
    kök listesi geçerse çivi KIRMIZI."""
    metin, capa = gercek_rapor["metin"], gercek_rapor["capa"]
    assert len(metin) == 1 and len(capa) >= 6, (len(metin), len(capa))
    metin_kokleri = [pathlib.Path(k).resolve() for k in metin[0]["kokler"]]
    assert len(set(metin_kokleri)) == len(metin_kokleri), metin[0]["kokler"]
    capa_kokleri = {pathlib.Path(k).resolve() for kk in capa for k in kk}
    assert (REPO / "deploy").resolve() in capa_kokleri, sorted(map(str, capa_kokleri))
    eksik = sorted(str(k) for k in capa_kokleri - set(metin_kokleri))
    assert not eksik, (eksik, metin[0]["kokler"])


# =================================================================================================
# D) AD ÇAKIŞMASI — iki kökte aynı adlı dosya: belirlenmiş davranış
# =================================================================================================

def test_AD_CAKISMASI_yolsuz_capa_IKIRCIKLI_yol_onekli_capa_KENDI_dosyasina(tmp_path, monkeypatch):
    """Gerçek depodaki çakışmanın (docs ↔ deploy/oracle-a1 RUNBOOK) sentetik ikizi. `docs/` kopyası 5, `deploy/`
    kopyası 3 satır: `oracle-a1/…` önekli 4. satır çapasının ÇÜRÜK çıkması hedefin deploy kopyası olduğunu kanıtlar
    (docs kopyasında 4. satır geçerli). Yolsuz çapa hiçbir kopyaya hüküm ETTİRMEZ — geçerli numarada da, bayat
    numarada da `ikircikli` (aday 2) olarak sayılır: yanlış hedefe çözüm YOK. `deploy` kökte olmasaydı yolsuz
    çapa docs kopyasına sessizce çözülür, deploy önekli çapa `kapsam_disi` olurdu → KIRMIZI."""
    ad = "RUNBOOK.md"
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / ad).write_text("bir\niki\nüç\ndört\nbeş\n", encoding="utf-8")
    (tmp_path / "deploy" / "oracle-a1").mkdir(parents=True)
    (tmp_path / "deploy" / "oracle-a1" / ad).write_text("bir\niki\nüç\n", encoding="utf-8")
    yolsuz_gecerli, yolsuz_bayat = _capa(ad, 4), _capa(ad, 99)
    docs_gecerli, docs_bayat = _capa("docs/" + ad, 4), _capa("docs/" + ad, 99)
    deploy_bayat = _capa("oracle-a1/" + ad, 4)
    (tmp_path / "docs" / "notlar.md").write_text(
        f"a `{yolsuz_gecerli}`\nb `{yolsuz_bayat}`\nc `{docs_gecerli}`\nd `{docs_bayat}`\ne `{deploy_bayat}`\n"
        f"f `{ad}` bölümü (satır 4)\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    kor: list = []
    curuk = codelaw.stale_text_anchors(codelaw.DOCS_CAPA_KOKU, cozulemeyen_out=kor)
    assert sorted((c["capa"], c["neden"]) for c in curuk) == sorted(
        [(docs_bayat, "menzil_disi"), (deploy_bayat, "menzil_disi")]), (curuk, kor)
    assert sorted((k["capa"], k["neden"], k["aday_n"]) for k in kor) == sorted(
        [(yolsuz_gecerli, "ikircikli", 2), (yolsuz_bayat, "ikircikli", 2), ("satır 4", "ikircikli", 2)]), kor
