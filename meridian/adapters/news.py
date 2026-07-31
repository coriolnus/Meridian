"""adapters/news.py — EMEKLİ MODÜL (ÇIKARILDI 2026-07-30, temizlik turu).

NE VARDI: `stock_news(symbols, limit)` (FMP `/news/stock` akışı), `status()` (dürüst sağlayıcı
durumu), `available()` ve `MAX_SYMBOLS`. `status()`ün kendi docstring'i 2026-07-21'de zaten
"bu modülün de üretim tüketicisi yok — skill yüzeyi" diyordu.

ÇAĞIRAN TARAMASI (2026-07-30, meridian/ + tests/ + ops/ + deploy/): `meridian` paketinde bu
modülü içe aktaran TEK bir satır yok. Tüketiciler yalnız `tests/test_macro_news_audit_v20.py` ve
`tests/test_review_backlog_v98.py`'nin sessiz-yutma satırlarıydı — ikisi de bu turda güncellendi.
`skills/canslim-screener/references/fmp_api_endpoints.md`'deki `stock_news` geçişi bir FMP
DOKÜMANTASYON satırıdır, bu fonksiyonun çağrısı değil.

NEDEN ÜÇÜ BİRDEN: `stock_news` gidince `available()` ve `MAX_SYMBOLS` de çağıransız kalırdı —
"ölü mekanizma sıfır" hedefi (§ hedef sözleşmesi md.1) yarım bir emeklilikle sağlanmaz. Haber
skilleri geri istenirse zincir FMP anahtarı üzerinden yeniden kurulur; kırpma/uyarı dersleri
aşağıda yazılı kalıyor ki aynı tuzaklar ikinci kez kurulmasın.

GERİ-AL (ve o zaman KORUNMASI gereken üç ders):
  * `stock_news`: `fmp._get("news/stock", {"symbols": ",".join(symbols[:20]), "limit": limit})`;
    anahtar TEK yerde (adapters/fmp.py) kalır, burada TEKRAR EDİLMEZ.
  * SESSİZ KIRPMA YASAĞI: uç nokta pratikte 20 sembol alıyor. 250 sembol isteyen çağıran 20
    tanesini alıp "haber yok" sanıyordu → kırpma `obs.warn("news_symbols_truncated", asked=…,
    sent=…)` ile KAYDA GEÇMELİ.
  * "HABER YOK" ≠ "HABER ALINAMADI": ağ/sağlayıcı hatasında `[]` dönmek DOĞRU davranıştır (çağıran
    boş akışla yaşayabilir) ama sessiz olması değil → `obs.warn("news_fetch_failed", …)`.
    `status()` de "anahtar var mı" değil "kaynak üretiyor mu" (`fmp.health()["ok"]`) demeliydi.
"""
from __future__ import annotations
