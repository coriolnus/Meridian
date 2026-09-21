"""test_gecici_artik_kabuk_copytree_v531.py — TSK-209c (2026-09-21): TSK-209b'nin kapattığı
GEÇİCİ ARTIK ailesini (`tmp*.tmp`, `.secrets_*.tmp`) tanımayan İKİ YÜZEY kapanır.

TSK-209b sınıflandırmayı `config`e (tek kaynak) taşıdı ve iki PYTHON yüzeyini (kum havuzu KÖKÜ +
teşhis paketi) ona bağladı. Ardında iki delik kaldı ve ikisi de AYNI sınıftır — "aynı gerçeği bilen
kod ile bilmeyen kod yan yana duruyor":

  (A) KABUK YÜZEYİ. `deploy/oracle-a1/meridian-backup.service` gece arşivini `tar` ile alır ve
      dışlama listesi TSK-197'de `state/secrets.json.bak-*` ailesini öğrenmişti; atomik yazımın
      artıklarını öğrenmedi. Yani `state/.secrets_ab12.tmp` biçimli bir artık — İÇERİĞİ operatör
      anahtar deposudur — gece arşivine girerdi. Arşiv PAYLAŞILABİLİR bir artefakttır (restore
      tatbikatı, teşhis), yani buradaki sınıf BOYUT değil MARUZİYETTİR.
  (B) DERİNLİK YÜZEYİ. `sprint._kur_kum_havuzu` KÖK girdilerini `_atlanir` ile süzüyordu, ama
      dizinleri `shutil.copytree(...)` ile İÇİ SÜZÜLMEDEN kopyalıyordu. Yani kökteki bir artık
      atlanırken `state/<altdizin>/tmpab12.tmp` biçimli kardeşi kum havuzuna giriyordu
      (TSK-209b'nin BEYANLI boşluğu).

ÖLÇÜLMÜŞ ZEMİN — bu turda koddan ve canlıdan okundu, hiçbir GERÇEK sır değeri açılmadan.
  * Canlı `state/` alt dizinlerinde (derinlik 2–3, sprint/bars hariç) bu ailelere uyan TEK ad
    `.locks/auth.json.lock`tur (Rol-1, A1 salt-okur, 2026-09-21 19:3xZ) — `auth.json*` deseniyle
    eşleşir, yani (B)'nin süzgeci onu ATLAR. ATLAMANIN ZARARSIZ OLDUĞU ÖLÇÜLDÜ, VARSAYILMADI:
    `store._FileLock.acquire` kilit DİZİNİNİ `mkdir(parents=True, exist_ok=True)` ile, kilit
    DOSYASINI `os.open(..., O_CREAT)` ile yokluğunda KENDİSİ yaratır — çocuk kendi kilidini açar.
    Çivi 5b/5c bu ölçümü kaynaktan ve davranıştan alır; ölçüm bir gün değişirse `.locks/` süzgeçten
    MUAF tutulmalıdır ve çivi o gün kırmızıya döner.
  * `sprint._reset_sandbox_state` `history/` ağacını `shutil.rmtree` ile SİLİP yeniden kurar. Bu
    yüzden bu dosyanın hiçbir çivisi `history/` altında ölçüm yapmaz: orada "kopyalanmadı" iddiası
    süzgeçten değil SIFIRLAMADAN gelirdi ve çivi yanlış sebeple yeşil kalırdı (bu deponun bir turda
    dört kez ölçtüğü sınıf). Ölçüm `quarantine/` ve `.locks/` altında yapılır — ikisi de canlıda
    VARDIR (yerel `state/` kökü, 2026-09-21) ve ikisine de sıfırlama dokunmaz.

NE ÇİVİLENİR
  1. Yedek birimi artık ailesini `--exclude` ile tanır — örnek adlar `config` desenlerinden
     TÜRETİLİR (elle liste yok): aileye bir üye eklenirse birim de öğrenmek zorundadır.
  2. BEDEL: birim kanonik sır defterlerini (`secrets.json`, `auth.json`) ve sıradan defterleri
     dışlamaya BAŞLAMAZ — gece yedeğinin İŞİ sırları kurtarmaktır (sprint'in işiyle bilerek ayrışır;
     v523 çivi 7 aynı ayrımı ters yönde tarif eder).
  3. Alt dizindeki artıklar kum havuzuna GİRMEZ (bugünkü kırmızı) ...
  3b. ... ama alt dizindeki MEŞRU dosyalar girmeye DEVAM eder ve artık ADLI bir DİZİN atlanmaz
     (bedel yasası: süzgeç yalnız DOSYA adlarına bakar, dizin adı eşleşmesi ölçülmedi).
  4. Atlama İZ bırakır: olay `alt_dizin_atlanan` alanını taşır; alt dizinde artık yokken alan boş.
  5. `.locks/auth.json.lock` atlanır, BİLDİRİLİR ve atlamanın zararsızlığı ÖLÇÜLÜR.
  6/7. Süzgeç tek kaynağa bağlıdır ve kendi eşleştiricisini yazmaz (daraltma sınırı ayrıca ölçülür).
  8. Birim başlığı TSK-209c beyanını BEDEL kalemiyle taşır.

CANLIYA DOKUNMAZ: dosya sistemi işlerinin tamamı `sandbox_state`in tmp ağacındadır; birim dosyası
yalnız METİN olarak okunur (çalıştırılmaz) ve `monkeypatch.undo()` YOKTUR.
"""
from __future__ import annotations

import ast
import inspect
import textwrap

import pytest

from meridian import auth, config, sprint, store
from tests.test_yedek_sir_kopyasi_disla_v517 import _desenler, _tar_dislar_mi

# Ölçümün yapıldığı iki CANLI alt dizin (yerel `state/` kökü, 2026-09-21): ikisi de
# `_reset_sandbox_state`in dokunmadığı ağaçlardır — `history/` BİLEREK kullanılmaz (modül şerhi).
KARANTINA = "quarantine"
KILITLER = ".locks"

# `quarantine/` altında canlıda ölçülen gerçek bir ad — "meşru dosya kopyalanmaya devam eder"
# iddiasının taşıyıcısı. Uydurma bir ad da işi görürdü; ölçülen ad, çivinin gerçek bir dosya
# sınıfını koruduğunu gösterir.
MESRU_KARANTINA = "sp500_constituents.FIXTURE-2026-07-18.json"
#: `.locks/` altında artık ailesine UYMAYAN bir kilit adı: aynı dizinde negatif kontrol.
MESRU_KILIT = "portfolio.json.lock"
#: Canlıda ölçülen TEK eşleşen alt dizin adı (`auth.json*` ailesi).
CANLI_KILIT = "auth.json.lock"

#: Artıkların içeriği yerine kullanılan NİŞAN — kum havuzunda ya da olay kaydında görünürse sızıntı.
NISAN = "V531-SIZINTI-NISANI"


def _ornek_ad(desen: str, jeton: str = "ab12cd") -> str:
    """`fnmatch` deseninden SOMUT bir örnek ad türetir (`*` → jeton, `?` → tek karakter).

    NEDEN TÜRETİLİR, NEDEN ELLE YAZILMAZ: desen ailesi `config`te tek kaynaktır ve bu dosya onun
    TÜKETİCİSİDİR. Örnek adları elle yazmak ikinci bir (sessizce bayatlayan) tanım açardı: aileye
    yeni bir desen girdiği gün bu çivi onu görmez ve "birim aileyi tanıyor" iddiası kapsamını
    kaybederdi. Türetilen adın gerçekten aileye ait olduğu her kullanımda AYRICA doğrulanır
    (`config.kopyalanmaz_mi`) — türetme kuralı bozulursa çivi kurulum çipasında düşer, sessizce
    geçmez. `jeton` parametresi aynı desenden İKİ ayrı ad üretmek içindir (dosya ↔ dizin ölçümü)."""
    return desen.replace("*", jeton).replace("?", "x")


def _artik_desenleri() -> tuple[str, ...]:
    """ATOMİK YAZIM ARTIĞI ailesinin TAMAMI, iki tek-kaynak sabitinden TÜRETİLEREK.

    Aile iki sabite BÖLÜNMÜŞTÜR ve bölünme bilinçlidir (`config.gecici_artik_mi` docstring'i):
    `.secrets_*.tmp` bir SIRDIR ve `SIR_DESENLERI`ye, `tmp*.tmp` sır DEĞİLDİR ve
    `GECICI_ARTIK_DESENLERI`ye aittir. Kabuk yüzeyi için ayrım önemsizdir — `tar` ikisini de
    dışlamak zorundadır — ama BİRLEŞTİRME KURALI ölçülebilir olmalıdır: aile, `.tmp` UZANTISIYLA
    biten desenlerdir (atomik yazımın `suffix=".tmp"` sözleşmesi; `store._atomic_write` ve
    `secrets._write_file` ikisi de bu son eki verir). Kural desen METNİNDEN okunur, elle sayılmaz:
    iki sabitten herhangi birine yeni bir `.tmp` deseni girdiği gün birim de öğrenmek zorunda
    kalır."""
    aile = tuple(d for d in (config.SIR_DESENLERI + config.GECICI_ARTIK_DESENLERI)
                 if d.endswith(".tmp"))
    assert aile, ("kurulum çipası: `config` sabitlerinde `.tmp` ile biten desen YOK — ya aile "
                  "boşaltıldı ya da atomik yazımın son ek sözleşmesi değişti; bu dosyanın türetme "
                  "kuralı artık hiçbir şey ölçmüyor")
    return aile


def _kum_havuzu(sid: str = "20990101-000000"):
    return sprint._kur_kum_havuzu(sid) / "state"


def _olaylar() -> list[dict]:
    return [e for e in store.read_jsonl("events.jsonl")
            if e.get("event") == "sprint_kum_havuzu_atlandi"]


def _canli_state_kur(alt_dizin_artiklari: bool = True) -> None:
    """Sentetik CANLI `state/` ağacı: iki alt dizin, içlerinde meşru dosyalar ve (istenirse) artıklar.

    `sandbox_state` `config.STATE`i tmp'ye çevirmiş ve `history/`+`bars/` dizinlerini kurmuştur;
    buraya yalnız bu turun ölçtüğü girdiler eklenir. KÖK seviyesine artık KONMAZ — kökü TSK-209b
    (v530) zaten ölçüyor ve buradaki iddia DERİNLİKTİR; kök artığı eklemek, alt dizin süzgeci hiç
    kurulmasa bile olay kaydını doldurup 4. çiviyi yanlış sebeple yeşile çevirirdi.

    `.locks/auth.json.lock` DE BURADA DOĞMAZ (yalnız 5a onu GERÇEK yoldan doğurur): her ağaçta var
    olsaydı 4b'nin "alan boş" ölçümü hiçbir zaman boş olamazdı."""
    live = config.STATE
    (live / "portfolio.json").write_text('{"positions":{},"realized_pnl":0.0}')

    kar = live / KARANTINA
    kar.mkdir(exist_ok=True)
    (kar / MESRU_KARANTINA).write_text('{"v531":"mesru-karantina-defteri"}')

    kil = live / KILITLER
    kil.mkdir(exist_ok=True)
    (kil / MESRU_KILIT).write_text("")

    if alt_dizin_artiklari:
        for desen in _artik_desenleri():
            ad = _ornek_ad(desen)
            assert config.kopyalanmaz_mi(ad), (
                f"kurulum çipası: `{desen}` deseninden türetilen `{ad}` tek kaynağa göre "
                f"kopyalanmaz DEĞİL — türetme kuralı bozuk, çivi hiçbir şey ölçmüyor")
            (kar / ad).write_text('{"icerik":"%s"}' % NISAN)


# ==================================================================================================
# 1 — KABUK YÜZEYİ: yedek birimi atomik yazım artığı ailesini DIŞLAR (bugünkü kırmızı)
# ==================================================================================================
def test_1_yedek_birimi_atomik_yazim_artik_ailesini_dislar():
    """AYRIŞMA ÇİVİSİ, TERS YÖN. v523 çivi 7 "yedeğin dışladığı sır-yedeği ailesini sprint de
    atlıyor mu" diye TEK YÖNLÜ sorar; burası eksik kalan yönü kapatır: `config`in tanıdığı atomik
    yazım artığı ailesini KABUK yüzeyi de tanıyor mu?

    Tek-kaynak yasası burada tek gövdeyi MÜMKÜN KILMAZ (biri systemd `tar` argümanı, diğeri Python
    `fnmatch` sabiti), o yüzden yasanın istisnası uygulanır: kopya kaçınılmaz → ayrışma çivisi.
    Örnek adlar `config` desenlerinden TÜRETİLİR, yani aileye yeni bir üye girdiği gün burası
    kırmızıya döner ve birim ExecStart'ı onunla birlikte tartılır.

    DIŞLAMA `state/` ÇAPALIDIR ve bu DARALTMA ÖLÇÜLMÜŞTÜR: her iki artık da `tempfile.mkstemp`
    tarafından `state/` KÖKÜNDE doğar (`store._atomic_write` `dir=` olarak state kökünü verir,
    `secrets._write_file` aynısını yapar). Çapasız bir desen tüm ağaçta eşleşirdi; bugün ölçülmüş
    bir ihtiyaç yok ve geniş desen yedeği sessizce EKSİK doğurma sınıfına girer (bedel yasası).
    Kum havuzu tarafı derinliğe iner, çünkü ORADA ölçülmüş bir ad vardır (`.locks/auth.json.lock`)."""
    birim_desenleri = _desenler()
    for desen in _artik_desenleri():
        uye = "state/" + _ornek_ad(desen)
        assert _tar_dislar_mi(uye, birim_desenleri), (
            f"`{uye}` gece arşivine GİRİYOR — `config` bu adı atomik yazımın artığı sayar "
            f"(`{desen}`) ve içeriği yazılan defterin kendisidir (operatör anahtar deposu ya da "
            f"pano oturum imza anahtarı olabilir); arşiv paylaşılabilir bir artefakttır. "
            f"`meridian-backup.service` ExecStart'ı aileyi tanımıyor: {birim_desenleri!r}")


# ==================================================================================================
# 2 — BEDEL: dışlama DAR — yedeğin İŞİ sırları kurtarmaktır
# ==================================================================================================
def test_2_yedek_birimi_kanonik_sir_defterlerini_ve_siradan_defteri_dislamaz():
    """BEDEL ÖLÇÜMÜ (bedel yasası). 1. çivi arşivden bir şey ÇIKARIYOR; bu çivi ne
    KAYBEDİLMEDİĞİNİ ölçer. İki yüzeyin sözleşmesi BİLEREK ayrışır (v523 çivi 7'nin beyanı): gece
    yedeği canlı `secrets.json`/`auth.json`ı arşive ALIR — yedeğin işi sırları kurtarmaktır —
    sprint onları ATAR, çünkü kum havuzunun işi sırdan uzak durmaktır. Bu tur ilkini DEĞİŞTİRMEZ.

    Kanonik adlar `config.SIR_TAM_ADLAR`dan okunur: tek kaynağa yeni bir sır defteri girerse
    "yedek onu da arşivliyor mu" sorusu kendiliğinden sorulur."""
    birim_desenleri = _desenler()
    for ad in sorted(config.SIR_TAM_ADLAR) + ["portfolio.json"]:
        uye = "state/" + ad
        assert not _tar_dislar_mi(uye, birim_desenleri), (
            f"`{uye}` gece arşivinden DÜŞTÜ — eklenen desen GENİŞ. Yedeğin işi sırları ve "
            f"defterleri kurtarmaktır; artık dışlaması yalnız `.tmp` son ekli GEÇİCİ adları "
            f"kapsamalıdır: {birim_desenleri!r}")


# ==================================================================================================
# 3 — DERİNLİK YÜZEYİ: alt dizindeki artıklar kum havuzuna GİRMEZ (bugünkü kırmızı)
# ==================================================================================================
def test_3_alt_dizindeki_artiklar_kum_havuzuna_girmez(sandbox_state):
    """BUGÜNKÜ KIRMIZI. Kök girdileri `_atlanir`dan geçiyordu ama dizinler `shutil.copytree` ile
    İÇİ SÜZÜLMEDEN kopyalanıyordu — TSK-209b'nin kendi beyanındaki boşluk. Ailenin alt dizinde
    GERÇEKTEN doğabildiğinin kanıtı canlıda ölçülmüş `.locks/auth.json.lock`tur (çivi 5a).

    İÇERİK DE ÖLÇÜLÜR: adın atlanması yetmez, artığın GÖVDESİ de kum havuzunda hiçbir yerde
    olmamalıdır — kopya başka bir adla sızmışsa nişan bulunur."""
    _canli_state_kur()
    sb = _kum_havuzu()
    for desen in _artik_desenleri():
        ad = _ornek_ad(desen)
        assert not (sb / KARANTINA / ad).exists(), (
            f"`{KARANTINA}/{ad}` kum havuzuna kopyalandı — alt dizinler `copytree` ile içi "
            f"süzülmeden kopyalanıyor; artığın içeriği yazılan defterin kendisidir")
    govdeler = [p.read_bytes() for p in sb.rglob("*") if p.is_file()]
    assert not any(NISAN.encode() in g for g in govdeler), (
        "artığın İÇERİĞİ kum havuzunda — ad atlandı ama gövde başka bir yoldan sızdı")


def test_3b_alt_dizindeki_mesru_dosyalar_ve_artik_ADLI_DIZIN_kopyalanir(sandbox_state):
    """BEDEL ÖLÇÜMÜ — süzgecin ne KAYBETTİRDİĞİ. İki ayrı daralma yönü ölçülür:

    (a) MEŞRU DOSYA: `quarantine/` ve `.locks/` altındaki normal adlar girmeye devam eder. Geniş
        bir süzgeç hiçbir testi kırmadan kum havuzunu EKSİK doğurur ve sprint sessizce yanlış
        ölçer (HALT vakasının sınıfı).
    (b) ARTIK ADLI DİZİN: süzgeç YALNIZ dosya adlarına bakar. Bir DİZİNİN adının desene uyması
        ölçülmemiş bir durumdur (canlıda örneği yok) ve dizini atlamak ALT AĞACIN TAMAMINI
        sessizce düşürürdü — ölçülmemiş bir daraltma, ölçülmüş bir kazançtan pahalıdır.

    `history/` BİLEREK KULLANILMAZ: `_reset_sandbox_state` o ağacı siler, yani oradaki bir iddia
    süzgeci değil sıfırlamayı ölçerdi."""
    _canli_state_kur()
    artik_dizin = _ornek_ad(_artik_desenleri()[0], jeton="dizin99")
    assert config.kopyalanmaz_mi(artik_dizin), (
        f"kurulum çipası: `{artik_dizin}` aileye uymuyor — bu çivi 'dizin adı atlanmaz' iddiasını "
        f"ölçemiyor")
    d = config.STATE / KARANTINA / artik_dizin
    d.mkdir()
    (d / "icerik.json").write_text('{"v531":"artik-adli-dizinin-icindeki-mesru-dosya"}')

    sb = _kum_havuzu()
    assert (sb / KARANTINA / MESRU_KARANTINA).exists(), (
        f"`{KARANTINA}/{MESRU_KARANTINA}` kum havuzuna GİRMEDİ — süzgeç meşru bir defteri yuttu")
    assert (sb / KILITLER / MESRU_KILIT).exists(), (
        f"`{KILITLER}/{MESRU_KILIT}` kum havuzuna GİRMEDİ — süzgeç artık ailesine uymayan bir "
        f"kilit adını da atıyor")
    assert (sb / KARANTINA / artik_dizin / "icerik.json").exists(), (
        f"`{KARANTINA}/{artik_dizin}` bir DİZİNDİR ve alt ağacıyla birlikte düştü — süzgeç dizin "
        f"adlarına da bakıyor; bu daraltma ölçülmedi ve alt ağacın tamamını sessizce yok eder")


# ==================================================================================================
# 4 — BEDEL YASASI: alt dizin atlaması İZ bırakır
# ==================================================================================================
def test_4_olay_alt_dizin_atlananlari_ADIYLA_tasir_icerik_tasimaz(sandbox_state):
    """Kum havuzu bir dosyayı atladığında tek iz `sprint_kum_havuzu_atlandi` olayıdır. Kök bacağı
    (`adlar`) TSK-208'den beri bildiriliyor; ALT DİZİN bacağı bu turda doğdu ve bildirilmezse
    kopyalanmayan dosya izsiz yok olur — desen bir gün meşru bir defteri yakalarsa körlük sessiz
    kalır.

    TABAN AD DEĞİL YOL YAZILIR (conftest `_CanliYazimKaydi` emsali): `bars/` ile `bars_intraday/`
    aynı adlı dosyalar barındırır, yani salt taban ad operatöre "hangi dizinden düştü" sorusunu
    cevaplamaz. İÇERİK/DEĞER/HASH ASLA yazılmaz: olay defteri panoya ve `ops/` sorgularına açıktır.

    OLAY TEK KALIR: iki bacak AYNI satırda raporlanır (ikinci bir olay satırı v530 çivi 6'nın
    'tam bir kez' iddiasını kırardı ve iki bacağı ayrı zaman damgalarına dağıtırdı)."""
    _canli_state_kur()
    _kum_havuzu()
    olaylar = _olaylar()
    assert len(olaylar) == 1, (
        f"alt dizinde dosya atlandı ama bilgi olayı TAM BİR kez yazılmadı ({len(olaylar)}) — "
        f"atlama sessiz, körlük ölçülemez")
    kayit = olaylar[0]
    alt = kayit.get("alt_dizin_atlanan", [])
    for desen in _artik_desenleri():
        yol = f"{KARANTINA}/{_ornek_ad(desen)}"
        assert yol in alt, (
            f"`{yol}` atlandı ama olayda YOK — adı `mkstemp` üretir, kodda YAZILI DEĞİLDİR; "
            f"bildirilmezse hiçbir iz kalmaz: {kayit!r}")
    assert f"{KILITLER}/{MESRU_KILIT}" not in alt, (
        f"`{MESRU_KILIT}` atlanan olarak bildirilmiş — atlanmaması gerekiyordu: {kayit!r}")
    assert NISAN not in str(kayit), f"olay kaydı dosya İÇERİĞİ taşıyor: {kayit!r}"


def test_4b_alt_dizinde_artik_yokken_alan_bos(sandbox_state):
    """AYIRT ETME GÜCÜ. Alan her kurulumda dolu görünseydi "bu gece alt dizinden bir şey düştü mü"
    sorusu cevapsız kalırdı. Burada KÖKTE bir artık vardır (olay YAZILIR) ama alt dizinlerde
    YOKTUR — yani alanın boşluğu gerçekten ölçülür. Olayı hiç yazdırmayan bir kurgu bu iddiayı
    ölçemezdi (vakum yeşili)."""
    _canli_state_kur(alt_dizin_artiklari=False)
    kok_artigi = _ornek_ad(config.GECICI_ARTIK_DESENLERI[0])
    (config.STATE / kok_artigi).write_text('{"icerik":"%s"}' % NISAN)
    _kum_havuzu()

    olaylar = _olaylar()
    assert len(olaylar) == 1, (
        f"kökte artık varken olay TAM BİR kez yazılmadı ({len(olaylar)}) — kurulum çipası düştü")
    kayit = olaylar[0]
    assert kok_artigi in kayit.get("adlar", []), (
        f"kurulum çipası: kök artığı bildirilmemiş, bu çivi yanlış olayı ölçüyor: {kayit!r}")
    assert "alt_dizin_atlanan" in kayit, (
        f"alan olayda HİÇ YOK — 'alt dizinden bir şey düşmedi' ile 'alt dizin hiç ölçülmedi' aynı "
        f"görünür; alanın VARLIĞI ölçümün yapıldığının tek kanıtıdır: {kayit!r}")
    assert kayit["alt_dizin_atlanan"] == [], (
        f"alt dizinde artık yokken alan dolu — bildirim ayırt etme gücünü kaybeder: {kayit!r}")


# ==================================================================================================
# 5 — CANLIDA ÖLÇÜLEN TEK EŞLEŞME: `.locks/auth.json.lock` ve atlamanın BEDELİ
# ==================================================================================================
def test_5a_canli_kilit_dosyasi_atlanir_ve_bildirilir(sandbox_state):
    """ÖLÇÜLMÜŞ VAKA (Rol-1, A1 salt-okur, 2026-09-21 19:3xZ): canlı `state/` alt dizinlerinde bu
    ailelere uyan TEK ad `.locks/auth.json.lock`tur ve `auth.json*` deseniyle eşleşir. Süzgeç onu
    ATLAR — beyan edilir, gizlenmez (5b/5c zararsızlığı ölçer).

    Dosya GERÇEK YOLDAN doğar (`auth.set_password` → `store.write_text` → `file_lock`): elle bir
    `.lock` dosyası yazmak adın ŞEKLİNİ taklit ederdi ama kilit yolunun onu gerçekten ürettiğini
    göstermezdi."""
    _canli_state_kur(alt_dizin_artiklari=False)
    auth.set_password("v531-sentetik-parola")
    assert (config.STATE / KILITLER / CANLI_KILIT).exists(), (
        "kurulum çipası: kilit dosyası gerçek yoldan doğmadı — `store.file_lock` yerleşimi "
        "değişmiş olabilir, bu çivi canlıda ölçülen adı artık ölçmüyor")

    sb = _kum_havuzu()
    assert not (sb / KILITLER / CANLI_KILIT).exists(), (
        f"`{KILITLER}/{CANLI_KILIT}` kum havuzuna kopyalandı — `auth.json*` ailesindendir")
    alt = _olaylar()[0].get("alt_dizin_atlanan", [])
    assert f"{KILITLER}/{CANLI_KILIT}" in alt, (
        f"canlıda ölçülen TEK eşleşme atlandı ama bildirilmedi — beyansız atlama: {alt!r}")


def test_5b_kilit_dosyasi_yoklugunda_kendini_yaratir_kaynak_olcumu():
    """ATLAMANIN ZARARSIZLIĞI BİR İDDİA DEĞİL ÖLÇÜMDÜR (uydurma yasağı). Kum havuzu çocuğu kendi
    `MERIDIAN_ROOT`uyla koşar; kilit dosyası kopyalanmadıysa çocuk onu bulamayacak mı?

    KAYNAK ÖLÇÜMÜ: `store._FileLock.acquire` kilit DİZİNİNİ `mkdir` ile, kilit DOSYASINI `os.open`
    çağrısına verilen `O_CREAT` bayrağıyla yokluğunda KENDİSİ yaratır.

    BUGÜN YEŞİLDİR VE BU BEYAN EDİLİR: çivi bir arızayı düzeltmez, `.locks/` muafiyetinin GEREKSİZ
    olduğu hükmünü ölçülebilir kılar. Ölçüm bir gün değişirse (tembel yaratma kaldırılır, `O_CREAT`
    düşerse) kırmızıya döner ve `.locks/` süzgeçten MUAF tutulmalıdır — karar o zaman yeniden
    tartılır. `textwrap.dedent` ZORUNLUDUR: `acquire` bir METOTtur, kaynağı girintilidir."""
    kaynak = ast.parse(textwrap.dedent(inspect.getsource(store._FileLock.acquire)))
    bayraklar = {d.attr for d in ast.walk(kaynak)
                 if isinstance(d, ast.Attribute) and d.attr.startswith("O_")}
    assert "O_CREAT" in bayraklar, (
        f"`store._FileLock.acquire` kilit dosyasını `O_CREAT` ile açmıyor — kopyalanmayan bir "
        f"kilit dosyası çocukta yeniden doğmaz ve `.locks/` süzgeçten muaf tutulmalıdır: "
        f"{sorted(bayraklar)!r}")
    assert any(isinstance(n, ast.Attribute) and n.attr == "mkdir" for n in ast.walk(kaynak)), (
        "`store._FileLock.acquire` kilit DİZİNİNİ kendisi kurmuyor — kum havuzunda `.locks/` hiç "
        "doğmazsa kilit yolu düşer")


def test_5c_kilit_dosyasi_bos_agacta_gercekten_dogar(sandbox_state):
    """5b'nin DAVRANIŞ kardeşi: kaynak okuması ne YAZDIĞINI söyler, bu çivi ne YAPTIĞINI ölçer.
    Kum havuzu çocuğunun durumu birebir taklit edilir — `.locks/` dizini hiç yokken kilit alınır."""
    kilit_dizini = config.STATE / KILITLER
    assert not kilit_dizini.exists(), "kurulum çipası: sandbox ağacında `.locks/` zaten var"
    ad = "v531_kilit_olcumu.json"
    with store.file_lock(ad):
        pass
    assert (kilit_dizini / (ad + ".lock")).exists(), (
        "kilit dosyası yokluğunda doğmadı — kum havuzuna kopyalanmayan `.locks/auth.json.lock` "
        "çocukta yeniden yaratılmaz ve atlama ZARARSIZ DEĞİLDİR")


# ==================================================================================================
# 6 — SÜZGEÇ TEK KAYNAĞA BAĞLI (v530 çivi 5b deseninin derinlik kardeşi)
# ==================================================================================================
def test_6_tek_kaynagi_oynatmak_alt_dizin_suzgecini_de_oynatir(sandbox_state, monkeypatch):
    """Süzgeç sınıflandırmayı ÇAĞRI ANINDA tek kaynaktan mı soruyor, yoksa kendi yerel desen
    kopyasından mı? `MESRU_KARANTINA` BİLEREK seçildi: 3b onun kopyalandığını ölçüyor, yani
    buradaki dışlanma yalnızca monkeypatch'ten gelebilir. Aynı anda türetilmiş artık adı GERİ
    GELMELİDİR — tek kaynak boşaltıldığında davranışın da boşalması, desenin gerçekten taşıyıcı
    olduğunu gösterir."""
    artik_ad = _ornek_ad(config.GECICI_ARTIK_DESENLERI[0])
    monkeypatch.setattr(config, "SIR_DESENLERI", (MESRU_KARANTINA,))
    monkeypatch.setattr(config, "GECICI_ARTIK_DESENLERI", ())
    monkeypatch.setattr(sprint, "SKIP_COPY_PATTERNS", config.SIR_DESENLERI)

    live = config.STATE
    (live / KARANTINA).mkdir(exist_ok=True)
    (live / KARANTINA / MESRU_KARANTINA).write_text('{"v531":"mesru"}')
    (live / KARANTINA / artik_ad).write_text('{"v531":"artik"}')

    sb = _kum_havuzu()
    assert not (sb / KARANTINA / MESRU_KARANTINA).exists(), (
        "tek kaynağa eklenen desen ALT DİZİNDE hüküm doğurmadı — süzgeç desenlerin İKİNCİ bir "
        "tanımını taşıyor (tek-kaynak yasası)")
    assert (sb / KARANTINA / artik_ad).exists(), (
        "tek kaynak artık desenini KAYBETTİĞİ hâlde dosya hâlâ atlanıyor — süzgeç deseni kendi "
        "gövdesine kopyalamış, çivi yanlış sebeple yeşil kalırdı")


# ==================================================================================================
# 7 — KARAR TEK YERDE: süzgeç kendi eşleştiricisini yazmaz
# ==================================================================================================
def test_7_alt_dizin_suzgeci_bilesik_yuklemi_cagirir():
    """KAYNAK DENETİMİ (v530 çivi 5a emsali). Üçüncü bir yüzey doğdu (kök, teşhis paketi, ve artık
    ALT DİZİN) ve üçü de aynı soruyu sorar. Süzgeç `fnmatch`i kendi gövdesinde çağırırsa karar
    ÇATALLANIR ve bir sonraki aile yalnız iki yüzeyde öğrenilir — TSK-209'da ölçülen ayrışmanın ta
    kendisi."""
    govde = inspect.getsource(sprint._alt_dizin_suzgeci)
    assert "config.kopyalanmaz_mi(" in govde, (
        "alt dizin süzgeci bileşik yüklemi çağırmıyor — üçüncü bir sınıflandırma tanımı doğdu")
    assert "fnmatch" not in govde, (
        "alt dizin süzgeci kendi desen eşleştiricisini kuruyor — karar tek yerde durmuyor")


@pytest.mark.parametrize("ad", ["portfolio.json", "trades.jsonl", "goal.yaml", "v0001.yaml",
                                "scoreboard-2026-09-21.json", "template.json", "tmp_notlar.md"])
def test_7b_suzgec_mesru_adlari_yakalamaz(ad):
    """SAF YÜZEY: süzgecin kararı dosya sistemi kurulmadan da ölçülür. Adlar v530'un daraltma
    sınırından ve sıradan defter adlarından gelir; biri yakalanırsa süzgeç GENİŞ yazılmıştır."""
    assert not config.kopyalanmaz_mi(ad), f"`{ad}` alt dizin süzgecinde yakalanıyor — daraltma"


# ==================================================================================================
# 8 — BİRİM BAŞLIĞINDA TSK-209c BEYANI (varlık çivisi, v517 çivi 6 deseni)
# ==================================================================================================
def test_8_birim_basliginda_tsk209c_beyani_bedel_ile():
    """Birim dosyasındaki her dışlama bu depoda GEREKÇESİYLE birlikte yaşar: `--exclude` bir gün
    "neden buradaydı" sorusuna cevap veremezse ilk temizlikte düşer. Beyan BEDELİ de taşımak
    zorundadır — neyin arşivde KALDIĞI, neyin çıktığı kadar önemlidir."""
    from tests.test_h3_tur2_v174 import _metin
    basliklar = []
    for satir in _metin("meridian-backup.service").splitlines():
        if satir.strip() == "[Unit]":
            break
        basliklar.append(satir)
    baslik = "\n".join(basliklar)
    assert "TSK-209c" in baslik, "meridian-backup.service: başlıkta TSK-209c beyanı yok"
    beyan = baslik[baslik.index("TSK-209c"):]
    for sozcuk in ("BEDEL", "secrets.json"):
        assert sozcuk in beyan, (
            f"meridian-backup.service: TSK-209c beyanı `{sozcuk}` kalemini taşımıyor — dışlamanın "
            f"ne KAYBETTİRMEDİĞİ yazılı değil")
