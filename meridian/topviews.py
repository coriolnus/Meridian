"""topviews.py — TOP VIEWS TOPLULAŞTIRMASI: dokuz facet, iki beyanlı payda, TAM metrik.

NEYİ OKUR. `trades.jsonl` (kapanmış işlem defteri) ve `trade_plans.jsonl` (plan/kapı defteri).
HİÇBİR ŞEY YAZMAZ — ne state'e, ne elek defterine. Saf okuma; çağıranı `/api/topviews`.

ÖLÇÜLEN BOŞLUK (2026-08-24, pano ajanının raporu). Panonun "Top Views" yüzeyi üç facet ailesini
çiziyordu ama YARIM ölçüyordu:

  * `n` her facette vardı; `toplam R` ve `kazanma` yalnız bazılarında;
  * **`PF` hiçbir tam-defter facetinde ölçülemiyordu.** Sebep bir eksiklik değil bir BİLGİ KAYBI:
    `/api/plots` hücrede yalnız ORTALAMA R veriyor ve ortalama R'den brüt kâr / brüt zarar ayrımı
    GERİ ÇIKARILAMAZ (aynı ortalama, sonsuz farklı kâr/zarar ayrışmasından doğar). Pano bunu
    dürüstçe `ölçülemedi + neden` diye basıyordu — uydurma yoktu, ama yüzeyin değeri oradaydı.
  * Üç ayrı payda (tam defter · son 40 işlem · plots hücresi) tek kartta yan yana duruyordu ve
    her yüzeyde ayrı ayrı beyan edilmek zorundaydı.

BU MODÜLÜN SÖZLEŞMESİ:

  1. DEFTER BİR KEZ OKUNUR, DOKUZ BOYUTTA TOPLANIR. Yedi facet TEK paydayı (kapanmış işlem
     defterinin TAMAMI) paylaşır; yalnız iki KAPI faceti plan defterini sayar, çünkü bir kapı
     REDDİ kapanmış işlemde yaşamaz — reddedilen plan hiç işleme dönüşmez. İki payda AYRIDIR ve
     `facet_kaynaklari` bunu facet başına ADIYLA söyler ("ölçüm bağlamı tuzağı": aynı yüzeyde
     farklı paydaları tek sayı gibi göstermek, sistemin reddettiği tek şeydir).
  2. PF SONSUZ OLAMAZ. `gross_loss == 0` ⇒ `pf is None` + neden. `float('inf')` iki kez yanlıştır:
     matematiksel olarak payda ÖLÇÜLMEMİŞTİR (sıfır değil, tanımsız) ve JSON'da `Infinity` üretip
     katı ayrıştırıcıları düşürür.
  3. `n == 0` SATIR BASILMAZ (v197 koşulsuz emisyon tavanı) — ve `satirlar` ASLA `[]` DÖNMEZ.
     İki hâl vardır: dolu liste, ya da `None` + neden. Boş liste "ölçtük, hiç yok" ile
     "ölçemedik" arasındaki farkı siler.
  4. ETİKETSİZ SATIR SESSİZCE DÜŞMEZ. Bir facetin etiketini taşımayan satır o facetin sayımına
     GİRMEZ (bir "?" kovasına koymak, etiketlenmemişi etiketlenmiş gibi gösterirdi) ama
     `etiketsiz_n` ile facet düzeyinde RAPORLANIR.

KOVA SINIRLARI VERİYE BAKILARAK SEÇİLMEDİ (aşağıda, her sınırın yanında gerekçesiyle). Sınırı
dağılıma bakarak seçmek bir eşik uydurmasıdır; burada kullanılanlar sistemin KENDİ birimlerinden
(R = planlanan risk katı; bar = seans) ve yaygın takvim/işlem bölmelerinden gelir.
"""
from __future__ import annotations

import datetime as _dt
from typing import Callable

from . import ledgerstamp, store

LEDGER = "trades.jsonl"
PLANS = "trade_plans.jsonl"

# ---- KOVA SINIRLARI — ÖNCEDEN SABİT, HER SINIRIN YANINDA GEREKÇESİ ----------------------------
# R KOVASI. Sınırlar sistemin kendi ölçü biriminden gelir: 1R = plan kurulurken göze alınan risk.
#   −1R : TASARIM SINIRI. Tam stop, kurgu gereği −1,0R'dir; bunun ALTI "planlanan riskten FAZLA
#         kaybedildi" demektir (gap, kayma, stop atlaması) ve tamamen başka bir arıza sınıfıdır.
#      0 : başabaş. Kâr/zarar işaretinin döndüğü nokta — her PF/kazanma hesabının doğal ayracı.
#   1/2/3R: TAM SAYI R KATLARI. Defterin kendisi hedefi bu birimde yazıyor
#         (`r_multiple_expected` alanı 2,5R gibi değerler taşır), yani okur zaten bu ızgarada
#         düşünüyor. Üçten sonrası tek kuyruk kovasıdır: daha ince bölmek, az örnekli hücreleri
#         çoğaltmaktan başka bir şey yapmaz.
R_KOVALARI: tuple[tuple[str, float | None, float | None], ...] = (
    ("<-1R",  None, -1.0),
    ("-1..0R", -1.0, 0.0),
    ("0..1R",   0.0, 1.0),
    ("1..2R",   1.0, 2.0),
    ("2..3R",   2.0, 3.0),
    (">=3R",    3.0, None),
)

# TUTMA KOVASI (`bars_held` = kapanışa kadar geçen SEANS sayısı). İkiye katlayan merdiven;
# sınırlar takvimden, dağılımdan DEĞİL:
#   0g   : aynı seans kapandı — bu bir tutuş değil, bir gap/aynı-gün mekanizmasıdır; 1g ile aynı
#          kovaya koymak iki farklı çıkış mekanizmasını tek satırda eritirdi.
#   1g   : bir sonraki seans.
#   2-3g : haftanın ilk yarısı ölçeği.
#   4-7g : BİR İŞLEM HAFTASI (5 seans) + payı.
#   8-15g: iki-üç işlem haftası.
#   16g+ : tek kuyruk kovası.
# BİLEREK `analytics.ALFA_TUTUS_DILIMLERI` ile AYNI merdiven — ama KOPYA, import DEĞİL: o sabit
# alfa/beta hücre boyutlandırması için var ve orada değişirse bu YÜZEYİN kovaları sessizce
# kaymamalı (facet sınırı bir yayın sözleşmesidir; bir başka modülün ayarı değil).
TUTMA_KOVALARI: tuple[tuple[str, int, int | None], ...] = (
    ("0g", 0, 0), ("1g", 1, 1), ("2-3g", 2, 3), ("4-7g", 4, 7), ("8-15g", 8, 15),
    ("16g+", 16, None),
)

# ---- FACET ADLARI VE AİLELERİ -----------------------------------------------------------------
AILELER: dict[str, tuple[str, ...]] = {
    "KAYNAK": ("kurulum", "rejim", "sektor"),
    "SONUC": ("cikis_nedeni", "tutma_kovasi", "r_kovasi"),
    "KAPI": ("kapi_reddi", "kapi_hukmu", "kaynak"),
}
FACETLER: tuple[str, ...] = tuple(ad for f in AILELER.values() for ad in f)

# ---- ÖLÇÜLEMEDİ NEDENLERİ (YASA 4: ≥20 karakter, ADIYLA) --------------------------------------
PF_YOK_R_YOK = ("bu kırılımdaki hiçbir satır r_multiple taşımıyor — brüt kâr/zarar ölçülemedi "
                "(sıfır DEĞİL: ölçülmedi)")
PF_YOK_ZARAR_YOK = "zarar eden işlem yok — PF tanımsız (bölme yok), sonsuz DEĞİL"
PF_YOK_ZARAR_SIFIR = ("zarar eden işlemlerin R toplamı tam sıfır — PF tanımsız (bölme yok), "
                      "sonsuz DEĞİL")


def _sayi(v) -> float | None:
    """Ham değerden sonlu float; çıkaramazsan None. `inf`/`nan` DEFTERDEN de gelebilir ve buradan
    içeri girerse tüm toplamı zehirler — sonlu olmayan değer ÖLÇÜLMEMİŞ sayılır."""
    try:
        f = float(v)
    except (TypeError, ValueError):  # sessiz-yutma: kayıp SESSİZ DEĞİL — çevrilemeyen değer o facetin `etiketsiz_n` sayacına düşer ve nedeni `etiketsiz_neden` ile yükte adıyla yazar; istisna metnini burada saklamak, yükün zaten taşıdığı bilgiyi ikinci bir kanala kopyalardı
        return None
    return f if f == f and f not in (float("inf"), float("-inf")) else None


def _yuvarla(x: float | None, basamak: int = 6) -> float | None:
    """Kayan-nokta kuyruğunu keser. 6 basamak BİLEREK: 3 basamak `2/3` gibi oranları testin
    `approx` toleransının dışına iter, yani ölçümün kendisini bozardı."""
    return None if x is None else round(x, basamak)


def _r_kovasi(v) -> str | None:
    r = _sayi(v)
    if r is None:
        return None
    for ad, lo, hi in R_KOVALARI:
        if (lo is None or r >= lo) and (hi is None or r < hi):
            return ad
    return None                                     # ulaşılamaz (kovalar tam kaplar) — savunma


def _tutma_kovasi(v) -> str | None:
    try:
        b = int(v)
    except (TypeError, ValueError):  # sessiz-yutma: `bars_held` okunamayan satır bir kovaya DÜŞÜRÜLMEZ (ölçülmemiş tutuşu "1g" göstermek uydurma olurdu) — `tutma_kovasi` facetinin `etiketsiz_n` sayacına girer ve nedeni yükte yazar
        return None
    for ad, lo, hi in TUTMA_KOVALARI:
        if b >= lo and (hi is None or b <= hi):
            return ad
    return None                                     # negatif bar sayısı — etiketsiz, uydurma yok


# =================================================================================================
# TOPLAYICI — tek jenerik hücre hesabı; dokuz facet ondan doğar
# =================================================================================================
def _bos_kova(deger: str) -> dict:
    return {"deger": deger, "n": 0, "r_n": 0, "wins": 0, "loss_n": 0,
            "_sum_r": 0.0, "_gw": 0.0, "_gl": 0.0}


def _kapat(k: dict) -> dict:
    """Ham sayaçları YAYIN satırına çevirir. R taşımayan hücrede toplamlar `0.0` DEĞİL `None`:
    boş kümenin toplamı matematikte sıfırdır ama DEFTERDE ölçülmemiştir ve `0.0` "başabaş
    kapandı" diye okunur."""
    r_n = k["r_n"]
    if r_n == 0:
        return {"deger": k["deger"], "n": k["n"], "r_n": 0,
                "sum_r": None, "gross_win": None, "gross_loss": None, "wins": 0,
                "pf": None, "kazanma": None, "pf_yok_nedeni": PF_YOK_R_YOK}
    gw, gl = k["_gw"], k["_gl"]
    if gl == 0.0:
        pf, neden = None, (PF_YOK_ZARAR_YOK if k["loss_n"] == 0 else PF_YOK_ZARAR_SIFIR)
    else:
        pf, neden = _yuvarla(gw / abs(gl)), None
    return {"deger": k["deger"], "n": k["n"], "r_n": r_n,
            "sum_r": _yuvarla(k["_sum_r"]), "gross_win": _yuvarla(gw),
            "gross_loss": _yuvarla(gl), "wins": k["wins"],
            "pf": pf, "kazanma": _yuvarla(k["wins"] / r_n), "pf_yok_nedeni": neden}


def _topla(satirlar: list[dict], etiketle: Callable[[dict], object],
           r_getir: Callable[[dict], list[float | None]]) -> tuple[list[dict], int, int]:
    """`(kovalar, etiketsiz_n, etiketi_bos_n)`.

    `etiketle` üç şey döndürebilir:
      * `None`            → ETİKETSİZ (ölçülemedi). Satır hiçbir kovaya girmez, `etiketsiz_n`e yazılır.
      * dize              → tek etiket.
      * liste             → ÇOK ETİKETLİ facet (bir plan birden çok kapı ölçütünde takılabilir).
                            Boş liste GEÇERLİ bir cevaptır ("hiçbirinde takılmadı") ve
                            `etiketi_bos_n`e yazılır — etiketsizlikle KARIŞTIRILMAZ.
    """
    kovalar: dict[str, dict] = {}
    etiketsiz = bos = 0
    for satir in satirlar:
        et = etiketle(satir)
        if et is None:
            etiketsiz += 1
            continue
        adlar = [str(x) for x in (et if isinstance(et, list) else [et]) if x not in (None, "")]
        if not adlar:
            if isinstance(et, list):
                bos += 1                            # ölçüldü, sonuç boş
            else:
                etiketsiz += 1                      # boş dize = etiket YOK
            continue
        rlar = r_getir(satir)
        for ad in adlar:
            k = kovalar.get(ad) or kovalar.setdefault(ad, _bos_kova(ad))
            k["n"] += 1
            for ham in rlar:
                r = _sayi(ham)
                if r is None:
                    continue
                k["r_n"] += 1
                k["_sum_r"] += r
                if r > 0:
                    k["wins"] += 1
                    k["_gw"] += r
                else:
                    k["loss_n"] += 1
                    k["_gl"] += r
    # SIRALAMA `n` AZALAN: pano kartı ilk satırları gösterir, en kalabalık kırılım üstte olmalı.
    # Eşitlikte ada göre — aynı defter iki koşumda aynı sırayı verir (deterministik yayın).
    hucreler = sorted((_kapat(k) for k in kovalar.values()), key=lambda c: (-c["n"], c["deger"]))
    return hucreler, etiketsiz, bos


def _pencere(satirlar: list[dict], alan: str, etiket: str) -> str:
    tarihler = sorted(str(s.get(alan))[:10] for s in satirlar if s.get(alan))
    if not tarihler:
        return f"ölçülemedi — taranan satırların hiçbiri `{alan}` taşımıyor"
    return f"{tarihler[0]} → {tarihler[-1]} ({etiket})"


# =================================================================================================
# FACET TANIMLARI
# =================================================================================================
_ISLEM_KAYNAK = f"{LEDGER} — kapanmış işlem defterinin TAMAMI"
_PLAN_KAYNAK = f"{PLANS} — plan/kapı defterinin TAMAMI"
_SEKTOR_KAYNAK = (f"{LEDGER} (payda: kapanmış işlem) × {PLANS} (sektör etiketi, `plan_id` "
                  f"birleştirmesi)")

_ISLEM_PAYDA = "payda = kapanmış işlem defterinin TAMAMI (kırpma yok, son-N penceresi yok)"
_PLAN_PAYDA = ("payda = plan defterinin TAMAMI. Bir PLAN sonuç taşımak ZORUNDA DEĞİLDİR: "
               "reddedilen plan hiç işleme dönüşmez, o yüzden `n` (plan) ile `r_n` (o planlardan "
               "doğmuş kapanmış işlem) AYRI sayılır")


def _etiketsiz_neden(facet: str) -> str:
    return {
        "kurulum": "işlem satırında `setup` alanı yok ya da boş",
        "rejim": "işlem satırında `regime` alanı yok ya da boş",
        "sektor": (f"işlemin `plan_id`si {PLANS}'de bulunamadı ya da plan `sector` taşımıyor "
                   f"(sektör alanı KAPANMIŞ İŞLEM defterinde YOKTUR)"),
        "cikis_nedeni": "işlem satırında `exit_reason` alanı yok ya da boş",
        "tutma_kovasi": "işlem satırında `bars_held` yok ya da sayıya çevrilemedi",
        "r_kovasi": "işlem satırında `r_multiple` yok ya da sayıya çevrilemedi",
        "kapi_reddi": "plan satırında yapısal `gate_checks` dizisi yok (hangi ölçütte takıldığı YAZILMAMIŞ)",
        "kapi_hukmu": "plan satırında `gate_verdict` alanı yok ya da boş",
        "kaynak": "ulaşılamaz — `ledgerstamp.kaynak_of` her satıra üç damgadan birini verir",
    }[facet]


def _tum_etiketsiz_neden(facet: str, n: int) -> str:
    ozel = {
        "kapi_reddi": (f"taranan {n} planın HİÇBİRİ yapısal `gate_checks` dizisi taşımıyor — hangi "
                       f"ölçütte takıldıkları YAZILMAMIŞ. Bu 'reddedilen plan yok' DEĞİLDİR."),
        "sektor": (f"taranan {n} kapanmış işlemin hiçbiri {PLANS}'de sektör etiketli bir plana "
                   f"bağlanamadı — sektör kırılımı bu turda ölçülemedi"),
    }
    return ozel.get(facet, f"taranan {n} satırın hiçbiri bu facetin etiketini taşımıyor "
                           f"({_etiketsiz_neden(facet)}) — kırılım bu turda ölçülemedi")


def _defter_bos_neden(facet: str, defter: str) -> str:
    return (f"{defter} boş ya da okunamadı — `{facet}` bu turda ölçülemedi; "
            f"'böyle bir kırılım yok' DEĞİL")


def _facet(facet: str, satirlar: list[dict], defter: str, etiketle, r_getir, *,
           cok_etiketli: bool = False, ek_ad: str | None = None) -> dict:
    """Tek facetin yayın bloğu. ÜÇ HÂL DEĞİL İKİ HÂL: dolu liste, ya da `None` + neden."""
    if not satirlar:
        return {"satirlar": None, "olculemedi_neden": _defter_bos_neden(facet, defter),
                "etiketsiz_n": 0, "etiketsiz_neden": _etiketsiz_neden(facet),
                "cok_etiketli": cok_etiketli, "ek": {}}
    hucreler, etiketsiz, bos = _topla(satirlar, etiketle, r_getir)
    ek = {ek_ad: bos} if ek_ad else {}
    if not hucreler:
        # ÖLÇÜM YAPILDI AMA SONUÇ BOŞ ile ÖLÇÜLEMEDİ ayrımı NEDENİN METNİNDE yaşar; ikisi de
        # `satirlar: None`dır çünkü `[]` yayınlamak panoda "boş kart" olarak çizilir ve okur
        # farkı göremez.
        neden = (f"ölçüm YAPILDI, sonuç boş: taranan {len(satirlar)} planın hepsi her kapı "
                 f"ölçütünden geçti — basılacak ret satırı yok"
                 if (cok_etiketli and bos == len(satirlar))
                 else _tum_etiketsiz_neden(facet, len(satirlar)))
        return {"satirlar": None, "olculemedi_neden": neden, "etiketsiz_n": etiketsiz,
                "etiketsiz_neden": _etiketsiz_neden(facet), "cok_etiketli": cok_etiketli, "ek": ek}
    return {"satirlar": hucreler, "olculemedi_neden": None, "etiketsiz_n": etiketsiz,
            "etiketsiz_neden": _etiketsiz_neden(facet), "cok_etiketli": cok_etiketli, "ek": ek}


# =================================================================================================
# YÜK
# =================================================================================================
def topviews() -> dict:
    """`/api/topviews` yükü. Saf okuma; iki defteri BİRER KEZ okur ve dokuz boyutta toplar."""
    islemler = store.read_jsonl(LEDGER)
    planlar = store.read_jsonl(PLANS)

    # PLAN → İŞLEM BİRLEŞTİRMESİ tek yerde kurulur ve İKİ YÖNDE de kullanılır: işlem faceti
    # sektörünü plandan alır, plan faceti sonucunu işlemden. Bir plan birden çok işlem doğurmuş
    # olabilir (kısmi çıkış/yeniden giriş) — LİSTE tutulur, `dict` ikinciyi sessizce yutardı.
    plan_by_id = {str(p.get("id")): p for p in planlar if p.get("id")}
    islem_by_plan: dict[str, list[dict]] = {}
    for t in islemler:
        pid = t.get("plan_id")
        if pid:
            islem_by_plan.setdefault(str(pid), []).append(t)

    def _islem_r(t: dict) -> list[float | None]:
        return [t.get("r_multiple")]

    def _plan_r(p: dict) -> list[float | None]:
        return [t.get("r_multiple") for t in islem_by_plan.get(str(p.get("id")), [])]

    def _sektor_et(t: dict):
        return (plan_by_id.get(str(t.get("plan_id") or "")) or {}).get("sector") or None

    def _reddi_et(p: dict):
        cks = p.get("gate_checks")
        if not isinstance(cks, list) or not cks:
            return None                             # yapısal iz YOK → etiketsiz, "ret yok" DEĞİL
        return [c.get("check") for c in cks
                if isinstance(c, dict) and c.get("passed") is False]

    islem_facet = {
        "kurulum": (lambda t: t.get("setup") or None),
        "rejim": (lambda t: t.get("regime") or None),
        "sektor": _sektor_et,
        "cikis_nedeni": (lambda t: t.get("exit_reason") or None),
        "tutma_kovasi": (lambda t: _tutma_kovasi(t.get("bars_held"))),
        "r_kovasi": (lambda t: _r_kovasi(t.get("r_multiple"))),
        "kaynak": ledgerstamp.kaynak_of,
    }
    bloklar: dict[str, dict] = {
        ad: _facet(ad, islemler, LEDGER, fn, _islem_r) for ad, fn in islem_facet.items()
    }
    bloklar["kapi_reddi"] = _facet("kapi_reddi", planlar, PLANS, _reddi_et, _plan_r,
                                   cok_etiketli=True,
                                   ek_ad="hicbir_olcutte_takilmayan_plan_n")
    bloklar["kapi_hukmu"] = _facet("kapi_hukmu", planlar, PLANS,
                                   lambda p: p.get("gate_verdict") or None, _plan_r)

    islem_pencere = _pencere(islemler, "ts_close", "ts_close")
    plan_pencere = _pencere(planlar, "date", "plan date")
    kaynaklar = {}
    for ad in FACETLER:
        plan_tabanli = ad in ("kapi_reddi", "kapi_hukmu")
        kaynaklar[ad] = {
            "kaynak": (_PLAN_KAYNAK if plan_tabanli
                       else (_SEKTOR_KAYNAK if ad == "sektor" else _ISLEM_KAYNAK)),
            "pencere": plan_pencere if plan_tabanli else islem_pencere,
            "n": len(planlar) if plan_tabanli else len(islemler),
            "payda": _PLAN_PAYDA if plan_tabanli else _ISLEM_PAYDA,
        }
    # ÇOK ETİKETLİ FACETİN PAYDASI AYRI CÜMLE İSTER: `n` toplamı plan sayısını AŞAR ve bunu
    # söylemeyen bir yüzey, okuru "390 planın 217'si" diye yanlış okumaya iter.
    kaynaklar["kapi_reddi"]["payda"] += (". ÇOK ETİKETLİ: bir plan birden çok ölçütte takılabilir, "
                                         "satırların `n` toplamı plan sayısını AŞAR")
    # R KOVASINDA PF BİR TAUTOLOJİDİR, BULGU DEĞİL. Kova zaten R'nin İŞARETİNE göre bölünür:
    # pozitif kovada brüt zarar YAPISAL OLARAK sıfırdır (PF hep `None`), negatif kovada brüt kâr
    # yapısal olarak sıfırdır (PF hep 0,0). Bunu söylemeyen bir yüzeyde okur `1..2R: PF ölçülemedi`
    # satırını stratejiye dair bir bilgi sanır — oysa kovanın TANIMININ yeniden okunuşudur.
    kaynaklar["r_kovasi"]["payda"] += (". PF BU FACETTE TAUTOLOJİKTİR: kova R'nin işaretine göre "
                                       "bölündüğü için pozitif kovada brüt zarar, negatif kovada "
                                       "brüt kâr YAPISAL olarak sıfırdır — buradaki PF bir bulgu "
                                       "değil kova tanımının yeniden okunuşudur")

    return {
        "as_of": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        "kaynak_defter": f"{LEDGER} (kapanmış işlem) + {PLANS} (plan/kapı)",
        "toplam_islem": len(islemler),
        "toplam_plan": len(planlar),
        "kapsam": (f"Dokuz facetin YEDİSİ tek paydayı sayar: kapanmış işlem defterinin TAMAMI "
                   f"({len(islemler)} satır, kırpma yok). İki KAPI faceti (kapı reddi, kapı hükmü) "
                   f"plan defterini sayar ({len(planlar)} plan) çünkü bir kapı reddi kapanmış "
                   f"işlemde YAŞAMAZ — reddedilen plan hiç işleme dönüşmez. Her facetin kendi "
                   f"kaynağı, penceresi ve paydası `facet_kaynaklari`ndadır."),
        "aileler": {aile: {ad: bloklar[ad] for ad in adlar} for aile, adlar in AILELER.items()},
        "facet_kaynaklari": kaynaklar,
    }
