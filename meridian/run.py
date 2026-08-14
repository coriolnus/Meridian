"""run.py — entrypoint (TOHUMLAMA + TEK ATIŞ). 24/7 KADANS BURADA DEĞİL: `scheduler.advance_once`.

  python -m meridian.run --dry-run --replay 2023-01-01:2024-12-31   # seed state from real history
  python -m meridian.run --once                                     # one live paper daily cycle
  MERIDIAN_AUTOSTART_CYCLE=1 uvicorn meridian.api:app               # 24/7 kadans (süreç-içi zamanlayıcı)

The replay writes REAL state (trades, equity, regime, candidates, plans, scoreboard) so the
dashboard and the reflection loop have genuine data — not fixtures. Research system. Paper mode.

KALICI KURAL — İki kadans yasası tek depoda yaşayamaz (C3, 2026-08-02).
`worker()` 24/7 kadansın İKİNCİ bir uygulamasıydı ve ÜRETİMDE HİÇ KOŞMUYORDU: canlı ve yerel
başlatma yollarının HEPSİ uvicorn + süreç-içi `scheduler.start()`tir (`deploy/oracle-a1/
meridian.service`, `ops/com.meridian.agent.plist`, `serve.sh`); `meridian.run` yalnız `--replay`
tohumu için çağrılıyordu. Koşmayan bir yol DÜZELTME BASKISI ÜRETMEZ — bu yüzden zamanlayıcıda
adıyla düzeltilmiş ÜÇ kusuru son gününe kadar taşıdı:
  (a) SEANS TANIMI: takvim indeksinden `sessions[-1]` okuyordu, yani BUGÜNÜN seansını GECE
      YARISINDAN itibaren "kapanmış" sayıyordu. `scheduler._last_closed_session` tam bu hatayı
      `market_close <= now` filtresiyle "audit #12" diye düzeltilmiş ilan ediyor.
  (b) VERİ YOLU: `dataset.load(use_cache=False)` çağırıyordu, `load_live()` DEĞİL — o yolda ne
      Finviz keşfi ne aynı-akşam Alpaca bacağı vardır (aynı-akşam kapısı `session=` yalnız
      `load_live` üzerinden verilir).
  (c) İLERLEME: `daily_cycle` dönüşü hiç sorgulanmadan `last_processed` yazılıyordu — kapsama
      kapısı `noop`/`waiting_for_universe`/`refused_regressive` dönse bile o seans bir daha
      denenmiyordu; sık/seyrek merdiven, `_repair_once_per_session` ve çoklu-seans yetişme
      döngüsü bu yolda YOKTU.
Seans-sonrası kadansların HİÇBİRİ (öğrenme, Y4, haftalık üçlü, arming, selfreview, yetim süpürme,
nous, sprint, earnings, intraday gap) burada yoktu. Dördüncü bir yama kusuru kapatırdı, SINIFI
kapatmazdı: sınıf "ikinci bir kadans uygulamasının var olması"dır. O yüzden hüküm EMEKLİLİKtir.

GERİ ALINABİLİRLİK. Gövde silindi ama KAYBOLMADI: bu turdan önceki her sürüm tam metni taşır
(`git show 8aaf05e:meridian/run.py`). Kadansın kendisi zaten `scheduler.py`de yaşıyor ve orada
DÜZELTİLMİŞ hâliyle koşuyor — yani geri alınacak bir yetenek değil, yalnız bir kopya emekli oldu.
`worker()` adı yaşamaya devam eder ama artık YÖNLENDİRİR (bkz. gövdesindeki gerekçe).
YAN ETKİ (beyan, kapsam DIŞI): `obs.ALARM_HEARTBEAT_STALE` jetonunun depodaki TEK üreticisi bu
döngüydü; jeton bugün üreticisiz kaldı. Üretimde zaten hiç ateşlenemiyordu (asılı-tick koruması
`meridian-tick-watchdog.timer`dır) — jetonun yeni bir üreticiye bağlanması ayrı bir bulgudur."""
from __future__ import annotations
import argparse

from rich.console import Console

from . import config, store, backtest, dataset, memory, versioning, health, loop, ledgerstamp
from . import broker as BR          # C18: ret SINIFI adı tek kaynaktan (`EV_MISSED_LIMIT`) —
                                    # dizgiyi burada ikinci kez yazmak, tam da bu turun kovaladığı
                                    # "aynı yasanın iki uygulaması" hatası olurdu

console = Console()


def bootstrap_v01() -> dict:
    """Ensure strategy.yaml v01 + its history snapshot exist."""
    p = config.strategy_path()
    if not p.exists():
        strat = config.default_strategy()
        config.dump_yaml(strat, p)
        versioning.snapshot(strat)
        console.print("[green]bootstrapped strategy.yaml v01[/green]")
    return config.load_strategy()


def _ancestor_from_history(version) -> dict:
    """Karnede satırı HİÇ olmayan bir ATA sürüm için history anlık görüntüsünden yalnız KARARI kurtar.

    Skor alanı bilerek yazılmaz. Re-seed kanıtı yeniden üretir; ama `state/history/vNNNN.yaml` bir
    performans kaydı değil bir parametre kararıdır — taşınabilir olan odur. Skorsuz ata satırı
    `rollback.evaluate_outcomes`'a dürüstçe "ölçemedim" dedirtir (`no_parent_score` açık kalır);
    uydurulmuş bir taban ise geri-alma kararını zehirler: canlı sürümün otomatik olarak ataya
    döndürülmesi demektir. Ölçülmemiş taban, yanlış tabandan iyidir."""
    path = config.HISTORY / f"v{int(version):04d}.yaml"
    if not path.exists():
        from . import obs
        obs.warn("reseed_ancestor_snapshot_missing", version=int(version), path=str(path),
                 detail="ata sürümün ne karne satırı ne anlık görüntüsü var — soyağacı burada kopuyor")
        # BOŞ SÖZLÜK DÖNMEK, KAYBI KARNEDE GÖRÜNMEZ KILIYORDU (2026-07-26): `{}` yazılan bir ata
        # satırı, "kararı kurtaramadım" ile "satır zaten boştu" arasında hiçbir ayrım bırakmıyor ve
        # kaybın tek izi olayda kalıyordu — karneyi okuyan (rollback, pano, öz-değerlendirme) yalnız
        # sessiz bir boşluk görüyordu. İŞARETLİ satır yazılır; skor alanı yine YOK, çünkü ölçülmemiş
        # bir taban uydurmak geri-alma kararını zehirler.
        return {"note": "history anlık görüntüsü yok — soyağacı burada kopuyor (skor yok)"}
    import yaml
    with open(path) as f:
        snap = yaml.safe_load(f) or {}
    row = {"note": "history anlık görüntüsünden kurtarıldı — SKOR YOK (yeniden hesaplanmadı)"}
    for _k in ("params", "parent"):
        if snap.get(_k) is not None:
            row[_k] = snap[_k]
    return row


def _reset_book_to(res, end: str) -> dict:
    """Kitabı, tohumlanan işlem defterine hizala. Açık pozisyon TAŞINMAZ: replay'in kapanışta açık
    kalan pozisyonu varsa o zaten `res.trades`'e girmemiştir ve canlı kitaba taşınması, gerçekte
    hiç alınmamış bir pozisyonu operatörün defterine yazmak olurdu.

    Kimlik: nakit = başlangıç sermayesi + Σ gerçekleşen K/Z. `meridian/recompute.py` bu kimliği
    bağımsız iki yoldan doğrular; buradaki yazım o denetimi geçmek ZORUNDA."""
    from .score import START_EQUITY
    realized = round(sum(float(t.get("pnl_dollars") or 0) for t in res.trades), 2)
    cash = round(START_EQUITY + realized, 2)
    peak = round(max([e[1] for e in res.equity] + [START_EQUITY]), 2) if res.equity else START_EQUITY
    book = {"cash": cash, "realized_pnl": realized, "last_id": len(res.trades),
            "positions": {}, "armed": [], "pending_exits": {}, "last_date": end,
            "day_start_equity": cash, "alpaca_submitted": [], "broker_rejected": [],
            "peak_equity": peak}
    # KİLİT (B3, 2026-07-31): tohum yolu CANLI defteri ezer. `store.file_lock` artık süreçler
    # arasıdır — bu yazım canlı worker koşarken tetiklenirse kitabı ortasından yakalamak yerine
    # sıraya girer (worker'ı durdurma disiplini yerini KORUR; kilit onun yerine geçmez).
    with store.file_lock("portfolio.json"):
        store.write_json("portfolio.json", book)
    console.print(f"[cyan]kitap tohumlanan deftere hizalandı: nakit {cash:,.2f}$ "
                  f"(gerçekleşen {realized:,.2f}$, zirve {peak:,.2f}$)[/cyan]")
    return book


# Nabız bu kadar taze ise CANLI bir worker koşuyor sayılır. Eşik, worker'ın kendi bayatlık
# alarmıyla (health.stale varsayılanı) aynı tutulur: iki yerde iki farklı "canlı" tanımı olsaydı
# biri diğerini sessizce yalanlardı.
RESEED_HEARTBEAT_FRESH_S = 900


def replay_seed(start: str, end: str) -> dict:
    """Populate state/ from a historical replay on real bars."""
    import os as _os
    # CANLI WORKER BEKÇİSİ (2026-07-26): re-seed state'i SIFIRDAN kurar. Aynı anda bir worker
    # koşuyorsa iki yazar aynı deftere biner (kitap, nabız, karne) ve hangi satırın hangi koşuma ait
    # olduğu bir daha ayrılamaz — hata sessizdir, hiçbir istisna fırlamaz.
    # "Worker koşuyor mu" UYDURULMAZ, ÖLÇÜLÜR: nabız tazeliği zaten bu soruyu cevaplıyor
    # (health.stale). Ayrı bir süreç taraması eklemek ikinci bir gerçek kaynağı doğururdu.
    _hb_age = health.heartbeat_age_seconds()
    if not health.stale(RESEED_HEARTBEAT_FRESH_S) and _os.environ.get("MERIDIAN_FORCE_RESEED") != "1":
        from . import obs
        obs.warn("reseed_refused_live_worker", heartbeat_age_s=round(_hb_age or 0, 1),
                 threshold_s=RESEED_HEARTBEAT_FRESH_S,
                 detail="nabız taze — canlı worker koşuyor; re-seed onun defterini altından çeker")
        console.print(f"[red]REDDEDİLDİ: nabız {round(_hb_age or 0)}sn önce yazılmış "
                      f"(<{RESEED_HEARTBEAT_FRESH_S}sn) — CANLI bir worker koşuyor. Re-seed onun "
                      f"defterini sıfırdan kurar. Önce worker'ı durdur; bilerek istiyorsan "
                      f"MERIDIAN_FORCE_RESEED=1 ile çalıştır.[/red]")
        return {"error": "live_worker_running", "heartbeat_age_s": round(_hb_age or 0, 1)}
    # re-seed EMNİYETİ (2026-07-20): replay kitabı sıfırdan kurar — silahlı plan varken çalıştırmak
    # o planların altından zemini çeker (GS böyle kaybedildi: 07-15 sabahı re-seed + eski seans-atlama).
    # Silahlı plan doluyken açık niyet ister: MERIDIAN_FORCE_RESEED=1.
    _armed = (store.read_json("portfolio.json", {}) or {}).get("armed") or []
    if _armed and _os.environ.get("MERIDIAN_FORCE_RESEED") != "1":
        names = ", ".join(a.get("ticker", "?") for a in _armed)
        console.print(f"[red]REDDEDİLDİ: {len(_armed)} silahlı plan var ({names}) — replay bunları siler. "
                      f"Bilerek istiyorsan MERIDIAN_FORCE_RESEED=1 ile çalıştır.[/red]")
        return {"error": "armed_plans_present", "armed": [a.get("ticker") for a in _armed]}
    # ÖĞRENME GEÇMİŞİ KORUMASI (denetim turu 26, 2026-07-21): replay, scoreboard.json'u TEK sürümlük
    # yeni bir sözlükle EZİYORDU. Silahlı-plan koruması vardı ama bu yoktu: v2/v3 shipping'ten sonra
    # bir re-seed, tüm sürüm karnesini (live_score/backtest_oos/terfi kaydı) yok ediyordu — ve
    # rollback'in ebeveyn-skoru geri düşüşü buradan besleniyor, yani geri alma da kör kalıyordu.
    _sb = store.read_json("scoreboard.json", {}) or {}
    _vers = (_sb.get("versions") or {})
    # BEKÇİ YALNIZ SKOR TAŞIYAN SATIRLARI SAYAR (2026-07-26). Önceki hâli `len(_vers) > 1` idi ve
    # kendi kendini kilitliyordu: bir önceki re-seed'in KURTARDIĞI skorsuz ata satırları (yukarıdaki
    # `_ancestor_from_history` yalnız kararı taşır, hiçbir skor yazmaz) sayıya giriyordu. Yani bir kez
    # re-seed yapan operatör, korunması gereken hiçbir ÖLÇÜM olmadığı hâlde sonsuza dek FORCE'a
    # mahkûm oluyordu — ve FORCE alışkanlığa dönüşürse gerçek geçmişi de o bayrak siler.
    # Korunmaya değer olan "satır sayısı" değil KANIT'tır: live_score ya da backtest_oos.
    _scored = sorted(v for v, row in _vers.items()
                     if isinstance(row, dict) and (row.get("live_score") is not None
                                                   or row.get("backtest_oos") is not None))
    if len(_scored) > 1 and _os.environ.get("MERIDIAN_FORCE_RESEED") != "1":
        console.print(f"[red]REDDEDİLDİ: karnede SKOR TAŞIYAN {len(_scored)} sürüm var (öğrenme "
                      f"geçmişi: {_scored}). Replay bunu siler. Bilerek istiyorsan "
                      f"MERIDIAN_FORCE_RESEED=1 ile çalıştır.[/red]")
        return {"error": "scoreboard_history_present", "versions": _scored}
    if _vers:                                   # zorlansa bile YOK ETME: önce arşivle
        _stamp = memory.now_iso().replace(":", "").replace("-", "")
        # H9 (kapı-dışı taşıma): düz `Path.write_text` KIRPMA sınıfıydı (yarı-yazımı okuyucu boş
        # arşiv sanardı). TEK KAPIdan geç — atomik+fsync+flock; kapı `history/` dizinini kendi kurar
        # (eski açık `config.HISTORY.mkdir` artık gereksiz). `ensure_ascii=False` biçimi KORUNUR: bu
        # bir KURTARMA arşividir (okuyucu = operatör; alttaki console satırı yolunu verir), baytları
        # aynen kalmalı — `write_json` ensure_ascii=True yazıp arşivi sessizce değiştirirdi.
        store.write_text(f"history/scoreboard-{_stamp}.json",
                         __import__("json").dumps(_sb, ensure_ascii=False, indent=2))
        console.print(f"[yellow]eski karne arşivlendi: history/scoreboard-{_stamp}.json[/yellow]")

    goal = config.goal()
    strat = bootstrap_v01()
    params = strat["params"]
    version = int(strat.get("version", 1))

    console.print(f"[cyan]loading real bars for the replay universe ({dataset.FETCH_START}..{dataset.FETCH_END})[/cyan]")
    bars, index = dataset.load()
    console.print(f"[cyan]replaying {start} → {end} through strategy.py + broker.py[/cyan]")
    # Tohumlanan plan defteri, CANLI döngünün ürettiğiyle AYNI şemayı taşımalı: karar ağacı dahil
    # (ikinci tur denetimi, 2026-07-21 — pano "neden GO verdi?" tablosu 144 satırın 144'ünde boştu).
    res = backtest.replay(params, bars, index, goal, start, end, strategy_version=version,
                          with_gate_detail=True)

    # write trades + equity
    # KAYNAK DAMGASI (BT-1, 2026-07-31): TOHUM yolunun yazımı burasıdır ve defterin TAMAMINI tek
    # seferde ezer. Damgasız bırakıldığında `learning_scorecard`/skor kalibrasyonu/alfa-beta bu
    # satırları canlı kanıt sanıyordu — oysa bunlar BUGÜNKÜ evrenle (survivorship) koşturulmuş bir
    # simülasyonun çıktısı. Sıradaki `equity_curve.json` yazımı bu toplu yazımın ZAMAN İMZASIDIR;
    # `ledgerstamp.seed_boundary()` geriye dönük sınırı tam olarak o çiftten ölçer — bu iki satırın
    # ARDIŞIKLIĞI bozulursa o ölçüm de bozulur.
    #   ↑ ARTIK BÖYLE DEĞİL (2026-08-14, v245-D; cümle tarihçe için duruyor, YANLIŞLANDI).
    #   `ledgerstamp.seed_boundary()` sınırı BU ÇİFTTEN ÖLÇMÜYOR ve eğrinin son noktasından hiç
    #   okumuyor: sıra (1) eğri zarfındaki son reset işaretinin DONMUŞ `egri_son_nokta` alanı,
    #   (2) yedek yol olarak `trades.jsonl` satırlarındaki `replay_seed` damgalarının en geç
    #   `ts_close`u; eğrinin güncel son noktası rapora yalnız BİLGİ olarak girer ("imza sınırı
    #   BELİRLEMEZ"). Değişimin sebebi: eğrinin tek yazarı artık bu blok değil —
    #   `loop._persist_equity_point` her seans sonunda eğriye nokta ekliyor (bacak-2), yani son
    #   noktadan okunan bir sınır her gün bugüne kayardı (ledgerstamp modül başlığı bu vakayı
    #   ölçümüyle anlatıyor: tohum 2026-08-13'te yenilendi, eğri 2026-07-20'de duruyordu).
    #   ARDIŞIKLIK YİNE DE ANLAMLI, AMA BAŞKA BİR ŞEY İÇİN: iki dosyanın mtime farkı
    #   `ledgerstamp._toplu_yazim_olculebilir` + `BULK_WRITE_TOLERANCE_S` ile bir TOPLU YAZIM
    #   İMZASI üretir ve rapora teşhis olarak girer. Yani bu iki satır ayrılırsa SINIR ölçümü
    #   değil, TEŞHİS zayıflar — ve aşağıdaki kilit gerekçesi (tek sıraya alma) aynen geçerlidir.
    #   YAN ETKİ BEYANI (A17, sessiz bırakılmıyor): bu düzeltme aşağıdaki iki yazımı ~13 satır
    #   aşağı kaydırdı, dolayısıyla `ledgerstamp.py`nin `run.py:203`/`run.py:204` SATIR çapaları
    #   bayatladı (metin çapaları — alıntıladıkları kod satırları — geçerli). O dosya bu turun
    #   dosya sınırının DIŞINDA, düzeltme sahibine devredildi; `ledgerstamp.py:82`nin
    #   "run.py:157 ve 158" çapası zaten bu turdan ÖNCE de bayattı. DERS: satır-numarası çapası,
    #   BAŞKA bir dosyadaki yorum düzenlemesini sessizce yük taşıyan bir işlem hâline getirir.
    # KİLİT (B3): iki yazım ARDIŞIK kalmalı (yukarıdaki gerekçe) ve ikisi de defterin tamamını
    # ezer — kilit ikisini tek sıraya alır, aradaki adım hâlâ tek bir sözlük kurmaktır.
    with store.file_lock("trades.jsonl"), store.file_lock("equity_curve.json"):
        store.write_jsonl("trades.jsonl", ledgerstamp.stamp_rows(res.trades, ledgerstamp.REPLAY_SEED))
        store.write_json("equity_curve.json", {"version": version, "points": res.equity})
    detail = res.detail(goal)
    # PROVENANS'I KORU (2026-07-22): re-seed karneyi sıfırdan kuruyordu ve aynı sürümde duran
    # operatör kararının kaydını (source=operator_override) siliyordu — karar strategy.yaml'da hâlâ
    # yürürlükteydi ama defterde görünmez oluyordu. Arşivlenen eski karnedeki aynı sürümün
    # source/note alanları taşınır; kanıt yeniden üretilir ama KARARIN İZİ kaybolmaz.
    # SOYAĞACI DA KORUNUR (2026-07-22, öğrenme-döngüsü denetimi kusur #3): `parent` sabit `None`
    # yazılıyor ve EBEVEYN SATIRI tamamen düşürülüyordu. `rollback.evaluate_outcomes` ebeveyn skorunu
    # karneden okur; ebeveyn satırı yoksa `par_score=None` ve döngü SESSİZCE `return None` eder —
    # her turda, kalıcı olarak. Yani re-seed, öğrenme döngüsünü kapatan şeyin ta kendisiydi.
    # Kanıt (skor/işlem sayısı) yeniden üretilir; SOYAĞACI ise kanıt değil KARAR geçmişidir, taşınır.
    _vers_prev = (_sb.get("versions") or {})
    _prev_row = (_vers_prev.get(str(version)) or {})
    # SOYAĞACININ İKİNCİ KAYNAĞI (2026-07-26): karne satırında `parent` alanı HİÇ bulunmayabilir —
    # canlı defterde bugün tam olarak bu vardı (v4 satırı `parent: null`, source=operator_override).
    # O hâlde ham `None`u taşımak soyağacını sessizce koparır ve aşağıdaki ata yürüyüşü hiç dönmez.
    # strategy.yaml ebeveyni BİLİYOR; soyağacı kanıt değil KARAR geçmişidir, o yüzden taşınır.
    # Düşüş sessiz olamaz: hangi kaynaktan geldiği kayda geçer.
    _par = _prev_row.get("parent")
    if _par is None:
        _par = strat.get("parent")
        if _par is not None:
            from . import obs
            obs.log("reseed_parent_from_strategy", version=version, parent=_par,
                    detail="karne satırında ebeveyn yoktu; strategy.yaml'daki soy kaydı taşındı — "
                           "aksi hâlde ata satırı hiç kurulmaz ve öğrenme döngüsü kilitli kalır")
    _row = {"params": params, "parent": _par, "live_score": detail["score"],
            "backtest_full": detail, "n_trades": len(res.trades), "live_since": memory.now_iso()}
    for _k in ("source", "note", "changed_variable", "backtest_oos", "promoted", "rolled_back"):
        if _prev_row.get(_k) is not None:
            _row[_k] = _prev_row[_k]
    _new_vers = {str(version): _row}
    # ATA ZİNCİRİNDE NE TAŞINIR — YORUM GERÇEĞE UYDURULDU (2026-07-26; eskisi kodu YANLIŞ anlatıyordu
    # ve "skor taşınmaz" diyordu):
    #   * SOYAĞACI/KARAR alanları (`params`, `parent`, `source`, `note`, `changed_variable`,
    #     `promoted`, `rolled_back`, `live_since`) — bunlar kanıt değil KARAR geçmişidir, re-seed
    #     bunları yeniden üretemez, o yüzden arşivden taşınır.
    #   * SKOR alanları (`live_score`, `backtest_oos`, `n_trades`) da BİLEREK taşınır: taşınmazsa
    #     `rollback.evaluate_outcomes` ebeveyn tabanını okuyamaz ve öğrenme döngüsü her turda
    #     `no_parent_score` ile sessizce açık kalır — kusurun kendisi buydu.
    #   * `backtest_full` taşınMAZ: ağır ve tamamen türetilebilir bir ayrıntı defteridir; tabanı
    #     okuyan hiçbir tüketici ona bakmaz.
    # UYARI (okuyucuya): taşınan skorlar YENİDEN HESAPLANMAMIŞTIR — ESKİ işlem popülasyonuna aittir.
    # Re-seed işlem defterini değiştirdiği için ata satırının skoru artık güncel defterle ölçülmüş
    # değildir; taban olarak kullanılabilir ama "bugünün verisiyle doğrulanmış" diye okunamaz.
    _seen, _p = {str(version)}, _par
    while _p is not None and str(_p) not in _seen:
        _pr = _vers_prev.get(str(_p)) or {}
        _anc = {k: v for k, v in _pr.items()
                if k in ("params", "parent", "source", "note", "changed_variable",
                         "backtest_oos", "live_score", "n_trades", "promoted",
                         "rolled_back", "live_since")}
        if not _anc:
            # ATA SATIRI KARNEDE HİÇ YOK (canlı hâl: v3). history anlık görüntüsü kararı hâlâ
            # taşıyor — YALNIZ onu kurtar. HİÇBİR SKOR ALANI YAZILMAZ: yeniden hesaplanmamış bir
            # sayı kanıt sayılamaz. Boş skorlu bir ata satırı "ölçemedim"i dürüstçe taşır; uydurulmuş
            # bir taban ise geri-alma kararını zehirler (v4 canlıyken v3'e dönüş demektir).
            _anc = _ancestor_from_history(_p)
        _new_vers[str(_p)] = _anc
        _seen.add(str(_p))
        _p = _anc.get("parent")
    if len(_new_vers) > 1:
        console.print(f"[cyan]soyağacı korundu: {sorted(_new_vers)} (rollback ebeveyn skorunu okuyabilir)[/cyan]")
    with store.file_lock("scoreboard.json"):    # B3: karneye üç ayrı yol yazıyor (bkz. versioning.py)
        store.write_json("scoreboard.json", {"current_version": version, "versions": _new_vers})

    # dated signal history for the Signals page — the real plans/candidates the replay produced.
    # PLAN DEFTERİ İŞLEM DEFTERİNİ TAŞIMAK ZORUNDA (2026-07-22, `eleme` dedektörü yakaladı):
    # eskiden son 300 plan yazılıyordu; işlemler 2023'ten başladığı için 129 işlemin 101'i artık var
    # olmayan bir plana işaret ediyordu. Sonuç sessizdi — LLM görüş kalibrasyonu ve gölge modelin
    # terfi ölçümü her turda satırların %78'ini birleştiremeyip düşürüyor, dışarıdan "veri
    # birikmemiş" gibi görünüyordu. Son 300'e ek olarak İŞLEME DÖNÜŞEN her plan korunur.
    _plans = res.plan_log or []
    _need = {t.get("plan_id") for t in res.trades if t.get("plan_id")}
    _keep = _plans[-300:]
    _have = {p.get("id") for p in _keep}
    _keep = [p for p in _plans if p.get("id") in _need and p.get("id") not in _have] + _keep
    store.write_jsonl("candidates.jsonl", (res.candidate_log or [])[-300:])
    with store.file_lock("trade_plans.jsonl"):  # B3: merge_dated_jsonl/update_jsonl ile aynı sıra
        store.write_jsonl("trade_plans.jsonl", _keep)

    # KİTABI DA YENİDEN KUR (2026-07-22 bulgusu — `yeniden_hesap` dedektörü yakaladı):
    # replay, trades/equity/scoreboard'u yeniden yazıyordu ama portfolio.json'a DOKUNMUYORDU.
    # Son döngü kitabı tazeleyecekti; ancak kitap replay bitişinden İLERİ bir tarihteyse geriye-döngü
    # koruması onu haklı olarak reddediyor ve kitap ESKİ kalıyor. Sonuç sessiz ve tehlikeli:
    # panoda nakit 100.000$ görünürken yeniden oynatılan defter 6.232$ kaybetmiş oluyordu; sermaye
    # eğrisi ile kitap birbirini tutmuyordu ve hiçbir istisna fırlamıyordu.
    # Re-seed tanımı gereği kitabı sıfırdan kurar — o yüzden kitap da tohumlanan deftere hizalanır.
    _reset_book_to(res, end)
    # final-day regime + a continuous live portfolio via one cycle on the last replay date
    loop.daily_cycle(bars, index, on_date=end)

    # seed lessons + heartbeat
    memory.distill_lessons(trade_stats={
        "n_trades": len(res.trades), "score": detail["score"], "sharpe": detail.get("sharpe"),
        "win_rate": detail.get("win_rate"), "max_drawdown": detail.get("max_drawdown"),
    })
    health.write_heartbeat(version=version, mode=config.MODE, replay_seeded=True,
                           n_trades=len(res.trades), score=detail["score"])
    # C18 ÜRETİM OKUYUCUSU (YASA 6, 2026-08-02): iki-motor turu `BacktestResult.entry_rejects`i
    # ÜRETTİ ama hiçbir üretim yolu onu BASMIYORDU. Yazılıp okunmayan bir sayaç, hiç ölçülmemiş
    # sayaçla aynı şeydir — ve bu sayacın söylediği şey tam olarak turun bulgusudur: replay artık
    # canlının REDDEDECEĞİ dolumları yazmıyor, kaçan dolumları SAYIYOR. Operatör re-seed bitiminde
    # tek satırda görür; sayı beklenmedik biçimde 0 ise bu da bir bulgudur (limit fiilen bağlamıyor).
    # SIFIR DA BASILIR: "ölçüldü ve sıfır" ile "hiç ölçülmedi" ayrı cümlelerdir (UYDURMA YASAĞI'nın
    # ikiz maddesi) — o yüzden None ayrı dala düşer.
    _rej = res.entry_rejects
    if _rej is None:
        console.print("[yellow]giriş retleri: ÖLÇÜLEMEDİ — replay ret sayacı yazmadı "
                      "(BacktestResult.entry_rejects=None)[/yellow]")
    else:
        _diger = " · ".join(f"{k}={v}" for k, v in sorted(_rej.items())
                            if k != BR.EV_MISSED_LIMIT)
        console.print(f"[cyan]giriş retleri: {BR.EV_MISSED_LIMIT}="
                      f"{int(_rej.get(BR.EV_MISSED_LIMIT, 0))}"
                      + (f" · {_diger}" if _diger else " (başka ret sınıfı yok)") + "[/cyan]")
    console.print(f"[green]seeded state: {len(res.trades)} trades, score={detail['score']}, "
                  f"final_equity={res.equity[-1][1] if res.equity else None}[/green]")
    return {"trades": len(res.trades), "detail": detail}


def once() -> dict:
    bootstrap_v01()
    bars, index = dataset.load()
    summary = loop.daily_cycle(bars, index)
    # TEK ATIŞLIK KOŞU İKİNCİ GÖRÜŞÜ BEKLEMELİ (2026-07-22): danışma katmanı daemon thread'te koşar;
    # uzun ömürlü zamanlayıcıda sorun değil ama `--once` süreci hemen çıkıyor ve thread öldürülüyordu.
    # Sonuç sessizdi: o seans hiç görüş almıyor, panoda bir hafta önceki görüş duruyordu.
    for _t in __import__("threading").enumerate():
        if _t.name == "candidate-review" and _t.is_alive():
            console.print("[cyan]LLM ikinci görüşü bekleniyor…[/cyan]")
            _t.join(timeout=600)
    console.print(f"[green]live cycle: {summary}[/green]")
    return summary


# KANONİK 24/7 YOL — tek cümle, tek yer. Dockerfile/compose/README/servis birimleri bunu anlatır;
# metin burada durur ki dört ayrı yerde dört ayrı hâle sürüklenmesin.
KADANS_YOLU = (
    "24/7 kadans bu süreçte DEĞİL: `MERIDIAN_AUTOSTART_CYCLE=1 uvicorn meridian.api:app` "
    "(api süreç-içi `scheduler.start()` bağlar). Yerelde `./serve.sh`; A1'de "
    "`systemctl start meridian` (deploy/oracle-a1/meridian.service).")


def worker(poll_seconds: int = 60) -> None:
    """EMEKLİ (C3, 2026-08-02) — kadans KOŞMAZ, çağıranı zamanlayıcı yoluna YÖNLENDİRİR.

    Gerekçe ve geri-alınabilirlik notu modül docstring'indedir ("İki kadans yasası tek depoda
    yaşayamaz"). Burada yalnız BİÇİM açıklanır:

    SESSİZCE DÖNMEZ, YÜKSEK SESLE REDDEDER. Bu fonksiyonu çağıran her yol (`python -m meridian.run`,
    eski Dockerfile CMD'i, eski compose `command`ı) bir 24/7 worker BAŞLATTIĞINI sanır. Sessiz bir
    `return`, "worker koştu ve hemen çıktı" gibi görünürdü — `restart: unless-stopped` altında bu,
    hiçbir kadans koşmadan sağlıklı görünen sonsuz bir yeniden başlatma döngüsüdür: emekli ettiğimiz
    kusur sınıfının (koşmayan mekanizma, sessiz sapma) aynısını başka kapıdan geri getirirdi.
    `SystemExit(2)` yanlış komutu operatörün önünde tutar ve süpervizöre de sıfır-dışı kod verir.

    `poll_seconds` imzada KALIR: `main()` onu `--poll`dan geçirir ve reddedilen çağrının hangi
    niyetle yapıldığı (bir poll döngüsü bekleniyordu) olay kaydına yazılır."""
    from . import obs
    try:
        obs.warn("retired_worker_invoked", poll_seconds=int(poll_seconds), detail=KADANS_YOLU)
    except Exception:  # sessiz-yutma: kayıt kanalı düştü; RET KARARI aşağıdaki SystemExit ile ZATEN uygulanıyor ve gerekçe konsola basıldı — kayıt denemesi reddi geri alamaz
        pass
    console.print("[red]REDDEDİLDİ: `run.worker()` EMEKLİ (C3, 2026-08-02) — ikinci bir kadans "
                  "uygulamasıydı, üretimde hiç koşmadı ve düzeltilmiş üç kusuru taşıyordu.[/red]")
    console.print(f"[yellow]{KADANS_YOLU}[/yellow]")
    console.print("[yellow]Tek seferlik bir seans için: python -m meridian.run --once[/yellow]")
    raise SystemExit(2)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Meridian worker")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--replay", type=str, help="START:END, e.g. 2023-01-01:2024-12-31")
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--cf-backfill", type=str, metavar="START:END",
                    help="karşı-olgusal defteri tarihten doldur (kanıt bootstrap); ör. 2022-01-01:2026-07-17")
    ap.add_argument("--parent-baseline", action="store_true",
                    help="canlı sürümün EBEVEYN tabanını walk-forward'dan ÖLÇ (varsayılan: hiçbir yere yazmaz)")
    ap.add_argument("--publish", action="store_true",
                    help="--parent-baseline ölçümünü karneye YAZ — ölçmek yayınlamak değildir, ayrı karar")
    # `--poll` bayrağı DURUYOR ama artık bir döngü beslemiyor: bayraklı çağrı emekli `worker()`a
    # düşer ve yönlendirmeyle reddedilir. Bayrağı sessizce KALDIRMAK, onu geçen eski bir betiği
    # "bilinmeyen argüman" hatasıyla düşürürdü — hata mesajı da yanlış yeri gösterirdi.
    ap.add_argument("--poll", type=int, default=60,
                    help="(EMEKLİ) eski 24/7 döngünün poll aralığı — kadans artık zamanlayıcıda")
    args = ap.parse_args(argv)

    if args.parent_baseline:
        from . import baseline
        out = baseline.measure_parent_baseline(publish=args.publish)
        console.print(f"[cyan]ebeveyn tabanı: {out}[/cyan]")
        return out
    if args.cf_backfill:
        from . import cf_backfill
        start, end = args.cf_backfill.split(":")
        console.print(f"[cyan]cf-tarih bootstrap {start} → {end} (ağ yok; önbellek CSV'leri)[/cyan]")
        out = cf_backfill.run(start=start or None, end=end or None)
        console.print(f"[green]cf backfill: {out}[/green]")
        return out
    if args.replay:
        start, end = args.replay.split(":")
        return replay_seed(start, end)
    if args.once:
        return once()
    worker(poll_seconds=args.poll)


if __name__ == "__main__":
    main()
