"""v512 · teşhis penceresi BİR İŞ GÜNÜDÜR, ve "pencere dışında" ile "kayıt yok" AYRI cümledir —
TSK-199, 2026-09-16.

NUMARA REZERVE EDİLDİ (Rol-1, 2026-09-16). `ls tests/` bu worktree'de `v512`yi boş gösteriyordu
ama ÖLÇÜM TEK BAŞINA YETMEZ: eşzamanlı worktree'ler birbirinin yeni dosyasını GÖREMEZ ve aynı
numara bugün iki kez çakıştı (v510→v511 taşıması). Numara bu yüzden `ls`ten değil rezervasyondan
gelir.

ÖLÇÜLEN SORUN (Rol-1 ölçümü, karar bu ölçümün üstüne kuruldu). `@sef` durum satırının İKİNCİ
yarısı ("denetçi teşhisi") olay defterinin son N olayına bakıyordu ve N=400'dü. A1 `events.jsonl`
2026-09-16: 20.228.000 bayt / 64.130 satır (~442 bayt/satır); günlük olay sayısı İŞ GÜNÜ ~700
(2026-09-14: 659 · 2026-09-15: 707), hafta sonu 75–105. Yani 400'lük pencere gerçekte ~0,57
GÜNLÜKTÜ: akşam koşan şef, bir ÖNCEKİ akşamın kendi denetim olayını YAPISAL OLARAK göremiyor ve
"kayıt yok" basıyordu — aynı satırda damga bir hüküm gösterirken. İki okuyucu ÇELİŞİYORDU. Hafta
sonu ise aynı pencere 4-5 güne uzuyordu: AYNI KOD GÜNE GÖRE FARKLI SONUÇ veriyordu.

BU DOSYANIN ASIL SÖZLEŞMESİ SABİTİN DEĞERİ DEĞİL, ÇIKTININ AYRIMIDIR (K3/K4): "ÖLÇEMEDİM" ile
"ÖLÇTÜM, YOK" aynı çıktıyla görünemez (uydurma yasağı). Sabiti büyütmek tek başına yetmez —
pencere ne kadar büyük olursa olsun bir gün dolar, ve dolduğu gün eski satır yine YOKLUK iddia
ederdi. Emsal aynı dosyada zaten var: `cevap_bas`ın `None` (ölçemedim) ↔ `""` (ölçtüm, boştu)
ayrımı (TSK-138 dilim-1).

NEDEN AYRI DOSYA, v434/v511'e EKLENMEDİ: v434 teşhis ALANLARININ (model · cevaplayan_model ·
cevap_bas) üretilip okunmasını ölçer, v511 durum satırının HANGİ KOŞUMA ait olduğunu. Bu dosyanın
sorusu üçüncüsü: okuyucu NE KADAR BAKTI ve bakmadığını nasıl söylüyor. Deponun emsali de budur —
v434 tam bu gerekçeyle v385'ten ayrılmıştı.

KAPSAM DIŞI, BİLİNÇLİ: damga şeması (donuk), TSK-198'in eklediği bağlam satırı ve sıralama
yolundaki ham düşüş dalları (TSK-201) bu turda HİÇ değişmedi — çiviler de onlara dokunmaz.

SANDBOX HER ÇİVİDE: bu dosyanın her ölçümü `events.jsonl` yazar/okur. `sandbox_state` olmadan
sentetik 5 MB'lık defterler CANLI `state/`e düşerdi (vaka sınıfı: ajan pytest-dışı state yazımı).
"""
from __future__ import annotations

import importlib
import json
import pathlib
import re

import pytest

from meridian import store
# TEK-KAYNAK: bayt sayan `open` sarmalayıcısı ve TAM OKUMANIN naif referansı v410'da ZATEN var ve
# orada çivilenmiş. Kopyalansaydı, v410'un sözleşmesi değiştiği gün bu dosya ölçtüğünü sandığı
# şeyi ölçmez olurdu.
from tests.test_read_jsonl_kuyruk_v410 import _acma_sarmalayici, _naif_oku

KOK = pathlib.Path(__file__).resolve().parent.parent
URETIM = KOK / "ops" / "sef_brifingi.py"

#: İŞ GÜNÜ OLAY ÖLÇÜMÜ — A1 `state/events.jsonl`, 2026-09-15 (aynı hafta 09-14: 659). Bu sayı
#: burada bir KOPYA DEĞİLDİR: K1 onu ÜRETİM ŞERHİNDE de arar, yani iki taraf ayrışırsa çivi öter.
#: Pencere bundan KÜÇÜKSE bir iş gününü kapsamıyordur ve akşam koşumu dünkü olayı göremez.
IS_GUNU_OLAY = 707

#: Satır boyu ölçümü (aynı defter, 2026-09-16): 20.228.000 bayt / 64.130 satır. K5'in sentetik
#: defteri bu boyu taklit eder — 256 KB'lik yoklama bloğu 900 satır TAŞIMASIN diye.
SATIR_BAYT = 442


@pytest.fixture
def m():
    """Üretim modülü. `_sef_kur` GEREKMEZ: bu dosya profil evine, LLM'e ya da sıralamaya hiç
    dokunmaz — yalnız defter okuyucusunu ve onun ÇIKTI CÜMLESİNİ ölçer."""
    return importlib.import_module("ops.sef_brifingi")


def _sabit_satirli_defter(dizin: pathlib.Path, n: int, satir_bayt: int = SATIR_BAYT,
                          ad: str = "events.jsonl") -> pathlib.Path:
    """SABİT satır uzunluklu sentetik defter (yalnız ASCII → bayt = karakter).

    Uzunluk SABİT tutulur çünkü K5 iki FARKLI BOYUTTA defteri karşılaştırır: satır boyu
    dalgalansaydı okunan bayt farkı dosya boyutundan mı satır boyundan mı geldiği ayrılamazdı."""
    ornek = json.dumps({"i": f"{0:07d}", "event": "dolgu", "msg": ""}, ensure_ascii=False)
    dolgu = satir_bayt - len(ornek) - 1          # -1: satır sonu
    assert dolgu > 0, f"satir_bayt={satir_bayt} iskelete ({len(ornek)}) sığmıyor"
    satirlar = [json.dumps({"i": f"{i:07d}", "event": "dolgu", "msg": "x" * dolgu},
                           ensure_ascii=False) for i in range(n)]
    p = dizin / ad
    p.write_text("\n".join(satirlar) + "\n", encoding="utf-8")
    return p


def _denetim_olayi(m, **ek) -> dict:
    """Bu botun bir denetim olayı. Olay ADI ve BOT ADI üretimden okunur, dizge TEKRARLANMAZ —
    kopyalanan bir ad ayrıştığında okuyucu hiçbir şey bulamaz ve çivi sessizce vakum-yeşil olur."""
    sd = importlib.import_module("ops.soul_denetimi")
    kayit = {"ts": "2026-09-16T22:03:14+00:00", "level": "info", "event": sd.OLAY,
             "bot": m.PROFIL_ADI, "hukum": "temiz", "kaynak": "llm",
             "model": "custom:kapi/nvidia/nemotron-3-ultra-550b-a55b:free",
             "cevaplayan_model": "nvidia/nemotron-3-super-120b-a12b:free", "cevap_bas": None}
    kayit.update(ek)
    return kayit


def _dolgu_olaylari(n: int, baslangic: int = 0) -> list[dict]:
    """Denetim olayı OLMAYAN `n` olay — pencereyi dolduran gerçek trafiğin sapı (defter üç botun
    ortağıdır ve iki şef koşumu arasına başka olaylar düşer)."""
    return [{"ts": "2026-09-16T10:00:00+00:00", "level": "info", "event": "dolgu",
             "i": baslangic + i} for i in range(n)]


def _gecer(metin: str, *adaylar: str) -> bool:
    """Adaylardan BİRİ metinde geçiyor mu?

    TÜRKÇE BÜYÜK/KÜÇÜK KATLAMASI GÜVENİLMEZDİR (`"İ".lower()` noktalı bir `i̇` üretir, `"I".lower()`
    `i`): `.lower()` ile arama, şerhteki vurgulu büyük harfli bir beyanı SESSİZCE kaçırırdı. O
    yüzden aranan biçimler ADIYLA verilir — çivi neyi aradığını saklamaz."""
    return any(a in metin for a in adaylar)


def _pencere_serhi() -> str:
    """`DENETIM_OLAY_PENCERESI` atamasının HEMEN ÜSTÜNDEKİ şerh bloğu.

    Şerh KAYNAKTAN okunur: bu dosyaya kopyalanan bir gerekçe, üretimdeki gerekçe silindiği gün
    yine yeşil kalır ve çivi var olmayan bir beyanı doğrulamış olurdu."""
    kaynak = URETIM.read_text(encoding="utf-8")
    ad = "DENETIM_OLAY_PENCERESI"
    i = kaynak.index(f"\n{ad} = ")
    blok = []
    for satir in reversed(kaynak[:i].splitlines()):
        if not satir.startswith("#"):
            break
        blok.append(satir)
    assert blok, f"{ad} atamasının üstünde HİÇ şerh yok — gerekçe ölçülemez"
    return "\n".join(reversed(blok))


# ================================================================================================
# K1 — PENCERE BİR İŞ GÜNÜNE DAYANIR VE ŞERHİ ÖLÇÜM TARİHİ TAŞIR
# ================================================================================================

def test_K1_PENCERE_BIR_IS_GUNU_OLAYINI_KAPSAR(m):
    """Pencerenin BİRİMİ satır değil GÜNDÜR: bir iş gününün ölçülmüş olay sayısını kapsamayan bir
    pencere, akşam koşumunda dünkü denetim olayını YAPISAL OLARAK göremez.

    Eşik bu yüzden "400'den büyük" değil "bir iş gününden küçük değil" diye yazılır — sayının
    kendisi değil, TEMSİL ETTİĞİ süre çivilenir."""
    assert m.DENETIM_OLAY_PENCERESI >= IS_GUNU_OLAY, (
        f"pencere {m.DENETIM_OLAY_PENCERESI} olay — ölçülen iş günü {IS_GUNU_OLAY} olaydan KÜÇÜK; "
        "akşam koşumu bir önceki akşamın kendi olayını göremez")


def test_K1_SERH_OLCUMU_VE_OLCUM_TARIHINI_TASIR(m):
    """Sayı taşıyan satır ölçüm tarihini taşır (CLAUDE.md). Tarihsiz bir sabit, türetildiği
    dünyanın ne zamanki dünya olduğunu söylemez — bir yıl sonra kimse 900'ün hâlâ bir iş günü
    olup olmadığını ölçemez.

    ÖLÇÜM ŞERHTE DE GEÇMELİ: `IS_GUNU_OLAY` bu dosyada bir kopya olarak durmasın diye, aynı sayı
    üretim şerhinde ARANIR — iki taraf ayrıştığı gün çivi öter (tek-kaynak yasası)."""
    serh = _pencere_serhi()
    assert re.search(r"\b20\d\d-\d\d-\d\d\b", serh), \
        f"pencere şerhinde ÖLÇÜM TARİHİ yok: {serh!r}"
    assert str(IS_GUNU_OLAY) in serh, (
        f"iş günü ölçümü ({IS_GUNU_OLAY}) üretim şerhinde geçmiyor — çivi ile üretim ayrışmış, "
        f"sabitin dayanağı ölçülemez: {serh!r}")
    assert "iş günü" in serh, f"şerh pencereyi bir İŞ GÜNÜ olarak adlandırmıyor: {serh!r}"


def test_K1_SERH_BEDELI_VE_ZAMAN_TABANLI_REDDI_BEYAN_EDER(m):
    """BEDEL YASASI + reddedilen alternatif. Pencereyi büyütmek okumayı ~5 katına çıkarır; bu
    kazancın YANINDA yazılmazsa körlük sessiz kalır. Ve ZAMAN TABANLI pencerenin neden
    SEÇİLMEDİĞİ de bilgidir — yazılmazsa bir sonraki tur aynı seçeneği sıfırdan tartışır."""
    serh = _pencere_serhi()
    assert _gecer(serh, "SABİT", "sabit"), \
        f"şerh bedelin SABİT olduğunu beyan etmiyor: {serh!r}"
    assert _gecer(serh, "BAĞIMSIZ", "bağımsız"), \
        f"şerh bedelin dosya boyutundan bağımsızlığını beyan etmiyor: {serh!r}"
    assert _gecer(serh, "ZAMAN TABANLI", "zaman tabanlı") and _gecer(serh, "SEÇİLMEDİ"), (
        f"şerh zaman tabanlı pencerenin neden seçilmediğini beyan etmiyor: {serh!r}")


# ================================================================================================
# K2 — REGRESYON: olay PENCEREDEYSE bulunur ve künyesi basılır
# ================================================================================================

def test_K2_PENCEREDEKI_OLAY_BULUNUR_VE_KUNYESI_BASILIR(m, sandbox_state):
    """POZİTİF KONTROL. K3/K4 ayrımı, okuyucunun bulabildiğini hâlâ bulduğunu göstermeden bir şey
    kanıtlamaz: her şeye "ölçülemedi" diyen bir okuyucu da K3'ü geçerdi."""
    olay = _denetim_olayi(m)
    store.write_jsonl("events.jsonl", _dolgu_olaylari(5) + [olay] + _dolgu_olaylari(3, 100))

    okuma = m._son_denetim_olayi()
    assert okuma.durum == m.PENCERE_BULUNDU, f"pencerede duran olay bulunamadı: {okuma.durum}"
    assert okuma.olay.get("cevaplayan_model") == olay["cevaplayan_model"]

    satir = m._denetci_teshis_satiri()
    assert olay["cevaplayan_model"] in satir, f"künye basılmadı: {satir!r}"
    assert "kayıt yok" not in satir and "PENCERE DIŞINDA" not in satir, \
        f"bulunan olay için 'bulunamadı' cümlesi basıldı: {satir!r}"


def test_K2_BASKA_BOTUN_OLAYI_BU_BOTUN_KAYDI_SAYILMAZ(m, sandbox_state):
    """Defter üç botun ortağıdır. Bot süzgeci düşerse okuyucu `@karne`nin künyesini `@sef`in
    satırında gösterir — ve o, bulunamamaktan DAHA kötü bir cevaptır (yanlış künye)."""
    store.write_jsonl("events.jsonl", _dolgu_olaylari(3) + [_denetim_olayi(m, bot="karne")])

    okuma = m._son_denetim_olayi()
    assert okuma.durum == m.PENCERE_KAYIT_YOK, \
        f"başka botun olayı bu botun kaydı sayıldı: {okuma.durum} · {okuma.olay!r}"


# ================================================================================================
# K3 — PENCERE DOLDU + olay yok → "ÖLÇÜLEMEDİ", "kayıt yok" DEĞİL  (bu turun ASIL kazancı)
# ================================================================================================

@pytest.fixture
def dolu_pencere(m, sandbox_state):
    """Defterde olay VARDIR ama pencereye GİRMEZ: en eskide bir denetim olayı, üstünde pencereyi
    taşıran dolgu. Gerçek dünyanın tam şekli budur — ölçüm 400'lük pencerede akşam koşumunun her
    gün bu duruma düştüğünü gösterdi."""
    eski = _denetim_olayi(m, ts="2026-09-15T22:03:14+00:00")
    store.write_jsonl("events.jsonl", [eski] + _dolgu_olaylari(m.DENETIM_OLAY_PENCERESI + 50))
    return eski


def test_K3_PENCERE_DOLDUYSA_DURUM_OLCULEMEDI_SINIFIDIR(m, dolu_pencere):
    """Okuyucu pencerenin SONUNA ulaştıysa, bulamamak bir YOKLUK ÖLÇÜMÜ değildir: daha eski
    kayıtlara HİÇ bakılmamıştır. Sınıf burada ayrılır, çünkü çıktı cümlesi bu sınıftan türer."""
    okuma = m._son_denetim_olayi()
    assert okuma.durum == m.PENCERE_DISINDA, (
        f"pencere dolduğu hâlde durum {okuma.durum!r} — 'ölçemedim' ile 'yok' ayrılmadı")
    assert okuma.olay == {}, "pencere dışındaki olay bulunmuş gibi döndü"
    assert okuma.taranan == m.DENETIM_OLAY_PENCERESI, (
        f"taranan {okuma.taranan} ≠ pencere {m.DENETIM_OLAY_PENCERESI} — 'pencere doldu' iddiası "
        "kanıtsız")


def test_K3_CIKTI_PENCERE_DISINDA_DER_KAYIT_YOK_DEMEZ(m, dolu_pencere):
    """UYDURMA YASAĞININ ÇIKTI YARISI: ayrım okunduğu yerde kaybolursa hiç yapılmamıştır.
    Operatörün gördüğü cümle "kayıt yok" DEMEMELİDİR — çünkü kaydın yokluğu ölçülmedi."""
    satir = m._denetci_teshis_satiri()
    assert "kayıt yok" not in satir, (
        f"pencere doldu ama satır YOKLUK iddia ediyor — ölçülmemiş bir yokluk uydurmadır: {satir!r}")
    assert "PENCERE DIŞINDA" in satir, f"satır 'pencere dışında' sınıfını adlandırmıyor: {satir!r}"
    assert "ÖLÇÜLEMEDİ" in satir, f"satır ölçülemediğini söylemiyor: {satir!r}"


def test_K3_OPERATORUN_GORDUGU_DURUM_SATIRI_DA_AYRIMI_TASIR(m, dolu_pencere):
    """YASA 6: ayrım yalnız iç fonksiyonda kalırsa operatöre ULAŞMAZ. Okuyucu zinciri
    `_durum_satiri`ya kadar izlenir — her koşumun İLK satırı odur."""
    satir = m._durum_satiri({"teslim_edilecek": [], "olculemeyen": []})
    assert m.ETIKET_DENETCI_TESHISI in satir, f"teşhis alanı durum satırında yok: {satir!r}"
    assert "PENCERE DIŞINDA" in satir, f"ayrım durum satırına ULAŞMIYOR: {satir!r}"


# ================================================================================================
# K4 — DEFTER KISA (pencere dolmadı) + olay yok → "kayıt yok" (DOĞRU negatif)
# ================================================================================================

def test_K4_KISA_DEFTERDE_YOKLUK_GERCEKTEN_OLCULUR(m, sandbox_state):
    """Defterin TAMAMI pencereye sığdıysa "yok" DOĞRUDUR ve öyle basılmalıdır. Her şeye
    "ölçülemedi" demek, ayrımı ters yönden yok etmekten başka bir şey değildir."""
    store.write_jsonl("events.jsonl", _dolgu_olaylari(12))

    okuma = m._son_denetim_olayi()
    assert okuma.durum == m.PENCERE_KAYIT_YOK, (
        f"defter pencereye sığdığı hâlde durum {okuma.durum!r} — doğru negatif kayboldu")
    assert okuma.taranan == 12, f"taranan olay sayısı yanlış: {okuma.taranan}"

    satir = m._denetci_teshis_satiri()
    assert "kayıt yok" in satir, f"ölçülmüş yokluk 'kayıt yok' denmedi: {satir!r}"
    assert "PENCERE DIŞINDA" not in satir, \
        f"ölçülmüş yokluk 'ölçülemedi' gibi basıldı: {satir!r}"


def test_K4_IKI_CUMLE_BIRBIRINDEN_AYIRT_EDILEBILIR(m, sandbox_state):
    """SÖZLEŞMENİN ÖZÜ TEK SATIRDA: aynı "bulamadım" sonucu, iki farklı NEDENLE iki FARKLI cümle
    üretmelidir. Eşitlerse ayrım kodda vardır ama operatörde YOKTUR.

    "FARKLI DİZGE" YETMEZ (mutasyon turunda ölçüldü): iki cümle yalnız taranan olay sayısında
    ayrılıyorsa sınıflar çökmüş olsa bile dizgeler farklı kalır ve çivi vakum-yeşile döner. O
    yüzden AYRIMIN KENDİSİ aranır: yokluk iddiası TAM OLARAK BİR cümlede geçmelidir."""
    store.write_jsonl("events.jsonl", _dolgu_olaylari(12))
    kisa = m._denetci_teshis_satiri()
    store.write_jsonl("events.jsonl", _dolgu_olaylari(m.DENETIM_OLAY_PENCERESI + 50))
    dolu = m._denetci_teshis_satiri()

    assert kisa != dolu, (
        "kısa defter ile dolu pencere AYNI cümleyi üretti — 'ölçülemedi' ile 'yok' aynı çıktıyla "
        f"görünüyor: {kisa!r}")
    yokluk = [s for s in (kisa, dolu) if "kayıt yok" in s]
    assert yokluk == [kisa], (
        "yokluk iddiası YALNIZ ölçülmüş negatifte geçmeli — kısa defter ve dolu pencere aynı "
        f"sınıfa katlanmış: kısa={kisa!r} · dolu={dolu!r}")


def test_K4_DEFTER_OKUNAMAZSA_UCUNCU_CUMLE_BASILIR(m, sandbox_state, monkeypatch):
    """ÜÇÜNCÜ SINIF: defter hiç okunamadıysa ne "yok" ne de "pencere dışında" doğrudur — hiç
    BAKILAMADI. Düşüş fail-open'dır (okuyucu teslimatı düşüremez) ama SESSİZ değildir."""
    from meridian import obs
    monkeypatch.setattr(obs, "recent", lambda n: (_ for _ in ()).throw(OSError("defter kilitli")))

    okuma = m._son_denetim_olayi()
    assert okuma.durum == m.PENCERE_OKUNAMADI, f"okuma düşüşü sınıflandırılmadı: {okuma.durum!r}"

    satir = m._denetci_teshis_satiri()
    assert "OKUNAMADI" in satir and "ÖLÇÜLEMEDİ" in satir, f"düşüş adıyla basılmadı: {satir!r}"
    assert "kayıt yok" not in satir, f"okunamayan defter YOKLUK gibi basıldı: {satir!r}"


# ================================================================================================
# K5 — BEDEL: pencere büyüdü ama okuma DOSYA BOYUTUNDAN BAĞIMSIZ kaldı
# ================================================================================================

def _olcen_open(sayac: dict):
    """v410'un bayt sayan `open`ına AÇILIŞ sayacı ekler: "kaç blok okundu" sorusunun cevabı
    bayt sayısında değil açılış/okuma sayısında görünür."""
    ic = _acma_sarmalayici(sayac)

    def _acan(*a, **kw):
        sayac["acilis"] += 1
        return ic(*a, **kw)
    return _acan


def test_K5_BEDEL_DOSYA_BUYUDUKCE_BUYUMEZ(m, sandbox_state, monkeypatch):
    """BEDEL ÖLÇÜMÜ, KARARIN DAYANAĞI. Pencere 400→900 çıkınca ilk 256 KB'lik yoklama bloğu
    yetmiyor ve ikinci bir blok okunuyor (~5 kat). Kararın şartı bu artışın SABİT kalmasıydı:
    defter büyüdükçe maliyet BÜYÜMEMELİ.

    İKİ FARKLI BOYUTTA defter ölçülür ve okunan BAYT ile AÇILIŞ sayısının EŞİT olması istenir —
    "sabit" iddiası ancak iki nokta karşılaştırılarak ölçülebilir. Mutlak bir bayt eşiğine çivi
    ATILMAZ (store'un blok sabitleri bu dosyanın sözleşmesi değildir); ölçülen şey BAĞIMSIZLIKTIR.

    Ölçüm ÜRETİM YOLUNDAN geçer (`_son_denetim_olayi`), doğrudan `store.read_jsonl`den değil:
    okuyucu bir gün pencereyi es geçip defteri tam okumaya başlarsa bayt dosya boyutuyla büyür ve
    bu çivi kırmızıya döner."""
    olcum, okumalar = {}, {}
    for n in (5_656, 11_312):                     # ~2,5 MB ve ~5,0 MB (SATIR_BAYT sabit)
        p = _sabit_satirli_defter(sandbox_state, n)
        sayac = {"bayt": 0, "acilis": 0}
        monkeypatch.setattr(store, "open", _olcen_open(sayac), raising=False)
        try:
            okumalar[n] = m._son_denetim_olayi()
        finally:
            monkeypatch.delattr(store, "open", raising=False)
        olcum[n] = (sayac["bayt"], sayac["acilis"], p.stat().st_size)
        print(f"K5 n={n}: dosya={p.stat().st_size} okunan_bayt={sayac['bayt']} "
              f"acilis={sayac['acilis']} taranan={okumalar[n].taranan} "
              f"durum={okumalar[n].durum}")
        assert sayac["bayt"] > 0, "sayaç hiç tetiklenmedi — sarmalama çalışmıyor olabilir"

    # BEDEL İDDİASI ÖNCE ÖLÇÜLÜR: sonuç doğruluğu (taranan/durum) aşağıda ayrıca tutulur, ama
    # "maliyet dosya boyutundan bağımsız" iddiası kendi başına bir sözleşmedir ve onu bir sonuç
    # kontrolünün arkasına gizlemek, mutasyon turunda bedel çivisinin hiç ÇALIŞMAMASINA yol açar.
    (b1, a1, s1), (b2, a2, s2) = olcum[5_656], olcum[11_312]
    assert s2 > s1 * 1.5, f"iki defter yeterince farklı boyutta değil: {s1} ↔ {s2}"
    assert b1 == b2, (
        f"okunan bayt dosya boyutuyla DEĞİŞTİ ({b1} ↔ {b2}) — bedel artık sabit değil, defter "
        "büyüdükçe teşhis okuması pahalanır")
    assert a1 == a2, f"okuma (blok) sayısı dosya boyutuyla değişti: {a1} ↔ {a2}"
    assert b1 < s1, (
        f"kuyruk okuma kazancı YOK: {b1} bayt okundu, küçük defter zaten {s1} bayt — tam-okuma "
        "eşiği devreye girmiş olabilir")

    for n, okuma in okumalar.items():
        assert okuma.taranan == m.DENETIM_OLAY_PENCERESI, (
            f"n={n}: pencere kadar olay taranmadı ({okuma.taranan}) — okuma yolu bozuk")
        assert okuma.durum == m.PENCERE_DISINDA, f"n={n}: beklenen sınıf değil: {okuma.durum!r}"


def test_K5_BUYUK_DEFTERDE_SONUC_TAM_OKUMAYLA_AYNI(m, sandbox_state):
    """BEDEL ÖLÇÜMÜ TEK BAŞINA YETMEZ: az okuyup YANLIŞ okumak da ucuzdur. Kuyruk okumasının
    döndürdüğü pencere, TAM OKUMANIN naif referansıyla BİREBİR eşit olmalı."""
    p = _sabit_satirli_defter(sandbox_state, 5_656)
    n = m.DENETIM_OLAY_PENCERESI
    assert store.read_jsonl("events.jsonl", limit=n) == _naif_oku(p, limit=n)
    assert len(store.read_jsonl("events.jsonl", limit=n)) == n
