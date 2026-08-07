# `conservation.unexplained = 14` — kök neden ölçümü (Rol-1, 2026-08-07)

**Okuyucu:** bu bulguyu koda çevirecek ajan + operatör. (YASA 6)

## 0. Önce kendi hipotezimin çürütülmesi

`universe_coverage` kusurunu (v206: "165 seans" aslında 165 OLAY) kapattıktan sonra
`conservation.unexplained`'i **"aynı kümülatif sayaç sınıfı"** diye işaretlemiştim.
**Bu hipotez YANLIŞ çıktı ve geri alınıyor.**

`watchdog.py:423-524` okundu. `conservation_report()` bir sayaç DEĞİL, her koşuda
sıfırdan kurulan bir **nüfus sayımı**: pencere satır değil TARİH tabanlı ve en eski
plana kadar açılıyor (`_gun = max(30, (bugün − en_eski).days + 2)`), `live_start`
pencereden değil **defterin tamamından** okunuyor (C6, 2026-08-02), ölçüm arızaları
(`conservation_plan_date_unparsable`, `conservation_cf_fate_unavailable`) sessizce
yutulmuyor ve pencereyi **daraltmıyor, genişletiyor**. Yani rapor, benim ona
yakıştırdığım kusurun tam tersini yapacak biçimde yazılmış.

Alarm gerçek. Kusur raporda değil, **raporun ölçtüğü şeyde**.

## 1. Canlı ölçüm (A1, 2026-08-07)

`conservation_report()` salt-okunur koşuldu:

| alan | değer |
|---|---|
| `ok` | **False** |
| `plans` | 408 |
| `traded` | 95 |
| `no_fill` | 5 (meşru terminal) |
| `replay_era` | 242 (kayıt körlüğü, sızıntı değil) |
| `live_start` | 2026-07-10 |
| **`unexplained`** | **14** |

Hüküm dağılımı — payda 408: `REVIEW` 258 · `GO` 103 · `NO_GO` 47.
Raporun gösterdiği 8 satırın **hepsi `REVIEW`**. Bu tesadüf değil, imza.

## 2. SINIF A — kimlik şeması dikişi (ölçüldü, 2 plan)

Plan defterinde **aynı plan iki kez** yazılı, iki ayrı kimlik şeması altında:

| kısa kimlik | uzun kimlik | tarih | hüküm | aynı ticker/giriş? |
|---|---|---|---|---|
| `P-2026-07-21-MMM` | `P-2026-07-21-MMM-episodic_pivot` | 2026-07-21 | NO_GO | evet / evet |
| `P-2026-07-23-NSC` | `P-2026-07-23-NSC-momentum_burst` | 2026-07-23 | REVIEW | evet / evet |
| `P-2026-07-23-UNP` | `P-2026-07-23-UNP-momentum_burst` | 2026-07-23 | REVIEW | evet / evet |

Şema dikişinin tarihi ölçüldü — **iki yazıcı AYNI ANDA canlı**:

- KISA biçim: 2023-01 → 2026-08 kesintisiz (2026-07'de n=9, 2026-08'de n=4 — **hâlâ yazıyor**)
- UZUN biçim: yalnız 2026-07 (n=24) ve 2026-08 (n=7)

**Sonuç:** broker reddi KISA ikize kaydedildi, UZUN ikizin hiçbir terminal kaydı yok
ve sessiz kayıp sayılıyor. MMM çifti kapıda `NO_GO` olduğu için elenir; geriye
**NSC ve UNP** kalır.

### 2b. Kod yorumu ölçümle çelişiyor

`watchdog.py:465-472` (K1, 2026-07-30) şunu iddia ediyor:

> "canlıdaki 4 red (UNP/NSC/TMO/RTX) `dropped` kümesine hiç giremiyor" → düzeltildi.

Ölçüm: canlıda **tam 4 `BROKER_REJECT` olayı** var ve düzeltme **yalnız 1'inde** işliyor.

| olay `plan_id` | plan defteri kimliği | `dropped`'a girer mi |
|---|---|---|
| `P-2026-07-23-UNP` | `…-UNP-momentum_burst` | ✗ bağlanamıyor |
| `P-2026-07-23-NSC` | `…-NSC-momentum_burst` | ✗ bağlanamıyor |
| `P-2026-07-23-TMO-momentum_burst` | aynısı | ✓ düşüyor |
| `P-2026-07-27-RTX` | `P-2026-07-23-RTX-…` (başka gün) | ✗ |

TMO **kontrol vakası**: aynı alarm, aynı gün, tam kimliği taşıdığı için rapordan
düşüyor. Dal ölü değil — dal **çalışıyor**, ama `dropped`'a yazdığı kimlik plan
defterinin kimliğiyle uyuşmuyor. Yorumun "düzeltildi" beyanı 4/4 değil **1/4**.

## 3. SINIF B — terminal yolu olmayan REVIEW (geri kalan ~12)

CSX · RTX · PKG · ROK · PANW · NUE ve diğerleri: **hiçbir kimlik biçimi altında
sıfır olay**. Hepsi `REVIEW`.

`REVIEW` = "insan gerekiyor". 258 REVIEW planın 67'si işleme dönmüş. Geri kalanın
büyük kısmı bir terminal kayıt bırakıyor; bu ~12'si bırakmıyor.

**Bağlantı (ölçülmedi, hipotez olarak işaretlenir):** operatöre teslim edilememiş
33 alarm ve eksik bildirim kanalı açık kalem olarak duruyor. Bir REVIEW planı insanı
bekliyorsa ve insan hiç haberdar olmuyorsa, planın sessizce sönmesi beklenen sonuçtur.
Bu **doğrulanmadı** — bildirim kanalının bu 12 plana dokunup dokunmadığı ölçülmeli.
Doğrulanırsa, eksik bildirim kanalının defterde **ölçülebilir bir bedeli** var demektir.

## 4. Hüküm — ne yapılacak

1. **Kimlik şemasını tekilleştir.** İki yazıcının ikisi de canlı; hangisinin kanon
   olduğu seçilmeli ve diğeri susturulmalı. Kanon seçilmeden yapılan her düzeltme
   dikişi kapatmaz, üstünü örter.
2. **`dropped` eşleşmesini kimlik-biçimine dayanıksız yap** — olay `plan_id`'si plan
   kimliğinin öneki ise eşleş (ya da tersi). Bu bir yama; asıl çözüm (1).
3. **`watchdog.py:465-472` yorumunu dürüstleştir.** "4 red düzeltildi" ölçümle
   çelişiyor; ölçülen 1/4. YASA: test korumuyorsa iddia yazılmaz.
4. **REVIEW için terminal yol tanımla.** Bir REVIEW planı ya işleme dönmeli, ya
   düşürüldüğü OLAYLA kaydedilmeli, ya da süresi dolduğunda bir olay bırakmalı.
   Şu an üçü de olmayan bir yol var ve sessiz kayıp tam oradan geliyor.
5. **Bildirim kanalı bağını ÖLÇ** (§3 hipotezi) — doğrulanana kadar iddia edilmez.

## 5. Ölçüm izleri

- `watchdog.conservation_report()` — A1, salt-okunur, `/opt/meridian/.venv`
- `trade_plans.jsonl` (408) · `events.jsonl` (plan_id taşıyan 9 ayrık kimlik) · `trades.jsonl`
- Betikler: `scratchpad/korunum_kok.py`, `scratchpad/ikiz.py` (stdin'den koşuldu; canlıya dosya yazılmadı)
- Yetim kimlik (olayda var / planda yok) = **0** — ilk hipotezimdi, çürütüldü.
