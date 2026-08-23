#!/usr/bin/env python3
"""plan_geri_doldur.py — kırpılmış `trade_plans` defterine, İŞLEME DÖNÜŞMÜŞ eksik planların iadesi.

NEDEN VAR (2026-08-23 canlı pano ihlal triyajı, kalem 4). Canlı DB'de `trade_plans` TAM 500
satırdı, işlem defteri 893 satır — 535 işlem var olmayan bir plana işaret ediyordu
(plan_join_yok). KÖK KODDAN ÖLÇÜLDÜ: `store.merge_dated_jsonl(cap=500)` defteri her günlük
döngüde son 500 satıra kırpıyordu ve İŞLEME DÖNÜŞEN planları da süpürüyordu. Tohum yazımı
(`run.replay_seed` → `_keep`: son 300 + işleme dönüşen HER plan) bu yasayı 2026-07-22'den beri
uyguluyordu ama replay'in kendi sonunda çağırdığı `loop.daily_cycle` aynı deftere
`merge_dated_jsonl` ile yazınca koruma İLK döngüde geri alınıyordu. Kırpan taraf v274'te kurala
bağlandı (store.merge_dated_jsonl: işleme dönüşen plan kırpılmaz); bu betik GEÇMİŞTE süpürülmüş
olanları geri koyar.

KAYNAK ÖLÇÜMÜ (uydurma yasağı — plan gövdesi işlem satırından TÜRETİLMEZ):
  * `research/olcumler/edg032c_taban_2026-08-22/kosum1/` defterlerinde plan gövdesi YOK —
    `islemler_tam_kontrol.json` yalnız `plan_id` alanını taşır (885/885), şasi (edg032b olcum.py)
    plan defterini artefakta hiç yazmıyor; `state_kontrol/` sandbox'ında da `trade_plans` yok.
  * Yerel A1 yedek tarball'ları da kaynak DEĞİL: kırpma tohumlamanın KENDİ içinde (son
    daily_cycle) olduğu için 08-14 tarball'ındaki DB bile zaten 500 satırdı (ölçüldü:
    backups/a1/state-2026-08-14.tar.gz → trade_plans=500, trades=887).
  * GEÇERLİ KAYNAK: replay determinist ve ÇİFT KAPIYLA kanıtlı (edg032c determinizm.json — iki
    taze-süreç koşumu bayt-özdeş). Aynı donmuş şasinin yeniden koşulduğu bir sandbox'ın
    `trade_plans.jsonl`i (kırpma öncesi tam plan kümesi) ya da kırpma öncesi herhangi bir gerçek
    yedek, eksik plan gövdelerini birebir verir. O koşumu ve canlıya uygulamayı Rol-1 yapar; bu
    betik kaynağı PARAMETRE olarak alır ve kaynakta olmayanı UYDURMAZ — adıyla raporlar.

NE YAPAR. `trades.jsonl`deki plan_id'lerden `trade_plans.jsonl`de karşılığı olmayanları bulur,
verilen kaynak(lar)dan gövdelerini çıkarır ve İDEMPOTENT ekler: var olan hiçbir satıra dokunmaz,
aynı id'yi iki kez eklemez, ikinci koşum yazacak bir şey bulamaz. Kurtarılanlar defterin BAŞINA
(tarih+id sırasıyla) konur — işlem defterinin işaret ettiği eski çağ satırlarıdır.

KULLANIM:
    uv run python ops/plan_geri_doldur.py --kaynak <yol> [--kaynak <yol> ...]   # KURU KOŞU
    uv run python ops/plan_geri_doldur.py --kaynak <yol> --uygula               # YAZ
    MERIDIAN_ROOT=/yol/kopya uv run python ops/plan_geri_doldur.py ...          # sandbox'ta dene
  Kaynak biçimleri: trade_plans.jsonl · plan listesi taşıyan .json · meridian.db (trade_plans
  tablosu, salt-okunur açılır) · state/ dizini (içinde ikisinden biri) · state-*.tar.gz.

ÇIKIŞ KODU: 0 = eksik yok ya da eksiklerin TAMAMI kapandı/kapanabilir · 1 = kaynaklarda
bulunamayan eksik kaldı (kapananlar yine de yazılır) · 2 = kaynak okunamadı / canlı worker
koşuyor (yazım reddedildi).
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import tarfile
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from meridian import health, store  # noqa: E402

PLANS = "trade_plans.jsonl"
TRADES = "trades.jsonl"
# replay_seed'in canlı-worker bekçisiyle AYNI eşik (run.RESEED_HEARTBEAT_FRESH_S): iki yerde iki
# farklı "canlı" tanımı olsaydı biri diğerini sessizce yalanlardı.
WORKER_TAZE_S = 900


# ---- kaynak okuyucular (hepsi SALT-OKUNUR) ------------------------------------------------------
def _jsonl_satirlari(p: Path) -> list[dict]:
    """Bir .jsonl dosyasını satır listesine çevirir; bozuk satır ATLANMAZ, sayılır ve raporlanır
    (sessiz veri kaybı, bu betiğin onarmaya geldiği kusurun ta kendisi)."""
    rows, bozuk = [], 0
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            bozuk += 1
    if bozuk:
        print(f"  UYARI: {p} içinde {bozuk} çözümlenemeyen satır ATLANDI (kaynak yarım olabilir)")
    return rows


def _db_planlari(db: Path) -> list[dict]:
    """SQLite kaynağından plan satırları — `mode=ro` (yedek dosyaya tek bayt yazılmaz; WAL/journal
    yaratma riski dâhil). Tip-koruma sözleşmesi gereği `extra_json` alanları satıra geri açılır."""
    c = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        cols = [r[1] for r in c.execute("PRAGMA table_info(trade_plans)")]
        out = []
        for rec in c.execute("SELECT * FROM trade_plans ORDER BY seq"):
            d = dict(zip(cols, rec))
            extra = d.pop("extra_json", None)
            d.pop("seq", None)
            d = {k: v for k, v in d.items() if v is not None}
            if extra:
                try:
                    d.update(json.loads(extra))   # storage sözleşmesi: okumada extra KAZANIR
                except (TypeError, ValueError):
                    pass
            out.append(d)
        return out
    finally:
        c.close()


def kaynak_planlari(yol: Path) -> list[dict]:
    """Tek kaynaktan plan satırlarını çıkarır; biçim yoldan ölçülür, varsayılmaz."""
    if yol.is_dir():
        for aday in (yol / PLANS, yol / "meridian.db", yol / "state" / PLANS,
                     yol / "state" / "meridian.db"):
            if aday.exists():
                return kaynak_planlari(aday)
        raise FileNotFoundError(f"{yol}: dizinde {PLANS} ya da meridian.db yok")
    if yol.suffix == ".jsonl":
        return _jsonl_satirlari(yol)
    if yol.suffix == ".db":
        return _db_planlari(yol)
    if yol.suffix == ".json":
        veri = json.loads(yol.read_text())
        if not isinstance(veri, list):
            raise ValueError(f"{yol}: plan LİSTESİ bekleniyordu, {type(veri).__name__} geldi")
        return [r for r in veri if isinstance(r, dict)]
    if yol.name.endswith(".tar.gz") or yol.name.endswith(".tgz"):
        with tarfile.open(yol) as tar, tempfile.TemporaryDirectory() as tmp:
            for uye in (f"state/{PLANS}", "state/meridian.db"):
                try:
                    tar.extract(uye, tmp)
                except KeyError:
                    continue
                return kaynak_planlari(Path(tmp) / uye)
        raise FileNotFoundError(f"{yol}: arşivde state/{PLANS} ya da state/meridian.db yok")
    raise ValueError(f"{yol}: tanınmayan kaynak biçimi (jsonl/json/db/dizin/tar.gz)")


# ---- ölçüm + yazım ------------------------------------------------------------------------------
def olc(kaynaklar: list[Path]) -> dict:
    """Eksikleri ve kaynaklardan kurtarılabilenleri ÖLÇER; hiçbir bayt yazmaz."""
    trades = store.read_jsonl(TRADES)
    planlar = store.read_jsonl(PLANS)
    mevcut = {p.get("id") for p in planlar if p.get("id")}
    gerekli = {t.get("plan_id") for t in trades if t.get("plan_id")}
    eksik = sorted(x for x in gerekli - mevcut)

    havuz: dict[str, dict] = {}
    for yol in kaynaklar:
        for r in kaynak_planlari(yol):
            rid = r.get("id")
            if rid and rid not in havuz:      # İLK kaynak kazanır (sıra çağıranın beyanıdır)
                havuz[rid] = r
    bulunan = [havuz[i] for i in eksik if i in havuz]
    bulunamayan = [i for i in eksik if i not in havuz]
    # SÖZLEŞME ÖLÇÜMÜ (ledgers.CONTRACTS) — BLOKLAMAZ, BEYAN EDER: eksik alanlı bir plan gövdesi,
    # plan_join_yok'tan (hiç plan yok) daha az bilgi kaybıdır; ama ihlali sessizce içeri almak da
    # olmaz — sayısı ve örneği rapora çıkar, hükmü Rol-1 verir.
    from meridian import ledgers as _lg
    ihlalli = [(p.get("id"), _lg.validate_row(PLANS, p)) for p in bulunan]
    ihlalli = [(i, v) for i, v in ihlalli if v]
    return {"n_trades": len(trades), "n_plan": len(planlar), "n_eksik": len(eksik),
            "eksik": eksik, "bulunan": bulunan, "bulunamayan": bulunamayan,
            "havuz_n": len(havuz), "ihlalli": ihlalli}


def uygula(rapor: dict) -> int:
    """Kurtarılan plan gövdelerini defterin başına İDEMPOTENT ekler (kilitli oku-değiştir-yaz)."""
    eklenecek = sorted(rapor["bulunan"], key=lambda p: (str(p.get("date") or ""), str(p.get("id"))))
    with store.file_lock(PLANS):
        planlar = store.read_jsonl(PLANS)
        mevcut = {p.get("id") for p in planlar if p.get("id")}
        yeni = [p for p in eklenecek if p.get("id") not in mevcut]   # ikinci kemer: yarışta da idempotent
        if not yeni:
            print("yazılacak yeni satır yok (idempotent: eksikler zaten kapanmış)")
            return 0
        store.write_jsonl(PLANS, yeni + planlar)
    from meridian import obs
    obs.log("plan_geri_dolduruldu", n=len(yeni),
            detail=f"trade_plans'a {len(yeni)} işleme-dönüşmüş plan iade edildi "
                   f"(kaynaklı geri-doldurma; ops/plan_geri_doldur.py)")
    print(f"YAZILDI: {len(yeni)} plan iade edildi (defter {len(planlar)} → {len(planlar) + len(yeni)})")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--kaynak", action="append", default=[],
                    help="plan gövdesi kaynağı (jsonl/json/db/dizin/tar.gz); tekrarlanabilir, ilk kazanır")
    ap.add_argument("--uygula", action="store_true", help="yaz (varsayılan KURU KOŞU)")
    ap.add_argument("--zorla", action="store_true",
                    help="canlı worker bekçisini atla (bilerek; varsayılan reddeder)")
    args = ap.parse_args(argv)

    try:
        rapor = olc([Path(k) for k in args.kaynak])
    except (OSError, ValueError, LookupError) as e:
        print(f"KAYNAK OKUNAMADI: {type(e).__name__}: {e}")
        return 2

    print(f"işlem defteri: {rapor['n_trades']} satır · plan defteri: {rapor['n_plan']} satır")
    print(f"plan_join_yok (işlemi var, planı yok): {rapor['n_eksik']}")
    print(f"kaynak havuzu: {rapor['havuz_n']} plan · kurtarılabilir: {len(rapor['bulunan'])}"
          f" · kaynaklarda YOK: {len(rapor['bulunamayan'])}")
    if rapor["bulunamayan"]:
        ilk = ", ".join(rapor["bulunamayan"][:8])
        print(f"  bulunamayanlar (ilk 8): {ilk} — bu gövdeler UYDURULMAZ; kırpma-öncesi bir kaynak"
              f" (determinist şasinin yeniden koşumu ya da kırpma-öncesi yedek) gerekir")
    if rapor["ihlalli"]:
        oid, ov = rapor["ihlalli"][0]
        print(f"  SÖZLEŞME NOTU: kurtarılan {len(rapor['ihlalli'])} gövde ledgers.CONTRACTS "
              f"alanlarını tam taşımıyor (örn. {oid}: {'; '.join(ov[:3])}) — yine de eklenir "
              f"(plan_join_yok daha büyük kayıptır); hüküm Rol-1'de")
    if not rapor["n_eksik"]:
        print("eksik yok — yapılacak iş yok (idempotent son durum)")
        return 0
    if not args.uygula:
        print("KURU KOŞU: hiçbir bayt yazılmadı (--uygula ile yazar)")
        return 1 if rapor["bulunamayan"] else 0

    # canlı worker bekçisi (replay_seed deseni): defterine yazacağımız sürecin altından çekmeyelim
    if not health.stale(WORKER_TAZE_S) and not args.zorla:
        print(f"REDDEDİLDİ: nabız {WORKER_TAZE_S} sn'den taze — canlı worker koşuyor olabilir. "
              f"Önce worker'ı durdur; bilerek istiyorsan --zorla.")
        return 2
    kod = uygula(rapor)
    return kod if not rapor["bulunamayan"] else 1


if __name__ == "__main__":
    sys.exit(main())
