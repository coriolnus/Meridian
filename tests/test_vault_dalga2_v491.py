"""test_vault_dalga2_v491.py — TSK-064 Faz-2 DALGA-2 (kalan bütün sırlar kasaya) REPO ÇİVİSİ.

NE ÇAKIYOR. Dalga-1 (v485) YALNIZ tek-değer dosyalarını taşıdı: bir `template` bloğu dosyanın
TAMAMINI yazar ve çok-değişkenli bir `.env`i kasadan render etmek, o dosyadaki AYAR satırlarının
da kasaya girmesini gerektirirdi. Dalga-2'nin kararı (spec §1) bu kısıtı kaldırmadan aşıyor:
Agent `<dosya>.vault` adında SIR-YALNIZ bir YAN DOSYA yazar, tüketici İKİ kaynağı birlikte okur.
Bu dosya o kararın repo tarafını çakar —

  A  Envanter: `vault_kv` dalga-2 girdileri + YENİ `vault_dosyalar` bloğu (şema, referans
     bütünlüğü, DEĞER YOK, önek sözlüğü, sahip sözlüğü)
  B  Üretici: `ops/vault_politika_uret.py` yan dosya şablonları + `exec` chown + render aralığı
  C  Birim ve tüketici bağlama: `vault-agent.service` yazma yüzeyi + drop-in'ler + A0 rolü
  D  `deploy/vault/vault_sir_koy.sh`: `env_satiri` kaynağı + KOPYA EŞİTLİĞİ kapısı
  E  `deploy/oracle-a1/sir_rotasyon.sh --vault`: kasadan başlayan rotasyon
  M  MUTASYONLAR — her çivinin hedeflediği dalı gerçekten ısırdığının kanıtı

NEDEN KAYNAK METNİ ÇİVİLERİ (v485 ile aynı gerekçe). Yerelde `vault` ikilisi YOKTUR, ajan A1'e
ssh yapmaz (CLAUDE.md §3) ve docker/hermes tüketicileri burada KOŞMAZ. Ölçülebilen şey
SÖZLEŞMEdir: hangi dosya, hangi alan, hangi kaynak, hangi sıra. Gerçek render, gerçek `--env-file`
çözümü ve hermes `env_loader`ın ikinci dosyayı okuyup okumadığı A1'de test-ateşlemesiyle ölçülür
(CLAUDE.md §9 "kurulu ≠ çalışır"); bu dosya o ölçümün YERİNE GEÇMEZ, önünü açar.

SIR DEĞERİ YASAĞI: hiçbir testte gerçek bir sır değeri yoktur; sahte değerler `SAHTE-` önekiyle
yazılır ve yalnız eşitlik/sha karşılaştırması için kullanılır.
"""
from __future__ import annotations

import os
import pathlib
import re
import subprocess

import pytest
import yaml

REPO = pathlib.Path(__file__).resolve().parents[1]
ENVANTER = REPO / "deploy" / "sir_envanteri.yaml"
VAULT_DIZIN = REPO / "deploy" / "vault"
AGENT_HCL = VAULT_DIZIN / "agent.hcl"
POLITIKA_AGENT = VAULT_DIZIN / "policies" / "meridian-agent.hcl"
BIRIM_AGENT = VAULT_DIZIN / "vault-agent.service"
URETICI = REPO / "ops" / "vault_politika_uret.py"
KOY_SH = VAULT_DIZIN / "vault_sir_koy.sh"
ROTASYON_SH = REPO / "deploy" / "oracle-a1" / "sir_rotasyon.sh"

#: DALGA-2'NİN SEKİZ SIRRI — sayı/ad burada ELLE durur (v485 DALGA1_SAYISI ile aynı gerekçe:
#: envanterden türetilseydi, envanterden bir satır düştüğünde çivi de onunla küçülür ve "her şey
#: uyuşuyor" derdi). Kaynak: spec §2.
DALGA2_ADLARI = (
    "openrouter_api_key",
    "bot_key_bekci",
    "bot_key_karne",
    "bot_key_sef",
    "bot_key_meridian",
    "pano_giris_parola",
    "hindsight_cp_access_key",
    "hindsight_cp_dataplane_api_key",
)

#: YAN DOSYALARIN TAM KÜMESİ (spec §2). Elle durur: envanterden türeyen bir liste, bir dosya
#: envanterden düştüğünde sessizce küçülürdü.
YAN_DOSYALAR = (
    "/opt/apisix/.env-apisix.vault",
    "/opt/hindsight/.env.vault",
    "/opt/hindsight/.env-cp.vault",
    "/home/ubuntu/.hermes/profiles/bekci/.env.vault",
    "/home/ubuntu/.hermes/profiles/karne/.env.vault",
    "/home/ubuntu/.hermes/profiles/sef/.env.vault",
    "/home/ubuntu/.hermes/.env.vault",
)

#: ÖNEK SÖZLÜĞÜ DONUKTUR ve TEK yerde yaşar: `sir_rotasyon.sh`in `ONEKLER` tablosu aynı iki
#: jetonu tanır (`-` ve `Bearer`). Envanterde önek LİTERAL DEĞİL JETONDUR — literal yazılsaydı
#: ("Bearer ") iki yazım (boşluklu/boşluksuz) sessizce ayrışırdı ve v485 E3'ün "değer yok"
#: taraması da onu bir sır değeri sanabilirdi.
ONEK_SOZLUGU = {None, "Bearer"}

#: Agent'ın render edeceği dosyanın SAHİBİ iki değerden biridir. `ubuntu` olan her dosya bir
#: `exec` chown gerektirir (Agent root koşar ve `template` bloğunda sahip parametresi YOKTUR —
#: resmî belge, ölçüldü 2026-09-14); `root` olan HİÇBİRİ gerektirmez.
SAHIP_SOZLUGU = {"root", "ubuntu"}

#: TAKMA AD TABLOSU — Rol-1 hükmü (2026-09-14, tur-2). Aynı DEĞERİ taşıyan sırların TEK kasa yolu
#: vardır; BİRİNCİL kasada ZATEN duran dalga-1 girdisidir, dalga-2 adı TAKMA ADdır. Tablo burada
#: ELLE durur (DALGA2_ADLARI ile aynı gerekçe): envanterden türetilseydi bir eşleme envanterden
#: düştüğünde çivi de onunla birlikte küçülür ve "her şey uyuşuyor" derdi.
#: Yön ÖNEMLİDİR: birincil dalga-1'dir çünkü değer kasada O YOLDA duruyor — tersini seçmek A1'de
#: bir göç (yeni yol + eski yolun emekliliği) gerektirirdi ve hükmün kazancı tam olarak bunun
#: gerekMEMESİdir.
TAKMA_ADLAR = {
    "openrouter_api_key": "HINDSIGHT_API_LLM_API_KEY",
    "bot_key_meridian": "kapi_apikey",
    "hindsight_cp_dataplane_api_key": "HINDSIGHT_API_TENANT_API_KEY",
}
TAKMA_AD_ALANI = "ayni_deger"


def _envanter() -> dict:
    return yaml.safe_load(ENVANTER.read_text(encoding="utf-8"))


def _vault_kv() -> list[dict]:
    return _envanter()["vault_kv"]


def _vault_dosyalar() -> list[dict]:
    veri = _envanter()
    assert "vault_dosyalar" in veri, (
        "deploy/sir_envanteri.yaml'da `vault_dosyalar` bloğu yok — dalga-2'nin yan dosya "
        "sözleşmesi envanterde DURMUYOR (spec §2)")
    return veri["vault_dosyalar"]


def _kv_adlari() -> set[str]:
    return {g["ad"] for g in _vault_kv()}


def _kv_yollu() -> list[dict]:
    """Kasada KENDİ yolu OLAN girdiler — takma adlar HARİÇ (`ayni_deger`)."""
    return [g for g in _vault_kv() if TAKMA_AD_ALANI not in g]


def _kasa_yolu(ad: str) -> str:
    """Bir `vault_kv` adının ÇÖZÜLMÜŞ kasa yolu: takma adda BİRİNCİLİNKİ."""
    ind = {g["ad"]: g for g in _vault_kv()}
    g = ind[ad]
    birincil = g.get(TAKMA_AD_ALANI)
    return ind[birincil]["vault_yolu"] if birincil else g["vault_yolu"]


def _yorumsuz(metin: str) -> str:
    """Kabuk/HCL yorum satırları düşürülmüş metin — "şerhte geçiyor" ile "kodda var" ayrımı."""
    return "\n".join(s for s in metin.splitlines() if not s.strip().startswith("#"))


def _birim_satirlari(yol: pathlib.Path, bolum: str | None = None) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    aktif: str | None = None
    for ham in yol.read_text(encoding="utf-8").splitlines():
        s = ham.strip()
        if not s or s.startswith("#"):
            continue
        if s.startswith("[") and s.endswith("]"):
            aktif = s[1:-1]
            continue
        if "=" not in s:
            continue
        if bolum is not None and aktif != bolum:
            continue
        k, _, v = s.partition("=")
        out.append((k.strip(), v.strip()))
    return out


def _degerler(yol: pathlib.Path, anahtar: str) -> list[str]:
    return [v for k, v in _birim_satirlari(yol) if k == anahtar]


# =================================================================================================
# A) ENVANTER — dalga-2 `vault_kv` girdileri + `vault_dosyalar` bloğu
# =================================================================================================

def test_A1_vault_kv_DALGA2_nin_SEKIZ_adini_tasir():
    """Sekiz ad da envanterde VE hepsi dalga-1 şemasına uyar. Bir ad eksik kalırsa Agent onu
    okuyamaz (politika ondan türer) ve yan dosya şablonu "dangling" bir referansa bakar."""
    adlar = _kv_adlari()
    eksik = [a for a in DALGA2_ADLARI if a not in adlar]
    assert not eksik, f"dalga-2 `vault_kv` girdisi eksik: {eksik}"


def test_A2_dalga2_girdileri_TEK_BICIM_semayi_KORUR():
    """`vault_yolu` = `secret/meridian/<ad>`, hedef `/etc/` altında, 0400 root — dalga-1'in
    şeması (v485 E2) dalga-2'de de GEÇERLİ. Şema gevşerse politika üretimi bir tahmin işine
    döner ve KV-v2'nin `data/` ara segmenti sessizce kayar."""
    for g in _vault_kv():
        if g["ad"] not in DALGA2_ADLARI:
            continue
        if TAKMA_AD_ALANI in g:
            # TAKMA AD: yol/hedef/mod/sahip BİRİNCİLİNDİR — kendi şeması T bölümünde ölçülür.
            continue
        assert g["vault_yolu"] == f"secret/meridian/{g['ad']}", g
        assert g["mod"] == "0400" and g["sahip"] == "root", g
        assert g["hedef"] == f"/etc/meridian/{g['ad']}", g


def test_A3_dalga2_girdisi_KAYNAK_tasir_ve_kaynak_semasi_DONUK():
    """`vault_sir_koy.sh` değeri NEREDEN alacağını envanterden okur (spec §4). Dalga-1'de kaynak
    hedefin KENDİSİYDİ (`/etc/meridian/<ad>` zaten dolu); dalga-2 sırları çok-değişkenli
    dosyaların İÇİNDE yaşıyor, yani kaynak bir `ALAN=` satırıdır ve envanterde YAZILI olmalı.
    Kaynağı beyan etmeyen bir girdi, taşımayı operatörün hafızasına bırakırdı."""
    for g in _vault_kv():
        if g["ad"] not in DALGA2_ADLARI:
            continue
        k = g.get("kaynak")
        assert isinstance(k, dict), f"{g['ad']}: `kaynak` bloğu YOK (spec §4)"
        assert set(k) == {"tur", "dosya", "alan", "onek"}, f"{g['ad']}: kaynak şeması ayrıştı: {sorted(k)}"
        assert k["tur"] in ("env_satiri", "dosya"), f"{g['ad']}: tanınmayan kaynak türü {k['tur']!r}"
        assert str(k["dosya"]).startswith("/"), f"{g['ad']}: kaynak yolu MUTLAK değil: {k['dosya']!r}"
        assert k["onek"] in ONEK_SOZLUGU, f"{g['ad']}: tanınmayan önek jetonu {k['onek']!r}"
        if k["tur"] == "env_satiri":
            assert re.fullmatch(r"[A-Z][A-Z0-9_]*", str(k["alan"] or "")), (
                f"{g['ad']}: env_satiri kaynağında ALAN adı yok/biçimsiz: {k['alan']!r}")
        else:
            assert k["alan"] is None, f"{g['ad']}: dosya kaynağında ALAN olamaz: {k['alan']!r}"


def test_A4_KOPYA_KAYNAKLARI_ayni_semayi_konusur():
    """Aynı sırrın ÖTEKİ kopyaları (spec §4: "14 kopya gerçekten aynı mı") aynı sözlükle yazılır.
    İkinci bir şema, kopya eşitliği kapısını sessizce yarım bırakırdı."""
    for g in _vault_kv():
        for kopya in g.get("kopya_kaynaklari") or []:
            assert set(kopya) == {"tur", "dosya", "alan", "onek"}, (
                f"{g['ad']}: kopya kaynağı şeması ayrıştı: {sorted(kopya)}")
            assert kopya["tur"] in ("env_satiri", "dosya"), kopya
            assert str(kopya["dosya"]).startswith("/"), kopya
            assert kopya["onek"] in ONEK_SOZLUGU, kopya


def test_A5_ROTASYON_SIRI_bagi_kopya_kumesiyle_BIREBIR():
    """AYRIŞMA ÇİVİSİ. `rotasyon_kopyalari` bloğu "bir değer döndüğünde hangi kopyalar aynı
    pencerede yazılmalı"nın TEK kaynağıdır. Bir dalga-2 sırrı o tabloda da yaşıyorsa (`rotasyon_siri`),
    kasaya taşınırken ölçülecek kopya kümesi ORADAN gelmek zorundadır — ikinci bir liste tutmak,
    TSK-181'in tam olarak ölçtüğü hâli (tabloya girmemiş bir kopya sessizce eski değerde yaşar)
    kasa tarafında yeniden üretirdi."""
    kopyalar = _envanter()["rotasyon_kopyalari"]["kopyalar"]
    tur_esleme = {"env": "env_satiri", "dosya": "dosya"}
    for g in _vault_kv():
        rot = g.get("rotasyon_siri")
        if not rot:
            continue
        beklenen = {
            (tur_esleme[k["tur"]], k["yol"], k.get("alan"), k.get("onek"))
            for k in kopyalar if k["sir"] == rot and k["tur"] in tur_esleme
        }
        gercek = {
            (k["tur"], k["dosya"], k["alan"], k["onek"])
            for k in [g["kaynak"], *(g.get("kopya_kaynaklari") or [])]
        }
        assert gercek == beklenen, (
            f"{g['ad']}: kaynak+kopya kümesi `rotasyon_kopyalari[{rot}]` ile AYRIŞTI.\n"
            f"  envanterde fazla: {sorted(gercek - beklenen)}\n"
            f"  rotasyonda fazla: {sorted(beklenen - gercek)}")


def test_A6_vault_dosyalar_SEMASI_ve_TAM_KUME():
    """Yan dosyaların sözleşmesi: mutlak yol, mod, sahip sözlüğü, tüketici beyanı, restart komutu
    ve EN AZ BİR satır. Satırsız bir yan dosya, Agent'ın BOŞ bir dosya render etmesi demektir —
    tüketici eski değerde kalır ve hiçbir şey bağırmaz."""
    dosyalar = _vault_dosyalar()
    yollar = [d["yol"] for d in dosyalar]
    assert yollar == list(YAN_DOSYALAR), f"yan dosya kümesi ayrıştı: {yollar}"
    for d in dosyalar:
        assert set(d) == {"yol", "mod", "sahip", "tuketici", "yeniden_baslat", "satirlar"}, (
            f"{d['yol']}: alan kümesi ayrıştı: {sorted(d)}")
        assert d["yol"].startswith("/") and d["yol"].endswith(".vault"), d["yol"]
        assert re.fullmatch(r"0[0-7]{3}", str(d["mod"])), f"{d['yol']}: mod biçimi: {d['mod']!r}"
        assert d["sahip"] in SAHIP_SOZLUGU, f"{d['yol']}: tanınmayan sahip {d['sahip']!r}"
        assert d["tuketici"], f"{d['yol']}: tüketici beyanı BOŞ (Yasa 6)"
        assert d["satirlar"], f"{d['yol']}: satır YOK — Agent BOŞ dosya render ederdi"
        for s in d["satirlar"]:
            assert set(s) == {"alan", "sir", "onek"}, f"{d['yol']}: satır şeması ayrıştı: {sorted(s)}"
            assert re.fullmatch(r"[A-Z][A-Z0-9_]*", s["alan"]), s
            assert s["onek"] in ONEK_SOZLUGU, s


def test_A7_yan_dosya_SATIRLARI_vault_kv_ye_REFERANSLI_dangling_YOK():
    """Her `satirlar[].sir` `vault_kv`de bir addır. Dangling bir referans, şablonun kasada
    OLMAYAN bir yolu okuması demektir: Agent 403/404 alır ve o dosya HİÇ render edilmez —
    tüketici eski kanalda kalır ve geçiş "yapıldı" sanılır."""
    adlar = _kv_adlari()
    eksik = [(d["yol"], s["sir"]) for d in _vault_dosyalar() for s in d["satirlar"]
             if s["sir"] not in adlar]
    assert not eksik, f"`vault_kv`de olmayan sır referansı: {eksik}"


def test_A8_yan_dosya_ASIL_dosyanin_YANINDA_ve_asil_dosya_envanterde_TANINIR():
    """`<dosya>.vault` adı bir üslup değil SÖZLEŞMEdir: tüketici iki kaynağı birlikte okur ve
    ikisi AYNI dizinde durur. Asıl dosya envanterin `dosyalar:`/`rotasyon_kopyalari` bloklarında
    TANINIYOR olmalı — tanınmayan bir asıl dosya, envanterin görmediği bir sır yüzeyidir."""
    veri = _envanter()
    bilinen = {d["yol"] for d in veri["dosyalar"]}
    bilinen |= {k["yol"] for k in veri["rotasyon_kopyalari"]["kopyalar"]}
    for d in _vault_dosyalar():
        asil = d["yol"][: -len(".vault")]
        assert asil in bilinen, (
            f"{d['yol']}: asıl dosya ({asil}) envanterde TANINMIYOR — envanterin görmediği bir "
            "sır yüzeyine yan dosya yazılıyor")


def test_A9_UBUNTU_sahipli_yan_dosya_YALNIZ_hermes_agacinda():
    """Agent'ın `exec` yetkisi (chown) TEK gerekçeyle var: hermes profil `.env`lerini `ubuntu`
    okur. Başka bir ağaçta `ubuntu` sahipliği istemek, o yetkinin gerekçesini sessizce
    genişletirdi (tasarım §6.3'ün "Agent tüketiciyi yeniden başlatmaz" ilkesinin komşusu)."""
    for d in _vault_dosyalar():
        if d["sahip"] == "ubuntu":
            assert d["yol"].startswith("/home/ubuntu/.hermes/"), (
                f"{d['yol']}: hermes ağacı DIŞINDA ubuntu sahipliği isteniyor")
        else:
            assert not d["yol"].startswith("/home/"), (
                f"{d['yol']}: /home altında root sahipli yan dosya — tüketici (ubuntu) okuyamaz")


def test_A10_ENVANTERDE_DEGER_YOK_kurali_dalga2_bloklarinda_da_GECERLI():
    """v439 E4 / v485 E3'ün aynı iddiası, iki yeni blok için. Önek JETONU (`Bearer`) bir değer
    DEĞİLDİR ve sözlüğü donuktur (yukarıda ölçülür); tarama onun dışındaki her yaprak dizgeyi
    gezer."""
    def yapraklar(dugum, yol=""):
        if isinstance(dugum, dict):
            for k, v in dugum.items():
                if k == "onek":
                    continue
                yield from yapraklar(v, f"{yol}.{k}")
        elif isinstance(dugum, list):
            for i, v in enumerate(dugum):
                yield from yapraklar(v, f"{yol}[{i}]")
        elif dugum is not None:
            yield yol, str(dugum)

    veri = _envanter()
    for blok in ("vault_kv", "vault_dosyalar"):
        for yol, deger in yapraklar(veri[blok], blok):
            assert not re.search(r"(?:^|[^A-Za-z])(sk-|hvs\.|Bearer\s)", deger), (
                f"{yol} sır değeri taşıyor olabilir: {deger!r}")


def test_A11_APISIX_yan_dosyasi_kapinin_DORT_SINIF_sirrini_tasir():
    """POZİTİF KONTROL — şema yeşilken kapsam boş kalabilir. `/opt/apisix/.env-apisix` dalga-2'nin
    en kalabalık dosyasıdır ve dördü de AYRI sınıftır: LLM anahtarı (+ `Bearer` önekli türevi),
    kapının YÖNETİM anahtarı, pano parolası, bot anahtarları. Biri düşerse kapı ya açılmaz ya da
    o yüzey eski kanalda kalır."""
    d = next(x for x in _vault_dosyalar() if x["yol"] == "/opt/apisix/.env-apisix.vault")
    alanlar = {s["alan"]: s for s in d["satirlar"]}
    for beklenen in ("OPENROUTER_API_KEY", "OPENROUTER_AUTH", "APISIX_ADMIN_KEY",
                     "PANO_GIRIS_PAROLA", "BOT_KEY_BEKCI", "BOT_KEY_KARNE", "BOT_KEY_SEF",
                     "BOT_KEY_MERIDIAN"):
        assert beklenen in alanlar, f"apisix yan dosyasında eksik alan: {beklenen}"
    assert alanlar["OPENROUTER_AUTH"]["onek"] == "Bearer", (
        "OPENROUTER_AUTH önek TAŞIMIYOR — kapının Authorization başlığı `Bearer ` olmadan geçersiz")
    assert alanlar["OPENROUTER_AUTH"]["sir"] == alanlar["OPENROUTER_API_KEY"]["sir"], (
        "OPENROUTER_AUTH ile OPENROUTER_API_KEY AYNI kasa yolundan gelmeli (türetilmiş değer)")


def test_A12_HINDSIGHT_failover_UYELERININ_ALTISI_da_yan_dosyada():
    """Zincir ÜYESİ ana anahtarı DEVRALMAZ (EDG-2026-080/081): altı üye satırı da kasadan
    gelmeli. Biri eksik kalırsa eski anahtar iptal edildiği gün o üye sessizce 401 alır ve zincir
    birincile düşer — rotasyonun en pahalı sessiz arıza sınıfı."""
    d = next(x for x in _vault_dosyalar() if x["yol"] == "/opt/hindsight/.env.vault")
    alanlar = {s["alan"] for s in d["satirlar"]}
    beklenen = {f"HINDSIGHT_API_{yuzey}_LLM_{n}_API_KEY"
                for yuzey in ("REFLECT", "CONSOLIDATION") for n in (1, 2, 3)}
    assert alanlar == beklenen, f"failover üye kümesi ayrıştı: {alanlar ^ beklenen}"
    assert {s["sir"] for s in d["satirlar"]} == {"openrouter_api_key"}, (
        "üye satırları tek kasa yolundan gelmeli (altısı da OpenRouter anahtarının kopyasıdır)")


# =================================================================================================
# B) ÜRETİCİ — `ops/vault_politika_uret.py` yan dosya şablonları
# =================================================================================================
# `deploy/vault/agent.hcl` ve `policies/*.hcl` ÜRETİLMİŞ dosyalardır (v485 §G): elle düzenlenen
# bir üretilmiş dosya bir sonraki üretimde sessizce geri alınır. Bu bölüm ÜRETİCİNİN dalga-2
# sözleşmesini ölçer; bayt eşitliğini v485 G2/G3 ölçmeye devam eder.

def _uretici():
    from tests.conftest import betikten_modul_yukle
    return betikten_modul_yukle(URETICI, "vault_politika_uret")


def _sablon_bloklari(metin: str) -> list[str]:
    """`template { … }` bloklarının gövdeleri — sırayla. Ayrıştırma satır tabanlıdır: bloklar
    üreticiden çıkar ve iç içe geçmezler (`exec { … }` HARİÇ, o da tek seviye)."""
    bloklar, birikim, derinlik = [], [], 0
    for satir in metin.splitlines():
        s = satir.strip()
        if derinlik == 0 and s == "template {":
            derinlik = 1
            birikim = []
            continue
        if derinlik:
            if s.endswith("{"):
                derinlik += 1
            elif s == "}":
                derinlik -= 1
                if derinlik == 0:
                    bloklar.append("\n".join(birikim))
                    continue
            birikim.append(satir)
    return bloklar


def test_B1_agent_POLITIKASI_dalga2_yollarini_da_READ_eder():
    """Politika `vault_kv`den TÜRER; dalga-2 yolları eklenmezse Agent onları OKUYAMAZ ve yan
    dosya HİÇ render edilmez (403). Joker YOK: kasaya yarın konacak bir sır Agent'a açılmaz."""
    metin = POLITIKA_AGENT.read_text(encoding="utf-8")
    yollar = set(re.findall(r'^path\s+"([^"]+)"', metin, re.M))
    for ad in DALGA2_ADLARI:
        # TAKMA ADIN yolu BİRİNCİLİNKİDİR: politikada aranan da odur, kendi adı DEĞİL.
        beklenen = _kasa_yolu(ad).replace("secret/", "secret/data/", 1)
        assert beklenen in yollar, f"politikada eksik dalga-2 yolu: {ad} → {beklenen}"


def test_B2_her_YAN_DOSYA_icin_BIR_sablon_ve_hedef_SIRASI_envanterden():
    """Şablon hedefleri = `vault_kv` hedefleri + `vault_dosyalar` yolları, ENVANTERİN SIRASIYLA.
    Sıra da sözleşmedir: iki liste arasında bir çivi yoksa biri sessizce ötekinden kopar."""
    metin = AGENT_HCL.read_text(encoding="utf-8")
    hedefler = re.findall(r'^\s*destination\s*=\s*"([^"]+)"', metin, re.M)
    beklenen = [g["hedef"] for g in _kv_yollu()] + [d["yol"] for d in _vault_dosyalar()]
    assert hedefler == beklenen, f"şablon hedefleri envanterle ayrıştı:\n{hedefler}\n{beklenen}"


def test_B3_yan_dosya_SABLONU_her_alan_icin_BIR_satir_uretir():
    """Şablonun satır sayısı envanterin satır sayısına EŞİT. Eksik bir satır, tüketicinin o
    değişkeni ESKİ kanaldan okuması demektir — geçiş yarım kalır ve hiçbir şey bağırmaz."""
    metin = AGENT_HCL.read_text(encoding="utf-8")
    for d in _vault_dosyalar():
        blok = [b for b in _sablon_bloklari(metin) if f'destination = "{d["yol"]}"' in b]
        assert len(blok) == 1, f"{d['yol']}: tam bir şablon bloğu bekleniyordu, {len(blok)} var"
        govde = blok[0]
        for s in d["satirlar"]:
            kalip = rf'^{re.escape(s["alan"])}=' + (r"Bearer " if s["onek"] == "Bearer" else "")
            assert re.search(kalip + r"\{\{ with secret", govde, re.M), (
                f"{d['yol']}: `{s['alan']}` satırı şablonda yok/biçimsiz")
        assert len(re.findall(r"^[A-Z][A-Z0-9_]*=", govde, re.M)) == len(d["satirlar"]), (
            f"{d['yol']}: şablon satır sayısı envanterle ayrıştı")


def test_B4_UBUNTU_sahipli_dosyada_EXEC_CHOWN_var_ROOT_sahiplide_YOK():
    """`template` bloğunda dosya SAHİBİ parametresi YOKTUR (yalnız `perms`; resmî belge, ölçüldü
    2026-09-14) ve Agent root koşar → render edilen dosya root:root olur. Tüketicisi `ubuntu`
    olan dosyalar için tek yol render sonrası `exec` chown'dur; KABUKSUZ ve SABİT argüman
    listesiyle. Root sahipli dosyada aynı `exec`, gereksiz bir yetki kullanımı olurdu."""
    metin = AGENT_HCL.read_text(encoding="utf-8")
    for d in _vault_dosyalar():
        blok = [b for b in _sablon_bloklari(metin) if f'destination = "{d["yol"]}"' in b][0]
        if d["sahip"] == "ubuntu":
            assert re.search(
                r'command\s*=\s*\["chown",\s*"ubuntu:ubuntu",\s*"' + re.escape(d["yol"]) + r'"\]',
                blok), f"{d['yol']}: exec chown YOK/biçimsiz (kabuksuz, sabit argüman listesi)"
        else:
            assert "exec" not in blok, f"{d['yol']}: root sahipli dosyada exec bloğu var"


def test_B5_RENDER_ARALIGI_bir_dakika_ve_TEK_yerde():
    """KV-v2 STATİK sırlar varsayılan 5 dk'da yeniden render edilir; rotasyon penceresindeki
    bekleme o süreyle SINIRLANIR. Değer `template_config` bloğunda TEK kez yaşar — ikinci bir
    yerde tekrarlanan bir süre, kadans değişince sessizce yalan olur (K7 sınıfı)."""
    metin = AGENT_HCL.read_text(encoding="utf-8")
    m = re.findall(r'static_secret_render_interval\s*=\s*"([^"]+)"', metin)
    assert m == ["1m"], f"render aralığı yok/tekrarlı: {m}"


def test_B6_agent_TUKETICIYI_YENIDEN_BASLATMAZ_exec_YALNIZ_chown():
    """Tasarım §6.4 KORUNUR: `exec` yetkisi dalga-2 ile doğdu ama SINIRI adıyla yazılıdır —
    `chown` bir restart DEĞİLDİR. Bir render'ın bakım penceresi dışında worker'ı düşürmesi hiçbir
    yerde verilmemiş bir yetkidir; restart operatörün/rotasyonun reçetesindedir."""
    metin = AGENT_HCL.read_text(encoding="utf-8")
    assert "systemctl" not in metin, "agent yapılandırmasına restart yolu sızmış"
    komutlar = re.findall(r"command\s*=\s*(\[[^\]]*\])", metin)
    assert komutlar, "exec komutu hiç yok — dalga-2'nin ubuntu sahipli dosyaları chown'suz kalır"
    for k in komutlar:
        assert k.startswith('["chown", "ubuntu:ubuntu", "/home/ubuntu/.hermes'), (
            f"exec komutu chown DIŞINDA bir şey yapıyor: {k}")


def test_B7_uretim_DETERMINISTIK_ve_diskteki_dosyalar_GUNCEL():
    """v485 G2/G3'ün dalga-2 tekrarı: üretici çalıştırıldığında disk BAYAT çıkmamalı. Tekrar
    burada çünkü yeni bir üretim dalı (yan dosyalar) eklendi ve bayatlık ancak o dal koşarken
    görünür."""
    mod = _uretici()
    assert mod.main(["--kontrol"]) == 0, (
        "üretilmiş dosyalar BAYAT — yeniden üret: python ops/vault_politika_uret.py --uygula")
    bir = {y.name: i for y, i in mod.beklenen()}
    iki = {y.name: i for y, i in mod.beklenen()}
    assert bir == iki, "üretim deterministik değil"


# =================================================================================================
# M) MUTASYONLAR — Task 1 (envanter + üretici)
# =================================================================================================
# ÇİVİ YEŞİLİ KANIT DEĞİLDİR (CLAUDE.md §6): yukarıdaki B çivileri yeşil olabilir ama hedefledikleri
# dalı hiç ısırmıyor olabilir. Her mutasyon, BİR dalı bilerek bozar ve o dalın çivisinin gerçekten
# kırmızıya döndüğünü ÖLÇER. Bozulan şey daima KAYNAK metnidir (üretici ya da envanter kopyası);
# depodaki hiçbir dosya değişmez.

def _mutant_uretici(tmp_path: pathlib.Path, eski: str, yeni: str, ad: str,
                    envanter: pathlib.Path | None = None):
    """Üreticinin MUTANT bir kopyası. `ENVANTER` yükleme sonrası enjekte edilir: kopya tmp'de
    doğduğu için kendi `parents[1]`i depo kökü DEĞİLDİR ve envanteri bulamazdı."""
    from tests.conftest import betikten_modul_yukle
    kaynak = URETICI.read_text(encoding="utf-8")
    assert eski in kaynak, f"mutasyon hedefi kaynakta yok (çivi bayatlamış): {eski!r}"
    hedef = tmp_path / f"{ad}.py"
    hedef.write_text(kaynak.replace(eski, yeni, 1), encoding="utf-8")
    mod = betikten_modul_yukle(hedef, ad)
    mod.ENVANTER = envanter or ENVANTER
    return mod


def test_M1_MUTASYON_exec_chown_dusurulurse_B4_KIRMIZI(tmp_path):
    """Senaryo: üretici `sahip: ubuntu` dalını atlar. Dosya render EDİLİR ama root:root kalır —
    hermes CLI (`ubuntu`) onu OKUYAMAZ ve bot her tetikte sessizce eski kanala düşer. Çıktı
    "başarılı" görünür; arıza ancak eski kanal kapatıldığında doğar."""
    mod = _mutant_uretici(tmp_path, '        if d["sahip"] != "root":', "        if False:",
                          "uret_mut_chown")
    metin = mod.agent_yapilandirmasi()
    ubuntu_dosyalari = [d for d in _vault_dosyalar() if d["sahip"] == "ubuntu"]
    assert ubuntu_dosyalari, "pozitif kontrol: ubuntu sahipli yan dosya YOK — mutasyon ölçemez"
    assert "chown" not in metin, "mutasyon uygulanmadı (çivi kendi hedefini kaybetmiş)"
    for d in ubuntu_dosyalari:
        blok = [b for b in _sablon_bloklari(metin) if f'destination = "{d["yol"]}"' in b][0]
        assert "exec" not in blok, "mutant yine de exec yazmış — mutasyon etkisiz"


def test_M2_MUTASYON_onek_dusurulurse_B3_KIRMIZI(tmp_path):
    """Senaryo: `onek` jetonu şablona yazılmaz. Kapının `OPENROUTER_AUTH` değeri `Bearer ` önekini
    KAYBEDER; upstream 401 verir ve arıza "kasa yanlış anahtar verdi" diye teşhis edilir — oysa
    anahtar doğrudur, başlık biçimi bozuktur (ölçülmüş sınıf: tırnak/önek biçimi)."""
    mod = _mutant_uretici(tmp_path, '            onek = ONEKLER[s.get("onek")]',
                          '            onek = ""', "uret_mut_onek")
    metin = mod.agent_yapilandirmasi()
    blok = [b for b in _sablon_bloklari(metin)
            if 'destination = "/opt/apisix/.env-apisix.vault"' in b][0]
    assert not re.search(r"^OPENROUTER_AUTH=Bearer ", blok, re.M), "mutasyon etkisiz"
    assert re.search(r"^OPENROUTER_AUTH=\{\{ with secret", blok, re.M), (
        "mutant beklenen bozuk biçimi üretmedi — mutasyon başka bir dalı vurmuş")


def test_M3_MUTASYON_dangling_referans_SESSIZCE_GECILMEZ(tmp_path):
    """Senaryo: bir yan dosya satırı `vault_kv`de OLMAYAN bir sırra bakar. Fail-closed olmasaydı
    o ALAN yan dosyada HİÇ doğmazdı: tüketici değişkeni eski kanaldan okumaya devam eder ve
    geçişin yarım kaldığı ancak eski kanal kapatıldığında — en pahalı anda — görünür."""
    bozuk = tmp_path / "envanter_bozuk.yaml"
    metin = ENVANTER.read_text(encoding="utf-8")
    eski = "{alan: PANO_GIRIS_PAROLA, sir: pano_giris_parola, onek: null}"
    assert eski in metin, "mutasyon hedefi envanterde yok (çivi bayatlamış)"
    bozuk.write_text(
        metin.replace(eski, "{alan: PANO_GIRIS_PAROLA, sir: OLMAYAN_SIR, onek: null}", 1),
        encoding="utf-8")
    mod = _mutant_uretici(tmp_path, "MONTAJ = \"secret\"", "MONTAJ = \"secret\"",
                          "uret_mut_dangling", envanter=bozuk)
    with pytest.raises(SystemExit) as hata:
        mod.agent_yapilandirmasi()
    assert "OLMAYAN_SIR" in str(hata.value), hata.value


def test_M4_MUTASYON_render_araligi_kayarsa_B5_KIRMIZI(tmp_path):
    """Senaryo: aralık varsayılana (5 dk) döner. Rotasyonun render beklemesi tavanı aşar ve
    pencere "ölçülemedi" ile kapanır — üstelik sebebi çıktıdan anlaşılmaz."""
    mod = _mutant_uretici(tmp_path, 'RENDER_ARALIGI = "1m"', 'RENDER_ARALIGI = "5m"',
                          "uret_mut_aralik")
    metin = mod.agent_yapilandirmasi()
    assert re.findall(r'static_secret_render_interval\s*=\s*"([^"]+)"', metin) == ["5m"], (
        "mutasyon etkisiz — çivi aralığı gerçekten ölçmüyor olabilir")


def test_M5_MUTASYON_yan_dosya_blogu_BOSSA_uretici_DURUR(tmp_path):
    """Fail-closed pozitif kontrolü: blok boşalırsa üretici PATLAR, sessizce dalga-1'e dönMEZ.
    Sessiz dönüş, `--kontrol` kapısının "GÜNCEL" demesi ve yan dosyaların hiç render edilmemesi
    demekti — yani geçiş "yapıldı" sanılırken hiçbir şey olmamış olurdu."""
    bozuk = tmp_path / "envanter_bos.yaml"
    metin = ENVANTER.read_text(encoding="utf-8")
    kesim = metin.index("\nvault_dosyalar:")
    bozuk.write_text(metin[:kesim] + "\nvault_dosyalar: []\n", encoding="utf-8")
    mod = _mutant_uretici(tmp_path, "MONTAJ = \"secret\"", "MONTAJ = \"secret\"",
                          "uret_mut_bos", envanter=bozuk)
    with pytest.raises(SystemExit):
        mod.agent_yapilandirmasi()


# =================================================================================================
# C) BİRİM + TÜKETİCİ BAĞLAMA — yazma yüzeyi, drop-in'ler, geri alım
# =================================================================================================
# Agent bir dosyayı YAZABİLİYOR olmalı (sandbox), tüketici de onu OKUYOR olmalı (drop-in). İkisi
# ayrı gerçektir ve ikisi de ayrı ayrı sessizce eksik kalabilir: yazamayan Agent dosyayı hiç
# doğurmaz, okumayan tüketici eski kanalda kalır. İkisi de "her şey yolunda" görünür.

DROPIN_DIZIN = REPO / "deploy"
ROL_DEFAULTS = REPO / "deploy" / "ansible" / "roles" / "meridian_a1" / "defaults" / "main.yml"


def _yan_dosya_dizinleri() -> set[str]:
    return {str(pathlib.PurePosixPath(d["yol"]).parent) for d in _vault_dosyalar()}


def _hedef_dizinleri() -> set[str]:
    return {str(pathlib.PurePosixPath(g["hedef"]).parent) for g in _kv_yollu()}


def _birim_dropinleri(birim: str) -> list[pathlib.Path]:
    """`deploy/` altında `<birim>.d/*.conf` — nerede yaşadıklarına bakmaksızın (apisix kendi
    dizininde, hindsight kendi dizininde; drop-in birimin YANINDA durur)."""
    return sorted(DROPIN_DIZIN.rglob(f"{birim}.d/*.conf"))


def _birim_dosyasi(birim: str) -> pathlib.Path:
    adaylar = sorted(DROPIN_DIZIN.rglob(birim))
    assert len(adaylar) == 1, f"{birim}: tam bir birim dosyası bekleniyordu: {adaylar}"
    return adaylar[0]


def test_C1_agent_YAZMA_YUZEYI_iki_blogun_dizinlerinden_TURER():
    """`ReadWritePaths` = `vault_kv` hedeflerinin DİZİNLERİ ∪ `vault_dosyalar` yan dosyalarının
    DİZİNLERİ. Dalga-2'nin bedeli tam olarak bu satırdır: Agent root koşar, `ProtectSystem=strict`
    onun tek frenidir ve yazma yüzeyi `/opt/apisix`, `/opt/hindsight`, hermes ağacıyla GENİŞLER
    (spec "Kabul edilen bedeller"). Genişleme SESSİZ olamaz — envanterden TÜRER ve burada ölçülür;
    envanterde olmayan bir dizine yazma izni ya da izinsiz bir hedef, ikisi de kırmızıdır."""
    beyan = set((_degerler(BIRIM_AGENT, "ReadWritePaths") or [""])[-1].split())
    beklenen = _hedef_dizinleri() | _yan_dosya_dizinleri()
    assert beyan == beklenen, (
        f"agent yazma yüzeyi envanterle AYRIŞTI.\n  birimde fazla: {sorted(beyan - beklenen)}"
        f"\n  envanterde fazla: {sorted(beklenen - beyan)}")


def test_C2_agent_CHOWN_YETENEGI_TEK_ve_DAR():
    """`CapabilityBoundingSet=` dalga-1'de BOŞTU ve bu doğruydu: Agent yalnız dosya yazıyordu.
    Dalga-2'nin `exec` chown'u root için bile CAP_CHOWN İSTER — boş kümede `chown ubuntu:ubuntu`
    EPERM ile düşer, dosya root:root kalır ve hermes onu okuyamaz. Yetenek EKLENİR ama TEK ve
    ADIYLA: ikinci bir yetenek, sapmanın gerekçesini sessizce genişletirdi."""
    deger = (_degerler(BIRIM_AGENT, "CapabilityBoundingSet") or [""])[-1]
    assert deger.split() == ["CAP_CHOWN"], (
        f"agent yetenek kümesi TEK ve CAP_CHOWN olmalı (dalga-2 exec chown'u): {deger!r}")


def test_C3_agent_HOME_yazma_deligi_BIRIM_SERHINDE_beyanli():
    """`ProtectHome=read-only` duruyor ve `ReadWritePaths` onun içine BİR DELİK açıyor (hermes
    ağacı). Bu, `ProtectSystem=strict` + `/etc` deliği ile aynı sınıftır ve aynı şekilde BEYANLI
    olmak zorundadır: birim dosyasını okuyan mühendis "home salt-okunur" satırını görüp yanlış bir
    güvene kapılmamalı. A1'de KURULDUĞU GÜN ölçülür (kurulu ≠ çalışır)."""
    assert (_degerler(BIRIM_AGENT, "ProtectHome") or [None])[-1] == "read-only"
    metin = BIRIM_AGENT.read_text(encoding="utf-8")
    assert "ProtectHome" in metin.split("[Service]")[0] or "/home/ubuntu" in metin, (
        "hermes ağacına yazma beyanı birim şerhinde yok")
    serh = "\n".join(s for s in metin.splitlines() if s.strip().startswith("#"))
    assert "ProtectHome" in serh and "A1" in serh, (
        "ProtectHome deliği ve A1 ölçümü birim şerhinde ADIYLA beyan edilmemiş")


def test_C4_SYSTEMD_tuketicisi_olan_her_yan_dosyanin_DROP_INI_var():
    """`yeniden_baslat` bir birim adıysa o birimin drop-in'i yan dosyayı ADIYLA okumalı. Drop-in
    yoksa Agent dosyayı render eder ve KİMSE okumaz — Yasa 6'nın tam tanımı, üstelik geçiş
    "yapıldı" sanılırken."""
    for d in _vault_dosyalar():
        birim = d["yeniden_baslat"]
        if not birim:
            # BEYANLI İSTİSNA: hermes ağacı. Tüketici bir systemd birimi değil hermes CLI'dır ve
            # `env_loader`ın İKİNCİ bir dosyayı okuyup okumadığı YERELDE ÖLÇÜLEMEZ (ajan A1'e ssh
            # yapmaz). Ölçülmemiş bir yeteneği "var" saymak geçişi sessizce yarım bırakırdı;
            # beyan ADIYLA durur ve ölçüm A1 penceresine aittir.
            assert "A1'DE ÖLÇÜLECEK" in d["tuketici"], (
                f"{d['yol']}: systemd tüketicisi YOK ve ölçüm beyanı da yok: {d['tuketici']!r}")
            continue
        metinler = "\n".join(p.read_text(encoding="utf-8") for p in _birim_dropinleri(birim))
        assert d["yol"] in metinler, (
            f"{d['yol']}: `{birim}` drop-in'lerinde bu yan dosyaya atıf YOK — render edilir ama "
            "kimse okumaz (Yasa 6)")


def test_C5_yan_dosya_EnvironmentFile_OPSIYONEL_isaretli():
    """`EnvironmentFile=-<yol>` — eksi işareti GERİ ALIM YOLUDUR: kasa hiç kurulmadan ya da Agent
    durdurulduktan sonra dosya YOKSA birim yine açılır ve eski kanalla koşar (tasarım §6.4).
    İşaretsiz bir satır, yan dosyayı bir AÇILIŞ ÖN ŞARTINA çevirirdi — yani kasanın arızası
    tüketicinin arızası olurdu."""
    bulundu = 0
    for conf in DROPIN_DIZIN.rglob("*.service.d/*.conf"):
        for satir in conf.read_text(encoding="utf-8").splitlines():
            s = satir.strip()
            if not s.startswith("EnvironmentFile=") or ".vault" not in s:
                continue
            bulundu += 1
            assert s.startswith("EnvironmentFile=-"), (
                f"{conf.name}: yan dosya opsiyonel değil ({s!r}) — kasa arızası tüketiciyi düşürür")
    assert bulundu >= 2, f"yan dosya EnvironmentFile satırı bulunamadı (çivi kör): {bulundu}"


def _execstart_jetonlari(metin: str) -> list[str]:
    """`ExecStart=` satırının (devam eden `\\` satırlarıyla birlikte) jetonları. Boş `ExecStart=`
    sıfırlaması ATLANIR: drop-in'de o satır bir SIFIRLAMADIR, bir komut değil."""
    jetonlar: list[str] = []
    devam = False
    for ham in metin.splitlines():
        s = ham.strip()
        if not devam:
            if not s.startswith("ExecStart=") or s == "ExecStart=":
                continue
            s = s[len("ExecStart="):]
        if s.endswith("\\"):
            s, devam = s[:-1], True
        else:
            devam = False
        jetonlar.extend(s.split())
    return jetonlar


def test_C6_apisix_DROP_IN_ExecStartI_TEMEL_BIRIMDEN_TURER():
    """ZORUNLU KOPYA + AYRIŞMA ÇİVİSİ. systemd'de `ExecStart`a bir bayrak EKLEMENİN yolu yoktur:
    drop-in önce onu SIFIRLAR, sonra TAMAMINI yeniden yazar. Yani komut satırı iki yerde yaşar ve
    tek-kaynak yasasının izin verdiği tek hâl budur — "kopya kaçınılmazsa türetme + ayrışma
    çivisi". İmaj sürümü, mount, ağ kipi temel birimde değişip drop-in'de değişmezse kapı ESKİ
    imajla açılır ve kimse fark etmez.

    İDDİA: drop-in'in jeton listesi = temel birimin jeton listesi + TAM OLARAK bir
    `--env-file <yan dosya>` çifti, ve yan dosya ASIL dosyadan SONRA gelir (docker aynı anahtarı
    taşıyan iki dosyada SONRAKİNİ geçerli sayar — sıra burada bir tercih değil, hükümdür)."""
    d = next(x for x in _vault_dosyalar() if x["yol"] == "/opt/apisix/.env-apisix.vault")
    temel = _execstart_jetonlari(_birim_dosyasi("apisix.service").read_text(encoding="utf-8"))
    dropinler = _birim_dropinleri("apisix.service")
    assert dropinler, "apisix.service.d drop-in'i YOK"
    metin = "\n".join(p.read_text(encoding="utf-8") for p in dropinler)
    assert re.search(r"^ExecStart=\s*$", metin, re.M), (
        "drop-in `ExecStart=` sıfırlaması taşımıyor — systemd ikinci bir ExecStart'ı EKLER ve "
        "konteyner İKİ kez başlatılırdı")
    yeni = _execstart_jetonlari(metin)
    assert "--env-file" in temel, "pozitif kontrol: temel birim --env-file kullanmıyor"
    i = yeni.index(d["yol"])
    assert yeni[i - 1] == "--env-file", f"yan dosya --env-file ile verilmemiş: {yeni[i - 2:i + 1]}"
    asil = d["yol"][: -len(".vault")]
    assert yeni.index(asil) < i, "yan dosya ASIL dosyadan ÖNCE geliyor — eski değer kazanır"
    assert yeni[: i - 1] + yeni[i + 1:] == temel, (
        "drop-in ExecStart'ı temel birimden BAŞKA bir şeyde de ayrışmış:\n"
        f"  drop-in: {yeni}\n  temel  : {temel}")


def test_C7_yeniden_baslat_birimleri_GERCEKTEN_var():
    """`yeniden_baslat` bir birim ADIdır ve o birim depoda VAR olmalı. Var olmayan bir ada restart
    atmak, rotasyonun bakım penceresinde "Unit not found" ile düşmesi demektir."""
    for d in _vault_dosyalar():
        if d["yeniden_baslat"]:
            assert _birim_dosyasi(d["yeniden_baslat"]).exists()


def test_C8_A0_ROLU_yeni_DROP_IN_dizinlerini_tasiyor():
    """Rol drop-in'leri `dropin_dizinleri`/`dropin_kaynaklari` listelerinden kopyalar. Yeni bir
    drop-in dizini listelere girmezse dosya REPODA durur, A1'e HİÇ gitmez — ve kimse bağırmaz
    (v451 bu eşitliği iki yönlü ölçer; burada dalga-2 kapsamı ADIYLA sabitlenir)."""
    veri = yaml.safe_load(ROL_DEFAULTS.read_text(encoding="utf-8"))
    for birim in sorted({d["yeniden_baslat"] for d in _vault_dosyalar() if d["yeniden_baslat"]}):
        dizin = f"{birim}.d"
        if not _birim_dropinleri(birim):
            continue
        assert dizin in veri["dropin_dizinleri"], f"A0 rolü `{dizin}` dizinini taşımıyor"
        assert any(pathlib.PurePath(g).parent.name == dizin for g in veri["dropin_kaynaklari"]), (
            f"A0 rolü `{dizin}` için KAYNAK glob'u taşımıyor")


def test_C9_MUTASYON_drop_in_yan_dosyayi_dusurse_C4_KIRMIZI(tmp_path):
    """Senaryo: drop-in'den yan dosya satırı silinir. Agent render etmeye DEVAM eder, tüketici
    eski kanaldan okur — ve iki-kanal dönemi bittiğinde (asıl dosyadan sır satırları kalkınca)
    tüketici ANAHTARSIZ kalır. Çivi bu hâli yakalamalı."""
    d = next(x for x in _vault_dosyalar() if x["yeniden_baslat"] == "hindsight-api.service")
    conf = _birim_dropinleri("hindsight-api.service")
    metin = "\n".join(p.read_text(encoding="utf-8") for p in conf)
    assert d["yol"] in metin, "pozitif kontrol: drop-in yan dosyayı taşımıyor"
    bozuk = "\n".join(s for s in metin.splitlines() if d["yol"] not in s)
    assert d["yol"] not in bozuk, "mutasyon etkisiz"


def test_C10_POZITIF_KONTROL_yazma_yuzeyi_dalga1_kumesini_GERCEKTEN_asar():
    """POZİTİF KONTROL — MUTASYON DEĞİL, ve adı bunu söylemeli (inceleme bulgusu, tur-2).

    C1 iki kümenin EŞİT olduğunu söyler; eşitlik, iki küme de dalga-1'in iki dizininde donmuş
    olsaydı da sağlanırdı. Bu çivi o körlüğü kapatır: beklenen küme dalga-1'i GERÇEKTEN kapsar
    ve ondan BÜYÜKTÜR. Kaynağa dokunmadığı için "MUTASYON" etiketi yanıltıcıydı — gerçek
    mutasyonlar M/D7/E5/T serisindedir."""
    beklenen = _hedef_dizinleri() | _yan_dosya_dizinleri()
    dalga1 = {"/etc/meridian", "/etc/hindsight/creds"}
    assert dalga1 < beklenen, "pozitif kontrol: dalga-2 hiçbir yeni dizin eklemiyor"
    assert dalga1 != beklenen, "mutasyon (dalga-1 kümesi) çiviye eşit — çivi kör"


# =================================================================================================
# D) `deploy/vault/vault_sir_koy.sh` — env_satiri kaynağı + KOPYA EŞİTLİĞİ kapısı (Task 3)
# =================================================================================================
# Dalga-1'de taşımanın kaynağı hedefin KENDİSİYDİ (`/etc/meridian/<ad>` zaten doluydu). Dalga-2
# sırları çok-değişkenli dosyaların İÇİNDE yaşıyor — kaynak bir `ALAN=` satırıdır — ve aynı değerin
# on üç kopyası var. Bu bölüm iki şeyi ölçer: değer DOĞRU kopyadan okunuyor mu, ve ÖTEKİ kopyalar
# gerçekten aynı mı. İkincisi bu turun en pahalı kapısıdır: kasa TEK KAYNAK olduğu an, yanlış bir
# kopyadan taşımak hatayı BÜTÜN tüketicilere yayar (TSK-181'in daha pahalı hâli).

SAHTE_DEGER_D = "SAHTE-DALGA2-DEGERI-0001"
SAHTE_JETON_D = "SAHTE-hvs-yonetici-jetonu"


def _sahte_vault(tmp_path: pathlib.Path) -> tuple[pathlib.Path, pathlib.Path, pathlib.Path]:
    """PATH'e konacak sahte `vault`: her çağrıyı ARGV'siyle log'lar, `kv put`un STDIN'ini saklar.
    Gerçek bir kasayla konuşmaz — ölçtüğü şey betiğin KENDİ davranışıdır."""
    binler = tmp_path / "sahte-bin"
    binler.mkdir(exist_ok=True)
    argv_log = tmp_path / "argv.log"
    kasa = tmp_path / "kasa"
    kasa.mkdir(exist_ok=True)
    (binler / "vault").write_text(
        "#!/usr/bin/env bash\n"
        f'echo "$*" >> "{argv_log}"\n'
        f'if [ "$1" = "kv" ] && [ "$2" = "put" ]; then cat > "{kasa}/$(echo "$3" | tr / _)"; exit 0; fi\n'
        f'if [ "$1" = "kv" ] && [ "$2" = "get" ]; then cat "{kasa}/$(echo "$4" | tr / _)"; exit 0; fi\n'
        "exit 0\n")
    (binler / "vault").chmod(0o755)
    return binler, argv_log, kasa


def _dalga2_sahne(tmp_path: pathlib.Path, kopya_degeri: str | None = None) -> pathlib.Path:
    """Kaynak dosyalar + KÜÇÜK bir envanter. Gerçek `/etc` ya da `/opt` yollarına DOKUNULMAZ.

    `kopya_degeri` verilirse ikinci kopya bilerek AYRI yazılır — "13 kopya gerçekten aynı mı"
    sorusunun kırmızı hâli."""
    kaynak = tmp_path / "kaynaklar"
    kaynak.mkdir(exist_ok=True)
    apisix = kaynak / "env-apisix"
    apisix.write_text(
        f'OPENROUTER_API_KEY="{SAHTE_DEGER_D}"\n'
        f'OPENROUTER_AUTH="Bearer {SAHTE_DEGER_D}"\n'
        "PANO_GIRIS_PAROLA=sahte-parola\n", encoding="utf-8")
    hermes = kaynak / "hermes.env"
    hermes.write_text(f"OPENROUTER_API_KEY={kopya_degeri or SAHTE_DEGER_D}\n", encoding="utf-8")
    env = tmp_path / "envanter.yaml"
    env.write_text(yaml.safe_dump({"vault_kv": [{
        "ad": "sahte_anahtar",
        "vault_yolu": "secret/meridian/sahte_anahtar",
        "hedef": str(kaynak / "etc_sahte_anahtar"),
        "mod": "0400", "sahip": "root",
        "tuketici": "vault_dosyalar şablonları (çivi sahnesi)",
        "rotasyon_siri": None,
        "kaynak": {"tur": "env_satiri", "dosya": str(apisix),
                   "alan": "OPENROUTER_API_KEY", "onek": None},
        "kopya_kaynaklari": [
            {"tur": "env_satiri", "dosya": str(apisix), "alan": "OPENROUTER_AUTH",
             "onek": "Bearer"},
            {"tur": "env_satiri", "dosya": str(hermes), "alan": "OPENROUTER_API_KEY",
             "onek": None},
        ],
    }]}, allow_unicode=True), encoding="utf-8")
    return env


def _koy_ortam(tmp_path: pathlib.Path, binler: pathlib.Path, env_yaml: pathlib.Path) -> dict:
    import sys as _sys
    jeton = tmp_path / "admin.token"
    jeton.write_text(SAHTE_JETON_D + "\n", encoding="utf-8")
    return dict(os.environ, PATH=f"{binler}:{os.environ['PATH']}",
                VAULT_BIN=str(binler / "vault"), ENVANTER=str(env_yaml),
                PYTHON_BIN=_sys.executable, HOME=str(tmp_path),
                VAULT_TOKEN_FILE=str(jeton))


def test_D1_koy_betigi_KAYNAK_SOZLESMESINI_envanterden_okur():
    """Kaynak türü ve alan adı BETİĞE YAZILMAZ, envanterden gelir. Elle yazılmış bir eşleme,
    envantere eklenen bir sırrın burada sessizce eksik kalması demektir (I8'in dalga-2 hâli)."""
    metin = _yorumsuz(KOY_SH.read_text(encoding="utf-8"))
    assert "env_satiri" in metin, "betik `env_satiri` kaynak türünü tanımıyor (dalga-2)"
    assert "kopya_kaynaklari" in metin, "kopya eşitliği kapısı betikte yok"
    for d in _vault_dosyalar():
        for s in d["satirlar"]:
            assert s["alan"] not in metin, f"{s['alan']} betiğe ELLE yazılmış (ikinci kaynak)"


def test_D2_koy_betigi_DEGERI_DEGISKENE_ALMAZ_ve_cat_ikamesi_YOK():
    """Değer yalnız BORUdan akar. `$(cat …)` ya da `deger=$(…)` biçimi onu bir kabuk değişkenine
    koyar; oradan bir hata mesajına, bir `set -x`e ya da `/proc/<pid>/environ`a sızması yalnız bir
    satır uzaktadır."""
    metin = _yorumsuz(KOY_SH.read_text(encoding="utf-8"))
    assert "$(cat" not in metin and "$(<" not in metin, "komut ikamesiyle dosya okunuyor"
    assert not re.search(r"^\s*set\s+-[a-z]*x", metin, re.M), "set -x açık"
    # sha256 komut ikamesi SERBESTTİR ve gerekçesi budur: `$( )` içinde AKAN şey HASH'tir, değer
    # değil. Ayrımı ölçmek için her komut ikamesinin gövdesi `_sha` ile bitmeli ya da değer
    # taşımamalı — aşağıdaki iddia `_deger`in ASLA bir ikameye girmediğini söyler.
    assert not re.search(r"=\s*\"?\$\(\s*_deger\b", metin), (
        "`_deger` çıktısı bir değişkene alınıyor — değer boruda KALMALI")


def test_D3_KURU_kosum_KAYNAGI_ve_KOPYA_OLCUMUNU_basar_kasaya_DOKUNMAZ(tmp_path):
    """Kuru koşum bu turda yalnız bir ön izleme değil, bir ÖLÇÜMDÜR: 13 kopyanın gerçekten aynı
    olup olmadığı taşımadan ÖNCE burada görünür. Ama hüküm vermez ve kasaya TEK çağrı yapmaz."""
    binler, argv_log, _ = _sahte_vault(tmp_path)
    r = subprocess.run(["bash", str(KOY_SH), "--kuru"], capture_output=True, text=True,
                       env=_koy_ortam(tmp_path, binler, _dalga2_sahne(tmp_path)))
    assert r.returncode == 0, f"kuru koşum düştü:\n{r.stdout}\n{r.stderr}"
    assert not argv_log.exists(), f"kuru koşum kasaya çağrı yaptı:\n{argv_log.read_text()}"
    assert "OPENROUTER_API_KEY" in r.stdout, "kuru koşum kaynak ALANINI söylemiyor"
    assert "EŞİT" in r.stdout, "kuru koşum kopya ölçümünü basmıyor"
    assert SAHTE_DEGER_D not in r.stdout, "kuru koşum DEĞER bastı"


def test_D4_UYGULA_env_satirindan_ONEKI_ve_TIRNAGI_soyarak_tasir(tmp_path):
    """Kaynak satır `ALAN="deger"` biçiminde olabilir ve `OPENROUTER_AUTH` önekli bir TÜREVDİR.
    Tırnak ya da önek soyulmazsa kasaya `"deger"` veya `Bearer deger` girer; Agent onu şablona
    olduğu gibi basar ve kapı upstream'de 401 alır — arıza kasada değil biçimde aranır."""
    binler, argv_log, kasa = _sahte_vault(tmp_path)
    r = subprocess.run(["bash", str(KOY_SH), "--uygula"], capture_output=True, text=True,
                       env=_koy_ortam(tmp_path, binler, _dalga2_sahne(tmp_path)))
    assert r.returncode == 0, f"uygula düştü:\n{r.stdout}\n{r.stderr}"
    konan = (kasa / "secret_meridian_sahte_anahtar").read_text(encoding="utf-8")
    assert konan == SAHTE_DEGER_D, f"kasaya konan değer biçimsiz: {konan!r}"
    assert SAHTE_DEGER_D not in argv_log.read_text(encoding="utf-8"), (
        "DEĞER ARGV'ye girdi — `ps` ile makinedeki herkese görünür")
    assert SAHTE_DEGER_D not in r.stdout, "değer terminale basıldı"


def test_D5_KOPYA_AYRISMASI_UYGULA_kipinde_DURDURUR_ve_kopyayi_ADIYLA_soyler(tmp_path):
    """TSK-181'in kasa tarafındaki hâli: bir kopya eski değerde kalmışsa, HANGİSİNİN doğru olduğu
    bilinemez. Taşımak bir tahmindir ve tahminin bedeli bütün tüketicilere yayılır — o yüzden
    betik DURUR, ayrışan kopyayı ADIYLA basar ve kasaya HİÇBİR ŞEY koymaz."""
    binler, argv_log, kasa = _sahte_vault(tmp_path)
    sahne = _dalga2_sahne(tmp_path, kopya_degeri="SAHTE-ESKI-KALMIS-ANAHTAR")
    r = subprocess.run(["bash", str(KOY_SH), "--uygula"], capture_output=True, text=True,
                       env=_koy_ortam(tmp_path, binler, sahne))
    assert r.returncode != 0, f"ayrışan kopyayla taşıma DURMADI:\n{r.stdout}"
    assert "hermes.env" in r.stdout, f"ayrışan kopya ADIYLA basılmıyor:\n{r.stdout}"
    assert not (kasa / "secret_meridian_sahte_anahtar").exists(), (
        "ayrışmaya rağmen kasaya yazıldı — yarım taşıma, taşımamaktan tehlikelidir")
    argv = argv_log.read_text(encoding="utf-8") if argv_log.exists() else ""
    assert "kv put" not in argv, f"ayrışmaya rağmen `kv put` çağrıldı:\n{argv}"


def test_D6_KOPYA_AYRISMASI_KURU_kipinde_RAPORLANIR_hukum_VERILMEZ(tmp_path):
    """Kuru koşum RAPORLAR, HÜKÜM VERMEZ (betiğin kendi sözleşmesi). Ayrışmada çıkış 1 vermek,
    operatörün listenin geri kalanını hiç görememesi demekti — oysa kuru koşumun bütün değeri
    "bugün ne var, ne yok"u BİR BÜTÜN olarak göstermesidir."""
    binler, argv_log, _ = _sahte_vault(tmp_path)
    sahne = _dalga2_sahne(tmp_path, kopya_degeri="SAHTE-ESKI-KALMIS-ANAHTAR")
    r = subprocess.run(["bash", str(KOY_SH), "--kuru"], capture_output=True, text=True,
                       env=_koy_ortam(tmp_path, binler, sahne))
    assert r.returncode == 0, f"kuru koşum ayrışmada DURDU (hüküm verdi):\n{r.stdout}"
    assert "AYRI" in r.stdout, f"kuru koşum ayrışmayı RAPORLAMIYOR:\n{r.stdout}"
    assert not argv_log.exists(), "kuru koşum kasaya çağrı yaptı"


def test_D7_MUTASYON_kopya_kapisi_silinirse_D5_KIRMIZI(tmp_path):
    """Çivi yeşili kanıt değildir: kapı kaldırıldığında ayrışan kopyayla taşıma SESSİZCE geçmeli
    (yani D5 gerçekten o dalı ölçüyor). Mutasyon kaynağı bozar, depodaki dosya DEĞİŞMEZ."""
    ham = KOY_SH.read_text(encoding="utf-8")
    capa = 'if [ -n "$AYRISAN" ]; then'
    assert capa in ham, f"mutasyon çapası kaynakta yok (çivi bayatlamış): {capa!r}"
    bozuk = tmp_path / "vault_sir_koy_bozuk.sh"
    bozuk.write_text(ham.replace(capa, "if false; then", 1), encoding="utf-8")
    binler, _, kasa = _sahte_vault(tmp_path)
    sahne = _dalga2_sahne(tmp_path, kopya_degeri="SAHTE-ESKI-KALMIS-ANAHTAR")
    r = subprocess.run(["bash", str(bozuk), "--uygula"], capture_output=True, text=True,
                       env=_koy_ortam(tmp_path, binler, sahne))
    assert r.returncode == 0 and (kasa / "secret_meridian_sahte_anahtar").exists(), (
        f"MUTASYON ISIRMADI: kapı silinince de durdu — D5 başka bir dalı ölçüyor olabilir:"
        f"\n{r.stdout}\n{r.stderr}")


def test_D8_DALGA1_girdisi_KAYNAKSIZ_calismaya_DEVAM_eder(tmp_path):
    """GERİYE UYUMLULUK POZİTİF KONTROLÜ: `kaynak` taşımayan (dalga-1) bir girdide kaynak hedefin
    KENDİSİDİR. Dalga-2 sözleşmesi eklenirken bu dalın sessizce kopması, yedi dalga-1 sırrının
    taşınamaması demekti — ve arıza ancak bakım penceresinde görünürdü."""
    import sys as _sys
    binler, _, kasa = _sahte_vault(tmp_path)
    kaynak = tmp_path / "kaynaklar"
    kaynak.mkdir(exist_ok=True)
    hedef = kaynak / "dash_token"
    hedef.write_text(SAHTE_DEGER_D + "\n", encoding="utf-8")
    env = tmp_path / "envanter_dalga1.yaml"
    env.write_text(yaml.safe_dump({"vault_kv": [{
        "ad": "dash_token", "vault_yolu": "secret/meridian/dash_token",
        "hedef": str(hedef), "mod": "0400", "sahip": "root", "tuketici": "test"}]}),
        encoding="utf-8")
    r = subprocess.run(["bash", str(KOY_SH), "--uygula"], capture_output=True, text=True,
                       env=_koy_ortam(tmp_path, binler, env))
    assert r.returncode == 0, f"dalga-1 yolu düştü:\n{r.stdout}\n{r.stderr}"
    assert (kasa / "secret_meridian_dash_token").read_text(encoding="utf-8") == SAHTE_DEGER_D
    assert _sys.executable  # PYTHON_BIN gerçekten kullanıldı (ortam kurulumunun pozitif kontrolü)


# =================================================================================================
# E) `deploy/oracle-a1/sir_rotasyon.sh --vault` — rotasyon KASADAN başlar (Task 4)
# =================================================================================================
# BUGÜNKÜ ROTASYON dosyaları TEK TEK yazar ve "unutulan kopya" sınıfı tam olarak buradan doğar.
# `--vault` kipi sırayı TERSİNE çevirir: değer ÖNCE kasaya konur, Agent onu bütün yan dosyalara
# render eder, rotasyon yalnız render'ı ÖLÇER ve tüketicileri yeniden başlatır. Eski kanal
# kopyaları iki-kanal dönemi boyunca AYNI pencerede kasadan gelen değerle eşitlenir.
#
# ŞİMLER: gerçek bir kasa YOKTUR. `vault` şimi `kv put`u bir dosyaya yazar ve — istenirse —
# Agent'ın yapacağı işi (kanonik dosyayı render etmek) taklit eder. Ölçülen şey betiğin KENDİ
# davranışıdır: hangi sırayla ne yapıyor, değer nereye giriyor, render gelmezse ne diyor.

from tests.test_sir_rotasyon_v447 import ESKI, _kos, _sahte_ortam  # noqa: E402

YENI_VAULT_DEGERI = "SAHTE-YENI-KASA-ANAHTARI-2026"

#: `--openrouter --vault` ARTIK BİRİNCİL YOLA YAZAR (Rol-1 hükmü, tur-2): `openrouter_api_key` bir
#: TAKMA ADdır ve kasadaki yol `HINDSIGHT_API_LLM_API_KEY`inkidir. Render kanıtı da birincilin
#: `hedef`idir — takma adın kendi kanonik kopyası YOKTUR (ikinci bir dosya, sırrın diskteki
#: yüzeyini gereksizce büyütürdü). İki sabit ELLE durur ve tablo ile ölçülür: envanterden
#: türetilseydi, eşleme envanterde bozulduğunda bu sahne de onunla birlikte bozulur ve "hâlâ
#: doğru yola yazıyoruz" derdi.
BIRINCIL_OR = TAKMA_ADLAR["openrouter_api_key"]
KASA_YOLU_OR = f"secret/meridian/{BIRINCIL_OR}"
KANONIK_HEDEF = "/etc/hindsight/creds/HINDSIGHT_API_LLM_API_KEY"


def _vault_sim(tmp_path: pathlib.Path, kok: pathlib.Path, render: bool = True) -> pathlib.Path:
    """PATH'e konacak sahte `vault`. `render=True` ise `kv put`tan sonra Agent'ın yapacağı işi
    (kanonik tek-değer dosyasını yazmak) TAKLİT eder; `False` ise HİÇBİR ŞEY render edilmez ve
    betiğin bekleme tavanı ölçülebilir hâle gelir."""
    binn = tmp_path / "bin"
    binn.mkdir(exist_ok=True)
    log = tmp_path / "vault_argv.log"
    kasa = tmp_path / "kasa"
    kasa.mkdir(exist_ok=True)
    hedef = kok / KANONIK_HEDEF.lstrip("/")
    render_satiri = f'  cp "{kasa}/deger" "{hedef}"\n' if render else "  :\n"
    (binn / "vault").write_text(
        "#!/usr/bin/env bash\n"
        f'echo "$*" >> "{log}"\n'
        'if [ "$1" = "login" ]; then cat > /dev/null; exit 0; fi\n'
        'if [ "$1" = "kv" ] && [ "$2" = "put" ]; then\n'
        f'  cat > "{kasa}/deger"\n'
        f"{render_satiri}"
        "  exit 0\n"
        "fi\n"
        f'if [ "$1" = "kv" ] && [ "$2" = "get" ]; then cat "{kasa}/deger"; exit 0; fi\n'
        "exit 0\n")
    (binn / "vault").chmod(0o755)
    return log


def _vault_ortam(tmp_path: pathlib.Path, ortam: dict, kok: pathlib.Path,
                 render: bool = True) -> tuple[dict, pathlib.Path]:
    log = _vault_sim(tmp_path, kok, render=render)
    jeton = kok / "etc/vault/admin.token"
    jeton.parent.mkdir(parents=True, exist_ok=True)
    jeton.write_text("SAHTE-hvs-yonetici\n", encoding="utf-8")
    # Kanonik hedef BAŞLANGIÇTA ESKİ değerdedir: render'ın GERÇEKTEN olduğunu ölçmenin tek yolu
    # "önce eski, sonra yeni" farkıdır. Dosya hiç yoksa "render oldu" ile "dosya doğdu" karışırdı.
    kanonik = kok / KANONIK_HEDEF.lstrip("/")
    kanonik.parent.mkdir(parents=True, exist_ok=True)
    kanonik.write_text(ESKI["or"] + "\n", encoding="utf-8")
    import sys as _sys
    # `VAULT_ENVANTER` AÇIKÇA verilir: mutasyon kopyası tmp'de doğar ve kendi `../` yolundan
    # envanteri BULAMAZDI (çivi o zaman "envanter yok" diye kırılır, ölçmek istediği dalı hiç
    # görmezdi). `PYTHON_BIN` sanal ortamın yorumlayıcısıdır — sistem python3'ünde PyYAML
    # olmayabilir ve o eksik, ölçülmek istenen davranışla ilgisiz bir kırmızı üretirdi.
    yeni = dict(ortam, VAULT_BIN=str(tmp_path / "bin" / "vault"),
                VAULT_TOKEN_FILE=str(jeton),
                VAULT_ENVANTER=str(ENVANTER), PYTHON_BIN=_sys.executable,
                VAULT_RENDER_TAVAN_S="1", VAULT_RENDER_ARALIK_S="0.05")
    return yeni, log


def test_E1_vault_kipi_SOZLESMESI_kaynakta():
    """Kaynak metni çivisi: kip TANINIYOR, bekleme SINIRLI ve tavan ADIYLA bir sabitte, restart
    listesi ENVANTERDEN geliyor, eski `--esitle` KALIYOR (dalga-2 onu emekli etmez: iki-kanal
    dönemi boyunca eski kanalın onarım yolu odur)."""
    metin = _yorumsuz(ROTASYON_SH.read_text(encoding="utf-8"))
    assert "--vault" in metin, "`--vault` kipi betikte yok"
    assert "VAULT_RENDER_TAVAN_S" in metin, "render bekleme TAVANI adıyla bir sabitte değil"
    assert "vault_dosyalar" in metin and "yeniden_baslat" in metin, (
        "restart listesi envanterin `vault_dosyalar` bloğundan TÜREMİYOR")
    assert "--esitle" in metin, "`--esitle` kipi düşürülmüş (iki-kanal döneminin onarım yolu)"
    assert not re.search(r"^\s*set\s+-[a-z]*x", metin, re.M), "set -x açık"
    assert "$(cat" not in metin and "$(<" not in metin, "komut ikamesiyle dosya okunuyor"


def test_E2_vault_KURU_kosumu_HICBIR_KOMUT_cagirmaz(tmp_path):
    """Kuru koşumun tek iddiası: HİÇBİR ŞEY YAPMAM. Kasaya `kv put` de, tüketiciye `restart` de
    yok; buna karşılık PLAN basılır — hangi kasa yolu, hangi yan dosyalar, hangi birimler ve
    ne kadar bekleme."""
    kok, ortam = _sahte_ortam(tmp_path)
    ortam, log = _vault_ortam(tmp_path, ortam, kok)
    r = _kos(ROTASYON_SH, ortam, "--vault", "--openrouter", "--kuru")
    assert r.returncode == 0, f"kuru koşum düştü:\n{r.stdout}\n{r.stderr}"
    assert not log.exists(), f"kuru koşum kasaya çağrı yaptı:\n{log.read_text()}"
    assert not (kok / ".sahte/systemctl.log").read_text().strip(), (
        "kuru koşum birim yeniden başlattı")
    assert KASA_YOLU_OR in r.stdout, "kasa yolu basılmıyor"
    assert BIRINCIL_OR in r.stdout, "takma adın BİRİNCİLİ kuru koşumda ADIYLA basılmıyor"
    assert "/opt/apisix/.env-apisix.vault" in r.stdout, "yan dosya listesi basılmıyor"
    assert "apisix.service" in r.stdout, "yeniden başlatılacak birim basılmıyor"
    assert "90" in r.stdout or "tavan" in r.stdout.lower(), "bekleme tavanı basılmıyor"


def test_E3_vault_UYGULA_kasaya_KOYAR_render_OLCER_ESKI_KANALI_esitler(tmp_path):
    """Mutlu yol, adım adım: (1) değer kasaya BORUYLA gider ve argv'de GÖRÜNMEZ; (2) kanonik
    dosyanın render edildiği ÖLÇÜLÜR; (3) eski kanal kopyaları KASADAN gelen değerle yazılır
    (iki-kanal dönemi); (4) tüketiciler yeniden başlar."""
    kok, ortam = _sahte_ortam(tmp_path)
    ortam, log = _vault_ortam(tmp_path, ortam, kok)
    r = _kos(ROTASYON_SH, ortam, "--vault", "--openrouter", girdi=f"{YENI_VAULT_DEGERI}\n")
    assert r.returncode == 0, f"uygula düştü:\n{r.stdout}\n{r.stderr}"
    argv = log.read_text(encoding="utf-8")
    assert f"kv put {KASA_YOLU_OR}" in argv, f"kasaya yazılmadı (BİRİNCİL yol):\n{argv}"
    assert "kv put secret/meridian/openrouter_api_key" not in argv, (
        f"TAKMA ADIN KENDİ yoluna yazıldı — hüküm 'aynı değer, TEK kasa yolu':\n{argv}")
    assert YENI_VAULT_DEGERI not in argv, "DEĞER ARGV'ye girdi (ps ile herkese görünür)"
    assert YENI_VAULT_DEGERI not in r.stdout, "değer terminale basıldı"
    # Eski kanal: on üç kopyadan üçü örneklenir (hepsi `_yaz` ile aynı yoldan yazılır).
    for yol, alan in (("opt/apisix/.env-apisix", "OPENROUTER_API_KEY"),
                      ("opt/hindsight/.env", "HINDSIGHT_API_REFLECT_LLM_1_API_KEY"),
                      ("home/ubuntu/.hermes/.env", "OPENROUTER_API_KEY")):
        icerik = (kok / yol).read_text(encoding="utf-8")
        assert f"{alan}=" in icerik and YENI_VAULT_DEGERI in icerik, (
            f"eski kanal kopyası kasadan gelen değerle eşitlenmedi: {yol} [{alan}]")
    log_birimler = (kok / ".sahte/systemctl.log").read_text(encoding="utf-8")
    assert "apisix.service" in log_birimler, "kapı yeniden başlatılmadı"


def test_E4_RENDER_GELMEZSE_TAVANDA_durur_ve_ESKI_KANAL_YAZILMAZ(tmp_path):
    """Agent render etmiyorsa (kasa mühürlü · politika eksik · birim düşmüş) rotasyon DEVAM
    EDEMEZ: eski kanalı kasadan gelmeyen bir değerle yazmak, kasayı kaynak sanıp ESKİ değeri
    yaymak olurdu. Bekleme SINIRLIDIR ve aşımda hüküm "ölçülemedi"dir (çıkış 2), "başarısız"
    değil — ikisi bu betikte AYRI hükümlerdir."""
    kok, ortam = _sahte_ortam(tmp_path)
    ortam, _ = _vault_ortam(tmp_path, ortam, kok, render=False)
    onceki = (kok / "opt/apisix/.env-apisix").read_text(encoding="utf-8")
    r = _kos(ROTASYON_SH, ortam, "--vault", "--openrouter", girdi=f"{YENI_VAULT_DEGERI}\n")
    assert r.returncode == 2, f"render gelmeyince çıkış {r.returncode} (2 bekleniyordu):\n{r.stdout}\n{r.stderr}"
    assert (kok / "opt/apisix/.env-apisix").read_text(encoding="utf-8") == onceki, (
        "render ölçülemezken eski kanal YAZILDI — kasa kaynak sanılıp eski değer yayılırdı")
    assert YENI_VAULT_DEGERI not in r.stdout + r.stderr, "değer çıktıya sızdı"


def test_E5_MUTASYON_render_olcumu_kaldirilirsa_E4_KIRMIZI(tmp_path):
    """Çivi yeşili kanıt değildir: render karşılaştırması kaldırılırsa betik HİÇBİR ŞEY render
    edilmemişken de ilerlemeli (yani E4 gerçekten o dalı ölçüyor)."""
    ham = ROTASYON_SH.read_text(encoding="utf-8")
    capa = 'if sudo cmp -s "$ISLIK/vault_yeni_kanon" "$ISLIK/vault_render_kanon"; then'
    assert capa in ham, f"mutasyon çapası kaynakta yok (çivi bayatlamış): {capa!r}"
    bozuk = tmp_path / "sir_rotasyon_bozuk.sh"
    bozuk.write_text(ham.replace(capa, "if true; then", 1), encoding="utf-8")
    bozuk.chmod(0o755)
    kok, ortam = _sahte_ortam(tmp_path)
    ortam, _ = _vault_ortam(tmp_path, ortam, kok, render=False)
    r = _kos(bozuk, ortam, "--vault", "--openrouter", girdi=f"{YENI_VAULT_DEGERI}\n")
    assert r.returncode != 2, (
        f"MUTASYON ISIRMADI: ölçüm kaldırılınca da 'ölçülemedi' dedi — E4 başka bir dalı "
        f"ölçüyor olabilir:\n{r.stdout}\n{r.stderr}")


def test_E6_vault_YALNIZ_rotasyon_alt_komutlariyla(tmp_path):
    """`--vault --envanter` ne ölçer ne yazar. Sessiz kabul, olmayan bir sözleşmeyi var gibi
    gösterir (`--esitle`nin aynı kapısıyla tek hüküm)."""
    kok, ortam = _sahte_ortam(tmp_path)
    ortam, _ = _vault_ortam(tmp_path, ortam, kok)
    r = _kos(ROTASYON_SH, ortam, "--vault", "--envanter")
    assert r.returncode != 0, f"`--vault --envanter` kabul edildi:\n{r.stdout}"
    assert "--vault" in r.stderr, f"ret gerekçesi kipi ADIYLA söylemiyor:\n{r.stderr}"


def test_E7_vault_KAPSAM_BEYANI_kasaya_bagli_OLMAYAN_sirri_soyler(tmp_path):
    """BEDEL YASASI. `--openrouter` İKİ anahtar döndürür (NOUS + OPENROUTER) ama kasaya bağlı
    olan YALNIZ biridir. Kuru koşum bunu ADIYLA söylemeli: söylemezse operatör "OpenRouter
    rotasyonu bitti" sanır ve motorun NOUS anahtarı sessizce eski değerde kalır."""
    kok, ortam = _sahte_ortam(tmp_path)
    ortam, _ = _vault_ortam(tmp_path, ortam, kok)
    r = _kos(ROTASYON_SH, ortam, "--vault", "--openrouter", "--kuru")
    assert "NOUS_API_KEY" in r.stdout, f"kasa kapsamı dışındaki sır beyan edilmiyor:\n{r.stdout}"


# =================================================================================================
# T) TAKMA AD (`ayni_deger`) — AYNI DEĞERİN TEK KASA YOLU (Rol-1 hükmü 2026-09-14, tur-2)
# =================================================================================================
# TUR-1'İN AÇIK KALEMİ: `openrouter_api_key` ile `HINDSIGHT_API_LLM_API_KEY`, `bot_key_meridian`
# ile `kapi_apikey`, `hindsight_cp_dataplane_api_key` ile `HINDSIGHT_API_TENANT_API_KEY` BUGÜN
# aynı değeri taşıyor ama kasada AYRI yollardı. Ayrışma taşıma anında ölçülüyordu; ROTASYONDAN
# SONRA ayrışma (biri döner, öteki dönmez) ölçülemiyordu — ve tam olarak o hâl, bu deponun en
# pahalı sınıfının (aynı gerçeğin iki kopyası) kasa içindeki biçimidir.
#
# HÜKÜM: aynı değerin TEK kasa yolu vardır ve o yol BİRİNCİLİNDİR — kasada ZATEN duran dalga-1
# girdisi. Dalga-2 adı bir TAKMA ADdır: kendi yolu, hedefi, modu, sahibi YOKTUR. Bu bölüm hükmün
# DÖRT yerde birlikte uygulandığını ölçer (envanter · üretici · sir_koy · rotasyon); biri eksik
# kalırsa hüküm yarım kalır ve yarım kalışı SESSİZDİR.

def test_T1_TAKMA_AD_tablosu_envanterle_BIREBIR():
    """Tablo ELLE durur, envanterden TÜREMEZ (DALGA2_ADLARI ile aynı gerekçe). İki yönlü ölçüm:
    beklenen her eşleme envanterde VAR, ve envanterde beklenmeyen bir takma ad YOK. İkinci yön
    olmasaydı yarın sessizce eklenen bir takma ad hiçbir kapıdan geçmeden kasaya girerdi."""
    gercek = {g["ad"]: g[TAKMA_AD_ALANI] for g in _vault_kv() if TAKMA_AD_ALANI in g}
    assert gercek == TAKMA_ADLAR, (
        f"takma ad tablosu envanterle AYRIŞTI.\n  envanterde fazla: "
        f"{sorted(set(gercek) - set(TAKMA_ADLAR))}\n  tabloda fazla: "
        f"{sorted(set(TAKMA_ADLAR) - set(gercek))}")


def test_T2_TAKMA_AD_KENDI_yolunu_TASIMAZ_ve_BIRINCIL_DALGA1_dir():
    """Üç iddia, üçü de hükmün bir yüzü:
    (a) takma ad `vault_yolu`/`hedef`/`mod`/`sahip` TAŞIMAZ — taşısaydı `ayni_deger` bir süs olur
        ve kasada ikinci yol yine açılırdı;
    (b) birincil kendisi bir takma ad DEĞİLDİR (zincir yok) — zincir, "tek yol" iddiasını bir
        dolambaçla yine ikiye bölerdi;
    (c) birincil DALGA-1 girdisidir, yani değer kasada O YOLDA zaten duruyor: hükmün bütün
        pratik kazancı A1'de bir GÖÇ gerekmemesidir."""
    ind = {g["ad"]: g for g in _vault_kv()}
    from tests.test_vault_faz2_v485 import DALGA1_ADLARI
    for takma, birincil in TAKMA_ADLAR.items():
        g = ind[takma]
        yasak = {"vault_yolu", "hedef", "mod", "sahip"} & set(g)
        assert not yasak, f"{takma}: takma ad KENDİ {sorted(yasak)} alanını taşıyor"
        assert birincil in ind, f"{takma}: `ayni_deger` {birincil!r} envanterde YOK (dangling)"
        assert TAKMA_AD_ALANI not in ind[birincil], (
            f"{takma} → {birincil}: birincil de bir takma ad (ZİNCİR) — birincil TEK olmalı")
        assert birincil in DALGA1_ADLARI, (
            f"{takma} → {birincil}: birincil dalga-1 girdisi DEĞİL — kasada yeni yol açılır ve "
            "A1'de göç gerekirdi (hükmün reddettiği yön)")
        assert "TAKMA AD" in g["tuketici"], (
            f"{takma}: tüketici beyanı takma ad olduğunu SÖYLEMİYOR: {g['tuketici']!r}")


def test_T3_URETICI_takma_adi_BIRINCILIN_yoluna_cozer():
    """Yan dosya satırı bir takma ada bakıyorsa şablon BİRİNCİLİN kasa yolunu okur. Çözülmeseydi
    Agent kasada OLMAYAN bir yolu okur (403/404) ve o alan yan dosyada HİÇ doğmazdı."""
    metin = AGENT_HCL.read_text(encoding="utf-8")
    olculen = 0
    for d in _vault_dosyalar():
        blok = [b for b in _sablon_bloklari(metin) if f'destination = "{d["yol"]}"' in b][0]
        for s in d["satirlar"]:
            if s["sir"] not in TAKMA_ADLAR:
                continue
            olculen += 1
            beklenen = f'secret/data/meridian/{TAKMA_ADLAR[s["sir"]]}'
            assert re.search(
                rf'^{re.escape(s["alan"])}=(?:Bearer )?\{{\{{ with secret "{re.escape(beklenen)}"',
                blok, re.M), (
                f"{d['yol']}: `{s['alan']}` takma adın KENDİ yolunu okuyor "
                f"(beklenen birincil yol: {beklenen})")
    assert olculen >= 3, f"pozitif kontrol: takma ad taşıyan yan dosya satırı ölçülemedi ({olculen})"


def test_T4_POLITIKADA_yol_TEKRARI_YOK_ve_takma_adin_KENDI_yolu_YOK():
    """HCL'de aynı `path` iki kez yazılamaz (ikincisi birinciyi gölgeler) ve daha önemlisi: iki
    kez yazılmış bir yol, politikayı okuyan mühendise iki AYRI sır varmış gibi görünür. Aynı
    ölçüm agent yapılandırmasının hedeflerinde de yapılır — takma adın kanonik tek-değer kopyası
    HİÇ doğmamalı (ikinci bir dosya, sırrın diskteki yüzeyini bir dosya daha büyütürdü)."""
    politika = POLITIKA_AGENT.read_text(encoding="utf-8")
    yollar = re.findall(r'^path\s+"([^"]+)"', politika, re.M)
    assert len(yollar) == len(set(yollar)), (
        f"politikada YOL TEKRARI: {sorted({y for y in yollar if yollar.count(y) > 1})}")
    hcl = AGENT_HCL.read_text(encoding="utf-8")
    hedefler = re.findall(r'^\s*destination\s*=\s*"([^"]+)"', hcl, re.M)
    assert len(hedefler) == len(set(hedefler)), "agent şablonlarında HEDEF TEKRARI"
    for takma in TAKMA_ADLAR:
        assert f'secret/data/meridian/{takma}' not in yollar, (
            f"{takma}: takma ad için KENDİ politika yolu üretilmiş — kasada ikinci yol")
        assert f"/etc/meridian/{takma}" not in hedefler, (
            f"{takma}: takma ad için KENDİ kanonik kopyası render ediliyor")


def _mutant_envanter(tmp_path: pathlib.Path, eski: str, yeni: str, ad: str) -> pathlib.Path:
    metin = ENVANTER.read_text(encoding="utf-8")
    assert eski in metin, f"mutasyon hedefi envanterde yok (çivi bayatlamış): {eski!r}"
    bozuk = tmp_path / f"{ad}.yaml"
    bozuk.write_text(metin.replace(eski, yeni, 1), encoding="utf-8")
    return bozuk


@pytest.mark.parametrize("etiket,eski,yeni,beklenen", [
    ("dangling", "    ayni_deger: kapi_apikey", "    ayni_deger: OLMAYAN_BIRINCIL",
     "dangling"),
    ("zincir", "    ayni_deger: kapi_apikey", "    ayni_deger: bot_key_bekci", "ZİNCİR"),
    ("kendi_yolu", "  - ad: bot_key_meridian\n    ayni_deger: kapi_apikey",
     '  - ad: bot_key_meridian\n    ayni_deger: kapi_apikey\n'
     '    vault_yolu: "secret/meridian/bot_key_meridian"',
     "vault_yolu"),
])
def test_T5_MUTASYON_BOZUK_takma_ad_URETICIYI_DURDURUR(tmp_path, etiket, eski, yeni, beklenen):
    """Üç bozuk hâl, üç ayrı sessiz arıza — üçü de PATLAMALI:
      · dangling  → şablon kasada OLMAYAN bir yolu okur, dosya hiç doğmaz (403/404)
      · ZİNCİR    → takma adın takma adı; "tek yol" iddiası bir dolambaçla yine ikiye böler
      · kendi yolu→ hükmün tam tersi: kasada ikinci yol açılır ve rotasyondan sonra ayrışır
    Fail-closed olmasaydı üretici "GÜNCEL" der, bayat kapı yeşil kalır ve geçiş yarım yapılırdı.

    NOT (zincir sahnesi): zincir tek bir satırla kurulamaz — `bot_key_meridian`in birincilini
    `bot_key_bekci` yapmak yetmez, `bot_key_bekci`nin KENDİSİNİN de bir takma ad olması gerekir.
    İkinci mutasyon onun yol/hedef/mod/sahip satırlarını `ayni_deger` ile değiştirir; yoksa çivi
    zinciri değil "takma ad kendi yolunu taşıyor" dalını ölçerdi (ilk denemede tam bu oldu)."""
    bozuk = _mutant_envanter(tmp_path, eski, yeni, f"env_{etiket}")
    if etiket == "zincir":
        # `bot_key_bekci`yi de bir takma ada çevir → `bot_key_meridian → bot_key_bekci → …`
        metin = bozuk.read_text(encoding="utf-8")
        capa = ('  - ad: bot_key_bekci\n'
                '    vault_yolu: "secret/meridian/bot_key_bekci"\n'
                '    hedef: "/etc/meridian/bot_key_bekci"\n'
                '    mod: "0400"\n'
                '    sahip: "root"\n')
        assert capa in metin, "zincir sahnesi kurulamadı (çapa bayatlamış)"
        bozuk.write_text(
            metin.replace(capa, '  - ad: bot_key_bekci\n    ayni_deger: kapi_apikey\n', 1),
            encoding="utf-8")
    mod = _mutant_uretici(tmp_path, 'MONTAJ = "secret"', 'MONTAJ = "secret"',
                          f"uret_mut_{etiket}", envanter=bozuk)
    with pytest.raises(SystemExit) as hata:
        mod.agent_yapilandirmasi()
    assert beklenen in str(hata.value), f"{etiket}: beklenen gerekçe basılmadı: {hata.value}"


# -------------------------------------------------------------------------------------------------
# T6-T8 — `vault_sir_koy.sh`: takma ad için `kv put` YOK, EŞİTLİK KAPISI VAR
# -------------------------------------------------------------------------------------------------
# Taşıma anında sorulan soru değişti: "bu değeri kasaya koy" değil, "bu takma adın kaynağı ile
# kasadaki BİRİNCİL değer BUGÜN gerçekten aynı mı". Ayrıştıkları gün takma adın tüketicisi (yan
# dosya alanı) kasadan BAŞKA bir değer alır ve arıza 401 olarak, kasadan çok uzakta görünür.

SAHTE_BIRINCIL_D = "SAHTE-BIRINCIL-DEGERI-0002"


def _takma_ad_sahne(tmp_path: pathlib.Path, takma_degeri: str | None = None) -> pathlib.Path:
    """İki girdili KÜÇÜK envanter: bir BİRİNCİL (kendi yolu var) + bir TAKMA AD (yolu yok).

    `takma_degeri` verilirse takma adın kaynağı bilerek AYRI yazılır — "aynı sanılan iki değer
    gerçekten aynı mı" sorusunun kırmızı hâli."""
    kaynak = tmp_path / "ta_kaynaklar"
    kaynak.mkdir(exist_ok=True)
    birincil_dosya = kaynak / "birincil"
    birincil_dosya.write_text(SAHTE_BIRINCIL_D + "\n", encoding="utf-8")
    takma_dosya = kaynak / "env-takma"
    takma_dosya.write_text(
        f"BIR_ALAN={takma_degeri or SAHTE_BIRINCIL_D}\n", encoding="utf-8")
    env = tmp_path / "envanter_takma.yaml"
    env.write_text(yaml.safe_dump({"vault_kv": [
        {"ad": "sahte_birincil", "vault_yolu": "secret/meridian/sahte_birincil",
         "hedef": str(birincil_dosya), "mod": "0400", "sahip": "root",
         "tuketici": "çivi sahnesi (birincil)"},
        {"ad": "sahte_takma", "ayni_deger": "sahte_birincil",
         "tuketici": "çivi sahnesi — TAKMA AD",
         "rotasyon_siri": None,
         "kaynak": {"tur": "env_satiri", "dosya": str(takma_dosya),
                    "alan": "BIR_ALAN", "onek": None}},
    ]}, allow_unicode=True), encoding="utf-8")
    return env


def test_T6_koy_TAKMA_AD_icin_KV_PUT_YAPMAZ_ve_ESITLIGI_olcer(tmp_path):
    """Mutlu yol: birincil kasaya KONUR, takma ad için `kv put` ÇAĞRILMAZ ve eşitlik ÖLÇÜLÜR.
    İkinci bir `put`, kasada ikinci bir yol açardı — hükmün engellediği tam olarak budur."""
    binler, argv_log, kasa = _sahte_vault(tmp_path)
    r = subprocess.run(["bash", str(KOY_SH), "--uygula"], capture_output=True, text=True,
                       env=_koy_ortam(tmp_path, binler, _takma_ad_sahne(tmp_path)))
    assert r.returncode == 0, f"uygula düştü:\n{r.stdout}\n{r.stderr}"
    argv = argv_log.read_text(encoding="utf-8")
    assert "kv put secret/meridian/sahte_birincil" in argv, f"birincil kasaya konmadı:\n{argv}"
    assert "kv put secret/meridian/sahte_takma" not in argv, (
        f"TAKMA AD için `kv put` çağrıldı — kasada ikinci yol açıldı:\n{argv}")
    assert not (kasa / "secret_meridian_sahte_takma").exists(), "takma ad kasada kendi yolunu aldı"
    assert "TAKMA AD" in r.stdout and "EŞİT" in r.stdout, (
        f"eşitlik ölçümü basılmıyor:\n{r.stdout}")
    assert SAHTE_BIRINCIL_D not in r.stdout, "değer terminale basıldı"


def test_T7_koy_TAKMA_AD_AYRISIRSA_DURUR_ve_IKI_ADI_da_soyler(tmp_path):
    """Ayrışma bir tahmin işi DEĞİLDİR: hangisinin doğru olduğu buradan bilinemez ve birincili
    takma adın değeriyle EZMEK, tahmini kasadan bütün tüketicilere yaymak olurdu. Betik DURUR ve
    iki adı da basar — hangi çiftin ayrıştığı çıktıdan okunabilmeli."""
    binler, argv_log, kasa = _sahte_vault(tmp_path)
    sahne = _takma_ad_sahne(tmp_path, takma_degeri="SAHTE-AYRISMIS-TAKMA-DEGER")
    r = subprocess.run(["bash", str(KOY_SH), "--uygula"], capture_output=True, text=True,
                       env=_koy_ortam(tmp_path, binler, sahne))
    assert r.returncode != 0, f"takma ad ayrışmasında taşıma DURMADI:\n{r.stdout}"
    assert "sahte_takma" in r.stdout and "sahte_birincil" in r.stdout, (
        f"ayrışan çift ADIYLA basılmıyor:\n{r.stdout}")
    kasada = (kasa / "secret_meridian_sahte_birincil").read_text(encoding="utf-8")
    assert kasada == SAHTE_BIRINCIL_D, (
        "BİRİNCİL takma adın ayrık değeriyle EZİLDİ — tahmin bütün tüketicilere yayılırdı")


def test_T8_MUTASYON_takma_ad_dali_silinirse_T6_ve_T7_KIRMIZI(tmp_path):
    """Çivi yeşili kanıt değildir: dal kaldırıldığında takma ad BİRİNCİLİN yoluna `kv put` yapar
    ve ayrışan değer birincili SESSİZCE EZER (çıkış 0). Yani T6/T7 gerçekten o dalı ölçüyor."""
    ham = KOY_SH.read_text(encoding="utf-8")
    capa = ('  if [ "$birincil" != "-" ]; then\n'
            '    kasa_sha="$("$VAULT_BIN" kv get -field=value "$yol"')
    assert capa in ham, f"mutasyon çapası kaynakta yok (çivi bayatlamış): {capa!r}"
    bozuk = tmp_path / "vault_sir_koy_takma_bozuk.sh"
    bozuk.write_text(ham.replace(
        capa, '  if false; then\n    kasa_sha="$("$VAULT_BIN" kv get -field=value "$yol"', 1),
        encoding="utf-8")
    binler, argv_log, kasa = _sahte_vault(tmp_path)
    sahne = _takma_ad_sahne(tmp_path, takma_degeri="SAHTE-AYRISMIS-TAKMA-DEGER")
    r = subprocess.run(["bash", str(bozuk), "--uygula"], capture_output=True, text=True,
                       env=_koy_ortam(tmp_path, binler, sahne))
    kasada = (kasa / "secret_meridian_sahte_birincil").read_text(encoding="utf-8")
    assert r.returncode == 0 and kasada == "SAHTE-AYRISMIS-TAKMA-DEGER", (
        f"MUTASYON ISIRMADI: dal silinince de durdu/ezmedi — T6/T7 başka bir dalı ölçüyor "
        f"olabilir:\n{r.stdout}\n{r.stderr}")


# -------------------------------------------------------------------------------------------------
# T9-T10 — `sir_rotasyon.sh --vault`: rotasyon BİRİNCİL yola, restart listesi TAKMA ADI DA KAPSAR
# -------------------------------------------------------------------------------------------------

def test_T9_rotasyon_KAPI_takma_adin_TUKETICISINI_de_yeniden_baslatir(tmp_path):
    """`--kapi --vault`: kasa yolu `secret/meridian/kapi_apikey`tir ve kapının yan dosyası o
    değeri TAKMA ADLA (`bot_key_meridian`) yazar. Restart listesi kasa YOLUNDAN toplandığı için
    `apisix.service` listeye girer. Ada göre toplansaydı yan dosya yeni değere döner, konteyner
    eski değeri ortamında tutar ve motor kapıdan 401 alırdı."""
    kok, ortam = _sahte_ortam(tmp_path)
    ortam, log = _vault_ortam(tmp_path, ortam, kok)
    r = _kos(ROTASYON_SH, ortam, "--vault", "--kapi", "--kuru")
    assert r.returncode == 0, f"kuru koşum düştü:\n{r.stdout}\n{r.stderr}"
    assert not log.exists(), "kuru koşum kasaya çağrı yaptı"
    assert "secret/meridian/kapi_apikey" in r.stdout, f"BİRİNCİL kasa yolu basılmıyor:\n{r.stdout}"
    assert "TAKMA AD" in r.stdout and "bot_key_meridian" in r.stdout, (
        f"takma ad ilişkisi kuru koşumda beyan edilmiyor:\n{r.stdout}")
    assert "/opt/apisix/.env-apisix.vault" in r.stdout, (
        f"takma adın yan dosyası listeye girmedi:\n{r.stdout}")
    assert "apisix.service" in r.stdout, (
        f"takma adın tüketicisi restart listesinde YOK:\n{r.stdout}")


def test_T10_MUTASYON_yan_dosya_sorgusu_ADA_donerse_T9_KIRMIZI(tmp_path):
    """Çivi yeşili kanıt değildir: sorgu kasa YOLU yerine ADA dönerse takma adın yan dosyası
    HİÇ bulunmaz ve restart listesi sessizce boşalır — yani T9 gerçekten o dalı ölçüyor."""
    ham = ROTASYON_SH.read_text(encoding="utf-8")
    capa = "    if any(coz(x[\"sir\"]) == hedef_yol for x in d[\"satirlar\"]):"
    assert capa in ham, f"mutasyon çapası kaynakta yok (çivi bayatlamış): {capa!r}"
    bozuk = tmp_path / "sir_rotasyon_takma_bozuk.sh"
    bozuk.write_text(ham.replace(
        capa, "    if any(x[\"sir\"] == hedef_yol for x in d[\"satirlar\"]):", 1), encoding="utf-8")
    bozuk.chmod(0o755)
    kok, ortam = _sahte_ortam(tmp_path)
    ortam, _ = _vault_ortam(tmp_path, ortam, kok)
    r = _kos(bozuk, ortam, "--vault", "--kapi", "--kuru")
    assert "/opt/apisix/.env-apisix.vault" not in r.stdout, (
        f"MUTASYON ISIRMADI: ada dönen sorgu da yan dosyayı buldu — T9 başka bir dalı ölçüyor "
        f"olabilir:\n{r.stdout}\n{r.stderr}")
