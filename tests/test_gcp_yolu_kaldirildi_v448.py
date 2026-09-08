"""test_gcp_yolu_kaldirildi_v448 — ÖLÜ GCP YOLU GERİ GELMEZ (IaC-K5, operatör kararı 2026-09-07).

BAĞLAM. Meridian 2026-08'de GCP'den Oracle A1'e taşındı. Taşınma bittiği hâlde GCP dağıtım yolu
depoda KALDI: dokuz dosya (sağlama betiği, IAP tüneli, log-tabanlı alarm politikaları, Hermes
kurucusu, Secret Manager yazıcısı, GCS yedek/geri-yükleme çifti, TLS vekilinin yapılandırması ve
depo kökündeki `deploy.sh` — `gcloud compute scp --tunnel-through-iap` ile bir GCE VM'ine kod
iten ÇALIŞTIRILABİLİR ayak) artı `meridian.secrets` içindeki DÖRDÜNCÜ sır kanalı. Hiçbiri koşmuyordu — ama hepsi OKUNUYORDU:
belgeler onlara reçete diye atıf veriyordu, testler onları "tek kaynak" sanıp ölçüyordu ve sır
zinciri var olmayan bir buluta düşen bir basamak taşıyordu. Bu deponun baskın kusur sınıfının
(kurulu ≠ çalışır) en uzun ömürlü örneğiydi.

BU DOSYANIN ÖLÇTÜĞÜ DÖRT ŞEY, ve dördü de AYRI bir gerilemenin adı:

  Ç1  DOKUZ DOSYA YOK, VE ONLARA ATIF DA YOK — bir rebase/merge/"geri alalım" turu onları geri
      getirirse burada düşer. Silinmiş bir reçete geri geldiğinde en pahalı hâli sessiz olmasıdır:
      kimse koşmaz, ama belge yine ona atıf verir ve bir gün biri koşar. Dosyanın YOKLUĞU ile
      ADININ yokluğu AYRI iki ölçümdür ve ikincisi ilkinden sonra gelir: tur-1'de sekiz dosya
      silindi ama `deploy/monitoring.sh` adı motor kodunda DÖRT yerde jeton kararlılığının
      GEREKÇESİ olarak durmaya devam etti — var olmayan bir tüketiciye yapılan bir atıf.
  Ç2  `secrets.KAYNAKLAR` ÜÇ BASAMAK — sözlük donuktur ve `status()["source"]`ın da sözlüğüdür.
      Dördüncü ad geri eklenirse pano çeviri sözlüğü ile motor ayrışır (tek-kaynak yasası).
  Ç3  ORTAM DEĞİŞKENİ VERİLSE BİLE KANAL YOK — eski kanalın anahtarı `MERIDIAN_GCP_PROJECT`
      ortam değişkeniydi. Kanalın kapandığını "kod okuyarak" değil, TUZAK MODÜLLE ölçeriz:
      `google.cloud` ithal edilirse test PATLAR. Yalnız kaynağı grep'lemek, geç bağlanan bir
      ithali (`import` fonksiyon gövdesinde) kaçırabilirdi.
  Ç4  `status()` "gcp" DEMEZ — farksal ölçümün okuyucusu budur (TSK-064 geçiş betiği bu yüzeyden
      "hangi kanal okunuyor" diye sorar). Var olmayan bir kanalı adıyla raporlamak, geçiş
      ölçümünü sessizce yanlış onaylardı.

Ç5 KALINTI TARAMASI ayrıca vardır: motor/test/ops AĞAÇLARINDA ve depo KÖKÜNDEKİ operatör-yüzlü
yapılandırma/şablon dosyalarında kanal ADI olarak "gcp", eski ortam değişkeninin adı ya da
`secretmanager` ithali KALMAZ. Kök AYRICA yazılıdır çünkü tur-1'in "kalıntı sıfır" hükmü yalnız üç
ağaç için doğruydu: `.env.example` operatöre kapanmış kanalı hâlâ REÇETE EDİYORDU ve `Dockerfile`
bulut sır istemcisini hâlâ KURUYORDU — ikisi de o üç ağacın dışında. Yorumlarda "GCP'den taşındı" TARİHÇESİ
serbesttir ve bilerek öyle: bu deponun kaydı geçmişi silmez, üstünü çizer — yasaklanan şey
tarihin anılması değil, ÇALIŞAN bir kanalın adının orada durmasıdır.

Ağ istemez, bulut istemez, sır istemez: her değer sahtedir ve adında öyle yazar.
"""
from __future__ import annotations

import inspect
import os
import pathlib
import re
import sys
import types

import pytest

from meridian import secrets
from tests.conftest import betikten_modul_yukle

REPO = pathlib.Path(__file__).resolve().parents[1]

#: IaC-K5 ile SİLİNEN dokuz dosya. Liste elle bakımlıdır ve olması gereken de budur: her ad bir
#: operatör kararının kaydıdır, bir desenin değil — `deploy/*.sh` gibi bir glob yazmak, yarın
#: doğacak MEŞRU bir A1 betiğini de yasaklardı.
SILINEN_YOLLAR = (
    "deploy/gcp_provision.sh",       # tek seferlik bulut sağlama (VM, ağ, IAM)
    "deploy/connect.sh",             # panoya IAP TCP tüneli
    "deploy/monitoring.sh",          # log-tabanlı alarm politikaları (ALARM_ jetonları)
    "deploy/install_hermes.sh",      # Hermes beynini VM'de kuran son adım
    "deploy/push_secret.sh",         # Secret Manager'a sır yazıcı
    "deploy/state_backup.sh",        # state/ → nesne deposu gece yedeği
    "deploy/state_restore.sh",       # nesne deposu → state/ geri yükleme
    "deploy/Caddyfile",              # TLS sonlandıran ters vekil (A1'de HİÇ koşmadı)
    # DOKUZUNCU DOSYA, tur-2'de eklendi. Kök `deploy.sh` yukarıdakilerin ÇALIŞTIRILABİLİR ayağıydı:
    # `gcloud compute scp --recurse --tunnel-through-iap` + `gcloud compute ssh … docker compose
    # up -d`. Tur-1'de kaldı çünkü adı GCP demiyordu; ölçüldüğünde gövdesi baştan sona GCP çıktı.
    # Tehlike sınıfı ötekilerden YÜKSEK: 0755'ti ve README onu "bayat docker yolu" diye gösteriyordu
    # — üç ortam değişkeni verip koşan biri gerçekten bir GCE VM'ine kod iterdi.
    "deploy.sh",
)

#: Eski kanalın ortam anahtarı. Test bu adı METİN olarak taşımak ZORUNDA (Ç3 onu kurar), o yüzden
#: kalıntı taraması bu dosyayı kendi kapsamının dışında tutar — gerekçesi `test_E1`de yazılı.
ESKI_PROJE_ENV = "MERIDIAN_GCP_PROJECT"


@pytest.fixture()
def kanalsiz(sandbox_state, monkeypatch):
    """Üç canlı kanalı da kapatır: credential dizini yok, ortamda ad yok, yerel kasa boş.

    `sandbox_state` ZORUNLU: `secrets._read_file` `config.STATE`i çağrı anında çözer, yani
    sandbox olmadan bu testler operatörün GERÇEK `state/secrets.json`ını okurdu — hem kirli bir
    ölçüm hem de sır dosyasına gereksiz bir dokunuş."""
    monkeypatch.delenv(secrets.CREDENTIAL_DIZIN_ENV, raising=False)
    monkeypatch.delenv("HERMES_API_KEY", raising=False)
    monkeypatch.delenv(ESKI_PROJE_ENV, raising=False)
    secrets.clear_cache()
    yield
    secrets.clear_cache()


# =================================================================================================
# Ç1 · SEKİZ DOSYA YOK
# =================================================================================================

@pytest.mark.parametrize("yol", SILINEN_YOLLAR)
def test_A1_olu_gcp_dosyasi_depoda_YOK(yol):
    """Silinen sekiz dosyadan hiçbiri geri gelmemeli.

    NEDEN ÇİVİ GEREKİYOR: bir dosyanın YOKLUĞU hiçbir testin doğal olarak ölçtüğü şey değildir.
    Geri gelen bir reçete derleme hatası vermez, test kırmaz, gözden kaçar — ve bir gün biri onu
    koşar (`gcp_provision.sh` bulut kaynağı yaratır, `push_secret.sh` sır yazar)."""
    p = REPO / yol
    assert not p.exists(), (
        f"{yol} geri gelmiş. Ölü GCP yolu IaC-K5 (2026-09-07) ile SİLİNDİ; A1 yolu "
        f"`deploy/oracle-a1/` altındadır ve TLS `deploy/apisix/` ile sonlandırılır.")


def test_A2_deploy_ust_duzeyinde_YALNIZ_iki_betik_kaldi():
    """Kapsam ölçülür, varsayılmaz: üst düzey `deploy/*.sh` kümesi ARTIK iki elemanlıdır.

    Bu sayı `ops/runbook_uret.py`nin "kapsam dışı, bilerek" beyanında ADIYLA yazılıdır. Küme
    büyür de beyan güncellenmezse, RUNBOOK okuyucusuna kaynak sözleşmesi hakkında YANLIŞ bir
    sınır anlatılır (tek-kaynak yasası)."""
    kalanlar = sorted(p.name for p in (REPO / "deploy").glob("*.sh"))
    assert kalanlar == ["hermes_api.sh", "verify_hermes_training.sh"], (
        f"üst düzey deploy/*.sh kümesi değişmiş: {kalanlar}. `ops/runbook_uret.py`nin kapsam "
        f"beyanı bu iki adı LİTERAL taşıyor — küme değiştiyse beyan da değişmeli.")


# =================================================================================================
# Ç2 · `KAYNAKLAR` ÜÇ BASAMAK
# =================================================================================================

def test_B1_KAYNAKLAR_uc_basamak_ve_SIRASI_cozum_sirasi():
    """Sözlük donuktur ve SIRA çözüm sırasıdır: credential → env → dosya.

    Dördüncü basamak (bulut sır deposu) IaC-K5 ile düştü. Sıra bir süs değil ölçümün kendisi:
    `_source_of` bu sırayı taklit eder ve TSK-064'ün farksal ölçümü o yüzeyden okur."""
    assert secrets.KAYNAKLAR == ("credential", "env", "file")


def test_B2_pano_sozlugu_KAYNAKLAR_ile_AYRISMAZ():
    """Panonun `SRC_TR` sözlüğü `KAYNAKLAR`ın KOPYASIDIR — kopya sessizce ayrışır.

    Kanal kapatılıp pano güncellenmezse artık ASLA üretilemeyecek bir kaynak adı için Türkçe
    karşılık taşınmaya devam ederdi: ölü kod değil, ölü BEYAN — operatöre var olmayan bir kanal
    vaat eder. (Aynı çivi v439'da da vardır; burada YÖNÜ ölçülür: kanal DÜŞTÜĞÜNDE de tutar.)"""
    app_js = (REPO / "meridian" / "web" / "app.js").read_text(encoding="utf-8")
    m = re.search(r"const SRC_TR = \{([^}]*)\}", app_js)
    assert m, "app.js içinde SRC_TR bulunamadı"
    assert set(re.findall(r"(\w+):", m.group(1))) == set(secrets.KAYNAKLAR)


# =================================================================================================
# Ç3 · ORTAM DEĞİŞKENİ VERİLSE BİLE KANAL YOK
# =================================================================================================

# `test_C1` EMEKLİ (tur-2, 2026-09-08) — ÇİVİ YEŞİLİ KANIT DEĞİLDİR, ikinci vaka.
#
# C1 şunu diyordu: eski ortam değişkeni kuruluyken `secrets.get(...) is None`. Docstring'i beklenen
# kazayı da adlandırıyordu ("dal DURUR, çağrı düşer, `_fetch` yine dallanır, bir istisna yer ve
# sessizce None döner"). Ama ÖLÇÜLDÜĞÜNDE (çekişmeli inceleme) o iddianın YAPISAL OLARAK kırmızıya
# DÖNEMEYECEĞİ çıktı: silinen dal tam olarak `except Exception: return None` biçimindeydi ve bulut
# istemcisi bu ortamda kurulu DEĞİL — dalı aynen geri koysan `from google.cloud import
# secretmanager` ImportError verir, `except` yutar, `get` yine None döner, C1 yine YEŞİL yanar.
# Yani C1 mutasyon-öncesi de mutasyon-sonrası da geçiyordu: M4'ü ısıran şey C2 (tuzak modül) ve
# C3 (kaynak taraması) idi, C1 değil.
#
# İddia SİLİNMEDİ, C2'ye DEVREDİLDİ: C2 birebir aynı davranışı ölçer, üstelik tuzak modül KURULUYKEN
# — yani orada "None döndü" cümlesi bir şey KANITLAR (kanal geri açılsaydı tuzak `BaseException`
# atardı). Aynı emsal `test_D1`de yazılıdır: davranış ayağı tek başına yetmez, yanına kaynak ayağı
# konur. Bedel: "tuzaksız, düz ortam" varyantı kayboldu — o varyantın hiçbir şey ölçmediği
# ölçüldüğü için bedel sıfırdır ve burada yazılı olması, bir sonraki turun onu "eksik" sanıp geri
# yazmasını engeller.


class _KanalGeriAcildi(BaseException):
    """Tuzağın attığı sinyal — `Exception` DEĞİL, ve bu ayrım testin can damarıdır.

    Eski GCP bloğu `except Exception` ile sarılıydı: `Exception` türeten bir tuzak SESSİZCE
    YUTULUR, `get` yine None döner ve test BOŞA yeşil yanar (tam olarak bu dosyanın kovaladığı
    yanlış-yeşil sınıfı — ilk yazımında birebir yaşandı). `BaseException` o sarmalı deler."""


def test_C2_bulut_istemcisi_ITHAL_EDILMEZ(kanalsiz, monkeypatch):
    """TUZAK MODÜL: `google.cloud`a dokunulursa test PATLAR — kaynak grep'i bunu ölçemez.

    Geç bağlanan bir ithal (`from … import …` fonksiyon GÖVDESİNDE) modül başlığında görünmez;
    tek güvenilir ölçüm ithalin KENDİSİNİ tuzaklamaktır. Tuzak `sys.modules`e monkeypatch ile
    konur, yani ne kurulu bir paket gerekir ne de temizlik unutulabilir.

    EMEKLİ EDİLEN `test_C1`İN İDDİASI DA BURADA (tur-2): eski ortam değişkeni kuruluyken `get`
    hiçbir şey uyduramaz. Orada o cümle hiçbir şey kanıtlamıyordu (gerekçe yukarıdaki emeklilik
    notunda); burada tuzak KURULUYKEN söylendiği için kanıtlıyor."""
    class _Tuzak(types.ModuleType):
        def __getattr__(self, ad):
            raise _KanalGeriAcildi(
                f"`google.cloud.{ad}` ithal edildi — bulut sır kanalı GERİ AÇILMIŞ (IaC-K5).")

    monkeypatch.setitem(sys.modules, "google", types.ModuleType("google"))
    monkeypatch.setitem(sys.modules, "google.cloud", _Tuzak("google.cloud"))
    monkeypatch.setenv(ESKI_PROJE_ENV, "sahte-proje-kimligi")
    secrets.clear_cache()
    assert secrets.get("HERMES_API_KEY") is None
    assert secrets.status()["HERMES_API_KEY"]["set"] is False


def test_C3_fetch_KAYNAGINDA_dorduncu_basamak_YOK():
    """Kablo ölçümü: `_fetch` gövdesi ÜÇ basamakta biter.

    Davranış testleri (C1/C2) kanalın SONUÇ vermediğini gösterir; bu test kanalın KODDA da
    olmadığını gösterir. İkisi ayrı: bir bayrakla kapatılmış ölü dal, davranış testini geçer ve
    bir sonraki turda "yalnız bayrağı aç" diye geri gelir."""
    src = inspect.getsource(secrets._fetch)
    for yasak in ("secretmanager", "google.cloud", ESKI_PROJE_ENV):
        assert yasak not in src, f"`secrets._fetch` hâlâ `{yasak}` taşıyor"


# =================================================================================================
# Ç4 · `status()` "gcp" DEMEZ
# =================================================================================================

def test_D1_source_of_hicbir_kosulda_gcp_DEMEZ(kanalsiz, monkeypatch):
    """`_source_of` yalnız `KAYNAKLAR`daki adlardan birini (ya da None) döndürür.

    Eski dal "ortamda proje var VE get bir değer verdi" ise "gcp" diyordu; get artık o değeri
    ancak alt kanallardan alabilir, yani dal kalsaydı DOSYADAN okunan bir sırrı "buluttan geldi"
    diye raporlardı — farksal ölçümün en sinsi yanlış-onayı.

    DAVRANIŞ AYAĞI TEK BAŞINA YETMEZ ve bunu yazmak dürüstlüğün şartı: bulut istemcisi bu
    ortamda KURULU DEĞİL, yani eski dal zaten hiçbir zaman değer üretemiyordu ve davranış
    iddiaları o dal DURURKEN de geçerdi. Bu yüzden kaynak ayağı yanına konuyor — asıl ısıran
    budur (C3'ün `_fetch` için yaptığının `_source_of` hâli)."""
    kaynak = inspect.getsource(secrets._source_of)
    for yasak in ('"gcp"', ESKI_PROJE_ENV):
        assert yasak not in kaynak, f"`secrets._source_of` hâlâ `{yasak}` taşıyor"

    monkeypatch.setenv(ESKI_PROJE_ENV, "sahte-proje-kimligi")
    monkeypatch.setenv("HERMES_API_KEY", "sahte-ortam-degeri")
    secrets.clear_cache()
    assert secrets._source_of("HERMES_API_KEY") == "env"

    monkeypatch.delenv("HERMES_API_KEY")
    secrets.set("HERMES_API_KEY", "sahte-dosya-degeri")
    assert secrets._source_of("HERMES_API_KEY") == "file"


def test_D2_status_kaynaklari_KAYNAKLAR_kumesinden(kanalsiz, monkeypatch):
    """Tüm `status()` çıktısı donuk sözlüğe uyar — hiçbir ad kaçak değildir."""
    monkeypatch.setenv(ESKI_PROJE_ENV, "sahte-proje-kimligi")
    monkeypatch.setenv("FMP_API_KEY", "sahte-ortam-degeri")
    secrets.clear_cache()
    kaynaklar = {v["source"] for v in secrets.status().values()}
    assert kaynaklar <= set(secrets.KAYNAKLAR) | {None}, kaynaklar


# =================================================================================================
# Ç5 · KALINTI TARAMASI
# =================================================================================================

#: Taranan yüzeyler — AĞAÇLAR ve depo KÖKÜNDEKİ tekil dosyalar. `docs/`, `research/` ve
#: `MERIDIAN_ENGINEERING_LOG.md` BİLEREK dışarıda: orası tarih kaydıdır ve tarihi yeniden yazmak
#: bu deponun yasağıdır.
#:
#: KÖK NEDEN AYRICA YAZILI (tur-2, ölçülmüş kaçak). Tur-1'de kapsam yalnız üç ağaçtı ve rapor
#: "kalıntı SIFIR" dedi — doğruydu, ama yalnız o üç ağaç için. Kapsamın DIŞINDA `.env.example`
#: operatöre `MERIDIAN_GCP_PROJECT=` satırını "enables Secret Manager lookups" şerhiyle REÇETE
#: ediyordu ve `Dockerfile` bulut sır istemcisini KURUYORDU. İkisi de tam olarak bu turun kapattığı
#: sınıftır: "ayar yapıldı sanılıyor, hiçbir kod okumuyor" (aynı gerekçeyle `deploy/meridian.service`
#: `Environment=` satırı ve pano `SRC_TR` sözlüğü temizlenmişti). Kapsam sınırı artık ÇİVİDE yazılı,
#: raporda değil.
TARANAN_AGACLAR = ("meridian", "tests", "ops")

#: Depo kökündeki operatör-yüzlü yapılandırma/şablon/dağıtım yüzeyleri. Uzantı süzgecine TABİ
#: DEĞİLLER (`Dockerfile` uzantısızdır, `.env.example` `.example` uzantılıdır) — adları YAZILI
#: olduğu için tamamı taranır.
TARANAN_KOK_DOSYALARI = (
    ".env.example", "Dockerfile", "docker-compose.yml", "dagit.sh", "serve.sh", "pyproject.toml",
)

#: Tek isim, tek kapsam: rapor ve docstring bu adı anar (tek-kaynak yasası — kapsamın iki ayrı
#: metinde sayılması tam da bu dosyanın kovaladığı ayrışmadır).
TARANAN_KOKLER = TARANAN_AGACLAR + TARANAN_KOK_DOSYALARI

#: Ağaç taramasının gireceği uzantılar. Kök dosyaları bu süzgece TABİ DEĞİLDİR (yukarı bkz.).
TARANAN_UZANTILAR = (".py", ".js", ".html", ".sh", ".toml", ".yaml")


def _taranan_dosyalar():
    """Ç5'in gezdiği dosyalar — ağaçlar (uzantı süzgeciyle) + kök dosyaları (süzgeçsiz).

    Kendi dosyasını DIŞLAR: gerekçe `test_E1`de yazılı."""
    ben = pathlib.Path(__file__).resolve()
    for kok in TARANAN_AGACLAR:
        for p in sorted((REPO / kok).rglob("*")):
            if p.is_file() and p.suffix in TARANAN_UZANTILAR and p.resolve() != ben:
                yield p
    for ad in TARANAN_KOK_DOSYALARI:
        p = REPO / ad
        if p.is_file():
            yield p

#: Kanal adı olarak yasak üç iz. `"gcp"` TIRNAKLI aranır: tırnaksız "GCP" düzyazıda geçebilir
#: ("GCP'den taşındı") ve o TARİHÇEDİR — yasak olan, bir sözlük değeri/dal etiketi olarak
#: kanalın adının kodda durmasıdır.
YASAK_IZLER = ('"gcp"', "'gcp'", "secretmanager", ESKI_PROJE_ENV)


#: Ç5 taramasının POZİTİF KONTROL TABANI. ÖLÇÜLDÜ 2026-09-08: 681 dosya (üç ağaç 675 + kök 6).
#: Eşik ölçümün KENDİSİ değil körlük alarmıdır — sayıya yapıştırmak dosya silen her meşru
#: temizliği kırmızıya çevirirdi. Emsal:
#: `tests/test_guvenlik_basliklari_v203.py::test_vekil_taramasi_SESSIZCE_BOS_DEGIL`.
KALINTI_TARAMA_ASGARI = 400


def test_E1b_kalinti_taramasi_SESSIZCE_BOS_DEGIL():
    """POZİTİF KONTROL: Ç5'in tarayıcısı gerçekten dosya BULUYOR — ve kök listesi TAM.

    `_taranan_dosyalar` iki yerde sessizce daralır: bir ağaç taşınırsa `rglob` boş döner, bir kök
    dosya silinir/yeniden adlandırılırsa `if p.is_file()` onu ATLAR ve tarama beş kökle devam eder.
    İki hâlde de `test_E1` HİÇBİR ŞEY taramadan yeşil yanar. v203 bu sınıfı kendi tarayıcısı için
    kapattı (`VEKIL_TARAMA_ASGARI`); burada AÇIK kalmıştı — aynı kusur, aynı kapı."""
    eksik = [ad for ad in TARANAN_KOK_DOSYALARI if not (REPO / ad).is_file()]
    assert not eksik, (
        f"taranacak kök dosya(lar) yok: {eksik}. Silindiyse `TARANAN_KOK_DOSYALARI` beyanı da "
        f"değişmeli — sessizce atlanan bir kök, kapsamı ölçülmeden daraltır.")
    n = len(list(_taranan_dosyalar()))
    assert n >= KALINTI_TARAMA_ASGARI, (
        f"kalıntı taraması yalnız {n} dosya gördü (asgari {KALINTI_TARAMA_ASGARI}, ölçülen taban "
        f"2026-09-08: 681). Ağaç taşınmış ya da uzantı süzgeci daralmış olabilir — `test_E1` bu "
        f"hâlde hiçbir şey ölçmeden geçer.")


def test_E1_motor_test_ops_agacinda_kanal_KALINTISI_YOK():
    """Kalıntı sıfır olmalı — ve KAPSAM burada yazılıdır, raporda değil.

    TARANAN: `meridian/`, `tests/`, `ops/` ağaçları (`.py`/`.js`/`.html`/`.sh`/`.toml`/`.yaml`) +
    depo kökünde `.env.example`, `Dockerfile`, `docker-compose.yml`, `dagit.sh`, `serve.sh`,
    `pyproject.toml`. TARANMAYAN: `docs/`, `research/`, `MERIDIAN_ENGINEERING_LOG.md` (tarih
    kaydı) ve `deploy/` altındaki A1 yüzeyleri (kanal adı orada geçmiyor; geçerse `test_E4`in
    atıf taraması değil bu iddia genişletilmeli).

    Neden BU DOSYA istisna: Ç3 kanalın kapandığını ölçmek için eski ortam değişkeninin adını METİN
    olarak kurmak zorunda. İstisnanın yazılı olması, sessiz bir kapsam daralmasından iyidir — bu
    dosya dışında hiçbir yer o adı taşımaz ve tarama tam olarak onu ölçer."""
    kalinti: list[str] = []
    for p in _taranan_dosyalar():
        metin = p.read_text(encoding="utf-8", errors="replace")
        for iz in YASAK_IZLER:
            if iz in metin:
                kalinti.append(f"{p.relative_to(REPO)} → {iz}")
    assert not kalinti, (
        "ölü bulut kanalının kalıntısı:\n  " + "\n  ".join(kalinti) +
        "\nKanal IaC-K5 (2026-09-07) ile kapandı; sıra credential → env → dosya.")


#: Bağımlılığın BEYAN EDİLDİĞİ ve KURULDUĞU iki yüzey. Tur-1 yalnız ilkini ölçtü ve ikincisi
#: sessizce kaldı: `Dockerfile` paketi `uv pip install --system …` satırında GERÇEKTEN kuruyordu,
#: yani "beyandan düştü" hükmü yarısı ölçülmemiş bir hükümdü. Beyan bir sözleşmeyse KURULUM daha
#: da bağlayıcıdır — imaja giren şey `uv audit`in tarayacağı gerçek yüzeydir.
BAGIMLILIK_YUZEYLERI = ("pyproject.toml", "Dockerfile")


@pytest.mark.parametrize("yuzey", BAGIMLILIK_YUZEYLERI)
def test_E2_bagimlilik_yuzeylerinde_bulut_sir_istemcisi_YOK(yuzey):
    """Ne beyan edilir ne kurulur: bulut sır istemcisi İKİ yüzeyden de düşer.

    Beyan bir SÖZLEŞMEDİR: kurulmayan ama beyan edilen bir bağımlılık `ops/import_tarama.py`nin
    daraltma hükmünü kirletir ve `uv audit` tedarik-zinciri kapısına okuyucusuz bir yüzey ekler
    (Yasa 6'nın bağımlılık hâli). Kurulum ise beyandan ÖTEDİR: `docker compose build` bir gün
    koşarsa, motorda karşılığı OLMAYAN bir bulut istemcisi imaja girer — üstelik aynı tur
    `docker-compose.yml`den ölü kabloyu çıkarmıştı, yani docker yolu kendi içinde tutarsız kalırdı."""
    metin = (REPO / yuzey).read_text(encoding="utf-8")
    assert "google-cloud-secret-manager" not in metin, (
        f"{yuzey} hâlâ bulut sır istemcisini taşıyor — kanal IaC-K5 ile kapandı; "
        f"beyan da kurulum da düşer")


def test_E3_CSP_TEK_KAYNAGI_uygulama_katmanindadir():
    """Vekil dosyası silindi; güvenlik başlıklarının TEK KAYNAĞI uygulama katmanıdır.

    v203 bu iki kaynağı DİZE EŞİTLİĞİYLE bağlıyordu. Vekil kopyası artık yok, yani "eşitlik"
    ölçülemez — ama ölçümün KORUDUĞU şey (ikinci bir canlı tanım doğmasın) burada sürer: motor
    ağacında politikayı tanımlayan başka bir yüzey OLMAMALI. Bedel yasası: kaybedilen ölçüm
    "iki kopya ayrıştı mı", kazanılan "kopya HİÇ yok"tur ve ikincisi daha güçlüdür."""
    from meridian.api import CSP_POLITIKASI, GUVENLIK_BASLIKLARI

    assert GUVENLIK_BASLIKLARI["Content-Security-Policy"] == CSP_POLITIKASI
    ikinci_tanim = [
        p.relative_to(REPO)
        for kok in ("meridian", "deploy", "ops")
        for p in sorted((REPO / kok).rglob("*"))
        if p.is_file() and p.suffix in (".conf", ".yaml", ".yml", "")
        and p.name != "app.js"
        and "Content-Security-Policy" in p.read_text(encoding="utf-8", errors="replace")
    ]
    assert not ikinci_tanim, (
        f"CSP'yi tanımlayan İKİNCİ bir yüzey var: {ikinci_tanim}. Vekil `header <ad> <değer>` "
        f"bir SET'tir — ikinci canlı tanım uygulamanınkini SESSİZCE ezer. Tek kaynak: "
        f"`meridian/api.py::GUVENLIK_BASLIKLARI`.")


#: Atıf taramasının ağaçları: motor + ops. `tests/` BİLEREK dışarıda ve gerekçesi ölçülmüştür —
#: test dosyaları silinen adları ÖLÇÜM KONUSU olarak taşımak zorundadır (bu dosyanın kendi
#: `SILINEN_YOLLAR` listesi; v203'ün "uzantısız dosya adları da olur" örneği). `docs/` ve
#: `research/` de dışarıda: orası tarih kaydıdır.
ATIF_AGACLARI = ("meridian", "ops")

#: "Bu taban ad hâlâ YAŞAYAN bir dosyayı adlandırıyor mu?" sorusunun sorulduğu yüzeyler.
#: DEPO KÖKÜNÜN TAMAMI DEĞİL — ve bu ayrım ölçülmüştür (2026-09-08, yeniden inceleme): ana
#: checkout'ta `.claude/worktrees/` altında SEKİZ kardeş worktree duruyor ve her biri bu turun
#: sildiği dosyaların BAYAT KOPYASINI taşıyor. Kök tarandığında dokuz adın DOKUZU da "yaşayan bir
#: dosya var" diye atlanıyordu: `atlanir` dokuz elemana çıkıyor, `aranir` BOŞ kalıyor ve atıf
#: taraması hiçbir ad aramadan yeşil yanıyordu — testin kendi docstring'inin adlandırdığı sessiz
#: kapsam çöküşünün ta kendisi. Kopyalar kaynak DEĞİLDİR: bir adın yaşayıp yaşamadığı ancak
#: deponun kendi izlenen ağaçlarından okunur.
YASAYAN_AD_KOKLERI = ("meridian", "ops", "tests", "deploy", "docs", "research")

#: Bir yolun parçalarından biri buysa dosya YOK sayılır — kardeş çalışma ağaçları, sanal ortam,
#: paket depoları, yedekler ve derleme artefaktları. Ad kökleri zaten bu dizinleri kapsamıyor;
#: bu süzgeç ikinci savunmadır (yarın `docs/` altına bir `node_modules` düşerse tarama yine
#: aynı sonucu verir).
YOK_SAYILAN_DIZINLER = frozenset(
    {".claude", ".venv", ".git", ".superpowers", "node_modules", "__pycache__", "backups", "state"})


def _yasayan_dosyalar():
    """`YASAYAN_AD_KOKLERI` altındaki dosyalar + depo KÖKÜNDEKİ tekil dosyalar.

    Kök `iterdir` ile gezilir, `rglob` ile DEĞİL: kökteki dosyalar sayılmalı ama köke inen bir
    özyineleme tam olarak kardeş worktree'lerin içine girerdi."""
    for kok in YASAYAN_AD_KOKLERI:
        d = REPO / kok
        if not d.is_dir():
            continue
        for p in d.rglob("*"):
            if p.is_file() and not (YOK_SAYILAN_DIZINLER & set(p.relative_to(REPO).parts)):
                yield p
    for p in REPO.iterdir():
        if p.is_file():
            yield p


def _atif_aranacak_adlar() -> tuple[list[str], list[str]]:
    """Hangi taban adlar aranabilir, hangileri ARANAMAZ — kural TÜRETİLİR, elle yazılmaz.

    Bir taban ad hâlâ YAŞAYAN bir dosyayı da adlandırıyorsa (kök `deploy.sh` silindi ama
    `deploy/oracle-a1/deploy.sh` canlı dağıtım betiğidir) o adı aramak, meşru bir atfı ölü sanardı.
    Elle bir istisna listesi tutmak ise `recompute` şerhinin adlandırdığı hastalıktır (liste eskir,
    dedektör kurt masalı anlatır) — o yüzden ayrım diskten türetilir ve ATLANANLAR da ölçülür.

    TÜRETMENİN KAPSAMI `YASAYAN_AD_KOKLERI`dir, depo kökü değil; gerekçe orada ölçülü yazılı ve
    `test_E5` onu çivi olarak ölçer."""
    yasayan = {p.name for p in _yasayan_dosyalar()}
    aranir, atlanir = [], []
    for yol in SILINEN_YOLLAR:
        ad = yol.rsplit("/", 1)[-1]
        (atlanir if ad in yasayan else aranir).append(ad)
    return aranir, atlanir


def test_E4_silinen_yollara_MOTOR_ve_OPS_agacinda_ATIF_YOK():
    """Ç1 dosyanın YOKLUĞUNU ölçer; bu iddia ADININ yokluğunu ölçer — ve ikisi ayrıdır.

    ÖLÇÜLMÜŞ BOŞLUK (tur-1): sekiz dosya silindi, `test_A1` yeşil yandı, ve `deploy/monitoring.sh`
    adı motor kodunda DÖRT yerde yaşamaya devam etti — `obs.py`de ALARM_ jetonlarının SABİT
    KALMA GEREKÇESİ olarak ("Tokens matched by deploy/monitoring.sh log filters"), `obs.alarm`
    docstring'inde, `selfreview.py`de ("monitoring.sh onu grepler") ve `loop.py`da. Bir kısıtın
    gerekçesi var olmayan bir tüketiciyi gösteriyorsa kısıtın OKUYUCUSU yoktur (Yasa 6'nın tersi):
    "bu jetonlar neden sabit kalmalı?" sorusu bir daha cevaplanamaz. Üstelik `obs.py`nin o şerhi
    ÜRETİLMİŞ `docs/RUNBOOK.md`e alıntı olarak akıyordu, yani bir olay anında operatör var olmayan
    bir betiği arardı.

    ATLANAN ADLAR ayrıca ölçülür: sessiz bir kapsam daralması (yeni bir ad çakışması doğar ve
    tarama onu sessizce atlar) bu testi bir gün hiçbir şey ölçmeden yeşil bırakırdı."""
    aranir, atlanir = _atif_aranacak_adlar()
    # BOŞ-TARAMA KAPISI, atlanan-ad beyanından ÖNCE: iki iddia da aynı anda düşer ama TEŞHİS
    # ayrıdır. `aranir` boşsa sorun "beyan eskimiş" değil, taramanın HİÇBİR ŞEY ölçmemesidir ve
    # o hâlde beyanı "güncellemek" körlüğü mühürler (ölçülmüş yanlış-teşhis yolu, 2026-09-08).
    assert aranir, (
        "atıf taraması HİÇBİR ad ölçmedi: dokuz taban adın hepsi 'yaşayan dosya var' diye "
        "atlandı. Bu, testin yeşil ama KÖR hâlidir — önce `_yasayan_dosyalar` kapsamına bak "
        "(bayat bir kopya ağacı kaynak sanılıyor olabilir), beyanı SONRA güncelle.")
    assert atlanir == ["deploy.sh"], (
        f"atlanan taban ad kümesi değişmiş: {atlanir} (ölçüldü 2026-09-08: yalnız `deploy.sh`, "
        f"çünkü `deploy/oracle-a1/deploy.sh` CANLI dağıtım betiğidir). Yeni bir çakışma doğduysa "
        f"ya ad ayrıştırılmalı ya da bu beyan güncellenmeli — sessizce atlanmamalı.")
    assert len(aranir) == len(SILINEN_YOLLAR) - 1

    atiflar: list[str] = []
    for agac in ATIF_AGACLARI:
        for p in sorted((REPO / agac).rglob("*")):
            if not p.is_file() or p.suffix not in TARANAN_UZANTILAR:
                continue
            metin = p.read_text(encoding="utf-8", errors="replace")
            for ad in aranir:
                if ad in metin:
                    atiflar.append(f"{p.relative_to(REPO)} → {ad}")
    assert not atiflar, (
        "silinen yollara motor/ops ağacında ATIF kalmış:\n  " + "\n  ".join(atiflar) +
        "\nAdı tarihçeye çevir ya da GERÇEK tüketiciyi yaz — var olmayan bir dosyayı gerekçe "
        "gösteren bir kısıt, gerekçesiz bir kısıttır.")


def test_E6_jeton_kararliligi_GEREKCESI_YASAYAN_okuyucuyu_ADIYLA_gosterir():
    """`test_E4` silinen ADIN gitmesini ölçer; bu iddia YERİNE GELENİN gerçek olmasını ölçer.

    ÖLÇÜLMÜŞ İKİNCİ HATA (2026-09-08, yeniden inceleme): ölü betik adı düştü, ama yerine yazılan
    gerekçe VAR OLMAYAN bir mekanizma anlatıyordu ("`notify.send`/`notify.inbox` jetonu satır
    METNİNDE düz alt-dizge olarak eşler"). Ölçüldüğünde kod tarafının satır metnini hiç taramadığı
    çıktı: `notify.inbox` olayın `alarm` ALANINI `obs.NOTIFY_TOKENS` KÜMESİNDE arar. Yani kısıtın
    okuyucusu yine yanlıştı — bir tur önceki kusurun aynısı, başka kılıkta.

    ÖLÇÜLEN İKİ GERÇEK OKUYUCU: (1) diske yazılmış sözlük anahtarları (`notify_undelivered.json`
    sayacı — `watchdog.parity_report` onu okur), (2) panonun `OLAY_YUZEYLERI` literal jeton
    listeleri. İkincisi TÜRETİLMEZ, elle yazılır: bir ALARM_ değerini yeniden adlandırmak olay
    çekmecesini o jeton için sessizce boşaltır.

    ÖLÇÜLEN METİN, RUNBOOK'A AKAN METİNDİR: gerekçe `ops/runbook_uret.py::alarm_envanteri` ile
    üreticiden okunur — operatörün olay anında gördüğü cümle budur ve yanlış olan da oydu.
    JETON PARİTESİ BURADA TEKRARLANMAZ (tek-kaynak yasası): `OLAY_YUZEYLERI` ↔ ALARM_ eşitliğini
    `tests/test_uiux_s1b_v154.py::test_t3_capa_kurali_tek_ve_donusumsuz` iki yönlü ölçüyor; burada
    yalnız OKUYUCUNUN GERÇEKTEN VAR OLDUĞU ölçülür."""
    uretici = betikten_modul_yukle(REPO / "ops" / "runbook_uret.py", "runbook_uret")
    gerekce = {a["jeton"]: a["gerekce"] for a in uretici.alarm_envanteri()}["HEARTBEAT_STALE"]
    for okuyucu in ("OLAY_YUZEYLERI", "notify_undelivered.json"):
        assert okuyucu in gerekce, (
            f"jeton kararlılığının gerekçesi `{okuyucu}` okuyucusunu ADIYLA anmıyor:\n{gerekce}\n"
            f"Bir kısıtın gerekçesi ölçülmüş bir okuyucuyu göstermek ZORUNDA — göstermiyorsa "
            f"kısıt gerekçesizdir (Yasa 6'nın tersi) ve bu dosya o kusuru iki kez ölçtü.")

    # OKUYUCU GERÇEKTEN ORADA MI: gerekçe bir adı anıyor diye o okuyucu var olmuş olmaz — bu
    # dosyanın kovaladığı kusurun tam tanımı budur. Pano yüzeyi ölçülür, jeton PARİTESİ değil.
    app_js = (REPO / "meridian" / "web" / "app.js").read_text(encoding="utf-8")
    blok = re.search(r"const OLAY_YUZEYLERI = \{(.*?)\n\};", app_js, re.S)
    assert blok, "gerekçe `OLAY_YUZEYLERI` diyor ama app.js'de öyle bir kayıt defteri YOK"
    literal = [t for d in re.findall(r"jetonlar:\s*\[([^\]]*)\]", blok.group(1))
               for t in re.findall(r'"([A-Z_]+)"', d)]
    assert literal, (
        "`OLAY_YUZEYLERI` var ama ELLE YAZILMIŞ literal jeton taşımıyor — gerekçenin anlattığı "
        "kırılganlık (liste türemez, ad değişince sessizce boşalır) artık geçerli değil demektir; "
        "gerekçe o zaman ölçüme göre yeniden yazılmalı.")


def test_E5_YASAYAN_ad_taramasi_KARDES_WORKTREE_KOPYALARINI_saymaz(tmp_path, monkeypatch):
    """Kopya kaynak DEĞİLDİR: `.claude/worktrees/` altındaki bayat bir kopya bir adı "yaşıyor"
    yapmaz.

    ÖLÇÜLMÜŞ VAKA (2026-09-08, yeniden inceleme). Tarama bir gün depo KÖKÜNÜ geziyordu ve bu,
    yazıldığı worktree'de zararsızdı — ama otoriter suite ANA CHECKOUT'ta koşar ve orada sekiz
    kardeş worktree duruyordu. Sonuç iki kat zararlıydı: `test_E4` kırmızı yanıyordu ve mesajı
    "beyanı güncelle" diye YANLIŞ TEŞHİSE götürüyordu; beyan güncellenseydi `aranir` boş kalır ve
    atıf taraması bir daha hiçbir şey ölçmezdi.

    Çivi SAHTE BİR DEPO kurar (tmp): yaşayan `deploy/oracle-a1/deploy.sh` + üç bayat kopya
    (kardeş worktree, sanal ortam, paket deposu). `REPO` o köke çevrilir; GERÇEK depo ağacına
    hiçbir şey yazılmaz."""
    for rel in ("meridian/obs.py", "ops/olcum.py", "deploy/oracle-a1/deploy.sh"):
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("# sahte", encoding="utf-8")
    bayat = (".claude/worktrees/agent-x/deploy/monitoring.sh",
             ".claude/worktrees/agent-x/deploy/Caddyfile",
             ".venv/lib/python3.13/site-packages/gcp_provision.sh",
             "node_modules/paket/connect.sh")
    for rel in bayat:
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("# bayat kopya", encoding="utf-8")
    # POZİTİF KONTROL: kurulum GERÇEKTEN diskte — dosyalar yazılmamış olsaydı iddia boş yere
    # yeşil yanardı (bu dosyanın kovaladığı yanlış-yeşil sınıfı).
    assert all((tmp_path / rel).is_file() for rel in bayat)

    monkeypatch.setattr(sys.modules[__name__], "REPO", tmp_path)
    aranir, atlanir = _atif_aranacak_adlar()
    assert atlanir == ["deploy.sh"], (
        f"bayat kopyalar 'yaşayan dosya' sayıldı: {atlanir}. Kardeş worktree/venv/paket deposu "
        f"kaynak değildir — `YOK_SAYILAN_DIZINLER` ve `YASAYAN_AD_KOKLERI` bunu kapatmalı.")
    assert "monitoring.sh" in aranir and "Caddyfile" in aranir
    assert len(aranir) == len(SILINEN_YOLLAR) - 1
