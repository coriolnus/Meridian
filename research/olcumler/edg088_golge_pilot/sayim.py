"""research/olcumler/edg088_golge_pilot/sayim.py — EDG-2026-088 GÖLGE İCRA SAYACI.

NE ÖLÇER. Kart `research/cards/EDG-2026-088-uyuyan-kurulum-golge-pilot.yaml`nin K=2 birincil
ölçüsünü (`EDG-088-toplam-R-CI`, `EDG-088-kazanma-orani`) ve üç pozitif kontrolünü,
`state/golge_icra.jsonl` gölge defterinden:
  1. K1 — toplam R + blok-bootstrap CI95 (kartın `esikler.ci_yontem`i: `olcum_araclari`nın
     moving-block bootstrap'ı; IID REDDEDİLİR).
  2. K2 — kazanma oranı (+ PF tanı).
  3. TANI — kurulum kırılımı, hüküm (kapı) dağılımı, çıkış nedeni dağılımı, kol kırılımı,
     bar kaynağı dağılımı. K'ye ÇARPILMAZ (kart: "kurulum başına kırılım TANIdır").
  4. PK (2) — kontrol kolu: gölge R ile GERÇEK işlem R'sinin (`trades.jsonl`) farkı.
  5. PK (3) — selef EDG-2026-049'un 6 uyuyan `pullback` planı: referans işaret (6/6 kayıp,
     toplam −4,725R) ve gölge tarafının onunla EŞLEŞİP eşleşmediği.

BETİK SAYAR, HÜKÜM VERMEZ (CLAUDE.md §5: "ölçüm kartına hüküm Rol-1'in"). Eşikler karttan OKUNUR
ve rapora yalnız SAYI olarak yazılır; hiçbir çıktıda "geçti/kaldı/GEÇER/KALIR" yoktur. Pencere
dolmadan (n ≥ `n_alt_plan` ∧ geçen gün ≤ `pencere_gun_ust`) markdown başlığı "HÜKÜM YOK
(betimleyici ara-rapor)"dur ve EŞİK KARŞILAŞTIRMASI BÖLÜMÜ HİÇ ÜRETİLMEZ — 049'un ikinci düşme
sebebi n<30 ile yazılmış eşik cümlesiydi.

KILL#5 — PK DÜŞERSE SAYI YAYILMAZ. Kartın kill-list'i "kontrol PK'sı (gölge≈gerçek) tutmazsa →
hiçbir sayı yayılmaz" der. `kontrol.gecti` ÖLÇÜLÜP `False` çıktığında K blokunun TAMAMI (n,
toplam_r, ci, kazanma_orani, pf, kırılımlar) hem JSON'da hem markdown'da BASTIRILIR: alanlar
`None` olur, `bastirilan` listesi adlarını taşır ve markdown "PK DÜŞTÜ — SAYI YAYILMAZ" başlığıyla
çıkar. `gecti is None` (ölçülemedi) BASTIRMAZ — "ölçülmedi" ile "ölçüldü ve tutmadı" aynı şey
değildir; ölçülemeyen PK hükmü yine engeller ama sayıyı gizlemek körlük üretirdi.

EŞİKLER İKİ KAYNAKTAN OKUNUR, HİÇBİRİ KOPYALANMAZ. Kart YAML'ı `esikler` bloğunu, `meridian.golge_icra`
aynı sayıları motor sabiti olarak taşır (motorun kendi çivisi ikisini zaten karşılaştırır). Bu betik
İKİSİNİ DE okur ve AYRIŞMAYI ölçer (`esik_ayrismasi`): ayrışma varsa yayın ENGELLENİR. Tek-kaynak
yasasının bu betikteki karşılığı budur — sayıyı üçüncü kez yazmak yerine iki kaynağı kıyaslamak.

K PAYDASININ TANIMI BİR KOPYADIR VE ÇİVİYLE BAĞLIDIR. Payda kuralı (`R` ölçülmüş ∧ `kaynak_bar_hash`
dolu) motorun `golge_icra.ozet` fonksiyonunda da yaşıyor; motora yeni bir yüzey eklemek bu turun
dosya kapsamı DIŞINDAYDI, o yüzden kural burada ikinci kez yazıldı. Kaçınılmaz kopyanın bedeli
ayrışmadır ve AYRIŞMA ÇİVİSİYLE kapatıldı: `tests/test_edg088_sayim_v461.py` aynı defteri hem
motorun `ozet()`ine hem bu betiğe verir ve n · toplam_r · kazanma_orani · pf · dağılımların BİREBİR
aynı olmasını ister (CLAUDE.md §4 tek-kaynak: "kopya kaçınılmazsa türetme + ayrışma çivisi").

CI ORTALAMANIN ARALIĞIDIR, TOPLAM TÜRETİLİR. `olcum_araclari.blok_bootstrap_ci` ORTALAMA R'nin
aralığını verir (fonksiyonun kendi beyanı). Kart "toplam R'nin CI95 alt sınırı > 0" der; toplam
= n × ortalama ve n > 0 sabit olduğu için İŞARET SINAMASI İKİSİNDE DE AYNIDIR. Çıktı ikisini de
taşır: `ci` (ortalama, ham fonksiyon çıktısı) ve `ci_toplam` (n ile ölçeklenmiş TÜRETME, alanı
`turetme` ile adlandırılmış). Türetme bir ölçüm değildir ve öyle sunulmaz.

SALT OKUNUR. Betik `state/`e ve `meridian.obs`a YAZMAZ, ağa ÇIKMAZ. Defteri `store` üzerinden
DEĞİL verilen dosya yolundan okur — yani `config.STATE`e hiç dokunmaz. `meridian.golge_icra`dan
yalnız DONUK SABİTLER ve alan adları alınır; motorun `adim`/`ozet`/`kayit_al` fonksiyonları
ÇAĞRILMAZ (hepsi `config.STATE`e bağlıdır). İthal zinciri ölçüldü (çivi:
`test_ithal_meridian_obs_u_TETIKLEMEZ_ve_state_ACMAZ`): `golge_icra` → `barclock` · `broker` ·
`store` · `strategy`; `meridian.obs` bu zincirde YOKTUR ve ithal hiçbir dosya açmaz.

`.md`ye ÇAPA YAZILMAZ ve `research/` altındaki bir betiğe nokta'lı sembol çapası da yazılmaz
(codelaw sembol taraması yalnız `meridian`/`tests`/`ops` köklerini çözer; buradaki bir çapa
sessizce çürürdü).

KOMUT SATIRI (ops sözleşmesi KOMUT SATIRIdır, `main()` değil):

    .venv/bin/python research/olcumler/edg088_golge_pilot/sayim.py \\
        --defter state/golge_icra.jsonl \\
        --cikti research/olcumler/edg088_golge_pilot/sonuc_<tarih>.json \\
        [--markdown research/olcumler/edg088_golge_pilot/sonuc_<tarih>.md] \\
        [--baslangic 2026-09-09T00:00Z] [--kart research/cards/EDG-2026-088-….yaml] \\
        [--gercek state/trades.jsonl] [--goal state/goal.yaml] \\
        [--pk3 research/olcumler/edg049_dormant_2026-08-23/islemler_tam_dormant_acik.json]
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import pathlib
import sys

import yaml

SANDBOX = pathlib.Path(__file__).resolve().parent
KOK = SANDBOX.parents[2]
# BETİK DOĞRUDAN KOŞULUR (`python research/.../sayim.py`), yani `sys.path[0]` bu dizindir ve depo
# kökü yolda DEĞİLDİR. Operatörün koşacağı BİÇİMDE çalışması için kök yola eklenir — "18 çivi
# yeşilken aracın kendisi koşmuyordu" vakasının sınıfı.
if str(KOK) not in sys.path:
    sys.path.insert(0, str(KOK))

from meridian import golge_icra as gi                                           # noqa: E402
from meridian.olcum_araclari import (BOOTSTRAP_N, BOOTSTRAP_TOHUM,  # noqa: E402
                                     blok_bootstrap_ci)

VARSAYILAN_KART = KOK / "research" / "cards" / "EDG-2026-088-uyuyan-kurulum-golge-pilot.yaml"
VARSAYILAN_GOAL = KOK / "state" / "goal.yaml"

#: KARTIN EŞİK ADI → MOTORUN SABİT ADI. Sayılar HİÇBİRİNDE yeniden yazılmaz; bu tablo yalnız iki
#: kaynağı EŞLER ki ayrışma ölçülebilsin. Kartta olup motorda olmayan (ya da tersi) bir eşik
#: eklenirse eşleşme tablosu eksik kalır ve `esik_ayrismasi` bunu ADIYLA söyler.
ESIK_ESLESMESI = {
    "n_alt_plan": "N_ALT",
    "ci_alt_R_ust": "CI_ALT_R",
    "kazanma_alt": "KAZANMA_ALT",
    "pencere_gun_ust": "PENCERE_GUN",
    "golge_gercek_fark_R_ust": "FARK_R_UST",
}

#: PK (3) SELEFİNİN SÜZGECİ. EDG-2026-049'un `islemler_tam_dormant_acik.json` artefaktında uyuyan
#: dilim `setup == "pullback"` satırlarıdır ve TAM ALTI tanedir (049 kartının n=6'sı). Sayı
#: BEKLENTİ olarak yazılıdır: altı çıkmazsa artefakt değişmiş demektir ve PK ölçülemez sayılır —
#: "6 bulduk" diye rapor etmek, aslında başka bir dilimi ölçmek olurdu.
PK3_SETUP = "pullback"
PK3_BEKLENEN_N = 6


# ==================================================================================================
# GİRDİ OKUMA — hepsi DOSYA YOLUNDAN; `store` / `config.STATE` KULLANILMAZ
# ==================================================================================================
def _jsonl_oku(yol: pathlib.Path) -> tuple[list[dict], int]:
    """JSONL defteri → (satırlar, bozuk_satir_sayisi). Dosya yoksa `FileNotFoundError`.

    Bozuk satır SESSİZCE atılmaz: sayısı raporun `girdi` bloğuna girer. Sessiz atma, defterin
    yarısını kaybetmiş bir ölçümü "temiz" gösterirdi.
    """
    yol = pathlib.Path(yol)
    if not yol.exists():
        raise FileNotFoundError(f"defter bulunamadı: {yol}")
    satirlar, bozuk = [], 0
    for ham in yol.read_text(encoding="utf-8").splitlines():
        ham = ham.strip()
        if not ham:
            continue
        try:
            obj = json.loads(ham)
        except json.JSONDecodeError:  # sessiz-yutma: bozuk JSONL satırı SAYILIR (girdi.n_bozuk_satir) ve rapora girer — sessizce atılan satır defterin yarısını kaybettirip ölçümü "temiz" gösterirdi
            bozuk += 1
            continue
        if isinstance(obj, dict):
            satirlar.append(obj)
        else:
            bozuk += 1
    return satirlar, bozuk


def _json_oku(yol: pathlib.Path):
    yol = pathlib.Path(yol)
    if not yol.exists():
        raise FileNotFoundError(f"dosya bulunamadı: {yol}")
    return json.loads(yol.read_text(encoding="utf-8"))


def _damga(x) -> dt.datetime | None:
    """ISO damgayı UTC'ye normalize eder. `Z` de `+00:00` da olur; ayrıştırılamazsa `None`.

    Dizge KIYASLANMAZ: "2026-09-09T00:00Z" ile "2026-09-09T00:00:00+00:00" AYNI andır ve dizge
    kıyası ikincisini pencerenin dışında sanırdı.
    """
    if not isinstance(x, str) or not x.strip():
        return None
    s = x.strip().replace("Z", "+00:00")
    try:
        t = dt.datetime.fromisoformat(s)
    except ValueError:  # sessiz-yutma: ayrıştırılamayan damga ADIYLA sayılır (n_bozuk_ts) — None dönmek ile 1970'e düşmek arasındaki fark, satırın pencerede mi dışında mı olduğudur
        return None
    return t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)


def _pencereye_al(satirlar: list[dict], baslangic: str | None):
    """`--baslangic`tan ÖNCEKİ satırları eler. Dönüş: (kalan, disarida, bozuk_ts).

    `--baslangic` verilmezse süzgeç HİÇ koşmaz ve satırların TAMAMI ölçüme girer; ayrıştırılamayan
    damgalı satırlar o durumda DIŞARIDA BIRAKILMAZ (paydayı hak etmeden küçültürdü) — yalnız
    sayılır.
    """
    if baslangic is None:
        bozuk = sum(1 for r in satirlar if _damga(r.get("ts")) is None)
        return list(satirlar), 0, bozuk
    t0 = _damga(baslangic)
    if t0 is None:
        raise SystemExit(f"HATA: --baslangic ayrıştırılamadı: {baslangic!r} "
                         "(ISO damga bekleniyor; sessizce boş rapor üretilmez)")
    kalan, disarida, bozuk = [], 0, 0
    for r in satirlar:
        t = _damga(r.get("ts"))
        if t is None:
            bozuk += 1
            continue
        if t < t0:
            disarida += 1
        else:
            kalan.append(r)
    return kalan, disarida, bozuk


# ==================================================================================================
# K PAYDASI — motorun `golge_icra.ozet` kuralının İKİNCİ YAZIMI (ayrışma çivisiyle bağlı)
# ==================================================================================================
def sayilir(satir: dict) -> bool:
    """Satır K paydasına girer mi? `R` ÖLÇÜLMÜŞ ∧ PIT çapası (`kaynak_bar_hash`) TAM.

    Tetiği hiç gelmeyen plan (`R=None`) ve çapası yarım kalan satır (`kaynak_bar_hash=None`)
    TANIdır, paydada DEĞİLDİR: eksik K, eşiği hak etmeden geçme yönünde yanlıdır.
    """
    return satir.get("R") is not None and bool(satir.get("kaynak_bar_hash"))


def _sirala(satirlar: list[dict]) -> list[dict]:
    """ZAMAN SIRASI — blok bootstrap'ın TEK bilgi kaynağı budur.

    Anahtar `cikis_ts` (işlemin kapandığı seans), eşitlikte yazım anı `ts`. Karıştırılmış bir
    seride blok yapısı anlamsızdır ve `blok_bootstrap_ci` bunu ANLAYAMAZ (kendi beyanı) — sıralama
    bu yüzden burada, çağırmadan ÖNCE yapılır.
    """
    return sorted(satirlar, key=lambda r: (str(r.get("cikis_ts") or ""), str(r.get("ts") or "")))


def _dagilim(satirlar: list[dict], alan: str) -> dict:
    """`alan` değerine göre sayım — ölçülemeyen değer `?` kovasına düşer, sessizce KAYBOLMAZ."""
    out: dict[str, int] = {}
    for r in satirlar:
        k = str(r.get(alan) if r.get(alan) is not None else "?")
        out[k] = out.get(k, 0) + 1
    return dict(sorted(out.items()))


# ==================================================================================================
# PK (2) — KONTROL KOLU (gölge ≈ gerçek)
# ==================================================================================================
def _friksiyon_payi(goal: dict, giris: float, stop: float) -> float | None:
    """Bir çiftin komisyon+kayma payı, R BİRİMİNDE. Ölçülemezse `None`.

    Pay = (gidiş-dönüş kayma + gidiş-dönüş komisyon) / (giriş − stop). `slippage_bps` goal'de TEK
    YÖN olarak yazılıdır (dosyanın kendi şerhi), o yüzden iki kez sayılır: giriş ve çıkış. Komisyon
    hisse başınadır ve o da iki bacak.
    """
    try:
        bps = float(goal.get("slippage_bps"))
        kom = float(goal.get("commission_per_share"))
        rps = float(giris) - float(stop)
    except (TypeError, ValueError):  # sessiz-yutma: goal alanı ya da fiyat ölçülemiyorsa pay UYDURULMAZ — None döner ve çift `olculemeyen`e adıyla girer
        return None
    if not (rps > 0) or not math.isfinite(rps):
        return None
    return (2.0 * (bps / 10000.0) * float(giris) + 2.0 * kom) / rps


def kontrol_olc(golge: list[dict], gercek_yolu, goal: dict, fark_ust: float) -> dict:
    """PK (2): `kol == "kontrol"` gölge satırlarını GERÇEK işlemlerle `plan_id` üzerinden eşler.

    `gecti` ÜÇ DEĞERLİDİR: `True` (ölçüldü, tuttu) · `False` (ölçüldü, tutmadı → kill#5, sayı
    yayılmaz) · `None` (ÖLÇÜLEMEDİ: defter yok ya da hiç çift yok). `None`u `False` saymak,
    ölçülmemiş bir PK'yı düşmüş göstererek hükmü hak etmeden engellerdi; `True` saymak ise hiç
    kontrol edilmemiş bir motoru doğrulanmış gösterirdi.
    """
    bos = {"n_cift": 0, "n_golge_kontrol": 0, "n_gercek": None, "ort_fark_r": None,
           "ort_mutlak_fark_r": None, "komisyon_kayma_payi": None, "gecti": None,
           "esik": fark_ust, "ciftler": [], "neden": None, "n_payi_olculemeyen": 0}
    kontrol = [r for r in golge if r.get("kol") == "kontrol" and sayilir(r)]
    bos["n_golge_kontrol"] = len(kontrol)
    if gercek_yolu is None:
        bos["neden"] = ("gerçek işlem defteri (`trades.jsonl`) VERİLMEDİ ve defterin yanında da "
                        "yok — PK (2) ÖLÇÜLEMEDİ")
        return bos
    gercek_satirlar, _ = _jsonl_oku(pathlib.Path(gercek_yolu))
    bos["n_gercek"] = len(gercek_satirlar)
    gercek = {}
    for t in gercek_satirlar:
        pid = t.get("plan_id")
        if pid is not None and t.get("r_multiple") is not None:
            gercek[str(pid)] = t
    if not kontrol:
        bos["neden"] = ("gölge defterinde `kol=\"kontrol\"` satırı YOK — kontrol kolu henüz "
                        "beslenmedi, PK (2) ÖLÇÜLEMEDİ")
        return bos

    ciftler, farklar, paylar, pay_yok = [], [], [], 0
    for r in kontrol:
        pid = str(r.get("plan_id"))
        t = gercek.get(pid)
        if t is None:
            continue
        try:
            fark = float(r["R"]) - float(t["r_multiple"])
        except (TypeError, ValueError):  # sessiz-yutma: R'si sayıya çevrilemeyen çift ATLANIR ve sayısı `ciftler` uzunluğu ile paydadan düşer — uydurulmuş bir fark, PK'yı hak etmeden geçirirdi
            continue
        pay = _friksiyon_payi(goal, r.get("giris_fiyat"), r.get("stop"))
        if pay is None:
            pay_yok += 1
        else:
            paylar.append(pay)
        farklar.append(fark)
        ciftler.append({"plan_id": pid, "ticker": r.get("ticker"), "golge_r": r.get("R"),
                        "gercek_r": t.get("r_multiple"), "fark_r": round(fark, 6),
                        "friksiyon_payi_r": (None if pay is None else round(pay, 6))})

    bos["ciftler"] = ciftler
    bos["n_cift"] = len(ciftler)
    bos["n_payi_olculemeyen"] = pay_yok
    if not ciftler:
        bos["neden"] = ("gölge kontrol satırlarının hiçbiri `plan_id` ile bir GERÇEK işleme "
                        "eşleşmedi — PK (2) ÖLÇÜLEMEDİ")
        return bos

    ort_fark = sum(farklar) / len(farklar)
    ort_mutlak = sum(abs(x) for x in farklar) / len(farklar)
    pay_ort = (sum(paylar) / len(paylar)) if paylar else None
    bos["ort_fark_r"] = round(ort_fark, 6)
    bos["ort_mutlak_fark_r"] = round(ort_mutlak, 6)
    bos["komisyon_kayma_payi"] = (None if pay_ort is None else round(pay_ort, 6))
    if pay_ort is None:
        bos["gecti"] = None
        bos["neden"] = ("komisyon+kayma payı hiçbir çiftte ölçülemedi (goal alanları ya da "
                        "giriş/stop eksik) — kartın 'pay içinde' şartı SINANAMADI")
        return bos
    # KART İKİ ŞART BİRDEN İSTER: ortalama |fark| ≤ 0,05R **∧** komisyon+kayma payının İÇİNDE.
    bos["gecti"] = bool(ort_mutlak <= float(fark_ust) and ort_mutlak <= pay_ort)
    return bos


# ==================================================================================================
# PK (3) — SELEF EDG-2026-049
# ==================================================================================================
def pk3_olc(pk3_yolu, golge: list[dict]) -> dict:
    """EDG-049'un 6 uyuyan `pullback` planı: referans işaret + gölge tarafıyla EŞLEŞME.

    REFERANS her zaman ölçülür (artefakt dosyadadır). GÖLGE TARAFI ancak gölge defterinde o 6
    `plan_id` varsa ölçülebilir; yoksa `esles` `None`dır ve neden ADIYLA yazılır — kartın
    "çıkmazsa harness kör sayılır" cümlesinin karşılığı budur. `esles=False` (ayrışma) ile
    `esles=None` (yeniden doğum hiç koşulmadı) AYRI hükümlerdir ve karıştırılmaz.
    """
    bos = {"kaynak": (None if pk3_yolu is None else str(pk3_yolu)), "setup": PK3_SETUP,
           "n": None, "kayip": None, "toplam_r": None, "plan_idler": [],
           "golge": {"n": None, "kayip": None, "toplam_r": None, "eksik_plan_idler": []},
           "esles": None, "fark_r": None, "neden": None}
    if pk3_yolu is None:
        bos["neden"] = "`--pk3` verilmedi — PK (3) ÖLÇÜLMEDİ"
        return bos
    ham = _json_oku(pathlib.Path(pk3_yolu))
    if not isinstance(ham, list):
        bos["neden"] = f"PK (3) artefaktı liste değil ({type(ham).__name__}) — ÖLÇÜLEMEDİ"
        return bos
    dilim = [r for r in ham if isinstance(r, dict) and r.get("setup") == PK3_SETUP]
    bos["n"] = len(dilim)
    if len(dilim) != PK3_BEKLENEN_N:
        bos["neden"] = (f"selef dilimi {len(dilim)} satır verdi, beklenen {PK3_BEKLENEN_N} — "
                        "artefakt değişmiş, PK (3) ÖLÇÜLEMEDİ (başka bir dilimi ölçmek 049 ile "
                        "kıyas OLMAZDI)")
        return bos
    rler = [float(r["r_multiple"]) for r in dilim if r.get("r_multiple") is not None]
    bos["kayip"] = sum(1 for x in rler if x < 0)
    bos["toplam_r"] = round(sum(rler), 6)
    bos["plan_idler"] = sorted(str(r.get("plan_id")) for r in dilim)

    hedef = set(bos["plan_idler"])
    golge_dilim = [r for r in golge if str(r.get("plan_id")) in hedef and sayilir(r)]
    eksik = sorted(hedef - {str(r.get("plan_id")) for r in golge_dilim})
    bos["golge"]["eksik_plan_idler"] = eksik
    if not golge_dilim:
        bos["neden"] = ("gölge defterinde 049'un 6 plan kimliğinden HİÇBİRİ yok — planlar "
                        "`strategy.scan_all` ile yeniden DOĞURULMADI (Rol-1 hükmü 3, seçenek c); "
                        "PK (3) ÖLÇÜLEMEDİ — HARNESS KÖR")
        return bos
    g_rler = [float(r["R"]) for r in golge_dilim]
    bos["golge"]["n"] = len(g_rler)
    bos["golge"]["kayip"] = sum(1 for x in g_rler if x < 0)
    bos["golge"]["toplam_r"] = round(sum(g_rler), 6)
    bos["fark_r"] = round(bos["golge"]["toplam_r"] - bos["toplam_r"], 6)
    if eksik:
        bos["neden"] = (f"6 planın {len(eksik)} tanesi gölge defterinde YOK ({', '.join(eksik)}) — "
                        "eşleşme EKSİK dilim üzerinden ölçülemez, PK (3) KISMİ")
        return bos
    # EŞLEŞME ÖLÇÜTÜ İŞARETTİR, EŞİTLİK DEĞİL. İki şasi (049 replay'i ve gölge motoru) aynı sayıyı
    # vermek zorunda değildir; kart "aynı işaret (6/6 kayıp) çıkmalı" der. Sayısal fark `fark_r`
    # ile ADIYLA durur ki Rol-1 büyüklüğünü de görsün.
    bos["esles"] = bool(bos["golge"]["kayip"] == bos["kayip"] == PK3_BEKLENEN_N
                        and bos["golge"]["toplam_r"] < 0 and bos["toplam_r"] < 0)
    return bos


# ==================================================================================================
# SAYIM
# ==================================================================================================
def calistir(*, defter, cikti=None, markdown=None, kart=None, baslangic=None,
             gercek=None, goal=None, pk3=None) -> dict:
    """Sayımı koşar ve sonuç sözlüğünü döner. `cikti`/`markdown` yalnız `ana`nın yazdığı yollardır;
    burada dosya YAZILMAZ (çağıran çivi saf sonucu okuyabilsin diye)."""
    defter = pathlib.Path(defter)
    kart_yolu = pathlib.Path(kart or VARSAYILAN_KART)
    goal_yolu = pathlib.Path(goal or VARSAYILAN_GOAL)
    kart_verisi = yaml.safe_load(kart_yolu.read_text(encoding="utf-8")) or {}
    esikler = dict(kart_verisi.get("esikler") or {})
    goal_verisi = yaml.safe_load(goal_yolu.read_text(encoding="utf-8")) or {}

    ham, bozuk = _jsonl_oku(defter)
    satirlar, disarida, bozuk_ts = _pencereye_al(ham, baslangic)

    if gercek is None:
        yan = defter.parent / "trades.jsonl"
        gercek = yan if yan.exists() else None

    # ---- eşik ayrışması (kart ↔ motor sabitleri) ------------------------------------------------
    modul_sabitleri, ayrisma = {}, []
    for kart_ad, modul_ad in ESIK_ESLESMESI.items():
        m = getattr(gi, modul_ad, None)
        modul_sabitleri[modul_ad] = m
        k = esikler.get(kart_ad)
        if k is None:
            ayrisma.append(f"{kart_ad}: kartta YOK (motor {modul_ad}={m})")
        elif m is None:
            ayrisma.append(f"{modul_ad}: motorda YOK (kart {kart_ad}={k})")
        elif float(k) != float(m):
            ayrisma.append(f"{kart_ad}={k} ≠ golge_icra.{modul_ad}={m}")
    ci_yontem_karti = str(esikler.get("ci_yontem") or "")
    if "blok_bootstrap_ci" not in ci_yontem_karti:
        ayrisma.append("kartın `esikler.ci_yontem` alanı `blok_bootstrap_ci` adını TAŞIMIYOR "
                       f"({ci_yontem_karti!r}) — kullanılan yöntem kartın donuk yöntemi DEĞİL")

    n_alt = int(modul_sabitleri["N_ALT"])
    pencere_gun = int(modul_sabitleri["PENCERE_GUN"])
    fark_ust = float(modul_sabitleri["FARK_R_UST"])

    # ---- K bloğu --------------------------------------------------------------------------------
    sayilanlar = _sirala([r for r in satirlar if sayilir(r)])
    olculemeyen_satirlar = [r for r in satirlar if not sayilir(r)]
    rler = [float(r["R"]) for r in sayilanlar]
    n = len(rler)
    kazanan = [x for x in rler if x > 0]
    kaybeden = [x for x in rler if x < 0]
    ci = blok_bootstrap_ci(rler)
    # IID REDDEDİLİR (kartın donuk yöntemi moving block'tur). `blok=1` yalnız n çok küçükken doğar;
    # aralığı sistematik olarak DARALTIR ve hükmü tek yönde kaydırır.
    ci_kabul = (None if ci.get("lo") is None else (ci.get("iid") is False))
    ci_toplam = {"lo": None, "hi": None, "ort": None,
                 "turetme": ("toplam = n × ortalama (n sabit) — `ci` ORTALAMANIN aralığıdır, bu "
                             "blok ondan TÜRETİLMİŞTİR, ayrıca ÖLÇÜLMEMİŞTİR; işaret sınaması "
                             "(alt sınır > 0) iki blokta AYNIDIR")}
    if ci.get("lo") is not None and n:
        ci_toplam.update(lo=round(ci["lo"] * n, 6), hi=round(ci["hi"] * n, 6),
                         ort=round(ci["ort"] * n, 6))

    ilk_ts = min((str(r.get("ts")) for r in satirlar if _damga(r.get("ts"))), default=None)
    son_ts = max((str(r.get("ts")) for r in satirlar if _damga(r.get("ts"))), default=None)
    simdi = dt.datetime.now(dt.timezone.utc)
    t0 = _damga(ilk_ts)
    gecen_gun = None if t0 is None else max(0, int((simdi - t0).days))
    yayilma_gun = (None if (t0 is None or _damga(son_ts) is None)
                   else max(0, int((_damga(son_ts) - t0).days)))
    doldu = (None if gecen_gun is None
             else bool(n >= n_alt and gecen_gun <= pencere_gun))

    kontrol = kontrol_olc(satirlar, gercek, goal_verisi, fark_ust)
    pk3_sonuc = pk3_olc(pk3, satirlar)

    # ---- KILL#5: PK ölçülüp DÜŞTÜYSE sayı yayılmaz ----------------------------------------------
    yayin_engeli: list[str] = []
    if kontrol["gecti"] is False:
        yayin_engeli.append(
            "kill#5 — PK (2) KONTROL ÖLÇÜLDÜ ve TUTMADI: ortalama |gölge R − gerçek R| = "
            f"{kontrol['ort_mutlak_fark_r']} (eşik {fark_ust}, komisyon+kayma payı "
            f"{kontrol['komisyon_kayma_payi']}). Kart: 'kontrol PK'sı tutmazsa hiçbir sayı "
            "yayılmaz.'")
    if ayrisma:
        yayin_engeli.append("eşik ayrışması — kart ile motor sabitleri AYNI DEĞİL: "
                            + " · ".join(ayrisma))

    k_blogu = {
        "n": n,
        "toplam_r": round(sum(rler), 6) if n else None,
        "ort_r": round(sum(rler) / n, 6) if n else None,
        "kazanma_orani": round(len(kazanan) / n, 6) if n else None,
        "pf": (round(sum(kazanan) / abs(sum(kaybeden)), 6) if kaybeden else None),
        "ci": ci,
        "ci_kabul": ci_kabul,
        "ci_toplam": ci_toplam,
        "kurulum_kirilimi": _dagilim(sayilanlar, "kurulum"),
        "hukum_dagilimi": _dagilim(sayilanlar, "hukum"),
        "cikis_neden_dagilimi": _dagilim(sayilanlar, "cikis_neden"),
        "kol_kirilimi": _dagilim(sayilanlar, "kol"),
        "bar_kaynak_dagilimi": _dagilim(sayilanlar, "bar_kaynak"),
    }
    bastirilan: list[str] = []
    if yayin_engeli:
        bastirilan = sorted(k_blogu)
        k_blogu = {ad: None for ad in bastirilan}

    olculemeyen: list[str] = []
    for r in olculemeyen_satirlar:
        neden = (r.get("olculemedi") or r.get("giris_reddi")
                 or ("kaynak_bar_hash YOK — PIT çapası yarım" if r.get("R") is not None
                     else "R ölçülmedi"))
        olculemeyen.append(f"{r.get('plan_id')} ({r.get('kol')}): {neden}")
    if bozuk:
        olculemeyen.append(f"bozuk_satir: {bozuk} satır JSON olarak ayrıştırılamadı")
    if bozuk_ts:
        olculemeyen.append(
            f"bozuk_ts: {bozuk_ts} satırın `ts` alanı ayrıştırılamadı — pencere içinde mi dışında "
            "mı olduğu ÖLÇÜLEMEDİ, satırlar dışarıda bırakıldı"
            if baslangic else
            f"bozuk_ts: {bozuk_ts} satırın `ts` alanı ayrıştırılamadı — `--baslangic` verilmediği "
            "için pencere süzgeci HİÇ uygulanmadı ve satırlar ölçüme DAHİL edildi")
    if kontrol["neden"]:
        olculemeyen.append(f"PK (2): {kontrol['neden']}")
    if kontrol["n_payi_olculemeyen"]:
        olculemeyen.append(f"PK (2): {kontrol['n_payi_olculemeyen']} çiftte komisyon+kayma payı "
                           "ölçülemedi (giriş/stop ya da goal alanı eksik)")
    if pk3_sonuc["neden"]:
        olculemeyen.append(f"PK (3): {pk3_sonuc['neden']}")
    if ci.get("neden"):
        olculemeyen.append(f"CI: {ci['neden']}")
    if ci.get("uyari"):
        olculemeyen.append(f"CI uyarı: {ci['uyari']}")
    if ci_kabul is False:
        olculemeyen.append("CI: blok=1 → IID bootstrap. Kartın donuk yöntemi MOVING BLOCK'tur; "
                           "bu aralık kartın eşiğini SINAMAZ (REDDEDİLDİ)")
    if gecen_gun is None:
        olculemeyen.append("pencere: hiçbir satırda ayrıştırılabilir `ts` yok — geçen gün "
                           "ÖLÇÜLEMEDİ (0 DEĞİL)")
    for satir in yayin_engeli:
        olculemeyen.append(satir)

    bayt = defter.stat().st_size
    sonuc = {
        "olcum_zamani": simdi.isoformat(timespec="seconds"),
        "kart": gi.KART,
        "girdi": {"defter": str(defter), "gercek": (str(gercek) if gercek else None),
                  "goal": str(goal_yolu), "pk3": (str(pk3) if pk3 else None),
                  "kart_yolu": str(kart_yolu), "baslangic": baslangic,
                  "n_ham_satir": len(ham), "n_pencere_disi": disarida,
                  "n_bozuk_satir": bozuk, "n_bozuk_ts": bozuk_ts},
        "esikler": esikler,
        "modul_sabitleri": modul_sabitleri,
        "esik_ayrismasi": ayrisma,
        "pencere": {"ilk_ts": ilk_ts, "son_ts": son_ts, "gun": pencere_gun,
                    "gecen_gun": gecen_gun, "yayilma_gun": yayilma_gun, "doldu": doldu,
                    "suresi_doldu": (None if gecen_gun is None
                                     else bool(gecen_gun > pencere_gun))},
        "kontrol": kontrol,
        "pk3": pk3_sonuc,
        "bedel": {"satir_gun": (round(len(ham) / gecen_gun, 4)
                                if gecen_gun and gecen_gun > 0 else None),
                  "bayt": bayt, "n_ham_satir": len(ham)},
        "yayin_engeli": yayin_engeli,
        "bastirilan": bastirilan,
        "olculemeyen": olculemeyen,
        "beyan": ("Bu betik SAYAR, HÜKÜM VERMEZ — eşikler kart EDG-2026-088'den ve "
                  "`meridian.golge_icra` sabitlerinden OKUNUR (kopyalanmaz), ayrışmaları "
                  "`esik_ayrismasi` ile ölçülür; hükmü Rol-1 aynı turda karta + K defterine "
                  "işler. K paydası KAPANAN ve R'si ÖLÇÜLMÜŞ ∧ PIT çapası TAM satırlardır; "
                  "`giris_yok` ve `kaynak_bar_hash=None` satırları TANIdır. CI ORTALAMANIN "
                  "moving-block aralığıdır (tohum/B/blok çıktıda adıyla); IID (blok=1) "
                  "REDDEDİLİR; `ci_toplam` bir TÜRETMEdir, ölçüm değildir. PK (2) ölçülüp "
                  "DÜŞERSE (kill#5) K blokunun tamamı BASTIRILIR. Ölçülemeyen her değer None + "
                  "neden'dir; 0 ile 'bilmiyorum' aynı şey değildir."),
    }
    sonuc.update(k_blogu)
    return sonuc


# ==================================================================================================
# MARKDOWN RAPOR
# ==================================================================================================
def _sayi(x, basamak=4) -> str:
    if x is None:
        return "None"
    if isinstance(x, float):
        return f"{x:.{basamak}f}"
    return str(x)


def _tablo(d: dict) -> str:
    return ", ".join(f"{k}×{v}" for k, v in (d or {}).items()) or "—"


def markdown_uret(sonuc: dict) -> str:
    p, k, pk3 = sonuc["pencere"], sonuc["kontrol"], sonuc["pk3"]
    s = [f"# EDG-2026-088 — uyuyan kurulum gölge icra sayımı ({sonuc['olcum_zamani']})", ""]

    # ---- 1) YAYIN ENGELİ: hiçbir K sayısı basılmaz ----------------------------------------------
    if sonuc["yayin_engeli"]:
        s += ["## PK DÜŞTÜ — SAYI YAYILMAZ", ""]
        s += [f"* {x}" for x in sonuc["yayin_engeli"]]
        s += ["", f"Bastırılan alanlar: `{'`, `'.join(sonuc['bastirilan'])}`.", "",
              "### Yalnız kontrol ölçümü (engelin kendisi)", "",
              f"* eşleşen çift: {k['n_cift']} · ortalama fark: {_sayi(k['ort_fark_r'])}R · "
              f"ortalama |fark|: {_sayi(k['ort_mutlak_fark_r'])}R",
              f"* eşik: {_sayi(k['esik'])}R · komisyon+kayma payı: "
              f"{_sayi(k['komisyon_kayma_payi'])}R", ""]
        s += ["---", "", sonuc["beyan"]]
        return "\n".join(s) + "\n"

    # ---- 2) PENCERE DOLMADI: betimleyici ara-rapor, EŞİK CÜMLESİ YOK ----------------------------
    if p["doldu"] is not True:
        s += ["## HÜKÜM YOK (betimleyici ara-rapor)", "",
              (f"Pencere DOLMADI: n={sonuc['n']} (alt sınır {sonuc['modul_sabitleri']['N_ALT']}) · "
               f"geçen gün={p['gecen_gun']} (üst sınır {p['gun']}). "
               "Bu raporda hiçbir eşik karşılaştırması YOKTUR — n<alt sınır ile yazılan eşik "
               "cümlesi selef 049'un ikinci düşme sebebiydi."), ""]
    else:
        s += ["## Pencere DOLDU — sayılar aşağıda (hüküm Rol-1'in)", ""]

    s += ["## K ölçüleri", "",
          f"* n (kapanan, R ölçülmüş, PIT çapası tam): **{sonuc['n']}**",
          f"* toplam R: **{_sayi(sonuc['toplam_r'])}** · ortalama R: {_sayi(sonuc['ort_r'])}",
          f"* kazanma oranı: **{_sayi(sonuc['kazanma_orani'])}** · PF: {_sayi(sonuc['pf'])}",
          f"* CI95 (ORTALAMA R): [{_sayi(sonuc['ci']['lo'])}, {_sayi(sonuc['ci']['hi'])}] — "
          f"{sonuc['ci']['yontem']}",
          f"* CI95 (TOPLAM R, türetme): [{_sayi(sonuc['ci_toplam']['lo'])}, "
          f"{_sayi(sonuc['ci_toplam']['hi'])}] — {sonuc['ci_toplam']['turetme']}",
          f"* CI kabul edildi mi (IID DEĞİL mi): {sonuc['ci_kabul']}", ""]

    s += ["## Tanı (K'ye çarpılmaz)", "",
          f"* kurulum kırılımı: {_tablo(sonuc['kurulum_kirilimi'])}",
          f"* hüküm (kapı) dağılımı: {_tablo(sonuc['hukum_dagilimi'])}",
          f"* çıkış nedeni dağılımı: {_tablo(sonuc['cikis_neden_dagilimi'])}",
          f"* kol kırılımı: {_tablo(sonuc['kol_kirilimi'])}",
          f"* bar kaynağı: {_tablo(sonuc['bar_kaynak_dagilimi'])}", ""]

    s += ["## Pozitif kontroller", "",
          f"* **PK (2) kontrol kolu** — ölçüldü mü: {k['gecti']} · çift: {k['n_cift']} · "
          f"ortalama fark: {_sayi(k['ort_fark_r'])}R · ortalama |fark|: "
          f"{_sayi(k['ort_mutlak_fark_r'])}R · komisyon+kayma payı: "
          f"{_sayi(k['komisyon_kayma_payi'])}R",
          f"* **PK (3) selef (EDG-2026-049)** — referans: n={pk3['n']}, kayıp={pk3['kayip']}, "
          f"toplam R={_sayi(pk3['toplam_r'])} · gölge: n={pk3['golge']['n']}, "
          f"kayıp={pk3['golge']['kayip']}, toplam R={_sayi(pk3['golge']['toplam_r'])} · "
          f"eşleşme: {pk3['esles']}", ""]

    # ---- 3) EŞİK KARŞILAŞTIRMASI YALNIZ PENCERE DOLUNCA ----------------------------------------
    if p["doldu"] is True:
        e = sonuc["modul_sabitleri"]
        s += ["## Eşik karşılaştırması (SAYI; hüküm cümlesi Rol-1'in)", "",
              "| Ölçü | Değer | Kartın eşiği |", "|---|---|---|",
              f"| n | {sonuc['n']} | {e['N_ALT']} |",
              f"| CI95 alt sınırı (ortalama R) | {_sayi(sonuc['ci']['lo'])} | {e['CI_ALT_R']} |",
              f"| CI95 alt sınırı (toplam R, türetme) | {_sayi(sonuc['ci_toplam']['lo'])} | "
              f"{e['CI_ALT_R']} |",
              f"| kazanma oranı | {_sayi(sonuc['kazanma_orani'])} | {e['KAZANMA_ALT']} |",
              f"| geçen gün | {p['gecen_gun']} | {e['PENCERE_GUN']} |",
              f"| PK (2) ortalama \\|fark\\| | {_sayi(k['ort_mutlak_fark_r'])} | {e['FARK_R_UST']} |",
              ""]

    s += ["## Bedel", "",
          f"* satır/gün: {_sayi(sonuc['bedel']['satir_gun'])} · defter: "
          f"{sonuc['bedel']['bayt']} bayt · ham satır: {sonuc['bedel']['n_ham_satir']}", ""]

    if sonuc["olculemeyen"]:
        s += ["## Ölçülemeyenler", ""] + [f"* {x}" for x in sonuc["olculemeyen"]] + [""]
    s += ["---", "", sonuc["beyan"]]
    return "\n".join(s) + "\n"


# ==================================================================================================
# CLI
# ==================================================================================================
def ana(argv=None) -> int:
    ap = argparse.ArgumentParser(description="EDG-2026-088 gölge icra sayacı")
    ap.add_argument("--defter", required=True, help="state/golge_icra.jsonl yolu (SALT OKUNUR)")
    ap.add_argument("--cikti", required=True, help="JSON sonuç yolu")
    ap.add_argument("--markdown", default=None, help="isteğe bağlı markdown rapor yolu")
    ap.add_argument("--baslangic", default=None,
                    help="ISO damga (Z ya da +00:00); bu andan ÖNCEKİ satırlar pencere dışıdır")
    ap.add_argument("--kart", default=str(VARSAYILAN_KART), help="eşiklerin okunduğu kart")
    ap.add_argument("--gercek", default=None,
                    help="trades.jsonl yolu (PK 2); verilmezse defterin yanındaki dosya aranır")
    ap.add_argument("--goal", default=str(VARSAYILAN_GOAL),
                    help="komisyon/kayma payının okunduğu goal.yaml")
    ap.add_argument("--pk3", default=None,
                    help="EDG-2026-049 kesiti (islemler_tam_dormant_acik.json) — PK (3)")
    ns = ap.parse_args(argv)

    sonuc = calistir(defter=ns.defter, kart=ns.kart, baslangic=ns.baslangic, gercek=ns.gercek,
                     goal=ns.goal, pk3=ns.pk3)

    cikti_yolu = pathlib.Path(ns.cikti)
    cikti_yolu.parent.mkdir(parents=True, exist_ok=True)
    cikti_yolu.write_text(json.dumps(sonuc, indent=2, sort_keys=True, ensure_ascii=False),
                          encoding="utf-8")
    if ns.markdown:
        md_yolu = pathlib.Path(ns.markdown)
        md_yolu.parent.mkdir(parents=True, exist_ok=True)
        md_yolu.write_text(markdown_uret(sonuc), encoding="utf-8")

    # PENCERE DIŞI VE YAYIN ENGELİ TERMİNALE BASILIR: operatör damga biçimi yüzünden pencereyi
    # kaybettiyse ya da kill#5 ateşlediyse bunu raporun içinde değil, komutu koştuğu anda görmeli.
    print(f"yazildi: {cikti_yolu} — n={sonuc['n']} toplam_r={_sayi(sonuc['toplam_r'])} "
          f"kazanma={_sayi(sonuc['kazanma_orani'])} pencere_doldu={sonuc['pencere']['doldu']} "
          f"gecen_gun={sonuc['pencere']['gecen_gun']} "
          f"pencere_disi={sonuc['girdi']['n_pencere_disi']} "
          f"pk2={sonuc['kontrol']['gecti']} pk3={sonuc['pk3']['esles']} "
          f"yayin_engeli={len(sonuc['yayin_engeli'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(ana())
