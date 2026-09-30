# Konuşan bot filosu — Parça 1b G1: Meridian araç sunucusunda bot başı araç alt kümesi — Uygulama Planı

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `meridian/mcp_server.py` bir bot adıyla (`--bot <ad>`) açıldığında YALNIZ o botun `kadro.araclar` listesindeki araçları sunar; araç kümesi mevcut 6 getter + pano sohbetinin okuma araçları (tek kaynak `sohbet.ARACLAR`, çalıştırıcı `sohbet._arac_kos` — VERİ çiti + scrub + tavan) + `oneri_yaz` + `is_iste` + `bot_hafizasi_ara`.

**Architecture:** Parça 0 v3 (2026-09-30 06:18Z) KAPIYI GEÇTİ: Hermes `mcp` kurulu (K-1), bekçi ikizi `meridian_regime`ı GERÇEKTEN çağırdı (oturumda `role: tool`), enjeksiyon reddedildi. Bu plan araç yüzeyini bot rolüne göre daraltır. Varsayılan profil `enabled: false` kalır (K-1); `--bot` verilmezse sunucu bugünkü 6 getter'ı sunar (geri uyum). Dağıtım yok; sohbet profilleri G2'de bağlar.

**Tech Stack:** Python 3 stdlib; mevcut `meridian.mcp_server` (satır-ayrımlı JSON-RPC), `meridian.sohbet` (`ARACLAR`, `_arac_kos`, `Arac`), `meridian.kadro`, `meridian.is_istek`, `meridian.bot_hafiza`.

**Spec:** `docs/superpowers/specs/2026-09-29-konusan-bot-filosu-design.md` §3.2 · Parça 0 raporu (v3 notu) · taslak `docs/superpowers/plans/2026-09-30-konusan-filo-parca1b-taslak.md` G1.

## Global Constraints
- Araç adları TEK KAYNAK: sohbet araçları `sohbet.ARACLAR` anahtarlarıyla, getter'lar `mcp_server` `TOOLS` adlarıyla, yeni ikisi `is_iste` ve `bot_hafizasi_ara` (= `kadro.PLANLI_ARACLAR`). `kadro.araclar` bu birleşik kümenin alt kümesi olmalı (v591 zaten çiviliyor).
- Sohbet araçları MCP'de `sohbet._arac_kos` üzerinden koşar — çit/scrub/tavan/şema doğrulaması KOPYALANMAZ.
- `--bot` verilince: bot kadroda `aktif` değilse süreç açılmaz (stderr'e ad + neden, çıkış ≠ 0). `tools/list` yalnız izinli araçları döner; izinli olmayan bir araç `tools/call` edilirse `isError: true` + "bu bot için izinli değil" (araç KOŞMAZ).
- `bot_hafizasi_ara` yalnız `hafiza: hepsi` botlara (bugün `sef`) listelenir — kadro `araclar`ında olsa bile `hafiza != hepsi` ise listelenmez (iki kat).
- `is_iste` MCP'den çağrılınca kanal BİLİNMEZ → `is_istek.is_iste(ad, kanal=None, cagiran="mcp:<bot>")`: defterde `kanal: null`, `cagiran` alanı; UYDURMA kanal yok. `kanal` verilince bugünkü doğrulama aynen.
- `oneri_yaz` MCP'den: mevcut `approvals.jsonl` yolu, bağlam `oturum = "mcp:<bot>"`; panonun sohbet önerisi onay akışı (`api` `_sohbet.CAGRI_KIND` / `oneri_kimligi_mi`) BOZULMAZ — ölç, çivile.
- Test numarası v597. Test adlarında FAILED/ERROR yok; yorumlarda `dosya.py:NNN` yok; Yasa 4/6; `sandbox_state`.

## Review Focus
1. `--bot` yazım hatası/kadro dışı bot → süreç sessizce 6 getter'la açılırsa bot yanlış araç görür → açılmamalı (Görev 1 testi).
2. `tools/list` süzülüp `tools/call` süzülmezse model listede olmayanı adıyla çağırabilir → iki kat çivili.
3. Sohbet aracı istisna fırlatırsa MCP döngüsü ölmemeli (bugünkü `isError` davranışı).
4. `oneri_yaz` MCP üzerinden yazılan satır panonun onay kutusunda görünmeli ve onaylanınca mevcut icra yolundan geçmeli (ikinci onay yolu YOK).
5. Hermes MCP aracı adını `mcp__meridian__<ad>` diye önekliyor (v3 ölçümü) — sunucu tarafı ad sözleşmesi `<ad>` kalır; önek Hermes'in işi.

---

### Task 1: Araç kaydı + `--bot` alt kümesi + sohbet araçları + `oneri_yaz` (`meridian/mcp_server.py`)

**Files:** Modify `meridian/mcp_server.py` · Test `tests/test_mcp_bot_alt_kume_v597.py`

**Interfaces:**
- Produces: `def arac_kaydi() -> dict[str, dict]` (ad → `{"name", "description", "inputSchema", "cagir": callable(args, baglam) -> str}`); `def izinli_araclar(bot: str | None, kadro=None) -> list[str]` (bot None → 6 getter adı; aksi hâlde `kadro.araclar` ∩ kayıt, `bot_hafizasi_ara` yalnız `hafiza == "hepsi"`); `def serve(stdin=None, stdout=None, bot: str | None = None) -> None`; `def main(argv: list[str] | None = None) -> int`.

- [ ] **Step 1: Başarısız testler** (`sandbox_state`; JSON-RPC satırlarını `io.StringIO` ile besle):

```python
def _rpc(bot, *mesajlar):
    import io, json
    from meridian import mcp_server as ms
    giris = io.StringIO("".join(json.dumps(m) + "\n" for m in mesajlar)); cikis = io.StringIO()
    ms.serve(giris, cikis, bot=bot)
    return [json.loads(s) for s in cikis.getvalue().splitlines() if s.strip()]

def _liste(bot):
    return sorted(t["name"] for t in _rpc(bot, {"jsonrpc": "2.0", "id": 1, "method": "tools/list"})[0]["result"]["tools"])

def test_bot_yokken_bugunku_alti_getter(sandbox_state):
    assert _liste(None) == sorted(["meridian_regime", "meridian_calibrations", "meridian_near_miss",
                                   "meridian_cf_summary", "meridian_selfreview", "meridian_candidate_context"])

def test_bekci_yalniz_kadro_araclari(sandbox_state):
    from meridian import kadro
    beklenen = sorted(set(kadro.bot_bul("bekci").araclar) - {"bot_hafizasi_ara"})
    assert _liste("bekci") == beklenen

def test_bot_hafizasi_ara_yalniz_hepsi_hafizali_bota(sandbox_state):
    assert "bot_hafizasi_ara" in _liste("sef") and "bot_hafizasi_ara" not in _liste("karne")

def test_izinli_olmayan_arac_cagrisi_reddedilir_ve_kosmaz(sandbox_state, monkeypatch):
    from meridian import mcp_server as ms
    kosuldu = []
    monkeypatch.setitem(ms.arac_kaydi_onbellek(), "meridian_regime",
                        {**ms.arac_kaydi()["meridian_regime"], "cagir": lambda a, b=None: kosuldu.append(1) or "x"})
    r = _rpc("bekci", {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                        "params": {"name": "meridian_regime", "arguments": {}}})[0]["result"]
    assert r["isError"] is True and "izinli değil" in r["content"][0]["text"] and kosuldu == []

def test_sohbet_araci_cit_ve_scrub_ile_doner(sandbox_state):
    r = _rpc("bekci", {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                        "params": {"name": "alarm_oku", "arguments": {}}})[0]["result"]
    assert r["content"][0]["text"].startswith("<<<VERI:alarm_oku>>>")

def test_kadro_disi_ya_da_pasif_botla_acilmaz(capsys):
    from meridian import mcp_server as ms
    assert ms.main(["--bot", "kod"]) != 0 and "kod" in capsys.readouterr().err
    assert ms.main(["--bot", "yokboyle"]) != 0
```
(Not: `arac_kaydi_onbellek()` testin kayıt girdisini değiştirebilmesi için modül düzeyi önbelleği döndüren küçük yardımcı; uygulayıcı daha temiz bir enjeksiyon yolu bulursa onu kullanır ve rapora yazar.)

- [ ] **Step 2: Kırmızı** — `.venv/bin/python -m pytest tests/test_mcp_bot_alt_kume_v597.py -p no:cacheprovider`
- [ ] **Step 3: Uygula** — kayıt: 6 getter bugünkü `TOOLS`tan; sohbet araçları `sohbet.ARACLAR`dan (`inputSchema = Arac.sema`, `cagir = lambda args, baglam: sohbet._arac_kos(ad, args, baglam, sohbet.ARACLAR)[0]`); `serve` `bot`a göre `izinli_araclar`; `tools/call` önce izin kontrolü; bağlam `{"oturum": f"mcp:{bot}"}`; `main` `argparse` `--bot`.
- [ ] **Step 4: Yeşil** · **Step 5: Mutasyon** (tools/call izin kontrolünü kaldır → kırmızı; `hafiza == "hepsi"` koşulunu kaldır → kırmızı; `main` kadro doğrulamasını kaldır → kırmızı; `_arac_kos` yerine doğrudan `Arac.cagir` → çit testi kırmızı).
- [ ] **Step 6: Kapsam** — v597 + mevcut mcp_server testleri (`grep -l "mcp_server" tests/test_*.py`) + sohbet testleri (`grep -l "from meridian import sohbet\|meridian.sohbet" tests/test_*.py`) + v591 + codelaw + v334 + v382 (seri, üçlü hüküm).

---

### Task 2: `is_iste` ve `bot_hafizasi_ara` MCP araçları

**Files:** Modify `meridian/mcp_server.py`, `meridian/is_istek.py` (`kanal=None` + `cagiran`), `meridian/bot_hafiza.py` (`ara(bot, soru, k=5) -> list[tuple[str, str]]`, salt-okur recall) · Test `tests/test_mcp_bot_alt_kume_v597.py`, `tests/test_is_istek_v594.py`, `tests/test_bot_hafiza_v596.py`

**Interfaces:**
- Consumes: Task 1 `arac_kaydi`, `izinli_araclar`
- Produces: `is_istek.is_iste(ad, kanal: str | None, *, simdi=None, kadro=None, cagiran: str | None = None) -> IsSonuc` (kanal None → defter `kanal: null` + `cagiran`); `HindsightHafiza.ara(bot, soru, k=5)`; MCP araçları `is_iste` (şema `{"ad": str}`) ve `bot_hafizasi_ara` (şema `{"bot": str, "soru": str}`; `bot` kadroda aktif değilse reddedilir), çıktılar VERİ çitli (`sohbet.arac_bloku`) + scrub.

- [ ] **Step 1: Başarısız testler** — MCP `is_iste` → `is_istek` defterinde `kanal is None`, `cagiran == "mcp:sef"`; tavan MCP'den de işler; `bot_hafizasi_ara` sahte `_cagir`la recall isteği `bot-<hedef>` bankasına, dönen metin çitli + scrub'lı; `bot_hafizasi_ara` `karne` sunucusundan çağrılırsa izinli değil; `is_iste(ad, kanal="faks")` hâlâ `ValueError`; `kanal=None` ama `cagiran` yoksa `ValueError` (kimliksiz istek yok).
- [ ] **Step 2–6:** kırmızı → uygula → yeşil → mutasyon (`cagiran` zorunluluğunu kaldır; `ara`yı PATCH'e bağla — silme/değiştirme OLMAMALI; çiti kaldır) → kapsam (v597, v594, v596, v593, v592, v591, codelaw, v334, v382).
