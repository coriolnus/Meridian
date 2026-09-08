"""test_edg086_sayim_v450.py — TSK-012 dalga-B / B3 Task 2: EDG-2026-086 SAYACININ çivisi.

NE ÇİVİLENİR (plan `docs/superpowers/plans/2026-09-08-pano-sohbet-b3.md` Task 2):
`research/olcumler/edg086_pano_sohbet/sayim.py` — kartın beş ölçüsünü `state/sohbet.jsonl`
şemasından sayar. YOL-TUTARLI POZİTİF KONTROL kartın `pozitif_kontrol` maddesinin (1) SENTETİK
ayağıdır: 20 satırlık sahte defterde BİLİNEN 3 uydurma · 2 metin-araç · 1 kota vardır ve sayaç
TAM OLARAK onları bulmalıdır (4. bir uydurma eklenince 4 bulmalıdır — çivinin kendi mutasyonu).

PK KAPSAMI TUR-2'DE GENİŞLETİLDİ (çekişmeli inceleme, 2026-09-08). Tur-1'in sentetik defteri üç
arıza sınıfına KÖRDÜ ve kill-list "pozitif kontrol tutmazsa hiçbir sayı yayılmaz" der:
  * üç uydurmanın hiçbiri SEMBOL sınıfından değildi (sembolün uydurma kolu hiç koşmuyordu),
  * `sema_disi` her turda 0, `llm_dustu` her satırda False'tu — K2 birincil ölçüsünün sayacını
    silen bir mutasyon hiçbir çiviyi kırmıyordu,
  * tek "araç çıktısız" satır SİSTEM ŞABLONUydu (kota); kartın kanonik arıza vakası olan
    "model konuştu ama hiç veri okumadı" satırı defterde YOKTU.
Üçü de bu dosyada artık ADIYLA vardır ve satır sayısı 20'de, sayım 3/2/1'de KALIR.

TEK ÇIKARICI (tek-kaynak yasası): sayaç cevabı `meridian.sohbet.cikti_atiflari` ile çıkarır —
defteri yazan tarafla AYNI fonksiyon. İki taraf ayrı yazılsaydı "uydurma" sayısı çıkarıcı farkını
ölçerdi. Bu dosya o kimliği ADIYLA çiviler.

SAYAÇ HÜKÜM VERMEZ (CLAUDE.md §5): eşikler karttan OKUNUR ve rapora SAYI olarak yazılır; "geçti"/
"kaldı" kelimesi hiçbir çıktıda geçmez. Pencere dolmadan markdown "HÜKÜM YOK" başlığı taşır.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import subprocess
import sys

import pytest
import yaml

from meridian import sohbet
from tests.conftest import betikten_modul_yukle

KOK = pathlib.Path(__file__).resolve().parents[1]
BETIK_YOLU = KOK / "research" / "olcumler" / "edg086_pano_sohbet" / "sayim.py"
KART_YOLU = KOK / "research" / "cards" / "EDG-2026-086-pano-sohbet-kalite.yaml"

#: PK defterinin zaman tabanı. Damgalar ARİTMETİKLE üretilir, elle yazılmaz: sayaç `--baslangic`
#: karşılaştırmasını artık AYRIŞTIRILMIŞ damga üzerinden yapar ve elle yazılan "10:99:00" gibi bir
#: dizge ayrıştırılamayan satır olurdu (tur-1'de öyle satırlar vardı ve kimse görmüyordu).
BAS = dt.datetime(2026, 9, 10, 10, 0, tzinfo=dt.timezone.utc)


def _sayim():
    return betikten_modul_yukle(BETIK_YOLU, "edg086_sayim")


def _ts(i: int) -> str:
    return (BAS + dt.timedelta(minutes=i)).isoformat()


# =================================================================================================
# SAHTE DEFTER KURUCULARI — `meridian.sohbet._kaydet`in yazdığı şekil
# =================================================================================================
def _atif(sayi=(), kimlik=(), yol=(), sembol=()):
    return {"sayi": sorted(sayi), "kimlik": sorted(kimlik),
            "yol": sorted(yol), "sembol": sorted(sembol)}


def _tur(*, atiflar=None, tool_calls=1, sema_disi=0, model="m1", sure_s=0.5, kesilen=None):
    t = {"model": model, "tool_calls": tool_calls, "sema_disi": sema_disi, "sure_s": sure_s}
    if atiflar is not None:
        t["cikti_atiflari"] = atiflar
    if kesilen:
        t["cikti_atif_kesildi"] = list(kesilen)
    return t


def _satir(ts, oturum, cevap, turlar, *, sure_s=2.0, model="m1", kota_bugun=5,
           llm_dustu=False, oneri_id=None, mesaj="soru"):
    return {"ts": ts, "oturum": oturum, "mesaj": mesaj, "cevap": cevap, "turlar": turlar,
            "kaynaklar": [], "model": model, "sure_s": sure_s,
            "jeton_giris": 10, "jeton_cikis": 5, "kota_bugun": kota_bugun,
            "oneri_id": oneri_id,
            "sema_disi_n": sum(int(t.get("sema_disi") or 0) for t in turlar),
            "llm_dustu": llm_dustu}


def _temiz_satir(i, oturum="S1"):
    """Cevabındaki HER atıf araç çıktısında GEÇEN bir satır — uydurma 0."""
    return _satir(_ts(i), oturum,
                  "AAPL için T00001 işlemi 12.5 ile kapandı.",
                  [_tur(atiflar=_atif(sayi=["12.5"], kimlik=["T00001"], sembol=["AAPL"])),
                   _tur(tool_calls=0)], sure_s=float(2 + (i % 5)))


def _pk_defteri() -> list[dict]:
    """20 satır: 3 UYDURMA · 2 METİN-ARAÇ · 1 KOTA (kartın sentetik PK'si).

    Üç uydurma ÜÇ AYRI SINIFTAN gelir (sayı · kimlik · SEMBOL) ve sembol olanı aynı zamanda
    "model konuştu ama hiç veri okumadı" satırıdır — kartın kanonik arıza vakası. Defter ayrıca
    bir ŞEMA-DIŞI tur (2 çağrı) ve bir ZİNCİR-DÜŞMESİ satırı taşır; ikisi de cevabı temiz olduğu
    için 3/2/1 sayımını bozmaz ama K2 sayaçlarının mutasyonunu ısırır."""
    satirlar = [_temiz_satir(i, "S1" if i < 7 else "S2") for i in range(13)]

    # ŞEMA-DIŞI KAPSAMI: ilk satırın araç turunda 3 çağrının 2'si şemaya uymadı; kalan 1 çağrı
    # veri okudu (atıf kümesi yerinde), yani cevabın paydası TAM ve satır hâlâ uydurmasız.
    satirlar[0]["turlar"][0]["tool_calls"] = 3
    satirlar[0]["turlar"][0]["sema_disi"] = 2
    satirlar[0]["sema_disi_n"] = 2

    # ZİNCİR DÜŞTÜ — SİSTEM METNİ: model konuşmadı, cevabı döngü yazdı. Ölçüm DIŞI (cevaptaki
    # hiçbir dizge modelin iddiası değildir).
    satirlar.append(_satir(_ts(13), "S2",
                           "model yok — zincirin hicbir ayagi cevap vermedi. Cevap URETILMEDI.",
                           [_tur(tool_calls=0, model=None)], model=None, llm_dustu=True))
    # (1) UYDURMA — sayı: 99.9 araç çıktısında YOK
    satirlar.append(_satir(_ts(14), "S2", "T00001 sonucu 99.9 oldu.",
                           [_tur(atiflar=_atif(sayi=["12.5"], kimlik=["T00001"])),
                            _tur(tool_calls=0)]))
    # (2) UYDURMA — kimlik: T02222 araç çıktısında YOK
    satirlar.append(_satir(_ts(15), "S2", "T02222 planı 12.5 taşıyor.",
                           [_tur(atiflar=_atif(sayi=["12.5"], kimlik=["T00001"])),
                            _tur(tool_calls=0)]))
    # (3) UYDURMA — SEMBOL, üstelik BOŞ PAYDALI satırdan: model cevap verdi ama hiçbir araç veri
    # okumadı. Kartın hipotez (a) maddesi tam olarak bu satırı "atıflarını araç çıktısından
    # KURMAMIŞ" saymak için yazılmıştı; tur-1 onu SİSTEM şablonlarıyla aynı kovaya atıp ölçüm
    # dışında bırakıyordu (eşiği geçme yönünde yanlılık).
    # `$` ÖNEKİ BİR ÇAPADIR VE ZORUNLUDUR (yeniden inceleme, 2026-09-08): sembol sınıfı artık
    # bağlam çapası ister, çapasız "NVDA tarafinda hareket var" cümlesi `belirsiz`e giderdi ve
    # PK'nin SEMBOL uydurması sessizce 3'ten 2'ye düşerdi.
    satirlar.append(_satir(_ts(16), "S2", "$NVDA tarafinda hareket var.",
                           [_tur(tool_calls=0)]))
    # (4-5) METİN-ARAÇ — cevapta `ad(` biçimi, o turda tool_calls yok (EDG-074 sınıfı)
    for i, oturum in ((17, "S1"), (18, "S2")):
        satirlar.append(_satir(_ts(i), oturum,
                               "once plan_oku(hedef) cagirmam gerekiyor",
                               [_tur(atiflar=_atif(kimlik=["T00001"])), _tur(tool_calls=0)]))
    # (6) KOTA — kapı model çağrılmadan kapandı: tur YOK, atıf YOK, cevapta kota sayıları var
    satirlar.append(_satir(_ts(19), "S2",
                           "kota dolu (120/120) — sohbet bugun model cagirmiyor.",
                           [], model=None, kota_bugun=120))
    return satirlar


def _defter_yaz(yol: pathlib.Path, satirlar: list[dict]) -> pathlib.Path:
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in satirlar),
                   encoding="utf-8")
    return yol


# =================================================================================================
# 0) TEK ÇIKARICI + KART KAYNAKLI EŞİKLER
# =================================================================================================
def test_sayac_cevabi_defteri_yazan_cikaricinin_KENDISIYLE_okur():
    s = _sayim()
    assert s.cikti_atiflari is sohbet.cikti_atiflari, "ikinci bir çıkarıcı doğdu (tek-kaynak)"
    assert s.belirsiz_semboller is sohbet.belirsiz_semboller, "kısa sembol kovası kopyalandı"
    assert s.BEYAZ_LISTE is sohbet.BEYAZ_LISTE, "araç adı listesi kopyalandı"


def test_esikler_KARTTAN_okunur_kopyalanmaz(tmp_path):
    s = _sayim()
    kart = yaml.safe_load(KART_YOLU.read_text(encoding="utf-8"))
    defter = _defter_yaz(tmp_path / "sohbet.jsonl", _pk_defteri())
    sonuc = s.calistir(defter=defter, kart=KART_YOLU)
    assert sonuc["esikler"]["uydurma_orani_ust"] == kart["esikler"]["uydurma_orani_ust"]
    assert sonuc["esikler"]["n_alt_mesaj"] == kart["esikler"]["n_alt_mesaj"]
    assert sonuc["esikler"]["kota_gunluk_tavan"] == kart["esikler"]["kota_gunluk_tavan"]


def test_seans_alt_siniri_kartin_pencere_metnine_baglidir():
    """Kartta seans eşiğinin MAKİNE OKUNUR alanı YOK (ölçüldü: `esikler` yalnız `n_alt_mesaj`
    taşıyor); sayı `veri_penceresi` DÜZ METNİNDE yaşıyor. Sessiz kopya yerine BAĞLI kopya:
    kart metni değişirse bu çivi öter ve sabit elle güncellenir."""
    s = _sayim()
    kart = yaml.safe_load(KART_YOLU.read_text(encoding="utf-8"))
    assert f"{s.SEANS_ALT} seans" in kart["veri_penceresi"], kart["veri_penceresi"]


# =================================================================================================
# 1) POZİTİF KONTROL — SENTETİK 20 satır: 3 / 2 / 1 (plan Task 2 / Çivi 1)
# =================================================================================================
def test_PK_sentetik_20_satirda_3_uydurma_2_metin_arac_1_kota(tmp_path):
    s = _sayim()
    defter = _defter_yaz(tmp_path / "sohbet.jsonl", _pk_defteri())
    sonuc = s.calistir(defter=defter, kart=KART_YOLU)

    assert sonuc["n_mesaj"] == 20, sonuc["n_mesaj"]
    assert sonuc["n_seans"] == 2, sonuc["n_seans"]
    assert sonuc["uydurma"]["uydurma"] == 3, sonuc["uydurma"]
    assert sonuc["arac"]["metin_arac_n"] == 2, sonuc["arac"]
    assert sonuc["kota"]["dolu_pencere_n"] == 1, sonuc["kota"]
    # SINIF KIRILIMI: üç uydurma ÜÇ AYRI sınıftan (tek sınıfa katlanmadılar) ve biri SEMBOL —
    # tur-1'de sembolün uydurma kolu hiçbir çivide koşmuyordu.
    kirilim = sonuc["uydurma"]["sinif_kirilimi"]
    assert kirilim["sayi"]["uydurma"] == 1 and kirilim["kimlik"]["uydurma"] == 1, kirilim
    assert kirilim["sembol"]["uydurma"] == 1 and kirilim["yol"]["uydurma"] == 0, kirilim
    assert {x["sinif"] for x in sonuc["uydurma"]["ornekler"]} == {"sayi", "kimlik", "sembol"}


def test_PK_semadisi_ve_zincir_dusmesi_sayaclari_DOLU(tmp_path):
    """K2'nin BİRİNCİL ölçüsü şema-dışı orandır; tur-1'de sentetik kapsamı SIFIRDI (her tur
    `sema_disi=0`, her satır `llm_dustu=False`) ve sayacı silen mutasyon hiçbir çiviyi kırmıyordu.
    Kota tarafında da `gun_basi_max`/`dolu_pencere_pay` için tek assert yoktu."""
    s = _sayim()
    defter = _defter_yaz(tmp_path / "sohbet.jsonl", _pk_defteri())
    sonuc = s.calistir(defter=defter, kart=KART_YOLU)

    assert sonuc["arac"]["sema_disi_n"] == 2, sonuc["arac"]
    assert sonuc["arac"]["toplam_tool_calls"] == 19, sonuc["arac"]
    assert sonuc["arac"]["tur_n"] == 36, sonuc["arac"]
    assert sonuc["kota"]["llm_dustu_n"] == 1, sonuc["kota"]
    assert sonuc["kota"]["gun_basi_max"] == 120, sonuc["kota"]
    assert sonuc["kota"]["gun_n"] == 1, sonuc["kota"]
    assert sonuc["kota"]["gun_basi_ort"] == pytest.approx(120.0), sonuc["kota"]
    assert sonuc["kota"]["dolu_pencere_pay"] == pytest.approx(1 / 20), sonuc["kota"]


def test_PK_MUTASYON_dorduncu_uydurma_eklenince_4_bulunur(tmp_path):
    """Çivinin kendi mutasyonu: sayaç sabit bir sayı döndürmüyor, GERÇEKTEN sayıyor. Dördüncü
    uydurma YOL sınıfındandır — dört sınıfın dördü de bu dosyada uydurma kolundan geçer."""
    s = _sayim()
    satirlar = _pk_defteri()
    satirlar.append(_satir(_ts(20), "S2", "Kural meridian/uydurma.py dosyasinda yazili.",
                           [_tur(atiflar=_atif(yol=["ops/olay_sorgu.py"])),
                            _tur(tool_calls=0)]))
    defter = _defter_yaz(tmp_path / "sohbet.jsonl", satirlar)
    sonuc = s.calistir(defter=defter, kart=KART_YOLU)
    assert sonuc["uydurma"]["uydurma"] == 4, sonuc["uydurma"]
    assert sonuc["uydurma"]["sinif_kirilimi"]["yol"]["uydurma"] == 1, sonuc["uydurma"]


def test_arac_adini_ANMAK_metin_arac_degildir(tmp_path):
    """AYRAÇ AYIRT EDİCİDİR: "plan_oku aracını kullandım" bir ARAÇ ÇAĞRISI DEĞİL, bir cümledir.
    Ayraç şartı düşerse cevabında araç adını anan her satır EDG-2026-074 sınıfına yazılırdı ve
    şema-dışı oranı hak etmediği bir sayıya şişerdi."""
    s = _sayim()
    satirlar = _pk_defteri()
    satirlar.append(_satir(_ts(25), "S2",
                           "plan_oku aracini kullandim ve sonucu okudum",
                           [_tur(atiflar=_atif(kimlik=["T00001"])), _tur(tool_calls=0)]))
    defter = _defter_yaz(tmp_path / "sohbet.jsonl", satirlar)
    sonuc = s.calistir(defter=defter, kart=KART_YOLU)
    assert sonuc["arac"]["metin_arac_n"] == 2, sonuc["arac"]


def test_yapisal_cagri_yapan_turda_metin_arac_sayilmaz(tmp_path):
    """Tur tavanı dolduğunda cevabı SİSTEM yazar ve son turda YAPISAL çağrı vardır. O turda model
    araç çağrısını metin olarak üretmiş değildir — sayılırsa arıza yanlış sınıfa yazılırdı."""
    s = _sayim()
    satirlar = _pk_defteri()
    satirlar.append(_satir(_ts(26), "S2",
                           "tur tavani doldu — plan_oku(hedef) denenmisti",
                           [_tur(atiflar=_atif(kimlik=["T00001"]), tool_calls=1)]))
    defter = _defter_yaz(tmp_path / "sohbet.jsonl", satirlar)
    sonuc = s.calistir(defter=defter, kart=KART_YOLU)
    assert sonuc["arac"]["metin_arac_n"] == 2, sonuc["arac"]


# =================================================================================================
# 2) PAYDA KOVALARI — SİSTEM metni ölçüm dışı, MODEL cevabı BOŞ PAYDAYLA ölçülür
# =================================================================================================
def test_sistem_metni_satirlari_olcum_DISI_ve_ADIYLA_gorunur(tmp_path):
    """Kota şablonunun "120/120"si ve zincir-düşmesi metni MODELİN İDDİASI DEĞİLDİR: o cümleleri
    döngü yazdı. Kill-list "cevabı tek başına okuyan sayım geçersiz" der — sayaç bu satırları
    ölçmez ve ölçmediğini ADIYLA raporlar (uydurma yasağı: sıfır ≠ bilmiyorum)."""
    s = _sayim()
    defter = _defter_yaz(tmp_path / "sohbet.jsonl", _pk_defteri())
    sonuc = s.calistir(defter=defter, kart=KART_YOLU)
    assert sonuc["uydurma"]["sistem_metni_n"] == 2, sonuc["uydurma"]
    assert sonuc["uydurma"]["n_satir"] == 18, sonuc["uydurma"]
    assert any("sistem_metni" in x for x in sonuc["olculemeyen"]), sonuc["olculemeyen"]


def test_model_konustu_arac_okumadi_satiri_BOS_PAYDAYLA_OLCULUR(tmp_path):
    """KARTIN KANONİK ARIZA VAKASI. Model hiçbir aracı çağırmadan "NVDA tarafında hareket var"
    diyorsa cevaptaki her atıf DAYANAKSIZDIR. Tur-1 bu satırı SİSTEM şablonlarıyla aynı kovaya
    atıp ölçüm dışında bırakıyordu — en saf uydurma sınıfı ölçümün tamamen dışında kalıyor ve
    donuk 0,05 eşiği hak etmeden geçiyordu (EXE-2026-006 sınıfı yanlılık)."""
    s = _sayim()
    defter = _defter_yaz(tmp_path / "sohbet.jsonl", _pk_defteri())
    sonuc = s.calistir(defter=defter, kart=KART_YOLU)
    assert sonuc["uydurma"]["bos_payda_n"] == 1, sonuc["uydurma"]
    # ESKİ DIŞLAMA MUTASYONU: bu satır ölçüm dışına atılırsa PK sayısı 3'ten 2'ye DÜŞER.
    assert sonuc["uydurma"]["uydurma"] == 3, sonuc["uydurma"]
    assert sonuc["uydurma"]["sinif_kirilimi"]["sembol"]["uydurma"] == 1, sonuc["uydurma"]


def test_tur_tavani_sablonu_SISTEM_metnidir(tmp_path):
    """Tur tavanında cevabı döngü yazar ve SON TUR yapısal çağrı taşır — yapısal imza budur."""
    s = _sayim()
    satirlar = [_temiz_satir(i, f"S{i % 10}") for i in range(5)]
    satirlar.append(_satir(_ts(30), "S9",
                           "tur tavani (6) doldu — arac dongusu durduruldu ve cevap URETILMEDI. "
                           "7 kez denendi.",
                           [_tur(atiflar=_atif(kimlik=["T00001"]), tool_calls=2)]))
    defter = _defter_yaz(tmp_path / "sohbet.jsonl", satirlar)
    sonuc = s.calistir(defter=defter, kart=KART_YOLU)
    assert sonuc["uydurma"]["sistem_metni_n"] == 1, sonuc["uydurma"]
    assert sonuc["uydurma"]["uydurma"] == 0, sonuc["uydurma"]


def test_kota_sablonu_ONEKI_meridian_sohbetten_TURER(tmp_path):
    """SİSTEM ŞABLONU TANIMASI KOPYA DEĞİL TÜREVDİR: sayaç öneki `meridian.sohbet`in KENDİ kota
    cümlesinden üretir. Şablon metni değişirse bu çivi öter — sessizce ayrışan bir kopya, dolu
    kota satırlarını "model uydurdu" saymaya başlardı."""
    s = _sayim()
    gercek = sohbet._kota_cevabi({"bugun": 120, "tavan": 120, "neden": None})
    olculemeyen = sohbet._kota_cevabi({"bugun": None, "tavan": 120, "neden": "halka doldu"})
    satirlar = [_temiz_satir(i, "S1") for i in range(3)]
    satirlar.append(_satir(_ts(31), "S1", gercek, [_tur(tool_calls=0)], kota_bugun=120))
    satirlar.append(_satir(_ts(32), "S1", olculemeyen, [_tur(tool_calls=0)], kota_bugun=None))
    defter = _defter_yaz(tmp_path / "sohbet.jsonl", satirlar)
    sonuc = s.calistir(defter=defter, kart=KART_YOLU)
    assert sonuc["uydurma"]["sistem_metni_n"] == 2, sonuc["uydurma"]
    assert sonuc["uydurma"]["uydurma"] == 0, sonuc["uydurma"]


# =================================================================================================
# 3) MESAJ YANKISI — operatörün kendi yazdığı atıf uydurma DEĞİLDİR
# =================================================================================================
def test_operatorun_MESAJINDAKI_atif_cevapta_tekrarlanirsa_uydurma_degildir(tmp_path):
    """Operatör "T00007 planı ne durumda?" diye sorar, araç "kayıt yok" der, model cevabında
    T00007'yi tekrarlar. Bu değer MODELİN ÜRETTİĞİ bir şey değil, KULLANICININ girdisinin
    yankısıdır; uydurma sayılsaydı oran hak etmeden YÜKSELİR ve donuk 0,05 eşiği sahte bir hüküm
    üretirdi. Kill-list ihlali yok: payda cevabı TEK BAŞINA okumuyor, araç çıktısı + operatör
    mesajı okunuyor."""
    s = _sayim()
    satirlar = [_temiz_satir(i, "S1") for i in range(3)]
    satirlar.append(_satir(_ts(33), "S1", "T00007 için kayıt yok, ama T00001 planı açık.",
                           [_tur(atiflar=_atif(kimlik=["T00001"])), _tur(tool_calls=0)],
                           mesaj="T00007 planı ne durumda?"))
    defter = _defter_yaz(tmp_path / "sohbet.jsonl", satirlar)
    sonuc = s.calistir(defter=defter, kart=KART_YOLU)

    assert sonuc["uydurma"]["uydurma"] == 0, sonuc["uydurma"]
    assert sonuc["uydurma"]["mesaj_kaynakli"] == 1, sonuc["uydurma"]
    assert sonuc["uydurma"]["mesaj_kaynakli_kirilimi"]["kimlik"] == 1, sonuc["uydurma"]


def test_mesajda_da_arac_ciktisinda_da_olmayan_atif_uydurmadir(tmp_path):
    """Mesaj paydası bir MUAFİYET DEĞİLDİR: operatörün sormadığı bir kimlik hâlâ uydurmadır."""
    s = _sayim()
    satirlar = [_temiz_satir(i, "S1") for i in range(3)]
    satirlar.append(_satir(_ts(34), "S1", "T00007 yok ama T09999 açık.",
                           [_tur(atiflar=_atif(kimlik=["T00001"])), _tur(tool_calls=0)],
                           mesaj="T00007 planı ne durumda?"))
    defter = _defter_yaz(tmp_path / "sohbet.jsonl", satirlar)
    sonuc = s.calistir(defter=defter, kart=KART_YOLU)
    assert sonuc["uydurma"]["uydurma"] == 1, sonuc["uydurma"]
    assert sonuc["uydurma"]["ornekler"][0]["atif"] == "T09999", sonuc["uydurma"]["ornekler"]


# =================================================================================================
# 4) ARAÇ ORANI — payda ÇAĞRIdır (kartın hipotezi), tur paydası TANIdır
# =================================================================================================
def test_arac_orani_CAGRI_paydalidir_ve_tur_paydasi_TANI_olarak_durur(tmp_path):
    """Kart hipotezi (b): "araç ÇAĞRILARININ ≥%90'ı şemaya uyar". Tur-1 paydayı TUR saymıştı ve
    `sohbet_dongusu` cevabı üreten çağrısız turu da listeye eklediği için payda ~2 kat şişiyordu;
    aynı PK defteri 0,10 eşiğinin iki yanına düşüyordu (tur paydası 0,0526 · çağrı paydası
    0,1053). METİN-ARAÇ TURU ÇAĞRI ÜRETMEZ, o yüzden paydaya KENDİSİ eklenir."""
    s = _sayim()
    defter = _defter_yaz(tmp_path / "sohbet.jsonl", _pk_defteri())
    sonuc = s.calistir(defter=defter, kart=KART_YOLU)
    a = sonuc["arac"]
    assert a["oran"] == pytest.approx((2 + 2) / (19 + 2)), a
    assert a["tur_paydali_oran"] == pytest.approx((2 + 2) / 36), a
    assert a["oran"] != pytest.approx(a["tur_paydali_oran"]), a


def test_arac_orani_1i_ASAMAZ(tmp_path):
    """Tur-1'de `sema_disi_n` ÇAĞRI, payda TUR sayıyordu: tek turda 3 şema-dışı çağrı + cevap turu
    → oran 1,5. Bir "oran" 1'i aşıyorsa birim karışmıştır ve kartın 0,10 eşiğinin yanına basılan
    sayı ölçüm değildir."""
    s = _sayim()
    satirlar = [_satir(_ts(i), "S1", "cevap",
                       [_tur(tool_calls=3, sema_disi=3), _tur(tool_calls=0)])
                for i in range(4)]
    defter = _defter_yaz(tmp_path / "sohbet.jsonl", satirlar)
    sonuc = s.calistir(defter=defter, kart=KART_YOLU)
    assert sonuc["arac"]["oran"] == pytest.approx(1.0), sonuc["arac"]
    assert sonuc["arac"]["oran"] <= 1.0, sonuc["arac"]


def test_hic_cagri_yoksa_arac_orani_None_ve_NEDEN(tmp_path):
    s = _sayim()
    satirlar = [_satir(_ts(i), "S1", "duz cevap", [_tur(tool_calls=0)]) for i in range(3)]
    defter = _defter_yaz(tmp_path / "sohbet.jsonl", satirlar)
    sonuc = s.calistir(defter=defter, kart=KART_YOLU)
    assert sonuc["arac"]["oran"] is None and sonuc["arac"]["oran_neden"], sonuc["arac"]


# =================================================================================================
# 5) ATIF KESME — SINIF BAŞINA; satırın tamamı elenmez
# =================================================================================================
def test_kesilen_SINIF_dislanir_satirin_tamami_DISLANMAZ(tmp_path):
    """`cikti_atif_kesildi` bir SINIF LİSTESİdir. Tur-1'de tek bayraktı ve satırın tamamını ölçüm
    dışına atıyordu; en çok sayı taşıyan (yani uydurma riski en yüksek) veri cevapları seçilerek
    eleniyor ve oran hak etmeden düşüyordu."""
    s = _sayim()
    satirlar = _pk_defteri()
    satirlar.append(_satir(_ts(21), "S2", "deger 77.7 ve T03333 kaydi.",
                           [_tur(atiflar=_atif(sayi=["12.5"], kimlik=["T00001"]),
                                 kesilen=["sayi"]),
                            _tur(tool_calls=0)]))
    defter = _defter_yaz(tmp_path / "sohbet.jsonl", satirlar)
    sonuc = s.calistir(defter=defter, kart=KART_YOLU)
    # `sayi` sınıfı EKSİK PAYDALIDIR → 77.7 uydurma SAYILMAZ; `kimlik` paydası TAM → T03333 sayılır.
    assert sonuc["uydurma"]["uydurma"] == 4, sonuc["uydurma"]
    assert sonuc["uydurma"]["sinif_kirilimi"]["kimlik"]["uydurma"] == 2, sonuc["uydurma"]
    assert sonuc["uydurma"]["atif_kesilen_sinif"] == {"sayi": 1}, sonuc["uydurma"]
    assert sonuc["uydurma"]["n_satir"] == 19, sonuc["uydurma"]
    assert any("atif_kesildi" in x for x in sonuc["olculemeyen"]), sonuc["olculemeyen"]


def test_eski_tekil_bayrak_TUM_siniflari_keser(tmp_path):
    """Geriye dönük dürüstlük: eski biçimdeki `cikti_atif_kesildi: true` satırlar (varsa) dört
    sınıfın DÖRDÜNÜ de eksik payda sayar — sessizce "payda tam" varsaymak sahte uydurma üretirdi."""
    s = _sayim()
    satirlar = [_temiz_satir(i, "S1") for i in range(3)]
    tur = _tur(atiflar=_atif(sayi=["12.5"]))
    tur["cikti_atif_kesildi"] = True
    satirlar.append(_satir(_ts(35), "S1", "deger 77.7 ve T03333.", [tur, _tur(tool_calls=0)]))
    defter = _defter_yaz(tmp_path / "sohbet.jsonl", satirlar)
    sonuc = s.calistir(defter=defter, kart=KART_YOLU)
    assert sonuc["uydurma"]["uydurma"] == 0, sonuc["uydurma"]
    assert sonuc["uydurma"]["atif_kesilen_sinif"] == {s_: 1 for s_ in sohbet.ATIF_SINIFLARI}


def test_pencere_OLCULEN_satir_sayisini_da_ister(tmp_path):
    """`pencere_doldu` ÜÇ koşullu bir VE'dir: mesaj eşiği ∧ seans eşiği ∧ GERÇEKTEN ÖLÇÜLEN satır
    eşiği. Tur-1'de kapı `n_mesaj` ile açılıyordu; 100 mesajın 90'ı ölçüm dışıysa "HÜKÜM YOK"
    başlığı düşer ve oran bir avuç satıra dayanırdı."""
    s = _sayim()
    satirlar = [_temiz_satir(i, f"S{i % 10}") for i in range(95)]
    satirlar += [_satir(_ts(200 + i), f"S{i % 10}", "kota dolu (120/120) — sohbet bugun model "
                        "cagirmiyor.", [], model=None, kota_bugun=120) for i in range(5)]
    defter = _defter_yaz(tmp_path / "sohbet.jsonl", satirlar)
    sonuc = s.calistir(defter=defter, kart=KART_YOLU)
    assert (sonuc["n_mesaj"], sonuc["n_seans"]) == (100, 10), sonuc["n_seans"]
    assert sonuc["uydurma"]["n_satir"] == 95, sonuc["uydurma"]
    assert sonuc["pencere_doldu"] is False, sonuc["pencere_doldu"]
    assert "HÜKÜM YOK" in s.markdown_uret(sonuc)


# =================================================================================================
# 6) KART EŞİĞİ EKSİKSE — fail-open YOK (None + neden)
# =================================================================================================
def test_esiksiz_kart_pencereyi_ACMAZ_OLCULEMEDI_der(tmp_path):
    """`or 0` fail-open'dı: `n_alt_mesaj` yoksa `n_mesaj >= 0` her zaman doğru olur ve kapının
    mesaj yarısı SESSİZCE düşerdi; `kota_gunluk_tavan` yoksa her satır "dolu pencere" sayılırdı.
    Uydurma yasağı ölçülemeyen değer için `None` + neden ister, 0 DEĞİL."""
    s = _sayim()
    sahte_kart = tmp_path / "kart.yaml"
    sahte_kart.write_text("card_id: SAHTE\nesikler:\n  uydurma_orani_ust: 0.05\n"
                          "veri_penceresi: '10 seans'\n", encoding="utf-8")
    satirlar = [_temiz_satir(i, f"S{i % 10}") for i in range(120)]
    defter = _defter_yaz(tmp_path / "sohbet.jsonl", satirlar)
    sonuc = s.calistir(defter=defter, kart=sahte_kart)

    assert sonuc["pencere_doldu"] is None, sonuc["pencere_doldu"]
    assert sonuc["pencere_neden"], sonuc
    assert sonuc["kota"]["dolu_pencere_n"] is None, sonuc["kota"]
    assert sonuc["kota"]["dolu_pencere_pay"] is None, sonuc["kota"]
    assert any("n_alt_mesaj" in x for x in sonuc["olculemeyen"]), sonuc["olculemeyen"]
    md = s.markdown_uret(sonuc)
    assert "ÖLÇÜLEMEDİ" in md, md[:600]
    assert "HÜKÜM YOK" in md, md[:600]


# =================================================================================================
# 7) BELİRSİZ — ölçülemeyen biçim uydurma DEĞİLDİR (plan Task 2 / Çivi 2)
# =================================================================================================
def test_yuzde_belirsiz_sayilir_uydurma_sayilmaz(tmp_path):
    s = _sayim()
    satirlar = _pk_defteri()
    satirlar.append(_satir(_ts(22), "S2", "T00001 icin oran %12 ve 1,103.",
                           [_tur(atiflar=_atif(kimlik=["T00001"])), _tur(tool_calls=0)]))
    defter = _defter_yaz(tmp_path / "sohbet.jsonl", satirlar)
    sonuc = s.calistir(defter=defter, kart=KART_YOLU)
    assert sonuc["uydurma"]["uydurma"] == 3, sonuc["uydurma"]
    assert sonuc["uydurma"]["belirsiz"] == 2, sonuc["uydurma"]


def test_binlik_noktali_sayi_ve_yazili_yuzde_BELIRSIZ_sayilir(tmp_path):
    """Tur-1'de "1.000.000" ne `sayi` ne `belirsiz`di — hem paydadan hem "ölçülemeyen" kovasından
    SESSİZCE düşüyordu; "yüzde 12" ise doğrudan uydurma adayı oluyordu. Kart "ölçülemeyen sınıf
    belirsiz ayrı sayılır" der: sessiz düşme uydurma yasağının ihlalidir."""
    s = _sayim()
    satirlar = [_temiz_satir(i, "S1") for i in range(3)]
    satirlar.append(_satir(_ts(36), "S1",
                           "Hacim 1.000.000 lot, ciro 2.500.000 dolar; yüzde 12 arttı, 34 % düştü.",
                           [_tur(atiflar=_atif(kimlik=["T00001"])), _tur(tool_calls=0)]))
    defter = _defter_yaz(tmp_path / "sohbet.jsonl", satirlar)
    sonuc = s.calistir(defter=defter, kart=KART_YOLU)
    assert sonuc["uydurma"]["uydurma"] == 0, sonuc["uydurma"]
    assert sonuc["uydurma"]["belirsiz"] == 4, sonuc["uydurma"]


def test_belirsiz_ve_sayi_KUMELERI_AYRIKTIR():
    """`belirsiz ∩ sayi = ∅` — aynı karakter aralığı iki kovaya birden düşerse ölçü çift sayar.
    Tur-1'de "12 %" HEM sayı HEM belirsizdi."""
    s = _sayim()
    metin = ("oran %12, tutar 1,103 ve 12,5; yüzde 12 arttı, 34 % düştü; Hacim 1.000.000 lot; "
             "YÜZDE 12 ve yüzde  12 ve 12  % ve %  12; 7 adet ve -2.4 getiri, 189.5 seviye")
    sayi_araliklari = [m.span() for m in sohbet.SAYI_RE.finditer(metin)]
    for m in s.BELIRSIZ_RE.finditer(metin):
        a, b = m.span()
        cakisan = [(x, y) for x, y in sayi_araliklari if x < b and a < y]
        assert not cakisan, (m.group(0), cakisan)
    assert sorted(m.group(0) for m in sohbet.SAYI_RE.finditer(metin)) == ["-2.4", "189.5", "7"]


def test_belirsiz_PAYI_raporlanir_ve_sifir_payda_NEDEN_tasir(tmp_path):
    """BEDEL YASASI. Türkçe ondalık virgülü sayı paydasını çökertirse "uydurma oranı 0,0000"
    satırı, sayı sınıfına neredeyse hiç bakılamamış bir ölçümü temsil eder ve 0,05 eşiğinin
    yanında dayanaklı görünür. Körlüğün belirtisi hiçbir şey olmasın diye pay ADIYLA basılır."""
    s = _sayim()
    satirlar = [_satir(_ts(i), "S1", "deger 1,103 ve 2,507 ile T00001.",
                       [_tur(atiflar=_atif(kimlik=["T00001"])), _tur(tool_calls=0)])
                for i in range(4)]
    defter = _defter_yaz(tmp_path / "sohbet.jsonl", satirlar)
    sonuc = s.calistir(defter=defter, kart=KART_YOLU)
    u = sonuc["uydurma"]
    assert u["sinif_kirilimi"]["sayi"]["payda"] == 0, u
    assert u["sinif_kirilimi"]["sayi"]["neden"], u
    assert u["belirsiz"] == 8 and u["payda"] == 4, u
    assert u["belirsiz_pay"] == pytest.approx(8 / 12), u
    assert "ölçülemeyen biçim payı" in s.markdown_uret(sonuc)


def test_kisa_sembol_adayi_uydurma_DEGIL_belirsizdir(tmp_path):
    """Evrende `MU`, `CI`, `T`, `O` gibi tek/iki harfli semboller var ve bunlar Türkçe metnin
    gündelik parçaları ("MU planı", "CI kırmızı"). Sembol sayılsalardı sistematik yanlış-pozitif
    üretirlerdi; sessizce atılsalardı ölçüm kör olurdu — `belirsiz` kovasına giderler."""
    s = _sayim()
    satirlar = [_temiz_satir(i, "S1") for i in range(3)]
    satirlar.append(_satir(_ts(37), "S1", "MU planı ve CI kırmızı; O yüzden bekliyoruz.",
                           [_tur(atiflar=_atif(kimlik=["T00001"])), _tur(tool_calls=0)]))
    defter = _defter_yaz(tmp_path / "sohbet.jsonl", satirlar)
    sonuc = s.calistir(defter=defter, kart=KART_YOLU)
    assert sonuc["uydurma"]["uydurma"] == 0, sonuc["uydurma"]
    assert sonuc["uydurma"]["belirsiz"] == 3, sonuc["uydurma"]


# =================================================================================================
# 8) GECİKME — quantiles; ölçülemeyen satır ayrı (plan Task 2 / Çivi 3)
# =================================================================================================
def test_gecikme_p50_p95_ve_olculemeyen_satir(tmp_path):
    import statistics

    s = _sayim()
    satirlar = _pk_defteri()
    sureler = sorted(float(r["sure_s"]) for r in satirlar if r["sure_s"] is not None)
    satirlar.append(_satir(_ts(23), "S2", "sure yok",
                           [_tur(atiflar=_atif(kimlik=["T00001"])), _tur(tool_calls=0)],
                           sure_s=None))
    defter = _defter_yaz(tmp_path / "sohbet.jsonl", satirlar)
    sonuc = s.calistir(defter=defter, kart=KART_YOLU)

    kesim = statistics.quantiles(sureler, n=100, method="inclusive")
    assert sonuc["gecikme"]["p50_s"] == pytest.approx(kesim[49]), sonuc["gecikme"]
    assert sonuc["gecikme"]["p95_s"] == pytest.approx(kesim[94]), sonuc["gecikme"]
    assert sonuc["gecikme"]["n"] == len(sureler), sonuc["gecikme"]
    assert sonuc["gecikme"]["sure_yok_n"] == 1, sonuc["gecikme"]
    # TUR KIRILIMI TANIDIR: kaç araç turu geçtiyse o kova (kart `olcum_plani` gecikme maddesi)
    assert set(sonuc["gecikme"]["tur_kirilimi"]) >= {"0", "2"}, sonuc["gecikme"]["tur_kirilimi"]


def test_tek_satirlik_defterde_gecikme_None_ve_NEDEN_yazilir(tmp_path):
    """İki noktadan az örneklemde `quantiles` hesaplanamaz — 0.0 yazmak "ölçtük" demek olurdu."""
    s = _sayim()
    defter = _defter_yaz(tmp_path / "sohbet.jsonl", [_temiz_satir(0)])
    sonuc = s.calistir(defter=defter, kart=KART_YOLU)
    assert sonuc["gecikme"]["p50_s"] is None and sonuc["gecikme"]["p95_s"] is None
    assert sonuc["gecikme"]["neden"], sonuc["gecikme"]


# =================================================================================================
# 9) MARKDOWN — pencere dolmadan HÜKÜM YOK, dolunca yalnız SAYI (plan Task 2 / Çivi 4)
# =================================================================================================
def test_pencere_dolmadan_markdown_HUKUM_YOK_basligi_tasir(tmp_path):
    s = _sayim()
    defter = _defter_yaz(tmp_path / "sohbet.jsonl", _pk_defteri())
    sonuc = s.calistir(defter=defter, kart=KART_YOLU)
    assert sonuc["pencere_doldu"] is False, sonuc
    md = s.markdown_uret(sonuc)
    assert "HÜKÜM YOK (betimleyici ara-rapor)" in md, md[:400]


def test_pencere_KOSULU_VE_dir_iki_yarisi_ayri_ayri_kapatir(tmp_path):
    """`pencere_doldu` bir VE'dir: mesaj eşiği ile seans eşiği birbirinin yerine geçmez. İki yarı
    ayrı ayrı sınanmazsa biri sessizce düşer ve pencere hak etmeden dolmuş görünür."""
    s = _sayim()
    # (a) seans YETER, mesaj YETMEZ (10 seans × 5 mesaj = 50 < 100)
    az_mesaj = _defter_yaz(tmp_path / "a" / "sohbet.jsonl",
                           [_temiz_satir(i, f"S{i % 10}") for i in range(50)])
    sonuc_a = s.calistir(defter=az_mesaj, kart=KART_YOLU)
    assert (sonuc_a["n_mesaj"], sonuc_a["n_seans"]) == (50, 10), sonuc_a["n_seans"]
    assert sonuc_a["pencere_doldu"] is False, sonuc_a

    # (b) mesaj YETER, seans YETMEZ (tek oturumda 100 mesaj)
    az_seans = _defter_yaz(tmp_path / "b" / "sohbet.jsonl",
                           [_temiz_satir(i, "TEK") for i in range(100)])
    sonuc_b = s.calistir(defter=az_seans, kart=KART_YOLU)
    assert (sonuc_b["n_mesaj"], sonuc_b["n_seans"]) == (100, 1), sonuc_b["n_seans"]
    assert sonuc_b["pencere_doldu"] is False, sonuc_b


def test_pencere_dolunca_esikler_yalnizca_SAYI_hukum_kelimesi_YOK(tmp_path):
    s = _sayim()
    satirlar = [_temiz_satir(i, f"S{i % 10}") for i in range(100)]
    defter = _defter_yaz(tmp_path / "sohbet.jsonl", satirlar)
    sonuc = s.calistir(defter=defter, kart=KART_YOLU)
    assert sonuc["pencere_doldu"] is True, (sonuc["n_mesaj"], sonuc["n_seans"])

    md = s.markdown_uret(sonuc)
    assert "HÜKÜM YOK" not in md, md[:400]
    for yasak in ("GEÇTİ", "KALDI", "geçti", "kaldı", "başarılı", "başarısız"):
        assert yasak not in md, (yasak, md[:600])
    assert "0.05" in md, "eşik SAYISI raporda yok"
    # EŞİĞİN YANINDAKİ ORAN KARTIN HİPOTEZİYLE AYNI BİRİMDE (çağrı paydalı) OLMALIDIR.
    assert "çağrı paydalı" in md, md[:1500]


# =================================================================================================
# 10) KOMUT SATIRI — ops sözleşmesi (plan Task 2 / Çivi 5)
# =================================================================================================
def test_komut_satiri_operatorun_kosacagi_bicimde_kosar_ve_state_e_YAZMAZ(tmp_path):
    defter = _defter_yaz(tmp_path / "defter" / "sohbet.jsonl", _pk_defteri())
    cikti = tmp_path / "out" / "sonuc.json"
    md = tmp_path / "out" / "sonuc.md"
    onceki = defter.read_bytes()

    ortam = dict(os.environ, MERIDIAN_ROOT=str(tmp_path), PYTHONPATH=str(KOK))
    r = subprocess.run([sys.executable, str(BETIK_YOLU), "--defter", str(defter),
                        "--cikti", str(cikti), "--markdown", str(md),
                        "--kart", str(KART_YOLU)],
                       capture_output=True, text=True, cwd=str(tmp_path), env=ortam)
    assert r.returncode == 0, (r.returncode, r.stdout, r.stderr)
    sonuc = json.loads(cikti.read_text(encoding="utf-8"))
    assert sonuc["uydurma"]["uydurma"] == 3, sonuc["uydurma"]
    assert md.exists() and "HÜKÜM YOK" in md.read_text(encoding="utf-8")
    # SALT-OKUNUR: girdi defteri değişmedi, `state/` doğmadı (sayaç state'e YAZMAZ).
    assert defter.read_bytes() == onceki, "sayaç girdi defterini değiştirdi"
    assert not (tmp_path / "state").exists(), "sayaç state/ altına yazdı"
    assert "uydurma=3" in r.stdout, r.stdout
    # OPERATÖR PENCEREYİ KAYBETTİĞİNİ TERMİNALDE GÖRMELİ (sessiz sıfır rapor sınıfı).
    assert "pencere_disi=" in r.stdout, r.stdout


def test_defter_verilmezse_hata(tmp_path):
    ortam = dict(os.environ, MERIDIAN_ROOT=str(tmp_path), PYTHONPATH=str(KOK))
    r = subprocess.run([sys.executable, str(BETIK_YOLU), "--cikti", str(tmp_path / "o.json")],
                       capture_output=True, text=True, cwd=str(tmp_path), env=ortam)
    assert r.returncode != 0, r.stdout
    assert "--defter" in (r.stderr or ""), r.stderr


def test_olmayan_defter_yolu_hata_verir(tmp_path):
    s = _sayim()
    with pytest.raises(FileNotFoundError):
        s.calistir(defter=tmp_path / "yok.jsonl", kart=KART_YOLU)


# =================================================================================================
# 11) PENCERE BAŞLANGICI — DAMGA AYRIŞTIRILIR, DİZGE KIYASLANMAZ
# =================================================================================================
def test_AYNI_ANI_gosteren_uc_damga_bicimi_AYNI_pencereyi_verir(tmp_path):
    """Defterin `ts`i "+00:00" ofsetli yazılır; planın komut satırı örneği ise "Z" ekli. Düz dizge
    kıyasında `'2026-09-10T10:00:00+00:00' >= '2026-09-10T10:00Z'` YANLIŞTIR (':' 0x3A < 'Z' 0x5A)
    ve `'…T10:00:00Z'` ile de yanlıştır ('+' 0x2B < 'Z') — operatör planın YAZDIĞI komutu koşarsa
    pencerenin İLK ANINDAKİ satırlar sessizce dışarı düşer. Aynı ANI gösteren üç yazım aynı
    pencereyi vermelidir; vermiyorsa ölçülen şey damga biçimidir, veri değil."""
    s = _sayim()
    defter = _defter_yaz(tmp_path / "sohbet.jsonl", _pk_defteri())
    for bicim in ("2026-09-10T10:00Z", "2026-09-10T10:00:00Z", "2026-09-10T10:00:00+00:00"):
        sonuc = s.calistir(defter=defter, kart=KART_YOLU, baslangic=bicim)
        assert sonuc["n_mesaj"] == 20, (bicim, sonuc["n_mesaj"])
        assert sonuc["girdi"]["n_pencere_disi"] == 0, (bicim, sonuc["girdi"])


def test_gun_ici_288_satirin_TUMU_pencerede_kalir(tmp_path):
    """Beş dakikalık aralıkla bir günün tamamı: 288 satır, ilki gün başlangıcının TAM ANINDA.
    Dizge kıyası o satırı biçim farkıyla eliyordu; ayrıştırılmış damga hepsini içeride bırakır."""
    s = _sayim()
    gun = dt.datetime(2026, 9, 10, tzinfo=dt.timezone.utc)
    satirlar = []
    for i in range(288):
        r = _temiz_satir(i, f"S{i % 10}")
        r["ts"] = (gun + dt.timedelta(minutes=5 * i)).isoformat()
        satirlar.append(r)
    defter = _defter_yaz(tmp_path / "sohbet.jsonl", satirlar)
    sonuc = s.calistir(defter=defter, kart=KART_YOLU, baslangic="2026-09-10T00:00Z")
    assert sonuc["n_mesaj"] == 288, sonuc["n_mesaj"]
    assert sonuc["girdi"]["n_pencere_disi"] == 0, sonuc["girdi"]


def test_bozuk_baslangic_HATA_verir_sessizce_bosaltmaz(tmp_path):
    """"2026-9-8" gibi bozuk bir damga tüm satırları elerdi ve betik `n_mesaj=0` ile sessizce boş
    bir rapor üretirdi — "ölçüm bağlamı tuzağı" sınıfı sessiz yanlış sayı."""
    s = _sayim()
    defter = _defter_yaz(tmp_path / "sohbet.jsonl", _pk_defteri())
    with pytest.raises(ValueError, match="baslangic"):
        s.calistir(defter=defter, kart=KART_YOLU, baslangic="2026-9-8")

    ortam = dict(os.environ, MERIDIAN_ROOT=str(tmp_path), PYTHONPATH=str(KOK))
    r = subprocess.run([sys.executable, str(BETIK_YOLU), "--defter", str(defter),
                        "--cikti", str(tmp_path / "o.json"), "--kart", str(KART_YOLU),
                        "--baslangic", "2026-9-8"],
                       capture_output=True, text=True, cwd=str(tmp_path), env=ortam)
    assert r.returncode != 0, r.stdout
    assert not (tmp_path / "o.json").exists(), "bozuk damgayla rapor yazıldı"


def test_ayristirilamayan_ts_ADIYLA_sayilir(tmp_path):
    s = _sayim()
    satirlar = _pk_defteri()
    bozuk = _temiz_satir(0, "S1")
    bozuk["ts"] = "2026-09-10T10:99:00+00:00"
    satirlar.append(bozuk)
    defter = _defter_yaz(tmp_path / "sohbet.jsonl", satirlar)
    sonuc = s.calistir(defter=defter, kart=KART_YOLU, baslangic="2026-09-10T00:00Z")
    assert sonuc["girdi"]["n_bozuk_ts"] == 1, sonuc["girdi"]
    assert sonuc["n_mesaj"] == 20, sonuc["n_mesaj"]
    assert any("bozuk_ts" in x for x in sonuc["olculemeyen"]), sonuc["olculemeyen"]


def test_baslangic_penceresi_eski_satirlari_disarida_birakir(tmp_path):
    s = _sayim()
    satirlar = [_satir("2026-09-01T10:00:00+00:00", "S0", "eski 12.5",
                       [_tur(atiflar=_atif(sayi=["12.5"])), _tur(tool_calls=0)])]
    satirlar += _pk_defteri()
    defter = _defter_yaz(tmp_path / "sohbet.jsonl", satirlar)
    sonuc = s.calistir(defter=defter, kart=KART_YOLU, baslangic="2026-09-10T00:00:00+00:00")
    assert sonuc["n_mesaj"] == 20, sonuc["n_mesaj"]
    assert sonuc["girdi"]["n_pencere_disi"] == 1, sonuc["girdi"]


# =================================================================================================
# 12) ÖNERİ / MODEL KIRILIMI / BOZUK SATIR
# =================================================================================================
def test_oneri_sayimi_onay_defterinden_okunur(tmp_path):
    s = _sayim()
    defter = _defter_yaz(tmp_path / "sohbet.jsonl", _pk_defteri())
    onaylar = tmp_path / "approvals.jsonl"
    satirlar = [
        {"ts": "2026-09-10T10:01:00+00:00", "id": "SO-20260910T100100Z-1", "kaynak": "sohbet",
         "tur": "not", "hedef": "", "gerekce": "g", "durum": "bekliyor", "oturum": "S1"},
        {"ts": "2026-09-10T10:02:00+00:00", "id": "SO-20260910T100200Z-2", "kaynak": "sohbet",
         "tur": "not", "hedef": "", "gerekce": "g", "durum": "bekliyor", "oturum": "S1"},
        {"ts": "2026-09-10T10:03:00+00:00", "id": "SO-20260910T100300Z-3", "kaynak": "sohbet",
         "tur": "not", "hedef": "", "gerekce": "g", "durum": "bekliyor", "oturum": "S1"},
        {"id": "SO-20260910T100100Z-1", "decision": "approve", "reason": "", "ts": "..."},
        {"id": "SO-20260910T100200Z-2", "decision": "reject", "reason": "", "ts": "..."},
        {"id": "rec:baska-uretici", "decision": "approve", "reason": "", "ts": "..."},
    ]
    onaylar.write_text("".join(json.dumps(r) + "\n" for r in satirlar), encoding="utf-8")

    sonuc = s.calistir(defter=defter, kart=KART_YOLU, onaylar=onaylar)
    assert sonuc["oneri"] == {"n": 3, "onaylanan": 1, "reddedilen": 1, "bekleyen": 1,
                              "neden": None}, sonuc["oneri"]


def test_onay_defteri_yoksa_oneri_None_ve_NEDEN(tmp_path):
    s = _sayim()
    defter = _defter_yaz(tmp_path / "sohbet.jsonl", _pk_defteri())
    sonuc = s.calistir(defter=defter, kart=KART_YOLU)
    assert sonuc["oneri"]["n"] is None and sonuc["oneri"]["neden"], sonuc["oneri"]


def test_model_kirilimi_kunye_basina_ayrilir(tmp_path):
    s = _sayim()
    satirlar = _pk_defteri()
    satirlar.append(_satir(_ts(24), "S2", "T09999 uydurma",
                           [_tur(atiflar=_atif(kimlik=["T00001"]), model="m2"),
                            _tur(tool_calls=0, model="m2")], model="m2"))
    defter = _defter_yaz(tmp_path / "sohbet.jsonl", satirlar)
    sonuc = s.calistir(defter=defter, kart=KART_YOLU)
    assert sonuc["model_kirilimi"]["m2"]["n"] == 1, sonuc["model_kirilimi"]
    assert sonuc["model_kirilimi"]["m2"]["uydurma_oran"] == 1.0, sonuc["model_kirilimi"]
    assert sonuc["model_kirilimi"]["m1"]["n"] == 18, sonuc["model_kirilimi"]


def test_bozuk_satir_sayilir_ve_sayimi_dusurmez(tmp_path):
    s = _sayim()
    yol = tmp_path / "sohbet.jsonl"
    yol.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in _pk_defteri())
                   + "{bu json degil\n[1,2,3]\n", encoding="utf-8")
    sonuc = s.calistir(defter=yol, kart=KART_YOLU)
    assert sonuc["n_mesaj"] == 20, sonuc["n_mesaj"]
    assert sonuc["girdi"]["n_bozuk_satir"] == 2, sonuc["girdi"]


# =================================================================================================
# 13) BOZUK DAMGA GEREKÇESİ DALA BAĞLIDIR (yeniden inceleme, 2026-09-08)
# =================================================================================================
def test_baslangicSIZ_kosumda_bozuk_ts_satiri_OLCUME_DAHIL_edildigini_soyler(tmp_path):
    """`--baslangic` VERİLMEYEN dalda pencere süzgeci HİÇ koşmaz: satırların TAMAMI (bozuk damgalı
    olanlar dahil) ölçüme girer. Tur-2'nin gerekçesi o dalda da "satırlar dışarıda bırakıldı"
    diyordu ve YANLIŞTI — hüküm turunda Rol-1 o cümleyi okuyup N satırı düşerse paydayı hak
    etmeden KÜÇÜLTÜR (eksik payda eşiği geçme yönünde yanlıdır)."""
    s = _sayim()
    satirlar = _pk_defteri()
    bozuk = _temiz_satir(0, "S1")
    bozuk["ts"] = "2026-09-10T10:99:00+00:00"
    satirlar.append(bozuk)
    defter = _defter_yaz(tmp_path / "sohbet.jsonl", satirlar)

    sonuc = s.calistir(defter=defter, kart=KART_YOLU)          # `--baslangic` YOK
    assert sonuc["girdi"]["n_bozuk_ts"] == 1, sonuc["girdi"]
    assert sonuc["n_mesaj"] == 21, sonuc["n_mesaj"]            # satır ELENMEDİ
    gerekce = [x for x in sonuc["olculemeyen"] if x.startswith("bozuk_ts")]
    assert len(gerekce) == 1, sonuc["olculemeyen"]
    assert "DAHİL" in gerekce[0], gerekce[0]
    assert "dışarıda" not in gerekce[0], gerekce[0]


def test_baslangicLI_kosumda_bozuk_ts_satiri_DISARIDA_birakildigini_soyler(tmp_path):
    """Aynı defter, aynı satır, DİĞER dal: pencere süzgeci koşar ve damgası ayrıştırılamayan satır
    içeride mi dışarıda mı bilinemediği için DIŞARIDA bırakılır. İki dal iki AYRI cümle söyler."""
    s = _sayim()
    satirlar = _pk_defteri()
    bozuk = _temiz_satir(0, "S1")
    bozuk["ts"] = "2026-09-10T10:99:00+00:00"
    satirlar.append(bozuk)
    defter = _defter_yaz(tmp_path / "sohbet.jsonl", satirlar)

    sonuc = s.calistir(defter=defter, kart=KART_YOLU, baslangic="2026-09-10T00:00Z")
    assert sonuc["n_mesaj"] == 20, sonuc["n_mesaj"]            # satır ELENDİ
    gerekce = [x for x in sonuc["olculemeyen"] if x.startswith("bozuk_ts")]
    assert len(gerekce) == 1 and "dışarıda" in gerekce[0], gerekce
    assert "DAHİL" not in gerekce[0], gerekce[0]


# =================================================================================================
# 14) SİSTEM İMZASI ÖZGÜLDÜR — geniş bir önek gerçek cevapları ölçüm dışına atardı
# =================================================================================================
def test_sistem_imzalari_OZGULDUR_ve_temiz_cevaplarla_CAKISMAZ():
    """ÖNEK YETMİYORDU (yeniden inceleme, 2026-09-08). Kota şablonunda değişken kısım dokuzuncu
    karakterde başlar, yani `split("(")[0]` en fazla "kota dolu" (9 karakter) üretebilirdi ve
    şablonun ayracı bir gün daha erkene kayarsa önek "kota" gibi AŞIRI GENİŞ bir dizgeye düşerdi:
    çivi yeşil kalır, ama "kota durumu şöyle…" diye başlayan GERÇEK bir model cevabı sistem metni
    sayılıp ölçüm dışına atılırdı (`n_satir` sessizce düşer).

    İMZA ŞABLONUN DEĞİŞMEZ GÖVDESİDİR ve iki sahte çağrının farkından TÜRETİLİR."""
    s = _sayim()
    imzalar = s._sistem_imzalari()
    assert len(imzalar) == 3, imzalar
    for imza in imzalar:
        assert len(imza) >= 12, (len(imza), imza)
    # ÖZGÜLLÜK: hiçbir imza TEMİZ bir PK cevabının içinde geçmez.
    for cevap in {r["cevap"] for r in _pk_defteri()[:13]} | {"kota durumu şöyle: bugün 12 çağrı",
                                                            "meşgul saatlerde AAPL 12.5 oldu"}:
        for imza in imzalar:
            assert imza not in cevap, (imza, cevap)
    # TÜREV: gerçek şablon metni imzayı GERÇEKTEN taşır (imza kopya değil, türev).
    assert any(i in sohbet._kota_cevabi({"bugun": 120, "tavan": 120, "neden": None})
               for i in imzalar)
    assert any(i in sohbet._kota_cevabi({"bugun": None, "tavan": 120, "neden": "halka doldu"})
               for i in imzalar)
    assert any(i in sohbet.MESGUL_CEVABI for i in imzalar)


# =================================================================================================
# 15) YASA 4 ve FAIL-CLOSED BEYAN (yeniden inceleme, 2026-09-08)
# =================================================================================================
def test_damga_yakalayicisi_ISARETLI_ve_GEREKCELI():
    """Yasa 4 `research/` altında MEKANİK olarak zorlanmıyor (codelaw yalnız `meridian`/`tests`/
    `ops` köklerini tarar) — ama yasa kökle sınırlı değil. Kardeş yakalayıcı işaretliyken bu
    yakalayıcının işaretsiz olması, zorlanamayan yerde yasanın gevşediğini gösterirdi."""
    import inspect

    s = _sayim()
    kaynak = inspect.getsource(s.damga_ayristir)
    assert "except ValueError:" in kaynak, kaynak
    gerekceler = [x.split("# sessiz-yutma:", 1)[1].strip()
                  for x in kaynak.splitlines() if "# sessiz-yutma:" in x]
    assert gerekceler, kaynak
    assert len(gerekceler[0]) >= 20, gerekceler


def test_beklenmedik_KESILDI_beyani_paydayi_TAM_saymaz_NEDEN_tasir(tmp_path):
    """FAIL-CLOSED. `cikti_atif_kesildi` bugün yalnız liste (ya da eski `True`) olarak yazılıyor;
    başka bir tip görülürse sayaç onu SESSİZCE yok sayıp o satırın paydasını TAM varsayıyordu —
    fonksiyonun kendi gerekçesi ("payda tam varsaymak sahte uydurma üretirdi") tam da bunu
    yasaklar. Beklenmedik beyan DÖRT sınıfı da eksik sayar ve ADIYLA raporlanır."""
    s = _sayim()
    satirlar = [_temiz_satir(i, "S1") for i in range(3)]
    tur = _tur(atiflar=_atif(sayi=["12.5"]))
    tur["cikti_atif_kesildi"] = "sayi"                      # LİSTE DEĞİL: beklenmedik tip
    satirlar.append(_satir(_ts(38), "S1", "deger 77.7 ve T03333.", [tur, _tur(tool_calls=0)]))
    defter = _defter_yaz(tmp_path / "sohbet.jsonl", satirlar)
    sonuc = s.calistir(defter=defter, kart=KART_YOLU)

    assert sonuc["uydurma"]["uydurma"] == 0, sonuc["uydurma"]
    assert sonuc["uydurma"]["atif_beyani_bozuk_n"] == 1, sonuc["uydurma"]
    assert sonuc["uydurma"]["atif_kesilen_sinif"] == {s_: 1 for s_ in sohbet.ATIF_SINIFLARI}
    assert any("atif_beyani_bozuk" in x for x in sonuc["olculemeyen"]), sonuc["olculemeyen"]


# =================================================================================================
# 16) SEMBOL ÇAPASI SAYAÇ TARAFINDA — cevap DAR, payda GENİŞ
# =================================================================================================
def test_capasiz_uc_harfli_sozcuk_UYDURMA_DEGIL_belirsizdir(tmp_path):
    """`DAL` (Delta Air Lines) bu deponun günlük sözlüğünde bir kelimedir ("dal ucu"). Çapasız
    yazımı sembol sayılsaydı araç çıktısında geçmediği için DOĞRUDAN uydurma olurdu ve 20 satırlık
    bir pencerede tek başına 0,05 eşiğini oynatabilirdi."""
    s = _sayim()
    satirlar = [_temiz_satir(i, "S1") for i in range(3)]
    satirlar.append(_satir(_ts(39), "S1", "DAL kapandı, kartı KALDI olarak işaretledim.",
                           [_tur(atiflar=_atif(kimlik=["T00001"])), _tur(tool_calls=0)]))
    defter = _defter_yaz(tmp_path / "sohbet.jsonl", satirlar)
    sonuc = s.calistir(defter=defter, kart=KART_YOLU)
    assert sonuc["uydurma"]["uydurma"] == 0, sonuc["uydurma"]
    assert sonuc["uydurma"]["belirsiz"] == 1, sonuc["uydurma"]
    assert sonuc["uydurma"]["sinif_kirilimi"]["sembol"]["payda"] == 3, sonuc["uydurma"]


def test_CAPALI_sembol_hala_uydurma_olabilir_capa_MUAFIYET_degildir(tmp_path):
    """Çapa bir MUAFİYET DEĞİLDİR: "$ZZZ 12.5" araç çıktısında geçmiyorsa hâlâ uydurmadır.
    (Kontrol: aynı satırın `kaynaklar` künyesinde geçen sembol paydaya girer, uydurma olmaz.)"""
    s = _sayim()
    satirlar = [_temiz_satir(i, "S1") for i in range(3)]
    satirlar.append(_satir(_ts(40), "S1", "$HAL 12.5 seviyesinde.",
                           [_tur(atiflar=_atif(sayi=["12.5"], kimlik=["T00001"])),
                            _tur(tool_calls=0)]))
    defter = _defter_yaz(tmp_path / "sohbet.jsonl", satirlar)
    sonuc = s.calistir(defter=defter, kart=KART_YOLU)
    assert sonuc["uydurma"]["uydurma"] == 1, sonuc["uydurma"]
    assert sonuc["uydurma"]["sinif_kirilimi"]["sembol"]["uydurma"] == 1, sonuc["uydurma"]

    # KAYNAK KÜNYESİ ÇAPADIR AMA PAYDA DEĞİLDİR: sembol sınıfa girer, araç çıktısında
    # geçmediği için hâlâ uydurmadır — çapa yalnız "bu bir ticker mı" sorusunu cevaplar.
    satirlar[-1]["kaynaklar"] = [{"arac": "bar_sorgu", "anahtar": "HAL 2026-09"}]
    defter2 = _defter_yaz(tmp_path / "b" / "sohbet.jsonl", satirlar)
    sonuc2 = s.calistir(defter=defter2, kart=KART_YOLU)
    assert sonuc2["uydurma"]["sinif_kirilimi"]["sembol"]["uydurma"] == 1, sonuc2["uydurma"]


def test_BUYUK_HARFLI_ve_COK_BOSLUKLU_yuzde_BELIRSIZ_kovasinda_SAYILIR(tmp_path):
    """SAYI SINIFINDAN ELENMEK YETMEZ. Elenen değer `belirsiz` kovasında SAYILMAZSA hem paydadan
    hem "ölçülemeyen" beyanından SESSİZCE düşer ve körlüğün belirtisi hiçbir şey olur (bedel
    yasası) — tur-2'de `YÜZDE 12` ve `yüzde  34` tam olarak böyle düşüyordu.

    İKİ KOVA AYNI BOŞLUK TAVANINI TAŞIR (üç): biri diğerinden geniş olsaydı aynı karakter aralığı
    hem `sayi` hem `belirsiz` sayılırdı; dar olsaydı değer iki kovadan da düşerdi."""
    s = _sayim()
    satirlar = [_temiz_satir(i, "S1") for i in range(3)]
    satirlar.append(_satir(_ts(41), "S1",
                           "T00001 icin YÜZDE 12 arttı, yüzde  34 düştü, 56  % kaldı.",
                           [_tur(atiflar=_atif(kimlik=["T00001"])), _tur(tool_calls=0)]))
    defter = _defter_yaz(tmp_path / "sohbet.jsonl", satirlar)
    sonuc = s.calistir(defter=defter, kart=KART_YOLU)
    assert sonuc["uydurma"]["uydurma"] == 0, sonuc["uydurma"]
    assert sonuc["uydurma"]["belirsiz"] == 3, sonuc["uydurma"]
    assert sonuc["uydurma"]["sinif_kirilimi"]["sayi"]["payda"] == 3, sonuc["uydurma"]
