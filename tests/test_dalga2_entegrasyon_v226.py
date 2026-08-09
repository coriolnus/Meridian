"""test_dalga2_entegrasyon_v226.py — DALGA-2 ENTEGRASYON+GÖSTERİM: üç GÖSTERİM/KALICILIK bacağı.

Dalga-2'nin veri/mantık bacağı (watchdog.liveness_report · api_public_summary tohum/canlı ·
universe unknown) v222-v225'te indi ve `test_dalga2_gozlem_v223` onu ÜRETİM tarafında çiviledi.
Bu dosya o verinin PANO/KALICILIK tarafını çiviler — üçü de "üretildi ama gösterilmiyor/kalıcı
değil" sınıfından:

  SB-1 — PANO BACAĞI KALICILIĞI. `api_alpaca_submit_armed` `mirror_submit_armed`i çağırıp plan
  başına BOYUT MAKBUZU (`meta["size_law"]`, loop.py:592) üretir; ama kalıcılık yaması yalnız
  `alpaca_submitted`/`armed`/`broker_rejected`i yamalıyordu → makbuz restart'ı ATLAYAMIYORDU
  (döngü bacağı `_save_broker`ın 14. anahtarıyla zaten kalıcı; pano bacağının eşdeğeri eksikti —
  08-06 AMGN pano/nabız vakası). Tek satır, `broker_rejected` ile AYNI kilit-altı desen.

  KALEM 3 (PANO) — LIVENESS KARTI. `/api/diagnostics.liveness` çiziliyor değildi. `canlilikBloku`
  onu Öğrenme beslemesi kartına ekler: üç hâl (koştu/koşmadı/ölçülemedi), renk YALNIZ anomalide
  (sev jetonu, yön değil), 'koşuyor' DEMEZ (ÖLÇÜLEMEDİ≠0). Cümle SUNUCUDAN gelir (uydurma yok).

  KALEM 6 (PANO) — TOHUM/CANLI MANŞET. landing manşeti ham `closed_trades`(96) gösteriyordu; 96
  replay TOHUMU dahil, gerçek canlı 1. `olculenSatiri` canlı n + ortalama R'yi ÖNE, tohumu İKİNCİL
  gösterir; $ P&L YOK, sabit sayı YOK (C10) — hepsi uçtan.

TESTLER KAYNAĞA + DAVRANIŞA BAKAR (repo deseni v219/v223/v225): saf üreteçler (`canlilikBloku`,
`olculenSatiri`) Node'da GERÇEKTEN koşturulur; UYGULAMA YÜKLENMEZ (oturum sözleşmesi: statik dilim
+ Node harness). size_law kalıcılığı sandbox'ta uçtan-uca (mock ayna + gerçek `store.update_json`).
"""
from __future__ import annotations

import json
import pathlib
import re
import shutil
import subprocess

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
WEB = REPO / "meridian" / "web"
APPJS = (WEB / "app.js").read_text()
LANDJS = (WEB / "landing.js").read_text()
APIPY = (REPO / "meridian" / "api.py").read_text()
LOOPPY = (REPO / "meridian" / "loop.py").read_text()

NODE = shutil.which("node")


# =================================================================================================
# 0 · DİLİM ÇIKARICI — saf üreteçleri Node'da koşturmak için (v219/v225 `_fn`i)
# =================================================================================================
def _fn(ad: str, kaynak: str = APPJS) -> str:
    for bas in (f"async function {ad}(", f"function {ad}(", f"class {ad} "):
        if bas in kaynak:
            i = kaynak.index(bas)
            parcalar = []
            for ln in kaynak[i:].splitlines(keepends=True):
                parcalar.append(ln)
                if ln.rstrip("\n") == "}":
                    break
            return "".join(parcalar)
    raise AssertionError(f"{ad}: kaynakta tanım bulunamadı")


# =================================================================================================
# 1 · SB-1 — size_law PANO BACAĞI KALICILIĞI (kaynak + uçtan-uca davranış)
# =================================================================================================
def _submit_yamasi() -> str:
    """`api_alpaca_submit_armed` içindeki kilit-altı `_yama` closure'ı."""
    i = APIPY.index("def api_alpaca_submit_armed(")
    j = APIPY.index("def _yama(doc):", i)
    return APIPY[j:APIPY.index("store.update_json(\"portfolio.json\", _yama", j)]


def test_sb1_yama_size_law_yamasi_KAYNAKTA():
    """Yama makbuzu size_law'ı da basar — `broker_rejected` ile AYNI desen (meta öncelikli,
    yoksa diskteki KORUNUR: tam-belge yazımı yasak, yabancı anahtar yaşar)."""
    y = _submit_yamasi()
    assert 'doc["size_law"] = meta.get("size_law", doc.get("size_law", {}))' in y, \
        "pano bacağı size_law makbuzunu yamalamıyor — makbuz restart'ı atlayamaz"
    # broker_rejected deseninin AYNISI (fallback zinciri meta→disk): dar bir `= meta[...]` değil.
    assert 'doc.get("size_law"' in y, "size_law fallback'ı diskteki mevcut makbuzu korumuyor"


def test_sb1_dongu_bacagi_ZATEN_kalici_referans():
    """Bağlam çivisi: döngü bacağı (`_save_broker`) size_law'ı ZATEN 14. anahtar olarak kalıcılar —
    pano bacağı onu tekrarlamıyordu, bu turun kapattığı asimetri buydu."""
    assert '"size_law": meta.get("size_law", {})' in LOOPPY, \
        "döngü bacağının size_law kalıcılığı kayboldu — asimetri iddiası dayanaksız"


def test_sb1_size_law_pano_submitten_sonra_DISKTE(sandbox_state, monkeypatch):
    """UÇTAN UCA: pano `submit_armed` çağrısı sonrası size_law makbuzu portfolio.json'da DİSKTE
    (restart-atlatma). Ayna mock'lanır (broker'a çıkılmaz), `store.update_json` GERÇEKTEN koşar."""
    from meridian import api, health, loop, store
    store.write_json("portfolio.json",
                     {"armed": [{"id": "P-1", "ticker": "AMGN"}], "last_date": "2026-08-09"})
    monkeypatch.setattr(api, "_auth", lambda r: None)
    monkeypatch.setattr(health, "halted", lambda: False)
    monkeypatch.setattr(api, "_diag_onbellek_bosalt", lambda neden: None)

    def _fake_mirror(meta, dstr, source="pano"):
        # mirror_submit_armed'ın YAPTIĞI: meta'yı YERİNDE değiştirir (makbuz + dedup kümesi).
        meta.setdefault("size_law", {})["P-1"] = {
            "eq_kaynak": "alpaca", "eq_now": 100000.0, "peak": 100000.0,
            "size_mult": 0.6, "kitap_rev": "rX"}
        meta["alpaca_submitted"] = ["P-1"]
        return {"ok": True, "submitted": 1, "submitted_ids": ["P-1"], "dropped_ids": [],
                "results": [], "equity": 100000.0, "detail": ""}
    monkeypatch.setattr(loop, "mirror_submit_armed", _fake_mirror)

    api.api_alpaca_submit_armed(None)              # request `_auth`ten sonra kullanılmıyor
    doc = store.read_json("portfolio.json", {})
    assert "size_law" in doc and "P-1" in doc["size_law"], \
        "size_law makbuzu diske yazılmadı — pano bacağı restart'ta makbuzu kaybeder"
    assert doc["size_law"]["P-1"]["size_mult"] == 0.6, "makbuzun içeriği (çarpan) diske taşınmadı"


def test_sb1_yabanci_anahtar_KORUNUR_tam_belge_yazilmaz(sandbox_state, monkeypatch):
    """Yamanın diğer yarısı: kilit-altı yama YABANCI anahtarı (ör. operatör sermaye beyanı) EZMEZ —
    `_save_broker` 2026-08-04 vakasının pano-bacağı ikizi."""
    from meridian import api, health, loop, store
    store.write_json("portfolio.json",
                     {"armed": [{"id": "P-1", "ticker": "AMGN"}], "last_date": "2026-08-09",
                      "sermaye_resetleri": [{"tarih": "2026-08-01", "tutar": 42}]})
    monkeypatch.setattr(api, "_auth", lambda r: None)
    monkeypatch.setattr(health, "halted", lambda: False)
    monkeypatch.setattr(api, "_diag_onbellek_bosalt", lambda neden: None)

    def _fake_mirror(meta, dstr, source="pano"):
        meta.setdefault("size_law", {})["P-1"] = {"size_mult": 1.0}
        return {"ok": True, "submitted": 1, "submitted_ids": ["P-1"], "dropped_ids": [],
                "results": [], "equity": 100000.0}
    monkeypatch.setattr(loop, "mirror_submit_armed", _fake_mirror)

    api.api_alpaca_submit_armed(None)
    doc = store.read_json("portfolio.json", {})
    assert doc.get("sermaye_resetleri") == [{"tarih": "2026-08-01", "tutar": 42}], \
        "kilit-altı yama yabancı anahtarı ezdi — tam-belge yazımı sızmış"
    assert "P-1" in doc.get("size_law", {}), "aynı yamada size_law da yazılmalı"


# =================================================================================================
# 2 · KALEM 3 (PANO) — LIVENESS KARTI: canlilikBloku üç dal (Node)
# =================================================================================================
def test_liveness_karti_sOgr_kartina_BAGLI():
    """`canlilikBloku(d.liveness)` Öğrenme beslemesi kartında GERÇEKTEN çağrılıyor (YASA 6: üretilen
    alanın okuyucusu var). Kadans nabzından SONRA — nabız 'dişli döndü mü', canlılık 'iş yaşıyor mu'."""
    assert "canlilikBloku(d.liveness)" in APPJS, "liveness alanının pano okuyucusu yok (çizilmiyor)"
    i = APPJS.index("Kadans nabzı")
    j = APPJS.index("canlilikBloku(d.liveness)")
    assert i < j, "canlılık bloğu kadans nabzından ÖNCE — pedagojik sıra bozuk (nabız≠canlılık)"


@pytest.fixture(scope="module")
def canlilik_ciktilari():
    if NODE is None:
        pytest.skip("node yok")
    # `_chip` + `esc` saplaması (üretimdeki reçetenin birebiri) — canlilikBloku bu ikisine dayanır.
    stub = ("const esc=s=>String(s==null?'':s)"
            ".replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');\n"
            "function _chip(t,c){return `<span class=\"tag ${c}\">${esc(t)}</span>`;}\n")
    V = {
        # koştu: iki bacak da canlı (sessiz/yeşil)
        "saglikli": {"sprint": {"ok": True, "beyan": "sprint KOŞUYOR (faz=search)"},
                     "learning": {"ok": True, "beyan": "öğrenme ilerliyor — 3 sa önce"}},
        # koşmadı: sprint orphan + öğrenme durdu (anomali)
        "anomali": {"sprint": {"ok": False, "beyan": "sprint 2 gündür KOŞMADI — çocuk ÖLÜ (sanmasın)"},
                    "learning": {"ok": False, "beyan": "öğrenme DURDU — 8 gündür yeni hipotez yok"}},
        # ölçülemedi: probe düştü (beyan 'koşuyor DEMEZ' içerir — bilerek)
        "olculemedi": {"sprint": {"ok": None, "olculemedi": True,
                                  "beyan": "sprint canlılığı ÖLÇÜLEMEDİ (RuntimeError) — 'koşuyor' DEMEZ"},
                       "learning": {"ok": None, "olculemedi": True,
                                    "beyan": "öğrenme yaşı ÖLÇÜLEMEDİ — 'taze' DEMEZ"}},
    }
    betik = (stub + _fn("canlilikBloku") + "\nconst V=" + json.dumps(V, ensure_ascii=False) + ";\n"
             + "const out={};for(const[k,v]of Object.entries(V))out[k]=canlilikBloku(v);\n"
             + "out._bos=canlilikBloku(null);out._yarim=canlilikBloku({sprint:{ok:true,beyan:'x'}});\n"
             + "process.stdout.write(JSON.stringify(out));")
    p = subprocess.run([NODE, "-e", betik], capture_output=True, text=True, timeout=120)
    assert p.returncode == 0, f"canlilikBloku harness Node'da patladı:\n{p.stderr[-3000:]}"
    return json.loads(p.stdout)


def test_liveness_kostu_dali_SESSIZ_yesil(canlilik_ciktilari):
    """Koştu (ok===true) → 'canlı' rozeti t-go (sessiz/yeşil); ANOMALİ rengi (t-no) YOK."""
    c = canlilik_ciktilari["saglikli"]
    assert 't-go">canlı<' in c, "sağlıklı bacak 'canlı' yeşil jetonu basmıyor"
    assert "t-no" not in c, "sağlıklı hâlde anomali rengi (t-no) sızmış — renk yalnız anomalide"
    assert "sprint KOŞUYOR" in c and "öğrenme ilerliyor" in c, "sunucu beyanı çizilmiyor"


def test_liveness_kosmadi_dali_ANOMALI_rengi(canlilik_ciktilari):
    """Koşmadı (ok===false) → anomali jetonu t-no; sprint 'KOŞMADI', öğrenme 'DURDU' (yön DEĞİL, sev)."""
    c = canlilik_ciktilari["anomali"]
    assert 't-no">KOŞMADI<' in c, "sprint orphan anomali jetonu (t-no KOŞMADI) yok"
    assert 't-no">DURDU<' in c, "öğrenme durması anomali jetonu (t-no DURDU) yok"
    # Beyan (N-gün sayısı dahil) SUNUCUDAN gelir — pano sayı UYDURMAZ.
    assert "2 gündür KOŞMADI" in c and "8 gündür yeni hipotez yok" in c, "N-gün beyanı çizilmiyor"


def test_liveness_olculemedi_dali_KOSUYOR_DEMEZ(canlilik_ciktilari):
    """ÖLÇÜLEMEDİ≠0: ok==null → 'ÖLÇÜLEMEDİ' + akromatik t-vi; NE t-go NE t-no (yeşil/kırmızı DEMEZ)."""
    c = canlilik_ciktilari["olculemedi"]
    assert 't-vi">ÖLÇÜLEMEDİ<' in c, "ölçülemedi hâli akromatik ÖLÇÜLEMEDİ jetonu basmıyor"
    assert "t-go" not in c, "ölçülemeyen canlılık YEŞİL boyanmış — 'koşuyor' der gibi"
    assert "t-no" not in c, "ölçülemeyen canlılık KIRMIZI boyanmış — anomali İDDİA ediyor"


def test_liveness_bos_ve_yarim_dal(canlilik_ciktilari):
    """lv yoksa BOŞ döner (kart susar, uydurma satır yok); tek bacak varsa yalnız o çizilir."""
    assert canlilik_ciktilari["_bos"] == "", "liveness yokken boş dönmüyor (hayalet satır)"
    y = canlilik_ciktilari["_yarim"]
    assert "sprint canlılığı" in y and "öğrenme canlılığı" not in y, \
        "eksik bacak için satır uydurulmuş/düşürülmüş"


def test_liveness_CSP_ve_renk_yalniz_anomalide():
    """Satır-içi script/olay özniteliği YOK (CSP-self); blok KENDİ içinde yön-rengi (pos/neg)
    ENJEKTE ETMEZ — renk yalnız sev jetonuyla (t-go/t-no/t-vi) gelir."""
    g = _fn("canlilikBloku")
    assert "<script" not in g and "onclick=" not in g, "canlilikBloku CSP'yi çiğniyor"
    for renk in ('class="neg"', 'class="pos"', "var(--red)", "var(--green)"):
        assert renk not in g, f"canlılık bloğuna yön rengi sızmış (sev değil): {renk}"


# =================================================================================================
# 3 · KALEM 6 (PANO) — TOHUM/CANLI MANŞET: olculenSatiri (Node + kaynak)
# =================================================================================================
def test_manset_olculenSatiri_BAGLI_ve_eski_blok_gitti():
    """landing manşeti artık saf `olculenSatiri(d)`den gelir; eski tek-sayı 'kapanmış işlem' bloğu
    (ham 96) kaldırıldı (aksi halde iki manşet çelişirdi)."""
    assert "rows.push(olculenSatiri(d))" in LANDJS, "manşet üreticisi çağrılmıyor"
    assert "kapanmış işlem <b>" not in LANDJS, "eski ham-toplam manşet satırı hâlâ duruyor"


def test_manset_UYDURMA_RAKAM_yok_hepsi_UCTAN():
    """C10 + landing 'uydurma rakam' geçmişi: manşet üreticisi hiçbir işlem sayısını SABİT yazmaz —
    canlı/tohum/skor/değişken/sürüm hepsi d.*'ten okunur."""
    g = _fn("olculenSatiri", LANDJS)
    for alan in ("d.closed_trades_live", "d.closed_trades_seed", "d.live", "d.score",
                 "d.variables_tried", "d.strategy_version"):
        assert alan in g, f"manşet {alan}'i uçtan okumuyor"
    # Gövdede işlem-sayısı literali OLMAZ: yalnız izinli sabitler (toFixed(2), var(--...)).
    govde = re.sub(r"toFixed\(2\)|var\(--\w+\)", "", g)
    kacak = [n for n in re.findall(r"\b\d{2,}\b", govde)]
    assert not kacak, f"manşette sabit çok-basamaklı sayı (uydurma rakam riski): {kacak}"


@pytest.fixture(scope="module")
def manset_ciktilari():
    if NODE is None:
        pytest.skip("node yok")
    V = {
        # 08-09 canlı fotoğrafı: 96 ham (95 tohum + 1 canlı); manşet '1'i öne almalı, '96'yı DEĞİL.
        "canli_08_09": {"closed_trades": 96, "closed_trades_live": 1, "closed_trades_seed": 95,
                        "live": {"n": 1, "mean_r": -1.5}, "score": 0.1605,
                        "variables_tried": 12, "strategy_version": 220},
        # canlı işlem henüz kapanmadı: n=0, mean_r yok → 'ortalama' GÖSTERİLMEZ (uydurma R yok)
        "canlisiz": {"closed_trades_live": 0, "closed_trades_seed": 95,
                     "live": {"n": 0, "mean_r": None}},
        # uç düştü / eksik alan → em-dash yer tutucu, çökme yok
        "bos": {},
    }
    betik = (_fn("olculenSatiri", LANDJS) + "\nconst V=" + json.dumps(V) + ";\n"
             + "const out={};for(const[k,v]of Object.entries(V))out[k]=olculenSatiri(v);\n"
             + "process.stdout.write(JSON.stringify(out));")
    p = subprocess.run([NODE, "-e", betik], capture_output=True, text=True, timeout=120)
    assert p.returncode == 0, f"olculenSatiri harness Node'da patladı:\n{p.stderr[-3000:]}"
    return json.loads(p.stdout)


def test_manset_canli_ONDE_tohum_IKINCIL(manset_ciktilari):
    """Canlı n + ortalama R ÖNDE; tohum İKİNCİL (mut). Ham toplam 96 manşet SAYISI DEĞİL."""
    c = manset_ciktilari["canli_08_09"]
    assert "canlı işlem <b>1</b>" in c, "gerçek canlı sayı (1) manşette öne çıkmıyor"
    assert "-1.50R" in c, "canlı ortalama R (riske göre getiri) gösterilmiyor"
    assert 'class="mut">tohum (replay) <b>95</b>' in c, "tohum ikincil (mut) olarak ayrılmıyor"
    # YANILTICI HAM TOPLAM manşetin BAŞ sayısı olamaz: '>...<b>96</b>' canlı/tohum olarak görünmez.
    assert "<b>96</b>" not in c, "ham toplam (96) hâlâ manşet sayısı olarak basılıyor — yanıltıcı"


def test_manset_dollar_PnL_SIZMAZ(manset_ciktilari):
    """$ P&L uç sözleşmesi gereği YOK (uç R-multiple taşır, öyle kalsın)."""
    for c in manset_ciktilari.values():
        d = c.lower()
        for sizinti in ("$", "pnl", "kâr", "dolar", "usd", "realized"):
            assert sizinti not in d, f"manşete hesap verisi ($/PnL) sızmış: {sizinti!r} — {c!r}"


def test_manset_canli_yokken_ortalama_UYDURULMAZ(manset_ciktilari):
    """mean_r null (henüz canlı R yok) → 'ortalama' satırı HİÇ çizilmez (0R uydurulmaz); tohum yine
    ayrık; eksik alanlar em-dash."""
    cs = manset_ciktilari["canlisiz"]
    assert "canlı işlem <b>0</b>" in cs and "ortalama" not in cs, \
        "canlı R yokken uydurma ortalama basılıyor"
    bos = manset_ciktilari["bos"]
    assert "—" in bos, "eksik alanlar em-dash yer tutucuya düşmüyor"


# =================================================================================================
# 4 · SÖZLEŞME BÜTÜNLÜĞÜ — yeni ozetSerit/kart YOK + node --check (şerit/ratchet beyanı gerekmedi)
# =================================================================================================
def test_yeni_ozetSerit_seridi_ACILMADI():
    """canlilikBloku srow/_chip diliyle çizer (ozetSerit DEĞİL) → _SERIT_BOLGELERI'ne yeni bir
    şerit BEYAN etmek GEREKMEDİ; ozetSerit çağrı sayısı v207/v219 tabanında (6) kalır."""
    assert APPJS.count("ozetSerit([") == 6, \
        "ozetSerit çağrı sayısı değişti — v191 _SERIT_BOLGELERI beyanı güncellenmeli"


def test_yeni_kart_ACILMADI_ratchet_dokunulmadi():
    """canlılık MEVCUT 'Öğrenme beslemesi' kartına EKLENDİ (yeni katKart DEĞİL) → v198 KART_TABANI
    ratchet'ine dokunmak GEREKMEDİ. `data-kart` sayısı canlilikBloku'ndan etkilenmez."""
    assert "canlilikBloku" in APPJS and 'data-kart="canlilik' not in APPJS, \
        "canlılık bir katKart olarak açılmış — KART_TABANI ratchet'i beyanlı güncellenmeli"


def test_node_check_temiz():
    """Satır-içi script yok + geçerli sözdizimi: app.js VE landing.js (CSP-self + node --check)."""
    if NODE is None:
        pytest.skip("node yok")
    for dosya in ("app.js", "landing.js"):
        p = subprocess.run([NODE, "--check", str(WEB / dosya)], capture_output=True, text=True)
        assert p.returncode == 0, f"node --check {dosya} patladı:\n{p.stderr[-2000:]}"
