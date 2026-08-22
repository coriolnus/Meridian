"""WP7/24b · SOUL KİLİDİ SINAMASI — CANLI HAM KANIT ÇEKİMİ (SALT-OKUMA).

Kart: EDG-2026-019 (skill görüş defteri) — bu çekim kartın ÖN-KOŞUL sorusunu ölçer:
"SOUL kilidi 2026-08-13'te açıldı (bc16f26) ama HİÇ SINANMADI — skill çağrı oranı
%1,1'den ne oldu?" (taban: docs/DENETIM-SKILL-CAGRI-IZI-2026-08-13.md — 1.113 oturumda
12 skill-araç çağrısı; docs/OLCUM-WP7-24B-SKILL-CAGRI-IZI-2026-08-14.md — düzeltme
kesintinin içine indi, v244'e dek model erişilemezdi).

KOŞUM (yereldeki oturumdan, stdin deseni — canlıya DOSYA YAZILMAZ; emsal: exe007):
    ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 \
        'cd /opt/meridian && ./.venv/bin/python -' \
        < research/olcumler/edg019_24b_sinama_2026-08-22/canli_cek.py \
        > research/olcumler/edg019_24b_sinama_2026-08-22/sonuc.json

NE ÖLÇER (hepsi ~/.hermes altından, YALNIZ okuma):
  (1) SOUL.md kablosu: sha256 + mtime + kilidi açan cümle ("ANALİZ SIRASINDA ARAÇ
      KULLANMAK SERBEST") canlı dosyada duruyor mu; yedekler listesi.
  (2) agent.log{,.1,.2,.3}: `agent.tool_executor: tool <ad> <durum>` satırları +
      `[YYYYMMDD_HHMMSS_hex]` oturum kimlikleri. ÜÇ PENCERE (donuk, betiğe gömülü):
        taban_once : ts <  2026-08-13 18:17  (SOUL kurulumundan önce — denetim tabanıyla
                     kıyas; log rotasyonu nedeniyle KISMİ, beyan edilir)
        golge      : 18:17 <= ts < 2026-08-15 00:00  (kesinti penceresi: 550×404,
                     OpenRouter v244 gecenin sonunda — bu kova hükme ESAS DEĞİL)
        temiz      : ts >= 2026-08-15 00:00  (düzeltme + erişilebilir model — SINAMA BU)
      Pencere başına: benzersiz oturum n · araç çağrısı dağılımı · skill-araç
      (skill_view+skills_list) n · oran = skill-araç / oturum (taban tanımıyla AYNI payda).
  (3) ~/.hermes/skills/.usage.json: view_count/last_viewed_at (çapraz doğrulama —
      log hedef skill ADI taşımıyor, hedefler yalnız buradan görünür).
  (4) ~/.hermes/sessions/request_dump_* gün sayımı (hata profili: kesinti bitti mi).

UYDURMA YASAĞI: okunamayan kalem null + `_hata`/`_neden` ile döner. Eşik/karar YOK —
bu betik sayı getirir, hükmü Rol-1 işler. Saat dilimi: log ts'leri sunucu yerelidir;
sunucunun utc_offset'i çıktıya yazılır (pencere sınırları sunucu-yerel okunur; SOUL
mtime 18:17 ile yedek adı 202608131817 [deploy.sh `date -u`] aynı — sunucu UTC beklenir,
yine de ölçülür, varsayılmaz).
"""
import datetime as dt
import hashlib
import json
import os
import re
import time
from collections import Counter
from pathlib import Path

H = Path.home() / ".hermes"
SINIR1 = "2026-08-13 18:17:00"   # SOUL.md kurulumu (mtime + .bak-202608131817)
SINIR2 = "2026-08-15 00:00:00"   # v244 (OpenRouter) sonrası temiz pencere başı — muhafazakâr
KILIT_ACIK_CUMLE = "ANALİZ SIRASINDA ARAÇ KULLANMAK SERBEST"

OUT: dict = {
    "kalem": "WP7-24b SOUL kilidi sinamasi",
    "kart": "EDG-2026-019 (on-kosul olcumu)",
    "cekim_zamani_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
    "sunucu_utc_offset_s": -time.timezone if not time.daylight else -time.altzone,
    "sunucu_tzname": list(time.tzname),
    "pencere_sinirlari_sunucu_yerel": {"SINIR1_soul_kurulumu": SINIR1,
                                       "SINIR2_temiz_pencere": SINIR2},
}

# ---------- (1) SOUL.md kablosu ----------
try:
    p = H / "SOUL.md"
    metin = p.read_text(encoding="utf-8")
    OUT["soul"] = {
        "yol": str(p),
        "sha256": hashlib.sha256(metin.encode()).hexdigest(),
        "bayt": p.stat().st_size,
        "mtime_sunucu_yerel": dt.datetime.fromtimestamp(p.stat().st_mtime).isoformat(timespec="seconds"),
        "kilit_acik_cumle_var": KILIT_ACIK_CUMLE in metin,
        "eski_yasak_cumle_var": ("araç çağrısı" in metin.lower()
                                 and "yok" in metin.lower() and KILIT_ACIK_CUMLE not in metin),
        "yedekler": sorted(f.name for f in H.glob("SOUL.md.*")),
    }
except Exception as e:
    OUT["soul"] = {"sha256": None, "_hata": f"{type(e).__name__}: {e}"}

# ---------- (2) agent.log ailesi ----------
TS_RE = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})")
SID_RE = re.compile(r"\[(\d{8}_\d{6}_[0-9a-f]{6})\]")
TOOL_RE = re.compile(r"agent\.tool_executor: tool (\S+) (\w+)")
SKILL_ARACLAR = {"skill_view", "skills_list"}


def kova(ts: str) -> str:
    if ts < SINIR1:
        return "taban_once"
    if ts < SINIR2:
        return "golge"
    return "temiz"


try:
    log_dosyalari = sorted(H.glob("logs/agent.log*"),
                           key=lambda f: f.stat().st_mtime)  # eski -> yeni
    oturum_ilk_ts: dict = {}          # sid -> ilk görülme ts
    arac_satirlari: list = []         # (ts, sid|None, tool, durum)
    dosya_kapsami: dict = {}
    for f in log_dosyalari:
        ilk, son, n = None, None, 0
        with open(f, encoding="utf-8", errors="replace") as fh:
            for satir in fh:
                n += 1
                m = TS_RE.match(satir)
                if not m:
                    continue
                ts = m.group(1)
                ilk = ilk or ts
                son = ts
                sm = SID_RE.search(satir)
                sid = sm.group(1) if sm else None
                if sid is not None and sid not in oturum_ilk_ts:
                    oturum_ilk_ts[sid] = ts
                tm = TOOL_RE.search(satir)
                if tm:
                    arac_satirlari.append((ts, sid, tm.group(1), tm.group(2)))
        dosya_kapsami[f.name] = {"satir_n": n, "ilk_ts": ilk, "son_ts": son}
    OUT["agent_log"] = {"dosyalar": dosya_kapsami}

    pencereler: dict = {}
    for ad in ("taban_once", "golge", "temiz"):
        sids = {s for s, ts in oturum_ilk_ts.items() if kova(ts) == ad}
        satirlar = [r for r in arac_satirlari if kova(r[0]) == ad]
        arac_sayimi = Counter(r[2] for r in satirlar)
        skill_satirlari = [r for r in satirlar if r[2] in SKILL_ARACLAR]
        n_oturum = len(sids)
        n_skill = len(skill_satirlari)
        pencereler[ad] = {
            "n_oturum": n_oturum,
            "n_arac_cagrisi": len(satirlar),
            "arac_dagilimi": dict(arac_sayimi.most_common()),
            "n_skill_arac": n_skill,
            "skill_arac_oturum_n": len({r[1] for r in skill_satirlari if r[1]}),
            "oran_skill_arac_bolu_oturum_pct": (round(100.0 * n_skill / n_oturum, 2)
                                                if n_oturum else None),
            "durum_dagilimi": dict(Counter(r[3] for r in satirlar).most_common()),
        }
    OUT["pencereler"] = pencereler
    # temiz penceredeki skill-araç çağrıları TEK TEK (kanıt satırları)
    OUT["temiz_skill_arac_cagrilari"] = [
        {"ts": r[0], "oturum": r[1], "arac": r[2], "durum": r[3]}
        for r in arac_satirlari if r[2] in SKILL_ARACLAR and kova(r[0]) == "temiz"]
    OUT["golge_skill_arac_cagrilari"] = [
        {"ts": r[0], "oturum": r[1], "arac": r[2], "durum": r[3]}
        for r in arac_satirlari if r[2] in SKILL_ARACLAR and kova(r[0]) == "golge"]
except Exception as e:
    OUT["agent_log"] = {"_hata": f"{type(e).__name__}: {e}"}
    OUT["pencereler"] = None

# ---------- (3) .usage.json çaprazı ----------
try:
    u = json.loads((H / "skills" / ".usage.json").read_text(encoding="utf-8"))
    ozet = {}
    for ad, kayit in (u.items() if isinstance(u, dict) else []):
        if not isinstance(kayit, dict):
            continue
        vc = kayit.get("view_count")
        lv = kayit.get("last_viewed_at")
        if vc or lv:
            ozet[ad] = {"view_count": vc, "last_viewed_at": lv,
                        "inject_count": kayit.get("inject_count"),
                        "last_injected_at": kayit.get("last_injected_at")}
    OUT["usage_json"] = {"goruntulenen_skiller": ozet,
                         "toplam_view_count": sum((k.get("view_count") or 0)
                                                  for k in ozet.values())}
except Exception as e:
    OUT["usage_json"] = {"goruntulenen_skiller": None, "_hata": f"{type(e).__name__}: {e}"}

# ---------- (4) request_dump gün profili ----------
try:
    gun = Counter()
    for f in (H / "sessions").glob("request_dump_*.json"):
        m = re.match(r"request_dump_(\d{8})_", f.name)
        if m:
            gun[m.group(1)] += 1
    OUT["request_dump_gun_sayimi"] = dict(sorted(gun.items()))
except Exception as e:
    OUT["request_dump_gun_sayimi"] = {"_hata": f"{type(e).__name__}: {e}"}

print(json.dumps(OUT, ensure_ascii=False, indent=1))
