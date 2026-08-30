# DEVİR BRIEF — EXE-2026-009 P-1: `pencere` damgası gönderim anına bağlandı

**Kaynak oturum:** `ai-trading-85` · **Tarih:** 2026-08-30 · **Temel:** `d9b7a74` (merge sonrası)
**Yetki notu:** operatör hükmü 2026-08-29 — "damgayı gönderim anına bağla, iki satırı da düzelt".
**Rol durumu:** `ai-trading-dc` kendini Rol-1 ilan etti; bu oturum bugün aynı ana checkout'ta
Rol-1 olarak iki commit+push attı (`6b9c6ad`, `177a92b`). CLAUDE.md md.85 gereği **durduruldu ve
operatöre soruldu** — bu brief, rol operatörce `dc`ye verilirse devralınacak paketi tarif eder.

## Commit'lenecek beş dosya (AÇIK YOL LİSTESİ — `git add -A` yasak)

```
meridian/loop.py
tests/test_pencere_kaydirma_v272.py
tests/test_pencere_damgasi_gonderim_ani_v335.py      (yeni)
tests/test_pencere_damga_duzeltmesi_v336.py          (yeni)
ops/pencere_damgasi_duzeltme_2026_08_29.py           (yeni)
```

## Ne değişti, neden

**Arıza (ölçüldü):** `pencere` damgası `_patch_entry_slippage` içinde, yani dolum DEFTERE
YAZILIRKEN basılıyordu. Gönderim ile yazım arasına bir dağıtım girerse ikisi ayrışır. Canlı vaka:
DE/PANW `ts=2026-08-21T20:32:22Z` ile 13:30 rejiminde gönderildi, canlı `barclock.py`
2026-08-23T14:53:43Z'de 1345'e döndü, satırlar 08-24'te yazılıp damgayı ORADA aldı →
EXE-009 hakeminin 1345 bandı %50 kontamine oldu, gerçek 1345 örneklemi n=2.
Teşhis: `research/olcumler/edg042_teshis_pencere_damgasi_2026-08-29/TESPIT.md` (177a92b'de).

**Kod (iki nokta, `meridian/loop.py`):**
1. `mirror_submit_armed` — gönderim satırına `"pencere": barclock.pencere_rejimi()` eklendi.
   Doğru çapa gönderim anıdır: pencere yasası GÖNDERİMİ geciktirir.
2. `_patch_entry_slippage` — damga basma dalı KALDIRILDI. Damgasız satır damgasız kalır;
   gönderim rejimi defterden okunamıyorsa uydurulmaz.

**`tests/test_pencere_kaydirma_v272.py`** — o dosyadaki `test_ayna_dolum_yamasi_pencere_damgasi_basar`
ESKİ sözleşmeyi çiviliyordu (`assert r["pencere"] == "1345"`). Silinmedi, hükme çevrildi:
`test_ayna_dolum_yamasi_pencere_damgasina_DOKUNMAZ`. Modül docstring'inin (2) maddesi de
güncellendi (tarihçe korunur, neyin ters çevrildiği yazılı).

## TDD kaydı (RED önce görüldü)

- `v335::test_gonderim_satiri_..._GONDERIM_aninda_tasir` — ilk koşumda YANLIŞ sebeple kırmızıydı
  (kurulum eksiği: `config.BROKER`); düzeltilip `KeyError: 'pencere'` ile doğru sebebe getirildi.
- `v335::test_damgasiz_satira_yazim_ani_rejimi_UYDURULMAZ` — `'1345' is None` ile arızayı birebir
  yakaladı. Kod sonra yazıldı.
- `v336` (4 test) — düzeltme betiği için; modül yokken ImportError ile RED.

## Doğrulama durumu

| Kapı | Sonuç |
|---|---|
| `v335` + `v336` + `v272` (yeni HEAD `d9b7a74` üzerinde) | **23 passed** |
| `v272` + `v141` + `v222` + `v278` (dokunulan yollar) | **107 passed**, `grep -E "FAILED|ERROR"` boş |
| `tests/test_bayat_bytecode_v334.py` (bytecode kapısı) | **12 passed** |
| `codelaw.report()['ok']` | **True** |
| **Tam suite** | **KOŞULMADI** — Rol-1'e ait; `meridian/loop.py` motor kaynağı, seçici tam suite istiyor |

**AKRAN UYARISININ ÖLÇÜMÜ:** `ai-trading-dc`, v335/v336 ham `exec_module` kullanıyorsa bytecode
kapısının kırmızı vereceğini bildirdi. Ölçüldü: her üç yeni dosyada da `exec_module` /
`spec_from_file_location` sayısı **0** — sıradan `import` kullanıyorlar. Kapı da yeşil (12 passed).
Uyarı bu paket için geçerli DEĞİL; yardımcıya geçirilecek bir çağrı yeri yok.

## Push kısıtı (CLAUDE.md md.171)

Motor kaynağına (`meridian/`) dokunuluyor → **push, tam suite hükmünden ÖNCE atılmaz.**

## BEKLEYEN İKİNCİ İŞ: canlı defterde iki satırın düzeltilmesi

Bu commit'in kapsamı DIŞINDA ama aynı operatör hükmünün ikinci yarısı.

- Betik: `ops/pencere_damgasi_duzeltme_2026_08_29.py` (kuru koşu varsayılan, `--yaz` ile yazar)
- **Canlı kuru koşu YAPILDI ve temiz:** 36 satırdan tam 2'si değişecek
  (`P-2026-08-21-DE`, `P-2026-08-21-PANW`), `ts` ve eski damga (`1345`) beklenenle birebir uyuştu.
- **Yazım henüz YAPILMADI.** Gerekenler: canlı worker durdurulmuş olmalı (CLAUDE.md md.63 —
  `meridian.service` şu an *active*), yani bakım penceresi; ve Rol-1 yetkisi.
- Kapsam sınırı: aynı planların `motor="ic"/karar="fill"` satırlarına DOKUNULMAZ. İç motorun
  dolumu gerçekten 08-24'te, 1345 yürürlükteyken oldu ve hiçbir bant onları okumaz
  (K1 filtresi `motor=="ayna"`).
- Bu düzeltme EXE-009 **kill#3'ü operatör istisnasıyla aşar**. Düzeltilen satır `pencere_duzeltme`
  alanıyla gerekçesini taşır (sessiz düzeltme yok).

## KARTA İŞLENECEK (yazım sonrası, Rol-1)

`research/cards/EXE-2026-009-pencere-kaydirma.yaml` → `acik_kalemler_2026_08_29` bloğu:
**P-1 KAPANDI** yazılacak ve kill#3'ün nasıl/neden aşıldığı kayda geçecek. **İstisna yapılıp
yazılmazsa kill kriteri sessizce çiğnenmiş olur.**
**P-2 (hakemin boş kontrol kolu) ve EDG-042 P-3 (K1'in karışık örneklemi) AÇIK KALIR.**
P-3 hatırlatması: K1 n=17/30, kaba izdüşüm ~3-4 hafta — kural eşik dolmadan konmalı, sonra
koymak sayıya bakarak kural seçmek olur.
