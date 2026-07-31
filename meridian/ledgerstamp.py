"""ledgerstamp.py — İŞLEM DEFTERİNİN KAYNAK DAMGASI (denetim bulgusu BT-1'in kapanışı).

NEDEN VAR. `state/trades.jsonl` iki AYRI yazardan besleniyor ve satırlar birbirinden ayırt
edilemiyordu:

  * İLERİ YOL — `loop._persist_trade` → `store.append_jsonl`: canlı kâğıt döngünün gerçekten
    kapattığı işlem. Bu satır GERÇEK KANITTIR.
  * TOHUM YOLU — `run.replay_seed` → `store.write_jsonl` (deftere TEK toplu yazım): geçmiş barlar
    üzerinde `backtest.replay` koşturularak ÜRETİLMİŞ satırlar. Bu satır bir SİMÜLASYONDUR ve
    üstelik BUGÜNKÜ evrenle koşturulduğu için survivorship taşır.

Damga olmadan `learning_scorecard`, skor kalibrasyonu ve alfa/beta ölçümü 95 satırın tamamını
"canlı defter" sanıyordu — yani sistemin kendi hakkındaki en temel sayısı (gerçek canlı n) hiçbir
yerde YOKTU. Bu modül üç şey yapar: (1) ileri yolun damgasını sağlar, (2) mevcut satırları
KANITA dayanarak geriye dönük damgalar, (3) okuyucuların damgayı ayrıştırabileceği tek sayaç
yüzeyini verir.

TOHUM SINIRI UYDURULMAZ, ÖLÇÜLÜR. Sınırın kanıtı `run.replay_seed`in KENDİ yazım sırasıdır:

    run.py:157   store.write_jsonl("trades.jsonl", res.trades)      # defterin TAMAMI
    run.py:158   store.write_json("equity_curve.json", {...})       # HEMEN ardından

`equity_curve.json`ı üretimde başka hiçbir yol yazmaz (tek yazar run.py:158). O hâlde:
  * eğrinin SON NOKTASININ tarihi = replay'in `end` parametresi = tohum penceresinin sınırı;
  * iki dosyanın mtime'ı saniyeler içinde ise defter o toplu yazımdan BU YANA hiç eklenmemiştir
    (append mtime'ı ileri taşırdı) — yani diskteki her satır o toplu yazımın ürünüdür.
İkisi bağımsız kanıttır ve birbirini doğrular; ikisi de yoksa satır `belirsiz` kalır. AYIRT
EDİLEMEYENE İSİM TAKMAK, ölçümü tam da BT-1'in şikâyet ettiği yere geri götürürdü.

CANLI WORKER KOŞARKEN YAZMA: `store` kilidi süreç-içidir (bu depoda belgeli). Migrasyon CLI'si
canlı süreç görürse `--uygula`yı REDDEDER (`--zorla` ile ezilir) — `barrepair` ile AYNI desen ve
AYNI ölçüm fonksiyonu (iki kopya = iki farklı "canlı" tanımı).

KULLANIM:
    python -m meridian.ledgerstamp                 # kuru koşu — sınıflandırma raporu
    python -m meridian.ledgerstamp --json          # aynı rapor, makine-okunur
    python -m meridian.ledgerstamp --uygula        # YAZAR (worker durdurulmuş olmalı)
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys

from . import config, store

# ---- ŞEMA ------------------------------------------------------------------------------------
FIELD = "kaynak"
LIVE_PAPER = "live_paper"        # canlı kâğıt döngünün kapattığı işlem — GERÇEK kanıt
REPLAY_SEED = "replay_seed"      # replay tohumunun ürettiği işlem — "training", canlı DEĞİL
BELIRSIZ = "belirsiz"            # ayırt edilemedi; uydurma yerine dürüst boşluk
GECERLI = frozenset({LIVE_PAPER, REPLAY_SEED, BELIRSIZ})

LEDGER = "trades.jsonl"
EQUITY = "equity_curve.json"

# İKİ YAZIMIN "AYNI ANDA" SAYILDIĞI PENCERE. run.py:157 ve 158 ardışıktır; aradaki tek iş bir
# sözlük kurmaktır (canlı defterde ölçülen fark 4 ms). 5 sn hem yavaş diskte hem yüklü bir VM'de
# rahat pay bırakır, ama bir sonraki SEANSIN append'iyle karışacak kadar geniş değildir.
BULK_WRITE_TOLERANCE_S = 5.0


def stamp(row: dict, kaynak: str) -> dict:
    """Satıra kaynak damgasını bas. VAR OLAN DAMGA EZİLMEZ — bir satırın kökeni bir kez ölçülür;
    ikinci bir yazar onu 'düzeltmeye' kalkarsa migrasyonun kanıtı sessizce kaybolur."""
    if kaynak not in GECERLI:
        raise ValueError(f"geçersiz kaynak damgası: {kaynak!r} (geçerli: {sorted(GECERLI)})")
    if not isinstance(row, dict):
        raise TypeError(f"satır sözlük olmalı, {type(row).__name__} geldi")
    if row.get(FIELD) in GECERLI:
        return row
    row[FIELD] = kaynak
    return row


def stamp_rows(rows: list[dict], kaynak: str) -> list[dict]:
    """Toplu damga — tohum yolunun (`run.replay_seed`) tek çağrısı."""
    return [stamp(r, kaynak) for r in rows]


def kaynak_of(row: dict) -> str:
    """Satırın damgası; yoksa/tanınmıyorsa BELİRSİZ (uydurma yok)."""
    v = row.get(FIELD)
    return v if v in GECERLI else BELIRSIZ


def counts(rows: list[dict] | None = None) -> dict:
    """DEFTER SAYAÇLARI — panonun ve karnenin okuduğu TEK yüzey.

    `belirsiz_n` "kökeni ayırt edilemeyen satır" sayısıdır ve DAMGASIZ satırları da KAPSAR: pano
    açısından ikisi aynı soruya çıkar ("bu satır kanıt mı, simülasyon mu — bilmiyoruz"). Alt kırılım
    `damgasiz_n` ile yanında durur, çünkü ikisi farklı EYLEM gerektirir: damgasız satır migrasyonla
    kapanabilir, açıkça `belirsiz` damgalı satır ise ölçüldü ve ayrılamadı."""
    rows = store.read_jsonl(LEDGER) if rows is None else rows
    live = seed = belirsiz = damgasiz = 0
    for r in rows:
        v = r.get(FIELD)
        if v == LIVE_PAPER:
            live += 1
        elif v == REPLAY_SEED:
            seed += 1
        else:
            belirsiz += 1
            if v is None:
                damgasiz += 1
    return {"live_paper_n": live, "replay_seed_n": seed, "belirsiz_n": belirsiz,
            "damgasiz_n": damgasiz, "toplam": len(rows),
            # OKURA TEK CÜMLE: "training" tohum satırlarının etiketidir (denetim BT-1 dili).
            "training_n": seed,
            "kapsam": ("live_paper = canlı kâğıt döngünün kapattığı işlem; replay_seed = tohum "
                       "koşusunun ÜRETTİĞİ işlem (training, survivorship'li); belirsiz = kökeni "
                       "ölçülemeyen satır (damgasızlar dahil)")}


def split(rows: list[dict] | None = None) -> dict[str, list[dict]]:
    """Defteri damgaya göre ayır — kalibrasyon/atribüsyon okuyucularının payda ayırma yolu."""
    rows = store.read_jsonl(LEDGER) if rows is None else rows
    out: dict[str, list[dict]] = {LIVE_PAPER: [], REPLAY_SEED: [], BELIRSIZ: []}
    for r in rows:
        out[kaynak_of(r)].append(r)
    return out


# ---- GERİYE DÖNÜK SINIR ÖLÇÜMÜ ----------------------------------------------------------------
def _mtime(name: str) -> float | None:
    """Arka uçtan bağımsız son-yazım zamanı (`store.mtime`). DOSYA çağında `stat().st_mtime`,
    SQLite çağında `entity_meta.updated_at`. Ölçülemezse None — uydurma yok."""
    return store.mtime(name)


def _toplu_yazim_olculebilir() -> bool:
    """TOPLU YAZIM İMZASI YALNIZ DOSYA ÇAĞINDA ANLAMLIDIR.

    İmza şuna dayanır: `run.py:163` defteri, `run.py:164` eğriyi yazar; iki AYRI dosyanın mtime'ı
    saniyeler içindeyse defter o toplu yazımdan beri hiç `append` almamıştır. SQLite'a taşındıktan
    sonra iki varlığın damgası TEK migrasyon transaction'ında AYNI ana düşer — yani fark her zaman
    ~0 çıkar ve imza "defter hiç eklenmedi" diye OKUNURDU. Bu bir ölçüm değil, migrasyonun kendi
    gölgesidir. Ölçülemeyen bir imzayı VAR saymak, tam olarak BT-1'in şikâyet ettiği hatadır."""
    return not (store.db_backed(LEDGER) or store.db_backed(EQUITY))


def seed_boundary() -> dict:
    """TOHUM PENCERESİNİN SINIRI — iki bağımsız kanıttan, tahminsiz.

    Kanıt-1 (sınırın KENDİSİ): `equity_curve.json`ın son noktasının tarihi. Bu dosyayı üretimde
    yalnız `run.replay_seed` yazar (run.py:158) ve içeriği replay'in `end` parametresine kadar
    uzanır. Yani "tohum koşusu nereye kadar gitti?" sorusunun defterdeki tek doğrudan cevabı.

    Kanıt-2 (TOPLU YAZIM İMZASI): `trades.jsonl` ile `equity_curve.json`ın mtime farkı. run.py'de
    iki yazım ardışıktır; fark saniyeler içindeyse defter o toplu yazımdan BU YANA hiç `append`
    almamıştır (append mtime'ı ileri taşırdı). İmza varsa "diskteki her satır tohumdur" iddiası
    ölçülmüş olur; yoksa sınır yine Kanıt-1'den okunur ama sonrası canlı eklemeye açıktır.

    Hiçbir kanıt yoksa `replay_end` None döner ve TÜM satırlar `belirsiz` sınıflanır."""
    eq = store.read_json(EQUITY, None)
    pts = (eq or {}).get("points") or []
    replay_end = None
    if pts:
        try:
            replay_end = str(pts[-1][0])[:10]
        except (IndexError, TypeError, ValueError):  # sessiz-yutma: eğri şeması beklenmedik — sınır ÖLÇÜLEMEDİ olarak kalır ve `neden` alanı bunu dışarı söyler (aşağıda), varsayılan bir tarih UYDURULMAZ
            replay_end = None
    _olculebilir = _toplu_yazim_olculebilir()
    t_led, t_eq = (_mtime(LEDGER), _mtime(EQUITY)) if _olculebilir else (None, None)
    delta = None if (t_led is None or t_eq is None) else round(abs(t_led - t_eq), 3)
    toplu = None if delta is None else bool(delta <= BULK_WRITE_TOLERANCE_S)
    if replay_end is None:
        guven, neden = "yok", (f"{EQUITY} okunamadı ya da nokta taşımıyor — tohum penceresinin "
                               f"sınırı ölçülemedi; hiçbir satır sınıflanamaz")
    elif toplu:
        guven, neden = "yuksek", (f"toplu yazım imzası VAR (mtime farkı {delta}sn ≤ "
                                  f"{BULK_WRITE_TOLERANCE_S}sn) — defter, {replay_end} sonuna kadar "
                                  f"koşan tohum yazımından bu yana hiç eklenmemiş")
    else:
        guven, neden = "orta", (f"toplu yazım imzası YOK (mtime farkı {delta}sn) — defter tohum "
                                f"yazımından SONRA da yazılmış; sınır yine {replay_end}, sonrası "
                                f"canlı eklemeye açık")
    return {"replay_end": replay_end, "toplu_yazim": toplu, "mtime_delta_s": delta,
            "n_equity_points": len(pts), "guven": guven, "neden": neden,
            "kanit": (f"{EQUITY} son noktası (tek yazar: run.replay_seed) + "
                      f"{LEDGER}/{EQUITY} mtime çifti"),
            "equity_ilk_nokta": (str(pts[0][0])[:10] if pts else None)}


def classify(rows: list[dict], boundary: dict | None = None) -> list[dict]:
    """Her satır için (kaynak, gerekçe) — SAF fonksiyon, hiçbir şey yazmaz.

    KURALLAR, sırasıyla:
      0. Satırda GEÇERLİ bir damga varsa DOKUNULMAZ (migrasyon idempotenttir).
      1. Sınır ölçülemediyse → `belirsiz`.
      2. `ts_close` yoksa/ayrıştırılamıyorsa → `belirsiz` (satırın hangi tarafta olduğu bilinmez).
      3. `ts_close <= replay_end` → `replay_seed`. Tohum yazımı defterin TAMAMINI yeniden yazar;
         o pencereye düşen her satır o yazımdan çıkmıştır.
      4. `ts_close > replay_end` → `live_paper` — YALNIZ defter tohum yazımından sonra da
         yazılmışsa. Toplu yazım imzası VARSA böyle bir satırın var olması ÇELİŞKİDİR (defter o
         yazımdan beri dokunulmamış olmalıydı) ve çelişki `live_paper` diye çözülmez: `belirsiz`
         kalır. Sınıflandırıcı kendi kanıtını yalanlayamaz."""
    b = boundary if boundary is not None else seed_boundary()
    end = b.get("replay_end")
    toplu = b.get("toplu_yazim")
    out = []

    def _k(kaynak, sinif, gerekce, degisti=True):
        # `sinif` GRUPLANABİLİR kural adıdır, `gerekce` o SATIRIN kanıtıdır. İkisi ayrı olmasaydı
        # rapor 95 satırı 90 ayrı "gerekçe"ye bölerdi (her tarih kendi başına bir metin) ve
        # okuyan "hangi KURAL kaç satırı damgaladı?" sorusunu hiç göremezdi.
        out.append({FIELD: kaynak, "sinif": sinif, "gerekce": gerekce, "degisti": degisti})

    for r in rows:
        mevcut = r.get(FIELD)
        if mevcut in GECERLI:
            _k(mevcut, "zaten_damgali", "satır zaten damgalı — dokunulmadı", degisti=False)
            continue
        if not end:
            _k(BELIRSIZ, "sinir_olculemedi", b.get("neden") or "tohum sınırı ölçülemedi")
            continue
        ts = str(r.get("ts_close") or "")[:10]
        try:
            _dt.date.fromisoformat(ts)
        except ValueError:  # sessiz-yutma: SESSİZ DEĞİL — istisnanın kendisi ÇIKTIYA çevriliyor (satır `belirsiz` damgalanır, `sinif=ts_close_ayristirilamadi` rapordaki sayaca girer ve gerekçe metni satırın yanında durur); ayrıca uyarı basmak, `classify`ın saf-fonksiyon sözleşmesini kırardı
            _k(BELIRSIZ, "ts_close_ayristirilamadi", f"ts_close ayrıştırılamadı ({ts!r})")
            continue
        if ts <= end:
            _k(REPLAY_SEED, "sinir_icinde", f"ts_close {ts} ≤ tohum sınırı {end}")
        elif toplu:
            _k(BELIRSIZ, "celiski_toplu_yazim",
               f"ÇELİŞKİ: ts_close {ts} > tohum sınırı {end} ama toplu yazım imzası defterin o "
               f"yazımdan beri değişmediğini söylüyor")
        else:
            _k(LIVE_PAPER, "sinir_disinda",
               f"ts_close {ts} > tohum sınırı {end} (tohum yazımından sonra eklenmiş)")
    return out


def migrate(apply: bool = False) -> dict:
    """TEK SEFERLİK GERİYE MİGRASYON. Kuru koşu VARSAYILANDIR (`barrepair` kuralı: veri yazan bir
    aracın varsayılanı yazmak olamaz). Uygulama tek atomik `write_jsonl` ile biter."""
    rows = store.read_jsonl(LEDGER)
    b = seed_boundary()
    kararlar = classify(rows, b)
    dagilim: dict[str, int] = {}
    siniflar: dict[str, int] = {}
    for k in kararlar:
        dagilim[k[FIELD]] = dagilim.get(k[FIELD], 0) + 1
        siniflar[k["sinif"]] = siniflar.get(k["sinif"], 0) + 1
    degisecek = sum(1 for k in kararlar if k["degisti"])
    rapor = {"applied": bool(apply), "n": len(rows), "sinir": b, "dagilim": dagilim,
             "degisecek": degisecek, "sinif_ozeti": siniflar,
             "onceki_sayaclar": counts(rows), "yazildi": False,
             "ornek": [{"id": r.get("id"), "ts_close": r.get("ts_close"), **k}
                       for r, k in list(zip(rows, kararlar))[:5]]}
    if not apply or not degisecek:
        return rapor
    yeni = [dict(r, **{FIELD: k[FIELD]}) for r, k in zip(rows, kararlar)]
    store.write_jsonl(LEDGER, yeni)
    rapor["yazildi"] = True
    rapor["sonraki_sayaclar"] = counts(yeni)
    try:
        from . import obs
        obs.warn("ledger_source_stamp_migrated", n=len(yeni), degisen=degisecek,
                 replay_end=b.get("replay_end"), guven=b.get("guven"),
                 **{k: int(v) for k, v in dagilim.items()},
                 detail="BT-1 kapanışı: işlem defteri satırları kaynak damgası kazandı; "
                        "learning_scorecard/skor kalibrasyonu/alfa-beta artık gerçek-canlı n'i "
                        "tohumdan ayırıyor")
    except Exception:  # sessiz-yutma: kayıt kanalı düştü; migrasyonun kendisi diske ATOMİK yazıldı ve rapor çağırana döndü — kayıt denemesi yazımı geri alamaz
        pass
    return rapor


def _worker_running() -> bool:
    """Canlı Meridian süreci var mı? `barrepair`in AYNI ölçümü — kopyalanmaz, çağrılır."""
    from .barrepair import _worker_running as _wr
    return _wr()


def _print(rapor: dict) -> None:
    mod = "UYGULANDI" if rapor.get("yazildi") else ("UYGULAMA İSTENDİ ama değişecek satır yok"
                                                    if rapor.get("applied")
                                                    else "KURU KOŞU (hiçbir bayt yazılmadı)")
    b = rapor["sinir"]
    print(f"[ledgerstamp] {mod}")
    print(f"  tohum sınırı: {b['replay_end']}  (güven: {b['guven']}) — {b['neden']}")
    print(f"  kanıt: {b['kanit']}")
    print(f"  defter satırı: {rapor['n']}, damgası değişecek: {rapor['degisecek']}")
    for k, v in sorted(rapor["dagilim"].items()):
        print(f"   {k:14s} {v}")
    for g, v in sorted(rapor["sinif_ozeti"].items(), key=lambda x: -x[1]):
        print(f"      · {v:4d} × kural: {g}")
    for e in rapor.get("ornek") or []:
        print(f"      örnek: {e.get('id')} ts_close={e.get('ts_close')} → {e[FIELD]} ({e['gerekce']})")
    if not rapor.get("applied") and rapor["degisecek"]:
        print("  → uygulamak için: python -m meridian.ledgerstamp --uygula  "
              "(worker DURDURULMUŞ olmalı)")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="python -m meridian.ledgerstamp",
        description="trades.jsonl satırlarına kaynak damgası (live_paper/replay_seed/belirsiz) basar")
    ap.add_argument("--uygula", action="store_true", help="YAZ (varsayılan: kuru koşu)")
    ap.add_argument("--json", action="store_true", help="raporu JSON olarak bas")
    ap.add_argument("--zorla", action="store_true", help="canlı süreç görülse de yaz (riski sen alırsın)")
    a = ap.parse_args(argv)
    if a.uygula and not a.zorla and _worker_running():
        print("[ledgerstamp] REDDEDİLDİ: canlı Meridian süreci görülüyor. Aynı defteri iki süreç "
              "yeniden yazamaz (store kilidi süreç-içidir). Önce `./ops/stop-worker.sh`, "
              "sonra tekrar dene (ya da --zorla).", file=sys.stderr)
        return 2
    rapor = migrate(apply=a.uygula)
    if a.json:
        print(json.dumps(rapor, ensure_ascii=False, indent=1, default=str))
    else:
        _print(rapor)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
