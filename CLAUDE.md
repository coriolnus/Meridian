# Meridian — Claude çalışma sözleşmesi (kısa tut; ayrıntı MERIDIAN_ENGINEERING_LOG.md'de)

1. HER OTURUM ÖNCE `MERIDIAN_ENGINEERING_LOG.md` oku: hedef sözleşmesi + açık kalanlar oradan.
2. Roller: Fable = mimari/brief/denetim/kök-neden (kod yazmaz; ops betiği/doküman hariç). Opus = brief kapsamında implementasyon. Tur başına tek konsolide brief; dosya-ayrıklık sözleşmesi.
3. Ölçüm disiplini: `research/cards/` ön-kayıt kartı olmadan ölçüm kodu YOK. Eşik sonradan değişmez; K grid'de ÇARPILARAK sayılır; kill-list dokunulmaz; ölçüm ajanı karta dokunmaz (hükmü Rol-1 işler).
4. Yasalar: UYDURMA YASAĞI (ölçülemeyen None + neden). YASA 4: sessiz-yutma işaretli + ≥20 karakter gerekçe. YASA 6: okuyucusuz yazım yok. PIT'siz fundamentals proxy YASAK.
5. Canlı sistem A1'de (Oracle, ubuntu@130.61.126.87). YERELDE `./serve.sh` KOŞMA (çift emir riski). Canlı worker koşarken state'e yazma. Dağıtım: dry-run + mtime kontrolü + bakım penceresi + doğrulama.
6. Test disiplini: tam suite yalnız Rol-1'de tek-otoriter; ajanlar kapsam testi koşar. tail-kesmeli triyaj yok — tam `grep -E "FAILED|ERROR"`.
7. Bekleme betiği (waiter) YASAK; uzun işler arka plan görevi olarak, çıktı dosyasından okunur.
8. GİT (2026-07-31'den beri): tur başına commit (Rol-1 atar; ajanlar git komutu KOŞMAZ). Kirli
   çalışma ağacıyla dağıtım YOK (`dagit.sh` kapısı; bilinçli istisna `--kirli-gec`). state/,
   backups/, .env versiyonlanmaz — sır asla commit'lenmez.
