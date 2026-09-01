"""EDG-2026-067 KIYAS KOŞUMU — donuk soru kümesiyle taban ve Hindsight kollarını ölçer.

NE YAPAR. `sorular.yaml` (DONDURULMUŞ 2026-09-01, kart gereği DEĞİŞTİRİLEMEZ) içindeki her
soruyu iki kola sorar, ÖNDEN DONUK ve MEKANİK bir hakemle sayar, JSON + markdown rapor yazar.

  · TABAN     : `taban_indeks.py` ile kurulmuş sqlite-vec indeksinde top-3.
  · HINDSIGHT : `POST {base}/banks/{bank}/memories/recall`.

HAKEM İKİ SAYIM ÜRETİR, İKİSİ DE RAPORA GİRER:
  (a) dosya-isabet      — ilk 3 sonuçtan birinin belgesi beklenen dosya.
  (b) dosya+bölüm-isabet— (a) VE o sonucun METNİ beklenen `dogrulama` alıntısını YA DA
                          beklenen `bolum` başlığını içeriyor (casefold + boşluk normalize).
ANA METRİK (b)'dir. (a) ayrı sütun olarak KALIR: Hindsight damıtılmış bellek döndürdüğünde
alıntı birebir geçmeyebilir ve tek sayım bu farkı gizlerdi (bedel yasası refleksi).

BU BETİK HÜKÜM VERMEZ. Kart eşikleri (+15 pp · %70 · tr %60) burada HİÇ geçmez; rapor yalnız
sayıları taşır. Eşiğe karşı okuma Rol-1'in işidir — ölçen ile hüküm veren aynı el olmaz.

UYDURMA YASAĞI, ŞEMA TARAFI. Hindsight cevabının `document_id` alanının NEREDE olduğu bu
depoda ÖLÇÜLMEDİ. Betik onu TAHMİN ETMEZ: donuk bir aday-yol listesini dener, KULLANDIĞI YOLU
rapora yazar, ve hiçbir sonuçtan kimlik çıkaramazsa SIFIR RAPOR ETMEZ — düşer ve
`--sema-ornek` koşulmasını söyler. "%0 isabet" ile "şemayı okuyamadım" aynı şey değildir.

ANAHTAR. `--key-file`den okunur, YALNIZ `Authorization` başlığına konur; URL'de, gövdede,
log'da, raporda geçmez. Yazımdan hemen önce `sizinti_denetle` çıktıyı tarar.

KULLANIM
    python kiyas_kos.py --db taban.sqlite --model-dir <bge-m3 onnx> \
        --sorular sorular.yaml --base http://127.0.0.1:8888/v1/default \
        --key-file /opt/hindsight/.key --rapor-dizin rapor/
    python kiyas_kos.py --sema-ornek --sorular sorular.yaml --base ... --key-file ... \
        --rapor-dizin rapor/        # ÖNCE BU: cevabın ham şemasını döker
"""
import argparse
import importlib.util
import json
import math
import pathlib
import re
import time
import urllib.request

_BURASI = pathlib.Path(__file__).resolve().parent


def _kaynaktan_yukle(yol, ad):
    """Kardeş betiği KAYNAKTAN derleyip yükler.

    `loader.exec_module` KULLANILMAZ: `SourceLoader.get_code()` derlemeden önce
    `__pycache__`e bakar ve boyut-koruyan bir düzenleme bayat bytecode'u "geçerli" saydırır
    (ölçülmüş vaka, 2026-08-30 — `ops/sasi_yukleyici.py`). `dont_inherit=True` zorunludur:
    yoksa yüklenen betik BU dosyanın `__future__` ifadelerini miras alır.
    """
    yol = pathlib.Path(yol)
    spec = importlib.util.spec_from_file_location(ad, yol)
    modul = importlib.util.module_from_spec(spec)
    kod = compile(yol.read_text(encoding="utf-8"), str(yol), "exec", dont_inherit=True)
    exec(kod, modul.__dict__)
    return modul


TABAN = _kaynaktan_yukle(_BURASI / "taban_indeks.py", "edg067_taban_indeks_ic")
dokuman_taban = TABAN.dokuman_taban

#: Soru başına kaç sonuç sayılır (kart metriği: isabet@3).
K = 3
# 120 → 360 (ölçüldü 2026-09-01 ~16:00Z): uzun Türkçe soruda recall 129,8 sn sürdü ve 120 sn
# sabiti isteği tam bitmek üzereyken kesti (sunucu logu: RECALL CANCELLED, client disconnected;
# kısa sorgu 3 sn — fark sorgu karmaşıklığı + o saatte tıkalı ücretsiz LLM ucu). İki not daha,
# aynı ölçümden: (a) `limit` parametresini sunucu TANIMIYOR ("Unknown parameters ignored") —
# sunucu varsayılanı döner (23 sonuç), hüküm zaten istemci-tarafı `[:K]` kesmesiyle verilir;
# (b) bu yüzden k'yı sunucuya taşıma girişimi YAPILMAZ.
ZAMAN_ASIMI = 360

#: Hindsight cevabında `document_id`nin ARANDIĞI yollar — SIRALI ve DONUK. Bu bir tahmin
#: DEĞİL bir arama planıdır: hangisinin tuttuğu rapora yazılır, hiçbiri tutmazsa koşum düşer.
KIMLIK_YOLLARI = (
    ("document_id",), ("documentId",), ("doc_id",),
    ("metadata", "document_id"), ("metadata", "doc_id"),
    ("document", "id"), ("document", "document_id"),
    ("source", "document_id"), ("memory", "document_id"),
)
#: Sonucun METNİ — hakem kuralı (b) burada arar.
METIN_YOLLARI = (
    ("content",), ("text",), ("summary",), ("body",), ("passage",),
    ("memory", "content"), ("chunk", "content"), ("metadata", "content"),
)
#: Cevap gövdesinde sonuç listesinin ARANDIĞI anahtarlar.
LISTE_ANAHTARLARI = ("items", "results", "memories", "data", "matches", "recalls")

_BOSLUK = re.compile(r"\s+")


# =================================================================================================
# NORMALİZASYON VE HAKEM
# =================================================================================================
def normalize(metin):
    """Boşluk dizileri tek boşluğa, kırpma, casefold. Üçü de gerekli: markdown sarması
    alıntıyı satır sonundan böler, başlıklar büyük harfle yazılır."""
    return _BOSLUK.sub(" ", str(metin or "")).strip().casefold()


def hakem(sonuclar, beklenen):
    """ÖNDEN DONUK, MEKANİK hüküm — elle yorum yok.

    Dönen: dosya_isabet (a), bolum_isabet (b), ilk3_dosyalar, okunamayan.
    `okunamayan`, belgesi çıkarılamayan sonuçların sayısıdır ve ISKALA SAYILMAZ: ölçülemeyen
    şey ihlal değildir, ama sayılır.
    """
    ilk3 = list(sonuclar)[:K]
    hedef = dokuman_taban(beklenen["dosya"])
    igneler = [normalize(beklenen.get("dogrulama")), normalize(beklenen.get("bolum"))]
    igneler = [i for i in igneler if i]

    dosya_isabet = False
    bolum_isabet = False
    okunamayan = 0
    for sonuc in ilk3:
        belge = sonuc.get("dosya")
        if belge is None:
            okunamayan += 1
            continue
        if dokuman_taban(belge) != hedef:
            continue
        dosya_isabet = True
        govde = normalize(sonuc.get("metin"))
        if govde and any(igne in govde for igne in igneler):
            bolum_isabet = True
            break
    return {"dosya_isabet": dosya_isabet, "bolum_isabet": bolum_isabet,
            "ilk3_dosyalar": [s.get("dosya") for s in ilk3], "okunamayan": okunamayan}


# =================================================================================================
# DONUK SORU KÜMESİ
# =================================================================================================
def sorulari_oku(yol):
    """Şema DOĞRULANARAK okur. Eksik alan sessizce boş dizgeye düşerse o soru hakem kuralı
    (b)'yi hiçbir zaman geçemez ve kol haksız yere kaybeder — Yasa 4 sınıfı bir sessizlik."""
    try:
        import yaml
    except ImportError as e:                # sessiz-yutma DEĞİL: reçeteli hataya çevriliyor
        raise RuntimeError(f"PyYAML kurulu değil ({e}) — A1'de `pip install pyyaml`") from e
    ham = yaml.safe_load(pathlib.Path(yol).read_text(encoding="utf-8"))
    sorular = (ham or {}).get("sorular")
    if not sorular:
        raise ValueError(f"{yol}: `sorular` boş ya da yok")
    gorulen = set()
    for soru in sorular:
        kimlik = soru.get("id")
        if not kimlik:
            raise ValueError(f"{yol}: `id` alanı olmayan soru var")
        if kimlik in gorulen:
            raise ValueError(f"{yol}: id ÇAKIŞMASI: {kimlik}")
        gorulen.add(kimlik)
        for alan in ("dil", "soru", "sinif", "beklenen"):
            if not soru.get(alan):
                raise ValueError(f"{yol}: {kimlik} soru kaydında `{alan}` eksik")
        for alan in ("dosya", "bolum", "dogrulama"):
            if not soru["beklenen"].get(alan):
                raise ValueError(f"{yol}: {kimlik} `beklenen.{alan}` eksik")
    return sorular


# =================================================================================================
# SIR
# =================================================================================================
#: Sızıntı taramasının ANLAMLI olabildiği asgari sır uzunluğu. Bir-iki karakterlik bir "sır"
#: sıradan metinden ayırt edilemez (`"k" in "kart"`), yani tarama sahte kırmızı üretir; kısa
#: anahtarı kabul edip taramayı sessizce işe yaramaz hâle getirmek ise körlüğün ta kendisidir.
#: Ölçülmüş vaka: bu çivi ilk koşumda tek-harfli test anahtarıyla öttü (2026-09-01).
SIR_ASGARI = 8


def anahtar_oku(yol):
    deger = pathlib.Path(yol).read_text(encoding="utf-8").strip()
    if not deger:
        raise ValueError(f"anahtar dosyası BOŞ: {yol}")
    if len(deger) < SIR_ASGARI:
        raise ValueError(
            f"anahtar dosyası ŞÜPHELİ KISA ({len(deger)} karakter, asgari {SIR_ASGARI}): {yol} — "
            f"kırpılmış ya da yanlış dosya olabilir. Bu uzunlukta bir sır, sızıntı taramasında "
            f"sıradan metinden ayırt EDİLEMEZ; koşum sahte kırmızıyla ilerlemez.")
    return deger


def sizinti_denetle(metinler, sir):
    """Yazılacak metinlerde sır ARANIR. Boş/None sır DENETLENEMEZ — `"" in metin` her zaman
    True'dur ve kapıyı sahte kırmızıya boğardı; sessizce yeşil de sayılmaz, çağıran bilir."""
    if not sir:
        return
    for metin in metinler:
        if sir in (metin or ""):
            raise RuntimeError("ANAHTAR SIZINTISI: sır çıktı metninde bulundu — dosya YAZILMADI")


# =================================================================================================
# HINDSIGHT KOLU
# =================================================================================================
def _yoldan_oku(kayit, yol):
    dugum = kayit
    for parca in yol:
        if not isinstance(dugum, dict) or parca not in dugum:
            return None
        dugum = dugum[parca]
    return dugum if isinstance(dugum, str) and dugum else None


def dokuman_kimligi_cikar(kayit):
    """(değer, kullanılan yol) ya da (None, None). Yol RAPORA yazılır — şema ölçülür,
    varsayılmaz."""
    for yol in KIMLIK_YOLLARI:
        deger = _yoldan_oku(kayit, yol)
        if deger is not None:
            return deger, ".".join(yol)
    return None, None


def metin_cikar(kayit):
    for yol in METIN_YOLLARI:
        deger = _yoldan_oku(kayit, yol)
        if deger is not None:
            return deger, ".".join(yol)
    return None, None


def sonuc_listesi(ham):
    if isinstance(ham, list):
        return ham
    if isinstance(ham, dict):
        for anahtar in LISTE_ANAHTARLARI:
            deger = ham.get(anahtar)
            if isinstance(deger, list):
                return deger
    return []


def hindsight_cagir(base, anahtar, bank, soru, k, ek=None):
    """Tek recall çağrısı. Anahtar YALNIZ başlıkta; soru gövdede, URL'de değil."""
    govde = {"query": soru, "limit": k}
    if ek:
        govde.update(ek)
    istek = urllib.request.Request(
        f"{base.rstrip('/')}/banks/{bank}/memories/recall",
        data=json.dumps(govde, ensure_ascii=False).encode("utf-8"),
        method="POST",
        headers={"Authorization": f"Bearer {anahtar}", "Content-Type": "application/json"})
    with urllib.request.urlopen(istek, timeout=ZAMAN_ASIMI) as cevap:
        return sonuc_listesi(json.loads(cevap.read() or b"{}"))


def hindsight_sonuclarini_cevir(ham_sonuclar):
    """Ham kayıtları hakemin anladığı {dosya, metin} biçimine çevirir; kullanılan şema
    yollarını da döndürür (rapora gider)."""
    cevrilmis = []
    yollar = set()
    for kayit in ham_sonuclar:
        kimlik, kimlik_yolu = dokuman_kimligi_cikar(kayit)
        metin, metin_yolu = metin_cikar(kayit)
        if kimlik_yolu:
            yollar.add(f"kimlik={kimlik_yolu}")
        if metin_yolu:
            yollar.add(f"metin={metin_yolu}")
        cevrilmis.append({"dosya": kimlik, "metin": metin})
    return cevrilmis, yollar


# =================================================================================================
# TABAN KOLU
# =================================================================================================
def taban_hazirla(db_yolu, model_dir, *, boyut=None, max_token=None):
    """(künye, ortam, kapat). Ortam = (db, gömücü); kapat çağrılabilir."""
    model = pathlib.Path(model_dir)
    if not model.is_dir():
        raise FileNotFoundError(f"model dizini YOK: {model} — taban kolu koşamaz")
    db_yolu = pathlib.Path(db_yolu)
    if not db_yolu.exists():
        raise FileNotFoundError(f"taban indeksi YOK: {db_yolu} — önce taban_indeks.py koşulmalı")
    gomucu = TABAN.OnnxGomucu(model, **{k: v for k, v in
                                        (("boyut", boyut), ("max_token", max_token))
                                        if v is not None})
    db = TABAN.vec_baglan(db_yolu)
    return TABAN.kunye_oku(db), (db, gomucu), db.close


def taban_sorgu(ortam, soru, k):
    db, gomucu = ortam
    vektor = gomucu([soru])[0]
    return TABAN.en_yakin(db, vektor, k)


# =================================================================================================
# RAPOR
# =================================================================================================
def yuzdelik(degerler, p):
    """Doğrusal ara-değerli yüzdelik. ÖLÇÜM YOKSA None — sıfır ile "bilmiyorum" aynı değildir."""
    d = sorted(x for x in degerler if x is not None)
    if not d:
        return None
    if len(d) == 1:
        return d[0]
    k = (len(d) - 1) * (p / 100.0)
    alt, ust = int(math.floor(k)), int(math.ceil(k))
    if alt == ust:
        return d[alt]
    return d[alt] + (d[ust] - d[alt]) * (k - alt)


def _kesit(satirlar):
    n = len(satirlar)
    return {"n": n,
            "dosya_isabet_3": (sum(1 for s in satirlar if s["dosya_isabet"]) / n) if n else None,
            "bolum_isabet_3": (sum(1 for s in satirlar if s["bolum_isabet"]) / n) if n else None}


def kol_ozeti(satirlar):
    """Genel + dil alt-kümeleri + sınıf alt-kümeleri + gecikme yüzdelikleri.
    BOŞ alt-kümede oran 0 DEĞİL None'dır (uydurma yasağı)."""
    ozet = {"genel": _kesit(satirlar)}
    for dil in ("tr", "en"):
        ozet[dil] = _kesit([s for s in satirlar if s["dil"] == dil])
    for sinif in ("arsiv", "karar", "recete"):
        ozet[f"sinif_{sinif}"] = _kesit([s for s in satirlar if s["sinif"] == sinif])
    gecikmeler = [s.get("gecikme_ms") for s in satirlar]
    ozet["gecikme_ms"] = {"p50": yuzdelik(gecikmeler, 50), "p95": yuzdelik(gecikmeler, 95)}
    ozet["okunamayan_sonuc"] = sum(s.get("okunamayan", 0) for s in satirlar)
    return ozet


def rapor_kur(satirlar, kunye=None, *, ek=None):
    kunye = kunye or {}
    kollar = {}
    for kol in sorted({s["kol"] for s in satirlar}):
        kollar[kol] = kol_ozeti([s for s in satirlar if s["kol"] == kol])

    korpus = {"head_commit": kunye.get("head_commit"),
              "chunk_sayisi": kunye.get("chunk_sayisi"),
              "kurulum_suresi_s": kunye.get("kurulum_suresi_s")}
    for alan, neden in (
            ("head_commit", "taban indeksi künyesi bu koşumda okunmadı (taban kolu koşmadı mı?)"),
            ("chunk_sayisi", "taban indeksi künyesi bu koşumda okunmadı"),
            ("kurulum_suresi_s", "taban indeksi bu koşumda kurulmadı; süre yalnız "
                                 "taban_indeks.py koşumunda ölçülür")):
        if korpus[alan] is None:
            korpus[alan + "_neden"] = neden

    rapor = {
        "kart": "EDG-2026-067",
        "uretim_ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "not": "Bu belge yalnız SAYI taşır. Kart eşikleriyle karşılaştırma Rol-1'e aittir.",
        "soru_sayisi": len({s["id"] for s in satirlar}),
        "korpus": korpus,
        "kollar": kollar,
        "sorular": satirlar,
    }
    if ek:
        rapor.update(ek)
    if {"taban", "hindsight"} <= set(kollar):
        t = kollar["taban"]["genel"]["bolum_isabet_3"]
        h = kollar["hindsight"]["genel"]["bolum_isabet_3"]
        rapor["aritmetik"] = {
            "bolum_isabet_3_fark_pp": round((h - t) * 100, 1) if (t is not None and h is not None)
            else None,
            "not": "yalın çıkarma (hindsight − taban); eşiğe karşı okuma Rol-1'e aittir"}
    return rapor


def _oran(x):
    return "ölçülemedi" if x is None else f"{x * 100:.1f}%"


def _sayi(x, birim=""):
    return "ölçülemedi" if x is None else f"{x:.1f}{birim}"


def rapor_markdown(rapor):
    sat = ["# EDG-2026-067 — recall kıyası ölçüm çıktısı",
           "",
           f"Üretim: {rapor['uretim_ts']} · soru sayısı: {rapor['soru_sayisi']} · "
           f"kart: {rapor['kart']}",
           "",
           f"> {rapor['not']}",
           "",
           "## Korpus / taban indeksi",
           "",
           f"- head_commit: `{rapor['korpus']['head_commit']}`",
           f"- chunk sayısı: {rapor['korpus']['chunk_sayisi']}",
           f"- taban indeks kurulum süresi: "
           f"{_sayi(rapor['korpus']['kurulum_suresi_s'], ' sn')}"]
    for alan in ("head_commit", "chunk_sayisi", "kurulum_suresi_s"):
        neden = rapor["korpus"].get(alan + "_neden")
        if neden:
            sat.append(f"  - `{alan}` ölçülemedi — {neden}")

    sat += ["", "## Kol özetleri", "",
            "| kol | n | dosya-isabet@3 | bölüm-isabet@3 | tr bölüm@3 | en bölüm@3 | "
            "p50 ms | p95 ms | okunamayan |",
            "|---|---|---|---|---|---|---|---|---|"]
    for kol, ozet in rapor["kollar"].items():
        sat.append(
            f"| {kol} | {ozet['genel']['n']} | {_oran(ozet['genel']['dosya_isabet_3'])} | "
            f"{_oran(ozet['genel']['bolum_isabet_3'])} | {_oran(ozet['tr']['bolum_isabet_3'])} | "
            f"{_oran(ozet['en']['bolum_isabet_3'])} | {_sayi(ozet['gecikme_ms']['p50'])} | "
            f"{_sayi(ozet['gecikme_ms']['p95'])} | {ozet['okunamayan_sonuc']} |")

    if "aritmetik" in rapor:
        fark = rapor["aritmetik"]["bolum_isabet_3_fark_pp"]
        sat += ["", f"Bölüm-isabet@3 farkı (hindsight − taban): "
                    f"{'ölçülemedi' if fark is None else f'{fark:+.1f} pp'} — "
                    f"{rapor['aritmetik']['not']}."]

    sat += ["", "## Sınıf alt-kümeleri", "",
            "| kol | arşiv | karar | reçete |", "|---|---|---|---|"]
    for kol, ozet in rapor["kollar"].items():
        sat.append(f"| {kol} | {_oran(ozet['sinif_arsiv']['bolum_isabet_3'])} | "
                   f"{_oran(ozet['sinif_karar']['bolum_isabet_3'])} | "
                   f"{_oran(ozet['sinif_recete']['bolum_isabet_3'])} |")

    sat += ["", "## Soru başına", "",
            "| id | dil | sınıf | kol | dosya-isabet | bölüm-isabet | dönen ilk-3 | ms |",
            "|---|---|---|---|---|---|---|---|"]
    for s in rapor["sorular"]:
        donen = ", ".join(str(d) for d in s["ilk3_dosyalar"]) or "—"
        sat.append(f"| {s['id']} | {s['dil']} | {s['sinif']} | {s['kol']} | "
                   f"{'✔' if s['dosya_isabet'] else '✘'} | "
                   f"{'✔' if s['bolum_isabet'] else '✘'} | {donen} | "
                   f"{_sayi(s.get('gecikme_ms'))} |")
    return "\n".join(sat) + "\n"


# =================================================================================================
# KOMUT SATIRI
# =================================================================================================
def _sema_ornegi(a, anahtar, sorular, rapor_dizin):
    """TEK örnek çağrı: ham cevabı döker. Şema BURADA ölçülür, kodda varsayılmaz."""
    ham = hindsight_cagir(a.base, anahtar, a.bank, sorular[0]["soru"], a.k, _ek_json(a))
    _, yollar = hindsight_sonuclarini_cevir(ham)
    cikti = json.dumps({"soru_id": sorular[0]["id"], "sonuc_sayisi": len(ham),
                        "bulunan_yollar": sorted(yollar), "ham": ham},
                       ensure_ascii=False, indent=1)
    sizinti_denetle([cikti], anahtar)
    hedef = rapor_dizin / "sema_ornegi.json"
    hedef.write_text(cikti, encoding="utf-8")
    print(f"şema örneği yazıldı: {hedef} · sonuç={len(ham)} · yollar={sorted(yollar)}")
    return 0


def _ek_json(a):
    return json.loads(a.recall_ek_json) if a.recall_ek_json else None


def main(argv=None):
    ap = argparse.ArgumentParser(description="EDG-067 taban/Hindsight recall kıyası")
    # VARSAYILANLAR BETİĞİN YANINDAN: donuk soru kümesi betikle birlikte taşınır (A1 kopyası
    # da öyle), rapor da kartın beklediği `rapor/` dizinine düşer. İkisi de override edilebilir.
    ap.add_argument("--sorular", default=str(_BURASI / "sorular.yaml"))
    ap.add_argument("--rapor-dizin", default=str(_BURASI / "rapor"))
    ap.add_argument("--kollar", default="taban,hindsight")
    ap.add_argument("--k", type=int, default=K)
    ap.add_argument("--db")
    ap.add_argument("--model-dir")
    ap.add_argument("--base")
    ap.add_argument("--key-file")
    ap.add_argument("--bank", default="meridian-arsiv")
    ap.add_argument("--recall-ek-json", default=None,
                    help="recall gövdesine eklenecek JSON (şema farklıysa)")
    ap.add_argument("--sema-ornek", action="store_true",
                    help="tek örnek recall çağrısının HAM cevabını döker ve çıkar")
    a = ap.parse_args(argv)

    kollar = [k.strip() for k in a.kollar.split(",") if k.strip()]
    bilinmeyen = [k for k in kollar if k not in ("taban", "hindsight")]
    if bilinmeyen:
        raise SystemExit(f"bilinmeyen kol: {bilinmeyen}")
    sorular = sorulari_oku(a.sorular)
    rapor_dizin = pathlib.Path(a.rapor_dizin)
    rapor_dizin.mkdir(parents=True, exist_ok=True)

    anahtar = None
    if "hindsight" in kollar or a.sema_ornek:
        if not (a.base and a.key_file):
            raise SystemExit("hindsight kolu için --base ve --key-file gerekli")
        anahtar = anahtar_oku(a.key_file)
    if a.sema_ornek:
        return _sema_ornegi(a, anahtar, sorular, rapor_dizin)

    kunye, ortam, kapat = {}, None, None
    if "taban" in kollar:
        if not (a.db and a.model_dir):
            raise SystemExit("taban kolu için --db ve --model-dir gerekli")
        kunye, ortam, kapat = taban_hazirla(a.db, a.model_dir)

    satirlar = []
    sema_yollari = set()
    hindsight_sonuc_toplam = 0
    hindsight_kimlik_okunan = 0
    try:
        for soru in sorular:
            for kol in kollar:
                t0 = time.perf_counter()
                if kol == "taban":
                    sonuclar = taban_sorgu(ortam, soru["soru"], a.k)
                else:
                    try:
                        ham = hindsight_cagir(a.base, anahtar, a.bank, soru["soru"], a.k,
                                              _ek_json(a))
                    except Exception as e:
                        # YUTMA DEĞİL, BAĞLAMLANDIRMA: düşen bir çağrı "0 sonuç" SAYILMAZ —
                        # sayılsaydı ağ arızası ıskala gibi görünür ve kol haksız kaybederdi.
                        # Koşum yarım bırakılır; yarım sayım rapor edilmez.
                        raise RuntimeError(
                            f"{soru['id']} recall çağrısı düştü ({type(e).__name__}: {e}) — "
                            f"koşum YARIM bırakıldı, rapor YAZILMADI") from e
                    sonuclar, yollar = hindsight_sonuclarini_cevir(ham)
                    sema_yollari |= yollar
                    hindsight_sonuc_toplam += len(sonuclar)
                    hindsight_kimlik_okunan += sum(1 for s in sonuclar if s["dosya"] is not None)
                gecikme = (time.perf_counter() - t0) * 1000.0
                hukum = hakem(sonuclar, soru["beklenen"])
                satirlar.append({"id": soru["id"], "dil": soru["dil"], "sinif": soru["sinif"],
                                 "kol": kol, "gecikme_ms": round(gecikme, 1), **hukum})
    finally:
        if kapat:
            kapat()

    if "hindsight" in kollar and hindsight_kimlik_okunan == 0:
        raise RuntimeError(
            f"HINDSIGHT ŞEMASI OKUNAMADI: {hindsight_sonuc_toplam} sonuçtan hiçbirinde "
            f"document_id bulunamadı (denenen yollar: "
            f"{['.'.join(y) for y in KIMLIK_YOLLARI]}). Bu SIFIR İSABET DEĞİLDİR — rapor "
            f"yazılmadı. Önce `--sema-ornek` ile ham cevabı dök, alan yolunu ölç, "
            f"KIMLIK_YOLLARI'na ekle.")

    ek = {"hindsight_sema_yollari": sorted(sema_yollari) or None} if "hindsight" in kollar else None
    rapor = rapor_kur(satirlar, kunye, ek=ek)
    damga = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    json_metin = json.dumps(rapor, ensure_ascii=False, indent=1)
    md_metin = rapor_markdown(rapor)
    sizinti_denetle([json_metin, md_metin], anahtar)
    (rapor_dizin / f"edg067_kiyas_{damga}.json").write_text(json_metin, encoding="utf-8")
    (rapor_dizin / f"edg067_kiyas_{damga}.md").write_text(md_metin, encoding="utf-8")
    print(f"rapor yazıldı: {rapor_dizin}/edg067_kiyas_{damga}.{{json,md}} · "
          f"{len(satirlar)} satır · kollar={kollar}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
