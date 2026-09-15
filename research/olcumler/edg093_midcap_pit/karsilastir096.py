"""EDG-2026-096 · ÜÇ ÜYELİK KİPİNİN KARŞILAŞTIRMASI — kart eşikleri, PK kapısı, kill-list tetiği.

Kart: research/cards/EDG-2026-096-edg016-katman-ii-sagkalan-yanliligi.yaml (`esikler`,
`kill_list`, `pozitif_kontrol`). KART DIŞINA ÖLÇÜM YOK; KARTA DOKUNULMAZ (yalnız OKUNUR); eşik
sonradan DEĞİŞMEZ. HÜKÜM YOK — `hukum` alanı sabit "YOK — Rol-1" (CLAUDE.md §3, §5).

NE YAPAR. EDG-093 ölçüm betiğinin (`k093.py`) ÜÇ ayrı koşumunun sonuç JSON'larını okur:
    A `asof`   — as-of PIT kohortu (EDG-093 PK-1'in TEKRARI),
    B `guncel` — defterin SON satırındaki küme bütün pencereye geriye uygulanmış,
    C `sabit`  — EDG-016'nın sabit evren listesi her güne uygulanmış,
ve bunları (a) kip × bacak × ufuk tablosuna, (b) KARTIN eşiklerine, (c) A ≡ PK-1 kapısına,
(d) KARTIN kill-list kalemlerine bağlar. HÜKÜM VERMEZ: Rol-1 kartı ve K defterini aynı turda
bu çıktıdan işler.

EŞİKLER KARTTAN OKUNUR, BURAYA GÖMÜLMEZ (tek-kaynak yasası, CLAUDE.md §4). Aynı kural kill-list
METİNLERİ için de geçerlidir: tetiklenen kalem kartın KENDİ CÜMLESİYLE yazılır; burada yalnız
"hangi cümle hangi ölçüme bağlı" eşlemesi durur ve eşleşmeyen kalem ADIYLA sayılır (kart
değişirse sessizce kaybolmasın diye).

BU BETİK ÖLÇMEZ, OKUR. Bar/panel/CI hesabı `k093.py`nindir; burada tek bir sayı yeniden
hesaplanmaz — yeniden hesaplansaydı iki kopya sessizce ayrışırdı. Ölçülemeyen her değer `None`
ve NEDENİYLE durur (uydurma yasağı: sıfır ile "bilmiyorum" aynı şey değildir).

`meridian` İTHAL EDİLMEZ (yalnız stdlib + yaml): ithal etmek canlı yapılandırmayı ve `obs`
yolunu bir ölçüm aracına bağlardı — pytest dışı koşum canlı deftere YAZAR (CLAUDE.md §2).
AĞA ÇIKILMAZ. Alt süreç YOKTUR. Bekleme döngüsü YOKTUR.

KOMUT SATIRI (sözleşme burasıdır, ana akış değil — CLAUDE.md §1):
    cd <depo kökü> && .venv/bin/python research/olcumler/edg093_midcap_pit/karsilastir096.py \\
        --asof <sonuc_093_<damga>.json> --guncel <sonuc_093_guncel_<damga>.json> \\
        --sabit <sonuc_093_sabit_<damga>.json> --pk1-referans <EDG-093 sonuc_093_*.json> \\
        --kart <EDG-2026-096 yaml> --cikti <dizin>
`--guncel`/`--sabit`/`--pk1-referans` ZORUNLU DEĞİLDİR: verilmeyen kip "ölçülemedi"dir ve o
eşiğin hükmü `None` kalır — eksik girdiyi "geçti" saymak, eşiği hak etmeden geçme yönünde yanlı
olurdu (CLAUDE.md §5, EXE-2026-006 dersi).
Çıkış kodu: 0 = sonuç yazıldı · 2 = kullanım hatası (eksik/bozuk girdi).

YAZIM — TEK YER `--cikti` (Yasa 6, okuyanı):
  * `<cikti>/sonuc_096_<damga>.json` → okuyan: Rol-1 (hüküm + K defteri).
  * `<cikti>/RAPOR_096_<damga>.md`   → okuyan: Rol-1 / operatör masası.

MODÜL DÜZEYİ TEMİZDİR: argparse ana akışın içinde kurulur, G/Ç yoktur — ithal etmek bir koşum
TETİKLEMEZ (çiviler bu yüzden fonksiyonları doğrudan çağırabilir).
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import pathlib
import sys

import yaml

KART_ID = "EDG-2026-096"
HUKUM = "YOK — Rol-1"

#: Karşılaştırılan kipler — SIRA ANLAMLIDIR (A referans, B ve C sınanan).
KIPLER = ("asof", "guncel", "sabit")

#: Kartın bacakları ve her bacağın DEĞER ALANI. `ii_b` bir korelasyondur (`ic`), diğerleri
#: getiri farkıdır (`ort`) — tek bir alan adı varsaymak sessizce None üretirdi.
BACAKLAR = (("i_ust20_kohort_fazlasi", "ort"),
            ("ii_a1_kova_tabanli_fazla", "ort"),
            ("ii_b_artik_ic_fazla", "ic"))
UFUKLAR = ("10", "20")

#: EDG-093 çıktısında koşum anahtarı belirsiz-isim kipidir; BİRİNCİL olan `dahil`dir.
BIRINCIL_KOSUM = "dahil"

#: KILL-LIST EŞLEMESİ — METİN DEĞİL ANAHTAR. Sol taraf bu betiğin ölçtüğü kapı, sağ taraf kart
#: cümlesinde ARANAN belirteç. Cümlenin KENDİSİ karttan gelir (kopya metin YOK); belirteç yalnız
#: "hangi cümle hangi kapıya bağlı" sorusunu çözer. Eşleşmeyen kart kalemi ADIYLA sayılır —
#: kart değişirse eşleme sessizce kaybolmasın.
KILL_ESLEME = (
    ("a_kipi_pk1", "A kipi PK-1"),
    ("katman_i_pk", "katman i PK"),
    ("b_ve_c_ci0_ici", "B VE C"),
    ("sabit_olculemeyen", "ölçülemeyen payı"),
    ("asof_regresyonu", "as-of kipi çıktısı"),
)


# =================================================================================================
# 0. KULLANIM HATASI / KÜÇÜK YARDIMCILAR
# =================================================================================================
def kullanim_hatasi(mesaj: str) -> None:
    """Kullanım hatası = çıkış 2 (argparse ile AYNI kod); neden stderr'e ADIYLA yazılır."""
    print(f"KULLANIM HATASI: {mesaj}", file=sys.stderr)
    raise SystemExit(2)


def damga_uret() -> str:
    """UTC damgası — saat TAHMİNLE değil saatten okunur (hafıza: saat-etiketi ölçülür)."""
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _sha256(p: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for blok in iter(lambda: f.read(1 << 20), b""):
            h.update(blok)
    return h.hexdigest()


def damgala(yol) -> dict:
    """(yol, sha256, neden) — dosya yoksa sha UYDURULMAZ, neden ADIYLA döner."""
    if yol is None:
        return {"yol": None, "sha256": None, "neden": "yol verilmedi"}
    p = pathlib.Path(yol)
    if not p.exists():
        return {"yol": str(p), "sha256": None, "neden": f"dosya yok: {p}"}
    return {"yol": str(p), "sha256": _sha256(p), "neden": None}


# =================================================================================================
# 1. GİRDİ OKUMA — kip sonuçları ve PK-1 referansı
# =================================================================================================
def kip_oku(yol, beklenen_kip: str) -> dict:
    """Bir kip koşumunun sonuç JSON'unu okur ve ETİKETİNİ DOĞRULAR.

    KİP UYUŞMASI ZORUNLUDUR: `--guncel`e as-of çıktısı verilirse tablo sessizce AYNI sayıyı iki
    kez gösterir ve hipotez kendi kendini "doğrular". Uyuşmazlık bir okuma hatasıdır — dosya
    KULLANILMAZ ve neden ADIYLA durur (uydurma yasağı)."""
    bos = {"okundu": False, "yol": None if yol is None else str(yol), "beklenen_kip": beklenen_kip,
           "bulunan_kip": None, "damga": None, "DURUM": None, "kosum_anahtari": None,
           "bacaklar": None, "sabit_liste_kunyesi": None, "neden": None}
    if yol is None:
        bos["neden"] = f"--{beklenen_kip} verilmedi — bu kip ÖLÇÜLEMEDİ (sayı UYDURULMAZ)"
        return bos
    p = pathlib.Path(yol)
    try:
        ham = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        # sessiz-yutma DEĞİL: sonuç okunamadı — kip ÖLÇÜLEMEDİ sayılır ve neden ADIYLA durur
        bos["neden"] = f"sonuç json okunamadı ({type(e).__name__}: {e}): {p}"
        return bos
    bulunan = ham.get("uyelik_kipi")
    bos["bulunan_kip"] = bulunan
    bos["damga"] = ham.get("damga_utc")
    bos["DURUM"] = ham.get("DURUM")
    if bulunan != beklenen_kip:
        bos["neden"] = (f"kip ETİKETİ uyuşmuyor: dosya `{bulunan}` diyor, bayrak "
                        f"`{beklenen_kip}` — yanlış eşlenmiş çıktı KULLANILMAZ")
        return bos
    kosumlar = ham.get("kosumlar") or {}
    anahtar = BIRINCIL_KOSUM if BIRINCIL_KOSUM in kosumlar else (
        sorted(kosumlar)[0] if kosumlar else None)
    if anahtar is None:
        bos["neden"] = f"sonuçta koşum YOK: {p}"
        return bos
    kosum = kosumlar[anahtar] or {}
    bos["kosum_anahtari"] = anahtar
    if kosum.get("DURUM") != "OLCULDU" or not kosum.get("bacaklar"):
        bos["neden"] = (f"koşum `{anahtar}` ÖLÇÜLEMEDİ: {kosum.get('neden') or 'bacak yok'}")
        return bos
    bos["okundu"] = True
    bos["bacaklar"] = kosum["bacaklar"]
    bos["sabit_liste_kunyesi"] = ham.get("sabit_liste_kunyesi")
    return bos


def pk1_detayi_oku(yol) -> dict:
    """EDG-093 sonucunun PK-1 detay bloğu — A kipinin karşılaştırıldığı ALTI bacak.

    Detay satırı `pk1_deger` alanını taşır; o sayı EDG-093 turunda AYNI kodun large-cap as-of
    kohortunda ürettiği değerdir. A kipi onu birebir yeniden üretmeliydi (kart PK (2))."""
    out = {"okundu": False, "yol": None if yol is None else str(yol), "damga": None,
           "detay": [], "neden": None}
    if yol is None:
        out["neden"] = "--pk1-referans verilmedi — A ≡ PK-1 kapısı ÖLÇÜLEMEDİ"
        return out
    p = pathlib.Path(yol)
    try:
        ham = json.loads(p.read_text(encoding="utf-8"))
        detay = ((ham.get("pk") or {}).get("pk1") or {}).get("detay") or []
    except (OSError, ValueError, AttributeError) as e:
        # sessiz-yutma DEĞİL: referans okunamadı — kapı ÖLÇÜLEMEDİ, kıyas UYDURULMAZ
        out["neden"] = f"PK-1 referansı okunamadı ({type(e).__name__}: {e}): {p}"
        return out
    if not detay:
        out["neden"] = f"PK-1 detay bloğu BOŞ (pk.pk1.detay): {p}"
        return out
    out["okundu"] = True
    out["damga"] = ham.get("damga_utc")
    out["detay"] = detay
    return out


def kart_oku(yol) -> dict:
    """Kart YAML'i — `esikler` ve `kill_list` BURADAN gelir, koda GÖMÜLMEZ."""
    p = pathlib.Path(yol)
    try:
        kart = yaml.safe_load(p.read_text(encoding="utf-8"))
    except (OSError, ValueError, yaml.YAMLError) as e:
        # sessiz-yutma DEĞİL: kart okunamazsa eşik UYDURULMAZ — koşum durur
        kullanim_hatasi(f"kart okunamadı ({type(e).__name__}: {e}): {p}")
    if not isinstance(kart, dict) or not isinstance(kart.get("esikler"), dict):
        kullanim_hatasi(f"kartta `esikler` bloğu yok ya da sözlük değil: {p}")
    if not isinstance(kart.get("kill_list"), list):
        kullanim_hatasi(f"kartta `kill_list` listesi yok: {p}")
    return kart


# =================================================================================================
# 2. TABLO — kip × bacak × ufuk
# =================================================================================================
def _bacak_degeri(kip_kaydi: dict, bacak: str, alan: str, ufuk: str) -> dict:
    """Tek hücre: değer + CI + CI-0-dışılık. Okunamayan hücre None + NEDENdir."""
    if not kip_kaydi.get("okundu"):
        return {"deger": None, "ci": None, "ci0_disi": None, "neden": kip_kaydi.get("neden")}
    b = ((kip_kaydi["bacaklar"].get(bacak) or {}).get(ufuk)) or {}
    return {"deger": b.get(alan), "ci": b.get("ci"), "ci0_disi": b.get("anlamli"),
            "pozitif_anlamli": b.get("pozitif_anlamli"), "n": b.get("n"),
            "neden": None if b else f"bacak yok: {bacak}@{ufuk}"}


def tablo_kur(kipler: dict) -> list[dict]:
    """kip × bacak × ufuk tablosu — Rol-1 hükmü BU tablodan okunur (Yasa 6 okuyanı)."""
    satirlar = []
    for kip in KIPLER:
        for bacak, alan in BACAKLAR:
            for ufuk in UFUKLAR:
                h = _bacak_degeri(kipler[kip], bacak, alan, ufuk)
                satirlar.append({"kip": kip, "bacak": bacak, "deger_alani": alan, "ufuk": ufuk,
                                 **h})
    return satirlar


# =================================================================================================
# 3. KAPI — A kipi ≡ EDG-093 PK-1 (altı bacak, kart toleransı)
# =================================================================================================
def a_kipi_pk1_kapisi(asof: dict, pk1: dict, tol: float) -> dict:
    """A kipi PK-1'in ALTI bacağını (3 bacak × 2 ufuk) TOLERANS İÇİNDE yeniden üretmeli.

    Bu kapı kartın PK (2)'sidir ve aynı zamanda İKİ kill-list kaleminin ölçümüdür ("A kipi PK-1
    ile eşit değilse → kod yolu bozuk" ve "as-of kipi çıktısı EDG-093 sonucundan ayrışırsa →
    regresyon"): bu koşumda EDG-093 referansı PK-1 detayının ta kendisidir, yani iki cümle TEK
    ölçüme bakar — bu bir kopya değil, yazılı bir eşleştirmedir."""
    out = {"tolerans": tol, "kiyaslanan_bacak_n": 0, "maks_mutlak_fark": None, "gecti": None,
           "detay": [], "neden": None,
           "tanim": "A kipi (as-of) EDG-093 PK-1 detayının ALTI bacağını tolerans içinde "
                    "yeniden üretmeli — kod yolunun bozulmadığının kanıtı"}
    if not asof.get("okundu"):
        out["neden"] = f"A kipi okunamadı: {asof.get('neden')}"
        return out
    if not pk1.get("okundu"):
        out["neden"] = pk1.get("neden")
        return out
    ref = {(str(r.get("bacak")), str(r.get("ufuk"))): r.get("pk1_deger") for r in pk1["detay"]}
    farklar = []
    for bacak, alan in BACAKLAR:
        for ufuk in UFUKLAR:
            a = ((asof["bacaklar"].get(bacak) or {}).get(ufuk) or {}).get(alan)
            r = ref.get((bacak, ufuk))
            fark = None if (a is None or r is None) else abs(float(a) - float(r))
            if fark is not None:
                farklar.append(fark)
            out["detay"].append({
                "bacak": bacak, "ufuk": ufuk, "a_kipi_deger": a, "pk1_deger": r,
                "mutlak_fark": fark, "gecti": None if fark is None else bool(fark <= tol),
                "neden": None if fark is not None else "değer ÖLÇÜLEMEDİ — kıyas yapılamadı"})
    out["kiyaslanan_bacak_n"] = len(out["detay"])
    if not farklar:
        out["neden"] = "hiçbir bacak kıyaslanamadı — kapı ÖLÇÜLEMEDİ"
        return out
    out["maks_mutlak_fark"] = max(farklar)
    out["olculen_bacak_n"] = len(farklar)
    out["gecti"] = bool(max(farklar) <= tol and len(farklar) == len(out["detay"]))
    return out


# =================================================================================================
# 4. EŞİKLER — DEĞERLER KARTTAN, HÜKÜM YOK
# =================================================================================================
def _ii_b_esigi(kipler: dict, esik: float) -> dict:
    """Kart: "B ya da C kipinde ii_b artık-IC @20 ≥ eşik VE CI-0-dışı → sağkalan DOĞRULANDI".

    İKİ KOŞUL BİRLİKTE: yalnız büyüklüğe bakmak, CI-0-içi bir gürültüyü "geçti" sayardı."""
    detay, degerler, gecenler = [], [], []
    for kip in ("guncel", "sabit"):
        h = _bacak_degeri(kipler[kip], "ii_b_artik_ic_fazla", "ic", "20")
        ic, ci0 = h.get("deger"), h.get("ci0_disi")
        gecti = None if (ic is None or ci0 is None) else bool(ic >= esik and ci0)
        detay.append({"kip": kip, "ic": ic, "ci0_disi": ci0, "gecti": gecti,
                      "neden": h.get("neden")})
        if ic is not None:
            degerler.append(ic)
        if gecti is not None:
            gecenler.append(gecti)
    return {
        "esik": esik, "deger": max(degerler) if degerler else None,
        "gecti": (any(gecenler) if gecenler else None),
        "detay": detay,
        "tanim": "B ya da C kipinde ii_b artık-IC @20 eşiği aşar VE CI-0-dışıysa geçer; iki kip "
                 "de ölçülemediyse hüküm None (eksik girdi 'geçti' sayılmaz)",
        "neden": None if gecenler else "B ve C kiplerinin ikisi de ÖLÇÜLEMEDİ",
    }


def _katman_i_esigi(kipler: dict, esik: float) -> dict:
    """Kart PK (1): katman i @20 ÜÇ KİPTE DE CI-0-dışı pozitif ve eşiğin üstünde.

    "Üç kipte de" lafzı GEVŞETİLMEZ: bir kip ölçülemediyse hüküm None'dır — iki kiple verilen
    bir "geçti", eşiği hak etmeden geçme yönünde yanlı olurdu."""
    detay, degerler, hepsi = [], [], []
    for kip in KIPLER:
        h = _bacak_degeri(kipler[kip], "i_ust20_kohort_fazlasi", "ort", "20")
        ort, ci0 = h.get("deger"), h.get("ci0_disi")
        gecti = None if (ort is None or ci0 is None) else bool(ort >= esik and ci0 and ort > 0)
        detay.append({"kip": kip, "ort": ort, "ci0_disi": ci0, "gecti": gecti,
                      "neden": h.get("neden")})
        if ort is not None:
            degerler.append(ort)
        hepsi.append(gecti)
    return {
        "esik": esik, "deger": min(degerler) if degerler else None,
        "gecti": (None if any(g is None for g in hepsi) else bool(all(hepsi))),
        "detay": detay,
        "tanim": "katman i @20 ÜÇ kipte de CI-0-dışı pozitif ve eşiğin üstünde olmalı; bir kip "
                 "ölçülemediyse hüküm None (kart lafzı 'üç kipte de')",
        "neden": ("bir ya da daha çok kip ÖLÇÜLEMEDİ — 'üç kipte de' sınavı kurulamadı"
                  if any(g is None for g in hepsi) else None),
    }


def _olculemeyen_esigi(kipler: dict, esik: float) -> dict:
    """Kart: sabit listenin bar/shares kapsamı dışında kalan payı eşiği AŞMAMALI.

    Sayı C koşumunun künyesinden OKUNUR, burada YENİDEN HESAPLANMAZ — iki kopya sessizce
    ayrışırdı (tek-kaynak yasası)."""
    kayit = kipler["sabit"]
    kunye = kayit.get("sabit_liste_kunyesi") or {}
    oran = kunye.get("kapsam_disi_oran")
    neden = None
    if not kayit.get("okundu"):
        neden = f"C kipi okunamadı: {kayit.get('neden')}"
    elif oran is None:
        neden = kunye.get("neden") or "künyede kapsam dışı oran YOK — ÖLÇÜLEMEDİ"
    return {"esik": esik, "deger": oran, "gecti": None if oran is None else bool(oran <= esik),
            "kaynak": kunye.get("kaynak"), "sabit_liste_sha256": kunye.get("sha256"),
            "kapsam_disi_n": kunye.get("kapsam_disi_n"), "sabit_liste_n": kunye.get("n"),
            "tanim": "sabit listenin ÖLÇÜLEMEYEN payı eşiği aşarsa C kipi bilgisizdir; sayı C "
                     "koşumunun künyesinden OKUNUR, yeniden hesaplanmaz",
            "neden": neden}


def esikleri_olc(kart_esikler: dict, kipler: dict, kapi: dict) -> dict:
    """Kartın DÖRT eşiği — adlar ve değerler KARTTAN; burada yalnız ölçüm bağlanır.

    Kartta olup burada bağlanmayan bir eşik SESSİZCE DÜŞMEZ: `neden` ile yazılır ve
    `gecti` None kalır (kart büyürse bu betiğin körlüğü görünür olsun diye)."""
    baglayici = {
        "ii_b_artik_ic_20g_alt": lambda e: _ii_b_esigi(kipler, e),
        "katman_i_pk_20g_alt": lambda e: _katman_i_esigi(kipler, e),
        "olculemeyen_sabit_liste_ust_oran": lambda e: _olculemeyen_esigi(kipler, e),
        "a_kipi_pk1_tutarlilik_tol": lambda e: {
            "esik": e, "deger": kapi.get("maks_mutlak_fark"), "gecti": kapi.get("gecti"),
            "tanim": "A kipi ≡ EDG-093 PK-1 (altı bacak) — değer maksimum mutlak farktır",
            "neden": kapi.get("neden")},
    }
    out = {}
    for ad, deger in kart_esikler.items():
        if ad not in baglayici:
            out[ad] = {"esik": deger, "deger": None, "gecti": None,
                       "neden": "bu eşiği ölçen kapı bu betikte YOK — kart büyümüş olabilir, "
                                "hüküm UYDURULMAZ"}
            continue
        out[ad] = baglayici[ad](deger)
    return out


# =================================================================================================
# 5. KILL-LIST — METİN KARTTAN, TETİK ÖLÇÜMDEN
# =================================================================================================
def kill_list_tetikleri(kart_kill: list, esikler: dict, kapi: dict, kipler: dict) -> tuple:
    """(tetiklenen kalemler, eşleme muhasebesi). Kalem METNİ kartın kendi cümlesidir.

    Tetik durumu ÜÇ DEĞERLİDİR: True (tetiklendi), False (tetiklenmedi), None (ölçülemedi —
    ölçülemeyen bir kill koşulu "tetiklenmedi" SAYILMAZ)."""
    def _b_c_ci0_ici():
        d = {x["kip"]: x for x in (esikler.get("ii_b_artik_ic_20g_alt") or {}).get("detay") or []}
        ci = [d.get(k, {}).get("ci0_disi") for k in ("guncel", "sabit")]
        if any(c is None for c in ci):
            return None
        return bool(not any(ci))

    def _katman_i_dusen():
        g = (esikler.get("katman_i_pk_20g_alt") or {}).get("gecti")
        return None if g is None else bool(not g)

    def _sabit_pay():
        e = esikler.get("olculemeyen_sabit_liste_ust_oran") or {}
        return None if e.get("gecti") is None else bool(not e["gecti"])

    def _a_kipi():
        return None if kapi.get("gecti") is None else bool(not kapi["gecti"])

    durumlar = {"a_kipi_pk1": _a_kipi(), "asof_regresyonu": _a_kipi(),
                "katman_i_pk": _katman_i_dusen(), "b_ve_c_ci0_ici": _b_c_ci0_ici(),
                "sabit_olculemeyen": _sabit_pay()}
    kaynak_kapi = {
        "a_kipi_pk1": "a_kipi_pk1_kapisi", "asof_regresyonu": "a_kipi_pk1_kapisi",
        "katman_i_pk": "esikler.katman_i_pk_20g_alt",
        "b_ve_c_ci0_ici": "esikler.ii_b_artik_ic_20g_alt",
        "sabit_olculemeyen": "esikler.olculemeyen_sabit_liste_ust_oran"}

    tetik, eslesen_metin, durum_satirlari = [], set(), []
    for anahtar, belirtec in KILL_ESLEME:
        kalemler = [str(k) for k in kart_kill if belirtec in str(k)]
        if len(kalemler) != 1:
            durum_satirlari.append({"anahtar": anahtar, "belirtec": belirtec,
                                    "kalem": None, "durum": None, "aday_n": len(kalemler),
                                    "neden": "kart kalemi TEK eşleşmedi — metin değişmiş olabilir"})
            continue
        kalem, durum = kalemler[0], durumlar.get(anahtar)
        eslesen_metin.add(kalem)
        durum_satirlari.append({"anahtar": anahtar, "belirtec": belirtec, "kalem": kalem,
                                "durum": durum, "kaynak_kapi": kaynak_kapi.get(anahtar),
                                "neden": None if durum is not None else "ÖLÇÜLEMEDİ"})
        if durum:
            tetik.append({"anahtar": anahtar, "kalem": kalem,
                          "kaynak_kapi": kaynak_kapi.get(anahtar)})
    muhasebe = {
        "kart_kalem_n": len(kart_kill), "eslesen_n": len(eslesen_metin),
        "eslesmeyen_kart_kalemleri": [str(k) for k in kart_kill if str(k) not in eslesen_metin],
        "durumlar": durum_satirlari,
        "tanim": "kalem METNİ karttan gelir; burada yalnız 'hangi cümle hangi kapıya bağlı' "
                 "eşlemesi durur. Eşleşmeyen kart kalemi ADIYLA sayılır — kart değişirse "
                 "eşleme sessizce kaybolmasın.",
    }
    return tetik, muhasebe


# =================================================================================================
# 6. RAPOR
# =================================================================================================
def _yuzde(x, nd=3):
    return "—" if x is None else f"{100.0 * float(x):.{nd}f}%"


def _sayi(x, nd=6):
    return "—" if x is None else f"{float(x):.{nd}f}"


def _ci(c):
    return "—" if not c else f"[{c['lo']:.6f} · {c['hi']:.6f}]"


def _isaret(x):
    return {True: "EVET", False: "hayır", None: "—"}.get(x, str(x))


def rapor_metni(sonuc: dict) -> str:
    """RAPOR_096 — okuyan Rol-1 / operatör masası. HÜKÜM YOK: yalnız sayı, eşik ve tetik."""
    s: list[str] = []
    a = s.append
    a("# EDG-2026-096 · üç üyelik kipinin karşılaştırması (as-of · güncel · sabit)")
    a("")
    a(f"**Hüküm:** {sonuc['hukum']} · **Damga:** {sonuc['damga_utc']}")
    a("")
    a("> Bu betik ÖLÇMEZ, OKUR: bütün sayılar EDG-093 ölçüm betiğinin üç koşumundan gelir. "
      "Eşikler ve kill-list metinleri KARTTAN okunur; hüküm Rol-1'indir.")
    a("")

    a("## Okunan koşumlar")
    a("")
    a("| Kip | Okundu | Damga | Koşum | Yol | sha256 |")
    a("|---|---|---|---|---|---|")
    for kip in KIPLER:
        k = sonuc["kipler"][kip]
        g = sonuc["girdi_damgasi"].get(kip) or {}
        a(f"| {kip} | {_isaret(k.get('okundu'))} | {k.get('damga') or '—'} | "
          f"{k.get('kosum_anahtari') or '—'} | `{k.get('yol') or '—'}` | "
          f"`{g.get('sha256') or (g.get('neden') or '—')}` |")
    p = sonuc["pk1_referansi"]
    a(f"| PK-1 ref | {_isaret(p.get('okundu'))} | {p.get('damga') or '—'} | — | "
      f"`{p.get('yol') or '—'}` | "
      f"`{(sonuc['girdi_damgasi'].get('pk1_referans') or {}).get('sha256') or '—'}` |")
    a("")

    a("## Kip × bacak tablosu")
    a("")
    a("| Kip | Bacak | Ufuk | Değer | %95 blok-CI | CI-0-dışı |")
    a("|---|---|---|---:|---|---|")
    for r in sonuc["tablo"]:
        bicim = _sayi(r["deger"]) if r["deger_alani"] == "ic" else _yuzde(r["deger"])
        a(f"| {r['kip']} | {r['bacak']} | {r['ufuk']}g | {bicim} | {_ci(r['ci'])} | "
          f"{_isaret(r['ci0_disi'])} |")
    a("")

    a("## Kart eşikleri")
    a("")
    a("| Eşik (karttan) | Değer | Eşik | Geçti |")
    a("|---|---:|---:|---|")
    for ad, e in sonuc["esikler"].items():
        a(f"| {ad} | {_sayi(e.get('deger'))} | {_sayi(e.get('esik'))} | "
          f"{_isaret(e.get('gecti'))}{(' · ' + str(e.get('neden'))) if e.get('neden') else ''} |")
    a("")

    k = sonuc["a_kipi_pk1_kapisi"]
    a("## A kipi ≡ EDG-093 PK-1 kapısı")
    a("")
    a(f"Kıyaslanan bacak: **{k.get('kiyaslanan_bacak_n')}** · maksimum mutlak fark: "
      f"**{_sayi(k.get('maks_mutlak_fark'), 9)}** · tolerans: {_sayi(k.get('tolerans'), 9)} · "
      f"geçti: **{_isaret(k.get('gecti'))}**"
      f"{(' · ' + str(k.get('neden'))) if k.get('neden') else ''}")
    a("")
    a("| Bacak | Ufuk | A kipi | PK-1 | Mutlak fark | Geçti |")
    a("|---|---|---:|---:|---:|---|")
    for r in k.get("detay") or []:
        a(f"| {r['bacak']} | {r['ufuk']}g | {_sayi(r['a_kipi_deger'])} | "
          f"{_sayi(r['pk1_deger'])} | {_sayi(r['mutlak_fark'], 9)} | {_isaret(r['gecti'])} |")
    a("")

    a("## Kill-list tetikleri")
    a("")
    if sonuc["kill_list_tetik"]:
        for t in sonuc["kill_list_tetik"]:
            a(f"- **TETİKLENDİ** ({t['anahtar']} ← {t['kaynak_kapi']}): {t['kalem']}")
    else:
        a("- Tetiklenen kalem YOK (ölçülemeyen kalemler aşağıdaki muhasebededir).")
    a("")
    a("| Anahtar | Durum | Kaynak kapı | Kart kalemi |")
    a("|---|---|---|---|")
    for d in sonuc["kill_list_muhasebesi"]["durumlar"]:
        a(f"| {d['anahtar']} | {_isaret(d.get('durum'))} | {d.get('kaynak_kapi') or '—'} | "
          f"{(d.get('kalem') or d.get('neden') or '—')} |")
    esm = sonuc["kill_list_muhasebesi"]["eslesmeyen_kart_kalemleri"]
    a("")
    a(f"Eşleşmeyen kart kalemi: **{len(esm)}**" + (f" — {esm}" if esm else ""))
    a("")
    a(f"_Üretici: `research/olcumler/edg093_midcap_pit/karsilastir096.py` · "
      f"hüküm {sonuc['hukum']}._")
    return "\n".join(s) + "\n"


# =================================================================================================
# 7. ANA AKIŞ
# =================================================================================================
def _ayristirici() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="karsilastir096.py",
        description="EDG-2026-096 — üç üyelik kipinin (asof/guncel/sabit) karşılaştırması, kart "
                    "eşikleri ve kill-list tetikleri. HÜKÜM YOK.")
    ap.add_argument("--asof", type=pathlib.Path, required=True,
                    help="A kipi sonuç json'u (EDG-093 as-of koşumu)")
    ap.add_argument("--guncel", type=pathlib.Path, default=None,
                    help="B kipi sonuç json'u; verilmezse bu kip ÖLÇÜLEMEDİ sayılır")
    ap.add_argument("--sabit", type=pathlib.Path, default=None,
                    help="C kipi sonuç json'u; verilmezse bu kip ÖLÇÜLEMEDİ sayılır")
    ap.add_argument("--pk1-referans", type=pathlib.Path, default=None,
                    help="EDG-093 sonuç json'u (pk.pk1.detay) — A kipi kapısının referansı")
    ap.add_argument("--kart", type=pathlib.Path, required=True,
                    help="EDG-2026-096 kart yaml'i — eşikler ve kill-list BURADAN okunur")
    ap.add_argument("--cikti", type=pathlib.Path, required=True, help="çıktı dizini")
    return ap


def main(argv=None) -> int:
    ARGV = _ayristirici().parse_args(argv)
    cikti = ARGV.cikti.resolve()
    cikti.mkdir(parents=True, exist_ok=True)
    damga = damga_uret()

    kart = kart_oku(ARGV.kart)
    yollar = {"asof": ARGV.asof, "guncel": ARGV.guncel, "sabit": ARGV.sabit}
    kipler = {kip: kip_oku(yollar[kip], kip) for kip in KIPLER}
    pk1 = pk1_detayi_oku(ARGV.pk1_referans)

    kapi = a_kipi_pk1_kapisi(kipler["asof"], pk1,
                             float(kart["esikler"].get("a_kipi_pk1_tutarlilik_tol") or 0.0))
    esikler = esikleri_olc(kart["esikler"], kipler, kapi)
    tetik, kill_muhasebe = kill_list_tetikleri(kart["kill_list"], esikler, kapi, kipler)

    girdi = {kip: damgala(yollar[kip]) for kip in KIPLER}
    girdi["pk1_referans"] = damgala(ARGV.pk1_referans)
    girdi["kart"] = damgala(ARGV.kart)
    girdi["olcum_kodu"] = damgala(pathlib.Path(__file__).resolve())

    sonuc = {
        "kart": KART_ID,
        "asama": "kip karşılaştırması — EDG-093 kodunun üç evren kipindeki koşumları",
        "hukum": HUKUM,
        "rol": "ölçüm ajanı — HÜKÜM VERMEZ, hüküm ÖNERİSİ DE YAZMAZ; kart dosyasına DOKUNULMADI",
        "okuyan": "(1) Rol-1: hüküm AYNI turda karta + K defterine işlenir (CLAUDE.md §5); "
                  "(2) RAPOR_096_<damga>.md okuyucusu (operatör masası).",
        "yazim_beyani": "YAZILAN HER ŞEY --cikti altındadır: sonuc_096_<damga>.json ve "
                        "RAPOR_096_<damga>.md. repo/state'e yazım YOK; meridian İTHAL EDİLMEDİ; "
                        "ağa çıkılmadı; hiçbir sayı yeniden hesaplanmadı (hepsi girdi "
                        "json'larından OKUNDU).",
        "damga_utc": damga, "olcum_tarihi": dt.datetime.now(dt.timezone.utc).isoformat(),
        "uretici": "research/olcumler/edg093_midcap_pit/karsilastir096.py",
        "girdi_damgasi": girdi,
        "kipler": {kip: {k: v for k, v in kipler[kip].items() if k != "bacaklar"}
                   for kip in KIPLER},
        "pk1_referansi": {k: v for k, v in pk1.items() if k != "detay"},
        "tablo": tablo_kur(kipler),
        "esikler": esikler,
        "a_kipi_pk1_kapisi": kapi,
        "kill_list_tetik": tetik,
        "kill_list_muhasebesi": kill_muhasebe,
        "k_beyani": {"satirlar": [
            "K = 2 (kart `k_registry`): EDG-096-guncel-liste-ii-b-artik-ic-20g ve "
            "EDG-096-sabit251-ii-b-artik-ic-20g — B ve C kiplerinin ii_b artık-IC @20 bacağı.",
            "A kipi EDG-093 PK-1'in TEKRARIdır ve K'ye GİRMEZ; tutarlılık kapısıdır.",
            "Katman i ve ii_a1 raporlanır, K harcamaz (kart `k_registry` şerhi).",
        ]},
    }

    json_yolu = cikti / f"sonuc_096_{damga}.json"
    json_yolu.write_text(json.dumps(sonuc, ensure_ascii=False, indent=2) + "\n",
                         encoding="utf-8")
    rapor_yolu = cikti / f"RAPOR_096_{damga}.md"
    rapor_yolu.write_text(rapor_metni(sonuc), encoding="utf-8")

    print(f"YAZILDI: {json_yolu}")
    print(f"YAZILDI: {rapor_yolu}")
    okunan = [k for k in KIPLER if kipler[k]["okundu"]]
    print(f"okunan kip={okunan} · A≡PK-1 geçti={kapi.get('gecti')} · "
          f"kill-list tetik={len(tetik)} · hüküm={HUKUM}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
