# research/olcumler — hüküm-kanıt arşivi (2026-07-31'den beri)

Kartların (`research/cards/`) atıf yaptığı ölçüm kanıtları: `sonuc.json` (her sayının kaynağı),
`RAPOR.md` (sayılar yalnız sonuc.json'dan basılır), ön-adım dosyaları ve kod damgaları.

NEDEN BURADA: ölçüm sandbox'ları (motor kopyaları, kol dökümleri, state dizinleri) oturum-geçici
scratchpad'de yaşar ve YAŞAMALIDIR (repo şişmez, motor kopyaları karışmaz). Ama HÜKÜM KANITI
kalıcıdır — kart "kanıt: X/sonuc.json" diyorsa o dosya git tarihinde durmalı. Ham kol dökümleri
(kol_*.json, yüzlerce KB) bilinçli DIŞARIDA; >2MB dosyalar kopyalanmaz.

Yeni ölçüm kapanınca: sonuc.json + RAPOR.md + on_adim*/kod_damgasi buraya kopyalanır, kartla
AYNI commit'te girer (Rol-1 işi).
