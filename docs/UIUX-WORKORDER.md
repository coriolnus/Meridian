MERIDIAN — Dünya Sınıfı Pano UI/UX Prompt'u (v5-uiux)
Kullanım: Bu belgeyi Claude Code'a repo kökünde `docs/UIUX-WORKORDER.md` olarak ver ve "bu dosyayı oku, WP0'ı çalıştır" de. Mühendislik (v4) ve strateji (edge-katalog) iş emirleriyle paraleldir; çelişkide anayasa üstündür. Bu belge yalnız görsel ve etkileşim katmanı hattıdır.
0) ROL VE KAPSAM SINIRI
Sen Meridian panosunda çalışan kıdemli bir UI/UX mühendisisin: bilgi mimarisi, görsel sistem, veri görselleştirme ve etkileşim tasarımı senin alanın. Sınırlar:

* Veri semantiğine, strateji mantığına, eşiklere dokunma; pano yalnız gösterir, yorum katmanı eklemez.
* Pano birçok tablonun kayıtlı okuyucusudur (codelaw): bir bileşeni kaldırmak bir tabloyu öksüz bırakabilir. Her bileşen silme/değiştirme işlemi okuyucu kaydına karşı kontrol edilir.
* Verify-first: mevcut pano kodunu, stack'i ve ekranları görmeden hiçbir varsayım yapma; WP0 onaylanmadan kod değişmez.

1) TASARIM TEZİ — "Cam kokpit" metaforu ciddiye alınır
Bu bir pazarlama dashboard'u değil; tek operatörlü bir kontrol odası enstrümanıdır. Tasarım kişiliği: sessiz hassas alet — süs yok, gösteriş yok; kişilik, sükûnetin kendisinden ve sayıların kusursuz dizilişinden gelir. İlke: sağlıklı sistem görünmezdir; renk bir olaydır.
İmza öğesi — "Sessiz Hat": Ekranın en üstünde, uçak overhead panelinden esinlenen tek ince şerit: 17 gözetim mekanizmasının nabzı + 2 bayrak/5 kilit + veri tazeliği, segmentler halinde. Her şey yolundayken şerit neredeyse görünmez koyu gridir (tek satırlık "sistem sağlıklı · son koşu 21:47 · kapsama %100" metniyle); bir mekanizma sustuğunda yalnız o segment yanar. Panonun hatırlanacağı tek şey budur; geri kalan her şey disiplinli ve sessizdir.
Anti-default uyarısı: "Koyu tema" burada siyah zemin + tek neon vurgu klişesine düşmez. Zemin ISA-101 çizgisinde yumuşak koyu griler; marka vurgu rengi diye bir şey yoktur — renk yalnız durum sinyalidir. Kimlik, vurgu renginin yokluğudur.
2) KANIT ÇIPALARI — tasarımı yönlendiren yedi bulgu
Ç1 — Gri zemin, renk = anormallik (ISA-101 / High-Performance HMI): Endüstriyel kontrol ekranlarında normal çalışan ekipman nötr gri çizilir; renk yalnız dikkat gerektiren duruma girer. Ekranın ~%90'ı nötr kalır; doygunluk şiddetle artar. Salt bu renk disiplininin, anormal durumların alarmlar çalmadan önce fark edilmesinde %48 iyileşme sağladığı raporlanmıştır. Her yerde renk = hiçbir yerde sinyal.
Ç2 — Karanlık kokpit (Airbus DQC): Sistem açık ve sağlıklıyken ışık sönüktür; ışık yalnız arıza/eylem gerektiğinde yanar — "arıza yoksa dikkat dağıtıcı da yoktur." Meridian gecesi sağlıklı geçtiyse pano sabah operatöre sessizlik göstermelidir; "her şey yolunda" hali özellikle tasarlanan bir ekrandır, boş bir ekran değil.
Ç3 — Alarm bütçesi (EEMUA 191 / ISA 18.2): Sürdürülebilir operatör yükü: normalde ~10 dakikada 1 alarm (≈6/saat); ~150/gün üstü kabul edilemez bölgeye girer; üst üste yığılmalar (flood) ayrıca tasarlanır. Pano bildirimleri bu bütçeye tabidir ve oran panoda ölçülür — alarm sistemi kendi karnesini gösterir.
Ç4 — Gauge yasağı, bullet grafiği (Few): Kadran/ibre göstergeleri az bilgi verir, çok yer kaplar, süsle doludur; yerine doğrusal bullet graph: ölçüm + hedef + nitel aralık tek kompakt satırda. Genel ilke: veri-dışı pikselleri kaldır, veri piksellerini güçlendir.
Ç5 — Shneiderman mantrası: "Önce genel görünüm, sonra yakınlaş ve filtrele, en son istek üzerine ayrıntı." Her ekran bu üç katmanla kurulur; Overview tek ekranda, kaydırmasız.
Ç6 — Tabular rakamlar: Canlı güncellenen sayılar proportional rakamlarla zıplar ve sütunlar hizalanmaz; `font-variant-numeric: tabular-nums` her rakama eşit genişlik verir, layout shift'i bitirir. Web fontlarının yalnız ~%16'sı tabular varyant taşır — font seçiminde tnum desteği zorunlu kriterdir.
Ç7 — Renk körlüğü ve çift kodlama: Erkeklerin ~%8'i kırmızı-yeşil ayırt edemez. Kâr/zarar ve durum asla yalnız renkle kodlanmaz: işaret (+/−), yön oku ve konum her zaman eşlik eder; mavi/turuncu, kırmızı/yeşilin güvenli alternatifidir; metin kontrastı ≥ 4.5:1, grafik öğeleri komşularına ≥ 3:1.
3) PROGRAM IA — Bilgi Mimarisi

* Kullanıcı ve işler: Tek operatör. Üç temel iş: J1 Sabah turu (≤60 sn: dün gece ne oldu, bu sabah ne silahlandı, sağlık nasıl), J2 Olay triyajı (alarm → teşhis → runbook → çözüm), J3 Araştırma incelemesi (karne, gölge kollar, hipotez hattı, K-defteri).
* Hiyerarşi: `Overview` (tek ekran) → alan sayfaları: `Veri Sağlığı`, `Koşu/Döngü`, `Portföy & Emirler`, `Öğrenme (Hermes/Gölge)`, `Gözetim & Alarmlar`, `Kilitler & Yapılandırma` → tekil detay: `bir koşu`, `bir işlem`, `bir hipotez kartı`.
* Her ekran tek cümlelik bir soruyu cevaplar; cevaplamadığı hiçbir veri o ekranda durmaz ("ekrana dök" yasağı).
* Navigasyon: kalıcı sol ray (ikon+etiket), Sessiz Hat her sayfada sabit. DoD: IA haritası + ekran başına "cevapladığı soru" cümlesi + J1'in 60 saniyelik akış çizimi.

4) PROGRAM V — Görsel Sistem

* Token mimarisi: Renk/tipografi/aralık/yükseklik token'ları W3C DTCG formatında (2025.10 kararlı spesifikasyon) tek `tokens.json`; tema (koyu birincil, açık ikincil) token katmanında türetilir. Kod token dışı renk/boyut kullanamaz (lint kuralı).
* Palet (ISA-101 esinli): Zemin: 3-4 kademeli yumuşak koyu gri (saf siyah yasak — parlama/kontrast yorgunluğu); çizgi/metin: açık griler. Durum rampası: bilgi=soluk mavi-gri, uyarı=amber, kritik=doygun kırmızı — kritik kırmızı yalnız kritikte, başka hiçbir yerde. Sağlıklı durumun rengi yoktur (nötr gri onay).
* Kâr/zarar kodlaması: Varsayılan çift-kodlama: işaret + yön oku + hue; kullanıcı tercihi olarak "mavi/turuncu" renk-körü paleti ve "renksiz (yalnız işaret)" modu. Yeşil, "her şey yeşil" duyarsızlaşmasını önlemek için serbest kullanımdan çıkarılır.
* Tipografi: Tek sans ailesi + veri için tnum garantili eşlenik (adaylar: Inter, IBM Plex Sans/Mono, Source Sans 3 — seçim kriteri: tabular figürler, slashed-zero, yüksek x-height, yoğun boyutta okunabilirlik). Tüm sayısal hücreler: `tabular-nums slashed-zero`, sağa hizalı, sabit ondalık. Dekoratif display fontu bilinçli olarak YOK — kişilik rakamlarda.
* Yoğunluk ve ızgara: 4px aralık ızgarası; `compact` varsayılan, `comfortable` seçenek; satır yüksekliği ve dolgu token'ları yoğunluk modundan türetilir. DoD: tokens.json + tema önizleme sayfası + kontrast denetim raporu (4.5:1 / 3:1) + PnL kodlama örnek seti.

5) PROGRAM D — Veri Görselleştirme Standartları

* Grafik seçim tablosu: hedefe karşı ölçüm → bullet (gauge/pie yasak); zaman serisi → çizgi/sparkline (Sessiz Hat altındaki kartlarda mini-trend: HPHMI "anlık değer değil eğilim" ilkesi — beklenen aralık bandıyla); sembol×seans kapsaması → ısı matrisi (tek-hue skala, kırmızı-yeşil gradyan yasak); equity eğrisi + altında drawdown paneli; işlem yaşam döngüsü → yatay zaman şeridi; gölge kolları (4×6) → küçük katlar (small multiples), ortak eksen.
* Tufte disiplini: veri-dışı piksel yok (3D, gölge, süs grid yok); bar'da sıfır taban zorunlu, çizgide serbest ama eksen kırılması işaretli; eksenler ve birimler her zaman etiketli.
* Dürüstlük çizim kuralları (anayasa 1'in görsel karşılığı): Eksik veri boşluk olarak çizilir — interpolasyon çizgisi YASAK; karantina noktaları ayrık işaretle; onarım-dolgusu noktaları `source` rozetiyle; her grafik köşesinde `asof` damgası.
* Grafikler renk olmadan da okunmalı (gri tona çevir testi): çizgi stilleri/uç etiketleri ile ayrım. DoD: chart standartları belgesi + 5 çekirdek grafiğin yeniden tasarımı (kapsama matrisi, equity+DD, karne dağılımı, gölge küçük katlar, koşu şelalesi).

6) PROGRAM A — Alarm ve Durum UX

* Sessiz Hat (Bölüm 1'deki imza): 17 mekanizma + kilitler + tazelik; sağlıklı segment koyu gri, susan segment amber/kırmızı + yaş sayacı ("breadth-analyzer · 2s 14dk sessiz").
* Severity üçlüsü: Kritik (hemen eylem; kırmızı; sesli/harici bildirimle eş), Uyarı (bugün ilgilen; amber), Bilgi (kayıt; renksiz, yalnız günlükte). Her alarm satırı: ne oldu → ne anlama geliyor → runbook linki (v4 O4 ile bütünleşik).
* Alarm bütçesi göstergesi: saatlik/günlük alarm oranı EEMUA-esinli eşiklere karşı mini-bullet; flood durumunda gruplama/özetleme davranışı tasarlanır (tek tek 40 satır değil "onarım geçidi: 40 sembol" tek satırı + genişlet).
* "Her şey yolunda" ekranı bilinçli tasarlanır: sabah turunda tek bakışta sükûnet; kutlama yok, konfeti yok — sadece doğrulanmış sessizlik. DoD: alarm envanteri + severity ataması + sessiz-durum ve flood-durum ekran tasarımları + bütçe göstergesi.

7) PROGRAM H — Dürüstlük Arayüzü (anayasa → piksel)

* None asla 0 değildir: eksik değer "—" + nedeni tooltip'te ("kaynak yayınlamadı, 21:47"); sıfırla karışamaz.
* Tazelik: her veri bloğunda `asof` + yaş; eşik aşımında blok görsel olarak soluklaşır ve Sessiz Hat'te tazelik segmenti uyarır.
* Provenance: kaynak rozetleri (alpaca / massive / repair), detayda `snapshot_id · config_hash · code_sha` — karar-anı fotoğrafı UI'da izlenebilir.
* Kilit paneli: 2 bayrak + 5 kilit her zaman görünür; paper kilidi "kapalı = güvenli" olarak pozitif çerçevelenir; kilit durumu değişimi olay günlüğüne bağlı.
* K-defteri ve eşikler: deneme sayacı, etkin-N ve DSR eşiği araştırma ekranında kalıcı; her performans tablosu brüt + net-kötümser çift sütun standardıyla; canlı-vs-backtest bandında ×0.5 çıpası çizili.
* Skill sayacı düzeltmesi: canlı (30) ve emekli (37) ayrık gösterim — bilinen 67 açığı bu programda kapanır. DoD: dürüstlük pattern kitaplığı (None, staleness, provenance, çift sütun, kilit) + uygulandığı ekran listesi.

8) PROGRAM R — Gerçek Zaman ve Performans Algısı

* Bağlantı durumu: WS aynası için kalıcı küçük gösterge (bağlı/yeniden bağlanıyor/koptu + son senkron yaşı); kopukken veriler "donmuş" olarak işaretlenir, sessizce bayat gösterilmez.
* Dolum akışı: bekleyen → kısmi → tam rozetleri; mutabakat sapması ayrı ve yüksek kontrastlı (sıfır olmalı; sıfır değilse Sessiz Hat'te segment yanar).
* Algı bütçeleri: ilk anlamlı boyama < 1s (yerel ağ/SSH tüneli), etkileşim tepkisi < 100ms; yüklemede skeleton (spinner değil); büyük tablolar sanallaştırılır; güncellenen hücrede kısa arka plan nabzı (≤300ms) + tabular-nums sayesinde zıplamasız.
* `prefers-reduced-motion` durumunda nabız/geçişler kapanır. DoD: performans bütçesi tanımı + ölçüm scripti + WS durum makinesinin UI eşlemesi.

9) PROGRAM X — Erişilebilirlik ve Ergonomi

* WCAG 2.2 AA taban: kontrast (4.5:1 metin, 3:1 grafik/UI), görünür odak halkası, hedef boyutu, başlık hiyerarşisi, tablo başlık ilişkileri.
* Klavye-öncelikli: `?` kısayol paleti, `g d / g a / g r` sayfa atlamaları, `j/k` satır gezinme, `Cmd+K` komut paleti (sembol/koşu/hipotez arama).
* Renk körlüğü simülasyonu tasarım denetiminin parçası (protanopi/döteranopi); gri-ton testi her yeni ekran için zorunlu. DoD: axe taraması temiz + klavye tur notu + simülasyon ekran görüntüleri.

10) PROGRAM S — Tasarım Sistemi ve Uygulama

* WP0 keşfi belirler: mevcut stack (şablon motoru? SPA? çizim kütüphanesi?) envanteri çıkar; yeniden yazım yasak (tetiksiz) — token + bileşen katmanı mevcut stack'e kademeli giydirilir (strangler). Stack değişikliği ancak ADR ile.
* Bileşen envanteri: `QuietLine`, `HealthTile`, `StatCell` (tnum), `DataTable` (sanallaştırılmış, çift-sütun destekli), `TrendSpark` (aralık bantlı), `BulletBar`, `HeatMatrix`, `LifecycleStrip`, `ProvenanceBadge`, `StalenessTag`, `LockPanel`, `AlarmRow`, `RunbookLink`, `LogViewer`.
* Mini styleguide sayfası: her bileşen, durumları (boş/yüklü/hatalı/bayat) ve karanlık kokpit halleriyle canlı örnekte.
* Metin/mikro-kopya: arayüz dili operatörün diliyle ("Koşu tamamlandı", "Onarım geçidi 3 delik kapattı"); hata mesajları ne olduğunu + ne yapılacağını söyler, özür dilemez; boş ekranlar eyleme davet eder. DoD: styleguide canlı + ilk 6 bileşen üretimde + kopya rehberi tek sayfa.

11) ANTİ-HEDEFLER
Gauge/kadran, pie, 3D, gradyan süsleri · marka vurgu rengi ve "neon aksan" estetiği · dekoratif animasyon (yalnız durum değişimi anime edilir — HPHMI kuralı) · genel admin-template görünümü · her metriği ekrana dökmek · tetiksiz framework göçü · kutlama/gamification öğeleri. Her biri için gerekçe yukarıdaki çıpalarda; istisna ancak ADR ile.
12) YOL HARİTASI — dört sprint (2'şer hafta)

* S1 — Zemin: WP0 (envanter + ekran görüntüleri + Nielsen-10 heuristik denetim tablosu) → onay → tokens.json + tipografi/tnum geçişi + kontrast denetimi. Çıkış: token'lar üretimde, sayı zıplaması sıfır.
* S2 — Kalp: Overview yeniden tasarımı (J1 60-sn turu) + Sessiz Hat v1 + dürüstlük pattern'lerinin ilk üçü (None, staleness, provenance). Çıkış: sabah turu tek ekran, sessiz-durum tasarımı canlı.
* S3 — Sinyal: Alarm/severity sistemi + nabız duvarı → Sessiz Hat entegrasyonu + Veri Sağlığı ekranı (kapsama matrisi) + chart standartları ilk 5 grafik. Çıkış: alarm bütçesi ölçülüyor, flood davranışı testli.
* S4 — Derinlik: Araştırma ekranları (gölge küçük katlar, K-defteri, çift-sütun tablolar, kilit paneli) + komut paleti + erişilebilirlik denetimi + performans bütçesi ölçümü. Çıkış: axe temiz, J3 akışı uçtan uca.

13) AÇILIŞ TALİMATI
İlk eylem: WP0 — (1) pano kod tabanı ve stack envanteri; (2) mevcut ekranların görüntü envanteri (operatörden ekran görüntüleri iste); (3) Nielsen 10 sezgisel ilkesine göre denetim tablosu (ihlal × şiddet × ekran); (4) en kritik 5 UX borcu; (5) S1 bilet önerileri. Onay gelmeden kod değişmez. Her görsel değişiklik, etkilediği tabloların okuyucu kaydını günceller.
14) KAYNAK KISA LİSTESİ
ISA-101 / High-Performance HMI (ASM Consortium; gri zemin, renk=anormallik, %48 tespit iyileşmesi; trend>anlık değer) · Airbus "dark & quiet cockpit" felsefesi (arıza yoksa ışık yok) · EEMUA 191 / ISA 18.2 alarm performans hedefleri (~1/10dk, ~150/gün üst sınır, flood yönetimi) · Stephen Few, Information Dashboard Design (bullet graph, gauge eleştirisi, veri-piksel ilkesi) · Tufte, The Visual Display of Quantitative Information (data-ink) · Shneiderman, "The Eyes Have It" (overview → zoom/filter → details-on-demand) · MDN `font-variant-numeric` + tabular figürler pratiği (tnum, layout shift; webfontların ~%16'sı destekler) · WCAG 2.2 + renk körlüğü rehberleri (%8 erkek; mavi/turuncu alternatifi; çift kodlama; 4.5:1 / 3:1) · W3C Design Tokens Format Module 2025.10 (kararlı token spesifikasyonu) · Nielsen'ın 10 sezgisel ilkesi (WP0 denetim çerçevesi).
