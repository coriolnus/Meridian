"""faz5_cikis.py — FAZ-5 ÇIKIŞ ÖLÇÜMÜ: dakika-hassas icranın CI'lı kazancı (kart EXE-2026-002).

NEDEN VAR. `health.faz6_kilitleri`nin ÜÇÜNCÜ kilidi (`faz5_cikisi`) bugüne kadar SABİT `False` /
`olculemedi` yazıyordu ve gerekçesi kendi kodunda duruyordu: "Faz-5 çıkış ölçümünü (dakika-hassas
icranın CI'lı kazancı) ÜRETEN kod yok". Merdivendeki dört kapalı kilidin üçü KANIT eksikliğinden
kapalıdır (edge 1/5, sonuç 0/4, DSR 1e-06) ve kodla açılamaz — kârlı işlem geçmişi ister. Bu kilit
TEK istisnaydı: kapalı olma sebebi ÖLÇÜMÜN YOKLUĞUydu. Bu modül o ölçümü üretir. Kilit bundan sonra
da kapalı kalabilir, ama gerekçesi "üreten kod yok"tan ÖLÇÜLMÜŞ bir cümleye döner ("örneklem 4/20"
gibi) — ve ikincisi zamanla kendiliğinden dolar, birincisi dolmaz.

NEDEN AYRI MODÜL, `analytics.py` DEĞİL (üç ölçülmüş sebep, bir tercih değil):
  1. `tests/test_wpm_sasi_v173::test_A_analytics_KENDI_bootstrapini_DEVRETMEDI` AST seviyesinde
     çivileniyor: `analytics.py` `olcum_araclari`yı import ETMEZ. Gerekçe yayımlanmış sayıların
     korunmasıdır (`analytics._blok_bootstrap_ci`, CIRCULAR blok=5 İŞLEM, `result_verdict`in
     tabanı). Bu ölçüm bir bootstrap ister; analytics'e konsaydı ya çivi kırılırdı ya da analytics
     içinde ÜÇÜNCÜ bir bootstrap gövdesi doğardı — ikisi de o testin engellediği sınıf.
  2. OKUDUĞU DEFTER FARKLI. `edge_verdict`/`result_verdict` KAPANMIŞ İŞLEM defterini okur
     (trades + kalibrasyon) ve "kenar var mı / para var mı" sorusuna R ve DOLAR biriminde cevap
     verir. Bu ölçüm 4b GÖLGE defterini okur ve "dakika-hassas GİRİŞ, EOD zamanlamasına göre ne
     kazandırırdı" sorusuna BPS biriminde cevap verir. Ortak tek şey hükmün tüketicisidir
     (Faz-6 zinciri), gövdesi değil.
  3. `health.faz6_kilitleri` üç hesabı ZATEN geç-import ile alıyor (`analytics`, `validation`,
     `dataset`). Dördüncüsü aynı desenle gelir; `analytics` içine konsaydı 4.173 satırlık dosyanın
     ithal maliyeti hiç değişmezdi ama kartın ölçümü onun yayımlanmış yüzeyine karışırdı.
Modülün adı kilidin adıyla AYNI (`faz5_cikisi` ↔ `faz5_cikis.py`): kilidi panoda gören okuyucu,
sayının hangi dosyadan geldiğini aramak zorunda kalmasın.

EŞİKLER KARTTAN GELİR VE KOD BUNLARI DEĞİŞTİREMEZ (`research/cards/EXE-2026-002-faz5-cikis-
olcumu.yaml`, ölçümden ÖNCE donduruldu): n_min = 20 · %95 · TARİH-KÜMELİ bootstrap 10.000 ·
kazanç E3 maliyet bandının ÜSTÜNDE. `kill_criteria` dokunulmazdır. Ölçüm sonucu hoşa gitmediğinde
değişecek olan şey eşik değil, hükümdür.

METODOLOJİK SINIR (kartta yazılı, burada YUMUŞATILMAZ). 4b'nin `sim_fill`i GÖZLENMİŞ bir dolum
DEĞİLDİR: `max(bar_open, entry_trigger)` kuralıyla ÜRETİLMİŞ bir modeldir; iç EOD dolumu da bir
simülasyondur. Yani BİRİNCİL karşılaştırma MODEL-MODEL'dir ve ölçtüğü şey ZAMANLAMA etkisidir,
gerçek icra kalitesi değil. İkisi de AYNI maliyet modelini taşır, fark yalnız zamanlamadan gelir.
Gerçek Alpaca dolumlarıyla kıyas AYRI bir satırdır (`gerceklik_capasi`), hüküm VERMEZ ve
`hukme_girmez: True` ile damgalanır — bir modeli gerçekle kıyaslamak modeli KAYIRIR.

BU MODÜL SAF OKUMADIR: hiçbir dosyaya yazmaz, hiçbir bayrağı çevirmez, hiçbir emir yolu açmaz.
"""
from __future__ import annotations

from . import config, store

# ---- KART SABİTLERİ (EXE-2026-002; ölçümden ÖNCE donduruldu, kod bunları değiştiremez) ---------
KART = "EXE-2026-002"
N_MIN = 20                  # asgari eşleşmiş çift; altında hüküm "ÖLÇÜLDÜ — ÖRNEKLEM YETERSİZ"
CI_SEVIYE = 0.95
BOOTSTRAP_N = 10_000        # kartın yazdığı replikasyon sayısı (repo varsayılanı 2.000 DEĞİL)
BOOTSTRAP_TOHUM = 11        # repo kanonu (olcum_araclari.BOOTSTRAP_TOHUM ile aynı sayı): aynı
                            # defter aynı aralığı verir — tekrarlanabilirlik şartı
KILL_ESLESMEME_ORANI = 0.20  # kill#4: BOZULMA (defter güvenilmezliği) oranı bunun ÜSTÜNDEyse hüküm
                            # YOK. R1 (EXE-2026-002-R1): oran YALNIZ bozulma sınıflarından hesaplanır
KAPSAM_DISI_SINIFLARI = ("eod_yok",)  # MEŞRU DOLMAMA — kill#4 DIŞI (R1). Gölge sağlam ama iç EOD
                            # motoru doldurmamayı SEÇTİ (limit kaçtı, kapı düşürdü, gap vetosu):
                            # eşleşme YAPISAL olarak oluşmaz. `kapsam_disi` olarak ADIYLA sayılır,
                            # hükmü GEÇERSİZ KILMAZ; yalnız eşleşen çift sayısını düşürür → n_min'e
                            # havale. BURADA OLMAYAN her eşleşmeme (golge_bozuk, bps_yok ve gelecekte
                            # doğacak her yeni kırılma) BOZULMA sayılır — fail-closed.
MIN_KUME = 2                # tek tarih kümesinde kümeler-arası dağılım KURULAMAZ (aşağıda gerekçe)
AD_TAVANI = 50              # ad/çift listelerinin BEYANLI tavanı — sayaçlar hep TAM, kırpma sayısı
                            # `*_kirpildi` ile yazılır (defter süresiz büyür ve bu sözlük
                            # /api/diagnostics yükünün içine girer)

EOD_DEFTERI = "trades.jsonl"
PORTFOLIO = "portfolio.json"
E2_DEFTERI = "entry_execution.jsonl"   # gerçeklik çapası: `motor="ayna"` = Alpaca dolumları


def _golge_defteri() -> str:
    """Gölge defterinin adı TEK KAYNAKTAN (`intraday_shadow.ORDERS_FILE`) gelir.

    GEÇ IMPORT, BİLEREK: `intraday_shadow` modül seviyesinde `health`i import eder ve `health` de
    bu modülü (geç) import edecektir. Modül seviyesinde bağlansaydı ithal grafiğinde bir halka
    doğardı; sabiti burada İKİNCİ kez yazmak ise defter adının iki yerde sessizce ayrışması
    demekti — ikisi de istenmiyor, geç import ikisini de çözer."""
    from .intraday_shadow import ORDERS_FILE
    return ORDERS_FILE


# ==================================================================================================
# TARİH-KÜMELİ (CLUSTER) BOOTSTRAP
# ==================================================================================================
# NEDEN DÜZ BOOTSTRAP DEĞİL. Aynı seansta dolan planlar AYNI AÇILIŞI paylaşır: o sabahki gap, o
# günün açılış müzayedesinin efektif spread'i ve o günün rejimi hepsine BİRLİKTE vurur. Yani bir
# gündeki iki dolum iki BAĞIMSIZ gözlem değildir; düz (IID) bootstrap onları bağımsız sayar,
# ortalamanın örnekleme dağılımını olduğundan DAR gösterir ve aralık ölçülmemiş bir kesinlik yazar.
# Hata TEK YÖNLÜDÜR: IID daima "daha anlamlı" görünür, hiçbir zaman daha az — yani bu kilidi HAK
# ETMEDEN açma yönünde yanlıdır. Kart bu yüzden yöntemi ölçümden önce dondurdu.
#
# NEDEN `olcum_araclari.blok_bootstrap_ci` DEĞİL (ikisi de "bağımlılığı koru" der ama AYNI ŞEY
# DEĞİLDİR). O araç MOVING BLOK bootstrap'ıdır: girdinin ZAMAN SIRALI tek bir seri olduğunu ve
# bağımlılığın komşu gözlemler arasında SÜREKLİ aktığını varsayar (blok = ardışık L gözlem). Buradaki
# bağımlılık yapısı süreklilik değil KÜMELENMEdir: aynı günün gözlemleri tam bağımlı, farklı günlerin
# gözlemleri değiştirilebilir (exchangeable). Bir günde 3, ertesi günde 1 dolum varsa "ardışık L
# gözlem" bloğu gün sınırlarını KESER — ne kümeyi korur ne de gerçek bir zaman komşuluğu ölçer.
# Küme bootstrap'ı GÜNLERİ yeniden örnekler ve seçilen günün TÜM gözlemlerini birlikte taşır; blok
# uzunluğu diye bir serbestlik de kalmaz (K'ya yazılacak bir seçim değildir).
def tarih_kumeli_bootstrap(degerler, tarihler, n_ornek: int = BOOTSTRAP_N,
                           seviye: float = CI_SEVIYE, tohum: int = BOOTSTRAP_TOHUM) -> dict:
    """ORTALAMANIN tarih-kümeli (cluster) bootstrap güven aralığı.

    Yeniden örneklenen birim GÜNDÜR, gözlem değil: G ayrı tarih varsa her replikasyonda G tarih
    YERİNE KOYARAK çekilir ve seçilen her tarihin TÜM gözlemleri havuza birlikte girer. Ortalama
    havuzun düz ortalamasıdır (yani büyük günler doğal olarak daha çok ağırlık taşır — gerçek
    örneklemde de öyleydi).

    ÖLÇÜLEMEDİĞİNDE UYDURMAZ: küme sayısı < 2 ise `lo`/`hi` **None** ve `neden` doludur;
    `sifiri_disliyor` da None'dır (False DEĞİL). Tek kümede her replikasyon AYNI havuzu üretir,
    yani genişliği SIFIR bir aralık çıkar ve o aralık "sıfırı dışlıyor" der — ölçülmemiş bir
    kesinliğin en tehlikeli hâli, çünkü kilidi açma yönünde yanlıdır.
    """
    import numpy as np

    ham_d = list(degerler) if degerler is not None else []
    ham_t = list(tarihler) if tarihler is not None else []
    if len(ham_d) != len(ham_t):
        raise ValueError(f"değer/tarih hizası bozuk: {len(ham_d)} değer, {len(ham_t)} tarih — "
                         "küme bootstrap'ı hangi gözlemin hangi güne ait olduğunu UYDURAMAZ")

    kume: dict = {}
    vals: list[float] = []
    n_cozulemeyen = 0
    for v, t in zip(ham_d, ham_t):
        try:
            f = float(v)
        except (TypeError, ValueError):  # sessiz-yutma: sayıya çevrilemeyen gözlem SAYILIR (n_cozulemeyen) ve çıktıda görünür — bir bootstrap'ta sessizce düşen gözlem, örneklem büyüklüğünü haber vermeden küçültür
            n_cozulemeyen += 1
            continue
        if f != f or f in (float("inf"), float("-inf")):
            n_cozulemeyen += 1
            continue
        anahtar = str(t) if t is not None else "?"
        kume.setdefault(anahtar, []).append(f)
        vals.append(f)

    n, g = len(vals), len(kume)
    ortak = {"n": n, "n_kume": g, "seviye": seviye, "tohum": tohum,
             "n_cozulemeyen": n_cozulemeyen,
             "kume_boylari": {k: len(v) for k, v in sorted(kume.items())},
             "yontem": (f"TARİH-KÜMELİ (cluster) bootstrap · yeniden örneklenen birim = SEANS · "
                        f"B={int(n_ornek)} · tohum={tohum} · yüzdelik aralığı"),
             "beyan": ("Aynı seansta dolan planlar aynı açılışı paylaşır ve BAĞIMSIZ SAYILAMAZ; "
                       "düz (IID) bootstrap aralığı sistematik olarak daraltır ve hükmü kilidi "
                       "AÇMA yönünde kaydırır. Aralık ORTALAMA içindir.")}
    if n == 0:
        return {**ortak, "ort": None, "lo": None, "hi": None, "sifiri_disliyor": None, "B": 0,
                "neden": "hiç ölçülebilir gözlem yok — ortalama da aralık da kurulamaz"}
    if g < MIN_KUME:
        return {**ortak, "ort": float(np.mean(vals)), "lo": None, "hi": None,
                "sifiri_disliyor": None, "B": 0,
                "neden": (f"tek tarih kümesi (küme={g} < {MIN_KUME}) — kümeler ARASI dağılım "
                          "kurulamaz; tek kümede bootstrap genişliği SIFIR bir aralık üretir ve "
                          "o aralık ölçülmemiş bir kesinliktir")}

    B = max(1, int(n_ornek))
    adlar = sorted(kume)
    toplam = np.array([sum(kume[a]) for a in adlar], dtype=float)
    boy = np.array([len(kume[a]) for a in adlar], dtype=float)
    rng = np.random.default_rng(tohum)
    sec = rng.integers(0, g, size=(B, g))            # G KÜME, yerine koyarak
    ortalamalar = toplam[sec].sum(axis=1) / boy[sec].sum(axis=1)
    alt = (1.0 - seviye) / 2.0 * 100.0
    lo, hi = (float(q) for q in np.percentile(ortalamalar, [alt, 100.0 - alt]))
    return {**ortak, "ort": float(np.mean(vals)), "lo": lo, "hi": hi, "B": B,
            "sifiri_disliyor": bool(lo > 0 or hi < 0), "neden": None}


# ==================================================================================================
# EŞLEŞTİRME + EŞLEŞTİRİLMİŞ FARK
# ==================================================================================================
def _eod_defteri() -> dict:
    """`plan_id` → iç EOD dolumu (fiyat, yön, kaynak). İKİ KAYNAK, biri diğerinin yerine geçmez:
    kapanmış işlemler (`trades.jsonl`) ve HÂLÂ AÇIK pozisyonlar (`portfolio.json`) — pozisyon
    açıkken de kıyas yapılabilmeli (`intraday_shadow.vs_eod` ile AYNI iki kaynak).

    YÖN DE BURADAN OKUNUR: gölge satırında `side` alanı YOKTUR ve kartın formülü kısa tarafta
    işareti ters çevirir. Yönü "long" diye VARSAYMAK, ölçülmemiş bir şeyi ölçülmüş göstermek
    olurdu — bugün canlı yol yalnız long üretiyor olsa bile (loop.py:1374), varsayım koda gömülmez.
    """
    out: dict = {}
    for tr in store.read_jsonl(EOD_DEFTERI):
        pid, e = tr.get("plan_id"), tr.get("entry")
        if pid and e is not None:
            try:
                out[pid] = {"fill": float(e), "side": tr.get("side"),
                            "kaynak": f"{EOD_DEFTERI} (kapanmış işlem)"}
            except (TypeError, ValueError):  # sessiz-yutma: biçimsiz `entry` EOD tarafını ölçülemez yapar; satır eşleşmez sayılır ve ADIYLA raporlanır (aşağıda), sessizce düşmez
                continue
    pf = store.read_json(PORTFOLIO, {}) or {}
    for p in (pf.get("positions") or {}).values():
        pid, e = p.get("plan_id"), p.get("entry")
        if pid and e is not None and pid not in out:
            try:
                out[pid] = {"fill": float(e), "side": p.get("side"),
                            "kaynak": f"{PORTFOLIO} (açık pozisyon)"}
            except (TypeError, ValueError):  # sessiz-yutma: aynı gerekçe — açık pozisyonun biçimsiz girişi de eşleşme sayılmaz ve adıyla görünür
                continue
    return out


def _bps_ve_r(sim_fill: float, eod_fill: float, side, qty, risk_dollars) -> tuple:
    """Kartın `features_asof` formülleri, BİREBİR:

        kazanc_bps = (eod_fill − golge_sim_fill) / eod_fill × 10000   [uzun; kısa taraf işaret ters]
        kazanc_R   = (eod_fill − golge_sim_fill) × qty / risk_dollars

    Dönen: (bps, R, neden) — ölçülemeyen bacak None ve `neden` doludur (0 DEĞİL).
    `eod_fill == 0` bölünemez; `qty`/`risk_dollars` yoksa R ölçülemez ama BPS ölçülebilir kalır —
    iki bacağı tek "ölçülemedi"ye katlamak, ölçülmüş olanı da atmak olurdu."""
    if not eod_fill:
        return None, None, "eod_fill 0/None — bps paydası kurulamaz"
    yon = str(side or "").lower()
    if yon not in ("long", "short"):
        return None, None, f"yön ölçülemedi (side={side!r}) — kısa tarafta işaret TERS çevrilir"
    isaret = 1.0 if yon == "long" else -1.0
    fark = (eod_fill - sim_fill) * isaret
    bps = fark / eod_fill * 10000.0
    try:
        r = fark * float(qty) / float(risk_dollars)
    except (TypeError, ValueError, ZeroDivisionError):  # sessiz-yutma: qty/risk_dollars yok ya da sıfır → R ölçülemez; BPS bacağı ÖLÇÜLDÜ ve atılmaz, R None döner ve sayacı çıktıda durur
        return bps, None, None
    return bps, r, None


def _cift(row: dict, eod: dict) -> dict:
    """Tek gölge satırının eşleştirme sonucu.

    `sinif` ÜÇ AYRI KIRILMA SINIFI taşır ve tek "eşleşmedi"ye katlanmaz — kill#4 ateşlediğinde
    kök-neden turuna gidecek olan tam olarak bu ayrımdır: `golge_bozuk` (4b yazımı kusurlu),
    `eod_yok` (join anahtarının karşılığı yok), `bps_yok` (eşleşti ama fark hesaplanamadı)."""
    pid = row.get("plan_id")
    ad = f"{pid or '?'}·{row.get('date') or '?'}"
    try:
        sf = float(row.get("sim_fill"))
    except (TypeError, ValueError):  # sessiz-yutma: `sim_fill` yoksa satır zaten evrene girmemeliydi; buraya düşerse ADIYLA eşleşmez sayılır — sessiz düşürme kartın açıkça yasakladığı şey
        return {"ad": ad, "sinif": "golge_bozuk", "neden": "gölge sim_fill biçimsiz/None"}
    e = eod.get(pid)
    if not e:
        return {"ad": ad, "sinif": "eod_yok", "neden": "iç EOD defterinde karşılığı YOK"}
    bps, r, neden = _bps_ve_r(sf, e["fill"], e.get("side"), row.get("qty"),
                              row.get("risk_dollars"))
    if bps is None:
        return {"ad": ad, "sinif": "bps_yok", "neden": neden}
    return {"ad": ad, "sinif": "eslesti", "plan_id": pid, "ticker": row.get("ticker"),
            "date": row.get("date"), "sim_fill": sf, "eod_fill": e["fill"],
            "side": e.get("side"), "eod_kaynak": e["kaynak"],
            "kazanc_bps": round(bps, 4),
            "kazanc_R": (None if r is None else round(r, 4)),
            # İKİNCİL bacak ölçülemediğinde BİRİNCİL bacak atılmaz; eksiklik satırda adıyla durur.
            "r_neden": (None if r is not None else
                        "gölge satırında qty/risk_dollars yok ya da 0 — R ÖLÇÜLEMEDİ (0 değil)")}


def gerceklik_capasi(ciftler: list) -> dict:
    """GERÇEKLİK ÇAPASI — AYRI SATIR, HÜKÜM VERMEZ (`hukme_girmez: True`).

    Aynı planların GERÇEK Alpaca dolumları (`entry_execution.jsonl`, `motor="ayna"`, `fill`) ile
    gölge `sim_fill`i arasındaki fark. Kartın metodolojik sınırı gereği bu satır kilidi AÇMAZ ve
    hükme GİRMEZ: birincil hüküm İKİ SİMÜLASYON arasında kurulur, çünkü bir modeli gerçek dolumla
    kıyaslamak modelin kendi varsayımı lehine sonuç üretir (modeli KAYIRIR). Burada söylenen tek
    şey "model gerçeğe ne kadar yakın"dır."""
    gercek: dict = {}
    for r in store.read_jsonl(E2_DEFTERI):
        if r.get("motor") != "ayna" or r.get("fill") is None:
            continue
        pid = r.get("plan_id")
        if not pid:
            continue
        try:
            gercek[pid] = float(r["fill"])
        except (TypeError, ValueError):  # sessiz-yutma: biçimsiz gerçek dolum çapaya girmez; çapa hükme girmediği için sayaç `n` ile beyan edilir, ayrı bir kova açılmaz
            continue
    vals, tarihler = [], []
    for c in ciftler:
        f = gercek.get(c.get("plan_id"))
        if f is None or not f:
            continue
        isaret = 1.0 if str(c.get("side") or "").lower() == "long" else -1.0
        vals.append((f - c["sim_fill"]) * isaret / f * 10000.0)
        tarihler.append(c.get("date"))
    if not vals:
        return {"n": 0, "ort_bps": None, "ci": None, "hukme_girmez": True,
                "neden": (f"eşleşmiş çiftlerin hiçbirinin GERÇEK Alpaca dolumu yok "
                          f"(state/{E2_DEFTERI} · motor=ayna · fill) — model-gerçek yakınlığı "
                          "ÖLÇÜLEMEDİ; 0 bps yazmak 'model mükemmel' demek olurdu"),
                "kapsam": "AYRI SATIR — kilidi açmaz, hükme girmez"}
    ci = tarih_kumeli_bootstrap(vals, tarihler)
    return {"n": len(vals), "ort_bps": round(ci["ort"], 4) if ci["ort"] is not None else None,
            "ci": {"alt": (None if ci["lo"] is None else round(ci["lo"], 4)),
                   "ust": (None if ci["hi"] is None else round(ci["hi"], 4)),
                   "neden": ci["neden"]},
            "hukme_girmez": True, "neden": None,
            "kapsam": ("AYRI SATIR — kilidi açmaz, hükme girmez; 'model gerçeğe ne kadar yakın' "
                       "beyanıdır (kart: metodolojik sınır)")}


# ==================================================================================================
# HÜKÜM
# ==================================================================================================
def cikis_olcumu(rows: list | None = None) -> dict:
    """FAZ-5 ÇIKIŞ HÜKMÜ: `{"gecer", "durum", "neden", "olcum", "esik"}`.

    HÜKÜM SIRASI (kartın kill listesiyle AYNI sıra — sıra da bir karardır):
      0. defter/evren BOŞ            → durum `olculemedi`, gecer False (ölçülemedi ≠ 0)
      1. KILL#4 BOZULMA > %20        → durum `olculemedi`, HÜKÜM YOK, kök-neden turu gerekiyor
                                       (R1: yalnız golge_bozuk+bps_yok; eod_yok kapsam DIŞI → n_min)
      2. n < n_min                   → durum `olculdu`,   gecer False, "ÖRNEKLEM YETERSİZ (n/20)"
      3. CI kurulamadı (küme < 2)    → durum `olculemedi`, gecer False (fail-closed)
      4. CI sıfırı İÇERİYOR          → durum `olculdu`,   gecer False (kill#1)
      5. CI tamamen NEGATİF          → durum `olculdu`,   gecer False (kill#2 — 4b bir maliyettir)
      6. CI alt sınırı ≤ maliyet bandı → durum `olculdu`, gecer False (kill#3 — anlamlı ama işe yaramaz)
      7. CI alt sınırı > band        → durum `olculdu`,   gecer True

    `gecer` ÜÇ DEĞERLİ DEĞİLDİR (health.py:108-113 sözleşmesi): ölçülemeyen kilit KAPALIdır.
    Kill#4 önce gelir çünkü eşleştirme kırıksa n de ortalama da CI de YANLIŞ bir evrenden gelir —
    kırık bir eşleştirmenin üstüne kurulan "örneklem yetersiz" cümlesi de yanlış olurdu.

    `rows` verilirse defter YENİDEN okunmaz (`intraday_shadow.vs_eod`/`summarize` deseni): bir uç
    tek istekte hem özeti hem hükmü derlerken iki okuma arasına düşen bir satır yüzünden aynı
    yanıtta iki farklı gerçek belirmesin."""
    from . import analytics as _an

    defter = _golge_defteri()
    ham = store.read_jsonl(defter) if rows is None else list(rows)
    # EVREN (kart): "4b gölge defterinde DOLUM ÜRETMİŞ her plan". Kapıda bloklanmış satır dolum
    # üretmemiştir — evrenin DIŞINDADIR, "eşleşmeyen" DEĞİLDİR. İkisini karıştırmak kill#4'ün
    # paydasını şişirir ve bir bütünlük sorunu olmadığı hâlde hükmü sildirirdi.
    evren = [r for r in ham if r.get("sim_fill") is not None]
    band = _an.pessimistic_band()
    band_bps = float(band.get("ek_bps_giris") or 0.0)
    esik = (f"eşleştirilmiş kazanç %{int(CI_SEVIYE * 100)} CI ALT SINIRI > E3 maliyet bandı "
            f"({band_bps} bps) VE n >= {N_MIN} (kart {KART}; tarih-kümeli bootstrap "
            f"B={BOOTSTRAP_N})")

    olcum: dict = {
        "kart": KART, "n_defter": len(ham), "n_evren": len(evren), "n_min": N_MIN,
        "kaynaklar": {"golge": f"state/{defter}",
                      "eod": f"state/{EOD_DEFTERI} + state/{PORTFOLIO}",
                      "gerceklik_capasi": f"state/{E2_DEFTERI} (motor=ayna)"},
        "maliyet_bandi": {"ek_bps_giris": band_bps, "taban": band.get("taban"),
                          "model": "pessimistic_band_v2 (E3)"},
        "birim": "BİRİNCİL bps (giriş fiyatının onbinde biri) · İKİNCİL R",
        "sinir": ("MODEL-MODEL karşılaştırması: 4b `sim_fill` = max(bar_open, entry_trigger) ile "
                  "ÜRETİLMİŞ bir modeldir, GÖZLENMİŞ dolum değil; iç EOD dolumu da simülasyondur. "
                  "Ölçülen şey ZAMANLAMA etkisidir, gerçek icra kalitesi değil."),
    }

    if not evren:
        return {"gecer": False, "durum": "olculemedi", "esik": esik,
                "olcum": {**olcum, "n_eslesen": None, "ortalama_bps": None,
                          "ci": None, "ortalama_R": None, "eslesmeyen": None},
                "neden": (f"4b gölge defterinde DOLUM ÜRETMİŞ satır YOK "
                          f"(defter {len(ham)} satır, evren 0) — eşleştirilmiş fark ÖLÇÜLEMEDİ. "
                          "Sıfır çift 'kazanç 0 bps' demek DEĞİLDİR; ölçüm yokken kilit "
                          "FAIL-CLOSED kapalıdır")}

    eod = _eod_defteri()
    sonuclar = [_cift(r, eod) for r in evren]
    ciftler = [c for c in sonuclar if c["sinif"] == "eslesti"]
    eslesmeyen = [c for c in sonuclar if c["sinif"] != "eslesti"]
    n = len(ciftler)

    # KILL#4 DARALTMASI (EXE-2026-002-R1). Eşleşmeyen İKİ AYRI OLGUdur ve kill#4 YALNIZ BOZULMAya
    # bakar (eski geniş ölçüt ikisini karıştırıyordu — kartın TANIM KUSURU):
    #   (a) BOZULMA — defter güvenilmez, hüküm verilemez: `golge_bozuk` (gölge satırı biçimsiz) +
    #       `bps_yok` (eşleşti ama fark hesaplanamadı). Oran BUNLARDAN hesaplanır; > %20 → hüküm YOK.
    #   (b) MEŞRU DOLMAMA — `eod_yok`: gölge sağlam ama iç EOD motoru doldurmamayı SEÇTİ (limit
    #       kaçtı, kapı düşürdü, gap vetosu). Bozulma DEĞİL, motorun kararıdır; eşleşme YAPISAL
    #       olarak oluşmaz ve OLUŞMAMALIDIR. `kapsam_disi` olarak ADIYLA raporlanır, hükmü GEÇERSİZ
    #       KILMAZ — yalnız eşleşen çift sayısını düşürür ve n_min kapısına havale edilir.
    # PAYDA eod_yok'u DIŞLAR (kartın "yalnız n'i düşürür" beyanının koddaki karşılığı): payda =
    # eşleşen + bozulma. eod_yok'u paydada tutmak ona kill#4'ü SEYRELTME etkisi verirdi — kart bunu
    # yasaklar (eod_yok'un TEK etkisi n'dir). Payda 0 ise bozulma da 0'dır (her şey eod_yok) → oran
    # 0, kill#4 tetiklenmez ve hüküm n_min'e gider. FAIL-CLOSED: kapsam dışı SINIF açıkça
    # `KAPSAM_DISI_SINIFLARI`dır; BURADA OLMAYAN her eşleşmeme BOZULMA sayılır.
    bozulma = [c for c in eslesmeyen if c["sinif"] not in KAPSAM_DISI_SINIFLARI]
    kapsam_disi = [c for c in eslesmeyen if c["sinif"] in KAPSAM_DISI_SINIFLARI]
    payda = n + len(bozulma)
    bozulma_orani = (len(bozulma) / payda) if payda else 0.0
    oran = len(eslesmeyen) / len(evren)   # RAPOR (kill DEĞİL): evrenin ne kadarı hiç eşleşMEdi

    # KART: "sessizce düşürülmez" — eşleşmeyen satır SAYISI ve ADI birlikte raporlanır.
    # KIRPMA BEYANLIDIR, SESSİZ DEĞİL: defter süresiz büyür ve bu sözlük /api/diagnostics yükünün
    # içine giriyor. `n` HER ZAMAN tamdır; kırpılan yalnız ad listesidir ve kaç adın kırpıldığı
    # `adlar_kirpildi` ile yazılır — "sessizce düşürülmez" kuralı sayının değil, GİZLEMENİN yasağıdır.
    olcum["eslesmeyen"] = {
        "n": len(eslesmeyen), "oran": round(oran, 4), "kill_esigi": KILL_ESLESMEME_ORANI,
        "adlar": [c["ad"] for c in eslesmeyen[:AD_TAVANI]],
        "adlar_kirpildi": max(0, len(eslesmeyen) - AD_TAVANI),
        "nedenler": [{"ad": c["ad"], "neden": c["neden"]} for c in eslesmeyen[:AD_TAVANI]],
        "sinif_dagilimi": {s: sum(1 for c in eslesmeyen if c["sinif"] == s)
                           for s in sorted({c["sinif"] for c in eslesmeyen})},
        # R1: kill#4'ü ateşleyen ALT-KÜME. Oran eod_yok'u DIŞLAYAN paydadan (eşleşen + bozulma)
        # gelir — bu, `oran` (evren paydalı, salt rapor) ile KARIŞTIRILMAMALIDIR.
        "bozulma": {
            "n": len(bozulma), "oran": round(bozulma_orani, 4), "payda": payda,
            "kill_esigi": KILL_ESLESMEME_ORANI,
            "adlar": [c["ad"] for c in bozulma[:AD_TAVANI]],
            "adlar_kirpildi": max(0, len(bozulma) - AD_TAVANI),
            "nedenler": [{"ad": c["ad"], "neden": c["neden"]} for c in bozulma[:AD_TAVANI]],
            "beyan": ("kill#4 PAYDASI = eşleşen + bozulma (eod_yok DIŞLANIR); oran > "
                      f"%{int(KILL_ESLESMEME_ORANI * 100)} → defter bütünlüğü sorunu, hüküm YOK"),
        },
        # R1: MEŞRU DOLMAMA — kill#4'ü GEÇERSİZ KILMAZ, yalnız n'i düşürür. ADIYLA raporlanır
        # (kart: "sessizce düşürülmez") ama BOZULMA sayılmaz.
        "kapsam_disi": {
            "n": len(kapsam_disi), "siniflar": list(KAPSAM_DISI_SINIFLARI),
            "adlar": [c["ad"] for c in kapsam_disi[:AD_TAVANI]],
            "adlar_kirpildi": max(0, len(kapsam_disi) - AD_TAVANI),
            "beyan": ("MEŞRU DOLMAMA (iç EOD motoru doldurmamayı SEÇTİ) — kill#4'ü GEÇERSİZ KILMAZ; "
                      "yalnız eşleşen çift sayısını düşürür ve n_min kapısına havale edilir"),
        },
    }
    olcum["n_eslesen"] = n
    olcum["ciftler"] = ciftler[-AD_TAVANI:]
    olcum["ciftler_kirpildi"] = max(0, n - AD_TAVANI)

    if bozulma_orani > KILL_ESLESMEME_ORANI:
        return {"gecer": False, "durum": "olculemedi", "esik": esik,
                "olcum": {**olcum, "ortalama_bps": None, "ci": None, "ortalama_R": None},
                "neden": (f"KILL#4 — BOZULMUŞ gölge satırı oranı %{bozulma_orani * 100:.1f} > "
                          f"%{KILL_ESLESMEME_ORANI * 100:.0f} ({len(bozulma)}/{payda} eşleşen+bozulma; "
                          f"{len(kapsam_disi)} eod_yok kapsam DIŞI): "
                          f"{', '.join(c['ad'] for c in bozulma[:5])}"
                          f"{' …' if len(bozulma) > 5 else ''}). Defter bütünlüğü sorunu: "
                          "ölçüm hükmü VERİLMEZ, önce eşleştirme kırılması KÖK-NEDEN turuna gider")}

    tarihler = [c["date"] for c in ciftler]
    ci_bps = tarih_kumeli_bootstrap([c["kazanc_bps"] for c in ciftler], tarihler)
    r_ciftler = [c for c in ciftler if c["kazanc_R"] is not None]
    ci_r = tarih_kumeli_bootstrap([c["kazanc_R"] for c in r_ciftler],
                                  [c["date"] for c in r_ciftler])

    def _yuvarla(ci: dict) -> dict:
        return {"ort": (None if ci["ort"] is None else round(ci["ort"], 4)),
                "alt": (None if ci["lo"] is None else round(ci["lo"], 4)),
                "ust": (None if ci["hi"] is None else round(ci["hi"], 4)),
                "n": ci["n"], "n_kume": ci["n_kume"], "B": ci["B"], "seviye": ci["seviye"],
                "sifiri_disliyor": ci["sifiri_disliyor"], "yontem": ci["yontem"],
                "kume_boylari": ci["kume_boylari"], "neden": ci["neden"]}

    ci_bps_y, ci_r_y = _yuvarla(ci_bps), _yuvarla(ci_r)
    olcum["ortalama_bps"] = ci_bps_y["ort"]
    olcum["ci"] = ci_bps_y
    olcum["ortalama_R"] = ci_r_y["ort"]
    olcum["ci_R"] = ci_r_y
    olcum["n_R_olculemeyen"] = n - len(r_ciftler)
    olcum["R_olculemeyen_adlar"] = [c["ad"] for c in ciftler if c["kazanc_R"] is None]
    olcum["gerceklik_capasi"] = gerceklik_capasi(ciftler)

    if n < N_MIN:
        return {"gecer": False, "durum": "olculdu", "esik": esik, "olcum": olcum,
                "neden": (f"ÖRNEKLEM YETERSİZ ({n}/{N_MIN}) — ölçüm KOŞTU, hüküm için asgari "
                          f"eşleşmiş çift sayısı dolmadı (kart {KART}: n_min={N_MIN}). Bu bir "
                          "başarısızlık değil ÖLÇÜLMÜŞ bir yetersizliktir ve zamanla kendiliğinden "
                          "dolar; kilit o zamana kadar FAIL-CLOSED kapalıdır")}

    alt, ust = olcum["ci"]["alt"], olcum["ci"]["ust"]
    if alt is None or ust is None:
        return {"gecer": False, "durum": "olculemedi", "esik": esik, "olcum": olcum,
                "neden": (f"n={n} yeterli ama CI KURULAMADI: {olcum['ci']['neden']}. "
                          "Aralıksız bir ortalama hüküm veremez — fail-closed")}
    if alt <= 0 <= ust:
        return {"gecer": False, "durum": "olculdu", "esik": esik, "olcum": olcum,
                "neden": (f"KILL#1 — n={n} ile %95 CI [{alt}, {ust}] bps SIFIRI İÇERİYOR: "
                          "dakika-hassas icranın ölçülebilir kazancı YOK. Faz-4b silahlanma bacağı "
                          "bu kanıtla GEREKÇELENDİRİLEMEZ")}
    if ust < 0:
        return {"gecer": False, "durum": "olculdu", "esik": esik, "olcum": olcum,
                "neden": (f"KILL#2 — n={n} ile %95 CI [{alt}, {ust}] bps TAMAMEN NEGATİF: "
                          "dakika-hassas icra EOD'den KÖTÜ. 4b bir maliyettir; faz merdiveni burada "
                          "DURUR ve 4b gölge kolu emekliliğe adaydır")}
    if alt <= band_bps:
        return {"gecer": False, "durum": "olculdu", "esik": esik, "olcum": olcum,
                "neden": (f"KILL#3 — CI pozitif [{alt}, {ust}] bps ama ALT SINIR E3 maliyet "
                          f"bandının ({band_bps} bps) ALTINDA: kazanç masrafı karşılamıyor, "
                          "'anlamlı ama işe yaramaz' olarak arşivlenir")}
    return {"gecer": True, "durum": "olculdu", "esik": esik, "olcum": olcum,
            "neden": None}
