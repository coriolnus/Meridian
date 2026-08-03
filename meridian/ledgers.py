"""ledgers.py — DEFTER SÖZLEŞMESİ (2026-07-21).

NEDEN VAR: 2026-07-21'de tek günde yedi hata çıktı ve altısı aynı kökten geliyordu — **her defteri
2-3 modül yazıyor, 5-8 modül okuyor, ve arada yazılı bir anlaşma yok.** Somut sonuçlar:

  * `trades.jsonl` satırlarında `setup`/`score` YOKTU (eski şemayla tohumlanmış defter, güncel kod)
    → skor kalibrasyonu ve gölge model 90 gerçek işlemin 90'ını da SESSİZCE eledi ("gerçek 0").
  * `plan_id` iki şemadaydı: backtest `P00140`, canlı döngü `P-{tarih}-{ticker}`
    → `cf_fidelity` — simülasyonun gerçeğe uyup uymadığını ölçen TEK mekanizma — hiç kurulamadı.
  * cf satırları `r_multiple_expected`'i `rr_expected` diye YENİDEN ADLANDIRIYORDU
    → yaması olan tüketici çalıştı, olmayan sessizce satır eledi.
  * `gate_checks` yalnız canlı döngüde üretiliyordu → panonun karar-ağacı tablosu 144/144 boştu.

Hiçbiri istisna fırlatmadı: `.get()` None döner, satır atlanır, sayı küçülür, kimse fark etmez.
800 testin hiçbiri yakalamadı çünkü testler KENDİ fixture'larını üretiyor — gerçek defterle
konuşmuyorlar.

SÖZLEŞME NE YAPAR: her defter için (a) zorunlu alanlar, (b) İZİNLİ yazarlar, (c) birleştirme
anahtarı ve formatı, (d) kanonik ad ↔ beyan edilmiş takma adlar. Üç yerden doğrulanır:
  1. üretici testleri — modül GERÇEK bir satır üretir, sözleşmeye uyar mı?
  2. statik tarama    — beyan edilmemiş bir yazar belirdi mi?
  3. canlı dedektör   — diskteki satırlar sözleşmeye uyuyor mu? (watchdog.parity_report)

Sözleşme KARAR VERMEZ; yalnız "bu defter söz verdiği şeyi taşımıyor" der.
"""
from __future__ import annotations

import ast
import pathlib
import re
from dataclasses import dataclass, field

from . import store

# Plan kimliği: canlı döngü, backtest ve cf_backfill'in ORTAK anahtarı. Bu formatın dışındaki bir
# kimlik, cf↔gerçek birleştirmesini imkânsız kılar (2026-07-21'de tam olarak bu oldu).
PLAN_ID_RE = re.compile(r"^P-\d{4}-\d{2}-\d{2}-.+")
CF_ID_RE = re.compile(r"^CF-\d{4}-\d{2}-\d{2}-.+")


@dataclass(frozen=True)
class Contract:
    """Bir defterin yazılı sözleşmesi."""
    required: tuple[str, ...]                    # her satırda BULUNMASI gereken alanlar
    writers: tuple[str, ...]                     # bu deftere yazmasına İZİN verilen modüller
    key: str | None = None                       # birleştirme anahtarı alanı
    key_format: re.Pattern | None = None         # ve beklenen biçimi
    aliases: tuple[tuple[str, str], ...] = ()    # (kanonik, beyan edilmiş takma ad)
    consumers: tuple[str, ...] = ()              # belgeleme: kim okuyor (taramaya girmez)
    note: str = ""


CONTRACTS: dict[str, Contract] = {
    "trades.jsonl": Contract(
        required=("id", "ts_open", "ts_close", "ticker", "r_multiple", "pnl_dollars",
                  "plan_id", "regime", "score", "setup", "strategy_version"),
        # satırı broker üretir, loop/run diske yazar. ledgerstamp: TEK SEFERLİK migrasyon yazarı
        # (BT-1, 2026-07-31) — hiçbir satır eklemez/silmez, YALNIZ `kaynak` damgasını basar ve
        # elle koşulur (kuru koşu varsayılan, canlı-süreç kilidi). Beyan edilmeden bırakılsaydı
        # bu sözleşmenin var olma sebebi olan "kimsenin haberi olmadan ikinci bir yazar"
        # sınıfının yeni bir örneği olurdu.
        writers=("loop.py", "run.py", "ledgerstamp.py"),
        key="plan_id", key_format=PLAN_ID_RE,
        consumers=("analytics", "score", "rollback", "shadow_model", "validation_report", "api",
                   "ledgerstamp"),
        # `kaynak` BİLEREK `required` DEĞİL: migrasyon canlı deftere HENÜZ uygulanmadı (dağıtım
        # sabah, Rol 1) ve zorunlu ilan etmek, doğru olmayan bir uyumluluk iddiası yazardı.
        # Migrasyon uygulandıktan SONRA buraya taşınacak — o an `damgasiz_n == 0` ile ölçülür.
        note="score/setup olmadan skor kalibrasyonu ve gölge model satırı SESSİZCE eler; "
             "`kaynak` damgası olmadan tohum satırları canlı kanıt sanılır (BT-1)"),
    "trade_plans.jsonl": Contract(
        required=("id", "date", "ticker", "setup", "score", "entry_trigger", "stop",
                  "gate_verdict", "strategy_version"),
        writers=("loop.py", "run.py", "hermes.py"),   # hermes: LLM görüş damgası (kilitli)
        key="id", key_format=PLAN_ID_RE,
        consumers=("analytics", "shadow_model", "api", "counterfactual"),
        note="gate_checks İSTEĞE BAĞLI ama üretilirse karar ağacı panoda okunur"),
    "counterfactuals.jsonl": Contract(
        required=("id", "date", "ticker", "setup", "regime", "status"),
        # cf_backfill DOĞRUDAN yazmaz — counterfactual.collect() üzerinden geçer. Sözleşme
        # DOĞRUDAN yazarı beyan eder; aracı modülü yazar saymak taramayı gürültüye boğar.
        writers=("counterfactual.py",),
        key="id", key_format=CF_ID_RE,
        aliases=(("r_multiple_expected", "rr_expected"),),
        consumers=("arming", "analytics", "shadow_model", "selfreview"),
        note="regime '?' olabilir (rejim bilinmiyorsa) ama ALAN bulunmalı — dilimleme ona bakar"),
    # G2 ALAN ADI KANONİKLEŞTİRME (K1, 2026-07-30). 2026-07-29'da deftere üç G2 alanı eklendi
    # (`rvol20`, `mom_12_1`, `rmom`) ve ad dikişi AYNI GÜN ayrıştı: defter `mom_12_1` yazıyor
    # (strategy.py:137), component_ic raporu `mom12_1` kullanıyor (component_ic.py:102). ledgers.py
    # 2026-07-21'de TAM BU "takma ad" hastalığı için kurulmuştu, ama candidates sözleşmesi ne
    # alanları ne alias'ı beyan ediyordu — yani kurulma sebebi olan hata kendi kapsamı dışında
    # yeniden açıldı.
    #
    # KANONİK AD = DEFTERİN ADI (`mom_12_1`): sözleşmenin konusu DİSKTEKİ satırdır, ve diskte 10
    # satırda `mom_12_1` var (canlı sayım 2026-07-30: rvol20 10/2 non-null, mom_12_1 10/2,
    # rmom 10/0). component_ic'in `mom12_1`'i RAPOR tarafının yazımıdır; alias olarak beyan edilir,
    # böylece bir yazar yarın rapor yazımıyla deftere yazarsa validate_row onu SESSİZ değil İHLAL
    # olarak görür. Yeniden adlandırma bilinçli olarak YAPILMADI: iki canlı yüzey de üretimde.
    #
    # NEDEN `required` DEĞİL: 323 satırın yalnız 10'unda alanlar var (07-29 sonrası). Zorunlu
    # yapmak 313 tarihsel satırı ihlalli gösterip makullük satırını kırmızıya boyardı — dedektör
    # kurt masalı anlatırdı. Alanlar İSTEĞE BAĞLI, adı ise sözleşmeli.
    "candidates.jsonl": Contract(
        required=("date", "ticker", "score", "setup"),
        writers=("loop.py", "run.py"),
        aliases=(("mom_12_1", "mom12_1"),),
        consumers=("api",),
        note="G2 alanları (rvol20/mom_12_1/rmom) İSTEĞE BAĞLI ve BİLİNÇLİ-None olabilir: `rmom` "
             "0/323 non-null çünkü hiçbir çağıran `index_close` vermiyor (strategy.evaluate_entry) "
             "— UYDURMA YASAĞI gereği ölçülemeyen alan None kalır, doldurulmaz"),
    "hypotheses.jsonl": Contract(
        required=("id", "ts", "variable", "status"),
        # sprint.py yalnız KUM HAVUZUNDAKİ kopyayı sıfırlar (ham yol yazımı, ayrı MERIDIAN_ROOT);
        # canlı state/hypotheses.jsonl'a yazan tek modül memory'dir.
        writers=("memory.py",),
        key="id", key_format=re.compile(r"^H\d{5}$"),
        # `api` EKSİKTİ (v130): api.py:1270 bu defteri OKUYOR (pano ship geçmişi/diff şeridi) ve
        # v130'da o okuma DSR damgalarını da taşıyor — sayılmayan bir tüketici, şema kararlarında
        # hesaba katılmayan bir tüketicidir (events.jsonl'da aynı eksik aynı turda düzeltilmişti).
        consumers=("reflect", "rollback", "probgate", "analytics", "selfreview", "api"),
        note="kimlik ASLA yeniden kullanılmaz (max+1) — defter kısalsa bile. "
             "Y1 SERT KAPI DAMGALARI (DSR hard-gate turu, 2026-07-30): ship yolundan geçen satırın "
             "`backtest` sözlüğü ayrıca `ship_modu` (paper | gercek_para), `dsr_dusuk` "
             "(True/False/**None**) ve `dsr_durum` (olculdu | olculemedi) taşır; tam hüküm "
             "`dsr_hard_kapi`/`pbo_hard_kapi` altında durur. `dsr_dusuk` ÜÇ DEĞERLİDİR ve None "
             "YALNIZ `dsr_durum=olculemedi` iken gelir — ölçülmemiş bir DSR'ye False yazmak "
             "'düşük değil' demek, yani yapılmamış bir ölçümün sonucunu uydurmak olurdu. "
             "İKİ YENİ STATÜ: `rejected_by_dsr` / `rejected_by_pbo` — kapı ölçümünü GEÇEN ama "
             "doğrulama kapısında düşen adaylar; `rejected_by_backtest` kovasına KARIŞTIRILAMAZ "
             "(kapı istatistiği 'backtest neyi eliyor?' sorusunu cevaplar ve süreç reddi o soruya "
             "girmez). Damgalar ZORUNLU alan DEĞİLDİR ve olmayacaktır: v130 öncesi satırlarda "
             "yokturlar ve retro damga yasağı gereği doldurulmazlar — damgasız satır 'sert kapı "
             "öncesi' demektir"),
    # TÜKETİCİ LİSTESİ EKSİKTİ (K1, 2026-07-30): `notify.inbox` (notify.py:78) ve
    # `analytics.autonomy` devre-kesici sayacı (analytics.py:106) da bu defteri okuyor. Sözleşmenin
    # TEK işi tam olmaktır: budama/şema kararları bu listeye bakılarak verilirse, sayılmayan iki
    # okuyucu hesaba katılmaz — ve ikisi de PENCERELİ okur (4000/400 satır), yani defterin hacmi
    # onların gördüğü tarihi doğrudan belirler.
    "events.jsonl": Contract(
        required=("ts", "level", "event"),
        writers=("obs.py",),
        consumers=("api", "watchdog", "selfreview", "notify", "analytics")),
    "spend.jsonl": Contract(
        required=("ts", "model", "cost_usd"),
        writers=("spend.py",),
        consumers=("analytics", "api")),
    "pipeline_runs.jsonl": Contract(
        required=("run_id", "pipeline", "started", "status"),
        writers=("skills.py",),
        consumers=("api",)),
    # Y1 DOĞRULAMA DEFTERİ (Hafta 3a, 2026-07-30). `seri` ZORUNLU alandır çünkü defterin VAR OLMA
    # SEBEBİ odur: PBO/CSCV, N adayın AYNI zaman ızgarasındaki getirilerini ister ve serisiz bir
    # satır PBO'ya hiç giremez — yani sessizce paydadan düşer (tam olarak `trades.jsonl`ın
    # `setup`/`score` dersinin aynısı: alan yoksa tüketici satırı sessizce eler).
    # `sharpe_gozlem` de zorunlu: DSR'nin deneme-varyansı bu alandan ÖLÇÜLÜR; eksikse hesap
    # gürültülü null yaklaşımına düşer ve bunun neden olduğu görünmez kalırdı.
    # 2.4 GÖLGE-VARYANT DEFTERİ SÖZLEŞMEYE GİRİYOR (3b, 2026-07-30). Sadeleştirme turu bu defteri
    # `codelaw.DECLARED_SINKS`e SÜRELİ bir beyanla koymuştu ("pano/api tüketicisi Hafta 3b'ye
    # devredildi"). Devir BU TURDA yapıldı: tüketici artık api `/api/diagnostics` → pano gölge-varyant
    # kartı, beyan satırı KALDIRILDI. Sözleşme o devrin ikinci yarısıdır — defterin ALANLARI da
    # yazılı olmalı, yoksa `trades.jsonl`ın `setup`/`score` dersi burada yeniden yaşanır.
    # `k_variants` ZORUNLU: çoklu-karşılaştırma PAYDASIDIR ve "en iyi varyant" okuması onsuz
    # kazananın-lanetini sessizce görmezden gelir.
    "shadow_variants.jsonl": Contract(
        required=("date", "variant", "label", "knobs", "signal_n", "would_arm_n", "k_variants"),
        writers=("shadow_variants.py",),
        key=None,
        consumers=("analytics", "api", "shadow_variants"),
        note="ship yolu YOKTUR — kâğıt karar defteri; only_variant/only_live ayrışmayı taşır"),
    # H3 BİLEŞİK ÖNERİ KUYRUĞU (Hermes paketi, 2026-07-30). `composite` ZORUNLU: kuyruğun VAR OLMA
    # SEBEBİ odur ve düğme demeti olmadan satır prescreen'e hiç giremez. `status` ZORUNLU çünkü
    # kuyruğun tam-döngülü olması (pending → measuring → measured) yalnız o alanla denetlenebilir;
    # eksikse "öner→ölç→öğren" halkasının koptuğu görünmez kalır.
    # DURUM ALFABESİ TAM HÂLİ (C14, 2026-08-02): pending → measuring → measured | measure_failed
    # (+ giriş redleri: rejected_shape). `measure_failed` bir BAŞARISIZLIK KAYDIDIR, bir ara durum
    # değil: ölçüm süreci sonucu geri yazmadan öldü (pid yoklaması), guard bütün adayları reddetti ya
    # da prescreen patladı. Ayrı bir durum olmasının sebebi ölçülebilirlik: 'pending'e geri düşseydi
    # bütçe harcanmış bir deneme yeniden sıraya girer ve sayaçlar aynı fikri iki kez sayardı;
    # 'measured' olsaydı `n_olculen` sonuçsuz satırları da sayar ve halka kapanmış GÖRÜNÜRDÜ.
    # Yazan: `hermes_composite.reap_measuring` (ölü süreç) + `prescreen.kuyruk_geri_yaz` (hata dalı).
    "composite_queue.jsonl": Contract(
        required=("ts", "id", "composite", "n_knobs", "status", "source"),
        writers=("hermes_composite.py",),   # satırı guard/hermes kurar, diske bu modül yazar
        key="id",
        consumers=("analytics", "api", "loop", "hermes"),
        note="kuyruğa girmek ONAY DEĞİL ölçüm sırasıdır; k_probes alanı aşınma defteriyle aynı dil"),
    # NOUS SİSTEM-ÖNERİ DEFTERİ (Katman B, ROADMAP §3.2, 2026-07-30). Beynin MEKANİZMA düzeyindeki
    # önerileri. Zorunlu alanların her biri bir karardır ve `trades.jsonl`ın `setup`/`score` dersinin
    # doğrudan uygulanmasıdır — alan yoksa tüketici satırı SESSİZCE eler:
    #   `gozlem`         : KANIT ATIFI burada yaşar. Kalite kapısı (nous_eval.kanit_atifi) bu alanda
    #                      telemetri jetonu arar; alan boş bir satır zaten deftere girmiş olamaz.
    #   `kanit_atifi`    : kapının EŞLEŞTİRDİĞİ jetonlar. Denetlenebilirliğin kendisi — bu alan
    #                      olmadan "kanıt atfı zorunlu" iddiası doğrulanamaz bir cümledir.
    #   `sekil`          : yolu belirler (parametre → kuyruk · tasarim/cekirdek_hakkinda → rapor).
    #                      Eksikse Katman D'nin ayrımı okunamaz hâle gelir.
    #   `onerilen_olcum` : önerinin falsifiye edilebilirliği. Yoksa öneri bir temennidir.
    #   `hafta`          : `hermes_composite.week_key` ile AYNI ISO biçimi (`2026-W31`) — Katman C'nin
    #                      H4 bütçe anahtarıyla birebir aynı olmak ZORUNDA (iki damga biçimi olsaydı
    #                      yılbaşı haftasında bütçe iki kez dolardı ya da hiç dolmazdı).
    # `sekil_beyan` ve `cekirdek_isaretleri` ZORUNLU DEĞİL ama YAZILIR: modelin KENDİ etiketi ile
    # kodun türettiği şekil ayrıştığında (yani model çekirdek hakkındaki bir öneriyi "parametre" diye
    # etiketlediğinde) bu iki alan o denemenin tek kaydıdır.
    "improvement_proposals.jsonl": Contract(
        required=("ts", "id", "hafta", "alan", "gozlem", "oneri", "beklenen_etki",
                  "onerilen_olcum", "oncelik", "sekil", "kanit_atifi"),
        writers=("nous_eval.py",),
        key="id", key_format=re.compile(r"^N\d{5}$"),
        consumers=("analytics", "api", "nous_eval"),
        note="DEFTER KABUL EDİLENLERİN kaydıdır: kalite kapısında düşen öneri buraya YAZILMAZ, "
             "düşme SAYISI ve NEDENİ `nous_eval_runs.json` koşu kaydında durur ve panoda görünür. "
             "ÖNERİ UYGULAMA DEĞİLDİR: `sekil=parametre` satırları H4 bütçesi içinde composite "
             "kuyruğuna girer (`kuyruk`/`kuyruk_id` alanları o köprünün kaydı), ship yolu yine "
             "kapı + operatördür. `sekil=cekirdek_hakkinda` satırları YALNIZ rapordur ve kuyruk "
             "yolu YAPISAL olarak kapalıdır (nous_eval._kuyruga_yaz — deneme ALARM üretir). "
             "AKIBET ALANI YOKTUR ve olmayacaktır: bir önerinin akıbeti ZAMANLA değişir "
             "(pending → measuring → measured) ve deftere yazılan damga bir hafta sonra yalan "
             "söylerdi — akıbet kuyruk satırından CANLI okunur (nous_eval._akibet)"),
    "validation_ledger.jsonl": Contract(
        required=("ts", "fingerprint", "etiket", "seri", "sharpe_gozlem", "n_trials", "passes"),
        writers=("validation.py",),      # satırı reflect._gate_eval kurar, diske validation yazar
        consumers=("analytics", "api"),
        note="seri = [[kapanış_tarihi, gerçekleşen_R], ...] — PBO'nun ortak takvim ızgarası "
             "anahtarı; serisiz satır PBO paydasından SESSİZCE düşer. "
             "YASA DAMGASI (PARA-v3, 2026-07-30): satır ayrıca `yasa_surumu` (para_v3 | "
             "eski_bilesik_marj), `oos_para`/`incumbent_para` (karar skorları) ve "
             "`dd_ok`/`candidate_dd`/`incumbent_dd` (düşüş vetosu) taşır. Bunlar ZORUNLU alan "
             "DEĞİLDİR ve olmayacaktır: geçiş öncesi satırlarda yokturlar ve retro damga yasağı "
             "gereği geriye dönük doldurulmazlar — `required`a eklemek, geçmiş satırların TAMAMINI "
             "sözleşme ihlali ilan etmek olurdu. Damgasız satır 'eski bileşik yasa' demektir. "
             "DÜŞÜŞ ALANLARININ OKUNUŞU (WP-M, 2026-08-03): `dd_veto_margin` MUTLAK bir düşüş "
             "tavanı DEĞİLDİR — veto koşulu `candidate_dd > incumbent_dd + marj`, yani marj aday↔"
             "incumbent FARKINA uygulanır ve tek yönlüdür (kötüleşme RET eder, iyileşme puan "
             "kazandırmaz). Mutlak tavan AYRI bir sayıdır ve `goal.max_drawdown`dır; marj onun "
             "yarısıdır (bkz. shadowlaw.DD_VETO_MARGIN türetimi). Bir satırdaki `candidate_dd`yi "
             "tek başına marjla kıyaslayan okuma, göreli bir marjı mutlak eşik sanar. "
             "M2M İKİZİ (PARA-v3 ②, 2026-08-02 — ÖLÇÜLÜR, VETO BAĞLAMAZ): satır ayrıca "
             "`dd_mtm_durum`, `dd_mtm_bagli`, `candidate_dd_mtm`/`incumbent_dd_mtm` taşır. Alanlar "
             "YAZARDAN doğrulandı (reflect._gate_eval'in validation.record_candidate çağrısı), "
             "DİSKTEN DEĞİL: bu checkout'un 204 satırının HİÇBİRİNDE yoklar (bacak 2026-08-02'de "
             "eklendi, o tarihten sonra bu ağaçta resmî değerlendirme yazılmadı) — UYDURMA YASAĞI "
             "gereği alan adları yazım satırından alındı. BU AİLE `dd_*`IN İKİNCİ ÖLÇÜMÜ DEĞİL, "
             "BAŞKA BİR CETVELDİR: `candidate_dd` KAPANMIŞ-İŞLEM sermaye eğrisinin maks düşüşü, "
             "`candidate_dd_mtm` AYNI dilimin günlük mark-to-market eğrisininki (açık pozisyonun "
             "içeride yaşattığı acı ilkinde GÖRÜNMEZ). İki aile tek sütunda havuzlanamaz ve biri "
             "diğerinin yerine okunamaz. `dd_mtm_durum='ihlal_baglanmadi'` HÜKÜM DEĞİLDİR: marj "
             "kapanmış-işlem düşüş dağılımından türetildi, M2M dağılımının σ'sı ÖLÇÜLMEDİ — o "
             "satır 'marj M2M'den türetilseydi bu aday RET edilirdi' der ve M2M-σ ölçüm kartının "
             "ham maddesidir. `dd_mtm_bagli=False` olduğu sürece `passes` bu bacaktan ETKİLENMEZ. "
             "`dd_mtm_ok` ve `dd_mtm_beyan` YALNIZ kapı kaydındadır, BU DEFTERDE YOKTUR — onları "
             "burada arayan tüketici sessizce None okur. Bu alanlar da ZORUNLU DEĞİLDİR (2026-08-02 "
             "öncesi satırlarda yokturlar, retro damga yasağı). "
             "TÜKETİCİ UYARISI: PBO/DSR bir popülasyon ister; iki farklı `yasa_surumu` iki farklı "
             "KARAR DEĞİŞKENİdir ve tek havuzda karıştırılamaz. "
             "PENCERE DAMGASI (HOLDOUT ROTASYONU R1, 2026-07-30): satır ayrıca `pencere_id` taşır "
             "(R1 = OOS 2024-01-01→2026-04-30, holdout 2026-04-30→2026-07-30 DONMUŞ). Zorunlu alan "
             "DEĞİLDİR — R1 öncesi satırlarda yoktur ve retro damga yasağı gereği doldurulmaz; "
             "damgasız satır 'R1 öncesi (R0)' demektir. `fingerprint` alanı ZATEN bu geometrinin "
             "hash'idir (oos_erosion.fingerprint), `pencere_id` onu okunabilir kılar. "
             "İKİNCİ TÜKETİCİ UYARISI, `yasa_surumu`nunkiyle AYNI ŞEKİLDE BAĞLAYICI: iki farklı "
             "`pencere_id` (ya da iki farklı `fingerprint`) İKİ FARKLI SINAV KÂĞIDIdır. R0'da "
             "ölçülmüş p/ΔS/PARA değerleri R1 değerleriyle KARŞILAŞTIRILAMAZ ve tek PBO/DSR "
             "ızgarasında havuzlanamaz — aşınma sayacı da her yeni pencerede sıfırdan başlar, yani "
             "düşük bir R1 sayacı 'aşınma yok' demek değil 'R1'de henüz ölçülmedi' demektir. "
             "HABERSİZ KIYAS YASAK; R0 kayıtları silinmedi, `arsiv_R0` işareti aldı "
             "(oos_erosion.arsivle — içerik değişmez, yalnız etiket eklenir)"),
    # İKİ İNTRADAY DEFTERİ SÖZLEŞMEYE GİRİYOR (K1, 2026-07-30). Faz 4a/4b defterleri bugüne kadar
    # sözleşme yasasının TAMAMEN dışındaydı: `watchdog.parity_report` yalnız CONTRACTS'ı gezer, ve
    # CONTRACTS 8 eski defterle sınırlıydı. Yani 2026-07-21'de yedi hatayı doğuran "sözleşmesiz
    # defter" deseni en YENİ iki defterde aynen yeniden açıktı.
    #
    # ÜÇ DAMGA — İDDİANIN CANLI DENETÇİSİ: intraday_shadow.py:241 "as_of >= close_ts sonradan
    # denetlenebilir" diyor, ama tek denetim fixture'lı birim testlerdi; diskteki GERÇEK satırlara
    # bakan hiçbir canlı dedektör yoktu. Üç damga (`decision_as_of`, `bar_t`, `close_ts`) burada
    # ZORUNLU alan olur — eksikse look-ahead denetimi hiç yapılamaz — ve karşılaştırmayı
    # watchdog.intraday_stamp_report() yapar.
    #
    # ALANLAR YAZARDAN DOĞRULANDI, DİSKTEN DEĞİL: iki defter de henüz 0 satır (bilinen açlık —
    # 4a saha 0 satır, gölge hiç satır görmedi). UYDURMA YASAĞI gereği kaynak uydurulmaz: adlar
    # intraday_cycle.py:125-131 ve intraday_shadow.py:230-243 yazım satırlarından alındı.
    "intraday_decisions.jsonl": Contract(
        required=("ts", "ticker", "source", "decision_as_of", "bar_t", "close_ts",
                  "admissible_bars", "fired"),
        writers=("intraday_cycle.py",),
        consumers=("api", "watchdog"),
        note="4a GÖZLEM defteri — sıfır yetki. `fired`/`entry_trigger` None OLABİLİR (plan yok ya "
             "da biçimsiz entry_trigger) ama ALAN bulunmalı; üç damga look-ahead denetiminin "
             "girdisidir (watchdog.intraday_stamp_report)"),
    "intraday_shadow_orders.jsonl": Contract(
        required=("plan_id", "ticker", "date", "status", "decision_as_of", "bar_t", "close_ts",
                  "sim_fill", "gate_inputs_as_of"),
        writers=("intraday_shadow.py",),
        key="plan_id", key_format=PLAN_ID_RE,
        consumers=("api", "watchdog"),
        note="4b GÖLGE defteri — emir yolu BİLEREK yok. `gate_inputs_as_of` zorunlu: kapı "
             "girdilerinin hangi ana ait olduğu yazılmazsa 'look-ahead yok' iddiası "
             "DOĞRULANAMAZ (bugüne kadar repo genelinde tek geçtiği yer yazıldığı satırdı)"),
}

_WRITE_CALLS = ("write_json", "write_jsonl", "append_jsonl", "merge_dated_jsonl",
                "update_json", "update_jsonl")


def validate_row(ledger: str, row: dict) -> list[str]:
    """Tek satırın sözleşme ihlalleri. Boş liste = uyumlu."""
    c = CONTRACTS.get(ledger)
    if not c or not isinstance(row, dict):
        return []
    out = [f"eksik alan: {k}" for k in c.required if k not in row]
    # TAKMA AD, KANONİK ADIN YERİNİ ALAMAZ (2026-07-22, mutasyon koşumu yakaladı): sözleşme takma
    # adı yalnız GERİYE DÖNÜK uyumluluk için tanır. Satır sadece eski adı taşıyorsa, yaması olmayan
    # her tüketici onu sessizce eler — mutasyon "yeniden adlandır" tam bu yüzden görünmezdi.
    for canonical, alias in c.aliases:
        if canonical not in row and alias in row:
            out.append(f"kanonik ad eksik: {canonical} (yalnız takma ad {alias} var)")
    if c.key and c.key_format and row.get(c.key) is not None:
        if not c.key_format.match(str(row[c.key])):
            out.append(f"anahtar biçimi tutmuyor: {c.key}={row[c.key]!r}")
    return out


def validate_live(ledger: str, sample: int = 200) -> dict:
    """Diskteki satırlar sözleşmeye uyuyor mu? (canlı dedektörün okuduğu)"""
    rows = store.read_jsonl(ledger, limit=sample)
    if not rows:
        return {"ledger": ledger, "rows": 0, "ok": True, "violations": {}, "note": "defter boş"}
    viol: dict[str, int] = {}
    for r in rows:
        for v in validate_row(ledger, r):
            viol[v.split("=")[0]] = viol.get(v.split("=")[0], 0) + 1
    return {"ledger": ledger, "rows": len(rows), "ok": not viol, "violations": viol}


UNPARSED: dict[str, str] = {}    # taranamayan modüller — sıfır-ihlal iddiasının dürüstlük şartı


_WRITERS_CACHE: dict = {}


def _src_stamp(root: str) -> tuple:
    """Kaynak ağacının parmak izi — bkz. codelaw._src_stamp, aynı gerekçe."""
    ps = sorted(pathlib.Path(root).rglob("*.py"))
    return (len(ps), max((q.stat().st_mtime_ns for q in ps), default=0))


def declared_writers(root: str = "meridian") -> dict[str, set]:
    """Statik tarama: hangi modül hangi deftere YAZIYOR (sabit adları da çözer).

    ÖNBELLEKLİ (2026-07-28): tüm kaynağı ast ile ayrıştırır ve /api/diagnostics'ten her
    Operasyon açılışında iki kez çağrılıyordu (ölçüm: 0,87 sn). Sonuç yalnız kaynağa bağlı;
    damga kaynak mtime'ıdır, kod değişince önbellek kendiliğinden düşer."""
    _key = (root, _src_stamp(root))
    _hit = _WRITERS_CACHE.get(_key)
    if _hit is not None:
        return {k: set(v) for k, v in _hit.items()}   # çağıran set'leri mutasyona uğratabilir

    out: dict[str, set] = {}
    for f in pathlib.Path(root).rglob("*.py"):
        try:
            tree = ast.parse(f.read_text())
        except (SyntaxError, OSError) as e:
            # Ayrıştırılamayan modül taramadan SESSİZCE düşerse, o modülün beyansız yazarı da
            # düşer: "0 ihlal" iddiası, atlanan dosyalar yüzünden BOŞ bir iddia olur. Körlük
            # kaydedilir ve report() tarafından dışarı verilir.
            UNPARSED[f.name] = f"{type(e).__name__}: {e}"
            continue
        consts = {}
        for n in tree.body:
            if isinstance(n, ast.Assign) and isinstance(n.value, ast.Constant) \
                    and isinstance(n.value.value, str):
                for t in n.targets:
                    if isinstance(t, ast.Name):
                        consts[t.id] = n.value.value
            elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name) \
                    and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str):
                consts[n.target.id] = n.value.value
        for n in ast.walk(tree):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
                    and n.func.attr in _WRITE_CALLS and n.args:
                a = n.args[0]
                name = (a.value if isinstance(a, ast.Constant) and isinstance(a.value, str)
                        else consts.get(a.id) if isinstance(a, ast.Name) else None)
                if name in CONTRACTS:
                    out.setdefault(name, set()).add(f.name)
    _WRITERS_CACHE.clear()
    _WRITERS_CACHE[_key] = out
    return {k: set(v) for k, v in out.items()}


def writer_violations() -> dict[str, dict]:
    """Beyan edilmemiş yazar var mı? (Guard'ın ikinci risk zarfı, mirror_stream'in ikinci iptal
    kopyası — hepsi 'kimsenin haberi olmadan ikinci bir yazar/uygulama' sınıfındandı.)"""
    actual = declared_writers()
    out = {}
    for ledger, c in CONTRACTS.items():
        have, want = actual.get(ledger, set()), set(c.writers)
        extra, missing = have - want, want - have
        if extra or missing:
            out[ledger] = {"beyan_edilmemis_yazar": sorted(extra),
                           "beyan_edilip_yazmayan": sorted(missing)}
    return out


def report() -> dict:
    """Sözleşmenin bütün durumu — pano + makullük dedektörü buradan okur."""
    live = {name: validate_live(name) for name in CONTRACTS}
    wv = writer_violations()
    bad = [v for v in live.values() if not v["ok"]]
    return {"ledgers": len(CONTRACTS), "compliant": len(live) - len(bad),
            "violating": [v["ledger"] for v in bad], "detail": live,
            "writer_violations": wv, "unparsed": dict(UNPARSED),
            # taranamayan modül varsa "yazar ihlali yok" iddiası eksik taramaya dayanıyor demektir
            "ok": not bad and not wv and not UNPARSED}
