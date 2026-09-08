# TSK-012 dalga-B — B3 ölçüm planı (EDG-2026-086: uydurma · araç disiplini · gecikme · kota · öneri)

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development. Steps use checkbox syntax.

**Goal:** `state/sohbet.jsonl` üzerinden EDG-2026-086'nın beş ölçüsünü sayan, yol-tutarlı pozitif kontrolü (sentetik 20 mesaj: 3 uydurma · 2 metin-araç · 1 kota) geçen
`research/olcumler/edg086_pano_sohbet/sayim.py` + bunun paydası için B1'e eklenen **tur başına çıktı atıf izi** (`turlar[i].cikti_atiflari`).
**Spec:** `docs/superpowers/specs/2026-09-07-pano-sohbet-design.md` §3 · **Kart:** `research/cards/EDG-2026-086-pano-sohbet-kalite.yaml` (eşikler DONUK: uydurma ≤0,05 ·
şema-dışı ≤0,10 · p50 ≤20 s · kota 120 · n ≥100 ∧ seans ≥10) · **Emsal sayaç:** `research/olcumler/edg083_zihin_modeli_ek_sayfalar/uydurma_say.py`
(`atiflari_cikar`, `SINIF_REGEXLERI`, `markdown_uret` deseni) · **Defter üreticisi:** `meridian/sohbet.py::_kaydet`, `sohbet_dongusu`, `_arac_kos`.

**Architecture:** Ölçümün PAYDASI araç çıktısıdır (kill-list: cevabı tek başına okuyan sayım geçersiz). Defter araç çıktısının METNİNİ saklamaz (8 KB × 6 tur × 100+ mesaj
ve sır yüzeyi); bunun yerine her turda araç çıktısından çıkarılan LİTERAL ATIF KÜMESİ saklanır — `meridian/sohbet.py::cikti_atiflari(metin) -> dict[str, list[str]]`
(sınıflar: `sayi` (tam/ondalık, binlik ayraçsız normal biçim), `kimlik` (T\d{5} · P-… · EDG-2026-\d{3} · TSK-\d{3} · SO-…), `yol` (uydurma_say YOL_RE), `sembol`
(evrendeki sembol listesiyle kesişim; `meridian.universe` ya da defterdeki sembol kümesi — ÖLÇ hangisi tek kaynak)). Sayaç cevaptaki aynı sınıf atıfları
çıkarır ve turların birleşik kümesinde arar. Aynı çıkarıcı iki tarafta (tek kaynak); sayaç `meridian.sohbet.cikti_atiflari`yı İTHAL eder, kopyalamaz.

**Tech Stack:** Python 3.12, stdlib (json, re, statistics); pytest çivileri `sandbox_state` ile; `.venv/bin/python`.

## Global Constraints
- Kart eşikleri ve pencere DEĞİŞMEZ; sayaç yalnız SAYAR, hüküm Rol-1'in (kart + K defteri aynı turda).
- Sayaç `state/`'e YAZMAZ; çıktı `research/olcumler/edg086_pano_sohbet/sonuc_<tarih>.{json,md}` (komut satırı `--defter`, `--cikti`, `--markdown`, `--baslangic`).
- Ölçülemeyen sınıf `belirsiz` ayrı sayılır, uydurma SAYILMAZ (uydurma yasağı); jeton/süre None ise "ölçülemedi".
- Sır: sayaç `notify.scrub`'dan geçmiş metinle çalışır (defter zaten süzgeçli); çivide sahte sır atıfı → hiçbir çıktıda görünmez.
- Yasa 4/6, çapa yasağı, `-q` yok, seri pytest, git yok; `meridian/sohbet.py`ye dokunulur → tam suite Rol-1'de.
- Test numaraları SABİT: v449 (`tests/test_sohbet_cikti_atif_v449.py`), v450 (`tests/test_edg086_sayim_v450.py`).

---

### Task 1 — `meridian/sohbet.py::cikti_atiflari` + defter alanı (implementer)
**Files:** Modify `meridian/sohbet.py` (yeni saf fonksiyon `cikti_atiflari(metin: str) -> dict[str, list[str]]`; `sohbet_dongusu` içinde her başarılı araç
çağrısından sonra `tur.setdefault("cikti_atiflari", {"sayi": [], "kimlik": [], "yol": [], "sembol": []})` sınıf başına BİRLEŞİM (tekilleştirilmiş, sıralı, sınıf başına
≤200 öğe; taşarsa `tur["cikti_atif_kesildi"]=True`) · Test `tests/test_sohbet_cikti_atif_v449.py`.
**Interfaces (Produces):** `cikti_atiflari(metin) -> {"sayi": [...], "kimlik": [...], "yol": [...], "sembol": [...]}` — deterministik, sıralı; sembol kaynağı fonksiyonun
docstring'inde ölçülerek yazılır (`universe` modülü ya da `state/universe.json` — hangisi canlıda tek kaynaksa).
- [ ] Çivi 1 (kırmızı): `cikti_atiflari("T00842 kapandı, 1.103R, AAPL 189.5, research/cards/EDG-2026-086-pano-sohbet-kalite.yaml, P-2026-09-07-3")` →
      sayi ⊇ {"1.103","189.5"} · kimlik ⊇ {"T00842","EDG-2026-086","P-2026-09-07-3"} · yol ⊇ {"research/cards/EDG-2026-086-pano-sohbet-kalite.yaml"} · sembol ⊇ {"AAPL"} (evren sahtesiyle).
- [ ] Çivi 2: `sohbet_dongusu` sahte model + sahte araç (çıktı "T00001 12.5") ile → defter satırında `turlar[0]["cikti_atiflari"]["kimlik"] == ["T00001"]`, `["sayi"] == ["12.5"]`;
      şema-dışı/arızalı araç çağrısında alan EKLENMEZ (payda şişmez).
- [ ] Çivi 3: 8 KB'lık çıktıda 300 farklı sayı → 200'de kesilir, `cikti_atif_kesildi` True.
- [ ] Çivi 4: sahte sır dizgesi araç çıktısında → `notify.scrub` sonrası atıf kümesinde YOK (scrub `_arac_kos`ta çıktıya uygulanıyor; çıkarma scrub SONRASI metinden).
- [ ] Uygulama (minimal) · mutasyon ≥3 (kesme tavanı · şema-dışıda alan eklenmesi · sembol kesişimi) · v440/v441/v444 yeşil · rapor.

### Task 2 — `research/olcumler/edg086_pano_sohbet/sayim.py` (implementer; Task 1 sonrası)
**Files:** Create `research/olcumler/edg086_pano_sohbet/sayim.py`, `research/olcumler/edg086_pano_sohbet/README.md` (komut satırı + alan sözlüğü) · Test `tests/test_edg086_sayim_v450.py`.
**Interfaces (Consumes):** `meridian.sohbet.cikti_atiflari` (cevap tarafı için aynı çıkarıcı), defter satır şeması (`_kaydet`).
**Komut satırı:** `python research/olcumler/edg086_pano_sohbet/sayim.py --defter state/sohbet.jsonl --cikti <json> [--markdown <md>] [--baslangic 2026-09-08T00:00Z]`
**Ölçüler (JSON):** `n_mesaj`, `n_seans`, `pencere_doldu` (n≥100 ∧ seans≥10), `uydurma: {payda, uydurma, belirsiz, oran, sinif_kirilimi}`, `arac: {tur_n, sema_disi_n,
metin_arac_n, oran}` (metin-araç: cevap metninde BEYAZ_LISTE araç adı `ad(` biçiminde geçiyor ∧ o turda tool_calls==0), `gecikme: {p50_s, p95_s, tur_kirilimi}`,
`kota: {gun_basi_max, gun_basi_ort, dolu_pencere_pay, llm_dustu_n}`, `oneri: {n, onaylanan, reddedilen, bekleyen}` (approvals.jsonl `kaynak=sohbet`), `model_kirilimi:
{kunye: {n, uydurma_oran, sema_disi_oran}}`, `olculemeyen: [...]`.
- [ ] Çivi 1 (kırmızı, PK-SENTETİK): 20 satırlık sahte defter (3 uydurma: cevapta araç kümesinde OLMAYAN sayı/kimlik/yol; 2 metin-araç turu; 1 llm_dustu/kota) →
      sayaç tam 3 / 2 / 1 bulur; 4. bir uydurma EKLENİRSE 4 (mutasyon).
- [ ] Çivi 2: `belirsiz` — cevapta sınıfı bilinmeyen sayı biçimi (örn. "%12") uydurma DEĞİL belirsiz.
- [ ] Çivi 3: gecikme p50/p95 `statistics.quantiles` ile; süre None olan satır `olculemeyen`e.
- [ ] Çivi 4: `pencere_doldu` False iken markdown "HÜKÜM YOK (betimleyici ara-rapor)" başlığı; True iken eşik satırları yalnız SAYI olarak (hüküm kelimesi YOK).
- [ ] Çivi 5: komut satırı subprocess ile tmp_path'te bir kez (ops sözleşmesi); `state/` yolu verilmezse hata.
- [ ] Uygulama · mutasyon ≥3 · rapor.

### Task 3 — Rol-1: merge → tam suite → dağıtım → kart `notlar`a "B3 sayacı hazır; pencere B2 dağıtımından itibaren" → 10 seans sonra `sayim.py` koşumu (kuru koşum
DEĞİL: `state/sohbet.jsonl` salt okunur, yazmaz) → PK-GERÇEK (10 cevap elle) → hüküm karta + K defterine.
