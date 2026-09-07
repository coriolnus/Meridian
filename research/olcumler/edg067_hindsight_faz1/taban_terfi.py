"""EDG-2026-067 TABAN TERFİSİ — haftalık tazelemenin SON adımı: yeni indeksi kabul et ya da
gerekçesiyle bırak (TSK-167 dilim-1).

NEDEN AYRI BİR BETİK. Haftalık tazeleme birimi üç adımdır (korpus paketi → indeks kurulumu →
terfi) ve ilk ikisi ZATEN mevcut betiklerdir (`manifest_uret.py`, `taban_indeks.py` — ikisi de
kart artefaktıdır, DEĞİŞTİRİLMEZ). Üçüncü adım koşullu bir karardır ve gidebileceği üç yer vardı:

  · `ExecStart=/bin/sh -c '...'` — systemd `$` ile başlayan her belirteci KENDİSİ genişletir
    (bilinmeyen değişken BOŞ dizgeye iner), yani kabuk değişkeni kullanan her satır sessizce
    bozulur. Terfi kararı iki satır sayısını karşılaştırmak zorunda, yani değişkensiz yazılamaz.
  · Python `-c` tek satırı — sözdizimi birim dosyasında yaşar ve HİÇBİR çivi onu koşturamaz.
  · AYRI BİR BETİK — sözleşmesi komut satırıdır, çivileri gerçek dosyalar üzerinde gerçek karar
    verdirir. Seçilen bu.

VE BU KOL YEREL OLARAK TAM ÖLÇÜLEBİLİR, arama kolundan farklı olarak: satır sayımı `chunk`
tablosundan gelir ve `chunk` NORMAL bir tablodur — vec0 sanal tablosuna, dolayısıyla sqlite-vec
uzantısına HİÇ dokunulmaz. Yani v438 çivileri burada sahte değil, gerçek sqlite dosyalarıyla
koşar.

KAPI. Yeni indeksin satır sayısı eskinin en az `--esik-oran` katıysa terfi eder. Kapının yönü
tek taraflıdır ve bilinçlidir: korpus BÜYÜR (günlük, kartlar, docs her hafta uzar), yani düşen
bir satır sayısı bir arıza işaretidir — yarım paket, kesilmiş bir ONNX koşumu, dolan disk.
BÜYÜMEYE tavan KONMADI: "bu hafta %40 büyüdü" bir arıza değil bir olaydır ve tavan koymak
tazelemeyi normal büyümenin kendisine karşı kırılgan yapardı.

BIRAKMA SESSİZ DEĞİLDİR (Yasa 6): gerekçe stdout'a — yani journal'a — basılır ve çıkış kodu 1
olur. `1`in OKUYUCUSU VAR: birim `failed` olur, `meridian/api.py`nin `/api/infra` yüzeyi
`ActiveState=failed`i "arizali" diye sınıflar ve panoda görünür. Sessizce 0 dönseydi taban
aylarca bayat kalabilir ve hiçbir şey bozuk görünmezdi.

`meridian` PAKETİ İTHAL EDİLMEZ — kardeş betiklerle aynı gerekçe (pytest dışı koşum
`meridian.obs` üzerinden canlı yerel deftere yazardı; 3 vaka, 2026-08-30). Çivi: v438.

ÇIKIŞ KODU SÖZLEŞMESİ
    0 — terfi edildi (hedef artık yeni indeks; eski sürüm `.onceki` ekiyle BİR sürüm saklandı)
    1 — terfi EDİLMEDİ ya da ölçüm yapılamadı; gerekçe stdout'ta, hedef DOKUNULMAMIŞ
    2 — kullanım hatası (argparse)

KULLANIM
    taban_terfi.py --yeni /opt/hindsight/edg067/taban.sqlite.yeni \
                   --hedef /opt/hindsight/edg067/taban.sqlite [--esik-oran 0.9]
"""
import argparse
import json
import os
import pathlib
import sqlite3

#: Kabul eşiği: yeni satır sayısı eskinin bu KATINDAN küçükse terfi YOK. Değer brief'ten gelir
#: (TSK-167 dilim-1); ÖLÇÜLMEDİ, SEÇİLDİ — ve seçim tek taraflı kapının gerekçesiyle birlikte
#: okunur (yukarıda). Karşılaştırma `>=`dır: tam eşikte kabul, çünkü eşiğin KENDİSİ sınırdır,
#: ihlal değil.
ESIK_ORAN = 0.9

#: Eski sürümün saklandığı ek. TEK sürüm saklanır — ikinci terfi üçüncü bir kopya bırakmaz;
#: yoksa /opt/hindsight/edg067 haftada bir indeks büyüklüğünde şişerdi (disk, A1'de 2021
#: ortasında dolan bir kaynak).
ONCEKI_EK = ".onceki"

#: Sayımın okunduğu tablo. `chunk_vec` (vec0) BİLEREK kullanılmaz: onu okumak sqlite-vec
#: uzantısını gerektirir ve terfi kararı uzantının varlığına bağlı OLMAMALIDIR — indeks kurulumu
#: zaten uzantıyla koştu, terfi yalnız sonucu sayar.
SAYIM_TABLOSU = "chunk"


def satir_say(yol):
    """`chunk` satır sayısı. Ölçülemezse (dosya bozuk, tablo yok) `ValueError` — SIFIR DÖNMEZ.
    Sıfır "indekste hiç chunk yok" demektir ve bozuk bir dosyayı öyle saymak, kapıyı tam da
    korumaya çalıştığı arızada AÇARDI (eski 100, "yeni 0" → oran 0 → bırak; ama tablo hiç
    okunamadıysa hüküm "bırak" değil "ölçemedim"dir)."""
    yol = pathlib.Path(yol)
    try:
        db = sqlite3.connect("file:%s?mode=ro" % yol, uri=True)
    except sqlite3.Error as e:
        raise ValueError("SATIR SAYIMI ÖLÇÜLEMEDİ: %s açılamadı (%s: %s)"
                         % (yol, type(e).__name__, e)) from e
    try:
        return int(db.execute("SELECT count(*) FROM %s" % SAYIM_TABLOSU).fetchone()[0])
    except sqlite3.Error as e:
        raise ValueError("SATIR SAYIMI ÖLÇÜLEMEDİ: %s içinde `%s` tablosu okunamadı (%s: %s)"
                         % (yol, SAYIM_TABLOSU, type(e).__name__, e)) from e
    finally:
        db.close()


def terfi_et(yeni, hedef, onceki_ek=ONCEKI_EK):
    """Eski sürümü sert-bağla, yeniyi ATOMİK olarak hedefin üstüne koy.

    SIRA ÖNEMLİ. Önce `os.link` (sert bağ), sonra `os.replace`: bu sırada hedef ADI hiçbir an
    KAYBOLMAZ — eşzamanlı bir arama koşumu ya eski ya yeni indeksi görür, "dosya yok"u değil.
    Ters sırada (`mv hedef onceki` + `mv yeni hedef`) araya düşen her okuyucu FileNotFound alırdı
    ve o pencere haftada bir, gecenin 03:30'unda, kimsenin bakmadığı anda açılırdı."""
    yeni, hedef = pathlib.Path(yeni), pathlib.Path(hedef)
    onceki = hedef.with_name(hedef.name + onceki_ek)
    if hedef.exists():
        if onceki.exists():
            onceki.unlink()
        os.link(hedef, onceki)
    os.replace(yeni, hedef)
    return onceki if hedef.exists() and onceki.exists() else None


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="taban_terfi.py",
        description="EDG-067 taban indeksi terfisi: satır-sayısı kapısı + atomik yerine koyma")
    ap.add_argument("--yeni", required=True, help="yeni kurulmuş indeks (taban.sqlite.yeni)")
    ap.add_argument("--hedef", required=True, help="canlı indeks yolu (taban.sqlite)")
    ap.add_argument("--esik-oran", type=float, default=ESIK_ORAN,
                    help="yeni/eski satır oranı alt sınırı (varsayılan %.2f)" % ESIK_ORAN)
    ap.add_argument("--onceki-ek", default=ONCEKI_EK,
                    help="eski sürümün saklandığı ek (varsayılan %s)" % ONCEKI_EK)
    a = ap.parse_args(argv)

    yeni, hedef = pathlib.Path(a.yeni), pathlib.Path(a.hedef)

    def bildir(karar, **alanlar):
        print(json.dumps({"karar": karar, "yeni": str(yeni), "hedef": str(hedef), **alanlar},
                         ensure_ascii=False))

    if not yeni.exists():
        bildir("BIRAKILDI", neden="yeni indeks YOK — indeks kurulumu adımı hiç çıktı üretmemiş")
        return 1

    try:
        yeni_satir = satir_say(yeni)
        # Hedef yoksa oran hesaplanamaz. `None` DÖNER, 0 değil: ilk kurulumda "eski sıfır satır"
        # demek, kapıyı sonsuza kadar açık bir kıyasa dayandırmak olurdu.
        eski_satir = satir_say(hedef) if hedef.exists() else None
    except ValueError as e:
        # Sessiz değil: gerekçe journal'a gider, hedefe DOKUNULMAZ, çıkış 1.
        bildir("BIRAKILDI", neden=str(e))
        return 1

    if eski_satir is None:
        onceki = terfi_et(yeni, hedef, a.onceki_ek)
        bildir("TERFI", yeni_satir=yeni_satir, eski_satir=None, esik_oran=a.esik_oran,
               onceki=str(onceki) if onceki else None,
               neden="hedef yoktu — ilk kurulum, kıyaslanacak satır sayısı ÖLÇÜLEMEZ")
        return 0

    esik = a.esik_oran * eski_satir
    if yeni_satir < esik:
        bildir("BIRAKILDI", yeni_satir=yeni_satir, eski_satir=eski_satir,
               esik_oran=a.esik_oran, esik_satir=esik,
               neden="yeni indeks eşiğin ALTINDA — `.yeni` teşhis için YERİNDE bırakıldı, "
                     "hedefe dokunulmadı")
        return 1

    onceki = terfi_et(yeni, hedef, a.onceki_ek)
    bildir("TERFI", yeni_satir=yeni_satir, eski_satir=eski_satir, esik_oran=a.esik_oran,
           esik_satir=esik, onceki=str(onceki) if onceki else None)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
