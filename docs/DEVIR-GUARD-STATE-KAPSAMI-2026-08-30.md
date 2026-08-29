# Devir notu — `meridian-guard.sh` state/ kapsamı (2026-08-30)

## Ne yapıldı
Kancanın **başlık iddiası** ile **gerçek kapsamı** arasındaki fark kapatıldı: kapsam genişletildi,
başlık indirilmedi.

## Ölçüm (madde 1)
`state/` altında **87 dosya**. Kanca **7 ad ailesi** + `HALT`/`LEARN_HALT` +
`goal|bounds|strategy.yaml` + `secrets.json` blokluyordu. Statik okuyucu/yazıcı taraması
(`meridian/`, `ops/`; `write_json`/`update_json`/`append_jsonl`/`open(`):
**24 korumasız dosya üretim kodunca yazılıyor.** Kanıt sınıfı olanlar:

| dosya | yazan | kaybedilen |
|---|---|---|
| `trades.jsonl` | loop · run · sprint | işlem defteri — operatöre sunulan kanıtın kendisi |
| `equity_curve.json` | run | sermaye eğrisi — panoda ve karnede görünen sayı |
| `scoreboard.json` | run · sprint · versioning | karne; `update_scoreboard` KİLİTSİZ |
| `trade_plans.jsonl` | hermes · loop · run | plan defteri |
| `broker_reconcile.json` | loop | mutabakat damgası — bayatlık alarmının baktığı yer |
| `notify_undelivered.json` | obs | alarm sayaçları |
| `hypotheses.jsonl` · `spend.jsonl` · 17 dosya daha | sprint · spend · … | öğrenme/maliyet defterleri |

**Tutarsızlık, tek cümle:** `portfolio.json` KORUMALI, `trades.jsonl` DEĞİLDİ. İkisi aynı sınıf
kanıttır; birini koruyup ötekini bırakmak bir hüküm değil bir eksikti.

**ÖLÇÜLEMEYEN (None + neden):** `barsarchive.log`, `dashboard.log` — kodda ADIYLA hiç geçmiyor
(dinamik ad ya da ölü artefakt olabilir); statik tarama çözemez.

## Hüküm (madde 2) — genişlet, indirme
İki ölçüme dayanır:
1. **Üretimi kırmaz.** O 24 dosyanın hepsi Meridian'ın KENDİ Python kodundan yazılıyor ve o
   yazımlar `pre_tool_call`a HİÇ uğramıyor — kanca yalnız AJANIN araçlarını görür.
2. **Arıza asimetrisi.** Fazla bloklamak ajana GÖRÜNÜR bir ret verir (mesaj MCP'yi adıyla söyler,
   geri alınabilir); az bloklamak operatöre sunulan kanıtı SESSİZCE tahrif eder.

Başlığı gerçeğe indirmek, işlem defterindeki bir deliği BELGELEMEK olurdu.

## Mekanizma — kör değil keskin
`tool_name` artık **çıkarılıyor** (şerhte hep yazılıydı, hiç okunmuyordu — okuma/yazma
ayıramamanın kökü buydu):
- **yapısal yazma araçları** → `state/` altına HİÇ yazamaz
- **`terminal`** → yalnız YAZMA ŞEKLİ bloklu (`>` `>>` `tee` `sed -i` `rm/mv/cp/truncate/dd`);
  `cat`/`grep`/`jq`/`tail` **serbest**
- **bilinmeyen araç sınıfı → BLOKLAR.** Vaka bilerek tersine kuruldu: yazma araçlarını sayıp
  gerisini serbest bırakmak, yarın eklenecek aracı sessizce serbest bırakmaktı
  (`disabled_toolsets`in kara-liste zaafının aynısı). Ret mesajı durumu adıyla söyler:
  "matcher genişletildiyse bu kanca da güncellenmelidir".
- Adı sayılan ailelerin **TÜM-ERİŞİM** bloğu aynen DURUYOR (okumaları MCP'ye gider — bilinçli).
- **FAIL-OPEN KORUNDU**: ayrıştırılamayan girdi hâlâ boş `{}` döner. Ham payload üstünden
  denylist yine koşar (kancanın kendi şerhinin sözü). İkisi çelişmez: biri SINIFLANDIRMA
  (fail-closed), öteki AYRIŞTIRMA (fail-open).

## Çiviler (madde 3)
Kancanın testi VARDI (`tests/test_authority_boundaries_v77.py`, `_guard_hook` betiği GERÇEKTEN
koşturuyor). Dört çivi eklendi, üçü kırmızı doğdu:
`test_c3_guard_BASLIK_IDDIASINI_TUTAR_state_yazimi_bloklu` (8 kanıt dosyası × yazma/kabuk/silme) ·
`test_c3_guard_state_OKUMASINI_BLOKLAMAZ` (pozitif kontrol — üstteki çivinin anlamlı olma şartı) ·
`test_c3_guard_BILINMEYEN_arac_sinifinda_FAIL_CLOSED` ·
`test_c3_guard_FAIL_OPEN_davranisi_KORUNDU`.

Koşum: 316 passed (kancaya atıf yapan HER dosya + H3 + küçük kuyruk). `bash -n` temiz.
Tam suite koşulmadı ve orantısız olurdu: üretim `.py` kodu DEĞİŞMEDİ, ve kancayı çağıran yerler
ölçüldü — iki config + üç test dosyası, hepsi koşuma dahil.

## OPERATÖRE — dağıtım sonucu, bilinmesi gereken
`ops/meridian-guard.sh` F9 istisnası DEĞİLDİR: dagit onu rsync ile TAŞIR. Yani genişletilmiş kanca
**bir sonraki `dagit.sh --uygula` ile canlıya iner** ve ayrıca bir etkinleştirme adımı yoktur.
Bu güvenli: kanca yalnız DAHA FAZLA ajan eylemini bloklayabilir, hiçbir üretim yazımı ondan
geçmez, ve en kötü durum operatörün etkileşimli hermes oturumunun `state/`e yazarken GÖRÜNÜR bir
ret alması (mesaj MCP'yi adıyla söyler).

## Açık kalan
`state/` altındaki 24 korumasız dosyanın **kilit** durumu tek tek ölçülmedi; bu turda ölçülen
şey ERİŞİM YETKİSİydi. `update_scoreboard`ın kilitsizliği depo hafızasından geliyor ve YENİDEN
DOĞRULANMADI. Ayrı kalem: "canlı worker koşarken state'e yazma" kuralının mekanizma karşılığı
(kilit) hâlâ bir KURAL, kapı değil.
