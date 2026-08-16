"""v196 — ACİL DÜZELTME TURU: üç kusur, tasarımdan BAĞIMSIZ.

Bu üç bulgu hangi yeniden-tasarım seçilirse seçilsin kusurdur; kaynağı
`docs/BASELINE-2026-08-06.md` (T3 · T12 · T2) ve hepsi ciddiyet-4 sınıfından.

  KALEM 1 — MOD HER DURUMDA GÖRÜNÜR (baseline §B.9 / T3).
    `#statustext` modu YALNIZ sağlıklı dalda basıyordu: `t.halted` → "DURDURULDU",
    `t.stale` → "gecikmiş · N sn". Her iki hâlde de "paper" hecesi DOM'DAN KAYBOLUYORDU —
    yani mod, tam da sistem bozukken görünmez oluyordu. Design rules'un cümlesi:
    *"the costliest accident class in this domain is an operator who believes they are in
    the other mode."* Ayrıca üç yerde mod KODA ÇAKILIYDI ("paper" sabit dizesi), yani
    `MERIDIAN_MODE=live` olduğu gün pano — güvenlik durumu kartı dahil — sessizce yalan
    söylerdi. Testler DAVRANIŞA bakar: fikstür başına gerçek dal Node'da koşturulur.

  KALEM 2 — FFILL ETİKETSİZ (baseline §B.2 / T12).
    `trend_shadow` iki yerde ileri-doldurma yapıyor (`_dilim`in sıralama penceresi,
    `_isaretle`in son-bilinen-kapanışı) ve sonuç ekrana ulaşıyor (`api.py` → `trend_kitabi`
    → Öğrenme#gölge). Web katmanında "dolduruldu" dizesi SIFIR kez geçiyordu: taşınmış bir
    kapanışla ölçülmüş bir kapanış aynı mürekkeple yazılıyordu. Doldurma meşru; ETİKETSİZ
    olması değildi. Sözleşme: DOLDURULMUŞ satır rozet TAŞIR, doldurulmamış TAŞIMAZ, bayrağı
    olmayan (eski) satır "ölçülemedi" der — üçü de ayırt edilebilir.

  KALEM 3 — `?? 0` / `|| 0` TRİYAJI (baseline §B.1 / T2).
    211 eşleşme elle sınıflandırıldı: (a) yalan söyleyenler 167, (b) güvenli 44. En kritik
    30'u düzeltildi, 137'si KUYRUKTA ve raporda satır satır yazılı — sessiz kısaltma yok.
    Rapor: `research/olcumler/nullsifir_triyaj_2026-08-06/RAPOR.md`.

TESTLER HEM KAYNAĞA HEM DAVRANIŞA BAKAR (repo deseni: v139 · v160 · v171 · v194). Kaynak
taraması bir dizginin varlığını ölçer; şablon dilimlerini Node'da FİİLEN koşturmak ise
"kaynakta doğru görünen şablon çalışma zamanında başka şey basıyor" sınıfını yakalar.
"""
from __future__ import annotations

import json
import pathlib
import re
import shutil
import subprocess

import pandas as pd
import pytest

from meridian import trend_shadow as ts

SRC = pathlib.Path(__file__).resolve().parents[1]
WEB = SRC / "meridian" / "web"
APPJS = (WEB / "app.js").read_text()
INDEX = (WEB / "index.html").read_text()
APIPY = (SRC / "meridian" / "api.py").read_text()
TS_SRC = (SRC / "meridian" / "trend_shadow.py").read_text()
RAPOR = SRC / "research" / "olcumler" / "nullsifir_triyaj_2026-08-06" / "RAPOR.md"

NODE = shutil.which("node")

# Yorumsuz gövde (v154/v155/v160/v171/v194 deseni): bir kuralın GEREKÇESİNİ anlatan yorum, o
# kuralın ihlali sanılmamalı. Bu turda ZORUNLU — her üç düzeltme de kaldırdığı deseni yorumda
# ADIYLA anlatıyor ("paper", "?? 0", "ffill" kelimeleri gerekçe metinlerinde geçiyor).
KOD = "\n".join(l for l in APPJS.splitlines() if not l.lstrip().startswith("//"))
CSS = INDEX[INDEX.index("<style>"):INDEX.index("</style>")]

NULLSIFIR = re.compile(r"(\?\?|\|\|)\s*0(?![\d.])")


def _blok(bas: str, bitti, kaynak: str = APPJS) -> str:
    """`bas` ile başlayan satırdan `bitti(satır)` doğru olana kadarki kaynak dilimi."""
    i = kaynak.index(bas)
    parcalar = []
    for ln in kaynak[i:].splitlines(keepends=True):
        parcalar.append(ln)
        if bitti(ln) and (len(parcalar) > 1 or bitti(ln)):
            return "".join(parcalar)
    raise AssertionError(f"kapanış bulunamadı: {bas}")


def _satir(baslangic: str) -> str:
    for ln in APPJS.splitlines():
        if ln.startswith(baslangic):
            return ln
    raise AssertionError(f"satır yok: {baslangic}")


def _nullsifir_say(metin: str) -> int:
    return sum(len(NULLSIFIR.findall(l)) for l in metin.splitlines()
               if not l.lstrip().startswith("//"))


# =============================================================================================
# KALEM 1 — MOD HER DURUMDA GÖRÜNÜR
# =============================================================================================
ESC_SRC = _satir("const esc = ")
ONK_SRC = _satir("const onk = ")
MODSABIT_SRC = _satir("const MOD_OLCULEMEDI = ")
MODJETON_SRC = _blok("function modJetonu(mod) {", lambda ln: ln.rstrip("\n") == "}")
DURUMYAZ_SRC = (_satir("let _DURUM_HTML = ") + "\n"
                + _blok("function durumYaz(html) {", lambda ln: ln.rstrip("\n") == "}"))
REFRESH_SRC = _blok("async function refreshStatus() {", lambda ln: ln.rstrip("\n") == "}")

# `refreshStatus` DİLİMİ OLDUĞU GİBİ KOŞAR: ağ/DOM stub'lanır, DAL MANTIĞINA DOKUNULMAZ. Testin
# yeniden yazdığı bir dal, testin kendi hayalini doğrularsa koruma değil dekor olur.
_MOD_HARNESS = """
const _dom = {};
const $ = id => (_dom[id] = _dom[id] || { id, className: "", textContent: "", innerHTML: "",
                                          title: "", style: {} });
let HALTED = null, _FIX = null;
function sessizHatGlobal() {}
const j = async () => { if (_FIX === "KOPUK") throw new Error("bağlantı yok"); return _FIX; };
%(esc)s
%(onk)s
%(modsabit)s
%(modjeton)s
%(durumyaz)s
%(refresh)s
const FIX = %(fikstur)s;
(async () => {
  const cikti = {};
  for (const [ad, yuk] of Object.entries(FIX)) {
    _FIX = yuk;
    _DURUM_HTML = "";                       // her fikstür temiz sayfadan başlar
    _dom.statustext = undefined;
    await refreshStatus();
    cikti[ad] = $("statustext").innerHTML;
  }
  process.stdout.write(JSON.stringify(cikti));
})();
"""

_FIKSTURLER = {
    # ÜÇ BOZUK DURUM + iki karşılaştırma dalı. `bos` = "veri-yok": uç cevap veriyor ama yük boş
    # (yerel görsel doğrulama sunucusunun tam hâli); `kopuk` = uç hiç cevap vermiyor.
    "saglikli": {"mode": "paper", "autonomy_level": 0, "heartbeat_age_seconds": 3},
    "halted": {"mode": "paper", "halted": True, "heartbeat_age_seconds": 11},
    "stale": {"mode": "paper", "stale": True, "heartbeat_age_seconds": 900},
    "bos": {},
    "kopuk": "KOPUK",
    "canli_halted": {"mode": "live", "halted": True, "heartbeat_age_seconds": 4},
    "canli_stale": {"mode": "live", "stale": True, "heartbeat_age_seconds": 700},
}


@pytest.fixture(scope="module")
def mod_ciktilari():
    if NODE is None:
        pytest.skip("node yok")
    betik = _MOD_HARNESS % {"esc": ESC_SRC, "onk": ONK_SRC, "modsabit": MODSABIT_SRC,
                            "modjeton": MODJETON_SRC, "durumyaz": DURUMYAZ_SRC,
                            "refresh": REFRESH_SRC,
                            "fikstur": json.dumps(_FIKSTURLER, ensure_ascii=False)}
    p = subprocess.run([NODE, "-e", betik], capture_output=True, text=True, timeout=60)
    assert p.returncode == 0, f"durum şeridi dilimi Node'da patladı:\n{p.stderr}"
    return json.loads(p.stdout)


def test_mod_kanali_HER_DURUMDA_DOMda(mod_ciktilari):
    """ASIL REGRESYON (T3). Yedi dalın YEDİSİNDE de moda ayrılmış bir öğe DOM'da bulunur.
    Arızalı hâlde `halted`/`stale`/`bos`/`kopuk` dallarında `data-mod` HİÇ yoktu."""
    for ad, html in mod_ciktilari.items():
        assert "data-mod=" in html, f"{ad}: mod kanalı DOM'dan kaybolmuş — {html!r}"


def test_bozuk_uc_durumda_MOD_DIZESI_okunuyor(mod_ciktilari):
    """Brief'in çivisi: üç bozuk-durum fikstüründe de mod DİZESİ (jetonun metni) DOM'da.
    `data-mod` bir makine kanalı; insan okuyucunun gördüğü metnin de orada olması gerekir."""
    for ad in ("halted", "stale", "bos"):
        html = mod_ciktilari[ad]
        assert ('data-mod="paper"' in html and ">paper<" in html) or "MOD ÖLÇÜLEMEDİ" in html, \
            f"{ad}: mod metni yok — {html!r}"
    assert ">paper<" in mod_ciktilari["halted"], "halted dalında ölçülmüş mod basılmıyor"
    assert ">paper<" in mod_ciktilari["stale"], "stale dalında ölçülmüş mod basılmıyor"


def test_live_dali_DOGRU_davraniyor(mod_ciktilari):
    """"live" dalı da doğru davranmalı: canlı modda hiçbir dal "paper" YAZMAZ. Bu kusurun en
    pahalı hâli — operatör canlı hesapta kâğıtta olduğunu sanar."""
    for ad in ("canli_halted", "canli_stale"):
        html = mod_ciktilari[ad]
        assert 'data-mod="live"' in html and ">live<" in html, f"{ad}: canlı mod basılmıyor"
        assert "paper" not in html, f"{ad}: CANLI modda 'paper' yazıyor — {html!r}"


def test_olculemeyen_mod_UYDURULMAZ(mod_ciktilari):
    """UYDURMA YASAĞI + ffill yasağı. Uç düştüğünde ya da alan boş geldiğinde jeton bir mod
    İDDİA ETMEZ ve SON BİLİNEN modu hatırlamaz — bayat bir "paper", canlı hesapta operatöre
    "kâğıttayım" dedirtirdi (bu turun KALEM 2'de kapattığı kusur sınıfının aynısı)."""
    for ad in ("bos", "kopuk"):
        html = mod_ciktilari[ad]
        assert "MOD ÖLÇÜLEMEDİ" in html, f"{ad}: ölçülemeyiş söylenmiyor — {html!r}"
        assert 'data-mod="olculemedi"' in html
        for uydurma in ("paper", "live", "kâğıt"):
            assert uydurma not in html, f"{ad}: ölçülmemiş mod UYDURULMUŞ ({uydurma})"


def test_durum_cumlesi_modu_TEKRAR_ETMIYOR(mod_ciktilari):
    """Aynı gerçeğin iki metni ilk düzenlemede ayrışır (bu deponun tekrar eden kusur sınıfı):
    mod artık YALNIZ jetonda; sağlıklı cümle "canlı · L0 · N sn önce"."""
    saglikli = mod_ciktilari["saglikli"]
    cumle = saglikli[saglikli.rindex("</span>") + len("</span>"):]   # jetondan SONRAKİ metin
    assert cumle.strip() == "canlı · L0 · 3 sn önce", cumle
    assert "paper" not in cumle, "mod iki yerde yazılıyor — ilk düzenlemede ayrışır"
    assert "canlı · paper" not in saglikli


def test_kopuk_dalda_da_baglanti_yok_YAZIYOR(mod_ciktilari):
    """Mod eklendi diye ESKİ bilgi düşmedi: bağlantı yokluğu hâlâ söyleniyor."""
    assert "bağlantı yok" in mod_ciktilari["kopuk"]
    assert "DURDURULDU" in mod_ciktilari["halted"]
    assert "gecikmiş" in mod_ciktilari["stale"]


def test_mod_jetonu_YENI_DIL_ACMIYOR():
    """Yeni bir sınıf/renk İCAT EDİLMEDİ: jeton panonun mevcut `.tag`/`.t-vi` reçetesidir ve
    `t-vi` akromatiktir (`--accent-tint`). Mod kroması bu turda AÇILMADI (T4 ayrı kalem);
    şiddet hue'ları (`--red`/`--amber`/`--green`) moda ÖDÜNÇ VERİLMEZ."""
    assert 'class="tag t-vi"' in MODJETON_SRC, "jeton mevcut rozet reçetesini kullanmıyor"
    assert ".t-vi{" in CSS, "t-vi sınıfı CSS'te yok — jeton hayalet sınıf kullanıyor"
    for hue in ("--red", "--amber", "--green", "t-no", "t-rv", "t-go"):
        assert hue not in MODJETON_SRC, f"mod jetonu şiddet/hüküm kanalını ödünç alıyor: {hue}"


def test_mod_SABIT_DIZEDEN_degil_OLCUMDEN_geliyor():
    """Kaynak taraması: panoda DOM'a basılan sabit "paper" dizesi KALMADI. Üç yer vardı —
    durum şeridi, kenar rayı "Otonomi" satırı ve Ayarlar'ın GÜVENLİK DURUMU kartı."""
    for eski in ("canlı · paper · ", "} · paper</b>", "Mod: <b>paper</b>"):
        assert eski not in KOD, f"koda çakılı mod dizesi hâlâ orada: {eski!r}"
    assert "modJetonu(t.mode)" in KOD and "modJetonu(d.mode)" in KOD
    assert "esc(today.mode || MOD_OLCULEMEDI)" in KOD


def test_guvenlik_karti_modu_UCTAN_okuyor():
    """YASA 6 çift yönlü: pano `d.mode` okuyor VE uç onu üretiyor. `live_enabled` bunun yerine
    GEÇMEZ — o bayrak iki koşulun VE'sidir (mod + risk kabulü), "mod live ama kabul yok"
    hâlinde false döner ve kart yine "paper" derdi."""
    assert '"mode": config.MODE,' in APIPY, "/api/secrets modu servis etmiyor"
    assert "live_enabled" in APIPY


# =============================================================================================
# KALEM 2 — FFILL ETİKETLİ (kaynak) ve GÖRÜNÜR (pano)
# =============================================================================================
def _gunler(n=6):
    return pd.bdate_range("2026-01-05", periods=n)


def _kare(idx, kapanislar):
    return pd.DataFrame({"open": kapanislar, "high": kapanislar, "low": kapanislar,
                         "close": kapanislar}, index=idx)


def test_dilim_ILERI_DOLDURULAN_hucreyi_ISARETLIYOR():
    """Bayrak VERİNİN YANINDA: `_dilim` her kareye `_dolduruldu` maskesi ekler. Maske ffill'DEN
    ÖNCE alınır — doldurulduktan sonra doldurulmuş hücre ölçülmüş hücreden ayırt edilemez."""
    idx = _gunler(6)
    tam = _kare(idx, [10.0, 11.0, 12.0, 13.0, 14.0, 15.0])
    delikli = _kare(idx, [10.0, float("nan"), float("nan"), 13.0, 14.0, 15.0])
    dilim = ts._dilim({"TAM": tam, "DELIK": delikli}, ["TAM", "DELIK"], idx)
    assert set(dilim) == {"TAM", "DELIK"}
    assert ts.dolduruldu_n(dilim["TAM"]) == 0, "boşluğu olmayan sembole doldurma yazılmış"
    assert ts.dolduruldu_n(dilim["DELIK"]) == 2
    assert bool(dilim["DELIK"][ts.DOLDU_KOL].loc[idx[1]]) is True
    assert bool(dilim["DELIK"][ts.DOLDU_KOL].loc[idx[3]]) is False
    # Doldurma FİİLEN yapılıyor (semantik değişmedi — yalnız etiketlendi).
    assert float(dilim["DELIK"].at[idx[2], "close"]) == 10.0


def test_dilim_IMZASI_KORUNDU_dis_cagiranlar_kirilmiyor():
    """Bayrağı ikinci bir dönüş değeri yapmak imzayı kırardı (v144 `_dilim` doğrudan çağırıyor).
    Köken şerhi veriyle AYNI nesnede taşınır; ayrı yaşasaydı ilk düzenlemede ayrışırdı."""
    idx = _gunler(4)
    dilim = ts._dilim({"A": _kare(idx, [1.0, 2.0, 3.0, 4.0])}, ["A"], idx)
    assert isinstance(dilim, dict) and "A" in dilim
    assert ts.DOLDU_KOL.startswith("_"), "köken kolonu piyasa kolonu gibi adlandırılmış"


def test_dilim_OMUR_DISINI_doldurmuyor_ve_ISARETLEMIYOR():
    """Bakma-ileri yasağı korunuyor: ömürden ÖNCE/SONRA kalan NaN doldurulmaz, dolayısıyla
    bayrak da almaz. Bayrak, ffill'in kapsamını olduğundan geniş göstermemeli."""
    idx = _gunler(6)
    gec = _kare(idx, [float("nan"), float("nan"), 12.0, float("nan"), 14.0, float("nan")])
    dilim = ts._dilim({"GEC": gec}, ["GEC"], idx)
    assert ts.dolduruldu_n(dilim["GEC"]) == 1          # yalnız 12 ile 14 arasındaki tek hücre
    assert pd.isna(dilim["GEC"].at[idx[0], "close"])   # ömürden önce: DOLDURULMADI
    assert pd.isna(dilim["GEC"].at[idx[5], "close"])   # ömürden sonra: DOLDURULMADI


def test_isaretle_SATIR_DUZEYINDE_bayrak_yaziyor():
    """Sözleşmenin çekirdeği: doldurulmuş satır bayrağı TAŞIR (>0), doldurulmamış TAŞIR ama
    SIFIRDIR. İkisi ayırt edilebilir olmak zorunda — "ölçüldü, taşıma yok" ile "hiç ölçülmedi"
    aynı piksele düşerse satır bir bilgi değil bir izlenim taşır."""
    idx = _gunler(3)
    kitap = ts.yeni_kitap()
    kitap["cash"] = 1000.0
    kitap["positions"] = {"AAA": {"shares": 10.0, "entry_date": "2026-01-05",
                                  "entry_price": 10.0, "peak_high": 10.0, "last_close": 10.0},
                          "BBB": {"shares": 5.0, "entry_date": "2026-01-05",
                                  "entry_price": 20.0, "peak_high": 20.0, "last_close": 20.0}}
    per = {"AAA": _kare(idx, [10.0, 11.0, 12.0]), "BBB": _kare(idx[:1], [20.0])}

    eksik = ts._isaretle(kitap, idx[0], per)           # iki sembolün de barı var
    assert eksik == []
    assert kitap["equity"][-1]["dolduruldu"] == 0

    eksik = ts._isaretle(kitap, idx[1], per)           # BBB'nin barı yok → ileri taşındı
    assert eksik == ["BBB"]
    assert kitap["equity"][-1]["dolduruldu"] == 1


def test_ozet_UC_HALI_ayirt_ediyor():
    """`ozet()` üç hâli DIŞARI verir: bayrak yok (ölçülemez) · 0 (ölçüldü, taşıma yok) · >0.
    `get(...) or 0` KULLANILMAZ — o katlama ÖLÇÜLEMEDİ≠0 yasasının doğrudan ihlali olurdu."""
    kitap = ts.yeni_kitap()
    kitap["equity"] = [{"date": "2026-01-05", "equity": 100.0},              # bayraksız (eski)
                       {"date": "2026-01-06", "equity": 101.0, "dolduruldu": 0},
                       {"date": "2026-01-07", "equity": 102.0, "dolduruldu": 3}]
    o = ts.ozet(kitap)
    assert o["son_dolduruldu"] == 3
    assert o["dolduruldu_gun"] == 1
    assert o["dolduruldu_olcumsuz"] == 1, "bayraksız satır sessizce 'doldurulmadı' sayılmış"

    kitap["equity"] = kitap["equity"][:1]              # yalnız bayraksız satır kaldı
    o2 = ts.ozet(kitap)
    assert o2["son_dolduruldu"] is None, "bayrağı olmayan satır 0 diye okunmuş (uydurma)"
    assert o2["dolduruldu_gun"] == 0 and o2["dolduruldu_olcumsuz"] == 1


def test_ozet_KARAR_penceresinin_doldurmasini_da_veriyor():
    """İki ffill yolu var; yalnız birini etiketlemek diğerini görünmez bırakırdı. Bekleyen
    ay-sonu kararı, SIRALAMA penceresindeki doldurulmuş hücre sayısını kendi içinde taşır."""
    kitap = ts.yeni_kitap()
    kitap["equity"] = [{"date": "2026-01-05", "equity": 100.0, "dolduruldu": 0}]
    assert ts.ozet(kitap)["karar_dolduruldu"] is None          # bekleyen karar yok
    kitap["pending"] = {"date": "2026-01-30", "exits": [], "entries": [], "aday": 5,
                        "en_iyi": [], "dolduruldu": 7, "dolduruldu_sembol": 3}
    assert ts.ozet(kitap)["karar_dolduruldu"] == 7


def test_SCHEMA_ARTIRILMADI_canli_defter_silinmiyor():
    """Bayrak eklendi ama `SCHEMA` BİLEREK sabit kaldı: `run_cycle` şema uyuşmazlığında kitabı
    `yeni_kitap()` ile SIFIRDAN doğuruyor — bir sürüm artışı CANLI gölge-defteri silerdi.
    Eski satırların bayraksız kalması bu yüzden bir kusur değil, ölçülmüş bir sınırdır."""
    assert ts.SCHEMA == 1, "SCHEMA artmış — canlı trend_book.json sıfırlanır"
    assert "SCHEMA BİLEREK ARTIRILMADI" in TS_SRC


def test_karar_bayragi_KARARIN_ICINDE_ayri_defterde_degil():
    """Ayrı bir defter, ilk düzenlemede karardan ayrışır ve "hangi karar hangi doldurmayla
    alındı" sorusu cevapsız kalırdı."""
    assert '"dolduruldu": int(sum(dolu.values())), "dolduruldu_sembol": len(dolu)' in TS_SRC
    assert "dolu = {t: dolduruldu_n(r) for t, r in dilim.items() if dolduruldu_n(r)}" in TS_SRC


# ---- pano tarafı: rozet MEVCUT desenden, yeni dil yok ---------------------------------------
DOLDURULDU_SRC = _blok("function _dolduruldu(icerik, n) {", lambda ln: ln.rstrip("\n") == "}")
DOLDURAN_SRC = _blok("function _dolduranSeanslar(tk) {", lambda ln: ln.rstrip("\n") == "}")
BELIRSIZ_SRC = _blok("function belirsiz(icerik, beyan) {", lambda ln: ln.rstrip("\n") == "}")
CHIP_SRC = _satir("function _chip(txt, cls)")
TRN_SRC = _satir("const trn = ")

_FFILL_HARNESS = """
%(esc)s
%(trn)s
%(chip)s
%(belirsiz)s
%(dolduruldu)s
%(dolduran)s
process.stdout.write(JSON.stringify({
  temiz: _dolduruldu("$1.234,00", 0),
  dolu:  _dolduruldu("$1.234,00", 2),
  olcumsuz: _dolduruldu("$1.234,00", null),
  satir_yok: _dolduranSeanslar({ pozisyon: 3 }),
  satir_var: _dolduranSeanslar({ dolduruldu_gun: 4, dolduruldu_olcumsuz: 11,
                                 karar_dolduruldu: 7 }),
  satir_temiz: _dolduranSeanslar({ dolduruldu_gun: 0, dolduruldu_olcumsuz: 0,
                                   karar_dolduruldu: null }),
}));
"""


@pytest.fixture(scope="module")
def ffill_ciktilari():
    if NODE is None:
        pytest.skip("node yok")
    betik = _FFILL_HARNESS % {"esc": ESC_SRC, "trn": TRN_SRC, "chip": CHIP_SRC,
                              "belirsiz": BELIRSIZ_SRC, "dolduruldu": DOLDURULDU_SRC,
                              "dolduran": DOLDURAN_SRC}
    p = subprocess.run([NODE, "-e", betik], capture_output=True, text=True, timeout=60)
    assert p.returncode == 0, f"doldurma işareti dilimi Node'da patladı:\n{p.stderr}"
    return json.loads(p.stdout)


def test_DOLDURULMUS_satir_rozet_TASIR_doldurulmamis_TASIMAZ(ffill_ciktilari):
    """Brief'in çivisi, iki yönlü. Tek yönlü olsaydı "her hücreye rozet bas" da geçerdi ve
    rozet bir bilgi taşımaz olurdu."""
    temiz, dolu = ffill_ciktilari["temiz"], ffill_ciktilari["dolu"]
    assert temiz == "$1.234,00", f"temiz hücreye süs basılmış: {temiz!r}"
    assert "belirsiz" not in temiz and "tag" not in temiz
    assert 'class="belirsiz"' in dolu and "İLERİ DOLDURULDU" in dolu
    assert "2 pozisyonun kendi barı yoktu" in dolu
    assert "$1.234,00" in dolu, "rozet değeri yutmuş"


def test_bayraksiz_hal_SESSIZCE_temiz_sayilmiyor(ffill_ciktilari):
    """Üçüncü hâl kendi cümlesini alır: "doldurulmadı" ile "doldurulup doldurulmadığı
    ölçülemiyor" aynı şey değildir."""
    o = ffill_ciktilari["olcumsuz"]
    assert "DOLDURMA ÖLÇÜLEMEDİ" in o
    assert 'class="belirsiz"' not in o, "ölçülemeyen hâle doldurma İDDİASI basılmış"


def test_doldurma_isareti_MEVCUT_deseni_kullaniyor():
    """Yeni dil İCAT EDİLMEDİ: işaret P5'in `belirsiz()` kanalı (kesik alt çizgi + ZORUNLU
    beyan) ve panonun `_chip`i. RENK YOK — renk bu panoda ÖLÇÜMÜN kanalı, doldurma ise
    ölçümün KÖKENİ hakkında bir şerh (`belirsiz()`in kendi gerekçesi)."""
    assert "belirsiz(" in DOLDURULDU_SRC and "_chip(" in DOLDURULDU_SRC
    assert ".belirsiz{" in CSS, "belirsiz sınıfı CSS'te yok"
    for hue in ("t-no", "t-rv", "t-go", "--red", "--amber", "--green", "warn", "neg", "pos"):
        assert hue not in DOLDURULDU_SRC, f"doldurma işareti renk kanalını kullanıyor: {hue}"
    assert 't-vi' in DOLDURULDU_SRC


def test_beyansiz_kesik_cizgi_YOK(ffill_ciktilari):
    """`belirsiz()` sözleşmesi: beyan olmadan kesik çizgi bir SÜStür. Beyanı çağıran yazar."""
    dolu = ffill_ciktilari["dolu"]
    assert 'title="' in dolu
    # Beyan KAÇIRILMIŞ hâlde durur (kesme işareti `&#39;` olur) — `belirsiz()` esc'liyor.
    assert "trend_shadow._isaretle" in dolu and "şasi ffill" in dolu
    assert "SON BİLİNEN KAPANIŞLA" in dolu


def test_muhasebe_satiri_UYDURMUYOR(ffill_ciktilari):
    """Uç bu alanları servis etmiyorsa satır HİÇ doğmaz — boş bir "0 seans" satırı, ölçülmemiş
    bir defteri temiz göstermek olurdu."""
    assert ffill_ciktilari["satir_yok"] == ""
    var = ffill_ciktilari["satir_var"]
    assert "4 seans" in var and "11 satır bayraktan önce" in var and "7 doldurulmuş hücre" in var
    temiz = ffill_ciktilari["satir_temiz"]
    assert "0 seans" in temiz
    assert "bayraktan önce" not in temiz and "doldurulmuş hücre" not in temiz


def test_YASA6_uretilen_alanlarin_OKUYUCUSU_var():
    """Üretilen her alanın bir okuyucusu olmalı; aksi hâlde alan "yazılıyor ama kimse okumuyor"
    olur. `api.py` özeti olduğu gibi geçiriyor (`trend_kitabi`), okuyucu pano."""
    for alan in ("son_dolduruldu", "dolduruldu_gun", "dolduruldu_olcumsuz", "karar_dolduruldu"):
        assert alan in TS_SRC, f"{alan} kaynakta üretilmiyor"
        assert alan in KOD, f"{alan} panoda OKUNMUYOR (YASA 6)"
    assert "trend_kitabi" in APIPY


def test_web_katmaninda_dolduruldu_dizesi_ARTIK_VAR():
    """Baseline'ın ölçtüğü boşluk: web katmanında "dolduruldu" 0 kez geçiyordu."""
    assert KOD.count("DOLDURULDU") >= 1 and "İleri doldurulan seans" in KOD


# =============================================================================================
# KALEM 3 — `?? 0` / `|| 0` triyajı
# =============================================================================================
# CIRCIR (ratchet). Sayı bir HEDEF değil bir TAVANDIR: bu turda 211'den 181'e indi ve bir daha
# yükselmemeli. Yeni bir `?? 0` eklemek isteyen, önce bu satırı DEĞİŞTİRMEK ve gerekçesini
# yazmak zorunda kalır — sessizce geri sızmasın diye.
#
# BİLİNÇLİ GÜNCELLEME — v-dalga2 (2026-08-09): 181 → 192 (körce DEĞİL; kapının kendi kuralı işledi).
# Dalga-2 (01ba684 + ff55a18) süpürücü ailesine 15 yeni `?? 0` guard'ı ekledi: olay çekmecesi EV_TR
# (`app.js:1179-1187`) + iptal tuşu sınıf dökümü (`app.js:3439`). ON BEŞİ de ELLE (b) SINIFLANDI —
# hepsi ÜRETİCİ-GARANTİLİ bölümleme sayaçlarıdır (YASA-6, uçtan doğrulandı: alpaca.py:487-491 ·
# api/loop olay yazıcıları HER olayda koşulsuz int(...)/len(...) basar, boş kova KAYNAKTA 0'a
# düşer = ÖLÇÜLMÜŞ sıfır, bu deponun zaten (b) saydığı biriktirici/bölümleme deseni). Hiçbiri
# liveness/manşet ölçülemedi-dalına sızmadı (manşet `!= null` üçlemesi kullanır, `?? 0` değil).
# `opCancelOpen`inki AYRICA v225 (test_dalga2_kucukler_v225.py:190) tarafından ZORUNLU. Satır satır:
# research/olcumler/nullsifir_triyaj_2026-08-06/RAPOR.md §7. Frozen 211/167/44/30/137 DEĞİŞMEDİ.
NULLSIFIR_TAVAN = 192


def test_nullsifir_sayisi_CIRCIRI_asmiyor():
    n = _nullsifir_say(APPJS)
    assert n <= NULLSIFIR_TAVAN, (
        f"`?? 0`/`|| 0` sayısı {n} — tavan {NULLSIFIR_TAVAN}. Yeni bir tanesi eklendiyse: "
        f"triyaj raporunu (research/olcumler/nullsifir_triyaj_2026-08-06/RAPOR.md) güncelle "
        f"ve (a)/(b) sınıfını GEREKÇESİYLE yaz.")


def test_kademe1_PARA_ve_R_bicimleyiciden_geciyor():
    """Kademe 1. `$0` ile "harcama ölçülmedi" aynı görünüyordu; `0.00R` ölçülmemiş bir işlemi
    SONUÇLANMIŞ gibi okutuyordu. İkisi de artık dürüst biçimleyiciden geçiyor."""
    assert "${money(sp.spent_usd)}" in KOD
    assert "$${sp.spent_usd ?? 0}" not in KOD
    assert 'Number(t.r || 0).toFixed(2)' not in KOD
    assert 't.r == null ? "—" : isr(t.r, trn(t.r, 2)) + "R"' in KOD


def test_kademe2_OLCULMEMISTEN_guvenli_taraf_IDDIASI_uretilmiyor():
    """Kademe 2 — en sinsi sınıf: bir DEDEKTÖR hiç ölçmediği hâlde temiz rapor veriyordu."""
    assert "boşluk sayısı ÖLÇÜLMEDİ" in KOD          # seans-içi boşluk tarayıcısı
    assert "sapma sayısı ÖLÇÜLMEDİ" in KOD           # evren sapması
    assert "bayat sayısı ÖLÇÜLMEDİ" in KOD           # evren kapsaması
    assert "kuyruk ÖLÇÜLMEDİ" in KOD                 # kanıt dolgusu kuyruğu
    assert "hipotez sayısı ÖLÇÜLMEDİ" in KOD         # hipotez halkasının boş kalma gerekçesi
    for eski in ("const n = g.bosluk_sayisi ?? 0", "const pend = it.backfill_pending || 0",
                 "${ud.n_stale || 0} endeksten düşen", "const n = w.n_hypotheses ?? 0",
                 "taze = n - (m.stale_n || 0)"):
        assert eski not in KOD, f"iddia üreten desen hâlâ orada: {eski!r}"


def test_kademe3_DURUST_BICIMLEYICI_devrede():
    """Kademe 3. `trn()` null'da zaten "—" basıyor; `?? 0` onu bilerek iptal ediyordu. İcra
    gerçekliği masasının (gönderim · ret · dolum · kill ölçütü · mutabakat) 17 çağrı yeri."""
    icra = KOD[KOD.index("const ay = slp2.ayna || {}"):KOD.index("İki motor mutabakatı")]
    assert _nullsifir_say(icra) == 0, "icra/ayna kartında hâlâ `?? 0` var"
    for alan in ("trn(ay.n)", "trn(dl.n_dolan)", "trn(ic.n)", "trn(slp2.n_defter)",
                 "trn(ic.kacan_limit_n)", "trn(mt.ortak_plan_n)"):
        assert alan in KOD, f"{alan} biçimleyiciye bağlanmamış"


def test_stopN_dali_UC_HALLI_kill_olcutu_uydurmuyor():
    """Yan etkinin çivisi: `stopN` çıplaklaşınca satırın DALI da düzeltilmeliydi — aksi hâlde
    değer "—" basarken metin "· ölçüt karşılandı" demeye devam ederdi, yani ÖLÇÜLMEMİŞ bir kill
    ölçütü GEÇMİŞ gibi okunurdu."""
    assert "const stopN = (ay.red_sinifi_dagilimi || {}).stop_vs_current;" in KOD
    assert "— ölçülmedi (alan yükte yok)" in KOD


def test_TRIYAJ_RAPORU_var_ve_sayilari_TUTUYOR():
    """Rapor bir dekor değil bir kayıt: kuyrukta kaç tane kaldığı YAZILI olmalı (sessiz kısaltma
    yok) ve bugünkü dosyadan yeniden ölçülebilmeli."""
    assert RAPOR.exists(), "triyaj raporu yok"
    metin = RAPOR.read_text()
    kalan = _nullsifir_say(APPJS)
    assert f"| `app.js` kalan eşleşme (düzeltme SONRASI) | **{kalan}** |" in metin, \
        "rapordaki kalan sayısı bugünkü dosyayla tutmuyor"
    assert "| — **(a) yalan söyleyenler** | **167** |" in metin
    assert "| — **(b) güvenli** | **44** |" in metin
    assert "| **KUYRUKTA KALAN (a)** | **137** |" in metin
    # Kuyruk SATIR SATIR yazılı: (a) kuyruğu kadar tablo satırı bulunmalı.
    assert metin.count("| a | ") == 137, "kuyruk tablosu eksik — sessiz kısaltma"
    assert metin.count("| b | ") == 44


def test_rapor_AYIRICIYI_beyan_ediyor():
    """Ayırıcı yazılı olmasaydı sınıflandırma denetlenemez bir hüküm olurdu."""
    metin = RAPOR.read_text()
    for cumle in ("YÖNTEM — ayırıcı tek cümlede", "(a) YALAN SÖYLEYENLER", "(b) GÜVENLİ",
                  "SIRALAMA — hangi 30, neden", "ÖLÇÜLEMEYENLER"):
        assert cumle in metin, f"raporda eksik bölüm: {cumle}"


@pytest.mark.skipif(NODE is None, reason="node yok")
def test_node_check_gecer():
    """Sözdizimi kapısı. Tek başına yetmez (v194 dersi: anlam kusuru bu kapıdan geçer) ama üç
    kalemin de yeni bir sözdizimi kusuru getirmediğini söyler."""
    r = subprocess.run([NODE, "--check", str(WEB / "app.js")], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
