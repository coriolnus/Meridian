#!/usr/bin/env bash
# hafiza_sor.sh — Hindsight arşiv bankasına LLM'siz recall (Rol-1 aktif kullanım, operatör 2026-09-06).
# Kullanım: hafiza_sor.sh "<soru>" [k=5] [bank=meridian-arsiv] [butce=mid]  (butce: low|mid|high — rerank aday sayısını belirler)
# Anahtar YALNIZ Authorization başlığında; çıktıda anahtar/URL parametresi yok.
#
# DEPOYA ALINDI 2026-09-25 (TSK-222, EDG-2026-103 ADIM-0 (b)) — `sayfa_oku.sh` ile aynı gerekçe ve
# aynı kurulum: `ln -sfn /opt/meridian/deploy/hindsight/hafiza_sor.sh ~/bin/hafiza_sor.sh`.
# DAVRANIŞ A1 KOPYASIYLA AYNI (0 sonuç basıldı · 1 soru yok/anahtar yok · 2 RECALL HATASI). Tek
# ekleme OKUMA KAYDI (`hafiza_okuma_kaydi.py`): soru METNİ kayda YAZILMAZ, sha256'sı yazılır —
# gerekçe modül başlığında. Ortam ezmeleri (`HAFIZA_PORT`, `HAFIZA_ANAHTAR_DOSYASI`) ve anlamları
# `sayfa_oku.sh` başlığındakiyle aynıdır.
#
# ANAHTAR SÜREÇ ARGV'SİNDE DURMAZ (TSK-064, 2026-09-25) — gerekçe ve sözleşme `sayfa_oku.sh`
# başlığında: bash anahtara dokunmaz, gömülü Python dosyayı kendisi okur (recall ~38 sn sürer; eskiden
# anahtar o süre boyunca `ps`te görünüyordu). Anahtar dosyası okunamazsa çıkış 1 (eskisi gibi), istek
# gitmez, kayıt yazılmaz; stderr'e tek satır (hata türü + yol) — eskiden `cat:` satırıydı. Sondaki
# CR/LF kırpılır; `RECALL HATASI` satırı ve her hata metni `arindir()`dan geçer — eskiden CR'lı bir
# anahtar dosyası anahtarı bu satırla STDOUT'a basıyordu (tur 2).
set -euo pipefail
SORU="${1:?soru gerekli}"; K="${2:-5}"; BANK="${3:-meridian-arsiv}"; BUTCE="${4:-mid}"
PORT="${HAFIZA_PORT:-8888}"
case "$PORT" in ''|*[!0-9]*) echo "HAFIZA_PORT yalnız rakam olabilir" >&2; exit 1;; esac
BASE="http://127.0.0.1:${PORT}/v1/default"
HAFIZA_BETIK="${BASH_SOURCE[0]}" python3 - "$SORU" "$K" "$BANK" "$BASE" "$BUTCE" <<'PY'
import sys, json, time, urllib.request
# >>> anahtar (TSK-064) — argv'de/ortamda DURMAZ, hiçbir çıktı kanalına BASILMAZ; dosyayı bu süreç okur
import os, pathlib
key = ""
def arindir(metin):
    """Basılacak hata metninden anahtarı `<anahtar>` ile değiştirir: ham, str-repr ve başlığın bayt-repr
    biçimi (http.client'ın geçersiz başlık hatası değeri `b'Bearer …'` diye basar)."""
    m = str(metin)
    if key:
        for bicim in (key, repr(key)[1:-1], repr(key.encode("latin-1", "backslashreplace"))[2:-1]):
            m = m.replace(bicim, "<anahtar>")
    return m
# yakalanmamış istisna ham traceback BASMAZ (mesajı anahtarı taşıyabilir): tür + arındırılmış mesaj, çıkış 1
sys.excepthook = lambda tur, deger, iz: print(f"{tur.__name__}: {arindir(deger)}", file=sys.stderr)
try:
    key = os.fsdecode(pathlib.Path(os.environ.get("HAFIZA_ANAHTAR_DOSYASI") or "/opt/hindsight/.key").read_bytes().rstrip(b"\r\n"))
except OSError as e:  # sessiz-yutma değil: hata türü + yol stderr'e, çıkış 1, istek GİTMEZ
    print(f"HAFIZA ANAHTARI OKUNAMADI: {type(e).__name__}: {arindir(e)}", file=sys.stderr); sys.exit(1)
# <<< anahtar
soru, k, bank, base, butce = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4], sys.argv[5]
# >>> okuma kaydı (EDG-2026-103 · TSK-222) — okuma işlevi bu bloğa BAĞLI DEĞİL
import os
T0 = time.time()
try:
    sys.dont_write_bytecode = True
    sys.path.insert(0, os.path.dirname(os.path.realpath(os.environ["HAFIZA_BETIK"])))
    import hafiza_okuma_kaydi as OKUMA
except Exception as e:  # sessiz-yutma değil: uyarı basılır, okuma kayıtsız sürer
    OKUMA = None
    print(f"UYARI: okuma kaydı modülü yüklenemedi ({type(e).__name__}) — bu okuma KAYDEDİLMEYECEK", file=sys.stderr)
def kaydet(**alan):
    if OKUMA is not None:
        OKUMA.yaz(betik="hafiza_sor", kip="recall", kimlik_metni=soru, bank=bank, butce=butce,
                  sure_s=time.time() - T0, **alan)
# <<< okuma kaydı
body = json.dumps({"query": soru, "budget": butce}, ensure_ascii=False).encode()  # `limit` API'ce tanınmıyor (2026-09-01 ölçümü)
req = urllib.request.Request(f"{base}/banks/{bank}/memories/recall", data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
t0 = time.time(); http = None
try:
    with urllib.request.urlopen(req, timeout=360) as r:
        ham = r.read(); http = r.status
        d = json.loads(ham)
except Exception as e:  # sessiz-yutma değil: hata türü+mesaj basılır, çıkış 2
    kaydet(durum="hata", hata=type(e).__name__, http=getattr(e, "code", http))
    print(f"RECALL HATASI: {type(e).__name__}: {arindir(e)[:200]}"); sys.exit(2)  # arındır, SONRA kes: kesim anahtarı yarıda bırakmasın
sure = time.time() - t0
res = d if isinstance(d, list) else next((d[a] for a in ("items","results","memories","data") if a in d), [])
kaydet(http=http, govde=ham, sonuc_n=len(res))  # basmadan ÖNCE: `| head` EPIPE'ı kaydı düşürmesin
print(f"# recall · bank={bank} · butce={butce} · k={k} · {sure:.1f} s · sonuç {len(res)}")
for i, r in enumerate(res[:k], 1):
    sc = r.get("scores") or {}
    skor = sc.get("final") or sc.get("score") or sc.get("rerank") or ""
    print(f"\n[{i}] {r.get('document_id','?')} · {r.get('type','?')} · {r.get('occurred_start') or r.get('mentioned_at') or ''} · skor={skor}")
    print("    " + (r.get("text") or "").replace("\n", " ")[:600])
PY
