"""test_capa_korluk_beyani_v529.py — TSK-211 AÇIK KALEMİ: KÖRLÜĞÜ DONDURAN BEYAN ÇİVİSİ.

BU ÇİVİ BİR DAVRANIŞI DEĞİL BİR BORCU DONDURUR. Ölçtüğü şey bir kazanç değil, bilinen ve
BEYAN EDİLMİŞ bir kayıptır; yeşil kalması "her şey yolunda" demek DEĞİL, "borç hâlâ ödenmedi ve
hâlâ tam olarak beyan edildiği kadar" demektir.

ZEMİN (ölçüldü 2026-09-21, kaynak: codelaw._dosya_adi_kuyrugu_mu docstring'inin "KAYIP AÇIK"
paragrafı): KAPSAM SINIRI (3) bir DİZGE eşleşmesidir, dosya adıyla nitelikli sembolü AYIRT
EDEMEZ. Kuyruk parçalarından HERHANGİ biri codelaw._CAPA_UZANTILARI jetonlarından biriyle
TESADÜFEN çakışırsa — store.Depo.db biçimi, "db" bir `.db` dosya uzantısı jetonu olduğu için —
eşleşme dosya adı sayılır ve `_hukum`e HİÇ GİRMEDEN atlanır: ne `cozulen`e, ne `curuyen`e, ne de
`cozulemeyen`e yazılır. Yani o çapa çürüse bile SESSİZ çürür; "cozulemeyen" kovası bile onu
saymaz, çünkü kova SAYILAN körlüğün adresidir, bu ise SAYILMAYAN körlüktür.

KURAL DEĞİŞMEDİ VE DEĞİŞMEMELİ (bu çivi bir düzeltme TALEBİ değildir): "herhangi bir parça"
kuralı M4/M5 mutasyonlarının gösterdiği gibi ZORUNLUDUR — yalnız SON parçaya bakan kural
`auth.json.tmp` vakasını, yalnız İLK parçaya bakan kural `secrets.bak.json` vakasını kaçırır
(v528). Körlük, o iki sahte-pozitif sınıfının BİLEREK ödenen bedelidir.

BU ÇİVİ KIRMIZIYA DÖNERSE NE YAPILIR: kırmızı, körlüğün KAPANDIĞI anlamına gelir (çapa artık bir
kovaya düşüyor). O gün bu çivi BİR ARIZA DEĞİL BİR HABERDİR: codelaw._dosya_adi_kuyrugu_mu
docstring'indeki "KAYIP AÇIK" paragrafı ile bu dosya BİRLİKTE güncellenir — beyan kalkar, çivi
ya yeni davranışı ölçen bir çiviye dönüşür ya da emekli edilir. Beyanı güncellemeden çiviyi
silmek ya da gevşetmek YASAKTIR: o an belge ile kod sessizce ayrışır (tek-kaynak yasası).

BEDEL YASASI — KÖRLÜK ÖLÇÜLDÜ, "yok" VARSAYILMADI: dedektörün hâlâ ısırdığı (c) bölümünde
pozitif kontrolle gösterilir; jeton taşımayan nitelikli çapa AYNI sentetik ağaçta `curuyen`e
düşer ve sağlam olanı `cozulen`e. Üçü AYNI taramada ölçülür, yani "hiçbir kovada yok" hükmü
sentetik ağacın bozukluğundan (modül çözülmemesi) doğamaz.

CANLI AĞAÇTA BORÇ DEFTERİ (e bölümü): körlük kuramsal DEĞİLDİR — bugün canlı ağaçta iki GERÇEK,
sınıf-biçimli, nitelikli çapa bu kural tarafından affediliyor ve ikisi de tam olarak körlüğü
ANLATAN paragrafın kendi örnekleridir (meridian/codelaw.py). Kendi körlüğünü anlatan metnin o
körlüğün örneği olması, v528'in öğrettiği dersin yansımalı ikinci hâlidir.

ÖLÇÜM NOTU (Rol-1'e, bu çivinin konusu DEĞİL): aynı docstring'in "BUGÜN ÖLÇÜLEN" paragrafındaki
üç sayı (15 affedilen · 0 sınıf biçimli · 4 modülü çözülen) bu paragrafın KENDİSİ yazılmadan
ÖNCE ölçülmüş görünüyor; bugünkü yeniden ölçüm modülü çözülen 6 ve sınıf biçimli 2 veriyor
(ikisi de o paragrafın örnekleri). Sayı düzeltmesi motor dosyasına yazım gerektirir, bu tur
kapsamı DIŞIDIR — rapora bulgu olarak geçti.
"""
from __future__ import annotations

import pathlib

from meridian import codelaw
# DÜZENEK YENİDEN KULLANIMI (tek-kaynak yasası): v528'in sentetik kök/tarama yardımcıları ve
# hedef modül gövdesi KOPYALANMAZ. Kopya sessizce ayrışır ve iki dosya aynı kapsam sınırını
# farklı sentetik ağaçlarda ölçmeye başlar (v525'in v416'yı ithal etme emsali).
from tests.test_capa_dosya_kuyrugu_v528 import _HEDEF_STORE, _sentetik_kok, _tara

#: Beyan edilen körlüğün çapası. KOD DİZGESİDİR, düzyazı DEĞİL — `_dosya_yorum_metni` kod
#: dizgelerini bilerek süzer, yani bu sabit üçüncü beslemeye GİRMEZ ve bu dosya kendi ölçtüğü
#: borç defterini kirletmez.
_KOR_CAPA = "`store.Depo.db`"
#: Aynı biçimde ama jetonsuz: dedektörün hâlâ ısırdığını gösteren pozitif kontrol.
_CURUK_CAPA = "`store.Depo.olmayan`"
#: Sentetik ağaçta GERÇEKTEN var olan sınıf üyesi — "hiçbir kovada yok" hükmünün ağaç
#: bozukluğundan doğmadığını AYNI taramada kanıtlar.
_SAGLAM_CAPA = "`store.Depo.var_olan_metot`"

#: Canlı ağaçtaki borç defteri: meridian/codelaw.py'nin "KAYIP AÇIK" paragrafının örnekleri.
#: Kuyruk sonları jeton taşır ("db", "log"), ilk parçaları sınıf biçimlidir.
_CANLI_BORC = ("store.Store.db", "guard.Kapi.log")


def _tum_kovalar(rapor: dict) -> list[dict]:
    """Üç kovanın BİRLEŞİMİ. "Hiçbir kovada yok" hükmü ancak üçü birden okunarak kurulabilir —
    yalnız `curuyen`e bakmak, `cozulemeyen`e düşen bir çapayı "görünmez" sanmak olurdu."""
    return [*rapor["cozulen"], *rapor["curuyen"], *rapor["cozulemeyen"]]


# ---------------------------------------------------------------------------
# (a) MEKANİZMA — körlüğün KAYNAĞI: jeton çakışması (yardımcı BİREBİR ölçülür)
# ---------------------------------------------------------------------------

def test_JETON_CAKISMASI_NITELIKLI_KUYRUGU_DOSYA_ADI_SAYAR():
    """Körlüğün tek satırlık kaynağı: kuyruğun HERHANGİ bir parçası jeton kümesindeyse eşleşme
    dosya adı sayılır. `Depo.db` GERÇEK bir nitelikli çapa biçimidir ama "db" bir uzantı
    jetonudur — yardımcı ikisini ayırt EDEMEZ ve bu, kuralın kendisidir."""
    assert "db" in codelaw._CAPA_UZANTILARI, \
        "zemin değişti: 'db' artık uzantı jetonu değilse bu dosyanın beyanı yeniden ölçülmeli"
    assert codelaw._dosya_adi_kuyrugu_mu("Depo.db") is True, \
        "beyan edilen körlük YOK — kural değişmiş olabilir, docstring ile birlikte güncellenmeli"
    assert codelaw._dosya_adi_kuyrugu_mu("Depo.olmayan") is False, \
        "jetonsuz nitelikli kuyruk affedilirse dedektör artık ısırmıyor demektir"


def test_SENTETIK_HEDEF_JETON_ADINI_TASIMAZ():
    """Düzeneğin ön koşulu: sentetik `store.py` içinde `db` adlı HİÇBİR ŞEY yok. Olsaydı,
    körlük kapandığı gün çapa `curuyen`e değil `cozulen`e düşer ve (b)'deki hüküm yanlış
    sebeple kırmızı olurdu."""
    assert "db" not in _HEDEF_STORE, \
        "sentetik hedef 'db' adını taşıyor — beyan çivisinin ön koşulu bozuldu"
    assert "class Depo" in _HEDEF_STORE and "var_olan_metot" in _HEDEF_STORE


# ---------------------------------------------------------------------------
# (b) BEYAN — GERÇEK nitelikli çapa ÜÇ KOVANIN HİÇBİRİNDE görünmez
# ---------------------------------------------------------------------------

def test_JETONLA_CAKISAN_NITELIKLI_CAPA_HICBIR_KOVADA_GORUNMEZ(tmp_path):
    """BEYAN ÇİVİSİ. `Depo` sınıfı sentetik hedefte VARDIR, `db` üyesi YOKTUR: körlük
    olmasaydı bu çapa `curuyen`/`sembol_yok` olurdu. Bugün hiçbir kovaya yazılmıyor.

    AYNI TARAMADA sağlam bir nitelikli çapa da geçirilir ve `cozulen`e düşmesi ölçülür —
    "hiçbir kovada yok" hükmü böylece sentetik ağacın çözülmemesinden DOĞAMAZ (vakumlu yeşil
    yasağı: bir çivi, ölçemediği için değil, ölçtüğü için yeşil olmalıdır).

    KIRMIZIYA DÖNERSE: körlük kapanmıştır. Bu dosyanın başlık docstring'i ile
    codelaw._dosya_adi_kuyrugu_mu docstring'indeki "KAYIP AÇIK" paragrafı BİRLİKTE güncellenir.
    """
    kok = _sentetik_kok(tmp_path, {"store.py": _HEDEF_STORE})
    r = _tara(kok, f"bkz. {_KOR_CAPA} alanı ve {_SAGLAM_CAPA} çağrısı")

    assert [c["sembol"] for c in r["cozulen"]] == ["Depo.var_olan_metot"], \
        f"sentetik ağaç sağlam çapayı ÇÖZEMEDİ — düzenek bozuk, hüküm kurulamaz: {r}"
    kor = [c for c in _tum_kovalar(r) if "Depo.db" in c["capa"]]
    assert kor == [], (
        "BEYAN EDİLEN KÖRLÜK KAPANMIŞ: uzantı jetonuyla çakışan nitelikli çapa artık bir kovaya "
        f"düşüyor ({kor}). Bu bir arıza DEĞİL bir haberdir — codelaw._dosya_adi_kuyrugu_mu "
        "docstring'indeki 'KAYIP AÇIK' paragrafı ile bu çivi AYNI turda birlikte güncellenir "
        "(beyanı güncellemeden çiviyi silmek/gevşetmek yasaktır: belge ile kod sessizce ayrışır)")


def test_CURUK_OLSA_DA_SESSIZ_CURUR_HUKUM_HIC_KURULMAZ(tmp_path):
    """Körlüğün PAHALI yüzü ayrıca dondurulur: hedef modül ÇÖZÜLÜYOR (kapsam sınırı 2 geçiliyor),
    sembol de GERÇEKTEN yok — yani hüküm kurulabilirdi. Kurulmuyor ve kurulamadığı da SAYILMIYOR:
    `cozulemeyen` kovası SAYILAN körlüğün adresidir, bu ise sayılmayan körlüktür."""
    kok = _sentetik_kok(tmp_path, {"store.py": _HEDEF_STORE})
    r = _tara(kok, f"yalnız {_KOR_CAPA}")

    assert r == {"cozulen": [], "curuyen": [], "cozulemeyen": []}, \
        f"tek başına taranan kör çapa bir iz bıraktı — beyan yeniden ölçülmeli: {r}"
    assert codelaw._MODUL_CAPA_DESENI.search(f"yalnız {_KOR_CAPA}") is not None, \
        "desen bu biçimi HİÇ eşleştirmiyorsa körlük başka bir yerdedir — beyan yanlış okunmuş"


# ---------------------------------------------------------------------------
# (c) POZİTİF KONTROL — dedektör HÂLÂ ısırıyor (körlük bir susturma DEĞİL)
# ---------------------------------------------------------------------------

def test_JETONSUZ_NITELIKLI_CAPA_HALA_CURUYENE_DUSER(tmp_path):
    """Kuyruk yine iki parçalı ve yine sınıf-nitelikli, ama HİÇBİR parçası uzantı jetonu değil.
    Hüküm DEĞİŞMEDEN kurulur. Bu çivi olmasaydı, "noktalı kuyruk = dosya adı" diye genişletilmiş
    bir kural da (b) bölümünü geçerdi ve körlük sessizce büyürdü."""
    kok = _sentetik_kok(tmp_path, {"store.py": _HEDEF_STORE})
    r = _tara(kok, f"bkz. {_CURUK_CAPA} çağrısı")

    assert [(c["capa"], c["neden"]) for c in r["curuyen"]] == [
        ("store.Depo.olmayan", "sembol_yok")], r
    assert r["cozulen"] == [] and r["cozulemeyen"] == [], r


# ---------------------------------------------------------------------------
# (e) CANLI AĞAÇ — BORÇ DEFTERİ: körlük kuramsal değildir, iki GERÇEK örneği var
# ---------------------------------------------------------------------------

def test_CANLI_AGACTAKI_BORC_DEFTERI_BEYAN_EDILDIGI_GIBI_DURUYOR():
    """İki GERÇEK, sınıf-biçimli, nitelikli çapa canlı ağaçta bu kural tarafından affediliyor —
    ikisi de körlüğü ANLATAN paragrafın (meridian/codelaw.py "KAYIP AÇIK") kendi örnekleridir.

    İKİ AYRI ŞEY ÖLÇÜLÜR, ve ikisi birden gerekir:
      1. VAKUM GUARD — örnekler canlı metinde GERÇEKTEN duruyor mu? Durmuyorsa aşağıdaki
         "hiçbir kovada yok" hükmü bedavaya yeşil olurdu.
      2. BORÇ — tarayıcı (tek kaynak: `codelaw.report()`) onları üç kovanın hiçbirinde
         raporlamıyor.

    (1) KIRMIZI olursa: örnekler değişmiş/silinmiş demektir; beyan paragrafı ile bu çivi birlikte
    güncellenir. (2) KIRMIZI olursa: körlük kapanmıştır — aynı ikili güncelleme.

    NEDEN `report()` DEĞİL: `report()`ın üçüncü besleme ÖZETİ yalnız `curuyen`i dışarı verir
    (`capa_n` = cozulen+curuyen); üç kovanın BİRLEŞİMİ oradan okunamaz, yani "hiçbir kovada yok"
    hükmü kurulamaz. İkinci bir tarayıcı YAZILMADI — `report()`ın İÇİNDE çağırdığı AYNI iki
    gövde (`_yorum_metinleri` + `capa_uyusmasi`) burada doğrudan, üretim kökleriyle çağrılır."""
    metin = codelaw._dosya_yorum_metni(pathlib.Path(codelaw.__file__))
    for capa in _CANLI_BORC:
        assert f"`{capa}`" in metin, (
            f"beyan örneği `{capa}` codelaw'un düzyazısında YOK — borç defteri bayat; "
            "'KAYIP AÇIK' paragrafı ile bu çivi birlikte güncellenmeli")

    py_kokler = codelaw._kokler(("meridian", *codelaw._EK_CAPA_KOKLERI))
    y = codelaw.capa_uyusmasi(codelaw._yorum_metinleri(), py_kokler=py_kokler, modul_bicimi=True)
    assert y["cozulen"], "canlı ağaçta HİÇ çözülen çapa yok — tarama boşa döndü, hüküm kurulamaz"
    gorunen = [c["capa"] for c in _tum_kovalar(y)
               if any(c["capa"].endswith(b) for b in _CANLI_BORC)]
    assert gorunen == [], (
        f"canlı ağaçtaki borç artık bir kovada GÖRÜNÜYOR ({gorunen}) — körlük kapanmış olabilir; "
        "codelaw._dosya_adi_kuyrugu_mu docstring'indeki 'KAYIP AÇIK' paragrafı ile bu çivi AYNI "
        "turda birlikte güncellenir")
