"""hermes_composite.py — BİLEŞİK ÖNERİ YOLU (Hermes paketi H3 + H4, 2026-07-30).

SORUN. Tek-değişken yasası (`goal.one_variable_only`) kapının temel disiplinidir ve KALKMAYACAK:
iki düğmeyi birlikte oynatıp iyileşme görmek, hangisinin işe yaradığını ÖLÇMEZ. Ama yasanın bir yan
etkisi vardı: hermes bir bileşik fikir ürettiğinde (ör. "stop_mode=1 İLE stop_buffer_atr=0.4 birlikte
anlamlı") o fikir guard'da REDDEDİLİP ÇÖPE gidiyordu. Fikrin kendisi bilgiydi; kaybı ölçülmemiş bir
kayıptı.

ÇÖZÜM (H3). Bileşik öneri guard'ı ATLAMAZ ve canlıya GİTMEZ — bir KUYRUĞA yazılır
(`state/composite_queue.jsonl`, ledgers sözleşmeli). Kuyruk, `prescreen --composite` yolunun (2026-07-30
sadeleştirme turunda inen resmî bileşik ölçüm yolu) girdisidir. Yani bileşik fikir tek-değişken
yasasını gevşetmez; ÖLÇÜLMEK üzere sıraya girer ve ship yolu yine kapı + operatördür.

ÇÖZÜM (H4). Kuyruk kendi kendine boşalmazsa yine kopuk kablodur. Gece döngüsü kuyruğa bakar ve
HAFTALIK YOKLAMA BÜTÇESİ içinde (WEEKLY_PROBE_BUDGET = 3) prescreen'i AYRI BİR ARKA PLAN SÜRECİNE
spawn eder — gece döngüsünü BLOKLAMAZ (`ops/barsarchive-run.sh` nohup deseni). Bütçe neden var:
her ölçüm bir DENEMEDİR ve aşınma defterine/DSR'ye N olarak girer; sınırsız otomatik yoklama,
deflasyonu kendi eliyle şişirip her adayı imkânsızlaştırır. Bütçe sayacı bu yüzden aşınma defteriyle
AYNI dili konuşur: her ölçüm `k_probes` beyanıyla kaydedilir.

YASALAR: bu modül KARAR VERMEZ. Kuyruğa yazar, bütçeyi sayar, süreci başlatır, sonucu deftere yazar.
`passes` semantiğine, tek-değişken yasasına ve kapı eşiklerine DOKUNMAZ."""
from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import subprocess

from . import obs, store

QUEUE_FILE = "composite_queue.jsonl"

# HAFTALIK YOKLAMA BÜTÇESİ — adlandırılmış sabit. 3/hafta: aşınma defteri bugün ~289 sorguda ve DSR
# 1e−06; haftada 3 ek deneme N'i ~%1 büyütür (deflasyona etkisi ölçülebilir ama ezici değil).
# Sayı BEYANDIR: değiştirilirse DSR paydası da değişir ve bunu bilmeden büyütmek, kapıyı kendi
# eliyle imkânsızlaştırmaktır.
WEEKLY_PROBE_BUDGET = 3
BUDGET_STATE = "composite_budget.json"

# Kuyruğa alınabilecek en fazla düğme sayısı. 2-3: bileşik ölçümün anlamı "birlikte anlamlı olan
# KÜÇÜK bir demet"tir; 5 düğmelik bir demet artık bir hipotez değil bir strateji yeniden yazımıdır
# ve tek bir prescreen ölçümüyle ayrıştırılamaz.
COMPOSITE_MAX_KNOBS = 3


def _week_key(ts: str | None = None) -> str:
    d = dt.date.fromisoformat((ts or dt.date.today().isoformat())[:10])
    iso = d.isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"


def week_key(ts: str | None = None) -> str:
    """Hafta damgasının DIŞ tüketicilere açık hâli (Katman C, 2026-07-30).

    NEDEN AYNI FONKSİYON: `nous_eval` önerileri hafta damgasıyla kaydeder ve Katman C köprüsü AYNI
    haftanın H4 bütçesinden düşer. İkinci bir damga biçimi (ör. `%Y-%W`, ya da ISO yılı yerine takvim
    yılı) sessizce ayrışır ve yılbaşı haftasında "bu hafta kaç yoklama harcandı" sorusu iki farklı
    cevap verirdi — bütçe bir hafta boyunca İKİ KEZ dolardı ya da hiç dolmazdı. Bütçeyi SAYAN modül
    damganın da tek kaynağıdır."""
    return _week_key(ts)


def validate_composite(composite: dict, bounds: dict) -> tuple[bool, list]:
    """Bileşik önerinin ŞEKİL denetimi. Yasa TEK YERDE: `guard.composite_shape_reasons`.

    Burada YİNELENMEZ — iki yerde iki şekil denetimi olsaydı kuyruğa GİREN aday ile guard'ın
    hüküm verdiği aday sessizce ayrışırdı (2026-07-21'in "her defteri 2-3 modül yazıyor, arada
    yazılı anlaşma yok" dersinin şekil-denetimi hâli)."""
    from . import guard
    nedenler = guard.composite_shape_reasons(composite, bounds)
    return (not nedenler), nedenler


def enqueue(composite: dict, *, rationale: str = "", source: str = "hermes",
            bounds: dict | None = None) -> dict:
    """Bileşik öneriyi kuyruğa yaz. DÖNÜŞ: {"queued": bool, "reasons": [...], "row": {...}|None}.

    Kuyruğa girmek bir ONAY DEĞİLDİR — ölçüm sırasına girmektir. `status` alanı yolun tamamını
    taşır: pending → measuring → measured (+ prescreen çıktısı) ya da rejected_shape."""
    from . import config
    b = bounds if bounds is not None else config.bounds()
    ok, nedenler = validate_composite(composite, b)
    row = {
        "ts": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "id": f"C{_next_seq():05d}",
        "composite": {str(k): v for k, v in (composite or {}).items()},
        "n_knobs": len(composite or {}),
        "rationale": str(rationale or "")[:500],
        "source": str(source),
        "status": "pending" if ok else "rejected_shape",
        "reasons": nedenler,
        "k_probes": None,           # ölçüldüğünde yazılır (aşınma defteriyle aynı dil)
        "result": None,
        "week": _week_key(),
    }
    store.append_jsonl(QUEUE_FILE, row)
    obs.log("composite_enqueued", id=row["id"], n_knobs=row["n_knobs"], status=row["status"],
            reasons=nedenler[:3])
    return {"queued": ok, "reasons": nedenler, "row": row}


def _next_seq() -> int:
    return len(store.read_jsonl(QUEUE_FILE)) + 1


def queue_status(rows: list | None = None) -> dict:
    """Kuyruğun okuma modeli.

    `rows` DIŞARIDAN verilir (shadow_variants.summarize deseni): kendi yazdığını kendi geri okuyan
    modül YASA 6'da tüketici SAYILMAZ ve statik artefakt grafı defteri "yazılıyor ama okunmuyor"
    diye işaretler. Gerçek tüketici `analytics.composite_queue_status()`tur ve satırları O okur;
    burada `rows=None` yalnız CLI kolaylığıdır."""
    rows = store.read_jsonl(QUEUE_FILE) if rows is None else list(rows)
    hafta = _week_key()
    used = _budget_used(hafta)
    by: dict[str, int] = {}
    for r in rows:
        by[str(r.get("status") or "?")] = by.get(str(r.get("status") or "?"), 0) + 1
    bekleyen = [r for r in rows if r.get("status") == "pending"]
    olculen = [r for r in rows if r.get("status") == "measured"]
    return {
        "n": len(rows), "durumlar": by,
        "bekleyen": [{"id": r.get("id"), "composite": r.get("composite"),
                      "rationale": (r.get("rationale") or "")[:160]} for r in bekleyen[:5]],
        "n_bekleyen": len(bekleyen), "n_olculen": len(olculen),
        "son_olcum": (olculen[-1].get("result") if olculen else None),
        "hafta": hafta, "haftalik_butce": WEEKLY_PROBE_BUDGET, "bu_hafta_kullanilan": used,
        "butce_kalan": max(0, WEEKLY_PROBE_BUDGET - used),
        "dosya": QUEUE_FILE,
        "beyan": ("kuyruğa girmek ONAY DEĞİL, ÖLÇÜM SIRASI. Ship yolu yine kapı + operatör; "
                  "tek-değişken yasası KALDIRILMADI."),
    }


def _budget_used(hafta: str | None = None) -> int:
    h = hafta or _week_key()
    st = store.read_json(BUDGET_STATE, {}) or {}
    return int((st.get("weeks") or {}).get(h, 0))


def _budget_take(hafta: str | None = None) -> bool:
    """Bütçeden BİR yoklama düş. False → bu hafta bütçe bitti (ölçüm başlatılmaz)."""
    h = hafta or _week_key()

    # `st`i YENİDEN BAĞLAMAK YASAK. `store.update_json` `fn(doc)`u çağırıp AYNI `doc` nesnesini
    # diske yazar; `st = st or {}` satırı BOŞ bir sözlükte (falsy!) YENİ bir nesne yaratıyordu ve
    # bütün mutasyonlar o yeni nesneye gidiyordu → dosyaya `{}` yazılıyor, sayaç hiç artmıyor, bütçe
    # SINIRSIZ oluyordu. İlk koşuda tam olarak bu yakalandı (10 yoklamanın 10'u da izin aldı) ve
    # bu, H4'ün tek emniyetinin sessizce yok olması demekti — DSR paydası sınırsız şişerdi.
    def _f(st):
        if st is None:                       # default `{}` verildiği için normalde olmaz
            return False
        weeks = st.setdefault("weeks", {})
        cur = int(weeks.get(h, 0))
        if cur >= WEEKLY_PROBE_BUDGET:
            st["_denied"] = True
            return True                       # yazılır: reddin kendisi de kayıttır
        weeks[h] = cur + 1
        st["_denied"] = False
        st["butce"] = WEEKLY_PROBE_BUDGET
        st["son"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
        return True

    out = store.update_json(BUDGET_STATE, _f, {})
    return not bool((out or {}).get("_denied"))


def mark(row_id: str, status: str, **fields) -> None:
    """Kuyruk satırının durumunu güncelle (JSONL yeniden yazımı — kuyruk küçük ve tavanlı)."""
    def _f(rows):
        for r in rows:
            if r.get("id") == row_id:
                r["status"] = status
                r.update(fields)
                r["status_ts"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
        return rows
    store.update_jsonl(QUEUE_FILE, _f)


# ---- H4: gece döngüsünün kancası ---------------------------------------------------------------
SPAWN_LOG = "logs/composite-prescreen.log"


def _python() -> str:
    """Ölçümü ÇALIŞAN YORUMLAYICIYLA başlat. `"python"` yazmak, canlı worker'ın .venv'i yerine
    sistem python'una düşme riskiydi (numpy/pandas yok → süreç anında ölür, log'da görünür ama
    bütçe harcanmış olur)."""
    import sys
    return sys.executable or "python"


def spawn_pending(limit: int = 1, dry_run: bool = False) -> dict:
    """Bekleyen bileşikleri HAFTALIK BÜTÇE içinde AYRI SÜREÇTE ölçmeye başlat.

    GECE DÖNGÜSÜNÜ BLOKLAMAZ: `prescreen --composite` dakikalar sürer; gece döngüsünün içinde
    senkron çağrılsaydı EOD işleri gecikirdi. Desen `ops/barsarchive-run.sh` ile aynı: nohup'lu
    ayrı süreç, kendi log dosyası, `start_new_session` ile döngünün süreç grubundan KOPUK (döngü
    ölse ölçüm devam eder ve tersi).

    Sonuç YAZIMI ölçümü yapan süreçtedir (prescreen çıktısı) — burada satır `measuring` olur ve
    ertesi gece `evidence_pack` kuyruğun durumunu görür. `dry_run`: testler için (süreç açmaz)."""
    rows = store.read_jsonl(QUEUE_FILE)
    bekleyen = [r for r in rows if r.get("status") == "pending"]
    out = {"n_bekleyen": len(bekleyen), "spawned": [], "atlanan": [], "butce_kalan": None,
           "dry_run": bool(dry_run)}
    if not bekleyen:
        out["not"] = "kuyruk boş — yapılacak ölçüm yok"
        out["butce_kalan"] = max(0, WEEKLY_PROBE_BUDGET - _budget_used())
        return out
    for r in bekleyen[:max(0, int(limit))]:
        if not _budget_take():
            out["atlanan"].append({"id": r.get("id"), "why": "haftalık yoklama bütçesi doldu"})
            obs.log("composite_budget_exhausted", id=r.get("id"), butce=WEEKLY_PROBE_BUDGET,
                    hafta=_week_key())
            break
        # BİÇİM PRESCREEN'İN SÖZLEŞMESİNDEN: `;` bir adayın DÜĞMELERİNİ ayırır (`|` ayrı adaylar).
        # Kuyruk satırı TEK bir bileşik adaydır → yalnız `;` kullanılır. `--workdir` zorunlu ve
        # kuyruk kimliğiyle adlandırılır: iki ölçüm birbirinin state kopyasını EZMESİN.
        arg = ";".join(f"{k}={v}" for k, v in (r.get("composite") or {}).items())
        workdir = f"/tmp/prescreen-{r.get('id')}"
        cmd = [_python(), "-m", "meridian.prescreen", "--composite", arg, "--workdir", workdir]
        if dry_run:
            out["spawned"].append({"id": r.get("id"), "cmd": cmd, "pid": None})
            mark(str(r.get("id")), "measuring", k_probes=1, cmd=" ".join(cmd), dry_run=True)
            continue
        try:
            root = pathlib.Path(__file__).resolve().parent.parent
            logp = root / SPAWN_LOG
            logp.parent.mkdir(parents=True, exist_ok=True)
            with open(logp, "a", encoding="utf-8") as fh:
                fh.write(f"\n=== {dt.datetime.now(dt.timezone.utc).isoformat()} {r.get('id')} "
                         f"{' '.join(cmd)}\n")
                fh.flush()
                p = subprocess.Popen(cmd, cwd=str(root), stdout=fh, stderr=subprocess.STDOUT,
                                     start_new_session=True,
                                     env={**os.environ, "PYTHONUNBUFFERED": "1"})
            mark(str(r.get("id")), "measuring", k_probes=1, pid=p.pid, cmd=" ".join(cmd))
            out["spawned"].append({"id": r.get("id"), "cmd": cmd, "pid": p.pid})
            obs.log("composite_prescreen_spawned", id=r.get("id"), pid=p.pid, knobs=arg)
        except Exception as e:
            # YASA 4: süreç başlatılamazsa BÜTÇE HARCANDI ama ölçüm olmadı — sessiz kalırsa kuyruk
            # dolu, bütçe boş, kimse fark etmez. Satır `pending` bırakılır ve uyarı basılır.
            obs.warn("composite_spawn_failed", id=r.get("id"), error=f"{type(e).__name__}: {e}",
                     detail="bileşik prescreen süreci BAŞLATILAMADI — bütçe harcandı, ölçüm yok")
            out["atlanan"].append({"id": r.get("id"), "why": f"spawn hatası: {type(e).__name__}"})
    out["butce_kalan"] = max(0, WEEKLY_PROBE_BUDGET - _budget_used())
    return out


def _cli() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Bileşik öneri kuyruğu (H3/H4)")
    ap.add_argument("--durum", action="store_true", help="kuyruk durumu")
    ap.add_argument("--ekle", help="düğme demeti: k=v,k=v")
    ap.add_argument("--gerekce", default="elle eklendi (CLI)")
    ap.add_argument("--spawn", action="store_true", help="bekleyeni ölçmeye başlat")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    if a.ekle:
        comp = {}
        for parca in a.ekle.split(","):
            if "=" in parca:
                k, v = parca.split("=", 1)
                comp[k.strip()] = float(v)
        print(json.dumps(enqueue(comp, rationale=a.gerekce, source="cli"), ensure_ascii=False, indent=1))
    if a.spawn:
        print(json.dumps(spawn_pending(dry_run=a.dry_run), ensure_ascii=False, indent=1))
    if a.durum or not (a.ekle or a.spawn):
        print(json.dumps(queue_status(), ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
