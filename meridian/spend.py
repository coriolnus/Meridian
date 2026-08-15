"""spend.py — Hermes LLM çağrılarının maliyet defteri ve aylık bütçe kapısı.

Ne yapar: birkaç kapanmış işlemde bir LLM çağıran, kendini geliştiren bir ajan faturayı
sessizce kabartabilir; bu modül harcamayı açık ve sınırlı tutar. Her gerçek sağlayıcı
çağrısının token kullanımı ve tahmini USD maliyeti `record` ile state/spend.jsonl'a eklenir.
Çağrı öncesi `over_budget` ayın harcaması bütçeye (HERMES_MONTHLY_BUDGET_USD, varsayılan $20)
ulaştığında True döner; Hermes o zaman ücretsiz deterministik öneriye düşer — döngü öğrenmeye
devam eder, yalnız ücretli çıkarım kapanır. `summary` ay özetini üretir (/api/spend → pano);
`estimate_cost`/`price_for` maliyeti model-başına fiyat tablosundan hesaplar (PRICES:
opus/sonnet/haiku/gemini/nous — model adında alt-dizge eşleşmesi; bilinmeyen model
muhafazakâr varsayılana düşer).

Değişmezler: fiyat MODEL BAŞINA olmak zorundadır — tek fiyatla ücretsiz katman çağrıları da
Opus listesinden fiyatlanır, harcanmamış para bütçeyi doldurur ve LLM katmanı sessizce
kapanırdı ("beyin neden susuyor" sorusunun görünmez cevabı); saat dilimi UTC'dir ki satırlar
diğer defterlerle (obs, memory, watchdog) yan yana okunabilsin; `thought_tokens` yalnız
sağlayıcı bildirdiğinde yazılır (UYDURMA YASAĞI: alan yokluğu "ölçülmedi"dir, sıfır değil) ve
maliyete katılmaz — fiyatlanan tek çıktı `out_tokens`tır.

Okur/yazar: spend.jsonl (append-only, store üzerinden). Anahtar gerektirmez; Hermes koşunca
kendiliğinden etkinleşir. Fiyatlar değiştiğinde env ile geçersiz kılınabilir."""
from __future__ import annotations
import datetime as dt
import os

from . import store

# per-1M-token list prices (USD); override via env when pricing changes
PRICE_IN_PER_M = float(os.environ.get("HERMES_PRICE_IN", "15.0"))
PRICE_OUT_PER_M = float(os.environ.get("HERMES_PRICE_OUT", "75.0"))
MONTHLY_BUDGET_USD = float(os.environ.get("HERMES_MONTHLY_BUDGET_USD", "20.0"))

# MODEL BAŞINA fiyat. Eskiden TEK bir fiyat vardı ve `record(model=...)`
# onu YOK SAYIYORDU: ücretsiz katmandaki Gemini ya da yerelde koşan Nous çağrıları da Opus listesi
# ($15/$75 per M) ile fiyatlanıyordu. Sonuç: HARCANMAMIŞ para bütçeyi doldurur, over_budget() true
# olur ve LLM katmanı sessizce kapanırdı — "beyin neden susuyor" sorusunun görünmez cevabı.
# Anahtar: model adında geçen alt-dizge (küçük harf). Bilinmeyen model → varsayılan (muhafazakâr).
PRICES: dict[str, tuple[float, float]] = {
    "opus": (15.0, 75.0),
    "sonnet": (3.0, 15.0),
    "haiku": (0.8, 4.0),
    "gemini": (float(os.environ.get("HERMES_PRICE_GEMINI_IN", "0.0")),
               float(os.environ.get("HERMES_PRICE_GEMINI_OUT", "0.0"))),   # varsayılan: ücretsiz katman
    "hermes-4": (0.0, 0.0),        # yerel/Nous portal — operatörün kurulumunda ücretsiz
    "nous": (0.0, 0.0),
}


def price_for(model: str | None) -> tuple[float, float]:
    """Model adına göre (girdi, çıktı) milyon-token fiyat çiftini verir; tanınmayan model varsayılan
    fiyata düşer."""
    m = str(model or "").lower()
    for key, pair in PRICES.items():
        if key in m:
            return pair
    return (PRICE_IN_PER_M, PRICE_OUT_PER_M)


def _now_iso() -> str:
    """UTC — defterin geri kalanıyla (obs, memory, watchdog) AYNI saat dilimi. Eskiden yerel saatti;
    ay sınırı diğer kayıtlarla kayıyor ve satırlar olay defteriyle yan yana okunamıyordu."""
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def estimate_cost(in_tokens: int, out_tokens: int, model: str | None = None) -> float:
    """Tek çağrının USD maliyetini hesaplar: (girdi + çıktı tokenları) × modelin milyon-token fiyatı,
    4 ondalığa yuvarlı."""
    p_in, p_out = price_for(model)
    return round(in_tokens * p_in / 1_000_000 + out_tokens * p_out / 1_000_000, 4)


def record(in_tokens: int, out_tokens: int, model: str, note: str = "", ts: str | None = None,
           thought_tokens: int | None = None) -> dict:
    """Append one call's usage to the ledger and return the row.

    thought_tokens: DÜŞÜNEN modellerin (gemini-3.x) gizli akıl yürütme tokenları — sağlayıcı bunları
    ÜRETİM tavanından yer ve faturalar, ama `candidatesTokenCount` içinde GÖRÜNMEZLER. Ölçülmediği
    yerde None kalır (uydurma yasağı): yalnız cevabında bu sayıyı bildiren sağlayıcı yolu doldurur,
    bu yüzden alan yoksa "sıfırdı" değil "ölçülmedi" demektir ve satıra hiç yazılmaz.
    Maliyet formülü DEĞİŞMEDİ: burada fiyatlanan tek çıktı `out_tokens`tır. Düşünce tokenlarını
    cost_usd'ye katmak fiyat sözleşmesini (ve mevcut denetim testlerini) değiştiren ayrı bir karardır;
    tek düşünen sağlayıcı olan gemini zaten ücretsiz katmanda (PRICES["gemini"] = 0/0) fiyatlanıyor.
    Sayı yine de defterde ve `summary()`de görünür — bütçenin görünmez tarafı artık ölçülebilir."""
    row = {"ts": ts or _now_iso(), "model": model, "in_tokens": int(in_tokens),
           "out_tokens": int(out_tokens), "cost_usd": estimate_cost(in_tokens, out_tokens, model),
           "note": note}
    if thought_tokens is not None:
        row["thought_tokens"] = int(thought_tokens)
    store.append_jsonl("spend.jsonl", row)
    return row


def month_spend(month: str | None = None) -> float:
    """Verilen ayın (varsayılan: içinde bulunulan UTC ayı) toplam harcamasını defterden toplar."""
    m = month or _now_iso()[:7]                      # YYYY-MM
    rows = store.read_jsonl("spend.jsonl")
    return round(sum(float(r.get("cost_usd", 0.0)) for r in rows if str(r.get("ts", ""))[:7] == m), 4)


def over_budget(budget: float | None = None, month: str | None = None) -> bool:
    """O ayki harcama bütçe tavanına ulaştı mı? Tavan 0/negatifse bütçe kapalı sayılır ve hep False döner."""
    cap = MONTHLY_BUDGET_USD if budget is None else budget
    return cap > 0 and month_spend(month) >= cap


def summary(month: str | None = None) -> dict:
    """Ayın harcama özeti: harcanan, bütçe, kalan, tavan aşıldı mı, çağrı sayısı ve düşünce tokenı toplamı.
    Hiçbir satır düşünce tokenı taşımıyorsa toplam None kalır — 0 yazmak ölçülmemişi ölçülmüş göstermek olurdu."""
    m = month or _now_iso()[:7]
    rows = store.read_jsonl("spend.jsonl")
    this_month = [r for r in rows if str(r.get("ts", ""))[:7] == m]
    spent = round(sum(float(r.get("cost_usd", 0.0)) for r in this_month), 4)
    # YASA 6 — üretilen alanın OKUYUCUSU: düşünce tokenları burada toplanır ve /api/spend üzerinden
    # panoya çıkar. Alanı HİÇ taşımayan satır "ölçülmedi"dir; hiçbiri taşımıyorsa toplam None kalır
    # (0 yazmak "düşünce yoktu" demek olurdu — ölçülmemişi ölçülmüş göstermek).
    measured = [r for r in this_month if r.get("thought_tokens") is not None]
    return {"month": m, "spent_usd": spent, "budget_usd": MONTHLY_BUDGET_USD,
            "remaining_usd": round(max(0.0, MONTHLY_BUDGET_USD - spent), 4),
            "over_budget": MONTHLY_BUDGET_USD > 0 and spent >= MONTHLY_BUDGET_USD,
            "calls_this_month": len(this_month),
            "thought_tokens": sum(int(r["thought_tokens"]) for r in measured) if measured else None}
