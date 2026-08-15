"""sermaye.py — antrenman tohumunun (replay_seed) K/Z'sini canlı-kâğıt sermayeden ayrıştıran, kuru-koşu-varsayılanlı reset aracı.

NE YAPAR. Kitabın (portfolio.json) dört sermaye alanını (cash / realized_pnl / day_start_equity /
peak_equity) canlı-kâğıt çağ için START_EQUITY tabanına taşır; ayrıştırmayı SİLEREK değil BEYAN
EDEREK yapar — kitapta `sermaye_resetleri` kaydı, eğri zarfında `reset_isaretleri` işareti, olay
defterinde `paper_equity_reset` satırı. Defterlere dokunmaz; mutabakat kimlikleri ofsetle ölçmeye
devam eder. Panonun ve CLI'nin okuduğu tek köken yüzeyi `koken()`tir.

NEDEN VAR. Defter-köken damgalama turu (`ledgerstamp`: live_paper / replay_seed / belirsiz)
defterin KÖKENİNİ ayırdı ama NAKDİ ayırmadı. Ölçülen hâl (canlı state, reset öncesi):

    portfolio.json  cash = 94.457,91$   realized_pnl = −5.542,09$   positions = {}
    trades.jsonl    95 satır, ledgerstamp 95/95 = replay_seed      canlı-kâğıt işlem = 0

Yani kitaptaki 5.542,09$'lık kayıp GERÇEK bir zarar DEĞİL: `run.replay_seed`in geçmiş barlar
üzerinde koşturduğu bir SİMÜLASYONUN çıktısı (üstelik bugünkü evrenle, survivorship'li). Pano bu
sayıya "Sermaye" diyordu ve iki ayrı yalan söylüyordu:

  1. GÖSTERİM: operatör "sistem 5.542$ kaybetti" diye okuyor; gerçekte canlı-kâğıt çağ hiç işlem
     yapmadı. Kaybın kendisi bir antrenman artefaktıdır.
  2. DAVRANIŞ (asıl zararlı olan): boyutlandırma tabanı `broker.equity()` = start_equity +
     realized_pnl'dir. `loop._load_broker` her turda `PaperBroker(START_EQUITY, …)` kurar ve
     üstüne diskten `realized_pnl`i basar — yani antrenman zararı, GERÇEK-CANLI çağın pozisyon
     boyutlarını her gün kısıyordu. `peak_equity` = 102.520,45$ ise aynı simülasyonun tepesidir ve
     de-risk rampası düşüşü ORADAN ölçer: canlı çağ, hiç yaşamadığı bir düşüşün cezasıyla başlardı.

ÖLÇÜLEN İNCE NOKTA — NAKDİ RESETLEMEK TEK BAŞINA HİÇBİR ŞEY YAPMAZDI. `broker.equity()` `cash`i
OKUMAZ (`PaperBroker.equity`: `eq = self.start_equity + self.realized_pnl` — ÇAPA SEMBOLDÜR;
burada "broker.py:263" yazıyordu, o satır bugün de-risk rampasına ait — satır-numarası çürümesi
sınıfı, ölçümle düzeltildi ve çapa sembole bağlandı). Yalnız `cash`i 100.000'e
çekmek panoyu düzeltir, boyutlandırmayı DÜZELTMEZ — kozmetik bir yama olurdu. Bu yüzden reset
kitabın DÖRT alanına birden dokunur ve dördünün de gerekçesi ayrı yazılıdır (aşağıda `_yeni_kitap`).

DEFTERLERE DOKUNULMAZ. `trades.jsonl` yerinde kalır: antrenman satırları öğrenmenin (kalibrasyon,
atribüsyon, shadow_model) girdisidir ve silinmeleri ölçüm zeminini yok ederdi. `equity_curve.json`
noktaları da SİLİNMEZ — eğrinin tarihi korunur, kırılma noktası BEYAN edilir (`reset_isaretleri`).

NEDEN EĞRİYE YENİ NOKTA EKLENMİYOR (ölçülmüş yan etki). `points`e bir nokta eklemek cazip: eğri
kırılmayı kendi çizerdi. Ama `ledgerstamp.seed_boundary()` tohum penceresinin sınırını EĞRİNİN SON
NOKTASININ TARİHİNDEN okur (`ledgerstamp.seed_boundary`; eğrinin tek yazarı `run.replay_seed`).
Reset günü bir nokta
eklenseydi tohum sınırı bugüne kayar ve bundan sonraki HER canlı satır `replay_seed` diye
damgalanırdı — yani bu turun kapattığı kusuru, tam da onu kapatan araç geri açardı. İşaret ayrı bir
zarf anahtarında durur; `points` dokunulmaz kalır.

  ↑ ÜSTTEKİ GEREKÇE YANLIŞLANDI (paragraf tarihçe için duruyor). İKİ
  DAYANAĞI DA ÖLDÜ: (1) `ledgerstamp.seed_boundary()` sınırı artık eğrinin son noktasından
  OKUMUYOR — sıra (a) son reset işaretinin DONMUŞ `egri_son_nokta` alanı, (b) yedek yol
  `trades.jsonl` `replay_seed` damgalarının en geç `ts_close`u; güncel son nokta rapora yalnız
  bilgi olarak girer ve "sınırı BELİRLEMEZ" diye beyanlıdır. (2) "tek yazar run.py" varsayımı
  da yok: `loop._persist_equity_point` her seans sonunda eğriye TEK nokta ekliyor (kadanslı
  yazar, bacak-2) — üstelik bu modülün kendisi de aynı zarfa reset İŞARETİ yazıyor (aşağıda,
  `uygula`). KARAR DEĞİŞMEDİ, GEREKÇESİ DEĞİŞTİ: reset günü `points`e nokta EKLENMEZ, çünkü
  (i) bu modülün işi nakit tabanını ayrıştırmaktır, eğrinin tarihini yeniden yazmak değil, ve
  (ii) o günün noktasını zaten kadanslı yazar seans sonunda kendi koyar — buradan ikinci bir
  nokta koymak aynı günü iki yazarlı hâle getirirdi (`_persist_equity_point` günde tek nokta
  değişmezini korur). Sınır artık işaretin DONMUŞ alanından okunduğu için eğriye nokta eklenmesi
  onu kaydırmaz; yani eski paragrafın korktuğu felaket yolu yapısal olarak kapalıdır.

MUTABAKAT KİMLİĞİ KIRILMAZ, BEYANLI HÂLE GETİRİLİR. Reset üç `recompute` kimliğini birden bozar
(`realized_pnl`, `cash_identity`, `equity_curve_tail`) — çünkü kitap yeni bir tabana taşındı,
defter ise eski tabanı taşıyor. Kimlikleri susturmak yerine OFSET beyan edilir: kitapta
`sermaye_resetleri` listesi durur, `ofset()` toplamı verir ve `recompute` GEÇMİŞTEN türeyen tarafa
(defter toplamı / eğri sonu) o ofseti ekler. Böylece kimlik ölçmeye devam eder: resetten SONRA
kaybolan ya da iki kez sayılan bir işlem yine yakalanır.

TEPE SERMAYE AFFI. `peak_equity` 102.520,45 → 100.000 bir GERİLEMEDİR ve `watchdog.
monotonicity_report` bunu haklı olarak bayraklar. Sessizce geçmek ("persist tabanı yutar") ya da
bayrağı kırmızı bırakmak (kurt masalı) yerine depoda zaten kurulu üçüncü yol kullanılır:
`watchdog.grant_amnesty` — YAZILI, tam eşleşmeli, gerekçeli af (re-seed'in 129→95 küçülmesinde
operatörün kullandığı yolun aynısı).

KURU KOŞU VARSAYILANDIR ve CANLI WORKER KOŞARKEN YAZILMAZ — `barrepair`/`ledgerstamp`/`dbmigrate`
ile AYNI desen ve AYNI ölçüm fonksiyonu (iki kopya = iki farklı "canlı" tanımı).

İDEMPOTENT. İkinci `--uygula` hiçbir bayt yazmaz ve `zaten_ayrisik` der. Ayrışıklığın kanıtı
kitaptaki `sermaye_resetleri` kaydıdır — nakdin 100.000 olması DEĞİL (canlı çağ kâr ederse nakit
100.000'den ayrılır ama ayrışıklık sürer).

KİLİT GİRİŞLER. `koken` (sermayenin köken bloğu — pano `/api/today` ve `--durum` aynı fonksiyonu
okur), `durum` (tam ölçüm + engeller/uyarılar), `plan` (kuru koşu), `uygula` (yazım sırası
bilinçli: eğri işareti → kitap → tepe affı → olay), `ofset`/`resetler`/`ayrisik`/`son_reset`
(mutabakatın okuduğu beyanlar), `sermaye_taban` (zımni tabanın sent-tam kanonik türetimi —
monotonluk dedektörünün izlediği büyüklük), `main` (CLI).

OKUR: portfolio.json, equity_curve.json, heartbeat.json, trades.jsonl (ledgerstamp damgalarıyla).
YAZAR (yalnız --uygula ile, kilit altında): portfolio.json (dört alan + reset kaydı),
equity_curve.json (yalnız `reset_isaretleri` zarf anahtarı — `points` DOKUNULMAZ), watchdog af
kaydı + olay defteri.

KULLANIM:
    python -m meridian.sermaye --durum      # köken ölçümü (hiçbir bayt yazılmaz)
    python -m meridian.sermaye              # KURU KOŞU — ne yazılacağı, satır satır
    python -m meridian.sermaye --json       # aynı rapor, makine-okunur
    python -m meridian.sermaye --uygula     # AYRIŞTIR (worker DURDURULMUŞ olmalı)
    python -m meridian.sermaye --uygula --gerekce "…"   # ≥20 karakter, olaya yazılır
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys

from . import ledgerstamp, store

PORTFOLIO = "portfolio.json"
EQUITY = "equity_curve.json"
HEARTBEAT = "heartbeat.json"

# KİTAPTAKİ RESET DEFTERİ. Liste, tek kayıt değil: ikinci bir reset (ör. canlı çağ yeniden
# tohumlanırsa) geçmişini SİLMEDEN üstüne yazabilsin diye. `ofset()` toplamı alır, yani mutabakat
# kimliği kaç reset olursa olsun aynı formülle ölçer.
RESET_KEY = "sermaye_resetleri"
# EĞRİ ZARFINDAKİ İŞARET. `points` DIŞINDAdır (modül başlığındaki seed_boundary gerekçesi);
# `storage._ddl` zarfın points-dışı anahtarlarını `env_json`da korur, yani SQLite çağında da yaşar.
CURVE_MARK_KEY = "reset_isaretleri"

# GEREKÇE EŞİĞİ. YASA 4'ün burada karşılığı: sermaye tabanını taşımak geri alınabilir ama
# AÇIKLANAMAZ olmamalı. 20 karakter "test" ya da "ok" yazmayı engeller, cümle kurmayı zorlar.
MIN_GEREKCE = 20

VARSAYILAN_GEREKCE = (
    "antrenman tohumunun (replay_seed) zararı canlı-kâğıt sermayeden ayrıştırıldı; canlı çağ "
    "100.000$ tabanından ve gerçek-canlı 0 işlemle başlar — defterler yerinde kalır"
)

EVENT = "paper_equity_reset"


# ---- KANONİK SERMAYE TABANI (canlı vaka) ------------------------------------------
def sermaye_taban(pf: dict | None = None, rows: list[dict] | None = None) -> float:
    """ZIMNİ SERMAYE TABANININ KANONİK (SENT-TAM) TÜRETİMİ — tek yerde, 2 hane.

    Büyüklük `watchdog.monotonicity_report`un SB-3 satırıdır: taban = realized_pnl − Σ trades.
    pnl_dollars ("normal işletimde SABİT; yalnız beyan taşır; beyanlar yalnız eklenir → ileri-only").
    CANLI ALARM (2026-08-12): "GERİLEME: sermaye_taban 5542.09 → 5542.08" — 0,01'lik kırık, beyan
    silinmesi DEĞİL, YUVARLAMA KIRIĞI. İki ölçülmüş bacağı var:

      (a) TOPLAMA TOZU: watchdog:1976 `round(realized − Σ float, 2)` hesabında Σ, her çağrıda ham
          float'ların o günkü sırasıyla toplanır; yarım-sent (x.xx5) sınırındaki bir taban, toz
          kadar farkla iki yöne yuvarlanır. Burada Σ SENT TAMSAYISIYLA alınır: defter satırları
          zaten 2 haneli yazılır (`PaperBroker.close_position` → `round(pnl, 2)`), yani `round(x*100)` terim başına
          KESİNDİR ve toplam, toplama sırasından/temsil tozundan bağımsız aynı tamsayıdır.
      (b) KAYNAK KAYMASI: broker `realized_pnl`i HAM (yuvarlanmamış) pnl ile biriktirir
          (`PaperBroker.scale_out` / `PaperBroker.close_position`) ama defter satırını yuvarlayıp
          yazar (aynı satır-yazımı) — `broker` modül başlığının kendi
          sözleşmesi ("realized_pnl == Σ row.pnl_dollars") sent altı kalıntılarla sürüklenir ve
          taban GERÇEKTEN yarım-sent sınırlarına oturur. Bu bacak YAZAR tarafında kapanır
          (yama: birikimi de `round(pnl, 2)` ile yap) — bu fonksiyon o dünyada TAM sabittir,
          bugünkü dünyada ise en azından (a) bacağını ve ölçüm-anı tozunu keser.

    KARŞILAŞTIRMA EPSILON'U BİLEREK YOK: eşik gevşetmek gerçek 1-sentlik silinmeyi de yutardı.
    Yazım/türetim stabilize edilir, dedektörün `v < p` kıyası DOKUNULMADAN kalır — aynı defter iki
    yoldan yazılınca sonuç bit-bit aynıdır, GERÇEK gerileme yine alarmlar.

    Bozuk satır SEMANTİĞİ watchdog ifadesiyle BİREBİR: `pnl_dollars` None/boş → 0; sayıya
    çevrilemeyen değer istisna fırlatır (watchdog kendi try'ında 'kaynak okunamadı' der — sahte bir
    0 uydurulmaz). Tüketiciler: `durum()` (CLI/pano yüzeyi) + watchdog:1976 (tek satırlık yama
    planı: `cur["sermaye_taban"] = _srm.sermaye_taban(pf, _tr)`)."""
    pf = store.read_json(PORTFOLIO, {}) if pf is None else (pf or {})
    rows = store.read_jsonl(ledgerstamp.LEDGER) if rows is None else rows
    r_sent = round(float(pf.get("realized_pnl") or 0.0) * 100)
    defter_sent = sum(round(float(t.get("pnl_dollars") or 0.0) * 100) for t in rows)
    return (r_sent - defter_sent) / 100.0


# ---- ÖLÇÜM (hiçbir bayt yazmaz) ----------------------------------------------------------------
def _hedef() -> float:
    """Ayrıştırma sonrası sermaye TABANI — TEK kaynaktan (`score.START_EQUITY`). Burada 100_000
    sabitini yazmak, `recompute`in kovaladığı 'aynı yasanın iki uygulaması' hatasının kendisi olurdu."""
    from .score import START_EQUITY
    return float(START_EQUITY)


def resetler(pf: dict | None = None) -> list[dict]:
    pf = store.read_json(PORTFOLIO, {}) if pf is None else pf
    r = (pf or {}).get(RESET_KEY) or []
    return [x for x in r if isinstance(x, dict)]


def ofset(pf: dict | None = None) -> float:
    """BEYAN EDİLMİŞ SERMAYE OFSETİ — kitabın tabanı, defterin tabanından ne kadar ayrıldı?

    `recompute`in üç kimliği bu sayıyı GEÇMİŞTEN türeyen tarafa ekler. Kayıt yoksa 0.0'dır ve
    hiçbir davranış değişmez (reset yapılmamış bir depoda modül tamamen görünmezdir)."""
    return round(sum(float(r.get("ofset") or 0.0) for r in resetler(pf)), 2)


def ayrisik(pf: dict | None = None) -> bool:
    return bool(resetler(pf))


def son_reset(pf: dict | None = None) -> dict | None:
    r = resetler(pf)
    return r[-1] if r else None


def _egri_isaretleri(eq: dict | None = None) -> list[dict]:
    eq = store.read_json(EQUITY, {}) if eq is None else eq
    m = (eq or {}).get(CURVE_MARK_KEY) or []
    return [x for x in m if isinstance(x, dict)]


def _pnl_ayristir(rows: list[dict] | None = None) -> dict:
    """Defterin K/Z toplamını KAYNAK DAMGASINA göre ayır.

    `pnl_dollars` taşımayan satır SESSİZCE 0 SAYILMAZ: ayrı sayılır (`pnl_olculemedi`) ve rapora
    çıkar — toplam, ölçülemeyen satır kadar eksiktir ve bunu söylemek zorundadır."""
    rows = store.read_jsonl(ledgerstamp.LEDGER) if rows is None else rows
    top: dict[str, float] = {ledgerstamp.LIVE_PAPER: 0.0, ledgerstamp.REPLAY_SEED: 0.0,
                             ledgerstamp.BELIRSIZ: 0.0}
    eksik: dict[str, int] = {k: 0 for k in top}
    for r in rows:
        k = ledgerstamp.kaynak_of(r)
        v = r.get("pnl_dollars")
        try:
            top[k] += float(v)
        except (TypeError, ValueError):  # sessiz-yutma: SESSİZ DEĞİL — satır `pnl_olculemedi` sayacına girer ve rapor/köken bloğu bu sayıyı taşır; 0 saymak toplamı hak etmediği bir kesinlikle yazardı
            eksik[k] += 1
    return {"toplam": {k: round(v, 2) for k, v in top.items()},
            "pnl_olculemedi": {k: v for k, v in eksik.items() if v}}


def koken() -> dict:
    """SERMAYENİN KÖKEN BLOĞU — panonun ve CLI'nin OKUDUĞU TEK YÜZEY.

    İki tüketici (api `/api/today`, bu modülün `--durum` çıktısı) aynı fonksiyonu çağırır: iki ayrı
    hesap olsaydı pano ile operatörün terminali aynı gün farklı bir "gerçek-canlı sermaye"
    söyleyebilirdi.

    TOHUM ETKİSİ UYDURULMAZ. `replay_seed` damgalı satır YOKKEN toplam 0.0 çıkar — ama bu "tohum
    etkisi yok" demek DEĞİLDİR, "damga hiç basılmamış" demek olabilir (bugün Mac kopyasındaki hâl:
    95 satırın 95'i `belirsiz`). O durumda alan None döner ve `tohum_etkisi_neden` sebebi söyler."""
    pf = store.read_json(PORTFOLIO, {}) or {}
    hb = store.read_json(HEARTBEAT, {}) or {}
    rows = store.read_jsonl(ledgerstamp.LEDGER)
    sayac = ledgerstamp.counts(rows)
    pnl = _pnl_ayristir(rows)
    r = son_reset(pf)
    canli_n = int(sayac["live_paper_n"])
    tohum_n = int(sayac["replay_seed_n"])
    belirsiz_n = int(sayac["belirsiz_n"])
    canli_pnl = pnl["toplam"][ledgerstamp.LIVE_PAPER]
    tohum_pnl = pnl["toplam"][ledgerstamp.REPLAY_SEED] if tohum_n else None
    tohum_neden = None
    if tohum_pnl is None:
        tohum_neden = (f"defterde `replay_seed` damgalı satır yok ve {belirsiz_n} satırın kökeni "
                       f"ölçülmedi — tohum etkisi 0 DEĞİL, ÖLÇÜLEMEDİ "
                       f"(`python -m meridian.ledgerstamp --uygula` damgayı basar)"
                       if belirsiz_n else
                       "defterde tohum satırı yok — antrenman tohumu hiç koşmamış")
    kitap_nakit = pf.get("cash")
    nabiz_eq = hb.get("equity")
    # ÜÇÜNCÜ HÂL KORUNUR: nabız ya da kitap sayı taşımıyorsa cevap `False` ("ayrışma yok") DEĞİL
    # `None`dur ("kıyas yapılamadı"). İkisini aynı değere indirmek, nabzın hiç yazılmadığı bir
    # sistemde panoya "her şey tutuyor" dedirtirdi.
    try:
        nabiz_ayrisik = (None if (kitap_nakit is None or nabiz_eq is None)
                         else abs(float(nabiz_eq) - float(kitap_nakit)) > 1.0)
    except (TypeError, ValueError):  # sessiz-yutma: nabız/kitap alanı sayıya çevrilemedi — kıyas YAPILAMADI, üçüncü hâl `None` olarak dışarı çıkar ve pano onu "ölçülmedi" gösterir
        nabiz_ayrisik = None
    return {
        # GERÇEK-CANLI SERMAYE KİTAPTAN OKUNUR, NABIZDAN DEĞİL: nabız yalnız worker bir tur
        # koştuğunda tazelenir; reset ile ilk tur ARASINDA nabız eski tabanı taşır. Otorite kitaptır.
        "gercek_canli_sermaye": kitap_nakit,
        "canli_islem_n": canli_n,
        "tohum_islem_n": tohum_n,
        "belirsiz_islem_n": belirsiz_n,
        "canli_pnl_usd": canli_pnl,
        "tohum_etkisi_usd": tohum_pnl,
        "tohum_etkisi_neden": tohum_neden,
        # RESET SONRASI 0 YAZILMAZ (brief kuralı): etki ÖLÇÜLMÜŞ hâliyle durur, DURUMU değişir.
        "tohum_etkisi_durum": "ayristirildi" if ayrisik(pf) else "sermayeden_dusuluyor",
        "tohum_etkisi_ibare": ("ayrıştırıldı — canlı sermayeden düşülmüyor" if ayrisik(pf)
                               else "canlı sermayeden düşülüyor"),
        "reset_tarihi": (r or {}).get("tarih"),
        "ayrisik": ayrisik(pf),
        "ofset_usd": ofset(pf),
        "sermaye_tabani": _hedef() if ayrisik(pf) else None,
        # BOYANMA KURALI: gerçek-canlı P&L 0 iken NÖTR. Kâr/zarar rengi, hiç işlem yapmamış bir
        # çağa duygu yükler — panonun bugüne kadarki kusuru tam olarak buydu (kırmızı bir sermaye).
        "renk": ("notr" if not canli_pnl else ("poz" if canli_pnl > 0 else "neg")),
        "ibare": f"gerçek-canlı ({canli_n} işlem)",
        "nabiz_sermaye": nabiz_eq,
        "nabiz_ayrisik": nabiz_ayrisik,
        "pnl_olculemedi": pnl["pnl_olculemedi"],
        "beyan": ("gösterilen sermaye KİTABIN nakdidir; tohum (antrenman) etkisi ayrı satırda "
                  "durur ve reset sonrası sermayeden düşülmez"),
    }


def durum() -> dict:
    """Tam ölçüm: köken bloğu + kitabın ilgili alanları + engeller. Hiçbir bayt yazılmaz."""
    pf = store.read_json(PORTFOLIO, {}) or {}
    eq = store.read_json(EQUITY, {}) or {}
    pts = (eq or {}).get("points") or []
    k = koken()
    isaretler = _egri_isaretleri(eq)
    out = {
        "ayrisik": ayrisik(pf),
        "koken": k,
        "kitap": {"cash": pf.get("cash"), "realized_pnl": pf.get("realized_pnl"),
                  "peak_equity": pf.get("peak_equity"),
                  "day_start_equity": pf.get("day_start_equity"),
                  "last_id": pf.get("last_id"), "last_date": pf.get("last_date"),
                  "n_pozisyon": len(pf.get("positions") or {}),
                  "n_silahli": len(pf.get("armed") or [])},
        "egri": {"n_nokta": len(pts),
                 "son_nokta": (list(pts[-1]) if pts else None),
                 "n_isaret": len(isaretler), "isaretler": isaretler},
        "hedef_cash": _hedef(),
        "resetler": resetler(pf),
        # ZIMNİ TABAN — KANONİK: monotonluk dedektörünün izlediği büyüklüğün sent-tam hâli.
        # Burada yüzeye çıkar ki operatör "taban kaç?" sorusunu alarm beklemeden ölçebilsin.
        "sermaye_taban_kanonik": sermaye_taban(pf),
    }
    out["engeller"] = _engeller(pf, out)
    out["uyarilar"] = _uyarilar(pf, k, isaretler)
    return out


def _engeller(pf: dict, d: dict) -> list[dict]:
    """UYGULAMAYI DURDURAN ÖLÇÜLMÜŞ NEDENLER. Her biri ad + insan cümlesi taşır."""
    e = []
    poz = pf.get("positions") or {}
    if poz:
        e.append({"ad": "dolu_pozisyon", "n": len(poz), "ticker": sorted(poz),
                  "neden": (f"{len(poz)} açık pozisyon var ({', '.join(sorted(poz))}). Sermaye "
                            f"tabanını açık pozisyon varken taşımak, o pozisyonların risk_dollars "
                            f"tabanını GERİYE DÖNÜK değiştirir: aynı pozisyon iki farklı sermayeye "
                            f"göre boyutlandırılmış olur ve R muhasebesi bir daha kapanmaz. "
                            f"Önce pozisyonlar kapansın.")})
    if d["ayrisik"]:
        e.append({"ad": "zaten_ayrisik", "n": len(d["resetler"]),
                  "neden": (f"kitapta {len(d['resetler'])} reset kaydı var (son: "
                            f"{(son_reset(pf) or {}).get('tarih')}) — ayrıştırma ZATEN yapılmış. "
                            f"İkinci kez uygulamak tabanı bir kez daha kaydırır ve mutabakat "
                            f"ofsetini iki katına çıkarırdı.")})
    return e


def _uyarilar(pf: dict, k: dict, isaretler: list[dict]) -> list[str]:
    """ENGEL DEĞİL ama operatörün BİLMESİ gereken ölçümler."""
    u = []
    if k["tohum_etkisi_usd"] is None and k["tohum_etkisi_neden"]:
        u.append(f"tohum etkisi ÖLÇÜLEMEDİ: {k['tohum_etkisi_neden']}. Ayrıştırma yine de "
                 f"yapılabilir — ofset kitaptan (yeni−eski) ÖLÇÜLÜR, damgadan türetilmez; ama "
                 f"panodaki 'tohum etkisi' satırı damga basılana kadar boş kalır.")
    n_silahli = len(pf.get("armed") or [])
    if n_silahli:
        u.append(f"{n_silahli} SİLAHLI plan var: qty'leri ESKİ sermayeye göre hesaplandı ve reset "
                 f"onları yeniden boyutlandırmaz — sıradaki açılışta eski boyutla ateşlerler.")
    if isaretler and not ayrisik(pf):
        u.append(f"YARIM UYGULAMA İZİ: eğride {len(isaretler)} reset işareti var ama kitapta reset "
                 f"kaydı YOK (önceki bir koşum eğriyi yazıp kitaba geçemeden düşmüş olabilir). "
                 f"Uygulama yeni bir işaret ekler; eskisi defterde beyanlı olarak KALIR.")
    if k["nabiz_ayrisik"]:
        u.append(f"nabız sermayesi ({k['nabiz_sermaye']}) kitabın nakdinden ({k['gercek_canli_sermaye']}) "
                 f"farklı — worker bir tur koşana kadar nabız eski tabanı taşır.")
    return u


# ---- PLAN + UYGULA -----------------------------------------------------------------------------
def _yeni_kitap(pf: dict, hedef: float) -> dict:
    """RESET EDİLEN DÖRT ALAN + HER BİRİNİN AYRI GEREKÇESİ.

      cash             → hedef : kitabın anlattığı sermaye; panonun okuduğu sayı.
      realized_pnl     → 0.0   : ASIL DAVRANIŞ ALANI. `broker.equity()` = start_equity +
                                 realized_pnl (broker.py:263) ve `loop._load_broker` start_equity'yi
                                 her turda START_EQUITY'ye sabitler — yani boyutlandırma tabanını
                                 belirleyen tek disk alanı budur. Sıfırlanmazsa reset KOZMETİK kalır.
      day_start_equity → hedef : gün P&L'i (equity − day_start)/day_start. Eski taban kalsaydı pano
                                 reset ertesi %5,87'lik UYDURMA bir günlük kâr gösterirdi.
      peak_equity      → hedef : de-risk rampası düşüşü tepeden ölçer (broker.max_positions_at).
                                 102.520,45 tohumun tepesidir; bırakılsaydı canlı çağ, hiç
                                 yaşamadığı bir düşüşün kısıtıyla doğardı.

    DOKUNULMAYANLAR ve nedenleri: `last_id` (yeni canlı satırlar 96'dan devam etmeli — sıfırlamak
    tohum satırlarıyla kimlik çakıştırırdı), `positions`/`armed`/`pending_exits` (boş olduğu
    ölçüldü, engelde), `broker_rejected`/`alpaca_submitted` (icra denetim izi — sermaye değil),
    `last_date` (veri kadansının damgası)."""
    onceki_cash = float(pf.get("cash") or 0.0)
    return {"cash": round(hedef, 2), "realized_pnl": 0.0,
            "day_start_equity": round(hedef, 2), "peak_equity": round(hedef, 2),
            "_onceki": {"cash": round(onceki_cash, 2),
                        "realized_pnl": round(float(pf.get("realized_pnl") or 0.0), 2),
                        "day_start_equity": pf.get("day_start_equity"),
                        "peak_equity": pf.get("peak_equity")}}


def plan(gerekce: str = VARSAYILAN_GEREKCE) -> dict:
    """KURU KOŞU: ne yazılacak? Hiçbir bayt yazılmaz, hiçbir dosya açılmaz (okuma dışında)."""
    pf = store.read_json(PORTFOLIO, {}) or {}
    d = durum()
    hedef = _hedef()
    yk = _yeni_kitap(pf, hedef)
    onceki = yk.pop("_onceki")
    rapor = {"applied": False, "yazildi": False, "gerekce": gerekce,
             "gerekce_uzunluk": len(str(gerekce or "").strip()),
             "durum": d, "hedef_cash": hedef,
             "onceki": onceki, "yeni": yk,
             "ofset": round(hedef - float(onceki["cash"]), 2),
             "engeller": d["engeller"], "uyarilar": d["uyarilar"]}
    if rapor["gerekce_uzunluk"] < MIN_GEREKCE:
        rapor["engeller"] = list(rapor["engeller"]) + [
            {"ad": "gerekce_kisa", "n": rapor["gerekce_uzunluk"],
             "neden": (f"gerekçe {rapor['gerekce_uzunluk']} karakter; en az {MIN_GEREKCE} gerekiyor. "
                       f"Sermaye tabanını taşımak geri alınabilir bir işlemdir ama AÇIKLANAMAZ "
                       f"olmamalıdır — gerekçe olaya yazılır ve altı ay sonra tek okunacak şeydir.")}]
    rapor["uygulanabilir"] = not rapor["engeller"]
    return rapor


def uygula(gerekce: str = VARSAYILAN_GEREKCE) -> dict:
    """AYRIŞTIRMAYI YAZ. Sıra bilerek şudur: (1) eğri işareti, (2) kitap, (3) af, (4) olay.

    Neden eğri ÖNCE: işaret tek başına ZARARSIZDIR (beyandır, hiçbir sayıyı değiştirmez) ve
    aradaki bir çökme `durum()`da 'YARIM UYGULAMA İZİ' olarak GÖRÜNÜR. Ters sırada kitap taşınmış
    ama kırılma beyansız kalırdı — yani sessiz hâl, tam da bu deponun kovaladığı kusur sınıfı."""
    rapor = plan(gerekce)
    rapor["applied"] = True
    if rapor["engeller"]:
        rapor["ok"] = False
        rapor["hata"] = "; ".join(f"{e['ad']}: {e['neden']}" for e in rapor["engeller"])
        return rapor

    hedef, onceki = rapor["hedef_cash"], rapor["onceki"]
    ts = _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat()
    reset_id = f"SR-{ts.replace(':', '').replace('-', '')}"
    k = rapor["durum"]["koken"]
    kayit = {"id": reset_id, "tarih": ts,
             "onceki_cash": onceki["cash"], "yeni_cash": round(hedef, 2),
             "ofset": rapor["ofset"],
             "onceki_realized_pnl": onceki["realized_pnl"], "yeni_realized_pnl": 0.0,
             "onceki_peak_equity": onceki["peak_equity"], "yeni_peak_equity": round(hedef, 2),
             "tohum_etkisi_usd": k["tohum_etkisi_usd"],
             "tohum_islem_n": k["tohum_islem_n"], "canli_islem_n": k["canli_islem_n"],
             "belirsiz_islem_n": k["belirsiz_islem_n"],
             "gerekce": str(gerekce).strip(), "arac": "meridian.sermaye"}

    # (1) EĞRİ İŞARETİ — `points` DOKUNULMAZ (modül başlığı: seed_boundary gerekçesi).
    egri_son = None
    with store.file_lock(EQUITY):
        eq = store.read_json(EQUITY, {}) or {}
        pts = eq.get("points") or []
        egri_son = list(pts[-1]) if pts else None
        isaret = {"id": reset_id, "tarih": ts, "tip": "paper_equity_reset",
                  "onceki_deger": onceki["cash"], "yeni_deger": round(hedef, 2),
                  "egri_son_nokta": egri_son, "gerekce": str(gerekce).strip(),
                  # İŞARETİN METNİ DE BİR BEYANDIR ve koddan geri kalamaz:
                  # eski cümle "nokta eklenmez ÇÜNKÜ eğrinin son noktası tohum sınırıdır" diyordu;
                  # sınır artık son noktadan okunmuyor (bu işaretin DONMUŞ `egri_son_nokta`
                  # alanından okunuyor) ve eğriye her seans kadanslı yazar nokta ekliyor. Gerekçe
                  # düzeltildi, karar aynı — bkz. modül başlığındaki mezar taşı.
                  "not": ("eğri noktaları SİLİNMEDİ: bu tarih tohum (antrenman) dönemine aittir ve "
                          "ölçüm girdisidir. İşaret, eğrinin bu noktadan sonra yeni bir sermaye "
                          "tabanına oturduğunu BEYAN eder — nokta olarak eklenmez, çünkü o günün "
                          "noktasını kadanslı yazar (loop._persist_equity_point) seans sonunda "
                          "kendi koyar; bu işaretin `egri_son_nokta` alanı ise DONDURULMUŞ tohum "
                          "sınırıdır (ledgerstamp.seed_boundary onu buradan okur)")}
        eq[CURVE_MARK_KEY] = _egri_isaretleri(eq) + [isaret]
        store.write_json(EQUITY, eq)
    rapor["egri_isareti"] = isaret

    # (2) KİTAP — dört alan + reset defteri. Kilit altında oku-değiştir-yaz (loop `_save_broker` ve
    #     hermes damgası aynı dosyaya yazıyor; `store.file_lock` süreçler arası).
    with store.file_lock(PORTFOLIO):
        pf = store.read_json(PORTFOLIO, {}) or {}
        yeni = _yeni_kitap(pf, hedef)
        yeni.pop("_onceki")
        pf.update(yeni)
        pf[RESET_KEY] = resetler(pf) + [kayit]
        store.write_json(PORTFOLIO, pf)
    rapor["kayit"] = kayit
    rapor["yazildi"] = True

    # (3) TEPE SERMAYE AFFI — meşru küçülmenin YAZILI kaydı. `was` monotonluk TABANINDAN okunur,
    #     kitaptan değil: dedektör kıyası `monotonic_state.json` ile yapar ve af TAM eşleşme ister.
    rapor["af"] = _peak_affi(round(hedef, 2), kayit)

    # (4) OLAY — panonun ve denetimin okuduğu satır.
    try:
        from . import obs
        obs.warn(EVENT, reset_id=reset_id,
                 eski_cash=onceki["cash"], yeni_cash=round(hedef, 2), ofset=rapor["ofset"],
                 eski_realized_pnl=onceki["realized_pnl"], yeni_realized_pnl=0.0,
                 eski_peak_equity=onceki["peak_equity"], yeni_peak_equity=round(hedef, 2),
                 tohum_pnl_usd=k["tohum_etkisi_usd"],
                 ledgerstamp_live_paper_n=k["canli_islem_n"],
                 ledgerstamp_replay_seed_n=k["tohum_islem_n"],
                 ledgerstamp_belirsiz_n=k["belirsiz_islem_n"],
                 egri_son_nokta=egri_son, gerekce=str(gerekce).strip(),
                 detail=("antrenman tohumunun K/Z'si canlı-kâğıt sermayeden ayrıştırıldı: kitap "
                         "100.000$ tabanına taşındı, defterler (trades/equity_curve noktaları) "
                         "DOKUNULMADAN kaldı, kırılma noktası eğride beyanlı"))
    except Exception:  # sessiz-yutma: kayıt kanalı düştü; ayrıştırma diske ATOMİK yazıldı ve rapor çağırana döndü — kayıt denemesi yazımı geri alamaz
        rapor["olay_yazilamadi"] = True
    rapor["ok"] = True
    rapor["sonraki_durum"] = durum()
    return rapor


def _peak_affi(yeni_peak: float, kayit: dict) -> dict:
    """`peak_equity` gerilemesi için TAM EŞLEŞMELİ af. Af yalnız GERÇEKTEN bir gerileme varsa
    verilir: taban yoksa ya da taban zaten yeni değerin altındaysa affedilecek bir şey yoktur ve
    gereksiz af, ileride GERÇEK bir kaybı sessizce yutabilecek bir muafiyet bırakırdı."""
    try:
        from . import watchdog as _wd
        taban = store.read_json(_wd.MONOTONIC_FILE, None) or {}
        was = taban.get("peak_equity")
        if was is None:
            return {"verildi": False, "neden": "monotonluk tabanı yok — affedilecek gerileme yok"}
        if float(was) <= yeni_peak:
            return {"verildi": False, "was": was,
                    "neden": f"taban {was} ≤ yeni tepe {yeni_peak} — gerileme yok"}
        a = _wd.grant_amnesty(
            "peak_equity", float(was), yeni_peak,
            reason=(f"sermaye tohum-ayrıştırması ({kayit['id']}): tepe {was} antrenman tohumunun "
                    f"(replay_seed, {kayit['tohum_islem_n']} satır) simülasyon tepesiydi; canlı-kâğıt "
                    f"çağ {yeni_peak}$ tabanından ve {kayit['canli_islem_n']} gerçek işlemle başlıyor. "
                    f"Küçülme kayıptan değil, TABAN DEĞİŞİMİNDEN. Gerekçe: {kayit['gerekce']}"),
            by="meridian.sermaye")
        return {"verildi": True, "was": float(was), "now": yeni_peak, "kayit": a}
    except Exception as e:  # sessiz-yutma: SESSİZ DEĞİL — af verilemedi bilgisi rapora çıkar; ayrıştırma geri alınmaz ama operatör monotonluk bayrağının kırmızı yanacağını BURADAN öğrenir
        return {"verildi": False, "hata": f"{type(e).__name__}: {e}",
                "neden": ("af yazılamadı — `watchdog.monotonicity_report` peak_equity gerilemesini "
                          "bayraklayacak; elle af: watchdog.grant_amnesty('peak_equity', …)")}


def _worker_running() -> bool:
    """Canlı Meridian süreci var mı? `barrepair`in AYNI ölçümü — kopyalanmaz, çağrılır."""
    from .barrepair import _worker_running as _wr
    return _wr()


# ---- YAZDIRMA ----------------------------------------------------------------------------------
def _p(x, birim="$") -> str:
    if x is None:
        return "—"
    try:
        return f"{float(x):,.2f}{birim}"
    except (TypeError, ValueError):  # sessiz-yutma: yalnız BİÇİMLEME yolu; ham değer olduğu gibi basılır, hiçbir ölçüm kaybolmaz
        return str(x)


def _durum_yaz(d: dict, baslik: bool = True) -> None:
    k = d["koken"]
    if baslik:
        print("[sermaye] KÖKEN ÖLÇÜMÜ (hiçbir bayt yazılmadı)")
    print(f"  ayrışık mı            : {'EVET' if d['ayrisik'] else 'HAYIR'}"
          + (f"  (reset {k['reset_tarihi']}, ofset {_p(k['ofset_usd'])})" if d["ayrisik"] else ""))
    print(f"  gerçek-canlı sermaye  : {_p(k['gercek_canli_sermaye'])}   [{k['ibare']}]  renk={k['renk']}")
    print(f"  canlı P&L             : {_p(k['canli_pnl_usd'])}")
    print(f"  tohum etkisi          : {_p(k['tohum_etkisi_usd'])}   ({k['tohum_etkisi_ibare']})")
    if k["tohum_etkisi_neden"]:
        print(f"      ↳ {k['tohum_etkisi_neden']}")
    print(f"  defter                : canlı {k['canli_islem_n']} · tohum {k['tohum_islem_n']} · "
          f"belirsiz {k['belirsiz_islem_n']}")
    b = d["kitap"]
    print(f"  kitap                 : nakit {_p(b['cash'])} · realized {_p(b['realized_pnl'])} · "
          f"tepe {_p(b['peak_equity'])} · gün-başı {_p(b['day_start_equity'])}")
    print(f"                          pozisyon {b['n_pozisyon']} · silahlı {b['n_silahli']} · "
          f"last_id {b['last_id']} · seans {b['last_date']}")
    if d.get("sermaye_taban_kanonik") is not None:
        print(f"  zımni taban (kanonik) : {_p(d['sermaye_taban_kanonik'])}   "
              f"[realized − Σ defter, sent-tam — monotonluk dedektörünün izlediği büyüklük]")
    e = d["egri"]
    print(f"  eğri                  : {e['n_nokta']} nokta · son {e['son_nokta']} · "
          f"{e['n_isaret']} reset işareti")
    for u in d["uyarilar"]:
        print(f"  ! UYARI: {u}")


def _yaz(rapor: dict) -> None:
    mod = ("UYGULANDI" if rapor.get("yazildi") else
           ("UYGULAMA REDDEDİLDİ" if rapor.get("applied") else "KURU KOŞU (hiçbir bayt yazılmadı)"))
    print(f"[sermaye] {mod}")
    # UYGULANDIYSA SONRAKİ HÂL BASILIR. Kuru koşunun anlık görüntüsünü "UYGULANDI" başlığının
    # altında basmak, operatöre yazımdan ÖNCEKİ kitabı yazımdan SONRAKİ sanki gibi gösterirdi —
    # aracın kendi çıktısı yalan söylerdi.
    _durum_yaz(rapor.get("sonraki_durum") or rapor["durum"], baslik=False)
    o, y = rapor["onceki"], rapor["yeni"]
    print(f"  --- {'YAZILAN' if rapor.get('yazildi') else 'YAZILACAK'} (kitap) ---")
    for alan in ("cash", "realized_pnl", "day_start_equity", "peak_equity"):
        print(f"    {alan:18s} {_p(o.get(alan)):>16s}  →  {_p(y.get(alan)):>16s}")
    print(f"    ofset (yeni−eski)  {_p(rapor['ofset']):>16s}   "
          f"→ recompute üç kimliği bu ofsetle ölçmeye devam eder")
    print(f"  --- {'YAZILAN' if rapor.get('yazildi') else 'YAZILACAK'} (eğri) ---")
    print(f"    {CURVE_MARK_KEY}: +1 işaret (points DOKUNULMAZ — {rapor['durum']['egri']['n_nokta']} "
          f"nokta yerinde kalır)")
    print(f"  --- DOKUNULMAYAN ---")
    print(f"    trades.jsonl ({rapor['durum']['koken']['tohum_islem_n'] + rapor['durum']['koken']['canli_islem_n'] + rapor['durum']['koken']['belirsiz_islem_n']} satır) · "
          f"equity_curve.points · last_id · broker_rejected · armed")
    print(f"  gerekçe ({rapor['gerekce_uzunluk']} karakter): {rapor['gerekce']}")
    for e in rapor["engeller"]:
        print(f"  ENGEL [{e['ad']}]: {e['neden']}")
    if rapor.get("af"):
        a = rapor["af"]
        print(f"  monotonluk affı: {'VERİLDİ' if a.get('verildi') else 'verilmedi'} "
              f"({a.get('neden') or f'''peak_equity {a.get('was')} → {a.get('now')}'''})")
    if rapor.get("olay_yazilamadi"):
        print("  ! olay kanalı yazılamadı (ayrıştırma diske yazıldı)")
    if not rapor.get("applied") and rapor.get("uygulanabilir"):
        print("  → uygulamak için: python -m meridian.sermaye --uygula "
              "(worker DURDURULMUŞ olmalı)")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="python -m meridian.sermaye",
        description="antrenman tohumunun K/Z'sini canlı-kâğıt sermayeden ayrıştırır "
                    "(defterlere dokunmaz)")
    ap.add_argument("--durum", action="store_true", help="yalnız köken ölçümü")
    ap.add_argument("--uygula", action="store_true", help="AYRIŞTIR (varsayılan: kuru koşu)")
    ap.add_argument("--json", action="store_true", help="raporu JSON olarak bas")
    ap.add_argument("--gerekce", default=VARSAYILAN_GEREKCE,
                    help=f"olaya ve kitaba yazılacak gerekçe (en az {MIN_GEREKCE} karakter)")
    ap.add_argument("--zorla", action="store_true",
                    help="canlı süreç görülse de yaz (riski sen alırsın)")
    a = ap.parse_args(argv)
    if a.durum:
        d = durum()
        if a.json:
            print(json.dumps(d, ensure_ascii=False, indent=1, default=str))
        else:
            _durum_yaz(d)
        return 0
    if a.uygula and not a.zorla and _worker_running():
        print("[sermaye] REDDEDİLDİ: canlı Meridian süreci görülüyor. Worker koşarken kitap "
              "taşınamaz — `loop._save_broker` her turda `cash`/`realized_pnl`i DİSKTEN OKUDUĞU "
              "hâliyle geri yazar, yani reset bir sonraki tikte sessizce geri alınır (kilit yarışı "
              "önler, geri-yazımı önlemez). Önce `./ops/stop-worker.sh`, sonra tekrar dene "
              "(ya da --zorla).", file=sys.stderr)
        return 2
    rapor = uygula(a.gerekce) if a.uygula else plan(a.gerekce)
    if a.json:
        print(json.dumps(rapor, ensure_ascii=False, indent=1, default=str))
    else:
        _yaz(rapor)
    return 0 if rapor.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
