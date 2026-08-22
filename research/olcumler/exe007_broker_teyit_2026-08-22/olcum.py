"""EXE-2026-007 · broker-teyitli defter — ÖLÇÜM (kart: research/cards/EXE-2026-007-broker-teyitli-defter.yaml, SALT-OKUNUR).

NE ÖLÇER (eşleşme kuralı KARTTA DONUK, burada yalnız uygulanır):
  Her reset-sonrası canlı defter satırı için ÜÇ DEĞERLİ teyit alanı:
    broker_teyitli     — (ticker, ts_open..ts_close aralığında ≥1 FILL)
    broker_karsiliksiz — aralıkta o ticker için HİÇ FILL yok
    olculemedi         — satır 2026-07-14 (Alpaca aktivite penceresinin başı) ÖNCESİNE taşıyor
                         YA DA broker geçmişi okunamadı → teyitli/karşılıksız'a KATILMAZ
  Miktar/fiyat eşleşmesi ARANMAZ (kart: "var mı yok mu", "doğru mu" değil).

GİRDİLER:
  (1) canli_ham.json — A1'den ssh-stdin deseniyle çekilmiş canlı kanıt (canli_cek.py; SALT-OKUMA).
      İçinde: trades.jsonl'ın TAMAMI (indeksli kıyas için) + hermes_status.json'ın
      `last_reflect_at` tabanı (Ö3'ün kaynağı — hermes_runtime._restored_baseline bu alanı okur).
  (2) Alpaca aktivite defteri — meridian.adapters.alpaca._paper_base()+_headers() ile httpx GET,
      TAM SAYFALAMA: page_size=100 (>100 yanıtı SÖZLÜĞE çevirir — kill kriteri; yanıt tipi her
      sayfada denetlenir), page_token=son kaydın id'si, after=2026-07-14T00:00:00Z.

TARİH GRANÜLERLİĞİ (beyanlı): defter ts_open/ts_close ÇIPLAK TARİH taşır (örn. "2026-08-07");
fill `transaction_time` UTC ISO'dur. Kıyas GÜN düzeyinde: transaction_time[:10] (UTC günü)
ts_open..ts_close aralığına (iki uç DAHİL) düşerse eşleşir. Normal seans dolumları (13:30–20:00
UTC) UTC gününde piyasa gününe eşittir; bu varsayım beyanlıdır, gizli değildir.

YAZMA GÜVENLİĞİ: sözleşme gereği state/ dizinine YAZILMAZ. Yapısal koruma: bu süreçte
meridian.store'un yazım fonksiyonları SAYAÇLI no-op'a bağlanır (obs.warn'ın events.jsonl
aynalaması dahil hiçbir kütüphane yan etkisi state'e satır düşüremez); denenen yazım sayısı
sonuc.json'a olgu olarak yazılır. Tek yazım hedefi: bu ölçüm dizini.

UYDURMA YASAĞI: ölçülemeyen her kalem None + neden (`olculemedi_nedenleri`).
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import sys

DIZIN = os.path.dirname(os.path.abspath(__file__))
CANLI_HAM = os.path.join(DIZIN, "canli_ham.json")
BROKER_HAM = os.path.join(DIZIN, "broker_ham.json")
SONUC = os.path.join(DIZIN, "sonuc.json")

RESET = "2026-08-01"                 # kart: 2026-08-01 reset'i sonrası pencere
AKTIVITE_BASI = "2026-07-14"         # Alpaca aktivite penceresinin ölçülmüş başı (kart beyanlı sınır 2)
AFTER = "2026-07-14T00:00:00Z"       # tam ISO gerekir — çıplak tarih boş döndürür (brief)
PAGE_SIZE = 100                      # >100 = yanıt sözlüğe döner (kill kriteri) — SABİT

# ---------------------------------------------------------------- yazma kilidi (yapısal)
_yazim_denemeleri: list[str] = []


def _yazim_kilidi() -> None:
    """meridian.store'un yazım yüzeyini süreç-içi no-op'a bağlar; denemeler olgu olarak sayılır."""
    from meridian import store as _store

    def _engelle(ad):
        def _f(*a, **k):
            _yazim_denemeleri.append(f"{ad}({a[0] if a else '?'})")
            return None
        return _f

    for ad in ("append_jsonl", "write_json", "write_yaml", "write_text"):
        if hasattr(_store, ad):
            setattr(_store, ad, _engelle(ad))


def _sha16(path: str) -> str | None:
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()[:16]
    except Exception:
        return None


# ---------------------------------------------------------------- (1) canlı kanıt
def canli_yukle() -> dict:
    with open(CANLI_HAM) as f:
        return json.load(f)


# ---------------------------------------------------------------- (2) broker aktiviteleri
def broker_cek() -> dict:
    """/v2/account/activities — TAM SAYFALAMA, SALT-OKUNUR GET. Dönüş:
    {"ok": bool, "aktiviteler": [...] | None, "sayfa_n": int, "_hata": str | None}"""
    import httpx
    from meridian.adapters import alpaca

    base = alpaca._paper_base()
    headers = alpaca._headers()
    url = f"{base}/v2/account/activities"
    aktiviteler: list[dict] = []
    page_token: str | None = None
    sayfa_n = 0
    while True:
        params: dict = {"after": AFTER, "page_size": PAGE_SIZE, "direction": "asc"}
        if page_token:
            params["page_token"] = page_token
        r = httpx.get(url, headers=headers, params=params, timeout=30)
        if r.status_code != 200:
            return {"ok": False, "aktiviteler": None, "sayfa_n": sayfa_n,
                    "_hata": f"HTTP {r.status_code}: {r.text[:200]}"}
        sayfa = r.json()
        if not isinstance(sayfa, list):
            # bilinen tuzak (kill kriteri): sözlük yanıt = sayfalama sözleşmesi bozuldu → ölçülemedi
            return {"ok": False, "aktiviteler": None, "sayfa_n": sayfa_n,
                    "_hata": f"yanıt liste değil {type(sayfa).__name__} — sayfalama sözleşmesi bozuldu"}
        sayfa_n += 1
        aktiviteler.extend(sayfa)
        if len(sayfa) < PAGE_SIZE:
            break
        page_token = str(sayfa[-1].get("id"))
        if not page_token or page_token == "None":
            return {"ok": False, "aktiviteler": None, "sayfa_n": sayfa_n,
                    "_hata": "son kaydın id'si yok — sayfalama süremez, TAM sayfalama garanti edilemez"}
    return {"ok": True, "aktiviteler": aktiviteler, "sayfa_n": sayfa_n, "_hata": None}


# ---------------------------------------------------------------- (3) kovalama (kural KARTTA DONUK)
def kovala(satir: dict, filller: list[dict], broker_ok: bool) -> tuple[str, list[dict], str | None]:
    """Dönüş: (kova, eşleşen filller, olculemedi_nedeni)."""
    ts_open = str(satir.get("ts_open") or "")[:10]
    ts_close = str(satir.get("ts_close") or "")[:10]
    if not broker_ok:
        return "olculemedi", [], "broker geçmişi okunamadı"
    if not ts_open or not ts_close:
        return "olculemedi", [], "satırda ts_open/ts_close yok — aralık kurulamaz"
    if ts_open < AKTIVITE_BASI:
        return "olculemedi", [], f"satır {AKTIVITE_BASI} öncesine taşıyor (aktivite penceresi dışı)"
    tik = satir.get("ticker")
    es = [f for f in filller
          if f.get("symbol") == tik and ts_open <= str(f.get("transaction_time") or "")[:10] <= ts_close]
    return ("broker_teyitli" if es else "broker_karsiliksiz"), es, None


def main() -> None:
    _yazim_kilidi()

    canli = canli_yukle()
    trades = (canli.get("trades") or {}).get("satirlar")
    if trades is None:
        raise SystemExit(f"canli_ham.json'da trades yok: {canli.get('trades')}")
    defter_n = len(trades)
    hs = canli.get("hermes_status") or {}
    taban = hs.get("last_reflect_at")

    broker = broker_cek()
    aktiviteler = broker["aktiviteler"] or []
    with open(BROKER_HAM, "w") as f:
        json.dump({"cekim_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                   "after": AFTER, "page_size": PAGE_SIZE, "sayfa_n": broker["sayfa_n"],
                   "ok": broker["ok"], "_hata": broker["_hata"],
                   "n": len(aktiviteler) if broker["ok"] else None,
                   "aktiviteler": aktiviteler if broker["ok"] else None}, f, indent=1)
    filller = [a for a in aktiviteler if a.get("activity_type") == "FILL"]

    # reset-sonrası pencere + tohum ayrımı (kill kriteri: replay_seed kıyasa GİRMEZ)
    reset_sonrasi = [(i, t) for i, t in enumerate(trades) if str(t.get("ts_close") or "")[:10] >= RESET]
    tohum = [(i, t) for i, t in reset_sonrasi if t.get("kaynak") == "replay_seed"]
    kiyas = [(i, t) for i, t in reset_sonrasi if t.get("kaynak") != "replay_seed"]

    dokum: list[dict] = []
    olculemedi_nedenleri: list[dict] = []
    kova_sayilari = {"broker_teyitli": 0, "broker_karsiliksiz": 0, "olculemedi": 0,
                     "tohum_kiyas_disi": len(tohum)}
    karsiliksiz: list[tuple[int, dict]] = []

    for i, t in kiyas:
        kova, es, neden = kovala(t, filller, broker["ok"])
        kova_sayilari[kova] += 1
        if kova == "broker_karsiliksiz":
            karsiliksiz.append((i, t))
        if neden:
            olculemedi_nedenleri.append({"indeks": i, "id": t.get("id"), "neden": neden})
        dokum.append({"indeks": i, "id": t.get("id"), "ticker": t.get("ticker"),
                      "ts_open": t.get("ts_open"), "ts_close": t.get("ts_close"),
                      "kaynak": t.get("kaynak"), "pnl_dollars": t.get("pnl_dollars"),
                      "plan_id": t.get("plan_id"), "kova": kova,
                      "eslesen_fill_n": len(es),
                      "eslesen_fill_zamanlari": [f.get("transaction_time") for f in es][:12]})
    for i, t in tohum:
        dokum.append({"indeks": i, "id": t.get("id"), "ticker": t.get("ticker"),
                      "ts_open": t.get("ts_open"), "ts_close": t.get("ts_close"),
                      "kaynak": t.get("kaynak"), "pnl_dollars": t.get("pnl_dollars"),
                      "plan_id": t.get("plan_id"), "kova": "tohum_kiyas_disi",
                      "eslesen_fill_n": None, "eslesen_fill_zamanlari": None})
    dokum.sort(key=lambda d: d["indeks"])

    # ---- Ö1: karşılıksız oran (payda = kıyasa giren reset-sonrası satır; tohum HARİÇ) ----
    kiyas_n = len(kiyas)
    kars_n = kova_sayilari["broker_karsiliksiz"]
    O1 = {"pay_karsiliksiz": kars_n, "payda_reset_sonrasi_kiyas": kiyas_n,
          "oran": (kars_n / kiyas_n) if kiyas_n else None,
          "not": "payda tohum (replay_seed) HARİÇ reset-sonrası satır; olculemedi kovası pay'a da "
                 "payda-düşümüne de sessizce KATILMADI (sayısı kova_sayilari'nda açık)"}

    # ---- Ö2: karşılıksız satırların pnl_dollars toplamı ----
    pnl_eksik = [t.get("id") for _, t in karsiliksiz if t.get("pnl_dollars") is None]
    O2 = {"toplam_pnl_dollars": round(sum(float(t["pnl_dollars"]) for _, t in karsiliksiz
                                          if t.get("pnl_dollars") is not None), 2) if karsiliksiz else 0.0,
          "satirlar": [{"id": t.get("id"), "ticker": t.get("ticker"),
                        "pnl_dollars": t.get("pnl_dollars")} for _, t in karsiliksiz],
          "pnl_olculemeyen": pnl_eksik or None}

    # ---- Ö3: yansıma tabanı vs karşılıksız indeksler ----
    # Taban kaynağı: hermes_status.json `last_reflect_at` — _horizon_ok'un `trades[last_at:]`
    # dilimini kuran değer; kalıcı hali hermes_runtime._restored_baseline'ın okuduğu STATUS_FILE.
    k_idx = [i for i, _ in karsiliksiz]
    if taban is None:
        O3 = {"taban": None, "olculemedi_nedeni": "hermes_status.json'da last_reflect_at yok/okunamadı"}
    else:
        taban_i = int(taban)
        sonra = [d for d in dokum if d["indeks"] >= taban_i and d["kova"] != "tohum_kiyas_disi"]
        O3 = {"taban_last_reflect_at": taban_i,
              "defter_n": defter_n,
              "tabandan_sonraki_satir_n": defter_n - taban_i,
              "tabandan_sonraki_karsiliksiz_n": sum(1 for d in sonra if d["kova"] == "broker_karsiliksiz"),
              "karsiliksiz_indeksler": k_idx,
              "hepsi_taban_altinda": all(i < taban_i for i in k_idx) if k_idx else None,
              "yansima_sayisi": hs.get("reflections"),
              "son_yansima": hs.get("last_reflection"),
              "gecmis_yansima_penceresine_giren_karsiliksiz_n":
                  sum(1 for i in k_idx if i < taban_i),
              "not": "kart Ö3 sorusu: karşılıksız satırlar _horizon_ok'un saydığı işlemlere giriyor mu? "
                     "Sayılar yukarıda; hüküm Rol-1'in."}

    # ---- ön-ölçüm kıyası (kart: koşum ön-ölçümü YENİDEN üretmeli) ----
    on = {"O1": "2/8 = 0.25", "O2": 277.99, "karsiliksiz_idler": ["T00096 (ALL)", "T00097 (VLO)"],
          "defter": 893, "taban": 887, "karsiliksiz_indeksler": [885, 886]}
    kiyas_on = {"beklenen": on,
                "olculen": {"O1": f"{kars_n}/{kiyas_n}", "O2": O2["toplam_pnl_dollars"],
                            "karsiliksiz_idler": [f"{t.get('id')} ({t.get('ticker')})" for _, t in karsiliksiz],
                            "defter": defter_n, "taban": taban, "karsiliksiz_indeksler": k_idx},
                "tutarli": (kars_n == 2 and kiyas_n == 8 and defter_n == 893 and taban == 887
                            and k_idx == [885, 886]
                            and abs((O2["toplam_pnl_dollars"] or 0) - 277.99) < 0.01)}

    sonuc = {"kart": "EXE-2026-007",
             "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
             "girdiler": {"canli_ham": {"dosya": "canli_ham.json", "sha256_16": _sha16(CANLI_HAM),
                                        "cekim_zamani": canli.get("cekim_zamani"),
                                        "defter_n": defter_n},
                          "broker": {"dosya": "broker_ham.json", "ok": broker["ok"],
                                     "_hata": broker["_hata"], "sayfa_n": broker["sayfa_n"],
                                     "aktivite_n": len(aktiviteler) if broker["ok"] else None,
                                     "fill_n": len(filller) if broker["ok"] else None,
                                     "en_eski_aktivite": (min((str(a.get("transaction_time") or a.get("date") or "")
                                                               for a in aktiviteler), default=None)
                                                          if broker["ok"] else None)}},
             "pencere": {"reset": RESET, "aktivite_basi": AKTIVITE_BASI,
                         "reset_sonrasi_toplam": len(reset_sonrasi)},
             "O1": O1, "O2": O2, "O3": O3,
             "kova_sayilari": kova_sayilari,
             "satir_dokumu": dokum,
             "olculemedi_nedenleri": olculemedi_nedenleri or None,
             "on_olcum_kiyasi": kiyas_on,
             "yazim_guvenligi": {"engellenen_state_yazim_denemesi": len(_yazim_denemeleri),
                                 "denemeler": _yazim_denemeleri or None}}
    with open(SONUC, "w") as f:
        json.dump(sonuc, f, indent=1, ensure_ascii=False)

    print(json.dumps({"O1": O1["oran"], "O2": O2["toplam_pnl_dollars"],
                      "kova_sayilari": kova_sayilari,
                      "on_olcum_tutarli": kiyas_on["tutarli"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
