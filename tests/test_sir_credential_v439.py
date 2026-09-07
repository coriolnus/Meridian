"""test_sir_credential_v439 — TSK-064 YOL-1 Faz-0 (envanter çivisi) + Faz-1B (meridian
NOUS_API_KEY / KAPI_APIKEY → systemd `LoadCredential`).

BAĞLAM. TSK-049 pano token'ı için TEK bir sırrı ortam kanalından systemd credential kanalına
taşıdı (`api._read_dash_token` + `deploy/oracle-a1/dash_token_credential.sh`). O tur bir sırra
özeldi; bu tur aynı deseni SIR ERİŞİMİNİN TEK KAPISINA (`meridian.secrets`) taşır, yani
`secrets.get` üzerinden okuyan HER tüketici — `hermes._nous_headers` dahil — tek satır kod
değişmeden kazanır. Kazanımın kendisi ÖLÇÜLÜR (bölüm D): "otomatik kazanır" varsayım olarak
bırakılırsa, kanalın gerçekten o çağrı yolunda olup olmadığı ancak canlıda ortam kapandığında
öğrenilir.

NEDEN ORTAM KANALI YETMİYOR. Bu depoda ortam ÇOCUKLARA AKAR (`serve.sh` uvicorn'u `env=os.environ`
ile, `hermes_composite` ajan alt süreçlerini devralınan ortamla doğurur) — `NOUS_API_KEY` bugün
motor sürecinin VE onun doğurduğu her LLM ajan sürecinin `/proc/<pid>/environ`ında okunur hâlde.
`LoadCredential=` sırrı ortama HİÇ koymaz: systemd onu PID 1 olarak (sandbox'tan ÖNCE) okur,
`$CREDENTIALS_DIRECTORY` altına 0400 bir tmpfs dosyası bırakır, süreç bitince siler. Gerekçenin
tamamı: `deploy/oracle-a1/meridian.service.d/53-nous-kapi-credential.conf`.

BÖLÜMLER
  A. `secrets.credential_oku` sözleşmesi — v184'ün yedi senaryosunun GENELLEŞTİRİLMİŞİ.
  B. Çözüm SIRASI: credential → env → dosya → GCP (credential ÖNCE; faz-2'de ortam kapanınca
     davranış sessizce değişmesin diye).
  C. `status()` kanal beyanı — geçiş betiğinin farksal ölçümünün OKUYUCUSU.
  D. `hermes._nous_headers` DEĞİŞMEDEN kazanır (kablo ölçümü).
  E. Faz-0 envanteri: `deploy/sir_envanteri.yaml` ↔ spec §1 AD listesi (ayrışma çivisi).
  F. Drop-in: iki `LoadCredential=` satırı, betikle aynı kaynak yolları.
  G. Geçiş betiği: `bash -n`, `durum`, `--geri-al` dalı; hiçbir yolda DEĞER basılmaz.
  H. Kaynak sözlüğü tek-kaynak: `secrets.KAYNAKLAR` ↔ panonun `SRC_TR`si.

SIR DEĞERİ YOK: bu dosyadaki her değer SAHTEDİR ve adında öyle yazar.
"""
from __future__ import annotations

import os
import pathlib
import re
import subprocess

import pytest
import yaml

from meridian import secrets

REPO = pathlib.Path(__file__).resolve().parents[1]
SPEC = REPO / "docs" / "TASARIM-SIR-YOL1-2026-09-03.md"
ENVANTER = REPO / "deploy" / "sir_envanteri.yaml"
DROPIN = REPO / "deploy" / "oracle-a1" / "meridian.service.d" / "53-nous-kapi-credential.conf"
BETIK = REPO / "deploy" / "oracle-a1" / "sir_credential_gecis.sh"
APP_JS = REPO / "meridian" / "web" / "app.js"

#: Faz-1B'nin taşıdığı iki sır. Ad → credential kaynak dosyası (drop-in ile BİREBİR aynı olmalı).
FAZ1B = {"NOUS_API_KEY": "/etc/meridian/nous_api_key",
         "KAPI_APIKEY": "/etc/meridian/kapi_apikey"}


@pytest.fixture()
def kred(tmp_path, monkeypatch):
    """`CREDENTIALS_DIRECTORY`yi kuran yardımcı — systemd'nin yaptığının testteki karşılığı.
    Dizini KURAR ama dosya YAZMAZ ("dizin var, dosya yok" senaryosu tam olarak o hâli ölçer)."""
    d = tmp_path / "credentials"
    d.mkdir()
    monkeypatch.setenv("CREDENTIALS_DIRECTORY", str(d))
    secrets.clear_cache()
    yield d
    secrets.clear_cache()


@pytest.fixture()
def temiz(monkeypatch, tmp_path):
    """Dört kanalı da kapatır: credential dizini yok, GCP projesi yok, yerel depo boş bir tmp'de.
    Önbellek iki uçta da temizlenir — `get` 300 sn TTL'lidir ve komşu test kirletebilir."""
    from meridian import config
    monkeypatch.delenv("CREDENTIALS_DIRECTORY", raising=False)
    monkeypatch.delenv("MERIDIAN_GCP_PROJECT", raising=False)
    monkeypatch.setattr(config, "STATE", tmp_path / "bos_state")
    secrets.clear_cache()
    yield
    secrets.clear_cache()


# =================================================================================================
# A) `credential_oku` SÖZLEŞMESİ — v184'ün yedi senaryosunun genelleştirilmişi
# =================================================================================================

def test_A1_credential_dizini_yoksa_None(monkeypatch):
    """`CREDENTIALS_DIRECTORY` yoksa okuyucu KANAL YOK der (None) — istisna atmaz, boş string
    dönmez. Boş string en kötü hâl olurdu: `get` için "ayarlı ama değersiz"."""
    monkeypatch.delenv("CREDENTIALS_DIRECTORY", raising=False)
    assert secrets.credential_oku("NOUS_API_KEY") is None


def test_A2_ciplak_deger_okunur_sondaki_yenisatir_kirpilir(kred):
    r"""Sözleşmedeki biçim ÇIPLAK değerdir; `LoadCredential` dosyanın TAMAMINI taşır ve kaynağı
    `printf '%s\n'` yazar. Kırpılmazsa değere görünmez bir `\n` yapışır — `Authorization` başlığı
    bozulur ve arıza "anahtar yanlış" gibi okunur (en sinsi hâl: ayarlı ama çalışmıyor)."""
    (kred / "NOUS_API_KEY").write_text("sahte-nous-degeri\n", encoding="utf-8")
    assert secrets.credential_oku("NOUS_API_KEY") == "sahte-nous-degeri"


def test_A3_KEY_VALUE_bicimi_taninir(kred):
    """Operatörün `.env` alışkanlığı `AD=deger`dir ve o satırın credential kaynağına
    kopyalanması ÖNGÖRÜLEBİLİR bir kazadır (v184'te aynı hoşgörü `MERIDIAN_DASH_TOKEN=` için
    var). Önek sessizce YUTULMAZ, TANINIR: aksi hâlde değer `NOUS_API_KEY=...` olur, sır
    "ayarlı" görünür ve upstream hep 401 verirdi."""
    (kred / "NOUS_API_KEY").write_text("NOUS_API_KEY=sahte-onekli-deger\n", encoding="utf-8")
    assert secrets.credential_oku("NOUS_API_KEY") == "sahte-onekli-deger"


def test_A3b_BASKA_bir_adin_oneki_YUTULMAZ(kred):
    """Hoşgörü DAR olmalı: yalnız İSTENEN adın öneki tanınır. `KAPI_APIKEY=` ile başlayan bir
    dosya `NOUS_API_KEY` diye okunuyorsa kaynak dosyalar KARIŞMIŞTIR — bunu sessizce düzeltmek
    arızayı gizler; değer olduğu gibi döner ve upstream'in 401'i sınıfı görünür kılar."""
    (kred / "NOUS_API_KEY").write_text("KAPI_APIKEY=sahte-karisik\n", encoding="utf-8")
    assert secrets.credential_oku("NOUS_API_KEY") == "KAPI_APIKEY=sahte-karisik"


@pytest.mark.parametrize("icerik", ["", "\n", "   \n\n", "NOUS_API_KEY=\n"])
def test_A4_bos_dosya_None(kred, icerik):
    """Boş/yalnız-boşluk dosya bir DEĞER değildir → None (kanal yok), boş string DEĞİL.
    Önekli-ama-değersiz biçim (`NOUS_API_KEY=`) aynı kovadadır."""
    (kred / "NOUS_API_KEY").write_text(icerik, encoding="utf-8")
    assert secrets.credential_oku("NOUS_API_KEY") is None


def test_A5_dizin_var_dosya_yok_None(kred):
    """systemd BAŞKA bir credential yüklediğinde dizin kurulur ama bu ad İÇİNDE OLMAZ. Arıza
    değildir ve patlamamalıdır: gerçekten zorunlu olduğu kurulumda sessiz kalmayan yer
    systemd'dir — `LoadCredential=` kaynağı yoksa birim HİÇ başlamaz."""
    assert not (kred / "NOUS_API_KEY").exists()
    assert secrets.credential_oku("NOUS_API_KEY") is None


def test_A5b_dizin_diskte_yoksa_patlamaz(monkeypatch, tmp_path):
    """`CREDENTIALS_DIRECTORY` ayarlı ama dizin DİSKTE YOK (bayat ortam / elle export). Okuyucu
    istisna atarsa `secrets.get` çağıran HER yol düşer — sır okuma bir açılış kapısı değildir."""
    monkeypatch.setenv("CREDENTIALS_DIRECTORY", str(tmp_path / "yok-boyle-bir-dizin"))
    assert secrets.credential_oku("NOUS_API_KEY") is None


def test_A5c_okunamayan_dosya_None(kred):
    """İzin ayağı: dosya VAR ama okunamıyor (0000). `# sessiz-yutma:` işaretinin gerekçesi budur
    ve yutmanın yolu ÖLÇÜLÜR, varsayılmaz."""
    f = kred / "NOUS_API_KEY"
    f.write_text("sahte-okunamayan\n", encoding="utf-8")
    f.chmod(0o000)
    try:
        if os.access(f, os.R_OK):  # root / izin uygulamayan dosya sistemi
            pytest.skip("izinler uygulanmıyor (root ya da izin-duyarsız dosya sistemi) — ölçülemez")
        assert secrets.credential_oku("NOUS_API_KEY") is None
    finally:
        f.chmod(0o600)


def test_A6_yol_gecisi_engellenir(kred):
    """Ad bir DOSYA ADIDIR, yol değil. `../` taşıyan bir ad credential dizininin DIŞINA çıkarsa
    okuyucu keyfi dosya okuyan bir ilkele dönüşürdü — ve adı çağıran verir."""
    (kred.parent / "disarida").write_text("sahte-disarida\n", encoding="utf-8")
    assert secrets.credential_oku("../disarida") is None


# =================================================================================================
# B) ÇÖZÜM SIRASI — credential → env → dosya → GCP
# =================================================================================================

def test_B1_credential_ortami_YENER(kred, monkeypatch):
    """Geçişin FAZ 1'i tam olarak bu hâldir (iki kanal aynı anda canlı). Öncelik credential'da
    olmazsa faz 2'de ortam kapandığında davranış SESSİZCE değişirdi — ve betiğin farksal ölçümü
    (sahte ortam + gerçek credential) geçişi haklı olarak reddederdi."""
    monkeypatch.setenv("NOUS_API_KEY", "sahte-ortam-degeri")
    (kred / "NOUS_API_KEY").write_text("sahte-credential-degeri\n", encoding="utf-8")
    secrets.clear_cache()
    assert secrets.get("NOUS_API_KEY") == "sahte-credential-degeri"


def test_B2_credential_yoksa_ortam(kred, monkeypatch):
    """Kanal EKLENİR, bir yasa değiştirmez: credential dosyası yokken davranış BİREBİR bugünküdür."""
    monkeypatch.setenv("NOUS_API_KEY", "sahte-ortam-degeri")
    secrets.clear_cache()
    assert secrets.get("NOUS_API_KEY") == "sahte-ortam-degeri"


def test_B3_credential_ve_ortam_yoksa_yerel_depo(temiz, monkeypatch, tmp_path):
    """Üçüncü basamak (yerel operatör kasası) yerinde kalır — sıra credential ÖNÜNE eklendi,
    altındaki basamaklar KAYDIRILMADI."""
    from meridian import config
    monkeypatch.delenv("NOUS_API_KEY", raising=False)
    monkeypatch.setattr(config, "STATE", tmp_path / "kasa")
    secrets.set("NOUS_API_KEY", "sahte-dosya-degeri")
    assert secrets.get("NOUS_API_KEY") == "sahte-dosya-degeri"


def test_B4_hicbir_kanal_yoksa_None(temiz, monkeypatch):
    """Hiçbiri veremezse None — "sıfır" ile "bilmiyorum" ayrımı korunur (uydurma yasağı)."""
    monkeypatch.delenv("NOUS_API_KEY", raising=False)
    assert secrets.get("NOUS_API_KEY") is None


def test_B5_fetch_SIRASI_kaynakta_yazili():
    """Kablo ölçümü: `_fetch` GERÇEKTEN credential ile mi başlıyor? Davranış testleri
    credential'ın önce geldiğini gösterir ama okuyucunun `get`e bağlandığını değil — bu depodaki
    en pahalı yanlış-yeşil sınıfı (v184'ün 8. testiyle aynı disiplin)."""
    import inspect
    src = inspect.getsource(secrets._fetch)
    assert "credential_oku" in src, "_fetch credential kanalını HİÇ çağırmıyor — kanal kablolanmadı"
    assert src.index("credential_oku") < src.index("os.environ.get(name)"), \
        "credential ortamdan SONRA çağrılıyor — faz-2'de davranış sessizce değişir"


# =================================================================================================
# C) `status()` KANAL BEYANI — farksal ölçümün okuyucusu
# =================================================================================================

def test_C1_status_credential_kanalini_ADIYLA_soyler(kred, monkeypatch):
    """Geçiş betiğinin faz-2'si "hangi kanal okunuyor" sorusunu sorar; cevabı VEREN yüzey budur.
    Kaynak "env" derse geçiş erkendir ve betik durur."""
    monkeypatch.setenv("NOUS_API_KEY", "sahte-ortam-degeri")
    (kred / "NOUS_API_KEY").write_text("sahte-credential-degeri\n", encoding="utf-8")
    secrets.clear_cache()
    st = secrets.status()["NOUS_API_KEY"]
    assert st["set"] is True and st["source"] == "credential"


def test_C2_status_DEGERI_SIZDIRMAZ(kred):
    """Değişmez: `status()` en fazla MASKELİ ipucu verir. Credential kanalı bu yasayı gevşetemez."""
    (kred / "KAPI_APIKEY").write_text("sahte-cok-uzun-kapi-degeri\n", encoding="utf-8")
    secrets.clear_cache()
    st = secrets.status()
    assert "sahte-cok-uzun-kapi-degeri" not in str(st)
    assert str(st["KAPI_APIKEY"]["hint"]).startswith("••••")


def test_C3_source_of_sirasi_fetch_ile_AYNI(kred, monkeypatch):
    """`_source_of` `_fetch`in AYNASIDIR — ayrışırsa durum raporu gerçek çözüm sırasını değil
    ESKİ sırayı anlatır ve farksal ölçüm yanlış kanalı onaylar (tek-kaynak yasası)."""
    monkeypatch.setenv("KAPI_APIKEY", "sahte-ortam")
    (kred / "KAPI_APIKEY").write_text("sahte-kred\n", encoding="utf-8")
    secrets.clear_cache()
    assert secrets._source_of("KAPI_APIKEY") == "credential"
    assert secrets.get("KAPI_APIKEY") == "sahte-kred"


# =================================================================================================
# D) `hermes._nous_headers` DEĞİŞMEDEN KAZANIR
# =================================================================================================

def test_D1_nous_headers_credential_kanalindan_besleniyor(kred, monkeypatch):
    """Faz-1B'nin TÜM kazancı bu tek ölçümde: `_nous_headers` bir satır bile değişmeden, yalnız
    `secrets.get` üzerinden okuduğu için credential kanalına geçti. Ölçülmezse "otomatik kazanır"
    bir VARSAYIM olarak kalır — ve varsayım ancak canlıda ortam kapandığında ölçülür."""
    from meridian import hermes
    monkeypatch.setenv("NOUS_API_KEY", "sahte-ortam-nous")
    monkeypatch.setenv("KAPI_APIKEY", "sahte-ortam-kapi")
    (kred / "NOUS_API_KEY").write_text("sahte-kred-nous\n", encoding="utf-8")
    (kred / "KAPI_APIKEY").write_text("sahte-kred-kapi\n", encoding="utf-8")
    secrets.clear_cache()
    h = hermes._nous_headers()
    assert h["Authorization"] == "Bearer sahte-kred-nous"
    assert h["apikey"] == "sahte-kred-kapi"


def test_D2_nous_headers_kaynagi_DEGISMEDI():
    """"Değişmez" iddiası da ÖLÇÜLÜR: yardımcı hâlâ `secrets.get` üzerinden okumalı. Kendi
    credential okumasını eklemiş olsaydı tek-kaynak yasası kırılır, iki okuma yolu ayrışırdı."""
    import inspect
    from meridian import hermes
    src = inspect.getsource(hermes._nous_headers)
    assert "secrets.get('NOUS_API_KEY')" in src or 'secrets.get("NOUS_API_KEY")' in src
    assert "CREDENTIALS_DIRECTORY" not in src, \
        "hermes kendi credential okumasını eklemiş — tek kapı bozuldu"


# =================================================================================================
# E) FAZ-0 ENVANTERİ — `deploy/sir_envanteri.yaml` ↔ spec §1 (AYRIŞMA ÇİVİSİ)
# =================================================================================================

def _spec_tablosu() -> tuple[dict[str, list[tuple[str, bool]]], int, set[str]]:
    """Spec §1 tablosunu AD listesine indirger: {dosya: [(ad, sır-mı)]}, ayar sayısı, sınıf harfleri.

    YALNIZ ADLAR: tabloda değer yok ve olmayacak (§4 bedel maddesi). Parantez içi açıklama atılır,
    `·` ayırır, `AD_{A,B}` küme-parantezi açılır; büyük-harf biçimine uymayan hücre AD DEĞİLDİR
    (ör. "diğer 29 (…)") ve ayar SAYISINA düşer."""
    metin = SPEC.read_text(encoding="utf-8")
    s1 = metin.split("## 1.")[1].split("**Bulgu-1")[0]
    s2 = metin.split("## 2.")[1].split("## 3.")[0]
    ad_re = re.compile(r"^[A-Z][A-Z0-9_]*(?:<[A-Z]+>)?$")
    tablo: dict[str, list[tuple[str, bool]]] = {}
    ayar_sayisi = 0
    dosya = None
    for satir in s1.splitlines():
        if not satir.startswith("|") or satir.startswith("|---") or "| Dosya |" in satir:
            continue
        h = [c.strip() for c in satir.strip().strip("|").split("|")]
        if len(h) < 4:
            continue
        if h[0]:
            dosya = h[0].strip("`")
            tablo.setdefault(dosya, [])
        if dosya is None:
            continue
        hucre = re.sub(r"\([^)]*\)", " ", h[2]).replace("`", "")
        hucre = re.sub(r"([A-Z0-9_]+)\{([^}]*)\}",
                       lambda m: " · ".join(m.group(1) + p.strip() for p in m.group(2).split(",")),
                       hucre)
        sir = bool(re.search(r"\bSIR\b", h[3]))
        for parca in hucre.split("·"):
            parca = parca.strip()
            if ad_re.match(parca):
                tablo[dosya].append((parca, sir))
            else:
                m = re.search(r"diğer (\d+)", parca)
                if m:
                    ayar_sayisi += int(m.group(1))
    siniflar = set(re.findall(r"^\| ([A-D]) ·", s2, flags=re.M))
    return tablo, ayar_sayisi, siniflar


def _envanter() -> dict:
    return yaml.safe_load(ENVANTER.read_text(encoding="utf-8"))


def test_E0_spec_ayristirici_POZITIF_KONTROL():
    """Ayrıştırıcının kendisi ölçülür: sıfır/boş bir sonuç, çivinin "her şey eşit" demesine yol
    açardı (boş küme boş kümeye eşittir — yasanın en sessiz arızası)."""
    spec, ayar, siniflar = _spec_tablosu()
    assert len(spec) == 6, spec
    assert sum(len(v) for v in spec.values()) == 21
    assert ayar == 29 and siniflar == {"A", "B", "C", "D"}
    assert ("NOUS_API_KEY", True) in spec["/opt/meridian/.env"]
    assert ("NOUS_MODEL", False) in spec["/opt/meridian/.env"]


def test_E1_envanter_dosyasi_VAR_ve_kaynagini_gosterir():
    """Faz-0'ın çıktısı bir DOSYADIR: A1'de `cut -d= -f1` ile alınan canlı ad listesi ona karşı
    kıyaslanır. Kaynağını göstermeyen envanter türetilmemiş bir kopyadır."""
    assert ENVANTER.exists(), "deploy/sir_envanteri.yaml yok — Faz-0 çıktısı üretilmedi"
    env = _envanter()
    assert env["kaynak_belge"] == "docs/TASARIM-SIR-YOL1-2026-09-03.md"
    assert env["olcum"], "ölçüm tarihi yok — sayı taşıyan satır tarih taşır"


def test_E2_DOSYA_listesi_spec_ile_AYNI():
    """Ayrışma çivisinin birinci ayağı. Spec'e yeni bir sır dosyası girer de envanter
    güncellenmezse geçiş o dosyayı HİÇ görmez ve kanal sessizce eski hâlinde kalır."""
    spec, _, _ = _spec_tablosu()
    env = _envanter()
    assert {d["yol"] for d in env["dosyalar"]} == set(spec)


def test_E3_AD_listesi_spec_ile_AYNI():
    """İkinci ayak — asıl ölçüm. Envanter YALNIZ AD taşır ve (dosya, ad, sır-mı) üçlüsü spec §1
    tablosundan TÜRETİLİR; iki kopya ayrışırsa buradan öter (tek-kaynak yasası)."""
    spec, _, _ = _spec_tablosu()
    env = _envanter()
    beklenen = {(d, a, s) for d, lst in spec.items() for a, s in lst}
    olculen = {(d["yol"], v["ad"], bool(v["sir"])) for d in env["dosyalar"] for v in d["degiskenler"]}
    assert olculen == beklenen


def test_E4_ENVANTERDE_DEGER_YOK():
    """§4 bedel maddesi: sır DEĞERİ hiçbir dosyaya girmez. Envanterde `ad:` vardır, `deger:`
    ASLA — bu çivi olmadan "yalnız ad" bir niyet beyanı olurdu."""
    ham = ENVANTER.read_text(encoding="utf-8")
    assert not re.search(r"^\s*-?\s*(deger|value|secret|token|key)\s*:", ham, flags=re.M | re.I)
    for d in _envanter()["dosyalar"]:
        for v in d["degiskenler"]:
            assert set(v) <= {"ad", "sir"}, f"beklenmeyen alan: {set(v)}"


def test_E5_AYAR_SAYISI_ve_SINIFLAR_spec_ten():
    """hindsight `.env`inin 29 ayar satırı sır DEĞİLDİR ama faz-2'nin "3 + 29 ayrımı"nın ölçüsüdür;
    sınıf harfi de §2'nin donuk sözlüğünden gelir — envanter kendi sözlüğünü uyduramaz."""
    _, ayar_sayisi, siniflar = _spec_tablosu()
    env = _envanter()
    assert sum(d.get("ayar_sayisi", 0) for d in env["dosyalar"]) == ayar_sayisi
    assert {d["sinif"] for d in env["dosyalar"]} <= siniflar


def test_E6_FAZ1B_hedefi_envanterde_A_SINIFI():
    """Bu turun taşıdığı iki ad envanterde `/opt/meridian/.env` altında, SIR ve A sınıfı olmalı —
    B/C sınıfı bir sırrı `LoadCredential`a taşımak yarım kazanımdır ve öyle beyan edilir (§2)."""
    env = _envanter()
    motor = next(d for d in env["dosyalar"] if d["yol"] == "/opt/meridian/.env")
    assert motor["sinif"] == "A"
    adlar = {v["ad"] for v in motor["degiskenler"] if v["sir"]}
    assert set(FAZ1B) <= adlar


# =================================================================================================
# F) DROP-IN
# =================================================================================================

def test_F1_dropin_iki_LoadCredential_satiri_tasir():
    """Faz-1B'nin systemd ayağı. Kaynak yolları betiğin yazdığı yollarla BİREBİR aynı olmalı —
    ayrışırsa birim HİÇ açılmaz (`LoadCredential` kaynağı yoksa unit başlamaz)."""
    assert DROPIN.exists(), "53-nous-kapi-credential.conf yok"
    metin = DROPIN.read_text(encoding="utf-8")
    satirlar = {s.strip() for s in metin.splitlines() if s.strip().startswith("LoadCredential=")}
    assert satirlar == {f"LoadCredential={ad}:{yol}" for ad, yol in FAZ1B.items()}


def test_F2_dropin_kaynak_yollari_BETIKLE_ayni():
    """Tek-kaynak: aynı yol iki dosyada yazılı. Çivi olmadan betiğin YAZDIĞI dosya ile birimin
    OKUDUĞU dosya sessizce farklılaşır ve arıza ancak restart anında çıkar."""
    betik = BETIK.read_text(encoding="utf-8")
    for ad, yol in FAZ1B.items():
        assert yol in betik, f"{ad} kaynak yolu betikte yok: {yol}"


def test_F3_dropin_ORTAM_kanalini_KAPATMAZ():
    """Faz-1 kanal EKLER, kapatmaz: `EnvironmentFile`a dokunan bir DİREKTİF faz-2 olurdu ve tek
    başına kurulduğunda motoru NOUS_API_KEY'siz açardı. Ölçüm YORUMU DEĞİL DİREKTİFİ arar —
    gerekçe metni o adı elbette anar; `#` ile başlayan satır systemd için yoktur."""
    direktifler = [s.strip() for s in DROPIN.read_text(encoding="utf-8").splitlines()
                   if s.strip() and not s.strip().startswith("#")]
    assert not [s for s in direktifler if s.startswith("EnvironmentFile")]
    assert direktifler[0] == "[Service]"


def test_F4_dropin_credential_KIMLIGI_SIR_ADIYLA_AYNI():
    """`LoadCredential=<kimlik>:<yol>` — kimlik `$CREDENTIALS_DIRECTORY` altındaki DOSYA ADIDIR
    ve `secrets.credential_oku(ad)` tam olarak o adı arar. Kimlik sır adından farklı olsaydı
    (v184'teki `dash_token` gibi küçük harf) okuyucu dosyayı bulamaz, kanal sessizce ölürdü."""
    for satir in DROPIN.read_text(encoding="utf-8").splitlines():
        if satir.strip().startswith("LoadCredential="):
            kimlik = satir.split("=", 1)[1].split(":", 1)[0]
            assert kimlik in FAZ1B, kimlik


# =================================================================================================
# G) GEÇİŞ BETİĞİ
# =================================================================================================

def _sahte_ortam(tmp_path: pathlib.Path) -> tuple[pathlib.Path, dict]:
    """Betiğin dokunduğu üç kökü tmp'de kurar, `sudo`/`systemctl`/`curl`u sahteleriyle değiştirir.
    Betik `SIR_GECIS_KOK` ile bu köke yönlendirilir (kanca YALNIZ çivi içindir; boşken gerçek
    yollar kullanılır — bkz. betikteki şerh)."""
    kok = tmp_path / "kok"
    (kok / "etc/systemd/system/meridian.service.d").mkdir(parents=True)
    (kok / "etc/meridian").mkdir(parents=True)
    (kok / "opt/meridian").mkdir(parents=True)
    binn = tmp_path / "bin"
    binn.mkdir()
    (binn / "sudo").write_text('#!/bin/sh\ncase "$1" in chown) exit 0 ;; *) exec "$@" ;; esac\n')
    (binn / "systemctl").write_text(
        '#!/bin/sh\ncase "$*" in\n'
        '  "--version") echo "systemd 255 (255.4-1ubuntu8.4)"; exit 0 ;;\n'
        '  *) exit 0 ;;\nesac\n')
    (binn / "curl").write_text('#!/bin/sh\necho 200\n')
    for f in ("sudo", "systemctl", "curl"):
        (binn / f).chmod(0o755)
    ortam = dict(os.environ, PATH=f"{binn}:{os.environ['PATH']}", SIR_GECIS_KOK=str(kok))
    return kok, ortam


def test_G0_betik_sozdizimi_gecerli():
    """`bash -n` — teslimden önceki en ucuz kapı. Betik A1'de bakım penceresinde koşar; sözdizimi
    hatası orada bulunursa pencere yanar."""
    assert BETIK.exists(), "sir_credential_gecis.sh yok"
    r = subprocess.run(["bash", "-n", str(BETIK)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def test_G1_durum_alt_komutu_DEGISTIRMEDEN_rapor_verir(tmp_path):
    """Operatörün koşacağı İLK komut. `durum` hiçbir şeyi değiştirmez ve iki adı da listeler:
    "kurulu mu" sorusunun cevabı ölçülür, varsayılmaz (ops aracı teslim kapısı, §6)."""
    kok, ortam = _sahte_ortam(tmp_path)
    r = subprocess.run(["bash", str(BETIK)], capture_output=True, text=True,
                       env=ortam, cwd=str(tmp_path))
    assert r.returncode == 0, r.stdout + r.stderr
    for ad in FAZ1B:
        assert ad in r.stdout
    assert not (kok / "etc/systemd/system/meridian.service.d"
                      "/53-nous-kapi-credential.conf").exists()


def test_G2_durum_SIR_DEGERINI_BASMAZ(tmp_path):
    """Kaynak dosyada değer VARKEN durum raporu onu göstermemeli — `stat` gösterir, `cat`
    göstermez. 2026-09-02'de bir sır tam olarak böyle terminale düştü (URL-gömülü parola)."""
    kok, ortam = _sahte_ortam(tmp_path)
    (kok / "etc/meridian/nous_api_key").write_text("SAHTE-GIZLI-DEGER-42\n")
    r = subprocess.run(["bash", str(BETIK)], capture_output=True, text=True,
                       env=ortam, cwd=str(tmp_path))
    assert "SAHTE-GIZLI-DEGER-42" not in (r.stdout + r.stderr)


def test_G3_geri_al_ORTAM_kanalini_geri_koyar(tmp_path):
    """GERİ-ALIM DALI. Faz-2 `.env`ten satırı siler; geri alma onu credential kaynağından GERİ
    YAZAR (değer terminale hiç uğramaz) ve drop-in'i kaldırır. Bu dal ölçülmezse, bakım
    penceresinde arıza çıktığında geri dönüş yolu hiç denenmemiş olur."""
    kok, ortam = _sahte_ortam(tmp_path)
    dropin = (kok / "etc/systemd/system/meridian.service.d/53-nous-kapi-credential.conf")
    dropin.write_text(DROPIN.read_text(encoding="utf-8"))
    (kok / "etc/meridian/nous_api_key").write_text("SAHTE-GERI-DEGER\n")
    envf = kok / "opt/meridian/.env"
    envf.write_text("NOUS_MODEL=sahte-model\nKAPI_APIKEY=sahte-kapi\n")   # faz-2 satırı silmişti
    r = subprocess.run(["bash", str(BETIK), "--geri-al", "NOUS_API_KEY"],
                       capture_output=True, text=True, env=ortam, cwd=str(tmp_path))
    assert r.returncode == 0, r.stdout + r.stderr
    icerik = envf.read_text(encoding="utf-8")
    assert "NOUS_API_KEY=SAHTE-GERI-DEGER\n" in icerik
    assert "NOUS_MODEL=sahte-model\n" in icerik, "geri alma komşu satırları YEDİ"
    assert "KAPI_APIKEY=sahte-kapi\n" in icerik, "geri alma ÖTEKİ sırrın satırını yedi"
    assert not dropin.exists(), "drop-in kaldırılmadı — credential kanalı hâlâ yürürlükte"
    assert "SAHTE-GERI-DEGER" not in (r.stdout + r.stderr)


def test_G3b_geri_al_ENVDE_ZATEN_VARSA_satiri_COGALTMAZ(tmp_path):
    """Faz-2 koşulmamışken geri alma çağrılırsa satır `.env`te DURUYORDUR. İkinci bir
    `NOUS_API_KEY=` satırı eklemek en sinsi hâl olurdu: systemd son satırı okur, operatör ilkini
    düzenler ve iki değer sessizce ayrışır."""
    kok, ortam = _sahte_ortam(tmp_path)
    (kok / "etc/meridian/nous_api_key").write_text("SAHTE-GERI-DEGER\n")
    envf = kok / "opt/meridian/.env"
    envf.write_text("NOUS_API_KEY=sahte-eski\nNOUS_MODEL=sahte-model\n")
    r = subprocess.run(["bash", str(BETIK), "--geri-al", "NOUS_API_KEY"],
                       capture_output=True, text=True, env=ortam, cwd=str(tmp_path))
    assert r.returncode == 0, r.stdout + r.stderr
    icerik = envf.read_text(encoding="utf-8")
    assert icerik.count("NOUS_API_KEY=") == 1, icerik
    assert "NOUS_API_KEY=SAHTE-GERI-DEGER\n" in icerik


def test_G4_bilinmeyen_ad_REDDEDILIR(tmp_path):
    """Betik iki adı TANIR; üçüncüsü bir yazım hatasıdır. Sessizce hiçbir şey yapmamak en kötü
    hâl olurdu: operatör "geçiş yapıldı" sanır."""
    _, ortam = _sahte_ortam(tmp_path)
    r = subprocess.run(["bash", str(BETIK), "--faz1", "BOYLE_BIR_SIR_YOK"],
                       capture_output=True, text=True, env=ortam, cwd=str(tmp_path))
    assert r.returncode != 0
    assert "BOYLE_BIR_SIR_YOK" in (r.stdout + r.stderr)


def test_G5_betik_ZORUNLU_kapilari_tasir():
    """Yapısal kapı listesi (davranışsal olarak ancak A1'de ölçülebilenler): systemd ≥247 sürüm
    kapısı, 0400 root kaynak izni, `read -s` (değer terminale/argv'ye girmez) ve faz-2 ölçümünün
    kendi ardını toplayan `trap`ı. Biri düşerse geçiş güvenliğini kaybeder."""
    metin = BETIK.read_text(encoding="utf-8")
    for kapi in ("247", "0400", "read -s", "trap"):
        assert kapi in metin, f"betikte eksik kapı: {kapi}"


def test_G6_betik_DEGERI_ARGV_ye_KOYMAZ():
    """`ps` argv'yi HERKESE gösterir. Değer bir dosyadan `cat` ile akıtılır; `sed -i "s/…$deger/"`
    ya da `awk -v v="$deger"` sınıfı bir kullanım sırrı makinedeki her kullanıcıya açardı."""
    metin = BETIK.read_text(encoding="utf-8")
    assert not re.search(r'awk\s+-v\s+\w+="\$(deger|yeni|val)', metin)
    assert not re.search(r'sed\s+(-i\s+)?["\'][^"\']*\$(deger|yeni|val)', metin)


# =================================================================================================
# H) KAYNAK SÖZLÜĞÜ TEK-KAYNAK — `secrets.KAYNAKLAR` ↔ panonun `SRC_TR`si
# =================================================================================================

def test_H1_KAYNAKLAR_cozum_sirasini_anlatir():
    """Sözlük donuk: `status()["source"]` yalnız bu dört değerden birini döner ve sıra ÇÖZÜM
    sırasıdır (credential → env → dosya → GCP)."""
    assert secrets.KAYNAKLAR == ("credential", "env", "file", "gcp")


def test_H2_pano_sozlugu_KAYNAKLAR_ile_AYRISMAZ():
    """Pano `SRC_TR` ile kaynak adını Türkçeye çevirir; o sözlük `KAYNAKLAR`ın KOPYASIDIR ve
    kopya sessizce ayrışır. "credential" eklenip pano güncellenmezse operatör kanalı ADIYLA
    göremez ve farksal ölçümün pano ayağı körleşir (tek-kaynak yasası)."""
    m = re.search(r"const SRC_TR = \{([^}]*)\}", APP_JS.read_text(encoding="utf-8"))
    assert m, "app.js içinde SRC_TR bulunamadı"
    assert set(re.findall(r"(\w+):", m.group(1))) == set(secrets.KAYNAKLAR)
