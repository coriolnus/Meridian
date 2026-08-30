# TEŞHİS — `pencere` damgası gönderim rejimini DEĞİL yazım rejimini söylüyor

**Tarih:** 2026-08-29 · **Rol-1** · **Tetikleyen:** operatör sorusu ("K1'in giriş medyanı neden
bu kadar yükseldi, bak") — EDG-2026-042 haftalık koşum #2'nin ardından.

**BU BİR ÖLÇÜM DEĞİLDİR.** Eşik üretmez, hüküm taşımaz, hiçbir kartın sayısını beslemez,
CI hesaplamaz. Bir DEFTER BÜTÜNLÜĞÜ teşhisidir: EXE-2026-009'un kendi kill#3'ünün ("geriye dönük
pencere yeniden-etiketleme yapılırsa geçersiz") çiğnenip çiğnenmediğini sorar. Salt-okuma;
canlıya ve `state/`'e tek bayt yazılmadı. EDG-042'nin donuk reçetesine DOKUNULMADI.

## Soru nasıl buraya geldi

EDG-042 K1 medyanı 2026-08-22 koşumunda +15,017 bps, 2026-08-29 koşumunda +29,786 bps.
Mekanik olarak medyan "yükselmedi": eski 13 satırın hiçbiri değişmedi, yeni 4 satırın dördü de
eski dağılımın en üst ikisi arasına düştü, medyan işaretçisi eski sıralı dizinin 7.'sinden
9.'suna kaydı (9. değer zaten 29,786'ydı). Asıl soru "dördü de neden büyük-pozitif" oldu.
Dördü de `pencere="1345"` damgalı, 13 eskisi damgasız — birebir örtüşme. Damganın DOĞRU olup
olmadığı işte burada sorgulandı.

## Kanıt (teshis_damga.json — bu dizinde)

Gönderim zaman damgası (`ts`) K1'in 17 satırı için:

| plan tarihi | ticker | `pencere` | `ts` (gönderim, UTC) | defter yazımı | yol |
|---|---|---|---|---|---|
| 2026-08-05..08-19 | 13 satır | `None` | `20:3x` / `22:10` | ertesi işlem günü | EOD GTC (eski) |
| 2026-08-21 | DE | **`1345`** | **`2026-08-21T20:32:22Z`** | 2026-08-24 | **EOD GTC (ESKİ)** |
| 2026-08-21 | PANW | **`1345`** | **`2026-08-21T20:32:22Z`** | 2026-08-24 | **EOD GTC (ESKİ)** |
| 2026-08-25 | ECL | `1345` | `2026-08-26T13:45:01Z` | 2026-08-26 | 13:45 penceresi (YENİ) |
| 2026-08-27 | CRM | `1345` | `2026-08-28T13:45:00Z` | 2026-08-28 | 13:45 penceresi (YENİ) |

Canlı `barclock.py` mtime (A1, salt-okuma): **2026-08-23 14:53:43 UTC** — 1345 sabiti canlıya
o an indi. Depoda karşılığı: `d8030c0` (2026-08-23).

Zaman çizgisi DE/PANW için: gönderim **08-21 20:32Z** (13:30 rejimi yürürlükte) → kaydırma
canlıya **08-23 14:53Z** → defter yazımı **08-24** → damga o anki sabitten "1345".

## Kök neden (kod)

`meridian/loop.py:2761` (`_patch_entry_slippage`):

    if "pencere" not in r:
        r["pencere"] = barclock.pencere_rejimi()   # YAZIM ANININ rejimi

Kod, mevcut damganın YENİDEN yazılmasına karşı korunmuş (yorumu kill#3'ü açıkça anıyor), ama
**bayat bir satıra İLK damgayı bugünün rejimiyle basmaya** karşı korunmamış. Kartın sözü:
"damga dolum anındaki YÜRÜRLÜK rejimini söyler". Gönderim ile defter yazımı arasına bir dağıtım
girdiğinde bu iki cümle ayrışır ve damga sessizce yalan söyler.

Normalde görünmez, çünkü yazım dolumu bir işlem günü izler (plan Cuma → dolum Pazartesi deseni
tabloda görülüyor: 08-14 Cuma → 08-17 Pazartesi). DE/PANW'de araya tam olarak kaydırmanın inişi
girdi.

## Etkisi

1. EXE-009 hakem katmanının **1345 bandı şu anda %50 kontamine**: 4 satırın 2'si eski rejimde
   gönderilmiş. Gerçek 1345 örneklemi **n=2**, n=4 değil.
2. Kontaminasyon iki donuk çekicinin taşıdığı alanlardan **GÖRÜNMÜYOR**: `ts` ne
   `edg042_*/canli_cek.py`'nin E2 alan listesinde ne `pencere_cek.py`'ninkinde var. Yani hakem
   kendi kontaminasyonunu ölçemez.
3. EDG-042 K1 medyanının yükselişinin nedeni "pencere kaydırması" diye TEK CÜMLEYLE
   açıklanamaz: yükseliş kaydırmadan ÖNCE gönderilmiş iki satırda da var (+80,7 · +87,1).

## Yeniden üretim (salt-okuma; hiçbir şey yazmaz)

    ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 \
        'cd /opt/meridian && ./.venv/bin/python -' < teshis_damga.py > teshis_damga.json

## Hüküm YOK — açık kalemler operatörde

Bu belge tespit eder, karar vermez. Doğan üç açık kalem EXE-2026-009 ve EDG-2026-042 kartlarına
işlendi (`P-1`, `P-2`, `P-3`); eşikler ve karar kuralları hiçbir kartta DEĞİŞTİRİLMEDİ.
