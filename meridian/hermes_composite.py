"""hermes_composite.py — bileşik (çok-düğmeli) önerilerin ölçüm kuyruğu: tek-değişken yasasını
gevşetmeden fikri çöpe atmamak.

Ne yapar: tek-değişken yasası (`goal.one_variable_only`) kapının temel disiplinidir ve kalkmaz —
iki düğmeyi birlikte oynatıp iyileşme görmek hangisinin işe yaradığını ÖLÇMEZ. Ama hermes bir
bileşik fikir ürettiğinde (ör. "stop_mode=1 İLE stop_buffer_atr=0.4 birlikte anlamlı") o fikir
bilgidir; guard'da reddedilip çöpe gitmesi ölçülmemiş bir kayıptı. `enqueue` bu fikri guard'ı
ATLAMADAN ve canlıya GİTMEDEN `state/composite_queue.jsonl` kuyruğuna yazar (ledgers sözleşmeli);
kuyruk `prescreen --composite` resmî ölçüm yolunun girdisidir. Gece döngüsü `spawn_pending` ile
haftalık yoklama bütçesi içinde prescreen'i ayrı bir arka plan sürecine başlatır (gece döngüsü
bloklanmaz); alt süreç `--queue-id` taşır ve ölçüm bitişinde aynı satıra `mark(id, "measured")`
yazılır. `reap_measuring` ölmüş ölçüm süreçlerini yoklayıp `measure_failed` damgalar — sessiz
asılı satır yoktur, ne damgalanan ne damgalanamayan hâl sessizdir. `week_key` hafta damgasının
tek kaynağıdır: bütçeyi sayan modül damgayı da tanımlar, ikinci bir biçim sessizce ayrışırdı.

Değişmezler: bu modül KARAR VERMEZ — `passes` semantiğine, tek-değişken yasasına ve kapı
eşiklerine dokunmaz; ship yolu yine kapı + operatördür (kuyruğa girmek onay değil, ölçüm
sırasıdır). Bütçe (WEEKLY_PROBE_BUDGET=3) bir beyandır: her ölçüm bir DENEMEDİR ve aşınma
defterine/DSR paydasına `k_probes` beyanıyla N olarak girer; sınırsız otomatik yoklama
deflasyonu kendi eliyle şişirip her adayı imkânsızlaştırır. Demet boyu en çok
COMPOSITE_MAX_KNOBS=3: daha büyüğü hipotez değil strateji yeniden yazımıdır. Şekil hükmü tek
yerdedir (`guard.composite_shape_reasons`) — iki denetim kopyası sessizce ayrışırdı.

Okur/yazar: composite_queue.jsonl (kuyruk; status: pending → measuring → measured /
measure_failed / rejected_shape) ve composite_budget.json (haftalık sayaç) yazar; olayları
events.jsonl'a (obs) düşer."""
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
    """Haftalık bütçe damgasını ISO takvimden üretir: "YYYY-Www" (ts yoksa bugün).

    Damganın TEK kaynağı burasıdır — bütçeyi sayan modül damgayı da tanımlar; ikinci bir
    biçim yılbaşı haftasında sessizce ayrışırdı."""
    d = dt.date.fromisoformat((ts or dt.date.today().isoformat())[:10])
    iso = d.isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"


def week_key(ts: str | None = None) -> str:
    """Hafta damgasının DIŞ tüketicilere açık hâli (Katman C).

    NEDEN AYNI FONKSİYON: `nous_eval` önerileri hafta damgasıyla kaydeder ve Katman C köprüsü AYNI
    haftanın yoklama bütçesinden düşer. İkinci bir damga biçimi (ör. `%Y-%W`, ya da ISO yılı yerine takvim
    yılı) sessizce ayrışır ve yılbaşı haftasında "bu hafta kaç yoklama harcandı" sorusu iki farklı
    cevap verirdi — bütçe bir hafta boyunca İKİ KEZ dolardı ya da hiç dolmazdı. Bütçeyi SAYAN modül
    damganın da tek kaynağıdır."""
    return _week_key(ts)


def validate_composite(composite: dict, bounds: dict) -> tuple[bool, list]:
    """Bileşik önerinin ŞEKİL denetimi. Yasa TEK YERDE: `guard.composite_shape_reasons`.

    Burada YİNELENMEZ — iki yerde iki şekil denetimi olsaydı kuyruğa GİREN aday ile guard'ın
    hüküm verdiği aday sessizce ayrışırdı ("her defteri 2-3 modül yazıyor, arada
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
    """Sıradaki kuyruk sıra numarası: mevcut satır sayısı + 1 (C%05d kimliğinin sayısal kısmı)."""
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
    # BAŞARISIZ ÖLÇÜM AYRI SAYILIR: `measure_failed`, `pending`den de `measured`dan da
    # BAŞKA bir olgudur — "sıra bekliyor" değil, "ölçüldü ve sonuç yok" da değil; ÖLÇÜM DENENDİ,
    # BÜTÇE HARCANDI, SONUÇ YOK. Tek sayaca katlansaydı halkanın koptuğu yer yine görünmezdi.
    basarisiz = [r for r in rows if r.get("status") == "measure_failed"]
    olculuyor = [r for r in rows if r.get("status") == "measuring"]
    return {
        "n": len(rows), "durumlar": by,
        "bekleyen": [{"id": r.get("id"), "composite": r.get("composite"),
                      "rationale": (r.get("rationale") or "")[:160]} for r in bekleyen[:5]],
        "n_bekleyen": len(bekleyen), "n_olculen": len(olculen),
        "n_basarisiz": len(basarisiz), "n_olculuyor": len(olculuyor),
        "son_basarisiz": ({"id": basarisiz[-1].get("id"), "neden": basarisiz[-1].get("neden")}
                          if basarisiz else None),
        "son_olcum": (olculen[-1].get("result") if olculen else None),
        "hafta": hafta, "haftalik_butce": WEEKLY_PROBE_BUDGET, "bu_hafta_kullanilan": used,
        "butce_kalan": max(0, WEEKLY_PROBE_BUDGET - used),
        "dosya": QUEUE_FILE,
        "beyan": ("kuyruğa girmek ONAY DEĞİL, ÖLÇÜM SIRASI. Ship yolu yine kapı + operatör; "
                  "tek-değişken yasası KALDIRILMADI."),
    }


def _budget_used(hafta: str | None = None) -> int:
    """Verilen haftada (varsayılan: bu hafta) şimdiye dek harcanmış yoklama sayısını okur.

    Sayaç `composite_budget.json` içindedir; kayıt yoksa 0 döner."""
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
    # bu, bileşik yolun tek emniyetinin sessizce yok olması demekti — DSR paydası sınırsız şişerdi.
    def _f(st):
        """`store.update_json` mutasyonu: hafta sayacını yerinde artırır, tavanda `_denied` basar.

        `st` YENİDEN BAĞLANMAZ — aynı nesne diske yazılır; yeni bir sözlük yaratmak sayacı
        sessizce sıfırlar ve haftalık bütçeyi sınırsız yapardı."""
        if st is None:                     # default `{}` verildiği için normalde olmaz
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


# ---- Gece döngüsünün kancası -------------------------------------------------------------------
SPAWN_LOG = "logs/composite-prescreen.log"


def _pid_canli(pid) -> bool | None:
    """Süreç YAŞIYOR mu? True/False/None — None = ÖLÇÜLEMEDİ ("ölü" DEĞİL, uydurma yasağı).

    `os.kill(pid, 0)` HİÇBİR sinyal göndermez; yalnız "bu pid'e sinyal gönderebilir miydim" sorusunu
    çekirdeğe sorar. ESRCH → böyle bir süreç yok (ölü). EPERM → süreç VAR ama başkasının (canlı sayılır;
    "izin yok"u "ölü" saymak, ölçümü koşan sürece ait olmayan bir hüküm kurmak olurdu).

    BEYAN EDİLMİŞ SINIR — PID GERİ DÖNÜŞÜMÜ: işletim sistemi pid'leri yeniden kullanır, dolayısıyla
    "canlı" cevabı o pid'in BİZİM prescreen'imiz olduğunu KANITLAMAZ. Yanılma yönü bilerek
    muhafazakârdır: geri dönüşmüş bir pid'i canlı sanıp bir tur daha bekleriz (satır asılı kalır ama
    YANLIŞ damga basılmaz); tersi yönde, koşan bir ölçümü "başarısız" damgalayıp sonucunu çöpe atmış
    olurduk. Kimlik kanıtı (cmdline eşlemesi) taşınabilir değil (Linux /proc vs. macOS) ve bu tur
    onu ölçmedi — açık ölçüm borcu."""
    try:
        p = int(pid)
    except (TypeError, ValueError):  # sessiz-yutma: pid alanı YOK ya da biçimsiz — bu bir ölçüm SONUCU değil ÖLÇÜLEMEZLİKtir; çağıran None'ı ayrı bir dal olarak işler ve damga basmaz
        return None
    if p <= 0:
        return None
    try:
        os.kill(p, 0)
        return True
    except ProcessLookupError:  # sessiz-yutma: istisnanın KENDİSİ ölçümün cevabıdır — ESRCH "böyle bir süreç yok" demektir ve çağıran onu measure_failed damgası + YASA 4 uyarısı olarak yazar; burada ikinci bir kanal gürültü olurdu
        return False
    except PermissionError:  # sessiz-yutma: EPERM "süreç VAR ama başkasının" demektir, yani canlılık ÖLÇÜLDÜ; izin yokluğunu ölüm saymak koşan bir ölçümü çöpe attırırdı ve bu bir arıza değil normal çok-kullanıcılı hâldir
        return True
    except OSError:  # sessiz-yutma: çekirdek başka bir nedenle cevap veremedi; canlılık ÖLÇÜLEMEDİ ve None dalı damga basmadan görünürlüğü korur
        return None


def reap_measuring(rows: list | None = None) -> dict:
    """'measuring' satırların süreç canlılığını yokla; ölmüş süreç → `measure_failed`.

    NEDEN: prescreen ayrı bir süreçte koşar (`start_new_session`). O süreç çökerse, VM yeniden
    başlarsa ya da OOM killer alırsa satır SONSUZA DEK 'measuring' kalırdı — `nous_eval._akibet`
    beyne "ÖLÇÜLÜYOR (prescreen süreci koşuyor)" demeye devam eder, beyin aynı öneriyi her hafta
    yeniden üretir ve haftalık bütçe harcanmış olur. Yoklama gece kancasının (spawn_pending) İLK
    adımıdır: yeni ölçüm başlatmadan önce eski ölçümlerin akıbeti kesinleşir.

    BÜTÇE İADE EDİLMEZ. `_budget_take` spawn'dan ÖNCE çağrılır ve o yoklama GERÇEKTEN harcandı
    (süreç açıldı, CPU yandı, belki yarım ölçüm yazıldı). Başarısızlığı bahane edip sayacı geri
    almak, bütçeyi "başarılı ölçüm sayacı"na çevirirdi — oysa bu bütçe DENEME sayar (DSR paydası
    da denemeleri sayar), başarıyı değil.

    ÜÇ DAL, ÜÇÜ DE GÖRÜNÜR: ölü → damga; canlı → dokunulmaz; ölçülemedi (pid yok/biçimsiz) →
    DAMGALANMAZ ama uyarılır ve `queue_status.n_olculuyor` içinde sayılır. Kuru koşum (`dry_run`)
    satırları hiç süreç açmadığı için ölçüm bile denemedi: ayrı bir kovada raporlanır."""
    rows = store.read_jsonl(QUEUE_FILE) if rows is None else list(rows)
    out: dict = {"olu": [], "canli": [], "olculemedi": [], "kuru_kosum": []}
    for r in rows:
        if str(r.get("status") or "") != "measuring":
            continue
        rid = str(r.get("id") or "")
        if r.get("dry_run"):
            out["kuru_kosum"].append(rid)
            continue
        canli = _pid_canli(r.get("pid"))
        if canli is True:
            out["canli"].append(rid)
            continue
        if canli is None:
            out["olculemedi"].append(rid)
            obs.warn("composite_measuring_pid_yok", id=rid, pid=r.get("pid"),
                     detail="'measuring' satırında yoklanabilir pid YOK — süreç canlılığı "
                            "ÖLÇÜLEMEDİ, bu yüzden damga basılmadı (uydurma yasağı); satır "
                            "kuyruk durumunda n_olculuyor içinde görünür")
            continue
        mark(rid, "measure_failed", pid=r.get("pid"),
             neden="ölçüm süreci ÖLÜ (pid yoklaması ESRCH) — sonuç geri yazılmadan sonlandı",
             result=None)
        out["olu"].append(rid)
        obs.warn("composite_measure_failed", id=rid, pid=r.get("pid"),
                 detail="bileşik ölçüm süreci sonuç yazmadan öldü — satır measure_failed "
                        "damgalandı; haftalık yoklama bütçesi HARCANDI ve iade edilmez")
    return out


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
    ölçüm bitince O SÜREÇ `--queue-id` ile aynı satıra `measured` yazar (halkayı kapatan kablo). Ertesi gece
    `evidence_pack` kuyruğun durumunu görür. `dry_run`: testler için (süreç açmaz).

    ÖLÜ SÜREÇ TOPLAMA İLK ADIMDIR: yeni ölçüm başlatmadan önce eski 'measuring' satırların akıbeti
    kesinleşir (`reap_measuring`). Sıra tersine olsaydı gece kancası, ölmüş bir ölçümün yanına bir
    yenisini koyar ve kuyruk "iki ölçüm koşuyor" derdi — biri aylar önce ölmüşken."""
    reaped = reap_measuring()
    rows = store.read_jsonl(QUEUE_FILE)
    bekleyen = [r for r in rows if r.get("status") == "pending"]
    out = {"n_bekleyen": len(bekleyen), "spawned": [], "atlanan": [], "butce_kalan": None,
           "dry_run": bool(dry_run), "reaped": reaped}
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
        #
        # `--queue-id` HALKAYI KAPATAN TEK BAYTTIR: alt süreç kuyruk kimliğini bilmeden
        # sonucu geri yazamaz — ve bilgi ona verilmediği için bugüne dek yazamadı. Kimlik komut
        # satırından taşınır (dosya/ortam değişkeni değil): `logs/composite-prescreen.log`a düşen
        # komut satırı, hangi sürecin hangi kuyruk satırını ölçtüğünün DENETLENEBİLİR kaydı olsun.
        arg = ";".join(f"{k}={v}" for k, v in (r.get("composite") or {}).items())
        workdir = f"/tmp/prescreen-{r.get('id')}"
        cmd = [_python(), "-m", "meridian.prescreen", "--composite", arg, "--workdir", workdir,
               "--queue-id", str(r.get("id") or "")]
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
    ap.add_argument("--yokla", action="store_true",
                    help="'measuring' satırların süreç canlılığını yokla (ölü → measure_failed)")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    if a.ekle:
        comp = {}
        for parca in a.ekle.split(","):
            if "=" in parca:
                k, v = parca.split("=", 1)
                comp[k.strip()] = float(v)
        print(json.dumps(enqueue(comp, rationale=a.gerekce, source="cli"), ensure_ascii=False, indent=1))
    if a.yokla:
        print(json.dumps(reap_measuring(), ensure_ascii=False, indent=1))
    if a.spawn:
        print(json.dumps(spawn_pending(dry_run=a.dry_run), ensure_ascii=False, indent=1))
    if a.durum or not (a.ekle or a.spawn or a.yokla):
        print(json.dumps(queue_status(), ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
