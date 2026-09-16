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
GERÇEK DEFTERE DOKUNULMAZ: her çivi `sandbox_state` altında koşar; canlı `state/bars/` açılmaz.
"""

from __future__ import annotations

import duckdb
import pandas as pd
import pytest

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
    """Süreç-içi sayaç ve tarih-duyuru defteri testler arasında SIZMAZ: biri dolu kalsaydı bir
    sonraki çivi kendi ölçtüğü turu değil, öncekinin kalıntısını okurdu."""
    _data._HACIM_ONDALIK.clear()
    _data._HACIM_ONDALIK_DUYURULDU.clear()
    yield
    _data._HACIM_ONDALIK.clear()
    _data._HACIM_ONDALIK_DUYURULDU.clear()


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
