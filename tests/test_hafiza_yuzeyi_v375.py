"""v375 · HAFIZA YÜZEYİ — `/api/hindsight` (TSK-091 Görev 1): Hindsight'ın SALT-OKUNUR pano vekili.

NUMARA KAYDI (vNNN kimlik sınıfı): v374 (`test_session_refresh_gunluk_v374.py`) doluydu, sıradaki
boş numara v375 ölçüldü (`ls tests/ | grep -oE "v[0-9]+" | sort -t v -k2 -n | tail -1`). Çakışma
YOK.

NEDEN BU DOSYA VAR. Bu uç, panonun tarayıcısıyla Hindsight'ın kimlikli `/v1/*` yüzeyi arasındaki
TEK duvardır — v361'in APISIX için kurduğu duvarın kardeşi. Tarayıcı 8888'e ASLA gitmez: sunucu
okur, anahtarsız bir gövde döner. v361'in iki yalan sınıfı burada da aynen yaşar:

  (1) SIR SINIFI — `/v1/*` çağrıları `Authorization: Bearer <anahtar>` taşır ve anahtar
      `/opt/hindsight/.env` (0600) içinde yaşar. "Gövdeyi olduğu gibi döndüreyim" diyen bir gün,
      tenant anahtarını panonun HTML'ine indirir. Bu dosyanın en sert çivisi budur ve VAKUM
      DEĞİLDİR: anahtarın GERÇEKTEN gönderildiğini de ölçer — gönderilmemiş bir sırrın yanıtta
      olmaması hiçbir şey kanıtlamaz (v361'in ölçülmüş dersi).

  (2) UYDURMA SINIFI — `/opt/hindsight/.env` bu makinede YOKTUR ve olmaması ihlal değil ÖLÇÜM
      SONUCUDUR (v361 `KAPI_ENV_DOSYASI` emsali birebir). Yani "ölçemedim" bu ucun NORMAL hâlidir
      ve `neden` ile SÖYLENMEK zorundadır. Boş `bankalar: []` panoda "hiç banka yok" diye okunur —
      oysa bugün ölçülen iki banka var (`meridian-arsiv`, `smoke-067`). `None` ≠ `0` ≠ `[]`.

BU DOSYA NEYİ ÇİVİLER
---------------------
A. KAYIT + YETKİ — üç uç da rota tablosunda, üçü de `_auth` kapılı, üçü de YALNIZ GET.
B. ÖLÇÜLEMEZLİK YUTULMAZ — env yokken/upstream düşükken 200 + DOLU `neden` (pano kararmaz).
C. ZARF AYNEN GEÇER — `stats`/`llm_stats`/`audit_stats` upstream gövdesinin aynısıdır (süzme yok).
D. SIR DUVARI — anahtar yanıtın hiçbir yerinde yok, ama istekte gerçekten gönderilmiş; istisna
   metnindeki anahtar da maskelenir (ikinci hat, `_kapi_maskele`).
E. LİSTE TAVANI SUNUCUDA — `limit=9999` upstream'e ≤200 gider (istemciye güven yok).
F. EKSİK PARAMETRE 400 DEĞİL — `bank` verilmezse pano KARARMAZ: 200 + neden.
G. YOL ENJEKSİYONU — `bank`/`kimlik` upstream URL'inin PATH'ine giriyor; kaçırılmazsa
   `../../` ile başka uca gidilir. Alıntılama çivili.
H. ZAMAN AŞIMI — her dış çağrı zaman aşımlı; sabit `_kapi_getir`in zorladığıyla AYNI (ayrışma
   çivisi: iki kopya sessizce ayrışır — tek-kaynak yasası).
I. TEK-KAYNAK ÇIKARIMI — `_env_anahtari(dosya, onek)` iki çağıranı da besler; v361 sarmalayıcısı
   davranışını KORUR.
J. CP-UI GENİŞLEMESİ (TSK-108 Görev 1, 2026-09-02) — yüzey üç uçtan yirmi iki uca çıktı;
   A–I'nin HER sözleşmesi yeni uçlarda da PARAMETRİK olarak koşar (tek tek yazılan çivi,
   yirmi ikinci uçta unutulur). Ek olarak: sorgu-dizesi enjeksiyonu, enum süzme, ve `recall`
   POST'unun "sorgu sınıfı" beyanlı istisnası.
K. GÖREV 6-A EKLENTİSİ (TSK-108 Görev 6-A, 2026-09-02) — İKİ yeni uç: `bellek-graf`
   (`GET /v1/default/banks/{bank}/graph`, `get_graph`) ve `profil`
   (`GET /v1/default/banks/{bank}/profile`, `get_bank_profile` — openapi'de `deprecated: true`
   ama CP'nin hâlâ kullandığı TEK profil ucu). İkisi de `CPUI` tablosuna girdi, yani J'nin
   PARAMETRİK çivilerinin TAMAMINDAN geçerler; burada yalnız tabloya SIĞMAYAN üç şey ayrıca
   çivilendi: R7 varsayılan-limit önceliği (CP > openapi > gönderme), `type` geçişi, ve
   kapsam-dışı bırakılan `document_id`/`chunk_id`. Fixture'ların İKİSİ DE sınıf (1) — A1'de
   2026-09-02 18:15 UTC'de ölçüldü (`GRAF_CANLI_GOVDE`/`PROFIL_GOVDE`, aşağıda).

   ÜÇÜNCÜ UÇ ("ozellikler") YAZILMADI. Brief `features` ucunun YOLUNU ölçmeyi istedi; ölçüm
   sonucu: upstream'de BAĞIMSIZ bir `features` yolu YOKTUR — `features` yalnız `/version`
   gövdesinin (`VersionResponse.features` → `FeaturesInfo`) bir ALANIdIR, banka altında değil
   (CP'nin `features.observations` bayrağı tam olarak burayı okur). Uydurma yasağı: olmayan bir
   yola vekil yazılmadı; bulgu devir raporuna taşındı.

UPSTREAM ÇAPASI — ÖLÇÜM BUGÜN YENİDEN TÜRETİLEBİLİR OLMALI
----------------------------------------------------------
Bu dosyanın ve `meridian/api.py` HAFIZA bloğunun BÜTÜN upstream iddiaları tek bir kaynaktan
okundu ve o kaynak artık SHA ile çapalıdır (düzeltme turu 1, 2026-09-02). Önce yalnız `tag
v0.9.2` yazıyordu — tag OYNATILABİLİR bir işaretçidir, yani "hangi metni okudum" sorusu yarın
cevaplanamazdı (kart olsaydı §5'in blob kuralı bunu zorlardı):

  depo   : github.com/vectorize-io/hindsight (özel değil — `gh api` ile okunur)
  tag    : v0.9.2  →  ANNOTATED tag nesnesi 52dcd3f80e1e1999685c7f083e013b47ee8bc8a5
  commit : ebad478240d3171bb88201ececda5e8d9883d22d   ← ÖLÇÜMÜN ÇAPASI BUDUR
  dosya  : hindsight-clients/go/api/openapi.yaml (10.730 satır, dataplane sözleşmesi)

`scope` FİLTRESİ ÖLÇÜLDÜ VE YOKTUR (brief kalemi, düzeltme turu 1). Görev brief'i `/liste`ye
`fact_type`/`scope` filtreleri istiyordu. Upstream `list_memories`
(`GET /v1/default/banks/{bank_id}/memories/list`) parametrelerinin TAMAMI şudur — yol: `bank_id`;
sorgu: `type`, `q`, `consolidation_state`, `state`, `document_id`, `entity_id`, `tags`,
`tags_match`, `limit`, `offset`; başlık: `authorization`. **`scope` YOKTUR.** Bu yüzden `/liste`de
`scope` KARŞILIĞI DA YOKTUR — düşürüldü, ölçülerek (`test_liste_scope_upstreame_gitmez`).
`scope` upstream'de yalnız `list_llm_requests`te vardır ("Filter by call scope") ve `/llm-istekleri`
onu ZATEN geçiriyor; iki uç karıştırılırsa brief'teki kalem "eksik" sanılır.

KAYNAK SINIFLARI — FIXTURE'IN NEREDEN GELDİĞİ ETİKETLİDİR
---------------------------------------------------------
Bu dosyanın kurucu dersi "fixture = ölçülmüş gerçek gövde"dir (düzeltme turu 1: uydurulmuş
`version` alanı çivinin KENDİ VARSAYIMINI doğrulamasına yol açmıştı). Yüzey büyüdükçe tek bir
"gerçek" etiketi yetmez, çünkü üç AYRI epistemik sınıf var ve karıştırılırsa yalan söylerler:

  (1) ÖLÇÜLDÜ — A1'deki canlı Hindsight'tan 2026-09-02'de alınan gövde. Aşağıdaki
      `BANKALAR_GOVDE` / `VERSION_GOVDE` / `AUDIT_GOVDE` bu sınıftadır; Görev 6-A'nın
      `GRAF_CANLI_GOVDE` / `PROFIL_GOVDE`si (18:15 UTC ölçümü) de AYNI sınıftadır.
  (2) KAYNAKTAN TÜRETİLDİ — upstream deposunun KENDİ yayımladığı OpenAPI sözleşmesindeki
      `example:` blokları (yukarıdaki commit çapası). Bunlar benim analojim DEĞİL, upstream'in
      yazdığı örneklerdir: ALAN ADLARI gerçektir. DEĞERLER örnektir — canlıda görülmüş sayılar
      değildir ve öyleymiş gibi okunamaz. Tekrar eden ikinci/üçüncü öğeler kısaltılmıştır;
      aynen-geçiş çivisi öğe SAYISINA değil gövde EŞİTLİĞİNE baktığı için kısaltma ölçümü
      değiştirmez.
  (3) SENTETİK — ne ölçüldü ne kaynakta var. Yalnız vekilin DAVRANIŞINI (süzmeden geçiriyor mu)
      ölçmek için. Adında `SENTETIK` geçer ve upstream şeması olduğunu İDDİA ETMEZ.

Bu ayrımın bedeli vardır ve ödenir: sınıf (2) bir gövdenin canlıda gerçekten öyle geldiğini
KANITLAMAZ. Kanıtladığı şey, alan adlarının upstream sözleşmesinden okunduğu — yani vekilin
bir ada göre davranması gerektiği yerde (bkz. `_hafiza_surum`) o adın uydurulmadığıdır.

SINIF ETİKETİ BİR İDDİADIR VE YANLIŞ OLABİLİR (düzeltme turu 1). İnceleme üç gövdenin ilan
edilen sınıfında OLMADIĞINI ölçtü ve üçü de burada düzeltildi:
  · `*-istatistik` uçlarına upstream'in LİSTE örnekleri bağlanmıştı (analoji) — oysa
    `AuditLogStatsResponse`/`LLMRequestStatsResponse` şemalarının KENDİ `example:` blokları var;
    ikisi de okundu (`DENETIM_ISTATISTIK_ORNEK`/`LLM_ISTATISTIK_ORNEK`). Aynı upstream yolunun
    canlı ölçümüyle (`AUDIT_GOVDE`) AYRIŞMADIĞI ayrıca çivili — iki kayıt tek gerçeği anlatmalı.
  · Tarihçe gövdesi sınıf-2 başlığı altındaydı ama upstream'de örneği YOK: hem
    `memories/{id}/history` hem `mental-models/{id}/history` yanıt şeması literal `{}`tir
    (ölçüldü). Adı `TARIHCE_SENTETIK` oldu ve şema iddiası taşımadığı yanına yazıldı.
"""
from __future__ import annotations

import json
import pathlib

import pytest
from fastapi.testclient import TestClient

from meridian import api

# Testte kullanılan SAHTE tenant anahtarı. Gerçek bir anahtara benzemesi kasıtlı: sızıntı çivisi
# gövdede bu dizgeyi arar ve kısa/rastlantısal bir değer yanlış NEGATİF verirdi.
SAHTE_ANAHTAR = "sahte-hindsight-tenant-v375-Rq9Zt4Wm"
GEREKCE_ASGARI = 10          # "yok" bir gerekçe değildir

#: POST bacağının GERÇEK fonksiyonu, MODÜL DÜZEYİNDE yakalanır — yani autouse `_ag_kapali`
#: muhafızı onu bir tuzakla değiştirmeden ÖNCE. `_hafiza_post`u davranışıyla ölçen çiviler
#: (zaman aşımı, maskeleme) bunu kullanır; `api._hafiza_post` üzerinden çağırsalardı ölçtükleri
#: şey kod değil TUZAK olurdu — ve muhafız kaldırılsa bile yeşil kalırlardı.
GERCEK_HAFIZA_POST = api._hafiza_post
#: GET bacağının gerçek fonksiyonu, AYNI gerekçeyle (delegasyon çivisi onu çağırır — muhafızın
#: tuzağını çağırsaydı ölçtüğü şey yine kod değil tuzak olurdu).
GERCEK_KAPI_GETIR = api._kapi_getir


# --------------------------------------------------------------------------- yardımcılar

class _Casus:
    """`_kapi_getir` casusu: URL'e göre gövde döndürür, her çağrıyı saklar.

    EŞLEŞME EN UZUN PARÇAYA GİDER (sıraya değil): `/v1/default/banks` başka bir anahtarın
    (`/v1/default/banks/x/stats`) ÖN EKİdir; sıraya güvenen bir casus, testin ölçtüğünü sessizce
    değiştirir. Bilinmeyen URL'de `AssertionError` atmak KASITLI: uç yeni bir kaynağa gitmeye
    başlarsa çivi sessizce geçmez, patlar.

    Değer `bytes` ise başarı, `str` ise `_kapi_getir`in `(None, neden)` arızası demektir."""

    def __init__(self, esleme: dict[str, bytes | str]):
        self.esleme = esleme
        self.cagrilar: list[dict] = []

    def __call__(self, url, basliklar=None, sir=None):
        return self._cevap({"url": url, "basliklar": basliklar or {}, "sir": sir,
                            "fiil": "GET", "govde": None})

    def post(self, url, basliklar=None, sir=None, govde=None):
        """`_hafiza_post` casusu — GET bacağıyla AYNI eşleme tablosunu kullanır.

        AYRI BİR CASUS SINIFI YAZILMADI, bilerek: iki casus iki eşleme tablosu demek olurdu ve
        "hangi tabloyu kurdum" sorusu testin kendi varsayımını kaybettiği yerdir. GİDEN GÖVDE
        saklanır — `recall`ın süzülmüş-geçiş çivisi tam olarak onu okur."""
        return self._cevap({"url": url, "basliklar": basliklar or {}, "sir": sir,
                            "fiil": "POST", "govde": govde})

    def _cevap(self, kayit: dict):
        self.cagrilar.append(kayit)
        url = kayit["url"]
        adaylar = [p for p in self.esleme if p in url]
        if not adaylar:
            raise AssertionError(f"uç BEKLENMEYEN bir kaynağa gitti: {url}")
        govde = self.esleme[max(adaylar, key=len)]
        if isinstance(govde, str):
            return None, govde
        return govde, None

    def url_ler(self) -> list[str]:
        return [c["url"] for c in self.cagrilar]

    def cagri(self, parca: str) -> dict:
        """Parçayı içeren TEK çağrı — yoksa/birden çoksa test kendi varsayımını kaybetmiş demektir."""
        eslesen = [c for c in self.cagrilar if parca in c["url"]]
        assert len(eslesen) == 1, f"{parca!r} için beklenen 1 çağrı, bulunan {len(eslesen)}"
        return eslesen[0]


def _client() -> TestClient:
    """Yaşam döngüsü BAŞLATILMADAN istemci (v287/v361 emsali): `with TestClient(app)`
    scheduler/hermes ipliklerini ayağa kaldırır ve bu uç için tamamen gereksizdir."""
    return TestClient(api.app)


@pytest.fixture(autouse=True)
def _ag_kapali(monkeypatch):
    """AĞ VARSAYILAN OLARAK KAPALI. Bu makinede 8888 bugün AYAKTA (ölçüldü 2026-09-02) — yani
    casusunu kurmayan bir test GERÇEK Hindsight'ı okur ve ölçtüğü şey artık kod değil o anki
    makine durumu olur. Her test kendi casusunu KENDİ kurar.

    İKİ BACAK KAPATILIR (TSK-108): `recall` POST'u `_kapi_getir`den GEÇMEZ — kendi boğazı
    `_hafiza_post`tur. Yalnız GET bacağını kapatan bir muhafız, POST çivilerinin CANLI 8888'e
    gitmesine izin verirdi ve o testler kodu değil makineyi ölçerdi. Bu fixture'ın kendisi de
    çivili: `test_ag_muhafizi_iki_bacagi_da_kapatir`."""
    def _yasak(*a, **kw):
        raise AssertionError("test kendi `_kapi_getir` casusunu kurmadı — gerçek ağ çağrısı yasak")

    def _yasak_post(*a, **kw):
        raise AssertionError("test kendi `_hafiza_post` casusunu kurmadı — gerçek ağ çağrısı yasak")

    monkeypatch.setattr(api, "_kapi_getir", _yasak)
    monkeypatch.setattr(api, "_hafiza_post", _yasak_post)
    yield


def _env_dosyasi(monkeypatch, tmp_path, anahtar: str | None = SAHTE_ANAHTAR) -> pathlib.Path:
    """Sahte `/opt/hindsight/.env`. `anahtar=None` → dosya HİÇ yazılmaz (bu makinenin gerçek hâli)."""
    yol = tmp_path / "hindsight.env"
    if anahtar is not None:
        yol.write_text(f"# yorum satiri\nHINDSIGHT_API_TENANT_API_KEY={anahtar}\nBASKA=deger\n")
    monkeypatch.setattr(api, "HAFIZA_ENV_DOSYASI", str(yol))
    return yol


# =================================================================================================
# ÖLÇÜLMÜŞ GERÇEK GÖVDELER — kaynak: A1 Hindsight, 2026-09-02 ölçümü. KAYIT BURADADIR.
# =================================================================================================
#
# ÇAPA BU DOSYANIN İÇİNDE, BİLEREK (E-9, düzeltme turu 2): burada önce ölçüm çıktısının dosya
# yoluna atıf vardı; `.superpowers/` GIT-IGNORE'ludur, yani o çapa cloud klonunda ÖLÜdür ve
# okuyanı hiçbir yere götürmez. Ölçümün KENDİSİ aşağıdaki fixture'lara taşındı — kanıt, ona atıf
# veren şerhle değil, gövdenin kendisiyle yaşar.
#
# NE DOĞRULANIR, NE DOĞRULANMAZ (E-10): bu fixture'lar vekilin ZARFINI çivilerler — "upstream ne
# döndürdüyse `stats`/`llm_stats`/`audit_stats` alanına AYNEN geçer". UPSTREAM ŞEMASINI
# ÇİVİLEMEZLER: Hindsight bir gün alan adı değiştirirse bu dosya yeşil kalır (vekil süzmediği için
# davranışı gerçekten değişmez) — sürüklenmeyi yakalayan şey `/version` çivileridir, çünkü orada
# vekil bir alanı ADIYLA okur. Yani "çivi yeşil" cümlesi burada şemanın doğruluğunu KANITLAMAZ.

#: Bugün A1'de ölçülen bank'ler. Bot bank'leri YOK — "bank yok" ≠ "ölçülemedi".
BANKALAR_GOVDE = json.dumps({"banks": [{"bank_id": "meridian-arsiv"}, {"bank_id": "smoke-067"}]}).encode()

#: `/version` GERÇEK gövdesi. DÜZELTME TURU 1: burada önce `{"version": …}` yazıyordu — UYDURULMUŞ
#: bir alan adı. Kod da aynı adı bekliyordu, yani çivi KENDİ VARSAYIMINI doğruluyordu ve canlıda
#: `surum` sonsuza dek `null` kalırdı. Fixture'ın gerçeğe çekilmesi, çivinin artık kodu değil
#: DÜNYAYI ölçtüğünün kanıtıdır (`api_version`, `version` DEĞİL).
SURUM_OLCULEN = "0.9.2"
VERSION_GOVDE = json.dumps({
    "api_version": SURUM_OLCULEN,
    "features": {"observations": True, "mcp": True, "worker": True, "bank_config_api": True,
                 "bank_llm_health": False, "file_upload_api": True},
}).encode()

#: `banks/{id}/stats` ve `llm-requests/stats`: gövde şekli ölçüm kaydında kesilmişti; bu ikisi
#: TEMSİLİdir (vekil aynen geçirdiği için davranış bunlardan bağımsızdır — yukarıdaki şerh).
STATS_GOVDE = json.dumps({"memory_count": 42, "size_bytes": 8192}).encode()
LLM_GOVDE = json.dumps({"request_count": 7, "total_tokens": 1234}).encode()

#: `audit-logs/stats` GERÇEK gövdesi (ölçüldü 2026-09-02). DÜZELTME TURU 2 (E-10): burada önce
#: `{"event_count": 3}` yazıyordu — UYDURULMUŞ bir şema; gerçek gövde kova tabanlıdır.
#:
#: `buckets` ÖLÇÜM ANINDA BOŞTU ve BOŞ BIRAKILDI: kova ELEMANININ şekli ölçülMEDİ, uydurulmuş bir
#: kova tam da bu turda kapatılan sahte-şema sınıfını geri getirirdi ("ölçemediğini uydurma" —
#: `{"time":…,"statuses":{…}}` benzeri bir eleman `llm-requests/stats`ten ANALOJİYLE türetilirdi,
#: ölçümden değil). İç içe gövdenin aynen geçtiği ayrıca çivili: `test_ic_ice_govde_aynen_gecer`.
AUDIT_GOVDE = json.dumps({
    "bank_id": "meridian-arsiv", "period": "7d", "trunc": "day",
    "start": "2026-08-26T08:36:44.641719+00:00", "buckets": [],
}).encode()

#: GÖREV 6-A (2026-09-02, A1 18:15 UTC, bank meridian-arsiv) — `banks/{id}/profile` gövdesinin
#: GERÇEK ANAHTARLARI. Ölçüm kaydı yalnız anahtar adlarını taşıyor ("yalnız ANAHTAR ADLARI
#: ölçüldü, değerler değil" — STATS_GOVDE/LLM_GOVDE emsali); DEĞERLER TEMSİLİdir. `background`
#: openapi'nin KENDİ `example:`inde YOK (alan nullable, örnek onu atlamış) ama CANLI gövdede
#: VARDI — bu da fixture'ın openapi örneğinden değil ÖLÇÜMDEN geldiğinin kanıtıdır.
#:
#: `_CPUI_GOVDELER`in KENDİ SÖZLEŞMESİYLE (`_cpui_esleme`) UYUMLU: aşağıdaki sınıf-1 gövdeler
#: `_tam_esleme`nin ÖN-KODLANMIŞ `bytes` kayıtlarından (`AUDIT_GOVDE` vb.) FARKLI olarak HAM
#: `dict`tir — `_cpui_esleme` her kaydı KENDİSİ `json.dumps().encode()`ler; burada da `.encode()`
#: edilseydi çift-kodlama olurdu (ölçüldü: kırmızı-önce turunda `TypeError: bytes JSON
#: serializable değil`).
PROFIL_GOVDE = {
    "bank_id": "meridian-arsiv", "name": "Meridian Arşiv", "background": None,
    "disposition": {"skepticism": 3, "literalism": 3, "empathy": 3},
    "mission": "Meridian'ın uzun-vadeli hafıza bankası",
}

#: GÖREV 6-A (2026-09-02, A1 18:15 UTC, bank meridian-arsiv, `?limit=2`) — `banks/{id}/graph`
#: gövdesinin GERÇEK ANAHTARLARI. Zarf {edges, limit, nodes, table_rows, total_units} —
#: `GraphDataResponse` (openapi) ile ALAN ADI düzeyinde tutarlı. `node.data`/`edge.data` İÇİ,
#: openapi'nin KISALTILMIŞ örneğinden DAHA ZENGİN ölçüldü (`type` YOK, `color`/`context`/`date`/
#: `entities`/`label`/`text` VAR — node; `color`/`entityName`/`lineStyle`/`linkType`/`source`/
#: `target`/`weight` VAR — edge); DEĞERLER yine TEMSİLİdir. HAM `dict` (yukarıdaki şerh).
GRAF_CANLI_GOVDE = {
    "nodes": [{"data": {"id": "n1", "label": "Alice works at Google", "color": "#42a5f5",
                        "context": "Work info", "date": "2026-08-15T10:30:00Z",
                        "entities": "Alice (PERSON), Google (ORGANIZATION)",
                        "text": "Alice works at Google"}}],
    "edges": [{"data": {"id": "n1-n2", "source": "n1", "target": "n2", "weight": 5,
                        "color": "#9e9e9e", "entityName": "Alice", "lineStyle": "solid",
                        "linkType": "semantic"}}],
    "table_rows": [{"id": "n1", "text": "Alice works at Google", "context": "Work info",
                    "date": "2026-08-15T10:30:00Z",
                    "entities": "Alice (PERSON), Google (ORGANIZATION)"}],
    "total_units": 1, "limit": 2,
}


def _tam_esleme(**degistir) -> dict[str, bytes | str]:
    """Sağlıklı bir Hindsight'ın tüm uçları. Tek tek ezilebilir (`**degistir`)."""
    esleme: dict[str, bytes | str] = {
        "/health": b'{"status":"ok"}',
        "/version": VERSION_GOVDE,
        "/v1/default/banks": BANKALAR_GOVDE,
    }
    for bank in ("meridian-arsiv", "smoke-067"):
        esleme[f"/banks/{bank}/stats"] = STATS_GOVDE
        esleme[f"/banks/{bank}/llm-requests/stats"] = LLM_GOVDE
        esleme[f"/banks/{bank}/audit-logs/stats"] = AUDIT_GOVDE
    esleme.update(degistir)
    return esleme


def _kurulum(monkeypatch, tmp_path, *, esleme=None, anahtar=SAHTE_ANAHTAR) -> _Casus:
    _env_dosyasi(monkeypatch, tmp_path, anahtar)
    casus = _Casus(_tam_esleme() if esleme is None else esleme)
    monkeypatch.setattr(api, "_kapi_getir", casus)
    monkeypatch.setattr(api, "_hafiza_post", casus.post)
    return casus


def _dolu(neden) -> bool:
    return isinstance(neden, str) and len(neden) >= GEREKCE_ASGARI


UCLAR = ("/api/hindsight", "/api/hindsight/liste?bank=meridian-arsiv",
         "/api/hindsight/detay?bank=meridian-arsiv&kimlik=m1")


# --------------------------------------------------------------- A. KAYIT + YETKİ

def test_ucler_rota_tablosunda_kayitli():
    yollar = {getattr(r, "path", None) for r in api.app.routes}
    for yol in ("/api/hindsight", "/api/hindsight/liste", "/api/hindsight/detay"):
        assert yol in yollar, f"`{yol}` kayıtlı değil — pano yüzeyi hiç doğmamış"


def test_yalniz_get(monkeypatch, tmp_path, sandbox_state):
    """SALT-OKUNUR SÖZLEŞMESİ. Bu uç Hindsight'ın YAZAN fiillerine (memory ekleme/silme) bir köprü
    DEĞİLDİR; GET dışında hiçbir fiil tanımlı olmamalı. 405 rota eşleşmesinde doğar (yetkiden
    ÖNCE), yani kapı açık bir istemci de POST edemez."""
    _kurulum(monkeypatch, tmp_path)
    cl = _client()
    for yol in ("/api/hindsight", "/api/hindsight/liste", "/api/hindsight/detay"):
        for fiil in ("post", "put", "delete", "patch"):
            r = getattr(cl, fiil)(yol)
            assert r.status_code == 405, f"{fiil.upper()} {yol} → {r.status_code} (405 bekleniyordu)"


@pytest.mark.parametrize("yol", UCLAR)
def test_uc_auth_cagiriyor(monkeypatch, tmp_path, sandbox_state, yol):
    """Kaynak metni değil DAVRANIŞ: `_auth` casusu çağrılmazsa kırmızı."""
    _kurulum(monkeypatch, tmp_path)
    cagrildi: list = []
    monkeypatch.setattr(api, "_auth", lambda request: cagrildi.append(1))
    r = _client().get(yol)
    assert r.status_code == 200, r.text
    assert cagrildi == [1], f"`{yol}`: `_auth` çağrılmadı — hafıza yetkisiz açık"


@pytest.mark.parametrize("yol", UCLAR)
def test_auth_kapisi_cerezsiz_401(monkeypatch, tmp_path, sandbox_state, yol):
    """GERÇEK token yolu (`_auth` casuslanmadan): çerez/token yoksa 401, token varsa 200.
    Hafıza bankası operasyonun anlatısıdır — yetkisiz okunmaz."""
    _kurulum(monkeypatch, tmp_path)
    monkeypatch.setattr(api, "DASH_TOKEN", "v375-pano-jetonu")
    monkeypatch.setattr(api.auth, "password_set", lambda: False)
    monkeypatch.setattr(api.auth, "verify_session", lambda c: False)

    cl = _client()
    assert cl.get(yol).status_code == 401, f"`{yol}`: token'sız istek geçti"
    ok = cl.get(yol, headers={"x-meridian-token": "v375-pano-jetonu"})
    assert ok.status_code == 200, ok.text


# ------------------------------------------------------ B. ÖLÇÜLEMEZLİK YUTULMAZ

@pytest.mark.parametrize("yol", UCLAR)
def test_env_yokken_200_ve_neden_dolu(monkeypatch, tmp_path, sandbox_state, yol):
    """`/opt/hindsight/.env` YOKKEN (bu makinenin gerçek hâli) üç uç da 200 döner ve ölçemediğini
    SÖYLER. 500 dönmek panonun Hafıza sayfasını komple karartırdı; sessiz `[]`/`{}` ise "hafızada
    hiçbir şey yok" YALANI olurdu."""
    _kurulum(monkeypatch, tmp_path, anahtar=None)
    r = _client().get(yol)
    assert r.status_code == 200, r.text
    g = r.json()

    if yol == "/api/hindsight":
        assert g["bankalar"] == [], "anahtar yokken banka UYDURULDU"
        assert _dolu(g["bankalar_neden"]), f"ölçülemezlik sessiz: {g['bankalar_neden']!r}"
        assert ".env" in g["bankalar_neden"], "gerekçe anahtar dosyasını ADIYLA söylemiyor"
        assert g["kota"] == {} and g["operasyon"] == {}
    elif "liste" in yol:
        assert g["ogeler"] == [] and _dolu(g["neden"])
    else:
        assert g["oge"] is None and _dolu(g["neden"])


def test_env_yokken_saglik_BAGIMSIZ_olculur(monkeypatch, tmp_path, sandbox_state):
    """`/health` ve `/version` ANAHTARSIZDIR (ölçüldü 2026-09-02). Anahtar yokluğunun sağlık
    bacağını da düşürmesi, TEK arızayı İKİ körlüğe çevirirdi (v361'in prometheus dersi)."""
    casus = _kurulum(monkeypatch, tmp_path, anahtar=None)
    g = _client().get("/api/hindsight").json()

    assert g["saglik"]["erisilebilir"] is True, "anahtar yokluğu sağlık bacağını da düşürdü"
    assert g["saglik"]["surum"] == SURUM_OLCULEN
    assert g["saglik"]["neden"] is None
    assert not any("/v1/" in u for u in casus.url_ler()), \
        "anahtar yokken kimlikli `/v1/*` ucuna anahtarsız istek atıldı"


def test_surum_gercek_api_version_alanindan_okunur(monkeypatch, tmp_path, sandbox_state):
    """DÜZELTME TURU 1 — CANLI ÖLÇÜMLE KANITLI SINIF. Hindsight `/version` gövdesinde sürüm alanı
    `api_version`dır, `version` DEĞİL (ölçüldü 2026-09-02, A1). Kod `version` beklediği için
    canlıda `surum` sonsuza dek `null` kalıyordu — üstelik SESSİZCE: hiçbir `neden` üretilmiyordu.
    Bu çivi gerçek gövdeyi besler, yani uydurulmuş bir alan adını doğrulayamaz."""
    _kurulum(monkeypatch, tmp_path)
    s = _client().get("/api/hindsight").json()["saglik"]
    assert s["surum"] == SURUM_OLCULEN, f"gerçek `/version` gövdesinden sürüm okunamadı: {s}"
    assert s["neden"] is None


@pytest.mark.parametrize("govde", [
    b'{"surum":"9.9.9","features":{}}',       # tanınmayan alan adı (şema sürüklenmesi)
    b'{"api_version":123}',                   # alan var, str DEĞİL
    b'{"api_version":""}',                    # alan var, BOŞ
    b'["0.9.2"]',                             # gövde sözlük bile değil
])
def test_taninmayan_surum_alani_sessizce_null_kalmaz(monkeypatch, tmp_path, sandbox_state, govde):
    """SKALER ALANDA DA "TANIMADIĞINI SESSİZCE BOŞ SAYMA". Bu, düzeltme turu 1'in ASIL bulgusuydu:
    ilke dizi/kimlik zarflarına uygulanmıştı ama `surum`a UYGULANMAMIŞTI. `surum: null` + BOŞ
    `neden`, panoda "Hindsight sürümünü bildirmiyor" diye okunur; oysa ölçülen "alan adını
    tanımadım"dır ve bu bir ŞEMA SÜRÜKLENMESİ ALARMIdır.

    Gerekçe alan ADLARINI taşır (sır değildir), DEĞERLERİ değil."""
    _kurulum(monkeypatch, tmp_path, esleme=_tam_esleme(**{"/version": govde}))
    s = _client().get("/api/hindsight").json()["saglik"]

    assert s["erisilebilir"] is True, "sürüm okunamaması sağlık bacağını da düşürdü"
    assert s["surum"] is None, "tanınmayan alandan sürüm UYDURULDU"
    assert _dolu(s["neden"]), f"sürüm alanı tanınmadı ama SESSİZ kalındı: {s['neden']!r}"
    assert "9.9.9" not in (s["neden"] or ""), "gerekçe alan DEĞERİNİ gövdeye taşıdı"


def test_saglik_erisilemez_200_ama_durust(monkeypatch, tmp_path, sandbox_state):
    """Hindsight tamamen düşükken: 200, `erisilebilir` YANLIŞ, `surum` `None` (0 ya da "" değil),
    `neden` DOLU."""
    _kurulum(monkeypatch, tmp_path, esleme={
        "/health": "127.0.0.1:8888 okunamadı (URLError: baglanti reddedildi)",
        "/version": "127.0.0.1:8888 okunamadı (URLError: baglanti reddedildi)",
        "/v1/default/banks": "127.0.0.1:8888 okunamadı (URLError: baglanti reddedildi)"})
    r = _client().get("/api/hindsight")
    assert r.status_code == 200, r.text
    g = r.json()
    assert g["saglik"]["erisilebilir"] is False
    assert g["saglik"]["surum"] is None, "ölçülemeyen sürüm UYDURULDU"
    assert _dolu(g["saglik"]["neden"])
    assert g["bankalar"] == [] and _dolu(g["bankalar_neden"])


def test_bozuk_json_yutulmaz(monkeypatch, tmp_path, sandbox_state):
    """Upstream 200 dönüp GÖVDESİ bozuksa: boş liste + DOLU neden. Sessiz `[]` panoda "banka yok"
    diye okunurdu — oysa ölçülen "gövdeyi anlamadım"dır."""
    _kurulum(monkeypatch, tmp_path, esleme=_tam_esleme(**{"/v1/default/banks": b"{bu json degil"}))
    g = _client().get("/api/hindsight").json()
    assert g["bankalar"] == []
    assert _dolu(g["bankalar_neden"])


def test_beklenmeyen_zarf_sessizce_bos_donmez(monkeypatch, tmp_path, sandbox_state):
    """ŞEMA SÜRÜKLENMESİ ALARMI. Hindsight bir gün banka zarfını değiştirirse, dizi ARAYAN kod
    sessizce `[]` döner ve pano "hafıza boş" der. Tanınmayan zarf `neden` ÜRETİR."""
    _kurulum(monkeypatch, tmp_path,
             esleme=_tam_esleme(**{"/v1/default/banks": b'{"beklenmedik": {"a": 1}}'}))
    g = _client().get("/api/hindsight").json()
    assert g["bankalar"] == []
    assert _dolu(g["bankalar_neden"]), "tanınmayan zarf SESSİZCE boş listeye çevrildi"


def test_bos_banka_listesi_olculdu_sayilir(monkeypatch, tmp_path, sandbox_state):
    """ÜÇ-DURUM AYRIMI: Hindsight ayakta ve GERÇEKTEN bankası yoksa `bankalar: []` ama
    `bankalar_neden: None`. Bu, ölçülememiş boşluktan (dolu `neden`) AYRI bir hâldir ve panonun
    boş-durum bileşeninin dayanağıdır."""
    _kurulum(monkeypatch, tmp_path, esleme=_tam_esleme(**{"/v1/default/banks": b'{"banks": []}'}))
    g = _client().get("/api/hindsight").json()
    assert g["bankalar"] == []
    assert g["bankalar_neden"] is None, "ÖLÇÜLMÜŞ boşluk 'ölçemedim' gibi gösterildi"
    assert g["kota"] == {} and g["operasyon"] == {}


def test_tek_banka_stats_arizasi_otekini_dusurmez(monkeypatch, tmp_path, sandbox_state):
    """İZOLASYON: bir bankanın `stats`i okunamazsa ÖTEKİ banka hâlâ ölçülür. Aksi hâlde tek bozuk
    banka bütün sayfayı karartırdı."""
    _kurulum(monkeypatch, tmp_path, esleme=_tam_esleme(
        **{"/banks/smoke-067/stats": "stats okunamadı (HTTPError: 500)"}))
    g = _client().get("/api/hindsight").json()
    kirilim = {b["bank_id"]: b for b in g["bankalar"]}

    assert kirilim["meridian-arsiv"]["stats"] == {"memory_count": 42, "size_bytes": 8192}
    assert kirilim["meridian-arsiv"]["stats_neden"] is None
    assert kirilim["smoke-067"]["stats"] is None, "ölçülemeyen stats için sahte gövde üretildi"
    assert _dolu(kirilim["smoke-067"]["stats_neden"])


# ------------------------------------------------------------ C. ZARF AYNEN GEÇER

def test_bankalar_stats_kota_operasyon_akisi(monkeypatch, tmp_path, sandbox_state):
    """Sözleşmenin ANA çivisi: dört bölüm de upstream gövdesini AYNEN taşır (süzme yok, maske var)
    ve zarfın şekli Görev 2'nin (UI) okuyacağı sözleşmedir."""
    casus = _kurulum(monkeypatch, tmp_path)
    r = _client().get("/api/hindsight")
    assert r.status_code == 200, r.text
    g = r.json()

    assert set(g) == {"saglik", "bankalar", "bankalar_neden", "kota", "operasyon"}, sorted(g)
    assert g["saglik"] == {"erisilebilir": True, "surum": SURUM_OLCULEN, "neden": None}

    assert [b["bank_id"] for b in g["bankalar"]] == ["meridian-arsiv", "smoke-067"]
    for b in g["bankalar"]:
        assert set(b) == {"bank_id", "stats", "stats_neden"}, sorted(b)
        assert b["stats"] == {"memory_count": 42, "size_bytes": 8192}, "upstream gövdesi SÜZÜLDÜ"
        assert b["stats_neden"] is None
    assert g["bankalar_neden"] is None

    assert set(g["kota"]) == {"meridian-arsiv", "smoke-067"}
    assert g["kota"]["meridian-arsiv"] == {"llm_stats": {"request_count": 7, "total_tokens": 1234},
                                           "neden": None}
    assert set(g["operasyon"]) == {"meridian-arsiv", "smoke-067"}
    assert g["operasyon"]["smoke-067"] == {"audit_stats": json.loads(AUDIT_GOVDE),
                                           "neden": None}

    # Ölçülen uçlar BİREBİR: uç yeni bir upstream'e gitmeye başlarsa (ya da bir bacağı düşürürse)
    # bu sayım ısırır. 2 (health+version) + 1 (banks) + 3×2 (banka başına stats/llm/audit) = 9.
    assert len(casus.cagrilar) == 9, casus.url_ler()


def test_ic_ice_govde_aynen_gecer(monkeypatch, tmp_path, sandbox_state):
    """AYNEN-GEÇİŞİN DERİNLİĞİ. Ölçülen `audit-logs/stats` gövdesinde `buckets` BOŞTU, yani gerçek
    fixture iç içe bir yapı taşımıyor ve "derin gövde de bozulmadan geçiyor mu" sorusu onunla
    ölçülemez.

    Buradaki gövde AÇIKÇA SENTETİKTİR — Hindsight'ın kova şeması olduğunu İDDİA ETMEZ (o şekil
    ölçülmedi). Ölçtüğü tek şey vekilin davranışıdır: sözlük/liste/sayı/`null` iç içe gelse de
    süzülmez, yeniden adlandırılmaz, düzleştirilmez."""
    sentetik = {"buckets": [{"time": "2026-09-01T00:00:00+00:00", "sayilar": [1, 2, 3],
                             "ic": {"derin": {"deger": None, "bayrak": False}}}],
                "toplam": 3}
    _kurulum(monkeypatch, tmp_path, esleme=_tam_esleme(
        **{"/banks/meridian-arsiv/audit-logs/stats": json.dumps(sentetik).encode()}))

    g = _client().get("/api/hindsight").json()
    assert g["operasyon"]["meridian-arsiv"]["audit_stats"] == sentetik, \
        "iç içe gövde aynen geçmedi — vekil süzüyor/düzleştiriyor"


def test_upstream_yollari_olculen_openapi_ile_ayni(monkeypatch, tmp_path, sandbox_state):
    """Uç, 2026-09-02'de openapi'den ÖLÇÜLEN yollara gider — uydurulmuş bir yola değil."""
    casus = _kurulum(monkeypatch, tmp_path)
    _client().get("/api/hindsight")
    urller = casus.url_ler()

    assert f"{api.HAFIZA_TABAN_URL}/health" in urller
    assert f"{api.HAFIZA_TABAN_URL}/version" in urller
    assert f"{api.HAFIZA_TABAN_URL}/v1/default/banks" in urller
    assert f"{api.HAFIZA_TABAN_URL}/v1/default/banks/meridian-arsiv/stats" in urller
    assert f"{api.HAFIZA_TABAN_URL}/v1/default/banks/smoke-067/llm-requests/stats" in urller
    assert f"{api.HAFIZA_TABAN_URL}/v1/default/banks/smoke-067/audit-logs/stats" in urller


def test_liste_ve_detay_zarfi(monkeypatch, tmp_path, sandbox_state):
    """`/liste` ve `/detay` da upstream gövdesini AYNEN taşır.

    `/detay` ZARFI 2026-09-02'de GENİŞLEDİ (TSK-108, plan: "mevcut; history eklenir"): CP'nin
    memory-detail-panel'i kaydı ve tarihçesini BİRLİKTE gösterir. Genişleme EK'tir — `oge`/`neden`
    sözleşmesi aynen durur, yani mevcut pano kodu kırılmaz.

    `/liste` ZARFINA `toplam` EKLENDİ (düzeltme turu 1, R4). Gerekçe bir tutarsızlıktır:
    `/gozlemler` AYNI upstream çağrısına (`memories/list`) gidiyor ve zarfın TAMAMINI (`total`
    dâhil) taşıyor; `/liste` ise diziyi söküp `total`ı düşürüyordu — tek kaynağın iki farklı
    gerçeği. Ek alandır, `ogeler`/`neden` aynen durur."""
    ogeler = json.dumps({"items": [{"id": "m1", "text": "ilk"}, {"id": "m2", "text": "ikinci"}],
                         "total": 150, "limit": 100, "offset": 0})
    tarihce = json.dumps({"items": [{"id": "h1", "action": "created"}]})
    _kurulum(monkeypatch, tmp_path, esleme={
        "/memories/list": ogeler.encode(),
        "/memories/m1": json.dumps({"id": "m1", "text": "ilk", "metadata": {"k": "v"}}).encode(),
        "/memories/m1/history": tarihce.encode()})

    liste = _client().get("/api/hindsight/liste?bank=meridian-arsiv").json()
    assert set(liste) == {"ogeler", "neden", "toplam"}, sorted(liste)
    assert liste["ogeler"] == [{"id": "m1", "text": "ilk"}, {"id": "m2", "text": "ikinci"}]
    assert liste["neden"] is None
    assert liste["toplam"] == 150, "sayfalamanın gerçeği (`total`) yine düşürüldü"

    detay = _client().get("/api/hindsight/detay?bank=meridian-arsiv&kimlik=m1").json()
    assert set(detay) == {"oge", "neden", "tarihce", "tarihce_neden"}, sorted(detay)
    assert detay["oge"] == {"id": "m1", "text": "ilk", "metadata": {"k": "v"}}
    assert detay["neden"] is None
    assert detay["tarihce"] == {"items": [{"id": "h1", "action": "created"}]}
    assert detay["tarihce_neden"] is None


@pytest.mark.parametrize("govde,beklenen", [
    ({"items": [], "total": 0}, 0),                     # SIFIR bir ölçümdür, "bilmiyorum" değil
    ({"items": []}, None),                              # alan yoksa UYDURULMAZ
    ({"items": [], "total": "yüz"}, None),              # tip sürüklenmesi sessizce 0 sayılmaz
    ([{"id": "m1"}], None),                             # zarfsız dizi: taşınacak toplam yok
])
def test_liste_toplami_uydurmaz(monkeypatch, tmp_path, sandbox_state, govde, beklenen):
    """UYDURMA YASAĞININ SAYFALAMA HÂLİ. `toplam` yokken `0` yazmak panoda "hiç kayıt yok" diye
    okunur — oysa ölçülen şey "kaç kayıt olduğunu SÖYLEMEDİ"dir. `None` ≠ `0` (bu dosyanın
    kurucu ayrımı, `bankalar: []` vakası)."""
    _kurulum(monkeypatch, tmp_path,
             esleme={"/memories/list": json.dumps(govde).encode()})
    g = _client().get("/api/hindsight/liste?bank=meridian-arsiv").json()
    assert g["toplam"] == beklenen, f"{govde!r} → toplam {g['toplam']!r}, beklenen {beklenen!r}"


def test_detay_bulunamayan_null_neden(monkeypatch, tmp_path, sandbox_state):
    """Bulunamayan kayıt: `oge` `None` (boş sözlük DEĞİL — "kayıt var ama içi boş" yalanı olurdu)
    ve `neden` DOLU."""
    _kurulum(monkeypatch, tmp_path,
             esleme={"/memories/yok": "detay okunamadı (HTTPError: 404 Not Found)"})
    r = _client().get("/api/hindsight/detay?bank=meridian-arsiv&kimlik=yok")
    assert r.status_code == 200, "bulunamayan kayıt panoyu 404'e düşürdü"
    g = r.json()
    assert g["oge"] is None
    assert _dolu(g["neden"]) and "404" in g["neden"], g["neden"]


# ---------------------------------------------------------------- D. SIR DUVARI

@pytest.mark.parametrize("yol", UCLAR)
def test_anahtar_govdeye_sizamaz(monkeypatch, tmp_path, sandbox_state, yol):
    """SIZINTI ÇİVİSİ, VAKUM DEĞİL: anahtar yanıtın HİÇBİR yerinde geçmez, ama `/v1/*` isteğinde
    `Authorization: Bearer …` olarak GERÇEKTEN gönderilmiştir. Gönderilmemiş bir sırrın yanıtta
    olmaması hiçbir şey kanıtlamaz (v361'in ölçülmüş dersi)."""
    casus = _kurulum(monkeypatch, tmp_path, esleme=_tam_esleme(
        **{"/memories/list": b'{"items": []}', "/memories/m1": b'{"id": "m1"}'}))
    r = _client().get(yol)

    assert r.status_code == 200, r.text
    assert SAHTE_ANAHTAR not in r.text, "TENANT ANAHTARI PANOYA SIZDI"

    kimlikli = [c for c in casus.cagrilar if "/v1/" in c["url"]]
    assert kimlikli, "kimlikli hiçbir çağrı yapılmamış — sızıntı çivisi vakumda koşuyordu"
    for c in kimlikli:
        assert c["basliklar"].get("Authorization") == f"Bearer {SAHTE_ANAHTAR}", \
            f"{c['url']}: ölçülen kimlik deseni `Authorization: Bearer` DEĞİL: {c['basliklar']}"
        assert "X-API-Key" not in c["basliklar"], \
            "`X-API-Key` ÖLÇÜLDÜ ve 401 veriyor (2026-09-02) — yanlış başlıkla gidiliyor"


def test_anahtarsiz_uclara_anahtar_gonderilmez(monkeypatch, tmp_path, sandbox_state):
    """EN AZ YETKİ: `/health` ve `/version` anahtarsız 200 veriyor (ölçüldü). Sırrı gereksiz yere
    tele koymak, sızıntı yüzeyini bedelsiz büyütmektir."""
    casus = _kurulum(monkeypatch, tmp_path)
    _client().get("/api/hindsight")
    for parca in ("/health", "/version"):
        assert not casus.cagri(parca)["basliklar"], \
            f"{parca} anahtarsız bir uç — yine de başlık gönderildi"


@pytest.mark.parametrize("yol", UCLAR)
def test_istisna_metnindeki_anahtar_maskelenir(monkeypatch, tmp_path, sandbox_state, yol):
    """İKİNCİ SAVUNMA HATTI (`_kapi_maskele`): alt katman bir gün anahtarı istisna metnine ya da
    upstream gövdesine koyarsa, o metin `neden`e/gövdeye AYNEN geçmemeli. Gerekçenin KENDİSİ
    silinmez — silmek sızıntıyı kapatıp körlüğü açardı."""
    sizan = f"401 — Authorization: Bearer {SAHTE_ANAHTAR} reddedildi"
    _kurulum(monkeypatch, tmp_path, esleme={
        "/health": b'{"status":"ok"}', "/version": VERSION_GOVDE,
        "/v1/default/banks": sizan, "/memories/list": sizan, "/memories/m1": sizan})

    r = _client().get(yol)
    assert r.status_code == 200, r.text
    assert SAHTE_ANAHTAR not in r.text, "istisna metniyle taşınan anahtar panoya sızdı"
    assert "***" in r.text, "maskeleme uğruna gerekçe komple silinmiş — körlük açıldı"


def test_upstream_govdesindeki_anahtar_maskelenir(monkeypatch, tmp_path, sandbox_state):
    """Sır upstream'in KENDİ gövdesinden de gelebilir (Hindsight bir gün tenant anahtarını
    `stats`e yazarsa). Aynen-geçiş sözleşmesi maskeyi ISKALAMAZ."""
    _kurulum(monkeypatch, tmp_path, esleme=_tam_esleme(
        **{"/banks/meridian-arsiv/stats": json.dumps({"tenant_key": SAHTE_ANAHTAR}).encode()}))
    r = _client().get("/api/hindsight")
    assert SAHTE_ANAHTAR not in r.text, "upstream gövdesindeki anahtar aynen panoya basıldı"


# ----------------------------------------------------------- E. LİSTE TAVANI SUNUCUDA

def test_liste_limit_tavani_kirpar(monkeypatch, tmp_path, sandbox_state):
    """KIRPMA SUNUCUDA. `limit` istemciden gelir ve istemciye GÜVENİLMEZ: `limit=9999` bir
    Hindsight sorgusunu ve pano yükünü sınırsız büyütür. Tavan `HAFIZA_LISTE_TAVANI`dır ve
    upstream URL'inde ÖLÇÜLÜR — "UI zaten 50 gönderiyor" bir güvence DEĞİLDİR."""
    casus = _kurulum(monkeypatch, tmp_path, esleme={"/memories/list": b'{"items": []}'})
    _client().get("/api/hindsight/liste?bank=meridian-arsiv&limit=9999")

    url = casus.cagri("/memories/list")["url"]
    assert "9999" not in url, f"kırpılmamış limit upstream'e gitti: {url}"
    assert f"limit={api.HAFIZA_LISTE_TAVANI}" in url, url
    assert api.HAFIZA_LISTE_TAVANI == 200


def test_liste_makul_limit_aynen_gecer(monkeypatch, tmp_path, sandbox_state):
    """Kırpma bir TAVANdır, sabit değil: tavanın altındaki değer AYNEN geçer (aksi hâlde sayfalama
    çalışmazdı)."""
    casus = _kurulum(monkeypatch, tmp_path, esleme={"/memories/list": b'{"items": []}'})
    _client().get("/api/hindsight/liste?bank=meridian-arsiv&limit=25&offset=75")
    url = casus.cagri("/memories/list")["url"]
    assert "limit=25" in url and "offset=75" in url, url


def test_liste_sacma_limit_offset_alt_sinira_oturur(monkeypatch, tmp_path, sandbox_state):
    """`limit=0`/negatif değerler upstream'e SIZMAZ: kimi API'de `limit=0` "hepsi" demektir ve
    tavanı sessizce delerdi. `offset` de negatif olamaz."""
    casus = _kurulum(monkeypatch, tmp_path, esleme={"/memories/list": b'{"items": []}'})
    _client().get("/api/hindsight/liste?bank=meridian-arsiv&limit=0&offset=-5")
    url = casus.cagri("/memories/list")["url"]
    assert "limit=0" not in url and "limit=-" not in url, url
    assert "offset=-" not in url and "offset=0" in url, url


@pytest.mark.parametrize("sorgu", ["limit=abc", "limit=1.5", "offset=xyz", "limit=&offset="])
def test_liste_bozuk_sayi_400_degil_tavana_oturur(monkeypatch, tmp_path, sandbox_state, sorgu):
    """EKSİK PARAMETRENİN KARDEŞİ: `limit`i `int` yazmak FastAPI'ye 422 ürettirir ve pano o cevabı
    gövde sanıp KARARIR — `bank` için kapatılan sınıf `limit` için açık kalamaz. Ayrıştırılamayan
    sayı bir ÖLÇÜM DEĞİLDİR: sessizce 0'a değil, beyan edilmiş varsayılana oturur."""
    casus = _kurulum(monkeypatch, tmp_path, esleme={"/memories/list": b'{"items": []}'})
    r = _client().get(f"/api/hindsight/liste?bank=meridian-arsiv&{sorgu}")

    assert r.status_code == 200, f"{sorgu!r}: {r.status_code} — pano karardı"
    url = casus.cagri("/memories/list")["url"]
    assert f"limit={api.HAFIZA_LISTE_TAVANI}" in url or "limit=1" in url, url
    assert "offset=0" in url, url


# --------------------------------------------------- F. EKSİK PARAMETRE 400 DEĞİL

def test_liste_bank_parametresiz_400_degil_neden(monkeypatch, tmp_path, sandbox_state):
    """FastAPI'nin varsayılanı ZORUNLU parametrede 422'dir ve pano o cevabı gövde sanıp KARARIR.
    Sözleşme: 200 + boş `ogeler` + DOLU `neden`. Ayrıca upstream'e HİÇ gidilmez."""
    casus = _kurulum(monkeypatch, tmp_path, esleme={"/memories/list": b'{"items": []}'})
    r = _client().get("/api/hindsight/liste")

    assert r.status_code == 200, f"eksik parametre {r.status_code} üretti — pano karardı"
    g = r.json()
    assert g["ogeler"] == []
    assert _dolu(g["neden"]) and "bank" in g["neden"], g["neden"]
    assert casus.cagrilar == [], "parametre eksikken yine de upstream'e gidildi"


@pytest.mark.parametrize("sorgu", ["", "?bank=meridian-arsiv", "?kimlik=m1", "?bank=&kimlik="])
def test_detay_eksik_parametre_400_degil_neden(monkeypatch, tmp_path, sandbox_state, sorgu):
    """`/detay` İKİ parametre ister; hangisi eksikse eksik — ve BOŞ dizge de eksiktir
    (`?bank=` bir değer DEĞİLDİR, upstream'e `/banks//memories/` diye giderdi)."""
    casus = _kurulum(monkeypatch, tmp_path, esleme={"/memories/m1": b'{"id":"m1"}'})
    r = _client().get(f"/api/hindsight/detay{sorgu}")

    assert r.status_code == 200, f"{sorgu!r}: {r.status_code}"
    g = r.json()
    assert g["oge"] is None
    assert _dolu(g["neden"])
    assert casus.cagrilar == [], f"{sorgu!r}: parametre eksikken upstream'e gidildi"


# --------------------------------------------------------------- G. YOL ENJEKSİYONU

@pytest.mark.parametrize("kotu", ["../../v1/default/banks", "a/../../etc", "a b", "a?x=1", "a#f"])
def test_bank_kimligi_yol_enjeksiyonuna_kapali(monkeypatch, tmp_path, sandbox_state, kotu):
    """`bank` KULLANICI GİRDİSİDİR ve upstream URL'inin PATH'ine giriyor. Kaçırılmazsa `../../`
    ile Hindsight'ın BAŞKA bir ucuna gidilir (yazan bir uca bile) — salt-okunur sözleşmesi
    istemcinin insafına kalırdı. `/` `%2F` olarak kaçırılmalı, çıplak kalmamalı."""
    casus = _kurulum(monkeypatch, tmp_path, esleme={"/memories/list": b'{"items": []}'})
    # GİRDİ İSTEMCİ TARAFINDA KAÇIRILIR, yoksa test VAKUMDA koşar: ölçüldü (mutasyon turu,
    # 2026-09-02) — `?bank=a#f` içindeki `#` bir FRAGMAN'dır, sunucuya hiç ulaşmaz ve çivi
    # kaçırılmamış `#`i "geçti" sanardı. Sunucunun GERÇEKTEN gördüğü değer `kotu` olmalı.
    import urllib.parse
    _client().get(f"/api/hindsight/liste?bank={urllib.parse.quote(kotu, safe='')}")

    url = casus.cagri("/memories/list")["url"]
    govde = url[len(f"{api.HAFIZA_TABAN_URL}/v1/default/banks/"):]
    kimlik = govde.split("/memories/list")[0]
    for ham in ("/", "..", " ", "?", "#"):
        assert ham not in kimlik, f"kaçırılmamış {ham!r} upstream PATH'ine girdi: {url}"


def test_detay_kimligi_yol_enjeksiyonuna_kapali(monkeypatch, tmp_path, sandbox_state):
    """Aynı sınıf, `kimlik` parametresinde."""
    casus = _kurulum(monkeypatch, tmp_path, esleme={"/memories/": b'{"id": "x"}'})
    _client().get("/api/hindsight/detay?bank=meridian-arsiv&kimlik=../../../stats")

    url = casus.cagrilar[0]["url"]
    kuyruk = url.split("/memories/", 1)[1]
    assert "/" not in kuyruk and ".." not in kuyruk, f"kaçırılmamış kimlik: {url}"


# ------------------------------------------------------------------ H. ZAMAN AŞIMI

def test_zaman_asimi_sabiti_beyanli():
    assert 0 < api.HAFIZA_ZAMAN_ASIMI_S <= 2.0


def test_zaman_asimi_kopyasi_ayrisirsa_isirir():
    """TEK-KAYNAK / AYRIŞMA ÇİVİSİ. Zaman aşımını GERÇEKTEN zorlayan sabit `_kapi_getir`in
    okuduğu `KAPI_ZAMAN_ASIMI_S`dir; `HAFIZA_ZAMAN_ASIMI_S` sözleşmenin BEYANIdır. İki kopya
    sessizce ayrışabilir: biri 2.0 kalıp öteki 30.0 olursa gövdedeki beyan YALAN söyler ve pano
    15 sn'lik yoklamada asılır. Ayrışma burada ÖTER."""
    assert api.HAFIZA_ZAMAN_ASIMI_S == api.KAPI_ZAMAN_ASIMI_S, (
        "beyan edilen hafıza zaman aşımı, `_kapi_getir`in zorladığından AYRIŞTI — "
        "beyan ya düzeltilmeli ya da `_kapi_getir` parametrikleştirilmeli")


def test_uc_state_defterine_yazmaz(monkeypatch, tmp_path, sandbox_state):
    """SALT-OKUNUR sözleşmesi: pano 15 sn'de bir yokluyor — yazan bir uç canlı defteri kirletirdi
    (v361 emsali)."""
    _kurulum(monkeypatch, tmp_path, esleme=_tam_esleme(
        **{"/memories/list": b'{"items": []}', "/memories/m1": b'{"id":"m1"}'}))
    once = sorted(p.name for p in sandbox_state.rglob("*"))
    cl = _client()
    for yol in UCLAR:
        cl.get(yol)
    assert sorted(p.name for p in sandbox_state.rglob("*")) == once


# ------------------------------------------------------- I. TEK-KAYNAK ÇIKARIMI

def test_env_anahtari_iki_cagirani_da_besler(monkeypatch, tmp_path):
    """`_env_anahtari(dosya, onek)` TEK kaynaktır: aynı ayrıştırma iki yerde kopyalanırsa
    (v361 + v375) sessizce ayrışır — tek-kaynak yasası."""
    yol = tmp_path / "x.env"
    yol.write_text("# yorum\nONEK_A=deger-a\nONEK_B=deger-b\n")

    assert api._env_anahtari(str(yol), "ONEK_A=") == ("deger-a", None)
    assert api._env_anahtari(str(yol), "ONEK_B=") == ("deger-b", None)

    deger, neden = api._env_anahtari(str(yol), "YOK_ONEK=")
    assert deger is None and _dolu(neden) and "YOK_ONEK=" in neden

    deger, neden = api._env_anahtari(str(tmp_path / "hic-yok.env"), "ONEK_A=")
    assert deger is None and _dolu(neden) and "hic-yok.env" in neden


def test_bos_deger_anahtar_sayilmaz(monkeypatch, tmp_path):
    """`ANAHTAR=` satırı bir anahtar DEĞİLDİR — boş dizgeyle `Bearer ` göndermek 401 döndürür ve
    arıza "yanlış anahtar" gibi görünürdü; gerçek arıza "anahtar hiç yok"tur."""
    yol = tmp_path / "bos.env"
    yol.write_text("HINDSIGHT_API_TENANT_API_KEY=\n")
    deger, neden = api._env_anahtari(str(yol), api.HAFIZA_ANAHTAR_ONEKI)
    assert deger is None and _dolu(neden) and "BOŞ" in neden


def test_v361_sarmalayicisi_davranisini_korur(monkeypatch, tmp_path):
    """ÇIKARIM REGRESYON ÇİVİSİ: `_kapi_admin_anahtari` artık `_env_anahtari`nin sarmalayıcısıdır
    ama SÖZLEŞMESİ değişmedi — v361 çivileri bu davranışa yaslanıyor."""
    yol = tmp_path / ".env-apisix"
    yol.write_text(f"# yorum\nAPISIX_ADMIN_KEY={SAHTE_ANAHTAR}\n")
    monkeypatch.setattr(api, "KAPI_ENV_DOSYASI", str(yol))
    assert api._kapi_admin_anahtari() == (SAHTE_ANAHTAR, None)

    monkeypatch.setattr(api, "KAPI_ENV_DOSYASI", str(tmp_path / "yok"))
    deger, neden = api._kapi_admin_anahtari()
    assert deger is None and ".env-apisix" not in (deger or "")
    assert _dolu(neden) and "yok" in neden


def test_hafiza_sabitleri_olculen_degerlerde():
    """Sabitler brief'in ÖLÇÜLMÜŞ gerçeklerinden gelir — uydurma değil."""
    assert api.HAFIZA_TABAN_URL == "http://127.0.0.1:8888"
    assert api.HAFIZA_ENV_DOSYASI == "/opt/hindsight/.env"
    assert api.HAFIZA_ANAHTAR_ONEKI == "HINDSIGHT_API_TENANT_API_KEY="
    assert api.HAFIZA_LISTE_TAVANI == 200


# =================================================================================================
# J. CP-UI GENİŞLEMESİ — TSK-108 Görev 1
# =================================================================================================
#
# YOL HARİTASI UYDURULMADI. Her yeni uç, Hindsight Control Plane'in (v0.9.2) KENDİ vekil
# rotasının gittiği dataplane ucuna gider; yollar ve sorgu parametreleri iki upstream kaynaktan
# OKUNDU (2026-09-02):
#   · `hindsight-control-plane/src/app/api/**/route.ts` — CP hangi uca, hangi parametreyle gidiyor
#   · `hindsight-clients/go/api/openapi.yaml` — dataplane'in KENDİ sözleşmesi (69 yol, 0.9.2)
# Bu yüzden aşağıdaki `CPUI` tablosu bir TASARIM DEĞİL bir ÖLÇÜM KAYDIdır: sağ sütun upstream'de
# gerçekten var olan yoldur. Uç yeni bir yola kayarsa `_Casus` "beklenmeyen kaynak" diye patlar.
#
# NEDEN PARAMETRİK: yüzey 3 uçtan 22 uca çıktı. Sözleşme başına TEK TEK yazılan çivi, yirmi ikinci
# uçta unutulur — ve unutulan çivi, olmayan çividen DAHA kötüdür (dosya "kapsıyorum" der).
# Aşağıdaki tablo ÇİVİLERİN GİRDİSİdir: yeni bir uç tabloya eklenmeden doğarsa
# `test_her_hafiza_ucu_tabloda_kayitli` öter.

#: (bizim yol + sorgu, upstream URL'de GÖRÜLMESİ gereken parça).
#: `B` bank kimliği; ikinci kimlikler `d1`/`z1`/`p1`.
CPUI: tuple[tuple[str, str], ...] = (
    ("/api/hindsight/ozet?bank=B", "/banks/B/stats/memories-timeseries"),
    ("/api/hindsight/varliklar?bank=B", "/banks/B/entities"),
    ("/api/hindsight/varlik-graf?bank=B", "/banks/B/entities/graph"),
    ("/api/hindsight/belgeler?bank=B", "/banks/B/documents"),
    ("/api/hindsight/belge-parcalari?bank=B&belge=d1", "/banks/B/documents/d1/chunks"),
    ("/api/hindsight/zihin-modelleri?bank=B", "/banks/B/mental-models"),
    ("/api/hindsight/zihin-modeli?bank=B&kimlik=z1", "/banks/B/mental-models/z1"),
    ("/api/hindsight/zihin-modeli-tarihce?bank=B&kimlik=z1", "/banks/B/mental-models/z1/history"),
    ("/api/hindsight/bilgi-tabani?bank=B", "/banks/B/knowledge-base/tree"),
    ("/api/hindsight/bilgi-arama?bank=B&q=alice", "/banks/B/knowledge-base/search"),
    ("/api/hindsight/bilgi-sayfasi?bank=B&sayfa=p1", "/banks/B/knowledge-base/pages/p1"),
    ("/api/hindsight/gozlemler?bank=B", "/banks/B/memories/list"),
    ("/api/hindsight/gozlem-kapsamlari?bank=B", "/banks/B/observations/scopes"),
    ("/api/hindsight/llm-istekleri?bank=B", "/banks/B/llm-requests"),
    ("/api/hindsight/llm-istatistik?bank=B", "/banks/B/llm-requests/stats"),
    ("/api/hindsight/denetim?bank=B", "/banks/B/audit-logs"),
    ("/api/hindsight/denetim-istatistik?bank=B", "/banks/B/audit-logs/stats"),
    ("/api/hindsight/islemler?bank=B", "/banks/B/operations"),
    ("/api/hindsight/yapilandirma?bank=B", "/banks/B/config"),
    # ---- Görev 6-A (2026-09-02) ----
    ("/api/hindsight/bellek-graf?bank=B", "/banks/B/graph"),
    ("/api/hindsight/profil?bank=B", "/banks/B/profile"),
)
CPUI_YOLLAR = tuple(y for y, _ in CPUI)

#: `{govde, neden}` zarfını taşıyan uçlar — yani `/ozet` (iki bacaklı) ve mevcut üçlü DIŞINDAKİLER.
CPUI_ZARFLI = tuple(y for y, _ in CPUI if not y.startswith("/api/hindsight/ozet"))

#: İkinci bir kimlik ZORUNLU olan uçlar: (yol, eksik parametrenin adı).
CPUI_IKI_KIMLIKLI = (
    ("/api/hindsight/belge-parcalari?bank=B", "belge"),
    ("/api/hindsight/zihin-modeli?bank=B", "kimlik"),
    ("/api/hindsight/zihin-modeli-tarihce?bank=B", "kimlik"),
    ("/api/hindsight/bilgi-sayfasi?bank=B", "sayfa"),
)

#: `limit` alan uçlar — kırpma SUNUCUDA olmalı (istemciye güven yok).
CPUI_LIMITLI = (
    ("/api/hindsight/varliklar?bank=B", "/banks/B/entities"),
    ("/api/hindsight/belgeler?bank=B", "/banks/B/documents"),
    ("/api/hindsight/belge-parcalari?bank=B&belge=d1", "/banks/B/documents/d1/chunks"),
    ("/api/hindsight/zihin-modelleri?bank=B", "/banks/B/mental-models"),
    ("/api/hindsight/bilgi-arama?bank=B&q=alice", "/banks/B/knowledge-base/search"),
    ("/api/hindsight/gozlemler?bank=B", "/banks/B/memories/list"),
    ("/api/hindsight/llm-istekleri?bank=B", "/banks/B/llm-requests"),
    ("/api/hindsight/denetim?bank=B", "/banks/B/audit-logs"),
    ("/api/hindsight/islemler?bank=B", "/banks/B/operations"),
    ("/api/hindsight/varlik-graf?bank=B", "/banks/B/entities/graph"),
    ("/api/hindsight/bellek-graf?bank=B", "/banks/B/graph"),
)

#: `tags` + `tags_match` ÇİFTİNİ kabul eden uçlar. DÜZELTME TURU 1 (I-3): `tags_match`in tek
#: çivisi `tags` VERMEDEN koşuyordu ve VAKUMDA yeşildi — kod etiket yokken `tags_match`i zaten
#: düşürüyor, yani çivi "sözlük süzdü" sanırken ölçtüğü şey etiket-bağlama kuralıydı. `/belgeler`
#: ve `/zihin-modelleri`nde ise hiçbir test `tags` göndermiyordu: kural orada TAMAMEN çivisizdi.
CPUI_ETIKETLI = (
    ("/api/hindsight/liste?bank=B", "/banks/B/memories/list"),
    ("/api/hindsight/belgeler?bank=B", "/banks/B/documents"),
    ("/api/hindsight/zihin-modelleri?bank=B", "/banks/B/mental-models"),
    ("/api/hindsight/bellek-graf?bank=B", "/banks/B/graph"),
)

#: ÖLÇÜLEN upstream `limit.maximum` değerleri (openapi, commit çapası dosya başlığında). Yalnız
#: SINIRI OLAN uçlar yazılı; ötekilerin şemasında `maximum` YOKTUR.
#:
#: BU TABLO BİR KIYAS ÇİVİSİDİR, kodun kaynağı DEĞİL: kod kendi tavanını `api._HAFIZA_UC_TAVANI`
#: ile taşır ve buradan TÜRETMEZ. İki kayıt ayrışırsa öter — çünkü kendi tavanımızı upstream'in
#: sınırının ÜSTÜNE koymak 422 üretir ve o 422 `neden`e "hafıza okunamadı" diye yazılır: yani
#: ölçüm arızası altyapı arızası gibi görünür (bu dosyanın kurucu yalan sınıfı).
UPSTREAM_LIMIT_MAKSIMUMU = {
    "/documents/d1/chunks": 1000, "/mental-models": 1000, "/knowledge-base/search": 50,
    "/operations": 100, "/audit-logs": 500, "/llm-requests": 500,
}


def _uc_kuyrugu(parca: str) -> str:
    return parca.split("/banks/B", 1)[1]


def _beklenen_tavan(parca: str) -> int:
    """Ucun beklenen tavanı KODUN TABLOSUNDAN türetilir, kopyalanmaz — kopyalansaydı tablo
    değiştiğinde çivi eski sayıyı doğrulamaya devam ederdi (çivi kendini doğrular)."""
    return api._HAFIZA_UC_TAVANI.get(_uc_kuyrugu(parca), api.HAFIZA_LISTE_TAVANI)


def _gonderilen_limit(url: str) -> int:
    import urllib.parse
    return int(urllib.parse.parse_qs(url.split("?", 1)[1])["limit"][0])


RECALL = "/api/hindsight/recall"


# ----------------------------------------------------- KAYNAKTAN TÜRETİLEN GÖVDELER (sınıf 2)
#
# Hepsi upstream `openapi.yaml` (v0.9.2) `example:` bloklarından. Alan ADLARI upstream'in;
# DEĞERLER upstream'in örnekleri — canlıda ölçülmüş sayılar DEĞİL.

STATS_ORNEK = {"bank_id": "user123", "total_nodes": 150, "total_links": 300,
               "total_documents": 10, "total_observations": 45, "pending_operations": 2,
               "failed_operations": 0, "last_memory_write_at": "2024-01-15T11:05:00Z",
               "nodes_by_fact_type": {"fact": 100, "observation": 20, "preference": 30}}
ZAMAN_SERISI_ORNEK = {"bank_id": "bank_id", "period": "7d", "trunc": "day",
                      "time_field": "created_at",
                      "buckets": [{"time": "time", "world": 0, "observation": 1, "experience": 6}]}
VARLIKLAR_ORNEK = {"items": [{"id": "123e4567-e89b-12d3-a456-426614174000",
                              "canonical_name": "John", "mention_count": 15,
                              "first_seen": "2024-01-15T10:30:00Z",
                              "last_seen": "2024-02-01T14:00:00Z"}],
                   "total": 150, "limit": 100, "offset": 0}
GRAF_ORNEK = {"nodes": [{"data": {"id": "uuid-1", "label": "Alice", "mentionCount": 12,
                                  "color": "#42a5f5"}}],
              "edges": [{"data": {"id": "uuid-1-uuid-2", "source": "uuid-1", "target": "uuid-2",
                                  "weight": 5, "linkType": "cooccurrence",
                                  "lastCooccurred": "2024-02-01T14:00:00Z"}}],
              "total_entities": 2, "total_edges": 1, "limit": 1000}
BELGELER_ORNEK = {"items": [{"id": "session_1", "bank_id": "user123", "content_hash": "abc123",
                             "memory_unit_count": 15, "text_length": 5420,
                             "tags": ["user_a", "session_123"],
                             "created_at": "2024-01-15T10:30:00Z",
                             "updated_at": "2024-01-15T10:30:00Z"}],
                  "total": 50, "limit": 100, "offset": 0}
PARCALAR_ORNEK = {"items": [{"chunk_id": "user123_session_1_0", "document_id": "session_1",
                             "bank_id": "user123", "chunk_index": 0,
                             "chunk_text": "This is the first chunk of the document...",
                             "created_at": "2024-01-15T10:30:00Z"}],
                  "total": 0, "limit": 6, "offset": 1}
ZIHIN_LISTE_ORNEK = {"items": [{"id": "id", "bank_id": "bank_id", "name": "name",
                                "content": "content", "source_query": "source_query",
                                "is_stale": True, "max_tokens": 0, "tags": ["tags"],
                                "created_at": "created_at",
                                "last_refreshed_at": "last_refreshed_at",
                                "trigger": {"mode": "full", "tags_match": "any",
                                            "fact_types": ["world"], "include_chunks": True}}],
                     "total": 5, "limit": 2, "offset": 7}
ZIHIN_TEK_ORNEK = {"id": "id", "bank_id": "bank_id", "name": "name", "content": "content",
                   "is_stale": True, "reflect_response": {"key": ""},
                   "trigger": {"mode": "full", "keep_trace": False}}
AGAC_ORNEK = {"roots": [{"id": "id", "kind": "folder", "name": "name",
                         "description": "description", "parent_id": "parent_id",
                         "managed": False, "is_stale": True, "children": [],
                         "mental_model_id": "mental_model_id", "tags": ["tags"],
                         "timestamp": "timestamp"}]}
ARAMA_ORNEK = {"results": [{"id": "id", "name": "name", "snippet": "snippet",
                            "score": 0.8008281904610115, "updated_at": "updated_at",
                            "mental_model_id": "mental_model_id"}], "total": 6}
SAYFA_ORNEK = {"id": "id", "name": "name", "type": "type", "description": "description",
               "tags": ["tags"], "timestamp": "timestamp", "body": "body", "markdown": "markdown"}
GOZLEM_LISTE_ORNEK = {"items": [{"id": "550e8400-e29b-41d4-a716-446655440000",
                                 "text": "Alice works at Google on the AI team",
                                 "type": "observation", "context": "Work conversation",
                                 "date": "2024-01-15T10:30:00Z",
                                 "metadata": {"source": "slack", "channel": "engineering"}}],
                      "total": 150, "limit": 100, "offset": 0}
KAPSAM_ORNEK = {"scopes": [{"count": 12, "tags": ["user:alice"]},
                           {"count": 4, "tags": ["user:alice", "project:apollo"]},
                           {"count": 2, "tags": []}]}
LLM_LISTE_ORNEK = {"bank_id": "bank_id", "total": 0, "limit": 6, "offset": 1,
                   "items": [{"id": "id", "trace_id": "trace_id", "span_id": "span_id",
                              "operation": "operation", "scope": "scope", "status": "status",
                              "provider": "provider", "model": "model", "input_tokens": 5,
                              "output_tokens": 2, "total_tokens": 9, "cached_tokens": 7,
                              "duration_ms": 5, "started_at": "started_at",
                              "ended_at": "ended_at", "llm_info": {"key": ""}}]}
DENETIM_LISTE_ORNEK = {"bank_id": "bank_id", "total": 0, "limit": 6, "offset": 1,
                       "items": [{"id": "id", "bank_id": "bank_id", "action": "action",
                                  "transport": "transport", "duration_ms": 5,
                                  "started_at": "started_at", "ended_at": "ended_at",
                                  "request": {"key": ""}, "response": {"key": ""},
                                  "metadata": {"key": ""}}]}
ISLEM_ORNEK = {"bank_id": "user123", "total": 150, "limit": 20, "offset": 0,
               "operations": [{"id": "550e8400-e29b-41d4-a716-446655440000",
                               "task_type": "retain", "status": "pending", "items_count": 5,
                               "created_at": "2024-01-15T10:30:00Z"}]}
YAPILANDIRMA_ORNEK = {"bank_id": "my-bank",
                      "config": {"retain_chunk_size": 3000,
                                 "retain_extraction_mode": "verbose"},
                      "overrides": {"retain_extraction_mode": "verbose"}}
RECALL_ORNEK = {"results": [{"id": "123e4567-e89b-12d3-a456-426614174000",
                             "text": "Alice works at Google on the AI team", "type": "world",
                             "context": "work info", "entities": ["Alice", "Google"],
                             "chunk_id": "456e7890-e12b-34d5-a678-901234567890",
                             "occurred_start": "2024-01-15T10:30:00Z",
                             "occurred_end": "2024-01-15T10:30:00Z"}],
                "trace": {"query": "What did Alice say about machine learning?",
                          "num_results": 1, "time_seconds": 0.123},
                "entities": {"Alice": {"entity_id": "123e4567-e89b-12d3-a456-426614174001",
                                       "canonical_name": "Alice", "observations": []}},
                "chunks": {}}

#: `audit-logs/stats` ve `llm-requests/stats` — DÜZELTME TURU 1 (I-1). Burada önce upstream'in
#: LİSTE uçlarının örnekleri (`DENETIM_LISTE_ORNEK`/`LLM_LISTE_ORNEK`, `{…, items:[…]}`) duruyordu:
#: ANALOJİYLE seçilmiş şekiller. Bu, aynı dosyanın CANLIDAN ölçtüğü `AUDIT_GOVDE` ile (kova
#: tabanlı, `items` YOK) çelişiyordu — tek dosyada aynı upstream yolu için İKİ farklı gerçek.
#: `AuditLogStatsResponse` ve `LLMRequestStatsResponse` şemalarının KENDİ `example:` blokları
#: ölçüldü ve buraya alındı; artık ilan edilen sınıf (2) DOĞRU.
DENETIM_ISTATISTIK_ORNEK = {"bank_id": "bank_id", "period": "period", "trunc": "trunc",
                            "start": "start",
                            "buckets": [{"time": "time", "total": 6, "actions": {"key": 0}}]}
LLM_ISTATISTIK_ORNEK = {"bank_id": "bank_id", "period": "period", "trunc": "trunc",
                        "start": "start",
                        "buckets": [{"time": "time", "total": 6, "statuses": {"key": 0},
                                     "tokens": {"input": 1, "output": 5, "total": 2,
                                                "cached": 5}}]}

# ------------------------------------------------------------------- SENTETİK GÖVDELER (sınıf 3)
#
# ÖLÇÜLDÜ Kİ YOK: tarihçe uçlarının upstream yanıt şeması literal `{}`tir — ne şema ne `example:`
# (`memories/{memory_id}/history` ve `mental-models/{mental_model_id}/history`, commit çapası
# dosya başlığında). Yani bu gövde ne canlıdan geldi ne kaynaktan türedi; iskeleti listeleme
# KARDEŞLERİNDEN alındı. DÜZELTME TURU 1 (I-2): adı `TARIHCE_ORNEK`ti ve sınıf-2 başlığı altında
# duruyordu — yani upstream şeması olduğunu İDDİA EDİYORDU. Ölçtüğü tek şey ZARF GEÇİŞİdir
# (vekil gövdeyi süzmüyor); şema iddiası TAŞIMAZ ve buradan bir alan adı okunamaz.
TARIHCE_SENTETIK = {"items": [{"id": "h1", "action": "created",
                               "at": "2024-01-15T10:30:00Z"}], "total": 1}

#: upstream parçası → gövde. `_Casus` en UZUN eşleşmeyi seçtiği için ön ek çakışmaları
#: (`/entities` ⊂ `/entities/graph`) doğru tarafa gider.
_CPUI_GOVDELER: dict[str, object] = {
    "/banks/B/stats": STATS_ORNEK,
    "/banks/B/stats/memories-timeseries": ZAMAN_SERISI_ORNEK,
    "/banks/B/entities": VARLIKLAR_ORNEK,
    "/banks/B/entities/graph": GRAF_ORNEK,
    "/banks/B/documents": BELGELER_ORNEK,
    "/banks/B/documents/d1/chunks": PARCALAR_ORNEK,
    "/banks/B/mental-models": ZIHIN_LISTE_ORNEK,
    "/banks/B/mental-models/z1": ZIHIN_TEK_ORNEK,
    "/banks/B/mental-models/z1/history": TARIHCE_SENTETIK,
    "/banks/B/knowledge-base/tree": AGAC_ORNEK,
    "/banks/B/knowledge-base/search": ARAMA_ORNEK,
    "/banks/B/knowledge-base/pages/p1": SAYFA_ORNEK,
    "/banks/B/memories/list": GOZLEM_LISTE_ORNEK,
    "/banks/B/memories/recall": RECALL_ORNEK,
    "/banks/B/observations/scopes": KAPSAM_ORNEK,
    "/banks/B/llm-requests": LLM_LISTE_ORNEK,
    "/banks/B/llm-requests/stats": LLM_ISTATISTIK_ORNEK,
    "/banks/B/audit-logs": DENETIM_LISTE_ORNEK,
    "/banks/B/audit-logs/stats": DENETIM_ISTATISTIK_ORNEK,
    "/banks/B/operations": ISLEM_ORNEK,
    "/banks/B/config": YAPILANDIRMA_ORNEK,
    "/banks/B/graph": GRAF_CANLI_GOVDE,
    "/banks/B/profile": PROFIL_GOVDE,
}
#: beklenen zarf gövdesi — yolun kendisinden değil, TABLODAN türetilir (tek kaynak).
CPUI_BEKLENEN = {yol: _CPUI_GOVDELER[parca] for yol, parca in CPUI}


def _cpui_esleme(**degistir) -> dict[str, bytes | str]:
    esleme: dict[str, bytes | str] = {p: json.dumps(g).encode()
                                      for p, g in _CPUI_GOVDELER.items()}
    esleme.update(degistir)
    return esleme


def _cpui(monkeypatch, tmp_path, **degistir) -> _Casus:
    return _kurulum(monkeypatch, tmp_path, esleme=_cpui_esleme(**degistir))


def _hafiza_rotalari() -> dict[str, set]:
    """`/api/hindsight*` rotaları → izin verilen fiiller. Kaynak metni değil ROTA TABLOSU."""
    return {r.path: set(getattr(r, "methods", set()) or set())
            for r in api.app.routes
            if str(getattr(r, "path", "")).startswith("/api/hindsight")}


# ------------------------------------------------------- J-A0. FIXTURE KAYITLARININ KENDİSİ

def test_denetim_istatistik_iki_kaydi_ayrismaz():
    """AYNI UPSTREAM YOLU, İKİ KAYIT — AYRIŞIRSA ÖTER (düzeltme turu 1, I-1'in kök nedeni).

    `audit-logs/stats` bu dosyada İKİ yerde yaşıyor: `AUDIT_GOVDE` (sınıf 1, A1'den 2026-09-02'de
    CANLI ölçüldü) ve `DENETIM_ISTATISTIK_ORNEK` (sınıf 2, upstream'in kendi `example:` bloğu).
    İki kayıt tek gerçeği anlatmalı; anlatmıyorsa BİRİ yanlıştır ve hangisi olduğu sessizce
    bilinemez. İnceleme tam bu boşlukta bir ANALOJİ yakaladı: yola upstream'in LİSTE örneği
    (`items:[…]`) bağlanmıştı ve canlı ölçümle (kova tabanlı) çelişiyordu.

    ALAN ADLARI kıyaslanır, DEĞERLER değil: canlı gövde bir bankanın gerçek sayılarını, örnek
    gövde upstream'in kurgusal sayılarını taşır — sayıların eşit olmasını beklemek yanlış
    ölçüm olurdu (`buckets` canlıda BOŞTU, o yüzden eleman şekli kıyaslanamaz)."""
    canli = set(json.loads(AUDIT_GOVDE))
    kaynak = set(DENETIM_ISTATISTIK_ORNEK)
    assert canli == kaynak, (
        f"aynı upstream yolunun iki kaydı ayrıştı — yalnız canlıda: {sorted(canli - kaynak)}; "
        f"yalnız kaynakta: {sorted(kaynak - canli)}")


def test_sentetik_govde_adiyla_beyanli():
    """SINIF ETİKETİ BİR İDDİADIR (I-2). Dosyanın kendi kuralı: sınıf-3 gövdelerin adında
    `SENTETIK` geçer. Tarihçe gövdesi `TARIHCE_ORNEK` adıyla sınıf-2 başlığının altındaydı —
    yani upstream şeması olduğunu İDDİA EDİYORDU; oysa iki tarihçe ucunun yanıt şeması da
    upstream'de literal `{}`tir (ne şema ne örnek). Kod bu alanları ADIYLA okumadığı için
    davranış riski yoktu; ihlal olan ETİKETTİ ve bu dosyanın kurucu dersi tam olarak etiketin
    doğruluğudur."""
    sentetikler = {ad for ad, deger in globals().items()
                   if ad.isupper() and deger is TARIHCE_SENTETIK}
    assert sentetikler == {"TARIHCE_SENTETIK"}, (
        f"sentetik gövde beyansız bir adla da yaşıyor: {sorted(sentetikler)}")


# ------------------------------------------------------------- J-A. KAYIT + YETKİ + FİİL

def test_her_hafiza_ucu_tabloda_kayitli():
    """TABLONUN KENDİSİ ÇİVİLİ. Bu dosyanın yirmiden fazla çivisi `CPUI`den besleniyor; tabloya
    girmemiş bir uç, o çivilerin HİÇBİRİNDEN geçmez ve dosya yine yeşil kalır — yani sessizce
    kapsamsız doğar. Rota tablosu ile bu dosyanın tablosu AYRIŞIRSA burada öter."""
    kayitli = set(_hafiza_rotalari())
    beklenen = {y.split("?")[0] for y in CPUI_YOLLAR} | {
        "/api/hindsight", "/api/hindsight/liste", "/api/hindsight/detay", RECALL}
    assert kayitli == beklenen, (
        f"rota tablosu ile çivi tablosu ayrıştı — yalnız rotada: {sorted(kayitli - beklenen)}; "
        f"yalnız çivide: {sorted(beklenen - kayitli)}")


def test_yazan_fiil_yalniz_recallda():
    """SALT-OKUNUR SÖZLEŞMESİNİN TEK KAYNAĞI. Uç uç `405` denemek yerine ROTA TABLOSU okunur:
    böylece yarın eklenen bir uç, çiviye dokunulmadan kapsama girer. `recall` BEYANLI
    İSTİSNAdır — durum değiştirmez, sorgu sınıfıdır (plan kapsam ruling'i, 2026-09-02) — ve
    istisna olduğu için TEK BAŞINA yazılır: listeye ikinci bir POST sızarsa burada öter."""
    for yol, fiiller in _hafiza_rotalari().items():
        yazanlar = fiiller - {"GET", "HEAD", "OPTIONS"}
        if yol == RECALL:
            assert yazanlar == {"POST"}, f"{yol}: beklenen yalnız POST, bulunan {sorted(fiiller)}"
        else:
            assert not yazanlar, f"{yol}: YAZAN fiil tanımlı ({sorted(yazanlar)}) — salt-okunur ihlali"


@pytest.mark.parametrize("yol", CPUI_YOLLAR)
def test_cpui_yalniz_get(monkeypatch, tmp_path, sandbox_state, yol):
    """Rota tablosu beyanının DAVRANIŞLA doğrulanması: GET dışı fiil 405."""
    _cpui(monkeypatch, tmp_path)
    cl = _client()
    for fiil in ("post", "put", "delete", "patch"):
        r = getattr(cl, fiil)(yol.split("?")[0])
        assert r.status_code == 405, f"{fiil.upper()} {yol} → {r.status_code}"


def test_recall_yalniz_post(monkeypatch, tmp_path, sandbox_state):
    _cpui(monkeypatch, tmp_path)
    cl = _client()
    for fiil in ("get", "put", "delete", "patch"):
        r = getattr(cl, fiil)(RECALL)
        assert r.status_code == 405, f"{fiil.upper()} {RECALL} → {r.status_code}"


@pytest.mark.parametrize("yol", CPUI_YOLLAR)
def test_cpui_auth_cagiriyor(monkeypatch, tmp_path, sandbox_state, yol):
    _cpui(monkeypatch, tmp_path)
    cagrildi: list = []
    monkeypatch.setattr(api, "_auth", lambda request: cagrildi.append(1))
    r = _client().get(yol)
    assert r.status_code == 200, r.text
    assert cagrildi == [1], f"`{yol}`: `_auth` çağrılmadı — hafıza yetkisiz açık"


def test_recall_auth_cagiriyor(monkeypatch, tmp_path, sandbox_state):
    """RECALL YAZMASA DA SORGULAR: yetkisiz bir çağıran bankanın içeriğini serbest metinle
    tarayabilirdi. Kapı GET uçlarıyla AYNI."""
    _cpui(monkeypatch, tmp_path)
    cagrildi: list = []
    monkeypatch.setattr(api, "_auth", lambda request: cagrildi.append(1))
    r = _client().post(RECALL, json={"bank": "B", "query": "alice"})
    assert r.status_code == 200, r.text
    assert cagrildi == [1]


@pytest.mark.parametrize("yol", CPUI_YOLLAR)
def test_cpui_auth_kapisi_cerezsiz_401(monkeypatch, tmp_path, sandbox_state, yol):
    _cpui(monkeypatch, tmp_path)
    monkeypatch.setattr(api, "DASH_TOKEN", "v375-pano-jetonu")
    monkeypatch.setattr(api.auth, "password_set", lambda: False)
    monkeypatch.setattr(api.auth, "verify_session", lambda c: False)
    cl = _client()
    assert cl.get(yol).status_code == 401, f"`{yol}`: token'sız istek geçti"
    assert cl.get(yol, headers={"x-meridian-token": "v375-pano-jetonu"}).status_code == 200


def test_recall_auth_kapisi_cerezsiz_401(monkeypatch, tmp_path, sandbox_state):
    _cpui(monkeypatch, tmp_path)
    monkeypatch.setattr(api, "DASH_TOKEN", "v375-pano-jetonu")
    monkeypatch.setattr(api.auth, "password_set", lambda: False)
    monkeypatch.setattr(api.auth, "verify_session", lambda c: False)
    cl = _client()
    govde = {"bank": "B", "query": "alice"}
    assert cl.post(RECALL, json=govde).status_code == 401
    assert cl.post(RECALL, json=govde,
                   headers={"x-meridian-token": "v375-pano-jetonu"}).status_code == 200


# --------------------------------------------------------- J-B. ÖLÇÜLEMEZLİK YUTULMAZ

@pytest.mark.parametrize("yol", CPUI_ZARFLI)
def test_cpui_env_yokken_200_ve_neden_dolu(monkeypatch, tmp_path, sandbox_state, yol):
    """Anahtar yokken (bu makinenin gerçek hâli) her uç 200 + `govde: None` + DOLU `neden`.
    Boş `{}` "banka boş" YALANI olurdu; 500 panoyu komple karartırdı."""
    _kurulum(monkeypatch, tmp_path, esleme=_cpui_esleme(), anahtar=None)
    r = _client().get(yol)
    assert r.status_code == 200, r.text
    g = r.json()
    assert set(g) == {"govde", "neden"}, sorted(g)
    assert g["govde"] is None, "anahtar yokken gövde UYDURULDU"
    assert _dolu(g["neden"]) and ".env" in g["neden"], g["neden"]


def test_ozet_env_yokken_iki_bacak_da_durust(monkeypatch, tmp_path, sandbox_state):
    _kurulum(monkeypatch, tmp_path, esleme=_cpui_esleme(), anahtar=None)
    g = _client().get("/api/hindsight/ozet?bank=B").json()
    assert set(g) == {"stats", "stats_neden", "zaman_serisi", "zaman_serisi_neden"}, sorted(g)
    assert g["stats"] is None and g["zaman_serisi"] is None
    assert _dolu(g["stats_neden"]) and _dolu(g["zaman_serisi_neden"])


def test_recall_env_yokken_200_ve_neden(monkeypatch, tmp_path, sandbox_state):
    casus = _kurulum(monkeypatch, tmp_path, esleme=_cpui_esleme(), anahtar=None)
    r = _client().post(RECALL, json={"bank": "B", "query": "alice"})
    assert r.status_code == 200, r.text
    g = r.json()
    assert g["govde"] is None and _dolu(g["neden"])
    assert casus.cagrilar == [], "anahtar yokken yine de upstream'e gidildi"


@pytest.mark.parametrize("yol", CPUI_ZARFLI)
def test_cpui_upstream_dusukken_200_ve_neden(monkeypatch, tmp_path, sandbox_state, yol):
    ariza = "127.0.0.1:8888 okunamadı (URLError: baglanti reddedildi)"
    _kurulum(monkeypatch, tmp_path,
             esleme={p: ariza for p in _CPUI_GOVDELER})
    r = _client().get(yol)
    assert r.status_code == 200, r.text
    g = r.json()
    assert g["govde"] is None, "arıza hâlinde sahte gövde üretildi"
    assert _dolu(g["neden"])


@pytest.mark.parametrize("yol", CPUI_ZARFLI)
def test_cpui_bozuk_json_yutulmaz(monkeypatch, tmp_path, sandbox_state, yol):
    """Upstream 200 dönüp gövdesi bozuksa: `govde: None` + DOLU neden. Sessiz `{}` panoda
    "kayıt yok" diye okunurdu; ölçülen ise "gövdeyi anlamadım"dır."""
    _kurulum(monkeypatch, tmp_path, esleme={p: b"{bu json degil" for p in _CPUI_GOVDELER})
    g = _client().get(yol).json()
    assert g["govde"] is None and _dolu(g["neden"])


@pytest.mark.parametrize("ham", [b"null", b""])
@pytest.mark.parametrize("yol", CPUI_ZARFLI)
def test_cpui_literal_null_govde_neden_uretir(monkeypatch, tmp_path, sandbox_state, yol, ham):
    """"TAM BİRİ DOLUDUR" BEYANININ KENAR DURUMU (düzeltme turu 1, M-6). Upstream literal `null`
    (ya da boş gövde) dönerse `json.loads` sessizce `None` verirdi ve zarf `{govde: None,
    neden: None}` olurdu — yani panonun "ÖLÇÜLEMEDİ" ile "BOŞ" ayrımı tam da bu dosyanın kurucu
    dersinin olduğu yerde kaybolurdu. `null` bu uçların HİÇBİRİNDE geçerli bir gövde değildir."""
    _kurulum(monkeypatch, tmp_path, esleme={p: ham for p in _CPUI_GOVDELER})
    g = _client().get(yol).json()
    assert g["govde"] is None
    assert _dolu(g["neden"]), "literal `null` gövde sessizce 'ölçüldü ama boş' diye geçti"


def test_ozet_bacaklari_birbirini_dusurmez(monkeypatch, tmp_path, sandbox_state):
    """İZOLASYON (`/api/hindsight`in banka-başına ayrımının kardeşi): `stats` düşerse zaman
    serisi HÂLÂ ölçülür. Bağlamak tek arızayı iki körlüğe çevirirdi."""
    casus = _cpui(monkeypatch, tmp_path,
                  **{"/banks/B/stats": "stats okunamadı (HTTPError: 500)"})
    g = _client().get("/api/hindsight/ozet?bank=B").json()
    assert g["stats"] is None and _dolu(g["stats_neden"])
    assert g["zaman_serisi"] == ZAMAN_SERISI_ORNEK, "bir bacağın arızası ötekini de düşürdü"
    assert g["zaman_serisi_neden"] is None
    assert len(casus.cagrilar) == 2, casus.url_ler()


def test_detay_tarihce_arizasi_kaydi_dusurmez(monkeypatch, tmp_path, sandbox_state):
    """`/detay` artık İKİ bacaklıdır (plan: "mevcut; history eklenir"). Tarihçe okunamazsa
    kaydın KENDİSİ hâlâ görünür — CP'nin memory-detail-panel'i tam olarak böyle davranır."""
    _kurulum(monkeypatch, tmp_path, esleme={
        "/memories/m1": json.dumps({"id": "m1", "text": "ilk"}).encode(),
        "/memories/m1/history": "history okunamadı (HTTPError: 500)"})
    g = _client().get("/api/hindsight/detay?bank=meridian-arsiv&kimlik=m1").json()
    assert g["oge"] == {"id": "m1", "text": "ilk"}
    assert g["neden"] is None, "tarihçe arızası kaydın gerekçesine bulaştı"
    assert g["tarihce"] is None, "ölçülemeyen tarihçe için sahte gövde üretildi"
    assert _dolu(g["tarihce_neden"])


# ---------------------------------------------------------------- J-C. ZARF AYNEN GEÇER

@pytest.mark.parametrize("yol", CPUI_ZARFLI)
def test_cpui_govde_aynen_gecer(monkeypatch, tmp_path, sandbox_state, yol):
    """AYNEN GEÇİŞ, ZARF SOYULMADAN. Dikkat: burada `items` dizisi ÇIKARILMAZ. Çıkarmak
    `total`/`limit`/`offset`i SESSİZCE düşürürdü ve pano "50 belgeden 20'si" diyemezdi —
    sayfalamanın gerçeği kaybolurdu (bedel yasası: gürültü azaltmanın bedeli ölçülür)."""
    _cpui(monkeypatch, tmp_path)
    r = _client().get(yol)
    assert r.status_code == 200, r.text
    g = r.json()
    assert set(g) == {"govde", "neden"}, sorted(g)
    assert g["neden"] is None
    assert g["govde"] == CPUI_BEKLENEN[yol], "upstream gövdesi SÜZÜLDÜ/yeniden adlandırıldı"


def test_ozet_iki_bacagi_da_aynen_gecer(monkeypatch, tmp_path, sandbox_state):
    _cpui(monkeypatch, tmp_path)
    g = _client().get("/api/hindsight/ozet?bank=B").json()
    assert g["stats"] == STATS_ORNEK
    assert g["zaman_serisi"] == ZAMAN_SERISI_ORNEK
    assert g["stats_neden"] is None and g["zaman_serisi_neden"] is None


@pytest.mark.parametrize("yol,parca", CPUI)
def test_cpui_upstream_yollari_kaynaktan_olculdu(monkeypatch, tmp_path, sandbox_state, yol, parca):
    """Uç, upstream'de GERÇEKTEN var olan yola gider. Sağ sütun `openapi.yaml` (v0.9.2) ve
    CP'nin kendi route.ts'lerinden okundu; uydurulmuş bir yol burada ısırır."""
    casus = _cpui(monkeypatch, tmp_path)
    _client().get(yol)
    tam = f"{api.HAFIZA_TABAN_URL}/v1/default{parca}"
    assert any(u.startswith(tam) for u in casus.url_ler()), \
        f"{yol} beklenen upstream yoluna gitmedi.\nbeklenen ön ek: {tam}\ngidilen: {casus.url_ler()}"


def test_gozlemler_upstreamde_observation_turunu_ister(monkeypatch, tmp_path, sandbox_state):
    """ÖLÇÜLDÜ, TAHMİN EDİLMEDİ: dataplane'de `GET /observations` YOKTUR (openapi v0.9.2'de o yol
    yalnız DELETE tanımlar). CP'nin observations-view'ı da bu yüzden `memories/list?type=observation`
    okur. Bizim `/gozlemler` aynı yere gider — "gözlem ucu var" varsayımı 404 üretirdi."""
    casus = _cpui(monkeypatch, tmp_path)
    _client().get("/api/hindsight/gozlemler?bank=B")
    url = casus.cagri("/memories/list")["url"]
    assert "type=observation" in url, url


def test_recall_govdesi_aynen_gecer(monkeypatch, tmp_path, sandbox_state):
    casus = _cpui(monkeypatch, tmp_path)
    r = _client().post(RECALL, json={"bank": "B", "query": "alice"})
    assert r.status_code == 200, r.text
    g = r.json()
    assert set(g) == {"govde", "neden"}, sorted(g)
    assert g["govde"] == RECALL_ORNEK and g["neden"] is None
    cagri = casus.cagri("/memories/recall")
    assert cagri["fiil"] == "POST", "recall GET ile denendi — upstream POST bekliyor"


# ------------------------------------------------------------------- J-D. SIR DUVARI

@pytest.mark.parametrize("yol", CPUI_YOLLAR)
def test_cpui_anahtar_govdeye_sizamaz(monkeypatch, tmp_path, sandbox_state, yol):
    """VAKUM DEĞİL: anahtar yanıtta yok AMA istekte `Authorization: Bearer` olarak gerçekten
    gönderilmiş. Gönderilmemiş bir sırrın yanıtta olmaması hiçbir şey kanıtlamaz."""
    casus = _cpui(monkeypatch, tmp_path)
    r = _client().get(yol)
    assert r.status_code == 200, r.text
    assert SAHTE_ANAHTAR not in r.text, "TENANT ANAHTARI PANOYA SIZDI"

    kimlikli = [c for c in casus.cagrilar if "/v1/" in c["url"]]
    assert kimlikli, "kimlikli hiçbir çağrı yok — sızıntı çivisi vakumda koşuyordu"
    for c in kimlikli:
        assert c["basliklar"].get("Authorization") == f"Bearer {SAHTE_ANAHTAR}", c["basliklar"]
        assert "X-API-Key" not in c["basliklar"], "`X-API-Key` ÖLÇÜLDÜ ve 401 veriyor"


def test_recall_anahtar_govdeye_sizamaz(monkeypatch, tmp_path, sandbox_state):
    casus = _cpui(monkeypatch, tmp_path)
    r = _client().post(RECALL, json={"bank": "B", "query": "alice"})
    assert SAHTE_ANAHTAR not in r.text
    cagri = casus.cagri("/memories/recall")
    assert cagri["basliklar"].get("Authorization") == f"Bearer {SAHTE_ANAHTAR}"
    assert cagri["sir"] == SAHTE_ANAHTAR, "POST bacağı maskeleyiciye sırrı VERMEDİ — ikinci hat kör"


@pytest.mark.parametrize("yol", CPUI_ZARFLI)
def test_cpui_istisna_metnindeki_anahtar_maskelenir(monkeypatch, tmp_path, sandbox_state, yol):
    sizan = f"401 — Authorization: Bearer {SAHTE_ANAHTAR} reddedildi"
    _kurulum(monkeypatch, tmp_path, esleme={p: sizan for p in _CPUI_GOVDELER})
    r = _client().get(yol)
    assert r.status_code == 200, r.text
    assert SAHTE_ANAHTAR not in r.text, "istisna metniyle taşınan anahtar panoya sızdı"
    assert "***" in r.text, "maskeleme uğruna gerekçe komple silinmiş — körlük açıldı"


@pytest.mark.parametrize("yol", CPUI_ZARFLI)
def test_cpui_upstream_govdesindeki_anahtar_maskelenir(monkeypatch, tmp_path, sandbox_state, yol):
    """Sır upstream'in KENDİ gövdesinden de gelebilir. Aynen-geçiş sözleşmesi maskeyi ISKALAMAZ —
    ve bu, 22 uçta tek tek değil TEK BOĞAZDA (`_hafiza_json`) sağlanmalı."""
    _kurulum(monkeypatch, tmp_path, esleme={
        p: json.dumps({"tenant_key": SAHTE_ANAHTAR}).encode() for p in _CPUI_GOVDELER})
    r = _client().get(yol)
    assert SAHTE_ANAHTAR not in r.text, "upstream gövdesindeki anahtar aynen panoya basıldı"


def test_recall_upstream_govdesindeki_anahtar_maskelenir(monkeypatch, tmp_path, sandbox_state):
    _cpui(monkeypatch, tmp_path,
          **{"/banks/B/memories/recall": json.dumps({"k": SAHTE_ANAHTAR}).encode()})
    r = _client().post(RECALL, json={"bank": "B", "query": "alice"})
    assert SAHTE_ANAHTAR not in r.text


# ------------------------------------------------- J-E. PARAMETRE SINIRLAMA (SUNUCUDA)

@pytest.mark.parametrize("yol,parca", CPUI_LIMITLI)
def test_cpui_limit_tavani_sunucuda(monkeypatch, tmp_path, sandbox_state, yol, parca):
    """`limit=9999` upstream'e GİTMEZ. `/liste` için kapatılan sınıf, on ucun daha açık kalmasıyla
    geri gelirdi: her listeleyen uç panonun yükünü ve Hindsight sorgusunu sınırsız büyütebilir."""
    casus = _cpui(monkeypatch, tmp_path)
    _client().get(f"{yol}&limit=9999")
    url = casus.cagri(parca)["url"]
    assert "9999" not in url, f"kırpılmamış limit upstream'e gitti: {url}"
    assert f"limit={_beklenen_tavan(parca)}" in url, url


@pytest.mark.parametrize("yol,parca", CPUI_LIMITLI)
def test_gonderilen_limit_upstream_maksimumunu_asmaz(monkeypatch, tmp_path, sandbox_state,
                                                     yol, parca):
    """ÖLÇÜLMEMİŞ 422 SINIFI (düzeltme turu 1). Sözleşme tavanımız 200'dü ve HER listeleyen uca
    aynen gidiyordu; oysa upstream `limit.maximum` uca göre değişir ve İKİ uçta 200'ün ALTINDAdır:
    `/operations` 100, `/knowledge-base/search` 50. Yani `/islemler` HİÇBİR parametre verilmeden
    (varsayılan limit = tavan) 422 alıyordu ve pano bunu "hafıza okunamadı" diye — yani ALTYAPI
    ARIZASI gibi — gösterirdi. Ölçüm `UPSTREAM_LIMIT_MAKSIMUMU`da; kod kendi tavanını ondan
    TÜRETMEZ, iki kayıt ayrışırsa burada öter."""
    casus = _cpui(monkeypatch, tmp_path)
    ust = UPSTREAM_LIMIT_MAKSIMUMU.get(_uc_kuyrugu(parca))
    if ust is None:
        pytest.skip(f"{parca}: upstream şemasında `maximum` yok — kıyaslanacak sınır da yok")
    for sorgu in ("", "&limit=9999"):
        casus.cagrilar.clear()
        _client().get(f"{yol}{sorgu}")
        url = casus.cagri(parca)["url"]
        assert _gonderilen_limit(url) <= ust, (
            f"{yol}{sorgu}: upstream sınırı {ust} iken {url} gitti — 422 üretir ve `neden`e "
            f"altyapı arızası gibi yazılır")


@pytest.mark.parametrize("yol,parca", CPUI_LIMITLI)
def test_cpui_bozuk_limit_422_uretmez(monkeypatch, tmp_path, sandbox_state, yol, parca):
    """Parametreler `str` tipli olmalı: `int` yazmak FastAPI'ye 422 ürettirir ve pano o cevabı
    gövde sanıp kararır (`bank` için kapatılan sınıfın kardeşi)."""
    casus = _cpui(monkeypatch, tmp_path)
    r = _client().get(f"{yol}&limit=abc&offset=xyz")
    assert r.status_code == 200, f"{yol}: {r.status_code} — pano karardı"
    url = casus.cagri(parca)["url"]
    assert "limit=abc" not in url and "offset=xyz" not in url, url


@pytest.mark.parametrize("sorgu,ad", [
    ("state=silinmis", "state"),
    ("consolidation_state=belirsiz", "consolidation_state"),
    # `tags` BİLEREK VERİLİYOR (düzeltme turu 1, I-3): `tags_match=hepsi` tek başına
    # gönderildiğinde kod onu `_hafiza_sozluk`a HİÇ sormadan düşürür (etiket-bağlama kuralı) —
    # yani vaka VAKUMDA yeşildi ve sözlük süzmesini ölçtüğünü sanıyordu. Etiketle birlikte
    # gönderildiğinde ölçülen şey gerçekten sözlüktür.
    ("tags=a,b&tags_match=hepsi", "tags_match"),
])
def test_liste_taninmayan_enum_upstreame_sizmaz(monkeypatch, tmp_path, sandbox_state, sorgu, ad):
    """ÖLÇÜLEN ENUM'LAR (openapi v0.9.2 + CP'nin kendi doğrulaması): `state` ∈ {valid,
    invalidated} · `consolidation_state` ∈ {failed, pending, done} · `tags_match` ∈ {any, all,
    any_strict, all_strict, exact}. Tanınmayan değer upstream'e GÖNDERİLMEZ: gönderilse 422
    döner ve pano "hafıza okunamadı" derdi — oysa arıza istemcinin verdiği kirli girdidir."""
    casus = _cpui(monkeypatch, tmp_path, **{"/memories/list": b'{"items": []}'})
    r = _client().get(f"/api/hindsight/liste?bank=B&{sorgu}")
    assert r.status_code == 200, r.text
    url = casus.cagri("/memories/list")["url"]
    assert f"{ad}=" not in url, f"tanınmayan {ad} değeri upstream'e sızdı: {url}"


@pytest.mark.parametrize("sorgu,beklenen", [
    ("state=valid", "state=valid"),
    ("consolidation_state=pending", "consolidation_state=pending"),
    ("fact_type=world", "type=world"),
    ("q=alice", "q=alice"),
    ("document_id=d9", "document_id=d9"),
    ("entity_id=e9", "entity_id=e9"),
    ("tags=a,b&tags_match=all", "tags=a&tags=b&tags_match=all"),
])
def test_liste_taninan_filtreler_upstreame_gecer(monkeypatch, tmp_path, sandbox_state,
                                                 sorgu, beklenen):
    """Süzme bir TAVAN değil bir SÖZLÜKTÜR: tanınan değer AYNEN geçer, yoksa filtre hiç
    çalışmazdı. `fact_type` → upstream'de `type` (CP'nin de kabul ettiği takma ad);
    `tags` virgülle verilir ve TEKRARLANAN parametreye açılır (upstream dizi bekliyor)."""
    casus = _cpui(monkeypatch, tmp_path, **{"/memories/list": b'{"items": []}'})
    _client().get(f"/api/hindsight/liste?bank=B&{sorgu}")
    url = casus.cagri("/memories/list")["url"]
    for parca in beklenen.split("&"):
        assert parca in url, f"{sorgu!r} → upstream'de {parca!r} yok: {url}"


@pytest.mark.parametrize("yol,parca", CPUI_ETIKETLI)
def test_etiketliyken_taninan_tags_match_upstreame_gecer(monkeypatch, tmp_path, sandbox_state,
                                                         yol, parca):
    """POZİTİF KAPAK (düzeltme turu 1, I-3). `tags_match`in bu üç uçta HİÇBİR pozitif çivisi
    yoktu: kod onu her zaman düşürseydi de dosya yeşil kalırdı — ve etiket eşleşmesi sessizce
    upstream varsayılanına (`any`) düşerdi, yani "hepsi bu etiketlerde" isteyen bir görünüm
    "herhangi biri" sonucunu alırdı."""
    casus = _cpui(monkeypatch, tmp_path)
    _client().get(f"{yol}&tags=a,b&tags_match=all")
    url = casus.cagri(parca)["url"]
    assert "tags=a" in url and "tags=b" in url, f"etiketler tekrarlanan parametreye açılmadı: {url}"
    assert "tags_match=all" in url, f"tanınan tags_match upstream'e geçmedi: {url}"


@pytest.mark.parametrize("yol,parca", CPUI_ETIKETLI)
def test_etiketliyken_taninmayan_tags_match_dusurulur(monkeypatch, tmp_path, sandbox_state,
                                                      yol, parca):
    """NEGATİF KAPAK — ve VAKUMSUZ olanı budur: etiket VERİLİ olduğu için `tags_match`i düşüren
    şey etiket-bağlama kuralı değil SÖZLÜKTÜR. Etiketlerin kendisi yine de gitmeli: tanınmayan
    eşleşme kipi yüzünden filtrenin TAMAMINI düşürmek, kullanıcının sorduğundan başka bir
    kümeyi göstermek olurdu."""
    casus = _cpui(monkeypatch, tmp_path)
    _client().get(f"{yol}&tags=a,b&tags_match=hepsi")
    url = casus.cagri(parca)["url"]
    assert "tags_match=" not in url, f"tanınmayan tags_match upstream'e sızdı: {url}"
    assert "tags=a" in url and "tags=b" in url, f"etiketler de düştü: {url}"


@pytest.mark.parametrize("yol,parca", CPUI_ETIKETLI)
def test_etiketsizken_tags_match_hic_gonderilmez(monkeypatch, tmp_path, sandbox_state,
                                                 yol, parca):
    """ETİKET-BAĞLAMA KURALI, AYRI ÖLÇÜLÜR (CP'nin `documents/route.ts`te gerekçelendirdiği
    davranış): `tags_match` tek başına gönderilirse FİLTRESİZ bir listelemede upstream'in kendi
    varsayılanını sessizce ezerdi. Bu kural sözlük süzmesinden BAŞKA bir kuraldır; ikisini tek
    çiviye yüklemek, birinin ötekini maskelemesine yol açtı (I-3'ün kök nedeni)."""
    casus = _cpui(monkeypatch, tmp_path)
    _client().get(f"{yol}&tags_match=all")
    url = casus.cagri(parca)["url"]
    assert "tags_match=" not in url, f"etiketsiz tags_match upstream'e gitti: {url}"


def test_liste_scope_upstreame_gitmez(monkeypatch, tmp_path, sandbox_state):
    """`scope` ÖLÇÜLDÜ VE `list_memories`TE YOKTUR (brief kalemi; parametre listesi dosya
    başlığında, commit çapasıyla). Brief'te adı geçen bir filtre sessizce düşürülemez — ama
    var olmayan bir parametreyi göndermek de 422 üretirdi. Bu çivi düşürmenin KAYDIdır:
    `/liste`ye `scope` eklenirse burada öter ve ekleyen kişi önce ölçmek zorunda kalır.
    (`scope` upstream'de yalnız `list_llm_requests`tedir ve `/llm-istekleri` onu geçirir.)"""
    casus = _cpui(monkeypatch, tmp_path)
    r = _client().get("/api/hindsight/liste?bank=B&scope=reflect")
    assert r.status_code == 200, r.text
    url = casus.cagri("/memories/list")["url"]
    assert "scope=" not in url, f"upstream'de olmayan `scope` gönderildi: {url}"


@pytest.mark.parametrize("yol,parca", [
    ("/api/hindsight/zihin-modelleri?bank=B", "/banks/B/mental-models"),
    ("/api/hindsight/zihin-modeli?bank=B&kimlik=z1", "/banks/B/mental-models/z1"),
])
def test_zihin_detail_taninmayan_deger_upstreame_sizmaz(monkeypatch, tmp_path, sandbox_state,
                                                        yol, parca):
    """ÖLÇÜLDÜ (düzeltme turu 1, M-1): `detail` upstream'de GERÇEK bir enum'dur —
    {metadata, content, full}, varsayılan `full` — ve iki uçta birden. Ham geçirilen tanınmayan
    bir değer 422 üretir; bu, "tanımadığını gönderme" ilkesinin kapatmak için var olduğu sınıfın
    ta kendisiydi ve tam da o ilkenin beyan edildiği blokta açık kalmıştı. Tanınan değerin
    geçtiği de ölçülür — yoksa "hep düşür" de yeşil kalırdı."""
    casus = _cpui(monkeypatch, tmp_path)
    _client().get(f"{yol}&detail=hersey")
    assert "detail=" not in casus.cagri(parca)["url"], casus.cagri(parca)["url"]

    casus.cagrilar.clear()
    _client().get(f"{yol}&detail=metadata")
    assert "detail=metadata" in casus.cagri(parca)["url"], casus.cagri(parca)["url"]


@pytest.mark.parametrize("yol,ad,kotu,varsayilan", [
    ("/api/hindsight/ozet?bank=B", "period", "asirlik", "7d"),
    ("/api/hindsight/ozet?bank=B", "time_field", "ne_zamansa", "created_at"),
    ("/api/hindsight/llm-istatistik?bank=B", "period", "asirlik", "7d"),
    ("/api/hindsight/denetim-istatistik?bank=B", "period", "asirlik", "7d"),
])
def test_taninmayan_period_beyanli_varsayilana_oturur(monkeypatch, tmp_path, sandbox_state,
                                                      yol, ad, kotu, varsayilan):
    """ÖLÇÜLEN SÖZLÜKLER: timeseries `period` ∈ {1h,12h,1d,7d,30d,90d}, `time_field` ∈
    {created_at, mentioned_at, occurred_start}; llm/audit stats `period` ∈ {1d,7d,30d}
    (hepsi openapi v0.9.2 açıklamalarından). Tanınmayan değer sessizce ATILMAZ — beyan edilmiş
    varsayılana oturur, yani pano "7 gün" der ve GERÇEKTEN 7 gün görür."""
    casus = _cpui(monkeypatch, tmp_path)
    r = _client().get(f"{yol}&{ad}={kotu}")
    assert r.status_code == 200, r.text
    ilgili = [u for u in casus.url_ler() if f"{ad}=" in u]
    assert ilgili, f"{ad} hiç gönderilmedi: {casus.url_ler()}"
    for url in ilgili:
        assert kotu not in url, f"tanınmayan {ad} upstream'e sızdı: {url}"
        assert f"{ad}={varsayilan}" in url, url


# ------------------------------------- J-K. GÖREV 6-A: bellek-graf'a ÖZGÜ (tabloya sığmayan) ----
#
# bellek-graf/profil GENEL CPUI/CPUI_LIMITLI/CPUI_ETIKETLI parametrik çivilerinden zaten geçer
# (yetki, ölçülemezlik, zarf-aynen-geçiş, sır duvarı, limit tavanı, tags/tags_match, yol
# enjeksiyonu, state defterine yazmama — J-A..J-G). Burada yalnız bu uca ÖZGÜ, tabloya sığmayan
# üç davranış çivilenir.

def test_bellek_graf_limitsiz_istekte_cp_varsayilanini_kullanir(monkeypatch, tmp_path,
                                                                sandbox_state):
    """R7 (brief): CP varsayılanı (200, ana sayfa çağrısı) > openapi'nin KENDİ varsayılanı
    (1000) > parametre hiç gönderilmez. `limit` hiç verilmezse upstream'e giden değer 200'dür —
    openapi'nin 1000'ini aynen taşımak, CP'nin gerçekte hiç istemediği bir yükü upstream'e
    bindirirdi (`limit.maximum` ÖLÇÜLDÜ VE YOKTUR, bu yüzden `UPSTREAM_LIMIT_MAKSIMUMU`da yok —
    kıyas çivisi bu ucu atlar, `test_gonderilen_limit_upstream_maksimumunu_asmaz` skip eder)."""
    casus = _cpui(monkeypatch, tmp_path)
    _client().get("/api/hindsight/bellek-graf?bank=B")
    url = casus.cagri("/banks/B/graph")["url"]
    assert "limit=200" in url, url
    assert "limit=1000" not in url, url


def test_bellek_graf_type_upstreame_gecer(monkeypatch, tmp_path, sandbox_state):
    """`type` (world/experience/observation) HAM geçer — openapi'de bu alan enum DEĞİLDİR
    (`nullable: true, type: string`), yani süzülmez, aynen taşınır. `q` aynı çağrıda geçtiği
    için birlikte ölçülür (ikisi de basit geçiş, ayrı testler tekrar olurdu)."""
    casus = _cpui(monkeypatch, tmp_path)
    _client().get("/api/hindsight/bellek-graf?bank=B&type=world&q=alice")
    url = casus.cagri("/banks/B/graph")["url"]
    assert "type=world" in url and "q=alice" in url, url


def test_bellek_graf_document_id_kapsam_disi(monkeypatch, tmp_path, sandbox_state):
    """`document_id`/`chunk_id` upstream `/graph` şemasında VAR ama brief'in ölçtüğü CP ana
    sayfa kümesi (`type`/`limit`/`q`/`tags`/`tags_match`) DEĞİL — bu uçta karşılığı YOK ve
    FastAPI tanımadığı sorgu parametresini sessizce yok sayar; upstream'e hiç gitmemeleri
    kapsam kararının (brief) DAVRANIŞLA doğrulanmasıdır."""
    casus = _cpui(monkeypatch, tmp_path)
    _client().get("/api/hindsight/bellek-graf?bank=B&document_id=d1&chunk_id=c1")
    url = casus.cagri("/banks/B/graph")["url"]
    assert "document_id=" not in url and "chunk_id=" not in url, url


# ----------------------------------------------------- J-F. EKSİK PARAMETRE 400 DEĞİL

@pytest.mark.parametrize("yol", [y.split("?")[0] for y in CPUI_ZARFLI])
def test_cpui_banksiz_400_degil_neden(monkeypatch, tmp_path, sandbox_state, yol):
    casus = _cpui(monkeypatch, tmp_path)
    r = _client().get(yol)
    assert r.status_code == 200, f"eksik parametre {r.status_code} üretti — pano karardı"
    g = r.json()
    assert g["govde"] is None
    assert _dolu(g["neden"]) and "bank" in g["neden"], g["neden"]
    assert casus.cagrilar == [], "parametre eksikken yine de upstream'e gidildi"


def test_ozet_banksiz_400_degil_neden(monkeypatch, tmp_path, sandbox_state):
    casus = _cpui(monkeypatch, tmp_path)
    r = _client().get("/api/hindsight/ozet")
    assert r.status_code == 200
    g = r.json()
    assert g["stats"] is None and g["zaman_serisi"] is None
    assert _dolu(g["stats_neden"]) and _dolu(g["zaman_serisi_neden"])
    assert casus.cagrilar == []


@pytest.mark.parametrize("yol,ad", CPUI_IKI_KIMLIKLI)
def test_cpui_ikinci_kimlik_eksikse_neden(monkeypatch, tmp_path, sandbox_state, yol, ad):
    """BOŞ DİZGE DE EKSİKTİR: `?belge=` bir değer DEĞİLDİR ve upstream'e `/documents//chunks`
    diye giderdi."""
    casus = _cpui(monkeypatch, tmp_path)
    for sorgu in ("", f"&{ad}="):
        r = _client().get(f"{yol}{sorgu}")
        assert r.status_code == 200, f"{yol}{sorgu}: {r.status_code}"
        g = r.json()
        assert g["govde"] is None
        assert _dolu(g["neden"]) and ad in g["neden"], g["neden"]
    assert casus.cagrilar == [], "kimlik eksikken upstream'e gidildi"


@pytest.mark.parametrize("govde", [{}, {"bank": "B"}, {"query": "alice"},
                                   {"bank": "B", "query": ""}, {"bank": "", "query": "alice"}])
def test_recall_eksik_parametre_400_degil(monkeypatch, tmp_path, sandbox_state, govde):
    casus = _cpui(monkeypatch, tmp_path)
    r = _client().post(RECALL, json=govde)
    assert r.status_code == 200, f"{govde!r}: {r.status_code} — pano karardı"
    g = r.json()
    assert g["govde"] is None and _dolu(g["neden"])
    assert casus.cagrilar == [], "eksik parametreyle upstream'e gidildi"


def test_recall_bozuk_json_govde_422_uretmez(monkeypatch, tmp_path, sandbox_state):
    """FastAPI'nin varsayılanı ayrıştırılamayan gövdede 422'dir ve pano o cevabı gövde sanıp
    KARARIR. GET tarafında kapatılan sınıf POST tarafında açık kalamaz."""
    casus = _cpui(monkeypatch, tmp_path)
    r = _client().post(RECALL, content=b"{bu json degil",
                       headers={"content-type": "application/json"})
    assert r.status_code == 200, f"{r.status_code} — pano karardı: {r.text[:200]}"
    g = r.json()
    assert g["govde"] is None and _dolu(g["neden"])
    assert casus.cagrilar == []


def test_recall_govde_sozluk_degilse_neden(monkeypatch, tmp_path, sandbox_state):
    """JSON geçerli ama sözlük değil (`[1,2]`): "alan okuyamadım" ölçümdür, çökme değil."""
    casus = _cpui(monkeypatch, tmp_path)
    r = _client().post(RECALL, json=[1, 2])
    assert r.status_code == 200, r.text
    assert _dolu(r.json()["neden"])
    assert casus.cagrilar == []


# ---------------------------------------------------------------- J-G. ENJEKSİYON

@pytest.mark.parametrize("yol", CPUI_YOLLAR)
def test_cpui_bank_yol_enjeksiyonuna_kapali(monkeypatch, tmp_path, sandbox_state, yol):
    """`bank` KULLANICI GİRDİSİDİR ve 22 uçta upstream PATH'ine giriyor. Tek bir uçta unutulan
    kaçırma, `../../` ile YAZAN bir uca gidilmesine yeter — salt-okunur sözleşmesi istemcinin
    insafına kalırdı. Kaçırma bu yüzden çağıranın disiplinine değil TEK YARDIMCIYA bağlıdır."""
    import urllib.parse
    kotu = "../../../v1/default/banks"
    casus = _cpui(monkeypatch, tmp_path,
                  **{"/v1/default/banks": b'{"banks": []}'})
    bozuk = yol.replace("bank=B", f"bank={urllib.parse.quote(kotu, safe='')}")
    _client().get(bozuk)

    # KAPAK (düzeltme turu 1, M-4): döngü çağrı listesi üzerinde; HİÇ çağrı yapılmasaydı bu çivi
    # sessizce yeşil olurdu. Kardeşi (`…ikinci_kimlik…`) bu kapağı taşıyordu, bu taşımıyordu.
    assert casus.cagrilar, "bank verildiği hâlde upstream'e hiç gidilmedi — çivi vakumda koştu"
    kok = f"{api.HAFIZA_TABAN_URL}/v1/default/banks/"
    for url in casus.url_ler():
        kimlik = url[len(kok):].split("/")[0].split("?")[0]
        for ham in ("..", " ", "?", "#"):
            assert ham not in kimlik, f"kaçırılmamış {ham!r} upstream PATH'ine girdi: {url}"


@pytest.mark.parametrize("yol,ad", CPUI_IKI_KIMLIKLI)
def test_cpui_ikinci_kimlik_yol_enjeksiyonuna_kapali(monkeypatch, tmp_path, sandbox_state,
                                                     yol, ad):
    import urllib.parse
    casus = _cpui(monkeypatch, tmp_path, **{"/v1/default/banks/B/": b"{}"})
    kotu = urllib.parse.quote("../../../stats", safe="")
    _client().get(f"{yol}&{ad}={kotu}")
    assert casus.cagrilar, "kimlik verildiği hâlde upstream'e hiç gidilmedi"
    for url in casus.url_ler():
        kuyruk = url.split(f"{api.HAFIZA_TABAN_URL}/v1/default/banks/B", 1)[1]
        assert ".." not in kuyruk, f"kaçırılmamış kimlik upstream PATH'ine girdi: {url}"


@pytest.mark.parametrize("yol,parca,ad", [
    ("/api/hindsight/liste?bank=B", "/memories/list", "q"),
    ("/api/hindsight/bilgi-arama?bank=B", "/knowledge-base/search", "q"),
    ("/api/hindsight/belgeler?bank=B", "/documents", "q"),
    ("/api/hindsight/denetim?bank=B", "/audit-logs", "action"),
    ("/api/hindsight/llm-istekleri?bank=B", "/llm-requests", "operation"),
])
def test_sorgu_degeri_ikinci_parametre_uretemez(monkeypatch, tmp_path, sandbox_state,
                                                yol, parca, ad):
    """SORGU DİZESİ ENJEKSİYONU — yol enjeksiyonunun az konuşulan kardeşi. `q=x&limit=99999`
    ham olarak yapıştırılırsa upstream'de İKİNCİ bir `limit` doğar ve sunucuda kurulan tavan
    sessizce delinir. Değerler kodlanmalı: `&` → `%26`."""
    import urllib.parse
    casus = _cpui(monkeypatch, tmp_path, **{"/memories/list": b'{"items": []}'})
    kotu = urllib.parse.quote("x&limit=99999", safe="")
    _client().get(f"{yol}&{ad}={kotu}")
    url = casus.cagri(parca)["url"]
    assert "limit=99999" not in url, f"sorgu değeri ikinci bir parametre üretti: {url}"
    assert "%26" in url, f"`&` kodlanmadı — değer ham geçti: {url}"


# ------------------------------------------- J-H. RECALL: SORGU SINIFI, SÜZÜLMÜŞ GEÇİŞ

def test_recall_yalniz_beyanli_alanlari_gecirir(monkeypatch, tmp_path, sandbox_state):
    """SÜZÜLMÜŞ GEÇİŞ (plan ruling'i). Recall gövdesi ISTEMCIDEN gelir ve upstream'e AYNEN
    verilirse, upstream'in yarın ekleyeceği YAZAN bir alan bizim salt-okunur sözleşmemizi
    istemcinin insafına bırakır. Bu yüzden geçiş bir BEYAZ LİSTEdir; liste openapi v0.9.2
    `RecallRequest` şemasından okundu ve o şemadaki YAZAN hiçbir alan yoktur."""
    casus = _cpui(monkeypatch, tmp_path)
    r = _client().post(RECALL, json={
        "bank": "B", "query": "alice", "types": ["world"], "budget": "mid",
        "max_tokens": 512, "trace": True, "tags": ["user_a"], "tags_match": "any",
        "prefer_observations": True,
        # kaçak yolcular — hiçbiri upstream gövdesine GİRMEMELİ
        "retain": {"text": "gizlice yaz"}, "state": "invalidated", "bank_id": "baska-banka",
        "updates": {"retain_extraction_mode": "custom"}, "reason": "x"})
    assert r.status_code == 200, r.text

    giden = casus.cagri("/memories/recall")["govde"]
    assert isinstance(giden, (bytes, bytearray)), f"gövde bytes olarak gitmedi: {type(giden)}"
    coz = json.loads(giden.decode())
    assert set(coz) <= {"query", "types", "budget", "max_tokens", "trace", "tags", "tags_match",
                        "prefer_observations", "query_timestamp"}, sorted(coz)
    assert coz["query"] == "alice" and coz["types"] == ["world"]
    for kacak in ("retain", "state", "bank_id", "updates", "reason"):
        assert kacak not in coz, f"beyaz liste dışı `{kacak}` upstream gövdesine sızdı"


def test_recall_bank_yol_parametresidir_govde_alani_degil(monkeypatch, tmp_path, sandbox_state):
    """`bank` YOL'a gider, gövdeye DEĞİL (CP'nin kendi recall route'u da böyle yapar). Gövdeye
    de konsaydı iki kaynak doğar ve hangi bankanın okunduğu belirsizleşirdi."""
    casus = _cpui(monkeypatch, tmp_path)
    _client().post(RECALL, json={"bank": "B", "query": "alice", "bank_id": "baska"})
    cagri = casus.cagri("/memories/recall")
    assert cagri["url"].endswith("/v1/default/banks/B/memories/recall"), cagri["url"]


def test_recall_max_tokens_tavani_sunucuda(monkeypatch, tmp_path, sandbox_state):
    """RECALL'IN "LIMIT"İ `max_tokens`TIR (openapi v0.9.2: `RecallRequest.limit` alanı YOKTUR —
    plan metnindeki "limit" bu alandır). Tavan upstream'in KENDİ varsayılanıdır (4096): ölçülmemiş
    daha yüksek bir tavan uydurmak yasak. `max_tokens=999999` bir LLM çağrısını ve pano gecikmesini
    sınırsız büyütürdü."""
    casus = _cpui(monkeypatch, tmp_path)
    _client().post(RECALL, json={"bank": "B", "query": "alice", "max_tokens": 999999})
    coz = json.loads(casus.cagri("/memories/recall")["govde"].decode())
    assert coz["max_tokens"] == api.HAFIZA_RECALL_TOKEN_TAVANI == 4096, coz


def test_recall_bozuk_max_tokens_422_degil_varsayilana_oturur(monkeypatch, tmp_path,
                                                              sandbox_state):
    casus = _cpui(monkeypatch, tmp_path)
    r = _client().post(RECALL, json={"bank": "B", "query": "alice", "max_tokens": "cok"})
    assert r.status_code == 200, r.text
    coz = json.loads(casus.cagri("/memories/recall")["govde"].decode())
    assert coz["max_tokens"] == api.HAFIZA_RECALL_TOKEN_TAVANI


def test_recall_json_baslikli_gider(monkeypatch, tmp_path, sandbox_state):
    casus = _cpui(monkeypatch, tmp_path)
    _client().post(RECALL, json={"bank": "B", "query": "alice"})
    basliklar = casus.cagri("/memories/recall")["basliklar"]
    assert basliklar.get("Content-Type") == "application/json", basliklar


# ---------------------------------------------------- J-I. ZAMAN AŞIMI + TEK KAYNAK

def test_iki_bacak_da_ortak_cekirdege_delege_eder(monkeypatch, tmp_path, sandbox_state):
    """KOPYA EMEKLİ EDİLDİ (düzeltme turu 1, I-4). `_hafiza_post` `_kapi_getir`in satır-satır
    kopyasıydı: aynı `try/urlopen(timeout=…)`, aynı geniş yakalama, aynı maskeleme, hatta aynı
    yorum. Kopya kalsaydı v361 tarafındaki her düzeltme (yeniden deneme, `Retry-After`, başlık
    politikası) POST bacağında SESSİZCE eksik kalırdı.

    ÇÖZÜM DOSYANIN KENDİ EMSALİ: `_env_anahtari` çıkarımında ortak gövde çekirdeğe alınmış,
    `_kapi_admin_anahtari` SARMALAYICI olarak kalmıştı. Burada da öyle — `_kapi_istek` çekirdek,
    iki eski ad sarmalayıcı, imzalar değişmedi.

    ESKİ ÇİVİNİN YERİNİ ALIR. Önce "iki kopya aynı zaman aşımını okuyor mu" ölçülüyordu; tek
    çekirdekte o soru SORULAMAZ hâle geldi. Ölçülmesi gereken yeni şey delegasyonun KENDİSİdir:
    sarmalayıcı çekirdekten koparılırsa (gövdesi geri kopyalanırsa) burada öter."""
    cagrilar: list = []

    def _sahte_cekirdek(url, basliklar, sir, *, govde=None, yontem="GET"):
        cagrilar.append({"url": url, "govde": govde, "yontem": yontem})
        return b'{"ok": true}', None

    monkeypatch.setattr(api, "_kapi_istek", _sahte_cekirdek)
    assert GERCEK_KAPI_GETIR("http://x/1", {"A": "b"}, "s") == (b'{"ok": true}', None)
    assert GERCEK_HAFIZA_POST("http://x/2", {"A": "b"}, "s", b'{"q":1}') == (b'{"ok": true}', None)
    assert cagrilar == [
        {"url": "http://x/1", "govde": None, "yontem": "GET"},
        {"url": "http://x/2", "govde": b'{"q":1}', "yontem": "POST"},
    ], f"sarmalayıcı çekirdeğe delege etmedi (kopya geri geldi): {cagrilar}"


def test_post_bacagi_ayni_zaman_asimini_zorlar(monkeypatch, tmp_path, sandbox_state):
    """DAVRANIŞ ÇİVİSİ (artık ayrışma çivisi DEĞİL): POST bacağı `urlopen`e GERÇEKTEN bir
    `timeout` geçiriyor mu, ve o değer sözleşmenin beyan ettiği sabit mi. Zaman aşımsız bir POST
    recall sorgusunda panoyu SONSUZA kadar asardı. Kopya çekirdeğe alındığı için "iki sabit
    ayrıştı" sınıfı yapısal olarak kapandı — ama davranışın kendisi hâlâ ölçülür."""
    gorulen: dict = {}

    class _Sahte:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self): return b'{"ok": true}'

    def _sahte_urlopen(istek, timeout=None):
        gorulen["timeout"] = timeout
        gorulen["method"] = istek.get_method()
        return _Sahte()

    import urllib.request
    monkeypatch.setattr(urllib.request, "urlopen", _sahte_urlopen)
    veri, neden = GERCEK_HAFIZA_POST("http://127.0.0.1:8888/x", {"Authorization": "Bearer y"},
                                     "y", b'{"query":"q"}')
    assert (veri, neden) == (b'{"ok": true}', None)
    assert gorulen["method"] == "POST", gorulen
    assert gorulen["timeout"] == api.KAPI_ZAMAN_ASIMI_S == api.HAFIZA_ZAMAN_ASIMI_S, gorulen


def test_post_bacagi_arizayi_yutmaz_ve_maskeler(monkeypatch, tmp_path, sandbox_state):
    def _patlat(istek, timeout=None):
        raise OSError(f"baglanti reddedildi (Bearer {SAHTE_ANAHTAR})")

    import urllib.request
    monkeypatch.setattr(urllib.request, "urlopen", _patlat)
    veri, neden = GERCEK_HAFIZA_POST("http://127.0.0.1:8888/x", {}, SAHTE_ANAHTAR, b"{}")
    assert veri is None
    assert _dolu(neden) and "OSError" in neden, neden
    assert SAHTE_ANAHTAR not in neden, "POST arıza metni sırrı taşıdı"


def test_ag_muhafizi_iki_bacagi_da_kapatir():
    """FIXTURE'IN KENDİSİ ÇİVİLİ. `_ag_kapali` yalnız `_kapi_getir`i kapatsaydı, recall çivileri
    bu makinede AYAKTA olan gerçek 8888'e gider ve kodu değil makineyi ölçerdi.

    "VAR MI" DEĞİL "TUZAK KURULDU MU" ÖLÇÜLÜR. İlk hâli `hasattr(api, "_hafiza_post")` diyordu ve
    VAKUMDA koşuyordu: fixture `raising=False` ile adı ZATEN yaratıyordu, yani `_hafiza_post` hiç
    yazılmamış olsa bile çivi yeşildi (ölçüldü, mutasyon turu 2026-09-02). Artık iki şey ölçülür:
    (a) muhafız gerçek fonksiyonun YERİNE geçmiş, (b) çağrılırsa GERÇEKTEN patlıyor."""
    assert api._hafiza_post is not GERCEK_HAFIZA_POST, \
        "ağ muhafızı POST bacağını kapatmamış — recall çivileri canlı 8888'e gidebilir"
    with pytest.raises(AssertionError, match="casusunu kurmadı"):
        api._hafiza_post("http://127.0.0.1:8888/x", {}, None, b"{}")


def _defter_izi(kok) -> list:
    """Defterin (ad, boyut) izi. DÜZELTME TURU 1 (M-5): önce yalnız DOSYA ADLARI karşılaştırılıyordu
    ve var olan bir deftere APPEND fark edilmiyordu — bu deponun kayıtlı `obs.log` vakası tam
    olarak odur (ajanın pytest dışı koşumu canlı deftere EKLEDİ, yeni dosya yaratmadı)."""
    return sorted((p.name, p.stat().st_size) for p in kok.rglob("*") if p.is_file())


@pytest.mark.parametrize("yol", CPUI_ZARFLI)
def test_cpui_state_defterine_yazmaz(monkeypatch, tmp_path, sandbox_state, yol):
    """SALT-OKUNUR: pano bu uçları görünüm değiştikçe yokluyor — yazan bir uç canlı defteri
    kirletirdi."""
    _cpui(monkeypatch, tmp_path)
    once = _defter_izi(sandbox_state)
    _client().get(yol)
    assert _defter_izi(sandbox_state) == once


def test_recall_state_defterine_yazmaz(monkeypatch, tmp_path, sandbox_state):
    """RECALL POST'TUR AMA YAZMAZ — beyanlı istisnanın ölçülmüş tarafı budur."""
    _cpui(monkeypatch, tmp_path)
    once = _defter_izi(sandbox_state)
    _client().post(RECALL, json={"bank": "B", "query": "alice"})
    assert _defter_izi(sandbox_state) == once


def test_recall_token_tavani_upstream_varsayilanindan_gelir():
    """Sabit ÖLÇÜLDÜ: `openapi.yaml` v0.9.2 `RecallRequest.max_tokens.default` = 4096."""
    assert api.HAFIZA_RECALL_TOKEN_TAVANI == 4096


def test_recall_max_tokens_istemci_sormadikca_dayatilmaz(monkeypatch, tmp_path, sandbox_state):
    """BEYAN İLE DAVRANIŞ AYRIŞMASI (düzeltme turu 1, M-7). Sabit "upstream'in KENDİ varsayılanı"
    diye beyan ediliyordu, ama istemci `max_tokens` göndermese bile gövdeye YAZILIYORDU — yani
    upstream yarın varsayılanını değiştirse bizim vekil onu sessizce 4096'ya SABİTLERDİ. Tavan
    bir SINIRDIR, bir DAYATMA değil: istemci sormadıysa alan hiç gitmez ve upstream kendi
    varsayılanını uygular. İstemci sorduğunda kırpma yerinde kalır (kardeş çiviler)."""
    casus = _cpui(monkeypatch, tmp_path)
    _client().post(RECALL, json={"bank": "B", "query": "alice"})
    coz = json.loads(casus.cagri("/memories/recall")["govde"].decode())
    assert "max_tokens" not in coz, f"istemci sormadan token tavanı dayatıldı: {coz}"
