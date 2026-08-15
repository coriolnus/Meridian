"""skill_evolve.py — ölçülmüş-zayıf skill'ler için revize SKILL.md TASLAĞI üreten, operatör-onaylı içerik-evrim döngüsü.

NE YAPAR. Karne (gerçek + karşı-olgusal katkı) hızla dolarken karnesi kötü skill'in İÇERİĞİ
sonsuza dek aynı kalıyordu. Bu modül döngüyü taslak düzeyinde kapatır: gerçek işlemde yeterli izi
olan (MIN_REAL_N) ve ortalama katkısı eşiğin altındaki (MAX_AVG_R) bir skill için ajan — katkı
verisi, çıkış-verimliliği ve derslerle temellendirilmiş — revize bir SKILL.md taslağını YAN
dosyaya (SKILL.md.v2-draft) yazar; taslak Skiller sayfasında görünür, operatör onaylarsa
yürürlüğe girer (eski sürüm SKILL.md.v{N}.bak olarak arşivlenir), reddederse silinir.

KİLİT GİRİŞLER. `weekly_draft` (haftada en fazla BİR taslak; mekanizma arızası sessiz kalamaz —
sağlık defterine kesinti yazılır ve hata yükseltilir), `weak_skills` (aday süzgeci),
`draft_revision` (ajan çağrısı + atomik taslak yazımı), `apply_revision`/`reject_revision`
(operatör kararı), `revisions`/`pending_drafts` (defter okuma), `_repo_skill_dir` (ad doğrulamalı
yol çözümü).

DEĞİŞMEZLER. OTOMATİK HİÇBİR ŞEY DEĞİŞMEZ: canlı SKILL.md yalnız operatör onay yolundan değişir.
Korunan skill'ler (skills.PROTECTED) ve çekirdek küme (CORE_NEVER) hem taslak üretiminde hem
UYGULAMADA reddedilir — savunma iki uçta da durur (tek uçlu hâli, elde taslağı bulunan korunan
skill'in apply ile ezilmesine açıktı). Skill adı doğrulanır ve çözülen yol skills/ altında kalmak
zorundadır (yol-kaçışı reddedilir). Defterin dönüş tipi tek noktada garanti list[dict]'tir: bozuk
disk şekli onarılır, onarım kayda geçer (bozuk şekil iki mekanizmayı sessizce düşürmüştü ve pano
sakin sistemle arızalı sistemi ayırt edemiyordu — ders korunur). Uygulama tarihi kayda geçer ki
karne sürüm-öncesi/sonrası kıyaslanabilsin.

OKUR: analytics.skill_attribution, exit_efficiency.json, state/lessons.md, skills/<ad>/SKILL.md.
YAZAR: state/skill_revisions.json + skills/<ad>/SKILL.md.v2-draft (SKILL.md'nin kendisi yalnız
onay yolunda değişir, eski sürüm arşivlenerek)."""
from __future__ import annotations
import datetime as dt
import json
import os
import re

from . import config, store, obs

REVISIONS_FILE = "skill_revisions.json"
MIN_REAL_N = 15            # taslak tetiklemek için skill'in GERÇEK işlemde en az bu kadar izi olmalı
MAX_AVG_R = -0.10          # ve ort. gerçek katkısı bunun altında (ölçülmüş-zayıf)
CORE_NEVER = {"pre-trade-discipline-gate", "position-sizer", "backtest-expert"}


def _skills_root() -> str:
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills")


def _repo_skill_dir(name: str) -> str:
    """Skill adından dizin — ADI DOĞRULAYARAK (denetim turu 29, 2026-07-21).

    Eskiden ad doğrudan os.path.join'e giriyordu: `../../..` içeren bir ad skills/ dışına çıkar ve
    apply_revision o yolda DOSYA DEĞİŞTİRİRDİ (os.replace). Ad panodan geliyor; yetki gerekiyor ama
    savunma tek katmana bırakılmaz. Ayrıca çözülen yolun skills/ altında kaldığı ayrıca doğrulanır."""
    if not name or not re.fullmatch(r"[A-Za-z0-9._-]+", str(name)) or str(name).startswith("."):
        raise ValueError(f"geçersiz skill adı: {name!r}")
    root = _skills_root()
    path = os.path.realpath(os.path.join(root, str(name)))
    if not (path == os.path.realpath(root) or path.startswith(os.path.realpath(root) + os.sep)):
        raise ValueError(f"skills/ dışına çıkan yol reddedildi: {name!r}")
    return path


def _refuse_protected(skill_name: str) -> str | None:
    """Korunan/çekirdek skill ASLA yazılamaz. Bu kontrol taslak ÜRETİMİNDE vardı ama UYGULAMADA
    yoktu (turu 29): elde bir taslak dosyası bulunan korunan bir skill, apply ile ezilebilirdi —
    kapı skill'i dahil. Savunma her iki uçta da olmalı."""
    from . import skills as sk
    protected = set(getattr(sk, "PROTECTED", ()) or ()) | CORE_NEVER
    return f"'{skill_name}' korumalı — içeriği revizyonla değiştirilemez" if skill_name in protected else None


def weak_skills() -> list[dict]:
    """Revizyon adayları: gerçek n>=MIN_REAL_N, ort.R<=MAX_AVG_R, korumasız, çekirdek-dışı, etkin."""
    from . import analytics, skills as sk
    protected = set(getattr(sk, "PROTECTED", ()) or ())
    enabled = {s2["name"] for s2 in sk.catalog() if s2.get("enabled")}
    out = []
    for a in analytics.skill_attribution().get("skills", []):
        n2 = a.get("n") or 0
        # katalog boşsa (sandbox/taze kurulum) enabled süzgeci atlanır — koruma süzgeci HER ZAMAN işler
        if ((not enabled or a["skill"] in enabled)
                and a["skill"] not in protected and a["skill"] not in CORE_NEVER
                and n2 >= MIN_REAL_N and a.get("avg_r") is not None and a["avg_r"] <= MAX_AVG_R):
            out.append(a)
    out.sort(key=lambda a: a["avg_r"])
    return out


def _coerce_revisions(raw) -> tuple[list[dict], str | None]:
    """(satırlar, onarım_notu) — bilinen bozuk disk şekillerinden list[dict] türet.

    ŞEKİLLER: çift-kodlanmış JSON metni (`"[...]"`), skill→kayıt SÖZLÜĞÜ, karışık liste. Üçünde de
    `for r in ...` bir `str` verir; onu düşürmek yerine anlamı korunarak satıra çevrilir."""
    note = None
    if isinstance(raw, str):
        try:
            raw, note = json.loads(raw), "çift-kodlanmış JSON metni bir kez daha çözüldü"
        except (ValueError, TypeError):  # sessiz-yutma: sonuç KAYDA GEÇİYOR — dönen not "defter okunamadı" der ve çağıran onu `skill_revisions_repaired` olarak loglar; bilgi kaybolmaz
            return [], "defter düz metindi — hiçbir revizyon kaydı okunamadı"
    if isinstance(raw, dict):
        rows = [{**v, "skill": v.get("skill") or k} for k, v in raw.items() if isinstance(v, dict)]
        return rows, note or "sözlük şekli (skill→kayıt) listeye çevrildi"
    if not isinstance(raw, list):
        return [], f"beklenmeyen defter tipi: {type(raw).__name__}"
    rows = [r for r in raw if isinstance(r, dict)]
    if len(rows) != len(raw):
        note = note or f"{len(raw) - len(rows)} satır sözlük değildi — düşürüldü"
    return rows, note


_REPAIR_WARNED = False


def revisions() -> list[dict]:
    """Revizyon defterini okuyan HERKES buradan geçer; dönüş tipi garanti list[dict].

    CANLI ARIZA (2026-07-20 → 07-21, 436 + 424 sessiz düşüş): state/skill_revisions.json diskte
    list[dict] DEĞİLDİ. `for r in <sözlük>` satır yerine ANAHTAR, `for r in <çift-kodlanmış metin>`
    ise KARAKTER verir — ikisi de bir sonraki `r.get(...)` çağrısında
    "AttributeError: 'str' object has no attribute 'get'" ile patlar. Defteri okuyan İKİ mekanizma
    da (bu modülün haftalık taslağı + selfreview.build'in 'revisions_pending' sayacı) her koşumda
    düştü, ikisi de çağıranda obs.warn'a yutuldu ve pano "dikkat maddesi yok" gösterdi: sakin
    sistemle ARIZALI sistem ayırt edilemedi. Tip kontrolü artık TEK noktada; bozuk şekil onarılır,
    onarıldığı KAYDEDİLİR ve düzeltilmiş hâli diske geri yazılır (aynı hata 400 kez tekrarlamasın)."""
    global _REPAIR_WARNED
    raw = store.read_json(REVISIONS_FILE, [])
    rows, note = _coerce_revisions(raw)
    if note is not None:
        if not _REPAIR_WARNED:                 # süreç başına bir kez uyar (olay seli yok)
            _REPAIR_WARNED = True
            obs.warn("skill_revisions_repaired", detail=note, was=type(raw).__name__,
                     kept=len(rows))
        store.write_json(REVISIONS_FILE, rows)
    return rows


def pending_drafts() -> list[dict]:
    # `skill` alanı ŞART: api/gelen kutusu r["skill"] ile okuyor — adsız bir kayıt orayı 500 yapardı.
    return [r for r in revisions() if r.get("status") == "draft" and r.get("skill")]


def _write_revisions(recs: list) -> None:
    """Deftere YALNIZ list[dict] yazılır — bozuk şekil bir daha diske dönemez."""
    store.write_json(REVISIONS_FILE, [r for r in recs if isinstance(r, dict)])


def draft_revision(skill_name: str) -> dict | None:
    """Ajan revizyon taslağı yazar. Çıktı: skills/<ad>/SKILL.md.v2-draft + kayıt. None = üretilemedi
    (ajan yok/kota/parse) — fail-open, hiçbir şey değişmez."""
    from . import hermes, analytics
    path = os.path.join(_repo_skill_dir(skill_name), "SKILL.md")
    if not os.path.isfile(path):
        return None
    current = open(path).read()[:4000]
    attr = next((a for a in analytics.skill_attribution().get("skills", [])
                 if a["skill"] == skill_name), {})
    ee = store.read_json("exit_efficiency.json", {}) or {}
    lessons = ""
    try:
        lp = config.STATE / "lessons.md"
        lessons = lp.read_text()[-2000:] if lp.exists() else ""
    except Exception:  # sessiz-yutma: yardımcı G/Ç yolu; çağıran yokluğu zaten yedek değerle karşılıyor ve asıl okuma hatası store katmanında bir kez uyarılıyor
        pass
    prompt = (f"You maintain Meridian's trading skill library. The skill below MEASURABLY underperforms "
              f"(real trades n={attr.get('n')}, avg_r={attr.get('avg_r')}R; simulated n={attr.get('n_cf')}, "
              f"cf_avg_r={attr.get('cf_avg_r')}R; exit-efficiency context: {ee.get('worst_reason')} leaves "
              f"{ee.get('worst_left_r')}R on the table). Rewrite it: keep the same frontmatter name and "
              f"overall purpose, fix the measured weaknesses, incorporate the lessons. Ground every change "
              f"in the numbers above.\n\nCURRENT SKILL.md:\n{current}\n\nRECENT LESSONS:\n{lessons}\n\n"
              f"Respond with the COMPLETE revised SKILL.md between <REVISED> and </REVISED> markers, then "
              f"one line: RATIONALE: <one sentence in Turkish>.")
    text = hermes._agent_call(prompt, preload=("backtest-expert",), kind="skill_revision",
                              timeout=300, max_wait=60.0)
    if not text or "<REVISED>" not in text or "</REVISED>" not in text:
        obs.warn("skill_revision_failed", skill=skill_name, detail="ajan taslak üretemedi (fail-open)")
        return None
    body = text.split("<REVISED>", 1)[1].split("</REVISED>", 1)[0].strip()
    if len(body) < 200:                                   # bariz bozuk taslak — yazma
        obs.warn("skill_revision_failed", skill=skill_name, detail="taslak çok kısa")
        return None
    rationale = ""
    for line in text.splitlines():
        if line.strip().upper().startswith("RATIONALE:"):
            rationale = line.split(":", 1)[1].strip()[:300]
            break
    draft_path = path + ".v2-draft"
    # KAPI-DIŞI TAŞIMA (H9 Kademe C): düz open(w) → store.write_text (atomik tmp+fsync+flock). NEDEN
    # ATOMİK ŞART: yarım/sıfır-baytlık taslak, operatör ONAY YOLUNDA os.replace ile CANLI SKILL.md'ye
    # taşınır → ajan bozuk skill okur. draft_path skills/ altında (STATE DIŞI) → store mutlak adı
    # olduğu gibi kullanır; tek yazar (bu fonksiyon) için kilit yeterli. YASA-6 OKUYUCU: onay yolu
    # (os.replace ile SKILL.md yapar) + pano ipucu (app.js:8367); taşınan SKILL.md sonra hermes-agent
    # skill kütüphanesince okunur.
    store.write_text(draft_path, body)
    recs = revisions()
    recs = [r for r in recs if not (r.get("skill") == skill_name and r.get("status") == "draft")]
    rec = {"skill": skill_name, "status": "draft", "rationale": rationale,
           "at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
           "evidence": {"n": attr.get("n"), "avg_r": attr.get("avg_r"),
                        "n_cf": attr.get("n_cf"), "cf_avg_r": attr.get("cf_avg_r")},
           "chars": len(body)}
    recs.append(rec)
    _write_revisions(recs)
    obs.log("skill_revision_drafted", skill=skill_name, chars=len(body))
    try:
        from . import notify
        if notify.configured():
            notify.send(f"📝 Skill revizyon taslağı hazır: {skill_name} — Skiller sayfasında onayını bekliyor")
    except Exception:  # sessiz-yutma: obs alarmı/kaydı bu noktada ZATEN yazıldı; ikincil bildirim kanalının (Telegram/webhook) düşmesi alarmı asla düşüremez
        pass
    return rec


def weekly_draft() -> dict | None:
    """Haftada en fazla bir taslak: bekleyen taslağı olmayan EN ZAYIF aday seçilir.

    ARIZA SESSİZ KALAMAZ (canlı: 436 koşumun 436'sı düştü, tek iz çağıranın obs.warn'ıydı ve pano
    boş görünüyordu): mekanizma çıktı üretemiyorsa bu uyarı değil KESİNTİdir — sağlık defterine
    seri sayacı + MECHANISM_STALE alarmı yazılır, sonra hata AYNEN yükseltilir ki zamanlayıcı
    haftayı 'yapıldı' diye işaretlemesin (yeniden deneme davranışı korunur)."""
    from . import selfreview
    try:
        have = {r["skill"] for r in pending_drafts()}
        out = None
        for a in weak_skills():
            if a["skill"] not in have:
                out = draft_revision(a["skill"])
                break
    except Exception as e:
        selfreview.mechanism_failed("skill_revision", e)
        raise
    # aday YOKSA da mekanizma sağlıklıdır: "önerilecek zayıf skill yok" dürüst bir cevaptır
    selfreview.mechanism_ok("skill_revision")
    return out


def apply_revision(skill_name: str) -> dict:
    """OPERATÖR ONAYI: taslak yürürlüğe girer; eski sürüm SKILL.md.v{N}.bak olarak arşivlenir;
    uygulama tarihi kayda geçer (karne sürüm-öncesi/sonrası kıyaslanabilir)."""
    refusal = _refuse_protected(skill_name)
    if refusal:
        obs.warn("skill_revision_refused", skill=skill_name, detail=refusal)
        return {"ok": False, "detail": refusal}
    try:
        path = os.path.join(_repo_skill_dir(skill_name), "SKILL.md")
    except ValueError as e:
        obs.warn("skill_revision_refused", skill=str(skill_name)[:40], detail=str(e))
        return {"ok": False, "detail": str(e)}
    draft = path + ".v2-draft"
    if not os.path.isfile(draft):
        return {"ok": False, "detail": "taslak yok"}
    n = 1
    while os.path.exists(f"{path}.v{n}.bak"):
        n += 1
    os.replace(path, f"{path}.v{n}.bak")
    os.replace(draft, path)
    recs = revisions()
    for r in recs:
        if r.get("skill") == skill_name and r.get("status") == "draft":
            r["status"] = "applied"
            r["applied_at"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
            r["archived_as"] = f"SKILL.md.v{n}.bak"
    _write_revisions(recs)
    obs.log("skill_revision_applied", skill=skill_name, archived=f"v{n}.bak")
    return {"ok": True, "archived": f"SKILL.md.v{n}.bak"}


def reject_revision(skill_name: str) -> dict:
    try:
        path = os.path.join(_repo_skill_dir(skill_name), "SKILL.md.v2-draft")
    except ValueError as e:
        return {"ok": False, "detail": str(e)}
    if os.path.isfile(path):
        os.unlink(path)
    recs = revisions()
    for r in recs:
        if r.get("skill") == skill_name and r.get("status") == "draft":
            r["status"] = "rejected"
    _write_revisions(recs)
    obs.log("skill_revision_rejected", skill=skill_name)
    return {"ok": True}
