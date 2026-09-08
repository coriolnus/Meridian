#!/usr/bin/env bash
# =================================================================================================
# sir_credential_gecis.sh — motor sırlarını systemd LoadCredential kanalına taşır (TSK-064 Faz-1B)
# =================================================================================================
# SUNUCUDA (A1) KOŞAR — `deploy.sh`/`cutover.sh` ile aynı sözleşme. Otomatik ÇAĞRILMAZ: bakım
# penceresinde, operatör eliyle. `dash_token_credential.sh`in (TSK-049, pano token'ı) AD ALAN
# genelleştirilmişidir: orada tek bir sır ve tek amaçlı bir `.env` vardı, burada AYNI dosyada
# yaşayan İKİ sır + yapılandırma satırları var — bu fark faz-2'yi değiştirir (aşağıda).
#
# TANINAN ADLAR: NOUS_API_KEY · KAPI_APIKEY. Üçüncü bir ad bir YAZIM HATASIDIR ve reddedilir:
# sessizce hiçbir şey yapmak en kötü hâl olurdu, çünkü operatör "geçiş yapıldı" sanır.
#
# KULLANIM:
#   ./sir_credential_gecis.sh                    → DURUM (hiçbir şey değiştirmez; önce bunu koş)
#   ./sir_credential_gecis.sh --faz1 <ad>        → credential kanalı EKLE (ortam kanalı KALIR)
#   ./sir_credential_gecis.sh --faz2 <ad>        → farksal ölçüm + ortam satırını KAPAT
#   ./sir_credential_gecis.sh --geri-al <ad>     → ortam satırını geri yaz, drop-in'i kaldır
#   ./sir_credential_gecis.sh --faz1-hafiza      → FAZ-1A: motora TENANT credential'ı (54 drop-in)
#   ./sir_credential_gecis.sh --geri-al-hafiza   → 54 drop-in'i kaldır (vekil dosya yolunu kullanır)
#
# FAZ-1A NİYE BURADA VE NİYE YALNIZ İKİ ALT KOMUT. Hindsight'ın KENDİ geçişi (üç sır →
# `/etc/hindsight/creds/*`, `hindsight-api.service.d/50-creds.conf` + `hindsight-api-baslat.sh`)
# BAŞKA bir birime aittir ve bu betiğin sözleşmesi (`meridian` birimi, `/opt/meridian/.env`,
# `_kanit_nous`) oraya UYMAZ — genelleştirmeye zorlamak iki geçişi birbirinin rehinesi yapardı.
# Buraya YALNIZ motoru DÜŞÜREBİLECEK tek adım girdi: `54-hafiza-credential.conf` motorun birimine
# bir `LoadCredential=` satırı ekler ve kaynak dosya yoksa MOTOR HİÇ AÇILMAZ. O kapı belgeye değil
# koda yazılır (53'te olduğu gibi). Faz-2 (hindsight `.env`inden 3 satırın çıkarılması) hindsight
# tarafının işidir ve BU BETİKTE YOKTUR — burada olmayan şey, burada yapılmayacak şeydir.
#
# SIR DEĞERİ HİÇBİR YOLDA BASILMAZ VE ARGV'YE GİRMEZ. `ps` argv'yi makinedeki HERKESE gösterir;
# 2026-09-02'de bir parola tam olarak bu sınıftan (URL-gömülü, süzgeç kara-listeliydi) terminale
# düştü. Bu betikte değer YALNIZ 0600'lük geçici dosyalar üzerinden akar: `read -s` ile alınır,
# `cat` ile akıtılır; hiçbir `sed`/`awk` değişkenine, hiçbir komut satırına konmaz. Çivi:
# `tests/test_sir_credential_v439.py`.
#
# NEDEN FAZ-2 BURADA "SATIR SİLMEK": pano token'ı tek amaçlı `.dash.env`te yaşıyordu, o yüzden boş
# `EnvironmentFile=` sıfırlaması yetiyordu. `/opt/meridian/.env` ise sır DIŞINDA yapılandırma da
# taşır (NOUS_MODEL, NOUS_ENDPOINT, MERIDIAN_FMP_BASE); dosyanın okunmasını tümden kesmek onları da
# götürürdü. Faz-2 bu yüzden SATIR bazlıdır ve geri alma da satır bazlıdır.
#
# 2026-09-07 OLAYI VE BURADAN ÇIKAN DÖRT KAPI (çivi: `tests/test_sir_credential_duzeltme_v445.py`).
# `--faz1 <ad>` istemine BOŞ geçilince değer `.env`ten TAŞINIR; o yol `.env`in 1. SATIRINI okuyordu
# (satır ADRESİ), `^<ad>=` DESENİNİ değil. Canlı `.env`in 1. satırı boştu: credential dosyaları
# 1 baytlık satır sonuyla yazıldı, `.env` satırları değersiz kaldı, `--faz2` farksal ölçümü SAHTE
# geçti ve dakika çözünürlüklü yedek adı ikinci koşumda ilkini EZDİ. Bugünkü hâl:
#   1. DEĞER ADIYLA ARANIR. `.env` kaynağında yalnız `^<ad>=` satırı; satır yoksa değer YOKTUR.
#   2. BOŞ DEĞER DEĞER DEĞİLDİR. Boşluk dışı en az bir karakter yoksa betik DURUR ve o ana kadar
#      HİÇBİR şey yazılmamıştır (`test -s` "1 bayt = dolu" derdi).
#   3. YEDEK EZİLMEZ. Ad + saniye çözünürlüklü damga, çakışmada `.1`/`.2`.
#   4. ÖLÇÜMÜN ÖLÇÜMÜ. Faz-2 önce NEGATİF KONTROL koşar: iki kanal da SAHTEYKEN kanıt YOK demeli.
#      Kanıt her koşulda OK diyorsa farksal ölçüm bir tiyatrodur — betik "ölçülemedi" deyip durur
#      (uydurma yasağı) ve ortam satırına DOKUNMAZ. Bedeli bir ek restart + doğrulamadır.
#
# 2026-09-08 — YUKARIDAKİ DÖRT KAPININ AÇTIĞI YÜZEYLER (çekişmeli inceleme; çivi: v445 K1..K7).
# Negatif kontrol iki kanalı da sahteye çeker; o pencerede gerçek değerin diskteki TEK kopyası
# `.olcum-yedek` dosyalarıdır. Buradan üç kural doğdu:
#   5. `.olcum-yedek` SİLİNMEZ. Faz-2 ve --geri-al bu dosyalar dururken HİÇBİR ŞEY yapmaz ve
#      ÇIKIŞ 2 ile kurtarma komutlarını basar (çıkış 1 "geçiş başarısız", 2 "önce elle kurtar").
#      Kesintiye uğramış tur yeniden koşulursa eski kod o kopyaları ilk iş olarak siliyordu.
#   6. POZİTİF TABAN. Negatif kontrolün "YOK"u ancak kanıt ucu koşum ÖNCESİNDE OK diyorsa bir şey
#      söyler; "hep-YOK" hâlinde faz-2 ölçmediği bir nedeni ("faz-2 erken") iddia ederdi.
#   7. YEDEK SIRDIR. `.env` yedekleri artık `/root/meridian-env-yedek` altında (0700 dizin, 0400
#      root:root): `.env`in yanındaki 0600 ubuntu kopya, faz-2 ortam satırını kapattıktan SONRA
#      bile sırrı servis kullanıcısına açık düz metinde bırakıyordu.
# Ayrıca: `--geri-al` kendi yedeğini alır, ÖTEKİ adın YERİNDE duran `.env` satırına dokunmaz
# (credential kaynağı rotasyondan sonra bayat olabilir) ve `$ad`ın satırını geri yazamadıysa
# drop-in'i KALDIRMADAN durur (yoksa sır iki kanaldan birden düşerdi).
set -euo pipefail

# TEST KANCASI — YALNIZ ÇİVİ İÇİN. Boşken (üretimdeki tek hâl) yollar mutlaktır; v439 çivisi burayı
# tmp'ye çevirip `durum` ve `--geri-al` dallarını GERÇEKTEN koşturur. Ops aracını teslim etmeden
# önce operatörün koşacağı BİÇİMDE bir kez koşmanın yolu budur (18 çivi yeşilken `--uygula`nın
# sessizce yok sayıldığı 2026-08-30 vakasının dersi).
KOK="${SIR_GECIS_KOK:-}"
# KANCA GÖRÜNÜR OLMALI. Üretimde yanlışlıkla ayarlıysa betik gerçek yollara HİÇ dokunmadan
# "başarılı" raporlar ve operatör geçişi yaptığını sanır — sessiz kanca, sessiz körlüktür.
# Boşken (üretimdeki tek hâl) bu satır HİÇ basılmaz; çivi B6b/B6c iki ucu da ölçer.
if [ -n "$KOK" ]; then
  echo "!!!!! TEST KÖKÜ AKTİF: $KOK — GERÇEK SİSTEM YOLLARI KULLANILMIYOR !!!!!" >&2
fi

BIRIM="$KOK/etc/systemd/system/meridian.service.d"
ETC="$KOK/etc/meridian"
ENVF="$KOK/opt/meridian/.env"
DASH_KRED="$KOK/etc/meridian/dash_token"
DROPIN_AD=53-nous-kapi-credential.conf
#: FAZ-1A'nın MOTOR ayağı (spec Bulgu-3): pano vekili Hindsight TENANT anahtarını okur ve o okuma
#: `secrets.credential_oku` üzerinden credential dizinine taşındı (`api._hafiza_anahtari`).
#: KAYNAK, hindsight biriminin okuduğu DOSYANIN TA KENDİSİDİR — iki yol ayrışsaydı operatör aynı
#: sırrı iki kez üretir, ikisi ilk rotasyonda sessizce ayrışırdı. Çivi: v439 I10/I11c.
HAFIZA_DROPIN_AD=54-hafiza-credential.conf
HAFIZA_KRED="$KOK/etc/hindsight/creds/HINDSIGHT_API_TENANT_API_KEY"
KAYNAK_DIR="$(cd "$(dirname "$0")" && pwd)/meridian.service.d"
API="${SIR_GECIS_API:-http://127.0.0.1:8080}"
#: `.env` YEDEKLERİNİN YERİ. `.env`in yanında DEĞİL: yedek `.env`in TAM KOPYASIDIR, yani sırrı
#: düz metin taşır. `cp -p` ile doğan kopya 0600 `ubuntu:ubuntu` idi — faz-2 ortam satırını
#: kapattıktan sonra bile sır servis kullanıcısının okuyabildiği bir dosyada yaşamaya devam
#: ediyordu (geçişin amacını sessizce geri alan kalıntı). Dizin 0700 root, dosyalar 0400 root.
YEDEK_DIR="$KOK/root/meridian-env-yedek"

#: Drop-in'deki `LoadCredential=<ad>:<kaynak>` satırlarıyla BİREBİR aynı olmak ZORUNDA — ayrışırsa
#: betik bir dosyaya yazar, birim başka bir dosyayı arar ve arıza restart anında çıkar. Çivi F2.
ADLAR="NOUS_API_KEY KAPI_APIKEY"

die() { echo "!! $*" >&2; exit 1; }
# ÇIKIŞ KODU SÖZLEŞMESİ TEK YERDE ANLATILIR: başlık bloğunun 5. maddesi. Burada YALNIZ uygulaması
# durur — `die`=1, `die_kurtarma`=2. Sözleşmeyi ikinci kez burada anlatmak tek-kaynak ihlaliydi:
# başlık RUNBOOK'a ÜRETİLİR, bu şerh üretilmez; ikisi ayrışsa operatör belgede bir şey okur,
# bakımı yapan kodda başkasını görürdü. BEDELİ: kodu okuyan bir satır yukarı bakmak zorunda.
die_kurtarma() { echo "!! $*" >&2; exit 2; }
oldu() { echo "  ✓ $*"; }

_kaynak_yolu() {
  case "$1" in
    NOUS_API_KEY) echo "$KOK/etc/meridian/nous_api_key" ;;
    KAPI_APIKEY)  echo "$KOK/etc/meridian/kapi_apikey" ;;
    *) return 1 ;;
  esac
}

_ad_dogrula() {
  _kaynak_yolu "$1" >/dev/null 2>&1 || die "tanınmayan sır adı: $1 (tanınanlar: $ADLAR)"
}

# LoadCredential systemd 247'de geldi. ÖLÇÜLÜR, VARSAYILMAZ: eski bir systemd'de drop-in sessizce
# yok sayılmaz — birim "unknown directive" ile açılmayabilir ve arıza bakım penceresinin ortasında
# çıkar. Kapı burada, değişiklikten ÖNCE.
_systemd_kapisi() {
  local sv; sv="$(systemctl --version | head -1 | awk '{print $2}')"
  [ "${sv%%.*}" -ge 247 ] 2>/dev/null || die "systemd $sv < 247 — LoadCredential YOK. Geçiş yapılamaz."
}

_servis_ayakta() {
  systemctl is-active --quiet meridian || return 1
  for _ in $(seq 1 30); do
    [ "$(curl -s -o /dev/null -w '%{http_code}' "$API/healthz" 2>/dev/null || echo 000)" = "200" ] && return 0
    sleep 1
  done
  return 1
}

# --- DEĞER TAŞIMA — hepsi dosya üzerinden, hiçbiri argv üzerinden ---------------------------------
# Bir dosyanın boşluk DIŞI içeriği var mı? `test -s` "1 bayt = dolu" der ve 2026-09-07'de o 1 bayt
# bir satır sonuydu: kapı geçti, boş "değer" hem credential kaynağına hem `.env`e yazıldı. Değerin
# KENDİSİ hiçbir değişkene girmez — yalnız boşluk-dışı karakterlerinin SAYISI okunur.
_dolu_mu() {
  [ "$(sudo cat "$1" 2>/dev/null | tr -d '[:space:]' | wc -c | tr -d ' ')" != "0" ]
}

# `.env`teki `<ad>=` satırının DEĞERİ var mı? `_dolu_mu`nun satır ölçeğindeki kardeşi ve aynı
# hükmü taşır: `<ad>=` (değersiz) satır "ayarlı" DEĞİLDİR. Değerin KENDİSİ hiçbir değişkene
# girmez — yalnız boşluk-dışı karakterlerinin SAYISI okunur (`ps` argv'yi herkese gösterir).
_env_satiri_dolu_mu() {
  local ad="$1"
  [ "$(sudo sed -n "/^${ad}=/{s/^${ad}=//;p;q;}" "$ENVF" 2>/dev/null \
       | tr -d '[:space:]' | wc -c | tr -d ' ')" != "0" ]
}

# `durum` için TEK SATIRLIK KAYNAK ÖZETİ. Üç hâl AYRI: yok · var-ama-boş · dolu. Eski rapor
# `test -s` kullanıyordu, yani olay günü 1 baytlık satır sonuyla yazılmış kaynakları "hazır"
# gösteriyordu — rapor, kapıların ölçtüğü şeyle AYNI şeyi ölçmeli (tek-kaynak yasası). Boyut da
# basılır: "boş" ile "yok" farklı arızalardır ve farklı kurtarma gerektirir.
_kaynak_ozeti() {
  local k="$1" n
  sudo test -e "$k" 2>/dev/null || { echo "YOK"; return 0; }
  if ! _dolu_mu "$k"; then
    n="$(sudo cat "$k" 2>/dev/null | wc -c | tr -d ' ')"
    echo "BOŞ (${n:-0} bayt)"
    return 0
  fi
  sudo stat -c '%a %U:%G' "$k" 2>/dev/null || echo "izin okunamadı"
}

# `<kaynak>`taki `<ad>` değerini `<hedef>`e yazar. İKİ KİP, çünkü İKİ KAYNAK SINIFI var ve onları
# karıştırmak 2026-09-07 olayının ta kendisidir:
#   env  → ÇOK SATIRLI `/opt/meridian/.env`. YALNIZ `^<ad>=` ile başlayan İLK satırın değeri alınır.
#          Satır yoksa sonuç BOŞTUR ve çağıran durur — "1. satırı al" bir TAHMİNDİR, ve tahmin
#          edilen dizge hem 0400 credential kaynağına hem `.env`e yazılırdı (olayda öyle oldu).
#   kred → TEK SATIRLI credential kaynağı. Sözleşme `secrets.credential_oku` ile AYNI: önce `<ad>=`
#          öneki denenir (operatörün `.env` satırını kaynağa kopyalaması ÖNGÖRÜLEBİLİR bir kazadır),
#          bulunamazsa ÇIPLAK ilk dolu satır. `.env` kipinde bu düşüş YOKTUR: orada "önek yok"
#          demek "bu dosyada o sır yok" demektir, "değeri ilk satırdır" demek değil.
# ESKİ HÂL bir sed SATIR ADRESİ (`1{…}`) kullanıyordu, desen değil — yani adı hiç aramıyordu.
# O kalıbın geri gelmesini v445 B6e ayrıca kovalar; davranış hükmü v445 B1/B1b/B1c'dedir.
_deger_dosyala() {
  local src="$1" ad="$2" hedef="$3" kip="$4" n
  # ÇİFT SATIR = BELİRSİZ DEĞER. `EnvironmentFile` satırları üstüne yazar: yürürlükteki değer
  # SONuncudur, oysa aşağıdaki `;q` İLKİNİ alır. İkisi ayrıysa faz-1 credential kaynağına
  # yürürlükte OLMAYAN değeri yazar ve faz-2 farksal ölçümü onu "gerçek" sanar. Hangisinin
  # yürürlükte olduğunu ölçemiyoruz — tahmin etmek uydurmadır, betik durur. (Yalnız `.env`
  # kipinde: credential kaynağı tek satırlıktır ve orada "ikinci satır" bir kaynak sınıfı değil.)
  if [ "$kip" = "env" ]; then
    # sessiz-yutma: `grep -c` EŞLEŞME YOKKEN rc 1 döner ve `set -e` altında betiği burada düşürürdü; yutulan tek şey o rc'dir — sayının kendisi (0/1/N) hemen aşağıdaki kapıda ölçülüyor
    n="$(sudo grep -c "^${ad}=" "$src" 2>/dev/null || true)"
    [ "${n:-0}" -le 1 ] 2>/dev/null || die "ÇİFT SATIR: $src içinde ${n} adet '^${ad}=' satırı var
     — hangisi yürürlükte belirsiz (systemd SONuncuyu okur, bu betik ilkini). Önce fazlası elle
     silinir, sonra --faz1 $ad. HİÇBİR dosya değiştirilmedi."
  fi
  sudo sed -n "/^${ad}=/{s/^${ad}=//;p;q;}" "$src" 2>/dev/null | tr -d '\r' > "$hedef"
  if [ ! -s "$hedef" ] && [ "$kip" = "kred" ]; then
    sudo sed -n '/[^[:space:]]/{p;q;}' "$src" 2>/dev/null | tr -d '\r' > "$hedef"
  fi
}

# `.env` YEDEĞİ — AD + SANİYE çözünürlüklü damga, ve ASLA üstüne yazmaz. Eski ad
# (`$ENVF.bak-%Y%m%d%H%M`) hem ADSIZ hem DAKİKA çözünürlüklüydü: 2026-09-07'de NOUS faz-1'in yedeği
# KAPI faz-1 tarafından aynı dakika içinde EZİLDİ ve geri dönüşün tek dayanağı gitti. Yedeğin
# alınamaması sessiz geçilmez: yedeksiz bir yazım, geri dönüşü olmayan bir yazımdır.
_env_yedekle() {
  local etiket="$1" taban hedef n=0
  sudo install -d -m 0700 "$YEDEK_DIR" \
    || die "yedek dizini açılamadı: $YEDEK_DIR — değişiklik YAPILMADI"
  # sessiz-yutma: chown yalnız root olarak anlamlıdır ve dizin izni (0700) zaten bir satır üstte zorlanıyor; testteki sahte kökte root YOKTUR
  sudo chown root:root "$YEDEK_DIR" 2>/dev/null || true
  taban="$YEDEK_DIR/.env.bak-$etiket-$(date -u +%Y%m%dT%H%M%SZ)"
  hedef="$taban"
  while sudo test -e "$hedef"; do
    n=$((n + 1))
    [ "$n" -le 99 ] || die "yedek adı üretilemedi ($taban .1..99 dolu) — değişiklik YAPILMADI"
    hedef="$taban.$n"
  done
  sudo cp -p "$ENVF" "$hedef" || die "$ENVF yedeklenemedi ($hedef) — değişiklik YAPILMADI"
  # İZİN KISMA SESSİZ GEÇİLMEZ: yedek `.env`in tam kopyasıdır, yani sırrı düz metin taşır.
  # 0400'e düşürülemeyen bir yedek, geçişin kapatmaya çalıştığı okuma yüzeyini AÇIK bırakır.
  sudo chmod 0400 "$hedef" || die "$hedef izni 0400'e kısılamadı — değişiklik YAPILMADI"
  # sessiz-yutma: yukarıdaki gerekçenin aynısı — sahiplik root'suz ortamda değiştirilemez, izin kapısı bir satır üstte ZORLANIYOR
  sudo chown root:root "$hedef" 2>/dev/null || true
  oldu "yedek: $hedef (0400 root:root · dizin 0700)"
}

# YARIDA KALMIŞ ÖLÇÜM TURU KAPISI — faz-2 ve geri alma bu dosyalar dururken HİÇBİR ŞEY yapmaz.
# Negatif kontrol penceresinde iki kanal da SAHTEDİR; süreç orada ölürse (trap SIGKILL'i
# yakalayamaz) gerçek değerin diskteki TEK kopyası `.olcum-yedek` dosyalarıdır — betiğin kendi
# journal satırı da kurtarma yolu olarak onları gösterir. Eski kod faz-2'nin ilk işi olarak
# `rm -f` ediyordu: operatörün "aynı komutu bir daha koş" refleksi sırrı diskten TÜMÜYLE
# siliyor, üstelik "Değişiklik YAPILMADI" diye bitiyordu. Kurtarma ELLE yapılır: hangi kopyanın
# gerçek olduğunu ancak operatör bilir (yedek gerçek, asıl sahte — ya da tur ilerlemişse tersi).
# KALINTI DOSYALARININ LİSTESİ — TEK KAYNAK. Hem kapı (aşağıda) hem `durum` raporu BU listeden
# türer. Ayrı ayrı taransalardı sessizce ayrışırlardı ve tam olarak öyle olmuştu: kalıntı dururken
# kapı faz-2'yi çıkış 2 ile durduruyor, ama operatörün koşacağı İLK komut (`durum`) rc 0 verip
# `olcum-yedek` kelimesini HİÇ etmiyordu — kapı biliyor, rapor bilmiyordu (Yasa 6; ölçüldü
# 2026-09-08). Satır başına bir yol basar; hiçbir kalıntı yoksa hiçbir şey basmaz.
_olcum_kalintisi_listesi() {
  local a k
  if sudo test -e "$ENVF.olcum-yedek"; then echo "$ENVF.olcum-yedek"; fi
  for a in $ADLAR; do
    k="$(_kaynak_yolu "$a")"
    if sudo test -e "$k.olcum-yedek"; then echo "$k.olcum-yedek"; fi
  done
  return 0
}

_olcum_kalintisi_kapisi() {
  local y satir=""
  # KURTARMA HEDEFİ YOLUN KENDİSİNDEN TÜRETİLİR (`.olcum-yedek` eki atılır): liste ile reçete ayrı
  # ayrı yazılsaydı biri ötekini sessizce yanlış dosyaya yollardı — ve o `mv` sırrın tek kopyasıdır.
  while IFS= read -r y; do
    [ -n "$y" ] || continue
    satir="$satir
     sudo mv -f \"$y\" \"${y%.olcum-yedek}\""
  done <<EOF
$(_olcum_kalintisi_listesi)
EOF
  [ -z "$satir" ] || die_kurtarma "ÖNCEKİ ÖLÇÜM TURU YARIDA KALMIŞ — diskte '.olcum-yedek'
     dosyaları duruyor. Bu betik onları SİLMEZ: iki kanal da sahteyken süreç ölmüşse GERÇEK
     değerin tek kopyası onlardır. Önce kurtar:$satir
     sudo systemctl restart meridian
     Sonra bu komutu tekrarla. Değişiklik YAPILMADI."
}

# ÖLÇÜM PENCERESİNİN GERİ ALICISI (EXIT trap'i). Negatif kontrol ile farksal ölçüm arasında
# `.env` ve/veya credential kaynağı SAHTE değer taşır; betik oradan hangi sebeple çıkarsa çıksın
# (die dahil) gerçek değerler geri gelmelidir. Tur-1'de bu pencerenin trap'i `trap "true"` idi:
# "negatif kontrol sırasında servis açılmadı" diyen bir çıkış sistemi İKİ KANALI DA SAHTE
# bırakıyordu. Yedek dosyası yoksa (o adım zaten geri alınmışsa) sessizce atlanır.
_olcum_kurtar() {
  local k="$1"
  if sudo test -e "$k.olcum-yedek"; then sudo mv -f "$k.olcum-yedek" "$k"; fi
  if sudo test -e "$ENVF.olcum-yedek"; then sudo mv -f "$ENVF.olcum-yedek" "$ENVF"; fi
  # sessiz-yutma: restart'ın hatası bastırılır çünkü asıl geri alma iki `mv`dir ve onların hatası bastırılmaz; restart zaten bir sonraki elle koşumda tekrarlanır
  sudo systemctl restart meridian >/dev/null 2>&1 || true
}

# `.env` içindeki `<ad>=` satırını `<deger dosyası>`nın içeriğiyle DEĞİŞTİRİR (yoksa ekler).
# Komşu satırlara dokunmaz ve satırı ÇOĞALTMAZ: iki `<ad>=` satırı en sinsi hâl olurdu — systemd
# sonuncuyu okur, operatör ilkini düzenler ve iki değer sessizce ayrışır.
_env_satiri_yaz() {
  local ad="$1" src="$2" yeni
  yeni="$(mktemp)"; chmod 600 "$yeni"
  sudo grep -v "^${ad}=" "$ENVF" > "$yeni" 2>/dev/null || true
  printf '%s=' "$ad" >> "$yeni"          # printf KABUK BUILTIN'i — argv'ye giden bir süreç yok
  sudo cat "$src" >> "$yeni"
  sudo install -m 600 "$yeni" "$ENVF"
  sudo chown ubuntu:ubuntu "$ENVF" 2>/dev/null || true
  rm -f "$yeni"
}

_env_satiri_sil() {
  local ad="$1" yeni
  yeni="$(mktemp)"; chmod 600 "$yeni"
  sudo grep -v "^${ad}=" "$ENVF" > "$yeni" 2>/dev/null || true
  sudo install -m 600 "$yeni" "$ENVF"
  sudo chown ubuntu:ubuntu "$ENVF" 2>/dev/null || true
  rm -f "$yeni"
}

# --- KANIT: motor GERÇEKTEN iş yapıyor mu? -------------------------------------------------------
# `/healthz` YETMEZ: kimlik doğrulaması İSTEMEYEN bir uçtur ve sır tamamen yanlışken de 200 döner.
# `/api/secrets/test/nous` panonun içinden `hermes.ping_brain("nous")` çağırır — yani ölçüm
# MOTORUN KENDİ SÜRECİNDE, `_nous_headers`ın kurduğu başlıklarla yapılır. Ayrı bir python koşumu
# bunu ölçemezdi: o süreçte `$CREDENTIALS_DIRECTORY` YOKTUR ve ölçüm sessizce ortam kanalını
# ölçerdi. HTTP kodu da yetmez — uç anahtar yanlışken de 200 döner, hüküm gövdedeki `ok` alanıdır.
# Pano token'ı da argv'ye girmez: curl'e `-K` ile 0600 bir yapılandırma dosyasından verilir.
# O config'in KENDİ GRAMERİ var: değer `"` ile sınırlanır ve `\` bir KAÇIŞTIR. Kaçırılmamış bir
# token satırı bozar (curl ya config'i reddeder ya başlığı yanlış kurar) ve arıza "anahtar yanlış"
# gibi görünür — ölçüm yanlış yerde aranır. Kaçış SIRALI: önce `\`, sonra `"`. Çivi: v445 B6a.
# `-e t -e p` (etiketsiz `t`, ayrı ifadeler) `;t;p` ile AYNI iki-biçim okumasıdır ama TAŞINABİLİR:
# BSD sed `t` sonrasını etiket sanıp "undefined label" der ve okuma SESSİZCE boş döner — geliştirme
# makinesinde ölçülemeyen bir kapı, ölçülmemiş bir kapıdır.
_kanit_nous() {
  local cfg cvp
  cfg="$(mktemp)"; chmod 600 "$cfg"
  {
    printf 'silent\n'
    printf 'header = "x-meridian-token: '
    sudo sed -n -e 's/^MERIDIAN_DASH_TOKEN=//p' -e t -e p "$DASH_KRED" 2>/dev/null | head -1 \
      | tr -d '\r\n' | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g'
    printf '"\n'
    printf 'url = "%s/api/secrets/test/nous"\n' "$API"
  } > "$cfg"
  cvp="$(curl -K "$cfg" 2>/dev/null || true)"
  rm -f "$cfg"
  case "$cvp" in
    *'"ok": true'*|*'"ok":true'*) echo OK ;;
    *) echo YOK ;;
  esac
}

# KAPI_APIKEY'in ÖN KAPISI. Kapının key-auth kilidi yürürlükte DEĞİLSE yanlış anahtarla da 200
# gelir; o hâlde "motor iş yapıyor" hangi kanalın okunduğu hakkında HİÇBİR ŞEY söylemez ve farksal
# ölçüm bir tiyatrodur. Ölçülemeyen şeye "geçti" demek uydurmadır (uydurma yasağı) — betik durur.
_kapi_kilidi_olc() {
  local uc kod
  uc="$(sudo sed -n 's/^NOUS_ENDPOINT=//p' "$ENVF" 2>/dev/null | head -1 | tr -d '\r\n')"
  [ -n "$uc" ] || die "NOUS_ENDPOINT okunamadı — kapı ucu bilinmiyor, KAPI_APIKEY ölçümü YAPILAMAZ"
  kod="$(curl -s -o /dev/null -w '%{http_code}' -H 'apikey: bilerek-yanlis-anahtar' \
         "${uc%/}/models" 2>/dev/null || echo 000)"
  case "$kod" in
    401|403) oldu "kapı kilidi yürürlükte (yanlış apikey → HTTP $kod) — farksal ölçüm anlamlı" ;;
    *) die "KAPI_APIKEY ÖLÇÜLEMEZ: yanlış apikey ile HTTP $kod — kapı key-auth kilidi yürürlükte DEĞİL.
     Bu hâlde 'motor çalışıyor' hangi kanalın okunduğunu KANITLAMAZ. Önce kilit açılır
     (ops/apisix_uygula.py), sonra --faz2. Değişiklik YAPILMADI." ;;
  esac
}

# =================================================================================================
durum() {
  local k kalinti
  echo "=== DURUM (TSK-064 Faz-1B) ==="
  echo "  systemd sürümü: $(systemctl --version 2>/dev/null | head -1)"
  echo "  drop-in $DROPIN_AD: $([ -f "$BIRIM/$DROPIN_AD" ] && echo KURULU || echo yok)"
  echo "  LoadCredential (yürürlükte): $(systemctl show meridian -p LoadCredential --value 2>/dev/null || true)"
  # RAPOR, KAPILARIN ÖLÇTÜĞÜ ŞEYİ ÖLÇER. Kalıntı dururken faz-1/faz-2/geri-alma ÇIKIŞ 2 ile durur;
  # bunu söylemeyen bir "durum" operatörü sağlıklı sanıp o üç komuta yollar. `durum` SALT-OKUNURDUR:
  # durmaz, SÖYLER. Yol basılır, değer basılmaz (dosyalar sır taşır, adları taşımaz).
  kalinti="$(_olcum_kalintisi_listesi | tr '\n' ' ' | sed -e 's/[[:space:]]*$//')"
  if [ -n "$kalinti" ]; then
    echo "  ölçüm kalıntısı: VAR ($kalinti) — faz-1/faz-2/--geri-al DURUR (çıkış 2); önce kurtar"
  else
    echo "  ölçüm kalıntısı: yok"
  fi
  for ad in $ADLAR; do
    k="$(_kaynak_yolu "$ad")"
    echo "  $ad"
    echo "      credential kaynağı ($k): $(_kaynak_ozeti "$k")"
    echo "      ortam kanalı ($ENVF): $(sudo grep -qs "^${ad}=" "$ENVF" && echo VAR || echo yok)"
  done
  echo "  --- Faz-1A (pano vekili, Hindsight TENANT anahtarı) ---"
  echo "  drop-in $HAFIZA_DROPIN_AD: $([ -f "$BIRIM/$HAFIZA_DROPIN_AD" ] && echo KURULU || echo yok)"
  echo "      credential kaynağı ($HAFIZA_KRED): $(_kaynak_ozeti "$HAFIZA_KRED")"
  echo "  servis: $(systemctl is-active meridian 2>/dev/null || true) · healthz: $(curl -s -o /dev/null -w '%{http_code}' "$API/healthz" 2>/dev/null || echo 000)"
  echo "  (değerler BASILMAZ — yalnız izin/varlık.)"
}

# =================================================================================================
faz1() {
  local ad="$1" kred tmp eksik a
  _ad_dogrula "$ad"
  kred="$(_kaynak_yolu "$ad")"
  echo "=== FAZ 1: $ad → LoadCredential kanalı (ortam kanalı KALIR) ==="
  # KALINTI KAPISI FAZ-1'DE DE, İSTEMDEN VE HER YAZIMDAN ÖNCE. Betiğin KENDİ die'ları operatörü
  # buraya yolluyor ("Önce --faz1 $ad ile kaynak yeniden yazılır"); oysa yarıda kalmış bir turda
  # `.env` ölçümün ATILACAK sahte değerini taşır ve boş geçilen istem tam O DEĞERİ credential
  # kaynağına taşırdı: rc 0 + "iki kanal da canlı", iki kanal da çöp anahtar (ölçüldü 2026-09-08).
  _olcum_kalintisi_kapisi
  _systemd_kapisi
  [ -d "$KAYNAK_DIR" ] || die "drop-in kaynağı yok: $KAYNAK_DIR (depo güncel mi?)"

  tmp="$(mktemp)"; chmod 600 "$tmp"
  trap 'rm -f "$tmp"' EXIT

  # DEĞER OPERATÖRDEN, EKRANA YANSIMADAN. Boş bırakılırsa `.env`teki mevcut değer TAŞINIR — o hâlde
  # faz-1 tam anlamıyla hareketsizdir. Rotasyon istenirse yeni değer buraya yapıştırılır
  # (TSK-049 hükmü: rotasyon + kanal geçişi aynı pencerede; OpenRouter anahtarları operatörde
  # olduğu için burada ZORLANMAZ, beyanla ertelenebilir).
  printf '  %s için YENİ değer (boş = .env icindeki mevcut degeri tasi): ' "$ad" >&2
  read -s -r _girilen || true
  echo >&2
  if [ -n "${_girilen:-}" ]; then
    printf '%s\n' "$_girilen" > "$tmp"
    unset _girilen
  else
    _deger_dosyala "$ENVF" "$ad" "$tmp" env
  fi
  # BOŞ DEĞER KAPISI. `[ -s "$tmp" ]` YETMEZ: 2026-09-07'de dosya 1 baytlık bir satır sonuydu ve
  # kapı GEÇTİ; o "değer" hem 0400 credential kaynağına hem `.env` satırına yazıldı ve iki sır da
  # iki kanaldan birden düştü. Hüküm boşluk DIŞI en az bir karakterdir. Bu satıra kadar HİÇBİR
  # yazım yapılmamıştır — reddedilen geçiş hiçbir iz bırakmaz (sıfır ile "bilmiyorum" aynı değil).
  _dolu_mu "$tmp" || die "$ad için DEĞER YOK — istem boş geçildi ve $ENVF içinde ^${ad}= satırı
     yok/boş (ya da girilen değer yalnız boşluktan ibaret). HİÇBİR dosya değiştirilmedi."

  # 1) CREDENTIAL KAYNAĞI — root:root 0400. Servis kullanıcısının okuması GEREKMEZ: dosyayı systemd
  #    PID 1 olarak, sandbox'tan ÖNCE okur. En dar izin, işi gören izindir.
  sudo install -d -m 0755 "$ETC"
  sudo install -m 0400 "$tmp" "$kred"
  sudo chown root:root "$kred" 2>/dev/null || true
  oldu "credential kaynağı yazıldı: $kred (0400 root:root)"

  # 2) ORTAM KANALI DA AYNI DEĞERE ÇEKİLİR. Faz 1'de iki kanal birden canlıdır; ayrı değer
  #    taşırlarsa hangisinin yürürlükte olduğu ölçüme değil ŞANSA kalır — ve faz 2'nin farksal
  #    ölçümü anlamını yitirir. İkisi eşitken geçiş her iki uygulama sürümünde de çalışır.
  _env_yedekle "$ad"
  _env_satiri_yaz "$ad" "$tmp"
  oldu "ortam kanalı aynı değere çekildi: $ENVF (0600)"
  rm -f "$tmp"; trap - EXIT

  # 3) DROP-IN — YALNIZ İKİ KAYNAK DA HAZIRKEN. `LoadCredential=` kaynağı yoksa birim HİÇ başlamaz;
  #    tek ad için kurmak, öteki kaynak üretilene kadar motoru açılmaz hâle getirirdi.
  # `test -s` DEĞİL `_dolu_mu`: 1 baytlık satır sonu taşıyan bir kaynak `test -s`i GEÇER, ama
  # `LoadCredential` onu BOŞ okutur — "iki kanal da canlı" yeşili basılır, oysa o ad credential
  # kanalından değersiz gelir ve arıza ancak faz-2 ortam satırını sildiğinde ortaya çıkar.
  eksik=""
  for a in $ADLAR; do
    _dolu_mu "$(_kaynak_yolu "$a")" || eksik="$eksik $a"
  done
  if [ -n "$eksik" ]; then
    echo "  · drop-in KURULMADI — kaynak dosyası eksik:$eksik"
    echo "    (LoadCredential kaynağı yoksa birim HİÇ açılmaz. Öteki ad için de --faz1 koş.)"
    return 0
  fi
  sudo install -d -m 0755 "$BIRIM"
  sudo cp "$KAYNAK_DIR/$DROPIN_AD" "$BIRIM/$DROPIN_AD"
  sudo systemctl daemon-reload
  sudo systemctl restart meridian
  if ! _servis_ayakta; then
    echo "!! servis AÇILMADI — GERİ ALINIYOR"
    sudo rm -f "$BIRIM/$DROPIN_AD"
    sudo systemctl daemon-reload; sudo systemctl restart meridian
    die "faz 1 başarısız (drop-in kaldırıldı, eski hâle dönüldü). Günlük: journalctl -u meridian -n 50"
  fi
  oldu "drop-in kuruldu · servis ayakta · iki kanal da canlı (credential ÖNCE okunur)"
  echo ">> Faz 2'ye geçmeden önce: ./sir_credential_gecis.sh --faz2 $ad (farksal ölçüm yapar)"
}

# =================================================================================================
faz2() {
  local ad="$1" kred sahte kanit neg taban
  _ad_dogrula "$ad"
  kred="$(_kaynak_yolu "$ad")"
  echo "=== FAZ 2: $ad ortam satırını kapat ==="
  [ -f "$BIRIM/$DROPIN_AD" ] || die "faz 1 kurulu değil — önce --faz1 $ad"
  # HER ŞEYDEN ÖNCE: yarıda kalmış bir tur var mı? Varsa `$kred` ölçümün SAHTE değerini taşıyor
  # olabilir ve aşağıdaki `_dolu_mu` onu memnuniyetle "dolu" sayar — gerçek hakkındaki tek bilgi
  # `.olcum-yedek`lerdedir.
  _olcum_kalintisi_kapisi
  _dolu_mu "$kred" || die "credential kaynağı BOŞ/yok: $kred
     ('test -s' YETMEZ — 2026-09-07'de dosya 1 baytlık bir satır sonuydu ve kapı geçti.) Faz-2 bu
     hâlde ortam satırını silerse sır HİÇBİR kanaldan okunamaz. Değişiklik YAPILMADI."
  [ "$ad" != "KAPI_APIKEY" ] || _kapi_kilidi_olc

  # ---- ÖLÇÜMÜN ÖLÇÜMÜ (NEGATİF KONTROL) ---------------------------------------------------------
  # Aşağıdaki farksal ölçümün mantığı "sahte ortam + gerçek credential → hâlâ OK ⇒ okunan kanal
  # credential'dır". Bu çıkarım YALNIZ OK anahtara BAĞLIYSA geçerlidir; uç her koşulda OK diyorsa
  # ölçüm hangi kanalın okunduğu hakkında HİÇBİR ŞEY söylemez. 2026-09-07'de credential dosyası
  # BOŞKEN faz-2 "geçti" — kanıtın kendisi hiç sınanmamıştı. Önce İKİ kanalı da sahteye çekip
  # kanıtın YOK dediğini görüyoruz; demezse ölçüm YAPILAMAMIŞTIR ve ölçülemeyen şeye "geçti"
  # demek uydurmadır (uydurma yasağı). Bedel: bir ek restart + bir ek doğrulama turu.
  #
  # POZİTİF TABAN — NEGATİF KONTROLÜN ÖLÇÜMÜ. Negatif kontrol "iki kanal da sahteyken kanıt YOK
  # demeli" der; ama uç ZATEN YOK diyorsa (pano token'ı bozuk, servis yarım, uç 500) o YOK
  # anahtar hakkında HİÇBİR ŞEY söylemez — ve ardından gelen farksal ölçüm de YOK döner, betik
  # "faz-2 erken, sürümü dağıt" diye YANLIŞ teşhis basar. Taban hiçbir şeye DOKUNMADAN ölçülür.
  taban="$(_kanit_nous)"
  [ "$taban" = "OK" ] || die "ÖLÇÜLEMEDİ: kanıt ucu BAŞLANGIÇTA OK demiyor ($taban) — yani daha
     hiçbir şeye dokunmadan kanıt YOK. Bu hâlde negatif kontrolün 'YOK'u da farksal ölçümün
     'YOK'u da anahtar hakkında hiçbir şey söylemez. Önce sebebi bul (pano token'ı: $DASH_KRED ·
     uç: $API/api/secrets/test/nous · servis: systemctl status meridian), sonra --faz2.
     Değişiklik YAPILMADI."
  oldu "pozitif taban: kanıt ucu koşum ÖNCESİNDE OK — negatif kontrolün YOK'u anlamlı olacak"

  sudo cp -p "$ENVF" "$ENVF.olcum-yedek"
  sudo cp -p "$kred" "$kred.olcum-yedek"
  # TRAP ÖLÇÜM PENCERESİNİN TAMAMINI KAPSAR. Buradan sonraki HER çıkış (die dahil) sahte
  # değerleri geri alır: pencere içinde `.env` ve/veya credential kaynağı SAHTEDİR ve yarım
  # bırakılan bir ölçüm motoru sahte anahtarla çalışır durumda bırakırdı.
  # shellcheck disable=SC2064
  trap "_olcum_kurtar '$kred'" EXIT
  sahte="$(mktemp)"; chmod 600 "$sahte"
  printf 'sahte-%s\n' "$(openssl rand -hex 8)" > "$sahte"
  # OKUYUCUSU OPERATÖRDÜR (Yasa 6): trap SIGKILL'i yakalayamaz. Süreç öldürülürse iki kanal da
  # sahte kalır ve kurtarma tek `mv`dir — o iki yolun journal'da yazılı olması gerekir.
  echo "  · ölçüm yedekleri alındı — süreç SIGKILL ile ölürse GERÇEK değerin tek kopyası bunlar:"
  echo "      sudo mv -f \"$ENVF.olcum-yedek\" \"$ENVF\""
  echo "      sudo mv -f \"$kred.olcum-yedek\" \"$kred\""
  echo "      sudo systemctl restart meridian"
  echo "    (bu dosyalar dururken --faz2/--geri-al hiçbir şey yapmaz ve çıkış 2 verir.)"
  echo "  · negatif kontrol: İKİ kanal da sahte — kanıt YOK demeli"
  _env_satiri_yaz "$ad" "$sahte"
  sudo install -m 0400 "$sahte" "$kred"
  # sessiz-yutma: chown yalnız root olarak anlamlıdır ve sahiplik zaten bir sonraki satırdaki restart + kanıt turunda dolaylı ölçülür; testteki sahte kökte root yoktur
  sudo chown root:root "$kred" 2>/dev/null || true
  sudo systemctl restart meridian
  _servis_ayakta || die "negatif kontrol sırasında servis açılmadı"
  neg="$(_kanit_nous)"
  if [ "$neg" = "OK" ]; then
    rm -f "$sahte"
    # Geri alma TRAP'in işidir (tek-kaynak): burada ikinci bir `mv` çifti yazmak, iki kurtarma
    # yolunun sessizce ayrışmasına açık kapı bırakırdı.
    die "ÖLÇÜLEMEDİ: kanıt ANAHTARA BAĞLI DEĞİL — İKİ kanal da SAHTEYKEN /api/secrets/test/nous
     yine OK dedi. Bu hâlde farksal ölçüm bir tiyatrodur ve hangi kanalın okunduğunu KANITLAMAZ.
     Önce kanıt ucu onarılır (hermes.ping_brain gerçekten anahtarla konuşmalı), sonra --faz2.
     Değişiklik YAPILMADI (iki kanal da eski değerine döndürüldü)."
  fi
  oldu "negatif kontrol: sahte anahtarla kanıt YOK — ölçüm ANAHTARA bağlı"

  # ---- FARKSAL ÖLÇÜM: uygulama sırrı HANGİ kanaldan okuyor? --------------------------------------
  # İki kanal aynı değeri taşırken "motor çalışıyor" HİÇBİR ŞEY kanıtlamaz — ortam kanalı okunuyor
  # olsa da aynı sonuç gelirdi. Tek dürüst ölçüm FARK yaratmaktır: ortam satırında SAHTE değer
  # KALIR, gerçek değer YALNIZ credential'a geri konur. Motor hâlâ iş yapıyorsa okunan kanal
  # credential'dır. Ölçüm KENDİ ARDINI TOPLAR: sahte değer her yolda geri alınır (trap).
  # Trap DEĞİŞMEZ: `_olcum_kurtar` artık olmayan `$kred.olcum-yedek`i atlar, `.env`i geri alır.
  # (Tek geri alma yolu = tek kaynak; ikinci bir trap dizgesi ilkinden sessizce ayrışırdı.)
  sudo mv -f "$kred.olcum-yedek" "$kred"
  rm -f "$sahte"
  echo "  · farksal ölçüm: ortam satırı SAHTE, credential GERÇEK"
  sudo systemctl restart meridian
  _servis_ayakta || die "ölçüm sırasında servis açılmadı"
  kanit="$(_kanit_nous)"
  sudo mv -f "$ENVF.olcum-yedek" "$ENVF"; trap - EXIT
  sudo systemctl restart meridian; _servis_ayakta || die "ölçüm sonrası servis açılmadı"

  [ "$kanit" = "OK" ] || die "UYGULAMA HÂLÂ ORTAM KANALINI OKUYOR (sahte ortam + gerçek credential → $kanit).
     Faz 2 ERKEN: motorun credential kanalını okuduğu (secrets._fetch sırası) sürümü dağıtılmış
     olmalı. Değişiklik YAPILMADI."
  oldu "farksal ölçüm: motor credential kanalını okuyor (sahte ortam satırıyla da iş yapıyor)"

  # SON KAPI — ortam satırı silinmeden ÖNCE credential kaynağı YENİDEN ölçülür. Ölçüm turu kaynağı
  # iki kez yerinden oynattı (`install` + `mv`); yarıda kalan bir tur BOŞ bir kaynak bırakabilirdi
  # ve tek kanal kapanınca sır hiçbir yerden okunamazdı.
  _dolu_mu "$kred" || die "credential kaynağı ölçüm turundan BOŞ çıktı: $kred
     Ortam satırı SİLİNMEDİ. Önce --faz1 $ad ile kaynak yeniden yazılır."

  _env_yedekle "faz2-$ad"
  _env_satiri_sil "$ad"
  sudo systemctl restart meridian
  if ! _servis_ayakta || [ "$(_kanit_nous)" != "OK" ]; then
    echo "!! faz 2 doğrulanamadı — GERİ ALINIYOR"
    geri_al "$ad"
    die "faz 2 başarısız (ortam satırı geri yazıldı). Günlük: journalctl -u meridian -n 50"
  fi
  oldu "$ad ortam kanalından ÇIKTI — artık yalnız credential'dan okunuyor"
  echo ">> Doğrula: sudo tr '\\0' '\\n' < /proc/\$(pgrep -f 'uvicorn meridian.api' | head -1)/environ | grep -c $ad   # 0 beklenir"
}

# =================================================================================================
# FAZ-1A — MOTOR AYAĞI. Yalnız drop-in kurar: kaynak dosyayı (`/etc/hindsight/creds/*`) hindsight
# tarafının geçişi üretir ve bu betik onu ÜRETMEZ — üretseydi aynı sır iki yerden doğar ve hangi
# kopyanın rotate edildiği ŞANSA kalırdı (tek-kaynak yasası).
faz1_hafiza() {
  echo "=== FAZ 1A: pano vekili → $HAFIZA_DROPIN_AD (dosya kanalı KALIR) ==="
  # AYNI KAPI: bu alt komut motoru RESTART eder. Yarıda kalmış bir ölçüm turunda restart, iki
  # kanalı da SAHTE olan motoru "ayakta" gösterir ve kurtarma penceresini sessizce uzatır.
  _olcum_kalintisi_kapisi
  _systemd_kapisi
  [ -d "$KAYNAK_DIR" ] || die "drop-in kaynağı yok: $KAYNAK_DIR (depo güncel mi?)"
  [ -f "$KAYNAK_DIR/$HAFIZA_DROPIN_AD" ] || die "drop-in dosyası yok: $KAYNAK_DIR/$HAFIZA_DROPIN_AD"

  # KAPI, DEĞİŞİKLİKTEN ÖNCE. `LoadCredential=` kaynağı yoksa systemd birimi HİÇ BAŞLATMAZ — yani
  # bu tek satır MOTORU kapatır. Aşağıdaki restart'ın geri alımı var, ama hiç girmemek daha ucuz:
  # hindsight tarafı kurulmadan motora bir hindsight sırrı bağlanmaz.
  _dolu_mu "$HAFIZA_KRED" || die "credential kaynağı YOK/BOŞ: $HAFIZA_KRED
     Bu satır kurulursa MOTOR HİÇ AÇILMAZ (LoadCredential kaynağı zorunludur). Önce hindsight
     tarafı: /etc/hindsight/creds/* (0400 root) + hindsight-api.service.d/50-creds.conf.
     Değişiklik YAPILMADI."

  sudo install -d -m 0755 "$BIRIM"
  sudo cp "$KAYNAK_DIR/$HAFIZA_DROPIN_AD" "$BIRIM/$HAFIZA_DROPIN_AD"
  sudo systemctl daemon-reload
  sudo systemctl restart meridian
  if ! _servis_ayakta; then
    echo "!! servis AÇILMADI — GERİ ALINIYOR"
    sudo rm -f "$BIRIM/$HAFIZA_DROPIN_AD"
    sudo systemctl daemon-reload; sudo systemctl restart meridian
    die "faz 1A başarısız (drop-in kaldırıldı, eski hâle dönüldü). Günlük: journalctl -u meridian -n 50"
  fi
  oldu "drop-in kuruldu · servis ayakta · vekil TENANT anahtarını credential kanalından okuyor"
  echo ">> Doğrula (pano): /api/hindsight gövdesinde bankalar DOLU, neden BOŞ olmalı."
  echo ">> Farksal ölçüm hindsight tarafındadır: /opt/hindsight/.env satırına SAHTE değer konup"
  echo "   pano hâlâ banka listeliyorsa okunan kanal credential'dır."
}

geri_al_hafiza() {
  echo "=== GERİ ALMA (Faz-1A): $HAFIZA_DROPIN_AD kaldırılıyor ==="
  # 53'e DOKUNULMAZ: iki drop-in ayrı yaşar ve motorun KENDİ sırlarının geçişi bu geri alımdan
  # etkilenmez. Vekil, dosya bacağına (`/opt/hindsight/.env`) düşer — kod iki kanalı da okur.
  sudo rm -f "$BIRIM/$HAFIZA_DROPIN_AD"
  sudo rmdir "$BIRIM" 2>/dev/null || true
  sudo systemctl daemon-reload
  sudo systemctl restart meridian
  _servis_ayakta || die "servis açılmadı — journalctl -u meridian -n 50"
  oldu "drop-in kaldırıldı, servis ayakta (vekil /opt/hindsight/.env bacağını kullanıyor)"
  echo "  · $HAFIZA_KRED SİLİNMEDİ (bilinçli: geri almanın kendisi geri alınabilir kalsın)."
}

# =================================================================================================
geri_al() {
  local ad="$1" kred tmp a sayi=0 yazilan="" yerinde="" ad_tamam=0
  _ad_dogrula "$ad"
  echo "=== GERİ ALMA: $ad ortam kanalına dön ==="

  # KESİNTİ SONRASI REFLEKS KOMUT BUDUR. Yarıda kalmış bir ölçüm turunda `.env` ve credential
  # kaynağı ölçümün SAHTE değerini taşır; aşağıdaki geri yazma o sahte değeri "gerçek" diye
  # `.env`e yazar ve ✓ raporlardı. Kurtarma kopyaları dururken tek doğru davranış durmaktır.
  _olcum_kalintisi_kapisi

  # GERİ ALMA DA `.env`E YAZAN BİR YOLDUR. Tur-1'de yedeksiz tek yazım yolu buydu: yanlış giden
  # bir geri alma sonrası dönülecek nokta yoktu (faz-1 ve faz-2 kendi yedeklerini alıyor).
  _env_yedekle "gerial-$ad"

  # 1) ORTAM SATIRLARI GERİ YAZILIR — YALNIZ `$ad` İÇİN DEĞİL, DROP-IN'İN TAŞIDIĞI HER AD İÇİN.
  #    Drop-in TEK dosyada iki `LoadCredential=` satırı taşır, yani aşağıdaki `rm` credential
  #    kanalını HER İKİ sır için kapatır. Faz-2'yi geçmiş ÖTEKİ adın `.env` satırı ise zaten
  #    silinmiştir: eski dar geri alma `--geri-al NOUS_API_KEY` ile KAPI_APIKEY'i her iki kanaldan
  #    birden düşürürdü ve `_servis_ayakta` (kimlik doğrulaması İSTEMEYEN /healthz) bunu göremezdi
  #    — geri alma DROP-IN kadar GENİŞ olmalı. Değer credential kaynağından okunur, terminale HİÇ
  #    uğramaz; kaynağı olmayan ad için satır UYDURULMAZ (boş bir `<ad>=` satırı "ayarlı ama
  #    değersiz" yalanı olurdu — uydurma yasağı). `_env_satiri_yaz` satırı ÇOĞALTMAZ, değiştirir.
  #    ÖTEKİ ADIN YERİNDE DURAN SATIRI EZİLMEZ. Credential kaynağı bir ROTASYONDAN sonra BAYAT
  #    olabilir (rotasyon credential'a yazılıp `.env` elle güncellendiyse ya da tersi); `$ad`
  #    için istenen geri alma, öteki adın taze ortam satırını bayat bir değerle sessizce
  #    değiştirmeyi KAPSAMAZ — ve kayıp sessizdir, çünkü `/healthz` kimlik doğrulamaz. Satır
  #    yerinde ve DEĞERLİYSE dokunulmaz; yazım yalnız satırı OLMAYAN (faz-2'yi geçmiş) ad için.
  for a in $ADLAR; do
    kred="$(_kaynak_yolu "$a")"
    if [ "$a" != "$ad" ] && _env_satiri_dolu_mu "$a"; then
      yerinde="$yerinde $a"
      echo "  · $a: ortam satırı zaten yerinde — DOKUNULMADI (bayat credential değeriyle ezilmez)"
      continue
    fi
    if ! _dolu_mu "$kred"; then
      echo "  · $a: credential kaynağı yok/boş ($kred) — ortam satırı geri YAZILAMADI (yedek: $YEDEK_DIR/.env.bak-*)"
      continue
    fi
    tmp="$(mktemp)"; chmod 600 "$tmp"
    _deger_dosyala "$kred" "$a" "$tmp" kred
    if _dolu_mu "$tmp"; then
      _env_satiri_yaz "$a" "$tmp"
      sayi=$((sayi + 1)); yazilan="$yazilan $a"
      [ "$a" != "$ad" ] || ad_tamam=1
      oldu "$ENVF içine $a satırı geri yazıldı (değer credential kaynağından; basılmadı)"
    else
      echo "  · $a: $kred okunamadı — ortam satırı geri YAZILAMADI"
    fi
    rm -f "$tmp"
  done
  echo "  · geri yazılan ad sayısı: $sayi —${yazilan:- (yok)}"
  [ -z "$yerinde" ] || echo "  · satır yerinde (dokunulmadı):$yerinde"

  # ORTAM KANALI ZATEN AYAKTAYSA GERİ ALMA ZATEN OLMUŞTUR. Hüküm "sır ortam kanalından
  # OKUNABİLSİN"dir — "bu koşumda YAZILMIŞ olsun" değil. `$ad`ın satırı YERİNDE ve DEĞERLİYSE
  # (faz-2 hiç koşmadı, ya da operatör yedekten elle yükledi) credential kanalını kapatmak sırrı
  # düşürmez. Bunu saymayan lafzi kapı aracı KENDİ VARLIK SEBEBİ olan hâlde kilitliyordu:
  # kaynaklar 1 baytken (olayın bıraktığı hâl) die "yedekten ^${ad}= satırını .env'e kopyala,
  # sonra tekrarla" diyor — satır ZATEN orada, operatör dediğini yapıyor, AYNI die geliyor; tek
  # çıkış betiği atlayıp drop-in'i elle silmekti ve betik bunu söylemiyordu (ölçüldü 2026-09-08).
  # DEĞER yarısı burada da zorunlu: `<ad>=` (değersiz) satır "ayarlı" DEĞİLDİR (`_env_satiri_dolu_mu`).
  if [ "$ad_tamam" != "1" ] && _env_satiri_dolu_mu "$ad"; then
    ad_tamam=1
    echo "  · $ad: satır yerinde (ortam kanalı) — geri yazmaya gerek yok, drop-in kaldırılabilir"
  fi

  # DROP-IN ANCAK `$ad` ORTAM KANALINDAN OKUNABİLİYORSA KALDIRILIR. Kaldırmak credential kanalını
  # kapatmaktır; `$ad`ın ortam satırı YOKSA/DEĞERSİZSE sır HİÇBİR kanaldan okunamaz ve
  # `_servis_ayakta` (kimlik doğrulaması İSTEMEYEN /healthz) bunu göremez — tur-1'de bu yol ✓ +
  # RC 0 dönüyordu. Değeri uydurmak da yasak; geriye tek dürüst seçenek durmaktır. Reçete artık
  # NO-OP DEĞİLDİR: buraya ancak satır gerçekten yok/değersizken gelinir.
  [ "$ad_tamam" = "1" ] || die "$ad ortam satırı YOK/DEĞERSİZ ve geri YAZILAMADI (credential
     kaynağı boş/yok: $(_kaynak_yolu "$ad")). Drop-in KALDIRILMADI — kaldırılsaydı $ad hiçbir
     kanaldan okunamaz, motor sessizce anahtarsız çalışırdı. Değeri elle geri yükle:
     $YEDEK_DIR/.env.bak-* (en yenisi) içindeki ^${ad}= satırını $ENVF içine kopyala, sonra bu
     komutu tekrarla — satır DEĞERLİ hâle gelince bu die gelmez, betik drop-in'i kaldırır."

  # 2) DROP-IN KALDIRILIR. Drop-in İKİ adı birden taşır (tek dosya) — yani bu adım credential
  #    kanalını HER İKİ sır için kapatır. Bilerek: yarım kurulu bir birim (bir kaynağı olan, öteki
  #    olmayan) hiç açılmazdı; geri almanın da bütün olması gerekir.
  sudo rm -f "$BIRIM/$DROPIN_AD"
  # sessiz-yutma: dizin boş değilse (54 drop-in'i duruyorsa) rmdir başarısız olur ve bu DOĞRU davranıştır — kaldırılması gereken tek dosya bir üstteki satırda kaldırıldı
  sudo rmdir "$BIRIM" 2>/dev/null || true
  sudo systemctl daemon-reload
  sudo systemctl restart meridian
  if _servis_ayakta; then
    oldu "drop-in kaldırıldı, servis ayakta ($ENVF yürürlükte)"
  else
    die "servis açılmadı — journalctl -u meridian -n 50"
  fi
  echo "  · credential kaynakları SİLİNMEDİ (bilinçli: geri almanın kendisi geri alınabilir kalsın)."
}

# =================================================================================================
case "${1:-}" in
  --faz1)    [ $# -ge 2 ] || die "kullanım: --faz1 <ad> — tanınanlar: $ADLAR"; faz1 "$2" ;;
  --faz2)    [ $# -ge 2 ] || die "kullanım: --faz2 <ad> — tanınanlar: $ADLAR"; faz2 "$2" ;;
  --geri-al) [ $# -ge 2 ] || die "kullanım: --geri-al <ad> — tanınanlar: $ADLAR"; geri_al "$2" ;;
  --faz1-hafiza)    faz1_hafiza ;;
  --geri-al-hafiza) geri_al_hafiza ;;
  "")        durum ;;
  *)         die "bilinmeyen argüman: $1 (--faz1 <ad> | --faz2 <ad> | --geri-al <ad> | --faz1-hafiza | --geri-al-hafiza | boş=durum)" ;;
esac
