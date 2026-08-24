"""v195-a — UX SADELEŞTİRME DALGA-0: beş quick-win (kaynak: docs/UX-SADELESTIRME-DENETIMI-2026-08-06.md).

BU DOSYANIN ÖLÇTÜĞÜ KUSUR SINIFI TEK: **üretilen bir gerçeğin okuyucusuz kalması** — ve onun en
pahalı hâli, eylemin SONUCUNUN hiçbir yere yazılmaması. Beş bulgunun beşi de aynı ailenin üyesi:

  B1 (cid-4) `#alp-msg` DİYE BİR ÖĞE YOKTU. `alpacaSubmit` her geri bildirimi `$("alp-msg")`e
     yazıyordu; öğe ne app.js'te ne index.html'de üretiliyordu. "Silahlı planları Alpaca'ya gönder"
     düğmesi ne "gönderiliyor…", ne "N emir gönderildi", ne de hatayı yazıyordu. AMGN
     "onay→gönderim kopukluğu" vakasının MEKANİK açıklaması budur.
  B2 (cid-4) `_inbox_count` REVIEW planlarını SAYMIYORDU: üç plan onay beklerken açılış ekranı
     "0 bekleyen onay — senden bir şey beklenmiyor" yazıyordu. None ≠ 0'ın kardeşi: 0 ≠ "yok".
  B3 (cid-4) Ayarlar'daki `alpacaClose`, Kademe 3 · FLATTEN ile AYNI ucu TEK `confirm()` ile
     çağırıyordu; müdahale paneli ise ekranda "ikinci bir yetki yolu yoktur" diyordu.
  B6 (cid-3) `api._sessiz_hat` `askida`/`n_askida` üretiyor, `sessizHat()` okumuyordu (YASA 6):
     eksik bekçinin nedeni yalnız HUD çipinin `title` ipucundaydı — hover-only.
  B4 (cid-3) `onaylar` bölümünün soru cümlesi "şu an benim onayımı bekleyen ne var?" idi ama
     REVIEW onayı Koşu & Döngü → adaylar → satır çekmecesinin İÇİNDE yaşıyordu.

TESTLER HEM KAYNAĞA HEM DAVRANIŞA BAKAR (repo deseni: v139/v155/v190/v194). Şablon dilimleri
Node'da FİİLEN koşturulur: kaynakta doğru görünen bir şablonun çalışma zamanında patlaması bu
deponun ölçülmüş kusur sınıfıdır (2026-08-06 müdahale arızası), yalnız dizgi aramak yetmez.
"""
from __future__ import annotations

import json
import pathlib
import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from meridian import api, config, store

SRC = pathlib.Path(__file__).resolve().parents[1]
WEB = SRC / "meridian" / "web"
APPJS = (WEB / "app.js").read_text()
INDEX = (WEB / "index.html").read_text()
APIPY = (SRC / "meridian" / "api.py").read_text()
CSS = INDEX[INDEX.index("<style>"):INDEX.index("</style>")]
NODE = shutil.which("node")
HDR = {"x-meridian-token": "T0KEN"}

# Yorumsuz gövde (v154/v171/v194 deseni): bir kuralın GEREKÇESİNİ anlatan yorum, o kuralın ihlali
# sanılmamalı — bu turun her kaldırma kararı "eski hâl şuydu, neden yanlıştı" diye yazıldı.
KOD = "\n".join(l for l in APPJS.splitlines() if not l.lstrip().startswith("//"))


def _govde(bas: str, bit: str) -> str:
    i = APPJS.index(bas)
    return APPJS[i:APPJS.index(bit, i)]


def _apipy_govde(bas: str, bit: str) -> str:
    i = APIPY.index(bas)
    return APIPY[i:APIPY.index(bit, i)]


def _pykod(govde: str) -> str:
    """Python dilimini YORUMSUZ ve DOCSTRING'SİZ bırak — aynı gerekçe (v139/v154): bir kuralın
    NEDEN konduğunu anlatan metin, o kuralın ihlali sanılmamalı."""
    if govde.count('"""') >= 2:
        govde = govde.split('"""', 2)[2]
    return "\n".join(l for l in govde.splitlines() if not l.lstrip().startswith("#"))


def _blok(bas: str, bitti) -> str:
    """`bas` ile başlayan satırdan `bitti(satır)` doğru olana kadarki kaynak dilimi (v194 deseni)."""
    i = APPJS.index(bas)
    parcalar: list[str] = []
    for ln in APPJS[i:].splitlines(keepends=True):
        parcalar.append(ln)
        if bitti(ln) and len(parcalar) > 1:
            return "".join(parcalar)
    raise AssertionError(f"kapanış bulunamadı: {bas}")


ESC_TRN = """
const esc = s => (s == null ? "" : String(s)).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",
  ">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const trn = (x, d = 0) => { const n = Number(x);
  return (x == null || !Number.isFinite(n)) ? "—" : n.toFixed(d); };
"""


def _node(betik: str) -> dict:
    if NODE is None:
        pytest.skip("node yok")
    p = subprocess.run([NODE, "-e", betik], capture_output=True, text=True, timeout=60)
    assert p.returncode == 0, f"şablon dilimi Node'da patladı:\n{p.stderr}"
    return json.loads(p.stdout)


# =================================================================================================
# KALEM 1 — #alp-msg: gönderim düğmesi ARTIK KONUŞUYOR (B1 · ciddiyet 4)
# =================================================================================================
def test_alp_msg_kabi_GERCEKTEN_uretiliyor():
    """ASIL REGRESYON. Bu satır düşerse `alpacaSubmit` yine boşluğa yazar ve düğme yine dilsizdir."""
    assert KOD.count('id="alp-msg"') == 1, "alp-msg kabı yok ya da iki yerde üretiliyor"
    kart = _govde("function _alpacaKartHTML(a) {", "\nRENDER.ayarlar = async () => {")
    assert 'id="alp-msg"' in kart, "kap Alpaca kartının dışında doğmuş — düğmesinden uzakta"
    assert 'data-act="alpacaSubmit"' in kart and kart.index('data-act="alpacaSubmit"') < kart.index('id="alp-msg"'), \
        "mesaj kabı düğmeden ÖNCE geliyor — kardeş desen (#intraday-arm-msg) düğmenin ardındadır"


def test_mesaj_YENIDEN_CIZIMDE_hayatta_kalir():
    """KUSURUN İKİNCİ YARISI. Başarılı gönderim `RENDER.ayarlar()` çağırıyor ve `_alpacaSonra()`
    kartı 1,4 sn sonra İKİNCİ kez değiştiriyor: mesaj yalnız DOM'da yaşasaydı iki kez silinir,
    yani düzeltme sessizce geri alınırdı."""
    assert "let _ALP_MSG" in APPJS, "kalıcı mesaj durumu yok"
    kart = _govde("function _alpacaKartHTML(a) {", "\nRENDER.ayarlar = async () => {")
    assert "${_ALP_MSG}" in kart, "şablon son sonucu geri koymuyor — yeniden çizim mesajı yer"
    sub = _blok("window.alpacaSubmit = async () => {", lambda ln: ln.rstrip("\n") == "};")
    assert "alpMsgYaz(" in sub and '$("alp-msg")' not in sub, \
        "mesaj doğrudan DOM'a yazılıyor — kalıcı durumdan geçmeli"


def test_ucun_HTTP_durumu_okunuyor():
    """Eski hâl doğrudan `.json()`a geçiyordu: 401/500 bir gövde döndürdüğünde arayüz onu BAŞARI
    gibi okur ve "0 emir gönderildi" yazardı — sessizce yanlış yaptıran sınıf."""
    sub = _blok("window.alpacaSubmit = async () => {", lambda ln: ln.rstrip("\n") == "};")
    assert "r.ok ?" in sub and "HTTP ${r.status}" in sub
    assert ".then(x => x.json())" not in sub, "HTTP durumu yine atlanıyor"


_ALP_SONUC = _blok("function _alpSonucSatiri(r) {", lambda ln: ln.rstrip("\n") == "}")


@pytest.fixture(scope="module")
def alp_sonuc() -> dict:
    """Sonuç satırı Node'da FİİLEN koşturulur — beş broker hâli, beş ayrı cümle."""
    betik = ESC_TRN + _ALP_SONUC + """
const out = {
  // AMGN VAKASI: onay verildi, düğmeye basıldı, emir gitti — ekran bunu SÖYLEMEK zorunda.
  amgn: _alpSonucSatiri({ ok: true, submitted: 1, detail: "",
                          results: [{ ticker: "AMGN", ok: true, qty: 12 }] }),
  karisik: _alpSonucSatiri({ ok: true, submitted: 1, results: [
      { ticker: "AMGN", ok: true },
      { ticker: "NVDA", ok: false, dedup: true, detail: "zaten gönderildi (dedup)" },
      { ticker: "MSFT", ok: false, detail: "insufficient buying power" },
      { ticker: "TSLA", ok: false, veto: true, detail: "gap riski" },
      { ticker: "AAPL", ok: false, reachable: false, detail: "timeout" }] }),
  halt: _alpSonucSatiri({ ok: false, detail: "HALT aktif — emir gönderilmez" }),
  olculemedi: _alpSonucSatiri({ ok: true, results: [] }),
  bosKuyruk: _alpSonucSatiri({ ok: true, submitted: 0, results: [], detail: "silahlı plan yok" }),
};
process.stdout.write(JSON.stringify(out));
"""
    return _node(betik)


def test_gonderim_sonucu_EKRANA_yazilir_amgn_vakasi(alp_sonuc):
    """Denetimin kapatmayı vaat ettiği vaka: bir emir gitti ve operatör bunu ekrandan öğreniyor."""
    assert "1 emir gönderildi" in alp_sonuc["amgn"]


def test_kismi_basari_HER_HALI_ayri_soyler(alp_sonuc):
    """Beş hâl tek "N gönderildi" cümlesine sıkıştırılırsa operatör, planının neden aynada
    olmadığını ekrandan öğrenemez."""
    m = alp_sonuc["karisik"]
    assert "1 emir gönderildi" in m
    assert "1 dedup" in m
    assert "gap-vetosu" in m and "broker reddi değil" in m
    assert "1 ulaşılamadı" in m and "SİLAHLI kaldı" in m
    assert "1 ret:" in m and "MSFT" in m and "insufficient buying power" in m


def test_ret_gerekcesi_YUTULMAZ(alp_sonuc):
    """YASA 4: brokerin reddi bir cevaptır; "0 gönderildi" deyip gerekçeyi yutmak sessiz yutmadır."""
    assert "gerekçe bildirilmedi" not in alp_sonuc["karisik"], "gerçek gerekçe varken yer tutucu basılmış"


def test_halt_dali_BASARI_gibi_okunmaz(alp_sonuc):
    assert "HALT aktif" in alp_sonuc["halt"]
    assert "emir gönderildi" not in alp_sonuc["halt"]


def test_olculemeyen_sayi_SIFIR_yazmaz(alp_sonuc):
    """None ≠ 0. Uç `submitted` vermediyse "0 emir gönderildi" bir uydurmadır."""
    assert "ölçülemedi" in alp_sonuc["olculemedi"]
    assert "0 emir gönderildi" not in alp_sonuc["olculemedi"]
    # Ölçülmüş sıfır ise AYNEN yazılır — dürüst boşluk gizlenmez.
    assert "0 emir gönderildi" in alp_sonuc["bosKuyruk"] and "silahlı plan yok" in alp_sonuc["bosKuyruk"]


def test_yukleniyor_hali_ve_dugme_kilidi():
    """Mutlu-yol yasak: yükleme hâli düğmeyi kilitler ve metnini değiştirir (planOnayla deseni)."""
    sub = _blok("window.alpacaSubmit = async () => {", lambda ln: ln.rstrip("\n") == "};")
    assert 'alpMsgYaz("gönderiliyor…")' in sub
    assert "disabled = true" in sub and "disabled = false" in sub, "düğme kilidi ya da geri alma yok"
    assert "finally" in sub, "ağ hatasında düğme sonsuza dek kilitli kalır"


# =================================================================================================
# KALEM 2 — inbox_count REVIEW planlarını SAYAR (B2 · ciddiyet 4)
# =================================================================================================
@pytest.fixture
def seeded(sandbox_state):
    repo = SRC / "state"
    for f in ("goal.yaml", "bounds.yaml"):
        shutil.copy2(repo / f, sandbox_state / f)
    config.reload_config()
    (sandbox_state / "strategy.yaml").write_text(yaml.safe_dump(config.default_strategy()))
    yield sandbox_state
    config.reload_config()


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(api, "DASH_TOKEN", "T0KEN")
    return TestClient(api.app)


def _plan(pid, verdict="REVIEW", date="2026-08-05", **ek):
    return {"id": pid, "date": date, "ticker": pid.split("-")[-1], "side": "long",
            "entry_trigger": 100.0, "stop": 95.0, "targets": [115.0], "size_r": 1.0,
            "r_multiple_expected": 3.0, "score": 71, "setup": "breakout_vcp",
            "gate_verdict": verdict, "gate_reasons": ["skor alt bantta"], **ek}


def test_bekleyen_review_sayima_GIRER(seeded, client):
    """CANLI KUSUR: üç REVIEW planı onay beklerken kart "0 bekleyen onay" yazıyordu."""
    store.write_jsonl("trade_plans.jsonl", [
        _plan("P-2026-08-05-AMGN"), _plan("P-2026-08-05-NVDA"), _plan("P-2026-08-05-MSFT")])
    store.write_json("portfolio.json", {"armed": [], "positions": {}, "last_date": "2026-08-05"})
    d = client.get("/api/today", headers=HDR).json()
    assert d["inbox_count"] == 3, "gelen kutusu sayacı REVIEW planlarını hâlâ görmüyor"
    assert [p["onay_bekliyor"] for p in d["todays_plans"]] == [True, True, True]


def test_sayim_OLCUTU_uc_kosullu(seeded, client):
    """GO onay beklemez (zaten kuyrukta) · NO_GO ASLA onaylanamaz · onaylı REVIEW artık beklemez ·
    seansı geçmiş plan onaylanamaz (uç da 409 verir). Dördü de sayımın DIŞINDA."""
    store.write_jsonl("trade_plans.jsonl", [
        _plan("P-2026-08-05-AMGN"),                                    # tek gerçek bekleyen
        _plan("P-2026-08-05-GOGO", verdict="GO"),
        _plan("P-2026-08-05-NOGO", verdict="NO_GO"),
        _plan("P-2026-08-05-ONAY", operator_onayi={"ts": "2026-08-05T14:55:00+00:00", "kanal": "pano"}),
    ])
    store.write_json("portfolio.json", {"armed": [], "positions": {}, "last_date": "2026-08-05"})
    d = client.get("/api/today", headers=HDR).json()
    bekleyen = [p["ticker"] for p in d["todays_plans"] if p["onay_bekliyor"]]
    assert bekleyen == ["AMGN"], f"ölçüt kaymış: {bekleyen}"
    assert d["inbox_count"] == 1


def test_seansi_gecmis_review_SAYILMAZ(seeded, client):
    """SIRA ZORUNLU: damgalama `expired`e bakar ve o alan `_enrich_stale_plans`te yazılır. Sayım
    ondan ÖNCE koşsaydı süresi dolmuş planlar da "onayını bekliyor" diye sayılırdı."""
    store.write_jsonl("trade_plans.jsonl", [_plan("P-2026-08-04-OLD", date="2026-08-04")])
    store.write_json("portfolio.json", {"armed": [], "positions": {},
                                        "last_date": "2026-08-05"})   # işlenen son seans DAHA YENİ
    d = client.get("/api/today", headers=HDR).json()
    assert d["todays_plans"][0]["expired"] is True
    assert d["todays_plans"][0]["onay_bekliyor"] is False
    assert d["inbox_count"] == 0


def test_cagri_sirasi_kaynakta_CIVILI():
    """Sıra bir yorum değil bir SÖZLEŞME: `_onay_bekleyen_damgala` `_enrich_stale_plans`ten SONRA."""
    g = _apipy_govde("def api_today(request: Request):", "\n@app.get(\"/api/signals\")")
    assert g.index("_enrich_stale_plans(") < g.index("_onay_bekleyen_damgala("), \
        "damgalama zenginleştirmeden ÖNCE koşuyor — expired bilinmeden onay bekleyen sayılır"
    assert g.index("_onay_bekleyen_damgala(") < g.index('d["inbox_count"]')


def test_sayac_kaynagi_TEK_ikinci_defter_okumasi_yok():
    """Aynı yanıtın içinde iki okuma anı = aynı sorunun iki cevabı. Plan sayımı `todays_plans`tan
    gelir; `_inbox_count` deftere kendi eliyle GİTMEZ."""
    fn = _pykod(_apipy_govde("def _inbox_count(planlar: list | None = None) -> int:",
                             "\n# ---------- write surface"))
    assert "trade_plans.jsonl" not in fn, "sayaç defteri ikinci kez okuyor"
    assert "read_jsonl" not in fn, "sayaç defteri ikinci kez okuyor"
    assert "onay_bekliyor" in fn, "sayaç sunucunun kendi damgasını okumuyor"


def test_olcut_TEK_YERDE_panoda_kopyasi_yok():
    """Pano bayrağı OKUR, ölçütü yeniden KURMAZ — yoksa kart ile liste aynı gün ayrışırdı."""
    assert 'p.onay_bekliyor' in APPJS
    assert 'gate_verdict === "REVIEW" && !p.operator_onayi' not in KOD, \
        "ölçüt panoda ikinci kez yazılmış"


def test_bir_olcumun_hatasi_digerini_SILMEZ():
    """YASA 4'ün ince hâli: skill/arming kaynağı patlarsa ÖLÇÜLMÜŞ plan sayısı sıfırlanmamalı."""
    fn = _pykod(_apipy_govde("def _inbox_count(planlar: list | None = None) -> int:",
                             "\n# ---------- write surface"))
    assert fn.index("n_plan = sum(") < fn.index("try:"), "plan sayımı try'ın içine düşmüş"
    assert "return n_plan" in fn.split("except Exception")[1]


def test_bugun_kartinin_bagi_ONAY_YUZEYINE_iner():
    """Kart bekleyen ONAYI sayıyorsa bağı da onay yüzeyine inmeli; sayfanın başına bırakıp
    "şimdi ara" demek kartın kendi cümlesini yarıda keser."""
    blok = re.search(r"const GENEL_KARTLARI = \[(.*?)\n\];", APPJS, re.S).group(1)
    # ÇİVİ TAŞINDI (D2-b): onay kuyruğunun yüzeyi ② Karar oldu; çapa aynen korundu.
    assert '["bugun",    "Bugün ne var",         "karar#onaylar"]' in blok
    # Bağ SAYISI değişmedi: kart hâlâ tek bağ taşır (v155 sözleşmesi).
    fn = _govde("function gbKart(anahtar, govde) {", '\n// "—" ile "0"')
    assert fn.count("data-act=") == 1
    assert "ALAN_ADI[k.sayfa]" in fn, "etiket ham adresi yazıyor (çapa etikete sızmış)"


def test_kart_REVIEW_kirilimini_yazar_ve_olculemeyeni_UYDURMAZ():
    g = _govde("  const silahliN = (t.armed_plans || []).length;", "\n  // ---- 4-6)")
    assert "onay_bekliyor" in g and "plan onayını bekliyor" in g
    assert "REVIEW ölçülemedi" in g, "plan defteri gelmediğinde 0 yazılıyor (uydurma)"
    assert "Array.isArray(t.todays_plans)" in g, "eksik liste boş liste sayılıyor"


# =================================================================================================
# KALEM 3 — FLATTEN'ın İKİNCİ ve ZAYIF yolu KAPANDI (B3 · ciddiyet 4)
# =================================================================================================
def test_yikici_ucun_TEK_cagirani_var():
    """Bir ucun kapısı, o uca giden EN ZAYIF yolun kapısıdır."""
    yerler = [m.start() for m in re.finditer(r"/api/alpaca/close_all", KOD)]
    assert len(yerler) == 1, f"close_all panoda {len(yerler)} yerden çağrılıyor"
    flat = _blok("window.opFlatten = async () => {", lambda ln: ln.rstrip("\n") == "};")
    assert "/api/alpaca/close_all" in flat, "tek çağrı Kademe 3'ün dışında"


def test_tek_confirmli_yol_OLDU():
    assert "window.alpacaClose" not in KOD, "tek-onaylı düzleştirme yolu geri gelmiş"
    assert 'data-act="alpacaClose"' not in KOD and 'data-act="alpacaClose"' not in INDEX
    eylemler = _govde("const EYLEMLER = new Set([", "]);")
    assert '"alpacaClose"' not in eylemler, "izin listesinde kalırsa 'kayıtlı ama tanımsız' olur"


def test_kalan_yol_IKI_ADIMLI():
    """Kademe 3 çift onay ister; kaldırılan düğme tek `confirm()` ile aynı ucu çağırıyordu."""
    flat = _blok("window.opFlatten = async () => {", lambda ln: ln.rstrip("\n") == "};")
    assert flat.count("confirm(") == 2, "FLATTEN'ın çift onayı zayıflamış"
    assert "SON ONAY" in flat


def test_ayarlar_karti_ADRES_birakti_kapi_degil():
    """Düğme kalkarken yol da kaybolmamalı: kart artık Kademe 3'e GÖTÜRÜR, çağırmaz."""
    kart = _govde("function _alpacaKartHTML(a) {", "\nRENDER.ayarlar = async () => {")
    assert 'data-a1="kilitler#mudahale"' in kart
    assert "FLATTEN" in kart and "çift onay" in kart


def test_mudahale_panelinin_BEYANI_artik_dogru():
    """Panel ekranda "ikinci bir yetki yolu yoktur" yazıyordu ve bu, düğme dururken YANLIŞTI."""
    assert "ikinci bir yetki yolu yoktur" in APPJS
    kart = _govde("function _alpacaKartHTML(a) {", "\nRENDER.ayarlar = async () => {")
    assert kart.count('data-act="alpacaSubmit"') == 1, "gönderim düğmesi çoğalmış"
    assert "data-act=" not in kart.split('data-act="alpacaSubmit"')[1].split("</div>")[0], \
        "düğme sırasında ikinci bir eylem doğmuş"


# =================================================================================================
# KALEM 4 — SESSİZ HAT askıda'yı OKUYOR (B6 · ciddiyet 3 · YASA 6)
# =================================================================================================
def test_api_hala_uretiyor_pano_ARTIK_okuyor():
    assert '"n_askida": len(askida)' in APIPY, "üretici düşmüş — testin tabanı kaybolur"
    sh = _govde("function sessizHat(sh) {", "\n// ---- ALARM BÜTÇESİ")
    assert "_shAskidaSatiri(sh.segmentler)" in sh, "şerit askıda dalını hâlâ okumuyor"


@pytest.fixture(scope="module")
def askida() -> dict:
    betik = ESC_TRN + "const SH_ACILIM_TAVAN = 4;\n" + _blok(
        "function _shAskidaSatiri(segmentler) {", lambda ln: ln.rstrip("\n") == "}") + """
const seg = ad => ({ ad, saglikli: true, ozet: "15/17" });
const out = {
  dolu: _shAskidaSatiri([{ ...seg("bekçiler"), n_askida: 2, askida: [
    { ad: "hermes_reflect", neden: "kota soğuması", detay: "3 anahtar tükendi", sure: "2 sa 10 dk" },
    { ad: "skill_evolve", neden: "kimlik havuzu boş", sure: "45 dk" }] }]),
  bos: _shAskidaSatiri([{ ...seg("bekçiler"), n_askida: 0, askida: [] }]),
  nedensiz: _shAskidaSatiri([{ ...seg("bekçiler"), n_askida: 1, askida: [{ ad: "x" }] }]),
  kirpik: _shAskidaSatiri([{ ...seg("bekçiler"), n_askida: 9, askida: [
    { ad: "a", neden: "n" }, { ad: "b", neden: "n" }, { ad: "c", neden: "n" },
    { ad: "d", neden: "n" }, { ad: "e", neden: "n" }] }]),
  adsiz: _shAskidaSatiri([{ ...seg("bekçiler"), n_askida: 2, askida: [] }]),
};
process.stdout.write(JSON.stringify(out));
"""
    return _node(betik)


def test_askida_ADIYLA_ve_NEDENIYLE_gorunur(askida):
    """Eksik bekçinin nedeni artık METİN: hover-only `title` ipucu klavyeyle erişilemezdi."""
    m = askida["dolu"]
    assert "2 askıda" in m
    assert "hermes_reflect" in m and "kota soğuması" in m
    assert "skill_evolve" in m and "kimlik havuzu boş" in m
    assert "2 sa 10 dk" in m


def test_askida_SAPMA_SAYILMAZ_alarm_hijyeni_korunur(askida):
    """Meşru bir beklemeyi kırmızıya boyamak, hattın var oluş sebebini (alarm yorgunluğu) yer."""
    assert "sh-sap" not in askida["dolu"] and "kritik" not in askida["dolu"]
    sh = _govde("function sessizHat(sh) {", "\n// ---- ALARM BÜTÇESİ")
    assert 'sh.saglikli ? " ok" : " sap"' in sh, "şeridin hâli askıda'dan etkilenir olmuş"
    assert "n_askida" not in sh.replace("_shAskidaSatiri(sh.segmentler)", ""), \
        "askıda sayımı sapma hesabına sızmış"
    # CSS de aynı sözü tutar: askıda satırında uyarı mürekkebi YOK.
    kural = re.search(r"\.sessizhat \.sh-ask\{([^}]*)\}", CSS).group(1)
    assert "--amber" not in kural and "--red" not in kural
    assert "flex-basis:100%" in kural, "satır kendi satırını almıyor — nowrap ritmi taşar"


def test_askida_yokken_HIC_konusmaz(askida):
    """Sessiz hattın birinci kuralı: sağlıklıyken sus."""
    assert askida["bos"] == ""


def test_okunamayan_neden_UYDURULMAZ(askida):
    assert "neden bildirilmedi" in askida["nedensiz"]
    assert "ad/neden uçtan gelmedi" in askida["adsiz"], "sayı varken ad yoksa satır sessizleşmiş"


def test_kirpma_SESSIZ_degil(askida):
    """Açılım tavanı şeridin mevcut kuralı; kırpılan sayı YAZILIR."""
    assert "+5 daha" in askida["kirpik"]


def test_api_alanlarinin_HEPSININ_okuyucusu_var():
    """YASA 6 paritesi: üreticinin yazdığı dört alanın dördü de panoda okunuyor."""
    uretici = _apipy_govde('"askida": [{"ad": a.get("name")', '"n_askida": len(askida)')
    fn = _blok("function _shAskidaSatiri(segmentler) {", lambda ln: ln.rstrip("\n") == "}")
    # "askida" kabın KENDİ adıdır, satırın alanı değil — sözlük anahtarlarını ondan ayır.
    alanlar = set(re.findall(r'"(\w+)":', uretici)) - {"askida"}
    assert alanlar, "üretici dilimi boş kesilmiş — testin kendisi bozuk"
    for alan in alanlar:
        assert f"a.{alan}" in fn, f"askıda.{alan} üretiliyor ama panoda okunmuyor (YASA 6)"


# =================================================================================================
# KALEM 5 — ONAYLAR BÖLÜMÜ KENDİ SORUSUNU CEVAPLIYOR (B4 · ciddiyet 3)
# =================================================================================================
def _onaylar_govde(yorumsuz: bool = False) -> str:
    g = _govde("RENDER.onaylar = async () => {", "\n// ================= öğrenme antrenmanı")
    if yorumsuz:
        g = "\n".join(l for l in g.splitlines() if not l.lstrip().startswith("//"))
    return g


def test_onay_bekleyen_planlar_ONAY_YUZEYINDE_listeleniyor():
    g = _onaylar_govde()
    assert 'j("/api/today")' in g, "bölüm plan defterini hiç okumuyor"
    assert "p.onay_bekliyor" in g and "Onayını bekleyen planlar" in g
    assert "planRowFull" in g, "satırlar adaylar tablosunun deseninden ayrılmış"


def test_IKINCI_onay_yolu_ACILMADI():
    """Bu turun kendi dersi: aynı yazma eylemine ikinci bir kapı açmak, kapattığımız kusurun ta
    kendisidir. Onay düğmesi TEK yerde (`planOnayBloguHTML`) ve o da çekmecenin içinde."""
    g = _onaylar_govde(yorumsuz=True)
    assert "planOnayBloguHTML" not in g and 'data-act="planOnayla"' not in g
    cagri = KOD.count("planOnayBloguHTML(") - KOD.count("function planOnayBloguHTML(")
    assert cagri == 1, f"onay bloğunun {cagri} çağıranı var — tek yüzey olmalı (çekmece)"
    assert KOD.count('id="plan-onay-btn"') == 1


def test_bos_ile_OLCULEMEDI_ayri_cumleler():
    g = _onaylar_govde()
    assert "ölçülemedi" in g and "bekleyen onay yok" in g.replace("\n", " ").replace("  ", " ")
    assert "plan üretilmedi" in g, "sıfır plan ile sıfır REVIEW aynı cümleye düşmüş"
    assert "NO_GO onaylanamaz" in g, "boş hâlin sebebi yazılmıyor"


def test_bolumun_soru_cumlesi_DEGISMEDI():
    """Yüzey soruya taşındı, soru yüzeye uydurulmadı."""
    assert 'onaylar:    "Bu bölüm şunu cevaplar: şu an benim onayımı bekleyen ne var?"' in APPJS


# =================================================================================================
# KALEM 6-7 — TİPOGRAFİ RAMPASI: sistemin KENDİ yasası (DESIGN.md "The Ramp Rule")
# =================================================================================================
# ÖLÇÜM (Rol-1, 2026-08-06): index.html'deki 125 `font-size` bildiriminin 123'ü rampadaydı. Kalan
# ikisi yasayı çiğniyordu — 19px (rampada yok; "bölüm başlığı ile sayfa başlığı arasında ÜÇÜNCÜ
# bir mertebe" diye okunur) ve 8px (hem rampa dışı hem okunabilirlik tabanının altında). Üçüncü
# kusur bir DEĞER değil bir İDİOM kaymasıydı: 10px Label basamağı bu sistemde rakam üstündeki mono
# mikro-etiketin imzasıdır; giriş formunun parola etiketleri o idioma değil normal form metnine ait.
#
# TARAMANIN KAPSAMI DÜZ BİLDİRİMLERDİR: `.gb-say`ın `clamp(20px,2.6vw,26px)` akışkan aralığı bir
# BASAMAK değil bir menzildir ve bu turun kalemi değildir — kapsam dışı olduğu burada YAZILI, ki
# "tarama görmedi" ile "bilerek dışarıda" karışmasın.
RAMPA_TABLO = re.compile(r"\|\s*[\w /]+\s*\|\s*`font-size:\s*(\d+)px`")


def _rampa() -> set[int]:
    """Rampa DESIGN.md'den okunur, teste GÖMÜLMEZ: iki liste olsaydı biri sessizce bayatlardı."""
    design = (SRC / "DESIGN.md").read_text()
    basamaklar = {int(m) for m in RAMPA_TABLO.findall(design)}
    assert len(basamaklar) == 9, f"DESIGN.md type-scale tablosu 9 basamak vermiyor: {sorted(basamaklar)}"
    return basamaklar


def test_index_html_RAMPA_DISI_deger_tasimaz():
    """SINIF-DÜZEYİ ÇİVİ. Tek bir ara değer ("biraz küçük göründü") rampayı bir kez deldiğinde,
    sonraki her ara değerin gerekçesi hazır olur."""
    rampa = _rampa()
    ihlaller = []
    for m in re.finditer(r"font-size:\s*(\d+)px", INDEX):
        px = int(m.group(1))
        if px not in rampa:
            ihlaller.append(f"index.html:{INDEX[:m.start()].count(chr(10)) + 1}: {px}px")
    assert not ihlaller, ("DESIGN.md 'The Ramp Rule' ihlali (rampa: "
                          + " · ".join(f"{p}px" for p in sorted(rampa)) + "):\n" + "\n".join(ihlaller))


# 2026-08-24 · TİP RAMPASI JETONLANDI. Aşağıdaki basamak çivileri BOYUTU ölçüyor, yazılış
# biçimini değil; `var(--t-sub)` gibi bir jeton index.html'in KENDİ `:root` tablosundan
# çözülür. Tabloyu buraya sabit yazmak, ölçülen şeyin ikinci bir kopyasını yaratırdı.
_KOK_TIP = dict(re.findall(r"--(t-[a-z0-9-]+|label-size)\s*:\s*(\d+px)",
                           re.sub(r"/\*.*?\*/", " ", INDEX, flags=re.S)))


def _px_coz(govde: str) -> str:
    return re.sub(r"var\(\s*--([a-z0-9-]+)\s*\)",
                  lambda m: _KOK_TIP.get(m.group(1), m.group(0)), govde)


def test_tip_jeton_cozucusu_CALISIYOR():
    """Çözücü boş dönerse yukarıdaki iki basamak çivisi sessizce anlamsızlaşır."""
    assert _KOK_TIP.get("t-sub") == "20px" and _KOK_TIP.get("t-cap") == "11px", _KOK_TIP
    assert _px_coz("font-size:var(--t-sub)") == "font-size:20px"


def test_bolum_basligi_HEADLINE_basamaginda():
    """19px → 20px (Headline). Sayfa başlığından (24px) hâlâ bir basamak aşağıda: hiyerarşi
    ağırlıkla değil BASAMAKLA korunuyor.

    2026-08-24: rampa JETONLANDI (`font-size:var(--t-sub)`). ÖLÇÜLEN ŞEY BASAMAKTIR,
    YAZILIŞ BİÇİMİ DEĞİL — jeton index.html'in kendi `:root`undan çözülür, buraya ikinci
    bir `20` sabiti yazılmaz."""
    kural = _px_coz(re.search(r"\.alan-bolum h2\.ph,\.alan-bolum h2\.greet\{([^}]*)\}", INDEX).group(1))
    assert "font-size:20px" in kural


def test_eksen_etiketi_OKUNABILIR_tabanda():
    """8px → 10px. Sönüklük MÜREKKEPLE kurulur (--tx2), puntoyla değil.

    2026-08-24 (Dub göçü): iddia bir TABAN, dondurulmuş bir sabit değil. Etiket basamağı
    maketin `--t-cap`ine (11px) çıktı; 11 ≥ 10, yani okunabilirlik iddiası ÇİĞNENMEDİ,
    GÜÇLENDİ. Eskiden burada literal `10px` yazılıydı ve rampa jetonlanınca çivi, ölçtüğü
    şey iyileştiği HÂLDE düştü — sabit, iddianın kendisi sanılmıştı."""
    kural = _px_coz(re.search(r"\.bl-ax\{([^}]*)\}", INDEX).group(1))
    m = re.search(r"font-size:(\d+)px", kural)
    assert m, ".bl-ax punto bildirmiyor"
    assert int(m.group(1)) >= 10, (
        f"eksen etiketi {m.group(1)}px — okunabilirlik tabanı 10px'in ALTINA düştü; "
        f"sönüklük mürekkeple kurulur, puntoyla değil")
    assert "var(--tx2)" in kural
    # Etiket SAYISI iki (iki uç) — sıkışma çözümü punto düşürmek değil, etiket azaltmaktır.
    assert APPJS.count('class="bl-ax"') == 2


def test_parola_etiketleri_MICRO_basamaginda():
    """10px imzası rakam üstündeki mono mikro-etikete ait; parola alanının etiketi form metnidir."""
    kural = _px_coz(re.search(r"\.gate-l\{([^}]*)\}", INDEX).group(1))
    assert "font-size:11px" in kural
    # İDİOM YERİNDE KALDI: rakam üstündeki mikro-etiket hâlâ Label basamağında — ve o basamağı
    # kendi jetonundan (`--label-size`) alıyor, yani idiomun tek bir sahibi var.
    assert "font-size:var(--label-size)" in re.search(r"\.bl-lab\{([^}]*)\}", INDEX).group(1)
    # 2026-08-24 (Dub göçü): ~~--label-size:10px~~ → 11px, maketin `--t-cap` basamağı.
    # ÖLÇÜLEN İDDİA "10" SABİTİ DEĞİL, TEK SAHİPLİK: mikro-etiket basamağını kendi jetonundan
    # alır ve o jeton rampanın kapak basamağıyla AYNI olmalı — iki ayrı 11px doğarsa idiom
    # yine ikiye bölünür ve bu çivinin varlık sebebi tam olarak o bölünmeyi engellemek.
    m_l = re.search(r"--label-size:(\d+)px", INDEX)
    m_c = re.search(r"--t-cap:(\d+)px", INDEX)
    assert m_l and m_c, "etiket/kapak basamağı jetonu bulunamadı"
    assert m_l.group(1) == m_c.group(1), (
        f"Label basamağı ({m_l.group(1)}px) rampanın kapak basamağından ({m_c.group(1)}px) "
        f"AYRILMIŞ — mikro-etiket idiomunun iki sahibi olur")
    # Ve etiketler gerçekten bu sınıfı kullanıyor (kural ile kullanım ayrışmasın).
    assert INDEX.count('class="gate-l"') == 2


# =================================================================================================
# ORTAK — sözdizimi kapısı
# =================================================================================================
@pytest.mark.skipif(NODE is None, reason="node yok")
def test_node_check_gecer():
    r = subprocess.run([NODE, "--check", str(WEB / "app.js")], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
