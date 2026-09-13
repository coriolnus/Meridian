"""rapor.py — EDG-2026-085 Senaryo-A (icra-anı IEX quote kaydı) ÇEVRİMDIŞI RAPOR ARACI.

NE YAPAR: pilot penceresinde motorun yazdığı quote kaydından (kayıt dizini, motor dışı; yazan
meridian/quotecapture.py) kartın DÖRT EKSENİNİ hesaplar ve iki dosya üretir:
  * kayıp oranı  — pencerede hiç quote yakalanamayan dolum payı, nedeni SINIFLI (kill#3)
  * tutarlılık   — dolum fiyatı [bid − 1 tick, ask + 1 tick] bandında kalan dolum payı
  * disk         — kayıt + ham defterinin seans başına baytı
  * CPU / worker — taban örnekleminin (taban.jsonl) pilot örneklemine göre deltası
artı üç pozitif kontrolden ikisi (PK-1 sentetik, PK-3 bar çaprazı); PK-2 (ham çerçeve eşleme) ELLE
yapılır ve bu araç onu "elle — Rol-1" diye ADIYLA raporlar, sessizce geçmiş saymaz.

SALT-OKURDUR: hiçbir şeye yazmaz, yalnız --cikti-dizin altına iki dosya üretir. Canlı state/,
E2 defteri ve meridian.db yalnız OKUNUR (sqlite `?mode=ro`).

UYDURMA YASAĞI: ölçülemeyen her alan None'dır ve yanında bir `..._neden` taşır. Örneklem kapısı
(kart: 30 dolum ∧ 10 seans) dolmadan `hukum` None'dır; betimleyici sayılar yine yazılır.
KILL#7: üç PK'dan biri KALDIysa hiçbir K sayısı yayılmaz (None + neden) ve çıkış kodu 2 olur.

ÇIKIŞ KODU SÖZLEŞMESİ
    0 — rapor yazıldı (PK düşmedi)
    1 — hata (kayıt dizini yok / okunamadı / argüman hatası)
    2 — pozitif kontrol KALDI: sayı yayılmadı (kill#7)

KULLANIM
    python -m research.olcumler.edg085_icra_ani_quote.rapor \\
        --kayit-dizin /opt/veri/olcum/edg085/kayit --state-dizin /opt/meridian/state \\
        --baslangic 2026-09-21 --bitis 2026-10-17 \\
        [--taban /opt/veri/olcum/edg085/taban.jsonl] [--pilot-taban P.jsonl] \\
        [--cikti-dizin C] [--pk-sentetik] [--tick 0.01]

KOMUT SATIRI sözleşmedir (ops yasası): gövde `kos(argv)`tur, `main()` değil — testler argv ile
çağırır, kabuk `python -m ...` ile.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import sqlite3
import statistics
import sys

# --- KART EŞİKLERİ (research/cards/EDG-2026-085-icra-ani-quote-kaydi-senaryo-a.yaml, AYNEN) -------
# Eşik ölçüm sonrası DEĞİŞMEZ (yeni eşik = yeni kart). Burada KOPYA değil, kartın sayısının
# makine-okunur karşılığıdır ve rapora AYNEN basılır ki okuyan hangi eşiğe karşı okuduğunu bilsin.
ESIKLER = {
    "kayip_orani_ust": 0.30,
    "tutarlilik_bant_ici_oran_alt": 0.95,
    "disk_gun_basi_mb_ust": 50,
    "cpu_payi_delta_ust_pp": 5,
    "healthz_p95_delta_ms_ust": 50,
    "n_uygun_alt": 30,
    "seans_alt": 10,
}
#: Kartın kill#5'i — hüküm metnine AYNEN girer (IEX temsiliyeti yeniden ölçülmeden yayılamaz).
KILL5 = ("IEX temsiliyeti (EDG-052 mirası) yeniden ölçülmeden 'quote güvenilir' yayılırsa "
         "→ geçersiz")
PAY_S = 30              # kart penceresi ±30 sn (motor tarafıyla aynı sayı; quotecapture PAY_S)
ACILIS_BASLANGIC = "13:30"
ACILIS_BITIS = "14:00"
MOTOR_COID_ONEKI = "P-"


# =================================================================================================
# Küçük yardımcılar — hepsi saf, hepsi ölçülemeyeni None yapar
# =================================================================================================
def _jsonl(yol: str) -> list[dict]:
    """Bir JSONL dosyasını okur; yoksa boş liste. Bozuk satır SESSİZCE atılmaz — sayılır."""
    if not os.path.exists(yol):
        return []
    out, bozuk = [], 0
    with open(yol, encoding="utf-8") as f:
        for s in f:
            s = s.strip()
            if not s:
                continue
            try:
                out.append(json.loads(s))
            except json.JSONDecodeError:  # sessiz-yutma: bozuk satır ATILMAZ, aşağıda SAYILIR ve rapora `bozuk_satir_n` olarak girer
                bozuk += 1
    if bozuk:
        out.append({"tur": "_bozuk", "n": bozuk, "yol": yol})
    return out


def _ts(s) -> dt.datetime | None:
    """RFC3339 → UTC datetime; çözülemeyen damga UYDURULMAZ (None)."""
    if not s:
        return None
    t = str(s).strip()
    if t.endswith("Z"):
        t = t[:-1] + "+00:00"
    tam, nokta, kalan = t.partition(".")
    if nokta:
        kesir = ""
        i = 0
        while i < len(kalan) and kalan[i].isdigit():
            kesir += kalan[i]
            i += 1
        t = f"{tam}.{kesir[:6]}{kalan[i:]}"
    try:
        d = dt.datetime.fromisoformat(t)
    except ValueError:  # sessiz-yutma: damga ayrıştırılamadı — None dönmek uydurmamaktır, çağıran satırı `..._neden` ile işaretler
        return None
    return d if d.tzinfo else d.replace(tzinfo=dt.timezone.utc)


def _f(x) -> float | None:
    """Sayıya çevrilemeyen değer None (uydurma yasağı)."""
    try:
        return float(x)
    except (TypeError, ValueError):  # sessiz-yutma: sayı olmayan alan — 0.0 yazmak ölçülmemişi ölçülmüş göstermek olurdu
        return None


def _yuzdelik(xs: list[float], q: float) -> float | None:
    """Kesme (nearest-rank) yüzdelik. n<1 → None. İki örnekten p95 üretmek bir HÜKÜM değildir;
    çağıran örneklem sayısını da rapora yazar."""
    ys = sorted(v for v in xs if v is not None)
    if not ys:
        return None
    k = max(1, min(len(ys), int(-(-q * len(ys) // 1))))
    return ys[k - 1]


def _medyan(xs: list[float]) -> float | None:
    ys = [v for v in xs if v is not None]
    return statistics.median(ys) if ys else None


def _gunler(baslangic: str, bitis: str) -> list[str]:
    """[baslangic, bitis] arasındaki takvim günleri (UTC, kapsayıcı)."""
    b, s = _ts(f"{baslangic}T00:00:00Z"), _ts(f"{bitis}T00:00:00Z")
    if b is None or s is None or s < b:
        return []
    out, g = [], b
    while g <= s:
        out.append(g.strftime("%Y-%m-%d"))
        g += dt.timedelta(days=1)
    return out


def _sha256(yol: str) -> str | None:
    """Girdi dosyasının içerik özeti — rapor hangi baytları okuduğunu KANITLAR (kart donuk girdi
    disiplininin dosya karşılığı)."""
    if not os.path.exists(yol):
        return None
    h = hashlib.sha256()
    with open(yol, "rb") as f:
        for blok in iter(lambda: f.read(65536), b""):
            h.update(blok)
    return h.hexdigest()


# =================================================================================================
# Kayıt okuma ve dolum çözümü
# =================================================================================================
def kayit_oku(kayit_dizin: str, gunler: list[str]) -> dict:
    """Kayıt + ham defterlerini okur. Döner: {satirlar, gun_satir, disk_bayt, girdi_sha256,
    seans_gunleri, bozuk_satir_n}."""
    satirlar: list[dict] = []
    gun_satir: dict[str, list[dict]] = {}
    disk = 0
    sha: dict[str, str] = {}
    seanslar: list[str] = []
    bozuk = 0
    for g in gunler:
        # DOSYA ADI ÖNEKİ `edg085_`: motorun yazdığı adla TEK KAYNAK (meridian/quotecapture.py::_yaz).
        # Önek motor tarafında `codelaw` desen anahtarını daraltmak için konuldu; okuyucu onu
        # AYNEN tekrar etmek zorunda — ayrışırsa rapor sessizce BOŞ seans görür.
        kayit_yolu = os.path.join(kayit_dizin, f"edg085_{g}.jsonl")
        ham_yolu = os.path.join(kayit_dizin, f"edg085_ham_{g}.jsonl")
        rows = [r for r in _jsonl(kayit_yolu) if r.get("tur") != "_bozuk"]
        bozuk += sum(r.get("n", 0) for r in _jsonl(kayit_yolu) if r.get("tur") == "_bozuk")
        if os.path.exists(kayit_yolu):
            seanslar.append(g)
            disk += os.path.getsize(kayit_yolu)
            sha[f"edg085_{g}.jsonl"] = _sha256(kayit_yolu)
        if os.path.exists(ham_yolu):
            disk += os.path.getsize(ham_yolu)
            sha[f"edg085_ham_{g}.jsonl"] = _sha256(ham_yolu)
        gun_satir[g] = rows
        satirlar += rows
    return {"satirlar": satirlar, "gun_satir": gun_satir, "disk_bayt": disk,
            "girdi_sha256": sha, "seans_gunleri": seanslar, "bozuk_satir_n": bozuk}


def dolum_satirlari(satirlar: list[dict], tick: float) -> list[dict]:
    """Kayıt satırlarından DOLUM BAŞINA bir ölçüm satırı üretir.

    PENCERE BURADA YENİDEN KURULUR (motorun `quote_n_pencere` alanına GÜVENİLMEZ): pencere açılış
    işaretinden (`tur:"pencere" olay:"ac"`) gönderim anı, dolum satırından dolum anı okunur ve
    [gönderim − PAY_S, dolum + PAY_S] dışındaki quote satırları `pencere_disi_n`e sayılır. Bu bir
    kopya değil BAĞIMSIZ İKİNCİ ÖLÇÜMDÜR: PK-1 tam olarak bu sınırı sınar; motorun alanını
    tekrarlasaydık pozitif kontrol kendi kendini onaylardı."""
    acilis: dict[str, dict] = {}
    quote: dict[str, list[dict]] = {}
    for r in satirlar:
        if r.get("tur") == "pencere" and r.get("olay") == "ac":
            acilis[str(r.get("coid"))] = r
        elif r.get("tur") == "quote":
            quote.setdefault(str(r.get("coid")), []).append(r)
    out = []
    for r in satirlar:
        if r.get("tur") != "dolum":
            continue
        coid = str(r.get("coid"))
        dolum_at = _ts(r.get("dolum_ts")) or _ts(r.get("alindi"))
        ac = acilis.get(coid)
        gonderim_at = _ts((ac or {}).get("alindi"))
        alt = (gonderim_at or dolum_at) - dt.timedelta(seconds=PAY_S) if dolum_at else None
        ust = dolum_at + dt.timedelta(seconds=PAY_S) if dolum_at else None
        icinde, disinda = [], 0
        for q in quote.get(coid, []):
            qat = _ts(q.get("alindi"))
            if qat is None or alt is None or ust is None:
                disinda += 1
            elif alt <= qat <= ust:
                icinde.append(q)
            else:
                disinda += 1
        son = r.get("son_quote") or {}
        bid, ask = _f(son.get("bid")), _f(son.get("ask"))
        fiyat = _f(r.get("dolum_fiyat"))
        bant_ici, bant_neden = None, None
        if bid is None or ask is None or fiyat is None:
            bant_neden = "bid/ask/dolum_fiyat eksik — bant hükmü kurulamaz"
        else:
            bant_ici = (bid - tick) <= fiyat <= (ask + tick)
        yakinlik = None
        if fiyat is not None and bid is not None and ask is not None:
            # YÖN-FARKINDALI YAKINLIK: long alışta referans ASK (agresif taraf), short satışta BID.
            ref = ask if str(r.get("yon", "")).lower() == "buy" else bid
            yakinlik = ((fiyat - ref) / ref * 10000.0) if ref else None
        out.append({
            "coid": coid, "sembol": r.get("sembol"), "yon": r.get("yon"),
            "gonderim_ts": (ac or {}).get("alindi"), "dolum_ts": r.get("dolum_ts"),
            "dolum_fiyat": fiyat, "bid": bid, "ask": ask,
            "quote_n": len(icinde), "pencere_disi_n": disinda,
            "bant_ici": bant_ici, "bant_ici_neden": bant_neden,
            "yakinlik_bps": yakinlik,
            "kayip_nedeni": r.get("kayip_nedeni"),
            "motor_quote_n": r.get("quote_n_pencere"),
            "alindi": r.get("alindi"),
        })
    return out


def _saat_kovasi(ts) -> str:
    """Tanı kırılımı: açılış (13:30–14:00Z) AYRI — EDG-052'nin açılış-dakikası bulgusunun canlı
    karşılığı burada görünür olmalı."""
    t = _ts(ts)
    if t is None:
        return "bilinmiyor"
    hhmm = t.strftime("%H:%M")
    return "acilis" if ACILIS_BASLANGIC <= hhmm < ACILIS_BITIS else "diger"


# =================================================================================================
# Defter çaprazları (E2 + trades) — eşlenemeyen dolum ADIYLA sayılır (kill#3)
# =================================================================================================
def e2_plan_idleri(state_dizin: str) -> set[str]:
    """E2 defterindeki plan kimlikleri (entry_execution.jsonl). Dosya yoksa boş küme."""
    return {str(r.get("plan_id")) for r in _jsonl(os.path.join(state_dizin, "entry_execution.jsonl"))
            if r.get("plan_id")}


def trades_fiyatlari(state_dizin: str) -> dict:
    """meridian.db `trades` tablosundan plan_id → {entry, alpaca_fill_price, dolum_ts}. SALT-OKUR
    (`?mode=ro`). DB yoksa boş sözlük + neden (uydurma yasağı)."""
    yol = os.path.join(state_dizin, "meridian.db")
    if not os.path.exists(yol):
        return {}
    out: dict[str, dict] = {}
    con = sqlite3.connect(f"file:{yol}?mode=ro", uri=True)
    try:
        for pid, entry, extra in con.execute(
                "SELECT plan_id, entry, extra_json FROM trades WHERE plan_id IS NOT NULL"):
            ek = {}
            if extra:
                try:
                    ek = json.loads(extra) or {}
                except json.JSONDecodeError:  # sessiz-yutma: extra_json bozuk — satırın KENDİSİ yine sayılır, yalnız ek alanlar boş kalır ve bu rapora düşer
                    ek = {"_extra_bozuk": True}
            out[str(pid)] = {"entry": _f(entry),
                             "alpaca_fill_price": _f(ek.get("alpaca_fill_price")),
                             "dolum_ts": ek.get("dolum_ts")}
    finally:
        con.close()
    return out


# =================================================================================================
# Pozitif kontroller
# =================================================================================================
#: PK-1 SENTETİK DESEN — bilinen sabit quote deseni, aynı çözümleyiciden geçer. Beklenen: kayıp 0,
#: bant-içi 1.0, pencere DIŞI 0 satır. Desen burada durur ki çözümleyici mutasyona uğradığında
#: (pencere sınırı, bant payı) kontrol KALSIN ve hiçbir sayı yayılmasın. Sentetik dolum
#: fiyatı ASK + 1 TICK'tir: bant payını kaldıran mutasyon PK-1'i de düşürür.
def _pk1_satirlar() -> list[dict]:
    def q(coid, sem, t, bid, ask):
        return {"tur": "quote", "alindi": t, "ts": t, "sembol": sem, "coid": coid,
                "faz": "pencere", "bid": bid, "ask": ask}
    return [
        {"tur": "pencere", "alindi": "2026-01-02T14:00:00Z", "sembol": "PKA", "coid": "P-PK1",
         "olay": "ac", "neden": "new"},
        q("P-PK1", "PKA", "2026-01-02T14:00:10Z", 10.00, 10.02),
        q("P-PK1", "PKA", "2026-01-02T14:00:20Z", 10.01, 10.03),
        # PENCERE DIŞI (gönderimden 10 dk önce): çözümleyici bunu SAYMAMALI
        q("P-PK1", "PKA", "2026-01-02T13:50:00Z", 9.00, 9.02),
        {"tur": "dolum", "alindi": "2026-01-02T14:00:25Z", "sembol": "PKA", "coid": "P-PK1",
         "yon": "buy", "dolum_ts": "2026-01-02T14:00:25Z", "dolum_fiyat": 10.04,
         "quote_n_pencere": 2, "son_quote": {"ts": "2026-01-02T14:00:20Z", "bid": 10.01,
                                             "ask": 10.03}, "kayip_nedeni": None},
    ]


def pk1_sentetik(tick: float) -> dict:
    """PK-1: sentetik desen → kayıp 0 · bant-içi 1.0 · pencere dışı 0. Üçü de tutmazsa KALDI."""
    d = dolum_satirlari(_pk1_satirlar(), tick)
    kayip = [r for r in d if r["quote_n"] == 0]
    bant = [r for r in d if r["bant_ici"] is True]
    disi = sum(r["pencere_disi_n"] for r in d)
    gecti = (len(d) == 1 and not kayip and len(bant) == 1 and disi == 1)
    # `disi == 1`: sentetik desen BİLEREK bir pencere-dışı quote taşır; çözümleyici onu saymalı
    # AMA pencere içine ALMAMALI. 0 olsaydı sınır yok sayılmış, 2 olsaydı içerideki quote da
    # dışarı atılmış olurdu — iki yönlü çivi.
    return {"hukum": "gecti" if gecti else "kaldi",
            "olculen": {"dolum_n": len(d), "kayip_n": len(kayip), "bant_ici_n": len(bant),
                        "pencere_disi_n": disi},
            "beklenen": {"dolum_n": 1, "kayip_n": 0, "bant_ici_n": 1, "pencere_disi_n": 1}}


def pk3_bar_caprazi(dolumlar: list[dict], satirlar: list[dict], state_dizin: str,
                    gunler: list[str]) -> dict:
    """PK-3: pencere içi min(ask)/max(bid) AYNI DAKİKANIN kapalı barının [low, high] bandında mı?
    Bar bulunamazsa hüküm KURULMAZ (None + neden) — ölçülemeyen ihlal sayılmaz."""
    barlar: dict[tuple, dict] = {}
    for g in gunler:
        for r in _jsonl(os.path.join(state_dizin, "intraday_bars", f"{g}.jsonl")):
            for sem, b in (r.get("bars") or {}).items():
                t = _ts(b.get("t"))
                if t is not None:
                    barlar[(sem, t.strftime("%Y-%m-%dT%H:%M"))] = b
    quote: dict[str, list[dict]] = {}
    for r in satirlar:
        if r.get("tur") == "quote":
            quote.setdefault(str(r.get("coid")), []).append(r)
    sinanan, dusen = 0, []
    for d in dolumlar:
        qs = [q for q in quote.get(d["coid"], []) if _f(q.get("bid")) is not None]
        t = _ts(d["dolum_ts"])
        if not qs or t is None:
            continue
        b = barlar.get((d["sembol"], t.strftime("%Y-%m-%dT%H:%M")))
        if not b:
            continue
        lo, hi = _f(b.get("l")), _f(b.get("h"))
        if lo is None or hi is None:
            continue
        min_ask = min(_f(q.get("ask")) for q in qs if _f(q.get("ask")) is not None)
        max_bid = max(_f(q.get("bid")) for q in qs)
        sinanan += 1
        if not (lo <= min_ask <= hi and lo <= max_bid <= hi):
            dusen.append({"coid": d["coid"], "sembol": d["sembol"], "min_ask": min_ask,
                          "max_bid": max_bid, "bar_low": lo, "bar_high": hi})
    if sinanan == 0:
        return {"hukum": None, "neden": "eşleşen dakika barı bulunamadı — çapraz kurulamadı",
                "sinanan_n": 0, "dusen": []}
    return {"hukum": "gecti" if not dusen else "kaldi", "neden": None,
            "sinanan_n": sinanan, "dusen": dusen}


# =================================================================================================
# Fizibilite: taban ↔ pilot deltası
# =================================================================================================
def taban_ozeti(yol: str | None) -> dict:
    """taban.jsonl özeti. GEÇERSİZ CPU SATIRLARI ELENİR ve SAYILIR: `cpu_kaynak != "cgroup"` olan
    satırlar 2026-09-13 öncesi MainPID (uv sarmalayıcı) ölçümüdür ve kartın ADIM-0 (3) kaydında
    GEÇERSİZ ilan edilmiştir — elemeyi kaydetmeden yapmak, bilinen bir hatayı sessizce sayıya
    çevirmek olurdu."""
    if not yol:
        return {"cpu_medyan": None, "cpu_neden": "taban dosyası verilmedi",
                "cpu_n_gecerli": 0, "cpu_n_elenen": 0, "healthz_p95_ms": None, "n": 0}
    rows = [r for r in _jsonl(yol) if r.get("tur") != "_bozuk"]
    gecerli = [r for r in rows if r.get("cpu_kaynak") == "cgroup"
               and _f(r.get("cpu_pct_tek_cekirdek")) is not None]
    elenen = len(rows) - len(gecerli)
    cpu = _medyan([_f(r.get("cpu_pct_tek_cekirdek")) for r in gecerli])
    hz = _yuzdelik([_f(r.get("healthz_p50_ms")) for r in rows
                    if _f(r.get("healthz_p50_ms")) is not None], 0.95)
    return {"cpu_medyan": cpu,
            "cpu_neden": None if cpu is not None else "geçerli (cgroup) CPU örneği yok",
            "cpu_n_gecerli": len(gecerli), "cpu_n_elenen": elenen,
            "healthz_p95_ms": hz, "n": len(rows)}


# =================================================================================================
# Ölçüm gövdesi
# =================================================================================================
def olc(kayit: dict, state_dizin: str, gunler: list[str], tick: float,
        taban: str | None, pilot_taban: str | None, pk_sentetik: bool) -> dict:
    """Dört ekseni + PK'ları hesaplar ve `sonuc` sözlüğünü döndürür (dosyaya yazmaz)."""
    satirlar = kayit["satirlar"]
    dolumlar = dolum_satirlari(satirlar, tick)
    n = len(dolumlar)
    kayipli = [d for d in dolumlar if d["quote_n"] == 0]
    nedenler: dict[str, int] = {}
    for d in kayipli:
        ad = d["kayip_nedeni"] or "neden_yazilmamis"
        nedenler[ad] = nedenler.get(ad, 0) + 1
    bant_paydasi = [d for d in dolumlar if d["bant_ici"] is not None]
    bant_ici = [d for d in bant_paydasi if d["bant_ici"]]
    e2 = e2_plan_idleri(state_dizin)
    eslenemeyen = sorted({d["coid"] for d in dolumlar
                          if str(d["coid"]).startswith(MOTOR_COID_ONEKI) and d["coid"] not in e2})
    bracket = sorted({d["coid"] for d in dolumlar
                      if not str(d["coid"]).startswith(MOTOR_COID_ONEKI)})
    trades = trades_fiyatlari(state_dizin)
    fiyat_ayrisma = []
    for d in dolumlar:
        t = trades.get(d["coid"])
        if t and d["dolum_fiyat"] is not None:
            ref = t.get("alpaca_fill_price") if t.get("alpaca_fill_price") is not None else t.get("entry")
            if ref is not None and abs(ref - d["dolum_fiyat"]) > tick:
                fiyat_ayrisma.append({"coid": d["coid"], "kayit": d["dolum_fiyat"], "defter": ref})
    n_seans = len(kayit["seans_gunleri"])
    tb, pb = taban_ozeti(taban), taban_ozeti(pilot_taban)
    cpu_delta = (pb["cpu_medyan"] - tb["cpu_medyan"]) \
        if (pb["cpu_medyan"] is not None and tb["cpu_medyan"] is not None) else None
    hz_delta = (pb["healthz_p95_ms"] - tb["healthz_p95_ms"]) \
        if (pb["healthz_p95_ms"] is not None and tb["healthz_p95_ms"] is not None) else None
    pk = {"sentetik": pk1_sentetik(tick) if pk_sentetik else
          {"hukum": None, "neden": "--pk-sentetik verilmedi"},
          "bar_capraz": pk3_bar_caprazi(dolumlar, satirlar, state_dizin, gunler),
          "gercek": {"hukum": None, "neden": "elle — Rol-1 (ham çerçeve eşlemesi, kart PK-2)"}}
    pk_dusen = [ad for ad, v in pk.items() if v.get("hukum") == "kaldi"]

    kayip_orani = (len(kayipli) / n) if n else None
    bant_orani = (len(bant_ici) / len(bant_paydasi)) if bant_paydasi else None
    disk_mb_gun = (kayit["disk_bayt"] / 1_048_576 / n_seans) if n_seans else None
    yayin_neden = None
    if pk_dusen:
        # KILL#7: PK düştüyse HİÇBİR sayı yayılmaz. Betimleyici sayımlar (n, seans) kalır —
        # onlar bir hüküm değil, ölçümün kendi hacmidir; K ölçüleri ve fizibilite deltaları düşer.
        yayin_neden = f"kill#7 — pozitif kontrol KALDI: {', '.join(pk_dusen)}; sayı yayılmadı"
        kayip_orani = bant_orani = disk_mb_gun = cpu_delta = hz_delta = None

    hukum, hukum_neden = None, None
    if pk_dusen:
        hukum_neden = yayin_neden
    elif n < ESIKLER["n_uygun_alt"] or n_seans < ESIKLER["seans_alt"]:
        hukum_neden = (f"örneklem kapısı açık: n_dolum={n} (alt {ESIKLER['n_uygun_alt']}) ∧ "
                       f"n_seans={n_seans} (alt {ESIKLER['seans_alt']}) — hüküm YOK, "
                       f"betimleyici sayılar yine yazıldı")
    else:
        hukum = {
            "kayip": "gecti" if kayip_orani <= ESIKLER["kayip_orani_ust"] else "kaldi",
            "tutarlilik": ("gecti" if (bant_orani is not None
                                       and bant_orani >= ESIKLER["tutarlilik_bant_ici_oran_alt"])
                           else "kaldi"),
            "fizibilite": _fizibilite_hukmu(disk_mb_gun, cpu_delta, hz_delta),
            "kill5": KILL5,
        }
    return {
        "pencere": {"baslangic": gunler[0] if gunler else None,
                    "bitis": gunler[-1] if gunler else None},
        "n_dolum": n, "n_seans": n_seans,
        "kayip_orani": kayip_orani, "kayip_nedenleri": nedenler,
        "bant_ici_oran": bant_orani, "bant_ici_n": len(bant_ici),
        "bant_paydasi_n": len(bant_paydasi),
        "tani_yon_farkindali_bps": _tani_bps(dolumlar),
        "tani_sembol_saat": _tani_sembol_saat(dolumlar),
        "disk_mb_gun": disk_mb_gun, "disk_bayt": kayit["disk_bayt"],
        "cpu_delta_pp": cpu_delta,
        "cpu_taban_n_gecerli": tb["cpu_n_gecerli"], "cpu_taban_n_elenen": tb["cpu_n_elenen"],
        "cpu_pilot_n_gecerli": pb["cpu_n_gecerli"], "cpu_pilot_n_elenen": pb["cpu_n_elenen"],
        "cpu_delta_neden": None if cpu_delta is not None else (
            yayin_neden or tb["cpu_neden"] or pb["cpu_neden"] or "CPU deltası ölçülemedi"),
        "healthz_p95_delta_ms": hz_delta,
        "eslenemeyen": eslenemeyen, "bracket_bacagi": bracket,
        "fiyat_ayrisma": fiyat_ayrisma, "bozuk_satir_n": kayit["bozuk_satir_n"],
        "pk": pk, "esikler": dict(ESIKLER), "yayin_neden": yayin_neden,
        "hukum": hukum, "hukum_neden": hukum_neden,
        "uretim_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "girdi_sha256": kayit["girdi_sha256"],
        "dolumlar": dolumlar,
    }


def _fizibilite_hukmu(disk, cpu, hz) -> str:
    """Üç fizibilite ekseninden HERHANGİ biri tavanı aşarsa KALDI; ölçülemeyen eksen hüküm
    kurdurmaz (None → 'olculemedi')."""
    olculen = [x for x in (disk, cpu, hz) if x is not None]
    if not olculen:
        return "olculemedi"
    if disk is not None and disk > ESIKLER["disk_gun_basi_mb_ust"]:
        return "kaldi"
    if cpu is not None and cpu > ESIKLER["cpu_payi_delta_ust_pp"]:
        return "kaldi"
    if hz is not None and hz > ESIKLER["healthz_p95_delta_ms_ust"]:
        return "kaldi"
    return "gecti"


def _tani_bps(dolumlar: list[dict]) -> dict:
    xs = [d["yakinlik_bps"] for d in dolumlar if d["yakinlik_bps"] is not None]
    return {"medyan": _medyan(xs), "p90": _yuzdelik(xs, 0.90), "n": len(xs),
            "neden": None if xs else "yön-farkındalı yakınlık için bid/ask/fiyat üçlüsü yok"}


def _tani_sembol_saat(dolumlar: list[dict]) -> dict:
    out: dict[str, dict] = {}
    for d in dolumlar:
        kova = _saat_kovasi(d["dolum_ts"] or d["alindi"])
        anahtar = f"{d['sembol']}|{kova}"
        rec = out.setdefault(anahtar, {"n": 0, "bant_ici_n": 0, "kayip_n": 0})
        rec["n"] += 1
        rec["bant_ici_n"] += 1 if d["bant_ici"] else 0
        rec["kayip_n"] += 1 if d["quote_n"] == 0 else 0
    return out


# =================================================================================================
# Çıktı
# =================================================================================================
def markdown(s: dict) -> str:
    """İnsan okunur rapor. HÜKÜM METNİ kartın kill#5'ini AYNEN taşır — 'quote güvenilir' cümlesi
    IEX temsiliyeti yeniden ölçülmeden yayılamaz."""
    sat = [f"# EDG-2026-085 Senaryo-A — icra-anı quote kaydı raporu",
           f"", f"Pencere: {s['pencere']['baslangic']} → {s['pencere']['bitis']} · "
                f"üretim {s['uretim_utc']}", ""]
    if s["yayin_neden"]:
        sat += [f"> **SAYI YAYILMADI** — {s['yayin_neden']}", ""]
    sat += ["| Eksen | Ölçülen | Eşik |", "|---|---|---|",
            f"| kayıp oranı | {s['kayip_orani']} | ≤ {s['esikler']['kayip_orani_ust']} |",
            f"| bant-içi oran | {s['bant_ici_oran']} | ≥ {s['esikler']['tutarlilik_bant_ici_oran_alt']} |",
            f"| disk (MB/seans) | {s['disk_mb_gun']} | ≤ {s['esikler']['disk_gun_basi_mb_ust']} |",
            f"| CPU delta (pp) | {s['cpu_delta_pp']} | ≤ {s['esikler']['cpu_payi_delta_ust_pp']} |",
            f"| healthz p95 delta (ms) | {s['healthz_p95_delta_ms']} | ≤ {s['esikler']['healthz_p95_delta_ms_ust']} |",
            "",
            f"n_dolum={s['n_dolum']} · n_seans={s['n_seans']} · "
            f"kayıp nedenleri: {s['kayip_nedenleri']}",
            f"eşlenemeyen dolum (E2'de plan_id yok): {s['eslenemeyen'] or 'yok'}",
            f"bracket bacağı (motor öneksiz coid, E2'de aranmaz): {s['bracket_bacagi'] or 'yok'}",
            f"fiyat ayrışması (kayıt ↔ defter): {s['fiyat_ayrisma'] or 'yok'}",
            f"CPU taban örneği: geçerli {s['cpu_taban_n_gecerli']} · elenen {s['cpu_taban_n_elenen']} "
            f"(cpu_kaynak≠cgroup → kart ADIM-0 (3) GEÇERSİZ ilanı)",
            "",
            f"PK-1 sentetik: {s['pk']['sentetik'].get('hukum')} · "
            f"PK-3 bar çaprazı: {s['pk']['bar_capraz'].get('hukum')} · "
            f"PK-2 gerçek: {s['pk']['gercek'].get('neden')}",
            "",
            f"HÜKÜM: {s['hukum'] or 'YOK'}" + (f" — {s['hukum_neden']}" if s["hukum_neden"] else ""),
            "",
            f"KILL#5 (karttan aynen): {KILL5}", ""]
    return "\n".join(sat)


def kos(argv: list[str]) -> int:
    """KOMUT SATIRI gövdesi. Döner: çıkış kodu (0 yazıldı · 1 hata · 2 PK kaldı)."""
    ap = argparse.ArgumentParser(prog="edg085-rapor", add_help=True)
    ap.add_argument("--kayit-dizin", required=True)
    ap.add_argument("--state-dizin", required=True)
    ap.add_argument("--baslangic", required=True)
    ap.add_argument("--bitis", required=True)
    ap.add_argument("--taban", default=None)
    ap.add_argument("--pilot-taban", default=None)
    ap.add_argument("--cikti-dizin", default=".")
    ap.add_argument("--pk-sentetik", action="store_true")
    ap.add_argument("--tick", type=float, default=0.01)
    a = ap.parse_args(argv)
    if not os.path.isdir(a.kayit_dizin):
        sys.stderr.write(f"kayıt dizini yok: {a.kayit_dizin}\n")
        return 1
    gunler = _gunler(a.baslangic, a.bitis)
    if not gunler:
        sys.stderr.write("pencere boş ya da bitiş başlangıçtan önce\n")
        return 1
    kayit = kayit_oku(a.kayit_dizin, gunler)
    sonuc = olc(kayit, a.state_dizin, gunler, a.tick, a.taban, a.pilot_taban, a.pk_sentetik)
    os.makedirs(a.cikti_dizin, exist_ok=True)
    with open(os.path.join(a.cikti_dizin, f"sonuc_{a.bitis}.json"), "w", encoding="utf-8") as f:
        json.dump(sonuc, f, ensure_ascii=False, indent=2)
    with open(os.path.join(a.cikti_dizin, f"rapor_{a.bitis}.md"), "w", encoding="utf-8") as f:
        f.write(markdown(sonuc))
    return 2 if sonuc["yayin_neden"] else 0


if __name__ == "__main__":
    sys.exit(kos(sys.argv[1:]))
