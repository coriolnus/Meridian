#!/usr/bin/env python3
"""EDG-2026-102 — replay stop çıkışlarının GERÇEK kayması: tick arşivinde eff_stop'a dokunuştan sonraki
ilk işlem fiyatı (EDG-2026-045 Ö2) · ölçüm betiği (TSK-221, 2026-09-25).

KART: research/cards/EDG-2026-102-replay-stop-kaymasi-tick.yaml — hipotez, eşik, kill-list, pozitif kontrol
ORADA DONUK. Betik karta DOKUNMAZ ve HÜKÜM İŞLEMEZ: karar kuralını kartın cümlesiyle BASAR; hükmü Rol-1
karta + K defterine aynı turda işler. Çivi dosyası: tests/test_edg102_stop_kayma_v546.py.

SÖZLEŞME KOMUT SATIRIDIR (A1, Rol-1, salt-okur):
  /opt/veri/pilot-venv/bin/python olcum.py --db /opt/meridian/state/meridian.db \\
      --tick-kok /opt/veri/tick/islem --bar-kok /opt/meridian/state/bars --cikti <dizin> [--elle-ornek 5]
  --kuru            tik VERİSİ OKUNMADAN: girdi dökümü + eff_stop öz-sınaması + gün dosyası/şema kapsamı +
                    bar kapsamı + PK-1 → <cikti>/kuru.json. A1'de GERÇEK koşumdan önceki kuru adımdır
                    (pyarrow okuyucusunun şema yolunu gerçek dosyalarda ilk kez sınar).
  --okuyucu duckdb  parquet okuyucusu. Varsayılan `pyarrow` = A1 sözleşmesi. `duckdb` yerel çivi yoludur
                    (depo venv'inde pyarrow YOK, ölçüldü 2026-09-25) — AÇIKÇA seçilir ve sonuc.json'a
                    yazılır; pyarrow yoksa betik duckdb'ye SESSİZCE DÜŞMEZ, adıyla durur.
Çıkış kodu: 0 ölçüm/kuru adım tamam (hüküm durumu sonuc.json `ozet.durum`da) · 2 kullanım/koruma reddi ·
3 parquet şema kapısı · 4 PK-1 (çalışma anı kimlik) düştü — gerçek veriye dokunulmadı.

BAĞIMLILIK: yalnız stdlib + pyarrow (A1 `/opt/veri/pilot-venv`). `meridian` İÇE AKTARILMAZ: A1'de motor
paketi `obs` üzerinden canlı yerel deftere yazabilir (CLAUDE.md §2); motorla aynılık betikte değil ÇİVİDE
kanıtlanır (v546 motoru içe aktarır). Veritabanı `sqlite3` + `file:…?mode=ro` URI ile SALT-OKUR açılır.
YAZIM YALNIZ `--cikti` ALTINDADIR; çıktı dizini girdi ağaçlarının (DB dizini, tik kökü, bar kökü) içine
düşerse betik REDDEDER; var olan sonuç dosyasının üstüne yazmaz (dondurulmuş ölçüm korunur).

════════ eff_stop TERSİNE-ÇEVİRME — formül MOTOR KAYNAĞINDAN okundu (sembol çapaları) ════════
Replay tohumu `meridian.run.replay_seed` → `meridian.backtest.replay`; stop çıkışı bar-içi kademe-2'dir:
  `meridian.broker.PaperBroker._touch_exit`:  eff_stop = max(pos.stop, pos.trail_stop)   [pre_scale_stop
        tabanı yalnız scale_out bankalama barında; replay'de exit.scale_out_frac = 0 → girdi `scaled_out`
        sayılır ve raporlanır]; `if o <= eff_stop: → "stop_gap"` (kart DIŞI); `if l <= eff_stop:
        return eff_stop, "stop"`  → ham çıkış = eff_stop'un KENDİSİ.
  `meridian.broker.PaperBroker.close_position`:  exit_fill = raw_exit * (1.0 - self.slip);
        satır["exit"] = round(exit_fill, 4);  self.slip = slippage_bps / 10000.0
        (`meridian.broker.PaperBroker.__init__`; replay broker'ı goal.slippage_bps ile kurar = 5).
  pos.stop = plan["stop"]  (`meridian.broker.PaperBroker.fill_entry`; plan alanı strateji tarafında
        round(…, 4) — `meridian.strategy`), trail_stop yuvarlanmamış bir float'tır
        (`meridian.strategy.manage_position`).
  İLERİ:  exit = round(eff_stop × (1 − s), 4),  s = 5 / 1e4  → `ileri_dolum` (motorla AYNI float işlemleri).
  TERS:   eff_stop ≈ exit / (1 − s)  → `ters_eff_stop`;  |ters − eff_stop| ≤ 0,5e-4 / (1 − s)
          (`ters_hata_siniri` — 4-hane yuvarlamanın ters görüntüsü).
  IZGARA KİLİDİ (beyanlı iyileştirme, öz-sınamanın yan ürünü): plan kaydındaki sert stop P,
          round(P × (1 − s), 4) == exit'i BİREBİR veriyorsa eff_stop = P (motorun kullandığı değerin
          kendisi). Gerekçe (v546 `test_izgara_kilidi_…`; inceleme 2026-09-25 ile düzeltildi): 4-hane yuvarlama
          artığının İŞARETİ fiyatların ~yarısında negatif (bağımsız kontrol ~200 bin kuruş fiyatı: ~%50/%50) —
          yanlılık "her zaman" DEĞİL. Ama etkisi ASİMETRİK: saf ters değer P'nin ≤ 5e-5 ALTINA düştüğünde TAM
          stop seviyesindeki tik dokunuş sayılmaz → dokunuş daha derin bir tike kayar → kayma YUKARI (hipotez
          yönüne); ÜSTÜNE düştüğünde kuruş ızgarasında arada tik olamaz → etki YOK. Yani saf ters, yalnız stop
          seviyesinde tam tik bulunan satırların ~yarısında yukarı yanlıdır. Trailing çıkışlarda P ≠ eff_stop →
          saf ters değer kullanılır (hata sınırı yukarıda). Tanı (f) saf-ters medyanını ayrıca basar.
ÖZ-SINAMA (kill-list 1): plan stop'u `trade_plans.stop` (satır `trades.plan_id` = `trade_plans.id`;
  tipli kolon + extra_json birleşimi `meridian.storage._cols_to_row` semantiğiyle — extra KAZANIR).
  Sınıflar: plan_ileri_esit (sert stop, ileri formül BİREBİR) · plan_trailing_ustte (ters > P + tol) ·
  plan_yakin_esit_degil (|ters − P| ≤ tol ama ileri eşit değil) · plan_alti_ihlal (ters < P − tol —
  imkânsız: eff_stop ≥ pos.stop → TERSİNE-ÇEVİRME REDDİ). Plan satırı yoksa işlem-içi türetim:
  sert stop = entry − r_payda_usd / qty (`meridian.broker.Position.r_payda_usd`, yalnız r_payda =
  "giris_riski" ve scaled_out değilse; tolerans iki 4-hane yuvarlamanın toplamı). GEÇER: (plan_ileri_esit +
  islem_ici_tutarli) ≥ 20 (kart: "en az 20 satırda tutarlı").

════════ TİK ARŞİVİ — birim ve ölçek ÜRETİCİDEN okundu ════════
`research/olcumler/edg066_tick_arsiv/pilot.py` (`ayristir`, `ParquetYazici`): islem/<GÜN>.parquet şeması
  ts int64 · sembol string · fiyat int64 · lot int32 · kosul uint8 · k_ts int64 · k_alis_fiyat int64 ·
  k_alis_lot int32 · k_satis_fiyat int64 · k_satis_lot int32.
  ts = IEX TOPS zaman damgası, POSIX epoch NANOSANİYE, UTC (pilot saat kovasını `ts // NS % 86400` ile
  UTC günün saniyesinden alır; tz alanı yok). fiyat/k_*_fiyat = TOPS "Price": 1e-4 birimli TAMSAYI
  (pilot başlığı: "fiyatlar 1e-4 tamsayı birim") → dolar = fiyat / 10000. kosul = TOPS sale-condition
  bayrak baytı (bit anlamları depoda BELGESİZ — kart); k_* = işlem ANINDAKİ son kotasyon, yoksa null.
  Dosya satır sırası = akış (mesaj) sırasıdır; eşit ts'de dosya sırası korunur (kararlı sıralama).
  Şema kapısı (`_sema_kapisi`) kullanılan sütunların tiplerini her dosyada doğrular — tip kayarsa DURUR.
Sembol: trades.ticker büyük harfe çevrilir, başka dönüşüm YOK (pilot/kapsam: sınıf hisseleri noktalı —
  BRK.B; motor da noktalı tutar, `meridian.adapters.data._cache_path` yalnız DOSYA adında '.'→'-' yapar).

════════ ÖLÇÜM (kart olcum_plani) ════════
Seans süzgeci: 09:30 ≤ ET < 16:00, `zoneinfo("America/New_York")` — DST-farkında; `kosul` BİRİNCİLDE
  KULLANILMAZ (kill-list 4; çivi: kosul değişince birincil bayt-özdeş).
tick_fill: o günün sembol kayıtları ts'e göre (kararlı); ilk fiyat ≤ eff_stop = DOKUNUŞ; dokunuştan SONRAKİ
  ilk kayıt fiyatı = tick_fill. Dokunuş yok → `dokunus_yok` (alt neden: gun_dosyasi_yok /
  seansta_sembol_kaydi_yok / fiyat_esige_inmedi — kapsam boşluğu da dokunuşsuzluktur, kart kill-2
  cümlesi); dokunuş son kayıt → `sonraki_yok`. İkisi medyana GİRMEZ, sayılır.
kayma_bps = (eff_stop − tick_fill) / eff_stop × 1e4 (long; aleyhte +).
Kestirim: medyan + %95 CI — seans-kümeli yüzdelik bootstrap, B=5000, seed=20260812. YÖNTEM EDG-2026-042
  `betimleyici`deki seans-kümeli bootstrap'in AYNISIDIR (random.Random(seed) · küme başına randrange ·
  statistics.median · lineer yüzdelik); v546 aynı girdide İKİSİNİN BİREBİR aynı CI'yı verdiğini çiviler.
  İÇE AKTARILMADI, çünkü: (a) o fonksiyon kova-eşik tablosuna (ESIK) ve 3 hane yuvarlamaya bağlı, ayrık
  bir bootstrap yüzeyi yok; (b) donmuş bir koşum dizinine çalışma-anı bağımlılığı, betiği A1'de tek dosya
  olarak koşulamaz yapar. EDG-045'in kendi bootstrap'i (numpy, AY kümeli EŞLENİK ΔP&L toplamı) başka bir
  istatistiktir ve numpy pilot-venv sözleşmesinde yoktur — künye (B, seed) aynen devralındı.
Karar kuralı (kart esikler.karar_kurali): n_olculen ≥ 100 ∧ ≥ 50 seans şartıyla; CI-alt > 5 → "STOP
  BACAĞINDA MODEL İYİMSER" · CI-üst < 5 → "MODEL YETERLİ (stop bacağı)" · aksi → "BELİRSİZ".
Kill-list: (1) öz-sınama < 20 → GEÇERSİZ · (2) dokunus_yok / uygun > %20 → medyan YAYIMLANMAZ ·
  (3) tek seans ölçülen örneklemin > %10'u → CI ŞERHLİ · (4) kosul birincilde yok (yapısal) ·
  (5) PK ayağı düşerse sayı yok (PK-1 çalışma anında; PK-2 Rol-1'in elle doğrulaması; PK-3 sayılır).
Pozitif kontrol: PK-1 kimlik (`pk1_kimlik`, gerçek veriden ÖNCE aynı kodla) · PK-2 `--elle-ornek N`
  sabit tohumlu örneklem, dokunuş ±3 kayıt ham dilim + elle doğrulama tarifi (OZET.md) · PK-3 bar çaprazı:
  ts_close günü bar düşüğü ≤ eff_stop (+ters toleransı) VE tik seans minimumu ≤ eff_stop; tutarsız sayılır.
  Bar CSV: `<bar-kok>/<ticker küçük, '.'→'-'>.csv`, sütunlar date,open,high,low,close,volume
  (`meridian.adapters.data._cache_path`, `meridian.adapters.data._write_bars`). BEYANLI RİSK (karta ek, tanı
  e): barlar SPLIT-düzeltmeli (`meridian.adapters.data._fetch_fmp` başlığı), tik fiyatları HAM → tohum
  zamanından önceki bir bölünme o satırın eff_stop'unu ham tikten ölçek kadar ayırır (ileri bölünme →
  dokunus_yok; ters bölünme → dev kayma). `olcek_orani` = bar kapanışı / tik seans son fiyatı, [0,9; 1,1]
  dışı `olcek_uyumsuz` sayılır; tanı (e) o satırlar dışlanınca medyanı basar. Birincil KARTA göre kalır.
Tanılar (hüküm değil): (a) kosul & 0x20 kayıtları dışlanınca medyan · (b) dokunuş anı kotasyon spread'i
  (k_satis − k_alis) · (c) yıl ve fiyat kovası kırılımı · (d) ek = medyan − 5 → EDG-045 {5,10,20} en yakın
  hücre · (e) ölçek-uyumlu altküme medyanı · (f) saf-ters (ızgara kilitsiz) medyan.

ÇIKTILAR (<cikti>/) VE OKUYUCULARI (Yasa 6): sonuc.json + OZET.md → Rol-1 hükmü (karta + K defterine);
  girdi_trades.json / girdi_planlar.json → içerik-adresli girdi dondurması (sha256'ları sonuc.json'da;
  Rol-1 yeniden koşumda karşılaştırır); kuru.json → kuru adımın Rol-1 okuması.
DİSİPLİN: uydurma yasağı (ölçülemeyen None + neden) · Yasa 4 (sessiz yutma yok) · git/state yazımı yok.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import pathlib
import platform
import random
import sqlite3
import statistics
import sys
import time
from zoneinfo import ZoneInfo

# ── KART SABİTLERİ (research/cards/EDG-2026-102-…yaml — v546 kartla birebir çiviler) ──────────────────
KART_ID = "EDG-2026-102"
ARAC_SURUMU = "1"
N_UYGUN_ALT = 100                 # esikler.n_uygun_alt
SEANS_ALT = 50                    # esikler.seans_alt
MODEL_VARSAYIMI_BPS = 5.0         # esikler.model_varsayimi_bps (= goal.slippage_bps)
SLIP_BPS = 5.0                    # replay broker'ının kayması — ters formülün s'si (öz-sınama doğrular)
DOKUNUS_YOK_TAVAN = 0.20          # kill-list 2: "%20'sini aşarsa"
TEK_SEANS_TAVAN = 0.10            # kill-list 3: "%10'undan fazlasını"
OZ_SINAMA_ALT = 20                # kill-list 1: "en az 20 satırda"
BOOT_B = 5000                     # olcum_plani: B=5000
BOOT_TOHUM = 20260812             # olcum_plani: seed=20260812
EDG045_HUCRELERI = (5, 10, 20)    # tanı (d)
KOSUL_TEK_LOT_BITI = 0x20         # tanı (a)

FIYAT_OLCEK = 10_000              # pilot: fiyatlar 1e-4 tamsayı birim
NS = 1_000_000_000
ET = ZoneInfo("America/New_York")
SEANS_ACILIS = dt.time(9, 30)
SEANS_KAPANIS = dt.time(16, 0)
OLCEK_BANDI = (0.9, 1.1)          # tanı (e): split ≥ 5:4 bu bandın dışına düşer
ELLE_PENCERE = 3                  # PK-2: dokunuş ±3 kayıt
FIYAT_KOVALARI = ((0.0, 25.0), (25.0, 50.0), (50.0, 100.0), (100.0, 250.0), (250.0, math.inf))

KARAR_IYIMSER = "STOP BACAĞINDA MODEL İYİMSER"
KARAR_YETERLI = "MODEL YETERLİ (stop bacağı)"
KARAR_BELIRSIZ = "BELİRSİZ"

CIKTI_DOSYALARI = ("sonuc.json", "OZET.md", "girdi_trades.json", "girdi_planlar.json")
KURU_DOSYALARI = ("kuru.json", "girdi_trades.json", "girdi_planlar.json")

# Kullanılan sütunlar ve kanonik tipleri (pilot `ayristir` ty şeması); iki okuyucunun tip adları eşlenir.
OKUNAN_SUTUNLAR = ("sembol", "ts", "fiyat", "lot", "kosul", "k_alis_fiyat", "k_satis_fiyat")
BEKLENEN_SEMA = {"ts": "i64", "sembol": "str", "fiyat": "i64", "lot": "i32", "kosul": "u8",
                 "k_alis_fiyat": "i64", "k_satis_fiyat": "i64"}
_TIP_ESLEME = {"int64": "i64", "BIGINT": "i64", "int32": "i32", "INTEGER": "i32",
               "uint8": "u8", "UTINYINT": "u8", "string": "str", "large_string": "str",
               "VARCHAR": "str"}


class SemaHatasi(RuntimeError):
    """Parquet şeması pilot sözleşmesinden saptı — birim/ölçek varsayımı çöker, ölçüm DURUR."""


# ── eff_stop formülü ve tersi ────────────────────────────────────────────────────────────────────────
def ileri_dolum(eff_stop: float, slip_bps: float = SLIP_BPS) -> float:
    """Motorun stop dolum satırı: round(eff_stop × (1 − s), 4) — AYNI float işlem sırası
    (`meridian.broker.PaperBroker.close_position`)."""
    s = slip_bps / 10000.0
    return round(eff_stop * (1.0 - s), 4)


def ters_eff_stop(exit_fiyat: float, slip_bps: float = SLIP_BPS) -> float:
    """exit → eff_stop (tersine-çevirme); hata ≤ `ters_hata_siniri`."""
    return exit_fiyat / (1.0 - slip_bps / 10000.0)


def ters_hata_siniri(slip_bps: float = SLIP_BPS) -> float:
    """4-hane yuvarlamanın (±0,5e-4) ters görüntüsü + float payı."""
    return 0.5e-4 / (1.0 - slip_bps / 10000.0) + 1e-9


def _sayi(x):
    """Sayıya çevrilebilen değer → float; değilse None (uydurma yok)."""
    if isinstance(x, bool) or x is None:
        return None
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def eff_stop_coz(satir: dict, plan_stoplari: list, slip_bps: float = SLIP_BPS) -> dict:
    """Bir stop satırının eff_stop'u + öz-sınama sınıfı. `plan_stoplari`: aynı plan_id'li plan kayıtlarının
    stop değerleri (0, 1 ya da çok). Dönen `red=True` → TERSİNE-ÇEVİRME REDDİ (satır uygun değildir)."""
    ex = _sayi(satir.get("exit"))
    if ex is None or ex <= 0:
        return {"eff_stop": None, "ters": None, "kaynak": None, "oz": "exit_okunamadi",
                "plan_stop": None, "red": True}
    ters = ters_eff_stop(ex, slip_bps)
    tol = ters_hata_siniri(slip_bps)
    stoplar = [v for v in (_sayi(p) for p in plan_stoplari) if v is not None and v > 0]
    out = {"ters": ters, "red": False, "plan_coklu": len(stoplar) > 1}
    if stoplar:
        esit = [p for p in stoplar if ileri_dolum(p, slip_bps) == ex]
        if esit:
            p = min(esit, key=lambda v: abs(v - ters))
            return {**out, "eff_stop": p, "kaynak": "plan_stop", "oz": "plan_ileri_esit", "plan_stop": p}
        altta = [p for p in stoplar if p <= ters + tol]
        if not altta:
            return {**out, "eff_stop": None, "kaynak": None, "oz": "plan_alti_ihlal",
                    "plan_stop": min(stoplar), "red": True}
        p = max(altta)
        oz = "plan_trailing_ustte" if ters > p + tol else "plan_yakin_esit_degil"
        return {**out, "eff_stop": ters, "kaynak": "ters_formul", "oz": oz, "plan_stop": p}
    # plan kaydı yok → işlem-içi sert stop (entry − r_payda_usd / qty)
    giris, payda, adet = _sayi(satir.get("entry")), _sayi(satir.get("r_payda_usd")), _sayi(satir.get("qty"))
    if (satir.get("r_payda") == "giris_riski" and not satir.get("scaled_out")
            and giris is not None and payda is not None and adet):
        sert = giris - payda / adet
        tol2 = tol + 0.5e-4 + 0.5e-4 / adet
        if ters < sert - tol2:
            return {**out, "eff_stop": None, "kaynak": None, "oz": "islem_ici_alti_ihlal",
                    "plan_stop": sert, "red": True}
        oz = "islem_ici_tutarli" if ters <= sert + tol2 else "islem_ici_trailing_ustte"
        return {**out, "eff_stop": ters, "kaynak": "ters_formul", "oz": oz, "plan_stop": sert}
    return {**out, "eff_stop": ters, "kaynak": "ters_formul", "oz": "kaynak_yok", "plan_stop": None}


OZ_SINIFLARI = ("plan_ileri_esit", "plan_trailing_ustte", "plan_yakin_esit_degil", "plan_alti_ihlal",
                "islem_ici_tutarli", "islem_ici_trailing_ustte", "islem_ici_alti_ihlal", "kaynak_yok",
                "exit_okunamadi")


def oz_sinama_ozeti(cozumler: list) -> dict:
    """Kill-list 1: formülün geri verdiği eff_stop plan/işlem-içi sert stopla ≥ 20 satırda tutarlı mı."""
    say = {k: 0 for k in OZ_SINIFLARI}
    for c in cozumler:
        say[c["oz"]] = say.get(c["oz"], 0) + 1
    tutarli = say["plan_ileri_esit"] + say["islem_ici_tutarli"]
    return {**say, "plan_coklu": sum(1 for c in cozumler if c.get("plan_coklu")),
            "tutarli_n": tutarli, "esik": OZ_SINAMA_ALT, "gecti": tutarli >= OZ_SINAMA_ALT,
            "beyan": ("tutarlı = plan_ileri_esit (sert stop, ileri formül exit'i BİREBİR verir) + "
                      "islem_ici_tutarli (plan yokken entry − r_payda_usd/qty ile tolerans içinde); "
                      "trailing satırlar tutarlılık sayısına GİRMEZ (trail yeniden hesaplanmadı), yalnız "
                      "'sert stopun altına düşmedi' sınanır — altına düşen satır tersine-çevirme reddidir")}


# ── seans süzgeci ve dokunuş ────────────────────────────────────────────────────────────────────────
def seans_siniri_ns(gun: dt.date) -> tuple[int, int]:
    """[09:30, 16:00) ET → epoch ns; DST zoneinfo'dan."""
    a = dt.datetime.combine(gun, SEANS_ACILIS, tzinfo=ET)
    k = dt.datetime.combine(gun, SEANS_KAPANIS, tzinfo=ET)
    return int(a.timestamp()) * NS, int(k.timestamp()) * NS


def seans_suz(kayitlar: list, gun: dt.date) -> list:
    """kayıt = (ts, fiyat, lot, kosul, k_alis, k_satis), dosya sırasıyla. ts'e göre KARARLI sıralar ve
    normal seansı süzer. `kosul`a BAKMAZ (kill-list 4)."""
    a, k = seans_siniri_ns(gun)
    return sorted((r for r in kayitlar if a <= r[0] < k), key=lambda r: r[0])


def kayma_bps(eff_stop: float, tick_fill: float) -> float:
    return (eff_stop - tick_fill) / eff_stop * 1e4


def dokunus_ve_dolum(seans: list, eff_stop: float) -> dict:
    """İlk fiyat ≤ eff_stop = dokunuş; SONRAKİ ilk kayıt = tick_fill."""
    for i, r in enumerate(seans):
        if r[1] is not None and r[1] / FIYAT_OLCEK <= eff_stop:
            if i + 1 >= len(seans):
                return {"sinif": "sonraki_yok", "dokunus_i": i, "dolum_i": None,
                        "tick_fill": None, "kayma_bps": None}
            fill = seans[i + 1][1] / FIYAT_OLCEK
            return {"sinif": "olculdu", "dokunus_i": i, "dolum_i": i + 1, "tick_fill": fill,
                    "kayma_bps": kayma_bps(eff_stop, fill)}
    return {"sinif": "dokunus_yok", "dokunus_i": None, "dolum_i": None, "tick_fill": None,
            "kayma_bps": None, "alt_neden": ("seansta_sembol_kaydi_yok" if not seans
                                             else "fiyat_esige_inmedi")}


# ── istatistik ─────────────────────────────────────────────────────────────────────────────────────
def yuzdelik(sirali: list, q: float):
    """Lineer interpolasyonlu yüzdelik (dahil-dahil) — EDG-042 `yuzdelik`in yuvarlamasız hâli."""
    if not sirali:
        return None
    if len(sirali) == 1:
        return sirali[0]
    k = (len(sirali) - 1) * q
    alt, ust = int(k), min(int(k) + 1, len(sirali) - 1)
    return sirali[alt] + (sirali[ust] - sirali[alt]) * (k - int(k))


def seans_kumeli_ci(kumeler: list, B: int = BOOT_B, tohum: int = BOOT_TOHUM) -> tuple:
    """Seans-kümeli yüzdelik bootstrap (EDG-042 `betimleyici` yöntemi BİREBİR): her tekrarda küme
    sayısı kadar küme yerine koyarak çekilir, çekilen kümelerin TÜM satırlarının medyanı alınır."""
    rng = random.Random(tohum)
    medyanlar = []
    for _ in range(B):
        secim = [x for _ in kumeler for x in kumeler[rng.randrange(len(kumeler))]]
        medyanlar.append(statistics.median(secim))
    medyanlar.sort()
    return yuzdelik(medyanlar, 0.025), yuzdelik(medyanlar, 0.975)


def karar_kurali(ci_alt: float, ci_ust: float, model: float = MODEL_VARSAYIMI_BPS) -> str:
    if ci_alt > model:
        return KARAR_IYIMSER
    if ci_ust < model:
        return KARAR_YETERLI
    return KARAR_BELIRSIZ


def en_yakin_hucre(medyan: float) -> dict:
    ek = medyan - MODEL_VARSAYIMI_BPS
    uzak = {h: abs(ek - h) for h in EDG045_HUCRELERI}
    enaz = min(uzak.values())
    return {"ek_bps": round(ek, 3), "hucre": min(h for h, u in uzak.items() if u == enaz),
            "esit_uzak_hucreler": sorted(h for h, u in uzak.items() if u == enaz),
            "uzakliklar": {str(h): round(u, 3) for h, u in uzak.items()}}


def _r3(x):
    return None if x is None else round(x, 3)


def _medyan_ozeti(satirlar: list, alan: str) -> dict:
    v = [r[alan] for r in satirlar if r.get(alan) is not None]
    return {"n_olculen": len(v), "medyan_bps": _r3(statistics.median(v)) if v else None}


def _dagilim(v: list) -> dict | None:
    if not v:
        return None
    s = sorted(v)
    return {"n": len(s), "medyan": _r3(statistics.median(s)), "p25": _r3(yuzdelik(s, 0.25)),
            "p75": _r3(yuzdelik(s, 0.75)), "min": _r3(s[0]), "max": _r3(s[-1])}


def _fiyat_kovasi(p: float) -> str:
    for a, b in FIYAT_KOVALARI:
        if a <= p < b:
            return f"[{a:g},{b:g})"
    return "?"


def _tanilar(olculen: list, uygun: list, medyan: float) -> dict:
    kos = [r for r in uygun if r.get("kosulsuz_sinif") is not None]
    yil: dict[str, list] = {}
    kova: dict[str, list] = {}
    for r in olculen:
        yil.setdefault(r["seans"][:4], []).append(r["kayma_bps"])
        kova.setdefault(_fiyat_kovasi(r["eff_stop"]), []).append(r["kayma_bps"])
    spread = [r["spread_bps"] for r in olculen if r.get("spread_bps") is not None]
    olcek_ok = [r for r in olculen if r.get("olcek_uyumsuz") is False]
    return {
        "kosul_0x20_disi": {
            **_medyan_ozeti([r for r in kos if r.get("kosulsuz_sinif") == "olculdu"],
                            "kayma_bps_kosulsuz"),
            "siniflar": {s: sum(1 for r in kos if r.get("kosulsuz_sinif") == s)
                         for s in ("olculdu", "dokunus_yok", "sonraki_yok")},
            "beyan": "kosul & 0x20 kayıtları seans listesinden çıkarılıp dokunuş/dolum YENİDEN arandı"},
        "dokunus_ani_spread_bps": {
            **(_dagilim(spread) or {"n": 0}),
            "kotasyon_yok_ya_da_tek_yanli_n": sum(1 for r in olculen if r.get("spread_bps") is None),
            "beyan": "(k_satis − k_alis) / eff_stop × 1e4, dokunuş kaydının işlem-anı kotasyonu"},
        "yil_kirilimi": {k: _dagilim(v) for k, v in sorted(yil.items())},
        "fiyat_kovasi_kirilimi": {k: _dagilim(v) for k, v in kova.items()},
        "en_yakin_edg045_hucresi": en_yakin_hucre(medyan),
        "olcek_uyumlu_altkume": {
            **_medyan_ozeti(olcek_ok, "kayma_bps"),
            "olcek_uyumsuz_n": sum(1 for r in olculen if r.get("olcek_uyumsuz") is True),
            "olcek_olculemedi_n": sum(1 for r in olculen if r.get("olcek_uyumsuz") is None),
            "beyan": ("KARTA EK TANI: bar split-düzeltmeli, tik ham; olcek_orani = bar close / tik seans "
                      f"son fiyatı, {OLCEK_BANDI} dışı → olcek_uyumsuz")},
        "saf_ters_izgara_kilitsiz": {
            **_medyan_ozeti([r for r in uygun if r.get("saf_ters_sinif") == "olculdu"],
                            "kayma_bps_saf_ters"),
            "dokunus_degisen_n": sum(1 for r in uygun if r.get("saf_ters_dokunus_farkli")),
            "beyan": "eff_stop her satırda exit/(1−s); ızgara kilidinin etkisini gösterir"},
    }


def ozetle(satirlar: list, oz_sinama: dict, pk1: dict) -> dict:
    """Satır sonuçlarından kartın kestirimi, kill-list ve karar. `satirlar[i]`: sinif, seans, kayma_bps,
    eff_stop (+ tanı alanları)."""
    siniflar: dict[str, int] = {}
    for r in satirlar:
        siniflar[r["sinif"]] = siniflar.get(r["sinif"], 0) + 1
    for s in ("olculdu", "dokunus_yok", "sonraki_yok", "ters_red", "yon_disi", "tarih_okunamadi"):
        siniflar.setdefault(s, 0)
    uygun = [r for r in satirlar if r["sinif"] in ("olculdu", "dokunus_yok", "sonraki_yok")]
    olculen = [r for r in satirlar if r["sinif"] == "olculdu"]
    oran = (siniflar["dokunus_yok"] / len(uygun)) if uygun else None
    seanslar: dict[str, list] = {}
    for r in olculen:
        seanslar.setdefault(r["seans"], []).append(r["kayma_bps"])
    n, n_seans = len(olculen), len(seanslar)
    pay = (max(len(v) for v in seanslar.values()) / n) if n else None
    kill = {"oz_sinama_gecti": bool(oz_sinama.get("gecti")),
            "dokunus_yok_orani": _r3(oran * 100) if oran is not None else None,
            "dokunus_yok_asimi": (oran > DOKUNUS_YOK_TAVAN) if oran is not None else None,
            "tek_seans_asimi": (pay > TEK_SEANS_TAVAN) if pay is not None else None,
            "kosul_birincilde": False,
            "pk1_gecti": bool(pk1.get("gecti"))}
    engeller = []
    if not kill["pk1_gecti"]:
        engeller.append("GECERSIZ: PK-1 (kimlik) düştü — kart: hiçbir sayı yayılmaz")
    if not kill["oz_sinama_gecti"]:
        engeller.append(f"GECERSIZ: kill-1 öz-sınama < {OZ_SINAMA_ALT} tutarlı satır — ölçüm geçersiz")
    if kill["dokunus_yok_asimi"]:
        engeller.append(f"YAYIMLANMAZ: kill-2 dokunus_yok %{kill['dokunus_yok_orani']} > %20 — sınıf "
                        "incelenir")
    if n < N_UYGUN_ALT or n_seans < SEANS_ALT:
        engeller.append(f"OLCULEMEDI: n={n} (≥{N_UYGUN_ALT}) · seans={n_seans} (≥{SEANS_ALT}) eşiği")
    durum = engeller[0].split(":")[0] if engeller else "KOSULLU_HUKUM"
    out = {"siniflar": siniflar, "n_uygun": len(uygun), "n_olculen": n, "n_seans": n_seans,
           "tek_seans_payi": pay, "kill_list": kill, "durum": durum, "engeller": engeller,
           "medyan_bps": None, "ci95_bps": None, "karar": None, "ci_serh": None, "tanilar": None,
           "kosullar": []}
    if engeller:
        return out
    kumeler = list(seanslar.values())
    alt, ust = seans_kumeli_ci(kumeler, BOOT_B, BOOT_TOHUM)
    med = statistics.median([r["kayma_bps"] for r in olculen])
    out.update({"medyan_bps": med, "ci95_bps": [_r3(alt), _r3(ust)],
                "karar": karar_kurali(alt, ust),
                "bootstrap": {"B": BOOT_B, "seed": BOOT_TOHUM, "kumeleme": "seans (ts_close günü)",
                              "yontem": "EDG-042 betimleyici seans-kümeli yüzdelik bootstrap"}})
    if kill["tek_seans_asimi"]:
        out["ci_serh"] = (f"kill-3: tek seans ölçülen örneklemin %{_r3(pay * 100)}'ini taşıyor "
                          f"(> %10) — CI şerhsiz yayımlanmaz")
    out["kosullar"] = ["PK-2: --elle-ornek dilimleri Rol-1 tarafından parquet'ten elle doğrulanmadan "
                       "hiçbir sayı yayılmaz (kart pozitif_kontrol 2)"]
    if out["ci_serh"]:
        out["kosullar"].append(out["ci_serh"])
    out["tanilar"] = _tanilar(olculen, uygun, med)
    return out


# ── PK-1: çalışma anı kimlik kontrolü (gerçek veriden ÖNCE, aynı kodla) ────────────────────────────
def pk1_kimlik() -> dict:
    """Sentetik bir DST günü (2024-03-11, EDT) üzerinde: seans öncesi eşik-altı kayıt YOK sayılır,
    dolum = eff_stop → 0 bps, 12 bps enjeksiyon → 12 bps."""
    gun = dt.date(2024, 3, 11)
    a, _ = seans_siniri_ns(gun)
    stop = 50.0

    def akis(dolum):
        return [(a - 3600 * NS, 485_000, 100, 0, None, None),       # seans öncesi, eşik altı
                (a + 1 * NS, 503_000, 100, 0, None, None),
                (a + 2 * NS, 500_000, 100, 0, 499_900, 500_100),    # dokunuş = stop
                (a + 3 * NS, int(round(dolum * FIYAT_OLCEK)), 100, 0, None, None)]
    kimlik = dokunus_ve_dolum(seans_suz(akis(50.0), gun), stop)
    enj = dokunus_ve_dolum(seans_suz(akis(49.94), gun), stop)
    ileri = ileri_dolum(48.37, SLIP_BPS) == 48.3458
    gecti = (kimlik["sinif"] == "olculdu" and kimlik["kayma_bps"] == 0.0 and kimlik["dokunus_i"] == 1
             and enj["sinif"] == "olculdu" and abs(enj["kayma_bps"] - 12.0) < 1e-9 and ileri)
    return {"gecti": gecti, "kimlik_bps": kimlik["kayma_bps"], "enjeksiyon_bps": enj["kayma_bps"],
            "ileri_formul_ornek": ileri,
            "beyan": "sentetik 2024-03-11 (EDT) akışı; seans öncesi eşik-altı kayıt dokunuş SAYILMAMALI"}


# ── girdi (SQLite, salt-okur) ───────────────────────────────────────────────────────────────────────
def _db_ac(db: pathlib.Path) -> sqlite3.Connection:
    con = sqlite3.connect(db.resolve().as_uri() + "?mode=ro", uri=True)
    con.row_factory = lambda c, r: {d[0]: r[i] for i, d in enumerate(c.description)}
    return con


def _birlestir(ham: dict, sayac: dict) -> dict:
    """Tipli kolonlar + extra_json; extra KAZANIR (`meridian.storage._cols_to_row` semantiği)."""
    out = {k: v for k, v in ham.items() if k not in ("seq", "extra_json") and v is not None}
    raw = ham.get("extra_json")
    if raw:
        try:
            out.update(json.loads(raw))
        except json.JSONDecodeError:
            sayac["extra_json_bozuk"] += 1    # sessiz-yutma DEĞİL: sayılır, sonuc.json'a yazılır
    return out


def _kanonik(obj) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def girdi_oku(db: pathlib.Path) -> dict:
    sayac = {"extra_json_bozuk": 0}
    con = _db_ac(db)
    try:
        ham = con.execute("SELECT * FROM trades ORDER BY seq").fetchall()
        sql_n = con.execute("SELECT COUNT(*) AS n FROM trades WHERE kaynak = 'replay_seed' "
                            "AND exit_reason = 'stop'").fetchone()["n"]
        secili = []
        for h in ham:
            b = _birlestir(h, sayac)
            if b.get("kaynak") == "replay_seed" and b.get("exit_reason") == "stop":
                secili.append((h, b))
        plan_idler = sorted({b.get("plan_id") for _, b in secili if b.get("plan_id")})
        plan_ham = []
        tablo_var = con.execute("SELECT name FROM sqlite_master WHERE type='table' AND "
                                "name='trade_plans'").fetchone() is not None
        if tablo_var:
            for i in range(0, len(plan_idler), 500):
                parca = plan_idler[i:i + 500]
                plan_ham += con.execute(
                    f"SELECT * FROM trade_plans WHERE id IN ({','.join('?' for _ in parca)}) ORDER BY seq",
                    parca).fetchall()
    finally:
        con.close()
    planlar: dict[str, list] = {}
    for p in plan_ham:
        b = _birlestir(p, sayac)
        planlar.setdefault(b.get("id"), []).append(b.get("stop"))
    trades_bayt = _kanonik([h for h, _ in secili])
    plan_bayt = _kanonik(plan_ham)
    return {"secili": secili, "planlar": planlar, "trades_bayt": trades_bayt, "plan_bayt": plan_bayt,
            "ozet": {"n_trades_tum": len(ham), "n_trades_filtreli": len(secili), "sql_capraz_n": sql_n,
                     "n_plan_satiri": len(plan_ham), "trade_plans_tablosu": tablo_var,
                     "trades_sha256": hashlib.sha256(trades_bayt).hexdigest(),
                     "planlar_sha256": hashlib.sha256(plan_bayt).hexdigest(),
                     **sayac}}


# ── parquet okuyucuları ────────────────────────────────────────────────────────────────────────────
def _sema_kapisi(sema: dict, yol) -> None:
    for ad, beklenen in BEKLENEN_SEMA.items():
        gercek = _TIP_ESLEME.get(sema.get(ad, "YOK"))
        if gercek != beklenen:
            raise SemaHatasi(f"{yol}: sütun {ad!r} tipi {sema.get(ad, 'YOK')!r} — beklenen {beklenen} "
                             "(pilot ayristir şeması); birim/ölçek varsayımı geçersiz, ölçüm DURUR")


def _sema_pyarrow(yol) -> dict:
    import pyarrow.parquet as pq
    return {f.name: str(f.type) for f in pq.read_schema(str(yol))}


def _sema_duckdb(yol) -> dict:
    import duckdb
    con = duckdb.connect()
    try:
        lit = str(yol).replace("'", "''")
        return {r[0]: r[1] for r in con.execute(f"DESCRIBE SELECT * FROM read_parquet('{lit}')").fetchall()}
    finally:
        con.close()


def _oku_pyarrow(yol, semboller) -> list:
    import pyarrow as pa
    import pyarrow.compute as pc
    import pyarrow.parquet as pq
    t = pq.read_table(str(yol), columns=list(OKUNAN_SUTUNLAR))
    tip = t.schema.field("sembol").type
    t = t.filter(pc.is_in(t.column("sembol"), value_set=pa.array(sorted(semboller), type=tip)))
    kol = [t.column(ad).to_pylist() for ad in OKUNAN_SUTUNLAR]
    return list(zip(*kol))


def _oku_duckdb(yol, semboller) -> list:
    import duckdb
    con = duckdb.connect()
    try:
        lit = str(yol).replace("'", "''")
        yer = ",".join("?" for _ in semboller)
        return con.execute(f"SELECT {', '.join(OKUNAN_SUTUNLAR)} FROM read_parquet('{lit}', "
                           f"file_row_number=true) WHERE sembol IN ({yer}) ORDER BY file_row_number",
                           sorted(semboller)).fetchall()
    finally:
        con.close()


OKUYUCULAR = {"pyarrow": (_sema_pyarrow, _oku_pyarrow), "duckdb": (_sema_duckdb, _oku_duckdb)}


def gun_oku(yol, semboller, okuyucu: str) -> dict:
    """{sembol: [(ts, fiyat, lot, kosul, k_alis, k_satis), …]} — DOSYA SIRASIYLA."""
    sema_fn, oku_fn = OKUYUCULAR[okuyucu]
    _sema_kapisi(sema_fn(yol), yol)
    out: dict[str, list] = {s: [] for s in semboller}
    for sym, ts, fiyat, lot, kosul, ka, ks in oku_fn(yol, semboller):
        out[sym].append((ts, fiyat, lot, kosul, ka, ks))
    return out


# ── bar CSV ─────────────────────────────────────────────────────────────────────────────────────────
def bar_dosyasi(bar_kok: pathlib.Path, ticker: str) -> pathlib.Path:
    return bar_kok / f"{ticker.lower().replace('.', '-')}.csv"


def bar_oku(bar_kok: pathlib.Path, ticker: str, onbellek: dict) -> dict | None:
    if ticker in onbellek:
        return onbellek[ticker]
    yol = bar_dosyasi(bar_kok, ticker)
    if not yol.exists():
        onbellek[ticker] = None
        return None
    import csv
    seri = {}
    with yol.open(newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            seri[str(r.get("date", ""))[:10]] = {k: _sayi(r.get(k)) for k in ("open", "high", "low", "close")}
    onbellek[ticker] = seri
    return seri


# ── satır işleme ────────────────────────────────────────────────────────────────────────────────────
def satirlari_hazirla(girdi: dict) -> tuple[list, list]:
    """Tik öncesi sınıflama + eff_stop. Dönüş (satır sonuçları, öz-sınama çözümleri)."""
    out, cozumler = [], []
    for h, b in girdi["secili"]:
        tkr = str(b.get("ticker") or "").upper()
        r = {"seq": h.get("seq"), "id": b.get("id"), "plan_id": b.get("plan_id"), "ticker": tkr,
             "ts_close": b.get("ts_close"), "exit": b.get("exit"), "side": b.get("side"),
             "scaled_out": bool(b.get("scaled_out"))}
        try:
            gun = dt.date.fromisoformat(str(b.get("ts_close") or "")[:10])
        except ValueError:
            gun = None                         # sessiz-yutma DEĞİL: satır tarih_okunamadi sınıfına düşer
        if b.get("side") != "long":
            r.update(sinif="yon_disi", neden="ters formül yalnız long için okundu (motor side=long sabiti)")
        elif gun is None or not tkr:
            r.update(sinif="tarih_okunamadi", neden="ts_close/ticker çözülemedi")
        else:
            c = eff_stop_coz(b, girdi["planlar"].get(b.get("plan_id"), []), SLIP_BPS)
            cozumler.append(c)
            r.update(seans=gun.isoformat(), eff_stop=c["eff_stop"], ters=c["ters"],
                     eff_stop_kaynak=c["kaynak"], oz=c["oz"], plan_stop=c["plan_stop"])
            if c["red"]:
                r.update(sinif="ters_red", neden=c["oz"])
            else:
                r["sinif"] = None              # tik aşamasında belirlenir
        out.append(r)
    return out, cozumler


def _dilim(seans: list, dok_i: int, dol_i) -> list:
    a = max(0, dok_i - ELLE_PENCERE)
    b = min(len(seans), (dol_i if dol_i is not None else dok_i) + ELLE_PENCERE + 1)
    out = []
    for i in range(a, b):
        ts, fiyat, lot, kosul, ka, ks = seans[i]
        sn, kalan = divmod(ts, NS)
        et = dt.datetime.fromtimestamp(sn, tz=ET)
        out.append({"i": i, "ts_ns": ts, "et": f"{et:%H:%M:%S}.{kalan:09d}",
                    "fiyat": fiyat / FIYAT_OLCEK, "fiyat_ham": fiyat, "lot": lot, "kosul": kosul,
                    "rol": ("dokunus" if i == dok_i else "dolum" if i == dol_i else "")})
    return out


def satir_olc(r: dict, ham: list | None, bar: dict | None) -> None:
    """Tek uygun satırı tik akışında ölçer (sonuç `r`ye yazılır)."""
    gun = dt.date.fromisoformat(r["seans"])
    eff = r["eff_stop"]
    if ham is None:
        r.update(sinif="dokunus_yok", alt_neden="gun_dosyasi_yok", kayma_bps=None)
        seans = []
    else:
        seans = seans_suz(ham, gun)
        d = dokunus_ve_dolum(seans, eff)
        r.update(sinif=d["sinif"], kayma_bps=d["kayma_bps"], tick_fill=d["tick_fill"],
                 alt_neden=d.get("alt_neden"), n_seans_kaydi=len(seans), n_seans_disi=len(ham) - len(seans))
        if d["dokunus_i"] is not None:
            dk = seans[d["dokunus_i"]]
            r["dokunus_ts_ns"] = dk[0]
            r["dokunus_fiyat"] = dk[1] / FIYAT_OLCEK
            ka, ks = dk[4], dk[5]
            r["spread_bps"] = ((ks - ka) / FIYAT_OLCEK / eff * 1e4
                               if ka and ks and ka > 0 and ks >= ka else None)
            r["dilim"] = _dilim(seans, d["dokunus_i"], d["dolum_i"])
            once = [x[1] for x in seans[:d["dokunus_i"]] if x[1] is not None]
            r["dokunus_oncesi_seans_min"] = (min(once) / FIYAT_OLCEK) if once else None
        # tanı (a): kosul & 0x20 dışı · tanı (f): saf ters formül
        kz = dokunus_ve_dolum([x for x in seans if not ((x[3] or 0) & KOSUL_TEK_LOT_BITI)], eff)
        r["kosulsuz_sinif"], r["kayma_bps_kosulsuz"] = kz["sinif"], kz["kayma_bps"]
        st = dokunus_ve_dolum(seans, r["ters"])
        r["saf_ters_sinif"], r["kayma_bps_saf_ters"] = st["sinif"], st["kayma_bps"]
        r["saf_ters_dokunus_farkli"] = st["dokunus_i"] != d["dokunus_i"]
    fiyatlar = [x[1] for x in seans if x[1] is not None]
    tmin = (min(fiyatlar) / FIYAT_OLCEK) if fiyatlar else None
    tum = [x[1] for x in (ham or []) if x[1] is not None]
    r["tik_gun_min_tum_kayitlar"] = (min(tum) / FIYAT_OLCEK) if tum else None
    tson = (fiyatlar[-1] / FIYAT_OLCEK) if fiyatlar else None
    b = (bar or {}).get(r["seans"])
    r["bar"] = b
    r["tik_seans_min"] = tmin
    r["pk3_bar_ayagi"] = (None if not b or b.get("low") is None
                          else b["low"] <= eff + ters_hata_siniri(SLIP_BPS))
    r["pk3_tick_ayagi"] = None if tmin is None else tmin <= eff
    r["pk3_tick_ayagi_gunluk"] = (None if r["tik_gun_min_tum_kayitlar"] is None
                                  else r["tik_gun_min_tum_kayitlar"] <= eff)
    oran = (b["close"] / tson) if (b and b.get("close") and tson) else None
    r["olcek_orani"] = _r3(oran) if oran is not None else None
    r["olcek_uyumsuz"] = None if oran is None else not (OLCEK_BANDI[0] <= oran <= OLCEK_BANDI[1])


def okuma_sinamasi(tick_kok: pathlib.Path, uygunlar: list, gunler: list, kapsam: dict,
                   okuyucu: str) -> dict:
    """Kuru adım: ÜRETİM okuyucusuyla (A1'de pyarrow) ilk mevcut günü gerçekten okur — şema değil,
    okuma YOLUNUN kendisi sınanır; süre tam koşumun kaba kestirimidir (× gün sayısı)."""
    for g in gunler:
        if g in kapsam["gun_dosyasi_yok"]:
            continue
        semboller = {r["ticker"] for r in uygunlar if r["seans"] == g}
        t0 = time.time()
        veri = gun_oku(tick_kok / f"{g}.parquet", semboller, okuyucu)
        gun = dt.date.fromisoformat(g)
        return {"gun": g, "sure_sn": round(time.time() - t0, 3),
                "bayt": (tick_kok / f"{g}.parquet").stat().st_size,
                "sembol": {s: {"kayit": len(v), "seans_kaydi": len(seans_suz(v, gun))}
                           for s, v in sorted(veri.items())}}
    return {"gun": None, "neden": "okunabilir gün dosyası yok"}


def pk3_ozeti(uygun: list) -> dict:
    return {"bar_ayagi_tutarsiz": sum(1 for r in uygun if r.get("pk3_bar_ayagi") is False),
            "bar_ayagi_olculemedi": sum(1 for r in uygun if r.get("pk3_bar_ayagi") is None),
            "tick_ayagi_tutarsiz": sum(1 for r in uygun if r.get("pk3_tick_ayagi") is False),
            "tick_ayagi_olculemedi": sum(1 for r in uygun if r.get("pk3_tick_ayagi") is None),
            "tick_ayagi_gunluk_tutarsiz": sum(1 for r in uygun if r.get("pk3_tick_ayagi_gunluk") is False),
            "tutarsiz_satirlar": [{"ticker": r["ticker"], "seans": r["seans"], "eff_stop": r["eff_stop"],
                                   "bar_low": (r.get("bar") or {}).get("low"),
                                   "tik_seans_min": r.get("tik_seans_min"), "sinif": r["sinif"]}
                                  for r in uygun if r.get("pk3_bar_ayagi") is False
                                  or r.get("pk3_tick_ayagi") is False],
            "durum": ("tutarsizlik_yok" if not any(r.get("pk3_bar_ayagi") is False
                                                   or r.get("pk3_tick_ayagi") is False for r in uygun)
                      else "tutarsiz_satir_var"),
            "beyan": ("kart: 'tutarsız satır sayılır ve raporlanır' — sayısal düşme eşiği kartta YOK; "
                      "hüküm Rol-1'in. Bar ayağı ters toleransıyla (+0,5e-4/(1−s)); tik ayağı seans "
                      "(09:30–16:00 ET) minimumu, dokunuşla aynı pencere. Kartın 'tick günlük min' "
                      "ifadesinin harfî okuması (seans dışı dahil TÜM kayıtlar) ayrıca "
                      "tick_ayagi_gunluk_tutarsiz olarak sayılır — ikisinin farkı seans dışı dokunuştur")}


def pk2_ornekler(olculen: list, n: int, tick_kok: pathlib.Path) -> list:
    if n <= 0 or not olculen:
        return []
    sirali = sorted(olculen, key=lambda r: (r["seans"], r["ticker"], r["seq"] or 0))
    secim = random.Random(BOOT_TOHUM).sample(sirali, min(n, len(sirali)))
    out = []
    for r in sorted(secim, key=lambda r: (r["seans"], r["ticker"])):
        a, k = seans_siniri_ns(dt.date.fromisoformat(r["seans"]))
        yol = tick_kok / f"{r['seans']}.parquet"
        out.append({"ticker": r["ticker"], "seans": r["seans"], "exit": r["exit"],
                    "eff_stop": r["eff_stop"], "eff_stop_kaynak": r["eff_stop_kaynak"],
                    "tick_fill": r["tick_fill"], "kayma_bps": r["kayma_bps"],
                    "dokunus_oncesi_seans_min": r.get("dokunus_oncesi_seans_min"),
                    "seans_ns": [a, k], "dilim": r.get("dilim"),
                    "elle_tarif": (
                        "python -c \"import pyarrow.parquet as pq, pyarrow.compute as pc; "
                        f"t=pq.read_table('{yol}', columns=['ts','sembol','fiyat','lot','kosul']); "
                        f"t=t.filter(pc.equal(t['sembol'], '{r['ticker']}')); "
                        f"t=t.filter(pc.and_(pc.greater_equal(t['ts'], {a}), pc.less(t['ts'], {k}))); "
                        f"t=t.sort_by('ts'); e={r['eff_stop']!r}*10000; "
                        "i=next(j for j,v in enumerate(t['fiyat'].to_pylist()) if v<=e); "
                        "print('dokunus', t.slice(i,1).to_pylist(), 'dolum', t.slice(i+1,1).to_pylist())\"")})
    return out


# ── koruma ve çıktı ─────────────────────────────────────────────────────────────────────────────────
def _icinde(yol: pathlib.Path, kok: pathlib.Path) -> bool:
    y, k = yol.resolve(), kok.resolve()
    return y == k or k in y.parents


def _yaz(yol: pathlib.Path, veri: bytes) -> None:
    yol.write_bytes(veri)


def _json(obj) -> bytes:
    return (json.dumps(obj, ensure_ascii=False, indent=1) + "\n").encode("utf-8")


def _arac_kunyesi(okuyucu: str) -> dict:
    kaynak = pathlib.Path(__file__).read_bytes()
    surum = None
    if okuyucu == "pyarrow":
        import pyarrow
        surum = pyarrow.__version__
    else:
        import duckdb
        surum = duckdb.__version__
    return {"betik": "research/olcumler/edg102_stop_kayma/olcum.py", "surum": ARAC_SURUMU,
            "betik_sha256": hashlib.sha256(kaynak).hexdigest(), "python": platform.python_version(),
            "okuyucu": okuyucu, "okuyucu_surumu": surum,
            "utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}


def _ozet_md(s: dict) -> str:
    o, g, oz, pk = s["ozet"], s["girdi"], s["oz_sinama"], s["pk"]
    L = [f"# {KART_ID} — replay stop kayması (tick) · ölçüm özeti",
         "", f"Araç: `{s['arac']['betik']}` sürüm {s['arac']['surum']} · sha256 `{s['arac']['betik_sha256']}` · "
         f"okuyucu {s['arac']['okuyucu']} {s['arac']['okuyucu_surumu']} · {s['arac']['utc']}",
         "", "Bu belge HÜKÜM DEĞİLDİR: karar kuralının çıktısıdır; hükmü Rol-1 karta + K defterine işler.",
         "", "## Girdi (içerik-adresli)",
         f"- trades (replay_seed ∧ stop): n={g['n_trades_filtreli']} (SQL çapraz: {g['sql_capraz_n']}) · "
         f"sha256 `{g['trades_sha256']}`",
         f"- plan satırı: {g['n_plan_satiri']} · sha256 `{g['planlar_sha256']}` · extra_json bozuk: "
         f"{g['extra_json_bozuk']}",
         "", "## Öz-sınama (kill-1)",
         f"- tutarlı {oz['tutarli_n']} / eşik {oz['esik']} → {'GEÇTİ' if oz['gecti'] else 'DÜŞTÜ'}",
         "- " + " · ".join(f"{k}={oz[k]}" for k in OZ_SINIFLARI),
         "", "## Sınıflar",
         "- " + " · ".join(f"{k}={v}" for k, v in o["siniflar"].items()),
         f"- uygun={o['n_uygun']} · ölçülen={o['n_olculen']} · seans={o['n_seans']} · "
         f"dokunus_yok oranı=%{o['kill_list']['dokunus_yok_orani']} · tek seans payı="
         f"{_r3(o['tek_seans_payi'] * 100) if o['tek_seans_payi'] is not None else None}%",
         "", "## Sonuç",
         f"- DURUM: **{o['durum']}**"]
    for e in o["engeller"]:
        L.append(f"- engel: {e}")
    if o["medyan_bps"] is not None:
        L += [f"- medyan kayma: **{_r3(o['medyan_bps'])} bps** · %95 CI {o['ci95_bps']} (seans-kümeli, "
              f"B={BOOT_B}, seed={BOOT_TOHUM})",
              f"- KARAR KURALI: **{o['karar']}** (model varsayımı {MODEL_VARSAYIMI_BPS:g} bps)"]
        for k in o["kosullar"]:
            L.append(f"- koşul: {k}")
    L += ["", "## Pozitif kontrol",
          f"- PK-1 kimlik (çalışma anı): {'GEÇTİ' if pk['pk1']['gecti'] else 'DÜŞTÜ'}",
          f"- PK-2 elle: {pk['pk2']['durum']} ({len(pk['pk2']['ornekler'])} örnek, aşağıda)",
          f"- PK-3 bar çaprazı: {pk['pk3']['durum']} · bar ayağı tutarsız {pk['pk3']['bar_ayagi_tutarsiz']} "
          f"(ölçülemedi {pk['pk3']['bar_ayagi_olculemedi']}) · tik ayağı tutarsız "
          f"{pk['pk3']['tick_ayagi_tutarsiz']} (ölçülemedi {pk['pk3']['tick_ayagi_olculemedi']})"]
    if o["tanilar"]:
        t = o["tanilar"]
        L += ["", "## Tanılar (hüküm değil)",
              f"- (a) kosul&0x20 dışı: {t['kosul_0x20_disi']['medyan_bps']} bps "
              f"(n={t['kosul_0x20_disi']['n_olculen']})",
              f"- (b) dokunuş anı spread: {json.dumps(t['dokunus_ani_spread_bps'], ensure_ascii=False)}",
              f"- (c) yıl: {json.dumps(t['yil_kirilimi'], ensure_ascii=False)}",
              f"- (c) fiyat kovası: {json.dumps(t['fiyat_kovasi_kirilimi'], ensure_ascii=False)}",
              f"- (d) EDG-045 en yakın hücre: {json.dumps(t['en_yakin_edg045_hucresi'], ensure_ascii=False)}",
              f"- (e) ölçek-uyumlu altküme: {json.dumps(t['olcek_uyumlu_altkume'], ensure_ascii=False)}",
              f"- (f) saf ters (ızgara kilitsiz): {json.dumps(t['saf_ters_izgara_kilitsiz'], ensure_ascii=False)}"]
    L += ["", "## PK-2 elle doğrulama örnekleri",
          "Her örnekte: dokunuş = seanstaki İLK fiyat ≤ eff_stop; dolum = hemen sonraki kayıt. Tarif satırı "
          "A1'de pilot-venv ile koşulur ve betik çıktısıyla karşılaştırılır."]
    for x in pk["pk2"]["ornekler"]:
        L += ["", f"### {x['ticker']} {x['seans']} · eff_stop {x['eff_stop']} ({x['eff_stop_kaynak']}) · "
                  f"tick_fill {x['tick_fill']} · kayma {_r3(x['kayma_bps'])} bps · dokunuş öncesi seans min "
                  f"{x['dokunus_oncesi_seans_min']}",
              "```"]
        for k in x["dilim"] or []:
            L.append(f"{k['i']:>6} {k['et']} {k['fiyat']:>12.4f} lot={k['lot']} kosul={k['kosul']} {k['rol']}")
        L += ["```", f"`{x['elle_tarif']}`"]
    return "\n".join(L) + "\n"


def olc(db, tick_kok, bar_kok, cikti, elle_ornek=5, kuru=False, okuyucu="pyarrow") -> int:
    db, tick_kok, bar_kok, cikti = map(pathlib.Path, (db, tick_kok, bar_kok, cikti))
    for kok in (db.parent, tick_kok.parent, bar_kok):
        if _icinde(cikti, kok):
            print(f"RED: --cikti {cikti} girdi ağacının içinde ({kok}) — çıktı yalnız ayrı bir dizine yazılır")
            return 2
    hedef = cikti / ("kuru.json" if kuru else "sonuc.json")
    if hedef.exists():
        print(f"RED: {hedef} zaten var — dondurulmuş ölçümün üstüne yazılmaz; yeni bir --cikti ver")
        return 2
    if not db.exists():
        print(f"RED: --db {db} yok")
        return 2
    if okuyucu == "pyarrow":
        try:
            import pyarrow.parquet  # noqa: F401
        except ImportError:
            print("RED: pyarrow yok — A1 sözleşmesi pilot-venv'dir; yerel çivi yolu için AÇIKÇA "
                  "--okuyucu duckdb verilir (sessiz geri düşüş yok)")
            return 2
    t0 = time.time()
    pk1 = pk1_kimlik()
    cikti.mkdir(parents=True, exist_ok=True)
    arac = _arac_kunyesi(okuyucu)
    if not pk1["gecti"]:
        _yaz(hedef, _json({"kart": KART_ID, "arac": arac, "pk": {"pk1": pk1},
                           "ozet": {"durum": "GECERSIZ", "engeller": ["PK-1 düştü — gerçek veriye "
                                                                     "dokunulmadı"]}}))
        print("GECERSIZ: PK-1 çalışma anı kimlik kontrolü düştü — gerçek veriye dokunulmadı")
        return 4
    girdi = girdi_oku(db)
    _yaz(cikti / "girdi_trades.json", girdi["trades_bayt"])
    _yaz(cikti / "girdi_planlar.json", girdi["plan_bayt"])
    satirlar, cozumler = satirlari_hazirla(girdi)
    oz = oz_sinama_ozeti(cozumler)
    uygunlar = [r for r in satirlar if r["sinif"] is None]
    gunler = sorted({r["seans"] for r in uygunlar})
    print(f"{KART_ID}: girdi {girdi['ozet']['n_trades_filtreli']} satır (SQL {girdi['ozet']['sql_capraz_n']}) · "
          f"uygun {len(uygunlar)} · {len(gunler)} seans · öz-sınama tutarlı {oz['tutarli_n']} → "
          f"{'GEÇTİ' if oz['gecti'] else 'DÜŞTÜ'}", flush=True)
    bar_onb: dict = {}
    if kuru:
        kapsam = {"gun_dosyasi_yok": [], "sema_uygun_gun": 0, "sema_hatasi": [],
                  "bar_dosyasi_yok": sorted({r["ticker"] for r in uygunlar
                                             if bar_oku(bar_kok, r["ticker"], bar_onb) is None}),
                  "bar_gunu_yok": sum(1 for r in uygunlar
                                      if (bar_oku(bar_kok, r["ticker"], bar_onb) or {}).get(r["seans"]) is None)}
        for g in gunler:
            yol = tick_kok / f"{g}.parquet"
            if not yol.exists():
                kapsam["gun_dosyasi_yok"].append(g)
                continue
            try:
                _sema_kapisi(OKUYUCULAR[okuyucu][0](yol), yol)
                kapsam["sema_uygun_gun"] += 1
            except SemaHatasi as e:
                kapsam["sema_hatasi"].append(str(e))   # sessiz-yutma DEĞİL: kuru adımın ölçtüğü şey budur
        okuma = okuma_sinamasi(tick_kok, uygunlar, gunler, kapsam, okuyucu)
        rapor = {"kart": KART_ID, "kip": "kuru", "arac": arac, "girdi": girdi["ozet"], "oz_sinama": oz,
                 "pk1": pk1, "siniflar_tik_oncesi": {s: sum(1 for r in satirlar if r["sinif"] == s)
                                                     for s in ("yon_disi", "tarih_okunamadi", "ters_red")},
                 "uygun_n": len(uygunlar), "seans_n": len(gunler), "kapsam": kapsam,
                 "okuma_sinamasi": okuma,
                 "scaled_out_n": sum(1 for r in satirlar if r["scaled_out"]),
                 "sure_sn": round(time.time() - t0, 1)}
        _yaz(hedef, _json(rapor))
        print(f"KURU: gün dosyası yok {len(kapsam['gun_dosyasi_yok'])} · şema uygun {kapsam['sema_uygun_gun']} · "
              f"şema hatası {len(kapsam['sema_hatasi'])} · bar dosyası yok {len(kapsam['bar_dosyasi_yok'])} · "
              f"okuma sınaması {okuma.get('gun')} {okuma.get('sure_sn')} sn → {hedef}")
        return 0
    try:
        for g in gunler:
            gun_r = [r for r in uygunlar if r["seans"] == g]
            yol = tick_kok / f"{g}.parquet"
            veri = gun_oku(yol, {r["ticker"] for r in gun_r}, okuyucu) if yol.exists() else None
            for r in gun_r:
                satir_olc(r, None if veri is None else veri.get(r["ticker"], []),
                          bar_oku(bar_kok, r["ticker"], bar_onb))
            print(f"  {g}: {len(gun_r)} satır · {'dosya yok' if veri is None else 'okundu'}", flush=True)
    except SemaHatasi as e:
        print(f"ŞEMA KAPISI: {e}")
        return 3
    ozet = ozetle(satirlar, oz, pk1)
    olculen = [r for r in satirlar if r["sinif"] == "olculdu"]
    uygun = [r for r in satirlar if r["sinif"] in ("olculdu", "dokunus_yok", "sonraki_yok")]
    pk = {"pk1": pk1,
          "pk2": {"durum": "ROL1_ELLE_DOGRULAMA_BEKLIYOR", "n_istenen": elle_ornek,
                  "ornekler": pk2_ornekler(olculen, elle_ornek, tick_kok)},
          "pk3": pk3_ozeti(uygun)}
    sonuc = {"kart": KART_ID, "arac": arac, "girdi": girdi["ozet"], "oz_sinama": oz, "ozet": ozet, "pk": pk,
             "scaled_out_n": sum(1 for r in satirlar if r["scaled_out"]),
             "sure_sn": round(time.time() - t0, 1),
             "satirlar": [{k: v for k, v in r.items() if k != "dilim"} for r in satirlar]}
    _yaz(cikti / "OZET.md", _ozet_md(sonuc).encode("utf-8"))
    _yaz(hedef, _json(sonuc))
    med = _r3(ozet["medyan_bps"]) if ozet["medyan_bps"] is not None else None
    print(f"DURUM {ozet['durum']} · n={ozet['n_olculen']} seans={ozet['n_seans']} · medyan {med} bps · "
          f"CI {ozet['ci95_bps']} · KARAR {ozet['karar']} · → {hedef}")
    for e in ozet["engeller"]:
        print(f"  engel: {e}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=f"{KART_ID} replay stop kayması (tick) ölçümü — salt-okur")
    ap.add_argument("--db", required=True, help="meridian.db (salt-okur açılır)")
    ap.add_argument("--tick-kok", required=True, help="islem/<YYYY-MM-DD>.parquet dizini")
    ap.add_argument("--bar-kok", required=True, help="bar CSV dizini (state/bars)")
    ap.add_argument("--cikti", required=True, help="çıktı dizini — yazım YALNIZ burada")
    ap.add_argument("--elle-ornek", type=int, default=5, help="PK-2 örnek sayısı (0 = kapalı)")
    ap.add_argument("--kuru", action="store_true", help="tik okumadan kapsam + öz-sınama")
    ap.add_argument("--okuyucu", choices=sorted(OKUYUCULAR), default="pyarrow")
    a = ap.parse_args(argv)
    return olc(a.db, a.tick_kok, a.bar_kok, a.cikti, a.elle_ornek, a.kuru, a.okuyucu)


if __name__ == "__main__":
    sys.exit(main())
