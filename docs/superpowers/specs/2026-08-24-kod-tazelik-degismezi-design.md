# Tasarım — kod-tazelik değişmezi: "active" ≠ "yeni kodu koşuyor"

**Tarih:** 2026-08-24 · **Yöntem:** superpowers:brainstorming · **Operatör onayı:** var
(yaklaşım C; beyan-öncesi düşme kararı da onaylandı) · **Durum:** UYGULANDI

## 1 · Tetikleyen olgu

12:30Z dağıtımı ısınma telemetrisini (`warmup_merdiven_kilitli`) canlıya indirdi. Dağıtımın
doğrulama adımı **"iki birim de active"** dedi ve bu **doğruydu**. Ama:

```
meridian-learn süreç başlangıcı : 2026-08-24 00:34:40Z
en yeni /opt/meridian/meridian/*.py : 2026-08-24 11:53:16Z   →  11 sa 19 dk FARK
```

Süreç, dağıtılan kodu **taşımıyordu**. Doğru bir cümle, anlamsız bir güvence verdi.

**Kök neden:** `dagit.sh`ın bakım penceresi yalnız `meridian meridian-barsarchive` durduruyordu
ve dosyada **`learn` kelimesi hiç geçmiyordu**. Birim 2026-08-17'de doğdu (ROADMAP §2-50),
betik güncellenmedi. Bilinçli dışlama DEĞİL — unutma.

**Sınıfın maliyeti:** öğrenme tarafına yapılan her dağıtım, biri ELLE restart edene kadar
sessizce etkisiz. Bu vaka hafızada zaten vardı ("7 gün bayat bytecode", 2026-08-24 00:34'te
elle restart edilmişti) — o zaman semptom giderildi, **neden giderilmedi**.

## 2 · Değerlendirilen yaklaşımlar

| | ne | neden seçilmedi |
|---|---|---|
| A | listeye `meridian-learn` ekle | bugünkü örneği kapatır, **sınıfı kapatmaz**: yarın eklenen birim aynı sessizlikle unutulur; ve "koşuyor mu" sorusu hâlâ cevapsız |
| B | birim listesini keşfederek türet | unutmayı önler ama `sprint@` örnekleri/timer'lar gibi dokunulmaması gerekenleri de yakalar; şimdi gereksiz karmaşa (YAGNI) |
| **C** | **ekle + KOŞTUĞUNU doğrula** | **seçildi** |

**C'nin gerekçesi:** bizi yanıltan "learn listede yok" değildi — **doğrulamanın `active` demesi ve
bunun doğru ama anlamsız olmasıydı.** A tek başına o yanılgıyı aynen bırakırdı.

## 3 · Tasarım — üç parça

### 3.1 Bakım penceresi öğrenme birimini kapsar
`dagit.sh` [4]: durdur/başlat listesi → `meridian meridian-barsarchive meridian-learn`.

**Restart bedeli ÖLÇÜLDÜ ve ucuz:** sonda önbelleği diske yazılıyor
(`reflect.PROBE_DISK_FILE = probe_cache.json`), döngü 300 sn'de bir uyanıyor
(`HERMES_POLL_SECONDS`), birim `Restart=always` + `TimeoutStopSec=120`. Kaybedilen en fazla
o anki turun **taze** hesabıdır; birikmiş önbellek kalır.

### 3.2 Yeni kapı [5b] — değişmez
```
her koşan meridian birimi için:
    ExecMainStartTimestamp  ≥  en yeni mtime(/opt/meridian/meridian/**/*.py)
```

**Kapsam ELLE SAYILMAZ, `ExecStart`tan TÜRETİLİR.** Birim adlarını yazsaydık yarın eklenen
birim aynı şekilde unutulurdu — düzeltmek istediğimiz sınıfın ta kendisi. Kural: `running`
durumda **ve** ExecStart'ı `/opt/meridian` altından python/uv koşan her birim.
`meridian-litestream` (litestream ikilisi) bu kuralla **kendiliğinden** dışarıda kalır.

Ölçülemeyen hâl (kaynak mtime'ı ya da süreç başlangıcı okunamadı) **ihlal sayılmaz**, ayrı
raporlanır — uydurma yasağının çapa tarafı.

### 3.3 Kapı [B] dağıtım-beyanından ÖNCE düşer  *(operatör kararı)*
Beyan `state/dagitim.json`a "bu sha canlıda" yazar. Süreçlerden biri eski kodu koşuyorsa bu
cümle **yanlıştır**. Kapı önce düşerse dosya eski sha'da kalır — **koşan sistemin gerçek hâli
odur**. Onarım: birimi döndür, `./dagit.sh --uygula`yı tekrar koş (rsync idempotent).

Reddedilen alternatif: beyanı yaz ama içine `tazelik_ihlali` alanı koy. Daha yumuşak ama
"dağıtım tamam" demiş olurduk.

### 3.4 Çiviler
`tests/test_dagit_f9_beyan_v266.py` (emsal: dosya zaten `dagit.sh`ı çiviliyor):
* `test_bakim_penceresi_ogrenme_birimini_KAPSAR` — durdur VE başlat satırlarında `meridian-learn`
* `test_kod_tazelik_kapisi_VAR_ve_BEYANDAN_ONCE` — [5b] var · `ExecMainStartTimestamp` okunuyor ·
  kapsam `ExecStart`tan türetiliyor · kapı beyandan ÖNCE · ihlalde `exit 1`

## 4 · Doğrulama (yapıldı)

* TDD: iki çivi önce yazıldı ve **kırmızı verdi**, sonra kod yazıldı → `17 passed`.
* `bash -n dagit.sh` temiz.
* **Kapı mantığı canlıda koşturuldu ve bugünkü ihlali YAKALADI:**
  `IHLAL meridian-learn.service 40716 /opt/meridian/meridian/hermes.py`
  (40.716 sn = 11 sa 19 dk; suçlu dosya, telemetriyi koyduğum dosyanın ta kendisi).
  `litestream` tarandı ve doğru şekilde elendi; öteki iki birim temiz geçti.
* Canlı onarıldı: `meridian-learn` 14:30:36Z'de döndürüldü, değişmez artık tutuyor.

## 5 · Beyan — ne YAPILMADI

* Yaklaşım **B** (listeyi tümüyle keşfederek türetme) uygulanmadı; [5b]'nin kapsam kuralı
  zaten türetilmiş olduğu için unutma sınıfı **doğrulama tarafında** kapandı. Bakım
  penceresinin kendi listesi hâlâ elle — bir birim eklenir ve listeye yazılmazsa [5b] onu
  **yakalar** ama dağıtım o turda düşer. Bilinçli: gürültülü başarısızlık, sessiz etkisizlikten iyidir.
* Isınma merdiveninin **kilidi onarılmadı** — ayrı iş, ölçüm kartı ister (merdiveni açmak K'yı
  büyütür → ön eleme eşiği sertleşir; etkinin yönü ölçülmemiş).
* `dagit.sh` canlıya rsync'lenen bir dosya değil, yerel dağıtım aracıdır; bu değişiklik
  dağıtım gerektirmez, bir sonraki `--uygula` koşumunda yürürlüğe girer.
