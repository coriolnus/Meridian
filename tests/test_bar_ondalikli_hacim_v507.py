"""v507 — TSK-192: ONDALIKLI HACİM. Bar defterine kesirli `volume` nasıl girdi, nerede durdurulur.

NUMARA SEÇİMİ: `ls tests | grep -E 'v50[0-9]|v51[0-9]'` ile ölçüldü (2026-09-16) — alınmış en
büyük numara v506 (`test_edg100_bar_arsiv_kiyas_v506.py`); v507 BOŞ. Çakışma yok.

KÖK NEDEN (ölçüldü 2026-09-16, EDG-2026-100 bulgusunun ardılı):
  * Canlı defterde 260 sembol / 1.357.997 satırda TEK bir ondalıklı hacim vardı:
    `state/bars/ea.csv` → `2026-07-29,…,3569440.107552`. Komşu günler TAM SAYI.
  * Değer ARİTMETİKLE ÜRETİLMEDİ: massive.com grouped/aggregate ucu `v` alanını KESİRLİ
    döndürüyor. İki bağımsız ölçüm: (a) sağlayıcı ucu EA/2026-07-29 için birebir
    `3569440.107552` verdi; (b) canlı anlık görüntü `state/massive_grouped_last.json`
    (2026-08-05 günü, 12.404 sembol) satırlarının 11.085'i kesirli hacim taşıyor.
  * Yol: `massive.to_bar` `v`yi `float(v)` ile aynen geçirir → `data.sanitize_bars` YALNIZ OHLC
    onarır (hacme dokunmaz) → `data._write_bars` diske aynen yazar. Kesir hiçbir kapıya çarpmaz.
  * Kol ne zaman açıldı: `state/massive_verify.json` → `checked_at 2026-07-29T20:59:40+00:00`,
    `verdict "uyumlu"` — `massive.write_enabled` kapısı O AN açıldı ve massive kolu zincire girdi.
    O doğrulama YALNIZ fiyat eksenini ölçüyor (kapanış sapması); hacmin tam sayı olup olmadığı
    hiç sorulmamıştı — kör nokta buradaydı.
  * Neden tek satır: massive kolunun yazdığı satırların üstüne ertesi turlarda geçmişin sahibi
    (cboe/nasdaq) TÜM seriyi getirir ve tekilleştirme `keep="last"` ile taze satırı seçer; sahibin
    getirmediği bir tarih ise defterde öylece kalır. Bu son halka ÖLÇÜLMEDİ (sağlayıcıya tarihsel
    kapsam sorgusu bu turun kapsamı dışıydı) — çiviler kalıcı sözleşmeyi ölçer, o halkayı değil.

DUYURU BİÇİMİ BİR ÖLÇÜMÜN SONUCUDUR (tur 2, inceleme bulgusu 7): yazım anında satır satır olay
basmak, 11.085/12.404 kesirli satırlık bir sağlayıcı evreninde tek koşumda binlerce olay demekti
(`obs._emit`te genel hız sınırı yok; 6 saatlik susturma yalnız `ALARM_*` jetonlarına uygulanır).
Desen deponun kendisinden alındı — `_note_ghost` (tarih başına, EVREN ÇAPINDA dedup) +
`_emit_ghost_round` (tur sonunda TEK satır) — ve `ops/bar_arsivle.py` tarafıyla AYNI: koşum sonu
tek özet. Bedel raporda sayıyla yazılı (olay/koşum: önce ~260, sonra 1).

NE ÇİVİLENİR:
  1. YAZIM BOĞAZI (`data._write_bars`) — ondalıklı hacim diske ONDALIKLI YAZILAMAZ (K1/K3).
  2. DUYURU — yuvarlama sessiz değildir (Yasa 4): tur sonunda `bar_ondalikli_hacim` özeti, ham
     değer örnekte (K1). Tam sayı hacim NE sayaç NE olay üretir (K2). Aynı bar ikinci kez
     duyurulmaz (K2b).
  3. KÖK NEDEN REGRESYONU — massive biçimindeki ham satır (`massive.to_bar` → onarım yolu
     `data._merge_repair_bar`) artık diske ondalık YAZAMAZ (K3).
  4. ARŞİV SESSİZ YUVARLAMASI GÖRÜNÜR — `ops/bar_arsivle.py` `volume`u BIGINT'e cast ederken
     kesri yutuyordu ve bunu HİÇBİR YERDE söylemiyordu (EDG-2026-100'de ancak dış kıyasla
     görüldü). Artık koşum sonunda `HACİM ONDALIK` özeti düşer (K4); temiz kaynakta hiç (K5).
  5. GÜRÜLTÜ TAVANI — 500 sembol TEK olay (K6) · yeni TARİH yeni özet, eski tarih tekrar
     duyurulmaz (K7) · örnek listesi TAVANLI, sayaç büyürken olay büyümez (K8).
  6. KAPSAM, UÇ DEĞİL (tur 3, inceleme bulgusu 1) — duyuru `load_many`/`repair_coverage` uçlarına
     bağlıyken sayacı dolduran yazım boğazına o ikisinin DIŞINDAN ulaşan yollar SESSİZDİ: tek
     başına `load_bars` (ayrı süreçlerde koşan yollar; K9) ve `barrepair` CLI aracı (K11). Kapsam
     İÇ İÇE açılır ve YALNIZ en dışta duyurur — K6'nın tavanı iç içe turda da korunur (K10) —
     ve çöküşte de duyurur, elde olan sayım kaybolmasın (K12).
  7. KURAL SINIF OLDU, LİSTE DEĞİL (tur 4, inceleme bulgusu 1) — tur 2, 3 ve 4 aynı hatayı üç kez
     üretti: yazım yolları ELLE sayıldı ve her turda biri atlandı (en son `sip_correct_provisional
     → _apply_sip_correction → _overwrite_bar`; o yol canlıda yalnız zamanlayıcının ardından
     KOŞULSUZ `repair_coverage` çağırması sayesinde duyuruyordu — SIRALAMAYA bağlı, belgesiz,
     testsiz bir kazaydı). K13 artık yolu değil KURALI ölçer ve listeyi KAYNAKTAN (ast) türetir:
     `_write_bars`i çağıran her üretim fonksiyonu ya kapsam dekoratörünü taşır ya da çağrısı bir
     kapsam bağlamının içindedir; `meridian/` + `ops/` ağaçları taranır, istisna kümesi BOŞ başlar
     ve kendi kendini denetler (gerekçesiz istisna da, ölü istisna da çiviyi kırar). Davranış
     tarafı: sip yolu tek başına da duyurur (K14a) ve çok sembollü sip turu TEK olay basar (K14b).

MUTASYON KANITI (KOŞULDU 2026-09-16 tur 2; her mutasyondan sonra dosya YEDEK KOPYADAN geri
alındı, sha256 kıyaslandı ve `__pycache__` silindi — bayat .pyc sahte yeşil üretir):
  * A — `data._write_bars`ten `df = _hacim_tam_sayi(...)` silindi: K1 · K2b · K3 · K6 · K7 · K8
    KIRMIZI (disk ondalık kalır, sayaç boş), K2 · K4 · K5 yeşil.
  * B — `_emit_hacim_round` gövdesi erken `return`: aynı altı çivi KIRMIZI, ama değer YİNE
    yuvarlanmış durumda — yani duyuru tarafı DEĞER tarafından bağımsız ölçülüyor (Yasa 4).
  * C — tur-sonu özeti yerine YAZIM ANINDA satır satır olay: K6 KIRMIZI, gerekçe ölçülü —
    "500 kesirli sembol 501 olay üretti (yazım anında 500) — gürültü tavanı yok"; K7 de KIRMIZI
    (aynı tarih sembol sembol tekrar duyuruldu). Gürültü tavanı GERÇEKTEN çivilenmiş.
  * D — `bar_arsivle._ondalik_hacim_bas` gövdesi erken `return`: YALNIZ K4 KIRMIZI, K5 yeşil.
MUTASYON KANITI (KOŞULDU 2026-09-16 tur 3; her mutasyondan sonra geri alındı ve `__pycache__`
silindi — bayat .pyc sahte yeşil üretir):
  * M1 — kapsam kapanışındaki `_emit_hacim_round()` silindi: K9·K10·K11·K12 KIRMIZI ("olay: 0"),
    eski dokuz çivi YEŞİL (onlar duyuruyu doğrudan çağırıyor — kapsam onların sorusu değil).
  * M2 — derinlik kapısı kaldırıldı (her kapanış duyurur): YALNIZ K10 KIRMIZI, ölçüsüyle —
    "iç kapsam olay bastı — tur ortasında duyuru: [0, 1, 1]".
  * M3 — `load_bars`ın kapsam dekoratörü silindi (tur 2'nin tam hâli): YALNIZ K9 KIRMIZI.
  * M4 — `barrepair.repair` kapsamı etkisiz bir bağlamla değiştirildi: YALNIZ K11 KIRMIZI.
  * M5 — kapanışta istisna varken duyuru bastırıldı: YALNIZ K12 KIRMIZI ("çöküşte sayım kayboldu").
MUTASYON KANITI (KOŞULDU 2026-09-16 tur 4; her mutasyondan sonra dosya YEDEK KOPYADAN geri alındı,
sha256 birebir kıyaslandı ve `__pycache__` silindi — bayat .pyc sahte yeşil üretir):
  * N1 — `_overwrite_bar`ın kapsam dekoratörü silindi (tur 3'ün TAM hâli): K13 KIRMIZI, ihlali
    ADRESİYLE basarak (modül yolu + satır + `_overwrite_bar()`) + K14a KIRMIZI
    ("tek başına `_overwrite_bar` SESSİZ yuvarladı (olay: 0)").
  * N2 — `sip_correct_provisional`ın kapsam dekoratörü silindi: YALNIZ K14b KIRMIZI, ölçüsüyle —
    "iç kapsam tur ortasında duyurdu: [0, 1, 1]". K13 YEŞİL kalır ve bu SINIRIN kendisidir: K13
    `_write_bars`in DOĞRUDAN çağıranlarını zorlar, toplu girişin gürültü tavanı K14b'nin işidir.
  * N3 — `_merge_repair_bar`ın kapsam dekoratörü silindi: YALNIZ K13 KIRMIZI. Bu yolu ölçen bir
    DAVRANIŞ çivisi yok (tek çağıranı zaten dekoratörlü) — yani K13 gerçekten davranış çivilerinin
    göremediği şeyi görüyor.
  * N4 — SINIF KANITI: `meridian/barrepair.py`ye kapsamsız, YENİ bir yazım yolu eklendi
    (`_mutasyon_yeni_yazim_yolu`): K13 KIRMIZI, doğduğu koşumda, adresiyle. Hiçbir davranış çivisi
    o fonksiyonu tanımıyordu — sabit listeli bir çivinin KAÇIRACAĞI durum tam olarak budur.
  * N5 — `barrepair.repair`in `with data._hacim_turu():` bloğu `contextlib.nullcontext()` ile
    değiştirildi: K13 + K11 KIRMIZI. K13 yalnız dekoratörü değil `with` BİÇİMİNİ de tanıyor
    (iki meşru koruma biçimi var, çivi ikisini de ayırt ediyor).
  * N6 — `K13_BEYANLI_ISTISNA`ya ihlal ETMEYEN bir anahtar kondu: K13 KIRMIZI ("ÖLÜ istisna
    (artık ihlal değil, kaldırılmalı)"). İstisna kümesi çürüyerek muafiyet biriktiremez.
  * N7 — `_write_bars`in ikinci bir tanımı eklendi: K13 KIRMIZI ("tanımı 2 yerde — yazım boğazı
    tekliğini kaybetti"). Tarama sessizce körleşemez; boşa dönen bir çivi "yeşil" sayılmaz.
GERÇEK DEFTERE DOKUNULMAZ: her çivi `sandbox_state` altında koşar; canlı `state/bars/` açılmaz.
"""

from __future__ import annotations

import ast
from pathlib import Path

import duckdb
import pandas as pd
import pytest

from meridian.adapters import alpaca as _alpaca
from meridian.adapters import data as _data
from meridian.adapters import massive as _massive
from ops import bar_arsivle

#: EA 2026-07-29'un canlı defterdeki HAM değeri — bu dosyanın ölçtüğü olgunun ta kendisi.
EA_HAM_HACIM = 3569440.107552


def _seanslar(ay: str, adet: int) -> list[str]:
    """`ay` (AAAA-AA) içindeki ilk `adet` GERÇEK XNYS seansı — takvimin tek kaynağı `_sessions`.
    Uydurma tarih kullanılsaydı `sanitize_bars` satırı hayalet sayıp düşürür ve çivi ölçtüğünü
    sandığı şeyi ölçmezdi (v435'in aynı gerekçesi)."""
    ses = sorted(g for g in _data._sessions() if g.startswith(ay))
    if len(ses) < adet:
        pytest.skip(f"takvim ölçülemedi ya da {ay} için {adet} seans yok (bulunan: {len(ses)})")
    return ses[:adet]


@pytest.fixture(autouse=True)
def _hacim_defteri_temiz():
    """Süreç-içi sayaç, tarih-duyuru defteri VE tur derinliği testler arasında SIZMAZ: biri dolu
    kalsaydı bir sonraki çivi kendi ölçtüğü turu değil, öncekinin kalıntısını okurdu. Derinlik de
    sıfırlanır — sızan bir derinlik, kapsamı 'hep iç kapsam' yapıp duyuruyu SESSİZCE yutardı."""
    _data._HACIM_ONDALIK.clear()
    _data._HACIM_ONDALIK_DUYURULDU.clear()
    _data._HACIM_TUR_DERINLIK = 0
    yield
    _data._HACIM_ONDALIK.clear()
    _data._HACIM_ONDALIK_DUYURULDU.clear()
    _data._HACIM_TUR_DERINLIK = 0


@pytest.fixture
def uyarilar(monkeypatch):
    """`obs.warn` yakalayıcı — olay ADIYLA ve alanlarıyla ölçülür (varlığı değil, içeriği)."""
    import meridian.obs as obs
    kayit: list[tuple[str, dict]] = []
    monkeypatch.setattr(obs, "warn", lambda ev, **kw: kayit.append((ev, kw)))
    return kayit


def _ozetler(uyarilar: list) -> list[dict]:
    return [kw for ev, kw in uyarilar if ev == _data.HACIM_ONDALIK_OLAY]


def _cerceve(gunler: list[str], hacimler: list[float]) -> pd.DataFrame:
    """`COLS` şemasında sentetik çerçeve; fiyatlar yumuşak (sıçrama karantina tetiklerdi)."""
    satirlar = []
    for i, (g, h) in enumerate(zip(gunler, hacimler)):
        c = 209.0 + i * 0.1
        satirlar.append({"date": pd.Timestamp(g), "open": c, "high": c + 0.3,
                         "low": c - 0.3, "close": c + 0.1, "volume": h})
    return pd.DataFrame(satirlar)[_data.COLS]


# ================================ K1 — YAZIM BOĞAZI + TUR SONU ÖZETİ ===========================

def test_K1_ondalikli_hacim_TAM_SAYI_yazilir_ve_TUR_SONUNDA_DUYURULUR(sandbox_state, uyarilar):
    """Sözleşme + Yasa 4 birlikte: değer tam sayıya bağlanır VE duyurulur — ama duyuru YAZIM
    ANINDA değil TUR SONUNDA, tek özette (gürültü tavanı; gerekçe `_emit_hacim_round`da)."""
    gunler = _seanslar("2024-01", 3)
    cp = _data._cache_path("EA")
    _data._write_bars(_cerceve(gunler, [3710592.0, EA_HAM_HACIM, 4143546.0]), cp)

    diskte = pd.read_csv(cp)
    assert list(diskte["volume"]) == [3710592.0, 3569440.0, 4143546.0], \
        f"ondalıklı hacim diske ONDALIKLI yazıldı: {list(diskte['volume'])}"
    assert _ozetler(uyarilar) == [], "yazım anında olay basıldı — tur sonu deseni bozuldu"
    assert _data._HACIM_ONDALIK[gunler[1]]["rows"] == 1, "sayaç yazım anında dolmadı"

    _data._emit_hacim_round()
    ozet = _ozetler(uyarilar)
    assert len(ozet) == 1, f"tur sonunda tek özet beklenir: {ozet}"
    assert ozet[0]["rows"] == 1 and ozet[0]["tickers"] == 1 and ozet[0]["dates"] == gunler[1]
    assert f"EA@{gunler[1]}={EA_HAM_HACIM!r}" in ozet[0]["ornekler"], \
        f"HAM değer duyurulmadı — kayıp ölçülemez: {ozet[0]['ornekler']}"
    assert ozet[0]["max_kesir"] == round(abs(EA_HAM_HACIM - round(EA_HAM_HACIM)), 6)
    assert ozet[0]["max_kesir_ticker"] == "EA"


# ================================ K2 — GÜRÜLTÜ BEDELİ ==========================================

def test_K2_tam_sayi_hacim_NE_SAYAC_NE_OLAY_uretir(sandbox_state, uyarilar):
    """Sağlıklı tur sessizdir: kapı her yazımda sayaç/olay üretseydi defter gürültüye boğulurdu."""
    gunler = _seanslar("2024-01", 3)
    cp = _data._cache_path("AAPL")
    _data._write_bars(_cerceve(gunler, [1000000.0, 2000000.0, 3000000.0]), cp)
    _data._emit_hacim_round()

    assert list(pd.read_csv(cp)["volume"]) == [1000000.0, 2000000.0, 3000000.0]
    assert _data._HACIM_ONDALIK == {}, "tam sayı hacim sayaca yazıldı"
    assert _ozetler(uyarilar) == [], "tam sayı hacimde özet basıldı — sağlıklı tur gürültülü"


def test_K2b_ayni_tarih_IKINCI_turda_tekrar_duyurulmaz(sandbox_state, uyarilar):
    """Dedup TARİH bazındadır: aynı seans ikinci turda yeniden bağırmaz (bir bozuk bar günlerce
    alarm üretemez). Değer sözleşmesi ikinci yazımda da TUTAR."""
    gunler = _seanslar("2024-01", 2)
    cp = _data._cache_path("EA")
    cerceve = _cerceve(gunler, [3710592.0, EA_HAM_HACIM])
    _data._write_bars(cerceve, cp)
    _data._emit_hacim_round()
    _data._write_bars(cerceve, cp)
    _data._emit_hacim_round()

    assert list(pd.read_csv(cp)["volume"]) == [3710592.0, 3569440.0]
    assert len(_ozetler(uyarilar)) == 1, "aynı tarih iki kez duyuruldu"


# ================================ K3 — KÖK NEDEN REGRESYONU ====================================

def test_K3_kok_neden_massive_ham_satiri_TASIR_yazim_bogazi_DURDURUR(sandbox_state, uyarilar):
    """Kök nedenin İKİ yarısı tek çivide: (a) sağlayıcı satırı kesri AYNEN taşır — ondalık bir
    aritmetik ürünü DEĞİL, kaynak verisidir; (b) aynı satır onarım yolundan diske girerken TAM
    SAYIYA bağlanır. (a) bir KARAKTERİZASYONDUR: sözleşme bilerek yazım boğazına konmuştur (her
    kol aynı kapıdan geçsin diye). Sözleşme bir gün kaynağa taşınırsa bu satır BİLİNÇLİ olarak
    güncellenir — sessizce değil."""
    ham = {"t": None, "o": 209.14, "h": 209.16, "l": 208.52, "c": 208.91, "v": EA_HAM_HACIM}
    gunler = _seanslar("2024-01", 3)
    bar = _massive.to_bar(ham, date=gunler[2])
    assert bar["volume"] == EA_HAM_HACIM, "sağlayıcı kesri kaynak katmanında ZATEN kayboluyor"

    cp = _data._cache_path("EA")
    _data._write_bars(_cerceve(gunler[:2], [3710592.0, 4143546.0]), cp)
    assert _data._merge_repair_bar("EA", {**bar, "date": gunler[2]}) is True

    diskte = pd.read_csv(cp)
    assert len(diskte) == 3, "onarım barı eklenmedi — çivi yolu ölçemedi"
    assert list(diskte["volume"]) == [3710592.0, 4143546.0, 3569440.0], \
        f"massive kaynaklı satır diske ONDALIKLI girdi: {list(diskte['volume'])}"

    _data._emit_hacim_round()
    ozet = _ozetler(uyarilar)
    assert len(ozet) == 1 and ozet[0]["dates"] == gunler[2], ozet


# ================================ K6/K7/K8 — GÜRÜLTÜ TAVANI ====================================

def test_K6_500_sembol_TEK_ozet_uretir(sandbox_state, uyarilar):
    """ÖLÇÜLMÜŞ GEREKÇE: sağlayıcı anlık görüntüsünde 11.085/12.404 sembol kesirli hacim taşıyor.
    Yazım anında olay basılsaydı evren kadar olay düşerdi; özet TEK olaydır ve sayıları TAŞIR."""
    gun = _seanslar("2024-01", 1)[0]
    for i in range(500):
        _data._write_bars(_cerceve([gun], [1000000.0 + i + 0.123456]),
                          _data._cache_path(f"SYM{i:03d}"))
    yazim_aninda = len(_ozetler(uyarilar))

    _data._emit_hacim_round()
    ozet = _ozetler(uyarilar)
    # SAYI ÖNCE ÖLÇÜLÜR: asıl sözleşme "olay sayısı 1"dir; yazım anındaki sıfır onun nedenidir.
    assert len(ozet) == 1, (f"500 kesirli sembol {len(ozet)} olay üretti (yazım anında "
                            f"{yazim_aninda}) — gürültü tavanı yok")
    assert yazim_aninda == 0, "yazım anında olay basıldı — tur sonu deseni bozuldu"
    assert ozet[0]["rows"] == 500 and ozet[0]["tickers"] == 500 and ozet[0]["n_dates"] == 1
    assert ozet[0]["dates"] == gun


def test_K7_YENI_TARIH_yeni_ozet_eski_tarih_SESSIZ(sandbox_state, uyarilar):
    """Dedup EVREN ÇAPINDA ve TARİH bazındadır: ikinci tur yalnız YENİ tarihi duyurur, eskisini
    tekrar etmez. "Hiç duyurma" ile "bir kez duyur" arasındaki farkı bu çivi ölçer."""
    g1, g2 = _seanslar("2024-01", 2)
    _data._write_bars(_cerceve([g1], [1000000.5]), _data._cache_path("EA"))
    _data._emit_hacim_round()
    _data._write_bars(_cerceve([g1, g2], [1000000.5, 2000000.25]), _data._cache_path("MSFT"))
    _data._emit_hacim_round()

    ozet = _ozetler(uyarilar)
    assert len(ozet) == 2, f"iki ayrı tarih iki özet vermedi: {ozet}"
    assert ozet[0]["dates"] == g1 and ozet[1]["dates"] == g2, ozet
    assert ozet[1]["rows"] == 1, "ikinci özet ESKİ tarihin satırlarını da saydı"


def test_K8_ornek_listesi_TAVANLI_sayac_buyur_olay_BUYUMEZ(sandbox_state, uyarilar):
    """Bedel yasası: örnek listesi tavanlıdır (`HACIM_ORNEK_SATIR`) ama SAYIM tam kalır — olay
    büyümeden kaç satır/sembolün etkilendiği ölçülebilir."""
    gun = _seanslar("2024-01", 1)[0]
    n = _data.HACIM_ORNEK_SATIR * 4
    for i in range(n):
        _data._write_bars(_cerceve([gun], [500000.0 + i + 0.5]), _data._cache_path(f"T{i:02d}"))
    _data._emit_hacim_round()

    ozet = _ozetler(uyarilar)[0]
    assert ozet["rows"] == n and ozet["tickers"] == n, "sayaç tavanla birlikte kırpıldı"
    assert len(ozet["ornekler"].split("; ")) == _data.HACIM_ORNEK_SATIR, ozet["ornekler"]
    assert ozet["ornek_tavani"] == _data.HACIM_ORNEK_SATIR, "tavan okuyucuya BEYAN edilmiyor"


# ================================ K4/K5 — ARŞİVİN SESSİZ YUVARLAMASI ===========================

def _csv_yaz(dizin, dosya: str, gunler: list[str], hacimler: list[float]) -> None:
    dizin.mkdir(parents=True, exist_ok=True)
    satirlar = ["date,open,high,low,close,volume"]
    for i, (g, h) in enumerate(zip(gunler, hacimler)):
        c = 100.0 + i
        satirlar.append(f"{g},{c:.2f},{c + 0.5:.2f},{c - 0.5:.2f},{c + 0.2:.2f},{h!r}")
    (dizin / dosya).write_text("\n".join(satirlar) + "\n", encoding="utf-8")


def test_K4_arsiv_BIGINT_yuvarlamasini_ADIYLA_bildirir(sandbox_state, tmp_path, capsys):
    """Arşiv şeması BIGINT KALIR (hisse adedi tam sayıdır) — değişen, kaybın BEYAN EDİLMESİDİR.
    Kayıp gerçek: parquet'teki değer CSV'dekinden farklıdır ve çivi ikisini de ölçer."""
    kaynak, hedef = tmp_path / "bars_kaynak", tmp_path / "barlar_hedef"
    gunler = _seanslar("2024-01", 3)
    _csv_yaz(kaynak, "ea.csv", gunler, [3710592.0, EA_HAM_HACIM, 4143546.0])

    rc = bar_arsivle.main(["--kaynak-dizin", str(kaynak), "--hedef", str(hedef), "--uygula"])
    yakalanan = capsys.readouterr()
    assert rc == 0, yakalanan.out + yakalanan.err
    assert "HACİM ONDALIK" in yakalanan.err, \
        f"arşiv yuvarlamayı SESSİZCE yaptı — stderr: {yakalanan.err}"
    assert "1 satır" in yakalanan.err and gunler[1] in yakalanan.err, yakalanan.err
    assert repr(EA_HAM_HACIM) in yakalanan.err, "HAM değer bildirilmedi — kayıp ölçülemez"

    con = duckdb.connect()
    try:
        degerler = [r[0] for r in con.execute(
            f"SELECT volume FROM read_parquet('{hedef / 'EA.parquet'}') ORDER BY date").fetchall()]
    finally:
        con.close()
    assert degerler == [3710592, 3569440, 4143546], \
        f"kayıp beyan edildi ama ölçüm tutmadı: {degerler}"


def test_K5_tam_sayi_kaynakta_arsiv_SUSAR(sandbox_state, tmp_path, capsys):
    """"Her koşumda sıfır" satırı bulgu değil gürültüdür: temiz kaynakta özet HİÇ basılmaz."""
    kaynak, hedef = tmp_path / "bars_kaynak", tmp_path / "barlar_hedef"
    _csv_yaz(kaynak, "ea.csv", _seanslar("2024-01", 3), [3710592.0, 3569440.0, 4143546.0])

    rc = bar_arsivle.main(["--kaynak-dizin", str(kaynak), "--hedef", str(hedef), "--uygula"])
    yakalanan = capsys.readouterr()
    assert rc == 0, yakalanan.out + yakalanan.err
    assert "HACİM ONDALIK" not in yakalanan.err, yakalanan.err


# ======================= K9/K10/K11/K12 — KAPSAM (uç değil) ====================================

def _sahte_fetch(monkeypatch, cerceve: pd.DataFrame, kaynak: str = "cboe"):
    """`load_bars`ın AĞ kolunu keser ve `cerceve`yi "çekilmiş" sayar (kaynak adı da yazılır —
    `_LAST_SOURCE` boş kalsaydı yükleyicinin sahiplik/dikiş dalları ölçülen yolu değiştirirdi)."""
    def _f(ticker, start, end, timeout=30.0, incremental_ok=False, **kw):
        _data._LAST_SOURCE[str(ticker).upper()] = kaynak
        return cerceve.copy()
    monkeypatch.setattr(_data, "fetch", _f)


def _hayalet_gun(baslangic: str) -> str:
    """`baslangic`tan SONRAKİ ilk takvim-DIŞI gün. Tarih uydurulmaz, takvimden TÜRETİLİR:
    kapının tek kaynağı `_sessions` ve hayalet satırın tanımı "o kaynakta olmayan gün"dür."""
    ses = _data._sessions()
    g = pd.Timestamp(baslangic)
    for _ in range(14):
        g += pd.Timedelta(days=1)
        if g.strftime("%Y-%m-%d") not in ses:
            return g.strftime("%Y-%m-%d")
    pytest.skip("takvimde 14 gün içinde seans-dışı gün yok — hayalet satır kurgulanamaz")


def test_K9_TEK_BASINA_load_bars_da_DUYURUR_load_many_CAGRILMADAN(sandbox_state, uyarilar, monkeypatch):
    """KAPSAM UÇTA DEĞİL: `load_bars` ölçüm/api/veri-kümesi/yeniden-hesap yollarından TEK BAŞINA
    çağrılır ve bunların bir kısmı AYRI süreçlerde koşar — o süreçte `load_many` hiç çalışmayabilir.
    Duyuru uçlara bağlıyken bu yolda sayaç dolup olay HİÇ basılmıyordu (gecikme değil KAYIP)."""
    gunler = _seanslar("2024-01", 3)
    _sahte_fetch(monkeypatch, _cerceve(gunler, [3710592.0, EA_HAM_HACIM, 4143546.0]))

    df = _data.load_bars("EA", gunler[0], gunler[-1], polite_delay=0.0)

    assert len(df) == 3, f"yükleyici yolu ölçülemedi (dönen satır: {len(df)})"
    assert list(pd.read_csv(_data._cache_path("EA"))["volume"]) == [3710592.0, 3569440.0, 4143546.0]
    ozet = _ozetler(uyarilar)
    assert len(ozet) == 1, f"tek başına `load_bars` turu duyurmadı (olay: {len(ozet)})"
    assert ozet[0]["rows"] == 1 and ozet[0]["tickers"] == 1 and ozet[0]["dates"] == gunler[1]
    assert f"EA@{gunler[1]}={EA_HAM_HACIM!r}" in ozet[0]["ornekler"], ozet[0]["ornekler"]
    assert _data._HACIM_TUR_DERINLIK == 0, "kapsam kapanmadı — derinlik sızdı"


def test_K10_IC_ICE_kapsam_TEK_OZET_verir_sayilar_TOPLAM(sandbox_state, uyarilar, monkeypatch):
    """`load_many` içindeki her `load_bars` bir İÇ kapsamdır: olay YALNIZ en dışta basılır.
    Bu çivi K6'nın (gürültü tavanı) iç içe hâlidir — kapsam uçlara değil derinliğe bağlı."""
    g1, g2 = _seanslar("2024-01", 2)
    ic_olaylar: list[int] = []

    def _f(ticker, start, end, timeout=30.0, incremental_ok=False, **kw):
        # HER SEMBOL ÇAĞRISINDA O ANA KADARKİ OLAY SAYISI: iç kapsam duyursaydı 0 kalmazdı.
        ic_olaylar.append(len(_ozetler(uyarilar)))
        _data._LAST_SOURCE[str(ticker).upper()] = "cboe"
        return _cerceve([g1, g2], [1000000.25, 2000000.5])
    monkeypatch.setattr(_data, "fetch", _f)

    _data.load_many(["EA", "MSFT", "NVDA"], g1, g2, use_cache=False)

    ozet = _ozetler(uyarilar)
    assert ic_olaylar == [0, 0, 0], f"iç kapsam olay bastı — tur ortasında duyuru: {ic_olaylar}"
    assert len(ozet) == 1, f"3 sembollük iç içe tur {len(ozet)} olay üretti — gürültü tavanı yok"
    assert ozet[0]["rows"] == 6 and ozet[0]["tickers"] == 3 and ozet[0]["n_dates"] == 2, ozet[0]
    assert ozet[0]["dates"] == f"{g1},{g2}", ozet[0]["dates"]
    assert _data._HACIM_TUR_DERINLIK == 0, "kapsam kapanmadı — derinlik sızdı"


def test_K11_barrepair_CLI_YOLU_da_DUYURUR(sandbox_state, uyarilar):
    """`python -m meridian.barrepair` AYRI bir süreçtir: ne yükleyici turu ne onarım süpürmesi
    koşar. Yazım `_write_bars`ten geçtiği için sayaç dolar — kapsam olmasaydı süreç biter ve olay
    HİÇ basılmazdı. Hayalet tarafının `bar_ghost_repair_applied` güvencesinin hacim karşılığı."""
    from meridian import barrepair

    g1, g2 = _seanslar("2024-01", 2)
    hayalet = _hayalet_gun(g2)
    cp = _data._cache_path("EA")
    cp.parent.mkdir(parents=True, exist_ok=True)
    # KURULUM `_write_bars` İLE YAPILMAZ: o kapı kesri yuvarlar ve çivi, ölçtüğünü sandığı şeyi
    # ölçmezdi (diskte ZATEN ondalıklı duran bir defteri onarım yolundan geçiriyoruz).
    _cerceve([g1, g2, hayalet], [3710592.0, EA_HAM_HACIM, 4000000.0]).to_csv(cp, index=False)

    rapor = barrepair.repair(["EA"], apply=True)

    assert rapor["ghost_rows"] == 1, f"hayalet satır kurgulanamadı: {rapor}"
    assert len(rapor["written"]) == 1, f"onarım yazmadı — çivi yolu ölçemedi: {rapor}"
    assert list(pd.read_csv(cp)["volume"]) == [3710592.0, 3569440.0], "onarım ondalık bıraktı"
    ozet = _ozetler(uyarilar)
    assert len(ozet) == 1, f"CLI onarım yolu SESSİZ yuvarladı (olay: {len(ozet)})"
    assert ozet[0]["dates"] == g2 and ozet[0]["rows"] == 1, ozet[0]
    assert _data._HACIM_TUR_DERINLIK == 0, "kapsam kapanmadı — derinlik sızdı"


def test_K12_ISTISNADA_da_DUYURULUR_ve_derinlik_SIFIRLANIR(sandbox_state, uyarilar):
    """ÇÖKÜŞTE SUSMAK, SAYIMI KAYBETMEKTİR: `with` kapanışı istisnada da koşar ve elde olan özet
    basılır. İki yarı ayrı ayrı ölçülür — çıplak kapsam VE dekoratörle sarılmış giriş."""
    g1, g2 = _seanslar("2024-01", 2)

    with pytest.raises(RuntimeError, match="tur ortasinda cokus"):
        with _data._hacim_turu():
            _data._write_bars(_cerceve([g1], [1000000.5]), _data._cache_path("EA"))
            assert _ozetler(uyarilar) == [], "kapsam içinde erken duyuru — tur sonu deseni bozuldu"
            raise RuntimeError("tur ortasinda cokus")

    ozet = _ozetler(uyarilar)
    assert len(ozet) == 1, f"çöküşte sayım kayboldu (olay: {len(ozet)})"
    assert ozet[0]["dates"] == g1 and ozet[0]["rows"] == 1, ozet[0]
    assert _data._HACIM_TUR_DERINLIK == 0, "istisnadan sonra derinlik sızdı — tur kalıcı sessizleşir"

    @_data._hacim_turu_kapsami
    def _coken_giris():
        _data._write_bars(_cerceve([g2], [2000000.75]), _data._cache_path("MSFT"))
        raise RuntimeError("dekorator turu coktu")

    with pytest.raises(RuntimeError, match="dekorator turu coktu"):
        _coken_giris()

    ozet = _ozetler(uyarilar)
    assert len(ozet) == 2, f"dekoratör yolu çöküşte duyurmadı: {ozet}"
    assert ozet[1]["dates"] == g2 and ozet[1]["rows"] == 1, ozet[1]
    assert _data._HACIM_TUR_DERINLIK == 0, "dekoratör istisnasında derinlik sızdı"


# =============== K13 — SINIF ÇİVİSİ: yazım yollarını KAYNAKTAN türet (liste EZBERLEME) =========
#
# NEDEN STATİK ÇİVİ, NEDEN DAHA FAZLA DAVRANIŞ ÇİVİSİ DEĞİL (tur 4, 2026-09-16): tur 2, tur 3 ve
# tur 4 aynı sınıf hatayı üretti — `_write_bars`e ulaşan yollar ELLE sayıldı ve her turda biri
# atlandı (sırasıyla: tek başına `load_bars` + `barrepair` CLI'ı, sonra `sip_correct_provisional
# → _apply_sip_correction → _overwrite_bar`). Her atlanan yol için bir davranış çivisi yazmak
# GEÇMİŞİ kapatır, GELECEĞİ kapatmaz: yarın eklenen beşinci yol yine sessiz olur. O yüzden bu çivi
# tek tek yolları değil KURALI ölçer ve yol listesini KAYNAK KODUNDAN (ast) türetir.
#
# TEK-KAYNAK YASASI: burada sabit bir "korunan fonksiyonlar" listesi YOKTUR. Aranan üç sembolün
# adı bile canlı modül nesnelerinden alınır (`_data._write_bars.__name__` vb.) — biri yeniden
# adlandırılırsa çivi SESSİZ kalmaz, AttributeError ile GÜRÜLTÜLÜ düşer.

#: BEYANLI İSTİSNA — BOŞ BAŞLAR (tur 4, 2026-09-16) ve öyle kalması beklenir.
#: Anahtar: "<depoya göre modül yolu>::<fonksiyon>"; değer: ≥20 karakter GEREKÇE (Yasa 4'ün
#: `# sessiz-yutma:` kaçışıyla aynı disiplin). Kapsam dışında bırakılan bir yazım yolu ancak
#: BURAYA yazılarak geçebilir; gerekçesiz istisna da, ARTIK İHLAL OLMAYAN ölü istisna da çiviyi
#: kırar (istisna kümesi kendi kendini denetler — `pitlaw.BILINEN_IHLALLER` ile aynı desen).
K13_BEYANLI_ISTISNA: dict[str, str] = {}


def _sembol_adi(dugum) -> str | None:
    """`f(...)` / `mod.f(...)` / `@mod.dek` biçimlerinde ÇAĞRILAN/UYGULANAN sembolün adı; yoksa None.
    Modül öneki bilinçli olarak YOK SAYILIR: aynı fonksiyona `data._write_bars` ve `_write_bars`
    diye iki ayrı yazım biçiminden ulaşılır (barrepair ↔ data) ve kural ikisinde de aynıdır."""
    if isinstance(dugum, ast.Name):
        return dugum.id
    if isinstance(dugum, ast.Attribute):
        return dugum.attr
    return None


def _gez(dugum, modul: str, fn: str, dekoratorlu: bool, kapsamda: bool,
         cagrilar: list[dict], adlar: tuple[str, str, str]) -> None:
    """Ağacı gezerek `yazim` çağrılarını bulur ve HER BİRİNİ iki soruyla etiketler: içinde
    bulunduğu fonksiyon kapsam DEKORATÖRÜNÜ taşıyor mu, çağrı bir kapsam `with`inin İÇİNDE mi?"""
    yazim, dekorator, uretici = adlar
    for c in ast.iter_child_nodes(dugum):
        if isinstance(c, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # YENİ GÖVDE = YENİ KORUMA SORUSU: dıştaki `with` iç fonksiyonun ÇAĞRILDIĞI anda açık
            # olmayabilir (fonksiyon bir geri-çağrı olarak saklanabilir). `kapsamda` DEVRALINMAZ.
            _gez(c, modul, c.name if fn == _K13_MODUL_GOVDESI else f"{fn}.{c.name}",
                 any(_sembol_adi(d) == dekorator for d in c.decorator_list), False, cagrilar, adlar)
            continue
        if isinstance(c, ast.Lambda):
            # LAMBDA DA BİR SINIRDIR, aynı gerekçeyle (gövde tanımlandığında değil çağrıldığında koşar).
            _gez(c, modul, f"{fn}.<lambda>", False, False, cagrilar, adlar)
            continue
        if isinstance(c, (ast.With, ast.AsyncWith)):
            acar = any(isinstance(i.context_expr, ast.Call)
                       and _sembol_adi(i.context_expr.func) == uretici for i in c.items)
            _gez(c, modul, fn, dekoratorlu, kapsamda or acar, cagrilar, adlar)
            continue
        if isinstance(c, ast.Call) and _sembol_adi(c.func) == yazim:
            cagrilar.append({"modul": modul, "fonksiyon": fn, "satir": c.lineno,
                             "dekorator": dekoratorlu, "kapsam": kapsamda})
        _gez(c, modul, fn, dekoratorlu, kapsamda, cagrilar, adlar)


#: Bir fonksiyonun DIŞINDA (modül gövdesinde) duran çağrının "fonksiyon" adı — anahtar da bundan üretilir.
_K13_MODUL_GOVDESI = "<modül gövdesi>"


def _kapsam_taramasi(kokler: list[Path], depo: Path,
                     adlar: tuple[str, str, str]) -> tuple[list[dict], int, int]:
    """(çağrılar, taranan .py sayısı, tanım sayısı) — yazım boğazına yapılan TÜM çağrılar + çivinin
    boşa dönmediğini kanıtlayan iki sayaç. Tanım sayısı 1 değilse sembol taşınmış/kopyalanmıştır
    ve tarama artık ölçtüğünü sandığı şeyi ölçmüyordur."""
    yazim = adlar[0]
    cagrilar: list[dict] = []
    taranan = tanim = 0
    for kok in kokler:
        for py in sorted(kok.rglob("*.py")):
            taranan += 1
            kaynak = py.read_text(encoding="utf-8")
            if yazim not in kaynak:
                continue                   # ucuz eleme: ast bedeli yalnız adı GEÇEN dosyaya ödenir
            agac = ast.parse(kaynak, filename=str(py))
            modul = py.resolve().relative_to(depo).as_posix()
            tanim += sum(1 for n in ast.walk(agac)
                         if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == yazim)
            _gez(agac, modul, _K13_MODUL_GOVDESI, False, False, cagrilar, adlar)
    return cagrilar, taranan, tanim


def _k13_anahtar(c: dict) -> str:
    return f"{c['modul']}::{c['fonksiyon']}"


def test_K13_write_bars_cagiran_HER_uretim_YOLU_kapsamda_KAYNAKTAN_turetilir(sandbox_state):
    """SÖZLEŞME TEK CÜMLE: `_write_bars`i çağıran her üretim fonksiyonu ya kapsam dekoratörünü
    taşır ya da çağrısı bir kapsam bağlamının içindedir. Yol listesi ezberlenmez — `meridian/` ve
    `ops/` ağaçları ast ile taranır; yarın eklenen yeni bir yazım yolu doğduğu gün bu çivi öter.

    KAPSAM `_write_bars`IN KENDİSİNE KONMAZ: o zaman her yazımda derinlik sıfıra düşer, tur sonu
    özeti satır satır dağılır ve tur 1'in gürültü seli (232 olay/koşum) geri gelir. Kural
    ÇAĞIRANA bakar — bu çivinin ölçtüğü şey de budur."""
    adlar = (_data._write_bars.__name__, _data._hacim_turu_kapsami.__name__,
             _data._hacim_turu.__name__)
    paket = Path(_data.__file__).resolve().parent.parent          # …/meridian
    depo = paket.parent
    kokler = [k for k in (paket, depo / "ops") if k.is_dir()]
    assert len(kokler) == 2, f"üretim ağaçları bulunamadı (bulunan: {[str(k) for k in kokler]})"

    cagrilar, taranan, tanim = _kapsam_taramasi(kokler, depo, adlar)

    # BOŞA DÖNMEME KANITI: tarama bir şey bulmadıysa çivi "yeşil" değil KÖRdür.
    assert taranan > 0, f"hiç .py taranmadı — ağaç yolu yanlış: {[str(k) for k in kokler]}"
    assert tanim == 1, f"`{adlar[0]}` tanımı {tanim} yerde — yazım boğazı tekliğini kaybetti"
    assert len(cagrilar) >= 2, \
        f"`{adlar[0]}` çağrısı bulunamadı ({len(cagrilar)}) — tarayıcı sessizce körleşti"

    ihlaller = [c for c in cagrilar if not (c["dekorator"] or c["kapsam"])]
    acikta = [c for c in ihlaller if _k13_anahtar(c) not in K13_BEYANLI_ISTISNA]
    assert not acikta, (
        "KAPSAMSIZ YAZIM YOLU — ondalıklı hacim sayacı dolar ama duyuru DÜŞMEZ (kalıcı kayıp):\n"
        + "\n".join(f"  {c['modul']}:{c['satir']} → {c['fonksiyon']}()" for c in acikta)
        + f"\n  ÇÖZÜM: o fonksiyona `@{adlar[1]}` ekle ya da çağrıyı `with {adlar[2]}():` içine al "
          f"(kapsam iç içe güvenlidir). Gerekçeli istisna: K13_BEYANLI_ISTISNA.")

    # İSTİSNA KÜMESİ KENDİNİ DENETLER: gerekçesiz istisna da, ÖLÜ istisna da geçmez.
    for anahtar, gerekce in K13_BEYANLI_ISTISNA.items():
        assert len(str(gerekce).strip()) >= 20, f"gerekçesiz istisna: {anahtar!r} → {gerekce!r}"
    olu = sorted(set(K13_BEYANLI_ISTISNA) - {_k13_anahtar(c) for c in ihlaller})
    assert not olu, f"ÖLÜ istisna (artık ihlal değil, kaldırılmalı): {olu}"


# =============== K14 — SIP DÜZELTME YOLU: duyurur, ama toplu turda TEK OLAY ====================

def _sip_defterine_yaz(ticker: str, gunler: list[str], seans: str, kapanis: float) -> Path:
    """Diskte TAM SAYI hacimli bir defter + defterde o seans için IEX damgası. Kurulum bilerek
    `_write_bars` ile YAPILMAZ: o kapı kesri yuvarlar ve çivi ölçtüğünü sandığı şeyi ölçmezdi."""
    cp = _data._cache_path(ticker)
    cp.parent.mkdir(parents=True, exist_ok=True)
    _cerceve(gunler, [3710592.0] * len(gunler)).to_csv(cp, index=False)
    _data._note_provisional(ticker, {seans: {
        "source": _data.ALPACA_SOURCE, "close": kapanis, "iex_volume": 5_000.0,
        "volume": 3710592.0, "ratio": 20.0, "volume_scaled": True,
        "at": "2026-07-29T20:20:00+00:00"}})
    return cp


def test_K14a_TEK_BASINA_overwrite_bar_da_DUYURUR(sandbox_state, uyarilar):
    """SIRALAMAYA BAĞLI KAZA KAPANDI: `sip_correct_provisional → _apply_sip_correction →
    _overwrite_bar` yolu tur 3'te kapsam DIŞINDAYDI ve duyuru yalnız zamanlayıcının hemen ardından
    `repair_coverage` çağırması sayesinde düşüyordu. `_overwrite_bar` artık kendi kapsamını açar —
    tek başına çağrıldığı HER bağlamda (test, yeniden oynatma, gelecekteki bir araç) duyurur."""
    gunler = _seanslar("2024-01", 3)
    seans, kapanis = gunler[1], 209.2                     # `_cerceve`nin i=1 satırındaki kapanış
    cp = _data._cache_path("EA")
    cp.parent.mkdir(parents=True, exist_ok=True)
    _cerceve(gunler, [3710592.0, 4143546.0, 3900000.0]).to_csv(cp, index=False)

    # YALNIZ HACİM DEĞİŞİR: fiyat sabit bırakılır ki ölçülen şey hacim kapısı olsun (fiyat sıçraması
    # `sanitize_bars` karantinasını tetikleyip satırı düşürseydi çivi başka bir dalı ölçerdi).
    assert _data._overwrite_bar("EA", {"date": seans, "close": kapanis,
                                       "volume": EA_HAM_HACIM}) is True

    assert list(pd.read_csv(cp)["volume"]) == [3710592.0, 3569440.0, 3900000.0], "ondalık diske indi"
    ozet = _ozetler(uyarilar)
    assert len(ozet) == 1, f"tek başına `_overwrite_bar` SESSİZ yuvarladı (olay: {len(ozet)})"
    assert ozet[0]["rows"] == 1 and ozet[0]["tickers"] == 1 and ozet[0]["dates"] == seans, ozet[0]
    assert f"EA@{seans}={EA_HAM_HACIM!r}" in ozet[0]["ornekler"], ozet[0]["ornekler"]
    assert _data._HACIM_TUR_DERINLIK == 0, "kapsam kapanmadı — derinlik sızdı"


def test_K14b_COK_SEMBOLLU_sip_turu_TEK_OLAY_basar(sandbox_state, uyarilar, monkeypatch):
    """TOPLU GİRİŞ KAPSAMI: `sip_correct_provisional` sembol döngüsü taşır. İçerideki her
    `_overwrite_bar` kendi kapsamını açar; dış kapsam olmasaydı N sembol N olay basardı (tur 2'nin
    kapattığı gürültü seli). İkisi birlikte: tek başına yol da duyurur, toplu tur TEK olay basar."""
    gunler = _seanslar("2024-01", 3)
    seans, kapanis = gunler[1], 209.2
    semboller = ["EA", "MSFT", "NVDA"]
    for t in semboller:
        _sip_defterine_yaz(t, gunler, seans, kapanis)

    ic_olaylar: list[int] = []

    def _sip_bars(syms, session, timeout=30.0):
        # HER SEMBOL İÇİN AYNI SEANS: kesirli hacim üç defterin üçüne de girer. OHLC tutarlı
        # (high ≥ close ≥ low) — bozuk bir bar `sanitize_bars` karantinasına düşer ve yazım
        # REDDEDİLİRDİ; o zaman çivi kapsamı değil karantinayı ölçerdi.
        return {t: {"open": kapanis, "high": kapanis + 0.2, "low": kapanis - 0.2,
                    "close": kapanis + 0.05, "volume": EA_HAM_HACIM} for t in syms}

    def _overwrite_izle(ticker, bar, _asil=_data._overwrite_bar):
        # DÖNGÜ ORTASINDA OLAY SAYIMI: iç kapsam duyursaydı bu liste 0'da kalmazdı.
        ic_olaylar.append(len(_ozetler(uyarilar)))
        return _asil(ticker, bar)

    monkeypatch.setattr(_alpaca, "data_available", lambda: True)
    monkeypatch.setattr(_alpaca, "sip_allowed", lambda d: True)
    monkeypatch.setattr(_alpaca, "sip_session_bars", _sip_bars)
    monkeypatch.setattr(_data, "_overwrite_bar", _overwrite_izle)

    rapor = _data.sip_correct_provisional()

    assert rapor["targets"] == 3 and rapor["corrected"] == 3, f"sip yolu ölçülemedi: {rapor}"
    assert ic_olaylar == [0, 0, 0], f"iç kapsam tur ortasında duyurdu: {ic_olaylar}"
    ozet = _ozetler(uyarilar)
    assert len(ozet) == 1, f"3 sembollük sip turu {len(ozet)} olay üretti — gürültü tavanı yok"
    assert ozet[0]["rows"] == 3 and ozet[0]["tickers"] == 3 and ozet[0]["dates"] == seans, ozet[0]
    for t in semboller:
        assert list(pd.read_csv(_data._cache_path(t))["volume"])[1] == 3569440.0, \
            f"{t}: sip düzeltmesi diske ondalık yazdı"
    assert _data._HACIM_TUR_DERINLIK == 0, "kapsam kapanmadı — derinlik sızdı"
