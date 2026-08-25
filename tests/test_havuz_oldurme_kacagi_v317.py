"""v317 — HAVUZ ÖLDÜRME KAÇAĞI: `_havuzu_oldur` HİÇBİR İŞÇİYİ ÖLDÜRMÜYOR.

ÖLÇÜLEN CANLI OLGU (A1, 2026-08-25): havuz 18:26:28'de iki işçi açtı, 18:56:29'da
`arama_havuzu_zaman_asimi biten=0 bekleyen=10` bastı — yani `_havuzu_oldur` KOŞTU. 19:43'te,
kırk yedi dakika sonra, iki işçi de HÂLÂ AYAKTAYDI: 487337 `R` durumunda %99,8 CPU (01:16:56
CPU-zamanı ve artıyor), 487340 `S` durumunda `wchan=anon_pipe_read` — bir daha ASLA
beslenmeyecek çağrı kuyruğunda donmuş, 224 MB tutuyor.

KÖK NEDEN (kaynakta okunur, aşağıda ÖLÇÜLÜR): `_havuzu_oldur` önce
`ex.shutdown(wait=False, cancel_futures=True)` çağırır. CPython 3.12'de `shutdown()`
gövdesinin SONUNDA `self._processes = None` vardır ve bu satır `wait` bayrağına BAKMAZ
(/usr/lib/python3.12/concurrent/futures/process.py). Dolayısıyla bir sonraki satırdaki
`getattr(ex, "_processes", {})` varsayılan `{}`e DÜŞMEZ — öznitelik VARDIR, değeri `None`dır —
ve `None.values()` `AttributeError` fırlatır. O istisnayı hemen altındaki `except Exception: pass`
yutar. `terminate()` HİÇ ÇAĞRILMAZ.

Sessiz-yutmanın kendi gerekçesi bunu "sürüm değişiminde olabilecek" bir uç durum sayıyor
("erişilemezse (sürüm değişimi) kalan tek bedel nice(15)'li yetim bir süreçtir"). Ölçüm bunun
tersini söylüyor: uç durum DEĞİL, TEK durum — her çağrıda olur.

KAÇAĞIN ÖMRÜ SINIRLI AMA UZUN (aynı gün ölçüldü, ilk okumam bunu FAZLA söylüyordu): 20:05'te iki
süreç de gitmişti, yani terk edilişten sonra ~47-69 dk yaşıyorlar — `terminate()` koştuğu için
değil, ellerindeki walk-forward bitip terk edilmiş kuyruk yıkıldığı için. Bedel kalıcı sızıntı
DEĞİL, atalet başına ~1 saatlik tam çekirdek + ~450 MB; üstelik tam da sıralı yedek yolun CPU
istediği pencerede.

ÇİVİ: davranışsal — "atalete çarpan havuzun işçileri ölmüş OLMALI". Ölçüm aracına değil
gözlenen olguya bağlıdır; düzeltme `_processes`i shutdown'dan ÖNCE yakalayabilir, `os.kill`
kullanabilir, başka bir yol tutabilir — çivi hepsini kabul eder, hiçbirini şart koşmaz.
"""
from __future__ import annotations
import multiprocessing as mp
import os
import time
from concurrent.futures import ProcessPoolExecutor

import pytest

from meridian import reflect


def _canli(pid: int) -> bool:
    """Süreç hâlâ var mı — `os.kill(pid, 0)` (sinyal göndermez, yalnız varlığı sorar)."""
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _isci_pidleri(ex, n: int, sure: float = 20.0) -> list[int]:
    """İşçiler GERÇEKTEN ayağa kalkana kadar bekler ve PID'lerini döndürür.

    DÜZENEK ÇİVİSİ: spawn yavaştır; işçiler hiç doğmadan `_havuzu_oldur` çağrılırsa çekirdek
    çivi HİÇBİR ŞEY ÖLÇMEDEN yeşil geçerdi ("ölecek süreç yoktu, demek ki hepsi öldü").
    Burada beklemek o sessiz-yeşili kapatır: işçiler doğmazsa test KURULUMDA düşer."""
    son = time.time() + sure
    while time.time() < son:
        procs = getattr(ex, "_processes", None) or {}
        pidler = [p.pid for p in procs.values() if p.pid and _canli(p.pid)]
        if len(pidler) >= n:
            return pidler
        time.sleep(0.05)
    pytest.fail(f"düzenek kurulamadı: {sure:.0f} sn'de {n} canlı işçi doğmadı "
                f"(çivi ölçmeden yeşil geçemesin diye kurulum burada düşer)")



def test_havuzu_oldur_iscileri_gercekten_oldurur():
    """Atalete çarpmış havuzun işçileri `_havuzu_oldur` sonrası YAŞAMAMALI.

    Canlıdaki iki işçi kırk yedi dakika sonra hâlâ ayaktaydı; burada on saniye yeter."""
    ctx = mp.get_context("spawn")
    ex = ProcessPoolExecutor(max_workers=2, mp_context=ctx)
    # `time.sleep` bilerek: kilitlenmiş bir işçiyi CPU yakmadan taklit eder (canlıdaki 487340
    # da tam olarak böyleydi — uyuyor, ölmüyor). Uzun süre = kendiliğinden çıkmaz.
    for _ in range(4):
        ex.submit(time.sleep, 600)
    pidler = _isci_pidleri(ex, 2)
    assert all(_canli(p) for p in pidler), "kurulum: öldürmeden ÖNCE işçiler canlı olmalıydı"

    reflect._havuzu_oldur(ex)

    son = time.time() + 10.0
    while time.time() < son and any(_canli(p) for p in pidler):
        time.sleep(0.1)
    kalan = [p for p in pidler if _canli(p)]
    for p in kalan:                       # test kaçak bırakmasın (çivinin kendi hijyeni)
        try:
            os.kill(p, 9)
        except OSError:
            pass
    assert not kalan, (
        f"_havuzu_oldur {len(pidler)} işçiden {len(kalan)}'ini öldüremedi ({kalan}) — "
        "canlıdaki kaçağın birebir aynısı: shutdown() `_processes`i None'a çeker, "
        "terminate döngüsü AttributeError'a düşer, `except Exception: pass` onu yutar")
