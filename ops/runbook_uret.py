#!/usr/bin/env python3
"""ops/runbook_uret.py — `docs/RUNBOOK.md` ÜRETİCİSİ (UIUX S1-T3, 2026-08-01).

NEDEN VAR. Panonun J2 zinciri "alarm → teşhis → runbook → çözüm" son halkasız koşuyordu:
alarm satırları ve sessiz-hat sapmaları bir hedef gösteremiyordu, çünkü bu depoda YAZILI BİR
RUNBOOK YOKTU (WP0 borç #1, İ9/şiddet 3). Elle yazılmış bir runbook ise iki hafta içinde
bayatlar ve bayat bir runbook YANLIŞ runbook'tur — operatörü var olmayan bir betiğe gönderir.
Bu yüzden runbook YAZILMAZ, ÜRETİLİR: kaynağı koddur ve kod değişince yeniden üretilir.

ONAYLI KAYNAK SÖZLEŞMESİ (WP0 §6.3 — operatör onayı):
  1. `ops/*.sh` ve `deploy/oracle-a1/*.sh` BAŞLIK YORUMLARI (her betiğin tepe açıklaması)
  2. `MERIDIAN_ENGINEERING_LOG.md` → "AÇIK KALANLAR" · "KALICI RİSKLER / DERSLER" ·
     "BU OTURUMDA BULUNAN + ÇÖZÜLEN" bölümleri (bilinen sınıflar)
  3. Envanter kaynakları (adları ve pencereleri UYDURULAMAZ, koddan okunur):
     `meridian/obs.py` ALARM_ sabitleri · `meridian/watchdog.py` EXPECTED sözlüğü ·
     `meridian/api.py::_sessiz_hat` sapma adları/ipuçları · `obs.alarm(...)` ateşleme
     yerleri · `watchdog.beat("...")` nabız yerleri.
  4. `ops/*.sh` ve `deploy/oracle-a1/*.sh` GÖVDESİNDEKİ `obs.alarm('JETON'...)` ateşlemeleri
     (seçenek C — WP0 §6.3 uzantısı, operatör onayı): bir betik GÖVDESİNDE bir jetonu
     ateşliyorsa o jetonun KURTARMA YÖNETİCİSİDİR (ör. `ops/keepalive.sh` ölü sunucuyu
     diriltir ve `MECHANISM_STALE` yazar) ve jetonun Çözüm alanına eşlenir. Başlık (madde 1)
     betiğin NE OLDUĞUNU söyler; gövde ateşlemesi hangi ALARMI ele aldığını — iki AYRI boyut,
     ve ikincisi başlıkta jetonun adı geçmese de (keepalive'de geçmez) koddan türer.

SÖZLEŞME DIŞI KAYNAK YOK. `deploy/*.sh` (üst düzey; monitoring.sh dahil) bilerek DIŞARIDA —
onaylı küme yukarıdaki DÖRT maddedir. Bu sınır belgede de yazar; sessiz bir kapsam genişlemesi,
"runbook'un kaynağı ne" sorusunu bir daha cevaplanamaz hale getirirdi.

UYDURMA YASAĞI (anayasa 1'in bu dosyadaki karşılığı). Bir alanın kaynağı yoksa o alan
"runbook girdisi henüz yazılmadı" der ve NEDEN yazılmadığını (hangi kaynakta arandı) söyler.
Hiçbir cümle "muhtemelen şudur" diye tamamlanmaz; eşleştirme kuralı LİTERAL AD GEÇİŞİDİR
(bulanık/anlamsal eşleştirme yok) ve kuralın kendisi üretilen belgenin başında yazılıdır.

DAMGA YOK, DETERMİNİSTİK ÇIKTI. Belgeye üretim ZAMANI yazılmaz: yazılsaydı her koşu diff
üretir, `--kontrol` kapısı anlamsızlaşır ve "belge kodla ayrıştı mı" sorusu ölçülemez olurdu.
Aynı kaynaklardan aynı metin çıkar; fark varsa fark GERÇEKTİR.

KULLANIM:
    python ops/runbook_uret.py                 # docs/RUNBOOK.md'yi üret/yaz
    python ops/runbook_uret.py --kontrol       # yazMA; diskteki belge güncel mi (çıkış 1 = bayat)
    python ops/runbook_uret.py --cikti /yol.md # başka bir hedefe yaz
"""
from __future__ import annotations

import argparse
import ast
import pathlib
import re
import sys

KOK = pathlib.Path(__file__).resolve().parents[1]
HEDEF = KOK / "docs" / "RUNBOOK.md"

# Sentinel — brief'in çivilediği ifade. Testler bu dizgeyi arar; değiştirilirse test kırılır.
YAZILMADI = "runbook girdisi henüz yazılmadı"

BETIK_KUMESI = ("ops/*.sh", "deploy/oracle-a1/*.sh")
LOG_BOLUMLERI = ("AÇIK KALANLAR", "KALICI RİSKLER", "BU OTURUMDA BULUNAN")


# ==================================================================================
# 1) ENVANTER OKUYUCULARI — hepsi KAYNAK DOSYAYI ayrıştırır, hiçbiri içe aktarmaz.
#    İçe aktarma, üreticiyi meridian'ın çalışma-anı bağımlılıklarına (ve state/'e)
#    bağlardı; bir belge üreticisi canlı durum okumamalıdır.
# ==================================================================================

def _oku(rel: str) -> str:
    return (KOK / rel).read_text(encoding="utf-8")


def _ustteki_yorum(satirlar: list[str], indeks: int) -> str:
    """`indeks` satırının ÜSTÜNDEKİ bitişik `#` yorum bloğu (yukarı doğru toplanır)."""
    blok: list[str] = []
    i = indeks - 1
    while i >= 0:
        s = satirlar[i].strip()
        if not s.startswith("#"):
            break
        blok.append(s.lstrip("#").strip())
        i -= 1
    return " ".join(reversed([b for b in blok if b]))


def _satir_sonu_yorumu(satir: str) -> str:
    """Satır sonundaki `# ...` yorumu. Dizgi içindeki `#` karakterini yutmamak için
    ayrıştırma ast ile yapılmaz — dizgiler önce maskelenir."""
    maske = re.sub(r'"[^"]*"|\'[^\']*\'', lambda m: "\0" * len(m.group(0)), satir)
    p = maske.find("#")
    return satir[p + 1:].strip() if p >= 0 else ""


def alarm_envanteri() -> list[dict]:
    """`meridian/obs.py` ALARM_ sabitleri → [{sabit, jeton, not, gerekce}] (dosya sırasında).

    NOT ile GEREKÇE ayrı tutulur: satır sonu yorumu jetonun TANIMIDIR ("ne oldu"), üstündeki
    blok ise o jetonun neden ayrı bir sınıf olduğudur ("neden bu alarm var"). İkisini tek
    alanda birleştirmek, kısa tanımı uzun gerekçenin içinde kaybederdi."""
    kaynak = _oku("meridian/obs.py")
    satirlar = kaynak.splitlines()
    out: list[dict] = []
    for i, s in enumerate(satirlar):
        m = re.match(r'^(ALARM_[A-Z_0-9]+)\s*=\s*"([A-Z_0-9]+)"', s)
        if not m:
            continue
        out.append({"sabit": m.group(1), "jeton": m.group(2),
                    "not": _satir_sonu_yorumu(s), "gerekce": _ustteki_yorum(satirlar, i)})
    return out


def mekanizma_envanteri() -> list[dict]:
    """`meridian/watchdog.py` EXPECTED → [{ad, pencere_s, not, gerekce}] (bildirim sırasında).

    Pencere DEĞERİ ast ile HESAPLANIR (`30 * 60` gibi ifadeler): metinden okumak "30" yazardı."""
    kaynak = _oku("meridian/watchdog.py")
    satirlar = kaynak.splitlines()
    agac = ast.parse(kaynak)
    sozluk = None
    for d in agac.body:
        hedef = (d.target if isinstance(d, ast.AnnAssign)
                 else (d.targets[0] if isinstance(d, ast.Assign) and d.targets else None))
        if isinstance(hedef, ast.Name) and hedef.id == "EXPECTED" and isinstance(d.value, ast.Dict):
            sozluk = d.value
            break
    if sozluk is None:
        raise SystemExit("watchdog.py içinde EXPECTED sözlüğü bulunamadı — üretici kaynağını kaybetti")
    out: list[dict] = []
    for anahtar, deger in zip(sozluk.keys, sozluk.values):
        if not (isinstance(anahtar, ast.Constant) and isinstance(anahtar.value, str)):
            continue
        i = anahtar.lineno - 1
        out.append({"ad": anahtar.value,
                    "pencere_s": _sayi(deger),
                    "not": _satir_sonu_yorumu(satirlar[i]),
                    "gerekce": _ustteki_yorum(satirlar, i)})
    return out


def _sayi(dugum: ast.AST) -> int:
    """`30 * 60` / `4 * 24 * 3600` gibi pencere ifadelerini HESAPLAR.

    `ast.literal_eval` burada YETMEZ (çarpım bir BinOp'tur ve o fonksiyon yalnız düz sabitleri
    çözer) ve `eval` KULLANILMAZ: kaynak bizim olsa da bir belge üreticisine kod yürütme
    yetkisi vermek gereksiz bir yüzeydir. Yalnız toplama/çarpma tanınır; başka bir düğüm
    gelirse ÜRETİM DURUR — sessizce 0 yazmak, penceresi 'yok' görünen bir mekanizma üretirdi."""
    if isinstance(dugum, ast.Constant) and isinstance(dugum.value, int):
        return dugum.value
    if isinstance(dugum, ast.BinOp) and isinstance(dugum.op, (ast.Mult, ast.Add)):
        sol, sag = _sayi(dugum.left), _sayi(dugum.right)
        return sol * sag if isinstance(dugum.op, ast.Mult) else sol + sag
    raise SystemExit(f"EXPECTED penceresi tanınmayan ifade: {ast.dump(dugum)} — üretici güncellenmeli")


def _fonksiyon(agac: ast.Module, ad: str) -> ast.FunctionDef:
    for d in ast.walk(agac):
        if isinstance(d, ast.FunctionDef) and d.name == ad:
            return d
    raise SystemExit(f"{ad}() bulunamadı — üretici kaynağını kaybetti")


def sessizhat_envanteri() -> tuple[list[dict], list[str]]:
    """`meridian/api.py::_sessiz_hat` → (sapma adları, bekçi-segmenti genel ipuçları).

    İKİ AYRI ÇIKARIM, çünkü kaynakta iki ayrı biçim var:
      * ADI SABİT sapmalar (`devre_kesici`, `nabız`, `veri_kalitesi` ve `kollar` demetindeki
        `soft_halt`/`halt_learning`) → kendi bölümlerini alır.
      * ADI DEĞİŞKEN sapmalar (bekçi segmenti: ad `s.get("name")`ten gelir) → adı burada
        okunamaz ama İPUCU sabittir; o ipuçları bütün mekanizma bölümlerinde teşhis adımı olur.
    İkincisini "ad bulunamadı" diye atmak, api.py'nin RUNBOOK İÇİN yazdığı cümleleri çöpe
    atmak olurdu — bu üretici tam olarak onları taşımak için var."""
    agac = ast.parse(_oku("meridian/api.py"))
    fn = _fonksiyon(agac, "_sessiz_hat")
    sapmalar: list[dict] = []
    bekci_ipuclari: list[str] = []
    gorulen: set[str] = set()

    def _sabit(dugum) -> str | None:
        return dugum.value if isinstance(dugum, ast.Constant) and isinstance(dugum.value, str) else None

    for d in ast.walk(fn):
        # (a) `kollar` demetleri: (ad, açık_mı, yol, ipucu)
        if isinstance(d, ast.Tuple) and len(d.elts) == 4:
            ad, ipucu = _sabit(d.elts[0]), _sabit(d.elts[3])
            if ad and ipucu and ad not in gorulen:
                gorulen.add(ad)
                sapmalar.append({"ad": ad, "detay": "kol ÇEKİLİ", "ipucu": ipucu})
        # (b) sapma sözlükleri — YALNIZ SABİT DİZGİLER. Sabit olmayan bir alanı `ast.unparse`
        # ile kaynak metnine çevirmek denendi ve YANLIŞ İÇERİK ÜRETTİ: `kollar` döngüsünün
        # sözlüğünde `"ipucu": ipucu` bir DEĞİŞKENDİR ve unparse ondan "ipucu" kelimesini
        # üretiyordu — runbook'a ipucu diye "ipucu" yazılıyordu. Ölçülemeyen alan atlanır.
        if isinstance(d, ast.Dict):
            alan = {}
            for anahtar, deger in zip(d.keys, d.values):
                k = _sabit(anahtar)
                if k in ("ad", "detay", "ipucu"):
                    alan[k] = _sabit(deger)
            if not alan.get("ipucu"):
                continue
            if alan.get("ad"):
                if alan["ad"] in gorulen:
                    continue
                gorulen.add(alan["ad"])
                sapmalar.append({"ad": alan["ad"], "detay": alan.get("detay") or "",
                                 "ipucu": alan["ipucu"]})
            elif alan["ipucu"] not in bekci_ipuclari:
                bekci_ipuclari.append(alan["ipucu"])
    return sapmalar, bekci_ipuclari


def _py_dosyalari() -> list[pathlib.Path]:
    return sorted((KOK / "meridian").rglob("*.py"))


def _kaynak_parcasi(kaynak: str, dugum: ast.AST) -> str:
    """Düğümün KAYNAKTAKİ metni, tek satıra indirilmiş.

    NEDEN `ast.unparse` DEĞİL (ölçüldü, 2026-08-01): unparse f-string'leri yeniden BASAR ve
    tırnak seçimi Python SÜRÜMÜNE göre değişir — 3.14 `f'…'`, 3.12 `f"…"` üretti. Aynı depodan
    iki farklı belge çıkması, `--kontrol` kapısını ve determinizm testini yalancı-kırmızıya
    çevirir; daha kötüsü, gerçek bir ayrışmayı gürültüye gömer. Kaynak parçası ise DOSYADA NE
    YAZIYORSA odur: sürümden bağımsız ve zaten göstermek istediğimiz şey."""
    parca = ast.get_source_segment(kaynak, dugum) or ""
    return " ".join(parca.split())


def atesleme_yerleri() -> dict[str, list[dict]]:
    """`obs.alarm(...)` çağrıları → {jeton: [{yer, mesaj}]}.

    ast ile, çünkü mesajlar çoğu zaman f-string ve satır kırıyor: metin araması ya mesajı
    kesik alır ya da hiç bulamaz. Mesaj KAYNAK HALİYLE taşınır — yer tutucular ({e},
    {s['name']}) korunur; bir değeri uydurmaktansa şablonu göstermek."""
    sabit_jeton = {a["sabit"]: a["jeton"] for a in alarm_envanteri()}
    out: dict[str, list[dict]] = {}
    for p in _py_dosyalari():
        kaynak = p.read_text(encoding="utf-8")
        try:
            agac = ast.parse(kaynak)
        except SyntaxError:  # sessiz-yutma DEĞİL: ayrıştırılamayan dosya aşağıda RAPORLANIR
            print(f"UYARI: {p} ayrıştırılamadı — ateşleme yerleri EKSİK olabilir", file=sys.stderr)
            continue
        for d in ast.walk(agac):
            if not (isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute)
                    and d.func.attr == "alarm" and d.args):
                continue
            ilk = d.args[0]
            if isinstance(ilk, ast.Constant) and isinstance(ilk.value, str):
                jeton = ilk.value
            elif isinstance(ilk, ast.Attribute) and ilk.attr in sabit_jeton:
                jeton = sabit_jeton[ilk.attr]
            else:
                continue
            mesaj = _kaynak_parcasi(kaynak, d.args[1]) if len(d.args) > 1 else ""
            out.setdefault(jeton, []).append(
                {"yer": f"{p.relative_to(KOK)}:{d.lineno}", "mesaj": mesaj})
    return out


def nabiz_yerleri() -> dict[str, list[str]]:
    """`watchdog.beat("ad")` çağrıları → {ad: [dosya:satır]}.

    BU EN DEĞERLİ TEŞHİS ADIMIDIR: "mekanizma sustu" alarmının ilk sorusu "nabzı KİM atıyor
    ve o kod yolu koşuyor mu"dur. Cevabı hiçbir yerde yazılı değildi; burada koddan türer."""
    out: dict[str, list[str]] = {}
    for p in _py_dosyalari():
        try:
            agac = ast.parse(p.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for d in ast.walk(agac):
            if (isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute)
                    and d.func.attr == "beat" and d.args
                    and isinstance(d.args[0], ast.Constant)
                    and isinstance(d.args[0].value, str)):
                out.setdefault(d.args[0].value, []).append(f"{p.relative_to(KOK)}:{d.lineno}")
    return out


def betik_basliklari() -> list[dict]:
    """Onaylı betik kümesinin BAŞLIK YORUMLARI → [{yol, baslik}] (yol sırasında).

    Başlık = shebang'dan sonraki İLK bitişik `#` bloğu. Betiğin gövdesindeki yorumlar ALINMAZ:
    başlık betiğin kendi sözleşmesidir, gövde ise uygulama ayrıntısı — ikisini karıştırmak
    runbook'u okunmaz bir kod dökümüne çevirirdi."""
    out: list[dict] = []
    for desen in BETIK_KUMESI:
        for p in sorted(KOK.glob(desen)):
            satirlar = p.read_text(encoding="utf-8").splitlines()
            i = 1 if satirlar and satirlar[0].startswith("#!") else 0
            blok: list[str] = []
            while i < len(satirlar):
                s = satirlar[i]
                if not s.startswith("#"):
                    break
                blok.append(s[1:].lstrip() if s[1:2] == " " else s[1:])
                i += 1
            out.append({"yol": str(p.relative_to(KOK)), "baslik": "\n".join(blok).strip()})
    return out


def betik_govde_atesleme() -> dict[str, list[dict]]:
    """Onaylı betik kümesinin GÖVDESİNDE `obs.alarm('JETON'...)` ateşleyen betikler →
    {jeton: [{yol, satirlar}]} (yol sırasında; satırlar dosya sırasında).

    NEDEN AYRI BİR ONAYLI KAYNAK BOYUTU (seçenek C). `betik_basliklari` betiğin BAŞLIK
    yorumunu okur — betiğin NE OLDUĞUNU. Ama bir betik GÖVDESİNDE bir jetonu `obs.alarm(...)`
    ile ateşliyorsa, o alarmı doğuran koşulu betik ZATEN ele alıyordur: `ops/keepalive.sh`
    ölü sunucuyu diriltir ve `MECHANISM_STALE` yazar. Yani betik o jetonun KURTARMA
    YÖNETİCİSİDİR ve jetonun Çözüm/betik alanına eşlenmesi GERÇEK bir bağdır — üstelik jetonun
    adı BAŞLIKTA geçmediğinden (keepalive başlığında `MECHANISM_STALE` yoktur) yalnız başlık
    taranırken bu bağ GÖRÜNMEZ kalıyordu; boş bir Çözüm alanı doğuruyordu.

    KURAL — LİTERAL AD GEÇİŞİ: `obs.alarm(` + tırnaklı jeton deseni, betiğin GÖVDESİNDE
    (başlık `#` bloğunun ALTINDA) ve YORUM OLMAYAN bir satırda. Yorumu dışlamak, gövdede sözü
    geçen ama ateşlenmeyen bir jetonu (ör. `# eskiden obs.alarm('X') vardı`) kurtarma
    yöneticisi diye UYDURMAKTAN korur — anayasa 1. Bulanık/anlamsal eşleştirme yoktur; bir
    jetonun gövde ateşlemesi yoksa Çözüm alanı boş kalır (o boşluk elle içerik borcudur, ayrı
    bir turdur — üretici var olmayan bir kurtarma betiği İCAT ETMEZ)."""
    desen = re.compile(r"""obs\.alarm\(\s*['"]([A-Z_0-9]+)['"]""")
    ham: dict[str, dict[str, list[int]]] = {}
    for desen_yol in BETIK_KUMESI:
        for p in sorted(KOK.glob(desen_yol)):
            satirlar = p.read_text(encoding="utf-8").splitlines()
            # Başlık bloğunu ATLA — betik_basliklari ile AYNI sınır: shebang + ilk bitişik `#`
            # bloğu başlıktır, gövde ondan sonra başlar. İki fonksiyon aynı sınırı görmezse
            # bir jeton hem başlık hem gövde kanalından çift sayılabilirdi.
            i = 1 if satirlar and satirlar[0].startswith("#!") else 0
            while i < len(satirlar) and satirlar[i].startswith("#"):
                i += 1
            for j in range(i, len(satirlar)):
                if satirlar[j].lstrip().startswith("#"):  # gövde YORUMU ateşleme değildir
                    continue
                for jeton in desen.findall(satirlar[j]):
                    ham.setdefault(jeton, {}).setdefault(
                        str(p.relative_to(KOK)), []).append(j + 1)
    return {jeton: [{"yol": yol, "satirlar": satir_nolari}
                    for yol, satir_nolari in yollar.items()]
            for jeton, yollar in ham.items()}


def log_maddeleri() -> list[dict]:
    """`MERIDIAN_ENGINEERING_LOG.md`'nin üç bölümündeki madde imli girdiler → [{bolum, metin}].

    Madde = `- ` ile başlayan satır + altındaki girintili devam satırları. Bölümün düzyazısı
    (madde olmayan paragraflar) alınmaz: runbook'un ihtiyacı olan şey SINIF listesidir."""
    metin = _oku("MERIDIAN_ENGINEERING_LOG.md")
    out: list[dict] = []
    bolum = None
    madde: list[str] = []

    def _kapat():
        if bolum and madde:
            out.append({"bolum": bolum, "metin": " ".join(x.strip() for x in madde).strip()})

    for satir in metin.splitlines():
        if satir.startswith("## "):
            _kapat()
            madde = []
            baslik = satir[3:].strip()
            bolum = baslik if any(baslik.startswith(b) for b in LOG_BOLUMLERI) else None
            continue
        if bolum is None:
            continue
        if satir.startswith("- "):
            _kapat()
            madde = [satir[2:]]
        elif madde and satir.startswith("  ") and satir.strip():
            madde.append(satir)
        elif not satir.strip():
            _kapat()
            madde = []
    _kapat()
    return out


# ==================================================================================
# 2) EŞLEŞTİRME — tek kural: LİTERAL AD GEÇİŞİ. Bulanık eşleştirme YOK.
# ==================================================================================

def _eslesen_betikler(ad: str, betikler: list[dict]) -> list[dict]:
    return [b for b in betikler if ad in b["baslik"]]


def _eslesen_log(ad: str, maddeler: list[dict]) -> list[dict]:
    return [m for m in maddeler if ad in m["metin"]]


# ==================================================================================
# 3) MARKDOWN ÜRETİMİ
# ==================================================================================

_TR_ASCII = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosucgiosu")


def capa(metin: str) -> str:
    """ASCII çapa — YALNIZ başlık metninden türeyen bölümler için (betik yolları, günlük
    bölümleri). Alarm/mekanizma/sapma bölümlerinin çapası ADIN KENDİSİDİR ve buradan geçmez:
    pano o adı çalışma anında API'den alır ve `/runbook#<ad>` kurar; araya bir dönüşüm koymak,
    panoda ve belgede İKİ AYRI slug kuralı doğurur ve biri sessizce bayatlar.

    Türkçe harfler önce ASCII karşılığına düşer: düz `[^a-z0-9]` süzgeci `ÇÖZÜLEN`i `-z-len`e
    çeviriyordu — okunaksız ve yanıltıcı."""
    return re.sub(r"[^a-z0-9]+", "-", metin.translate(_TR_ASCII).lower()).strip("-")


def _sure(saniye: int) -> str:
    if saniye % 86400 == 0:
        return f"{saniye // 86400} gün"
    if saniye % 3600 == 0:
        return f"{saniye // 3600} sa"
    return f"{saniye // 60} dk"


def _baslik_ozeti(baslik: str) -> str:
    """Betik başlığının İLK satırı (+ devamı varsa `…`). Kurtarma yöneticisi bağının yanına
    betiğin NE OLDUĞUNU koyar; başlığın TAMAMINI Çözüm alanına dökmek bölümü bir kod dökümüne
    çevirirdi ve başlığın tamamı zaten [Betik dizini] bölümünde duruyor. İlk satır + `…`
    (kesme değil, devam işareti): özetin eksik olduğu okuyucuya dürüstçe söylenir."""
    satirlar = [s for s in baslik.splitlines() if s.strip()]
    if not satirlar:
        return ""
    return satirlar[0].strip() + (" …" if len(satirlar) > 1 else "")


def _bolum(ad: str, capa: str, belirti: list[str], teshis: list[str], cozum: list[str]) -> list[str]:
    """Tek bölümün gövdesi. ÜÇ ALAN SABİT ve hiçbiri atlanmaz: boş bir alan `YAZILMADI`
    cümlesini taşır. Alanı hiç yazmamak, "burada söylenecek bir şey yok" ile "burası
    yazılmadı"yı aynı sessizliğe gömerdi."""
    p: list[str] = [f"## {ad} {{#{capa}}}", ""]
    for baslik, satirlar in (("Belirti", belirti), ("Teşhis adımları", teshis),
                             ("Çözüm / betik", cozum)):
        p.append(f"### {baslik}")
        p.append("")
        if satirlar:
            # İKİ BOŞLUKLA BAŞLAYAN GİRDİ ALT MADDEDİR: ateşleme yerleri "şu jeton şu 7 yoldan
            # gelir" cümlesinin ALTINDA durmalı; düz listeye dökülürse yedi yol, üstündeki
            # cümleyle aynı mertebede görünür ve hangisinin hangisine ait olduğu kaybolur.
            p += [(f"  - {s.strip()}" if s.startswith("  ") else f"- {s}") for s in satirlar]
        else:
            p.append(f"- **{YAZILMADI}** — onaylı kaynaklarda (betik başlıkları · mühendislik "
                     f"günlüğü) `{ad}` adı literal olarak geçmiyor.")
            if baslik.startswith("Çözüm"):
                # SENTİNEL SİLİNMEZ, YANINA YÖN KONUR. Boşluğun adı yukarıda duruyor (bir eksiği
                # gizlemek onu kapatmaz); ama operatörü hiçbir yere göndermemek de bir seçim
                # değil. Bu satır bir EŞLEŞME İDDİASI DEĞİLDİR — "eşleşen betik yok, betik
                # kümesinin tamamı burada, hükmü sen ver" der.
                p.append("- Eşleşme iddiası olmadan yön: onaylı betik kümesinin tamamı "
                         "[Betik dizini](#betikler) bölümünde; hüküm operatöründür.")
        p.append("")
    return p


def uret() -> str:
    alarmlar = alarm_envanteri()
    mekanizmalar = mekanizma_envanteri()
    sapmalar, bekci_ipuclari = sessizhat_envanteri()
    atesleme = atesleme_yerleri()
    nabizlar = nabiz_yerleri()
    betikler = betik_basliklari()
    betik_govde = betik_govde_atesleme()
    baslik_yollari = {b["yol"]: b["baslik"] for b in betikler}
    log = log_maddeleri()

    p: list[str] = []
    p += [
        "# Meridian · Operasyon Runbook",
        "",
        "> **ÜRETİLMİŞ DOSYA — ELLE DÜZENLEME YAPMA.** Kaynağı koddur; elle yazılan her satır",
        "> bir sonraki üretimde silinir. Yeniden üret: `python ops/runbook_uret.py`",
        "> · bayat mı diye sor: `python ops/runbook_uret.py --kontrol`",
        "",
        "Bu belgenin panodaki okuyucusu **`/runbook`** sayfasıdır (YASA 6). Pano alarm satırları",
        "ve sessiz-hat sapmaları buradaki bölüm çapalarına (`/runbook#<ad>`) bağlanır.",
        "",
        "## Kaynak sözleşmesi ve eşleştirme kuralı {#kaynak-sozlesmesi}",
        "",
        "Onaylı kaynaklar (WP0 §6.3, operatör onayı) — bunların DIŞINDA hiçbir yerden içerik alınmaz:",
        "",
        "- `ops/*.sh` ve `deploy/oracle-a1/*.sh` **başlık yorumları** (shebang'dan sonraki ilk `#` bloğu)",
        "- `MERIDIAN_ENGINEERING_LOG.md` → " + " · ".join(f"“{b}…”" for b in LOG_BOLUMLERI),
        "- envanter kaynakları: `meridian/obs.py` (ALARM_ sabitleri) · `meridian/watchdog.py`",
        "  (EXPECTED pencereleri + `beat()` nabız yerleri) · `meridian/api.py::_sessiz_hat`",
        "  (sapma adları ve runbook ipuçları) · `obs.alarm(...)` ateşleme yerleri",
        "- `ops/*.sh` ve `deploy/oracle-a1/*.sh` **gövdesindeki `obs.alarm(...)` ateşlemeleri**:",
        "  bir betik gövdesinde bir jetonu ateşliyorsa o jetonun **kurtarma yöneticisidir** ve",
        "  jetonun Çözüm alanına eşlenir — başlıkta adı geçmese bile koddan türer (ör.",
        "  `ops/keepalive.sh` → `MECHANISM_STALE`)",
        "",
        "**Kapsam dışı, bilerek:** `deploy/*.sh` (üst düzey, `monitoring.sh` dahil) onaylı kümede",
        "değil. Sessiz bir kapsam genişlemesi yerine sınır burada yazılı duruyor.",
        "",
        "**Eşleştirme kuralı — LİTERAL AD GEÇİŞİ.** Bir bölüme betik/günlük maddesi ancak o metinde",
        "bölümün adı harfi harfine geçiyorsa iliştirilir. Anlamsal/bulanık eşleştirme YOK: bir",
        f"alarmı yanlış betiğe bağlamak, hiç bağlamamaktan kötüdür. Kaynağı olmayan alan “**{YAZILMADI}**”",
        "der ve nerede aradığını söyler — o cümle bir eksiğin ADIDIR, doldurulacak bir boşluk değil.",
        "",
        "**Üretim damgası yoktur, bilerek:** belge zaman damgası taşısaydı her koşu diff üretir ve",
        "“kodla ayrıştı mı” sorusu ölçülemez olurdu. Aynı kaynaktan aynı metin çıkar.",
        "",
        "---",
        "",
    ]

    # ---- ÖZET SAYIM ---------------------------------------------------------------------
    p += [
        "## Envanter özeti {#envanter}",
        "",
        f"- **{len(alarmlar)} alarm jetonu** (`meridian/obs.py`) — hepsi bildirim beyaz-listesinde",
        f"  (`NOTIFY_TOKENS` ALARM_ sabitlerinden TÜRETİLİR, elle liste değil)",
        f"- **{len(mekanizmalar)} bekçi mekanizması** (`meridian/watchdog.py::EXPECTED`)",
        f"- **{len(sapmalar)} sessiz-hat sapma adı** (`meridian/api.py::_sessiz_hat`; bekçi segmentinin",
        f"  adları değişkendir ve yukarıdaki mekanizma listesinden gelir)",
        f"- **{len(betikler)} ops betiği** başlığıyla okundu",
        f"- **{len(log)} günlük maddesi** üç bölümden toplandı",
        "",
        "---",
        "",
        "# Alarmlar {#alarmlar}",
        "",
        "Bir alarm panoda üç yerde görünür: **Alarm gelen kutusu** (Bugün), **olay akışı** ve —",
        "kanal kuruluysa — telefon bildirimi. Aşağıdaki her bölüm o jetonun kendi teşhis hattıdır.",
        "",
    ]

    for a in alarmlar:
        jeton = a["jeton"]
        belirti = []
        if a["not"]:
            belirti.append(f"{a['not']} *(kaynak: `meridian/obs.py` — `{a['sabit']}`)*")
        if a["gerekce"]:
            belirti.append(f"Neden ayrı bir sınıf: {a['gerekce']} *(kaynak: `meridian/obs.py`)*")
        yerler = atesleme.get(jeton, [])
        # BELİRTİ BOŞ KALMASIN DİYE UYDURMA YOK — İKİNCİ GERÇEK KAYNAK VAR. Dört jetonun
        # (ROLLBACK, CIRCUIT_BREAKER, DATA_QUALITY, HALT_ACTIVE) obs.py'de satır sonu yorumu
        # hiç yok; ama ateşleme yerlerindeki MESAJ ŞABLONU belirtinin ta kendisidir
        # ("günlük kayıp devre kesici: {day_pnl_pct:.2%}"). Şablonu operatöre göstermek,
        # panoda göreceği cümlenin aynısıdır — eşleştirmesi tek bakışta olur.
        if not belirti and yerler:
            belirti.append("`obs.py`'de bu jetonun satır-sonu tanımı YOK; belirti, panoda "
                           "görünecek mesaj şablonlarından okunur (ateşleme yerleri aşağıda).")
        teshis = []
        if yerler:
            teshis.append(f"Bu jetonu **{len(yerler)} kod yolu** ateşliyor — hangisinin konuştuğu "
                          "olay kaydındaki `detail` alanından okunur:")
            # SIRA (dosya, SATIR NUMARASI) — düz metin sıralaması `…:1077`u `…:125`ten önce
            # koyuyordu; okuyan kişi listeyi dosyada takip edemez.
            for y in sorted(yerler, key=lambda x: (x["yer"].rsplit(":", 1)[0],
                                                   int(x["yer"].rsplit(":", 1)[1]))):
                mesaj = f" → mesaj şablonu: `{y['mesaj']}`" if y["mesaj"] else ""
                teshis.append(f"  `{y['yer']}`{mesaj}")
        else:
            teshis.append(f"Kodda `obs.alarm` ateşleme yeri BULUNAMADI — jeton tanımlı ama hiçbir "
                          f"yol onu üretmiyor. Bu bir bulgudur: ya mekanizma kablolanmamış, ya jeton emekli.")
        teshis.append("Kaydın tamamı: panoda alarm satırına bas → çekmece; diskte `state/events.jsonl`.")

        cozum = []
        for b in _eslesen_betikler(jeton, betikler):
            cozum.append(f"`{b['yol']}` — başlığında `{jeton}` geçiyor.")
        # SEÇENEK C — GÖVDE ATEŞLEMESİ: betik gövdesinde bu jetonu obs.alarm ile ateşliyorsa
        # KURTARMA YÖNETİCİSİDİR. Başlıkta ad geçmese de (keepalive'de geçmez) bağ koddan
        # gerçektir; bu, jetonun boş kalan Çözüm alanını GERÇEK bir kaynaktan kapatır.
        for atesleyen in betik_govde.get(jeton, []):
            yol = atesleyen["yol"]
            satir = ", ".join(str(n) for n in atesleyen["satirlar"])
            cozum.append(f"`{yol}` — gövdesinde `obs.alarm('{jeton}')` ateşliyor (satır {satir}); "
                         f"bu betik jetonun KURTARMA YÖNETİCİSİDİR.")
            ozet = _baslik_ozeti(baslik_yollari.get(yol, ""))
            if ozet:
                cozum.append(f"  Betik özeti: {ozet}")
        for m in _eslesen_log(jeton, log):
            cozum.append(f"**{m['bolum']}** → {m['metin']}")
        p += _bolum(jeton, jeton.lower(), belirti, teshis, cozum)

    # ---- BEKÇİ MEKANİZMALARI -------------------------------------------------------------
    p += [
        "---",
        "",
        "# Bekçi mekanizmaları {#mekanizmalar}",
        "",
        "Bekçi (`meridian/watchdog.py`) YALNIZ GÖZLEMDİR: hiçbir mekanizmayı yeniden başlatmaz,",
        "hiçbir kararı etkilemez. Bir mekanizma penceresini aştığında sessiz hattın **bekçiler**",
        "segmenti açılır ve `MECHANISM_STALE` ateşlenir. Aşağıdaki her bölüm tek bir mekanizmanın",
        "penceresini, nabzını KİMİN attığını ve nerede arayacağını söyler.",
        "",
        "Nabız defteri: `state/mechanism_beats.json` (ad → son damga, epoch saniye).",
        "",
    ]

    for m in mekanizmalar:
        ad = m["ad"]
        belirti = [f"Beklenen azami sessizlik **{_sure(m['pencere_s'])}**; aşılırsa `MECHANISM_STALE` "
                   f"ve sessiz hatta `bekçiler` segmenti açılır *(kaynak: `meridian/watchdog.py::EXPECTED`)*."]
        if m["not"]:
            belirti.append(f"Pencere gerekçesi: {m['not']} *(kaynak: `meridian/watchdog.py`)*")
        if m["gerekce"]:
            belirti.append(f"{m['gerekce']} *(kaynak: `meridian/watchdog.py`)*")

        teshis = []
        yerler = nabizlar.get(ad, [])
        if yerler:
            teshis.append("Nabzı atan kod yolu — **ilk soru bu yolun koşup koşmadığıdır**: "
                          + " · ".join(f"`{y}`" for y in yerler))
        else:
            teshis.append(f"`watchdog.beat(\"{ad}\")` çağrısı kodda BULUNAMADI — mekanizma "
                          "EXPECTED'de bekleniyor ama nabzı atan bir yol yok. Bu, bekçinin kendi "
                          "kör noktasıdır ve bir kablolama bulgusudur.")
        teshis.append("Son damga: `state/mechanism_beats.json` → `" + ad + "`; "
                      "rapor: `watchdog.report()` (panoda Operasyon → bekçi rozeti).")
        for ip in bekci_ipuclari:
            teshis.append(f"{ip} *(kaynak: `meridian/api.py::_sessiz_hat`)*")

        cozum = []
        for b in _eslesen_betikler(ad, betikler):
            cozum.append(f"`{b['yol']}` — başlığında `{ad}` geçiyor.")
        for x in _eslesen_log(ad, log):
            cozum.append(f"**{x['bolum']}** → {x['metin']}")
        p += _bolum(ad, ad, belirti, teshis, cozum)

    # ---- SESSİZ HAT SAPMALARI ------------------------------------------------------------
    p += [
        "---",
        "",
        "# Sessiz hat sapmaları {#sessiz-hat}",
        "",
        "Sessiz hat üç segmenti toplar: **bekçiler** (yukarıdaki mekanizmalar) · **kilitler** ·",
        "**veri**. Kilitler burada Faz-6 kilit zinciri DEĞİLDİR: bunlar DURDURMA kollarıdır,",
        "normal konumları kapalıdır ve açık olmaları bir sapmadır.",
        "",
    ]
    for s in sapmalar:
        belirti = [f"{s['detay']} *(kaynak: `meridian/api.py::_sessiz_hat`)*"] if s["detay"] else []
        teshis = [f"{s['ipucu']} *(kaynak: `meridian/api.py::_sessiz_hat` — sapmanın kendi runbook ipucu)*"]
        cozum = []
        for b in _eslesen_betikler(s["ad"], betikler):
            cozum.append(f"`{b['yol']}` — başlığında `{s['ad']}` geçiyor.")
        for x in _eslesen_log(s["ad"], log):
            cozum.append(f"**{x['bolum']}** → {x['metin']}")
        p += _bolum(s["ad"], s["ad"], belirti, teshis, cozum)

    # ---- BETİK DİZİNİ --------------------------------------------------------------------
    p += [
        "---",
        "",
        "# Betik dizini {#betikler}",
        "",
        "Onaylı kümedeki her betiğin KENDİ başlık sözleşmesi, olduğu gibi. Kod bloğu içinde",
        "veriliyor ki betiğin kendi biçimi (kullanım satırları, kurulum komutları) bozulmasın.",
        "",
    ]
    for b in betikler:
        p += [f"## `{b['yol']}` {{#{capa(b['yol'])}}}", ""]
        if b["baslik"]:
            p += ["```", b["baslik"], "```", ""]
        else:
            p += [f"- **{YAZILMADI}** — betiğin başlık yorumu yok (shebang'dan sonra `#` bloğu "
                  "bulunamadı); betiğin kendi sözleşmesi yazılmamış.", ""]

    # ---- BİLİNEN SINIFLAR ----------------------------------------------------------------
    p += [
        "---",
        "",
        "# Bilinen sınıflar ve açık kalanlar {#siniflar}",
        "",
        "`MERIDIAN_ENGINEERING_LOG.md`'den olduğu gibi taşınır. Bir alarmın açıklaması burada",
        "olabilir: bu depoda tekrar eden şey tek tek hatalar değil, HATA SINIFLARIDIR.",
        "",
    ]
    for baslik in LOG_BOLUMLERI:
        maddeler = [m for m in log if m["bolum"].startswith(baslik)]
        if not maddeler:
            continue
        p += [f"## {maddeler[0]['bolum']} {{#{capa(baslik)}}}", ""]
        p += [f"- {m['metin']}" for m in maddeler]
        p += [""]

    return "\n".join(p).rstrip() + "\n"


# ==================================================================================
# 4) CLI
# ==================================================================================

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="docs/RUNBOOK.md üreticisi (kaynak: kod + ops başlıkları)")
    ap.add_argument("--kontrol", action="store_true",
                    help="yazma; diskteki belge üretilenle aynı mı (çıkış 1 = bayat)")
    ap.add_argument("--cikti", default=str(HEDEF), help="hedef dosya (varsayılan docs/RUNBOOK.md)")
    a = ap.parse_args(argv)
    metin = uret()
    hedef = pathlib.Path(a.cikti)
    if a.kontrol:
        mevcut = hedef.read_text(encoding="utf-8") if hedef.exists() else ""
        if mevcut == metin:
            print(f"GÜNCEL · {hedef} ({len(metin.splitlines())} satır)")
            return 0
        print(f"BAYAT · {hedef} kaynakla ayrışmış — `python ops/runbook_uret.py` ile yeniden üret",
              file=sys.stderr)
        return 1
    hedef.parent.mkdir(parents=True, exist_ok=True)
    hedef.write_text(metin, encoding="utf-8")
    bos = metin.count(YAZILMADI)
    bolum = metin.count("\n## ")
    print(f"yazıldı: {hedef} · {bolum} bölüm · {len(metin.splitlines())} satır · "
          f"{bos} “{YAZILMADI}” girdisi")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
