# TASARIM — `sir_rotasyon.sh --db --vault`: Hindsight DB parolasının kasaya BAĞLANMASI (TSK-064 açık kalem)

Rol-1 (Fable), 2026-09-21 20:3xZ. Durum: TASARIM — kod yok, uygulama ayrı dilim (Opus implementer, kart-önce
değil ama ROADMAP-önce: TSK-064). Bu belge ÖLÇÜLMÜŞ zeminden yazıldı; her iddia yanında kaynağı var.

## 1. Ölçülmüş zemin (2026-09-21)
- Kasa TAM DSN taşır: `secret/meridian/HINDSIGHT_API_DATABASE_URL` → Agent render hedefi
  `/etc/hindsight/creds/HINDSIGHT_API_DATABASE_URL` (0400), tüketici `hindsight-api.service`
  (`LoadCredential`), render aralığı `RENDER_ARALIGI = "1m"` (`ops/vault_politika_uret.py`, `agent.hcl`
  `static_secret_render_interval`). Kaynak: `deploy/vault/agent.hcl`, `deploy/sir_envanteri.yaml`.
- Rotasyonun sırrı ise yalnız PAROLA alanıdır: `HINDSIGHT_DB_PAROLA` iki kopya — `tur: sql`
  (`ALTER ROLE hindsight PASSWORD`, SQL dosyası `psql -f` ile koşar, sonra silinir; parola argv'ye
  GİRMEZ) ve `tur: url` (DSN kopyası; YALNIZ parola alanı değişir, query korunur — `yaz-url`
  yardımcısı `urlsplit/urlunsplit`, kullanıcı+parola kodlanır). Kaynak: `deploy/sir_envanteri.yaml`
  `alt_komut: db` girdileri; `sir_rotasyon.sh` §"tür=sql / tür=url".
- Eski yol parolayı BETİK İÇİNDE üretir ve BASMAZ → kasa rotasyondan ÖNCE güncellenemez; bugün `--db`
  yalnız Agent hedefi UYARISI basar (`_agent_hedefi_uyarisi`, v521 A2/E), `--db --vault` YOK.
- Mevcut `--vault` akışı (bağlı sırlar için, `sir_rotasyon.sh` kasa döngüsü): sır başına
  (1) değeri OPERATÖRDEN ister (`vault_yeni`, üretmez) → (2) `_vault kv put <yol> value=-` (stdin,
  argv'de değer yok) → (3) render bekle: hedef dosyanın kanonik kopyası kasadaki değere `cmp -s` ile
  BİREBİR eşit olana kadar (tavan `VAULT_RENDER_TAVAN_S`; aşılırsa `olcum_yok` + ÖNCE DÖNEN SIR uyarısı)
  → (4) eski kanalları `_yaz` ile günceller → (döngü sonu) tüketici birimlerini yeniden başlatır →
  kanıt. Boş değer = sır ADIYLA atlanır; hepsi boşsa `die` (kasaya hiçbir şey yazılmaz).

## 2. Sorun: DSN'nin İKİ hakikat noktası var ve sıralama ölçülmemiş
Parola hem Postgres rolünde (`ALTER ROLE`, GERİ ALINAMAZ kanal) hem DSN'de (kasa → render → tüketici)
yaşar. İkisi aynı anda değişemez; arada bir PENCERE vardır ve pencerenin yönü sonucu belirler:
- **A) ALTER ROLE ÖNCE, kasa SONRA:** render tamamlanana kadar dosyada ESKİ parola, DB'de YENİ.
  Çalışan `hindsight-api` havuzdaki bağlantılarla sürer; ama bu pencerede bir restart/yeni bağlantı
  KESİN düşer. Pencere ≥ render aralığı (1 dk) + kuyruk. REDDEDİLİR.
- **B) Kasa ÖNCE, render kanıtı, ALTER ROLE SONRA:** render tamamlanana kadar dosyada YENİ parola,
  DB'de ESKİ. Çalışan servis yine havuzla sürer; yeni bağlantı bu pencerede düşer — ama pencere
  betiğin kendi kontrolünde ve KISA: render kanıtı `cmp` ile ölçülür ölçülmez `ALTER ROLE` koşar
  (saniyeler). Sonra restart → yeni parolayla bağlanır. SEÇİLİR.
Yani sıra: **kasa → render kanıtı → ALTER ROLE → restart → kanıt.** Geri alınamayan adım (ALTER)
en sona, restart'ın hemen önüne konur; ondan önceki her adım KV v2 sürümüyle geri alınabilir.

## 3. Akış (uygulanacak — `--db --vault`)
1. Ön kontrol: kasa mühürsüz, `secret/meridian/HINDSIGHT_API_DATABASE_URL` OKUNABİLİR (`_vault kv get`
   — eski DSN KASADAN alınır, render dosyasından DEĞİL: tek kaynak; dosya bayat/eksik olabilir).
2. Yeni parola OPERATÖRDEN (mevcut kasa yolu sözleşmesi: "bu yol değeri ÜRETMEZ, sizden ister").
   Boşsa sır adıyla atlanır → yapacak iş yok → `die` (hiçbir şey yazılmadı).
3. Yeni DSN = eski DSN'nin parola alanı değiştirilmiş hâli (`yaz-url` yardımcısı; kullanıcı/yol/query
   korunur, kodlama `quote`). Eski DSN `$YEDEK` altına 0600 yazılır (geri alma girdisi).
4. `_vault kv put` (stdin). KV v2 SÜRÜM numarası kaydedilir (`vault kv metadata get` → `current_version`)
   — geri alma `vault kv rollback -version=<eski>`.
5. Render kanıtı: hedef dosya kanonik kopyası kasadaki yeni DSN'e `cmp -s` ile eşit olana kadar
   (mevcut mekanizma, tavan `VAULT_RENDER_TAVAN_S`). AŞILIRSA: ALTER ROLE KOŞMAZ, KV otomatik geri
   alınır (`rollback`), `olcum_yok` + ADIYLA beyan — DB'ye dokunulmamıştır, sistem eski hâlinde.
6. `ALTER ROLE hindsight PASSWORD` — mevcut `tur: sql` kanalı aynen (SQL dosyası 0600, `psql -f`,
   sonra silinir; parola argv'ye girmez). BAŞARISIZSA: KV `rollback` + render bekle (eski DSN geri) +
   `die "ALTER ROLE başarısız — parola DEĞİŞMEDİ, kasa geri alındı"`.
7. Tüketici restart: `hindsight-api.service` (mevcut `_vault_tuketici_birimleri` + `_restart_carpani`).
8. Kanıt (mevcut `--db` kanıtı aynen): yeni parolayla `psql` (PGPASSFILE 0600, ayrı kimlik) bağlanır;
   `hindsight-api` `/health` 200; eski parola bağlanAMAZ (negatif kontrol). Kanıt düşerse geri alma
   reçetesi basılır: eski parola `ALTER ROLE` (yedekten) + KV rollback + restart.
9. Kuru koşum (`--db --vault --kuru`): planı 1–8 sırasıyla ADIYLA basar, hiçbir yazım/kasa çağrısı yok;
   Agent hedefi uyarısı bu yolda GEREKMEZ (kasa yolu zaten Agent'ı besliyor) — `_agent_hedefi_uyarisi`
   yalnız eski yolda kalır (v522 sözleşmesi).

## 4. Envanter değişikliği
`deploy/sir_envanteri.yaml`: `HINDSIGHT_API_DATABASE_URL` kv girdisine `rotasyon_siri: HINDSIGHT_DB_PAROLA`
(dalga-1 emsali: dash/apisix/nous). `rotasyon_kopyalari` `alt_komut: db` iki kopyası (sql + url) AYNEN —
kasa yolu url kopyasını Agent'a bırakır, sql kopyasını kendi koşar. v447 `_kopyalar()` ↔ envanter
hizası (tek-kaynak çivisi) korunur; v485 E1 dar gevşeme `rotasyon_siri` için zaten var.

## 5. Bedel ve riskler (ölçülmüş / ölçülmemiş ayrımıyla)
- Pencere B'nin süresi ÖLÇÜLMEDİ (render kanıtı → ALTER arası; beklenti saniyeler). İlk gerçek koşumda
  ölçülüp bu belgeye yazılır.
- `hindsight-api`nin havuzu parola değişince YENİDEN bağlanmaya çalışır mı (restart'sız düşer mi)?
  ÖLÇÜLMEDİ — bu yüzden restart adım 7'de ZORUNLU tutulur, "gerekmeyebilir" varsayılmaz.
- `vault kv rollback` politikada izinli mi? ÖLÇÜLMEDİ — uygulama dilimi `deploy/vault/policy`yi okur;
  izin yoksa rollback yerine eski DSN'i `kv put` ile geri yazar (aynı etki, sürüm numarası +1).
- KV'de DSN düz metin olarak (parola dâhil) durur — bugün de öyle (kasa tam URL taşır); bu tasarım
  yeni bir sızıntı yüzeyi AÇMAZ, mevcut yüzeyi kullanır.
- Vault Agent "geri yazma" hipotezi (TSK-064 açık kalem: Agent render hedefine eski yolla yazılırsa
  ≤1 dk'da ezer mi) bu tasarımla İLGİSİZ hâle gelir: kasa yolu hedefe yazmaz, Agent yazar.

## 6. Çiviler (uygulama dilimi, yeni numara Rol-1 rezervi)
1. Sahte kök + sahte `vault`/`psql` sarmalayıcı (v447/v521 düzeneği): `--db --vault --kuru` planı 1–8
   sırasıyla basar, hiçbir yazım yok. 2. Gerçek koşum simülasyonu: KV put → render (sahte Agent dosyayı
   yazar) → ALTER (sahte psql) → restart (sahte systemctl) sırası KAYDEDİLİR ve ASSERT edilir; ALTER
   render kanıtından ÖNCE koşamaz (mutasyon: sıra ters çevrilince kırmızı). 3. Render tavanı aşılınca
   ALTER koşmaz ve KV rollback çağrılır. 4. ALTER düşünce KV rollback + die; hiçbir "başarılı" satırı
   yok. 5. Değer/parola/DSN hiçbir çıktıya basılmaz (mevcut sözleşme). 6. Envanter `rotasyon_siri`
   hizası (v447/v485/v521 yeşil). 7. Eski yol `--db` DEĞİŞMEDİ (30 senaryo eşitlik emsali, v522).

## 7. Karar noktası (operatöre değil, Rol-1'e): sıra
Bu belge B sırasını seçer; A'nın reddi ölçümle değil AKIL YÜRÜTMEYLE (pencere yönü). İlk gerçek koşum
pencereyi ölçer; ölçüm B'yi çürütürse belge revize edilir, kod değil (kart-önce disiplini burada
"belge-önce").
