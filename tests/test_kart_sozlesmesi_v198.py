"""v198 · D2-a — KART/HÜCRE SÖZLEŞMESİ (katlanır kart, `.pm-*` dilinin üstüne).

ÖLÇÜLEN KUSUR (docs/BASELINE-2026-08-06.md §3.2, bu turda BAĞIMSIZ olarak yeniden ölçüldü):
kart sayısı beş alan sayfasının HİÇBİRİNDE bir bütçe değil. Ölçülen asimetri Öğrenme 39 kart /
Gözetim 3 — on üç kat. Bütçesi olan iki yüzey (`GENEL_KARTLARI` 6, `DURUM_KARTLARI` 4) o bütçeyi
LİSTE-VERİ olarak tuttuğu için tutuyor; alan sayfalarında böyle bir liste yoktu, dolayısıyla
sayılamıyordu da.

SIRA KASITLI: sözleşme yeni bilgi mimarisinden ÖNCE gelir (docs/TASARIM-YONU-2026-08-07.md dalga 2,
UX denetimi §7 karşı-argümanı). Sözleşmesiz bir sayfa birleşmesi, yoğun iki sayfayı tek sütuna
dizip yükü ikiye katlardı.

BU DOSYA NEYİ ÇİVİLER
---------------------
1. ÜÇ KAPI — kapalı özet "içeride önemli bir şey var mı?"yı cevaplamak ZORUNDA (denetim §5.1).
   Kapıdan geçemeyen özet BOŞ döner ve kart KATLANMAZ. Node'da davranış olarak ölçülür.
2. COLLAPSE KURALLARI — varsayılan kapalı · dikkat açık · accordion DEĞİL · tek global kontrol ·
   sessionStorage (localStorage değil) · ANOMALİ HAFIZAYI EZER · klavye/aria.
3. KART BÜTÇESİ — her alan sayfası için YAZILI tavan + ölçülmüş toplamın ratchet'i.
4. TEK TANIM — ikinci bir kart/hücre dili doğmuyor; özet `hucreGovde` çıktısı.
5. PAYDA BEYANI — paydasız çubuk çizilmez (v192'nin kuralı özette de geçerli).

TESTLER KAYNAĞA BAKAR (repo deseni: test_pano_turu_v139, test_pano_durum_kartlari_v191): kusur da
orada yaşıyor. Saf fonksiyonların DAVRANIŞI ayrıca Node'da koşturulur (test_acil_dogruluk_v196
deseni) — bir kapı kuralı yalnız kaynakta "yazıyor" diye tutmuş sayılmaz.
"""
from __future__ import annotations

import json
import pathlib
import re
import shutil
import subprocess

import pytest

SRC = pathlib.Path(__file__).resolve().parents[1]
WEB = SRC / "meridian" / "web"
APPJS = (WEB / "app.js").read_text()
INDEX = (WEB / "index.html").read_text()

NODE = shutil.which("node")

# Yorumsuz gövde (v139/v155/v160/v191/v196 deseni): bu turun her kuralı kendi gerekçesini kaynakta
# yazıyor ve o gerekçe bir BİLDİRİM sanılmamalı — yoksa doğru davranan kod kendi belgesi yüzünden
# hem düşer hem geçer.
KOD = "\n".join(l for l in APPJS.splitlines() if not l.lstrip().startswith("//"))
CSS = INDEX[INDEX.index("<style>"):INDEX.index("</style>")]
CSS_KOD = re.sub(r"/\*.*?\*/", "", CSS, flags=re.S)

# Ölçüm betiği testin yanında değil `research/olcumler/` altında yaşar (ölçüm ≠ hüküm); test onu
# ithal eder ki ATIF ALGORİTMASI tek yerde tanımlı olsun. İki kopya olsaydı biri güncellenir,
# diğeri sessizce bayatlardı — tam olarak bu turun kapattığı sınıf.
_OLCUM = SRC / "research" / "olcumler" / "kart_sozlesmesi_2026-08-07" / "say_kart.py"


def _olcum_modulu():
    import importlib.util
    spec = importlib.util.spec_from_file_location("_kart_olcum", _OLCUM)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---- ÖLÇÜLMÜŞ TABAN (RATCHET) -----------------------------------------------------------------
# 2026-08-07'de ölçüldü (`research/olcumler/kart_sozlesmesi_2026-08-07/say_kart.py`). Yöntem
# baseline'ın devraldığı üç sayıyı bağımsız olarak yeniden üretiyor: Öğrenme 39, Gözetim 3,
# Kilitler 5. Bu tablo bir HEDEF değil bir FOTOĞRAFtır: sessizce kart eklenmesin diye çivilidir.
# Değiştirmek serbesttir — ama BEYANLI, yani bu satırı düzenleyerek.
# D2-b'DE BEYANLI GÜNCELLENDİ (2026-08-07). Yüzeyler birleşti ve tek yeni bölüm eklendi:
#   karar  = kosu 4 + portfoy 17            = 21  (kart TAŞINDI, doğmadı)
#   saglik = veri 9 + gozetim 3 + cizelge 2 = 14  (+2: canlı zaman çizelgesi — `workflow.html`in
#            halefi; iki emisyon, biri teşhis ucu okunamadığındaki DÜRÜST BOŞLUK dalı)
#   ogrenme 39 · kilitler 5 (değişmedi)
# RATCHET KORUNUYOR: taşınan kart sayılmaz, DOĞAN kart bu satırda gerekçesiyle beyan edilir.
# D3-UI'DA BEYANLI GÜNCELLENDİ (2026-08-07) — C1'in on işi on YENİ kart doğurdu ve ONU (yalnız onu)
# bu satır kaydeder. Ratchet'in istediği tam olarak bu: sessizce eklenmesin, BEYANLA eklensin.
#   karar   21 → 26  (+5: retkarne · eylemsizlik · emiryasam · cikis · denetim)
#   saglik  14 → 15  (+1: cizelge:damga — mekanizma nabız damgaları uca açıldı)
#   ogrenme 39 → 43  (+4: maliyet · rollback · regresyon · olgunlasma)
#   kilitler 5 →  5  (değişmedi — ⑤'e iş düşmedi)
# ONUNUN DA KAPAĞI VAR: bütçesi zaten aşılmış üç yüzeye kapaksız kart eklemek "ilk bakışta düşen
# yük"ü on kart büyütmek olurdu. Kapak sayıları `KAPAK_TABANI`nın TABANINI aşıyor (test `>=`);
# yeni kapakların kendisi `tests/test_firsat_yuzeyleri_v200.py`de tek tek çivilendi.
# v211'DE BEYANLI GÜNCELLENDİ (2026-08-07) — TEK yeni kart, gerekçesi risk:
#   karar   26 → 27  (+1: mutabakat:koruma — çıplak motor pozisyonlarına OCO önerisi + onay kapısı)
# NEDEN DOĞDU: canlı ölçümde dört motor pozisyonu broker'da korumasızdı ve panoda "korumayı yeniden
# kur" diye bir yüzey YOKTU (oku · gir · düzleştir vardı). Kart mutabakat masasına girdi, çünkü
# taşıdığı asıl bulgu bir mutabakat bulgusudur: iç defter 33/43/64/54 der, broker 22/22/37/25 der
# ve emir BROKER adedini kullanır. Kapak altındadır ama GİZLENEMEZ: çıplak pozisyon varken özet
# rozet taşır, rozet `data-dikkat` doğurur ve kurucu oturum hafızasını EZEREK kartı açar.
# v219'DA BEYANLI GÜNCELLENDİ (2026-08-09, dalga W4 · 93ae96a) — TEK yeni kart:
#   ogrenme 43 → 44  (+1: hermes:telemetri — `agent_calls` defterinin İLK pano okuyucusu;
#                     hermes.py:2503'ün "veri hazır, çizim henüz yok" beyanını KAPATIR)
# Kapak altında: `KAPAK_TABANI` ogrenme 18 → ÖLÇÜLEN 23, taban KORUNUYOR.
# v229'DA BEYANLI GÜNCELLENDİ (2026-08-09, dalga W-UX D3-b) — ÜÇ yeni FIRSAT kartı (docs/TASARIM-
# YONU-2026-08-07 §7'nin F1/F2/F14'ü); hepsi kapak altında, üçü de "üretiliyor ama görünmüyor"
# kovasından bir kalem kapatır ve UÇTAN okur (uydurma rakam yasağı):
#   saglik  15 → 17  (+2: veriboru:kagitcanli [F1 · kâğıt-canlı ayrışması, /api/public/summary'nin
#                     ledgerstamp ayrımının İLK pano okuyucusu] · operasyon:esik [F14 · iki kademeli
#                     eşik + NO_DATA, `esikHal`in canlı vitrini])
#   ogrenme 44 → 45  (+1: bilesenic:sapma [F2 · canlı-backtest sapmasının kökü — E2 defterinin
#                     limit-bacağı ölçümü + iç-motor totoloji-beyanı])
#   karar 27 · kilitler 5 (değişmedi — bu üç yüzey ③/④'e düştü)
# Kapak altında: `KAPAK_TABANI` saglik 4→ÖLÇÜLEN 7, ogrenme 18→ÖLÇÜLEN 24 — tabanlar KORUNUYOR.
# v230'DA BEYANLI GÜNCELLENDİ (2026-08-09, dalga W-UX D3-b devamı) — TEK yeni FIRSAT kartı (docs/
# TASARIM-YONU-2026-08-07 §7'nin F5'i); kapak altında, "üretiliyor ama görünmüyor" kovasından bir
# kalem kapatır ve UÇTAN okur (uydurma rakam yasağı):
#   saglik  17 → 18  (+1: operasyon:alarmkok [F5 · yinelenen arıza taksonomisi — `watchdog.alarm_gunluk`ın
#                     İLK pano okuyucusu; v192 sayacı UCA çıkıyordu ama `test_bastirma_sayaci_PANOYA_cikar`
#                     "dış okuyucusu api.py'dir" der → pano çizmiyordu, YASA 6 boşluğu])
#   karar 27 · ogrenme 45 · kilitler 5 (değişmedi — F5 ③'e düştü)
# Kapak altında: `KAPAK_TABANI` saglik ÖLÇÜLEN 7→8, taban 4 KORUNUYOR (`>=`).
KART_TABANI = {"karar": 27, "saglik": 18, "ogrenme": 45, "kilitler": 5}
# Bu turda kapağa geçirilen kart sayısı — UX denetimi §5.3'ün 2/3/4 numaralı öncelikleri.
# Öncelik 1 (Bölüm 5'i beşe bölmek) bir İÇERİK kararıdır ve D2-b'ye bırakıldı; bu tur sözleşmeyi
# kurar, kart bölmez. Sayı bir TABAN: düşerse (kapak sökülürse) test kırmızıya döner.
# D2-b: yüzeyler birleşti — taban da BİRLEŞTİ, düşmedi (veri 4 + gozetim 0 → saglik 4;
# kosu 0 + portfoy 3 → karar 3; ogrenme 18 aynen). Kapaklı kart sayısı bir SÖZLEŞME TABANIDIR:
# bir kartın kapağı sökülürse bu satır düşer.
# v219 ÖLÇÜMÜ (2026-08-09) — DÖRT ALANIN DA KAPAK SAYISI ÖLÇÜLDÜ, taban DEĞİŞMEDİ:
#   karar 9 (taban 3) · saglik 5 (taban 4) · ogrenme 23 (taban 18) · kilitler 0 (taban 0).
# TABAN NEDEN YÜKSELTİLMİYOR: bu satırın işi "kapak sökülmesin"dir, "kapak sayısı artsın" değil.
# Ölçüleni tabana çekmek, kapaklı bir kartın MEŞRU şekilde açılmasını (bir kart dikkat ister hâle
# gelirse yüzeye çıkar) sessizce yasaklardı — `test_butce_asimi_GIZLENMEZ_beyan_edilir`in
# korumaya çalıştığı şeyin tam tersi. Ölçüm buraya KAYIT olarak yazılır: taban ile gerçek
# arasındaki açıklık artık görünür ve bir sonraki tur "18 hâlâ anlamlı bir taban mı" diye
# sorabilir — sayı, sorulmamış bir soru olarak kalmaz.
KAPAK_TABANI = {"saglik": 4, "karar": 3, "ogrenme": 18, "kilitler": 0}


# ==============================================================================================
# 1 · ÜÇ KAPI — kapalı özetin sözleşmesi (davranış, Node)
# ==============================================================================================
def _fn(ad: str, kaynak: str = APPJS) -> str:
    """Fonksiyon dilimi. İki biçim: `function ad(` (sütun-0 `}`ye kadar) ve tek satırlık
    `const ad = …` (ok fonksiyonu — `esc` bu biçimde)."""
    if f"function {ad}(" in kaynak:
        i = kaynak.index(f"function {ad}(")
        parcalar = []
        for ln in kaynak[i:].splitlines(keepends=True):
            parcalar.append(ln)
            if ln.rstrip("\n") == "}":
                break
        return "".join(parcalar)
    i = kaynak.index(f"const {ad} = ")
    return kaynak[i:kaynak.index("\n", i) + 1]


_HARNESS = """
%(esc)s
%(cubuk)s
%(govde)s
%(ozet)s
const KANIT_TAVAN_N = 61;
const kanitOrani = n => (!n || !Number.isFinite(Number(n))) ? null
  : Math.min(1, Math.log10(Number(n) + 1) / Math.log10(KANIT_TAVAN_N));
const vakalar = %(vakalar)s;
const out = {};
for (const [ad, o] of Object.entries(vakalar)) out[ad] = kartOzeti(o);
process.stdout.write(JSON.stringify(out));
"""

# Her vaka bir KAPIyı sınar. "gecer_*" geçmeli, "duser_*" düşmeli (boş dizgi).
_VAKALAR = {
    # KAPI 1+3b — değer var, meta sayı taşıyor
    "gecer_tam":        {"deger": "7 → 4", "oran": 0.57, "payda": "uygulanabilir desen (7)",
                         "meta": "3 desen düşüyor · 1 dedektör ölçemedi"},
    # KAPI 1 — değer YOK ama gerekçe var (≥20 karakter)
    "gecer_verisiz":    {"deger": None, "rozet": "ÖLÇÜLEMEDİ",
                         "meta": "uç bu alanı hiç vermedi — ölçülemedi (sıfır DEĞİL)."},
    # KAPI 2 — oran var, payda YOK → çubuk paydasız olurdu; ÖZET DÜŞER
    "duser_paydasiz":   {"deger": "12", "oran": 0.4, "meta": "24 satır ölçüldü"},
    # KAPI 3 — değer var ama metada SAYI yok
    "duser_sayisiz":    {"deger": "12", "meta": "bir şeyler oldu"},
    # KAPI 3a — iki satırdan fazla meta
    "duser_ucsatir":    {"deger": "12", "meta": "1 a<br>2 b<br>3 c"},
    # KAPI 1 — değer de yok, gerekçe de yok
    "duser_bos":        {},
    # KAPI 1 — değer yok, gerekçe ÇOK KISA (bir gerekçe sayılmaz)
    "duser_kisa_neden": {"deger": None, "meta": "yok"},
    # DİKKAT — rozet varsa özet dikkat işareti taşır
    "dikkat_rozet":     {"deger": "3", "rozet": "3 İHLAL", "meta": "7 desenden 3'ü düşüyor"},
    # DİKKAT — `warn` ŞİDDET kanalıdır, dikkat doğurur
    "dikkat_warn":      {"deger": "3", "degerSinif": "warn", "meta": "7 desenden 3'ü düşüyor"},
    # DİKKAT DEĞİL — `neg` YÖN kanalıdır (K/Z işareti); negatif bir sayı sapma değildir
    "dikkatsiz_neg":    {"deger": "-0,2R", "degerSinif": "neg", "meta": "18 işlem ölçüldü"},
    # SIFIR BİR ÖLÇÜMDÜR: 0 değeri "veri yok" dalına DÜŞMEZ
    "gecer_sifir":      {"deger": 0, "meta": "0 ders yazılmış · 12 satır okundu"},
}


@pytest.fixture(scope="module")
def ozet_ciktilari():
    if NODE is None:
        pytest.skip("node yok")
    betik = _HARNESS % {
        "esc": _fn("esc"), "cubuk": _fn("hucreCubuk"),
        "govde": _fn("hucreGovde"), "ozet": _fn("kartOzeti"),
        "vakalar": json.dumps(_VAKALAR, ensure_ascii=False),
    }
    p = subprocess.run([NODE, "-e", betik], capture_output=True, text=True, timeout=60)
    assert p.returncode == 0, f"kartOzeti dilimi Node'da patladı:\n{p.stderr}"
    return json.loads(p.stdout)


@pytest.mark.parametrize("ad", [k for k in _VAKALAR if k.startswith("gecer_")])
def test_kapilardan_gecen_ozet_URETILIR(ozet_ciktilari, ad):
    """Üç kapıyı geçen özet `.kk-ozet` üretir — kart katlanabilir hâle gelir."""
    assert 'class="kk-ozet"' in ozet_ciktilari[ad], f"{ad}: özet üretilmedi — {ozet_ciktilari[ad]!r}"


@pytest.mark.parametrize("ad", [k for k in _VAKALAR if k.startswith("duser_")])
def test_kapidan_dusen_ozet_BOS_DONER(ozet_ciktilari, ad):
    """SÖZLEŞMENİN ÇİVİSİ: özet üretilemeyen kart COLLAPSE ALMAZ. Boş özetli bir kapak yükü
    azaltmaz, TIK ARTIRIR — denetim §5.1'in tam cümlesi."""
    assert ozet_ciktilari[ad] == "", f"{ad}: kapıdan geçmemeliydi — {ozet_ciktilari[ad]!r}"


def test_paydasiz_CUBUK_cizilmez(ozet_ciktilari):
    """v192'nin kuralı özette de geçerli: payda beyanlı değilse çubuk hiç doğmaz. Burada bir adım
    daha ileri gidilir — paydasız oran ÖZETİN kendisini düşürür (yarım kanıtla soru cevaplanmaz)."""
    assert ozet_ciktilari["duser_paydasiz"] == ""
    tam = ozet_ciktilari["gecer_tam"]
    assert 'class="pm-conf"' in tam and 'data-payda="uygulanabilir desen (7)"' in tam, \
        f"payda beyanı çubuğa girmemiş: {tam!r}"


def test_sifir_bir_OLCUMDUR_veri_yok_dalina_dusmez(ozet_ciktilari):
    """`0` ölçülmüş bir sayıdır; "veri yok" ölçülememiş olmaktır. Aynı piksele düşemezler."""
    assert "pm-none" not in ozet_ciktilari["gecer_sifir"], "0 değeri 'veri yok' dalına düşmüş"
    assert "pm-none" in ozet_ciktilari["gecer_verisiz"], "ölçülemeyen değer boş hücre dalına düşmemiş"


def test_dikkat_isareti_ROZET_ve_SIDDETten_turer_yonden_DEGIL(ozet_ciktilari):
    """Dikkat = rozet (ölçülemeyen/sapan hâl) ya da `warn` (ŞİDDET rolü). `neg` YÖN rolüdür —
    negatif bir sayıyı dikkat saymak kapağı fiilen kaldırırdı (her gün bir kart negatiftir)."""
    assert 'data-dikkat="1"' in ozet_ciktilari["dikkat_rozet"]
    assert 'data-dikkat="1"' in ozet_ciktilari["dikkat_warn"]
    assert 'data-dikkat="1"' not in ozet_ciktilari["dikkatsiz_neg"], \
        "YÖN rolü (neg) dikkat doğuruyor — beş renk rolü karışmış (D1)"


# ==============================================================================================
# 2 · COLLAPSE KURALLARI (kaynak sözleşmesi)
# ==============================================================================================
def test_ozetsiz_kart_KAPAK_ALMAZ_kurucuda():
    """Kurucu, `.kk-ozet` bulamadığı kartı `data-kat="hayir"` işaretler ve kapak kurmaz."""
    kur = KOD[KOD.index("function katKurulumu("):KOD.index("function _katKontrolCiz(")]
    assert 'if (!ozet)' in kur and 'kat = "hayir"' in kur, \
        "özetsiz kart için kapak-yok dalı yok — sözleşmenin çivisi düşmüş"
    assert "ozetsiz.push" in kur, "özet üretemeyen kart SAYILMIYOR — bulgu sessizce yutuluyor (YASA 4)"
    assert "console.warn" in kur or "console.error" in kur, \
        "özetsiz kart bulgusu konsola düşmüyor — YASA 4 (sessiz yutma yasağı)"


def test_varsayilan_KAPALI_ve_ilk_bolum_ACIK():
    kur = KOD[KOD.index("function katKurulumu("):KOD.index("function _katKontrolCiz(")]
    assert "ilkBolum" in kur and "ALAN_BOLUMLERI" in kur, \
        "sayfanın 1. bölümü kuralı uygulanmıyor (ALAN_BOLUMLERI okunmuyor)"
    assert re.search(r"acik\s*=\s*hatirlanan\s*==\s*null\s*\?\s*\(kayit\.bolum === ilkBolum\)", kur), \
        "varsayılan KAPALI + 1. bölüm AÇIK hükmü tek satırda kurulmuyor"


def test_dikkat_ACIK_baslar_ve_HAFIZAYI_EZER():
    """Oturum hafızası bir alarmı gizleyebilseydi bu sözleşme bir güvenlik açığı olurdu."""
    kur = KOD[KOD.index("function katKurulumu("):KOD.index("function _katKontrolCiz(")]
    assert re.search(r"if \(dikkat && !acik\) \{ acik = true;", kur), \
        "dikkat, hatırlanan 'kapalı' hâli EZMİYOR"
    assert "kapalı hatırlanmıştı — sapma geldiği için açıldı" in APPJS, \
        "hafızanın ezildiği ekranda BEYAN edilmiyor (denetim §5.2'nin tam cümlesi)"


def test_accordion_DEGIL_kartlar_bagimsiz():
    """Birini açmak diğerini kapatmaz. Kapak eylemi YALNIZ kendi kartına dokunur."""
    kapak = KOD[KOD.index("function katKapak("):KOD.index("function katKurulumu(")]
    # Tek kartın dışına çıkan bir sorgu (querySelectorAll) accordion'un imzasıdır.
    assert "querySelectorAll" not in kapak, \
        "katKapak başka kartlara dokunuyor — accordion davranışı sızmış"
    # Global kontrol AYRI bir yoldur ve iki AÇIK komutu vardır (aç / kapat) — accordion değil.
    assert 'data-kk-hepsi="ac"' in APPJS and 'data-kk-hepsi="kapat"' in APPJS


def test_sayfa_basina_TEK_global_kontrol():
    ciz = KOD[KOD.index("function _katKontrolCiz("):KOD.index("function _katKontrolTazele(")]
    assert 'querySelector(".alan-bas")' in ciz, "global kontrol `.alan-bas` içine girmiyor"
    assert 'querySelector(".kk-kontrol")' in ciz and ".remove()" in ciz, \
        "kontrol yeniden çizimde çoğalıyor — sayfa başına TEK kontrol kuralı yok"
    assert "if (!_KAT_KATLANIR) return;" in ciz, \
        "katlanır kart yokken de kontrol çiziliyor — hiçbir şeyi açmayan bir düğme ekranda yalandır"
    # `.kk-kontrol` ve `.kk-hepsi` YALNIZ burada doğar (tek çıkış).
    assert KOD.count('kap.className = "kk-kontrol"') == 1, "global kontrol ikinci bir yerde de üretiliyor"


def test_oturum_hafizasi_sessionStorage_localStorage_DEGIL():
    """Geçen haftanın açık kartı bu sabahın bakışını yönetmemeli (denetim §5.2)."""
    hafiza = KOD[KOD.index("const _katAnahtar ="):KOD.index("function _katDurumYaz(")]
    assert "sessionStorage" in hafiza, "oturum hafızası sessionStorage kullanmıyor"
    assert "localStorage" not in hafiza, "kapak hâli localStorage'a yazılıyor — oturumlar arası sızıntı"
    assert '`mrd-kart:${alan}:${kart}`' in APPJS, "hafıza anahtarı sözleşmedeki biçimde değil"
    # Depolama erişimi try/catch'li: özel kipte bir kapak yüzünden sayfa çizilmemeli.
    assert hafiza.count("catch") >= 2, "sessionStorage erişimi korumasız — özel kipte sayfa düşer"


def test_klavye_ve_aria_sozlesmesi():
    kur = KOD[KOD.index("function katKurulumu("):KOD.index("function _katKontrolCiz(")]
    assert 'createElement("button")' in kur and 'dugme.type = "button"' in kur, \
        "başlık kontrolü <button> değil — Tab/Enter/Space yerli sözleşmesi kaybolur"
    assert 'setAttribute("aria-controls"' in kur, "aria-controls kurulmuyor"
    assert 'govde.setAttribute("role", "region")' in kur, "gövde bir region değil"
    assert 'govde.setAttribute("aria-labelledby", dugme.id)' in kur, \
        "region adsız — adsız bir landmark ekran okuyucuda duyurulmaz"
    durum = KOD[KOD.index("function _katDurumYaz("):KOD.index("function katKapak(")]
    assert 'aria-expanded' in durum and "govde.hidden" in durum, \
        "aria-expanded ile görünürlük BİRLİKTE değişmiyor — gören ve duyan operatör ayrışır"
    assert ":focus-visible" in CSS_KOD[CSS_KOD.index(".kk-dugme"):CSS_KOD.index(".kk-ad")], \
        ".kk-dugme odak halkası yok — klavye turu görünmez olur"


def test_baslik_metni_TASINIR_kopyalanmaz():
    """Kart başlıklarının bir kısmı çip/alt-etiket taşıyor; metni yeniden yazmak onları düşürürdü."""
    kur = KOD[KOD.index("function katKurulumu("):KOD.index("function _katKontrolCiz(")]
    assert "while (bas.firstChild) ad.appendChild(bas.firstChild);" in kur, \
        "başlık düğümleri taşınmıyor (metin yeniden yazılıyor olabilir)"
    assert 'ozet.querySelector(".pm-thin")' in kur and "dugme.appendChild(rozet)" in kur, \
        "durum rozeti başlığa taşınmıyor — kapalı kartta sapma görünmez"


def test_hareket_200ms_alti_ve_reduced_motion_guardli():
    """`--t` jetonu ≤200ms olmalı ve global `prefers-reduced-motion` sıfırlaması yerinde durmalı."""
    m = re.search(r"--t:\s*([\d.]+)(m?s)", CSS_KOD)
    assert m, "--t geçiş jetonu bulunamadı"
    sure = float(m.group(1)) * (1000 if m.group(2) == "s" else 1)
    assert sure <= 200, f"geçiş süresi {sure}ms — sözleşme ≤200ms"
    assert re.search(r"@media\(prefers-reduced-motion:reduce\)\{\s*\*\{transition:none!important",
                     CSS_KOD.replace("\n", "")), \
        "global prefers-reduced-motion sıfırlaması yok — kapak animasyonu guard'sız kalır"


def test_CSP_satir_ici_olay_ozniteligi_YOK():
    """Kapak mekanizması tek delege dinleyicide; satır içi `onclick` CSP'de ölü düğme demektir."""
    kk = KOD[KOD.index("function katKart("):KOD.index("const DURUM_SAYFALARI")]
    assert not re.search(r"\son[a-z]+=\"", kk), "kapak bloğunda satır içi olay özniteliği var (CSP)"
    assert 'e.target.closest(".kk-dugme")' in KOD, "kapak tıklaması delege dinleyicide değil"


# ==============================================================================================
# 3 · KART BÜTÇESİ
# ==============================================================================================
def _butce():
    blok = KOD[KOD.index("const KART_BUTCESI = {"):]
    blok = blok[:blok.index("};") + 2]
    return {m.group(1): int(m.group(2)) for m in re.finditer(r"(\w+):\s*(\d+)", blok)}


def _alan_bolumleri():
    blok = KOD[KOD.index("const ALAN_BOLUMLERI = {"):]
    blok = blok[:blok.index("};") + 2]
    return {m.group(1): re.findall(r'"(\w+)"', m.group(2))
            for m in re.finditer(r"(\w+):\s*\[([^\]]*)\]", blok)}


def test_her_alan_sayfasinin_YAZILI_butcesi_var():
    """Denetim §6: kart sayısını bir tasarım bütçesi yapan tek mekanizma LİSTE-VERİdir ve beş alan
    sayfasına da yayılmalıdır. Bugüne dek yalnız Genel Bakış (6) ve durum ızgarası (4) sayılabiliyordu."""
    butce, alanlar = _butce(), _alan_bolumleri()
    assert set(butce) == set(alanlar), \
        f"bütçesiz alan sayfası var: {sorted(set(alanlar) - set(butce))} · fazla: {sorted(set(butce) - set(alanlar))}"
    for alan, v in butce.items():
        assert v >= 1, f"{alan}: bütçe {v} — anlamsız tavan"


def test_olculen_kart_toplami_TABANLA_ayni():
    """RATCHET: sessizce kart eklenemez. Sayı değişecekse bu dosyadaki `KART_TABANI` BEYANLI olarak
    düzenlenir — ölçüm betiği (`research/olcumler/.../say_kart.py`) ile aynı algoritmayı kullanır."""
    sonuc, _kayit, _kullanim = _olcum_modulu().olc(APPJS)
    olculen = {alan: v["toplam"] for alan, v in sonuc.items()}
    assert olculen == KART_TABANI, (
        f"kart sayımı tabandan ayrıştı — ölçülen {olculen}, taban {KART_TABANI}. "
        "Kart eklendiyse tabanı BEYANLI güncelle; silindiyse gerekçesi D2-b kaydına yazılmalı.")


def test_kapaga_gecen_kart_sayisi_TABANIN_ALTINA_dusmez():
    sonuc, _kayit, _kullanim = _olcum_modulu().olc(APPJS)
    for alan, taban in KAPAK_TABANI.items():
        kapakli = sonuc[alan]["kapakli"]
        assert kapakli >= taban, \
            f"{alan}: kapaklı kart {kapakli} < taban {taban} — bir kartın kapağı sökülmüş"


def test_butce_asimi_GIZLENMEZ_beyan_edilir():
    """Tavan aşıldığında kart zorla kapatılmaz — dikkat isteyen bir kartı bütçe uğruna kapatmak
    bu sözleşmeyi bir güvenlik açığına çevirirdi. Aşım SAYIYLA yazılır."""
    tazele = KOD[KOD.index("function _katKontrolTazele("):KOD.index("document.addEventListener(\"click\", e => {\n  const hepsi")]
    assert "KART_BUTCESI[" in tazele, "bütçe okunmuyor"
    assert "aşıldı" in tazele, "bütçe aşımı beyan edilmiyor"
    assert "_katDurumYaz" not in tazele, "bütçe aşımında kart zorla kapatılıyor — alarm gizlenebilir"
    assert "ÖLÇÜLEMEDİ" in tazele, "bütçesi yazılmamış sayfa için ölçülemedi dalı yok (uydurma yasağı)"


def test_butce_asimi_SIDDET_RENGI_tasimaz():
    """Renk yalnız anomalide (D1'in beş rolü). Bir tasarım borcu anomali değildir."""
    blok = CSS_KOD[CSS_KOD.index(".kk-kontrol"):]
    blok = blok[:blok.index(".kk-butce") + 200]
    assert "--sev-" not in blok, "bütçe kontrolü şiddet jetonu okuyor — rol sızıntısı"
    assert "mut" in KOD[KOD.index("function _katKontrolCiz("):KOD.index("function _katKontrolTazele(")], \
        "bütçe beyanı sönük (.mut) kanalda değil"


# ==============================================================================================
# 4 · TEK TANIM — ikinci bir kart/hücre dili doğmuyor
# ==============================================================================================
def test_kapali_ozet_HUCRE_GOVDESIDIR_ikinci_sayi_dili_yok():
    ozet = KOD[KOD.index("function kartOzeti("):KOD.index("const _katAnahtar =")]
    assert "hucreGovde(o)" in ozet, "özet `hucreGovde` çıktısı değil — ikinci bir hücre dili doğmuş"
    # `.kk-*` sınıfları YALNIZ kapağın kendisini taşır: sayı/oran/meta biçimi tanımlamazlar.
    kk_css = CSS_KOD[CSS_KOD.index(".kat-kart > .t"):CSS_KOD.index(".kk-butce") + 120]
    for yasak in ("font-variant-numeric", "tabular-nums"):
        assert yasak not in kk_css, f".kk-* bloğunda `{yasak}` var — ikinci bir sayı dili kuruluyor"


def test_katKart_ve_kartOzeti_TEK_CIKIS():
    """`data-kart` özniteliği ve `.kk-ozet` hücresi YALNIZ bu iki fonksiyondan doğar; ikinci bir
    üretici, 'kart başına tek sözleşme' kuralını sayılamaz bir vaade çevirirdi (gbKart deseni)."""
    assert KOD.count('` data-kart="') == 1, "data-kart ikinci bir yerde de üretiliyor"
    assert KOD.count('<span class="kk-ozet"') == 1, ".kk-ozet ikinci bir yerde de üretiliyor"
    assert KOD.count('govde.className = "kk-govde"') == 1, ".kk-govde ikinci bir yerde de üretiliyor"


def test_kayit_defteri_ile_kaynak_AYRISMAZ():
    """Kayıtsız anahtar sessizce düşer (kart kapak almaz) — bu bir hata sınıfıdır, ölçülmeli.
    Ölü kayıt da öyle: kullanılmayan bir anahtar, sonra aranacak bir hayalet bırakır."""
    _sonuc, kayit, kullanim = _olcum_modulu().olc(APPJS)
    assert not (set(kullanim) - set(kayit)), \
        f"kayıtsız anahtar kullanılıyor (kapak almaz): {sorted(set(kullanim) - set(kayit))}"
    assert not (set(kayit) - set(kullanim)), \
        f"kayıtlı ama kullanılmayan anahtar (ölü kayıt): {sorted(set(kayit) - set(kullanim))}"


def test_kayit_defterindeki_bolum_ALAN_BOLUMLERI_ile_uyumlu():
    """`bolum` alanı zorunlu ve gerçek: 'sayfanın 1. bölümü açık başlar' kuralı ancak bölüm adı
    doğruysa uygulanabilir. Yanlış bölüm adı, kuralı SESSİZCE devre dışı bırakırdı."""
    blok = KOD[KOD.index("const KART_KAYDI = {"):]
    blok = blok[:blok.index("};") + 2]
    kayitlar = re.findall(r'"([\w:]+)":\s*\{\s*alan:\s*"(\w+)",\s*bolum:\s*"(\w+)"', blok)
    assert kayitlar, "kayıt defteri okunamadı"
    alanlar = _alan_bolumleri()
    for anahtar, alan, bolum in kayitlar:
        assert alan in alanlar, f"{anahtar}: bilinmeyen alan sayfası {alan!r}"
        assert bolum in alanlar[alan], f"{anahtar}: {bolum!r} bölümü {alan!r} sayfasında yok"


def test_kurucu_alanSayfasinin_SON_adimi():
    """Bütçe SAYFANIN — bölüm bölüm kurmak, sayfanın bütçesini bölüm bölüm saymak olurdu."""
    kalip = KOD[KOD.index("function alanSayfasi("):KOD.index("function satirKoru(")]
    assert "katKurulumu(kap, id);" in kalip, "kart sözleşmesi sayfa çiziminde kurulmuyor"
    assert kalip.index("_bolumBasliklariniIndir(kap);") < kalip.index("katKurulumu(kap, id);"), \
        "kurucu başlık mertebesi düzeltmesinden ÖNCE koşuyor — h2 taşıması yarım kalır"


def test_kurucu_iki_kez_kosunca_BOZULMAZ():
    """Bölüm bazlı yeniden çizimler kurucuyu tekrar tetikler; kurulmuş kart yeniden sarılmamalı."""
    kur = KOD[KOD.index("function katKurulumu("):KOD.index("function _katKontrolCiz(")]
    assert 'kart.dataset.katKuruldu === "1"' in kur, "yeniden kurulum koruması yok"


# ==============================================================================================
# 5 · YOĞUN-UZMAN MUAFİYETİ (denetim §5.2) — yoğun düzen cezalandırılmaz
# ==============================================================================================
def test_data_kat_hayir_muafiyeti_kurucuda_okunuyor():
    kur = KOD[KOD.index("function katKurulumu("):KOD.index("function _katKontrolCiz(")]
    assert 'kart.dataset.kat === "hayir"' in kur, \
        "yoğun-uzman muafiyeti (data-kat=hayir) okunmuyor — tablolar zorla katlanır"


# ==============================================================================================
# 6 · GÖÇ ETMİŞ KARTLARIN ÖZETİ DÜRÜST (uydurma yasağı, kaynak taraması)
# ==============================================================================================
def test_gocen_kartlarda_ozet_UYDURMA_SIFIR_uretmiyor():
    """Özet çağrılarında `?? 0` ile DOM'a yazılan bir DEĞER olmamalı: 'ölçemedik' ile 'ölçtük, sıfır
    çıktı' aynı piksele düşemez. (Sayaç/uzunluk gibi aritmetik kullanımlar kapsam dışı — bunlar
    `meta` içinde ve gerçekten sayımdır.)"""
    for m in re.finditer(r"kartOzeti\(", KOD):
        # Çağrının `deger:` alanını al — parantez dengesi yerine ilk `deger:` … `,` dilimi yeterli.
        dilim = KOD[m.end():m.end() + 600]
        d = re.search(r"deger:\s*([^\n]*)", dilim)
        if not d:
            continue
        assert not re.search(r"\?\?\s*0(?![\d.])", d.group(1)), \
            f"özet DEĞERİ `?? 0` ile sıfıra çöküyor: {d.group(1).strip()!r}"


def test_olculemedi_dalinda_ROZET_ve_NEDEN_birlikte():
    """`deger: null` yazan her özet ya bir rozet ya da ≥20 karakterlik bir gerekçe taşımak zorunda —
    kapı 1'in kaynak tarafındaki karşılığı. (Kapının kendisi Node testinde ölçülüyor.)"""
    eksik = []
    for m in re.finditer(r"kartOzeti\(", KOD):
        dilim = KOD[m.end():m.end() + 900]
        if not re.search(r"deger:\s*null", dilim):
            continue
        blok = dilim[:dilim.find("})") + 2] or dilim
        if "meta:" not in blok:
            eksik.append(blok[:90])
    assert not eksik, f"ölçülemedi dalında gerekçesiz özet: {eksik}"
