"""loop.py — canlı ileri-yönlü kâğıt döngüsü: kapanan her işlem günü için bir kez koşan günlük
karar motoru.

Yeni kapanmış barın üzerine tam bir tur işler: rejimi kurar, açık pozisyonları yeni barda yönetir,
evreni tarayıp giriş planları üretir ve koruma kapılarından geçirir, uygun planları bir sonraki
seansın açılışı için silahlandırır, öğrenme katmanını besler ve kalp atışını yazar. Ayna (Alpaca
kâğıt) tarafında gerçek emrin TEK kapısı da buradadır; dolum/ret/koruma mutabakatı da bu modülde işlenir.

Kilit girişler: `daily_cycle(bars, index, on_date)` (ana giriş; zamanlayıcı/worker bunu çağırır),
`mirror_submit_armed` / `mirror_submit_ve_kalicilastir` (tek gönderim kapısı — intraday gönderim
bacağı da buradan geçer), `reconcile_broker_state` (broker mutabakatı), `operator_onay_ver` /
`girise_uygun` (plan onay yolu), `_persist_trade` (kapanan işlem, tekilleştirilmiş),
`_persist_equity_point` (sermaye eğrisinin kadanslı yazarı).

Değişmezler: backtest ile AYNI strategy.py/broker.py kullanılır — canlı ve simüle davranış
ayrışamaz; kararlar ancak evrenin ÇOĞUNLUĞUNUN barı olan seansta alınır (kapsama kapısı: yanlı bir
kesitte karar vermektense bir gün geride olmak dürüsttür); strategy.yaml mtime değişince sıcak
yüklenir — parametre değişikliği için yeniden dağıtım yok; ölçüm katmanı (giriş-icra/slipaj defteri)
kararı ASLA bloklamaz ama düşerse sessiz de kalmaz; keşif sondaları sert R tavanlarıyla sınırlıdır
(rejim kilitlenmesini kırmak için — kanıt birikmeyen rejim sonsuza dek aç kalıyordu).

Okur/yazar: portfolio.json (kalıcı defter — öğrenme yeniden başlatmayı atlatır), trade_plans.jsonl,
trades.jsonl, entry_execution.jsonl (okuyan: analytics → tanılama → pano), equity_curve.json,
kalp atışı (health.write_heartbeat). Komşular: strategy, broker, regime, guard, dataset, skills,
adapters.data, adapters.alpaca, obs."""
from __future__ import annotations
import datetime as dt
import pandas as pd

from . import config, store, strategy as strat, regime as regime_mod, indicators as ind
from . import guard, health, skills, dataset, obs, earnings, rollback, ledgerstamp
from .adapters import data as data_adapter
from .backtest import SECTORS, _adv
from . import broker as BR                 # E1 giriş-icra yasası (olay adları + karar fonksiyonları)
from .broker import PaperBroker, derisk_mult, max_positions_at, bps_delta as _bps
from .score import START_EQUITY

PORTFOLIO = "portfolio.json"
# KEŞİF (mikro-sonda) bütçesi — rejim kilitlenmesini kırar: bütçe %0 rejimlerde kanıt birikmiyordu
# (chop: 3.5 yılda 8 işlem) → rejim-koşullu makine sonsuza dek aç kalıyordu. Sert tavanlar:
EXPLORE_MAX_R = 0.25       # keşif SONDASI başına risk tavanı (R)
EXPLORE_MAX_POS = 5        # öğrenme debisi (operatör, 2026-07-20 akşam): kâğıt modunda kanıt debisi öncelik
EXPLORE_TOTAL_R = 1.25     # 5 × 0.25R — toplam keşif riski hâlâ hesabın %1.25'i (kâğıt)
MIRROR_DRIFT_TOL = 0.005   # >0.5% gap between internal sim fill and actual Alpaca fill → mirror_drift alarm

# ---- E2: GİRİŞ İCRA / SLİPAJ DEFTERİ ----------------------------------------------------------
# NEDEN AYRI DEFTER: `trades.jsonl` KAPANMIŞ işlemi yazar; girişin İCRASI (hangi yasa, hangi limit,
# doldu mu, dolmadıysa neden, dolduysa resmî açılışa göre kaç bps) orada yeri olmayan ve çoğu zaman
# HİÇ KAPANMAYAN bir olgudur — kaçan bir giriş asla bir trade satırı doğurmaz, yani mevcut deftere
# yazılamazdı ve tam bu yüzden bugüne kadar ÖLÇÜLMÜYORDU. `broker_reconcile.json` ise anlık görüntü
# (tarihçe yok, üzerine yazılır); slipaj bir DAĞILIM sorusudur ve tek anlık görüntüyle sorulamaz.
# OKUYUCULAR (YASA 6 zinciri): analytics.entry_execution_summary → /api/diagnostics `icra` → pano;
# ayrıca E3 kalibratörü (analytics.pessimistic_band_update) ampirik bandı buradan üretir.
ENTRY_LEDGER = "entry_execution.jsonl"
ENTRY_LEDGER_CAP = 4000    # satır tavanı — defter büyür, sonsuza dek değil
# İÇ-MOTOR TOTOLOJİSİ: iç motorun "dolum vs resmî açılış" bps'i TOTOLOJİKtir — dolum fiyatı
# açılıştan SABİT slippage ile türetilir (broker.fill_entry: base_fill = açılış × (1+slippage_bps/1e4)
# + modellenmiş likidite etkisi), gerçek bir piyasa dolumu değildir. Açılışa göre bps ölçmek tanımı
# gereği slippage_bps sabitini geri üretir. UYDURMA YASAĞI + ÖLÇÜLEMEDİ≠0 → satıra None + bu beyan
# yazılır (E1 grid'i bu bacağı KAPSAMAZ; o `fill_vs_limit_bps` limit-bacağını ölçer).
IC_ACILIS_TOTOLOJI_BEYAN = (
    "ÖLÇÜLEMEDİ: iç-motor dolumu açılıştan SABİT slippage ile türetiliyor "
    "(base_fill = açılış × (1+slippage_bps/1e4) + likidite etkisi), gerçek piyasa dolumu DEĞİL — "
    "resmî açılışa göre bps tanımı gereği slippage_bps sabitini yeniden üretir (totoloji, ölçüm değil)")


def _entry_exec_write(row: dict) -> None:
    """E2 defterine tek satır. ASLA döngüyü bozmaz (ölçüm katmanı kararı bloklamaz), ama sessizce
    de kaybolmaz: yazım düşerse olay defterine uyarı düşer.

    KİLİT: append `file_lock(ENTRY_LEDGER)` altında. `store.append_jsonl`in
    dosya dalı KİLİTSİZdir (store.py) ve aynı deftere `_entry_exec_trim`/`_patch_entry_slippage`
    OKU-DEĞİŞTİR-YAZ uygular; kilit olmadan bir trim/patch, araya düşen bir append'i EZERDİ (write
    tüm defteri yeniden yazar). Üç E2 yazarı da aynı kilidi paylaşır — `_save_broker`ın PORTFOLIO
    deseninin aynısı; kilit süreç-içi RLock + süreçler-arası flock (store._FileLock)."""
    try:
        with store.file_lock(ENTRY_LEDGER):
            store.append_jsonl(ENTRY_LEDGER, {"ts": dt.datetime.now(dt.timezone.utc)
                                              .isoformat(timespec="seconds"), **row})
    except Exception as e:
        obs.warn("entry_exec_ledger_write_failed", error=f"{type(e).__name__}: {e}",
                 plan_id=row.get("plan_id"), ticker=row.get("ticker"))


def _reject_class(detail, veto=None, reachable=None) -> str:
    """Broker ret METNİNİ sınıfa indirger — özet yüzeyinde "ret dağılımı" ancak sınıflanabilir bir
    eksende anlamlıdır (ham metin sembol adı taşır, her satır tekil görünür). TANINMAYAN metin
    `diger` olur ve ham metin satırda KALIR: sınıflandırma bir özettir, kanıtın yerine geçmez."""
    if veto:
        return "gap_veto"
    if reachable is False:
        return "unreachable"
    s = str(detail or "").lower()
    if "stop price" in s and "current price" in s:
        return "stop_vs_current"        # E1'in kapattığı KÖK NEDEN — sayacı sıfıra inmeli
    if "insufficient" in s or "buying power" in s:
        return "buying_power"
    if "tradable" in s or "halted" in s or "inactive" in s:
        return "not_tradable"
    if "duplicate" in s or "client_order_id" in s:
        return "duplicate_coid"
    if "qty" in s or "quantity" in s:
        return "qty"
    if "wash" in s:
        return "wash_trade"
    if "limit price" in s or "limit_price" in s:
        return "limit_price"
    return "diger"


def _entry_exec_trim() -> None:
    """Tavanı aşan defteri en yeni ENTRY_LEDGER_CAP satıra indirir (döngü sonunda, ucuz).

    KİLİT: oku-değiştir-yaz TEK kritik bölge — read ile write `file_lock(ENTRY_LEDGER)`
    altında; araya bir append/patch girip yeni satırı kaybettiremez."""
    try:
        with store.file_lock(ENTRY_LEDGER):
            rows = store.read_jsonl(ENTRY_LEDGER)
            if len(rows) > ENTRY_LEDGER_CAP:
                store.write_jsonl(ENTRY_LEDGER, rows[-ENTRY_LEDGER_CAP:])
    except Exception as e:
        obs.warn("entry_exec_ledger_trim_failed", error=f"{type(e).__name__}: {e}")


UNIVERSE_MIN_COVERAGE = 0.90   # kararlar, evrenin en az bu oranının barı olan seansta alınır
UNIVERSE_LAG_MAX_D = 5         # bu kadar geriye bakılır; daha eskisi veri arızasıdır (uyarı)


class _MirrorUnreachable(Exception):
    """Ayna (Alpaca) ulaşılamıyor: gönderim atlanır, planlar SİLAHLI kalır — iç defter tek gerçek."""


# ==================================================================================================
# AYNA ÇIKIŞ KUYRUĞU — İÇ MOTORUN ÇIKIŞ KARARI AYNAYA İLETİLİR
# ==================================================================================================
# BULGU: `pending_exits` → `close_position` yolu (time_stop / regime_flip / giveback / erken itlaf)
# YALNIZ iç defteri kapatıyordu. Aynadaki bracket TP/SL taşıdığı için pozisyon AÇIK kalıyor,
# mutabakat onu `engine_orphans` sayıp HER TURDA alarm basıyor ve sembol `_mirror_busy` üzerinden
# kalıcı olarak karar dışına düşüyordu. Kuyruk üç şey için var:
#   1. İki motorun ÇIKIŞI da aynı kararla kapansın (giriş tarafı E1'de zaten hizalanmıştı).
#   2. Kapatma DÜŞERSE yetim SESSİZ kalmasın — alarm + bir sonraki döngüde yeniden deneme.
#   3. Çıkış-kaynaklı yetim, "iç defter planı düşürdü ama ayna doldu" (split-brain) yetiminden
#      AYRI sınıflansın: ikisi farklı teşhis, aynı isimle sayılırlarsa ikisi de okunamaz hâle gelir.
# İKİ-MOTOR YASASI: iç motorun ÇIKIŞ KARARI burada DEĞİŞMEZ — yalnız ayna o kararı izler.
# DOKUNULMAYAN: intraday `_touch_exit` (TP/SL) çıkışlarının aynada KARŞILIĞI VARDIR (bracket'ın
# kendi bacakları doldurur) — onları buradan kapatmak çift satış olurdu. `scale_out`un ayna boşluğu
# ise bilinçli ve belgeli (reconcile `scaled` dalı), bu tur onu da değiştirmez.
MIRROR_EXIT_KEY = "mirror_exit_pending"

# ==================================================================================================
# ÇIKIŞ DOLUM-YAMASI KUYRUĞU (teşhis docs/TESHIS-WPE-AYNA-DOLUM-2026-08-10.md)
# ==================================================================================================
# İKİ BOŞLUK, TEK MEKANİZMA:
#   "karar" kolu — karar-çıkışı dolum körlüğü: `DELETE /v2/positions` kapatması coid'i Alpaca-üretimi YENİ bir
#        market emri doğurur; trades-yaması yalnız `by_coid[plan_id]`in bacaklarını okuduğu için o
#        dolum HİÇBİR deftere akmıyordu (fotoğrafta kapanışların ~%38'i — slipaj örneklemi sistematik
#        olarak TP/SL-bacağına yanlıydı). Artık kapatma cevabındaki emir kimliği (`close_order_id`)
#        kuyruğa yazılır ve reconcile o emrin `filled_avg_price`ını okuyup satırı yamalar.
#   "bacak" kolu — tek-atış yaması: eski (1.3) yalnız AYNI TURDA kapananlara bakıyordu; kapanış turundaki API
#        arızası ya da bacağın FARKLI GÜNDE dolması yamayı SONSUZA DEK kaybediyordu (E2'nin giriş
#        yarısı her tur yeniden denerken çıkış yarısı denemiyordu — asimetri). Kuyruk kalıcıdır
#        (_save_broker anahtarı), her reconcile turunda yeniden denenir, tavana varınca VAZGEÇİŞ
#        OLAYLIDIR ve satıra dürüst beyan düşer (fiyat UYDURULMAZ: None + neden).
# EMİR ÜRETMEZ: kuyruk yalnız OKUR ve yamalar — bu tur ölçüm/görünürlük turudur (icra yok).
EXIT_FILL_KEY = "exit_fill_pending"
EXIT_FILL_MAX_TRIES = 5     # tur; sınırlı pencere — sonsuz retry yeni bir sessizlik sınıfı olurdu
EXIT_FILL_CAP = 80          # kuyruk tavanı (kapanış debisi küçük; taşma patolojiktir ve OLAYLIdır)


def _exit_fill_kaydet(meta: dict, plan_id, ticker, *, kaynak: str, dstr: str,
                      order_id=None, order_id_neden=None, reason=None) -> None:
    """Kapanan işlemi çıkış dolum-yaması kuyruğuna yaz. `kaynak`:
      * "karar" — DELETE kapatması; dolum `close_order_id`li emirden okunacak.
      * "bacak" — dokunuş çıkışı; dolum parent bracket'ın TP/SL bacağından okunacak (eski 1.3 yolu,
                  artık yeniden-denemeli).
    İdempotent: plan_id kuyruktaysa üzerine YAZILMAZ (karar kaydının order_id'si korunur; yalnız
    eksik order_id sonradan gelirse tamamlanır). plan_id yoksa satır eşlenemez → dürüst uyarı."""
    if not plan_id:
        obs.warn("exit_fill_patch_planidsiz", ticker=ticker, kaynak=kaynak,
                 detail="kapanan işlemde plan_id yok — trades satırı ayna dolumuyla eşlenemez, "
                        "yama kuyruğuna ALINMADI (ölçülemedi; uydurma eşleme yok)")
        return
    q = meta.setdefault(EXIT_FILL_KEY, {})
    cur = q.get(plan_id)
    if cur is not None:
        if order_id and not cur.get("order_id"):
            cur["order_id"] = str(order_id)
            cur["kaynak"] = kaynak
        return
    if len(q) >= EXIT_FILL_CAP:
        en_eski = min(q, key=lambda k: str(q[k].get("since") or ""))
        dusen = q.pop(en_eski)
        obs.warn("exit_fill_kuyruk_tasti", dusen_plan_id=en_eski, ticker=dusen.get("ticker"),
                 cap=EXIT_FILL_CAP,
                 detail="çıkış dolum-yaması kuyruğu tavana vurdu — en eski kayıt beyansız düştü; "
                        "bu debi patolojiktir (kapanış sayısı ≤ pozisyon tavanı olmalı)")
    q[plan_id] = {"ticker": ticker, "kaynak": kaynak, "order_id": (str(order_id) if order_id else None),
                  "order_id_neden": order_id_neden, "reason": reason, "since": dstr, "tries": 0}


def _mirror_exit_enqueue(meta: dict, ticker: str, plan_id, reason: str, dstr: str) -> None:
    """İç motorun uyguladığı çıkışı ayna kuyruğuna yazar. Yalnız `alpaca_paper` modunda: iç-broker
    modunda kuyruk hiç doğmaz (davranış birebir eskisi)."""
    if config.BROKER != "alpaca_paper":
        return
    pend = meta.setdefault(MIRROR_EXIT_KEY, {})
    cur = dict(pend.get(ticker) or {})
    pend[ticker] = {"plan_id": plan_id or cur.get("plan_id"),
                    "reason": reason or cur.get("reason"),
                    "since": cur.get("since") or dstr,
                    "tries": int(cur.get("tries") or 0),
                    "naked": bool(cur.get("naked"))}


def _mirror_exit_sync(meta: dict, dstr: str) -> dict:
    """Kuyruktaki her çıkışı aynada uygular. BAŞARISIZI KUYRUKTA BIRAKIR — bir sonraki döngüde
    yeniden denenir; hiçbir yetim sessizce terk edilmez (deneme sayısı satırda taşınır).

    Denemeye tavan KOYULMADI bilerek: "N denemeden sonra vazgeç" tam olarak sessiz yetim üretirdi.
    Kuyruk pozisyon sayısıyla sınırlıdır (≤ max_open_positions), yani sınırsız büyüyemez."""
    out: dict = {"closed": [], "failed": [], "skipped": None}
    pend = dict(meta.get(MIRROR_EXIT_KEY) or {})
    if not pend:
        return out
    if config.BROKER != "alpaca_paper":
        out["skipped"] = f"broker={config.BROKER}"
        return out
    from .adapters import alpaca
    if not alpaca.paper_available():
        out["skipped"] = "paper_available()=False"
        obs.warn("mirror_exit_deferred", n=len(pend), tickers=sorted(pend),
                 detail="Alpaca kimliği/erişimi yok — ayna çıkışı ERTELENDİ, kuyruk duruyor")
        return out
    kalan: dict = {}
    for t, info in pend.items():
        info = dict(info or {})
        info["tries"] = int(info.get("tries") or 0) + 1
        try:
            res = alpaca.close_engine_position(t, plan_id=info.get("plan_id"))
        except Exception as e:
            res = {"ok": False, "detail": f"{type(e).__name__}: {e}", "naked": False}
        if res.get("ok"):
            out["closed"].append({"ticker": t, "qty": res.get("closed_qty"), "tries": info["tries"]})
            # KARAR KOLU: kapatma emrinin kimliği dolum-yaması kuyruğuna — reconcile o emrin
            # `filled_avg_price`ını okuyup trades satırına yamalar (E2 giriş-yamasının simetriği).
            # `closed_qty=0` dalı (pozisyon zaten yoktu) kuyruğa YAZILMAZ: ölçülecek dolum yok.
            if float(res.get("closed_qty") or 0.0) > 0:
                _exit_fill_kaydet(meta, info.get("plan_id"), t, kaynak="karar", dstr=dstr,
                                  order_id=res.get("close_order_id"),
                                  order_id_neden=res.get("close_order_neden"),
                                  reason=info.get("reason"))
            obs.log("mirror_exit_closed", ticker=t, plan_id=info.get("plan_id"),
                    reason=info.get("reason"), qty=res.get("closed_qty"), tries=info["tries"],
                    cancelled=len(res.get("cancelled") or []),
                    # OLAY-KATMANI YÜZÜ: kapatma EMRİNİN kimliği olayda taşınır — dolum fiyatı
                    # bu anda HENÜZ yok (market emri az önce doğdu), fiyatı reconcile yaması yazar.
                    close_order_id=res.get("close_order_id"),
                    close_order_neden=res.get("close_order_neden"),
                    detail=str(res.get("detail", ""))[:120])
            continue
        info["naked"] = bool(info.get("naked")) or bool(res.get("naked"))
        info["son_detay"] = str(res.get("detail", ""))[:200]
        info["owned"] = bool(res.get("owned"))
        kalan[t] = info
        out["failed"].append({"ticker": t, **{k: info[k] for k in ("tries", "naked", "son_detay")}})
        obs.alarm(obs.ALARM_MIRROR_DRIFT,           # SABİT sapma sınıfı (çıkış icra edilemedi, sizing değil)
                  f"ayna çıkışı kapatılamadı: {t} ({info.get('reason')}) — iç defter KAPALI, aynada "
                  f"AÇIK; {info['tries']}. deneme"
                  + (" — KORUMA BACAĞI İPTAL EDİLDİ, pozisyon ÇIPLAK" if info["naked"] else ""),
                  ticker=t, plan_id=info.get("plan_id"), tries=info["tries"],
                  naked=info["naked"], owned=info["owned"], detail=info["son_detay"],
                  # iptal→kapat kapısı — True ise kapatma hiç DENENMEDİ (koruma/bacak iptali
                  # düştü ve emir hâlâ canlı); yarım-durum yerine bu turu alarmla geçirdik.
                  cancel_failed=bool(res.get("cancel_failed")),
                  drift_sinifi="cikis_yetimi")
    meta[MIRROR_EXIT_KEY] = kalan
    return out


# ==================================================================================================
# SİLAHLI PLANIN KAPI-DIŞI DÜŞÜRÜLMESİ — SESSİZ DEĞİL
# ==================================================================================================
# BULGU: `if not halted and not breaker and not data_bad and size_mult > 0:` tutmazsa TÜM silahlı
# planlar `carried=[]` ile hiçbir olay / defter satırı / `broker_status` damgası olmadan yok
# oluyordu. Aynı sessizlik plan başına da vardı (`if len(b.positions) < eff_max_open and ...` else'siz).
# İLKE ZATEN AYNI DOSYADA YAZILI (gap-veto dalı): "silahlı bir planın kaybolma sebebi defterden
# okunabilmeli". Bu blok o ilkeyi kapı-dışı düşürmelere uygular. KARAR DEĞİŞMEZ: plan yine düşer.
def _stamp_plan_status(plans: list) -> None:
    """Düşürülen planların `broker_status` damgasını trade_plans.jsonl'a KALICI yazar.

    Neden `merge_dated_jsonl` değil: o çağrı bir TARİHİN tüm satırlarını verilen listeyle DEĞİŞTİRİR
    — elimizde yalnız düşen alt küme varken kullanmak aynı günün diğer planlarını SİLERDİ. Kilitli
    `update_jsonl` ile satır bazında yama yapılır (araya giren yazarlar korunur)."""
    by_id = {p.get("id"): p.get("broker_status") for p in (plans or [])
             if p.get("id") and p.get("broker_status")}
    if not by_id:
        return

    def _yama(rows: list) -> bool:
        """Plan defteri satırlarına yeni `broker_status` damgasını basar; değişiklik olduysa True.

        Yalnız DEĞİŞEN satıra dokunur — araya giren yazarların satırları korunur."""
        ch = False
        for r in rows:
            s = by_id.get(r.get("id"))
            if s and r.get("broker_status") != s:
                r["broker_status"] = s
                ch = True
        return ch

    try:
        store.update_jsonl("trade_plans.jsonl", _yama)
    except Exception as e:
        obs.warn("plan_status_stamp_failed", error=f"{type(e).__name__}: {e}", n=len(by_id))


def _armed_drop_row(pl: dict, dstr: str, gate: str, **extra) -> None:
    """Düşen silahlı plana: `broker_status` damgası + olay + E2 defter satırı (üçü birden).

    E2'DE `motor="kapi"` — BİLİNÇLİ: bu satır ne iç motorun ne aynanın bir İCRA kararıdır, plan
    ikisine de ULAŞMADAN kapıda düştü. `motor="ic"` yazsaydık `analytics.entry_execution_summary`
    kartın kill-ölçütü olan `dolmama_orani`nın PAYDASINI şişirirdi — ölçüm eşiği kod değişikliğiyle
    sessizce kayardı (kill-list dokunulmazdır). ÖLÇÜM BORCU KAPANDI:
    `analytics.entry_execution_summary` artık `kapi` kovasını AYRI sayıyor (`kapi_dagilimi` —
    betimleyici, oran/eşik ÜRETMEZ) ve pano mutabakat masası onu yüzeye çıkarıyor; eski okuyucular
    — olay defteri (`armed_dropped`) ve plan satırının `broker_status` damgası — yanında aynen
    duruyor (gap-veto ile birebir aynı desen)."""
    status = f"armed_dropped_{gate}"
    pl["broker_status"] = status
    obs.warn("armed_dropped", ticker=pl.get("ticker"), plan_id=pl.get("id"), gate=gate,
             broker_status=status, plan_date=pl.get("date"),
             detail="silahlı plan kapı-dışı koşulda düşürüldü — dolum HİÇ denenmedi", **extra)
    _entry_exec_write({"date": dstr, "plan_id": pl.get("id"), "ticker": pl.get("ticker"),
                       "motor": "kapi", "entry_trigger": pl.get("entry_trigger"),
                       "karar": status, "fill": None,
                       "fill_vs_resmi_acilis_bps": None, "fill_vs_limit_bps": None,
                       "red_detay": {"kapi": gate, **extra}})


# İKİ ÇAĞIRAN, İKİ OLAY ADI: aynı iptal YOLU iki FARKLI olguyu anlatır.
# HALT/breaker "motor durduruldu, ayna da dursun" der; günlük kadans "bu emrin seansı bitti, tetiği
# bayatladı" der. Tek adla yazılsalardı olay defterini okuyan her gece "HALT oldu" sanardı — ve o
# okuma UYDURMA olurdu (YASA 6: okuyucusuz/yanlış-okunan yazım yok).
EV_MIRROR_ENTRIES_CANCELLED = "mirror_entries_cancelled"        # HALT/breaker kapısı
EV_STALE_ENTRIES_CANCELLED = "mirror_stale_entries_cancelled"   # günlük kadans — bayat tetik


def _cancel_mirror_entries(dstr: str, gate: str, *, olay: str = EV_MIRROR_ENTRIES_CANCELLED,
                           detail: str = "HALT/breaker: aynadaki dolmamış giriş emirleri "
                                         "kapatıldı (sahiplik önekli)") -> dict:
    """Aynadaki DOLMAMIŞ giriş emirlerini kapat — İKİ çağıranın ORTAK yolu.

    Eskiden HALT yalnız İÇ tarafı durduruyordu; ayna emri D-1 akşamından TIF=day ile canlıydı ve
    HALT onu iptal etmiyordu — iç motor "bugün giriş yok" derken ayna dolabiliyordu. Sahiplik
    süzgeci adaptörün İÇİNDE (`cancel_open_entries`: yalnız ENGINE_COID_PREFIX önekli, yalnız
    DOLMAMIŞ emirler; dolmuş parent'ın koruma bacaklarına DOKUNULMAZ).

    `olay`/`detail` ÇAĞIRANIN beyanıdır: mekanizma aynı, ANLATI farklı (bkz. yukarıdaki iki sabit).
    Varsayılanlar HALT/breaker dalınındır — yani bu turdan önceki tek çağıranın davranışı birebir
    korunur."""
    if config.BROKER != "alpaca_paper":
        return {"skipped": f"broker={config.BROKER}"}
    try:
        from .adapters import alpaca
        if not alpaca.paper_available():
            return {"skipped": "paper_available()=False"}
        res = alpaca.cancel_open_entries()
        obs.log(olay, gate=gate, date=dstr,
                cancelled=len(res.get("cancelled") or []), kept=len(res.get("kept") or []),
                foreign=len(res.get("foreign") or []), detail=detail)
        return res
    except Exception as e:
        obs.warn("mirror_entry_cancel_failed", error=f"{type(e).__name__}: {e}", gate=gate)
        return {"ok": False, "detail": f"{type(e).__name__}: {e}"}


# ==================================================================================================
# BAYAT TETİK ARTIK TIF'e HAVALE EDİLEMEZ — GÜNLÜK KADANS İPTALİ
# ==================================================================================================
# NEDEN DOĞDU: `broker.ENTRY_TIF` DAY iken bayat-tetik korumasını BROKER yapıyordu — dolmamış giriş
# emri seans kapanışında kendiliğinden sönüyordu. Ama Alpaca bracket'ında `time_in_force` TEKTİR ve
# emrin TAMAMINA uygulanır: aynı DAY, DOLMUŞ pozisyonların koruma bacaklarını da her akşam
# öldürüyordu (ölçüm: 2026-08-06 20:00-20:02Z, dört pozisyon çıplak). TIF GTC'ye alındı; koruma
# artık yaşıyor — ve bayat-tetik koruması bu fonksiyonla motorun kendi eline geçti.
# YETKİ GENİŞLEMESİ DEĞİL: iptal yine adaptörün denetlenmiş yolundan geçer — yalnız
# ENGINE_COID_PREFIX önekli (operatörün emri `foreign`, dokunulmaz), yalnız `filled_qty=0`
# (dolmuş parent `kept`), koruma bacaklarına ASLA. Yani bu çağrı, DAY'in körlemesine yaptığı işin
# yalnız DOĞRU YARISINI yapar.
def _cancel_stale_entry_orders(dstr: str) -> dict:
    """Günlük kadans: bir SEANS için silahlanmış, o seansta dolmamış giriş emirlerini geri çek.

    NE ZAMAN: `daily_cycle`ta, o seansın dolum kararları verildikten SONRA ve yeni planlar
    silahlanıp aynaya gönderilmeden ÖNCE. Bu sıra zorunludur — daha erken çağrılsa bugünün
    kararı bir emri iptal ederdi, daha geç çağrılsa BU AKŞAM gönderilen taze emirleri keserdi.

    KAPI-KOŞULSUZ (HALT/breaker/veri/kısma dallarında da koşar): kapı kapalıysa `meta["armed"]`
    zaten boşaltılıyor, yani iç motor o planları KALICI olarak düşürüyor. Aynadaki GTC emri
    yaşamaya devam etseydi iç defterin düşürdüğü bir planı ayna doldurabilirdi — loop.py'nin
    kendi adını koyduğu "motor yetimi"/split-brain sınıfı, üstelik artık süresiz. HALT dalında
    `_armed_dropped_by_gate` zaten iptal ettiği için bu çağrı o gün 0 iptal bulur ve olay defteri
    bunu dürüstçe yazar (iki ayrı ad, iki ayrı satır).

    KAPSAM SINIRI — BEYANLI (TIF=day'e göre TEK davranış farkı): `daily_cycle` seansı İŞLEMEDEN
    dönerse (`no dates` / `waiting_for_universe` / `refused_regressive`) bu kadans koşmaz ve GTC
    emri o seansı aşar; DAY'de emir kendiliğinden sönerdi. BİLİNÇLİ: o dallarda iç motor kararını
    HENÜZ VERMEMİŞTİR ve silahlı küme duruyordur — emri geri çekmek "iç taraf doldurur, aynada
    emir yok" ayrışmasını üretirdi, yani hatanın ters yönünü. Kalan risk bayat tetiğin bir seans
    daha yaşamasıdır ve tavanı zaten `_carry_armed_without_bar`ın tek-seans taşıma yasasıdır.
    `noop` dalı (bu seans zaten işlendi) da BİLEREK dışarıda: kadans o gün ZATEN koştu, ve döngü
    300 sn'de bir uyandığı için oraya bağlamak her poll'de bir broker iptal turu demek olurdu."""
    return _cancel_mirror_entries(
        dstr, "gunluk_kadans", olay=EV_STALE_ENTRIES_CANCELLED,
        detail="günlük kadans: seansı biten dolmamış giriş emirleri geri çekildi — bayat tetik "
               "sonraki seansa taşınmaz. Koruma bacakları YAŞAR (dolmuş parent `kept` altında).")


def _armed_dropped_by_gate(meta: dict, dstr: str, gate: str) -> None:
    """Kapı kapalıyken TÜM silahlı planlar düşer (KARAR AYNEN KORUNDU) — ama artık defterden
    okunabilir biçimde. HALT/breaker'da ayrıca aynadaki dolmamış girişler iptal edilir; bu iptal
    silahlı plan OLMASA DA koşar, çünkü ayna emri önceki akşamdan kalmış olabilir."""
    if gate in ("halt", "breaker"):
        _cancel_mirror_entries(dstr, gate)
    armed = list(meta.get("armed") or [])
    if not armed:
        return
    for pl in armed:
        _armed_drop_row(pl, dstr, gate)
    _stamp_plan_status(armed)
    obs.log("armed_dropped_batch", gate=gate, n=len(armed), date=dstr,
            tickers=[p.get("ticker") for p in armed][:10])


# ==================================================================================================
# OPERATÖR ONAYI — REVIEW PLANININ TEK KOŞUL NOKTASI
# ==================================================================================================
# OPERATÖR ŞİKÂYETİ: "review edebiliyorum, işlem yapamıyorum". Ölçüm doğruladı: kapı REVIEW
# hükmü verdiğinde pano planı GÖSTERİYOR ama operatörün elinde tek bir eylem yoktu — ve keşif
# modunda (bütçe %0 ya da uyuyan kurulum) REVIEW planı HİÇ silahlanmıyor (aşağıdaki iki dal
# `explore_pool`a YALNIZ GO alıyordu). Yani hüküm okunabiliyor, uygulanamıyordu.
#
# ONAY BİR OLAYDIR, HÜKÜM DEĞİL (UYDURMA YASAĞI): `gate_verdict` GERİYE DÖNÜK DEĞİŞMEZ — kapı o
# an ne dediyse defterde o kalır; operatörün onayı planın YANINA kendi zaman damgası ve kanalıyla
# yazılır (`operator_onayi`). Kapı istatistikleri (verdict_counts, kill ölçütleri, cf defteri) bu
# yüzden KİRLENMEZ: onaylı bir REVIEW hâlâ bir REVIEW'dür ve öyle sayılır.
#
# NO_GO ASLA ONAYLANMAZ (mutlak): guard'ın sert kuralı bir bilgi eksikliği değil bir REDdir;
# operatöre "bu reddi ez" düğmesi vermek kapının kendisini kaldırmak olurdu. Onay yalnız
# "insan baksın" diyen hükmü kapatır, reddi değil.
ONAY_ALANI = "operator_onayi"
ONAY_KANALI = "pano"


def operator_onayli(pl: dict) -> bool:
    """Planda operatör onayı OLAYI var mı? (Alanın varlığı değil, damgası ölçülür.)"""
    o = pl.get(ONAY_ALANI)
    return bool(isinstance(o, dict) and o.get("ts"))


def girise_uygun(pl: dict, verdict: str | None = None) -> bool:
    """TEK KOŞUL NOKTASI: bu plan giriş kuyruğuna (silahlanma) girebilir mi?

    GO → evet. REVIEW → YALNIZ operatör onayı varsa. NO_GO → ASLA, koşulsuz.

    KAPI ATLANMAZ, OKUNUR: bu fonksiyon guard'ın hükmünü YENİDEN DEĞERLENDİRMEZ ve hiçbir kapıyı
    devre dışı bırakmaz — silahlanma sonrası dolum yolundaki kapıların TAMAMI (HALT, devre kesici,
    veri kalitesi, slot tavanı, de-risk çarpanı, E1 limit/gap yasası) aynen koşar. Buradaki tek
    soru, planın o kapılara ULAŞIP ulaşmadığıdır."""
    v = str(verdict if verdict is not None else (pl.get("gate_verdict") or ""))
    if v == "NO_GO":
        return False
    return v == "GO" or (v == "REVIEW" and operator_onayli(pl))


def operator_onay_ver(plan_id: str, *, kanal: str = ONAY_KANALI) -> dict:
    """Panodan gelen "onayla ve arm et" niyeti — TEK YAZIM YOLU (uç nokta buradan geçer).

    NEDEN api.py'DE DEĞİL BURADA: `trade_plans.jsonl`in yazar listesi `ledgers.CONTRACTS`ta
    YAZILIDIR (loop/run/hermes). Uç noktanın deftere kendi eliyle yazması, o sözleşmenin var olma
    sebebi olan "kimsenin haberi olmadan ikinci yazar" sınıfının yeni bir örneği olurdu. Uç nokta
    niyeti bildirir, defterin yasası burada yaşar (`api_halt` → `health.set_halt` ile aynı desen).

    İKİ YAZIM, İKİ DEFTER: (1) plan satırına onay damgası — kapı hükmü DEĞİŞMEDEN; (2) kitabın
    silahlı kümesine plan — çünkü onay döngüden SONRA gelir ve `daily_cycle` aynı seansı yeniden
    üretmez (`meta["last_date"] == dstr` → noop). Silahlı kümeye girmeyen bir onay, hiçbir şey
    yapmayan bir düğme olurdu.

    ONAY = İCRA YETKİSİ (2026-08-11, İŞ-2-EOD — tarihçe-koru): v190'daki sözleşme "EMİR GÖNDERMEZ"
    idi ve gerekçesi "ikinci bir emir yolu açmamak"tı. P-2026-08-07-VLO vakası bu sözleşmenin
    boşluğunu kanıtladı: döngüden SONRA gelen onay, bir sonraki turun açılış fazında iç motorca
    dolup silahlı kümeden çıkıyor ve `mirror_submit_armed`ın P3-sonu çağrısı onu HİÇ görmüyordu —
    onaylı emir Alpaca'ya hiç gitmedi. Artık onay anında AYNI TEK KAPIDAN gönderilir
    (`mirror_submit_ve_kalicilastir` → `mirror_submit_armed` — ikinci emir gövdesi YOK, tek kapı korunur);
    dolum bir sonraki açılışta iç motorun kapılarından geçerek olur.

    YARIŞ PENCERESİ, BEYANLI: `_save_broker` kitabı yazarken `armed`ı DÖNGÜNÜN belleğinden basar.
    Onay tam bir döngü turunun ortasında gelirse bu ekleme o turun yazımıyla kaybolabilir (pencere
    dar: döngü günde bir kez koşar). Kayıp sessiz değildir — onay damgası plan satırında KALIR,
    pano rozeti onaylı gösterir ve plan silahlı kümede görünmez; ayrıca `daily_cycle` aynı seansı
    yeniden işlerse onayı satırdan geri okur (`_onaylar` taşıması).

    Dönüş sözleşmesi: {"ok", "kod", "neden", ...}. `kod` HTTP durumudur ve uç nokta onu AYNEN
    kullanır: 404 (plan defterde yok) · 409 (onaylanamaz — sebebi `neden`de) · 200 (onaylandı)."""
    rows = store.read_jsonl("trade_plans.jsonl")
    plan = next((r for r in reversed(rows) if r.get("id") == plan_id), None)
    if plan is None:
        return {"ok": False, "kod": 404, "neden": f"plan defterde yok: {plan_id}"}
    verdict = str(plan.get("gate_verdict") or "?")
    if verdict == "NO_GO":
        return {"ok": False, "kod": 409,
                "neden": "NO_GO onaylanamaz — disiplin kapısının sert reddi MUTLAKTIR; "
                         "onay yalnız 'insan baksın' diyen REVIEW hükmünü kapatır"}
    if verdict != "REVIEW":
        return {"ok": False, "kod": 409,
                "neden": f"yalnız REVIEW planı onaylanır (bu planın kapı hükmü: {verdict})"}
    pdate = str(plan.get("date") or "")
    if not pdate:
        return {"ok": False, "kod": 409,
                "neden": "planın tarihi yok — seans geçerliliği ÖLÇÜLEMİYOR, onay verilmez"}
    meta = store.read_json("portfolio.json", {}) or {}
    book_at = str(meta.get("last_date") or "")
    if book_at and pdate < book_at:
        return {"ok": False, "kod": 409,
                "neden": f"seansı geçmiş plan onaylanamaz (plan {pdate}, kitap {book_at}) — "
                         f"planlar TEK SEANS geçerlidir; seviyeleri bayat, bir daha silahlanamaz"}
    if health.halted():
        return {"ok": False, "kod": 409,
                "neden": "HALT aktif — yeni giriş silahlanmaz. Onaylasaydık plan bir sonraki turda "
                         "kapı-dışı düşerdi (armed_dropped_halt); sessiz bir 'onaylandı' yerine "
                         "dürüst bir ret: önce DEVAM et"}
    ticker = plan.get("ticker")
    if ticker in (meta.get("positions") or {}):
        return {"ok": False, "kod": 409,
                "neden": f"{ticker} zaten açık pozisyon — aynı isimde ikinci giriş yok"}
    armed = list(meta.get("armed") or [])
    zaten_silahli = any(a.get("id") == plan_id for a in armed)
    _tavan = int(config.goal()["limits"]["max_open_positions"])
    _acik = len(meta.get("positions") or {})
    if not zaten_silahli and _acik + len(armed) >= _tavan:
        return {"ok": False, "kod": 409,
                "neden": f"slot yok: {_acik} açık + {len(armed)} silahlı, tavan {_tavan} "
                         f"(max_open_positions) — onay kapıyı gevşetemez"}

    zaten_onayli = operator_onayli(plan)
    onay = (plan.get(ONAY_ALANI) if zaten_onayli
            else {"ts": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                  "kanal": str(kanal)[:24]})
    if not zaten_onayli:
        def _onay_yaz(rows_: list) -> bool:
            """Plan defterinde bu plana operatör onayı damgasını basar (yalnız onay alanı BOŞSA).

            Hüküm alanına (`gate_verdict`) DOKUNULMAZ; ikinci kez çağrılırsa yeniden yazmaz."""
            ch = False
            for r in rows_:
                if r.get("id") == plan_id and not r.get(ONAY_ALANI):
                    r[ONAY_ALANI] = onay          # hüküm alanına DOKUNULMAZ (gate_verdict aynen)
                    ch = True
            return ch
        store.update_jsonl("trade_plans.jsonl", _onay_yaz)

    def _arm_yama(doc):
        """Onaylanan planı kitabın silahlı kümesine ekler; zaten varsa hiçbir şey yazmaz.

        DEDUP: ikinci onay ikinci emir doğurmaz — aynı plan kimliği kümede varsa False döner."""
        if not isinstance(doc, dict):
            return False
        arm = list(doc.get("armed") or [])
        if any(a.get("id") == plan_id for a in arm):
            return False                          # dedup: ikinci onay ikinci emir doğurmaz
        arm.append({**plan, ONAY_ALANI: onay})
        doc["armed"] = arm
        return True

    kitap = store.update_json("portfolio.json", _arm_yama, {})
    # E1 İCRA YASASI VAR MI? `entry_law[plan_id]` sinyal barı kapanışında sabitlenmiş atr/ref_price
    # taşır (as-of ihlali yok). YOKSA UYDURULMAZ: dolum yalnız yüzde tavanıyla kurulur ve bu satır
    # operatöre BEYAN edilir — döngü v190'dan beri bu seansın REVIEW planlarının yasasını da tutar,
    # yani yasa yokluğu ancak eski (v190 öncesi üretilmiş) planlarda görülür.
    yasa_var = bool((kitap.get("entry_law") or {}).get(plan_id))
    # ================================================================================================
    # ONAY = İCRA YETKİSİ (İŞ-2-EOD, operatör 2026-08-11 — P-2026-08-07-VLO fiyaskosu):
    # "EMİR GÖNDERMEZ" sözleşmesi kaldırıldı. Eski akışta onay yalnız silahlı kümeye yazıyor, aynaya
    # gönderim döngünün P3 sonuna (ya da pano düğmesine) kalıyordu; döngüden SONRA gelen onay bir
    # SONRAKİ turun AÇILIŞ fazında iç motorca dolup silahlı kümeden çıkınca aynaya emir HİÇ gitmedi
    # (VLO: iç dolum 304.04×61, aynada sıfır emir, split_brain). Artık onay anında AYNI TEK KAPIDAN
    # (mirror_submit_ve_kalicilastir → mirror_submit_armed) gönderilir — iç motor hangi yasayla
    # (E1-v2, entry_law yan tablosu) dolduracaksa ayna da aynı yasayla, planın SİLAHLANMA ANINDA
    # emirlenir (normal akışın birebir karşılığı: silahlanma akşamı gönderim). Setup'ın ARMED_SETUPS'ta
    # olup olmaması BURADA süzgeç DEĞİLDİR: onaylı plan gönderilir (onay = icra yetkisi).
    # SESSİZLİK YASAK (İŞ-3a): gönderimin sonucu — ya da yolun yokluğu — yanıt ve olayda AÇIKÇA yazar;
    # onay REDDEDİLMEZ (operatör bilerek iç-defter denemesi yapabilir).
    # ================================================================================================
    if config.BROKER != "alpaca_paper":
        gonderim = None
        icra_yolu = (f"AYNA KAPALI — onay yalnız İÇ-DEFTERE işler, broker'a emir GİTMEZ "
                     f"(broker={config.BROKER}); iç dolum bir sonraki açılışta")
    else:
        try:
            gonderim = mirror_submit_ve_kalicilastir(source="onay", sadece_plan_id=plan_id)
        except Exception as e:
            gonderim = {"ok": False, "submitted": 0, "detail": f"{type(e).__name__}: {e}"}
            obs.warn("onay_gonderim_dustu", plan_id=plan_id, error=f"{type(e).__name__}: {e}",
                     detail="onay-anı ayna gönderimi istisnayla düştü — plan SİLAHLI, döngünün "
                            "geç-gönderim kemeri (daily_cycle) yeniden dener")
        _sonuc0 = (gonderim.get("results") or [{}])[0]
        if gonderim.get("ok") and gonderim.get("submitted"):
            icra_yolu = (f"ayna: bracket GÖNDERİLDİ (coid={plan_id}, qty={_sonuc0.get('qty')}) — "
                         f"iç dolum bir sonraki açılışta, ayna dolumu tetik kesişiminde")
        elif _sonuc0.get("dedup"):
            icra_yolu = "ayna: emir ZATEN gönderilmişti (dedup) — ikinci emir doğmadı"
        elif plan_id in (gonderim.get("dropped_ids") or []):
            icra_yolu = (f"ayna: gönderim DÜŞTÜ ve plan silahlı kümeden çıkarıldı "
                         f"({str(_sonuc0.get('detail') or gonderim.get('detail') or '')[:160]}) — "
                         f"iç motor da doldurmayacak (tek yasa)")
        else:
            icra_yolu = (f"ayna: GÖNDERİLEMEDİ ({str(gonderim.get('detail') or _sonuc0.get('detail') or '?')[:160]}) "
                         f"— plan SİLAHLI kaldı; onay iç-deftere işler, broker'a HENÜZ gitmedi. "
                         f"Döngünün geç-gönderim kemeri yeniden dener; bekçi (ONAYLI_PLAN_GONDERILMEDI) "
                         f"dolum sonrası boşluğu alarmlar")
    ev = obs.log("plan_operator_approved", plan_id=plan_id, ticker=ticker, date=pdate,
                 gate_verdict=verdict, kanal=onay.get("kanal"), icra_yasasi=yasa_var,
                 zaten_onayliydi=zaten_onayli, zaten_silahliydi=zaten_silahli,
                 armed_n=len(kitap.get("armed") or []),
                 icra_yolu=icra_yolu,
                 gonderim_ok=(None if gonderim is None else bool(gonderim.get("ok") and gonderim.get("submitted"))),
                 detail="operatör REVIEW planını onayladı — kapı hükmü DEĞİŞMEDİ (onay bir "
                        "olaydır); plan giriş kuyruğuna alındı VE aynaya gönderim onay anında "
                        "denendi (onay = icra yetkisi, 2026-08-11); dolum kapıları (HALT/breaker/"
                        "veri/slot/de-risk/E1 limit) aynen koşar")
    return {"ok": True, "kod": 200, "plan_id": plan_id, "ticker": ticker, "date": pdate,
            "gate_verdict": verdict, ONAY_ALANI: onay, "silahli": plan_id not in set((gonderim or {}).get("dropped_ids") or []),
            "zaten_onayliydi": zaten_onayli, "zaten_silahliydi": zaten_silahli,
            "icra_yasasi": yasa_var, "armed_n": len(kitap.get("armed") or []),
            "ts": ev.get("ts"),
            "icra_yolu": icra_yolu,
            "gonderim": (None if gonderim is None else
                         {"ok": bool(gonderim.get("ok")), "submitted": gonderim.get("submitted", 0),
                          "detail": str(gonderim.get("detail") or "")[:200],
                          "dropped_ids": gonderim.get("dropped_ids") or []}),
            "not": (None if yasa_var else
                    "E1 icra yasası (atr/ref_price) bu plan için defterde YOK — limit yalnız yüzde "
                    "tavanıyla kurulur, ATR ölçülemedi (uydurulmadı)"),
            "neden": "onaylandı — plan silahlı kuyruğa alındı; iç dolum bir sonraki açılışta; "
                     "aynaya gönderim ONAY ANINDA tek kapıdan denendi (sonuç: icra_yolu)"}


# ==================================================================================================
# AYNAYA GÖNDERİM — TEK KAPI
# ==================================================================================================
# BULGU: bu gövde YALNIZ `daily_cycle`ın içinde yaşıyordu ve panodaki "gönder" düğmesi
# (api.py /api/alpaca/submit_armed) kendi ÇIPLAK `submit_plan` çağrısını kuruyordu. Sonuç: ikinci
# bir emir yolu — de-risk çarpanı YOK (%5 düşüşte iç motor 0,6 ile doldururken düğme TAM boyut
# gönderiyordu), entry_law girdileri (atr/ref_price) YOK (aynı planda İKİ farklı limit tavanı;
# üstelik ref_price=None gap dalını `marketable_limit`e çevirip kırılım teyidini tümden kaldırıyordu),
# dedup (`alpaca_submitted`) YOK, E2 defter satırı YOK, `_MirrorUnreachable` reddi YOK (hesap
# okunamazken hayali 100k üzerinden boyutlandırıyordu).
# BU TURDA MANTIK DEĞİŞMEDİ, TAŞINDI: iki çağıran da buradan geçer. Ayrım yalnız GİRDİLERİN
# NEREDEN GELDİĞİNDE: döngü kendi taze `eq_now`/`plans`ını verir, uç nokta veremediği için
# fonksiyon onları defterden okur (okunamazsa REDDEDER — hayali sermayeyle gönderim yok).
def mirror_submit_armed(meta: dict, dstr: str, *, eq_now: float | None = None,
                        plans: list | None = None, halted: bool | None = None,
                        source: str = "loop") -> dict:
    """Silahlı planları Alpaca PAPER aynasına gönderir (E1 yasası + de-risk + dedup + E2 + red sınıfı).

    `meta` YERİNDE değiştirilir (armed / alpaca_submitted / broker_rejected) — KALICILIK ÇAĞIRANIN
    İŞİDİR: döngü tur sonunda `_save_broker` ile yazar, uç nokta dönen `submitted_ids`/`dropped_ids`
    ile portfolio.json'a KİLİT ALTINDA yama uygular (canlı worker'ın armed setini ezmemek için tam
    belge yazımı YASAK).

    `eq_now`: İÇ defterin güncel öz sermayesi — de-risk çarpanının PAYDASI `meta['peak_equity']` ile
    aynı defterden gelmek zorundadır (Alpaca öz sermayesiyle karıştırmak çarpanı bozar). None ise
    nabızdan okunur; nabız da yoksa gönderim REDDEDİLİR (UYDURMA YASAĞI: ölçülemeyen çarpan 1.0
    varsayılamaz — tam olarak tek-kapı yasasının düzelttiği kusur budur)."""
    out: dict = {"ok": False, "submitted": 0, "results": [], "equity": None, "detail": "",
                 "source": source, "submitted_ids": [], "dropped_ids": []}
    if config.BROKER != "alpaca_paper":
        return {**out, "detail": f"broker={config.BROKER} — ayna kapalı"}
    if halted is None:
        halted = health.halted()
    if halted:
        return {**out, "detail": "HALT aktif — emir gönderilmez"}
    if not meta.get("armed"):
        return {**out, "ok": True, "detail": "silahlı plan yok"}
    from .adapters import alpaca
    if not alpaca.paper_available():
        # DAVRANIŞ FARKI, BEYANLI: döngü eskiden bu kapıyı hiç kontrol etmiyor, anahtarsız
        # hâlde `account()`u çağırıp `_MirrorUnreachable` üzerinden HER TUR bir BROKER_REJECT
        # ALARMI basıyordu. Anahtar YOKLUĞU bir broker arızası değil bir YAPILANDIRMA hâlidir —
        # alarm sınıfını kirletiyordu. Sessizleşmedi, SINIFI DÜŞTÜ: uyarı olarak kayda geçer.
        obs.warn("mirror_submit_skipped", kaynak=source, n=len(meta.get("armed") or []),
                 detail="ALPACA_PAPER_KEY yok — ayna gönderimi atlandı, planlar SİLAHLI kaldı")
        return {**out, "detail": "Alpaca paper anahtarları yok"}
    # BOYUT MAKBUZU: makbuzun `eq_kaynak` alanı — çarpanın PAYININ HANGİ DAL'dan geldiği.
    # Döngü kendi `eq_now`unu geçirir ("eq_now"); pano düğmesi geçirmez ve nabızdan okunur ("nabiz").
    # BAYAT-SERMAYE vakasında 6 Ağustos AMGN bacağı tam olarak bayat NABIZDAN boyutlandı — makbuz
    # bu ayrımı tek alanda söyler. Fallback `eq_now`u yeniden atamadan ÖNCE yakalanır.
    _eq_kaynak = "eq_now" if eq_now is not None else "nabiz"
    if eq_now is None:
        _hb = store.read_json(health.HEARTBEAT, {}) or {}
        if _hb.get("equity") is None:
            return {**out, "detail": "iç defter öz sermayesi okunamadı (nabızda `equity` yok) — "
                                     "de-risk çarpanı ÖLÇÜLEMEZ, gönderim reddedildi"}
        eq_now = float(_hb["equity"])
    try:
        acct = alpaca.account()
        if acct is None and not alpaca.transport()["ok"]:
            # ULAŞILAMADI ≠ 100k. Hesap okunamıyorken START_EQUITY'ye düşmek, hayali bir
            # sermaye üzerinden boyutlandırmak demekti; üstelik gönderimler de ağ hatasıyla
            # düşüp geçerli planları 'broker reddi' diye siliyordu. Aynayı ATLA, planlar
            # SİLAHLI kalsın — iç defter zaten tek gerçek (denetim 2026-07-21).
            obs.alarm(obs.ALARM_BROKER_REJECT,
                      f"Alpaca ulaşılamıyor — ayna atlandı, {len(meta['armed'])} plan silahlı kaldı",
                      detail=alpaca.transport().get("error", "")[:160])
            raise _MirrorUnreachable()
        eq = float(acct["equity"]) if acct and "equity" in acct else START_EQUITY
        out["equity"] = eq
        submitted, sent, rejected, kept = set(meta.get("alpaca_submitted", [])), 0, [], []
        vetoed: list = []              # E1 gap-risk vetosu — ret DEĞİL, kendi kararımız
        # BOYUT MAKBUZU: kitabın o anki KİMLİĞİ — makbuzdaki `kitap_rev`. Bir sonraki tur dolum
        # anındaki rev ile kıyaslanırsa "kitap gönderim↔dolum arasında DEĞİŞTİ Mİ" (bayat-sermaye
        # sınıfı) tek bakışta okunur. Arka-uç bağımsız: DB'de entity rev, dosyada boyut damgası —
        # ikisi de yalnız İÇERİK değişince değişen bir sayaç (store.stamp). `peak` de bir kez okunur.
        _kitap_rev = store.stamp(PORTFOLIO)[1]
        _peak = meta.get("peak_equity", START_EQUITY)
        for pl in meta["armed"]:
            if pl["id"] in submitted:
                kept.append(pl)
                out["results"].append({"ticker": pl.get("ticker"), "ok": False,
                                       "detail": "zaten gönderildi (dedup)", "dedup": True})
                continue
            # E1: ayna İÇ MOTORLA AYNI icra girdilerini alır — ATR ve referans fiyat
            # yan tablodan (silahlanma anında sabitlendi), yasa `broker.entry_law`dan.
            _lw = (meta.get("entry_law") or {}).get(pl.get("id")) or {}
            _smult = derisk_mult(eq_now, _peak)   # mirror the SAME drawdown de-risk as the internal fill
            # BOYUT MAKBUZU: plan başına, çarpanın ÜÇ girdisi (eq_now · peak ·
            # size_mult) + hangi daldan geldiği (eq_kaynak) + kitabın kimliği (kitap_rev). Yeni defter/
            # gerçek kaynağı YOK: meta["size_law"] `_save_broker`ın 14. anahtarı olarak kalıcılaşır.
            # Gönderim SONUCUNDAN bağımsız yazılır — reddedilen/veto edilen planın da boyut TABANI
            # kanıttır (bayat-sermaye turunda sapmayı çözmek üç deftere bakmayı gerektirmişti).
            meta.setdefault("size_law", {})[pl.get("id")] = {
                "eq_kaynak": _eq_kaynak, "eq_now": round(float(eq_now), 2),
                "peak": round(float(_peak), 2), "size_mult": round(float(_smult), 4),
                "kitap_rev": _kitap_rev}
            res = alpaca.submit_plan(pl, eq, size_mult=_smult,
                                     atr=_lw.get("atr"), ref_price=_lw.get("ref_price"))
            out["results"].append({"ticker": pl.get("ticker"), **res})
            _law_out = res.get("law") or _lw
            _entry_exec_write({
                "date": dstr, "plan_id": pl.get("id"), "ticker": pl.get("ticker"),
                "motor": "ayna", "entry_trigger": pl.get("entry_trigger"),
                "limit": _law_out.get("limit"), "atr": _law_out.get("atr"),
                "law": _law_out.get("law"), "emir_tipi": _law_out.get("mode"),
                "tif": _law_out.get("tif"), "gap_at_submit": _law_out.get("gap_at_submit"),
                "karar": ("submitted" if res.get("ok")
                          else ("gap_veto" if res.get("veto")
                                else ("unreachable" if res.get("reachable") is False
                                      else "rejected"))),
                "red_nedeni": (None if res.get("ok") else str(res.get("detail", ""))[:200]),
                "red_sinifi": (None if res.get("ok")
                               else _reject_class(res.get("detail"), veto=res.get("veto"),
                                                  reachable=res.get("reachable"))),
                "kaynak": source,
                "qty": res.get("qty"), "fill": None,
                "fill_vs_resmi_acilis_bps": None, "fill_vs_limit_bps": None})
            if res.get("veto"):
                # GAP-RİSK VETOSU: bizim kararımız, broker reddi DEĞİL. Plan silahlı
                # KALMAZ (iç motor da `gap_at_submit` üzerinden aynı vetoyu uygular —
                # tek yasa) ve ret dağılımına yazılmaz, yoksa broker sağlığı hakkında
                # yanlış bir sayı üretirdi. Plan SATIRI damgalanır: silahlı bir planın
                # kaybolma sebebi defterden okunabilmeli (broker_status ile aynı desen).
                pl["broker_status"] = "gap_veto"
                vetoed.append(pl)
                out["dropped_ids"].append(pl["id"])
                obs.log(BR.EV_GAP_VETO, ticker=pl.get("ticker"), plan_id=pl.get("id"),
                        trigger=pl.get("entry_trigger"), limit=_law_out.get("limit"))
                continue
            if res.get("ok"):
                submitted.add(pl["id"]); sent += 1; kept.append(pl)
                out["submitted_ids"].append(pl["id"])
            elif res.get("reachable") is False:
                # ağ arızası — plan SİLAHLI kalır, 'reddedildi' diye düşürülmez
                kept.append(pl)
                obs.log("alpaca_submit_unreachable", ticker=pl["ticker"],
                        detail=str(res.get("detail", ""))[:160])
            else:
                # STRICT (Phase 1.1): a rejected order is NOT marked submitted and is DROPPED from
                # the armed set, so the internal broker never fills a phantom trade next open.
                pl["broker_status"] = "failed_broker_rejection"
                rejected.append({"date": dstr, "plan_id": pl["id"], "ticker": pl["ticker"],
                                 "detail": str(res.get("detail", ""))[:200]})
                out["dropped_ids"].append(pl["id"])
                obs.alarm(obs.ALARM_BROKER_REJECT, f"Alpaca reddi: {pl['ticker']} — {res.get('detail','')}",
                          ticker=pl["ticker"], plan_id=pl["id"])
            obs.log("alpaca_submit", ticker=pl["ticker"], ok=res.get("ok"),
                    detail=res.get("detail", ""), kaynak=source)
        meta["armed"] = kept                       # phantom-free: only Alpaca-accepted plans stay armed
        meta["alpaca_submitted"] = list(submitted)[-200:]
        if rejected or vetoed:
            # DURABLE failed_broker_rejection: trade_plans.jsonl was serialized BEFORE this branch,
            # so re-merge the (same, now-mutated) plan dicts — the on-disk rows gain broker_status.
            # Also keep a bounded ledger in portfolio meta; reconcile surfaces it to the dashboard.
            # `plans` YOKSA (pano yolu — o tur üretilmiş plan listesi elimizde değil) satır bazında
            # kilitli yama: merge_dated_jsonl bir TARİHİN tüm satırlarını değiştirdiği için alt
            # kümeyle çağrılamaz (aynı günün diğer planlarını silerdi).
            if plans is not None:
                store.merge_dated_jsonl("trade_plans.jsonl", dstr, plans)
            else:
                _stamp_plan_status(list(vetoed)
                                   + [{"id": r["plan_id"],
                                       "broker_status": "failed_broker_rejection"} for r in rejected])
            meta["broker_rejected"] = (meta.get("broker_rejected", []) + rejected)[-50:]
        if sent:
            obs.log("alpaca_orders_sent", n=sent, equity=eq, kaynak=source)
        return {**out, "ok": True, "submitted": sent}
    except _MirrorUnreachable:  # sessiz-yutma: ayna erişilemezliğinin alarmı yukarıda ZATEN yazıldı; burada ikinci kez uyarmak aynı olayı çiftler
        return {**out, "detail": "ayna ulaşılamıyor — planlar silahlı kaldı", "unreachable": True}
    except Exception as e:
        obs.warn("alpaca_submit_failed", error=f"{type(e).__name__}: {e}", kaynak=source)
        return {**out, "detail": f"{type(e).__name__}: {e}"}


# ==================================================================================================
# TEK KAPI + KALICILAŞTIRMA — DÖNGÜ-DIŞI ÇAĞIRANLARIN ORTAK YOLU (İŞ-2-EOD/4b, 2026-08-11)
# ==================================================================================================
# VAKA (P-2026-08-07-VLO, operatör: "onayladığım bir emrin gönderilmemesi büyük bir fiyasko"):
# operatör onayı planı silahlı kümeye koyuyordu ama aynaya GÖNDERİM yalnız iki yerden tetikleniyordu
# — döngünün P3 sonu (:1640) ve pano düğmesi. Onay döngüden SONRA gelince plan bir SONRAKİ turun
# AÇILIŞ fazında iç motorca dolup silahlı kümeden çıkıyor, :1640 onu hiç görmüyordu → Alpaca'ya emir
# hiç gitmedi, reconcile split_brain alarmladı. Bu yardımcı, pano ucundaki gönderim+kalıcılaştırma
# desenini (api_alpaca_submit_armed) fonksiyonlaştırır ki onay anı ve intraday 4b AYNI tek kapıdan
# (mirror_submit_armed) geçsin; İKİNCİ bir emir gövdesi yazılmaz.
def mirror_submit_ve_kalicilastir(dstr: str | None = None, *, source: str,
                                  sadece_plan_id: str | None = None) -> dict:
    """Diskteki kitabı okuyarak silahlı planları aynaya gönderir ve yan etkileri portfolio.json'a
    KİLİT ALTINDA yamalar (tam-belge yazımı YASAK — canlı worker'ın armed setini ezerdi; pano ucuyla
    birebir aynı yama: dedup kümesine ekle, düşenleri kimlikle çıkar, boyut makbuzunu bas).

    `sadece_plan_id`: verilirse YALNIZ o plan gönderilir (görünüm-meta: armed daraltılır; dedup /
    entry_law / peak / size_law kitaptan). intraday 4b bunu kullanır — silahlı kümedeki DİĞER
    planların gönderim anı kendi tetikleyicilerinindir (onay anı ya da döngü), 4b'nin değil.

    YARIŞ PENCERESİ, BEYANLI (operator_onay_ver docstring'indeki pencerenin ikizi): döngü tam bu
    anda `_save_broker` yazarsa buradaki yama kaybolabilir. Kayıp sessiz ve tehlikesiz değil ama
    KEMERLİ: (a) Alpaca coid teklik yasası aynı planın ikinci bracket'ını reddeder; (b) 4b'nin
    Alpaca-tarafı idempotens kontrolü (açık emir + pozisyon) gönderim öncesi ayrıca bakar."""
    kitap = store.read_json(PORTFOLIO, {}) or {}
    meta = kitap
    if sadece_plan_id is not None:
        secilen = [p for p in (kitap.get("armed") or []) if p.get("id") == sadece_plan_id]
        if not secilen:
            return {"ok": False, "submitted": 0, "results": [], "equity": None,
                    "submitted_ids": [], "dropped_ids": [],
                    "detail": f"plan silahlı kümede değil: {sadece_plan_id}"}
        meta = {**kitap, "armed": secilen}
    # BOŞ TARİH YASAK (pano ucundaki gerekçenin aynısı): E2 penceresi `date >= cutoff` ile süzüyor —
    # boş dize her pencereden sessizce düşerdi. Satırın tarihi eylemin tarihidir.
    if not dstr:
        dstr = str(meta.get("last_date") or dt.date.today().isoformat())
    res = mirror_submit_armed(meta, dstr, source=source)
    gonderilen, dusen = set(res.get("submitted_ids") or []), set(res.get("dropped_ids") or [])
    if gonderilen or dusen:
        def _yama(doc):
            """Gönderim sonucunu kitaba kalıcılaştırır: gönderilen kimlikler biriktirilir, veto/ret yiyen
            planlar silahlı kümeden KİMLİKLE düşer, ret listesi ve boyut makbuzu tazelenir.

            STRICT yasa: düşen plan kümede kalmaz — iç motor bir sonraki açılışta hayalet dolum
            yapamaz."""
            if not isinstance(doc, dict):
                return False
            doc["alpaca_submitted"] = list(dict.fromkeys(
                list(doc.get("alpaca_submitted") or []) + sorted(gonderilen)))[-200:]
            # STRICT yasa (Phase 1.1) burada da: veto/ret yiyen plan silahlı kümeden KİMLİKLE çıkar —
            # iç motor bir sonraki açılışta hayalet dolum yapamaz.
            doc["armed"] = [p for p in (doc.get("armed") or []) if p.get("id") not in dusen]
            doc["broker_rejected"] = meta.get("broker_rejected", doc.get("broker_rejected", []))
            # boyut makbuzu (pano bacağıyla aynı kilit-altı desen): meta'nın makbuzu diskteki belgeye
            # basılır; meta'nınki kitabın kendi sözlüğünden tohumlandığı için içerik-koruyucudur.
            doc["size_law"] = meta.get("size_law", doc.get("size_law", {}))
            return True
        store.update_json(PORTFOLIO, _yama, {})
    return {**res, "submitted_ids": sorted(gonderilen), "dropped_ids": sorted(dusen)}


def _universe_drift_check() -> None:
    """Elle bakımlı evren endeksten düşmüş isim taşıyor mu? 2026-07-21'de 7 ölü sembol ELLE
    bulunmuştu; artık bunu söyleyen bir mekanizma var (adapters.constituents denetimi, tur 3).
    Günde bir kez yeter — constituents.current() zaten günlük önbellekli. Asla döngüyü bozmaz."""
    try:
        from .adapters import constituents as _con
        rep = _con.universe_drift()
        store.write_json("universe_drift.json", {**rep, "date": dt.date.today().isoformat()})
        if rep.get("status") == "ok" and rep.get("n_stale"):
            obs.alarm("DATA_QUALITY",
                      f"evren sapması: {rep['n_stale']} sembol S&P 500'de yok — {', '.join(rep['stale'][:8])}",
                      n_stale=rep["n_stale"])
    except Exception as e:
        obs.warn("universe_drift_failed", error=f"{type(e).__name__}: {e}")


def _load_broker() -> tuple[PaperBroker, dict]:
    """Kitabı diskten yükler: `(PaperBroker, meta)`.

    Nakit, gerçekleşmiş K/Z, son emir kimliği ve açık pozisyonlar `portfolio.json`dan geri kurulur;
    kayma/komisyon hedef sözleşmesinden okunur. Defter yoksa boş bir meta (silahlı küme, bekleyen
    çıkışlar, gün-başı sermaye) döner — uydurma durum üretilmez."""
    goal = config.goal()
    slip = float(goal.get("slippage_bps", 5))
    comm = float(goal.get("commission_per_share", 0.0))
    st = store.read_json(PORTFOLIO, None)
    b = PaperBroker(START_EQUITY, slip, comm)
    if st:
        b.cash = st["cash"]; b.realized_pnl = st["realized_pnl"]; b._id = st.get("last_id", 0)
        from .broker import Position
        for t, p in st.get("positions", {}).items():
            b.positions[t] = Position(**p)
    return b, (st or {"armed": [], "pending_exits": {}, "last_date": None,
                      "day_start_equity": START_EQUITY, MIRROR_EXIT_KEY: {}})


_HOTSTATE_OFF_LOGGED: set = set()


def _hotstate_off_once(key: str, where: str, reader: str) -> None:
    """Kapatılmış sıcak-yazımın SÜREÇ BAŞINA BİR KEZ kaydı.

    Neden hiç kaydetmemek değil: sessizce kaldırılmış bir yazım, aylar sonra "Redis'te fiyat neden
    yok?" sorusunu kaynaksız bırakır. Neden her turda değil: statik bir olgu için günlük olay yazmak,
    obs defterini bilgi taşımayan satırlarla şişirir. Her restart'ta bir kez → durum güncel kalır,
    defter temiz kalır."""
    if key in _HOTSTATE_OFF_LOGGED:
        return
    _HOTSTATE_OFF_LOGGED.add(key)
    obs.log("hotstate_write_disabled", key=key, where=where, reader=reader,
            detail=f"yalnız-yazılır katman kapatıldı (2026-07-30): {reader} üretimde hiç çağrılmıyor; "
                   f"hotstate fonksiyonu SİLİNMEDİ, kanca yorumda — tüketici gelince tek satır")


def _save_broker(b: PaperBroker, meta: dict) -> None:
    """Kitabı diske yaz — SAHİPLENİLEN ALANLARI YAMALAYARAK, belgeyi EZEREK DEĞİL.

    2026-08-04 VAKASI (research/olcumler/portfoy_sifirlama_2026-08-04/KOKNEDEN.md). Bu fonksiyon
    `store.write_json(PORTFOLIO, st)` ile belgeyi TAM yazıyordu ve `st` SABİT 13 ANAHTARLIK bir
    beyaz listeydi. Sonuç: listede olmayan her anahtar ilk noop-olmayan döngüde SESSİZCE yok
    oluyordu. Canlıda yok olan şey, operatörün 2026-08-01'de yazdığı SERMAYE BEYANIYDI
    (`sermaye_resetleri`) — beyan gidince `recompute` ofseti 0'a düştü ve üç kimlik birden kırıldı.
    "Seçici sıfırlama" görüntüsü sıfırlamada değil, SERİLEŞTİRMENİN BEYAZ LİSTESİNDEYDİ.

    NEDEN DAR BİR YAMA (`st["sermaye_resetleri"] = …`) DEĞİL: o, sınıfı bir kez daha ELLE kapatmak
    olurdu — bir sonraki beyan anahtarını yazan kişi aynı tuzağa düşerdi. Yapısal kapı, sahipliği
    yazarın KENDİ listesiyle sınırlamaktır: `update_json` diskteki belgeyi kilit altında okur,
    üstüne yalnız aşağıdaki 14 alanı basar; yabancı anahtarlar (bugünkü beyan VE gelecekteki her
    beyan) yerinde yaşar. Aynı aile: `health.write_heartbeat` çok-yazarlı nabız alanları, `storage._touch`
    eğri zarfı.

    RATCHET: yazımdan ÖNCE, aynı kilit altında, beyan ölçüsü İKİ kaynakla kıyaslanır —
    diskteki belge ve döngünün tur başında okuduğu `meta`. Ölçü düşüyorsa yazım REDDEDİLİR ve
    alarm basılır: `_save_broker` bu kaybı çimentolayan yazar olamaz."""
    from dataclasses import asdict
    st = {"cash": b.cash, "realized_pnl": b.realized_pnl, "last_id": b._id,
          "positions": {t: asdict(p) for t, p in b.positions.items()},
          "armed": meta.get("armed", []), "pending_exits": meta.get("pending_exits", {}),
          "last_date": meta.get("last_date"), "day_start_equity": meta.get("day_start_equity", START_EQUITY),
          # both survive restarts: alpaca_submitted is the double-submit dedup set (losing it re-fires
          # brackets after every restart — Alpaca's duplicate-client_order_id rejection was the only net);
          # broker_rejected is the failed-submission ledger the dashboard reads via broker_reconcile.
          "alpaca_submitted": meta.get("alpaca_submitted", []),
          "broker_rejected": meta.get("broker_rejected", []),
          # E1: silahlı planların icra kararı (limit/ATR/gap) — RESTART'I ATLATMALI. Yoksa
          # yeniden başlatma sonrası dolum yasası "ATR ölçülemedi"ye düşer ve aynı plan iki farklı
          # limitle iki motorda ayrışır (tam olarak bu turun kapattığı kusur).
          "entry_law": meta.get("entry_law", {}),
          # peak_equity MUST survive restarts/reloads: every cycle reloads meta from disk, so without
          # this the running peak collapsed to max(START_EQUITY, current) — drawdown always read ~0 and
          # the graded de-risk ramp + position throttle were PERMANENTLY inert.
          "peak_equity": meta.get("peak_equity", START_EQUITY),
          # AYNA ÇIKIŞ KUYRUĞU: aynada kapatılamamış çıkışlar RESTART'I ATLATMALI. Kaybolursa iç defteri kapalı,
          # aynası açık bir pozisyon sessizce kalıcı yetim olur — bu bulgunun ta kendisi.
          MIRROR_EXIT_KEY: meta.get(MIRROR_EXIT_KEY, {}),
          # BOYUT MAKBUZU (docs/BAYAT-SERMAYE-KOK-2026-08-07.md): plan başına —
          # RESTART'I ATLATMALI (entry_law ile aynı gerekçe, 14. sahiplenilen anahtar). Bayat-sermaye
          # turunun bekçisi: 08-05 aynanın yarım boyutlu emrini çözmek ÜÇ ayrı deftere (portfolio /
          # events / trade_plans) bakmayı gerektirmişti; makbuz boyut kararının girdilerini TEK
          # satırda söyler (eq_kaynak · eq_now · peak · size_mult · kitap_rev; dolum-anı damgasından beri iç dolum
          # anında `dolum_eq`/`dolum_peak` ikinci yarısı damgalanır). Yazan: mirror_submit_armed.
          "size_law": meta.get("size_law", {}),
          # ÇIKIŞ DOLUM-YAMASI KUYRUĞU (teşhis 2026-08-10): RESTART'I ATLATMALI (15. anahtar).
          # Kaybolursa kapanan işlemin gerçek ayna dolumu bir daha ARANMAZ — tek-atış kusuru
          # restart kılığında geri gelirdi. Yazanlar: `_mirror_exit_sync` (karar kapatmaları,
          # close_order_id ile) + `reconcile_broker_state` başı (bacak kapatmaları); tüketen:
          # `_exit_fill_yamasi` (her reconcile turu).
          EXIT_FILL_KEY: meta.get(EXIT_FILL_KEY, {})}
    # AYNI KİLİT: Hermes'in görüş damgası da portfolio.json'a yazıyor (ayrı iş parçacığı) —
    # ikisi de store.file_lock(PORTFOLIO) altında olmalı, yoksa biri diğerinin defterini ezer.
    # `update_json` kilidi ZATEN alır (yeniden girişli); dıştaki `with` okuma+kıyas+yazımın TEK
    # kritik bölge olmasını sağlar — kıyas ile yazım arasına başka bir yazar giremez.
    with store.file_lock(PORTFOLIO):
        red: dict = {}

        def _yama(doc):
            """Kitabın SAHİPLENİLEN alanlarını diskteki belgeye işler; yabancı anahtarlar yerinde kalır.

            BEYAN KAPISI: yazımdan sonraki beyan ölçüsü hem diskteki hem döngüdeki hâle göre
            gerilerse yazım REDDEDİLİR (False) ve neden `red` sözlüğüne bırakılır — sermaye beyanı
            sessizce kaybolamaz. Belge sözlük değilse de reddedilir; çağıran alarm basıp tam yazım
            yapar."""
            if not isinstance(doc, dict):
                # Diskteki belge sözlük değil (dış hasar). Korunacak yabancı anahtar YOKTUR;
                # yazımı atlamak kitabın o turunu kaybettirirdi → aşağıda alarm + tam yazım.
                red["neden"] = "belge_sozluk_degil"
                return False
            olculer = (("disk", BR.beyan_olcusu(doc)), ("dongu", BR.beyan_olcusu(meta)))
            doc.update(st)                    # SAHİPLENİLEN alanlar; yabancılar YERİNDE kalır
            yeni = BR.beyan_olcusu(doc)
            for kaynak, eski in olculer:
                g = BR.beyan_gerilemesi(eski, yeni)
                if g:
                    red.update({"kaynak": kaynak, **g})
                    return False
            return True

        store.update_json(PORTFOLIO, _yama, {})
        if red.get("neden") == "belge_sozluk_degil":
            obs.alarm(obs.ALARM_DATA_QUALITY,
                      "portfolio.json bir sözlük DEĞİL — kitap tam belge olarak yeniden yazıldı",
                      yazar="loop._save_broker", neden=red["neden"],
                      detail="yama uygulanamadı; korunacak yabancı anahtar yok, kitap kaybolmasın "
                             "diye tam yazım yapıldı (defterin önceki içeriği okunamıyordu)")
            store.write_json(PORTFOLIO, st)
        elif red:
            # YAZIM REDDEDİLDİ — ve bu SESSİZ DEĞİL: kitap bu tur diske inmez, alarm operatöre
            # kaybı AYNI DÖNGÜDE söyler. Kendi kendini iyileştirir: sonraki tur `meta`yı diskten
            # yeniden okur, taban düşer ve yazımlar sürer (kalıcı kilitlenme değil, tek tur fren).
            obs.alarm(obs.ALARM_DATA_QUALITY,
                      "sermaye beyanı silinecekti — kitap yazımı REDDEDİLDİ",
                      yazar="loop._save_broker", **red,
                      detail="beyan yalnız EKLENEBİLİR (grant_amnesty ailesi): meşru bir küçülme "
                             "YAZILI olmak zorundadır. Kitap bu tur yazılmadı; beyanı silen yazar "
                             "aranmalı (KOKNEDEN 2026-08-04).")
    # SICAK KOPYA — DEVRE DIŞI. Bu satır pozisyonları `mrd:pos`a
    # yazıyordu ("intraday'de ms-latency erişim"). ÖLÇÜM: `hotstate.get_positions`ın PRODÜKSİYONDA
    # hiçbir çağıranı yok — yalnız testler okuyor. Yani katman YALNIZ-YAZILIRDI: her turda Redis'e
    # gidiliyor, kimse okumuyordu. Tüketici bağlamak pano/api tarafını ister (bu turun dokunma
    # yasağında), o yüzden karar KANITA göre verildi: bedava sadelik, yazımı kapat.
    #   GERİ AÇMA TEK SATIR: aşağıdaki iki satırın yorumunu kaldır. `hotstate.cache_positions`
    #   SİLİNMEDİ ve testleri duruyor — 4b/pano tüketicisi geldiği gün kanca hazır.
    # from . import hotstate
    # hotstate.cache_positions(st["positions"])
    _hotstate_off_once("mrd:pos", "_save_broker", "get_positions")


def _llm_veto_filter(meta: dict) -> None:
    """LLM danışman katmanı: YALNIZ terfili ajan (analytics.llm_promoted — yazılı kalibrasyon kuralı),
    YALNIZ 'REVIEW + karşı' planı DOLUMDAN düşürebilir. GO'ya dokunamaz, NO_GO'yu açamaz, boyut/çıkış
    yetkisi yok. AYNA TUTARLILIK YASASI: plan Alpaca'ya gönderildiyse önce ORADA iptal doğrulanır;
    doğrulanamazsa plan düşürülMEZ — iki defterin ayrışması vetodan büyük risktir."""
    from . import analytics as _an_llm
    if not _an_llm.llm_promoted():
        return
    kept_armed = []
    for pl in meta.get("armed", []):
        veto = pl.get("gate_verdict") == "REVIEW" and pl.get("llm_opinion") == "karşı"
        if not veto:
            kept_armed.append(pl); continue
        if pl["id"] in set(meta.get("alpaca_submitted", [])):
            from .adapters import alpaca as _alp_v
            ok_cancel = False
            try:
                for o in _alp_v.orders(status="open", limit=100, nested=True):
                    if o.get("client_order_id") == pl["id"] and float(o.get("filled_qty") or 0) <= 0:
                        ok_cancel = bool(_alp_v.cancel_order(o.get("id")).get("ok"))
                        break
            except Exception:  # sessiz-yutma: ağ/sağlayıcı hatası bu yolun NORMAL hâli; çağıran boş sonuç üzerinden yedek kaynağa düşer ve kaynak seçimi ayrıca kaydedilir
                ok_cancel = False
            if not ok_cancel:
                kept_armed.append(pl)
                obs.warn("llm_veto_kept_mirror", ticker=pl.get("ticker"),
                         detail="ayna iptali doğrulanamadı — tutarlılık için dolum sürüyor")
                continue
        obs.log("llm_veto_strip", ticker=pl.get("ticker"), plan_id=pl.get("id"),
                detail="terfili ajan vetosu: REVIEW + karşı → dolum düşürüldü")
        # KİLİTLİ oku-değiştir-yaz: eskiden çıplak read+write idi ve AYNI
        # deftere Hermes'in görüş damgası (`store.update_jsonl`, kilitli) ile `merge_dated_jsonl`
        # de yazıyor. Kilit tek taraflıysa kilit yoktur: kaybeden yazar bütün araya girmiş
        # satırları eski kopyasıyla geri alırdı ve hiçbir yerde iz kalmazdı.
        def _veto_patch(rows, _pid=pl["id"]):
            """Plan defterindeki bu plana `llm_veto=True` damgasını basar; satır bulunduysa True.

            Kilitli oku-değiştir-yaz içinde koşar: aynı deftere yazan diğer yazarların satırları
            geri alınmaz."""
            hit = False
            for _pr in rows:
                if _pr.get("id") == _pid:
                    _pr["llm_veto"] = True
                    hit = True
            return hit

        store.update_jsonl("trade_plans.jsonl", _veto_patch)
    meta["armed"] = kept_armed


SCAN_DEBT_FILE = "scan_debt.json"
SCAN_DEBT_MAX_AGE_D = 7    # takvim günü; bu yaşta hâlâ bar yoksa borç olaylı düşer (ölü sembol şüphesi)
SCAN_DEBT_CAP = 300


def _scan_debt_add(ticker: str, dstr: str) -> None:
    """Güncellik denetiminde elenen (seans barı henüz yayınlanmamış) sembol borç defterine yazılır —
    bar gelince kaçan kesişim karşı-olgusala işlenir. Kayıp artık görünmez değil, ölçülü."""
    debts = store.read_json(SCAN_DEBT_FILE, [])
    if any(r["ticker"] == ticker and r["date"] == dstr for r in debts):
        return
    if len(debts) >= SCAN_DEBT_CAP:
        return
    debts.append({"ticker": ticker, "date": dstr})
    store.write_json(SCAN_DEBT_FILE, debts)


def _nabiz(asama: str, i: int | None = None, n: int | None = None) -> None:
    """İLERLEME NABZI — gerekçe `scheduler.py`nin İLERLEME NABZI bloğunda; biçim kararları
    `adapters/data.py:_nabiz` ile AYNI (geç import, hüküm zamanlayıcıda). İki kopya değil iki
    ÇAĞIRAN: hüküm veren tek fonksiyon `scheduler.nabiz`tır, buradaki yalnız onu güvenli çağırır."""
    try:
        from . import scheduler
        scheduler.nabiz(asama, i, n)
    except Exception:  # sessiz-yutma: nabız saf telemetridir — zamanlayıcı bu süreçte yüklü olmayabilir (replay/backtest/sprint) ve bir damga denemesi günlük döngüyü ASLA düşüremez
        pass


def _scan_debt_collect(per: dict, d, eff: dict) -> dict:
    """Barı SONRADAN gelen borçlar için kaçan seansı o günkü kuyruk + o günkü RS ile değerlendir.
    Dönüş: {seans: [(sinyal, ["geç_bar"]), ...]} — yalnız karşı-olgusal deftere gider (sıfır yetki)."""
    import datetime as _dt2
    debts = store.read_json(SCAN_DEBT_FILE, [])
    if not debts:
        return {}
    from . import indicators as ind2
    keep, out = [], {}
    rs_cache: dict = {}
    for row in debts:
        t, ds = row["ticker"], row["date"]
        df_t = per.get(t)
        target = pd.Timestamp(ds)
        if df_t is None:
            continue                                     # evrenden çıkmış — borç düşer
        if target not in df_t.index:
            age = (d.date() - _dt2.date.fromisoformat(ds)).days
            if age > SCAN_DEBT_MAX_AGE_D:
                obs.warn("scan_debt_expired", ticker=t, date=ds,
                         detail=f"{age} gündür bar yok — ölü sembol şüphesi, borç düşürüldü")
            else:
                keep.append(row)
            continue
        if ds not in rs_cache:                           # RS o GÜNÜN evren kesitiyle — bugünküyle değil
            rets = {t2: float(df2.loc[:target]["close"].iloc[-1]
                              / df2.loc[:target]["close"].iloc[-1 - strat.RS_LOOKBACK] - 1.0)
                    for t2, df2 in per.items()
                    if target in df2.index and len(df2.loc[:target]) > strat.RS_LOOKBACK + 1}
            rs_cache[ds] = ind2.rs_rating(rets)
        tail = df_t.loc[:target].reset_index().tail(340)
        for su, sig in strat.scan_all(tail, eff, rs_cache[ds].get(t, 50), ticker=t).items():
            if su in strat.ARMED_SETUPS:
                out.setdefault(ds, []).append((sig, ["geç_bar"]))
        obs.log("scan_debt_resolved", ticker=t, date=ds, found=len(out.get(ds, [])))
    store.write_json(SCAN_DEBT_FILE, keep)
    return out


def _near_miss_blockers(sig, eff: dict) -> list:
    """Gevşek gölge taramasında doğan ama SIKI eşiklerde ölen sinyal için ölüm nedenleri.
    vr/prox EntrySignal alanı değil — notes içinden okunur (best-effort; bulunamazsa "diğer")."""
    import re as _re
    out = []
    if sig.rs_rating < eff.get("entry.rs_rating_min", 70):
        out.append("rs")
    if sig.score < eff.get("entry.min_score", 60):
        out.append("skor")
    m = _re.search(r"vr=([\d.]+)", sig.notes or "")
    if m and float(m.group(1)) < eff.get("entry.min_volume_ratio", 1.5):
        out.append("hacim")
    m = _re.search(r"prox=([\d.-]+)%", sig.notes or "")
    if m and float(m.group(1)) > eff.get("entry.pivot_proximity_pct", 2.0):
        out.append("uzamış")
    return out or ["diğer"]


def _carry_armed_without_bar(armed: list, has_bar) -> tuple[list, list]:
    """P4 dolum ayrıştırıcısı — kök neden (canlıda 2026-07-15): dolum anında bar henüz
    YAYINLANMAMIŞSA plan sessizce buharlaşıyordu, hiçbir olay yazılmadan. Tek-seans yasası "bayat
    sinyalle girme" içindir; YAYINLANMAMIŞ seans görülmemiş seanstır. Bar'ı olan planlar dolum
    adayı; olmayanlar BİR seans taşınır (olaylı), ikinci seansta da bar yoksa olaylı düşer."""
    fillable, carried = [], []
    for plan in armed:
        t = plan.get("ticker")
        if has_bar(t):
            fillable.append(plan)
            continue
        c2 = int(plan.get("carried") or 0)
        if c2 < 1:
            plan["carried"] = c2 + 1
            carried.append(plan)
            obs.log("armed_no_bar_carried", ticker=t, plan_id=plan.get("id"),
                    detail="bar yayınlanmadı — plan bir seans taşındı")
        else:
            obs.warn("armed_expired_no_bar", ticker=t, plan_id=plan.get("id"),
                     detail="ikinci seansta da bar yok — plan düşürüldü (kayıtlı)")
    return fillable, carried


_RECONCILE_ATLANDI_LOGGED: set = set()


def _reconcile_gunu_atlandi(sinif: str, dstr: str) -> None:
    """B7b (teşhis 2026-08-10): `noop` / `waiting_for_universe` / `refused_regressive` dalları
    reconcile'a HİÇ varmadan döner — o gün dolumlar yalnız Kanal-1'de (mirror_orders, kitap-dışı)
    yaşar ve `broker_reconcile.json` ÖNCEKİ seanstan konuşur. Bu kadans BİLİNÇLİdir (EOD kitap
    turu); değişen şey sessizliğidir: gün sınıfı artık OLAYLANIR ki "mutabakat neden bayat?"
    sorusu defterden cevaplansın (skip-yazıcı `_skip` yalnız broker/paper dallarını kapsıyordu).

    Tekilleştirme `_hotstate_off_once` desenidir: gün+sınıf başına süreçte BİR olay — noop dalı her
    gün-içi poll'da vurur, her vuruşta yazmak defteri bilgi taşımayan satırlarla şişirirdi.
    Yalnız `alpaca_paper`da: ayna yokken 'reconcile atlandı' demek olmayan bir borcu olaylamaktır."""
    if config.BROKER != "alpaca_paper":
        return
    k = (dstr, sinif)
    if k in _RECONCILE_ATLANDI_LOGGED:
        return
    _RECONCILE_ATLANDI_LOGGED.add(k)
    obs.log("reconcile_atlandi", sinif=sinif, date=dstr,
            detail="günlük tur reconcile'a varmadan döndü — broker_reconcile.json önceki seanstan "
                   "konuşur; gün içi ayna dolumları o gün yalnız Kanal-1'de (mirror_orders) görünür "
                   "(B7b beyanı; kadans bilinçli, sessizliği değil)")


def daily_cycle(bars: dict, index: pd.DataFrame, on_date: str | None = None) -> dict:
    """Process the latest closed trading day. Returns a summary dict."""
    # goal/bounds lru_cache'i uzun ömürlü süreçte dosyayı DONDURUYORDU: operatörün goal.yaml'da
    # elle değiştirdiği limit, sunucu yeniden başlatılana dek hiç görülmezdi.
    config.reload_config()
    goal = config.goal()
    limits = goal["limits"]
    strat_cfg = config.load_strategy()           # hot-reloaded each cycle
    params = strat_cfg["params"]
    version = int(strat_cfg.get("version", 1))
    skills.reconcile_enablement()                # pick up any key added/removed since the last cycle

    idx = index.set_index("date").sort_index()
    per = {t: df.set_index("date").sort_index() for t, df in bars.items()}
    all_dates = list(idx.index)
    if on_date:
        all_dates = [d for d in all_dates if str(d.date()) <= on_date]
    if not all_dates:
        return {"error": "no dates"}
    d = all_dates[-1]
    # ---- EVREN BÜTÜNLÜĞÜ KAPISI (canlı kanıtla bulundu) ----
    # Seans tarihini ENDEKSİN son barı belirliyordu. Ama ücretsiz kaynaklar sembol bazında farklı
    # hızda güncelleniyor: canlıda SPY 07-21 barına sahipken 250 sembolün yalnız 46'sı sahipti.
    # Tazelik koruması kalan 204'ü "bayat kuyruk" diye ATLIYOR — yani motor evrenin %18'ini tarayıp
    # "aday: 0" yazıyordu (son 5 seansın beşinde de öyle oldu). Üstelik o %18 rastgele değil,
    # HANGİ KAYNAĞIN önce güncellediğine bağlı: kapı 250 sembollük evrende ölçüyor, canlı taraf
    # yanlı bir alt kümede karar veriyor — kapı≠canlı ayrışmasının en kötü biçimi.
    # Çözüm: evrenin ÇOĞUNLUĞUNUN barı olan EN SON seansı işle. Gecikmeli ücretsiz veriyle bir gün
    # geride olmak dürüsttür; %18'lik yanlı bir kesitte karar vermek değildir.
    _n_uni, _deferred_for_coverage = max(1, len(per)), False
    for _cand in reversed(all_dates[-UNIVERSE_LAG_MAX_D:] or [d]):
        _cov = sum(1 for _df in per.values() if _cand in _df.index)
        if _cov / _n_uni >= UNIVERSE_MIN_COVERAGE:
            if _cand != d:
                _deferred_for_coverage = True
                obs.log("session_deferred_for_coverage", index_session=str(d.date()),
                        chosen=str(_cand.date()), coverage=round(_cov / _n_uni, 3),
                        detail="endeksin son barı evrenin çoğunda yok — kararlar tam evrende alınır")
            d = _cand
            break
    else:
        _cov0 = sum(1 for _df in per.values() if all_dates[-1] in _df.index)
        obs.warn("universe_coverage_low", date=str(all_dates[-1].date()),
                 coverage=round(_cov0 / _n_uni, 3), min_required=UNIVERSE_MIN_COVERAGE,
                 detail="hiçbir yakın seansta evren kapsaması yeterli değil — endeksin seansıyla devam")
    dstr = str(d.date())

    # KAPSAMA ERTELEMESİ ile MONOTONLUK BEKÇİSİ çarpışması: kitap, düzeltme öncesi
    # %18 kapsamalı bir seansta ilerletilmiş olabilir. O zaman tam-kapsamalı seans kitabın GERİSİNDE
    # kalır ve bekçi haklı olarak reddeder — ama sebep "bayat/yedek kaynak" DEĞİL, "evren henüz
    # yetişmedi"dir. İkisini aynı alarmla anlatmak teşhisi bozar: bu bir BEKLEME, bir arıza değil.
    _book_at0 = store.read_json("portfolio.json", {}).get("last_date")
    if _deferred_for_coverage and _book_at0 and dstr < str(_book_at0):
        obs.log("waiting_for_universe", chosen=dstr, book_at=str(_book_at0),
                index_session=str(all_dates[-1].date()),
                detail="tam kapsamalı seans kitabın gerisinde — barlar yetişince o seans işlenecek")
        _reconcile_gunu_atlandi("waiting_for_universe", dstr)     # B7b: atlanan mutabakat OLAYLI
        return {"status": "waiting_for_universe", "date": dstr, "book_at": str(_book_at0),
                "index_session": str(all_dates[-1].date())}

    # ---- monotonluk bekçisi: kitap asla GERİYE işlemez (GS'yi öldüren halka, 2026-07-15 10:29) ----
    # Bayat yedek kaynak endeksi geriletmişti; döngü sorgulamadan 07-13'ü işleyip kitabı geri sardı ve
    # silahlı planı geçmiş bir seansta yaktı. İşlenecek seans kitabın son tarihinden ESKİYSE reddet
    # (eşit güne izin var: re-seed sonu + elle buton aynı günü yineleyebilir — mevcut davranış).
    _book_at = store.read_json("portfolio.json", {}).get("last_date")
    if _book_at and dstr < str(_book_at):
        obs.warn("regressive_session_refused", date=dstr, book_at=str(_book_at),
                 detail="endeks kitabın gerisinde — bayat/yedek kaynak şüphesi; kitap geri sarılmaz")
        _reconcile_gunu_atlandi("refused_regressive", dstr)      # B7b: atlanan mutabakat OLAYLI
        return {"status": "refused_regressive", "date": dstr, "book_at": str(_book_at)}

    # ---- data-quality gate: bad bars must never drive trades (Hard Rule 7) ----
    idx_ok, idx_issues = data_adapter.validate_bars(idx.loc[:d].reset_index(), "SPY")
    tick_bad = []
    for t, dfp in per.items():
        ok, iss = data_adapter.validate_bars(dfp.loc[:d].reset_index(), t)
        if not ok:
            tick_bad.append(t)
    data_bad = (not idx_ok) or (len(tick_bad) > len(per) * 0.25)
    # bağımsız kaynak AYNI seans kapanışında >%1.5 sapma raporladıysa bar güvenilmez —
    # gecikme/kaynak-yok durumları ('source_lagging', 'fetch_failed') ASLA halt sebebi değildir.
    _xc = store.read_json("index_crosscheck.json", {})
    xc_bad = (_xc.get("date") == dstr and _xc.get("status") == "diverged")
    if xc_bad:
        data_bad = True
        obs.alarm(obs.ALARM_DATA_QUALITY, f"endeks çapraz-doğrulama sapması: {_xc.get('divergence')}",
                  date=dstr, primary=_xc.get("primary_close"), cboe=_xc.get("cboe_close"))
    store.write_json("data_quality.json", {"date": dstr, "index_ok": idx_ok,
                     "index_issues": idx_issues, "tickers_failed": tick_bad,
                     "universe": len(per), "crosscheck": _xc.get("status"),
                     "data_halt": data_bad})
    if data_bad:
        obs.alarm(obs.ALARM_DATA_QUALITY, f"veri kalitesi kapısı: index_ok={idx_ok}, {len(tick_bad)} hisse başarısız",
                  date=dstr, index_ok=idx_ok, tickers_failed=tick_bad[:10])

    b, meta = _load_broker()
    if meta.get("last_date") == dstr:
        # already processed this bar; just refresh heartbeat.
        # REJİM DE TAZELENİR (sahiplik dedektörü yakaladı): bu kısa yol rejimi ve
        # bütçeyi damgalamıyordu. Nabız çok yazarlı olduğu için alanlar bir kez düştüğünde HUD
        # "rejim yok / bütçe yok" gösteriyor ve bir daha kendiliğinden dolmuyordu — seans zaten
        # işlenmişse rejim BİLİNMİYOR değildir, diskte durur.
        _rg = store.read_json("regime.json", {}) or {}
        health.write_heartbeat(version=version, open_positions=len(b.positions),
                               equity=round(b.equity(_marks(per, d)), 2), last_bar=dstr,
                               regime=_rg.get("regime"),
                               exposure_budget_pct=_rg.get("exposure_budget_pct"),
                               note="bar already processed")
        _reconcile_gunu_atlandi("noop", dstr)                    # B7b: atlanan mutabakat OLAYLI
        return {"status": "noop", "date": dstr}

    marks = _marks(per, d)
    # OPEN-phase risk decisions (breaker, de-risk, sizing) mark at D's OPEN — the close isn't known at
    # the open (close-marks here let the morning decisions see the afternoon's move).
    marks_open = {t: per[t].loc[d, "open"] for t in b.positions if t in per and d in per[t].index}
    day_start_equity = meta.get("day_start_equity", b.equity(marks_open))

    # ---- 1. OPEN(D): pending exits + armed entries from the prior cycle ----
    for t, reason in list(meta.get("pending_exits", {}).items()):
        if t in b.positions and t in per and d in per[t].index:
            # ÇIKIŞ KUYRUĞU: plan kimliği pozisyon kapanMADAN önce okunur — kapandıktan sonra `b.positions`ta
            # yoktur ve aynadaki bracket'ı hangi emre bağlayacağımızı söyleyen TEK anahtar odur.
            _pid = getattr(b.positions[t], "plan_id", None)
            b.close_position(t, per[t].loc[d, "open"], reason, dstr)
            _persist_trade(b.closed[-1])
            _mirror_exit_enqueue(meta, t, _pid, reason, dstr)
    meta["pending_exits"] = {}
    _mirror_exit_sync(meta, dstr)     # kuyruk + önceki turlardan kalan yeniden denemeler

    halted = health.halted()
    day_pnl_pct = (b.equity(marks_open) - day_start_equity) / day_start_equity if day_start_equity else 0.0
    breaker = health.circuit_breaker_tripped(day_pnl_pct, goal)
    if breaker:
        obs.alarm(obs.ALARM_CIRCUIT_BREAKER, f"günlük kayıp devre kesici: {day_pnl_pct:.2%}",
                  date=dstr, day_pnl_pct=round(day_pnl_pct, 4), limit_pct=goal["limits"]["max_daily_loss_pct"])
        try:
            from . import notify
            notify.breaker(day_pnl_pct)
        except Exception:  # sessiz-yutma: obs alarmı/kaydı bu noktada ZATEN yazıldı; ikincil bildirim kanalının (Telegram/webhook) düşmesi alarmı asla düşüremez
            pass
    eq_now = b.equity(marks_open)
    meta["peak_equity"] = max(meta.get("peak_equity", START_EQUITY), eq_now)
    size_mult = derisk_mult(eq_now, meta["peak_equity"])   # graded de-risk on running drawdown
    eff_max_open = max_positions_at(eq_now, meta["peak_equity"], limits["max_open_positions"])  # + throttle
    with skills.pipeline_run("P4_EXECUTE", artifact="state/trades.jsonl"):   # executions must be auditable
        try:
            _llm_veto_filter(meta)   # yalnız TERFİLİ ajanın dar vetosu (fonksiyona bak)
        except Exception as e:
            obs.warn("llm_veto_layer_failed", error=f"{type(e).__name__}: {e}")
        carried = []
        # kapı hangi sebeple kapandı? Sıra ÖNEMLİ — birden çok koşul aynı anda tutabilir ve
        # damga TEK olmalı; en sert/en dıştaki sebep kazanır (HALT > breaker > veri > kısma).
        _kapi = ("halt" if halted else "breaker" if breaker else "data_bad" if data_bad
                 else "throttle" if size_mult <= 0 else None)
        _dusen: list = []
        # İŞ-2-EOD KEMERİ, TOPLAMA YARISI (P-2026-08-07-VLO): iç motorun BU turda
        # doldurduğu ama aynaya HİÇ gönderilmemiş planlar (onay-anı gönderimi düşmüş/ulaşamamış,
        # unreachable-kalmış ya da düzeltme-öncesi silahlanmış her plan). Küme dolum ANINDA ölçülür
        # — dolumdan sonra plan silahlı kümeden çıkar ve P3-sonu `mirror_submit_armed` onu göremez.
        _gonderilmis0 = set(meta.get("alpaca_submitted") or [])
        _ic_dolan_gonderilmemis: list = []
        if _kapi is None:
            fillable, carried = _carry_armed_without_bar(
                meta.get("armed", []), lambda t: t in per and d in per[t].index)
            _law_tbl = meta.get("entry_law") or {}
            for plan in fillable:
                t = plan["ticker"]
                if len(b.positions) < eff_max_open and t not in b.positions:
                    # E1: İCRA GİRDİLERİ PLANDAN DEĞİL YAN TABLODAN. `entry_law` sözlüğü silahlanma
                    # anında (sinyal barı kapanışı) yazılır — as-of ihlali yok, plan DEFTERİ şeması
                    # da iki motorda aynı kalır (pivot ile aynı desen, bkz. broker.fill_entry).
                    _lw = _law_tbl.get(plan.get("id")) or {}
                    _open = float(per[t].loc[d, "open"])
                    _rej: dict = {}
                    _pos = b.fill_entry(plan, _open, dstr, eq_now, size_mult=size_mult,
                                        adv=_adv(per[t], d), atr=_lw.get("atr"),
                                        pivot=float(_lw.get("pivot") or 0.0),   # yapı çizgisi
                                        gap_at_submit=_lw.get("gap_at_submit"), reject_out=_rej)
                    _base = {"date": dstr, "plan_id": plan.get("id"), "ticker": t, "motor": "ic",
                             "entry_trigger": plan.get("entry_trigger"), "limit": _lw.get("limit"),
                             "atr": _lw.get("atr"), "law": _lw.get("law"),
                             "gap_at_submit": _lw.get("gap_at_submit"),
                             "resmi_acilis": round(_open, 4)}
                    if _pos is not None:
                        # İÇ-MOTOR TOTOLOJİSİ: `_pos.entry` açılıştan SABİT slippage ile
                        # türetilir (broker.fill_entry), yani resmî açılışa göre bps ölçmek
                        # slippage_bps sabitini geri üretir — bir ÖLÇÜM değil totoloji. None + beyan
                        # (bkz. IC_ACILIS_TOTOLOJI_BEYAN). `fill_vs_limit_bps` AYRIDIR (dolum limit
                        # TAVANINA göre; E1 grid tam onu ölçer) ve KALIR.
                        _entry_exec_write({**_base, "karar": "fill", "fill": round(_pos.entry, 4),
                                           "qty": _pos.qty,
                                           "fill_vs_resmi_acilis_bps": None,
                                           "fill_vs_resmi_acilis_beyan": IC_ACILIS_TOTOLOJI_BEYAN,
                                           "fill_vs_limit_bps": _bps(_pos.entry, _lw.get("limit"))})
                        # DOLUM-ANI DAMGASI (teşhis 2026-08-10): boyut makbuzunun İKİNCİ YARISI — DOLUM anının
                        # boyut tabanı makbuza damgalanır. Sapma sınıflandırıcısı yaşlı pozisyonda
                        # "dolum tabanı" diye BUGÜNÜN eq'sini kıyaslayıp sebep UYDURUYORDU; damga
                        # varsa kıyas dolum gününün GERÇEK tabanıyla yapılır, yoksa `olculemedi`.
                        # Yalnız MEVCUT makbuza yazılır: makbuzsuz plana yarım makbuz üretmek,
                        # gönderim-bacağı ölçülmemişken kıyas varmış gibi görünmek olurdu.
                        _rcpt6 = (meta.get("size_law") or {}).get(plan.get("id"))
                        if _rcpt6 is not None and _rcpt6.get("dolum_eq") is None:
                            _rcpt6["dolum_eq"] = round(float(eq_now), 2)
                            _rcpt6["dolum_peak"] = round(float(meta.get("peak_equity", START_EQUITY)), 2)
                        # İŞ-2-EOD kemeri: iç dolum VAR, ayna gönderim izi YOK → geç-gönderim
                        # adayı (aşağıda, bayat-tetik süpürmesinden SONRA gönderilir).
                        if plan.get("id") and plan["id"] not in _gonderilmis0:
                            _ic_dolan_gonderilmemis.append(plan)
                    else:
                        _reason = _rej.get("reason") or "bilinmiyor"
                        _entry_exec_write({**_base, "karar": _reason, "fill": None,
                                           "fill_vs_resmi_acilis_bps": None,
                                           "fill_vs_limit_bps": None,
                                           "red_detay": {k: v for k, v in _rej.items()
                                                         if k not in ("reason", "ticker", "plan_id")}})
                        # KAÇAN İŞLEM ÖLÇÜLÜR, YUTULMAZ. Karşı-olgusal defter bu planın kaydını
                        # P3'te ZATEN açtı (counterfactual.collect her planı açar) — yani "girseydik
                        # ne olurdu?" sorusunun cevabı aynı `plan_id` ile orada birikiyor. Buradaki
                        # olay o kaydın İCRA sebebini adlandırır; ikisi plan_id ile birleşir.
                        if _reason in (BR.EV_MISSED_LIMIT, BR.EV_GAP_VETO):
                            obs.warn(_reason, ticker=t, plan_id=plan.get("id"),
                                     entry_trigger=plan.get("entry_trigger"),
                                     limit=_lw.get("limit"), open=round(_open, 4),
                                     asim_bps=_rej.get("asim_bps"),
                                     detail="E1 giriş yasası: dolum yazılmadı — cf defteri aynı "
                                            "plan_id ile kaçan işlemin sonucunu ölçmeye devam eder")
                else:
                    # PLAN-BAŞI SESSİZLİK: bu dalın else'i YOKTU — slot dolduğu ya da sembol
                    # zaten defterde olduğu için düşen plan hiçbir iz bırakmadan yok oluyordu.
                    # KARAR AYNI (plan düşer), yalnız SEBEBİ artık okunabilir.
                    _armed_drop_row(plan, dstr,
                                    "slot_full" if len(b.positions) >= eff_max_open else "already_open",
                                    open_positions=len(b.positions), eff_max_open=eff_max_open)
                    _dusen.append(plan)
            if _dusen:
                _stamp_plan_status(_dusen)
        else:
            _armed_dropped_by_gate(meta, dstr, _kapi)
        meta["armed"] = carried
        # BAYAT TETİK KADANSI. Buranın SEBEBİ: (1) yukarıdaki blok bu seansın dolum
        # kararlarını VERDİ (dolan doldu, dolmayan `entry_missed_limit`/kapı damgasıyla düştü),
        # yani hâlâ dolmamış duran her motor giriş emri artık bayattır; (2) yeni planların
        # üretimi/silahlanması ve `mirror_submit_armed` HENÜZ koşmadı (P3, aşağıda) — bu akşam
        # gönderilecek TAZE emirler bu iptalden etkilenmez; (3) `carried` (barı yayınlanmamış plan)
        # dahil, DÜN silahlanıp bugün de dolmamış GTC girişleri bu çağrı kapsar. TIF=day iken bu
        # temizliği broker yapıyordu (ve yaparken korumayı da kesiyordu) — motorun kendi işi oldu.
        # `carried` İÇİN DAVRANIŞ DEĞİŞMEDİ: iptal edilen emri `reconcile_broker_state` (1.2)
        # DEAD görüp planı silahlı kümeden düşürür — TIF=day'de emir aynı akşam `expired` olduğu
        # için o düşürme ZATEN oluyordu. Yani bu satır taşıma mekanizmasını bozmuyor, onun
        # bugünkü fiilî sonucunu aynen sürdürüyor.
        _cancel_stale_entry_orders(dstr)
        # ==========================================================================================
        # İŞ-2-EOD KEMERİ, GÖNDERİM YARISI (2026-08-11 — P-2026-08-07-VLO sınıf kapanışı):
        # "İÇ MOTORUN DOLDURDUĞU HİÇBİR PLAN AYNAYA GÖNDERİLMEMİŞ KALAMAZ." Onay-anı gönderimi
        # (operator_onay_ver) normal yoldur ve bu kemer o yol çalıştığında dedup'la NO-OP olur;
        # burası onay-anı gönderiminin düştüğü / ulaşamadığı / hiç yaşanmadığı (düzeltme-öncesi
        # silahlanma, unreachable-kalan akşam gönderimi) vakaların yakalayıcısıdır.
        # YER BİLİNÇLİ: bayat-tetik süpürmesinden SONRA — süpürmeden önce gönderilseydi taze emir
        # aynı turda "bayat" diye kesilirdi (P3-sonu gönderimiyle aynı sıra yasası). Emir bu akşam
        # çıkar, bir SONRAKİ seans dolabilir; dolmadan kalırsa ertesi süpürme onu meşru keser
        # (tek-seans taşıma yasasının aynısı). Geç kalmış bir gönderim, hiç yapılmamış bir
        # gönderimden dürüsttür — ve olay defterine ADIYLA düşer.
        # GÖRÜNÜM-META: armed'a DOKUNULMAZ (plan iç kitapta ZATEN dolu — silahlı kümeye geri koymak
        # ertesi açılışta İKİNCİ iç dolum demekti); dedup/entry_law/makbuz döngünün kendi meta'sından.
        # ==========================================================================================
        if _ic_dolan_gonderilmemis and config.BROKER == "alpaca_paper":
            _gec_view = {"armed": list(_ic_dolan_gonderilmemis),
                         "alpaca_submitted": list(meta.get("alpaca_submitted") or []),
                         "entry_law": meta.get("entry_law") or {},
                         "peak_equity": meta.get("peak_equity", START_EQUITY),
                         "size_law": meta.setdefault("size_law", {})}
            try:
                _gec = mirror_submit_armed(_gec_view, dstr, eq_now=eq_now, halted=halted,
                                           source="loop_gec_gonderim")
                meta["alpaca_submitted"] = list(_gec_view.get("alpaca_submitted")
                                                or meta.get("alpaca_submitted") or [])
                if _gec_view.get("broker_rejected"):
                    meta["broker_rejected"] = (meta.get("broker_rejected", [])
                                               + list(_gec_view["broker_rejected"]))[-50:]
                obs.warn("mirror_gec_gonderim", date=dstr, n=len(_ic_dolan_gonderilmemis),
                         submitted=_gec.get("submitted", 0),
                         plan_ids=[p.get("id") for p in _ic_dolan_gonderilmemis][:10],
                         detail="iç motor dolum yazdı ama aynaya gönderim izi yoktu — tek kapıdan "
                                "GEÇ gönderildi (onay-anı yolunun yakalayıcı kemeri); emir bir "
                                "sonraki seansta dolabilir, dolmazsa ertesi süpürmede kesilir")
            except Exception as e:
                # YASA 4: kemerin arızası günlük turu düşüremez ama sessiz de kalamaz — gönderilmemiş
                # onaylı dolumun son bekçisi İŞ-3b alarmıdır (ONAYLI_PLAN_GONDERILMEDI).
                obs.warn("mirror_gec_gonderim_dustu", error=f"{type(e).__name__}: {e}", date=dstr,
                         n=len(_ic_dolan_gonderilmemis),
                         detail="geç-gönderim kemeri istisnayla düştü — aynasız iç dolumları "
                                "reconcile split_brain + ONAYLI_PLAN_GONDERILMEDI bekçisi yakalar")

    # GÜNLÜK KESİCİ PENCERESİ İKİ MOTORDA AYNI. Bu yazım seansın SONUNDA
    # ve KAPANIŞ markıyla yapılıyordu (`b.equity(_marks(per, d))`); okuma tarafı ise D+1'in AÇILIŞ
    # markıyla (`marks_open`). Sonuç: canlı kesicinin penceresi
    # KAPANIŞ(D)→AÇILIŞ(D+1), yani YALNIZ GECELİK BOŞLUK — portföy düzeyinde −%3'lük bir gecelik
    # boşluk pratikte oluşmadığı için `max_daily_loss_pct: 3.0` canlıda fiilen ATILDI. Replay
    # (backtest.py `day_start_equity = broker.equity(marks_open_on(d))`, dolumlardan SONRA) ve
    # gölge-v2 (shadow_lifecycle.py `bk["day_start_equity"] = b.equity(_marks_open())`) ise
    # AÇILIŞ(D)→AÇILIŞ(D+1) penceresini, yani D'nin TÜM seansını ölçüyordu. Kanonik semantik
    # REPLAY'inkidir (2026-07-18 denetiminin yarım kalmış düzeltmesi: okuma tarafı açılışa
    # çevrilmiş, YAZMA tarafı kapanışta unutulmuş) ve canlı taraf ona EŞİTLENDİ.
    # FAZ SIRASI DA BİREBİR: backtest.py bu satırı dolumlardan SONRA, gün-içi çıkışlardan ÖNCE
    # yazar — bu blok da tam orada. Markı hesaplayan sözlük YENİDEN kurulur: `marks_open` fill'den
    # ÖNCE hesaplandığı için bu turda dolan pozisyonları içermez ve onları işaretsiz bırakmak
    # gün-başı sermayesini eksik ölçerdi.
    meta["day_start_equity"] = b.equity({t: float(per[t].loc[d, "open"]) for t in b.positions
                                         if t in per and d in per[t].index})

    # ---- 2. INTRADAY(D): touch exits ----
    # regime-resolved params for intraday consumers: at this point P1 hasn't recomputed yet, so the
    # regime known intraday is the PREVIOUS session's (regime.json on disk) — same semantics as the
    # backtest's prev_eff. Flat `params` here silently ignored exit.scale_out_*@regime overrides.
    prev_regime = store.read_json("regime.json", {}).get("regime", "any")
    eff_intraday = config.resolve_params(params, strat_cfg.get("params_by_regime"), prev_regime)
    for t in list(b.positions.keys()):
        if t in per and d in per[t].index:
            bar = per[t].loc[d]
            _pos = b.positions[t]                       # MFE/MAE su işaretleri her seans güncellenir
            _pos.hi_water = max(_pos.hi_water, float(bar["high"]))
            _pos.lo_water = min(_pos.lo_water or float(bar["low"]), float(bar["low"]))
            b.scale_out(b.positions[t], {"high": bar["high"], "low": bar["low"], "open": bar["open"]},
                        eff_intraday)   # bank partial before full exit (stop-first conservatism inside)
            ex = b._touch_exit(b.positions[t], {"open": bar["open"], "high": bar["high"], "low": bar["low"]})
            if ex:
                b.close_position(t, ex[0], ex[1], dstr); _persist_trade(b.closed[-1])
            else:
                b.positions[t].bars_held += 1

    try:                                   # karşı-olgusal defter ilerler — dönüş görmezden gelinir,
        from . import counterfactual, watchdog as _wd   # hiçbir karar bu deftere bakmaz (sıfır yetki)
        counterfactual.advance(per, d, dstr)
        _wd.beat("cf_advance")
    except Exception as e:
        obs.warn("cf_advance_failed", error=f"{type(e).__name__}: {e}")

    # ---- 3. CLOSE(D): P1 regime, manage trails, P2 screen, P3 plan+guard, arm ----
    with skills.pipeline_run("P1_REGIME", artifact="state/regime.json"):
        rj = regime_mod.build_regime_json(idx.loc[:d].reset_index(), params, dstr)
        srets = {t: float(dfp.loc[:d]["close"].iloc[-1] / dfp.loc[:d]["close"].iloc[-22] - 1.0)
                 for t, dfp in per.items() if len(dfp.loc[:d]) > 22}
        rj["leading_sectors"] = regime_mod.sector_momentum(srets, SECTORS)
        store.write_json("regime.json", rj)
    regime_ok = rj["regime"] in ("trend_up", "chop") and rj["exposure_budget_pct"] > 0
    eff = config.resolve_params(params, strat_cfg.get("params_by_regime"), rj["regime"])  # regime-conditional

    for t in list(b.positions.keys()):
        if t in per and d in per[t].index:
            pos = b.positions[t]
            df_t = per[t].loc[:d].reset_index()
            pos_regime_ok = (rj["regime"] in ("trend_up", "chop")) if getattr(pos, "exploration", False) else regime_ok
            dec = strat.manage_position(df_t, {"entry": pos.entry, "stop": pos.stop,
                    "trail_stop": pos.trail_stop, "r_per_share": pos.r_per_share,
                    # SÖZLÜĞÜN İKİNCİ KOPUKLUĞU. Pivot fill_entry'e geçse bile bu sözlükte
                    # yoksa `early_kill_pivot_exit` yine None okuyup False dönerdi — iki kopukluk
                    # bağımsızdı, ikisi de kapanmadan knob canlıda ateşleyemez. Replay
                    # (backtest.py) ve gölge-v2 (shadow_lifecycle.py) bu alanı zaten taşıyordu.
                    "pivot": pos.pivot},
                    eff, pos.bars_held, pos_regime_ok)
            pos.trail_stop = dec.trail_stop
            if dec.exit_now:
                meta["pending_exits"][t] = dec.exit_reason

    candidates, plans, dormant_sigs, explore_pool = [], [], [], []
    near_miss_sigs = []
    # NEAR-MISS GÖLGE BACAĞI GÖRÜNÜRLÜĞÜ (2026-08-12 — 2026-07-30→08-12 iki haftalık sessiz ölüm
    # dersi, YASA 4+6): bacak koşmadıysa özet olaya 0 değil None yazılır ("ölçüldü, sıfır" ile
    # "hiç ölçülmedi" ayrı olgulardır — UYDURMA YASAĞI) ve nedeni ayrı olayla deftere düşer.
    _p2_kostu = False        # P2 taraması (near-miss gölge bacağı dahil) bu turda gerçekten koştu mu?
    _nm_toplama = None       # cf.collect'in near-miss muhasebesi (ana çağrıdan kopya; None = collect konuşmadı)
    late_by_date = {}        # geç-bar borç kesişimleri — blok koşmadığı turda da özet olay okur (NameError koruması)
    # P3 BLOĞUNUN DIŞINDA TANIMLANIR, İÇİNDE DEĞİL: blok `halted`/`data_bad`/slot koşuluna bağlıdır
    # ve koşmadığı turda sayaç TANIMSIZ kalırdı — `daily_cycle` olayı o turda NameError'la düşerdi.
    _kapsam_disi = 0         # bu turda karartma kapısının KONUŞAMADIĞI plan sayısı (beyanlı fail-open)
    _takvim_dusen = 0        # …ve takvim güvenilmezliği yüzünden GO→REVIEW düşen plan sayısı
    # TAKVİM GÜVENİLMEZLİĞİ — TUR BAŞINA BİR KEZ ÖLÇÜLÜR. Aday başına
    # çağırmak `_load()`u aday sayısı kadar `stat()`latırdı; hüküm zaten TÜM sembolleri aynı anda
    # bağladığı için tur başına tek ölçüm hem doğru hem ucuzdur. Sabit yerde tanımlanır (`_kapsam_disi`
    # ile aynı gerekçe): P3 bloğu koşmadığı turda da `daily_cycle` olayı bu değeri okur.
    _takvim_kusuru = None
    try:
        _takvim_kusuru = earnings.calendar_untrustworthy()
    except Exception as e:
        # YASA 4: yüklemin kendisi düşerse SESSİZCE "takvim sağlam" demek, kapatmak için yazdığımız
        # kapıyı kendi hatamızla yeniden açmak olurdu. Davranış fail-open'a döner (bilinen, ölçülmüş
        # eski hâl) ama arıza ADIYLA görünür.
        obs.warn("earnings_calendar_health_check_failed", error=f"{type(e).__name__}: {e}",
                 detail="takvim güvenilmezlik yüklemi koşamadı — karartma kapısı bu turda ESKİ "
                        "davranışta (sembol-bazlı fail-open); GO→REVIEW düşürmesi UYGULANMADI")
    if _takvim_kusuru:
        # YASA 4 GEREKÇELİ OLAY: bu satır olmadan "bugün neden hiç GO yok?" sorusunun cevabı
        # hiçbir defterde durmazdı. Tur başına BİR kez; plan başına tekrarlamak asıl sinyali gömerdi.
        obs.warn("earnings_calendar_untrustworthy", date=dstr, **{k: v for k, v in _takvim_kusuru.items()
                                                                  if k != "sebep"},
                 sebep=_takvim_kusuru.get("sebep"),
                 detail="karartma kapısı BU TURDA hiçbir sembolde konuşamıyor (takvim ufku karartma "
                        "penceresini taşımıyor ya da son pencere kısmi geldi) — TÜM planlar karartma "
                        "varsayılanına düştü: GO→REVIEW. NO_GO'lar değişmedi; kapının körlüğü bir "
                        "sembolün suçu değildir, o yüzden red değil İNCELEME.")
    explore_mode = (not halted and not data_bad and rj["exposure_budget_pct"] <= 0)
    if not halted and not data_bad and (rj["exposure_budget_pct"] > 0 or explore_mode) \
            and len(b.positions) < limits["max_open_positions"]:
        _p2_kostu = True
        with skills.pipeline_run("P2_SCREEN", artifact="state/candidates.jsonl"):
            # Faz 0 KARANTİNA: validate_bars'ın 'hard' düşürdüğü ticker'lar bugüne dek yalnız
            # LİSTELENİYORDU (%25 eşiği aşılmadıkça) — bozuk barlı tek hisse aday üretebiliyordu.
            # Artık taramadan ve RS havuzundan dışlanır; mevcut pozisyon yönetimi etkilenmez.
            _quarantine = set(tick_bad)
            rets = {}
            for t, df_t in per.items():
                if t in _quarantine or d not in df_t.index:
                    continue
                sub = df_t.loc[:d]
                if len(sub) > strat.RS_LOOKBACK + 1:
                    rets[t] = float(sub["close"].iloc[-1] / sub["close"].iloc[-1 - strat.RS_LOOKBACK] - 1.0)
            rs_map = ind.rs_rating(rets)
            # Huni ölçümü: aday kuraklığında ölümlerin ezici kısmının
            # kırılım-SONRASI eşiklerde (hacim×1.5, RS 70) olduğunu gösterdi. Gevşek bir GÖLGE taraması
            # eşiğin hemen altında ölenleri karşı-olgusal deftere yazar ki "hangi eşik masada para
            # bırakıyor?" ÖLÇÜLSÜN. Sıfır yetki: karar/kapı bu satırları asla okumaz; eşik değişikliği
            # ancak kanıt biriktikten sonra OOS kapısından geçerek gelebilir.
            _rx = strat.relax_for_near_miss(eff)             # TEK KAYNAK (strategy.py) — cf_backfill ile aynı
            late_by_date = _scan_debt_collect(per, d, eff)   # barı sonradan gelenlerin kaçan kesişimleri
            for _i_p, (t, df_t) in enumerate(per.items(), 1):
                # NABIZ: evren boyu tarama — sembol başına İKİ `scan_all` (sıkı + gevşek) ve
                # her biri gösterge penceresi hesaplar. Ağ yok ama CPU var; uzun bir yetişme turunda
                # bu blok tek başına bekçi eşiğini yiyebilir.
                _nabiz("tarama", _i_p, len(per))
                if t in b.positions or t in _quarantine:
                    continue
                if d not in df_t.index:                      # güncellik: bu seansın barı henüz yok →
                    _cut = df_t.loc[:d]                      # bayat kuyrukla taranMAZ (kök-neden sınıfı
                    if len(_cut) and (d.date() - _cut.index[-1].date()).days <= SCAN_DEBT_MAX_AGE_D:
                        _scan_debt_add(t, dstr)              # taze gecikme → borç; kadim kuyruk → sessiz geç
                    continue
                _tail = _scan_tail(df_t, d)
                _all = strat.scan_all(_tail, eff, rs_map.get(t, 50), ticker=t)
                for _su, _s3 in strat.scan_all(_tail, _rx, rs_map.get(t, 50), ticker=t).items():
                    if _su in strat.ARMED_SETUPS and _su not in _all:
                        near_miss_sigs.append((_s3, _near_miss_blockers(_s3, eff)))
                for _s2 in _all.values():              # uyuyan kurulum ateşlemeleri karşı-olgusala
                    if _s2.setup not in strat.ARMED_SETUPS:
                        dormant_sigs.append(_s2)
                        # operatör öğrenme-modu: uyuyan kurulumun ateşlemesi ADAY da olur —
                        # kapıdan geçer, ama YALNIZ keşif sondası olarak (0.25R) silahlanabilir. Gerçek-R
                        # kanıtı yalnız cf simülasyonundan değil küçük gerçek işlemlerden de birikir;
                        # tam silahlanma kararı yine haftalık değerlendirme + kapı ölçümünündür.
                        row2 = {"date": dstr, "source_skill": skills.screener_for(_s2.setup),
                                "sector": SECTORS.get(t, "?"), "dormant_setup": True, **_s2.as_row()}
                        candidates.append(row2)
                sig = next((_all[su] for su in strat.ARMED_SETUPS if su in _all), None)
                if sig:
                    row = {"date": dstr, "source_skill": skills.screener_for(sig.setup),   # the screener that actually fired
                           "sector": SECTORS.get(t, "?"), **sig.as_row()}
                    candidates.append(row)
            candidates.sort(key=lambda c: c["score"], reverse=True)
            store.merge_dated_jsonl("candidates.jsonl", dstr, candidates)

        from .shadow_model import ShadowTradeOutcomeModel
        try:
            _shadow = ShadowTradeOutcomeModel.load()
        except Exception:  # sessiz-yutma: yardımcı G/Ç yolu; çağıran yokluğu zaten yedek değerle karşılıyor ve asıl okuma hatası store katmanında bir kez uyarılıyor
            _shadow = None
        # aynadaki meşgul semboller (canlı emir + motor yetimi) — yalnız alpaca_paper modunda dolu;
        # iç-broker modunda boş küme = davranış değişmez.
        _rc_snap = store.read_json("broker_reconcile.json", {}) if config.BROKER == "alpaca_paper" else {}
        _mirror_busy = set(_rc_snap.get("alive_order_syms") or []) | \
                       set((_rc_snap.get("positions") or {}).get("engine_orphans") or [])
        if config.BROKER == "alpaca_paper":
            try:                                     # olay-güdümlü katman: ANLIK bekleyenler (websocket)
                from .mirror_stream import pending_symbols_snapshot
                _mirror_busy |= pending_symbols_snapshot()
            except Exception as e:
                # YASA 4: bu düşerse _mirror_busy EKSİK kalır ve aynada zaten bekleyen
                # bir sembole İKİNCİ emir gidebilir. Sessizken tek belirtisi "bir gün fazladan bir
                # emir" olurdu — yani hata değil, miktar değişimi.
                obs.warn("mirror_pending_snapshot_failed", error=f"{type(e).__name__}: {e}",
                         detail="meşgul sembol kümesi disk anlık görüntüsüyle sınırlı")
        with skills.pipeline_run("P3_PLAN", artifact="state/trade_plans.jsonl"):
            sector_ct = {}
            for t in b.positions:
                sector_ct[SECTORS.get(t, "?")] = sector_ct.get(SECTORS.get(t, "?"), 0) + 1
            slots = limits["max_open_positions"] - len(b.positions)
            # OPERATÖR ONAYI TAŞINIR. `merge_dated_jsonl` bu TARİHİN tüm satırlarını yeniden
            # yazar; aynı seans yeniden işlenirse (re-seed sonu ya da elle tetik — monotonluk bekçisi
            # EŞİT güne izin verir) operatörün onayı SESSİZCE silinir ve onaylı plan bir daha
            # silahlanamazdı. Onay bir OLAYdır: yeniden üretilen satıra aynen taşınır, hüküm değişmez.
            _onaylar = {r.get("id"): r.get(ONAY_ALANI)
                        for r in store.read_jsonl("trade_plans.jsonl")
                        if r.get("date") == dstr and r.get(ONAY_ALANI)}
            _plan_law: dict = {}     # plan_id → E1 icra kararı (aşağıda silahlananlar için saklanır)
            others_rets = [ind.returns_tail(per[o].loc[:d, "close"]) for o in b.positions if o in per]  # once/day
            # NAV TAVANLARININ ÜRETİCİ TARAFI. `guard._y3_portfolio_caps`
            # equity/sector_notional/heat_pct (portföy) + notional/risk_dollars (plan) okuyor; canlı
            # döngü BUNLARIN HİÇBİRİNİ göndermiyordu, yani `portfolio.sector_cap`/`heat_cap` knob'ları
            # açılsa bile yapısal olarak bağlayamıyordu (en sıkı tavanla bile hüküm birebir aynı).
            # Kitap seansta BİR KEZ ölçülür (aday döngüsü içinde değişmez); silahlananlar aday başına
            # eklenir, çünkü `open_risk_r` bacağı da onları sayıyor. NAV KAPANIŞ markıyla: kapı D'nin
            # kapanışında koşar, `marks_open` sabahın devre-kesici penceresine aittir.
            _y3_mk = _marks(per, d)
            _y3_eq = b.equity(_y3_mk)
            _y3_book = [{"sector": SECTORS.get(t, "?"), "qty": p.qty, "entry": p.entry,
                         "stop": p.stop, "trail_stop": p.trail_stop, "mark": _y3_mk.get(t)}
                        for t, p in b.positions.items()]
            for c in candidates:
                portfolio = {"open_positions": len(b.positions) + len(meta["armed"]),
                             # 0.0 at ARM time — identical to the backtest (backtest.py "breaker enforced
                             # at fill, not at arm"): the live loop passing the real day P&L here NO_GO'd
                             # candidates the walk-forward would have armed on the same bars, silently
                             # diverging live from simulated behavior. The breaker still
                             # blocks the FILL next open in both engines.
                             "sector_counts": sector_ct, "day_pnl_pct": 0.0,
                             "open_risk_r": sum(p.size_r for p in b.positions.values())
                                            + sum(a["size_r"] for a in meta["armed"]),
                             "max_corr": ind.corr_max(per[c["ticker"]].loc[:d, "close"], others_rets),
                             **guard.y3_portfolio_inputs(_y3_book, meta["armed"], equity=_y3_eq,
                                                         size_fn=b.size_position)}
                _pid = (f"P-{dstr}-{c['ticker']}-{c.get('setup','')}" if c.get("dormant_setup")
                        else f"P-{dstr}-{c['ticker']}")   # uyuyan: kurulum ekli kimlik (çakışma + ayrışma)
                plan = {"id": _pid, "date": dstr, "ticker": c["ticker"], "side": "long",
                        "entry_trigger": c["entry_trigger"], "stop": c["stop"],
                        "targets": [c["profit_target"]], "size_r": min(c["size_r"], limits["max_position_r"]),
                        "r_multiple_expected": round((c["profit_target"] - c["entry_trigger"]) / c["r_per_share"], 2),
                        "regime_at_plan": rj["regime"], "sector": c["sector"], "score": c["score"],
                        "setup": c.get("setup", "breakout_vcp"),
                        "dormant_setup": bool(c.get("dormant_setup")),
                        "profit_target": c["profit_target"], "strategy_version": version,
                        "skill_chain": [skills.screener_for(c.get("setup", "breakout_vcp")), "position-sizer", "pre-trade-discipline-gate"]}
                if _onaylar.get(_pid):                  # önceki turda verilmiş onay taşınır
                    plan[ONAY_ALANI] = _onaylar[_pid]
                _checks = []                            # Faz 3 (5b): yapılandırılmış karar ağacı
                # dolar büyüklükleri kapıya PLAN ŞEMASINI BOZMADAN gider — `armed_pivots`/`atr`
                # yan haritalarıyla aynı gerekçe: `notional`/`risk_dollars` bir DEFTER alanı değil,
                # tavanın girdisidir. E2'ye (`trade_plans.jsonl`) yazılan sözlük `plan`dır ve şeması
                # değişmedi; kapıya giden onun zenginleştirilmiş KOPYASIDIR.
                _gate_plan = {**plan, **guard.y3_plan_inputs(plan, equity=_y3_eq,
                                                             size_fn=b.size_position)}
                verdict, greasons = guard.classify_gate(_gate_plan, portfolio, rj, goal, eff, detail_out=_checks)
                _bl = earnings.in_blackout(c["ticker"], dstr)
                # DOĞRULANDI mı yoksa VERİ YOK mu? İkisi de "passed" görünüyordu; canlıda evrenin
                # %28'inde (250'nin 69'u) takvim yok, yani guard o isimlerde sessizce kapalı. Plan
                # kaydı artık bunu taşıyor.
                _ek = earnings.known(c["ticker"])
                _checks.append({"check": "earnings_blackout", "passed": not _bl, "severity": "hard",
                                "value": c["ticker"], "threshold": None,
                                "coverage": "known" if _ek else "no_calendar_data",
                                "note": ("kazanç öncesi karartma (earnings blackout)" if _bl
                                         else (None if _ek else "kazanç takvimi YOK — kontrol edilemedi"))})
                if verdict != "NO_GO" and _bl:
                    verdict = "NO_GO"; greasons = list(greasons) + ["kazanç öncesi karartma (earnings blackout)"]
                # FAIL-OPEN ARTIK BEYANLI. `gate_checks.coverage` bunu 2026-07-21'den
                # beri taşıyordu ama KARAR SATIRINDA — panonun ve operatörün ilk baktığı
                # `gate_reasons`ta — iz yoktu: evrenin 57/251'inde karartma kapısı sessizce
                # geçirgendi. Not KARAR DEĞİŞTİRMEZ (NO_GO değil, REVIEW'e düşürme değil): veri
                # yokluğu sembolün suçu değil, bizim görünürlük borcumuzdur. Metnin "NOT: " öneki
                # ve gerekçesi `earnings.COVERAGE_NOTE`ta yazılı.
                if not _ek:
                    greasons = list(greasons) + [earnings.COVERAGE_NOTE]
                    _kapsam_disi += 1
                # TAKVİM GÜVENİLMEZSE KAPI SEMBOLE DEĞİL TURA KAPANIR.
                # Ölçüm ve iki bilinçli istisna `earnings.calendar_untrustworthy` blokunda.
                # NEDEN NO_GO DEĞİL REVIEW: kapının kör olması bir SEMBOLÜN kusuru değildir; red
                # etmek, bilgi yokluğunu kanıt sayıp planı gömmek olurdu (arming'in `gate_undefined`
                # dersinin aynısı). REVIEW "insan/ikinci kapı baksın" der ve kararı KAYBETMEZ.
                # NO_GO'ya DOKUNULMAZ: zaten reddedilmiş bir planı REVIEW'e ÇIKARMAK kapıyı
                # gevşetmek olurdu — bu blok yalnız sıkıştırabilir.
                if _takvim_kusuru:
                    _tk_dusus = verdict == "GO"
                    _checks.append({"check": "earnings_calendar_health", "passed": False,
                                    "severity": "soft", "value": _takvim_kusuru.get("kod"),
                                    "threshold": f"ileri_gun>={earnings.BLACKOUT_DAYS}",
                                    "note": _takvim_kusuru.get("sebep")})
                    if _tk_dusus:
                        verdict = "REVIEW"
                        greasons = list(greasons) + [
                            earnings.CALENDAR_UNTRUSTWORTHY_NOTE.format(sebep=_takvim_kusuru.get("sebep"))]
                        _takvim_dusen += 1
                # SENKRON KORUMASI (v3 kriter-1): aynada bu hisse için hâlâ CANLI bir emir ya da motor
                # yetimi pozisyon varken YENİ karar üretilmez — çifte maruziyet/karışık defter riski.
                # Kaynak: son uzlaştırmanın anlık görüntüsü (her döngü sonunda tazelenir).
                _mb = c["ticker"] in _mirror_busy
                _checks.append({"check": "mirror_busy", "passed": not _mb, "severity": "hard",
                                "value": c["ticker"], "threshold": None,
                                "note": "aynada bekleyen emir/yetim pozisyon var" if _mb else None})
                if verdict != "NO_GO" and _mb:
                    verdict = "NO_GO"; greasons = list(greasons) + ["aynada bekleyen emir/yetim pozisyon var"]
                plan["gate_verdict"], plan["gate_reasons"] = verdict, greasons
                plan["gate_checks"] = _checks           # panodaki karar-ağacı tablosu buradan okur
                try:                                   # v3 gölge kanıtı — kapı kararına dokunmaz
                    pw = _shadow.predict_proba(plan) if _shadow else None
                    if pw is not None:
                        plan["p_win_shadow"] = pw
                        # TERFİLİ modelin TEK yetkisi: REVIEW + çok düşük P(kazanç) → NO_GO.
                        # GO ve NO_GO kararlarına hiçbir koşulda dokunmaz; terfi kriteri shadow_model'de
                        # yazılı (canlı Brier taban-oranı yenmeden bu blok hiç çalışmaz).
                        from .shadow_model import ShadowTradeOutcomeModel as _SMv
                        _sv = verdict == "REVIEW" and pw < _SMv.REVIEW_VETO_P and _SMv.is_promoted()
                        _checks.append({"check": "shadow_veto", "passed": not _sv, "severity": "hard",
                                        "value": pw, "threshold": f">={_SMv.REVIEW_VETO_P}",
                                        "note": "gölge model (terfili) vetosu" if _sv else None})
                        if _sv:
                            verdict = "NO_GO"
                            greasons = list(greasons) + [f"gölge model (terfili): P(kazanç) %{int(pw*100)} < %{int(_SMv.REVIEW_VETO_P*100)}"]
                            plan["gate_verdict"], plan["gate_reasons"] = verdict, greasons
                except Exception as e:
                    # YASA 4 — EN TEHLİKELİ SINIF: burası bir KAPI KARARI. Sessizce
                    # düşerse gölge model vetosu HİÇ uygulanmaz, plan GO kalır ve karar ağacında
                    # "shadow_veto" satırı da hiç görünmez (gate_checks 144/144 boş kalmasının aynısı).
                    obs.warn("shadow_veto_check_failed", plan_id=plan.get("id"),
                             ticker=plan.get("ticker"), error=f"{type(e).__name__}: {e}")
                plans.append(plan)
                # E1 İCRA GİRDİLERİ — SİNYAL BARI KAPANIŞINDA SABİTLENİR ("emir parametreleri
                # plan anında sabitlenir; as-of ihlali yok"). Referans fiyat o kapanıştır: emir
                # kapanıştan SONRA, ertesi açılıştan ÖNCE gider. `entry_trigger` çoğu kurulumda tam
                # olarak bu kapanıştır — buy-stop'un "stop price must be greater than current price"
                # ile reddedilmesinin (95/95) kökü budur ve karar `gap_at_submit` ile kayda geçer.
                try:
                    _ref = float(per[c["ticker"]].loc[d, "close"])
                except Exception:  # sessiz-yutma: referans ÖLÇÜLEMEDİ ve karar sözlüğü bunu `ref_kaynak` ile beyan eder (uydurma fiyat yok)
                    _ref = None
                # PİVOT DA BU YAN TABLODA TAŞINIR. Kurulumun yapı çizgisi
                # `strategy.early_kill_pivot_exit`in okuduğu TEK girdidir; replay (backtest.armed_pivots)
                # ve gölge-v2 onu taşıyordu, canlı motor TAŞIMIYORDU → `Position.pivot` daima 0.0 →
                # knob terfi etse canlıda SESSİZ NO-OP, replayde ateşler (sahte-terfi yolu). Plan
                # SÖZLÜĞÜNE konmaz (şema iki motorda aynı kalmalı, test_differential_v60) — icra
                # girdisi olduğu için icra tablosuna konur, `atr`/`ref_price` ile aynı yasa.
                # Ölçülemezse None (0.0 DEĞİL): fill_entry `pivot or 0.0` ile "bilinmiyor"a düşer.
                _pv = float(c.get("pivot") or 0.0)
                _plan_law[plan["id"]] = {
                    **BR.entry_order_decision(float(c["entry_trigger"]), ref_price=_ref,
                                              atr=c.get("atr")),
                    "pivot": (_pv if _pv > 0 else None)}
                # TEK KOŞUL NOKTASI (`girise_uygun`): iki keşif dalı da eskiden `verdict == "GO"`
                # yazıyordu ve operatörün REVIEW planına verdiği onayın hiçbir yolu yoktu — kapı
                # "insan baksın" diyor, insan bakıyor, sonra hiçbir şey olmuyordu. Çıta GEVŞEMEDİ:
                # onaysız REVIEW bu iki dalda hâlâ silahlanmaz, NO_GO hiçbir koşulda geçmez.
                if plan["dormant_setup"]:
                    # uyuyan kurulum: normal slot ASLA — yalnız keşif sondası (GO ya da operatör
                    # onaylı REVIEW; boyut tavanı EXPLORE_MAX_R aynen bağlar)
                    if girise_uygun(plan, verdict):
                        explore_pool.append(plan)
                elif explore_mode:
                    # KEŞİF: GO ya da operatör-onaylı REVIEW aday olur — silahlama döngü SONUNDA
                    # (havuzdan seçim). Onaysız REVIEW keşifte silahlanMAZ (çıta yüksek kalır).
                    if girise_uygun(plan, verdict):
                        explore_pool.append(plan)
                elif verdict != "NO_GO" and slots > 0:   # GO/REVIEW arm at L0; NO_GO never trades
                    meta["armed"].append(plan)
                    sector_ct[c["sector"]] = sector_ct.get(c["sector"], 0) + 1
                    slots -= 1
            # KEŞİF SLOT SEÇİMİ: kapıyı geçmiş eşitler arasından tek sonda. ≥2 adayda yerel ajan
            # SIRALAYICI olarak sorulur (yetkisi yalnız bu seçim; boyut/karar üretemez); cevap yoksa
            # skor sırası (havuz zaten skor-sıralı adaylardan doldu) — fail-open.
            if explore_pool:
                open_expl = [pos for pos in b.positions.values() if getattr(pos, "exploration", False)]
                armed_expl = [a for a in meta["armed"] if a.get("exploration")]
                n_explore = len(open_expl) + len(armed_expl)
                used_r = sum(float(getattr(p2, "size_r", 0)) for p2 in open_expl) + \
                         sum(float(a.get("size_r") or 0) for a in armed_expl)
                # sıralama: ≥2 adayda yerel ajanın seçimi başa, kalanlar skor sırası (havuz zaten sıralı)
                ordered = list(explore_pool)
                if len(ordered) > 1:
                    try:
                        from . import hermes as _hm
                        pick = _hm.rank_explore([{"ticker": p2["ticker"], "setup": p2.get("setup"),
                                                  "score": p2.get("score"),
                                                  "rr": p2.get("r_multiple_expected")}
                                                 for p2 in ordered])
                        if pick:
                            ordered.sort(key=lambda p2: 0 if p2["ticker"] == pick else 1)
                    except Exception:  # sessiz-yutma: geç bağlanan yardımcı modül/çağrı; asıl karar bu değere bağlı değil ve çağıran yokluğu yedek değerle karşılıyor
                        pass
                for chosen in ordered:
                    if n_explore >= EXPLORE_MAX_POS or used_r + EXPLORE_MAX_R > EXPLORE_TOTAL_R + 1e-9:
                        break
                    chosen["size_r"] = min(float(chosen["size_r"]), EXPLORE_MAX_R)
                    chosen["exploration"] = True
                    chosen["gate_reasons"] = list(chosen.get("gate_reasons") or []) + \
                        [f"keşif sondası ({'uyuyan kurulum' if chosen.get('dormant_setup') else 'bütçe %0'}): "
                         f"kanıt toplama, {EXPLORE_MAX_R}R tavan"]
                    meta["armed"].append(chosen)
                    n_explore += 1
                    used_r += float(chosen["size_r"])
                    obs.log("exploration_armed", ticker=chosen["ticker"], regime=rj["regime"],
                            size_r=chosen["size_r"], slot=n_explore, llm_ranked=len(explore_pool) > 1)
            # E1 YAN TABLOSU: yalnız SİLAHLI planların icra kararı taşınır (taşınan/carried planlar
            # dahil — onların kararı ÖNCEKİ seansta sabitlendi ve YENİDEN hesaplanmaz: yeniden
            # hesaplasaydık aynı plan iki farklı limitle iki farklı motorda dolabilirdi).
            # Sınırlıdır (silahlı sayısı ≤ max_open_positions + keşif tavanı) → sonsuz büyüme yok.
            _prev_law = dict(meta.get("entry_law") or {})
            _prev_law.update(_plan_law)
            # SİLAHLILARA EK OLARAK BU SEANSIN REVIEW PLANLARI DA YASASINI KORUR. Operatör
            # onayı döngüden SONRA gelir; onaylanan plan ancak SİLAHLANMA ANINDAKİ (sinyal barı
            # kapanışı) icra girdileriyle kuyruğa alınabilir. Yasa atılsaydı onaylı plan
            # atr/ref_price'sız dolardı: aynı planda iki farklı limit tavanı ve kırılım teyidinin
            # kaybı — tek-kapı yasasının kapattığı kusurun ta kendisi. SINIR KORUNUR: küme her seans SIFIRDAN
            # kurulur (silahlı ≤ tavan + o seansın REVIEW planları), yani birikim yok.
            _yasa_tut = {a["id"] for a in meta["armed"] if a.get("id")} | \
                        {p2["id"] for p2 in plans
                         if p2.get("gate_verdict") == "REVIEW" and p2.get("id")}
            meta["entry_law"] = {pid: _prev_law[pid] for pid in _yasa_tut if pid in _prev_law}
            store.merge_dated_jsonl("trade_plans.jsonl", dstr, plans)
            try:                                   # günün TÜM planları + uyuyan ateşlemeler
                from . import counterfactual       # karşı-olgusal deftere açılır (dönüş görmezden gelinir)
                counterfactual.collect(dstr, plans, {a["id"] for a in meta["armed"]}, dormant_sigs,
                                       int(float(eff.get("exit.time_stop_days", 15))),
                                       near_miss=near_miss_sigs, regime=rj["regime"])
                # ANA collect'in muhasebesi geç-borç çağrıları EZMEDEN kopyalanır:
                # özet olaydaki `near_miss_yazilan` bu seansın satırlarını sayar, geç-borcunkini değil.
                _nm_toplama = dict(counterfactual.SON_TOPLAMA)
                for _ds, _rows in (late_by_date or {}).items():    # kaçan seanslar kendi tarihleriyle
                    counterfactual.collect(_ds, [], set(), [],
                                           int(float(eff.get("exit.time_stop_days", 15))),
                                           near_miss=_rows, regime=rj["regime"])
            except Exception as e:
                obs.warn("cf_collect_failed", error=f"{type(e).__name__}: {e}")
            if meta["armed"]:                              # push a single new-plans alert (no-op if unconfigured)
                try:
                    from . import notify
                    if notify.configured():
                        top = meta["armed"][0]
                        # ham `notify.send` metni yerine `notify.new_plan` — üretilip
                        # HİÇ çağrılmayan sarmalayıcı buraya bağlandı ve metin TEK yerde kaldı.
                        # Kapı hükmü de metne girer (GO ile REVIEW aynı bildirim değil).
                        notify.new_plan(top["ticker"], top.get("gate_verdict") or "?",
                                        top.get("r_multiple_expected"),
                                        n=len(meta["armed"]), date=dstr)
                except Exception:  # sessiz-yutma: obs alarmı/kaydı bu noktada ZATEN yazıldı; ikincil bildirim kanalının (Telegram/webhook) düşmesi alarmı asla düşüremez
                    pass
            # mirror the agent's armed BUY decisions to the Alpaca PAPER account (opt-in backend, paper-only)
            # GÖVDE `mirror_submit_armed`A TAŞINDI — pano düğmesi de AYNI kapıdan
            # geçsin diye. Mantık değişmedi; buradaki tek fark çağrı olması.
            mirror_submit_armed(meta, dstr, eq_now=eq_now, plans=plans, halted=halted, source="loop")

        # ---- 2.4 GÖLGE-VARYANT PORTFÖYLERİ: tek kanca, SIFIR yetki, kendi defteri ----------------
        # P3'ün DIŞINDA (pipeline_run bloğu kapandıktan sonra): ölçüm katmanının maliyeti/arızası
        # denetlenen P3 açıklığına yazılmasın. Nüfus canlı akışın ÜST KÜMESİ (aday ∪ near-miss;
        # gerekçe shadow_variants başlığında). Dilim/RS/sektör/korelasyon girdileri ÇAĞRILABİLİR
        # olarak geçer — gölge onların ikinci bir sürümünü tutmaz. Hata gölgede kalır: bu blok
        # düşerse günlük tur aynen devam eder (planlar ZATEN diske yazıldı).
        try:
            from . import shadow_variants as _sv
            _sv.record_cycle(
                dstr,
                sorted({c["ticker"] for c in candidates} | {s.ticker for s, _ in near_miss_sigs}),
                tail_of=lambda t: _scan_tail(per[t], d),
                rs_of=lambda t: rs_map.get(t, 50),
                sector_of=lambda t: SECTORS.get(t, "?"),
                max_corr_of=lambda t: ind.corr_max(per[t].loc[:d, "close"], others_rets),
                eff=eff, regime=rj, goal=goal, limits=limits, bounds=config.bounds(),
                version=version,
                book={"positions": {t: {"sector": SECTORS.get(t, "?"), "size_r": p.size_r}
                                    for t, p in b.positions.items()},
                      "equity": eq_now, "peak_equity": meta.get("peak_equity", START_EQUITY)},
                live_armed=[a["ticker"] for a in meta["armed"]], explore_mode=bool(explore_mode),
                # GÖLGE-v2: barlar + indeks + rejim bayrağı GEÇİLİRSE aynı kanca
                # yaşam-döngüsü motorunu da koşturur (fill → yönetim → çıkış → mark, varyant başına
                # kalıcı kâğıt kitap). `per`/`idx` ZATEN burada; ikinci bir bar yükleyici YOK.
                bars=per, index_bars=idx, regime_ok=regime_ok)
        except Exception as e:
            obs.warn("shadow_variants_failed", error=f"{type(e).__name__}: {e}")

    if not _p2_kostu:
        # YASA 4: P2 koşmayınca near-miss gölge bacağı da koşmaz — bugüne dek bu
        # sessizdi ve "defterde near-miss neden yok?" sorusu iki hafta cevapsız kaldı. Sebep
        # türetimi blok koşulunun birebir tersidir; explore_mode budget≤0 hâlini zaten kapsadığı
        # için (halted/data_bad değilse) kalan tek sebep kitap doluluğudur.
        obs.log("near_miss_scan_atlandi", date=dstr,
                sebep=("halted" if halted else "data_bad" if data_bad else "kitap_dolu"),
                detail="P2 taraması (near-miss gölge bacağı DAHİL) bu turda hiç koşmadı — özet "
                       "olayda near_miss=None 'ölçülmedi' demektir, 0 değil")

    if plans:
        # yerel LLM ajanından aday İKİNCİ GÖRÜŞÜ — arka planda (danışma katmanı; kapıyı değiştirmez,
        # döngüyü bloklamaz, hata verirse sessizce düşer)
        try:
            from . import hermes
            hermes.review_candidates_async(dstr)
        except Exception:  # sessiz-yutma: danışma katmanı — LLM ikinci görüşü kapıyı DEĞİŞTİRMEZ; yokluğu kararı bozmaz, hatası da günlük turu bloklayamaz
            pass

    meta["last_date"] = dstr
    # SICAK FİYAT — DEVRE DIŞI. Bu blok seansın kapanış fiyatlarını
    # `mrd:price`a yazıyordu. ÖLÇÜM: `hotstate.get_price`ın PRODÜKSİYONDA hiçbir çağıranı yok (yalnız
    # testler); intraday tüketicisi bilerek sıcak fiyatı DEĞİL admissible barın OHLC'sini okuyor
    # (intraday_cycle: "ASLA sıcak fiyattan"). Yani EOD kapanışlarını Redis'e kopyalamak evrenin
    # tamamı için her tur pipeline yazımı yapıp kimseye okutmamaktı — bedava sadelik, kapatıldı.
    #   NOT: `mrd:price`ın DİĞER yazıcısı (`hotstate.ingest_bars`, kapanmış bar → sıcak fiyat) YERİNDE
    #   DURUYOR; kapanan yalnız EOD kopyasıdır. GERİ AÇMA: aşağıdaki dört satırın yorumunu kaldır.
    # try:
    #     from . import hotstate
    #     _closes = {t: float(per[t].loc[d, "close"]) for t in per if d in per[t].index}
    #     if _closes:
    #         hotstate.set_prices(_closes, ts=dstr)
    # except Exception:  # sessiz-yutma: hotstate uçucu türev; fiyat kopyalama hatası günlük turu düşüremez
    #     pass
    _hotstate_off_once("mrd:price", "daily_cycle", "get_price")
    # `meta["day_start_equity"]` ARTIK BURADA YAZILMIYOR. Eski satır
    # (`b.equity(_marks(per, d))` — KAPANIŞ markı) canlı devre kesicisini bir GECELİK BOŞLUK
    # kesicisine indiriyordu; yazım açılış fazına, replay ile aynı noktaya taşındı (yukarıda
    # GÜNLÜK KESİCİ bloğu). Buraya ikinci bir yazım koymak, iki motoru yeniden ayrıştırırdı.
    mirror = {}
    try:
        mirror = reconcile_broker_state(meta, dstr, b.closed,   # Phase 1: reconcile internal book ↔ Alpaca mirror
                                        # `ts_open` sapma sınıflandırıcısının YAŞ sinyalidir —
                                        # bugün dolmayan pozisyonda bugünün eq'siyle kıyas YAPILMAZ.
                                        open_positions={t: {"qty": p.qty, "scaled_out": p.scaled_out,
                                                            "trail_stop": p.trail_stop, "plan_id": p.plan_id,
                                                            "ts_open": p.ts_open}
                                                        for t, p in b.positions.items()},
                                        # E2: RESMÎ AÇILIŞ bu seansın barlarından gelir — mutabakat
                                        # katmanı ikinci bir bar kaynağı açmaz (tek gerçek).
                                        opens={t: float(df.loc[d, "open"]) for t, df in per.items()
                                               if d in df.index},
                                        # DOLUM anının boyut tabanı — iç motor bu `eq_now`la
                                        # doldurdu (yukarıda :1114). Adet sapması sınıflandırması bunu
                                        # gönderim makbuzuyla kıyaslar (drift_sinifi).
                                        fill_eq_now=eq_now,
                                        # koruma-OCO dolumu kitaba kapanış olarak işlenebilsin
                                        # diye kitabın kendisi geçilir (_save_broker aşağıda, kapanış
                                        # aynı turda kalıcılaşır).
                                        broker=b)
    except Exception as e:
        obs.warn("reconcile_failed", error=f"{type(e).__name__}: {e}")
    _entry_exec_trim()
    _save_broker(b, meta)

    try:
        with skills.pipeline_run("P5_LEARN", artifact="state/hypotheses.jsonl"):   # learning is auditable too
            outcome = rollback.evaluate_outcomes(goal)   # close the learning loop: promote/rollback + writeback
            try:
                from .shadow_model import ShadowTradeOutcomeModel as _SM
                _SM.refit_and_save()                     # v3 gölge model — her döngü ucuz yeniden-eğitim
                from .regime_trigger import DeferredRegimeBudgetTrigger
                DeferredRegimeBudgetTrigger().evaluate() # v3 ertelenmiş bütçe tetikleyicisi (yalnız sinyal)
                from . import analytics as _an           # skor kalibrasyonu — rapor, karar değil
                _cal = _an.score_calibration()
                if _cal:
                    store.write_json("score_calibration.json", _cal)
                    obs.log("score_calibration", n=_cal["n"], rank_ic=_cal["rank_ic"])
                    # ANLIK DEĞER ÜZERİNE YAZILIR, TREND BİRİKİR: bar günü başına tek nokta
                    # (idempotent — aynı gün ikinci koşu yazmaz). "IC yükseliyor mu?" sorusu
                    # ancak defterde tarih tarih duran bir seriyle cevaplanabilir.
                    _an.record_score_calibration_point(dstr, _cal)
                from . import probgate as _pg            # kapı meta-kalibrasyonu (kendini sıkılaştırır)
                _pg.refresh_meta_calibration()
                _an.llm_opinion_calibration()            # LLM görüş kalibrasyonu (terfi kuralı yazılı)
                _an.exit_efficiency()                    # MFE/MAE muhasebesi (rapor + UCB dürtme bayrağı)
                _an.cf_fidelity()                        # cf simülasyonunun canlıya sadakati
                # Aşama 1.2: bileşen IC'si (rs/tight/vol/prox × 5/10/20 bar × katman). Bileşenler
                # defterde alan olarak durmadığı için barlardan yeniden hesaplanır — bu yüzden
                # P5'in en pahalı adımı (evren CSV'leri okunur). Günde bir koşar ve SIFIR yetkisi
                # vardır; düşerse döngü aynen devam eder (dış try zaten sarıyor, ama bu adımın
                # maliyeti diğerlerini rehin almasın diye kendi koruması var).
                try:
                    from . import component_ic as _cic
                    _cic.component_ic()
                except Exception as e:
                    obs.warn("component_ic_failed", error=f"{type(e).__name__}: {e}")
                # Aşama 1.3: min_score eşik eğrisi. Bileşen IC'siyle AYNI bar evrenini okur (bu
                # yüzden hemen ardından koşar — CSV'ler işletim sistemi önbelleğinde sıcak) ve
                # onun gibi SIFIR yetkilidir. Ayrı korumada: eğri düşerse bileşen tablosu yaşar.
                try:
                    from . import threshold_curve as _tc
                    _tc.build()
                except Exception as e:
                    obs.warn("threshold_curve_failed", error=f"{type(e).__name__}: {e}")
                # ÖNER→ÖLÇ→ÖĞREN OTOMASYONU (Hermes paketi). Kuyrukta bekleyen
                # bileşik varsa HAFTALIK YOKLAMA BÜTÇESİ içinde prescreen AYRI BİR SÜREÇTE başlar.
                # GECE DÖNGÜSÜNÜ BLOKLAMAZ: prescreen dakikalar sürer, senkron çağrılsaydı EOD işleri
                # gecikirdi (ops/barsarchive-run.sh nohup deseni). Kendi korumasında: kuyruk yolu
                # düşse bile P5'in geri kalanı yaşar.
                try:
                    from . import hermes_composite as _hc
                    _sp = _hc.spawn_pending(limit=1)
                    if _sp.get("spawned"):
                        obs.log("composite_queue_spawned", n=len(_sp["spawned"]),
                                butce_kalan=_sp.get("butce_kalan"))
                except Exception as e:
                    obs.warn("composite_spawn_hook_failed", error=f"{type(e).__name__}: {e}")
                # SKILL ÖZ-YÖNETİMİ: atıf kanıtı eşiğini aşan skiller. PROTECTED beşlisi ASLA;
                # motor-içi skiller yalnız RAPORLANIR (bayrak yazımı davranışı değiştirmez).
                try:
                    from . import skills as _sk5
                    _sk5.auto_shadow_from_evidence()
                except Exception as e:
                    obs.warn("skill_auto_shadow_failed", error=f"{type(e).__name__}: {e}")
                _an.mae_profile()                        # stopların kör ikizi (MAE muhasebesi)
                _an.near_miss_report()                   # darboğaz: hangi eşik masada para bırakıyor?
                _an.regime_edge()                        # cf-bootstrap bulgusu: rejim başına edge (ajana besleme)
                _universe_drift_check()                  # evren ölü isim taşıyor mu?
                from . import watchdog as _wd5
                _wd5.check_integrity_and_alarm()         # ÜRETKENLİK+KORUNUM+DETERMİNİZM (sessiz hata avı)
                _wd5.beat("p5_calibrations")
            except Exception as e:
                obs.warn("v3_learn_layer_failed", error=f"{type(e).__name__}: {e}")
        if outcome:
            obs.log("outcome_evaluated", **{k: outcome[k] for k in ("version", "delta", "promoted", "rolled_back") if k in outcome})
    except Exception as e:
        obs.warn("evaluate_outcomes_failed", error=f"{type(e).__name__}: {e}")

    # ---- TREND KOLU GÖLGE-KİTABI — ANA İŞTEN SONRA, SIFIR YETKİ ----
    # İncumbent kol (chandelier × N=10) canlı barlarda SANAL bir defterde yürür.
    # Emir yolu, portföy, plan, karne: HİÇBİRİNE dokunmaz — tek yazdığı `trend_book.json`.
    # HATA ANA DÖNGÜYÜ ASLA KIRMAZ (YASA 4): bir gölge defterinin muhasebesi, gerçek kitabın
    # nabzını/kapanışını rehin alamaz. Yutma SESSİZ DEĞİL — olay adıyla kaydedilir ve gölge
    # özeti None kalır (uydurma sıfır DEĞİL: "ölçülemedi" ile "pozisyon yok" ayrı şeylerdir).
    _trend = None
    try:
        from . import trend_shadow as _ts
        _trend = _ts.run_cycle(bars, index, on_date=dstr)
    except Exception as e:
        obs.warn("trend_shadow_failed", error=f"{type(e).__name__}: {e}", date=dstr,
                 detail="gölge-kitap turu düştü — canlı döngü ETKİLENMEDİ (sıfır yetkili katman)")
    _trend_ozet = ({"pozisyon": _trend.get("pozisyon"), "equity": _trend.get("equity"),
                    "status": _trend.get("status")} if isinstance(_trend, dict) else None)

    equity = round(b.equity(_marks(per, d)), 2)
    # WP2-D BACAK-2 — SEANS SONU NOKTASI. Nabızdan HEMEN ÖNCE: ikisi de aynı `equity` sayısını
    # taşır ve araya bir yazım girerse pano ile eğri aynı turda iki farklı sayı gösterirdi.
    # Yazım kararı fonksiyonun kendisindedir (idempotens, taban, ölçülemeyen değer) — burada
    # yalnız MAKBUZ alınır ve aşağıdaki olay/dönüşte okunur.
    _egri_nokta = _persist_equity_point(dstr, equity, meta)
    health.write_heartbeat(version=version, open_positions=len(b.positions), equity=equity,
                           last_bar=dstr, regime=rj["regime"], exposure_budget_pct=rj["exposure_budget_pct"],
                           armed=len(meta["armed"]), day_pnl_pct=round(day_pnl_pct, 4),
                           breaker_tripped=breaker, halted=halted, data_ok=not data_bad,
                           explore_mode=bool(explore_mode),
                           **ayna_sapma_alanlari(mirror))
    # KAPSAM SAYACI: "kaç plan üretildi" ile "kaç planda karartma kapısı KONUŞABİLDİ"
    # ayrı sayılardır. İkincisi bugüne dek hiçbir olayda yoktu; fail-open sessizken bir eğilim
    # (kapsamın aşınması) yalnız plan plan bakılarak görülebilirdi. `takvim_bos` üçüncü hâli taşır:
    # "57 sembol eksik" ile "takvim HİÇ yok" aynı sayıyla anlatılmaz.
    _kapsam = {"plan": len(plans), "kapsanan": len(plans) - _kapsam_disi, "kapsam_disi": _kapsam_disi,
               "takvim_bos": not earnings._load(),
               # TAKVİM SAĞLIĞI AYNI SATIRDA: "kaç planda kapı konuşamadı" ile "kapı
               # BU TUR hiç konuşamadı" ayrı olgulardır ve ikincisi birincisini anlamsız kılar.
               # Sayaç üretilip TÜKETİLİYOR (YASA 6): karne/pano bu alandan okur.
               "takvim_guvenilmez": (_takvim_kusuru or {}).get("kod"),
               "takvim_guvenilmez_sebep": (_takvim_kusuru or {}).get("sebep"),
               "takvim_dusen_plan": _takvim_dusen}
    # NEAR-MISS KURAKLIK BEKÇİSİ: ana tarama aday bulmuşken GEVŞEK gölgenin 0 bulması
    # yapısal olarak şüphelidir (Temmuz tabanı: her aday gününde ≥1 near-miss; 07-16: 1 aday/12 nm,
    # 07-28: 6/19). 2026-07-30→08-12 sessiz ölümü tam bu geometriyle yaşandı ve hiçbir olay yoktu.
    # Olay eşik tablosunu [sıkı, gevşek] çiftleriyle taşır: iki sütun eşitse gevşetme fiilen ÖLÜdür
    # (bantsız tarama) — kök teşhisi canlı defterden tek satırla okunur. relax_for_near_miss
    # TEK-KAYNAKTIR ve burada yalnız OKUNUR.
    if _p2_kostu and candidates and not near_miss_sigs:
        _rx_k = strat.relax_for_near_miss(eff)
        obs.warn("near_miss_kurak", date=dstr, candidates=len(candidates),
                 esikler={k: [eff.get(k), _rx_k.get(k)]
                          for k in ("entry.min_volume_ratio", "entry.rs_rating_min",
                                    "entry.min_score", "entry.pivot_proximity_pct")},
                 detail="ana tarama aday buldu ama gevşek gölge 0 near-miss üretti — bant boş ya da "
                        "bacak ölü; esikler[k]=[sıkı, gevşek], çiftler eşitse gevşetme etkisiz")
    # BU SATIR PANONUN "DÜN GECE" KARTININ KAYNAĞIDIR (YASA 6 zinciri):
    # `api._son_dongu` olay defterinin KUYRUĞUNDAN bu satırı okur → `/api/today.son_dongu` → kart.
    # Kart eskiden `/api/events`in SON 80 KAYDINDA bunu arıyordu; günde BİR yazılan bir olay, gün
    # içindeki poll/uyarı satırlarıyla o pencereden taşınca kart "ölçülemedi" diyordu — oysa döngü
    # koşmuştu. Düzeltme OKUYUCU tarafındadır (pencere yerine defterin kuyruğu); yeni bir durum
    # dosyası AÇILMADI: döngünün yazdığı dosya kümesi bilinçli ve sınırlı bir listedir
    # (test_loop_gaps_v48::test_loop_writes_only_declared_state_files) ve olgu ZATEN bu satırda
    # yazılı — ikinci bir kopya, aynı olgunun iki sahibi demek olurdu.
    # `near_miss*` sayaçları: üretim `near_miss` (bacak koşmadıysa None — uydurma 0
    # yok), deftere düşen `near_miss_yazilan` (cf.collect muhasebesi; collect konuşmadıysa None),
    # geç-bar borcundan gelen `near_miss_gec`. Okuyucu: pano "dün gece" kartı + teşhis.
    obs.log("daily_cycle", date=dstr, regime=rj["regime"], candidates=len(candidates), plans=len(plans),
            near_miss=(len(near_miss_sigs) if _p2_kostu else None),
            near_miss_yazilan=((_nm_toplama or {}).get("nm_yazilan") if _p2_kostu else None),
            near_miss_gec=(sum(len(v) for v in (late_by_date or {}).values()) if _p2_kostu else None),
            armed=len(meta["armed"]), open_positions=len(b.positions), equity=equity,
            halted=halted, breaker=breaker, data_ok=not data_bad, trend_book=_trend_ozet,
            earnings_kapsami=_kapsam,
            # WP2-D bacak-2 makbuzu: eğriye nokta yazıldı mı, yazılmadıysa NEDEN (YASA 6 — bu
            # satırın okuyucusu pano "dün gece" kartı + teşhis; yazılmayan nokta SESSİZ kalamaz).
            egri_nokta=_egri_nokta)
    return {"status": "ok", "date": dstr, "regime": rj["regime"], "candidates": len(candidates),
            "plans": len(plans), "armed": len(meta["armed"]), "open_positions": len(b.positions),
            "near_miss": (len(near_miss_sigs) if _p2_kostu else None),
            "equity": equity, "halted": halted, "breaker": breaker, "data_ok": not data_bad,
            "trend_book": _trend_ozet, "egri_nokta": _egri_nokta}


SCAN_TAIL_BARS = 340       # P2 tarama penceresi: 252-bar ısınma + haftalık resample payı


def _scan_tail(df_t, d):
    """P2'nin tarama dilimi — TEK TANIM.

    `.loc[:d]` NEDENSELLİK kesimidir (d'den sonrası görünmez), `.tail(SCAN_TAIL_BARS)` maliyet
    kesimidir. Bu ikisi bir tarife: gölge-varyant katmanı AYNI dilim üzerinde ölçmek zorundadır,
    yoksa varyantın "aynı aday akışı" iddiası ilk pencere kaymasında yalan olur. Reçete iki yerde
    elle yazılıydı; tek tanıma indi ve çağıranlar onu paylaşıyor."""
    return df_t.loc[:d].reset_index().tail(SCAN_TAIL_BARS)


def _marks(per, d):
    """`d` seansında barı OLAN sembollerin kapanış fiyatları: `{ticker: close}`.

    O tarihte verisi olmayan sembol sözlüğe HİÇ girmez (eksik fiyat ileri taşınmaz)."""
    return {t: per[t].loc[d, "close"] for t in per if d in per[t].index}


def _persist_trade(trade: dict) -> None:
    """Append a closed trade — DEDUPED against recent rows. Trades are appended mid-cycle but broker
    state (the position's existence + last_date) is saved only at cycle end; if the cycle dies in
    between, every 300s retry reloads the old state, re-closes the same position, and would append the
    identical row again — one crash-day could stack dozens of duplicates into the learning ledger
    (audit #11). Identity = (plan_id|ticker, ts_close, exit_reason, exit price).

    KAYNAK DAMGASI: BURASI defterin İLERİ yoludur — bu fonksiyondan geçen her
    satır canlı kâğıt döngünün GERÇEKTEN kapattığı bir işlemdir. Tohum yolu (`run.replay_seed`)
    defterin tamamını tek seferde yazar ve kendi damgasını basar. Damga satır diske DÜŞMEDEN
    basılır: sonradan damgalamak, damgasız bir aralık doğurur ve bulgu tam olarak o aralıktı."""
    ledgerstamp.stamp(trade, ledgerstamp.LIVE_PAPER)
    key = (trade.get("plan_id") or trade.get("ticker"), str(trade.get("ts_close")),
           str(trade.get("exit_reason")), round(float(trade.get("exit") or 0.0), 6))
    for r in store.read_jsonl("trades.jsonl")[-30:]:
        if (r.get("plan_id") or r.get("ticker"), str(r.get("ts_close")),
                str(r.get("exit_reason")), round(float(r.get("exit") or 0.0), 6)) == key:
            obs.warn("duplicate_trade_suppressed", ticker=trade.get("ticker"), ts_close=trade.get("ts_close"))
            return
    store.append_jsonl("trades.jsonl", trade)


# ---- WP2-D BACAK-2: SERMAYE EĞRİSİNİN KADANSLI YAZARI (2026-08-14) ----------------------------
# NEDEN VAR. `equity_curve.json`a nokta ekleyen HİÇBİR kadanslı yazar YOKTU: yalnız
# `run.replay_seed` (tohum — defterin tamamını tek seferde yazar) ve `sermaye.uygula` (`points`e
# DOKUNMAZ, zarfa reset işareti basar). Canlıda ölçülen sonuç: eğri 2026-07-20'de dondu, 24 gün tek
# nokta eklenmedi, pano P&L eğrisi hareketsiz kaldı ve operatör bunu "P&L yansıtmıyor" diye okudu
# (ROADMAP WP2-D · EDG-2026-036:175-178).
#
# SIRA ZORUNLUYDU VE UYULDU. Bu yazar ancak `ledgerstamp.seed_boundary` sınırı EĞRİNİN SON
# NOKTASINDAN okumayı bıraktıktan SONRA yazılabilirdi (bacak-1). Aksi hâlde eklenen her nokta tohum
# sınırını bugüne taşırdı ve o günden sonraki HER canlı satır `replay_seed` damgalanırdı — köken
# defterinin aktif olarak bozulması. Çivi: tests/test_defter_kaynak_damgasi_v140.py::
# test_B_CIVI_EGRIYE_NOKTA_EKLENINCE_SINIR_DEGISMEZ.
#
# HANGİ TABANDA YAZILIR — EĞRİNİN KENDİ TABANINDA, KİTABINKİNDE DEĞİL. `sermaye.uygula` kitabı yeni
# bir tabana taşır (canlı çağ 100.000$'dan başlar) ama eğri noktalarını SİLMEZ; kırılma `ofset`
# olarak BEYAN edilir ve `recompute`in `equity_curve_tail` kimliği eğrinin sonuna tam olarak o
# ofseti EKLEYEREK ölçer (`recompute.report` kimlik kıyasları). Ham `eq_now` yazmak iki şeyi birden bozardı:
#   (a) kimlik ofseti İKİ KEZ sayar → kalıcı kırmızı bir mutabakat satırı (kurt masalı),
#   (b) eğri, reset gününde ofset kadar SIÇRAR → hiç kazanılmamış bir günlük kâr çizilir; sermaye.py
#       :339 bu hatayı adıyla ("%5,87'lik UYDURMA bir günlük kâr") zaten uyarıyordu.
# Nokta bu yüzden `eq_now − ofset` olarak yazılır: seri TEK tabanda kalır, kimlik ölçmeye devam
# eder ve kırılma yine yalnız `reset_isaretleri` beyanında durur.
#
# AD NEDEN LİTERAL SABİT (`ledgerstamp.EQUITY` değil): sahiplik/YASA-6 tarayıcıları statiktir ve
# yalnız dizge sabitlerini çözer (test_na_revision_v53::_writes modül-içi `AD = "x.json"`
# atamalarını da izler, ama MODÜL DIŞI bir niteliği — `ledgerstamp.EQUITY` — çözemez). Niteliği
# kullanmak yazımı ortak-sahiplik taramasından ve `codelaw.artifact_graph`tan GİZLERDİ; yani
# "sessizce bir dosyanın sahibi olmama" kuralını tam da onu ölçen araçtan kaçarak çiğnerdi.
# İkiz literal `sermaye.EQUITY`/`ledgerstamp.EQUITY` ile aynı sınıftır ve çivisi vardır:
# test_wp2d_egri_kadansli_yazar_v245::test_CIVI_egri_dosya_adi_TEK.
EQUITY_CURVE = "equity_curve.json"


def _persist_equity_point(dstr: str, eq_now, meta: dict) -> dict:
    """Seans sonunda eğriye TEK nokta: `(dstr, eq_now − beyanlı ofset)`.

    İDEMPOTENT — GÜNDE TEK NOKTA. Kıyas EĞRİNİN SON NOKTASIYLA yapılır, tüm seride arama ile değil:
    koşum tekrarı/restart/elle tetik aynı güne ikinci bir satır yazamaz, aynı gün İÇİNDE değişen
    değer yerinde tazelenir (nokta SAYISI sabit kalır), ve GEÇMİŞ noktalara asla dokunulmaz. Son
    nokta bugünden İLERİDEYSE yazım REDDEDİLİR: geriye yazmak eğrinin tarihini değiştirirdi ve
    "bayat bar ile koşan bir tur" sessizce geçmişi düzeltemez.

    ÖLÇÜLEMEYEN NOKTA YAZILMAZ. `eq_now` sayıya çevrilemiyor/sonlu değilse, tarih ayrıştırılamıyorsa
    ya da beyanlı ofset okunamıyorsa SATIR YAZILMAZ ve neden hem dönüşte hem olay defterinde durur.
    Sıfır ya da bayat bir değer yazmak, eğriyi tam da onu okumak isteyen soruya (P&L nereye gitti?)
    karşı yalancı yapardı.

    YAZIM TEK KAPIDAN: `store.update_json` = `file_lock` + oku-değiştir-yaz + atomik yazım. İkinci
    bir yazım yolu icat edilmez; zarfın `points` DIŞINDAKİ anahtarları (reset işaretleri, version)
    olduğu gibi korunur — bacak-1'in sınırı tam olarak orada yaşıyor.

    DÖNÜŞ: makbuz sözlüğü (yazıldı mı, hangi değer, hangi taban, yazılmadıysa NEDEN). Döngünün
    `daily_cycle` olayına ve dönüşüne girer — YASA 6: üretilen satırın okuyucusu vardır."""
    import math
    # `durum` DÖRT HÂLİ AYIRIR ve makine-okunurdur: yazildi · tazelendi (aynı gün, değişen değer) ·
    # idempotent_atlandi (aynı gün, aynı değer — nokta ZATEN yerinde) · yazilmadi (ölçülemedi/
    # reddedildi, `neden` söyler). `yazildi` bool'u geriye uyum için durur ama ÜÇÜNCÜ HÂLİ
    # taşıyamaz: "yazmadım çünkü zaten yazılı" ile "yazamadım" aynı bayrağa düşerse pano bacağı
    # (WP2-D bacak-3) doğru cümleyi kuramaz ve `neden` metnine göre dizge eşleştirmek zorunda kalır.
    mak = {"yazildi": False, "durum": "yazilmadi", "tarih": dstr, "deger": None, "eq_now": None,
           "ofset": None, "neden": None}
    try:
        try:
            dt.date.fromisoformat(str(dstr or "")[:10])
        except ValueError:
            mak["neden"] = f"seans tarihi ayrıştırılamadı ({dstr!r}) — nokta yazılmadı"
            obs.warn("equity_point_skipped", neden=mak["neden"], date=str(dstr))
            return mak
        try:
            v = float(eq_now)
        except (TypeError, ValueError):  # sessiz-yutma: SESSİZ DEĞİL — çevrilemeyen değer NaN'a düşürülür ve bir SONRAKİ satırdaki `isfinite` kapısı onu "ölçülemedi" olarak dışarı söyler (makbuz + `equity_point_skipped` olayı); iki dalın (biçimsiz / sonsuz) tek yerde toplanması, aynı hükmü iki kez yazmayı önler
            v = float("nan")
        if not math.isfinite(v):
            mak["neden"] = f"öz sermaye ölçülemedi ({eq_now!r}) — nokta yazılmadı (sıfır YAZILMAZ)"
            obs.warn("equity_point_skipped", neden=mak["neden"], date=dstr)
            return mak
        mak["eq_now"] = round(v, 2)
        # BEYANLI TABAN. `meta` bu turun başında diskten okunan kitabın kendisidir (`_load_broker`),
        # yani ofset kitabın `sermaye_resetleri` kaydından — ikinci bir okuma ve ikinci bir "an" yok.
        try:
            from . import sermaye as _srm
            ofs = float(_srm.ofset(meta if isinstance(meta, dict) else None))
        except Exception as e:
            mak["neden"] = (f"beyanlı sermaye ofseti okunamadı ({type(e).__name__}: {e}) — nokta "
                            f"YAZILMADI: hangi tabanda yazılacağı ölçülemeyen bir nokta, eğriyi "
                            f"kimliğiyle birlikte bozar")
            obs.warn("equity_point_skipped", neden=mak["neden"], date=dstr)
            return mak
        mak["ofset"] = round(ofs, 2)
        deger = round(v - ofs, 2)
        mak["deger"] = deger
        red: dict = {}

        def _ekle(doc):
            """Bu seansın noktasını özsermaye eğrisine ekler ya da aynı günün noktasını YERİNDE tazeler.

            ÜÇ RET: kuyruk ayrıştırılamıyorsa, son nokta bu seanstan İLERİDEYSE (geriye yazım) ve
            aynı gün-aynı değerse hiçbir bayt yazılmaz; neden `red` sözlüğüne bırakılır."""
            pts = (doc or {}).setdefault("points", [])
            son = pts[-1] if pts else None
            son_t = None
            if isinstance(son, (list, tuple)) and son:
                son_t = str(son[0])[:10]
            if son is not None and son_t is None:
                red["neden"] = ("eğrinin son noktası ayrıştırılamadı — nokta yazılmadı (bozuk bir "
                                "kuyruğun üstüne yazmak seriyi sessizce iki parçaya bölerdi)")
                return False
            if son_t is not None and son_t > str(dstr)[:10]:
                red["neden"] = (f"eğrinin son noktası {son_t}, seans {dstr} — GERİYE yazım "
                                f"reddedildi (eğrinin tarihi değiştirilmez)")
                return False
            if son_t == str(dstr)[:10]:
                try:
                    ayni = abs(float(son[1]) - deger) < 0.005
                except (TypeError, ValueError, IndexError):  # sessiz-yutma: aynı günün mevcut noktası okunamadı — "değişmedi" DİYEMEYİZ, o yüzden `ayni=False` ile nokta TAZELENİR (bozuk değer ölçülmüş bir değerle değişir); sessiz olan hâl, okunamayan bir değeri "aynı" sayıp yazımı atlamak olurdu
                    ayni = False
                if ayni:
                    red["ayni"] = True
                    return False                     # aynı gün, aynı değer → tek bayt yazılmaz
                pts[-1] = [str(dstr)[:10], deger]    # aynı gün → YERİNDE tazelenir (nokta SAYISI sabit)
                red["tazelendi"] = True
                return True
            pts.append([str(dstr)[:10], deger])
            return True

        store.update_json(EQUITY_CURVE, _ekle, {"points": []})
        if red.get("neden"):
            mak["neden"] = red["neden"]
            obs.warn("equity_point_skipped", neden=mak["neden"], date=dstr, deger=deger)
            return mak
        if red.get("ayni"):
            mak["neden"] = "aynı gün aynı değer zaten yazılı — idempotent atlama"
            mak["yazildi"], mak["durum"] = False, "idempotent_atlandi"
            return mak
        mak["yazildi"] = True
        mak["tazelendi"] = bool(red.get("tazelendi"))
        mak["durum"] = "tazelendi" if mak["tazelendi"] else "yazildi"
        return mak
    except Exception as e:  # sessiz-yutma: eğri yazımı ÖLÇÜM katmanıdır ve canlı kararı/kapanışı rehin alamaz; düşüş adıyla olay defterine geçer ve makbuz `yazildi: False` + neden ile döner (uydurma nokta YOK)
        mak["neden"] = f"{type(e).__name__}: {e}"
        obs.warn("equity_point_failed", error=mak["neden"], date=str(dstr),
                 detail="sermaye eğrisine kadanslı nokta yazılamadı — döngü ETKİLENMEDİ")
        return mak


def _trail_patch_alarm(sym: str, res: dict, frm: float, to: float) -> None:
    """Faz 0: iç HWM yükseldi ama broker PATCH'i reddetti → iç stop ile Alpaca stopu AYRIŞTI.
    Eski kod bunu yalnız logluyordu; ayrışma bir sonraki reconcile'a dek görünmezdi. Artık alarm."""
    if not res.get("ok"):
        obs.alarm(obs.ALARM_TRAIL_DESYNC,
                  f"trail PATCH reddedildi: {sym} {frm}→{to}",
                  ticker=sym, from_stop=frm, to_stop=to, detail=str(res.get("detail", ""))[:200])


def _entry_fill_price(order: dict) -> float | None:
    """Bir emrin KENDİ dolum fiyatı (`filled_avg_price`). İki tüketici, tek hüküm: (a) bracket
    PARENT'ının GİRİŞ dolumu — `exit_fill_price`in ikizi: o BACAKLARA bakar (çıkış), bu emrin
    kendisine; (b) karar kapatma emri (`DELETE /positions`ın doğurduğu market SELL) — o da düz bir
    emirdir, dolumu kendi gövdesindedir. `partially_filled` de gerçek bir `filled_avg_price`
    taşır ve atlanırsa slipaj ölçümü tam icra karıştığında sessizce boşalır (denetim #54'ün dersi)."""
    if not isinstance(order, dict):
        return None
    if str(order.get("status", "")).lower() not in ("filled", "partially_filled"):
        return None
    v = order.get("filled_avg_price")
    if v in (None, ""):
        return None
    try:
        return float(v)
    except (TypeError, ValueError):  # sessiz-yutma: biçimsiz tek alan; satır `fill: None` ile kalır ve payda sayacında görünür
        return None


def _patch_entry_slippage(by_coid: dict, opens: dict | None, dstr: str) -> dict:
    """E2 — SLİPAJ DEFTERİNİN DOLUM YARISI. Aynadaki GİRİŞ emri dolduğunda ilgili satıra iki bps
    yazılır ve satır bir daha yazılmaz (idempotent: `fill` doluysa atlanır).

      * `fill_vs_resmi_acilis_bps` — ödediğimiz fiyat, o seansın RESMÎ AÇILIŞINA göre. Açılış
        mikroyapısının faturası tam olarak budur (E3 bandının ampirik girdisi).
      * `fill_vs_limit_bps`        — ödediğimiz fiyat, yasanın tavanına göre. Negatif = tavanın
        altında doldu (yasa para bıraktı), 0'a yakın = tavanda dolduk (limit BAĞLADI).

    Resmî açılış yoksa (bar gelmemiş) o bps None kalır — açılışı dolum fiyatıyla ikame etmek,
    ölçmek istediğimiz farkı tanımı gereği sıfır yapardı.

    KISMİ DOLUM DONMAZ (B5a, teşhis 2026-08-10): eski idempotens `fill is not None` idi — ilk
    fotoğraf `partially_filled` ise satır o anda DONUYORDU; GTC kalanı sonraki seans(lar)da dolmaya
    devam ettiğinde (fill_qty/ortalama değişir) satır asla güncellenmiyordu. Artık yalnız TERMİNAL
    satır donar: `fill_status=partially_filled` satırlar emir terminal olana dek her tur tazelenir
    (idempotens korunur: değişmemiş kısmi satır yeniden yazılmaz). Kısmi-dolmuş emir sonradan
    süpürülür/iptal olursa (`canceled` + filled_qty>0) o da bir SONdur: ortalama fiyat son kez
    yazılır ve satır gerçek statüsüyle donar."""
    out = {"eslesen": 0, "yazilan": 0, "acilis_yok": 0, "kismi_tazelenen": 0}
    # KİLİT: read_jsonl → (değiştir) → write_jsonl TEK kritik bölge, hepsi
    # `file_lock(ENTRY_LEDGER)` altında. Eskiden read KİLİTSİZdi ve write kendi kilidini AYRI
    # alıyordu; ikisinin arasına aynı deftere düşen bir append/patch, write tüm defteri yeniden
    # yazınca EZİLİYORDU (kayıp-güncelleme). `write_jsonl`in mkstemp+os.replace'i ATOMİKLİK verir
    # (yarım/boş dosya yok) ama oku-değiştir-yaz'ı SERİALİZE ETMEZ — eski "atomik" yorumu yanlışlıkla
    # ikincisini ima ediyordu; iki AYRI garanti, kayıp-güncelleme kapısı kilittir.
    with store.file_lock(ENTRY_LEDGER):
        try:
            rows = store.read_jsonl(ENTRY_LEDGER)
        except Exception as e:
            obs.warn("entry_exec_ledger_read_failed", error=f"{type(e).__name__}: {e}")
            return out
        changed = False
        for r in rows:
            if r.get("motor") != "ayna":
                continue
            kismi = (r.get("fill") is not None
                     and str(r.get("fill_status") or "") == "partially_filled")
            if r.get("fill") is not None and not kismi:
                continue                       # TERMİNAL satır donuk (idempotens korunur)
            o = by_coid.get(r.get("plan_id"))
            af = _entry_fill_price(o) if o else None
            if af is None and kismi and isinstance(o, dict):
                # B5a son-durum dalı: kısmi-dolmuş emir sonradan iptal/süpürülmüş (`canceled` +
                # filled_qty>0). `_entry_fill_price` ölü statüde fiyat vermez (giriş yamasında
                # doğru davranış) ama burada dolum GERÇEKLEŞMİŞ ve fiyatı gövdede duruyor —
                # okunur, satır gerçek statüsüyle DONDURULUR. Okunamazsa satır kısmi kalır (uydurma yok).
                try:
                    ham = o.get("filled_avg_price")
                    af = float(ham) if ham not in (None, "") else None
                except (TypeError, ValueError):  # sessiz-yutma: biçimsiz tek alan; satır kısmi kalır ve sonraki tur yeniden denenir
                    af = None
            if af is None:
                continue
            if kismi:
                eski = (r.get("fill"), r.get("fill_qty"), r.get("fill_status"))
                yeni = (round(af, 4), o.get("filled_qty"), str(o.get("status", "")).lower())
                if eski == yeni:
                    continue                   # kısmi ama DEĞİŞMEMİŞ — defter boşuna yazılmaz
                out["kismi_tazelenen"] += 1
            else:
                out["eslesen"] += 1
            op = (opens or {}).get(r.get("ticker"))
            if op is None:
                op = r.get("resmi_acilis")
            if op is None:
                out["acilis_yok"] += 1
            r["fill"] = round(af, 4)
            r["fill_qty"] = o.get("filled_qty")
            r["fill_status"] = str(o.get("status", "")).lower()
            r["resmi_acilis"] = (round(float(op), 4) if op is not None else None)
            r["fill_vs_resmi_acilis_bps"] = _bps(af, op)
            r["fill_vs_limit_bps"] = _bps(af, r.get("limit"))
            r["fill_kaydedildi"] = dstr
            changed = True
            out["yazilan"] += 1
        if changed:
            try:
                store.write_jsonl(ENTRY_LEDGER, rows)   # kilit altında — oku-değiştir-yaz serialize
            except Exception as e:
                obs.warn("entry_exec_ledger_patch_failed", error=f"{type(e).__name__}: {e}")
    return out


# =============================================================================================
# MIRROR_DRIFT SAPMA SINIFI (`drift_sinifi`)
# =============================================================================================
# VAKA (docs/BAYAT-SERMAYE-KOK-2026-08-07.md): 08-05 gecesi DÖRT MIRROR_DRIFT alarmı bastı,
# dördü de ADET sapması dedi (54 vs 25 …) ve HİÇBİRİ sebebi ADLANDIRMADI — belirti (%49 sapma)
# görüldü, SINIF söylenmedi. Gerçek kök: gönderim anında kitabın boyut tabanı 94.457,91$, dolum
# anında 100.000$ (bayat sermaye). Bu yardımcı, adet sapmasını boyut makbuzuyla
# (`meta["size_law"]` — GÖNDERİM anının girdileri) DOLUM anının girdilerine kıyaslayıp
# sapmayı ADLANDIRIR. ALARMIN KENDİSİ/EŞİĞİ (>%25) DEĞİŞMEZ — yalnız SEBEP alanı eklenir.
# Türetilemeyen sınıf UYDURULMAZ: `olculemedi` + neden (0/boş DEĞİL — YASA: UYDURMA YASAĞI).
_DRIFT_EPS_EQ   = 1.0        # eq_now farkı: makbuz 2 ondalığa yuvarlı — $1 altı yuvarlama gürültüsü
_DRIFT_EPS_MULT = 1e-3       # size_mult farkı: makbuz 4 ondalığa yuvarlı
_DRIFT_SEANS_S  = 24 * 3600  # "nabız yaşı > 1 seans" eşiği (sermaye_kaynagi korroborasyonu)


def _drift_sinifi_adet(receipt: dict | None, fill_eq_now, fill_peak,
                       dolum_taze: bool | None = None) -> tuple[str, str]:
    """ADET sapmasının (`reconcile_broker_state` 1.2b) SEBEP SINIFINI türet — sapma sınıfı tablosu.

    Girdi: `receipt` = boyut makbuzu (`meta["size_law"][plan_id]`, GÖNDERİM anının girdileri:
    eq_kaynak/eq_now/peak/size_mult/kitap_rev; dolum-anı damgasından beri iç dolum anında `dolum_eq`/`dolum_peak`
    İKİNCİ YARISI damgalanır) · `fill_eq_now`/`fill_peak` = BU TURUN açılış girdileri ·
    `dolum_taze` = pozisyon BU seansta mı doldu (`ts_open == dstr`; None = yaş okunamadı).
    Sınıf, iki bacağın SEBEBİNİ ayırt ETTİĞİ kadar kesindir; ayırt edilemiyorsa `olculemedi` —
    0/boş DEĞİL, ADI OLAN üçüncü hâl (UYDURMA YASAĞI).

    ANAKRONİZM (fill_eq_now, teşhis 2026-08-10): `fill_eq_now` DOLUM anının değil BU TURUN
    tabanıdır — yalnız pozisyon bu seansta dolduysa ikisi aynı şeydir. Yaşlı pozisyonda kıyasın sağ
    bacağı makbuzun `dolum_eq` damgasıdır; damga da yoksa kıyas YAPILMAZ (`olculemedi` + neden) —
    "gönderim eq X ≠ dolum eq Y" cümlesindeki Y'nin bugünün sayısı olması sebep UYDURMAKTI.

    Sıra NEDENLİdir (ilk eşleşen kazanır):
      makbuzsuz_boyut         — boyut makbuzu YOK (restart-öncesi / makbuzsuz gönderim): boyut
                                kararının girdileri kayıtsız. `olculemedi`nin ADLI alt-hâli —
                                2026-08-12 forensiği: eski pozisyon sapmalarının
                                tamamı bu addır, jenerik `olculemedi` teşhisi gizliyordu.
      olculemedi(dolum yok)   — reconcile eq_now'suz çağrıldı (eski çağıran): kıyas yapılamaz.
      olculemedi(anakronizm)  — pozisyon BU seansta dolmadı ve makbuzda `dolum_eq` damgası yok:
                                dolum-anı tabanı bilinmiyor, bugünün tabanıyla kıyas YAPILMAZ.
      sermaye_kaynagi         — makbuz eq_kaynak=nabiz VE nabız yaşı>1 seans: boyut PAYINI bayat
                                nabızdan aldı (kitap değil) — KANAL-özgü kök, generic tabandan ÖNCE.
      boyutlama_tabani        — çarpan iki bacakta farklı VE makbuz eq_now ≠ dolum eq: boyut
                                tabanı gönderim↔dolum arasında kaydı (canlı vaka: 94457,91 vs 100000).
      derisk_carpani          — çarpan farklı ama eq ~aynı: de-risk eşiği/kartı arada değişti.
      kitap_kaydi             — çarpan aynı ama makbuz kitap_rev ≠ dolum rev: kitap arada DEĞİŞTİ.
      olculemedi(beyan/icra)  — tüm ölçülebilir girdiler eşit: kalan fark icra (limit/slipaj/kısmi)
                                VEYA beyan_kaydi — makbuz beyan_n/ofset TAŞIMADIĞINDAN ayrılamaz
                                (makbuz genişletme AYRI kalem).
    KISMİ DOLUM bu tabloda DEĞİL: onun kanıtı makbuz değil EMRİN KENDİSİdir (filled_qty<qty) ve
    çağıran (1.2b) `_kismi_dolum_tespiti` ile bu fonksiyona hiç gelmeden sınıflar."""
    if not receipt:
        return "makbuzsuz_boyut", ("plan için SB-1 boyut makbuzu (size_law) yok — restart-öncesi "
                                   "ya da makbuzsuz gönderim; boyut kararının girdileri kayıtsız, "
                                   "gönderim↔dolum kıyası kurulamaz (ROADMAP Ö-7, 2026-08-12 "
                                   "forensiği: 'olculemedi'nin adlı alt-hâli)")
    # kıyasın SAĞ bacağı (dolum-anı tabanı) üç kaynaktan, güven sırasıyla:
    #   1. makbuz `dolum_eq` damgası (iç dolum anında basıldı — yaşdan bağımsız doğru taban),
    #   2. `fill_eq_now`, YALNIZ pozisyon bu seansta dolduysa (bu turun açılış tabanı = dolum tabanı),
    #   3. yoksa kıyas YOK — bugünün sayısını dolum tabanı diye kullanmak sebep uydurmaktı.
    _d_eq = receipt.get("dolum_eq")
    if _d_eq is not None:
        taban, taban_peak = _d_eq, receipt.get("dolum_peak", fill_peak)
    elif fill_eq_now is None:
        return "olculemedi", ("dolum-anı eq_now geçilmedi (reconcile eq_now'suz çağrıldı) — "
                              "makbuzla kıyas yapılamadı")
    elif dolum_taze is True:
        taban, taban_peak = fill_eq_now, fill_peak
    else:
        return "olculemedi", ("dolum-anı sermaye tabanı bilinmiyor: makbuzda `dolum_eq` damgası yok"
                              + (" ve pozisyonun ts_open'ı okunamadı" if dolum_taze is None
                                 else " ve pozisyon bu seansta dolmadı")
                              + " — BUGÜNÜN eq_now'u ile kıyas anakronizm olurdu (B6); kıyas YAPILMADI")
    r_eqk, r_eqn = receipt.get("eq_kaynak"), receipt.get("eq_now")
    r_mult, r_rev = receipt.get("size_mult"), receipt.get("kitap_rev")
    try:
        f_eqn  = float(taban)
        f_peak = float(taban_peak) if taban_peak is not None else START_EQUITY
        f_mult = derisk_mult(f_eqn, f_peak)
    except (TypeError, ValueError):  # sessiz-yutma: dolum-anı eq/peak sayı DEĞİL (biçimsiz/None) — çarpan yeniden üretilemez; hüküm UYDURULMAZ, `olculemedi`ye düşer (dönüşteki neden bunu söyler)
        return "olculemedi", "dolum-anı eq/peak sayıya çevrilemedi — çarpan yeniden üretilemedi"
    # sermaye_kaynagi: nabız KANALI + bayatlık. KANAL-özgü kök, generic taban kıyasından ÖNCE gelir
    # (canlı AMGN bacağı: pano dalı `eq_now` almaz, boyutu bayat nabızdan okur).
    if r_eqk == "nabiz":
        age = health.heartbeat_age_seconds()
        if age is not None and age > _DRIFT_SEANS_S:
            return "sermaye_kaynagi", (f"makbuz eq_kaynak=nabiz ve nabız yaşı {age/3600:.1f} sa "
                                       f"(>1 seans) — boyut PAYINI bayat nabızdan aldı, kitaptan değil")
    # boyutlama_tabani / derisk_carpani: çarpan iki bacakta farklı mı? (asıl sizing kolu)
    if r_mult is not None and abs(float(r_mult) - f_mult) > _DRIFT_EPS_MULT:
        if r_eqn is not None and abs(float(r_eqn) - f_eqn) > _DRIFT_EPS_EQ:
            return "boyutlama_tabani", (f"gönderim eq_now {float(r_eqn):g}$ ≠ dolum eq_now {f_eqn:g}$ "
                                        f"→ çarpan {float(r_mult):g}→{f_mult:g}; boyut tabanı "
                                        f"gönderim↔dolum arasında kaydı")
        return "derisk_carpani", (f"çarpan iki bacakta farklı ({float(r_mult):g} vs {f_mult:g}) ama "
                                  f"eq_now ~aynı — de-risk eşiği/kartı gönderim↔dolum arasında değişti")
    # kitap_kaydi: çarpan aynı ama kitap arada değişti mi? (boyut tabanı kaymadan içerik oynadı)
    if r_rev is not None:
        try:
            f_rev = (store.stamp(PORTFOLIO) or (None, None))[1]
        except Exception:  # sessiz-yutma: rev damgası okunamadı — kitap_kaydi ayrımı düşer, hüküm son dala geçer (uydurma yok)
            f_rev = None
        if f_rev is not None and r_rev != f_rev:
            return "kitap_kaydi", (f"makbuz kitap_rev {r_rev} ≠ dolum-anı rev {f_rev} — kitap "
                                   f"gönderim↔dolum arasında DEĞİŞTİ (boyut tabanı kaymadı)")
    # tüm ölçülebilir girdiler eşit → icra VEYA beyan_kaydi; makbuz beyanı ölçmez → olculemedi
    return "olculemedi", ("eq_now/size_mult/kitap_rev eşit; kalan fark icra (limit/slipaj/kısmi "
                          "dolum) VEYA beyan_kaydi olabilir — size_law makbuzu beyan_n/ofset "
                          "taşımadığından ayrım YAPILAMADI (SB-1 makbuz genişletme AYRI kalem)")


def _kismi_dolum_tespiti(order) -> tuple[str, str] | None:
    """KISMİ DOLUM TESPİTİ (teşhis 2026-08-10): adet sapmasının DOĞRUDAN kanıtı — giriş emri KISMÎ mi doldu?

    Sapma sınıfı tablosunda `kismi_dolum` diye bir sınıf YOKTU; kısmi dolum ancak `olculemedi` gerekçe
    METNİNDE geçiyor, eq/çarpan kıyası tesadüfen tutarsa sapma yanlışlıkla boyutlama sınıflarına
    yazılıyordu. Kanıt makbuz kıyası değil EMRİN KENDİSİdir: `filled_qty < qty` (ya da statü
    `partially_filled`) ise ayna adedi tanım gereği eksiktir — makbuz heuristiğinden ÖNCE gelir.
    NOT: 08-06 dört-pozisyon vakası kısmi dolum ÇIKMADI (emirler tam dolmuştu, fark boyutlamaydı) —
    sınıf GELECEK vakalar için var; tespit ölçülemiyorsa None döner ve hüküm sapma sınıfı tablosuna kalır."""
    if not isinstance(order, dict):
        return None
    try:
        istenen = float(order.get("qty") or 0.0)
    except (TypeError, ValueError):  # sessiz-yutma: biçimsiz tek alan; kanıt kurulamaz, hüküm sapma sınıfı tablosuna düşer (uydurma sınıf yok)
        istenen = 0.0
    try:
        dolan = float(order.get("filled_qty") or 0.0)
    except (TypeError, ValueError):  # sessiz-yutma: biçimsiz tek alan; kanıt kurulamaz, hüküm sapma sınıfı tablosuna düşer (uydurma sınıf yok)
        return None
    st = str(order.get("status", "")).lower()
    if st == "partially_filled" or (istenen > 0 and 0 < dolan < istenen - 1e-9):
        return "kismi_dolum", (f"giriş emri KISMÎ doldu: {dolan:g}/{istenen:g} adet "
                               f"(status={st or '?'}) — ayna adedi bu yüzden eksik; boyutlama "
                               f"kıyası değil icra olgusu (B5)")
    return None


# ==================================================================================================
# EMİR PENCERESİ — SAYFALI ÇEKİM (B7a, teşhis docs/TESHIS-WPE-AYNA-DOLUM-2026-08-10.md)
# ==================================================================================================
# BULGU: `orders(status="all", limit=200)` sayfasızdı — 200 üst-düzey emri aşan bir boşlukta (uzun
# kesinti + yoğun trafik) daha eski dolumlar `by_coid`e hiç girmiyor, E2 satırı sonsuza dek
# `fill=None` kalıyor ve "dolmadı" diye OKUNUYORDU (pencere-dışılık ile dolmamışlık ayırt edilemez).
# ÇÖZÜM: geriye doğru `until=<önceki sayfanın en eski submitted_at'i>` ile sayfalanır; HEDEF, hâlâ
# dolum bekleyen en eski kaydın tarihidir (E2 `fill=None`/kısmi satırlar + çıkış-yaması kuyruğu).
# Kapsanamazsa (sayfa tavanı) bu SESSİZ DEĞİL: `kapsandi=False` panoya yazılır + olay düşer —
# "pencere-dışı, hüküm yok" beyanı (dolmadı SANILMAZ).
_EMIR_PENCERESI_SAYFA_TAVANI = 5      # 5 × 200 = 1000 emir; tavan aşımı beyanlıdır, sessiz değil


_EMIR_PENCERESI_UFUK_GUN = 14   # E2 hedef ufku (takvim günü) — gerekçe fonksiyon docstring'inde


def _emir_penceresi_hedefi(meta: dict, dstr: str) -> str | None:
    """Pencerenin GERİYE dek uzanması gereken tarih: dolum bekleyen en eski kayıt. Kaynaklar:
    E2 defterinin `fill=None` ya da kısmi (`partially_filled`) ayna satırları + çıkış dolum-yaması
    kuyruğunun `since` tarihleri. Hiç bekleyen yoksa None → tek sayfa yeter (bugünkü davranış).

    UFUK (bilinçli): E2'de `fill=None` iki ayrı olguyu kapsar — "henüz dolmadı" VE "hiç dolmadı"
    (dolmama_orani'nın MEŞRU paydası; kaçan giriş sonsuza dek fill=None kalır). İkincisi hedefe
    alınsaydı pencere her tur en eski kaçan girişe dek sayfalanır, tavana çarpar ve her gün sahte
    'kapsanamadı' olayı basardı (alarm hijyeni). Giriş emri E1'de TIF=DAY, GTC kalıntısı da akşam
    süpürülür — ufuktan (14 gün) yaşlı bir ayna girişinin hâlâ dolabilir olması yapısal olarak
    mümkün değil; ufuk dışı satır 'dolmadı' sınıfının kendisidir, pencere borcu değil."""
    tarihler: list = []
    try:
        esik = (dt.date.fromisoformat(str(dstr))
                - dt.timedelta(days=_EMIR_PENCERESI_UFUK_GUN)).isoformat()
    except ValueError:  # sessiz-yutma: dstr tarih olarak okunamadı -> ufuk süzgeci devre dışı kalır (dar değil GENİŞ davranış: hiçbir hedef elenmez); hata yutulmuyor, boş eşik aşağıda tüm satırları hedefe alır
        esik = ""
    try:
        for r in store.read_jsonl(ENTRY_LEDGER):
            if r.get("motor") != "ayna" or r.get("karar") != "submitted":
                continue
            if r.get("fill") is None or str(r.get("fill_status") or "") == "partially_filled":
                d0 = str(r.get("date") or "")
                if d0 and d0 >= esik:
                    tarihler.append(d0)
    except Exception as e:
        obs.warn("emir_penceresi_hedef_okunamadi", error=f"{type(e).__name__}: {e}",
                 detail="E2 defteri okunamadı — pencere hedefi yalnız çıkış kuyruğundan kuruldu")
    for v in (meta.get(EXIT_FILL_KEY) or {}).values():
        if v.get("since"):
            tarihler.append(str(v["since"]))
    return min(tarihler) if tarihler else None


def _alpaca_emir_penceresi(alpaca_mod, hedef: str | None) -> tuple[list, dict]:
    """Emir listesini SAYFALI çek (en yeniden geriye). Dönüş: (emirler, pencere_özeti).

    İlk sayfanın taşıma arızası ESKİ davranışla bire bir yukarı fırlar (çağıranın arıza dalı);
    SONRAKİ sayfaların arızası eldekini düşürmez — toplanan pencere `kapsandi=False` + nedenle
    döner (yarım pencere, tam pencere GİBİ konuşamaz)."""
    pencere = {"sayfa": 0, "n_emir": 0, "kapsandi": True, "en_eski": None, "hedef": hedef,
               "neden": None}
    toplam: list = []
    gorulen: set = set()
    until = None
    while True:
        pencere["sayfa"] += 1
        # `until` YALNIZ 2. sayfadan itibaren geçilir: ilk sayfa çağrısı eski tek-sayfa çağrının
        # imzasıyla BİREBİR aynı kalır (geriye uyum — eski saplamalar/sarmalayıcılar kırılmaz).
        kw = {"status": "all", "limit": 200, "nested": True}
        if until:
            kw["until"] = until
        sayfa = alpaca_mod.orders(**kw)
        if not alpaca_mod.transport()["ok"]:
            if pencere["sayfa"] == 1:
                raise RuntimeError(alpaca_mod.transport().get("error") or "alpaca transport down")
            pencere.update({"kapsandi": False,
                            "neden": f"sayfa {pencere['sayfa']} okunamadı (taşıma arızası) — "
                                     f"pencere yarım, hedefe varılamadı"})
            break
        yeni = [o for o in (sayfa or []) if str(o.get("id") or id(o)) not in gorulen]
        gorulen |= {str(o.get("id") or id(o)) for o in yeni}
        toplam.extend(yeni)
        damgalar = [str(o.get("submitted_at") or "") for o in (sayfa or []) if o.get("submitted_at")]
        en_eski = min(damgalar) if damgalar else None
        if en_eski:
            pencere["en_eski"] = en_eski[:10]
        if len(sayfa or []) < 200:
            break                                  # tarihçenin sonu — pencere tam
        if hedef is None:
            break                                  # bekleyen yok: tek sayfa yeter (eski davranış)
        if en_eski is None:
            pencere.update({"kapsandi": False,
                            "neden": "sayfada submitted_at okunamadı — geriye sayfalanamaz"})
            break
        if en_eski[:10] < str(hedef):
            break                                  # hedef tarihten eskisine ulaşıldı — kapsandı
        if pencere["sayfa"] >= _EMIR_PENCERESI_SAYFA_TAVANI:
            pencere.update({"kapsandi": False,
                            "neden": f"sayfa tavanı ({_EMIR_PENCERESI_SAYFA_TAVANI}×200) aşıldı — "
                                     f"hedef {hedef} pencereye alınamadı"})
            break
        until = en_eski
    pencere["n_emir"] = len(toplam)
    if not pencere["kapsandi"]:
        # YASA-4: pencere-dışılık ile dolmamışlık AYNI ŞEY DEĞİL — beyan olayla düşer; E2/yama
        # okumaları bu turda pencere-dışı satırlar için HÜKÜM VERMEZ (dolmadı sanılmaz).
        obs.warn("reconcile_emir_penceresi_asilamadi", hedef=hedef, en_eski=pencere["en_eski"],
                 sayfa=pencere["sayfa"], n_emir=pencere["n_emir"], neden=pencere["neden"],
                 detail="dolum bekleyen en eski kayıt emir penceresine sığmadı — pencere-dışı "
                        "satırlar için hüküm YOK (fill=None 'dolmadı' diye okunmasın, B7a)")
    return toplam, pencere


# ==================================================================================================
# ÇIKIŞ DOLUM-YAMASI İŞLEME — kuyruk her reconcile turunda denenir, vazgeçiş OLAYLI
# ==================================================================================================
def _exit_fill_yamasi(meta: dict, by_coid: dict, by_id: dict, dstr: str, out: dict,
                      alpaca_mod) -> None:
    """Kuyruktaki her kapanışın AYNA dolum fiyatını ara ve trades satırına yamala.

    İki okuma yolu (kayıttaki `kaynak`):
      * "karar" — `close_order_id`li market emri; önce bu turun penceresinden (`by_id`),
        yoksa kimlikle tekil GET (`alpaca.order_by_id` — pencere boşluğundan bağımsız).
      * "bacak" — parent bracket'ın dolan TP/SL bacağı (`alpaca.exit_fill_price`).
    Bulunursa: kilitli yama `alpaca_fill_price + mirror_divergence` (+eşik aşımında `icra` sınıflı
    MIRROR_DRIFT — eski 1.3 ile aynı eşik/alarm) ve kuyruktan düşer. Bulunamazsa `tries` artar;
    `EXIT_FILL_MAX_TRIES` turda VAZGEÇİŞ: olay + satıra dürüst `alpaca_fill_beyan` (fiyat
    UYDURULMAZ — None + neden; `alpaca_fill_price` anahtarı AÇILMAZ ki geç gelen gerçek dolum
    hâlâ yamanabilsin). Kilit penceresi ağ çağrılarını KAPSAMAZ (eski 1.3 yasası)."""
    pend = dict(meta.get(EXIT_FILL_KEY) or {})
    out["exit_fill"] = {"bekleyen": 0, "yamalanan": 0, "vazgecilen": 0}
    if not pend:
        return
    trades = store.read_jsonl("trades.jsonl")
    son: dict = {}
    for i, t in enumerate(trades):
        if t.get("plan_id") in pend:
            son[t["plan_id"]] = i                  # plan başına EN YENİ satır
    yamalar: dict = {}
    beyanlar: dict = {}
    kalan: dict = {}
    for pid, info in pend.items():
        info = dict(info or {})
        info["tries"] = int(info.get("tries") or 0) + 1
        i = son.get(pid)
        if i is None:
            obs.warn("exit_fill_patch_satirsiz", plan_id=pid, ticker=info.get("ticker"),
                     detail="trades.jsonl'da bu plan_id'li satır yok (trim/eski defter?) — "
                            "yamalanacak yer yok, kayıt kuyruğundan düşürüldü")
            continue
        row = trades[i]
        if row.get("alpaca_fill_price") is not None:
            continue                               # zaten yamalı (ör. koruma_dolumu satırı) — düş
        af, af_neden = None, None
        if info.get("kaynak") == "karar":
            oid = info.get("order_id")
            if oid:
                o = by_id.get(str(oid)) or alpaca_mod.order_by_id(str(oid))
                af = _entry_fill_price(o) if o else None
                if af is None:
                    af_neden = (f"kapatma emri {str(oid)[:20]}… bu tur okunamadı/dolum fiyatı yok "
                                f"(status={str((o or {}).get('status') or 'okunamadı')})")
            else:
                af_neden = ("kapatma emrinin kimliği yok — "
                            + str(info.get("order_id_neden") or "DELETE cevabı kimlik taşımadı"))
        else:
            o = by_coid.get(pid)
            af = alpaca_mod.exit_fill_price(o) if o else None
            if af is None:
                af_neden = ("parent emir pencerede yok" if o is None
                            else "bracket bacağında dolum fiyatı yok (bacak henüz dolmadı / iptal)")
        if af is not None:
            sim = float(row.get("exit") or 0.0)
            div = abs(af - sim) / sim if sim else 0.0
            yamalar[pid] = {"alpaca_fill_price": round(af, 4), "mirror_divergence": round(div, 5)}
            out["exit_fill"]["yamalanan"] += 1
            obs.log("mirror_exit_fill_patched", plan_id=pid, ticker=info.get("ticker"),
                    kaynak=info.get("kaynak"), reason=info.get("reason"), tries=info["tries"],
                    alpaca_fill=round(af, 4), sim=round(sim, 4), divergence=round(div, 5),
                    detail="kapanan işlemin GERÇEK ayna dolumu satıra yamalandı (B1/B2)")
            if div > MIRROR_DRIFT_TOL:
                # SABİT sapma sınıfı `icra` — eski 1.3 ile AYNI eşik, AYNI alarm (davranış korunur).
                out["drift"].append({"ticker": info.get("ticker"), "sim": round(sim, 4),
                                     "alpaca": round(af, 4), "div_pct": round(div * 100, 3),
                                     "drift_sinifi": "icra"})
                obs.alarm(obs.ALARM_MIRROR_DRIFT,
                          f"ayna sapması: {info.get('ticker')} — sim {round(sim, 4)} vs Alpaca "
                          f"{round(af, 4)} (%{div*100:.2f})",
                          ticker=info.get("ticker"), sim=round(sim, 4), alpaca_fill=round(af, 4),
                          divergence=round(div, 4), drift_sinifi="icra")
            continue
        if info["tries"] >= EXIT_FILL_MAX_TRIES:
            beyan = (f"ÖLÇÜLEMEDİ: ayna çıkış dolum fiyatı {info['tries']} reconcile turunda "
                     f"okunamadı — {af_neden}; fiyat UYDURULMADI (None + bu neden)")
            beyanlar[pid] = beyan
            out["exit_fill"]["vazgecilen"] += 1
            obs.warn("mirror_exit_fill_vazgecildi", plan_id=pid, ticker=info.get("ticker"),
                     kaynak=info.get("kaynak"), tries=info["tries"], neden=af_neden,
                     detail="çıkış dolum-yaması vazgeçişle kapandı — satıra dürüst beyan yazıldı; "
                            "`alpaca_fill_price` anahtarı açılmadı (geç gelen gerçek dolum hâlâ "
                            "yamanabilir)")
            continue
        info["son_neden"] = str(af_neden or "")[:160]
        kalan[pid] = info
    meta[EXIT_FILL_KEY] = kalan
    out["exit_fill"]["bekleyen"] = len(kalan)
    if yamalar or beyanlar:
        def _yama(rows, _y=yamalar, _b=beyanlar):
            """İşlem defterine ayna çıkış dolumlarını (ölçüm) ya da beyanlarını işler.

            Plan başına EN YENİ satır hedeflenir ve yalnız `alpaca_fill_price` HÂLÂ boşsa yazılır;
            gerçek ölçüm gelince eski beyan kalkar. Ölçüm varken beyan yazılmaz."""
            hedefte: dict = {}
            for _i, _t in enumerate(rows):         # plan başına EN YENİ satır (yeniden okunur)
                if _t.get("plan_id") in _y or _t.get("plan_id") in _b:
                    hedefte[_t["plan_id"]] = _i
            hit = False
            for _pid, _i in hedefte.items():
                if _pid in _y and rows[_i].get("alpaca_fill_price") is None:
                    rows[_i].update(_y[_pid])
                    rows[_i].pop("alpaca_fill_beyan", None)   # ölçüm geldi — eski beyan kalkar
                    hit = True
                elif _pid in _b and rows[_i].get("alpaca_fill_price") is None \
                        and not rows[_i].get("alpaca_fill_beyan"):
                    rows[_i]["alpaca_fill_beyan"] = _b[_pid]
                    hit = True
            return hit

        store.update_jsonl("trades.jsonl", _yama)  # kilitli oku-değiştir-yaz (telemetri)


# ==================================================================================================
# KORUMA-OCO DOLUMU → KİTAP KAPANIŞI (teşhis docs/TESHIS-WPE-AYNA-DOLUM-2026-08-10.md)
# ==================================================================================================
# BULGU: koruma OCO'sunun (coid `P-KORUMA-…`) bir bacağı DOLUNCA pozisyon aynada gerçekten
# kapanıyor; ama mutabakat yalnız `by_coid[plan_id]` ile eşleştiğinden bu dolumu göremiyor, sembolü
# her tur YANLIŞ sınıfla (`split_brain`) alarmlıyor ve kapanış hiçbir deftere işlenmiyordu — iç
# kitap günler sonra kendi bar-simülasyonuyla (farklı gün/fiyat) kapanıyor, GERÇEK çıkış fiyatı
# kayboluyordu. İKİ-MOTOR YASASINA AYKIRI DEĞİL: yasa, aynanın TELEMETRİSİ iç simülasyonun karar
# fiyatlarını değiştirmesin der; burada olan şey karar değil OLGUDUR — pozisyon artık YOK ve onu
# açık tutmak simülasyon değil hayalet yönetmek olurdu. Kitaplama yine iç kitabın KENDİ maliyet
# modelinden geçer (`close_position` raw fiyata slipajı kendisi uygular — dokunuş çıkışlarıyla
# aynı desen); GERÇEK dolum satıra `alpaca_fill_price` olarak ayrıca yazılır ve `mirror_divergence`
# model↔gerçek farkını ölçer.
def _koruma_dolumu_bul(all_orders: list, sym: str) -> dict | None:
    """Sembolün KORUMA-SINIFI emirlerinde dolmuş bacak ara. Sınıf hükmü `alpaca.coid_sinifi`den
    (v220 aile+yön, v221 grup kemerleri — süzgeç KOPYALANMAZ, yeniden kullanılır); dolum okuma
    `alpaca.koruma_fill`den. İlk dolum döner; yoksa None."""
    from .adapters import alpaca
    for o in (all_orders or []):
        if str(o.get("symbol")) != sym:
            continue
        if alpaca.coid_sinifi(o)[0] != alpaca.SINIF_KORUMA:
            continue
        kf = alpaca.koruma_fill(o)
        if kf is not None:
            return {**kf, "coid": o.get("client_order_id")}
    return None


def _koruma_dolumu_isle(kd: dict, sym: str, out: dict, dstr: str, broker) -> None:
    """Koruma dolumunu KİTABA işle + DOĞRU sınıfla alarmla (split_brain değil `koruma_dolumu`).

    Çıkış tipi dolan bacağa göre `koruma_stop` / `koruma_hedef` — çıkış-tipi sözlüğü AÇIKTIR
    (tüketiciler group-by okur: `analytics.py` → `profit_waterfall` → `by_reason.setdefault`,
    `api.api_plots` → `exits`; sabit bir
    enum yok — `CF_SIM_EXITS` yalnız CF simülasyon çıkışlarının listesidir), yeni ad kendi kovasını
    açar ve görünür kalır.

    UYDURMA YASAĞI: fiyat ya da bacak tipi okunamıyorsa kitaba İŞLENMEZ (0/varsayım yok) — alarm
    nedeni taşır, koruma emri pencerede durdukça bir sonraki tur yeniden denenir. `broker` yoksa
    (eski imzalı çağıran / pano force-sync) yine yalnız sınıflandırılır. YASA-4: her işlenemeyen
    dal nedeniyle birlikte seslidir; YASA-6: kayıt hem MIRROR_DRIFT olayına hem
    `broker_reconcile.json.positions.koruma_dolumu`ya düşer (pano + bekçi okuyucuları mevcut)."""
    bacak, fiyat = kd.get("bacak"), kd.get("price")
    reason = {"stop": "koruma_stop", "hedef": "koruma_hedef"}.get(bacak)
    neden = str(kd.get("neden") or "")
    islendi = False
    if fiyat is None:
        neden = neden or "dolum fiyatı legs'ten okunamadı"
    elif reason is None:
        neden = neden or "dolan bacağın tipi okunamadı — çıkış tipi seçilemez"
    elif broker is None:
        neden = "iç kitap erişimi yok (broker geçilmedi) — kapanış bir sonraki günlük tura kaldı"
    elif sym not in getattr(broker, "positions", {}):
        neden = "iç kitapta pozisyon bulunamadı (anlık görüntü ile kitap ayrışmış olabilir)"
    else:
        row = broker.close_position(sym, float(fiyat), reason, dstr)
        sim = float(row.get("exit") or 0.0)
        row["alpaca_fill_price"] = round(float(fiyat), 4)          # GERÇEK dolum — telemetri (1.3 simetriği)
        row["mirror_divergence"] = round(abs(float(fiyat) - sim) / sim, 5) if sim else 0.0
        _persist_trade(row)
        islendi = True
        # AYNA-KAPATMA KUYRUĞUNA BİLEREK YAZILMAZ (`_mirror_exit_enqueue` yok): pozisyonu aynada
        # kapatan ZATEN koruma dolumu — kuyruğa yazmak var olmayan pozisyonu kapatmaya çalışıp
        # sahte deneme/alarm turu üretirdi.
    out["positions"]["koruma_dolumu"].append(
        {"ticker": sym, "bacak": bacak, "fiyat": fiyat, "coid": kd.get("coid"),
         "exit_tipi": reason, "kitap": "kapatildi" if islendi else f"islenmedi: {neden}"})
    fiyat_s = "None" if fiyat is None else f"{float(fiyat):g}"
    obs.alarm(obs.ALARM_MIRROR_DRIFT,
              f"koruma dolumu: {sym} aynada koruma bacağıyla kapandı (bacak={bacak or '?'}, "
              f"fiyat={fiyat_s})"
              + (f" — iç kitaba `{reason}` kapanışı işlendi" if islendi
                 else f" — kitaba İŞLENEMEDİ: {neden}"),
              ticker=sym, drift_sinifi="koruma_dolumu", bacak=bacak, fiyat=fiyat,
              coid=kd.get("coid"), islendi=islendi, neden=neden or None)


# ==================================================================================================
# AYNA SAPMASI İKİ BOYUTLUDUR — NABIZ BUGÜNE DEK YALNIZ BİRİNİ TAŞIYORDU
# (`docs/DENETIM-SPLIT-SINIFI-2026-08-13.md`; canlı ölçüm 2026-08-12T22:01Z)
# --------------------------------------------------------------------------------------------------
# `mirror_drift` FİYAT sapmasıdır (`MIRROR_DRIFT_TOL`, bu dosyanın :25'i — iç sim dolumu ile gerçek
# Alpaca dolumu arasındaki fark). ADET sapması BAŞKA bir gerçektir (`position_drift`, :3075 —
# `missing_on_alpaca` ∪ `qty_drift`) ve yalnız `broker_reconcile.json`a yazılıyordu; NABIZDA O
# ANAHTAR HİÇ YOKTU. Ölçülen sonuç: pano HESAP rozeti nabzı okuduğu için (app.js) `mirror_drift`
# False görüp **"ayna uyumlu" (yeşil)** yazarken 4/4 pozisyon ~2 kat ayrıktı (NUE 54/25 · EMR 64/37
# · BKNG 43/22 · AMGN 33/22) ve AYNI ekranın eylem şeridi "Alpaca aynasında sapma var" diyordu.
# Kök neden bir DÜZELTMENİN yan ürünü: P6 tekilleştirmesi sapma METNİNİ mutabakat masasına taşıdı,
# özet rozeti ise başka bir alandan besleniyordu ve taşınmadı — rozet eski evin anahtarında kaldı.
#
# ALAN YAYAN TARAFA EKLENİR, TÜKETİCİYE YAMA ATILMAZ: nabzı okuyan HER tüketici (pano rozeti,
# /api/today, digest ve bundan sonra yazılacak olanlar) böylece otomatik kapsanır. Tüketiciyi
# yamalamak, "kapının kapsamı elle tutulan bir liste" kusurunu bir kez daha üretirdi.
#
# ÖLÇÜLMEDİ ≠ TEMİZ (UYDURMA YASAĞI). Mutabakat atlandıysa/düştüyse `checked` False'tur (:2778 iskelet
# + :2833 damga; `daily_cycle`daki `except` dalında `mirror` boş sözlüktür) ve o hâlde sapma hakkında
# HİÇBİR ŞEY bilmiyoruz → iki alan da `None`. Eski `bool(mirror.get("drift"))` biçimi tam bu uydurmayı
# yapıyordu: mutabakat hiç koşmasa bile nabza "sapma yok" düşüyordu.
#
# `None` DA HER TUR AÇIKÇA YAZILIR: nabız BİNDİRMELİ yazılır (`health.write_heartbeat` — alan sahipliği
# yasası), yani anahtarı hiç yazmamak DÜNKÜ değeri sonsuza dek taşırdı.
# ==================================================================================================
def ayna_sapma_alanlari(mirror: dict | None) -> dict:
    """Mutabakat çıktısından NABIZ alanları: `mirror_checked` + iki sapma boyutu (fiyat · adet).

    Saf fonksiyon — `daily_cycle` bunu `write_heartbeat(**...)` ile açar. AYRI durmasının nedeni
    ölçülebilirlik: sapmanın nabza doğru düşüp düşmediği tam bir günlük tur koşturmadan sınanabilmeli
    (kapının kendisi de bir kapı gerektirmemeli)."""
    m = mirror or {}
    olculdu = bool(m.get("checked"))
    pos = m.get("positions") or {}
    return {"mirror_checked": olculdu,
            # ATLAMA SINIFI ROZETE KADAR TAŞINIR (bkz. `_skip`): "ayna yok" (dahili broker) ile
            # "ayna okunamadı" (kimlik/erişim/arıza) ayrı hükümlerdir. Ölçülmüş bir turda alan
            # None kalır — sınıf ancak atlanan turun özelliğidir.
            "mirror_skip_sinifi": (None if olculdu else m.get("skip_sinifi")),
            "mirror_drift": (bool(m.get("drift")) if olculdu else None),
            "position_drift": (bool(pos.get("missing_on_alpaca") or pos.get("qty_drift"))
                               if olculdu else None)}


def reconcile_broker_state(meta: dict, dstr: str, closed_this_cycle: list,
                           open_positions: dict | None = None,
                           opens: dict | None = None,
                           fill_eq_now: float | None = None,
                           broker=None) -> dict:
    """Phase 1 reconciliation — bring the internal book into agreement with the Alpaca PAPER mirror.

      * strip locally-armed plans whose Alpaca order is DEAD (rejected/canceled/expired) so the internal
        broker doesn't fill a phantom next open (complements the strict-submit path);
      * POSITION reconciliation — internal open positions vs alpaca.positions(): an internal position with
        no Alpaca position AND no live entry order is split-brain (alarm); a shared symbol whose quantities
        diverge >25% is sizing drift (alarm); an Alpaca position the engine never opened (e.g. the
        operator's own holdings) is listed as external — informational only, NEVER an alarm;
      * audit execution DIVERGENCE — the internal simulator's gap-aware exit vs the ACTUAL Alpaca fill. A gap
        beyond MIRROR_DRIFT_TOL fires an alarm + sets a dashboard mirror_drift flag, and the real Alpaca fill
        is written to the trade row (alpaca_fill_price) so real-world slippage vs the model is measurable.

    Matched by client_order_id == plan_id. Guarded to BROKER==alpaca_paper; any Alpaca API failure is logged,
    never fatal to the cycle. Writes state/broker_reconcile.json for the dashboard.

    `fill_eq_now`: DOLUM anının boyut tabanı (iç motorun `daily_cycle`de kullandığı `eq_now`).
    ADET sapması (1.2b) tespit edilince boyut makbuzuyla kıyaslanıp `drift_sinifi` türetilir.
    OPSİYONELdir (varsayılan None) — eski çağıranlar bozulmaz; None ise sınıf `olculemedi` olur.

    `broker` (teşhis 2026-08-10): iç kitabın kendisi (PaperBroker). Koruma-OCO dolumu tespit
    edilince pozisyon kapanışını kitaba İŞLEMEK için gerekir. OPSİYONELdir — eski çağıranlar
    bozulmaz; None ise koruma dolumu yine DOĞRU SINIFLANIR (split_brain değil `koruma_dolumu`)
    ama kitaba işlenemez ve alarm bunu nedeniyle söyler (bir sonraki günlük tur işler)."""
    out = {"checked": False, "stripped": [], "drift": [],
           "positions": {"missing_on_alpaca": [], "qty_drift": [], "external": [],
                         "koruma_dolumu": []}}
    # ATLAMA DA BİR SONUÇTUR. Bu iki dal HİÇBİR ŞEY YAZMADAN dönüyordu: broker_reconcile.json dünkü
    # içeriğiyle diskte kalıyor, pano onu GÜNCEL mutabakat sanıp okuyordu — "kontrol edilmedi" ile
    # "kontrol edildi, temiz" ayırt edilemiyordu. Arıza dalı (aşağıda) zaten api_ok=False yazıyor;
    # atlama dalları da nedenini yazmalı, yoksa bayat artefakt taze konuşur.
    # ATLAMA SINIFI: "AYNA YOK" ile "AYNA OKUNAMADI" aynı şey değildir ve nabza
    # taşınırken ayrılmaları gerekir. Dahili brokerde kıyaslanacak bir ayna HİÇ YOKTUR — o hâli
    # "ölçülemedi" diye amber basmak, hiç var olmayan bir arızayı sonsuza dek raporlamak olurdu
    # (kurt masalı). Kimlik/erişim yokluğu ise GERÇEKTEN ölçülemeyen bir olgudur.
    def _skip(reason: str, sinif: str = "olculemedi") -> dict:
        """Mutabakatı atlar: artefakta `checked=False` + atlama nedeni/sınıfı yazar ve özeti döner.

        Sınıf ayrımı bilinçlidir: `ayna_yok` (kıyaslanacak ayna hiç yok) ile `olculemedi` (ayna var
        ama okunamadı) aynı şey değildir; bayat artefaktın taze konuşmasını engeller."""
        prev = store.read_json("broker_reconcile.json", {})
        store.write_json("broker_reconcile.json", {**prev, "checked": False, "skip_reason": reason,
                         "skip_sinifi": sinif, "date": dstr,
                         "updated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")})
        out["skip_sinifi"] = sinif
        return out

    if config.BROKER != "alpaca_paper":
        return _skip(f"broker={config.BROKER} — ayna mutabakatı yalnız alpaca_paper'da anlamlı",
                     "ayna_yok")
    from .adapters import alpaca
    # BACAK KOLU (teşhis 2026-08-10): bu turda kapananlar KALICI dolum-yaması kuyruğuna — TEK-ATIŞ DEĞİL.
    # Kayıt, aşağıdaki paper_available/API arıza dallarından ÖNCE düşer: kapanış turundaki geçici
    # arıza artık yamayı sonsuza dek kaybettiremez (kuyruk meta'da yaşar, `_save_broker` kalıcılaştırır,
    # sonraki reconcile yeniden dener). İki süzgeç: (a) satır zaten gerçek dolum taşıyor (koruma_dolumu
    # yolu satırı kapanış anında yazar), (b) ayna kapatması HÂLÂ kuyruktaysa
    # (`MIRROR_EXIT_KEY`) ölçülecek dolum henüz YOK — kapatma başarınca `karar` kaydı kimlikle düşer.
    _bekleyen_kapatma = set((meta.get(MIRROR_EXIT_KEY) or {}).keys())
    for _tr in (closed_this_cycle or []):
        if _tr.get("alpaca_fill_price") is not None:
            continue
        if str(_tr.get("ticker")) in _bekleyen_kapatma:
            continue
        _exit_fill_kaydet(meta, _tr.get("plan_id"), _tr.get("ticker"), kaynak="bacak",
                          dstr=dstr, reason=_tr.get("exit_reason"))
    if not alpaca.paper_available():
        return _skip("paper_available()=False — kimlik/erişim yok, ayna okunamadı")
    try:
        # nested=True is REQUIRED: the flat list endpoint splits a bracket into 3 top-level orders with
        # legs=[], so exit_fill_price() (which reads the parent's legs) would always see nothing and the
        # divergence audit below would silently no-op. nested returns the parent carrying its TP/SL legs.
        # pencere artık SAYFALIdır — hedef, dolum bekleyen en eski kayıt (E2 + çıkış kuyruğu);
        # kapsanamayan pencere beyanlıdır (`emir_penceresi.kapsandi=False` + olay), sessiz değil.
        all_orders, out["emir_penceresi"] = _alpaca_emir_penceresi(
            alpaca, _emir_penceresi_hedefi(meta, dstr))
        # alpaca.orders() İSTİSNA FIRLATMAZ — hata durumunda [] döner. Yani
        # aşağıdaki `except` ÖLÜ KOD'du ve API arızası "hiç emir yok" gibi okunuyordu: a_by_sym da boş
        # kalıp AÇIK HER POZİSYON 'Alpaca'da kayıp' diye split-brain alarmı üretiyor, pano ise
        # api_ok=True gösteriyordu. Arızayı artık taşıma kaydı söylüyor (ilk sayfa arızası helper'dan
        # AYNI RuntimeError ile fırlar — davranış birebir eski).
        if not alpaca.transport()["ok"]:
            raise RuntimeError(alpaca.transport().get("error") or "alpaca transport down")
    except Exception as e:
        obs.warn("reconcile_orders_failed", error=f"{type(e).__name__}: {e}")
        # SAFE-FAIL görünürlüğü: broker API'sine ulaşılamadı — sessiz kalma, panoya işle (şerit amber)
        prev = store.read_json("broker_reconcile.json", {})
        store.write_json("broker_reconcile.json", {**prev, "api_ok": False, "date": dstr,
                         "updated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")})
        return out
    out["checked"] = True
    by_coid = {o.get("client_order_id"): o for o in (all_orders or []) if o.get("client_order_id")}
    by_id = {str(o.get("id")): o for o in (all_orders or []) if o.get("id")}   # kapatma emri kimlikle
    DEAD = {"rejected", "canceled", "cancelled", "expired", "done_for_day"}

    # (1.1) E2 — GİRİŞ SLİPAJ DEFTERİNİN DOLUM YARISI. Emirler ZATEN okundu; ikinci bir çağrı yok.
    out["entry_slippage"] = _patch_entry_slippage(by_coid, opens, dstr)

    # (1.2) strip armed plans whose mirror order is dead
    kept = []
    for pl in meta.get("armed", []):
        o = by_coid.get(pl.get("id"))
        if o and str(o.get("status", "")).lower() in DEAD:
            out["stripped"].append(pl.get("ticker"))
            obs.log("reconcile_strip_armed", ticker=pl.get("ticker"), status=o.get("status"))
        else:
            kept.append(pl)
    if len(kept) != len(meta.get("armed", [])):
        meta["armed"] = kept

    # (1.2b) POSITION reconciliation — Alpaca-reported positions vs the internal book's open positions.
    # A symbol can legitimately be internal-only while its Alpaca stop-entry hasn't triggered yet, so
    # "missing" requires no position AND no live (non-dead, non-filled) order for that symbol.
    try:
        apos = alpaca.positions()
        if not alpaca.transport()["ok"]:                 # [] burada 'pozisyon yok' DEĞİL, arıza
            raise RuntimeError(alpaca.transport().get("error") or "alpaca transport down")
    except Exception as e:
        obs.warn("reconcile_positions_failed", error=f"{type(e).__name__}: {e}")
        # pozisyon listesi okunamadıysa POZİSYON mutabakatını hiç yapma: boş listeyle karşılaştırmak
        # her açık pozisyon için sahte 'Alpaca'da kayıp' alarmı üretir (denetim 2026-07-21).
        out["positions"]["api_ok"] = False
        store.write_json("broker_reconcile.json", {**store.read_json("broker_reconcile.json", {}),
                         "api_ok": False, "date": dstr,
                         "updated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")})
        return out
    a_by_sym = {str(p.get("symbol")): p for p in (apos or [])}
    alive_order_syms = {o.get("symbol") for o in (all_orders or [])
                        if str(o.get("status", "")).lower() not in DEAD | {"filled"}}
    local = {str(t): (dict(q) if isinstance(q, dict) else {"qty": float(q), "scaled_out": False})
             for t, q in (open_positions or {}).items()}
    for sym, info in local.items():
        qty, scaled = float(info.get("qty") or 0.0), bool(info.get("scaled_out"))
        ap = a_by_sym.get(sym)
        if ap is None:
            if sym not in alive_order_syms:
                # KORUMA-OCO DALI (teşhis 2026-08-10): "iç açık + aynada ne pozisyon ne canlı emir" İKİ ayrı
                # olgunun ortak görüntüsüdür ve ikisi ayrı sınıftır:
                #   koruma_dolumu → sembolün KORUMA-sınıfı emri (yapısal kemerler: coid_sinifi,
                #                   v220/v221) DOLMUŞ — pozisyon aynada korumayla KAPANDI; kitaba
                #                   kapanış işlenir (aşağıdaki yardımcı), split_brain DEĞİL.
                #   split_brain   → koruma dolumu da yok: gerçek durum ayrışması (eski davranış).
                kd = _koruma_dolumu_bul(all_orders, sym)
                if kd is not None:
                    _koruma_dolumu_isle(kd, sym, out, dstr, broker)
                    continue
                out["positions"]["missing_on_alpaca"].append(sym)
                # SABİT sapma sınıfı — sizing/sermaye sapması DEĞİL, durum ayrışması (iç açık, aynada
                # ne pozisyon ne emir). Sizing taksonomisi uymaz; brief-sanction ile ADI konur.
                obs.alarm(obs.ALARM_MIRROR_DRIFT,
                          f"ayna pozisyonu kayıp: {sym} içeride açık, Alpaca'da ne pozisyon ne emir var",
                          ticker=sym, local_qty=qty, drift_sinifi="split_brain")
            continue
        try:
            aq = float(ap.get("qty") or 0.0)
        except (TypeError, ValueError):  # sessiz-yutma: ağ/sağlayıcı hatası bu yolun NORMAL hâli; çağıran boş sonuç üzerinden yedek kaynağa düşer ve kaynak seçimi ayrıca kaydedilir
            continue
        if scaled:
            continue   # internal book banked a partial (qty reduced by design); the mirror bracket still
                       # holds full size — a KNOWN, intentional gap, not drift (audit #16 false alarm)
        # sizing runs off two slightly different equities (internal book vs Alpaca account), so small qty
        # gaps are expected; >25% relative gap is real drift, not rounding.
        if qty > 0 and abs(aq - qty) / qty > 0.25:
            # sapmayı ADLANDIR — boyut makbuzunu (`size_law`) dolum-anı girdilerine
            # kıyasla. Alarm/eşik (>%25) DEĞİŞMEZ; yalnız `drift_sinifi` + neden eklenir. Makbuz
            # yoksa `makbuzsuz_boyut`, türetilemezse `olculemedi` (0/boş DEĞİL).
            # Türetme ASLA fırlamaz (helper içi).
            # KISMİ DOLUM makbuz kıyasından ÖNCE — kanıtı emrin kendisi (filled_qty<qty).
            _kismi = _kismi_dolum_tespiti(by_coid.get(info.get("plan_id")))
            if _kismi is not None:
                _sinif, _neden = _kismi
            else:
                # yaş sinyali — pozisyon BU seansta mı doldu? (ts_open yoksa None = okunamadı;
                # sınıflandırıcı yaşlı/yaşsız pozisyonda bugünün eq'siyle kıyas YAPMAZ.)
                _ts0 = str(info.get("ts_open") or "")[:10]
                _rcpt = (meta.get("size_law") or {}).get(info.get("plan_id"))
                _sinif, _neden = _drift_sinifi_adet(_rcpt, fill_eq_now,
                                                    meta.get("peak_equity", START_EQUITY),
                                                    dolum_taze=(None if not _ts0 else _ts0 == dstr))
            out["positions"]["qty_drift"].append({"ticker": sym, "local_qty": qty, "alpaca_qty": aq,
                                                  "drift_sinifi": _sinif})
            obs.alarm(obs.ALARM_MIRROR_DRIFT,
                      f"ayna adet sapması: {sym} — içeride {qty:g}, Alpaca'da {aq:g}"
                      f" · sapma sınıfı: {_sinif} — {_neden}",
                      ticker=sym, local_qty=qty, alpaca_qty=aq,
                      drift_sinifi=_sinif, drift_neden=_neden)
    # engine-orphans vs true externals: a bracket the ENGINE submitted (client_order_id 'P-…') can fill
    # on Alpaca after the internal side dropped its plan (breaker day, slot race, gap guard) — that is
    # split-brain and must ALARM, not hide under 'external' with the operator's own holdings (audit #14).
    engine_syms = {o.get("symbol") for o in (all_orders or [])
                   if str(o.get("client_order_id", "")).startswith("P-")
                   and str(o.get("status", "")).lower() in ("filled", "partially_filled")}
    # ÇIKIŞ-KAYNAKLI YETİM AYRI SINIFTIR. İki teşhis aynı isimle sayılırsa ikisi de okunamaz:
    #   engine_orphans → "iç defter planı düşürdü, ayna DOLDU" (split-brain, sebebi bilinmiyor)
    #   exit_orphans   → "iç motor ÇIKTI, aynayı kapatmayı denedik, kapanmadı" (sebep BİLİNİYOR,
    #                     kuyrukta duruyor ve her döngüde yeniden deneniyor)
    # Ayrımın ikinci sonucu: `_mirror_busy` (P3 karar kilidi) yalnız `engine_orphans`ı okur, yani
    # çıkış-kaynaklı yetim sembolü SONSUZA DEK karar dışı bırakmaz — huninin kendi kendini aç
    # bırakması bu bulgunun asıl zararıydı. Koruma kaybolmaz: bracket'ın canlı bacakları varken sembol
    # `alive_order_syms` üzerinden zaten kilitlidir.
    _exit_pending = set((meta.get(MIRROR_EXIT_KEY) or {}).keys())
    _tum_yetim = sorted(sym for sym in a_by_sym if sym not in local and sym in engine_syms)
    orphans = [s for s in _tum_yetim if s not in _exit_pending]
    exit_orphans = [s for s in _tum_yetim if s in _exit_pending]
    # ==============================================================================================
    # YETİM SINIFLAMASI (teşhis 2026-08-10): "motor_yetimi" ÜÇ AYRI OLGUNUN ortak adıydı ve üçü tek isimle
    # okunamıyordu (çıkış kuyruğu gerekçesinin giriş tarafındaki ihlali). SINIF AYRIMI (yalnız
    # görünürlük — kabul/kapatma OPERATÖR kararıdır, bu tur EMİR ÜRETMEZ; `engine_orphans`
    # listesi ve `_mirror_busy` karar kilidi BİREBİR aynı kalır):
    #   tasima_gecikmesi — plan hâlâ SİLAHLI kümede (taşınan/bar bekleyen/onaylı): ayna gün içi
    #                      doldu, iç dolum bir sonraki açılışta — bekleme, arıza değil.
    #   cikis_gecikmesi  — iç kitap sembolü YAKIN ZAMANDA kapattı (dolum-yaması kuyruğunda ya da
    #                      son satırlarda) ama ayna pozisyonu duruyor: bacak/kapatma dolumu gecikti.
    #   giris_yetimi     — ikisi de değil: aynanın DOLDURDUĞU girişin iç kitapta karşılığı yok
    #                      (gerçek yetim; kabul-mü-kapat-mı politikası operatörde).
    # ==============================================================================================
    _armed_syms = {str(a.get("ticker")) for a in (meta.get("armed") or []) if a.get("ticker")}
    _efp_syms = {str(v.get("ticker")) for v in (meta.get(EXIT_FILL_KEY) or {}).values()
                 if v.get("ticker")}
    _son_kapanis: dict = {}
    for _r in store.read_jsonl("trades.jsonl")[-60:]:
        if _r.get("ticker"):
            _son_kapanis[str(_r["ticker"])] = str(_r.get("ts_close") or "")

    def _yakin_kapanis(sym: str) -> bool:
        """İç kitap bu sembolü son 7 gün içinde kapattı mı? (son 60 defter satırından bakılır).

        Tarih ayrıştırılamıyorsa False — yakınlık KANITLANAMADI, uydurulmaz."""
        ts = _son_kapanis.get(sym)
        if not ts:
            return False
        try:
            return 0 <= (dt.date.fromisoformat(dstr) - dt.date.fromisoformat(ts[:10])).days <= 7
        except ValueError:  # sessiz-yutma: biçimsiz tarih tek satırı düşürür; sınıf `giris_yetimi`ye kalır (yakınlık KANITLANAMADI, uydurulmaz)
            return False

    def _yetim_sinifla(sym: str) -> tuple[str, str]:
        """Aynada açık ama iç kitapta olmayan sembolü sınıflar: `(sinif, neden)`.

        Üç sınıf: `tasima_gecikmesi` (plan hâlâ silahlı — bekleme, arıza değil), `cikis_gecikmesi`
        (iç kitap yakında kapattı, kapatma dolumu bekleniyor) ve `giris_yetimi` (gerçek yetim,
        kabul-mü-kapat-mı OPERATÖR kararı). SALT SINIFLANDIRMA — emir üretmez."""
        if sym in _armed_syms:
            return "tasima_gecikmesi", ("plan hâlâ silahlı kümede (taşınan/bar bekleyen) — ayna "
                                        "gün içi doldu, iç dolum bir sonraki açılışta; bekleme, "
                                        "arıza değil")
        if sym in _efp_syms or _yakin_kapanis(sym):
            return "cikis_gecikmesi", ("iç kitap bu sembolü yakın zamanda KAPATTI ama ayna "
                                       "pozisyonu duruyor — çıkış bacağı/kapatma dolumu bekleniyor "
                                       "(B2); dolum-yaması kuyruğu izliyor")
        return "giris_yetimi", ("aynanın DOLDURDUĞU girişin iç kitapta karşılığı yok — gerçek "
                                "yetim; kabul-mü-kapat-mı OPERATÖR kararı (bu tur emir üretmez)")

    orphans_sinifli = []
    for sym in orphans:
        _ys, _yn = _yetim_sinifla(sym)
        orphans_sinifli.append({"ticker": sym, "sinif": _ys, "neden": _yn})
        obs.alarm(obs.ALARM_MIRROR_DRIFT,           # durum ayrışması, sizing değil (sınıflı alt-ad)
                  f"motor yetimi ({_ys}): {sym} Alpaca'da açık (motorun emri dolmuş) ama iç "
                  f"defterde yok — {_yn}",
                  ticker=sym, drift_sinifi=_ys)
    for sym in exit_orphans:
        obs.alarm(obs.ALARM_MIRROR_DRIFT,           # SABİT sapma sınıfı (çıkış icra edilemedi, sizing değil)
                  f"çıkış yetimi: {sym} iç motor çıktı ama ayna kapatılamadı — kuyrukta, "
                  f"bir sonraki döngüde yeniden denenecek",
                  ticker=sym, reason=(meta.get(MIRROR_EXIT_KEY) or {}).get(sym, {}).get("reason"),
                  tries=(meta.get(MIRROR_EXIT_KEY) or {}).get(sym, {}).get("tries"),
                  drift_sinifi="cikis_yetimi")
    out["positions"]["engine_orphans"] = orphans          # eski okuyucular (pano sayacı, _mirror_busy) BOZULMAZ
    out["positions"]["engine_orphans_sinifli"] = orphans_sinifli   # sınıflı görünürlük (pano passthrough)
    out["positions"]["exit_orphans"] = exit_orphans
    out["positions"]["external"] = sorted(sym for sym in a_by_sym
                                          if sym not in local and sym not in engine_syms)  # info only, no alarm

    # (1.2c) DİNAMİK TRAILING-STOP AYNA SENKRONU: iç defterin iz süren stop'u yükseldiyse, aynadaki
    # bracket'ın stop bacağı da yükseltilir (PATCH) — YALNIZ YUKARI, koruma asla gevşetilmez. Bu,
    # trail sıkılaştıkça aynanın eski stop'ta kalıp sapma alarmı üretmesini kökten keser.
    out["trail_synced"] = []
    for sym, info in local.items():
        ts = info.get("trail_stop")
        pid = info.get("plan_id")
        if not ts or not pid:
            continue
        parent = by_coid.get(pid)
        if not parent:
            continue
        for leg in (parent.get("legs") or []):
            if str(leg.get("type")) != "stop" or str(leg.get("status")).lower() not in ("new", "held", "accepted", "open"):
                continue
            try:
                cur_stop = float(leg.get("stop_price") or 0.0)
            except (TypeError, ValueError):  # sessiz-yutma: ağ/sağlayıcı hatası bu yolun NORMAL hâli; çağıran boş sonuç üzerinden yedek kaynağa düşer ve kaynak seçimi ayrıca kaydedilir
                continue
            if float(ts) > cur_stop * 1.001:               # anlamlı yükseliş; asla aşağı çekme
                res = alpaca.replace_order_stop(leg.get("id"), float(ts), cur_stop=cur_stop)  # sınır da reddeder
                out["trail_synced"].append({"ticker": sym, "from": cur_stop, "to": round(float(ts), 2),
                                            "ok": bool(res.get("ok"))})
                obs.log("mirror_trail_synced", ticker=sym, from_stop=cur_stop, to_stop=round(float(ts), 2),
                        ok=bool(res.get("ok")), detail=str(res.get("detail", ""))[:120])
                _trail_patch_alarm(sym, res, cur_stop, float(ts))

    # (1.3) execution-divergence audit — ARTIK KUYRUK-GÜDÜMLÜ (teşhis 2026-08-10).
    # Eski dal yalnız `closed_this_cycle` üzerinde TEK ATIŞtı: kapanış turundaki API arızası ya da
    # farklı günde dolan bacak yamayı sonsuza dek kaybediyordu; DELETE-kapatmalarının (karar
    # çıkışları, ~%38) dolumu ise YAPISAL olarak hiç okunamıyordu. Kuyruk turun başında dolduruldu
    # (bu turda kapananlar + önceki turların bekleyenleri); burada her kayıt için iki okuma yolundan
    # (`karar`=close_order_id'li market emri, `bacak`=parent'ın TP/SL bacağı) dolum aranır, bulunan
    # kilitli yamayla satıra yazılır, bulunamayan `EXIT_FILL_MAX_TRIES` tura kadar taşınır ve
    # vazgeçiş OLAYLI + satıra dürüst beyanla kapanır. Eşik/alarm ("icra", MIRROR_DRIFT_TOL) aynen.
    _exit_fill_yamasi(meta, by_coid, by_id, dstr, out, alpaca)

    # Faz 1 (1a): HAYALET emirler — Alpaca'da canlı görünen ama yerel izde (armed/alpaca_submitted/
    # mirror durum makinesi) karşılığı olmayan coid'ler. Motor bunları AÇMADI: ya operatör elle emir
    # girdi ya da defter/tarihçe ayrıştı. Kırmızı etiket panoda; asla otomatik iptal edilmez (politika).
    _known = set(meta.get("alpaca_submitted", []) or []) | {a.get("id") for a in meta.get("armed", [])}
    try:
        _known |= set((store.read_json("mirror_orders.json", {}) or {}).get("orders", {}).keys())
    except Exception as e:
        # YASA 4: bu okuma sessizce düşerse _known EKSİK kalır ve motorun kendi emirleri
        # "hayalet" diye panoya kırmızı düşer — yani sessiz yutma burada YANLIŞ ALARM üretiyordu.
        obs.warn("mirror_orders_unreadable", error=f"{type(e).__name__}: {e}",
                 detail="hayalet listesi eksik bilinen-emir kümesiyle hesaplandı")
    out["ghosts"] = [{"symbol": o.get("symbol"), "coid": o.get("client_order_id"),
                      "status": o.get("status")}
                     for o in (all_orders or [])
                     if str(o.get("status", "")).lower() not in DEAD | {"filled"}
                     and o.get("client_order_id") and o.get("client_order_id") not in _known][:20]
    if out["ghosts"]:
        obs.warn("reconcile_ghost_orders", n=len(out["ghosts"]),
                 symbols=[g["symbol"] for g in out["ghosts"]][:8])
    # Faz 1 (1d): bu reconcile turunun zorlama-senkron özeti — saydamlık paneli buradan okur
    out["force_sync"] = {"stripped": len(out["stripped"]),
                         "trail_patched": sum(1 for x in out.get("trail_synced", []) if x.get("ok")),
                         "trail_failed": sum(1 for x in out.get("trail_synced", []) if not x.get("ok"))}
    pos = out["positions"]
    from . import watchdog as _wd6
    _wd6.beat("mirror_reconcile")
    store.write_json("broker_reconcile.json", {
        "date": dstr, "mirror_drift": bool(out["drift"]), "stripped": out["stripped"], "drift": out["drift"][:10],
        "ghosts": out["ghosts"], "force_sync": out["force_sync"],
        "position_drift": bool(pos["missing_on_alpaca"] or pos["qty_drift"]), "positions": pos,
        "failed_submissions": (meta.get("broker_rejected") or [])[-10:],
        # v3 senkron kriterleri: canlı emirli semboller (P3 aynı hisseyi yeniden silahlamasın) +
        # broker API sağlığı (kesinti panoda görünür olmalı) + trail senkron kaydı
        "alive_order_syms": sorted(s for s in alive_order_syms if s),
        "api_ok": True, "trail_synced": out.get("trail_synced", []),
        # Görünürlük üçlüsü (teşhis 2026-08-10; okuyucu: /api/alpaca `reconcile` passthrough +
        # /api/diagnostics — pano mutabakat masası):
        #   entry_slippage  — E2 yama sayaçları. Teşhisin TEK okuyucusuz-yazım bulgusu buydu
        #                     (üretiliyor, hiçbir artefakta girmiyordu — YASA-6 ihlali kapandı).
        #   exit_fill       — çıkış dolum-yaması kuyruğunun tur özeti (bekleyen/yamalanan/vazgeçilen).
        #   emir_penceresi  — B7a sayfalı pencerenin kapsam beyanı (kapsandi=False sessiz değil).
        "entry_slippage": out.get("entry_slippage"),
        "exit_fill": out.get("exit_fill"),
        "emir_penceresi": out.get("emir_penceresi"),
        "updated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")})
    return out
