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

OLAY ADLARI bot önekiyle üretilir (`olay_oneki`): `sef_brifingi_denetci_rota_dustu` gibi — v455
çivileri sef'in adlarını AYNEN bekler, bekci/karne kendi adlarıyla yazar (teşhis bot bazında okunur).

GEÇ BAĞLAMA: `profil_evi` ve `profil_cagir` çağrı anında çözülür (çağrılabilir verilebilir), çünkü
çiviler `m._profili_cagir` / `m.HERMES_PROFIL_HOME`'u monkeypatch'ler ve sahte profil o anda
görünmelidir (v455 B-serisi deseni).

OKUR: profil `config.yaml` + `SOUL.md`, ortam değişkeni, `secrets`. YAZAR: yalnız `obs.log` olayları.
"""
from __future__ import annotations

import os
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

    def _ev(self):
        return self._profil_evi() if callable(self._profil_evi) else self._profil_evi

    def cevaplayan_oku(self) -> str | None:
        """SON denetçi çağrısında GERÇEKTEN cevap veren model — ölçülmediyse `None`."""
        return self.son_cevaplayan_model

    def cagir(self, prompt: str) -> str:
        """Denetçi çağrısı — kapının seçilen rotasına DOĞRUDAN; ölçülemeyen kapı → profil yolu."""
        self.son_cevaplayan_model = None          # ÖNCE sıfırla: bayat ölçüm sızamaz (v455 B4)
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
        sistem = soul_sistem_metni(ev)
        if sistem:
            govde["messages"].append({"role": "system", "content": sistem})
        govde["messages"].append({"role": "user", "content": notify.scrub(prompt)})
        r = httpx.post(f"{kok}{DENETIM_ROTALARI[rota]}/chat/completions",
                       headers={KAPI_BASLIK: anahtar, "Content-Type": "application/json"},
                       json=govde, timeout=self.model_timeout_s)
        r.raise_for_status()
        d = r.json()
        cevaplayan = str((d or {}).get("model") or "").strip()
        if cevaplayan:
            self.son_cevaplayan_model = cevaplayan
        else:
            obs.log(f"{self.olay_oneki}_cevaplayan_model_olculemedi", rota=rota,
                    neden="kapı yanıt gövdesinde `model` alanı yok ya da boş",
                    detail="cevaplayan model ÖLÇÜLEMEDİ — olaya `None` yazılır, UYDURULMAZ")
        ch = ((d or {}).get("choices") or [{}])[0] or {}
        metin = str((ch.get("message") or {}).get("content") or "").strip()
        bitis = str(ch.get("finish_reason") or "")
        if bitis == "length":
            raise RuntimeError(f"kapı cevabı KESİLDİ (finish_reason=length, rota={rota})")
        if not metin:
            raise RuntimeError(f"kapı 200 döndü ama içerik YOK (finish_reason={bitis or '?'}, "
                               f"rota={rota})")
        return metin
