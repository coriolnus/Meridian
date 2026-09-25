#!/usr/bin/env bash
# sayfa_oku.sh — Hindsight zihin modeli sayfasını LLM'siz okur (Rol-1 aktif kullanım; EDG-083 okuyucu).
# Kullanım: sayfa_oku.sh            → sayfaları listeler (id · ad · sürüm · son tazeleme)
#           sayfa_oku.sh <ad|id>    → sayfa içeriğini basar
#
# DEPOYA ALINDI 2026-09-25 (TSK-222, EDG-2026-103 ADIM-0 (b)). O güne dek yalnız A1 `~/bin`de,
# sürümsüz yaşıyordu; CLAUDE.md §0 adım 5 ve §2 ona atıf yapıyor. A1 kurulumu `hafiza_ara.sh`
# emsali: `ln -sfn /opt/meridian/deploy/hindsight/sayfa_oku.sh ~/bin/sayfa_oku.sh` — KOPYA
# DEĞİL sembolik bağ; kayıt modülü (`hafiza_okuma_kaydi.py`) bu dosyanın GERÇEK yolunun yanında
# aranır, kopya kurulursa okuma yine çıkar ama kaydedilmediği stderr'e yazılır.
#
# DAVRANIŞ A1 KOPYASIYLA AYNI: çıktı biçimi, argümanlar, çıkış kodları birebir
# (0 okundu · 1 anahtar/HTTP/bağlantı hatası (traceback) · 2 BULUNAMADI). Tek ekleme OKUMA KAYDI:
# her çağrı `HAFIZA_OKUMA_KAYDI` (varsayılan /opt/veri/olcum/edg103/okuma.jsonl) dosyasına TEK
# JSON satırı ekler — alanlar, yer tutucu kuralı ve okuyucusu (EDG-2026-103) modül başlığında.
# Kayıt yazılamazsa okuma yine çıkar, uyarı stderr'e gider. Kayıt çıktı BASILMADAN önce yazılır:
# `| head` ile kısaltılan uzun bir sayfada print EPIPE'la düşer ve sonra yazılan kayıt kaybolurdu.
#
# ORTAMDAN EZİLEBİLEN İKİ DEĞER (varsayılanlar A1'in değerleri; çivi v547 sahte sunucuyla koşar):
#   HAFIZA_PORT             (8888) — ana bilgisayar SABİT 127.0.0.1: anahtar makineden çıkamaz;
#                           yalnız rakam kabul edilir (`8888@baska.host` ana bilgisayarı değiştirirdi)
#   HAFIZA_ANAHTAR_DOSYASI  (/opt/hindsight/.key)
set -euo pipefail
PORT="${HAFIZA_PORT:-8888}"
case "$PORT" in ''|*[!0-9]*) echo "HAFIZA_PORT yalnız rakam olabilir" >&2; exit 1;; esac
KEY=$(cat "${HAFIZA_ANAHTAR_DOSYASI:-/opt/hindsight/.key}"); BASE="http://127.0.0.1:${PORT}/v1/default/banks/meridian-arsiv"
HAFIZA_BETIK="${BASH_SOURCE[0]}" python3 - "${1:-}" "$KEY" "$BASE" <<'PY'
import sys, json, urllib.request
ad, key, base = sys.argv[1], sys.argv[2], sys.argv[3]
# >>> okuma kaydı (EDG-2026-103 · TSK-222) — okuma işlevi bu bloğa BAĞLI DEĞİL
import os, time
T0 = time.time(); SON = {"http": None, "govde": None}
try:
    sys.dont_write_bytecode = True
    sys.path.insert(0, os.path.dirname(os.path.realpath(os.environ["HAFIZA_BETIK"])))
    import hafiza_okuma_kaydi as OKUMA
except Exception as e:  # sessiz-yutma değil: uyarı basılır, okuma kayıtsız sürer
    OKUMA = None
    print(f"UYARI: okuma kaydı modülü yüklenemedi ({type(e).__name__}) — bu okuma KAYDEDİLMEYECEK", file=sys.stderr)
def kaydet(**alan):
    if OKUMA is not None:
        OKUMA.yaz(betik="sayfa_oku", sure_s=time.time() - T0, **alan)
def kaydet_hata(e, **alan):
    kaydet(durum="hata", hata=type(e).__name__, http=getattr(e, "code", SON["http"]), **alan)
# <<< okuma kaydı
def get(u):
    r = urllib.request.Request(u, headers={"Authorization": f"Bearer {key}"})
    SON["http"] = SON["govde"] = None
    with urllib.request.urlopen(r, timeout=60) as x:
        SON["govde"] = x.read(); SON["http"] = x.status
        return json.loads(SON["govde"])
try:
    d = get(f"{base}/mental-models")
except Exception as e:
    kaydet_hata(e, kip="sayfa" if ad else "liste"); raise
items = d if isinstance(d, list) else next((d[k] for k in ("items","mental_models","models","data") if k in d), [])
if not ad:
    kaydet(kip="liste", http=SON["http"], govde=SON["govde"], sonuc_n=len(items))  # basmadan ÖNCE: `| head` EPIPE'ı kaydı düşürmesin
    print(f"# zihin modelleri: {len(items)}")
    for m in items:
        print(f"- {m.get('id')} · {m.get('name')} · v{m.get('version', m.get('current_version','?'))} · {m.get('last_refreshed_at') or m.get('updated_at') or ''}")
    sys.exit(0)
m = next((m for m in items if ad in (m.get("id"), m.get("name"))), None)
if not m:
    kaydet(kip="sayfa", kimlik_metni=ad, http=SON["http"], durum="bulunamadi"); print(f"BULUNAMADI: {ad}"); sys.exit(2)
try:
    full = get(f"{base}/mental-models/{m['id']}")
except Exception as e:
    kaydet_hata(e, kip="sayfa", kimlik=m.get("id"), ad=m.get("name")); raise
icerik = full.get("content") or full.get("text") or full.get("body") or ""
kaydet(kip="sayfa", kimlik=full.get("id"), ad=full.get("name"), tazeleme=full.get("last_refreshed_at"),
       http=SON["http"], icerik=icerik)  # basmadan ÖNCE (liste dalındaki gerekçe)
print(f"# {full.get('name')} · id={full.get('id')} · v{full.get('version','?')} · tazeleme={full.get('last_refreshed_at') or ''}")
print(icerik if icerik else "(içerik boş) alanlar: " + ", ".join(full.keys()))
PY
