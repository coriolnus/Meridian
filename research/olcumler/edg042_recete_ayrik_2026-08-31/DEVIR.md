# DEVİR BRIEF — EDG-2026-042 R3: P-3/AYRIK reçete revizyonu

**Kaynak:** `ai-trading-85` (yan oturum) · **2026-08-31** · **Commit/dağıtım:** Rol-1 (`ai-trading-dc`)
**Hedef dizin:** `research/olcumler/edg042_recete_ayrik_2026-08-31/` (ad Rol-1'ce onaylandı)

## 0. ATOMİKLİK ŞARTI — ÖNCE BU

> **İŞARETÇİ GÜNCELLENMEDEN BU PAKET COMMIT'LENMEZ.**

Görev metni `[2]` artık reçete dizini/sha taşımıyor; donuk reçeteyi **karttan** okuyor. Bu,
kartın "GÜNCEL DONUK REÇETE İŞARETÇİSİ" kaydını **yük taşıyan** hale getirdi. Kart bloğu
(`p3_karar_ayrik_ts_2026_08_31`) + işaretçinin bu dizine güncellenmesi + bu paket **TEK
commit'te** gitmeli.

Ayrışırsa: 2026-09-05 koşumu R2'ye (`edg042_recete_short_2026-08-24/`) gider — orada ne `ts`
var ne kol ayrımı — ama görev metni `giris_1345`/`giris_once` bekler. Görev, reçetenin
üretmediği kovaları arar ve tur **sessizce anlamsızlaşır**. Rol-1'in mekanik çivisi
(işaretçinin gösterdiği dizin var + `canli_cek.py`'si `ts` çekiyor) bu şartın makine tarafı.

## 1. Taşınacak dosyalar (`eski/` HARİÇ — o yalnız regresyon koşumunun geçici kopyasıydı)

```
KOMUT.txt          canli_cek.py       olcum.py          canli_ham.json
sonuc.json         ozdeslik.json      sinama.py         sinama.json
sonuc_ts_yok.json  DEVIR.md
```

## 2. Künye

| dosya | sha256 | önceki |
|---|---|---|
| `canli_cek.py` | `a846449e…` | `4c6b85a5…` |
| `olcum.py` | `1787a9ff…` | R2 `1dcb7708…` |

Önceki reçete dizinlerine **tek bayt yazılmadı** (`edg042_kosum_2026-08-22/`,
`edg042_recete_short_2026-08-24/`) — hangi koşumun hangi reçeteyi kullandığı dizinden izlenir.

## 3. Değişen / değişmeyen

**Değişen — iki dosya, üç nokta:** `E2_ALAN`'a `ts` · `PENCERE_SINIRI` + tek-sınır beyanı ·
`gonderim_kolu()` + K1'in iki kola bölünmesi + `giris_ortak`.

**Değişmeyen:** eşik **değerleri** (30/10 · 15/6), karar kuralı, kill kriterleri, bootstrap
künyesi (B=5000, seed=20260812, kümeleme=SEANS), K2/K3 formülleri, R2 yön koşullaması.
P-3 kova tanımını **daralttı**, eşiği değil.

## 4. Doğrulama durumu

| Kapı | Sonuç |
|---|---|
| Regresyon (`ozdeslik.json`) — aynı snapshot, eski vs yeni reçete | K2 + K3 + `cikis_ortak` **bayt-özdeş**, GEÇTİ |
| Satır korunumu | 15 + 2 + 0 `olculemedi` = **17** = eski havuzlanmış n |
| Sentetik `ts` (`sinama.json`) | **10/10 GEÇTİ** (sınır ±1 sn, tam üst, iki gerçek damga, tz normalizasyonu, dört "kol belirlenemez" dalı) |
| Uydurma yasağı, gerçek veri (`sonuc_ts_yok.json`) | `ts`siz snapshot → iki kol da n=0, 17/17 `olculemedi` |
| Havuzlanmış `giris` anahtarı | çıktıda **YOK** |
| Damga biçimi (EDG-037) | harfiyen korundu; donukluk `kalici_taban` alanında |
| **pytest** | **KOŞULMADI** — ağaç donuk, otoriter suite Rol-1'de |
| **git / dağıtım** | **YOK** — yan oturum |

## 5. Ölçülen (BETİMLEYİCİ — hüküm DEĞİL, iki kol da eşik altında)

`giris_once` n=15 / 5 seans / medyan **16,131** · `giris_1345` n=2 / 2 seans / medyan **210,07**
· K2 n=6 · K3 n=4 · `olculemedi` 0.

Havuzlanmış medyan **29,786** idi — yani **havuzlanmış sayı iki kolun hiçbirine benzemiyor**.
AYRIK kararının ilk somut görüntüsü. Ama `giris_1345` **n=2**: bu bir gözlem değil bir işarettir,
karar kuralı **uygulanmadı**.

## 6. Snapshot künyesi — bilerek böyle

`canli_ham.json` **2026-08-31'de** çekildi (sha `41a75a45…`), 08-29 haftalık koşumunun snapshot'ı
**değil**. Rol-1 hükmü (a): sınama snapshot'ı pakette **kalır**, çünkü regresyon kanıtı bir
snapshot'a dayanmak zorundadır — dayanaksız kanıt kanıt değildir (R2 emsali de kanıt-snapshot'ını
taşıyordu). Dizin adı `recete` (koşum değil); yürürlükteki haftalık artefakt **2026-09-05'te**
bu reçeteyle üretilecek.

## 7. Kart tarafında bu paketle eşleşmesi gerekenler (Rol-1)

1. `p3_karar_ayrik_ts_2026_08_31` bloğu (taslak mesajla geçildi)
2. **GÜNCEL DONUK REÇETE İŞARETÇİSİ → `edg042_recete_ayrik_2026-08-31/`** ← atomiklik şartı
3. `kalici_taban` satırı: "`giris_once` çıktısı `kalici_taban` alanıyla işaretlenir; damga
   biçimi (EDG-037) DEĞİŞMEDİ (operatör hükmü 2026-08-31)"
4. K disiplini: "K TOPLAM = 3 korundu; `giris_1345` halef, `giris_once` grid'de sayılmaz"
5. ROADMAP §2 Ö-54'teki **iki** bayat "~3-4 hafta" + §7 satırı

## 8. Açık kalanlar (bu paketin dışında)

- **P-2** — hakemin kontrol kolu yapısal olarak boş; öneri tetiği inşaen açılamaz. Operatör kalemi.
- **EK bölümünün sabit dizin işaretçisi** — `[2]`'den emekli edilen sınıfın aynısı, aynı dosyada;
  P-2 çerçevelenirken aynı tek-kaynak çözümünü almalı.
- **Seyrelme mekanizması ölçülemedi** — plan-günü başına dolum 3,0 → 1,0; E2 red/veto satırı
  tutmuyor, sebep bu defterle okunamaz. Ayrı kart adayı.
