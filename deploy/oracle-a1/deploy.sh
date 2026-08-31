#!/usr/bin/env bash
# deploy.sh — Meridian'ı Oracle Cloud Always Free Ampere A1 (aarch64 Ubuntu) üzerine kurar.
# A1 ÜZERİNDE, repo /opt/meridian'a kopyalandıktan SONRA çalıştır. Idempotent: tekrar koşulabilir.
#
#   ssh ubuntu@<A1-IP>
#   sudo mkdir -p /opt/meridian && sudo chown ubuntu:ubuntu /opt/meridian
#   # (yerelden) rsync -az --exclude .venv ./ ubuntu@<A1-IP>:/opt/meridian/
#   cd /opt/meridian && bash deploy/oracle-a1/deploy.sh
#
# Not: normalde bu betiği ELLE koşman gerekmez — yereldeki cutover.sh (aynı dizinde) durdurma +
# rsync + bu betik + token + doğrulama sırasını tek komutta yürütür.
#
# DAGİT KAPSAMI DIŞI CANLI ARTEFAKTLAR (F9) — dagit BU DOSYALARI TAŞIMAZ, ELLE kurulur;
# ÇOĞUNUN kurulum adımı bu betiğin gövdesindedir (sudo cp + daemon-reload); İSTİSNALAR aşağıda
# ADIYLA işaretli — litestream.yml (`litestream_kur.sh`) ve aylık bucket kopyası (kendi birim
# başlığı) bu betikte KURULMAZ; "hepsi buradadır" demek onları görünmez kılardı. dagit.sh [F9]
# içerik kapısı her dağıtımda repo↔canlı sürüklenmesini RAPORLAR (engellemez — kurulum kararı ve
# bakım penceresi operatörün).
# SAYI DÜZYAZIYA GÖMÜLMEZ. Bu başlık bir zamanlar "DÖRT ARTEFAKT" diyor ve dördünü sayıyordu;
# `F9_LISTE` bu arada 11 çifte çıktı ve başlık sessizce yalan oldu — üstelik bayatlayan taraf tam
# da operatörün KURULUM adımlarını okuduğu yerdi. Tek kaynak dagit.sh `F9_LISTE`dir; aşağısı onun
# okunur özetidir ve kapsaması çivilidir
# (tests/test_dagit_f9_beyan_v266.py::test_f9_LISTESININ_TAMAMI_deploy_sh_BASLIGINDA_ADLANDIRILIR
#  — listedeki her artefakt burada TAM REPO YOLUYLA geçmek ZORUNDA; sayı ölçülmez, KAPSAMA
#  ölçülür):
#   * deploy/oracle-a1/meridian-sprint@.service   → /etc/systemd/system/  (v241 sprint cgroup birimi)
#   * deploy/oracle-a1/50-meridian-sprint.rules   → /etc/polkit-1/rules.d/  (v241 tetik izni)
#   * deploy/hermes/SOUL.md                       → ~ubuntu/.hermes/SOUL.md  (v242 hermes brifingi)
#   * deploy/hermes/config.yaml                   → ~ubuntu/.hermes/config.yaml  (v326 ajan duruşu)
#   * deploy/oracle-a1/meridian-tick-watchdog.service → /etc/systemd/system/  (asılı-tick bekçisi)
#   * deploy/oracle-a1/meridian-tick-watchdog.timer   → /etc/systemd/system/  (aynı bekçinin tetiği)
#   * deploy/oracle-a1/litestream.yml             → /etc/litestream.yml  (litestream_kur.sh, 2026-08-23)
#   * deploy/oracle-a1/meridian-aylik-bucket-kopya.service → /etc/systemd/system/  (aylık
#     bar-arşivi bucket kopyası; kurulumu KENDİ birim başlığındadır, bu betikte değil)
#   * deploy/oracle-a1/meridian-aylik-bucket-kopya.timer → /etc/systemd/system/  (aynı kopyanın tetiği)
#   * deploy/oracle-a1/meridian-brifing.service   → /etc/systemd/system/  (v327 — @sef kadansı 22:00 UTC)
#   * deploy/oracle-a1/meridian-brifing.timer     → /etc/systemd/system/  (o kadansın tek tetiği)
#   * deploy/oracle-a1/meridian-bekci.service     → /etc/systemd/system/  (Faz 3 — @bekci kadansı
#     10:00 UTC; AYRI birim, brifing'e ikinci ExecStart DEĞİL — gerekçe birim başlığında)
#   * deploy/oracle-a1/meridian-bekci.timer       → /etc/systemd/system/  (o kadansın tek tetiği)
#   * deploy/oracle-a1/meridian-karne.service     → /etc/systemd/system/  (Faz 4 — @karne kadansı
#     HAFTALIK: Cumartesi 16:00 UTC. AYRI birim; kadansı kardeşlerinden FARKLI olduğu için ortak
#     bir birime binmek bir teslimatın kadansını ötekinin kararı yapardı — gerekçe birim başlığında)
#   * deploy/oracle-a1/meridian-karne.timer       → /etc/systemd/system/  (o kadansın tek tetiği;
#     gün seçimi DEFTER SESSİZLİĞİdir, tercih değil — gerekçe timer başlığında)
#   * BOT PROFİLLERİ (Faz 2: @sef · Faz 3: @bekci · Faz 4: @karne) → ~ubuntu/.hermes/profiles/<ad>/ — her biri
#     ÜÇ dosya, ELLE kurulur. TAM REPO YOLLARIYLA yazılır, kısa adla DEĞİL — ve bu kural artık
#     KOŞULSUZ: `config.yaml`, `SOUL.md` ve `distribution.yaml` listede birden çok kez geçiyor,
#     basename eşleyen bir çivi bir profilin satırlarının silinmesini ötekiler yüzünden
#     gizlerdi (denetim 2026-08-30; kural Faz 3'te sayımdan bağımsız hâle getirildi):
#       - deploy/hermes/profiles/sef/distribution.yaml    (manifest; env beyanı — safe-root + anahtar)
#       - deploy/hermes/profiles/sef/config.yaml          (duruş: guard kancası · deny · kapalı araçlar)
#       - deploy/hermes/profiles/sef/SOUL.md              (botun kalıcı brifingi)
#       - deploy/hermes/profiles/bekci/distribution.yaml  (manifest; env beyanı — safe-root + anahtar)
#       - deploy/hermes/profiles/bekci/config.yaml        (duruş: guard kancası · deny · kapalı araçlar)
#       - deploy/hermes/profiles/bekci/SOUL.md            (botun kalıcı brifingi)
#       - deploy/hermes/profiles/karne/distribution.yaml  (manifest; env beyanı — safe-root + anahtar)
#       - deploy/hermes/profiles/karne/config.yaml        (duruş: guard kancası · deny · kapalı araçlar)
#       - deploy/hermes/profiles/karne/SOUL.md            (botun kalıcı brifingi)
#   * deploy/hindsight/hindsight-api.service      → /etc/systemd/system/  (Hindsight bellek API'si,
#     Faz-1 2026-08-31; /opt/hindsight/.env F9'DA DEĞİL — sır taşır, repoda yalnız env.iskelet durur)
#   * deploy/hindsight/hindsight-yedek.service    → /etc/systemd/system/  (gecelik pg_dump yedeği)
#   * deploy/hindsight/hindsight-yedek.timer      → /etc/systemd/system/  (o yedeğin tetiği 03:30 UTC)
#     KURULUM BU BETİKTE DEĞİL, BİLEREK: `hermes profile install` canlıda YENİ BİR AJAN KİMLİĞİ
#     doğurur ve bu operatör kararıdır (CLAUDE.md madde 5). Betiğin yaptığı iki şey var: her
#     botun kum havuzunu (`/opt/meridian/var/bots/<ad>`) YARATIR ve ÜÇ ADIMLIK reçeteyi BASAR.
#     "Tek komut" demek yanlış olurdu — ortadaki adım (profilin kendi `.env`i) atlanırsa profil
#     KURULUR, KOŞAR ve her gün sessizce HAM teslimata düşer: yani yanlış çalışır, bozuk görünmez.
#     ÇOĞALTMA BİLİNÇLİDİR, TEMBELLİK DEĞİL: profil blokları döngüye alınmadı çünkü her botun
#     SÜRÜCÜ BİRİMİ ad kuralından türetilemiyor (@sef'inki `meridian-brifing`) ve o türetmeyi
#     UYDURMAK, bakım penceresinde koşan bir betikte ölçülmemiş bir çıkarım olurdu. Sürüklenmeyi
#     kopya DEĞİL ÇİVİ engelliyor: kapsam `deploy/hermes/profiles/` dizininden TÜRETİLİYOR
#     (tests/test_bot_profil_durusu_v329.py), yani üçüncü profil bu blokları YAZMADAN eklenemez.
# KISALTMA YASAK: "X.service + .timer" biçimi `.timer` dosyasının ADINI hiç yazmaz ve o ad
# listeden düşse başlık aynı kalırdı — yukarıdaki çivi tam olarak bunu reddediyor.
set -euo pipefail
cd "$(dirname "$0")/../.."   # repo kökü (/opt/meridian)
REPO="$(pwd)"
echo "== Meridian A1 kurulumu · $REPO =="

# 1) sistem paketleri
#    redis-server ŞART, opsiyonel değil: meridian/hotstate.py sıcak durumu (heartbeat, mrd:bars ring)
#    Redis'te tutar ve meridian/barsarchive.py o ring'i okuyup diske arşivler. Redis yoksa arşivci
#    her turda "REDIS YOK" deyip boşa döner, dakikalık barlar TEMELLİ kaybolur.
#    Ubuntu paketi VARSAYILAN OLARAK yalnız 127.0.0.1 dinler (/etc/redis/redis.conf → `bind 127.0.0.1
#    -::1`). BU AYARA DOKUNMA: A1'in public IP'sinde parolasız Redis açmak anlamına gelir.
if command -v apt-get >/dev/null; then
  sudo apt-get update -qq
  sudo apt-get install -y -qq curl ca-certificates rsync redis-server >/dev/null
  sudo systemctl enable --now redis-server
  echo "-- redis: $(redis-cli ping 2>&1 | head -1)   (dinlenen adres: $(redis-cli CONFIG GET bind 2>/dev/null | tail -1))"
fi

# 2) uv (aarch64 Linux) — Meridian venv'i uv.lock'tan bire bir kurulur (derleme yok, hepsi wheel)
if ! command -v uv >/dev/null 2>&1; then
  echo "-- uv kuruluyor"
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi
export PATH="$HOME/.local/bin:$PATH"
echo "uv: $(uv --version)"

# 3) Meridian bağımlılıkları (uv.lock → tekrarlanabilir; aarch64 wheel'leri)
echo "-- uv sync (bağımlılıklar)"
uv sync --frozen 2>/dev/null || uv sync
uv run python -c "import meridian.api, pandas, numpy, fastapi; print('meridian import OK')"

# 4) state/ var mı? (yoksa uyar — operatör yerelden rsync'lemeli)
if [ ! -f state/portfolio.json ] && [ ! -s state/meridian.db ]; then
  echo "!! state/portfolio.json (ya da state/meridian.db) yok — yereldeki state/ dizinini rsync'le:"
  echo "   rsync -az ./state/ ubuntu@<A1-IP>:/opt/meridian/state/"
fi
# sırlar 0600 (rsync -a izinleri taşır ama garanti altına al; dosya yoksa atla — SESSİZ DEĞİL)
for f in state/secrets.json state/auth.json; do
  if [ -f "$f" ]; then chmod 600 "$f"; echo "-- izin 0600: $f"; else echo "-- $f YOK (panodan girilecek)"; fi
done

# 5) hermes-agent (ajan beyni). Saf Python paketi → aarch64 Linux'a kurulabilir.
#    meridian/hermes.py:_hermes_bin() sırası: HERMES_LOCAL_BIN → PATH → ~/.hermes/bin/hermes →
#    ~/.local/bin/hermes. Resmi installer bunlardan birine kurar; meridian.service'in PATH'i
#    /home/ubuntu/.local/bin'i zaten içeriyor.
#    KURULUM BAŞARISIZSA YIKMIYORUZ: Meridian ajan yoksa deterministik öneriye düşer — döngü/kapı/
#    işlem çalışmaya devam eder (RUNBOOK Bölüm D). Ama sessizce geçmiyoruz (YASA 4).
HERMES_BIN=""
for c in "$(command -v hermes || true)" "$HOME/.hermes/bin/hermes" "$HOME/.local/bin/hermes"; do
  if [ -n "$c" ] && [ -x "$c" ]; then HERMES_BIN="$c"; break; fi
done
if [ -n "$HERMES_BIN" ]; then
  echo "-- hermes zaten kurulu: $HERMES_BIN"
else
  echo "-- hermes-agent yok → resmi installer koşuluyor (aarch64 Linux destekli)"
  if curl -fsSL https://hermes-agent.nousresearch.com/install.sh | sh; then
    export PATH="$HOME/.local/bin:$HOME/.hermes/bin:$PATH"
    for c in "$(command -v hermes || true)" "$HOME/.hermes/bin/hermes" "$HOME/.local/bin/hermes"; do
      if [ -n "$c" ] && [ -x "$c" ]; then HERMES_BIN="$c"; break; fi
    done
  else
    echo "!! HERMES KURULUMU BAŞARISIZ — kurulum durdurulmuyor, ama beyin zinciri EKSİK koşacak."
    echo "   Etki: nous bacağı ikili olmadan çalışmaz (state/secrets.json'da NOUS_API_KEY de YOK)."
    echo "   Kalan yol: gemini bacağı (GEMINI_API_KEY) veya Ayarlar'dan NOUS_ENDPOINT=<portal-url>."
    echo "   Hiçbiri yoksa Meridian deterministik öneriye düşer (döngü durmaz)."
  fi
fi
if [ -n "$HERMES_BIN" ]; then
  # DOĞRULAMA: ikilinin varlığı çalıştığını kanıtlamaz (yarım kurulum/venv kırığı olabilir).
  if "$HERMES_BIN" --version 2>&1 | head -1; then :; else
    echo "!! $HERMES_BIN çalışmıyor (--version başarısız) — beyin zinciri nous bacağı DEVRE DIŞI sayılmalı"
  fi
fi

# 6) systemd birimleri (yerli, docker yok)
echo "-- systemd birimleri"
sudo cp deploy/oracle-a1/meridian.service            /etc/systemd/system/meridian.service
sudo cp deploy/oracle-a1/meridian-barsarchive.service /etc/systemd/system/meridian-barsarchive.service
sudo cp deploy/oracle-a1/meridian-backup.service     /etc/systemd/system/meridian-backup.service
sudo cp deploy/oracle-a1/meridian-backup.timer       /etc/systemd/system/meridian-backup.timer
# OnFailure hedefi: meridian.service ölürse operatöre haber verir. enable EDİLMEZ (oneshot,
# yalnız OnFailure tetikler). Kanal kurulu değilse birim no-op'tur ve nedenini journal'a yazar.
sudo cp deploy/oracle-a1/meridian-fail-notify.service /etc/systemd/system/meridian-fail-notify.service
# ASILI-TİCK BEKÇİSİ (2026-08-02 küçük-kuyruk turu — BU ADIM EKSİKTİ).
# Bekçi 2026-07-31'de CANLIDA elle kurulmuştu ve depoda hiç yoktu; dolayısıyla bu betik onu
# KURMUYORDU. Sonucu: taze bir kurulum ya da `cutover.sh` (adım 4 bu betiği çağırır) panoyu
# asılı-tick korumasız canlıya çıkarırdı — "canlılık != ilerleme" vakası (2026-07-30 21:14→22:27,
# ölçülen sessizlik 73,1 dk) hiçbir bekçiye çarpmadan tekrarlanabilirdi.
sudo cp deploy/oracle-a1/meridian-tick-watchdog.service /etc/systemd/system/meridian-tick-watchdog.service
sudo cp deploy/oracle-a1/meridian-tick-watchdog.timer   /etc/systemd/system/meridian-tick-watchdog.timer
# BRİFİNG KADANSI (v327, 2026-08-27 — tick-watchdog'un AYNI SINIFI, üçüncü tekrar). `ops/
# alarm_backlog_digest.py` YAZILMIŞ ve ÇALIŞIYORDU ama HİÇBİR KADANSA ASILI DEĞİLDİ: canlıda 310
# teslim edilmemiş alarm ve 16 okunmamış iyileştirme önerisi birikmişti — sistem hesaplıyor,
# kimse okumuyordu. Birim İKİ teslimatı TEK sarmalayıcıyla koşturur: biri düşse öteki yine koşar
# VE herhangi biri düşerse birim `failed` olur (bkz. birim başlığı; `-` öneki BİLEREK YOK, o önek
# çıkış kodunu yutar ve Telegram kırıldığında arıza HER GÜN sessiz kalırdı).
# YEDEK ALINMAZ ve bu bilinçlidir: birim dosyaları repodan TAM olarak yeniden üretilir, canlıda
# elle yazılmış bir içerikleri yoktur (aşağıdaki ~/.hermes dosyalarının tersine).
#
# DEVİR KAPISI — `enable` KAPISININ İKİZİ, BİR KATMAN YUKARISI (denetim 2026-08-30). Aşağıdaki
# kapı yalnız timer'ın AÇILMASINI koruyordu; birim DOSYASI koşulsuz kopyalanıyordu. Timer A1'de
# zaten AÇIKSA (bir kez açıldıktan sonra öyle kalır — kapı bilerek "açık tut" der) ilgisiz bir
# sebeple koşan tek bir dağıtım günlük teslimatın ExecStart'ını sessizce `@sef`e çevirirdi:
# profil kurulu olmadığı için HAM modda, ve kimse bu devri KARAR olarak vermemişken. `cutover.sh`
# adım 4 bu betiği çağırıyor, yani "ilgisiz bir sebep" gündelik bir olaydır.
# KAPININ ŞEKLİ, `enable` kapısıyla AYNI: kadans KAPALIYSA kopyalamak zararsızdır (koşan bir şey
# yok) → kopyala. AÇIKSA yalnız (a) yürürlükteki ExecStart ZATEN `sef_brifingi.py` ise (devir
# olmuş, tazeleme idempotenttir) ya da (b) operatör `MERIDIAN_BRIFING_DEVRI=1` ile AÇIKÇA
# istediyse kopyalanır. Aksi hâlde DOKUNULMAZ ve yürürlükteki teslimat ADIYLA basılır.
BRIFING_ENABLED="$(systemctl is-enabled meridian-brifing.timer 2>/dev/null || true)"
BRIFING_EXEC="$(systemctl cat meridian-brifing.service 2>/dev/null | grep -m1 '^ExecStart=' || true)"
if [ "$BRIFING_ENABLED" != "enabled" ] || [ "${MERIDIAN_BRIFING_DEVRI:-0}" = "1" ] || \
   case "$BRIFING_EXEC" in *sef_brifingi.py*) true ;; *) false ;; esac; then
  sudo cp deploy/oracle-a1/meridian-brifing.service       /etc/systemd/system/meridian-brifing.service
  sudo cp deploy/oracle-a1/meridian-brifing.timer         /etc/systemd/system/meridian-brifing.timer
  echo "-- brifing birimi kuruldu/tazelendi (kadans=${BRIFING_ENABLED:-yok})"
else
  echo "!! BRİFİNG BİRİMİ DEVREDİLMEDİ — kadans AÇIK ve YÜRÜRLÜKTEKİ teslimat repodakinden farklı."
  echo "   YÜRÜRLÜKTEKİ: ${BRIFING_EXEC:-(okunamadı)}"
  echo "   REPODAKİ    : $(grep -m1 '^ExecStart=' deploy/oracle-a1/meridian-brifing.service)"
  echo "   Günlük Telegram teslimatını değiştirmek bir OPERATÖR KARARIDIR; bu dağıtım onu"
  echo "   kendiliğinden vermez. Devretmek için:  MERIDIAN_BRIFING_DEVRI=1 bash deploy/oracle-a1/deploy.sh"
fi
# BEKÇİ KADANSI (Faz 3 — @bekci). YUKARIDAKİ KAPININ İKİZİ, ve kopyalanmasının sebebi ŞU: bu
# birim `meridian-brifing`ten AYRIDIR ve ayrı olması ASIL KARARDIR (iki bot ayrı artefaktın
# sahibi; biri düşerse öteki koşmalı — tam gerekçe birim başlığında). Ayrı birim, ayrı kapı
# demektir: brifing'in `is-enabled` ölçümü bu timer hakkında HİÇBİR ŞEY söylemez.
# BUGÜN CANLIDA BU BİRİM YOK — yani "devir" bacağı bugün boş çalışır ve kapı sanki gereksizmiş
# gibi görünür. Değil: timer bir kez açıldıktan sonra AÇIK KALIR, ve o günden sonra ilgisiz bir
# sebeple koşan tek bir dağıtım (`cutover.sh` adım 4 bu betiği çağırıyor) çalışan bir teslimatın
# ExecStart'ını kimse karar vermeden değiştirebilirdi. Kapıyı birim doğarken koymak, onu bir
# vakadan SONRA koymaktan ucuzdur — `@sef`te tam tersi oldu.
BEKCI_ENABLED="$(systemctl is-enabled meridian-bekci.timer 2>/dev/null || true)"
BEKCI_EXEC="$(systemctl cat meridian-bekci.service 2>/dev/null | grep -m1 '^ExecStart=' || true)"
if [ "$BEKCI_ENABLED" != "enabled" ] || [ "${MERIDIAN_BEKCI_DEVRI:-0}" = "1" ] || \
   case "$BEKCI_EXEC" in *bekci_brifingi.py*) true ;; *) false ;; esac; then
  sudo cp deploy/oracle-a1/meridian-bekci.service         /etc/systemd/system/meridian-bekci.service
  sudo cp deploy/oracle-a1/meridian-bekci.timer           /etc/systemd/system/meridian-bekci.timer
  echo "-- bekçi birimi kuruldu/tazelendi (kadans=${BEKCI_ENABLED:-yok})"
else
  echo "!! BEKÇİ BİRİMİ DEVREDİLMEDİ — kadans AÇIK ve YÜRÜRLÜKTEKİ teslimat repodakinden farklı."
  echo "   YÜRÜRLÜKTEKİ: ${BEKCI_EXEC:-(okunamadı)}"
  echo "   REPODAKİ    : $(grep -m1 '^ExecStart=' deploy/oracle-a1/meridian-bekci.service)"
  echo "   Günlük Telegram teslimatını değiştirmek bir OPERATÖR KARARIDIR; bu dağıtım onu"
  echo "   kendiliğinden vermez. Devretmek için:  MERIDIAN_BEKCI_DEVRI=1 bash deploy/oracle-a1/deploy.sh"
fi
# KARNE KADANSI (Faz 4 — @karne). YUKARIDAKİ İKİ KAPININ ÜÇÜNCÜSÜ ve aynı gerekçelerle: birim
# `meridian-brifing`ten de `meridian-bekci`den de AYRIDIR (üç bot ayrı artefaktın sahibi; biri
# düşerse ötekiler koşmalı), yani `is-enabled` ölçümü de AYRI olmak zorunda — bir timer'ın durumu
# öteki hakkında HİÇBİR ŞEY söylemez.
# BU BOTTA KAPI DAHA DA ÖNEMLİ, ÇÜNKÜ KADANS HAFTALIK: yanlışlıkla devredilen bir ExecStart
# günlük bir teslimatta bir gün sonra fark edilir, haftalıkta BİR HAFTA sonra. Ve `@karne`
# DEĞİŞTİ/AYNI işaretlerini son TESLİM EDİLEN karneye göre kuruyor — devir sırasında kaçan bir
# hafta yalnız bir mesajı değil bir kıyas halkasını da düşürür.
# BUGÜN CANLIDA BU BİRİM YOK — yani "devir" bacağı bugün boş çalışır ve kapı gereksizmiş gibi
# görünür. Değil: timer bir kez açıldıktan sonra AÇIK KALIR, ve o günden sonra ilgisiz bir
# sebeple koşan tek bir dağıtım (`cutover.sh` adım 4 bu betiği çağırıyor) çalışan bir teslimatın
# ExecStart'ını kimse karar vermeden değiştirebilirdi.
KARNE_ENABLED="$(systemctl is-enabled meridian-karne.timer 2>/dev/null || true)"
KARNE_EXEC="$(systemctl cat meridian-karne.service 2>/dev/null | grep -m1 '^ExecStart=' || true)"
if [ "$KARNE_ENABLED" != "enabled" ] || [ "${MERIDIAN_KARNE_DEVRI:-0}" = "1" ] || \
   case "$KARNE_EXEC" in *karne_brifingi.py*) true ;; *) false ;; esac; then
  sudo cp deploy/oracle-a1/meridian-karne.service         /etc/systemd/system/meridian-karne.service
  sudo cp deploy/oracle-a1/meridian-karne.timer           /etc/systemd/system/meridian-karne.timer
  echo "-- karne birimi kuruldu/tazelendi (kadans=${KARNE_ENABLED:-yok})"
else
  echo "!! KARNE BİRİMİ DEVREDİLMEDİ — kadans AÇIK ve YÜRÜRLÜKTEKİ teslimat repodakinden farklı."
  echo "   YÜRÜRLÜKTEKİ: ${KARNE_EXEC:-(okunamadı)}"
  echo "   REPODAKİ    : $(grep -m1 '^ExecStart=' deploy/oracle-a1/meridian-karne.service)"
  echo "   Haftalık Telegram teslimatını değiştirmek bir OPERATÖR KARARIDIR; bu dağıtım onu"
  echo "   kendiliğinden vermez. Devretmek için:  MERIDIAN_KARNE_DEVRI=1 bash deploy/oracle-a1/deploy.sh"
fi
# SPRINT ŞABLON BİRİMİ (v241, 2026-08-13 — tick-watchdog'un AYNI DERSİ, bu kez baştan uygulandı).
# Öğrenme sprinti 2026-08-13'e dek worker'ın çocuğu olarak doğuyordu (`sprint.py` Popen) ve systemd
# varsayılan `KillMode=control-group` yüzünden HER `systemctl restart meridian` onu biçiyordu —
# o gün üç sprint tam bu şekilde öldü (41, 113 ve 1 adımda; üçünün de tetiği bir restart'tı).
# Kendi birimi olduğu için artık worker'ın cgroup'unda DEĞİL; birim dosyasında `PartOf`/`BindsTo`/
# `After=meridian.service` BİLEREK YOK. `enable` EDİLMEZ (şablon + `[Install]` yok): örnekleri
# `sprint.start()` sid ile tetikler. Kurulmazsa sistem bozulmaz — kod `sprint_systemd_yok` olayıyla
# eski Popen yoluna GÖRÜNÜR şekilde düşer (`kosum_yolu` damgası), ama o yolda sorun geri gelir.
sudo cp deploy/oracle-a1/meridian-sprint@.service       /etc/systemd/system/meridian-sprint@.service
# POLKIT KURALI (v241, 2026-08-13 — CANLI ÖLÇÜMÜN sonucu): worker `NoNewPrivileges=true` altında
# koştuğu için `sudo` (setuid) root'a yükselemiyor ve sprint birimini tetikleyemiyordu. Bu kural
# yalnız `ubuntu` kullanıcısına, yalnız `meridian-sprint@*` birimleri için manage-units izni verir —
# `NoNewPrivileges=no` tavizini VERMEDEN (H3 koruma kalemi yerinde kalır). Eşlik eden satır:
# meridian.service `Environment=MERIDIAN_SPRINT_SYSTEMCTL=/usr/bin/systemctl` (tetiği sudo'suz yapar).
sudo cp deploy/oracle-a1/50-meridian-sprint.rules       /etc/polkit-1/rules.d/50-meridian-sprint.rules
sudo systemctl restart polkit
# HERMES BRİFİNGİ (SOUL.md) — v242, 2026-08-13. tick-watchdog ve polkit ile AYNI SINIF: dosya
# CANLIDA elle kurulmuştu ve depoda YOKTU, yani taze bir kurulum beyni brifingsiz açardı (ya da
# eski bir kopya elde kalırdı). Brifing ölçülebilir davranış üretir: 2026-08-13'te içindeki
# "araç çağrısı … yok" satırı ÇIKTI BİÇİMİNE daraltıldı çünkü bir üstteki maddenin ("skill'in
# SKILL.md'sini oku") tek uygulama yolunu yasaklıyordu — ölçüm: 1.113 oturumda %1,1 skill aracı
# çağrısı (docs/DENETIM-SKILL-CAGRI-IZI-2026-08-13.md). ÜZERİNE YAZMAZ: varsa yedeklenir.
if [ -f deploy/hermes/SOUL.md ]; then
  mkdir -p "$HOME/.hermes"
  [ -f "$HOME/.hermes/SOUL.md" ] && cp "$HOME/.hermes/SOUL.md" "$HOME/.hermes/SOUL.md.bak-$(date -u +%Y%m%d%H%M)"
  cp deploy/hermes/SOUL.md "$HOME/.hermes/SOUL.md"
  echo "-- hermes brifingi kuruldu: ~/.hermes/SOUL.md"
fi
# HERMES GÜVENLİK DURUŞU (config.yaml) — v326, 2026-08-27. SOUL.md ile AYNI SINIF ve AYNI DİZİN.
# Ölçüm (§9.0): canlıda `approvals` HİÇ TANIMLI DEĞİLDİ — tek savunma kendi şerhinde "parse
# edilemezse FAIL-OPEN" diyen guard kancasıydı. Dosya ayrıca `skills.external_dirs` ile
# `deploy/hermes/skills/` dizinini hermes'e KAYDEDER: o kayıt olmadan depodaki hiçbir SKILL.md
# yüklenmez (YASA 6 — okuyucusuz artefakt). Duruşu `tests/test_hermes_config_durusu_v326.py`
# çiviler; canlı↔repo sürüklenmesini dagit [F9] raporlar.
# ÜZERİNE YAZMAZ: varsa yedeklenir — SOUL.md ile aynı gerekçe, üstelik daha güçlüsü: `hermes
# config set` ve profil işlemleri BU DOSYAYA canlıda yazar, yani burada gerçekten kaybedilecek
# bir içerik olabilir.
if [ -f deploy/hermes/config.yaml ]; then
  mkdir -p "$HOME/.hermes"
  # SANİYE ÇÖZÜNÜRLÜĞÜ + EZMEME (denetim 2026-08-29): dakika damgası, aynı dakika içinde iki
  # deploy.sh koşumunda İLK yedeği repo kopyasıyla ezerdi — yani canlıda elle düzenlenmiş
  # config'in TEK kopyası, tam da onu korumak için yazılmış satır tarafından yok edilirdi.
  # `-n` (no-clobber) ikinci bir güvenlik: aynı saniyeye düşen iki koşum bile birbirini ezmez.
  [ -f "$HOME/.hermes/config.yaml" ] && cp -n "$HOME/.hermes/config.yaml" "$HOME/.hermes/config.yaml.bak-$(date -u +%Y%m%dT%H%M%SZ)"
  cp deploy/hermes/config.yaml "$HOME/.hermes/config.yaml"
  echo "-- hermes yapılandırması kuruldu: ~/.hermes/config.yaml"
fi
# ÇALIŞTIRMA BİTİ: rsync tabanlı dağıtım (dagit.sh / push_code_a1.sh) izinleri her zaman
# taşımayabilir; `Type=oneshot` bir ExecStart çalıştırılamazsa birim 203/EXEC ile düşer ve bekçi
# SESSİZCE ölür. Her koşuda garanti altına alınır (`.dash.env` izin sabitlemesiyle aynı sınıf).
sudo chmod +x deploy/oracle-a1/tick_watchdog.sh
# PANO TOKEN'I — BİRİMDE DEĞİL, 0600'lük /opt/meridian/.dash.env'te (H3 tur-1/2):
# meridian.service onu `EnvironmentFile=-/opt/meridian/.dash.env` ile okur; birim dosyası 0644'tür,
# sır oraya YAZILMAZ. Dosya SUNUCUDA üretilir, dağıtımla TAŞINMAZ (dagit.sh rsync'i .dash.env'i
# bilerek dışlar — 2026-08-01 vakası: --delete A1'dekini silmişti). Eski `grep CHANGEME` bekçisi
# ÖLDÜ: H3 tur-2 placeholder'ı birimden çıkarınca desen-bağımlı bekçi SESSİZ NO-OP oldu ve taze
# kurulum token'sız kalırdı — o yüzden desen değil DOSYANIN KENDİSİ ölçülür. İDEMPOTENT: dolu
# dosyaya DOKUNULMAZ; üzerine yazmak operatörün canlı token'ını habersiz döndürmek olurdu.
if [ ! -s /opt/meridian/.dash.env ]; then
  echo "-- pano token'ı üretiliyor → /opt/meridian/.dash.env (openssl rand -hex 24)"
  printf 'MERIDIAN_DASH_TOKEN=%s\n' "$(openssl rand -hex 24)" | sudo tee /opt/meridian/.dash.env >/dev/null
else
  echo "-- /opt/meridian/.dash.env zaten dolu — DOKUNULMADI (mevcut token korunuyor)"
fi
# izinler her koşuda garanti altına alınır (yukarıdaki secrets/auth chmod'larıyla aynı sınıf;
# içeriğe dokunmaz)
sudo chown ubuntu:ubuntu /opt/meridian/.dash.env
sudo chmod 600 /opt/meridian/.dash.env
# DOĞRULAMA (sed-vakası dersi: adımın gerçekleştiğini dosya söyler): dolu + 0600, değilse DUR —
# token'sız devam etmek panoyu parolasız canlıya çıkarmak olurdu
DASH_IZIN="$(stat -c '%a' /opt/meridian/.dash.env 2>/dev/null || echo YOK)"
if [ ! -s /opt/meridian/.dash.env ] || [ "$DASH_IZIN" != "600" ]; then
  echo "!! /opt/meridian/.dash.env DOĞRULANAMADI (izin=$DASH_IZIN) — pano token'sız kalırdı"
  exit 1
fi
echo "-- pano token'ı: /opt/meridian/.dash.env dolu + 0600 ✓"
mkdir -p /home/ubuntu/backups     # yedek hedefi — timer ilk atışta var olmalı
# @sef BOT KUM HAVUZU (Faz 2) — botun TEK yazılabilir dizini; brifing birimi
# `HERMES_WRITE_SAFE_ROOT` ile tam buraya bağlıyor. BU SATIR OLMADAN DİZİN HİÇ DOĞMAZ ve bunu
# ölçtük: `dagit.sh` rsync'i `/var`ı ANKORLU olarak DIŞLIYOR (aksi hâlde `--delete` botun
# biriktirdiği her şeyi her dağıtımda silerdi) ve `.gitignore` da `/var/` taşıyor — yani depo
# tarafında karşılığı YOK, canlıda birinin yaratması ŞART. Emsal bir üst satırdadır: yedek
# timer'ının hedefi de tam bu gerekçeyle burada yaratılıyor.
# 0700: kum havuzunun içeriği yalnız botu ilgilendirir ve umask'a bırakılan bir dizin makineden
# makineye farklı izinle doğar (`.dash.env` 0600 sabitlemesiyle aynı sınıf).
mkdir -p /opt/meridian/var/bots/sef
chmod 700 /opt/meridian/var/bots/sef
# SAHİPLİK ÖLÇÜLÜR, VARSAYILMAZ: betik `sudo bash deploy/...` ile koşulursa dizin ROOT'un olur ve
# birim (`User=ubuntu`) kendi kum havuzuna YAZAMAZ — üstelik sessizce, çünkü ham-brifing düşüş
# yolu tam bu arızayı maskeler (bot yazamaz, brifing yine gider, kimse fark etmez).
BOT_KUM_SAHIP="$(stat -c '%U' /opt/meridian/var/bots/sef 2>/dev/null || echo YOK)"
if [ "$BOT_KUM_SAHIP" != "ubuntu" ]; then
  echo "-- @sef kum havuzu sahibi '$BOT_KUM_SAHIP' — ubuntu'ya alınıyor"
  sudo chown -R ubuntu:ubuntu /opt/meridian/var/bots/sef
fi
echo "-- @sef kum havuzu hazır: /opt/meridian/var/bots/sef (0700, ubuntu) — manifestin kum-havuzu adımı BU BETİKTE yapıldı"
# @bekci BOT KUM HAVUZU (Faz 3) — üstteki blokla AYNI gerekçe, AYRI DİZİN. Ayrı olması §9.3'ün
# "her bot kendi artefaktının TEK yazarı" sözleşmesidir: paylaşılan bir kum havuzunda biri
# ötekinin damgasını/defterini ezebilirdi ve bu, iki botun da yanlış rapor vermesi demekti.
mkdir -p /opt/meridian/var/bots/bekci
chmod 700 /opt/meridian/var/bots/bekci
BEKCI_KUM_SAHIP="$(stat -c '%U' /opt/meridian/var/bots/bekci 2>/dev/null || echo YOK)"
if [ "$BEKCI_KUM_SAHIP" != "ubuntu" ]; then
  echo "-- @bekci kum havuzu sahibi '$BEKCI_KUM_SAHIP' — ubuntu'ya alınıyor"
  sudo chown -R ubuntu:ubuntu /opt/meridian/var/bots/bekci
fi
echo "-- @bekci kum havuzu hazır: /opt/meridian/var/bots/bekci (0700, ubuntu) — manifestin kum-havuzu adımı BU BETİKTE yapıldı"
# @karne BOT KUM HAVUZU (Faz 4) — üstteki iki blokla AYNI gerekçe, AYRI DİZİN (§9.3: her bot
# kendi artefaktının TEK yazarı). ÜÇÜNCÜ BOTLA AYRIKLIK DAHA DA BAĞLAYICI: paylaşılan bir kum
# havuzunda üç botun herhangi ikisi birbirinin dosyasını ezebilirdi ve hangisinin ezdiği
# ölçülemezdi.
mkdir -p /opt/meridian/var/bots/karne
chmod 700 /opt/meridian/var/bots/karne
KARNE_KUM_SAHIP="$(stat -c '%U' /opt/meridian/var/bots/karne 2>/dev/null || echo YOK)"
if [ "$KARNE_KUM_SAHIP" != "ubuntu" ]; then
  echo "-- @karne kum havuzu sahibi '$KARNE_KUM_SAHIP' — ubuntu'ya alınıyor"
  sudo chown -R ubuntu:ubuntu /opt/meridian/var/bots/karne
fi
echo "-- @karne kum havuzu hazır: /opt/meridian/var/bots/karne (0700, ubuntu) — manifestin kum-havuzu adımı BU BETİKTE yapıldı"
sudo systemctl daemon-reload
sudo systemctl enable meridian meridian-barsarchive
sudo systemctl enable --now meridian-backup.timer   # timer şimdi başlar; service'i o tetikler
sudo systemctl enable --now meridian-tick-watchdog.timer
# BRİFİNG KADANSI — DOSYA KURULUMU ile ETKİNLEŞTİRME AYRI EYLEMDİR (denetim 2026-08-29).
# Kardeş timer'lar burada koşulsuz `enable --now` yer; brifing İÇİN BU YANLIŞ OLURDU: bu birim
# operatöre GÜNLÜK TELEGRAM MESAJI gönderir. `cutover.sh` adım 4 bu betiği çağırıyor, yani
# ilgisiz bir sebeple koşan tek bir dağıtım, kimsenin karar vermediği bir bildirim kadansını
# AÇARDI. Kurulum kararı operatörün (başlıktaki F9 cümlesinin aynısı) — burada uygulanıyor.
# KENDİ KENDİNİ ONARIR: bir kez açıldıktan sonra her dağıtım onu AÇIK TUTAR (idempotent
# yeniden-enable); kapalıyken hiçbir dağıtım onu açmaz. Yani kapı yalnız İLK açılışa bakar.
# BİRİMİN KENDİSİ enable EDİLMEZ — `Type=oneshot`, tetiği timer'dır.
# `BRIFING_ENABLED` YUKARIDA, devir kapısında ÖLÇÜLDÜ — burada yeniden ölçülmez: aynı olgunun
# iki kaynağı, ikisinin ayrışabileceği anlamına gelir (bu betiğin `$HOME` dersiyle aynı sınıf).
# Aradaki adımlar timer'ın enable durumunu DEĞİŞTİRMEZ (yalnız dosya kopyalar).
if [ "$BRIFING_ENABLED" = "enabled" ]; then
  sudo systemctl enable --now meridian-brifing.timer
  # "kurulu != çalışır" — kardeş bekçiye uygulanan disiplin buraya da (denetim 2026-08-29).
  BRIFING_TIMER="$(systemctl is-active meridian-brifing.timer 2>&1 || true)"
  echo "-- brifing kadansı: enabled · timer=$BRIFING_TIMER · sonraki: $(systemctl list-timers meridian-brifing.timer --no-pager --no-legend 2>/dev/null | awk '{print $1, $2, $3}')"
  if [ "$BRIFING_TIMER" != "active" ]; then
    echo "!! meridian-brifing.timer AÇIKTI ama AKTİF DEĞİL — alarm yığını ve öneriler sessizce birikir"; exit 1
  fi
else
  echo "-- brifing kadansı: dosyalar KURULDU, kadans KAPALI (bilinçli — günlük Telegram teslimatı"
  echo "   operatör kararıdır). Kadansı açan komut (aşağıdaki @sef reçetesinin 3. adımı):"
  echo "       sudo systemctl enable --now meridian-brifing.timer"
  # TIRNAK KAÇIŞI, SÜS DEĞİL: bu satır bir zamanlar KAÇIRILMAMIŞ ters-tırnak taşıyordu ve çift
  # tırnak içinde ters-tırnak KOMUT İKAMESİDİR — `Persistent=true` bir atama olarak koşup BOŞ
  # dönüyordu, yani uyarı ekrana "birim  taşıyor" diye çıkıyordu. Uyarının öznesi sessizce
  # kayboluyordu; tam da bu betiğin her yerde kapattığı "sessiz kayıp" sınıfı.
  echo "   UYARI (systemd sözleşmesinden ÇIKARIM, bu kutuda ÖLÇÜLMEDİ): birim \`Persistent=true\`"
  echo "   taşıyor ve hiç tetiklenmemiş bir timer'ın damgası yoktur — ilk enable ANINDA bir koşum"
  echo "   ateşleyebilir. İlk mesajın hemen gelmesi arıza DEĞİLDİR."
fi
# BEKÇİ KADANSI — brifing kapısının İKİZİ, aynı gerekçelerle (bkz. yukarısı). AYRI ÖLÇÜM ŞART:
# iki timer bağımsızdır ve birinin `is-enabled` değeri öteki hakkında hiçbir şey söylemez.
# `BEKCI_ENABLED` YUKARIDA, devir kapısında ÖLÇÜLDÜ — burada yeniden ölçülmez (aynı olgunun iki
# kaynağı, ikisinin ayrışabileceği anlamına gelir). Aradaki adımlar enable durumunu DEĞİŞTİRMEZ.
if [ "$BEKCI_ENABLED" = "enabled" ]; then
  sudo systemctl enable --now meridian-bekci.timer
  BEKCI_TIMER="$(systemctl is-active meridian-bekci.timer 2>&1 || true)"
  echo "-- bekçi kadansı: enabled · timer=$BEKCI_TIMER · sonraki: $(systemctl list-timers meridian-bekci.timer --no-pager --no-legend 2>/dev/null | awk '{print $1, $2, $3}')"
  if [ "$BEKCI_TIMER" != "active" ]; then
    echo "!! meridian-bekci.timer AÇIKTI ama AKTİF DEĞİL — takılı/duran durumlar sessizce birikir"; exit 1
  fi
else
  echo "-- bekçi kadansı: dosyalar KURULDU, kadans KAPALI (bilinçli — günlük Telegram teslimatı"
  echo "   operatör kararıdır). Kadansı açan komut (aşağıdaki @bekci reçetesinin 3. adımı):"
  echo "       sudo systemctl enable --now meridian-bekci.timer"
  echo "   NOT: bu tetik @sef'inkinden 12 saat uzağa (10:00 UTC) kondu — iki bot AYNI operatöre"
  echo "   AYNI kanaldan yazıyor ve dakikalar arayla düşen iki mesaj tek yığın gibi okunur."
fi
# KARNE KADANSI — iki kardeş kapının ÜÇÜNCÜSÜ, aynı gerekçelerle (bkz. yukarısı). AYRI ÖLÇÜM
# ŞART: üç timer bağımsızdır. `KARNE_ENABLED` YUKARIDA, devir kapısında ÖLÇÜLDÜ — burada yeniden
# ölçülmez (aynı olgunun iki kaynağı, ikisinin ayrışabileceği anlamına gelir).
if [ "$KARNE_ENABLED" = "enabled" ]; then
  sudo systemctl enable --now meridian-karne.timer
  KARNE_TIMER="$(systemctl is-active meridian-karne.timer 2>&1 || true)"
  echo "-- karne kadansı: enabled · timer=$KARNE_TIMER · sonraki: $(systemctl list-timers meridian-karne.timer --no-pager --no-legend 2>/dev/null | awk '{print $1, $2, $3}')"
  if [ "$KARNE_TIMER" != "active" ]; then
    echo "!! meridian-karne.timer AÇIKTI ama AKTİF DEĞİL — amaç sorusu haftalarca cevapsız kalır"; exit 1
  fi
else
  echo "-- karne kadansı: dosyalar KURULDU, kadans KAPALI (bilinçli — haftalık Telegram teslimatı"
  echo "   operatör kararıdır). Kadansı açan komut (aşağıdaki @karne reçetesinin 3. adımı):"
  echo "       sudo systemctl enable --now meridian-karne.timer"
  echo "   NOT: bu tetik HAFTALIKtır (Cumartesi 16:00 UTC) ve GÜN bir tercih DEĞİL: hesap defteri"
  echo "   iki kez okuyup kıyaslıyor, araya düşen bir işlem eklemesi hükmü fail-closed olarak"
  echo "   ÖLÇÜLEMEDİ'ye çeviriyor. Cumartesi seans olmayan ilk gündür (Cuma kapanışına 19-20 sa)."
fi

# @sef PROFİLİ — DURUM RAPORU + REÇETE. Kapı DEĞİL, RAPOR: profilsiz bir kurulum BOZUK değildir,
# brifing ham yolundan teslim etmeye devam eder ([F9] kapısının duruşuyla aynı — sürüklenmeyi
# GÖRÜNÜR kıl, hükmü operatöre bırak). Aşağıdaki ÜÇ EYLEM manifestin (deploy/hermes/profiles/sef/
# distribution.yaml) kurulum notundakilerle AYNIDIR ve bu bir dilek değil ÇİVİLİ bir olgudur
# (tests/test_bot_profil_durusu_v329.py::test_RECETENIN_HER_EYLEMI_IKI_BELGEDE_DE_GECER). Bir
# kez ayrıştılar: manifest timer'dan hiç söz etmiyordu ve o eksik, operatörün okuduğu taraftaydı.
# PROFİL YOLU ÖLÇÜLÜR, VARSAYILMAZ (denetim 2026-08-30). `$HOME` bu betikte GÜVENİLİR DEĞİL:
# başlıktaki reçete `sudo mkdir`/`sudo cp` içeriyor ve betik `sudo bash deploy/...` ile
# koşulabilir — o hâlde `$HOME=/root` olur, kurulu profil "KURULU DEĞİL" raporlanır ve `.env`
# uyarısı HİÇ ateşlenmez. Kum havuzunun sahipliği bir üstte `stat` ile ÖLÇÜLÜYOR; burada da
# ölçülür: gerçek çağıran `SUDO_USER`dır, `$HOME` yalnız yedektir.
SEF_EV="$(getent passwd "${SUDO_USER:-$(id -un)}" 2>/dev/null | cut -d: -f6)"
SEF_PROFIL="${SEF_EV:-$HOME}/.hermes/profiles/sef"
SEF_KAYNAK="$REPO/deploy/hermes/profiles/sef"
echo "-- @sef profil yolu (ölçüldü, çağıran=${SUDO_USER:-$(id -un)}): $SEF_PROFIL"
# AYNI OLGUNUN İKİ KAYNAĞI KARŞILAŞTIRILIR (denetim 2026-08-30). Profil yolu iki yerde yaşıyor:
# burada (ölçülerek türetilir) ve birimde (`Environment=HERMES_HOME=…`, systemd `$HOME` ikamesi
# YAPAMAZ, o yüzden SABİT yazılmak zorunda). İkisi ayrışırsa arıza SESSİZDİR: bu betik "profil
# kurulu ✓" der, birim BAŞKA bir dizini gösterir, harness onu reddeder ve brifing sonsuza dek
# ham gider. Karşılaştırmak bir kapı değil bir ÖLÇÜMdür — hüküm operatörün.
SEF_BIRIM_HOME="$(grep -m1 '^Environment=HERMES_HOME=' deploy/oracle-a1/meridian-brifing.service | cut -d= -f3-)"
if [ "$SEF_BIRIM_HOME" != "$SEF_PROFIL" ]; then
  echo "!! @sef PROFİL YOLU AYRIŞIYOR — bu betik '$SEF_PROFIL' ölçtü, birim '$SEF_BIRIM_HOME' diyor."
  echo "   Zamanlanmış koşumu BİRİM belirler: yol yanlışsa harness profili REDDEDER ve brifing"
  echo "   HER GÜN sessizce ham gider (sıralama katmanı kalıcı kapanır, hiçbir şey kırmızı olmaz)."
fi
if [ -d "$SEF_PROFIL" ]; then
  echo "-- @sef profili KURULU: $SEF_PROFIL"
  # ORTADAKİ ADIM EN SESSİZ OLANIDIR, ve bu ÖLÇÜLDÜ: manifestteki env_requires .env YAZMAZ,
  # kurulu profile yalnız .env.EXAMPLE bırakır (.env kullanıcı-sahiplidir, dağıtım ona hiç
  # dokunamaz). Anahtarsız profil kurulur, koşar ve HER GÜN ham brifinge düşer — 'çalışıyor' görünür.
  if [ ! -s "$SEF_PROFIL/.env" ]; then
    echo "!! @sef .env YOK/BOŞ ($SEF_PROFIL/.env) — profil KURULU ama ANAHTARSIZ. Etkisi SESSİZ:"
    echo "   model her koşumda düşer, brifing HAM gider, teslimat 'çalışıyor' görünür. Doldur:"
    echo "       cp $SEF_PROFIL/.env.EXAMPLE $SEF_PROFIL/.env  &&  \${EDITOR:-nano} $SEF_PROFIL/.env"
  fi
else
  echo "-- @sef profili KURULU DEĞİL — brifing HAM yoldan teslim eder (bozuk değil, SIRALAMASIZ)."
  echo "   Kurmak ÜÇ AYRI EYLEMDİR ve 'tek komut' demek YANLIŞ olur: ortadaki atlanırsa profil"
  echo "   KURULUR ve YANLIŞ ÇALIŞIR (anahtarsız, hiç düşünmeden); sonuncusu atlanırsa hiç KOŞMAZ."
  echo "     1) hermes profile install $SEF_KAYNAK"
  echo "     2) cp $SEF_PROFIL/.env.EXAMPLE $SEF_PROFIL/.env  &&  \${EDITOR:-nano} $SEF_PROFIL/.env"
  echo "        (OPENROUTER_API_KEY — profilin KENDİ .env'i; dağıtım ona ASLA dokunmaz)"
  echo "     3) sudo systemctl enable --now meridian-brifing.timer"
  echo "   NOT, ADIM DEĞİL: kum havuzunu (/opt/meridian/var/bots/sef) bu betik zaten yarattı."
  echo "   GÜNCELLEME TUZAĞI (ölçüldü): 'hermes profile update sef' config.yaml'ı KORUR —"
  echo "   duruş değiştiyse 'hermes profile update sef --force-config' gerekir."
fi

# @bekci PROFİLİ — DURUM RAPORU + REÇETE (Faz 3). Yukarıdaki @sef bloğunun İKİZİ ve yine bir
# KAPI DEĞİL RAPOR: profilsiz bir kurulum BOZUK değildir, bekçi ham listeyi teslim etmeye devam
# eder (tespit deterministiktir; model yalnız SIRALAR). Aşağıdaki ÜÇ EYLEM manifestin
# (deploy/hermes/profiles/bekci/distribution.yaml) kurulum notundakilerle AYNIDIR ve bu bir
# dilek değil ÇİVİLİ bir olgudur (test_bot_profil_durusu_v329.py::
# test_RECETENIN_HER_EYLEMI_IKI_BELGEDE_DE_GECER — kapsam artık profil dizininden TÜRETİLİYOR,
# yani üçüncü bot bu bloğu yazmadan eklenemez).
BEKCI_EV="$(getent passwd "${SUDO_USER:-$(id -un)}" 2>/dev/null | cut -d: -f6)"
BEKCI_PROFIL="${BEKCI_EV:-$HOME}/.hermes/profiles/bekci"
BEKCI_KAYNAK="$REPO/deploy/hermes/profiles/bekci"
echo "-- @bekci profil yolu (ölçüldü, çağıran=${SUDO_USER:-$(id -un)}): $BEKCI_PROFIL"
BEKCI_BIRIM_HOME="$(grep -m1 '^Environment=HERMES_HOME=' deploy/oracle-a1/meridian-bekci.service | cut -d= -f3-)"
if [ "$BEKCI_BIRIM_HOME" != "$BEKCI_PROFIL" ]; then
  echo "!! @bekci PROFİL YOLU AYRIŞIYOR — bu betik '$BEKCI_PROFIL' ölçtü, birim '$BEKCI_BIRIM_HOME' diyor."
  echo "   Zamanlanmış koşumu BİRİM belirler: yol yanlışsa harness profili REDDEDER ve bekçi"
  echo "   HER GÜN sessizce ham liste gönderir (sıralama katmanı kalıcı kapanır, hiçbir şey kırmızı olmaz)."
fi
if [ -d "$BEKCI_PROFIL" ]; then
  echo "-- @bekci profili KURULU: $BEKCI_PROFIL"
  if [ ! -s "$BEKCI_PROFIL/.env" ]; then
    echo "!! @bekci .env YOK/BOŞ ($BEKCI_PROFIL/.env) — profil KURULU ama ANAHTARSIZ. Etkisi SESSİZ:"
    echo "   model her koşumda düşer, liste HAM gider, teslimat 'çalışıyor' görünür. Doldur:"
    echo "       cp $BEKCI_PROFIL/.env.EXAMPLE $BEKCI_PROFIL/.env  &&  \${EDITOR:-nano} $BEKCI_PROFIL/.env"
  fi
else
  echo "-- @bekci profili KURULU DEĞİL — bekçi HAM yoldan teslim eder (bozuk değil, SIRALAMASIZ)."
  echo "   Kurmak ÜÇ AYRI EYLEMDİR ve 'tek komut' demek YANLIŞ olur: ortadaki atlanırsa profil"
  echo "   KURULUR ve YANLIŞ ÇALIŞIR (anahtarsız, hiç düşünmeden); sonuncusu atlanırsa hiç KOŞMAZ."
  echo "     1) hermes profile install $BEKCI_KAYNAK"
  echo "     2) cp $BEKCI_PROFIL/.env.EXAMPLE $BEKCI_PROFIL/.env  &&  \${EDITOR:-nano} $BEKCI_PROFIL/.env"
  echo "        (OPENROUTER_API_KEY — profilin KENDİ .env'i; dağıtım ona ASLA dokunmaz)"
  echo "     3) sudo systemctl enable --now meridian-bekci.timer"
  echo "   NOT, ADIM DEĞİL: kum havuzunu (/opt/meridian/var/bots/bekci) bu betik zaten yarattı."
  echo "   GÜNCELLEME TUZAĞI (ölçüldü): 'hermes profile update bekci' config.yaml'ı KORUR —"
  echo "   duruş değiştiyse 'hermes profile update bekci --force-config' gerekir."
fi

# @karne PROFİLİ — DURUM RAPORU + REÇETE (Faz 4). Yukarıdaki iki bloğun ÜÇÜNCÜSÜ ve yine bir
# KAPI DEĞİL RAPOR: profilsiz bir kurulum BOZUK değildir, karne ölçülen dört hükmü teslim etmeye
# devam eder (hüküm deterministiktir; model yalnız SÖZE ÇEVİRİR). Aşağıdaki ÜÇ EYLEM manifestin
# (deploy/hermes/profiles/karne/distribution.yaml) kurulum notundakilerle AYNIDIR ve bu bir dilek
# değil ÇİVİLİ bir olgudur (test_bot_profil_durusu_v329.py::
# test_RECETENIN_HER_EYLEMI_IKI_BELGEDE_DE_GECER — kapsam profil dizininden TÜRETİLİYOR).
KARNE_EV="$(getent passwd "${SUDO_USER:-$(id -un)}" 2>/dev/null | cut -d: -f6)"
KARNE_PROFIL="${KARNE_EV:-$HOME}/.hermes/profiles/karne"
KARNE_KAYNAK="$REPO/deploy/hermes/profiles/karne"
echo "-- @karne profil yolu (ölçüldü, çağıran=${SUDO_USER:-$(id -un)}): $KARNE_PROFIL"
KARNE_BIRIM_HOME="$(grep -m1 '^Environment=HERMES_HOME=' deploy/oracle-a1/meridian-karne.service | cut -d= -f3-)"
if [ "$KARNE_BIRIM_HOME" != "$KARNE_PROFIL" ]; then
  echo "!! @karne PROFİL YOLU AYRIŞIYOR — bu betik '$KARNE_PROFIL' ölçtü, birim '$KARNE_BIRIM_HOME' diyor."
  echo "   Zamanlanmış koşumu BİRİM belirler: yol yanlışsa harness profili REDDEDER ve karne"
  echo "   HER HAFTA sessizce ham gider (sunum katmanı kalıcı kapanır, hiçbir şey kırmızı olmaz)."
fi
if [ -d "$KARNE_PROFIL" ]; then
  echo "-- @karne profili KURULU: $KARNE_PROFIL"
  if [ ! -s "$KARNE_PROFIL/.env" ]; then
    echo "!! @karne .env YOK/BOŞ ($KARNE_PROFIL/.env) — profil KURULU ama ANAHTARSIZ. Etkisi SESSİZ:"
    echo "   model her koşumda düşer, karne HAM gider, teslimat 'çalışıyor' görünür. Doldur:"
    echo "       cp $KARNE_PROFIL/.env.EXAMPLE $KARNE_PROFIL/.env  &&  \${EDITOR:-nano} $KARNE_PROFIL/.env"
  fi
else
  echo "-- @karne profili KURULU DEĞİL — karne HAM yoldan teslim eder (bozuk değil, SUNUMSUZ)."
  echo "   Kurmak ÜÇ AYRI EYLEMDİR ve 'tek komut' demek YANLIŞ olur: ortadaki atlanırsa profil"
  echo "   KURULUR ve YANLIŞ ÇALIŞIR (anahtarsız, hiç düşünmeden); sonuncusu atlanırsa hiç KOŞMAZ."
  echo "     1) hermes profile install $KARNE_KAYNAK"
  echo "     2) cp $KARNE_PROFIL/.env.EXAMPLE $KARNE_PROFIL/.env  &&  \${EDITOR:-nano} $KARNE_PROFIL/.env"
  echo "        (OPENROUTER_API_KEY — profilin KENDİ .env'i; dağıtım ona ASLA dokunmaz)"
  echo "     3) sudo systemctl enable --now meridian-karne.timer"
  echo "   NOT, ADIM DEĞİL: kum havuzunu (/opt/meridian/var/bots/karne) bu betik zaten yarattı."
  echo "   GÜNCELLEME TUZAĞI (ölçüldü): 'hermes profile update karne' config.yaml'ı KORUR —"
  echo "   duruş değiştiyse 'hermes profile update karne --force-config' gerekir."
fi
# @karne BİRİM DURUMUNU NASIL OKUMALI — BU BOTTA "yeşil mi?" REFLEKSİ YETMEZ.
# Kardeş botlarda birim durumu teslimatın ÖZETİDİR. @karne RAPOR botudur ve SUSMAZ: kadansı
# geldiyse mesaj her hâlükârda gider, hesap patlasa bile. Sonuç ikisi birden:
echo "-- @karne birim durumu nasıl okunur (ÖLÇÜLDÜ: ops/karne_brifingi.py::main — kaynak, canlı değil):"
echo "     çıkış 0 = TESLİM EDİLDİ. Dört hükmün NE DEDİĞİNDEN bağımsız: bir 'KALDI' BULGUdur,"
echo "               koşum hatası değil (aksi hâlde deneyin kötü her haftası birim arızası"
echo "               görünür ve operatör timer'ı susturur)."
echo "     çıkış 1 = gönderim düştü · çıkış 2 = bildirim kanalı yapılandırılmamış. İkisi de"
echo "               birimi 'failed' yapar ve /api/infra bunu 'arizali' diye panoya taşır."
echo "   İLK CANLI KOŞUM BİR DOĞRULAMA TURUDUR, TESLİMAT TURU DEĞİL: canlı defter uzun süredir"
echo "   sessizse ya da 30 işlem gününden kısaysa DÖRT hüküm de meşru olarak ÖLÇÜLEMEDİ döner."
echo "   DİKKAT — O HÂLDE BİRİM KIRMIZIYA DÖNMEZ, YEŞİL KALIR (çıkış 0): 'susmaz' sözleşmesi"
echo "   gereği mesaj gider. Yani hükmü BİRİM DURUMUNDAN DEĞİL MESAJIN GÖVDESİNDEN oku —"
echo "   '⚠ KARNE HESAPLANAMADI' satırı, ÖLÇÜLEMEDİ hükümleri ve kapsam beyanı oradadır:"
echo "       journalctl -u meridian-karne -n 80   ·   uv run python ops/karne_hesap.py --json"
echo "   ÖLÇÜLMÜŞ AÇIK KALEM (Rol-1'e devredildi, bu betik ÇÖZMEZ): ops/karne_hesap.py CLI'sı"
echo "   'dördü de ÖLÇÜLEMEDİ → çıkış 2' kapısını taşır ve gerekçesinde 'birim tam ölçüm"
echo "   kesintisinde sonsuza dek yeşil görünürdü' der — ama birim O CLI'yı değil harness'i"
echo "   koşuyor ve harness kesintiyi teslim edip 0 dönüyor. Kapı bugün birime ULAŞMIYOR."

# DOĞRULANMAMIŞ KALEMLER — BEYAN, İDDİA DEĞİL (UYDURMA YASAĞI). Kurulum çıktısı 'güvenli' izlenimi
# bırakır; o izlenimin ölçülmemiş kısımları burada ADIYLA söylenir, yoksa sessizce güvence olurlar.
# BİR KEZ BASILIR, PROFİL BAŞINA DEĞİL: ikisi de AYNI mekanizmanın ölçülmemiş kısmıdır (aynı
# Hermes ikilisi, aynı systemd duruşu) ve her profilde tekrarlamak, uyarıyı okunmaz kılardı.
echo "   DOĞRULANMADI (1) — KURULAN HER BOT PROFİLİ İÇİN (@sef · @bekci · @karne): profilin pre_tool_call"
echo "   guard kancasının BAŞSIZ (TTY'siz) koşumda gerçekten ateşlendiği CANLIDA HİÇ ölçülmedi."
echo "   Bilinen: satıcının kendi testi, TTY yokken ve onay bayrağı yokken kabuk kancalarının HİÇ"
echo "   kaydolmadığını söylüyor. Karşı-tedbir iki yanlı (config: hooks_auto_accept · çağrı:"
echo "   --accept-hooks) ama İKİSİ DE satıcı KAYNAĞINDAN okundu, gerçek bir başsız koşumdan DEĞİL."
echo "   DOĞRULANMADI (2): birimler ProtectHome=read-only altında koşuyor ve ~/.hermes yazma izni"
echo "   ReadWritePaths'e ÇIKARIMLA açıldı (emsal: meridian.service tur-1 EROFS kırıklığı)."
echo "   İkisini de ilk koşumdan sonra doğrula (ÜÇ BİRİM DE, ayrı ayrı — biri temiz koşuyor diye"
echo "   öteki koşuyor sayılmaz; @karne HAFTALIK olduğu için ilk kaydı BİR HAFTA gecikebilir,"
echo "   beklemek yerine 'sudo systemctl start meridian-karne.service' ile elle test-ateşle —"
echo "   'kurulu != çalışır', fail-notify dersi):"
echo "       journalctl -u meridian-brifing -n 50   ·   journalctl -u meridian-bekci -n 50"
echo "       journalctl -u meridian-karne -n 50"

# BEKÇİ KURULUM DOĞRULAMASI — "kurulu != çalışır" (fail-notify dersi, 2026-07-30: birim iki gün
# kuruluydu ve ilk test-ateşlemede IndentationError verdi). Burada ÜÇ ayrı gerçek ölçülür ve
# hiçbiri diğerinin yerine geçmez: (a) ExecStart hedefi gerçekten ÇALIŞTIRILABİLİR mi, (b) timer
# gerçekten AKTİF mi, (c) betik bir kez KOŞTURULDUĞUNDA beklenen satırı basıyor mu.
# (c) BİLEREK VAR: eski gömülü sürüm systemd `$` ikamesi yüzünden hiçbir zaman restart edemiyordu
# ve bunu YALNIZ çıktısına bakınca ("[tick-watchdog] ilerleme var (s)" — boş `${YAS}`) anlaşılıyordu.
# Desen değil DURUM ölçülür: hüküm satırı yaşı SAYIYLA basmalı.
if [ ! -x /opt/meridian/deploy/oracle-a1/tick_watchdog.sh ]; then
  echo "!! tick-watchdog betiği çalıştırılabilir değil — bekçi 203/EXEC ile sessizce ölürdü"; exit 1
fi
sudo systemctl start meridian-tick-watchdog.service || true
TICK_CIKTI="$(journalctl -u meridian-tick-watchdog.service -n 20 --no-pager 2>/dev/null | grep -o '\[tick-watchdog\].*' | tail -1)"
TICK_TIMER="$(systemctl is-active meridian-tick-watchdog.timer 2>&1 || true)"
echo "-- tick-watchdog: timer=$TICK_TIMER · son satır: ${TICK_CIKTI:-(YOK)}"
if [ "$TICK_TIMER" != "active" ]; then
  echo "!! meridian-tick-watchdog.timer AKTİF DEĞİL — asılı-tick koruması yok"; exit 1
fi
case "$TICK_CIKTI" in
  *"ilerleme var ("[0-9]*|*"bayat"*|*"ÖLÇÜLEMEDİ"*|*"YAS lütfu"*) : ;;
  *) echo "!! tick-watchdog beklenen hüküm satırını basmadı (systemd \$ ikamesi sınıfı?) — çıktı: ${TICK_CIKTI:-(YOK)}"; exit 1 ;;
esac

# 7) tohum + başlat
#    KORUMA (serve.sh:16 ile BİREBİR): dolu bir state üzerine replay KOŞULMAZ. Eski sürüm bu kontrolü
#    taşımıyordu → rsync'lenmiş CANLI state'in üstüne 2022→bugün replay koşabiliyordu.
#    SQLite GEÇİŞİ SONRASI TUZAK KAPALI (WP-H/H9, 2026-07-31): migrasyon sonrası defter
#    `state/meridian.db` içindedir ve `state/trades.jsonl` `.migrated` ekiyle durur — tek başına
#    `-s state/trades.jsonl` kontrolü DOLU defteri BOŞ görüp CANLI defterin üstüne replay koşardı.
if [ ! -s state/trades.jsonl ] && [ ! -s state/meridian.db ]; then
  echo "-- TOHUM: state/trades.jsonl boş/yok ve state/meridian.db yok → geçmişten tohumlanıyor (2022 → bugün)"
  uv run python -m meridian.run --dry-run --replay 2022-01-01:"$(date +%F)" \
    || echo "   (tohum başarısız — canlı turlarla devam edilecek; sebebi yukarıdaki çıktıda)"
elif [ -s state/trades.jsonl ]; then
  echo "-- TOHUM ATLANDI: state/trades.jsonl dolu ($(wc -l < state/trades.jsonl) satır) — taşınan canlı state korunuyor"
else
  echo "-- TOHUM ATLANDI: defter SQLite'ta (state/meridian.db) — taşınan canlı state korunuyor"
  uv run python -m meridian.dbmigrate --durum || true
fi
sudo systemctl restart meridian meridian-barsarchive
sleep 8

# 8) doğrulama
echo "== durum =="
printf 'redis-cli ping        : %s\n' "$(redis-cli ping 2>&1 | head -1)"
for u in redis-server meridian meridian-barsarchive; do
  # is-active aktif değilken 3 döner; set -e altında betiği düşürmesin — durum ZATEN basılıyor (YASA 4)
  printf '%-22s: %s\n' "$u" "$(systemctl is-active "$u" 2>&1 || true)"
done
systemctl --no-pager status meridian | head -6 || true   # status aktif değilken 3 döner; üstteki is-active satırı gerçeği söylüyor
echo "-- zamanlayıcılar --"
systemctl list-timers --no-pager 'meridian-*' || true    # timer hiç yoksa boş liste + 1 döner; üstte enable edildi
curl -s -o /dev/null -w "healthz  : %{http_code}  (200=taze, 503=bayat ama süreç canlı)\n" http://127.0.0.1:8080/healthz || true
curl -s -o /dev/null -w "api/today: %{http_code}\n" http://127.0.0.1:8080/api/today || true
echo ""
echo "PANO: SSH tünel öner →  ssh -L 8080:127.0.0.1:8080 ubuntu@<A1-IP>  → tarayıcıda http://localhost:8080"
echo "loglar:  journalctl -u meridian -f   ·   journalctl -u meridian-barsarchive -f"
