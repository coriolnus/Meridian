"""v238 ARIZA TURU — canlıda ölçülen ÜÇ sessiz arızanın kapanış testleri (2026-08-13).

Üçünün ortak sınıfı: **bir mekanizma çalışıyor GÖRÜNÜYOR ama ürettiği şey kimseye ulaşmıyor.**

[A] EVREN DENETİMİ SURVIVORSHIP KANITI ÜRETMİYORDU. `constituents._fetch_tables`
    `pd.read_html(r.text)` çağırıyordu; pandas 3.0.3 ham HTML DİZGESİNİ dosya-yolu sanıyor ve
    canlı `state/universe_drift.json` `reason: "FileNotFoundError: [Errno 2] No such file or
    directory: <!DOCTYPE html>..."` yazıyordu. Yani rapor "kaynak yok" diyordu ve NEDENİ de
    yanlış sınıftaydı (dosya yok ≠ ayrıştırılamadı). Yerelde birebir üretildi (pandas 3.0.3):
    ham dizge → FileNotFoundError · `io.StringIO(...)` → parse OK.
    BEYAN DÜZELTMESİ: modül başlığındaki "(a) lxml/bs4/html5lib kurulu değil" iddiası ARTIK
    YANLIŞ (lxml 6.1.1 kurulu, pyproject ana bağımlılık); "(b) Wikipedia 403" iddiası HÂLÂ
    DOĞRU (2026-08-13 ölçümü: HTTP 403, gövde 141 bayt). Başlık ikisini de tarihiyle yazar.

[B] "UYGULA" DÜĞMESİ SESSİZ ÖLÜYORDU (operatör vakası). Öneri üreteci + kayıt kapısı ÜÇ eylem
    tanıyordu (shadow/activate/**lean_in**), uygulayıcı yalnız İKİ. `lean_in` için
    `{"ok": False, "reason": "unknown action 'lean_in'"}` dönüyordu, api uç bunu HTTP **200** ile
    yolluyordu, pano yalnız FIRLATILAN hatayı yazdığı için (v219 sözleşmesi) ekranda hiçbir şey
    olmuyordu — v219'da kapatılan sessiz-ret sınıfının 200-gövde-ret yolundan ikinci örneği.
    İKİ AYRI KUSUR, İKİSİ DE KAPALI: (B1) `ok:False` artık durum koduyla FIRLAR; (B2) `lean_in`
    "uygulanabilir" gibi SUNULMAZ (`actions: []` + dürüst not — `arming:{setup}` emsali).

[C] `orphan_state_files` DAMGALI GÖÇ ARŞİVİNİ YETİM SAYIYORDU. Canlı:
    `state/scoreboard.json.migrated-20260812-201359-p192112`. Dedektör haksız değildi (okuyucusu
    yok) ama SINIFI yanlıştı: bu, `store._bayat_defter_suzgeci`in çarpışma dalıdır (hedef doluysa
    `.migrated-<ts>-p<pid>`) ve düz `.migrated` zaten tanınıyordu. Artık TANINMIŞ TERMİNAL SINIF —
    `migrasyon_artigi` adıyla SAYILIR (sessizce yok sayılmaz) ve satırı düşürmez.

BU DOSYANIN KURALI (v204'ten devralındı): bir dedektörü/kapıyı susturmanın iki yolu vardır ve
yalnız biri dürüsttür. Aşağıdaki her "artık geçiyor" testinin YANINDA bir "hâlâ yakalıyor"
testi durur; deseni gevşetmedik, sınıfı düzelttik.
"""
from __future__ import annotations

import inspect
import io
import json
import pathlib

import pytest
from fastapi.testclient import TestClient

from meridian import api, config, obs, recompute, skills, store
from meridian.adapters import constituents as con

REPO = pathlib.Path(__file__).resolve().parent.parent


# =================================================================================================
# [A] EVREN DENETİMİ — pandas-3'te HAM DİZGE DOSYA YOLU SANILIYOR
# =================================================================================================
def _wiki_fikstur(n: int = 3) -> str:
    """Wikipedia'nın İKİ tablosunu taklit eden sabit HTML (ağ YOK — 403 yüzünden gidilemiyor).
    Şekil gerçeğe göre kurulur: tablo-0 `Symbol` kolonu, tablo-1 iki katlı başlık
    (Date · Added/Ticker · Removed/Ticker) — `_fetch_tables`in okuduğu tam yapı."""
    satir = "".join(f"<tr><td>SYM{i:03d}</td><td>Firma {i}</td></tr>" for i in range(n))
    return f"""<html><body>
<table id="constituents"><tr><th>Symbol</th><th>Security</th></tr>{satir}</table>
<table id="changes">
  <tr><th colspan="1">Date</th><th colspan="2">Added</th><th colspan="2">Removed</th></tr>
  <tr><th>Date</th><th>Ticker</th><th>Security</th><th>Ticker</th><th>Security</th></tr>
  <tr><td>2024-10-01</td><td>AMTM</td><td>Amentum</td><td></td><td></td></tr>
  <tr><td>2024-09-23</td><td>PLTR</td><td>Palantir</td><td>AAL</td><td>American</td></tr>
</table></body></html>"""


class _Yanit:
    def __init__(self, text: str, status_code: int = 200):
        self.text, self.status_code = text, status_code


def _httpx_ver(monkeypatch, govde: str, kod: int = 200) -> None:
    import httpx
    monkeypatch.setattr(httpx, "get", lambda *a, **k: _Yanit(govde, kod))


def _pandas3_semantigi(monkeypatch) -> None:
    """pandas 3 davranışını KURULU SÜRÜMDEN BAĞIMSIZ dayat: `read_html`a DİZGE gelirse dosya
    yolu sanılır ve FileNotFoundError atılır. Canlıda pandas 3.0.3 var (yerelde de birebir
    üretildi) ama regresyon çivisi bir sürüm tesadüfüne bağlı olmamalı — yarın taban pandas 2'ye
    çekilirse test sessizce kör olurdu."""
    import pandas as pd
    gercek = pd.read_html

    def _sarmal(kaynak, *a, **k):
        if isinstance(kaynak, str):
            raise FileNotFoundError(f"[Errno 2] No such file or directory: {kaynak[:60]}")
        return gercek(kaynak, *a, **k)

    monkeypatch.setattr(pd, "read_html", _sarmal)


def test_A_fikstur_HTML_pandas3te_AYRISTIRILIYOR(sandbox_state, monkeypatch):
    """ARIZANIN DOĞRUDAN ÇİVİSİ: pandas-3 semantiği dayatılmışken `_fetch_tables` YİNE DE
    ayrıştırmalı. Düzeltme öncesi bu test `(None, None)` + FileNotFoundError ile kırmızıydı."""
    _pandas3_semantigi(monkeypatch)
    _httpx_ver(monkeypatch, _wiki_fikstur(3))
    cur, changes = con._fetch_tables()
    assert cur == ["SYM000", "SYM001", "SYM002"], f"semboller ayrıştırılamadı: {cur}"
    assert [c["added"] for c in changes] == ["AMTM", "PLTR"], changes
    assert changes[1]["removed"] == "AAL" and changes[0]["removed"] == "", changes
    assert "FileNotFoundError" not in con.health()["error"], con.health()


def test_A_dizge_yolu_REGRESYONU_kaynakta_kapali():
    """YAPISAL ÇİVİ: `pd.read_html(r.text)` geri gelirse test kırmızıya döner. Fonksiyonel çivi
    tek başına yetmez — biri `io.StringIO`yu 'gereksiz' diye sadeleştirirse arıza AYNEN geri
    gelir ve yalnız pandas-3 makinelerinde görünür."""
    # YORUMSUZ GÖVDE (v215 `_govde` dersi): gerekçe yorumu ESKİ çağrıyı alıntılıyor ve alıntı bir
    # ÇAĞRI DEĞİLDİR — ham metinde aramak, testi kendi belgelendirmesine karşı kırardı.
    src = "\n".join(l for l in inspect.getsource(con._fetch_tables).splitlines()
                    if not l.lstrip().startswith("#"))
    assert "io.StringIO(r.text)" in src, "StringIO sarmalı kaybolmuş — pandas-3'te dizge=dosya yolu"
    assert "pd.read_html(r.text)" not in src, "ham dizge yolu geri gelmiş"


def test_A_tablosuz_govde_DURUST_sebep_yaziyor(sandbox_state, monkeypatch):
    """SEBEP SINIFI DA DÜZELTİLDİ. Varsayılan zincir lxml tablo bulamazsa bs4+html5lib'e düşer;
    html5lib kurulu olmadığı için hata `ImportError: Import html5lib failed` olurdu — yani
    GERÇEK sebep "tablo yok" iken `health()` "paket eksik" derdi. Tam da bu dosyanın başlığındaki
    (a) beyanını çürüten yanlış-teşhis döngüsü. `flavor="lxml"` sabitlendiği için sebep dürüst."""
    _httpx_ver(monkeypatch, "<html><body><p>403 forbidden</p></body></html>")
    from meridian.adapters import fmp
    monkeypatch.setattr(fmp, "available", lambda: False)
    assert con.current() == []
    hata = con.health()["error"]
    assert "html5lib" not in hata, f"eksik-paket YANLIŞ sınıfı geri gelmiş: {hata}"
    assert "No tables found" in hata or "ValueError" in hata, hata


def test_A_403_HALA_gecerli_ve_saydam(sandbox_state, monkeypatch):
    """Beyanın (b) yarısı 2026-08-13'te YENİDEN ÖLÇÜLDÜ ve DOĞRU çıktı: bu UA'ya 403. StringIO
    düzeltmesi bunu değiştirmez ve değiştirmediği GÖRÜNÜR kalmalı — 'düzelttik' cümlesi
    kaynağın açıldığı anlamına gelmemeli."""
    _httpx_ver(monkeypatch, "", 403)
    from meridian.adapters import fmp
    monkeypatch.setattr(fmp, "available", lambda: False)
    assert con.current() == []
    assert con.health()["ok"] is False and "403" in con.health()["error"]


def test_A_baslik_beyani_OLCUME_gore_tarihli(sandbox_state):
    """YASA: çürümüş bir beyan, olmayan bir sınırı canlı sanmaya yol açar — bu vakada tam olarak
    oldu (gerçek kök aylarca 'bilinen eski sınır' sanıldı). Başlık artık ÖLÇÜMÜ ve TARİHİ taşır,
    ve iddiaların ikisi de burada BAĞIMSIZ doğrulanır (metne değil, kuruluma bakarak)."""
    doc = con.__doc__ or ""
    assert "2026-08-13" in doc and "io.StringIO" in doc, "beyan tarihli ölçümle güncellenmemiş"
    assert "FileNotFoundError" in doc, "gerçek kök beyanda yazılı değil"
    import lxml  # noqa: F401  — (a) iddiasının çürüdüğünün ÖLÇÜSÜ: kurulum gerçekten var
    assert "lxml" in (REPO / "pyproject.toml").read_text(), "lxml ana bağımlılık olmaktan çıkmış"


def test_A_uctan_uca_MAKUL_liste_onbellege_yaziliyor(sandbox_state, monkeypatch):
    """Zincirin tamamı: fikstür → StringIO → makullük kapısı → önbellek → `current()`. Kaynak
    bir gün açılırsa (UA/anlaşma) evren denetiminin GERÇEKTEN kanıt üreteceğinin çivisi."""
    _pandas3_semantigi(monkeypatch)
    _httpx_ver(monkeypatch, _wiki_fikstur(460))
    from meridian.adapters import fmp
    monkeypatch.setattr(fmp, "available", lambda: False)
    out = con.current()
    assert len(out) == 460 and con.health()["source"] == "wikipedia"
    assert store.read_json(con.CACHE, {})["source"] == "wikipedia"


# =================================================================================================
# [B] "UYGULA" SESSİZ ÖLÜMÜ — (B1) ret GÖRÜNÜR · (B2) lean_in UYGULANABİLİR GİBİ SUNULMAZ
# =================================================================================================
def _istemci(monkeypatch) -> TestClient:
    monkeypatch.setattr(api, "DASH_TOKEN", None)
    return TestClient(api.app)


def _kayit() -> None:
    store.write_json("skills_registry.json", {"skills": {
        "loser-skill": {"category": "x", "fmp": "-", "alpaca": "-", "enabled": True,
                        "mode": "active", "style_active": True, "pipeline": "P2_SCREEN"},
    }})


def _oneri(action: str, skill: str = "loser-skill") -> None:
    store.append_jsonl(skills.SKILL_RECS, {"ts": "2026-08-13T00:00:00+00:00", "skill": skill,
                                           "action": action, "rationale": "ölçüm",
                                           "pending": True, "applied": False})


# ---- B0: sözlük TEK KAYNAK ---------------------------------------------------------------------
def test_B0_uygulanabilir_ONERILEBILIRIN_alt_kumesi():
    """Ayrımın kendisi bir beyan: her uygulanabilir eylem önerilebilirdir, tersi ŞART DEĞİL."""
    assert set(skills.UYGULANABILIR_EYLEMLER) < set(skills.ONERILEBILIR_EYLEMLER)
    assert "lean_in" in skills.ONERILEBILIR_EYLEMLER
    assert "lean_in" not in skills.UYGULANABILIR_EYLEMLER


def test_B0_hermes_semasi_TEK_KAYNAKTAN_turuyor():
    """ARIZANIN KÖKÜ ÇOĞALTILMIŞ LİSTEYDİ. Enum artık `skills.ONERILEBILIR_EYLEMLER`den çıkar;
    elle yazılı bir üçlü geri gelirse burası kırmızı olur. Sıra da korunur (v106 çivisi)."""
    from meridian import hermes
    enum = hermes.HYP_SCHEMA["properties"]["skill_recommendation"]["properties"]["action"]["enum"]
    assert enum == list(skills.ONERILEBILIR_EYLEMLER) == ["shadow", "activate", "lean_in"]
    assert '"enum": ["shadow"' not in inspect.getsource(hermes)[:8000], "elle liste geri gelmiş"


def test_B0_kayit_kapisi_SOZLUKTEN_okuyor(sandbox_state):
    """`record_recommendation` hâlâ üç eylemi de KAYDEDER: `lean_in` bir ölçümdür ve operatörün
    görmesi gerekir. Kaydedilebilirlik ile uygulanabilirlik AYRI sorulardır."""
    _kayit()
    assert skills.record_recommendation({"skill": "loser-skill", "action": "lean_in",
                                         "rationale": "güçlü katkı"}) is True
    assert skills.record_recommendation({"skill": "loser-skill", "action": "delete",
                                         "rationale": "x"}) is False


# ---- B1: ret GÖRÜNÜR ---------------------------------------------------------------------------
def test_B1_lean_in_ARTIK_200_ILE_SESSIZCE_gecmiyor(sandbox_state, monkeypatch):
    """ARIZANIN DOĞRUDAN ÇİVİSİ (operatör vakası). Düzeltme öncesi: 200 + `{"ok": false, ...}`,
    pano hiçbir şey yazmıyordu. Şimdi 4xx/409 → `apiFetch` `ApiHata` fırlatır → `applySkillRec`
    `eylemHatasiYaz` ile NEDENİ ekrana basar."""
    _kayit()
    c = _istemci(monkeypatch)
    r = c.post("/api/skills/apply", json={"skill": "loser-skill", "action": "lean_in"})
    assert r.status_code == 409, f"ret HÂLÂ sessiz: {r.status_code} {r.text[:200]}"
    detay = r.json()["detail"]
    assert "rec:loser-skill" in detay, detay                 # operatörün onay kimliği gövdede
    assert "uygulayıcısı yok" in detay and len(detay) >= 20, detay
    assert store.read_json("skills_registry.json", {})["skills"]["loser-skill"].get("shadow") \
        is not True, "reddedilen eylem DÜNYAYI değiştirmiş"


@pytest.mark.parametrize("eylem,beklenen", [("delete", 400), ("lean_in", 409), ("", 400)])
def test_B1_durum_kodu_KODDAN_turer_metinden_degil(sandbox_state, monkeypatch, eylem, beklenen):
    """400 (istek BOZUK) ile 409 (DÜNYANIN DURUMU çakışıyor) ayrımı `kod` alanından türer.
    Serbest `reason` metnine göre dallanmak, cümle değişince kapıyı sessizce kaydırırdı."""
    _kayit()
    c = _istemci(monkeypatch)
    r = c.post("/api/skills/apply", json={"skill": "loser-skill", "action": eylem})
    assert r.status_code == beklenen, f"{eylem!r}: {r.status_code} {r.text[:160]}"


def test_B1_korumali_ve_kayitsiz_de_GORUNUR_ret(sandbox_state, monkeypatch):
    _kayit()
    c = _istemci(monkeypatch)
    r1 = c.post("/api/skills/apply", json={"skill": "portfolio-manager", "action": "shadow"})
    assert r1.status_code == 409 and "korumalı" in r1.json()["detail"]
    r2 = c.post("/api/skills/apply", json={"skill": "yok-boyle", "action": "shadow"})
    assert r2.status_code == 409 and "kayıtlı değil" in r2.json()["detail"]


def test_B1_ret_OLAY_defterine_de_dusuyor(sandbox_state, monkeypatch):
    """YASA 4: reddedilen bir eylem yalnız ekranda değil, defterde de görünür — operatör o an
    ekrana bakmıyor olabilir ve 'basıldı ama olmadı' vakası sonradan da kurulabilmeli."""
    _kayit()
    c = _istemci(monkeypatch)
    c.post("/api/skills/apply", json={"skill": "loser-skill", "action": "lean_in"})
    ev = [e for e in obs.recent(limit=200) if e.get("event") == "skill_action_refused"]
    assert ev and ev[-1]["kod"] == "uygulayicisi_yok" and ev[-1]["action"] == "lean_in", ev


def test_B1_ret_olayi_PANODA_TURKCE_cumleye_bagli():
    """YASA 6 (okuyucusuz yazım yok): olay defterine düşen ret, olay çekmecesinde ham bir mono
    jeton olarak akmamalı. Cümle `obs.warn`un BİREBİR alanlarını okur — uydurma alan yok."""
    src = (REPO / "meridian" / "web" / "app.js").read_text()
    assert "\n  skill_action_refused:" in src, "ret olayı EV_TR sözlüğünde yok"
    i = src.index("\n  skill_action_refused:")
    cumle = src[i:i + 320]
    for alan in ("e.skill", "e.action", "e.kod", "e.detail"):
        assert alan in cumle, f"{alan} cümlede okunmuyor"


def test_B1_BASARILI_uygulama_200_DEGISMEDI(sandbox_state, monkeypatch):
    """REGRESYON KAPISI: düzeltme yalnız RET yolunu değiştirdi. Başarı yolu (v215 L0 çivisi)
    birebir aynı — 200 + `{"ok": true}` + registry gerçekten yazılı."""
    _kayit()
    c = _istemci(monkeypatch)
    r = c.post("/api/skills/apply", json={"skill": "loser-skill", "action": "shadow"})
    assert r.status_code == 200 and r.json()["ok"] is True, r.text[:200]
    assert skills.registry()["skills"]["loser-skill"]["shadow"] is True


def test_B1_surec_ici_cagiran_SOZLUK_sozlesmesini_koruyor(sandbox_state):
    """Fonksiyonun kendisi İSTİSNA FIRLATMAZ ve fırlatmamalı: `auto_shadow_from_evidence` reddi
    bir KANIT SATIRI olarak yazıyor (`atlanan` → "UYGULANAMADI: <reason>"). Orayı istisnaya
    çevirmek, ölçüm döngüsünü bir bayrak reddi yüzünden düşürürdü."""
    _kayit()
    r = skills.apply_skill_action("portfolio-manager", "shadow")
    assert r["ok"] is False and r["kod"] == "korumali" and r["reason"]
    assert "res.get(\"ok\")" in inspect.getsource(skills.auto_shadow_from_evidence)


# ---- B2: lean_in "uygulanabilir" gibi SUNULMAZ --------------------------------------------------
def test_B2_gelen_kutusu_lean_in_icin_DUGME_CIZDIRMIYOR(sandbox_state, monkeypatch):
    """`arming:{setup}` emsali: uygulayıcısı olmayan öğe `actions: []` + dürüst `note` taşır.
    Pano gelen kutusu düğmeleri `(it.actions || [])` üzerinden çizdiği için düğme HİÇ doğmaz —
    yani operatör basacak bir şey bulamaz, boşuna basıp sessizlik yaşamaz."""
    _kayit()
    _oneri("lean_in")
    c = _istemci(monkeypatch)
    oge = next(i for i in c.get("/api/approvals").json()["inbox"] if i["type"] == "skill_rec")
    assert oge["actions"] == [], oge
    assert oge["uygulanabilir"] is False
    assert "davranışsal karşılığı yok" in oge["note"], oge["note"]


def test_B2_uygulanabilir_oneri_DUGMESINI_KAYBETMEDI(sandbox_state, monkeypatch):
    """Karşı-çivi: shadow/activate önerileri AYNEN uygulanabilir kalır. B2 bir kısıtlama değil
    bir DÜRÜSTLÜK düzeltmesiydi; gelen kutusunu boşaltmak çözüm olmazdı."""
    _kayit()
    _oneri("shadow")
    c = _istemci(monkeypatch)
    oge = next(i for i in c.get("/api/approvals").json()["inbox"] if i["type"] == "skill_rec")
    assert oge["actions"] == ["apply"] and oge["uygulanabilir"] is True and "note" not in oge


def test_B2_damga_TEK_URETICIDE_basiliyor(sandbox_state):
    """Damga `pending_recommendations`ta basılır; üç yüzey de (gelen kutusu · öğrenme kartı ·
    beceri sayfası) oradan beslenir. Üç yerde üç kez cevaplanan bir soru, birinin sessizce
    ayrışması demekti — arızanın kökü tam olarak buydu."""
    _kayit()
    _oneri("lean_in", "loser-skill")
    rows = {r["skill"]: r for r in skills.pending_recommendations()}
    r = rows["loser-skill"]
    assert r["uygulanabilir"] is False and r["uygulanamama_notu"]
    ham = [x for x in store.read_jsonl(skills.SKILL_RECS) if x.get("pending")]
    assert "uygulanabilir" not in ham[-1], "defter satırı KİRLETİLMİŞ — damga yalnız kopyada olmalı"


def test_B2_pano_uygulanabilirligi_YUKTEN_okuyor():
    """DÖRDÜNCÜ KOPYA KALKTI: `RENDER.hermes` eylem adlarını elle saymıyor, sunucunun
    `uygulanabilir` alanını okuyor. Elle sayım geri gelirse aynı ayrışma yeniden mümkün olur."""
    src = (REPO / "meridian" / "web" / "app.js").read_text()
    kod = "\n".join(l for l in src.splitlines() if not l.lstrip().startswith("//"))
    assert "rc.uygulanabilir" in kod, "pano yükteki damgayı okumuyor"
    i = kod.index("const applyable")
    assert "rc.uygulanabilir" in kod[i:i + 200], "applyable hâlâ elle listeden türüyor"


# =================================================================================================
# [C] MAKULLÜK — DAMGALI GÖÇ ARŞİVİ TANINMIŞ TERMİNAL SINIF (yetim DEĞİL, ama ADIYLA SAYILIR)
# =================================================================================================
def _satir(sandbox) -> dict:
    recompute._CORPUS_CACHE.clear()
    return recompute._orphan_state_files()


def _dolu(p: pathlib.Path, n: int = 3) -> None:
    p.write_text(json.dumps({"x": list(range(n))}))          # >4 bayt: boş dosya bulgu değildir


def test_C_damgali_goc_arsivi_YETIM_SAYILMIYOR(sandbox_state):
    """CANLI DOSYANIN BİREBİR ADI. Düzeltme öncesi bu ad `orphans` listesine düşüyor ve makullük
    satırını KIRMIZIYA çekiyordu."""
    _dolu(sandbox_state / "scoreboard.json.migrated-20260812-201359-p192112")
    row = _satir(sandbox_state)
    assert "scoreboard.json.migrated-20260812-201359-p192112" in row["migrasyon_artigi"]
    assert "üretilip tüketilmeyen kanıt" not in (row["detail"] or ""), row["detail"]
    assert row["ok"] is True, row["detail"]


def test_C_ADIYLA_sayiliyor_sessizce_yok_sayilmiyor(sandbox_state):
    """SESSİZ MUAFİYET DEĞİL. `detail` bilerek seçildi: watchdog satırlara yalnız
    `check`/`ok`/`detail` taşıyor, yani operatörün gördüğü TEK metin bu. Sayıyı ek bir
    alana koyup burada susmak "sessizce yok say" ile aynı sonucu verirdi.

    ÇAPA SATIR DEĞİL SEMBOL: burada önce watchdog.py'nin 1075. satırına bir çapa
    yazılıydı; hotstate görünürlük turu o dosyaya satır ekleyince çapa bayatladı ve
    `codelaw` düştü. Aynı ders bu turda ÜÇÜNCÜ kez yaşandı — satır numarası gömen her
    çapa, çapaladığı dosyanın her düzenlemesinde bayatlar."""
    _dolu(sandbox_state / "scoreboard.json.migrated-20260812-201359-p192112")
    d = _satir(sandbox_state)["detail"]
    assert "migrasyon_artigi: 1" in d, d
    assert "scoreboard.json.migrated-20260812-201359-p192112" in d, d
    assert "TAŞIR" in d, "temizlik prosedürü (taşı, silme) satırda yazılı değil"


def test_C_duz_migrated_arsivi_ZATEN_taniniyordu(sandbox_state):
    """Regresyon: düz `.migrated` türetmesi bozulmadı ve o AYRI kalır (geri dönüş HEDEFİ odur —
    `dbmigrate --geri-al` yalnız düz adı asıl adına döndürür)."""
    _dolu(sandbox_state / "scoreboard.json.migrated")
    row = _satir(sandbox_state)
    assert row["ok"] is True and row["migrasyon_artigi"] == []


@pytest.mark.parametrize("ad", [
    "scoreboard.json.migrated-elle",                      # damga biçimi tutmuyor
    "scoreboard.json.migrated-20260812",                  # damga YARIM
    "uydurma_defter.json.migrated-20260812-201359-p1",    # kök `known` DEĞİL
])
def test_C_BEKCI_ZAYIFLATILMADI_uydurma_damga_yetim_kalir(sandbox_state, ad):
    """v204 KURALI: deseni gevşetmek = bekçiyi kör etmek. Tanıma TÜRETİLİR — kök `known` içinde
    OLMAK ZORUNDA ve son ek yazıcının kendi damga biçimine (`%Y%m%d-%H%M%S` + `-p<pid>`) uymak
    ZORUNDA. Üçü de bu kapıdan geçemez ve yetim kalır."""
    _dolu(sandbox_state / ad)
    row = _satir(sandbox_state)
    assert row["ok"] is False and ad in (row["detail"] or ""), row["detail"]
    assert ad not in row["migrasyon_artigi"]


def test_C_yedek_artigi_HALA_yetim(sandbox_state):
    """v204'ün bekçisi bu turda da ayakta: `.bak-` artığı YETİMDİR ve öyle kalmalı (kaynağı
    `dagit.sh`ta onarıldı; dedektör susturulmadı)."""
    (sandbox_state / "goal.yaml.bak-202608021652").write_text("goal: 1\nx: 2\n")
    row = _satir(sandbox_state)
    assert row["ok"] is False and "goal.yaml.bak-202608021652" in (row["detail"] or "")


def test_C_yazici_SILMIYOR_gerekcesi_kaynakta_yazili():
    """HÜKÜM: temizlik KOD tarafında yapılmaz. `store` yasası açık ("hiçbir şey silinmez ve
    üzerine yazılmaz") ve damgalı arşiv, düz `.migrated` DOLUYKEN doğar — yani elde iki kuşak
    arşiv vardır ve damgalıyı silmek, geri dönüşü olmayan tek kopyayı yok etmek olurdu."""
    src = inspect.getsource(recompute._orphan_state_files)
    assert "silinmez" in src and "ops/state_yetim_temizle.sh" in src, \
        "temizlik hükmü ve prosedürü dedektörde gerekçelenmemiş"
    from meridian import store as _st
    assert "hiçbir şey silinmez ve üzerine yazılmaz" in inspect.getsource(_st)
