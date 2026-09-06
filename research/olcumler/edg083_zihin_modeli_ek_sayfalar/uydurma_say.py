"""research/olcumler/edg083_zihin_modeli_ek_sayfalar/uydurma_say.py — EDG-2026-083 UYDURMA sayacı.

NE ÖLÇER. Kart `research/cards/EDG-2026-083-zihin-modeli-talep-uzerine-ek-sayfalar.yaml`nin
`olcum_plani` 3. maddesi: Hindsight zihin modeli sayfalarının (markdown METİN, Rol-1 hatırladığı
"kaynak") her sürümünden depo atıfları BEŞ SINIFA (`yol`/`kart`/`kalem`/`civi`/`sha`) ayrılıp GERÇEK
depoda doğrulanır; sayfa "hatırlanan"dır, bu betiğin ürettiği oran "ölçülen"dir. Betik HÜKÜM
VERMEZ: eşikler (kartın `esikler` alanı, %80 toplam / %60 sayfa-başı) burada GEÇMEZ — hükmü Rol-1
verir (CLAUDE.md §5, "Ölçüm kartına hüküm: Rol-1").

ROL: ÖLÇÜM ajanı. AĞA ÇIKMAZ (yalnız `--repo` altında dosya sistemi + `git`in salt-okunur alt
komutları: `ls-files`, `cat-file -e`). `meridian` paketinden HİÇBİR ŞEY içe aktarmaz — bu betik
`meridian.obs`a ULAŞAMAZ, pytest DIŞI bir koşum canlı yerel deftere yazamaz (AJAN kuralı). Karta
DOKUNMAZ, yalnız (gelecekte, ayrı bir çağrıda) OKUYABİLİR — bu betik onu OKUMAZ bile: eşikler
burada YOKTUR ki okunsun, hüküm dışı kalması bilinçli bir tasarım kararı.

GİRDİ ŞEMASI. `--sayfa-dizin <dizin>`: her sayfa BİR dosya. `<id>.json` şeması
`{"id","name","version","content"}` (yalnız `content` ZORUNLU okunur — `id` yoksa dosya adının
gövdesi `id` sayılır); `<id>.md` ham içeriktir (`id` = dosya adının gövdesi, `name`/`version` None).

BEŞ ATIF SINIFI (kart `olcum_plani` 3. madde — hepsi RAPORDA AYRI sayılır; regex ÇIKARIMI hâlâ
BEŞtir, aşağıdaki R1/R3(b) rulingları bu beşten İKİSİNİ (`sha`/`yol`) alt-sınıflara AYIRIR — yeni
regex EKLENMEZ):
  1. `yol`   — depo-yolu görünümlü dizge (regex `YOL_RE`) → İKİ kademeli doğrulanır (Rol-1 ruling
               2026-09-06, ÖLÇÜMDEN ÖNCE — kartın "depoda grep -F ile doğrulanır" ifadesinin
               içinde): (a) `tam` — mevcut kural, `git -C <repo> ls-files` kümesinde TAM EŞLEŞME;
               (b) `ad` — atıfta `/` YOKSA ve kümedeki bir dosyanın basename'i atıfla birebir
               eşleşiyorsa doğrulanır (dizinsiz atıf EKSİK-BELİRTİLMİŞtir, UYDURMA değil). Atıfta
               `/` VARSA `ad` hiç denenmez — yanlış dizinli atıf (`ops/guard.py` depoda yoksa)
               `meridian/guard.py`ye basename ile KAYMAZ. `dogrulanan` = `tam` + `ad` (ikisi
               ayrık sayılır); baştaki `./` soyulur, `%23`/`#`den sonrası soyulur. Uzantı listesi
               (Rol-1 ruling 2026-09-06, brief-uydurma-say-3, R3a): `jsonl`/`csv`/`log`/`sqlite`/
               `bak` eklendi VE uzantıdan sonra kelime-sınırı (`(?![A-Za-z0-9_])`) zorunlu —
               eskiden `candidates.jsonl` içinden `candidates.json` KESİLİYORDU (uzantı listesi
               `json`u `jsonl`in içinde buluyordu, sınır yoktu); artık tam atıf yakalanır.
  2. `kart`  — `EDG-2026-NNN` → `research/cards/EDG-2026-NNN-*.yaml` GLOB'u dolu mu (DEĞİŞMEDİ —
               R2'nin ROADMAP-metni gevşetmesi yalnız `kalem`edir, `kart`a SIÇRAMAZ).
  3. `kalem` — `TSK-NNN` → `ROADMAP.md` metninde HERHANGİ BİÇİMDE geçiyor mu (Rol-1 ruling
               2026-09-06, brief-uydurma-say-3, R2): eskiden yalnız `[TSK-NNN]` köşeli-parantez
               biçimi arandığı için `**TSK-061**` (tabloda kalın biçim) yanlışlıkla UYDURMA
               sayılıyordu — artık düz alt-dizge araması (`kod in roadmap_metni`) yeterli, çevresi
               `[...]`/`**...**`/çıplak fark etmez.
  4. `civi`  — `vNNN` (üç haneli) → `tests/` içinde `*_vNNN.py` ile biten bir dosya var mı.
  5. `sha`   — 7-40 haneli salt-hex dizge (tamamı rakamsa ELENİR — düz sayı, sha DEĞİL) →
               `git -C <repo> cat-file -e <sha>^{commit}` (rc=0 → doğrulandı; rc≠0 → doğrulanamadı,
               bu bir HATA DEĞİL, sha'nın kendisi geçersiz/yok demektir).
Aynı atıf bir sayfada birden çok geçerse TEK sayılır (`atiflari_cikar` küme döner).

İKİ EK SINIF, `sha`/`yol`DAN TÜRETİLİR (Rol-1 ruling 2026-09-06, brief-uydurma-say-3 — regex
EKLENMEZ, doğrulama SIRASINDA yeniden sınıflandırılır, çift SAYILMAZ):
  6. `bellek` (R1) — bir `sha` adayı (7-40 hex) `--bellek-kimlikleri <dosya>` (satır başına bir
               Hindsight bellek kimliği, tam uuid ya da hex) verilmişse ÖNCE bu kümede ÖNEK
               eşleşmesi (adayın kümedeki bir satırın BAŞI olup olmadığı) aranır: eşleşirse sınıf
               `bellek`, DOĞRULANMIŞ, `sha` yoluna (git cat-file) hiç GİRİLMEZ. Eşleşmezse mevcut
               `sha` yolu aynen işler. Gözlem: sayfa "Gözlem `03b5fc34`" gibi ifadelerle commit
               DEĞİL, A1 `memory_units.id` önekine atıf yapıyordu — bu UYDURMA değil YANLIŞ SINIF
               idi. Dosya verilmemişse `bellek` raporda `None` + `bellek_neden` alanı dolar.
  7. `calisma_dosyasi` (R3b) — bir `yol` adayı NE `tam` NE `ad` ile doğrulanabildiyse VE atıfta
               `/` yoksa VE `--calisma-dosyalari <dosya>` (satır başına bir dosya adı; A1 `state/`
               + `backups/` + `/opt/veri` listesi, ölçüm anında DONDURULMUŞ) verilmişse, atıfın
               (zaten dizinsiz olduğu için kendisi = basename'i) bu kümede TAM eşleşiyorsa sınıf
               `calisma_dosyasi`, DOĞRULANMIŞ (depo DIŞI ama GERÇEK — örn. `notify_undelivered.json`,
               `state/`de yaşar, versiyonsuzdur). Liste verilmemişse `calisma_dosyasi` raporda
               `None` + `calisma_dosyasi_neden` alanı dolar; bu durumda atıf `yol` sınıfında
               doğrulanamayan kalır (eski davranış KORUNUR).

UYDURMA YASAĞI: `oran` (`dogrulanan/toplam`) `toplam==0`da `None`dur, `0.0` DEĞİL — "hiç atıf
yoktu" ile "atıfların hiçbiri doğrulanmadı" (bu durumda `oran=0.0`, GERÇEKTEN ölçüldü) FARKLI
şeylerdir; ilk durumda `oran_neden` alanı doldurulur.

YASA 4 (sessiz-yutma yok): `git` çağrısının KENDİSİ çökerse (örn. `git` ikili dosyası PATH'te
yoksa — `subprocess.run`ın fırlattığı `OSError`) bu İKİ yerde (`ls_files_getir`, `sha_dogrula`)
YAKALANIR ve mesaj AÇIKÇA döner: `ls_files_getir` için ayrı dönüş değeri, `sha_dogrula` için o
sha'yı "doğrulanamadı" sayan bir dönüş DEĞERİ — ikisi de `calistir`de global `hata` listesine
toplanır, hiçbir yerde yutulmaz. Normal negatif sonuç (dosya ls-files'ta yok / sha cat-file'da
bulunamadı, rc≠0) bu YASANIN kapsamı DIŞINDA kalır — o bir ÇÖKME değil, GERÇEK bir ölçüm sonucudur.

ÇAPA YASAĞI: bu dosyada `dosya.py` + iki-nokta + rakam biçiminde satır çapası hiç kullanılmaz;
başka bir betiğe/modüle backtick'li nokta'lı (`modül.sembol`) atıf da YOK — bu betik `research/`
altında yaşar ve `codelaw`ın sembol-çapası taraması yalnız `meridian`+`tests` köklerini görür,
buraya nokta'lı bir atıf yazmak (referans çözülemeyeceği için) yanıltıcı olurdu."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import re
import subprocess

SANDBOX = pathlib.Path(__file__).resolve().parent

# ======================================================================================
# SINIF REGEXLERİ (kart olcum_plani 3. madde — beşi de HEPSİ RAPORDA AYRI sayılır)
# ======================================================================================

YOL_RE = re.compile(
    r"[A-Za-z0-9_./-]+\.(?:py|md|yaml|yml|ts|tsx|sh|jsonl|json|txt|css|csv|log|sqlite|bak)"
    r"(?![A-Za-z0-9_])")
KART_RE = re.compile(r"EDG-2026-\d{3}")
KALEM_RE = re.compile(r"TSK-\d{3}")
CIVI_RE = re.compile(r"\bv\d{3}\b")
SHA_RE = re.compile(r"\b[0-9a-f]{7,40}\b")

SINIF_REGEXLERI = {"yol": YOL_RE, "kart": KART_RE, "kalem": KALEM_RE, "civi": CIVI_RE, "sha": SHA_RE}
SINIF_SIRASI = ("yol", "kart", "kalem", "civi", "sha")


def _yol_normallestir(atif: str) -> str:
    """Baştaki `./`yi soyar, `%23`/`#`den (varsa, hangisi ÖNCE geliyorsa) sonrasını keser —
    `YOL_RE`nin kendi karakter kümesi bu ikisini zaten İÇERMEZ (eşleşme onlardan önce durur);
    normalleştirme, sayfa içeriği ileride farklı bir çıkarma yoluyla (örn. bir markdown bağlantı
    ayrıştırıcısı) beslenirse aynı sözleşmeyi KORUMAK için burada AYRICA yapılır (brief şartı)."""
    if atif.startswith("./"):
        atif = atif[2:]
    kesme_noktalari = [i for i in (atif.find("%23"), atif.find("#")) if i != -1]
    if kesme_noktalari:
        atif = atif[: min(kesme_noktalari)]
    return atif


def atiflari_cikar(icerik: str) -> dict[str, set[str]]:
    """Sayfa içeriğinden BEŞ sınıfın her birini AYRI bir kümeye çıkarır (tekilleştirilmiş —
    "aynı atıf bir sayfada birden çok geçse TEK sayılır", kart olcum_plani 3. madde). `sha` sınıfı
    tamamı rakam olan dizgeleri ELER (düz bir sayı sha GÖRÜNÜMLÜ olabilir ama sha DEĞİLDİR)."""
    sonuc: dict[str, set[str]] = {sinif: set() for sinif in SINIF_SIRASI}
    for sinif in SINIF_SIRASI:
        for eslesme in SINIF_REGEXLERI[sinif].finditer(icerik):
            atif = eslesme.group(0)
            if sinif == "yol":
                atif = _yol_normallestir(atif)
            elif sinif == "sha" and atif.isdigit():
                continue
            sonuc[sinif].add(atif)
    return sonuc


# ======================================================================================
# SINIF DOĞRULAYICILARI — dosya sistemi (kart/kalem/civi) + git salt-okunur (yol/sha)
# ======================================================================================

def ls_files_getir(repo) -> tuple[frozenset[str] | None, str | None]:
    """(kume|None, hata|None). `hata` yalnız `git` GERÇEKTEN çalıştırılamazsa (OSError) ya da
    `ls-files` beklenmedik bir rc döndürürse dolar — kartın hiç yol atıfı içermemesi ayrı bir
    durumdur ve buraya girmez (o zaman zaten kume üzerinde arama hiç yapılmaz)."""
    try:
        r = subprocess.run(["git", "-C", str(repo), "ls-files"],
                           capture_output=True, text=True, check=False)
    except OSError as exc:
        # sessiz-yutma: git ikili dosyası PATH'te yoksa/çalıştırılamazsa BÜTÜN 'yol' sınıfı bu
        # koşumda doğrulanamaz sayılır; çökme burada durdurulur ama mesaj YUTULMAZ — çağıran
        # (`calistir`) bunu global 'hata' listesine ekler (Yasa 4)
        return None, f"git ls-files çalıştırılamadı: {exc}"
    if r.returncode != 0:
        return None, f"git ls-files hata döndü (rc={r.returncode}): {(r.stderr or '').strip()}"
    return frozenset(satir for satir in r.stdout.splitlines() if satir), None


def sha_dogrula(repo, sha: str) -> tuple[bool, str | None]:
    """(dogrulandi_mi, hata|None). `hata` yalnız `git` GERÇEKTEN çalıştırılamazsa dolar; sha
    bilinmiyorsa (rc≠0, normal negatif sonuç) `hata=None` ile `False` döner — "hata = doğrulanamadı"
    (brief) tam burada: OSError DIŞINDAKİ her durum sha'nın kendisi hakkında bir SONUÇTUR."""
    try:
        r = subprocess.run(["git", "-C", str(repo), "cat-file", "-e", f"{sha}^{{commit}}"],
                           capture_output=True, text=True, check=False)
    except OSError as exc:
        # sessiz-yutma: git ikili dosyası PATH'te yoksa bu sha doğrulanamadı sayılır (aşağıdaki
        # dönüş) AMA neden dışarı SIZAR — çağıran global 'hata' listesine ekler (Yasa 4)
        return False, f"git cat-file çalıştırılamadı: {exc}"
    return (r.returncode == 0), None


def yol_dogrula(atif: str, ls_kume: frozenset[str] | None) -> tuple[bool, bool, list[str]]:
    """`yol` sınıfı İKİ kademeli doğrulama (Rol-1 ruling 2026-09-06, ÖLÇÜMDEN ÖNCE — kart
    `olcum_plani` 3. madde "depoda grep -F ile doğrulanır" ifadesinin İÇİNDE sayılır):
    1. `tam` — mevcut kural: `ls_kume`de birebir eşleşme.
    2. `ad`  — atıfta `/` YOKSA ve `ls_kume` içinde basename'i (son `/`den sonrası) atıfla BİREBİR
       eşleşen ≥1 dosya varsa DOĞRULANMIŞ sayılır (dizinsiz atıf EKSİK-BELİRTİLMİŞtir, UYDURMA
       değildir). Atıfta `/` VARSA `ad` hiç DENENMEZ — yanlış dizinli bir atıf (`ops/guard.py`
       depoda yoksa) `meridian/guard.py`ye basename ile KAYMAZ: yanlış dizin = yanlış atıf.
    Döner: `(tam, ad, ad_eslesenler)` — `ad_eslesenler` en çok 5 yol, sıralı; `tam` doğruysa ya da
    atıfta `/` varsa `ad`/`ad_eslesenler` her zaman `(False, [])`dur (kategoriler AYRIK — çağıran
    `dogrulanan = tam_sayisi + ad_sayisi`yı çift saymadan toplayabilsin diye)."""
    if ls_kume is None:
        return False, False, []
    tam = atif in ls_kume
    if tam or "/" in atif:
        return tam, False, []
    ad_eslesenler = sorted(p for p in ls_kume if p.rsplit("/", 1)[-1] == atif)
    return False, bool(ad_eslesenler), ad_eslesenler[:5]


def kart_dogrula(repo, kod: str) -> bool:
    dizin = pathlib.Path(repo) / "research" / "cards"
    if not dizin.is_dir():
        return False
    return any(dizin.glob(f"{kod}-*.yaml"))


def kalem_dogrula(repo, kod: str, roadmap_metni: str | None = None) -> bool:
    """Rol-1 ruling 2026-09-06 (brief-uydurma-say-3, R2): `kod` (`TSK-NNN`) `ROADMAP.md` metninde
    HERHANGİ BİÇİMDE (köşeli parantez `[TSK-NNN]`, kalın `**TSK-NNN**`, çıplak) geçiyorsa
    doğrulanmıştır — eski sürüm yalnız köşeli-parantez arıyordu, bu yüzden tabloda kalın yazılan
    GERÇEK bir referansı (`TSK-061`) yanlışlıkla UYDURMA sayıyordu. `kart` (`EDG-2026-NNN`) bu
    gevşetmenin DIŞINDA kalır — `kart_dogrula` hâlâ dosya varlığı ister, metin geçişi SAYILMAZ."""
    if roadmap_metni is None:
        yol = pathlib.Path(repo) / "ROADMAP.md"
        if not yol.exists():
            return False
        roadmap_metni = yol.read_text(encoding="utf-8")
    return kod in roadmap_metni


def civi_dogrula(repo, kod: str) -> bool:
    dizin = pathlib.Path(repo) / "tests"
    if not dizin.is_dir():
        return False
    return any(dizin.glob(f"*_{kod}.py"))


def _satir_listesi_oku(yol) -> frozenset[str]:
    """`--bellek-kimlikleri`/`--calisma-dosyalari` ortak girdi biçimi: satır başına BİR değer,
    boş satırlar ve kenar boşlukları atılır. Dosyanın kendisi yoksa `FileNotFoundError` OLDUĞU
    GİBİ yukarı fırlar — bu bir git/ağ çökmesi değil, operatörün yanlış yol vermesidir; Yasa 4'ün
    'sessiz-yutma' kapsamı DIŞINDA kalır (yakalanıp gizlenecek bir şey yok, hemen görünür olmalı)."""
    metin = pathlib.Path(yol).read_text(encoding="utf-8")
    return frozenset(satir.strip() for satir in metin.splitlines() if satir.strip())


def bellek_dogrula(atif: str, bellek_kume: frozenset[str] | None) -> bool:
    """`bellek` sınıfı (R1, Rol-1 ruling 2026-09-06, brief-uydurma-say-3): `atif` (bir `sha`
    adayı, 7-40 hex) `bellek_kume`deki (Hindsight bellek kimlik listesi) BİR satırın ÖN EKİYSE
    (büyük/küçük harf duyarsız `startswith`) doğrulanmıştır — sayfa bellek kimliğini KISALTILMIŞ
    yazar (`Gözlem 03b5fc34`), tam kimlik A1 `memory_units.id`dedir. Liste `None` ise (hiç
    verilmemiş) HER ZAMAN `False` döner — bu durumda aday normal `sha` yoluna düşer, buraya hiç
    girmemiş sayılmaz (çağıran `bellek_kume is None`u AYRICA kontrol eder)."""
    if bellek_kume is None:
        return False
    atif_kucuk = atif.lower()
    return any(m.lower().startswith(atif_kucuk) for m in bellek_kume)


def calisma_dosyasi_dogrula(atif: str, calisma_kume: frozenset[str] | None) -> bool:
    """`calisma_dosyasi` sınıfı (R3b, Rol-1 ruling 2026-09-06, brief-uydurma-say-3): dizinsiz bir
    `yol` adayı ne `tam` ne `ad` ile doğrulanabildiyse, A1 `state/`+`backups/`+`/opt/veri`
    listesinde (ölçüm anında DONDURULMUŞ, `--calisma-dosyalari`) TAM eşleşiyorsa doğrulanmıştır:
    depo DIŞI ama GERÇEK bir çalışma dosyasıdır (`notify_undelivered.json` gibi), UYDURMA değil.
    Liste `None` ise HER ZAMAN `False` döner — çağıran bu durumda atıfı `yol` sınıfında
    doğrulanamayan bırakır (eski davranış korunur)."""
    if calisma_kume is None:
        return False
    return atif in calisma_kume


# ======================================================================================
# SAYFA YÜKLEME — `<id>.json` (şema) ya da `<id>.md` (ham)
# ======================================================================================

def sayfalari_yukle(sayfa_dizin) -> list[dict]:
    sayfa_dizin = pathlib.Path(sayfa_dizin)
    dosyalar = sorted(p for p in sayfa_dizin.iterdir() if p.suffix in (".json", ".md"))
    sayfalar: list[dict] = []
    for yol in dosyalar:
        if yol.suffix == ".json":
            veri = json.loads(yol.read_text(encoding="utf-8"))
            if not isinstance(veri, dict):
                raise ValueError(f"sayfa JSON'u bir sözlük değil: {yol}")
            sayfa_id = str(veri.get("id") or yol.stem)
            icerik = str(veri.get("content") or "")
            ad = veri.get("name")
            surum = veri.get("version")
        else:
            sayfa_id = yol.stem
            icerik = yol.read_text(encoding="utf-8")
            ad = None
            surum = None
        sayfalar.append({"id": sayfa_id, "name": ad, "version": surum, "content": icerik,
                         "kaynak_dosya": str(yol)})
    return sayfalar


# ======================================================================================
# SAYFA-DÜZEYİ ÖLÇÜM
# ======================================================================================

def sayfa_olc(sayfa: dict, repo, ls_kume: frozenset[str] | None, roadmap_metni: str | None,
             hata_biriktirici: list, *, bellek_kume: frozenset[str] | None = None,
             calisma_dosyalari_kume: frozenset[str] | None = None) -> dict:
    """Bir sayfanın (`{'id','content',...}`) BEŞ sınıf atıfını çıkarır, her birini doğrular,
    sayfa başına `{toplam, dogrulanan, oran, oran_neden, sinif_bazinda, dogrulanamayan}` döner.
    `sinif_bazinda['yol']` ayrıca (Rol-1 ruling 2026-09-06, ölçümden önce) `dogrulanan_tam`,
    `dogrulanan_ad`, `ad_eslesmeleri` (`{atıf: [eşleşen yollar]}`, ad ile doğrulananlar için) taşır.
    `hata_biriktirici` (çağıranın listesi) `sha_dogrula`nın OSError kaynaklı mesajlarını TOPLAR —
    bu fonksiyon kendi başına bir global 'hata' alanı ÜRETMEZ, yalnız BİRİKTİRİR (Yasa 4).

    `bellek_kume`/`calisma_dosyalari_kume` (Rol-1 ruling 2026-09-06, brief-uydurma-say-3, R1/R3b):
    verilmişse (`None` DEĞİLSE) bir `sha` adayı önce `bellek_dogrula` ile, bir dizinsiz-ve-
    doğrulanamayan `yol` adayı `calisma_dosyasi_dogrula` ile denenir; eşleşirse atıf o sınıfa
    TAŞINIR (kaynak sınıfın `toplam`ına hiç GİRMEZ, çift SAYILMAZ) ve DAİMA doğrulanmış sayılır —
    ruling eşleşmeyeni zaten eski yoluna (sha/yol doğrulanamayan) bırakır. Liste `None` ise ilgili
    `sinif_bazinda` girdisi `None` olur, yanına `<sinif>_neden` alanı eklenir (uydurma yasağı:
    'hiç denenmedi' ile '0 doğru' KARIŞTIRILMAZ)."""
    atiflar = atiflari_cikar(sayfa["content"])
    sinif_bazinda: dict[str, dict] = {}
    dogrulanamayan_liste: list[dict] = []
    toplam = 0
    dogrulanan = 0
    bellek_aktif = bellek_kume is not None
    calisma_aktif = calisma_dosyalari_kume is not None
    bellek_toplam = 0
    calisma_toplam = 0

    for sinif in SINIF_SIRASI:
        kume = atiflar[sinif]
        s_toplam = 0
        s_dogrulanan = 0
        s_dogrulanamayan: list[str] = []
        s_dogrulanan_tam = 0
        s_dogrulanan_ad = 0
        s_ad_eslesmeleri: dict[str, list[str]] = {}
        for atif in sorted(kume):
            if sinif == "yol":
                tam, ad, ad_eslesenler = yol_dogrula(atif, ls_kume)
                if not (tam or ad) and calisma_aktif and "/" not in atif \
                        and calisma_dosyasi_dogrula(atif, calisma_dosyalari_kume):
                    # R3b: dizinsiz + depoda-yok + çalışma-dosyası listesinde VAR → bu atıf
                    # 'yol' toplamına hiç girmez, 'calisma_dosyasi' sınıfına TAŞINIR (doğrulanmış)
                    calisma_toplam += 1
                    continue
                s_toplam += 1
                if tam:
                    s_dogrulanan_tam += 1
                elif ad:
                    s_dogrulanan_ad += 1
                    s_ad_eslesmeleri[atif] = ad_eslesenler
                ok = tam or ad
                if ok:
                    s_dogrulanan += 1
                else:
                    s_dogrulanamayan.append(atif)
                    dogrulanamayan_liste.append({"sinif": sinif, "atif": atif})
                continue
            if sinif == "sha" and bellek_aktif and bellek_dogrula(atif, bellek_kume):
                # R1: bellek ÖNEK eşleşmesi git cat-file'dan ÖNCE denenir; eşleşen atıf 'sha'
                # toplamına hiç girmez, 'bellek' sınıfına TAŞINIR (doğrulanmış, ağa çıkılmaz)
                bellek_toplam += 1
                continue
            s_toplam += 1
            if sinif == "kart":
                ok = kart_dogrula(repo, atif)
            elif sinif == "kalem":
                ok = kalem_dogrula(repo, atif, roadmap_metni)
            elif sinif == "civi":
                ok = civi_dogrula(repo, atif)
            else:  # sha (bellek'e KAYMAYAN geri kalan)
                ok, hata = sha_dogrula(repo, atif)
                if hata:
                    hata_biriktirici.append(hata)
            if ok:
                s_dogrulanan += 1
            else:
                s_dogrulanamayan.append(atif)
                dogrulanamayan_liste.append({"sinif": sinif, "atif": atif})
        sinif_veri = {"toplam": s_toplam, "dogrulanan": s_dogrulanan,
                     "dogrulanamayan": s_dogrulanamayan}
        if sinif == "yol":
            # Rol-1 ruling 2026-09-06 (ölçümden ÖNCE): tam+ad ayrık sayılır, dogrulanan == toplamı
            sinif_veri["dogrulanan_tam"] = s_dogrulanan_tam
            sinif_veri["dogrulanan_ad"] = s_dogrulanan_ad
            sinif_veri["ad_eslesmeleri"] = s_ad_eslesmeleri
        sinif_bazinda[sinif] = sinif_veri
        toplam += s_toplam
        dogrulanan += s_dogrulanan

    if bellek_aktif:
        sinif_bazinda["bellek"] = {"toplam": bellek_toplam, "dogrulanan": bellek_toplam,
                                   "dogrulanamayan": []}
        toplam += bellek_toplam
        dogrulanan += bellek_toplam
    else:
        sinif_bazinda["bellek"] = None
        sinif_bazinda["bellek_neden"] = "bellek kimlik listesi verilmedi"

    if calisma_aktif:
        sinif_bazinda["calisma_dosyasi"] = {"toplam": calisma_toplam, "dogrulanan": calisma_toplam,
                                            "dogrulanamayan": []}
        toplam += calisma_toplam
        dogrulanan += calisma_toplam
    else:
        sinif_bazinda["calisma_dosyasi"] = None
        sinif_bazinda["calisma_dosyasi_neden"] = "çalışma dosyası listesi verilmedi"

    oran = (dogrulanan / toplam) if toplam else None
    oran_neden = (None if toplam
                 else "sayfada hiçbir depo atıfı (yol/kart/kalem/civi/sha) bulunamadı — oran tanımsız, uydurulamaz")
    return {"id": sayfa["id"], "kaynak_dosya": sayfa.get("kaynak_dosya"),
            "toplam": toplam, "dogrulanan": dogrulanan,
            "oran": round(oran, 6) if oran is not None else None,
            "oran_neden": oran_neden, "sinif_bazinda": sinif_bazinda,
            "dogrulanamayan": dogrulanamayan_liste}


def _toplami_hesapla(sayfa_sonuclari: list[dict]) -> dict:
    """Sayfa sonuçlarını toplar. `yol` sınıfı için `dogrulanan_tam`/`dogrulanan_ad` sayfalar
    arasında toplanır, `ad_eslesmeleri` birleştirilir (aynı atıf birden çok sayfada geçse eşleşen
    yollar AYNIdır — `ls_kume`nin saf bir fonksiyonu — bu yüzden çakışma riski yoktur).

    `bellek`/`calisma_dosyasi` (R1/R3b, Rol-1 ruling 2026-09-06, brief-uydurma-say-3): bu ikisi
    `calistir` düzeyinde TEK karara bağlıdır (`--bellek-kimlikleri`/`--calisma-dosyalari` ya
    verilir ya verilmez, sayfa başına DEĞİŞMEZ) — ilk sayfanın durumuna bakmak yeterlidir, karışık
    (bir sayfada dict bir sayfada `None`) durum hiç OLUŞMAZ."""
    toplam = 0
    dogrulanan = 0
    sinif_bazinda = {sinif: {"toplam": 0, "dogrulanan": 0, "dogrulanamayan": []}
                     for sinif in SINIF_SIRASI}
    sinif_bazinda["yol"]["dogrulanan_tam"] = 0
    sinif_bazinda["yol"]["dogrulanan_ad"] = 0
    sinif_bazinda["yol"]["ad_eslesmeleri"] = {}

    bellek_aktif = bool(sayfa_sonuclari) and sayfa_sonuclari[0]["sinif_bazinda"].get("bellek") is not None
    if bellek_aktif:
        sinif_bazinda["bellek"] = {"toplam": 0, "dogrulanan": 0, "dogrulanamayan": []}
    else:
        sinif_bazinda["bellek"] = None
        sinif_bazinda["bellek_neden"] = "bellek kimlik listesi verilmedi"

    calisma_aktif = bool(sayfa_sonuclari) and sayfa_sonuclari[0]["sinif_bazinda"].get("calisma_dosyasi") is not None
    if calisma_aktif:
        sinif_bazinda["calisma_dosyasi"] = {"toplam": 0, "dogrulanan": 0, "dogrulanamayan": []}
    else:
        sinif_bazinda["calisma_dosyasi"] = None
        sinif_bazinda["calisma_dosyasi_neden"] = "çalışma dosyası listesi verilmedi"

    dogrulanamayan_liste: list[dict] = []
    for s in sayfa_sonuclari:
        toplam += s["toplam"]
        dogrulanan += s["dogrulanan"]
        for sinif, veri in s["sinif_bazinda"].items():
            if veri is None or sinif.endswith("_neden"):
                continue  # bellek/calisma_dosyasi liste verilmediyse: None + ayrı '_neden' alanı
            sinif_bazinda[sinif]["toplam"] += veri["toplam"]
            sinif_bazinda[sinif]["dogrulanan"] += veri["dogrulanan"]
            sinif_bazinda[sinif]["dogrulanamayan"].extend(
                {"sayfa": s["id"], "atif": a} for a in veri["dogrulanamayan"])
            if sinif == "yol":
                sinif_bazinda["yol"]["dogrulanan_tam"] += veri.get("dogrulanan_tam", 0)
                sinif_bazinda["yol"]["dogrulanan_ad"] += veri.get("dogrulanan_ad", 0)
                for atif, yollar in veri.get("ad_eslesmeleri", {}).items():
                    sinif_bazinda["yol"]["ad_eslesmeleri"].setdefault(atif, yollar)
        dogrulanamayan_liste.extend({"sayfa": s["id"], **d} for d in s["dogrulanamayan"])
    oran = (dogrulanan / toplam) if toplam else None
    oran_neden = (None if toplam
                 else "hiçbir sayfada depo atıfı bulunamadı — toplam oran tanımsız, uydurulamaz")
    return {"toplam": toplam, "dogrulanan": dogrulanan,
            "oran": round(oran, 6) if oran is not None else None,
            "oran_neden": oran_neden, "sinif_bazinda": sinif_bazinda,
            "dogrulanamayan": dogrulanamayan_liste}


# ======================================================================================
# UÇTAN-UCA — `calistir` (CLI'nin de çağırdığı GERÇEK gövde)
# ======================================================================================

def calistir(*, sayfa_dizin, repo, bellek_kimlikleri=None, calisma_dosyalari=None) -> dict:
    """`bellek_kimlikleri`/`calisma_dosyalari` (R1/R3b, brief-uydurma-say-3): `None` (varsayılan)
    ise ilgili sınıf raporda `None`+`_neden` kalır (eski davranış). Bir yol verilmişse dosya
    satır-satır okunur (`_satir_listesi_oku`) ve TÜM sayfalara AYNI küme uygulanır."""
    sayfa_dizin = pathlib.Path(sayfa_dizin)
    repo = pathlib.Path(repo)
    hata_biriktirici: list[str] = []

    sayfalar_ham = sayfalari_yukle(sayfa_dizin)
    ls_kume, ls_hata = ls_files_getir(repo)
    if ls_hata:
        hata_biriktirici.append(ls_hata)

    roadmap_yolu = repo / "ROADMAP.md"
    roadmap_metni = roadmap_yolu.read_text(encoding="utf-8") if roadmap_yolu.exists() else None

    bellek_kume = _satir_listesi_oku(bellek_kimlikleri) if bellek_kimlikleri is not None else None
    calisma_kume = _satir_listesi_oku(calisma_dosyalari) if calisma_dosyalari is not None else None

    sayfa_sonuclari = [sayfa_olc(sayfa, repo, ls_kume, roadmap_metni, hata_biriktirici,
                                  bellek_kume=bellek_kume, calisma_dosyalari_kume=calisma_kume)
                       for sayfa in sayfalar_ham]
    toplam = _toplami_hesapla(sayfa_sonuclari)

    return {
        "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "girdi": {"sayfa_dizin": str(sayfa_dizin), "repo": str(repo),
                  "n_sayfa": len(sayfa_sonuclari),
                  "sayfa_dosyalari": [s["kaynak_dosya"] for s in sayfa_sonuclari]},
        "sayfalar": {s["id"]: s for s in sayfa_sonuclari},
        "toplam": toplam,
        "hata": sorted(set(hata_biriktirici)),
        "beyan": ("Bu betik HÜKÜM VERMEZ — eşik (kart EDG-2026-083 'esikler' alanı) burada GEÇMEZ, "
                 "Rol-1'in ayrı hükmüdür. 'yol' sınıfı git ls-files kümesine, 'sha' git cat-file'a "
                 "bağlıdır; ikisi de --repo kökünde SALT-OKUNUR çalışır, ağa çıkılmaz. "
                 "yol: dizinsiz atıf basename eşleşmesiyle doğrulanır (Rol-1 ruling 2026-09-06, "
                 "ölçümden önce). R1-R3 (brief-uydurma-say-3, 2026-09-06): kalem TSK-NNN "
                 "ROADMAP.md metninde HERHANGİ biçimde (köşeli parantez şart DEĞİL) geçiyorsa "
                 "doğrulanmıştır; bellek --bellek-kimlikleri verilmişse bir sha adayı önce bu "
                 "kümede önek aranarak doğrulanır (eşleşmezse eski sha yolu); calisma_dosyasi "
                 "--calisma-dosyalari verilmişse depoda bulunamayan dizinsiz bir yol atıfının "
                 "basename'i bu listede varsa doğrulanmıştır (depo dışı ama gerçek) — ikisi de "
                 "liste verilmezse None + neden kalır."),
    }


# ======================================================================================
# MARKDOWN RAPOR (isteğe bağlı `--markdown`)
# ======================================================================================

def markdown_uret(sonuc: dict) -> str:
    def _oran_metni(veri: dict) -> str:
        if veri["oran"] is None:
            return f"None ({veri['oran_neden']})"
        return f"{veri['oran']:.2%}"

    satirlar = ["# EDG-2026-083 — uydurma sayacı sonucu", "",
               f"Ölçüm zamanı: {sonuc['olcum_zamani']}",
               f"Sayfa dizini: `{sonuc['girdi']['sayfa_dizin']}`  ·  Repo: `{sonuc['girdi']['repo']}`",
               "", "| Sayfa | Toplam | Doğrulanan | Oran |", "|---|---|---|---|"]
    for sid, s in sorted(sonuc["sayfalar"].items()):
        satirlar.append(f"| {sid} | {s['toplam']} | {s['dogrulanan']} | {_oran_metni(s)} |")
    t = sonuc["toplam"]
    satirlar.append(f"| **TOPLAM** | {t['toplam']} | {t['dogrulanan']} | {_oran_metni(t)} |")
    satirlar += ["", "## Sınıf bazında (toplam)", "", "| Sınıf | Toplam | Doğrulanan |", "|---|---|---|"]
    for sinif in SINIF_SIRASI:
        veri = t["sinif_bazinda"][sinif]
        satirlar.append(f"| {sinif} | {veri['toplam']} | {veri['dogrulanan']} |")
    if sonuc.get("hata"):
        satirlar += ["", "## Hata (Yasa 4 — sessizce yutulmadı)"]
        satirlar += [f"- {h}" for h in sonuc["hata"]]
    return "\n".join(satirlar) + "\n"


# ======================================================================================
# CLI — `--sayfa-dizin`/`--repo`/`--cikti`/`--markdown` (ops sözleşmesi KOMUT SATIRIdır)
# ======================================================================================

def ana(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sayfa-dizin", required=True)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--cikti", required=True)
    ap.add_argument("--markdown", default=None)
    ap.add_argument("--bellek-kimlikleri", default=None,
                    help="R1: satır başına bir Hindsight bellek kimliği (tam uuid ya da hex)")
    ap.add_argument("--calisma-dosyalari", default=None,
                    help="R3b: satır başına bir dosya adı (A1 state/+backups/+/opt/veri, dondurulmuş)")
    ns = ap.parse_args(argv)

    sonuc = calistir(sayfa_dizin=ns.sayfa_dizin, repo=ns.repo,
                     bellek_kimlikleri=ns.bellek_kimlikleri,
                     calisma_dosyalari=ns.calisma_dosyalari)

    cikti_yolu = pathlib.Path(ns.cikti)
    cikti_yolu.parent.mkdir(parents=True, exist_ok=True)
    cikti_yolu.write_text(json.dumps(sonuc, indent=2, sort_keys=True, ensure_ascii=False),
                          encoding="utf-8")

    if ns.markdown:
        md_yolu = pathlib.Path(ns.markdown)
        md_yolu.parent.mkdir(parents=True, exist_ok=True)
        md_yolu.write_text(markdown_uret(sonuc), encoding="utf-8")

    t = sonuc["toplam"]
    oran_str = f"{t['oran']:.4f}" if t["oran"] is not None else "None"
    print(f"yazildi: {cikti_yolu} — sayfa={sonuc['girdi']['n_sayfa']} toplam_atif={t['toplam']} "
          f"dogrulanan={t['dogrulanan']} oran={oran_str} hata_n={len(sonuc['hata'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(ana())
