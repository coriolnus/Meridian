"""ops/tohum_pit_yenile.py — TSK-159 S5: canlı tohum diliminin PIT üyelikle (varyant A) değişimi.

OPERATÖR KARARI (2026-09-07 sabah): "S5 tohum değişimini onaylıyorum, A varyantı ile devam et."
PLAN: `docs/superpowers/plans/2026-09-07-s5-tohum-pit.md` (Task 1; ruling 1-5 bağlayıcı).
KART: EDG-2026-082 (ölçüm) · EDG-2026-036 (2026-08-13 emsali: UYGULAMA_PROSEDURU + asama2_UYGULANDI).

NE YAPAR. Canlı `trades.jsonl`/`trade_plans.jsonl` defterindeki TOHUM dilimini (kaynak damgası
`replay_seed`) aynı parametre/hedef/takvimle ama `uyelik=as_of` (varyant A) ile üretilmiş PIT
tohumuyla DEĞİŞTİRİR. Canlı satırlar (`live_paper`) ve kökeni ölçülemeyen satırlar (`belirsiz`)
BİT-AYNI korunur; eski tohum SİLİNMEZ, arşivlenir.

NE YAPMAZ (EDG-036 kill'leri, ruling 4). `run.replay_seed` ÇAĞRILMAZ: o yol kitabı sıfırdan kurar,
canlı satırları siler, plan defterini tamamen ezer, karneyi arşivler. Bu betik `scoreboard.json`a,
`candidates.jsonl`a, `portfolio.json`a ve `equity_curve.json`un `points` dizisine HİÇ DOKUNMAZ;
yazım yalnız `store` kapısından (file_lock + write_jsonl/write_json) geçer, elle SQL yoktur.

DAMGA SÖZLEŞMESİ (ruling 1 — `kaynak` değeri DEĞİŞMEZ). Yeni satırlar da `kaynak=replay_seed`
taşır: `ledgerstamp.GECERLI` dışında yeni bir kaynak değeri (ör. `replay_seed_pit`) her satırı
`belirsiz` yapar ve EDG-036'da ölçülen "13 tüketici kaynak-kör" hâlinde defteri okunamaz kılardı.
PIT tohumu bunun yerine `tohum_parti`/`pit_uyelik`/`varyant` alanlarıyla ayırt edilir (dosya
yolunda satırın kendi alanları; SQLite arka ucunda `extra_json` — `storage._row_to_cols` bilinmeyen
alanları oraya koyar ve okumada extra KAZANIR) ve AYRI tohum sürüm uzayında (`strategy_version=91`)
durur: 2026-08-13'ün sv=90 gerekçesi aynen geçerlidir (ebeveyn tabanı kirlenmesin, geri-alma
kapısı tohum yüzünden açılmasın).

KURU KOŞUM SÖZLEŞMESİ. `--uygula` VERİLMEDİKÇE `state/` ve yedek dizinine TEK BAYT yazılmaz.
`--rapor-dizin` verilmezse rapor YALNIZ stdout'a basılır — yani argümansız kuru koşum diskte
hiçbir iz bırakmaz. `--uygula` ise `--rapor-dizin` İSTER: okuyucusuz yazım YASA 6 ihlalidir.

KAPI-0 (yazımdan önce, ölçülür — uydurulmaz):
  · nabız TAZE ise (`health.stale(run.RESEED_HEARTBEAT_FRESH_S)` False) canlı bir worker koşuyor
    demektir → `--uygula` REDDEDİLİR. Kuru koşum serbesttir (yalnız okur).
  · `portfolio.armed` doluysa → REDDEDİLİR (silahlı planın altından defter çekilmez).
  Eşik `meridian.run`dan İTHAL edilir, ikinci bir sayı burada yazılmaz (tek-kaynak yasası).

ÜYELİK TÜRETİMİ TEK KAYNAKTAN. Varyant A üyelik fonksiyonu KOPYALANMAZ: EDG-082 ölçüm betiği
(`research/olcumler/edg082_pit_tohum/olcum.py`) `ops/sasi_yukleyici.kaynaktan_yukle` ile İTHAL
edilir ve `uyelik_fonksiyonlarini_kur(...)["A"]` AYNEN kullanılır. Girdiler ölçümle AYNI donuk
artefaktlardır ve sha256'ları rapora + her satırın damgasına girer: `--girdi-html` (S&P 500
tarihsel değişiklik tablosunun ham HTML'i) ve `--guncel-liste` (donuk güncel üyelik JSON'u).

PARAMETRE KAYNAĞI — PLANDAN SAPMA, BEYANLI. Plan `run.bootstrap_v01()` diyordu; o fonksiyon
`strategy.yaml` YOKSA dosyayı YAZAR (`config.dump_yaml` + `versioning.snapshot`) ve bu, kuru
koşumun "tek bayt yazmam" sözünü kırardı. Dosya VARKEN `bootstrap_v01()` zaten `config.
load_strategy()`e birebir eşittir. Betik bu yüzden `config.load_strategy()` çağırır ve
`strategy.yaml` YOKSA DURUR (rc=1): `load_strategy` o hâlde sessizce `default_strategy()`e düşer
ve tohum "yürürlükteki paketi temsil eder" beyanı YALAN olurdu.

BAR KAYNAĞI. `dataset.load()` — üretim yolu, `run.replay_seed`in okuduğu barların AYNISI. EDG-082
ölçümü bilerek AYRI bir minimal temizlik (`temiz_bar_oku`) kullanmıştı (ölçüm ajanı `obs`a
ULAŞAMAZ); burada amaç CANLI defteri değiştirmek olduğu için üretim boru hattı seçildi ve fark
raporun `beyan` alanında yazılıdır. SONUÇ: bu betik pytest DIŞINDA koşulduğunda `data.sanitize_
bars` nadir yollarında `obs.warn` yazabilir — o yüzden yalnız Rol-1 tarafından, canlı makinede
koşulur (ajan koşumu YASAK, CLAUDE.md §2).

ÇIKIŞ KODU: 0 = ok · 1 = KAPI-0 reddi / girdi eksik / yazım düştü · 2 = kullanım hatası.

KULLANIM:
    python ops/tohum_pit_yenile.py --girdi-html <hist.html> --guncel-liste <guncel.json>   # KURU
    python ops/tohum_pit_yenile.py --girdi-html … --guncel-liste … \\
        --rapor-dizin research/olcumler/edg082_pit_tohum/s5_2026-09-07                     # KURU+rapor
    python ops/tohum_pit_yenile.py --girdi-html … --guncel-liste … --uygula \\
        --rapor-dizin research/olcumler/edg082_pit_tohum/s5_2026-09-07                     # YAZ

Çivi: tests/test_tohum_pit_yenile_v433.py
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import pathlib
import re
import statistics
import sys
import time

KOK = pathlib.Path(__file__).resolve().parents[1]
if str(KOK) not in sys.path:
    # Betik DOĞRUDAN koşuluyor (`python ops/tohum_pit_yenile.py`), o hâlde `sys.path[0]` depo kökü
    # değil `ops/` dizinidir ve ne `meridian` ne `ops.` ön eki çözülür.
    sys.path.insert(0, str(KOK))

import yaml                                                                     # noqa: E402

from meridian import (analytics, backtest, config, dataset, health,             # noqa: E402
                      ledgerstamp, olcum_araclari, rollback, run, score as score_mod,
                      sermaye, store, versioning, watchdog)
from ops.sasi_yukleyici import kaynaktan_yukle                                  # noqa: E402

BETIK_ADI = "ops/tohum_pit_yenile.py"

# ---- SÖZLEŞME SABİTLERİ (plan ruling 1) --------------------------------------------------------
TOHUM_PARTI = "EDG-082A-2026-09-07"
PIT_UYELIK = "as_of"
VARYANT = "A"
TOHUM_SURUM = 91                 # AYRI tohum sürüm uzayı (2026-08-13'te sv=90 idi; aynı gerekçe)
VARSAYILAN_BASLANGIC = "2022-01-01"

KART036 = KOK / "research" / "cards" / "EDG-2026-036-tohum-yenileme.yaml"
EDG082_OLCUM = KOK / "research" / "olcumler" / "edg082_pit_tohum" / "olcum.py"
VARSAYILAN_YEDEK_DIZIN = KOK / "backups"

LEDGER = ledgerstamp.LEDGER              # "trades.jsonl" — ad TEK kaynaktan
PLAN_DEFTERI = "trade_plans.jsonl"
PORTFOLIO = sermaye.PORTFOLIO
EQUITY = sermaye.EQUITY

# Yeni tohum satırının TAŞIDIĞI serbest alanlar (rapor + çivi bu listeyi okur; ikinci bir literal
# liste yazmak, bu deponun "aynı gerçeğin iki kopyası" sınıfı olurdu).
DAMGA_ALANLARI = ("tohum_parti", "pit_uyelik", "varyant", "params_sha256", "guncel_liste_sha256",
                  "html_sha256", "motor_kunye", "motor_kunye_kirli", "pencere", "evren_n",
                  "friksiyon_serhi")

_SERH_DESENI = re.compile(r"FRİKSİYON ŞERHİ\*\*:\s*\"([^\"]+)\"")


# ==================================================================================================
# SAF YARDIMCILAR — hiçbiri diske/ağa dokunmaz
# ==================================================================================================

def _sha_rows(rows: list[dict]) -> str:
    """Satır listesinin içerik özeti — `json.dumps(sort_keys=True)` satırlarının sha256'sı."""
    ham = "".join(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n" for r in rows)
    return hashlib.sha256(ham.encode("utf-8")).hexdigest()


def _sha_dosya(yol) -> str:
    return hashlib.sha256(pathlib.Path(yol).read_bytes()).hexdigest()


def _tarih(v) -> str | None:
    """Ham değerden ISO tarih (ilk 10 karakter); ayrıştırılamazsa None — uydurma yok."""
    if v is None:
        return None
    s = str(v)[:10]
    try:
        dt.date.fromisoformat(s)
    except ValueError:  # sessiz-yutma DEĞİL: biçimsiz değer çağırana None döner ve sayaçlara `olculemedi` olarak girer
        return None
    return s


def friksiyon_serhi_oku(kart_yolu=KART036) -> str:
    """EDG-036 `asama1_hukmu.DAMGA_KARARI` içindeki FRİKSİYON ŞERHİ metnini KARTTAN okur.

    Metin KOPYALANMAZ: kart tek kaynaktır ve şerh değişirse damga da değişir. Şerh bulunamazsa
    ValueError — betik metni UYDURMAZ (kart kuralı: ölçülemeyen değer yazılmaz)."""
    kart = yaml.safe_load(pathlib.Path(kart_yolu).read_text(encoding="utf-8"))
    blok = ((kart or {}).get("asama1_hukmu") or {}).get("DAMGA_KARARI") or ""
    m = _SERH_DESENI.search(str(blok))
    if not m:
        raise ValueError(f"FRİKSİYON ŞERHİ kartta bulunamadı: {kart_yolu} "
                         f"(beklenen desen: **…FRİKSİYON ŞERHİ**: \"…\")")
    return m.group(1).strip()


def defter_ayir(rows: list[dict]) -> dict:
    """İşlem defterini TOHUM ve KORUNAN olarak ayırır — SAF fonksiyon.

    KORUNAN = damgası `replay_seed` OLMAYAN her satır: `live_paper` (gerçek kâğıt-icra kanıtı) VE
    `belirsiz` (kökeni ölçülemeyen satır). Belirsiz satırı da korumak BİLİNÇLİDİR: "tohum olduğunu
    ÖLÇEMEDİK" ile "tohumdur" aynı cümle değildir ve ölçülmemiş bir satırı silmek uydurma yönünde
    bir karardır. Sıra KORUNUR (`rows` sırası)."""
    tohum, korunan = [], []
    for r in rows:
        (tohum if ledgerstamp.kaynak_of(r) == ledgerstamp.REPLAY_SEED else korunan).append(r)
    return {"tohum": tohum, "korunan": korunan}


def plan_ayir(planlar: list[dict], *, korunan_plan_idleri: set, eski_tohum_siniri: str | None) -> dict:
    """Plan defterini TOHUM ve KORUNAN olarak ayırır — SAF fonksiyon.

    Plan satırında `kaynak` damgası YOKTUR (yalnız işlem defterinde vardır), o yüzden ayrım ÜÇ
    ÖLÇÜLEBİLİR ölçütün BİRLEŞİMİdir ve hiçbiri tahmin değildir:
      (0) `tohum_parti` alanı taşıyan plan TOHUMDUR — bu betiğin KENDİ yazdığı damga; bir sonraki
          tohum değişimi bu planları tahminsiz bulur (2026-08-13'te bu damga yoktu, bu yüzden ayrım
          o gün tarih sezgisine kalmıştı).
      (1) `llm_opinion` alanı taşıyan plan KORUNUR — EDG-036 hükmü: LLM görüşü YALNIZ canlı yolda
          basılır, `backtest.replay` bu alanı ÜRETEMEZ. 2026-08-13'te `run.replay_seed`in plan
          defterini tam ezmesi tam da bu 8 planı yok etmişti (llm_calibration 4 çift → 1).
      (2) KORUNAN bir işlemin `plan_id`si olan plan KORUNUR — korunum dedektörü (`watchdog.
          conservation_report`) işlemi planına bağlar; planı düşen canlı işlem "sessiz kayıp" olur.
      (3) `date`i ESKİ tohum sınırından (eski tohum satırlarının en geç `ts_close`u) SONRA olan
          plan KORUNUR — canlı dönemde doğmuş, henüz işleme dönüşmemiş ve LLM görüşü almamış
          planlar bu ölçütle kurtulur. Sınır ÖLÇÜLEMEZSE (eski tohum yok / `ts_close` biçimsiz)
          bu ölçüt UYGULANMAZ ve rapor bunu söyler."""
    tohum, korunan = [], []
    for p in planlar:
        pid = str(p.get("id") or "")
        tarih = _tarih(p.get("date"))
        if p.get("tohum_parti") is not None:
            tohum.append(p)
            continue
        if (p.get("llm_opinion") is not None
                or pid in korunan_plan_idleri
                or (eski_tohum_siniri is not None and tarih is not None
                    and tarih > eski_tohum_siniri)):
            korunan.append(p)
        else:
            tohum.append(p)
    return {"tohum": tohum, "korunan": korunan}


def defter_ozeti(rows: list[dict]) -> dict:
    """İşlem defterinin kaynak kırılımı — `ledgerstamp.counts` TEK kaynağından, ek olarak sha."""
    ozet = dict(ledgerstamp.counts(rows))
    ayrik = defter_ayir(rows)
    ozet["korunan_n"] = len(ayrik["korunan"])
    ozet["korunan_sha256"] = _sha_rows(ayrik["korunan"])
    ozet["tohum_sha256"] = _sha_rows(ayrik["tohum"])
    ozet["tohum_partileri"] = sorted({str(r.get("tohum_parti")) for r in ayrik["tohum"]
                                      if r.get("tohum_parti") is not None})
    return ozet


def plan_ozeti(planlar: list[dict]) -> dict:
    return {"toplam": len(planlar),
            "llm_opinion_n": sum(1 for p in planlar if p.get("llm_opinion") is not None),
            "gate_checks_n": sum(1 for p in planlar if p.get("gate_checks")),
            "tohum_partileri": sorted({str(p.get("tohum_parti")) for p in planlar
                                       if p.get("tohum_parti") is not None}),
            "sha256": _sha_rows(planlar)}


def tohum_ozeti(rows: list[dict]) -> dict:
    """Bir tohum diliminin betimleyici özeti: n, R istatistikleri, yıl bazında n, çıkış nedeni."""
    r_degerler = [float(t["r_multiple"]) for t in rows if t.get("r_multiple") is not None]
    yil: dict = {}
    for t in rows:
        d = _tarih(t.get("ts_open")) or _tarih(t.get("ts_close"))
        anahtar = d[:4] if d else "olculemedi"
        yil[anahtar] = yil.get(anahtar, 0) + 1
    neden: dict = {}
    for t in rows:
        k = str(t.get("exit_reason") or "olculemedi")
        neden[k] = neden.get(k, 0) + 1
    ts_kapanislar = [d for d in (_tarih(t.get("ts_close")) for t in rows) if d]
    return {
        "n": len(rows),
        "avg_r": round(sum(r_degerler) / len(r_degerler), 4) if r_degerler else None,
        "medyan_r": round(statistics.median(r_degerler), 4) if r_degerler else None,
        "kazanma_orani": (round(sum(1 for r in r_degerler if r > 0) / len(r_degerler), 4)
                          if r_degerler else None),
        "olculemedi_r_n": len(rows) - len(r_degerler),
        "pnl_toplam": round(sum(float(t["pnl_dollars"]) for t in rows
                                if t.get("pnl_dollars") is not None), 2) if rows else 0.0,
        "pnl_olculemedi_n": sum(1 for t in rows if t.get("pnl_dollars") is None),
        "yil_bazinda": dict(sorted(yil.items())),
        "cikis_nedeni": dict(sorted(neden.items())),
        "ilk_ts_close": min(ts_kapanislar) if ts_kapanislar else None,
        "son_ts_close": max(ts_kapanislar) if ts_kapanislar else None,
        "sha256": _sha_rows(rows),
    }


def sizinti_olc(rows: list[dict], uyelik_fn, hic_uye: set) -> dict:
    """PIT SIZINTISI: açılış tarihinde üye OLMAYAN sembolde açılmış işlem var mı (beklenen 0).

    EDG-079'un (ticker, ts_open) çift eşlemesinin DOĞRUDAN karşılığı: burada eski bir sızıntı
    listesiyle eşleştirme yapılmaz, ÜYELİK FONKSİYONUNUN KENDİSİNE sorulur — kıyas çapası eski
    ölçümün defterine değil bu koşumun kendi üyelik kaynağına bağlanır. `ts_open` ayrıştırılamayan
    satır SESSİZCE geçmez: `olculemedi_n` olarak sayılır."""
    uye_olmayan, hic_uye_esen, olculemedi = [], [], 0
    for t in rows:
        d = _tarih(t.get("ts_open"))
        tic = str(t.get("ticker") or "").upper()
        if d is None or not tic:
            olculemedi += 1
            continue
        if tic not in uyelik_fn(d):
            uye_olmayan.append({"ticker": tic, "ts_open": d})
            if tic in hic_uye:
                hic_uye_esen.append({"ticker": tic, "ts_open": d})
    return {"n_islem": len(rows), "n_uye_olmayan": len(uye_olmayan),
            "n_hic_uye": len(hic_uye_esen), "olculemedi_n": olculemedi,
            "ornek_uye_olmayan": uye_olmayan[:10],
            "beklenen": {"n_uye_olmayan": 0, "n_hic_uye": 0},
            "not": ("varyant A hiç-üye 6 sembolü de HARİÇ tutar; ikisinin de 0 olması beklenir. "
                    "ASİMETRİ (tasarım §2): süzgeç üye-olmayanı düşürür ama o tarihte üye olup "
                    "barı artık evrende bulunmayan sembolü GERİ GETİREMEZ — PIT tohum bir ÜST SINIRDIR.")}


def yeni_tohum_damgala(trades: list[dict], damgalar: dict) -> list[dict]:
    """Replay işlemlerine tohum damgalarını basar ve `kaynak=replay_seed` damgasını `ledgerstamp`
    kapısından geçirir. `stamp` var olan geçerli damgayı EZMEZ (o yasa burada da geçerli)."""
    out = []
    for t in trades:
        r = dict(t)
        r.update(damgalar)
        r["strategy_version"] = TOHUM_SURUM
        out.append(r)
    return ledgerstamp.stamp_rows(out, ledgerstamp.REPLAY_SEED)


def yeni_plan_damgala(planlar: list[dict], damgalar: dict) -> list[dict]:
    """Tohum planlarına parti damgasını basar — bir sonraki değişimin `plan_ayir` ölçütü (0)."""
    out = []
    for p in planlar:
        r = dict(p)
        r["tohum_parti"] = damgalar["tohum_parti"]
        r["pit_uyelik"] = damgalar["pit_uyelik"]
        r["varyant"] = damgalar["varyant"]
        r["strategy_version"] = TOHUM_SURUM
        out.append(r)
    return out


# ==================================================================================================
# KAPI-0 — canlı worker + silahlı plan (ÖLÇÜLÜR, uydurulmaz)
# ==================================================================================================

def kapi_0(uygula: bool) -> dict:
    esik = float(run.RESEED_HEARTBEAT_FRESH_S)      # TEK KAYNAK: eşik burada yeniden yazılmaz
    yas = health.heartbeat_age_seconds()
    bayat = health.stale(esik)
    pf = store.read_json(PORTFOLIO, {}) or {}
    armed = pf.get("armed") or []
    nedenler = []
    if not uygula:
        nedenler.append("kuru koşum: yazım istenmedi (`--uygula` yok)")
    if not bayat:
        nedenler.append(f"nabız TAZE ({yas}sn < {esik}sn) — canlı worker koşuyor; tohum değişimi "
                        f"onun defterini altından çeker (run.replay_seed ile AYNI kapı)")
    if armed:
        nedenler.append(f"{len(armed)} silahlı plan var ({', '.join(str(a.get('ticker')) for a in armed)}) "
                        f"— defter değişimi o planların zeminini çeker")
    return {"esik_s": esik, "nabiz_yasi_s": (round(yas, 1) if yas is not None else None),
            "nabiz_bayat": bayat, "armed_n": len(armed),
            "armed": [str(a.get("ticker")) for a in armed],
            "uygula_istendi": bool(uygula),
            "uygula_izni": bool(uygula and bayat and not armed),
            "nedenler": nedenler,
            "not": ("nabız yaşı ÖLÇÜLEMEZSE `health.stale` fail-closed BAYAT sayar — o hâlde kapı "
                    "AÇILIR; Rol-1 worker'ı ayrıca `ops/stop-worker.sh` ile durdurmuş olmalıdır")}


# ==================================================================================================
# YAZIM — arşiv ÖNCE, sonra defterler (sıra bilinçli)
# ==================================================================================================

def arsiv_yaz(yol, tohum_trades: list[dict], tohum_planlar: list[dict]) -> dict:
    """Eski tohumu (işlem + plan) TEK bir JSONL arşivine yazar ve yanına `.sha256` düşer.

    SATIR BİÇİMİ: `{"defter": "<ad>", "satir": {…}}`. Sarmalayıcı ZORUNLU çünkü iki ayrı defterin
    satırları tek dosyada duruyor ve orijinal satır BOZULMADAN (hiçbir alan eklenmeden) içeride
    kalmalı — arşivin değeri bit-aynılığındadır. Arşiv SİLİNMEZ ve ÜZERİNE YAZILMAZ: hedef dosya
    zaten varsa FileExistsError (tarihçe-koru)."""
    yol = pathlib.Path(yol)
    yol.parent.mkdir(parents=True, exist_ok=True)
    if yol.exists():
        raise FileExistsError(f"arşiv hedefi ZATEN VAR, üzerine yazılmaz: {yol}")
    govde = "".join(
        json.dumps({"defter": defter, "satir": satir}, sort_keys=True, ensure_ascii=False) + "\n"
        for defter, satirlar in ((LEDGER, tohum_trades), (PLAN_DEFTERI, tohum_planlar))
        for satir in satirlar)
    yol.write_text(govde, encoding="utf-8")
    sha = hashlib.sha256(govde.encode("utf-8")).hexdigest()
    sha_yolu = yol.with_suffix(yol.suffix + ".sha256")
    sha_yolu.write_text(f"{sha}  {yol.name}\n", encoding="utf-8")
    return {"arsiv_yolu": str(yol), "arsiv_sha_yolu": str(sha_yolu), "arsiv_sha256": sha,
            "arsiv_n_trades": len(tohum_trades), "arsiv_n_planlar": len(tohum_planlar),
            "arsiv_bayt": len(govde.encode("utf-8")),
            "trades_sha256": _sha_rows(tohum_trades), "planlar_sha256": _sha_rows(tohum_planlar)}


def _egri_isareti_yaz(onceki_n: int, yeni_n: int, ts: str) -> dict:
    """Eğri zarfına `tohum_degisimi` işareti düşer — `points` DİZİSİNE DOKUNMAZ (ruling 3).

    Anahtar `sermaye.CURVE_MARK_KEY`den, mevcut işaretler `sermaye._egri_isaretleri`den okunur;
    ikinci bir literal burada yazılmaz. İşarete BİLEREK `egri_son_nokta` KONMAZ: o alan
    `ledgerstamp._sinir_reset_isaretinden`in çapraz-sağlama yoludur ve "reset ANINDA eğrinin son
    noktası" anlamına gelir — tohum sınırını oraya yazmak o alanın anlamını sessizce değiştirirdi.
    Alan yokluğu zararsızdır: o okuyucu sondan geriye tarar ve konuşabilen ilk işareti alır."""
    isaret = {"id": f"TD-{ts.replace(':', '').replace('-', '')}", "tur": "tohum_degisimi",
              "tip": "tohum_degisimi", "ts": ts, "tarih": ts,
              "tohum_parti": TOHUM_PARTI, "pit_uyelik": PIT_UYELIK, "varyant": VARYANT,
              "onceki_n": onceki_n, "yeni_n": yeni_n, "tohum_surumu": TOHUM_SURUM,
              "gerekce": (f"TSK-159 S5: tohum dilimi PIT üyelikle (varyant A, uyelik=as_of) "
                          f"yeniden kuruldu; eski tohum arşivlendi, `points` DOKUNULMADI"),
              "not": ("bu işaret bir SERMAYE RESETİ DEĞİLDİR: kitap, `realized_pnl` ve eğri "
                      "noktaları değişmedi — yalnız defterin tohum dilimi değişti. `egri_son_nokta` "
                      "alanı BİLEREK YOKTUR (bkz. ops/tohum_pit_yenile.py::_egri_isareti_yaz)")}
    with store.file_lock(EQUITY):
        eq = store.read_json(EQUITY, {}) or {}
        eq[sermaye.CURVE_MARK_KEY] = sermaye._egri_isaretleri(eq) + [isaret]
        store.write_json(EQUITY, eq)
    return isaret


def _yaz(*, eski_tohum, eski_tohum_planlar, yeni_tohum, korunan_trades,
         yeni_planlar, korunan_planlar, yedek_dizin, ts) -> dict:
    """Sıra BİLİNÇLİ: (1) arşiv, (2) işlem defteri, (3) plan defteri, (4) eğri işareti.

    Arşiv ÖNCE çünkü tek geri dönüş yolu odur: arşiv düşerse hiçbir defter değişmemiş olur.
    Eğri işareti EN SON çünkü tek başına zararsız bir BEYANDIR ve yarım kalırsa yalnız beyan eksik
    kalır — defterler tutarlıdır."""
    yedek_dizin = pathlib.Path(yedek_dizin)
    arsiv = arsiv_yaz(yedek_dizin / f"tohum-arsiv-{ts}.jsonl", eski_tohum, eski_tohum_planlar)

    yeni_defter = list(yeni_tohum) + list(korunan_trades)
    with store.file_lock(LEDGER):
        store.write_jsonl(LEDGER, yeni_defter)

    yeni_plan_defteri = list(yeni_planlar) + list(korunan_planlar)
    with store.file_lock(PLAN_DEFTERI):
        store.write_jsonl(PLAN_DEFTERI, yeni_plan_defteri)

    isaret = _egri_isareti_yaz(len(eski_tohum), len(yeni_tohum), ts)
    return {"calisti": True, "ts": ts, **arsiv,
            "trades": {"yazilan_n": len(yeni_defter), "yeni_tohum_n": len(yeni_tohum),
                       "korunan_n": len(korunan_trades)},
            "trade_plans": {"yazilan_n": len(yeni_plan_defteri),
                            "yeni_tohum_n": len(yeni_planlar),
                            "korunan_n": len(korunan_planlar)},
            "egri_isareti": isaret,
            "dokunulmayanlar": ["scoreboard.json", "candidates.jsonl", "portfolio.json",
                                "equity_curve.json:points", "state/history/*"]}


# ==================================================================================================
# YAZIM SONRASI DOĞRULAMA — betik kendi ölçer, EŞİK YOK (hüküm Rol-1'in)
# ==================================================================================================

def _korunum() -> dict:
    try:
        rapor = watchdog.conservation_report()
    except Exception as e:  # sessiz-yutma DEĞİL: neden ADIYLA rapora girer, sayı UYDURULMAZ
        return {"calisti": False, "aciklanamayan": None,
                "neden": f"watchdog.conservation_report düştü: {type(e).__name__}: {e}"}
    return {"calisti": True, "plans": rapor.get("plans"),
            "aciklanamayan": rapor.get("unexplained"),
            "not": "eşik YOK — 2026-08-13'te bu kapı 3 ile düşmüş ve gerekçesiyle kabul edilmişti"}


def _dsr_pbo() -> dict:
    try:
        return {"calisti": True, "trio": analytics.validation_trio()}
    except Exception as e:  # sessiz-yutma DEĞİL: DSR/PBO ölçülemedi ve nedeni rapora yazıldı
        return {"calisti": False, "trio": None,
                "neden": f"analytics.validation_trio düştü: {type(e).__name__}: {e}"}


def _rollback_kapisi(goal: dict) -> dict:
    """Geri-alma kapısının KARAR NOKTASINA KADARki girdileri (EDG-036b `BAYRAK_rollback_kapisi`
    deseniyle AYNI türetim). `_would_have` replay'i BURADA KOŞULMAZ — o bar tabanı ister ve
    kararın kendisi bu betiğin işi değildir; rapor girdileri taşır, hükmü Rol-1 verir."""
    try:
        st = config.load_strategy()
        v, par = int(st.get("version", 1)), st.get("parent")
        tr = store.read_jsonl(LEDGER)
        ereg = rollback._ship_eval_regime(v)
        trs = [t for t in tr if str(t.get("regime")) == ereg] if ereg else tr
        cur = [t for t in trs if t.get("strategy_version") == v]
        pr = [t for t in trs if t.get("strategy_version") == par]
        ms = int(goal["min_sample"])
        sbv = (versioning.scoreboard().get("versions", {}) or {}).get(str(par), {}) or {}
        cur_score = score_mod.score(cur, goal) if len(cur) >= ms else None
        par_score = score_mod.score(pr, goal) if len(pr) >= ms else None
        yol = "islemlerden"
        if par_score is None and not ereg:
            par_score = sbv.get("live_score", sbv.get("backtest_oos"))
            yol = "scoreboard.live_score|backtest_oos"
        par_score2 = rollback._parent_score_fallback(v, par_score)
        if par_score2 != par_score:
            yol = "shipping_gate_incumbent_oos (_parent_score_fallback)"
        esik = goal.get("rollback_if_worse_by")
        delta = (None if (cur_score is None or par_score2 is None)
                 else round(cur_score - par_score2, 4))
        return {"calisti": True, "version": v, "parent": par, "ship_eval_regime": ereg,
                "min_sample": ms, "n_cur": len(cur), "n_parent": len(pr),
                "cur_score": cur_score, "par_score": par_score2, "par_score_yolu": yol,
                "rollback_if_worse_by": esik, "ham_delta": delta,
                "KAPI_ACILIYOR": (None if (delta is None or esik is None)
                                  else bool(delta < -float(esik))),
                "not": ("nihai karar `rollback._karar_girdisi` (would_have replay'i) ile verilir — "
                        "o replay BURADA KOŞULMADI; bunlar karar noktasına KADARki girdilerdir")}
    except Exception as e:  # sessiz-yutma DEĞİL: girdiler ölçülemedi ve neden rapora ADIYLA girdi
        return {"calisti": False, "neden": f"{type(e).__name__}: {e}"}


def _kimlik_cakismasi(rows: list[dict], alan: str = "id") -> dict:
    sayac: dict = {}
    for r in rows:
        k = str(r.get(alan))
        sayac[k] = sayac.get(k, 0) + 1
    cift = sorted(k for k, n in sayac.items() if n > 1 and k != "None")
    return {"toplam": len(rows), "tekil": len(sayac), "cift_n": len(cift), "cift": cift[:20]}


def dogrulama_yap(*, onceki_korunan_sha, onceki_realized, onceki_points, goal) -> dict:
    """YAZIM SONRASI ölçüm — defter DİSKTEN yeniden okunur (bellekteki nesne değil)."""
    rows = store.read_jsonl(LEDGER)
    planlar = store.read_jsonl(PLAN_DEFTERI)
    ayrik = defter_ayir(rows)
    pf = store.read_json(PORTFOLIO, {}) or {}
    eq = store.read_json(EQUITY, {}) or {}
    sonra_korunan_sha = _sha_rows(ayrik["korunan"])
    sinir = ledgerstamp.seed_boundary()
    tohum_max = max((_tarih(t.get("ts_close")) or "" for t in ayrik["tohum"]), default="") or None
    return {
        "calisti": True,
        "canli": {"korunan_n": len(ayrik["korunan"]), "sha256_once": onceki_korunan_sha,
                  "sha256_sonra": sonra_korunan_sha,
                  "bit_ayni": bool(onceki_korunan_sha == sonra_korunan_sha)},
        "realized_pnl": {"once": onceki_realized, "sonra": pf.get("realized_pnl"),
                         "ayni": bool(pf.get("realized_pnl") == onceki_realized)},
        "yeni_tohum_n": len(ayrik["tohum"]),
        "seed_boundary": sinir,
        "seed_boundary_yeni_tohum_max_ts_close": tohum_max,
        "seed_boundary_eslesti": bool(sinir.get("replay_end") == tohum_max),
        "counts": ledgerstamp.counts(rows),
        "equity": {"n_nokta_once": onceki_points, "n_nokta_sonra": len((eq.get("points") or [])),
                   "points_ayni": bool(len(eq.get("points") or []) == onceki_points),
                   "n_isaret": len(sermaye._egri_isaretleri(eq))},
        "trades_kimlik": _kimlik_cakismasi(rows),
        "planlar_kimlik": _kimlik_cakismasi(planlar),
        "korunum": _korunum(),
        "dsr_pbo": _dsr_pbo(),
        "rollback_kapisi": _rollback_kapisi(goal),
        "not": ("EŞİK YOK: bu blok ÖLÇÜMdür, hüküm Rol-1'indir. `trades_kimlik.cift_n` > 0 ise "
                "tohum ve canlı satırlar aynı `T%05d` numarasını paylaşıyor demektir — bu betik "
                "YENİDEN NUMARALAMAZ (ayrı araç: ops/trade_id_yeniden_numarala.py)."),
    }


# ==================================================================================================
# ANA GÖVDE
# ==================================================================================================

def calistir(*, girdi_html, guncel_liste, uygula=False, baslangic=VARSAYILAN_BASLANGIC,
             bitis=None, rapor_dizin=None, yedek_dizin=VARSAYILAN_YEDEK_DIZIN,
             kart_yolu=KART036, olcum_yolu=EDG082_OLCUM, kapi_atla=False) -> dict:
    """Uçtan uca gövde (CLI'nin çağırdığı GERÇEK yol — testler bunu doğrudan da çağırabilir)."""
    simdi = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    ts = simdi.strftime("%Y%m%dT%H%M%SZ")
    rapor: dict = {
        "arac": BETIK_ADI,
        "mod": "uygula" if uygula else "kuru",
        "zaman": simdi.isoformat(),
        "sozlesme": {"tohum_parti": TOHUM_PARTI, "pit_uyelik": PIT_UYELIK, "varyant": VARYANT,
                     "tohum_surumu": TOHUM_SURUM, "kaynak_damgasi": ledgerstamp.REPLAY_SEED,
                     "damga_alanlari": list(DAMGA_ALANLARI),
                     "plan": "docs/superpowers/plans/2026-09-07-s5-tohum-pit.md",
                     "kartlar": ["EDG-2026-082", "EDG-2026-036"]},
        "acik_sorular": [],
    }
    rapor["kapi_0"] = kapi_0(uygula)

    # ---- ÖNCEKİ DEFTER (salt-okuma) ------------------------------------------------------------
    eski_rows = store.read_jsonl(LEDGER)
    eski_planlar = store.read_jsonl(PLAN_DEFTERI)
    pf = store.read_json(PORTFOLIO, {}) or {}
    eq = store.read_json(EQUITY, {}) or {}
    ayrik = defter_ayir(eski_rows)
    eski_tohum, korunan_trades = ayrik["tohum"], ayrik["korunan"]
    eski_tohum_siniri = max((_tarih(t.get("ts_close")) or "" for t in eski_tohum), default="") or None
    korunan_plan_idleri = {str(t.get("plan_id")) for t in korunan_trades if t.get("plan_id")}
    plan_ayrik = plan_ayir(eski_planlar, korunan_plan_idleri=korunan_plan_idleri,
                           eski_tohum_siniri=eski_tohum_siniri)
    onceki_korunan_sha = _sha_rows(korunan_trades)
    rapor["onceki"] = {
        "trades": defter_ozeti(eski_rows),
        "trade_plans": plan_ozeti(eski_planlar),
        "trade_plans_ayrim": {"tohum_n": len(plan_ayrik["tohum"]),
                              "korunan_n": len(plan_ayrik["korunan"]),
                              "eski_tohum_siniri": eski_tohum_siniri,
                              "siniri_olculemedi": eski_tohum_siniri is None},
        "portfolio": {"realized_pnl": pf.get("realized_pnl"), "cash": pf.get("cash"),
                      "armed_n": len(pf.get("armed") or [])},
        "equity": {"n_nokta": len(eq.get("points") or []),
                   "n_isaret": len(sermaye._egri_isaretleri(eq))},
        "eski_tohum": tohum_ozeti(eski_tohum),
    }

    # ---- KAPI-0 REDDİ: pahalı hiçbir şey koşturulmaz -------------------------------------------
    if uygula and not rapor["kapi_0"]["uygula_izni"]:
        rapor["replay"] = {"calisti": False, "neden": "KAPI-0 reddi — replay koşulmadı"}
        rapor["kiyas"] = {"calisti": False, "neden": "KAPI-0 reddi"}
        rapor["girdi_kimligi"] = {"calisti": False, "neden": "KAPI-0 reddi"}
        rapor["yazim"] = {"calisti": False, "neden": "KAPI-0 reddi: " + "; ".join(rapor["kapi_0"]["nedenler"])}
        rapor["dogrulama"] = {"calisti": False, "neden": "yazım yapılmadı"}
        rapor["gecerli"] = False
        rapor["beyan"] = "KAPI-0 REDDETTİ — hiçbir bayt yazılmadı."
        return rapor

    # ---- PARAMETRE / HEDEF ---------------------------------------------------------------------
    if not config.strategy_path().exists():
        rapor["gecerli"] = False
        rapor["replay"] = {"calisti": False, "neden": "strategy.yaml YOK"}
        rapor["kiyas"] = {"calisti": False, "neden": "strategy.yaml YOK"}
        rapor["girdi_kimligi"] = {"calisti": False, "neden": "strategy.yaml YOK"}
        rapor["yazim"] = {"calisti": False, "neden": "strategy.yaml YOK"}
        rapor["dogrulama"] = {"calisti": False, "neden": "yazım yapılmadı"}
        rapor["beyan"] = (
            f"DURDU: `{config.strategy_path()}` YOK. `config.load_strategy()` o hâlde sessizce "
            f"`default_strategy()`e düşer ve tohum, YÜRÜRLÜKTEKİ paketi değil varsayılanları "
            f"temsil ederdi — bu, tohum damgasının beyanını yalanlar. Betik dosyayı YAZMAZ "
            f"(kuru koşum sözleşmesi); Rol-1 canlı kurulumda koşturur.")
        return rapor

    strateji = config.load_strategy()
    params = strateji["params"]
    goal = config.goal()
    params_sha = hashlib.sha256(json.dumps(params, sort_keys=True).encode("utf-8")).hexdigest()

    # ---- ÜYELİK TÜRETİMİ (EDG-082 ölçüm betiğinden İTHAL — kopya YOK) ---------------------------
    o = kaynaktan_yukle(olcum_yolu, "edg082_olcum_s5")
    degisiklikler, tablo_meta, html_sha = o.degisiklikleri_yukle(girdi_html)
    guncel = o.guncel_liste_oku(guncel_liste)
    guncel_sha = _sha_dosya(guncel_liste)
    fonksiyonlar = o.uyelik_fonksiyonlarini_kur(degisiklikler, guncel)
    uyelik_a = fonksiyonlar[VARYANT]
    hic_uye = set(fonksiyonlar["_hic_uye_set"])

    # ---- BARLAR + PENCERE ----------------------------------------------------------------------
    bars, index_bars = dataset.load()
    seanslar = sorted({str(x)[:10] for x in index_bars["date"]}) if len(index_bars) else []
    bitis_kaynak = "--bitis"
    if not bitis:
        if not seanslar:
            rapor["gecerli"] = False
            rapor["beyan"] = ("DURDU: `--bitis` verilmedi ve endeks barı BOŞ — son tam seans "
                              "ÖLÇÜLEMEDİ, uydurulmaz.")
            return rapor
        bitis = seanslar[-1]
        bitis_kaynak = "endeks barlarının SON tarihi (ölçüldü, uydurulmadı)"

    kunye = olcum_araclari.kod_surumu_damgasi(KOK)
    serh = friksiyon_serhi_oku(kart_yolu)
    rapor["girdi_kimligi"] = {
        "calisti": True,
        "html_yolu": str(girdi_html), "html_sha256": html_sha, "tablo_meta": tablo_meta,
        "guncel_liste_yolu": str(guncel_liste), "guncel_liste_sha256": guncel_sha,
        "guncel_liste_n": len(guncel),
        "params_sha256": params_sha, "strateji_surumu_canli": int(strateji.get("version", 1)),
        "tohum_strateji_surumu": TOHUM_SURUM,
        "baslangic": baslangic, "bitis": bitis, "bitis_kaynak": bitis_kaynak,
        "evren_n": len(bars), "index_n_seans": len(seanslar),
        "motor_kunye": kunye, "friksiyon_serhi": serh,
        "olcum_betigi": str(olcum_yolu), "kart036": str(kart_yolu),
    }

    # ---- REPLAY A ------------------------------------------------------------------------------
    t0 = time.perf_counter()
    res = backtest.replay(params, bars, index_bars, goal, baslangic, bitis,
                          strategy_version=TOHUM_SURUM, with_gate_detail=True, uyelik=uyelik_a)
    sure = round(time.perf_counter() - t0, 3)

    damgalar = {"tohum_parti": TOHUM_PARTI, "pit_uyelik": PIT_UYELIK, "varyant": VARYANT,
                "params_sha256": params_sha, "guncel_liste_sha256": guncel_sha,
                "html_sha256": html_sha, "motor_kunye": kunye.get("git_head"),
                "motor_kunye_kirli": kunye.get("kirli_agac"),
                "pencere": f"{baslangic}..{bitis}", "evren_n": len(bars),
                "friksiyon_serhi": serh}
    yeni_tohum = yeni_tohum_damgala(res.trades or [], damgalar)

    # PLAN DEFTERİ: 2026-08-13 şeması — son 300 plan + İŞLEME DÖNÜŞEN her plan (run.replay_seed ile
    # AYNI kural; kopya değil, aynı iki satır: aksi hâlde işlemlerin çoğu var olmayan plana bakar).
    ham_planlar = res.plan_log or []
    gerekli = {t.get("plan_id") for t in (res.trades or []) if t.get("plan_id")}
    tut = ham_planlar[-300:]
    var = {p.get("id") for p in tut}
    tut = [p for p in ham_planlar if p.get("id") in gerekli and p.get("id") not in var] + tut
    yeni_planlar_ham = yeni_plan_damgala(tut, damgalar)
    # KORUNAN PLAN KAZANIR: aynı kimlikte hem tohum hem korunan plan varsa tohum planı DÜŞÜRÜLÜR
    # (canlı kanıt kutsaldır ve çift kimlik korunum dedektörünü belirsizleştirirdi). Sayılır.
    korunan_ids = {str(p.get("id")) for p in plan_ayrik["korunan"]}
    cakisan = sorted({str(p.get("id")) for p in yeni_planlar_ham if str(p.get("id")) in korunan_ids})
    yeni_planlar = [p for p in yeni_planlar_ham if str(p.get("id")) not in korunan_ids]

    rapor["replay"] = {
        "calisti": True, "sure_s": sure, "n_islem": len(res.trades or []),
        "n_plan_ham": len(ham_planlar), "n_plan_tutulan": len(yeni_planlar_ham),
        "n_plan_cakisma_dusen": len(cakisan), "n_aday": len(res.candidate_log or []),
        "n_equity_nokta": len(res.equity or []),
        "entry_rejects": res.entry_rejects, "earnings_gate": res.earnings_gate,
        "uyelik_cagri_n": len(fonksiyonlar["_cagrilar_a"]),
        "not": ("`equity` ve `candidates` çıktısı KULLANILMADI: eğri `points`ine ve "
                "`candidates.jsonl`a dokunulmuyor (ruling 3 + plan adım 5)."),
    }

    # ---- KIYAS ---------------------------------------------------------------------------------
    eski_ozet = rapor["onceki"]["eski_tohum"]
    yeni_ozet = tohum_ozeti(yeni_tohum)
    kapi = {"calisti": False, "neden": "--kapi-atla verildi"}
    if not kapi_atla:
        try:
            kapi = {"calisti": True, **o.kapi_hukumleri(uyelik_a, params, bars, index_bars, goal,
                                                        TOHUM_SURUM)}
        except Exception as e:  # sessiz-yutma DEĞİL: kapı özeti ölçülemedi, nedeni raporda
            kapi = {"calisti": False, "neden": f"kapi_hukumleri düştü: {type(e).__name__}: {e}"}
    rapor["kiyas"] = {
        "calisti": True,
        "eski_tohum": eski_ozet, "yeni_tohum": yeni_ozet,
        "delta": {"n": yeni_ozet["n"] - eski_ozet["n"],
                  "avg_r": (None if (yeni_ozet["avg_r"] is None or eski_ozet["avg_r"] is None)
                            else round(yeni_ozet["avg_r"] - eski_ozet["avg_r"], 4)),
                  "medyan_r": (None if (yeni_ozet["medyan_r"] is None or eski_ozet["medyan_r"] is None)
                               else round(yeni_ozet["medyan_r"] - eski_ozet["medyan_r"], 4)),
                  "kazanma_orani": (None if (yeni_ozet["kazanma_orani"] is None
                                             or eski_ozet["kazanma_orani"] is None)
                                    else round(yeni_ozet["kazanma_orani"] - eski_ozet["kazanma_orani"], 4)),
                  "pnl_toplam": round(yeni_ozet["pnl_toplam"] - eski_ozet["pnl_toplam"], 2)},
        "sizinti": sizinti_olc(yeni_tohum, uyelik_a, hic_uye),
        "eski_tohum_sizinti": sizinti_olc(eski_tohum, uyelik_a, hic_uye),
        "kapi": kapi,
        "plan_cakismasi": {"n": len(cakisan), "kimlikler": cakisan[:20]},
        "not": ("eşik YOK — hüküm Rol-1'in (kart EDG-2026-082 eşikleri). `eski_tohum_sizinti` "
                "kıyas çapasıdır: aynı üyelik fonksiyonu ESKİ tohuma uygulanınca kaç sızıntı "
                "görünüyor (EDG-079 hükmü: 885 satırda 95)."),
    }

    # ---- YAZIM ---------------------------------------------------------------------------------
    if not uygula:
        rapor["yazim"] = {"calisti": False, "neden": "kuru koşum (`--uygula` verilmedi)",
                          "projeksiyon": {"yeni_defter_n": len(yeni_tohum) + len(korunan_trades),
                                          "arsivlenecek_trades_n": len(eski_tohum),
                                          "arsivlenecek_planlar_n": len(plan_ayrik["tohum"]),
                                          "korunacak_trades_n": len(korunan_trades),
                                          "korunacak_planlar_n": len(plan_ayrik["korunan"]),
                                          "yeni_plan_defteri_n": len(yeni_planlar) + len(plan_ayrik["korunan"])}}
        rapor["dogrulama"] = {"calisti": False,
                              "neden": "kuru koşum — yazım yapılmadı, YAZIM SONRASI ölçüm YOK"}
        rapor["gecerli"] = True
    else:
        try:
            rapor["yazim"] = _yaz(eski_tohum=eski_tohum, eski_tohum_planlar=plan_ayrik["tohum"],
                                  yeni_tohum=yeni_tohum, korunan_trades=korunan_trades,
                                  yeni_planlar=yeni_planlar, korunan_planlar=plan_ayrik["korunan"],
                                  yedek_dizin=yedek_dizin, ts=ts)
            rapor["yazim"]["trade_plans"]["cakisan_kimlik_n"] = len(cakisan)
            rapor["yazim"]["trade_plans"]["cakisan_kimlikler"] = cakisan[:20]
            rapor["dogrulama"] = dogrulama_yap(onceki_korunan_sha=onceki_korunan_sha,
                                               onceki_realized=pf.get("realized_pnl"),
                                               onceki_points=len(eq.get("points") or []),
                                               goal=goal)
            rapor["gecerli"] = bool(rapor["dogrulama"]["canli"]["bit_ayni"]
                                    and rapor["dogrulama"]["realized_pnl"]["ayni"]
                                    and rapor["dogrulama"]["equity"]["points_ayni"])
        except Exception as e:  # sessiz-yutma DEĞİL: hata ADIYLA rapora ve stderr'e çıkar, rc=1
            rapor["yazim"] = {"calisti": False,
                              "hata": f"{type(e).__name__}: {e}",
                              "not": ("SIRA GEREĞİ: arşiv İLK adımdır — arşiv aşamasında düşen bir "
                                      "koşum defterlere HİÇ dokunmamıştır. Sonraki aşamalarda "
                                      "düşerse arşiv diskte durur ve geri dönüş oradan yapılır.")}
            rapor["dogrulama"] = {"calisti": False, "neden": "yazım düştü"}
            rapor["gecerli"] = False
            print(f"HATA (yazım): {type(e).__name__}: {e}", file=sys.stderr)

    rapor["beyan"] = (
        "Bu betik `run.replay_seed` ÇAĞIRMAZ (EDG-036 kill: canlı satırları siler, planları ezer, "
        "karneyi arşivler). Yazım yalnız `store` kapısından geçer; `scoreboard.json`, "
        "`candidates.jsonl`, `portfolio.json` ve `equity_curve.json:points` DOKUNULMAZ. Barlar "
        "ÜRETİM yolundan (`dataset.load`) gelir — EDG-082 ölçümü bilerek ayrı bir minimal temizlik "
        "(`temiz_bar_oku`) kullanmıştı, yani bu koşumun bar temizliği ölçümünkinden FARKLIDIR ve "
        "iki koşumun işlem sayıları birebir eşit çıkmayabilir. `uyelik` süzgeci üye-olmayanı "
        "düşürür ama delist barını GERİ GETİREMEZ: PIT tohum bir ÜST SINIRDIR (tasarım §2).")
    rapor["acik_sorular"] = [
        "trade `id` (T%05d) yeniden numaralama BU BETİĞİN İŞİ DEĞİL: yeni tohum T00001'den başlar "
        "ve korunan canlı satırlarla çakışabilir — `dogrulama.trades_kimlik.cift_n` ölçer, "
        "düzeltmeyi `ops/trade_id_yeniden_numarala.py` yapar (Rol-1 kararı).",
        "aynı kimlikte hem tohum hem canlı plan varsa TOHUM planı düşürülür (canlı kazanır); "
        "plan bu kararı yazmıyordu — `kiyas.plan_cakismasi` sayıyı taşır.",
        "`--bitis` verilmezse endeks barlarının SON tarihi alınır; o tarih KISMİ bir seans olabilir "
        "(`dataset.load` aynı-akşam bacağını taşımaz ama önbellek taze olabilir) — Rol-1 son TAM "
        "seansı biliyorsa `--bitis` ile açıkça vermelidir.",
        "`equity_curve.points` DOKUNULMADI (ruling 3): yeni tohumun eğrisi (`res.equity`) "
        "YAZILMADI, yani eğri hâlâ ESKİ tohumun noktalarını taşıyor. Bu bilinçli — ama defter ile "
        "eğri arasındaki bu ayrışma kayda değer bir açık kalemdir.",
    ]
    return rapor


# ==================================================================================================
# RAPOR YAZIMI (YASA 6 okuyucusu) + CLI
# ==================================================================================================

def rapor_md(rapor: dict) -> str:
    g = rapor.get("girdi_kimligi") or {}
    k = rapor.get("kiyas") or {}
    y = rapor.get("yazim") or {}
    d = rapor.get("dogrulama") or {}
    sat = [f"# Tohum PIT yenileme — {rapor['mod'].upper()} ({rapor['zaman']})", "",
           f"- araç: `{rapor['arac']}` · parti: `{TOHUM_PARTI}` · varyant: {VARYANT} "
           f"· üyelik: {PIT_UYELIK} · sv={TOHUM_SURUM}",
           f"- KAPI-0: uygula_izni={rapor['kapi_0']['uygula_izni']} "
           f"({'; '.join(rapor['kapi_0']['nedenler']) or 'engel yok'})",
           f"- pencere: {g.get('baslangic')}..{g.get('bitis')} ({g.get('bitis_kaynak')})",
           f"- girdi: html sha `{str(g.get('html_sha256'))[:16]}…` · güncel liste sha "
           f"`{str(g.get('guncel_liste_sha256'))[:16]}…` · params sha `{str(g.get('params_sha256'))[:16]}…`",
           ""]
    o = rapor.get("onceki") or {}
    if o:
        t = o["trades"]
        sat += ["## Önceki defter",
                f"- trades: toplam {t['toplam']} · replay_seed {t['replay_seed_n']} · "
                f"live_paper {t['live_paper_n']} · belirsiz {t['belirsiz_n']}",
                f"- trade_plans: {o['trade_plans']['toplam']} "
                f"(llm_opinion {o['trade_plans']['llm_opinion_n']}) → tohum "
                f"{o['trade_plans_ayrim']['tohum_n']} / korunan {o['trade_plans_ayrim']['korunan_n']}",
                f"- realized_pnl: {o['portfolio']['realized_pnl']} · eğri noktası "
                f"{o['equity']['n_nokta']}", ""]
    if k.get("calisti"):
        e, n = k["eski_tohum"], k["yeni_tohum"]
        sat += ["## Kıyas — eski tohum ↔ yeni tohum", "",
                "| ölçüm | eski | yeni | Δ |", "|---|---|---|---|",
                f"| n | {e['n']} | {n['n']} | {k['delta']['n']} |",
                f"| avg_r | {e['avg_r']} | {n['avg_r']} | {k['delta']['avg_r']} |",
                f"| medyan_r | {e['medyan_r']} | {n['medyan_r']} | {k['delta']['medyan_r']} |",
                f"| kazanma | {e['kazanma_orani']} | {n['kazanma_orani']} | {k['delta']['kazanma_orani']} |",
                f"| pnl$ | {e['pnl_toplam']} | {n['pnl_toplam']} | {k['delta']['pnl_toplam']} |", "",
                f"- yıl bazında (yeni): {n['yil_bazinda']}",
                f"- çıkış nedeni (yeni): {n['cikis_nedeni']}",
                f"- SIZINTI (yeni): üye-olmayan {k['sizinti']['n_uye_olmayan']} · hiç-üye "
                f"{k['sizinti']['n_hic_uye']} · ölçülemedi {k['sizinti']['olculemedi_n']}",
                f"- SIZINTI (eski, aynı üyelikle): üye-olmayan {k['eski_tohum_sizinti']['n_uye_olmayan']}",
                f"- kapı: {k['kapi'].get('oos_durum') or k['kapi'].get('neden')} "
                f"(oos_score {k['kapi'].get('oos_score')})", ""]
    sat += ["## Yazım", f"- çalıştı: {y.get('calisti')} — {y.get('neden') or y.get('hata') or 'ok'}"]
    if y.get("calisti"):
        sat += [f"- arşiv: `{y['arsiv_yolu']}` (sha256 `{y['arsiv_sha256'][:16]}…`, "
                f"{y['arsiv_n_trades']} işlem + {y['arsiv_n_planlar']} plan)",
                f"- trades: {y['trades']['yazilan_n']} satır "
                f"(yeni tohum {y['trades']['yeni_tohum_n']} + korunan {y['trades']['korunan_n']})",
                f"- trade_plans: {y['trade_plans']['yazilan_n']} satır "
                f"(çakışan kimlik {y['trade_plans'].get('cakisan_kimlik_n')})",
                f"- eğri işareti: `{y['egri_isareti']['id']}` (points DOKUNULMADI)"]
    if d.get("calisti"):
        sat += ["", "## Yazım sonrası doğrulama (EŞİK YOK — hüküm Rol-1'in)",
                f"- canlı satırlar bit-aynı: {d['canli']['bit_ayni']} ({d['canli']['korunan_n']} satır)",
                f"- realized_pnl aynı: {d['realized_pnl']['ayni']} ({d['realized_pnl']['sonra']})",
                f"- seed_boundary.replay_end: {d['seed_boundary']['replay_end']} "
                f"(yeni tohum max ts_close {d['seed_boundary_yeni_tohum_max_ts_close']}, "
                f"eşleşti {d['seed_boundary_eslesti']})",
                f"- counts: {d['counts']['live_paper_n']} live / {d['counts']['replay_seed_n']} tohum "
                f"/ {d['counts']['belirsiz_n']} belirsiz",
                f"- eğri: points {d['equity']['n_nokta_sonra']} (aynı: {d['equity']['points_ayni']}), "
                f"işaret {d['equity']['n_isaret']}",
                f"- korunum açıklanamayan: {d['korunum'].get('aciklanamayan')}",
                f"- işlem kimliği çift: {d['trades_kimlik']['cift_n']} · plan kimliği çift: "
                f"{d['planlar_kimlik']['cift_n']}",
                f"- rollback kapısı: ham_delta {d['rollback_kapisi'].get('ham_delta')} · "
                f"KAPI_ACILIYOR {d['rollback_kapisi'].get('KAPI_ACILIYOR')}"]
    sat += ["", "## Beyan", rapor["beyan"], "", "## Açık sorular"]
    sat += [f"{i}. {s}" for i, s in enumerate(rapor["acik_sorular"], 1)]
    return "\n".join(sat) + "\n"


def rapor_yaz(rapor: dict, rapor_dizin) -> dict:
    d = pathlib.Path(rapor_dizin)
    d.mkdir(parents=True, exist_ok=True)
    js = d / "rapor.json"
    md = d / "rapor.md"
    js.write_text(json.dumps(rapor, indent=2, sort_keys=True, ensure_ascii=False, default=str),
                  encoding="utf-8")
    md.write_text(rapor_md(rapor), encoding="utf-8")
    return {"json": str(js), "md": str(md)}


def ana(argv=None) -> int:
    ap = argparse.ArgumentParser(description="TSK-159 S5 — tohum diliminin PIT üyelikle değişimi")
    ap.add_argument("--girdi-html", required=True,
                    help="S&P 500 tarihsel değişiklik tablosunun HAM HTML'i (EDG-076 içerik-adresli)")
    ap.add_argument("--guncel-liste", required=True, help="donuk güncel üyelik listesi (JSON list)")
    ap.add_argument("--uygula", action="store_true", help="YAZ (varsayılan: kuru koşum)")
    ap.add_argument("--baslangic", default=VARSAYILAN_BASLANGIC)
    ap.add_argument("--bitis", default=None,
                    help="son TAM seans; verilmezse endeks barlarının son tarihi ÖLÇÜLÜR")
    ap.add_argument("--rapor-dizin", default=None,
                    help="rapor.json + rapor.md buraya; VERİLMEZSE rapor yalnız stdout'a "
                         "(kuru koşum o hâlde diskte iz bırakmaz). `--uygula` ile ZORUNLU.")
    ap.add_argument("--yedek-dizin", default=str(VARSAYILAN_YEDEK_DIZIN),
                    help="eski tohum arşivinin yazılacağı dizin (varsayılan: <depo>/backups)")
    ap.add_argument("--kart036", default=str(KART036), help="friksiyon şerhinin OKUNACAĞI kart")
    ap.add_argument("--olcum-betigi", default=str(EDG082_OLCUM),
                    help="varyant A üyelik türetiminin İTHAL EDİLECEĞİ EDG-082 ölçüm betiği")
    ap.add_argument("--kapi-atla", action="store_true",
                    help="kapı hükümlerini (walk_forward) ATLA — pahalı ikinci koşum")
    ns = ap.parse_args(argv)

    if ns.uygula and not ns.rapor_dizin:
        print("KULLANIM HATASI: `--uygula` `--rapor-dizin` İSTER — okuyucusuz yazım YASA 6 ihlali.",
              file=sys.stderr)
        return 2
    for ad, yol in (("--girdi-html", ns.girdi_html), ("--guncel-liste", ns.guncel_liste)):
        if not pathlib.Path(yol).exists():
            print(f"KULLANIM HATASI: {ad} dosyası yok: {yol}", file=sys.stderr)
            return 2

    rapor = calistir(girdi_html=ns.girdi_html, guncel_liste=ns.guncel_liste, uygula=ns.uygula,
                     baslangic=ns.baslangic, bitis=ns.bitis, rapor_dizin=ns.rapor_dizin,
                     yedek_dizin=ns.yedek_dizin, kart_yolu=pathlib.Path(ns.kart036),
                     olcum_yolu=pathlib.Path(ns.olcum_betigi), kapi_atla=ns.kapi_atla)

    if ns.rapor_dizin:
        yollar = rapor_yaz(rapor, ns.rapor_dizin)
        print(f"rapor: {yollar['json']} · {yollar['md']}")
    else:
        print(rapor_md(rapor))
    return 0 if rapor.get("gecerli") else 1


if __name__ == "__main__":
    raise SystemExit(ana())
