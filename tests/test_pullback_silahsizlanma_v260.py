"""Pullback silahsızlanması — çiviler (B1 operatör kararı 2026-08-22, kart EDG-2026-039).

KARAR: seçenek A — `ARMED_SETUPS`ten çıkar. Gerekçe kartın hükmü (KANIT ASİMETRİSİ):
zarar üç bağımsız kaynakta tutarlı (replay n=6 kazanma %0 · canlı n=4 −1,00R · cf n=29 −0,885R
[karar günü ölçümü]) · çıkarmanın faydası kanıtsız AMA zararı da yok · silahlı tutmak her seans
ısı/slot/sermaye yiyor, silahsızken kanıt cf'de birikmeye DEVAM ediyor · geri dönüş tek satır.
"""
import pathlib

from meridian import strategy as strat

KOK = pathlib.Path(__file__).resolve().parents[1]


def test_pullback_silahsiz():
    assert "pullback" not in strat.ARMED_SETUPS, \
        "B1 kararı (2026-08-22): pullback silahsızlandı — geri ekleme YALNIZ yeniden-silahlanma kapısından"


def test_kalan_uclu_ve_sira_korundu():
    """Silahsızlanma yalnız pullback'i çıkarır; kalan üçlünün kendisi ve EKLEME SIRASI korunur
    (v92'nin sıra disiplini: sonradan silahlanan, öncekilerin ARKASINA eklenir)."""
    assert strat.ARMED_SETUPS == ("breakout_vcp", "exhaustion_hammer", "momentum_burst"), \
        f"beklenen üçlü korunmadı: {strat.ARMED_SETUPS}"


def test_yeniden_silahlanma_kapisi_YAZILI():
    """Karar 'kalıcı çıkarma' DEĞİL 'eşikli bekleme': cf'de n≥30 VE ort-R CI-alt > 0 olursa
    kart-önce yeniden değerlendirme. Kapı kodda (kararın yaşadığı yerde) yazılı olmalı —
    yoksa altı ay sonra 'neden silahsız?' sorusunun cevabı kaybolur."""
    src = (KOK / "meridian" / "strategy.py").read_text(encoding="utf-8")
    i = src.index("ARMED_SETUPS = (")   # ATAMAYA çapa — ilk metin geçişi docstring'de (ölçüldü, tahmin değil)
    blok = src[max(0, i - 1200):i + 200]
    assert "EDG-2026-039" in blok, "silahsızlanma kararının kart atfı ARMED_SETUPS yanında değil"
    assert "n≥30" in blok or "n>=30" in blok, "yeniden-silahlanma eşiği (n≥30) yazılı değil"
    assert "CI-alt" in blok, "yeniden-silahlanma eşiği (CI-alt>0) yazılı değil"


def test_uyuyan_kanit_kanali_yapisal():
    """Kartın (iii) gerekçesinin ÖN KOŞULU: silahsız kurulum cf'de ölçülmeye DEVAM etmeli.
    Kanal `cf_backfill`ın dormant dalı — `ARMED_SETUPS` DIŞINDA kalan sinyaller `dormant_setup`
    damgasıyla aday olur. Bu dal silinirse yeniden-silahlanma kapısı HİÇ ateşleyemez ve karar
    'eşikli bekleme'den 'sessiz kalıcı çıkarma'ya dönüşür — çivi tam bunu engeller."""
    src = (KOK / "meridian" / "cf_backfill.py").read_text(encoding="utf-8")
    assert "not in strat.ARMED_SETUPS" in src, "dormant dalı kayboldu — silahsız kurulum artık taranmıyor"
    assert "dormant_setup" in src, "dormant damgası kayboldu — silahsız aday ayırt edilemez"
