#!/usr/bin/env python3
"""sermaye_beyani_iade.py — SİLİNMİŞ SERMAYE BEYANININ KİTABA İADESİ (R1, 2026-08-04).

NEDEN VAR — TAM BAĞLAM (research/olcumler/portfoy_sifirlama_2026-08-04/KOKNEDEN.md).
2026-08-01T15:14:29Z'de operatör `python -m meridian.sermaye --uygula` koştu. O yazım TAM
BEYANLIYDI: kitap 100.000$ tabanına taşındı (cash · realized_pnl · day_start_equity ·
peak_equity) VE taşımanın kaydı `portfolio.sermaye_resetleri` içine gerekçesiyle yazıldı.
Hafta sonundan sonraki İLK noop-olmayan seansta `loop._save_broker` kitabı SABİT 13 ANAHTARLIK
bir beyaz listeyle yeniden serileştirdi ve listede olmayan `sermaye_resetleri` SESSİZCE yok oldu.
Beyan gidince `recompute` ofseti 0,0'a düştü ve üç kimlik birden kırıldı → 2026-08-04T01:16
MAKULLÜK alarmları.

KAYBOLAN TEK ŞEY BEYANDIR; SAYILAR DOĞRUDUR. Aynı işlemin diğer üç ayağı hâlâ diskte duruyor:
`equity_curve` zarfındaki `reset_isaretleri`, `state/monotonic_amnesty.json` peak affı ve
`state/events.jsonl` içindeki `paper_equity_reset` satırı. Bu betik kitaba, tam metniyle YEDEKTEN
okunan kaydı geri koyar ve kitabı BEYAN EDİLMİŞ tabana döndürür. Üç MAKULLÜK satırı bununla
dürüstçe yeşile döner — susturma DEĞİL: ofset gerçekten beyanlıdır ve `recompute` resetten sonra
kaybolan/iki kez sayılan bir işlemi HÂLÂ yakalar.

TERS YÖNLÜ ONARIMI DA GERİ ALIR. Kimlikleri yeşile döndürmenin ikinci bir yolu daha vardır ve
YANLIŞTIR: kitabı defterin eski tabanına geri çekmek (cash 94.457,91 / realized −5.542,09).
O yol sayıları uzlaştırır ama OPERATÖRÜN KARARINI geri alır — antrenman tohumunun zararı yeniden
canlı sermayeden düşülür ve boyutlandırma tabanı yine küçülür (`broker.equity()` =
start_equity + realized_pnl). Bu betik kitabı BEYAN EDİLEN tabana götürdüğü için böyle bir onarım
yapılmışsa o da geri alınmış olur. Ne bulduğunu VARSAYMAZ: ÖNCE tablosu diskte ne varsa onu basar.

SIRA ÖNEMLİ: ÖNCE D1 (loop._save_broker artık belgeyi ezmiyor, yamalıyor), SONRA bu iade.
D1'siz bir iade bir sonraki seansta yine silinirdi.

PARA KIMILDAMAZ. Bu betik bir emir göndermez, bir pozisyon açmaz/kapatmaz, brokera dokunmaz.
Yalnız `state/portfolio.json` (canlıda SQLite `portfolio.doc_json`) belgesinin ÜÇ alanına
(cash · realized_pnl · day_start_equity) ve beyan defterine yazar — yazımı da D1'in yasasıyla
yapar: KİLİT ALTINDA YAMA, tam-belge ezme DEĞİL. `peak_equity` DIŞARIDADIR (gerekçesi
`yeni_kitap`ta): monoton bir büyüklüktür ve geriye çekmek yazılı bir af ister.

KULLANIM:
    uv run python ops/sermaye_beyani_iade.py                    # KURU KOŞU (varsayılan)
    uv run python ops/sermaye_beyani_iade.py --uygula           # YAZ (worker DURMUŞ olmalı)
    uv run python ops/sermaye_beyani_iade.py --yedek <tar.gz|db>     # başka bir yedekten oku
    uv run python ops/sermaye_beyani_iade.py --kayit-dosyasi <json>  # kaydı dosyadan al (A1'de
        yedek tarball'ı yoktur; kuru koşu kaydı JSON olarak basar, operatör onu taşıyabilir)
    MERIDIAN_ROOT=/yol/kopya uv run python ops/sermaye_beyani_iade.py   # sandbox kopyada dene

ÇIKIŞ KODU: 0 = ok (ya da zaten beyanlı) · 1 = engel/doğrulama düştü · 2 = kaynak okunamadı /
canlı worker koşuyor.
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import tarfile
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from meridian import recompute, sermaye, store, watchdog  # noqa: E402

# YEDEKTEKİ KAYDIN KİMLİĞİ — DOĞRULAMA İÇİN, ÜRETİM İÇİN DEĞİL. Kayıt yedekten OKUNUR (metni
# uydurulmaz); bu iki sabit yalnız "okuduğum şey gerçekten o kayıt mı" sorusunu cevaplar. Başka
# bir kayıt gelirse betik durur: yanlış bir beyanı kitaba yazmak, beyansızlıktan kötüdür.
BEKLENEN_ID = "SR-20260801T151429+0000"
BEKLENEN_OFSET = 5542.09
VARSAYILAN_YEDEK = Path(__file__).resolve().parent.parent / "backups/a1/state-2026-08-02.tar.gz"
DB_UYE = "state/meridian.db"          # tarball içindeki CANLI DB (sprint kum havuzlarınınki DEĞİL)


# ---- KAYNAK: KAYIT YEDEKTEN OKUNUR --------------------------------------------------------------
def _doc_from_db(db_yolu: Path) -> dict:
    """Yedek DB'den `portfolio.doc_json` — SALT OKUNUR açılır (`mode=ro`), yedek dosyaya tek bayt
    yazılmaz (WAL/journal yaratma riski dâhil)."""
    c = sqlite3.connect(f"file:{db_yolu}?mode=ro", uri=True)
    try:
        row = c.execute("SELECT doc_json FROM portfolio WHERE id=1").fetchone()
    finally:
        c.close()
    if not row:
        raise LookupError(f"{db_yolu}: portfolio tablosunda belge yok")
    return json.loads(row[0])


def kayit_yedekten(yedek: Path) -> tuple[dict, str]:
    """Beyan kaydını yedekten çıkar. Yedek bir `.tar.gz` ya da doğrudan bir `.db` olabilir."""
    if yedek.suffix == ".db":
        doc = _doc_from_db(yedek)
        kaynak = str(yedek)
    else:
        with tarfile.open(yedek) as t:
            try:
                uye = t.getmember(DB_UYE)
            except KeyError as e:
                raise LookupError(f"{yedek}: `{DB_UYE}` üyesi yok") from e
            f = t.extractfile(uye)
            if f is None:
                raise LookupError(f"{yedek}: `{DB_UYE}` okunamadı")
            # Tek üye geçici bir dosyaya açılır: sqlite bir dosya tanıtıcısı ister, akış değil.
            with tempfile.TemporaryDirectory() as td:
                gecici = Path(td) / "yedek.db"
                gecici.write_bytes(f.read())
                doc = _doc_from_db(gecici)
        kaynak = f"{yedek}::{DB_UYE}"
    kayitlar = sermaye.resetler(doc)
    if not kayitlar:
        raise LookupError(f"{kaynak}: yedekteki kitapta da `{sermaye.RESET_KEY}` YOK — bu yedek "
                          f"beyanı taşımıyor, daha eski/başka bir yedek gerekir")
    return kayitlar[-1], kaynak


def kayit_dosyadan(yol: Path) -> tuple[dict, str]:
    yuk = json.loads(Path(yol).read_text())
    kayit = yuk[-1] if isinstance(yuk, list) else yuk
    if not isinstance(kayit, dict):
        raise LookupError(f"{yol}: JSON bir kayıt (sözlük) ya da kayıt listesi olmalı")
    return kayit, str(yol)


# ---- ÖLÇÜM ---------------------------------------------------------------------------------------
def _pnl_toplami() -> float:
    return round(sum(float(t.get("pnl_dollars") or 0.0)
                     for t in store.read_jsonl("trades.jsonl")), 2)


def _egri_sonu() -> float | None:
    pts = (store.read_json(sermaye.EQUITY, {}) or {}).get("points") or []
    son = pts[-1] if pts else None
    if isinstance(son, (list, tuple)) and len(son) > 1:
        try:
            return float(son[1])
        except (TypeError, ValueError):  # sessiz-yutma: eğrinin son noktası sayı değil — kimlik ÖLÇÜLEMEDİ demektir ve None tam olarak bunu söyler; çağıran satırı "ölçülemedi" diye basar, uydurma bir değerle YEŞİL göstermez
            return None
    return None


def kimlikler(pf: dict) -> list[dict]:
    """`recompute`in ÜÇ kimliği, VERİLEN kitap belgesi için. Kuru koşuda henüz diske yazılmamış
    bir belgeyi de ölçebilmek için kimlik burada kurulur — ama sabitler (`START_EQUITY`, para
    toleransı) `recompute`ten İTHAL edilir: ikinci bir tanım, 'aynı yasanın iki uygulaması' olurdu.
    Uygulamadan SONRA otorite yine `recompute.report()`tur (aşağıda o da basılır)."""
    ofs = sermaye.ofset(pf)
    pnl = _pnl_toplami()
    tail = _egri_sonu()
    cash = float(pf.get("cash") or 0.0)
    realized = float(pf.get("realized_pnl") or 0.0)
    poz = bool(pf.get("positions") or {})
    satir = [
        {"ad": "realized_pnl", "a": round(realized, 2), "b": round(pnl + ofs, 2),
         "aciklama": "kitap gerçekleşen K/Z  ↔  Σ defter + beyanlı ofset"},
        {"ad": "cash_identity", "a": round(cash, 2),
         "b": round(recompute._start_equity() + pnl + ofs, 2),
         "aciklama": "kitap nakdi  ↔  başlangıç + Σ defter + beyanlı ofset",
         "olculemedi": "açık pozisyon var — kimlik yalnız pozisyonsuzken tanımlı" if poz else None},
        {"ad": "equity_curve_tail",
         "a": None if tail is None else round(tail + ofs, 2), "b": round(cash, 2),
         "aciklama": "eğri sonu + beyanlı ofset  ↔  kitap nakdi",
         "olculemedi": "eğrinin son noktası okunamadı" if tail is None else None},
    ]
    for s in satir:
        s.setdefault("olculemedi", None)
        s["ok"] = (None if s["olculemedi"] or s["a"] is None
                   else abs(s["a"] - s["b"]) <= recompute.MONEY_TOL)
    return satir


def _kitap_ozeti(pf: dict) -> dict:
    o = sermaye.ofset(pf)
    return {"cash": pf.get("cash"), "realized_pnl": pf.get("realized_pnl"),
            "day_start_equity": pf.get("day_start_equity"), "peak_equity": pf.get("peak_equity"),
            "n_beyan": len(sermaye.resetler(pf)), "ofset": o,
            "beyan_id": [r.get("id") for r in sermaye.resetler(pf)]}


def _beyan_ekle(doc: dict, kayit: dict) -> None:
    """Kaydı beyan defterine EKLE — AYNI ID VARSA EKLEME. İdempotens buradan gelir: ikinci bir
    koşu ofseti iki katına çıkarıp üç kimliği TERS yönde kırardı. Tek uygulama, iki çağıran
    (projeksiyon ve gerçek yazım) — projeksiyonun yazımdan farklı bir şey göstermesi, raporun
    kendisini yalancı yapardı."""
    mevcut = sermaye.resetler(doc)
    if str(kayit.get("id")) in {str(r.get("id")) for r in mevcut}:
        return
    doc[sermaye.RESET_KEY] = mevcut + [kayit]


def yeni_kitap(pf: dict, kayit: dict) -> dict:
    """İADE EDİLEN HÂL — üç alan + beyan defteri. `peak_equity` BİLEREK DIŞARIDA: monoton bir
    büyüklüktür, resetten bu yana meşru olarak yükselmiş olabilir ve geriye çekmek yeni bir af
    (`watchdog.grant_amnesty`) isterdi. 2026-08-01 affı zaten yazılıdır; rapor onu gösterir."""
    hedef = float(recompute._start_equity())
    yeni = dict(pf)
    yeni.update({"cash": round(hedef, 2), "realized_pnl": 0.0,
                 "day_start_equity": round(hedef, 2)})
    _beyan_ekle(yeni, kayit)
    return yeni


def engeller(pf: dict, kayit: dict, kimlik_satirlari: list[dict], worker: bool) -> list[dict]:
    e = []
    if worker:
        e.append({"ad": "canli_worker", "neden":
                  "canlı Meridian süreci görülüyor. Worker koşarken kitap yazılmaz: aynı turda "
                  "`_save_broker` kendi sahiplendiği alanları geri yazar ve ÖNCE/SONRA raporu "
                  "yalan söyler. Önce `./ops/stop-worker.sh` (ya da --zorla)."})
    poz = pf.get("positions") or {}
    if poz:
        e.append({"ad": "dolu_pozisyon", "neden":
                  f"{len(poz)} açık pozisyon var ({', '.join(sorted(poz))}). Sermaye tabanını açık "
                  f"pozisyon varken taşımak, o pozisyonların risk_dollars tabanını GERİYE DÖNÜK "
                  f"değiştirir (sermaye.py ile aynı engel)."})
    if str(kayit.get("id")) in {str(r.get("id")) for r in sermaye.resetler(pf)}:
        e.append({"ad": "zaten_beyanli", "neden":
                  f"kitapta `{kayit.get('id')}` kaydı ZATEN var — iade yapılmış. İkinci kez yazmak "
                  f"ofseti iki katına çıkarır ve üç kimliği ters yönde kırardı."})
    kirik = [s["ad"] for s in kimlik_satirlari if s["ok"] is False]
    if kirik:
        e.append({"ad": "kimlik_tutmuyor", "neden":
                  f"iade SONRASI hâlde şu kimlik(ler) hâlâ tutmuyor: {', '.join(kirik)}. Beyanın "
                  f"iadesi bunları yeşile döndürmüyorsa kitapta BAŞKA bir sapma daha var; yazmadan "
                  f"önce o bulunmalı (bu betik alarmı susturmak için değil, beyanı iade etmek "
                  f"içindir)."})
    return e


# ---- YAZDIRMA ------------------------------------------------------------------------------------
def _p(x) -> str:
    if x is None:
        return "—"
    try:
        return f"{float(x):,.2f}$"
    except (TypeError, ValueError):  # sessiz-yutma: yalnız BİÇİMLEME yolu; ham değer olduğu gibi basılır ve hiçbir ölçüm kaybolmaz
        return str(x)


def _ozet_yaz(baslik: str, oz: dict, kim: list[dict]) -> None:
    print(f"  --- {baslik} ---")
    print(f"    cash {_p(oz['cash']):>14s} · realized {_p(oz['realized_pnl']):>13s} · "
          f"gün-başı {_p(oz['day_start_equity']):>13s} · tepe {_p(oz['peak_equity']):>13s}")
    print(f"    beyan: {oz['n_beyan']} kayıt {oz['beyan_id']} · ofset {_p(oz['ofset'])}")
    for s in kim:
        isaret = "ÖLÇÜLEMEDİ" if s["ok"] is None else ("TUTUYOR" if s["ok"] else "KIRIK")
        print(f"    {s['ad']:18s} {isaret:11s} {_p(s['a']):>14s} ↔ {_p(s['b']):>14s}   "
              f"{s['olculemedi'] or s['aciklama']}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="ops/sermaye_beyani_iade.py",
        description="silinmiş sermaye beyanını yedekten okuyup kitaba iade eder (para kımıldamaz)")
    ap.add_argument("--uygula", action="store_true", help="YAZ (varsayılan: kuru koşu)")
    ap.add_argument("--yedek", default=str(VARSAYILAN_YEDEK), help="tar.gz ya da .db yolu")
    ap.add_argument("--kayit-dosyasi", default=None, help="beyan kaydını bu JSON'dan al")
    ap.add_argument("--zorla", action="store_true", help="engellere rağmen yaz (riski sen alırsın)")
    ap.add_argument("--json", action="store_true", help="raporu JSON olarak bas")
    a = ap.parse_args(argv)

    try:
        kayit, kaynak = (kayit_dosyadan(Path(a.kayit_dosyasi)) if a.kayit_dosyasi
                         else kayit_yedekten(Path(a.yedek)))
    except (OSError, LookupError, ValueError, json.JSONDecodeError, sqlite3.Error,
            tarfile.TarError) as e:
        print(f"[iade] KAYNAK OKUNAMADI: {type(e).__name__}: {e}", file=sys.stderr)
        return 2

    uyusmaz = []
    if str(kayit.get("id")) != BEKLENEN_ID:
        uyusmaz.append(f"id {kayit.get('id')} ≠ {BEKLENEN_ID}")
    if abs(float(kayit.get("ofset") or 0.0) - BEKLENEN_OFSET) > 0.01:
        uyusmaz.append(f"ofset {kayit.get('ofset')} ≠ {BEKLENEN_OFSET}")
    if uyusmaz and not a.zorla:
        print(f"[iade] REDDEDİLDİ — yedekten okunan kayıt beklenenle uyuşmuyor: "
              f"{'; '.join(uyusmaz)}. Yanlış bir beyanı kitaba yazmak, beyansızlıktan kötüdür "
              f"(--zorla ile geçilebilir).", file=sys.stderr)
        return 2

    pf = store.read_json(sermaye.PORTFOLIO, {}) or {}
    once_oz, once_kim = _kitap_ozeti(pf), kimlikler(pf)
    proj = yeni_kitap(pf, kayit)
    sonra_oz, sonra_kim = _kitap_ozeti(proj), kimlikler(proj)
    worker = sermaye._worker_running() and not a.zorla
    eng = engeller(pf, kayit, sonra_kim, worker)

    rapor = {"applied": bool(a.uygula), "yazildi": False, "kaynak": kaynak, "kayit": kayit,
             "kayit_uyusmazlik": uyusmaz, "state": str(os.environ.get("MERIDIAN_ROOT") or "repo"),
             "once": {"kitap": once_oz, "kimlikler": once_kim},
             "sonra": {"kitap": sonra_oz, "kimlikler": sonra_kim}, "engeller": eng,
             "egri_isaretleri": [i.get("id") for i in sermaye._egri_isaretleri()],
             "peak_affi": store.read_json(watchdog.AMNESTY_FILE, []) or []}

    if a.uygula and not eng:
        # D1'İN YASASI BURADA DA GEÇERLİ: tam-belge yazımı YOK. Diskteki belge kilit altında
        # okunur, üstüne yalnız bu betiğin SAHİPLENDİĞİ dört şey yazılır — yabancı anahtarlar
        # (armed, entry_law, pending_exits, …) dokunulmadan kalır.
        def _yama(doc):
            if not isinstance(doc, dict):
                return False
            hedef = float(recompute._start_equity())
            doc.update({"cash": round(hedef, 2), "realized_pnl": 0.0,
                        "day_start_equity": round(hedef, 2)})
            _beyan_ekle(doc, kayit)
            return True

        with store.file_lock(sermaye.PORTFOLIO):
            store.update_json(sermaye.PORTFOLIO, _yama, {})
        rapor["yazildi"] = True
        pf2 = store.read_json(sermaye.PORTFOLIO, {}) or {}
        rapor["sonra"] = {"kitap": _kitap_ozeti(pf2), "kimlikler": kimlikler(pf2)}
        # OTORİTE: yazımdan sonra kimlikleri `recompute`in KENDİSİ ölçer.
        rapor["recompute"] = [{"check": r["check"], "ok": r["ok"], "detail": r.get("detail")}
                              for r in recompute.report()["rows"]
                              if r["check"] in ("realized_pnl", "cash_identity",
                                                "equity_curve_tail")]

    if a.json:
        print(json.dumps(rapor, ensure_ascii=False, indent=1, default=str))
        return _cikis(eng, bool(a.uygula))

    mod = ("UYGULANDI" if rapor["yazildi"] else
           ("UYGULAMA REDDEDİLDİ" if a.uygula else "KURU KOŞU (hiçbir bayt yazılmadı)"))
    print(f"[iade] {mod}   state={rapor['state']}")
    print(f"  kaynak      : {kaynak}")
    print(f"  kayıt       : {kayit.get('id')} · ofset {_p(kayit.get('ofset'))} · "
          f"{kayit.get('tarih')}")
    print(f"  gerekçe     : {kayit.get('gerekce')}")
    _ozet_yaz("ÖNCE (diskte ne var)", once_oz, once_kim)
    _ozet_yaz("SONRA (yazıldı)" if rapor["yazildi"] else "SONRA (yazılacak)",
              rapor["sonra"]["kitap"], rapor["sonra"]["kimlikler"])
    print(f"  --- DOKUNULMAYAN ---")
    print(f"    peak_equity ({_p(once_oz['peak_equity'])}) · trades.jsonl · equity_curve.points · "
          f"armed · entry_law · last_id · broker_rejected")
    print(f"    eğri reset işaretleri: {rapor['egri_isaretleri'] or '— (YOK: eğri zarfı da silinmiş)'}")
    print(f"    peak_equity affı    : "
          f"{[f'''{x.get('field')} {x.get('was')}→{x.get('now')}''' for x in rapor['peak_affi']] or '— (yok)'}")
    for e in eng:
        print(f"  ENGEL [{e['ad']}]: {e['neden']}")
    for r in rapor.get("recompute", []):
        print(f"  recompute[{r['check']:18s}] {'TUTUYOR' if r['ok'] else 'KIRIK'} — {r['detail']}")
    if not a.uygula and not eng:
        print("  → uygulamak için: uv run python ops/sermaye_beyani_iade.py --uygula "
              "(worker DURDURULMUŞ olmalı)")
    return _cikis(eng, bool(a.uygula))


def _cikis(eng: list[dict], uygula: bool) -> int:
    """`zaten_beyanli` TEK BAŞINAYSA çıkış kodu 0'dır: iade zaten yapılmış, yapılacak bir iş yok
    ve bu bir ARIZA değildir (`sermaye.uygula`nın idempotens sözleşmesiyle aynı). Yanına başka bir
    engel eklendiğinde kod 1'e döner — o zaman gerçekten bakılacak bir şey vardır."""
    if not (eng and uygula):
        return 0
    return 0 if {e["ad"] for e in eng} == {"zaten_beyanli"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
