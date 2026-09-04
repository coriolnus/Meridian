"""tests/test_birim_timeout_v409.py — TSK-123, 2026-09-04.

Dört oneshot brifing biriminde (`meridian-brifing` · `meridian-bekci` · `meridian-karne` ·
`meridian-skill-gorus`) `TimeoutStartSec=` beyanı ölçülür (A1'de dördü de `infinity` idi:
`systemctl show -p TimeoutStartUSec`). Asılı bir çağrı (`hermes -z` alt süreci) birimi sonsuza
dek `activating` bırakır ve etkin bir oneshot'ken timer BİR SONRAKİ tetiği ATLAR — sessiz
teslimat düşüşü (TSK-014 Ö-5). Bu çivi tavanın VARLIĞINI, SAYISAL olduğunu, makul bir aralıkta
durduğunu ve — üç bot (`@sef`/`@bekci`/`@karne`) için — gerçek en-kötü-yol formülünü
(`KOSUM_CAGRI_TAVANI × PROFIL_TIMEOUT_S`) EN AZ karşıladığını ölçer.

SABİTLER KAYNAKTAN İTHAL EDİLİR, ÇİVİYE YAZILMAZ (tek-kaynak yasası) — `PROFIL_TIMEOUT_S` üç
harness dosyasının HER BİRİNDE ayrı ayrı tanımlıdır (bilerek, `ops/soul_denetimi.py` başlığının
gerekçesiyle: türetim döngüsel ithal olurdu) ve `KOSUM_CAGRI_TAVANI` `ops/soul_denetimi.py`de
TEK yerde tanımlıdır. Bu çivi üçünü de MODÜLDEN okur; bir sabit kaynakta değişirse çivi
YENİDEN HESAPLAR, eski bir sayıyı tekrarlamaz.

`meridian-skill-gorus.service` KAPSAM DIŞI BIRAKILMAZ ama FORMÜLE TABİ DEĞİLDİR: ExecStart'ı
(`--uygula`) ÖLÇÜLDÜ (grep, 2026-09-04) — `ops/skill_gorus_uret.py`de `subprocess`/`requests`/
`urllib`/`socket`/`_profili_cagir`/`soul_denetimi` hiçbiri yok, yani sayılacak bir hermes çağrısı
yok ve `PROFIL_TIMEOUT_S` o dosyada TANIMLI DEĞİL. Bu birim yalnız VARLIK+ARALIK çivisine tabidir.
"""
from __future__ import annotations

import importlib
import pathlib

import pytest

KOK = pathlib.Path(__file__).resolve().parent.parent
BIRIM_KOKU = KOK / "deploy" / "oracle-a1"

# Aralık — brief D4: 60 s ≤ değer ≤ 3600 s. Kaynağı bu çividir (yeni bir birim/formül taşımaz,
# yalnız "makul bir zaman aşımı" ne demek sorusuna bir kapı koyar).
TABAN_S = 60
TAVAN_S = 3600

# (birim dosya adı, hermes'e gerçekten giden harness modülü ya da None [formüle tabi değil]).
# Harness modülü ÖLÇÜLEREK eşlenir: her üçü de `Environment=HERMES_HOME=` ile kendi profiline
# bağlanan, `soul_denetimi.gecir`i çağıran botlardır (kaynak: bu dosyaların `ExecStart=` satırı).
BIRIMLER = [
    ("meridian-brifing.service", "ops.sef_brifingi"),
    ("meridian-bekci.service", "ops.bekci_brifingi"),
    ("meridian-karne.service", "ops.karne_brifingi"),
    ("meridian-skill-gorus.service", None),
]


def _yonergeler(yol: pathlib.Path) -> list[str]:
    """Birim dosyasının YÖNERGE satırları (yorumlar HARİÇ) — `test_bot_profil_durusu_v329.py`
    ile aynı desen: bu dosyalar kararlarını uzun uzun anlatır ve aranan anahtarların adı
    gerekçe metninde de geçer; yorumu sayan bir çivi satır DÜŞTÜKTEN sonra bile yeşil kalır."""
    return [ln.strip() for ln in yol.read_text(encoding="utf-8").splitlines()
            if ln.strip() and not ln.strip().startswith(("#", ";"))]


def _timeout_deger(yol: pathlib.Path) -> float | None:
    """`TimeoutStartSec=` YÖNERGESİNİN sayısal değeri, yoksa/ayrıştırılamazsa `None`."""
    for ln in _yonergeler(yol):
        if ln.startswith("TimeoutStartSec="):
            ham = ln.split("=", 1)[1].strip()
            try:
                return float(ham)
            except ValueError:
                return None
    return None


@pytest.mark.parametrize("ad,_mod", BIRIMLER, ids=[b[0] for b in BIRIMLER])
def test_TIMEOUT_START_SEC_VAR_SAYISAL_VE_ARALIKTA(ad, _mod):
    """VARLIK ÇİVİSİ — bir birimden `TimeoutStartSec=` satırını silmek bu çiviyi öter (D4
    mutasyonu). `infinity`/boş/dizge bir değer de aynı şekilde düşer: `float()` onu ayrıştıramaz
    ve tavan `None` kalır."""
    yol = BIRIM_KOKU / ad
    assert yol.is_file(), f"{ad}: birim dosyası depoda YOK ({yol})"
    deger = _timeout_deger(yol)
    assert deger is not None, (
        f"{ad}: `TimeoutStartSec=` YOK ya da sayısal değil — bu birim asılı bir çağrıda "
        "SONSUZA dek 'activating' kalır ve etkin oneshot'ken timer sıradaki tetiği ATLAR "
        "(TSK-014 Ö-5, sessiz teslimat düşüşü)")
    assert TABAN_S <= deger <= TAVAN_S, (
        f"{ad}: TimeoutStartSec={deger!r} aralık dışı — {TABAN_S} s ≤ değer ≤ {TAVAN_S} s olmalı "
        "(çok düşükse sağlıklı bir koşumu bile keser, çok yüksekse 'infinity'nin sessiz "
        "riskini biçim değiştirerek geri getirir)")


@pytest.mark.parametrize("ad,mod_adi", [(a, m) for a, m in BIRIMLER if m is not None],
                          ids=[b[0] for b in BIRIMLER if b[1] is not None])
def test_TIMEOUT_EN_KOTU_YOL_FORMULUNU_KARSILAR(ad, mod_adi):
    """FORMÜL ÇİVİSİ (brief D4, `@sef` için ZORUNLU — burada üç hermes-çağıran bota da
    uygulanır çünkü üçü ölçülerek AYNI yapıda bulundu: kendi `PROFIL_TIMEOUT_S`i + paylaşılan
    `ops.soul_denetimi.KOSUM_CAGRI_TAVANI`).

    Sabitler MODÜLDEN ithal edilir (uydurma yasağı + tek-kaynak yasası): bir harness dosyası
    `MODEL_TIMEOUT_S`/`HARNESS_PAYI_S`i değiştirirse bu çivi YENİDEN HESAPLAR, eski bir
    sayıyı tekrarlamaz."""
    harness = importlib.import_module(mod_adi)
    soul = importlib.import_module("ops.soul_denetimi")
    profil_timeout = getattr(harness, "PROFIL_TIMEOUT_S", None)
    kosum_tavani = getattr(soul, "KOSUM_CAGRI_TAVANI", None)
    assert isinstance(profil_timeout, (int, float)), (
        f"{mod_adi}: `PROFIL_TIMEOUT_S` YOK ya da sayısal değil — formül ÖLÇÜLEMEDİ")
    assert isinstance(kosum_tavani, int), (
        "ops.soul_denetimi: `KOSUM_CAGRI_TAVANI` YOK ya da tamsayı değil — formül ÖLÇÜLEMEDİ")
    taban = kosum_tavani * profil_timeout
    deger = _timeout_deger(BIRIM_KOKU / ad)
    assert deger is not None, f"{ad}: `TimeoutStartSec=` YOK — kardeş çivi zaten kırmızı olmalı"
    assert deger >= taban, (
        f"{ad}: TimeoutStartSec={deger!r} < {kosum_tavani} × PROFIL_TIMEOUT_S({profil_timeout!r}) "
        f"= {taban!r} — en kötü yol (koşum başına en çok {kosum_tavani} hermes çağrısı, her biri "
        f"{profil_timeout!r} sn'ye kadar) bu tavanla KESİLİR ve teslimat GEREKSİZ YERE düşer")


@pytest.mark.parametrize("ad,_mod", BIRIMLER, ids=[b[0] for b in BIRIMLER])
def test_BASLIK_SERHI_KUNYE_VE_KAYNAK_ADLARINI_TASIR(ad, _mod):
    """Başlık şerhi formülü ANLATMALI, sayıyı ÇIPLAK bırakmamalı (CLAUDE.md §2 "değer tahmin
    etmek" satırı + künye kuralı). Künye eksikse bu değerin HANGİ turda NEDEN seçildiği bir
    sonraki okuyucu için kaybolur; kaynak sabitin adı eksikse değer sayının kendisiyle
    AYRIŞABİLİR (tek-kaynak yasası) ve kimse fark etmez."""
    metin = (BIRIM_KOKU / ad).read_text(encoding="utf-8")
    assert "TSK-123, 2026-09-04" in metin, f"{ad}: başlık şerhinde `TSK-123, 2026-09-04` künyesi YOK"
    assert "PROFIL_TIMEOUT_S" in metin, (
        f"{ad}: şerh `PROFIL_TIMEOUT_S` kaynak sabitinin ADINI anmıyor — sayı çıplak yazılmış "
        "olabilir (uydurma/tek-kaynak riski)")
    assert "TimeoutStartSec=" in metin, f"{ad}: yönerge dosyada beklenirken bulunamadı"
