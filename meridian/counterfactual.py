"""counterfactual.py — karşı-olgusal defter: alınmayan her tam-şekilli adayı simüle edip kanıta çevirir.

NEDEN VAR. Motorun ana darboğazı kanıt bant genişliğidir: tarayıcı her gün onlarca ticker için tam
plan kurar ama yalnız alınan 1-2 işlem etiket üretir. Bu modül alınmayan her adayı — NO_GO/REVIEW
kalanları, slot yetmeyenleri, eşiğin hemen altında ölen near-miss'leri VE uyuyan kurulumların
ateşlemelerini (uyuyan küme ARMED_SETUPS'tan TÜRER; silahlanan kurulum kümeden çıkar) — simüle
bracket ile sonuna kadar izleyip ayrı bir deftere yazar: girer miydi, stop mu hedef mi, kaç R,
MFE/MAE. Her satıra o seansın rejimi damgalanır (rejimsiz kanıt, rejim-bazlı öneriyi taşıyamaz).

KİLİT GİRİŞLER: `collect` (P3 sonunda o günün planları + uyuyan sinyaller + near-miss'ler açılır;
çift-kayıt koruması hem açık satırlara hem çözülmüş defter kimliklerine bakar; sınıf muhasebesi
SON_TOPLAMA'ya düşer), `advance` (her seans açık satırları KENDİ giriş-sonrası barlarıyla çözer),
`resolved_rows` (tüketicilerin okuduğu süzülmüş görünüm), MAX_OPEN tavanı, DEFAULT_TIME_STOP.

YASA AYNASI: giriş motorun birebir yasasıyla simüle edilir (bir SONRAKİ seans açılışı; boşluk
koruması MAX_ENTRY_GAP_PCT ve stop-altı açılış; slipaj fiyatın içinde). Çıkış STATİK bracket'tır:
sert stop / hedef (stop-önce muhafazakârlığı, broker._touch_exit ile aynı sıra) + zaman stopu;
trail / scale-out / rejim-dönüşü çıkışları BİLEREK yok — amaç seçilim kalitesini ölçmek, birebir
P&L kopyası değil; sapma burada belgelidir.

SIFIR YETKİ: bu defter hiçbir kapı kararına kanıt OLAMAZ (seçilim yanlılığı + doldurma gerçekçiliği
eksik); yalnız gölge katmanları besler — gölge modelin eğitim seti, silahlanma ölçümü, skor
kalibrasyonu. Yetkisizlik test-zorlamalıdır (test_evidence_v4).
OKUR: goal.yaml (slipaj), barlar. YAZAR: yalnız cf_open.json (OPEN_FILE) + counterfactuals.jsonl
(LEDGER)."""
from __future__ import annotations

from . import store, obs, config
from .broker import MAX_ENTRY_GAP_PCT

OPEN_FILE = "cf_open.json"          # açık karşı-olgusallar (bekleyen giriş / aktif izleme)
LEDGER = "counterfactuals.jsonl"    # çözülmüş satırlar — gölge katmanların ham maddesi
MAX_OPEN = 2500                     # 250 evrene göre tavan (~60 kayıt/gün × 15g zaman-stopu + pay); doluluk panelde
DEFAULT_TIME_STOP = 15              # exit.time_stop_days ile aynı varsayılan


def _slip() -> float:
    """Kayma (slippage) oranını `goal.yaml`dan okur (bps → oran). Okunamazsa 5 bps sabitine düşer ve
    bu düşüş YASA 4 uyarısıyla işaretlenir — sessiz sapma yok."""
    try:
        return float(config.goal().get("slippage_bps", 5)) / 10000.0
    except Exception as e:
        # YASA 4: goal.yaml okunamaz/biçimsizse kayma varsayımı sessizce SABİTE düşer — cf getirileri
        # gerçek maliyet varsayımından kopar ve cf↔gerçek karşılaştırması yanıltıcı olur.
        obs.warn("slippage_default_used", error=f"{type(e).__name__}: {e}", fallback_bps=5)
        return 5.0 / 10000.0


_LEDGER_IDS: dict = {"mtime": None, "ids": set()}

# SON TOPLAMANIN MUHASEBESİ (near-miss gölge bacağı ölümü). `collect` dönüşü int kalır
# (22 test + cf_backfill o sözleşmeye bağlı); sınıf-bazlı sayım BURADAN okunur. OKUYUCULAR (YASA 6):
# loop.daily_cycle özet olayı (`near_miss_yazilan`) + testler. Süreç-içi ve çağrı-başına ezilir;
# loop ana collect'ten HEMEN sonra kopyalar (geç-borç collect'leri ezmeden önce).
SON_TOPLAMA: dict = {}


def _ledger_ids() -> set:
    """Çözülmüş satır kimlikleri — dosya mtime'ına göre önbellekli (backfill 1139 seans çağırır,
    her seferinde 7000+ satır okumak O(n²) olurdu)."""
    from . import config as _cfg
    p = _cfg.STATE / LEDGER
    try:
        mt = p.stat().st_mtime
    except OSError:  # sessiz-yutma: yardımcı G/Ç yolu; çağıran yokluğu zaten yedek değerle karşılıyor ve asıl okuma hatası store katmanında bir kez uyarılıyor
        _LEDGER_IDS.update(mtime=None, ids=set())
        return _LEDGER_IDS["ids"]
    if _LEDGER_IDS["mtime"] != mt:
        _LEDGER_IDS.update(mtime=mt, ids={r.get("id") for r in store.read_jsonl(LEDGER) if r.get("id")})
    return _LEDGER_IDS["ids"]


def collect(dstr: str, plans: list, armed_ids: set, dormant_sigs: list, time_stop_days: int,
            near_miss: list = (), regime: str = "?", strategy_version: int | None = None) -> int:
    """P3 sonunda çağrılır: o günün TÜM planları (silahlı/silahsız) + uyuyan kurulum sinyalleri
    bekleyen karşı-olgusal olarak açılır. Dönüş: eklenen kayıt sayısı (loop görmezden gelir).
    near_miss: (EntrySignal, blocked_by listesi) çiftleri — eşiğin HEMEN altında ölen adaylar
    Sıfır yetki; resolved_rows bunları VARSAYILAN dışlar.

    regime: O SEANSIN rejimi. DENETİM BULGUSU — plan satırları rejimi plandan
    alıyordu ama UYUYAN ve EŞİK-ALTI satırlar "?" ile yazılıyordu: canlı defterin %70'i (7115'in
    4950'si) rejimsizdi. Sonuç, sessiz bir mantık boşluğuydu: selfreview eşik-altı kanıtından
    "`knob`@rejim sondası aramaya değer" ÖNERİSİ üretiyor — ama kanıtın kendisinde rejim YOK.
    Öneri hangi rejime yazılacağını dayandıramıyordu. Rejim artık her satıra damgalanıyor.

    strategy_version: Bu satırı ÜRETEN strateji sürümü. OPERATÖR SORUSUNUN CEVABI BURADA:
    "sistem son tohumdan beri gelişti, defter bunu yansıtıyor mu?" — 2026-08-25'te
    ölçüldüğünde 7260 satırın 7260'ı damgasızdı ve soru defterden CEVAPLANAMIYORDU.
    Bedeli somuttu: `exhaustion_hammer` 2026-08-11'de silahlandı ama defterde 15 satırı
    vardı (komşuları 6079 ve 1135'te) — çünkü geri dolum o kurulum VARKEN koşulmamıştı.
    Damga olmadan bu ayrım yalnız tarih aralığına bakan bir sezgiyle kuruluyordu.
    `None` = ÖLÇÜLEMEDİ (çağıran sürümü bilmiyor); 1 varsayıp yazmak UYDURMA olurdu.
    Okuyucusu `surum_dokumu()` (YASA 6)."""
    open_rows = store.read_json(OPEN_FILE, [])
    # ÇİFT KAYIT KORUMASI (backfill tekrarından ÖNCE bulundu): eskiden yalnız AÇIK
    # satırlar eleniyordu. Çözülmüş bir satır artık open_rows'ta olmadığı için, defteri yeniden
    # üreten her koşu AYNI kanıtı İKİNCİ kez açar ve çözer → 7115 satır 14000 olur, her ölçüm
    # (kazanma oranı, ort. R, skill katkısı) çift sayılmış kanıtla hesaplanır. Kimse fark etmezdi.
    seen = {r["id"] for r in open_rows} | _ledger_ids()
    added, dropped = 0, 0
    # SINIF MUHASEBESİ: near-miss bacağı 2026-07-30→08-12 arası İKİ HAFTA sessizce ölü
    # kaldı ve bu fonksiyonun içinden hiçbir sayı dışarı sızmadığı için kimse görmedi. Düşme
    # nedenleri ayrı sayılır: tavan (MAX_OPEN — yazım sırası plan→uyuyan→near-miss olduğundan tavan
    # ÖNCE near-miss'i aç bırakır), çift (dedup — zararsız: satır zaten defterde; yeniden-koşularda
    # normaldir), rps (entry≤stop — sinyal geometrisi bozuk, satır hiç doğmaz).
    _sayim = {"plan": 0, "dormant": 0, "near_miss": 0}
    _tavan = {"plan": 0, "dormant": 0, "near_miss": 0}
    _cift = {"plan": 0, "dormant": 0, "near_miss": 0}
    _nm_rps = 0
    try:                                   # #3: skill-katkı ölçümü cf hızında — satır screener'ını taşır
        from . import skills as _sk
        _scr = _sk.screener_for
    except Exception:  # sessiz-yutma: isteğe bağlı bağımlılık yok — yokluğu kusur değil yapılandırma; içe aktarma denemesinin kendisi zaten cevaptır
        _scr = lambda s2: None

    def _push(row, sinif="plan"):
        """Bir karşı-olgusal satırı açık listeye ekler ve sınıf bazında sayar. Kimlik zaten varsa çift
        olarak, tavan doluysa düşen olarak sayılır — her iki hâlde de satır EKLENMEZ."""
        nonlocal added, dropped
        if row["id"] in seen:
            _cift[sinif] += 1
            return
        if len(open_rows) >= MAX_OPEN:
            dropped += 1
            _tavan[sinif] += 1
            return
        open_rows.append(row); seen.add(row["id"]); added += 1; _sayim[sinif] += 1

    for p in plans:
        rps = float(p["entry_trigger"]) - float(p["stop"])
        if rps <= 0:
            continue
        _push({"id": f"CF-{dstr}-{p['ticker']}-{p.get('setup','?')}", "date": dstr,
               "strategy_version": strategy_version,
               "ticker": p["ticker"], "setup": p.get("setup", "?"), "score": p.get("score"),
               "entry_trigger": float(p["entry_trigger"]), "stop": float(p["stop"]),
               "target": float(p.get("profit_target") or (p.get("targets") or [0])[0]),
               # KANONİK AD + eski ad: sınır geçişlerinde alan adı değişiyordu —
               # plan `r_multiple_expected` yazıyor, cf onu `rr_expected` diye YENİDEN ADLANDIRIYORDU.
               # Tüketiciler bunu "iki ad da olabilir" yamasıyla telafi ediyor; yaması olmayan her
               # yeni tüketici satırı SESSİZCE eler. Artık ikisi de yazılıyor.
               "rr_expected": p.get("r_multiple_expected"),
               "r_multiple_expected": p.get("r_multiple_expected"),
               "regime": p.get("regime_at_plan", "?"),
               # DANIŞMAN GÖRÜŞÜ PLANDAN TAŞINIR (köken takibi bulgusu). `_resolve`
               # satır 163'te `row.get("llm_opinion")` arıyor ve BULAMIYORDU: açık cf satırı bu
               # alanı hiç taşımıyordu. Ölçüldü: 69.945 cf satırının SIFIRI. Sonuç, panodaki
               # "sim 0 çift" — LLM kalibrasyonunun karşıolgusal kanadı kalıcı olarak ölüydü ve
               # hiçbir istisna oluşmadı. `dormant` ile birebir aynı sınıf, aynı fonksiyon.
               "llm_opinion": p.get("llm_opinion"),
               "verdict": p.get("gate_verdict", "?"), "taken": p["id"] in armed_ids,
               "screener": (p.get("skill_chain") or [None])[0] or _scr(p.get("setup", "?")),
               # UYUYAN ETİKETİ PLANDAN OKUNUR: burada sabit `False` yazılıyordu. Ama
               # cf_backfill uyuyan kurulum sinyallerini HEM `plans`e HEM `dormant_sigs`e koyuyor ve
               # ikisinin cf kimliği AYNI biçimde (`CF-{gün}-{ticker}-{setup}`). Plan döngüsü önce
               # koştuğu için kimliği kapıyor, dormant push'u çift-kayıt korumasına takılıp eleniyor.
               # Sonuç: defterde 1116 momentum_burst satırı var ama `dormant` alanı HEPSİNDE False —
               # yani "uyuyan kurulum kanıtı" diye filtreleyen her tüketici SIFIR satır görüyor.
               "dormant": bool(p.get("dormant_setup")),
               "status": "pending", "time_stop_days": int(time_stop_days),
               "bars_held": 0}, "plan")
    for sig in dormant_sigs:                     # uyuyan kurulumlar: silahlanma kararının ileriye-dönük kanıtı
        rps = float(sig.entry_trigger) - float(sig.stop)
        if rps <= 0:
            continue
        _push({"id": f"CF-{dstr}-{sig.ticker}-{sig.setup}", "date": dstr,
               "strategy_version": strategy_version,
               "ticker": sig.ticker, "setup": sig.setup, "score": sig.score,
               "entry_trigger": float(sig.entry_trigger), "stop": float(sig.stop),
               "target": float(sig.profit_target),
               "rr_expected": round((sig.profit_target - sig.entry_trigger) / rps, 2),
               "r_multiple_expected": round((sig.profit_target - sig.entry_trigger) / rps, 2),
               "regime": regime or "?", "verdict": "DORMANT", "taken": False, "dormant": True,
               "screener": _scr(sig.setup),
               "status": "pending", "time_stop_days": int(time_stop_days), "bars_held": 0}, "dormant")
    for sig, blockers in near_miss:              # eşik-altı gölge adaylar: eşiklerin masada bıraktığı ölçülsün
        rps = float(sig.entry_trigger) - float(sig.stop)
        if rps <= 0:
            _nm_rps += 1                         # sessizce eleniyordu — sayısı artık olaya taşınır
            continue
        _push({"id": f"CF-{dstr}-{sig.ticker}-{sig.setup}-nm", "date": dstr,
               "strategy_version": strategy_version,
               "ticker": sig.ticker, "setup": sig.setup, "score": sig.score,
               "entry_trigger": float(sig.entry_trigger), "stop": float(sig.stop),
               "target": float(sig.profit_target),
               "rr_expected": round((sig.profit_target - sig.entry_trigger) / rps, 2),
               "r_multiple_expected": round((sig.profit_target - sig.entry_trigger) / rps, 2),
               "regime": regime or "?", "verdict": "NEAR_MISS", "taken": False, "dormant": False,
               "near_miss": True, "blocked_by": list(blockers),
               "screener": _scr(sig.setup),
               "status": "pending", "time_stop_days": int(time_stop_days), "bars_held": 0}, "near_miss")
    if dropped:
        # SINIF KIRILIMI EKLENDİ: toplam sayı hangi kanıt sınıfının aç kaldığını
        # söylemiyordu — yazım sırası gereği tavana İLK kurban hep near-miss'tir.
        obs.warn("cf_ledger_full", dropped=dropped, cap=MAX_OPEN,
                 plan=_tavan["plan"], dormant=_tavan["dormant"], near_miss=_tavan["near_miss"],
                 detail="açık defter tavanda — yazım sırası plan→uyuyan→near-miss olduğundan tavan "
                        "önce near-miss bacağını aç bırakır (gölge kanıtı sessizce eksilirdi)")
    # NEAR-MISS KAYIP OLAYI (YASA 4): rps/tavan kaybı deftere hiç girmemiş kanıttır ve
    # bugüne dek İZSİZDİ — 07-30 sonrası iki haftalık sessiz ölüm bu fonksiyonda görünmez kalmıştı.
    # Çift (dedup) kayıp SAYILIR ama tek başına olay üretmez: yeniden-koşuların normal davranışıdır.
    _nm_kayip = _nm_rps + _tavan["near_miss"]
    if _nm_kayip:
        (obs.warn if _sayim["near_miss"] == 0 else obs.log)(
            "cf_near_miss_yutuldu", date=dstr, gelen=len(near_miss), yazilan=_sayim["near_miss"],
            rps_gecersiz=_nm_rps, tavan=_tavan["near_miss"], cift=_cift["near_miss"],
            detail="near-miss gölge satırlarının bir kısmı deftere HİÇ GİRMEDEN düştü "
                   "(rps_gecersiz: entry≤stop geometrisi; tavan: MAX_OPEN doluluğu)")
    SON_TOPLAMA.clear()
    SON_TOPLAMA.update(date=dstr, yazilan=added, nm_gelen=len(near_miss),
                       nm_yazilan=_sayim["near_miss"], nm_rps=_nm_rps,
                       nm_tavan=_tavan["near_miss"], nm_cift=_cift["near_miss"])
    store.write_json(OPEN_FILE, open_rows)
    return added


def _resolve(row: dict, dstr: str, status: str, exit_px: float | None = None,
             reason: str | None = None) -> dict:
    """Açık kaydı kapat → deftere yazılacak satır. entered=False satırlar da yazılır (no_fill istatistiği
    seçilim analizinde anlamlı) ama r_multiple'ları None — model eğitimi entered=True'yu süzer."""
    # `row[k]` YERİNE `.get()`: açık defter uzun ömürlüdür — şema büyüdüğünde diskte hâlâ eski
    # satırlar durur ve KeyError bütün çözümleme turunu düşürürdü (`r_multiple_expected`
    # eklenince tam bu oldu). Eksik alan satırı düşürmez; None taşır ve tüketici süzer.
    # `strategy_version` LİSTEYE 2026-08-25'te GİRDİ ve girmemiş olması ÖLÇÜLDÜ: kum havuzu
    # sondasında açık 106 satır damgalıyken çözülmüş 282 satır damgasız çıktı. İzin listesi
    # doğru bir tasarım (alanlar açıkça sayılır) ama genişletilmediğinde yeni alan sessizce
    # ölür — ve ölçümlerin ÇOĞU çözülmüş satırları okur (`resolved_rows`), yani damga tam
    # ihtiyaç duyulan yerde yok olurdu.
    out = {k: row.get(k) for k in ("id", "date", "ticker", "setup", "score", "entry_trigger", "stop",
                                   "target", "rr_expected", "r_multiple_expected", "regime", "verdict",
                                   "taken", "dormant", "strategy_version")}
    # kanonik ad ↔ takma ad: hangisi varsa ikisi de dolar (ledgers.py sözleşmesindeki alias beyanı)
    if out["r_multiple_expected"] is None:
        out["r_multiple_expected"] = out["rr_expected"]
    elif out["rr_expected"] is None:
        out["rr_expected"] = out["r_multiple_expected"]
    if row.get("llm_opinion"):
        out["llm_opinion"] = row["llm_opinion"]
    if row.get("screener"):
        out["screener"] = row["screener"]
    if row.get("near_miss"):
        out["near_miss"] = True
        out["blocked_by"] = row.get("blocked_by") or []          # #4: görüş çözülmüş satıra taşınır (gösterge kalibrasyonu)
    out.update({"resolved": dstr, "status": status, "exit_reason": reason,
                "entered": status.startswith("closed"), "bars_held": row.get("bars_held", 0)})
    if out["entered"]:
        entry, rps = row["entry"], row["entry"] - row["stop"]
        exit_fill = exit_px * (1.0 - _slip())
        out.update({"entry": round(entry, 4), "exit": round(exit_fill, 4),
                    "r_multiple": round((exit_fill - entry) / rps, 3) if rps > 0 else None,
                    "mfe_r": round((row["hi"] - entry) / rps, 3) if rps > 0 else None,
                    "mae_r": round((entry - row["lo"]) / rps, 3) if rps > 0 else None})
    return out


def advance(per: dict, d, dstr: str) -> dict:
    """Her günlük döngüde çağrılır: açık karşı-olgusalları günün barıyla ilerletir. Motor yasası:
    bekleyen giriş yalnız plan gününü izleyen İLK seansta dolar (boşluk korumalarıyla), dolmazsa
    no_fill. Aktifler: stop-önce bar yürüyüşü + zaman stopu. Dönüş özeti loop görmezden gelir."""
    open_rows = store.read_json(OPEN_FILE, [])
    if not open_rows:
        return {"open": 0}
    slip = _slip()
    still, resolved = [], []
    for row in open_rows:
        if row["date"] >= dstr:                          # bugün açıldı — ilk barı SONRAKİ seans
            still.append(row); continue
        t = row["ticker"]
        if t not in per or d not in per[t].index:        # bar yok (delist/veri boşluğu) → süresiz bekletme yok
            row["_miss"] = row.get("_miss", 0) + 1
            if row["_miss"] > 5:
                resolved.append(_resolve(row, dstr, "expired_no_data"))
            else:
                still.append(row)
            continue
        bar = per[t].loc[d]
        o, h, l, c = float(bar["open"]), float(bar["high"]), float(bar["low"]), float(bar["close"])
        if row["status"] == "pending":
            # motorun giriş yasası birebir: sonraki seans açılışı, boşluk korumaları, slipaj fiyatta
            if o > row["entry_trigger"] * (1.0 + MAX_ENTRY_GAP_PCT):
                resolved.append(_resolve(row, dstr, "no_fill_gap")); continue
            if o <= row["stop"]:
                resolved.append(_resolve(row, dstr, "no_fill_gap_stop")); continue
            row.update({"status": "active", "entry": o * (1.0 + slip), "entry_date": dstr,
                        "hi": h, "lo": l, "bars_held": 0})
            # doldurma günü barı da yürünür (motor da aynı gün stop/hedefe bakar) — aşağıya düş
        if row["status"] == "active":
            row["hi"] = max(row.get("hi", h), h); row["lo"] = min(row.get("lo", l), l)
            ex = None
            # broker._touch_exit ile AYNI iki kademe: önce AÇILIŞ (barın ilk basılan
            # fiyatı — sırası kesin), sonra bar içi (sıra bilinemez → stop önce). Eski sıra bar-içi
            # stop dokunuşunu açılıştaki hedef boşluğunun ÖNÜNE koyuyordu; bu defterde GERÇEKLEŞTİ:
            # CF-2025-10-28-SWKS-momentum_burst, bar(o=83.14, h=84.53, l=78.59), hedef 82.74,
            # stop 79.27 → açılış zaten hedefin üstündeydi, satır -1.01R yazıldı; doğrusu ≈-0.02R.
            if o <= row["stop"]:
                ex = (o, "stop_gap")
            elif o >= row["target"]:
                ex = (o, "target_gap")
            elif l <= row["stop"]:
                ex = (row["stop"], "stop")
            elif h >= row["target"]:
                ex = (row["target"], "target")
            elif row["bars_held"] + 1 >= row.get("time_stop_days", DEFAULT_TIME_STOP):
                ex = (c, "time_stop")
            if ex:
                resolved.append(_resolve(row, dstr, "closed", exit_px=ex[0], reason=ex[1]))
            else:
                row["bars_held"] += 1; still.append(row)
    store.write_json(OPEN_FILE, still)
    for r in resolved:
        store.append_jsonl(LEDGER, r)
    return {"open": len(still), "resolved": len(resolved)}


def surum_dokumu() -> dict:
    """Defterin STRATEJİ SÜRÜMÜ kırılımı — `strategy_version` damgasının OKUYUCUSU (YASA 6).

    OPERATÖRÜN SORUSUNU CEVAPLAR: "sistem son tohumdan beri gelişti; kanıt bugünün
    stratejisini mi yansıtıyor?" Damga olmadan bu soru defterden çıkmıyordu ve tarih
    aralığına bakan bir sezgiyle kuruluyordu (`exhaustion_hammer` 15 satır vs
    `breakout_vcp` 6079 — fark yetenek değil, geri dolumun o kurulum varken koşulmamış
    olmasıydı).

    `damgasiz` AYRI SAYILIR ve bu bilinçli: damgasız satırlar 2026-08-25'ten ESKİdir ve
    hangi sürümle üretildikleri BİR DAHA bilinemez. Onları bir sürüme yamamak, ölçülemeyeni
    ölçülmüş göstermek olurdu. Sayı küçüldükçe defter tazelenmiş demektir.

    AÇIK ve ÇÖZÜLMÜŞ satırların İKİSİ birden sayılır: kanıtın tamamı budur, yalnız
    çözülmüşe bakmak açık izlemedeki tazeliği görünmez kılardı.
    """
    dokum: dict[str, int] = {}
    damgasiz = 0
    for r in list(store.read_json(OPEN_FILE, [])) + list(store.read_jsonl(LEDGER)):
        if not isinstance(r, dict):
            continue
        v = r.get("strategy_version")
        if v is None:
            damgasiz += 1
        else:
            dokum[str(v)] = dokum.get(str(v), 0) + 1
    return {"dokum": dokum, "damgasiz": damgasiz, "n": sum(dokum.values()) + damgasiz,
            "beyan": ("`damgasiz` = 2026-08-25 öncesi satırlar; sürümü BİR DAHA bilinemez. "
                      "Sayı küçüldükçe defter bugünün stratejisiyle tazelenmiş demektir.")}


def resolved_rows(entered_only: bool = True, include_near_miss: bool = False) -> list:
    """near_miss satırları VARSAYILAN dışarıda: 8 mevcut tüketici (silahlanma, skill-katkı, gölge model,
    LLM kalibrasyonu, öz-değerlendirme…) eşik-altı gölge adaylarla seyrelmemeli — onlar yalnız
    near_miss_report'un sorusudur ("hangi eşik masada para bırakıyor?")."""
    rows = store.read_jsonl(LEDGER)
    if not include_near_miss:
        rows = [r for r in rows if not r.get("near_miss")]
    return [r for r in rows if r.get("entered")] if entered_only else rows
