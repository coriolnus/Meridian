#!/usr/bin/env python3
"""ops/vaka_sabitle.py — CANLI ARIZA → DONDURULMUŞ FİKSTÜR (D3 modül 3, C2-3, 2026-08-07).

NEDEN VAR (`docs/PATTERN-ETUDU-2026-08-06.md` C2-3). Bu depoda bir canlı arızayı KALICI bir
regresyon testine çeviren yol YOKTU: fikstürler ELLE yazılıyordu ve elle yazılan fikstür,
arızanın kendisini değil arızayı yazanın HATIRLADIĞINI donduruyor. Ölçülmüş emsal: da6bec3
vakasında v76 fikstürü elle onarıldı (17→68 işlem). LangSmith'in "Add to Dataset" deseninin
Meridian karşılığı budur — ve burada bir görünüm değil MEKANİZMA olarak yazılır.

NE YAPAR. Verilen bir OLAY PENCERESİ (ts aralığı) + ilgili defter/durum adları için:
  1. kaynaktaki (yedek tarball · açılmış dizin · canlı `state/`) DURUM KESİTİNİ okur,
  2. defterlerden pencereye DÜŞEN SATIRLARI süzer,
  3. ikisini de SIR-MASKELİ ve DETERMİNİSTİK biçimde `tests/fikstur/vaka_<tarih>_<ad>/` altına
     bir KARE olarak dondurur,
  4. `VAKA.json` manifestine kaynağı, pencereyi, satır sayılarını ve her dosyanın sha256'sını
     yazar — "bu fikstür nereden geldi" sorusu bir daha cevapsız kalmasın.

KARE KAVRAMI. Bir arıza tek bir fotoğraf değildir: 2026-08-04 vakasında ÜÇ kare vardır (beyan
yerindeyken · beyan silindikten sonra · onarımdan sonra) ve regresyon testi ancak kareler
arasındaki FARKI çivileyebilir. Her `--kare` çağrısı aynı vaka klasörüne ayrı bir alt klasör
ekler; manifest kareleri birlikte tutar.

DETERMİNİZM — DAMGA YOK. Üretim ZAMANI hiçbir dosyaya yazılmaz (aynı disiplin:
`ops/runbook_uret.py`). Aynı kaynaktan aynı bayt çıkar; iki koşum arasında bir fark varsa o fark
GERÇEKTİR. JSON `sort_keys=True, indent=1, ensure_ascii=False` ile yazılır ve satır sonu tektir.

SIR MASKELEME — TEK KAYNAK. Metin alanları `agent_telemetry.sirlari_maskele` ile geçirilir; bu
fonksiyon YALNIZ sır desenlerini uygular, metnin BİÇİMİNE (satır sonu, uzunluk) dokunmaz —
`maskele()`nin tek-satıra-katla + kırp davranışı bir fikstürde veriyi bozardı. İkinci bir
maskeleme uygulaması YASAK: iki kopya sessizce ayrışır, ayrışan taraf sızdırır.

YAZMA SINIRI. Bu betik YALNIZ `tests/fikstur/` altına yazar. Kaynağa (yedek, canlı `state/`)
tek bayt yazmaz: tarball geçici bir dizine açılır, DB salt-okunur kopyadan okunur, canlı `state/`
yolunda hiçbir yazım çağrısı yoktur. Kuru koşu VARSAYILANDIR.

KULLANIM:
    # ne dondurulacağını göster (yazMAZ) — bu komut 2026-08-04 vakasının 'oncesi' karesini üretti
    python ops/vaka_sabitle.py --ad sermaye_beyani_silinmesi --tarih 2026-08-04 \
        --kare oncesi --kaynak backups/a1/state-2026-08-02.tar.gz \
        --baslangic 2026-08-01T15:14 --bitis 2026-08-01T15:15 \
        --durum portfolio.json --defter events.jsonl --defter-tam trades.jsonl \
        --aciklama "…" --kok-neden research/olcumler/portfoy_sifirlama_2026-08-04/KOKNEDEN.md

    # aynı komut + --uygula → tests/fikstur/vaka_2026-08-04_sermaye_beyani_silinmesi/kare_oncesi/
    python ops/vaka_sabitle.py ... --uygula

    python ops/vaka_sabitle.py --listele          # dondurulmuş vakalar + kareleri

  `--defter` PENCEREYLE süzülür (o pencerede OLAN şeyler: olaylar), `--defter-tam` OLDUĞU GİBİ
  alınır (o ana kadar BİRİKMİŞ taban: işlem defteri — kimlik kıyasının paydası). Tabanı
  pencereyle süzmek onu boşaltır: ölçüldü, `trades.jsonl` 95 satır → pencere içi 0.

ÇIKIŞ KODU: 0 = ok · 1 = doğrulama/argüman hatası · 2 = kaynak okunamadı.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tarfile
import tempfile
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK))

from meridian import agent_telemetry as _at   # noqa: E402  — SIR MASKELEMESİNİN TEK KAYNAĞI

FIKSTUR_KOK = KOK / "tests" / "fikstur"
MANIFEST = "VAKA.json"
OLAY_DOSYASI = "olaylar.jsonl"
DURUM_DIZINI = "durum"
DEFTER_DIZINI = "defter"
SURUM = 1

# Pencere süzmesinin baktığı zaman alanları — SIRAYLA denenir. Adlar UYDURULMADI: `events.jsonl`
# `ts`, `trades.jsonl` `ts_close`/`ts_open`, `trade_plans.jsonl`/`candidates.jsonl` `date`,
# `counterfactuals.jsonl` `date` taşır (bkz. `meridian/ledgers.py` sözleşmeleri).
TS_ALANLARI = ("ts", "ts_close", "ts_open", "date", "tarih", "decision_as_of")


# ================================================================================================
# KAYNAK — YEDEK TARBALL · AÇILMIŞ DİZİN · CANLI state/
# ================================================================================================

class Kaynak:
    """Okunabilir bir `state/` kesiti. `with Kaynak(...) as k:` içinde `k.durum(ad)` /
    `k.defter(ad)` çağrılır.

    TEK OKUMA YOLU, İKİNCİ BİR SQL UYGULAMASI YOK: kaynak dizini `config.STATE` olarak
    bağlanır ve okuma `store.read_json`/`store.read_jsonl` üzerinden yapılır. Böylece SQLite'a
    taşınmış altı defter (H9 migrasyonu) ile düz dosyalar AYNI kapıdan okunur; burada elle SQL
    yazmak, `storage`ın kolon↔satır çevirisini ikinci kez (ve yanlış) uygulamak olurdu."""

    #: Kaynaktan HER ZAMAN çıkarılan üye: SQLite'a taşınmış altı defter (H9) yalnız burada yaşar.
    DB_UYESI = "meridian.db"

    def __init__(self, yol: Path, adlar: list[str] | None = None):
        self.istenen = Path(yol)
        self.adlar = list(adlar or [])
        self._tmp: tempfile.TemporaryDirectory | None = None
        self.state: Path | None = None
        self.etiket = str(yol)

    def __enter__(self) -> "Kaynak":
        p = self.istenen
        if p.is_dir():
            # Hem `<dizin>/state/` hem doğrudan `<dizin>` (state'in kendisi) kabul edilir.
            self.state = (p / "state") if (p / "state").is_dir() else p
        elif p.suffix in (".gz", ".tgz") or p.name.endswith(".tar.gz"):
            self._tmp = tempfile.TemporaryDirectory(prefix="vaka_sabitle_")
            hedef = Path(self._tmp.name)
            self._tarballdan_ac(p, hedef)
            self.state = hedef / "state"
            self.etiket = f"{p}::state/"
        else:
            raise SystemExit(f"[vaka] kaynak bir dizin ya da .tar.gz olmalı: {p}")
        if not self.state.is_dir():
            raise SystemExit(f"[vaka] kaynakta state dizini yok: {p}")
        self._baglan()
        return self

    def _tarballdan_ac(self, tarball: Path, hedef: Path) -> None:
        """YALNIZ İSTENEN ÜYELERİ aç — tüm tarball'ı DEĞİL.

        İKİ AYRI GEREKÇE, ikisi de ölçülmüş: (a) BOYUT — canlı yedek 112 MB'dır (ölçüm:
        `backups/a1/state-2026-08-02.tar.gz`) ve fikstür için gereken üç dosyadır; komple açmak
        bir fikstür işini bir disk işine çevirir. (b) GÜVENLİK — yedek `state/sprint/*/skills`
        altında MUTLAK YOLA giden symlink'ler taşıyor (kum havuzu kurulumundan kalma) ve
        Python 3.12'nin `data` filtresi bunları haklı olarak reddediyor (`AbsoluteLinkError`).
        Süzerek açmak, filtreyi gevşetmeden sorunu ortadan kaldırır: symlink üyeleri hiç
        dokunulmaz, açılan her üye DÜZ DOSYADIR ve düz dosya olduğu ayrıca DOĞRULANIR."""
        hedef_state = hedef / "state"
        hedef_state.mkdir(parents=True, exist_ok=True)
        istenen = {f"state/{self.DB_UYESI}"} | {f"state/{a}" for a in self.adlar}
        # Migrasyon sonrası düz dosyalar `.migrated` ekiyle DONAR; DB yoksa (eski yedek) o kopya
        # tek kaynaktır, o yüzden ikisi de aranır.
        istenen |= {a + ".migrated" for a in list(istenen)}
        with tarfile.open(tarball) as t:
            for uye in t.getmembers():
                if uye.name not in istenen:
                    continue
                if not uye.isfile():
                    continue          # symlink/dizin: fikstür kaynağı olamaz, sessizce değil
                f = t.extractfile(uye)
                if f is None:
                    continue
                (hedef / uye.name).parent.mkdir(parents=True, exist_ok=True)
                (hedef / uye.name).write_bytes(f.read())

    def _baglan(self) -> None:
        from meridian import config, storage
        self._eski = (config.STATE, config.BARS, config.HISTORY)
        storage.close_connections()
        config.STATE = self.state
        config.BARS = self.state / "bars"
        config.HISTORY = self.state / "history"

    def __exit__(self, *exc):
        from meridian import config, storage
        storage.close_connections()
        config.STATE, config.BARS, config.HISTORY = self._eski
        if self._tmp is not None:
            self._tmp.cleanup()
        return False

    def durum(self, ad: str):
        from meridian import store
        return store.read_json(ad, None)

    def defter(self, ad: str) -> list[dict]:
        from meridian import store
        return store.read_jsonl(ad)


# ================================================================================================
# SÜZME + MASKELEME
# ================================================================================================

def satir_zamani(satir: dict) -> str | None:
    """Satırın zaman damgası — UYDURULMAZ. Hiçbir bilinen alan yoksa None ve satır penceresiz
    sayılır (çağıran onu `zamansiz` kovasında AYRI raporlar; sessizce atmak veya sessizce almak
    ikisi de yalan olurdu)."""
    for alan in TS_ALANLARI:
        v = satir.get(alan)
        if isinstance(v, str) and v:
            return v
    return None


def pencerede(satir: dict, baslangic: str | None, bitis: str | None) -> bool | None:
    """Satır pencerede mi? None = ZAMANI ÖLÇÜLEMEDİ (ne 'içinde' ne 'dışında')."""
    ts = satir_zamani(satir)
    if ts is None:
        return None
    if baslangic and ts < baslangic:
        return False
    if bitis and ts > bitis:
        return False
    return True


def maskele_derin(o, anahtar=None):
    """Sözlük/liste ağacındaki string yapraklarına sır maskelemesi uygular — İKİ KURALLA:

      (a) ANAHTARI sır adı olan değer (`api_key`, `dash_token`, …) TAMAMEN maskelenir. Sözlükte
          her değerin bir adı vardır; sırrı adından yakalamak, gövdesinden tahmin etmekten hem
          kesin hem ucuzdur.
      (b) Geri kalan metinlerde YALNIZ ÇAPALI desenler koşar (`ad=<değer>`, `Bearer <jeton>`) —
          çıplak-jeton sezgisi KAPALIDIR. Gerekçesi ölçülmüş bir yanlış pozitiftir: bu betiğin
          ilk koşumunda `plan_id = "P-2026-07-23-TMO-momentum_burst"` (32 karakter, harf+rakam)
          «uzun-jeton» diye maskelendi ve fikstür vakanın VERİSİNİ kaybetti. Bir fikstürün sırrı
          sızmamalı, ama verisi de bozulmamalı — ikisi aynı anda ancak bu ayrımla mümkün.

    ANAHTARLARIN KENDİSİNE DOKUNULMAZ: bir anahtar sırrın ADIdır, değeri değil, ve adı korumak
    teşhistir. Sayı/bool/None aynen geçer: bir fikstürün sayısını maskelemek onu ölçülemez yapardı."""
    if isinstance(o, dict):
        return {k: maskele_derin(v, k) for k, v in o.items()}
    if isinstance(o, list):
        return [maskele_derin(v, anahtar) for v in o]
    if isinstance(o, str):
        if anahtar is not None and _at.gizli_ad(anahtar):
            return "«gizli»"
        return _at.sirlari_maskele(o, ciplak_jeton=False)
    return o


def maske_sayisi(metin: str) -> int:
    """Üretilen dosyada kaç maske izi var? Manifeste yazılır — SESSİZ MASKELEME YOK: bir fikstürün
    kaç alanının kırpıldığı, onu okuyanın bilmesi gereken bir olgudur."""
    return metin.count("«gizli»") + metin.count("«uzun-jeton»")


# ================================================================================================
# YAZIM (deterministik)
# ================================================================================================

def _json_metni(o) -> str:
    return json.dumps(o, ensure_ascii=False, indent=1, sort_keys=True) + "\n"


def _jsonl_metni(rows: list[dict]) -> str:
    return "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows)


def _sha256(metin: str) -> str:
    return hashlib.sha256(metin.encode("utf-8")).hexdigest()


def vaka_dizini(ad: str, tarih: str) -> Path:
    return FIKSTUR_KOK / f"vaka_{tarih}_{ad}"


def manifest_oku(dizin: Path) -> dict:
    p = dizin / MANIFEST
    if p.exists():
        return json.loads(p.read_text())
    return {}


# ================================================================================================
# ANA İŞ
# ================================================================================================

def sabitle(*, ad: str, tarih: str, kare: str, kaynak: Path, baslangic: str | None,
            bitis: str | None, durumlar: list[str], defterler: list[str],
            tam_defterler: list[str], aciklama: str, kok_neden: str | None,
            uygula: bool) -> dict:
    """Bir kareyi dondur (ya da kuru koşuda ne dondurulacağını hesapla). Dönüş: kare özeti.

    `defterler` PENCEREYLE süzülür, `tam_defterler` OLDUĞU GİBİ alınır ve bu ayrım zorunludur:
    bir arızanın bazı girdileri "o pencerede olan şeyler" (olaylar), bazıları ise "o ana kadar
    BİRİKMİŞ taban"dır (işlem defteri — kimlik kıyasının paydası). Tabanı pencereyle süzmek onu
    boşaltır ve kimlik testi hiç kurulamaz (ölçüldü: `trades.jsonl` 95 satır → pencere içi 0)."""
    dizin = vaka_dizini(ad, tarih)
    kare_dizini = dizin / f"kare_{kare}"
    dosyalar: dict[str, str] = {}          # göreli yol → içerik metni
    ozet: dict = {"kaynak": str(kaynak), "pencere": {"baslangic": baslangic, "bitis": bitis},
                  "durum": {}, "defter": {}}

    with Kaynak(kaynak, adlar=list(durumlar) + list(defterler) + list(tam_defterler)) as k:
        for dad in durumlar:
            doc = k.durum(dad)
            if doc is None:
                raise SystemExit(f"[vaka] durum belgesi kaynakta YOK ya da okunamadı: {dad} "
                                 f"({k.etiket}) — eksik bir kesiti donduramayız")
            metin = _json_metni(maskele_derin(doc))
            dosyalar[f"{DURUM_DIZINI}/{dad}"] = metin
            ozet["durum"][dad] = {"sha256": _sha256(metin), "bayt": len(metin.encode("utf-8")),
                                  "maskelenen": maske_sayisi(metin)}
        for lad in list(defterler) + list(tam_defterler):
            tam = lad in tam_defterler
            ham = k.defter(lad)
            icinde, zamansiz = [], 0
            for r in ham:
                v = True if tam else pencerede(r, baslangic, bitis)
                if v is None:
                    zamansiz += 1
                elif v:
                    icinde.append(r)
            rows = [maskele_derin(r) for r in icinde]
            hedef = OLAY_DOSYASI if lad == "events.jsonl" else f"{DEFTER_DIZINI}/{lad}"
            metin = _jsonl_metni(rows)
            dosyalar[hedef] = metin
            ozet["defter"][lad] = {"dosya": hedef, "kaynak_satir": len(ham), "alinan": len(rows),
                                   "pencereli": not tam, "zamansiz_atlanan": zamansiz,
                                   "sha256": _sha256(metin), "bayt": len(metin.encode("utf-8")),
                                   "maskelenen": maske_sayisi(metin)}

    ozet["dosya_n"] = len(dosyalar)
    if not uygula:
        return ozet

    # --- YAZIM: kare dizini TAMAMEN yeniden kurulur (yarım kalmış eski bir kare kalmasın) ------
    if kare_dizini.exists():
        shutil.rmtree(kare_dizini)
    for rel, metin in dosyalar.items():
        yol = kare_dizini / rel
        yol.parent.mkdir(parents=True, exist_ok=True)
        yol.write_text(metin, encoding="utf-8")

    man = manifest_oku(dizin)
    man.setdefault("surum", SURUM)
    man["ad"], man["tarih"] = ad, tarih
    man["aciklama"] = aciklama or man.get("aciklama", "")
    if kok_neden:
        man["kok_neden"] = kok_neden
    man.setdefault("maskeleme",
                   "meridian.agent_telemetry.sirlari_maskele(ciplak_jeton=False) + gizli_ad "
                   "(TEK KAYNAK). İki kural: (a) anahtarı sır adı olan değer tamamen «gizli», "
                   "(b) metinde yalnız ÇAPALI desenler (ad=<değer>, Bearer <jeton>). Çıplak-jeton "
                   "sezgisi KAPALI — yapılandırılmış veride yanlış pozitif üretiyordu (ölçüldü: "
                   "plan_id maskelenmişti). Metnin biçimi/uzunluğu DEĞİŞTİRİLMEZ; her dosyanın "
                   "`maskelenen` sayacı kaç maske uygulandığını söyler (sessiz maskeleme yok)")
    man.setdefault("uretici", "ops/vaka_sabitle.py")
    man.setdefault("kareler", {})
    man["kareler"][kare] = ozet
    (dizin / MANIFEST).write_text(_json_metni(man), encoding="utf-8")
    return ozet


def listele() -> int:
    if not FIKSTUR_KOK.is_dir():
        print("[vaka] tests/fikstur/ yok — henüz dondurulmuş vaka yok")
        return 0
    n = 0
    for d in sorted(FIKSTUR_KOK.glob("vaka_*")):
        man = manifest_oku(d)
        kareler = ", ".join(sorted(man.get("kareler", {}))) or "(kare yok)"
        print(f"  {d.name}\n      kareler: {kareler}\n      {man.get('aciklama', '')}")
        n += 1
    print(f"[vaka] {n} dondurulmuş vaka")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="canlı arıza → dondurulmuş regresyon fikstürü")
    ap.add_argument("--listele", action="store_true", help="dondurulmuş vakaları bas ve çık")
    ap.add_argument("--ad", help="vaka adı (snake_case; dizin adına girer)")
    ap.add_argument("--tarih", help="vaka tarihi YYYY-MM-DD (dizin adına girer)")
    ap.add_argument("--kare", default="ana", help="kare adı (ör. oncesi/arizali/onarim)")
    ap.add_argument("--kaynak", help="yedek .tar.gz, açılmış dizin ya da canlı state kökü")
    ap.add_argument("--baslangic", default=None, help="pencere başı (ISO ön-eki; dâhil)")
    ap.add_argument("--bitis", default=None, help="pencere sonu (ISO ön-eki; dâhil)")
    ap.add_argument("--durum", action="append", default=[], help="dondurulacak durum belgesi (tekrarlanır)")
    ap.add_argument("--defter", action="append", default=[], help="pencereden süzülecek defter (tekrarlanır)")
    ap.add_argument("--defter-tam", action="append", default=[],
                    help="PENCERESİZ (tamamı alınacak) defter — birikmiş taban için (tekrarlanır)")
    ap.add_argument("--aciklama", default="", help="vakanın tek cümlelik tanımı")
    ap.add_argument("--kok-neden", default=None, help="kök-neden belgesinin depo-içi yolu")
    ap.add_argument("--uygula", action="store_true", help="YAZ (varsayılan: kuru koşu)")
    a = ap.parse_args(argv)

    if a.listele:
        return listele()
    eksik = [n for n in ("ad", "tarih", "kaynak") if not getattr(a, n)]
    if eksik:
        ap.error("eksik argüman: " + ", ".join("--" + n for n in eksik))
    if not (a.durum or a.defter or a.defter_tam):
        ap.error("en az bir --durum ya da --defter gerekir (boş fikstür bir fikstür değildir)")

    kaynak = Path(a.kaynak)
    if not kaynak.exists():
        print(f"[vaka] kaynak yok: {kaynak}", file=sys.stderr)
        return 2
    ozet = sabitle(ad=a.ad, tarih=a.tarih, kare=a.kare, kaynak=kaynak,
                   baslangic=a.baslangic, bitis=a.bitis, durumlar=a.durum, defterler=a.defter,
                   tam_defterler=a.defter_tam, aciklama=a.aciklama, kok_neden=a.kok_neden,
                   uygula=a.uygula)
    kip = "YAZILDI" if a.uygula else "KURU KOŞU (yazılmadı)"
    print(f"[vaka] {kip} — vaka_{a.tarih}_{a.ad} / kare_{a.kare}")
    print(f"       kaynak: {ozet['kaynak']}")
    print(f"       pencere: {ozet['pencere']['baslangic']} → {ozet['pencere']['bitis']}")
    for dad, d in sorted(ozet["durum"].items()):
        print(f"       durum   {dad}: {d['bayt']} bayt · maskelenen {d['maskelenen']} "
              f"· sha256 {d['sha256'][:12]}")
    for lad, d in sorted(ozet["defter"].items()):
        print(f"       defter  {lad}: {d['alinan']}/{d['kaynak_satir']} satır alındı "
              f"({'pencereli' if d['pencereli'] else 'PENCERESİZ (tamamı)'}; zamansız atlanan "
              f"{d['zamansiz_atlanan']}) · maskelenen {d['maskelenen']} "
              f"· sha256 {d['sha256'][:12]}")
    if not a.uygula:
        print("       --uygula ile yaz")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
