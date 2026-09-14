"""Brifing denetçisinin KAPI ROTASI — üç botun (sef · bekci · karne) ORTAK çağrı yolu.

TSK-138 dilim-2 (2026-09-08) denetçi çağrısını hermes profil yolundan (150 sn dış duvar) kapının
seçilen rotasına ("hızlı" varsayılan) taşıdı — ama YALNIZ `ops/sef_brifingi.py`de. Ölçüm
(A1 `state/events.jsonl`, 2026-09-09/10 10:0xZ): `bekci` denetçisi hâlâ "profil 150 sn'de bitmedi"
ile düşüyordu, `karne` olaylarında `cevaplayan_model=None` kalıyordu — ikisi de `cagir=_profili_cagir`
veriyordu, rota onlara hiç ulaşmamıştı. Bu modül o kodu TEK yere taşır (tek-kaynak yasası: üç
kopya üç ayrı hızda çürürdü) ve her bot kendi `DenetciRota` örneğini kurar.

SÖZLEŞME (sef'teki asıl gövdeyle birebir, 2026-09-12'de taşındı; gerekçelerin uzun hâli
`ops/sef_brifingi.py` başlığındaki TSK-138 bölümünde):
  * Rota `SOUL_DENETIM_ROTA` ortam değişkeninden okunur; boş → `hizli`; tanınmayan → ADIYLA olaya
    yazılır ve varsayılana düşülür (Yasa 4: yazım hatası sessiz davranış değişikliği olamaz).
  * Kapı kökü profilin KENDİ `config.yaml`ından (`providers.kapi.base_url`, `/llm/` önekinden
    kesilir) ÖLÇÜLÜR; kod içinde adres YOK (2026-09-02'de adres bir kez zaten taşındı).
  * Anahtar `meridian.secrets.get("KAPI_APIKEY")` — birime `LoadCredential` drop-in'i ile gelir
    (`deploy/oracle-a1/<birim>.service.d/54-kapi-credential.conf`; üç oneshot birimde AYNI satır).
  * `max_tokens` profilin `model.max_tokens`ından AYNEN; ölçülemezse UYDURULMAZ.
  * Kök / anahtar / max_tokens ölçülemezse çağrı profil yoluna DÜŞER ve düşüş `<bot>_denetci_rota_dustu`
    olayıyla deftere yazılır — denetim sessizce kapanmaz, ama cevaplayan model ölçülemez.
  * İstem `notify.scrub`tan geçer (model çağrısı bir VERİ ÇIKIŞIDIR).
  * Cevaplayan model kapı yanıtının `model` alanından okunur; yoksa `None` + olay.
  * Muhakeme kipi `SOUL_DENETIM_REASONING`dan okunur; boş → `kapali`; tanınmayan → ADIYLA olaya
    (dilim-3, aşağıdaki ÖLÇÜM bloğu). `model_timeout_s` 120 sn DEĞİŞMEDİ (v455 D1).
  * HTTP 200 gövdesi içindeki üst-akım hatası ADIYLA olaya + TEK yeniden deneme; ikincisi de
    düşerse `RuntimeError` → çağıranın mevcut `llm_dustu` dalı (teslimat DÜŞMEZ).
  * Her başarılı kapı çağrısı süre/jeton olarak ölçülür (`<önek>_denetci_cagri` + `son_olcum`).

OLAY ADLARI bot önekiyle üretilir (`olay_oneki`): `sef_brifingi_denetci_rota_dustu` gibi — v455
çivileri sef'in adlarını AYNEN bekler, bekci/karne kendi adlarıyla yazar (teşhis bot bazında okunur).

ÖLÇÜM 2026-09-14 (TSK-138 dilim-3 — Rol-1 ölçtü; çiviler `tests/test_denetci_rota_reasoning_v486.py`).
Bekçi 10:03Z koşumu `llm_dustu` (cagri_n=3, ReadTimeout). Kapı günlüğü AYNI koşum için 75,5 s ve
138,7 s: birincil örnek 0,3-0,4 s'de 429 ("shared pool"), kapı yedeğe düştü, istemci 120 s'de
vazgeçti, kapı isteği 138 s'de 200 ile bitirdi (boşa giden çağrı). İKİ AYRI ARIZA SINIFI ÇIKTI:

  1. MUHAKEME BÜTÇESİ. Kontrollü ölçüm (aynı rota, SOUL sistem mesajı, 3.476 istem jetonu):
     varsayılan → 1.252 muhakeme jetonu / 30 s · muhakeme kapalı → 24 jeton / 1,4 s ve TEMİZ JSON ·
     muhakeme tavanı 400 → 6,7 s ama gerçek olay adlarını "uydurma" saydı (orta yol denendi,
     ÖLÇÜLDÜ, seçilmedi). KARAR: muhakeme VARSAYILAN OLARAK KAPALI (`DENETIM_REASONING_ENV`).
     KAZANÇ 75-138 s → ~2-10 s. BEDEL (bedel yasası): muhakemesiz denetçi "uydurma" sınıfını daha
     az yakalayabilir — bu yüzden her başarılı çağrı süre/jeton olarak ÖLÇÜLÜR (`_denetci_cagri`),
     iki gece `brifing_kural_denetimi.ihlal` ile yan yana okunur. GERİ ALIM: ortam değişkeni
     `acik` (ara basamak `dusuk`), dağıtım gerekmez.
  2. HTTP 200 İÇİNDE HATA GÖVDESİ. OpenRouter üst-akımın "Service temporarily overloaded"
     hatasını 200 gövdesinde `error` alanı olarak döndürüyor ve `choices` HİÇ GELMİYOR. Kapının
     kendi yedekleme koşulu (`fallback_strategy: [http_429, http_5xx]`) bunu GÖREMEZ — taşıyıcı
     durum kodu 200'dür. Bugüne kadar bu gövde "kapı 200 döndü ama içerik YOK" hatasına, oradan
     `llm_dustu`ya düşüyordu: 09-05/06'nın "cevap JSON değil" sınıfının KÖKÜ budur ve hüküm
     yanlış tarafı suçluyordu (denetçinin cevabı değil, üst-akımın hiç cevap vermemesi).
     KARAR: hata ADIYLA deftere (`_denetci_ustakim_hatasi`) + TEK yeniden deneme.

GEÇ BAĞLAMA: `profil_evi` ve `profil_cagir` çağrı anında çözülür (çağrılabilir verilebilir), çünkü
çiviler `m._profili_cagir` / `m.HERMES_PROFIL_HOME`'u monkeypatch'ler ve sahte profil o anda
görünmelidir (v455 B-serisi deseni).

OKUR: profil `config.yaml` + `SOUL.md`, ortam değişkeni, `secrets`. YAZAR: yalnız `obs.log` olayları.
"""
from __future__ import annotations

import os
import time
from pathlib import Path

import yaml

from meridian import notify, obs, secrets

DENETIM_ROTA_ENV = "SOUL_DENETIM_ROTA"
# Rota → kapı yolu. `profil` bir URL DEĞİL, dilim-2'den ÖNCEKİ davranıştır (hermes CLI) ve TAM geri
# alma yoludur: iki değerli bir bayrak yalnız rotayı geri alır, doğrudan HTTP yolunu bırakırdı.
DENETIM_ROTALARI = {"hizli": "/llm/hizli/v1", "danisma": "/llm/v1", "profil": None}
VARSAYILAN_DENETIM_ROTASI = "hizli"
# Kapı kökünün profil `base_url`undan kesildiği yer. Kök KODA YAZILMAZ (tek-kaynak yasası).
KAPI_ROTA_ONEKI = "/llm/"
# Kapının `key-auth` eklentisi tüketiciyi BU BAŞLIKTAN tanır. DEĞER hiçbir log/olay/çıktıya girmez.
KAPI_BASLIK = "apikey"
KAPI_SIR_ADI = "KAPI_APIKEY"

DENETIM_REASONING_ENV = "SOUL_DENETIM_REASONING"
# Kip → istek gövdesine yazılacak `reasoning` PARÇASI. `None` "alanı HİÇ YAZMA" demektir ve bu
# `{"enabled": True}` ile AYNI ŞEY DEĞİLDİR: `acik` bu turdan ÖNCEKİ gövdeyi geri getirir, yani
# sağlayıcının kendi varsayılanını — açıkça `True` yazmak, o varsayılan bir gün değişirse geri
# almayı SESSİZCE başka bir şeye çevirirdi (rota sözlüğündeki `profil: None` ile aynı disiplin).
DENETIM_REASONING_KIPLERI: dict[str, dict | None] = {
    "kapali": {"enabled": False},
    "dusuk": {"effort": "low"},
    "acik": None,
}
VARSAYILAN_DENETIM_REASONING = "kapali"

# ÜST-AKIM HATASINDA TEK YENİDEN DENEME — SAYI 1'DİR, BEKLEME SINIRLIDIR (CLAUDE.md §7 ayrımı).
# Yasak olan şey kendi kurduğun YOKLAMA DÖNGÜSÜDÜR; burada döngü yoktur: tek bir bekleme, tek bir
# tekrar, üçüncü çağrı ASLA. Kotasız bir yüzeyde "birkaç kez daha dene" operatörün bütçesini
# sessizce yakar ve üst-akım doluyken ısrar kuyruğu uzatır.
USTAKIM_YENIDEN_DENEME_SN = 5
# Üst-akım mesajı BİZİM YAZMADIĞIMIZ, uzunluğu sağlayıcının elinde olan bir metindir — deftere
# kırpılarak girer. TEK KAYNAK: çivi de bu sabitten okur.
USTAKIM_MESAJ_TAVANI = 120


def denetci_rotasi(olay_oneki: str) -> str:
    """Denetçi çağrısının rotası. Varsayılan HIZLI; tanınmayan değer ADIYLA kayda geçer."""
    ham = (os.environ.get(DENETIM_ROTA_ENV) or "").strip()
    if not ham:
        return VARSAYILAN_DENETIM_ROTASI
    if ham not in DENETIM_ROTALARI:
        obs.log(f"{olay_oneki}_denetci_rotasi_taninmadi", deger=ham,
                gecerli=sorted(DENETIM_ROTALARI),
                detail=f"{DENETIM_ROTA_ENV} tanınmadı — VARSAYILAN rota kullanıldı, denetim "
                       "durmadı")
        return VARSAYILAN_DENETIM_ROTASI
    return ham


def denetim_reasoning(olay_oneki: str) -> str:
    """Denetçi çağrısının MUHAKEME kipi. Varsayılan KAPALI; tanınmayan değer ADIYLA kayda geçer.

    `denetci_rotasi` ile BİREBİR aynı desen (tek-kaynak yasası ikiz bir okuyucu değil, ikiz bir
    SÖZLEŞME ister): yazım hatası sessiz bir davranış değişikliği olamaz (Yasa 4) — `kapalı`
    (Türkçe ı) yazan bir operatör bugün hiçbir uyarı almadan varsayılanda kalır ve iki gecelik
    ölçüm "hangi kipte gitti" sorusuna cevap veremezdi."""
    ham = (os.environ.get(DENETIM_REASONING_ENV) or "").strip()
    if not ham:
        return VARSAYILAN_DENETIM_REASONING
    if ham not in DENETIM_REASONING_KIPLERI:
        obs.log(f"{olay_oneki}_denetci_reasoning_taninmadi", deger=ham,
                gecerli=sorted(DENETIM_REASONING_KIPLERI),
                detail=f"{DENETIM_REASONING_ENV} tanınmadı — VARSAYILAN kip kullanıldı, denetim "
                       "durmadı")
        return VARSAYILAN_DENETIM_REASONING
    return ham


def ustakim_hatasi(govde: dict) -> dict | None:
    """HTTP 200 gövdesinin İÇİNDEKİ üst-akım hatası — yoksa `None`.

    İKİ ŞART BİRLİKTE: `choices` YOK **ve** `error` bir eşleme. Yalnız `error`a bakmak, cevabı
    da hatayı da taşıyan (kısmi) bir gövdeyi sağlam cevaba rağmen düşürürdü; yalnız `choices`
    yokluğuna bakmak ise boş cevabı üst-akım arızası sayıp BOŞUNA ikinci bir çağrı ödetirdi —
    boş cevap tekrar istenince aynı boş cevap gelir, üst-akım hatası ise GEÇİCİDİR."""
    if govde.get("choices"):
        return None
    hata = govde.get("error")
    return hata if isinstance(hata, dict) else None


def _jeton(deger) -> int | None:
    """Yanıttaki jeton sayısı — tam sayı değilse `None`. SIFIR YAZILMAZ (uydurma yasağı):
    "ölçemedim" ile "sıfır jeton harcandı" aynı şey değildir ve ikisi aynı alandan okunuyorsa
    ölçüm gecelerinin ortalaması muhakemesiz kipin kazancını OLDUĞUNDAN BÜYÜK gösterir."""
    if isinstance(deger, bool) or not isinstance(deger, int):
        return None
    return deger


def usage_jetonlari(govde: dict) -> tuple[int | None, int | None, int | None]:
    """`(prompt, completion, reasoning)` jetonları — kapı yanıtının `usage` bloğundan.

    Muhakeme jetonu OpenAI-uyumlu gövdede "completion_tokens_details" altında gelir ve muhakeme
    yapmayan modeller o ayrıntıyı HİÇ yazmaz; o durumda değer `None`dır (yukarıdaki gerekçe)."""
    blok = govde.get("usage")
    if not isinstance(blok, dict):
        return None, None, None
    ayrinti = blok.get("completion_tokens_details")
    ayrinti = ayrinti if isinstance(ayrinti, dict) else {}
    return (_jeton(blok.get("prompt_tokens")), _jeton(blok.get("completion_tokens")),
            _jeton(ayrinti.get("reasoning_tokens")))


def profil_config(profil_evi) -> dict | None:
    """Profilin `config.yaml`ı — eşleme değilse/okunamıyorsa `None` (sessiz, çağıran ADLANDIRIR)."""
    yol = Path(str(profil_evi or "")) / "config.yaml"
    try:
        cfg = yaml.safe_load(yol.read_text(encoding="utf-8"))
    except Exception:  # sessiz-yutma: DEĞİL — dönüş `None` ve ÇAĞIRAN onu kendi olay adıyla deftere yazar; istisnanın metni burada bir şey söylemez
        return None
    return cfg if isinstance(cfg, dict) else None


def kapi_koku(profil_evi) -> tuple[str | None, str | None]:
    """`(kök, neden)` — kapının şema+host+port kökü, profilin KENDİ `config.yaml`ından ÖLÇÜLÜR."""
    cfg = profil_config(profil_evi)
    if cfg is None:
        return None, "profil `config.yaml` okunamadı ya da eşleme değil"
    girdi = ((cfg.get("providers") or {}).get("kapi")
             if isinstance(cfg.get("providers"), dict) else None)
    if not isinstance(girdi, dict):
        return None, "`providers.kapi` girdisi yok ya da eşleme değil"
    base = str(girdi.get("base_url") or "").strip()
    kesim = base.find(KAPI_ROTA_ONEKI)
    if kesim <= 0:
        return None, f"`providers.kapi.base_url` `{KAPI_ROTA_ONEKI}` taşımıyor: {base!r}"
    return base[:kesim], None


def profil_model_adi(profil_evi) -> str | None:
    """Profilin `model.default` künyesi — istek gövdesine yazılan ad (kapı bu alanı EZER)."""
    cfg = profil_config(profil_evi)
    blok = (cfg or {}).get("model")
    if isinstance(blok, str):
        return blok.strip() or None
    if isinstance(blok, dict):
        return str(blok.get("default") or "").strip() or None
    return None


def profil_model_kimligi(profil_evi, olay_oneki: str) -> str | None:
    """Denetim olayına künye olarak giden İSTENEN model adı — ölçülemezse `None` + ADIYLA olay.

    `profil_model_adi`nin sinyalli kabuğu: `None` bir tahminle DOLDURULMAZ (uydurma yasağı) ve her
    düşüş dalı deftere yazılır (Yasa 4) — "model alanı yok" ile "config okunamadı" ayrımı teşhisin
    kendisidir."""
    cfg = profil_config(profil_evi)
    if cfg is None:
        obs.log(f"{olay_oneki}_model_kimligi_olculemedi", neden="profil `config.yaml` okunamadı",
                detail="denetim olayındaki `model` künyesi `None` kalır — uydurulmaz")
        return None
    ad = profil_model_adi(profil_evi)
    if ad is None:
        obs.log(f"{olay_oneki}_model_kimligi_olculemedi", neden="`model.default` alanı yok ya da boş",
                detail="denetim olayındaki `model` künyesi `None` kalır — uydurulmaz")
    return ad


def profil_max_tokens(profil_evi) -> int | None:
    """Profilin `model.max_tokens` değeri — AYNEN taşınır; ölçülemezse `None` (elle sayı yazılmaz)."""
    cfg = profil_config(profil_evi)
    blok = (cfg or {}).get("model")
    if not isinstance(blok, dict):
        return None
    deger = blok.get("max_tokens")
    if isinstance(deger, bool) or not isinstance(deger, int) or deger <= 0:
        return None
    return deger


def soul_sistem_metni(profil_evi) -> str | None:
    """Profilin `SOUL.md`si — doğrudan çağrının sistem mesajı (hermes'in okuduğu AYNI dosya)."""
    try:
        metin = (Path(str(profil_evi or "")) / "SOUL.md").read_text(encoding="utf-8").strip()
    except Exception:  # sessiz-yutma: DEĞİL — `None` dönüşü sistem mesajını düşürür, çağrı yine gider; SOUL.md yokluğu `soul_denetimi.uslup_blogu` tarafından ayrıca ölçülür
        return None
    return metin or None


class DenetciRota:
    """Bir botun denetçi çağrı yolu: `cagir(prompt)` + `cevaplayan_oku()`.

    `profil_evi`: yol ya da yolu döndüren çağrılabilir · `profil_cagir`: hermes profil yolu
    (düşüş hedefi; çağrı anında çözülür) · `olay_oneki`: olay adlarının bot öneki ·
    `model_timeout_s`: HTTP bütçesi (botun `MODEL_TIMEOUT_S`i, dış 150 sn duvarı bu yolda YOK)."""

    def __init__(self, *, profil_evi, profil_cagir, olay_oneki: str, model_timeout_s: float):
        self._profil_evi = profil_evi
        self._profil_cagir = profil_cagir
        self.olay_oneki = olay_oneki
        self.model_timeout_s = model_timeout_s
        self.son_cevaplayan_model: str | None = None
        # SON BAŞARILI KAPI ÇAĞRISININ ÖLÇÜMÜ — `_denetci_cagri` olayıyla AYNI alanlar (tek
        # kaynak: sözlük hem olaya hem buraya gider). `cagir` başında `None`a sıfırlanır, çünkü
        # bayat bir ölçüm düşen bir çağrının yanında "yapılmış gibi" okunurdu (v455 B4 dersi).
        self.son_olcum: dict | None = None

    def _ev(self):
        return self._profil_evi() if callable(self._profil_evi) else self._profil_evi

    def _ustakim_olayi(self, hata: dict, rota: str, *, ilk: bool) -> None:
        """Üst-akım hatasını ADIYLA deftere yazar — mesaj SÜZÜLÜR ve KIRPILIR.

        Süzgeç isteğe bağlı değil: sağlayıcı hata metnine kendi isteğinin URL'ini gömebilir ve o
        URL sorgu parametresinde bir anahtar taşıyabilir. Süzgeç olmasaydı sır, kendi defterimize
        kendi elimizle yazılırdı (`notify.scrub`un var oluş gerekçesi). Okuyucu: Rol-1'in TSK-138
        ölçüm satırı ve `llm_dustu` kök-neden ayrımı — "denetçinin cevabı bozuk" ile "üst-akım
        hiç cevap vermedi" ancak bu olayla ayrılır."""
        obs.log(f"{self.olay_oneki}_denetci_ustakim_hatasi", kod=hata.get("code"),
                mesaj=notify.scrub(str(hata.get("message") or ""))[:USTAKIM_MESAJ_TAVANI],
                rota=rota,
                detail=("kapı HTTP 200 döndürdü ama gövde üst-akım hatası taşıyor (choices YOK) — "
                        + ("TEK yeniden deneme yapılıyor" if ilk else
                           "yeniden deneme de düştü, hüküm `llm_dustu` olur (teslimat DÜŞMEZ)")))

    def cevaplayan_oku(self) -> str | None:
        """SON denetçi çağrısında GERÇEKTEN cevap veren model — ölçülmediyse `None`."""
        return self.son_cevaplayan_model

    def cagir(self, prompt: str) -> str:
        """Denetçi çağrısı — kapının seçilen rotasına DOĞRUDAN; ölçülemeyen kapı → profil yolu."""
        self.son_cevaplayan_model = None          # ÖNCE sıfırla: bayat ölçüm sızamaz (v455 B4)
        self.son_olcum = None                     # aynı gerekçe, aynı an (süre/jeton da bayatlar)
        rota = denetci_rotasi(self.olay_oneki)
        if DENETIM_ROTALARI[rota] is None:
            return self._profil_cagir(prompt)

        ev = self._ev()
        kok, neden = kapi_koku(ev)
        anahtar = (secrets.get(KAPI_SIR_ADI) or "").strip()
        azami_jeton = profil_max_tokens(ev)
        if not kok or not anahtar or azami_jeton is None:
            if neden is None and not anahtar:
                neden = f"`{KAPI_SIR_ADI}` sırrı yok ya da boş"
            if neden is None and azami_jeton is None:
                neden = "profil `model.max_tokens` ÖLÇÜLEMEDİ (elle sayı yazılmaz)"
            obs.log(f"{self.olay_oneki}_denetci_rota_dustu", rota=rota, neden=neden,
                    detail="denetçi kapı rotası ÖLÇÜLEMEDİ — çağrı hermes profil yoluna döndü, "
                           "denetim yapılmaya devam eder (cevaplayan model ölçülemez)")
            return self._profil_cagir(prompt)

        import httpx
        govde = {"messages": [], "model": profil_model_adi(ev) or "", "max_tokens": azami_jeton}
        kip = denetim_reasoning(self.olay_oneki)
        parca = DENETIM_REASONING_KIPLERI[kip]
        if parca is not None:
            govde["reasoning"] = dict(parca)
        sistem = soul_sistem_metni(ev)
        if sistem:
            govde["messages"].append({"role": "system", "content": sistem})
        govde["messages"].append({"role": "user", "content": notify.scrub(prompt)})
        url = f"{kok}{DENETIM_ROTALARI[rota]}/chat/completions"
        basliklar = {KAPI_BASLIK: anahtar, "Content-Type": "application/json"}

        def _tek_cagri() -> tuple[dict, float]:
            """Kapıya TEK istek — `(gövde, süre_sn)`. Süre GERÇEK bir `monotonic` farkıdır."""
            t0 = time.monotonic()
            r = httpx.post(url, headers=basliklar, json=govde, timeout=self.model_timeout_s)
            r.raise_for_status()
            return (r.json() or {}), round(time.monotonic() - t0, 2)

        d, sure_sn = _tek_cagri()
        yeniden = 0
        hata = ustakim_hatasi(d)
        if hata is not None:
            self._ustakim_olayi(hata, rota, ilk=True)
            time.sleep(USTAKIM_YENIDEN_DENEME_SN)   # TEK ATIM, döngü DEĞİL (sabitin gerekçesine bak)
            yeniden = 1
            d, sure_sn = _tek_cagri()
            hata = ustakim_hatasi(d)
            if hata is not None:
                self._ustakim_olayi(hata, rota, ilk=False)
                raise RuntimeError(f"kapı üst-akım hatası (kod {hata.get('code')}, rota {rota}) "
                                   "— yeniden deneme de düştü")
        cevaplayan = str((d or {}).get("model") or "").strip()
        if cevaplayan:
            self.son_cevaplayan_model = cevaplayan
        else:
            obs.log(f"{self.olay_oneki}_cevaplayan_model_olculemedi", rota=rota,
                    neden="kapı yanıt gövdesinde `model` alanı yok ya da boş",
                    detail="cevaplayan model ÖLÇÜLEMEDİ — olaya `None` yazılır, UYDURULMAZ")
        # ÇAĞRI ÖLÇÜMÜ — KAZANCIN VE BEDELİN AYNI SATIRDAN OKUNDUĞU YER (bedel yasası).
        # OKUYUCU (Yasa 6): Rol-1'in TSK-138 ölçüm satırı — A1 `state/events.jsonl` üzerinde bu
        # olay adının grep'i; iki gecelik kıyas `brifing_kural_denetimi` ihlal sayısıyla YAN YANA
        # yapılır (muhakemesiz denetçi "uydurma"yı daha az yakalarsa bedel ORADAN görünür).
        # KESİLMİŞ/BOŞ CEVAP DA ÖLÇÜLÜR (aşağıdaki iki `raise`den ÖNCE): kapı cevabı ürettiyse
        # jeton HARCANMIŞTIR ve yalnız mutlu yolu ölçen bir sayaç, tam da pahalı koşumları
        # (muhakeme tavanını dolduran kesilmiş cevapları) ortalamanın dışında bırakırdı.
        # `sure_sn` CEVABI VEREN çağrının kendi süresidir; yeniden deneme olduğunda araya giren
        # bekleme ve düşen ilk çağrı `yeniden_deneme=1` ile okunur (model gecikmesi ile toplam
        # duvar süresi AYRI şeylerdir ve ölçülen şey model gecikmesidir).
        p_tok, c_tok, r_tok = usage_jetonlari(d or {})
        self.son_olcum = {"rota": rota, "reasoning_kipi": kip, "sure_sn": sure_sn,
                          "prompt_tok": p_tok, "completion_tok": c_tok, "reasoning_tok": r_tok,
                          "cevaplayan_model": self.son_cevaplayan_model,
                          "yeniden_deneme": yeniden}
        obs.log(f"{self.olay_oneki}_denetci_cagri", **self.son_olcum)
        ch = ((d or {}).get("choices") or [{}])[0] or {}
        metin = str((ch.get("message") or {}).get("content") or "").strip()
        bitis = str(ch.get("finish_reason") or "")
        if bitis == "length":
            raise RuntimeError(f"kapı cevabı KESİLDİ (finish_reason=length, rota={rota})")
        if not metin:
            raise RuntimeError(f"kapı 200 döndü ama içerik YOK (finish_reason={bitis or '?'}, "
                               f"rota={rota})")
        return metin
