# Tasarım — Hindsight entegrasyonu (tetikli; Ajan-B + ölçülmüş semantik-arama ihtiyacı)

Durum: TASARIM (kod yok, kurulum yok). Tetik: Ajan-B indikten sonra semantik-arama ihtiyacının
ölçülmesi. Uygulama KART-ÖNCE başlar (aşağıda taslak eşikler). Aday kıyası:
docs/DEGERLENDIRME-HAFIZA-ADAYLARI-2026-08-31.md (sıralama: HİÇBİRİ→Hindsight→…).

## 0. Tek cümlelik şekil

Hindsight, A1'de localhost'a kilitli TEK içsel servis olarak koşar; ona YALNIZ bizim harness
kodumuz yazar (botlar asla), okuma yalnız `api.py` üzerinden çitli bağlam olarak akar; `reflect`
kapalı doğar; her cevap provenansıyla (kanıt + ispat sayısı + güven) panoda görünür.

## 1. Yerleşim ve filo bedeli (beyanlı)

- A1'de kurulum biçimi RESMÎ BEST PRACTICE'e göre seçilir (docker dahil — operatör 2026-08-31:
  "direk reddetme, best practice ne diyorsa onu yapacağız"; önceki "Docker YOK/filo kararı"
  cümlesi Rol-1'in aşırı-genellemesiydi — hermes-terminal kararı o bağlama özgüydü, DÜZELTİLDİ).
  Tercih ilkesi: genel sisteme katkı sağlayabilecek bileşenler (örn. Postgres) uygulama
  seviyesinde/native kurulmaya ADAY; karma senaryo (api konteynerde + pg native) resmî destekliyse
  masada. Somut hüküm docs/INCELEME-HINDSIGHT-DERIN-2026-08-31.md raporundan gelir.
  Her durumda: `127.0.0.1` bind — dışa kapalı; tek giriş kapısı api.py proxy'si.
- Filo disiplini tam uygulanır: iki birim + sağlık kapıları (healthz + pg isalive) + F9 kaydı +
  YEDEK HİKÂYESİ: gecelik `pg_dump` timer'ı → `backups/` (litestream SQLite'a özgü — pg'de dump).
- Kaynak beyanı: A1 4-çekirdek ARM, RAM 12GB (operatör 24GB'ye yükseltebilir — hüküm inceleme raporunda,
  iki senaryolu); pg+hindsight boşta hafif, retain anları LLM-bağımlı.
  Sprint pencereleriyle çakışma ölçülür (kartta).

## 2. Bank yapısı (kimlik ayrımı)

| bank | içerik | yazan |
|---|---|---|
| `sef` / `bekci` / `karne` | o botun TESLİM metinleri + damgaları | harness (teslim anında) |
| `ana` | ana beynin karar/yansıma özetleri | harness (reflect döngüsü sonrası) |
| `operator-sohbet` | Ajan-B konuşma turları | api.py sohbet ucu |
| `arsiv` | günlük/kart/karar belgeleri (git-sha'lı) | batch ingest (Rol-1 komutu) |

Metadata sözleşmesi: `kaynak_tur` (teslim/sohbet/belge/karar) · `ts` · `yol` · `git_sha`
(belgelerde) · `damga` alanları. Sözleşme çivilenir (v-serisi).

## 3. Yazım yolu — kapı felsefesi (tasarımın kalbi)

- **BOTLAR HİNDSIGHT'A ERİŞMEZ.** Bot duruşu (memory disabled, tek-atışlık, "dünü bilmiyorsun")
  DEĞİŞMEZ — hafıza botlara değil, PANO/SOHBET katmanına ve operatöre hizmet eder. Botların
  SOUL gerekçesi ("hafızası olduğunu sanan model uydurur") yürürlükte kalır.
- **retain'i yalnız harness çağırır**, belirlenmiş üretim noktalarından (tablo §2). Ajanın
  "aklına geleni" yazma yolu YOK — Honcho'yu eleyen özerk-çıkarım sınıfı kapıdan girmez.
- **reflect KAPALI doğar** (özerk sentez = ayrı kart + operatör kararı; açılırsa önce gölge).
- **Memory Defense AÇIK** (45-desen sır/PII taraması) + bizim VERI-çiti: retain'e giden her
  metin zaten çitli kaynaklardan gelir; çit dışı talimat metni veri olarak saklanır.
- Enjeksiyon-kalıcılaşma sigortası (Hindsight'ın seçilme sebebi): sızan tek cümle düşük
  ispat-sayılı observation kalır; panoda provenansı görünür olduğundan denetlenebilir.

## 4. Okuma yolu

- **Ajan-B sohbeti:** operatör sorusu → api.py sohbet ucu → `recall` (ilgili bank + arsiv;
  semantik+BM25+graf+zamansal) → sonuçlar VERI-çitiyle hermes tek-atışlık çağrısına bağlam →
  cevap + panoda "bu cevap şu kanıtlara dayandı" satırı (observation kimlikleri + güven).
- **Pano arama kutusu:** LLM'siz doğrudan recall — arşiv/karar araması ("EDG-042 kill#3
  istisnası ne zaman, neden?" sınıfı sorular).
- Ana beynin recall danışması: FAZ-3, ayrı kart (karar yüzeyine bağlanma sınıfı — probgate
  emsaliyle önce gölge).

## 5. Ölçüm kartı taslağı (tetik ateşlenince ön-kayıt)

- Hipotez: gerçek operatör soruları kümesinde (N≥30, önceden dondurulur) Hindsight recall'u,
  MINIMAL TABAN ÇİZGİye (sqlite-vec + kendi şemamız — "hiçbiri" seçeneğinin somut hâli) karşı
  doğru-pasaj isabetinde anlamlı üstün.
- Eşikler önden donuk: isabet farkı ölçülür; taban çizgiyi ANLAMLI geçemezse KALDI — basit
  çözüm kazanır (YAGNI). Maliyet sütunu zorunlu: retain başına token+gecikme, günlük kota payı.
- Kill: Memory Defense kapalı koşum geçersiz · bank-dışı okuma/sızıntı geçersiz · botlardan
  doğrudan erişim geçersiz · satıcı benchmark'ı kanıt olarak KULLANILAMAZ (kendi çözücümüz).
- PK: bilinen-cevaplı soru gerçek arşivde uçtan uca; negatif: çitli sahte-talimat metni
  cevaba TALİMAT olarak sızmaz, veri olarak raporlanır.

## 6. Aşamalar

- **Faz 0 — tetik ölçümü:** Ajan-B inince: operatör sorularının bugünkü araçlarla (grep/pano)
  karşılanamama oranı ölçülür. Karşılanıyorsa entegrasyon AÇILMAZ (kayıt düşülür).
- **Faz 1:** kurulum (2 birim + yedek + F9) → `arsiv` bank'ine batch ingest → pano arama
  (salt recall, LLM'siz). En düşük riskli dilim; kartın ana ölçümü burada koşar.
- **Faz 2:** `operator-sohbet` + teslim bank'leri → Ajan-B cevaplarına çitli bağlam.
- **Faz 3 (ayrı kart):** ana beyin danışması · reflect değerlendirmesi.

## 7. Değişmeyenler (açık beyan)

Bot duruşu ve SOUL kuralları · teslim/damga mekaniği · ship yetkisi (kapı) · VERI-çiti ·
"hatırlanan değil ölçülen" ilkesi — hafıza katmanı ölçülen defterlerin YERİNE değil,
üzerine arama katmanı olarak gelir. Karar günlüğü/kartlar SSoT kalır; Hindsight indeks'tir,
kayıt değil (çelişkide defter kazanır — tek-kaynak yasası).

## 8. Kapsam sorusu — "bütün altyapı için persistent memory olur mu?" (operatör, 2026-08-31)

KAYIT KATMANI OLARAK HAYIR — dört ilke birden engeller: karar-yolu determinizmi ("determinist
ve ağsız") · yeniden-üretilebilirlik (LLM çıkarımı deterministik değil — earnings-takvimi
PIT-değil vakasının sınıfı) · tek-kaynak (defter gerçeklerinin LLM-özetli ikinci kopyası ayrışır)
· uydurma yasağı (güven-skorlu "hatırlanan" ≠ "ölçülen").

İNDEKS KATMANI OLARAK EVET, SİSTEM-GENELİ: `arsiv` bank'i her defterin insan-okur izdüşümünü
kapsayacak şekilde büyüyebilir (kart hükümleri · karar günlüğü · mühendislik günlüğü vakaları ·
teslimler · incident'lar · suite/dağıtım beyanları) — hepsi harness-yazımlı, git-sha'lı,
kaynağına geri-bağlantılı. Öğrenme döngüsü Faz-3'te DANIŞABİLİR (cevap danışmadır, kapı
defterden karar verir). Sınır tek cümle: **okuyan herkes, yazan yalnız harness, karar veren
yalnız defter.** Gelecek kart bu bölümü kapsam-tanımı olarak devralır.

## 9. Genişleme menüsü (tetikli — çekirdek + taban-çizgi kill'i geçtikten SONRA)

Sınır aynı kaldıkça genişleme = bank/ingest kalemi (mimari değişmez). Değer sırasıyla:
1. NEDENSEL ZİNCİR: olay defteri ↔ karar günlüğü ↔ commit gövdeleri graf+zamansal bağlı —
   "alarm→müdahale→sonuç" sorguları (bugünkü elle-grep triyajlarının indeksli hâli).
2. COMMIT GÖVDESİ ARŞİVİ: neden-kaydı kültürü aranabilir olur.
3. SUITE/ARIZA HAFIZASI: kırmızı + kök neden + çözüm → tekrar-arıza teşhisi.
4. MÜKERRER-ÖNLEME (danışma): yeni öneri/kart taslağına benzerleri recall'dan gelir
   ("değerlendirildi-alınmadı" uyarısı — yeniden-tartışma önlenir).
5. ALARM-YANI VAKA BAĞLAMI: panoda alarmın yanında sınıfının son vakaları + çözümleri.
6. OTURUMLAR-ARASI ERİŞİM: /api üzerinden her Claude oturumu (cloud klonlar dahil — ~/.claude
   taşınamaz sınıfının panzehiri) aynı kurumsal hafızayı sorgular.

İKİ DİSİPLİN: her bank YASA 6'ya tabi (okuyucusuz bank açılmaz; recall sayacı kullanım ölçer,
okunmayan emekli — skill kataloğu emsali) · sıralama değişmez (çekirdek taban-çizgi kill'ini
geçmeden menü açılmaz; YAGNI hepsine şamil).
