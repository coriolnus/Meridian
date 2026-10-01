#!/usr/bin/env python3
"""EXE-2026-012 — KILL#1 canlı çapası: HÜKÜM BETİĞİ (B dilimi, 2026-10-01). Aletin defterinin OKUYUCUSU (Yasa 6).

KART: research/cards/EXE-2026-012-kill1-canli-capa.yaml — hipotez, eşikler, kill-list, pozitif kontrol ORADA DONUK.
Betik eşikleri KARTTAN okur (kodda gömülü eşik yok), karta YAZMAZ, hükmü İŞLEMEZ: hüküm Rol-1'in okuduğu bir ÖLÇÜMDÜR
(kart kill_list "OTOMATİK KAPI YASAĞI"). Çivi dosyası: tests/test_exe012_hukum_v607.py.

GİRDİLER
  defter  `state/exe012_tur_atif.jsonl` — yazan `meridian.intraday_cycle.IntradayConsumer._atif_bosalt`; satır = bir
          sürecin bir seanstaki olayları (alanlar satırın `alanlar` başlığında, kayıt yuvarlamasız).
  tanık   isteğe bağlı: Prometheus HTTP API yanıtları, satır başına bir JSON (`/api/v1/query_range` → matrix ya da
          `/api/v1/query` → vector; metrik `meridian_intraday_cycle_seconds_bucket`). Betik Prometheus'a KENDİSİ
          BAĞLANMAZ — Rol-1 A1'de çeker, dosyayı verir (`tanik-plani` seans başına sorguyu ET'den, DST-doğru basar).
  ADIM-0b için planli defter (`intraday_shadow_planli_orders.jsonl`) ve karar defteri (`intraday_decisions.jsonl`).
ÇIKTI: tek JSON — `--cikti` yoluna (stdout'a tek satır özet) ya da stdout'a. Başka HİÇBİR yere yazmaz.

SÖZLEŞME KOMUT SATIRIDIR (A1, Rol-1, salt-okur; çalışma dizini /opt/meridian):
  python research/olcumler/exe012_kill1_canli/hukum.py hukum --defter state/exe012_tur_atif.jsonl \\
      --baslangic YYYY-AA-GG --yeniden-baslatma-esigi {acilis|pencere} [--tanik T.jsonl] [--bakis 1|2] \\
      [--kusurlu-kok-neden-kartta GUN ...] [--kart K.yaml] [--cikti sonuc.json]
  … adim0a --tanik T.jsonl [--gun GUN ...] [--cikti …]
  … adim0b --planli-defter P --karar-defteri K --adim0a A0.json --baslangic GUN [--bitis GUN] [--cikti …]
  … adim0c --defter D --seans GUN [--tanik T.jsonl] [--cikti …]
  … tanik-plani --gun GUN [GUN ...]
Çıkış kodu: 0 tamam (hüküm sonucun İÇİNDE) · 2 kullanım ya da girdi hatası (mesaj stderr'de).

HÜKÜM (kart `olcum_plani`)
  EVREN      pencerenin TEMİZ seanslarının `processed` olayları (`HUKUM_EVRENI`); `error` sayılır, havuza girmez.
  TEMİZ      seans içinde yeniden başlatma yok ∧ tanık 'kusurlu' değil; ayrıca okuyucunun gördüğü veri kayıpları
             (bozuk/yarım satır → `eksik`, seans ortası `kapanis` → `kismi`, defteri olmayan seans günü → `defter_yok`).
  YENİDEN BAŞLATMA  satırlar (seans, surec_baslangic, pid) ile birleşir; bir sürecin başlangıcı seansın EŞİK anı ile
             kapanışı arasındaysa seans içi yeniden başlatmadır. EŞİK SAATİ KARTTA YOK ("seans içi" — 09:30 açılış mı,
             09:45 giriş penceresi mi?): Rol-1 `--yeniden-baslatma-esigi` ile seçer (varsayılan YOK); her seans iki
             adayla da sınıflanır, ayrışanlar `esik_duyarliligi`nda adıyla.
  PENCERE    `--baslangic`tan itibaren ilk N temiz seans; N = kart `pencere_seans` × `--bakis` (ikinci bakış "+20").
  R          Y = X − Z; R = p95(X_havuz) / p95(Y_havuz); p95 `meridian.olcum_araclari.p95` (v217 `_p95` ile özdeş).
  CI         SEANS-kümeli bootstrap — `meridian.olcum_araclari.kume_bootstrap` (faz5 ile ORTAK gövde); B, seviye karttan,
             tohum `olcum_araclari.BOOTSTRAP_TOHUM` (= faz5_cikis.BOOTSTRAP_TOHUM).
  ÜÇLÜ       R > tavan → KILL · R ≤ tavan ∧ CI_üst ≤ tavan → YEŞİL · aksi → ÖLÇÜLEMEDİ (sınırda pay YOK).
  GEÇERLİLİK üçlünün ÜSTÜNDE: şema ihlali / Y ≤ 0 / zaman tutarsızlığı → GEÇERSİZ; pencere dolmadı / kusurlu tanığın
             kök nedeni karta yazılmadı / yazım < n_yazim_min / takvim yok → ÖLÇÜLEMEDİ. Nihai karar ile üçlü AYRI
             alanlarda; R tavanı aşarken geçerlilik ÖLÇÜLEMEDİ diyorsa `tavan_asildi` bunu adıyla gösterir.
  TANIK      defter X'leri tanığın kova sınırlarıyla MOTORUN KENDİ `gecikme.Histogram`ında (bisect_left — le kuralı)
             binlenir; Prometheus processed sayaçlarının iki seans-dışı sınır anı (09:45 ET öncesi son ortak örnek ·
             kapanış sonrası ilk ortak örnek, aynı ET günü) farkıyla kıyaslanır. Sınırda örnek yok ya da arada sayaç
             azalmış → 'tanıksız' (dışlanmaz); sayım farklı → 'kusurlu' (alet kusuru, seans düşer ve kök neden karta
             yazılana dek hüküm durur). `error` farkı yalnız raporlanır.
  TANILAR    t1–t6 (kart TANILAR) — hüküm üretmez.

BAĞIMLILIK: stdlib + PyYAML + numpy; `meridian`dan YALNIZ SAF YAPRAKLAR (`IZINLI_MERIDIAN_MODULLERI`: barclock — tek
takvim/saat yolu, gecikme — le binlemesi, olcum_araclari — p95 + küme bootstrap). obs/store/config YÜKLENMEZ: betik canlı
deftere ya da `state/`e yazamaz (v607 H: statik kapanış + operatör biçiminde ayrı süreç ölçümü). Betik kendi ağacını
`sys.path` başına koyar — venv'e kurulu başka bir kopyanın motoru yüklenmez.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import itertools
import json
import math
import pathlib
import re
import statistics
import sys

import yaml

KOK = pathlib.Path(__file__).resolve().parents[3]
if not sys.path or sys.path[0] != str(KOK):
    sys.path.insert(0, str(KOK))       # KENDİ ağacının motoru (worktree tuzağı: venv ana checkout'a kurulu)

from meridian import barclock, gecikme, olcum_araclari  # noqa: E402  — YALNIZ saf yapraklar (v607 H1)

# ---- sözleşme sabitleri (aletle AYRIŞMA çivisi v607 I2) ----------------------------------------------------------
KART_KIMLIGI = "EXE-2026-012"
KART_YOLU = KOK / "research" / "cards" / "EXE-2026-012-kill1-canli-capa.yaml"
SEMA = 1
GEREKLI_ALANLAR = ("outcome", "x_s", "z_s", "ofset_s", "planli_giris", "planli_yazim")
BOSALTMA_SOZLUGU = ("seans_kapandi", "seans_degisti", "kapanis")
BOSALTMA_KAPANIS = "kapanis"
HUKUM_EVRENI = ("processed",)
IZINLI_MERIDIAN_MODULLERI = ("barclock", "gecikme", "olcum_araclari")
YENIDEN_BASLATMA_ESIKLERI = ("acilis", "pencere")
KILL, YESIL, OLCULEMEDI, GECERSIZ = "KILL", "YEŞİL", "ÖLÇÜLEMEDİ", "GEÇERSİZ"
TANIK_ESIT, TANIK_YOK, TANIK_KUSURLU = "eşit", "tanıksız", "kusurlu"
METRIK = "meridian_intraday_cycle_seconds_bucket"
PROMETHEUS_ADRESI = "http://127.0.0.1:9095"   # kart adim0 ADIM-0a ("Prometheus 127.0.0.1:9095") — yalnız plan metni
T5_PENCERE_S = 60.0                            # kart TANILAR t5: "önceki 60 s ile sonraki 60 s (bir bar periyodu)"
F_YAZIM_DUZELTME_ESIGI = 0.05                  # kart adim0 ADIM-0b: "f_yazim ≥ %5 ise beyanli_sinirlar(1) … düzeltilir"
# Sınıf önceliği (bir seans birden çok nedene sahip olabilir; hepsi `nedenler`de, `sinif` ilkidir).
SEANS_SINIFLARI = ("takvim_yok", "seans_disi", "eksik", "defter_yok", "yeniden_baslatma", "kismi", "kusurlu",
                   "islenen_yok")

# p95 ve kantil TEK TANIMDAN (v217 `_p95` ile özdeş; ikinci gövde yok — v607 A1).
p95 = olcum_araclari.p95
sirali_kantil = olcum_araclari.sirali_kantil

_SEANS_RE = re.compile(r'"seans":\s*"(\d{4}-\d{2}-\d{2})"')
_GUN_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


# =================================================================================================================
# yardımcılar
# =================================================================================================================

def _sha256(yol) -> str:
    return hashlib.sha256(pathlib.Path(yol).read_bytes()).hexdigest()


def _iso(metin) -> dt.datetime:
    """ISO-8601 → tz'li UTC (tz'siz damga UTC sayılır — aletin damgaları hep tz'lidir)."""
    a = dt.datetime.fromisoformat(str(metin))
    return (a if a.tzinfo else a.replace(tzinfo=dt.timezone.utc)).astimezone(dt.timezone.utc)


def _gun(metin: str) -> str:
    if not isinstance(metin, str) or not _GUN_RE.match(metin):
        raise ValueError(f"gün YYYY-AA-GG olmalı: {metin!r}")
    dt.date.fromisoformat(metin)
    return metin


def _et_an(gun: str, dakika: int) -> dt.datetime:
    """ET duvar saatinde `gun` + `dakika` (gece yarısından) → UTC. DST zoneinfo'dan (barclock.NY — tek saat yolu)."""
    d = dt.date.fromisoformat(gun)
    yerel = dt.datetime.combine(d, dt.time(dakika // 60, dakika % 60), tzinfo=barclock.NY)
    return yerel.astimezone(dt.timezone.utc)


def seans_sinirlari(gun: str) -> dict:
    """O günün XNYS seans aralığı (`barclock.seans_araligi` — tek takvim yolu; erken kapanış 13:00 ET dahil) + giriş
    penceresi anı (`barclock.ENTRY_WINDOW_ET_MIN`) + ET gün sınırları. Hepsi UTC."""
    durum, acilis, kapanis, hata = barclock.seans_araligi(gun)
    utc = dt.timezone.utc
    ertesi = (dt.date.fromisoformat(gun) + dt.timedelta(days=1)).isoformat()
    return {"durum": durum, "hata": hata,
            "acilis": acilis.astimezone(utc) if acilis else None,
            "kapanis": kapanis.astimezone(utc) if kapanis else None,
            "pencere": _et_an(gun, barclock.ENTRY_WINDOW_ET_MIN),
            "gun_basi": _et_an(gun, 0), "gun_sonu": _et_an(ertesi, 0)}


def _seans_gunleri(bas: str, son: str) -> list:
    """[bas, son] arasındaki XNYS seans günleri (takvim okunamazsa gün yine döner — sınıfı `takvim_yok` olur)."""
    out, d, bitis = [], dt.date.fromisoformat(bas), dt.date.fromisoformat(son)
    while d <= bitis:
        if d.weekday() < 5 and barclock.seans_araligi(d.isoformat())[0] in ("ok", "takvim_yok"):
            out.append(d.isoformat())
        d += dt.timedelta(days=1)
    return out


def _bol(a, b):
    """a / b; payda sıfır ya da yoksa None (ölçülemeyen oran UYDURULMAZ)."""
    return None if (a is None or not b) else a / b


def _ozet(vals: list) -> dict:
    return {"n": len(vals), "medyan_y": (statistics.median(vals) if vals else None),
            "p95_y": (p95(vals) if vals else None)}


# =================================================================================================================
# kart
# =================================================================================================================

def kart_esikleri(yol=None) -> dict:
    """Kartın `esikler` alanı — TEK kaynak. Eksik eşik `ValueError` (kodda yedek değer YOK)."""
    yol = pathlib.Path(yol or KART_YOLU)
    kart = yaml.safe_load(yol.read_text(encoding="utf-8")) or {}
    if kart.get("card_id") != KART_KIMLIGI:
        raise ValueError(f"kart kimliği {kart.get('card_id')!r} ≠ {KART_KIMLIGI} ({yol})")
    e = kart.get("esikler") or {}
    out = {}
    for ad, tip in (("tavan_R", float), ("ci_seviye", float), ("bootstrap_B", int), ("pencere_seans", int),
                    ("n_yazim_min", int)):
        if e.get(ad) is None:
            raise ValueError(f"kart eşiği yok: esikler.{ad} ({yol})")
        out[ad] = tip(e[ad])
    out["p95_tanimi"] = e.get("p95_tanimi")
    out["tohum"] = olcum_araclari.BOOTSTRAP_TOHUM
    out["kart_yolu"] = str(yol)
    out["kart_sha256"] = _sha256(yol)
    return out


# =================================================================================================================
# defter
# =================================================================================================================

def _sema_denetimi(v) -> str | None:
    """Satır aletin sözleşmesine uyuyor mu? Uymuyorsa nedenin metni (okuyucu ile yazar ayrışmış → GEÇERSİZ)."""
    if not isinstance(v, dict):
        return "satır JSON nesnesi değil"
    if v.get("kart") != KART_KIMLIGI:
        return f"kart {v.get('kart')!r}"
    if v.get("sema") != SEMA:
        return f"şema {v.get('sema')!r} (okuyucu {SEMA})"
    alanlar = v.get("alanlar")
    if not isinstance(alanlar, list) or not set(GEREKLI_ALANLAR) <= set(alanlar):
        return f"alanlar {alanlar!r}"
    if v.get("bosaltma") not in BOSALTMA_SOZLUGU:
        return f"bosaltma {v.get('bosaltma')!r}"
    if not isinstance(v.get("seans"), str) or not _GUN_RE.match(v["seans"]):
        return f"seans {v.get('seans')!r}"
    if not isinstance(v.get("pid"), int):
        return f"pid {v.get('pid')!r}"
    for alan in ("surec_baslangic", "yazim_ts"):
        try:
            _iso(v.get(alan))
        except (TypeError, ValueError):
            return f"{alan} {v.get(alan)!r}"
    olaylar = v.get("olaylar")
    if not isinstance(olaylar, list) or v.get("n") != len(olaylar):
        return f"n {v.get('n')!r} ≠ olay sayısı"
    ix = {a: alanlar.index(a) for a in GEREKLI_ALANLAR}
    for o in olaylar:
        if not isinstance(o, list) or len(o) != len(alanlar):
            return "olay biçimi alanlarla uyuşmuyor"
        if not isinstance(o[ix["outcome"]], str):
            return f"outcome {o[ix['outcome']]!r}"
        for a in ("x_s", "z_s", "ofset_s"):
            d = o[ix[a]]
            if isinstance(d, bool) or not isinstance(d, (int, float)) or not math.isfinite(d):
                return f"{a} {d!r}"
        for a in ("planli_giris", "planli_yazim"):
            if isinstance(o[ix[a]], bool) or not isinstance(o[ix[a]], int) or o[ix[a]] < 0:
                return f"{a} {o[ix[a]]!r}"
    return None


def defter_oku(yol) -> dict:
    """Defteri okur: geçerli satırlar (`veri` + `bayt`), bozuk (yarım) satırlar ve şema ihlalleri AYRI listelerde.

    Bozuk satır SIGKILL/OOM'un beyanlı izidir (alet şerhi): ayıklanır, seansı ADIYLA `eksik` sayılır — sessiz düşmez."""
    satirlar, bozuk, ihlal = [], [], []
    with open(yol, "rb") as f:
        for no, ham in enumerate(f, 1):
            if not ham.strip():
                continue
            metin = ham.decode("utf-8", "replace")
            try:
                veri = json.loads(metin)
            except json.JSONDecodeError:   # sessiz-yutma DEĞİL: bozuk satır `bozuk` listesine seansıyla girer ve seansı EKSİK yapar
                es = _SEANS_RE.search(metin)
                bozuk.append({"satir_no": no, "seans": es.group(1) if es else None})
                continue
            neden = _sema_denetimi(veri)
            if neden:
                ihlal.append({"satir_no": no, "neden": neden})
                continue
            satirlar.append({"satir_no": no, "veri": veri, "bayt": len(ham)})
    return {"satirlar": satirlar, "bozuk": bozuk, "sema_ihlali": ihlal}


def surec_seanslari(satirlar: list) -> dict:
    """Satırları (seans, surec_baslangic, pid) ile BİRLEŞTİRİR: bir süreç bir seansa birden çok satır yazabilir (ara
    `seans_kapandi`, kapanış kuyruğu). Olaylar alan ADIYLA çözülür (satırın kendi `alanlar` başlığından)."""
    out: dict = {}
    for s in satirlar:
        v = s["veri"]
        anahtar = (v["seans"], v["surec_baslangic"], v["pid"])
        k = out.setdefault(anahtar, {"seans": v["seans"], "surec_baslangic": v["surec_baslangic"], "pid": v["pid"],
                                     "olaylar": [], "bosaltmalar": [], "yazimlar": [], "satir_kb": []})
        alanlar = v["alanlar"]
        k["olaylar"].extend(dict(zip(alanlar, o)) for o in v["olaylar"])
        k["bosaltmalar"].append(v["bosaltma"])
        k["yazimlar"].append(v["yazim_ts"])
        k["satir_kb"].append(s["bayt"] / 1024.0)
    return out


def _islenen(olaylar) -> list:
    return [o for o in olaylar if o["outcome"] in HUKUM_EVRENI]


# =================================================================================================================
# tanık (Prometheus dışa aktarımı)
# =================================================================================================================

def tanik_oku(yol) -> dict:
    """Prometheus yanıt satırları → {(outcome, le): {ts: değer}}. Tek kaynak (job, instance) şart; çelişen örnek hata."""
    seriler: dict = {}
    kaynaklar, yok_sayilan = set(), 0
    with open(yol, encoding="utf-8") as f:
        for no, satir in enumerate(f, 1):
            if not satir.strip():
                continue
            yanit = json.loads(satir)
            if yanit.get("status") != "success":
                raise ValueError(f"tanık satır {no}: status {yanit.get('status')!r}")
            veri = yanit.get("data") or {}
            tip = veri.get("resultType")
            if tip not in ("matrix", "vector"):
                raise ValueError(f"tanık satır {no}: resultType {tip!r}")
            for seri in veri.get("result") or []:
                metrik = seri.get("metric") or {}
                if metrik.get("__name__") != METRIK:
                    yok_sayilan += 1
                    continue
                kaynaklar.add((metrik.get("job"), metrik.get("instance")))
                hedef = seriler.setdefault((metrik.get("outcome"), metrik.get("le")), {})
                for ts, deger in (seri.get("values") or []) if tip == "matrix" else [seri.get("value")]:
                    ts, deger = float(ts), float(deger)
                    if hedef.get(ts, deger) != deger:
                        raise ValueError(f"tanık satır {no}: aynı ana çelişen iki örnek ({metrik})")
                    hedef[ts] = deger
    if len(kaynaklar) > 1:
        raise ValueError(f"tanıkta birden çok kaynak: {sorted(map(str, kaynaklar))}")
    return {"seriler": seriler, "kaynak": (sorted(map(str, kaynaklar)) or [None])[0], "yok_sayilan_seri": yok_sayilan}


def _le_sirasi(etiketler) -> list:
    """le etiketleri artan sınır sırasıyla, `+Inf` en sonda."""
    return sorted((e for e in etiketler if e != "+Inf"), key=float) + (["+Inf"] if "+Inf" in etiketler else [])


def _sinir_anlari(tanik: dict, sinir: dict) -> tuple:
    """(t0, t1, neden): processed serilerinin ORTAK örnek anlarından 09:45 ET öncesi SON ve kapanış sonrası İLK (aynı ET
    günü). Bulunamazsa ya da arada bir processed sayacı azalmışsa (sıfırlanma) t0/t1 None ve neden dolu."""
    proc = {le: n for (o, le), n in tanik["seriler"].items() if o == "processed"}
    if "+Inf" not in proc:
        return None, None, "tanıkta processed `+Inf` serisi yok"
    ortak = set.intersection(*(set(n) for n in proc.values()))
    onceler = [t for t in ortak if sinir["gun_basi"].timestamp() <= t < sinir["pencere"].timestamp()]
    sonralar = [t for t in ortak if sinir["kapanis"].timestamp() < t < sinir["gun_sonu"].timestamp()]
    if not onceler:
        return None, None, "sınırda örnek yok: 09:45 ET öncesinde (önce) ortak processed örneği bulunmadı"
    if not sonralar:
        return None, None, "sınırda örnek yok: kapanıştan sonra (sonra) ortak processed örneği bulunmadı"
    t0, t1 = max(onceler), min(sonralar)
    for le, noktalar in proc.items():
        ara = [noktalar[t] for t in sorted(noktalar) if t0 <= t <= t1]
        if any(b < a for a, b in zip(ara, ara[1:])):
            return None, None, f"sayaç sıfırlandı (processed le={le} sınırlar arasında azaldı) — fark tanık değil"
    return t0, t1, None


def _tanik_seans(tanik, sinir: dict, xs: list, n_error: int) -> dict:
    """Bir seansın tanık hükmü: eşit / tanıksız / kusurlu (+ neden, sayımlar)."""
    if tanik is None:
        return {"durum": TANIK_YOK, "neden": "tanık dosyası verilmedi"}
    if sinir["durum"] != "ok":
        return {"durum": TANIK_YOK, "neden": f"seans aralığı yok ({sinir['durum']})"}
    t0, t1, neden = _sinir_anlari(tanik, sinir)
    if neden:
        return {"durum": TANIK_YOK, "neden": neden}
    proc = {le: n for (o, le), n in tanik["seriler"].items() if o == "processed"}
    sira = _le_sirasi(proc)
    try:
        h = gecikme.Histogram("exe012_tanik_seconds", "EXE-2026-012 tanik binlemesi",
                              [float(le) for le in sira if le != "+Inf"])
    except ValueError as e:
        return {"durum": TANIK_YOK, "neden": f"tanığın kova tanımı geçersiz: {e}"}
    for x in xs:
        h.gozlemle(x)                                  # motorun KENDİ binlemesi (bisect_left — le kuralı)
    defter = h.anlik()[None]["kova_sayilari"]
    birikimli = [proc[le][t1] - proc[le][t0] for le in sira]
    prometheus = [int(c) for c in [birikimli[0]] + [b - a for a, b in zip(birikimli, birikimli[1:])]]
    err = tanik["seriler"].get(("error", "+Inf")) or {}
    out = {"t0": dt.datetime.fromtimestamp(t0, dt.timezone.utc).isoformat(),
           "t1": dt.datetime.fromtimestamp(t1, dt.timezone.utc).isoformat(),
           "prometheus_processed": sum(prometheus), "defter_processed": len(xs), "reddedilen_x": h.reddedilen,
           "error_farki": (int(err[t1] - err[t0]) if (t0 in err and t1 in err) else None), "defter_error": n_error}
    if prometheus == defter and h.reddedilen == 0:
        return {"durum": TANIK_ESIT, "neden": None, **out}
    fark = {le: {"prometheus": p, "defter": d} for le, p, d in zip(sira, prometheus, defter) if p != d}
    return {"durum": TANIK_KUSURLU, "neden": "defter kova sayımı ≠ Prometheus sınır farkı (alet kusuru)",
            "kova_farki": fark, **out}


# =================================================================================================================
# seans sınıflaması
# =================================================================================================================

def _seans_degerlendir(gun: str, kayitlar: list, eksik: bool, tanik, esik_adi: str) -> dict:
    sinir = seans_sinirlari(gun)
    olaylar = [o for k in kayitlar for o in k["olaylar"]]
    islenen = _islenen(olaylar)
    n_error = sum(1 for o in olaylar if o["outcome"] == "error")
    nedenler, gecersiz = [], []
    yb = {e: None for e in YENIDEN_BASLATMA_ESIKLERI}
    if sinir["durum"] == "takvim_yok":
        nedenler.append("takvim_yok")
    elif sinir["durum"] != "ok":
        nedenler.append("seans_disi")
        if islenen:
            gecersiz.append(f"{gun} seans günü değil ama {len(islenen)} işlenen olay taşıyor")
    else:
        for e in YENIDEN_BASLATMA_ESIKLERI:
            esik = sinir["acilis"] if e == "acilis" else sinir["pencere"]
            yb[e] = any(esik <= _iso(k["surec_baslangic"]) < sinir["kapanis"] for k in kayitlar)
        for k in kayitlar:
            if _islenen(k["olaylar"]) and _iso(k["surec_baslangic"]) >= sinir["kapanis"]:
                gecersiz.append(f"{gun} kapanıştan sonra başlamış süreç (pid {k['pid']}) işlenen olay taşıyor")
    if eksik:
        nedenler.append("eksik")
    if not kayitlar:
        nedenler.append("defter_yok")
    if yb.get(esik_adi):
        nedenler.append("yeniden_baslatma")
    if sinir["durum"] == "ok" and any(b == BOSALTMA_KAPANIS and _iso(y) < sinir["kapanis"]
                                      for k in kayitlar for b, y in zip(k["bosaltmalar"], k["yazimlar"])):
        nedenler.append("kismi")
    tanik_sonuc = _tanik_seans(tanik, sinir, [o["x_s"] for o in islenen], n_error)
    if tanik_sonuc["durum"] == TANIK_KUSURLU:
        nedenler.append("kusurlu")
    if kayitlar and not islenen:
        nedenler.append("islenen_yok")
    sinif = next((s for s in SEANS_SINIFLARI if s in nedenler), "temiz")
    return {"seans": gun, "sinif": sinif, "temiz": sinif == "temiz", "nedenler": nedenler,
            "yeniden_baslatma": yb, "tanik": tanik_sonuc, "n_processed": len(islenen), "n_error": n_error,
            "n_yazim_satir": sum(o["planli_yazim"] for o in islenen),
            "surecler": [{"surec_baslangic": k["surec_baslangic"], "pid": k["pid"], "bosaltmalar": k["bosaltmalar"],
                          "n_olay": len(k["olaylar"]), "satir_kb": k["satir_kb"]} for k in kayitlar],
            "_gecersiz": gecersiz}


# =================================================================================================================
# istatistik
# =================================================================================================================

def uclu_hukum(r, ci_ust, tavan) -> str:
    """Kartın ÜÇLÜ HÜKMÜ, sınırda pay YOK: R > tavan → KILL · R ≤ tavan ∧ CI_üst ≤ tavan → YEŞİL · aksi → ÖLÇÜLEMEDİ."""
    if r > tavan:
        return KILL
    if ci_ust is not None and ci_ust <= tavan:
        return YESIL
    return OLCULEMEDI


def r_noktasi(seans_xy: list) -> tuple:
    """(R, p95_X, p95_Y) havuzlanmış; p95_Y ≤ 0 ise R None (bölünemez — uydurulmaz)."""
    xs = [x for s, _ in seans_xy for x in s]
    ys = [y for _, s in seans_xy for y in s]
    px, py = p95(xs), p95(ys)
    return (px / py if py > 0 else None), px, py


def r_bootstrap(seans_xy: list, *, B: int, seviye: float, tohum: int) -> tuple:
    """SEANS-kümeli bootstrap (ortak çekirdek `olcum_araclari.kume_bootstrap`): her replikasyonda seçilen seansların
    TÜM olayları havuza girer, istatistik havuzun p95 oranıdır. Seans listeleri önceden sıralanır (eş sıralı koşular
    birleşir — tanım aynı, maliyet düşer)."""
    xs = [sorted(x) for x, _ in seans_xy]
    ys = [sorted(y) for _, y in seans_xy]

    def istatistik(sec):
        out = []
        for satir in sec.tolist():
            hx = list(itertools.chain.from_iterable(xs[i] for i in satir))
            hy = list(itertools.chain.from_iterable(ys[i] for i in satir))
            out.append(p95(hx) / p95(hy))
        return out

    return olcum_araclari.kume_bootstrap(len(seans_xy), istatistik, n_ornek=B, seviye=seviye, tohum=tohum)


def _tanilar(pencere: list, seans_olaylari: dict, seans_kayitlari: dict) -> dict:
    """Kart TANILAR t1–t6 — hüküm üretmez, K'ye girmez."""
    havuz = [(g, o) for g in pencere for o in _islenen(seans_olaylari[g])]
    X = [o["x_s"] for _, o in havuz]
    Y = [o["x_s"] - o["z_s"] for _, o in havuz]
    n = len(havuz)
    t1 = []
    for g in pencere:
        isl = _islenen(seans_olaylari[g])
        px, py = p95([o["x_s"] for o in isl]), p95([o["x_s"] - o["z_s"] for o in isl])
        t1.append({"seans": g, "n": len(isl), "p95_x": px, "p95_y": py, "r_s": _bol(px, py)})
    olculen = [s for s in t1 if s["r_s"] is not None]
    yazim = [(g, o) for g, o in havuz if o["planli_yazim"] > 0]
    en_kotu = max(yazim, key=lambda go: go[1]["x_s"]) if yazim else None
    t2 = {"n_yazim_olay": len(yazim), "n_yazim_satir": sum(o["planli_yazim"] for _, o in havuz),
          "z_medyan": statistics.median([o["z_s"] for _, o in yazim]) if yazim else None,
          "z_maks": max(o["z_s"] for _, o in yazim) if yazim else None,
          "en_kotu_olay": ({"seans": en_kotu[0], "x_s": en_kotu[1]["x_s"], "z_s": en_kotu[1]["z_s"],
                            "y_s": en_kotu[1]["x_s"] - en_kotu[1]["z_s"]} if en_kotu else None)}
    t3 = {}
    if n:
        t3 = {"p99_orani": _bol(sirali_kantil(X, 0.99), sirali_kantil(Y, 0.99)), "maks_orani": _bol(max(X), max(Y)),
              "y_q94": sirali_kantil(Y, 0.94), "y_q95": p95(Y), "y_q96": sirali_kantil(Y, 0.96),
              "r_q94": _bol(sirali_kantil(X, 0.94), sirali_kantil(Y, 0.94)),
              "r_q96": _bol(sirali_kantil(X, 0.96), sirali_kantil(Y, 0.96))}
    oranlar = [o["z_s"] / (o["x_s"] - o["z_s"]) for _, o in havuz if o["x_s"] - o["z_s"] > 0]
    t4 = {"p95_z_bolu_y": p95(oranlar) if oranlar else None}
    once, sonra, yazimsiz = [], [], []
    for g in pencere:
        for k in seans_kayitlari.get(g, []):                 # ofset yalnız AYNI süreç içinde kıyaslanır
            isl = _islenen(k["olaylar"])
            yazimsiz.extend(o["x_s"] - o["z_s"] for o in isl if o["planli_yazim"] == 0)
            for w in (o for o in isl if o["planli_yazim"] > 0):
                for o in isl:
                    if o["planli_yazim"] > 0:
                        continue
                    if w["ofset_s"] - T5_PENCERE_S <= o["ofset_s"] < w["ofset_s"]:
                        once.append(o["x_s"] - o["z_s"])
                    elif w["ofset_s"] < o["ofset_s"] <= w["ofset_s"] + T5_PENCERE_S:
                        sonra.append(o["x_s"] - o["z_s"])
    t5 = {"pencere_s": T5_PENCERE_S, "n_yazim_olay": len(yazim), "onceki": _ozet(once), "sonraki": _ozet(sonra),
          "yazimsiz_tum": _ozet(yazimsiz),
          "beyan": "kaba iz: piyasa hareketliliğiyle karışır, hüküm değil (kart beyanli_sinirlar 2)"}
    hatalar = [o for g in pencere for o in seans_olaylari[g] if o["outcome"] == "error"]
    t6 = {"n_processed": n, "f_giris": _bol(sum(1 for _, o in havuz if o["planli_giris"] > 0), n),
          "f_yazim": _bol(len(yazim), n), "n_error": len(hatalar),
          "n_error_z_pozitif": sum(1 for o in hatalar if o["z_s"] > 0)}
    return {"t1": {"seanslar": t1, "en_kotu": (max(olculen, key=lambda s: s["r_s"]) if olculen else None)},
            "t2": t2, "t3": t3, "t4": t4, "t5": t5, "t6": t6}


# =================================================================================================================
# HÜKÜM
# =================================================================================================================

def _neden(kod: str, metin: str) -> dict:
    return {"kod": kod, "metin": metin}


def hukum(defter_yolu, *, baslangic: str, esik_adi: str, tanik_yolu=None, bakis: int = 1, kusurlu_kabul=(),
          kart_yolu=None) -> dict:
    """KILL#1 canlı çapası hükmü (kart `olcum_plani` HÜKÜM EVRENİ · ÜÇLÜ HÜKÜM · SEANS TANIĞI · TANILAR)."""
    if esik_adi not in YENIDEN_BASLATMA_ESIKLERI:
        raise ValueError(f"yeniden başlatma eşiği {esik_adi!r} ∉ {YENIDEN_BASLATMA_ESIKLERI} (kart saat vermiyor; "
                         "Rol-1 seçer — varsayılan yok)")
    if bakis not in (1, 2):
        raise ValueError(f"bakış 1 ya da 2 (kart veri_penceresi: ÖLÇÜLEMEDİ → bir kez +pencere): {bakis!r}")
    _gun(baslangic)
    kabul = sorted({_gun(g) for g in kusurlu_kabul})
    esikler = kart_esikleri(kart_yolu)
    oku = defter_oku(defter_yolu)
    kayitlar = surec_seanslari(oku["satirlar"])
    tanik = tanik_oku(tanik_yolu) if tanik_yolu else None

    seans_kayitlari: dict = {}
    for k in kayitlar.values():
        seans_kayitlari.setdefault(k["seans"], []).append(k)
    bozuk_seanslar = {b["seans"] for b in oku["bozuk"] if b["seans"]}
    defter_gunleri = set(seans_kayitlari) | bozuk_seanslar
    son = max(defter_gunleri | {baslangic})
    evren = defter_gunleri | set(_seans_gunleri(baslangic, son))
    seanslar = {g: _seans_degerlendir(g, seans_kayitlari.get(g, []), g in bozuk_seanslar, tanik, esik_adi)
                for g in sorted(evren)}

    hedef = esikler["pencere_seans"] * bakis
    adaylar = [g for g in sorted(seanslar) if g >= baslangic]
    pencere = []
    for g in adaylar:
        if seanslar[g]["temiz"]:
            pencere.append(g)
            if len(pencere) == hedef:
                break
    dolu = len(pencere) == hedef
    sinir_gun = pencere[-1] if dolu else (adaylar[-1] if adaylar else None)
    araliktaki = [g for g in adaylar if sinir_gun is not None and g <= sinir_gun]
    dusenler = [g for g in araliktaki if g not in pencere and seanslar[g]["sinif"] != "seans_disi"]
    sonrasi = [g for g in adaylar if sinir_gun is not None and g > sinir_gun]
    for g, s in seanslar.items():
        s["konum"] = ("pencere_oncesi" if g < baslangic else "pencere" if g in pencere
                      else "pencere_sonrasi" if g in sonrasi else "pencere_disi")

    seans_olaylari = {g: [o for k in seans_kayitlari.get(g, []) for o in k["olaylar"]] for g in seanslar}
    seans_xy = []
    for g in pencere:
        isl = _islenen(seans_olaylari[g])
        seans_xy.append(([o["x_s"] for o in isl], [o["x_s"] - o["z_s"] for o in isl]))
    havuz_y = [y for _, ys in seans_xy for y in ys]
    n_yazim_satir = sum(o["planli_yazim"] for g in pencere for o in _islenen(seans_olaylari[g]))
    n_yazim_olay = sum(1 for g in pencere for o in _islenen(seans_olaylari[g]) if o["planli_yazim"] > 0)

    gecersiz, olculemedi = [], []
    if oku["sema_ihlali"]:
        gecersiz.append(_neden("defter_semasi", f"{len(oku['sema_ihlali'])} satır aletin sözleşmesine uymuyor "
                                                f"(ilk: {oku['sema_ihlali'][0]})"))
    zaman = [m for s in seanslar.values() for m in s["_gecersiz"]]
    if zaman:
        gecersiz.append(_neden("zaman_tutarsiz", "; ".join(zaman[:5])))
    y_kotu = sum(1 for y in havuz_y if not (y > 0))
    if y_kotu:
        gecersiz.append(_neden("z_x_disinda", f"{y_kotu} olayda Y = X − Z ≤ 0: Z planli dal gövdesinin DIŞINA taşmış "
                                              "(kart kill_list 'Tek kaynak')"))
    if any("takvim_yok" in seanslar[g]["nedenler"] for g in araliktaki):
        olculemedi.append(_neden("takvim_yok", "XNYS takvimi okunamadı — seans sınırları ölçülemedi"))
    if not dolu:
        olculemedi.append(_neden("pencere_dolmadi", f"temiz seans {len(pencere)}/{hedef} (kart: pencere uzar)"))
    bekleyen = [g for g in araliktaki if "kusurlu" in seanslar[g]["nedenler"] and g not in kabul]
    if bekleyen:
        olculemedi.append(_neden("kusurlu_kok_neden", f"kusurlu tanıklı seans(lar) {bekleyen}: kök neden karta "
                                                      "yazılmadan hüküm verilmez (kart kill_list)"))
    if n_yazim_satir < esikler["n_yazim_min"]:
        olculemedi.append(_neden("yazim_az", f"pencerede yazım {n_yazim_satir} < {esikler['n_yazim_min']} — kol "
                                             "fiilen çalışmadı (kart kill_list; EXE-2026-003 kill#2 aynı pencereyle)"))

    r = px = py = None
    lo = hi = None
    B = 0
    uclu = None
    uclu_nedeni = []
    if havuz_y and not y_kotu:
        r, px, py = r_noktasi(seans_xy)
    if r is not None:
        if len(seans_xy) >= olcum_araclari.KUME_MIN:
            lo, hi, B = r_bootstrap(seans_xy, B=esikler["bootstrap_B"], seviye=esikler["ci_seviye"],
                                    tohum=esikler["tohum"])
        uclu = uclu_hukum(r, hi, esikler["tavan_R"])
        if uclu == OLCULEMEDI:
            uclu_nedeni.append(_neden("ci_genis", f"R ≤ tavan ama CI üstü {hi} > {esikler['tavan_R']}")
                               if hi is not None else _neden("ci_yok", "aralık kurulamadı (küme sayısı < 2)"))
    elif not havuz_y:
        olculemedi.append(_neden("havuz_bos", "pencerede işlenen olay yok"))

    if gecersiz:
        karar, nedenler = GECERSIZ, gecersiz + olculemedi
    elif olculemedi:
        karar, nedenler = OLCULEMEDI, olculemedi
    else:
        karar, nedenler = uclu, uclu_nedeni
    for s in seanslar.values():
        s.pop("_gecersiz")
    return {
        "kart": KART_KIMLIGI, "betik": "research/olcumler/exe012_kill1_canli/hukum.py",
        "uretim_ts": dt.datetime.now(dt.timezone.utc).isoformat(),
        "kod": {"betik_sha256": _sha256(__file__), "meridian_yolu": str(pathlib.Path(barclock.__file__).resolve().parent)},
        "girdi": {"defter": {"yol": str(defter_yolu), "sha256": _sha256(defter_yolu), "satir_n": len(oku["satirlar"]),
                             "bozuk_satir": oku["bozuk"], "sema_ihlali_n": len(oku["sema_ihlali"]),
                             "sema_ihlali": oku["sema_ihlali"][:20]},
                  "tanik": ({"yol": str(tanik_yolu), "sha256": _sha256(tanik_yolu), "kaynak": tanik["kaynak"],
                             "yok_sayilan_seri": tanik["yok_sayilan_seri"]} if tanik else None),
                  "kart": {"yol": esikler["kart_yolu"], "sha256": esikler["kart_sha256"]}},
        "parametreler": {"baslangic": baslangic, "bakis": bakis, "pencere_temiz_seans": hedef,
                         "yeniden_baslatma_esigi": esik_adi, "kusurlu_kok_neden_kartta": kabul},
        "esikler": {k: esikler[k] for k in ("tavan_R", "ci_seviye", "bootstrap_B", "pencere_seans", "n_yazim_min",
                                            "tohum", "p95_tanimi")},
        "esik_duyarliligi": [g for g, s in seanslar.items()
                             if None not in s["yeniden_baslatma"].values()
                             and s["yeniden_baslatma"]["acilis"] != s["yeniden_baslatma"]["pencere"]],
        "seanslar": list(seanslar.values()),
        "pencere": {"seanslar": pencere, "n_temiz": len(pencere), "hedef": hedef, "dolu": dolu,
                    "dusenler": [{"seans": g, "sinif": seanslar[g]["sinif"], "nedenler": seanslar[g]["nedenler"]}
                                 for g in dusenler],
                    "sonrasi_n": len(sonrasi)},
        "hukum": {"karar": karar, "uclu": uclu, "nedenler": nedenler, "r_nokta": r,
                  "r_eksi_1": (r - 1.0 if r is not None else None), "p95_x": px, "p95_y": py,
                  "ci": {"lo": lo, "hi": hi, "B": B, "seviye": esikler["ci_seviye"], "tohum": esikler["tohum"],
                         "n_kume": len(seans_xy), "yontem": "SEANS-kümeli bootstrap (olcum_araclari.kume_bootstrap), "
                                                           "istatistik p95(X)/p95(Y), yüzdelik aralığı"},
                  "tavan": esikler["tavan_R"], "tavan_asildi": (r is not None and r > esikler["tavan_R"]),
                  "n_olay": len(havuz_y), "n_seans": len(seans_xy), "n_yazim_satir": n_yazim_satir,
                  "n_yazim_olay": n_yazim_olay,
                  "n_error": sum(1 for g in pencere for o in seans_olaylari[g] if o["outcome"] == "error")},
        "tanilar": _tanilar(pencere, seans_olaylari, seans_kayitlari),
    }


# =================================================================================================================
# ADIM-0 (kart `adim0` — hesap kısmı; betimlemedir, hüküm değildir)
# =================================================================================================================

def _kova_payi(sira: list, sayim: list, n: int, alt_sinir_mi: bool) -> float | None:
    """≥ 50 ms payı. `alt_sinir_mi`: kovanın ALT sınırı ≥ 0,05 (x > 50 ms) · değilse kovanın le'si ≥ 0,05."""
    if not n:
        return None
    toplam, onceki = 0, 0.0
    for le, c in zip(sira, sayim):
        ust = math.inf if le == "+Inf" else float(le)
        if (onceki if alt_sinir_mi else ust) >= 0.05:
            toplam += c
        onceki = ust
    return toplam / n


def adim0a(tanik_yolu, gunler=None) -> dict:
    """ADIM-0a: seans başına processed/skipped/error sayısı (sayaçların iki seans-dışı sınır anı farkı — tanıkla AYNI
    anlar), processed p95'in düştüğü KOVA (değer değil; `olcum_araclari.kantil_indeksi`), ≥ 50 ms payı (iki tanım)."""
    tanik = tanik_oku(tanik_yolu)
    if gunler is None:
        tarihler = {dt.datetime.fromtimestamp(ts, dt.timezone.utc).astimezone(barclock.NY).date().isoformat()
                    for n in tanik["seriler"].values() for ts in n}
        gunler = [g for g in sorted(tarihler) if barclock.seans_araligi(g)[0] == "ok"]
    out = []
    for g in gunler:
        sinir = seans_sinirlari(_gun(g))
        if sinir["durum"] != "ok":
            out.append({"seans": g, "durum": "taniksiz", "neden": f"seans aralığı yok ({sinir['durum']})"})
            continue
        t0, t1, neden = _sinir_anlari(tanik, sinir)
        if neden:
            out.append({"seans": g, "durum": "taniksiz", "neden": neden})
            continue
        satir = {"seans": g, "durum": "olculdu", "neden": None,
                 "t0": dt.datetime.fromtimestamp(t0, dt.timezone.utc).isoformat(),
                 "t1": dt.datetime.fromtimestamp(t1, dt.timezone.utc).isoformat()}
        for sonuc in ("processed", "skipped", "error"):
            n = tanik["seriler"].get((sonuc, "+Inf")) or {}
            satir[sonuc] = int(n[t1] - n[t0]) if (t0 in n and t1 in n) else None
        proc = {le: n for (o, le), n in tanik["seriler"].items() if o == "processed"}
        sira = _le_sirasi(proc)
        birikimli = [proc[le][t1] - proc[le][t0] for le in sira]
        sayim = [int(c) for c in [birikimli[0]] + [b - a for a, b in zip(birikimli, birikimli[1:])]]
        n = sum(sayim)
        satir["kova_sayilari"] = dict(zip(sira, sayim))
        satir["p95_kovasi_le"] = None
        if n:
            k, kum = olcum_araclari.kantil_indeksi(n, 0.95), 0
            for le, c in zip(sira, sayim):
                kum += c
                if kum > k:
                    satir["p95_kovasi_le"] = le
                    break
        satir["pay_50ms_ustu"] = {"tanim": "x > 0,05 s (alt sınırı ≥ 50 ms olan kovalar + taşma)",
                                  "deger": _kova_payi(sira, sayim, n, True)}
        satir["pay_le_50ms_ve_ustu"] = {"tanim": "le ≥ 0,05 kovaları + taşma (x > 0,025 s)",
                                        "deger": _kova_payi(sira, sayim, n, False)}
        out.append(satir)
    return {"kart": KART_KIMLIGI, "adim": "ADIM-0a", "girdi": {"tanik": str(tanik_yolu), "sha256": _sha256(tanik_yolu)},
            "seanslar": out, "not": "betimlemedir — eşik DEĞİL, hükmü değiştirmez (kart esikler)"}


def _jsonl(yol) -> tuple:
    satirlar, bozuk = [], 0
    with open(yol, encoding="utf-8", errors="replace") as f:
        for s in f:
            if not s.strip():
                continue
            try:
                satirlar.append(json.loads(s))
            except json.JSONDecodeError:   # sessiz-yutma DEĞİL: bozuk satır `bozuk_satir` sayacına girer ve çıktıda görünür
                bozuk += 1
    return satirlar, bozuk


def adim0b(planli_yolu, karar_yolu, adim0a_yolu, *, baslangic: str, bitis: str | None = None, kart_yolu=None) -> dict:
    """ADIM-0b: seans başına planli YAZIM (planli defter satırı; olay = ayrı `decision_as_of`) ve planli dala GİRİŞ
    olayları (karar defteri: fired=true ∧ plan_source=planned, `decision_as_of` ile olaya gruplanır); payda ADIM-0a'nın
    örtüşen seanslardaki processed sayısı → f_giris, f_yazim; 20 seansta beklenen yazım (seans günü ortalaması ×
    kart `pencere_seans`) vs `n_yazim_min`."""
    esikler = kart_esikleri(kart_yolu)
    _gun(baslangic)
    planli, planli_bozuk = _jsonl(planli_yolu)
    karar, karar_bozuk = _jsonl(karar_yolu)
    yazim_satir, yazim_olay, giris_olay = {}, {}, {}
    cozulemeyen = 0
    for r in planli:
        g = r.get("date")
        if not isinstance(g, str) or not _GUN_RE.match(g):
            cozulemeyen += 1
            continue
        yazim_satir[g] = yazim_satir.get(g, 0) + 1
        yazim_olay.setdefault(g, set()).add(r.get("decision_as_of"))
    for r in karar:
        if r.get("fired") is not True or r.get("plan_source") != "planned":
            continue
        an = barclock.parse_utc(r.get("decision_as_of"))
        if an is None:
            cozulemeyen += 1
            continue
        giris_olay.setdefault(barclock.session_date(an), set()).add(r.get("decision_as_of"))
    a0 = json.loads(pathlib.Path(adim0a_yolu).read_text(encoding="utf-8"))
    processed = {s["seans"]: s["processed"] for s in a0.get("seanslar", [])
                 if s.get("durum") == "olculdu" and s.get("processed") is not None}
    goruler = set(yazim_satir) | set(giris_olay)
    son = bitis or max(goruler | {baslangic})
    gunler = [g for g in _seans_gunleri(baslangic, son)]
    tablo = [{"seans": g, "yazim_satir": yazim_satir.get(g, 0), "yazim_olay": len(yazim_olay.get(g, ())),
              "giris_olay": len(giris_olay.get(g, ())), "processed": processed.get(g)} for g in gunler]
    ortusen = [s for s in tablo if s["processed"] is not None]
    payda = sum(s["processed"] for s in ortusen)
    f_giris = _bol(sum(s["giris_olay"] for s in ortusen), payda)
    f_yazim = _bol(sum(s["yazim_olay"] for s in ortusen), payda)
    beklenen = (sum(s["yazim_satir"] for s in tablo) / len(tablo) * esikler["pencere_seans"]) if tablo else None
    return {"kart": KART_KIMLIGI, "adim": "ADIM-0b",
            "girdi": {"planli": str(planli_yolu), "planli_sha256": _sha256(planli_yolu), "planli_bozuk": planli_bozuk,
                      "karar": str(karar_yolu), "karar_sha256": _sha256(karar_yolu), "karar_bozuk": karar_bozuk,
                      "adim0a": str(adim0a_yolu), "cozulemeyen_satir": cozulemeyen},
            "aralik": [baslangic, son], "seans_n": len(tablo), "ortusen_seans_n": len(ortusen), "seanslar": tablo,
            "f_giris": f_giris, "f_yazim": f_yazim, "beklenen_yazim_20_seans": beklenen,
            "n_yazim_min": esikler["n_yazim_min"],
            "f_yazim_duzeltme_esigi_asildi": (f_yazim is not None and f_yazim >= F_YAZIM_DUZELTME_ESIGI),
            "not": "betimlemedir — f_yazim ≥ %5 ise kart beyanli_sinirlar(1) sayıyla düzeltilir (Rol-1)"}


def adim0c(defter_yolu, seans: str, *, tanik_yolu=None) -> dict:
    """ADIM-0c: aletin İLK seansı — tanık eşit mi, defter satır boyutu, R_0 ve Z dağılımı (kayda geçer, hüküm değil)."""
    _gun(seans)
    oku = defter_oku(defter_yolu)
    kayitlar = [k for k in surec_seanslari(oku["satirlar"]).values() if k["seans"] == seans]
    olaylar = [o for k in kayitlar for o in k["olaylar"]]
    isl = _islenen(olaylar)
    tanik = tanik_oku(tanik_yolu) if tanik_yolu else None
    sinir = seans_sinirlari(seans)
    zs = [o["z_s"] for o in isl]
    r0 = None
    if isl:
        r0 = r_noktasi([([o["x_s"] for o in isl], [o["x_s"] - o["z_s"] for o in isl])])[0]
    return {"kart": KART_KIMLIGI, "adim": "ADIM-0c", "seans": seans,
            "girdi": {"defter": str(defter_yolu), "sha256": _sha256(defter_yolu)},
            "tanik": _tanik_seans(tanik, sinir, [o["x_s"] for o in isl],
                                  sum(1 for o in olaylar if o["outcome"] == "error")),
            "satir_kb": [kb for k in kayitlar for kb in k["satir_kb"]],
            "bozuk_satir": [b for b in oku["bozuk"] if b["seans"] == seans],
            "surec_n": len(kayitlar), "n_processed": len(isl), "r_0": r0,
            "z": {"n": len(zs), "n_pozitif": sum(1 for z in zs if z > 0),
                  "medyan": statistics.median(zs) if zs else None, "p95": p95(zs) if zs else None,
                  "maks": max(zs) if zs else None},
            "f_giris": _bol(sum(1 for o in isl if o["planli_giris"] > 0), len(isl)),
            "f_yazim": _bol(sum(1 for o in isl if o["planli_yazim"] > 0), len(isl)),
            "n_yazim_satir": sum(o["planli_yazim"] for o in isl),
            "not": "ADIM-0c seansı pencereye GİRMEZ (kart adim0 + kill_list) — betimlemedir, hüküm değil"}


def tanik_plani(gunler) -> list:
    """Seans başına tanık dışa aktarım planı: sınır anları (ET'den, DST-doğru, erken kapanış takvimden) ve query_range
    sorgusu. Rol-1 A1'de çeker, yanıtları satır satır tek dosyaya yazar."""
    out = []
    for g in gunler:
        s = seans_sinirlari(_gun(g))
        if s["durum"] != "ok":
            out.append({"seans": g, "durum": s["durum"], "hata": s["hata"]})
            continue
        bas = (s["pencere"] - dt.timedelta(minutes=45)).isoformat()
        son = (s["kapanis"] + dt.timedelta(minutes=30)).isoformat()
        out.append({"seans": g, "durum": "ok", "once_bitis": s["pencere"].isoformat(),
                    "sonra_baslangic": s["kapanis"].isoformat(),
                    "sorgu": {"query": METRIK, "start": bas, "end": son, "step": "30s"},
                    "komut": (f"curl -s {PROMETHEUS_ADRESI}/api/v1/query_range --data-urlencode 'query={METRIK}' "
                              f"--data-urlencode 'start={bas}' --data-urlencode 'end={son}' "
                              f"--data-urlencode 'step=30s' >> tanik.jsonl; echo >> tanik.jsonl")})
    return out


# =================================================================================================================
# komut satırı
# =================================================================================================================

def _ozet_satiri(sonuc: dict) -> str:
    h = sonuc.get("hukum")
    if not h:
        return f"{sonuc.get('adim', 'EXE-2026-012')} tamam"
    return (f"EXE-2026-012 hüküm: {h['karar']} (üçlü {h['uclu']}) · R={h['r_nokta']} · CI üst={h['ci']['hi']} · "
            f"temiz seans {sonuc['pencere']['n_temiz']}/{sonuc['pencere']['hedef']} · "
            f"nedenler {[n['kod'] for n in h['nedenler']]}")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="hukum.py", description="EXE-2026-012 KILL#1 canlı çapası hüküm betiği")
    alt = p.add_subparsers(dest="komut", required=True)
    h = alt.add_parser("hukum")
    h.add_argument("--defter", required=True)
    h.add_argument("--baslangic", required=True)
    h.add_argument("--yeniden-baslatma-esigi", required=True, choices=YENIDEN_BASLATMA_ESIKLERI)
    h.add_argument("--tanik")
    h.add_argument("--bakis", type=int, default=1, choices=(1, 2))
    h.add_argument("--kusurlu-kok-neden-kartta", nargs="*", default=[])
    h.add_argument("--kart")
    h.add_argument("--cikti")
    a = alt.add_parser("adim0a")
    a.add_argument("--tanik", required=True)
    a.add_argument("--gun", nargs="*")
    a.add_argument("--cikti")
    b = alt.add_parser("adim0b")
    b.add_argument("--planli-defter", required=True)
    b.add_argument("--karar-defteri", required=True)
    b.add_argument("--adim0a", required=True)
    b.add_argument("--baslangic", required=True)
    b.add_argument("--bitis")
    b.add_argument("--kart")
    b.add_argument("--cikti")
    c = alt.add_parser("adim0c")
    c.add_argument("--defter", required=True)
    c.add_argument("--seans", required=True)
    c.add_argument("--tanik")
    c.add_argument("--cikti")
    t = alt.add_parser("tanik-plani")
    t.add_argument("--gun", nargs="+", required=True)
    arg = p.parse_args(argv)
    try:
        if arg.komut == "hukum":
            sonuc = hukum(arg.defter, baslangic=arg.baslangic, esik_adi=arg.yeniden_baslatma_esigi,
                          tanik_yolu=arg.tanik, bakis=arg.bakis, kusurlu_kabul=arg.kusurlu_kok_neden_kartta,
                          kart_yolu=arg.kart)
        elif arg.komut == "adim0a":
            sonuc = adim0a(arg.tanik, arg.gun or None)
        elif arg.komut == "adim0b":
            sonuc = adim0b(arg.planli_defter, arg.karar_defteri, arg.adim0a, baslangic=arg.baslangic,
                           bitis=arg.bitis, kart_yolu=arg.kart)
        elif arg.komut == "adim0c":
            sonuc = adim0c(arg.defter, arg.seans, tanik_yolu=arg.tanik)
        else:
            sonuc = {"kart": KART_KIMLIGI, "adim": "tanik-plani", "plan": tanik_plani(arg.gun)}
    except (OSError, ValueError, KeyError) as e:
        print(f"HATA ({type(e).__name__}): {e}", file=sys.stderr)
        return 2
    metin = json.dumps(sonuc, ensure_ascii=False, indent=1)
    cikti = getattr(arg, "cikti", None)
    if cikti:
        pathlib.Path(cikti).write_text(metin + "\n", encoding="utf-8")
        print(_ozet_satiri(sonuc))
    else:
        print(metin)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
