"""test_arama_ui_v460.py — [TSK-167 dilim-2 · Task 2] PANO ARAMA GÖRÜNÜMÜ = HAFIZA
YÜZEYİNİN ONUNCU DURAĞININ BEKÇİSİ (2026-09-08, Rol-1 hükümleri K3/K6/K7).

NUMARA ÇAKIŞMASI ÖLÇÜLDÜ (2026-09-08, brief kalemi):
`ls tests .claude/worktrees/*/tests | grep -oE 'v[0-9]+' | sort -t v -k2 -n | tail -1`
→ **v459** (Task 1'in çivisi, kardeş worktree'de). v460 BOŞTU; taşıma gerekmedi.

TETİK: ROADMAP [TSK-167] dilim-2. Dilim-1 A1'de bir anlamsal arama CLI'ı kurdu
(`deploy/hindsight/hafiza_ara.sh`), Task 1 onu `GET /api/arama` olarak panoya bir
OKUYUCU diye açtı; bu görev o ucun ekran karşılığıdır. Ev seçimi K7 hükmü:
Hafıza yüzeyinin ONUNCU durağı — TSK-118'in `hafiza-dersler` emsali birebir
(çivi ailesi: `tests/test_hafiza_dersler_duragi_v394.py`).

ÇİVİNİN SINIFI VE ZAYIFLIĞI AÇIKÇA YAZILI (v286/v288/v375/v378/v388/v394 ailesinin
kurulu cevabı — `ui/` altında test çatısı YOKTUR, ölçüldü `ui/package.json`: yalnız
`build` ve `kontrol` betikleri var): bu dosya TS/TSX'i METİN olarak okur. Ölçtüğü şey
davranış DEĞİL, davranışı üreten satırın VARLIĞIDIR. Zayıflık mutasyonla telafi edilir
(rapora yazılı, ≥4 mutasyon).

SAYIM BU DOSYADA DEĞİL v394'TE DE DEĞİL — İKİSİ AYRI SORU SORAR (tek-kaynak yasası):
v394 "dersler DOKUZUNCU sırada mı" sorusunu, bu dosya "arama ONUNCU ve SON mu"
sorusunu ölçer. v394'ün `len(...) == 9` sabiti bu dilimde ÖNEK (ilk dokuz) kontrolüne
çevrildi ve künyesi oraya yazıldı; iki dosyada iki ayrı toplam tutmak, bir sonraki
durak eklendiğinde ikisinin sessizce ayrışması demekti.

DIŞ BAĞIMLILIK BEYANI (dürüstlük kalemi): `meridian/arama.py` Task 1'in dalında
yaşıyor ve BU worktree'nin HEAD'inde YOK. `--dosya` beyaz listesi ayrışma çivisi
(`test_dosya_secenekleri_KORPUS_ONEKLERININ_ALT_KUMESI`) bu yüzden modül VARSA ölçer,
yoksa ADIYLA atlar — Rol-1'in merge sonrası tam suite koşumunda etkinleşir. Sessiz
bir `pass` değil görünür bir `skip`tir: "ölçülmedi" ile "ölçüldü, temiz" aynı satırda
görünmemeli.
"""
from __future__ import annotations

import pathlib
import re

import pytest

KOK = pathlib.Path(__file__).resolve().parents[1]
PANO = KOK / "ui/src/pano"
HAFIZA = PANO / "yuzeyler/hafiza"

ALANLAR = PANO / "alanlar.ts"
KOMUTLAR = PANO / "komutlar.ts"
GORUNUMLER = HAFIZA / "gorunumler.ts"
HAFIZA_YUZEYI = HAFIZA / "HafizaYuzey.tsx"
ARAMA_GORUNUMU = HAFIZA / "Arama.tsx"
ARAMA_MANTIK = HAFIZA / "aramaMantigi.ts"
PALET = PANO / "kabuk/search-dialog.tsx"

#: Task 1'in modülü — BU DALDA YOK (dosya başlığındaki beyan).
ARAMA_MODULU = KOK / "meridian/arama.py"

#: Bu dilimin DOĞURDUĞU iki dosya. "Yeni dosya" kuralları (yoklama yok, `fetch(` yok,
#: ham hex yok) YALNIZ bunlarda ölçülür: mevcut dosyaların kendi çivileri var ve
#: onların geçmişini bu dosyadan yeniden yargılamak kapsam kaymasıdır.
YENI_DOSYALAR = (ARAMA_GORUNUMU, ARAMA_MANTIK)

_YORUM = re.compile(r"/\*.*?\*/|(?<![:'\"])//[^\n]*", re.S)


def soy_metin(metin: str) -> str:
    """Şerhleri söker. Meridian'ın belge geleneği kararın gerekçesini yazarken
    YASAKLANAN ŞEYİ ALINTILAR; soymadan ölçen çivi kendi şerhini ihlal sanır
    (v286'nın `_soy` dersi, v394 emsali)."""
    return _YORUM.sub(" ", metin)


def soy(p: pathlib.Path) -> str:
    return soy_metin(p.read_text(encoding="utf-8"))


def ham(p: pathlib.Path) -> str:
    return p.read_text(encoding="utf-8")


# ============================================================================
# (0) ÖLÇÜM ARACININ KENDİSİ
# ============================================================================

def test_olculen_dosyalar_YERINDE():
    """KÖRLÜK ALARMI (v394 emsali): yol bayatlarsa aşağıdaki her `in` kontrolü sessizce
    boş metin okur ve çivi "temiz" der. Dosya varlığı AYRI ölçülür ki 'sıfır ihlal' bir
    okuma yokluğu olmasın."""
    for p in (ALANLAR, KOMUTLAR, GORUNUMLER, HAFIZA_YUZEYI, ARAMA_GORUNUMU, ARAMA_MANTIK, PALET):
        assert p.is_file(), f"ölçülecek dosya yok: {p}"
        assert len(p.read_text(encoding="utf-8")) > 200, f"dosya beklenmedik biçimde küçük: {p}"


def test_YORUM_SOKUCUSU_kendisi_olculuyor():
    """POZİTİF KONTROL (v378/v388/v394 emsali): sökücü çalışmıyorsa aşağıdaki VARLIK ve
    YOKLUK iddialarının hepsi sessizce yalan söyler."""
    ornek = 'const a = "IZ";\n// IZ\n/* IZ */\n{/* IZ */}\nconst b = `IZ`;\n'
    assert soy_metin(ornek).count("IZ") == 2, soy_metin(ornek)
    kod = 'const re = /ab/g;\nif (a < b) { x(); }\nconst t = `${a}/${b}`;\n'
    assert soy_metin(kod) == kod, "sökücü bilinen bir kod bloğunu yiyor"


# ============================================================================
# (K1) KİMLİK ÜÇ DOSYADA — `alanlar.ts` · `gorunumler.ts` · `GOVDELER`
# ============================================================================

def _memory_bolumler_kimlikleri() -> list[str]:
    """SINIR HAM METİNDE ARANIR (v394 dersi): blok sonundaki `// ---- SAYFALAR` işareti
    bir yorumdur ve `soy()` onu da söker — sökülmüş metinde arayan desen kendi ölçtüğü
    şeyi yok ederdi. Yalnız YAKALANAN blok soyulur."""
    m = re.search(r"\n  memory:\s*\{(.*?)\n  \},\n\n  // ---- SAYFALAR", ham(ALANLAR), re.S)
    assert m, "YUZEYLER.memory bloğu okunamadı — desen bayat"
    return re.findall(r'kimlik:\s*"(hafiza-[a-z]+)"', soy_metin(m.group(1)))


def test_kayitta_ONUNCU_bolum_hafiza_arama():
    kimlikler = _memory_bolumler_kimlikleri()
    assert kimlikler.count("hafiza-arama") == 1, f"hafiza-arama kaydı yok ya da tekil değil: {kimlikler}"
    assert kimlikler[-1] == "hafiza-arama", (
        f"hafiza-arama kaydın SONUNDA değil: {kimlikler} — K7 hükmü 'onuncu durak, SONA eklenir'"
    )
    assert len(kimlikler) == 10, f"YUZEYLER.memory.bolumler on değil: {len(kimlikler)} ({kimlikler})"


def test_arama_kaydinin_BASLIK_VE_SORUSU():
    m = re.search(
        r'\{\s*kimlik:\s*"hafiza-arama",\s*baslik:\s*"([^"]+)",\s*soru:\s*"([^"]+)"', soy(ALANLAR)
    )
    assert m, "hafiza-arama kaydı beklenen biçimde okunamadı"
    assert m.group(1) == "Arama", f"başlık {m.group(1)!r} (beklenen 'Arama')"
    assert m.group(2) == "Bu soruya hangi belgeler yakın?", f"soru {m.group(2)!r}"


def test_arama_kaydinin_IKONU_recall_ile_AYNI_DEGIL():
    """`hafiza-recall` zaten `Search` ikonunu taşıyor. İkisini aynı ikonla çizmek, sol
    gezinmede iki ayrı sorunun tek şeye benzemesi demekti — Recall bankaya, Arama
    DEPOYA sorar (ikisi ayrı kaynak, aşağıdaki banka beyanı)."""
    a = soy(ALANLAR)
    m = re.search(r'kimlik:\s*"hafiza-arama",[^}]*ikon:\s*([A-Za-z0-9_]+)', a)
    assert m, "hafiza-arama kaydının ikonu okunamadı"
    r = re.search(r'kimlik:\s*"hafiza-recall",[^}]*ikon:\s*([A-Za-z0-9_]+)', a)
    assert r, "hafiza-recall kaydının ikonu okunamadı"
    assert m.group(1) != r.group(1), f"iki görünüm aynı ikonu taşıyor: {m.group(1)}"


def test_gorunum_LISTESINDE_onuncu_kimlik_SONA_eklendi():
    """CP paritesi iddiası İLK SEKİZ için korunur (`gorunumler.ts` başlığı); dokuzuncu
    TSK-118'in, onuncu bu dilimin — ikisi de SONA eklendi, aralarına değil."""
    m = re.search(r"HAFIZA_GORUNUMLERI\s*=\s*\[(.*?)\]\s*as const", soy(GORUNUMLER), re.S)
    assert m, "HAFIZA_GORUNUMLERI dizisi okunamadı — desen bayat"
    kimlikler = re.findall(r'"(hafiza-[a-z]+)"', m.group(1))
    assert kimlikler == [
        "hafiza-anasayfa", "hafiza-bellekler", "hafiza-bilgi", "hafiza-recall",
        "hafiza-reflect", "hafiza-belgeler", "hafiza-varliklar", "hafiza-yapilandirma",
        "hafiza-dersler", "hafiza-arama",
    ], f"sıra ya da küme bozuk: {kimlikler}"


def test_govde_TABLOSUNDA_arama_govdesi_VAR():
    """`Record<HafizaGorunumu, …>` eksik girdide DERLEMEYİ kırar, ama AD yanlışsa derleme
    geçer ve ekran sessiz kalır — bu çivi adı da ölçüyor (v394 emsali)."""
    s = soy(HAFIZA_YUZEYI)
    assert '"hafiza-arama": Arama,' in s, "GOVDELER tablosunda hafiza-arama görünümü yok"
    assert 'import { Arama } from "./Arama";' in s, "Arama görünüm gövdesi içe aktarılmıyor"


def test_arama_govdesinin_EKRAN_CAPASI_VAR():
    """v288 parite deseni: `BolumKart` `id={\\`bolum-${kimlik}\\`}` üretir ve regex bunu
    GÖREMEZ — v288'in kendi çözümü çağrı yerindeki `kimlik="…"` literalini okumaktır."""
    assert 'kimlik="hafiza-arama"' in soy(ARAMA_GORUNUMU), \
        "BolumKart çağrısı kimlik propunu literal taşımıyor"


# ============================================================================
# (K2) UI KISITLARI — YOKLAMA YOK · TEK KAPI · HAM HEX YOK
# ============================================================================

def test_yeni_dosyalarda_useApi_YOK():
    """YOKLAMA YASAK (plan Global Constraints): her sorgu A1'in 4 OCPU'sunda bir ONNX
    oturumu kurar. `useApi(yol, periyot)` bu görünümde 15/30 sn'de bir arama koşturur ve
    bedeli hiçbir yerde görünmezdi. Sorgu OPERATÖR eylemiyle koşar."""
    for p in YENI_DOSYALAR:
        assert "useApi(" not in soy(p), f"{p.name} yoklama kancasını kullanıyor (useApi)"


def test_yeni_dosyalarda_fetch_YOK():
    """TEK KAPI (v378'in `fetch(` yasağı): ikinci bir HTTP uygulaması kimlik/401/hata
    gövdesi sözleşmesinden sessizce ayrışır."""
    for p in YENI_DOSYALAR:
        assert "fetch(" not in soy(p), f"{p.name} kendi fetch'ini açıyor"
        # İKİ HATLI (v378 Y-2 dersi): şerh içine gizlenmiş bir çağrı da sayılmaz —
        # ham metinde geçiyorsa YALNIZ şerhte geçmeli.
        if "fetch(" in ham(p):
            assert "v378" in ham(p) or "tek kapı" in ham(p).lower(), \
                f"{p.name} ham metninde `fetch(` var ve gerekçesi yazılı değil"


def test_yeni_dosyalar_apiGet_KAPISINI_kullaniyor():
    """Yokluk kanıtı tek başına yeterli değil: `fetch(` yoksa ama `apiGet` de yoksa,
    ekran hiç okumuyordur ve iki yasak da bedavaya yeşil olur."""
    birlesik = "\n".join(soy(p) for p in YENI_DOSYALAR)
    assert "apiGet" in birlesik, "yeni dosyaların hiçbiri `veri.ts::apiGet` kapısını kullanmıyor"


#: HAM HEX — `#rgb`, `#rrggbb`, `#rrggbbaa`. Kelime sınırı yerine `#` öncesinde
#: harf/rakam OLMAMASI aranır (`&#39;` gibi varlıkları elemek için).
_HAM_HEX = re.compile(r"(?<![\w])#[0-9a-fA-F]{3,8}\b")


def test_yeni_dosyalarda_HAM_HEX_YOK():
    """Renk YALNIZ `--color-*` jetonlarından ve anlam utility'lerinden gelir."""
    for p in YENI_DOSYALAR:
        bulunan = _HAM_HEX.findall(soy(p))
        assert not bulunan, f"{p.name} ham hex taşıyor: {bulunan}"


def test_HAM_HEX_YASAGININ_EVI_BURASI_OLCULDU():
    """BEDEL/KAPSAM ÖLÇÜMÜ (brief kalemi: "v208/v407 kapsamına giriyor mu ÖLÇ"):
    v208 YALNIZ `meridian/web/*.html` jeton bloklarını karşılaştırır, v407 ise
    `ui/src` altında `card`/`accent` bracket okumasını arar. İKİSİ DE bu dilimin
    doğurduğu `.tsx`teki ham rengi GÖRMEZ — yasağın evi bu yüzden BURASI.
    Bu çivi o boşluğun kapandığını değil, boşluğun VAR olduğunu ölçer: bir gün
    v208/v407 genişletilirse bu satır kırmızıya döner ve kopya yasak kaldırılır."""
    v208 = (KOK / "tests/test_jeton_birligi_v208.py").read_text(encoding="utf-8")
    assert "ui/src" not in v208 and "UI_SRC" not in v208, \
        "v208 artık ui/src'yi de tarıyor — buradaki ham hex yasağı ikinci kopya oldu"
    v407 = (KOK / "tests/test_jeton_shadcn_cakisma_v407.py").read_text(encoding="utf-8")
    assert "_HAM_HEX" not in v407, "v407 ham hex taramaya başladı — kopya yasak"


def test_HAM_HEX_DESENI_kendisi_olculuyor():
    """Deseni ölçmeyen bir yasak, sessizce her şeyi geçirir."""
    assert _HAM_HEX.findall('color: "#0af"') == ["#0af"]
    assert _HAM_HEX.findall('bg-[#112233]') == ["#112233"]
    assert _HAM_HEX.findall("var(--color-basari)") == []


def test_AbortController_kullaniliyor():
    """ÖNCEKİ İSTEK İPTAL EDİLİR: operatör ikinci kez "Ara"ya bastığında birinci turun
    yanıtı hâlâ yoldadır ve onu yazmak, ekranda ESKİ sorgunun sonucunu YENİ sorgunun
    başlığı altında bırakırdı (`veri.ts` bayat-gövde sınıfının aynısı)."""
    birlesik = "\n".join(soy(p) for p in YENI_DOSYALAR)
    assert "new AbortController()" in birlesik, "istek iptali kurulmamış"
    assert re.search(r"\.abort\(\)", birlesik), "kurulan kontrol hiç `abort()` edilmiyor"
    assert re.search(r"signal", birlesik), "iptal sinyali `apiGet`e geçirilmiyor"


# ============================================================================
# (K3) DÖRT DURUM AYRIK — VE `mesgul` `neden`DEN ÖNCE
# ============================================================================

def _durum_coz_govdesi() -> str:
    s = soy(ARAMA_MANTIK)
    m = re.search(r"export function durumCoz\((.*?)\n\}", s, re.S)
    assert m, "`durumCoz` okunamadı — desen bayat (dört durumun tek kaynağı bu fonksiyon)"
    return m.group(1)


def test_MESGUL_NEDENDEN_ONCE_dallanir():
    """TASK 1 SÖZLEŞMESİ (rapor § "Dört durum"): `mesgul: true` dalında `neden` DE doludur
    (`arama.MESGUL_NEDENI`). `neden` önce kontrol edilirse meşgul hâli ekranda
    "Ölçülemedi" diye çizilir — operatör başka bir aramanın koştuğunu ÖĞRENEMEZ ve
    sistemin arızalandığını sanar."""
    govde = _durum_coz_govdesi()
    i_mesgul = govde.find("mesgul")
    i_neden = govde.find("neden")
    assert i_mesgul >= 0, "`durumCoz` `mesgul` alanını hiç okumuyor"
    assert i_neden >= 0, "`durumCoz` `neden` alanını hiç okumuyor"
    assert i_mesgul < i_neden, (
        "`neden` `mesgul`den ÖNCE dallanıyor — meşgul hâli 'Ölçülemedi' diye çizilir"
    )


def test_neden_dalinda_SONUC_YOK_dizgesi_YOK():
    """"Boş sonuç" ile "ölçülemedi" tek cümleye katlanamaz (uydurma yasağı)."""
    s = soy(ARAMA_GORUNUMU) + soy(ARAMA_MANTIK)
    assert "sonuç yok" not in s.lower(), \
        "ekranda 'sonuç yok' dizgesi var — ölçülemeyen bir arama ölçülmüş gibi okunur"


def test_dort_durumun_HEPSI_AYRI_CIZILIYOR():
    s = soy(ARAMA_MANTIK)
    for tur in ('"mesgul"', '"olculemedi"', '"bos"', '"dolu"'):
        assert tur in s, f"durum ayrımında {tur} yok — dört hâl tek kutuya katlanmış"


def test_BOS_dali_ESIK_YOK_cumlesini_tasiyor():
    """Sıralama saf mesafedir; bir eşik VARMIŞ gibi "eşleşme bulunamadı" demek, ölçülmemiş
    bir kapıyı ölçülmüş göstermek olurdu."""
    s = soy(ARAMA_GORUNUMU).lower()
    assert "eşik yok" in s, "boş liste dalı 'eşik yok, sıralama saf mesafedir' beyanını taşımıyor"


def test_OLCULEMEDI_bileseni_kullaniliyor():
    """Uydurma yasağının ekran karşılığı ortak bileşendir (`Olculemedi`); kendi cümlesini
    yazan bir dal, `neden`i zorunlu tutan sözleşmenin dışına düşer."""
    assert "Olculemedi" in soy(ARAMA_GORUNUMU), "ölçülemedi hâli ortak bileşenle çizilmiyor"


# ============================================================================
# (K4) BEYANLAR — BANKA SEÇİCİ · BELGE AÇILMAZ · İSABET ORANI · BAYATLIK
# ============================================================================

def test_banka_secici_BEYANI_var():
    """K3 hükmü: kabuk her görünümün üstüne "Banka" seçicisi çizer; bu görünüm bankayı
    KULLANMAZ (kaynak sqlite-vec taban indeksi). Sessizce yok saymak, operatöre etkisi
    olmayan bir denetim göstermek olurdu."""
    s = soy(ARAMA_GORUNUMU)
    assert "Banka" in s, "banka seçicisinin bu görünümde etkisiz olduğu YAZILI değil"
    assert re.search(r"Banka[^<]{0,200}(etkile|kullan)", s), \
        "banka beyanı bir cümle değil yalnız bir kelime — etkisizliği açıkça yazılmalı"


def test_gorunum_bank_ozelligini_OKUMUYOR():
    """Beyan yetmez: gövde `bank`i gerçekten okumamalı, yoksa cümle kendi kodunu
    yalanlar. Ölçüm bileşenin YIKIM LİSTESİNDE yapılır (`{ kayit }`) — metnin
    herhangi bir yerinde `bank` aramak, beyan cümlesinin kendisini ihlal sayardı."""
    m = re.search(r"export function Arama\(\{([^}]*)\}", soy(ARAMA_GORUNUMU))
    assert m, "Arama bileşeninin özellik yıkımı okunamadı — desen bayat"
    assert "bank" not in m.group(1), \
        f"görünüm `bank` özelliğini alıyor — beyanla çelişiyor: {m.group(1).strip()}"


def test_belge_ACILMAZ_beyani_var():
    """`/api/belge?yol=` ucu YOKTUR (ölçüldü). Satırı tıklanabilir yapmak, olmayan bir
    yeteneği var göstermek olurdu; yokluk EKRANDA yazılı."""
    s = soy(ARAMA_GORUNUMU).lower()
    assert "açılmaz" in s or "açılmıyor" in s, "belge açılmadığı ekranda yazılı değil"
    assert "yolu kopyala" in s, "yol kopyalama karşılığı yok (beyanın telafisi)"


def test_derin_bag_ROADMAP_yuzeyine_KURULMUYOR():
    """`ROADMAP.md%237` sonucu ROADMAP yüzeyine derin bağ TAŞIMAZ: kesitin document_id'si
    bir sayfa çapası DEĞİLDİR ve bağ operatörü yanlış yere götürürdü."""
    s = soy(ARAMA_GORUNUMU)
    assert "/dashboard/kanban" not in s, "sonuç satırı ROADMAP yüzeyine derin bağ kuruyor"


def test_isabet_orani_TEK_KAYNAKTAN_ve_KUNYELI():
    """Ölçülmüş sayı ekrana ikinci kez elle yazılırsa sessizce ayrışır. Sabit TEK yerde
    durur, künyesi (EDG-067, n=36) yanındadır ve bir CEVAP değil ADAY LİSTESİ olduğu
    aynı cümlede yazılıdır."""
    # SAYIM SOYULMUŞ METİNDE: şerhte gerekçesiyle geçmesi MEŞRU (ve istenir) — yasak olan
    # ikinci bir BİLDİRİM, yani ekrana ayrıca yazılmış ikinci bir oran.
    mantik = soy(ARAMA_MANTIK)
    assert mantik.count("55,6") == 1, \
        f"isabet oranı `aramaMantigi.ts` KODUNDA {mantik.count('55,6')} kez geçiyor — tek kaynak olmalı"
    kunyeli = ham(ARAMA_MANTIK)
    assert "EDG-067" in kunyeli or "EDG-2026-067" in kunyeli, "isabet oranının künyesi yok"
    assert "n=36" in kunyeli or "n = 36" in kunyeli, "örneklem büyüklüğü beyansız"
    assert "55,6" not in ham(ARAMA_GORUNUMU), "oran görünüme İKİNCİ kez yazılmış (kopya)"
    # HARF DUYARLI ARANIYOR — VE BU BİLİNÇLİ: Python'un `lower()`ı Türkçe `İ`yi
    # birleşen noktalı bir `i`ye çevirir ("li̇stesi̇"), yani harf-duyarsız bir arama
    # bu cümleyi SESSİZCE bulamazdı. Cümle ekranda vurgulu geçiyor, öyle ölçülüyor.
    assert "ADAY LİSTESİ" in mantik, \
        "okuma talimatı 'cevap değil ADAY LİSTESİdir' cümlesini taşımıyor"


def test_bayatlik_rozeti_head_commit_ve_uretim_ts():
    """İndeks HAFTALIK tazelenir (Pazar 08:15Z). Künyesiz bir sonuç listesi "canlı depo"
    diye okunurdu."""
    s = soy(ARAMA_GORUNUMU)
    assert "head_commit" in s, "künye commit'i ekranda yok"
    assert "uretim_ts" in s, "künye üretim damgası ekranda yok"
    assert "08:15Z" in s or "haftalık" in s, "tazeleme kadansı ekranda beyan edilmiyor"


def test_kunye_alanlari_SAYI_SANILMIYOR():
    """Task 1 raporu: `kunye` alan DEĞERLERİ DİZGEDİR (`chunk_sayisi` bir sayı gibi
    görünse de dizge). Üzerinde aritmetik/`toLocaleString` yapan bir ekran sessizce
    `NaN` basardı."""
    s = soy(ARAMA_GORUNUMU)
    assert not re.search(r"chunk_sayisi[^\n]{0,60}toLocaleString", s), \
        "`chunk_sayisi` sayı gibi biçimlendiriliyor — alan dizgedir"


# ============================================================================
# (K5) KUTU — `k` YALNIZ 5/10 · `dosya` KAPALI LİSTE · KIRPMA BEDELİ
# ============================================================================

def test_k_secenekleri_YALNIZ_5_VE_10():
    """K6 hükmü: API tavanı 20 (sohbetle ortak sabit) ama PANO 20 sunmaz — her sorgu bir
    ONNX oturumu ve `k` büyüdükçe CLI'ın aday çekimi (k×4) de büyür."""
    m = re.search(r"K_SECENEKLERI\s*=\s*\[(.*?)\]", soy(ARAMA_MANTIK), re.S)
    assert m, "K_SECENEKLERI okunamadı — desen bayat"
    degerler = [int(x) for x in re.findall(r"\d+", m.group(1))]
    assert degerler == [5, 10], f"k seçenekleri {degerler} (K6 hükmü: yalnız 5 ve 10)"


def test_dosya_secenekleri_KAPALI_LISTE():
    m = re.search(r"DOSYA_SECENEKLERI\s*=\s*\[(.*?)\]\s*as const", soy(ARAMA_MANTIK), re.S)
    assert m, "DOSYA_SECENEKLERI okunamadı — desen bayat"
    degerler = re.findall(r'deger:\s*"([^"]*)"', m.group(1))
    assert degerler[0] == "", "ilk seçenek 'hepsi' (boş değer) olmalı"
    assert "docs/" in degerler and "research/cards/" in degerler, f"kapalı liste eksik: {degerler}"
    assert "ROADMAP.md" not in degerler, \
        "ham `ROADMAP.md` seçeneği GEÇERSİZDİR (indekste `ROADMAP.md%237` kesiti var)"


def test_dosya_secenekleri_KORPUS_ONEKLERININ_ALT_KUMESI():
    """AYRIŞMA ÇİVİSİ: UI'ın kapalı listesi sunucunun beyaz listesinin ALT KÜMESİ olmalı —
    aksi hâlde seçilebilen bir önek 400 döndürür ve düğme çalışır görünüp reddedilir.

    Modül bu dalda YOK (dosya başlığındaki beyan); Rol-1'in merge sonrası koşumunda
    etkinleşir. Sessiz `pass` değil görünür `skip`."""
    if not ARAMA_MODULU.is_file():
        pytest.skip(
            "meridian/arama.py bu dalda YOK (Task 1 kardeş dalda; merge sonrası ölçülür) — "
            "ayrışma çivisi ATLANDI, temiz DEĞİL"
        )
        return
    kaynak = ARAMA_MODULU.read_text(encoding="utf-8")
    m = re.search(r"KORPUS_ONEKLERI[^=]*=\s*\((.*?)\)", kaynak, re.S)
    assert m, "meridian/arama.py::KORPUS_ONEKLERI okunamadı — desen bayat"
    onekler = set(re.findall(r'"([^"]+)"', m.group(1)))
    g = re.search(r"DOSYA_SECENEKLERI\s*=\s*\[(.*?)\]\s*as const", soy(ARAMA_MANTIK), re.S)
    assert g, "DOSYA_SECENEKLERI okunamadı"
    ui = {d for d in re.findall(r'deger:\s*"([^"]*)"', g.group(1)) if d != ""}
    assert ui <= onekler, f"UI listesi sunucunun beyaz listesinde olmayan önek taşıyor: {ui - onekler}"


def test_kirpma_BEDELI_ekranda():
    """BEDEL YASASI: uç kesiti 600 karakterde kırpar ve `kesit_kirpildi` + `metin_uzunluk`
    ile bunu BEYAN eder. Ekran o beyanı çizmezse kırpma görünmez olur ve operatör kesik
    bir kesiti tam sanar."""
    s = soy(ARAMA_GORUNUMU)
    assert "kesit_kirpildi" in s, "kırpma bayrağı okunmuyor"
    assert "metin_uzunluk" in s, "tam uzunluk okunmuyor"
    assert "karakter" in s, "kırpma beyanı ekranda cümleye dönüşmüyor"


def test_mesafe_HAM_basiliyor():
    """`Recall.tsx`in ölçülmüş gerekçesi: `0,001125` ile `0,001004` yuvarlandığında ikisi de
    "0,001" olur ve sıralamanın niçin böyle olduğu okunamaz."""
    s = soy(ARAMA_GORUNUMU)
    assert not re.search(r"mesafe[^\n]{0,80}toFixed", s), "mesafe yuvarlanıyor (toFixed)"
    assert not re.search(r"mesafe[^\n]{0,80}maximumFractionDigits", s), \
        "mesafe yuvarlanıyor (toLocaleString basamak sınırı)"


def test_korpus_disi_sayisi_EKRANDA():
    """Sunucu korpus dışı satırları DÜŞÜRÜR ve sayısını beyan eder; ekran o sayıyı
    yutarsa süzgeç sessiz olur."""
    assert "korpus_disi_n" in soy(ARAMA_GORUNUMU), "korpus dışı sayacı ekranda yok"


# ============================================================================
# (K6) ⌘K — METNİ TAŞIR, ATEŞLEMEZ
# ============================================================================

def _palet_komut_govdesi() -> str:
    """"Belgelerde ara…" komutunun `onSelect` gövdesi."""
    s = soy(PALET)
    m = re.search(
        r"keywords=\{\[\.\.\.BELGELERDE_ARA_ANAHTARLARI\]\}(.*?)onSelect=\{\(\)\s*=>\s*\{(.*?)\n\s*\}\}",
        s, re.S,
    )
    assert m, "palet komutunun onSelect gövdesi okunamadı — desen bayat"
    govde = m.group(2)
    # KOMŞU KOMUTUN GÖVDESİNİ ÖLÇMEDİĞİMİZ ÇİVİLİ: "Ajan'a sor" satırı aynı dosyada ve
    # neredeyse aynı biçimde duruyor; yanlış gövdeyi ölçen bir çivi, bu komut hiç
    # yazılmamışken bile yeşil kalırdı.
    assert "sohbetIstegiBirak" not in govde, "yakalanan gövde komşu komutunki (Ajan'a sor)"
    return govde


def test_palet_komutu_KAYITLI():
    s = soy(PALET)
    assert "Belgelerde ara" in s, "⌘K paletinde 'Belgelerde ara…' komutu yok"
    assert "BELGELERDE_ARA_YOLU" in s, "komut kanonik adresi tek kaynaktan almıyor"
    k = soy(KOMUTLAR)
    assert "BELGELERDE_ARA_YOLU" in k and "BELGELERDE_ARA_ANAHTARLARI" in k, \
        "palet komutunun adresi/anahtarları `komutlar.ts`te tanımlı değil"


def test_palet_YOLU_yuzeyYolu_ILE_kuruluyor():
    """Adres elle yazılırsa `alanlar.ts` kaydıyla sessizce ayrışır (v394'ün sohbet-bağı
    dersi: çalışan ama yanlış yere giden bağ, çalışmayan bağdan sinsidir)."""
    m = re.search(r"BELGELERDE_ARA_YOLU\s*=\s*(.+)", soy(KOMUTLAR))
    assert m, "BELGELERDE_ARA_YOLU tanımı okunamadı"
    assert "yuzeyYolu(" in m.group(1), f"adres elle yazılmış: {m.group(1).strip()}"
    assert '"hafiza-arama"' in m.group(1), "adres onuncu durağın kimliğini taşımıyor"


def test_palet_komutunun_onSelectinde_AG_CAGRISI_YOK():
    """PALETİN HÜKMÜ: hızlı erişim ≠ icra. Ayrıca her tuş vuruşunda bir ONNX süreci
    doğurmamak için sorgu ATEŞLENMEZ."""
    govde = _palet_komut_govdesi()
    for yasak in ("apiGet", "fetch(", "apiPost", "/api/arama"):
        assert yasak not in govde, f"palet komutu ağ çağrısı yapıyor: {yasak}"


def test_palet_komutu_METNI_TASIYOR():
    govde = _palet_komut_govdesi()
    assert "aramaIstegiBirak(query)" in govde, "yazılmış metin istek kutusuna bırakılmıyor"
    assert "router.push(BELGELERDE_ARA_YOLU)" in govde, "komut arama görünümüne gitmiyor"


def test_istek_kutusu_ADRES_SORGUSUYLA_tasinmiyor():
    """ÖLÇÜLMÜŞ SINIR (`gorunumler.ts::sekmeliYol`): adres kurucusu bugün TEK sorgu
    anahtarı biliyor (`sekme`) ve ikincisini sessizce düşürürdü. Ayrıca operatörün
    serbest metnini adres çubuğuna yazmak geçmişte kalıcı bir kopya bırakırdı."""
    assert "?soru=" not in soy(PALET), "palet sorguyu adrese yazıyor"
    m = re.search(r"BELGELERDE_ARA_YOLU\s*=\s*(.+)", soy(KOMUTLAR))
    assert m and "soru" not in m.group(1), "kanonik adres sorgu metnini taşıyor"


def test_istek_kutusu_TEK_SEFERLIK():
    """`sohbetIstegiBirak` emsali: tüketilmiş istek ikinci kez uygulanırsa kutu her
    yeniden çizimde kendi kendine dolar."""
    s = soy(ARAMA_MANTIK)
    assert "export function aramaIstegiBirak(" in s, "istek kutusu bırakıcısı yok"
    assert "export function aramaIstegiAl(" in s, "istek kutusu okuyucusu yok"
    m = re.search(r"export function aramaIstegiAl\((.*?)\n\}", s, re.S)
    assert m and re.search(r"bekleyen\w*\s*=\s*null", m.group(1)), \
        "`aramaIstegiAl` kutuyu BOŞALTMIYOR — istek ikinci kez uygulanır"


def test_gorunum_ISTEGI_TUKETIYOR_ama_ATESLEMIYOR():
    """Metin kutuya düşer, sorgu KOŞMAZ: taşıma bir icra değildir."""
    s = soy(ARAMA_GORUNUMU)
    assert "aramaIstegiAl" in s, "görünüm palet isteğini hiç okumuyor (metin kaybolur)"
    m = re.search(r"aramaIstegiAl\(\)(.*?)\n\s*\}", s, re.S)
    assert m, "istek tüketimi okunamadı"
    assert "ara(" not in m.group(1), "istek tüketilirken sorgu ATEŞLENİYOR"


def test_palet_anahtarlari_ARAMA_govdesine_YAZILDI():
    """`BOLUM_EK` tablosu TEK kaynak (v394 deseni); operatör "belge", "grep", "docs" diye
    arar, başlıktaki kelimeyi değil."""
    blok = re.search(r"const BOLUM_EK[^=]*=\s*\{(.*?)\n\};", soy(KOMUTLAR), re.S)
    assert blok, "BOLUM_EK tablosu okunamadı — desen bayat"
    satir = re.search(r'"hafiza-arama":\s*\[(.*?)\]', blok.group(1), re.S)
    assert satir, "hafiza-arama satırı BOLUM_EK'te yok"
    anahtarlar = re.findall(r'"([^"]+)"', satir.group(1))
    for k in ("belge", "docs", "gunluk", "arama"):
        assert k in anahtarlar, f"palet anahtarı eksik: {k!r} ({anahtarlar})"
    assert all(a == a.lower() for a in anahtarlar), f"anahtarlar katlanmış yazılmalı: {anahtarlar}"


# ============================================================================
# (K7) SORGU KURULUMU — TEK YER, KAÇIRILMIŞ
# ============================================================================

def test_sorgu_adresi_TEK_YERDE_kuruluyor():
    s = soy(ARAMA_MANTIK)
    assert "export function aramaYolu(" in s, "sorgu adresi kurucusu yok"
    assert "URLSearchParams" in s, "sorgu parametreleri elle birleştiriliyor — kaçırma yok"
    assert "/api/arama" in s, "uç yolu `aramaMantigi.ts`te tanımlı değil"
    assert "/api/arama" not in soy(ARAMA_GORUNUMU), \
        "uç yolu görünümde İKİNCİ kez yazılmış — `ARAMA_UC` sabiti üzerinden alınmalı"


def test_bos_soru_ISTEK_DOGURMUYOR():
    """Uç boş soruya 400 döner; ekranın kapalı listesi bu sınıfı ZATEN üretmemeli."""
    s = soy(ARAMA_GORUNUMU)
    assert re.search(r"trim\(\)\s*===\s*\"\"", s), "boş soru kontrolü yok"
