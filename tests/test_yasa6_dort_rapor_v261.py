"""v261 — DÖRT OKUYUCUSUZ BEKÇİ RAPORU PANOYA BAĞLANIR (WP8 · YASA 6 kapanışı).

ÖLÇÜLEN BOŞLUK (docs/TASARIM-F8-DURUM-SOZLUGU-2026-08-22.md §T2): `goal_failure_report` ·
`kitap_damga_report` · `mutabakat_tazelik_report` · `onayli_gonderim_report` dördü de
watchdog'da üretiliyor, alarm satırı akışa düşüyor ama DURUM YÜZEYİ yok — hiçbir uç servis
etmiyor, app.js 0 okuma. Operatör "şu an ne âlemde" sorusunu ancak son alarmı bularak
cevaplayabiliyor. Bu dördü fonksiyon olduğu için `codelaw.artifact_graph` onları göremez:
mevcut YASA-6 denetimi bu sınıfa YAPISAL olarak kör — çivileri bu dosya taşır.

SÖZLEŞME (testler bunu çiviler):
  * `/api/diagnostics` `bekci_durumlari` bloğunu servis eder (dört anahtar; rapor OLDUĞU
    GİBİ geçer — F8 geçiş haritası "ÖNCE yüzey aç, sonra adlandır" der, alan çevrilmez).
  * Rapor başına YALITIM: biri düşerse üçü ayakta kalır, düşen iskeletle görünür
    (`olculemedi` + `olculemedi_neden`) — 0'a/temiz'e çevrilmez.
  * `kitap_damga_report` PERSIST'SİZ çağrılır: taban yalnız `check_kitap_damga_and_alarm`da
    ilerler; okuma yolu tabana yazsaydı dedektörü körleştirirdi (raporun kendi sözleşmesi).
  * Pano dar okuyucu `bekciDurumlari(bd)` ile okur; üç değerli hüküm AYRI görünür
    (TEMİZ / İHLAL / ÖLÇÜLEMEDİ / KAPSAM DIŞI — kanonik sözlük §4b) ve null bir sayıya
    ASLA 0 basılmaz (v196 yasası: null = ölçülemedi ≠ 0).

TESTLER HEM KAYNAĞA HEM DAVRANIŞA BAKAR (repo deseni: v196 · v259): kaynak çivisi dizgiyi,
Node koşusu şablonun ÇALIŞMA ZAMANI çıktısını ölçer.
"""
from __future__ import annotations

import ast
import json
import pathlib
import re
import shutil
import subprocess

import pytest

SRC = pathlib.Path(__file__).resolve().parents[1]
APIPY = (SRC / "meridian" / "api.py").read_text(encoding="utf-8")
APPJS = (SRC / "meridian" / "web" / "app.js").read_text(encoding="utf-8")
NODE = shutil.which("node")

DORT_ANAHTAR = ("goal_failure", "kitap_damga", "mutabakat_tazelik", "onayli_gonderim")

# v196 çırçırının deseni: yorum satırları düşülür — kuralın GEREKÇESİNİ anlatan yorum,
# kuralın ihlali sanılmamalı.
NULLSIFIR = re.compile(r"(\?\?|\|\|)\s*0(?![\d.])")


def _js_blok(bas: str) -> str:
    """`bas` ile başlayan satırdan, tek başına `}` olan kapanış satırına kadarki app.js dilimi."""
    i = APPJS.index(bas)
    parcalar = []
    for ln in APPJS[i:].splitlines(keepends=True):
        parcalar.append(ln)
        if ln.rstrip("\n") == "}" and len(parcalar) > 1:
            return "".join(parcalar)
    raise AssertionError(f"kapanış bulunamadı: {bas}")


def _js_satir(baslangic: str) -> str:
    for ln in APPJS.splitlines():
        if ln.startswith(baslangic):
            return ln
    raise AssertionError(f"satır yok: {baslangic}")


def _py_fn(ad: str) -> ast.FunctionDef | None:
    for d in ast.walk(ast.parse(APIPY)):
        if isinstance(d, ast.FunctionDef) and d.name == ad:
            return d
    return None


# =============================================================================================
# §1 — ÜRETİM UCU: /api/diagnostics `bekci_durumlari` bloğu
# =============================================================================================

def test_api_bekci_durumlari_fonksiyonu_var():
    assert _py_fn("_bekci_durumlari") is not None, \
        "_bekci_durumlari YOK — dört bekçi raporunun servis yüzeyi kurulmamış (T2 açık)"


def test_diagnostics_yaniti_blogu_tasir():
    """Fonksiyonun var olması yetmez — `/api/diagnostics` yanıtı onu TAŞIMALI (ölü kod değil)."""
    govde = APIPY[APIPY.index("def api_diagnostics"):]
    govde = govde[:govde.index("@app.get")]
    assert '"bekci_durumlari"' in govde and "_bekci_durumlari(" in govde, \
        "/api/diagnostics `bekci_durumlari` bloğunu servis etmiyor — YASA 6 borcu duruyor"


def test_dort_rapor_oldugu_gibi_gecer(monkeypatch):
    """Blok dört raporu ANAHTAR ADIYLA ve İÇERİĞİNE DOKUNMADAN taşır (sentez yok, uydurma yok)."""
    from meridian import api, watchdog
    yukler = {
        "goal_failure_report": {"failed": False, "threshold": -0.05, "realized_30d": 0.012,
                                "n": 31, "detail": "çivi"},
        "kitap_damga_report": {"ok": True, "olculemedi": False, "damgasiz": [], "rows": [],
                               "izlenen": ["portfolio.json"]},
        "mutabakat_tazelik_report": {"ok": True, "olculemedi": False, "kapsam_disi": False,
                                     "neden": "", "yas_h": 2.5},
        "onayli_gonderim_report": {"ok": True, "olculemedi": False, "kapsam_disi": False,
                                   "neden": "", "ihlaller": [], "kontrol_edilen": 3},
    }
    for fn, yuk in yukler.items():
        monkeypatch.setattr(watchdog, fn, lambda _y=yuk: _y)
    out = api._bekci_durumlari()
    assert set(out) == set(DORT_ANAHTAR), f"anahtar kümesi yanlış: {sorted(out)}"
    assert out["goal_failure"] == yukler["goal_failure_report"]
    assert out["kitap_damga"] == yukler["kitap_damga_report"]
    assert out["mutabakat_tazelik"] == yukler["mutabakat_tazelik_report"]
    assert out["onayli_gonderim"] == yukler["onayli_gonderim_report"]


def test_dusen_rapor_yalitilir_ve_iskeletle_gorunur(monkeypatch):
    """Bir bekçinin düşmesi teşhis ucunun tamamını düşürmez; düşen 'temiz' DEĞİL
    ÖLÇÜLEMEDİ olarak, nedeniyle görünür (uydurma yasağı)."""
    from meridian import api, watchdog

    def _patla():
        raise RuntimeError("bilerek: kapsam çivisi")

    monkeypatch.setattr(watchdog, "mutabakat_tazelik_report", _patla)
    monkeypatch.setattr(watchdog, "goal_failure_report",
                        lambda: {"failed": None, "threshold": None, "realized_30d": None,
                                 "detail": "sabit"})
    monkeypatch.setattr(watchdog, "kitap_damga_report",
                        lambda persist=False: {"ok": True, "olculemedi": False,
                                               "damgasiz": [], "rows": [], "izlenen": []})
    monkeypatch.setattr(watchdog, "onayli_gonderim_report",
                        lambda: {"ok": True, "olculemedi": False, "kapsam_disi": False,
                                 "neden": "", "ihlaller": [], "kontrol_edilen": 0})
    out = api._bekci_durumlari()
    mt = out["mutabakat_tazelik"]
    assert mt.get("ok") is None and mt.get("olculemedi") is True
    assert "RuntimeError" in str(mt.get("olculemedi_neden")), \
        "düşüşün nedeni iskelette YOK — sessiz yutma"
    assert out["kitap_damga"].get("ok") is True, "komşu rapor yalıtılmadı"
    assert out["goal_failure"].get("detail") == "sabit"


def test_kitap_damga_persistsiz_cagirilir():
    """EN KRİTİK API ÇİVİSİ. Taban yalnız `check_kitap_damga_and_alarm`da ilerler; servis
    yolu `persist=True` geçirirse her pano isteği tabanı ezer ve dedektör KÖRLEŞİR
    (kitap_damga_report'un kendi sözleşmesi — '/api/diagnostics'i açık tutmak dedektörü
    körleştirirdi')."""
    f = _py_fn("_bekci_durumlari")
    assert f is not None
    assert "persist" not in ast.unparse(f), \
        "_bekci_durumlari persist parametresine dokunuyor — okuma yolu tabana yazamaz"


def test_gercek_kosut_sandbox_taban_dosyasi_yazmaz(sandbox_state):
    """Davranış çivisi: GERÇEK raporlar boş sandbox'ta koşar — uç dört anahtarı üretir ve
    kitap-damga taban dosyası (entity_damga.json) YAZILMAZ (okuma yolu tabana dokunmaz)."""
    from meridian import api, watchdog
    out = api._bekci_durumlari()
    assert set(out) == set(DORT_ANAHTAR)
    assert not (sandbox_state / watchdog.DAMGA_FILE).exists(), \
        "servis yolu kitap-damga TABANINI yazdı — dedektör körleşir (persist sızıntısı)"
    # boş sandbox'ta hüküm UYDURULMAZ: kitap yok → ölçülemedi (temiz değil)
    assert out["kitap_damga"].get("ok") is None
    assert out["kitap_damga"].get("olculemedi") is True


# =============================================================================================
# §2 — PANO OKUYUCUSU: dar fonksiyon `bekciDurumlari(bd)`
# =============================================================================================
def _okuyucu() -> str:
    """Okuyucu bölgesi = sınıf sözlüğü satırı + dar fonksiyon gövdesi (ikisi tek sözleşme)."""
    assert "function bekciDurumlari(" in APPJS, \
        "pano okuyucusu YOK — dört rapor hâlâ okuyucusuz (YASA 6)"
    return _js_satir("const BEKCI_SINIF_TR = ") + "\n" + _js_blok("function bekciDurumlari(")


def test_pano_dort_anahtari_okur():
    govde = _okuyucu()
    for k in DORT_ANAHTAR:
        assert k in govde, f"okuyucu `{k}` raporunu OKUMUYOR — yüzey yarım"


def test_operasyon_sayfasi_okuyucuyu_cagirir():
    """Fonksiyonun varlığı yetmez: Gözetim & Alarmlar sayfası onu ÇİZMELİ (ölü kod değil)."""
    i = APPJS.index("RENDER.operasyon = async")
    govde = APPJS[i:APPJS.index("RENDER.cizelge", i)]
    assert "bekciDurumlari(" in govde, \
        "RENDER.operasyon okuyucuyu çağırmıyor — kart hiçbir sayfada çizilmez"
    assert "bekci_durumlari" in govde, "çağrıya teşhis yükünün bloğu verilmiyor"


def test_okuyucuda_nullsifir_yok():
    """v196 yasası yeni kodda: `?? 0` / `|| 0` SIFIR eşleşme (çırçır 192 tavanına tek
    satır bile eklenmez)."""
    govde = _okuyucu()
    n = sum(len(NULLSIFIR.findall(l)) for l in govde.splitlines()
            if not l.lstrip().startswith("//"))
    assert n == 0, f"okuyucuda {n} adet `?? 0`/`|| 0` — null 0'a bulaştırılıyor"


def test_okuyucu_kanonik_kelimeleri_kullanir():
    """Kanonik sözlük §4b: hüküm kelimeleri TEMİZ · İHLAL · ÖLÇÜLEMEDİ · KAPSAM DIŞI.
    Kitap damgası taksonomisi kendi kelimelerini panoya ADIYLA çıkarır."""
    govde = _okuyucu()
    for kelime in ("TEMİZ", "ÖLÇÜLEMEDİ", "KAPSAM DIŞI"):
        assert kelime in govde, f"kanonik hüküm kelimesi yok: {kelime}"
    for sinif in ("damgasiz_yazim", "damga_ilerledi_icerik_ayni"):
        assert sinif in govde, f"kitap damga sınıfı panoya çıkmıyor: {sinif}"


# ---- Node davranış koşusu (v196 deseni: şablon dilimi FİİLEN koşar) --------------------------
_HARNESS = """
%(esc)s
%(trn)s
%(chip)s
%(sinif_tr)s
%(fn)s
const FIX = %(fikstur)s;
const out = {};
for (const [ad, yuk] of Object.entries(FIX)) out[ad] = bekciDurumlari(yuk);
console.log(JSON.stringify(out));
"""

FIKSTUR = {
    # uç bloğu hiç vermedi → dört bekçinin durumu ÖLÇÜLEMEDİ (temiz DEĞİL)
    "yok": None,
    # dördü ölçülmüş-temiz
    "temiz": {
        "goal_failure": {"failed": False, "threshold": -0.05, "realized_30d": 0.012, "n": 31,
                         "detail": "30g getiri +1.20% >= esik -5.00%"},
        "kitap_damga": {"ok": True, "olculemedi": False, "damgasiz": [],
                        "izlenen": ["portfolio.json"],
                        "rows": [{"ad": "portfolio.json", "sinif": "degisim_yok",
                                  "detay": "içerik ve damga aynı"}]},
        "mutabakat_tazelik": {"ok": True, "olculemedi": False, "kapsam_disi": False,
                              "neden": "", "kayit_seansi": "2026-08-21",
                              "kitap_seansi": "2026-08-21", "yas_h": 2.5,
                              "checked": True, "api_ok": True},
        "onayli_gonderim": {"ok": True, "olculemedi": False, "kapsam_disi": False, "neden": "",
                            "ihlaller": [], "kontrol_edilen": 3,
                            "payda_beyani": "operatör-onaylı açık iç pozisyon"},
    },
    # EN KRİTİK FİKSTÜR — null ≠ 0: sayılar ölçülemedi, 0 BASILMAZ
    "olculemedi": {
        "goal_failure": {"failed": None, "threshold": -0.05, "realized_30d": None, "n": 2,
                         "min_sample": 20, "detail": "2/20 kapanan işlem — hüküm None"},
        "kitap_damga": {"ok": None, "olculemedi": True, "damgasiz": [],
                        "izlenen": ["portfolio.json"],
                        "rows": [{"ad": "portfolio.json", "sinif": "olculemedi",
                                  "detay": "belge okunamadı"}]},
        "mutabakat_tazelik": {"ok": None, "olculemedi": True, "kapsam_disi": False,
                              "neden": "broker_reconcile.json yok/okunamadı",
                              "kayit_seansi": None, "kitap_seansi": None, "yas_h": None,
                              "checked": None, "api_ok": None},
        "onayli_gonderim": {"ok": None, "olculemedi": True, "kapsam_disi": False,
                            "neden": "reconcile fotoğrafı yok", "ihlaller": [],
                            "kontrol_edilen": 0},
    },
    # ihlal hâli: renk/etiket yalnız anomalide
    "ihlal": {
        "goal_failure": {"failed": True, "threshold": -0.05, "realized_30d": -0.081, "n": 40,
                         "detail": "SÖZLEŞME HÜKMÜ"},
        "kitap_damga": {"ok": False, "olculemedi": False, "damgasiz": ["portfolio.json"],
                        "izlenen": ["portfolio.json"],
                        "rows": [{"ad": "portfolio.json", "sinif": "damgasiz_yazim",
                                  "detay": "yazım store kapısından geçmedi"}]},
        "mutabakat_tazelik": {"ok": False, "olculemedi": False, "kapsam_disi": False,
                              "neden": "kayıt 2026-08-18 seansından, kitap 2026-08-21",
                              "kayit_seansi": "2026-08-18", "kitap_seansi": "2026-08-21",
                              "yas_h": 71.3, "checked": True, "api_ok": True},
        "onayli_gonderim": {"ok": False, "olculemedi": False, "kapsam_disi": False, "neden": "",
                            "ihlaller": [{"ticker": "VLO", "plan_id": "P-1",
                                          "gonderim_izi": False, "onay_ts": "2026-08-20"}],
                            "kontrol_edilen": 4},
    },
    # kapsam dışı: yapılandırma hâli — ne temiz ne ihlal ne arıza
    "kapsamdisi": {
        "goal_failure": {"failed": None, "threshold": None, "realized_30d": None,
                         "detail": "failure_below tanımlı değil"},
        "kitap_damga": {"ok": True, "olculemedi": False, "damgasiz": [], "izlenen": [], "rows": []},
        "mutabakat_tazelik": {"ok": None, "olculemedi": True, "kapsam_disi": True,
                              "neden": "broker=internal — ayna yok"},
        "onayli_gonderim": {"ok": None, "olculemedi": True, "kapsam_disi": True,
                            "neden": "broker=internal — ayna yok", "ihlaller": [],
                            "kontrol_edilen": 0},
    },
}


@pytest.fixture(scope="module")
def node_cikti():
    if NODE is None:
        pytest.skip("node yok")
    kaynak = _HARNESS % {
        "esc": _js_satir("const esc = "),
        "trn": _js_satir("const trn = "),
        "chip": _js_satir("function _chip(txt, cls)"),
        "sinif_tr": _js_satir("const BEKCI_SINIF_TR = "),
        "fn": _js_blok("function bekciDurumlari("),
        "fikstur": json.dumps(FIKSTUR, ensure_ascii=False),
    }
    p = subprocess.run([NODE, "-e", kaynak], capture_output=True, text=True, timeout=30)
    assert p.returncode == 0, f"node koşusu düştü:\n{p.stderr}"
    return json.loads(p.stdout)


def test_node_blok_yoksa_olculemedi_der(node_cikti):
    out = node_cikti["yok"]
    assert "ÖLÇÜLEMEDİ" in out, "uç bloğu vermedi ama kart bunu SÖYLEMİYOR"
    assert "TEMİZ" not in out, "ölçülemeyen dört bekçi 'temiz' kılığında"


def test_node_temiz_halde_dort_temiz(node_cikti):
    out = node_cikti["temiz"]
    assert out.count("TEMİZ") >= 4, "dört ölçülmüş-temiz rapor dört TEMİZ hüküm basmalı"
    assert "ÖLÇÜLEMEDİ" not in out


def test_node_null_sayiya_sifir_basilmaz(node_cikti):
    """EN KRİTİK ÇİVİ (kasıtlı-kırmızı ile doğrulanır). `yas_h=null` → '0' DEĞİL 'ölçülemedi';
    `realized_30d=null` → yüzde uydurulmaz. v196 yasasının bu karttaki hâli."""
    out = node_cikti["olculemedi"]
    assert out.count("ÖLÇÜLEMEDİ") >= 4, "dört ölçülemeyen rapor dört ÖLÇÜLEMEDİ hüküm basmalı"
    assert "0,0 sa" not in out and "0 sa önce" not in out, \
        "yaş null'ken 0 basıldı — null bulaştırma (v196 ihlali)"
    assert "%0" not in out, "getiri null'ken %0 basıldı — null bulaştırma"
    assert "TEMİZ" not in out, "ölçülemeyen hüküm temiz kılığında"


def test_node_ihlal_halde_etiketler(node_cikti):
    out = node_cikti["ihlal"]
    assert "İHLAL" in out or "DAMGASIZ" in out, "ihlal hâli hükümsüz basılıyor"
    assert "VLO" in out, "onaylı-gönderim ihlal listesi (ticker) kartta görünmüyor"
    assert "TEMİZ" not in out


def test_node_kapsam_disi_ayri_gorunur(node_cikti):
    """KAPSAM DIŞI ≠ ÖLÇÜLEMEDİ: dahili brokerde ayna bekçileri arıza değil yapılandırma
    hâlindedir (koruma dedektörünün üç-hâl disiplini)."""
    out = node_cikti["kapsamdisi"]
    assert "KAPSAM DIŞI" in out, "kapsam_disi hâli ayrı kelimeyle yazılmıyor"
