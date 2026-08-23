# CANLI TRİYAJ — 2026-08-24 gecesi (Rol-1, otonom tur)

_Hafızadaki ders gereği oturumun ilk işi: "alarm öttü, kimse dinlemedi" (VLO vakası).
Bu kez alarm gerçekten öttü, dinlendi, ve **yeni iş kalemi çıkmadı** — nedeni aşağıda._

## Nabız (2026-08-23T23:44Z / yerel 02:44)
`healthz` 200 · heartbeat yaşı 61 s · `halted:false` · mod `paper` · `last_bar 2026-08-21`
· equity 107.236,86 · 7 açık pozisyon · 2 silahlı · rejim `trend_up` · `breaker_tripped:false`
· `data_ok:true` · ack edilmemiş alarm **0** · `watchdog_alarmed: []`
Birimler: `meridian` active · `meridian-learn` active · **`meridian-sprint` inactive** (bilinen açık kalem).

## Bayrak: `mirror_drift:true` + `position_drift:true` — İNCELENDİ, YENİ ARIZA DEĞİL
| boyut | ölçüm |
|---|---|
| FİYAT sapması | LLY: sim 1.229,88 ↔ Alpaca 1.244,74 = **%1,208**, sınıf `icra` (tol. %0,5) |
| ADET sapması | EMR 64/37 · BKNG 43/22 · AMGN 33/22 (`makbuzsuz_boyut`) · MRNA 13/8 (`kitap_kaydi`) |
| dışarıdan | NVDA (broker'da var, kitapta yok) |

**Hüküm: bu kalıntı ÖLÇÜLMÜŞ ve KAPATILMIŞ bir kalemin (`Ö-53`) düzeltme-öncesi artığıdır.**
Kök neden 2026-08-22'de bulundu: aynı `1R=%1` kuralı İKİ farklı sermaye tabanına uygulanıyordu
(`eq_now=_hb["equity"]` kitap ↔ `eq=acct["equity"]` ayna). Operatör iki tabanın birleştirilmesine
karar verdi; B (ayna kitabın tabanıyla boyutlanır) + D (`_adet_benimse`) v257/v258 ile indi.
Düzeltme **ileriye dönüktür** — mevcut yedi makbuz alanı taşımıyor ve geriye doldurmak uydurma
olurdu. Sınıflandırıcı da artık sebep uydurmuyor: `makbuzsuz_boyut` adıyla beyan ediyor.

**Açık kalan (yeni iş DEĞİL, bekleyen KANIT):** `eq_ayna` / üç-taban makbuzunun ve
`_adet_benimse`nin İLK canlı davranışsal kanıtı **yeni bir gönderim** bekliyor. 08-22'den beri
yeni gönderim olup olmadığı ölçülmedi — sabaha bırakıldı (§ Gece raporu).

## Korumasız pozisyon endişesi — ÇÜRÜTÜLDÜ
`broker_reconcile.json`'daki `alive_order_syms` beş sembol sayıyordu (AMGN·BKNG·DE·EMR·PANW)
ama yedi açık pozisyon var; ilk okumada "dördü korumasız" gibi göründü. **Doğrudan ölçüldü**
(`/api/alpaca/koruma`): `korumasiz: 0 / toplam: 7`. Yedisi de `korumali:true`, `kismi:false`,
kapsanan adet = `broker_adet`. Yani koruma GERÇEK pozisyonu kapsıyor; kitabın fazla sayması
(`adet_ayrisik:true` yedisinde de) yukarıdaki Ö-53 kalıntısıdır ve korumayı etkilemiyor.
`alive_order_syms` daha dar bir şeyi ölçüyor (08-21 damgalı anlık görüntü) — panoda "koruma
kapsaması" iddiası için o alan OKUNMAMALI; `korumasiz/toplam` çifti okunmalı.

## Diğer okumalar
`api_ok:true` · `ghosts: []` · `trail_synced: []` · `force_sync` sıfır · `exit_fill`:
bekleyen 1 / yamalanan 2 / vazgeçilen 0 · `emir_penceresi` kapsandı (28 emir, 07-14→08-19)
· `failed_submissions` en yenisi 2026-07-27 (eski, yeni başarısızlık yok).

## Sonuç
Canlı sistem sağlam ve **dağıtıma engel yok**. Bir sonraki ABD seansı ~13:30Z (14 saat sonra);
bakım penceresi geniş.
