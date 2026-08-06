"""tests/vaka.py — DONDURULMUŞ VAKA YÜKLEYİCİSİ (D3 modül 3'ün okuma ucu, 2026-08-07).

`ops/vaka_sabitle.py` bir canlı arızayı `tests/fikstur/vaka_<tarih>_<ad>/` altına dondurur;
BU dosya onu bir teste geri yükler. İkisi tek bir sözleşmenin iki ucudur ve sözleşme
`VAKA.json` manifestidir.

NEDEN AYRI BİR MODÜL, `conftest.py` İÇİNDE DEĞİL: `conftest` 246 test dosyasının ortak
yüzeyidir ve oraya konan her şey her koşumda ithal edilir. Yükleyici YALNIZ vaka testleri
tarafından kullanılır; `conftest`teki tek şey ince bir fikstür (`vaka`) olup gövde buradadır.

BÜTÜNLÜK KAPISI — `dogrula()`. Yüklerken her dosyanın sha256'sı manifestteki değerle
KARŞILAŞTIRILIR. Sebebi bu modülün var olma sebebiyle aynı: elle onarılan fikstür (da6bec3
vakası, v76) artık ARIZAYI değil onaranın hatırladığını taşır. Sessizce sürüklenen bir fikstür,
yeşil bir testi anlamsız yapar; kapı onu ADIYLA düşürür.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
from dataclasses import dataclass

FIKSTUR_KOK = pathlib.Path(__file__).resolve().parent / "fikstur"
MANIFEST = "VAKA.json"
OLAY_DOSYASI = "olaylar.jsonl"
DURUM_DIZINI = "durum"
DEFTER_DIZINI = "defter"


def _sha256(metin: str) -> str:
    return hashlib.sha256(metin.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Vaka:
    """Dondurulmuş bir vaka + kareleri. Salt okunurdur: fikstür dosyalarına HİÇBİR yazım yok."""

    ad: str
    dizin: pathlib.Path
    manifest: dict

    # ---- kareler ------------------------------------------------------------------------------
    @property
    def kareler(self) -> list[str]:
        return sorted(self.manifest.get("kareler", {}))

    def kare(self, ad: str) -> dict:
        k = self.manifest.get("kareler", {}).get(ad)
        if k is None:
            raise KeyError(f"{self.ad}: '{ad}' karesi yok (var olanlar: {', '.join(self.kareler)})")
        return k

    def _kare_dizini(self, kare: str) -> pathlib.Path:
        self.kare(kare)                       # kare adı doğrulansın
        return self.dizin / f"kare_{kare}"

    # ---- içerik -------------------------------------------------------------------------------
    def durum(self, kare: str, ad: str) -> dict:
        """Dondurulmuş bir durum belgesi (ör. `portfolio.json`) — sözlük olarak."""
        yol = self._kare_dizini(kare) / DURUM_DIZINI / ad
        if not yol.exists():
            raise FileNotFoundError(f"{self.ad}/kare_{kare}: durum belgesi yok: {ad}")
        return json.loads(yol.read_text(encoding="utf-8"))

    def olaylar(self, kare: str) -> list[dict]:
        """Pencereye düşen olay satırları (`events.jsonl` kesiti). Kare olay taşımıyorsa boş liste."""
        return self._jsonl(self._kare_dizini(kare) / OLAY_DOSYASI)

    def defter(self, kare: str, ad: str) -> list[dict]:
        """Dondurulmuş bir defter kesiti (ör. `trades.jsonl`)."""
        if ad == "events.jsonl":
            return self.olaylar(kare)
        return self._jsonl(self._kare_dizini(kare) / DEFTER_DIZINI / ad)

    @staticmethod
    def _jsonl(yol: pathlib.Path) -> list[dict]:
        if not yol.exists():
            return []
        return [json.loads(s) for s in yol.read_text(encoding="utf-8").splitlines() if s.strip()]

    # ---- sandbox'a kurulum --------------------------------------------------------------------
    def state_kur(self, kare: str, *, olaylar: bool = False) -> list[str]:
        """Karenin durum belgelerini ve defterlerini AKTİF `config.STATE` dizinine yaz.

        ÇAĞIRAN SANDBOX'TA OLMAK ZORUNDA: yazım `store` üzerinden gider ve `store` `config.STATE`e
        bakar. `sandbox_state` fikstürü olmadan çağrılırsa CANLI state'e yazardı — bu yüzden
        `conftest`teki `vaka` fikstürü `sandbox_state`e BAĞLIDIR ve doğrudan çağrı beklenmez.

        `olaylar=False` VARSAYILANDIR: bir testin çoğu zaman istediği şey KİTAP ve DEFTERdir;
        `events.jsonl`ı sandbox'a dökmek `watchdog`/`obs` yollarını dondurulmuş bir geçmişle
        besler ve testin ölçtüğü şeyi bulandırır. İsteyen açıkça açar.

        Dönüş: yazılan artefakt adları (yazılan hiçbir şey yoksa boş liste — sessiz başarı yok)."""
        from meridian import store
        k = self.kare(kare)
        yazilan: list[str] = []
        for ad in sorted(k.get("durum", {})):
            store.write_json(ad, self.durum(kare, ad))
            yazilan.append(ad)
        for ad in sorted(k.get("defter", {})):
            if ad == "events.jsonl" and not olaylar:
                continue
            store.write_jsonl(ad, self.defter(kare, ad))
            yazilan.append(ad)
        return yazilan

    # ---- bütünlük -----------------------------------------------------------------------------
    def dogrula(self) -> list[str]:
        """Manifestteki her sha256'yı diskle karşılaştır. Dönüş: SAPMA listesi (boş = temiz)."""
        sapmalar: list[str] = []
        for kare, k in sorted(self.manifest.get("kareler", {}).items()):
            kd = self.dizin / f"kare_{kare}"
            beklenen = {f"{DURUM_DIZINI}/{ad}": d["sha256"] for ad, d in k.get("durum", {}).items()}
            beklenen.update({d["dosya"]: d["sha256"] for d in k.get("defter", {}).values()})
            for rel, sha in sorted(beklenen.items()):
                yol = kd / rel
                if not yol.exists():
                    sapmalar.append(f"{kare}/{rel}: DOSYA YOK")
                    continue
                gercek = _sha256(yol.read_text(encoding="utf-8"))
                if gercek != sha:
                    sapmalar.append(f"{kare}/{rel}: sha256 {gercek[:12]} ≠ manifest {sha[:12]}")
        return sapmalar


# ================================================================================================
# YÜKLEME
# ================================================================================================

def vakalar() -> list[str]:
    """Dondurulmuş vaka dizin adları (`vaka_<tarih>_<ad>`)."""
    if not FIKSTUR_KOK.is_dir():
        return []
    return sorted(p.name for p in FIKSTUR_KOK.glob("vaka_*") if (p / MANIFEST).exists())


def yukle(ad: str) -> Vaka:
    """Vakayı adıyla yükle — tam dizin adı (`vaka_2026-08-04_x`) ya da yalnız `<ad>` verilebilir.

    Eşleşme AÇIKTIR: birden fazla vaka aynı `<ad>`ı taşıyorsa hata verir. Bulanık eşleşme, iki
    farklı arızayı aynı fikstür sanma riskidir ve bu modülün amacı tam tersidir."""
    if not FIKSTUR_KOK.is_dir():
        raise FileNotFoundError(f"fikstür kökü yok: {FIKSTUR_KOK} (ops/vaka_sabitle.py üretir)")
    adaylar = [d for d in vakalar() if d == ad or d.split("_", 2)[-1] == ad]
    if not adaylar:
        raise FileNotFoundError(f"vaka bulunamadı: {ad!r} (var olanlar: {', '.join(vakalar()) or '-'})")
    if len(adaylar) > 1:
        raise LookupError(f"{ad!r} birden çok vakayla eşleşti: {', '.join(adaylar)}")
    dizin = FIKSTUR_KOK / adaylar[0]
    man = json.loads((dizin / MANIFEST).read_text(encoding="utf-8"))
    v = Vaka(ad=adaylar[0], dizin=dizin, manifest=man)
    sapmalar = v.dogrula()
    if sapmalar:
        raise AssertionError(
            f"{v.ad}: dondurulmuş fikstür manifestle AYRIŞMIŞ — elle düzenlenmiş olabilir. "
            f"Fikstür elle onarılırsa arızayı değil onaranın hatırladığını taşır (da6bec3/v76 "
            f"dersi). Sapmalar: " + "; ".join(sapmalar))
    return v
