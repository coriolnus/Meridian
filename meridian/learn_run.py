"""learn_run.py — Hermes öğrenme (yansıma) bekleme döngüsünün AYRI SÜREÇ giriş noktası.

Ne yapar: `hermes_runtime` bekleme döngüsünü KENDİ sürecinde, ön planda koşturur. `meridian-learn`
systemd birimi bunu `ExecStart` olarak çağırır; süreç yaşadığı sürece döngü yaşar.

NEDEN VAR (ROADMAP §2-50, ölçüldü 2026-08-16):
Döngü bugüne kadar API sunucusunun İÇİNDE bir daemon ipliğiydi. Ölçüm: `py-spy` yığını
`hermes-standby → coordinate_descent_search → walk_forward → replay`; API süreci %93-100 CPU'da
kesintisiz, `/api/public/summary` 2,6-14,0 sn, yük ortalaması 1,14 (4 çekirdekte → biri dolu, ÜÇÜ
BOŞ). Sebep patoloji değil GIL: pano isteği backtest hesabının arkasına diziliyordu. Profilde
(25 sn, 50 Hz, 1392 örnek) hiçbir anormallik yok — yalnız normal bir backtest yükü, yanlış yerde.
İkinci belirti aynı köke bağlıydı: `reflect._havuz_tavani` işçi sayısını `cpu-2`ye kısıyor ve
gerekçesi kendi docstring'inde yazılı bir CANLI VAKA (2026-08-03: iki işçi panoyu boğdu, operatör
elle `renice` attı). Yani paralellik, süreç paylaşımı yüzünden kısılmıştı — tavan bir tasarım
tercihi değil, bu kusurun YAMASIYDI.

NE YAPMAZ: öğrenme mantığına DOKUNMAZ. Bu bir yerleşim değişikliğidir; arama sonuçları
`_PROBE_CACHE` anahtarlıdır ve determinizm sıraya değil anahtara dayanır (`_havuz_tavani`
docstring'inin beyanı) — sonuçlar bit-özdeş kalmalıdır.

EŞZAMANLILIK: ek koruma GEREKMEDİ, zaten vardı. `reflect._ProcessLock` (`state/.reflect.lock`
üzerinde BLOKSUZ `fcntl.flock`) tam bu senaryoyu adıyla öngörmüş: *"süreç-içi `_reflect_lock`
İKİNCİ BİR SÜRECİ durduramaz… kaybeden dürüst 'locked' cevabı alır."* API sürecindeki elle
tetikleme (`/api/hermes/reflect_now`) ile bu süreçteki bekleme döngüsü aynı kilidi paylaşır.

DURDURMA: systemd SIGTERM yollar → `_isaret` kancası `hermes_runtime.stop()` çağırır → döngü
bayrağını görür ve turunu bitirip çıkar. `TimeoutStopSec` dolmadan inemezse systemd SIGKILL atar;
o hâlde bile yarım kalan yansıma `_ProcessLock`u bırakır (flock süreç ölümünde çekirdek tarafından
serbest bırakılır) ve `SEARCH_PROGRESS` diskte `running=True` DONAR — bu bilinçli: `sprint`in
bayatlık yasası (`ARAMA_BAYAT_SAAT`) donmuş bayrağı zaten yakalar ve temizler.
"""

import os
import signal
import sys

from . import hermes_runtime, obs


def _isaret(imza, _cerceve) -> None:
    """SIGTERM/SIGINT kancası: döngüye dur bayrağını koyar. Süreci BURADA öldürmez — koşan bir
    yansımanın yarıda kesilmesi bir öğrenme turunu çöpe atar; döngü turunu bitirip kendisi iner."""
    obs.log("learn_run_durdurma_istegi", imza=int(imza),
             detail="dur bayrağı kondu — koşan yansıma turunu bitirip inecek")
    hermes_runtime.stop()


def main(argv: list[str] | None = None) -> int:
    """Döngüyü başlatır ve ipliğine katılır (süreç ön planda bloklar — systemd `Type=simple`).

    `start()` iplik açar; burada ona KATILIRIZ. Neden doğrudan `_run` çağırmıyoruz: `start()`
    bookkeeping yapıyor (`started_at`, `poll_seconds`, ilk `_persist`) ve pano o alanları okuyor —
    ikinci bir başlatma yolu açmak, deponun tekrar eden "aynı yasanın iki uygulaması" kusuru olurdu.
    """
    argv = sys.argv[1:] if argv is None else argv
    poll = int(os.environ.get("HERMES_POLL_SECONDS", "300"))
    if argv:                                   # tek konumsal argüman: poll saniyesi (test/elle koşum)
        poll = int(argv[0])
    for s in (signal.SIGTERM, signal.SIGINT):
        signal.signal(s, _isaret)
    obs.log("learn_run_basladi", poll_seconds=poll, pid=os.getpid(),
             detail="öğrenme bekleme döngüsü AYRI SÜREÇTE (ROADMAP §2-50)")
    sonuc = hermes_runtime.start(poll_seconds=poll)
    th = getattr(hermes_runtime, "_thread", None)
    if th is None:
        # Döngü açılamadı (örn. başka bir başlatma zaten var ya da kapalı). SESSİZ ÇIKMA:
        # systemd `Restart=always` ile bunu sonsuz döngüye çevirirdi ve sebebi görünmezdi.
        obs.warn("learn_run_baslatilamadi", sonuc=sonuc,
                 detail="hermes_runtime.start() iplik açmadı — birim çıkıyor, sebep sonuçta")
        return 1
    th.join()
    obs.log("learn_run_bitti", detail="bekleme döngüsü indi")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
