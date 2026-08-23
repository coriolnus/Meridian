# RAPOR — §4 HAVUZ SAHİPSİZLERİ SINIFLANDIRMA ÖNERİSİ (2026-08-23)

**Kapsam:** 2026-08-23 §4 boşaltmasında DOKUNULMAYAN yedi kalem (ROADMAP :1805-1807 beyanı):
Ö-39 · Ö-41 · Ö-30 · Ö-42 · Ö-43 · Ö-33 · Ö-46. Her biri için bugünkü kod/tahta gerçeğiyle
önerilen sınıf + tek paragraf gerekçe.
**HÜKÜM YOK:** bu belge yalnız sınıflandırma ÖNERİSİDİR — taşımayı/kapatmayı Rol-1 yapar;
ROADMAP'e bu turda DOKUNULMADI.
**Ölçüm sınırı (uydurma yasağı):** canlı A1 state'i okunmadı; "kod gerçeği" bu çalışma ağacının
(worktree, a033256 üstü) grep/AST/okuma ölçümüdür. `state/` içinden yalnız git-İZLİ `goal.yaml`
okundu. Ö-41/Ö-42'de kalemin kendi tarihsel sayısı yeniden üretilemedi; ikisinde de bugünkü sayı
KENDİ yöntem beyanıyla verildi (yöntem farkı ≠ kalemin yanlışlığı).

## Özet tablosu

| Kalem | Önerilen sınıf | Tek cümle |
|---|---|---|
| Ö-39 | **WP7'ye taşı** (karar kalemi) | Künye/atıf ailesi WP7'de birleşti; iş bir ölçüm değil YOL kararı (Rol-1). |
| Ö-41 | **WP5-G'ye taşı** | Mutasyon-kapsamı suite hijyenidir; boşluk bugün de ~40 dosya, iş "davranış mı metin mi" sınıflaması. |
| Ö-30 | **Arşiv adayı** (bayat) | Çekirdek kusur kapanmış: `config.py` yedeği 0,5 ve çivili — sahip sorusu (WP2/WP6) düşmüş. |
| Ö-42 | **WP6'ya taşı** | `codelaw.capa_uyusmasi()` hâlâ yok; tarayıcı işi codelaw'ın evi WP6'dır. |
| Ö-43 | **Ders kaydı → arşiv adayı** | Düzeltme ve bayat-çapa kuyruğu kapanmış; ders Ö-49/WP6-E süpürme yöntemine zaten girdi. |
| Ö-33 | **Arşiv adayı** (ders kaydı) | Kural kurumsallaşmış (CLAUDE.md §6 + hafıza + hermes.py belge bloğu); açık iş gövdesi yok. |
| Ö-46 | **Arşiv adayı** (ders kaydı) | Fail-closed düzeltme kodda yerinde; kalan tek şey tarihçe (H00029 bilinçli retro-düzeltilmedi). |

---

## Ö-39 — Kalibrasyon "hangi beyin ne kadar isabetli"yi cevaplayamıyor (yapısal)

**Önerilen sınıf: WP7'ye taşıma adayı — "karar-önce" şerhli kalem (kart adayı DEĞİL).**
Bugünkü kod gerçeği kalemin beyanını aynen doğruluyor: `grep -c candidate_review
meridian/analytics.py` **bugün de 0**; ölçümün bayatlamasını donduran çivi
`tests/test_zincir_kunye_v246.py` yerinde. Yani eksik olan ölçüm değil (ölçüm 2026-08-14'te
yapılmış ve çivilenmiş), **yol kararıdır**: plan satırına ikinci alan yazmak yetki-sınırı yasasını
(`test_authority_boundaries_v77::test_c3`, `degisen == {"llm_opinion"}`) değiştirmeyi gerektirir;
ayrı atıf defteri ise `ledgers.CONTRACTS` kaydı + kalibrasyon tarafında tüketici ister. Kart
ön-kayıt disiplini burada yanlış alet olur — eşik/K harcayan yeni bir ölçüm yok, mimari seçim var.
Ailesi de taşınmış durumda: 2026-08-23 boşaltmasında Ö-31 (`active_model()` künye kusurunun ikinci
evi) ve Ö-40 (`nous_eval` künye alanları) **WP7'ye** gitti; Ö-39 aynı künye/atıf zincirinin karar
ucudur ve ayrı yerde durursa üç kalem yine birbirinden habersiz işlenir. Öncelik kalemin kendi
beyanıyla yüksek: model seçimi bir kaldıraç ve bugün geri-beslemesi yok.

## Ö-41 — Mutasyon kapsamı: seçim listesi ↔ türetme kuralı boşluğu

**Önerilen sınıf: WP5-G'ye taşıma adayı (ölçüm altyapısı / suite hijyeni).**
Bugünkü ölçüm (bu tur): `pyproject.toml` `pytest_add_cli_args_test_selection` listesi **45
girdiye** çıkmış (kalem yazıldığında 39'du — dört v237-emsali tekil ekleme yapılmış demek ki desen
işliyor ama boşluğu kapatmıyor); türetme kuralının modül-düzeyi AST eşi bugün **85 test modülü**
buluyor (kalemde 79; benim taramam YALNIZ modül-düzeyi import sayar, kalemin kuralı fonksiyon-içi
importu da saydığından gerçek sayı ≥85) → boşluk bugün de **~40 dosya** ve büyümeye açık (tests/
toplamı 340 modül). Kalemin asıl işi değişmemiş: 40 dosyayı "davranış-çivisi mi metin-çivisi mi"
diye sınıflamak — metin-çivili dosyaları körlemesine eklemek mutasyon skorunu ŞİŞİRİR (bu turun
kendi davranışsızlık çivisi bile bu yüzden AST ile yazıldı, dizgiyle değil). Ev olarak WP5-G doğru
adres: 2026-08-23 boşaltması suite-hijyeni kalemlerini (Ö-32 suite-içi gerçek ağ çağrısı, Ö-35a)
zaten oraya koydu ve ritüelin sahibi (`ops/haftalik_mutasyon.sh`) WP5'in ölçüm-altyapısı alanına
girer. Kart gerekmez: eşik yok, K harcayan hipotez yok — sınıflama emeği var.

## Ö-30 — Ayrılmaz çiftin iki yarısı farklı yedek davranışında

**Önerilen sınıf: ARŞİV ADAYI — kalem BAYAT, iş gövdesi kapanmış.**
Kalemin şart koştuğu düzeltme bugün kodda ve çivili: `config.py:364` `"position_size_r": 0.5`
(modül başlığı :14 "canlı yüzeyle hizalı 0.5'tir" diye beyan ediyor; :319-339 bloğu "NEDEN 1,0
DEĞİL 0,5 — bu yedek CANLIYLA AYRIŞIKTI" gerekçesini ve operatörün 2026-08-12 §E.1 karar kaynağını
yazıyor), çivi `tests/test_wp2d_pano_beyani_v246.py:349` `BEKLENEN_BOYUT = 0.5`. Kalemin "hiçbir
test 1.0'ı çivilemiyor" ölçümü de bu düzeltmeyle tersine dönmüş: artık 0,5 çivili. Üç
`default_strategy()` kullanıcısı (run.py ilk koşum, mutation.py kum havuzu, yedek düşüşü) tek
kaynaktan beslendiği için üçü birden hizalanmış — kalemin "hangisi İSTENEN" karar sorusu fiilen
cevaplanmış (operatör kararına bağlandı). Sahip belirsizliği (WP2 mi WP6 mı) de düşmüş durumda:
WP2 cephesi 2026-08-22'de "TAM KAPANDI" ilan edildi ve bu düzeltme o kapanışın (WP2-D) içinde.
Rol-1'in yapacağı tek şey kalemi üstü-çizili kapatıp §7'ye kapanış izini yazmak.

## Ö-42 — Çapa deseni: satır çapası sessiz çürür, sembol çapası sesli

**Önerilen sınıf: WP6'ya taşıma adayı (codelaw iş kalemi); (1)/(3) adımları çalışma-kuralı notu.**
Açık iş gövdesi bugün de duruyor: önerinin (2) adımı `codelaw`a genel `capa_uyusmasi()` tarayıcısı
— **bugün `meridian/codelaw.py`de yok** (grep 0). Sayı tarafında dürüst bir uyumsuzluk beyanı
gerekiyor: kalem "meridian/ içinde 138 çapa" der; bugün `dosya.py:SATIR` biçimli çapayı
`grep -Eo '[A-Za-z0-9_/]+\.py ?:[0-9]+'` ile saydığımda meridian/*.py'de **17** buluyorum. 138'in
yöntemi belgelenmemiş (muhtemelen daha geniş desen ya da o günkü ağaç); sayı yeniden üretilemedi —
ama sayının küçülmesi SINIFI kapatmaz: bayat satır-çapası vakaları gerçek ve yaşanmış
(`state/goal.yaml:140`taki "A17: eski `:352`/`:359` çapaları bayattı" düzeltme izi bu sınıfın
kanıtı olarak bugün de yerinde). Ev olarak WP6 doğru adres: tarayıcı bir bütünlük/denetim
mekanizmasıdır ve codelaw'ın diğer tarayıcıları (artifact_graph, DECLARED_* doğrulamaları)
WP6'nın (Sistem Bütünlüğü) alanında yaşıyor. (1) "yeni çapalar `modül.sembol`" ve (3) "eskiler
çevresi düzenlendikçe dönüştürülür" adımları iş kalemi değil çalışma kuralıdır — Rol-1 uygun
görürse §0/H hattı notuna bir satır.

## Ö-43 — Yanlışlanan iddianın üçüncü örneği veriye yazılmıştı

**Önerilen sınıf: DERS KAYDI → arşiv adayı; ders WP6-E ailesine tek satır not.**
Kalemin iki somut kuyruğu da bugün kapanmış görünüyor: (1) `sermaye.py` reset-notu düzeltmesi
kodda (bugün :542 civarındaki yorum "eski cümle 'nokta eklenmez ÇÜNKÜ eğrinin son noktası tohum
sınırıdır' diyordu" diye düzeltmeyi tarihçeliyor; `state/`e yanlış iddia yazan cümle üretimden
çıkmış); (2) "rapor edildi, düzeltilemedi" denilen bayat `goal.yaml:130` çapası da sonradan
kapanmış — bugün `state/goal.yaml:140` doğru hedefi (`guard.py:386 sector_cap_basis`) gösteriyor
ve eski `:352`/`:359` çapalarının bayat olduğunu A17 iziyle kendisi beyan ediyor. Geriye yalnız
ders kalıyor: "beyan-çürümesi taraması yorumlara değil, koda gömülü METİN ÜRETEN yazımlara da
uygulanmalı." Bu ders sahipsiz değil artık — Ö-49 sınıfının süpürme yöntemi (çapa çarpıştırma,
`docs/DENETIM-BAYAT-BEYAN-SUPURME-2026-08-23.md`) ve Ö-38/Ö-34 ile birlikte beyan-çürümesi ailesi
2026-08-23'te **WP6-E**'de toplandı. Öneri: Rol-1 dersi WP6-E gövdesine tek satır ("metin-üreten
yazımlar da tarama kapsamında") olarak işler, kalemi arşivler.

## Ö-33 — Kardeş ajan pytest çakışması (orkestrasyon dersi)

**Önerilen sınıf: ARŞİV ADAYI — ders kurumsallaşmış, açık iş gövdesi yok.**
Kalem kendini zaten "(Rol-1 çalışma kuralı; ROADMAP'e kayıt amaçlı)" diye tanımlıyor ve kuralın
üç kalıcı evi bugün yerinde: `CLAUDE.md` madde 6 ("tam suite yalnız Rol-1'de tek-otoriter;
ajanlar kapsam testi koşar"), oturum-hafızası kaydı ("Paralel ajan test çakışması — dosya-ayrıklığı
YETMEZ, state/ paylaşımlı") ve kodun kendi belge bloğu (`hermes.py:410-419` bu çakışma sınıfını
kalemin yazıldığı gün bile belgeliyordu). Yani kaydın taşıdığı bilgi üç ayrı otoriter yüzeyde
yaşıyor; §4'te dördüncü bir kopya olarak durması, tam da bu deponun kapattığı "aynı gerçeğin ikinci
metni sessizce bayatlar" sınıfını üretir. Taşınacak WP yok, kart yok, ölçüm yok — Rol-1 üstü
çizip §8 arşivine (ders satırıyla) indirebilir.

## Ö-46 — 28f: teyit/arama deliği iki nüshalıydı, fail-closed kapatıldı

**Önerilen sınıf: ARŞİV ADAYI — ders kaydı; düzeltme kodda yerinde, kalan iş yok.**
Kalemin gövdesi zaten "düzeltildi"nin raporu: üç değerli (geçti/geçmedi/ölçülemedi), fail-closed,
eşiklere dokunulmadı. Bugünkü kod bunu taşıyor: `reflect.py` :563-565 `evaluate_search` dönüşünde
"İKİ SEBEPLE `law=\"legacy\"` döner ve ikisi AYNI ŞEY DEĞİLDİR" ayrımını (dilim-yok ↔
dilim-var-ölçemedim) açıkça işliyor; :354 dilim-yok dalının sözleşmesi yazılı. "Ayrım sınırı
bilinçli" beyanı (olmayan sınavdan kalınmaz — fail-closed yalnız "yasa yürürlükte, ölçüm yok"
hâline biner) kalemin içinde kayıtlı ve kodla tutarlı. Tek açık uç tarihçe niteliğinde: geçmiş
vaka H00029 → v0003 **bilerek** retro-düzeltilmedi (tarihçe-koru) — bu bir iş kalemi değil, bir
kayıt. Sınıf komşusu Ö-45 ("28d teşhisi") 2026-08-23'te KART ADAYI etiketi aldı; Ö-46'nın ondan
farkı, planı değiştiren açık bir ölçüm sorusu TAŞIMAMASI. Rol-1 kapanış iziyle arşive indirebilir.

---
*Ölçüm ajanı damgası: bu belge envanter + öneridir; ROADMAP'e, kartlara ve koda (bu kalem
kapsamında) dokunulmadı. Taşıma/kapatma hükümleri Rol-1'de.*
