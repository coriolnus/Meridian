#!/usr/bin/env bash
# belge_esitle.sh — BELGE EŞİTLEME YOLU: belgeleri DAĞITIMDAN BAĞIMSIZ olarak canlıya taşır
# (TSK-177, operatör onayı 2026-09-08).
#
# NEDEN VAR. Panonun `/api/roadmap` ucu A1'deki `/opt/meridian/ROADMAP.md` KOPYASINI okur,
# depodakini değil. Bugüne kadar bir yazım düzeltmesinin panoda görünmesi için tam dağıtım hattı
# koşuyordu: tedarik-zinciri + mimari + import kapıları, worker DURDURMA, `uv sync`, yeniden
# başlatma — ve motor kaynağına dokunulmuş bir turda bunlardan önce ~9 dakikalık tam suite
# hükmü. Bir virgül için canlı motoru durdurmak, bedeli faydasından büyük bir törendi ve
# pratikte belge düzeltmelerinin canlıya GİTMEMESİNE yol açtı. Bu betik o bedeli kaldırır: yalnız
# belge taşır — hiçbir birimi durdurmaz, hiçbir servisi yeniden başlatmaz, `uv sync` çağırmaz.
#
# BU BİR DAĞITIM DEĞİLDİR ve dağıtımın yerine GEÇMEZ. Motor sürümü canlıya YALNIZ ./dagit.sh ile
# çıkar (o betiğin başlığındaki SÜRÜM TERFİSİ SÖZLEŞMESİ değişmedi). Bu yolun taşıyabileceği
# şeyler aşağıda TEK dizidir (`BELGE_KUMESI`) ve `[0d]` kapısı yasak sınıfı ÇALIŞMA ANINDA ölçer:
# `.py`/`.sh` uzantısı ile `meridian/`, `ops/`, `deploy/`, `ui/`, `state/` ve `*.env*` bu yoldan
# GEÇEMEZ. "Bu betik yalnız belge taşır" bir niyet beyanı değil, ölçülen bir kapıdır.
#
# BELGE KÜMESİ: ROADMAP.md · MERIDIAN_ENGINEERING_LOG.md · docs/ (alt dizinleriyle;
# `docs/RUNBOOK.md` ÜRETİLMİŞ ama commit'li olduğu için kümededir — canlıdaki kopya depodakiyle
# aynı olmalı) · research/cards/ (ölçüm kartları + üretilmiş README.md).
#
# --------------------------------------------------------------------------------------------
# AKTARIM KÜMESİ GİT'TEN TÜRER (tur 3, 2026-09-08).
#
# rsync `.gitignore` OKUMAZ. Tur-2 bu boşluğu bir KAPIYLA kapatıyordu ([0c]: kümede izli olmayan
# TEK dosya varsa DUR) ve o kapı ana checkout'ta ölçüldüğünde operatörün İLK kuru koşumunu
# durduruyordu (`docs/mutasyon/.2026-08-01.ham.log`, `.gitignore` kaynaklı). Kapı doğruydu ama
# yanlış katmandaydı: artık aktarılacak yolların LİSTESİ `git ls-files -z` çıktısıdır ve rsync'e
# `--files-from` + `--from0` ile verilir. İzlenmeyen ya da yok sayılan bir dosya listede YOKTUR,
# yani rsync onu HİÇ GÖRMEZ — koruma kapıdan YAPIYA taşındı.
# Bu yüzden `[0c]` bir kapı değil, bir RAPORdur: "disk ≠ git" bilgisi (hangi dosya aktarılmayacak)
# basılır ve akış DURMAZ. Liste git INDEX'inden gelir; [0a] (temiz ağaç) index ile diskin aynı
# olduğunu zaten garanti eder, yani listedeki bir yol diskte eksik olamaz.
#
# İKİ FAZ — VE NEDENİ ÖLÇÜLDÜ (openrsync 2.6.9-uyumlu, yerel sahne, 2026-09-08):
#     $ rsync -a --delete --from0 --files-from=<liste> ./docs/ dst/docs/
#     >f+++++++ alt/K.md            ← hedefteki `eski.md` ve `alt/ESKI.md` DURDU: 0 silme
# `--files-from` verildiğinde rsync hedef dizinleri TARAMAZ; `--delete` sessizce ölür. Tek çağrıda
# birleştirilseydi hayalet temizliği "yeşil görünüp" hiç koşmazdı (kazanç ölçülüp bedel
# ölçülmeseydi görülmezdi — bedel yasası). Bu yüzden:
#   FAZ-1 AKTARIM — `--files-from`/`--from0` (git listesi), `--delete` YOKTUR. `--checksum` da
#                   BURADA verilir (Rol-1 hükmü, A1 GNU rsync 3.2.7 ölçümü, 2026-09-08 — aşağıya
#                   bak, `_cagri_kur`).
#   FAZ-2 SİLME   — SALT-SİLME geçişi: `--delete --max-delete=N --existing --ignore-existing`.
#                   `--existing` yeni DOSYA yaratmaz, `--ignore-existing` var olan DOSYAYI
#                   güncellemez — DOSYA aktarımı YOK (ölçüldü). Ama openrsync'te salt-silme
#                   geçişi eksik alt DİZİNLERİ yaratabilir ve var olan dizinlerin mtime'ını
#                   güncelleyebilir (ölçüldü, tur-3: `docs/mutasyon/` boş dizin olarak oluştu,
#                   `.d..t....` satırı) — "sıfır aktarım" iddiası DOSYA düzeyinde doğru, DİZİN
#                   düzeyinde değil. GNU man'i "(including directories)" der; A1'deki ilk kuru
#                   koşumda doğrula. Yalnız DİZİN girdileri için.
# SIRA: önce TÜM aktarımlar, sonra TÜM silmeler. Silme geri alınamayan yarıdır — bir aktarım
# düşerse hiçbir silme koşmamış olur.
# FAZ-2'nin ölçütü DİSKTİR, git değil (rsync'e ikinci bir liste veremeyiz; yukarıdaki ölçüm).
# BEDELİ AÇIKÇA: diskte duran ama izli OLMAYAN bir dosya, hedefteki adaşını silinmekten KORUR.
# `[0c]` raporu tam olarak o dosyaları basar — bu körlük sessiz değildir.
#
# SEMBOLİK BAĞ: `--no-links` her çağrıda verilir; ölçüldü — bağ AKTARILMAZ (`skipping non-regular
# file`, çıkış 0). Tur-2'de `docs/mutlak.py -> /etc/passwd` biçimli bir bağ dört kapının hepsini
# geçip canlıya bağ olarak gidiyordu (`cL+++++++`). Artık iki savunma var: izlenmeyen bağ zaten
# listede yoktur, İZLİ bir bağ ise `--no-links` ile atlanır ve `[0d]` onu "atlandı: N bağ" diye
# RAPOR eder (durdurmaz — taşınmayan bir şey zarar veremez, ama sessiz de kalmaz).
#
# --------------------------------------------------------------------------------------------
# SİLME KAPSAMI — bu betiğin en pahalı sınıfı, DÖRT KATLI kapatıldı (tur 2-3, 2026-09-08).
#
# ÖLÇÜLEN KAZA (tur-1 kodu, openrsync, yerel sahne):
#     $ rsync -a --relative --delete ./research/cards  dst/
#     *deleting research/olcumler/edg075/state/seans_DEPODA_YOK.json
#     *deleting research/edgar_facts/facts.json          ← 7 silme, yalnız 1'i kümede
# `research/cards` İKİ SEVİYELİDİR: `--relative` hedefte `research/` dizinini "ima edilen dizin"
# olarak yaratır ve `--delete` onu da budar. A1'de `research/` ~290 MB'tır; bunun yalnız ~952
# KB'ı (`research/cards`) belge kümesindedir. Kalanı (`olcumler`, `edgar_facts`, `pit_universe`)
# git'te KARŞILIĞI OLMAYAN, canlı-sahipli veridir — `dagit.sh`ın `RSYNC_EXC` listesi onları
# dağıtımdan bilerek DIŞLAR. Geri dönüşü git'ten OLMAYAN sınıf.
#
#   (1) YAPISAL — `--relative` KULLANILMAZ. Her küme girdisi kendi çağrılarını alır ve hedef yolu
#       AÇIK yazılır (`./docs/` → `<uzak>/docs/`). İma edilen dizin sınıfı böylece hiç DOĞMAZ;
#       `--delete` yalnız o alt ağacın içini budayabilir. Kök DOSYALAR `--delete` ALMAZ (kök
#       kapsamlı bir silme `/opt/meridian`ın tamamını budardı).
#   (2) BAYRAK — `--no-implied-dirs` yine de verilir; biri gün gelip `--relative`e dönerse ikinci
#       savunma olarak orada durur (güvenlik bir lehçenin davranışına bırakılamaz).
#   (3) TAVAN — `--max-delete=N`. N = aktarım listesindeki İZLİ dosya sayısının %10'u, en az 5.
#       TAVAN HER rsync ÇAĞRISINA (küme girdisindeki HER DİZİNE) AYRI verilir — TEK bir TOPLAM
#       bütçe DEĞİLDİR. Bugünkü kümede iki dizin girdisi vardır (`docs`, `research/cards`), yani
#       gerçek üst sınır N+N'dir; TOPLAM üzerinde ikinci bir eşik YOKTUR (ÖLÇÜLDÜ: docs 5 +
#       research/cards 5 hayalet, tavan 5 → çıkış 0, 10'u da silindi). Rapor bunu ÇAĞRI BAŞINA
#       satırlarla + tavansız bir toplamla gösterir: `silinecek (<dizin>): N (tavan T)` her
#       silme çağrısı için ayrı, `silinecek toplam: N` tavan iddiası TAŞIMADAN.
#       Tavan aşılırsa rsync 25 ile çıkar ve betik `DURDU: silme tavanı aşıldı` + çıkış 1 der.
#       ÖLÇÜLDÜ: tavan ÖN-TARAMADA (`-n`) da 25 verir ve hedefte tek bayt değişmez — yani "kaynak
#       boş / kök yanlış" hâli hiçbir şey silinmeden yakalanır. (Gerçek koşumda rsync tavana
#       kadar siler sonra durur; ön-tarama ZORUNLU olduğu için o hâle normalde gelinmez.)
#   (4) KAPI — her `*deleting` satırının yolu, kümeden TÜRETİLEN silme kapsamına karşı ölçülür.
#       İKİ ayak: kapsam öneki tutmayan yol · `..` TAŞIYAN yol (ön ek eklenmiş bir yol bile
#       `docs/../research/...` ile kapsamdan çıkabilir). Tek ihlal `DURDU: silme kapsamı dışı
#       yol` + çıkış 1 demektir. Kapı HEM ön-taramada HEM gerçek koşumda çalışır.
#       ÜÇÜNCÜ bir "mutlak yol" ayağı tur-2'de vardı ve ÖLÇÜLDÜ Kİ ÖLÜYDÜ (mutasyonla: kaldırınca
#       hiçbir çivi ötmüyordu). Sebebi: rapor ön eki MUTLAK yola da ekleniyordu (`docs//etc/passwd`)
#       ve o dize kapsam önekiyle BAŞLADIĞI için kapıyı geçiyordu. Ayak kaldırıldı, asıl hata
#       düzeltildi: `_onekle` mutlak yola ön ek EKLEMEZ, böylece mutlak yol kapsam ayağına takılır
#       (bir mutlak yol hiçbir zaman `docs/` ile başlayamaz). Ölçüldü: openrsync `*deleting`
#       yollarını her zaman HEDEFE GÖRE basar (hedef mutlak yolla verildiğinde bile) — mutlak yol
#       bugün gözlenen bir hâl değil, kapının kapattığı bir sınıftır.
#
# `*deleting` satırlarının yolları HEDEFE GÖREdir (rsync onları dizin-içi basar); rapor onlara
# küme girdisinin ön ekini EKLER, yani operatör `research/cards/EMEKLI.yaml` görür, `EMEKLI.yaml`
# değil — hangi ağaçtan silindiği raporda kaybolmaz. Ön ek YALNIZ yol taşıyan satırlara eklenir
# (itemize ve `*deleting`): rsync uyarı ve `--max-delete` bildirimini de STDOUT'a basar (ölçüldü)
# ve onlara ön ek eklemek metni bozardı.
#
# HEDEFTEKİ ARA DİZİN: ölçüldü (openrsync, 2026-09-08) — `<uzak>/research/` yoksa rsync onu
# SESSİZCE yaratır ve çıkış 0 verir. Tur-2 başlığı "rsync düşer ve betik DURUR" diyordu; bu
# YANLIŞTI ve kaldırıldı. Bedeli açıkça yazılır: `MERIDIAN_A1_DIR` yanlış yazılırsa bu betik
# canlıda yeni bir ağaç kurup "TAMAM" der — hedef dizin operatörün doğrulayacağı şeydir.
#
# KURU KOŞUM ARTEFAKTI (tur-3 inceleme Z3, ölçüldü openrsync 2026-09-08): kuru koşumda hedef
# dizin yoksa rsync liste dışını da sayabilir; uygulamada sızmaz (ölçüldü). Hedef alt ağaç
# (ör. `research/cards/`) HİÇ yoksa, `-n` ön-taramasında SALT-SİLME geçişi TEK BAŞINA koşarken
# `--existing` henüz var olmayan bir hedefe karşı YOK SAYILAN (izlenmeyen) dosyaları bile
# "aktarılacak" (`<f…`) diye raporlayabilir — `dosya_n` bu yüzden şişebilir (gerçek izli yoldan
# FAZLA görünür). `--uygula`da SIZMAZ: AKTARIM fazı hedef dizini ÖNCE yaratır, SİLME fazı ondan
# SONRA `--existing` ile koşar ve yok sayılan dosya hiçbir zaman yaratılmaz/silinmez — bu satırı
# görürsen SIZINTI değil, hedef ağacın (henüz) eksik olduğunun işaretidir. `[0c]` raporundaki
# "rsync bu yolları hiç görmez" cümlesi AKTARIM fazı için doğrudur; bu kuru-koşum istisnası
# yalnız SİLME fazına ve yalnız hedef alt ağaç eksikken doğar.
# --------------------------------------------------------------------------------------------
#
# `--delete` TÜRETİLİR, ikinci bir listeden okunmaz (Tek-kaynak yasası: aynı gerçeğin iki kopyası
# sessizce ayrışır). Küme girdisi bir DİZİNSE silme fazı vardır — git'te silinmiş bir belge
# canlıda hayalet olarak kalmasın; bir DOSYAysa YOKTUR. Silme kapsamı listesi de aynı diziden türer.
#
# KAPILAR — sırayla, ilk kırmızıda `DURDU:` + çıkış 1:
#   [0a] çalışma ağacı temiz (`status --porcelain` boş) — yarım iş canlıya gitmez.
#   [0b] HEAD push'lanmış (`rev-list --count origin/main..HEAD` = 0). Yalnız A1'de duran bir
#        belge, hiçbir klonun göremediği bir gerçektir: cloud oturumları GitHub'daki hâli görür ve
#        canlı ile depo sessizce ayrışırdı. `fetch` DÜŞERSE kapı geçilmiş SAYILMAZ (fail-closed).
#   [0c] aktarım listesi git'ten türetilir. KAPI DEĞİL, RAPOR — istisnası: küme girdisi diskte
#        YOKSA ya da bir kök DOSYA git'te İZLİ DEĞİLSE durur (o girdi hiç taşınmazken "eşitlendi"
#        demek, taşınmayanı taşınmış bildirmek olurdu).
#   [0d] aktarım listesinde yasak sınıf dosya YOK (yukarıdaki liste) — hem küme dizisi hem
#        listedeki her yol. Sembolik bağlar burada RAPOR edilir (aktarılmazlar).
#   [1]  silme kapsamı kapısı + silme tavanı (yukarıdaki (3) ve (4)).
#
# ÇIKIŞ KODLARI: 0 = geçti (kuru koşum ya da doğrulanmış eşitleme) · 1 = DURDU (kapı, silme
#   kapsamı ihlali, silme tavanı ya da rsync'in kendi sıfır-dışı çıkışı) · 2 = eşitlendi ama
#   DOĞRULANAMADI (ROADMAP sha ayrışık ya da ölçülemedi; beyan yazılamadı) · 3 = kullanım hatası.
#   2 de bir BAŞARISIZLIKTIR: ölçülemeyen eşitleme "eşitlendi" sayılmaz.
#   rsync sıfır-dışı çıkarsa aktarım YARIM kalmış olabilir; o ana kadarki itemize izi SİLİNMEZ,
#   basılır ve yolu yazılır (kayıtsız kısmi yazım, Yasa 6 sınıfı bir körlüktür).
#
# BEYAN VE OKUYUCULARI (Yasa 6). `--uygula` sonunda A1'e `state/belge_esitleme.json` yazılır (TEK
# satır: esitlenen_sha · esitlendi_utc · esitleyen_host · dosya_n · silinen_n), geçici ad + `mv`
# ile ATOMİK, ardından geri okunup bayt kıyası yapılır. Dosya `state/` altındadır, yani `dagit.sh`
# rsync'i ona DOKUNMAZ — doğru yer: bir dağıtım, belge eşitlemesinin kaydını ezmemeli.
# OKUYUCU 1 — BU BETİK: her koşum `[3]` adımında son eşitleme kaydını A1'den okuyup BASAR.
# OKUYUCU 2 — PANO: `/api/roadmap` yanıtının `belge_esitleme` alanı (TSK-177 dilim 2; ayrı bir
# worktree'de hazır, uç bu dosyayı okuyup panoya "son eşitleme" satırı olarak basar).
# Yani beyan üretilip tüketilmeyen bir kanıt değildir; okuyucuları kaldırılırsa bu satır da
# kaldırılmalıdır.
#
# SIR: token hiçbir satıra BASILMAZ, ssh argümanına KONULMAZ **ve A1'de `curl`ün argümanına da
# GİRMEZ** — uzak istek `curl --config -` ile kurulur, yani başlık uzak sürecin stdin'inden
# okunur ve `ps aux` çıktısında görünmez. (Tur-1'de uzak kabuk `$_t`yi genişletip `curl`e argüman
# veriyordu; başlık bunun tersini iddia ediyordu — ölçülen ile yazılan ayrışmıştı.)
# `/api/roadmap` ölçümü İSTEĞE BAĞLIDIR: token yoksa "ölçülemedi: token yok" yazılır ve akış
# DURMAZ (uydurma yasağı: ölçülemeyen sayı uydurulmaz).
#
# --------------------------------------------------------------------------------------------
# RSYNC İKİLİSİ — SEÇİM VE LEHÇE KAPISI ([00], tur 4, TSK-177).
#
# ÖLÇÜLDÜ (Rol-1, 2026-09-08, A1'e karşı İLK `--kuru` koşumu): macOS `/usr/bin/rsync` openrsync'tir
# (protokol 29) ve A1 GNU rsync 3.2.7 ile PROTOKOL UYUMSUZDUR — `--from0 --files-from` ön-taraması
# A1 tarafında `ABORTING due to invalid path from sender: degerlendirme/PLAN-KONSOLIDE-2026-09-06.md`
# + `rsync error: protocol incompatibility (code 2)` verdi. Betik o gün DOĞRU durdu (`DURDU: rsync
# ÇIKIŞ 2`, fail-closed, sıfır yazım) ama kök sebep bir LEHÇE farkıydı, kapı eksikliği değil.
# `brew install rsync` (GNU 3.5.0, `/opt/homebrew/bin/rsync`) ile AYNI koşum TEMİZ geçti.
#
# SEÇİM SIRASI TEK YERDEDİR ([00] adımı — git durumundan bağımsız, betiğin İLK gate'i):
#   1. `RSYNC_BIN` ortam değişkeni verilmişse O kullanılır (testlerin şim geçersiz kılma yolu ve
#      operatörün elle belirtme yolu — Tek-kaynak yasası: seçim ikinci bir yerde tekrarlanmaz).
#   2. Yoksa `/opt/homebrew/bin/rsync` ÇALIŞTIRILABİLİRSE O kullanılır — bu Mac'te GNU rsync'in
#      kurulu olduğu bilinen konum.
#   3. Yoksa `command -v rsync` (PATH'teki ilk `rsync`).
# Seçilen ikilinin `--version` İLK SATIRI `openrsync` içeriyorsa betik DURUR — KURU koşumda DAHİ:
# yanlış lehçeyle "ön-tarama temiz geçti" sanıp `--uygula`ya geçmek, A1'de aynı `ABORTING`i
# üretirdi; kuru koşumun "hiçbir bayt yazmama" güvencesi lehçe uyuşmazlığını GÖSTERMEZ. Reçete
# basılır: `brew install rsync`. Mevcut davranışlara (iki faz, silme tavanı, `--checksum`)
# DOKUNULMAZ — bu kapı yalnız HANGİ `rsync` ikilisinin çağrıldığını belirler.
# --------------------------------------------------------------------------------------------
#
# KULLANIM
#   bash ops/belge_esitle.sh                 # KURU koşum (VARSAYILAN) — hiçbir yere yazmaz
#   bash ops/belge_esitle.sh --kuru          # aynısı, açıkça
#   bash ops/belge_esitle.sh --uygula        # ön-tarama + eşitle + beyan + doğrulama
#   bash ops/belge_esitle.sh --kok <yol>     # depo kökünü değiştir (test / ikinci checkout)
#
# ROL: Rol-1. Yan oturum ve ajan KOŞMAZ — canlıya yazan her yol ./dagit.sh ile aynı yetki
# sınıfındadır. KÖK VARSAYILANI `$HOME/AI-Trading`tir ve bu ./dagit.sh ile bilinçli olarak
# AYNIDIR: betiğin nereden çağrıldığına bakmak, bir worktree'nin kendi ağacını canlıya
# eşitlemesine kapı açardı.
set -euo pipefail

KEY="${MERIDIAN_A1_KEY:-$HOME/.ssh/oci-a1.key}"
IP="${MERIDIAN_A1_IP:-130.61.126.87}"
UZAK="${MERIDIAN_A1_DIR:-/opt/meridian}"
KOK="$HOME/AI-Trading"
SSH=(ssh -i "$KEY" -o ConnectTimeout=15 "ubuntu@$IP")

#: TEK KAYNAK — taşınacak belge kökleri. Bu dizi `tests/test_belge_esitle_v453.py` ile KİLİTLİDİR:
#: bir kök eklemek/çıkarmak testi kırar, yani kapsam genişlemesi sessiz olamaz. Silme kapsamı da
#: buradan TÜRER (aşağıdaki `_KAPSAM`) — ikinci bir liste sessizce ayrışırdı.
BELGE_KUMESI=("ROADMAP.md" "MERIDIAN_ENGINEERING_LOG.md" "docs" "research/cards")

MOD="kuru"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --kuru)   MOD="kuru";   shift ;;
    --uygula) MOD="uygula"; shift ;;
    --kok)    KOK="${2:?--kok bir dizin ister}"; shift 2 ;;
    *) echo "!! bilinmeyen argüman: $1"
       echo "   Kullanım: bash ops/belge_esitle.sh [--kuru|--uygula] [--kok <repo>]"; exit 3 ;;
  esac
done

# Yasak sınıf TEK yerde tanımlanır — kapı [0d] hem küme dizisini hem aktarım listesindeki her
# yolu BU fonksiyona sorar. İki ayrı liste tutulsaydı biri güncellenip öteki unutulurdu.
_yasak_mi() {
  case "$1" in
    *.py|*.sh)                              return 0 ;;
    meridian/*|ops/*|deploy/*|ui/*|state/*) return 0 ;;
    *.env|*.env.*|.env|.env.*)              return 0 ;;
  esac
  return 1
}

# sha256: A1 Ubuntu'da `sha256sum` her zaman vardır; geliştirme makinesi (macOS) `shasum -a 256`
# taşıyabilir. Hiçbiri yoksa değer UYDURULMAZ — "OLCULEMEDI" döner ve hüküm çıkış 2 olur.
_sha256_yerel() {
  if   command -v sha256sum >/dev/null; then sha256sum    "$1" | cut -d' ' -f1
  elif command -v shasum    >/dev/null; then shasum -a 256 "$1" | cut -d' ' -f1
  else printf '%s\n' "OLCULEMEDI"; fi
}

_RC=0
_IZ_KORU=0
IZ="$(mktemp -t belge_esitle_iz.XXXXXX)"
IZ_ON="$(mktemp -t belge_esitle_izon.XXXXXX)"
HAM="$(mktemp -t belge_esitle_ham.XXXXXX)"
IZSIZ_LOG="$(mktemp -t belge_esitle_izsiz.XXXXXX)"
BEYAN="$(mktemp -t belge_esitle_beyan.XXXXXX)"
LISTE_D="$(mktemp -d -t belge_esitle_liste.XXXXXX)"

# İZ KORUMASI: rsync sıfır-dışı çıkarsa taşınmış olabilecek şeyin TEK kaydı bu dosyalardır.
# Tur-1'de trap onları koşulsuz siliyordu — yarım aktarım izsiz kalırdı.
_temizle() {
  rm -f "$HAM" "$IZSIZ_LOG" "$BEYAN"
  rm -rf "$LISTE_D"
  if [[ "$_IZ_KORU" == "1" ]]; then
    echo "  (rsync izleri KORUNDU — kısmi aktarımın kaydı: $IZ_ON · $IZ)"
  else
    rm -f "$IZ" "$IZ_ON"
  fi
}
trap _temizle EXIT

echo "=== belge eşitleme · mod=$MOD · kök=$KOK · hedef=ubuntu@$IP:$UZAK ==="
cd "$KOK"

# ---------------------------------------------------------------------------------------------
# [00] RSYNC İKİLİSİ SEÇİMİ — git durumundan bağımsız, betiğin İLK gate'i (başlığa bak). Sıra:
# RSYNC_BIN ortam değişkeni → /opt/homebrew/bin/rsync (varsa) → command -v rsync. Seçilen ikili
# openrsync ise KURU koşumda DAHİ durulur — yanlış lehçeyle "temiz geçti" sanmak A1'de protokol
# uyumsuzluğuna kadar gizli kalırdı.
echo "--- [00] rsync ikili seçimi ---"
if [[ -n "${RSYNC_BIN:-}" ]]; then
  RSYNC="$RSYNC_BIN"
elif [[ -x /opt/homebrew/bin/rsync ]]; then
  RSYNC="/opt/homebrew/bin/rsync"
else
  RSYNC="$(command -v rsync)" || RSYNC=""
fi
if [[ -z "$RSYNC" ]]; then
  echo "DURDU: rsync bulunamadı — PATH'te yok, RSYNC_BIN de verilmedi."
  exit 1
fi
_RSYNC_SURUM="$("$RSYNC" --version 2>&1 | awk 'NR==1')"
if [[ "$_RSYNC_SURUM" == *openrsync* ]]; then
  echo "DURDU: yerel rsync openrsync — --files-from protokolü A1 GNU rsync ile uyumsuz (ölçüldü 2026-09-08)."
  echo "       seçilen ikili: $RSYNC ($_RSYNC_SURUM)"
  echo "       çare: brew install rsync (GNU 3.5.0, /opt/homebrew/bin/rsync otomatik seçilir),"
  echo "       ya da RSYNC_BIN=<GNU rsync yolu> ile açıkça ver."
  exit 1
fi
echo "  ✓ GNU rsync seçildi: $RSYNC"

# ---------------------------------------------------------------------------------------------
echo "--- [0a] çalışma ağacı temiz mi ---"
_kirli="$(git status --porcelain)"
if [[ -n "$_kirli" ]]; then
  echo "DURDU: çalışma ağacı KİRLİ — commit'lenmemiş belge canlıya gitmez."
  printf '%s\n' "$_kirli" | sed 's/^/    /'
  exit 1
fi
_HEAD="$(git rev-parse HEAD)"
echo "  ✓ temiz — HEAD $(git rev-parse --short HEAD)"

# ---------------------------------------------------------------------------------------------
echo "--- [0b] HEAD push'lanmış mı ---"
if ! git fetch -q origin; then
  echo "DURDU: 'fetch origin' BAŞARISIZ — HEAD'in push'lanmış olduğu ÖLÇÜLEMEDİ."
  echo "       Ölçülemeyen kapı geçilmiş sayılmaz (fail-closed)."
  exit 1
fi
_ITILMEMIS="$(git rev-list --count origin/main..HEAD)"
if [[ "$_ITILMEMIS" != "0" ]]; then
  echo "DURDU: HEAD push'lanmamış — $_ITILMEMIS commit origin/main'in ilerisinde."
  echo "       Push'lanmamış bir belgeyi canlıya koymak, cloud/GitHub ile A1'i ayrıştırır."
  echo "       Çare: push origin main"
  exit 1
fi
echo "  ✓ origin/main ile aynı hizada"

# ---------------------------------------------------------------------------------------------
# AKTARIM LİSTESİ — git'ten türer. Her küme girdisi için NUL-ayrık bir liste dosyası üretilir;
# rsync'e `--from0 --files-from=` ile verilir. `-z`/`--from0` çifti şart: boşluk ya da yeni satır
# taşıyan bir ad, satır-ayrık listede sessizce ikiye bölünürdü.
_liste_yolu() { printf '%s/%s.liste' "$LISTE_D" "$(printf '%s' "$1" | tr '/' '_')"; }

echo "--- [0c] aktarım listesi (git ls-files) + disk≠git raporu ---"
_N_IZLI=0
_YASAK=()
_BAGLAR=()
_DISK_FAZLA=()
for e in "${BELGE_KUMESI[@]}"; do
  if [[ ! -e "$e" ]]; then
    echo "DURDU: küme girdisi diskte YOK: $e"
    echo "       Var olmayan bir kökü 'eşitlendi' saymak, taşınmayanı taşınmış bildirmek olurdu."
    exit 1
  fi
  _L="$(_liste_yolu "$e")"
  # stderr DOSYAYA alınır, SUSTURULMAZ: aşağıdaki hata dalı onu aynen basar (Yasa 4).
  # Hata dalı TEK: iki girdi türü için iki kopya mesaj, sessizce ayrışan iki kopya olurdu — ve
  # mutasyonla ölçüldü ki biri kaldırıldığında çivi öteki sayesinde YEŞİL kalıyordu (kör nokta).
  _liste_rc=0
  if [[ -d "$e" ]]; then
    # Alt dizinden koşulur: `git ls-files` yolları O DİZİNE göre basar ve rsync'in beklediği
    # biçim tam olarak budur (`--files-from` yolları kaynak köküne GÖREdir).
    git -C "$e" ls-files -z > "$_L" 2>"$IZSIZ_LOG" || _liste_rc=$?
    _ONEK_E="$e/"
  else
    git ls-files -z -- "$e" > "$_L" 2>"$IZSIZ_LOG" || _liste_rc=$?
    _ONEK_E=""
  fi
  # Liste ALINAMAZSA kapı geçilmiş sayılmaz — [0b]'nin `fetch` dalıyla aynı fail-closed sınıfı:
  # ölçülemeyen bir aktarım kümesiyle canlıya yazmak, ne taşındığını bilmeden "eşitledim"
  # demektir. `set -e` ile sessizce düşmek sözleşme dışı bir çıkış kodu üretirdi.
  if [[ "$_liste_rc" != "0" ]]; then
    echo "DURDU: '$e' için aktarım listesi ALINAMADI (git ls-files düştü, çıkış $_liste_rc) —"
    echo "       ne taşınacağı ÖLÇÜLEMEDİ. Ölçülemeyen kapı geçilmiş sayılmaz (fail-closed)."
    sed 's/^/    /' "$IZSIZ_LOG"
    exit 1
  fi
  if [[ ! -d "$e" ]]; then
    if [[ ! -s "$_L" ]]; then
      echo "DURDU: küme girdisi git'te İZLİ DEĞİL: $e"
      echo "       Aktarım listesi git'ten türer; izli olmayan bir kök DOSYA hiç taşınmazken"
      echo "       'eşitlendi' demek, taşınmayanı taşınmış bildirmek olurdu."
      exit 1
    fi
  fi
  while IFS= read -r -d '' _f; do
    _N_IZLI=$((_N_IZLI + 1))
    _tam="$_ONEK_E$_f"
    if _yasak_mi "$_tam"; then _YASAK+=("$_tam"); fi
    if [[ -L "$_tam" ]]; then _BAGLAR+=("$_tam"); fi
  done < "$_L"
  # DİSK ≠ GİT RAPORU (yalnız dizinler; kök dosyalar yukarıda zaten izli olmak zorunda).
  # Bağlar da sayılır: `find -type f` onları GÖRMEZDİ ve tur-2'nin kör noktası tam oradaydı.
  if [[ -d "$e" ]]; then
    find "$e" \( -type f -o -type l \) -print | LC_ALL=C sort > "$LISTE_D/_disk"
    tr '\0' '\n' < "$_L" | sed "s|^|$e/|" | LC_ALL=C sort > "$LISTE_D/_git"
    while IFS= read -r _f; do
      if [[ -n "$_f" ]]; then _DISK_FAZLA+=("$_f"); fi
    done < <(LC_ALL=C comm -23 "$LISTE_D/_disk" "$LISTE_D/_git")
  fi
done
echo "  ✓ aktarım listesi git'ten türedi — $_N_IZLI izli yol"
if [[ ${#_DISK_FAZLA[@]} -gt 0 ]]; then
  echo "  ! disk ≠ git — ${#_DISK_FAZLA[@]} yol diskte VAR ama izli DEĞİL; aktarım listesinde YOK:"
  printf '    %s\n' "${_DISK_FAZLA[@]}"
  echo "    (RAPOR, kapı DEĞİL: rsync bu yolları hiç görmez. Ama SİLME fazının ölçütü disktir,"
  echo "     yani bu adlar hedefteki adaşlarını silinmekten KORUR — bilinçli bir bedel.)"
fi

# ---------------------------------------------------------------------------------------------
echo "--- [0d] aktarım listesinde yasak sınıf var mı ---"
for e in "${BELGE_KUMESI[@]}"; do
  if _yasak_mi "$e" || _yasak_mi "$e/"; then _YASAK+=("(küme kökü) $e"); fi
done
if [[ ${#_YASAK[@]} -gt 0 ]]; then
  echo "DURDU: bu yol YALNIZ belge taşır — kümede motor/ops/dağıtım sınıfı dosya var:"
  printf '    %s\n' "${_YASAK[@]}"
  echo "       Kod canlıya YALNIZ ./dagit.sh ile çıkar (worker durdurma + doğrulama kapılarıyla)."
  exit 1
fi
echo "  ✓ yasak sınıf yok (.py/.sh · meridian/ ops/ deploy/ ui/ state/ · *.env*)"
if [[ ${#_BAGLAR[@]} -gt 0 ]]; then
  echo "  atlandı: ${#_BAGLAR[@]} bağ — sembolik bağ AKTARILMAZ (rsync --no-links):"
  printf '    %s\n' "${_BAGLAR[@]}"
fi

# ---------------------------------------------------------------------------------------------
# SİLME KAPSAMI — kümeden TÜRETİLİR. Yalnız dizin girdilerinin ALTI silinebilir.
_KAPSAM=()
for e in "${BELGE_KUMESI[@]}"; do
  if [[ -d "$e" ]]; then _KAPSAM+=("$e/"); fi
done
_KAPSAM_METIN="$(printf '%s\n' "${_KAPSAM[@]}")"

# SİLME TAVANI: izli dosya sayısının %10'u, en az 5. Silinecekler KAYNAĞIN YOKLUĞUNDAN türer,
# yani "kaynak boş / kök yanlış" hâlinin imzası ANORMAL BÜYÜK bir silme listesidir.
_TAVAN=$(( _N_IZLI / 10 ))
if [[ "$_TAVAN" -lt 5 ]]; then _TAVAN=5; fi

# rsync itemize yollarını HEDEFE GÖRE basar (dizin aktarımında dizin-içi). Rapor ve kapı için
# küme girdisinin ön eki EKLENİR — yoksa silinen dosyanın hangi ağaçtan gittiği görünmezdi.
_onekle() {   # $1 = ham rsync çıktısı · $2 = yol öneki ("" = kök dosya çağrısı)
  awk -v p="$2" '
    # Ön ek YALNIZ yol taşıyan satırlara eklenir: itemize (`>f…`, `cd…`) ve `*deleting`. rsync
    # uyarı satırlarını ve `--max-delete` bildirimini de standart çıktıya basar (ölçüldü
    # 2026-09-08, openrsync) ve onlara ön ek eklemek metni bozardı: "Deletions docs/stopped…".
    match($0, /^(\*deleting|[<>ch.][fdlLDS][^ \t]*)[ \t]+/) {
      yol = substr($0, RLENGTH + 1)
      # MUTLAK yola ön ek EKLENMEZ: `docs//etc/passwd` anlamsızdır ve kapsam kapısının ön-ek
      # ayağını yanlışlıkla GEÇERDİ (tur-2 incelemesi Y4 — ölü ayağın asıl sebebi buydu).
      if (yol ~ /^\//) { print; next }
      print substr($0, 1, RLENGTH) p yol
      next
    }
    { print }
  ' "$1"
}

# Kapsam dışı silme yollarını basar. İKİ ihlal sınıfı: kapsam öneki tutmayan · `..` taşıyan.
# İkincisi tırmanma sınıfıdır: ön ek eklenmiş bir yol bile `..` ile kapsamdan çıkardı. Mutlak
# yol için ayrı bir ayak YOKTUR — mutlak yol kapsam önekiyle başlayamaz, ilk ayak onu yakalar
# (ölçüldü: ayrı ayak mutasyona kör kalıyordu, `_onekle`nin ön-ek hatası düzeltildi).
_kapsam_disi_yollar() {   # $1 = ön ekli iz dosyası
  # Kapsam listesi ORTAM üzerinden geçer: `awk -v` ataması SATIR SONU taşıyamaz (ölçüldü
  # 2026-09-08: `awk: newline in string`), ENVIRON ise ham metni olduğu gibi verir.
  BELGE_KAPSAM="$_KAPSAM_METIN" awk '
    BEGIN { n = split(ENVIRON["BELGE_KAPSAM"], K, "\n") }
    /^\*deleting/ {
      yol = $0
      sub(/^\*deleting[ \t]+/, "", yol)
      if (yol ~ /(^|\/)\.\.(\/|$)/) { print yol; next }
      icinde = 0
      for (i = 1; i <= n; i++) if (K[i] != "" && index(yol, K[i]) == 1) icinde = 1
      if (icinde == 0) print yol
    }
  ' "$1"
}

_kapsam_kapisi() {   # $1 = ön ekli iz dosyası · $2 = aşama etiketi
  local _disi
  _disi="$(_kapsam_disi_yollar "$1")"
  if [[ -n "$_disi" ]]; then
    echo "DURDU: silme kapsamı dışı yol ($2) — bu yolların git'te KARŞILIĞI YOK ve bu betiğin"
    echo "       onlara dokunma yetkisi de yok (A1'de research/ altı canlı-sahipli veri taşır):"
    printf '%s\n' "$_disi" | sed 's/^/    /'
    echo "       İzinli silme kapsamı (küme dizisinden türetilir): ${_KAPSAM[*]}"
    _IZ_KORU=1
    exit 1
  fi
}

# Çağrı TEK yerde kurulur; ön-tarama ve gerçek koşum AYNI diziyi kullanır (tek fark: `-n`).
# İki ayrı yerde kurulsaydı ön-taramanın ölçtüğü şey ile uygulananın yaptığı şey ayrışabilirdi.
_cagri_kur() {   # $1 = küme girdisi · $2 = faz ("aktarim" | "silme") → _CAGRI ve _ONEK
  local _l
  _l="$(_liste_yolu "$1")"
  if [[ -d "$1" ]]; then
    if [[ "$2" == "silme" ]]; then
      # SALT-SİLME geçişi: `--existing` yeni DOSYA yaratmaz, `--ignore-existing` var olan
      # DOSYAYI güncellemez — DOSYA aktarımı YOK (ölçüldü). openrsync'te eksik alt DİZİNLERİ
      # yine de yaratabilir ve dizin mtime'ını güncelleyebilir (ölçüldü, başlığa bak) — "sıfır
      # aktarım" DOSYA düzeyinde doğrudur, DİZİN düzeyinde değil. Ölçütü DİSKTİR (rsync ikinci
      # bir `--files-from` listesini `--delete` ile birlikte KULLANMAZ — ölçüldü, başlığa bak).
      _CAGRI=("${_BAYRAK[@]}" --delete "--max-delete=$_TAVAN" --existing --ignore-existing
              -e "ssh -i $KEY" "./$1/" "ubuntu@$IP:$UZAK/$1/")
    else
      # --checksum YALNIZ aktarım dalında (silme hiç taşımaz, bedelsiz olsa da anlamsız olurdu).
      # Rol-1 hükmü, A1 GNU rsync 3.2.7 ölçümü (2026-09-08): `-a`nın hızlı kıyası (boyut+mtime)
      # AYNI boyut + AYNI mtime taşıyan ama İÇERİĞİ değişen bir belgeyi SESSİZCE atlar — yalnız
      # `[3]`teki ROADMAP.md sha kıyası bunu yakalardı, o da SADECE ROADMAP.md içindir. Belge
      # kümesi küçük olduğu için bayt-bayt kıyasın bedeli önemsizdir.
      _CAGRI=("${_BAYRAK[@]}" --checksum --from0 "--files-from=$_l"
              -e "ssh -i $KEY" "./$1/" "ubuntu@$IP:$UZAK/$1/")
    fi
    _ONEK="$1/"
  else
    # Kök DOSYA: liste zaten depo-göreli tam yolu taşır, kaynak kökü `./`dir ve `--delete` YOK.
    # Ölçüldü: `--files-from` verildiğinde `./` ağacı TARANMAZ, yalnız listedeki ad taşınır.
    # `--checksum`: aynı gerekçe (yukarı bak) — kök dosyalar da hızlı kıyasın kör noktasına girer.
    _CAGRI=("${_BAYRAK[@]}" --checksum --from0 "--files-from=$_l" -e "ssh -i $KEY" "./" "ubuntu@$IP:$UZAK/")
    _ONEK=""
  fi
}

_kos_rsync() {   # $1 girdi · $2 faz · $3 hedef iz · $4 aşama · $5 "-n" ya da ""
  local _rc=0
  _cagri_kur "$1" "$2"
  : > "$HAM"
  if [[ -n "$5" ]]; then
    "$RSYNC" "$5" "${_CAGRI[@]}" > "$HAM" || _rc=$?
  else
    "$RSYNC" "${_CAGRI[@]}" > "$HAM" || _rc=$?
  fi
  _onekle "$HAM" "$_ONEK" >> "$3"
  if [[ "$_rc" == "25" ]]; then
    echo "DURDU: silme tavanı aşıldı — küme girdisi '$1' ($4). Tavan=$_TAVAN (izli yol: $_N_IZLI)."
    echo "       rsync çıkış 25: hedefte tavandan ÇOK dosya 'fazlalık' sayıldı. Silinecekler"
    echo "       KAYNAĞIN YOKLUĞUNDAN türer, yani bu, kaynağın BOŞ ya da KÖKÜN YANLIŞ olduğu"
    echo "       hâlin imzasıdır. Kapıyı gevşetmeden ÖNCE kökü ve kaynağı doğrula."
    sed 's/^/    /' "$3"
    _IZ_KORU=1
    exit 1
  fi
  if [[ "$_rc" != "0" ]]; then
    echo "DURDU: rsync ÇIKIŞ $_rc — küme girdisi '$1' ($4)."
    echo "       Sıfır-dışı çıkış, aktarımın YARIM kaldığı anlamına gelebilir; o ana kadarki"
    echo "       itemize izi silinmez, aşağıda basılır ve yolu yazılır."
    sed 's/^/    /' "$3"
    _IZ_KORU=1
    exit 1
  fi
}

# SIRA: önce TÜM aktarımlar, sonra TÜM silmeler. Silme geri alınamayan yarıdır — bir aktarım
# düşerse hiçbir silme koşmamış olur.
_faz_kos() {   # $1 = hedef iz · $2 = aşama etiketi · $3 = "-n" ya da ""
  for e in "${BELGE_KUMESI[@]}"; do
    _kos_rsync "$e" "aktarim" "$1" "$2" "$3"
  done
  for e in "${BELGE_KUMESI[@]}"; do
    if [[ -d "$e" ]]; then _kos_rsync "$e" "silme" "$1" "$2" "$3"; fi
  done
}

_BAYRAK=(-a --no-links --no-implied-dirs --itemize-changes)
echo "  rsync: $RSYNC — $_RSYNC_SURUM"

# ÖN-TARAMA HER MODDA ZORUNLUDUR: tek bayt yazılmadan önce silinecekler ölçülür ve kapıdan
# geçirilir. Kuru koşumun raporu da budur (`--uygula`da ayrıca gerçek koşum raporu basılır).
echo "--- [1a] rsync ÖN-TARAMA (-n: hiçbir bayt yazılmaz) ---"
_faz_kos "$IZ_ON" "ön-tarama" "-n"
_kapsam_kapisi "$IZ_ON" "ön-tarama"
_N_SIL_ON="$(awk '/^\*deleting/ {n++} END {print n+0}' "$IZ_ON")"

if [[ "$MOD" == "uygula" ]]; then
  # Z1 (tur-3 inceleme): tavan ÇAĞRI BAŞINADIR — toplamla YAN YANA basmak "tavan 5, en fazla
  # 5 gider" diye okunurdu. Her silme çağrısı KENDİ satırını alır, toplam AYRI ve TAVANSIZ basılır.
  echo "  ✓ ön-tarama kapsam kapısından geçti — tavan ÇAĞRI BAŞINADIR (toplam DEĞİL):"
  for e in "${BELGE_KUMESI[@]}"; do
    if [[ -d "$e" ]]; then
      _n_e="$(awk -v p="*deleting $e/" 'index($0, p) == 1 {n++} END {print n+0}' "$IZ_ON")"
      echo "    silinecek ($e): $_n_e (tavan $_TAVAN)"
    fi
  done
  echo "    silinecek toplam: $_N_SIL_ON"
  echo '--- [1b] rsync UYGULA (ön-taramayla AYNI argümanlar, -n YOK) ---'
  _faz_kos "$IZ" "uygula" ""
  _kapsam_kapisi "$IZ" "uygula"
else
  cat "$IZ_ON" > "$IZ"
fi

# SAYIM `awk` ile: eşleşme yokken de 0 ile çıkar (`grep -c` boş kümede rc=1 verip `set -e` ile
# betiği düşürürdü). Kısa okuyucu (`head`) KULLANILMAZ — yazan tarafa SIGPIPE gönderir ve raporu
# sessizce budar; kuru koşumun tamamı okunmak İÇİN vardır (bedel yasası).
_N_DOSYA="$(awk '/^[<>]f/ {n++} END {print n+0}' "$IZ")"
_N_SIL="$(awk '/^\*deleting/ {n++} END {print n+0}' "$IZ")"
sed 's/^/    /' "$IZ"
echo "  dosya_n=$_N_DOSYA  silinen_n=$_N_SIL"
if [[ "$MOD" == "uygula" && "$_N_SIL_ON" != "$_N_SIL" ]]; then
  echo "  ! ÖN-TARAMA ile GERÇEK koşum AYRIŞTI: ön-tarama $_N_SIL_ON, gerçek $_N_SIL silme."
  echo "    (aynı argümanlarla koşuldu — fark, iki koşum arasında canlıda bir değişiklik demektir)"
fi
if [[ "$_N_SIL" != "0" ]]; then
  echo "  SİLİNECEK — canlıda VAR, git'te YOK. HER ADI DOĞRULA (bunlar 'beklenen' değildir):"
  echo "    silme kapsamı yapısal olarak ${_KAPSAM[*]} altıyla sınırlıdır; dışına çıkan tek yol"
  echo "    betiği DURDURUR — ama kapsam İÇİNDE yanlış bir ad da silinebilir."
  awk '/^\*deleting/ {print "    " $0}' "$IZ"
fi

# ---------------------------------------------------------------------------------------------
if [[ "$MOD" == "uygula" ]]; then
  echo "--- [2] beyan (state/belge_esitleme.json → A1) ---"
  _UTC="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  printf '{"esitlenen_sha": "%s", "esitlendi_utc": "%s", "esitleyen_host": "%s", "dosya_n": %s, "silinen_n": %s}\n' \
    "$_HEAD" "$_UTC" "$(hostname)" "$_N_DOSYA" "$_N_SIL" > "$BEYAN"
  sed 's/^/    /' "$BEYAN"
  if "${SSH[@]}" "cat > $UZAK/state/.belge_esitleme.json.tmp && mv $UZAK/state/.belge_esitleme.json.tmp $UZAK/state/belge_esitleme.json" < "$BEYAN" \
     && "${SSH[@]}" "cat $UZAK/state/belge_esitleme.json" | cmp -s - "$BEYAN"; then
    echo "  ✓ beyan yazıldı — bayt-özdeş doğrulandı"
  else
    echo "  !! BEYAN YAZILAMADI/DOĞRULANAMADI — bu eşitleme kaydı görünmez kalır."
    _RC=2
  fi
fi

# ---------------------------------------------------------------------------------------------
echo "--- [3] doğrulama ---"
if [[ "$MOD" == "uygula" ]]; then
  _YEREL_SHA="$(_sha256_yerel ROADMAP.md)"
  if ! _UZAK_SHA="$("${SSH[@]}" "sha256sum $UZAK/ROADMAP.md | cut -d' ' -f1")"; then _UZAK_SHA=""; fi
  if [[ "$_YEREL_SHA" == "OLCULEMEDI" || -z "$_UZAK_SHA" ]]; then
    echo "  !! ROADMAP.md sha256 ÖLÇÜLEMEDİ (yerel=$_YEREL_SHA uzak='${_UZAK_SHA:-yok}') — eşitlik iddiası KURULAMAZ."
    _RC=2
  elif [[ "$_YEREL_SHA" == "$_UZAK_SHA" ]]; then
    echo "  ✓ ROADMAP.md EŞİT — sha256 $_YEREL_SHA"
  else
    echo "  !! ROADMAP.md AYRIK — yerel $_YEREL_SHA ≠ canlı $_UZAK_SHA"
    _RC=2
  fi
fi

# BEYANIN OKUYUCUSU (Yasa 6) — her koşumda basılır, `--kuru` dâhil.
if _SON="$("${SSH[@]}" "cat $UZAK/state/belge_esitleme.json")"; then
  echo "  son eşitleme kaydı: $_SON"
else
  echo "  son eşitleme kaydı: YOK ya da okunamadı (bu yol henüz hiç uygulanmamış olabilir)"
fi

# İSTEĞE BAĞLI ÖLÇÜM — panonun GERÇEKTEN gördüğü bayt. Token yoksa DURDURMAZ.
_DASH="$KOK/.dash.env"
if [[ -r "$_DASH" ]] && grep -q '^MERIDIAN_DASH_TOKEN=' "$_DASH"; then
  _TOK="$(awk '/^MERIDIAN_DASH_TOKEN=/{sub(/^MERIDIAN_DASH_TOKEN=/,""); print; exit}' "$_DASH")"
  # TOKEN HİÇBİR ARGV'YE GİRMEZ — ne yerel ssh'ın, ne A1'deki curl'ün. `--config -` başlığı
  # uzak sürecin STDIN'inden okur; uzak kabuk token'ı genişletmez, `ps aux` onu göremez.
  if _YANIT="$(printf 'header = "x-meridian-token: %s"\nurl = "http://127.0.0.1:8080/api/roadmap?ozet=1"\n' "$_TOK" \
                | "${SSH[@]}" 'curl -s -m 20 --config -')"; then
    _BAYT="$(printf '%s' "$_YANIT" | awk 'match($0, /"bayt": *[0-9]+/) {print substr($0, RSTART, RLENGTH); exit}' | tr -dc '0-9')"
    if [[ -n "$_BAYT" ]]; then
      echo "  /api/roadmap bayt=$_BAYT (yerel $(wc -c < ROADMAP.md | tr -d ' '))"
    else
      echo "  /api/roadmap: ölçülemedi — yanıtta 'bayt' alanı yok (uç yetki hatası döndürmüş olabilir)"
    fi
  else
    echo "  /api/roadmap: ölçülemedi — uca ulaşılamadı"
  fi
else
  echo "  /api/roadmap: ölçülemedi — token yok ($_DASH okunamıyor ya da MERIDIAN_DASH_TOKEN taşımıyor)"
fi

# ---------------------------------------------------------------------------------------------
if [[ "$MOD" == "kuru" ]]; then
  echo ">> KURU KOŞUM BİTTİ. Uygulamak için: bash ops/belge_esitle.sh --uygula"
elif [[ "$_RC" == "0" ]]; then
  echo ">> EŞİTLEME TAMAM $_HEAD $_UTC $_N_DOSYA"
else
  echo ">> EŞİTLEME DOĞRULANAMADI (çıkış $_RC) — belgeler taşındı ama eşitlik/beyan ÖLÇÜLEMEDİ."
fi
exit "$_RC"
