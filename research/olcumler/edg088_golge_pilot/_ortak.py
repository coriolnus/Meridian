"""_ortak.py — EDG-2026-088 gölge pilotunun İKİ ölçüm betiğinin (`pk2_gercek`, `pk3_selef`)
PAYLAŞTIĞI ÜÇ yardımcı: ölçüm-ön-şartı istisnası, `sys.path` kurulumu ve canlı `state/` kapısı.

NİÇİN AYRI BİR MODÜL (TEK-KAYNAK YASASI, tur-1 raporu §Kaygı 4 ve 9).
  1. CANLI STATE KAPISI İKİ KEZ YAZILMIŞTI. `pk3_selef.kos` kapıyı satır içinde taşıyordu
     (çağrılabilir bir yüzeyi yoktu), `pk2_gercek._state_izni` ise aynı üç satırın beyanlı
     ikinci kopyasıydı. Aynı gerçeğin iki kopyası sessizce ayrışır: birinde gevşetilen bir
     karşılaştırma ötekinde kalır ve "kapı var" iddiası yarısı için doğru olur. Kapı artık
     BURADA yaşar; iki betik de çağırır ve ayrışma çivisi (v472 D3) yardımcıyı yamayıp İKİ
     betiğin de yamayı gördüğünü ölçer.
  2. `meridian` İTHALİ CWD'YE BIRAKILMIŞTI. `meridian` bu makinede kurulu ve kurulu kopya ANA
     CHECKOUT'u gösteriyor (ölçüldü 2026-09-13): depo kökü `sys.path`e konmazsa bir
     worktree'den koşan betik sessizce BAŞKA bir ağacın motorunu ölçer ve bunu hiçbir yerde
     söylemez. `pk2_gercek` kendi bootstrap'ını taşıyordu, `pk3_selef` TAŞIMIYORDU — yani iki
     kardeş ölçüm ayağı aynı soruyu iki farklı ağaçta cevaplayabilirdi. `yolu_kur` o kapıyı
     ikisinde de aynı biçimde kurar ve çözülen kökü DÖNDÜRÜR, böylece sonuç künyesine yazılan
     `motor_yolu` bir iddia değil bir ÖLÇÜM olur.

BU MODÜL MOTORU İTHAL ETMEZ. `meridian`e dokunmaz, `state/` açmaz, dosya yazmaz — `yolu_kur`
çağrılmadan önce de ithal edilebilsin diye (tavuk-yumurta: yolu kuran şeyin kendisi yolda
olmalıdır, o yüzden iki betik de kendi dizinini `sys.path`e koyan üç satırlık bir bootstrap
taşır ve bu modülü ondan sonra ithal eder).
"""
from __future__ import annotations

import pathlib
import sys


class Blok(Exception):
    """Ölçüm ön şartı tutmadı — koşum BAŞLAMAZ (çıkış 1). Sessiz devam etmek, ölçülmemiş bir
    tabanı ölçülmüş gibi raporlamak olurdu.

    SINIF BURADA YAŞAR ki `pk2_gercek.Blok`, `pk3_selef.Blok` ve bu modülün attığı istisna AYNI
    NESNE olsun: üç ayrı sınıf olsaydı `except Blok` bir betikte yakalar, ötekinde geçirirdi.
    """


def sandbox_dizin(betik: str | pathlib.Path | None = None) -> pathlib.Path:
    """Ölçüm dizini (`research/olcumler/edg088_golge_pilot`) — BETİĞİN KENDİ konumundan."""
    return pathlib.Path(betik or __file__).resolve().parent


def depo_koku(betik: str | pathlib.Path | None = None) -> pathlib.Path:
    """Depo kökü — ölçüm dizininden YUKARI sayılarak. Mutlak yol GÖMÜLMEZ: gömülü bir kök,
    deponun başka bir checkout'unda (worktree, taze klon, cloud) sessizce yanlış ağacı gösterirdi.
    """
    return sandbox_dizin(betik).parents[2]


def yolu_kur(betik: str | pathlib.Path | None = None) -> tuple[str, str]:
    """Depo kökünü `sys.path[0]`a, ölçüm dizinini hemen ardına koyar. Dönüş: `(kök, ölçüm dizini)`.

    KÖK NEDEN BAŞTA. `meridian` paketi bu makinede KURULU ve kurulu kopya ana checkout'u
    gösteriyor; kök yolda önce gelmezse `import meridian` kurulu kopyaya düşer ve bir
    worktree'de koşan ölçüm BAŞKA bir ağacın motorunu ölçer. Ölçüm dizini de gerekir: iki betik
    birbirini ve `sayim`ı ithal eder (`research/` bir paket DEĞİLDİR — ölçümler birbirinden
    yalıtık dizinlerdir, o yüzden ithal yolla yapılır).

    Zaten yoldaysa ÖNE ALINIR (yalnız `not in` bakmak yetmez: başka bir ithal yolu sonradan
    kökün önüne bir dizin koyabilir ve kapı sessizce açılırdı).
    """
    kok, sandbox = str(depo_koku(betik)), str(sandbox_dizin(betik))
    for yol in (sandbox, kok):          # ters sırada eklenir → son eklenen (kök) [0]'da kalır
        while yol in sys.path:
            sys.path.remove(yol)
        sys.path.insert(0, yol)
    return kok, sandbox


def state_izni(state_dizin: str | pathlib.Path,
               kok: str | pathlib.Path | None = None) -> pathlib.Path:
    """Geçici state kökü deponun `state/` ağacının ALTINDA olamaz — TEK KAYNAK.

    Canlı deftere yazan bir ölçüm, ölçtüğü sistemi değiştirirdi (vaka sınıfı: ajanın pytest dışı
    koşumu canlı `state/`e yazıyor, 2026-08-30 ×3). Kapı GEVŞETİLEMEZ ve tek yerde yaşar; iki
    ölçüm betiği de bunu çağırır (`pk2_gercek._state_izni`, `pk3_selef.kos`).
    """
    state_dizin = pathlib.Path(state_dizin)
    canli = pathlib.Path(kok) if kok is not None else depo_koku()
    canli = canli / "state"
    coz = state_dizin.resolve()
    if coz == canli or canli in coz.parents:
        raise Blok(f"--state-dizin deponun state/ ağacının altında: {state_dizin} — canlı "
                   "deftere yazım yasak, geçici bir dizin ver")
    return state_dizin
