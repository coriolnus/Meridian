#!/usr/bin/env python3
"""EDG-2026-106 — replay girişlerini koda sadık canlı giriş kuralıyla, BÖLÜNME YENİDEN ÖLÇEKLEMELİ tick arşivinde yeniden
yürütme · ölçüm betiği (TSK-224 tur 3, 2026-09-25).

KART: research/cards/EDG-2026-106-replay-giris-canli-kural-tick-olcekli.yaml — hipotez, eşik, kill-list, pozitif kontrol
ORADA DONUK. Selef EDG-2026-105 koşuldu, kill-3 doğru ateşledi (%7,177 > %5): bar CSV'leri geriye dönük BÖLÜNME-DÜZELTMELİ,
tick arşivi HAM. Bu betik plan tarafı fiyatları tick'in ham ölçeğine basit kesir çarpanıyla çevirir. Selefin betiği
(research/olcumler/edg105_giris_kurali/olcum.py) DOKUNULMAZ — EDG-105 kartı o betiğin blob'una bağlıdır; ondan devralınan
tanımlar `EDG105_KOPYA_TANIMLAR`da ve v551'de AST ayrışma çivisiyle bağlıdır. Betik karta DOKUNMAZ ve HÜKÜM İŞLEMEZ.
Çivi dosyası: tests/test_edg106_giris_kurali_v551.py.

SÖZLEŞME KOMUT SATIRIDIR (A1, Rol-1, salt-okur, DAĞITIMSIZ — betik stdin'den TEK DOSYA koşar):
  ssh … "/opt/veri/pilot-venv/bin/python - --betik-sha256 <yerel sha256> --db /opt/meridian/state/meridian.db \\
      --tick-kok /opt/veri/tick/islem --bar-kok /opt/meridian/state/bars --cikti <dizin> [--kuru] \\
      [--elle-ornek N]" < research/olcumler/edg106_giris_kurali/olcum.py
  --kuru            birincil HESAPLANMAZ: TÜM gün dosyaları okunur (ölçek ilk tik gerektirir) → f dağılımı, eşlenemez /
                    parite dışı / ölçülemeyen sayıları, monotonluk ihlalleri, beklenen kill-3 payı (kart ADIM-0 4/836 ile
                    yan yana), plan anı tip dağılımı, erken kapanış, öz-sınama, PK-1 → <cikti>/kuru.json. DOLAN/DOLMAZ YOK.
  --elle-ornek N    PK-2: ≥ 4 GAP, varsa STOP-LIMIT, varsa ≥ 1 DOLMAZ, varsa ≥ 1 f ≠ 1 satır; YALNIZ yayımlanan durumda.
  --okuyucu duckdb  yerel çivi yolu (pyarrow yoksa SESSİZ geri düşüş yok). --betik-sha256: stdin kipinde ZORUNLU beyan.
Çıkış kodu: 0 tamam (hüküm durumu sonuc.json `ozet.durum`da) · 2 kullanım/koruma reddi · 3 parquet şema kapısı ·
4 PK-1 (çalışma anı kimlik) düştü — gerçek veriye dokunulmadı.

BAĞIMLILIK: yalnız stdlib (fractions dahil) + pyarrow; `meridian` İÇE AKTARILMAZ (CLAUDE.md §2 — obs yazımı); motorla
aynılık v551'de. Veritabanı `file:…?mode=ro`. YAZIM YALNIZ `--cikti` ALTINDA.

════════ SABİTLER (EDG-105 ile AYNEN; sembol çapaları) ════════
  09:45 ET ← `meridian.barclock.ENTRY_WINDOW_ET_MIN` · emir tipi ← `meridian.broker.entry_order_decision` (ref = plan
  günü kapanışı, `meridian.loop.daily_cycle`) · L canlı ÇİFT yuvarlama: `meridian.broker.entry_limit_price` → karar
  `round(·, 4)` → `meridian.adapters.alpaca.submit_bracket` `round(·, 2)` · replay dolumu
  `meridian.broker.PaperBroker.fill_entry` · erken kapanış listesi EDG-105 (kart adim_0) DONUK.

════════ ÖLÇEK EŞLEME (YENİ) → `olcek_esle`, `olcekle` ════════
  r = giriş günü bar açılışı / o günün ilk normal-seans tick fiyatı. F = {1} ∪ {1/k : k=2..30} ∪ {k : k=2..10} ∪
  {2/3, 3/4, 4/5, 3/2, 4/3, 5/4} (`OLCEK_KUMESI`). f = F'de r'ye |r/f − 1| ölçüsüyle EN YAKIN öğe, sapma ≤ %2
  (`OLCEK_TOL`, sınır DAHİL) ise; yoksa `olcek_eslenemez` (alt neden kesir_disi). Hepsi `fractions.Fraction` ile TAM:
  plan fiyatı ONDALIK gösteriminden kesre çevrilir (`_kesir` — `Fraction(1.07)` ikili artığı taşır ve 1,07 ÷ 1/10'u
  10,700000000000001 yapardı), tick 1e-4 tamsayıdan. İki aday birden %2 içindeyse en yakın seçilir, ikincisi
  `olcek_ikinci_aday` alanına yazılır (yalnız 1/26–1/30 bölgesinde mümkün).
  Parite: plan günü kapanışı / tetik ∉ [0,9; 1,1] → `olcek_parite_disi` (plan fiyatları bar ölçeğinde değil; GE sınıfı).
  Monotonluk (kill-4, `monotonluk_uygula`): ticker başına f'ler tarih sırasıyla ya hep ≤ ya hep ≥ (tek yön) olmalı; değilse o
  ticker'ın TÜM f ≠ 1 satırları `olcek_eslenemez` (alt neden monotonluk_ihlali) — sonuç alanları silinir.
  Yeniden ölçekleme: tetik, trades.entry, plan günü kapanışı ve bar değerleri ÷ f ile HAM birime (`*_tik` alanları); L ham
  birimde canlı çift yuvarlama zinciriyle (`limit_fiyati(tetik_tik)` — canlı emir o gün ham fiyatla verilirdi);
  fark_bps birimsiz. f = 1 satırlar EDG-105 yoluyla BAYT-ÖZDEŞ geçer (v551 satır-düzeyi çivi).

════════ ÖYKÜNÜCÜ (EDG-105 AYNEN — `canli_kural`) ════════
  t0 = ts ≥ 09:45 ET ilk kayıt; tip = plan günü kapanışı ≥ tetik ? GAP : STOP-LIMIT; GAP → t0'dan SONRAKİ ilk ≤ L kayıt;
  STOP-LIMIT → aktivasyon ≥ tetik, dolum aktivasyondan SONRAKİ ilk ≤ L kayıt; 16:00'a dek yoksa DOLMAZ; t0 yoksa akis_yok.

════════ PAYDALAR (`PAYDALAR`) ve KILL-LIST ════════
  kill-1 öz-sınama · kill-2 akis_yok / aday > %10 · kill-3 (olcek_eslenemez + olcek_parite_disi + olcek_olculemedi) /
  (aday − akis_yok) > %5 → YAYIMLANMAZ · kill-4 monotonluk · kill-5 tek seans > %10 → CI şerhli · kill-6 kosul yalnız
  tanıda · kill-7 tip yalnız plan günü kapanışından · kill-8 PK ayakları. n ≥ 300 ∧ ≥ 100 seans her birincil kendi
  paydasında. H1 = DOLMAZ / (DOLMAZ + DOLAN) · H2 = DOLAN'da fark_bps medyanı; seans-kümeli bootstrap B=5000, seed=20260812.

════════ SONUÇ ALANI DİSİPLİNİ (tur 3) → `yayim_gorunumu` ════════
  Bir birincil yayımlanmıyorsa (engel ya da n eşiği) satır-düzeyi sonuç alanları (`SONUC_ALANLARI`: canli_dolum, fark_bps,
  tanı sonuçları, dilim …) sonuc.json'a YAZILMAZ; H1 yayımlanmıyorsa DOLAN/DOLMAZ satır sınıfları `BIRINCIL_GIZLI`
  maskelenir ve özet yalnız toplamı (`birincil_aday_n`) taşır; H2'nin n'i (DOLAN sayısı) de gizlenir; tanılar ve PK-2
  örnekleri yazılmaz; OZET.md ve stdout yalnız engel nedenini basar. `parmak_izi` gizlenmemiş iç sonucun sha256'sıdır
  (tersinmez; tam ↔ elle koşum eşitliği için).

════════ TANILAR ════════
  (a)–(h) EDG-105 AYNEN · (i) f ≠ 1 satırlar dışlanınca iki birincil (nokta) · (j) ölçek tablosu (f dağılımı, ticker × f).

ÇIKTILAR VE OKUYUCULARI (Yasa 6): sonuc.json + OZET.md → Rol-1 hükmü; girdi_*.json → girdi dondurması (sha256'lar
sonucta); kuru.json → kuru adımın Rol-1 okuması. DİSİPLİN: uydurma yasağı · Yasa 4 · git/state yazımı yok.
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
import re
import sqlite3
import statistics
import sys
import time
from fractions import Fraction
from zoneinfo import ZoneInfo

# ── KART SABİTLERİ (research/cards/EDG-2026-106-…yaml — v551 kartla birebir çiviler) ─────────────────
KART_ID = "EDG-2026-106"
ARAC_SURUMU = "1"
BETIK_YOLU = "research/olcumler/edg106_giris_kurali/olcum.py"
KAYNAK = "replay_seed"
N_UYGUN_ALT = 300                 # esikler.n_uygun_alt
SEANS_ALT = 100                   # esikler.seans_alt
DOLMAZ_ESIK_PCT = 5               # esikler.dolmaz_esik_pct (H1, yüzde)
FIYAT_BANDI_BPS = 5               # esikler.fiyat_bandi_bps (H2, ±bps)
OZ_SINAMA_ALT = 20                # kill-list 1 (EDG-105 AYNEN)
OZ_SINAMA_TOL_BPS = 1.0           # kill-list 1
AKIS_YOK_TAVAN = 0.10             # kill-list 2
OLCEK_DISLANAN_TAVAN = 0.05       # kill-list 3
TEK_SEANS_TAVAN = 0.10            # kill-list 5
TIP_KAYNAGI = "plan_gunu_kapanisi"  # kill-list 7
PK3_TUTARSIZ_TAVAN = 0.20         # pozitif_kontrol 3
PK2_GAP_ALT = 4                   # pozitif_kontrol 2 (EDG-105 AYNEN)
ACILIS_YAKIN_BPS = 0.5            # tanı (h): selef ADIM-0 kovası
BOOT_B = 5000                     # olcum_plani: B=5000
BOOT_TOHUM = 20260812             # olcum_plani: seed=20260812
KOSUL_TEK_LOT_BITI = 0x20         # tanı (e)
TETIK_REF_ESIT_TOL = 1e-4         # kuru adım: "kapanış == tetik (±1e-4)"
OLCEK_TOL_PCT = 2                 # esikler.olcek_eslem_tolerans_pct
OLCEK_TOL = Fraction(OLCEK_TOL_PCT, 100)
#: olcum_plani: F = {1} ∪ {1/k : k=2..30} ∪ {k : k=2..10} ∪ {2/3, 3/4, 4/5, 3/2, 4/3, 5/4} — TAM kesirler
OLCEK_KUMESI = tuple(sorted({Fraction(1)} | {Fraction(1, k) for k in range(2, 31)} | {Fraction(k) for k in range(2, 11)}
                            | {Fraction(2, 3), Fraction(3, 4), Fraction(4, 5), Fraction(3, 2), Fraction(4, 3),
                               Fraction(5, 4)}))
ADIM0_BEKLENEN_KILL3 = (4, 836)   # kart adim_0: "beklenen eşlenemez pay: 4 / 836 = %0,48"
#: EDG-105 kart adim_0: XNYS erken kapanış (13:00 ET) günleri 2022-01 → 2026-07 — DONUK (v551: kart = betik = mcal)
ERKEN_KAPANIS_GUNLERI = ("2022-11-25", "2023-07-03", "2023-11-24", "2024-07-03", "2024-11-29", "2024-12-24",
                         "2025-07-03", "2025-11-28", "2025-12-24")

# ── MOTOR SABİTLERİ (EDG-105 AYNEN; v551 motorla eşitliği çiviler) ────────────────────────────────────
GIRIS_PENCERE_ET_DK = 9 * 60 + 45   # meridian.barclock.ENTRY_WINDOW_ET_MIN
ACILIS_ET_DK = 9 * 60 + 30          # tanı (b)
LIMIT_PCT_CAP = 0.04                # state/goal.yaml execution_v2.limit_pct_cap
SLIP_BPS = 5.0                      # state/goal.yaml slippage_bps
KARAR_HANE = 4                      # meridian.broker.entry_order_decision: "limit": round(limit, 4)
KURUS_HANE = 2                      # meridian.adapters.alpaca.submit_bracket: round(float(entry_limit), 2)

FIYAT_OLCEK = 10_000              # pilot: fiyatlar 1e-4 tamsayı birim
NS = 1_000_000_000
ET = ZoneInfo("America/New_York")
SEANS_ACILIS = dt.time(9, 30)
SEANS_KAPANIS = dt.time(16, 0)
OLCEK_BANDI = (0.9, 1.1)          # parite bandı: plan günü kapanışı / tetik ∈ [0,9; 1,1]
ELLE_PENCERE = 3
FIYAT_KOVALARI = ((0.0, 25.0), (25.0, 50.0), (50.0, 100.0), (100.0, 250.0), (250.0, math.inf))

KARAR_H1_IYIMSER = "REPLAY DOLUMU İYİMSER (canlıda dolmayan girişler)"
KARAR_H1_ESDEGER = "DOLUM EŞDEĞER"
KARAR_H2_IYIMSER = "REPLAY GİRİŞ FİYATI İYİMSER"
KARAR_H2_KOTUMSER = "REPLAY GİRİŞ FİYATI KÖTÜMSER"
KARAR_H2_ESDEGER = "GİRİŞ FİYATI EŞDEĞER (model yeterli)"
KARAR_BELIRSIZ = "BELİRSİZ"

ON_SINIFLAR = ("yon_disi", "tarih_okunamadi", "giris_okunamadi", "plan_yok", "plan_belirsiz", "tetik_okunamadi",
               "erken_kapanis")
OLCEK_SINIFLARI = ("olcek_eslenemez", "olcek_parite_disi", "olcek_olculemedi")
TIK_SINIFLARI = ("DOLAN", "DOLMAZ", "akis_yok") + OLCEK_SINIFLARI
GIZLI_SINIF = "BIRINCIL_GIZLI"
#: Birincilin sonucunu (ya da ondan türetilebilecek olanı) taşıyan satır alanları — yayımlanmayan durumda YAZILMAZ.
SONUC_ALANLARI = ("canli_dolum", "fark_bps", "oykunucu_sinif", "dolmaz_neden", "t930_sinif", "t930_dal", "t930_fark_bps",
                  "kosulsuz_sinif", "kosulsuz_fark_bps", "spread_bps", "dolum_ts_ns", "dolum_gecikme_dk", "akt_ts_ns",
                  "akt_gecikme_dk", "t0_sonrasi_max", "t0_sonrasi_min", "akt_sonrasi_min", "dilim")

CIKTI_DOSYALARI = ("sonuc.json", "OZET.md", "girdi_trades.json", "girdi_planlar.json")
KURU_DOSYALARI = ("kuru.json", "girdi_trades.json", "girdi_planlar.json")

PAYDALAR = {
    "aday": ("tik aşamasına giren satır = replay_seed girdisi − tik-öncesi sınıflar (yon_disi, tarih_okunamadi, "
             "giris_okunamadi, plan_yok, plan_belirsiz, tetik_okunamadi, erken_kapanis); bu sınıflar ayrıca sayılır"),
    "erken_kapanis": ("EDG-105 listesindeki XNYS 13:00 ET günlerinin girişleri birincilden DIŞLANIR ve sayılır; aday "
                      "değildir, kill-2/kill-3/PK-3 paylarına girmez"),
    "olcek_eslem": ("r = bar açılışı / ilk normal-seans tik; f = F'de |r/f − 1| ölçüsüyle en yakın öğe, ≤ %2 (dahil) "
                    "ise; hepsi Fraction ile TAM (plan fiyatı ondalık gösteriminden). f ≠ 1 satırlarda plan tarafı "
                    "÷ f ile ham birime, L ham birimde canlı çift yuvarlamayla"),
    "kill1_oz_sinama": ("SAYIM: |trades.entry − bar_açılış × (1 + 5 bps)| / entry × 1e4 ≤ 1 bps satır ≥ 20 (plan "
                        "biriminde — ölçekten bağımsız)"),
    "kill2_akis_yok": "akis_yok / aday; > %10 → iki birincil YAYIMLANMAZ",
    "kill3_olcek": ("(olcek_eslenemez + olcek_parite_disi + olcek_olculemedi) / (aday − akis_yok); > %5 → YAYIMLANMAZ. "
                    "Sınıf sırası: akis_yok → ref_yok / bar_acilis_yok (olculemedi) → kesir_disi (eslenemez) → "
                    "kapanis_tetik (parite_disi) → monotonluk_ihlali (eslenemez, ticker düzeyinde sonradan)"),
    "kill4_monoton": ("ticker başına f'ler tarih sırasıyla tek yönlü (hep ≤ ya da hep ≥) olmalı; değilse o ticker'ın "
                      "TÜM f ≠ 1 satırları (sınıfı ne olursa olsun) olcek_eslenemez olur ve sonuç alanları silinir"),
    "kill5_tek_seans": "her birincil KENDİ paydasında en kalabalık seansın payı > %10 → CI şerhli (düşürülmez)",
    "kill6_kosul": "yapısal: öykünücü zaman-tabanlı, kosul yalnız tanı (e)'de okunur — birincilde süzgeç YOK",
    "kill7_tip": "yapısal: emir tipi YALNIZ plan günü bar kapanışından (`emir_tipi`) — kill_list.tip_kaynagi",
    "kill8_pk": ("PK-1 çalışma anı kimlik (ölçek kimliği dahil; düşerse exit 4) · PK-2 Rol-1 elle (koşul) · PK-3 tutarsız "
                 "/ (ölçeği çözülmüş, paritede, ayakları ölçülebilen aday); > %20 ya da payda 0 → GECERSIZ"),
    "h1": "DOLMAZ / (DOLMAZ + DOLAN) × 100 — akis_yok, ölçek ve erken kapanış dışlamaları paydada YOK",
    "h2": "DOLAN satırlarda fark_bps = (canli_dolum − entry_tik) / entry_tik × 1e4 medyanı (aleyhte +, birimsiz)",
    "n_esigi": "her birincil KENDİ paydasında ≥ 300 satır ∧ ≥ 100 seans (H1: DOLAN + DOLMAZ; H2: DOLAN)",
    "gizlilik": ("bir birincil yayımlanmıyorsa satır sonuç alanları yazılmaz; H1 yayımlanmıyorsa DOLAN/DOLMAZ sınıfları "
                 "maskelenir ve özette yalnız birincil_aday_n kalır; stdout/OZET.md yalnız engel nedenini basar"),
}

OKUNAN_SUTUNLAR = ("sembol", "ts", "fiyat", "lot", "kosul", "k_alis_fiyat", "k_satis_fiyat")
BEKLENEN_SEMA = {"ts": "i64", "sembol": "str", "fiyat": "i64", "lot": "i32", "kosul": "u8",
                 "k_alis_fiyat": "i64", "k_satis_fiyat": "i64"}
_TIP_ESLEME = {"int64": "i64", "BIGINT": "i64", "int32": "i32", "INTEGER": "i32",
               "uint8": "u8", "UTINYINT": "u8", "string": "str", "large_string": "str",
               "VARCHAR": "str"}

# EDG-2026-102 betiğinden BİREBİR kopyalar — v551 ayrışma çivisi.
EDG102_KOPYA_TANIMLAR = ("SemaHatasi", "_sayi", "seans_siniri_ns", "seans_suz", "yuzdelik", "seans_kumeli_ci",
                         "_r3", "_dagilim", "_fiyat_kovasi", "_db_ac", "_birlestir", "_kanonik", "_sema_kapisi",
                         "_sema_pyarrow", "_sema_duckdb", "_oku_pyarrow", "_oku_duckdb", "gun_oku", "bar_dosyasi",
                         "bar_oku", "okuma_sinamasi", "_icinde", "_yaz", "_json")
EDG102_KOPYA_SABITLER = ("FIYAT_OLCEK", "NS", "ET", "SEANS_ACILIS", "SEANS_KAPANIS", "OLCEK_BANDI", "BOOT_B",
                         "BOOT_TOHUM", "OKUNAN_SUTUNLAR", "BEKLENEN_SEMA", "_TIP_ESLEME", "KOSUL_TEK_LOT_BITI",
                         "ELLE_PENCERE", "FIYAT_KOVALARI")
# EDG-2026-105 betiğinden (research/olcumler/edg105_giris_kurali/olcum.py, blob dd16ae6c) BİREBİR kopyalar — v551.
EDG105_KOPYA_TANIMLAR = ("limit_ham", "limit_karar", "limit_fiyati", "emir_tipi", "replay_giris", "oz_fark_bps",
                         "acilis_dali", "fark_bps", "pencere_ns", "t0_bul", "canli_kural", "seans_kumeli_oran_ci",
                         "karar_h1", "karar_h2", "_sayim", "_ikili", "_gruplu", "_pk3_satir", "oz_sinama_ozeti",
                         "_kumeler", "_birincil_iskelet", "_esik_engeli", "_h1_blok", "_h2_blok", "girdi_oku",
                         "satirlari_hazirla", "bar_alanlari", "_bantta", "_dilim", "_kaynak_sha256")
EDG105_KOPYA_SABITLER = ("KAYNAK", "N_UYGUN_ALT", "SEANS_ALT", "DOLMAZ_ESIK_PCT", "FIYAT_BANDI_BPS", "OZ_SINAMA_ALT",
                         "OZ_SINAMA_TOL_BPS", "AKIS_YOK_TAVAN", "OLCEK_DISLANAN_TAVAN", "TEK_SEANS_TAVAN",
                         "TIP_KAYNAGI", "PK3_TUTARSIZ_TAVAN", "PK2_GAP_ALT", "ACILIS_YAKIN_BPS", "TETIK_REF_ESIT_TOL",
                         "ERKEN_KAPANIS_GUNLERI", "GIRIS_PENCERE_ET_DK", "ACILIS_ET_DK", "LIMIT_PCT_CAP", "SLIP_BPS",
                         "KARAR_HANE", "KURUS_HANE", "KARAR_H1_IYIMSER", "KARAR_H1_ESDEGER", "KARAR_H2_IYIMSER",
                         "KARAR_H2_KOTUMSER", "KARAR_H2_ESDEGER", "KARAR_BELIRSIZ")


class SemaHatasi(RuntimeError):
    """Parquet şeması pilot sözleşmesinden saptı — birim/ölçek varsayımı çöker, ölçüm DURUR."""


def _sayi(x):
    """Sayıya çevrilebilen değer → float; değilse None (uydurma yok)."""
    if isinstance(x, bool) or x is None:
        return None
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


# ── motor formülleri (EDG-105 kopyaları) ──────────────────────────────────────────────────────────────
def limit_ham(tetik: float, cap: float = LIMIT_PCT_CAP) -> float:
    """Ham L = tetik + tetik·cap — `meridian.broker.entry_limit_price` (atr=None) ile AYNI float işlem sırası."""
    t = float(tetik)
    return t + t * float(cap)


def limit_karar(tetik: float, cap: float = LIMIT_PCT_CAP) -> float:
    """Karar sözlüğündeki L — `meridian.broker.entry_order_decision` `"limit": round(limit, 4)`."""
    return round(limit_ham(tetik, cap), KARAR_HANE)


def limit_fiyati(tetik: float, cap: float = LIMIT_PCT_CAP) -> float:
    """CANLI L = emir gövdesindeki `limit_price`: karar L'si (4 hane) kuruşa yuvarlanır (ÇİFT yuvarlama zinciri)."""
    return round(float(limit_karar(tetik, cap)), KURUS_HANE)


def emir_tipi(ref: float, tetik: float) -> str:
    """Plan anı emir tipi — `meridian.broker.entry_order_decision`: `gap = ref ≥ tetik` → GAP, aksi → STOP-LIMIT."""
    return "GAP" if ref >= tetik else "STOP_LIMIT"


def replay_giris(acilis: float, slip_bps: float = SLIP_BPS) -> float:
    """Replay dolumu: round(açılış × (1 + s), 4) — `meridian.broker.PaperBroker.fill_entry` + `close_position`."""
    s = slip_bps / 10000.0
    return round(acilis * (1.0 + s), 4)


def oz_fark_bps(entry: float, bar_acilis: float, slip_bps: float = SLIP_BPS) -> float:
    """Kill-1: |entry − bar_açılış × (1 + 5 bps)| / entry × 1e4."""
    return abs(entry - bar_acilis * (1.0 + slip_bps / 10000.0)) / entry * 1e4


def acilis_dali(entry: float, tetik: float, slip_bps: float = SLIP_BPS) -> tuple[float, str]:
    """Tanı (h): açılış ≈ entry / (1 + 5 bps); tetiğe göre ±0,5 bps → yakın, altı (gap-down), üstü."""
    acilis = entry / (1.0 + slip_bps / 10000.0)
    bps = (acilis - tetik) / tetik * 1e4
    if abs(bps) <= ACILIS_YAKIN_BPS:
        return bps, "acilis_yakin"
    return bps, ("acilis_alti" if bps < 0 else "acilis_ustu")


def fark_bps(canli: float, replay: float) -> float:
    """H2: (canli_dolum − trades.entry) / trades.entry × 1e4 — aleyhte (canlı pahalı) POZİTİF."""
    return (canli - replay) / replay * 1e4


# ── ölçek eşleme (YENİ) ──────────────────────────────────────────────────────────────────────────────
def _kesir(x) -> Fraction:
    """Plan fiyatının ONDALIK gösteriminden TAM kesir. Plan fiyatları ondalık değerlerdir (4 hane yuvarlı defter / CSV);
    `Fraction(float)` ikili artığı taşır ve ÷ f'de kuruş-altı sahte kayma üretir (1,07 ÷ 1/10 → 10,700000000000001)."""
    return Fraction(repr(float(x)))


def olcek_esle(bar_acilis, ilk_tik_ham) -> dict:
    """r = bar açılışı / ilk normal-seans tik (1e-4 tamsayı) → F'de |r/f − 1| ölçüsüyle en yakın f; sapma ≤ %2 (dahil)
    değilse f = None. Eşit uzaklıkta küçük f önce (sıralı demet). Hesap baştan sona Fraction ile TAM."""
    if not bar_acilis or bar_acilis <= 0 or not ilk_tik_ham or ilk_tik_ham <= 0:
        return {"f": None, "r": None, "sapma": None, "en_yakin": None, "ikinci_aday": None}
    r = _kesir(bar_acilis) / Fraction(int(ilk_tik_ham), FIYAT_OLCEK)
    adaylar = sorted((abs(r / f - 1), f) for f in OLCEK_KUMESI)
    sapma, en_yakin = adaylar[0]
    esli = sapma <= OLCEK_TOL
    ikinci = next((g for d, g in adaylar[1:] if d <= OLCEK_TOL), None) if esli else None
    return {"f": en_yakin if esli else None, "r": r, "sapma": sapma, "en_yakin": en_yakin, "ikinci_aday": ikinci}


def olcekle(x: float, f: Fraction) -> float:
    """Plan birimindeki fiyat → HAM (tick) birim: x ÷ f, ondalık-tam kesirle; f = 1'de x'in KENDİSİ (bayt-özdeş yol)."""
    if f == 1:
        return x
    return float(_kesir(x) / f)


# ── seans süzgeci, pencere ve koda sadık öykünücü ──────────────────────────────────────────────────
def seans_siniri_ns(gun: dt.date) -> tuple[int, int]:
    """[09:30, 16:00) ET → epoch ns; DST zoneinfo'dan."""
    a = dt.datetime.combine(gun, SEANS_ACILIS, tzinfo=ET)
    k = dt.datetime.combine(gun, SEANS_KAPANIS, tzinfo=ET)
    return int(a.timestamp()) * NS, int(k.timestamp()) * NS


def seans_suz(kayitlar: list, gun: dt.date) -> list:
    """kayıt = (ts, fiyat, lot, kosul, k_alis, k_satis), dosya sırasıyla. ts'e göre KARARLI sıralar ve
    normal seansı süzer. `kosul`a BAKMAZ (EDG-106 kill-list 6)."""
    a, k = seans_siniri_ns(gun)
    return sorted((r for r in kayitlar if a <= r[0] < k), key=lambda r: r[0])


def pencere_ns(gun: dt.date, dk: int = GIRIS_PENCERE_ET_DK) -> int:
    """Giriş penceresinin açılışı (ET duvar saati `dk` dakika) → epoch ns; DST zoneinfo'dan."""
    t = dt.datetime.combine(gun, dt.time(dk // 60, dk % 60), tzinfo=ET)
    return int(t.timestamp()) * NS


def t0_bul(seans: list, esik_ns: int):
    """ts ≥ eşik olan ilk FİYATLI kaydın indeksi; yoksa None."""
    return next((i for i, r in enumerate(seans) if r[0] >= esik_ns and r[1] is not None), None)


def canli_kural(seans: list, tetik: float, limit: float, esik_ns: int, ref: float) -> dict:
    """Koda sadık öykünücü (başlık). Tip YALNIZ `ref`ten (plan günü kapanışı) — `ref` zorunludur, varsayılanı YOK;
    p0 yalnız raporlanır. `seans` normal seans, ts'e göre kararlı sıralı. Fiyatsız kayıt atlanır."""
    t0 = t0_bul(seans, esik_ns)
    if t0 is None:
        return {"sinif": "akis_yok", "dal": None, "t0_i": None, "akt_i": None, "dolum_i": None,
                "p0": None, "canli_dolum": None, "neden": "pencere_sonrasi_kayit_yok"}
    out = {"t0_i": t0, "p0": seans[t0][1] / FIYAT_OLCEK, "akt_i": None, "dolum_i": None, "canli_dolum": None,
           "neden": None, "dal": emir_tipi(ref, tetik)}
    if out["dal"] == "GAP":
        bas = t0 + 1
    else:
        akt = next((i for i in range(t0, len(seans))
                    if seans[i][1] is not None and seans[i][1] / FIYAT_OLCEK >= tetik), None)
        if akt is None:
            return {**out, "sinif": "DOLMAZ", "neden": "tetik_kirilmadi"}
        out["akt_i"] = akt
        bas = akt + 1
    dol = next((i for i in range(bas, len(seans))
                if seans[i][1] is not None and seans[i][1] / FIYAT_OLCEK <= limit), None)
    if dol is None:
        return {**out, "sinif": "DOLMAZ",
                "neden": "sonraki_kayit_yok" if bas >= len(seans) else "limit_ici_kayit_yok"}
    return {**out, "sinif": "DOLAN", "dolum_i": dol, "canli_dolum": seans[dol][1] / FIYAT_OLCEK}


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


def seans_kumeli_oran_ci(kumeler: list, B: int = BOOT_B, tohum: int = BOOT_TOHUM) -> tuple:
    """H1: `seans_kumeli_ci` ile AYNI yeniden-örnekleme şeması (random.Random(tohum) · küme başına randrange);
    istatistik = havuzlanmış 0/1 satırların ortalaması × 100 (DOLMAZ = 1)."""
    rng = random.Random(tohum)
    oranlar = []
    for _ in range(B):
        secim = [x for _ in kumeler for x in kumeler[rng.randrange(len(kumeler))]]
        oranlar.append(sum(secim) / len(secim) * 100.0)
    oranlar.sort()
    return yuzdelik(oranlar, 0.025), yuzdelik(oranlar, 0.975)


def karar_h1(ci_alt: float, ci_ust: float, esik: float = DOLMAZ_ESIK_PCT) -> str:
    """Kart: CI-alt > 5 → İYİMSER · CI-üst ≤ 5 → EŞDEĞER · aksi → BELİRSİZ."""
    if ci_alt > esik:
        return KARAR_H1_IYIMSER
    if ci_ust <= esik:
        return KARAR_H1_ESDEGER
    return KARAR_BELIRSIZ


def karar_h2(ci_alt: float, ci_ust: float, bant: float = FIYAT_BANDI_BPS) -> str:
    """Kart: CI-alt > +5 → İYİMSER · CI-üst < −5 → KÖTÜMSER · CI tamamen [−5, +5] → EŞDEĞER · aksi → BELİRSİZ."""
    if ci_alt > bant:
        return KARAR_H2_IYIMSER
    if ci_ust < -bant:
        return KARAR_H2_KOTUMSER
    if ci_alt >= -bant and ci_ust <= bant:
        return KARAR_H2_ESDEGER
    return KARAR_BELIRSIZ


def _r3(x):
    return None if x is None else round(x, 3)


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


def _sayim(degerler) -> dict:
    out: dict[str, int] = {}
    for v in degerler:
        out[str(v)] = out.get(str(v), 0) + 1
    return dict(sorted(out.items()))


def _ikili(satirlar: list, sinif_alan: str = "sinif", fark_alan: str = "fark_bps") -> dict:
    """Bir satır kümesinde (verilen sınıf/fark alanlarıyla) DOLMAZ payı ve DOLAN fark medyanı."""
    h = [r for r in satirlar if r.get(sinif_alan) in ("DOLAN", "DOLMAZ")]
    dm = sum(1 for r in h if r[sinif_alan] == "DOLMAZ")
    fk = [r[fark_alan] for r in h if r[sinif_alan] == "DOLAN" and r.get(fark_alan) is not None]
    return {"n": len(h), "dolmaz_n": dm, "dolan_n": len(h) - dm,
            "dolmaz_pct": _r3(dm / len(h) * 100.0) if h else None,
            "fark_medyan_bps": _r3(statistics.median(fk)) if fk else None,
            "digeri_n": len(satirlar) - len(h)}


def _gruplu(satirlar: list, anahtar, **kw) -> dict:
    g: dict[str, list] = {}
    for r in satirlar:
        g.setdefault(str(anahtar(r)), []).append(r)
    return {k: _ikili(v, **kw) for k, v in sorted(g.items())}


def _tanilar(h1_set: list, aday: list) -> dict:
    dolan = [r for r in h1_set if r["sinif"] == "DOLAN"]
    dolmaz = [r for r in h1_set if r["sinif"] == "DOLMAZ"]
    spread = [r["spread_bps"] for r in dolan if r.get("spread_bps") is not None]
    isaret: dict[str, list] = {}
    for r in h1_set:
        isaret.setdefault(str(r.get("acilis_dal")), []).append(r)
    olcekli_tkr = sorted({r["ticker"] for r in aday if r.get("_f") is not None and r["_f"] != 1})
    return {
        "a_dal_kirilimi": _gruplu(h1_set, lambda r: r.get("dal")),
        "b_0930_varyanti": {
            **_ikili(h1_set, "t930_sinif", "t930_fark_bps"),
            "dal_sayimi": _sayim(r.get("t930_dal") for r in h1_set),
            "beyan": ("aynı koda sadık öykünücü (tip plan günü kapanışından, ölçek aynı), t0 = 09:30 ET ilk kayıt — "
                      "replay'in açılış varsayımının ilk IEX işleminden farkı; 9:45 penceresinin payını ayırır")},
        "c_gecikme_dk": {
            "dolum": _dagilim([r["dolum_gecikme_dk"] for r in dolan if r.get("dolum_gecikme_dk") is not None]),
            "aktivasyon": _dagilim([r["akt_gecikme_dk"] for r in h1_set if r.get("akt_gecikme_dk") is not None]),
            "beyan": "t0 kaydından dakika"},
        "d_yil": _gruplu(h1_set, lambda r: r["seans"][:4]),
        "d_fiyat_kovasi": _gruplu(h1_set, lambda r: _fiyat_kovasi(r["tetik"])),
        "e_kosul_0x20_disi": {
            **_ikili(h1_set, "kosulsuz_sinif", "kosulsuz_fark_bps"),
            "beyan": "kosul & 0x20 kayıtları seanstan çıkarılıp öykünücü (t0 dahil) YENİDEN koşuldu; digeri_n = akis_yok"},
        "f_dolum_ani_spread_bps": {
            **(_dagilim(spread) or {"n": 0}),
            "kotasyon_yok_ya_da_tek_yanli_n": len(dolan) - len(spread),
            "beyan": "(k_satis − k_alis) / canli_dolum × 1e4 (ham birimde, birimsiz), dolum kaydının işlem-anı kotasyonu"},
        "g_dolmaz_replay_sonucu": {
            "n": len(dolmaz), "exit_reason": _sayim(r.get("exit_reason") for r in dolmaz),
            "r_multiple": _dagilim([r["r_multiple"] for r in dolmaz if r.get("r_multiple") is not None]),
            "dolan_karsilastirma": {
                "exit_reason": _sayim(r.get("exit_reason") for r in dolan),
                "r_multiple": _dagilim([r["r_multiple"] for r in dolan if r.get("r_multiple") is not None])},
            "beyan": "yalnız BETİMLEYİCİ — P&L etkisi ayrı kartın işidir"},
        "h_acilis_tetik_isareti": {
            k: {**_ikili(v), "fark_dagilimi": _dagilim([r["fark_bps"] for r in v
                                                         if r["sinif"] == "DOLAN" and r.get("fark_bps") is not None])}
            for k, v in sorted(isaret.items())},
        "i_f1_disi_haric": {
            **_ikili([r for r in h1_set if r.get("_f") == 1]),
            "dislanan_f1_disi_n": sum(1 for r in h1_set if r.get("_f") is not None and r["_f"] != 1),
            "beyan": "f ≠ 1 (yeniden ölçeklenmiş) satırlar DIŞLANINCA iki birincil (nokta) — ölçeklemenin sonucu "
                     "sürüklemediğinin gösterimi"},
        "j_olcek_tablosu": {
            "f_dagilimi": _sayim(r["olcek_f"] for r in aday if r.get("olcek_f")),
            "ticker_f": {t: _sayim(r["olcek_f"] for r in aday if r["ticker"] == t and r.get("olcek_f"))
                         for t in olcekli_tkr},
            "eslenemez_ticker": _sayim(r["ticker"] for r in aday if r["sinif"] == "olcek_eslenemez"),
            "parite_disi_ticker": _sayim(r["ticker"] for r in aday if r["sinif"] == "olcek_parite_disi")},
    }


# ── pozitif kontroller ──────────────────────────────────────────────────────────────────────────────
def pk1_kimlik() -> dict:
    """EDG-105 ayakları (EST + EDT; GAP, tetik altında açılan GAP, STOP-LIMIT, tetiksiz DOLMAZ, L-üstü DOLMAZ, 09:30
    kırılımı SAYILMAZ, kuruş yuvarlaması) + ÖLÇEK kimliği: bilinen f ∈ {1/10, 1/2, 3} ile ölçeklenmiş plan fiyatları, ham
    akışta f = 1 ile AYNI dal/dolum; F'nin %2 dışındaki oran eşlenemez."""
    tetik = 50.0
    lim = limit_fiyati(tetik)
    sonuc = {}
    for gun in (dt.date(2024, 1, 10), dt.date(2024, 7, 10)):
        a, _ = seans_siniri_ns(gun)
        p = pencere_ns(gun)

        def k(sn, fiyat):
            return (p + int(sn * NS), int(round(fiyat * FIYAT_OLCEK)), 100, 0, None, None)
        on = (a, 505_000, 100, 0, None, None)           # 09:30 kırılımı — pencere ÖNCESİ

        def kos(akis, ref):
            return canli_kural(seans_suz([on] + akis, gun), tetik, lim, p, ref)
        gap = kos([k(0, 50.5), k(1, 50.06), k(2, 51.0)], 50.0)
        gap_alt = kos([k(0, 49.4), k(2, 49.45), k(90, 49.6)], 50.0)
        stp = kos([k(0, 49.5), k(60, 50.0), k(61, 50.06)], 49.0)
        yok = kos([k(0, 49.5), k(60, 49.9)], 49.0)
        ust = kos([k(0, 52.5), k(1, 52.3), k(2, 53.0)], 50.0)
        sonuc[gun.isoformat()] = (
            gap["sinif"] == "DOLAN" and gap["dal"] == "GAP" and gap["t0_i"] == 1 and gap["dolum_i"] == 2
            and gap["canli_dolum"] == 50.06
            and gap_alt["sinif"] == "DOLAN" and gap_alt["dal"] == "GAP" and gap_alt["canli_dolum"] == 49.45
            and stp["sinif"] == "DOLAN" and stp["dal"] == "STOP_LIMIT" and stp["akt_i"] == 2 and stp["dolum_i"] == 3
            and yok["sinif"] == "DOLMAZ" and yok["neden"] == "tetik_kirilmadi"
            and ust["sinif"] == "DOLMAZ" and ust["neden"] == "limit_ici_kayit_yok")
    # ölçek kimliği — ham akış (tick birimi) ve ham plan (f = 1) referansı
    gun = dt.date(2024, 7, 10)
    a, _ = seans_siniri_ns(gun)
    p = pencere_ns(gun)
    ham = seans_suz([(a, 598_000, 100, 0, None, None), (p, 594_000, 100, 0, None, None),
                     (p + 60 * NS, 600_000, 100, 0, None, None), (p + 61 * NS, 600_600, 100, 0, None, None)], gun)
    k1 = canli_kural(ham, 60.0, limit_fiyati(60.0), p, 59.0)
    olcek_ok = {}
    for f in (Fraction(1, 10), Fraction(1, 2), Fraction(3)):
        plan = {ad: float(_kesir(v) * f) for ad, v in (("tetik", 60.0), ("ref", 59.0), ("acilis", 59.8))}
        e = olcek_esle(plan["acilis"], 598_000)
        kf = None
        if e["f"] == f:
            tt = olcekle(plan["tetik"], f)
            kf = canli_kural(ham, tt, limit_fiyati(tt), p, olcekle(plan["ref"], f))
        olcek_ok[str(f)] = (kf is not None and k1["sinif"] == "DOLAN"
                            and (kf["sinif"], kf["dal"], kf["akt_i"], kf["dolum_i"], kf["canli_dolum"])
                            == (k1["sinif"], k1["dal"], k1["akt_i"], k1["dolum_i"], k1["canli_dolum"]))
    eslenemez = olcek_esle(5.25, 500_000)["f"] is None              # r = 0,105: 1/10'a %5 uzak
    isaret = fark_bps(50.06, 50.0) > 0
    kurus = limit_fiyati(10.0125) == 10.41 and limit_fiyati(12.315) == 12.81
    gecti = all(sonuc.values()) and isaret and lim == 52.0 and kurus and all(olcek_ok.values()) and eslenemez
    return {"gecti": gecti, "gunler": sonuc, "fark_isareti_aleyhte_pozitif": isaret, "limit_ornek": lim,
            "kurus_yuvarlamasi": kurus, "olcek_kimligi": olcek_ok, "olcek_eslenemez": eslenemez,
            "beyan": "EDG-105 kimlik ayakları + ölçek kimliği (f ∈ {1/10, 1/2, 3} ham akışta f = 1 ile aynı sonucu "
                     "vermeli) + %2 dışı oranın eşlenmemesi"}


def _pk3_satir(r: dict):
    """PK-3 bir satırda: uygulanan koşulların tutarsızlığı; ayağı ölçülemeyen satır → None."""
    y = (r.get("pk3_bar_yuksek"), r.get("pk3_tik_yuksek"))
    d = (r.get("pk3_bar_dusuk"), r.get("pk3_tik_dusuk")) if r.get("plan_dal") == "GAP" else None
    if None in y or (d is not None and None in d):
        return None
    return {"yuksek": y[0] != y[1], "dusuk": (d[0] != d[1]) if d is not None else False,
            "bar_evet_tik_hayir": bool(y[0] and not y[1])}


def pk3_ozeti(aday: list) -> dict:
    olc = [(r, s) for r in aday if (s := _pk3_satir(r)) is not None]
    tut = [(r, s) for r, s in olc if s["yuksek"] or s["dusuk"]]
    oran = (len(tut) / len(olc)) if olc else None
    bir = [(r, s) for r, s in olc if r["sinif"] in ("DOLAN", "DOLMAZ")]
    bir_tut = sum(1 for _, s in bir if s["yuksek"] or s["dusuk"])
    return {"payda_n": len(olc), "tutarsiz_n": len(tut), "olculemedi_n": len(aday) - len(olc),
            "tutarsiz_pct": _r3(oran * 100.0) if oran is not None else None,
            "esik_pct": PK3_TUTARSIZ_TAVAN * 100.0,
            "dustu": True if oran is None else oran > PK3_TUTARSIZ_TAVAN,
            "yuksek_tutarsiz_n": sum(1 for _, s in tut if s["yuksek"]),
            "dusuk_tutarsiz_n": sum(1 for _, s in tut if s["dusuk"]),
            "yuksek_bar_evet_tik_hayir": sum(1 for _, s in tut if s["bar_evet_tik_hayir"]),
            "birincil_altkume": {"n": len(bir), "tutarsiz_n": bir_tut,
                                 "tutarsiz_pct": _r3(bir_tut / len(bir) * 100.0) if bir else None},
            "tutarsiz_satirlar": [{"ticker": r.get("ticker"), "seans": r.get("seans"), "olcek_f": r.get("olcek_f"),
                                   "tetik_tik": r.get("tetik_tik"), "limit_tik": r.get("limit_tik"),
                                   "plan_dal": r.get("plan_dal"), "bar_tik": r.get("bar_tik"),
                                   "tik_seans_max": r.get("tik_seans_max"), "tik_seans_min": r.get("tik_seans_min"),
                                   "sinif": r["sinif"], **s} for r, s in tut],
            "beyan": ("kart PK-3, ÖLÇEKLENMİŞ plan birimiyle (bar ÷ f, tetik ÷ f, L ham birimde): GAP satırlarında bar "
                      "düşüğü ≤ L ⇔ tik min ≤ L; her satırda bar yükseği ≥ tetik ⇔ tik maks ≥ tetik. Ölçeği çözülmeyen "
                      "ve parite dışı satırlarda ayaklar ÖLÇÜLEMEZ (plan ölçeği belirsiz) — paydaya girmez")}


# ── özet ve karar ───────────────────────────────────────────────────────────────────────────────────
def oz_sinama_ozeti(satirlar: list) -> dict:
    """Kill-1: bar açılışı × (1 + 5 bps) trades.entry'yi ≤ 1 bps farkla veren satır ≥ 20."""
    olc = [r["oz_fark_bps"] for r in satirlar if r.get("oz_fark_bps") is not None]
    tut = sum(1 for v in olc if v <= OZ_SINAMA_TOL_BPS)
    return {"tutarli_n": tut, "olculen_n": len(olc),
            "olculemedi_n": sum(1 for r in satirlar if "oz_fark_bps" in r and r["oz_fark_bps"] is None),
            "esik": OZ_SINAMA_ALT, "tolerans_bps": OZ_SINAMA_TOL_BPS, "gecti": tut >= OZ_SINAMA_ALT,
            "fark_dagilimi_bps": _dagilim(olc),
            "beyan": PAYDALAR["kill1_oz_sinama"]}


def _kumeler(satirlar: list, deger) -> dict:
    k: dict[str, list] = {}
    for r in satirlar:
        k.setdefault(r["seans"], []).append(deger(r))
    return k


def _birincil_iskelet(ad: str, satirlar: list, kume: dict, payda: str) -> dict:
    n = len(satirlar)
    pay = (max(len(v) for v in kume.values()) / n) if n else None
    return {"ad": ad, "payda": payda, "n": n, "n_seans": len(kume), "tek_seans_payi": pay,
            "tek_seans_asimi": (pay > TEK_SEANS_TAVAN) if pay is not None else None,
            "durum": None, "engel": None, "karar": None, "ci_serh": None}


def _esik_engeli(out: dict) -> str | None:
    if out["n"] < N_UYGUN_ALT or out["n_seans"] < SEANS_ALT:
        return (f"OLCULEMEDI: {out['ad']} paydası n={out['n']} (≥{N_UYGUN_ALT}) · seans={out['n_seans']} "
                f"(≥{SEANS_ALT}) eşiği")
    return None


def _serh(out: dict) -> None:
    if out["tek_seans_asimi"]:
        out["ci_serh"] = (f"kill-5: {out['ad']} — tek seans paydanın %{_r3(out['tek_seans_payi'] * 100)}'ini "
                          "taşıyor (> %10) — CI şerhsiz yayımlanmaz")


def _h1_blok(h1_set: list, engeller: list) -> dict:
    kume = _kumeler(h1_set, lambda r: 1.0 if r["sinif"] == "DOLMAZ" else 0.0)
    out = _birincil_iskelet("H1", h1_set, kume, "DOLMAZ + DOLAN")
    dolmaz = sum(1 for r in h1_set if r["sinif"] == "DOLMAZ")
    out.update(dolmaz_n=dolmaz, dolan_n=len(h1_set) - dolmaz, oran_pct=None, ci95_pct=None)
    if engeller:
        out["durum"] = engeller[0].split(":")[0]
        return out
    esik = _esik_engeli(out)
    if esik:
        out.update(durum="OLCULEMEDI", engel=esik)
        return out
    alt, ust = seans_kumeli_oran_ci(list(kume.values()), BOOT_B, BOOT_TOHUM)
    out.update(durum="KOSULLU_HUKUM", oran_pct=dolmaz / len(h1_set) * 100.0, ci95_pct=[_r3(alt), _r3(ust)],
               karar=karar_h1(alt, ust), esik_pct=DOLMAZ_ESIK_PCT,
               bootstrap={"B": BOOT_B, "seed": BOOT_TOHUM, "kumeleme": "seans (giriş günü)",
                          "istatistik": "havuzlanmış DOLMAZ oranı × 100"})
    _serh(out)
    return out


def _h2_blok(h2_set: list, engeller: list) -> dict:
    kume = _kumeler(h2_set, lambda r: r["fark_bps"])
    out = _birincil_iskelet("H2", h2_set, kume, "DOLAN")
    out.update(medyan_bps=None, ci95_bps=None, dagilim=None)
    if engeller:
        out["durum"] = engeller[0].split(":")[0]
        return out
    esik = _esik_engeli(out)
    if esik:
        out.update(durum="OLCULEMEDI", engel=esik)
        return out
    alt, ust = seans_kumeli_ci(list(kume.values()), BOOT_B, BOOT_TOHUM)
    degerler = [r["fark_bps"] for r in h2_set]
    out.update(durum="KOSULLU_HUKUM", medyan_bps=statistics.median(degerler), ci95_bps=[_r3(alt), _r3(ust)],
               karar=karar_h2(alt, ust), bant_bps=FIYAT_BANDI_BPS, dagilim=_dagilim(degerler),
               bootstrap={"B": BOOT_B, "seed": BOOT_TOHUM, "kumeleme": "seans (giriş günü)",
                          "yontem": "EDG-042 betimleyici seans-kümeli yüzdelik bootstrap (medyan)"})
    _serh(out)
    return out


def monotonluk_uygula(satirlar: list) -> dict:
    """Kill-4: ticker başına ölçeği çözülmüş satırların f'leri tarih sırasıyla tek yönlü (hep ≤ ya da hep ≥) değilse o
    ticker'ın TÜM f ≠ 1 satırları `olcek_eslenemez` (monotonluk_ihlali) olur; sonuç alanları ve PK-3 ayakları silinir."""
    gruplar: dict[str, list] = {}
    for r in satirlar:
        if r.get("_f") is not None:
            gruplar.setdefault(r["ticker"], []).append(r)
    ihlal: dict[str, list] = {}
    yeniden = 0
    for tkr, rows in sorted(gruplar.items()):
        sirali = sorted(rows, key=lambda r: (r["seans"], r.get("seq") or 0))
        fs = [r["_f"] for r in sirali]
        if all(a <= b for a, b in zip(fs, fs[1:])) or all(a >= b for a, b in zip(fs, fs[1:])):
            continue
        ihlal[tkr] = [[r["seans"], str(r["_f"])] for r in sirali]
        for r in sirali:
            if r["_f"] != 1:
                for k in SONUC_ALANLARI:
                    r.pop(k, None)
                r.update(sinif="olcek_eslenemez", olcek_alt_neden="monotonluk_ihlali", pk3_bar_yuksek=None,
                         pk3_tik_yuksek=None, pk3_bar_dusuk=None, pk3_tik_dusuk=None)
                yeniden += 1
    return {"ihlal_tickerlar": ihlal, "yeniden_siniflanan_n": yeniden}


def ozetle(satirlar: list, oz_sinama: dict, pk1: dict, monoton: dict | None = None) -> dict:
    """İki birincil, kill-list ve iki AYRI karar (gizlenmemiş İÇ görünüm; yayım için `yayim_gorunumu`)."""
    siniflar = {s: 0 for s in ON_SINIFLAR + TIK_SINIFLARI}
    for r in satirlar:
        siniflar[str(r["sinif"])] = siniflar.get(str(r["sinif"]), 0) + 1
    aday = [r for r in satirlar if r["sinif"] in TIK_SINIFLARI]
    akisli = [r for r in aday if r["sinif"] != "akis_yok"]
    h1_set = [r for r in aday if r["sinif"] in ("DOLAN", "DOLMAZ")]
    h2_set = [r for r in aday if r["sinif"] == "DOLAN"]
    akis_oran = (siniflar["akis_yok"] / len(aday)) if aday else None
    olcek_n = sum(siniflar[s] for s in OLCEK_SINIFLARI)
    olcek_oran = (olcek_n / len(akisli)) if akisli else None
    pk3 = pk3_ozeti(aday)
    monoton = monoton or {"ihlal_tickerlar": {}, "yeniden_siniflanan_n": 0}
    kill = {"oz_sinama_gecti": bool(oz_sinama.get("gecti")),
            "akis_yok_pct": _r3(akis_oran * 100.0) if akis_oran is not None else None,
            "akis_yok_asimi": (akis_oran > AKIS_YOK_TAVAN) if akis_oran is not None else None,
            "olcek_dislanan_pct": _r3(olcek_oran * 100.0) if olcek_oran is not None else None,
            "olcek_asimi": (olcek_oran > OLCEK_DISLANAN_TAVAN) if olcek_oran is not None else None,
            "olcek_eslenemez_n": siniflar["olcek_eslenemez"], "olcek_parite_disi_n": siniflar["olcek_parite_disi"],
            "olcek_olculemedi_n": siniflar["olcek_olculemedi"],
            "olcek_alt_nedenleri": _sayim(r.get("olcek_alt_neden") for r in aday if r["sinif"] in OLCEK_SINIFLARI),
            "olcek_tolerans_pct": OLCEK_TOL_PCT,
            "monotonluk_ihlali_tickerlar": sorted(monoton["ihlal_tickerlar"]),
            "kosul_birincilde": False,
            "tip_kaynagi": TIP_KAYNAGI,
            "erken_kapanis_n": siniflar["erken_kapanis"],
            "pk1_gecti": bool(pk1.get("gecti")),
            "pk3_dustu": pk3["dustu"],
            "pk2": "ROL1_ELLE_DOGRULAMA_BEKLIYOR"}
    engeller = []
    if not kill["pk1_gecti"]:
        engeller.append("GECERSIZ: PK-1 (kimlik) düştü — kart: hiçbir sayı yayılmaz")
    if not kill["oz_sinama_gecti"]:
        engeller.append(f"GECERSIZ: kill-1 öz-sınama < {OZ_SINAMA_ALT} tutarlı satır — ölçüm geçersiz")
    if kill["pk3_dustu"]:
        engeller.append(f"GECERSIZ: PK-3 bar çaprazı tutarsızlık %{pk3['tutarsiz_pct']} (> %20 ya da ölçülemedi) "
                        "— ayak düştü, hiçbir sayı yayılmaz")
    if kill["akis_yok_asimi"]:
        engeller.append(f"YAYIMLANMAZ: kill-2 akis_yok %{kill['akis_yok_pct']} > %10 — sınıf incelenir")
    if kill["olcek_asimi"]:
        engeller.append(f"YAYIMLANMAZ: kill-3 ölçek dışlanan %{kill['olcek_dislanan_pct']} > %5 (eşlenemez "
                        f"{kill['olcek_eslenemez_n']} · parite dışı {kill['olcek_parite_disi_n']} · ölçülemedi "
                        f"{kill['olcek_olculemedi_n']})")
    h1, h2 = _h1_blok(h1_set, engeller), _h2_blok(h2_set, engeller)
    if engeller:
        durum = engeller[0].split(":")[0]
    else:
        durum = "KOSULLU_HUKUM" if "KOSULLU_HUKUM" in (h1["durum"], h2["durum"]) else "OLCULEMEDI"
    kosullar = []
    if not engeller:
        kosullar.append("PK-2: --elle-ornek dilimleri Rol-1 tarafından parquet'ten elle doğrulanmadan hiçbir sayı "
                        "yayılmaz (kart pozitif_kontrol 2)")
        kosullar += [h["ci_serh"] for h in (h1, h2) if h["ci_serh"]]
    return {"siniflar": siniflar, "n_aday": len(aday), "n_akisli": len(akisli),
            "akis_yok_alt_nedenleri": _sayim(r.get("alt_neden") for r in aday if r["sinif"] == "akis_yok"),
            "dolmaz_nedenleri": _sayim(r.get("dolmaz_neden") for r in h1_set if r["sinif"] == "DOLMAZ"),
            "kill_list": kill, "pk3": pk3, "durum": durum, "engeller": engeller,
            "h1": h1, "h2": h2, "kosullar": kosullar,
            "tanilar": None if engeller else _tanilar(h1_set, aday)}


# ── sonuç alanı disiplini (tur 3) ──────────────────────────────────────────────────────────────────
def _gizli_blok(h: dict, genel_engel: str | None) -> dict:
    return {"ad": h["ad"], "payda": h["payda"], "durum": h["durum"], "gizli": True,
            "engel_nedeni": genel_engel or (f"{h['ad']} paydası eşiğin altında (≥ {N_UYGUN_ALT} satır ∧ ≥ {SEANS_ALT} "
                                            "seans) — sayı yayılmaz")}


def _satir_cikti(r: dict) -> dict:
    return {k: v for k, v in r.items() if not k.startswith("_") and k != "dilim"}


def yayim_gorunumu(ozet: dict, satirlar: list, pk2: dict) -> tuple[dict, list, dict, dict]:
    """Yayımlanmayan birincilin sonucu (ya da ondan türetilebilen sayılar) sonuc.json/OZET.md/stdout'a GİRMEZ."""
    h1g = ozet["h1"]["durum"] != "KOSULLU_HUKUM"
    h2g = h1g or ozet["h2"]["durum"] != "KOSULLU_HUKUM"      # H1 gizliyken H2'nin n'i (DOLAN) H1'i ele verir
    gizlilik = {"h1": h1g, "h2": h2g}
    if not (h1g or h2g):
        return ozet, [_satir_cikti(r) for r in satirlar], pk2, gizlilik
    genel = ozet["engeller"][0] if ozet["engeller"] else None
    satir_cikti = []
    for r in satirlar:
        s = {k: v for k, v in _satir_cikti(r).items() if k not in SONUC_ALANLARI}
        if h1g and s["sinif"] in ("DOLAN", "DOLMAZ"):
            s["sinif"] = GIZLI_SINIF
        satir_cikti.append(s)
    oz = dict(ozet)
    oz["tanilar"] = None
    oz["h2"] = _gizli_blok(ozet["h2"], genel)
    if h1g:
        sin = dict(ozet["siniflar"])
        oz["birincil_aday_n"] = sin.pop("DOLAN", 0) + sin.pop("DOLMAZ", 0)
        oz["siniflar"] = sin
        oz["dolmaz_nedenleri"] = None
        oz["h1"] = _gizli_blok(ozet["h1"], genel)
        pk3 = dict(ozet["pk3"])
        pk3["tutarsiz_satirlar"] = [{**t, "sinif": GIZLI_SINIF if t["sinif"] in ("DOLAN", "DOLMAZ") else t["sinif"]}
                                    for t in ozet["pk3"]["tutarsiz_satirlar"]]
        oz["pk3"] = pk3
    pk2g = {"durum": "YAYIMLANMADI_GIZLI", "istenen": pk2.get("istenen"), "ornekler": [], "kota": None,
            "kota_karsilandi": None}
    return oz, satir_cikti, pk2g, gizlilik


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
        sql_n = con.execute("SELECT COUNT(*) AS n FROM trades WHERE kaynak = ?", (KAYNAK,)).fetchone()["n"]
        secili = []
        for h in ham:
            b = _birlestir(h, sayac)
            if b.get("kaynak") == KAYNAK:
                secili.append((h, b))
        plan_idler = sorted({str(b.get("plan_id")) for _, b in secili if b.get("plan_id")})
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
        planlar.setdefault(b.get("id"), []).append(b)
    trades_bayt = _kanonik([h for h, _ in secili])
    plan_bayt = _kanonik(plan_ham)
    return {"secili": secili, "planlar": planlar, "trades_bayt": trades_bayt, "plan_bayt": plan_bayt,
            "ozet": {"n_trades_tum": len(ham), "n_trades_filtreli": len(secili), "sql_capraz_n": sql_n,
                     "n_plan_satiri": len(plan_ham), "trade_plans_tablosu": tablo_var,
                     "strategy_version": _sayim(b.get("strategy_version") for _, b in secili),
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
def satirlari_hazirla(girdi: dict) -> list:
    """Tik öncesi sınıflama (erken kapanış dahil) + tetik/L + açılış↔tetik işareti. Uygun satırda `sinif` None."""
    out = []
    for h, b in girdi["secili"]:
        tkr = str(b.get("ticker") or "").upper()
        r = {"seq": h.get("seq"), "id": b.get("id"), "plan_id": b.get("plan_id"), "ticker": tkr,
             "ts_open": b.get("ts_open"), "entry": _sayi(b.get("entry")), "side": b.get("side"),
             "exit_reason": b.get("exit_reason"), "r_multiple": _sayi(b.get("r_multiple")),
             "strategy_version": b.get("strategy_version")}
        try:
            gun = dt.date.fromisoformat(str(b.get("ts_open") or "")[:10])
        except ValueError:
            gun = None                         # sessiz-yutma DEĞİL: satır tarih_okunamadi sınıfına düşer
        if gun is not None and tkr:
            r["seans"] = gun.isoformat()
        planlar = girdi["planlar"].get(b.get("plan_id"), []) if b.get("plan_id") else []
        tetikler = sorted({v for v in (_sayi(p.get("entry_trigger")) for p in planlar) if v is not None})
        if b.get("side") != "long":
            r.update(sinif="yon_disi", neden="öykünücü yalnız long için tanımlı (kart: hepsi long)")
        elif gun is None or not tkr:
            r.update(sinif="tarih_okunamadi", neden="ts_open/ticker çözülemedi")
        elif r["entry"] is None or r["entry"] <= 0:
            r.update(sinif="giris_okunamadi", neden="trades.entry okunamadı")
        elif not planlar:
            r.update(sinif="plan_yok", neden="trade_plans'ta plan_id eşleşmesi yok")
        elif len(tetikler) > 1:
            r.update(sinif="plan_belirsiz", neden=f"aynı plan_id'de farklı entry_trigger: {tetikler}")
        elif not tetikler or tetikler[0] <= 0:
            r.update(sinif="tetik_okunamadi", neden="entry_trigger okunamadı")
        else:
            p = planlar[0]
            tetik = tetikler[0]
            bps, dal = acilis_dali(r["entry"], tetik)
            r.update(sinif=None, tetik=tetik, limit=limit_fiyati(tetik), limit_ham=limit_ham(tetik),
                     plan_stop=_sayi(p.get("stop")), plan_tarihi=(str(p.get("date") or "")[:10] or None),
                     acilis_tetik_bps=bps, acilis_dal=dal)
            if r["seans"] in ERKEN_KAPANIS_GUNLERI:
                r.update(sinif="erken_kapanis", neden="XNYS 13:00 ET erken kapanış günü (kart adim_0 listesi)")
        out.append(r)
    return out


def bar_alanlari(r: dict, seri: dict | None) -> None:
    """Giriş günü barı (öz-sınama, ölçek, PK-3 bar ayakları) + plan günü kapanışı (emir tipi ref'i, kill-3 kolu)."""
    b = (seri or {}).get(r.get("seans")) if r.get("seans") else None
    r["bar"] = b
    r["bar_acilis"] = b.get("open") if b else None
    r["oz_fark_bps"] = (oz_fark_bps(r["entry"], r["bar_acilis"])
                        if r.get("entry") and r["bar_acilis"] else None)
    ref = (seri or {}).get(r.get("plan_tarihi")) if r.get("plan_tarihi") else None
    r["ref_kapanis"] = ref.get("close") if ref else None
    tetik, lim = r.get("tetik"), r.get("limit")
    r["plan_dal"] = emir_tipi(r["ref_kapanis"], tetik) if (tetik and r["ref_kapanis"] is not None) else None
    r["ref_tetik_orani"] = (r["ref_kapanis"] / tetik) if (tetik and r["ref_kapanis"] is not None) else None
    r["pk3_bar_yuksek"] = (None if tetik is None or not b or b.get("high") is None else b["high"] >= tetik)
    r["pk3_bar_dusuk"] = (None if lim is None or not b or b.get("low") is None else b["low"] <= lim)


def _bantta(x: float) -> bool:
    return OLCEK_BANDI[0] <= x <= OLCEK_BANDI[1]


def _dilim(seans: list, roller: dict) -> list:
    idx = set()
    for i in roller:
        idx |= set(range(max(0, i - ELLE_PENCERE), min(len(seans), i + ELLE_PENCERE + 1)))
    out = []
    for i in sorted(idx):
        ts, fiyat, lot, kosul, ka, ks = seans[i]
        sn, kalan = divmod(ts, NS)
        et = dt.datetime.fromtimestamp(sn, tz=ET)
        out.append({"i": i, "ts_ns": ts, "et": f"{et:%H:%M:%S}.{kalan:09d}",
                    "fiyat": None if fiyat is None else fiyat / FIYAT_OLCEK, "fiyat_ham": fiyat, "lot": lot,
                    "kosul": kosul, "k_alis": ka, "k_satis": ks, "rol": roller.get(i, "")})
    return out


def satir_olc(r: dict, ham: list | None, oykunucu: bool = True) -> None:
    """Tek aday satırı: ölçek eşleme → (akis_yok · ölçülemedi · eşlenemez · parite) → öykünücü ham birimde. Sonuç `r`ye.
    `oykunucu=False` (kuru): ölçek aşamasında durur, sınıf `olcek_uygun` — DOLAN/DOLMAZ üretilmez."""
    gun = dt.date.fromisoformat(r["seans"])
    tetik = r["tetik"]
    r["_f"] = None
    if ham is None:
        r.update(sinif="akis_yok", alt_neden="gun_dosyasi_yok", pk3_tik_yuksek=None, pk3_tik_dusuk=None,
                 tik_seans_max=None, tik_seans_min=None, olcek_orani=None, olcek_f=None)
        return
    seans = seans_suz(ham, gun)
    fiyatlar = [x[1] for x in seans if x[1] is not None]
    r.update(n_seans_kaydi=len(seans), n_seans_disi=len(ham) - len(seans), n_fiyatsiz=len(seans) - len(fiyatlar))
    r["tik_seans_max"] = (max(fiyatlar) / FIYAT_OLCEK) if fiyatlar else None
    r["tik_seans_min"] = (min(fiyatlar) / FIYAT_OLCEK) if fiyatlar else None
    ilk = (fiyatlar[0] / FIYAT_OLCEK) if fiyatlar else None
    oran = (r["bar_acilis"] / ilk) if (r.get("bar_acilis") and ilk) else None
    r["ilk_tik"], r["olcek_orani"] = ilk, _r3(oran) if oran is not None else None
    e = olcek_esle(r.get("bar_acilis"), fiyatlar[0] if fiyatlar else None)
    f = e["f"]
    r["_f"] = f
    r.update(olcek_f=None if f is None else str(f),
             olcek_en_yakin=None if e["en_yakin"] is None else str(e["en_yakin"]),
             olcek_sapma_pct=None if e["sapma"] is None else float(e["sapma"] * 100),
             olcek_ikinci_aday=None if e["ikinci_aday"] is None else str(e["ikinci_aday"]))
    ref = r.get("ref_kapanis")
    if f is not None:
        tetik_t = olcekle(tetik, f)
        lim_t = limit_fiyati(tetik_t)
        entry_t = olcekle(r["entry"], f)
        ref_t = None if ref is None else olcekle(ref, f)
        b = r.get("bar")
        bar_t = None if not b else {k: (None if v is None else olcekle(v, f)) for k, v in b.items()}
        r.update(tetik_tik=tetik_t, limit_tik=lim_t, entry_tik=entry_t, ref_tik=ref_t, bar_tik=bar_t)
        r["pk3_tik_yuksek"] = None if r["tik_seans_max"] is None else r["tik_seans_max"] >= tetik_t
        r["pk3_tik_dusuk"] = None if r["tik_seans_min"] is None else r["tik_seans_min"] <= lim_t
        r["pk3_bar_yuksek"] = None if not bar_t or bar_t.get("high") is None else bar_t["high"] >= tetik_t
        r["pk3_bar_dusuk"] = None if not bar_t or bar_t.get("low") is None else bar_t["low"] <= lim_t
    else:
        r.update(pk3_tik_yuksek=None, pk3_tik_dusuk=None, pk3_bar_yuksek=None, pk3_bar_dusuk=None)
    esik = pencere_ns(gun)
    if t0_bul(seans, esik) is None:
        r.update(sinif="akis_yok",
                 alt_neden="seansta_sembol_kaydi_yok" if not fiyatlar else "pencere_sonrasi_kayit_yok")
        return
    if ref is None:
        r.update(sinif="olcek_olculemedi", olcek_alt_neden="ref_yok")   # tip belirlenemez → öykünücü koşmaz
        return
    if not r.get("bar_acilis"):
        r.update(sinif="olcek_olculemedi", olcek_alt_neden="bar_acilis_yok")
        return
    if f is None:
        r.update(sinif="olcek_eslenemez", olcek_alt_neden="kesir_disi")
        return
    if not _bantta(ref / tetik):
        r.update(sinif="olcek_parite_disi", olcek_alt_neden="kapanis_tetik", pk3_bar_yuksek=None, pk3_tik_yuksek=None,
                 pk3_bar_dusuk=None, pk3_tik_dusuk=None)
        return
    if not oykunucu:
        r["sinif"] = "olcek_uygun"
        return
    k = canli_kural(seans, tetik_t, lim_t, esik, ref_t)
    t0 = seans[k["t0_i"]]
    r.update(dal=k["dal"], oykunucu_sinif=k["sinif"], dolmaz_neden=k["neden"], p0=k["p0"], t0_ts_ns=t0[0],
             canli_dolum=k["canli_dolum"],
             fark_bps=fark_bps(k["canli_dolum"], entry_t) if k["sinif"] == "DOLAN" else None)
    r["sinif"] = k["sinif"]
    roller = {k["t0_i"]: "t0"}
    if k["akt_i"] is not None:
        a = seans[k["akt_i"]]
        r["akt_ts_ns"], r["akt_gecikme_dk"] = a[0], (a[0] - t0[0]) / (60 * NS)
        roller[k["akt_i"]] = "aktivasyon" if k["akt_i"] != k["t0_i"] else "t0+aktivasyon"
    if k["sinif"] == "DOLAN":
        d = seans[k["dolum_i"]]
        r["dolum_ts_ns"], r["dolum_gecikme_dk"] = d[0], (d[0] - t0[0]) / (60 * NS)
        ka, ks = d[4], d[5]
        r["spread_bps"] = ((ks - ka) / FIYAT_OLCEK / k["canli_dolum"] * 1e4
                           if ka and ks and ka > 0 and ks >= ka else None)
        roller[k["dolum_i"]] = "dolum"
    else:
        sonra = [(i, seans[i][1]) for i in range(k["t0_i"], len(seans)) if seans[i][1] is not None]
        i_max, f_max = max(sonra, key=lambda x: x[1])
        i_min, f_min = min(sonra, key=lambda x: x[1])
        r["t0_sonrasi_max"], r["t0_sonrasi_min"] = f_max / FIYAT_OLCEK, f_min / FIYAT_OLCEK
        roller.setdefault(i_max if k["dal"] == "STOP_LIMIT" else i_min,
                          "t0_sonrasi_max" if k["dal"] == "STOP_LIMIT" else "t0_sonrasi_min")
        if k["akt_i"] is not None:
            aks = [seans[i][1] for i in range(k["akt_i"] + 1, len(seans)) if seans[i][1] is not None]
            r["akt_sonrasi_min"] = (min(aks) / FIYAT_OLCEK) if aks else None
    r["dilim"] = _dilim(seans, roller)
    k930 = canli_kural(seans, tetik_t, lim_t, pencere_ns(gun, ACILIS_ET_DK), ref_t)
    r["t930_sinif"], r["t930_dal"] = k930["sinif"], k930["dal"]
    r["t930_fark_bps"] = fark_bps(k930["canli_dolum"], entry_t) if k930["sinif"] == "DOLAN" else None
    kz = canli_kural([x for x in seans if not ((x[3] or 0) & KOSUL_TEK_LOT_BITI)], tetik_t, lim_t, esik, ref_t)
    r["kosulsuz_sinif"] = kz["sinif"]
    r["kosulsuz_fark_bps"] = fark_bps(kz["canli_dolum"], entry_t) if kz["sinif"] == "DOLAN" else None


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


def pk2_ornekler(satirlar: list, n: int, tick_kok: pathlib.Path) -> dict:
    """PK-2 (kart): ≥ 4 GAP (DOLAN öncelikli), varsa ≥ 1 STOP-LIMIT, varsa ≥ 1 DOLMAZ, varsa ≥ 1 f ≠ 1; kalan sabit
    tohumla rastgele. Havuz = birincil satırlar (DOLAN + DOLMAZ)."""
    kota = {"GAP": 0, "STOP_LIMIT": 0, "DOLMAZ": 0, "f_1_disi": 0}
    if n <= 0:
        return {"istenen": n, "ornekler": [], "kota": kota, "kota_karsilandi": None}
    h1 = sorted([r for r in satirlar if r["sinif"] in ("DOLAN", "DOLMAZ")],
                key=lambda r: (r["seans"], r["ticker"], r["seq"] or 0))
    rng = random.Random(BOOT_TOHUM)
    secilen: list[int] = []

    def olcekli(r):
        return r.get("_f") is not None and r["_f"] != 1

    def sec(kosul, k):
        havuz = [i for i, r in enumerate(h1) if i not in secilen and kosul(r)]
        k = min(k, len(havuz), n - len(secilen))
        if k > 0:
            secilen.extend(rng.sample(havuz, k))

    def say(kosul):
        return sum(1 for i in secilen if kosul(h1[i]))
    sec(lambda r: r["dal"] == "GAP" and r["sinif"] == "DOLAN", PK2_GAP_ALT)
    sec(lambda r: r["dal"] == "GAP", PK2_GAP_ALT - say(lambda r: r["dal"] == "GAP"))
    sec(lambda r: r["dal"] == "STOP_LIMIT" and r["sinif"] == "DOLAN", 1)
    sec(lambda r: r["dal"] == "STOP_LIMIT", 1 - say(lambda r: r["dal"] == "STOP_LIMIT"))
    sec(lambda r: r["sinif"] == "DOLMAZ", 1 - say(lambda r: r["sinif"] == "DOLMAZ"))
    sec(lambda r: olcekli(r) and r["sinif"] == "DOLAN", 1 - say(olcekli))
    sec(olcekli, 1 - say(olcekli))
    sec(lambda r: True, n - len(secilen))
    for i in secilen:
        kota[h1[i]["dal"]] += 1
        kota["DOLMAZ"] += h1[i]["sinif"] == "DOLMAZ"
        kota["f_1_disi"] += olcekli(h1[i])
    stop_var = any(r["dal"] == "STOP_LIMIT" for r in h1)
    dolmaz_var = any(r["sinif"] == "DOLMAZ" for r in h1)
    olcekli_var = any(olcekli(r) for r in h1)
    ornekler = []
    for i in sorted(secilen, key=lambda j: (h1[j]["seans"], h1[j]["ticker"])):
        r = h1[i]
        gun = dt.date.fromisoformat(r["seans"])
        ornekler.append({k: r.get(k) for k in ("ticker", "seans", "tetik", "entry", "ref_kapanis", "plan_tarihi",
                                                "bar_acilis", "ilk_tik", "olcek_f", "tetik_tik", "limit_tik",
                                                "entry_tik", "ref_tik", "dal", "sinif", "dolmaz_neden", "p0",
                                                "canli_dolum", "fark_bps", "t0_sonrasi_max", "t0_sonrasi_min",
                                                "akt_sonrasi_min")}
                        | {"pencere_ns": [pencere_ns(gun), seans_siniri_ns(gun)[1]],
                           "parquet": str(tick_kok / f"{r['seans']}.parquet"), "dilim": r.get("dilim"),
                           "elle_kural": ("f = F'de bar_acilis / ilk_tik'e en yakın basit kesir (≤ %2); tetik_tik = tetik ÷ f, "
                                          "entry_tik = entry ÷ f, ref_tik = ref_kapanis ÷ f (ondalık-tam); tip = ref ≥ "
                                          "tetik ? GAP : STOP_LIMIT; limit_tik = round(round(tetik_tik × 1,04, 4), 2); "
                                          "seans = sembol kayıtları, pencere_ns[0] ≤ ts < pencere_ns[1], ts'e göre "
                                          "kararlı sıralı, fiyat/1e4; t0 = ilk kayıt; GAP → dolum = t0'dan SONRAKİ ilk "
                                          "fiyat ≤ limit_tik; STOP_LIMIT → aktivasyon = t0'dan itibaren ilk fiyat ≥ "
                                          "tetik_tik, dolum = aktivasyondan SONRAKİ ilk fiyat ≤ limit_tik; yoksa DOLMAZ. "
                                          "fark_bps = (dolum − entry_tik) / entry_tik × 1e4")})
    karsilandi = (kota["GAP"] >= PK2_GAP_ALT and (not stop_var or kota["STOP_LIMIT"] >= 1)
                  and (not dolmaz_var or kota["DOLMAZ"] >= 1) and (not olcekli_var or kota["f_1_disi"] >= 1))
    return {"istenen": n, "ornekler": ornekler, "kota": kota, "kota_karsilandi": karsilandi,
            "havuzda_stop_limit": stop_var, "havuzda_dolmaz": dolmaz_var, "havuzda_f_1_disi": olcekli_var}


# ── koruma ve çıktı ─────────────────────────────────────────────────────────────────────────────────
def _icinde(yol: pathlib.Path, kok: pathlib.Path) -> bool:
    y, k = yol.resolve(), kok.resolve()
    return y == k or k in y.parents


def _yaz(yol: pathlib.Path, veri: bytes) -> None:
    yol.write_bytes(veri)


def _json(obj) -> bytes:
    return (json.dumps(obj, ensure_ascii=False, indent=1) + "\n").encode("utf-8")


def _kaynak_sha256() -> tuple[str | None, str | None]:
    """Dosya kipinde betiğin kendi sha256'sı; stdin kipinde (`python -`) None + neden."""
    yol = globals().get("__file__")
    if isinstance(yol, str) and yol != "<stdin>" and pathlib.Path(yol).is_file():
        return hashlib.sha256(pathlib.Path(yol).read_bytes()).hexdigest(), None
    return None, ("stdin koşumu (python -): kaynak dosyası yok, betik kendi baytlarını okuyamaz — "
                  "betik_sha256_beyan Rol-1'in yerel sha256'sıdır (doğrulanamaz beyan)")


def _arac_kunyesi(okuyucu: str, kendi_sha, sha_neden, beyan) -> dict:
    if okuyucu == "pyarrow":
        import pyarrow
        surum = pyarrow.__version__
    else:
        import duckdb
        surum = duckdb.__version__
    return {"betik": BETIK_YOLU, "surum": ARAC_SURUMU, "kip": "dosya" if kendi_sha else "stdin",
            "betik_sha256": kendi_sha, "betik_sha256_neden": sha_neden, "betik_sha256_beyan": beyan,
            "python": platform.python_version(), "okuyucu": okuyucu, "okuyucu_surumu": surum,
            "utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}


def _h_satiri(h: dict) -> str:
    if h.get("gizli"):
        return f"{h['ad']} [{h['payda']}] · durum {h['durum']} · GİZLİ (yayımlanmadı) · neden: {h['engel_nedeni']}"
    if h["ad"] == "H1":
        deger = f"oran %{_r3(h['oran_pct'])} · CI {h['ci95_pct']}" if h["oran_pct"] is not None else "—"
    else:
        deger = f"medyan {_r3(h['medyan_bps'])} bps · CI {h['ci95_bps']}" if h["medyan_bps"] is not None else "—"
    return (f"{h['ad']} [{h['payda']}] n={h['n']} seans={h['n_seans']} · durum {h['durum']} · {deger} · "
            f"KARAR {h['karar']}")


def _ozet_md(s: dict) -> str:
    o, g, oz, pk, a = s["ozet"], s["girdi"], s["oz_sinama"], s["pk"], s["arac"]
    kl = o["kill_list"]
    L = [f"# {KART_ID} — replay girişi ↔ koda sadık canlı giriş kuralı, bölünme yeniden ölçekli (tick) · ölçüm özeti",
         "", f"Araç: `{a['betik']}` sürüm {a['surum']} · kip {a['kip']} · sha256 `{a['betik_sha256']}` · "
         f"beyan `{a['betik_sha256_beyan']}` · okuyucu {a['okuyucu']} {a['okuyucu_surumu']} · {a['utc']}",
         f"Parmak izi (iç sonuç): `{s['parmak_izi']}` · gizlilik {s['gizlilik']}",
         "", "Bu belge HÜKÜM DEĞİLDİR: iki karar kuralının çıktısıdır; hükmü Rol-1 karta + K defterine işler.",
         "", "## Girdi (içerik-adresli)",
         f"- trades (kaynak=replay_seed): n={g['n_trades_filtreli']} (SQL çapraz: {g['sql_capraz_n']}; tüm "
         f"trades {g['n_trades_tum']}) · sha256 `{g['trades_sha256']}`",
         f"- plan satırı: {g['n_plan_satiri']} · sha256 `{g['planlar_sha256']}` · extra_json bozuk: "
         f"{g['extra_json_bozuk']} · strategy_version {g['strategy_version']}",
         "", "## Paydalar"] + [f"- **{k}**: {v}" for k, v in PAYDALAR.items()] + [
         "", "## Öz-sınama (kill-1)",
         f"- tutarlı {oz['tutarli_n']} / eşik {oz['esik']} (≤ {oz['tolerans_bps']} bps) → "
         f"{'GEÇTİ' if oz['gecti'] else 'DÜŞTÜ'} · ölçülen {oz['olculen_n']} · ölçülemedi {oz['olculemedi_n']}",
         "", "## Sınıflar",
         "- " + " · ".join(f"{k}={v}" for k, v in o["siniflar"].items())
         + (f" · birincil_aday_n={o['birincil_aday_n']} (DOLAN/DOLMAZ ayrımı GİZLİ)" if "birincil_aday_n" in o else ""),
         f"- akis_yok alt nedenleri: {o['akis_yok_alt_nedenleri']} · DOLMAZ nedenleri: "
         f"{o['dolmaz_nedenleri'] if o['dolmaz_nedenleri'] is not None else 'GİZLİ'}",
         "", "## Ölçek (kill-3 · kill-4)",
         f"- dışlanan %{kl['olcek_dislanan_pct']} (eşik %5) · eşlenemez {kl['olcek_eslenemez_n']} · parite dışı "
         f"{kl['olcek_parite_disi_n']} · ölçülemedi {kl['olcek_olculemedi_n']} · alt nedenler "
         f"{kl['olcek_alt_nedenleri']} · monotonluk ihlali {kl['monotonluk_ihlali_tickerlar']}",
         "", "## Kill-list",
         "- " + " · ".join(f"{k}={v}" for k, v in kl.items()),
         "", "## Sonuç (iki hüküm AYRI)", f"- DURUM: **{o['durum']}**"]
    for e in o["engeller"]:
        L.append(f"- engel: {e}")
    for h in (o["h1"], o["h2"]):
        L.append(f"- {_h_satiri(h)}" + (f" · engel: {h['engel']}" if h.get("engel") else ""))
    for k in o["kosullar"]:
        L.append(f"- koşul: {k}")
    p3 = pk["pk3"]
    L += ["", "## Pozitif kontrol",
          f"- PK-1 kimlik (çalışma anı, ölçek kimliği dahil): {'GEÇTİ' if pk['pk1']['gecti'] else 'DÜŞTÜ'}",
          f"- PK-2 elle: {pk['pk2']['durum']} ({len(pk['pk2']['ornekler'])} örnek, kota {pk['pk2']['kota']}, "
          f"karşılandı {pk['pk2']['kota_karsilandi']})",
          f"- PK-3 bar çaprazı (ölçekli birim): tutarsız {p3['tutarsiz_n']} / {p3['payda_n']} (%{p3['tutarsiz_pct']}, "
          f"eşik %{p3['esik_pct']:g}) → {'DÜŞTÜ' if p3['dustu'] else 'GEÇTİ'} · yüksek koşulu "
          f"{p3['yuksek_tutarsiz_n']} · düşük koşulu (GAP) {p3['dusuk_tutarsiz_n']} · ölçülemedi {p3['olculemedi_n']}"]
    if o["tanilar"]:
        L += ["", "## Tanılar (hüküm değil)"]
        for k, v in o["tanilar"].items():
            L.append(f"- **{k}**: {json.dumps(v, ensure_ascii=False)}")
    L += ["", "## PK-2 elle doğrulama örnekleri"]
    for x in pk["pk2"]["ornekler"]:
        L += ["", f"### {x['ticker']} {x['seans']} · f {x['olcek_f']} · {x['dal']} (ref {x['ref_kapanis']} @ "
                  f"{x['plan_tarihi']}) · {x['sinif']} · tetik {x['tetik']} → ham {x['tetik_tik']} · L ham "
                  f"{x['limit_tik']} · entry ham {x['entry_tik']} · p0 {x['p0']} · canlı dolum {x['canli_dolum']} · "
                  f"fark {_r3(x['fark_bps'])} bps", f"`{x['parquet']}` · pencere_ns {x['pencere_ns']}", "```"]
        for k in x["dilim"] or []:
            L.append(f"{k['i']:>6} {k['et']} {k['fiyat']!s:>12} lot={k['lot']} kosul={k['kosul']} {k['rol']}")
        L += ["```", f"Kural: {x['elle_kural']}"]
    return "\n".join(L) + "\n"


def _gunleri_oku(tick_kok, uygunlar, gunler, okuyucu, oykunucu: bool, kapsam: dict | None) -> int:
    """Gün gün oku ve satırları ölç. Tam kipte şema hatası → 3; kuru kipte hata kapsam'a yazılır ve satırlar ölçülemez."""
    for g in gunler:
        gun_r = [r for r in uygunlar if r["seans"] == g]
        yol = tick_kok / f"{g}.parquet"
        if not yol.exists():
            if kapsam is not None:
                kapsam["gun_dosyasi_yok"].append(g)
            veri = None
        else:
            try:
                veri = gun_oku(yol, {r["ticker"] for r in gun_r}, okuyucu)
                if kapsam is not None:
                    kapsam["sema_uygun_gun"] += 1
            except SemaHatasi as e:
                if kapsam is None:
                    print(f"ŞEMA KAPISI: {e}")
                    return 3
                kapsam["sema_hatasi"].append(str(e))   # sessiz-yutma DEĞİL: kuru adımın ölçtüğü şey budur
                for r in gun_r:
                    r.update(sinif="sema_okunamadi", _f=None)
                continue
        for r in gun_r:
            satir_olc(r, None if veri is None else veri.get(r["ticker"], []), oykunucu=oykunucu)
        print(f"  {g}: {len(gun_r)} satır · {'dosya yok' if veri is None else 'okundu'}", flush=True)
    return 0


def olc(db, tick_kok, bar_kok, cikti, elle_ornek=0, kuru=False, okuyucu="pyarrow", betik_sha256=None) -> int:
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
    kendi_sha, sha_neden = _kaynak_sha256()
    if betik_sha256 is not None and not re.fullmatch(r"[0-9a-f]{64}", betik_sha256):
        print("RED: --betik-sha256 64 küçük harf onaltılık karakter olmalı")
        return 2
    if kendi_sha is None and betik_sha256 is None:
        print("RED: stdin koşumunda --betik-sha256 ZORUNLU — betik kendi baytlarını okuyamaz; sonuç hangi "
              "betikle üretildiğini taşımalı (yerel `shasum -a 256 olcum.py`)")
        return 2
    if kendi_sha is not None and betik_sha256 is not None and kendi_sha != betik_sha256:
        print(f"RED: --betik-sha256 beyanı ({betik_sha256}) koşan dosyanın sha256'sıyla ({kendi_sha}) ayrışıyor")
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
    arac = _arac_kunyesi(okuyucu, kendi_sha, sha_neden, betik_sha256)
    if not pk1["gecti"]:
        _yaz(hedef, _json({"kart": KART_ID, "arac": arac, "pk": {"pk1": pk1},
                           "ozet": {"durum": "GECERSIZ", "engeller": ["PK-1 düştü — gerçek veriye dokunulmadı"]}}))
        print("GECERSIZ: PK-1 çalışma anı kimlik kontrolü düştü — gerçek veriye dokunulmadı")
        return 4
    girdi = girdi_oku(db)
    _yaz(cikti / "girdi_trades.json", girdi["trades_bayt"])
    _yaz(cikti / "girdi_planlar.json", girdi["plan_bayt"])
    satirlar = satirlari_hazirla(girdi)
    bar_onb: dict = {}
    for r in satirlar:
        if r.get("seans"):
            bar_alanlari(r, bar_oku(bar_kok, r["ticker"], bar_onb))
    oz = oz_sinama_ozeti(satirlar)
    uygunlar = [r for r in satirlar if r["sinif"] is None]
    gunler = sorted({r["seans"] for r in uygunlar})
    print(f"{KART_ID}: girdi {girdi['ozet']['n_trades_filtreli']} satır (SQL {girdi['ozet']['sql_capraz_n']}) · "
          f"aday {len(uygunlar)} · {len(gunler)} seans · erken kapanış "
          f"{sum(1 for r in satirlar if r['sinif'] == 'erken_kapanis')} · öz-sınama tutarlı {oz['tutarli_n']} → "
          f"{'GEÇTİ' if oz['gecti'] else 'DÜŞTÜ'}", flush=True)
    if kuru:
        kapsam = {"gun_dosyasi_yok": [], "sema_uygun_gun": 0, "sema_hatasi": [],
                  "bar_dosyasi_yok": sorted({r["ticker"] for r in satirlar
                                             if r.get("seans") and bar_onb.get(r["ticker"]) is None}),
                  "bar_gunu_yok": sum(1 for r in uygunlar if r.get("bar") is None)}
        _gunleri_oku(tick_kok, uygunlar, gunler, okuyucu, False, kapsam)
        monoton = monotonluk_uygula(uygunlar)
        okuma = okuma_sinamasi(tick_kok, uygunlar, gunler, kapsam, okuyucu)
        refli = [r for r in uygunlar if r.get("ref_kapanis") is not None]
        say = {s: sum(1 for r in uygunlar if r["sinif"] == s) for s in OLCEK_SINIFLARI + ("akis_yok",)}
        akisli = len(uygunlar) - say["akis_yok"]
        pay = sum(say[s] for s in OLCEK_SINIFLARI)
        rapor = {"kart": KART_ID, "kip": "kuru", "arac": arac, "girdi": girdi["ozet"], "oz_sinama": oz,
                 "pk1": pk1, "siniflar_tik_oncesi": {s: sum(1 for r in satirlar if r["sinif"] == s)
                                                     for s in ON_SINIFLAR},
                 "aday_n": len(uygunlar), "seans_n": len(gunler), "kapsam": kapsam, "okuma_sinamasi": okuma,
                 "olcek": {"f_dagilimi": _sayim(r["olcek_f"] for r in uygunlar if r.get("olcek_f")),
                           "olcek_eslenemez_n": say["olcek_eslenemez"],
                           "olcek_parite_disi_n": say["olcek_parite_disi"],
                           "olcek_olculemedi_n": say["olcek_olculemedi"], "akis_yok_n": say["akis_yok"],
                           "olcek_uygun_n": sum(1 for r in uygunlar if r["sinif"] == "olcek_uygun"),
                           "alt_nedenler": _sayim(r.get("olcek_alt_neden") for r in uygunlar
                                                  if r["sinif"] in OLCEK_SINIFLARI),
                           "ikinci_aday_n": sum(1 for r in uygunlar if r.get("olcek_ikinci_aday")),
                           "monotonluk_ihlali_tickerlar": sorted(monoton["ihlal_tickerlar"]),
                           "monotonluk_ayrinti": monoton["ihlal_tickerlar"],
                           "kill3_payi_pct": _r3(pay / akisli * 100.0) if akisli else None,
                           "kill3_pay_payda": [pay, akisli],
                           "adim0_beklenen": {"pay": ADIM0_BEKLENEN_KILL3[0], "payda": ADIM0_BEKLENEN_KILL3[1],
                                              "pct": _r3(ADIM0_BEKLENEN_KILL3[0] / ADIM0_BEKLENEN_KILL3[1] * 100.0)},
                           "ticker_f": {t: _sayim(r["olcek_f"] for r in uygunlar if r["ticker"] == t and r.get("olcek_f"))
                                        for t in sorted({r["ticker"] for r in uygunlar
                                                         if r.get("_f") is not None and r["_f"] != 1})},
                           "dislanan_satirlar": [{k: r.get(k) for k in ("ticker", "seans", "sinif", "olcek_alt_neden",
                                                                        "olcek_orani", "olcek_en_yakin",
                                                                        "olcek_sapma_pct", "ref_tetik_orani")}
                                                 for r in uygunlar if r["sinif"] in OLCEK_SINIFLARI]},
                 "plan_tipi_dagilimi": {"GAP": sum(1 for r in refli if r["plan_dal"] == "GAP"),
                                        "STOP_LIMIT": sum(1 for r in refli if r["plan_dal"] == "STOP_LIMIT"),
                                        "ref_yok": len(uygunlar) - len(refli)},
                 "tetik_ref_esit_n": sum(1 for r in refli
                                         if abs(r["tetik"] - r["ref_kapanis"]) <= TETIK_REF_ESIT_TOL + 1e-9),
                 "acilis_tetik_dal_dagilimi": _sayim(r["acilis_dal"] for r in uygunlar),
                 "yil": _sayim(r["seans"][:4] for r in uygunlar),
                 "paydalar": PAYDALAR, "sure_sn": round(time.time() - t0, 1)}
        _yaz(hedef, _json(rapor))
        ol = rapor["olcek"]
        print(f"KURU: gün dosyası yok {len(kapsam['gun_dosyasi_yok'])} · şema uygun {kapsam['sema_uygun_gun']} · "
              f"şema hatası {len(kapsam['sema_hatasi'])} · f {ol['f_dagilimi']} · eşlenemez {ol['olcek_eslenemez_n']} · "
              f"parite dışı {ol['olcek_parite_disi_n']} · ölçülemedi {ol['olcek_olculemedi_n']} · akis_yok "
              f"{ol['akis_yok_n']} · monotonluk ihlali {ol['monotonluk_ihlali_tickerlar']} · kill-3 payı "
              f"%{ol['kill3_payi_pct']} (ADIM-0 beklenen %{ol['adim0_beklenen']['pct']}) · tip "
              f"{rapor['plan_tipi_dagilimi']} → {hedef}")
        return 0
    rc = _gunleri_oku(tick_kok, uygunlar, gunler, okuyucu, True, None)
    if rc:
        return rc
    monoton = monotonluk_uygula(uygunlar)
    ozet = ozetle(satirlar, oz, pk1, monoton)
    ic_satirlar = [_satir_cikti(r) for r in satirlar]
    pk2 = {"durum": "ROL1_ELLE_DOGRULAMA_BEKLIYOR", **pk2_ornekler(satirlar, elle_ornek, tick_kok)}
    parmak = hashlib.sha256(_kanonik({"ozet": ozet, "oz_sinama": oz, "satirlar": ic_satirlar})).hexdigest()
    oz_y, satir_y, pk2_y, gizlilik = yayim_gorunumu(ozet, satirlar, pk2)
    pk = {"pk1": pk1, "pk2": pk2_y, "pk3": oz_y["pk3"]}
    sonuc = {"kart": KART_ID, "arac": arac, "girdi": girdi["ozet"], "oz_sinama": oz, "paydalar": PAYDALAR,
             "gizlilik": gizlilik, "monotonluk": monoton, "ozet": oz_y, "pk": pk,
             "sure_sn": round(time.time() - t0, 1), "parmak_izi": parmak, "satirlar": satir_y}
    _yaz(cikti / "OZET.md", _ozet_md(sonuc).encode("utf-8"))
    _yaz(hedef, _json(sonuc))
    print(f"DURUM {oz_y['durum']} · aday {oz_y['n_aday']} · parmak izi {parmak[:16]} → {hedef}")
    for h in (oz_y["h1"], oz_y["h2"]):
        print(f"  {_h_satiri(h)}")
    for e in oz_y["engeller"]:
        print(f"  engel: {e}")
    for x in pk2_y["ornekler"]:
        print(f"  PK-2 {x['ticker']} {x['seans']} f={x['olcek_f']} {x['dal']} {x['sinif']} tetik_tik={x['tetik_tik']} "
              f"L={x['limit_tik']} p0={x['p0']} dolum={x['canli_dolum']} fark={_r3(x['fark_bps'])}")
        for k in x["dilim"] or []:
            print(f"      {k['i']:>6} {k['et']} {k['fiyat']!s:>12} kosul={k['kosul']} {k['rol']}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=f"{KART_ID} replay girişi ↔ koda sadık canlı giriş kuralı, bölünme "
                                             "yeniden ölçekli (tick) — salt-okur")
    ap.add_argument("--db", required=True, help="meridian.db (salt-okur açılır)")
    ap.add_argument("--tick-kok", required=True, help="islem/<YYYY-MM-DD>.parquet dizini")
    ap.add_argument("--bar-kok", required=True, help="bar CSV dizini (state/bars)")
    ap.add_argument("--cikti", required=True, help="çıktı dizini — yazım YALNIZ burada")
    ap.add_argument("--elle-ornek", type=int, default=0, help="PK-2 örnek sayısı (0 = kapalı; kart ≥ 6)")
    ap.add_argument("--kuru", action="store_true", help="birincilsiz: ölçek dağılımı + kapsam + tip dağılımı")
    ap.add_argument("--okuyucu", choices=sorted(OKUYUCULAR), default="pyarrow")
    ap.add_argument("--betik-sha256", default=None,
                    help="stdin koşumunda ZORUNLU: koşan betiğin yerel sha256'sı (beyan)")
    a = ap.parse_args(argv)
    return olc(a.db, a.tick_kok, a.bar_kok, a.cikti, a.elle_ornek, a.kuru, a.okuyucu, a.betik_sha256)


if __name__ == "__main__":
    sys.exit(main())
