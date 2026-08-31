# Ajan kalıcı hafıza katmanı — dört aday kıyası (2026-08-31)

**Yazan:** araştırma ajanı (Rol-1 değil). **Okuyan:** Rol-1 / operatör — karar bu dosyada VERİLMEZ,
malzemesi hazırlanır. **Kapsam:** SALT ARAŞTIRMA. Hiçbir şey kurulmadı, hiçbir kaynak dosya
değiştirilmedi, pytest/git koşulmadı.

**Ölçüm künyeleri:** yıldız/lisans/son-itiş sayıları GitHub REST API'den 2026-08-31'de okundu.
README/doküman iddiaları satıcının KENDİ beyanıdır ve öyle etiketlendi — bağımsız doğrulanmadı.
Sayı taşıyan her satır bu tarihi taşır.

---

## 0. İki ad belirsizliği — önce onlar

**"memo" → mem0 (`mem0ai/mem0`).** Arama "memo" adlı ayrı bir ajan-hafıza projesi göstermedi.
Yakın adaşlar var ve karıştırılabilir: `MemTensor/MemOS`, `MemoriLabs/Memori`, `BAI-LAB/MemoryOS`.
Hiçbiri operatörün tarif ettiği "dört aday" listesinin bilinen üyesi değil ve hiçbiri mem0
kadar baskın değil. **Hüküm: "memo" = mem0.** Aksini düşündüren bir şey varsa operatör söylemeli.

**"Hindsight" → `vectorize-io/hindsight` (Vectorize).** GitHub'da aynı adı taşıyan birden çok depo
var, ama üçü (`McBorisson/AGENT-MEMORY-Hindsight`, `iosub/HERMES-hindsight`,
`mcp-research/vectorize-io__hindsight`) aynı üst-akımın klonu/aynası. Özgün ve bakımı yapılan
depo `vectorize-io/hindsight`. **Belirsizlik düşük ama sıfır değil** — arXiv 2512.12818 ("Hindsight
is 20/20") aynı ekibin makalesi olarak görünüyor, doğrulanmadı.

---

## 1. Ölçülmüş künye tablosu (GitHub API, 2026-08-31)

| | mem0 | Honcho | Hindsight | Supermemory |
|---|---|---|---|---|
| Depo | `mem0ai/mem0` | `plastic-labs/honcho` | `vectorize-io/hindsight` | `supermemoryai/supermemory` |
| Yıldız | **64.421** | 6.960 | 21.959 | 29.161 |
| Fork | 7.552 | 862 | 1.683 | 2.546 |
| Lisans | Apache-2.0 | **AGPL-3.0** | MIT | MIT |
| Ana dil | Python | Python | Python | **TypeScript** |
| Doğum | 2023-06-20 | 2023-09-10 | **2025-10-30** | 2024-02-27 |
| Son itiş | 2026-08-31 | 2026-08-29 | 2026-08-31 | 2026-08-29 |
| Açık konu | 706 | 161 | 110 | 174 |
| Arşivli | hayır | hayır | hayır | hayır |

Dördü de canlı bakımda — "terk edilmiş" eleme kriteri hiçbirini elemiyor.

---

## 2. mem0 (`mem0ai/mem0`)

**Ne:** LLM ajanlarına takılan "evrensel hafıza katmanı". Konuşma metninden LLM ile olgu çıkarır,
vektör deposuna yazar, sonraki çağrılarda geri getirir. Üç katman sunuyor: gömülü Python
kütüphanesi · Docker'lı self-host yığın · yönetilen bulut. En büyük ekosistem, en çok yıldız.

| Eksen | Hüküm |
|---|---|
| 1. Self-host | ✔ Apache-2.0, gömülü Python kütüphanesi; varsayılan Qdrant DİSK ÜSTÜ (`/tmp/qdrant`) + SQLite geçmiş (`~/.mem0/history.db`) — **ayrı sunucu şart değil**. Docker yığını opsiyonel. |
| 2. Filo bedeli | ✔ **En düşük.** Süreç içine gömülür; yeni systemd birimi, sağlık kapısı, ayrı yedek hikâyesi GEREKMEZ. Yedek = iki dosya yolu. |
| 3. Enjeksiyon | ⚠ LLM çıkarımlı serbest metin; **ADD-only** — olgular üzerine yazılmadan birikir, yani kirlenme MONOTONdur, silinene kadar kalıcı. Kaçış var: `infer=False` ham/şemalı yazımı mümkün kılar, `get_all`/`delete` denetlenebilir yüzey verir. Yazan kontrolü ancak BİZ kurarsak var. |
| 4. Çok-ajan | ✔ **En temiz eşleşme.** `user_id` + `agent_id` + `run_id` üçlüsü — kaynakta ölçüldü (`mem0/memory/main.py`, `ENTITY_PARAMS = frozenset({"user_id","agent_id","run_id"})`); en az biri zorunlu. sef/bekci/karne/ana → `agent_id`, tur → `run_id`. |
| 5. LLM bağı | ⚠ Varsayılan OpenAI (`gpt-5-mini` + `text-embedding-3-small`); sağlayıcı takılabilir (Ollama vb.). Ama **her `add()` bir LLM çıkarım çağrısı + embedding çağrısı**dır — yazma başına maliyet, kota etkisi gerçek. |
| 6. Olgunluk | ✔ 64.4k yıldız, Apache-2.0 (ticari kısıt yok), YC S24, Python-yerli. ⚠ **Graph memory ücretli Pro'ya kapalı**; topluluk raporları self-host dokümanını "seyrek" buluyor (üçüncü taraf iddiası, doğrulanmadı). |

**Meridian'a uyum:** Filo bedeli açısından dördün en ucuzu ve tek gerçek "kütüphane" adayı — bu
büyük. Kimlik modeli bot filosuna birebir oturuyor. Ama `infer=False` ile yazan kontrolünü geri
aldığımız anda geriye kalan şey "kendi yazdığımız metnin üstünde bir vektör indeksi"dir; o zaman
soru şu olur: bunun için bir bağımlılık mı, yoksa sqlite-vec + kendi şemamız mı?

---

## 3. Honcho (`plastic-labs/honcho`)

**Ne:** "Değişen insanları, ajanları, grupları zaman içinde anlayan durumlu ajanlar" için hafıza
altyapısı. Ham mesajları saklar, ARKA PLANDA bir "deriver" işçisiyle üzerlerinde akıl yürütür ve
her (gözlemleyen, gözlenen) çifti için bir temsil çıkarır. Kavramsal olarak en iddialısı.

| Eksen | Hüküm |
|---|---|
| 1. Self-host | ✔ Var (docker-compose / `honcho start`), ama bedeli ağır: **Postgres + pgvector VE Redis VE ayrı deriver işçi süreci**. Yönetilen bulut da mevcut. |
| 2. Filo bedeli | ✘ **En yüksek.** api + deriver + Postgres + Redis → 3-4 systemd birimi, 3-4 sağlık kapısı, iki ayrı yedek hikâyesi (pg dump + redis). |
| 3. Enjeksiyon | ✘ **En zayıf yazma-yolu kontrolü — ve bu bir kusur değil, ürünün TANIMI.** Ne yazılacağına uygulama değil deriver karar verir; ajan hakkında özerk çıkarım yapmak Honcho'nun varlık sebebidir. Meridian profillerinin yasakladığı şeyin tam adı bu. |
| 4. Çok-ajan | ✔ **Kavramsal olarak en zengini.** workspace / peer / session; peer'lar insan da ajan da olabilir, gözlem izinleri çift bazında ayarlanır, scope'lar geri-çağırmayı sınırlar. Dört bot + pano sohbeti için fazlasıyla yeterli. |
| 5. LLM bağı | ✘ Gemini/Anthropic/OpenAI yapılandırılabilir, ama deriver **mesaj başına sürekli arka plan LLM çağrısı** yapar. Eşzamansız olduğu için bütçelemesi de zor — jeton maliyeti öngörülemez. |
| 6. Olgunluk | ⚠ 6.960 yıldız (dördün en azı), Python SDK (`honcho-ai`) var, aktif. **Lisans AGPL-3.0 — dördün tek copyleft'i ve tek ağ-şartlı olanı.** Değiştirilip ağdan erişilebilir kılınırsa kaynak sunma yükümlülüğü doğar; Meridian'ın herkese açık bir yüzeyi (landing / `/api/public/summary`) olduğu için bu bayrak boş değil, hukuk sorusu operatörde. |

**Meridian'a uyum:** En kötü. Ürünün çekirdek vaadi — "model konuşmadan kendi başına sonuç
çıkarsın" — Meridian'ın uydurma yasağıyla ve bot profillerinin yazılma gerekçesiyle DOĞRUDAN
çelişiyor. Üstüne en pahalı filo bedeli ve tek lisans bayrağı.

---

## 4. Hindsight (`vectorize-io/hindsight`)

**Ne:** "Zamanla öğrenen ajanlar" için hafıza sistemi; konuşma geçmişi geri getirmeye değil
öğrenmeye odaklandığını söylüyor. Üç fiil: **retain** (LLM'le olgu/varlık/ilişki çıkar), **recall**
(semantik + BM25 + graf + zamansal, dört koldan arama ve cross-encoder yeniden sıralama),
**reflect** (mevcut hafızadan yeni bağlantı sentezle).

| Eksen | Hüküm |
|---|---|
| 1. Self-host | ✔ **Tam self-host, MIT.** Docker (gömülü Postgres'li tek konteyner mümkün), compose, `pip install hindsight-api`, Helm. **Postgres + pgvector**; ayrı vektör DB gerekmez. Bulut opsiyonel. |
| 2. Filo bedeli | ⚠ **Orta-yüksek.** REST API'li ayrı bir servis → 1 yeni systemd birimi + sağlık kapısı + pg yedek hikâyesi. Honcho'dan hafif (Redis yok, ayrı işçi yok), mem0'dan ağır. |
| 3. Enjeksiyon | ⚠ Yazım yine LLM çıkarımlı — **ama dördün en denetlenebiliri.** Çıktı "observation" (kanıtlı, ispat-sayılı, güven skorlu inanç) olarak yapılanır: bir iddia onu doğuran retain olaylarına geri izlenebilir ve tek bir enjekte cümlenin ispat sayısı düşük kalır. Ayrıca **"Memory Defense"** — 45 desenle sır/PII taraması (opt-in) — dörtte açık bir sızıntı kontrolü sunan TEK aday. Metadata filtresiyle erişim kısıtı. |
| 4. Çok-ajan | ⚠ **bank** başına izole depo (kullanıcı/ajan/proje). Dört bot = dört bank, temiz. Ama **belgelenmiş bir session/run modeli yok** — tur bazlı kapsama metadata ile elle kurulur. mem0'ın `run_id`'sinden zayıf. |
| 5. LLM bağı | ✔ **En geniş.** 25+ sağlayıcı; OpenAI-uyumlu uç noktalar, LiteLLM/LiteLLMRouter geçidi, yerel (Ollama/LMStudio/LlamaCPP). **OpenRouter buradan sorunsuz geçer.** LLM anahtarı ZORUNLU. |
| 6. Olgunluk | ⚠ MIT (ticari kısıt yok), Python, `hindsight-client` + Node/Go/CLI, bank başına gömülü MCP uç noktası. 21.959 yıldız — ama depo **2025-10-30 doğumlu, dördün EN GENCİ**: en az savaş görmüş olan. mem0/Zep/LangMem'i yendiği iddiası **satıcının kendi ölçümü**, bağımsız doğrulanmadı. |

**Meridian'a uyum:** Kültüre en yakın aday. Kanıt-ispat-güven üçlüsü Meridian'ın "ÖLÇÜLDÜ /
ÇIKARSANDI — açıkça" refleksiyle aynı dili konuşuyor ve dörtte bir iddianın kaynağını
gösterebilen tek sistem. Bedeli: yeni bir servis birimi ve 10 aylık bir bağımlılık.

---

## 5. Supermemory (`supermemoryai/supermemory`)

**Ne:** "AI için hafıza ve bağlam katmanı" — konuşmalardan olgu çıkarır, kullanıcı profili tutar,
çelişkileri ve güncellemeleri yönetir, süresi geçeni düşürür. Ürün olarak hem barındırılan API
hem de "tek ikili, sıfır yapılandırma" yerel koşum sunuyor.

| Eksen | Hüküm |
|---|---|
| 1. Self-host | ✔ MIT; motor depoda (`packages/memory-graph` ölçüldü, monorepo'da `apps/web`, `apps/mcp` da var). Yerel koşum tek ikili + `./.supermemory` dizini; **dış altyapı gerekmez**, embedding varsayılanı YEREL (`Xenova/bge-base-en-v1.5`). |
| 2. Filo bedeli | ⚠ **Orta.** Tek daemon, kendi veri dizini, yedek = bir dizin. Ama **TypeScript/Node çalışma zamanı** — Python + systemd filosuna İKİNCİ bir dil/çalışma zamanı sokar; sürüm, güvenlik yaması ve sağlık kapısı ayrı bir dünyada yaşar. |
| 3. Enjeksiyon | ⚠ Yazım LLM çıkarımlı serbest metinden yapılanmış olgu. **Tek otomatik bayatlık kontrolü burada** (çelişki çözümü + otomatik süre dolumu) — bu gerçek bir artı. Ama kanıt/provenans izi Hindsight kadar açık değil; yazan kontrolü belgelerde net değil (ÖLÇÜLMEDİ). |
| 4. Çok-ajan | ✘ **`containerTag`** ile düz etiket bazlı ayrım ("müşteriye, repoya, her neye göre"). İşi görür ama dördün en zayıf biçimsel ayrımı — ne oturum ne gözlemci/gözlenen kavramı var. |
| 5. LLM bağı | ✔ **En ucuzu.** LLM: OpenAI/Anthropic/Gemini/Groq veya herhangi bir OpenAI-uyumlu uç (OpenRouter geçer). Embedding: **varsayılan YEREL** → geri getirme dış embedding maliyeti SIFIR. Ollama ile tamamen çevrimdışı mümkün — dörtte bunu yapabilen tek aday. |
| 6. Olgunluk | ✔ 29.161 yıldız, MIT, aktif. ⚠ TypeScript-yerli; Python SDK var (`pip install supermemory`) ve `baseURL`'i `http://localhost:6767`e çevirerek self-host örneğine bağlanıyor — yani Python entegrasyonu **HTTP istemcisi**, kütüphane değil. |

**Meridian'a uyum:** Maliyet ekseninde çekici (yerel embedding + tek ikili). İki şey engel: yabancı
çalışma zamanı ve düz etiketli kimlik ayrımı. Dört ayrı bot kimliği + ilerde pano sohbeti için
`containerTag` yeterince keskin bir sınır değil.

---

## 6. Çapraz tablo — altı eksen

| Eksen | mem0 | Honcho | Hindsight | Supermemory |
|---|---|---|---|---|
| 1. Self-host | ✔ kütüphane | ✔ ağır yığın | ✔ servis+pg | ✔ tek ikili |
| 2. Filo bedeli | **✔ en düşük (birim yok)** | ✘ en yüksek (3-4 birim) | ⚠ 1 birim + pg | ⚠ 1 birim, yabancı runtime |
| 3. Enjeksiyon kontrolü | ⚠ ADD-only, `infer=False` kaçışı | ✘ özerk çıkarım = tanımı | **⚠ en denetlenebilir (kanıt+güven+PII tarama)** | ⚠ çelişki/süre var, provenans zayıf |
| 4. Çok-ajan | **✔ user/agent/run** | ✔ peer/session/scope | ⚠ bank, oturum yok | ✘ düz etiket |
| 5. LLM bağı | ⚠ yazma başına LLM+embed | ✘ sürekli arka plan LLM | ✔ 25+ sağlayıcı, OpenRouter ✔ | **✔ yerel embedding, çevrimdışı olabilir** |
| 6. Olgunluk/lisans | ✔ 64k, Apache-2.0 (graph ücretli) | ⚠ 7k, **AGPL** | ⚠ 22k, MIT, **10 aylık** | ✔ 29k, MIT, TS-yerli |

---

## 7. "HİÇBİRİ" — masada, ve dürüstçe en güçlü seçenek

Bu seçenek nezaketen yazılmıyor. Depo bu soruya **zaten bir kere cevap vermiş** ve cevabını
gerekçesiyle çivilemiş.

**Ölçülen olgu:** `@sef`, `@bekci`, `@karne` — üç botun ÜÇÜNDE de `agent.disabled_toolsets`
listesinde `memory` var. Gerekçe profillerde yazılı ve üç maddeli:

- (a) hermes hafıza deposu `HERMES_HOME/memories/` altına, yani **safe-root'un DIŞINA** yazar;
- (b) açmak safe-root'u profil evine genişletmeyi zorunlu kılar ve **botun kendi guard
  yapılandırmasının üstüne yazma yolunu yeniden açar** (kendini silahsızlandırma);
- (c) profile özel üçüncü sebep, ve **en ağırı odur** — `@bekci`nin kendi sözleriyle:
  *"Hafızası olduğunu sanan bir model 'bu dün de böyleydi' cümlesini UYDURUR — ve o cümle tam
  olarak botun tek işidir."* `@karne`de aynısı: *"bu botun mesajının EN DEĞERLİ parçası 'GEÇEN
  HAFTAYA GÖRE NE DEĞİŞTİ' cümlesidir. Hafızası olduğunu sanan bir model o cümleyi UYDURUR."*

**Dört adayın DÖRDÜ de tam olarak (c)'nin tarif ettiği şeydir:** girdiden LLM ile çıkarılmış
serbest metni saklayıp sonraki koşumun prompt'una geri koyan sistemler. Hiçbirinin BİRİNCİL yolu
"yalnız harness yazar, sabit şemayla" değil. Yani üçünü de kurmak, üç botun kapattığı deliği
**dışarıdan yeniden açmaktır** — üstüne (a) ve (b)'nin yerine yeni bir ağ yüzeyi ve yeni bir
yazılabilir depo koyarak.

**Ve yerine konan şey zaten var, üstelik daha iyi.** Depo "geçen sefere göre ne değişti" sorusunu
HATIRLAYARAK değil **ÖLÇEREK** cevaplıyor: harness kendi damga dosyasını tutar
(`state/karne_brifingi_damga.json`, `state/bekci_brifingi_damga.json` — **sahibi HARNESS**, botun
safe-root'u `/opt/meridian/var/bots/<ad>`, oraya yazamaz), değişimin kimliğini üçlü olarak sabitler
`(hukum, deger, esik)`, gerekçeyi kasten kimliğin DIŞINDA bırakır (yoksa her hüküm her hafta
"DEĞİŞTİ" görünürdü), ve `OLCULEMEDI→ölçüldü` / `ölçüldü→OLCULEMEDI` geçişlerini ayrı ve
öncelikli bir sınıf sayar. Bu desen dört adayın hiçbirinin vermediği üç şeyi veriyor: **yazan
tek ve bot değil · şema sabit ve çivili · körleşme kendisi bir sinyal.**

**Dış katmanın marjinal değeri, dürüstçe:** bugünkü işlerde **yok denecek kadar az.** Dört botun
sorduğu sorular SABİT ve ÖLÇÜLEBİLİR; onlara semantik geri getirme değil deterministik hesap
lazım. Dış katman ancak Meridian'ın bugün SAHİP OLMADIĞI bir işte kazanır:

> **büyük, yapılandırılmamış bir metin yığını üzerinde serbest-biçimli semantik geri getirme** —
> örn. "Haziran'da IWM hakkında ne sonuca varmıştık?" tipi pano sohbeti, ya da mühendislik
> günlüğü + kart arşivi + devir brief'leri üzerinde arama.

O iş bugün bir teslimat değil. **Öyleyse kural şudur: adayı seçmeden önce KARTI yaz.** İş
tanımlanmadan katman seçmek, çözüm arayan bir araç almaktır.

---

## 8. Sıralamam ve gerekçesi

**0. HİÇBİRİ (birincil tavsiye) → 1. Hindsight → 2. mem0 → 3. Supermemory → 4. Honcho.**

Birincil tavsiyem hiçbiri, çünkü bu kıyasın altı ekseninden en ağırı üçüncüsüdür ve üçüncü eksende
dört adayın dördü de aynı yapısal kusuru taşıyor: hafızaya giren şey LLM'in girdiden çıkardığı
serbest metindir, ve o metin sonraki koşumun prompt'una geri döner — yani depo üç botun
`disabled_toolsets`'inde `memory` satırını yazarken kapattığı deliğin ta kendisi, dışarıdan
yeniden açılmış hâli; üstelik karşılığında alınan "geçen sefere göre ne değişti" yeteneği depoda
zaten var ve HATIRLANMIŞ değil ÖLÇÜLMÜŞ hâlde (harness sahipli damga, üçlü kimlik, botun yazma
yetkisi sıfır), yani takas "yok olan bir yeteneği kazanmak" değil "ölçülen bir yeteneği hatırlanan
bir yetenekle değiştirmek"tir ve o yönde her adım uydurma yasağının ters yönüdür. Yine de bir
gün semantik geri getirme gereken gerçek bir iş doğarsa — pano sohbeti ya da günlük/kart arşivi
üzerinde arama — sıralamam **Hindsight**'la başlar: MIT, tek Python servisi + Postgres, ve
dörtte bir iddiayı kanıtına geri izleyebilen tek sistem (kanıt + ispat sayısı + güven skoru), üstüne
45 desenli sır/PII taraması ve OpenRouter'ın sorunsuz geçtiği 25+ sağlayıcı — yani üçüncü eksendeki
ortak kusuru en azından DENETLENEBİLİR kılan tek aday, ki depo defalarca "provenans için bedel
öde" tarafını seçmiştir. **mem0** hemen arkasında ve tek bir eksende ondan üstün: süreç içine
gömülür, yani yeni systemd birimi/sağlık kapısı/yedek hikâyesi getirmez ve `user_id`+`agent_id`+
`run_id` üçlüsü dört bota birebir oturur — ama `infer=False` ile yazan kontrolünü geri aldığımız
anda geriye "kendi yazdığımız metnin üstünde bir vektör indeksi" kalır, ki o zaman sqlite-vec +
kendi şemamız daha az bağımlılıkla aynı işi yapar; graph'ın ücretli tarafta olması da OSS
vaadini inceltiyor. **Supermemory** üçüncü, çünkü maliyet ekseninde en iyisi (yerel embedding,
tek ikili, çevrimdışı mümkün) ama Python/systemd filosuna ikinci bir çalışma zamanı sokuyor ve
düz `containerTag` ayrımı dört bot + pano için yeterince keskin bir sınır değil. **Honcho** sonuncu
ve tereddütsüz: en pahalı filo bedeli (Postgres + Redis + deriver + api), dörtteki tek AGPL —
Meridian'ın herkese açık bir yüzeyi olduğu için boş olmayan bir hukuk bayrağı — ve en önemlisi,
çekirdek vaadi olan "ajan hakkında özerk arka plan çıkarımı" tam olarak bot profillerinin
yasaklamak için yazıldığı davranıştır: kusuru bir hata değil, ürün tanımıdır.

---

## 9. ÖLÇÜLMEDİ — açık kalanlar

Bunlar bu turda ölçülmedi; karara girmeden önce ölçülmeli:

1. **Hiçbir aday kurulmadı, hiçbiri koşturulmadı.** Tüm davranış iddiaları satıcı dokümanından.
2. **Hindsight'ın kıyaslama iddiası** (mem0/Zep/LangMem'i geçtiği) satıcının kendi ölçümü.
3. **Supermemory'nin `curl | bash` ile dağıttığı ikilinin** depodaki kaynaktan mı üretildiği
   doğrulanmadı — MIT etiketi depoya ait, ikiliye ait olduğu ölçülmedi.
4. **mem0'ın `infer=False` yolunun** gerçekten LLM çağrısını atlayıp ham metni sakladığı
   kaynaktan doğrulanmadı (dokümandan okundu).
5. **Honcho'nun AGPL-3.0 §13'ünün** "ayrı servis olarak çağırma" senaryosunda ne getirdiği
   hukuk sorusudur, mühendislik sorusu değil — operatörde.
6. **Ölçüm kartı yok.** §5 gereği: kart yoksa ölçüm kodu yok. Bu dosya bir kıyastır, ölçüm
   değildir; herhangi bir adayın Meridian'da denenmesi ÖNCE bir kart ister
   (hipotez, eşik, kill-list, başarı tanımı).
