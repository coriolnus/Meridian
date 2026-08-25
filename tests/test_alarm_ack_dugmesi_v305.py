"""ALARM ONAY DÜĞMESİ — UCUN OKUYUCUSU PANODA VAR · v305

VAKA (2026-08-25, operatör): "arayüzde alarmları okundu olarak işaretleyebileceğim bir onay
butonu yok." Ölçüldü ve haklı: `POST /api/alerts/ack` BAŞINDAN BERİ vardı ama panoda hiçbir
yerden çağrılmıyordu — yani gelen kutusunu kapatmanın tek yolu curl'dü. Sonuç: canlıda 23
alarm birikmişti (9'u 2026-08-09'dan `NAKED_POSITION`).

BU BİR YASA 6 VAKASIDIR, TERSİNDEN: yazılan bir artefaktın okuyucusu olmalı derken, ÇAĞRILAN
bir ucun da çağıranı olmalı. Çağıransız uç, olmayan uçla aynı işi görür — ve kalıcı kırmızı
bir rozet, hiç kırmızı olmamakla aynı bilgiyi taşır (kimse bakmaz). VLO dersi: "alarm öttü,
kimse dinlemedi".

BU ÇİVİNİN KORUDUĞU ÜÇ ŞEY:
  (1) Düğme VAR ve ucu ÇAĞIRIYOR — bir daha sessizce kaybolmasın.
  (2) Metin NE YAPTIĞINI söylüyor: ACK SİLMEZ, SUSTURUR (`notify.py` yasası) ve okunma sınırı
      "şimdi"ye değil GÖSTERİLEN en yeni olaya ilerler (api.py `_seen_max`). Bunu söylemeyen
      bir düğme operatöre "hepsini kapattım" dedirtir.
  (3) Güncelleme İYİMSER DEĞİL: uç cevabına değil YENİDEN OKUMAYA güveniliyor (kriz kolları
      emsali) — "gönderdim ama gerçekten oldu mu" sorusu ekranda cevaplanır.
"""
from __future__ import annotations

import pathlib
import re

KOK = pathlib.Path(__file__).resolve().parents[1]
KAYNAK = KOK / "ui/src/pano/yuzeyler/sistem/Operasyon.tsx"


def _src() -> str:
    return KAYNAK.read_text(encoding="utf-8")


def test_ack_ucu_panodan_CAGRILIYOR():
    """ASIL ÇİVİ: uç çağıransız kalmasın."""
    s = _src()
    # ALT-DİZE TUZAĞI (mutasyonla yakalandı): düz `"/api/alerts/ack" in s` YETMEZ — o dize
    # yukarıdaki yorum bloğunda da geçiyor, ve `"krizPost" in s` import satırıyla tatmin
    # oluyordu. Çağrının KENDİ BİÇİMİ çivilenir.
    assert re.search(r'krizPost\(\s*"/api/alerts/ack"', s), (
        "alarm yüzeyi `POST /api/alerts/ack` ucunu ÇAĞIRMIYOR (dize bir yorumda geçiyor "
        "olabilir) — uç çağıransız, operatörün gelen kutusunu kapatmasının pano yolu YOK")
    assert "await krizPost" in s, "POST beklenmiyor — sonuç okunmadan başarı varsayılır"


def test_dugme_ACK_ANLAMINI_yaziyor():
    """ACK'in ne YAPMADIĞI, ne yaptığı kadar önemli: silmiyor, ve yalnız gösterileni kapatıyor."""
    s = _src()
    assert "SİLMEZ" in s and "SUSTURUR" in s, (
        "düğme ACK'in silmediğini söylemiyor — operatör alarmların kaybolduğunu sanabilir")
    assert "GÖSTERİ" in s, (
        "okunma sınırının GÖSTERİLEN en yeni olaya ilerlediği yazılmıyor — ekranda görünmeyen "
        "alarm kapanmaz ve operatör 'hepsini kapattım' sanır")


def test_hata_SESSIZ_yutulmuyor():
    """`ok:false` bu ailede 200 İÇİNDE gelebilir; başarısız ACK sessizce başarı gibi görünmemeli."""
    s = _src()
    assert re.search(r"if\s*\(!s\.ok\)", s), "ACK cevabının başarısı hiç sınanmıyor"
    assert "toast.error" in s, "başarısız ACK operatöre BİLDİRİLMİYOR"
    assert "OLDUĞU GİBİ" in s or "gitmedi" in s, (
        "hata mesajı gelen kutusunun DEĞİŞMEDİĞİNİ söylemiyor")


def test_guncelleme_IYIMSER_degil():
    """Kriz kolları emsali: uç cevabına değil yeniden okumaya güvenilir."""
    s = _src()
    # ALT-DİZE TUZAĞI (mutasyonla yakalandı): `onBitti` props TİPİNDE de geçiyor, `tazele`
    # ise çağrı yerinde — ikisinin varlığı çağrının YAPILDIĞINI kanıtlamaz.
    assert re.search(r"^\s*onBitti\(\);", s, re.M), (
        "ACK sonrası `onBitti()` ÇAĞRILMIYOR (yorum satırına alınmış olabilir) — ekran "
        "iyimser bir yalan gösterebilir")
    assert re.search(r"onBitti=\{\s*durum\.tazele\s*\}", s), (
        "yeniden okuma kancası yüzeyin `tazele`sine BAĞLI DEĞİL — çağrı bir yere gitmiyor")


def test_olculemeyen_sayida_dugme_TEKLIF_EDILMEZ():
    """UYDURMA YASAĞI komşusu: kaç alarmı kapattığını bilmeden 'gördüm' demek, görmeden
    imzalamaktır. `pending` ölçülemediyse düğme HİÇ çizilmez."""
    s = _src()
    assert re.search(r"bekleyen\s*===\s*undefined", s), (
        "`pending` ölçülemediğinde düğme yine de çiziliyor — kaç alarmın kapandığı bilinmeden "
        "ACK verilir")


def test_bos_kutuda_dugme_YERINE_durum_var():
    """Sıfır bekleyende tıklanacak bir şey olmamalı ama yüzey SESSİZ de kalmamalı."""
    s = _src()
    assert "gelen kutusu temiz" in s, (
        "gelen kutusu boşken yüzey hiçbir şey söylemiyor — 'düğme yok' ile 'kutu temiz' "
        "operatör için AYNI görünür")
