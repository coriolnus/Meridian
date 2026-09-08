"""v454 · TSK-177 dilim-2 — `state/belge_esitleme.json` BEYANININ GERÇEK OKUYUCUSU.

ÖLÇÜLEN BOŞLUK (2026-09-08). `ops/belge_esitle.sh` belge kümesini A1'e rsync ettikten SONRA
tek satırlık bir beyan yazar (`esitlenen_sha` · `esitlendi_utc` · `esitleyen_host` · `dosya_n` ·
`silinen_n`). Motor tarafında bu dosyanın HİÇBİR okuyucusu yoktu; `recompute._orphan_state_files`
onu haklı olarak "üretilip tüketilmeyen kanıt" sayıyor ve canlı bekçi kırmızıya dönüyordu —
YASA 6'nın (okuyucusuz yazım yok) tam da tarif ettiği sınıf.

İKİ YANLIŞ ÇIKIŞ, BİR DOĞRU ÇIKIŞ
---------------------------------
✘ Adı `codelaw.DECLARED_SINKS`e yazmak: beyan, dosyayı OKUNUR yapmaz — yalnız bekçiyi susturur.
  Operatör panoda hâlâ "hangi belge A1'de duruyor?" sorusunun cevabını göremezdi.
✘ Dedektörü gevşetmek: bekçiyi kör etmek, bulguyu kapatmak değildir.
✔ GERÇEK okuyucu: tahtayı servis eden uç (`/api/roadmap`), tahtanın A1'deki kopyasının NE KADAR
  TAZE olduğunu da söyler. Eşitlenen kümenin baş aktörü `ROADMAP.md`dir ve bu uç tam onu servis
  eder; tazeliği ayrı bir uca koymak aynı gerçeği iki yerden okutmak olurdu (tek-kaynak yasası).

BU DOSYA NEYİ ÇİVİLER
---------------------
a. DOSYA YOK → `belge_esitleme` `None` + `belge_esitleme_neden` "dosya yok". Sessiz `None`
   yasaktır: "ölçemedim" ile "eşitleme hiç yapılmadı" ekranda aynı görünürdü.
b. GEÇERLİ DOSYA → beş alan BİREBİR. Uç değer UYDURMAZ, DÖNÜŞTÜRMEZ, KIRPMAZ.
c. BOZUK JSON → `None` + neden, ve istek yine **200**. Beyan okunamadı diye tahta kaybolmaz.
d. EKSİK ALAN → `None` + neden (eksik alanın ADIYLA). Yarım beyanı tam gibi göstermek, uydurma
   yasağının ihlalidir; hangi alanın eksik olduğunu söylememek ise okuyanı kaynağa iter.
e. YASA 6 — `codelaw.artifact_graph` bu ad için bir OKUYUCU GÖRÜYOR ve dolayısıyla
   `recompute._orphan_state_files` sahnede dosya DURURKEN onu yetim SAYMIYOR. Çivi POZİTİF
   KONTROLLÜDÜR: aynı sahneye uydurma bir yetim de bırakılır ve dedektörün onu GÖRDÜĞÜ ölçülür —
   yoksa "yetim yok" cümlesi, dedektörün hiç çalışmadığı bir sahnede de yeşil olurdu.
f. SALT OKUMA — uç dosyaya DOKUNMAZ (içerik + mtime değişmez). Bu uç zaten yazma ucu olmayan
   bir yüzeydir; okuyucu eklerken sessizce bir yazar doğurmak, çözdüğü sınıfı geri getirirdi.
"""
from __future__ import annotations

import json
import pathlib

import pytest
from fastapi.testclient import TestClient

from meridian import api, codelaw, config, recompute

REPO = pathlib.Path(__file__).resolve().parents[1]

#: Gerçek yazıcının biçimine uyan geçerli bir beyan (sha 40 hex, utc `Z` ile biter).
GECERLI: dict = {
    "esitlenen_sha": "b790de5c4f1a2e8d9b0c3a7f6e5d4c3b2a190817",
    "esitlendi_utc": "2026-09-08T19:04:11Z",
    "esitleyen_host": "meridian-mac",
    "dosya_n": 37,
    "silinen_n": 2,
}

#: Dosyanın adı YAZICININ (`ops/belge_esitle.sh`) sözleşmesidir; burada LİTERAL durur, çünkü
#: ucun sabitinden türetilseydi uç adı değiştirdiği gün çivi de sessizce onunla birlikte kayardı
#: (aynı yanlışı ölçen bir test, hiçbir şey ölçmez). Ayrışma ayrı bir çiviyle ölçülür (e0).
AD = "belge_esitleme.json"


def _client() -> TestClient:
    """Yaşam döngüsü BAŞLATILMADAN istemci (v287 deseni): `with TestClient(app)` scheduler/hermes
    ipliklerini ayağa kaldırır — bu uç için gereksiz ve paralel ajan penceresinde risk."""
    return TestClient(api.app)


def _yaz(metin: str) -> pathlib.Path:
    """Sahneye ham metin bırakır (bozuk JSON senaryosu ham metin ister; `store.write_json`
    geçemezdi)."""
    p = pathlib.Path(config.STATE) / AD
    p.write_text(metin, encoding="utf-8")
    return p


def _govde() -> dict:
    r = _client().get("/api/roadmap")
    assert r.status_code == 200, r.text
    return r.json()


# ---------------------------------------------------------------- a. DOSYA YOK

def test_a_dosya_yoksa_None_ve_ADIYLA_neden(sandbox_state):
    g = _govde()
    assert "belge_esitleme" in g, "alan hiç üretilmemiş — uç beyanı okumuyor"
    assert g["belge_esitleme"] is None
    assert g["belge_esitleme_neden"] == "dosya yok", g["belge_esitleme_neden"]


def test_a2_neden_alani_SESSIZ_None_birakmiyor(sandbox_state):
    """`None` + gerekçesiz bir gövde, 'ölçemedim' ile 'eşitleme yapılmadı'yı aynı gösterir."""
    g = _govde()
    assert isinstance(g["belge_esitleme_neden"], str) and len(g["belge_esitleme_neden"]) >= 3


# ---------------------------------------------------------------- b. GEÇERLİ DOSYA

def test_b_gecerli_dosya_BES_ALANI_BIREBIR_dondurur(sandbox_state):
    _yaz(json.dumps(GECERLI))
    g = _govde()
    assert g["belge_esitleme"] == GECERLI, g["belge_esitleme"]
    assert g["belge_esitleme_neden"] is None, "beyan okundu ama neden alanı hâlâ dolu"


@pytest.mark.parametrize("alan", sorted(GECERLI))
def test_b2_her_alan_TEK_TEK_gorunuyor(alan, sandbox_state):
    """Toplu eşitlik bir alanın sessizce düşmesini yakalar, ama HANGİSİ olduğunu söylemez."""
    _yaz(json.dumps(GECERLI))
    assert _govde()["belge_esitleme"][alan] == GECERLI[alan]


def test_b3_uc_FAZLA_alan_sizdirmiyor(sandbox_state):
    """Yazıcı bir gün ek alan yazarsa uç onu sessizce panoya taşımaz: sözleşme BEŞ alandır."""
    _yaz(json.dumps({**GECERLI, "gizli_ek": "sizinti"}))
    assert set(_govde()["belge_esitleme"]) == set(GECERLI)


# ---------------------------------------------------------------- c. BOZUK JSON

def test_c_bozuk_json_None_neden_ve_ISTEK_200(sandbox_state):
    _yaz("{ bu gecerli json degil")
    r = _client().get("/api/roadmap")
    assert r.status_code == 200, "beyan bozuk diye TAHTA kayboldu — uç fail-open olmalı"
    g = r.json()
    assert g["belge_esitleme"] is None
    assert isinstance(g["belge_esitleme_neden"], str) and len(g["belge_esitleme_neden"]) >= 20, (
        f"bozuk beyan için gerekçe yok/kısa: {g['belge_esitleme_neden']!r}")
    assert g.get("ok") is True, "tahta gövdesi beyandan bağımsız olmalı"


def test_c2_govdesi_JSON_ama_NESNE_degil(sandbox_state):
    """`[]` ya da `null` geçerli JSON'dur ama beyan DEĞİLDİR — 'bozuk' kovasına düşmeli."""
    for ham in ("[]", "null", '"dize"'):
        _yaz(ham)
        g = _govde()
        assert g["belge_esitleme"] is None, f"{ham!r} beyan sayıldı"
        assert g["belge_esitleme_neden"], f"{ham!r} için gerekçe yok"


# ---------------------------------------------------------------- d. EKSİK ALAN

@pytest.mark.parametrize("eksik", sorted(GECERLI))
def test_d_eksik_alan_None_ve_EKSIGIN_ADI(eksik, sandbox_state):
    _yaz(json.dumps({k: v for k, v in GECERLI.items() if k != eksik}))
    g = _govde()
    assert g["belge_esitleme"] is None, f"{eksik} eksikken beyan TAM sayıldı"
    neden = g["belge_esitleme_neden"]
    assert eksik in (neden or ""), f"gerekçe eksik alanın adını söylemiyor: {neden!r}"


# ---------------------------------------------------------------- e. YASA 6

def test_e0_ucun_sabiti_YAZICININ_adiyla_AYNI():
    """Uç adı bir gün değişirse dosya diskte yetim kalır ve pano boş beyan gösterir; ayrışma
    burada ADIYLA ölçülür (çivi ucun sabitini TÜRETMEZ — bkz. `AD` şerhi)."""
    assert api._BELGE_ESITLEME_ADI == AD, (
        f"uç `{api._BELGE_ESITLEME_ADI}` okuyor, yazıcı `{AD}` yazıyor — beyan yetim kalır")


def test_e1_artifact_graph_bu_ad_icin_OKUYUCU_goruyor():
    """Statik graf `store.read_json("belge_esitleme.json")` çağrısını GÖRMELİ. Görmezse
    `recompute._orphan_state_files`in `known` kümesi bu adı içermez ve bekçi kırmızıya döner."""
    g = codelaw.artifact_graph()
    kayit = (g.get("artifacts") or {}).get(AD)
    assert kayit is not None, (
        f"`{AD}` statik grafta HİÇ yok — hiçbir modül onu `store.read_json` ile okumuyor; "
        "beyan dosyası yetim kalır (YASA 6)")
    assert kayit["readers"], f"`{AD}` grafta var ama okuyucusu yok: {kayit}"
    assert "api.py" in kayit["readers"], (
        f"okuyucu `api.py` değil ({kayit['readers']}) — dilim-2'nin sözleşmesi pano ucudur")


def test_e2_orphan_taramasi_YETIM_SAYMIYOR_pozitif_kontrollu(sandbox_state):
    """Sahnede beyan dosyası DURURKEN dedektör onu yetim saymamalı — ama aynı sahnede uydurma bir
    yetim GÖRÜLMELİ, yoksa çivi dedektörün hiç çalışmadığı bir sahnede de yeşil olurdu."""
    _yaz(json.dumps(GECERLI))
    uydurma = "uydurma_yetim_v454.json"
    (pathlib.Path(config.STATE) / uydurma).write_text(json.dumps({"a": 1}), encoding="utf-8")

    satir = recompute._orphan_state_files()
    detay = satir["detail"]

    assert uydurma in detay, (
        f"POZİTİF KONTROL DÜŞTÜ: dedektör bu sahnede uydurma yetimi bile görmüyor ({satir}) — "
        "aşağıdaki 'yetim değil' hükmü hiçbir şey kanıtlamazdı")
    assert AD not in detay, (
        f"`{AD}` hâlâ yetim listesinde: {detay}. Okuyucu eklendi ama statik graf onu görmüyor "
        "(ad literal değil mi? `store.read_json` yerine başka bir kapı mı kullanıldı?)")


# ---------------------------------------------------------------- f. SALT OKUMA

def test_f_uc_beyana_DOKUNMUYOR(sandbox_state):
    """Okuyucu eklerken sessizce bir YAZAR doğurmak, çözülen sınıfı geri getirirdi."""
    p = _yaz(json.dumps(GECERLI))
    once = (p.read_bytes(), p.stat().st_mtime_ns)
    _govde()
    assert (p.read_bytes(), p.stat().st_mtime_ns) == once, "uç beyan dosyasına YAZDI"


def test_f2_dosya_yokken_uc_dosya_URETMIYOR(sandbox_state):
    """`store.read_json` okuma yolunda dosya yaratmaz; bir gün `update_json`a kayılırsa bu çivi öter."""
    _govde()
    assert not (pathlib.Path(config.STATE) / AD).exists(), "okuma yolu boş bir beyan ÜRETTİ"

# ---------------------------------------------------------------- h. HATA DALI

def test_h_roadmap_okunama_ALANLAR_VAR(sandbox_state, monkeypatch, tmp_path):
    """ROADMAP dosyası okunamadığında (`OSError` dal) da `belge_esitleme` ve
    `belge_esitleme_neden` alanları gövdede durmalıdır — beyan okunamadığı için hata yanıtını
    göstersek de, hangi belge A1'de olduğu sorusunun cevabını gizlememeliyiz. Hata dalı kodu:

        except OSError as e:
            return {"ok": False, "bolumler": None, ...,
                    "belge_esitleme": besitleme, "belge_esitleme_neden": besitleme_neden}

    İnceleme Mutasyon D gösterdi ki bu iki alan henüz HİÇBİR testle korunmuyordu.

    DİKİŞ, REPO AĞACI DEĞİL: `/api/roadmap` tahtanın yolunu `_roadmap_yolu()` ile çözer
    (`meridian/api.py`) ve `OSError` dalı o `Path`in `p.stat()`/`p.read_text()` çağrısından
    gelir. Depo KÖKÜNDEKİ gerçek `ROADMAP.md`yi `rename` ile taşımak (a) test ortasında çökerse
    dosyayı kalıcı kaybettirir, (b) tam suite `-n 4` ile paralel koşarken aynı dosyayı okuyan
    başka testleri (v351, v343 …) rastgele KIRMIZI yapar. Bunun yerine YALNIZ ucun dikişi
    (`api._roadmap_yolu`) `monkeypatch` ile var-olmayan bir `tmp_path` yoluna çevrilir — depo
    ağacına hiç dokunulmaz, `ROADMAP.md` yerinde kalır."""
    yok_yolu = tmp_path / "yok_ROADMAP_v454.md"
    assert not yok_yolu.exists(), "sahne kirli: geçici yol zaten var — OSError garanti değil"
    monkeypatch.setattr(api, "_roadmap_yolu", lambda: yok_yolu)

    r = _client().get("/api/roadmap")
    assert r.status_code == 200, "beyan hatasından sonra da tahta 200 dönmeli"
    g = r.json()
    assert g.get("ok") is False, "ROADMAP okunamadı ama ok=True"
    assert "hata" in g and g["hata"], "hata mesajı yok/boş"

    # HATA DALINDA DA ALANLAR DURMALΙ — bu çiviyi kıran iki alan var
    assert "belge_esitleme" in g, "hata dalında belge_esitleme alanı yok"
    assert "belge_esitleme_neden" in g, "hata dalında belge_esitleme_neden alanı yok"
    # Beyan dosyası yokken (test ortamında) alanlar None olmalı
    assert g["belge_esitleme"] is None, "beyan dosyası yokken belge_esitleme None olmalı"
    assert isinstance(g["belge_esitleme_neden"], str), "belge_esitleme_neden string olmalı"
