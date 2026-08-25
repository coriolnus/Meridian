"""v280 · M11 KOVA-6 — PANO DEĞER-KÖRLÜĞÜ + `entry_law` ÇÜRÜK BEYANI.

Kaynak ölçüm: `docs/TARAMA-KOVA6-ALAN-MERCEGI-2026-08-24.md` §2.2 (T-2) ve §4.
Bulgular bu turda BAĞIMSIZ olarak yeniden ölçüldü (kör uygulama yok) — aşağıdaki iki kusur
kaynak koddan doğrulandı:

(1) DEĞER-KÖRLÜĞÜ. `loop.py` bir silahlı planın kaybolma sebebini plan defterine `broker_status`
    alanıyla yazar ve ÜÇ değer üretir: `failed_broker_rejection` (`loop` pano-dürüstlük bloğu/852),
    `gap_veto` (loop.py:813) ve `armed_dropped_<kapı>` (loop.py:332, f-string). Pano yalnız
    BİRİNCİSİNİ tanıyordu: `nextSessionCard`in `else` dalı diğer HER değeri nötr/olumlu
    "gönderilecek" rozetiyle çiziyor, `_durumEmirKarti` ise `bekleyen = silahlı − gönderilen −
    ret` aritmetiğiyle onları "gönderilecekte kaldı" sayacına yazıyordu. Yani gap-vetosuyla ya da
    HALT/kesici kapısıyla DÜŞÜRÜLMÜŞ bir plan panoda "gönderilecek" görünürdü. Plan çekmecesinde
    (`RECORD_VIEW.plan`) aynı körlük TERS yönde: `pdRow` boş değeri satır BASMADAN yutar, yani
    düşme sebebi hiç görünmezdi — oysa o damga tam "defterden okunabilsin" diye eklenmişti
    (`SISTEM-DENETIMI-2026-08-02` #14/#16'nın düzeltmesi). Yazan bacak indi, okuyan bacak inmedi.

    Bugün SOĞUK bir kusurdur (41 günlük olay penceresinde `armed_dropped` 0, `entry_gap_veto` 0),
    bu yüzden davranış SENTETİK veriyle sınanır — canlı örnek beklemek çiviyi süresiz ertelerdi.

(2) ÇÜRÜK BEYAN. `entry_law` yan tablosunun dört alt-alanı (`olay`, `offset_kaynak`, `ref_kaynak`,
    `limit_bps`) `broker.entry_order_decision`da ÜRETİLİR ve `portfolio.json`a yazılır, ama
    ÜRETİMDE HİÇ OKUNMAZ; tek tüketicileri testlerdir. İkisi ayrıca kodun kendi yorumunda
    "okuyucusu E2 defteri" diye BEYAN EDİLİYORDU — oysa `loop._entry_exec_write` çağrıları
    `_law_out`tan yalnız `limit/atr/law/mode/tif/gap_at_submit` alanlarını seçer; bu dört alan
    E2 satırına HİÇ girmez (canlı `entry_execution.jsonl` 30 satırının alan listesi de onları
    taşımıyor — tarama §4). Beyan çürüktü.

BU DOSYA NEYİ ÇİVİLER
---------------------
A. `aynaDurumu` — DEĞER-FARKINDALI rozet sözleşmesi, Node'da GERÇEKTEN koşturularak
   (v194/v198/v239 deseni: kaynak-metin çivisi "kod değişti mi"yi ölçer, davranış çivisi
   "kod ne diyor"u).
B. POZİTİF KONTROL — tanınmayan bir durum değeri sessizce "gönderilecek" OLAMAZ; ham basılır ve
   "tanınmayan" işareti taşır (v196/v197 emisyon disiplini). Karşı-yönlü kontrol de var: temiz
   plan GERÇEKTEN "gönderilecek" demeli, yoksa rozeti sabit "düştü" yapmak testi yeşil bırakırdı.
C. SAYAÇ — `bekleyen` yalnız damgasız/gönderilmemiş planları sayar; veto/düşme/bilinmeyen
   kovaları DIŞARIDA. Eski aritmetiğin mezar taşı da burada.
D. ÜRETİCİ↔TÜKETİCİ DEĞER EŞLEŞMESİ (taramanın R2 onarımının kalıcı hâli) — `loop.py`nin ürettiği
   HER `broker_status` değeri panonun sözlüğünde bir karşılık bulmalı.
E. `entry_law` beyan çivisi — çürük ifade geri gelirse kırmızı; damga ile GERÇEK (üretimde okuyucu
   var mı) iki yönlü bağlanır: alan bir gün gerçekten bağlanırsa damga bayatlar ve test kırmızıya
   döner (Ö-49 bayat-beyan sınıfı bir daha sessizce doğmasın).
"""
from __future__ import annotations

import io
import json
import pathlib
import re
import shutil
import subprocess
import tempfile
import tokenize

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
APPJS = (REPO / "meridian" / "web" / "app.js").read_text()
BROKER = (REPO / "meridian" / "broker.py").read_text()
LOOP = (REPO / "meridian" / "loop.py").read_text()

NODE = shutil.which("node")

# `entry_law` yan tablosunun ÜRETİLEN ama üretimde OKUNMAYAN alt-alanları (tarama §4).
OLU_ENTRY_LAW_ALANLARI = ("olay", "offset_kaynak", "ref_kaynak", "limit_bps")


def _yorumsuz_py(src: str) -> str:
    """Python kaynağından YORUM belirteçlerini SİLER, kalan metni AYNEN korur (boşlukla doldurur).

    Beyan çivisi kodu ölçer, yorumu değil: bir alanın adı yorumda geçiyor diye "okunuyor"
    saymak, tam da bu dosyanın kapattığı çürük-beyan kusurunun tersini üretirdi.

    NEDEN "BOŞLUKLA DOLDUR" DA "BELİRTEÇLERİ BİRLEŞTİR" DEĞİL: f-string'ler Python 3.12+'da
    parçalı belirteçlere ayrılır (`f"armed_dropped_{gate}"` → 5+ belirteç). Birleştirilmiş metinde
    literal KAYBOLUR ve alt-dizge çivileri sessizce kör kalırdı."""
    satirlar = src.splitlines(keepends=True)
    try:
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type != tokenize.COMMENT:
                continue
            i, (a, b) = tok.start[0] - 1, (tok.start[1], tok.end[1])
            satirlar[i] = satirlar[i][:a] + " " * (b - a) + satirlar[i][b:]
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return src        # ayrıştırılamadıysa HAM kaynağa düş: çivi kör kalmaz, fazla sıkı olur
    return "".join(satirlar)


# ====================== A · DEĞER-FARKINDALI ROZET — YAPISAL ÇİVİLER ======================

def test_a1_deger_kor_else_dali_mezar_tasi():
    """MEZAR TAŞI: "failed_broker_rejection değilse gönderilecek" biçimi geri gelemez."""
    kod = "\n".join(l for l in APPJS.splitlines() if not l.lstrip().startswith("//"))
    assert 'p.broker_status === "failed_broker_rejection" ? \'<span class="tag t-no">RET</span>\'' \
        not in kod, "değer-kör ikili rozet (RET / gönderilecek) nüksetti — tarama §2.2 / T-2"
    assert "function aynaDurumu(bs, gonderildi)" in kod, \
        "değer-farkındalı durum yardımcısı kaybolmuş"
    # "gönderilecek" ibaresi TEK bir yerde doğabilmeli: damgasız planın dalı.
    n = kod.count('"gönderilecek"')
    assert n == 1, f'"gönderilecek" {n} yerde üretiliyor — ikinci (değer-kör) bir yol açılmış'


def test_a2_rozet_uc_uretici_degerini_de_taniyor():
    govde = re.search(r"function aynaDurumu\(bs, gonderildi\) \{(.*?)\n\}", APPJS, re.S)
    assert govde, "aynaDurumu gövdesi bulunamadı"
    g = govde.group(1)
    for deger in ("failed_broker_rejection", "gap_veto", "armed_dropped_"):
        assert deger in g, f"rozet `{deger}` değerini tanımıyor — üretici onu YAZIYOR (loop.py)"


def test_a3_sayac_eski_aritmetigi_mezar_tasi():
    """`bekleyen = silahlı − gönderilen − ret` düşürülmüş planı "bekleyen" sayardı."""
    kod = "\n".join(l for l in APPJS.splitlines() if not l.lstrip().startswith("//"))
    assert "armed.length - gonderilen - ret" not in kod, \
        "değer-kör `bekleyen` aritmetiği nüksetti — veto/düşme yine 'gönderilecekte kaldı' sayılır"
    assert "function aynaSayaclari(armed, gonderilmisIdler)" in kod, \
        "değer-farkındalı sayaç yardımcısı kaybolmuş"


def test_a4_plan_cekmecesi_dusme_sebebini_yutmuyor():
    """`pdRow` boş değeri satır BASMADAN yutar: eski hâlde gap-vetolu planın çekmecesinde
    'Ayna' satırı hiç görünmüyordu — damga tam bunun için yazılmıştı."""
    kod = "\n".join(l for l in APPJS.splitlines() if not l.lstrip().startswith("//"))
    assert 'pdRow("Ayna", p.broker_status === "failed_broker_rejection" ? "broker reddetti" : "")' \
        not in kod, "plan çekmecesi yine yalnız broker reddini tanıyor (diğer damgalar yutuluyor)"
    assert 'pdRow("Ayna", aynaDurumu(p.broker_status, false).uzun)' in kod, \
        "plan çekmecesi durum sözlüğünü kullanmıyor"


# ====================== A/B/C · DAVRANIŞ — NODE'DA GERÇEKTEN KOŞTURULUR ======================

def _js_kaynak() -> str:
    """`aynaDurumu` + `aynaSayaclari` + bağlı olduğu sözlük — saf, DOM'suz parça."""
    sozluk = re.search(r"(const AYNA_KAPI_TR = \{.*?\};)", APPJS, re.S)
    f1 = re.search(r"(function aynaDurumu\(bs, gonderildi\) \{.*?\n\})", APPJS, re.S)
    f2 = re.search(r"(function aynaSayaclari\(armed, gonderilmisIdler\) \{.*?\n\})", APPJS, re.S)
    assert sozluk, "AYNA_KAPI_TR sözlüğü bulunamadı"
    assert f1, "aynaDurumu gövdesi bulunamadı"
    assert f2, "aynaSayaclari gövdesi bulunamadı"
    return "\n".join((sozluk.group(1), f1.group(1), f2.group(1)))


def _node_kos(cagri: str):
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as fh:
        fh.write(_js_kaynak() + f"\nconsole.log(JSON.stringify({cagri}));\n")
        yol = fh.name
    try:
        r = subprocess.run([NODE, yol], capture_output=True, text=True, timeout=30)
    finally:
        pathlib.Path(yol).unlink(missing_ok=True)
    assert r.returncode == 0, f"node koşmadı: {r.stderr[:500]}"
    return json.loads(r.stdout.strip())


# (broker_status, gönderildi mi) → (kova, rozet metni, tanınmıyor mu)
DOGRULUK = [
    # POZİTİF KONTROL: damgasız plan GERÇEKTEN "gönderilecek" demeli — yoksa rozeti sabit
    # "düştü" yapmak bütün negatif hükümleri yeşil bırakırdı.
    (None, False, "bekleyen", "gönderilecek", False),
    ("", False, "bekleyen", "gönderilecek", False),
    # Aynaya gerçekten gitmiş plan: damga ne olursa olsun "aynada".
    (None, True, "aynada", "aynada", False),
    # Bilinen üç üretici değeri — hiçbiri "bekleyen" DEĞİL, hiçbiri "gönderilecek" DEMİYOR.
    ("failed_broker_rejection", False, "ret", "RET", False),
    ("gap_veto", False, "dusen", "VETO: gap", False),
    ("armed_dropped_halt", False, "dusen", "DÜŞTÜ: halt", False),
    ("armed_dropped_breaker", False, "dusen", "DÜŞTÜ: kesici", False),
    ("armed_dropped_data_bad", False, "dusen", "DÜŞTÜ: veri arızası", False),
    ("armed_dropped_throttle", False, "dusen", "DÜŞTÜ: kısma", False),
    ("armed_dropped_slot_full", False, "dusen", "DÜŞTÜ: slot dolu", False),
    ("armed_dropped_already_open", False, "dusen", "DÜŞTÜ: açık pozisyon", False),
    # TANINMAYAN KAPI ADI: düşme KESİN (önek tanınıyor), kapı adı ham basılır + işaretlenir.
    ("armed_dropped_yeni_kapi", False, "dusen", "DÜŞTÜ: yeni_kapi ?", True),
    # TAM TANINMAYAN DEĞER: sessiz "gönderilecek" varsayımı YASAK — ham + işaret.
    ("bilinmeyen_damga", False, "bilinmeyen", "bilinmeyen_damga ?", True),
]


@pytest.mark.skipif(NODE is None, reason="node yok — yapısal çiviler (a1-a4) yine koşuyor")
@pytest.mark.parametrize("bs,gonderildi,kova,metin,taninmiyor", DOGRULUK)
def test_b1_rozet_dogruluk_tablosu(bs, gonderildi, kova, metin, taninmiyor):
    out = _node_kos(f"aynaDurumu({json.dumps(bs)}, {json.dumps(gonderildi)})")
    assert out["kova"] == kova, f"{bs!r} → {out}"
    assert out["kisa"] == metin, f"{bs!r} → {out['kisa']!r}"
    assert out["taninmiyor"] is taninmiyor, f"{bs!r} → {out}"
    assert out["sinif"], "rozet sınıfı boş — durum kendi mürekkebiyle çizilemez"


@pytest.mark.skipif(NODE is None, reason="node yok")
@pytest.mark.parametrize("bs", ["gap_veto", "armed_dropped_halt", "armed_dropped_slot_full",
                                "failed_broker_rejection", "bilinmeyen_damga"])
def test_b2_hicbir_damgali_plan_gonderilecek_demiyor(bs):
    """ASIL İDDİA: damgalı bir plan panoda ASLA nötr/olumlu okunamaz."""
    out = _node_kos(f"aynaDurumu({json.dumps(bs)}, false)")
    assert "gönderilecek" not in out["kisa"], f"{bs} → {out['kisa']!r}"
    assert out["kova"] != "bekleyen", f"{bs} `bekleyen` kovasında — sayaç yine yalan söyler"
    assert out["uzun"], f"{bs} için çekmece metni boş — pdRow satırı yutar, sebep GÖRÜNMEZ"


@pytest.mark.skipif(NODE is None, reason="node yok")
def test_c1_sayaclar_veto_ve_dusmeyi_bekleyenden_disliyor():
    armed = [{"id": "p1", "broker_status": None},                     # bekleyen
             {"id": "p2", "broker_status": None},                     # aynada (gönderilmiş)
             {"id": "p3", "broker_status": "gap_veto"},               # düştü
             {"id": "p4", "broker_status": "armed_dropped_halt"},     # düştü
             {"id": "p5", "broker_status": "failed_broker_rejection"},  # ret
             {"id": "p6", "broker_status": "bilinmeyen_damga"}]       # tanınmayan
    out = _node_kos(f"aynaSayaclari({json.dumps(armed)}, {json.dumps(['p2'])})")
    assert out == {"gonderilen": 1, "bekleyen": 1, "ret": 1, "dusen": 2, "taninmayan": 1}, out


@pytest.mark.skipif(NODE is None, reason="node yok")
def test_c2_temiz_silahli_kume_hepsini_bekleyen_sayar():
    """POZİTİF KONTROL: sayaç sabit sıfır yapılarak yeşile boyanamaz."""
    armed = [{"id": "a"}, {"id": "b"}, {"id": "c"}]
    out = _node_kos(f"aynaSayaclari({json.dumps(armed)}, [])")
    assert out["bekleyen"] == 3 and out["dusen"] == 0 and out["taninmayan"] == 0, out


# ====================== D · ÜRETİCİ ↔ TÜKETİCİ DEĞER EŞLEŞMESİ (R2 kalıcı hâli) ==============

def test_d1_uretilen_her_broker_status_degeri_panoda_taniniyor():
    """Taramanın R2 onarımı kalıcı bir çiviye dönüşür: alan-düzeyi eşleşme YETMEZ, DEĞER düzeyinde
    eşleşme gerekir. Üretici yeni bir damga eklerse pano onu tanımak ZORUNDA."""
    kod = _yorumsuz_py(LOOP)
    uretilen = set(re.findall(r'broker_status"?\]?\s*[:=]\s*"([a-z_]+)"', kod))
    assert uretilen, "loop.py'de broker_status literali bulunamadı — çivi kör kaldı"
    govde = re.search(r"function aynaDurumu\(bs, gonderildi\) \{(.*?)\n\}", APPJS, re.S)
    assert govde, "aynaDurumu gövdesi bulunamadı"
    for d in uretilen:
        assert d in govde.group(1), (
            f"loop.py `{d}` damgası üretiyor ama pano tanımıyor — değer-düzeyi ölü dal (§2.2)")


def test_d2_armed_dropped_oneki_ve_kapi_adlari_karsilaniyor():
    """`armed_dropped_<kapı>` bir f-string'dir; önek jenerik karşılanır, bilinen kapı adları da
    sözlükte olmalı (yoksa operatör 'DÜŞTÜ: data_bad' gibi ham bir anahtar okur)."""
    kod = _yorumsuz_py(LOOP)
    assert 'f"armed_dropped_{' in kod, (
        "üretici damga biçimi değişmiş — pano öneki artık yanlış yerde arıyor olabilir")
    sozluk = re.search(r"const AYNA_KAPI_TR = \{(.*?)\};", APPJS, re.S)
    assert sozluk, "AYNA_KAPI_TR sözlüğü bulunamadı"
    taninan = set(re.findall(r"(\w+):", sozluk.group(1)))
    kod = _yorumsuz_py(LOOP)
    kapilar: set[str] = set()
    m = re.search(r"_kapi = \((.*?)\)\n", kod, re.S)
    if m:
        kapilar |= set(re.findall(r'"([a-z_]+)"', m.group(1)))
    # `_armed_drop_row(pl, dstr, <kapı>, …)` — YALNIZ ÜÇÜNCÜ konumsal argüman okunur. Kaba bir
    # "çağrının çevresindeki N karakter" penceresi `ticker=`/olay adı gibi ALAKASIZ literalleri de
    # toplardı (ad çakışması tuzağı, §1.2/2).
    for c in re.finditer(r"_armed_drop_row\(", kod):
        i, derinlik, arg, args = c.end(), 1, [], []
        while i < len(kod) and derinlik:
            ch = kod[i]
            if ch in "([{":
                derinlik += 1
            elif ch in ")]}":
                derinlik -= 1
                if not derinlik:
                    break
            if ch == "," and derinlik == 1:
                args.append("".join(arg)); arg = []
            else:
                arg.append(ch)
            i += 1
        args.append("".join(arg))
        if len(args) >= 3:
            kapilar |= set(re.findall(r'"([a-z_]+)"', args[2]))
    eksik = {k for k in kapilar if k not in taninan}
    assert not eksik, f"üretici kapı adları panoda karşılıksız: {sorted(eksik)}"


def test_d3_iki_kapi_sozlugu_ayni_anahtarlari_tasir():
    """PANODA KAPI ADLARININ İKİ SÖZLÜĞÜ VAR ve bu bilinçlidir (biri 92px rozet metni, öteki
    icra masasının tam satır etiketi — aynı SÖZCÜK DAĞARCIĞI, farklı UZUNLUK). Tehlike: yeni bir
    kapı adı yalnız BİRİNE eklenirse öteki yüzey ham anahtar basar. Bu turun kapattığı kusurun
    (yazan bacak indi, okuyan bacak inmedi) tam kardeşi — o yüzden anahtar kümeleri çivilenir."""
    a = re.search(r"const AYNA_KAPI_TR = \{(.*?)\};", APPJS, re.S)
    b = re.search(r"const KAPI_TR = \{(.*?)\};", APPJS, re.S)
    assert a and b, "iki kapı sözlüğünden biri bulunamadı"
    ka = set(re.findall(r"(\w+):", a.group(1)))
    kb = set(re.findall(r"(\w+):", b.group(1)))
    assert ka and kb, "kapı sözlükleri boş ayrıştı — çivi kör kaldı"
    assert ka == kb, (
        f"iki kapı sözlüğü ayrıştı — yalnız birinde olanlar: {sorted(ka ^ kb)}; "
        "bir kapı adı tek yüzeye eklenmiş, öteki ham anahtar basacak")


# ====================== E · `entry_law` BEYAN ÇİVİSİ ======================

def test_e1_curuk_beyan_mezar_tasi():
    """MEZAR TAŞI: çürük ifade geri gelemez — E2 satırı bu alanları TAŞIMIYOR
    (`loop._entry_exec_write` çağrıları `_law_out`tan yalnız limit/atr/law/mode/tif/gap seçer).

    İFADE ALINTILANARAK BİLE YAZILAMAZ: bir alt-dizge çivisi, düzeltme metni yasaklı ifadeyi
    tırnak içinde tekrar ederse KÖR kalır. Düzeltme olguyu ANLATIR, ifadeyi kopyalamaz."""
    assert "okuyucusu E2 defteri" not in BROKER, (
        "çürük beyan nüksetti: `offset_kaynak`ın okuyucusu E2 defteri DEĞİL (tarama §4)")


DAMGA_BASI = "── ÖLÜ-ALAN DAMGASI[M11]"


def test_e2_dort_alan_olu_damgasi_tasiyor():
    """DAMGA: alanlar KALDIRILMADI (şema kararı Rol-1'in), ama gerçek durumları yazılı."""
    assert DAMGA_BASI in BROKER, "M11 ölü-alan damga BLOĞU yok (yalnız atıf yeterli değil)"
    damga = BROKER.split(DAMGA_BASI, 1)[1][:2200]
    for alan in OLU_ENTRY_LAW_ALANLARI:
        assert alan in damga, f"damga `{alan}` alanını adlandırmıyor"
    # BÜYÜK/KÜÇÜK HARF ÖNEMSİZ: çivi İDDİAyı ölçer, vurguyu değil. `İ`.lower() Python'da
    # birleşik noktalı `i̇` verir (Türkçe nokta tuzağı) — normalize edilmezse çivi kör kalırdı.
    duz = damga.replace("İ", "i").lower()
    assert "üretimde okunmaz" in duz, "damga gerçek durumu ('üretimde okunmaz') söylemiyor"
    assert "test" in duz, "damga tek tüketiciyi (testler) adlandırmıyor"


def _uretim_okuyuculari(alan: str) -> list[str]:
    """`meridian/` altında alanı OKUYAN üretim satırları (yorumlar hariç, yazım literali hariç).

    SÖZCÜK SINIRI ZORUNLU: çıplak `.olay` deseni `e.olay_sayaci` / `rb.olaylar` gibi TAMAMEN
    AYRI alanları yakalıyordu — ad çakışması taramanın kendi kalıntı kusurlarından biri (§1.2/2)
    ve burada da aynı tuzağa düşerdi."""
    a = re.escape(alan)
    py_pat = re.compile(rf"""\[\s*['"]{a}['"]\s*\]|\.(?:get|pop|setdefault)\(\s*['"]{a}['"]""")
    js_pat = re.compile(rf"""\[\s*['"]{a}['"]\s*\]|\.{a}\b""")
    hits: list[str] = []
    for f in sorted((REPO / "meridian").rglob("*.py")):
        for i, l in enumerate(_yorumsuz_py(f.read_text()).splitlines(), 1):
            if py_pat.search(l):
                hits.append(f"{f.name}:{i}")
    for f in sorted((REPO / "meridian" / "web").glob("*.js")):
        kod = [l for l in f.read_text().splitlines() if not l.lstrip().startswith("//")]
        for i, l in enumerate(kod, 1):
            if js_pat.search(l):
                hits.append(f"{f.name}:{i}")
    return hits


@pytest.mark.parametrize("alan", OLU_ENTRY_LAW_ALANLARI)
def test_e3_damga_gercekle_iki_yonlu_bagli(alan):
    """İKİ YÖNLÜ: alan bir gün GERÇEKTEN üretime bağlanırsa damga bayatlar ve bu test kırmızıya
    döner — beyan-çürümesi (Ö-49) sessizce geri doğmasın. Bugünkü ölçüm: sıfır üretim okuyucusu."""
    okuyucular = _uretim_okuyuculari(alan)
    assert not okuyucular, (
        f"`{alan}` artık üretimde okunuyor ({okuyucular}) — `broker.py`deki ÖLÜ-ALAN DAMGASI[M11] "
        f"BAYATLADI; damgayı güncelle (alan artık ölü değil)")


def test_e4_e2_defteri_bu_alanlari_hala_yazmiyor():
    """Damganın dayandığı OLGU: E2 satırı bu alanları taşımıyor. Taşımaya başlarsa damga yanlış
    olur — o gün bu test kırmızı yanar ve beyan tazelenir."""
    kod = _yorumsuz_py(LOOP)
    for alan in ("offset_kaynak", "ref_kaynak"):
        assert f'"{alan}"' not in kod, (
            f"`{alan}` artık loop.py'de geçiyor — E2 defterine yazılıyorsa damga bayatladı")


# ====================== F · PLAN DEFTERİ ALAN DAMGALARI (Ö-5…Ö-8) ======================
#
# Kaynak öneri: `docs/TARAMA-KOVA6-ALAN-MERCEGI-2026-08-24.md` §7 Ö-5…Ö-8. Kalıp §E'nin
# BİREBİR kardeşi: damga METNİ çivilenir + damganın DAYANDIĞI OLGU ayrıca çivilenir, böylece
# alan bir gün gerçekten üretime bağlanırsa (ya da bağı KESİLİRSE) damga BAYATLAR ve test
# kırmızıya döner. Şema alanı KALDIRILMAZ, davranış DEĞİŞMEZ (test_differential_v60 yeşil kalır).
#
# Ö-7'DE BAĞIMSIZ ÖLÇÜM TARAMAYI DÜZELTTİ (kör uygulama yok — bkz. damga ve belge §7 şerhi):
# taramanın 13. satırı `sector`ü "davranış? HAYIR" diye sınıflamıştı, ama `guard.py`nin CANLI
# sert kapısı (`sector_cap`, POZİSYON SAYISI tavanı) plan alanını KOŞULSUZ okur. Uyuyan olan
# İKİNCİ tavandır (`portfolio.sector_cap`, NOTIONAL payı). Damga bu ayrımı yazar; aşağıdaki iki
# çivi de iki yarımı ayrı ayrı tutar.

DAMGA_BASLARI = {
    "Ö-5": "── ALAN DAMGASI[M11·Ö-5]",
    "Ö-6": "── ALAN DAMGASI[M11·Ö-6]",
    "Ö-7": "── ALAN DAMGASI[M11·Ö-7]",
    "Ö-8": "── ALAN DAMGASI[M11·Ö-8]",
}

GUARD = (REPO / "meridian" / "guard.py").read_text()


def _damga(kaynak: str, oneri: str, n: int = 2600) -> str:
    bas = DAMGA_BASLARI[oneri]
    assert bas in kaynak, f"{oneri} damga BLOĞU yok (yalnız atıf yeterli değil)"
    return kaynak.split(bas, 1)[1][:n]


def _duz(s: str) -> str:
    """Türkçe nokta tuzağı: `İ`.lower() birleşik noktalı `i̇` verir (§E/e2 dersi)."""
    return s.replace("İ", "i").lower()


# ---------------------------------------------------------------- Ö-5 · `side` (ÖLÜ)

def test_f1_side_damgasi_var():
    """DAMGA: `side` plan alanı ÖLÜ (sıfır üretim okuyucusu) ama KALDIRILMADI — şema iki motorda
    aynı kalmak zorunda (`test_differential_v60`). Damga o kararı ve gerekçesini taşır."""
    for kaynak, ad in ((LOOP, "loop.py"), (BROKER, "broker.py")):
        d = _duz(_damga(kaynak, "Ö-5"))
        assert "side" in d, f"{ad}: Ö-5 damgası alanı adlandırmıyor"
        assert "kaldir" in d or "kaldır" in d.replace("ı", "i"), \
            f"{ad}: damga 'KALDIRMA YOK' kararını söylemiyor"
    assert "short" in _duz(_damga(LOOP, "Ö-5")), \
        "damga alanın NEDEN durduğunu (gelecekteki short desteği) söylemiyor"


def test_f2_side_sabiti_hala_plani_okumuyor():
    """DAMGANIN DAYANDIĞI OLGU — İKİ YÖNLÜ: (a) `broker.py` pozisyonu `side="long"` SABİTİYLE
    kurar, plan alanını okumaz; (b) üretimde hiçbir `plan`-adlı sözlük `side` okumaz.

    ÇİVİNİN BEYANLI SINIRI (ad çakışması — tarama §1.2/2): `side` adı işlem satırı, açık pozisyon
    ve Alpaca emri sözlüklerinde de yaşar (`watchdog.py` `p.get("side")` bir ALPACA POZİSYONUdur,
    `faz5_cikis.py` `p.get("side")` bir AÇIK POZİSYONdur — ikisi de elle doğrulandı). Bu yüzden
    çivi çıplak `p` değişkenini DEĞİL, yalnız plan bağlamını adlandıran isimleri tarar; daha geniş
    bir desen ALAKASIZ okuyucularla sürekli kırmızı yanar ve çivi sökülürdü."""
    assert 'side="long"' in BROKER, (
        "`broker.py` artık `side` sabitini yazmıyor — plan alanı bağlanmış olabilir, Ö-5 damgası BAYATLADI")
    plan_pat = re.compile(r"""(?:plan|pln|_gate_plan|_plan)\s*(?:\[\s*['"]side['"]\s*\]"""
                          r"""|\.get\(\s*['"]side['"])""")
    hits = []
    for f in sorted((REPO / "meridian").rglob("*.py")):
        for i, l in enumerate(_yorumsuz_py(f.read_text()).splitlines(), 1):
            if plan_pat.search(l):
                hits.append(f"{f.name}:{i}")
    assert not hits, (
        f"plan `side` artık üretimde okunuyor ({hits}) — ALAN DAMGASI[M11·Ö-5] BAYATLADI; "
        "damgayı tazele (alan artık ölü değil)")


# ---------------------------------------------------------------- Ö-6 · `targets` (YEDEKLİ İKİZ)

def test_f3_targets_damgasi_var():
    d = _duz(_damga(LOOP, "Ö-6"))
    assert "targets" in d and "profit_target" in d, "Ö-6 damgası ikizi adlandırmıyor"
    assert "counterfactual" in d, "damga cf YEDEK okumasını (kaldırmayı yasaklayan olgu) söylemiyor"


def _liste_ici(kod: str, i: int) -> str | None:
    """`[` konumundan başlayıp DENGELİ kapanışa kadar olan içeriği döndürür.

    Kaba `\\[[^\\]]*\\]` deseni `[c["profit_target"]]` ifadesini İÇ `]`de keserdi — yani çivi
    üreticinin gerçek ifadesini hiç görmeden yeşil kalırdı."""
    if i >= len(kod) or kod[i] != "[":
        return None
    derinlik = 0
    for j in range(i, len(kod)):
        if kod[j] in "([{":
            derinlik += 1
        elif kod[j] in ")]}":
            derinlik -= 1
            if not derinlik:
                return kod[i + 1:j]
    return None


def _tepe_virgul(s: str) -> int:
    d, n = 0, 0
    for ch in s:
        if ch in "([{":
            d += 1
        elif ch in ")]}":
            d -= 1
        elif ch == "," and d == 0:
            n += 1
    return n


def _deger(kod: str, i: int) -> str:
    """`i`den başlayan sözlük DEĞERİNİ, TEPE düzeydeki virgüle/satır sonuna kadar döndürür.

    Kaba `[^,\n]+` deseni `round(px * 1.15, 4)` ifadesini İÇ virgülde keserdi — üretici ile
    ikizini karşılaştıran çivi o zaman ikisi AYNI olduğu hâlde kırmızı yanardı (yanlış-alarm).
    """
    d, out = 0, []
    for ch in kod[i:]:
        if ch in "([{":
            d += 1
        elif ch in ")]}":
            if d == 0:
                break
            d -= 1
        elif (ch == "," and d == 0) or ch == "\n":
            break
        out.append(ch)
    return "".join(out)


def test_f4_targets_hala_profit_targetin_yedekli_ikizi():
    """DAMGANIN DAYANDIĞI OLGU: HER üretici `targets`i TEK elemanlı ve o eleman AYNI dosyanın
    `profit_target` ifadesiyle AYNI yazar — canlı 500/500 sapma-0 ölçümünün kod tarafındaki
    karşılığı budur. Alan bir gün gerçek bir HEDEF MERDİVENİ taşırsa (çok elemanlı ya da farklı
    ifade) 'yedekli ikiz' beyanı BAYATLAR ve bu test kırmızıya döner."""
    uretici = 0
    for f in sorted((REPO / "meridian").rglob("*.py")):
        kod = _yorumsuz_py(f.read_text())
        pt = {re.sub(r"\s+", " ", _deger(kod, m.end())).strip()
              for m in re.finditer(r'"profit_target"\s*:\s*', kod)}
        for m in re.finditer(r'"targets"\s*:\s*(?=\[)', kod):
            ic = _liste_ici(kod, m.end())
            assert ic is not None, f"{f.name}: `targets` listesi ayrıştırılamadı"
            uretici += 1
            assert _tepe_virgul(ic) == 0, (
                f"{f.name}: `targets` ARTIK ÇOK ELEMANLI ({ic!r}) — 'yedekli ikiz' damgası BAYATLADI")
            norm = re.sub(r"\s+", " ", ic).strip()
            assert norm in pt, (
                f"{f.name}: `targets` ifadesi ({norm!r}) `profit_target` ifadelerinden ({sorted(pt)}) "
                "ayrıştı — ALAN DAMGASI[M11·Ö-6] BAYATLADI")
    assert uretici >= 4, f"`targets` üreticileri bulunamadı ({uretici}) — çivi kör kaldı"


# ---------------------------------------------------------------- Ö-7 · `sector` (İKİ TAVAN)

def test_f5_sector_damgasi_var():
    d = _duz(_damga(GUARD, "Ö-7", 3200))
    assert "sector" in d, "Ö-7 damgası alanı adlandırmıyor"
    assert "portfolio.sector_cap" in d, "damga UYUYAN knob'u adlandırmıyor"
    assert "y3_sector_cap" in d, "damga uyuyan kapının ADINI vermiyor"
    assert "uyu" in d, "damga 'uyuyan bağ' ayrımını söylemiyor"


def test_f6_canli_sektor_kapisi_hala_plan_alanini_okuyor():
    """DAMGANIN BİRİNCİ YARISI (taramanın 13. satırının DÜZELTMESİ): `sector` bugün CANLI bir sert
    kapıya girer — `classify_gate` alanı KOŞULSUZ okur ve `sector_cap` kontrolüne verir. Bu bağ
    bir gün kesilirse damga ('canlı yarım') bayatlar ve test kırmızıya döner."""
    kod = _yorumsuz_py(GUARD)
    m = re.search(r"\ndef classify_gate\(.*?\n(?=\ndef )", kod, re.S)
    assert m, "classify_gate gövdesi bulunamadı"
    g = m.group(0)
    assert re.search(r'sec\s*=\s*plan\.get\(\s*"sector"', g), (
        "`classify_gate` artık plan `sector` alanını okumuyor — ALAN DAMGASI[M11·Ö-7]'nin "
        "'CANLI YARIM' beyanı BAYATLADI")
    kapi = re.search(r'_chk\(\s*"sector_cap"\s*,(.*?)\n\s*(?:#|_chk\()', g, re.S)
    assert kapi, "`sector_cap` sert kontrolü bulunamadı"
    assert "sc.get(sec" in kapi.group(1), (
        "`sector_cap` kontrolü artık plandan gelen sektörü kullanmıyor — damga bayatladı")


def test_f7_uyuyan_sektor_knobu_hala_kosullu():
    """DAMGANIN İKİNCİ YARISI: UYUYAN olan `portfolio.sector_cap` (NOTIONAL payı) tavanıdır —
    knob 0/yok iken `y3_sector_cap` kontrolü hiç KURULMAZ. Knob koşulsuz hâle gelirse (ya da
    varsayılanı 0 olmaktan çıkarsa) 'uyuyan bağ' beyanı bayatlar ve bu test kırmızıya döner."""
    kod = _yorumsuz_py(GUARD)
    m = re.search(r"\ndef _y3_portfolio_caps\(.*?(?=\ndef |\Z)", kod, re.S)
    assert m, "_y3_portfolio_caps gövdesi bulunamadı"
    g = m.group(0)
    assert re.search(r'cap_pct\s*=\s*float\(\s*p\.get\(\s*"portfolio\.sector_cap"\s*,\s*0', g), (
        "`portfolio.sector_cap` artık 0 varsayılanıyla okunmuyor — uyuyan-bağ beyanı bayatladı")
    kosul = g.index("if cap_pct > 0:")
    assert kosul < g.index('_chk("y3_sector_cap"'), (
        "`y3_sector_cap` artık knob koşulunun DIŞINDA kuruluyor — uyuyan bağ UYANDI, damga bayatladı")


# ---------------------------------------------------------------- Ö-8 · `exploration` + `carried`

def test_f8_kesif_damgasi_var():
    """Kalemin ADI da damganın parçası: 'keşif bütçesi' değil 'keşif ÜRETİCİ KURAKLIĞI' —
    yanlış iş (tavanı ayarlamaya çalışmak) tam bu addan doğardı (tarama T-3)."""
    d = _duz(_damga(LOOP, "Ö-8", 3200))
    assert "exploration" in d and "carried" in d, "Ö-8 damgası iki alanı da adlandırmıyor"
    assert "kablo" in d, "damga 'kablo canlı' yarımını söylemiyor"
    assert "kurak" in d, "damga 'üretim kurak' yarımını söylemiyor"
    assert "bütçe" in d or "butce" in d, "damga yanlış-ad tuzağını (bütçe) adlandırmıyor"


def test_f9_kesif_kablosu_hala_canli():
    """DAMGANIN DAYANDIĞI OLGU (1): açık pozisyonun çıkış rejim kapısını GEVŞETEN dal.
    Kablo kesilirse 'kablo canlı' beyanı bayatlar ve test kırmızıya döner."""
    kod = _yorumsuz_py(LOOP)
    assert re.search(r'pos_regime_ok\s*=\s*.*getattr\(pos,\s*"exploration"', kod), (
        "keşif çıkış-gevşetme dalı kaybolmuş — ALAN DAMGASI[M11·Ö-8]'in 'kablo canlı' yarımı BAYATLADI")


def test_f10_carried_kablosu_hala_canli():
    """DAMGANIN DAYANDIĞI OLGU (2): ikinci bar-sız seansta planı DÜŞÜREN sayaç + iki olayı."""
    kod = _yorumsuz_py(LOOP)
    m = re.search(r"\ndef _carry_armed_without_bar\(.*?\n(?=\ndef |\n_)", kod, re.S)
    assert m, "_carry_armed_without_bar gövdesi bulunamadı"
    g = m.group(0)
    assert 'plan.get("carried")' in g, "`carried` artık okunmuyor — düşürme sayacı koptu"
    assert 'plan["carried"]' in g, "`carried` artık yazılmıyor — sayaç üreticisi koptu"
    for ev in ("armed_no_bar_carried", "armed_expired_no_bar"):
        assert ev in g, f"`{ev}` olayı kaybolmuş — kuraklık ölçümünün TEK kanıt kanalıydı"


def test_f11_kesif_uretici_yuzeyi_tek():
    """'ÜRETİM KURAK' beyanı ÖLÇÜLEN bir üretici yüzeyine dayanır: `exploration` bayrağını üretimde
    TEK bir yol (keşif havuzu seçimi) `True` yapar. İkinci bir üretici doğarsa kuraklık ölçümü
    yeniden yapılmalıdır — o gün bu test kırmızı yanar."""
    yazan = []
    for f in sorted((REPO / "meridian").rglob("*.py")):
        for i, l in enumerate(_yorumsuz_py(f.read_text()).splitlines(), 1):
            if re.search(r'\[\s*"exploration"\s*\]\s*=', l):
                yazan.append(f"{f.name}:{i}")
    assert len(yazan) == 1, (
        f"`exploration` üretici yüzeyi değişti ({yazan}) — 'ÜRETİM KURAK' beyanı ölçülen tek "
        "üreticiye dayanıyordu; ALAN DAMGASI[M11·Ö-8] BAYATLADI")
