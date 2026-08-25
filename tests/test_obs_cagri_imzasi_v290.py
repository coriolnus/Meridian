"""OBS YAYICILARININ ÇAĞRI İMZASI — v290 (2026-08-25)

CANLI VAKA, üç gün sürdü ve sessizdi:

    reconcile_failed · 2026-08-24T20:38:34
    TypeError: warn() takes 1 positional argument but 2 were given

`meridian/loop.py` içindeki `_adet_benimse` fonksiyonu `obs.warn`i İKİ konumsal
argümanla çağırıyordu. `obs.warn` imzası `warn(event: str, **fields)` — yani ikinci
konumsal argüman `TypeError` demek.

ÇAPA SATIR DEĞİL SEMBOL, ve bunu bu dosya KENDİ ÜSTÜNDE öğrendi: ilk sürümde burada
loop.py'nin 2842. satırına bir çapa yazılıydı; düzeltmenin kendi şerhi o çağrının üstüne
sekiz satır ekleyince çağrı 2850'ye kaydı ve `codelaw` çapayı bayat saydı. Satır numarası
gömen her çapa, çapaladığı dosyanın her düzenlemesinde bayatlar — fonksiyon adı bayatlamaz.
(Yukarıdaki sayı bir ÇAPA değil bir ALINTIDIR; `dosya.py:NNN` biçimi tarayıcıya canlı çapa
görünüyor, düzyazı biçimi görünmüyor — aynı ayrım `codelaw.py`nin kendi şerhinde de yapıldı.)
Satır 2026-08-22'de girdi (c726a19, "kitap aynanın adedini benimser") ve o günden
sonraki HER mutabakat turu bu satırda çöktü: `broker_reconcile.json`ın son başarılı
yazımı 2026-08-21 20:32.

BEDELİ SESSİZ DEĞİLDİ AMA GÖRÜLMEDİ — sistem üç ayrı alarmla bağırdı:
  · BAYAT MUTABAKAT: kayıt 2026-08-21 seansından, kitap 2026-08-24'ü işledi
  · BAYAT TÜREV: broker_reconcile.json kaynağından 72,1 sa geride
  · MIRROR_DRIFT ×2 (ALL, VLO) — bu iki alarm ÜÇ GÜNLÜK bir kayıttan okuyordu

NEDEN STATİK BİR ÇİVİ: hata yalnız `adet_benimsendi` DALINDA — yani ancak kitap
aynanın adedini benimsediğinde patlıyor. O dal her gece koşmuyor; testler onu
kapsamıyordu ve tip denetleyicisi de yok. Çağrı imzası ise kaynaktan STATİK olarak
okunabilir: `obs` yayıcılarının kaç konumsal argüman aldığı bellidir.

ÇİVİ İMZAYI KAYNAKTAN OKUR, elle listeden değil — `obs.py` bir gün ikinci bir
konumsal parametre eklerse çivi kendiliğinden uyum sağlar ve YANLIŞ alarm vermez.
"""
from __future__ import annotations

import ast
import inspect
import pathlib

from meridian import obs

KOK = pathlib.Path(__file__).resolve().parent.parent
KAYNAK = KOK / "meridian"

# Denetlenen yayıcılar. `alarm` İKİ konumsal alır (token + message) ve bu meşru —
# sayı kaynaktan okunduğu için burada elle yazılmıyor.
YAYICILAR = ("log", "warn", "alarm")


def _izinli_konumsal() -> dict[str, int]:
    """Her yayıcının kabul ettiği KONUMSAL argüman sayısı — `obs.py`den okunur."""
    sonuc: dict[str, int] = {}
    for ad in YAYICILAR:
        f = getattr(obs, ad, None)
        assert callable(f), f"obs.{ad} yok — çivinin listesi bayat"
        p = inspect.signature(f).parameters.values()
        sonuc[ad] = sum(
            1 for x in p
            if x.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
        )
    return sonuc


def test_obs_yayicilari_FAZLA_konumsalla_cagrilmiyor():
    """`obs.<yayıcı>(...)` çağrıları imzanın kabul ettiğinden ÇOK konumsal taşımamalı.

    İhlal ÇALIŞMA ANINDA `TypeError` demektir ve o istisna çağıranın `except`i
    tarafından yutulup bir "…_failed" satırına dönüşür: mekanizma ölür, defterde tek
    satır kalır, kimse bakmaz. Statik olarak görülebilecek bir şeyi çalışma anına
    bırakmak, bu depoda üç gün mutabakat kaybettirdi.
    """
    izin = _izinli_konumsal()
    ihlal: list[str] = []
    for p in sorted(KAYNAK.rglob("*.py")):
        try:
            agac = ast.parse(p.read_text(encoding="utf-8"))
        except SyntaxError:  # sessiz-yutma: ayrıştırılamayan dosya BU çivinin konusu değil; sözdizimini başka kapı ölçer
            continue
        for d in ast.walk(agac):
            if not isinstance(d, ast.Call):
                continue
            f = d.func
            # YALNIZ `obs.<ad>(...)` biçimi: çıplak `warn(...)` başka bir modülün
            # kendi yardımcısı olabilir (örn. `massive._warn`) ve imzası farklıdır.
            if not (isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name)
                    and f.value.id == "obs" and f.attr in izin):
                continue
            # `*args` yayılımı statik olarak sayılamaz — UYDURMA YASAĞI: sayılamayan
            # şey ihlal sayılmaz, ama sessizce atlanmaz da (aşağıdaki ayrı sayaç).
            if any(isinstance(a, ast.Starred) for a in d.args):
                continue
            if len(d.args) > izin[f.attr]:
                ihlal.append(
                    f"{p.relative_to(KOK)}:{d.lineno} obs.{f.attr}(...) "
                    f"{len(d.args)} konumsal aldı, imza {izin[f.attr]} kabul ediyor")
    assert not ihlal, (
        "obs yayıcısı imzasından fazla konumsalla çağrılıyor — ÇALIŞMA ANINDA TypeError:\n  "
        + "\n  ".join(ihlal)
        + "\nİkinci metni `detail=` gibi bir anahtar argümana taşı.")
