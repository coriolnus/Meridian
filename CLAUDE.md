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
4. Rol-1 isen `gh run list --branch main --limit 3` oku: CI kırmızıysa o turun İLK işi kök nedendir (vaka
   2026-09-15: 8 gün kırmızı, TSK-190).
5. Rol-1 isen A1'de `~/bin/sayfa_oku.sh meridian-hedef-sapma` (LLM'siz GET) oku; sayfa bir karara
   girerse o kararın yanına `kaynak: zihin modeli <ad> v<n>` yaz, girmezse yazma (sahte-kullanım yasağı).
   Kural EDG-2026-089 penceresinin ön şartıdır (operatör (b) melez+retain, 2026-09-13); kaldırılırsa kart KALIR.

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
| `deploy/` | A1 systemd birimleri + hermes bot profilleri (`deploy/hermes/profiles/<ad>/`); `deploy/ansible/`: A0 rolü (`site.yml`) + dağıtım playbook'u (`dagit.yml`, 17 kapı) + tek-kaynak listeler; koleksiyon `ansible-galaxy collection install -r deploy/ansible/requirements.yml` |
| `docs/RUNBOOK.md` | **ÜRETİLMİŞ** (`ops/runbook_uret.py`) — elle düzenlenmez, birleştirilmez |
| `MERIDIAN_ENGINEERING_LOG.md` | Gerekçe + vaka arşivi; bu dosyadaki künyelerin hedefi |
| `serve.sh` | Canlı servis — yerelde koşma (çift-emir riski) |
| `dagit.sh` | Dağıtım — bir sürümlük İNCE SARMALAYICI (2026-09-08): `deploy/ansible/dagit.yml`e yönlendirir (`--dry-run` = `--check --diff`); kapılar ve listeler ORADA (`deploy/ansible/vars/dagit_vars.yml` tek kaynak). Cwd'ye bakmaz, HER ZAMAN ana checkout (`$HOME/AI-Trading`) HEAD'ini iter |
| `AGENTS.md` | **SYMLINK → `CLAUDE.md`** (kopya DEĞİL — tek-kaynak yasası). Codex ve AGENTS.md okuyan araçlar aynı anayasayı görür; araca bağlı farklar `docs/DEVIR-CODEX-2026-09-16.md`de |
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
| `git` (HERHANGİ komut) | Rol-1 miyim? YAN oturum için salt-okunur dahil yasak (tırmanma vakası 2026-08-26). AJAN yalnız BEYAZ LİSTE okur: `log·show·blame·diff·rev-parse·status` — `stash` dahil mutasyon yapan HER ŞEY yasak (stash okuma DEĞİLDİR). Gevşetme 2026-08-31: 2 zararsız-itiraf + inceleme kalitesi ölçümüyle, operatör onayı. |
| `git add -A` / `git add .` | Hiçbir zaman (vaka a94d425). |
| `dagit.sh` / `ansible-playbook … dagit.yml` (kuru koşum dahil) | Rol-1 miyim? `git status --porcelain` boş mu? Worker durdu mu? `ansible.posix` koleksiyonu kurulu mu? Kip bayrağı TEK mi (çelişen çift → çıkış 2, playbook çağrılmaz)? |
| "Dağıtıma hazır" cümlesi | Rol-1 değilsem yazmam. |
| `research/` altına ölçüm kodu | `research/cards/` altında kart var mı? Yoksa kod yok. |
| Bir karar / ruling / ayar değişikliği yazmak | Kalıcı hafızayı kontrol ettin mi (A1 `~/bin/hafiza_sor.sh` recall + ilgili zihin modeli sayfası + memory/ + `ops/kart_benzer.py`) ve kaynağı karara yazdın mı ("kaynak: recall/sayfa/memory" ya da "hafıza: benzer kayıt yok")? Atıfsız karar kontrol edilmemiş sayılır (operatör direktifi 2026-09-06). |
| Yeni kart açmak | `ops/kart_benzer.py --hipotez "…"` koştun mu? Listedeki KALDI/NO-GO benzerleri `selef`/`ref`'e yazdın mı, ya da 'benzer yok' beyanı düştün mü? (TSK-170, 2026-09-06: 19 KALDI + 2 NO-GO kart var; başarısız yaklaşım bilmeden yeniden denenmez.) |
| Kart dosyasına yazmak | Rol-1 miyim? Değilsem dokunmam. |
| ROADMAP.md'ye madde yazmak | Şemaya uyuyor mu? (`docs/TASARIM-ROADMAP-STANDART-2026-09-01.md`: `[TSK-###]` başlık + status/born/owner/size/trigger donuk sözlükten + What/Why/Ref; cepheler PRG-##; §6 endeksi kart kimliğiyle; dış kimlikler Ref'e). Uymayanı v351 çivisi kırar. |
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
| Temel-veri (earnings/insider/short-interest/float) okumak | Kaynak PIT mi (as-of alanı var ve korunuyor mu)? Tarihsel yeniden yürütmede PIT'siz kaynak SIFIR TOLERANS (§4, `pitlaw`). |
| Yeni kapı yüzeyi (GO/NO_GO/REVIEW döndüren fn) ya da yeni tarayıcı yazmak | `pitlaw` sözleşme kaydına eklendi mi? Eklenmezse yasa o yüzeyde KÖR — çivi bilinen vokabülerle konuşursan öter, konuşmazsan ÖTMEZ. |
| Gürültü/çıktı azaltan değişiklik | Ne KAYBETTİĞİNİ de ölçtün mü? Kazanç ölçülüp bedel ölçülmezse körlük sessizdir (vaka @bekci, 2026-08-30). |

---

## 3. Kimsin: roller ve konumlar

**Model rolü (KİM):** Fable = mimari, brief, denetim, kök-neden, ops betiği, doküman; uygulama kodu
yazmaz. Opus = brief kapsamında implementasyon. **KOD YAZAN HER AJAN OPUS'tur** — düzeltme turu ve
"küçük" backend kalemi dahil; Sonnet yalnız inceleme/rapor/salt-okur ölçüm, Haiku yalnız mekanik katman;
model tavanları (Opus ≤10 · Sonnet ≤25 · Haiku ≤40) EŞ ZAMANLI koşan ajan sayısıdır — günlük
toplam değil, rol dağıtımı da değil (operatör 2026-09-13). Tur başına tek konsolide brief; brief dosya
sahipliğini söyler.

**Konum (NEREDE), modelden bağımsız:** Rol-1 (ana checkout, orkestratör, TEK) · Yan oturum · Ajan.
İki oturum kendini Rol-1 sayıyorsa dur, sor. **Rol-1 oturumu masaüstü uygulamasının Code
sekmesindedir** (operatör 2026-09-16 "burası ana oturum kalsın"); VS Code bir EDİTÖRDÜR — orada açılan
Claude oturumu YAN oturumdur. İki arayüz aynı oturumu aynı anda süremez: ayrı oturum havuzları tutarlar ve
koşan bir oturumu sürdürme denemesi KOPYA başlatır (ölçüldü 2026-09-16). İki yönlü zarar (vaka 2026-08-26): (a) ana oturum
kendini "yalnız implementasyon" sanıp tur kapanışı commit+push'unu atlar; (b) yan oturum kendini
Rol-1 sanıp otoriter suite/push başlatır.

| Eylem | Rol-1 | Yan | Ajan |
|---|---|---|---|
| Tam suite | ✔ | ✘ | ✘ |
| Kapsam testi | ✔ | ✔ | ✔ (ardışık) |
| git — yazan her komut | ✔ | ✘ | ✘ |
| git salt-okunur beyaz liste (`log·show·blame·diff·rev-parse·status`) | ✔ | ✘ | ✔ (2026-08-31) |
| Dağıtım ve dağıtım önermek | ✔ | ✘ | ✘ |
| Ölçüm kartına hüküm | ✔ | ✘ | ✘ |
| `state/`'e yazmak | worker durmuşken | ✘ | ✘ |
| pytest dışı, `obs`'a ulaşan koşum | bilinçli kuru koşum | ✘ | ✘ |
| A1'de **durum değiştirmeyen** okuma (`status·show·list-units·journalctl·ls·cat·grep·curl healthz`) | ✔ | ✔ (2026-09-16) | ✘ |
| A1'de **durum değiştiren** her komut (`start·stop·restart·yazma·silme·sudo değişiklik`) | ✔ | ✘ | ✘ |
| Depo dosyasına yazmak (kod/belge) | ✔ | ✘ — istisna: operatörün DOĞRUDAN talimatı + Rol-1'e bildirim | ✔ (kendi worktree'sinde) |
| Taslak üretimi (brief·rapor·inceleme·ölçüm tasarımı) — scratchpad'de | ✔ | ✔ (2026-09-16) | ✔ |
| Dil sunucusu/editör yüzeyi (tanılama, sembol, arama, kod açıklama) | ✔ | ✔ | ✔ |

**Ek iş nereye:** varsayılan ALT AJAN (bu turun işi — Rol-1'in ağacı, commit'i, suite'i).
Worktree yalnız üç tetikle: iş bu turun kapsamı DIŞINDA · Rol-1'in ağacı donukken paralel
ilerlemeli · dağıtım kararı operatörün (chip). Worktree oturumu şeridinde kalır: ana checkout'ta
git yok (vaka 2026-08-30: şeritten çıkan oturum bayat merge + Rol-1 çekişmesi üretti).

Yan/ajan tur sonu: kanıt (test çıktısı, diff özeti) + devir brief'i. Git yok, dağıtım önerisi yok.

**YAN OTURUM YETKİ PAKETİ (operatör 2026-09-16 "faydalı yetkiler tanımlayalım").** Yan oturum bir
GÖZ ve bir TASLAK TEZGÂHIDIR; eli Rol-1'indir. Dört sınıf AÇIK:
1. **Editör-yerel iş** — dosya/sembol okuma, arama, dil sunucusu tanılamaları, kod açıklama, yerel
   diff okuma. Risk yok, bildirim gerekmez.
2. **Salt-okur canlı triyaj** — A1'de durum DEĞİŞTİRMEYEN komutlar. Alarmı erken yakalamak bu
   paketin asıl gerekçesidir (vaka: `meridian-backup` 2026-09-15'ten beri kırıktı, tek işaret bir
   systemd durumuydu). Bulgu AKSİYONA çevrilmez: ölçülür, Rol-1'e devredilir.
3. **Taslak üretimi** — brief, inceleme raporu, ölçüm tasarımı, belge taslağı; hepsi scratchpad'de.
   Depo dosyasına inmesi Rol-1'in kararıdır.
4. **Kendi worktree'sinde kapsam testi** — ayrı `state/` taşıdığı için eşzamanlı koşabilir (2026-09-07).

KAPALI kalanlar (gerekçe matriste): git yazma · dağıtım ve dağıtım önerisi · tam suite · A1'de durum
değiştiren her komut · sır okuma/yazma · kart dosyası · `state/` · `ROADMAP.md`/`CLAUDE.md` yazımı.
Operatör yan oturuma doğrudan bir depo düzenlemesi söylerse yapar, ama AYNI turda Rol-1'e bildirir —
bildirmezse Rol-1 donmuş ağaç ve dağıtım kapılarında o değişikliği sürpriz olarak bulur (vaka
2026-09-16: VS Code MCP ayarı).

---

## 4. Yasalar — hiçbir brief, akış veya araç gevşetemez

Numara tarihî KİMLİKTİR: kodda "Yasa 4" 275, "Yasa 6" 405 atıf taşır — yeniden adlandırılmaz.
Yasa 1-3 ve 5 HİÇ VAR OLMADI (ölçüldü 2026-08-30); yeni yasa numara ALMAZ (vNNN kimlik sınıfı).
Zorlanma katmanı dürüstçe etiketlidir — zorlanamayan yasa, zorlananla aynı güçte değildir.

**Mekanik — `codelaw` ölçer, suite kırmızı yapar:**
- **Yasa 4 — sessiz yutma yok:** sinyalsiz `except` ihlaldir; kaçış AÇIK işaretle:
  `# sessiz-yutma: <≥20 karakter gerekçe>`.
- **Yasa 6 — okuyucusuz yazım yok:** okunmayan artefakt üretilmemişten farksızdır; meşru
  istisna BEYANLA olur (`DECLARED_SINKS`, gerekçeli).
- **PIT'siz fundamentals proxy yasak** — mekanikleşti 2026-08-31: denetçi
  `meridian/pitlaw.py::rapor`, çiviler `tests/test_pit_yasasi_v341.py` +
  `tests/test_pit_sinif_turetimi_v342.py`. İki dünya, iki hüküm: **tarihsel yeniden yürütme**
  (replay/geri-dolum/tohum) SIFIR TOLERANS; **canlı karar yüzeyi** beyanlı taban (düşer,
  YÜKSELMEZ). Kaydın kendisi de denetlenir: sınıf ataması ve iki sözleşme kaynaktan türetilir —
  kayıtsız kapı yüzeyi ya da tarayıcı doğduğu gün çivi öter. `BILINEN_IHLALLER` 2026-08-31'de
  BOŞALDI (EDG-2026-062: tarihsel çapa EDGAR arşivine bağlandı; iki kayıt öz-denetimli
  korumalı-zincir beyanına taşındı). Tarihçe: `docs/DEVIR-PIT-CIVISI-2026-08-30.md`.

**Sözleşme — çiviler parça parça zorlar, kalanı denetim yakalar:**
- **Uydurma yasağı:** ölçülemeyen değer `None` + neden. Sıfır ile "bilmiyorum" aynı şey değildir.
- **Tek-kaynak yasası** (terfi 2026-08-30): aynı gerçeğin iki kopyası sessizce ayrışır —
  sayı/liste/kural TEK kaynaktan türetilir; kopya kaçınılmazsa türetme + ayrışma çivisi
  (vaka ×3: günlük↔CLAUDE.md zıt suite emri · F9 başlık/liste · damga mantığı).
- **Bedel yasası** (terfi 2026-08-30): çıktıyı/gürültüyü azaltan değişiklik ne KAYBETTİĞİNİ
  de ölçer — kazanç ölçülüp bedel ölçülmezse körlüğün belirtisi hiçbir şeydir (vaka @bekci).


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

- Tam suite yalnız Rol-1'de, tek-otoriter, **arka planda**, `-n 4 --dist worksteal` ile (~13 dk —
  13.222 test, 2026-09-16 ölçümü: aynı HEAD'de ardışık `--dist load` 20:28 ↔ `worksteal` 13:13, takas
  yazımı %40 az; yavaş testler bir işçiyi bağlarken boştaki işçiler iş çalar). `-n 4` BELLEK tavanıdır:
  makine 8 GB, işçi ~680 MB — daha fazla işçi takasa düşer ve YAVAŞLAR. Hedefli/küçük koşumlar SERİ:
  `-n 4` küçük kümede işçi-açılışıyla net kayıptır. Suite penceresinde ajan/VS Code test koşumu YOK
  (yük-flake, vaka 2026-09-15 suite #56).
- **DÖRT KATMAN — hangi koşum NEREDE** (operatör 2026-09-16; ölçüm TSK-193, kaynak ROADMAP'ten
  buraya taşındı — kural burada yaşar):
  1. **Yazarken tek dosya → VS Code test paneli** (~10 s). `.vscode/` yapılandırması bunun için
     kuruldu: yorumlayıcı `.venv`e pinli, kaydetmede KEŞİF KAPALI (13k test her kaydetmede yeniden
     taranmasın ve otoriter suite penceresine düşmesin), `launch.json`da iki koşum (açık dosya · `-k`).
     Bu katman EDİTÖR KULLANICISININDIR — hızlı geri besleme içindir, hüküm üretmez.
  2. **Merge öncesi hedefli kapsam + tarama çivileri → terminal, SERİ** (1–3 dk).
  3. **Motor push öncesi tam suite → Rol-1, ARKA PLAN, `-n 4 --dist worksteal`** (~13 dk).
  4. **Her push → CI duman** (~2 dk). Tam suite CI'a TAŞINMAZ: temiz klonda ~65 state-bağımlı
     kırmızı + 2 vCPU + dakika kotası.
  Rol-1 ve ajanlar 1. katmanı KULLANMAZ, terminalde koşar. Nedeni araç tercihi değil ÖLÇÜM:
  hüküm ÜÇLÜDÜR ve üçü de DOSYADAN okunur (`FAILED|ERROR` grep + "N passed" satırı + `PYTEST_EXIT`);
  test paneli bu üçlüyü vermez, ayrıca ajanlar worktree'de çalışır ve editör ana checkout'u açar.
  Panel yeşili bir HÜKÜM DEĞİLDİR — harness bildirimiyle aynı sınıftadır (§6 üçlü hüküm maddesi).
- **Donmuş ağaç:** suite koşarken dal değiştirilmez, dosya düzenlenmez. Başlarken HEAD'i çıktı
  dosyasına yaz; biterken karşılaştır — eşit değilse yeşil, tepenin ölçümü DEĞİLDİR: deltanın
  etkilenen kümesini ayrıca koş (vaka: paralel oturum, 2026-08-30).
- **Hüküm ÜÇLÜDÜR, üçü birden:** `grep -E "FAILED|ERROR|[0-9]+ failed" out.log` boş + "N passed"
  özet satırı VAR + dosyadaki `PYTEST_EXIT=0`. Harness'in "completed (exit 0)" bildirimi pytest'in
  hükmü DEĞİLDİR — üç kez gerçekte kırmızıyken "exit 0" dedi (vaka 2026-08-29/30, 2026-09-21).
  `FAILED` jetonu TEK BAŞINA YETMEZ: addopts `-q` kırmızıyı o jetonla basmayabilir — suite #71'de
  `1 failed` iken `FAILED|ERROR` grep'i BOŞ döndü, kurtaran `PYTEST_EXIT` oldu (vaka 2026-09-21).
- Koşum her yerde `.venv/bin/python -m pytest` — worktree'lerde venv yok, sistem python'u pytest
  içermez; "koşamıyorum" ile "kırmızı" karışır.
- Ajanlar eşzamanlı pytest koşmaz: `state/` paylaşımlı, fixture'lar çakışır. Dosya-ayrıklığı yetmez.
  GEVŞETME (operatör 2026-09-07: "ajanlar pytest koşabilsin"): AYRI WORKTREE'lerdeki ajanlar eşzamanlı KAPSAM testi koşabilir
  (her worktree kendi `state/`ini taşır); aynı checkout'ta yine yasak, tam suite yine tek ve Rol-1'de.
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
- Push'tan sonra CI hükmü AYNI turda okunur: `gh run list --branch main --limit 3` — kırmızıysa kök neden
  o turda, sonraki push'a ertelenmez. main 8 gün kırmızı kaldı, hiçbir triyaj sormuyordu (vaka
  2026-09-15, TSK-190). Motor turunda üçlü suite hükmü CI'nın yerine geçmez: ikisi ayrı kapıdır.
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
- Reçete: temiz ağaç → `--dry-run` oku (= playbook `--check --diff`; `*deleting` satırları ve PLAY RECAP `failed=0`) → mtime kontrolü → worker durdur → dağıt → doğrula → log. İlk gerçek playbook dağıtımı OPERATÖR GÖZETİMİNDE (2026-09-08, TSK-176 Task 4).
  Dağıtım kaydına o ANKİ main HEAD'i yaz — beyan edilen sha ile giden sha ayrıştı (vaka EDG-016).
- Yeni systemd birimi kurulduğu gün elle test-ateşlenir: "kurulu" ≠ "çalışır" (fail-notify H9'dan
  beri sessiz arızalıydı — vaka 2026-08-30).

> ✘ Worktree'den "ağacım temiz, dagit.sh koşuyorum" — başka oturumun yarım işi canlıya gitti.
> ✔ Commit edilmemiş işi bırak, devir brief'i yaz, Rol-1 dağıtır.

---

## 10. Superpowers (zorunlu)

Rol ayrımının üstüne eklenir: karar/tasarım → brainstorming, writing-plans · plan icrası (bu
oturumda: görev başına taze ajan + görev incelemesi + dal-sonu denetimi) →
subagent-driven-development · plan icrası (ayrı oturum/worktree) → executing-plans ·
implementasyon → test-driven-development · arıza → systematic-debugging (Faz 1 teşhis bitmeden
çözüm yok) · inceleme → requesting/receiving-code-review · bitirmeden →
verification-before-completion · dal kapanışı → finishing-a-development-branch · paralel
bağımsız işler → dispatching-parallel-agents, using-git-worktrees (worktree = yan oturum).
Bir akış §4–§9 ile çelişirse Meridian kuralı kazanır.

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
