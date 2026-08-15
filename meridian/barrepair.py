"""barrepair.py — diskteki bar defterlerinden HAYALET SEANS satırlarını temizleyen onarım/envanter aracı.

NE YAPAR: `adapters.data.sanitize_bars` kapısı takvim doğrulaması kazandığından beri hiçbir hayalet
satır belleğe giremez; ama diskte ZATEN duran satırlar ancak o sembol yeniden yazıldığında temizlenir
ve emekli/bayat semboller hayaleti sonsuza dek taşırdı — `state/bars` üzerinden üretilmiş artefaktlar
(component_ic, cf defterleri, eşik eğrileri) hangi tabandan çıktığı belirsiz kalırdı. Bu araç o
migrasyon adımıdır: defterleri tarar, düşecek satırları sınıflandırır (birebir_kopya / yakin_kopya /
duz_bar_sifir_hacim / duzeltilmemis_fiyat) ve istenirse kapıdan geçirip atomik yeniden yazar.
Ölçülmüş taban (sayım, tahmin değil): kapalı 2025-05-26 (Memorial Day) ve 2018-11-22 (Thanksgiving)
günlerinde toplam 442 hayalet satır; geçerli seanslarda 3 izole düzeltilmemiş satır.

KİLİT GİRİŞLER: scan()/repair() (hayalet temizliği), integrity_scan()/integrity_apply()
(`--integrity-tara`: satır SİLMEYEN kırılma envanteri), CLI `python -m meridian.barrepair`
(--uygula / --sembol / --json / --zorla / --integrity-tara).

DEĞİŞMEZLER: (1) KURU KOŞU VARSAYILANDIR — `--uygula` verilmeden hiçbir bayt yazılmaz; veri silen
bir aracın varsayılanının yazmak olması bu depoda yaşanmış hata sınıfıdır. (2) YAZIM SANCTIONED
YOLDAN: satır silmek dosyayı küçültür ve determinizm dedektörü küçülmeyi haklı olarak "sessiz bar
mutasyonu" sayar — `data._bump_wf_rev()` bu yüzden İLK yazımdan ÖNCE çağrılır (erken bump zararsız,
geç bump ölümcül: süreç yazım ortasında ölürse defter küçülmüş, revizyon sabit kalır). (3) Canlı
worker görülürse `--uygula` REDDEDİLİR (`--zorla` ezer): store kilidi süreç-içidir, yazım atomik
olsa da aynı defteri iki sürecin aynı anda yeniden yazması önlenir. (4) İkinci kusur sınıfı olan
dönemsel ölçek/kimlik kırılmaları SİLİNMEZ — kırılma satırı yeni ölçeğin ilk barıdır; önceki dönem
`state/bars_integrity.json`da "ölçüm için güvensiz" damgalanır ve ölçüm yolları (component_ic,
cf_backfill) o dönemi defterden öğrenip dışlar; bu yazım da wf-revizyonu bumplar.

OKUR/YAZAR: `state/bars/*.csv` defterlerini okur; --uygula ile onları atomik (`data._write_bars`)
yeniden yazar; --integrity-tara --uygula ile `state/bars_integrity.json` yazar (yalnız TAM evren —
kısmi tarama, taranmayan sembollerin damgasını silerdi ve reddedilir).
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys

import pandas as pd

from . import config
from .adapters import data


def _files(symbols: list[str] | None):
    """Taranacak bar defterlerinin yolları: `symbols` verilirse YALNIZ diskte VAR OLANLARI, yoksa
    `state/bars/*.csv` defterlerinin tamamı (sıralı)."""
    if symbols:
        return [data._cache_path(s) for s in symbols if data._cache_path(s).exists()]
    return sorted(config.BARS.glob("*.csv"))


def scan(symbols: list[str] | None = None) -> dict:
    """DİSKTEKİ her defteri OKU (yazma yok) ve kapının düşüreceği satırları sınıflandır.

    SINIF ETİKETLERİ TAHMİN DEĞİL ÖLÇÜMDÜR: her hayalet satır, kendinden önceki gerçek seansla
    KIYASLANARAK etiketlenir — `birebir_kopya` (bütün alanlar aynı), `yakin_kopya` (kapanış %0,5
    içinde), `duz_bar_sifir_hacim` (OHLC eşit ve hacim 0), `duzeltilmemis_fiyat` (|hareket| > %35).
    Etiket rapora girer, çünkü "kaç satır düştü" sorusundan çok "NE düştü" sorusu operatörün
    türetilmiş artefaktlar hakkında karar vermesini sağlar."""
    out: dict = {"files": 0, "rows": 0, "ghost_rows": 0, "quarantine_rows": 0,
                 "dates": {}, "tickers": {}, "unreadable": [], "refused": {},
                 "calendar": data.CALENDAR, "calendar_ok": bool(data._sessions())}
    for cp in _files(symbols):
        t = cp.stem.upper()
        try:
            raw = pd.read_csv(cp, parse_dates=["date"])
        except Exception as e:
            out["unreadable"].append(f"{t}: {type(e).__name__}: {e}")
            continue
        out["files"] += 1
        out["rows"] += len(raw)
        df = raw.sort_values("date").reset_index(drop=True)
        # KAPININ REDDETTİĞİ DEFTER RAPORA AYRI KALEM GİRER: "0 hayalet satır" cümlesi, kapı o
        # defteri hiç adjudike etmediyse YANILTICIDIR. Ölçüm SAF fonksiyonla yapılır — kuru koşunun
        # "hiçbir bayt yazılmadı" vaadi, ölçümün olay defterine yazmamasına bağlıdır.
        red = data.calendar_mismatch(df)
        if red:
            out["refused"][t] = red
        gh = data._ghost_mask(df)
        # SIRA KAPININ SIRASIDIR: önce takvim, SONRA karantina. Ters sırada hayalet satırın kendisi
        # komşu olur ve gerçek bir barı "sıçrama" gibi gösterirdi (BKNG'nin 05-23 ve 05-27 barları
        # tam olarak böyle suçlanırdı) — yani rapor, düzeltmenin yaratacağı hâli değil, kirli hâlin
        # gölgesini ölçerdi.
        clean = df.loc[~gh].reset_index(drop=True)
        q = data._unadjusted_mask(clean)
        n_g, n_q = int(gh.sum()), int(q.sum())
        if not (n_g or n_q):
            continue
        out["ghost_rows"] += n_g
        out["quarantine_rows"] += n_q
        rows = []
        for i in df.index[gh]:
            rows.append((str(df.at[i, "date"])[:10], _classify(df, i), "ghost_session"))
        for i in clean.index[q]:
            rows.append((str(clean.at[i, "date"])[:10], "duzeltilmemis_fiyat", "unadjusted_row"))
        out["tickers"][t] = [{"date": d, "class": k, "gate": g} for d, k, g in sorted(rows)]
        for d, k, g in rows:
            row = out["dates"].setdefault(d, {"rows": 0, "gate": g, "classes": {}, "tickers": []})
            row["rows"] += 1
            row["classes"][k] = int(row["classes"].get(k) or 0) + 1
            if len(row["tickers"]) < 250:
                row["tickers"].append(t)
    return out


def _classify(df: pd.DataFrame, i: int) -> str:
    """Hayalet satır ÖNCEKİ gerçek satıra göre ne? (etiketler `scan` docstring'inde tanımlı)"""
    if i == 0:
        return "ilk_satir"
    cur, prev = df.iloc[i], df.iloc[i - 1]
    try:
        if all(abs(float(cur[c]) - float(prev[c])) < 1e-9 for c in ("open", "high", "low", "close", "volume")):
            return "birebir_kopya"
        pc = float(prev["close"])
        r = float(cur["close"]) / pc if pc else None
        if r is not None and (r > 1.35 or r < 0.74):
            return "duzeltilmemis_fiyat"
        if (abs(float(cur["open"]) - float(cur["close"])) < 1e-9
                and abs(float(cur["high"]) - float(cur["low"])) < 1e-9 and float(cur["volume"]) == 0):
            return "duz_bar_sifir_hacim"
        if r is not None and abs(r - 1.0) < 0.005:
            return "yakin_kopya"
    except (TypeError, ValueError, ZeroDivisionError):  # sessiz-yutma: tek satırın biçimi bozuk — etiket "diger" olur, satır YİNE düşer (etiket kararı değiştirmez)
        pass
    return "diger"


def repair(symbols: list[str] | None = None, apply: bool = False) -> dict:
    """Kuru koşu (varsayılan) ya da UYGULAMA. Uygulama: her etkilenen defter kapıdan geçirilir ve
    ATOMİK olarak yeniden yazılır; wf-revizyonu İLK yazımdan ÖNCE bir kez bumplanır."""
    rapor = scan(symbols)
    rapor["applied"] = bool(apply)
    rapor["written"] = []
    if not apply or not (rapor["ghost_rows"] or rapor["quarantine_rows"]):
        return rapor
    data._bump_wf_rev()          # ÖNCE (yukarıdaki 2. kural: geç bump = sessiz mutasyon riski)
    for t in sorted(rapor["tickers"]):
        cp = data._cache_path(t)
        try:
            raw = pd.read_csv(cp, parse_dates=["date"])
            clean, rep = data.sanitize_bars(raw, t)
            if clean is None or clean.empty or len(clean) >= len(raw):
                continue                       # kapı bir şey düşürmediyse dosyaya DOKUNMA
            data._write_bars(clean, cp)
            rapor["written"].append({"ticker": t, "before": int(len(raw)), "after": int(len(clean)),
                                     "report": {k: int(v) for k, v in rep.items()}})
        except Exception as e:
            rapor["unreadable"].append(f"{t}: YAZIM BAŞARISIZ {type(e).__name__}: {e}")
    try:
        from . import obs
        obs.warn("bar_ghost_repair_applied", files=len(rapor["written"]),
                 ghost_rows=rapor["ghost_rows"], quarantine_rows=rapor["quarantine_rows"],
                 dates=",".join(sorted(rapor["dates"])),
                 detail="diskteki hayalet seans satırları silindi; wf revizyonu bumplandı "
                        "(determinizm kontrolü için SANCTIONED yol) — türetilmiş artefaktlar "
                        "(component_ic, cf defterleri, eşik eğrileri) yeniden üretilmeli")
    except Exception:  # sessiz-yutma: kayıt kanalı düştü; onarımın kendisi diske yazıldı ve rapor döndü
        pass
    return rapor


def integrity_scan(symbols: list[str] | None = None) -> dict:
    """DİSKTEKİ her defteri OKU ve ÇÖZÜLMEMİŞ ölçek/kimlik kırılmalarının envanterini üret (SAF).

    NE ÜRETİR: `state/bars_integrity.json`in gövdesi — sembol → güvenli_baslangic + kirilma_listesi
    + tespit_kuralı. Satır SİLMEZ: bu sınıfın çözümü silmek DEĞİL damgalamaktır (gerekçesi
    `adapters.data`in bars_integrity bloğunda; kalıcı dikişin satırı yeni ölçeğin İLK barıdır).

    RAPOR İKİ YÖNLÜ OKUNUR — envanterin yanında `yanlis_pozitif_adaylari` listesi de basılır:
    kuralın "gerçek piyasa olayı" deyip DAMGALAMADIĞI büyük kalıcı adımlar. Yalnız damgalananları
    basmak, kuralın kaçırdıklarını görünmez yapardı; iki liste birlikte elle denetlenebilir."""
    out: dict = {"rev": 1, "kural": {
        "BREAK_UP": data.BREAK_UP, "BREAK_DN": data.BREAK_DN,
        "BREAK_OGAP_TOL": data.BREAK_OGAP_TOL, "BREAK_HL_NORMAL": data.BREAK_HL_NORMAL,
        "CORRUPT_HL_MAX": data.CORRUPT_HL_MAX, "PHANTOM_DOLLAR_VOL": data.PHANTOM_DOLLAR_VOL,
        "PHANTOM_WINDOW": data.PHANTOM_WINDOW, "UNADJ_REVERT_TOL": data.UNADJ_REVERT_TOL,
        "beyan": "K1 ölçek dikişi · K2 bozuk kesit · K3 hayalet geçmiş (bkz. data.integrity_breaks)"},
        "semboller": {}, "yanlis_pozitif_adaylari": [], "taranan": 0, "okunamayan": []}
    for cp in _files(symbols):
        t = cp.stem.upper()
        try:
            raw = pd.read_csv(cp, parse_dates=["date"])
        except Exception as e:
            out["okunamayan"].append(f"{t}: {type(e).__name__}: {e}")
            continue
        out["taranan"] += 1
        df = raw.sort_values("date").reset_index(drop=True)
        # KAPININ SIRASI: envanter, ONARIM SONRASI dünyayı ölçmeli. Hayalet satır ve karantina satırı
        # zaten düşecek; onları kırılma sanmak, düzeltilecek bir arızayı kalıcı damga yapardı.
        gh = data._ghost_mask(df)
        if gh.any():
            df = df.loc[~gh].reset_index(drop=True)
        q = data._unadjusted_mask(df)
        if q.any():
            df = df.loc[~q].reset_index(drop=True)
        ss, brk = data.integrity_safe_start(df)
        if brk:
            out["semboller"][t] = {
                "guvenli_baslangic": ss,
                "ilk_bar": str(df["date"].iloc[0])[:10] if len(df) else None,
                "dislanan_bar": int((df["date"].astype(str).str.slice(0, 10) < ss).sum()) if ss else int(len(df)),
                "kirilma_listesi": brk,
                "tespit_kurali": ",".join(sorted({b["kural"] for b in brk}))}
        out["yanlis_pozitif_adaylari"].extend(_fp_candidates(t, df))
    out["sembol_sayisi"] = len(out["semboller"])
    out["kirilma_sayisi"] = sum(len(v["kirilma_listesi"]) for v in out["semboller"].values())
    out["dislanan_bar_toplam"] = sum(int(v["dislanan_bar"] or 0) for v in out["semboller"].values())
    return out


def _fp_candidates(ticker: str, df: pd.DataFrame) -> list[dict]:
    """Kuralın DAMGALAMADIĞI büyük kalıcı adımlar — elle denetim listesi (hüküm YOK, yalnız görünürlük)."""
    if df is None or len(df) < 5:
        return []
    f = data._integrity_feats(df)
    dates = df["date"].astype(str).str.slice(0, 10)
    damgali = {b["tarih"] for b in data.integrity_breaks(df)}
    out = []
    for i in range(1, len(df)):
        r = f["r"].iloc[i]
        if not (r == r) or not (r >= data.BREAK_UP or r <= data.BREAK_DN):
            continue
        drr = f["drr"].iloc[i]
        if (drr == drr and drr < data.UNADJ_REVERT_TOL) or dates.iloc[i] in damgali:
            continue
        og, hl = f["ogap"].iloc[i], f["hl"].iloc[i]
        out.append({"ticker": ticker, "tarih": dates.iloc[i], "oran": round(float(r), 4),
                    "acilis_orani": round(float(og), 3) if og == og else None,
                    "high_low": round(float(hl), 3) if hl == hl else None,
                    "hukum": "gerçek piyasa olayı sayıldı — damgalanmadı"})
    # TEKİL bozuk bar (kümeye girmediği için K2 damgası ALMADI) da denetime düşer: kural onu
    # kasten affetti, ve affedilen bir bulgunun görünmez kalması bu depoda üretilip tüketilmeyen
    # kanıttır. Küme zaten damgalandıysa listeye ikinci kez girmez.
    damga_tarih = {b["tarih"] for b in data.integrity_breaks(df) if b["kural"] == "K2"}
    if not damga_tarih:
        for tarih in data.integrity_corrupt_bars(df):
            i = int(dates[dates == tarih].index[0])
            out.append({"ticker": ticker, "tarih": tarih, "oran": round(float(f["r"].iloc[i]), 4),
                        "acilis_orani": None, "high_low": round(float(f["hl"].iloc[i]), 3),
                        "hukum": "TEKİL bozuk bar (high/low>3) — kümelenmediği için damgalanmadı"})
    return out


def integrity_apply(rapor: dict) -> dict:
    """Envanteri `state/bars_integrity.json` olarak YAZ — SANCTIONED yoldan.

    wf-revizyonu ÖNCE bumplanır: defter ölçüm evrenini daraltır, yani önbelleklenmiş walk-forward'lar
    artık BAŞKA bir bar kümesine aittir. Bump olmadan yazmak, `barrepair --uygula`nın satır silerken
    yaptığı hatanın aynısı olurdu — sonuç değişti, revizyon sabit."""
    from . import store
    data._bump_wf_rev()
    kayit = dict(rapor)
    kayit["uretildi"] = _dt.datetime.now().isoformat(timespec="seconds")
    kayit.pop("okunamayan", None)
    store.write_json(data.INTEGRITY_FILE, kayit)
    try:
        from . import obs
        # BEYAN KODLA EŞİTLENDİ: bu satır `dataset.load_cached`i
        # de "güvensiz dönemi dışlayanlar" arasında sayıyordu; `data.measurement_bars` docstring'i
        # (GERÇEK KAYNAK) bunu ölçülmüş gerekçeyle REDDEDİYOR — `dataset` yolu BİLEREK bağlanmadı,
        # `load_cached` yalnız `sanitize_bars` + `_window` çağırır. Yani onarımın kendi olayı, kirli
        # kalan tabloları temiz ilan ediyordu; üstelik türetilmiş artefaktların yeniden üretilip
        # üretilmeyeceğine karar veren satırda (UYDURMA YASAĞI'nın tam hedefi). Hangi yolların HÂLÂ
        # güvensiz dönemi GÖRDÜĞÜ artık aynı cümlede yazılıdır.
        obs.warn("bars_integrity_written", symbols=kayit["sembol_sayisi"],
                 breaks=kayit["kirilma_sayisi"], rows_excluded=kayit["dislanan_bar_toplam"],
                 detail="güvensiz dönemi DIŞLAYAN yollar: component_ic + cf_backfill (ikisi de "
                        "data.measurement_bars üzerinden). HÂLÂ KİRLİ DÖNEMİ GÖREN yollar: "
                        "dataset.load / dataset.load_cached — yani walk-forward, prescreen, reflect "
                        "ve canlı tarama (gerekçe: data.measurement_bars docstring'i). Türetilmiş "
                        "artefaktlar YENİDEN ÜRETİLMELİ")
    except Exception:  # sessiz-yutma: kayıt kanalı düştü; defter diske yazıldı ve rapor döndü
        pass
    return kayit


def _print_integrity(rapor: dict) -> None:
    """Bütünlük taraması raporunu insan-okur metne döker: damgalanan sembol/kırılma sayıları, ölçümden
    düşen bar sayısına göre ilk 20 sembol, damgalanmayan büyük kalıcı adım adayları (elle denetim) ve
    okunamayan defterler. Yalnız basar — dosya yazmaz."""
    print(f"[barrepair] BÜTÜNLÜK TARAMASI — {rapor['taranan']} defter")
    print(f"  damgalanan sembol: {rapor['sembol_sayisi']}, kırılma: {rapor['kirilma_sayisi']}, "
          f"ölçümden düşen bar: {rapor['dislanan_bar_toplam']}")
    sirali = sorted(rapor["semboller"].items(), key=lambda kv: -(kv[1]["dislanan_bar"] or 0))
    for t, v in sirali[:20]:
        ilk = v["kirilma_listesi"][0]
        print(f"   {t:6s} güvenli≥{v['guvenli_baslangic']}  (-{v['dislanan_bar']} bar) "
              f"{v['tespit_kurali']:6s} n={len(v['kirilma_listesi'])} "
              f"ilk={ilk['tarih']}/{ilk['sinif']}"
              + (f"/×{ilk['oran']}" if ilk["oran"] else ""))
    if len(sirali) > 20:
        print(f"   … +{len(sirali) - 20} sembol daha (tam liste: --json)")
    fp = rapor.get("yanlis_pozitif_adaylari") or []
    print(f"  DAMGALANMAYAN büyük kalıcı adım (elle denetim): {len(fp)}")
    for x in fp[:12]:
        print(f"   {x['ticker']:6s} {x['tarih']} ×{x['oran']} açılış_oranı={x['acilis_orani']} "
              f"high/low={x['high_low']}")
    if rapor.get("okunamayan"):
        print(f"  OKUNAMAYAN: {rapor['okunamayan'][:5]}")


def _worker_running() -> bool:
    """Canlı Meridian süreci var mı? (conftest'in aynı ölçümü — tek desen, iki tüketici)"""
    import subprocess
    try:
        r = subprocess.run(["pgrep", "-f", "uvicorn meridian.api"], capture_output=True,
                           text=True, timeout=5)
        return bool(r.stdout.strip())
    except (OSError, subprocess.SubprocessError):  # sessiz-yutma: pgrep yoksa ölçüm yapılamadı — aşağıda muhafazakâr taraf ("koşuyor say")
        return True


def _print(rapor: dict) -> None:
    """Onarım raporunu insan-okur metne döker: kip (uygulandı / kuru koşu), takvim durumu, taranan
    defter/satır, hayalet ve karantina satır sayıları, tarih kırılımı, yazılan defterler (türetilmiş
    artefakt uyarısıyla), kapının reddettiği ve okunamayan defterler. Yalnız basar — dosya yazmaz."""
    mod = "UYGULANDI" if rapor.get("applied") else "KURU KOŞU (hiçbir bayt yazılmadı)"
    print(f"[barrepair] {mod} — takvim {rapor['calendar']} "
          f"({'okundu' if rapor['calendar_ok'] else 'OKUNAMADI → kapı FAIL-OPEN, satır düşmez'})")
    print(f"  taranan defter: {rapor['files']}, toplam satır: {rapor['rows']}")
    print(f"  hayalet seans satırı: {rapor['ghost_rows']}, karantina satırı: {rapor['quarantine_rows']}")
    for d, row in sorted(rapor["dates"].items()):
        siniflar = ", ".join(f"{k}={v}" for k, v in sorted(row["classes"].items()))
        print(f"   {d} [{row['gate']}] {row['rows']} dosya — {siniflar}")
        print(f"      örnek: {', '.join(sorted(row['tickers'])[:12])}"
              + (" …" if len(row["tickers"]) > 12 else ""))
    if rapor.get("written"):
        print(f"  YAZILAN defter: {len(rapor['written'])} "
              f"(ilk: {', '.join(w['ticker'] for w in rapor['written'][:8])})")
        print("  → wf revizyonu bumplandı; TÜRETİLMİŞ ARTEFAKTLAR YENİDEN ÜRETİLMELİ "
              "(component_ic.json, cf defterleri, eşik eğrileri)")
    if rapor.get("refused"):
        ornek = ", ".join("{} %{}".format(t, v.get("share_pct"))
                          for t, v in list(rapor["refused"].items())[:6])
        print(f"  KAPI REDDETTİ (kitlesel takvim uyuşmazlığı, satır DÜŞÜRÜLMEDİ): "
              f"{len(rapor['refused'])} defter — {ornek}")
    if rapor.get("unreadable"):
        print(f"  OKUNAMAYAN/HATALI: {rapor['unreadable'][:5]}")
    if not rapor.get("applied") and (rapor["ghost_rows"] or rapor["quarantine_rows"]):
        print("  → uygulamak için: python -m meridian.barrepair --uygula  (worker DURDURULMUŞ olmalı)")


def main(argv: list[str] | None = None) -> int:
    """CLI girişi. Varsayılan KURU KOŞUdur; `--uygula` yazar ve canlı Meridian süreci görülüyorsa
    (`--zorla` yoksa) REDDEDER — aynı defteri iki süreç yeniden yazamaz. `--integrity-tara` satır
    silmeyen kırılma envanterini üretir; onun `--uygula`sı TAM evren ister (kısmi tarama, taranmayan
    sembollerin damgasını silerdi). Çıkış kodu: 0 başarı, 2 reddedildi."""
    ap = argparse.ArgumentParser(prog="python -m meridian.barrepair",
                                 description="state/bars defterlerinden hayalet seans satırlarını temizler")
    ap.add_argument("--uygula", action="store_true", help="YAZ (varsayılan: kuru koşu)")
    ap.add_argument("--sembol", default="", help="virgülle ayrılmış sembol listesi (varsayılan: hepsi)")
    ap.add_argument("--json", action="store_true", help="raporu JSON olarak bas")
    ap.add_argument("--zorla", action="store_true", help="canlı süreç görülse de yaz (riski sen alırsın)")
    ap.add_argument("--integrity-tara", action="store_true", dest="integrity",
                    help="ÇÖZÜLMEMİŞ ölçek/kimlik kırılması envanteri (satır SİLMEZ; --uygula ile "
                         "state/bars_integrity.json yazılır)")
    a = ap.parse_args(argv)
    syms = [s.strip().upper() for s in a.sembol.split(",") if s.strip()] or None
    if a.uygula and not a.zorla and _worker_running():
        print("[barrepair] REDDEDİLDİ: canlı Meridian süreci görülüyor. Aynı defteri iki süreç "
              "yeniden yazamaz — kilit yarışı önler ama iki farklı NİYETLE yeniden yazmayı "
              "önlemez. Önce `./ops/stop-worker.sh`, "
              "sonra tekrar dene (ya da --zorla).", file=sys.stderr)
        return 2
    if a.integrity:
        rapor = integrity_scan(syms)
        # KISMİ TARAMA DEFTERİ EZEMEZ: `--sembol` ile üretilen envanter, taranmayan sembollerin
        # damgasını SİLMİŞ bir defter yazardı (defterin tüketicisi de o eksikliği göremezdi).
        if a.uygula and syms:
            print("[barrepair] REDDEDİLDİ: --integrity-tara --uygula TAM evren ister; --sembol ile "
                  "yazılan defter taranmayan sembollerin damgasını siler.", file=sys.stderr)
            return 2
        if a.uygula:
            rapor = integrity_apply(rapor)
        if a.json:
            print(json.dumps(rapor, ensure_ascii=False, indent=1, default=str))
        else:
            _print_integrity(rapor)
            if not a.uygula:
                print("  → yazmak için: python -m meridian.barrepair --integrity-tara --uygula")
        return 0
    rapor = repair(syms, apply=a.uygula)
    if a.json:
        print(json.dumps(rapor, ensure_ascii=False, indent=1, default=str))
    else:
        _print(rapor)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
