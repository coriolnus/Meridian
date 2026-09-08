"""EDG-2026-067 ARAMA CLI'I — sqlite-vec taban indeksinde soru sorar (TSK-167 dilim-1).

NE OLDUĞU. `taban_indeks.py` bir ÖLÇÜM kolu olarak doğdu: kart
`research/cards/EDG-2026-067-hindsight-faz1-bgem3-recall.yaml` Hindsight recall'unu minimal bir
taban çizgiye karşı koydu ve hüküm (2026-09-07, operatör kararı K1 / TSK-060 MELEZ) Hindsight'ı
ARAMA katmanı olmaktan çıkardı. Geriye kalan taban indeksi artık bir ölçüm artefaktı DEĞİL, günlük
kullanılan bir araçtır — bu betik onun komut satırıdır.

ÖLÇÜLEN TABAN (EDG-067 hükmü, bu betiğin ne VAAT ETTİĞİNİN sınırı):
bölüm-isabet@3 %27,8 · dosya-isabet@3 %55,6 · p50 0,62 s. Yani ilk üç sonuçtan birinin DOĞRU
DOSYA olma oranı kabaca yarıdır. Bu bir zayıflık değil bir OKUMA TALİMATIdır: çıktı bir cevap
değil bir ADAY LİSTESİdir; hüküm dosyayı açan insanındır.

YASA 6 — OKUYUCU KİM. (a) Rol-1 triyajı: karar/kart/kök-neden öncesi "bu daha önce yaşandı mı"
sorusu (kalıcı direktif 2026-09-06, `hafiza_sor.sh` recall'ünün tamamlayıcısı — grep'in değil).
(b) Pano `/api/arama` yüzeyi, TSK-167 dilim-2. Okuyucusu olmayan bir çıktı üretilmez.

`meridian` PAKETİ İTHAL EDİLMEZ — taban_indeks'in kuralı burada da geçerlidir ve burada DAHA
bağlayıcıdır: bu betik pytest DIŞINDA, elle, sık koşar. Motor paketine dokunsaydı her arama
`meridian.obs` üzerinden canlı yerel deftere yazardı (3 vaka, 2026-08-30). Çivi: v438.

SIR YOK. Ne anahtar dosyası okur ne de bir HTTP yetkilendirme başlığı kurar — `kiyas_kos.py`nin
Hindsight kolu bir HTTP istemcisidir ve o kol buraya HİÇ girmez; yalnız taban (yerel sqlite) kolu
ithal edilir. Çivi v438 kaynağı bu sınıfın belirteçlerine karşı tarar.

KOŞUM YERİ A1. Yerel macOS Python'ında `sqlite3` uzantı yükleyemez ve onnxruntime/tokenizers/
sqlite_vec kurulu değildir — `taban_hazirla` o iki arızayı AYRI AYRI adlandırıp düşer, bu betik
mesajı AYNEN basıp 1 döner. A1 sarmalayıcısı: `deploy/hindsight/hafiza_ara.sh`.

ÇIKIŞ KODU SÖZLEŞMESİ
    0 — koşum tamamlandı (sonuç BOŞ olabilir: "sonuç yok" bir BULGUdur, arıza değil)
    1 — girdi/uzantı arızası; `taban_hazirla`nın mesajı stderr'e AYNEN basılır
    2 — kullanım hatası (argparse)
    3 — ÖLÇÜLEMEDİ: model/şema ayrışması (gömme boyutu beklenenden farklı, `boyut_dogrula`nın
        `ValueError`ı). stderr'e `ölçülemedi: <neden>` öneğiyle basılır.
        NEDEN 3, NEDEN 2 DEĞİL (bulgu K4, 2026-09-08): brief bu sınıf için 2 demişti, ama 2 bu
        modülde ZATEN argparse kullanım hatasına ayrılmış (v438 `test_gercek_surecte_soru_
        eksikse_rc2`) — aynı sayıyı iki farklı reçeteye vermek, sarmalayıcının "komutu yanlış
        yazdım" ile "indeks modelle ayrışmış" arasında ayrım yapmasını imkânsız kılardı.
        NEDEN 1 DEĞİL: 1 GİRDİ arızasıdır (dosya yok, uzantı yüklenemedi) ve reçetesi "yolu
        düzelt / uzantıyı kur"dur; 3'ün reçetesi "indeksi modelle YENİDEN kur"dur.

KULLANIM
    hafiza_ara.py --db /opt/hindsight/edg067/taban.sqlite --model-dir <bge-m3 onnx> \
                  [-k 5] [--dosya docs/] [--json] "<soru>"
"""
import argparse
import importlib.util
import json
import pathlib
import sqlite3
import sys

_BURASI = pathlib.Path(__file__).resolve().parent

#: Tablo görünümünde metin kesitinin tavanı (karakter). Terminal satırı bir chunk'ın tamamını
#: (pencere 1500 karakter) taşıyamaz; `--json` ham metni KESMEDEN verir, yani bedel ödenmez.
KESIT_TAVANI = 240

#: KIRPMA İŞARETİ — kaç KARAKTERİN düştüğünü söyler ve TAVANIN İÇİNDE durur (bulgu K8,
#: 2026-09-08). Eskiden kesme SESSİZDİ: okuyucu (operatör ve `meridian/sohbet.py::
#: _arac_hafiza_ara` üzerinden model) 241 karakterlik bir chunk ile 20.000 karakterlik bir
#: chunk'ı AYIRT EDEMİYORDU — Yasa 4'ün sessiz-yutma sınıfı ve bedel yasasının "ne kaybettiğini
#: de ölç" hükmü. BİRİM KARAKTER, satır DEĞİL: `kesit` metni tek satıra KATLAR, orada "satır"
#: diye bir şey kalmaz. İşaret tavanın İÇİNDE uygulanır, yani v438'in `len(kesit) <=
#: KESIT_TAVANI` değişmezi KIRILMAZ (ölçüldü: o değişmez `<=`dır, `==` değil).
KESIT_ISARETI = "…(+%d kr)"

#: `--dosya` süzgeci ISTEMCI TARAFINDADIR: vec0 KNN sorgusu `dosya_yolu`na göre daraltılamaz
#: (`en_yakin`in SQL'i tek MATCH + k alır). O yüzden k×4 aday çekilip süzülür. Kat SEÇİLDİ,
#: ÖLÇÜLMEDİ: dört kat, %55,6 dosya-isabetinde bir önekin ilk üçe girme şansını makul kılacak
#: kadar geniş; daha büyük bir kat p50 0,62 s'lik gecikmeyi süzgeç olmayan koşumlara da yaymadan
#: büyütürdü. Süzgeçten kaç adayın düştüğü HER koşumda raporlanır — kat yetersizse operatör onu
#: sayıdan görür, tahminden değil.
ADAY_KATI = 4

#: Tablo alan ayıracı. `--json` makine yüzeyidir; bu görünüm İNSAN içindir.
AYIRAC = " · "


def _kaynaktan_yukle(yol, ad):
    """Kardeş betiği KAYNAKTAN derleyip yükler — `kiyas_kos.py`nin aynı yardımcısıyla AYNI
    gerekçe: `loader.exec_module` derlemeden önce `__pycache__`e bakar ve boyut-koruyan bir
    düzenleme bayat bytecode'u "geçerli" saydırır (ölçülmüş vaka, 2026-08-30).
    `dont_inherit=True` zorunludur: yoksa yüklenen betik BU dosyanın `__future__` ifadelerini
    miras alır.

    KOPYA MI? Evet, üç dosyada üçüncü kez yazılan bir gövde bu — ve tek-kaynak yasasının doğru
    okuması ithal etmemek yönünde DEĞİL: `ops/sasi_yukleyici.py`yi ithal etmek `ops/` paketini,
    dolayısıyla depo kökünü `sys.path`e sokmak demek olurdu ve o yol `meridian`ı bu betiğin
    erişimine AÇAR. Yükleyicinin kendisi ithal edilemeyeceği için gövde tekrarlanır; ayrışma
    riski v438'in `test_kiyas_kostan_ithal_eder_kopyalamaz` çivisiyle DEĞİL, gövdenin
    davranışsal olarak sınanmasıyla taşınır (aynı üç satır, aynı üç gerekçe).
    """
    yol = pathlib.Path(yol)
    spec = importlib.util.spec_from_file_location(ad, yol)
    modul = importlib.util.module_from_spec(spec)
    kod = compile(yol.read_text(encoding="utf-8"), str(yol), "exec", dont_inherit=True)
    exec(kod, modul.__dict__)
    return modul


KIYAS = _kaynaktan_yukle(_BURASI / "kiyas_kos.py", "edg067_kiyas_kos_arama")

#: İTHAL, KOPYA DEĞİL. İki gövde olsaydı gömme sözleşmesi (cls havuzlama, 1024, prefix yok) bir
#: gün ölçüm kolunda değişir, arama kolunda kalırdı — ve arama sessizce başka bir vektör uzayında
#: koşardı. Tek-kaynak yasası tam olarak bunu yasaklıyor.
taban_hazirla = KIYAS.taban_hazirla
taban_sorgu = KIYAS.taban_sorgu

#: Künyeden basılan alanlar ve SIRA. Alan yoksa `None` basılır — sıfır ya da boş dizge ile
#: "künyede yok" aynı şey değildir (uydurma yasağı).
KUNYE_ALANLARI = ("uretim_ts", "head_commit", "chunk_sayisi", "dosya_sayisi")


def kesit(metin, tavan=KESIT_TAVANI):
    """Tek satıra katlanmış, tavanla sınırlı metin. Katlama ŞART: chunk'lar markdown gövdesidir
    ve ham hâlleri satır sonu taşır — tablonun bir satırı sessizce üçe bölünürdü.

    KIRPMA GÖRÜNÜRDÜR (gerekçe `KESIT_ISARETI`nde): tavana sığan metin OLDUĞU GİBİ döner (sığan
    her kesite sonek koymak tabloyu gürültüyle doldurur ve sinyali anlamsızlaştırırdı); kırpılan
    metin `…(+N kr)` ile biter ve TOPLAM uzunluk tavanı AŞMAZ.

    KESİM NOKTASI SABİT NOKTA İLE BULUNUR: işaretin uzunluğu düşen karakter SAYISINA, sayı ise
    kesim noktasına bağlıdır (öz-göndergeli). Birkaç yineleme rakam basamağı değişse bile
    oturur; oturmazsa son `[:tavan]` tavanı KOŞULSUZ garanti eder."""
    duz = " ".join(str(metin).split())
    if len(duz) <= tavan:
        return duz
    kesim = tavan
    for _ in range(4):
        aday = tavan - len(KESIT_ISARETI % (len(duz) - kesim))
        if aday == kesim:
            break
        kesim = aday
    if kesim < 1:
        return duz[:tavan]
    return (duz[:kesim] + KESIT_ISARETI % (len(duz) - kesim))[:tavan]


def mesafe_yaz(deger):
    """Üç ondalık. Ölçülemeyen mesafe `None` basılır, 0.000 DEĞİL — sıfır mesafe "birebir aynı"
    demektir ve bir eksik değeri öyle göstermek okuyucuyu yanıltırdı."""
    if deger is None:
        return "None"
    return "%.3f" % float(deger)


def kunye_satiri(kunye):
    kunye = kunye or {}
    return "# indeks: " + AYIRAC.join(
        "%s=%s" % (alan, kunye.get(alan)) for alan in KUNYE_ALANLARI)


#: GÖRÜNÜR KAÇIŞ karakteri — `AYIRAC` (" · ") bir SÜTUN İÇİNDE geçerse `_alanlar`-tarzı
#: `split(AYIRAC, 4)` ayrıştırıcısı sütunu YANLIŞ yerden keser (bulgu C5a, 2026-09-08).
#: `bolum` alanı `taban_indeks.py::bolumlere_ayir`'ın ürettiği ham markdown başlığıdır ve depo
#: kendi başlıklarında (ör. "### C.1 · Limit tavanını...") AYNI diziyi taşıyabilir. Sıradan bir
#: boşlukla değiştirmek de kaymayı önlerdi ama iki farklı ayıracı görsel olarak AYIRT EDİLEMEZ
#: kılardı; '‧' (U+2027, FIGURE SPACE değil FIGÜR NOKTASI) okuyucuya "burada bir kaçış var"
#: sinyalini taşır.
KACIS_NOKTASI = "‧"


def _kacir(deger) -> str:
    """Bir alan İÇİNDEKİ `AYIRAC` dizisini görünür biçimde kaçırır. YALNIZ SON OLMAYAN
    sütunlara uygulanır (`kesit` zaten son sütundur ve `split(AYIRAC, 4)`in maxsplit sözleşmesi
    son parçayı bölmeden bırakır — kaçış orada gereksizdir)."""
    return str(deger).replace(AYIRAC, f" {KACIS_NOKTASI} ")


def tablo_satiri(sira, sonuc):
    return AYIRAC.join((
        str(sira),
        mesafe_yaz(sonuc.get("mesafe")),
        _kacir(sonuc.get("dosya")),
        _kacir(sonuc.get("bolum")),
        kesit(sonuc.get("metin", "")),
    ))


def suz(ham, onek, k):
    """(sonuçlar, süzülen sayısı). Önek YOKSA süzme de yoktur ve `None` döner — 0 ile "süzgeç
    çalışmadı" aynı görünmesin diye (aynı ayrım, aynı yasa)."""
    if not onek:
        return list(ham)[:k], None
    esles = [s for s in ham if str(s.get("dosya", "")).startswith(onek)]
    return esles[:k], len(ham) - len(esles)


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="hafiza_ara.py",
        description="EDG-067 taban indeksinde anlamsal arama (sqlite-vec + bge-m3 ONNX)")
    ap.add_argument("--db", required=True, help="taban.sqlite yolu")
    ap.add_argument("--model-dir", required=True, help="bge-m3 ONNX dizini (A1 canlı kurulum)")
    ap.add_argument("-k", type=int, default=5, help="kaç sonuç (varsayılan 5)")
    ap.add_argument("--dosya", default=None,
                    help="sonuçları bu dosya-yolu ÖNEKİYLE süz (ör. docs/)")
    ap.add_argument("--json", action="store_true", dest="json_cikti",
                    help="ham sonuç listesini JSON olarak stdout'a bas (künye stderr'e gider)")
    ap.add_argument("soru")
    a = ap.parse_args(argv)
    if a.k < 1:
        ap.error("-k EN AZ 1 olmalı (verilen: %d)" % a.k)

    # Künye ve şerhler `--json` modunda stderr'e gider: stdout O ZAMAN saf JSON'dur ve `jq`
    # boru hattı kırılmaz. Tablo modunda ikisi de stdout'tadır, `#` önekiyle ayırt edilir.
    serh_akisi = sys.stderr if a.json_cikti else sys.stdout

    try:
        kunye, ortam, kapat = taban_hazirla(a.db, a.model_dir)
    except ValueError as e:
        # ÖLÇÜLEMEZLİK, GİRDİ ARIZASI DEĞİL (bulgu K4, 2026-09-08): `taban_indeks.py::
        # boyut_dogrula` model/şema ayrışmasını (gömme boyutu beklenenden farklı) BU sınıfla
        # fırlatır. Reçetesi "indeksi modelle yeniden kur"dur ve rc 1'in ("yolu düzelt")
        # reçetesinden AYRIDIR — sarmalayıcı ikisini ancak farklı kodlarla ayırabilir.
        print("ölçülemedi: %s" % e, file=sys.stderr)
        return 3
    except (RuntimeError, FileNotFoundError, sqlite3.Error) as e:
        # SESSİZ DEĞİL: mesaj AYNEN stderr'e gider ve çıkış kodu 1 olur. Sarmalanmaz, çünkü
        # `vec_baglan` iki arızayı (uzantı desteği yok / sqlite_vec kurulu değil) BİLEREK ayrı
        # adlandırıyor ve iki arızanın REÇETESİ farklı — araya konan her önek o ayrımı bulandırır.
        print(str(e), file=sys.stderr)
        return 1

    try:
        istenen = a.k * ADAY_KATI if a.dosya else a.k
        ham = taban_sorgu(ortam, a.soru, istenen)
    except ValueError as e:
        # Aynı ayrım sorgu katmanında da geçerli (K4): `boyut_dogrula` burada da düşebilir ve
        # ÖLÇÜLEMEZLİK sınıfıdır — önekli, rc 3.
        print("ölçülemedi: %s" % e, file=sys.stderr)
        return 3
    except (RuntimeError, sqlite3.Error) as e:
        # Girdi arızası (indeks şeması bozuk, vec0 tablosu yok): yutulmaz — metin AYNEN basılır,
        # 1 dönülür.
        print(str(e), file=sys.stderr)
        return 1
    finally:
        kapat()

    sonuclar, suzulen = suz(ham, a.dosya, a.k)

    print(kunye_satiri(kunye), file=serh_akisi)
    if suzulen is not None:
        print("# --dosya %r: %d aday çekildi, %d süzüldü, %d kaldı"
              % (a.dosya, len(ham), suzulen, len(sonuclar)), file=serh_akisi)

    if a.json_cikti:
        # HAM liste: `en_yakin`in döndürdüğü satırlar OLDUĞU GİBİ. Kesit/sıra eklemek burada
        # bir KAYIP olurdu — dilim-2'nin pano yüzeyi tam metni isteyecek.
        print(json.dumps(sonuclar, ensure_ascii=False))
        return 0

    if not sonuclar:
        print("# eşik yok, sıralama saf mesafedir: boş liste 'indekste hiç chunk yok' ya da "
              "'--dosya öneki hiçbir adayı bırakmadı' demektir", file=serh_akisi)
        print("sonuç yok")
        return 0

    for sira, sonuc in enumerate(sonuclar, 1):
        print(tablo_satiri(sira, sonuc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
