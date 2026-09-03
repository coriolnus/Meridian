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
   bir sonraki uçta unutulur). Ek olarak: sorgu-dizesi enjeksiyonu, enum süzme, ve `recall`
   POST'unun "sorgu sınıfı" beyanlı istisnası.
K. GÖREV 6-A EKLENTİSİ (TSK-108 Görev 6-A, 2026-09-02) — İKİ yeni uç: `bellek-graf`
   (`GET /v1/default/banks/{bank}/graph`, `get_graph`) ve `profil`
   (`GET /v1/default/banks/{bank}/profile`, `get_bank_profile` — openapi'de `deprecated: true`
   ama CP'nin hâlâ kullandığı TEK profil ucu). İkisi de `CPUI` tablosuna girdi, yani J'nin
   PARAMETRİK çivilerinin TAMAMINDAN geçerler; burada yalnız tabloya SIĞMAYAN üç şey ayrıca
   çivilendi: R7 varsayılan-limit önceliği (CP > openapi > gönderme), `type` geçişi, ve
   kapsam-dışı bırakılan `document_id`/`chunk_id`. Fixture'ların İKİSİ DE sınıf (1) — A1'de
   2026-09-02 18:15 UTC'de ölçüldü (`GRAF_CANLI_GOVDE`/`PROFIL_GOVDE`, aşağıda).

L. YAZMA UÇLARI (TSK-111 dilim 1, Task 11-A, 2026-09-02) — SALT-OKUNURLUK ARTIK MUTLAK DEĞİL.
   Operatör kararı: "butonların çalışması lazım" (Operasyonlar satırındaki İptal/Yeniden dene/
   Kaydı sil; Ana Sayfa FAILED panelindeki kurtarma). Yüzeye İKİ yazan uç girdi:
   `POST /api/hindsight/islem/{eylem}` (eylem ∈ iptal|yeniden-dene|sil) ve
   `POST /api/hindsight/konsolidasyon/kurtar`. Bu bölümün çivilediği şey, o iki ucun
   salt-okunur kardeşleriyle AYNI dört duvarı taşıdığı (sır · ölçülemezlik · zaman aşımı ·
   yol enjeksiyonu) VE yazan bir ucun iki EK duvarı olduğudur:
     · SÖZLÜK KAPALI — `eylem` istemciden gelir ama upstream yolu ONDAN TÜRETİLMEZ; kapalı bir
       sözlükten okunur. Açık bir eşleme, "eylem" adını upstream yoluna çeviren bir istemci-
       kontrollü şablon olurdu ve bu ucun tamamı bir yol-enjeksiyonu yüzeyine dönerdi.
     · İZ ZORUNLU — operatörün BASTIĞI her düğme deftere düşer (v54 sözleşmesi). Yazan ama iz
       bırakmayan bir uç, "bu neden böyle oldu" sorusunu cevapsız bırakır — ve buradaki eylem
       GERİ ALINAMAZ (`sil` bir operasyon kaydını KALICI olarak siler).
   Upstream ölçüldü (aynı commit çapası): dört ucun HİÇBİRİNDE `requestBody` YOKTUR — ne
   `cancel_operation`, ne `retry_operation`, ne `delete_operation`, ne `recover_consolidation`.
   CP'nin KENDİ istemcisi de gövdesiz çağırıyor (`lib/api.ts`, ölçüldü). Yani "beyaz liste"
   BOŞTUR ve boşluğu çivilidir — yarın bir alan eklenirse sessizce geçmesin diye.

   ÜÇÜNCÜ UÇ ("ozellikler") YAZILMADI. Brief `features` ucunun YOLUNU ölçmeyi istedi; ölçüm
   sonucu: upstream'de BAĞIMSIZ bir `features` yolu YOKTUR — `features` yalnız `/version`
   gövdesinin (`VersionResponse.features` → `FeaturesInfo`) bir ALANIdIR, banka altında değil
   (CP'nin `features.observations` bayrağı tam olarak burayı okur). Uydurma yasağı: olmayan bir
   yola vekil yazılmadı; bulgu devir raporuna taşındı.

M. `/varlik` — TSK-112 GÖREV 12-A (2026-09-03) — CP `entities-view` künye paneli tek bir yeni uç
   ister: `GET /api/hindsight/varlik?bank=&id=` → upstream `GET /entities/{entity_id}`
   (`get_entity`, aynı commit çapası, `EntityDetailResponse`). Zarf `{govde, neden}` —
   `zihin-modeli` emsali (TEK bacaklı okuma; `/detay`nin iki bacaklı `oge`/`tarihce`si BURADA
   GEÇERLİ DEĞİL, ayrı bir tarihçe ucu YOK). `/liste`nin `entity_id` süzgeci brief'te bu görevin
   parçası olarak anılıyor ama ÖLÇÜM SONUCU ZATEN VARDI (T1 R1, `list_memories` parametresi) —
   bu turun kendisi onu yeniden EKLEMEDİ, mutasyonla DOĞRULADI.

   `id` DUVARI 11-A'DAN ÖDÜNÇ (`_hafiza_yol_parcasi_guvenli`, tek-kaynak yasası), `bank`'TAN
   FARKLI POLİTİKAYLA: CPUI tablosundaki kardeş uçların tümünde kimlik yalnız KAÇIRILIR
   (`_hafiza_kacir`) — kirli girdi upstream'e escape'lenmiş gider, sözleşme 200'dür.
   `/varlik`ın `id`si REDDEDİLİR (400): CP künye panelinin `id`si her zaman `/varliklar`/`bellek-graf` düğümünden gelen bir
   UUID'dir, serbest metin değil. `bank` kardeş uçlarla AYNI kaçırma politikasında KALIR — yalnız
   `id` için sözleşme değişti. Uç `CPUI` TABLOSUNDADIR (bank enjeksiyonu/auth/sır/zarf/limit-yok
   çivilerinin TAMAMINDAN parametrik geçer) ama `CPUI_IKI_KIMLIKLI`YE BİLEREK EKLENMEDİ — o liste
   ikinci kimliğin KAÇIRILDIĞINI varsayar; `id`nin REDDİ ayrı çivilerle test edilir (J-L).

N. `/webhooklar` — TSK-109 (2026-09-03) — DÜRÜST BOŞLUK KAPANDI. Panonun Hafıza ▸ Yapılandırma
   sayfasındaki webhook alt sekmesi bugüne kadar "bu pano webhook'ları okumuyor" diyordu: bir
   ölçüm sonucu değil bir KAPSAM SINIRI beyanıydı. Bu tur o sınırı SALT-OKUNUR bir listeyle
   kaldırıyor — `GET /api/hindsight/webhooklar?bank=` → upstream
   `GET /v1/default/banks/{bank_id}/webhooks` (`list_webhooks`, aynı commit çapası). Zarf
   `{govde, neden}`, `/belgeler` emsali.

   ÜÇ ŞEY ÖLÇÜLDÜ VE ÜÇÜ DE KARDEŞ LİSTE UÇLARINDAN FARKLI ÇIKTI — refleksle kopyalanan kalıp
   üçünde de yalan söylerdi:
     · SORGU PARAMETRESİ YOKTUR. `list_webhooks`in parametrelerinin TAMAMI şudur — yol:
       `bank_id`; başlık: `authorization`. `limit`/`offset` YOK. Bu yüzden uç `CPUI_LIMITLI`ye
       GİRMEZ ve `_hafiza_sayfa_sorgusu` ÇAĞRILMAZ; çağrılsaydı upstream'in tanımadığı iki
       parametre tele giderdi ve FastAPI onları sessizce yok saydığı için hata GÖRÜNMEZDİ.
     · ZARFTA `total` YOKTUR. `WebhookListResponse`in tek alanı — ve tek `required`i — `items`.
       Yani bu uçta sayfalama ÇİZİLEMEZ: "50'den 20'si" cümlesi kurulamaz, kurulmaya da
       ÇALIŞILMAZ (uydurma yasağı). `/liste`nin `toplam` eki BU UCA TAŞINAMAZ.
     · GÖVDE `secret` TAŞIR VE VEKİLDE SÜZÜLÜR (Rol-1 hükmü, 2026-09-03, düzeltme turu 1).
       `WebhookResponse.secret` webhook imzalama sırrıdır ve upstream onu liste yanıtında
       döndürür. İlk yazımda aynen geçiyordu ("CP de indiriyor" gerekçesiyle); hüküm bunu
       ÇEVİRDİ ve gerekçe İKİ YASA: (a) YASA 6 — bu panonun webhook YAZMA yolu YOK, yani sırrın
       tarayıcıda HİÇBİR OKUYUCUSU yok; CP'nin düzenleme penceresi vardır, bizim yoktur, o
       yüzden "CP ile birebir" burada bir gerekçe DEĞİL. (b) sır hijyeni. Süzgeç `secret`
       anahtarını SİLER ve yerine `secret_tanimli: bool` yazar — üç hâl korunur: alan hiç
       gelmediyse anahtar HİÇ YAZILMAZ (uydurma yasağı), geldi ve boşsa/`null`sa `False`,
       doluysa `True`. Başka hiçbir alana dokunulmaz.

       TEK BOĞAZ DELİNMEDİ: `_hafiza_zarf` isteğe bağlı bir `donustur` kancası aldı ve
       VARSAYILANI `None`dır — yani kalan uçların gövdesi bayt-aynı geçmeye devam eder
       (`test_zarf_kancasi_VARSAYILAN_OLARAK_KAPALI`). Aynen-geçiş çivisi bu ucu artık
       `CPUI_AYNEN` listesinden DIŞLAR ve dışlama BEYANLIDIR (`CPUI_DONUSTURULEN`) — sessiz bir
       istisna, unutulmuş bir istisnadır.

   YAZMA YOLU AÇILMADI. CRUD (`create_webhook`/`update_webhook`/`delete_webhook`) ve teslimat
   geçmişi (`list_webhook_deliveries`) bu turun DIŞINDA; panodaki düğmeler Faz-2 rozetiyle
   görünür ama devre dışı kalır. Rota tablosu çivisi (`test_yazan_fiil_yalniz_beyanli_yollarda`)
   bunu davranışla zorlar: bu yola yazan bir fiil sızarsa öter.

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

import inspect
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
#: YAZMA bacağının gerçek fonksiyonu (TSK-111 dilim 1). ÜÇÜNCÜ bir bacak var çünkü yazan uçlar
#: `_kapi_getir`den de `_hafiza_post`tan da GEÇMEZ: fiil DELETE olabiliyor ve HTTP DURUMU
#: ölçülüyor. Muhafız üç bacağı da kapatmazsa, yazma çivileri bu makinede AYAKTA olan gerçek
#: 8888'e GERÇEK bir `sil` gönderirdi — okuma çivilerinde yalnız yanlış ölçüm olan şey burada
#: GERİ ALINAMAZ bir veri kaybıdır.
GERCEK_HAFIZA_YAZ_ISTEK = api._hafiza_yaz_istek


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
        #: Arıza dalında upstream'in DÖNDÜĞÜ HTTP kodu. Varsayılan `None` KASITLI: ağ arızasında
        #: (bağlantı reddi, zaman aşımı) HİÇBİR HTTP kodu yoktur ve `0`/`500` yazmak uydurma
        #: olurdu — `None` ile "kod ölçülemedi" arasındaki fark bu ucun tüm dersidir.
        self.ariza_http: int | None = None
        #: Başarı dalının HTTP kodu. 200 varsayılan; `ok`un "2xx" şartını ölçen çivi bunu
        #: 2xx DIŞINA çeker (M-2: "çağrı gitti" ile "cevap çözüldü" ayrı gerçeklerdir).
        self.basari_http: int = 200

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

    def yaz(self, url, basliklar=None, sir=None, *, govde=None, yontem="GET", durum=None):
        """`_hafiza_yaz_istek` casusu — AYNI eşleme tablosu (kardeşlerinin gerekçesi).

        FİİLİ CASUS DEĞİL ÇAĞIRAN SÖYLER: `yontem` kaydedilir ve çivi onu okur. Bir `DELETE`in
        sessizce `POST`a dönmesi (ya da tersi) upstream'de BAŞKA bir uca gitmek demektir —
        `/operations/{id}` (iptal) ile `/operations/{id}/retry` (yeniden dene) aynı ön eki
        paylaşıyor, yani yalnız URL'e bakan bir çivi o sapmayı GÖREMEZ."""
        cevap = self._cevap({"url": url, "basliklar": basliklar or {}, "sir": sir,
                             "fiil": yontem, "govde": govde})
        if durum is not None:
            durum["http"] = self.basari_http if cevap[1] is None else self.ariza_http
        return cevap

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

    ÜÇ BACAK KAPATILIR (TSK-108 + TSK-111 dilim 1): `recall` POST'u `_kapi_getir`den GEÇMEZ —
    kendi boğazı `_hafiza_post`tur; YAZMA uçları da ikisinden geçmez — boğazları
    `_hafiza_yaz_istek`tir. Eksik kapatılan her bacak, o bacağın çivilerinin CANLI 8888'e
    gitmesine izin verir ve o testler kodu değil makineyi ölçer. Yazma bacağında bedel daha
    ağırdır: kaçan bir çağrı gerçek bir operasyon kaydını SİLER. Bu fixture'ın kendisi de
    çivili: `test_ag_muhafizi_uc_bacagi_da_kapatir`."""
    def _yasak(*a, **kw):
        raise AssertionError("test kendi `_kapi_getir` casusunu kurmadı — gerçek ağ çağrısı yasak")

    def _yasak_post(*a, **kw):
        raise AssertionError("test kendi `_hafiza_post` casusunu kurmadı — gerçek ağ çağrısı yasak")

    def _yasak_yaz(*a, **kw):
        raise AssertionError("test kendi `_hafiza_yaz_istek` casusunu kurmadı — "
                             "gerçek ağ çağrısı yasak")

    monkeypatch.setattr(api, "_kapi_getir", _yasak)
    monkeypatch.setattr(api, "_hafiza_post", _yasak_post)
    monkeypatch.setattr(api, "_hafiza_yaz_istek", _yasak_yaz)
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
#: TEK KAYNAK (Ruling R28, takip turu): `VERSION_GOVDE`nin İÇİNDEN türetilir, yeniden
#: YAZILMAZ — iki kopya (biri burada, biri yukarıda) sessizce ayrışırdı.
OZELLIKLER_OLCULEN = json.loads(VERSION_GOVDE)["features"]

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
    monkeypatch.setattr(api, "_hafiza_yaz_istek", casus.yaz)
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
    assert g["saglik"]["ozellikler"] == OZELLIKLER_OLCULEN, "anahtar yokluğu features bacağını da düşürdü"
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


# --------------------------------------------------- RULING R28 (2026-09-02, Görev 6-A takibi)
#
# `features` upstream'de BAĞIMSIZ bir yol DEĞİLDİR (Görev 6-A raporu, `task-6a-report.md`) —
# `VersionResponse.features`tır, `/version`in KENDİ gövdesinde. Bu yüzden YENİ bir uç AÇILMADI:
# `api_hindsight`in ZATEN çektiği `/version` gövdesinden `saglik.ozellikler` adıyla, AYNEN (opak,
# süzülmeden) geçirilir. Aşağıdaki dört çivi: (1) varken aynen geçer + İKİNCİ istek açılmaz,
# (2) yokken None+neden, (3) `surum` bacağının arızasından BAĞIMSIZ ölçülür, (4) gerekçe metni
# DEĞER taşımaz (`_hafiza_surum` emsaliyle AYNI disiplin — sır sızmaz).

def test_ozellikler_govde_aynen_gecer(monkeypatch, tmp_path, sandbox_state):
    """`features` VARKEN `saglik.ozellikler` adıyla AYNEN (opak) geçer. AYNI ÇAĞRIDAN: `surum`u
    besleyen `/version` isteğiyle AYNI gövde kullanılır — İKİNCİ bir `/version` isteği AÇILMAZ
    (çağrı sayısı ölçülür, kaynak-metin değil davranış)."""
    casus = _kurulum(monkeypatch, tmp_path)
    g = _client().get("/api/hindsight").json()

    assert g["saglik"]["ozellikler"] == OZELLIKLER_OLCULEN, "features aynen geçmedi"
    assert g["saglik"]["neden"] is None
    version_cagrilari = [c for c in casus.cagrilar if c["url"].endswith("/version")]
    assert len(version_cagrilari) == 1, \
        f"`ozellikler` İKİNCİ bir /version isteği açtı: {len(version_cagrilari)} çağrı"


def test_ozellikler_yokken_none_ve_neden(monkeypatch, tmp_path, sandbox_state):
    """`features` alanı YOKSA UYDURULMAZ: `ozellikler: None` + DOLU `neden` — sessiz `{}` panoda
    "hiç özellik yok" YALANI olurdu; oysa ölçülen "alan adını tanımadım"dır."""
    _kurulum(monkeypatch, tmp_path, esleme=_tam_esleme(
        **{"/version": json.dumps({"api_version": SURUM_OLCULEN}).encode()}))
    g = _client().get("/api/hindsight").json()

    assert g["saglik"]["ozellikler"] is None, "features UYDURULDU"
    assert g["saglik"]["surum"] == SURUM_OLCULEN, "ozellikler arızası surum bacağını da düşürdü"
    assert _dolu(g["saglik"]["neden"]) and "features" in g["saglik"]["neden"], g["saglik"]["neden"]


def test_ozellikler_surum_arizasindan_BAGIMSIZ_olculur(monkeypatch, tmp_path, sandbox_state):
    """İZOLASYON (`saglik`in bacak-ayrımı emsali, `_hafiza_ozellikler` docstring'i): `surum` alanı
    tanınmasa da (`api_version` yerine `surum` adıyla geldiyse) `features` HÂLÂ ayrı okunur — tek
    bacağın arızası ötekini karartmamalı. İkisi de AYNI ham `surum_veri`den okunduğu için bu,
    `surum_neden`in `_hafiza_surum` çağrısıyla EZİLMESİNİN `ozellikler`i etkilemediğinin kanıtıdır."""
    _kurulum(monkeypatch, tmp_path, esleme=_tam_esleme(
        **{"/version": b'{"surum":"9.9.9","features":{"mcp":true}}'}))
    g = _client().get("/api/hindsight").json()

    assert g["saglik"]["surum"] is None, "tanınmayan alandan surum UYDURULDU"
    assert g["saglik"]["ozellikler"] == {"mcp": True}, "surum arızası features bacağını da düşürdü"


def test_ozellikler_neden_deger_tasimaz(monkeypatch, tmp_path, sandbox_state):
    """SIR SIZMAZ (R28), `_hafiza_surum`in emsaliyle AYNI disiplin: `features` yokken üretilen
    `neden` gövdenin DEĞERLERİNİ taşımaz — yalnız görülen alan ADLARINI. `/version` anahtarsız
    çağrıldığı için (`test_anahtarsiz_uclara_anahtar_gonderilmez`) bu gövde `_kapi_maskele`den
    sırsız (`sir=None`) geçer; gerçek ikinci savunma hattı gerekçe metninin DEĞER taşımamasıdır."""
    _kurulum(monkeypatch, tmp_path, esleme=_tam_esleme(
        **{"/version": json.dumps({"api_version": "gizli-deger-9.9.9"}).encode()}))
    g = _client().get("/api/hindsight").json()

    assert g["saglik"]["ozellikler"] is None
    assert _dolu(g["saglik"]["neden"])
    assert "gizli-deger-9.9.9" not in g["saglik"]["neden"], "neden GÖVDE DEĞERİNİ taşıdı"


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
    assert g["saglik"]["ozellikler"] is None, "ölçülemeyen features UYDURULDU"
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
    assert g["saglik"] == {"erisilebilir": True, "surum": SURUM_OLCULEN,
                           "ozellikler": OZELLIKLER_OLCULEN, "neden": None}

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

#: (kirli `bank`, duvarın onu REDDEDİP reddetmediği). Duvarın sözlüğü `_HAFIZA_YASAK_PARCA` +
#: boşluk kuralıdır; `?` ve `#` o sözlükte YOKTUR ve olmaları da gerekmez — sorgu/fragman
#: ayırıcıları upstream PATH'inde kaçırılınca zararsızdır. AYRIM ÖLÇÜLDÜ, VARSAYILMADI: her iki
#: sınıf da ayrı ayrı çivilidir, çünkü "hepsi reddedilir" demek duvarın kapsamını, "hepsi
#: kaçırılır" demek de duvarın varlığını yalanlardı.
BANK_KIRLI_GIRDILER = (
    ("../../v1/default/banks", True),     # baştaki `../`
    ("a/../../etc", True),                # ortadaki `/../`
    ("a b", True),                        # boşluk
    ("a?x=1", False),                     # `?` duvarın sözlüğünde YOK → kaçırılır
    ("a#f", False),                       # `#` aynı
    # DÜZELTME TURU 3: `/` İÇEREN BANKA DA GEÇER ve bu BEYANLIdır. Kural bank ile kimlikler
    # için AYNIdır (tek boğaz, tek kural); `/` traversal DEĞİLdir, traversal `..`dır.
    ("B/x", False),
)


@pytest.mark.parametrize("kotu,reddedilir", BANK_KIRLI_GIRDILER)
def test_bank_kimligi_yol_enjeksiyonuna_kapali(monkeypatch, tmp_path, sandbox_state,
                                               kotu, reddedilir):
    """`bank` KULLANICI GİRDİSİDİR ve upstream URL'inin PATH'ine giriyor. Kaçırılmazsa `../../`
    ile Hindsight'ın BAŞKA bir ucuna gidilir (yazan bir uca bile) — salt-okunur sözleşmesi
    istemcinin insafına kalırdı.

    İKİ HAT (nihai inceleme Ö1, 2026-09-03): duvar (`_hafiza_bank_yolu` → `_hafiza_yol_parcasi_
    guvenli`) yol-parçası sözlüğündeki bir şey görürse istek upstream'e HİÇ ÇIKMAZ; duvarın
    kapsamı dışında kalan kirlilik ise KAÇIRILIR (`%2F`/`%23`). Kaçırmanın tek başına yetmediği
    ölçüldü: uvicorn ASGI yolunu rotalamadan ÖNCE `unquote` eder ve upstream de uvicorn üstünde
    koşar — bu yüzden iki hat birlikte durur."""
    casus = _kurulum(monkeypatch, tmp_path, esleme={"/memories/list": b'{"items": []}'})
    # GİRDİ İSTEMCİ TARAFINDA KAÇIRILIR, yoksa test VAKUMDA koşar: ölçüldü (mutasyon turu,
    # 2026-09-02) — `?bank=a#f` içindeki `#` bir FRAGMAN'dır, sunucuya hiç ulaşmaz ve çivi
    # kaçırılmamış `#`i "geçti" sanardı. Sunucunun GERÇEKTEN gördüğü değer `kotu` olmalı.
    import urllib.parse
    r = _client().get(f"/api/hindsight/liste?bank={urllib.parse.quote(kotu, safe='')}")
    assert r.status_code == 200, f"{kotu!r}: {r.status_code} — pano kararacak bir kod döndü"

    if reddedilir:
        assert casus.cagrilar == [], (
            f"{kotu!r}: duvarın reddetmesi gereken girdi upstream'e gitti: {casus.url_ler()}")
        assert "yol kaçışı" in r.text or "boşluk ya da kontrol karakteri" in r.text, r.text[:200]
        return

    url = casus.cagri("/memories/list")["url"]
    govde = url[len(f"{api.HAFIZA_TABAN_URL}/v1/default/banks/"):]
    kimlik = govde.split("/memories/list")[0]
    for ham in ("/", "..", " ", "?", "#"):
        assert ham not in kimlik, f"kaçırılmamış {ham!r} upstream PATH'ine girdi: {url}"


def test_detay_kimligi_yol_enjeksiyonuna_kapali(monkeypatch, tmp_path, sandbox_state):
    """Aynı sınıf, `kimlik` parametresinde — VE AYNI BEKLENTİ DEĞİŞİMİ (düzeltme turu 2, Y-1):
    kirli kimlik artık kaçırılıp geçirilmiyor, `_hafiza_bank_yolu`da REDDEDİLİYOR."""
    casus = _kurulum(monkeypatch, tmp_path, esleme={"/memories/": b'{"id": "x"}'})
    r = _client().get("/api/hindsight/detay?bank=meridian-arsiv&kimlik=../../../stats")

    assert r.status_code == 200, f"{r.status_code} — ret pano kararacak bir kodla döndü"
    assert casus.cagrilar == [], f"kirli kimlik upstream'e gitti: {casus.url_ler()}"
    assert "yol kaçışı" in r.text, r.text[:200]


def test_kirli_OLMAYAN_ikinci_kimlik_KACIRILARAK_gecer(monkeypatch, tmp_path, sandbox_state):
    """DUVARIN BEDELİ ÖLÇÜLÜR (bedel yasası, `bank` kardeşinin aynısı): reddeden bir duvar,
    MEŞRU kimliği de reddederse ikinci-kimlikli altı uç birden ölür. Duvarın sözlüğünde
    OLMAYAN kirlilik (nokta) hâlâ KAÇIRILARAK geçer — iki hat birlikte çalışır."""
    casus = _cpui(monkeypatch, tmp_path)
    r = _client().get("/api/hindsight/zihin-modeli?bank=B&kimlik=z1")
    assert r.status_code == 200 and r.json()["neden"] is None, r.text
    assert casus.cagrilar, "temiz kimlik de kesildi — duvar yüzeyi öldürdü"
    assert api._hafiza_bank_yolu("B", "/memories/{}", ("a.b",)) == (
        f"{api._HAFIZA_BANK_KOKU}/B/memories/a%2Eb", None)


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
# NEDEN PARAMETRİK: yüzey 2026-09-02'de 3 uçtan 22 uca çıktı. Sözleşme başına TEK TEK yazılan
# çivi, bir sonraki uçta unutulur — ve unutulan çivi, olmayan çividen DAHA kötüdür (dosya
# "kapsıyorum" der). Aşağıdaki tablo ÇİVİLERİN GİRDİSİdir: yeni bir uç tabloya eklenmeden doğarsa
# `test_her_hafiza_ucu_tabloda_kayitli` öter.

#: (bizim yol + sorgu, upstream URL'de GÖRÜLMESİ gereken parça).
#: `B` bank kimliği; ikinci kimlikler `d1`/`z1`/`p1`.
CPUI: tuple[tuple[str, str], ...] = (
    ("/api/hindsight/ozet?bank=B", "/banks/B/stats/memories-timeseries"),
    ("/api/hindsight/varliklar?bank=B", "/banks/B/entities"),
    ("/api/hindsight/varlik?bank=B&id=e1", "/banks/B/entities/e1"),
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
    # ---- TSK-109 (2026-09-03): sorgusuz, `total`sız, `secret` taşıyan liste ----
    ("/api/hindsight/webhooklar?bank=B", "/banks/B/webhooks"),
)
CPUI_YOLLAR = tuple(y for y, _ in CPUI)

#: `{govde, neden}` zarfını taşıyan uçlar — yani `/ozet` (iki bacaklı) ve mevcut üçlü DIŞINDAKİLER.
CPUI_ZARFLI = tuple(y for y, _ in CPUI if not y.startswith("/api/hindsight/ozet"))

#: GÖVDESİ AYNEN GEÇMEYEN UÇLAR — BEYANLI İSTİSNA LİSTESİ (Rol-1 hükmü 2026-09-03).
#: `_hafiza_zarf`in `donustur` kancasını kullanan uçlar buraya YAZILIR. Liste boş kaldığı sürece
#: `CPUI_AYNEN == CPUI_ZARFLI`dir. Neden beyanlı: aynen-geçiş çivisinden bir ucu SESSİZCE
#: çıkarmak (ör. `if yol != …` diye) o ucun gövde sözleşmesini ÇİVİSİZ bırakırdı ve dosya yine
#: "kapsıyorum" derdi. Buraya giren her uç, KENDİ dönüşümünü ayrıca çivilemek zorundadır —
#: `/webhooklar` için `test_webhooklar_imza_sirri_VEKILDE_SUZULUR` + `..._UC_HALLI`.
CPUI_DONUSTURULEN = ("/api/hindsight/webhooklar?bank=B",)

#: Gövdesi upstream'den AYNEN geçen uçlar (aynen-geçiş çivisinin girdisi).
CPUI_AYNEN = tuple(y for y in CPUI_ZARFLI if y not in CPUI_DONUSTURULEN)

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
#: `EntityDetailResponse` (openapi v0.9.2, commit ebad4782 — `get_entity`) `example:` bloğu, TSK-112
#: Görev 12-A. Sınıf (2): alan ADLARI upstream'in, DEĞERLER upstream'in kurgusal örneği.
VARLIK_TEK_ORNEK = {"id": "123e4567-e89b-12d3-a456-426614174000", "canonical_name": "John",
                    "mention_count": 15, "first_seen": "2024-01-15T10:30:00Z",
                    "last_seen": "2024-02-01T14:00:00Z",
                    "observations": [{"text": "John works at Google",
                                       "mentioned_at": "2024-01-15T10:30:00Z"}]}
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
#: `WebhookListResponse` + `WebhookResponse` + `WebhookHttpConfig` (`list_webhooks`, aynı commit
#: çapası) `example:` blokları, TSK-109. Sınıf (2): alan ADLARI upstream'in, DEĞERLER upstream'in
#: kurgusal örneği. Örnekteki İKİNCİ (birebir aynı) öğe kısaltıldı — dosya konvansiyonu.
#:
#: ZARFI KARDEŞLERİNDEN FARKLI VE BU ÖLÇÜLDÜ: `total`/`limit`/`offset` YOKTUR; şemanın tek alanı
#: ve tek `required`i `items`. `secret` upstream'in KENDİ liste yanıtındadır — fixture'a bizim
#: eklediğimiz bir alan DEĞİL; vekil onu SÜZER ve fixture o süzgecin GİRDİSİdir
#: (çivi: `test_webhooklar_imza_sirri_VEKILDE_SUZULUR`).
WEBHOOK_LISTE_ORNEK = {"items": [{"id": "id", "bank_id": "bank_id", "url": "url",
                                  "secret": "secret", "event_types": ["event_types"],
                                  "enabled": True,
                                  "http_config": {"method": "POST", "timeout_seconds": 0,
                                                  "headers": {"key": "headers"},
                                                  "params": {"key": "params"}},
                                  "created_at": "created_at", "updated_at": "updated_at"}]}
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
    "/banks/B/entities/e1": VARLIK_TEK_ORNEK,
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
    "/banks/B/webhooks": WEBHOOK_LISTE_ORNEK,
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
        "/api/hindsight", "/api/hindsight/liste", "/api/hindsight/detay", RECALL} | set(YAZAN_YOLLAR)
    assert kayitli == beklenen, (
        f"rota tablosu ile çivi tablosu ayrıştı — yalnız rotada: {sorted(kayitli - beklenen)}; "
        f"yalnız çivide: {sorted(beklenen - kayitli)}")


def test_yazan_fiil_yalniz_beyanli_yollarda():
    """SALT-OKUNURLUĞUN TEK KAYNAĞI. Uç uç `405` denemek yerine ROTA TABLOSU okunur: böylece
    yarın eklenen bir uç, çiviye dokunulmadan kapsama girer.

    ADI DEĞİŞTİ, SÖZLEŞMESİ DEĞİL (TSK-111 dilim 1, 2026-09-02). Eski adı
    `test_yazan_fiil_yalniz_recallda`ydı ve o ad artık YALAN söylerdi: operatör kararıyla
    (`butonların çalışması lazım`) yüzeye İKİ gerçek yazan uç girdi. Değişen şey listenin
    KENDİSİ, kuralı değil: yazan fiil YALNIZ burada ADIYLA yazılı yollarda olabilir; listeye
    beyansız bir POST/DELETE sızarsa burada öter. `recall` hâlâ istisnadır ama artık
    "durum değiştirmediği için" (sorgu sınıfı), ötekiler "operatör onayıyla" listede."""
    beyanli = set(YAZAN_YOLLAR) | {RECALL}
    for yol, fiiller in _hafiza_rotalari().items():
        yazanlar = fiiller - {"GET", "HEAD", "OPTIONS"}
        if yol in beyanli:
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

@pytest.mark.parametrize("yol", CPUI_AYNEN)
def test_cpui_govde_aynen_gecer(monkeypatch, tmp_path, sandbox_state, yol):
    """AYNEN GEÇİŞ, ZARF SOYULMADAN. Dikkat: burada `items` dizisi ÇIKARILMAZ. Çıkarmak
    `total`/`limit`/`offset`i SESSİZCE düşürürdü ve pano "50 belgeden 20'si" diyemezdi —
    sayfalamanın gerçeği kaybolurdu (bedel yasası: gürültü azaltmanın bedeli ölçülür).

    GİRDİSİ `CPUI_ZARFLI` DEĞİL `CPUI_AYNEN` (Rol-1 hükmü 2026-09-03): dönüştüren uçlar BEYANLI
    bir listeden (`CPUI_DONUSTURULEN`) çıkarılır ve kendi dönüşüm çivilerini taşır. Fark
    önemli — sessiz bir `if` ile atlamak, o ucun gövde sözleşmesini çivisiz bırakırdı."""
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
    ve bu, tablodaki uçların tümünde tek tek değil TEK BOĞAZDA (`_hafiza_json`) sağlanmalı."""
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
    """`bank` KULLANICI GİRDİSİDİR ve CPUI tablosundaki her uçta upstream PATH'ine giriyor.
    Tek bir uçta unutulan kaçırma, `../../` ile YAZAN bir uca gidilmesine yeter — salt-okunur
    sözleşmesi istemcinin insafına kalırdı.

    BEKLENTİ DEĞİŞTİ: "KAÇIRILIR" DEĞİL "REDDEDİLİR" (nihai inceleme Ö1, Rol-1 hükmü
    2026-09-03). Bu çivi önce kirli `bank`ın upstream'e ESCAPE'lenerek gitmesini ölçüyordu ve
    ölçüm doğruydu ama SÖZLEŞME yanlıştı: kaçırma tek başına bir yol-parçası duvarı değildir
    (uvicorn `path = unquote(raw_path)` — `%2F` rotalamadan ÖNCE `/`ye döner ve upstream de
    uvicorn üstünde koşar). Duvar `_hafiza_bank_yolu`ya taşındı; artık kirli `bank` upstream'e
    HİÇ GİTMEZ. İki şey birlikte ölçülür: gerekçe DOLU ve çağrı listesi BOŞ — yalnız "kaçırıldı"
    diyen bir çivi, duvarın kaldırıldığı günü göremezdi."""
    import urllib.parse
    kotu = "../../../v1/default/banks"
    casus = _cpui(monkeypatch, tmp_path,
                  **{"/v1/default/banks": b'{"banks": []}'})
    bozuk = yol.replace("bank=B", f"bank={urllib.parse.quote(kotu, safe='')}")
    r = _client().get(bozuk)

    assert r.status_code == 200, f"{yol}: {r.status_code} — ret pano kararacak bir kodla döndü"
    metin = r.text
    assert casus.cagrilar == [], (
        f"{yol}: kirli `bank` upstream'e gitti — duvar delindi: {casus.url_ler()}")
    # KAPAK: ret SESSİZ olamaz. `neden` alanının hangi isimle geldiği uca göre değişir
    # (`/ozet` iki bacaklı) — bu yüzden gerekçe METNİNDEN ölçülür, alan adından değil.
    assert "yol kaçışı" in metin, f"{yol}: ret gerekçesiz döndü: {metin[:200]}"


@pytest.mark.parametrize("yol,ad", CPUI_IKI_KIMLIKLI)
def test_cpui_ikinci_kimlik_yol_enjeksiyonuna_kapali(monkeypatch, tmp_path, sandbox_state,
                                                     yol, ad):
    """BEKLENTİ DEĞİŞTİ: "KAÇIRILIR" DEĞİL "REDDEDİLİR" (düzeltme turu 2, Y-1).

    `bank` duvarı `_hafiza_bank_yolu`ya taşındığında ikinci kimlik yalnız kaçırılmaya devam
    ediyordu — yani Ö1'in reddettiği "yarım duvar" bir kademe aşağı taşınmıştı ve bu çivi
    ZAYIF duruşu AKTİF olarak çiviliyordu. Duvarın ölçülmüş gerekçesi (uvicorn `unquote`
    rotalamadan ÖNCE koşar) hangi segmentte olduğuna bakmaz: ikinci kimlik de upstream
    PATH'inin bir parçasıdır ve `../../` oradan da banka sınırının dışına çıkar."""
    import urllib.parse
    casus = _cpui(monkeypatch, tmp_path, **{"/v1/default/banks/B/": b"{}"})
    kotu = urllib.parse.quote("../../../stats", safe="")
    r = _client().get(f"{yol}&{ad}={kotu}")
    assert r.status_code == 200, f"{yol}: {r.status_code} — ret pano kararacak bir kodla döndü"
    assert casus.cagrilar == [], (
        f"{yol}: kirli kimlik upstream'e gitti — duvar delindi: {casus.url_ler()}")
    assert "yol kaçışı" in r.text, f"{yol}: ret gerekçesiz döndü: {r.text[:200]}"


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


# --------------------------------- J-L. GÖREV 12-A: `/varlik`a ÖZGÜ (id duvarı, tabloya sığmayan)
#
# `/varlik` CPUI TABLOSUNDADIR (yukarıda) ve o yüzden J-A…J-G'nin PARAMETRİK çivilerinin
# TAMAMINDAN geçer — `bank` enjeksiyon çivisi (J-G, `test_cpui_bank_yol_enjeksiyonuna_kapali`)
# dâhil: bu ucun `bank`ı kardeşleriyle AYNI kaçırma politikasındadır. Burada YALNIZ tabloya
# SIĞMAYAN şey çivilenir: `id`nin 11-A'dan ödünç alınan REDDETME duvarı. `CPUI_IKI_KIMLIKLI`ye
# BİLEREK EKLENMEDİ — o liste ikinci kimliğin KAÇIRILDIĞINI varsayar
# (`test_cpui_ikinci_kimlik_yol_enjeksiyonuna_kapali` kirli bir kimliğin upstream'e
# ESCAPE'lenerek GİTTİĞİNİ ölçer, `casus.cagrilar` boş olursa öter); `/varlik`ın `id`si onun
# yerine REDDEDİLİR ve upstream'e HİÇ gidilmez — aynı listeye eklenseydi o çivi "kimlik verildiği
# hâlde upstream'e hiç gidilmedi" diye YANLIŞ nedenle kırmızı olurdu.

@pytest.mark.parametrize("sorgu,eksik_alan", [
    ("", "bank"), ("?bank=B", "id"), ("?id=e1", "bank"),
    ("?bank=&id=e1", "bank"), ("?bank=B&id=", "id"),
])
def test_varlik_eksik_parametre_400_degil_neden(monkeypatch, tmp_path, sandbox_state,
                                                 sorgu, eksik_alan):
    """BOŞ DİZGE DE EKSİKTİR (F/J-F emsali): `?id=` bir değer DEĞİLDİR. Eksiklik `_hafiza_eksik`
    ile `_hafiza_yol_parcasi_guvenli` DEVREYE GİRMEDEN ÖNCE yakalanır — ikisi karışırsa "eksik"
    (200 + neden) "kirli" (400) diye YANLIŞ kodla dönerdi."""
    casus = _cpui(monkeypatch, tmp_path)
    r = _client().get(f"/api/hindsight/varlik{sorgu}")
    assert r.status_code == 200, f"{sorgu!r}: {r.status_code} — eksik parametre 400 üretti"
    g = r.json()
    assert set(g) == {"govde", "neden"}, sorted(g)
    assert g["govde"] is None
    assert _dolu(g["neden"]) and eksik_alan in g["neden"], g["neden"]
    assert casus.cagrilar == [], f"{sorgu!r}: parametre eksikken upstream'e gidildi"


@pytest.mark.parametrize("kotu", ["../../../stats", "a/../../etc", "a%2Fb", "a b", "e1/../x"])
def test_varlik_id_yol_kacisi_reddedilir(monkeypatch, tmp_path, sandbox_state, kotu):
    """ID DUVARI (TSK-112 Görev 12-A, 11-A'dan ÖDÜNÇ): `id` upstream URL'inin PATH'ine giriyor ve
    CP künye panelinde her zaman `/varliklar`/`bellek-graf`tan gelen bir UUID'dir — serbest metin
    DEĞİL. Kardeş uçların aksine kirli girdi burada KAÇIRILIP GEÇİRİLMEZ, REDDEDİLİR: 400 +
    `govde: None` + DOLU `neden`, upstream'e HİÇ gidilmeden (11-A'nın `test_islem_yol_kacisi_
    reddedilir` emsali, okuma tarafının aynısı — GİRDİ İSTEMCİ TARAFINDA KAÇIRILIR ki sunucunun
    GERÇEKTEN gördüğü değer `kotu` olsun, G bölümünün mutasyon dersi)."""
    import urllib.parse
    casus = _cpui(monkeypatch, tmp_path)
    r = _client().get(f"/api/hindsight/varlik?bank=B&id={urllib.parse.quote(kotu, safe='')}")
    assert r.status_code == 400, f"{kotu!r}: {r.status_code} — kirli id upstream'e kaçırılarak geçti"
    g = r.json()
    assert set(g) == {"govde", "neden"}, sorted(g)
    assert g["govde"] is None
    assert _dolu(g["neden"]) and "id" in g["neden"], g["neden"]
    assert casus.cagrilar == [], f"{kotu!r}: kirli id'yle yine de upstream'e gidildi"


# ------------------------------ J-M. TSK-109: `/webhooklar`a ÖZGÜ (tabloya sığmayan üç ölçüm) ---
#
# Uç `CPUI` TABLOSUNDADIR, yani J-A…J-G'nin PARAMETRİK çivilerinin TAMAMINDAN geçer: kayıt,
# yalnız-GET, `_auth`, ölçülemezlik yutulmaz (arıza/JSON-değil/boş gövde), zarf aynen geçer, sır
# duvarı (istek + istisna + upstream gövdesi), eksik `bank`, `bank` yol enjeksiyonu, deftere
# yazmama. `CPUI_LIMITLI`ye ve `CPUI_ETIKETLI`ye GİRMEDİ — ve girmemesi bir tercih değil bir
# ÖLÇÜM SONUCUDUR; ilk çivi tam olarak onu kaydeder.

def test_webhooklar_upstreame_sorgu_gondermez(monkeypatch, tmp_path, sandbox_state):
    """ÖLÇÜLDÜ: `list_webhooks`in parametrelerinin TAMAMI yol `bank_id` + başlık `authorization`.
    SORGU PARAMETRESİ YOKTUR — `limit`/`offset` dâhil.

    NEDEN ÇİVİ GEREKİYOR: kardeş on listeleyen uç `_hafiza_sayfa_sorgusu`dan geçiyor ve o kalıbı
    refleksle kopyalamak burada SESSİZ bir yalan üretirdi — FastAPI tanımadığı sorgu
    parametresini yok sayar, yani upstream 422 vermez, `neden` boş kalır ve URL'de var olmayan
    bir sözleşme yazılı durur. İstemci ne gönderirse göndersin sonuç aynı olmalı: uç `limit`i
    imzasında TAŞIMAZ, dolayısıyla upstream URL'i sorgusuz kalır."""
    casus = _cpui(monkeypatch, tmp_path)
    _client().get("/api/hindsight/webhooklar?bank=B&limit=9999&offset=5")
    url = casus.cagri("/banks/B/webhooks")["url"]
    assert "?" not in url, f"upstream'de karşılığı olmayan bir sorgu dizesi kuruldu: {url}"


def test_webhooklar_zarfinda_toplam_yoktur(monkeypatch, tmp_path, sandbox_state):
    """`WebhookListResponse`in TEK alanı `items`tır (`required: [items]`, ölçüldü) — kardeş liste
    uçlarının `total`/`limit`/`offset` üçlüsü BU UÇTA YOKTUR.

    İKİ ŞEYİ BİRDEN TUTAR: (a) fixture'ın kaydı upstream şemasıyla aynı kalır — ikinci bir alan
    eklenirse burada öter, çünkü o alan artık ÖLÇÜLMÜŞ değil UYDURULMUŞ olur; (b) vekil zarfa
    kendi `toplam`ını EKLEMEZ. `/liste`ye `toplam` eklenmesi (düzeltme turu 1, R4) meşruydu
    çünkü orada upstream `total` GÖNDERİYORDU; buraya taşınması taşınacak sayı olmadığı için
    uydurma olurdu ve pano "N webhook'tan M'si" diye YANLIŞ bir cümle kurardı."""
    assert set(WEBHOOK_LISTE_ORNEK) == {"items"}, (
        "fixture upstream şemasından ayrıştı — `WebhookListResponse` yalnız `items` taşır")
    _cpui(monkeypatch, tmp_path)
    g = _client().get("/api/hindsight/webhooklar?bank=B").json()
    assert set(g) == {"govde", "neden"}, sorted(g)
    assert set(g["govde"]) == {"items"}, (
        f"zarfa upstream'de olmayan bir alan eklendi: {sorted(g['govde'])}")


#: SINIF (3) — SENTETİK. Upstream'in kendi `example:`i `secret` DEĞERİNİ de "secret" yazıyor,
#: yani anahtar adıyla değeri AYNI dizge. O fixture'la "değer sızmadı" demek ölçemezdi: `secret`
#: kelimesinin yanıtta olmaması anahtarın mı değerin mi düştüğünü söylemez. Bu sabit yalnız
#: SÜZGECİN DAVRANIŞINI ölçmek için var ve upstream şeması olduğunu İDDİA ETMEZ.
WEBHOOK_SIRRI_SENTETIK = "wh-imza-sirri-CIVI-SENTETIK"

#: `_webhook_govdesi`nin "anahtar HİÇ yok" hâli — `None` bir DEĞERdir ve üçüncü hâlle karışırdı.
_SIR_ANAHTARI_YOK = object()


def _webhook_govdesi(sir: object = _SIR_ANAHTARI_YOK) -> bytes:
    """Casus gövdesi FIXTURE'IN KENDİSİNDEN türer, elle yazılmaz — yalnız `secret` değişir.

    Elle yazılsaydı iki kayıt (fixture + bu gövde) sessizce ayrışırdı ve "başka alana
    dokunulmadı" çivisi kendi kopyasını doğrulardı (tek-kaynak yasası)."""
    oge = dict(WEBHOOK_LISTE_ORNEK["items"][0])
    if sir is _SIR_ANAHTARI_YOK:
        oge.pop("secret", None)
    else:
        oge["secret"] = sir
    return json.dumps({"items": [oge]}).encode()


def test_webhooklar_imza_sirri_VEKILDE_SUZULUR(monkeypatch, tmp_path, sandbox_state):
    """ROL-1 HÜKMÜ (2026-09-03 gece, TSK-109 düzeltme turu 1). Bu çivi ilk yazımda TERSİNİ
    söylüyordu (`..._suzulmeden_gecer`): sır aynen geçiyordu ve gerekçe "CP de indiriyor"du.
    Hüküm gerekçeyi reddetti, iki yasayla:

      (a) YASA 6 — OKUYUCUSUZ YAZIM YOK. Bu panonun webhook YAZMA yolu YOKTUR; sırrın
          tarayıcıda hiçbir okuyucusu yok. CP'nin düzenleme penceresi VAR, bizim YOK — yani
          "CP ile birebir" burada bir gerekçe değil, bir benzetme.
      (b) SIR HİJYENİ — okunmayan bir sırrı taşımak, taşımanın bedelini bedava sanmaktır.

    ÖLÇÜLEN ÜÇ ŞEY: sır DEĞERİ yanıtın hiçbir yerinde yok · `secret` anahtarı yok ·
    `secret_tanimli` doğru. DÖRDÜNCÜSÜ AYRI VE ÖNEMLİ: başka HİÇBİR alana dokunulmadı —
    beklenen gövde fixture'dan TÜRETİLİR, elle yazılmaz."""
    casus = _cpui(monkeypatch, tmp_path,
                  **{"/banks/B/webhooks": _webhook_govdesi(WEBHOOK_SIRRI_SENTETIK)})
    r = _client().get("/api/hindsight/webhooklar?bank=B")
    assert r.status_code == 200, r.text
    assert casus.cagri("/banks/B/webhooks"), "vakum: upstream'e hiç gidilmedi, süzgeç ölçülmedi"
    assert WEBHOOK_SIRRI_SENTETIK not in r.text, "WEBHOOK İMZALAMA SIRRI PANOYA SIZDI"

    oge = r.json()["govde"]["items"][0]
    assert "secret" not in oge, "`secret` anahtarı zarfta duruyor — süzgeç değeri değil adı da siler"
    assert oge["secret_tanimli"] is True, (
        f"sır DOLUYKEN `secret_tanimli` doğru değil: {oge.get('secret_tanimli')!r}")

    beklenen = {k: v for k, v in WEBHOOK_LISTE_ORNEK["items"][0].items() if k != "secret"}
    assert {k: v for k, v in oge.items() if k != "secret_tanimli"} == beklenen, (
        "süzgeç `secret` dışında bir alana da dokundu — sözleşme TEK alanla sınırlı")


@pytest.mark.parametrize("sir,beklenen", [
    (WEBHOOK_SIRRI_SENTETIK, True),
    (None, False),
    ("", False),
    (_SIR_ANAHTARI_YOK, None),
])
def test_webhooklar_secret_tanimli_UC_HALLI(monkeypatch, tmp_path, sandbox_state, sir, beklenen):
    """ÜÇ HÂL, ÜÇÜ AYRI — UYDURMA YASAĞININ SÜZGEÇTEKİ KARŞILIĞI. `secret_tanimli`yi her zaman
    yazmak, alan HİÇ gelmediğinde "sır tanımlı değil" diye ÖLÇÜLMEMİŞ bir hüküm basardı; oysa
    o durumda bilinen tek şey upstream'in bu alanı göndermediğidir. `beklenen is None` =
    anahtar HİÇ YAZILMAMALI."""
    _cpui(monkeypatch, tmp_path, **{"/banks/B/webhooks": _webhook_govdesi(sir)})
    oge = _client().get("/api/hindsight/webhooklar?bank=B").json()["govde"]["items"][0]
    assert "secret" not in oge, "her hâlde `secret` anahtarı düşer"
    if beklenen is None:
        assert "secret_tanimli" not in oge, (
            "upstream alanı hiç göndermedi ama vekil bir hüküm yazdı — ölçülmemiş `False`")
    else:
        assert oge["secret_tanimli"] is beklenen, (
            f"{sir!r} için beklenen {beklenen}, gelen {oge.get('secret_tanimli')!r}")


def test_zarf_kancasi_VARSAYILAN_OLARAK_KAPALI(monkeypatch, tmp_path, sandbox_state):
    """TEK BOĞAZ DELİNMEDİ. Süzme, `_hafiza_zarf`e `donustur` adında İSTEĞE BAĞLI bir kanca
    eklenerek yapıldı; kancanın varsayılanı `None`dır ve o hâlde gövde AYNEN geçer. Burada
    ikisi ölçülür: imzadaki varsayılan ve kardeş bir ucun gövdesinin bayt düzeyinde aynılığı.

    KAPSAM SINIRI BEYANLI (mutasyonla ÖLÇÜLDÜ, düzeltme turu 1): bu çivi kancanın YANLIŞ BİR
    UCA BAĞLANMASINI YAKALAYAMAZ. `donustur=_webhook_sirrini_suz` `/belgeler`e verildiğinde
    süzgeç orada NO-OP'tur (belge öğelerinde `secret` yoktur), yani gövde bayt-aynı kalır ve
    bu çivi YEŞİL kalır — mutasyon koşuldu, geçti. Bağlantının kendisini ölçen çivi ayrıdır:
    `test_zarf_kancasi_YALNIZ_BEYANLI_UCLARDA_BAGLI`. İkisini tek çivi sanmak, "yeşil" ile
    "kapsanmış"ı karıştırmak olurdu."""
    varsayilan = inspect.signature(api._hafiza_zarf).parameters["donustur"].default
    assert varsayilan is None, f"`donustur` kancasının varsayılanı değişti: {varsayilan!r}"

    ham = json.dumps(BELGELER_ORNEK).encode()
    _cpui(monkeypatch, tmp_path, **{"/banks/B/documents": ham})
    govde = _client().get("/api/hindsight/belgeler?bank=B").json()["govde"]
    assert json.dumps(govde, sort_keys=True) == json.dumps(json.loads(ham), sort_keys=True), (
        "kancanın varsayılanı kardeş ucun gövdesini değiştirdi — sessiz bir yüzey değişikliği")


def test_zarf_kancasi_YALNIZ_BEYANLI_UCLARDA_BAGLI(monkeypatch, tmp_path, sandbox_state):
    """KANCA HANGİ UÇLARA BAĞLI — DAVRANIŞTAN ÖLÇÜLÜR, KAYNAK METNİNDEN DEĞİL.

    Bu çivi `CPUI_DONUSTURULEN` beyanının DOĞRU olduğunu zorlar: tablodaki her uç çağrılır ve
    `_hafiza_zarf`e `donustur` GERÇEKTEN verilen uçların kümesi beyanla kıyaslanır. İki yönlü
    ısırır — beyansız bir uca kanca bağlanırsa da (o uç aynen-geçiş çivisinden düşmeden gövdesi
    değişmiş olurdu), beyanlı bir uçtan kanca DÜŞERSE de (sır sızardı).

    NEDEN GEREKTİ: kardeşi (`..._VARSAYILAN_OLARAK_KAPALI`) yanlış bağlantıyı GÖREMİYOR — süzgeç
    başka bir uçta no-op olduğu için gövde bayt-aynı kalıyor ve çivi yeşil geçiyordu (mutasyonla
    ölçüldü, düzeltme turu 1). "Çivi yeşili kanıt değildir" dersinin bu turdaki karşılığı."""
    _cpui(monkeypatch, tmp_path)
    ozgun = api._hafiza_zarf
    kancali: list[str] = []
    izlenen: dict[str, str] = {}

    def sarmal(*konum, donustur=None, **ad):
        if donustur is not None:
            kancali.append(izlenen["yol"])
        return ozgun(*konum, donustur=donustur, **ad)

    monkeypatch.setattr(api, "_hafiza_zarf", sarmal)
    for yol in CPUI_ZARFLI:
        izlenen["yol"] = yol
        r = _client().get(yol)
        assert r.status_code == 200, f"{yol}: {r.status_code} — süpürme eksik ölçtü"

    assert sorted(set(kancali)) == sorted(CPUI_DONUSTURULEN), (
        f"kanca beyanla ayrıştı — kancalı: {sorted(set(kancali))}; "
        f"beyanlı: {sorted(CPUI_DONUSTURULEN)}")


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


def test_ag_muhafizi_uc_bacagi_da_kapatir():
    """FIXTURE'IN KENDİSİ ÇİVİLİ. `_ag_kapali` yalnız `_kapi_getir`i kapatsaydı, recall çivileri
    bu makinede AYAKTA olan gerçek 8888'e gider ve kodu değil makineyi ölçerdi.

    "VAR MI" DEĞİL "TUZAK KURULDU MU" ÖLÇÜLÜR. İlk hâli `hasattr(api, "_hafiza_post")` diyordu ve
    VAKUMDA koşuyordu: fixture `raising=False` ile adı ZATEN yaratıyordu, yani `_hafiza_post` hiç
    yazılmamış olsa bile çivi yeşildi (ölçüldü, mutasyon turu 2026-09-02). Artık iki şey ölçülür:
    (a) muhafız gerçek fonksiyonun YERİNE geçmiş, (b) çağrılırsa GERÇEKTEN patlıyor.

    ÜÇÜNCÜ BACAK (TSK-111 dilim 1): yazma boğazı. Kaçan bir yazma çağrısının bedeli okuma
    bacağınınkinden AĞIRdır — `sil` gerçek bir operasyon kaydını KALICI olarak siler."""
    for ad, gercek, cagri in (
            ("_hafiza_post", GERCEK_HAFIZA_POST,
             lambda: api._hafiza_post("http://127.0.0.1:8888/x", {}, None, b"{}")),
            ("_hafiza_yaz_istek", GERCEK_HAFIZA_YAZ_ISTEK,
             lambda: api._hafiza_yaz_istek("http://127.0.0.1:8888/x", {}, None,
                                           yontem="DELETE"))):
        assert getattr(api, ad) is not gercek, \
            f"ağ muhafızı `{ad}` bacağını kapatmamış — çiviler canlı 8888'e gidebilir"
        with pytest.raises(AssertionError, match="casusunu kurmadı"):
            cagri()


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


# =================================================================================================
# L. YAZMA UÇLARI — TSK-111 dilim 1 (Task 11-A, 2026-09-02)
# =================================================================================================
#
# YOL HARİTASI YİNE ÖLÇÜLDÜ, TÜRETİLMEDİ. Dört upstream ucu da aynı commit çapasından okundu
# (`hindsight-clients/go/api/openapi.yaml`, ebad4782…; satır çapaları: `cancel_operation` 2775,
# `retry_operation` 2880, `delete_operation` 2926, `recover_consolidation` 3622) ve CP'nin KENDİ
# istemcisiyle (`hindsight-control-plane/src/lib/api.ts`) karşılaştırıldı. İki bulgu:
#   · HİÇBİRİNDE `requestBody` YOK — parametreler yalnız YOLDA (`bank_id`, `operation_id`) ve
#     isteğe bağlı `authorization` başlığında. CP de gövdesiz çağırıyor.
#   · `cancel` ile `retry`nin yolları aynı ön eki paylaşıyor (`/operations/{id}` ⊂
#     `/operations/{id}/retry`), yani yalnız URL'e bakan bir çivi fiil sapmasını GÖREMEZ —
#     bu yüzden aşağıdaki tablo FİİLİ de taşır ve çivi ikisini BİRLİKTE ölçer.

#: (bizim `eylem`, upstream FİİL, upstream URL'de görülmesi gereken parça). ÖLÇÜM KAYDIdır.
YAZMA_EYLEMLERI: tuple[tuple[str, str, str], ...] = (
    ("iptal", "DELETE", "/banks/B/operations/o1"),
    ("yeniden-dene", "POST", "/banks/B/operations/o1/retry"),
    ("sil", "DELETE", "/banks/B/operations/o1/delete"),
)
#: KONSOLİDASYON DA SÖZLÜKLEŞTİ (düzeltme turu 1, R30-ek). `kurtar` tek başına bir rotaydı;
#: `tetikle` eklenince aynı 15 satır (auth → gövde → duvar → threadpool → iz → diag) ÜÇÜNCÜ kez
#: yazılacaktı. `{eylem}` deseni `islem`in aynısıdır ve `/konsolidasyon/kurtar` YOLU DEĞİŞMEDİ —
#: `{eylem}` onu da eşler, yani 11-B'nin yazacağı istemci kırılmaz (çivi: `test_kurtar_yolu_AYNEN`).
ISLEM_KOK = "/api/hindsight/islem"
KONSOLIDASYON_KOK = "/api/hindsight/konsolidasyon"
KURTAR = f"{KONSOLIDASYON_KOK}/kurtar"
TETIKLE = f"{KONSOLIDASYON_KOK}/tetikle"
#: Rota tablosunda YAZAN fiile izin verilen yollar — `test_yazan_fiil_yalniz_beyanli_yollarda`
#: ve `test_her_hafiza_ucu_tabloda_kayitli` bundan beslenir (tek kaynak).
YAZAN_YOLLAR = (f"{ISLEM_KOK}/{{eylem}}", f"{KONSOLIDASYON_KOK}/{{eylem}}")

#: (eylem, upstream FİİL, upstream URL parçası, gövde BEYAZ LİSTESİ). Dördüncü sütun ÖLÇÜMDÜR:
#: `recover_consolidation`ın `requestBody`si YOK, `trigger_consolidation`ınki VAR
#: (`ConsolidationRequest.observation_scopes`, openapi ~3829). "Dördünün boşluğu beşincisi için
#: kanıt değildir" — inceleme bu kalemi ayrıca ölçmemizi istedi ve ölçüm ikisini AYIRDI.
KONSOLIDASYON_EYLEMLERI: tuple[tuple[str, str, str, tuple], ...] = (
    ("kurtar", "POST", "/banks/B/consolidation/recover", ()),
    ("tetikle", "POST", "/banks/B/consolidate", ("observation_scopes",)),
)


def _islem(eylem: str) -> str:
    return f"{ISLEM_KOK}/{eylem}"


def _konsolidasyon(eylem: str) -> str:
    return f"{KONSOLIDASYON_KOK}/{eylem}"


# ---- KAYNAKTAN TÜRETİLEN GÖVDELER (sınıf 2) — upstream `example:` blokları, aynı commit çapası.
#      `CancelOperationResponse`/`RetryOperationResponse`/`DeleteOperationResponse` ÜÇÜ DE aynı üç
#      alanı taşır (`success`/`message`/`operation_id`, üçü de `required`); yalnız `message`
#      metni ayrışır — o yüzden tek şablondan türetilir, üç kez YAZILMAZ (tek-kaynak yasası).
ORNEK_ISLEM_KIMLIGI = "550e8400-e29b-41d4-a716-446655440000"


def _islem_ornegi(mesaj_sonu: str) -> dict:
    return {"success": True, "message": f"Operation {ORNEK_ISLEM_KIMLIGI} {mesaj_sonu}",
            "operation_id": ORNEK_ISLEM_KIMLIGI}


#: `RecoverConsolidationResponse.example` — TEK alan (`retried_count`, `required`).
KURTAR_ORNEK = {"retried_count": 42}
#: `ConsolidationResponse.example` — `operation_id` (required) + `deduplicated` (default false).
#: DEĞER GERÇEKTEN BÖYLE: upstream'in kendi örneği alan adını değer olarak yazmış; "temsili"
#: diye düzeltmek, sınıf-2 etiketini (kaynaktan TÜRETİLDİ) yalan yapardı.
TETIKLE_ORNEK = {"operation_id": "operation_id", "deduplicated": False}
#: Yazma uçlarının upstream gövdeleri; anahtarlar `_Casus` eşleme tablosunun parçalarıdır.
_YAZMA_GOVDELER: dict[str, object] = {
    "/banks/B/operations/o1": _islem_ornegi("cancelled"),
    "/banks/B/operations/o1/retry": _islem_ornegi("queued for retry"),
    "/banks/B/operations/o1/delete": _islem_ornegi("deleted"),
    "/banks/B/consolidation/recover": KURTAR_ORNEK,
    "/banks/B/consolidate": TETIKLE_ORNEK,
}


def _yazma(monkeypatch, tmp_path, *, anahtar=SAHTE_ANAHTAR, **degistir) -> _Casus:
    """Yazma çivilerinin casusu: CP-UI okuma tablosu + dört yazma ucu AYNI eşlemede.

    NEDEN AYNI TABLO: bir yazma ucu yanlışlıkla bir OKUMA yoluna saparsa (ya da tersi) casus
    "beklenmeyen kaynak" diye patlamaz — ama `cagri()` tekliği ve fiil kıyası sapmayı yakalar.
    Ayrı tablo kursaydık sapma "beklenmeyen kaynak" olarak görünürdü ve HANGİ uca gittiği
    kaybolurdu."""
    esleme = _cpui_esleme(**{p: json.dumps(g).encode() for p, g in _YAZMA_GOVDELER.items()})
    esleme.update(degistir)
    return _kurulum(monkeypatch, tmp_path, esleme=esleme, anahtar=anahtar)


def _yazma_govdesi(**ek) -> dict:
    return {"bank": "B", "id": "o1", **ek}


# ------------------------------------------------------------------- L-A. SÖZLÜK KAPALI

def test_islem_eylem_sozlugu_olculen_upstream_yollariyla_ayrismaz():
    """KIYAS ÇİVİSİ (`UPSTREAM_LIMIT_MAKSIMUMU` emsali): kodun sözlüğü upstream ÖLÇÜMÜNDEN
    türetilmez, KIYASLANIR. Ayrışırlarsa bir düğme sessizce BAŞKA bir upstream ucuna basar —
    ve bu uçlarda "başka uç" demek `iptal` yerine `sil` demek olabilir (geri alınamaz)."""
    olculen = {eylem: (fiil, parca.split("/banks/B", 1)[1], ())
               for eylem, fiil, parca in YAZMA_EYLEMLERI}
    kodun = {eylem: (fiil, kuyruk.format("o1"), beyaz)
             for eylem, (fiil, kuyruk, beyaz) in api._HAFIZA_ISLEM_EYLEMLERI.items()}
    assert kodun == olculen, f"eylem sözlüğü upstream ölçümüyle ayrıştı: {kodun} ≠ {olculen}"


#: `""` LİSTEDEN ÇIKARILDI (düzeltme turu 1, M-4c): boş segment rotayı HİÇ eşleştirmiyor, yani
#: o vaka bizim sözlüğümüzü değil FastAPI'yi ölçüyordu — sayıyı şişiren vakumlu bir parametre.
@pytest.mark.parametrize("eylem", ["yok", "consolidate", "../sil", "iptal2", "IPTAL"])
def test_islem_taninmayan_eylem_upstreame_gitmez(monkeypatch, tmp_path, sandbox_state, eylem):
    """SÖZLÜK KAPALI OLMASAYDI bu uç bir yol-enjeksiyonu yüzeyi olurdu: `eylem` istemciden gelir.
    İki şey birlikte ölçülür — (a) 4xx döner, (b) upstream'e HİÇ çağrı gitmez. Yalnız (a)'yı
    ölçen bir çivi, "önce çağır sonra hata dön" gibi bir sapmayı GÖREMEZ."""
    casus = _yazma(monkeypatch, tmp_path)
    r = _client().post(_islem(eylem), json=_yazma_govdesi())
    assert r.status_code in (400, 404), f"{eylem!r} → {r.status_code}"
    assert casus.cagrilar == [], f"tanınmayan eylem upstream'e gitti: {casus.url_ler()}"


def test_islem_taninmayan_eylem_gerekcesi_olculu(monkeypatch, tmp_path, sandbox_state):
    """4xx'in gövdesi de DOLU olmalı: pano düğmeyi neden reddettiğini operatöre söyler."""
    _yazma(monkeypatch, tmp_path)
    govde = _client().post(_islem("yok"), json=_yazma_govdesi()).json()
    assert govde["ok"] is False and _dolu(govde["neden"]), govde
    assert govde["govde"] is None and govde["http"] is None, govde


# --------------------------------------------------------- L-B. ÜÇ EYLEM, DOĞRU FİİL + YOL

@pytest.mark.parametrize("eylem,fiil,parca", YAZMA_EYLEMLERI)
def test_islem_dogru_fiil_ve_yola_gider(monkeypatch, tmp_path, sandbox_state, eylem, fiil, parca):
    casus = _yazma(monkeypatch, tmp_path)
    r = _client().post(_islem(eylem), json=_yazma_govdesi())
    assert r.status_code == 200, r.text
    cagri = casus.cagri(parca)
    assert cagri["fiil"] == fiil, f"{eylem}: fiil {cagri['fiil']}, beklenen {fiil}"
    assert cagri["url"].endswith(parca), f"{eylem}: {cagri['url']} → {parca} beklenirdi"


@pytest.mark.parametrize("eylem,fiil,parca", YAZMA_EYLEMLERI)
def test_islem_upstream_govdesi_aynen_gecer(monkeypatch, tmp_path, sandbox_state,
                                            eylem, fiil, parca):
    """Vekil upstream cevabını SÜZMEZ: pano `success`/`message`/`operation_id`i olduğu gibi
    görür. Süzseydik upstream yarın bir alan eklediğinde pano onu sessizce kaybederdi."""
    _yazma(monkeypatch, tmp_path)
    govde = _client().post(_islem(eylem), json=_yazma_govdesi()).json()
    assert govde["govde"] == _YAZMA_GOVDELER[parca], govde
    assert govde["ok"] is True and govde["neden"] is None and govde["http"] == 200, govde


def test_islem_govdesiz_gider(monkeypatch, tmp_path, sandbox_state):
    """ÖLÇÜLDÜ: üç upstream ucunun HİÇBİRİNDE `requestBody` YOK (openapi, aynı çapa) ve CP de
    gövdesiz çağırıyor. İstemcinin gövdesini upstream'e iletmek, ölçülmemiş bir sözleşmeyi
    ölçülmüş gibi göstermek olurdu."""
    casus = _yazma(monkeypatch, tmp_path)
    _client().post(_islem("iptal"), json=_yazma_govdesi(fazladan="sızmamalı"))
    cagri = casus.cagri("/banks/B/operations/o1")
    assert cagri["govde"] is None, f"gövdesiz uca gövde gitti: {cagri['govde']!r}"


# ------------------------------------------------------------------ L-C. KONSOLİDASYON KURTARMA

def test_kurtar_dogru_yola_gider(monkeypatch, tmp_path, sandbox_state):
    casus = _yazma(monkeypatch, tmp_path)
    r = _client().post(KURTAR, json={"bank": "B"})
    assert r.status_code == 200, r.text
    cagri = casus.cagri("/consolidation/recover")
    assert cagri["fiil"] == "POST" and cagri["url"].endswith("/banks/B/consolidation/recover")
    assert r.json()["govde"] == KURTAR_ORNEK, r.json()


def test_kurtar_beyaz_listesi_BOS_olculdu(monkeypatch, tmp_path, sandbox_state):
    """`recall`ın beyaz listesi DOLU çünkü `RecallRequest` şeması dolu. Burada ölçüm sonucu
    BOŞTUR: `recover_consolidation`ın `requestBody`si YOKTUR (openapi ~3622; CP `lib/api.ts`
    `recoverConsolidation` da gövdesiz gönderiyor). Boşluk ÇİVİLİDİR — yarın upstream bir alan
    eklerse "aynen geçiş" onu istemcinin insafına açmasın diye."""
    casus = _yazma(monkeypatch, tmp_path)
    _client().post(KURTAR, json={"bank": "B", "force": True, "limit": 999, "id": "o1"})
    assert casus.cagri("/consolidation/recover")["govde"] is None, "kurtarmaya gövde sızdı"


def test_kurtar_bank_zorunlu(monkeypatch, tmp_path, sandbox_state):
    casus = _yazma(monkeypatch, tmp_path)
    r = _client().post(KURTAR, json={})
    assert r.status_code == 400, r.text
    assert r.json()["ok"] is False and _dolu(r.json()["neden"]), r.json()
    assert casus.cagrilar == [], f"eksik `bank` ile upstream'e gidildi: {casus.url_ler()}"


# ------------------------------------------------------------------------- L-D. YOL GÜVENLİĞİ

@pytest.mark.parametrize("kimlik", ["../../v1/default/banks/other/operations/x",
                                    "o1/../delete", "..", "a//b", "/a", "o1\\x"])
def test_islem_yol_kacisi_reddedilir(monkeypatch, tmp_path, sandbox_state, kimlik):
    """OKUMA UÇLARINDA KAÇIRMA YETERLİYDİ, BURADA DEĞİL. `_hafiza_kacir` `/`yi `%2F`, `.`yı
    `%2E` yapar — ama `%2F`yi ROTALAMADAN ÖNCE çözen bir vekil katmanı (bilinen bypass sınıfı)
    onu yine yol atlaması olarak okur. Okumada bedeli yanlış bir GÖRÜNTÜ; burada `iptal`in
    `delete`e dönmesi, yani GERİ ALINAMAZ bir kayıp. İki savunma birlikte: açık RED + kaçırma."""
    casus = _yazma(monkeypatch, tmp_path)
    r = _client().post(_islem("iptal"), json={"bank": "B", "id": kimlik})
    assert r.status_code == 400, f"{kimlik!r} → {r.status_code}"
    assert casus.cagrilar == [], f"yol kaçışı upstream'e gitti: {casus.url_ler()}"


def test_islem_kimligi_kacirilarak_gider(monkeypatch, tmp_path, sandbox_state):
    """AÇIK RED TEK BAŞINA YETMEZ: reddedilmeyen ama yine de tehlikeli karakterler (`?`, `#`,
    `%`) URL'in SORGU/PARÇA sınırını kaydırabilir. Kaçırma ikinci hattır ve ölçülür."""
    casus = _yazma(monkeypatch, tmp_path,
                   **{"/operations/o%3Fx%23y": b'{"success": true}'})
    _client().post(_islem("iptal"), json={"bank": "B", "id": "o?x#y"})
    url = casus.cagrilar[0]["url"]
    assert url.endswith("/operations/o%3Fx%23y"), url


def test_islem_bank_kimligi_de_kacirilir(monkeypatch, tmp_path, sandbox_state):
    casus = _yazma(monkeypatch, tmp_path, **{"/operations/o1": b'{"success": true}'})
    _client().post(_islem("iptal"), json={"bank": "b?n", "id": "o1"})
    assert "/banks/b%3Fn/operations/o1" in casus.cagrilar[0]["url"], casus.cagrilar[0]["url"]


def test_islem_alanlari_zorunlu(monkeypatch, tmp_path, sandbox_state):
    """DÜZELTME TURU 1 (I-1): eksik/boş alan artık 200+neden DEĞİL **400**+neden.

    OKUMA UÇLARININ "F" SÖZLEŞMESİNDEN (eksik parametre 400 değil) BİLİNÇLİ SAPMA. O sözleşme
    panonun 15 sn'de bir yokladığı GET uçları içindir: eksik parametreyle gelen bir yoklama
    sayfayı karartmamalı. Burada istek pano tarafından ELLE kurulur ve eksik alan bir İSTEMCİ
    HATASIdır; 200 döndürmek onu geçici bir ölçüm arızası gibi gösterirdi ve 11-B'nin hatası
    canlıda "Hindsight cevap vermiyor" diye okunurdu. Zarf AYNI dört alandır — pano kararmaz."""
    casus = _yazma(monkeypatch, tmp_path)
    for govde in ({}, {"bank": "B"}, {"id": "o1"}, {"bank": "", "id": "o1"},
                  {"bank": "B", "id": ""}):
        r = _client().post(_islem("iptal"), json=govde)
        assert r.status_code == 400, (govde, r.status_code, r.text)
        assert r.json()["ok"] is False and _dolu(r.json()["neden"]), (govde, r.json())
    assert casus.cagrilar == [], f"eksik alanla upstream'e gidildi: {casus.url_ler()}"


@pytest.mark.parametrize("yol", ["/api/hindsight/islem/iptal", KURTAR])
def test_yazma_bozuk_json_panoyu_karartmaz(monkeypatch, tmp_path, sandbox_state, yol):
    """GET tarafında kapatılan sınıf (422 → pano kararması) POST tarafında da kapalı."""
    _yazma(monkeypatch, tmp_path)
    r = _client().post(yol, content=b"{bozuk", headers={"Content-Type": "application/json"})
    assert r.status_code == 200, r.text
    assert r.json()["ok"] is False and _dolu(r.json()["neden"]), r.json()


# ---------------------------------------------------------------------------- L-E. İZ + ZARF

@pytest.mark.parametrize("yol,govde,eylem", [
    ("/api/hindsight/islem/iptal", {"bank": "B", "id": "o1"}, "iptal"),
    ("/api/hindsight/islem/yeniden-dene", {"bank": "B", "id": "o1"}, "yeniden-dene"),
    ("/api/hindsight/islem/sil", {"bank": "B", "id": "o1"}, "sil"),
    (KURTAR, {"bank": "B"}, "konsolidasyon-kurtar"),
])
def test_yazma_deftere_iz_birakir(monkeypatch, tmp_path, sandbox_state, yol, govde, eylem):
    """v54 SÖZLEŞMESİ DAVRANIŞLA ÖLÇÜLÜR. v54 kaynak metninde `obs.log` ARAR — yani orada bir
    satır bulunması izin GERÇEKTEN atıldığını kanıtlamaz. Burada `obs.log` casuslanır ve
    ALANLAR okunur: operatörün hangi bankada hangi operasyona ne yaptığı defterde YAZILI mı."""
    _yazma(monkeypatch, tmp_path)
    satirlar: list = []
    monkeypatch.setattr(api.obs, "log", lambda olay, **alan: satirlar.append((olay, alan)))
    r = _client().post(yol, json=govde)
    assert r.status_code == 200, r.text
    izler = [a for o, a in satirlar if o == "hafiza_yazma"]
    assert len(izler) == 1, f"`hafiza_yazma` izi {len(izler)} kez atıldı: {satirlar}"
    iz = izler[0]
    assert iz["eylem"] == eylem and iz["bank"] == "B", iz
    # M-1: boole başarı alanının bu dosyadaki konvansiyonu `ok=` (5 emsal); `sonuc=` ile yazılan
    # bir satırı `ok=` ile tarayan her defter sorgusu ıskalardı.
    assert iz["ok"] is True and iz["http"] == 200, iz
    assert iz["id"] == govde.get("id"), iz


def test_yazma_izi_upstream_yolunu_ve_anahtari_TASIMAZ(monkeypatch, tmp_path, sandbox_state):
    """DEFTERE YAZILAN SIR, SIZAN SIRDIR (`session_drop` emsali, aynı dosya). İz operatörün
    eylemini anlatır; upstream URL'i ya da tenant anahtarı defterin işi DEĞİLDİR."""
    _yazma(monkeypatch, tmp_path)
    satirlar: list = []
    monkeypatch.setattr(api.obs, "log", lambda olay, **alan: satirlar.append((olay, alan)))
    _client().post(_islem("sil"), json={"bank": "B", "id": "o1"})
    metin = repr([a for o, a in satirlar if o == "hafiza_yazma"])
    assert SAHTE_ANAHTAR not in metin, f"iz satırı anahtar taşıdı: {metin}"
    assert api.HAFIZA_TABAN_URL not in metin and "/v1/default/banks" not in metin, metin


@pytest.mark.parametrize("yol,govde", [("/api/hindsight/islem/iptal", {"bank": "B", "id": "o1"}),
                                       (KURTAR, {"bank": "B"})])
def test_yazma_diag_zarfini_dusurur(monkeypatch, tmp_path, sandbox_state, yol, govde):
    """v181 SÖZLEŞMESİ DAVRANIŞLA ÖLÇÜLÜR (kaynak metni değil): operatörün AZ ÖNCE bastığı
    düğmenin sonucu 45 saniyelik teşhis zarfının arkasında kalmamalı."""
    _yazma(monkeypatch, tmp_path)
    nedenler: list = []
    monkeypatch.setattr(api, "_diag_onbellek_bosalt", lambda neden: nedenler.append(neden))
    _client().post(yol, json=govde)
    assert len(nedenler) == 1 and _dolu(nedenler[0]), nedenler


def test_yazma_basarisizken_diag_zarfi_dusmez(monkeypatch, tmp_path, sandbox_state):
    """`_diag_onbellek_bosalt`ın KENDİ sözleşmesi: YALNIZ BAŞARIDA. Düşürseydi her başarısız
    tıklama bir TAM teşhis hesabı tetiklerdi — geçersizleştirme kendi çözdüğü sorunu geri
    getirirdi."""
    _yazma(monkeypatch, tmp_path, **{"/banks/B/operations/o1": "upstream 500"})
    nedenler: list = []
    monkeypatch.setattr(api, "_diag_onbellek_bosalt", lambda neden: nedenler.append(neden))
    r = _client().post(_islem("iptal"), json={"bank": "B", "id": "o1"})
    assert r.json()["ok"] is False, r.json()
    assert nedenler == [], f"başarısız yazma teşhis zarfını düşürdü: {nedenler}"


# ---------------------------------------------------------- L-F. ÖLÇÜLEMEZLİK + SIR + YETKİ

def test_yazma_upstream_arizasi_200_ve_neden(monkeypatch, tmp_path, sandbox_state):
    """500 DEĞİL 200 + DOLU `neden` (bu bloğun kurucu sözleşmesi): pano kararmaz, düğme
    operatöre NEDEN olmadığını söyler. `http` de geçer — 404 (kayıt zaten yok) ile 500
    (upstream bozuk) operatör için AYNI şey değildir."""
    casus = _yazma(monkeypatch, tmp_path,
                   **{"/banks/B/operations/o1/retry": "upstream 500 döndü"})
    casus.ariza_http = 500
    r = _client().post(_islem("yeniden-dene"), json={"bank": "B", "id": "o1"})
    assert r.status_code == 200, r.text
    govde = r.json()
    assert govde["ok"] is False and govde["govde"] is None, govde
    assert _dolu(govde["neden"]) and govde["http"] == 500, govde


def test_yazma_http_kodu_yoksa_None_kalir(monkeypatch, tmp_path, sandbox_state):
    """UYDURMA YASAĞI'NIN BU UÇTAKİ HÂLİ: bağlantı reddinde HTTP kodu YOKTUR. `0` ya da `500`
    yazmak, ölçülmemiş bir sunucu cevabını ölçülmüş gibi gösterirdi."""
    casus = _yazma(monkeypatch, tmp_path,
                   **{"/banks/B/operations/o1": "baglanti reddedildi"})
    assert casus.ariza_http is None
    govde = _client().post(_islem("iptal"), json={"bank": "B", "id": "o1"}).json()
    assert govde["http"] is None and govde["ok"] is False and _dolu(govde["neden"]), govde


def test_yazma_anahtar_yokken_200_ve_neden(monkeypatch, tmp_path, sandbox_state):
    """`/opt/hindsight/.env` bu makinede YOKTUR — bu ucun NORMAL hâli."""
    casus = _yazma(monkeypatch, tmp_path, anahtar=None)
    r = _client().post(_islem("iptal"), json={"bank": "B", "id": "o1"})
    assert r.status_code == 200, r.text
    assert r.json()["ok"] is False and _dolu(r.json()["neden"]), r.json()
    assert casus.cagrilar == [], "anahtarsız çağrı yine de tele çıktı"


@pytest.mark.parametrize("yol,govde", [("/api/hindsight/islem/sil", {"bank": "B", "id": "o1"}),
                                       (KURTAR, {"bank": "B"})])
def test_yazma_sir_gonderilir_ama_sizmaz(monkeypatch, tmp_path, sandbox_state, yol, govde):
    """VAKUM DEĞİL: gönderilmemiş bir sırrın yanıtta olmaması hiçbir şey kanıtlamaz. İki şey
    birlikte — (a) `Authorization: Bearer <anahtar>` GERÇEKTEN gitti, (b) yanıtta yok."""
    casus = _yazma(monkeypatch, tmp_path)
    r = _client().post(yol, json=govde)
    assert SAHTE_ANAHTAR not in r.text, "tenant anahtarı yanıta sızdı"
    cagri = casus.cagrilar[0]
    assert cagri["basliklar"].get("Authorization") == f"Bearer {SAHTE_ANAHTAR}", cagri["basliklar"]
    assert cagri["sir"] == SAHTE_ANAHTAR, "yazma bacağı maskeleyiciye sırrı VERMEDİ — ikinci hat kör"


def test_yazma_ariza_metnindeki_sir_maskelenir(monkeypatch, tmp_path, sandbox_state):
    """İKİNCİ SAVUNMA HATTI: alt katman kimlik bilgisini istisna metnine basarsa gerekçe
    SİLİNMEZ (körlük açardı), yalnız sır maskelenir."""
    _yazma(monkeypatch, tmp_path,
           **{"/banks/B/operations/o1":
              f"OSError: baglanti reddedildi (Bearer {SAHTE_ANAHTAR})"})
    govde = _client().post(_islem("iptal"), json={"bank": "B", "id": "o1"}).json()
    assert SAHTE_ANAHTAR not in json.dumps(govde), govde
    assert "OSError" in govde["neden"], govde


@pytest.mark.parametrize("yol,govde", [("/api/hindsight/islem/iptal", {"bank": "B", "id": "o1"}),
                                       (KURTAR, {"bank": "B"})])
def test_yazma_auth_cagiriyor(monkeypatch, tmp_path, sandbox_state, yol, govde):
    _yazma(monkeypatch, tmp_path)
    cagrildi: list = []
    monkeypatch.setattr(api, "_auth", lambda request: cagrildi.append(1))
    r = _client().post(yol, json=govde)
    assert r.status_code == 200, r.text
    assert cagrildi == [1], f"`{yol}`: `_auth` çağrılmadı — yazma yüzeyi yetkisiz açık"


@pytest.mark.parametrize("yol,govde,jetonlu_kod", [
    ("/api/hindsight/islem/iptal", {"bank": "B", "id": "o1"}, 200),
    ("/api/hindsight/islem/yok", {"bank": "B", "id": "o1"}, 404),
    (KURTAR, {"bank": "B"}, 200),
    (TETIKLE, {"bank": "B"}, 200),
])
def test_yazma_jetonsuz_401(monkeypatch, tmp_path, sandbox_state, yol, govde, jetonlu_kod):
    """GERÇEK kapı (`_auth` casuslanmadan). TANINMAYAN EYLEM DE LİSTEDE, bilerek: sözlük
    kontrolü yetkiden ÖNCE koşsaydı, kimliksiz bir çağıran hangi eylemlerin var olduğunu
    404/401 farkından okuyabilirdi (vokabüler sızıntısı).

    DÜZELTME TURU 1 (M-4a/b): iki gevşeklik kapandı. (a) 401 dalında `cagrilar == []` de ölçülür —
    "401 döndü ama upstream'e de gitti" sapması eskiden görünmezdi. (b) jetonlu çağrının NE
    döndüğü artık parametrede YAZILI; `in (200, 400, 404)` yalnız "401 değil"i ölçüyordu."""
    casus = _yazma(monkeypatch, tmp_path)
    monkeypatch.setattr(api, "DASH_TOKEN", "v375-pano-jetonu")
    monkeypatch.setattr(api.auth, "password_set", lambda: False)
    assert _client().post(yol, json=govde).status_code == 401, yol
    assert casus.cagrilar == [], f"401 döndü ama upstream'e gidildi: {casus.url_ler()}"
    r = _client().post(yol, json=govde, headers={"x-meridian-token": "v375-pano-jetonu"})
    assert r.status_code == jetonlu_kod, r.text


# ------------------------------------------------------- L-G. ÇEKİRDEK: DELEGASYON + DURUM

def test_yaz_bacagi_ortak_cekirdege_delege_eder(monkeypatch, tmp_path, sandbox_state):
    """ÜÇÜNCÜ BACAK DA KOPYA DEĞİL SARMALAYICI (kardeşlerinin dersi). Kopya olsaydı
    `_kapi_istek`teki her düzeltme (yeniden deneme, `Retry-After`, başlık politikası) yazma
    bacağında SESSİZCE eksik kalırdı."""
    cagrilar: list = []

    def _sahte_cekirdek(url, basliklar, sir, *, govde=None, yontem="GET", durum=None):
        cagrilar.append({"url": url, "govde": govde, "yontem": yontem})
        if durum is not None:
            durum["http"] = 204
        return b'{"ok": true}', None

    monkeypatch.setattr(api, "_kapi_istek", _sahte_cekirdek)
    kutu: dict = {}
    assert GERCEK_HAFIZA_YAZ_ISTEK("http://x/3", {"A": "b"}, "s", yontem="DELETE",
                                   durum=kutu) == (b'{"ok": true}', None)
    assert cagrilar == [{"url": "http://x/3", "govde": None, "yontem": "DELETE"}], cagrilar
    assert kutu == {"http": 204}, kutu


def test_yaz_bacagi_gercek_DELETE_gonderir_ve_zaman_asimli(monkeypatch, tmp_path, sandbox_state):
    """DAVRANIŞ ÇİVİSİ (`_hafiza_post`un kardeşi): `urlopen`e GERÇEKTEN `DELETE` ve sözleşmenin
    beyan ettiği zaman aşımı gidiyor mu. Zaman aşımsız bir yazma çağrısı, operatör düğmeye
    bastığında panoyu SONSUZA kadar asardı."""
    gorulen: dict = {}

    class _Sahte:
        status = 200

        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self): return b'{"success": true}'

    def _sahte_urlopen(istek, timeout=None):
        gorulen["timeout"] = timeout
        gorulen["method"] = istek.get_method()
        return _Sahte()

    import urllib.request
    monkeypatch.setattr(urllib.request, "urlopen", _sahte_urlopen)
    kutu: dict = {}
    veri, neden = GERCEK_HAFIZA_YAZ_ISTEK("http://127.0.0.1:8888/x", {"Authorization": "Bearer y"},
                                          "y", yontem="DELETE", durum=kutu)
    assert (veri, neden) == (b'{"success": true}', None)
    assert gorulen["method"] == "DELETE", gorulen
    assert gorulen["timeout"] == api.KAPI_ZAMAN_ASIMI_S == api.HAFIZA_ZAMAN_ASIMI_S, gorulen
    assert kutu == {"http": 200}, kutu


def test_yaz_bacagi_HTTPError_kodunu_olcer(monkeypatch, tmp_path, sandbox_state):
    """`http` ALANI UYDURULMADI, ÖLÇÜLDÜ: `urlopen` 4xx/5xx'te `HTTPError` atar ve kodu
    `.code`tadır. Kodu `neden` metninden AYRIŞTIRMAK (regex) kırılgan olurdu ve upstream'in
    hata cümlesi değiştiği gün pano sessizce yanlış kod gösterirdi."""
    import urllib.error
    import urllib.request

    def _patlat(istek, timeout=None):
        raise urllib.error.HTTPError("http://x", 409, "Conflict", {}, None)

    monkeypatch.setattr(urllib.request, "urlopen", _patlat)
    kutu: dict = {}
    veri, neden = GERCEK_HAFIZA_YAZ_ISTEK("http://x", {}, None, yontem="POST", durum=kutu)
    assert veri is None and _dolu(neden), neden
    assert kutu == {"http": 409}, kutu


def test_yaz_bacagi_ag_arizasinda_kod_uydurmaz(monkeypatch, tmp_path, sandbox_state):
    import urllib.request

    def _patlat(istek, timeout=None):
        raise OSError("baglanti reddedildi")

    monkeypatch.setattr(urllib.request, "urlopen", _patlat)
    kutu: dict = {}
    veri, neden = GERCEK_HAFIZA_YAZ_ISTEK("http://x", {}, None, yontem="DELETE", durum=kutu)
    assert veri is None and "OSError" in neden, neden
    assert kutu == {"http": None}, f"HTTP kodu olmayan arızaya kod uyduruldu: {kutu}"


def test_okuma_bacaklari_durum_kutusu_istemez():
    """SARMALAYICILAR BOZULMADI (v361 yeşil kalmalı): `durum` KELİMESİ-ANAHTARLI ve
    VARSAYILANI `None` — eski iki sarmalayıcının imzası ve davranışı DEĞİŞMEDİ."""
    import inspect
    imza = inspect.signature(api._kapi_istek).parameters["durum"]
    assert imza.kind is inspect.Parameter.KEYWORD_ONLY and imza.default is None, imza
    for ad in ("_kapi_getir", "_hafiza_post"):
        assert "durum" not in inspect.signature(GERCEK_KAPI_GETIR if ad == "_kapi_getir"
                                                else GERCEK_HAFIZA_POST).parameters, ad


# =================================================================================================
# L-H … L-K. DÜZELTME TURU 1 (inceleme: I-1 · I-2 · I-3 · I-4 · M-2 · R30-ek `tetikle`)
# =================================================================================================

# ---------------------------------------------------- L-H. TİP DUVARI + BANK DUVARI (I-1, I-2)
#
# İNCELEMENİN ÖLÇTÜĞÜ ŞEY (saf stdlib, pytest'siz): duvarlar TİP KÖRÜYDÜ.
#   `{"id": 123}`      → `"/" in 123`            → TypeError → yakalanmamış → **500**
#   `{"id": ["../x"]}` → `"/" in ["../x"]`       → False, yani duvar "GÜVENLİ" diyordu;
#                        sonra `_hafiza_kacir([...])` → TypeError → **500**
#   `{"bank": {...}}`  → `bank` için duvar ZATEN YOKTU → `_hafiza_kacir` → **500**
# İki şey birden bozuktu: (a) "bozuk istek panoyu KARARTMAZ" sözleşmesi (500 = kararma),
# (b) duvar-2'nin güvencesi bir TİP TESADÜFÜNE yaslanıyordu — `["../x"]` bugün kaçırıcıda
# patlıyor diye güvenli değildi, yalnız ŞANSLIYDI.

#: (alan, değer, beklenen ret sınıfı). TEK yardımcı iki alana da uygulanır (I-2): duvarın
#: BEYAN EDİLMİŞ gerekçesi ("`%2F`yi rotalamadan ÖNCE çözen ara katman") `bank` için de aynen
#: geçerli — gerekçe doğruysa duvar yarım olamaz, yanlışsa duvar gereksiz olurdu.
#: DÜZELTME TURU 3 (Rol-1 hükmü 2026-09-03): `/` ARTIK REDDEDİLMEZ — bu depodaki belge
#: kimlikleri REPO YOLUdur ve tur 2'nin `/` yasağı bütün belgeleri kırdı (regresyon, ölçüm
#: `api.py::_hafiza_yol_parcasi_guvenli` docstring'inde). Tablodan `o1/delete` ve
#: `b/operations/o1/delete` bu yüzden ÇIKARILDI: ikisi de artık MEŞRU kimlik biçimidir ve
#: onları burada tutmak, düzeltilmiş kuralın tersini çivilemek olurdu. Yerine traversal'ın
#: GERÇEK yolları ve boş-segment sınıfı geldi.
YOL_PARCASI_RETLERI = (
    ("id", 123, "alan_tipi"),
    ("id", ["../x"], "alan_tipi"),
    ("id", {"a": 1}, "alan_tipi"),
    ("id", None, "alan_tipi"),
    ("id", True, "alan_tipi"),
    ("id", "", "alan_bos"),
    ("id", "../../v1/default/banks/x/operations/y", "yol_kacisi"),   # baştaki `../`
    ("id", "docs/../../stats", "yol_kacisi"),                        # ortadaki `/../`
    ("id", "docs/..", "yol_kacisi"),                                 # sondaki `/..`
    ("id", "..", "yol_kacisi"),                                      # tek başına
    ("id", "%2E%2E", "yol_kacisi"),                                  # çift kodlama
    ("id", "docs//x.md", "bos_segment"),                             # boş segment
    ("id", "/docs/x.md", "bos_segment"),                             # baştaki `/`
    ("id", "docs/x.md/", "bos_segment"),                             # sondaki `/`
    ("id", "o 1", "alan_boslugu"),
    ("id", "o\t1", "alan_boslugu"),
    ("id", "o\x00 1", "alan_boslugu"),                                # kontrol karakteri
    ("bank", 123, "alan_tipi"),
    ("bank", {"a": 1}, "alan_tipi"),
    ("bank", None, "alan_tipi"),
    ("bank", "", "alan_bos"),
    ("bank", "..", "yol_kacisi"),
    ("bank", "../x", "yol_kacisi"),
    ("bank", "b%2Fc", "yol_kacisi"),
    ("bank", "b n", "alan_boslugu"),
)


@pytest.mark.parametrize("alan,deger,sinif", YOL_PARCASI_RETLERI)
def test_yol_parcasi_duvari_iki_alana_da_uygulanir(monkeypatch, tmp_path, sandbox_state,
                                                   alan, deger, sinif):
    """400 + dolu neden + upstream'e HİÇ gitmeme — üçü birlikte. Yalnız "500 değil"i ölçen bir
    çivi, sessizce upstream'e giden bir sapmayı göremezdi."""
    casus = _yazma(monkeypatch, tmp_path)
    govde = {"bank": "B", "id": "o1"}
    govde[alan] = deger
    r = _client().post(_islem("iptal"), json=govde)
    assert r.status_code == 400, f"{alan}={deger!r} → {r.status_code}: {r.text[:200]}"
    g = r.json()
    assert g == {"ok": False, "http": None, "govde": None, "neden": g["neden"]}, g
    assert _dolu(g["neden"]), g
    assert casus.cagrilar == [], f"{alan}={deger!r} upstream'e gitti: {casus.url_ler()}"


@pytest.mark.parametrize("deger", [123, {"a": 1}, "", "..", "b/../c", "b//c", "b n"])
def test_konsolidasyon_bank_duvari_da_ayni(monkeypatch, tmp_path, sandbox_state, deger):
    """AYNI YARDIMCI, AYNI DUVAR — ikinci rota unutulursa burada öter.

    DÜZELTME TURU 3: `b/c` listeden ÇIKTI, çünkü artık MEŞRU bir banka biçimidir (kural bank
    ile kimlikler için AYNI ve `/` traversal değildir). Yerine traversal'ın gerçek yolu
    (`b/../c`) ve boş segment (`b//c`) geldi."""
    casus = _yazma(monkeypatch, tmp_path)
    r = _client().post(KURTAR, json={"bank": deger})
    assert r.status_code == 400, f"{deger!r} → {r.status_code}: {r.text[:200]}"
    assert casus.cagrilar == [], f"{deger!r} upstream'e gitti: {casus.url_ler()}"


def test_yol_parcasi_duvari_TEK_yardimcidir():
    """TEK KAYNAK, DAVRANIŞLA: yardımcı casuslanır ve İKİ rotanın da ondan geçtiği ölçülür.
    Kaynak metni taramak (iki çağrı var mı) beyanı ölçerdi; bu, gerçek çağrıyı ölçer."""
    assert callable(api._hafiza_yol_parcasi_guvenli)
    # Yardımcının KENDİSİ: sözleşmesi `(neden, sinif)` ve güvenlide ikisi de `None`.
    assert api._hafiza_yol_parcasi_guvenli("id", "o1") == (None, None)
    neden, sinif = api._hafiza_yol_parcasi_guvenli("bank", 5)
    assert sinif == "alan_tipi" and _dolu(neden) and "bank" in neden, (neden, sinif)


@pytest.mark.parametrize("yol,govde", [("/api/hindsight/islem/iptal", {"bank": "B", "id": "o1"}),
                                       (KURTAR, {"bank": "B"})])
def test_iki_rota_da_yol_parcasi_yardimcisini_cagirir(monkeypatch, tmp_path, sandbox_state,
                                                      yol, govde):
    _yazma(monkeypatch, tmp_path)
    gorulen: list = []

    def _casus(ad, deger):
        gorulen.append(ad)
        return None, None

    monkeypatch.setattr(api, "_hafiza_yol_parcasi_guvenli", _casus)
    assert _client().post(yol, json=govde).status_code == 200
    assert "bank" in gorulen, f"{yol}: `bank` duvardan geçmedi ({gorulen})"


# --------------------------------------------------------------- L-I. TEK KAYNAK (I-3 a + b)

def test_bank_yolu_TEK_kaynaktan_kurulur(monkeypatch, tmp_path, sandbox_state):
    """(a) OKUMA, YAZMA ve RECALL bacakları AYNI URL kurucusunu çağırır. Kopya kalsaydı kaçırma
    politikasındaki bir düzeltme (örn. `~` ya da `%` kuralı) yazan bacakta SESSİZCE eski
    politikada kalırdı — ve bu bacakta "başka bir uca gitmek" `iptal` yerine `sil` demektir.
    Bu turun KENDİ dersi buydu (`_hafiza_post` kopyası `_kapi_istek`e çıkarılmıştı).

    ÜÇÜNCÜ BACAK 2026-09-03'te KATILDI (nihai inceleme Ö1): `_hafiza_recall` URL'i kökten ELLE
    kuruyordu, yani `bank` duvarı okuma+yazmaya taşındığında recall'a GELMEZDİ ve "duvar tek
    boğazda" cümlesi doğduğu gün yarım olurdu."""
    _yazma(monkeypatch, tmp_path)
    gorulen: list = []
    gercek = api._hafiza_bank_yolu

    def _casus(bank, kuyruk="", kimlikler=()):
        gorulen.append((bank, kuyruk, kimlikler))
        return gercek(bank, kuyruk, kimlikler)

    monkeypatch.setattr(api, "_hafiza_bank_yolu", _casus)
    _client().get("/api/hindsight/islemler?bank=B")           # OKUMA bacağı
    _client().post(_islem("sil"), json={"bank": "B", "id": "o1"})   # YAZMA bacağı
    _client().post(RECALL, json={"bank": "B", "query": "alice"})    # RECALL bacağı
    assert [g[1] for g in gorulen] == [
        "/operations", "/operations/{}/delete", "/memories/recall"], gorulen


def test_bank_yolu_kacirmayi_kendisi_yapar():
    """Kurucunun SÖZLEŞMESİ: `(yol, neden)` — kök + kaçırılmış bank + kaçırılmış kimliklerle
    doldurulmuş kuyruk; ve KİRLİ `bank`ta yol YOK, gerekçe VAR (nihai inceleme Ö1). Yalnız
    başarı dalını ölçen bir çivi, duvarın sessizce kaldırılmasını göremezdi."""
    assert api._hafiza_bank_yolu("b.n", "/operations/{}", ("o.1",)) == (
        f"{api._HAFIZA_BANK_KOKU}/b%2En/operations/o%2E1", None)
    yol, neden = api._hafiza_bank_yolu("../x", "/operations")
    assert yol is None and _dolu(neden) and "bank" in neden, (yol, neden)


def test_istek_govdesi_okuyucusu_TEK_kaynaktan(monkeypatch, tmp_path, sandbox_state):
    """(b) `recall` satır-içi kopyasını korumuştu; I-1'in düzeltmesi İKİ yerde yapılmak zorunda
    kalacaktı. Artık tek okuyucu — ve recall'ın davranışı DEĞİŞMEDİ (kardeş çiviler yeşil)."""
    _yazma(monkeypatch, tmp_path)
    gorulen: list = []
    gercek = api._hafiza_istek_govdesi

    async def _casus(request, alanlar):
        gorulen.append(tuple(alanlar))
        return await gercek(request, alanlar)

    monkeypatch.setattr(api, "_hafiza_istek_govdesi", _casus)
    _client().post(RECALL, json={"bank": "B", "query": "alice"})
    _client().post(_islem("iptal"), json={"bank": "B", "id": "o1"})
    _client().post(KURTAR, json={"bank": "B"})
    assert gorulen == [("bank", "query"), ("bank", "id"), ("bank",)], gorulen


# ------------------------------------------------------------------- L-J. RET İZİ (I-4)
#
# "OPERATÖRÜN BASTIĞI HER DÜĞME DEFTERE DÜŞER" BEYANI YARIMDI: iz yalnız upstream'e ULAŞAN
# çağrılar için atılıyordu. `..` içeren bir `id` denemesi bu yüzeyde bir SONDA denemesidir ve tam
# olarak defterde görmek isteyeceğin şeydir; hiçbir yerde görünmüyordu. v54 bunu yakalayamaz —
# rota bloğunda `obs.log` METNİNİ görüp geçer.

#: (yol, gövde, beklenen sınıf). Dört ret dalı da temsil edilir.
RET_DALLARI = (
    ("/api/hindsight/islem/yok", {"bank": "B", "id": "o1"}, "eylem_taninmiyor"),
    ("/api/hindsight/islem/iptal", [1, 2], "govde_cozulemedi"),
    ("/api/hindsight/islem/iptal", {"bank": "B"}, "alan_tipi"),
    ("/api/hindsight/islem/iptal", {"bank": "B", "id": "../x"}, "yol_kacisi"),
    ("/api/hindsight/konsolidasyon/yok", {"bank": "B"}, "eylem_taninmiyor"),
    ("/api/hindsight/konsolidasyon/kurtar", {"bank": ".."}, "yol_kacisi"),
)


@pytest.mark.parametrize("yol,govde,sinif", RET_DALLARI)
def test_reddedilen_yazma_da_deftere_dusar(monkeypatch, tmp_path, sandbox_state,
                                           yol, govde, sinif):
    _yazma(monkeypatch, tmp_path)
    satirlar: list = []
    monkeypatch.setattr(api.obs, "log", lambda olay, **alan: satirlar.append((olay, alan)))
    _client().post(yol, json=govde)
    retler = [a for o, a in satirlar if o == "hafiza_yazma_red"]
    assert len(retler) == 1, f"ret izi {len(retler)} kez atıldı: {satirlar}"
    assert retler[0]["sinif"] == sinif, retler[0]


def test_ret_izi_HAM_DEGER_tasimaz(monkeypatch, tmp_path, sandbox_state):
    """SEL VE SIZINTI RİSKİ: ret dalı kimliksiz değil ama yine de istemci-tetiklidir. Deftere
    ham dize yazmak, bir sondacıya kanıt defterine SINIRSIZ metin yazdırma imkânı verirdi
    (`/api/logout`un v54'te beyan edilmiş gerekçesinin aynısı). Sınıf + tip + uzunluk yeter."""
    _yazma(monkeypatch, tmp_path)
    satirlar: list = []
    monkeypatch.setattr(api.obs, "log", lambda olay, **alan: satirlar.append((olay, alan)))
    zehir = "../../etc/passwd-COK-OZEL-DIZGE"
    _client().post(_islem("iptal"), json={"bank": "B", "id": zehir})
    _client().post(_islem("SONDA-EYLEMI-COK-OZEL"), json={"bank": "B", "id": "o1"})
    metin = repr([a for o, a in satirlar if o == "hafiza_yazma_red"])
    assert zehir not in metin and "SONDA-EYLEMI" not in metin, f"ret izi ham değer taşıdı: {metin}"
    assert "uzunluk" in metin and "sinif" in metin, metin


def test_ret_izi_tanimayan_eylemde_eylem_alanini_UYDURMAZ(monkeypatch, tmp_path, sandbox_state):
    """`eylem` KAPALI SÖZLÜĞÜN anahtarıdır. Tanınmayan bir eylemde o alan `None` olmalı —
    istemcinin verdiği dizgeyi oraya yazmak, ham değeri kapı arkasından deftere sokardı."""
    _yazma(monkeypatch, tmp_path)
    satirlar: list = []
    monkeypatch.setattr(api.obs, "log", lambda olay, **alan: satirlar.append((olay, alan)))
    _client().post(_islem("yok"), json={"bank": "B", "id": "o1"})
    ret = [a for o, a in satirlar if o == "hafiza_yazma_red"][0]
    assert ret["eylem"] is None and ret["sinif"] == "eylem_taninmiyor", ret
    _client().post(_islem("sil"), json={"bank": "B", "id": "../x"})
    ret2 = [a for o, a in satirlar if o == "hafiza_yazma_red"][1]
    assert ret2["eylem"] == "sil", ret2       # tanınan eylem YAZILIR: sözlükten gelir, hamdan değil


# ------------------------------------------------------------------- L-K. `ok` SÖZLEŞMESİ (M-2)

def test_ok_cevap_cozuldu_VE_2xx_demektir(monkeypatch, tmp_path, sandbox_state):
    """İNCELEMENİN M-2'Sİ: `ok` iki gerçeği birleştiriyordu. Upstream yazmayı YAPIP çözülemez bir
    gövde döndürürse pano `ok:false` görür ve operatör TEKRAR basar — `sil`de bu ikinci bir
    geri-alınamaz çağrıdır. Ayrım UCUZ çünkü `http` zaten ölçülüyor: `ok:false` + `http:200`
    "çağrı gitti, cevabı çözemedim" demektir ve UI bunu "olmadı" diye çizemez."""
    casus = _yazma(monkeypatch, tmp_path, **{"/banks/B/operations/o1": b"{bu json degil"})
    casus.ariza_http = 200
    g = _client().post(_islem("iptal"), json={"bank": "B", "id": "o1"}).json()
    assert g["ok"] is False and _dolu(g["neden"]), g
    assert g["http"] == 200, f"çağrının GİTTİĞİ bilgisi kayboldu: {g}"


def test_ok_2xx_DISINDA_dogru_olamaz(monkeypatch, tmp_path, sandbox_state):
    """Sözleşmenin ÖTEKİ yarısı: gövde çözülse bile 2xx olmayan bir cevap başarı değildir."""
    casus = _yazma(monkeypatch, tmp_path)
    casus.basari_http = 302
    g = _client().post(_islem("iptal"), json={"bank": "B", "id": "o1"}).json()
    assert g["ok"] is False and g["http"] == 302, g


# --------------------------------------------------- L-L. KONSOLİDASYON SÖZLÜĞÜ (R30-ek)

def test_konsolidasyon_eylem_sozlugu_olculen_upstreamle_ayrismaz():
    olculen = {eylem: (fiil, parca.split("/banks/B", 1)[1], beyaz)
               for eylem, fiil, parca, beyaz in KONSOLIDASYON_EYLEMLERI}
    kodun = {eylem: (fiil, kuyruk, beyaz)
             for eylem, (fiil, kuyruk, beyaz) in api._HAFIZA_KONSOLIDASYON_EYLEMLERI.items()}
    assert kodun == olculen, f"konsolidasyon sözlüğü ölçümle ayrıştı: {kodun} ≠ {olculen}"


def test_kurtar_yolu_AYNEN_calisir(monkeypatch, tmp_path, sandbox_state):
    """R30-ek'in KOŞULU: `{eylem}` desenine geçiş, 11-B'nin yazacağı `/konsolidasyon/kurtar`
    yolunu KIRMAMALI. Yol değişikliğinin maliyeti bugün sıfır çünkü tüketen istemci yok — ama
    yolun kendisi sözleşmedir ve burada kilitlenir."""
    casus = _yazma(monkeypatch, tmp_path)
    r = _client().post("/api/hindsight/konsolidasyon/kurtar", json={"bank": "B"})
    assert r.status_code == 200, r.text
    assert r.json()["govde"] == KURTAR_ORNEK, r.json()
    assert casus.cagri("/consolidation/recover")["fiil"] == "POST"


@pytest.mark.parametrize("eylem,fiil,parca,beyaz", KONSOLIDASYON_EYLEMLERI)
def test_konsolidasyon_dogru_fiil_ve_yola_gider(monkeypatch, tmp_path, sandbox_state,
                                                eylem, fiil, parca, beyaz):
    casus = _yazma(monkeypatch, tmp_path)
    r = _client().post(_konsolidasyon(eylem), json={"bank": "B"})
    assert r.status_code == 200, r.text
    cagri = casus.cagri(parca)
    assert cagri["fiil"] == fiil and cagri["url"].endswith(parca), cagri
    assert r.json()["govde"] == _YAZMA_GOVDELER[parca], r.json()


@pytest.mark.parametrize("eylem", ["yok", "recover", "consolidate", "KURTAR", "../sil"])
def test_konsolidasyon_taninmayan_eylem_upstreame_gitmez(monkeypatch, tmp_path, sandbox_state,
                                                         eylem):
    casus = _yazma(monkeypatch, tmp_path)
    r = _client().post(_konsolidasyon(eylem), json={"bank": "B"})
    assert r.status_code in (400, 404), f"{eylem!r} → {r.status_code}"
    assert casus.cagrilar == [], f"tanınmayan eylem upstream'e gitti: {casus.url_ler()}"


def test_tetikle_beyaz_listesi_DOLU_olculdu(monkeypatch, tmp_path, sandbox_state):
    """DÖRDÜN BOŞLUĞU BEŞİNCİSİ İÇİN KANIT DEĞİLDİ (inceleme kalemi, ölçüldü): `/consolidate`in
    `requestBody`si VAR — `ConsolidationRequest`, tek alan `observation_scopes` (nullable
    array-of-array-of-string). Beyaz liste bu kez DOLU ve KAPALI: şemada olmayan hiçbir alan
    geçmez. Şeklin KENDİSİ upstream'e bırakılır (422 → `neden`); beyaz liste güvenlik sınırıdır,
    şema doğrulayıcısı değil — uydurulmuş bir doğrulama, ölçülmemiş bir kısıtı ölçülmüş gibi
    gösterirdi."""
    casus = _yazma(monkeypatch, tmp_path)
    _client().post(TETIKLE, json={"bank": "B", "observation_scopes": [["a", "b"]],
                                  "force": True, "id": "o1", "limit": 9})
    coz = json.loads(casus.cagri("/banks/B/consolidate")["govde"].decode())
    assert coz == {"observation_scopes": [["a", "b"]]}, coz


def test_tetikle_istemci_sormadikca_govde_HIC_gitmez(monkeypatch, tmp_path, sandbox_state):
    """`recall`ın `max_tokens` dersi (düzeltme turu 1, M-7) burada da geçerli: upstream'in
    `requestBody`si ZORUNLU DEĞİL ve CP de gövdesiz çağırıyor (`lib/api.ts::triggerConsolidation`).
    Boş bir `{}` göndermek, upstream'in kendi varsayılanını sessizce EZEBİLİRDİ."""
    casus = _yazma(monkeypatch, tmp_path)
    _client().post(TETIKLE, json={"bank": "B"})
    assert casus.cagri("/banks/B/consolidate")["govde"] is None, "istemci sormadan gövde gitti"


def test_kurtar_hala_govdesiz_gider(monkeypatch, tmp_path, sandbox_state):
    """`tetikle` gövde alıyor diye `kurtar` da almaya BAŞLAMAMALI — sözlükteki beyaz liste
    eylem BAŞINA ölçüldü."""
    casus = _yazma(monkeypatch, tmp_path)
    _client().post(KURTAR, json={"bank": "B", "observation_scopes": [["a"]]})
    assert casus.cagri("/consolidation/recover")["govde"] is None


def test_tetikle_govde_dali_json_baslikli_gider(monkeypatch, tmp_path, sandbox_state):
    """M-3 KAPANDI: `_hafiza_yaz`ın `govde` dalı ölü ve çivisizdi; `tetikle` onun İLK kullanıcısı.
    Dal `Content-Type` politikası taşıyor ve o politika artık ölçülü."""
    casus = _yazma(monkeypatch, tmp_path)
    _client().post(TETIKLE, json={"bank": "B", "observation_scopes": [["a"]]})
    basliklar = casus.cagri("/banks/B/consolidate")["basliklar"]
    assert basliklar.get("Content-Type") == "application/json", basliklar
    assert basliklar.get("Authorization") == f"Bearer {SAHTE_ANAHTAR}", basliklar


# =================================================================================================
# N. NİHAİ DAL DÜZELTMESİ (2026-09-03) — inceleme Ö1/Ö2/Ö4/Ö5 + K1/K2/K5/K7 + CSRF + A12
# =================================================================================================
#
# BU BÖLÜMÜN ORTAK DERSİ TEKTİR: bir yardımcı/şerh MUTLAK konuşuyor, ikinci çağıran onu
# daraltıyor, daraltma yalnız İKİNCİ çağıranda yazılı kalıyor. İnceleme beş kalemin beşini de
# aynı desende buldu. Buradaki çiviler beyanı değil DAVRANIŞI zorlar — beyanın kendisini
# zorlayanlar (bayat şerh, kapsam listesi) ayrıca ve ADIYLA işaretli.


# ---------------------------------------------------------------- A1. BANK DUVARI TEK BOĞAZDA ---

#: Duvarın ısırması gereken bacaklar — ROTA ÜZERİNDEN ölçülebilenler. YAZMA BACAĞI BU
#: TABLODA YOK VE BU BİR ÖLÇÜM SONUCUDUR (düzeltme turu 2, Y-6): `/api/hindsight/islem/*`
#: rotasında ret `_hafiza_yazma_girdisi`nin duvarından gelir ve istek `_hafiza_yaz`a HİÇ
#: ULAŞMAZ — yani `_hafiza_bank_yolu`daki duvar silinse bile o parametre YEŞİL kalırdı
#: (çivi kendi kapsadığını sanırdı). Yazma bacağı ayrı çivide, yardımcıyı DOĞRUDAN çağırarak
#: ölçülür (`test_bank_duvari_YAZMA_bacaginda_da_isirir`).
BANK_DUVARI_BACAKLARI = (
    ("get", "/api/hindsight/varliklar?bank=..%2F..%2Fstats", None),
    ("post", "/api/hindsight/recall", {"bank": "../../x", "query": "alice"}),
)


@pytest.mark.parametrize("fiil,yol,govde", BANK_DUVARI_BACAKLARI)
def test_bank_duvari_UC_BACAKTA_da_isirir(monkeypatch, tmp_path, sandbox_state, fiil, yol, govde):
    """Ö1 HÜKMÜ (b): duvar YARIM OLAMAZ — `_hafiza_yol_parcasi_guvenli` `bank`a da uygulanır ve
    uygulama yeri TEK BOĞAZdır (`_hafiza_bank_yolu`), üç bacağın üçünde birden.

    ÖLÇÜLMÜŞ GEREKÇE: uvicorn `scope["path"]`i rotalamadan ÖNCE `unquote` eder (`h11_impl` ve
    `httptools_impl` aynı satırı taşır: `path = unquote(raw_path)`), ve upstream Hindsight de
    uvicorn üstünde koşar — yani `%2F` bizim kaçırmamızdan sonra ARA KATMANDA `/`ye döner.
    Kaçırma TEK BAŞINA bir yol-parçası duvarı DEĞİLDİR. Duvar bu yüzden kaçırmanın YANINDA
    durur, yerine değil.

    İKİ ŞEY DEĞİŞMEZ: gerekçe DOLU ve upstream'e HİÇ çağrı ÇIKMAZ. Yazma bacağı bu tabloda
    DEĞİL — gerekçesi tablonun başında yazılı (Y-6) ve kardeş çivide ölçülüyor."""
    casus = _yazma(monkeypatch, tmp_path)
    cl = _client()
    r = cl.get(yol) if fiil == "get" else cl.post(yol, json=govde)
    assert r.status_code in (200, 400), f"{yol}: {r.status_code} — pano kararacak bir kod döndü"
    g = r.json()
    assert g.get("govde") is None, g
    assert _dolu(g.get("neden")), g
    assert casus.cagrilar == [], f"{yol}: kirli `bank` ile upstream'e gidildi: {casus.url_ler()}"


#: ÖLÇÜLMÜŞ GERÇEK BELGE KİMLİĞİ (A1, 2026-09-03 02:31Z — Rol-1 ölçümü). Hindsight'taki
#: belge kimlikleri REPO YOLUdur: içe alma betiği `document_id`yi repo yoluna eşitliyor.
#: Bu sabit bir FIXTURE değil bir KAYITtır: tur 2'nin "`/` reddedilir" kuralı tam olarak bu
#: biçimi kırdı ve `/belge-parcalari` (Belgeler çekmecesi) her belgede boş döndü.
GERCEK_BELGE_KIMLIGI = "research/cards/EDG-2026-037-tca-gercek-friksiyon.yaml"


def test_SLASH_iceren_MESRU_belge_kimligi_GECER(monkeypatch, tmp_path, sandbox_state):
    """DÜZELTME TURU 3 — REGRESYON ÇİVİSİ (Rol-1 hükmü 2026-09-03).

    Tur 2 duvarı bütün kimliklere yaydı ve kural o gün `/`yi de reddediyordu. ÖLÇÜM bunun
    yanlış olduğunu gösterdi: belge kimlikleri repo yoludur ve upstream
    `documents/{document_id}/chunks` onu HEM `%2F` kaçırılmış (200) HEM ham `/` (200) ile
    kabul ediyor. Yani yasak, güvenlik kazancı olmadan yüzeyi kırıyordu — traversal `/` ile
    değil `..` ile yapılır ve o hâlâ reddediliyor (kardeş çiviler).

    İKİ ŞEY BİRLİKTE ÖLÇÜLÜR: (1) çağrı GERÇEKTEN çıkıyor (yoksa çivi vakumda koşardı) ve
    (2) kimlik upstream PATH'ine KAÇIRILARAK giriyor — yani `/` "izinli" olmak ham geçmek
    DEĞİLDİR; kaçırma politikası (`_hafiza_kacir`, `safe=""`) aynen duruyor."""
    import urllib.parse
    kacirilmis = urllib.parse.quote(GERCEK_BELGE_KIMLIGI, safe="").replace(".", "%2E")
    casus = _cpui(monkeypatch, tmp_path,
                  **{f"/documents/{kacirilmis}/chunks": json.dumps(PARCALAR_ORNEK).encode()})
    r = _client().get(f"/api/hindsight/belge-parcalari?bank=B"
                      f"&belge={urllib.parse.quote(GERCEK_BELGE_KIMLIGI, safe='')}")
    assert r.status_code == 200, r.text
    g = r.json()
    assert g["neden"] is None and g["govde"] == PARCALAR_ORNEK, g
    assert casus.cagrilar, "meşru belge kimliği duvarda kesildi — çivi vakumda koşmadı, KIRILDI"
    url = casus.cagri("/chunks")["url"]
    assert f"/documents/{kacirilmis}/chunks" in url, url
    assert "/documents/research/cards/" not in url, f"kimlik HAM `/` ile gitti (kaçırma düştü): {url}"


def test_slash_YASAGI_geri_gelirse_YARDIMCI_da_isirir():
    """Aynı hüküm, yardımcı düzeyinde — rota katmanından BAĞIMSIZ. `bank` ve kimlik AYNI
    kuraldan geçer (tek boğaz, tek kural): ikisinde de `/` geçer, `..` geçmez."""
    assert api._hafiza_yol_parcasi_guvenli("belge", GERCEK_BELGE_KIMLIGI) == (None, None)
    assert api._hafiza_yol_parcasi_guvenli("bank", "B/x") == (None, None)
    for kotu in ("..", "../x", "x/..", "a/../b", "a//b", "/a", "a/", "a%2Fb", "a b"):
        neden, sinif = api._hafiza_yol_parcasi_guvenli("belge", kotu)
        assert _dolu(neden) and sinif in {"yol_kacisi", "bos_segment", "alan_boslugu"}, (kotu, neden, sinif)


def test_bank_duvari_YAZMA_bacaginda_da_isirir(monkeypatch, tmp_path, sandbox_state):
    """YAZMA BACAĞI YARDIMCIYI DOĞRUDAN ÇAĞIRARAK ÖLÇÜLÜR (düzeltme turu 2, Y-6).

    Rota üzerinden ölçmek MÜMKÜN DEĞİL: `_hafiza_yazma_girdisi` kirli `bank`ı daha erken
    reddediyor ve `_hafiza_yaz` hiç çağrılmıyor — yani rota parametresi `_hafiza_bank_yolu`daki
    duvarı DEĞİL o erken kapıyı ölçerdi. İkinci hattın anlamı tam olarak "birinci hat
    atlandığı gün" olduğuna göre, ikinci hat birinciden BAĞIMSIZ ölçülmeli."""
    casus = _yazma(monkeypatch, tmp_path)
    sonuc = api._hafiza_yaz("DELETE", "/operations/{}", "../../x", kimlikler=("o1",))
    assert sonuc == {"ok": False, "http": None, "govde": None, "neden": sonuc["neden"]}, sonuc
    assert _dolu(sonuc["neden"]) and "bank" in sonuc["neden"], sonuc["neden"]
    assert casus.cagrilar == [], f"kirli `bank` ile upstream'e gidildi: {casus.url_ler()}"

    # KİMLİK BACAĞI DA AYNI YARDIMCIDAN (Y-1): temiz `bank`, kirli kimlik.
    sonuc2 = api._hafiza_yaz("DELETE", "/operations/{}", "B", kimlikler=("../x",))
    assert sonuc2["ok"] is False and _dolu(sonuc2["neden"]), sonuc2
    assert casus.cagrilar == [], f"kirli kimlik ile upstream'e gidildi: {casus.url_ler()}"


def test_bank_duvari_TEMIZ_bankayi_gecirir(monkeypatch, tmp_path, sandbox_state):
    """DUVARIN BEDELİ ÖLÇÜLÜR (bedel yasası): reddeden bir duvar, meşru bankayı da reddederse
    yüzeyin tamamı ölür. Bu çivi duvarın YALNIZ kirliyi kestiğini ölçer."""
    casus = _cpui(monkeypatch, tmp_path)
    r = _client().get("/api/hindsight/varliklar?bank=B")
    assert r.status_code == 200 and r.json()["neden"] is None, r.text
    assert casus.cagrilar, "temiz banka da kesildi — duvar yüzeyi öldürdü"


# ------------------------------------------------------- A2. OKUMA TARAFININ RET İZİ (Ö4) -------

def test_varlik_id_reddi_DEFTERE_dusar(monkeypatch, tmp_path, sandbox_state):
    """Ö4: `/varlik` ret dalı ölçülen sınıfı ATIYORDU ve hiçbir iz bırakmıyordu — yani `..`
    içeren bir `id` denemesi (bu yüzeyde bir SONDA denemesi) `/api/hindsight*` altında İZSİZ
    kalabilen tek yerdi. `_hafiza_yazma_reddi`nin kendi gerekçesi ("izin BURADA olması bir
    tercih değil SÖZLEŞME") okuma ucunda da aynen geçerlidir: sonda denemesi, hangi ucun
    reddettiğine göre değişmez."""
    _cpui(monkeypatch, tmp_path)
    satirlar: list = []
    monkeypatch.setattr(api.obs, "log", lambda olay, **alan: satirlar.append((olay, alan)))
    r = _client().get("/api/hindsight/varlik?bank=B&id=..%2F..%2Fstats")
    assert r.status_code == 400, r.text
    retler = [a for o, a in satirlar if o == "hafiza_okuma_red"]
    assert len(retler) == 1, f"okuma reddi {len(retler)} kez deftere düştü: {satirlar}"
    assert retler[0]["sinif"] == "yol_kacisi", retler[0]
    assert retler[0]["alan"] == "id", retler[0]
    assert retler[0]["uzunluk"] == len("../../stats"), retler[0]


def test_varlik_ret_izi_HAM_DEGER_tasimaz(monkeypatch, tmp_path, sandbox_state):
    """Yazma tarafının `test_ret_izi_HAM_DEGER_tasimaz` sözleşmesi okuma tarafında da geçerli:
    deftere ham dizge yazmak, kapıya erişen bir sondacıya kanıt defterine SINIRSIZ metin
    yazdırma imkânı verirdi."""
    _cpui(monkeypatch, tmp_path)
    satirlar: list = []
    monkeypatch.setattr(api.obs, "log", lambda olay, **alan: satirlar.append((olay, alan)))
    zehir = "..%2F..%2Fetc%2Fpasswd-COK-OZEL-DIZGE"
    _client().get(f"/api/hindsight/varlik?bank=B&id={zehir}")
    metin = repr([a for o, a in satirlar if o == "hafiza_okuma_red"])
    assert "COK-OZEL-DIZGE" not in metin, f"okuma ret izi ham değer taşıdı: {metin}"
    assert "uzunluk" in metin and "sinif" in metin, metin


# ----------------------------------------- A3/A4/A5/A10. BEYANIN KENDİSİ (bayat şerh sınıfı) ----
#
# BU ÜÇ ÇİVİ METİN TARAR VE BUNU BİLEREK YAPAR (v312 `test_pano_KENDI_UCUNU_yalanlamiyor`
# emsalinin `api.py` tarafındaki karşılığı). Ölçtükleri şey davranış değil BEYANdır — ve bu
# dosyanın kurucu dersi tam olarak "bayat bir beyan, bir sonraki okuyucu için ölçümdür".

_API_KAYNAK = pathlib.Path(api.__file__).read_text(encoding="utf-8")


def _sabit_serhi(ad: str, satir_sayisi: int = 14) -> str:
    """Sabitin ÜSTÜNDEKİ şerh bloğu — ölçüm sabitin kendi satırından geriye doğru okunur.
    KÖRLÜK ALARMI: sabit bulunamazsa boş metin dönmez, bağırılır."""
    satirlar = _API_KAYNAK.splitlines()
    for i, s in enumerate(satirlar):
        if s.startswith(f"{ad} ") or s.startswith(f"{ad}:") or s.startswith(f"{ad} ="):
            return "\n".join(satirlar[max(0, i - satir_sayisi):i])
    raise AssertionError(f"sabit kaynakta bulunamadı — çapa bayat: {ad}")


def test_recall_serhi_KAPSAM_DISI_alanlari_ADIYLA_yazar():
    """Ö2: beyaz liste "`RecallRequest` şemasından okundu" diyordu; ölçüm (bu deponun KENDİ
    kaydı, `docs/INCELEME-HINDSIGHT-DERIN-2026-08-31.md` §1.5) şemada DÖRT alan daha olduğunu
    söylüyor. Liste kapalı olması DOĞRU; yalan olan "şemadan okundu" cümlesiydi — okuyucu
    listeyi TAM sanardı. Dört alanın gerekçesi TEK yerde (bu şerhte) yaşar; `Recall.tsx` ona
    İŞARET eder, kopyalamaz (tek-kaynak yasası)."""
    serh = _sabit_serhi("_HAFIZA_RECALL_ALANLARI")
    for alan in ("temporal_window", "tag_groups", "include", "min_scores"):
        assert alan in serh, f"kapsam dışı alan şerhte adıyla yazılı değil: {alan}"
    assert "Faz-1" in serh, "kapsam kararı (Faz-1 alt kümesi) şerhte yazılı değil"


def test_recall_docstringi_DUSURULEN_alani_gerekce_gostermez():
    """Ö2'nin en kötü hâli: `api_hindsight_recall` docstring'i POST olma gerekçesi olarak
    KODUN DÜŞÜRDÜĞÜ iki alanı (`temporal_window`, `min_scores`) örnek gösteriyordu. Örnek
    listede GERÇEKTEN olan alanlardan seçilir; aynı cümlenin `tests/test_na_revision2_v54.py`
    muafiyet yorumundaki kopyası da bu çiviyle birlikte düzeltildi."""
    doc = api.api_hindsight_recall.__doc__ or ""
    for dusen in ("temporal_window", "min_scores", "tag_groups"):
        assert dusen not in doc, (
            f"recall docstring'i düşürülen `{dusen}` alanını POST gerekçesi gösteriyor")
    assert "types" in doc and "tags" in doc, "örnek alanlar beyaz listeden seçilmemiş"


def test_islem_sozlugu_serhinde_BAYAT_yardimci_ADI_yok():
    """Ö5: sabitin üstünde İKİ `#:` bloğu ardışık duruyordu; eskisi kuyruk konvansiyonunu
    `_hafiza_bank_json`e bağlıyordu, oysa I-3a o sorumluluğu `_hafiza_bank_yolu`ya taşımıştı.
    Bayat beyan yalnız eski değil ARTIK YANLIŞtı."""
    serh = _sabit_serhi("_HAFIZA_ISLEM_EYLEMLERI")
    assert "_hafiza_bank_json" not in serh, (
        "bayat şerh geri geldi — kuyruk konvansiyonunun sahibi `_hafiza_bank_yolu`dur")
    assert "_hafiza_bank_yolu" in serh, "kuyruk konvansiyonunun sahibi şerhte yazılı değil"


def test_uc_tavani_serhi_MAKSIMUMSUZ_UCLARI_ADIYLA_yazar():
    """K1: şerh "yazılı olmayan uçların şemasında `maximum` YOKTUR" diyordu ama üç uç ADIYLA
    geçmiyordu. İddia yanlışsa `/islemler`in bu turda kapattığı 422 sınıfı aynen geri gelir.
    ÖLÇÜM 2026-09-03 (openapi.yaml @ ebad4782, `gh api`): `list_entities` limit
    `default:100 minimum:0`, `get_entity_graph` limit `default:1000 minimum:0`, `list_documents`
    limit `default:100 minimum:0` — ÜÇÜNDE DE `maximum` YOK."""
    serh = _sabit_serhi("_HAFIZA_UC_TAVANI", 20)
    for uc in ("/documents", "/entities", "/entities/graph"):
        assert uc in serh, f"`maximum`suz uç şerhte adıyla yazılı değil: {uc}"


def test_konsolidasyon_serhi_OKUYUCUSUZ_beyaz_listeyi_ITIRAF_eder():
    """K7: `observation_scopes` beyaz listesinin bugün OKUYUCUSU YOK — v378
    (`test_tetikleme_UST_YUZEY_GIBI_GOVDESIZ_gider`) UI'ın onu HİÇ göndermemesini AKTİF olarak
    çiviliyor. Güvenlik sınırı olarak meşru; Yasa 6 karşısında BEYANLA durur, sessizlikle değil."""
    serh = _sabit_serhi("_HAFIZA_KONSOLIDASYON_EYLEMLERI", 20)
    assert "okuyucusu" in serh.lower(), (
        "beyaz listenin bugün okuyucusuz olduğu şerhte yazılı değil (Yasa 6 beyanı)")


# ------------------------------------------------------------ A6. BOŞ GÖVDE DALI DA MASKELİ ----

def test_bos_govde_NEDENI_de_maskelenir():
    """K2: `_hafiza_govde_coz`un kendi docstring'i "MASKELEME TEK BOĞAZDAN GEÇER" diyor ama
    boş/`null` dalı `_kapi_maskele`den geçmiyordu. Bugün `url` sır taşımıyor (anahtar başlıkta);
    ikinci savunma hattının BEYAN EDİLMİŞ anlamı ise "birinci hattın delindiği günü karşılamak".
    Yardımcı DOĞRUDAN çağrılır: dalın tek kapısı budur ve rota üzerinden url'e sır sokmak
    ölçümü değil kurulumu ölçerdi."""
    veri, neden = api._hafiza_govde_coz(
        f"http://x/y?tok={SAHTE_ANAHTAR}", b"", None, SAHTE_ANAHTAR)
    assert veri is None and _dolu(neden), (veri, neden)
    assert SAHTE_ANAHTAR not in neden, f"boş gövde gerekçesi anahtarı taşıdı: {neden}"


# --------------------------------------------------------- A9. `/bilgi-arama` OFFSET YOKLUĞU ----

def test_bilgi_arama_offset_GONDERMEZ(monkeypatch, tmp_path, sandbox_state):
    """K5: kardeşleri (`/varlik-graf`, `/bellek-graf`) aynı sapmayı gerekçesiyle yazmıştı;
    `/bilgi-arama` sessizdi. ÖLÇÜM 2026-09-03 (openapi @ ebad4782): `search_knowledge_base`
    parametrelerinin TAMAMI yol `bank_id` · sorgu `q` · sorgu `limit` · başlık `authorization`.
    `offset` YOKTUR — göndermek 422 üretirdi. Çivi davranışı ölçer: istemci `offset` verse bile
    upstream sorgusunda o ad geçmez."""
    casus = _cpui(monkeypatch, tmp_path)
    _client().get("/api/hindsight/bilgi-arama?bank=B&q=alice&offset=25")
    url = casus.cagri("/knowledge-base/search")["url"]
    assert "offset" not in url, f"upstream'de olmayan `offset` gönderildi: {url}"


# ------------------------------------------------------ A11. YAZAN UÇLARIN CSRF DURUŞU ---------

def test_yazma_uclarinin_CSRF_DURUSU_cerezde():
    """İNCELEMECİNİN ÖLÇÜMÜ (nihai inceleme, güçlü yan 6): panonun ilk YAZAN yüzeyi çapraz-site
    bir POST'a açık DEĞİL, çünkü oturum çerezi `httponly=True, samesite="strict"` yazılıyor.
    O duruş bu yüzeyin `sil` gibi GERİ ALINAMAZ fiilleri için bir önkoşul — ve bugün yalnız
    v114'te, `/api/login` YANITINDA ölçülüyordu.

    İKİNCİ OKUYUCU BİLEREK (tek-kaynak yasasının istisnası, gerekçeli): v114 "giriş ucu çerezi
    doğru yazıyor mu" sorusunu sorar; burada sorulan soru "yazan uçların CSRF duruşu hâlâ ayakta
    mı"dır. İki soru ayrı yüzeylerde ölür. Ölçüm KOPYALANMAZ, ÜRETİLİR: başlık gerçekten
    kurulur ve okunur."""
    baslik = api._oturum_cerez_basligi("civi-jetonu", 60, False)
    assert "httponly" in baslik.lower(), f"oturum çerezi HttpOnly değil: {baslik}"
    assert "samesite=strict" in baslik.lower().replace(" ", ""), (
        f"oturum çerezi SameSite=Strict değil — yazan uçlar çapraz-siteye açılır: {baslik}")


# ----------------------------------------------- A12. WEBHOOK SÜZGECİ FAIL-CLOSED (Rol-1) -------

def test_webhook_suzgeci_TANIMAYAN_SEKILDE_govdeyi_GECIRMEZ(monkeypatch, tmp_path, sandbox_state):
    """ROL-1 HÜKMÜ (2026-09-03, TSK-109 düzeltme turu endişesi): süzgeç `items` görmezse gövdeyi
    AYNEN geçiriyordu — yani upstream şeması kayıp sırrı başka bir alana taşıdığı gün, süzgeç
    sessizce açılırdı. SIR HİJYENİ > ERİŞİLEBİLİRLİK: tanınmayan şekilde gövde VERİLMEZ, gerekçe
    verilir. Bu bir sessiz yutma DEĞİL, beyanlı bir fail-closed dalıdır."""
    ham = json.dumps({"webhooks": [{"id": "w1", "secret": WEBHOOK_SIRRI_SENTETIK}]}).encode()
    _cpui(monkeypatch, tmp_path, **{"/banks/B/webhooks": ham})
    r = _client().get("/api/hindsight/webhooklar?bank=B")
    assert r.status_code == 200, r.text
    g = r.json()
    assert g["govde"] is None, f"tanınmayan şekilde gövde geçti: {g}"
    assert _dolu(g["neden"]) and "süzülemediği" in g["neden"], g["neden"]
    assert WEBHOOK_SIRRI_SENTETIK not in r.text, "imza sırrı yanıta sızdı"
