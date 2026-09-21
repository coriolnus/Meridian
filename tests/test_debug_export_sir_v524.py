"""test_debug_export_sir_v524.py — TSK-209 (2026-09-21): `/api/debug_export` paketi PANO OTURUM
İMZA ANAHTARINI taşıyordu; vaat ile mekanizma ayrışmıştı.

ÖLÇÜLMÜŞ ZEMİN (Rol-1, 2026-09-21 — kodda, dosya İÇERİĞİ okunmadan).
`meridian/api.py::api_debug_export` süzgeci şöyleydi:

    skip = {"secrets.json"}
    if not f.is_file() or f.name in skip or f.suffix not in (".json", ".jsonl", ".yaml", ".csv"):

ve docstring'i "secrets.json ve bars/ KESİNLİKLE dışarıda: anahtar sızdırmayan, paylaşilabilir
teşhis paketi" diye VAAT ediyordu. `state/auth.json` uzantısı `.json`, `skip` kümesinde DEĞİL →
her pakete GİRİYORDU. O kaydın içinde ne var (KODDAN, `meridian/auth.py::set_password` —
değer okunmadı): `salt` + `hash` (scrypt n=2^15/r=8/p=1 parola özeti) ve `key`
(`_secrets.token_bytes(32)`, oturum çerezinin HMAC İMZA ANAHTARI, `auth._key`/`auth.issue_session`).
Paketi eline geçiren bir kişi GEÇERLİ OTURUM ÇEREZİ üretebilir — paket "paylaşılabilir" diye
etiketliydi.

VAADİ BUGÜN TUTAN ŞEY TESADÜFTÜ. `secrets.json.bak-20260915T073825Z-tsk189` (canlıda ölçülmüş ad)
pakete girmiyordu, ama sebebi dışlama DEĞİL: `Path.suffix` o adda
`.bak-20260915T073825Z-tsk189`tır ve izinli uzantı kümesinde yoktur. Aynı dosya
`state/secrets.bak.json` adını taşısaydı `suffix` `.json` olurdu ve İÇERİ GİRERDİ. Yani sır kararı
UZANTI SÜZGECİNE bağlıydı; bu testin ana iddiası kararın ondan BAĞIMSIZ ve ONDAN ÖNCE
verilmesidir.

SINIR: uç `_auth(request)` ile korumalıdır, yani uzaktan anonim sömürülemez. Ölçülen risk
PAKETİN PAYLAŞILMASIDIR — ucun adı ve docstring'i tam olarak onu teşvik ediyordu.

SINIFIN İKİNCİ YÜZEYİ DÜN KAPANDI: TSK-208 aynı sınıfı sprint kum havuzu tarafında kapattı
(`meridian/sprint.py`, `tests/test_sprint_sir_yedegi_v523.py`). Bu tur sınıflandırmayı
`meridian/config.py`ye TEK KAYNAK olarak taşır ve iki yüzeyi aynı yükleme bağlar.

NE ÇİVİLENİR
  1. `auth.json` sentetik ağaçta VARKEN pakete GİRMEZ (bugünkü kırmızı).
  2. `secrets.json`, `secrets.json.bak-…` ve `state/secrets.bak.json` üçü de GİRMEZ — üçüncüsü İZİNLİ
     uzantı (`.json`) taşıdığı hâlde (ikinci kırmızı: sır kararı uzantıdan bağımsız olmalı).
  3. DARALTMA YOK: sır olmayan normal defterler pakete girmeye devam eder (bedel yasası).
  4. Okunamayan dosya (0o000, izinli uzantı) → uç 500 DÖNMEZ, dosya pakete girmez ve
     `manifest.json` onu ADIYLA + nedeniyle taşır (Yasa 4: sessiz atlama yok, beyanlı atlama var).
  5. Manifest/paket hiçbir sır DEĞERİ ya da hash'i taşımaz — yalnız ADLAR.
  6. SPRINT REGRESYONU: `sprint._atlanir` bugünkü hükmü BİREBİR korur (kaynak taşındı, davranış
     değil).
  7. TEK KAYNAK: `api` ve `sprint` AYNI yüklemi (`config.sir_dosyasi_mi`) çağırır; ikinci bir
     tanım yok. Davranış bacağı da var — tek kaynağı oynatmak ucun hükmünü oynatır.
  8. (TUR 2 / F1) `auth.json` YEDEKLERİ de sırdır — İKİ YÜZEYDE birden (teşhis paketi + kum
     havuzu), ve genişlemenin SINIRI ölçülür (`auth_x.json`/`authz.json`/`auth.yaml` sır DEĞİL).

CANLIYA DOKUNMAZ: her şey `sandbox_state` altında tmp'de kurulur; `monkeypatch.undo()` YOKTUR.
"""
from __future__ import annotations

import io
import json
import os
import warnings
import zipfile

import pytest
from fastapi.testclient import TestClient

from meridian import api, auth, config, sprint

# Canlıda ÖLÇÜLEN sır yedeği adı (A1, 2026-09-21 — TSK-208/v523 ile aynı ad). Tek kaynak v517'dir;
# burada `state/` önekSİZ taban ad ile çalışılır çünkü uç `config.STATE` kökünü gezer.
from tests.test_yedek_sir_kopyasi_disla_v517 import DISLANMALI

SIR_YEDEGI = os.path.basename(DISLANMALI[0])

# İZİNLİ UZANTI TAŞIYAN sır adı. Bu ad canlıda YOKTUR ve olmadığı BEYAN EDİLİR (uydurma yasağı):
# ölçülen şey "bugün böyle bir dosya var" değil, "böyle adlandırılsaydı süzgeç onu tutamazdı".
# TSK-189 rotasyonu yedeği `secrets.json.bak-…` diye adlandırdı; `state/secrets.bak.json` aynı işin
# bir sonraki operatörün elinde alacağı kadar makul bir biçimdir ve sınıf aynıdır.
SIR_IZINLI_UZANTILI = "secrets.bak.json"

# `secrets.json` ailesinin İÇERİĞİ yerine kullanılan NİŞAN dizesi — pakette/manifestte görünürse
# sızıntı var. GERÇEK `state/secrets.json` bu testin hiçbir yerinde okunmaz/yazılmaz; her şey
# `sandbox_state`in tmp ağacındadır.
NISAN = "V524-SIZINTI-NISANI"

# Sentetik pano parolası. `auth.set_password` ≥12 karakter ister ve ucun kimlik kapısı (`_auth`)
# parola kuruluyken OTURUM ÇEREZİ ZORUNLU kılar — yani bu testin düzeneği ucu gerçek duruşuyla
# çağırır, kapıyı devre dışı bırakarak değil.
PAROLA = "v524-sentetik-parola"

# root olarak koşulursa 0o000 okuma kapısı ölçülemez. BEYAN ederiz, `skip` ETMEYİZ (§5 uydurma
# yasağı: "ölçülmedi" ile "ölçtüm, temiz" aynı renge boyanmaz).
_ROOT = hasattr(os, "geteuid") and os.geteuid() == 0

# Uçun BUGÜNKÜ izinli uzantı kümesi — testin kurulum çipası, ucun sabitinden TÜRETİLMEZ (türetilse
# uzantı kümesi değiştiği gün çivi de sessizce onunla birlikte kayardı).
IZINLI_UZANTILAR = (".json", ".jsonl", ".yaml", ".csv")


def _client() -> TestClient:
    """Yaşam döngüsü BAŞLATILMADAN istemci (v287/v454 emsali): `with TestClient(app)` scheduler ve
    hermes ipliklerini ayağa kaldırır — bu uç için gereksiz, paralel ajan penceresinde risk.

    Çerez `auth.issue_session()` ile GERÇEK imza anahtarından üretilir: kapı kapalı bırakılır ve
    testin ölçtüğü şey yetki değil PAKETİN İÇERİĞİ olur."""
    c = TestClient(api.app)
    c.cookies.set(auth.COOKIE_NAME, auth.issue_session())
    return c


def _imza_anahtari() -> str:
    """Sentetik ağaçtaki oturum İMZA ANAHTARINI döner — sızıntı nişanı olarak kullanılır.

    OKUNAN DOSYA `sandbox_state`in tmp ağacındadır ve bu testin kendi `auth.set_password`
    çağrısının ürünüdür; operatörün gerçek `state/auth.json`ı hiçbir zaman açılmaz. Nişanın
    UYDURMA olmaması taşıyıcıdır: `auth.json`ın sızdırdığı şey tam olarak bu alandır
    (`auth._key` → `auth._sign` HMAC), yani paket gövdesinde onu aramak, riskin kendisini ölçer."""
    return json.loads((config.STATE / "auth.json").read_text())["key"]


def _canli_state_kur(izinli_uzantili_sir: bool = True) -> dict[str, bytes]:
    """Sentetik CANLI `state/` ağacı kurar; "pakete GİRMESİ gereken" normal defterleri döndürür.

    `sandbox_state` `config.STATE`i tmp'ye çevirmiş, `history/`+`bars/` dizinlerini ve depodaki
    `goal.yaml`/`bounds.yaml`ı oraya koymuştur; buraya yalnız bu turun ölçtüğü girdiler eklenir.
    Sır dosyalarının içeriği NİŞANDIR — gerçek sır değeri hiçbir yerde okunmaz."""
    live = config.STATE
    (live / "portfolio.json").write_text('{"positions":{},"realized_pnl":0.0}')
    (live / "trades.jsonl").write_text('{"event":"v524_isaret"}\n')
    girmeli = {ad: (live / ad).read_bytes()
               for ad in ("portfolio.json", "trades.jsonl", "goal.yaml", "bounds.yaml")
               if (live / ad).exists()}
    assert len(girmeli) == 4, f"kurulum çipası: sentetik ağaçta normal defter eksik ({sorted(girmeli)})"

    # sır ailesi — üçü de AD olarak sırdır
    (live / "secrets.json").write_text('{"ALPACA_KEY":"%s-secrets"}' % NISAN)
    (live / SIR_YEDEGI).write_text('{"ALPACA_KEY":"%s-bak"}' % NISAN)
    if izinli_uzantili_sir:
        (live / SIR_IZINLI_UZANTILI).write_text('{"ALPACA_KEY":"%s-izinli"}' % NISAN)
    # PANO KİMLİK KAYDI GERÇEK YOLDAN DOĞAR: `auth.set_password` scrypt tuzu+özetini ve oturum
    # imza anahtarını kendi yazar (0600, atomik). Elle sahte bir sözlük yazmak dosyanın ŞEKLİNİ
    # taklit eder ama anahtar üretim yolunu ölçmezdi — ve `password_set()` yanlış dallanırdı.
    auth.set_password(PAROLA)
    assert auth.password_set(), "kurulum çipası: sentetik ağaçta parola kurulmadı"
    return girmeli


def _paket() -> tuple[zipfile.ZipFile, bytes, int]:
    """Ucu çağırır; (zip, ham gövde, http durumu) döner. 500'de zip açılmaz — çağıran durumu ölçer."""
    r = _client().get("/api/debug_export")
    if r.status_code != 200:
        return None, r.content, r.status_code          # type: ignore[return-value]
    return zipfile.ZipFile(io.BytesIO(r.content)), r.content, r.status_code


def _adlar() -> list[str]:
    z, _, kod = _paket()
    assert kod == 200, f"uç {kod} döndü — paket ölçülemez"
    return z.namelist()


def _manifest() -> dict:
    z, _, kod = _paket()
    assert kod == 200, f"uç {kod} döndü — manifest ölçülemez"
    return json.loads(z.read("manifest.json"))


# ==================================================================================================
# 1 — auth.json pakete girmez (BUGÜNKÜ KIRMIZI)
# ==================================================================================================
def test_1_auth_json_pakete_GIRMEZ(sandbox_state):
    """`state/auth.json` panonun scrypt parola özeti (`salt`+`hash`) ile oturum çerezinin HMAC İMZA
    ANAHTARINI (`key`) taşır (`meridian/auth.py`; 0600 atomik yazım). Paketi eline geçiren geçerli
    oturum çerezi ÜRETEBİLİR — yani "paylaşılabilir teşhis paketi" vaadi bu dosyayla tutulamaz."""
    _canli_state_kur()
    assert "state/auth.json" not in _adlar(), (
        "`auth.json` debug paketine girdi — pano oturum imza anahtarı paylaşılabilir bir zip'e "
        "kondu; ucun docstring'i 'anahtar sızdırmayan' diyor")


# ==================================================================================================
# 2 — sır ailesinin tamamı dışarıda; İZİNLİ UZANTI taşısa bile
# ==================================================================================================
@pytest.mark.parametrize("ad", ["secrets.json", SIR_YEDEGI, SIR_IZINLI_UZANTILI])
def test_2_sir_ailesi_izinli_uzanti_tasisa_da_GIRMEZ(sandbox_state, ad):
    """ÜÇÜNCÜ AD TAŞIYICIDIR. `secrets.json` bugün TAM ADLA, `secrets.json.bak-…` ise yalnızca
    `suffix` izinli kümede olmadığı için dışarıda kalıyordu — biri karar, diğeri TESADÜF.
    `state/secrets.bak.json` ikisini ayırır: sır adıdır ve `suffix`i `.json`dur. Sır kararı uzantıdan
    BAĞIMSIZ verilmiyorsa yalnız bu satır kırmızıya döner."""
    _canli_state_kur()
    if ad == SIR_IZINLI_UZANTILI:
        assert os.path.splitext(ad)[1] in IZINLI_UZANTILAR, (
            "kurulum çipası: ölçülen ad izinli uzantı taşımıyor — test kendi iddiasını ölçmüyor")
    assert f"state/{ad}" not in _adlar(), (
        f"`{ad}` debug paketine girdi — sır dosyasının yedeği/geçici kopyası da sırdır ve karar "
        f"uzantı süzgecine bırakılamaz")


# ==================================================================================================
# 3 — DARALTMA YOK (bedel yasası)
# ==================================================================================================
def test_3_normal_defterler_pakete_girmeye_devam_eder(sandbox_state):
    """Düzeltme paketi DARALTMAMALI: geniş bir desen (`*secret*`, `*.json`) hiçbir testi kırmadan
    teşhis paketini boşaltırdı ve operatör arızayı yerel defterde arayamazdı. Burada içerik
    bayt-bayt karşılaştırılır — 'ad listede var' yetmez, dosya sağlam girmiş olmalı."""
    girmeli = _canli_state_kur()
    z, _, kod = _paket()
    assert kod == 200, f"uç {kod} döndü"
    for ad, icerik in girmeli.items():
        assert f"state/{ad}" in z.namelist(), f"`{ad}` pakete GİRMEDİ — düzeltme paketi daralttı"
        assert z.read(f"state/{ad}") == icerik, f"`{ad}` pakette bozuldu"


# ==================================================================================================
# 4 — OKUNAMAYAN dosya: 500 YOK, beyanlı atlama VAR
# ==================================================================================================
def test_4_okunamayan_dosya_500_URETMEZ_ve_manifestte_ADIYLA_kayitlidir(sandbox_state):
    """Sır kararı uzantıdan önce verilince döngüye BAŞKA bir kırılganlık kalır: izinli uzantılı ama
    OKUNAMAYAN bir dosya `z.write` içinde `PermissionError` yükseltir ve UCUN TAMAMI 500 döner —
    teşhis paketi, teşhis edilmesi gereken anda kaybolur. Bu, TSK-208'in sprint tarafında ölçtüğü
    canlı arızanın (0600 root:root sır yedeği, `User=ubuntu`) API kardeşidir.

    Yasa 4 gereği atlama SESSİZ olamaz: dosya pakete girmez ama `manifest.json` onu ADIYLA ve
    NEDENİYLE taşır."""
    _canli_state_kur()
    kirik = config.STATE / "okunamaz_defter.json"
    kirik.write_text('{"v524":"okunamaz"}')
    os.chmod(kirik, 0o000)
    if _ROOT:
        warnings.warn(UserWarning(
            "v524/4: süreç root — 0o000 okuma kapısı root'u durdurmaz, bu testin ARIZA BACAĞI "
            "ÖLÇÜLMEDİ (atlanmadı: atlama iddiası da yeşil görünürdü)."))
    try:
        z, govde, kod = _paket()
        assert kod == 200, (
            f"uç {kod} döndü — okunamayan TEK dosya bütün teşhis paketini düşürdü: {govde[:300]!r}")
        adlar = z.namelist()
        manifest = json.loads(z.read("manifest.json"))
    finally:
        os.chmod(kirik, 0o600)         # tmp_path sökümü okuyabilsin

    if not _ROOT:
        assert "state/okunamaz_defter.json" not in adlar, "okunamayan dosya pakete girdi"
        kayitlar = manifest.get("okunamayan_dosyalar", [])
        assert [k.get("ad") for k in kayitlar] == ["okunamaz_defter.json"], (
            f"okunamayan dosya manifest'e ADIYLA yazılmadı — atlama sessiz: {manifest!r}")
        assert kayitlar[0].get("sebep"), f"atlamanın NEDENİ yazılmadı: {kayitlar[0]!r}"


# ==================================================================================================
# 5 — manifest ve paket yalnız AD taşır; DEĞER/hash taşımaz
# ==================================================================================================
def test_5_manifest_ve_paket_hicbir_sir_DEGERI_tasimaz(sandbox_state):
    """Manifest'e "dışarıda bırakılan sır dosyaları" ADLARIYLA girer — içerik, değer ya da hash
    ASLA. Adın kendisi zaten kodda yazılıdır; değeri yazmak ucun var olma sebebini (anahtar
    sızdırmamak) manifestin içinde yeniden delerdi. Nişan dizesi PAKETİN TAMAMINDA aranır: sır
    dosyası başka bir yoldan (ör. `.tail` dalı) sızarsa da burası kırmızıya döner."""
    _canli_state_kur()
    anahtar = _imza_anahtari()
    z, govde, kod = _paket()
    assert kod == 200, f"uç {kod} döndü"
    manifest = json.loads(z.read("manifest.json"))

    disarida = manifest.get("disarida_birakilan_sirlar", [])
    assert sorted(disarida) == sorted(["auth.json", "secrets.json", SIR_YEDEGI,
                                       SIR_IZINLI_UZANTILI]), (
        f"dışarıda bırakılan sır dosyaları manifest'e ADLARIYLA girmedi: {manifest!r}")
    metin = json.dumps(manifest)
    assert NISAN not in metin and anahtar not in metin, f"manifest sır DEĞERİ taşıyor: {manifest!r}"
    assert NISAN.encode() not in govde, (
        "`secrets.json` ailesinin İÇERİĞİ zip gövdesinde — bir dosya süzgeci atlatmış ya da "
        "manifest değeri yazmış")
    assert anahtar.encode() not in govde, (
        "OTURUM İMZA ANAHTARI zip gövdesinde — paketi eline geçiren geçerli çerez üretebilir; "
        "ucun docstring'indeki 'anahtar sızdırmayan' vaadi tutmuyor")


# ==================================================================================================
# 6 — SPRINT REGRESYONU: kaynak taşındı, hüküm taşınmadı
# ==================================================================================================
def test_6_sprint_atlama_hukmu_BIREBIR_korunur():
    """TSK-208 kararı: kaynak `config.py`ye taşınır, DAVRANIŞ taşınmaz. Bu çivi v523'ün
    ölçtüğünden bağımsız bir açıdan bakar — v523 yolu dosya sistemiyle ölçer, burası saf yüzeydir
    ve taşıma turunun tam olarak kırabileceği şeyi (kümenin içeriğini) doğrudan sorar."""
    for ad in ("auth.json", "secrets.json", SIR_YEDEGI, "secrets.json.tmp", "secrets.json.new",
               "HALT", "meridian.db", "meridian.db-wal", "meridian.db-shm",
               "bars", "bars_intraday", "intraday_bars", "sprint"):
        assert sprint._atlanir(ad), f"`{ad}` kum havuzuna kopyalanıyor — taşıma hükmü daralttı"
    for ad in ("portfolio.json", "trades.jsonl", "strategy.yaml", "goal.yaml", "bounds.yaml",
               "history", "events.jsonl", "scoreboard.json", "hypotheses.jsonl"):
        assert not sprint._atlanir(ad), f"`{ad}` artık atlanıyor — taşıma hükmü genişletti"


# ==================================================================================================
# 7 — TEK KAYNAK: iki yüzey, tek yüklem
# ==================================================================================================
def test_7a_sprint_ve_api_sabitleri_config_TEN_TURER():
    """Kimlik ölçümü (`is`): `sprint.SKIP_COPY_PATTERNS` `config`teki demetin KENDİSİ olmalı. Eşitlik
    (`==`) yetmez — birebir aynı içerikli İKİNCİ bir demet yazılsaydı `==` yeşil kalır ve kopyalar
    ilk ayrışmada sessizce ayrılırdı (tek-kaynak yasası)."""
    assert sprint.SKIP_COPY_PATTERNS is config.SIR_DESENLERI, (
        "`sprint.SKIP_COPY_PATTERNS` `config.SIR_DESENLERI`den TÜREMİYOR — desen listesinin ikinci "
        "bir tanımı var ve kopyalar sessizce ayrışır")
    assert set(config.SIR_TAM_ADLAR) <= sprint.SKIP_COPY, (
        f"sır TAM ADLARI sprint'in atlama kümesinde değil: "
        f"{sorted(set(config.SIR_TAM_ADLAR) - sprint.SKIP_COPY)}")


def test_7b_tek_kaynagi_oynatmak_UCUN_hukmunu_oynatir(sandbox_state, monkeypatch):
    """7a'nın DAVRANIŞ kardeşi ve asıl ısırığı: uç sınıflandırmayı ÇAĞRI ANINDA tek kaynaktan mı
    soruyor, yoksa kendi yerel kopyasından mı? Tek kaynağa yabancı bir ad eklenir; uç onu
    dışlamıyorsa `api.py` ikinci bir tanım taşıyor demektir.

    `portfolio.json` BİLEREK seçildi: 3. çivi onun pakete GİRDİĞİNİ ölçüyor, yani buradaki
    dışlanma yalnızca monkeypatch'ten gelebilir."""
    _canli_state_kur()
    assert "state/portfolio.json" in _adlar(), "kurulum çipası: `portfolio.json` zaten pakette yok"
    monkeypatch.setattr(config, "SIR_TAM_ADLAR", frozenset(config.SIR_TAM_ADLAR | {"portfolio.json"}))
    adlar = _adlar()
    assert "state/portfolio.json" not in adlar, (
        "tek kaynağa eklenen ad uçta hüküm doğurmadı — `api_debug_export` sır kümesinin İKİNCİ bir "
        "tanımını taşıyor (tek-kaynak yasası)")
    assert "portfolio.json" in _manifest().get("disarida_birakilan_sirlar", []), (
        "dışlama olmuş ama manifest'e yazılmamış — beyansız atlama")


def test_7c_sprint_DESEN_BACAGI_yalnizca_DESENDIR(monkeypatch):
    """`sprint._desen_atlar` sözleşmesi gereği YALNIZ desen bacağıdır; tam adlar oraya katılmaz.

    BU ÇİVİYİ BİR MUTASYON DOĞURDU (TSK-209 ölçümü, 2026-09-21). Taşıma turunun mutasyon
    bataryasında M9 — `_desen_atlar`a tam ad bacağını da katmak — v523'ün HİÇBİR çivisini
    kırmadı. Sebep: `_yalniz_desenle_atlanir` önce `ad not in SKIP_COPY` sorar ve
    `SKIP_COPY ⊇ config.SIR_TAM_ADLAR` olduğu için (7a bunu ayrıca ölçer) sonuç hiç değişmiyordu.
    Yani sözleşme DOĞRUYDU ama GÖZLEMLENEMİYORDU — ve gözlemlenemeyen bir sözleşme ilk yeniden
    yazımda sessizce kaybolur.

    KAYIP NE OLURDU: biri `auth.json`ı `SKIP_COPY`den düşürdüğü gün (örneğin "zaten sır kümesinde
    var" diye) bildirim kararı o adı "adı önceden bilinmeyen" sayıp HER kurulumda olay defterine
    yazmaya başlardı — TSK-208 tur 2'de (bulgu B3) tam olarak kapatılan çelişkinin geri gelmesi.

    ÖLÇÜM ARACI TUR 2'DE DEĞİŞTİ. Tur 1'de ayrımı `auth.json` görünür kılıyordu: tam ad kümesinde
    VARdı, hiçbir desenle eşleşMİYORDU. F1 (`auth.json*` deseni) o ayrımı TÜKETTİ — artık
    `SIR_TAM_ADLAR`ın HER üyesi bir desenle de eşleşiyor (tam savunma örtüşmesi), yani gerçek
    adlardan hiçbiri iki bacağı ayıramaz. Çivi bu yüzden SENTETİK bir ada taşındı: tek kaynağa
    monkeypatch ile hiçbir desene uymayan bir ad eklenir ve desen bacağının onu GÖRMEMESİ ölçülür.
    Sentetik ad bir zayıflama değil GÜÇLENDİRMEDİR — gerçek bir ada bağlıyken çivi, o adın desen
    durumu değiştiği gün (bugün olduğu gibi) sessizce anlamını kaybediyordu."""
    monkeypatch.setattr(config, "SIR_TAM_ADLAR",
                        frozenset(config.SIR_TAM_ADLAR | {"v524_sentetik_sir_adi"}))
    assert config.sir_dosyasi_mi("v524_sentetik_sir_adi"), (
        "kurulum çipası: sentetik ad tek kaynağa girmedi — çivi kendi iddiasını ölçmüyor")
    assert not sprint._desen_atlar("v524_sentetik_sir_adi"), (
        "DESEN bacağı TAM AD kümesini de soruyor — `_yalniz_desenle_atlanir`ın 'adı önceden "
        "bilinmeyen' ayrımı artık taşımıyor; tam ad kümesine giren her ad bildirime de sızar")
    assert sprint._desen_atlar("secrets.json") and sprint._desen_atlar("auth.json"), (
        "kurulum çipası: iki kanonik sır adı da desenle eşleşmeli (bilinçli SAVUNMA ÖRTÜŞMESİ — "
        "biri tam ad kümesinden düşse bile atlanmaya devam eder)")


# ==================================================================================================
# 8 — TUR 2 / F1: `auth.json` YEDEKLERİ de sırdır (Rol-1 düzeltme turu, 2026-09-21)
# ==================================================================================================
#: F1 öncesi ölçüm (Rol-1 + bu ajan, bağımsız): `config.sir_dosyasi_mi("auth.json.bak") → False`.
#: TAM AD kümesi kanonik adı tutuyordu, YEDEĞİNİ tutmuyordu — TSK-208'de 283 sprint kurulumunu
#: düşüren `secrets.json.bak-20260915T073825Z-tsk189` ile BİREBİR aynı sınıf (ELLE alınmış yedek).
AUTH_YEDEKLERI = ("auth.json.bak-20260921", "auth.json.tmp")

#: DARALTMA SINIRI — bu adlar sır DEĞİLDİR ve öyle kalmalıdır. `auth.json*` deseni `auth`
#: önekinin tamamını değil yalnız `auth.json` ile BAŞLAYAN adları yakalar.
AUTH_SIR_OLMAYANLAR = ("auth_x.json", "authz.json", "auth.yaml")


@pytest.mark.parametrize("ad", AUTH_YEDEKLERI)
def test_8a_auth_json_YEDEKLERI_IKI_YUZEYDE_de_disarida(sandbox_state, ad):
    """İKİ YÜZEY birden ölçülür — teşhis paketi VE kum havuzu. Tek yüzey ölçmek yetmezdi: tek
    kaynağın anlamı zaten "iki yüzey aynı hükmü verir"dir.

    `auth.json.bak-…` bugün teşhis paketine GİRMİYORDU ama sebebi dışlama DEĞİL TESADÜFTÜ
    (`.bak-…` izinli uzantı değil) — bu deponun dördüncü kez ölçtüğü tesadüf sınıfı. Kum havuzuna
    ise GERÇEKTEN kopyalanıyordu, yani oturum imza anahtarı `state/sprint/<sid>/state/` altında
    SANDBOX_KEEP kadar çoğalırdı.

    `state/auth.json.tmp` HAKKINDA DÜRÜST NOT: bu adı bugün HİÇBİR kod yolu ÜRETMİYOR — `auth._write`
    H9'dan beri `store.write_text`e devrediyor ve onun tmp adı `mkstemp` ile benzersizdir
    (`tmpXXXXXX.tmp`). Ad, eski sürümlerin bıraktığı ya da elle üretilen bir artığın sınıfını
    temsil eder; "bugün üretiliyor" İDDİA EDİLMİYOR."""
    _canli_state_kur()
    (config.STATE / ad).write_text('{"key":"%s-auth-yedek"}' % NISAN)

    z, govde, kod = _paket()
    assert kod == 200, f"uç {kod} döndü"
    assert f"state/{ad}" not in z.namelist(), (
        f"`{ad}` teşhis paketine girdi — bir sır dosyasının YEDEĞİ de sırdır (F1)")
    assert ad in json.loads(z.read("manifest.json")).get("disarida_birakilan_sirlar", []), (
        f"`{ad}` dışlandı ama manifest'e ADIYLA yazılmadı — beyansız atlama")
    assert NISAN.encode() not in govde, "yedeğin İÇERİĞİ zip gövdesinde"

    assert sprint._atlanir(ad), (
        f"`{ad}` kum havuzuna KOPYALANIYOR — TSK-208'in `secrets.json.bak-…` ile birebir aynı "
        f"sınıfı, bu kez pano oturum imza anahtarıyla")


@pytest.mark.parametrize("ad", AUTH_SIR_OLMAYANLAR)
def test_8b_auth_deseni_DARALTMA_YAPMAZ(sandbox_state, ad):
    """BEDEL YASASI — F1 bir GENİŞLEMEDİR ve genişlemenin SINIRI ölçülür.

    `auth*` ya da `*auth*` yazmak hiçbir testi kırmadan hem kum havuzunu hem teşhis paketini
    eksik doğururdu (HALT vakasının sınıfı). Desen `auth.json` ÖNEKİNE bağlıdır: `auth_x.json`
    (alt çizgi), `authz.json` (harf) ve `auth.yaml` (başka uzantı) eşleşMEZ.

    BEDEL AYRICA SAYILDI: yerel `state/` kökünün 93 girdisinde `auth` ile başlayan TEK ad
    `auth.json`dır; A1 canlı kökünde de (Rol-1, 145 ad) yalnız üç sır yakalanıyor. Yani F1'in
    bugünkü yanlış-pozitif maliyeti SIFIRDIR — ama sıfır olduğu ÖLÇÜLDÜ, varsayılmadı."""
    assert not config.sir_dosyasi_mi(ad), (
        f"`{ad}` sır sayılıyor — `auth.json*` deseni GENİŞ yazılmış; meşru bir defter hem teşhis "
        f"paketinden hem kum havuzundan sessizce düşer")
    assert not sprint._atlanir(ad), f"`{ad}` kum havuzuna girmiyor — desen kopyalamayı daralttı"

    _canli_state_kur()
    (config.STATE / ad).write_text('{"v524":"mesru-defter"}')
    z, _, kod = _paket()
    assert kod == 200, f"uç {kod} döndü"
    if ad.endswith((".json", ".yaml")):          # izinli uzantı → pakette GÖRÜNMELİ
        assert f"state/{ad}" in z.namelist(), (
            f"`{ad}` teşhis paketinden düştü — operatör arızayı yerel defterde arayamaz")
