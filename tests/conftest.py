import hashlib
import importlib.util
import ipaddress
import os
import pathlib
import socket
import sys

import pandas as pd
import numpy as np
from pathlib import Path as _Path
import pytest

from meridian import config
# BETİK YÜKLEYİCİ — TEK UYGULAMA `ops/sasi_yukleyici.py`DEDİR (üretim tarafındaki on üç şasi
# çağrı yeri de oradan çağırır). Buradaki `betikten_modul_yukle` adı KORUNUR: on yedi test çağrı
# yeri onu kullanıyor. İkinci bir GÖVDE yazmak bu turun kovaladığı "iki kopya sessizce ayrışır"
# sınıfının ta kendisi olurdu. Gerekçenin tamamı o dosyanın başlığında.
from ops.sasi_yukleyici import kaynaktan_yukle as betikten_modul_yukle  # noqa: F401

# ---- MODÜL-DURUMU TABANI: BAŞLANGIÇ DEĞERİ İTHALDE FOTOĞRAFLANIR (2026-08-02) -------------------
# `_clear_module_caches` bugüne dek her sızıntıyı TEK TEK, elle yazılmış bir literalle sıfırlıyordu
# (`_fmp._HEALTH`). O desenin iki kusuru var ve ikisi de ölçüldü:
#   (a) LİTERAL SÜRÜKLENMESİ — sıfırlama değeri üretim modülünden KOPYALANMIŞ bir sözlüktür; üretim
#       tarafına bir alan eklenince kopya sessizce eksik kalır ve "sıfırlandı" sanılan durum aslında
#       yarım sıfırlanır. Taban artık modülün KENDİ literalinden okunur, kopyalanmaz.
#   (b) TEMBEL FOTOĞRAF TUZAĞI — fotoğrafı ilk `_clear_module_caches` çağrısında almak, o ana kadar
#       koşmuş sandbox'sız bir testin KİRLETTİĞİ durumu "başlangıç değeri" diye dondurabilirdi.
#       İthal anı tek güvenli an: conftest test modüllerinden ÖNCE yüklenir, hiçbir test koşmamıştır.
# İthal maliyeti ölçüldü: dört modül 0,14 sn ve hiçbirinin modül düzeyinde G/Ç yan etkisi yok.
import meridian.scheduler as _sch_mod
import meridian.adapters.constituents as _con_mod
import meridian.adapters.shortinterest as _si_mod
import meridian.adapters.fmp as _fmp_mod
# v215 SINIF-KAPAMASI (2026-08-09): iki modül daha. Marjinal ithal maliyeti ÖLÇÜLDÜ — dördünün
# 0,215 sn'sinin üstüne 0,0008 sn (ikisi de zaten `config`/`httpx` üzerinden dolaylı yüklüydü) ve
# ikisinin de modül düzeyinde G/Ç yan etkisi yok.
import meridian.adapters.alpaca as _alp_mod
import meridian.obs as _obs_mod
# v274 SEL-KESİMİ SAYACI (2026-08-23): api._REFRESH_SON — session_refresh kesimi (ip, yol) başına
# süreç-içi durum tutar. TestClient'ın IP'si her testte aynıdır ("testclient"), yani tazeleme
# olayını ölçen bir test pencereyi doldurunca SONRAKİ testin refresh olayı sessizce örneklenirdi —
# `auth._FAILS` vakasının birebir tekrarı. api zaten suite'in her yerinde yüklü; marjinal ithal
# maliyeti yok.
# TSK-106 (2026-09-02) SIZINTIYI BÜYÜTTÜ, KÜÇÜLTMEDİ: pencere artık 5 dk'lık örneklem değil UTC
# TAKVİM GÜNÜ ve "anında yazılan satır" yalnız çiftin İLK olayına ait. Yani kayıt sızarsa sonraki
# testin tazelemesi 5 dk sonra değil ERTESİ GÜNE kadar hiç yazılmaz — sızıntının sonucu
# "geç görünen satır"dan "hiç görünmeyen satır"a döndü. Bu sıfırlama artık daha da bağlayıcı.
import meridian.api as _api_mod
# v345 PIT ARŞİV SAYACI (2026-08-31, EDG-2026-062 Görev 3): `earnings_pit._SAYAC` bu turda ÜRETİM
# yolundan artmaya başladı — `backtest.replay` ve `cf_backfill.run` kazanç çapasını PIT arşivinden
# soruyor ve her çağrı üç kovadan birine düşüyor. Yani sızıntının sınıfı büyüdü: eskiden sayacı
# yalnız İKİ test dosyası (v344, v345) kendi autouse fikstürüyle kirletiyor ve kendi temizliyordu;
# artık `replay`/`run` çağıran HER test dosyası onu kirletir ve hiçbiri temizlemekle yükümlü
# değildir. Kalan sayaç bir sonraki dosyanın "kaç çağrı yapıldı" ölçümünü sessizce şişirir —
# `scheduler._state` ve `_fmp._HEALTH` vakalarının birebir aynısı, yalnız kaynağı üretim yolu.
# İthal maliyeti: modül `config` dışında hiçbir şeye bağlı değil ve modül düzeyinde G/Ç yapmaz
# (kendi başlığında beyanlı: `meridian.obs`a ULAŞMAZ).
# KAPSAMIN DÜRÜST SINIRI: bu mekanizma YALNIZ sözlükleri yerinde sıfırlar. `earnings_pit`in ufuk
# memosu (`_NESIL` int, `_UFUK_MEMO` dict|None) buraya GİREMEZ — ve girmesi de gerekmez: memo
# `_NESIL` ile anahtarlıdır, `_NESIL` yalnız `_CACHE` İÇERİĞİ değiştiğinde artar ve önbellek
# anahtarı (yol, mtime) olduğundan başka bir arşive geçen test yeniden yükleme tetikler → memo
# kendiliğinden düşer. Bayat memo okunabilmesi için iki AYRI arşivin aynı yolda aynı mtime'ı
# taşıması gerekirdi. Sızan tek durum sayaçtır ve kayıt onu kapatır.
import meridian.earnings_pit as _epit_mod

# (modül, öznitelik) — hepsi SÖZLÜK ve hepsi YERİNDE sıfırlanır (clear+update): yeni bir dict
# atamak, o sözlüğe başka modüllerden tutulan referansları koparır ve sıfırlama hiçbir şeye
# dokunmamış olurdu (`_fmp._HEALTH` dersi, 2026-07-26).
_MODUL_DURUMLARI = (
    # scheduler._state — KANITLI VAKA (2026-08-02): `test_regime_patch::test_scheduler_flag_
    # survives_publish_lag` kısmi seçimlerde (`-k "scheduler or regime or bottleneck"`) DÜŞÜYORDU.
    # Test yalnız `last_refetch_session`/`refetch_attempts` alanlarını kuruyor; komşu bir testten
    # devralınan `refetch_chase="2026-07-17"` merdiveni "son tarih doldu" dalına sokup bayrağı
    # yakıyordu. Tek başına yeşil, paket içinde kırmızı — yani ölçülen şey dedektör değil SIRA.
    # (Aynı ders `tests/test_ogrenme_otomasyonu_v136.py`de dosya-yerel bir fikstürle zaten yazılıydı;
    #  burada kaynağa taşındı, çünkü sonraki her dosya aynı fikstürü yeniden yazmak zorunda kalırdı.)
    (_sch_mod, "_state"),
    # fmp._HEALTH — 2026-07-26'da bulunmuş vaka; gerekçesi `_clear_module_caches` içinde yazılı.
    (_fmp_mod, "_HEALTH"),
    # constituents/_HEALTH ve shortinterest/_HEALTH — AYNI SINIF, KANIT DÜZEYİ FARKLI ve bu beyan
    # edilir: bir kırmızı test GÖZLENMEDİ. Ölçülen şey şu (geçici pytest eklentisiyle, 121 testlik
    # `-k "scheduler or regime or bottleneck"` seçiminde): ikisi de testler arası TAŞINIYOR
    # (constituents 68, shortinterest 119 testin başında tabandan farklıydı) ve okuyucuları
    # `fmp._HEALTH`inkiyle aynı sınıftan — `watchdog.production_report` (gövdesinde
    # `constituents.health()`) ve `/api/diagnostics`in sağlayıcı satırları: `api._saglayicilar`
    # (gövdesinde `shortinterest.health()`). Yani mekanizma birebir aynı; eksik olan
    # yalnız o mekanizmanın bugün ateşlediği bir testin bulunmuş olması.
    # ÇAPA SEMBOLE ÇEVRİLDİ (2026-08-24, v282 turu). Bu iki okuyucu önce SATIR NUMARASIYLA
    # çapalanmıştı ve ölçüldüğünde İKİSİ DE yanlış yeri gösteriyordu:
    #   çapa-mezar-taşı `watchdog.py:195` → `production_report`ın (bugün 404) değil başka bir docstring'in gövdesi
    #   çapa-mezar-taşı `api.py:1553`     → `/api/diagnostics`in değil `/api/today`in defter bloğu
    # İkisi de
    # `codelaw.stale_line_anchors`tan KAZARA geçiyordu — yasa "boş satır ya da yorum mu?" diye
    # sorar, "doğru şeyi mi gösteriyor?" diye değil. api.py'ye tek bir import satırı eklenince
    # ikincisi bir yorum satırına kayıp yasayı düşürdü; kusur o import değil, numara çapasının
    # kendisiydi (`codelaw.stale_line_anchors` docstring'i bu sınıfı adıyla anlatır).
    (_con_mod, "_HEALTH"),
    (_si_mod, "_HEALTH"),
    # alpaca._TRANSPORT — KANITLI VAKA, OTORİTER SUITE KIRMIZISI (2026-08-08). `tests/
    # test_onay_kapisi_v215.py` kontrol uçlarına POST atıyor; bir uç broker'a uzanınca adaptör
    # `_note(False, …)` ile taşıma kaydını `ok=False`a çekiyor ve kayıt DOSYA BİTİNCE de öyle
    # kalıyordu. `loop.reconcile_broker_state` `alpaca.orders`/`positions` YAMALANMIŞ OLSA BİLE
    # `alpaca.transport()["ok"]`i AYRICA sınar (`loop.mirror_submit_armed` ve `loop._alpaca_emir_penceresi`) → `test_regime_patch` ve
    # `test_robustness_patch` yalıtımda yeşil, v215'in ARDINDAN kırmızı. v215 kendi dosya-yerel
    # fikstürüyle kendi kirini geri alıyor (ve almalı — açan kapatır), ama SINIF orada kapanmaz:
    # taşıma kaydını kirleten bir SONRAKİ dosya aynı fikstürü yeniden yazmak zorunda kalırdı.
    # Kaynağa taşındı; `scheduler._state`in 2026-08-02'de izlediği yolun aynısı.
    (_alp_mod, "_TRANSPORT"),
    # obs._SUPPRESS_LOGGED — AYNI SINIF, KANIT DÜZEYİ FARKLI ve bu beyan edilir: bir kırmızı test
    # GÖZLENMEDİ (v215 ölçtü, `/api/halt` bisect'te temiz çıktı). Mekanizma yine de birebir aynı:
    # her alarm jeton başına 6 saatlik SUSTURMA penceresini bu sözlüğe yazar (`obs._emit` (olay yazım yolu)-152), yani
    # alarm ateşleyen bir test, bildirim davranışını ölçen bir SONRAKİ testi kendi kurmadığı bir
    # susturmayla karşılaştırır. `tests/test_alarm_delivery_v71.py:177` bunu bugün tek satırlık bir
    # `monkeypatch.setattr(obs, "_SUPPRESS_LOGGED", {})` ile kendi başına çözüyor — yani sızıntı
    # zaten BİLİNİYOR, yalnız tek yerden kapatılmamıştı.
    (_obs_mod, "_SUPPRESS_LOGGED"),
    # api._REFRESH_SON — session_refresh kesiminin gün defteri (gerekçe ithal bloğunda,
    # v274 + TSK-106).
    (_api_mod, "_REFRESH_SON"),
    # earnings_pit._SAYAC — PIT çapasının üç kovası (gerekçe ithal bloğunda, v345/Görev 3).
    # `sayac_sifirla` da YERİNDE günceller (yeni sözlük atamaz), yani bu mekanizmayla aynı
    # sözleşmededir: dışarıda tutulan referanslar kopmaz.
    (_epit_mod, "_SAYAC"),
)
_MODUL_DURUMU0 = {f"{m.__name__}.{a}": dict(getattr(m, a)) for m, a in _MODUL_DURUMLARI}

# ---- CANLI STATE SIZINTI BEKÇİSİ (2026-07-22) ---------------------------------------------------
# Bulgu: tekil test dosyaları canlı `state/`e dokunmuyordu ama TAM SUITE dokunuyordu — canlı nabzı
# (regime/equity/last_bar) siliyor, pano "rejim yok" gösteriyordu. Sebep sınıfı: bir test arka plan
# döngüsü/iş parçacığı başlatıyor ya da fikstür dışında yazıyor; sandbox söküldükten SONRA yazım
# canlı dizine düşüyor. Hiçbir test kırılmıyor, kimse fark etmiyor — bugünün baskın hata deseninin
# ta kendisi. Bekçi her testten sonra canlı dizini karşılaştırır ve sızıntıyı ADIYLA düşürür.
_LIVE = pathlib.Path(__file__).resolve().parent.parent / "state"

# ---- GİT-İZLİ SÖZLEŞME DOSYALARI: PARMAK İZİ mtime DEĞİL İÇERİK (2026-08-02) --------------------
# Bu iki dosya `state/` altında olmalarına rağmen GİT-İZLİDİR — `dagit.sh` [1b] adımının SSoT'si
# (c783442'den beri). CLAUDE.md'deki "state/ versiyonlanmaz" cümlesinin BİLİNÇLİ istisnasıdırlar.
# SONUCU ŞU: ana checkout'ta paralel bir oturumun git işlemi (checkout/stash/restore) onları
# REPO İÇERİĞİYLE BİREBİR yeniden yazar — dosya değişmez, mtime değişir. Bu katmanda mtime o hâlde
# SIZINTIYI değil GİT TRAFİĞİNİ ölçüyordu ve alarm nondeterministik oluyordu.
#   KANIT (2026-08-02): `test_regime_patch::test_scheduler_flag_survives_publish_lag` teardown'unda
#   `['bounds.yaml']` ile düştü. inode adliyesi: goal.yaml doğum 14:28:04; bounds.yaml doğum
#   18:01:21 + YERİNDE yeniden-yazım 18:06:34. Son içerik `.git/index` blob'uyla BİREBİR aynıydı
#   (yani yazan taraf repo→state restorasyonuydu, bir test değil). Testler ayrıca AKLANDI: iki
#   enstrümanlı tam tekrar koşumu (tüm Python alt süreçlerine sitecustomize audit-hook + 0,2 sn
#   mtime poller; worktree + ana checkout; 84 test ×2 yeşil) canlı bounds.yaml'a TEK yazım denemesi
#   göstermedi. Yanlış alarmın bedeli, doğru alarmın bedelinden büyüktür: susturulan bir bekçi.
# GERÇEK-KAYNAK `git ls-files state/`TİR ama conftest git koşturamaz (ve koşsa her teste bir alt
# süreç eklerdi) → bu küme ELLE tutulur: `state/` altına ÜÇÜNCÜ bir dosya versiyona girerse buraya
# elle eklenmelidir, yoksa aynı yanlış alarm o dosyada geri döner.
_IZLI_SOZLESME_DOSYALARI = ("bounds.yaml", "goal.yaml")


def _izli_icerik_ozeti(yol: str) -> str | None:
    """İzli sözleşme dosyasının sha256'sı; okunamazsa None (çağıran mtime'a geri düşer).

    ÖLÇÜM BÜTÇESİ: iki dosya × ~30 KB, test başına iki parmak izi → ~120 KB/test okuma. Komşu
    yorumdaki ölçüm (650 dosyada os.scandir ~4-5 ms) yanında pratik olarak görünmez; bunun
    karşılığında kapatılan şey, katmanın TAMAMINI susturmaya götüren bir yanlış-alarm sınıfıdır."""
    try:
        with open(yol, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except OSError:  # sessiz-yutma: bekçinin KENDİ G/Ç'si düştü (dosya git tarafından o an değiştiriliyor olabilir) — çağıran mtime_ns'e geri düşer, yani dedektör kapanmaz sadece eski hassasiyetine iner
        return None


def _live_fingerprint() -> dict:
    # ALT DİZİNLER DE TARANIR (2026-07-29, C2 turu): eski glob("*.json*") yalnız köke bakıyordu —
    # state/bars_intraday/ altına düşen 16 MB'lık sızıntı bu katmana da görünmezdi. os.scandir
    # yığını ölçüldü: 650 dosyada ~4-5ms (rglob ~50ms); katman zaten yalnız uygulama kapalıyken
    # koşar, suite başına maliyet kabul edilebilir. Anahtar `_LIVE`e GÖRELİ yoldur: iki farklı
    # alt dizindeki aynı adlı dosya (ör. bars/AAPL.json ve bars_intraday/AAPL.json) `p.name` ile
    # birbirini eziyordu — sızıntı sayısı eksik, adı yanıltıcı olurdu.
    import os as _os
    out: dict = {}
    stack = [str(_LIVE)]
    base = str(_LIVE) + _os.sep
    while stack:
        d = stack.pop()
        try:
            with _os.scandir(d) as it:
                for e in it:
                    if e.is_dir(follow_symlinks=False):
                        stack.append(e.path)
                    elif e.is_file(follow_symlinks=False):
                        rel = e.path.removeprefix(base)
                        # MUAFİYET — YALNIZ `.locks/*.lock` (2026-08-09): `store.file_lock` süreçler
                        # arası flock için `state/.locks/<ad>.lock` dosyasını `os.open` ile açar;
                        # yazım kancaları `builtins.open`/`store.*`/`Path.write_*`i sarar ama `os.open`ı
                        # SARMAZ (doğru — kilit veri değil), yani katman 1 kilidi hiç görmez. STATE
                        # DIŞINA yazan bir sandbox testi (sprint history'si mutlak yolla geçer,
                        # config.dump_yaml fallback'i) kilit adını CANLI `_state()/.locks`e düşürür;
                        # bu GEÇİCİ bir flock artefaktıdır, kalıcı state DEĞİLDİR ve kancalara
                        # görünmemesi BEKLENEN davranıştır. SINIR DAR: yalnız `.locks/` altındaki
                        # `.lock` dosyaları elenir — gerçek CANLI state değişimi hâlâ yakalanır.
                        if rel.startswith(".locks" + _os.sep) and rel.endswith(".lock"):
                            continue
                        # İZLİ İKİLİ İÇERİKLE, GERİ KALAN HER ŞEY mtime İLE (gerekçe yukarıda).
                        # Karşılaştırma GÖRELİ YOL üzerindedir: yalnız KÖKteki bounds/goal.yaml
                        # muaftır — bir alt dizinde aynı adı taşıyan dosya git-izli değildir ve
                        # dedektör orada daraltılmaz.
                        ozet = _izli_icerik_ozeti(e.path) if rel in _IZLI_SOZLESME_DOSYALARI else None
                        out[rel] = (ozet if ozet is not None
                                    else e.stat(follow_symlinks=False).st_mtime_ns)
        except OSError:  # sessiz-yutma: canlı dizin yoksa (taze klon/CI) karşılaştıracak bir şey de yoktur
            pass
    return out


def _app_is_running() -> bool:
    """Canlı Meridian süreci var mı? Artık bekçiyi KAPATMAZ — yalnız İKİNCİ katmanı sınırlar."""
    import subprocess
    try:
        r = subprocess.run(["pgrep", "-f", "uvicorn meridian.api"],
                           capture_output=True, text=True, timeout=5)
        return bool(r.stdout.strip())
    except (OSError, subprocess.SubprocessError):  # sessiz-yutma: pgrep yoksa/başarısızsa 'uygulama koşmuyor' varsayılır — bekçi AÇIK kalır, yani muhafazakâr taraf
        return False


_APP_RUNNING = _app_is_running()

# ---- NEDEN İKİ KATMAN (2026-07-22) --------------------------------------------------------------
# Bekçi eskiden uygulama koşarken TAMAMEN kapanıyordu, çünkü mtime karşılaştırması "bu testin
# yazımı" ile "koşan uygulamanın yazımı"nı ayırt edemiyordu. Ama operatörün test koşturmasının en
# olası olduğu an, uygulamanın açık olduğu andır — yani bekçi tam da en çok gerektiği zaman kapalıydı.
#
# BEDELİ ÖLÇÜLDÜ: `test_url_is_a_resolvable_wss_paper_url` endpoint'i şemasız bir değere yamalayıp
# `_url()` çağırıyordu ama `sandbox_state` almıyordu; `obs.warn` CANLI events.jsonl'a düşüyordu.
# Defterde günde 32 `mirror_stream_bad_base` biriktir ve bir üretim arızası gibi okundu — saatler
# yanlış yerde arandı. Testin canlı deftere yazması, operatöre sunulan kanıtı kirletmektir.
#
# Çözüm ayrım noktasını değiştirmek: mtime "kim yazdı"yı bilemez, ama YAZIM ÇAĞRISINI bu süreçte
# yakalarsak fail zaten bizimdir — uygulamanın eşzamanlı yazımları hiç görünmez.
#   Katman 1 (HER ZAMAN AÇIK): süreç-içi yazım kancaları. Uygulama açıkken de çalışır.
#   Katman 2 (yalnız uygulama KAPALIYKEN): eski mtime parmak izi — kancaların göremediği yazımları
#            yakalar (örn. testin başlattığı ALT SÜREÇ ya da fikstür söküldükten sonra yazan iplik).
# İkisi birbirinin yerine değil, tamamlayıcısıdır.
_LIVE_ROOT = _LIVE.resolve()


class _CanliYazimKaydi:
    """Bu SÜREÇTEKİ yazımlardan canlı dizine düşenleri adıyla toplar.

    KAYIT GÖRELİ YOLDUR, `p.name` DEĞİL (2026-07-29): katman 1 artık alt dizinlere yazan ham
    `open()` çağrılarını da görüyor (bkz. 4. blok), ama sızıntı `2026-07-29.jsonl (open)` diye
    raporlanırsa operatör hangi dizine düşüldüğünü BİLEMEZ — `bars/` ile `bars_intraday/` aynı
    ada sahip dosyalar barındırır. Bekçinin değeri sızıntıyı ADIYLA düşürmesindeyse, ad tam olmalı."""

    def __init__(self):
        self.hits: list[str] = []

    def note(self, path, nasil: str) -> None:
        try:
            # YOL HER ZAMAN ÇÖZÜLÜR (2026-07-29): eskiden yalnız GÖRELİ yollar `resolve()` ediliyordu,
            # absolute yollar olduğu gibi karşılaştırılıyordu — ama `_LIVE_ROOT` ÇÖZÜLMÜŞ bir yoldur.
            # Normalize edilmemiş bir absolute yol `relative_to`dan ValueError alır ve sızıntı SESSİZCE
            # elenirdi: bekçiyi atlatmanın ÜÇÜNCÜ yolu. Ölçüldü — tmp'de kurulan sahte canlı dizine
            # yazan ham `open()` yalnız bu yüzden kaydedilmedi (/var→/private/var bağı).
            # VE BU DEPODA GERÇEK BİR VAKA: `~/Documents/Claude/AI-Trading` bu deponun kendisine giden
            # bir SEMBOLİK BAĞ (test_kimlik_v114 satır ~218'de belgeli). O yol üzerinden gelen bir
            # yazım canlı state'e düşer ama çözülmemiş hâliyle canlı köke göreli DEĞİLDİR — bekçi
            # kördü. Sızıntıyı ADIYLA düşürmesi beklenen bir bekçinin sessiz kaldığı yer, tam olarak
            # bu turda kapatılan delik sınıfının kendisidir.
            # Bedeli çözülmüş yol başına bir realpath; `note` yalnız yazım boğazlarından çağrılır.
            p = pathlib.Path(path).resolve()
            rel = p.relative_to(_LIVE_ROOT)    # canlı dizinin DIŞINDAYSA ValueError → sessizce çık
        except (ValueError, OSError, TypeError):  # sessiz-yutma: yol canlı dizinde değil ya da çözümlenemedi — bekçinin ilgi alanı dışı, testi düşürmez
            return
        kayit = f"{rel} ({nasil})"
        if kayit not in self.hits:
            self.hits.append(kayit)


# ---- ÜRETİM GLOBALLERİ SIZINTI BEKÇİSİ (2026-07-22) ---------------------------------------------
# Bulgu: `tests/test_cf_backfill_v14.py` `backtest.SECTORS.setdefault(...)` ile ÜRETİM sözlüğüne
# yazıyor ve geri almıyordu. SECTORS modül düzeyinde, değiştirilebilir ve `loop.SECTORS` ile AYNI
# nesne — yani sektör-tavanı kapısının okuduğu harita. Alfabetik sırada zehirleme SONRA geldiği için
# hiç görünmedi; suite ters sırada koşturulunca `test_b3_sector_map_covers_the_universe_exactly`
# düştü. Sıra bağımlı bir suite, geçtiğinde bile bir şey KANITLAMAZ: yarın bir dosya adı değişince
# yeşil kalır ya da kırmızıya döner, ikisi de aynı koda karşılık gelir.
_MUTABLE_GLOBALS = (("meridian.backtest", "SECTORS"),)


def _globals_snapshot() -> dict:
    import importlib
    snap = {}
    for mod, attr in _MUTABLE_GLOBALS:
        try:
            obj = getattr(importlib.import_module(mod), attr)
            snap[f"{mod}.{attr}"] = dict(obj) if isinstance(obj, dict) else set(obj)
        except Exception:  # sessiz-yutma: modül yoksa/okunamıyorsa karşılaştıracak bir şey de yoktur — bekçi sessizce devre dışı, testi düşürmez
            pass
    return snap


@pytest.fixture(autouse=True)
def _no_production_global_mutation():
    """Bir test üretim modülündeki değiştirilebilir bir globali kirletirse ADIYLA düşsün.
    `monkeypatch.setitem/setattr` kullanan testler etkilenmez (fikstür sökümünde geri alınır)."""
    before = _globals_snapshot()
    yield
    after = _globals_snapshot()
    for key, prev in before.items():
        now = after.get(key)
        if now != prev:
            eklenen = sorted(set(now) - set(prev))
            silinen = sorted(set(prev) - set(now))
            pytest.fail(f"ÜRETİM globali kirletildi: {key} (eklenen={eklenen[:8]} silinen={silinen[:8]}) "
                        f"— `monkeypatch.setitem/setattr` kullan; kalıcı yazım sonraki testleri "
                        f"sessizce etkiler ve suite'i SIRA BAĞIMLI yapar")


def _kancalari_kur(kayit) -> list:
    """Yazım BOĞAZLARINI sarar; geri alma listesi döndürür. Hepsi ÇAĞRI ANINDA yolu çözer:
    `sandbox_state` config.STATE'i tmp'ye çevirdiği için sandbox'lı testlerin yazımları canlı
    dizine düşmez ve hiç kaydedilmez.

    NEDEN `monkeypatch` FİKSTÜRÜ DEĞİL (2026-07-22): bekçi paylaşılan monkeypatch'e bağlanınca
    fikstür SÖKÜM SIRASINA giriyor ve komşu bekçiyi bozdu — `_no_production_global_mutation`,
    testin `monkeypatch.setitem` ile yaptığı geçici SECTORS değişikliği HENÜZ GERİ ALINMADAN
    ölçüm yapıp doğru testleri suçladı. Bir bekçinin ölçtüğü şeyi kendi varlığı değiştiriyorsa,
    o bekçi kanıt değil gürültü üretir. Kendi kancalarını kendi kurup kendi söker."""
    import os as _os
    from meridian import store
    geri: list = []

    # 1) store ilkelleri — kodun yazım sözleşmesi. `append_jsonl` ÖZELLİKLE önemli: obs.warn
    #    buradan geçer, yani defter kirlenmesinin tam yolu (canlıda yaşanan sızıntı buydu).
    for ad in ("write_json", "write_jsonl", "append_jsonl"):
        _asil = getattr(store, ad)

        def _sar(name, *a, _asil=_asil, _ad=ad, **k):
            try:
                yol = pathlib.Path(name) if _os.path.isabs(str(name)) else store._state() / str(name)
                kayit.note(yol, f"store.{_ad}")
            except Exception:  # sessiz-yutma: kancanın kendi muhasebesi düştü — ASIL yazım her hâlükârda yapılır, bekçi testi bozamaz
                pass
            return _asil(name, *a, **k)

        setattr(store, ad, _sar)
        geri.append(lambda ad=ad, _asil=_asil: setattr(store, ad, _asil))

    # 2) os.replace — ATOMİK yazarların ortak son adımı (store, config.yaml, secrets.json).
    #    mkstemp+replace deseni store dışında da kullanıldığı için boğaz burada yakalanır.
    _asil_replace = _os.replace

    def _replace(src, dst, *a, **k):
        kayit.note(dst, "os.replace")
        return _asil_replace(src, dst, *a, **k)

    _os.replace = _replace
    geri.append(lambda: setattr(_os, "replace", _asil_replace))

    # 3) Path.write_text/write_bytes/touch — store'u atlayan doğrudan yazarlar (memory.py lessons,
    #    health.py HALT bayrakları, run.py scoreboard). HALT bayrağı özellikle kritik: sandbox'sız
    #    bir test canlı sistemi DURDURABİLİR ve eski bekçi bunu uygulama açıkken hiç görmezdi.
    for ad in ("write_text", "write_bytes", "touch"):
        _asil_m = getattr(pathlib.Path, ad)

        def _sar_m(self, *a, _asil_m=_asil_m, _ad=ad, **k):
            kayit.note(self, f"Path.{_ad}")
            return _asil_m(self, *a, **k)

        setattr(pathlib.Path, ad, _sar_m)
        geri.append(lambda ad=ad, _asil_m=_asil_m: setattr(pathlib.Path, ad, _asil_m))

    # 4) builtins.open / io.open — boğazları ATLAYAN ham yazarlar (2026-07-29, C2 turu bulgusu):
    #    `barsarchive` dayanıklılık için `open()`+`fsync` kullanır; bir testin `monkeypatch.undo()`
    #    kazası paylaşılan fikstürün TÜM yamalarını söktü ve arşivci canlı `state/bars_intraday/`
    #    altına 16 MB yazdı — yukarıdaki üç boğazın HİÇBİRİ görmedi. Bu blok o sınıfı kapatır.
    #    PERFORMANS: derin yol çözümü (resolve+relative_to) yalnız write-modlu ('w'/'a'/'x'/'+')
    #    VE str'inde 'state' geçen açılışlarda; okuma açılışları tek küme kesişimiyle geçer.
    #    Python 3.12'de `io.open` builtins.open'ın TA KENDİSİDİR ve `Path.open`/`Path.write_text`
    #    modül-global `io.open`u çağırır — iki adı da AYNI sarmalayıcıya bağla, ikisini de geri al.
    #    int fd'ler ('os.fdopen') str'inde 'state' içermez, doğal elenir.
    import builtins as _bi
    import io as _io
    _asil_open = _bi.open

    def _open_sar(file, mode="r", *a, **k):
        try:
            if isinstance(mode, str) and (set(mode) & set("wax+")) and "state" in str(file):
                kayit.note(file, "open")
        except Exception:  # sessiz-yutma: kancanın kendi muhasebesi düştü — ASIL açılış her hâlükârda yapılır, bekçi testi bozamaz
            pass
        return _asil_open(file, mode, *a, **k)

    _bi.open = _open_sar
    _io.open = _open_sar
    geri.append(lambda: (setattr(_bi, "open", _asil_open), setattr(_io, "open", _asil_open)))

    return geri


@pytest.fixture(autouse=True)
def _no_live_state_writes(request):
    """KATMAN 1 her zaman açık; KATMAN 2 yalnız uygulama kapalıyken anlamlı (yukarıdaki gerekçe)."""
    # CANLI-YOL DAMGA MUAFİYETİ (2026-08-23, v21 vakası): `yerel_donmus_defter` damgası gerçek
    # state'e karşı İLK storage.active() çağrısında tembel ateşler ve obs yazımı GERÇEK
    # events.jsonl'a düşer — tam bu bekçinin yasakladığı sınıf. Damganın sahibi üretim
    # süreçleridir, testler değil; gerçek db-yolu önbelleğe önden eklenir. Kum-havuzu damgaları
    # ETKİLENMEZ (anahtar yol-bazlı; v268 kendi set'ini kurarak sınar).
    from meridian import config as _cfg, storage as _st
    _st._YEREL_OLCULDU.add(str(_Path(_cfg.STATE) / "meridian.db"))
    kayit = _CanliYazimKaydi()
    geri = _kancalari_kur(kayit)
    before = None if _APP_RUNNING else _live_fingerprint()
    try:
        yield
    finally:
        for f in reversed(geri):        # kancalar HER hâlükârda sökülür — test düşse de, hata atsa da
            f()
    if kayit.hits:
        pytest.fail(f"CANLI state'e YAZILDI ({request.node.name}): {sorted(kayit.hits)} — testler "
                    f"yalnız `sandbox_state` içinde yazabilir. Canlı defter operatöre sunulan "
                    f"kanıttır; test artefaktı oraya düşerse üretim arızası gibi okunur.")
    if before is not None:
        after = _live_fingerprint()
        changed = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
        if changed:
            # TEŞHİS İPUCU: izli dosyalarda mtime yenilemeleri artık ELENİYOR (bkz.
            # `_IZLI_SOZLESME_DOSYALARI`). Bu alarm o dosyalardan birini gösteriyorsa geriye iki
            # olasılık kalır ve operatör hangisini aradığını bilmelidir; ipucu olmadan bu turda
            # kapatılan yanlış-alarm sınıfı yeniden aranırdı.
            izli = [k for k in changed if k in _IZLI_SOZLESME_DOSYALARI]
            ipucu = (f" [{izli} GİT-İZLİdir (dagit [1b] SSoT); içerik-aynı mtime yenilemeleri artık "
                     f"elenmektedir — yani bu alarm İÇERİK farkı ya da DOĞUM demektir. Doğumu "
                     f"paralel bir oturumun git işlemi (checkout/stash/restore) de üretebilir: "
                     f"önce `git status`/`git diff` ile bak, sonra testi suçla]" if izli else "")
            pytest.fail(f"CANLI state DEĞİŞTİ ({request.node.name}): {changed}{ipucu} — yazım kancalara "
                        f"görünmedi, yani ALT SÜREÇ ya da fikstür söküldükten sonra yazan bir iplik "
                        f"var. Bu sınıf, uygulama açıkken taranamaz — worker'ı `./ops/stop-worker.sh` "
                        f"ile durdur (çıplak pkill probe havuzunu yetim bırakır; 2026-07-26 vakası) "
                        f"ve keepalive diriltmesin diye `state/keepalive.pid` dosyasını sil.")


# ---- HERMES ARKA PLAN İPLİĞİ SIZINTISI (2026-07-29) ---------------------------------------------
# Yukarıdaki KATMAN 2 uyarısı "fikstür söküldükten sonra yazan bir iplik" diyordu ve tam olarak bu
# oluyordu. Danışma katmanı iki yerde AYRIK bir daemon thread'i başlatır:
#   loop.daily_cycle  → hermes.review_candidates_async()  (iplik: "candidate-review")
#   /api/...          → hermes.backfill_opinions_async()  (iplik: "opinion-backfill")
# İkisi de `hermes._agent_call`e iner: GERÇEK bir alt süreç (yerel hermes CLI) çalıştırır ve
# `obs.log("agent_call", ...)` ile deftere yazar. Yazım anında hangi dizine düşeceğini
# `config.STATE` belirler — ve `sandbox_state` monkeypatch'i test BİTİNCE geri alınır. Yani iplik
# testten uzun yaşadığında yazımı CANLI `state/events.jsonl`a düşer: operatörün defterinde, hiçbir
# testi kırmadan, gerçek bir `agent_call` kaydı gibi görünen bir test artefaktı. Sıra bağımlıdır
# (ipliğin bitiş anı ile fikstür sökümü yarışır), yani "bugün geçti" hiçbir şey kanıtlamaz.
#
# İKİ KATLI ÇÖZÜM — önlemek ve yakalamak aynı şey değildir:
#   ÖNLE : iki spawner varsayılan olarak NO-OP'a çevrilir. Hiçbir test bu ipliği İSTEMİYORDU;
#          danışma katmanı kapıyı değiştirmez, dolayısıyla hiçbir testin beklentisi ona bağlı
#          değil (depoda `*_async` çağrısını doğrulayan tek bir test yok — arandı). Çağrılar
#          KAYDEDİLİR: bir test "danışma katmanı tetiklendi mi" diye sormak isterse
#          `hermes_async_cagrilari` fikstürüyle sorabilir — yeteneği kaldırmıyoruz, ipliği.
#   YAKALA: teardown'da hâlâ yaşayan bir hermes ipliği varsa test ADIYLA düşer. Yarın eklenecek
#          ÜÇÜNCÜ bir async yol bu muhafazadan sessizce geçemez; önlem listesi eskir, dedektör
#          eskimez.
_HERMES_IPLIK_ADLARI = ("candidate-review", "opinion-backfill",
                        "hermes-standby", "hermes-reflect-now")


class _SahteIplik:
    """`review_candidates_async` çağırana Thread DÖNDÜRÜR ve sözleşmesi 'gerekirse join et'tir.
    No-op yerine None dönmek o sözleşmeyi kırardı (`AttributeError: 'NoneType' has no 'join'`),
    yani testi gerçek bir kusur yokken düşürürdü. Zaten bitmiş bir iplik gibi davranır."""

    name = "hermes-async-noop"

    def join(self, timeout=None):
        return None

    def is_alive(self):
        return False


@pytest.fixture(autouse=True)
def hermes_async_cagrilari(request):
    """Hermes danışma ipliklerini VARSAYILAN olarak başlatma; çağrıları kaydet; sızıntıyı yakala.

    Gerçek ipliği isteyen test `@pytest.mark.hermes_gercek_iplik` işaretini koyar ve ipliği KENDİ
    join etmekle yükümlü olur (aksi halde aşağıdaki dedektör onu adıyla düşürür).

    KENDİ YAMASINI KENDİ KURAR/SÖKER — `monkeypatch` FİKSTÜRÜNÜ PAYLAŞMAZ: bu dosyada aynı ders
    iki kez yazılı (bkz. `_kancalari_kur` ve `_hotstate_off_by_default` gerekçeleri). Paylaşılan
    monkeypatch'e bağlanan bir bekçi, fikstür SÖKÜM SIRASINA girer; komşu bekçi (`_no_production_
    global_mutation`) ölçümünü henüz geri alınmamış bir yamanın üstünde yapıp MASUM bir testi
    suçlamıştı. Bir bekçinin ölçtüğü şeyi kendi varlığı değiştiriyorsa, o bekçi kanıt değil
    gürültü üretir."""
    import meridian.hermes as _hm
    cagrilar: list[tuple[str, tuple, dict]] = []
    geri: list = []
    if "hermes_gercek_iplik" not in request.keywords:
        for ad in ("review_candidates_async", "backfill_opinions_async"):
            _asil = getattr(_hm, ad)
            setattr(_hm, ad,
                    lambda *a, _ad=ad, **k: (cagrilar.append((_ad, a, k)), _SahteIplik())[1])
            geri.append(lambda ad=ad, _asil=_asil: setattr(_hm, ad, _asil))
    try:
        yield cagrilar
    finally:
        for f in reversed(geri):    # yamalar HER hâlükârda sökülür — test düşse de, hata atsa da
            f()
    import threading
    kalan = sorted({t.name for t in threading.enumerate()
                    if any(t.name.startswith(p) for p in _HERMES_IPLIK_ADLARI)})
    if kalan:
        pytest.fail(
            f"HERMES ARKA PLAN İPLİĞİ SIZDI ({request.node.name}): {kalan} — iplik testten uzun "
            f"yaşıyor. `config.STATE` sandbox'tan geri alındıktan sonra yazarsa kayıt CANLI "
            f"state/events.jsonl'a düşer ve operatörün defterinde gerçek bir `agent_call` gibi "
            f"okunur. İpliği başlatan çağrıyı taklit et ya da testte join et.")


# ---- YEREL GERÇEK AJAN İKİLİSİ TESTLERE KAPALI (2026-08-02) -------------------------------------
# Yukarıdaki blok hermes İPLİĞİNİ kesiyordu; bu blok o ipliğin ALT SÜRECİNİ kesiyor — aynı
# ÖNLE/YAKALA felsefesinin bir katman aşağısı, ve önlenen şey daha pahalı.
#
# ÖLÇÜLEN VAKA (2026-08-02): `test_regime_patch::test_scheduler_flag_survives_publish_lag` GERÇEK
# kadans makinesini koşturuyor; `nous_eval → hermes._agent_call` yolu makinede KURULU gerçek
# `~/.local/bin/hermes` ikilisini buluyor ve başlatıyordu. O CLI kendi `~/.hermes/config.yaml`
# kaydıyla `python -m meridian.mcp_server`ı MERIDIAN_ROOT=/Users/erdemozturk/AI-Trading (yani ANA
# CHECKOUT — canlı-kopya state) sabitiyle doğuruyor. Üç bedelin ikisi ölçüldü, üçüncüsü bekliyordu:
#   (1) GERÇEK Gemini kotası yanıyor — bir 429 fırtınası bu yoldan ölçüldü;
#   (2) operatörün `~/.hermes` durumuna TESTTEN yazılıyor;
#   (3) MCP BUGÜN salt-okur olduğu için canlı state'e yazım OLMADI. Yani kapı bugün şans eseri
#       kapalıydı: ajan/MCP tarafına yarın eklenecek İLK yazım yolu doğrudan canlı state'e düşerdi.
# Ayrıca bir testin makinedeki kurulumu keşfedip süreç doğurması, o testin sonucunu MAKİNEYE bağlar:
# başka bir makinede başka sonuç veren bir test, geçtiğinde de hiçbir şey kanıtlamaz.
#
# ÜRETİM YOLU DEĞİŞMEZ: `_agent_call` None ikiliyle zaten DÜRÜST fail-open'dır (None döner, süreç
# doğmaz, çağıran deterministik yoluna iner). Kesilen tek şey KEŞİF koludur.
_HERMES_BIN_ENV0 = os.environ.get("HERMES_LOCAL_BIN")


def _hermes_bin_stub() -> str | None:
    """Yalnız TESTİN ENJEKTE ETTİĞİ ikiliyi onurlandırır; keşif kollarını hiç yürütmez.

    NEDEN DÜPEDÜZ `lambda: None` DEĞİL: üç test (test_regime_patch 327/358/389) tmp'de sahte bir
    betik yaratıp `monkeypatch.setenv("HERMES_LOCAL_BIN", ...)` ile gösteriyor ve `subprocess.run`ı
    zaten saplıyor — koşulsuz None onların BEKLENTİSİNİ değiştirirdi. Kesilmesi gereken kol
    keşiftir (PATH → ~/.hermes/bin → ~/.local/bin), testin açıkça verdiği yol değil.

    NEDEN `!= _HERMES_BIN_ENV0`: KABUKTAN miras alınan bir değer de makinedeki GERÇEK ikiliyi
    gösterebilir — o hâlde kapı bir ortam değişkeniyle sessizce açılırdı. Yalnız süreç İÇİNDE
    enjekte edilen (yani ithal anındaki fotoğraftan farklı) değer test-kaynaklı sayılır.
    `os.path.exists` kontrolü üretimdeki kolun aynısıdır: sahte yol da gerçekten var olmalı."""
    cand = os.environ.get("HERMES_LOCAL_BIN")
    if cand and cand != _HERMES_BIN_ENV0 and os.path.exists(cand):
        return cand
    return None


@pytest.fixture(autouse=True)
def _yerel_ajan_ikilisi_kapali():
    """Hiçbir test makinede kurulu GERÇEK hermes CLI'yi başlatmasın (gerekçe: yukarıdaki blok).

    KENDİ YAMASINI KENDİ KURAR/SÖKER — `monkeypatch` FİKSTÜRÜNÜ PAYLAŞMAZ: bu dosyada aynı ders üç
    kez yazılı (`_kancalari_kur`, `hermes_async_cagrilari`, `_hotstate_off_by_default`); paylaşılan
    monkeypatch'e bağlanmak fikstür SÖKÜM SIRASINI değiştirir ve komşu bekçilerin ölçümünü bozar.
    try/finally: yama HER hâlükârda geri konur — test düşse de, hata atsa da.

    SIRA GARANTİSİ (testin yaması kazanır): autouse fikstürler test-düzeyi `monkeypatch`ten ÖNCE
    kurulur, dolayısıyla sahte ikili isteyen testlerin kendi `setattr`ı (v169/v13/v96 deseni) bu
    saplamanın ÜSTÜNE yazar; söküm ters sırada olduğu için monkeypatch önce saplamayı geri koyar,
    sonra bu fikstür GERÇEK çözümleyiciyi geri koyar. Zincir her iki yönde de kapalıdır.

    ORİJİNALİ YIELD EDER: gerçek çözümleyiciyi SINAYAN testin ona ulaşabileceği tek yol budur
    (`hermes_bin_cozumleyici_asil` fikstürü) — aksi halde o test kendi saplamasını ölçerdi."""
    import meridian.hermes as _hm
    _asil = _hm._hermes_bin
    _hm._hermes_bin = _hermes_bin_stub
    try:
        yield _asil
    finally:
        _hm._hermes_bin = _asil


@pytest.fixture
def hermes_bin_cozumleyici_asil(_yerel_ajan_ikilisi_kapali):
    """GERÇEK `_hermes_bin` çözümleyicisi — yukarıdaki autouse saplamasının BİLİNÇLİ istisnası.
    Çözümleyicinin KENDİSİNİ sınayan test bunu `monkeypatch.setattr` ile geri takar; saplamayı
    ölçen bir test, ölçtüğünü sandığı üretim koluna hiç dokunmamış olurdu."""
    return _yerel_ajan_ikilisi_kapali


# ---- DIŞ AĞ TESTLERE KAPALI: SOKET DÜZEYİNDE (2026-08-02) ---------------------------------------
# Bir önceki blok yerel bir ALT SÜRECİ kesiyordu; bu blok o sürecin de altındaki katmanı kesiyor —
# İŞLETİM SİSTEMİ SOKETİNİ. Aynı ÖNLE/YAKALA felsefesinin en alt basamağı, ve kapsadığı yüzey en
# geniş olanı: hangi kütüphane kullanılırsa kullanılsın (httpx, requests, urllib, redis-py), makine
# dışına giden her TCP bağlantısı TEK bir yerden — `socket.socket.connect` — geçer. Adaptör başına
# saplama yazmak bu sınıfı asla kapatamaz, çünkü kapatılması gereken şey adaptörlerin LİSTESİ değil,
# o listenin YARIN ALACAĞI HÂLdir.
#
# ÖLÇÜLEN VAKA (2026-08-02): `test_regime_patch::test_scheduler_flag_survives_publish_lag` GERÇEK
# kadans makinesini koşturuyor; `scheduler.advance_once → earnings.refresh →
# data.nasdaq_earnings_window` yolu `api.nasdaq.com`a GÜN BAŞINA bir istek atıyordu. Sayılar (kapı
# YOKKEN, geçici bir sayaç eklentisiyle ölçüldü): o TEK test 23 dış TCP bağlantısı; 13 dosyalık
# süpürme 4 ayrı dış IP'ye toplam 37 bağlantı. Bedel üç katmanlı ve üçü de ölçüldü:
#   (1) NONDETERMİNİZM — testin sonucu Nasdaq'ın o ANKİ cevabına bağlanır. Ağ yokken ya da uç 5xx
#       dönerken kırmızı olur ve o kırmızılık ÜRÜNLE ilgisizdir; geçtiğinde de bir şey KANITLAMAZ,
#       çünkü ölçtüğü şey kod değil o günün internetidir. (`_yerel_ajan_ikilisi_kapali` bloğundaki
#       "makineye bağlı test hiçbir şey kanıtlamaz" dersinin ağ kolu.)
#   (2) KOTA — Nasdaq kolu anahtarsızdır, ama `earnings.refresh` gün kapsaması eşiğin (0,90)
#       altına düşünce FMP YEDEĞİNE iner ve o kol GERÇEK anahtarla koşar (250 istek/gün = bütün
#       günlük kota). Yani bir test koşumu canlı sistemin veri bütçesini yakabilir.
#   (3) SÜRE — 13 dosyalık süpürmede 70,8sn duvar süresine karşılık 20,0sn CPU; aradaki ~50sn
#       düpedüz ağ beklemesidir.
#
# NE GEÇER: AF_UNIX (soket çifti / yerel IPC) ve LOOPBACK (127.0.0.0/8, ::1, "localhost"). Bu bir
# kolaylık değil ZORUNLULUK: `hotstate` KENDİ testleri (v83/v84) `redis://127.0.0.1:6379` ile
# GERÇEK Redis'e bağlanır — `_hotstate_off_by_default` onları bilerek muaf tutar ve bu kapı da
# onların ÜSTÜNDE durur. Kapının konusu "ağ" değil, MAKİNE DIŞINA çıkan IP trafiğidir.
#
# NEDEN "DENEMEDEN": paket YOLA ÇIKMADAN düşülür. Bağlanıp sonra kapatmak (ya da timeout'a
# bırakmak) üç bedelin üçünü de ödemiş olurdu — uç isteği görür, kota yanar, süre akar.
#
# KAPSAMIN DÜRÜST SINIRI (uydurma yasağı): kapı YALNIZ `connect`/`connect_ex`i sarar. Ad çözümü
# (`getaddrinfo`) C katmanındadır, Python soket nesnesinden geçmez ve SARILMAZ — yani dış bir ad
# için DNS sorgusu hâlâ çözümleyiciye gidebilir. Kesilen şey hedefe giden BAĞLANTIdır; "test
# süreci hiç paket üretmez" DEĞİLDİR ve öyle okunmamalıdır.
_YEREL_ADLAR = frozenset({"localhost", "localhost.localdomain", ""})


class DisAgErisimiKapali(RuntimeError):
    """Bir test MAKİNE DIŞINA bağlanmaya çalıştı; bağlantı DENENMEDEN düşürüldü.

    `RuntimeError` SEÇİMİ BİLİNÇLİ, `OSError` DEĞİL: OSError türevi bir istisna httpcore/httpx'in
    bağlantı-hatası eşlemesine takılıp `httpx.ConnectError`e dönüşürdü ve çağıran tarafta "ağ
    yoktu" diye okunurdu — yani kapı, kapattığı şeyi TAKLİT eder ve GÖRÜNMEZ olurdu. Amaç tam
    tersi: yamalanmamış yol gürültülü biçimde görünsün.

    Ama `Exception` türevi olması da ZORUNLU: üretimin dürüst fail-open yolları (`_get_json` üç
    denemeden sonra `FetchError`a çevirir, `nasdaq_earnings_window` günü GÜN BAZINDA yutar ve
    `stats`e sayar) `except Exception` ile yazılıdır. BaseException türetmek o yolları kırar ve
    kapı, ölçmek istediği DAVRANIŞI değiştirmiş olurdu."""


def _mesaj(adres) -> str:
    return (
        f"DIŞ AĞ TESTLERE KAPALI: bir test {adres!r} adresine bağlanmaya çalıştı "
        f"(bağlantı DENENMEDİ — hedefe paket gitmedi). Bu bir kapı arızası değil, YAMALANMAMIŞ BİR "
        f"YOL bulgusudur: o test bugün ne ölçtüğünü sanıyorsa sansın, fiilen o anki ağın durumunu "
        f"ölçüyor. ÇÖZÜM ağı açmak değil, ADAPTÖRÜ TESTİNDE YAMALAMAKtır — örn. "
        f"`monkeypatch.setattr(meridian.adapters.data, '_get_json', ...)`, ya da bir üst katmanda "
        f"`data.nasdaq_earnings_window` / `fmp.historical_eod`. Geçen tek trafik makine İÇİdir: "
        f"AF_UNIX ve loopback (127.0.0.0/8, ::1, localhost) — hotstate'in gerçek-Redis testleri "
        f"oradan koşar. Gerekçe: tests/conftest.py, 'DIŞ AĞ TESTLERE KAPALI' bloğu."
    )


def _yerel_adres_mi(sock, adres) -> bool:
    """Bu adres MAKİNE İÇİ mi? (AF_UNIX / loopback / belirtilmemiş)"""
    if getattr(sock, "family", None) not in (socket.AF_INET, socket.AF_INET6):
        return True          # AF_UNIX, AF_NETLINK, AF_BLUETOOTH...: IP çıkışı değil, kapının konusu dışı
    try:
        host = adres[0]
    except (TypeError, IndexError, KeyError):  # sessiz-yutma: AF_INET(6) için beklenmedik adres şekli; hüküm veremediğimiz bir adresi YEREL SAYMAK kapıyı sessizce açardı, dışarı sayılır
        return False
    if isinstance(host, (bytes, bytearray)):
        host = bytes(host).decode("ascii", "replace")
    if not isinstance(host, str):
        return False
    if host.lower() in _YEREL_ADLAR:
        return True
    try:
        ip = ipaddress.ip_address(host.split("%")[0])   # "fe80::1%en0" → kapsam ekini at
    except ValueError:  # sessiz-yutma: IP değil ÇÖZÜMLENMEMİŞ ad (örn. "api.nasdaq.com"); ad çözmek kapının işi değil ve çözülmemiş bir ad YEREL SAYILAMAZ → dışarı
        return False
    return ip.is_loopback or ip.is_unspecified          # 0.0.0.0 / :: → çekirdek bunu yerele çevirir


@pytest.fixture(autouse=True)
def _dis_ag_kapali():
    """Hiçbir test makine DIŞINA TCP bağlantısı açmasın (gerekçe: yukarıdaki blok).

    KENDİ YAMASINI KENDİ KURAR/SÖKER — `monkeypatch` FİKSTÜRÜNÜ PAYLAŞMAZ: bu dosyada aynı ders
    dört kez yazılı (`_kancalari_kur`, `hermes_async_cagrilari`, `_hotstate_off_by_default`,
    `_yerel_ajan_ikilisi_kapali`); paylaşılan monkeypatch'e bağlanmak fikstür SÖKÜM SIRASINI
    değiştirir ve komşu bekçilerin ölçümünü bozar. try/finally: yama HER hâlükârda geri konur —
    test düşse de, hata atsa da.

    SIRA GARANTİSİ (testin yaması kazanır): autouse fikstürler test-düzeyi `monkeypatch`ten ÖNCE
    kurulur. Bu kapıda sıra ayrıca ÖNEMSİZdir, çünkü rekabet YOK: testin yaması ADAPTÖR katmanında
    olur (`data._get_json`, `fmp.historical_eod`) ve o yol soket katmanına hiç İNMEZ — kapı sessiz
    kalır. Kapı yalnız yamalanmamış BİR yol kaldığında konuşur; söylediği şey de tam olarak budur.

    KAÇIŞ FİKSTÜRÜ YOKTUR, ve bilerek yoktur: "şu test dışarı çıkabilsin" düğmesi, kapının
    kapattığı sınıfı tek satırda geri açan bir yol bırakırdı ve BUGÜN o düğmenin tüketicisi yok
    (tüketicisiz mekanizma yasağı). `_yerel_ajan_ikilisi_kapali`nın `hermes_bin_cozumleyici_asil`
    istisnası bu kapıya EMSAL DEĞİL: orada muafiyetin somut bir tüketicisi vardı — çözümleyicinin
    KENDİSİNİ sınayan test. Burada dış ağın kendisini sınayan bir test yok."""
    _asil, _asil_ex = socket.socket.connect, socket.socket.connect_ex
    # `connect`/`connect_ex` socket.socket'in KENDİ __dict__inde DEĞİL — C tabanından (_socket.socket)
    # miras alınır. Sökerken körlemesine geri ATAMAK, sınıfa aslında hiç var olmamış bir girdi
    # bırakırdı (davranış aynı, ama sınıfın şekli kalıcı olarak değişmiş olurdu). Doğru söküm:
    # başlangıçta girdi VARSA geri koy, YOKSA sil ve mirası yeniden aç.
    _vardi = {"connect": "connect" in socket.socket.__dict__,
              "connect_ex": "connect_ex" in socket.socket.__dict__}

    def _kapi(self, adres):
        if _yerel_adres_mi(self, adres):
            return _asil(self, adres)
        raise DisAgErisimiKapali(_mesaj(adres))

    def _kapi_ex(self, adres):
        # connect_ex normalde errno DÖNDÜRÜR, atmaz. Burada bilerek ATIYOR: sessiz bir errno,
        # kapının bulduğu yamalanmamış yolu çağıranın "bağlanamadım" dalına gömerdi — yani kapı
        # kurulmuş ama görünmez olurdu (bu depodaki en pahalı kusur sınıfı).
        if _yerel_adres_mi(self, adres):
            return _asil_ex(self, adres)
        raise DisAgErisimiKapali(_mesaj(adres))

    socket.socket.connect, socket.socket.connect_ex = _kapi, _kapi_ex
    try:
        yield
    finally:
        for _ad, _fn in (("connect", _asil), ("connect_ex", _asil_ex)):
            if _vardi[_ad]:
                setattr(socket.socket, _ad, _fn)
            elif _ad in socket.socket.__dict__:
                delattr(socket.socket, _ad)


def _clear_module_caches():
    """Süreç-içi modül önbellekleri testler ARASI taşınır (2026-07-23, tarama bulgusu): bir test
    canlı skills/ ya da earnings verisinden okuyup dolan önbelleği bir sonrakine sızdırıyordu ve o
    test kendi kurmadığı veriyle 'geçiyor' görünüyordu. sandbox'a giriş/çıkışta hepsi sıfırlanır."""
    import meridian.earnings as _ea
    import meridian.skills as _sk
    import meridian.reflect as _rf
    import meridian.adapters.fmp as _fmp
    import meridian.secrets as _se
    # SIR ÖNBELLEĞİ DE SIZIYORDU (2026-07-26): `secrets.get` değerleri süreç-içi bir sözlükte
    # (TTL'li) tutuyor. Bir test `NOUS_MODEL`/`FMP_API_KEY` yamalayıp okuduğunda değer önbelleğe
    # düşüyor ve SONRAKİ test, kendi kurmadığı bir sırla "geçiyor" görünüyordu — ya da tersi:
    # gerçek makinedeki bir anahtar suite'e sızıp beyin zinciri ölçümünü değiştiriyordu.
    _se.clear_cache()
    # FMP KOTA BLOĞU DA SIZIYORDU (2026-07-26): `_KEY_BLOCKED` modül-global ve 429 gören bir test
    # anahtarı 1 saatliğine blokluyor; sonraki testler o bloğu MİRAS alıyordu. Bugüne kadar
    # görünmüyordu çünkü `_get`, tüm anahtarlar bloklu olsa bile birincil anahtarla YİNE DE bir
    # istek atıyordu — yani blok test-arası sızıyor ama sonucu maskeleniyordu. O fall-through
    # kaldırılınca sızıntı ortaya çıktı (test_data_audit_v17: tek başına geçiyor, paket içinde düşüyor).
    _fmp._KEY_BLOCKED.clear()
    # SAĞLIK KAYDI DA SIZIYORDU (2026-07-26): `_HEALTH` modül-global ve her çağrı onu günceller.
    # Sandbox'sız bir test mock 429 ile ok=False & calls>0 bırakınca SONRAKİ watchdog testi kendi
    # kurmadığı bir 'fmp_source starved' bulgusunu görüyordu — testin geçmesi ya da düşmesi
    # sırasına bağlı hâle gelir ve o an dedektör değil, sızıntı ölçülüyor demektir.
    #
    # ZAMANLAYICI DURUMU DA SIZIYORDU (2026-08-02): `scheduler._state` aynı sınıf, daha keskin —
    # merdiven alanları (`refetch_chase`, `refetch_sparse_attempts`, `refetch_next_at`) bir sonraki
    # teste taşınıyor ve o test yalnız kendi bildiği iki alanı kurduğu için ARTIĞIN üstüne yazamıyor.
    #
    # ÜÇÜ DE (+ iki kardeş `_HEALTH`) TEK YERDEN, MODÜLÜN KENDİ BAŞLANGIÇ DEĞERİYLE sıfırlanır;
    # gerekçe ve kanıt düzeyleri `_MODUL_DURUMLARI` tanımında satır satır yazılı. Elle yazılmış
    # literal ARTIK YOK: üretim tarafına eklenen bir alan, buradaki kopyayı sessizce eskitiyordu.
    for _mod, _attr in _MODUL_DURUMLARI:
        _d = getattr(_mod, _attr)
        _d.clear()                                   # YERİNDE: dış referanslar kopmasın
        _d.update(_MODUL_DURUMU0[f"{_mod.__name__}.{_attr}"])
    # KABA-KUVVET SAYACI DA SIZIYORDU (2026-07-29): `auth._FAILS` modül-global ve IP başına
    # başarısız giriş zaman damgası tutar. TestClient'ın istemci IP'si HER testte aynıdır
    # ("testclient"), yani başarısız girişi ölçen bir test 8 deneme biriktirince SONRAKİ testin
    # ilk `POST /api/login` çağrısı 429 (kilitli) alıyordu — kendi kurmadığı bir durumdan. Klasik
    # sıra bağımlılığı: tek başına yeşil, paket içinde kırmızı. Sayaç yerinde temizlenir (clear),
    # yeni bir dict ATANMAZ: `auth` modülündeki diğer referanslar kopardı ve sıfırlama hiçbir
    # şeye dokunmamış olurdu — `_fmp._HEALTH` ile aynı ders.
    import meridian.auth as _auth_mod
    _auth_mod._FAILS.clear()
    # `auth._DROP_REPORTED` AYNI SINIF (2026-08-14, kayan oturum turu): oturum-düşüşü olayının
    # sel kapısı da IP anahtarlı süreç-içi bir defterdir ve TestClient'ın IP'si her testte aynı
    # ("testclient"). Bir test düşüş olayını tetikleyip pencereyi kapatınca, SONRAKİ testin
    # beklediği olay 5 dakika boyunca hiç basılmazdı — `_FAILS` vakasının birebir tekrarı.
    _auth_mod._DROP_REPORTED.clear()
    _ea._CACHE.clear()
    _sk._DESC_CACHE = None            # dict|None: yeniden okumaya zorla
    for c in (_rf._CACHE_WARNED,):
        c.clear()
    for c in (_rf._INC_CACHE, _rf._PROBE_CACHE):
        c.clear()


@pytest.fixture(autouse=True)
def _hotstate_off_by_default(request):
    """Redis SICAK KATMANI testlerde varsayılan KAPALI (2026-07-23). Canlı döngü hook'ları
    (loop._save_broker → hotstate.cache_positions, daily_cycle → set_prices) test-arası CANLI
    Redis'e yazmamalı: (a) test izolasyonu bozulur, (b) her _save_broker'da bağlantı+ping suite'i
    yavaşlatır, (c) kirlenmiş bir _client kapalı-porta soket-timeout'la suite'i ASAR (bu bulundu).
    `_redis`'i None'a sabitlemek tüm hotstate okuma/yazmalarını no-op yapar — hook'lar canlıdaki
    graceful-degradation yolunu izler. hotstate KENDİ testleri (nodeid'de 'hotstate') gerçek Redis.

    KENDİ HOOK'UNU try/finally ile KUR/KALDIR — `monkeypatch` PAYLAŞMA: monkeypatch fikstürüne
    bağlanmak teardown sırasını değiştirir ve komşu SECTORS-guard'ı MASUM bir testi suçlar
    (2026-07-23 bunu yeniden yaşadım; ders zaten kayıtlıydı)."""
    if "hotstate" in request.node.nodeid:
        yield
        return
    from meridian import hotstate
    _orig = hotstate._redis
    hotstate._redis = lambda: None
    try:
        yield
    finally:
        hotstate._redis = _orig


@pytest.fixture
def sandbox_state(tmp_path, monkeypatch):
    """Redirect all state I/O to a temp dir. Clears config + module caches so nothing leaks between tests."""
    state = tmp_path / "state"
    (state / "history").mkdir(parents=True)
    (state / "bars").mkdir(parents=True)
    monkeypatch.setattr(config, "STATE", state)
    monkeypatch.setattr(config, "HISTORY", state / "history")
    monkeypatch.setattr(config, "BARS", state / "bars")
    # YEREL AJAN YAPILANDIRMASI SUITE'E SIZIYORDU (2026-07-26): `hermes.AGENT_CONFIG` GERÇEK
    # `~/.hermes/config.yaml` yolunu gösteriyor ve `_agent_provider()` onu okuyor. Yani beyin
    # zinciri ölçümü (paylaşılan üst-akış tespiti) operatörün MAKİNESİNDEKİ dosyaya bağlıydı:
    # aynı test farklı makinede farklı sonuç verirdi ve geçtiğinde bir şey KANITLAMAZDI. Testler
    # kendi yapılandırmalarını bu yola yazar; dosya yoksa okuma dürüstçe None döner.
    import meridian.hermes as _hermes
    monkeypatch.setattr(_hermes, "AGENT_CONFIG", str(tmp_path / "hermes_config.yaml"))
    # goal/bounds ZORUNLU yapılandırmadır: yoksa config.goal() FileNotFoundError atar. Her test
    # dosyası bunu kendi `seeded` fikstüründe ayrı ayrı kopyalıyordu; kaynağa taşındı (2026-07-22)
    # ki sandbox'a alınan her test, ek fikstür yazmadan gerçek yapılandırmayla koşabilsin.
    import shutil
    repo = pathlib.Path(__file__).resolve().parent.parent / "state"
    for f in ("goal.yaml", "bounds.yaml"):
        src = repo / f
        if src.exists():
            shutil.copy2(src, state / f)
    config.goal.cache_clear()
    config.bounds.cache_clear()
    _clear_module_caches()
    yield state
    config.goal.cache_clear()
    config.bounds.cache_clear()
    _clear_module_caches()


@pytest.fixture
def vaka(sandbox_state):
    """DONDURULMUŞ CANLI VAKA yükleyicisi (D3 modül 3, 2026-08-07): `vaka("<ad>")` → `tests.vaka.Vaka`.

    `ops/vaka_sabitle.py` bir canlı arızayı `tests/fikstur/vaka_<tarih>_<ad>/` altına dondurur;
    bu fikstür onu bir teste geri yükler. `sandbox_state`e BAĞLIDIR ve bu bir kolaylık değil bir
    KAPIDIR: `Vaka.state_kur()` `store` üzerinden yazar, yani sandbox yoksa CANLI `state/`e
    yazardı. Bağımlılığı buraya koymak, çağıranın unutmasını yapısal olarak imkânsız kılar.

    Yükleme sırasında manifestteki sha256'lar diskle karşılaştırılır — elle düzenlenmiş bir
    fikstür ADIYLA düşer (bkz. `tests/vaka.py` başlığı)."""
    from .vaka import yukle
    return yukle


@pytest.fixture
def kod_govdesi():
    """`kod_govdesi(yol)` → YORUMLARI AYIKLANMIŞ kaynak metni. Kaynak-tarayıcı çivilerin ortak aleti.

    NEDEN FİKSTÜR (2026-09-01, v218↔v357 tek-kaynak): iki test dosyası da "bu modülde şu çağrı
    GEÇMİYOR" diye ölçüyor ve ikisi de naif `satir.split("#")[0]` kullanıyordu. O ayıklama bir
    DİZGİNİN İÇİNDEKİ `#`i yorum sanar (`"a#b"` → `"a`) ve satırın gerisini sessizce siler: çivi,
    silinen bölgede duran bir ihlali GÖREMEZ — yani yasağın kapsamı, yasak metnin nerede yazıldığına
    bağlı olurdu. `tokenize` Python'un kendi ayrıştırıcısıdır ve dizgi ile yorumu karıştırmaz.
    Yardımcının İKİ KOPYASI, aynı körlüğün iki yerde ayrı ayrı düzeltilmesi demekti."""
    import io
    import tokenize

    def _al(yol) -> str:
        # YERLEŞİM KORUNUR, YALNIZ YORUM KESİLİR: jetonları yeniden birleştirmek `sg.evren()`i
        # `sg . evren ( )`e çevirir ve "şu çağrı geçiyor mu" araması hiçbir şey bulamaz. Yorum
        # jetonu HER ZAMAN tek satırlıktır, o yüzden satırı başlangıç sütunundan kesmek yeter.
        src = pathlib.Path(yol).read_text(encoding="utf-8")
        satirlar = src.splitlines()
        for t in tokenize.generate_tokens(io.StringIO(src).readline):
            if t.type == tokenize.COMMENT:
                satir, sutun = t.start
                satirlar[satir - 1] = satirlar[satir - 1][:sutun]
        return "\n".join(satirlar)
    return _al


def make_bars(n=320, seed=7, trend=0.0006, breakout_at=None):
    """Deterministic OHLCV with an optional clean breakout near the end."""
    rng = np.random.default_rng(seed)
    close = [100.0]
    for i in range(1, n):
        close.append(close[-1] * (1 + trend + rng.normal(0, 0.01)))
    close = np.array(close)
    if breakout_at:
        close[breakout_at:] *= 1.06  # step up to force a fresh high
    openp = close * (1 + rng.normal(0, 0.002, n))
    # OHLC TUTARLILIĞI (2026-07-23, tarama bulgusu): high/low YALNIZ close etrafında üretiliyordu,
    # open bağımsızdı — open bazen high'ı aşıyor ya da low'un altına düşüyordu ve `validate_bars`
    # bunu 'hard' (ohlc_inconsistent) reddediyordu. Yani make_bars kullanan HER test, üretimin veri
    # kapısının REDDEDECEĞİ barlarla koşuyordu. high >= max(o,c) ve low <= min(o,c) GARANTİ: fitili
    # gövdenin İKİ ucundan genişlet, tek uçtan değil.
    hi_base = np.maximum(openp, close)
    lo_base = np.minimum(openp, close)
    high = hi_base * (1 + np.abs(rng.normal(0, 0.004, n)))
    low = lo_base * (1 - np.abs(rng.normal(0, 0.004, n)))
    vol = rng.integers(1_000_000, 3_000_000, n).astype(float)
    if breakout_at:
        vol[breakout_at:] *= 2.0
    dates = pd.bdate_range("2022-01-03", periods=n)
    return pd.DataFrame({"date": dates, "open": openp, "high": high, "low": low,
                         "close": close, "volume": vol})


# ================================================================================================
# TSX DAVRANIŞ ÖLÇÜM HATTI — SÖK · ÇEVİR · KOŞTUR (2026-09-01)
# ================================================================================================
# NEDEN BURADA. Pano çivileri "kaynakta şu dize geçiyor mu" diye ölçmez; karar veren SAF işlevleri
# TSX'ten söker, `esbuild` ile çevirir ve `node`da GERÇEKTEN çağırır. Alt-dize tuzağı bu depoda
# tekrar tekrar yakalandı: bir alan adının kaynakta (hele yorumda) geçmesi OKUNDUĞUNU kanıtlamaz.
#
# HAT ÖNCE v316'DA YAZILDI, SONRA v354'E KOPYALANDI ve ikinci kopya "ithal ediliyor" diye beyan
# edildi — beyanla gerçeğin ayrıştığı nokta (görev incelemesi, 2026-09-01). TEK-KAYNAK YASASI:
# ayrıştırıcı TEK yerde durur, iki çivi de buradan alır. Kopya kalsaydı, biri düzeltilip öteki
# düzeltilmediğinde iki çivi AYNI TSX hakkında farklı hüküm kurardı.
#
# `kosucu` PARAMETRESİ BİR ARIZANIN BEDELİDİR: köprü çivileri `subprocess.run`u SÜREÇ GENELİNDE
# saplıyor (komutun kendisi de sözleşmenin parçası olduğu için). Saplama açıkken hattın kendi
# `esbuild`/`node` çağrıları da o saplamaya düşer ve ölçüm aracı sessizce `returncode=1` alır —
# çivi, ölçtüğü şey yüzünden DEĞİL kendi hattı yüzünden kırmızıya döner. Çağıran, saplamadan ÖNCE
# yakaladığı gerçek koşucuyu buraya verir.
import json as _json
import re
import subprocess as _subprocess
import tempfile as _tempfile

UI_KOK = _Path(__file__).resolve().parent.parent / "ui"
ESBUILD_YOLU = UI_KOK / "node_modules/.bin/esbuild"


def tsx_yorumlari_soy(metin: str) -> str:
    """Yorumları atar. Bir kuralın YORUMDA geçmesi uygulandığını kanıtlamaz."""
    metin = re.sub(r"\{/\*.*?\*/\}", "", metin, flags=re.S)
    metin = re.sub(r"/\*.*?\*/", "", metin, flags=re.S)
    return re.sub(r"^\s*//.*$", "", metin, flags=re.M)


def _tsx_esle(metin: str, bas: int, ac: str, kapa: str) -> int:
    """`bas`taki açılış imini eşleyen kapanışın BİR SONRASI."""
    derinlik, j = 0, bas
    while j < len(metin):
        if metin[j] == ac:
            derinlik += 1
        elif metin[j] == kapa:
            derinlik -= 1
            if derinlik == 0:
                return j + 1
        j += 1
    raise AssertionError(f"{ac} eşleşmedi (konum {bas})")


def _tsx_kapsam(metin: str, imza: str) -> tuple[int, int]:
    """İşlev GÖVDESİNİN açılış `{`si ile eşleşen `}`inin konumları.

    NEDEN BU KADAR DİKKATLİ: "imzadan sonraki ilk `{`" YANLIŞ cevaptır. Parametre yıkımı
    (`function X({ b }: …)`) ve nesne DÖNÜŞ TİPİ (`): { hal: … } {`) o ilk süslüyü çalar; ölçüm
    sessizce yanlış metni inceler ve çivi hiçbir şeyi tutmaz."""
    i = metin.find(imza)
    assert i != -1, f"`{imza}` bulunamadı (yorumlar soyulmuş kaynakta)"
    j = _tsx_esle(metin, metin.index("(", i), "(", ")")   # parametre listesini geç
    while True:
        while j < len(metin) and (metin[j].isspace() or metin[j] == ":"):
            j += 1                                         # dönüş tipi imi (`:`) ve boşluk
        assert j < len(metin) and metin[j] == "{", f"`{imza}` gövdesi bulunamadı"
        bas, son = j, _tsx_esle(metin, j, "{", "}")
        k = son
        while k < len(metin) and metin[k].isspace():
            k += 1
        if k < len(metin) and metin[k] == "{":
            j = k          # az önceki süslü DÖNÜŞ TİPİydi; gövde bir sonraki
            continue
        return bas, son


def tsx_islev_govdesi(metin: str, imza: str) -> str:
    """İşlevin gövdesi (süslü parantezler dâhil).

    NEDEN GÖVDE, NEDEN DOSYA GENELİ DEĞİL: bir ifadenin dosyada BİR YERDE geçmesi, o ifadenin ŞU
    işlevde durduğunu kanıtlamaz — kapı sökülüp başka bir işlevde bırakılsa dosya geneline bakan
    ölçüm yeşil kalırdı."""
    bas, son = _tsx_kapsam(metin, imza)
    return metin[bas:son]


def tsx_islev_kaynagi(metin: str, imza: str) -> str:
    """İmzasıyla birlikte işlevin TAM kaynağı — çeviriye bu gider."""
    _, son = _tsx_kapsam(metin, imza)
    return metin[metin.find(imza):son]


def tsx_saf_islevleri_cevir(kaynak: str, adlar, *, kosucu=None) -> str:
    """Adı verilen DIŞA AKTARILMIŞ saf işlevleri söküp `esbuild` ile JS'e çevirir."""
    kosucu = kosucu or _subprocess.run
    parcalar = []
    for ad in adlar:
        imza = f"export function {ad}("
        assert imza in kaynak, f"`{ad}` DIŞA AKTARILMIŞ bir işlev değil — davranışı ölçülemez"
        parcalar.append(tsx_islev_kaynagi(kaynak, imza))
    ts = "\n".join(parcalar).replace("export function", "function")
    cp = kosucu([str(ESBUILD_YOLU), "--loader=ts"], input=ts, capture_output=True,
                text=True, timeout=60)
    assert cp.returncode == 0, f"esbuild çeviremedi: {cp.stderr}"
    return cp.stdout


def tsx_islev_cagir(cevrilmis: str, ad: str, *argumanlar, kosucu=None):
    """Sökülen okuyucuyu `node`da GERÇEKTEN çağırır ve dönen hükmü verir."""
    kosucu = kosucu or _subprocess.run
    js = (cevrilmis + "\nconst __a = " + _json.dumps(list(argumanlar), ensure_ascii=False)
          + f";\nconsole.log(JSON.stringify({ad}(...__a)));\n")
    with _tempfile.TemporaryDirectory() as d:
        yol = _Path(d) / "olcum.mjs"
        yol.write_text(js, encoding="utf-8")
        cp = kosucu(["node", str(yol)], capture_output=True, text=True, timeout=60)
    assert cp.returncode == 0, f"node çalıştıramadı: {cp.stderr}"
    return _json.loads(cp.stdout.strip().split("\n")[-1])


def tsx_bileseni_cizdir(giris_tsx: str, cozum_dizini, ortam: dict | None = None,
                        *, kosucu=None) -> str:
    """Bir REACT BİLEŞENİNİ `node`da SUNUCU TARAFINDA çizer ve HTML çıktısını verir.

    NEDEN SAF İŞLEV ÇAĞRISI YETMİYOR (ölçülmüş kusur, 2026-09-01): saf okuyucular doğru hüküm
    kurabilir ve o hüküm EKRANA HİÇ ÇIKMAYABİLİR — bileşen, kartın erken çıkışlarının ardında
    dururken tam olarak bu oldu. Montaj bir MONTAJ ölçümü ister: gövdeyi ver, HTML'i oku.

    `--format=cjs` ZORUNLU: `react-dom/server` CJS'tir ve ESM paketine gömüldüğünde `require`
    (`util`) çözülemez — ilk denemede tam olarak bu düştü.
    """
    kosucu = kosucu or _subprocess.run
    with _tempfile.TemporaryDirectory() as d:
        paket = _Path(d) / "cizim.cjs"
        yap = kosucu([str(ESBUILD_YOLU), "--bundle", "--format=cjs", "--platform=node",
                      "--loader=tsx", "--jsx=automatic",
                      f"--tsconfig={UI_KOK / 'tsconfig.json'}", f"--outfile={paket}"],
                     input=giris_tsx, capture_output=True, text=True, timeout=180,
                     cwd=str(cozum_dizini))
        assert yap.returncode == 0, f"esbuild paketleyemedi:\n{yap.stderr}"
        cp = kosucu(["node", str(paket)], capture_output=True, text=True, timeout=120,
                    env={**os.environ, **(ortam or {})})
    assert cp.returncode == 0, f"node çizemedi:\n{cp.stderr}"
    return cp.stdout


# ================================================================================================
# BETİK YÜKLEYİCİ — gövde burada DEĞİL (2026-08-30)
# ================================================================================================
# `betikten_modul_yukle` yukarıda `ops.sasi_yukleyici.kaynaktan_yukle`den ithal edilir. Kusurun,
# ölçümünün ve `dont_inherit=True` gerekçesinin tamamı o dosyanın başlığındadır; buraya İKİNCİ bir
# anlatı yazmak, anlatının kendisini ayrışabilir iki kopyaya bölmek olurdu.

# ================================================================================================
# CANLI-STATE GEREKTİREN TESTLER — BEYANLI ATLAMA (2026-08-16)
# ================================================================================================
# ÖLÇÜLEN DURUM. Taze bir klonda (cloud oturumu, CI, yeni makine) tam suite 82 kırmızı sonuç
# veriyordu ve bunların 80'i bir HATA değildi: `state/` versiyonlanmıyor (CLAUDE.md kural 8;
# yalnız goal.yaml + bounds.yaml izli), gerçek defterler A1'de. Yani testler kodun bozuk
# olduğunu değil, VERİNİN OLMADIĞINI raporluyordu.
#
# NEDEN BU BİR KUSUR. Bu deponun her yerinde yazan ayrım burada tutulmuyordu: "ölçtük, kötü" ile
# "ölçemedik" AYNI piksele düşüyordu. 80 kırmızının içinde 2 gerçek bulgu vardı (DSR sıfır-varyans
# ihlali ve bayat RUNBOOK) ve ikisi de aylarca görünmedi — çünkü kimse 82 satırlık bir kırmızı
# listeyi okumaz. Sürekli kırmızı bir kapı, bakılmayan kapıdır (`ops/kapilar.sh` dersinin aynısı).
#
# ÇÖZÜM VE SINIRI. Eksik state ATLAMA'dır, başarısızlık değil — ve atlama ADIYLA görünür
# (`pytest -rs` nedeni basar). Depo bu deseni zaten kullanıyor (`pytest.skip("node yok")`,
# `pytest.skip("beyin zinciri bu ortamda yapılandırılmamış (temiz klon/CI)")`); yeni olan tek şey
# listenin BEYANLI ve DENETLENEBİLİR olması.
#
# ÜÇ GÜVENLİK ŞARTI — yoksa bu mekanizma "kırmızıyı halının altına süpürme" aracına dönerdi:
#   (1) KOŞUL YALNIZ DOSYANIN VARLIĞIDIR. Artefakt varsa test NORMAL koşar ve düşerse DÜŞER.
#       A1'de ve state'i olan her makinede davranış BİREBİR eskisi gibidir; hiçbir hüküm yumuşamaz.
#   (2) LİSTE BAYATLARSA KOŞUM KIRILIR. Bir beyan hiçbir teste karşılık gelmiyorsa (test yeniden
#       adlandırıldı/silindi) aşağıdaki kapı hata verir. Beyan, işi bitince kalamaz — bu deponun
#       `stale_sinks`/`stale_claims` disiplininin test tarafındaki karşılığı.
#   (3) LİSTE ELLE VE DAR TUTULUR. Buraya bir test EKLEMEK, "bu testin ölçtüğü şey canlı defterdir"
#       demektir. Ölçtüğü şey KOD olan bir test buraya YAZILAMAZ — yazılırsa gerçek bir regresyon
#       taze klonda sessizce atlanır. Ekleme gerekçesi ilgili kovanın başlığında yazılıdır.
_CANLI_STATE_BEYANI: dict[str, tuple[tuple[str, ...], str, dict[str, tuple[str, ...]]]] = {
    # kova adı: ((gereken state artefaktları), neden, {dosya: (test fonksiyonu, ...)})
    "skills_registry": (
        ("state/skills_registry.json",),
        "canlı skill kayıt defteri A1'de; bu çiviler o defterin İÇERİĞİNİ ölçer (arşivlenmiş "
        "kayıt disabled mı, zincir tutarlı mı, damga bayat mı) — defter yokken hüküm KURULAMAZ. "
        "Depodaki `skills/` klasörü defterin yerine geçmez: kayıt defteri etkinlik/emeklilik "
        "durumunu taşır, klasör yalnız içeriği.",
        {
            "test_skill_cleanup_v121.py": (
                "test_c1c_hayalet_arsivde_YOKTUR_ve_skill_SAYILMAZ",
                "test_c2_archived_registry_entries_are_disabled_unchained_and_reasoned",
                "test_c2b_merged_entries_name_their_target",
                "test_c2c_chain_contradictions_are_cleared_for_survivors",
                "test_c3b_live_registry_has_no_enabled_retired_entry",
                "test_c3c_archived_entries_are_outside_the_key_gate_with_provenance",
                "test_c4b_every_chained_skill_is_live_and_registered",
                "test_c5b_enabled_skills_all_have_a_live_folder",
                "test_c6_protected_five_untouched",
                "test_c6b_hermes_and_skill_evolve_preloads_point_at_live_skills",
                "test_c7_no_stale_run_stamps_survive",
                "test_c7b_archived_skills_have_no_run_stamp_and_keep_provenance",
                "test_c7c_cleared_stamp_is_recorded_not_silently_dropped",
                "test_c9_measure_then_activate_carries_its_condition",
                "test_c9b_activation_conditions_are_measurement_gated",
                "test_c10c_public_summary_computes_skill_counts_from_the_registry",
            ),
            "test_navigator_retirement_gate_v126.py": (
                "test_r1_digest_matches_live_registry_byte_for_byte",
                "test_r1b_digest_carries_every_retired_entry_and_merge_target",
                "test_r2_no_archived_name_in_actionable_fields",
                "test_r3_archived_primary_becomes_an_honest_gap",
                "test_r3b_dividend_gap_suggests_only_the_live_portfolio_manager",
                "test_r4_archived_secondary_is_excluded_and_named",
                "test_r5_registry_and_bundled_facts_agree_modulo_declared_source",
                "test_r7_protected_five_survive_the_gate",
                "test_r8_gate_is_pure_idempotent_and_output_is_stable",
                "test_r9_cli_reports_registry_source_from_repo_root",
                "test_r9b_digest_builder_check_passes",
            ),
            # `skills.enabled_in` / önyükleme kümeleri kayıt defterinden doğar: defter yokken
            # etkin skill listesi BOŞ döner ve iki çivi de boş kümeyle karşılaşır.
            "test_audit_fixes.py": ("test_pipeline_run_reports_only_engine_implemented_as_invoked",),
            "test_llm_advisor_v6.py": ("test_skill_preload_sets_are_curated_and_capped",),
        }),
    "strateji_yaml": (
        ("state/strategy.yaml",),
        "çalışan strateji parametreleri canlıda üretilir ve versiyonlanmaz; bu çiviler dosyanın "
        "İÇERİĞİNİ (sürüm, düğme değerleri, dokunulmazlık) ölçer.",
        {
            "test_bottleneck_v12.py": ("test_daily_cycle_refuses_regressive_session",
                                       "test_operator_budget_floor_is_versioned"),
            "test_cf_backfill_v14.py": ("test_backfill_only_touches_cf_files",
                                        "test_plans_for_session_shape_and_gate"),
            "test_score_rebuild_v115.py": ("test_h3_strategy_yaml_DOKUNULMADI",),
            "test_wpd_kardes_pit_v185.py": ("test_cf_backfill_karartma_VETOSU_URETMEZ",),
        }),
    "canli_defter": (
        ("state/trades.jsonl",),
        "canlı işlem defteri — bu çiviler GERÇEK satırlar üzerinde ölçüm yapar (varyans ataması, "
        "geçiş tablosu, MAE karnesi, otonomi sayımı, gölge-görüş kesişimi). Fikstür üretmek bu "
        "testlerin AMACINI ortadan kaldırır: ölçtükleri şey canlı defterin kendisidir.",
        {
            "test_hafta3b_v125.py": (
                "test_2C_component_ic_SEMASI_kaynaktan_dogrulandi",
                "test_2C_kucultme_verdict_TABANLARINA_girmez",
                "test_H1_karne_tek_ciftte_SAYI_uydurmaz",
                "test_H2_olu_aileler_ve_hic_onerilmemis_dugmeler_DINAMIK",
                "test_MAE_karnesi_kazanan_kaybeden_AYRI_olcer",
                "test_canli_kanit_paketi_H_paketini_TASIR",
                "test_gecis_tablosu_canli_defterden_kosar_ve_GECIS_BEYAN_EDER",
                "test_otonomi_sayimi_TS_TABANLI_satir_penceresi_DEGIL",
                "test_varyans_atamasi_E_raporunu_replike_eder_ve_v3_TEK_TERIM",
            ),
            "test_execution_fidelity_v75.py": (
                "test_gercek_defter_girisleri_BASILMIS_bir_barin_ACILISI",
                "test_gercek_barlarda_yeni_cikis_sirasi_islem_defterini_bozmuyor",
            ),
            "test_para_yasasi_v127.py": ("test_varyans_atamasi_PARA_payi_YUZDE_YUZ",),
            "test_skill_gorus_v218.py": (
                "test_katman_IKI_YONLU_keser_negatif_kanit_EMEKLILIK_isaretine_duser",),
        }),
    "mutasyon_tabani": (
        ("state/trades.jsonl", "state/skills_registry.json"),
        "mutasyon koşum hattı TEMİZ bir tabanda başlar (kendi kapısı: 'kirli bir temelde her "
        "mutasyon yakalandı görünür ve kapsama sayısı yalan söyler'). Taze klonda taban kirlidir "
        "çünkü `parity:brain_availability` dedektörü canlı beyin zincirini bulamaz — yani hattın "
        "KENDİ ön şartı sağlanmıyor, hattın kendisi bozuk değil.",
        {"test_mutation_v61.py": (
            "test_a_full_run_leaves_the_live_ledgers_untouched",
            "test_baseline_state_is_genuinely_clean",
            "test_blind_spots_are_reported_with_their_reason",
            "test_caught_inventory_is_pinned",
            "test_coverage_number_matches_the_inventory",
            "test_each_caught_mutation_names_the_detector_that_saw_it",
            "test_every_mutation_is_classified",
            "test_human_report_names_every_missed_class",
            "test_missed_inventory_is_pinned",
            "test_network_dependent_checks_are_declared_out_of_scope",
            "test_the_harness_records_that_each_mutation_changed_the_state",
            "test_the_sieve_detector_is_either_used_or_its_absence_is_logged",
        )}),
}

# ORTAM KOŞULLARI — state değil, KONTEYNERİN kendisi. Aynı üç şart geçerli; koşul yine ölçülür,
# varsayılmaz (bir sonraki makinede IPv6 varsa test koşar ve düşerse düşer).
_ORTAM_BEYANI: dict[str, tuple[str, str, dict[str, tuple[str, ...]]]] = {
    "ipv6": ("ipv6_yok",
             "çekirdek/konteyner IPv6 soketi açtırmıyor (socket.AF_INET6 → EAFNOSUPPORT); çivi "
             "dış adrese bağlanmamayı ölçer, IPv6 yokluğunu değil.",
             {"test_kadans_ag_kapisi_v177.py": ("test_dis_adres_baglanmadan_adli_istisnayla_duser",)}),
    "sudo": ("sudo_gereksiz",
             "süreç ROOT koşuyor, dolayısıyla `sprint._systemctl_komutu()` doğru davranıp "
             "`sudo -n` öneki OLMADAN dönüyor; çivi ÜRETİM kurulumunu (root olmayan servis "
             "kullanıcısı) ölçer ve bu konteynerde o kurulum yok.",
             {"test_sprint_systemd_v241.py": ("test_tetik_komutu_uretimde_sudo_n_systemctl",)}),
}


def _ortam_kosulu(ad: str) -> bool:
    """Beyan edilen ortam şartı SAĞLANIYOR mu? (True → test normal koşar.) Ölçülür, varsayılmaz."""
    if ad == "ipv6_yok":
        try:
            socket.socket(socket.AF_INET6, socket.SOCK_STREAM).close()
            return True
        except OSError:
            return False
    if ad == "sudo_gereksiz":
        return os.geteuid() != 0
    raise AssertionError(f"bilinmeyen ortam şartı: {ad}")   # beyan bayatladı


def _eksik_artefaktlar(gerekli: tuple[str, ...]) -> list[str]:
    """Beyan edilen state artefaktlarının HANGİLERİ diskte yok? (Repo kökünden bakılır — bu
    beyanların konusu SANDBOX değil, deponun yanındaki gerçek `state/` dizinidir.)"""
    kok = pathlib.Path(__file__).resolve().parents[1]
    return [a for a in gerekli if not (kok / a).exists()]


def pytest_collection_modifyitems(config, items):
    """Beyanlı canlı-state/ortam şartı sağlanmayan testleri ADIYLA atlar (bkz. yukarıdaki blok).

    BAYAT BEYAN KOŞUMU KIRAR: bir beyan hiçbir toplanan teste karşılık gelmiyorsa hata verilir —
    ama YALNIZ ilgili dosya bu koşuma dahilse. `pytest -k` ya da tek dosya koşumlarında beyanın
    karşılıksız kalması normaldir; bayatlık ancak dosya toplandığı hâlde AD tutmadığında ölçülür."""
    toplanan: dict[str, set[str]] = {}
    for it in items:
        toplanan.setdefault(pathlib.Path(str(it.fspath)).name, set()).add(
            it.originalname or it.name.split("[")[0])

    isaretli: list[tuple[str, str, str]] = []      # (dosya, fonksiyon, sebep)
    for _kova, (gerekli, neden, hedefler) in _CANLI_STATE_BEYANI.items():
        eksik = _eksik_artefaktlar(gerekli)
        for dosya, fonksiyonlar in hedefler.items():
            if dosya not in toplanan:
                continue
            bilinmeyen = [f for f in fonksiyonlar if f not in toplanan[dosya]]
            if bilinmeyen:
                # `UsageError`: `assert` burada INTERNALERROR olarak çıkar ve okunmaz; bu bir
                # kurulum hatasıdır, çökme değil — pytest onu adıyla ve tek satırda raporlasın.
                raise pytest.UsageError(
                    f"BAYAT CANLI-STATE BEYANI — {dosya} toplandı ama şu adlar yok: {bilinmeyen}. "
                    f"Test yeniden adlandırıldıysa beyanı da güncelle; silindiyse beyanı SİL "
                    f"(conftest._CANLI_STATE_BEYANI). Beyan, işi bitince yerinde duramaz.")
            if eksik:
                for f in fonksiyonlar:
                    isaretli.append((dosya, f, f"{', '.join(eksik)} YOK (temiz klon/CI) — {neden}"))

    for _kova, (sart, neden, hedefler) in _ORTAM_BEYANI.items():
        saglaniyor = _ortam_kosulu(sart)
        for dosya, fonksiyonlar in hedefler.items():
            if dosya not in toplanan:
                continue
            bilinmeyen = [f for f in fonksiyonlar if f not in toplanan[dosya]]
            if bilinmeyen:
                raise pytest.UsageError(
                    f"BAYAT ORTAM BEYANI — {dosya}: {bilinmeyen} (conftest._ORTAM_BEYANI)")
            if not saglaniyor:
                for f in fonksiyonlar:
                    isaretli.append((dosya, f, f"ortam şartı sağlanmıyor — {neden}"))

    if not isaretli:
        return
    sebepler = {(d, f): s for d, f, s in isaretli}
    for it in items:
        anahtar = (pathlib.Path(str(it.fspath)).name, it.originalname or it.name.split("[")[0])
        if anahtar in sebepler:
            it.add_marker(pytest.mark.skip(reason=sebepler[anahtar]))


# ---- KÖKEN TAKİBİ: paketin kendisi sonda olur (2026-07-22) ----
# Baskın kusur sınıfı ("üretici X yazar, tüketici Y okur") hiçbir testte görünmez, çünkü her test
# KENDİ fikstürünü kurar: iki tarafın beklentisini aynı el yazar, ayrışamazlar. Çözüm tek tek
# parite testi yazmak DEĞİL — 1257 testin GERÇEK okuma yollarını ölçüm aracı olarak kullanmak.
# MERIDIAN_PROVENANCE=1 ile açılır; varsayılan kapalıdır (üretim yolunda sıfır maliyet).
def pytest_sessionstart(session):
    import os
    if os.environ.get("MERIDIAN_PROVENANCE") == "1":
        from meridian import provenance
        provenance.basla()


def pytest_sessionfinish(session, exitstatus):
    import os
    # ---- .locks BUDAMASI (ROADMAP Ö-5, 2026-08-12) ----
    # pytest sandbox'ları MUTLAK tmp yollarını kilitleyince repo `state/.locks` altında
    # oturum-başına-benzersiz kilit adları birikiyordu (WP-S2 ölçümü: tek koşu +2, budama yok).
    # Mekanizma ve güvenlik sözleşmesi `store.kilit_budamasi`dadır (yalnız SERBEST — non-blocking
    # flock alınabilen — VE eski dosyalar silinir; tutulan kilit DOKUNULMAZDIR, testi v234).
    # TETİK BİLEREK YALNIZ BURADA: canlı worker'ın `.locks`'u sınırlı ad kümesidir (pytest çöpü
    # orada doğmaz), başlangıca bağlamak sıfır kazanca karşı yarış penceresi açardı. xdist
    # worker'ında koşmaz (`workerinput`): eşzamanlı test süreçleri bitmeden budayıcı çalışmasın.
    if not hasattr(session.config, "workerinput"):
        try:
            from meridian import store as _store
            r = _store.kilit_budamasi()
            if r["budandi"]:
                print(f"\n[kilit-budama] {len(r['budandi'])} eski serbest kilit silindi "
                      f"(tutulan {r['tutulan']}, genç {r['genc']}, hata {r['hata']}) — {r['dizin']}")
        except Exception as e:
            # sessiz-yutma değil, beyanlı: budayıcının düşmesi test sonucunu değiştiremez ama
            # görünmez de kalamaz — tek satır beyan basılır, oturum çıkış kodu ellenmez.
            print(f"\n[kilit-budama] atlandı: {type(e).__name__}: {e}")
    if os.environ.get("MERIDIAN_PROVENANCE") != "1":
        return
    import json
    from meridian import provenance
    rep = provenance.rapor()
    provenance.dur()
    # ÇIKTI ARTIK docs/ ALTINDA (K1, 2026-07-30): rapor depo KÖKÜNE yazılıyordu ve orada 8 gün
    # bayat, okuyucusuz ve `ok:false` diye durdu — okunmayan bir "sorun var" raporu yanlış güven
    # kaynağıdır. Daha kötüsü: `recompute` orphan taraması yalnız `state/*.json*` gezdiği için
    # kökteki bu dosyayı HİÇ göremiyordu (K1'de o kesit de genişletildi). docs/ altında olması
    # onu bir BELGE yapar: üretimi elle (MERIDIAN_PROVENANCE=1) tetiklenen, tarihli bir ölçüm.
    out = os.environ.get("MERIDIAN_PROVENANCE_OUT") or "docs/provenance_report.json"
    with open(out, "w") as f:
        json.dump(rep, f, ensure_ascii=False, indent=1)
    print(f"\n[köken] artefakt={rep['artifacts']} satır={rep['rows_seen']} "
          f"sürüklenme={len(rep['drift'])} belirsiz={len(rep['inconclusive'])} "
          f"ölü_alan={len(rep['dead_fields'])} → {out}")
