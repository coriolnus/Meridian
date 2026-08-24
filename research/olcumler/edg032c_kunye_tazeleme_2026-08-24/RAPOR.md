# edg032c KÜNYE TAZELEME — BAYT-ÖZDEŞLİK KANITI (2026-08-24)

**HÜKÜM: BİT-NÖTRLÜK KANITLANDI.** Künye tazelendi (yalnız `motor_sha256` + `kunye_tarihcesi`).

Yetki: Rol-1 devri (koordinatör görev mesajı, 2026-08-24 — EDG-2026-057 künye kapısı tıkanması).
Emsal: EDG-048 / EDG-049 künye-tazeleme protokolü AYNEN.

---

## 1. SORU

`EDG-2026-057` künye kapısında durdu: künyedeki motor sha 4'lüsünün ÜÇÜ bugünkü motorla
eşleşmiyordu. Statik teşhis (koordinatör ölçümü — **İMDİR, KANITLAMAZ**):

| dosya | künye (v273) | bugün (v276) | statik teşhis |
|---|---|---|---|
| `broker.py`   | `09f5d0850122376a…` | `e4c5c91515d8ec35…` | 10 satır, YALNIZ YORUM (ölü-alan damgaları; `da43a91` ile commit'lendi) |
| `backtest.py` | `b59c059f43d4e410…` | `b59c059f43d4e410…` | **DEĞİŞMEDİ** |
| `strategy.py` | `449039624127c66d…` | `d6ae533c8a578f74…` | commit `06a6cff`, 36 KOD satırı — "OPT Faz-1 kablolama (v276): 5 yeni düğme **bit-nötr** bounds-okur" |
| `guard.py`    | `bb984356798278a5…` | `475e19e7b38f0650…` | 14 satır, YALNIZ YORUM (ölü-alan damgaları; `da43a91`) |

`06a6cff` commit mesajı bit-nötrlük **İDDİA** ediyordu ve künye o commit'ten sonra hiç
tazelenmediği için iddia **SINANMAMIŞTI**. Bu koşumun işi iddiayı sınamaktı.

## 2. NE KOŞULDU

Şasi `edg032b_tamsatir_2026-08-13/olcum.py` YENİDEN KURULMADI — importlib ile yüklendi,
`SANDBOX` bu dizine çevrildi (edg032c/kosum1'e tek bayt yazılamaz: **yapısal** koruma),
`ref.kosum("kontrol", smoke=False)` olduğu gibi çağrıldı. TEK uyarlama (edg032c beyanı AYNEN):
`ARMED_BEKLENEN` → B1 yasası (dünya-BEKLENTİSİ, motor DEĞİL). Parametre enjeksiyonu YOK
(merkez hücre: slot 20 · 0,5R · 5R zarf).

TAM pencere (2022-01-01→2026-07-30, sv=3, 251 sembol) **İKİ KEZ**, her biri taze süreç + bakir
sandbox (`state_kontrol` her koşum öncesi silindi, donmuş EDG-022 kopyalarından yeniden kuruldu).

## 3. KARIŞTIRICILARIN ÖNCEDEN ELENMESİ

Bu, bulguyu yorumlanabilir kılan adım — koşumdan ÖNCE ölçüldü:

| karıştırıcı | ölçüm | sonuç |
|---|---|---|
| `state/bars` (canlı önbellek, salt-okunur symlink) | taban koşumundan (2026-08-22 23:32) sonra değişen dosya sayısı = **0** (en yeni: `spy.csv` 2026-08-13) | ELENDİ |
| EDG-022 donmuş config (sandbox kaynağı) | `goal/strategy/bounds` sha'ları künyedeki `sandbox_kaynagi_edg022` ile **BİREBİR** | ELENDİ |
| Şasi | `edg032b/olcum.py` = `75cef79215a7404f…` = künyedeki `sasi.sha256` | ELENDİ |

**Sonuç: defterler ayrışsaydı geriye TEK değişken kalırdı — MOTOR.** Ayrışmadılar.

## 4. SHA TABLOSU — DÖRT KANONİK DOSYA + alan_envanteri

| dosya | edg032c/kosum1 (taban) | kosum1_yeni | kosum2_yeni | hüküm |
|---|---|---|---|---|
| `islemler_tam_kontrol.json` | `5f54b533465f640f…` | `5f54b533465f640f…` | `5f54b533465f640f…` | **ÜÇ YÖNLÜ BAYT-ÖZDEŞ** |
| `islemler_kontrol.json` | `447b5ea137d75247…` | `447b5ea137d75247…` | `447b5ea137d75247…` | **ÜÇ YÖNLÜ BAYT-ÖZDEŞ** |
| `seanslar_kontrol.json` | `983f2e2d91a35979…` | `983f2e2d91a35979…` | `983f2e2d91a35979…` | **ÜÇ YÖNLÜ BAYT-ÖZDEŞ** |
| `sonuc_kontrol.json` | `9c5b493b90fbc9a7…` | `7bc7e381d14e02c5…` | `ec5af20cb9587aa6…` | bayt farklı — **YAPISAL**, aşağı bak |
| `alan_envanteri_kontrol.json` (ek kanıt) | `b5ccfd4422e09207…` | `b5ccfd4422e09207…` | `b5ccfd4422e09207…` | **ÜÇ YÖNLÜ BAYT-ÖZDEŞ** |

### 4. kanonik dosya (`sonuc`) neden bayt kapısında DEĞİL

Bayt-özdeşlik bu dosyada **yapısal olarak imkansızdır**: şasi ona koşum KİMLİĞİ yazar.
Künyenin kendi `determinizm_kaniti.kapi_sha256` kaydı da bu dosyayı İÇERMEZ (üç defter).
Bayt farkının kaynağı alan alan ölçüldü — **tam olarak beş alan**, başka hiçbiri:

`olcum_zamani` · `sure_sn` · `kill3_mtime` · `motor_sha256_16` · `config_sha256_16`

Son ikisi ayrıca denetlendi (görev şartı: "motor dışında bir şey kaydıysa bayt-özdeşlik
anlamını yitirir"):

* `motor_sha256_16`: broker/strategy/guard değişti — **ölçümün konusu budur**, beklenen.
  `backtest.py` aynı.
* `config_sha256_16`: koşumun GERÇEKTEN OKUDUĞU `sandbox` + `edg022` sütunları üç yaml'da da
  **BİREBİR AYNI**. Yalnız `repo_state` sütunu kaydı: `goal.yaml` `0f0a7b4b…`→`98869980…`,
  `bounds.yaml` `3acb44b1…`→`a001e4b3…`. Bunlar künyenin kendi notuyla **bağlam içindir,
  koşumda OKUNMAZ**; ayrıca CLAUDE.md md.8'in İZLİ ikilisidir (paralel git trafiği
  içerik-aynı yeniden yazar). `strategy.yaml` repo_state'i bile değişmemiş.
  → **motor dışı kayma YOK.**

Yerine 10 ÖLÇÜM BLOĞU derin-eşitlikle sınandı (`performans`, `doluluk`, `tepe_isi`, `betim`,
`tasnif_tum_seans`, `birincil`, `ci95_ay_kumeli`, `islem`, `replay`, `hucre`):

* `kosum1_yeni` ↔ `kosum2_yeni`: **10/10 eşit**
* `kosum1_yeni` ↔ `edg032c/kosum1`: **10/10 eşit** (`replay` bloğu dahil — `n_endeks_satir`=1408 sabit)

> **SIKI KAPI NOTU:** EDG-049 emsali bu ikinci kıyası *bilgi* sayıyordu (`n_endeks_satir`
> koşum-günü önbellek uzunluğudur — edg040 dersi). Bu turda koordinatör talimatıyla
> **KAPIYA alındı** (fail-closed): meşru bir önbellek kayması olsaydı bile künye otomatik
> tazelenmez, Rol-1'e giderdi. Kayma olmadı, kapı geçti.

## 5. DETERMİNİZM (kosum1_yeni ↔ kosum2_yeni)

**GEÇTİ.** Üç defterin üçü de bayt-özdeş + `alan_envanteri` bayt-özdeş + 10/10 sonuç bloğu
derin-eşit. Motor determinist; taze süreç ve bakir sandbox arasında sürüklenme yok.

Betimleyici özet (her iki koşumda ve tabanda AYNI): `n=885` (bvcp 318 · eh 228 · mb 339) ·
`net_pnl=23806.13` · `maxdd_kanonik=0.1263` · `sharpe=0.594` · `avg_r=0.083` ·
`bütünlük geçerli=True` · `frame_miss=0 dup=0 scan!=plan=0`.

## 6. MOTOR SHA — KOŞUM BAŞI / SONU (fail-closed pin)

Pin `V276_PIN` koşum turunun başında (00:43Z) çivilendi; **her fazın başında VE sonunda**
doğrulandı (sapma = `sys.exit`, koşum geçersiz). Bu tur boyunca başka ajanlar uçuştaydı.

| ölçüm noktası | broker | backtest | strategy | guard |
|---|---|---|---|---|
| ön-uçuş 00:43Z | `e4c5c915…` | `b59c059f…` | `d6ae533c…` | `475e19e7…` |
| kosum1 önce/sonra | `e4c5c915…` | `b59c059f…` | `d6ae533c…` | `475e19e7…` |
| kosum2 önce/sonra | `e4c5c915…` | `b59c059f…` | `d6ae533c…` | `475e19e7…` |
| zincir sonu 01:20Z | `e4c5c915…` | `b59c059f…` | `d6ae533c…` | `475e19e7…` |

**Dört noktada sabit = True.** `motor_ayni_kosum_icinde` her iki koşumda True.
Uçuş ortasında mtime'lar da denetlendi: `da43a91` commit'i çalışma ağacını yeniden YAZMADI
(sha ve mtime değişmedi) — commit kaydeder, dosyayı ezmez.

## 7. HÜKÜM

**BİT-NÖTRLÜK KANITLANDI.** Kapı sekiz koşulun sekizinde geçti:
`defter3=True determinizm=True çivi=True ae=True blok_k1k2=True blok_k1ref=True motor=True v276=True`

* `broker.py` + `guard.py` yorum-only iddiası: defter düzeyinde **doğrulandı**.
* `strategy.py` `06a6cff` "bit-nötr" iddiası: **artık iddia değil, kanıt.** 5 yeni düğme
  (`exit.trail_arm_r`, `rvol_band_score` merkez/yarı-genişlik vb.) opsiyonel `_f(params, …)`
  okumasıdır ve eski gövde sabitlerine düşer; donmuş EDG-022 `strategy.yaml`'ı o anahtarları
  içermez, `bounds.yaml`'a satır yazılmamıştır. Beklenti buydu — **ölçüm beklentiyi doğruladı.**
* `ARMED_SETUPS` B1 üçlüsünde: koşum başı assert'i ile doğrulandı (`06a6cff` yasaya dokunmadı).

## 8. KÜNYEYE NE YAZILDI

Dosya: `research/olcumler/edg032c_taban_2026-08-22/TABAN_KUNYESI.json`
sha `dcb8f3b8a59b8984…` → `ddbef18a3e1695bd…`
Yedek: `kunye_yedek_pre_tazeleme.json` (koşumdan ÖNCE alındı; `dcb8f3b8…`)

**DEĞİŞEN (yalnız 2 alan):**
1. `motor_sha256` — `kosum1_once` + `kosum2_sonra` BİRLİKTE (iç tutarlılık: `dort_noktada_sabit`),
   yalnız `broker.py` · `strategy.py` · `guard.py`. `backtest.py` DOKUNULMADI (değişmemişti).
2. `kunye_tarihcesi` — 4 → 7 girdi (dosya başına: eski sha, eski mtime, yeni sha, neden,
   kanıt yolu, yedek yolu, yetki).

**DOKUNULMAYAN (15 üst düzey alan, makine ile doğrulandı):**
`taban` · `dondurma_tarihi_utc` · `neden` · `kanonik_taban_dosyalari` · `determinizm_kaniti` ·
`sasi` · `yasa` · `config_sha256` · `pencere` · `evren` · `hucre` · `cost_model` ·
`butunluk_gecerli` · `taban_ozeti_betimleyici` · `hukum_yok`

## 9. SÜRE

| faz | süre |
|---|---|
| `kosum1_yeni` | 1007,5 sn (16,8 dk) |
| `kosum2_yeni` | 1203,3 sn (20,1 dk) |
| kapı + künye | < 1 sn |
| **toplam (kurulum dahil)** | **~40 dk** (03:40→04:20 yerel) |

Emsal edg048 kontrol koşumu 746 sn sürmüştü; bu tur makine paralel ajanlarla yüklüydü.

## 10. ÜRETİLEN DOSYALAR

`olcum.py` · `bayt_ozdeslik.json` (kanıt) · `kunye_yedek_pre_tazeleme.json` ·
`kosum1_yeni/` · `kosum2_yeni/` (her biri 5 çıktı + `run_kunye.json`) ·
`kosum1_yeni.log` · `kosum2_yeni.log` · `kosum_zincir.log` · `RAPOR.md`
`fark.json` **ÜRETİLMEDİ** — yalnız kapı düşerse üretilir; kapı geçti.

**HÜKÜM YOK beyanı:** Bu rapor "v276 değişikliği iyi/kötü" DEMEZ. Yalnız *bit-nötr mü*
sorusunu ölçer. Düğmelerin AÇILDIĞINDA ne yapacağı ayrı bir sorudur ve ayrı kart ister.

---

## 11. BEYAN — `state/` DOKUNUŞ DENETİMİ (YASA 4: sessiz yutma yok)

Görev şartı "`state/` altına YAZMA" idi. Koşum sonrası denetlendi:

**Yazılmayan (hepsinin mtime'ı koşumdan ÖNCE):** `meridian.db` · `scoreboard.json` ·
`portfolio.json` · `trades.jsonl` · `trade_plans.jsonl` · `goal.yaml` · `bounds.yaml` ·
`strategy.yaml`. Replay şasisi kendi sandbox'ına (`edg032c_kunye_tazeleme_2026-08-24/
state_kontrol`) yazar; `state/bars` yalnız SALT-OKUNUR symlink olarak okundu.

**Tek dokunuş — BEYANLI:** `state/events.jsonl`'a bir `warn` satırı düştü
(`yerel_donmus_defter`, `storage.py:393`; yol başına bir kez damgalanır). Bu, meridian içe
aktarıldığında ortak gözlem defterine düşen **append-only** bir kayıttır — durum mutasyonu
DEĞİLDİR ve ölçümü etkilemez. Kaçınılamazdı: şasi motoru içe aktarmak zorunda.

**Bana ait OLMAYAN:** `state/.locks/` altındaki iki yeni stub dosyası `pytest-395` /
`pytest-396` damgalıdır — **başka bir ajanın test koşumundan** gelir. Bu oturumda test suite
KOŞULMADI (görev yasağı). Kayıt, aynı pencerede başka ajanların uçuşta olduğunun teyididir;
motor pin'inin dört noktada denetlenmesinin sebebi de budur.
