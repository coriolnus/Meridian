"""v515 · sessizlik jetonu doğal Türkçe "sessiz" kelimesiyle ÇARPIŞMAZ — TSK-202.

NUMARA KİMLİKTİR: `v515` Rol-1 tarafından REZERVE EDİLDİ (2026-09-17). Bu çalışma kopyasında ne
dosya adı ne metin olarak geçiyordu (ölçüldü: `ls tests` + depo içi arama).

ÖLÇÜLEN SORUN (Rol-1 ölçümü, bu turda YENİDEN ölçülmedi): A1'de son 30 günde dört
`bekci_brifingi_sessizlik_jetonu_yakin_iska` olayı var ve DÖRDÜ DE YANLIŞ POZİTİF — cevap alanları
dolu, gerçek brifing (biri "operatör müdahalesi gerekebilir" diyor). Model susmak İSTEMEMİŞ;
metinde doğal Türkçe "sessiz" kelimesi geçmiş. Mekanizma: yakın-ıska araması cevabı Türkçe
İ/I/i/ı katlayıp BÜYÜTTÜKTEN SONRA kelime listesinde `SESSIZ` arıyordu, yani küçük harfli doğal
"sessiz" kontrol jetonuyla AYNI dizgeye katlanıyordu → sıralanmış brifing ham listeye düşüyordu.
Bu turun ek ölçümü: `@bekci` ve `@sef` SOUL'unun "ilk satır sade özet" ÖRNEĞİ küçük harfli
"sessiz" taşıyor ("bir ölçüm 6 gündür sessiz ama …"); 09-06 öneki de örneğin açılışını izliyor
("Sistem sağlıklı …"). Modelin kelimeyi istemden aldığı bir OLASILIKTIR, ölçülmedi.

ROL-1 KARARI, TUR 1: TAM jeton eşleşmesi AYNEN kalır (katlanmış karşılaştırma); yakın ıska yalnız
KONTROL KELİMESİ BİÇİMİNDE (tümüyle büyük harfli ayrı kelime) aranır.
ROL-1 KARARI, TUR 2 (K5 bedeli REDDEDİLDİ): Tur 1 kuralında "bugün sessiz kalıyorum" gibi KISA bir
susma niyeti makullük kapısını geçip gövde olarak gidiyordu — orijinal asimetrinin koruduğu sınıfın
ta kendisi. Ölçülen dört yanlış pozitif UZUN brifinglerdi. Ayrım UZUNLUĞA bağlandı:
  · anlamlı karakter < `soul_denetimi.KISA_CEVAP_ANLAMLI_TAVAN` → katlanmış kelime eşleşmesi yakın ıska
    (eski güvenli davranış);
  · aksi hâlde yalnız büyük harfli kontrol kelimesi biçimi yakın ıska.
"Anlamlı karakter" makullük kapısının sayımıdır ve TEK tanımdır (`anlamli_karakter_sayisi`); üç
botun `_cevap_makul`u da aynı fonksiyonu okur.

TEK KAYNAK KARARI (Tur 1 ölçümü): üç bot jeton sabitini, kenar kümesini ve iki fonksiyonu AYRI
KOPYA taşıyordu ve kopyalar SESSİZCE AYRIŞMIŞTI — şerhleri "NBSP dâhil" diyordu, ama `@bekci` ve
`@karne` kopyasında NBSP yerine düz boşluk vardı. Türetme seçildi (Rol-1 KABUL: kopya hatası
düzeltildi). Botlar arasındaki TEK TASARIM farkı (karnede yakın-ıska dalı yok — SAPMA 1)
tüketimdedir: karne ortak fonksiyonun yalnız tam yarısını okur.

ÇİVİLER:
  K2 — TAM JETON: `SESSIZ`, `sessiz`, `Sessiz.`, backtick'li, Türkçe `SESSİZ` → tam jeton.
  K3 — GERÇEK YAKIN ISKA: kontrol kelimesi biçimli jeton + fazladan içerik → yakın ıska; KISA ve
       UZUN cevapta ayrı ayrı (uzun dal büyük harf kuralını, kısa dal katlanmış eşleşmeyi taşır).
  K4 — ÜÇ BOT: jeton ve anlamlı-karakter sayımı kopyası yok, ortak fonksiyonlar çağrılır; NBSP
       ayrışmasının kapandığı ve üç botun aynı jeton kararını verdiği uçtan uca ölçülür.
  K5 — KISA KÜÇÜK HARFLİ NİYET → yakın ıska (ham) — Tur 1'de tersiydi. Kalan bedel (tavanın
       üstündeki küçük harfli niyet paragrafı) adıyla ölçülür ve sabitlenir.
  K6 — ölçülen dört yanlış pozitifin BİÇİMİNDEKİ uzun brifingler yakın ıska DEĞİL (Tur 1'in K1'i,
       tavan sınırına göre uzun metinlerle yeniden kuruldu). Eski kuralda çarpıştıkları ayrıca ölçülür.
  K7 — tavanın hemen altı / tam sınırı ve tavan değerinin GEREKÇESİ (ölçülen iki küme arasında).

SANDBOX HER UÇTAN UCA ÇİVİDE: `sirala`/`sun` `obs.log` yazar.
"""
from __future__ import annotations

import ast
import importlib
import pathlib

import pytest

from tests.test_ham_dal_beyani_v513 import _kur
from tests.test_soul_denetimi_v385 import _Kuyruk, _temiz_cevap

KOK = pathlib.Path(__file__).resolve().parent.parent
BOTLAR = ("sef", "bekci", "karne")
SIRALAMA_FN = {"sef": "sirala", "bekci": "sirala", "karne": "sun"}

#: Kural denetimi yoluna varış işareti.
DENETIM_YOLU = "kural_gecisi"
#: `(None, "llm")` — bot susma hükmü verdi, teslimat YOK.
SUSMA = "susma"
YAKIN_ISKA_DALI = "sessizlik_jetonu_yakin_iska"

#: Görünmez karakterler kaynakta KAÇIŞLA değil kod noktasıyla kurulur (bir düzenleme aracı `\\u`
#: kaçışını gerçek karaktere çevirip ayrışmayı yeniden gözden saklayabiliyor — Tur 1'de oldu).
NBSP = chr(0x00A0)


def _sd():
    sd = importlib.import_module("ops.soul_denetimi")
    # WORKTREE PYTHONPATH TUZAĞI: modül BU ağaçtan yüklenmediyse çivi başka bir kodu ölçer.
    assert pathlib.Path(sd.__file__).resolve().is_relative_to(KOK), (
        f"ortak modül bu ağaçtan yüklenmedi: {sd.__file__} (kök {KOK})")
    return sd


def _say(metin: str) -> int:
    """Makullük kapısının TEK sayımı — çivi ikinci bir sayım yazmaz."""
    return _sd().anlamli_karakter_sayisi(metin)


def _eski_kural_yakin_iska(cevap: str) -> bool:
    """TSK-202 ÖNCESİ yakın-ıska kuralı — POZİTİF KONTROL için bilerek burada durur: cevap katlanıp
    BÜYÜTÜLDÜKTEN sonra kelime listesinde jeton aranıyordu. Bir vaka metni bu kuralda yakın ıska
    DEĞİLSE, çivi onun düzeldiğini değil hiç çarpışmadığını ölçer (vakum-yeşil)."""
    sd = _sd()
    norm = sd.jeton_normalize(cevap)
    if norm == sd.SESSIZLIK_JETONU:
        return False
    return sd.SESSIZLIK_JETONU in [w.strip(sd.JETON_KENAR_KARAKTERLERI) for w in norm.split()]


def _kosum(bot, cevap, tmp_path, monkeypatch, request):
    """GERÇEK sıralama/sunum yolu: sahte model `cevap`ı verir, denetçi (çağrılırsa) TEMİZ der.
    Dönüş: (modül, ham, metin, kaynak)."""
    m = _kur(bot, tmp_path, monkeypatch, request)
    monkeypatch.setattr(m, "_profili_cagir", _Kuyruk(cevap, _temiz_cevap()))
    ham = m.topla()
    metin, kaynak = getattr(m, SIRALAMA_FN[bot])(ham)
    return m, ham, metin, kaynak


def _sonuc(ham, metin, kaynak) -> str:
    return SUSMA if (metin is None and kaynak == "llm") else str(ham.get("dal"))


def _olaylar() -> list[str]:
    from meridian import store
    return [str(e.get("event")) for e in store.read_jsonl("events.jsonl")]


# ================================================================================================
# ÖLÇÜM KÜMELERİ — tavanın iki yanı
# ================================================================================================

#: Ölçülen dört yanlış pozitifin (A1, bekci, 08-31 · 09-06 · 09-11 · 09-12) BİÇİMİNİ taşıyan uzun
#: brifingler. Kopya DEĞİL biçim taklidi: SOUL'un istediği yapı (sade ilk satır + kalem satırları),
#: dördünün de ilk satırı ROADMAP'e kaydedilen öneki izler, üçü çok satırlı, hepsinde küçük harfli
#: doğal "sessiz" (tırnaklı, virgüllü, iki nokta, cümle içi).
UZUN_BRIFINGLER = [
    'ÖLÇÜLEMEDİ: 108 olayda kadans ölçülemedi. Ölçülemeyen olaylar "sessiz" değil, ölçülemiyor; '
    "bu fark önemli.\n- tick_kadansi 108 olayda ölçülemedi. Ölçüm zinciri kırık olabilir. Olay "
    "defterine bak.",
    "Sistem sağlıklı görünüyor; iki ölçüm grubu dikkat çekiyor. Öneri kuyruğu üç gündür sessiz, "
    "bu beklenen bir durgunluk ama warmup merdiveni 93 turdur kilitli ve sprint liyakatle hiç "
    "ateşlemiyor, bugün duvar kaydına bakılmalı.",
    "Sistemde 10 gündür beklenen bir olay gelmiyor.\n- Kaynak sessiz kaldı ama kadans ölçülemedi. "
    "Sessizlik zararsız da olabilir, kırık bir bağ da. Bağlantı günlüğüne bugün bak.",
    "Sistemde bir kurtarma mekanizması 3 gündür takılı, iki brifing akışı da durmuş — operatör "
    "müdahalesi gerekebilir.\n- Akışlar sessiz: hata yok, çıktı da yok.\n- Kurtarma birimi üç "
    "gündür yeniden başlamadı; birim günlüğüne bak.",
]
UZUN_BRIFING_SAYIMLARI = [158, 187, 140, 180]

#: Doğal SUSMA NİYETİ cümleleri — model yalnız `SESSIZ` yazmak yerine küçük harfle gerekçe
#: eklediğinde. Tek cümlelik en uzun örnek bilerek ayrıntılıdır (tavanın alt yanı).
NIYET_CUMLELERI = [
    "sessiz kalıyorum",
    "bugün sessiz kalıyorum",
    "Bugün sessiz kalıyorum, bildirilecek yeni bir şey yok.",
    "Kaynaklarda değişen bir kalem yok; bugünkü hükmüm: sessiz.",
    "Bugün bildirilecek yeni bir şey yok, o yüzden sessiz kalıyorum.",
    "sessiz — takılı duvar hâlâ aynı durumda, yeni bir ölçüm gelmedi, dün de bildirilmişti.",
    "Bugün sessiz kalıyorum: alarm yığınında yeni kalem yok, öneri kuyruğu değişmedi ve takılı "
    "duvar dün zaten bildirildi.",
]
NIYET_SAYIMLARI = [15, 20, 45, 48, 52, 69, 98]

#: KALAN BEDEL — tavanın ÜSTÜNDEKİ küçük harfli susma niyeti paragrafı (yakın ıskadan kaçan sınıf).
UZUN_NIYET_PARAGRAFI = (
    "Bugün sessiz kalıyorum: alarm yığınında yeni kalem yok, öneri kuyruğu değişmedi, takılı duvar "
    "dün zaten bildirildi ve değeri aynı kaldı; ölçülemeyen kaynak da yok, yarın yeniden bakarım.")
UZUN_NIYET_SAYIMI = 154

#: ROADMAP'e kaydedilen dört yanlış pozitif ÖNEKİ (ASCII çevriyazı, "..." kırpmaları çıkarıldı).
#: Tam 200 karakterlik alanlar bu depoda YOK (A1 olay defterinde) — bu sayılar ALT SINIRDIR, kapı
#: değildir. Kayıt, tavanın FP yanının neden A1'de doğrulanması gerektiğini sayıyla gösterir.
FP_ONEKLERI = [
    'OLCULEMEDI: 108 olayda Olculemeyen olaylar "sessiz" degil, olc',
    "Sistem saglikli gorunuyor; iki olcum grubu dikkat cekiyor",
    "Sistemde 10 gundur beklenen bir olay gelmiyor",
    "Sistemde bir kurtarma mekanizmasi 3 gundur takili, iki brifing akisi da durmus — operator "
    "mudahalesi gerekebilir",
]
FP_ONEK_ALT_SINIRLARI = [51, 49, 39, 95]

#: SOUL'un (bekci ve sef) "ilk satır sade özet" örneği — küçük harfli "sessiz" TAŞIYOR.
SOUL_ILK_SATIR_ORNEGI = "Sistem sağlıklı; bir ölçüm 6 gündür sessiz ama nedeni zararsız görünüyor."


# ================================================================================================
# K2 — TAM JETON aynen tanınır
# ================================================================================================

TAM_JETONLAR = ["SESSIZ", "sessiz", "Sessiz.", "`SESSIZ`", "SESSİZ", "**SESSİZ**", "- SESSIZ"]


@pytest.mark.parametrize("cevap", TAM_JETONLAR)
def test_K2_TAM_JETON_KATLANMIS_KARSILASTIRMAYLA_AYNEN_TANINIR(cevap):
    """Cevabın TAMAMI jetonsa küçük harf de, noktalama da, Türkçe İ de SUSMA demektir."""
    assert _sd().jeton_gecer_mi(cevap) == (True, False), (
        f"{cevap!r} tam jeton olarak TANINMADI: {_sd().jeton_gecer_mi(cevap)}")


# ================================================================================================
# K3 — GERÇEK YAKIN ISKA: kontrol kelimesi biçimi + fazladan içerik (kısa ve uzun)
# ================================================================================================

KISA_YAKIN_ISKALAR = [
    "SESSIZ\n\nama şunu da ekleyeyim: duvar hâlâ sınanmıyor.",
    "Bugün SESSIZ çünkü kayda değer bir şey yok.",
    "Bugün SESSİZ çünkü kayda değer bir şey yok.",
    "**SESSIZ** — yalnız bir not düşeyim.",
]
#: Uzun dalın kendi kuralı (büyük harf) ayrıca ölçülür: kısa örnekler katlanmış eşleşmeyle de yakın
#: ıska olurdu, yani uzun daldaki büyük harf kuralını ISIRMAZLAR.
UZUN_YAKIN_ISKALAR = [
    "SESSIZ\n\n" + UZUN_BRIFINGLER[3],
    UZUN_BRIFINGLER[1] + " Genel hüküm: SESSİZ.",
]


@pytest.mark.parametrize("cevap", KISA_YAKIN_ISKALAR + UZUN_YAKIN_ISKALAR)
def test_K3_KONTROL_KELIMESI_BICIMINDE_JETON_YAKIN_ISKADIR(cevap):
    """ASİMETRİ KORUNUR: model jetonu kontrol kelimesi biçiminde yazıp yanına içerik eklediyse
    niyet ölçülemez — güvenli yön HAMdır. Türkçe noktalı `SESSİZ` de büyük harftir."""
    assert _sd().jeton_gecer_mi(cevap) == (False, True), (
        f"{cevap!r} yakın ıska sayılmadı: {_sd().jeton_gecer_mi(cevap)}")


def test_K3_UZUN_YAKIN_ISKALAR_GERCEKTEN_TAVANIN_USTUNDE():
    """Vakum-yeşile karşı: uzun örnekler uzun DALI ölçmüyorsa K3'ün uzun yarısı boştur."""
    tavan = _sd().KISA_CEVAP_ANLAMLI_TAVAN
    assert all(_say(c) >= tavan for c in UZUN_YAKIN_ISKALAR), [_say(c) for c in UZUN_YAKIN_ISKALAR]


@pytest.mark.parametrize("bot", ["sef", "bekci"])
@pytest.mark.parametrize("cevap", [KISA_YAKIN_ISKALAR[1], UZUN_YAKIN_ISKALAR[0]],
                         ids=["kisa", "uzun"])
def test_K3_GERCEK_YAKIN_ISKA_HAM_DALA_DUSER(bot, cevap, tmp_path, monkeypatch, sandbox_state,
                                            request):
    m, ham, metin, kaynak = _kosum(bot, cevap, tmp_path, monkeypatch, request)
    assert ham.get("dal") == YAKIN_ISKA_DALI and kaynak == "ham", (
        f"@{bot}: gerçek yakın ıska ham dala düşmedi: dal={ham.get('dal')!r} · {kaynak!r}")
    assert f"{bot}_brifingi_{YAKIN_ISKA_DALI}" in _olaylar(), f"@{bot}: yakın ıska ADIYLA kayda geçmedi"


# ================================================================================================
# K4 — ÜÇ BOT, TEK KAYNAK
# ================================================================================================

#: Botlarda artık DURMAMASI gereken kopya adları (TSK-202 öncesi üç botta ayrı ayrı vardı).
KOPYA_TANIMLAR = frozenset({"_jeton_normalize", "_jeton_gecer_mi"})
KOPYA_SABITLER = frozenset({"_KENAR_KARAKTERLERI", "_TR_KATLAMA"})


@pytest.mark.parametrize("bot", BOTLAR)
def test_K4_BOTTA_JETON_KOPYASI_YOK_ORTAK_FONKSIYON_CAGRILIR(bot):
    """KAYNAK TARAMASI (AST): bot jeton ilkelini ve anlamlı-karakter sayımını KENDİSİ yazmaz, ortak
    fonksiyonları çağırır. Jeton sabitini adıyla taşıyan bot (karne) onu TÜRETİR."""
    sd = _sd()
    src = (KOK / "ops" / f"{bot}_brifingi.py").read_text(encoding="utf-8")
    agac = ast.parse(src)
    tanimlar = {n.name for n in ast.walk(agac)
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    assert not (tanimlar & KOPYA_TANIMLAR), (
        f"@{bot} jeton fonksiyonunun KOPYASINI yeniden tanımladı: {sorted(tanimlar & KOPYA_TANIMLAR)}")
    for d in agac.body:
        if not isinstance(d, ast.Assign):
            continue
        adlar = {t.id for t in d.targets if isinstance(t, ast.Name)}
        assert not (adlar & KOPYA_SABITLER), (
            f"@{bot} kenar/katlama kümesinin KOPYASINI taşıyor: {sorted(adlar & KOPYA_SABITLER)}")
        assert not (isinstance(d.value, ast.Constant) and d.value.value == sd.SESSIZLIK_JETONU), (
            f"@{bot} jeton dizgesini LİTERAL olarak yeniden yazdı: {ast.unparse(d)}")
        if "SESSIZLIK_JETONU" in adlar:
            assert ast.unparse(d.value) == "soul_denetimi.SESSIZLIK_JETONU", (
                f"@{bot} jeton sabitini türetmiyor: {ast.unparse(d)}")
    cagrilar = {ast.unparse(n.func) for n in ast.walk(agac) if isinstance(n, ast.Call)}
    assert "soul_denetimi.jeton_gecer_mi" in cagrilar, (
        f"@{bot} ortak `soul_denetimi.jeton_gecer_mi`yi çağırmıyor")
    assert "soul_denetimi.anlamli_karakter_sayisi" in cagrilar, (
        f"@{bot} makullük sayımını ortak `soul_denetimi.anlamli_karakter_sayisi`den almıyor")
    nitelikler = {n.attr for n in ast.walk(agac) if isinstance(n, ast.Attribute)}
    assert "isalnum" not in nitelikler, (
        f"@{bot} İKİNCİ bir anlamlı-karakter sayımı taşıyor (`isalnum`) — tavan ile taban ayrışır")


def test_K4_KENAR_KUMESI_BOSLUK_AILESINI_BEYAN_ETTIGI_GIBI_TASIR():
    """Ayrışmanın KENDİSİ: şerh "NBSP ve sıfır-genişlikliler dâhil" diyordu, iki kopyada NBSP yoktu."""
    kume = set(_sd().JETON_KENAR_KARAKTERLERI)
    bosluk_ailesi = {" ", "\t", "\r", "\n", NBSP, chr(0x200B), chr(0x200C), chr(0x200D), chr(0xFEFF)}
    assert bosluk_ailesi <= kume, f"kenar kümesinde eksik boşluk: {sorted(map(repr, bosluk_ailesi - kume))}"


#: (cevap, bot başına beklenen sonuç). NBSP'li satırlar ayrışmanın uçtan uca izidir — botlar cevabı
#: önce `str.strip()` ile kırpar (NBSP'yi kenardan zaten soyar), o yüzden NBSP İÇERİDE olmalı.
UC_BOT_TABLOSU = [
    ("-" + NBSP + "SESSIZ", {"sef": SUSMA, "bekci": SUSMA, "karne": "sessizlik_jetonu_anomalisi"}),
    ("`" + NBSP + "SESSIZ" + NBSP + "`",
     {"sef": SUSMA, "bekci": SUSMA, "karne": "sessizlik_jetonu_anomalisi"}),
    ("sessiz", {"sef": SUSMA, "bekci": SUSMA, "karne": "sessizlik_jetonu_anomalisi"}),
    # SAPMA 1: karnede yakın-ıska dalı YOK — tasarım farkı tüketimde, ilkelde değil.
    ("Bugün SESSIZ çünkü kayda değer bir şey yok.",
     {"sef": YAKIN_ISKA_DALI, "bekci": YAKIN_ISKA_DALI, "karne": DENETIM_YOLU}),
    ("bugün sessiz kalıyorum",
     {"sef": YAKIN_ISKA_DALI, "bekci": YAKIN_ISKA_DALI, "karne": DENETIM_YOLU}),
    (UZUN_BRIFINGLER[2], {"sef": DENETIM_YOLU, "bekci": DENETIM_YOLU, "karne": DENETIM_YOLU}),
]


@pytest.mark.parametrize("bot", BOTLAR)
@pytest.mark.parametrize("cevap,beklenen", UC_BOT_TABLOSU,
                         ids=["madde_nbsp", "backtick_nbsp", "kucuk_tam", "yakin_iska",
                              "kisa_niyet", "uzun_brifing"])
def test_K4_UC_BOT_AYNI_JETON_KARARINI_VERIR(bot, cevap, beklenen, tmp_path, monkeypatch,
                                            sandbox_state, request):
    m, ham, metin, kaynak = _kosum(bot, cevap, tmp_path, monkeypatch, request)
    assert _sonuc(ham, metin, kaynak) == beklenen[bot], (
        f"@{bot} {cevap!r}: beklenen {beklenen[bot]!r}, ölçülen {_sonuc(ham, metin, kaynak)!r}")


def test_K4_KARNE_JETON_SABITI_ORTAK_NESNEDIR():
    karne = importlib.import_module("ops.karne_brifingi")
    assert karne.SESSIZLIK_JETONU is _sd().SESSIZLIK_JETONU


# ================================================================================================
# K5 — KISA küçük harfli niyet YAKIN ISKADIR; kalan bedel adıyla
# ================================================================================================

@pytest.mark.parametrize("cevap", NIYET_CUMLELERI)
def test_K5_KISA_KUCUK_HARFLI_NIYET_YAKIN_ISKADIR(cevap):
    """Orijinal asimetrinin koruduğu sınıf: model susmak istedi ama jetonu tam yazmadı. Kısa cevapta
    niyet ölçülemez → güvenli yön HAM. "bugün sessiz kalıyorum" (20) ve "sessiz kalıyorum" (15) dahil."""
    assert _say(cevap) < _sd().KISA_CEVAP_ANLAMLI_TAVAN, f"niyet cümlesi kısa değil: {_say(cevap)}"
    assert _sd().jeton_gecer_mi(cevap) == (False, True), (
        f"kısa susma niyeti yakın ıskadan KAÇTI (Tur 1 bedeli geri geldi): {cevap!r}")


@pytest.mark.parametrize("bot", ["sef", "bekci"])
@pytest.mark.parametrize("cevap", NIYET_CUMLELERI[:3], ids=["sessiz_kaliyorum",
                                                            "bugun_sessiz_kaliyorum", "cumle_45"])
def test_K5_KISA_NIYET_HAM_DALA_DUSER_GOVDE_OLMAZ(bot, cevap, tmp_path, monkeypatch, sandbox_state,
                                                request):
    """Uçtan uca: niyet cümlesi TESLİM EDİLMEZ; `@sef`te ham brifing gider (kaynaklar kaybolmaz)."""
    m, ham, metin, kaynak = _kosum(bot, cevap, tmp_path, monkeypatch, request)
    assert (ham.get("dal"), kaynak) == (YAKIN_ISKA_DALI, "ham"), (
        f"@{bot}: kısa niyet ham dala düşmedi: {ham.get('dal')!r} · {kaynak!r} · {metin!r}")
    govde, _damga = m._paketle(metin, kaynak, ham)
    assert cevap not in govde, f"@{bot}: niyet cümlesi gövdeye girdi: {govde!r}"
    isaret = "MECHANISM_STALE" if bot == "sef" else "warmup_merdiven_kilitli"
    assert isaret in govde, f"@{bot}: ham gövde teslim edilmiyor: {govde!r}"


@pytest.mark.parametrize("bot", ["sef", "bekci"])
def test_K5_KALAN_BEDEL_TAVAN_USTU_KUCUK_HARFLI_NIYET_PARAGRAFI(bot, tmp_path, monkeypatch,
                                                              sandbox_state, request):
    """KAYBEDİLEN ŞEY — adıyla (bedel yasası). Tavanın ÜSTÜNDE, küçük harfli, susma niyetli bir
    paragraf yakın ıskadan KAÇAR: makullük kapısını geçer, denetim yoluna varır ve (denetçi temiz
    derse) model metni teslim edilir. Denetçinin şema soruları sessizlik niyetini sormaz (ölçülür).
      · `@sef`  — metin GÖVDENİN kendisidir: ham brifing gitmez, kaynaklar damgalanabilir.
      · `@bekci`— metin yalnız sıralama bloğudur: ölçülen liste yine gider."""
    sd = _sd()
    assert _say(UZUN_NIYET_PARAGRAFI) == UZUN_NIYET_SAYIMI >= sd.KISA_CEVAP_ANLAMLI_TAVAN
    assert _eski_kural_yakin_iska(UZUN_NIYET_PARAGRAFI), "paragraf eski kuralda yakın ıska değildi — vakum"
    assert not any("sess" in alan for alan in sd.SEMA_ALANLARI), (
        f"denetçi şeması artık sessizlik soruyor — bedel yeniden ölçülmeli: {sorted(sd.SEMA_ALANLARI)}")
    m, ham, metin, kaynak = _kosum(bot, UZUN_NIYET_PARAGRAFI, tmp_path, monkeypatch, request)
    assert ham.get("dal") == DENETIM_YOLU and (metin, kaynak) == (UZUN_NIYET_PARAGRAFI, "llm"), (
        f"@{bot}: kalan bedel sınıfının yolu değişti: dal={ham.get('dal')!r} · {kaynak!r}")
    govde, damga = m._paketle(metin, kaynak, ham)
    assert UZUN_NIYET_PARAGRAFI in govde
    if bot == "sef":
        assert "MECHANISM_STALE" not in govde, "sef: ham brifing de gövdeye girdi — bedel ölçümü yanlış"
        assert damga and damga == [k["kaynak"] for k in ham["teslim_edilecek"]], (
            f"sef: damgalanabilir kaynak kümesi beklenenden farklı: {damga!r}")
    else:
        assert "warmup_merdiven_kilitli" in govde, "bekci: niyet paragrafı ÖLÇÜLEN LİSTEYİ düşürdü"


# ================================================================================================
# K6 — ölçülen yanlış pozitiflerin biçimindeki UZUN brifingler yakın ıska DEĞİL
# ================================================================================================

@pytest.mark.parametrize("cevap", UZUN_BRIFINGLER, ids=["0831", "0906", "0911", "0912"])
def test_K6_UZUN_BRIFINGDEKI_DOGAL_SESSIZ_YAKIN_ISKA_DEGIL(cevap):
    """Saf fonksiyon: uzun, dolu brifing ne tam jeton ne yakın ıska. ESKİ kuralda yakın ıska olduğu
    ve tavanın ÜSTÜNDE olduğu ayrıca ölçülür — metin çarpışmayı ve uzun dalı GERÇEKTEN taşıyor."""
    sd = _sd()
    assert _eski_kural_yakin_iska(cevap), f"vaka metni eski kuralda çarpışmıyor — vakum: {cevap!r}"
    assert _say(cevap) >= sd.KISA_CEVAP_ANLAMLI_TAVAN, f"vaka metni tavanın altında: {_say(cevap)}"
    assert sd.jeton_gecer_mi(cevap) == (False, False), (
        f"doğal 'sessiz' kelimesi uzun brifingde hâlâ kontrol jetonu sayılıyor (4/4 yanlış pozitif "
        f"sınıfı): {cevap!r} → {sd.jeton_gecer_mi(cevap)}")


@pytest.mark.parametrize("bot", ["sef", "bekci"])
@pytest.mark.parametrize("cevap", UZUN_BRIFINGLER, ids=["0831", "0906", "0911", "0912"])
def test_K6_UZUN_BRIFING_SIRALAMA_OLARAK_TESLIM_EDILIR(bot, cevap, tmp_path, monkeypatch,
                                                     sandbox_state, request):
    """Uçtan uca: 09-12 vakasında "operatör müdahalesi gerekebilir" diyen SIRALI bir brifing ham
    listeye düşmüştü. Artık denetim yoluna varır ve (temiz hükümle) AYNEN teslim edilir."""
    m, ham, metin, kaynak = _kosum(bot, cevap, tmp_path, monkeypatch, request)
    assert ham.get("dal") == m.soul_denetimi.DAL_KURAL_GECISI == DENETIM_YOLU, (
        f"@{bot}: uzun brifing denetim yoluna varmadı, dal={ham.get('dal')!r}")
    assert (metin, kaynak) == (cevap, "llm"), f"@{bot}: dolu brifing teslim edilmedi: {kaynak!r}"
    assert f"{bot}_brifingi_{YAKIN_ISKA_DALI}" not in _olaylar(), (
        f"@{bot}: yanlış pozitif yakın-ıska olayı yine deftere düştü")


# ================================================================================================
# K7 — tavanın sınırı ve GEREKÇESİ
# ================================================================================================

def _sinir_metni(n: int, jeton: str = "sessiz") -> str:
    """Anlamlı karakter sayısı TAM `n` olan, `jeton` kelimesini ayrı kelime olarak taşıyan metin.
    Sayım ortak fonksiyonla DOĞRULANIR — yardımcı kendi sayımını yazmaz."""
    bas = f"Kaynak {jeton} kaldı; "
    kalan = n - _say(bas)
    metin = bas + "kalem " * (kalan // 5) + "x" * (kalan % 5)
    assert _say(metin) == n, (n, _say(metin))
    return metin.rstrip()


def test_K7_TAVAN_ALTI_KUCUK_HARF_YAKIN_ISKA_TAVAN_SINIRINDA_DEGIL():
    tavan = _sd().KISA_CEVAP_ANLAMLI_TAVAN
    assert _sd().jeton_gecer_mi(_sinir_metni(tavan - 1)) == (False, True), (
        f"tavanın bir altı ({tavan - 1}) kısa sayılmadı")
    assert _sd().jeton_gecer_mi(_sinir_metni(tavan)) == (False, False), (
        f"tavanın kendisi ({tavan}) hâlâ kısa sayılıyor — sınır kaydı")


@pytest.mark.parametrize("jeton", ["Sessiz", "sessız"])
def test_K7_TAVAN_ALTINDA_KATLANMIS_ESLESME_TAVAN_USTUNDE_DEGIL(jeton):
    """Kısa dal KATLANMIŞ eşleşmedir: cümle başı `Sessiz` ve `sessız` yazımı da yakalanır; uzun dalda
    ikisi de kontrol kelimesi biçimi DEĞİLDİR."""
    tavan = _sd().KISA_CEVAP_ANLAMLI_TAVAN
    assert _sd().jeton_gecer_mi(_sinir_metni(tavan - 1, jeton)) == (False, True)
    assert _sd().jeton_gecer_mi(_sinir_metni(tavan, jeton)) == (False, False)


@pytest.mark.parametrize("jeton", ["SESSIZ", "SESSİZ"])
def test_K7_TAVAN_USTUNDE_BUYUK_HARF_KONTROL_KELIMESI_YINE_YAKIN_ISKA(jeton):
    tavan = _sd().KISA_CEVAP_ANLAMLI_TAVAN
    assert _sd().jeton_gecer_mi(_sinir_metni(tavan, jeton)) == (False, True)
    assert _sd().jeton_gecer_mi(_sinir_metni(tavan + 40, jeton)) == (False, True)


def test_K7_TAVAN_OLCULEN_IKI_KUMENIN_ARASINDA():
    """GEREKÇE ÇİVİSİ — tavanın değeri bir seçim değil iki ölçülen kümenin arasıdır:
      · alt yan: doğal susma niyeti cümleleri (en uzun tek cümle örneği 98);
      · üst yan: ölçülen dört yanlış pozitifin biçimindeki uzun brifingler (en kısası 140).
    Sayımlar LİTERAL kayıttır: kümeye bir örnek eklenir ya da sayım değişirse çivi öter ve tavan
    bilinçli olarak yeniden değerlendirilir."""
    tavan = _sd().KISA_CEVAP_ANLAMLI_TAVAN
    assert [_say(c) for c in NIYET_CUMLELERI] == NIYET_SAYIMLARI
    assert [_say(c) for c in UZUN_BRIFINGLER] == UZUN_BRIFING_SAYIMLARI
    assert max(NIYET_SAYIMLARI) < tavan <= min(UZUN_BRIFING_SAYIMLARI), (
        f"tavan {tavan} iki kümenin arasında değil: niyet ≤ {max(NIYET_SAYIMLARI)}, "
        f"uzun brifing ≥ {min(UZUN_BRIFING_SAYIMLARI)}")


def test_K7_OLCULEN_FP_ONEKLERI_ALT_SINIR_KAYDI():
    """ÖLÇÜM KAYDI, kapı değil: ROADMAP'teki dört FP öneği (tam 200 karakterlik alanlar A1'de) ALT
    SINIRLARDIR ve dördü de tavanın ALTINDA kalır — yani bu depodaki metinlerle FP yanı KANITLANAMAZ.
    Gerçek alanların sayımı A1'de aynı fonksiyonla yapılmalıdır (devir kalemi)."""
    tavan = _sd().KISA_CEVAP_ANLAMLI_TAVAN
    assert [_say(c) for c in FP_ONEKLERI] == FP_ONEK_ALT_SINIRLARI
    assert all(s < tavan for s in FP_ONEK_ALT_SINIRLARI), (
        "önek alt sınırı tavanı geçti — bu kayıt ve devir kalemi güncellenmeli")


def test_K7_KALAN_YANLIS_POZITIF_SINIFI_GUVENLI_YONDE():
    """Tavanın DİĞER bedeli, adıyla: tavan altındaki KISA gerçek brifing küçük harfli "sessiz"
    taşıyorsa yine yakın ıska → ham. SOUL'un kendi ilk-satır örneği tek başına bu sınıftadır. Yön
    GÜVENLİDİR (sıralama kaybolur, alarm kaybolmaz)."""
    sd = _sd()
    for metin in (SOUL_ILK_SATIR_ORNEGI, "Sistem sessiz kaldı ama kadans ölçülemedi."):
        assert _say(metin) < sd.KISA_CEVAP_ANLAMLI_TAVAN
        assert sd.jeton_gecer_mi(metin) == (False, True), metin


def test_K7_SOUL_ILK_SATIR_ORNEGI_KUCUK_HARFLI_SESSIZ_TASIR():
    """Kök nedenin istem yarısı (ölçüm kaydı): iki alarm botunun SOUL'u modele küçük harfli "sessiz"
    içeren bir ilk satır ÖRNEĞİ veriyor. SOUL değişirse bu kayıt yeniden okunmalı."""
    for bot in ("bekci", "sef"):
        soul = (KOK / "deploy" / "hermes" / "profiles" / bot / "SOUL.md").read_text(encoding="utf-8")
        assert SOUL_ILK_SATIR_ORNEGI in soul, f"@{bot} SOUL ilk-satır örneği değişti"
