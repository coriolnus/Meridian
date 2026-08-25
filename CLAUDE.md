# Meridian — Claude çalışma sözleşmesi (kısa tut; ayrıntı MERIDIAN_ENGINEERING_LOG.md'de)

1. HER OTURUM ÖNCE `MERIDIAN_ENGINEERING_LOG.md` oku: hedef sözleşmesi + açık kalanlar oradan.
2. Roller: Fable = mimari/brief/denetim/kök-neden (kod yazmaz; ops betiği/doküman hariç). Opus = brief
   kapsamında implementasyon. Tur başına tek konsolide brief; dosya-ayrıklık sözleşmesi.
   ROL-1 TANIMI (2026-08-26 denetimi): madde 3/6/8/10 "Rol-1" der ama tanımı hiçbir yerde yoktu — iki
   sözlük (model adı: Fable/Opus · konum adı: Rol-1/ajan) birbirine bağlı değildi. **Rol-1 = ANA
   CHECKOUT'ta koşan orkestratör oturumdur; MODEL KİMLİĞİNDEN BAĞIMSIZ bir KONUM adıdır** (bugün Fable,
   ama Opus koşan bir ana oturum da Rol-1'dir). Alt ajanlar ve worktree/yan oturumlar Rol-1 DEĞİLDİR.
   İKİ YÖNLÜ ZARARI KAPATIR: (a) ana oturum kendini "yalnız implementasyon" sayıp tur-kapanışı
   commit+push'unu atlamaz; (b) yan oturum kendini Rol-1 sanıp otoriter suite başlatmaz/push atmaz.
3. Ölçüm disiplini: `research/cards/` ön-kayıt kartı olmadan ölçüm kodu YOK. Eşik sonradan değişmez; K grid'de ÇARPILARAK sayılır; kill-list dokunulmaz; ölçüm ajanı karta dokunmaz (hükmü Rol-1 işler).
4. Yasalar: UYDURMA YASAĞI (ölçülemeyen None + neden). YASA 4: sessiz-yutma işaretli + ≥20 karakter gerekçe. YASA 6: okuyucusuz yazım yok. PIT'siz fundamentals proxy YASAK.
5. Canlı sistem A1'de (Oracle, ubuntu@130.61.126.87). YERELDE `./serve.sh` KOŞMA (çift emir riski). Canlı worker koşarken state'e yazma. Dağıtım: dry-run + mtime kontrolü + bakım penceresi + doğrulama.
   DAĞITIM YETKİSİ (2026-08-26 denetimi — belge reçeteyi veriyordu, SAHİBİNİ vermiyordu; kural yalnız
   oturum hafızasındaydı ve `.claude/` versiyonlanmadığı için GitHub'dan klonlayan cloud oturumu onu HİÇ
   ALMIYORDU): dağıtım yalnız **Rol-1**indir (madde 2). Yan/worktree oturumları ve ajanlar canlıya
   DAĞITMAZ ve dağıtım ÖNERMEZ — işi bitince commit + kanıt yazıp devir brief'i bırakır.
   ÖLÇÜLMÜŞ TUZAK, ezber düzeltmesi: `dagit.sh` NEREDEN çağrılırsa çağrılsın ANA CHECKOUT'u dağıtır
   (`dagit.sh:28` `REPO="$HOME/AI-Trading"` + `cd "$REPO"`). Yani yan oturum kendi kolunu canlıya
   İTEMEZ — bunun yerine ana checkout'un O ANKİ HEAD'ini, muhtemelen BAŞKA bir oturumun yarım işini
   iter, ve kirlilik kapısı da kendi temiz ağacına değil ANA checkout'a bakar. "Ağacım temiz" hissi
   burada bir güvence DEĞİLDİR.
6. Test disiplini: tam suite yalnız Rol-1'de tek-otoriter; ajanlar kapsam testi koşar. tail-kesmeli triyaj yok — tam `grep -E "FAILED|ERROR"`.
7. Bekleme betiği (waiter) YASAK. TANIM (2026-08-26 denetimi — cümle yasakladığı şeyi tanımlamıyordu ve
   "arka plan görevi olarak" ibaresi İSTİSNA sanıldı, iki ölçülü ihlal doğurdu): yasak olan KENDİ
   KURDUĞUN YOKLAMA DÖNGÜSÜdür (`until`/`while` + `sleep`) — ÖN PLANDA da ARKA PLANDA da. **Döngünün
   nerede koştuğu muafiyet değildir.** Doğru yol: uzun işi `run_in_background` ile başlat, BİTİŞ
   BİLDİRİMİNİ bekle (harness oturumu kendisi yeniden çağırır), çıktı dosyasını BİR KEZ oku. Gerçek
   koşul/olay izlemesi gerekiyorsa elle döngü değil `Monitor` aracı kullanılır.
   ZORUNLU SONUÇ: tam suite ÖN PLANDA koşturulamaz — Bash tavanı 600 sn, suite 18-50 dk
   (docs/RUNBOOK.md:1344,1350). Arka plan burada bir tercih değil, tek yoldur.
8. GİT (2026-07-31'den beri): tur başına commit — Rol-1 UYGUN GÖRDÜĞÜ ANDA, operatör onayı
   beklemeden atar (kalıcı yetki 2026-07-31); ajanlar git komutu KOŞMAZ. Kirli
   çalışma ağacıyla dağıtım YOK (`dagit.sh` kapısı; bilinçli istisna `--kirli-gec`). state/,
   backups/, .env versiyonlanmaz — sır asla commit'lenmez (İSTİSNA: state/goal.yaml +
   state/bounds.yaml İZLİdir — dagit [1b] SSoT, c783442; ana checkout'taki git işlemleri bu
   ikisini içerik-aynı yeniden yazar, bekçi/mtime teşhisinde önce birth + .git/logs bak,
   2026-08-02 vakası). AJAN UÇUŞTAYKEN hüküm/doküman
   commit'leri AÇIK YOL LİSTESİYLE atılır (`git add -A` yasak — a94d425 vakası: tur ayrıklığını
   süpürüp bulandırdı). Tur-kapanışı commit'inden sonra `git push origin main` (2026-08-12'den
   beri; remote: github.com/coriolnus/Meridian, özel) — cloud oturumları GitHub'daki hali
   klonlar, push'lanmamış iş cloud'da görünmez. Push canlıya dağıtım DEĞİLDİR; dağıtım hâlâ
   dagit.sh üzerinden.
9. SUPERPOWERS ZORUNLU (2026-08-17'den beri): Bu depoda çalışan her Claude oturumu,
   `superpowers` plugin'ini ve bileşenlerini (brainstorming, systematic-debugging,
   test-driven-development, writing-plans, executing-plans, requesting/receiving-code-review,
   verification-before-completion, using-git-worktrees vb.) kullanmak ZORUNDADIR — madde 2'deki
   rol ayrımının (Fable=mimari/brief/denetim, Opus=implementasyon) ÜSTÜNE eklenir, onu iptal
   etmez: hangi rol kod/karar üretiyorsa, kendi kapsamında ilgili superpowers skill akışını
   (örn. karar/tasarım işi → brainstorming; implementasyon → TDD; bitirmeden önce →
   verification-before-completion) izler. Çelişki halinde bu dosyadaki madde 1-8 (Meridian'a
   özgü ölçüm/git/dağıtım disiplini) önceliklidir — superpowers akışı bu kısıtları gevşetemez
   (örn. "bekleme betiği yasak" [madde 7] veya "tam suite tek-otoriter" [madde 6] superpowers
   önerisiyle çakışırsa Meridian kuralı kazanır).
10. WORKFLOW / ULTRACODE — İZİN KAPISI ≠ MUHAKEME KAPISI (2026-08-26). Oturum system prompt'u
    "workflow kullanma, kullanıcı istemedikçe" der; ultracode'un AÇIK olması o cümlenin kendi
    istisna şartını (`unless the user requested it`) KARŞILAR — Workflow aracının tanımı
    ultracode'u geçerli opt-in biçimleri arasında sayar. Yani ÇELİŞKİ YOKTUR: ultracode açıkken
    fan-out yapmaya İZİN vardır. Kaldırdığı tek şey izin kapısıdır; şu ikisini KALDIRMAZ:
    (a) MUHAKEME KAPISI — `token-tutumlulugu`: fan-out yalnız GEREKÇELİ. İş gerçekten
        ayrışmıyorsa (tek dosya, sıkı bağlı sözleşme, önce teşhis gereken arıza) tek ajan daha
        iyidir. Teşhis BİTMEDEN fan-out, N ajana tahmin ettirmektir (systematic-debugging Faz 1).
        Ultracode'un kendi metni de mekanik/konuşma turlarını zaten muaf tutar.
    (b) NASIL KOŞACAĞI — madde 1-8 burada da ÖNCELİKLİDİR (madde 9'un emsali):
        · madde 6 → ajanlar EŞZAMANLI pytest KOŞMAZ; tam suite yalnız Rol-1'de, DONMUŞ ağaçta.
          Dosya-ayrıklığı YETMEZ: `state/` paylaşımlıdır ve iki kapsam testi birbirinin
          fixture'ını bozar (`paralel-ajan-test-cakismasi` vakası).
        · madde 7 → workflow içinde bekleyici/sleep-döngüsü YOK.
        · madde 8 → ajanlar git komutu koşmaz; commit/push Rol-1'de kalır.
        · madde 3 → ön-kayıt kartı olmadan ölçüm ajanı çıkarılmaz; ajan karta dokunmaz.
    ÖZET: "ultracode açık" = fan-out serbest, ama NE ZAMAN'ı muhakeme, NASIL'ı madde 1-8 belirler.
