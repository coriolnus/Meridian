"""İşlem satırı PARAYI göstermeli, yalnız R'yi değil (operatör şikâyeti 2026-08-21).

BİLDİRİM: *"canlıda hangi işlemin ne kadar para kazandırdığını veya kaybettirdiğini net
göremiyorum."*

ÖLÇÜLDÜ: `tradeRows` altı sütun basıyor — tarih · sembol · çıkış nedeni · **R** · rejim ·
ayna sapması. `pnl_dollars` YALNIZ çekmecede (`pdRow("Net K/Z", …)`), yani operatör her işlemin
parasını görmek için satırı TEK TEK açmak zorunda. Liste seviyesinde para YOK.

NEDEN BU BİR KUSUR, BİR TERCİH DEĞİL — deponun kendi kuzey yıldızı:
*"R-birimi geniş stopa YAPISAL ÖNYARGILIDIR (boyut R-nötr küçülür, kazanan R'leri daralır);
dolar merceği olmadan sermaye kararı verilemez."* Yani R tek başına gösterildiğinde operatör
bilerek yanlı bir mercekten bakıyor ve doğrusunu görmek için 15 kez tıklaması gerekiyor.

Bu çivi R'yi KALDIRMAZ — ikisi YAN YANA durmalı. R karşılaştırılabilirlik, dolar gerçeklik verir.
"""
import pathlib
import re

APP = pathlib.Path(__file__).resolve().parents[1] / "meridian" / "web" / "app.js"


def _traderows() -> str:
    s = APP.read_text(encoding="utf-8")
    i = s.index("function tradeRows(")
    # PENCERE FONKSİYONUN SONUNA KADAR, SABİT KARAKTER SAYISI DEĞİL (2026-08-21): ilk hâl
    #  idi ve fonksiyona yorum eklenince pencere satırı DIŞARIDA bıraktı — çivi
    # kodu değil KENDİ penceresini ölçüyordu. Sonraki  tanımına kadar oku.
    j = s.find("\nfunction ", i + 10)
    return s[i:j if j > 0 else i + 6000]


def test_islem_satiri_DOLAR_tasir():
    src = _traderows()
    assert "pnl_dollars" in src, (
        "işlem satırı `pnl_dollars` göstermiyor — operatör parayı görmek için her satırı TEK TEK "
        "açmak zorunda; kuzey yıldızı 'dolar merceği olmadan sermaye kararı verilemez' diyor")


def test_R_de_KALIR_ikisi_yan_yana():
    """Dolar eklemek R'yi kaldırmak DEĞİLDİR: R karşılaştırılabilirlik, dolar gerçeklik verir."""
    src = _traderows()
    assert "r_multiple" in src, "R sütunu kaldırılmış — ikisi YAN YANA durmalı"


def test_sutun_sayisi_ile_grid_UYUMLU():
    """Sütun eklenip `grid-template-columns` güncellenmezse satır KAYAR — sessiz bir görsel kusur.

    Bu çivi ikisini birbirine bağlar: `<span>` sayısı ile grid sütun sayısı EŞİT olmalı."""
    src = _traderows()
    m = re.search(r"grid-template-columns:([^\"']+)", src)
    assert m, "grid-template-columns bulunamadı"
    sutun = len(m.group(1).split())
    # satır gövdesindeki üst düzey <span> sayısı
    govde = src[src.index("class=\"trow rowbtn\""):]
    govde = govde[:govde.index("</button>")]
    span = len(re.findall(r"<span(?![^>]*class=\"(?:tag|mono-num)\"[^>]*>\s*<)", govde))
    # iç içe span'lar sayılmasın diye yalnız satır başındaki hizayı sayıyoruz
    ust = len(re.findall(r"\n      <span", govde))
    assert ust == sutun, (
        f"grid {sutun} sütun tanımlıyor ama satır {ust} hücre basıyor — satır KAYAR")
