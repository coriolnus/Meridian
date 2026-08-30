"""v200 · D3-UI — FIRSAT YÜZEYLERİ (C1'in on işi).

BU DOSYANIN ÖLÇTÜĞÜ KUSUR SINIFI: **"veri üretiliyor ama panoda görünmüyor."**
`docs/PATTERN-ETUDU-2026-08-06.md` §C1 yirmi iki FIRSAT satırından onunu adlandırdı ve üçü doğrudan
SAYILABİLİR bir iddiaydı — o gün üçü de doğruydu:

  * `near_miss.json` 4.988 çözülmüş satır taşıyor ve **hiçbir uç tüketicisi yok**; adı `app.js`'te
    hiç geçmiyor. Kanıt tablosu görünmez, hükmü görünür.
  * `app.js` içinde **"rollback" kelimesi sıfır kez** geçiyor — oysa otomatik geri-alma PRODUCT.md'nin
    AÇIK vaadi ve konumlandırmanın dört sütunundan biri. Bir vaadin görünmezliği onu ölçülemez yapar.
  * `/api/spend` ucunun web tarafında **sıfır çağıranı** var; panoya ulaşan tek şey aylık toplam ve
    `over_budget` bayrağı.

Bu depoda zincirin ilk iki halkası zaten zorlanıyor (`codelaw.artifact_graph`, `ledgers.
declared_writers`, YASA 6). Kopan halka üçüncüsü: **HTTP → DOM**. Statik Python grafı JS'i göremez;
bir defter okunuyor görünürken pano onu hiç çizmiyor olabilir. Bu dosya o halkayı çiviler.

NEYİ ÇİVİLER (brief'in dört ölçütü, on iş için ayrı ayrı)
--------------------------------------------------------
 (a) VERİ GERÇEKTEN BAĞLANDI — defter → uç üreticisi → uç alanı → pano tüketicisi → RENDER →
     kart kaydı. Zincir ölçüm betiğiyle sayılır (`research/olcumler/firsat_2026-08-07/say_zincir.py`);
     beklenti tablosu O betikte ELLE yazılıdır, kaynaktan türetilmez — türetilseydi test "kod
     kendine uyuyor mu?" derdi ve kopuk bir zincir yeşil kalırdı.
 (b) VERİ YOKKEN ÖLÇÜLEMEDİ + NEDEN — her kart `null` girdiyle Node'da KOŞTURULUR ve çıktısında
     "ÖLÇÜLEMEDİ" ile ≥20 karakterlik bir gerekçe aranır. Sıfır ya da boş tablo YASAK.
 (c) KART SÖZLEŞMESİNE UYUM (v198) — tek `class="card"` emisyonu, `data-kart` çıpası, `.kk-ozet`
     kapalı özeti; hem dolu hem boş dalda.
 (d) PAYDA BEYANI (v192) — çizilen her `.pm-conf` çubuğu `data-payda` taşır; paydasız oran özeti
     düşürür ve düşen özet kartı katlanamaz yapar.

Ayrıca: yukarıdaki ÜÇ SINIFIN kapandığını ölçen çiviler + emekli `/api/spend` ucuna yeni tüketici
BAĞLANMADIĞININ çivisi (K1 hükmü: "bu uçlara YENİ tüketici bağlanmaz — kanonik yüzey /api/hermes").

TESTLER KAYNAĞA VE DAVRANIŞA BAKAR (repo deseni v139/v196/v198): saf HTML üreteçleri Node'da
gerçekten koşturulur — bir dürüstlük kuralı yalnız kaynakta "yazıyor" diye tutmuş sayılmaz.
"""
from __future__ import annotations

import json
import pathlib
import re
import shutil
import subprocess

import pytest

from tests.conftest import betikten_modul_yukle

SRC = pathlib.Path(__file__).resolve().parents[1]
WEB = SRC / "meridian" / "web"
APPJS = (WEB / "app.js").read_text()
APIPY = (SRC / "meridian" / "api.py").read_text()

NODE = shutil.which("node")

# Yorumsuz gövde: bu turun her kararı gerekçesiyle kaynakta yazıyor ve o gerekçe bir BİLDİRİM
# sanılmamalı — yoksa silinmiş bir zincir kendi mezar taşı yüzünden "hâlâ bağlı" görünür.
KOD = "\n".join(l for l in APPJS.splitlines() if not l.lstrip().startswith("//"))
APIKOD = "\n".join(l for l in APIPY.splitlines() if not l.lstrip().startswith("#"))

# Ölçüm betiği testin yanında değil `research/olcumler/` altında yaşar (ölçüm ≠ hüküm); test onu
# İTHAL eder ki zincir algoritması tek yerde tanımlı olsun. İki kopya olsaydı biri güncellenir,
# diğeri sessizce bayatlardı — tam olarak bu turun kapattığı sınıf (kart sözleşmesinin deseni).
_OLCUM = SRC / "research" / "olcumler" / "firsat_2026-08-07" / "say_zincir.py"


def _olcum_modulu():
    return betikten_modul_yukle(_OLCUM, "_firsat_olcum")


# ==============================================================================================
# 0 · ORTAK DİLİM ÇIKARICI — saf üreteçleri Node'da koşturmak için
# ==============================================================================================
def _fn(ad: str, kaynak: str = APPJS) -> str:
    """Fonksiyon/sabit dilimi.

    `function ad(` sütun-0 `}`ye kadar okunur (repo deseni, v198'in `_fn`i). `const ad = …` ise
    DENGELİ okunur: satırlar, açılan parantez/köşeli/küme sayısı kapananla eşitlenene ve satır
    `;` ile bitene kadar biriktirilir. Naif "ilk satır" kuralı bu dosyada YETMİYOR — `kanitOrani`
    ve `isr` iki satıra yayılıyor ve yarım alınmış bir ok fonksiyonu Node'da sözdizimi hatası
    verir; hata harness'ta doğduğu için de ölçülen kod hakkında hiçbir şey söylemez."""
    if f"function {ad}(" in kaynak:
        i = kaynak.index(f"function {ad}(")
        parcalar = []
        for ln in kaynak[i:].splitlines(keepends=True):
            parcalar.append(ln)
            if ln.rstrip("\n") == "}":
                break
        return "".join(parcalar)
    i = kaynak.index(f"const {ad} = ")
    parcalar, derinlik = [], 0
    for ln in kaynak[i:].splitlines(keepends=True):
        parcalar.append(ln)
        # Dizgiler ÖNCE düşer (içlerindeki `//` bir yorum değildir), sonra satır-sonu yorumu.
        # Yorum atılmazsa `const pctf = …;   // fraction -> %` satırı ";" ile BİTMİŞ sayılmaz,
        # dilim bir sonraki satırı da yutar ve `cls` harness'a İKİ KEZ girer (ölçülmüş vaka).
        govde = re.sub(r'"[^"]*"|\'[^\']*\'|`[^`]*`', "", ln)
        govde = re.sub(r"//.*$", "", govde)
        derinlik += sum(govde.count(c) for c in "([{") - sum(govde.count(c) for c in ")]}")
        if derinlik <= 0 and govde.rstrip().endswith(";"):
            break
    return "".join(parcalar)


# Kart üreteçlerinin ihtiyaç duyduğu TÜM ortam. Liste açık yazılır: gizli bir bağımlılık,
# harness'ın sessizce başka bir sürümü koşturması demek olurdu.
_ORTAM = ["esc", "trn", "money", "pctf", "cls", "isr", "_chip", "REGIME_TR", "EXIT_TR",
          "KANIT_TAVAN_N", "kanitOrani", "AZ_ORNEK_N", "azOrnek", "hucreCubuk", "hucreGovde",
          "kartOzeti", "detayKatmani", "KART_KAYDI", "katKart"]
# On iş + iki ortak yardımcı (`firsatBos` ÖLÇÜLEMEDİ dalının tek biçimi, `firsatKunye` kanıt sınıfı).
_KARTLAR = ["firsatBos", "firsatKunye", "firsatRetKarnesi", "firsatEylemsizlik", "firsatEmirYasam",
            "firsatCikisNedeni", "firsatDenetimIzi", "firsatCizelgeIzi", "firsatMaliyetKarnesi",
            "firsatRollbackSicili", "firsatRegresyon", "firsatOlgunlasma"]

# ---- VAKALAR: her kart İKİ kez koşar — DOLU girdiyle ve NULL girdiyle. ------------------------
# Dolu girdiler canlı defterlerin ŞEKLİNİ taşır (alan adları ve tipleri birebir); değerler
# küçültülmüştür çünkü test bir sayı doğrulamıyor, DAVRANIŞ doğruluyor.
_DOLU = {
    "firsatRetKarnesi": [{"near_miss": {
        "var": True, "resolved_total": 4988,
        "kaynak": {"source": "yalnız-simüle", "n_real": 0, "n_cf": 4988, "generated": "2026-07-29T21:10:09+00:00"},
        "kovalar": [{"blocked_by": "hacim", "n": 4243, "entered": 4215, "n_r": 4215, "avg_r": 0.049,
                     "rejim": [{"rejim": "trend_up", "n_r": 2840, "avg_r": 0.121},
                               {"rejim": "chop", "n_r": 810, "avg_r": -0.217}]},
                    {"blocked_by": "rs", "n": 1217, "entered": 1211, "n_r": 1211, "avg_r": 0.117,
                     "rejim": [{"rejim": "trend_up", "n_r": 873, "avg_r": 0.156}]}]}}],
    "firsatEylemsizlik": [{"eylemsizlik": {
        "var": True, "exposure_budget_pct": 0,
        "birincil": {"ad": "REJİM BÜTÇESİ 0", "aciklama": "rejim maruziyet bütçesi sıfır",
                     "kanit": "exposure_budget_pct = 0"},
        "nedenler": [{"ad": "REJİM BÜTÇESİ 0", "aciklama": "rejim maruziyet bütçesi sıfır",
                      "kanit": "exposure_budget_pct = 0"}],
        "neden_yok_aciklama": None, "verdict_counts": {"NO_GO": 10},
        "gate_reasons": {"exposure_budget": 10}, "olay_sayaci": {"session_deferred_for_coverage": 240},
        "olay_penceresi": 3000, "halted": False, "learn_halted": False, "data_ok": True}}],
    "firsatEmirYasam": [{"emir_yasam": {
        "var": True, "n": 2, "gosterilen": 2, "durum_dagilim": {"filled": 1, "canceled": 1},
        "updated": "2026-07-30T14:54:27+00:00", "last_event_ts": "2026-07-19T17:15:15+00:00",
        "satirlar": [{"coid": "abc", "symbol": "F", "side": "buy", "status": "filled",
                      "event": "fill", "filled_qty": "10", "filled_avg_price": 12.5,
                      "order_id": "o1", "updated": "2026-07-19T17:15:15+00:00",
                      "plan_entry_trigger": 12.4, "slipaj_bps": 80.6, "plan_var": True},
                     {"coid": "def", "symbol": "F", "side": "sell", "status": "canceled",
                      "event": "canceled", "filled_qty": "0", "filled_avg_price": None,
                      "order_id": "o2", "updated": "2026-07-19T17:15:15+00:00",
                      "plan_entry_trigger": None, "slipaj_bps": None, "plan_var": False}]}}],
    "firsatCikisNedeni": [{"exit_efficiency": {
        "n": 2201, "avg_left_r": 1.105, "worst_reason": "stop_gap", "worst_left_r": 1.973,
        "_kaynak": {"source": "gerçek+simüle", "n_real": 95, "n_cf": 2106},
        "reasons": {"stop": {"n": 892, "n_cf": 846, "avg_mfe_r": 0.621, "avg_realized_r": -0.992, "left_r": 1.613},
                    "stop_gap": {"n": 132, "n_cf": 124, "avg_mfe_r": 0.578, "avg_realized_r": -1.395, "left_r": 1.973}}}}],
    "firsatDenetimIzi": [{
        "sorgu": {"sembol": None, "verdict": None, "limit": 60},
        "defter": {"plans_total": 390, "eslesen": 390, "gosterilen": 60, "limit": 60},
        "satirlar": [{"date": "2026-07-28", "ticker": "MAR", "setup": "exhaustion_hammer",
                      "score": 64, "verdict": "NO_GO", "reasons": ["exposure_budget %0"],
                      "checks": [], "entry_trigger": 1.0, "id": "P-1", "exploration": False,
                      "llm_veto": False}],
        "verdict_sayim": {"GO": 101, "REVIEW": 250, "NO_GO": 39},
        "semboller": [{"ticker": "AAPL", "n": 3, "verdicts": {"GO": 2, "NO_GO": 1},
                       "ilk": "2025-10-20", "son": "2026-07-28"}],
        "sembol_n": 178, "neden": None}],
    "firsatCizelgeIzi": [{
        "var": True, "damgalar": {"scheduler_poll": "2026-07-30T14:50:13+00:00",
                                  "p5_calibrations": "2026-07-29T21:10:11+00:00"},
        "damga_neden_yok": None,
        "kosular": [{"run_id": "P5-1", "pipeline": "P5_LEARN", "started": "2026-07-29T21:10:01+00:00",
                     "finished": "2026-07-29T21:10:11+00:00", "status": "ok", "error": None,
                     "skills_invoked": 0, "skills_declared_not_run": 9, "skills_skipped": 1,
                     "artifacts": 3}],
        "cagrilar": [{"ts": "2026-07-30T06:13:48+00:00", "kind": "proposal", "model": "m",
                      "attempt": 2, "empty": True, "tool_calls": 0}],
        "son_dongu": {"var": True, "date": "2026-07-28", "ts": "2026-07-29T21:10:11+00:00",
                      "yas_saat": 196.5, "candidates": 10, "plans": 10, "armed": 0},
        "donguler": [], "olay_penceresi": 3000, "scheduler_updated": "x",
        "bekci_ok": 7, "bekci_total": 20}],
    "firsatMaliyetKarnesi": [{
        "spend": {"spent_usd": 0.39, "budget_usd": 20.0, "over_budget": False},
        "spend_detay": {
            "var": True, "ay": "2026-08",
            "toplam": {"n": 12, "in_tokens": 327121, "out_tokens": 2309, "cost_usd": 0.3904, "thought_tokens": 0},
            "bu_ay": {"n": 0, "in_tokens": 0, "out_tokens": 0, "cost_usd": 0.0, "thought_tokens": 0},
            "modeller": [{"ad": "gemini-3.5-flash", "n": 12, "in_tokens": 327121, "out_tokens": 2309, "cost_usd": 0.3904, "thought_tokens": 0}],
            "kollar": [{"ad": "reflect", "n": 12, "in_tokens": 327121, "out_tokens": 2309, "cost_usd": 0.3904, "thought_tokens": 0}],
            "gunler": [{"gun": "2026-07-29", "n": 1, "in_tokens": 15345, "out_tokens": 267, "cost_usd": 0.0, "thought_tokens": 0}],
            "son": [], "olculemeyen_satir": 0, "satir_n": 12,
            "butce_kotasi": None, "arac_kullanimi": None}}],
    "firsatRollbackSicili": [{
        "var": True, "current_version": 3, "geri_alinan_n": 1, "esik": 0.05,
        "surumler": [{"version": "4", "rolled_back": True, "reinstated": None,
                      "source": "operator_override", "note": "operatör tabanı yürürlükte",
                      "parent": None, "live_score": -0.0089, "backtest_oos": None,
                      "baseline_verdict": None, "baseline_source": None, "baseline_n_trades": None,
                      "n_trades": 95, "live_since": "2026-07-23T09:17:18+00:00", "guncel": False},
                     {"version": "3", "rolled_back": None, "reinstated": True, "source": None,
                      "note": None, "parent": None, "live_score": None, "backtest_oos": 0.1245,
                      "baseline_verdict": "olculebilir", "baseline_source": "parent_backfill",
                      "baseline_n_trades": 103, "n_trades": None, "live_since": None, "guncel": True}],
        "acik_dongu": {}, "acik_dongu_neden": None,
        "olaylar": [{"ts": "2026-07-28T09:55:00+00:00", "event": "rollback_like_for_like_overturn",
                     "version": 4, "parent": 3, "reason": None, "detay": {}}],
        "olay_penceresi": 3000}],
    "firsatRegresyon": [{
        "var": True, "islem_n": 95, "az_ornek_esigi": 10, "sinir": "Kırılım YALNIZ damgalı satırlardan türer.",
        "surumler": [{"version": "4", "n": 95, "avg_r": -0.042, "az_ornek": False,
                      "rejim": [{"ad": "trend_up", "n": 57, "avg_r": -0.005, "az_ornek": False}],
                      "cikis": [{"ad": "stop", "n": 40, "avg_r": -0.98, "az_ornek": False}],
                      "setup": []},
                     {"version": "3", "n": 20, "avg_r": 0.10, "az_ornek": False,
                      "rejim": [{"ad": "trend_up", "n": 20, "avg_r": 0.10, "az_ornek": False}],
                      "cikis": [], "setup": []}],
        "fark": {"yeni": "4", "eski": "3",
                 "rejim": [{"ad": "trend_up", "delta_r": -0.105, "n_yeni": 57, "n_eski": 20, "az_ornek": False},
                           {"ad": "chop", "delta_r": None, "neden": "karşılaştırma dilimi yok"}]},
        "hipotezler": []}],
    "firsatOlgunlasma": [
        {"n": 12, "min_sample": 30, "score": None},
        {"ready": False, "regime": "chop", "trades": 3, "trades_needed": 8, "span_days": 5, "min_days": 20},
        # `l0_to_l1` ŞEKLİ ÜRETİCİDEN ALINDI (`analytics.autonomy_ladder`): anahtarlar
        # label/met/detail/manual. Uydurma bir şekil (ör. `criterion`) testi yeşil bırakır ama
        # kart canlıda boş etiket çizerdi — fikstür üreticinin gerçeğini taşımak zorunda.
        {"auto_progress": {"met": 4, "total": 5},
         "l0_to_l1": [{"label": "≥ 60 closed paper trades", "met": True, "detail": "95 / 60", "manual": False},
                      {"label": "Broker key present", "met": None, "detail": None, "manual": True}]},
        {"n": 89, "corr": 0.935},
    ],
}
# BOŞ VAKA — her kartın ÖLÇÜLEMEDİ dalı. Argüman sayısı doludakiyle AYNI olmalı, yoksa JS
# `undefined` alır ve test bir dalı hiç sınamadan geçerdi.
_BOS = {ad: [None] * len(args) for ad, args in _DOLU.items()}


@pytest.fixture(scope="module")
def kart_ciktilari():
    """On kartı Node'da GERÇEKTEN koşturur — dolu ve boş girdiyle."""
    if NODE is None:
        pytest.skip("node yok")
    ortam = "\n".join(_fn(a) for a in _ORTAM)
    kartlar = "\n".join(_fn(a) for a in _KARTLAR)
    betik = (ortam + "\n" + kartlar + "\n"
             + "const DOLU = " + json.dumps(_DOLU, ensure_ascii=False) + ";\n"
             + "const BOS = " + json.dumps(_BOS, ensure_ascii=False) + ";\n"
             + """
const out = {};
for (const [ad, args] of Object.entries(DOLU)) out[ad + "|dolu"] = globalThis[ad](...args);
for (const [ad, args] of Object.entries(BOS)) out[ad + "|bos"] = globalThis[ad](...args);
process.stdout.write(JSON.stringify(out));
""")
    p = subprocess.run([NODE, "-e", betik], capture_output=True, text=True, timeout=120)
    assert p.returncode == 0, f"fırsat kartları Node'da patladı:\n{p.stderr[-3000:]}"
    return json.loads(p.stdout)


_ISLER = sorted(_DOLU)


# ==============================================================================================
# 1 · (a) VERİ GERÇEKTEN BAĞLANDI — defter → uç → pano zinciri
# ==============================================================================================
def test_on_isin_zinciri_UCTAN_UCA_TAM():
    """C1'in on işi için zincir tek tek sayılır: uç üreticisi VAR mı, uca BAĞLI mı, pano
    tüketicisi VAR mı, bir RENDER'dan ÇAĞRILIYOR mu, kart kaydı ve kapağı yerinde mi.

    Bir halkanın kopması sessizdir: uç alanı üretilir ama kimse okumaz (YASA 6'nın HTTP→DOM
    katmanındaki hâli) ya da üreteç tanımlıdır ama hiçbir sayfadan çağrılmaz (ölü yüzey)."""
    sonuc = _olcum_modulu().olc(APIPY, APPJS)
    assert len(sonuc) == 10, f"on iş bekleniyordu, {len(sonuc)} satır ölçüldü"
    kopuk = [f"{z['is']}: uç={z['uc_bagli']} üretici={z['uretici_var']} tüketici={z['tuketici_var']} "
             f"çağrı={z['pano_cagri_n']} kayıt={z['kart_kayitli']} kapak={z['kart_kullaniliyor']}"
             for z in sonuc if not z["zincir_tam"]]
    assert not kopuk, "zincir kopuk:\n" + "\n".join(kopuk)


def test_her_is_BAGLAYICI_yuzeyine_yerlesti():
    """docs/TASARIM-YONU-2026-08-07.md §3 BAĞLAYICI: hangi iş hangi yüzeyde. Yüzey ataması bir
    zevk meselesi değil — yanlış yüzeye konan bir kart, o yüzeyin SORU CÜMLESİNİ bozar."""
    blok = re.search(r"const ALAN_BOLUMLERI = \{(.*?)\n\};", APPJS, re.S)
    assert blok, "ALAN_BOLUMLERI tanımlı değil"
    bolumler = {alan: re.findall(r'"(\w+)"', liste)
                for alan, liste in re.findall(r"^\s*(\w+):\s*\[([^\]]*)\]", blok.group(1), re.M)}
    kayit = dict(re.findall(r'^\s*"([\w:]+)":\s*\{\s*alan:\s*"(\w+)",\s*bolum:\s*"(\w+)"',
                            APPJS, re.M) and
                 [(m[0], (m[1], m[2])) for m in re.findall(
                     r'^\s*"([\w:]+)":\s*\{\s*alan:\s*"(\w+)",\s*bolum:\s*"(\w+)"', APPJS, re.M)])
    for z in _olcum_modulu().olc(APIPY, APPJS):
        assert z["kart"] in kayit, f"{z['is']}: kart kaydı yok — kapak alamaz"
        alan, bolum = kayit[z["kart"]]
        assert alan == z["yuzey"], f"{z['is']}: yüzey {alan}, bağlayıcı olan {z['yuzey']}"
        assert bolum == z["bolum"], f"{z['is']}: bölüm {bolum}, beklenen {z['bolum']}"
        assert bolum in bolumler.get(alan, []), \
            f"{z['is']}: `{bolum}` bölümü `{alan}` yüzeyinin bölüm listesinde yok"


def test_uc_uretici_ler_YALNIZ_OKUMA():
    """UÇ EKLEME İZNİ YALNIZ OKUMAYDI. Bir üreticinin state'e yazması, teşhis okumasının yan
    etkiyle defter değiştirmesi demek olurdu — ve o yan etki her pano açılışında koşardı."""
    for ad in ("_near_miss_karne", "_emir_yasam", "_spend_detay", "_hat_cizelgesi",
               "_rollback_sicili", "_regresyon_kirilimi", "_eylemsizlik"):
        i = APIKOD.index(f"def {ad}(")
        govde = APIKOD[i:]
        son = re.search(r"\n(?=def |@app\.)", govde)
        govde = govde[:son.start()] if son else govde
        for yasak in ("store.write", "store.append", ".write_text(", "obs.log(", "obs.warn(",
                      "obs.alarm("):
            assert yasak not in govde, f"{ad}: `{yasak}` — okuma ucu state'e/deftere yazıyor"
    # Yeni rota da GET olmalı: sorgulanabilir denetim izi bir okuma yüzeyidir.
    assert '@app.get("/api/audit_trail")' in APIKOD, "denetim izi ucu GET değil"
    assert '@app.post("/api/audit_trail")' not in APIKOD


# ==============================================================================================
# 2 · (b) VERİ YOKKEN "ÖLÇÜLEMEDİ + NEDEN" — asla 0, asla boş kart
# ==============================================================================================
@pytest.mark.parametrize("ad", _ISLER)
def test_veri_yokken_OLCULEMEDI_ve_NEDEN_yaziyor(kart_ciktilari, ad):
    """Uydurma yasağının bu turdaki uygulaması. `null` girdide kart YOK OLMAZ, "0" da YAZMAZ:
    ÖLÇÜLEMEDİ der ve NEDENİNİ yazar. Gerekçe ≥20 karakter (YASA 4'ün ölçüsü) — kısa bir gerekçe
    `kartOzeti`nin 3b kapısını da düşürür, yani kusur sessiz kalamaz."""
    html = kart_ciktilari[ad + "|bos"]
    assert "ÖLÇÜLEMEDİ" in html, f"{ad}: boş dalda ÖLÇÜLEMEDİ yazmıyor — {html[:200]!r}"
    duz = re.sub(r"<[^>]*>", " ", html)
    m = re.search(r"ÖLÇÜLEMEDİ\s*[—·-]\s*(.{20,})", duz)
    assert m, f"{ad}: ÖLÇÜLEMEDİ'nin gerekçesi yok ya da 20 karakterden kısa — {duz[:260]!r}"


@pytest.mark.parametrize("ad", _ISLER)
def test_bos_dalda_UYDURMA_SIFIR_yok(kart_ciktilari, ad):
    """"Ölçtük, sıfır çıktı" ile "ölçemedik" aynı piksele düşemez. Boş dalda büyük değer hücresi
    (`.pm-yield`) BASILMAZ; onun yerine boş hücre dalı (`.pm-none`) çalışır."""
    html = kart_ciktilari[ad + "|bos"]
    assert "pm-none" in html, f"{ad}: boş dalda `.pm-none` yok — sıfır uydurulmuş olabilir"
    assert "pm-yield" not in html, f"{ad}: boş dalda büyük DEĞER basılmış — ölçülemeyen ölçülmüş gibi"


def test_bos_dalda_da_KART_var(kart_ciktilari):
    """Kartın YOKLUĞU bir bilgi taşımaz. Veri gelmediğinde kart ekranda DURUR ve nedenini yazar —
    yoksa operatör "bu tur veri yoktu" ile "bu kart hiç yazılmamış"ı ayırt edemez."""
    for ad in _ISLER:
        html = kart_ciktilari[ad + "|bos"]
        n_kart = html.count('class="card')
        assert n_kart == 1, f"{ad}: boş dalda kart sayısı {n_kart}"


# ==============================================================================================
# 3 · (c) KART SÖZLEŞMESİNE UYUM (v198)
# ==============================================================================================
@pytest.mark.parametrize("ad", _ISLER)
@pytest.mark.parametrize("dal", ["dolu", "bos"])
def test_kart_sozlesmesi_TEK_KART_CIPA_OZET(kart_ciktilari, ad, dal):
    """Üç işaret birden: (1) TEK `class="card"` emisyonu — iki dallı bir kart bütçeyi iki kez yer
    ve `say_kart.py` onu iki kart sayar; (2) `data-kart` çıpası — kapağı kuran `katKurulumu` onu
    arar, yoksa kart katlanmaz; (3) `.kk-ozet` — kapalı özet, kartı AÇMADAN "içeride önemli bir
    şey var mı?"yı cevaplar."""
    html = kart_ciktilari[f"{ad}|{dal}"]
    assert html.count('class="card') == 1, f"{ad}/{dal}: kart emisyonu tek değil"
    assert re.search(r'data-kart="[\w:]+"', html), f"{ad}/{dal}: `data-kart` çıpası yok"
    assert 'class="kk-ozet"' in html, \
        f"{ad}/{dal}: kapalı özet üretilmedi — kart katlanamaz (üç kapıdan biri düşmüş): {html[:240]!r}"
    assert '<h2 class="t">' in html, f"{ad}/{dal}: kart başlığı yok"


def test_kartlar_yeni_bir_HUCRE_DILI_acmiyor(kart_ciktilari):
    """v192/v198'in tek dil kuralı: on yeni kartın hiçbiri kendi sayı/kart sınıfını icat etmez.
    İkinci bir hücre ailesi, ilk düzenlemede iki dilin ayrışması demekti."""
    izin = {"pm-yield", "pm-conf", "pm-n", "pm-thin", "pm-none", "pm-cell", "pm-sectlabel",
            "kk-ozet", "card", "rise", "t", "tbl", "trow", "head", "srow", "hint", "mut", "tick",
            "chain", "mono-num", "tag", "t-go", "t-no", "t-vi", "t-rv", "empty", "tx3", "warn",
            "pos", "neg", "detay-kat", "dk-not", "dk-govde", "dk-neden", "searchbox", "rowbtn",
            "dlbtn", "g2", "acct", "r", "lstack", "gc", "p", "f", "blink", "sitem", "on"}
    bilinmeyen = set()
    for k, html in kart_ciktilari.items():
        for m in re.findall(r'class="([^"]*)"', html):
            for s in m.split():
                if s.startswith("${"):
                    continue
                if s not in izin:
                    bilinmeyen.add(f"{k}:{s}")
    assert not bilinmeyen, f"tanımsız/yeni sınıf icat edilmiş: {sorted(bilinmeyen)}"


def test_yeni_kartlarin_HEPSI_kapak_altinda():
    """On yeni kart, bütçesi ZATEN aşılmış üç yüzeye ekleniyor. Kapaksız eklemek "ilk bakışta
    düşen yük"ü on kart büyütmek olurdu — sözleşmenin ölçtüğü tam olarak o. Kayıt + kullanım
    ikisi birden aranır: kayıtsız bir `katKart` çağrısı sessizce BOŞ döner ve kart kapak almaz."""
    for z in _olcum_modulu().olc(APIPY, APPJS):
        assert z["kart_kayitli"], f"{z['is']}: `{z['kart']}` KART_KAYDI'nda yok"
        assert z["kart_kullaniliyor"], f"{z['is']}: `katKart(\"{z['kart']}\")` kaynakta çağrılmıyor"


# ==============================================================================================
# 4 · (d) PAYDA BEYANI (v192) — paydasız çubuk çizilmez
# ==============================================================================================
@pytest.mark.parametrize("ad", _ISLER)
def test_cizilen_her_CUBUK_paydasini_BEYAN_ediyor(kart_ciktilari, ad):
    """Bir çubuk "ne kadar dolu" der; neyin paydası olduğu yazmıyorsa okur onu KENDİ uydurduğu
    bir tavana göre okur. `hucreCubuk` paydasız çubuk çizmez — bu test onun fiilen böyle
    davrandığını ÇIKTI üstünde doğrular (kaynakta yazması yetmez)."""
    for dal in ("dolu", "bos"):
        html = kart_ciktilari[f"{ad}|{dal}"]
        for cubuk in re.findall(r'<span class="pm-conf"[^>]*>', html):
            assert "data-payda=" in cubuk, f"{ad}/{dal}: paydasız çubuk çizilmiş — {cubuk!r}"
            payda = re.search(r'data-payda="([^"]*)"', cubuk)
            assert payda and len(payda.group(1)) >= 3, f"{ad}/{dal}: payda beyanı boş — {cubuk!r}"


def test_paydasiz_ORAN_ozeti_dusurur_ve_kart_katlanmaz():
    """Sözleşmenin ikinci katmanı: paydasız bir ORAN yalnız çubuğu değil ÖZETİ düşürür. On kartın
    hepsi `kartOzeti`ye oran verirken payda da veriyor mu — kaynakta çiftli aranır."""
    for ad in _KARTLAR:
        govde = _fn(ad)
        for blok in re.findall(r"kartOzeti\((.*?)\)\s*(?:;|\n\s*:|\n\s*\})", govde, re.S):
            if re.search(r"\boran:\s*(?!null)", blok):
                assert "payda:" in blok, f"{ad}: `oran` verilmiş ama `payda` beyan edilmemiş"


# ==============================================================================================
# 5 · KAPANAN ÜÇ SINIF — etüdün SAYILABİLİR iddiaları
# ==============================================================================================
def test_ROLLBACK_sinifi_kapandi():
    """Etüt ölçtü: "`app.js` içinde 'rollback' kelimesi SIFIR kez geçiyor" — PRODUCT.md'nin AÇIK
    vaadinin panoda hiçbir karşılığı yoktu. Bir vaadin görünmezliği onu ölçülemez yapar."""
    say = _olcum_modulu().sinif_sayaci(APPJS, APIPY)
    assert say["rollback_gecisi"] > 0, "app.js'te 'rollback' hâlâ sıfır kez geçiyor"
    assert "firsatRollbackSicili" in KOD, "rollback sicili kartı yok"
    assert "rollback" in APIKOD, "uç tarafında rollback sicili üretilmiyor"


def test_SPEND_sinifi_KANONIK_UCTA_kapandi():
    """İKİ YÖNLÜ ÇİVİ. Etüdün ölçtüğü kusur ("/api/spend'in web çağıranı SIFIR") kapanmalı — AMA
    doğru düzeltme o EMEKLİ uca tüketici bağlamak DEĞİL: `api.py` kendi kuralını yazıyor ("bu
    uçlara YENİ tüketici bağlanmaz — kanonik yüzey /api/hermes `spend`"). Kırılım o yüzden
    kanonik ucun içinde doğdu. Test ikisini birden ölçer: emekli uç ÇAĞRILMIYOR, kırılım
    panoda GÖRÜNÜYOR."""
    say = _olcum_modulu().sinif_sayaci(APPJS, APIPY)
    assert say["spend_ucu_cagirani"] == 0, \
        "app.js EMEKLİ `/api/spend` ucunu çağırıyor — K1 hükmü ihlal edildi (kanonik uç /api/hermes)"
    assert say["spend_detay_ucta"] >= 1, "kanonik uçta `spend_detay` servis edilmiyor"
    assert say["spend_detay_tuketicisi"] >= 1, \
        "panoda `spend_detay` okuyan yok — çağrı-başına maliyet hâlâ görünmüyor"
    assert "K1-EMEKLİ" in APIPY, "emeklilik beyanı kaynaktan silinmiş — kural izsiz kalır"


def test_NEAR_MISS_sinifi_kapandi():
    """Etüt ölçtü: "`near_miss.json`ın HİÇBİR uç tüketicisi yok ve `app.js`'te adı geçmiyor."
    Künye de aynı zincirin parçası: defter `yalnız-simüle` (n_real 0) ve o damga panoya ULAŞMALI —
    ulaşmazsa karşı-olgusal bir tahmin gerçekleşmiş kâr gibi okunur (R8)."""
    assert "near_miss" in APIKOD, "uç tarafında near_miss servis edilmiyor"
    assert "near_miss" in KOD, "app.js'te near_miss hâlâ geçmiyor"
    uretici = APIKOD[APIKOD.index("def _near_miss_karne("):]
    assert '"kaynak": doc.get("_kaynak")' in uretici, "künye uçta taşınmıyor — kanıt sınıfı düşer"
    assert "firsatKunye(nm.kaynak)" in KOD, "künye panoda çizilmiyor — simüle kanıt gerçek gibi okunur"


# ==============================================================================================
# 6 · DÜRÜSTLÜK KENARLARI — bu turun kendi tuzakları
# ==============================================================================================
def test_cizelge_ESKI_BORC_BEYANI_guncellendi():
    """D2-b `saglik#cizelge` yüzeyini kurarken bir borç BEYAN ETMİŞTİ: "adım başına damga
    `state/mechanism_beats.json`da var ama panoya açılmamış … Damgaların uca açılması D3-UI'ın
    işi." Borç kapandıysa BEYAN da güncellenmeli — kapanmış bir borcun eski cümlesi ekranda
    durursa pano kendi hakkında yalan söyler."""
    bas = KOD[KOD.index('bolumBasHTML("cizelge"'):]
    bas = bas[:bas.index(");")]
    assert "henüz uca açılmadı" not in bas, "çizelge altyazısı hâlâ 'damga uca açılmadı' diyor"
    assert "mechanism_beats" in APIKOD, "damgalar uçta okunmuyor"
    assert "damgalar" in KOD, "damgalar panoda çizilmiyor"


def test_cizelge_damgasiz_adim_icin_SAAT_UYDURMUYOR():
    """Damgası olan mekanizma için GERÇEK saat yazılır; olmayan için saat ÜRETİLMEZ. `_hat_cizelgesi`
    bozuk epoch'u sessizce atlar (anahtar hiç yazılmaz) — 0 epoch yazsaydı pano 1970'i gösterirdi."""
    uretici = APIKOD[APIKOD.index("def _hat_cizelgesi("):]
    uretici = uretici[:uretici.index("\ndef ")]
    assert "continue" in uretici, "bozuk damga için atlama dalı yok"
    assert "fromtimestamp" in uretici, "epoch → ISO çevrimi yok"
    assert "damga_neden_yok" in uretici, "damga yokluğunun GEREKÇESİ taşınmıyor"


def test_denetim_izi_TAVANI_ve_PAYDAYI_birlikte_beyan_ediyor():
    """Etüdün hükmü: "çözüm tavanı kaldırmak değil, SORGULANABİLİR kılmak." O yüzden uç hem
    defterin TAMAMINI sayar (`plans_total`) hem sorgunun eşleşmesini (`eslesen`) hem gösterileni
    (`gosterilen`). Üçü birden yazılmazsa "denetim izi" iddiası yine yarım kalır."""
    govde = _fn("firsatDenetimIzi")
    for alan in ("plans_total", "eslesen", "gosterilen", "limit"):
        assert alan in govde, f"denetim izi kartı `{alan}` paydasını yazmıyor"
    uc = APIKOD[APIKOD.index("def api_audit_trail("):]
    uc = uc[:uc.index("\n@app.")]
    assert '"plans_total": len(hepsi)' in uc, "uç defterin TAMAMINI saymıyor"
    assert '"eslesen": len(secili)' in uc, "uç sorgu eşleşmesini saymıyor"


def test_denetim_filtresi_YALNIZ_OKUMA_ve_KAYITLI_eylem():
    """Yeni bir EYLEM YÜZEYİ açılmadı (tek emir-yolu yasası): tek etkileşim bir GET sorgusudur.
    Ad `EYLEMLER` izin listesinde kayıtlı olmalı — kayıtsız bir `data-act` sessizce düşer."""
    izin = KOD[KOD.index("const EYLEMLER = new Set(["):]
    izin = izin[:izin.index("]);")]
    assert '"denetimAra"' in izin, "denetimAra izin listesinde yok — filtre sessizce ölür"
    govde = KOD[KOD.index("window.denetimAra = "):]
    govde = govde[:govde.index("\n};") + 3]
    for yasak in ("method: \"POST\"", "method: 'POST'", "apiFetch("):
        assert yasak not in govde, f"denetim filtresi yazma yapıyor: {yasak}"
    assert "/api/audit_trail" in KOD, "filtre okuma ucuna bağlı değil"


def test_regresyon_karti_OLCULEMEYEN_KIYASI_uydurmuyor():
    """Tek sürümlü bir defterde "neyi bozdu" sorusunun KIYAS TARAFI yoktur. Uç `fark: None`
    döndürür ve kart bunu SÖYLER — sıfır delta çizmek "hiçbir şey değişmedi" demek olurdu."""
    # ANCHOR YORUM OLAMAZ: `APIKOD` yorumsuz gövdedir (bu dosyanın başındaki gerekçe) — bir yorum
    # başlığına çapa atmak, testi kendi süzgecinin sildiği bir metne bağlamak olurdu.
    uretici = APIKOD[APIKOD.index("def _regresyon_kirilimi("):]
    uretici = uretici[:uretici.index('@app.get("/api/audit_trail")')]
    assert "fark = None" in uretici, "kıyas yokluğu için None dalı yok"
    assert "len(cikti) >= 2" in uretici, "iki sürüm şartı yok — tek sürümde delta uydurulabilir"
    govde = _fn("firsatRegresyon")
    assert "KIYAS YOK" in govde, "kart kıyas yokluğunu rozetle söylemiyor"
    assert "ÖLÇÜLEMEZ" in govde or "ölçülemedi" in govde.lower(), "kıyas yokluğu cümleyle yazılmıyor"


def test_olgunlasma_karti_ESIGI_PANOYA_SABITLEMIYOR():
    """C10 dersi: eşik panoya sabit yazılmaz. `min_sample` hedeften, ufuk kapısı beyin durumundan,
    merdiven `/api/summary`den okunur. Sabit bir sayı yazılsaydı hedef değiştiği gün pano yalan
    söylerdi — ve o yalan sessiz olurdu."""
    govde = _fn("firsatOlgunlasma")
    assert "sd || {}).min_sample" in govde or "(sd || {}).min_sample" in govde, \
        "min_sample uçtan okunmuyor"
    # STİL ÖZNİTELİKLERİ ÖNCE DÜŞER: `font-weight:400` ve `grid-template-columns:…px` birer
    # ÇİZİM sabitidir, bir eşik değil. Ayrım şart — yoksa test doğru davranan bir kartı kendi
    # sütun genişliği yüzünden kırmızıya çevirir ve kural gürültüye boğulup sökülür.
    olcum = re.sub(r'style="[^"]*"', "", govde)
    supheli = [m for m in re.findall(r"(?<![\w.\-])(\d{2,})(?![\w.%])", olcum)
               if m not in ("10", "11", "16", "19")]
    assert not supheli, f"kartta çıplak eşik sayısı var: {supheli} — eşik uçtan okunmalı"


def test_kartlar_KOSULSUZ_renk_emisyonu_uretmiyor():
    """D1'in kuralı: renk YALNIZ anomalide. On yeni kart, `pos`/`neg`/`warn` jetonunu ancak bir
    koşul dalında basabilir. Ölçüm betiği (tara_emisyon.py) tüm dosyayı zaten tarıyor; burada
    aynı iddia YENİ KARTLAR için ayrıca çivileniyor — tavanın 0 olduğu bir ölçümde bir sızıntı
    dosyanın başka bir yerinde de kırmızı verirdi ve bu test hangi kartın kaçırdığını söyler."""
    tarayici = SRC / "research" / "olcumler" / "renk_rolleri_2026-08-07" / "tara_emisyon.py"
    mod = betikten_modul_yukle(tarayici, "_tara")
    ks, _kl = mod.scan(str(WEB / "app.js"))
    # Yeni kartların satır aralıkları: her üretecin gövdesinin başladığı satırdan bittiği satıra.
    satirlar = APPJS.splitlines()
    araliklar = []
    for ad in _KARTLAR:
        bas = next(i for i, l in enumerate(satirlar) if l.startswith(f"function {ad}("))
        son = next(i for i in range(bas + 1, len(satirlar)) if satirlar[i].rstrip() == "}")
        araliklar.append((ad, bas + 1, son + 1))
    sizinti = [f"{ad}:{x['satir']} {x['kod'][:70]}" for x in ks
               for ad, a, b in araliklar if a <= x["satir"] <= b]
    assert not sizinti, "fırsat kartlarında koşulsuz renk emisyonu:\n" + "\n".join(sizinti)


def test_node_check_gecer():
    """Sözdizimi çivisi (v196 deseni): on kart + bir eylem eklendi, dosya hâlâ ayrıştırılabilir
    olmalı. `node --check` bir testin yerine geçmez ama bir sözdizimi hatası her şeyin yerine geçer."""
    if NODE is None:
        pytest.skip("node yok")
    p = subprocess.run([NODE, "--check", str(WEB / "app.js")], capture_output=True, text=True)
    assert p.returncode == 0, f"node --check düştü:\n{p.stderr}"
