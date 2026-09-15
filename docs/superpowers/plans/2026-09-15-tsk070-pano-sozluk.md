# TSK-070 pano bacağı — kanonik durum sözlüğü TÜM ailelere (A8) + Vite panoda yeni yüzey (A2) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `/api/diagnostics.durum_sozlugu.satirlar` bütün aileleri (bekçi 4 · dedektör 8 · canlılık 2 · kadans 17 · kitap damgası · kilit 3 · mandal · hermes ısınma · intraday atlamaları) tek kanonik kelime kümesiyle taşır; Vite panoda yeni "Durum sözlüğü" yüzeyi bu satırları aile başına basar; eski `app.js` dokunulmaz.

**Architecture:** Backend: `meridian/durum_sozlugu.py`ye `PANO_KELIME` (tek kaynak) + aile adaptörleri (`kadans_satirlari`, `kitap_satirlari`, `kilit_satirlari`, `mandal_satirlari`, `hermes_satiri`, `intraday_satirlari`) + `normalize_satir`e `aile`/`kelime`/`n` alanları; `meridian/api.py::_durum_sozlugu` bunları birleştirir; `diagnostics.mandallar` yeni yüzey (obs/watchdog mandal defterlerinden okuma). UI: `ui/src/pano/yuzeyler/sistem/DurumSozlugu.tsx` + `uctipleri.ts` `durum_sozlugu` tipi + `alanlar.ts` durağı; build artefaktları en son.

**Tech Stack:** Python 3.12 (FastAPI `meridian/api.py`), pytest; Vite/React/TS (`ui/`), `npm run build` (tsc + vite + `ops/pano_artefakt_temizle.py`).

**Spec:** `docs/TASARIM-F8-DURUM-SOZLUGU-2026-08-22.md` §4a/§4b + **§9 (2026-09-15 ek — hükümler ve adaptör tablosu)**; keşif raporu scratchpad `kesif_tsk070_pano.md`.

## Global Constraints

- Kelime yalnız backend'de (`PANO_KELIME`); UI ham kelime ÇEVİRMEZ (Task 2 çivisi ham dizgeleri yasaklar). Kelime kümesi tasarım §4b/§9.1 ile birebir (çivi belgeyi dosyadan okur).
- Uydurma yasağı: ölçülemeyen `ok=None` + `olculemedi`/`askida`; sayı `None` → pano "ÖLÇÜLEMEDİ (0 DEĞİL)"; "BOŞTA" üretici ölçmedikçe satır YOK; `devre_kesici` kademe numarası YOK.
- Eski `meridian/web/app.js` DOKUNULMAZ; v261/v271 yeşil kalır. Yeni test numaraları v503/v504 (`ls tests | grep v50[34]` boş; çakışırsa sonraki).
- `/api/diagnostics` 300 sn poll: mandal yüzeyi yalnız dosya okur (`store.read_json`), hesap yapmaz; yanıt boyutu/süresi Task 4'te önce/sonra ölçülür (Bedel yasası).
- UI build EN SON adım (dagit [5c] mtime kapısı; hafıza ui-build-en-son-adim); `ui/src` değişince Task 3'te bir kez build; artefakt hijyeni v478.
- Kod yazan ajan Opus; her görev Sonnet incelemesi; `dosya.py:NNN` çapası yok; `except` işaretli; Yasa 6: her yeni alanın okuyucusu adıyla (pano yüzeyi / v503).

---

### Task 1: Backend — `PANO_KELIME` + aile adaptörleri + `mandallar` yüzeyi + `_durum_sozlugu` genişletme (v503)

**Files:**
- Modify: `meridian/durum_sozlugu.py` (yeni sabitler/fonksiyonlar; `normalize_satir` çıktısına `aile`, `kelime`, `n`)
- Modify: `meridian/api.py` — `_durum_sozlugu(bd, teshis)` imzası genişler (integrity/liveness/watchdog/hud/heartbeat/mlops/intraday gövdesini alır) ve `/api/diagnostics`e `mandallar` alanı
- Test: `tests/test_durum_sozlugu_aileler_v503.py`

**Interfaces:**
- Consumes: `watchdog.report()` `{stale[], never[], askida[], ok, n_ok, total}` + `watchdog.EXPECTED` (17 ad); `integrity_report_cached()`; `liveness_report()` `{sprint, learning}` (her biri `ok`); `bekci_durumlari.kitap_damga.rows[].sinif`; `hud.halted`, `hud.learn_halted`, `heartbeat.breaker_tripped`; `mlops.warmup` (`last_result`, `skip`); `intraday.skipped` (dict); mandal dosyaları `state/alarm_mandal.json`, `watchdog_alarmed.json`, `integrity_alarmed.json` (`store.read_json`, yoksa `None` → ÖLÇÜLEMEDİ).
- Produces: `durum_sozlugu.satirlar[]` = `{aile, kimlik, kelime, ok, olculemedi, kapsam_disi, askida, neden, beyan, kaynak_alan, n}`; `durum_sozlugu.aileler` = aile → satır sayısı; `diagnostics.mandallar`.

- [ ] **Step 1: Kırmızı çiviler (özet — tam dosya implementer'da; her çivi bir davranış)**

```python
"""v503 · Durum sözlüğü TÜM ailelere (TSK-070 A8, tasarım §9.1)."""
import json, pathlib, re
import pytest
from meridian import durum_sozlugu as D
ROOT = pathlib.Path(__file__).resolve().parents[1]
TASARIM = ROOT / "docs/TASARIM-F8-DURUM-SOZLUGU-2026-08-22.md"

def _belge_kelimeleri():
    """§4b + §9.1 tablolarındaki büyük-harfli kanonik kelimeler (tek kaynak = belge)."""
    m = TASARIM.read_text(encoding="utf-8")
    return set(re.findall(r"\b(PENCEREDE|GECİKTİ|HİÇ KOŞMADI|ASKIDA|BASTIRILDI|TEMİZ|İHLAL|ÖLÇÜLEMEDİ|KAPSAM DIŞI|DEDEKTÖR DÜŞTÜ|KOŞUYOR|DURDU \((?:orphan|stall)\)|DEĞİŞİM YOK|DAMGALI DEĞİŞİM|İÇERİK-AYNI YENİDEN YAZIM|DAMGASIZ YAZIM|İLK GÖZLEM|KAPALI|ÇEKİLİ|İLK ALARM|MANDALLI|YENİDEN|DÜŞTÜ|SEANS DIŞI|PENCERE ÖNCESİ|HALT|BAYAT|BAR YOK)\b", m))

def test_a_pano_kelime_kumesi_belgeyle_birebir():
    assert set(D.PANO_KELIME.values()) == _belge_kelimeleri()

def test_b_kadans_17_satir_expected_ile_birebir(sandbox_state):
    from meridian import watchdog as W
    rapor = {"stale": ["cf_advance"], "never": ["y4_collect"], "askida": ["shadow_fit"], "ok": None, "n_ok": 14, "total": 17}
    s = D.kadans_satirlari(rapor, W.EXPECTED)
    assert len(s) == 17 and {x["kimlik"] for x in s} == set(W.EXPECTED)
    k = {x["kimlik"]: x for x in s}
    assert k["cf_advance"]["kelime"] == "GECİKTİ" and k["cf_advance"]["ok"] is False
    assert k["y4_collect"]["kelime"] == "HİÇ KOŞMADI" and k["shadow_fit"]["kelime"] == "ASKIDA" and k["shadow_fit"]["ok"] is None and k["shadow_fit"]["askida"] is True
    assert k["scheduler_poll"]["kelime"] == "PENCEREDE" and k["scheduler_poll"]["ok"] is True
    assert all(x["aile"] == "kadans" for x in s)

def test_c_kilit_ters_isaret_ve_devre_kesici_kademesiz():
    s = {x["kimlik"]: x for x in D.kilit_satirlari({"halted": False, "learn_halted": True}, {"breaker_tripped": None})}
    assert s["soft_halt"]["kelime"] == "KAPALI" and s["soft_halt"]["ok"] is True
    assert s["halt_learning"]["kelime"] == "ÇEKİLİ" and s["halt_learning"]["ok"] is False and "Kademe 4" in s["halt_learning"]["beyan"]
    assert s["devre_kesici"]["kelime"] == "ÖLÇÜLEMEDİ" and s["devre_kesici"]["ok"] is None and "Kademe" not in s["devre_kesici"]["beyan"]

def test_d_canlilik_bosta_uretilmez_ve_orphan_stall():
    s = {x["kimlik"]: x for x in D.canlilik_satirlari({"sprint": {"ok": False, "beyan": "x"}, "learning": {"ok": True, "beyan": "y"}})}
    assert s["sprint"]["kelime"] == "DURDU (orphan)" and s["learning"]["kelime"] == "KOŞUYOR"
    assert "BOŞTA" not in {x["kelime"] for x in s.values()}

def test_e_intraday_null_olculemedi_sifir_degil():
    s = {x["kimlik"]: x for x in D.intraday_satirlari({"session": 3, "pencere": None})}
    assert s["session"]["kelime"] == "SEANS DIŞI" and s["session"]["n"] == 3
    assert s["pencere"]["kelime"] == "ÖLÇÜLEMEDİ" and s["pencere"]["n"] is None and s["pencere"]["olculemedi"] is True

def test_f_mandal_yuzeyi_dosyadan_ve_yoksa_olculemedi(sandbox_state):
    m = D.mandal_yuzeyi()   # store.read_json ile; sandbox'ta dosya yok
    assert m["alarm_mandal"] is None and m["watchdog_alarmed"] is None
    s = D.mandal_satirlari(m)
    assert all(x["kelime"] == "ÖLÇÜLEMEDİ" and x["ok"] is None for x in s)

def test_g_hermes_isinma_skip_neden_ailesinde():
    s = D.hermes_satiri({"last_result": "halt_learning", "skip": "lock_busy"})
    assert s["kelime"] == "ASKIDA" and s["neden"] == "isinma:lock_busy" and s["ok"] is None
    assert D.hermes_satiri({"last_result": "error: RuntimeError", "skip": None})["kelime"] == "İHLAL"

def test_h_api_durum_sozlugu_tum_aileleri_tasir(sandbox_state, monkeypatch):
    from meridian import api
    # `_durum_sozlugu(bd, teshis)` — teshis sahte gövde; satır aile sayımı tasarım §9.1 ile
    ...  # implementer: dört bekçi + 8 dedektör + 2 canlılık + 17 kadans + kitap + 3 kilit + mandal(≥3) + hermes(1) + intraday(5) → aileler sayımı
```

- [ ] **Step 2: Kırmızıyı gör** — `.venv/bin/python -m pytest tests/test_durum_sozlugu_aileler_v503.py -p no:cacheprovider` → AttributeError/FAILED.

- [ ] **Step 3: `durum_sozlugu.py` — `PANO_KELIME` + adaptörler** (isimler testteki gibi; her fonksiyon docstring'inde Yasa-6 okuyucusu: `api._durum_sozlugu` → pano `DurumSozlugu.tsx`)

```python
PANO_KELIME = {  # TEK KAYNAK — tasarım §4b + §9.1; v503 test_a belgeyle birebir çiviler
    "kadans:ok": "PENCEREDE", "kadans:stale": "GECİKTİ", "kadans:never": "HİÇ KOŞMADI", "kadans:askida": "ASKIDA", "kadans:bastirildi": "BASTIRILDI",
    "dedektor:ok": "TEMİZ", "dedektor:ihlal": "İHLAL", "dedektor:olculemedi": "ÖLÇÜLEMEDİ", "dedektor:kapsam_disi": "KAPSAM DIŞI", "dedektor:dustu": "DEDEKTÖR DÜŞTÜ",
    "canlilik:ok": "KOŞUYOR", "canlilik:orphan": "DURDU (orphan)", "canlilik:stall": "DURDU (stall)",
    "kitap:degisim_yok": "DEĞİŞİM YOK", "kitap:damgali_degisim": "DAMGALI DEĞİŞİM", "kitap:damga_ilerledi_icerik_ayni": "İÇERİK-AYNI YENİDEN YAZIM",
    "kitap:damgasiz_yazim": "DAMGASIZ YAZIM", "kitap:taban_yok": "İLK GÖZLEM", "kilit:kapali": "KAPALI", "kilit:cekili": "ÇEKİLİ",
    "mandal:ilk": "İLK ALARM", "mandal:mandalli": "MANDALLI", "mandal:yeniden": "YENİDEN", "mandal:dustu": "DÜŞTÜ",
    "intraday:session": "SEANS DIŞI", "intraday:pencere": "PENCERE ÖNCESİ", "intraday:halt": "HALT", "intraday:stale": "BAYAT", "intraday:no_bars": "BAR YOK",
}
KILIT_BEYAN = {"soft_halt": "Kademe 1 · Soft Halt", "halt_learning": "Kademe 4 · Öğrenme durdurma", "devre_kesici": "Devre kesici (kademe ölçülmedi)"}

def _satir(aile, kimlik, kelime, ok, *, neden=None, beyan="", kaynak_alan="", n=None, olculemedi=False, kapsam_disi=False, askida=False) -> dict:
    return {"aile": aile, "kimlik": kimlik, "kelime": kelime, "ok": ok, "olculemedi": olculemedi, "kapsam_disi": kapsam_disi,
            "askida": askida, "neden": neden, "beyan": beyan, "kaynak_alan": kaynak_alan, "n": n}

def kadans_satirlari(rapor: dict, expected) -> list[dict]:
    stale, never, askida = set(rapor.get("stale") or []), set(rapor.get("never") or []), set(rapor.get("askida") or [])
    out = []
    for ad in sorted(expected):
        if ad in never:    out.append(_satir("kadans", ad, PANO_KELIME["kadans:never"], False, kaynak_alan="watchdog.never"))
        elif ad in stale:  out.append(_satir("kadans", ad, PANO_KELIME["kadans:stale"], False, kaynak_alan="watchdog.stale"))
        elif ad in askida: out.append(_satir("kadans", ad, PANO_KELIME["kadans:askida"], None, askida=True, kaynak_alan="watchdog.askida"))
        else:              out.append(_satir("kadans", ad, PANO_KELIME["kadans:ok"], True, kaynak_alan="watchdog.n_ok"))
    return out
# kilit_satirlari / canlilik_satirlari / kitap_satirlari / mandal_yuzeyi / mandal_satirlari / hermes_satiri / intraday_satirlari — §9.1 tablosu birebir;
# dedektör ailesi mevcut normalize_satir(kimlik, rapor) + aile="dedektor" + kelime türetimi (ok→TEMİZ, False→İHLAL, None→olculemedi/kapsam_disi/dustu ayrımı).
```

- [ ] **Step 4: `api.py`** — `_durum_sozlugu(bd, teshis)`: `satirlar = bekçi(4) + dedektör(integrity) + canlılık(liveness) + kadans(watchdog) + kitap(rows) + kilit(hud, heartbeat) + mandal(mandallar) + hermes(mlops.warmup) + intraday(skipped)`; `aileler` sayımı; `/api/diagnostics`e `mandallar = durum_sozlugu.mandal_yuzeyi()` (Yasa-6 okuyucu: `_durum_sozlugu` + pano). Mevcut `beyan`/`pencere`/`sayac_rejimi` alanları AYNEN.

- [ ] **Step 5: Yeşili gör + kapsam** — `tests/test_durum_sozlugu_aileler_v503.py tests/test_f8_durum_sozlugu_v271.py tests/test_f8_sayac_kalici_v499.py tests/test_yasa6_dort_rapor_v261.py tests/test_codelaw_v59.py tests/test_codelaw_kor_nokta_v214.py tests/test_e_partisi_v278.py tests/test_kucuk_paket_v275.py tests/test_bayat_bytecode_v334.py tests/test_kovab_dilim_v382.py tests/test_tests_ops_satir_capasi_v401.py tests/test_yorum_sembol_capasi_v402.py tests/test_review_backlog_v98.py`. Mutasyon: `PANO_KELIME`den bir kelimeyi değiştir → test_a kırmızı; kadans adaptöründe stale/never sırasını değiştir → test_b; devre_kesici beyanına "Kademe 3" yaz → test_c.

- [ ] **Step 6: Commit (Rol-1).**

---

### Task 2: Vite pano — `durum_sozlugu` tipi + `DurumSozlugu.tsx` yüzeyi + durak (v504)

**Files:**
- Modify: `ui/src/pano/yuzeyler/sistem/uctipleri.ts` (`TeshisGovdesi.durum_sozlugu?: DurumSozluguGovdesi` — `satirlar[]`, `aileler`, `esanlamli_okumalar`, `pencere`, `sayac_rejimi`, `beyan`)
- Create: `ui/src/pano/yuzeyler/sistem/DurumSozlugu.tsx`
- Modify: `ui/src/pano/alanlar.ts` (sistem alanına "Durum sözlüğü" durağı; mevcut durak kayıt desenini birebir izle) ve gerekiyorsa yüzey yönlendiricisi (Operasyon'un kayıtlı olduğu dosya)
- Test: `tests/test_pano_durum_sozlugu_v504.py` (kaynak-grep + tip sözleşmesi; Node/vitest KOŞMAZ)

**Interfaces:** Consumes Task 1 `satirlar[]` şeması. Produces: `/`'de "Durum sözlüğü" durağı.

- [ ] **Step 1: Kırmızı çiviler** (tsx dosyası yok → FAILED)

```python
"""v504 · Vite panoda Durum sözlüğü yüzeyi (TSK-070 A2/A8, tasarım §9.2) — kaynak-grep + tip sözleşmesi."""
import pathlib, re
ROOT = pathlib.Path(__file__).resolve().parents[1]
UI = ROOT / "ui/src/pano"
TSX = UI / "yuzeyler/sistem/DurumSozlugu.tsx"
HAM = ["stale", "never", "learning_halted", "damga_ilerledi_icerik_ayni", "no_bars", "lock_busy", "bg_reflect"]

def test_a_yuzey_var_ve_satirlar_kelime_basar():
    m = TSX.read_text(encoding="utf-8")
    assert "durum_sozlugu" in m and ".satirlar" in m and ".kelime" in m and ".aile" in m and ".beyan" in m

def test_b_ui_ham_kelime_cevirmez():
    m = TSX.read_text(encoding="utf-8")
    for h in HAM:
        assert f'"{h}"' not in m and f"'{h}'" not in m, f"ham kelime UI'da çevriliyor: {h} (kelime backend'de, tek kaynak)"

def test_c_olculemedi_sifir_degil_kalibi():
    assert "ÖLÇÜLEMEDİ (0 DEĞİL)" in TSX.read_text(encoding="utf-8")

def test_d_tip_sozlesmesi_ve_durak():
    t = (UI / "yuzeyler/sistem/uctipleri.ts").read_text(encoding="utf-8")
    assert re.search(r"durum_sozlugu\??:\s*DurumSozluguGovdesi", t) and "satirlar:" in t and "kelime:" in t
    a = (UI / "alanlar.ts").read_text(encoding="utf-8")
    assert "Durum sözlüğü" in a and "DurumSozlugu" in a

def test_e_eski_appjs_dokunulmadi():
    m = (ROOT / "meridian/web/app.js").read_text(encoding="utf-8")
    assert "f8SozlukSatiri" in m and "bekciDurumlari" in m  # eski kart yerinde (ikincil UI)
```

- [ ] **Step 2: Kırmızıyı gör.**
- [ ] **Step 3: Tip + yüzey.** `DurumSozlugu.tsx`: `/api/diagnostics` verisini mevcut sistem yüzeylerinin okuduğu hook/kaynakla al (Operasyon.tsx'in deseni); `satirlar`ı `aile`ye göre grupla (sıra: kadans · dedektör · canlılık · bekçi · kitap · kilit · mandal · hermes · intraday); satır: rozet (`kelime`; renk rolü `ok`: true→nötr, false→şiddet, null→bilgi — jetonlar.css rolleri, ham hex yok) + `kimlik` + `beyan` (+ `n` varsa; `n === null` → "ÖLÇÜLEMEDİ (0 DEĞİL)"); altta eşanlamlı-okuma sayaçları + `pencere` (ilk/son kayıt, gün) + `sayac_rejimi`. Boş gövde (`durum_sozlugu` yok) → "ölçülemedi" durumu, uydurma yok.
- [ ] **Step 4: `npx tsc -b` (ui/) yeşil** — tip hataları yok. Build YAPMA (Task 3).
- [ ] **Step 5: Yeşili gör** — `tests/test_pano_durum_sozlugu_v504.py tests/test_kok_cevrimi_v298.py tests/test_uiux_s1b_v154.py tests/test_kovab_dilim_v382.py tests/test_tests_ops_satir_capasi_v401.py tests/test_yorum_sembol_capasi_v402.py`. Mutasyon: tsx'e `"stale"` sabiti ekle → test_b kırmızı.
- [ ] **Step 6: Commit (Rol-1).**

---

### Task 3: UI build + artefakt hijyeni (Rol-1; EN SON adım)

- [ ] `cd ui && npm run build` (tsc + vite + `ops/pano_artefakt_temizle.py --uygula`) → `meridian/web/pano.html` + `pano-assets/pano-*.js/css` + `manifest.json` yenilenir.
- [ ] `tests/test_pano_artefakt_temizlik_v478.py` + `tests/test_kok_cevrimi_v298.py` yeşil; `git status` yalnız üretilen artefaktlar.
- [ ] Commit: "Pano UI build: TSK-070 durum sözlüğü yüzeyi artefaktları" (yalnız artefakt yolları). Build'den sonra `ui/src`e DOKUNMA (dagit [5c]).

---

### Task 4: Dağıtım + kanıt + bedel ölçümü (Rol-1)

- [ ] Tam suite (motor `api.py` + `durum_sozlugu.py`) → push → `dagit.sh --dry-run` ([5c] geçer) → `--uygula`.
- [ ] Kanıt A1: `/api/diagnostics.durum_sozlugu.aileler` sayımı (kadans 17 · dedektör 8 · canlılık 2 · bekçi 4 · kilit 3 · mandal ≥3 · hermes 1 · intraday 5 · kitap n); pano `/`'de "Durum sözlüğü" durağı ekran görüntüsü (tarayıcı ile); `mandallar` alanı dolu.
- [ ] Bedel: `/api/diagnostics` yanıt boyutu ve süresi önce/sonra (A1 curl `-w %{size_download} %{time_total}`), günlük + ROADMAP TSK-070 notu; eşanlamlı sayaç penceresi devam.
- [ ] ROADMAP TSK-070: pano bacağı canlı; kalan: eski `app.js` F8 kartı emekliliği (ayrı kalem, EDG-089 penceresi sonrası).

## Self-review (2026-09-15)
- Spec: §9.1'in dokuz ailesi Task 1'de; §9.2 yüzey Task 2; §9.3 çiviler v503/v504; §9.4 bedel Task 4.
- Yer tutucu: Task 1 Step 1 test_h gövdesi implementer'a bırakıldı (`...`) — kasıtlı: sahte teşhis gövdesi Task 1 Step 4'teki imzaya bağlı; implementer test_h'yi `_durum_sozlugu(bd, teshis)` imzasıyla tamamlar (gereksinim: aile sayımı §9.1 tablosu). Diğer adımlarda yer tutucu yok.
- Tutarlılık: `_satir` alan adları Task 1/2 arasında aynı (`aile, kimlik, kelime, ok, olculemedi, kapsam_disi, askida, neden, beyan, kaynak_alan, n`).
