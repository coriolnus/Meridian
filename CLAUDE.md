# Meridian — CLAUDE.md

Self-learning swing-trade araştırma ve kâğıt-icra sistemi (US hisseleri).
Bu dosya her oturumda yüklenir: yalnız **kural, komut ve tetik** içerir. Gerekçe ve vaka geçmişi →
`MERIDIAN_ENGINEERING_LOG.md`; `(vaka YYYY-AA-GG)` künyesi oradaki kaydı gösterir — künyeli bir
kuralı silmeden/gevşetmeden önce o kaydı oku. Sayı taşıyan her satır ölçüm tarihini taşır.

---

## 0. Oturum başı — ilk mesajda yaz

1. `MERIDIAN_ENGINEERING_LOG.md` oku (hedef sözleşmesi + açık kalanlar).
2. Konumunu söyle: `git rev-parse --show-toplevel` → `$HOME/AI-Trading` ve orkestratörsen **Rol-1**;
   worktree/ikinci terminal/cloud klonu ise **yan oturum**; subagent isen **ajan**.
3. Bu turda geçemeyeceğin kapıları listele (§3 matrisi). Örn. "Ajanım: git yok, dağıtım yok,
   tam suite yok, kartsız ölçüm yok, pytest dışı koşum yok."

**Muafiyet kuralı:** "Bu kural bana uygulanmaz" diye düşünüyorsan, bu düşünce dur-ve-sor nedenidir.
Ölçülmüş ihlallerin hepsi muafiyet iddiasıyla başladı (vaka 2026-08-26).

---

## 1. Proje haritası

| Yol | Ne |
|---|---|
| `meridian/` | Motor: loop, broker, guard, scheduler, codelaw… — canlıda koşan kod |
| `ops/` | Operasyon betikleri. Sözleşmeleri KOMUT SATIRIdır, `main()` değil (vaka 2026-08-30) |
| `tests/` | Tam suite ~26 dk (6 koşum, 7.696 test, 2026-08-30) |
| `research/cards/` | Ölçüm ön-kayıt kartları |
| `state/` | Çalışma durumu — versiyonlanmaz; istisna `goal.yaml`, `bounds.yaml` (izli, SSoT) |
| `backups/`, `.env`, `.dash.env` | Versiyonlanmaz, sır içerir — asla commit'lenmez |
| `deploy/` | A1 systemd birimleri + hermes bot profilleri (`deploy/hermes/profiles/<ad>/`) |
| `docs/RUNBOOK.md` | **ÜRETİLMİŞ** (`ops/runbook_uret.py`) — elle düzenlenmez, birleştirilmez |
| `MERIDIAN_ENGINEERING_LOG.md` | Gerekçe + vaka arşivi; bu dosyadaki künyelerin hedefi |
| `serve.sh` | Canlı servis — yerelde koşma (çift-emir riski) |
| `dagit.sh` | Dağıtım — cwd'ye bakmaz, HER ZAMAN ana checkout HEAD'ini iter |
| `.claude/` | **VERSİYONLANMAZ** (`.gitignore`) → cloud klonuna GİTMEZ. Kural taşıması gereken her şey BU dosyada olmalı (vaka 2026-08-26) |

Canlı: A1 Oracle, `ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87`. A1'e komut her zaman ssh
sarmalı yazılır — iki tarafta da var olan komut sessizce yanlış makinede koşar.
Remote: `github.com/coriolnus/Meridian` (özel). PR'lar squash-merge: dal ucu ata değildir,
"birleşmiş mi" sorusu PR durumundan ölçülür.

---

## 2. Eylem anı kapıları — komutu yazmadan ÖNCE

Kurallar burada tetiklenir. Sol sütundaki şeyi yapmak üzereysen sağ sütunu sor.

| Yapmak üzeresin | Önce sor |
|---|---|
| `pytest` (herhangi) | Konumum ne? Başka ajan uçuşta mı? Tam suite ise: Rol-1 miyim, ağaç donmuş mu, HEAD'i kaydettim mi? `-q` verme (pyproject zaten `-q`; `-qq` özeti siler — "temiz" ile "çıktı yok" aynı görünür). |
| pytest DIŞI bir betik/komut koşmak | `meridian.obs`'a ulaşabilir mi? Ulaşıyorsa canlı yerel deftere YAZAR (3 vaka, 2026-08-30). Davranış görmek istiyorsan `sandbox_state`'li çivi yaz. |
| `monkeypatch.undo()` | Hiçbir zaman — autouse fixture'ları (`sandbox_state` dahil) da geri alır (vaka 2026-08-30). |
| `sleep`, `while`, `until`, `watch` | Bekleme döngüsü mü kuruyorum? Yasak (§7) — ön planda da arka planda da. |
| `git` (HERHANGİ komut) | Rol-1 miyim? Ajan/yan için salt-okunur `git status` bile yasak (2 refleks vakası, 2026-08-30). |
| `git add -A` / `git add .` | Hiçbir zaman (vaka a94d425). |
| `dagit.sh` (dry-run dahil) | Rol-1 miyim? `git status --porcelain` boş mu? Worker durdu mu? |
| "Dağıtıma hazır" cümlesi | Rol-1 değilsem yazmam. |
| `research/` altına ölçüm kodu | `research/cards/` altında kart var mı? Yoksa kod yok. |
| Kart dosyasına yazmak | Rol-1 miyim? Değilsem dokunmam. |
| `state/`'e yazmak | Canlı worker duruyor mu? Rol-1 miyim? |
| Yerel `state/`'ten canlı hakkında sayı okumak | Yerel defter test artefaktlarıyla kirli olabilir — o soru A1'de sorulur (vaka 2026-08-30). |
| `./serve.sh` | Yerelde hiçbir zaman. |
| `except:` / `pass` / fallback | İşaretli + ≥20 karakter gerekçe var mı? (Yasa 4) |
| Bir değer tahmin etmek | Ölçülemiyorsa `None` + neden. (Uydurma yasağı) |
| Dosya/log/alan yazmak | Okuyanı gösterebiliyor muyum? (Yasa 6) |
| `dosya.py:123` biçiminde atıf yazmak | Çapa SATIR değil SEMBOL olmalı — satır kayar, CI kırar (3 commit vakası); `.md`'yi hiçbir tarayıcı görmez, orada sessizce çürür. Çapa taşıyan dosyada satır eklemek/silmek BAŞKA çapaları kırar. |
| Yeni test dosyası adlandırmak (`vNNN`) | Numara KİMLİKTİR: çakışıyor mu? Çakışmada az-çapalı taraf taşınır, kaydı dosya başlığına (vaka v331×2, 2026-08-30). |
| Üretilmiş dosyayı düzenlemek/birleştirmek | Asla elle — yeniden üret, sonucu kıyasla (rebase'de de). |
| Test sonucuna karar vermek | Hüküm ÜÇLÜDÜR (§6). `tail` ile asla; harness bildirimi hüküm değildir. |
| Çivi yazdıktan sonra "yeşil" demek | Mutasyonla ısırdığını gösterdin mi? Bir turda 4 çivi yanlış sebeple yeşildi (2026-08-30). |
| Gürültü/çıktı azaltan değişiklik | Ne KAYBETTİĞİNİ de ölçtün mü? Kazanç ölçülüp bedel ölçülmezse körlük sessizdir (vaka @bekci, 2026-08-30). |

---

## 3. Kimsin: roller ve konumlar

**Model rolü (KİM):** Fable = mimari, brief, denetim, kök-neden, ops betiği, doküman; uygulama kodu
yazmaz. Opus = brief kapsamında implementasyon. Tur başına tek konsolide brief; brief dosya
sahipliğini söyler.

**Konum (NEREDE), modelden bağımsız:** Rol-1 (ana checkout, orkestratör, TEK) · Yan oturum · Ajan.
İki oturum kendini Rol-1 sayıyorsa dur, sor. İki yönlü zarar (vaka 2026-08-26): (a) ana oturum
kendini "yalnız implementasyon" sanıp tur kapanışı commit+push'unu atlar; (b) yan oturum kendini
Rol-1 sanıp otoriter suite/push başlatır.

| Eylem | Rol-1 | Yan | Ajan |
|---|---|---|---|
| Tam suite | ✔ | ✘ | ✘ |
| Kapsam testi | ✔ | ✔ | ✔ (ardışık) |
| git (her komut, salt-okunur dahil) | ✔ | ✘ | ✘ |
| Dağıtım ve dağıtım önermek | ✔ | ✘ | ✘ |
| Ölçüm kartına hüküm | ✔ | ✘ | ✘ |
| `state/`'e yazmak | worker durmuşken | ✘ | ✘ |
| pytest dışı, `obs`'a ulaşan koşum | bilinçli kuru koşum | ✘ | ✘ |

Yan/ajan tur sonu: kanıt (test çıktısı, diff özeti) + devir brief'i. Git yok, dağıtım önerisi yok.

---

## 4. Yasalar — hiçbir brief, akış veya araç gevşetemez

- **Uydurma yasağı:** ölçülemeyen değer `None` + neden. Sıfır ile "bilmiyorum" aynı şey değildir.
- **Yasa 4:** sessiz yutma yok — işaretli + ≥20 karakter gerekçe.
- **Yasa 6:** okuyucusuz yazım yok.
- **PIT'siz fundamentals proxy yasak.**

---

## 5. Ölçüm

- Kart yoksa ölçüm kodu yok, ölçüm ajanı yok. Kart asgarisi: hipotez, eşik, K grid, kill-list,
  veri penceresi, başarı tanımı, yol-tutarlı pozitif kontrol (tek-enstrümanlı PK portföy-yolu
  hatalarına kördür — vaka 2026-08-25).
- Eşik sonradan değişmez (yeni eşik = yeni kart). K grid'de çarpılarak sayılır. Kill-list karta
  dokunulmadan değişmez — ölçümle çürüyen kriter de YERİNDE düzeltilmez, yeni kartla emekli edilir.
- Kart bir artefaktı donduruyorsa girdi çalışma ağacına değil git BLOB'una (içerik-adresli)
  bağlanır — ağaç değişir, kart sessizce ölür (vaka EDG-2026-059, üç kez).
- Ajan karta dokunmaz, çıktı yolunu devir brief'ine yazar. Hükmü Rol-1 işler — ve İŞLEMEK şudur:
  hüküm AYNI turda karta + K defterine yazılır; işlenmemiş hüküm "açık kalem"dir. Eksik K, eşiği
  hak etmeden geçme yönünde yanlıdır (vaka EXE-2026-006).

> ✘ Sonucu gördükten sonra karttaki eşiği 0.05'ten 0.10'a çekmek.
> ✔ Yeni kart açmak, eskisini "kaldı" olarak kapatmak.

---

## 6. Test

- Tam suite yalnız Rol-1'de, tek-otoriter, **arka planda** (~26 dk — 6 koşum, 2026-08-30; Bash
  tavanı 600 sn, ön plan imkânsız).
- **Donmuş ağaç:** suite koşarken dal değiştirilmez, dosya düzenlenmez. Başlarken HEAD'i çıktı
  dosyasına yaz; biterken karşılaştır — eşit değilse yeşil, tepenin ölçümü DEĞİLDİR: deltanın
  etkilenen kümesini ayrıca koş (vaka: paralel oturum, 2026-08-30).
- **Hüküm ÜÇLÜDÜR, üçü birden:** `grep -E "FAILED|ERROR" out.log` boş + "N passed" özet satırı
  VAR + dosyadaki `PYTEST_EXIT=0`. Harness'in "completed (exit 0)" bildirimi pytest'in hükmü
  DEĞİLDİR — iki kez gerçekte kırmızıyken "exit 0" dedi (vaka 2026-08-29/30).
- Koşum her yerde `.venv/bin/python -m pytest` — worktree'lerde venv yok, sistem python'u pytest
  içermez; "koşamıyorum" ile "kırmızı" karışır.
- Ajanlar eşzamanlı pytest koşmaz: `state/` paylaşımlı, fixture'lar çakışır. Dosya-ayrıklığı yetmez.
- **Çivi yeşili kanıt değildir:** yeşilden sonra mutasyonla her çivinin hedeflediği dalı gerçekten
  ısırdığını göster (bir turda 4 çivi yanlış sebeple yeşildi). Ops aracı tesliminden önce aracı
  operatörün koşacağı BİÇİMDE bir kez koş — 18 çivi yeşilken `--uygula` sessizce yok sayılıyordu
  (vaka 2026-08-30).

> ✘ "Dosyalarımız ayrı, ikimiz de pytest koşabiliriz."
> ✔ Ajanlar bitince Rol-1 tek suite koşar; ajanlar yalnız kendi kapsamlarını, ardışık.

---

## 7. Uzun iş ve bekleme

- Yasak: kendi kurduğun yoklama döngüsü — **nerede koşarsa koşsun**. Döngünün arka planda olması
  muafiyet değildir; iki bekleyici birbirini 10 saat canlı tuttu (vaka 2026-08-17).
- Yol: `run_in_background` → bitiş bildirimini bekle (harness seni çağırır) → çıktıyı BİR kez oku.
  Bildirim seni UYANDIRIR, hüküm VERMEZ — hüküm §6'nın üçlüsüdür.
- Olay izlemesi gerekiyorsa Monitor aracı.

> ✘ `(while ! grep -q DONE out.log; do sleep 30; done) &` — "arka planda, yasak ön plan içindi."
> ✔ `run_in_background` ile başlat, bildirimi bekle, RC'yi dosyadan oku.

---

## 8. Git

- Commit/push yalnız Rol-1, onay beklemez (kalıcı yetki 2026-07-31). Ajan/yan HİÇBİR git komutu
  koşmaz — salt-okunur dahil.
- Tur kapanışı: commit → `git push origin main`. Push'lanmamış iş cloud'da yoktur. **Push ≠ dağıtım.**
- Motor kaynağına (`meridian/`) dokunan turda push, tam suite hükmünden ÖNCE atılmaz — üç ardışık
  commit CI kırmızısı üretti (vaka 2026-08-29).
- Ajan uçuştayken: `git add <açık yollar>`. `git add -A` yasak (vaka a94d425).
- Üretilmiş belgeler (RUNBOOK) tur kapanışında BİR kez üretilir; günlük düzenlemesi + yeniden
  üretim TEK commit'te (ayrışırsa çivi her günlük commit'inde kırılır — tekrarlanan vaka).
- Rebase/birleştirmede üretilmiş dosya: birleştirme kabul edilmez — yeniden üret, otomatik
  birleştirmeyle kıyasla (vaka 2026-08-30: aynı çıktı, ama ancak kıyas sonrası bilinebilir).
- `state/`, `backups/`, `.env` versiyonlanmaz; istisna `goal.yaml`, `bounds.yaml`. mtime
  alarmında önce `stat` (birth) + `.git/logs` (vaka 2026-08-02).

> ✘ Ajan uçuştayken `git add -A && git commit -m "docs"` — ajanın yarım işi commit'e karıştı.
> ✔ `git add docs/x.md research/cards/y.md && git commit`.

---

## 9. Canlı ve dağıtım

- Yerelde `./serve.sh` yok. Worker koşarken `state/` yazımı yok.
- Dağıtım yalnız Rol-1. Yan/ajan dağıtmaz, "hazır" demez — `dagit.sh` NEREDEN çağrılırsa çağrılsın
  ana checkout'un O ANKİ HEAD'ini iter, senin ağacını değil; "ağacım temiz" bir güvence DEĞİLDİR
  (vaka 2026-08-26).
- Reçete: temiz ağaç → `--dry-run` oku → mtime kontrolü → worker durdur → dağıt → doğrula → log.
  Dağıtım kaydına o ANKİ main HEAD'i yaz — beyan edilen sha ile giden sha ayrıştı (vaka EDG-016).
- Yeni systemd birimi kurulduğu gün elle test-ateşlenir: "kurulu" ≠ "çalışır" (fail-notify H9'dan
  beri sessiz arızalıydı — vaka 2026-08-30).

> ✘ Worktree'den "ağacım temiz, dagit.sh koşuyorum" — başka oturumun yarım işi canlıya gitti.
> ✔ Commit edilmemiş işi bırak, devir brief'i yaz, Rol-1 dağıtır.

---

## 10. Superpowers (zorunlu)

Rol ayrımının üstüne eklenir: karar/tasarım → brainstorming, writing-plans · implementasyon →
executing-plans, TDD · arıza → systematic-debugging (Faz 1 teşhis bitmeden çözüm yok) · inceleme →
code-review · bitirmeden → verification-before-completion · paralel iş → git-worktrees
(worktree = yan oturum). Bir akış §4–§9 ile çelişirse Meridian kuralı kazanır.

---

## 11. Workflow / ultracode

- Ultracode AÇIK = fan-out'a izin var (system prompt'un kendi istisnası karşılanmıştır).
- İzin ≠ gerekçe: tek dosya / sıkı bağlı sözleşme / teşhis bitmemiş arıza / mekanik tur → tek ajan.
  "Bağımsız kaynak" sayarken bağlamında ZATEN olanı sayma (vaka 2026-08-30: dört kaynağın ikisi
  bağlamdaydı, fan-out şişirilmiş gerekçeyle açıldı). Gerekçeyi brief'e bir cümleyle yaz.
- Fan-out içinde §2 kapıları ve §5–§9 aynen geçerli.

---

## 12. Öncelik ve belirsizlik

Çelişkide: §4 Yasalar → §5–§9 → §10 Superpowers → §11 Workflow → oturum system prompt'u.
Kural belirsizse **yapma**; günlüğe "açık kalan" yaz, brief'te sor.
