"""codelaw.py — İKİ STATİK YASA (2026-07-21).

NEDEN VAR: 2026-07-21'de tek günde on üç hata çıktı ve **hiçbiri istisna fırlatmadı**. Denetim
iki YAPISAL taşıyıcı buldu; bu modül ikisini de kaynak koddan, çalışma zamanına hiç dokunmadan
ölçer:

  (4) SESSİZ YUTMA. `except Exception: pass` gerçek bir kusuru sessiz bir MİKTAR DEĞİŞİMİNE
      çevirir. En kötü örneği sessiz-hata dedektörünün KENDİ içindeydi: `starved.append(...)`
      satırı `starved` tanımlanmadan önce duruyordu ve çıplak bir `except Exception: pass`
      `NameError`'ı yutuyordu — yani sessiz hataları bulmak için var olan dedektör sessizce
      başarısız oluyordu. Kaçış yolu vardır ama AÇIK olmak zorundadır: `# sessiz-yutma: <gerekçe>`.
      "Üşendim"i "karar verdim ve nedenini yazdım"a çevirir; bütün mesele bu.

  (6) ÜRETİLİP TÜKETİLMEYEN ARTEFAKT. Yedi desenli bütünlük raporu diske yazıldı, API'den
      servis edildi — ve **hiçbir pano paneli okumadı**. Aynı şekilde `gate_checks` yalnız canlı
      motorda üretildiği için panonun karar-ağacı tablosu 144 satırın 144'ünde boştu. Kimsenin
      okumadığı bir artefakt, üretilmemiş artefakttan ayırt edilemez.

Bu modül SAF DENETİMDİR: durum değiştirmez, karar vermez, diske yazmaz. Yalnız "şu satırda sinyal
üretmeyen bir yakalayıcı var" ve "şu defteri kimse okumuyor" der.
"""
from __future__ import annotations

import ast
import copy
import pathlib
import re
from typing import Any

# ---------------------------------------------------------------------------
# (4) SESSİZ-YUTMA YASAĞI
# ---------------------------------------------------------------------------

# Kaçış yolu işareti. Gerekçe ZORUNLU: iki nokta üst üsteden sonra en az 4 anlamlı karakter.
# İşaretsiz sessizlik ihlaldir; gerekçesiz işaret de ihlaldir (aksi hâlde "# sessiz-yutma:" yazıp
# geçmek, `pass` yazmakla aynı şey olurdu).
MARKER_RE = re.compile(r"#\s*sessiz-yutma\s*:\s*(.+)$")
_MIN_GEREKCE = 4

# Sinyal sayılan çağrılar. obs.log/warn/alarm bu projenin kanonik kanalı; logging/print/traceback
# de sinyaldir (kanal kötü olabilir ama SESSİZ değildir).
SIGNAL_ATTRS = frozenset({
    "log", "warn", "warning", "alarm", "error", "exception", "critical", "info", "debug",
    "print_exc", "format_exc", "print_exception", "emit", "notify", "alert",
})
SIGNAL_NAMES = frozenset({"print", "log", "warn", "alarm", "repr_exc"})

_SKIP_DIRS = {"__pycache__", ".venv", "node_modules", ".git"}

# Bu turda BAŞKA iş kollarına ait olduğu için düzenlenemeyen dosyalar. İhlalleri BEYAN EDİLİR ve
# raporlanır — allowlist DEĞİL: yasa hepsini saymaya devam eder, yalnız "sıfır" iddiası düzenlenebilir
# yüzeyle sınırlıdır. Bir dosya bu listeden çıktığında ihlalleri anında teste düşer.
OTHER_TRACK_FILES = frozenset({"analytics.py", "shadow_model.py", "sieve.py", "watchdog.py",
                               "ledgers.py", "mutation.py", "backtest.py"})

# TARAYICININ KENDİ KÖRLÜĞÜ. Ayrıştırılamayan ya da okunamayan her dosya BURAYA yazılır ve
# report()'ta görünür. Neden: bu modülün var oluş sebebi "sessiz hataları bulan dedektörün sessizce
# başarısız olması"ydı — `except SyntaxError: continue` yazıp devam etmek, tam olarak o hatayı
# tekrarlamak olurdu. Bozuk bir modül taranmadıysa, sıfır ihlal RAPORU VAKUMDUR.
UNSCANNED: list[dict] = []


def _note_unscanned(path, exc: BaseException, phase: str) -> None:
    rec = {"file": str(path), "phase": phase, "error": f"{type(exc).__name__}: {exc}"}
    if rec not in UNSCANNED:
        UNSCANNED.append(rec)


def _py_files(root: str):
    for f in sorted(pathlib.Path(root).rglob("*.py")):
        if any(p in _SKIP_DIRS for p in f.parts):
            continue
        yield f


def _enclosing(tree: ast.AST) -> list[tuple[ast.ExceptHandler, str]]:
    """Her ExceptHandler'ı içinde bulunduğu fonksiyon/sınıf yolu ile eşleştirir."""
    out: list[tuple[ast.ExceptHandler, str]] = []

    def visit(node: ast.AST, scope: str) -> None:
        for child in ast.iter_child_nodes(node):
            nxt = scope
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                nxt = f"{scope}.{child.name}" if scope else child.name
            if isinstance(child, ast.ExceptHandler):
                out.append((child, scope or "<module>"))
            visit(child, nxt)

    visit(tree, "")
    return out


def _has_signal(h: ast.ExceptHandler) -> bool:
    """Yakalayıcı bilgi ÜRETİYOR mu? Üç yoldan biri yeterlidir:
      1. yeniden fırlatıyor (bare raise ya da yeni istisna),
      2. bir kayıt/uyarı çağrısı yapıyor (obs.*, logging.*, print, traceback.*),
      3. istisnayı `as e` ile bağlayıp gövdede KULLANIYOR — yani hata bilgisi bir yere taşınıyor
         (`errors.append(str(e))`, `return {"error": str(e)}` gibi).
    Hiçbiri yoksa hata orada ölür: `pass`, çıplak `continue`, ya da sessiz bir yedek atama."""
    for stmt in h.body:
        for n in ast.walk(stmt):
            if isinstance(n, ast.Raise):
                return True
            if isinstance(n, ast.Call):
                f = n.func
                if isinstance(f, ast.Attribute) and f.attr in SIGNAL_ATTRS:
                    return True
                if isinstance(f, ast.Name) and f.id in SIGNAL_NAMES:
                    return True
    if h.name:
        for stmt in h.body:
            for n in ast.walk(stmt):
                if isinstance(n, ast.Name) and n.id == h.name:
                    return True
    return False


def _handler_span(h: ast.ExceptHandler) -> tuple[int, int]:
    end = getattr(h, "end_lineno", None) or h.lineno
    for stmt in h.body:
        end = max(end, getattr(stmt, "end_lineno", stmt.lineno))
    return h.lineno, end


def marker_of(lines: list[str], start: int, end: int) -> str | None:
    """`# sessiz-yutma: <gerekçe>` işaretini yakalayıcının ÜSTÜNDEKİ satırda ya da İÇİNDE arar.
    ast yorumları düşürdüğü için kaynak metni okumak zorundayız — kaçış yolunun bilinçli
    olmasının bedeli bu."""
    lo = max(1, start - 1)
    for i in range(lo, min(end, len(lines)) + 1):
        m = MARKER_RE.search(lines[i - 1])
        if m and len(m.group(1).strip().strip("-—:")) >= _MIN_GEREKCE:
            return m.group(1).strip()
    return None


def _has_bare_marker(lines: list[str], start: int, end: int) -> bool:
    """Gerekçesiz `# sessiz-yutma:` var mı? (Onurlu rapor için: işaret koyulmuş ama boş.)"""
    lo = max(1, start - 1)
    for i in range(lo, min(end, len(lines)) + 1):
        m = MARKER_RE.search(lines[i - 1])
        if m and len(m.group(1).strip().strip("-—:")) < _MIN_GEREKCE:
            return True
        if m:
            return False
    return bool(any("sessiz-yutma" in lines[i - 1] for i in range(lo, min(end, len(lines)) + 1)))


def scan_source(src: str, filename: str = "<string>") -> list[dict]:
    """Tek bir kaynak metnindeki sinyalsiz yakalayıcılar. (Testlerin pozitif kontrolü buradan
    beslenir — tarayıcının gerçekten çalıştığını sentetik bir kaynakla kanıtlayabilmek için.)"""
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        _note_unscanned(filename, e, "silent_handlers")
        return []
    lines = src.splitlines()
    out: list[dict] = []
    for h, scope in _enclosing(tree):
        if _has_signal(h):
            continue
        start, end = _handler_span(h)
        note = " ".join(lines[start - 1].strip().split())
        body = " ".join(lines[min(start, len(lines))].strip().split()) if start < len(lines) else ""
        out.append({
            "file": filename,
            "line": h.lineno,
            "function": scope,
            "note": f"{note} -> {body}"[:160],
            "marker": marker_of(lines, start, end),
            "bare_marker": _has_bare_marker(lines, start, end),
        })
    return out


def silent_handlers(root: str = "meridian", include_annotated: bool = False) -> list[dict]:
    """Sinyal üretmeyen bütün `except` blokları. Varsayılan olarak yalnız İŞARETSİZ olanlar —
    yani ihlaller — döner; `include_annotated=True` gerekçeli olanları da listeler (denetim için)."""
    out: list[dict] = []
    for f in _py_files(root):
        try:
            src = f.read_text()
        except OSError as e:
            _note_unscanned(f, e, "silent_handlers")
            continue
        for hit in scan_source(src, str(f)):
            if hit["marker"] and not include_annotated:
                continue
            out.append(hit)
    return out


def annotated_handlers(root: str = "meridian") -> list[dict]:
    """Bilinçli olarak sessiz bırakılmış yakalayıcılar — gerekçeleriyle. Bu liste UZARSA yasa
    aşınıyor demektir; sayısı raporlanabilsin diye ayrı durur."""
    return [h for h in silent_handlers(root, include_annotated=True) if h["marker"]]


# ---------------------------------------------------------------------------
# (6) ARTEFAKT TÜKETİM GRAFİĞİ
# ---------------------------------------------------------------------------

WRITE_CALLS = frozenset({"write_json", "write_jsonl", "append_jsonl", "update_json",
                         "update_jsonl", "merge_dated_jsonl"})
READ_CALLS = frozenset({"read_json", "read_jsonl"})

# Kodda BAŞKA BİR MODÜLDEN doğrudan okuyucusu olmaması meşru olan artefaktlar. Beyan edilmemiş bir
# "yazılıyor ama okunmuyor" artefaktı İHLALDİR — çünkü 2026-07-21'de tam olarak öyle bir dosya
# (yedi desenli bütünlük raporu) üretilip hiç okunmamıştı. Buradaki her satır bir KARARDIR, muafiyet
# değil: ya tüketici bir ERİŞİMCİ FONKSİYON üzerinden dolaylıdır (statik tarama fonksiyon içindeki
# okumayı yazan modüle sayar), ya dosya modülün KENDİ işletim durumudur (önbellek, alarm tekilleştirme,
# iş kuyruğu) ve dışarıdan okunması zaten anlamsızdır.
DECLARED_SINKS: dict[str, str] = {
    # NOT (2026-07-27): `finviz_universe.json` buradan ÇIKARILDI. Beyanı doğruydu — okuyucusu
    # yalnız kendi modülündeydi, statik graf onu göremiyordu. Artık DIŞ bir okuyucusu var:
    # `marketview.build` keşfedilen evreni bars'ta olmayan semboller için satır üretmekte
    # kullanıyor ve gerekçesini panonun Piyasa sekmesine taşıyor. Muafiyet işi bittikten sonra
    # da yerinde dursaydı liste "kimsenin bakmadığı çöplüğe" dönerdi (yukarıdaki kural).
    "monotonic_amnesty.json": "watchdog.grant_amnesty yazar, watchdog._amnesty_index okur (aynı modül "
                              "→ statik graf göremez). İçerik ÖLÜ DEĞİL: monotonicity_report onu "
                              "'amnestied' alanıyla dışa verir ve pano gerekçesiyle birlikte gösterir. "
                              "Meşru küçülmenin (re-seed) yazılı kaydı — bkz. 2026-07-22 trades 129→96",
    # --- erişimci fonksiyon üzerinden dolaylı tüketim (pano → api → fonksiyon → dosya) ---
    # NOT (2026-07-26): `learning_loop_open.json` buradan ÇIKARILDI. Beyanı "watchdog makullük
    # dedektörü toplamı okur" diyordu ama böyle bir okuyucu YOKTU — beyanın kendisi eksik tüketiciyi
    # örtüyordu. Okuyucu artık gerçek (`watchdog.parity_report` → `learning_loop` satırı → pano), o
    # yüzden artefakt bir lağım değil; beyan kalsaydı `stale_sinks` ihlali olurdu (bir muafiyet, işi
    # bittikten sonra da yerinde durursa liste 'kimsenin bakmadığı çöplüğe' döner).
    "hypothesis_id_hwm.json": "memory.record yazar, memory.next_id okur (aynı modül → statik graf "
                              "göremez). Kimlik yüksek-su işareti: defter TAMAMEN silinse bile "
                              "numaralar geri sarmasın, arşivlenmiş satırlarla çakışmasın",
    "skill_revisions.json": "skill_evolve.revisions() okur (tip-güvenli tek okuyucu); api /api/skills "
                            "ve selfreview.build() oradan geçer → pano 'Revizyon taslakları' kartı. "
                            "HAM okuma bilinçli olarak kaldırıldı (2026-07-22): defter sözlük şeklinde "
                            "bozulduğunda ham okuma iki mekanizmayı 860 kez çökertmişti",
    "brain_cooldown.json": "hermes.brain_cooldown()/active_brain() okur; hermes_runtime.status() "
                           "brain_availability olarak dışa verir → api /api/hermes → pano "
                           "'Sağlayıcı durumu' satırı. 429 sonrası soğuma penceresi burada tutulur "
                           "(2026-07-22) — aynı modül içinde okunduğu için statik graf göremez",
    "bar_source_seams.json": "adapters.data.seam_report() okur; api /api/diagnostics "
                             "pipeline.bar_source_seams → pano Bölüm 4 'Kaynak dikişi' satırı. "
                             "Uyarı susturuldu (250 sembol × her tur log çöplüğüydü) ama DURUM "
                             "burada sayılıyor ve panoda görünüyor — susturmak yok saymak değildir",
    "massive_grouped_last.json": "adapters.massive.snapshot() okur (aynı modül → statik graf göremez; "
                                 "dosya adı SNAPSHOT_FILE sabitiyle geçer). Massive'in grouped-daily "
                                 "ucundan gelen GÜNLÜK tüm-piyasa anlık görüntüsü: 250 sembollük bir "
                                 "tazeleme bunu TEK çağrıyla doldurup hepsini buradan okur. Diskte "
                                 "tutulmasının sebebi süreç sınırı — zamanlayıcı ve api AYRI "
                                 "süreçlerdir; bellek-içi memo olsaydı her süreç bir çağrı daha yakardı",
    "massive_verify.json": "adapters.massive.verify_state()/write_enabled()/status() okur (aynı modül). "
                           "AYARLAMA (adjusted) ÖLÇEĞİ ÖLÇÜMÜNÜN HÜKMÜ: Massive'in barları yazım "
                           "zincirine girsin mi? `--dogrula` yazar, kapı okur. 'uyumsuz' yazarsa kapı "
                           "kapanır ve zincir FMP/Cboe'de kalır — yani bu dosya fiilen bir EMNİYET "
                           "ANAHTARIDIR, rapor değil",
    "massive_crosscheck.json": "adapters.data.crosscheck_report() okur; Massive ile zincirin yazdığı "
                               "kapanışların ÖRTÜŞEN günlerdeki farkının birikimi (kaç bar kıyaslandı, "
                               "kaçı toleransı aştı, en kötüsü hangi sembolde). Alarm tek başına "
                               "'kanıt üretip tüketmemek' olurdu: hangi tarafın haklı olduğu ancak bu "
                               "sayılardan çıkar",
    "agent_tooluse.json": "hermes.integrations_status() okur; api /api/hermes → pano 'entegrasyonlar' "
                          "panelinde MCP araç kullanım oranı olarak görünür",
    "oos_erosion.json": "oos_erosion.record() yazar, oos_erosion.report()/status() okur (aynı modül "
                        "→ statik graf göremez). DIŞ tüketici gerçek: api /api/diagnostics "
                        "mlops.oos_erosion → pano Edge kartı 'OOS aşınması' satırı (sorgu sayacı + "
                        "yürürlükteki ek marj). Ayrıca reflect._gate_eval her değerlendirmede "
                        "status() ile okuyup marjı uygular — yani içerik ölü değil, kapı çıtasını "
                        "fiilen belirliyor (Aşama 2.2, 2026-07-28)",
    "approvals.jsonl": "api.py hem yazar hem okur ve /api/approvals ile panoya servis eder — tüketici "
                       "pano JS'idir (app.js 'approvals')",
    "skill_recommendations.jsonl": "skills.pending_recommendations() okur; api /api/hermes içindeki "
                                   "skill_recommendations alanı olarak panoya çıkar (app.js render eder)",
    "sprint_status.json": "sprint.status() okur; /api/sprint ve /api/hermes üzerinden panonun sprint "
                          "paneline gider",
    "integrity_audit_log.json": "integrity_registry.coverage_report() okur; api_diagnostics 'coverage' "
                                "alanında panoya çıkar — bileşen başına son denetim tarihi",
    "fmp_usage.json": "adapters.fmp.usage() okur; api_diagnostics pipeline.fmp_usage alanında panoya "
                      "çıkar (429/kota kesintilerinin sayısal izi)",
    "regime_trigger.json": "DeferredRegimeBudgetTrigger kendi durumunu taşır; dışarıdan okuyan "
                           "analytics/loop dosyaya değil SINIFA bakar — durum sınıfın iç meselesidir",
    "sp500_constituents.json": "endeks bileşen listesinin ağ önbelleği; tüketici adapters.constituents "
                               "erişimcileridir, dosya değil",

    # --- Y4 veri katmanı (ROADMAP §3.4): TÜKETİCİ BİLİNÇLİ OLARAK ERTELENDİ ---------------------
    # Bu dört artefaktın bugünkü tüketicisi adaptörlerin KENDİ CLI'ı ve v117 testleridir; loop/api/cf
    # bağlantısı SONRAKİ tura ertelendi. Erteleme bir üşenme değil, ÖLÇÜLMÜŞ bir gerekçe:
    #   * insider: rutin/fırsatçı sınıflaması 3 YILLIK bir geçmiş penceresi ister. FMP'nin
    #     `insider-trading/search` ucu ücretsiz planda HTTP 402 döndüğü CANLI DOĞRULANDI
    #     (2026-07-29), yani pencere ancak `/latest` akışının günlük birikmesiyle dolar. Bugün
    #     bağlanacak bir tüketici, `siniflanamadi` ile dolu bir dosyayı sinyal sanardı — dosyanın
    #     `kapsam.siniflama_hazir_mi` alanı tam da o bağlantının NE ZAMAN yapılabileceğini söyler.
    #   * shortinterest: "filtreli vs filtresiz" karşı-olgusal defterde ÖLÇÜLMEDEN bir kaçınma
    #     filtresi kapıya bağlanırsa, hiç ölçülmemiş bir kısıt canlı stratejiyi daraltmış olur.
    # Beyan bu yüzden burada duruyor: erteleme yazılı, gerekçeli ve süresi ölçülebilir. Tüketici
    # bağlandığı gün bu satırlar KALDIRILMALI — yoksa `stale_sinks` ihlali olarak geri döner.
    "insider_trades.json": "Form 4 ham defteri (artımlı; su işareti + kapsam burada). Okuyucusu aynı "
                           "modüldeki insider.ozet()/durum() — statik graf aynı-modül okumayı göremez. "
                           "DIŞ tüketici ertelendi: 3 yıllık sınıflama penceresi dolmadan bağlanamaz "
                           "(FMP search ucu ücretsiz planda 402; bkz. yukarıdaki gerekçe)",
    "insider_signals.json": "sembol-başına fırsatçı net alım özeti. Bugünkü tüketici CLI + "
                            "tests/test_insider_v117.py; loop/api bağlantısı `kapsam.siniflama_hazir_mi` "
                            "True olana kadar BİLİNÇLİ olarak ertelendi — bugün bağlanan bir okuyucu "
                            "`siniflanamadi` dolu bir dosyayı sinyal sanardı",
    "short_interest.json": "FINRA kısa pozisyon özeti + bayatlık damgası (yayın tarihi, gecikme, "
                           "bayat_mi). Bugünkü tüketici CLI + tests/test_shortinterest_v117.py; kaçınma "
                           "filtresi olarak kapıya bağlanması, karşı-olgusal defterde 'filtreli vs "
                           "filtresiz' ÖLÇÜLDÜKTEN sonraki tura ertelendi",
    "short_interest_float.json": "float/sharesOutstanding önbelleği (FMP profile, sembol başına 1 istek "
                                 "olduğu için TAVANLI ve kalıcı). Okuyucusu aynı modüldeki "
                                 "shortinterest.ozet() — SI%float paydası; dosya kendi başına bir "
                                 "sinyal değil, kota tasarrufu için tutulan yardımcı defterdir",

    # NOT (2026-07-30, Hafta 3b): `shadow_variants.jsonl` buradan ÇIKARILDI — beyan SÜRELİYDİ ve
    # devri yazılıydı ("Hafta 3b `/api/diagnostics`e özeti bağladığı gün BU SATIR KALDIRILMALI").
    # Devir yapıldı: `analytics.shadow_variant_summary()` defteri DIŞ bir modülden okuyor,
    # `/api/diagnostics` onu taşıyor, pano gölge-varyant kartını çiziyor (varyant başına son karar +
    # kümülatif ayrışma sayısı) ve defter `ledgers.CONTRACTS`e girdi. Muafiyet işi bittikten sonra
    # da yerinde dursaydı liste "kimsenin bakmadığı çöplüğe" dönerdi — üstteki kuralın kendisi.

    # --- modülün KENDİ işletim durumu: dışarıdan okunması yanlış olurdu ---
    "composite_budget.json": "H4'ün HAFTALIK YOKLAMA BÜTÇESİ sayacı (hermes_composite). Yazan ve okuyan "
                             "AYNI modül (`_budget_take`/`_budget_used`) → statik graf göremez. İçerik ölü "
                             "DEĞİL: sayaç `queue_status()` üzerinden /api/diagnostics'e ve panonun Hermes "
                             "karnesi kartına 'bütçe kalan N/3' olarak çıkar. Dosya modülün kendi işletim "
                             "durumudur (iş kuyruğu sayacı) — bir başka modülün ham okuması anlamsız olurdu, "
                             "çünkü bütçe düşürme kararı kilitli oku-değiştir-yaz içinde verilmek zorunda",
    "notify_sent.json": "obs._maybe_notify'ın token başına 6 saatlik susturma penceresi — sırf bildirim "
                        "tekrarını kesmek için var; başka bir modülün okuması anlamsız",
    "inc_cache.json": "reflect'in incumbent walk-forward önbelleği (bar revizyonuna bağlı); yalnız "
                      "hesabı hızlandırır, hiçbir karara girmez",
    "probe_cache.json": "reflect'in sonda önbelleği — aynı gerekçe; içeriği türetilmiş, kaynak değil",
    "bars_source.json": "bir ticker'ın barlarını hangi kaynağın yazdığının sabitlemesi; adapters.data "
                        "kendi kaynak seçimini tutarlı tutmak için okur",
    "scan_debt.json": "loop'un kendi İŞ KUYRUĞU (barı geç gelen ticker'lar). Dışarıya taşıyan şey dosya "
                      "değil olaylardır: scan_debt_expired / scan_debt_resolved",

    # --- alarm tekilleştirme / bütünlük dedektörü iç durumu (watchdog iş kolu) ---
    "watchdog_alarmed.json": "alarm tekilleştirme durumu — aynı alarmın her turda yeniden basılmasını "
                             "engeller; dışarıya çıkan şey alarmın kendisidir",
    "integrity_alarmed.json": "aynı disiplin, bütünlük alarmları için",
    "mechanism_beats.json": "mekanizma nabızları (hangi mekanizma en son ne zaman çalıştı); watchdog "
                            "bayatlık kararını buradan verir ve sonucu integrity_report ile dışarı taşır",
    # NOT (2026-08-01): `monotonic_state.json` buradan ÇIKARILDI. Beyanı doğruydu — okuyucusu yalnız
    # kendi modülündeydi (watchdog.monotonicity_report), statik graf onu "dış okuyucusu yok" diye
    # görüyordu. Artık DIŞ bir okuyucusu var: `sermaye._peak_affi` affın `was` değerini dedektörün
    # KENDİ TABANINDAN okur — kitaptaki `peak_equity`den değil, çünkü af TAM eşleşme ister ve
    # dedektör kıyası bu dosyayla yapar. İkisi ayrışsaydı af hiç tutmaz, bayrak sonsuza dek kırmızı
    # kalırdı. Muafiyet işi bittikten sonra da yerinde dursaydı liste "kimsenin bakmadığı çöplüğe"
    # dönerdi (bu sözlüğün kendi kuralı; aynı gerekçeyle finviz_universe ve learning_loop_open çıktı).
    "ownership_state.json": "sahiplik dedektörünün önceki ölçümü — aynı gerekçe",
    "bars_fingerprint.json": "bar dosyalarının parmak izi; determinizm dedektörünün karşılaştırma tabanı",

    # --- paralel iş kolu (bu turda düzenlenemeyen dosyalar) ---
    "sieve.json": "eleme muhasebesi, sieve.py iş kolunun ürünü. ŞU AN tek okuyucusu kendi testidir "
                  "(tests/test_sieve_v58.py); panoya bağlanması o iş kolunun işi — burada beyan "
                  "ediliyor ki 'kimse okumuyor' gerçeği kayıt altında kalsın, sessizce değil",
}


def _module_consts(tree: ast.Module) -> dict[str, str]:
    """Modül düzeyindeki string sabitleri (ledgers.declared_writers'daki çalışan öncül taklit
    edildi): `_EVENTS = "events.jsonl"` gibi adların çözülmemesi, yazarı görünmez yapardı."""
    consts: dict[str, str] = {}
    for n in tree.body:
        if isinstance(n, ast.Assign) and isinstance(n.value, ast.Constant) \
                and isinstance(n.value.value, str):
            for t in n.targets:
                if isinstance(t, ast.Name):
                    consts[t.id] = n.value.value
        elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name) \
                and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str):
            consts[n.target.id] = n.value.value
    return consts


def _global_consts(root: str) -> dict[str, str]:
    """Modüller arası sabit tablosu: `from .obs import _EVENTS` gibi ödünç alınmış adlar için
    ikinci şans. Çakışan adlar (aynı ad, farklı değer) DÜŞÜRÜLÜR — yanlış çözmektense
    `unresolved` demek dürüsttür."""
    seen: dict[str, str | None] = {}
    for f in _py_files(root):
        try:
            tree = ast.parse(f.read_text())
        except (SyntaxError, OSError) as e:
            _note_unscanned(f, e, "artifact_graph:consts")
            continue
        for k, v in _module_consts(tree).items():
            if k in seen and seen[k] != v:
                seen[k] = None
            else:
                seen.setdefault(k, v)
    return {k: v for k, v in seen.items() if v}


def _looks_like_artifact(s: str) -> bool:
    return s.endswith((".json", ".jsonl"))


_GRAPH_CACHE: dict = {}


def _src_stamp(root: str) -> tuple:
    """Kaynak ağacının parmak izi: dosya sayısı + en yeni değişiklik zamanı.
    61 stat() çağrısı, mikrosaniyeler — ayrıştırmanın yanında ölçülemez."""
    ps = sorted(pathlib.Path(root).rglob("*.py"))
    return (len(ps), max((q.stat().st_mtime_ns for q in ps), default=0))


def artifact_graph(root: str = "meridian") -> dict:
    """Her artefakt için: yazarlar, okuyucular ve BAŞKA hiçbir modül tarafından okunmuyorsa
    `unread` bayrağı. Çözülemeyen adlar (f-string, değişken, çağrı) sessizce yutulmaz —
    `unresolved` listesine yazılır; tarayıcının kendi körlüğünü gizlemesi bu yasanın ihlali olurdu."""
    # ÖNBELLEK — KAYNAK MTIME'INA BAĞLI (2026-07-28). Bu fonksiyon projenin TÜM Python
    # kaynağını ast ile ayrıştırır ve panonun /api/diagnostics ucundan HER Operasyon açılışında
    # iki kez çağrılıyordu. Ölçüm: uç 4,18 sn; 1,17 sn'i burası, 419 ast.parse + 614.836 ast.walk.
    # Sonuç yalnız kaynağa bağlı: sunucu koşarken kaynak değişmez, değişirse damga değişir ve
    # önbellek kendiliğinden düşer. Zaman aşımı YOK — bayatlık değil, doğruluk garantisi.
    _key = (root, _src_stamp(root))
    _hit = _GRAPH_CACHE.get(_key)
    if _hit is not None:
        return copy.deepcopy(_hit)   # çağıran mutasyonu önbelleği kirletmesin

    gconsts = _global_consts(root)
    arts: dict[str, dict[str, Any]] = {}
    unresolved: list[dict] = []

    for f in _py_files(root):
        try:
            src = f.read_text()
            tree = ast.parse(src)
        except (SyntaxError, OSError) as e:
            _note_unscanned(f, e, "artifact_graph")
            continue
        consts = _module_consts(tree)
        mod = f.name
        for n in ast.walk(tree):
            if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.args):
                continue
            attr = n.func.attr
            role = ("writer" if attr in WRITE_CALLS else
                    "reader" if attr in READ_CALLS else None)
            if role is None:
                continue
            a = n.args[0]
            name = None
            if isinstance(a, ast.Constant) and isinstance(a.value, str):
                name = a.value
            elif isinstance(a, ast.Name):
                name = consts.get(a.id) or gconsts.get(a.id)
            elif isinstance(a, ast.Attribute):
                name = gconsts.get(a.attr)
            if name is None or not _looks_like_artifact(name):
                unresolved.append({"file": str(f), "line": n.lineno, "call": attr,
                                   "role": role, "arg": ast.dump(a)[:80]})
                continue
            rec = arts.setdefault(name, {"writers": set(), "readers": set(),
                                         "writer_sites": [], "reader_sites": []})
            rec["writers" if role == "writer" else "readers"].add(mod)
            rec[f"{'writer' if role == 'writer' else 'reader'}_sites"].append(f"{mod}:{n.lineno}")

    out: dict[str, dict] = {}
    for name, rec in sorted(arts.items()):
        writers, readers = sorted(rec["writers"]), sorted(rec["readers"])
        # "başka bir modül okuyor mu?" — kendi yazdığını kendi geri okuyan modül tüketici sayılmaz;
        # 2026-07-21'deki bütünlük raporu da kendi içinde tutarlıydı, eksik olan DIŞARIDAN okunmasıydı.
        external = sorted(set(readers) - set(writers))
        out[name] = {"writers": writers, "readers": readers, "external_readers": external,
                     "writer_sites": sorted(rec["writer_sites"]),
                     "reader_sites": sorted(rec["reader_sites"]),
                     "unread": bool(writers) and not external}

    unread = [k for k, v in out.items() if v["unread"]]
    _res = {"artifacts": out,
            "unresolved": unresolved,
            "unread": sorted(unread),
            "declared_sinks": sorted(k for k in unread if k in DECLARED_SINKS),
            "violations": sorted(k for k in unread if k not in DECLARED_SINKS),
            "stale_sinks": sorted(k for k in DECLARED_SINKS if k in out and not out[k]["unread"])}
    _GRAPH_CACHE.clear()
    _GRAPH_CACHE[_key] = _res
    return copy.deepcopy(_res)


def dashboard_mentions(term: str, path: str = "meridian/web/app.js") -> bool:
    """Panonun gerçekten okuyup okumadığını app.js'i tarayarak DOĞRULAR (salt okuma). "Panoda
    gösteriliyor" gerekçesi, kanıtlanabilir olmadıkça gerekçe değildir."""
    try:
        return term in pathlib.Path(path).read_text()
    except OSError as e:
        # Pano dosyası okunamadıysa "pano okumuyor" DEĞİL, "doğrulayamadım" doğru cevaptır; körlük
        # kayda geçer, aksi hâlde gerekçe kanıtsız kabul edilmiş olurdu.
        _note_unscanned(path, e, "dashboard_mentions")
        return False


def report(root: str = "meridian") -> dict:
    """İki yasanın birlikte durumu — tek bakışta 'kaç ihlal' cevabı."""
    sil = silent_handlers(root)
    ann = annotated_handlers(root)
    graph = artifact_graph(root)
    return {"silent_handlers": len(sil), "annotated_handlers": len(ann),
            "artifacts": len(graph["artifacts"]), "unread": graph["unread"],
            "artifact_violations": graph["violations"],
            "unresolved_artifact_calls": len(graph["unresolved"]),
            "unscanned": list(UNSCANNED),          # tarayıcının göremedikleri — sıfır ihlal iddiasının şartı
            "ok": not sil and not graph["violations"] and not UNSCANNED}
