"""adapters/macro.py — EMEKLİ MODÜL (ÇIKARILDI 2026-07-30, temizlik turu).

NE VARDI: `snapshot()` (SPY serisinden türetilmiş makro/rejim anlık görüntüsü) ve `status()`
(sağlayıcı künyesi). İkisi de 2026-07-21 tur-5 denetiminde "ÜRETİM TÜKETİCİSİ YOK — skill yüzeyi
iskelesi" diye YAZILI olarak işaretlenmişti; bu tur o teşhisi kapattı.

ÇAĞIRAN TARAMASI (2026-07-30, meridian/ + tests/ + ops/ + deploy/ + skills/): `meridian` paketinde
bu modülü içe aktaran TEK bir satır yok (`from . import macro` / `import macro` → 0 eşleşme).
Tek tüketici `tests/test_macro_news_audit_v20.py` ve `tests/test_gaps_final_v52.py`'nin
determinizm satırıydı — ikisi de bu turda güncellendi. `skills/` altındaki `macro.get(...)`
eşleşmeleri BAŞKA betiklerin kendi yerel sözlükleridir, bu modül değil.

NEDEN SARMALAYICI DEĞİL DE ÖLÜ: canlı rejim sınıflaması `regime.classify` ile DOĞRUDAN döngüde
yapılıyor (loop.py) ve `snapshot()` yalnız aynı fonksiyonu SPY barlarıyla bir kez daha çağırıp
sözlüğe sarıyordu. İkinci bir "rejim gerçeği" üreten, hiç okunmayan bir yol.

GERİ-AL: modül gövdesi tekti — `WINDOW_START = "2023-01-01"` sabiti, `snapshot(index_bars=None)`
(bars yoksa `data.load_bars(data.INDEX_SYMBOL, WINDOW_START, dataset.fetch_end())` ile yükler,
sonra `regime.classify` + `regime.distribution_days` + `regime.follow_through` sonuçlarını
`{"available": True, "source": "index-derived (SPY)", ...}` sözlüğünde döndürürdü) ve
`status()` (sabit künye sözlüğü). Dosya SİLİNMEDİ ki geri-al notu adresinde dursun; içe
aktarılması hâlâ hatasızdır ve hiçbir ad sunmaz.
"""
from __future__ import annotations
