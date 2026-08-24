"""codelaw.py — iki statik yasanın (sessiz-yutma, okuyucusuz-yazım) kaynak-kod denetçisi.

Tek günde çıkan bir hata dalgasının hiçbiri istisna fırlatmamıştı; denetim iki YAPISAL taşıyıcı
buldu ve bu modül ikisini de çalışma zamanına hiç dokunmadan, ast ile kaynaktan ölçer:

  YASA 4 — SESSİZ YUTMA: sinyal üretmeyen `except` bloğu ihlaldir; gerçek bir kusur sessiz bir
  miktar değişimine dönüşür. Kaçış yolu vardır ama AÇIK olmak zorundadır: `# sessiz-yutma:
  <gerekçe>` (gerekçesiz işaret de ihlal — "üşendim"i "karar verdim ve nedenini yazdım"a çevirir).
  Girişler: `scan_source`/`silent_handlers`/`annotated_handlers`; sinyal tanımı SIGNAL_ATTRS/
  SIGNAL_NAMES. Ders kalıcı: sessiz hataları bulan dedektörün kendisi çıplak bir `except` yüzünden
  sessizce başarısız olmuştu — bekçinin kendi körlüğünü bilmemesi bekçiliğin tersidir.

  YASA 6 — ÜRETİLİP TÜKETİLMEYEN ARTEFAKT: kimsenin okumadığı artefakt, üretilmemişten ayırt
  edilemez. `artifact_graph` her `store` okuma/yazma çağrısını yazar/okuyucu grafına çözer;
  çözemediğini ADLI `unresolved` kovasına düşürür ve her erişim biçimini sayar (`access_patterns`);
  taranamayan dosya `UNSCANNED`e yazılır — sıfır-ihlal iddiası eksik taramaya dayanamaz. Meşru
  okuyucusuzluk BEYANLA olur: `DECLARED_SINKS` (gerekçeli tekil beyan), `DECLARED_SINK_PATTERNS`
  (koddan türetilen desen beyanı — tarihli/dinamik adlar), `HUMAN_INVOKED_SINKS` (dış okuyucusu
  olan ama çağıranı insan olan defter). Beyanın kendisi de denetlenir: `declared_claims`/
  `stale_claims`/`unverifiable_claims` iddiaları fonksiyon-çağrı düzeyinde sınar.

Modül SAF DENETİMDİR: durum değiştirmez, karar vermez, diske yazmaz; yalnız kaynak ağacını
(meridian/*.py) okur. Toplu hüküm `report()` ile panoya ve bekçiye çıkar."""
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
OTHER_TRACK_FILES = frozenset({"shadow_model.py", "sieve.py", "watchdog.py",
                               "ledgers.py", "mutation.py", "backtest.py"})

# TARAYICININ KENDİ KÖRLÜĞÜ. Ayrıştırılamayan ya da okunamayan her dosya BURAYA yazılır ve
# report()'ta görünür. Neden: bu modülün var oluş sebebi "sessiz hataları bulan dedektörün sessizce
# başarısız olması"ydı — `except SyntaxError: continue` yazıp devam etmek, tam olarak o hatayı
# tekrarlamak olurdu. Bozuk bir modül taranmadıysa, sıfır ihlal RAPORU VAKUMDUR.
UNSCANNED: list[dict] = []


# KAYNAK OKUMA SÖZLEŞMESİ (bu modüldeki HER `read_text` için).
#   (a) `encoding="utf-8"` AÇIKÇA verilir. Verilmezse çözücü `locale.getpreferredencoding()`e
#       düşer: `LC_ALL=C` bir kabukta (CI kabukları, systemd birimleri, cron) kodlama ASCII olur
#       ve bu deponun Türkçe kaynak dosyalarının neredeyse HEPSİ okunamaz hâle gelir. Tarayıcının
#       hükmü koştuğu kabuğun yerel ayarına bağlı olamaz.
#   (b) `except` demetinde `ValueError` BULUNUR. `UnicodeDecodeError` bir `ValueError` alt
#       sınıfıdır ve `OSError`ın altında DEĞİLDİR; demet yalnız `(SyntaxError, OSError)` olduğu
#       sürece kodlaması bozuk tek bir dosya, tarayıcıyı UNSCANNED'e yazdırmak yerine ÇÖKERTİRDİ.
#       Bu, bu modülün var oluş sebebinin tam tersidir: bekçi kendi körlüğünü RAPOR eder, körlükte
#       ölmez. Okunamayan dosya `UNSCANNED`e düşer ve `report()["ok"]` bu yüzden False olur.
def _note_unscanned(path, exc: BaseException, phase: str) -> None:
    """Taranamayan dosyayı `UNSCANNED` defterine (dosya + evre + hata TÜRÜ) yazar; aynı kayıt
    iki kez düşmez. Tarayıcının kendi körlüğü sessiz kalmasın diye: eksik tarama raporda görünür."""
    rec = {"file": str(path), "phase": phase, "error": f"{type(exc).__name__}: {exc}"}
    if rec not in UNSCANNED:
        UNSCANNED.append(rec)


def _py_files(root: str):
    """`root` altındaki `.py` dosyalarını ad sırasıyla üretir; `_SKIP_DIRS` (`__pycache__`,
    `.venv`, `node_modules`, `.git`) altında kalan yollar atlanır.

    ELEME KÖK ALTINDA YAPILIR, MUTLAK YOLDA DEĞİL. Eski hâl `f.parts` diyordu, yani yolun
    TÜM bileşenlerini — deponun KENDİSİ `.venv` (ya da `.git`, `node_modules`) adlı bir dizinin
    altında duruyorsa her dosya eleniyor, tarayıcı SIFIR dosya dönüyor ve "ihlal yok" diyordu.
    Sıfır-ihlal, sıfır-tarama demekti: bekçinin kendi körlüğünü yeşil sanması. Eleme artık
    `f.relative_to(kok).parts` üzerindedir — karar deponun NEREYE kurulduğuna değil, kökün
    ALTINDAKİ yapıya bakar."""
    kok = pathlib.Path(root)
    for f in sorted(kok.rglob("*.py")):
        if any(p in _SKIP_DIRS for p in f.relative_to(kok).parts):
            continue
        yield f


# ---------------------------------------------------------------------------
# KAYNAK OKUMA + AYRIŞTIRMA MEMOSU — AYNI AĞACI ALTI KEZ AYRIŞTIRMAYI BİTİRİR
# ---------------------------------------------------------------------------
# ÖLÇÜM (2026-08-16, bu makine): soğuk `report()` 20,09 sn · 576 `ast.parse` · 110,5 MB tepe
# bellek. 576 = 96 modül × 6 tam gezinti: `silent_handlers`, `annotated_handlers`,
# `_global_consts` (İKİ kez — hem `artifact_graph` hem `declared_claims` çağırıyor),
# `artifact_graph`, `declared_claims`. Sıcak yolda bile 192 kalıyordu (sonuç önbellekleri
# yalnız İKİ fazı kurtarıyor, geri kalan dördü her çağrıda yeniden ayrıştırıyordu).
#
# MEMO SONUÇ DEĞİL GİRDİ ÖNBELLEĞİDİR ve bu ayrım önemli: `_GRAPH_CACHE`/`_CLAIMS_CACHE` bir
# taramanın ÇIKTISINI saklar (ve körlüğünü — bkz. önbellek sözleşmesi bloğu); bu memo yalnız
# "aynı dosyayı aynı mtime'da ikinci kez okuma/ayrıştırma" der. Dolayısıyla körlük sözleşmesiyle
# ilgisi YOKTUR: ayrıştırma DÜŞERSE memoya hiçbir şey girmez, istisna çağırana aynen çıkar ve
# `_note_unscanned` her fazda eskisi gibi çalışır. Başarısızlığı önbelleğe koymak, körlük kaydını
# tek faza indirir ve fazların birbirinden bağımsız rapor verme özelliğini bozardı.
#
# GEÇERSİZLEŞTİRME DOSYA BAŞINADIR (`st_mtime_ns` + `st_size`): tek bir dosya değişince yalnız o
# girdi düşer. Sunucu koşarken kaynak değişmez; değiştiği an ilgili girdi kendiliğinden yenilenir.
_KAYNAK_MEMO: dict[str, tuple[tuple, str]] = {}
_AST_MEMO: dict[str, tuple[tuple, ast.Module]] = {}


def _dosya_damgasi(path) -> tuple:
    """Tek dosyanın parmak izi: (mtime_ns, boyut). `stat` çağrısı mikrosaniyeler — ayrıştırmanın
    yanında ölçülemez. Boyut da bakılır: aynı ns içinde yapılan iki yazım (testlerin tmp_path'i)
    yalnız mtime'a bakan bir memoyu kandırabilirdi."""
    st = pathlib.Path(path).stat()
    return (st.st_mtime_ns, st.st_size)


def _kaynak_oku(path) -> str:
    """Dosya metnini (utf-8) memodan ya da diskten verir. İstisnalar AYNEN yukarı çıkar —
    çağıranların `except (OSError, ValueError)` sözleşmesi değişmez."""
    anahtar = str(path)
    damga = _dosya_damgasi(path)                       # OSError buradan da çıkabilir: kasıtlı
    onbellek = _KAYNAK_MEMO.get(anahtar)
    if onbellek is not None and onbellek[0] == damga:
        return onbellek[1]
    src = pathlib.Path(path).read_text(encoding="utf-8")
    _KAYNAK_MEMO[anahtar] = (damga, src)
    return src


def _ast_oku(path) -> ast.Module:
    """Dosyanın AST'sini memodan ya da taze ayrıştırmadan verir.

    DÖNEN AĞAÇ PAYLAŞILIR — çağıranlar onu MUTASYONA UĞRATMAZ (bu modüldeki tüm tüketiciler
    `ast.walk`/`iter_child_nodes` ile yalnız OKUR). Kopya çıkarmak memonun bütün kazancını geri
    verirdi: `copy.deepcopy` bir ağaç için ayrıştırmadan pahalıdır."""
    anahtar = str(path)
    damga = _dosya_damgasi(path)
    onbellek = _AST_MEMO.get(anahtar)
    if onbellek is not None and onbellek[0] == damga:
        return onbellek[1]
    tree = ast.parse(_kaynak_oku(path))                # SyntaxError çağırana AYNEN çıkar
    _AST_MEMO[anahtar] = (damga, tree)
    return tree


def _enclosing(tree: ast.AST) -> list[tuple[ast.ExceptHandler, str]]:
    """Her ExceptHandler'ı içinde bulunduğu fonksiyon/sınıf yolu ile eşleştirir."""
    out: list[tuple[ast.ExceptHandler, str]] = []

    def visit(node: ast.AST, scope: str) -> None:
        """Ağacı özyineli gezer: fonksiyon/sınıf düğümlerinde kapsam yolunu uzatır ve rastladığı
        her `ExceptHandler`ı o anki kapsamla birlikte `out`a ekler."""
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
    """Yakalayıcının kaynak satır aralığı `(ilk, son)` — gövdedeki ifadelerin en büyük bitiş
    satırıyla genişletilir. `# sessiz-yutma:` işaretinin aranacağı pencereyi belirler."""
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
    """Tek bir kaynak METNİNDEKİ sinyalsiz yakalayıcılar. (Testlerin pozitif kontrolü buradan
    beslenir — tarayıcının gerçekten çalıştığını sentetik bir kaynakla kanıtlayabilmek için.)

    METİN GİRİŞİ KORUNDU, AYRIŞTIRMA AYRILDI: gövde `_scan_agac`a taşındı ki DOSYADAN gelen
    çağıran (`silent_handlers`) ayrıştırmayı memodan alabilsin. Bu fonksiyonun sözleşmesi
    (dizge al, ayrıştıramazsan körlüğe yaz, [] dön) değişmedi."""
    try:
        tree = ast.parse(src)
    except (SyntaxError, ValueError) as e:
        # ValueError: `ast.parse` NUL baytlı kaynakta SyntaxError DEĞİL ValueError fırlatır
        # ("source code string cannot contain null bytes") — demete alınmasaydı tarayıcı
        # UNSCANNED'e yazmak yerine ÇÖKERDİ. Ayrıştıramamak kayda geçer, çökmek geçmez.
        _note_unscanned(filename, e, "silent_handlers")
        return []
    return _scan_agac(tree, src, filename)


def _scan_agac(tree: ast.Module, src: str, filename: str) -> list[dict]:
    """`scan_source`un ayrıştırma-sonrası gövdesi: hazır bir AST + kaynağı üzerinde sinyalsiz
    yakalayıcıları toplar. Ayrı durur ki dosyadan gelen yol aynı ağacı ikinci kez ayrıştırmasın."""
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
            # MEMODAN: metin de ağaç da bu turda başka fazlarca zaten okunmuş/ayrıştırılmıştır.
            # `SyntaxError` demete EKLENDİ çünkü ayrıştırma artık burada oluyor — eskiden onu
            # `scan_source` yakalayıp aynı evre adıyla körlüğe yazıyordu; kayıt DEĞİŞMEDİ.
            src, tree = _kaynak_oku(f), _ast_oku(f)
        except (SyntaxError, OSError, ValueError) as e:   # ValueError: UnicodeDecodeError dâhil
            _note_unscanned(f, e, "silent_handlers")
            continue
        for hit in _scan_agac(tree, src, str(f)):
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
# "yazılıyor ama okunmuyor" artefaktı İHLALDİR — çünkü tam olarak öyle bir dosya
# (yedi desenli bütünlük raporu) üretilip hiç okunmamıştı. Buradaki her satır bir KARARDIR, muafiyet
# değil: ya tüketici bir ERİŞİMCİ FONKSİYON üzerinden dolaylıdır (statik tarama fonksiyon içindeki
# okumayı yazan modüle sayar), ya dosya modülün KENDİ işletim durumudur (önbellek, alarm tekilleştirme,
# iş kuyruğu) ve dışarıdan okunması zaten anlamsızdır.
DECLARED_SINKS: dict[str, str] = {
    "litestream.env": "yazarı api/secrets.litestream_env_sync (0600 doğum); OKUYUCUSU MODÜL "
        "DEĞİL systemd'dir — meridian-litestream.service.d/10-s3-env.conf EnvironmentFile= ile "
        "yükler (S3 kimliği, AŞAMA-2 2026-08-23). Statik graf birim dosyalarını okuyamaz; beyan "
        "kalkarsa (S3 replica emekli olursa) bu satır da kalkar — stale_sinks bekçisi izler",
    "pool_exhausted_seen.json": "hermes kimlik-havuzu son-tükenme-zamanı çivisi (v188) — okuyucu "
        "aynı modülde (_pool_seen_at, süreç-yeniden-başlatma sonrası kota-sıfırlama kıyası için "
        "kalıcı olmak ZORUNDA); statik graf modül-içi okumayı göremiyor (finviz vakasındaki sınıf)",
    # NOT: `finviz_universe.json` buradan ÇIKARILDI. Beyanı doğruydu — okuyucusu
    # yalnız kendi modülündeydi, statik graf onu göremiyordu. Artık DIŞ bir okuyucusu var:
    # `marketview.build` keşfedilen evreni bars'ta olmayan semboller için satır üretmekte
    # kullanıyor ve gerekçesini panonun Piyasa sekmesine taşıyor. Muafiyet işi bittikten sonra
    # da yerinde dursaydı liste "kimsenin bakmadığı çöplüğe" dönerdi (yukarıdaki kural).
    "monotonic_amnesty.json": "watchdog.grant_amnesty yazar, watchdog._amnesty_index okur (aynı modül "
                              "→ statik graf göremez). İçerik ÖLÜ DEĞİL: monotonicity_report onu "
                              "'amnestied' alanıyla dışa verir ve pano gerekçesiyle birlikte gösterir. "
                              "Meşru küçülmenin (re-seed) yazılı kaydı — bkz. 2026-07-22 trades 129→96",
    "search_progress.json": "canlı arama ilerlemesinin SÜREÇLER-ARASI nüshası (ROADMAP Ö-50). "
        "Yazan `hermes._progress_aynala`, okuyan `hermes.search_progress_oku` — ikisi de AYNI "
        "modülde, o yüzden statik graf dış okuyucu göremiyor. GERÇEK tüketiciler başka modüllerde "
        "ve erişimci fonksiyon üzerinden geliyor: `hermes_runtime.status` → /api/hermes → pano, ve "
        "`sprint._arama_durumu` → sprint kapısı. İkincisi EMNİYET tüketicisidir: öğrenme döngüsü "
        "kendi systemd biriminde koştuğu için sprint bu bayrağı bellekte GÖREMEZ; dosya olmasaydı "
        "boş sözlüğü 'meşgul değil' okur ve koşan aramanın üstüne 8 çekirdeklik antrenman başlatırdı",
    # --- erişimci fonksiyon üzerinden dolaylı tüketim (pano → api → fonksiyon → dosya) ---
    # NOT: `learning_loop_open.json` buradan ÇIKARILDI. Beyanı "watchdog makullük
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
    # NOT: KARDEŞ defter `agent_calls.jsonl` BİLEREK burada DEĞİLDİR. Onun DIŞ
    # okuyucusu gerçektir ve statik graf onu görür: `hermes.integrations_status()` satırları
    # `store.read_jsonl(_at.CAGRI_DEFTERI, ...)` ile KENDİ okur, yorumu `agent_telemetry.ozet()`e
    # verir. Muafiyet yerine gerçek tüketici tercih edildi — YASA 6'nın kaçış yolu, kapatabildiğin
    # yerde kullanılmaz.
    "agent_traces.jsonl": "HAM AJAN İZİ (D3 modül 2, C2-2): çağrı başına tam stdout+stderr, "
                          "sır-maskeli, akış başına 8.000 karakter tavanlı ve 300 satırlık halkasal "
                          "budamalı. Tüketicisi `agent_telemetry.iz_oku()` (aynı modül → statik graf "
                          "göremez) ve `ops/vaka_sabitle.py` (fikstür dondurucusu; `meridian/` "
                          "DIŞINDA, tarama kapsamı dışı). HAM SATIRLAR PANOYA BİLEREK TAŞINMAZ: "
                          "~5 MB'lık ham izi HTTP gövdesine koymak hem maliyet hem sızıntı "
                          "yüzeyidir; panoya çıkan şey defterin DOLULUĞUdur "
                          "(`agent_telemetry.ozet()['iz']` → hermes.integrations_status → "
                          "/api/hermes), yani 'budama işliyor mu' sorusu dosyaya bakmadan "
                          "cevaplanır. Defter teşhis içindir: aranır, özetlenmez",
    "warmup_scale.json": "hermes.warmup_budget()/warmup_budget_feedback() yazar ve okur (aynı modül "
                         "→ statik graf göremez; `brain_cooldown.json` ile BİREBİR aynı sınıf). "
                         "Isınma sprintinin bütçe merdiveni: çarpan + ÖLÇÜLEN duvar (H11 süre "
                         "tavanına takılan genişlik). Kalıcı olmak ZORUNDA — merdiven koşumlar "
                         "ARASINDA yaşar ve süreç yeniden başlatıldığında sıfırlanırsa kural her "
                         "restart'ta tabandan başlar (yani hiç işlemez). DIŞ tüketici gerçek: "
                         "hermes_runtime._warmup_sprint türetilen bütçeyi `last_warmup.butce/"
                         "butce_carpani/k_max/butce_formulu` olarak hermes_status.json'a yazar → "
                         "api /api/hermes 'warmup.last' → pano; yani 'kural koşuyor mu' sorusu "
                         "dosyaya bakmadan cevaplanır (v193, 2026-08-06)",
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
    # BEYAN, "OKUYUCUSU YOK" DEĞİL "STATİK GRAF GÖREMİYOR" DİYOR — okuyucu ÖLÇÜLDÜ.
    # `yeniden_hesap:orphan_state_files` bu dosyayı 7 yetimden biri sayıyordu; ölçüm hükmü şu:
    # okuyucusu VAR ve canlı yolun tam ortasında. Tarayıcının körlüğü sınıfsal — `artifact_graph`
    # yalnız `store.read_*`/`write_*` çağrılarını görür, auth kendi dosya erişimini kullanır
    # (`_auth_file().read_text()`), tıpkı `secrets.json` gibi. Beyan edilmeseydi dedektör her turda
    # gerçek olmayan bir bulgu bağırır, gerçek bir yetim o gürültüde kaybolurdu.
    # ÇAPA SATIR DEĞİL SEMBOL: bu satırda önce api.py'nin 420. satırına bir çapa yazılıydı,
    # kayan-oturum turundan sonra gerçek satır 426 oldu ve HİÇBİR test kırmızı vermedi — çünkü
    # kapı yalnız terimin VARLIĞINA bakıyordu. (Yukarıdaki sayı bir ÇAPA değil bir ALINTIDIR: emekli bir çapayı ÖRNEK olarak anıyor. İki nokta üst üsteli biçim (`dosya.py:NNN`) tarayıcıya canlı çapa görünüyordu ve 2026-08-25'te api.py'nin başına dört satır girince üçü birden 'bayat' sayıldı — yani anlatı, anlattığı şeyin kurbanı oldu. Biçim düzyazıya çevrildi; hikâye durdu.) Satır
    # numarası gömen her çapa, çapaladığı dosyanın her düzenlemesinde bayatlar; `codelaw`ın kendi
    # kovaladığı sınıf tam budur. Bu yüzden çapa artık FONKSİYON ADI + ÇAĞRI DİZGİSİDİR
    # (`api._auth` içinde `auth.verify_session(`) ve UYUŞMASI çivilenir — bkz.
    # tests/test_beyan_bayatligi_v246.py: çapa kaynakla eşleşmezse test düşer, sessizlik yapısal
    # olarak imkânsızdır. Aynı çivi YAZAN LİSTESİNİ de UYUŞMA olarak ölçer: auth.py'de `_write`e
    # ulaşan her AÇIK giriş bu metinde ADIYLA geçmek zorundadır (varlık değil, tamlık).
    "auth.json": "PANONUN KİMLİK DOSYASI — scrypt parola tuzu+özeti (`algo`) ve oturum imza anahtarı "
                 "(`key`). YAZIM TEK KAPIDAN: `auth._write` (0600 atomik). O kapıyı çağıranlar "
                 "`auth.set_password`, `auth.rotate_key` ve `auth._key()`; `_key()` anahtar YOKSA "
                 "üretip yazar, dolayısıyla imza yoluna giren HER giriş dosyayı ilk çağrıda "
                 "DOĞURABİLİR: `auth.issue_session`, `auth.refresh_session` (kayan oturum, v245-B — "
                 "→`_sign`→`_key()`; eskiden bu ad listede YOKTU) ve `auth.verify_session` "
                 "(→`_parse_session`→`_key()`). Kabuk yolu: `python -m meridian.auth_cli set` "
                 "(→set_password) ve `... logout-all` (→rotate_key). OKUYAN: `auth._read()` — "
                 "password_set/verify_password/verify_session/issue_session/refresh_session hepsi "
                 "oradan geçer; DIŞ tüketici api.py'dir ve dolaylıdır (erişimci fonksiyon sınıfı): "
                 "`api._auth` bağımlılığı her korumalı uçta `auth.verify_session(` çağırır (ÇAPA "
                 "SEMBOLDÜR, satır numarası DEĞİL — üstteki nota bak), /api/login "
                 "`verify_password`+`issue_session`, /api/auth/status `password_set`. Yani dosya "
                 "okunmasa 51 uç 401 dönerdi — ölü değil, panonun kapısı. `secrets.json` ile AYNI "
                 "sınıf (recompute.accessor_read): store.* dışından okunuyor, statik graf göremiyor",

    # --- Y4 veri katmanı: TÜKETİCİ BİLİNÇLİ OLARAK ERTELENDİ ------------------------------------
    # Bu dört artefaktın bugünkü tüketicisi adaptörlerin KENDİ CLI'ı ve v117 testleridir; loop/api/cf
    # bağlantısı SONRAKİ tura ertelendi. Erteleme bir üşenme değil, ÖLÇÜLMÜŞ bir gerekçe:
    #   * insider: rutin/fırsatçı sınıflaması 3 YILLIK bir geçmiş penceresi ister. FMP'nin
    #     `insider-trading/search` ucu ücretsiz planda HTTP 402 döndüğü CANLI DOĞRULANDI,
    #     yani pencere ancak `/latest` akışının günlük birikmesiyle dolar. Bugün
    #     bağlanacak bir tüketici, `siniflanamadi` ile dolu bir dosyayı sinyal sanardı — dosyanın
    #     `kapsam.siniflama_hazir_mi` alanı tam da o bağlantının NE ZAMAN yapılabileceğini söyler.
    #   * shortinterest: "filtreli vs filtresiz" karşı-olgusal defterde ÖLÇÜLMEDEN bir kaçınma
    #     filtresi kapıya bağlanırsa, hiç ölçülmemiş bir kısıt canlı stratejiyi daraltmış olur.
    # Beyan bu yüzden burada duruyor: erteleme yazılı, gerekçeli ve süresi ölçülebilir. Tüketici
    # bağlandığı gün bu satırlar KALDIRILMALI — yoksa `stale_sinks` ihlali olarak geri döner.
    # BEYAN TAZELENDİ (mekanizma ölçtü): "DIŞ tüketici ertelendi" cümlesi
    # ÇÜRÜTÜLDÜ — `declared_claims()` üretim yolunda gerçek bir dış çağıran buldu.
    "insider_trades.json": "Form 4 ham defteri (artımlı; su işareti + kapsam burada). Okuma "
                           "`insider.defter_oku()` içindedir (aynı modül → statik "
                           "graf göremez); sarmalayıcıları `ozet()`/`durum()`. DIŞ ÇAĞIRAN ÖLÇÜLDÜ "
                           "(2026-08-08): `scheduler._y4_collect` seans başına bir kez "
                           "`insider.ozet()` ve `insider.durum()` çağırır, sonucu "
                           "`scheduler_status.json`a düşer ve "
                           "panonun sağlayıcı kartını besler — yani defterin DOLULUĞU dosyaya "
                           "bakmadan görünür. Hâlâ yok olan şey bir KARAR tüketicisidir (kapı/filtre): "
                           "3 yıllık sınıflama penceresi dolmadan bağlanamaz (FMP `search` ucu "
                           "ücretsiz planda 402; bkz. yukarıdaki blok)",
    "insider_signals.json": "sembol-başına fırsatçı net alım özeti. Bugünkü tüketici CLI + "
                            "tests/test_insider_v117.py; loop/api bağlantısı `kapsam.siniflama_hazir_mi` "
                            "True olana kadar BİLİNÇLİ olarak ertelendi — bugün bağlanan bir okuyucu "
                            "`siniflanamadi` dolu bir dosyayı sinyal sanardı",
    # BEYAN TAZELENDİ: "bugünkü tüketici CLI + testler" ÇÜRÜTÜLDÜ —
    # `declared_claims()` üretim yolunda gerçek bir dış çağıran buldu.
    "short_interest.json": "FINRA kısa pozisyon özeti + bayatlık damgası (yayın tarihi, gecikme, "
                           "bayat_mi). Okuma `shortinterest.durum()` içindedir "
                           "(aynı modül → statik graf göremez). DIŞ ÇAĞIRAN "
                           "ÖLÇÜLDÜ (2026-08-08): `scheduler._y4_collect` seans başına bir kez "
                           "`shortinterest.durum()` çağırır ve sonucu "
                           "`scheduler_status.json` üzerinden panonun sağlayıcı kartına taşır — "
                           "bayatlık damgası dosyaya bakmadan görünür. Hâlâ yok olan şey bir KARAR "
                           "tüketicisidir: kaçınma filtresi olarak kapıya bağlanması, karşı-olgusal "
                           "defterde 'filtreli vs filtresiz' ÖLÇÜLDÜKTEN sonraki turun işidir",
    "short_interest_float.json": "float/sharesOutstanding önbelleği (FMP profile, sembol başına 1 istek "
                                 "olduğu için TAVANLI ve kalıcı). Okuyucusu aynı modüldeki "
                                 "shortinterest.ozet() — SI%float paydası; dosya kendi başına bir "
                                 "sinyal değil, kota tasarrufu için tutulan yardımcı defterdir",

    # NOT: `shadow_variants.jsonl` buradan ÇIKARILDI — beyan SÜRELİYDİ ve
    # devri yazılıydı ("`/api/diagnostics`e özeti bağladığı gün BU SATIR KALDIRILMALI").
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
    # NOT: `mechanism_beats.json` buradan ÇIKARILDI ve gerekçesi bu listenin
    # KENDİ kuralıdır ("muafiyet işi bittikten sonra da yerinde dursaydı liste kimsenin bakmadığı
    # çöplüğe dönerdi" — aynı gerekçeyle monotonic_state, finviz_universe ve learning_loop_open
    # çıkmıştı). Beyan doğruydu: nabızları yalnız `watchdog` okuyor, dışarıya taşınan şey
    # `integrity_report`ın GECİKME hükmüydü — yani "bu adım saat 03:12'de koştu" bilgisi hiçbir
    # uçtan gelmiyordu. Bu bir BORÇ olarak yazılmıştı (app.js `RENDER.cizelge`: "adım başına
    # damga mechanism_beats.json'da var ama panoya açılmamış"); sonraki tur borcu kapattı:
    # `api._hat_cizelgesi` dosyayı DOĞRUDAN okur, `/api/diagnostics` `cizelge` alanıyla servis
    # eder, pano `firsatCizelgeIzi` kartında gerçek saatiyle çizer. Zincir tam, muafiyet gereksiz.
    # NOT: `monotonic_state.json` buradan ÇIKARILDI. Beyanı doğruydu — okuyucusu yalnız
    # kendi modülündeydi (watchdog.monotonicity_report), statik graf onu "dış okuyucusu yok" diye
    # görüyordu. Artık DIŞ bir okuyucusu var: `sermaye._peak_affi` affın `was` değerini dedektörün
    # KENDİ TABANINDAN okur — kitaptaki `peak_equity`den değil, çünkü af TAM eşleşme ister ve
    # dedektör kıyası bu dosyayla yapar. İkisi ayrışsaydı af hiç tutmaz, bayrak sonsuza dek kırmızı
    # kalırdı. Muafiyet işi bittikten sonra da yerinde dursaydı liste "kimsenin bakmadığı çöplüğe"
    # dönerdi (bu sözlüğün kendi kuralı; aynı gerekçeyle finviz_universe ve learning_loop_open çıktı).
    "ownership_state.json": "sahiplik dedektörünün önceki ölçümü — aynı gerekçe",
    "entity_damga.json": "damgasız-yazım dedektörünün önceki ölçümü (SB-4, 2026-08-09): izlenen "
                         "belgenin (rev/updated_at) damgası + içerik sha256'sı. `watchdog."
                         "kitap_damga_report` yazar ve okur — aynı modül, yani statik graf DIŞ "
                         "okuyucu göremez; `watchdog_alarmed`/`ownership_state` ile BİREBİR aynı "
                         "sınıf ve aynı gerekçe. Dışarıya çıkan şey dosya DEĞİL, DATA_QUALITY "
                         "alarmıdır: 'kitap bu tur store kapısı DIŞINDAN değişti'. Kalıcı olmak "
                         "ZORUNDA — kıyas iki POLL ARASINDADIR (300 sn) ve süreç yeniden başlarsa "
                         "bellek-içi bir taban 2026-08-04 sınıfı bir yazımı sessizce yutardı",
    "bars_fingerprint.json": "bar dosyalarının parmak izi; determinizm dedektörünün karşılaştırma tabanı",

    # --- eleme muhasebesi: BEYAN GERÇEKLE DEĞİŞTİRİLDİ ------------------------------------------
    "sieve.json": "eleme muhasebesi (sieve.py iş kolunun ürünü). DIŞ TÜKETİCİ GERÇEK ve bir KARAR "
                  "GİRDİSİDİR — ölçüldü 2026-08-08. Zincir: `store.read_json` çağrısı "
                  "`sieve.stages()` içindedir (aynı modül → statik graf göremez), sarmalayıcısı "
                  "`sieve.report()`, ve onu ÜÇ dış modül çağırır: `api.api_diagnostics` (sonuç "
                  "`api._ogrenme_blogu` → `api._terfi_hukmu`'ne girer ve TERFİ HÜKMÜNÜN gerekçe "
                  "metnini belirler), `mutation.detector_red` (mutasyon kapısının kırmızı kümesine "
                  "`sieve:<asama>:<kural>` satırları), `watchdog.parity_report` (bütünlük raporunun "
                  "`eleme:` satırları). SATIR NUMARASI BİLEREK YAZILMADI: bu beyanın hastalığı "
                  "bayatlamaktı; `api.py` haftalık yüzlerce satır kayıyor ve çivilenmiş bir satır "
                  "numarası ikinci bir bayat iddia üretirdi — `declared_claims()` zaten "
                  "modül.fonksiyon düzeyinde doğruluyor. ESKİ BEYAN BAYATTI: panoya hiç bağlı "
                  "olmadığını söylüyordu ve `stale_sinks` bunu YAPISAL olarak göremezdi — "
                  "tetikleyicisi `unread` bayrağıdır, tek `store` okuması aynı modülde olduğu için "
                  "`unread` True kalıyor ve muafiyet 'geçerli' görünüyordu",
}


# ---------------------------------------------------------------------------
# BEYAN EDİLEBİLİRLİĞİN İKİ BOŞLUĞU
# ---------------------------------------------------------------------------
# `DECLARED_SINKS`in anahtarı bir ARTEFAKT ADIDIR ve o ad `unread` listesinden gelir. Bu iki şeyi
# yapısal olarak beyan EDİLEMEZ kılıyordu:
#   (a) TARİHLİ AD. `bararchive.archive_frame` `f"{ARCHIVE_DIR}/{day}.jsonl"` yazar; ad hiç
#         çözülmez, `artifacts`a girmez, `DECLARED_SINKS`e yazılan satır ölü bir muafiyet olur
#         (üstelik anahtar hiç eşleşmediği için kimse fark etmez). `bararchive.py`nin kendi
#         başlığı bu sapmayı Rol-1'e RAPORLAMIŞTI — yani bilinen, yazılı bir boşluk.
#   (b) DIŞ OKUYUCUSU OLAN ama o okuyucusu YALNIZ BİR CLI BAYRAĞINDAN çağrılan defter.
#         `unread` False olduğu için `DECLARED_SINKS`e konamaz: anında `stale_sinks` ihlali olurdu.
# İkisi için iki AYRI kayıt açıldı. Ayrı olmalarının sebebi kozmetik değil: üçünün İDDİASI ve
# dolayısıyla ÇÜRÜME ŞARTI farklıdır (bkz. `declared_claims`).

#: DESEN BEYANI. Anahtar, `_joined_glob` tarafından KODDAN TÜRETİLEN şekildir — elle yazılan
#: bir glob değil. Değer yapısaldır (düz metin değil), çünkü ders şuydu: serbest metne
#: gömülü iddia sessizce çürür. `sinanamaz` alanı ZORUNLUDUR ya da iddia SINANIR.
DECLARED_SINK_PATTERNS: dict[str, dict[str, str]] = {
    "intraday_bars/*.jsonl": {
        "sinif": "gelecek_tuketici",
        "gerekce": "DAKİKALIK BAR ARŞİVİ — Faz-5/6 KANIT KORPUSU. YAZAN: `bararchive.archive_frame` "
                   "(`store.append_jsonl(f'{ARCHIVE_DIR}/{day}.jsonl', ...)` çağrısı), "
                   "çağıranı `hotstate` — CANLI SICAK YOL, dakikalık. BUGÜN TÜKETİCİSİ YOK ve bu "
                   "ÖLÇÜLMÜŞ bir karardır, ihmal değil: intraday hattı (hotstate → mrd:bars) "
                   "uçucudur (~2 seans TTL), 'dakika-hassas icra EOD'dan gerçekten iyi mi?' sorusu "
                   "ancak geçmiş çerçeveler biriktikten SONRA cevaplanabilir ve bugün başlamayan "
                   "birikim üç ay sonra da üç aylık olmaz. SINIRSIZ DEĞİL: `bararchive._retention` "
                   "ARCHIVE_KEEP_DAYS (120 takvim günü) üstünü siler ve silinenleri SAYAR — yani "
                   "bu bir çöp yığını değil, süreli bir korpus. ADLANDIRILMIŞ GELECEK TÜKETİCİ: "
                   "Faz-5/6 kanıt korpusu, kart ailesi EXE-2026-002 — dakika-hassas icra ölçümü "
                   "genişlerse ham bar kaynağı bu arşivdir. ROL-1 HÜKMÜ (2026-08-08): yazım "
                   "SÖKÜLMEZ; tarayıcıyı memnun etmek için veri silinmez.",
        "sinanamaz": "GELECEK-ZAMAN İDDİASI. 'Faz-5/6 bunu okuyacak' bugünkü çağrı analiziyle "
                     "sınanamaz — sınanabilir olsaydı zaten bir tüketici olurdu. Bu satır o "
                     "sınanamazlığı AÇIK EDER; `declared_claims` iddiayı test etmeye ÇALIŞMAZ ve "
                     "onu `unverifiable_claims` kovasında ADIYLA raporlar. Sessiz muafiyet ile "
                     "farkı budur: sınanamayan iddia gizlenmez, işaretlenir. DEVİR ŞARTI: Faz-5/6 "
                     "ölçümü arşivi okuduğu gün BU SATIR KALDIRILMALI ve gerçek tüketici yazılmalı.",
    },
}

#: ÇAĞIRANI İNSAN OLAN DEFTER. Disiplin: "çağıranı YOK" ile "çağıranı İNSAN" ayrı
#: şeylerdir ve taramanın kendisi bu ayrımı korudu. Bu kayıt `DECLARED_SINKS`ten AYRIDIR çünkü
#: buradaki artefaktın DIŞ okuyucusu VARDIR (`unread` False) — `DECLARED_SINKS`e konsa anında
#: `stale_sinks` ihlali olurdu. İddia SINANABİLİR ve sınanır: `cli` alanındaki modül+bayrak
#: gerçekten var mı, ve okuyucu o bayrağın kolundan erişilebiliyor mu.
HUMAN_INVOKED_SINKS: dict[str, dict[str, str]] = {
    "shadow_trades.jsonl": {
        "sinif": "cagirani_insan",
        "cli": "meridian.shadow_variants --karne",
        "gerekce": "GÖLGE-v2 YAŞAM-DÖNGÜSÜ İŞLEM DEFTERİ. YAZAN: `shadow_lifecycle` "
                   "(`store.append_jsonl(TRADES_FILE, ...)`; ad `TRADES_FILE` sabitinde) — modülün başlığı "
                   "SIFIR YETKİ bloğudur: canlı portfolio/trades/trade_plans'a ve aynaya HİÇBİR yol "
                   "çıkmaz, buradaki para sayıları bir KANIT HIZLANDIRICISIDIR, onay değil. OKUYAN: "
                   "`shadow_variants._load_books` — DIŞ modüldür, bu yüzden "
                   "`unread` False'tur ve artefakt bir ihlal DEĞİLDİR. BEYANIN SEBEBİ o okuyucunun "
                   "TEK ÇAĞIRANIDIR: `shadow_variants.main()`in `--karne` kolu, yani ÇAĞIRAN BİR "
                   "İNSANDIR; hiçbir üretim yolu (loop/scheduler/api/pano) bu defteri okumaz. "
                   "'Çağıranı yok' ile 'çağıranı insan' aynı şey değildir — birincisi ihlal, "
                   "ikincisi bir karardır; ama KAYITSIZ kalırsa ikisi ayırt edilemez, bu satır tam "
                   "olarak o ayrımı kayda geçirir. DEVİR ŞARTI: kardeşi `shadow_variants.jsonl` "
                   "2026-07-30'da `analytics.shadow_variant_summary` → `/api/diagnostics` → pano "
                   "devrini aldı ve muafiyetten ÇIKTI; bu defter o devri aldığı gün BU SATIR DA "
                   "KALDIRILMALI.",
    },
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
            tree = _ast_oku(f)                   # memo: bu fonksiyon tur başına İKİ kez çağrılıyor
        except (SyntaxError, OSError, ValueError) as e:   # ValueError: UnicodeDecodeError dâhil
            _note_unscanned(f, e, "artifact_graph:consts")
            continue
        for k, v in _module_consts(tree).items():
            if k in seen and seen[k] != v:
                seen[k] = None
            else:
                seen.setdefault(k, v)
    return {k: v for k, v in seen.items() if v}


def _looks_like_artifact(s: str) -> bool:
    """Dize bir artefakt adına benziyor mu? (yalnız `.json`/`.jsonl` uzantısı ölçülür)."""
    return s.endswith((".json", ".jsonl"))


# ---------------------------------------------------------------------------
# TARAYICININ KENDİ KÖRLÜĞÜNÜN ADLANDIRILMASI
# ---------------------------------------------------------------------------
# ÖLÇÜM ÖNCE, HÜKÜM SONRA. Denetim `_store().read_json(...)`
# desenini "grafikte HİÇ görünmüyor" diye kaydetmişti. ÖLÇÜLDÜ ve bu YANLIŞ çıktı:
# o çağrıların AST şekli `Call(func=Attribute(value=Call(func=Name('_store')), attr='read_json'))`
# ve eski filtre yalnız `isinstance(n.func, ast.Attribute)` diye sorup TABANA hiç bakmadığı için
# dokuzunun da adı çözülüyordu — hepsi writer_sites/reader_sites'ta duruyordu
# (`insider` · `shortinterest` · `massive` modüllerindeki dokuz çağrı), `massive_verify.json`
# dâhil. Bulgunun ASIL çekirdeği ise doğrudur ve tam olarak buradadır: **tarayıcı ÇÖZEMEDİĞİ
# deseni saymıyordu.** Ölçülen gerçek kör sınıflar:
#   (1) `func` bir `ast.Name` — `from .store import read_json` sonrası ÇIPLAK ad çağrısı. Filtre
#       `isinstance(n.func, ast.Attribute)` dediği için 6 gerçek çağrı (`store.py` →
#       `update_json`/`update_jsonl`/`merge_dated_jsonl` içleri) ne artefakta, ne
#       `unresolved`a, ne `UNSCANNED`e düşüyordu: HİÇBİR SAYAÇTA yoktu.
#   (2) konumsal argümanı olmayan çağrı (`store.write_json(name=...)`): `n.args` boş → `continue`.
#       Bugün 0 örnek var, ama kapı YAPISALDI; sıfır örnek "kapalı" demek değildir.
# Bir bekçinin kendi körlüğünü BİLMEMESİ bekçiliğin tersidir. Artık her `store` okuma/yazma
# çağrısı ya ÇÖZÜLÜR ya da ADLANDIRILMIŞ bir `unresolved` kovasına düşer; ayrıca her erişimin
# TABAN BİÇİMİ sayılır (`access_patterns`), çünkü "hangi biçimleri görüyorum" ölçülmeden
# "hepsini görüyorum" bir iddia değil temennidir.

#: `unresolved` kovaları — her biri ADLANDIRILMIŞ bir körlük sınıfıdır, sessiz `continue` değil.
#: `desen_beyanli`: ad hâlâ ÇÖZÜLEMİYOR (tarihli f-string) ama ŞEKLİ türetildi ve o şekil
#: `DECLARED_SINK_PATTERNS`te gerekçesiyle beyanlı — "çözüldü" değil, "sahiplenildi".
UNRESOLVED_REASONS = ("konumsal_arg_yok", "ad_cozulemedi", "artefakt_adi_degil", "desen_beyanli")


def _base_shape(b: ast.AST) -> str:
    """Erişimin TABAN biçimi: `store.` → `ad:store`, `_store().` → `cagri:_store()`,
    `self._st.` → `oznitelik:_st`. Rapora çıkar; hangi desenin kaç kez göründüğü ölçülür."""
    if isinstance(b, ast.Name):
        return f"ad:{b.id}"
    if isinstance(b, ast.Call):
        inner, _ = _callee(b)
        return f"cagri:{inner or '?'}()"
    if isinstance(b, ast.Attribute):
        return f"oznitelik:{b.attr}"
    return f"diger:{type(b).__name__}"


def _callee(n: ast.Call) -> tuple[str | None, str]:
    """(çağrılan fonksiyonun sade adı, erişim deseni). Ad çözülemezse (Subscript, lambda, ...)
    `None` döner ve desen yine ADLANDIRILIR — çözülemeyen şekil de sayılabilir olmalı."""
    f = n.func
    if isinstance(f, ast.Attribute):
        return f.attr, _base_shape(f.value)
    if isinstance(f, ast.Name):
        return f.id, "ciplak_ad"          # `from .store import read_json` → `read_json(...)`
    return None, f"cozulemeyen_sekil:{type(f).__name__}"


def _joined_glob(a: ast.AST, consts: dict, gconsts: dict) -> str | None:
    """Tarihli/dinamik bir f-string adından ŞEKİL türetir: sabit parçalar korunur, çözülebilen
    değişkenler değerine, çözülemeyenler `*`a döner.
        f"{ARCHIVE_DIR}/{day}.jsonl"  →  "intraday_bars/*.jsonl"

    NEDEN TÜRETİLİYOR, ELLE YAZILMIYOR (tasarım kararı): desen anahtarı KODDAN ÖLÇÜLÜR.
    İnsan bir glob yazsaydı, kod değiştiğinde glob sessizce yanlış kalırdı — bayat-beyan hastalığının
    aynısı, bu sefer desen katmanında. Türetilmiş anahtar, ad şekli değiştiği an eşleşmeyi
    bırakır ve dosya yeniden `ad_cozulemedi`ye düşer. Yani beyan otomatik olarak BAYATLAR."""
    if not isinstance(a, ast.JoinedStr):
        return None
    parts: list[str] = []
    for v in a.values:
        if isinstance(v, ast.Constant) and isinstance(v.value, str):
            parts.append(v.value)
        elif isinstance(v, ast.FormattedValue):
            inner = v.value
            got = None
            if isinstance(inner, ast.Name):
                got = consts.get(inner.id) or gconsts.get(inner.id)
            elif isinstance(inner, ast.Attribute):
                got = gconsts.get(inner.attr)
            parts.append(got if got else "*")
        else:
            parts.append("*")
    glob = "".join(parts)
    # ard arda düşen `*`ları tekille: `**` bir şey anlatmaz, `*` anlatır
    while "**" in glob:
        glob = glob.replace("**", "*")
    return glob if _looks_like_artifact(glob) else None


def _site_key(site: str) -> tuple[str, int]:
    """`dosya.py:<satır>` biçimindeki bir ÇAĞRI YERİNİN sıralama anahtarı: `(dosya, int(satır))`.

    Düz `sorted()` SÖZLÜKSELdir ve satır numarasını METİN sayar: aynı dosyanın 3074. satırı,
    573. satırından ÖNCE gelir (çünkü `'3' < '5'`). Bu listeler denetim çıktısıdır ve insan
    gözüyle kaynağa KARŞI okunur — kaynağın akışıyla ilgisiz bir sıra, okuyanı gösterilen yerin
    gerçekten var olup olmadığını aramaya zorlar. Ayraç yoksa ya da parça sayı değilse satır 0
    sayılır: hüküm UYDURULMAZ, yalnız ad sırası korunur.

    ÖRNEK ÇAPA BİLEREK YAZILMADI: bu docstring'e gerçek bir `dosya.py` + numara çifti koymak,
    `stale_line_anchors`ın kovaladığı sınıftan YENİ bir çapa üretirdi — kendi yasasını ihlal eden
    bir yardımcı.

    `isascii()` GUARD'I ZORUNLU: `str.isdigit()` Unicode'da RAKAM SAYILAN her şeye True der —
    üst-simge ve daire içi biçimler dâhil — ama `int()` onları KABUL ETMEZ. Yani yalnız
    `isdigit()` bakan bir guard, sıralamayı korumak için yazıldığı hâlde `ValueError` ile
    çökerdi: koruyucunun kendisi yeni bir çökme yolu.

    GUARD `int()`İN KÜMESİ DEĞİL, ONUN GÜVENLİ ALT KÜMESİDİR (2026-08-16'da düzeltildi; eski
    cümle "tam olarak `int()`in aldığı kümedir" diyordu ve bu YANLIŞTI). `int()`in aldığı küme
    `str.isdecimal()`tir ve ASCII-dışı ondalıkları da kapsar (Arap-Hint `١٢٣` → 123). Buradaki
    daha dar guard BİLİNÇLİDİR: bu fonksiyonun konusu KAYNAK KODDAKİ satır numaralarıdır ve
    onlar ASCII'dir; ASCII-dışı bir "satır numarası" görürsek doğru hüküm onu sayıya çevirmek
    değil, ad sırasına düşürmektir. Yani daralma bir eksiklik değil, kapsam beyanıdır — ama
    "eşittir" diye yazılırsa okuyucu `int()`in davranışını yanlış öğrenir."""
    dosya, ayrac, satir = site.rpartition(":")
    if not ayrac or not (satir.isascii() and satir.isdigit()):
        return (site, 0)
    return (dosya, int(satir))


_GRAPH_CACHE: dict = {}

# ---------------------------------------------------------------------------
# ÖNBELLEK + KÖRLÜK SÖZLEŞMESİ — TEK GÖVDE
# ---------------------------------------------------------------------------
# SINIF (tek örnek değil): mtime-damgalı bir tarama önbelleği, isabet dalında HİÇBİR dosya
# okumadığı için körlük kaydı da ÜRETMEZ. `UNSCANNED` boş kalır, `report()["ok"]` "kör noktam
# yok" der — oysa tarama hiç yapılmamıştır. Bu modülde üç örneği vardı (`_GRAPH_CACHE`,
# `_CLAIMS_CACHE`, `ledgers._WRITERS_CACHE`); biri düzeltilip ikisi bırakılırsa sınıf kapanmaz.
# Bu yüzden saklama ve geri-yazma TEK gövdededir: her önbellek `(sonuç, körlük)` çifti saklar.
#
# KÖRLÜĞÜN SEÇİMİ EVRE ADIYLA YAPILIR, "bu turda eklendi mi" ile DEĞİL: `_note_unscanned`
# yinelenen kaydı ikinci kez EKLEMEZ (idempotent defter), dolayısıyla "tur öncesi/sonrası uzunluk
# farkı" ölçümü zaten defterde duran bir kaydı bu taramanın körlüğü saymaz ve `UNSCANNED.clear()`
# sonrası geri yazamazdı. Evre adı ise taramanın KİMLİĞİDİR ve her çağrıda aynıdır.
# (Önceki hâli `u.get("_kok") == root` filtresiydi; `_note_unscanned` `_kok` anahtarını HİÇ
# yazmadığı için filtre daima boş dönüp `or list(UNSCANNED)` yedeğine düşüyordu — yani önbelleğe
# BAŞKA taramaların körlüğü de giriyor ve isabette geri yazılıyordu. Ölü filtre kaldırıldı.)
_YOK = object()   # "önbellekte yok" ile "önbellekte None var"ı ayıran nöbetçi

# Önbellek başına tutulan girdi sayısı. 8 = üretim ağacı + testlerin aynı anda dolaşımda tuttuğu
# birkaç `tmp_path` ağacı. Sınırın işi BELLEK, doğruluk değil: bayat girdi anahtarın içindeki
# kaynak damgasıyla zaten elenir (bkz. `_src_stamp`).
_ONBELLEK_SLOT = 8


def _onbellek_oku(cache: dict, key) -> Any:
    """Önbellek isabetinde SONUCU döndürür ve o taramanın körlük kayıtlarını `UNSCANNED`e
    İDEMPOTENT biçimde geri yazar; ıska hâlinde `_YOK` nöbetçisini döndürür.

    Sonuç derin kopyalanır: çağıranın mutasyonu önbelleği kirletmesin."""
    hit = cache.get(key, _YOK)
    if hit is _YOK:
        return _YOK
    res, korluk = hit
    for kayit in korluk:
        if kayit not in UNSCANNED:
            UNSCANNED.append(kayit)
    return copy.deepcopy(res)


def _onbellege_yaz(cache: dict, key, res: Any, evreler: tuple[str, ...]) -> Any:
    """Sonucu, o taramanın körlük kayıtlarıyla BİRLİKTE saklar ve sonucun kopyasını döndürür.

    `evreler`: bu taramanın `_note_unscanned` evre adlarının ön ekleri.

    ÖNBELLEK ARTIK TEK SLOTLUK DEĞİL (2026-08-16). Eski hâl her yazımdan önce `clear()` çağırıyordu
    ve gerekçesi "damga değişince eski girdi zaten geçersizdir" idi — ama anahtar `(root, damga)`
    ÇİFTİDİR: FARKLI bir `root` ile yapılan tek bir çağrı (testlerin `tmp_path` ağaçları, ölçüm
    betikleri) üretim girdisini damgası hâlâ geçerliyken atıyordu. Ölçülen bedel: test paketinde
    ~16 zorunlu yeniden kurulum. Girdiler artık EKLEME SIRASINA göre tutuluyor ve sınır aşılınca
    EN ESKİ düşüyor; sınır bellek için var, doğruluk için değil — bayat girdi zaten anahtarla
    (damgayla) elenir, LRU'nun yaptığı yalnız gereksiz yeniden taramayı önlemek."""
    korluk = [dict(u) for u in UNSCANNED
              if str(u.get("phase", "")).startswith(evreler)]
    cache.pop(key, None)                      # yeniden ekleme: bu anahtar en TAZE sıraya geçsin
    cache[key] = (copy.deepcopy(res), korluk)
    while len(cache) > _ONBELLEK_SLOT:
        cache.pop(next(iter(cache)))          # dict ekleme sırasını korur → en eski girdi
    return res


def _src_stamp(root: str) -> tuple:
    """Kaynak ağacının parmak izi: dosya sayısı + en yeni değişiklik zamanı.
    61 stat() çağrısı, mikrosaniyeler — ayrıştırmanın yanında ölçülemez."""
    ps = sorted(pathlib.Path(root).rglob("*.py"))
    return (len(ps), max((q.stat().st_mtime_ns for q in ps), default=0))


def artifact_graph(root: str = "meridian") -> dict:
    """Her artefakt için: yazarlar, okuyucular ve BAŞKA hiçbir modül tarafından okunmuyorsa
    `unread` bayrağı. Çözülemeyen adlar (f-string, değişken, çağrı) sessizce yutulmaz —
    `unresolved` listesine yazılır; tarayıcının kendi körlüğünü gizlemesi bu yasanın ihlali olurdu."""
    # ÖNBELLEK — KAYNAK MTIME'INA BAĞLI. Bu fonksiyon projenin TÜM Python
    # kaynağını ast ile ayrıştırır ve panonun /api/diagnostics ucundan HER Operasyon açılışında
    # iki kez çağrılıyordu. Ölçüm: uç 4,18 sn; 1,17 sn'i burası, 419 ast.parse + 614.836 ast.walk.
    # Sonuç yalnız kaynağa bağlı: sunucu koşarken kaynak değişmez, değişirse damga değişir ve
    # önbellek kendiliğinden düşer. Zaman aşımı YOK — bayatlık değil, doğruluk garantisi.
    # KÖRLÜK ÖNBELLEĞE DE GİRER (ölçülmüş kusurun kapanışı): isabet dalı hiçbir dosya OKUMADIĞI
    # için `_note_unscanned` çalışmaz ve `UNSCANNED` BOŞ kalırdı — yani ikinci çağrıdan itibaren
    # bekçi "hiç kör noktam yok" der, oysa taramayı hiç yapmamıştır. Reprodüksiyon: bozuk dosyalı
    # ağaçta ilk çağrı körlüğü kaydeder, `UNSCANNED.clear()` sonrası ikinci çağrı 0 kaydeder.
    # Bu, bu modülün kendi sözleşmesini (bekçi körlüğünü RAPOR eder) çürütüyordu. Çözüm: körlük
    # kayıtları sonuçla BİRLİKTE saklanır ve isabette İDEMPOTENT biçimde geri yazılır.
    _key = (root, _src_stamp(root))
    _hit = _onbellek_oku(_GRAPH_CACHE, _key)
    if _hit is not _YOK:
        return _hit

    gconsts = _global_consts(root)
    arts: dict[str, dict[str, Any]] = {}
    unresolved: list[dict] = []
    patterns: dict[str, int] = {}      # görülen HER `store` erişim deseninin sayımı

    for f in _py_files(root):
        try:
            src = _kaynak_oku(f)
            tree = _ast_oku(f)
        except (SyntaxError, OSError, ValueError) as e:   # ValueError: UnicodeDecodeError dâhil
            _note_unscanned(f, e, "artifact_graph")
            continue
        consts = _module_consts(tree)
        mod = f.name
        for n in ast.walk(tree):
            if not isinstance(n, ast.Call):
                continue
            attr, base = _callee(n)
            role = ("writer" if attr in WRITE_CALLS else
                    "reader" if attr in READ_CALLS else None)
            if role is None:
                continue
            # BURADAN AŞAĞISI BİR `store` ERİŞİMİDİR. Hiçbir çıkış yolu sessiz olamaz: ya artefakt
            # grafiğine, ya ADLI bir `unresolved` kovasına gider (yukarıdaki blok).
            patterns[base] = patterns.get(base, 0) + 1
            site = {"file": str(f), "line": n.lineno, "call": attr, "role": role, "base": base}
            if not n.args:
                # kwargs-only / argümansız çağrı: ad HİÇ yok. Eskiden `n.args` filtrede olduğu için
                # sessizce düşüyordu — çözülemeyen erişim, sayılmayan erişim demekti.
                unresolved.append({**site, "arg": "<konumsal-arg-yok>",
                                   "arg_kind": "yok", "reason": "konumsal_arg_yok"})
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
                # ÇÖZÜLEMEDİ — ama ŞEKLİ türetilebilir mi? `f"{ARCHIVE_DIR}/{day}.jsonl"` gibi bir
                # ad `intraday_bars/*.jsonl` desenine iner; o desen beyanlıysa artefakt SAHİPLİDİR.
                # Desen eşleşmesi bir AF DEĞİLDİR: ad hâlâ `unresolved`da kalır ve sayılır, yalnız
                # kovası "sahipsiz körlük"ten "beyanlı desen"e döner. Beyansız tarihli ad hâlâ
                # `ad_cozulemedi`dir — desteğin genel af olmadığının yapısal çivisi budur.
                glob = _joined_glob(a, consts, gconsts)
                sebep = ("desen_beyanli" if glob in DECLARED_SINK_PATTERNS else
                         "ad_cozulemedi" if name is None else "artefakt_adi_degil")
                kayit = {**site, "arg": ast.dump(a)[:80], "arg_kind": type(a).__name__,
                         "reason": sebep}
                if glob:
                    kayit["pattern"] = glob
                unresolved.append(kayit)
                continue
            rec = arts.setdefault(name, {"writers": set(), "readers": set(),
                                         "writer_sites": [], "reader_sites": []})
            rec["writers" if role == "writer" else "readers"].add(mod)
            rec[f"{'writer' if role == 'writer' else 'reader'}_sites"].append(f"{mod}:{n.lineno}")

    out: dict[str, dict] = {}
    for name, rec in sorted(arts.items()):
        writers, readers = sorted(rec["writers"]), sorted(rec["readers"])
        # "başka bir modül okuyor mu?" — kendi yazdığını kendi geri okuyan modül tüketici sayılmaz;
        # O bütünlük raporu da kendi içinde tutarlıydı, eksik olan DIŞARIDAN okunmasıydı.
        external = sorted(set(readers) - set(writers))
        out[name] = {"writers": writers, "readers": readers, "external_readers": external,
                     # SIRA (dosya, SAYISAL satır) — sözlüksel değil; bkz. `_site_key`
                     "writer_sites": sorted(rec["writer_sites"], key=_site_key),
                     "reader_sites": sorted(rec["reader_sites"], key=_site_key),
                     "unread": bool(writers) and not external}

    unread = [k for k, v in out.items() if v["unread"]]
    by_reason: dict[str, int] = {r: 0 for r in UNRESOLVED_REASONS}
    desen_yerleri: dict[str, list[str]] = {}
    for u in unresolved:
        by_reason[u["reason"]] = by_reason.get(u["reason"], 0) + 1
        if u["reason"] == "desen_beyanli":
            desen_yerleri.setdefault(u["pattern"], []).append(
                f"{u['file'].rsplit('/', 1)[-1]}:{u['line']}")
    # BEYANI OLUP KODDA KARŞILIĞI KALMAYAN DESEN — ölü muafiyetin desen katmanındaki karşılığı.
    # `DECLARED_SINKS`in "stale_sinks"i ile aynı disiplin: beyan, işi bitince kalmaz.
    orphan_patterns = sorted(set(DECLARED_SINK_PATTERNS) - set(desen_yerleri))
    _res = {"artifacts": out,
            "unresolved": unresolved,
            # KÖRLÜĞÜN SAYIMI: "kaç tane göremedim" sorusunun tek satırlık cevabı.
            "unresolved_by_reason": by_reason,
            "access_patterns": dict(sorted(patterns.items())),
            # DESEN KATMANI: hangi beyanlı desen kodda nerede karşılanıyor.
            "declared_patterns": {k: sorted(v, key=_site_key)
                                  for k, v in sorted(desen_yerleri.items())},
            "orphan_patterns": orphan_patterns,
            "unread": sorted(unread),
            "declared_sinks": sorted(k for k in unread if k in DECLARED_SINKS),
            "violations": sorted(k for k in unread if k not in DECLARED_SINKS),
            "stale_sinks": sorted(k for k in DECLARED_SINKS if k in out and not out[k]["unread"])}
    # Bu taramanın körlüğü sonuçla BİRLİKTE saklanır (isabet dalı onları geri yazar). İki evre:
    # dosyaların kendi ayrıştırması ("artifact_graph") ve sabit tablosu ("artifact_graph:consts").
    return _onbellege_yaz(_GRAPH_CACHE, _key, _res, ("artifact_graph",))


# ---------------------------------------------------------------------------
# (6b) BEYANIN KENDİSİNİN DENETİMİ — "YANLIŞ MUAFİYET" SINIFI
# ---------------------------------------------------------------------------
# YAPISAL DELİK (denetim bulgusu). `stale_sinks` tek bir sinyale bakar:
#     stale_sinks = [k for k in DECLARED_SINKS if k in out and not out[k]["unread"]]
# Yani bir muafiyetin bayatladığını ancak GRAFİK dış okuyucu görürse anlar. `sieve.json` tam bu
# deliğe düşmüştü: beyanı "panoya bağlı değil, tek okuyucusu kendi testi" diyordu; gerçekte
# `api.py` → `api_diagnostics` `sieve.report()` çağırıyor ve sonuç TERFİ HÜKMÜNÜ belirliyordu. Grafik bunu
# göremez çünkü tek `store` okuması `sieve.stages`'dedir (aynı modül) → `external_readers` boş →
# `unread` True → muafiyet "geçerli" görünür. Tetikleyici yanlış sinyale bağlıydı.
#
# KAPAMA (asgari, bilerek dar): beyan METNİNİN İDDİASI, FONKSİYON-ÇAĞRI düzeyinde doğrulanır.
# Bir beyan "bu artefaktı üretim kodunda kimse okumuyor" diyorsa (aşağıdaki desenler), tarayıcı
# okumayı İÇEREN fonksiyonu ve onu çağıran modül-içi sarmalayıcıyı bulur, sonra BAŞKA bir
# `meridian/` modülünün o fonksiyonu çağırıp çağırmadığına bakar. Çağırıyorsa iddia ÇÜRÜKTÜR.
#
# AŞIRIYA KAÇMAMA SINIRI — BİLİNÇLİ: bu TAM bir çağrı grafiği DEĞİLDİR. Modül içinde yalnız
# `_HOP` (=1) sıçrama izlenir. Ölçüldü: 1 sıçrama `report()` → `stages()` zincirini yakalar;
# sınırsız fixpoint 35 beyanın 28'ini "dış erişimci var" diye işaretliyordu (modülün neredeyse
# her fonksiyonu okumaya erişiyor) — yani gürültü. Dedektörün işi ihbar etmek değil, YANLIŞ BEYANI
# yakalamaktır; yakalayamadığı derin zincirler `unread`/`stale_sinks`'in alanında kalır.
_HOP = 1

#: "Üretim kodunda okuyucusu yok" İDDİASININ metin biçimleri. Liste DAR tutulur: bir beyanın
#: "aynı modül → statik graf göremez" demesi bir iddia DEĞİL, grafiğin sınırının tarifidir ve
#: buraya girmez. Buraya yalnız DAVRANIŞSAL bir yokluk iddiası girer.
CLAIM_NO_PROD_READER = (
    re.compile(r"tek\s+okuyucu(?:su)?[^.;]{0,80}test", re.I),            # "tek okuyucusu kendi testi"
    re.compile(r"tüketici(?:si)?[^.;]{0,80}tests?/", re.I),              # "tüketici ... tests/test_x.py"
    re.compile(r"dış\s+(?:tüketici|okuyucu)[^.;]{0,80}ertelen", re.I),   # "DIŞ tüketici ertelendi"
    re.compile(r"(?:loop|api|pano)[^.;]{0,40}bağlant[^.;]{0,80}ertelen", re.I),
    re.compile(r"okuyucu(?:su)?\s+yok", re.I),
    re.compile(r"kimse\s+okumuyor", re.I),
)


def _func_index(tree: ast.AST) -> dict[str, list]:
    """Nitelenmemiş fonksiyon adı → düğümler (sınıf içindekiler dâhil; ad çakışırsa hepsi)."""
    out: dict[str, list] = {}

    def visit(n: ast.AST) -> None:
        """Ağacı özyineli gezip her fonksiyon/async fonksiyon tanımını NİTELENMEMİŞ adıyla
        `out` dizinine ekler (ad çakışırsa aynı ada birden çok düğüm birikir)."""
        for ch in ast.iter_child_nodes(n):
            if isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef)):
                out.setdefault(ch.name, []).append(ch)
            visit(ch)

    visit(tree)
    return out


def _called_names(node: ast.AST) -> set[str]:
    """Bu düğümün gövdesinde çağrılan fonksiyonların çözülebilen adları (küme).
    Adı `_callee` ile çözülemeyen çağrılar kümeye girmez — yanlış ad UYDURULMAZ."""
    return {c for c in (_callee(n)[0] for n in ast.walk(node) if isinstance(n, ast.Call)) if c}


def _reads_artifact(node: ast.AST, artifact: str, consts: dict, gconsts: dict) -> bool:
    """Bu fonksiyonun GÖVDESİ `artifact`ı okuyan bir `store` çağrısı içeriyor mu?"""
    for n in ast.walk(node):
        if not (isinstance(n, ast.Call) and n.args):
            continue
        fname, _ = _callee(n)
        if fname not in READ_CALLS:
            continue
        a = n.args[0]
        if isinstance(a, ast.Constant) and a.value == artifact:
            return True
        if isinstance(a, ast.Name) and (consts.get(a.id) or gconsts.get(a.id)) == artifact:
            return True
        if isinstance(a, ast.Attribute) and gconsts.get(a.attr) == artifact:
            return True
    return False


def _call_index(mods: dict) -> dict[tuple[str, str], list[str]]:
    """(hedef modül kökü, fonksiyon adı) → ['çağıran.py:satır', ...] — TÜM ağaç için TEK geçiş.

    Çözülen çağrı biçimleri: `_sv.report()` (takma adlı import), `meridian.sieve.report()`,
    `from .sieve import report` sonrası `report()`, ve `__import__("meridian.sieve",
    fromlist=["report"]).report()`. SONUNCUSU api.py'nin GERÇEK biçimidir — görülmeseydi o çürük
    beyan yine sessiz kalırdı, yani bu satır bulgunun kendisidir.

    NEDEN İNDEKS: beyan başına tüm ağacı yeniden yürümek 36× maliyetti (ölçüldü: 9,6 sn).
    Tek geçişte 0,6 sn. `report()` test/ops yolundadır ama 9 saniyelik bir bekçi koşturulmaz,
    koşturulmayan bekçi de bekçi değildir."""
    stems = {m[:-3] for m in mods}
    idx: dict[tuple[str, str], list[str]] = {}
    for om, (otree, _p) in mods.items():
        alias: dict[str, str] = {}       # yerel ad → modül kökü
        imported: dict[str, str] = {}    # doğrudan ithal edilen fonksiyon → modül kökü
        for n in ast.walk(otree):
            if isinstance(n, ast.ImportFrom):
                st = n.module.split(".")[-1] if n.module else None
                for a in n.names:
                    if st in stems:
                        imported[a.asname or a.name] = st
                    if a.name in stems:
                        alias[a.asname or a.name] = a.name
            elif isinstance(n, ast.Import):
                for a in n.names:
                    last = a.name.split(".")[-1]
                    if last in stems:
                        alias[a.asname or a.name.split(".")[0]] = last
        for c in ast.walk(otree):
            if not isinstance(c, ast.Call):
                continue
            f, st, nm = c.func, None, None
            if isinstance(f, ast.Attribute):
                b, nm = f.value, f.attr
                if isinstance(b, ast.Name):
                    st = alias.get(b.id)
                elif isinstance(b, ast.Attribute):
                    st = b.attr if b.attr in stems else None
                elif isinstance(b, ast.Call) and isinstance(b.func, ast.Name) \
                        and b.func.id == "__import__" and b.args \
                        and isinstance(b.args[0], ast.Constant):
                    cand = str(b.args[0].value).split(".")[-1]
                    st = cand if cand in stems else None
            elif isinstance(f, ast.Name):
                st, nm = imported.get(f.id), f.id
            if st and nm:
                idx.setdefault((st, nm), []).append(f"{om}:{c.lineno}")
    return idx


def _argparse_flags(tree: ast.AST) -> set[str]:
    """Bu modülün argparse ile TANIMLADIĞI bayraklar. `--karne` beyanının çürümesi, bayrağın
    kaldırılmasıyla OLMALI — o yüzden iddia metne değil bu kümeye bakar."""
    out: set[str] = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
                and n.func.attr == "add_argument":
            for a in n.args:
                if isinstance(a, ast.Constant) and isinstance(a.value, str) \
                        and a.value.startswith("-"):
                    out.add(a.value)
    return out


def _reach_in_module(tree: ast.AST, artifact: str, consts: dict, gconsts: dict) -> set[str]:
    """`artifact`ı okuyan fonksiyonlar + `_HOP` sıçrama uzaktaki modül-içi sarmalayıcıları."""
    defs = _func_index(tree)
    reach = {fn for fn, nodes in defs.items()
             if any(_reads_artifact(nd, artifact, consts, gconsts) for nd in nodes)}
    for _ in range(_HOP):                      # BİLEREK SIĞ — bkz. yukarıdaki sınır notu
        reach |= {fn for fn, nodes in defs.items()
                  if any(_called_names(nd) & reach for nd in nodes)}
    return reach


_CLAIMS_CACHE: dict = {}


def declared_claims(root: str = "meridian", declared: dict[str, str] | None = None,
                    patterns: dict[str, dict] | None = None,
                    human: dict[str, dict] | None = None) -> list[dict]:
    """ÜÇ beyan kaydının birlikte denetimi. Her kaydın İDDİASI farklıdır, dolayısıyla ÇÜRÜME
    ŞARTI da farklıdır — tek bir "bayat mı" sorusu üçünü birden ölçemez:

      kind="sink"    (`DECLARED_SINKS`)         iddia: "üretimde okuyucusu yok".
                     ÇÜRÜR: başka bir modül, okumayı içeren (ya da bir sıçrama uzaktaki)
                     fonksiyonu çağırıyorsa. `stale_sinks`in göremediği sınıf budur.
      kind="pattern" (`DECLARED_SINK_PATTERNS`) iddia: sınıfa göre değişir.
                     `sinanamaz` alanı varsa iddia GELECEK-ZAMANLIDIR, test EDİLMEZ ve
                     `unverifiable=True` ile ADIYLA raporlanır. Alan YOKSA beyan sınanabilirliğini
                     hiç söylememiş demektir → ÇÜRÜK sayılır. Sessizlik yapısal olarak imkânsız.
      kind="human"   (`HUMAN_INVOKED_SINKS`)    iddia: "tek tüketici şu CLI bayrağı".
                     ÇÜRÜR: modül yoksa, bayrak argparse'ta yoksa, okuyucu `main`den
                     erişilemiyorsa, ya da artefaktın dış okuyucusu hiç yoksa (yanlış kayıt).
    """
    # ENJEKSİYON = YALITIM. Üçünden BİRİ verildiyse diğerleri de BOŞ sayılır, canlı kayıtlara
    # düşmez. Aksi hâlde sentetik bir `root` ile tek kayıt sınanırken canlı desen/CLI beyanları
    # o ağaçta karşılıksız kalıp sahte "çürük" üretirdi — dedektörün kendi testini kirletmesi.
    _canli = declared is None and patterns is None and human is None
    decl = DECLARED_SINKS if _canli else (declared or {})
    pats = DECLARED_SINK_PATTERNS if _canli else (patterns or {})
    hum = HUMAN_INVOKED_SINKS if _canli else (human or {})
    if _canli:
        # ÖNBELLEK + KÖRLÜK: bkz. `_onbellek_oku`. İsabet dalında `artifact_graph` HİÇ
        # çağrılmadığı için onun körlüğünü kendi önbelleği geri yazamaz — bu yüzden burada
        # saklanan evre kümesi grafiğinkini de KAPSAR.
        _key = (root, _src_stamp(root))
        _hit = _onbellek_oku(_CLAIMS_CACHE, _key)
        if _hit is not _YOK:
            return _hit

    gconsts = _global_consts(root)
    mods: dict[str, tuple] = {}
    for f in _py_files(root):
        try:
            mods[f.name] = (_ast_oku(f), f)
        except (SyntaxError, OSError, ValueError) as e:   # ValueError: UnicodeDecodeError dâhil
            _note_unscanned(f, e, "declared_claims")

    graph = artifact_graph(root)
    idx = _call_index(mods)
    out: list[dict] = []
    for art, gerekce in decl.items():
        claim = [r.pattern for r in CLAIM_NO_PROD_READER if r.search(gerekce)]
        info = graph["artifacts"].get(art) or {}
        host_mods = sorted({s.split(":")[0] for s in info.get("reader_sites", [])}) \
            or sorted(info.get("writers", []))
        accessors: dict[str, list[str]] = {}
        for m in host_mods:
            if m not in mods:
                continue
            tree, _path = mods[m]
            stem, consts = m[:-3], _module_consts(tree)
            for fn in _reach_in_module(tree, art, consts, gconsts):
                # kendi modülünden gelen çağrı tüketici DEĞİLDİR (grafiğin `external_readers`
                # kuralıyla aynı disiplin: kendi yazdığını kendi okuyan modül sayılmaz)
                # SIRA (dosya, SAYISAL satır) — bkz. `_site_key`. Bu listeler `writer_sites`/
                # `reader_sites` ile AYNI raporda yan yana okunur; biri sayısal biri sözlüksel
                # sıralanırsa aynı çıktı iki farklı sıra gösterir ve okuyan, farkı bir BULGU
                # sanar. Sıra tek yasadan gelir.
                yerler = sorted((s for s in idx.get((stem, fn), []) if not s.startswith(f"{m}:")),
                                key=_site_key)
                if yerler:
                    accessors[f"{stem}.{fn}"] = yerler
        out.append({"kind": "sink", "artifact": art, "claim_patterns": claim,
                    "claims_no_prod_reader": bool(claim),
                    "host_modules": host_mods, "unverifiable": None,
                    "desen_yerleri": [],   # yalnız kind="pattern" doldurur — alan HER kayıtta VAR
                    # değer listeleri ÇAĞRI YERİ (`_site_key`); anahtarlar `modul.fn` adıdır ve
                    # ad sırası (düz `sorted`) onlar için doğrudur.
                    "external_accessors": {k: sorted(v, key=_site_key)
                                           for k, v in sorted(accessors.items())},
                    "stale_claim": bool(claim) and bool(accessors)})

    # --- kind="pattern": sınanabilirliğini SÖYLEMEYEN beyan çürüktür -----------------------
    kod_desenleri = graph["declared_patterns"]
    for pat, spec in pats.items():
        sinanamaz = (spec or {}).get("sinanamaz")
        yerler = kod_desenleri.get(pat, [])
        nedenler = []
        if not sinanamaz and not (spec or {}).get("cli"):
            nedenler.append("sinanabilirlik_beyan_edilmemis")
        if not yerler:
            # beyan var, kodda o şekilde yazan kimse yok → ölü muafiyet (stale_sinks emsali)
            nedenler.append("desen_kodda_yok")
        out.append({"kind": "pattern", "artifact": pat, "claim_patterns": [],
                    # ALAN ŞEKLİ ÜÇ KAYITTA DA AYNI (2026-08-16). `host_modules` eskiden burada
                    # ÇAĞRI YERLERİ (`dosya.py:NNN`) taşıyordu, sink/human kayıtlarında ise MODÜL
                    # ADLARI — tek ad, iki şekil. Böyle bir alanı bir tüketici ancak `kind`e bakıp
                    # dallanarak okuyabilir; bakmayan taraf sessizce yanlış şeyi okur (bu deponun
                    # `aliases` sözleşmesinin kurulma sebebi olan hastalığın aynısı). Modül adları
                    # yerlerden TÜRETİLİR, yerlerin kendisi `desen_yerleri`nde ADIYLA durur.
                    "claims_no_prod_reader": False,
                    "host_modules": sorted({_site_key(s)[0] for s in yerler}),
                    "desen_yerleri": sorted(yerler, key=_site_key),
                    # SINANAMAZ İDDİA GİZLENMEZ, İŞARETLENİR: gelecek-zaman iddiası bugünkü çağrı
                    # analiziyle test edilemez; edilemediği için YOK SAYILMAZ, adıyla raporlanır.
                    "unverifiable": sinanamaz,
                    "external_accessors": {}, "stale_reasons": nedenler,
                    "stale_claim": bool(nedenler)})

    # --- kind="human": "çağıranı İNSAN" iddiası CLI düzeyinde sınanır ----------------------
    for art, spec in hum.items():
        cli = (spec or {}).get("cli") or ""
        modul, _, bayrak = cli.partition(" ")
        stem = modul.split(".")[-1]
        dosya = f"{stem}.py"
        nedenler, erisimciler = [], {}
        if not cli:
            nedenler.append("cli_beyan_edilmemis")
        elif dosya not in mods:
            nedenler.append(f"cli_modulu_yok:{modul}")
        else:
            tree, _p = mods[dosya]
            if bayrak not in _argparse_flags(tree):
                nedenler.append(f"cli_bayragi_yok:{bayrak}")
            consts = _module_consts(tree)
            reach = _reach_in_module(tree, art, consts, gconsts)
            if not reach:
                nedenler.append("okuyucu_bu_modulde_yok")
            elif "main" not in reach:
                # okuyucu var ama CLI girişinden erişilemiyor → "çağıranı insan" iddiası yanlış
                nedenler.append("okuyucu_main_kolundan_erisilemiyor")
            # SIRA (dosya, SAYISAL satır) — bkz. `_site_key`; aynı raporda iki farklı sıra olmasın.
            erisimciler = {f"{stem}.{fn}": sorted(idx.get((stem, fn), []), key=_site_key)
                           for fn in sorted(reach)}
        info = graph["artifacts"].get(art) or {}
        if info and info.get("unread"):
            # dış okuyucusu YOK — bu kayda değil `DECLARED_SINKS`e ait (yanlış dosyalanmış beyan)
            nedenler.append("dis_okuyucu_yok_DECLARED_SINKS_e_ait")
        out.append({"kind": "human", "artifact": art, "claim_patterns": [],
                    "claims_no_prod_reader": False, "host_modules": sorted(info.get("readers", [])),
                    "desen_yerleri": [],   # yalnız kind="pattern" doldurur — alan HER kayıtta VAR
                    "unverifiable": None, "cli": cli, "external_accessors": erisimciler,
                    "stale_reasons": nedenler, "stale_claim": bool(nedenler)})

    if _canli:
        return _onbellege_yaz(_CLAIMS_CACHE, (root, _src_stamp(root)), out,
                              ("declared_claims", "artifact_graph"))
    return copy.deepcopy(out)


def stale_claims(root: str = "meridian", declared: dict[str, str] | None = None,
                 patterns: dict[str, dict] | None = None,
                 human: dict[str, dict] | None = None) -> list[dict]:
    """Yalnız ÇÜRÜTÜLMÜŞ beyanlar. Boş olmalı; dolu ise bir muafiyet gerçeği örtüyor demektir."""
    return [c for c in declared_claims(root, declared, patterns, human) if c["stale_claim"]]


def unverifiable_claims(root: str = "meridian") -> list[dict]:
    """SINANAMAYAN ama BEYAN EDİLMİŞ iddialar — gelecek-zamanlı tüketici sözleri. Bu liste bir
    muafiyet değil bir BORÇ DEFTERİDİR: her satır, bugün ölçülemeyen bir vaattir ve devir şartı
    kendi metninde yazılıdır. Boş olması gerekmez; GÖRÜNMEZ olması yasaktır."""
    return [{"artifact": c["artifact"], "kind": c["kind"], "neden": c["unverifiable"]}
            for c in declared_claims(root) if c.get("unverifiable")]


def dashboard_mentions(term: str, path: str = "meridian/web/app.js") -> bool:
    """Panonun gerçekten okuyup okumadığını app.js'i tarayarak DOĞRULAR (salt okuma). "Panoda
    gösteriliyor" gerekçesi, kanıtlanabilir olmadıkça gerekçe değildir."""
    try:
        return term in _kaynak_oku(path)      # memo: app.js tur başına birkaç kez sorulur
    except (OSError, ValueError) as e:          # ValueError: UnicodeDecodeError'ı da kapsar
        # Pano dosyası okunamadıysa "pano okumuyor" DEĞİL, "doğrulayamadım" doğru cevaptır; körlük
        # kayda geçer, aksi hâlde gerekçe kanıtsız kabul edilmiş olurdu.
        _note_unscanned(path, e, "dashboard_mentions")
        return False


#: Satır çapası deseni: `dosya.py:NNN`. Beyanlarda ve yorumlarda geçen bu biçim, çapaladığı
#: dosyanın HER düzenlemesinde bayatlar — bir docstring eklemek onlarca çapayı sessizce yanlışa
#: çevirir. Bu depoda tam olarak bu sınıf ölçüldü ve elle ~117 yerde düzeltildi; ELLE DÜZELTME
#: SINIFI KAPATMADI (aynı turda yenisi doğdu ve bir test onu dondurdu). Yasa bu yüzden var.
_CAPA_DESENI = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*\.py):(\d+)\b")


#: Yasanın `meridian/` DIŞINDA da baktığı canlı kod kökleri (2026-08-16'da eklendi; `report()`
#: bunları geçer, sentetik `root` ile çağıran testler GEÇMEZ).
#: KAPSAM ÖLÇÜLEREK SEÇİLDİ, ezberden değil: `tests/` 77 çapa taşıyor ve 14'ü çürüktü —
#: hata ayıklayan kişiyi yanlış satıra gönderen CANLI iddialar. `ops/` 0 çapa taşıyor (temiz,
#: ama kapsamda olması gelecekteki çapayı doğarken yakalar).
#: `docs/` BİLEREK DIŞARIDA: 2324 çapanın 704'ü çürük, ama 668'i TARİHLİ teşhis belgelerinde
#: (`…-2026-08-02.md`) — onlar tarihli birer KAYITTIR, yazıldıkları gün doğruydular ve geriye
#: dönük "düzeltmek" tarihi tahrif etmek olurdu. Kalan 36'sı üretilen `RUNBOOK.md`de ve kaynağın
#: kendi yorum bloklarının kopyasıdır; orası üreticinin işidir (ROADMAP Ö-49, açık kalem).
_EK_CAPA_KOKLERI = ("tests", "ops")


def stale_line_anchors(root: str = "meridian",
                       cozulemeyen_out: list | None = None,
                       ek_kokler: tuple[str, ...] = ()) -> list[dict]:
    """SATIR ÇAPASI YASASI: kaynaktaki her `dosya.py:NNN` çapasını ÖLÇER ve çürükleri döndürür.

    Çapa üç biçimde çürür ve üçü de burada yakalanır:
      * `menzil_disi` — numara dosyanın satır sayısını aşıyor (çapa artık hiçbir şeyi göstermiyor),
      * `bos_satir`   — gösterdiği satır boş,
      * `yorum`       — gösterdiği satır bir yorum (çapa kod göstermeliydi).

    Hedef dosya BASENAME ile çözülür; aynı adlı iki dosya varsa (`ikircikli`) hüküm verilmez —
    ölçülemeyen şey ihlal SAYILMAZ (UYDURMA YASAĞI). Kendi kendini de tarar: bu modülün
    beyanlarındaki çapalar da ölçülür.

    ÇÖZÜLEMEYEN ÇAPA SESSİZCE DÜŞMEZ (2026-08-16 denetim bulgusu). Hüküm verilemeyen çapa —
    hedef ağaçta YOK (`hedef_yok`) ya da aynı ad birden çok dosyada (`ikircikli`) — eskiden
    `continue` ile atılıyordu: yani yasa "0 çürük" derken kaçının hakkında hüküm KURAMADIĞINI
    söylemiyordu. Bu tam olarak `artifact_graph`ın `unresolved` kovasıyla kapattığı sınıftır ve
    bir körlük-raporlama yasasının kendi körlüğünü gizlemesi, yasanın kendi ihlaliydi.
    `cozulemeyen_out` verilirse bu kayıtlar ORAYA yazılır ve `report()` onları
    `line_anchor_unresolved` ADIYLA dışarı verir. İHLAL SAYILMAZLAR (`ok`u False'a çekmezler):
    ölçülemeyen şey ihlal değildir — ama SAYILIR.

    Neden burada: `stale_claims` beyanın ULAŞILABİLİRLİĞİNİ doğrular, METNİNİ değil — çapa
    metnin içinde yaşadığı için o kapının yapısal kör noktasıdır.
    """
    # TARANAN KÖKLER ve ADRES DEFTERİ AYNI KÜMEDEN kurulur: `tests/` içindeki bir çapa
    # `meridian/`deki bir dosyayı gösterebilir (ve çoğu öyle yapar), dolayısıyla adres defteri
    # tüm köklerden doğar — yoksa o çapalar "hedef_yok" diye ölçülemez sayılırdı.
    kokler = [root, *ek_kokler]
    adres: dict[str, list[pathlib.Path]] = {}
    for k in kokler:
        kok = pathlib.Path(k)
        if not kok.exists():
            continue
        for f in kok.rglob("*.py"):
            if any(p in _SKIP_DIRS for p in f.relative_to(kok).parts):
                continue
            adres.setdefault(f.name, []).append(f)

    # BEYANLI MUAFİYET (YASA 4'ün deseni): bir satır bayat çapayı KANIT olarak alıntılıyorsa —
    # yani dersin kendisi "şu çapa bayatladı" ise — çürüklüğü bulgu değil, anlatının parçasıdır.
    # İşaret zorunlu ve GÖRÜNÜR: `çapa-mezar-taşı`. İşaretsiz hiçbir çapa muaf değildir.
    MUAFIYET = "çapa-mezar-taşı"
    curuk: list[dict] = []
    for f in (g for k in kokler if pathlib.Path(k).exists() for g in _py_files(k)):
        try:
            satirlar = _kaynak_oku(f).splitlines()
        except (OSError, ValueError) as e:            # ValueError: UnicodeDecodeError'ı da kapsar
            # ÇAĞRI DÜZELTİLDİ: `_note_unscanned(path, exc, phase)` ÜÇ argüman ister; burada iki
            # veriliyordu (ikincisi de istisna değil ÖNCEDEN BİÇİMLENMİŞ metindi). Yani okunamayan
            # tek bir dosya, körlüğü kayda geçirmek yerine bekçiyi TypeError ile çökertirdi —
            # yakalayıcının kendisi yeni bir çökme yolu açmıştı.
            _note_unscanned(str(f), e, "stale_line_anchors")
            continue
        for i, satir in enumerate(satirlar, 1):
            if MUAFIYET in satir:
                continue
            for m in _CAPA_DESENI.finditer(satir):
                hedef_ad, n = m.group(1), int(m.group(2))
                hedefler = adres.get(hedef_ad, [])
                if len(hedefler) != 1:
                    # hüküm YOK — ama kayıt VAR (yukarıdaki "çözülemeyen çapa" notu).
                    if cozulemeyen_out is not None:
                        cozulemeyen_out.append(
                            {"kaynak": f"{f.name}:{i}", "capa": m.group(0),
                             "neden": "hedef_yok" if not hedefler else "ikircikli",
                             "aday_n": len(hedefler)})
                    continue
                try:
                    # MEMO BURADA EN ÇOK KAZANDIRIYOR: hedef dosya ÇAPA BAŞINA bir kez okunuyordu
                    # (canlı ağaçta ~95 çapa, çoğu aynı birkaç dosyayı gösteriyor).
                    hedef_satirlar = _kaynak_oku(hedefler[0]).splitlines()
                except (OSError, ValueError):  # sessiz-yutma: HEDEF dosya okunamıyorsa çapa hakkında hüküm veremeyiz; ölçülemeyen şey ihlal SAYILMAZ (UYDURMA YASAĞI) — taranamayan dosyanın kendisi zaten _note_unscanned ile kayda geçer
                    continue
                if n < 1 or n > len(hedef_satirlar):
                    neden = "menzil_disi"
                else:
                    govde = hedef_satirlar[n - 1].strip()
                    if not govde:
                        neden = "bos_satir"
                    elif govde.startswith("#"):
                        neden = "yorum"
                    else:
                        continue                      # kod satırı → çapa AYAKTA
                curuk.append({"kaynak": f"{f.name}:{i}", "capa": m.group(0), "neden": neden})
    return curuk


def report(root: str = "meridian") -> dict:
    """İki yasanın birlikte durumu — tek bakışta 'kaç ihlal' cevabı."""
    sil = silent_handlers(root)
    ann = annotated_handlers(root)
    graph = artifact_graph(root)
    curuk = stale_claims(root)
    capa_kor: list[dict] = []
    # EK KÖKLER YALNIZ ÜRETİM AĞACINDA: sentetik bir `root` ile çağıran testler kendi tmp ağacını
    # ölçmek ister; oraya depo `tests/`ini karıştırmak testin ölçtüğü şeyi bozardı.
    capalar = stale_line_anchors(root, cozulemeyen_out=capa_kor,
                                 ek_kokler=_EK_CAPA_KOKLERI if root == "meridian" else ())
    return {"silent_handlers": len(sil), "annotated_handlers": len(ann),
            "artifacts": len(graph["artifacts"]), "unread": graph["unread"],
            "artifact_violations": graph["violations"],
            "unresolved_artifact_calls": len(graph["unresolved"]),
            # KÖRLÜĞÜN ADI ve SAYISI: "kaç çağrıyı çözemedim, hangi sınıftan" — sessiz
            # `continue` yerine sayılabilir kova. `access_patterns` ise "hangi erişim biçimlerini
            # GÖRÜYORUM"un sayımıdır; kapsam bilinmeden sıfır-ihlal iddiası vakumdur.
            "unresolved_by_reason": graph["unresolved_by_reason"],
            "store_access_patterns": graph["access_patterns"],
            # DESEN BEYANLARI: tarihli/dinamik adın SAHİPLENİLDİĞİ yer.
            "declared_patterns": graph["declared_patterns"],
            "orphan_patterns": graph["orphan_patterns"],
            # ÇÜRÜTÜLMÜŞ MUAFİYET BEYANLARI — `stale_sinks`in yapısal kör noktası.
            # Üç kaydı da kapsar: sink · pattern · human.
            "stale_claims": [c["artifact"] for c in curuk],
            # SINANAMAYAN ama BEYANLI iddialar: muafiyet değil BORÇ defteri.
            "unverifiable_claims": [u["artifact"] for u in unverifiable_claims(root)],
            "unscanned": list(UNSCANNED),          # tarayıcının göremedikleri — sıfır ihlal iddiasının şartı
            # ÇÜRÜK SATIR ÇAPALARI: beyanın METNİ ölçülür (stale_claims yalnız ULAŞILABİLİRLİĞİ
            # ölçer, bu onun yapısal kör noktasıydı). Elle süpürme sınıfı kapatmadı; yasa kapatır.
            "stale_line_anchors": capalar,
            # ÇAPA YASASININ KENDİ KÖRLÜĞÜ: hükmü KURULAMAYAN çapalar (hedef ağaçta yok, ya da
            # aynı ad birden çok dosyada). `unresolved_by_reason` ile aynı disiplin — "0 çürük"
            # iddiası, kaçının ölçülemediği bilinmeden okunamaz. `ok`u ETKİLEMEZ: ölçülemeyen şey
            # ihlal DEĞİLDİR (UYDURMA YASAĞI), ama sayılmayan körlük de körlüğü gizlemektir.
            "line_anchor_unresolved": capa_kor,
            "line_anchor_unresolved_by_reason": {
                n: sum(1 for c in capa_kor if c["neden"] == n)
                for n in sorted({c["neden"] for c in capa_kor})},
            "ok": not sil and not graph["violations"] and not curuk and not UNSCANNED
                  and not capalar}
