# Palet Turu (TSK-117) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Pano renklerini rol jetonlarına bağlamak: rezerve hue bantları dışında kalan seri rampası, anlam jetonları (`--basari/--uyari/--kritik/--bilgi`) ve 416 literal Tailwind renk sınıfının aile başına göçü; gece yön-eksi/kritik çakışması kapanır; renk körlüğü ölçülür.

**Architecture:** Tek kaynak `meridian/web/tokens.json` → `ops/jeton_css_uret.py` → `ui/src/jetonlar.css`; pano bugün bu dosyayı YÜKLEMİYOR (Huni.tsx şerhi "o dosya bu uygulamaya bağlı değil") — Görev 1 köprüyü kurar (generator `.dark` seçicisi + `tema.css` import + `@theme inline` anlam eşlemesi). Sonraki görevler literal sınıfları utility jetonlarına (`bg-uyari-t`, `text-basari`) çevirir; seri rampası serbest hue'lara taşınır; huni jetonları seriye bağlanır; DUGUM_STILI istisnası kapanır. Her görev kendi çivisi + mutasyonu + `npm run build` EN SON adımıyla biter.

**Tech Stack:** Vite + React 19 + Tailwind v4 (`@theme inline`), Python 3.12 pytest çivileri (`tests/`), `ops/jeton_css_uret.py` (DTCG tokens.json → CSS), colorsys (hue ölçümü).

**Spec:** `docs/TASARIM-PALET-REZERVE-HUE-2026-09-03.md` (S1=A′ · S2 huni seriye · S3 195° BİLGİ rezerve · S4 renk körlüğü bu turda · S5 dört dilim).

## Global Constraints

- Rezerve bantlar (spec §2): KRİTİK 336°–6° · UYARI+YÖN-EKSİ 8°–30° · BAŞARI+YÖN-ARTI 132°–155° · BİLGİ 185°–210° · GEZİNME 210°–232° · MOD 245°–270°. Serbest: 32°–130° · 156°–184° · 234°–244° · 272°–334°.
- Tek kaynak: rol renkleri yalnız `meridian/web/tokens.json`; `ui/src/jetonlar.css` ÜRETİLİR (`python ops/jeton_css_uret.py`), elle düzenlenmez; `tests/test_jeton_birligi_v208.py` ayrışmayı yakalar.
- Literal sınıf sayımı (aile başına) yalnız DÜŞER; her dilim raporda önce/sonra sayısıyla (bedel yasası).
- Ekran değişir (renk göçü bir DEĞİŞİKLİKTİR: emerald-500 ≈160° → sev-3 145°); her dilim sonunda Rol-1 Browser panelinde görsel tur, operatör hükmü.
- `dosya.py:SATIR` çapası yasak (şerhte bile); şerhler künyeli `TSK-117, 2026-09-03`; sessiz-yutma yok; uydurma yok.
- `npm run build` her görevin SON adımı (mtime kapısı [5c]); bundle hash değişir, `pano.html` + `manifest.json` vite yazar; eski bundle'ı ajan SİLMEZ (Rol-1 `git rm`).
- pytest her zaman `.venv/bin/python -m pytest <dosyalar>` SERİ; git komutu ajanlarda YOK (commit adımları Rol-1'indir).
- Yeni test numaraları: v395'ten başlar (`ls tests | grep -oE "v[0-9]{3}" | sort | tail -1` ile her görevde yeniden ölç).

---

### Task 1: Köprü — jetonlar.css panoya bağlanır, anlam jetonları `@theme inline`'da

**Files:**
- Modify: `ops/jeton_css_uret.py` (`uret` — gece bloğu seçicisi)
- Modify: `ui/src/tema.css` (`@import` + `@theme inline` anlam eşlemesi)
- Modify: `meridian/web/tokens.json` (rol/anlam katmanı: dört alias)
- Test: `tests/test_anlam_jetonlari_v395.py`

**Interfaces:**
- Consumes: `tokens.json` rol jetonları `--sev-1/--sev-2/--sev-3` (+`-h`, `-t`), `--sky` (195° ailesi).
- Produces: CSS değişkenleri `--basari`, `--basari-h`, `--basari-t`, `--uyari(-h,-t)`, `--kritik(-h,-t)`, `--bilgi(-h,-t)` (jetonlar.css, alias ile) ve Tailwind utility'leri `bg-basari`, `bg-basari-t`, `text-basari`, `border-basari-h` … (`@theme inline`: `--color-basari: var(--basari)` vb.). Sonraki görevler YALNIZ bu adları kullanır.

- [ ] **Step 1: Kırmızı çivi — pano jetonlar.css'i yüklemiyor ve anlam jetonu yok**

```python
# tests/test_anlam_jetonlari_v395.py
"""v395 — TSK-117 Görev 1: köprü. Pano (ui/src) rol jetonlarını YÜKLER ve dört anlam jetonu
tek kaynaktan (tokens.json alias) türer. (TSK-117, 2026-09-03)"""
import json, pathlib, re
from meridian import config

UI = pathlib.Path(config.ROOT) / "ui" / "src"
TEMA = UI / "tema.css"
JETON = UI / "jetonlar.css"
TOKENS = pathlib.Path(config.ROOT) / "meridian" / "web" / "tokens.json"
ANLAM = ("basari", "uyari", "kritik", "bilgi")
KAYNAK = {"basari": "sev-3", "uyari": "sev-2", "kritik": "sev-1", "bilgi": "sky"}

def test_tema_jetonlar_css_i_import_eder():
    assert re.search(r'@import\s+"\.\./jetonlar\.css"', TEMA.read_text(encoding="utf-8")), \
        "pano rol jetonlarını yüklemiyor — Huni.tsx şerhindeki 'bağlı değil' hâli sürüyor"

def test_anlam_jetonlari_tokens_jsonda_ALIAS_olarak_var():
    d = json.loads(TOKENS.read_text(encoding="utf-8"))
    anlam = d["rol"]["gunduz"].get("anlam") or {}
    for ad in ANLAM:
        v = anlam[ad]["$value"]
        assert v == "{rol.gunduz.%s.%s}" % ("siddet" if ad != "bilgi" else "renk", KAYNAK[ad]) or v.startswith("{"), \
            f"{ad}: değer alias DEĞİL ({v}) — kopya hue tek-kaynak yasasını kırar"

def test_jetonlar_css_anlam_degiskenlerini_var_ile_bagliyor():
    css = JETON.read_text(encoding="utf-8")
    for ad in ANLAM:
        m = re.search(rf"--{ad}:\s*var\(--([a-z0-9-]+)\)", css)
        assert m and m.group(1) == KAYNAK[ad], f"--{ad} → var(--{KAYNAK[ad]}) bekleniyordu"

def test_theme_inline_utility_eslemesi():
    tema = TEMA.read_text(encoding="utf-8")
    for ad in ANLAM:
        assert re.search(rf"--color-{ad}:\s*var\(--{ad}\)", tema), f"--color-{ad} eşlemesi yok (utility doğmaz)"
        assert re.search(rf"--color-{ad}-t:\s*var\(--{ad}-t\)", tema), f"--color-{ad}-t eşlemesi yok"

def test_gece_blogu_pano_dark_sinifini_da_kapsar():
    css = JETON.read_text(encoding="utf-8")
    assert re.search(r"^\[data-theme=\"dark\"\],\s*\.dark\s*\{", css, re.M), \
        "gece bloğu yalnız [data-theme=dark] — pano .dark sınıfıyla anahtarlıyor, gece jetonları panoda ölü kalır"
```

- [ ] **Step 2: Kırmızıyı gör**

Run: `.venv/bin/python -m pytest tests/test_anlam_jetonlari_v395.py`
Expected: 5 FAILED (import yok; anlam katmanı yok; değişken yok; eşleme yok; `.dark` yok).

- [ ] **Step 3: tokens.json'a anlam katmanı (alias) — gündüz VE gece**

`meridian/web/tokens.json` içinde `rol.gunduz` ve `rol.gece` altına `anlam` grubu (DTCG alias; üretici `{a.b.c}` → `var(--c)` çevirir — `ops/jeton_css_uret.py::_css_degeri`):

```json
"anlam": {
  "$description": "ANLAM JETONLARI (TSK-117, 2026-09-03): yüzeyler hue adıyla değil İŞ adıyla bağlanır; her biri bir rol jetonunun ALIAS'ıdır, yeni renk YOK.",
  "basari":   {"$value": "{rol.gunduz.siddet.sev-3}",   "$description": "başarı/nominal = P3", "$extensions": {"org.meridian.css": {"var": "--basari",   "tema": "gunduz"}}},
  "basari-h": {"$value": "{rol.gunduz.siddet.sev-3-h}", "$extensions": {"org.meridian.css": {"var": "--basari-h", "tema": "gunduz"}}},
  "basari-t": {"$value": "{rol.gunduz.siddet.sev-3-t}", "$extensions": {"org.meridian.css": {"var": "--basari-t", "tema": "gunduz"}}},
  "uyari":    {"$value": "{rol.gunduz.siddet.sev-2}",   "$extensions": {"org.meridian.css": {"var": "--uyari",    "tema": "gunduz"}}},
  "uyari-h":  {"$value": "{rol.gunduz.siddet.sev-2-h}", "$extensions": {"org.meridian.css": {"var": "--uyari-h",  "tema": "gunduz"}}},
  "uyari-t":  {"$value": "{rol.gunduz.siddet.sev-2-t}", "$extensions": {"org.meridian.css": {"var": "--uyari-t",  "tema": "gunduz"}}},
  "kritik":   {"$value": "{rol.gunduz.siddet.sev-1}",   "$extensions": {"org.meridian.css": {"var": "--kritik",   "tema": "gunduz"}}},
  "kritik-h": {"$value": "{rol.gunduz.siddet.sev-1-h}", "$extensions": {"org.meridian.css": {"var": "--kritik-h", "tema": "gunduz"}}},
  "kritik-t": {"$value": "{rol.gunduz.siddet.sev-1-t}", "$extensions": {"org.meridian.css": {"var": "--kritik-t", "tema": "gunduz"}}},
  "bilgi":    {"$value": "{tema.gunduz.renk.sky}",      "$description": "BİLGİ rolü (S3 2026-09-03): 195° ailesi rezerve", "$extensions": {"org.meridian.css": {"var": "--bilgi", "tema": "gunduz"}}}
}
```

`sky`'ın tokens.json'daki gerçek yolunu ÖLÇ (`python - <<EOF` ile `d` içinde `"sky"` anahtarını ara) ve alias'ı o yola yaz; `bilgi-h`/`bilgi-t` için kaynak yoksa `sky` üzerinden `rgba(...,.35)`/`.10` DEĞERLİ iki yeni jeton tanımla ve `$description`a "sky'dan türetilmiş saç teli/tint; tek kaynak sky" yaz (sıcaklık: `sev-*-h/-t` emsali %35/%10). Gece için aynı grubu `rol.gece.anlam` altında `tema: "gece"` ile TEKRARLA (alias hedefleri gece jetonları).

- [ ] **Step 4: Üreticiye `.dark` seçicisi**

`ops/jeton_css_uret.py::uret` içinde gece bloğu:

```python
    # TSK-117 (2026-09-03): pano (ui/src) temayı `.dark` sınıfıyla anahtarlar (shadcn); eski yüzeyler
    # `[data-theme="dark"]` ile. İki seçici, TEK blok — değer takımı ayrışamaz (v208 ruhu).
    gece = blok('[data-theme="dark"], .dark', kova["gece"])
```

(Eski `:root:not([data-theme='light'])` bloğu varsa aynen kalır — ölç ve raporda yaz; iki gece bloğu aynı değerleri taşır.) Sonra: `.venv/bin/python ops/jeton_css_uret.py` → `ui/src/jetonlar.css` yeniden üretilir.

- [ ] **Step 5: tema.css import + `@theme inline` eşlemesi**

`ui/src/tema.css` başına (Tailwind import'undan SONRA):

```css
@import "../jetonlar.css"; /* TSK-117, 2026-09-03: rol jetonları panoya bağlandı (tokens.json tek kaynak) */
```

`@theme inline` bloğuna:

```css
  /* ANLAM JETONLARI (TSK-117, 2026-09-03) — utility: bg-basari, bg-basari-t, text-uyari, border-kritik-h, text-bilgi … */
  --color-basari: var(--basari);   --color-basari-h: var(--basari-h);   --color-basari-t: var(--basari-t);
  --color-uyari: var(--uyari);     --color-uyari-h: var(--uyari-h);     --color-uyari-t: var(--uyari-t);
  --color-kritik: var(--kritik);   --color-kritik-h: var(--kritik-h);   --color-kritik-t: var(--kritik-t);
  --color-bilgi: var(--bilgi);     --color-bilgi-h: var(--bilgi-h);     --color-bilgi-t: var(--bilgi-t);
```

- [ ] **Step 6: Yeşili gör + mevcut çiviler**

Run: `.venv/bin/python -m pytest tests/test_anlam_jetonlari_v395.py tests/test_jeton_birligi_v208.py tests/test_renk_rolleri_v197.py tests/test_ui_pilot_kapilari_v286.py`
Expected: PASS (v208 jetonlar.css ↔ tokens.json senkron; v197 rol sızıntısı yok).

- [ ] **Step 7: Mutasyon**

`--color-basari` satırını sil → `test_theme_inline_utility_eslemesi` ötmeli; alias'ı hex'e çevir → `test_anlam_jetonlari_tokens_jsonda_ALIAS_olarak_var` ötmeli; geri al.

- [ ] **Step 8: Build EN SON**

Run: `cd ui && npm run kontrol && npm run build` — bundle + CSS hash değişir (jetonlar.css artık bundle'da). `date -u` damgası raporda.

- [ ] **Step 9: Commit (Rol-1)**

```bash
git add ops/jeton_css_uret.py meridian/web/tokens.json ui/src/jetonlar.css ui/src/tema.css tests/test_anlam_jetonlari_v395.py meridian/web/pano.html meridian/web/pano-assets/manifest.json meridian/web/pano-assets/pano-<yeni>.js meridian/web/pano-assets/pano-<yeni>.css
git commit -m "TSK-117 G1: jetonlar.css panoya bağlandı (.dark seçicisi), anlam jetonları alias (basari/uyari/kritik/bilgi) + @theme utility'leri; v395"
```

---

### Task 2: K-0 — gece yön-eksi ile gece kritik aynı renk (0°/1°, l74)

**Files:**
- Modify: `meridian/web/tokens.json` (`rol.gece.yon.yon-eksi`, `-h`, `-t`)
- Regenerate: `ui/src/jetonlar.css`
- Test: `tests/test_gece_rol_hue_ayrimi_v396.py`

**Interfaces:**
- Consumes: gündüz `yon-eksi` #b43c0b (hue 17°), gece `sev-1` #ff7e7c (1°).
- Produces: gece `--yon-eksi` yeni değeri (hue 17° ± 3°, l≈70%), aynı hue'dan `-h` (.35) ve `-t` (.10).

- [ ] **Step 1: Kırmızı çivi — gece rol jetonları ikili hue farkı ≥ 8°**

```python
# tests/test_gece_rol_hue_ayrimi_v396.py
"""v396 — TSK-117 K-0: gece rol jetonları arasında hue çakışması yok (yön-eksi 0° ↔ kritik 1° vakası).
Hue hesabı testin İÇİNDE (colorsys) — sabit tablo yazılmaz. (TSK-117, 2026-09-03)"""
import colorsys, json, pathlib, re
from meridian import config

TOKENS = pathlib.Path(config.ROOT) / "meridian" / "web" / "tokens.json"
MIN_FARK = 8.0   # derece; spec §4 K-0

def _hue(hexstr):
    r, g, b = (int(hexstr[i:i+2], 16) / 255 for i in (1, 3, 5))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return h * 360, s, l

def _rol_kromatik(tema):
    d = json.loads(TOKENS.read_text(encoding="utf-8"))["rol"][tema]
    out = {}
    for grup in ("siddet", "yon", "mod", "nav"):
        for ad, j in d.get(grup, {}).items():
            if ad.startswith("$"): continue
            v = j.get("$value") if isinstance(j, dict) else None
            if isinstance(v, str) and re.fullmatch(r"#[0-9a-fA-F]{6}", v):
                h, s, l = _hue(v)
                if s >= 0.12: out[f"{grup}/{ad}"] = h
    return out

def _dairesel(a, b):
    d = abs(a - b) % 360
    return min(d, 360 - d)

def test_gece_yon_eksi_ile_kritik_ayri_hue():
    h = _rol_kromatik("gece")
    assert _dairesel(h["yon/yon-eksi"], h["siddet/sev-1"]) >= MIN_FARK, \
        f"gece yön-eksi {h['yon/yon-eksi']:.0f}° ≈ kritik {h['siddet/sev-1']:.0f}° — negatif K/Z ile P1 alarmı aynı renk"

def test_gece_yon_eksi_gunduz_hue_ailesinde():
    g = _rol_kromatik("gunduz"); n = _rol_kromatik("gece")
    assert _dairesel(g["yon/yon-eksi"], n["yon/yon-eksi"]) <= 6.0, "gece yön-eksi gündüzle aynı hue ailesinde olmalı (kimlik hue, ışıklılık temayla)"

def test_gece_rol_ciftleri_farkli_gruplar_arasi_min_fark():
    h = _rol_kromatik("gece")
    ihlal = []
    adlar = sorted(h)
    for i, a in enumerate(adlar):
        for b in adlar[i+1:]:
            if a.split("/")[0] != b.split("/")[0] and _dairesel(h[a], h[b]) < MIN_FARK:
                ihlal.append((a, b, round(h[a]), round(h[b])))
    # BEYANLI istisnalar: siddet/sev-2 ↔ yon/yon-eksi AYNI bant (spec §2: bilinçli, ışıklılıkla ayrılır)
    ihlal = [x for x in ihlal if {x[0].split("/")[1], x[1].split("/")[1]} != {"sev-2", "yon-eksi"}]
    assert not ihlal, f"gece rol hue çakışmaları: {ihlal}"
```

- [ ] **Step 2: Kırmızıyı gör** — Run: `.venv/bin/python -m pytest tests/test_gece_rol_hue_ayrimi_v396.py` → `test_gece_yon_eksi_ile_kritik_ayri_hue` FAIL (0° vs 1°).

- [ ] **Step 3: Değeri türet (uydurma değil: gündüz hue + gece ışıklılık kuralı)**

```python
# tek seferlik türetim (scratchpad'de koş, sonucu tokens.json'a yaz, komutu raporda göster)
import colorsys
h,l,s = colorsys.rgb_to_hls(*(int("#b43c0b"[i:i+2],16)/255 for i in (1,3,5)))   # gündüz yön-eksi hue
r,g,b = colorsys.hls_to_rgb(h, 0.70, s)  # gece ışıklılık: mevcut gece yön-eksi l≈0,74 bandı (ölç: gece sev-1 l=0,74, yon-arti l=0,58) → 0,70 seçildi (ön-kayıt)
print("#%02x%02x%02x" % (round(r*255), round(g*255), round(b*255)))
```

`rol.gece.yon.yon-eksi.$value` = çıkan hex; `-h` = `rgba(r,g,b,.35)`, `-t` = `rgba(r,g,b,.10)`; `$description`a "K-0 (TSK-117, 2026-09-03): eski #f98080 (0°) gece kritik #ff7e7c (1°) ile çakışıyordu; hue gündüz yön-eksi ailesine (17°) alındı, ışıklılık 0,70". `python ops/jeton_css_uret.py` ile jetonlar.css yeniden.

- [ ] **Step 4: Yeşili gör** — Run: `.venv/bin/python -m pytest tests/test_gece_rol_hue_ayrimi_v396.py tests/test_jeton_birligi_v208.py tests/test_renk_rolleri_v197.py` → PASS.
- [ ] **Step 5: Mutasyon** — gece yön-eksi'yi #f98080'e geri al → test 1 ötmeli; geri al.
- [ ] **Step 6: Build EN SON** — `cd ui && npm run kontrol && npm run build`.
- [ ] **Step 7: Commit (Rol-1)** — `git add meridian/web/tokens.json ui/src/jetonlar.css tests/test_gece_rol_hue_ayrimi_v396.py meridian/web/pano.html meridian/web/pano-assets/...` · mesaj: "TSK-117 K-0: gece yön-eksi hue 0°→17° (kritikle çakışma kapandı); v396 gece hue ayrım çivisi".

---

### Task 3: K-2a — UYARI ailesi göçü (amber-*, 238 kullanım / 44 dosya)

**Files:**
- Modify: `ui/src/**/*.tsx` içinde `amber-*` sınıfı taşıyan dosyalar (liste görev başında `grep -rlE "\b(bg|text|border|ring|from|to|fill|stroke)-amber-[0-9]{2,3}\b" ui/src` ile ÖLÇÜLÜR — 44 beklenir)
- Test: `tests/test_literal_renk_gocu_v397.py` (aile başına tavan; sonraki görevler aynı dosyaya tavan düşürerek devam eder)

**Interfaces:**
- Consumes: Görev 1 utility'leri: `bg-uyari`, `bg-uyari-t`, `text-uyari`, `border-uyari-h`, `ring-uyari-h`.
- Produces: `LITERAL_TAVAN = {"amber": 0, "emerald": 135, "red": 31, "sky": 12}` sözlüğü testte (ölçülen başlangıç değerleri; her görev kendi ailesini 0'a çeker).

- [ ] **Step 1: Ölç ve çiviyi yaz (tavan = bugünkü sayı; amber 0)**

```python
# tests/test_literal_renk_gocu_v397.py
"""v397 — TSK-117 K-2: literal Tailwind renk sınıfları anlam jetonlarına göçer; sayım aile başına
YALNIZ DÜŞER (bedel yasası: her dilim önce/sonra). Tavanlar ölçüm günü (2026-09-03) değerleridir,
göç dilimi ailesini 0'a çeker. (TSK-117, 2026-09-03)"""
import pathlib, re
from meridian import config

UI = pathlib.Path(config.ROOT) / "ui" / "src"
DESEN = re.compile(r"\b(?:bg|text|border|ring|from|to|fill|stroke)-(amber|emerald|green|red|sky)-[0-9]{2,3}\b")
# Görev 3 sonrası: amber 0. Görev 4: emerald+green 0. Görev 5: red 0. Görev 6: sky 0.
LITERAL_TAVAN = {"amber": 0, "emerald": 130, "green": 5, "red": 31, "sky": 12}
ESLEME = {"amber": "uyari", "emerald": "basari", "green": "basari", "red": "kritik", "sky": "bilgi"}

def _sayim():
    s = {k: 0 for k in LITERAL_TAVAN}
    for p in UI.rglob("*.tsx"):
        for m in DESEN.finditer(p.read_text(encoding="utf-8")):
            s[m.group(1)] += 1
    return s

def test_literal_sinif_sayimi_tavani_asmaz():
    s = _sayim()
    asan = {k: (v, LITERAL_TAVAN[k]) for k, v in s.items() if v > LITERAL_TAVAN[k]}
    assert not asan, f"literal renk sınıfı geri geldi (aile: (bulunan, tavan)): {asan} — jeton: {ESLEME}"

def test_gocen_aileler_anlam_utility_kullaniyor():
    # 0'a çekilmiş her aile için en az bir dosya karşılık gelen utility'yi kullanmalı (göç silme değil dönüştürme)
    metin = "\n".join(p.read_text(encoding="utf-8") for p in UI.rglob("*.tsx"))
    for aile, tavan in LITERAL_TAVAN.items():
        if tavan == 0:
            assert re.search(rf"\b(?:bg|text|border|ring)-{ESLEME[aile]}(?:-t|-h)?\b", metin), \
                f"{aile} 0'a indi ama {ESLEME[aile]} utility'si hiç kullanılmıyor — sınıflar silinmiş, dönüştürülmemiş"
```

- [ ] **Step 2: Kırmızıyı gör** — Run: `.venv/bin/python -m pytest tests/test_literal_renk_gocu_v397.py` → amber 238 > 0 FAIL.

- [ ] **Step 3: Eşleme tablosuyla dönüştür (elle, dosya dosya; sed DEĞİL — her kullanım bağlamına bakılır)**

| Literal | Anlam utility | Kural |
|---|---|---|
| `bg-amber-{50,100,200,300}` | `bg-uyari-t` | zemin/tint |
| `bg-amber-{400,500,600}` | `bg-uyari` | dolu vurgu (çip/rozet gövdesi) |
| `text-amber-{300,400}` | `text-uyari` (gece) / `text-uyari` | mürekkep; tema jetonu ışıklılığı zaten taşır |
| `text-amber-{500,600,700}` | `text-uyari` | mürekkep |
| `border-amber-*`, `ring-amber-*` | `border-uyari-h` / `ring-uyari-h` | saç teli |
| `from-/to-amber-*`, `fill-/stroke-amber-*` | `from-uyari` … / `fill-uyari` | |
| `dark:*-amber-*` | ÖNEK KALDIRILIR (jeton temayı kendisi taşır) | |

Bağlam UYARI değilse (ör. amber bir "seçili" ya da "vurgu" için kullanılmış) DÖNÜŞTÜRME, raporda "anlam dışı kullanım" listesine yaz ve tavanı o sayıya çek (beyanlı).

- [ ] **Step 4: Yeşili gör** — Run: `.venv/bin/python -m pytest tests/test_literal_renk_gocu_v397.py tests/test_anlam_jetonlari_v395.py tests/test_arayuz_dili_v323.py tests/test_kovab_b12_v384.py` → PASS.
- [ ] **Step 5: Mutasyon** — bir dosyada `bg-uyari-t`yi `bg-amber-100`e geri çevir → tavan çivisi ötmeli; geri al.
- [ ] **Step 6: Build EN SON + görsel tur notu** — `cd ui && npm run kontrol && npm run build`; raporda dönüştürülen dosya sayısı ve "anlam dışı" listesi. Rol-1 görsel turu (operatör hükmü) → sonraki göreve geçiş kapısı.
- [ ] **Step 7: Commit (Rol-1)** — "TSK-117 K-2a: uyarı ailesi (amber → uyari) N dosya; v397 tavan amber=0".

---

### Task 4: K-2b — BAŞARI ailesi göçü (emerald-* 130 + green-* 5 / 36 dosya) + K-3 seri-9 "başarı" kullanımı

**Files:**
- Modify: `emerald-*`/`green-*` taşıyan `ui/src/**/*.tsx` (grep ile ölç) + `text-[var(--color-seri-9)]` "başarı" anlamıyla kullanılan 3 yer (`grep -rn "color-seri-9" ui/src`)
- Modify: `tests/test_literal_renk_gocu_v397.py` (`LITERAL_TAVAN["emerald"]=0, ["green"]=0`)
- Test: `tests/test_basari_seri9_ayrildi_v398.py`

**Interfaces:** Consumes `bg-basari(-t)`, `text-basari`, `border-basari-h`. Produces: `--color-seri-9` yalnız VERİ serilerinde (grafik) kullanılır.

- [ ] **Step 1: Kırmızı çiviler**

```python
# tests/test_basari_seri9_ayrildi_v398.py
"""v398 — TSK-117 K-3: 'başarı' anlamı seri rampasından (--color-seri-9) ayrıldı; seri jetonları yalnız
grafik/veri bileşenlerinde geçer. (TSK-117, 2026-09-03)"""
import pathlib, re
from meridian import config
UI = pathlib.Path(config.ROOT) / "ui" / "src"
VERI_BILESENLERI = ("takimyildizi.tsx", "Huni.tsx", "grafik", "chart")   # seri jetonu izinli dosyalar (ölç, genişletme raporla)

def test_seri_jetonu_veri_disi_bilesende_yok():
    ihlal = []
    for p in UI.rglob("*.tsx"):
        if any(k in str(p) for k in VERI_BILESENLERI): continue
        for m in re.finditer(r"var\(--color-seri-\d+\)|\bseri-\d+\b", p.read_text(encoding="utf-8")):
            ihlal.append(f"{p.relative_to(UI)}:{m.group(0)}")
    assert not ihlal, f"seri (veri kimliği) jetonu anlam taşıyan yüzeyde: {ihlal}"
```

`LITERAL_TAVAN["emerald"] = 0; LITERAL_TAVAN["green"] = 0` (v397).

- [ ] **Step 2: Kırmızıyı gör** — v398 (3 yer) + v397 (emerald 130) FAIL.
- [ ] **Step 3: Dönüştür** — Görev 3 tablosunun `basari` karşılığı (`emerald/green-{50..300}`→`bg-basari-t`; `400-600`→`bg-basari`/`text-basari`; border/ring→`-h`); seri-9 başarı kullanımları → `text-basari`. Anlam dışı (emerald "seçili" vb.) → raporda liste, tavan beyanlı.
- [ ] **Step 4: Yeşil** — `pytest tests/test_basari_seri9_ayrildi_v398.py tests/test_literal_renk_gocu_v397.py tests/test_anlam_jetonlari_v395.py tests/test_hafiza_genel_bakis_v388.py`.
- [ ] **Step 5: Mutasyon** — bir `text-basari`yi `text-[var(--color-seri-9)]`e geri çevir → v398 ötmeli.
- [ ] **Step 6: Build EN SON**; görsel tur (başarı rengi 160°→145° kayması operatöre GÖSTERİLİR — ekran değişir, beyan).
- [ ] **Step 7: Commit (Rol-1)** — "TSK-117 K-2b/K-3: başarı ailesi (emerald/green → basari), seri-9 anlam yükü kaldırıldı; v397/v398".

---

### Task 5: K-2c — KRİTİK ailesi (red-* 31 / 13 dosya)

**Files:** `red-*` taşıyan `.tsx` dosyaları; `tests/test_literal_renk_gocu_v397.py` (`red: 0`).

- [ ] **Step 1:** v397'de `LITERAL_TAVAN["red"] = 0` → kırmızı (31).
- [ ] **Step 2:** Dönüştür: `bg-red-{50..300}`→`bg-kritik-t`; `bg-red-{400..600}`→`bg-kritik`; `text-red-*`→`text-kritik`; `border/ring-red-*`→`-h`. Yıkıcı buton (destructive) shadcn `variant="destructive"` kullanıyorsa jetona DOKUNMA (shadcn `--destructive` ayrı kanal; raporda say).
- [ ] **Step 3:** Yeşil: `pytest tests/test_literal_renk_gocu_v397.py tests/test_anlam_jetonlari_v395.py tests/test_ui_pilot_kapilari_v286.py`.
- [ ] **Step 4:** Mutasyon (bir `text-kritik` → `text-red-600`) → ötmeli; geri al.
- [ ] **Step 5:** Build EN SON; görsel tur.
- [ ] **Step 6:** Commit (Rol-1) — "TSK-117 K-2c: kritik ailesi (red → kritik); v397 red=0".

---

### Task 6: K-2d — BİLGİ ailesi (sky-* 12 / 3 dosya) + S3 beyanı

**Files:** `sky-*` taşıyan 3 dosya; `tests/test_literal_renk_gocu_v397.py` (`sky: 0`); `docs/TASARIM-PALET-REZERVE-HUE-2026-09-03.md` §2 satırı (BİLGİ rezerve, K-2d tamam).

- [ ] **Step 1:** v397 `sky: 0` → kırmızı (12).
- [ ] **Step 2:** Dönüştür (`bilgi`, `bilgi-t`, `bilgi-h`). Bağlam "gezinme/seçim" ise `nav` jetonu (ROL 6) — bilgi DEĞİL; raporda ayır.
- [ ] **Step 3:** Yeşil: v397 + v395 + v388 (`test_DUGUM_RENKLERI_rol_bantlarinda_DEGIL` — BİLGİ bandı sözlükte, camgöbeği istisnası hâlâ gerekli; Görev 7'de kapanır).
- [ ] **Step 4:** Mutasyon → ötmeli; geri al. **Step 5:** Build EN SON. **Step 6:** Commit (Rol-1) — "TSK-117 K-2d: bilgi ailesi (sky → bilgi); literal renk sınıfı 416→0 (anlam dışı beyanlılar hariç)".

---

### Task 7: K-4 — Seri rampası A′ + huni seriye + DUGUM_STILI istisnası kapanır

**Files:**
- Modify: `ui/src/tema.css` (`:root`/`.dark` `--seri-6..10`)
- Modify: `meridian/web/tokens.json` (`huni-1/2/3` → seri değerleriyle AYNI hex + "= seri-6/7/8" beyanı) + regenerate `ui/src/jetonlar.css`
- Modify: `ui/src/pano/yuzeyler/hafiza/takimyildizi.tsx` (`DUGUM_STILI.tur`, `isiDuraklari`)
- Modify: `tests/test_hafiza_genel_bakis_v388.py` (`ISTISNALAR = {}`; ROL_BANTLARI sözlüğü tam)
- Test: `tests/test_seri_rampasi_serbest_bant_v399.py`

**Interfaces:**
- Produces: seri 6–10 yeni hue'lar: `--seri-6: var(--color-teal-600)` (≈175°), `--seri-7: var(--color-lime-600)` (≈85°), `--seri-8: var(--color-fuchsia-600)` (≈292°), `--seri-9: var(--color-pink-600)` (≈329°), `--seri-10: var(--color-yellow-600)` (≈45°); gece 400'ler. (Ön-kayıt seçimi; hepsi spec §2 serbest bantlarda — çivi hesaplar, tablo yazmaz.)
- `DUGUM_STILI.tur`: `world: "teal"` (seri-6), `experience: "pembe"` (seri-9), `observation: "soluk"`, `entity: "yazi"`; `isiDuraklari: [soluk, teal, pembe]`. Jeton adları `paletOku` sözlüğünde tanımlanır (ölç).

- [ ] **Step 1: Kırmızı çivi**

```python
# tests/test_seri_rampasi_serbest_bant_v399.py
"""v399 — TSK-117 K-4 (S1=A′, S2): seri rampası 6–10 rol bantları DIŞINDA; huni jetonları seri değerlerinden
TÜRER (kopya değil); Tailwind palet hex'leri testin içinde çözülür (tema.css var(--color-X-N) → tailwind
palet dosyası ölçülerek). (TSK-117, 2026-09-03)"""
import colorsys, json, pathlib, re
from meridian import config
ROOT = pathlib.Path(config.ROOT); TEMA = ROOT/"ui"/"src"/"tema.css"; TOKENS = ROOT/"meridian"/"web"/"tokens.json"
BANTLAR = {"KRITIK": (336, 366), "UYARI": (8, 30), "BASARI": (132, 155), "BILGI": (185, 210), "NAV": (210, 232), "MOD": (245, 270)}

def _hue(hexstr):
    r,g,b = (int(hexstr[i:i+2],16)/255 for i in (1,3,5)); h,l,s = colorsys.rgb_to_hls(r,g,b); return h*360

def _tailwind_hex(ad):
    """`--color-teal-600` → hex: node_modules/tailwindcss/theme.css içinden ÖLÇ (oklch ise oklch→sRGB dönüşümü v388'deki yardımcıyla)."""
    from tests.test_hafiza_genel_bakis_v388 import _tailwind_renk_hex  # v388'de tanımlı yardımcı; yoksa buraya taşı ve v388 ithal etsin
    return _tailwind_renk_hex(ad)

def _seri(tema_blok):
    css = TEMA.read_text(encoding="utf-8")
    blok = re.search(rf"{tema_blok}\s*\{{([^}}]*)\}}", css, re.S).group(1)
    return {int(m.group(1)): m.group(2) for m in re.finditer(r"--seri-(\d+):\s*var\((--color-[a-z]+-\d+)\)", blok)}

def _bantta(h):
    for ad,(a,b) in BANTLAR.items():
        if a <= h < b or (b > 360 and (h >= a or h < b-360)): return ad
    return None

def test_seri_6_10_rol_bantlarinda_DEGIL():
    for blok in (":root", r"\.dark"):
        for k, tw in _seri(blok).items():
            if k < 6: continue
            h = _hue(_tailwind_hex(tw)); assert _bantta(h) is None, f"seri-{k} ({tw}, {h:.0f}°) rol bandında: {_bantta(h)}"

def test_huni_jetonlari_seri_degerlerinden_turer():
    d = json.loads(TOKENS.read_text(encoding="utf-8"))
    huni = d["rol"]["gunduz"]["huni"]
    seri = _seri(":root")
    for i, k in ((1, 6), (2, 7), (3, 8)):
        assert huni[f"huni-{i}"]["$value"].lower() == _tailwind_hex(seri[k]).lower(), f"huni-{i} ≠ seri-{k} (kopya ayrıştı)"
        assert "seri-" in huni[f"huni-{i}"].get("$description", ""), "huni beyanı 'seri-N' türetimini söylemeli"

def test_dugum_stili_istisnasi_KAPANDI():
    from tests.test_hafiza_genel_bakis_v388 import ISTISNALAR
    assert ISTISNALAR == {}, "palet turu bitti — DUGUM_STILI istisnası ölü muafiyet olmamalı"
```

(`huni` grubunun tokens.json'daki gerçek yolu ÖLÇÜLÜR — `grep -n "huni-1" meridian/web/tokens.json`; test ona göre.)

- [ ] **Step 2: Kırmızıyı gör** — seri-6 nav, seri-7 uyarı, seri-8 mod, seri-9 bilgi bantlarında → FAIL; huni kopya → FAIL; ISTISNALAR dolu → FAIL.
- [ ] **Step 3: tema.css rampası** — `:root` 600'ler, `.dark` 400'ler (teal/lime/fuchsia/pink/yellow); şerh: "A′ (TSK-117, 2026-09-03): rol bantları dışı; tema.css'in kendi 'ardışık iki ton komşu değil' kuralı korunur (175→85→292→329→45)".
- [ ] **Step 4: huni** — tokens.json `huni-1/2/3` değerleri = seri-6/7/8 hex'leri (600), `$description`: "= tema.css --seri-6 (teal-600) — VERİ görseli, rol değil (S2)"; gece: 400 karşılıkları. `python ops/jeton_css_uret.py`.
- [ ] **Step 5: DUGUM_STILI** — `tur.world = "teal"`, `experience = "pembe"`; `isiDuraklari = ["soluk","teal","pembe"]`; `paletOku` sözlüğüne `teal: var(--color-seri-6)` (adı ölç). v388 `ISTISNALAR = {}`; `test_ISTISNALAR_KUNYELI_ve_HALA_GEREKLI` boş listeyle yeşil kalıyor mu ÖLÇ — kalmıyorsa "boş = istisna yok" dalını yaz.
- [ ] **Step 6: Yeşil** — `pytest tests/test_seri_rampasi_serbest_bant_v399.py tests/test_hafiza_genel_bakis_v388.py tests/test_jeton_birligi_v208.py tests/test_renk_rolleri_v197.py`.
- [ ] **Step 7: Mutasyon** — seri-8'i violet-600'e geri al → bant çivisi ötmeli; huni-1'i #2563eb'e geri al → türetim çivisi ötmeli; geri al.
- [ ] **Step 8: Build EN SON**; görsel tur: Bellekler tam graf + Huni + Sermaye grafiği (10 seri) operatöre.
- [ ] **Step 9: Commit (Rol-1)** — "TSK-117 K-4: seri rampası A′ (teal/lime/fuchsia/pink/yellow), huni seriye bağlı, DUGUM_STILI istisnası kapandı; v399".

---

### Task 8: S4 — Renk körlüğü ölçümü (deuteranopi/protanopi simülasyonu + ışıklılık farkı)

**Files:**
- Create: `tests/test_renk_korlugu_v400.py`
- Modify: `docs/TASARIM-PALET-REZERVE-HUE-2026-09-03.md` §6 (S4 sonucu, ölçülen sayılar)

**Interfaces:** Consumes tokens.json gündüz/gece rol jetonları (`sev-2`↔`sev-3`, `yon-arti`↔`yon-eksi`, `kritik`↔`uyari`). Produces: her çift için simüle edilmiş ΔL (WCAG bağıl ışıklılık farkı) ve kontrast oranı; eşik ÖN-KAYIT: **kontrast ≥ 1,4:1** çift başına (tasarım seçimi, ölçüm değil — spec §6 "ölçülmeyen: colorblind" boşluğu kapanır).

- [ ] **Step 1: Çivi (önce koş — bugünkü değerler kırmızı mı yeşil mi ÖLÇÜLÜR; kırmızıysa jeton ışıklılığı Görev 2 emsaliyle ayarlanır, hue değil)**

```python
# tests/test_renk_korlugu_v400.py
"""v400 — TSK-117 S4: rol çiftleri deuteranopi/protanopi simülasyonunda ışıklılıkla ayrılıyor mu.
Simülasyon: Viénot-Brettel-Mollon (1999) LMS projeksiyonu (matrisler literatürden, kaynak docstring'de).
Eşik ön-kayıt: kontrast oranı ≥ 1,4:1 (WCAG bağıl ışıklılık). (TSK-117, 2026-09-03)"""
import json, pathlib
from meridian import config
TOKENS = pathlib.Path(config.ROOT)/"meridian"/"web"/"tokens.json"
ESIK = 1.4
CIFTLER = [("siddet","sev-2","siddet","sev-3"), ("yon","yon-eksi","yon","yon-arti"), ("siddet","sev-1","siddet","sev-2")]
# sRGB → linear
def _lin(c): c/=255; return c/12.92 if c<=0.04045 else ((c+0.055)/1.055)**2.4
def _rgb(hexstr): return [_lin(int(hexstr[i:i+2],16)) for i in (1,3,5)]
# RGB→LMS (Hunt-Pointer-Estevez, D65) ve deuteranopi/protanopi projeksiyonları (Viénot 1999)
RGB2LMS = [[0.31399022,0.63951294,0.04649755],[0.15537241,0.75789446,0.08670142],[0.01775239,0.10944209,0.87256922]]
LMS2RGB = [[5.47221206,-4.6419601,0.16963708],[-1.1252419,2.29317094,-0.1678952],[0.02980165,-0.19318073,1.16364789]]
DEUTAN = [[1,0,0],[0.9513092,0,0.04866992],[0,0,1]]
PROTAN = [[0,1.05118294,-0.05116099],[0,1,0],[0,0,1]]
def _mm(M,v): return [sum(M[i][j]*v[j] for j in range(3)) for i in range(3)]
def _sim(rgb, P): return _mm(LMS2RGB, _mm(P, _mm(RGB2LMS, rgb)))
def _Y(rgb): r,g,b=(max(0,min(1,x)) for x in rgb); return 0.2126*r+0.7152*g+0.0722*b
def _kontrast(a,b): ya,yb=_Y(a),_Y(b); hi,lo=max(ya,yb),min(ya,yb); return (hi+0.05)/(lo+0.05)

def _jeton(tema,grup,ad):
    d=json.loads(TOKENS.read_text(encoding="utf-8")); return d["rol"][tema][grup][ad]["$value"]

def test_rol_ciftleri_renk_korlugunde_isiklilikla_ayrilir():
    ihlal=[]
    for tema in ("gunduz","gece"):
        for g1,a1,g2,a2 in CIFTLER:
            x,y=_rgb(_jeton(tema,g1,a1)),_rgb(_jeton(tema,g2,a2))
            for adi,P in (("deutan",DEUTAN),("protan",PROTAN)):
                k=_kontrast(_sim(x,P),_sim(y,P))
                if k<ESIK: ihlal.append((tema,a1,a2,adi,round(k,2)))
    assert not ihlal, f"renk körlüğünde ayrışmayan rol çiftleri (kontrast<{ESIK}): {ihlal}"
```

- [ ] **Step 2: Koş** — Run: `.venv/bin/python -m pytest tests/test_renk_korlugu_v400.py`. YEŞİLSE: sonuç sayıları (her çift kontrastı) raporda + spec §6'ya "S4 ölçüldü: …". KIRMIZIYSA: ihlal eden çiftin gece/gündüz ışıklılığı (hue sabit) Görev 2'deki türetim deseniyle ayarlanır (tokens.json + regenerate; v396/v208 yeşil kalmalı) — hue'ya dokunulmaz.
- [ ] **Step 3: Mutasyon** — ESIK'i 1.0 yap → çivi hiçbir çifti yakalamamalı (körlük tabanı: en az bir çift 1.0'ın üstünde ama 1.4'ün altına inmiş olsaydı yakalanırdı — raporda gerçek min kontrastı yaz). ESIK 3.0 → en az bir çift ötmeli (dönüşümün gerçekten ölçtüğünün kanıtı).
- [ ] **Step 4: Spec güncelle** — §6 "Ölçülmeyen: colorblind" cümlesi → ölçülen tabloyla değişir.
- [ ] **Step 5: Commit (Rol-1)** — "TSK-117 S4: renk körlüğü çivisi v400 (Viénot simülasyonu, kontrast ≥1,4) + spec §6".

---

## Self-review (Rol-1, yazım anında)

- Spec kapsama: §2 bantlar → G7/G8 çivileri; §4 K-0 → G2, K-1 → G1, K-2 → G3–G6, K-3 → G4, K-4 → G7; §7 S1 → G7, S2 → G7 (huni), S3 → G1/G6 (`--bilgi`), S4 → G8, S5 → G3–G6 dört dilim. Boşluk: 195° ailesinin `sky/blue/sapphire` üç jetonundan hangisi `--bilgi` kaynağı — G1 Step 3 "sky'ın gerçek yolunu ölç" ile açık bırakıldı (implementer ölçer; blue/sapphire'ın rolü raporda).
- Placeholder: "<yeni>" bundle adları commit satırlarında — dosya adı build sonrası doğar, Rol-1 ölçer (kaçınılmaz). Başka TBD yok.
- Tip/ad tutarlılığı: `--basari/--uyari/--kritik/--bilgi` + `-h/-t` G1'de doğar, G3–G6 aynı adları kullanır; `LITERAL_TAVAN` v397'de tek sözlük, G4–G6 aynı dosyayı düzenler; `ISTISNALAR` v388'den ithal (G7).
- Bedel: her dilim önce/sonra sayım + görsel tur; G7 seri kimliği zayıf iki ton (lime/yellow) beyanlı.
