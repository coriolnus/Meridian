# DEVİR NOTU — cloud oturumu → yerel taraf (2026-08-17)

Bu not, cloud oturumunda (GitHub PR turu) yapılan işin ve orada **ölçülmüş üç dersin** yerel
tarafa taşınması içindir. Cloud oturumu bu notla kapanıyor.

Aktarım deponun kendi mekanizmasından gidiyor çünkü iki taraf birbirine mesaj atamıyor
(`ListAgents` → erişilebilir oturum yok). Öbür yönde aynı işi `docs/DEVIR-2026-08-17-GECE.md`
yapmıştı.

## 1. NE İNDİ — iki PR, ikisi de main'de

| PR | commit | iş |
|---|---|---|
| **#7** | `3f5d583` | önbellek körlüğü sınıfı (3/3) · çapa yasasının kendi körlüğü · beş uydurma · iki dayanıklılık deliği · tam suite 82 kırmızı → 0 |
| **#8** | `22806b5` | tarama 6→1 · yasa `tests/`e açıldı · dört bayat beyan · iki kopya/şekil · bildirim alanı sürtünmesi · KILL#1 negatif kontrolü |

Paralel iş (Ö-50, 23c, HAT/TAHTA) bunların **üstüne** geldi; çakışma yok. Doğrulandı — şu semboller
`origin/main`de duruyor: `_onbellek_oku` (codelaw+ledgers+api) · `_CANLI_STATE_BEYANI` (conftest) ·
`_DEJENERE_YAYILIM_ORANI` (validation) · `_EK_CAPA_KOKLERI` (codelaw) ·
`kontrol_sapmasi` (test_golge_planli_kol_v217).

## 2. ÜÇ DERS — hepsi ölçüldü, hepsi taşınmaya değer

### 2.1 `pytest -rs` ÖLÇÜM KÖR NOKTASI (bu turda üç yanlış rapora sebep oldu)

`-rs`, özet bölümünü **yalnız atlananlara** indirir; `FAILED` satırları HİÇ basılmaz. Dolayısıyla
`grep -c '^FAILED'` ile sayan biri kırmızıyı **göremez**. Bu turda tam suite'in 1 kırmızısı üç ayrı
raporda "0 kırmızı" diye geçti.

HAT'ın H4 kapısı zaten *"tam `grep -E "FAILED|ERROR"`, tail-kesme YOK"* diyor; bu dersin eklediği
şey bir adım ötesi: **grep'e değil, ilerleme satırına bak.** Sayım bayraklardan bağımsızdır:

```python
import re
from collections import Counter
t = open(cikti, encoding="utf-8", errors="replace").read()
ilerleme = "".join(re.findall(r"^([.sFExX]+)\s+\[", t, re.M))
print(Counter(ilerleme))                        # {'.': geçen, 's': atlanan, 'F': düşen, 'E': hata}
print(re.findall(r"\n_{5,} (.+?) _{5,}\n", t))  # düşenlerin ADI
```

Not: son tek-satırlık tally (`N passed, …`) bazen hiç yazılmadan süreç sonlanıyor — **yokluğu
sonucun eksik olduğu anlamına gelmez, ama varlığına da güvenilmemeli.**

### 2.2 ZAMANLAMA TESTLERİNDE NEGATİF KONTROL — eşiğe dokunmadan

`test_golge_planli_kol_v217::test_p95_dongu_suresi_kart_tavanini_ASMIYOR` kırmızı verdi (1,1475×,
tavan 1,10). Eşiğe dokunulmadı (kill-list dokunulmaz, `CLAUDE.md` kural 3). Bunun yerine
**taban↔dal ayrı worktree'de, DÖNÜŞÜMLÜ sırayla** dörder kez ölçüldü:

```
taban (origin/main): 1,0539 · 0,8330 · 1,2590 · 1,1578 → ort 1,0759 · tavanı AŞAN 2/4
dal:                 0,9045 · 0,9442 · 1,0823 · 0,8363 → ort 0,9418 · tavanı AŞAN 0/4
```

Taban da aşıyor ve dal daha hızlı → test bir regresyonu değil **aletin çözünürlüğünü**
raporluyordu. Çözüm üçüncü bir hüküm: kapalı kolun kendi iki yarısı **negatif kontrol** olarak
bölünür; kontrolün 1,0'dan sapması aranan etkiye (%10) ULAŞIYORSA hüküm **"ölçemedim"**dir
(`pytest.skip`, nedende sayılarıyla). Kontrol sıkıyken tavan aynen uygulanır — gerçek bir %10
regresyon hâlâ düşer.

**Desen genel:** ölçülemeyen aleti ihlal saymak UYDURMA YASAĞInın ihlalidir. Başka zamanlama
kartlarında da aynı şekilde kurulabilir.

### 2.3 SIRA DİSİPLİNİ — düşüşü TABANA karşı ölç

Bir düşüşün regresyon mu ortam mı olduğu, **taban ayrı worktree'de aynı makinede dönüşümlü
koşturulmadan** bilinemez:

```bash
git worktree add /tmp/.../taban origin/main
# taban→dal, dal→taban, … en az 3-4 kez; sabit sıra makinenin artan yükünü tek kola yazar
git worktree remove --force /tmp/.../taban
```

Hüküm: taban temiz + dal kırmızı → regresyon **sende** · ikisi de kırmızı → tabandan devralınan
(ayrı kalem, merge'ü bloklamaz) · dağılımlar örtüşüyor → ortam/gürültü (2.2'ye bak).

## 3. AÇIK BIRAKILANLAR — `Ö-49`'un kalanı (tahtada H0)

Ölçüldü, sonra **bilinçli** bırakıldı:

- **`docs/` yasa kapsamına ALINMADI.** 2324 çapa, 704 çürük — ama **668'i TARİHLİ teşhis
  belgelerinde** (`SISTEM-DENETIMI-2026-08-02.md` tek başına 190, `ARTEFAKT-TARAMASI-2026-08-07.md`
  158). Onlar tarihli birer KAYITTIR; yazıldıkları gün doğruydular ve geriye dönük "düzeltmek"
  tarihi tahrif etmek olur.
- **GERÇEK KALEM: üretilen `RUNBOOK.md`'deki 36 çapa.** Üretici, kaynağın yorum bloklarını
  kopyalarken `çapa-mezar-taşı` muafiyet işaretini kopyaya TAŞIMIYOR — yani muaf bir çapa
  RUNBOOK'ta muafiyetsiz görünüyor. Üreticinin işi (`ops/runbook_uret.py`).
- **Sayısal-literal çürümesi için dedektör YOK.** Ölçülmüş vaka: bir yorum "bugünkü sözleşme:
  0,04 / 0,08" diyordu, ikisi de ikiye katlanmıştı (bugün 0,08 / 0,16) ve oran testi yeşil kaldığı
  için bayatlık GÖRÜNMEDİ. `stale_line_anchors`ın kardeşi bir yasa: prozadaki sabit ↔ koddaki
  sabit. Mekanik, dar, kart gerektirmez.
- **Çapa BAŞKA bir kod satırına kaymışsa yakalanmıyor** (yalnız boş/yorum/menzil-dışı ölçülür).
  Kapatmak için çapanın gösterdiği İFADEyi de saklamak gerekir — biçim değişikliği, ayrı tur.

## 4. `A2` BİLDİRİM KANALI — kod tarafında eksik YOK

Zincir uçtan uca ölçüldü: `obs.alarm → notify.send` hazır · `POST /api/secrets/{name}` var ·
`TELEGRAM_*`/`MERIDIAN_WEBHOOK_URL` `secrets.ALLOWED`da · pano Ayarlar ekranında üç alan da çizili ·
"kanal yok" uyarısı üç ayrı yüzeyden raporlanıyor. **Eksik olan tek şey operatörün elindeki
DEĞER.**

Uygulanabilir olan sürtünmeydi ve kapatıldı: alan açıklamaları TANIM yazıyordu, yönerge değil
("BotFather'dan alınan bot anahtarı."). Üçü de tıklanabilir sıraya çevrildi — özellikle chat ID
adımı, çünkü Telegram'da bot ilk mesajı atamaz, sohbet ancak operatör yazınca doğar
(`/newbot` → jeton → **bota mesaj at** → `getUpdates` → `chat.id`, grup ise eksi işareti dahil).

## 5. CLOUD TARAFININ YANLIŞLARI (kayda geçsin)

Bu oturumda söylenip sonra ölçümle yanlış çıkan üç iddia:

1. **"tam suite 0 kırmızı"** (×3) — `-rs` kör noktası; gerçek 1 kırmızıydı (§2.1).
2. **"superpowers kurulu değil"** — kurulu. Bu konteynerin skill anlık görüntüsü
   `2026-08-15 14:14`te donmuş, Superpowers `2026-08-16`da eklenmiş; yani sorun kurulumda değil
   **oturumun yaşındaydı**. Yeni oturum açılınca 14 skill gelir.
3. **"canlı v246'da, dağıtım bekliyor"** — canlı `v249`daymış (v248 + v249 inmiş).

Üçü de aynı sınıftan: **elimdeki anlık görüntüyü güncel gerçek sandım.** Cloud oturumu klonu ve
plugin listesini AÇILIŞTA dondurur; uzun süren bir oturumda o fotoğraf bayatlar.

## 6. ORTAM DURUMU (kapanışta)

- arka plan süreci **yok** · zamanlanmış görev **yok** (5 `send_later` kaydı `run_once_fired`)
- `claude/code-review-lx116u` = `origin/main`, push'lu · ek worktree yok · çalışma ağacı temiz
- PR #7 ve #8 **merged**, izleme kapalı
