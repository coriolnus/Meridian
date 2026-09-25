"""deploy/hindsight/hafiza_okuma_kaydi.py — Hindsight okuma kaydı (EDG-2026-103 ADIM-0 (b), TSK-222).

NEDEN VAR. EDG-2026-103 "zihin modeli sayfaları neden karara girmiyor" sorusunu dört kola ayırır;
K1 (okunuyor mu) ve K2 (okunan sayfa kararla konuca örtüşüyor mu) bir OKUMA OLAYI kaynağı ister.
Hindsight API'sinin mental-models uçları erişim/görüntülenme alanı TUTMUYOR (kart ADIM-0 (c),
2026-09-25 A1'de ölçüldü: alanlar bank_id·content·created_at·id·is_stale·last_memory_seen_at·
last_refreshed_at·max_tokens·name·reflect_response·source_query·tags·trigger). O yüzden okuma
kaydı YENİ bir yazım yoludur ve iki okuyucu betik (`sayfa_oku.sh`, `hafiza_sor.sh`) onu BU
modülle yazar — iki betikte iki yazar kopyası olsaydı alan kümeleri sessizce ayrışırdı
(tek-kaynak yasası).

OKUYUCU (Yasa 6): EDG-2026-103 ölçümü — K1 kadansı ve K2 konu eşleşmesi bu dosyadan sayılır
(`research/olcumler/edg103_okuma_ilgi_atif/`, kart `olcum_plani`). Başka okuyucusu yoktur.

BİR SATIR = BİR ÇAĞRI. Her satır aynı ALANLAR kümesini taşır; uygulanmayan alan `null`dır
(sıfır DEĞİL — uydurma yasağı: "bilmiyorum" ile "0" aynı şey değildir).
  v         şema sürümü (1)
  ts        kaydın yazıldığı an, UTC ISO (okuma BİTİŞİ; başlangıç = ts − sure_s)
  betik     sayfa_oku | hafiza_sor
  kip       liste | sayfa | recall
  kimlik    sayfa: sunucunun döndürdüğü sayfa id'si · recall ve BULUNAMADI: "sha256:<hex>"
  ad        sayfa adı (sunucudan — kullanıcı girdisi DEĞİL)
  tazeleme  sayfanın last_refreshed_at'i (K2'nin anlık görüntü eşleşmesi için)
  bank/butce recall argümanları
  http      son HTTP durum kodu; bağlantı kurulamadıysa null
  bayt/sha256 GÖVDE ölçüsü — liste/recall: ham HTTP gövdesi; sayfa: sayfanın `content` alanı
            (okurun gördüğü metin; ham gövde her tazelemede meta alanlarla değişir)
  durum     gercek | yer_tutucu | bos | bulunamadi | hata
  sonuc_n   liste: sayfa sayısı · recall: sonuç sayısı
  sure_s    betiğin python kısmının başından kayda kadar geçen süre
  hata      yalnız istisna SINIFININ adı (mesaj yazılmaz)
  etiket    HAFIZA_OKUMA_ETIKET (PK/test-ateşleme ayrımı; kart kill-list: "sentetik PK gerçek
            sayıma karışmaz, ayrı işaretlenir") — yalnız `[a-z0-9][a-z0-9_-]{0,31}` yazılır,
            başka her değer `gecersiz` olur

SORU METNİ YAZILMAZ — KARAR (TSK-222). Recall sorusu serbest metindir ve bu betik A1'de `~/bin`den
koşar, `meridian` içe aktaramaz (sır süzgeci `notify.scrub` erişilemez; kopyalamak ikinci bir
süzgeç doğururdu). Kartın kill-list'i sırrı SIFIR toleransla kapatır. Kartın dört kolu soru metnine
ihtiyaç DUYMAZ: K2 okunan SAYFANIN içeriğini kararla eşler, K4 kararın KENDİ atfını okur — kararın
konusu karar metninde (git/ROADMAP/günlük/kart) zaten yazılıdır. Soru yerine sha256'sı yazılır:
aynı soruyu gruplamaya ve kararda alıntılanan soruyu (birebir) kayıtla eşlemeye yeter. Aynı gerekçe
BULUNAMADI sayfa argümanına uygulanır; sunucunun döndürdüğü sayfa adı ise beyaz listedir (var olan
bir sayfanın adı) ve açık yazılır.

ANAHTAR VE URL ASLA YAZILMAZ: bu modül ikisini de görmez — çağıran yalnız yukarıdaki alanları geçer.

YER TUTUCU (kart kill-list, EDG-083 vakası): yeni açılan sayfanın içeriği tazeleme bitene dek
"Generating content..." yer tutucusudur; 2026-09-06'da bir betik bunu "içerik var" sanıp sayfaları
hazır saydı. Kural (o vakanın düzeltmesiyle aynı): içerik boş → `bos`; içerik yer tutucu metni YA DA
`last_refreshed_at` boş → `yer_tutucu`; yalnız ikisi de geçerse `gercek`. API alanı ileride kalkarsa
her okuma `yer_tutucu` görünür — sessiz sahte-geçiş değil, kartın PK'sında görünen bir kırmızı.

YAZIM ASLA OKUMAYI DÜŞÜRMEZ. Kayıt dizini yoksa ya da yazılamazsa uyarı stderr'e basılır ve çağıran
normal çıktısını verir (Yasa 4: sessiz yutma yok; ama okuma işlevi kayda BAĞLI değil). Dizin bu
modülce YARATILMAZ — kurulum Rol-1'in (A1'de `install -d`), betik kendi kendini kurmaz.

Bu dosya `meridian`ı içe aktarmaz, yalnız stdlib kullanır (A1 sistem python3'ü ile koşar).
"""
import datetime
import hashlib
import json
import os
import re
import sys

SEMA = 1
VARSAYILAN_YOL = "/opt/veri/olcum/edg103/okuma.jsonl"
ORTAM_YOL = "HAFIZA_OKUMA_KAYDI"
ORTAM_ETIKET = "HAFIZA_OKUMA_ETIKET"
ALANLAR = ("v", "ts", "betik", "kip", "kimlik", "ad", "tazeleme", "bank", "butce", "http",
           "bayt", "sha256", "durum", "sonuc_n", "sure_s", "hata", "etiket")

_YER_TUTUCU = re.compile(r"generating content\s*(\.{3}|…)?", re.IGNORECASE)
_ETIKET = re.compile(r"[a-z0-9][a-z0-9_-]{0,31}")


def _uyar(mesaj):
    print(f"UYARI: {mesaj}", file=sys.stderr)


def kimlik_ozeti(metin):
    """Serbest metin kimliğin yazılabilir hâli: `sha256:<hex>` (UTF-8)."""
    return "sha256:" + hashlib.sha256(metin.encode("utf-8")).hexdigest()


def sayfa_durumu(icerik, tazeleme):
    """Sayfa içeriğinin sınıfı: `bos` · `yer_tutucu` · `gercek` (kural modül başlığında)."""
    govde = (icerik or "").strip()
    if not govde:
        return "bos"
    if _YER_TUTUCU.fullmatch(govde) or not tazeleme:
        return "yer_tutucu"
    return "gercek"


def _etiket(ortam):
    ham = ortam.get(ORTAM_ETIKET)
    if ham is None or ham == "":
        return None
    if _ETIKET.fullmatch(ham):
        return ham
    _uyar(f"{ORTAM_ETIKET} biçimsiz — kayda 'gecersiz' yazıldı (izinli: küçük harf, rakam, _ -)")
    return "gecersiz"


def satir_kur(*, betik, kip, sure_s, kimlik=None, kimlik_metni=None, ad=None, tazeleme=None,
              bank=None, butce=None, http=None, govde=None, icerik=None, sonuc_n=None,
              durum=None, hata=None, ortam=None, simdi=None):
    """Tek kayıt satırı (sözlük). `kimlik_metni` verilirse kimlik onun ÖZETİDİR, metnin kendisi
    satıra girmez. `icerik` verilirse gövde odur ve durum sayfa kuralıyla sınıflanır."""
    ortam = os.environ if ortam is None else ortam
    simdi = simdi or datetime.datetime.now(datetime.timezone.utc)
    if kimlik_metni is not None:
        kimlik = kimlik_ozeti(kimlik_metni)
    if icerik is not None:
        govde = icerik.encode("utf-8")
        if durum is None:
            durum = sayfa_durumu(icerik, tazeleme)
    if durum is None:
        durum = "gercek" if sonuc_n else "bos"
    satir = {
        "v": SEMA,
        "ts": simdi.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "betik": betik, "kip": kip, "kimlik": kimlik, "ad": ad, "tazeleme": tazeleme,
        "bank": bank, "butce": butce, "http": http,
        "bayt": len(govde) if govde is not None else None,
        "sha256": hashlib.sha256(govde).hexdigest() if govde is not None else None,
        "durum": durum, "sonuc_n": sonuc_n,
        "sure_s": round(float(sure_s), 3),
        "hata": hata, "etiket": _etiket(ortam),
    }
    return satir


def yaz(**alan):
    """Satırı kurar ve kayıt dosyasına EKLER. Asla istisna fırlatmaz: yazılamazsa stderr'e
    uyarır ve False döner — okuma işlevi kayda bağlı değildir. Dönüş: yazıldı mı."""
    yol = os.environ.get(ORTAM_YOL) or VARSAYILAN_YOL
    try:
        metin = json.dumps(satir_kur(**alan), ensure_ascii=False, sort_keys=True) + "\n"
        with open(yol, "a", encoding="utf-8") as f:
            f.write(metin)
        return True
    except OSError as e:  # sessiz-yutma değil: uyarı stderr'e basılır, okuma çıktısı etkilenmez
        _uyar(f"okuma kaydı yazılamadı ({yol}): {e.strerror or type(e).__name__}")
        return False
    except Exception as e:  # sessiz-yutma değil: beklenmeyen kusur okumayı düşürmesin, ADIYLA söylensin
        _uyar(f"okuma kaydı kurulamadı ({type(e).__name__}) — bu okuma KAYDEDİLMEDİ")
        return False
