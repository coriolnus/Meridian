#!/usr/bin/env bash
# deploy/oracle-a1/kod_tazelik.sh — [5b] KOD-TAZELİK DEĞİŞMEZİ: "active" ≠ "yeni kodu koşuyor".
#
# NE ÖLÇER:  süreç başlangıcı  >=  en yeni  <kök>/meridian/**/*.py  mtime'ı
#
# ÖLÇÜLEN VAKA (2026-08-24). Dağıtım doğrulaması "iki birim de active" dedi ve bu DOĞRUYDU; ama
# `meridian-learn` 00:34:40'tan beri koşuyordu ve en yeni kaynak 11:53:16'ydı. Doğru bir cümle,
# ANLAMSIZ bir güvence verdi: `active`, sürecin hangi KODU taşıdığı hakkında hiçbir şey söylemez.
# Yarı-etkili bir dağıtım "TAMAM" damgası aldı.
#
# KAPSAM ELLE SAYILMAZ, ExecStart'TAN TÜRETİLİR. Birim adları yazılsaydı yarın eklenen bir birim
# aynı sessizlikle unutulurdu — düzeltilmek istenen sınıfın ta kendisi. Kural: `running` durumda VE
# ExecStart'ı kurulum kökünden python/uv koşan her `meridian*` birimi. `meridian-litestream`
# (litestream ikilisi, Python değil) kendiliğinden DIŞARIDA kalır.
#
# KUM HAVUZU İSTİSNASI (TSK-140, 2026-09-04): birim dosyasının KENDİ beyanı (Description "kum
# havuzunda") varsa süreç başlangıç kodunu taşır ve bitince yeni kodla açılır — bu IHLAL değil
# BEKLENEN'dir; çağıran onu dağıtım beyanına (`sandbox_eski_kod`) yazar, kapı DÜŞMEZ. Ad listesi
# YOK: işaret birimden türer, yarın eklenen kum-havuzu birimi de aynı yoldan geçer.
#
# NEREDEN GELDİ: gövde `dagit.sh`ın [5b] adımında `ssh '<çok satırlı kabuk>'` olarak gömülüydü.
# TSK-176 Faz A1'de dosyaya çıkarıldı — `deploy/ansible/dagit.yml` bunu `script:` ile koşturacak
# ve gömülü çok-satır kabuk bir Ansible görevinde YASAK (A0 kuralı + 2026-07-30 IndentationError
# vakası). Taşımada İKİ beyanlı değişiklik var, ölçüldü 2026-09-08:
#   (1) Kullanılmayan `bas=$(systemctl show … ExecMainStartTimestampMonotonic)` ataması DÜŞTÜ —
#       hiçbir satır onu okumuyordu (YASA 6: okuyucusuz yazım yok).
#   (2) mtime taraması İKİ PLATFORMLU: önce GNU `find -printf` (A1'in yolu — eski gömülü
#       gövdenin TEK yolu), boş dönerse BSD `find -exec stat -f`. İkinci dal betiğin geliştirici
#       makinesinde de ÖLÇÜLEBİLMESİ içindir — çiviyi platforma bağımlı kılmak, "koşamıyorum"
#       ile "temiz"i karıştırmaktır.
#
# SIRA BİR AYRINTI DEĞİL, KAPININ KENDİSİ (düzeltme turu 2, ölçüldü 2026-09-08). İlk yazımda
# sonda BSD-ÖNCELİKLİydi ve kapı A1'de HİÇ ÖLÇMÜYORDU: GNU'da `stat -f` FORMAT DEĞİL
# `--file-system`tir, yani `stat -f '%m %N' <dosya>` başarısız OLMAZ — format dizgesi bir operand
# sayılıp stderr'e hata düşer (`2>/dev/null` yutar), gerçek dosya için dosya-sistemi raporu
# STDOUT'a basılır. `_ENYENI` boş dönmediği için GNU yedeği hiç koşmaz, `_YENI` sayı yerine
# `Inodes:` olur ve `[ N -lt "Inodes:" ]` hata verip YANLIŞ döner: kapı her koşumda "temiz" der.
# İki onarım birlikte gerekir — sıra TERSİNE, ve türetilen değer SAYISAL KAPIdan geçer: sıra tek
# başına yarınki bir biçim değişikliğine karşı yine kör kalırdı (uydurma yasağı: ölçülemeyen
# değer "temiz" DEĞİLDİR).
#
# KULLANIM:  bash deploy/oracle-a1/kod_tazelik.sh [kurulum-kökü]     (varsayılan /opt/meridian)
#
# ÇIKTI — satır başına bir bulgu (bulgu yoksa hiçbir satır):
#   IHLAL     <birim> <yaş-sn> <en-yeni-kaynak>   süreç eski kodu koşuyor
#   BEKLENEN  <birim> <yaş-sn> <en-yeni-kaynak>   kum-havuzu birimi (TSK-140)
#   OLCULEMEDI <ne>                                ölçüm yapılamadı — "temiz" DEĞİLDİR
# ÇIKIŞ KODU: 0 = IHLAL yok (dağıtım sürer) · 1 = en az bir IHLAL (çağıran DURUR, beyan yazılmaz)
#
# NEDEN BEYANDAN ÖNCE KOŞAR: beyan `state/dagitim.json`a "bu sha canlıda" yazar. Süreçlerden biri
# eski kodu koşuyorsa o cümle YANLIŞTIR. Kapı önce düşerse dosya eski sha'da kalır — koşan
# sistemin GERÇEK hâli odur (operatör kararı 2026-08-24). Onarım: birimi döndür, dağıtımı tekrar
# koş (rsync idempotent).
#
# OKUYUCU (YASA 6): dagit.sh [5b] adımı · deploy/ansible/dagit.yml (Task 2) ·
# tests/test_ansible_dagit_v452.py bölüm A4d.
set -u

KOK="${1:-/opt/meridian}"

# En yeni kaynak: "epoch yol". GNU `find -printf` ÖNCE (A1'in yolu; macOS find onu "unknown
# primary" ile reddeder → boş); boş dönerse BSD `find -exec stat -f`. Sıranın gerekçesi başlıkta.
_ENYENI="$(find "$KOK/meridian" -name "*.py" -printf '%T@ %p\n' 2>/dev/null | sort -rn | head -1)"
if [ -z "$_ENYENI" ]; then
  _ENYENI="$(find "$KOK/meridian" -name "*.py" -exec stat -f '%m %N' {} \; 2>/dev/null \
             | sort -rn | head -1)"
fi
if [ -z "$_ENYENI" ]; then
  # ÖLÇÜLEMEYEN "temiz" DEĞİLDİR (uydurma yasağı) — ama IHLAL de değildir: çağıran 0 görür ve
  # satırı operatöre basar. Kaynak ağacı okunamıyorsa sorun dağıtımın kendisindedir, bu kapıda değil.
  echo "OLCULEMEDI kaynak-mtime-okunamadi"
  exit 0
fi
_YENI="${_ENYENI%% *}"; _YENI="${_YENI%.*}"          # epoch (kesir kırpılır — iki platform tek biçim)
_YENI_AD="${_ENYENI#* }"

# SAYISAL KAPI: "boş değil" ile "ölçüldü" AYNI ŞEY DEĞİLDİR. Sonda sayı olmayan bir şey
# döndürdüyse (GNU `stat -f` dosya-sistemi raporu; yarın değişecek bir çıktı biçimi) aşağıdaki
# `-lt` kıyası bash'te hata verip YANLIŞ döner ve betik sessizce "IHLAL yok" derdi — kapının tam
# tersi. Satır operatöre GÖRÜNÜR ve dagit [5b] onu mevcut "ölçülemedi" dalıyla işler.
case "$_YENI" in
  ''|*[!0-9]*) echo "OLCULEMEDI kaynak-mtime-sayisal-degil"; exit 0 ;;
esac

_IHLAL=0
for _u in $(systemctl list-units --type=service --state=running --no-legend --plain 2>/dev/null \
            | awk '{print $1}' | grep "^meridian"); do
  _es="$(systemctl show "$_u" -p ExecStart --value 2>/dev/null)"
  case "$_es" in *"$KOK"*python*|*"$KOK"*|*uv*) ;; *) continue ;; esac
  case "$_es" in *litestream*) continue ;; esac
  _bas_epoch="$(date -u -d "$(systemctl show "$_u" -p ExecMainStartTimestamp --value)" +%s 2>/dev/null)"
  if [ -z "$_bas_epoch" ]; then
    echo "OLCULEMEDI $_u sureç-baslangici-okunamadi"
    continue
  fi
  # Kaynak mtime'ıyla AYNI sayısal kapı: boş olmayan ama sayı olmayan bir damga (yerelleştirilmiş
  # `date`, biçim değişikliği) `-lt`yi hataya düşürür ve BİRİM sessizce temiz sayılırdı.
  _bas="${_bas_epoch%.*}"
  case "$_bas" in
    ''|*[!0-9]*) echo "OLCULEMEDI $_u sureç-baslangici-sayisal-degil"; continue ;;
  esac
  if [ "$_bas" -lt "$_YENI" ]; then
    _yas=$(( _YENI - _bas ))
    _acik="$(systemctl show "$_u" -p Description --value 2>/dev/null)"
    case "$_acik" in
      *"kum havuzunda"*) echo "BEKLENEN $_u $_yas $_YENI_AD" ;;
      *)                 echo "IHLAL $_u $_yas $_YENI_AD"; _IHLAL=1 ;;
    esac
  fi
done

exit "$_IHLAL"
