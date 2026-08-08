"""v219 · DALGA W4-N5 — PANO GÖRÜNÜRLÜĞÜ: dört ölçülmüş borç.

BU DOSYANIN ÖLÇTÜĞÜ KUSUR SINIFI: **"mekanizma çalışıyor ama operatör onun çalıştığını
göremiyor."** Dördü de tek tek ölçülmüş, dördü de aynı çatının altında.

  1. **409-YUTMASI.** `apiFetch` (app.js) 2xx dışını `Response` olarak GERİ DÖNDÜRÜYORDU ve
     çağıranların çoğu `r.ok`a bakmıyordu. L1'de uygulama kapısı (`api._onay_kapisi`) bir
     uygulamayı reddederken 409 + gövdede `[kimlik] <≥20 karakter gerekçe>` yazıyor
     (`api._ONAY_RET_NEDEN`); `applySkillRec`in boş `catch`i ile birleşince ölçülen davranış
     şuydu: operatör "Uygula"ya basar, sunucu gerekçesiyle REDDEDER, ekranda hiçbir şey olmaz.
     Kardeş `skillRev`in `alert`i de HİÇ tetiklenmiyordu (fırlatan yoktu).
  2. **EV_TR AİLE BOŞLUĞU.** `koruma_*` + onay-kapısı olayları — bir tanesi "pozisyon HÂLÂ
     çıplak", bir tanesi "operatör onayı reddetti" diyor — olay akışına HAM ADLA düşüyordu.
  3. **`k.olcum` ÇİZİLMİYORDU.** Beş Faz-6 kilidinin `olcum` sözlüğünün (n, ortalama bps, %95
     CI, eşleşmeyen oranı, DSR, pencere) hiçbir pano okuyucusu yoktu; pano yalnız `esik` +
     `neden` çiziyordu ve ikisi de bir `title=` ipucunun içindeydi.
  4. **HERMES TELEMETRİSİ ÇİZİLMİYORDU.** `agent_calls` özeti `/api/hermes` gövdesinde AKIYOR
     (hermes.py bunu kendi yorumunda "veri hazır, çizim henüz yok" diye beyan ediyordu) —
     yani defterin YASA-6 tüketicisi bir API ALANIydı, bir OKUYUCU değil.

TESTLER KAYNAĞA VE DAVRANIŞA BAKAR (repo deseni v139/v196/v198/v200): saf üreteçler Node'da
GERÇEKTEN koşturulur. Bir dürüstlük kuralı yalnız kaynakta "yazıyor" diye tutmuş sayılmaz —
ve bu turun kusuru tam olarak "yazıyordu ama çalışmıyordu" sınıfındaydı.

UYGULAMA YÜKLENMEZ: pano canlı Alpaca akışına bağlı bir süreçle aynı kabuğu paylaşıyor
(oturum sözleşmesi §5). Ölçüm bu yüzden statik dilim + Node harness'ıyla yapılır; `fetch`,
`document` ve `alert` saplanır.
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
APIPY = (SRC / "meridian" / "api.py").read_text()
WATCHPY = (SRC / "meridian" / "watchdog.py").read_text()
HEALTHPY = (SRC / "meridian" / "health.py").read_text()
FAZ5PY = (SRC / "meridian" / "faz5_cikis.py").read_text()
TELPY = (SRC / "meridian" / "agent_telemetry.py").read_text()

NODE = shutil.which("node")

# Yorumsuz gövde (repo deseni): bu turun her kararı gerekçesiyle kaynakta yazıyor ve o gerekçe
# bir BİLDİRİM sanılmamalı — yoksa silinmiş bir mekanizma kendi mezar taşı yüzünden yaşıyor
# görünür ve test hem düşer hem geçer.
KOD = "\n".join(l for l in APPJS.splitlines() if not l.lstrip().startswith("//"))


# ==============================================================================================
# 0 · DİLİM ÇIKARICI — saf üreteçleri Node'da koşturmak için (v200'ün `_fn`i + sınıf desteği)
# ==============================================================================================
def _fn(ad: str, kaynak: str = APPJS) -> str:
    """`async function` / `function` / `class` sütun-0 `}`ye kadar; atamalar DENGELİ okunur.

    `async function` ÖNCE denenir: `function apiFetch(` dizgesi `async function apiFetch(`in
    İÇİNDE de geçiyor ve önce o eşleşirse dilim `async` olmadan çıkar — Node'da "await is only
    valid in async functions" ile patlar ve hata ölçülen kod hakkında hiçbir şey söylemez
    (ölçülmüş vaka, bu dosyanın ilk koşumu)."""
    for bas in (f"async function {ad}(", f"function {ad}(", f"class {ad} "):
        if bas in kaynak:
            i = kaynak.index(bas)
            parcalar = []
            for ln in kaynak[i:].splitlines(keepends=True):
                parcalar.append(ln)
                if ln.rstrip("\n") == "}":
                    break
            return "".join(parcalar)
    # `window.X = async (…) => {…};` ve `const X = …;` aynı dengeli okumayı kullanır.
    for anahtar in (f"window.{ad} = ", f"const {ad} = "):
        if anahtar in kaynak:
            break
    else:
        raise AssertionError(f"{ad}: kaynakta tanım bulunamadı")
    i = kaynak.index(anahtar)
    parcalar, derinlik = [], 0
    for ln in kaynak[i:].splitlines(keepends=True):
        parcalar.append(ln)
        # Dizgiler ÖNCE düşer (içlerindeki `//` yorum değildir), sonra satır-sonu yorumu —
        # yoksa `const pctf = …;  // …` satırı ";" ile bitmiş sayılmaz ve dilim taşar (v200 dersi).
        govde = re.sub(r'"[^"]*"|\'[^\']*\'|`[^`]*`', "", ln)
        govde = re.sub(r"//.*$", "", govde)
        derinlik += sum(govde.count(c) for c in "([{") - sum(govde.count(c) for c in ")]}")
        if derinlik <= 0 and govde.rstrip().endswith(";"):
            break
    return "".join(parcalar)


def _yorumsuz(kod: str) -> str:
    """Satır-başı VE satır-sonu yorumlarını düşürür (dizgiler korunarak).

    NEDEN GEREKLİ: bu turun gerekçeleri KALDIRILAN çağrının adını yazıyor (`RENDER.hermes()`
    "sabit çağrı kaldırıldı" cümlesinin içinde geçiyor). Yalnız satır-başı yorumu atmak yetmez —
    silinmiş kod kendi mezar taşı yüzünden hâlâ yaşıyor görünür ve test yanlış düşer."""
    out = []
    for ln in kod.splitlines():
        if ln.lstrip().startswith("//"):
            continue
        # Dizgi içindeki `//` bir yorum DEĞİLDİR: dizgiler AYNI UZUNLUKTA maskelenir ki
        # bulunan indeks ham satırda da geçerli olsun.
        maske = re.sub(r'"[^"]*"|\'[^\']*\'|`[^`]*`', lambda mm: "'" * len(mm.group(0)), ln)
        i = maske.find("//")
        out.append(ln[:i] if i != -1 else ln)
    return "\n".join(out)


def _node(betik: str, ad: str):
    if NODE is None:
        pytest.skip("node yok")
    p = subprocess.run([NODE, "-e", betik], capture_output=True, text=True, timeout=120)
    assert p.returncode == 0, f"{ad} Node'da patladı:\n{p.stderr[-3000:]}"
    return json.loads(p.stdout)


# ==============================================================================================
# 1 · 409-YUTMASI — sunucunun gerekçesi YÜZEYE ÇIKIYOR (davranış, Node)
# ==============================================================================================
# `_onay_kapisi`nin 409 gövdesi bu dizgeyle BİREBİR aynı biçimdedir: `[kimlik] ` öneki + ≥20
# karakterlik gerekçe. Önek operatörün `POST /api/approvals/{id}`ye geçireceği dizgedir ve
# kırpılırsa cevap yarım kalır — o yüzden testin aradığı şey "mesajda geçiyor mu" değil,
# "OLDUĞU GİBİ geçiyor mu".
_409_GEREKCE = ("[rec:vcp_squeeze] onay defterinde bu öneriye ait KARAR YOK — L1+'ta uygulama, "
                "`POST /api/approvals/{id}` ile yazılmış bir `approve` satırı gerektirir (fail-closed)")

_APIFETCH_HARNESS = """
%(sinif)s
%(apifetch)s
%(esc)s
%(hatayaz)s
const API_BASE = "";
const API_TOKEN = "";
const _JC = new Map();
let YETKISIZ = 0;
function _yetkisizYakala(r) { if (r && r.status === 401) YETKISIZ++; return r; }

const VAKALAR = %(vakalar)s;
const out = {};
(async () => {
  for (const [ad, v] of Object.entries(VAKALAR)) {
    globalThis.fetch = async () => ({ ok: v.status < 400, status: v.status,
                                      text: async () => v.govde, json: async () => JSON.parse(v.govde) });
    _JC.set("kirli", 1);
    try {
      const r = await apiFetch("/api/dene", { method: "POST" });
      out[ad] = { firlatti: false, ok: r.ok, status: r.status, jc: _JC.size };
    } catch (e) {
      out[ad] = { firlatti: true, ad: e.name, status: e.status, detay: e.detay,
                  mesaj: e.message, jc: _JC.size };
    }
  }
  out["_yetkisiz_sayaci"] = YETKISIZ;

  // --- eylemHatasiYaz: kutulu ve kutusuz dal ---
  let ALERT = null;
  globalThis.alert = m => { ALERT = m; };
  const kutu = { innerHTML: "" };
  globalThis.$ = () => null;
  const hata = { message: "HTTP 409 — " + %(gerekce)s, status: 409, detay: %(gerekce)s };
  const kutuluDondu = eylemHatasiYaz(kutu, hata, "ONAY KAPISI REDDETTİ.");
  const kutusuzDondu = eylemHatasiYaz(null, hata, "kutusuz dal");
  out["_kutulu"] = { dondu: kutuluDondu, html: kutu.innerHTML };
  out["_kutusuz"] = { dondu: kutusuzDondu, alert: ALERT };
  // XSS: sunucu gövdesi olduğu gibi DOM'a girmez.
  const kutu2 = { innerHTML: "" };
  eylemHatasiYaz(kutu2, { message: "<img src=x onerror=alert(1)>" }, null);
  out["_kacis"] = kutu2.innerHTML;
  process.stdout.write(JSON.stringify(out));
})();
"""


@pytest.fixture(scope="module")
def apifetch_ciktilari():
    vakalar = {
        # (a) ONAY KAPISI REDDİ — bu turun merkezi vakası.
        "409": {"status": 409, "govde": json.dumps({"detail": _409_GEREKCE}, ensure_ascii=False)},
        # (b) JSON OLMAYAN GÖVDE (vekil hatası): `detail` yok ama ham metin tek ipucudur.
        "502_ham": {"status": 502, "govde": "<html><body>502 Bad Gateway</body></html>"},
        # (c) FastAPI 422 — `detail` bir LİSTEdir; dizgeye çevrilmezse "[object Object]" basılırdı.
        "422_liste": {"status": 422, "govde": json.dumps({"detail": [{"loc": ["body", "skill"],
                                                                      "msg": "field required"}]})},
        # (d) 401 — kapak açılır AMA çağrı yine de fırlar (sessiz başarı yok).
        "401": {"status": 401, "govde": json.dumps({"detail": "oturum doldu"})},
        # (e) 2xx — fırlatma YOK, yanıt olduğu gibi döner.
        "200": {"status": 200, "govde": json.dumps({"ok": True})},
    }
    betik = _APIFETCH_HARNESS % {
        "sinif": _fn("ApiHata"), "apifetch": _fn("apiFetch"), "esc": _fn("esc"),
        "hatayaz": _fn("eylemHatasiYaz"),
        "vakalar": json.dumps(vakalar, ensure_ascii=False),
        "gerekce": json.dumps(_409_GEREKCE, ensure_ascii=False),
    }
    return _node(betik, "apiFetch harness")


def test_409_gerekcesi_OLDUGU_GIBI_yuzeye_cikiyor(apifetch_ciktilari):
    """ÇEKİRDEK ÇİVİ. 409 bir `Response` olarak sessizce geri dönemez: `ApiHata` fırlar, gövdedeki
    `detail` hem `detay` alanında hem MESAJIN İÇİNDE durur ve `[kimlik]` öneki KIRPILMAZ."""
    r = apifetch_ciktilari["409"]
    assert r["firlatti"] is True, "4xx hâlâ yutuluyor — çağıran hiçbir şey olmamış gibi devam eder"
    assert r["ad"] == "ApiHata" and r["status"] == 409
    assert r["detay"] == _409_GEREKCE, "sunucunun gerekçesi kırpılmış ya da değişmiş"
    assert _409_GEREKCE in r["mesaj"], "gerekçe MESAJA girmiyor — `alert`/mesaj kutusu onu göremez"
    assert r["mesaj"].startswith("HTTP 409 — "), "durum kodu mesajın önünde yazılı değil"
    assert "rec:vcp_squeeze" in r["mesaj"], "kimlik öneki düşmüş — operatör NEYİ onaylayacağını bilemez"


def test_JSON_olmayan_govde_de_gerekce_tasir(apifetch_ciktilari):
    """Bir vekil 502'si `detail` taşımaz; ham gövde operatörün elindeki TEK ipucudur ve
    "sunucu sebep bildirmedi" demek onu silmek olurdu."""
    r = apifetch_ciktilari["502_ham"]
    assert r["firlatti"] and r["status"] == 502
    assert "502 Bad Gateway" in r["detay"], "ham gövde gerekçeye taşınmıyor"


def test_422_detay_LISTESI_dizgeye_cevriliyor(apifetch_ciktilari):
    """FastAPI doğrulama hatasında `detail` bir listedir. Çevrilmezse ekrana `[object Object]`
    düşerdi — bir hata mesajının en işe yaramaz hâli."""
    r = apifetch_ciktilari["422_liste"]
    assert "[object Object]" not in r["mesaj"], "detay nesnesi dizgeye çevrilmiyor"
    assert "field required" in r["detay"]


def test_401_kapagi_acar_AMA_yine_de_firlatir(apifetch_ciktilari):
    """`_yetkisizYakala` fırlatmadan ÖNCE koşar (oturum kapağı her koşulda açılmalı), ama 401 de
    bir hatadır: çağıran "oldu" sanmamalı."""
    assert apifetch_ciktilari["_yetkisiz_sayaci"] == 1, "401 kapağı atlanıyor"
    assert apifetch_ciktilari["401"]["firlatti"] is True, "401 sessizce yutuluyor"


def test_2xx_yolu_DEGISMEDI_ve_mutasyon_onbellegi_dusuyor(apifetch_ciktilari):
    """Regresyon çivisi: fırlatma eklemek okuma yolunu bozmamalı ve GET dışı istek yanıt
    önbelleğini düşürmeye devam etmeli (yoksa eylem sonrası eski durum geri okunur)."""
    r = apifetch_ciktilari["200"]
    assert r["firlatti"] is False and r["ok"] is True
    assert r["jc"] == 0, "POST yanıt önbelleğini düşürmüyor — eylem sonrası bayat durum okunur"


def test_eylem_hatasi_KUTUYA_yazilir_kutusuzsa_ALERT_duser(apifetch_ciktilari):
    """SESSİZ DAL YOK (YASA 4). İki dal da ölçülür; ikisinde de gerekçenin TAMAMI görünür."""
    k = apifetch_ciktilari["_kutulu"]
    assert k["dondu"] is True and _409_GEREKCE in k["html"].replace("&#39;", "'").replace("&quot;", '"')
    assert "ONAY KAPISI REDDETTİ." in k["html"], "ek açıklama kutuya girmiyor"
    ks = apifetch_ciktilari["_kutusuz"]
    assert ks["dondu"] is False and ks["alert"] and _409_GEREKCE in ks["alert"], \
        "kutusuz yüzey SESSİZ kalıyor — reddin hiçbir izi yok"


def test_hata_metni_DOM_a_kacisla_girer(apifetch_ciktilari):
    """Gerekçe sunucudan gelen METİNdir; olduğu gibi `innerHTML`e girerse pano bir enjeksiyon
    yüzeyine döner. Kaçış `esc` üstünden — ikinci bir kaçış dili açılmaz."""
    html = apifetch_ciktilari["_kacis"]
    assert "<img" not in html and "&lt;img" in html


# ---- KAYNAK TARAFI: yazma yollarında BOŞ `catch` KALMADI ------------------------------------
_YAZMA_YOLLARI = ["applySkillRec", "skillRev", "sprintStart", "sprintStop", "hermesCtl",
                  "korumaKur", "planOnayla", "intradayArm", "ackAlerts"]


def test_bos_catch_KALMADI():
    """YASA 4 pano yüzeyi: `catch (e) {}` bir kusur değil bir SESSİZLİKtir ve sessizlik bu turda
    ölçülen kusurun taşıyıcısıydı. Boş gövdeli hiçbir `catch` kalmamalı; yutan her dal işaretli
    ve ≥20 karakter gerekçeli olmalı."""
    bos = re.findall(r"catch\s*(?:\([^)]*\))?\s*\{\s*\}", APPJS)
    assert not bos, f"boş catch kalmış: {bos}"


@pytest.mark.parametrize("ad", _YAZMA_YOLLARI)
def test_yazma_yolu_HATAYI_YUZEYE_TASIYOR(ad):
    """Her yazma yolu ya kendi mesaj kutusuna yazar, ya `eylemHatasiYaz`a devreder, ya da
    `alert` eder — ama hiçbiri hatayı yere düşürmez."""
    g = _fn(ad)
    assert "catch" in g, f"{ad}: hata yolu hiç ele alınmıyor"
    yuzey = ("eylemHatasiYaz(" in g or "innerHTML" in g or "alert(" in g
             or "korumaMsgYaz(" in g or "alpMsgYaz(" in g)
    assert yuzey, f"{ad}: hata bir yüzeye yazılmıyor"


def test_basarisiz_onay_YENIDEN_CIZIM_yapmiyor():
    """Ölçülen ikinci kusur: eski `skillRev` hata OLSA BİLE `RENDER.skiller()` çağırıyordu —
    yeniden çizim mesaj kutusunu siler ve ret yine görünmez olurdu. Tazeleme yalnız BAŞARIDA."""
    for ad in ("skillRev", "applySkillRec"):
        g = _yorumsuz(_fn(ad))
        i = g.index("catch")
        assert "return;" in g[i:], f"{ad}: hata dalı erken dönmüyor — tazeleme mesajı silecek"
        assert "RENDER.skiller()" not in g and "RENDER.hermes()" not in g, \
            f"{ad}: sabit bir RENDER çağrısı var — düğme İKİ yüzeyde ve biri her zaman görünmez"
        assert "_aktifSayfayiCiz()" in g, f"{ad}: tazeleme aktif sayfaya bağlı değil"


def test_hamYanit_MUAFIYETI_tek_yerde_ve_BEYANLI():
    """Fırlatmanın TEK istisnası. `alpacaSubmit` durum kodunu kendi satırında okur (v195-a
    hükmü: sonuç kalıcı `_ALP_MSG` durumuna yazılır ve iki yeniden çizimden sağ çıkar). Muafiyet
    bir gevşeklik değil bir BEYANdır — sayılabilir olmalı, yoksa sessizce yayılır ve fırlatma
    sözleşmesi kâğıt üstünde kalır."""
    assert KOD.count("opts.hamYanit") == 1, "muafiyet kapısı ikinci bir yerde de okunuyor"
    kullanan = re.findall(r"hamYanit: true", KOD)
    assert len(kullanan) == 1, f"`hamYanit` {len(kullanan)} yerde kullanılıyor — muafiyet yayılmış"
    sub = _fn("alpacaSubmit")
    assert "hamYanit: true" in sub, "muafiyeti kullanan yüzey `alpacaSubmit` değil"
    assert "r.ok ?" in sub and "HTTP ${r.status}" in sub, "muaf yüzey durumu KENDİ okumuyor"


def test_ret_mesaji_kutusu_AKTIF_SAYFADAN_secilir():
    """Gizli sayfa DOM'dan silinmez ve aynı beceri iki yüzeyde listelenebilir. Sabit `id` ile
    arama, mesajı OPERATÖRÜN BAKMADIĞI sayfaya yazardı — yutmanın en ikna edici taklidi."""
    g = _fn("eylemKutusu")
    assert '.page.active' in g, "kutu aktif sayfadan seçilmiyor"
    assert "data-eylem-msg" in g
    # Üç yüzeyin üçünde de çıpa var: revizyon taslakları · onay kutusu · Eksen-2 öneri kartı.
    assert KOD.count('data-eylem-msg="${esc(') == 3, \
        "eylem mesaj çıpası üç yüzeyin hepsinde değil (revizyon · onay kuyruğu · öneri kartı)"


# ==============================================================================================
# 2 · EV_TR — KORUMA + ONAY KAPISI AİLESİ (davranış, Node)
# ==============================================================================================
# ADLAR UÇTAN ÖLÇÜLDÜ: aşağıdaki liste `api.py`/`watchdog.py` içindeki `obs.log`/`obs.warn`
# çağrılarının BİREBİR adlarıdır. Test bunu ayrıca doğrular (aşağıda) — uydurulmuş bir olay adı
# ekranda ASLA görünmez ve sessizce ölü bir çeviri olarak kalırdı.
_YENI_OLAYLAR = ["approval_gate_passed", "approval_missing_refused", "approval_decision",
                 "koruma_kur_istegi", "koruma_oco_gonderildi", "koruma_oco_dusuru",
                 "koruma_kur_ozet", "koruma_onay_bayat", "koruma_dedektoru_dustu"]

# Olay gövdeleri de uçtan alındı (kwargs adları birebir).
_OLAY_VAKALARI = {
    "approval_gate_passed": {"kimlik": "rec:vcp", "yol": "skills.apply_skill_action", "seviye": 1,
                             "atfedilemeyen": 0},
    "approval_missing_refused": {"kimlik": "rev:atr", "yol": "skill_evolve.apply_revision",
                                 "seviye": 1, "karar": "yok", "bozuk": 0, "atfedilemeyen": 0,
                                 "neden": "[rev:atr] onay defterinde bu öneriye ait KARAR YOK"},
    "approval_decision": {"approval_id": "rec:vcp", "decision": "approve", "has_reason": True},
    "koruma_kur_istegi": {"oneri_id": "abc123", "onay_verildi": True, "onaylayan": "operator",
                          "sonuc": "gonderildi", "gonderilen": 2, "toplam": 4, "ozet": "2/4"},
    "koruma_oco_gonderildi": {"plan_id": "kor-NVDA", "ticker": "NVDA", "adet": 22, "stop": 101.5,
                              "hedef": 132.0, "tif": "gtc", "onaylayan": "operator",
                              "oneri_id": "abc123", "adet_kaynagi": "broker"},
    "koruma_oco_dusuru": {"plan_id": "kor-AMD", "ticker": "AMD", "adet": 37, "stop": 90.0,
                          "hedef": 110.0, "onaylayan": "operator", "reachable": True,
                          "hata": "422 insufficient qty"},
    "koruma_kur_ozet": {"gonderilen": 2, "toplam": 4, "onaylayan": "operator", "oneri_id": "abc123"},
    "koruma_onay_bayat": {"verilen": "eski", "olculen": "abc123"},
    "koruma_dedektoru_dustu": {"error": "OSError: broker unreachable"},
}


@pytest.fixture(scope="module")
def ev_tr_ciktilari():
    betik = (_fn("EV_TR") + "\nconst V = " + json.dumps(_OLAY_VAKALARI, ensure_ascii=False) + ";\n"
             + "const out = { _adlar: Object.keys(EV_TR) };\n"
             + "for (const [ad, e] of Object.entries(V)) out[ad] = EV_TR[ad] ? EV_TR[ad](e) : null;\n"
             + "out._bilinmeyen = EV_TR['bu_olay_yok'] ? 'CEVIRI VAR' : null;\n"
             + "process.stdout.write(JSON.stringify(out));")
    return _node(betik, "EV_TR harness")


@pytest.mark.parametrize("ad", _YENI_OLAYLAR)
def test_yeni_olay_TURKCE_cumleye_baglandi(ad, ev_tr_ciktilari):
    """Her yeni olay bir CÜMLEdir, bir jeton değil: en az üç kelime ve ham olay adını İÇERMEZ
    (içerseydi çeviri değil süsleme olurdu)."""
    c = ev_tr_ciktilari[ad]
    assert c, f"{ad}: EV_TR'de çevirisi yok"
    assert ad not in c, f"{ad}: cümle hâlâ ham olay adını basıyor"
    assert len(c.split()) >= 3, f"{ad}: cümle değil, jeton: {c!r}"


def test_olay_cumleleri_OLCULEN_ALANLARI_tasiyor(ev_tr_ciktilari):
    """Cümle bir etiket değil bir RAPORdur: olayın karar taşıyan alanları metne girmeli."""
    c = ev_tr_ciktilari
    assert "rev:atr" in c["approval_missing_refused"] and "REDDETTİ" in c["approval_missing_refused"]
    assert "NVDA" in c["koruma_oco_gonderildi"] and "22" in c["koruma_oco_gonderildi"]
    assert "AMD" in c["koruma_oco_dusuru"] and "çıplak" in c["koruma_oco_dusuru"]
    assert "2/4" in c["koruma_kur_ozet"]
    assert "abc123" in c["koruma_onay_bayat"]
    assert "OSError" in c["koruma_dedektoru_dustu"]


def test_cevirisiz_olay_HAM_ADLA_dusmeye_devam_eder(ev_tr_ciktilari):
    """Mevcut davranış KORUNUR: bilinmeyen olay gizlenmez, mono ham adıyla akar."""
    assert ev_tr_ciktilari["_bilinmeyen"] is None
    akis = _fn("eventsFeed")
    assert 'class="chain">${esc(name)}' in akis, "çevirisiz olay ham adla çizilmiyor"


def test_EV_TR_UYDURMA_olay_adi_cevirmiyor():
    """En sinsi hâl: var olmayan bir olayın çevirisi. Ölü çeviri hiçbir zaman ekrana düşmez ve
    'bu olay panoda görünür' iddiası sessizce yanlış olur. Adlar ÜRETİCİDEN doğrulanır."""
    py = APIPY + "\n" + WATCHPY
    uretilen = set(re.findall(r"obs\.(?:log|warn)\(\s*[\"']([a-z_0-9]+)[\"']", py))
    for ad in _YENI_OLAYLAR:
        assert ad in uretilen, f"EV_TR '{ad}' çeviriyor ama üreten `obs.log/warn` çağrısı YOK"


def test_koruma_ve_onay_ailesi_EV_TR_de_TAM():
    """Aile bütün: bu turda ölçülen dokuz adın dokuzu da sözlükte."""
    ev = _fn("EV_TR")
    for ad in _YENI_OLAYLAR:
        assert f"\n  {ad}:" in ev, f"{ad} EV_TR sözlüğünde yok"


# ==============================================================================================
# 3 · `k.olcum` ÇİZİMİ — beş kilidin ölçümü (davranış, Node)
# ==============================================================================================
_F6_ORTAM = ["esc", "trn", "KANIT_TAVAN_N", "kanitOrani", "hucreCubuk", "hucreGovde",
             "ozetHucre", "ozetSerit", "_F6_BOS", "kilitOlcumHucreleri"]

_CIKIS_OLCUMU = {
    "kart": "EXE-2026-002", "n_defter": 31, "n_evren": 26, "n_min": 20,
    "kaynaklar": {"golge": "state/intraday_shadow_orders.jsonl", "eod": "state/trades.jsonl"},
    "maliyet_bandi": {"ek_bps_giris": 4.0, "taban": "e3", "model": "pessimistic_band_v2 (E3)"},
    "birim": "BİRİNCİL bps · İKİNCİL R",
    "eslesmeyen": {"n": 2, "oran": 0.0769, "kill_esigi": 0.2, "adlar": ["P-A", "P-B"],
                   "adlar_kirpildi": 0, "nedenler": [], "sinif_dagilimi": {"eod_yok": 2}},
    "n_eslesen": 24, "ortalama_bps": 12.5,
    "ci": {"ort": 12.5, "alt": -3.1, "ust": 28.4, "n": 24, "n_kume": 6, "B": 10000,
           "seviye": 0.95, "sifiri_disliyor": False, "yontem": "tarih-kümeli blok bootstrap",
           "kume_boylari": [4, 4, 4, 4, 4, 4], "neden": None},
    "ortalama_R": 0.02, "n_R_olculemeyen": 0, "R_olculemeyen_adlar": [],
}

_KILIT_VAKALARI = {
    # (a) EDGE / SONUÇ — `olcum` bir DİZGE ("geçen/toplam ölçüt").
    "edge_kaniti": {"gecer": False, "durum": "olculdu", "olcum": "3/5",
                    "esik": "EDGE hükmü: beş ölçütün BEŞİ de eşik+anlamlılık",
                    "neden": "edge kanıtlanmadı"},
    "sonuc_hukmu": {"gecer": True, "durum": "olculdu", "olcum": "4/4",
                    "esik": "SONUÇ hükmü: dört DOLAR ölçütünün DÖRDÜ", "neden": None},
    # (b) FAZ-5 — bu turun en kalabalık ölçümü.
    "faz5_cikisi": {"gecer": False, "durum": "olculdu",
                    "olcum": {"intraday_decisions_n": 88, "intraday_shadow_orders_n": 31,
                              "cikis_olcumu": _CIKIS_OLCUMU},
                    "esik": "Faz-5 çıkışı: 4a saha verisi + CI alt sınırı > band",
                    "neden": "ÖRNEKLEM YETERSİZ (24/20 değil) — örnek gerekçe"},
    # (c) OPERATÖR — bir bayrak; ölçülebilir büyüklüğü YOK ve bu beyan edilir.
    "operator_onayi": {"gecer": False, "durum": "olculdu", "olcum": {"intraday_arm": False},
                       "esik": "operatör onayı: state/INTRADAY_ARM elle açık",
                       "neden": "state/INTRADAY_ARM YOK — silahsız"},
    # (d) DSR ÖLÇÜLEMEDİ — "0" DEĞİL.
    "dsr_gecer": {"gecer": False, "durum": "olculemedi",
                  "olcum": {"dsr": None, "pencere_id": "R1-2026-04-30", "n_trials": 41},
                  "esik": "yürürlükteki pencerede DSR > 0.95", "neden": "DSR ölçülemedi"},
    # (e) FAZ-5 ÇAĞRIDA DÜŞTÜ — `cikis_olcumu` null (health'in fail-closed sarmalayıcısı).
    "faz5_dustu": {"gecer": False, "durum": "olculemedi",
                   "olcum": {"intraday_decisions_n": 0, "intraday_shadow_orders_n": 0,
                             "cikis_olcumu": None},
                   "esik": "Faz-5 çıkış ölçümü", "neden": "ÇAĞRIDA DÜŞTÜ: ValueError"},
    # (f) ÖLÇÜM SÖZLÜĞÜ HİÇ GELMEDİ — alanın yokluğu sıfır DEĞİLDİR.
    "olcum_yok": {"gecer": False, "durum": "olculemedi", "olcum": None,
                  "esik": "eşik", "neden": "uç okunamadı"},
}


@pytest.fixture(scope="module")
def kilit_ciktilari():
    ortam = "\n".join(_fn(a) for a in _F6_ORTAM)
    betik = (ortam + "\nconst V = " + json.dumps(_KILIT_VAKALARI, ensure_ascii=False) + ";\n"
             + """
const out = {};
for (const [ad, k] of Object.entries(V)) {
  const h = kilitOlcumHucreleri(ad, k);
  out[ad] = {
    hucreler: h,
    html: ozetSerit([ozetHucre("Ölçülen", h.olculen), ozetHucre("Örneklem", h.orneklem),
                     ozetHucre("Aralık", h.aralik), ozetHucre("Defter", h.defter)],
                    "Faz-6 kilit ölçümü"),
  };
}
process.stdout.write(JSON.stringify(out));
""")
    return _node(betik, "kilit ölçüm harness")


@pytest.mark.parametrize("ad", sorted(_KILIT_VAKALARI))
def test_kilit_seridi_DORT_hucre_ciziyor(ad, kilit_ciktilari):
    """Dört hücre kilide göre değil SORUYA göre sabittir — bir kilidin o sorusu yoksa hücre
    doğar ve "veri yok" der. Hücrenin HİÇ doğmaması, sorunun sorulmadığını gizlerdi."""
    html = kilit_ciktilari[ad]["html"]
    assert html.count('class="pm-cell"') == 4, f"{ad}: dört hücre çizilmiyor"
    for etiket in ("Ölçülen", "Örneklem", "Aralık", "Defter"):
        assert f">{etiket}<" in html, f"{ad}: `{etiket}` hücresi yok"


@pytest.mark.parametrize("ad", sorted(_KILIT_VAKALARI))
def test_cizilen_her_CUBUK_paydasini_BEYAN_ediyor(ad, kilit_ciktilari):
    """v192 kuralı: paydası yazılmayan bir çubuk, okurun kendi uydurduğu bir tavana göre
    okunur. `hucreCubuk` paydasız çizmez — burada çıktıda DOĞRULANIR."""
    html = kilit_ciktilari[ad]["html"]
    for cubuk in re.findall(r'<span class="pm-conf"[^>]*>', html):
        m = re.search(r'data-payda="([^"]*)"', cubuk)
        assert m and m.group(1).strip(), f"{ad}: paydasız çubuk çizilmiş: {cubuk}"


@pytest.mark.parametrize("ad", sorted(_KILIT_VAKALARI))
def test_OLCULEMEDI_sifir_YAZMIYOR_ve_gerekce_taşıyor(ad, kilit_ciktilari):
    """ÖLÇÜLEMEDİ ≠ 0 — bu yüzeyin tek kuralı. Değeri olmayan her hücre `.pm-none` "veri yok"
    dalına düşer VE en az 20 karakterlik bir gerekçe taşır (YASA 4 ölçüsü)."""
    h = kilit_ciktilari[ad]["hucreler"]
    for isim, o in h.items():
        if o.get("deger") in (None, ""):
            meta = re.sub(r"<[^>]*>", " ", str(o.get("meta") or "")).strip()
            assert len(meta) >= 20, f"{ad}.{isim}: değersiz hücrede gerekçe yok/kısa: {meta!r}"
            assert meta not in ("0", "0,00"), f"{ad}.{isim}: ölçülemeyen hücreye sıfır yazılmış"
    assert '<span class="pm-none">veri yok</span>' in kilit_ciktilari[ad]["html"] or \
        all(o.get("deger") not in (None, "") for o in h.values())


# ---- ALTINCI ŞERİDİN PAYDA DENETİMİ ----------------------------------------------------------
# `test_pano_durum_kartlari_v191.test_dort_bolumun_ozet_seridi_var_ve_TIKLANMAZ`in kendi hükmü:
# "_SERIT_BOLGELERI'ne bir satır eklemek bir kauçuk damga DEĞİLDİR — o yüzeyin de PAYDALARININ
# denetlenmesi gerekir". Beşinci şeridin bedeli `_EKSEN2_PAYDALARI`ydı; altıncınınki budur.
#
# ÖLÇÜLEN AYRIM: dört hücrenin İKİSİNİN paydası VARDIR ve ikisinin YOKTUR — ve yokluk bir unutma
# değil bir HÜKÜMdür:
#   Ölçülen  → payda VAR ama YALNIZ ölçüt-sayan kilitlerde (EDGE/SONUÇ: "kaçı geçti/kaç ölçüt").
#              Faz-5'in ortalaması bir bps değeridir; bir ORANIN payı değildir, tavanı YOKTUR.
#   Örneklem → payda VAR ama YALNIZ n_min'i olan kilitte (Faz-5). DSR'nin `n_trials`ının tavanı
#              yoktur ("kaç deneme TAM sayılır?" tanımsız) — uydurulmuş bir tavana göre doluluk
#              çizmek, ölçülmemiş bir yeterliliği ölçülmüş gibi göstermek olurdu.
#   Aralık   → payda YOK, oran da YOK. Bir güven aralığının "doluluğu" tanımsızdır.
#   Defter   → payda YOK, oran da YOK. Bir defterin satır sayısının tavanı yoktur.
_KILIT_PAYDALI = {("edge_kaniti", "olculen"): "5 ölçüt (HEPSİ geçmeli)",
                  ("sonuc_hukmu", "olculen"): "4 ölçüt (HEPSİ geçmeli)",
                  ("faz5_cikisi", "orneklem"): "asgari eşleşmiş çift (n_min=20)"}
_KILIT_PAYDASIZ_HUCRE = ("aralik", "defter")


def test_altinci_seridin_DORT_PAYDASI_denetlendi(kilit_ciktilari):
    """Paydası olan hücre ADIYLA yazılı; olmayan hücre `oran` DA vermez (paydasızlık bir hüküm).
    Bu, v191'in beşinci şerit için kurduğu denetimin altıncısıdır."""
    for ad, v in kilit_ciktilari.items():
        for isim, o in v["hucreler"].items():
            beklenen = _KILIT_PAYDALI.get((ad, isim))
            if beklenen is not None:
                assert o.get("payda") == beklenen, f"{ad}.{isim}: payda değişmiş — denetim bayatladı"
                assert o.get("oran") is not None, f"{ad}.{isim}: paydası var ama oranı yok"
            else:
                assert not o.get("oran"), \
                    f"{ad}.{isim}: tavanı OLMAYAN bir hücreye oran girmiş — uydurma doluluk"
    # İki hücre HİÇBİR kilitte çubuk taşımaz: hükmün kendisi budur.
    for ad, v in kilit_ciktilari.items():
        for isim in _KILIT_PAYDASIZ_HUCRE:
            o = v["hucreler"][isim]
            assert not o.get("oran") and not o.get("payda"), \
                f"{ad}.{isim}: paydasız olması gereken hücreye çubuk girmiş"


def test_olcum_sozlugu_HIC_GELMEZSE_dort_hucre_de_durust(kilit_ciktilari):
    """En sert dal: uç `olcum` alanını hiç göndermedi. Dört hücrenin dördü de "veri yok" +
    gerekçe basar; bir tanesi bile sayı UYDURMAZ."""
    v = kilit_ciktilari["olcum_yok"]
    assert v["html"].count('<span class="pm-none">veri yok</span>') == 4
    assert "ÖLÇÜLEMEDİ" in v["html"], "ölçülemeyen kilit rozetsiz kalıyor"
    assert 'class="pm-conf"' not in v["html"], "veri yokken çubuk çizilmiş — uydurma doluluk"


def test_faz5_kilidinin_SAYILARI_gercekten_ciziliyor(kilit_ciktilari):
    """Bu turun asıl kazancı: n/n_min, ortalama bps, %95 CI ve eşleşmeyen oranı artık bir
    cümlenin içinden değil ÖLÇÜMÜN kendisinden okunuyor."""
    html = kilit_ciktilari["faz5_cikisi"]["html"]
    assert "12,5 bps" in html, "ortalama bps çizilmiyor"
    assert "24/20" in html, "örneklem n/n_min çizilmiyor"
    assert "-3,1" in html and "28,4" in html, "%95 CI aralığı çizilmiyor"
    assert "10.000" in html or "10000" in html, "bootstrap B'si çizilmiyor"
    assert "kill eşiği" in html, "eşleşmeyen oranının kill eşiği yazılmıyor"
    # Örneklem çubuğu n_min paydasına bağlı — uydurma bir tavana değil.
    assert 'data-payda="asgari eşleşmiş çift (n_min=20)"' in html


def test_ci_KURULAMADIGINDA_neden_yaziliyor(kilit_ciktilari):
    """Aralıksız bir ortalama hüküm veremez; "—" yerine sunucunun NEDENİ okunur."""
    html = kilit_ciktilari["faz5_dustu"]["html"]
    assert "aralık KURULAMADI" in html or "veri yok" in html


def test_renk_YALNIZ_olculemeyen_kilitte(kilit_ciktilari):
    """D1: renk yalnız anomalide. KAPALI bir kilit anomali DEĞİLDİR (zincir fail-closed ve
    kapalılık tasarımın kendisi) — anomali ÖLÇÜLEMEYEN kilittir."""
    kapali_olculdu = kilit_ciktilari["edge_kaniti"]["hucreler"]["olculen"]
    assert not kapali_olculdu.get("degerSinif"), "ölçülmüş ama kapalı kilit renk taşıyor"
    olculemedi = kilit_ciktilari["dsr_gecer"]["hucreler"]["olculen"]
    assert olculemedi.get("degerSinif") == "warn" and olculemedi.get("rozet") == "ÖLÇÜLEMEDİ"


def test_kilit_serit_bloklari_faz6Satiri_icinde_ciziliyor():
    """Üretici bir yerden ÇAĞRILMAZSA ölçüm yine görünmez — bu turun kusurunun aynısı."""
    g = _fn("faz6Satiri")
    assert "kilitOlcumHucreleri(ad, k)" in g, "üretici kilit zincirinde çağrılmıyor"
    assert "detayKatmani(" in g, "ölçüm bloğu bir katmana yerleşmemiş"
    assert "f.adlar.map" in g, "beş kilidin hepsi çizilmiyor"


def test_okunan_alanlar_URETICIDE_GERCEKTEN_var():
    """PANO ŞEKLİ UYDURMUYOR. Okuduğu her alan üreticinin kaynağında yazılı olmalı; olmayan bir
    alanı okumak, canlıda sessizce boş çizmek demektir (fikstürle yeşil, canlıda kör)."""
    for alan in ("n_eslesen", "n_min", "ortalama_bps", "eslesmeyen", "kill_esigi",
                 "maliyet_bandi", "ek_bps_giris", "n_evren", "yontem", "n_kume"):
        assert f'"{alan}"' in FAZ5PY, f"faz5_cikis.py `{alan}` üretmiyor — pano hayalet alan okuyor"
    for alan in ("cikis_olcumu", "intraday_decisions_n", "intraday_shadow_orders_n",
                 "intraday_arm", "dsr", "pencere_id", "n_trials"):
        assert f'"{alan}"' in HEALTHPY, f"health.py `{alan}` üretmiyor — pano hayalet alan okuyor"


# ==============================================================================================
# 4 · HERMES ÇAĞRI TELEMETRİSİ KARTI — D2-a sözleşmesi (davranış, Node)
# ==============================================================================================
_TEL_ORTAM = ["esc", "trn", "pctf", "KANIT_TAVAN_N", "kanitOrani", "hucreCubuk", "hucreGovde",
              "kartOzeti", "detayKatmani", "KART_KAYDI", "katKart", "firsatBos",
              "hermesTelemetriKarti"]

_TEL_DOLU = {"agent_calls": {
    "n": 12, "pencere_s": 86400.0, "pencere_disi": 37,
    "sure_ms": {"p50": 4210.0, "p95": 38110.5, "max": 41002.2, "toplam": 121540.8},
    "sinif": {"dolu": 9, "bos": 2, "zaman_asimi": 1},
    "model": {"gemini-2.5-pro": 8, "claude-opus": 4},
    "tasiyici": {"yerel_ajan": 10, "http": 2},
    "arac": {"olculen": 7, "olculemeyen": 5, "toplam_arac": 21, "ort": 3.0},
    "en_yavas": {"iz_id": "iz-9", "kind": "reflect", "model": "gemini-2.5-pro",
                 "sure_ms": 41002.2, "sonuc_sinifi": "zaman_asimi"},
    "iz": {"bayt": 1_240_000, "satir_tavani": 300, "akis_tavani_kr": 8000,
           "disk_tavani_mb": 4.98, "doluluk": 0.249, "satir_n": None,
           "beyan": "satır sayısı ÖLÇÜLMEDİ (yalnız bayt damgası okunur)"},
    "beyan": "süre ÖLÇÜM ANINDA yazılır; `arac_cagri_n=None` ÖLÇÜLEMEDİ demektir (0 DEĞİL)"}}

# PENCEREDE HİÇ ÇAĞRI YOK ama defter DOLU — "hiç çağrı olmadı" ile "hepsi eski" AYNI DEĞİL.
_TEL_BOS_PENCERE = {"agent_calls": {
    "n": 0, "pencere_s": 86400.0, "pencere_disi": 412,
    "sure_ms": {"p50": None, "p95": None, "max": None, "toplam": None},
    "sinif": {}, "model": {}, "tasiyici": {},
    "arac": {"olculen": 0, "olculemeyen": 0, "toplam_arac": 0, "ort": None},
    "en_yavas": None, "iz": {}, "beyan": "beyan"}}


@pytest.fixture(scope="module")
def telemetri_ciktilari():
    ortam = "\n".join(_fn(a) for a in _TEL_ORTAM)
    betik = (ortam + "\nconst V = " + json.dumps(
        {"dolu": _TEL_DOLU, "bos_pencere": _TEL_BOS_PENCERE, "olculemedi": {}, "yok": None},
        ensure_ascii=False) + ";\n"
        + "const out = {};\nfor (const [ad, it] of Object.entries(V)) out[ad] = hermesTelemetriKarti(it);\n"
        + "process.stdout.write(JSON.stringify(out));")
    return _node(betik, "hermes telemetri harness")


@pytest.mark.parametrize("dal", ["dolu", "bos_pencere", "olculemedi", "yok"])
def test_telemetri_karti_TEK_KART_CIPA_OZET(dal, telemetri_ciktilari):
    """D2-a sözleşmesi: tek `class="card"` emisyonu, `data-kart` çıpası ve `.kk-ozet` kapalı
    özeti — DÖRT dalın hepsinde. Özetsiz bir kart katlanamaz ve kapak sözleşmesinden düşer."""
    html = telemetri_ciktilari[dal]
    assert html.count('class="card') == 1, f"{dal}: kart sayısı 1 değil"
    assert 'data-kart="hermes:telemetri"' in html, f"{dal}: kart kaydı çıpası yok"
    assert '<span class="kk-ozet"' in html, f"{dal}: kapalı özet üretilmemiş (kart katlanamaz)"


@pytest.mark.parametrize("dal", ["olculemedi", "yok"])
def test_telemetri_veri_YOKKEN_OLCULEMEDI_ve_NEDEN(dal, telemetri_ciktilari):
    """Boş dal SIFIR yazmaz: "0 çağrı" ile "ölçüm gelmedi" aynı piksele düşerse pano bir bilgi
    değil bir izlenim taşır."""
    html = telemetri_ciktilari[dal]
    assert "ÖLÇÜLEMEDİ" in html
    assert 'class="pm-none">veri yok<' in html, "boş dalda değer hücresi 'veri yok' demiyor"
    duz = re.sub(r"<[^>]*>", " ", html)
    assert "DEĞİLDİR" in duz or "DEĞİL" in duz, "boşluğun 'sıfır değil' beyanı yok"
    assert 'class="pm-conf"' not in html, "veri yokken çubuk çizilmiş"


def test_telemetri_PENCERE_DISI_satirlar_beyan_ediliyor(telemetri_ciktilari):
    """`ozet()`in kendi beyanı: boş bir özet, "hiç çağrı olmadı" ile "hepsi pencerenin dışında"
    arasındaki farkı söyleyemezse YANLIŞ GÜVEN üretir."""
    html = telemetri_ciktilari["bos_pencere"]
    assert "412" in html, "pencere dışı satır sayısı yazılmıyor"
    duz = re.sub(r"<[^>]*>", " ", html)
    assert "AYNI ŞEY DEĞİLDİR" in duz or "pencerenin dışında" in duz


def test_telemetri_dolu_dalda_KARAR_SAYILARI_var(telemetri_ciktilari):
    """Kartın cevapladığı soru: "gece koşusu neden uzadı, hangi çağrı takıldı".
    Başlık sayısı SÜRE değil SINIF — boş dönen bir çağrı hızlıdır ve p95 onu göstermez."""
    html = telemetri_ciktilari["dolu"]
    assert "9/12" in html, "kullanılabilir cevap oranı başlıkta değil"
    assert 'data-payda="pencerede ölçülen ajan çağrısı (son 24 sa)"' in html, "payda beyanlı değil"
    assert "p95 38.111 ms" in html, "p95 süresi özet metasında yazılmıyor"
    assert "41.002 ms · reflect" in html, "en yavaş çağrının kimliği yazılmıyor"
    assert "zaman_asimi" in html, "sonuç sınıfı dağılımı çizilmiyor"
    assert "yerel_ajan" in html, "taşıyıcı kırılımı çizilmiyor"
    assert "BOŞ DÖNEN ÇAĞRI" in html, "dolu olmayan çağrılar rozetle işaretlenmiyor"


def test_telemetri_ARAC_olculemeyen_PAYDAYA_katilmiyor(telemetri_ciktilari):
    """`-Q` sessiz mod oturum özetini bastırır ve araç sayısı ÖLÇÜLEMEZ. Ölçülemeyeni paydaya
    katmak oranı sessizce seyreltirdi — sayı ayrı yazılır."""
    html = telemetri_ciktilari["dolu"]
    assert "ÖLÇÜLEMEDİ" in html and "-Q" in html
    duz = re.sub(r"<[^>]*>", " ", html)
    assert "5" in duz and "7" in duz, "ölçülen/ölçülemeyen ayrımı sayıyla yazılmıyor"


def test_telemetri_cizilen_her_CUBUK_paydasini_BEYAN_ediyor(telemetri_ciktilari):
    for dal, html in telemetri_ciktilari.items():
        for cubuk in re.findall(r'<span class="pm-conf"[^>]*>', html):
            m = re.search(r'data-payda="([^"]*)"', cubuk)
            assert m and m.group(1).strip(), f"{dal}: paydasız çubuk: {cubuk}"


def test_telemetri_karti_KAPAK_ALTINDA_ve_KAYITLI():
    """Öğrenme yüzeyinin kart bütçesi zaten aşılmış: yeni kart kapaksız eklenemez."""
    assert '"hermes:telemetri":   { alan: "ogrenme", bolum: "hermes" }' in APPJS, \
        "kart kaydı yok — `katKart` boş döner ve kart kapak ALMAZ"
    assert KOD.count('katKart("hermes:telemetri")') == 1


def test_telemetri_karti_RENDERdan_cagriliyor():
    """Ölçülen kusurun aynısına düşmemek için: üretilen kart bir sayfaya YERLEŞMİŞ olmalı —
    hermes.py'nin "veri hazır, çizim yok" beyanını kapatan şey çağrının kendisidir."""
    assert "${hermesTelemetriKarti(d.integrations)}" in KOD, "kart hiçbir sayfada çizilmiyor"
    # Çağrı `page-hermes` gövdesinin İÇİNDE (④ Öğrenme yüzeyi, `hermes` bölümü).
    i = KOD.index('$("page-hermes").innerHTML')
    assert "hermesTelemetriKarti" in KOD[i:i + 6000], "çağrı Öğrenme yüzeyinin dışında"


def test_telemetri_okudugu_alanlar_URETICIDE_var():
    """Şekil uydurulmuyor: okunan her alan `agent_telemetry.ozet()`/`iz_durum()` çıktısında var."""
    for alan in ("pencere_s", "pencere_disi", "sure_ms", "p50", "p95", "toplam", "sinif",
                 "model", "tasiyici", "arac", "olculen", "olculemeyen", "ort", "en_yavas",
                 "sonuc_sinifi", "iz", "beyan", "bayt", "disk_tavani_mb"):
        assert f'"{alan}"' in TELPY, f"agent_telemetry.py `{alan}` üretmiyor"


# ==============================================================================================
# 5 · SÖZDİZİMİ — bir sözdizimi hatası her testin yerine geçer (v196/v200 deseni)
# ==============================================================================================
def test_node_check_gecer():
    if NODE is None:
        pytest.skip("node yok")
    p = subprocess.run([NODE, "--check", str(WEB / "app.js")], capture_output=True, text=True)
    assert p.returncode == 0, f"node --check düştü:\n{p.stderr}"


def test_satir_ici_script_YOK():
    """CSP: satır-içi script bu depoda yasak (v198 `test_CSP_satir_ici_olay_ozniteligi_YOK`
    ile aynı çatı). Bu turun eklediği hiçbir yüzey `<script>` ya da `on*=` ÜRETMİYOR.
    Ölçüm yorumsuz gövdede yapılır: kuralın kendisi kaynakta düzyazıyla anlatılıyor ve o
    anlatı bir emisyon sanılmamalı."""
    assert "<script" not in KOD, "kaynak bir <script> emisyonu üretiyor"
    kalip = re.findall(r'\bon(?:click|error|load|change|submit)\s*=\s*["\']', KOD)
    assert not kalip, f"satır içi olay özniteliği: {kalip}"
