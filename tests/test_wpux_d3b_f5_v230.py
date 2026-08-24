"""v230 · WP-UX D3-b — DÖRDÜNCÜ FIRSAT YÜZEYİ (F5 · YİNELENEN ARIZA TAKSONOMİSİ).

docs/TASARIM-YONU-2026-08-07 §7'nin kalan on beş FIRSAT satırından bir tanesi daha PANO bacağına
indi (F1/F2/F14 v229'da inmişti):

  F5 — Yinelenen arızaları taksonomiye kümeleme (③ saglik#operasyon · "alarm gürültüsünün kökü").
    `watchdog.alarm_gunluk` v192'den beri mekanizma başına GÜNLÜK {alarm · bastırılan · askıda}
    sayacını yazıyordu; `test_alarm_hijyeni_v192::test_bastirma_sayaci_PANOYA_cikar` "sayacın DIŞ
    okuyucusu api.py'dir" der — yani sayı UCA çıkıyordu ama HİÇBİR PANO YÜZEYİ onu çizmiyordu
    (YASA 6 boşluğu; "üretiliyor ama görünmüyor" kovası). `firsatAlarmTaksonomi` o defterin İLK
    pano okuyucusudur: her satır bir mekanizma (arıza sınıfı), en gürültülü üstte; ALARM üretilen ·
    BASTIRILDI tavana takılıp susturulan (SESSİZ DEĞİL, sayılı) · ASKIDA alarm hiç üretmeyen MEŞRU
    bekleme (kota soğuması / kimlik havuzu). Bastırma ile askıda AYRI kovadır.

Kart MEVCUT sözleşmenin üstüne oturur: kart sözleşmesi (v198 · kartOzeti/katKart), ÖLÇÜLEMEDİ≠0
(v191/v196 · `?? 0`/`|| 0` yok), D1'in renk rolleri (RENK YOK — taksonomi bir sayım, bir şiddet
değil) ve UÇTAN okuma (uydurma rakam yasağı; landing-fabricated-figures dersi). Yeni jeton/renk/
bileşen YOK; `.trow` tablosu (F1 emsali) — `ozetSerit` bütçesine (v191) DOKUNULMADI.

TESTLER HEM DAVRANIŞA HEM KAYNAĞA BAKAR (v196/v198/v229 deseni): saf fonksiyon Node'da FİİLEN
koşturulur — "kaynakta doğru görünen şablon çalışma zamanında başka şey basıyor" sınıfını yakalar.
Alt-düzey biçimleyiciler (trn/pctf/isr/kanitOrani) v229 emsaliyle harness'te SADIK kopyadır; ölçülen
fonksiyonun (firsatAlarmTaksonomi + kartOzeti/hucreGovde zinciri) KENDİ kaynağı çıkarılıp koşturulur.
"""
from __future__ import annotations

import json
import pathlib
import re
import shutil
import subprocess

import pytest

SRC = pathlib.Path(__file__).resolve().parents[1]
WEB = SRC / "meridian" / "web"
APPJS = (WEB / "app.js").read_text()
INDEX = (WEB / "index.html").read_text()

NODE = shutil.which("node")

# Yorumsuz gövde (v191/v229 deseni): bir kuralın GEREKÇESİNİ anlatan yorum, o kuralın ihlali/beyanı
# sanılmamalı — bu turun fonksiyonu kaldırdığı/eklediği deseni yorumda ADIYLA anlatıyor.
KOD = "\n".join(l for l in APPJS.splitlines() if not l.lstrip().startswith("//"))


def _flat(s: str) -> str:
    return re.sub(r"\s+", " ", s)


def _fn(ad: str, kaynak: str = APPJS) -> str:
    """Fonksiyon/tek-satırlık-const dilimi (v198/v229 `_fn` deseni)."""
    if f"function {ad}(" in kaynak:
        i = kaynak.index(f"function {ad}(")
        parcalar = []
        for ln in kaynak[i:].splitlines(keepends=True):
            parcalar.append(ln)
            if ln.rstrip("\n") == "}":
                break
        return "".join(parcalar)
    i = kaynak.index(f"const {ad} = ")
    return kaynak[i:kaynak.index("\n", i) + 1]


def _obj(ad: str) -> str:
    """Çok satırlı const nesne dilimi (`const AD = { … \\n};`)."""
    i = APPJS.index(f"const {ad} = {{")
    return APPJS[i:APPJS.index("\n};", i) + len("\n};")]


# Alt-düzey biçimleyiciler — SADIK kopya (v229 harness emsali). Türkçe locale yerine "en-US"
# kullanılır ki binlik ayırıcı testte kararlı olsun — biçim değil, DAL mantığı ölçülüyor.
_STUBS = """
const trn = (x, d = 0) => { const n = Number(x); return (x == null || !Number.isFinite(n)) ? "\\u2014"
  : n.toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d }); };
const pctf = (x, d = 2) => { const n = Number(x); return (x == null || !Number.isFinite(n)) ? "\\u2014"
  : "%" + (n * 100).toFixed(d); };
const isr = (x, metin) => { const n = Number(x); if (x == null || !Number.isFinite(n) || n <= 0) return metin;
  const s = String(metin); return (s[0] === "%" || s[0] === "$") ? s[0] + "+" + s.slice(1) : "+" + s; };
const KANIT_TAVAN_N = 61;
const kanitOrani = n => (!n || !Number.isFinite(Number(n))) ? null
  : Math.min(1, Math.log10(Number(n) + 1) / Math.log10(KANIT_TAVAN_N));
const AZ_ORNEK_N = 10;
const azOrnek = n => n != null && Number.isFinite(Number(n)) && Number(n) < AZ_ORNEK_N;
"""

_GERCEK = ["esc", "hucreCubuk", "hucreGovde", "kartOzeti", "firsatBos", "katKart",
           "firsatAlarmTaksonomi"]


def _harness_govde() -> str:
    return _STUBS + "\n" + _obj("KART_KAYDI") + "\n" + "\n".join(_fn(f) for f in _GERCEK)


# ---- FİKSTÜRLER ------------------------------------------------------------------------------
_F5 = {
    # DOLU: üç mekanizma — biri gürültülü + AĞIR bastırma, biri askıda (neden'li), biri temiz.
    # scheduler_poll gürültü = 1+11 = 12 (en üstte olmalı) · mirror_reconcile 2 · hermes_poll 0.
    "dolu": {"gun": "2026-08-09", "durum": "dolu",
             "mekanizmalar": {
                 "hermes_poll": {"alarm": 0, "bastirilan": 0, "askida": 2,
                                 "son_askida_neden": "kota_sogumasi"},
                 "scheduler_poll": {"alarm": 1, "bastirilan": 11, "askida": 0,
                                    "son_askida_neden": None},
                 "mirror_reconcile": {"alarm": 2, "bastirilan": 0, "askida": 0,
                                      "son_askida_neden": None}},
             "n_alarm": 3, "n_bastirilan": 11, "n_askida": 2, "tavan": 3,
             "beyan": "mekanizma başına GÜNLÜK alarm tavanı (v192)."},
    # TEMİZ: dolu ama 0 bastırma → rozet YOK (kapak kapalı kalır), '0 bastırıldı' UYDURMA DEĞİL.
    "temiz": {"gun": "2026-08-09", "durum": "dolu",
              "mekanizmalar": {"mirror_reconcile": {"alarm": 2, "bastirilan": 0, "askida": 0}},
              "n_alarm": 2, "n_bastirilan": 0, "n_askida": 0, "tavan": 3, "beyan": "tavan (v192)."},
    # DEFTER YOK: defter bugün yazılmadı — '0 alarm' DEĞİL, üçüncü hâl.
    "defter_yok": {"gun": None, "mekanizmalar": {}, "n_alarm": 0, "n_bastirilan": 0,
                   "durum": "defter_yok",
                   "beyan": "bugün hiç mekanizma-gecikme alarmı üretilmedi (defter yazılmadı)"},
    "yok": None,     # uç düştü
}

_DRIVER = """
const F5 = %(f5)s;
const out = {};
for (const [k, v] of Object.entries(F5)) out[k] = firsatAlarmTaksonomi(v);
process.stdout.write(JSON.stringify(out));
"""


@pytest.fixture(scope="module")
def ciktilar():
    if NODE is None:
        pytest.skip("node yok")
    betik = _harness_govde() + _DRIVER % {"f5": json.dumps(_F5, ensure_ascii=False)}
    p = subprocess.run([NODE, "-e", betik], capture_output=True, text=True, timeout=60)
    assert p.returncode == 0, f"F5 dilimi Node'da patladı:\n{p.stderr}"
    return json.loads(p.stdout)


# =============================================================================================
# F5 — DAVRANIŞ
# =============================================================================================
def test_f5_taksonomi_mekanizma_basina_kumeleniyor(ciktilar):
    """Her mekanizma bir satır (arıza sınıfı); üç sütun başlığı + kartın kimliği ekranda."""
    h = ciktilar["dolu"]
    assert 'data-kart="operasyon:alarmkok"' in h
    for mek in ("scheduler_poll", "hermes_poll", "mirror_reconcile"):
        assert mek in h, f"{mek} taksonomide yok"
    fl = _flat(h)
    assert "MEKANİZMA" in fl and "ALARM" in fl and "BASTIRILDI" in fl and "ASKIDA" in fl


def test_f5_bastirma_GORUNUR_ve_rozet(ciktilar):
    """İş emrinin çivisi: bastırma görünmezse hijyen ile körlük ayırt edilemez. 11 bastırma
    satırda + özet rozetinde ('11 BASTIRILDI') + alt toplamda görünür."""
    h = ciktilar["dolu"]
    assert "11" in h, "bastırılan sayı ekranda değil"
    fl = _flat(h)
    assert "11 BASTIRILDI" in fl, "bastırma özet rozetine taşınmıyor (kapağı açan dikkat işareti)"
    # Rozet `data-dikkat="1"` doğurur → kurucu kartı AÇAR: bastırma kapak yüzünden gizlenemez.
    assert 'data-dikkat="1"' in h, "bastırma varken kapak açan dikkat işareti (rozet) doğmuyor"
    assert "bastırma görünmezse" in fl or "hijyen ile körlük" in fl, "bastırmanın NEDEN önemli olduğu yazmıyor"


def test_f5_askida_bastirmadan_AYRI_kovada(ciktilar):
    """ASKIDA ≠ BASTIRILAN: askıda alarm hiç üretmeyen MEŞRU bekleme; ayrı sütun + son neden."""
    fl = _flat(ciktilar["dolu"])
    assert "kota_sogumasi" in fl, "askıda mekanizmanın son nedeni (son_askida_neden) ekranda yok"
    assert "MEŞRU bekleme" in fl and "AYRI kova" in fl, "askıda/bastırma ayrımı beyan edilmiyor"


def test_f5_en_gurultulu_USTTE(ciktilar):
    """Taksonominin işi KÖKÜ göstermek: en gürültülü mekanizma (alarm+bastırılan) üstte.
    scheduler_poll (1+11=12) > mirror_reconcile (2) > hermes_poll (0)."""
    h = ciktilar["dolu"]
    i_sch = h.index("scheduler_poll")
    i_mir = h.index("mirror_reconcile")
    i_her = h.index("hermes_poll")
    assert i_sch < i_mir < i_her, f"sıra kökü göstermiyor: sch={i_sch} mir={i_mir} her={i_her}"


def test_f5_temiz_gun_rozet_YOK_bastirma_uydurmaz(ciktilar):
    """0 bastırma bir BAŞARIsızlık değil temiz bir gündür: 'BASTIRILDI' rozeti DOĞMAZ (kapak
    kapalı kalır) ve alt satır 'bastırma yok' der — '0 bastırıldı' uydurma bir alarm değil."""
    h = ciktilar["temiz"]
    fl = _flat(h)
    # Dikkat işareti (kapağı açan `data-dikkat`) rozetten doğar; 0 bastırmada rozet="" → işaret YOK.
    assert 'data-dikkat="1"' not in h, "0 bastırmada dikkat işareti doğmuş — kapak gereksiz açılıyor"
    assert "11 BASTIRILDI" not in fl, "temiz günde bir bastırma rozeti uydurulmuş"
    assert "bastırma yok" in fl, "temiz günde bastırma yokluğu beyan edilmiyor"


def test_f5_defter_yok_SIFIR_uydurmaz(ciktilar):
    """'0 alarm' ile 'defter yazılmadı' AYRI şeydir (üçüncü hâl). Defter yoksa kart bir CÜMLE
    basar, uydurma bir sıfır tablo DEĞİL."""
    h = ciktilar["defter_yok"]
    fl = _flat(h)
    assert "DEFTER YAZILMADI" in h
    assert "defter yazılmadı" in fl and "0 alarm" in fl and "aynı kovaya düşmez" in fl
    assert ">0<" not in h, "defter yokken uydurma bir sıfır basılmış"
    # Mekanizma tablosu HİÇ çizilmez (satır yok).
    assert "MEKANİZMA</span>" not in h, "boş defterde taksonomi tablosu çiziliyor"


def test_f5_uc_dustu_OLCULEMEDI(ciktilar):
    """Uç düştü: 'ÖLÇÜLEMEDİ' + KAYNAK adı; '0 alarm' UYDURMAZ."""
    h = ciktilar["yok"]
    assert "ÖLÇÜLEMEDİ" in h and "alarm_gunluk" in h
    assert ">0<" not in h, "uç düştüğünde uydurma sıfır basılmış"


# =============================================================================================
# KAYNAK / SÖZLEŞME — kayıt, bağ (YASA 6), jeton, uydurma, ozetSerit, CSP, node --check
# =============================================================================================
def test_f5_kartin_KAYDI_ve_BOLUMU_dogru():
    """Kart KART_KAYDI'da doğru yüzey/bölümle kayıtlı (③ saglik#operasyon)."""
    kayit = _obj("KART_KAYDI")
    assert '"operasyon:alarmkok": { alan: "saglik",  bolum: "operasyon" }' in kayit


def test_f5_BOLUMUNE_baglandi_YASA6():
    """YASA 6: kartın bir çağıranı var (aksi hâlde çizilmez). RENDER.operasyon `alarm_gunluk`ı
    okur ve firsatAlarmTaksonomi'ye verir."""
    op = KOD[KOD.index("RENDER.operasyon = "):KOD.index("RENDER.cizelge = ")]
    assert "firsatAlarmTaksonomi(" in op, "kart RENDER.operasyon'a bağlanmamış"
    assert "watchdog" in op and "alarm_gunluk" in op, "kart alarm_gunluk defterini okumuyor"


def test_f5_v192_pano_okuyucusu_NIHAYET_var():
    """`test_alarm_hijyeni_v192::test_bastirma_sayaci_PANOYA_cikar` sayacın DIŞ okuyucusunu
    'api.py'dir' diye çiviliyordu — yani sayı UCA çıkıyor, PANO çizmiyordu (YASA 6 boşluğu). F5 o
    boşluğu kapatır: fonksiyon defterin ALANLARINI (mekanizmalar/bastırılan/alarm) fiilen okur."""
    fn = _fn("firsatAlarmTaksonomi")
    for alan in ("mekanizmalar", "n_bastirilan", "n_alarm", "bastirilan", "askida", "son_askida_neden"):
        assert alan in fn, f"{alan} F5'te okunmuyor — v192 sayacının pano okuyucusu eksik"


def test_f5_yeni_ozetSerit_serit_ACILMADI():
    """F5 `.trow` tablosuyla çizer (ozetSerit DEĞİL) → v191 `_SERIT_BOLGELERI` bütçesine
    dokunulmadı; ozetSerit çağrı sayısı v226/v229 tabanında (6) kalır."""
    # 2026-08-24 (operatör turu): ALTI → YEDİ. Artış bir EKLEME değil bir BÖLÜNMEDİR:
    # «bir sonraki açılış» kartı Bugün'e taşınırken şeridini yanında götürdü, Adaylar
    # bölümü de kendi şeridini geri aldı — ve ikisinin PAYDASI FARKLI (son seans ↔
    # pencerenin tamamı). İki payda iki şerit demektir; aynı etiketi iki farklı paydayla
    # basmak v192'nin kapattığı kusurdu. Beyan: v191 `_SERIT_BOLGELERI` (yedi bölge).
    assert APPJS.count("ozetSerit([") == 7, "ozetSerit sayısı değişti — v191 _SERIT_BOLGELERI güncellenmeli"


def test_f5_UYDURMA_SIFIR_getirmedi():
    """`?? 0`/`|| 0` tavanı (v196/v229): F5 ölçülemedi≠0'ı EXPLICIT null denetimiyle kurar; tek
    bir null-sıfır katlaması eklemez (sayaçlar `trn` ile basılır — 0 'ölçülen', '—' 'yok')."""
    nf = re.compile(r"(\?\?|\|\|)\s*0(?![\d.])")
    g = "\n".join(l for l in _fn("firsatAlarmTaksonomi").splitlines() if not l.lstrip().startswith("//"))
    assert not nf.search(g), "firsatAlarmTaksonomi `?? 0`/`|| 0` içeriyor — ÖLÇÜLEMEDİ≠0 explicit kurulmalı"


def test_f5_YENI_RENK_JETONU_ACMAZ():
    """D1 + CSP: taksonomi bir ŞİDDET DEĞİL bir sayımdır → ham hue (--red/--amber/--green) OKUMAZ
    ve yeni bir renk jetonu açmaz (renk yalnız anomalide; dikkat rozetle taşınır)."""
    g = _fn("firsatAlarmTaksonomi")
    for hue in ("--red", "--amber", "--green"):
        assert hue not in g, f"firsatAlarmTaksonomi ham hue okuyor: {hue}"


def test_f5_CSP_satir_ici_olay_ozniteligi_YOK():
    """CSP script-src 'self': kart salt-okumadır, satır içi `onclick`/`on*` YOK, dış kaynak YOK."""
    g = _fn("firsatAlarmTaksonomi")
    assert not re.search(r'\son[a-z]+="', g), "firsatAlarmTaksonomi satır içi olay özniteliği taşıyor (CSP)"
    assert "http://" not in g and "https://" not in g


@pytest.mark.skipif(NODE is None, reason="node yok")
def test_node_check_gecer():
    r = subprocess.run([NODE, "--check", str(WEB / "app.js")], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
