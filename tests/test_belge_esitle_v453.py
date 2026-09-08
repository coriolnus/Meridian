"""v453 — TSK-177: `ops/belge_esitle.sh`, belgelerin dağıtımdan BAĞIMSIZ canlıya gitme yolu.

NUMARA KİMLİKTİR ve ÖLÇÜLDÜ (2026-09-08, bu worktree'de
`ls tests | grep -oE 'v[0-9]+' | sort -t v -k2 -n | tail -1`): en büyük kullanılan `vNNN` `v452`
(`test_ansible_dagit_v452.py`) — `v453` boştur, çakışma YOK.

NE ÇİVİLENİR. Betiğin taşıdığı iddia tek cümlede şudur: *"belgeleri canlıya taşırım; kod
taşımam, hiçbir şeyi durdurmam, ve taşıdığımı ÖLÇERİM."* Bu üç parçanın her biri ayrı ayrı
sessizce bozulabilir, o yüzden her biri ayrı çivi taşır:

  [A] KAPSAM   — küme dizisi kilitli, yasak sınıf (`.py`/`.sh`/motor dizinleri/`*.env*`) kapıda
                 ölçülüyor. Bir gün biri kümeye `ops` eklerse bu yol sessizce ikinci bir dağıtım
                 kanalına dönerdi (worker durdurmadan, suite hükmü olmadan, kapısız).
  [B] KAPILAR  — [0a] kirli ağaç · [0b] push'lanmamış HEAD (+ `fetch` düşerse FAIL-CLOSED) ·
                 [0c] izlenmeyen dosya RAPOR edilir (tur-3: kapı DEĞİL — aşağıya bak). Her biri
                 POZİTİF+NEGATİF çift: yalnız "DURDU" tarafı çivilenseydi, HER ZAMAN duran bir
                 betik de yeşil kalırdı.
  [C] ÖLÇÜM    — `--kuru` HİÇBİR bayt yazmaz · `--delete` yalnız dizinlerde ve ön-tarama
                 ZORUNLU · beyan beş alanlı, tek satır, atomik ve geri okunuyor · sha ayrışınca
                 çıkış 2 · token yokken "ölçülemedi" deyip DURMUYOR · sır hiçbir akışta —
                 A1'deki `curl` argv'si DAHİL — görünmüyor.
  [E] SİLME     — GERÇEK `rsync` ile, davranış düzeyinde: `--delete` kapsamdan TAŞMIYOR (tur-2
                 bloker'ı), kapsam kapısı taşkında DURDURUYOR, rsync sıfır-dışı çıkışta iz
                 KORUNUYOR. Argüman düzeyi (C2) ile davranış düzeyi (E1) AYRI iddialardır:
                 tur-1'de argüman çivileri 28/28 yeşilken canlı silme 10 dosyaya yayılıyordu.

A1'E HİÇBİR BAĞLANTI YOK — VE BU BİR SÖZ DEĞİL, BİR KİLİT. Dört sahte komut (`ssh`, `rsync`,
`curl`, `sha256sum`) PATH'in BAŞINA konur; ayrıca `git` de sarmalanır ve GERÇEK depo ağacında
(`/Users/.../AI-Trading` ve altındaki worktree'ler) çalıştırılmaya kalkarsa rc=113 ile ÖTER.
Sebebi ölçülmüş bir kaza sınıfıdır (v349'un `_sistemik_ssh_kilidi` kaydı): bir test `--kok`
vermeyi UNUTURSA betik varsayılan köke (`$HOME/AI-Trading`) düşer ve orada `fetch` koşardı —
yani bir ajan testi, ana checkout'un ref'lerini yazardı. Tekil testleri yamamak yetmez; kilit
AUTOUSE'dur, unutulan bir `--kok` artık sessizce geçemez.

`monkeypatch.undo()` HİÇBİR YERDE ÇAĞRILMAZ (CLAUDE.md §2: autouse fikstürleri de geri alırdı).

MUTASYONLA ÖLÇÜLDÜ (2026-09-08) — çivi yeşili kanıt değildir. 14 mutasyon uygulandı, 14'ü de
hedeflediği çiviyi KIRMIZI yaptı (tablo tur raporunda). İlk turda 11'den BİRİ yeşil kaldı ve o
körlük bu dosyayı DEĞİŞTİRDİ:

  * M11 — beyanın GERİ OKUNMASINI silen mutasyon hiçbir çiviyi kırmadı. Sebebi ölçüldü: hem C3
    hem C8, `echo`nun bastığı "bayt-özdeş doğrulandı" cümlesine bakıyordu; cümle kıyas
    koşmasa da basılmaya devam ediyordu. Operatöre BASILAN metin, o ölçümün yapıldığının
    kanıtı DEĞİLDİR (aynı sınıf: "yorum tarihçe, kod hüküm"). İki çivi eklendi — C8b
    (`SIM_BEYAN_BOZ`: yazım başarılı görünür, içerik AYRIDIR → kıyas koşmuyorsa sessizce
    "tamam" olurdu) ve C3'ün geri-okuma ÇAĞRI SAYIMI.
  * D2b — 27 çivinin hepsi `--kok` veriyordu, yani `KOK="$HOME/AI-Trading"` satırı hiç
    KOŞMUYORDU: oradaki bir yazım hatası suite yeşilken operatörün ilk koşumunda patlardı
    (CLAUDE.md §6, 2026-08-30 vakası). Bayraksız biçim artık uçtan uca koşuluyor (M14 ısırır).

A1'E TEK BİR PAKET GİTMEDİ. İKİ SAHNE VARDIR ve ikisi de ağsızdır: [A]-[D] şimli sahne
(rsync/ssh/curl/sha256sum taklit edilir, argüman ve akış sözleşmeleri orada ölçülür) · [E]
ŞİMSİZ sahne (GERÇEK `rsync`, ŞEFFAF `ssh` — konak adı atılır, uzak komut yerelde koşar; silme
SEMANTİĞİ ancak orada ölçülebilir). Tur-1'in bloker'ı tam olarak ilk sahnenin kör noktasındaydı:
rsync şimi `*deleting` satırlarını KENDİ ürettiği için `--delete`in kapsamdan taşması o sahnede
doğamıyordu (tur-2, 2026-09-08).

TUR-2 MUTASYONLARI (10 mutasyon; tablo tur raporunda): `--relative` biçimine tam dönüş E1'i,
`--no-implied-dirs`in kalkması C2'yi, kapsam kapısının susturulması ve `..` ayağının kalkması
E3'ü, ön-taramanın atlanması C2+E3'ü, rapor ön ekinin kalkması C9+E1'i, rsync çıkış kodunun
yutulması ve izin koşulsuz silinmesi E4'ü, token'ın uzak `curl` argv'sine dönmesi C11'i KIRDI.

TUR-3 — DÖRT YENİ İDDİA, YENİ BİR BÖLÜM ([F]) VE BİR KAPININ EMEKLİLİĞİ:

  * AKTARIM LİSTESİ ARTIK GİT'TEN TÜRER (`git ls-files -z` → `--files-from`/`--from0`). Tur-2'nin
    "[0c] izlenmeyen dosya varsa DUR" kapısı ana checkout'ta operatörün İLK kuru koşumunu
    durduruyordu (ölçüldü: `docs/mutasyon/.*.ham.log`, `.gitignore`lu). Koruma kapıdan YAPIYA
    taşındı: yok sayılan dosya listede yoktur, rsync onu hiç görmez. [0c] artık RAPOR (B4) ve
    davranış ayağı F1'dedir — GERÇEK rsync ile, çünkü şim sahnesinde `--files-from`in kalkması
    görünmezdi (şim listeyi okumasaydı tautoloji olurdu; şim artık listeye UYAR).
  * İKİ FAZ, ve nedeni ÖLÇÜLDÜ: `--files-from` + `--delete` openrsync'te HİÇBİR ŞEY silmez.
    Tek çağrıda birleştirmek hayalet temizliğini "yeşil görünüp hiç koşmaz" hâline sokardı
    (mutasyon P6 → E1+C2 kırmızı). Silme artık ayrı bir SALT-SİLME geçişidir.
  * SEMBOLİK BAĞ: `--no-links` + `[0d]` "atlandı: N bağ" raporu (F2). Tur-2'de bir bağ DÖRT
    kapının hepsini geçip canlıya gidiyordu.
  * SİLME TAVANI: `--max-delete=N` (izli yolun %10'u, en az 5) + rsync 25 → DURDU (F3). Ölçüldü:
    tavan ÖN-TARAMADA da 25 verir, yani hiçbir şey silinmeden durulur.
  * KAPSAM KAPISININ "MUTLAK YOL" AYAĞI KALDIRILDI. Ölü olduğu mutasyonla kanıtlanmıştı; asıl
    hata ayakta değil, rapor ön ekindeydi (`docs//etc/passwd` kapsam önekiyle BAŞLIYORDU). Ön ek
    artık mutlak yola eklenmez ve mutlak yol ilk ayağa takılır (F4).

TUR-3 MUTASYONLARI — 12 mutasyon, 12'si de ISIRDI, kör nokta YOK (tablo tur raporunda): aktarım
listesinin kalkması F1+C2'yi, `--no-links`in kalkması F2+C2'yi, tavanın kalkması F3+C2'yi, ön ek
hatasının geri gelmesi F4'ü, salt-silme geçişinin ikinci bir aktarıma dönmesi F1+C2'yi, iki fazın
birleşmesi E1+C2'yi, disk≠git raporunun susması B4'ü, bağ raporunun susması F2'yi, `..` ayağının
kalkması E3'ü, `[0d]`nin listeyi gezmemesi A2'yi, liste fail-closed dalının kalkması B6'yı, kök
DOSYA kapısının kalkması B7'yi KIRDI.

VE YİNE BİR MUTASYON TASARIMI DEĞİŞTİRDİ (tur-1'in M11'i, tur-3'ün P11'i — aynı sınıf). İlk
koşumda P11 YEŞİL kaldı: liste alınamadığında DURDURAN hata dalı İKİ KEZ yazılmıştı (dizin ve
kök-dosya girdileri için ayrı ayrı) ve mutasyon yalnız birini kaldırınca çivi ÖTEKİ kopya
sayesinde yeşil kalıyordu. Aynı gerçeğin iki kopyası yalnız sessizce AYRIŞMAKLA kalmaz, birbirini
ÖRTEREK bir çiviyi de kör eder. Hata dalı TEKE indirildi (`_liste_rc`), P11 ısırdı.

TUR-4 — [00] RSYNC İKİLİSİ SEÇİMİ (CANLI BULGU, Rol-1 2026-09-08). macOS `/usr/bin/rsync`
openrsync'tir (protokol 29); A1 GNU rsync 3.2.7 ile `--from0 --files-from` protokol UYUMSUZDUR
(A1'de `ABORTING due to invalid path from sender` + `protocol incompatibility (code 2)` — betik
DOĞRU durdu, fail-closed, ama sebep bir lehçe farkıydı). Yeni bir gate: seçim sırası `RSYNC_BIN` →
`/opt/homebrew/bin/rsync` (varsa) → `command -v rsync`; seçilen ikili openrsync ise KURU koşumda
DAHİ durur. `sahne` fikstürü artık `RSYNC_BIN`i varsayılan olarak `kutu/rsync` şimine SABİTLER —
yoksa bu geliştirme makinesindeki GERÇEK `/opt/homebrew/bin/rsync` (GNU 3.5.0, kurulu) [00]'ın
2. ayağından sessizce seçilir ve ONLARCA şim tabanlı çivi körleşirdi (`_iz(sahne, "rsync")` hep
boş kalırdı — ölçülmeden önce bu tuzağa bizzat düşüldü, düzeltildi). `sahne_gercek_rsync` bunu
POP eder — [G3]'ün asıl ölçtüğü şey budur. [G] üç çivi: G1 (RSYNC_BIN seçiliyor mu), G2 (openrsync
reddi + sıfır transfer), G3 (gerçek sahne GNU seçiyor ve basıyor).
"""

from __future__ import annotations

import json
import os
import pathlib
import re
import shlex
import shutil
import subprocess

import pytest

REPO = pathlib.Path(__file__).resolve().parent.parent
BETIK = REPO / "ops" / "belge_esitle.sh"

#: Kilidin öttüğünü testin GÖREBİLMESİ için işaret — sessizce rc=0 taklit etmek, kaçağı
#: "başarı" diye yutmak olurdu (v349'un aynı dersi).
GIT_KILIT_ISARET = "@@GERCEK-DEPO-GIT-YAKALANDI@@"

#: Sahte deponun belge kümesi — betiğin dört kökünün hepsini temsil eder (iki kök dosya,
#: iki dizin; dizinlerden biri ALT DİZİN taşır ki `--relative` yolu düzleştirmesin).
SAHNE_DOSYALARI = {
    "ROADMAP.md": "# ROADMAP\n\n## §1 tahta\n- [TSK-177] belge eşitleme\n",
    "MERIDIAN_ENGINEERING_LOG.md": "# Günlük\n\n## AÇIK KALANLAR\n- yok\n",
    "docs/RUNBOOK.md": "# RUNBOOK (ÜRETİLMİŞ)\n",
    "docs/alt/KARAR-2026-09-08-x.md": "# Karar\n",
    "research/cards/EDG-2026-999-ornek.yaml": "kimlik: EDG-2026-999\nhipotez: ornek\n",
    "research/cards/README.md": "# Kartlar (ÜRETİLMİŞ)\n",
}

# =================================================================================================
# ŞİMLER — hepsi /bin/sh; her biri çağrıldığını DOSYAYA yazar (mock değil, ayrı süreç).
# =================================================================================================

SSH_SIM = r"""#!/bin/sh
# Sahte ssh: argümanları kaydeder, uzak tarafı $SIM_UZAK dizini ile taklit eder.
KOMUT=""
for a in "$@"; do KOMUT="$a"; done
printf '%s\n' "$*" >> "$SIM_SSH_IZ"
case "$KOMUT" in
  *"cat > "*"mv "*)
      # BEYAN YAZIMI (atomik: .tmp + mv). stdin'i uzak state dosyasına koyar.
      if [ "${SIM_BEYAN_HATA:-0}" = "1" ]; then exit 1; fi
      mkdir -p "$SIM_UZAK/state"
      cat > "$SIM_UZAK/state/belge_esitleme.json"
      # SIM_BEYAN_BOZ: yazım BAŞARILI görünür ama uzak içerik gönderilenden AYRIDIR — geri
      # okuma kıyasının gerçekten koştuğunu ölçmenin tek yolu budur (mutasyon M11).
      if [ "${SIM_BEYAN_BOZ:-0}" = "1" ]; then
        echo "SESSIZ-BOZULMA" >> "$SIM_UZAK/state/belge_esitleme.json"
      fi
      exit 0 ;;
  "cat "*belge_esitleme.json)
      if [ -f "$SIM_UZAK/state/belge_esitleme.json" ]; then
        cat "$SIM_UZAK/state/belge_esitleme.json"; exit 0
      fi
      echo "cat: dosya yok" >&2; exit 1 ;;
  *sha256sum*)
      if [ "${SIM_SHA_HATA:-0}" = "1" ]; then exit 1; fi
      if [ "${SIM_SHA_BOZ:-0}" = "1" ]; then
        echo "deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef"; exit 0
      fi
      if [ -f "$SIM_UZAK/ROADMAP.md" ]; then
        "$SIM_PY" -c 'import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest())' "$SIM_UZAK/ROADMAP.md"
        exit 0
      fi
      echo "sha256sum: dosya yok" >&2; exit 1 ;;
  *curl*)
      # UZAK ARGV MODELLENİR: komut uzak kabukta koşuyormuş gibi ÇALIŞTIRILIR ve PATH'teki
      # `curl` şimi KENDİ argv'sini kaydeder. Tur-1'de bu dal yalnız stdin okuyordu, yani
      # "token uzak `ps aux`ta görünür mü" sorusu HİÇ modellenmemişti (bulgu B6).
      exec /bin/sh -c "$KOMUT" ;;
esac
exit 0
"""

RSYNC_SIM = r"""#!/bin/sh
# Sahte rsync. `--version` bir AKTARIM DEĞİLDİR ve ize YAZILMAZ: yazılsaydı "kaç rsync çağrıldı"
# ölçümü (C1/C2) sürüm sorgusuyla şişerdi.
#
# İKİ FAZ MODELLENİR (tur 3): `--files-from` taşıyan çağrı AKTARIMDIR ve şim LİSTEYE UYAR —
# listede olmayan bir dosyayı taşımaz. `--delete` taşıyan çağrı SALT-SİLME geçişidir ve hiçbir
# şey taşımaz. Şim listeyi UYDURMAZ: "izlenmeyen dosya hedefe gitmez" iddiası ancak listenin
# gerçekten okunmasıyla ölçülebilir. `--no-links` de modellenir (gerçek rsync'in ölçülen metni:
# `skipping non-regular file "<ad>"`), yoksa bayrağın kalkması bu sahnede sessiz kalırdı.
if [ "$1" = "--version" ]; then
  echo "rsync  version 3.9.9-SIM  protocol version 31"
  exit 0
fi
printf '%s\n' "$*" >> "$SIM_RSYNC_IZ"
KURU=0; SIL=0; NOLINK=0; LISTE=""
for a in "$@"; do
  case "$a" in
    -n)             KURU=1 ;;
    --delete)       SIL=1 ;;
    --no-links)     NOLINK=1 ;;
    --files-from=*) LISTE="${a#--files-from=}" ;;
  esac
done
ONCEKI=""; SON=""
for a in "$@"; do ONCEKI="$SON"; SON="$a"; done
KAYNAK="$ONCEKI"; HEDEF="$SON"
UZAK_YOL="${HEDEF#*:}"
REL="${UZAK_YOL#$MERIDIAN_A1_DIR}"
VAR="$SIM_UZAK$REL"

# FAZ-1 AKTARIM. GERÇEK rsync itemize yollarını LİSTEDEKİ hâliyle basar (2026-09-08 ölçümü,
# openrsync: `>f+++++++ alt/K.md`). Ön eki BETİK ekler — şim onu ÜRETMEZ, yoksa kapsam kapısı
# kendi ürettiği ön eki doğrulayan bir tautolojiye dönerdi.
if [ -n "$LISTE" ]; then
  tr '\0' '\n' < "$LISTE" | while IFS= read -r rel; do
    [ -n "$rel" ] || continue
    if [ -L "$KAYNAK$rel" ]; then
      if [ "$NOLINK" = "1" ]; then echo "skipping non-regular file \"$rel\""; continue; fi
      echo "cL+++++++ $rel -> $(readlink "$KAYNAK$rel")"
      if [ "$KURU" = "0" ]; then mkdir -p "$(dirname "$VAR$rel")"; cp -R "$KAYNAK$rel" "$VAR$rel"; fi
      continue
    fi
    echo ">f+++++++ $rel"
    if [ "$KURU" = "0" ]; then
      mkdir -p "$(dirname "$VAR$rel")"
      cp "$KAYNAK$rel" "$VAR$rel"
    fi
  done
fi

# FAZ-2 SALT-SİLME. Taşımaz; yalnız `*deleting` bildirir.
if [ "$SIL" = "1" ]; then
  j=0
  while [ "$j" -lt "${SIM_SIL_N:-0}" ]; do
    echo "*deleting hayalet-$j.md"
    j=$((j+1))
  done
  # SIM_SIL_KACAK / SIM_SIL_MUTLAK — rsync'in KAPSAMDAN TAŞAN bir silme bildirdiği iki dünya.
  # Yapısal düzeltmeden (açık hedef yolu) sonra bu hâller gerçek rsync'te doğmaz; kapsam
  # KAPISININ öttüğünü ölçmenin tek yolu onları burada ÜRETMEKTİR. `..` tırmanması ön ek
  # eklenmiş bir yolun bile kapsamdan çıkabileceğini, mutlak yol ise ön ekin hiç eklenmemesi
  # gerektiğini gösterir (tur-2 incelemesi Y4).
  if [ "${SIM_SIL_KACAK:-0}" = "1" ]; then
    echo "*deleting ../research/edgar_facts/facts.json"
  fi
  if [ "${SIM_SIL_MUTLAK:-0}" = "1" ]; then
    echo "*deleting /etc/passwd"
  fi
fi
# RC EN SONDA: kısmi aktarım YAPILMIŞ olur, sonra düşer — "taşındı ama kayıtsız" hâli budur.
if [ "$KURU" = "1" ]; then exit "${SIM_RSYNC_RC_KURU:-0}"; fi
exit "${SIM_RSYNC_RC:-0}"
"""

#: [00] G1 — RSYNC_BIN'in GERÇEKTEN kullanıldığını ölçmenin tek yolu, varsayılan `kutu/rsync`
#: şiminden (RSYNC_SIM, SIM_RSYNC_IZ'e yazar) AYRI bir iz taşıyan İKİNCİ bir GNU-biçimli şimdir.
#: `--version` çağrıldığını da AYRI bir dosyaya işaretler (RSYNC_SIM bunu bilinçli YAZMAZ —
#: yukarıdaki gerekçeye bak — o yüzden aynı izi paylaşamaz).
RSYNC_BIN_ALT_SIM = r"""#!/bin/sh
if [ "$1" = "--version" ]; then
  : > "$SIM_RSYNC_BIN_VERSIYON_IZ"
  echo "rsync  version 3.9.9-ALT  protocol version 31"
  exit 0
fi
printf '%s\n' "$*" >> "$SIM_RSYNC_BIN_IZ"
exit 0
"""

#: [00] G2 — GERÇEK openrsync'in ÖLÇÜLMÜŞ `--version` metnini AYNEN üretir (bu Mac,
#: `/usr/bin/rsync --version`, 2026-09-08: "openrsync: protocol version 29" ilk satır). Herhangi
#: bir aktarım/silme argümanıyla çağrılırsa da bunu bir ize yazar — [00] kapısı onu hiç
#: ÇAĞIRMAMALIDIR (betik `--version`den SONRA, ilk transfer çağrısından ÖNCE durur).
RSYNC_OPENRSYNC_SIM = r"""#!/bin/sh
if [ "$1" = "--version" ]; then
  echo "openrsync: protocol version 29"
  echo "rsync version 2.6.9 compatible"
  exit 0
fi
printf '%s\n' "$*" >> "$SIM_RSYNC_OPENRSYNC_IZ"
exit 0
"""

CURL_SIM = r"""#!/bin/sh
# Sahte curl: KENDİ argv'sini ve stdin'ini AYRI izlere yazar. İki iz ayrı olmalı — token'ın
# argv'de OLMADIĞI ile stdin'den GEÇTİĞİ birbirinden bağımsız iki iddiadır.
printf '%s\n' "$*" >> "$SIM_CURL_IZ"
cat >> "$SIM_TOKEN_IZ"
printf '%s' "${SIM_API_YANIT:-}"
exit 0
"""

SHA_SIM = r"""#!/bin/sh
# Sahte sha256sum: GERÇEK özet üretir (kıyas anlamlı kalsın) ama çağrıldığını kaydeder.
printf '%s\n' "$*" >> "$SIM_SHA_IZ"
"$SIM_PY" -c 'import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest()+"  "+sys.argv[1])' "$1"
"""

GIT_KILIT = r"""#!/bin/sh
# SİSTEMİK KİLİT: GERÇEK depo ağacında git koşulmasını imkânsız kılar. `$PWD` KULLANILMAZ —
# subprocess `cwd=` verse bile çocuk süreç ebeveynin PWD ortam değişkenini miras alır ve kilit
# yanlış dizini ölçerdi; `pwd -P` gerçek çalışma dizinini söyler.
# SIM_LSFILES_HATA: aktarım listesinin ALINAMADIĞI dünya (fail-closed ayağı, B6).
if [ "${SIM_LSFILES_HATA:-0}" = "1" ]; then
  for a in "$@"; do
    if [ "$a" = "ls-files" ]; then
      echo "fatal: SIM — git ls-files düştü" >&2
      exit 128
    fi
  done
fi
D="$(pwd -P)"
case "$D" in
  "$SIM_YASAK_KOK"|"$SIM_YASAK_KOK"/*)
      echo "@@GERCEK-DEPO-GIT-YAKALANDI@@ pwd=$D argv=$*" >&2
      exit 113 ;;
esac
exec "$SIM_GERCEK_GIT" "$@"
"""


def _yaz_sim(kutu: pathlib.Path, ad: str, govde: str) -> None:
    p = kutu / ad
    p.write_text(govde, encoding="utf-8")
    p.chmod(0o755)


@pytest.fixture
def sahne(tmp_path):
    """tmp_path'te SAHTE bir Meridian deposu + sahte `origin` + PATH şimleri.

    `origin` gerçek bir çıplak depodur (yerel yol): `fetch`/`rev-list` ağ olmadan, GERÇEK git
    semantiğiyle koşar. Sahte bir remote taklidi, [0b] kapısının asıl ölçtüğü şeyi (git'in
    ilerideki commit sayımı) taklit etmiş olurdu.
    """
    gercek_git = shutil.which("git")
    assert gercek_git, "git PATH'te yok — sahne kurulamaz"

    kutu = tmp_path / "bin"
    kutu.mkdir()
    uzak_fs = tmp_path / "a1"          # A1'in taklidi (rsync/ssh buraya yazar)
    uzak_fs.mkdir()
    repo = tmp_path / "repo"
    repo.mkdir()
    ciplak = tmp_path / "origin.git"

    izler = {ad: tmp_path / f"{ad}.iz" for ad in ("ssh", "rsync", "sha", "token", "curl")}
    for p in izler.values():
        p.touch()

    ort = {
        "PATH": f"{kutu}{os.pathsep}{os.environ.get('PATH', '')}",
        # $HOME var olmayan bir dizine çekilir: `--kok` verilmezse betik $HOME/AI-Trading'e
        # düşer ve orası YOKTUR — yani unutulan bir --kok sessizce gerçek depoya gidemez.
        "HOME": str(tmp_path / "bos-ev"),
        "MERIDIAN_A1_KEY": str(tmp_path / "sahte-anahtar.key"),
        "MERIDIAN_A1_IP": "203.0.113.9",       # TEST-NET-3: yönlendirilemez, kazara bile gitmez
        "MERIDIAN_A1_DIR": "/opt/meridian",
        "SIM_UZAK": str(uzak_fs),
        "SIM_PY": shutil.which("python3") or "python3",
        "SIM_SSH_IZ": str(izler["ssh"]),
        "SIM_RSYNC_IZ": str(izler["rsync"]),
        "SIM_SHA_IZ": str(izler["sha"]),
        "SIM_TOKEN_IZ": str(izler["token"]),
        "SIM_CURL_IZ": str(izler["curl"]),
        "SIM_YASAK_KOK": str(REPO.parent if REPO.name != "AI-Trading" else REPO),
        "SIM_GERCEK_GIT": gercek_git,
        # RSYNC_BIN ŞİMİ SABİTLER (TSK-177 tur 4, [00] gate'i): seçim sırası artık
        # RSYNC_BIN → /opt/homebrew/bin/rsync (varsa) → PATH. İkinci ayak bu geliştirme
        # makinesinde GERÇEKTEN VAR (GNU 3.5.0) — RSYNC_BIN verilmeseydi şim sahnesi sessizce
        # GERÇEK rsync'e kayardı ve `_iz(sahne, "rsync")` hep boş kalırdı (körlük, Yasa 6 sınıfı).
        # RSYNC_BIN, [00]'ın KENDİ öncelik sırasının EN TEPESİ olduğu için bu, gerçek operatör
        # akışını da ölçer: G1 çivisi.
        "RSYNC_BIN": str(kutu / "rsync"),
    }
    # Kilit GERÇEK ana checkout'u hedefler: bu dosya bir worktree'den de koşuyor olabilir ve
    # worktree ana checkout'un ALTINDADIR, yani tek kök ikisini de kapatır.
    ana = REPO
    while ana.name != "AI-Trading" and ana.parent != ana:
        ana = ana.parent
    ort["SIM_YASAK_KOK"] = str(ana)

    for ad, govde in (("ssh", SSH_SIM), ("rsync", RSYNC_SIM), ("curl", CURL_SIM),
                      ("sha256sum", SHA_SIM), ("git", GIT_KILIT)):
        _yaz_sim(kutu, ad, govde)

    tam_ort = {**os.environ, **ort}

    def _g(*args, cwd=repo):
        return subprocess.run(["git", *args], cwd=str(cwd), env=tam_ort,
                              capture_output=True, text=True, check=True, timeout=120)

    # `cwd=` ŞART: verilmezse çocuk süreç pytest'in çalışma dizinini (yani GERÇEK depo ağacını)
    # miras alır ve sistemik git kilidi rc=113 ile öter. Kilit bu satırı ilk yazışta gerçekten
    # yakaladı (2026-09-08) — kilidin kendisi de böylece bir kez ÖLÇÜLMÜŞ oldu.
    subprocess.run(["git", "init", "--bare", "-b", "main", str(ciplak)], env=tam_ort,
                   cwd=str(tmp_path), capture_output=True, text=True, check=True, timeout=120)
    _g("init", "-b", "main")
    _g("config", "user.email", "sahne@ornek.gecersiz")
    _g("config", "user.name", "Sahne")
    for rel, govde in SAHNE_DOSYALARI.items():
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(govde, encoding="utf-8")
    # `.dash.env` ve `*.gecici` YOK SAYILIR: ikisi de [0c]'nin varlık sebebini kurar —
    # yok sayılan dosya `status`ta görünmez ama rsync onu taşırdı.
    (repo / ".gitignore").write_text(".dash.env\n*.gecici\n", encoding="utf-8")
    _g("add", ".gitignore", *SAHNE_DOSYALARI.keys())
    _g("commit", "-m", "sahne")
    _g("remote", "add", "origin", str(ciplak))
    _g("push", "-q", "-u", "origin", "main")

    return {"repo": repo, "uzak": uzak_fs, "ort": ort, "tam_ort": tam_ort,
            "iz": izler, "git": _g, "kutu": kutu}


def _kos(sahne, *args, kok=True, **ek_ort):
    """`kok=False` operatörün GERÇEKTE yazacağı bayraksız biçimi koşar (varsayılan kök yolu)."""
    ort = {**sahne["tam_ort"], **ek_ort}
    komut = ["bash", str(BETIK)]
    if kok:
        komut += ["--kok", str(sahne["repo"])]
    komut += list(args)
    return subprocess.run(komut, env=ort, capture_output=True, text=True, timeout=300,
                          cwd=str(sahne["repo"].parent))


def _iz(sahne, ad: str) -> list[str]:
    return [s for s in sahne["iz"][ad].read_text(encoding="utf-8").splitlines() if s.strip()]


def _kilit_otmedi(r) -> None:
    """Her koşumda sorulur: sistemik git kilidi ötmüş mü? Ötmüşse test 'geçmiş' olamaz —
    betik gerçek depo ağacında git koşmuş demektir."""
    assert GIT_KILIT_ISARET not in (r.stdout + r.stderr), \
        f"BETİK GERÇEK DEPODA git KOŞTU:\n{r.stderr}"


def _kaynak() -> str:
    return BETIK.read_text(encoding="utf-8")


def _kod_satirlari() -> list[str]:
    """Betiğin YORUM OLMAYAN satırları. Gerekçe yorumları aranan dizgeleri AYNEN taşır
    (v452'nin ölçülmüş tuzağı: `"<yol>" in metin` çivisi yorum yüzünden yeşil kalmıştı) —
    davranış iddiası KOD satırından ölçülür."""
    return [s for s in _kaynak().splitlines() if not s.lstrip().startswith("#")]


def _cagri_satirlari() -> list[str]:
    """Yorum OLMAYAN **ve** `echo`/`printf` ile BAŞLAMAYAN satırlar.

    İKİNCİ TUZAK, İLK KOŞUMDA ÖLÇÜLDÜ (2026-09-08): yorumları elemek YETMEDİ. Kapı [0d]'nin
    onarım reçetesi bir yorum değil bir `echo`dur ve "./dagit.sh" adını AYNEN taşır — D5 çivisi
    betikte hiçbir dağıtım çağrısı olmadığı hâlde kırmızı yandı. Operatöre BASILAN bir metin,
    o işin YAPILDIĞININ kanıtı değildir (v452'nin aynı dersi, ters yönden)."""
    return [s for s in _kod_satirlari() if not re.match(r"\s*(echo|printf)\b", s)]


# =================================================================================================
# [A] KAPSAM — küme kilidi ve yasak sınıf
# =================================================================================================

def test_A1_kume_dizisi_KILITLI_dort_kok():
    """TEK KAYNAK VE KİLİT. Küme betikte tek bir dizidir; buradaki eşitlik onu dondurur.

    Kapsam genişlemesi SESSİZ OLAMAZ: bu yol worker durdurmadan, `uv sync` çalıştırmadan ve
    tam suite hükmü beklemeden canlıya yazar. Kümeye bir kaynak dizini eklemek, kapısız ikinci
    bir dağıtım kanalı açmak olurdu — o karar bir testi kırmak zorunda."""
    m = re.search(r"^BELGE_KUMESI=\((.*)\)\s*$", _kaynak(), re.M)
    assert m, "BELGE_KUMESI dizisi bulunamadı — küme tek dizi olmalı"
    assert shlex.split(m.group(1)) == [
        "ROADMAP.md", "MERIDIAN_ENGINEERING_LOG.md", "docs", "research/cards"]


def test_A2_yasak_sinif_diskteki_py_dosyasini_YAKALAR(sahne):
    """[0d]'nin ASIL yükü: küme kökleri temiz olsa BİLE altlarına bir `.py` düşerse yol kapanır.

    Bu ihtimal teorik değil — `docs/` altına bir üretici betiği koymak (ya da bir ölçüm kartının
    yanına yardımcı script bırakmak) bu depoda olabilecek bir şeydir, ve o dosya buradan
    geçseydi canlıya KAPISIZ kod gitmiş olurdu."""
    p = sahne["repo"] / "docs" / "sahte_uretici.py"
    p.write_text("print('canlıya kapısız kod')\n", encoding="utf-8")
    sahne["git"]("add", "docs/sahte_uretici.py")
    sahne["git"]("commit", "-m", "sahte py")
    sahne["git"]("push", "-q", "origin", "main")

    r = _kos(sahne)
    _kilit_otmedi(r)
    assert r.returncode == 1, r.stdout
    assert "DURDU:" in r.stdout and "docs/sahte_uretici.py" in r.stdout
    assert not _iz(sahne, "rsync"), "kapı DURDURDU ama rsync yine de çağrıldı"


def test_A3_temiz_kumede_yasak_sinif_kapisi_GECER(sahne):
    """NEGATİF EŞ: [0d] her zaman durduran bir kapı olsaydı A2 de yeşil kalırdı."""
    r = _kos(sahne)
    _kilit_otmedi(r)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "✓ yasak sınıf yok" in r.stdout


# =================================================================================================
# [B] KAPILAR — [0a] · [0b] · [0c]
# =================================================================================================

def test_B1_0a_kirli_agac_DURDURUR(sahne):
    """Commit'lenmemiş bir belge canlıya giderse, canlıdaki metnin hiçbir git nesnesinde
    karşılığı olmaz — 'canlıda ne var' sorusu bir daha cevaplanamaz."""
    (sahne["repo"] / "ROADMAP.md").write_text("# ROADMAP\nyarım iş\n", encoding="utf-8")
    r = _kos(sahne)
    _kilit_otmedi(r)
    assert r.returncode == 1, r.stdout
    assert "DURDU:" in r.stdout and "KİRLİ" in r.stdout
    assert "ROADMAP.md" in r.stdout, "hangi dosyanın kirli olduğu yazılmıyor"
    assert not _iz(sahne, "rsync") and not _iz(sahne, "ssh")


def test_B2_0b_pushlanmamis_HEAD_DURDURUR(sahne):
    """Yalnız A1'de duran bir belge, hiçbir klonun göremediği bir gerçektir: cloud oturumu
    GitHub'daki hâli görür, pano A1'dekini — ikisi sessizce ayrışır."""
    (sahne["repo"] / "ROADMAP.md").write_text("# ROADMAP\nyeni satır\n", encoding="utf-8")
    sahne["git"]("add", "ROADMAP.md")
    sahne["git"]("commit", "-m", "push'lanmamış")
    r = _kos(sahne)
    _kilit_otmedi(r)
    assert r.returncode == 1, r.stdout
    assert "DURDU:" in r.stdout and "push'lanmamış" in r.stdout
    assert "1 commit" in r.stdout, "kaç commit ileride olduğu ölçülüp yazılmıyor"
    assert not _iz(sahne, "rsync")


def test_B3_0b_fetch_DUSERSE_kapi_gecilmis_sayilmaz(sahne):
    """FAIL-CLOSED. `fetch` düşerse "ileride commit yok" DEĞİL "ÖLÇEMEDİM" doğrudur.
    Ölçülemeyen kapıyı geçilmiş saymak, bu depoda adı konmuş bir hata sınıfıdır."""
    sahne["git"]("remote", "set-url", "origin", str(sahne["repo"].parent / "boyle-bir-origin-yok.git"))
    r = _kos(sahne)
    _kilit_otmedi(r)
    assert r.returncode == 1, r.stdout
    assert "DURDU:" in r.stdout and "ÖLÇÜLEMEDİ" in r.stdout
    assert not _iz(sahne, "rsync")


def test_B4_0c_izlenmeyen_dosya_RAPOR_EDILIR_ve_LISTEYE_GIRMEZ(sahne):
    """[0a] YETMEZ — ama çare KAPI DEĞİL, YAPIdır (tur 3).

    `docs/gizli.gecici` `.gitignore`ludur: `status --porcelain` onu GÖRMEZ, yani [0a] temiz der.
    rsync de `.gitignore` OKUMAZ. Tur-2 bunu bir kapıyla kapatıyordu ve o kapı operatörün İLK
    kuru koşumunu ana checkout'ta DURDURUYORDU (ölçüldü: `docs/mutasyon/.*.ham.log`). Artık
    aktarım listesi `git ls-files`ten türer: yok sayılan dosya listede YOKTUR, rsync onu hiç
    görmez. [0c] bu yüzden bir RAPORdur — DURDURMAZ, ama sessiz de kalmaz.

    Davranış ayağı (dosya GERÇEKTEN gitmiyor mu) F1'dedir; burası akış ve rapor ayağıdır."""
    (sahne["repo"] / "docs" / "gizli.gecici").write_text("yok sayılan\n", encoding="utf-8")
    durum = subprocess.run(["git", "status", "--porcelain"], cwd=str(sahne["repo"]),
                           env=sahne["tam_ort"], capture_output=True, text=True, timeout=60)
    assert durum.stdout.strip() == "", \
        "önkoşul çöktü: dosya yok sayılmıyor, o hâlde bu test [0a]'yı ölçüyor olurdu"

    r = _kos(sahne, "--uygula")
    _kilit_otmedi(r)
    assert r.returncode == 0, f"rapor kapıya dönmüş (rc={r.returncode})\n{r.stdout}"
    assert "DURDU:" not in r.stdout
    assert "disk ≠ git" in r.stdout and "docs/gizli.gecici" in r.stdout, \
        f"aktarılmayan dosya RAPOR edilmiyor — körlük sessiz olurdu:\n{r.stdout}"
    # Şim listeye UYAR: dosya listede yoksa hedefe de gitmez.
    assert not (sahne["uzak"] / "docs" / "gizli.gecici").exists(), "yok sayılan dosya canlıya gitti"
    aktarilan = [s for s in r.stdout.splitlines() if ">f" in s]
    assert not any("gizli.gecici" in s for s in aktarilan), \
        f"yok sayılan dosya aktarım listesinde: {aktarilan}"


def test_B6_aktarim_LISTESI_alinamazsa_FAIL_CLOSED(sahne):
    """[0b]'nin `fetch` dalıyla AYNI SINIF, yeni katmanda: aktarım kümesi artık git'ten türüyor,
    yani `git ls-files` düşerse "ne taşınacağı" ÖLÇÜLEMEMİŞ demektir. `set -e` ile sessizce
    düşmek sözleşme dışı bir çıkış kodu üretirdi (tur-2'de rsync'in 23'ü tam olarak böyle
    kaçmıştı); burada DURDU + çıkış 1 + git'in kendi hata metni basılır."""
    r = _kos(sahne, "--uygula", SIM_LSFILES_HATA="1")
    _kilit_otmedi(r)
    assert r.returncode == 1, f"ölçülemeyen liste geçilmiş sayıldı (rc={r.returncode})\n{r.stdout}"
    assert "DURDU:" in r.stdout and "aktarım listesi ALINAMADI" in r.stdout
    assert "fail-closed" in r.stdout
    assert "git ls-files düştü" in r.stdout, "git'in kendi hata metni YUTULMUŞ (Yasa 4)"
    assert not _iz(sahne, "rsync"), "liste ölçülemedi ama rsync yine de çağrıldı"


def test_B7_kok_DOSYA_izli_degilse_DURDURUR(sahne):
    """DİZİNDE rapor, KÖK DOSYADA kapı — ve ayrım ölçülür.

    Yok sayılan bir dosya bir dizin girdisinin ALTINDAYSA aktarım listesinde olmaması doğru
    davranıştır (B4/F1: taşınmaz, raporlanır). Ama küme girdisinin KENDİSİ bir dosyaysa aynı hâl
    başka bir şey demektir: `ROADMAP.md` hiç taşınmazken betik "EŞİTLEME TAMAM" derdi — panonun
    okuduğu dosya bayat kalır ve kimse fark etmez. Bu yüzden orada DURULUR."""
    sahne["git"]("rm", "-q", "--cached", "ROADMAP.md")
    (sahne["repo"] / ".gitignore").write_text(".dash.env\n*.gecici\nROADMAP.md\n", encoding="utf-8")
    sahne["git"]("add", ".gitignore")
    sahne["git"]("commit", "-m", "ROADMAP izlenmiyor")
    sahne["git"]("push", "-q", "origin", "main")
    durum = subprocess.run(["git", "status", "--porcelain"], cwd=str(sahne["repo"]),
                           env=sahne["tam_ort"], capture_output=True, text=True, timeout=60)
    assert durum.stdout.strip() == "", "önkoşul çöktü: [0a] bunu zaten yakalıyor olurdu"

    r = _kos(sahne, "--uygula")
    _kilit_otmedi(r)
    assert r.returncode == 1, f"izli olmayan kök DOSYA sessizce atlandı (rc={r.returncode})\n{r.stdout}"
    assert "DURDU:" in r.stdout and "İZLİ DEĞİL" in r.stdout and "ROADMAP.md" in r.stdout
    assert ">> EŞİTLEME TAMAM" not in r.stdout
    assert not _iz(sahne, "rsync")


def test_B5_temiz_pushlanmis_agac_TUM_KAPILARDAN_GECER(sahne):
    """NEGATİF EŞ (B1-B4'ün hepsi için): kapılar her zaman durusaydı dördü de yeşil kalırdı."""
    r = _kos(sahne)
    _kilit_otmedi(r)
    assert r.returncode == 0, r.stdout + r.stderr
    for etiket in ("[0a]", "[0b]", "[0c]", "[0d]"):
        assert etiket in r.stdout, f"{etiket} kapısı çıktıda etiketli değil"
    assert "DURDU:" not in r.stdout


# =================================================================================================
# [C] ÖLÇÜM — kuru koşum · rsync argümanları · beyan · doğrulama · sır
# =================================================================================================

def test_C1_kuru_kosum_HICBIR_YAZIM_yapmaz(sahne):
    """KURU KOŞUM VARSAYILANDIR ve gerçekten kurudur: rsync `-n` ile koşar, uzak tarafa tek bayt
    gitmez, beyan dosyası OLUŞMAZ. Varsayılanı 'uygula' olan bir canlı-yazma betiği, yanlış
    kökle çalıştırılan tek bir çağrıda geri dönüşü olmayan bir iş yapardı."""
    r = _kos(sahne)          # bayraksız = kuru
    _kilit_otmedi(r)
    assert r.returncode == 0, r.stdout + r.stderr
    assert ">> KURU KOŞUM BİTTİ" in r.stdout
    assert "[1a] rsync ÖN-TARAMA" in r.stdout

    cagrilar = _iz(sahne, "rsync")
    assert len(cagrilar) == 6, \
        f"4 aktarım (küme başına bir) + 2 salt-silme (dizin başına bir) bekleniyordu: {cagrilar}"
    for c in cagrilar:
        assert " -n " in f" {c} ", f"kuru koşumda rsync -n YOK: {c}"

    assert list(sahne["uzak"].iterdir()) == [], "kuru koşum uzak tarafa yazdı"
    assert not (sahne["uzak"] / "state" / "belge_esitleme.json").exists()
    for satir in _iz(sahne, "ssh"):
        assert "mv " not in satir, f"kuru koşumda yazan ssh çağrısı: {satir}"


def test_C2_delete_KAPSAMI_ARGUMAN_duzeyinde(sahne):
    """ARGÜMAN SÖZLEŞMESİ (davranış ayağı: E1/F1/F2/F3). Sessizce bozulabilecek her iddia ayrı:

    1. İKİ FAZ. Aktarım çağrısı `--files-from`/`--from0` TAŞIR ve `--delete` TAŞIMAZ; silme
       çağrısı `--delete --max-delete=N --existing --ignore-existing` taşır ve `--files-from`
       TAŞIMAZ. Tek çağrıda birleştirmek ölçülmüş bir sessiz arızadır (openrsync: `--files-from`
       ile `--delete` HİÇBİR ŞEY silmez) — hayalet temizliği yeşil görünüp hiç koşmazdı.
    2. `--delete` yalnız DİZİN girdilerinde; kök DOSYALARDA hiç yok (kök kapsamlı bir silme
       `/opt/meridian`ın tamamını budardı).
    3. `--relative` YOK, `--no-implied-dirs` VAR, `--no-links` VAR, hedef yolu AÇIK. Tur-1'in
       bloker'ı `--relative`in ima ettiği `research/` dizininin `--delete` kapsamına girmesiydi.
    4. SIRA: önce TÜM aktarımlar, sonra silmeler — silme geri alınamayan yarıdır.
    5. ÖN-TARAMA ZORUNLU ve ÖNCE; ön-tarama ile gerçek koşum AYNI argümanları taşır (tek fark
       `-n`). Ayrışırlarsa operatörün onayladığı liste ile uygulanan iş farklı olurdu."""
    r = _kos(sahne, "--uygula")
    _kilit_otmedi(r)
    assert r.returncode == 0, r.stdout + r.stderr

    cagrilar = [shlex.split(c) for c in _iz(sahne, "rsync")]
    assert len(cagrilar) == 12, f"6 ön-tarama + 6 gerçek çağrı bekleniyordu: {cagrilar}"
    on, ger = cagrilar[:6], cagrilar[6:]
    assert all("-n" in c for c in on), f"ilk altı çağrı KURU değil: {on}"
    assert all("-n" not in c for c in ger), f"son altı çağrı kuru: {ger}"
    assert [[a for a in c if a != "-n"] for c in on] == ger, \
        "ön-tarama ile gerçek koşum AYNI argümanları taşımıyor"

    # (kaynak, --delete var mı) → fazın kimliği. SIRA da burada dondurulur.
    beklenen = [("./", False), ("./", False), ("./docs/", False), ("./research/cards/", False),
                ("./docs/", True), ("./research/cards/", True)]
    for etiket, asama in (("ön-tarama", on), ("gerçek", ger)):
        gorulen = []
        for parcalar in asama:
            assert "--relative" not in parcalar, f"{etiket}: --relative geri gelmiş: {parcalar}"
            assert "--no-implied-dirs" in parcalar, f"{etiket}: --no-implied-dirs yok: {parcalar}"
            assert "--no-links" in parcalar, f"{etiket}: --no-links yok: {parcalar}"
            assert "--itemize-changes" in parcalar, f"{etiket}: --itemize-changes yok: {parcalar}"
            kaynak, hedef = parcalar[-2], parcalar[-1]
            siliyor = "--delete" in parcalar
            gorulen.append((kaynak, siliyor))
            assert hedef.endswith(kaynak.lstrip(".")), \
                f"{etiket}: hedef yolu AÇIK değil ({kaynak} → {hedef}) — ima edilen dizin doğar"
            if siliyor:
                # SALT-SİLME geçişi: taşımaz. İki bayrak da yoksa bu çağrı ikinci bir aktarımdır
                # ve `--files-from` listesini AŞARAK izlenmeyen dosyaları canlıya taşırdı.
                assert "--existing" in parcalar and "--ignore-existing" in parcalar, \
                    f"{etiket}: silme geçişi salt-silme değil: {parcalar}"
                assert not any(a.startswith("--files-from") for a in parcalar), \
                    f"{etiket}: `--files-from` + `--delete` — ölçüldü: HİÇBİR ŞEY silmez: {parcalar}"
                # TAVAN: izli yol sayısının %10'u, en az 5 (sahnede 6 izli yol → 5).
                assert "--max-delete=5" in parcalar, f"{etiket}: silme tavanı yok: {parcalar}"
            else:
                assert "--from0" in parcalar, f"{etiket}: --from0 yok (NUL-ayrık liste): {parcalar}"
                liste = [a for a in parcalar if a.startswith("--files-from=")]
                assert len(liste) == 1, f"{etiket}: aktarım listesi verilmemiş: {parcalar}"
                assert not any(a.startswith("--max-delete") for a in parcalar), \
                    f"{etiket}: aktarım çağrısında silme tavanı: {parcalar}"
        assert gorulen == beklenen, f"{etiket}: faz/sıra dağılımı ayrışmış: {gorulen}"


def test_C3_beyan_BES_ALAN_tek_satir_atomik_ve_geri_okunmus(sahne):
    """Beyan, eşitlemenin TEK kalıcı kanıtıdır. Üç şey birden ölçülür: içerik (beş alan),
    biçim (TEK satır — okuyucu satır bazlı) ve YAZIM YOLU (geçici ad + `mv`; doğrudan yazım
    yarıda kesilirse okuyucu YARIM bir JSON görürdü)."""
    r = _kos(sahne, "--uygula")
    _kilit_otmedi(r)
    assert r.returncode == 0, r.stdout + r.stderr

    p = sahne["uzak"] / "state" / "belge_esitleme.json"
    ham = p.read_text(encoding="utf-8")
    assert ham.count("\n") == 1 and ham.endswith("\n"), f"beyan tek satır değil: {ham!r}"
    kayit = json.loads(ham)
    assert set(kayit) == {"esitlenen_sha", "esitlendi_utc", "esitleyen_host",
                          "dosya_n", "silinen_n"}
    assert re.fullmatch(r"[0-9a-f]{40}", kayit["esitlenen_sha"]), kayit["esitlenen_sha"]
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", kayit["esitlendi_utc"])
    assert isinstance(kayit["dosya_n"], int) and isinstance(kayit["silinen_n"], int)

    # ATOMİK YAZIM: geçici ad + mv, TEK ssh komutunda.
    yazim = [s for s in _iz(sahne, "ssh") if "mv " in s]
    assert len(yazim) == 1, f"tam bir atomik yazım bekleniyordu: {yazim}"
    assert ".belge_esitleme.json.tmp" in yazim[0] and "&& mv" in yazim[0]
    # GERİ OKUMA GERÇEKTEN KOŞTU MU? Mesajın kendisi kanıt DEĞİLDİR (mutasyon M11: kıyas
    # silindiğinde "bayt-özdeş doğrulandı" satırı aynen basılmaya devam etti ve çivi yeşil
    # kaldı). Ölçülen şey ÇAĞRI: `[2]` doğrulaması + `[3]` okuyucusu = İKİ geri okuma.
    geri_okuma = [s for s in _iz(sahne, "ssh") if "cat " in s and "mv " not in s]
    assert len(geri_okuma) == 2, f"beyan geri okuma çağrısı eksik: {geri_okuma}"
    assert "bayt-özdeş doğrulandı" in r.stdout


def test_C4_beyan_sha_HEAD_ile_AYNI(sahne):
    """Beyandaki sha, o an eşitlenen ağacın tepesi OLMALI — başka bir sha yazmak, canlıdaki
    belgeyi yanlış bir commit'e bağlar ve 'canlıda ne var' sorusunu yanlış cevaplatır."""
    r = _kos(sahne, "--uygula")
    _kilit_otmedi(r)
    assert r.returncode == 0, r.stdout + r.stderr
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(sahne["repo"]),
                          env=sahne["tam_ort"], capture_output=True, text=True,
                          timeout=60).stdout.strip()
    kayit = json.loads((sahne["uzak"] / "state" / "belge_esitleme.json").read_text())
    assert kayit["esitlenen_sha"] == head
    assert f">> EŞİTLEME TAMAM {head}" in r.stdout


def test_C5_sha_AYRIK_ise_cikis_2(sahne):
    """Dosyalar taşındı ama eşitlik ÖLÇÜLEMEDİ/tutmadı — bu bir başarı değildir. Çıkış 0
    dönseydi çağıran betik/operatör 'eşitlendi' diye okurdu."""
    r = _kos(sahne, "--uygula", SIM_SHA_BOZ="1")
    _kilit_otmedi(r)
    assert r.returncode == 2, f"rc={r.returncode}\n{r.stdout}"
    assert "AYRIK" in r.stdout
    assert ">> EŞİTLEME TAMAM" not in r.stdout, "ayrışıkken 'TAMAM' yazıyor"


def test_C6_sha_OLCULEMEDIGINDE_de_cikis_2(sahne):
    """'Ölçemedim' ile 'eşit' aynı şey değildir (uydurma yasağı)."""
    r = _kos(sahne, "--uygula", SIM_SHA_HATA="1")
    _kilit_otmedi(r)
    assert r.returncode == 2, r.stdout
    assert "ÖLÇÜLEMEDİ" in r.stdout


def test_C7_sha_ESITSE_cikis_0(sahne):
    """NEGATİF EŞ: C5/C6 her zaman 2 dönen bir betikle de yeşil kalırdı."""
    r = _kos(sahne, "--uygula")
    _kilit_otmedi(r)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "ROADMAP.md EŞİT" in r.stdout
    assert _iz(sahne, "sha"), "yerel sha256sum hiç çağrılmamış — kıyas tek taraflı olurdu"


def test_C8_beyan_yazilamazsa_cikis_2(sahne):
    """Beyan yazılamazsa eşitleme KAYITSIZ kalır; sessizce 0 dönmek onu görünmez yapardı."""
    r = _kos(sahne, "--uygula", SIM_BEYAN_HATA="1")
    _kilit_otmedi(r)
    assert r.returncode == 2, r.stdout
    assert "BEYAN YAZILAMADI" in r.stdout


def test_C8b_geri_okuma_SESSIZ_BOZULMAYI_yakalar(sahne):
    """GERİ OKUMANIN ASIL İŞİ. C8 yazımın DÜŞTÜĞÜ hâli ölçer; burada yazım BAŞARILI görünür ama
    uzak içerik gönderilenden AYRIDIR — kıyas koşmuyorsa bu hâl sessizce 'tamam' olur.

    NEDEN AYRI BİR ÇİVİ: mutasyon M11 (kıyası sil) hem C3'ü hem C8'i YEŞİL bıraktı — çünkü
    ikisi de `echo`nun bastığı 'bayt-özdeş doğrulandı' cümlesine bakıyordu. Operatöre BASILAN
    metin, o ölçümün yapıldığının kanıtı değildir; kanıt, bozulmanın YAKALANMASIDIR."""
    r = _kos(sahne, "--uygula", SIM_BEYAN_BOZ="1")
    _kilit_otmedi(r)
    assert r.returncode == 2, f"sessiz bozulma 'tamam' sayıldı (rc={r.returncode})\n{r.stdout}"
    assert "DOĞRULANAMADI" in r.stdout
    assert "bayt-özdeş doğrulandı" not in r.stdout


def test_C9_deleting_satirlari_RAPORA_girer_ve_head_kullanilmaz(sahne):
    """SIGPIPE SINIFI. Silme satırları operatörün göreceği tek yerdir; `head` ile kısaltmak
    yazan tarafa SIGPIPE gönderir ve raporu SESSİZCE budardı (bedel yasası: kısaltmanın ne
    kaybettirdiği de ölçülür). Hem davranış hem kaynak ölçülür."""
    r = _kos(sahne, "--uygula", SIM_SIL_N="3")
    _kilit_otmedi(r)
    assert r.returncode == 0, r.stdout + r.stderr
    # İki dizin × 3 satır = 6 silme; hepsi rapora girmeli, hiçbiri kırpılmamalı.
    assert r.stdout.count("*deleting") == 12, r.stdout   # itemize dökümü + özet blok
    assert "silinen_n=6" in r.stdout
    for i in range(3):
        assert f"docs/hayalet-{i}.md" in r.stdout
        assert f"research/cards/hayalet-{i}.md" in r.stdout
    kayit = json.loads((sahne["uzak"] / "state" / "belge_esitleme.json").read_text())
    assert kayit["silinen_n"] == 6

    assert not any(re.search(r"\bhead\b", s) for s in _kod_satirlari()), \
        "betik kodunda `head` var — kısa okuyucu raporu sessizce budar"


def test_C10_token_YOKKEN_olculemedi_der_ve_DURMAZ(sahne):
    """İsteğe bağlı ölçüm, zorunlu bir kapıya dönüşmemeli: token yoksa akış devam eder ama
    sayı UYDURULMAZ — 'ölçülemedi' + sebep yazılır."""
    r = _kos(sahne)
    _kilit_otmedi(r)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "/api/roadmap: ölçülemedi — token yok" in r.stdout
    assert not _iz(sahne, "token"), "token yokken uca istek atılmış"


def test_C11_token_VARKEN_bayt_olculur_ve_SIR_HICBIR_AKISTA_gorunmez(sahne):
    """SIR SÜZGECİ — DÖRT sızıntı yolu, dördü de ayrı ayrı ölçülür.

    stdout · stderr · YEREL ssh argv · **A1'DEKİ curl argv**. Dördüncüsü tur-1'de ölçülmüyordu:
    şim yalnız stdin okuyordu, uzak kabuğun `$_t`yi genişletip `curl`e ARGÜMAN vermesi hiç
    modellenmemişti — başlık "argümana konulmaz" diyor, kod A1'de tam tersini yapıyordu
    (bulgu B6). Şim artık uzak komutu gerçekten koşuyor ve `curl` kendi argv'sini kaydediyor.

    Pozitif kanıt da aranır: token uzak sürecin STDIN'inden GEÇMİŞ olmalı — yoksa "sızmadı"
    iddiası "hiç gönderilmedi" ile karışırdı."""
    sir = "SIR-TOKEN-cok-gizli-4f2a9c"
    (sahne["repo"] / ".dash.env").write_text(f"MERIDIAN_DASH_TOKEN={sir}\n", encoding="utf-8")
    r = _kos(sahne, SIM_API_YANIT='{"ok": true, "yol": "ROADMAP.md", "bayt": 424242}')
    _kilit_otmedi(r)
    assert r.returncode == 0, r.stdout + r.stderr

    assert "bayt=424242" in r.stdout, r.stdout
    assert sir not in r.stdout, "TOKEN STDOUT'A DÜŞTÜ"
    assert sir not in r.stderr, "TOKEN STDERR'E DÜŞTÜ"
    assert all(sir not in s for s in _iz(sahne, "ssh")), \
        "TOKEN yerel ssh ARGÜMANINDA — yerel süreç listesinde görünürdü"
    curl_argv = _iz(sahne, "curl")
    assert curl_argv, "uzak curl hiç koşmamış — 'argv temiz' iddiası ölçülmemiş olurdu"
    assert all(sir not in s for s in curl_argv), \
        f"TOKEN A1'DE curl ARGÜMANINDA — `ps aux` onu görürdü: {curl_argv}"
    assert any("--config" in s for s in curl_argv), \
        f"uzak istek --config ile kurulmamış: {curl_argv}"
    # POZİTİF: token uzak sürecin STDIN'inden geçti.
    stdin_izi = "\n".join(_iz(sahne, "token"))
    assert f'header = "x-meridian-token: {sir}"' in stdin_izi, \
        f"token stdin'den geçmemiş — ölçüm hiç yapılmamış olabilir: {stdin_izi!r}"


def test_C12_api_yaniti_bozuksa_olculemedi_ve_DURMAZ(sahne):
    """Uç 401/hata döndürürse sayı uydurulmaz; akış da durmaz (isteğe bağlı ölçüm)."""
    (sahne["repo"] / ".dash.env").write_text("MERIDIAN_DASH_TOKEN=x\n", encoding="utf-8")
    r = _kos(sahne, SIM_API_YANIT='{"detail":"yetkisiz"}')
    _kilit_otmedi(r)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "/api/roadmap: ölçülemedi" in r.stdout and "bayt=" not in r.stdout


def test_C13_beyanin_OKUYUCUSU_her_kosumda_basar(sahne):
    """YASA 6. `state/belge_esitleme.json`ın okuyucusu bu betiğin kendisidir — yoksa beyan
    'üretilip tüketilmeyen kanıt' olurdu. Okuma İKİ hâlde de dürüst konuşur: kayıt yokken
    'YOK' der (boş/uydurma satır basmaz), varken AYNEN basar."""
    once = _kos(sahne)
    _kilit_otmedi(once)
    assert "son eşitleme kaydı: YOK" in once.stdout

    _kos(sahne, "--uygula")
    sonra = _kos(sahne)
    _kilit_otmedi(sonra)
    kayit = (sahne["uzak"] / "state" / "belge_esitleme.json").read_text().strip()
    assert f"son eşitleme kaydı: {kayit}" in sonra.stdout


# =================================================================================================
# [D] SÖZLEŞME — komut satırı, sözdizimi, yasa 4
# =================================================================================================

def test_D1_bash_n_temiz():
    r = subprocess.run(["bash", "-n", str(BETIK)], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr


def test_D2_bilinmeyen_arguman_cikis_3(sahne):
    """Sessizce yok saymak yerine ADIYLA reddeder: `--uygla` yazan biri, hiçbir şey olmamış
    gibi bir kuru koşum görüp 'eşitledim' sanırdı."""
    r = _kos(sahne, "--uygla")
    assert r.returncode == 3, r.stdout + r.stderr
    assert "bilinmeyen argüman" in r.stdout and "Kullanım:" in r.stdout
    assert not _iz(sahne, "rsync")


def test_D2b_BAYRAKSIZ_operator_bicimi_varsayilan_koku_kullanir(sahne, tmp_path):
    """OPERATÖRÜN KOŞACAĞI BİÇİM (CLAUDE.md §6). Diğer 27 çivinin HEPSİ `--kok` verir, yani
    `KOK="$HOME/AI-Trading"` satırı hiçbir testte KOŞMUYORDU: o satırdaki bir yazım hatası tüm
    suite yeşilken operatörün İLK koşumunda patlardı — 18 çivi yeşilken `--uygula`nın sessizce
    yok sayıldığı vakanın (2026-08-30) aynısı.

    Sahne `$HOME/AI-Trading`i sahte depoya bağlar; ana fikstürün `$HOME`u BİLEREK var olmayan
    bir dizindir (unutulan `--kok` sessizce geçemesin), bu test kendi `$HOME`unu kurar."""
    ev = tmp_path / "ev-varsayilan"
    ev.mkdir()
    (ev / "AI-Trading").symlink_to(sahne["repo"])

    r = _kos(sahne, "--uygula", kok=False, HOME=str(ev))
    _kilit_otmedi(r)
    assert r.returncode == 0, r.stdout + r.stderr
    assert f"kök={ev}/AI-Trading" in r.stdout, f"varsayılan kök kullanılmamış:\n{r.stdout}"
    assert (sahne["uzak"] / "state" / "belge_esitleme.json").exists(), \
        "bayraksız biçim uçtan uca koşmadı"
    assert ">> EŞİTLEME TAMAM" in r.stdout


def test_D3_yasa4_sessiz_yutma_yok():
    """Yasa 4 — `codelaw` yalnız `.py` tarar, yani bir `.sh` dosyasında sessiz yutma MEKANİK
    olarak yakalanmaz. Kapı burada kurulur: gerekçesiz `|| true` ve `2>/dev/null` yok."""
    kod = _kod_satirlari()
    assert not [s for s in kod if "|| true" in s], "gerekçesiz `|| true`"
    assert not [s for s in kod if "2>/dev/null" in s], \
        "stderr çöpe atılıyor — hata kanıtı dosyaya alınmalı, susturulmamalı"


def test_D4_calistirilabilir_ve_RUNBOOK_baslik_sozlesmesine_uyar():
    """`ops/*.sh` RUNBOOK üreticisinin onaylı kümesindedir: başlık = shebang'ten SONRA gelen
    BİTİŞİK `#` bloğudur. Boş satırla bölünmüş bir başlık, belgeye yarım geçerdi."""
    assert os.access(BETIK, os.X_OK), "betik çalıştırılabilir değil"
    satirlar = _kaynak().splitlines()
    assert satirlar[0] == "#!/usr/bin/env bash"
    blok = []
    for s in satirlar[1:]:
        if not s.startswith("#"):
            break
        blok.append(s)
    baslik = "\n".join(blok)
    assert len(blok) > 20, "başlık bloğu bitişik değil ya da çok kısa"
    for beklenen in ("KULLANIM", "--uygula", "--kuru", "--kok", "ÇIKIŞ KODLARI"):
        assert beklenen in baslik, f"başlıkta `{beklenen}` yok — sözleşme RUNBOOK'a çıkmaz"


def test_D5_yerelde_worker_durdurma_ve_uv_sync_YOK():
    """BU BİR DAĞITIM DEĞİLDİR. Betiğin var oluş sebebi tam olarak bunları YAPMAMASIdır;
    biri gün gelip 'garanti olsun' diye bir restart eklerse, belge düzeltmesi yeniden canlı
    motoru durduran bir işleme dönerdi."""
    kod = "\n".join(_cagri_satirlari())
    for yasak in ("systemctl", "uv sync", "serve.sh", "dagit.sh"):
        assert yasak not in kod, f"betik kodunda `{yasak}` var — bu yol dağıtım değildir"
    # POZİTİF EŞ: adın YALNIZ operatör mesajında geçtiği ölçülür — yasak listesi boş bir
    # kaynakta da yeşil kalırdı, oysa reçetenin kullanıcıya söylenmesi İSTENEN davranıştır.
    assert any("dagit.sh" in s for s in _kod_satirlari()), \
        "betik operatöre 'kod yalnız dagit.sh ile çıkar' reçetesini hiç söylemiyor"


# =================================================================================================
# [E] SİLME KAPSAMI — GERÇEK rsync ile, DAVRANIŞ düzeyinde (tur 2)
#
# NEDEN AYRI BİR BÖLÜM. Yukarıdaki `RSYNC_SIM` silme satırlarını `echo "*deleting $AD/..."` ile
# ÜRETİR: yani `*deleting` yolları TANIM GEREĞİ aktarılan dizinin altındadır. O sahnede
# `--delete`in kapsamdan TAŞMASI fiziksel olarak imkânsızdır — şim, ölçülmesi gereken davranışın
# yerine tasarım niyetini koyar. C2 argüman DAĞILIMINI ölçer (değerli), `--delete`in NE SİLDİĞİNİ
# ölçmez.
#
# Bu körlüğün bedeli ÖLÇÜLDÜ (2026-09-08, tur-1 kodu, openrsync 2.6.9-uyumlu):
#     $ rsync -a --relative --delete ./research/cards  dst/
#     *deleting research/olcumler/e1/state/seans.json
#     *deleting research/olcumler/e1/
#     *deleting research/edgar_facts/facts.json      ← 7 silme, yalnız 1'i kümede
# `research/cards` İKİ SEVİYELİDİR; `--relative` hedefte `research/` dizinini "ima edilen dizin"
# olarak yaratır ve `--delete` onu da budar. A1'de `research/` = ~290 MB'tır ve bunun yalnız
# ~952 KB'ı (`research/cards`) belge kümesindedir; kalanı (`olcumler` 277 MB, `edgar_facts`,
# `pit_universe`) git'te KARŞILIĞI OLMAYAN canlı-sahipli veridir — `dagit.sh`ın `RSYNC_EXC`
# listesi onları dağıtımdan bilerek DIŞLAR. Geri dönüşü git'ten OLMAYAN sınıf.
#
# Buradaki sahne şimsizdir: PATH'te GERÇEK `rsync` durur, `ssh` yerine ŞEFFAF bir şim vardır
# (seçenekleri ve konağı atar, uzak komutu YERELDE koşar) ve `$UZAK` gerçek bir dizindir. Yani
# rsync'in kendi silme semantiği, betiğin kendi kurduğu argümanlarla, uçtan uca koşar.
# A1'E YİNE TEK PAKET GİTMEZ: konak adı atılır, hiçbir sokete dokunulmaz.
# =================================================================================================

#: Şeffaf ssh: `-i`/`-o` seçeneklerini ve konağı atar, KALANI yerelde koşar. rsync uzak komutu
#: ÇOK argümanla verir (`rsync --server …`), `${SSH[@]}` ise TEK bir kabuk dizgesiyle — ikisi
#: ayrı ele alınır, yoksa boşluk taşıyan bir yol sessizce bölünürdü.
SSH_SEFFAF = r"""#!/bin/sh
printf '%s\n' "$*" >> "$SIM_SSH_IZ"
while [ $# -gt 0 ]; do
  case "$1" in
    -i|-o|-p|-l|-F) shift 2 ;;
    -*)             shift ;;
    *)              shift; break ;;
  esac
done
if [ $# -eq 1 ]; then exec /bin/sh -c "$1"; fi
exec "$@"
"""

#: A1'in GERÇEK şekli: `research/` altında git'te KARŞILIĞI OLMAYAN canlı-sahipli veri +
#: kümede olan ama git'ten silinmiş gerçek hayaletler + kökte yetim bir dosya + motor kaynağı.
A1_TAKLIDI = {
    "research/edgar_facts/facts.json": "{}\n",
    "research/olcumler/edg075/sonuc.json": "{}\n",
    "research/olcumler/edg075/state/seans_DEPODA_YOK.json": "{}\n",
    "research/pit_universe/u.csv": "sembol\n",
    "docs/eski.md": "# git'te YOK\n",
    "research/cards/EMEKLI.yaml": "kimlik: EMEKLI\n",
    "KOK_YETIM.md": "# kökte yetim\n",
    "meridian/loop.py": "# motor kaynağı — bu yol ona DOKUNMAZ\n",
}

#: Silinmesi BEKLENEN (kümede, git'te yok) · DOKUNULMAMASI beklenen (kapsam dışı).
E_SILINMELI = ["docs/eski.md", "research/cards/EMEKLI.yaml"]
E_DURMALI = [y for y in A1_TAKLIDI if y not in E_SILINMELI]


@pytest.fixture
def sahne_gercek_rsync(sahne):
    """`sahne`nin şimsiz varyantı: GERÇEK `rsync`, ŞEFFAF `ssh`, gerçek bir `$UZAK` dizini."""
    gercek_rsync = shutil.which("rsync", path=os.environ.get("PATH", ""))
    assert gercek_rsync, "rsync PATH'te yok — silme kapsamı ölçülemez"

    (sahne["kutu"] / "rsync").unlink()          # şim kalkar → PATH gerçek rsync'i bulur
    _yaz_sim(sahne["kutu"], "ssh", SSH_SEFFAF)

    uzak = sahne["uzak"]
    for rel, govde in A1_TAKLIDI.items():
        p = uzak / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(govde, encoding="utf-8")
    (uzak / "state").mkdir(exist_ok=True)       # beyanın yazılacağı yer

    for d in (sahne["ort"], sahne["tam_ort"]):
        d["MERIDIAN_A1_DIR"] = str(uzak)
        # RSYNC_BIN burada KALDIRILIR: şim dosyası az önce silindi, yol artık YOK — [00]
        # seçim sırasının 2./3. ayağını (`/opt/homebrew/bin/rsync` → PATH) GERÇEKTEN ölçmenin
        # tek yolu, 1. ayağın (RSYNC_BIN) burada BOŞ olmasıdır (G3 çivisi).
        d.pop("RSYNC_BIN", None)
    sahne["gercek_rsync"] = gercek_rsync
    return sahne


def _a1_var(sahne, rel: str) -> bool:
    return (sahne["uzak"] / rel).exists()


def test_E1_delete_KAPSAMI_gercek_rsync_ile_research_altini_SILMEZ(sahne_gercek_rsync):
    """BLOKER'IN ÇİVİSİ. `--uygula` sonrası A1 taklidinde:

    * `research/edgar_facts/`, `research/olcumler/**`, `research/pit_universe/` DURUR —
      bunlar git'te karşılığı olmayan canlı-sahipli veridir, bu yolun onlara dokunma yetkisi YOK.
    * `docs/eski.md` ve `research/cards/EMEKLI.yaml` SİLİNİR — gerçek hayaletler, silme
      kapsamının İÇİ (yalnız 'hiç silmiyor' demek, `--delete`i tamamen kaldıran bir yamayı da
      yeşil geçirirdi).
    * kök dosyalara ve `meridian/`e DOKUNULMAZ.
    """
    s = sahne_gercek_rsync
    r = _kos(s, "--uygula")
    _kilit_otmedi(r)
    assert r.returncode == 0, r.stdout + r.stderr

    duran = [y for y in E_DURMALI if not _a1_var(s, y)]
    assert duran == [], (
        "KAPSAM DIŞI SİLME — git'te karşılığı olmayan canlı veri gitti: "
        f"{duran}\n{r.stdout}"
    )
    silinen = [y for y in E_SILINMELI if _a1_var(s, y)]
    assert silinen == [], f"hayalet temizliği hiç koşmadı: {silinen}\n{r.stdout}"


def test_E2_kuru_kosum_gercek_rsync_ile_TEK_BAYT_yazmaz(sahne_gercek_rsync):
    """NEGATİF EŞ + kuru koşumun GERÇEK rsync'le ölçümü: `-n` şimin taklit ettiği bir şey
    değildir, rsync'in kendi davranışıdır. Kuru koşum hiçbir hayaleti bile silmez."""
    s = sahne_gercek_rsync
    once = sorted(p.relative_to(s["uzak"]).as_posix()
                  for p in s["uzak"].rglob("*") if p.is_file())
    r = _kos(s)
    _kilit_otmedi(r)
    assert r.returncode == 0, r.stdout + r.stderr
    sonra = sorted(p.relative_to(s["uzak"]).as_posix()
                   for p in s["uzak"].rglob("*") if p.is_file())
    assert once == sonra, f"kuru koşum A1 taklidini DEĞİŞTİRDİ:\n{set(once) ^ set(sonra)}"


def test_E3_KAPSAM_KAPISI_taskin_silmede_DURDURUR(sahne):
    """KAPININ KENDİSİ (üçüncü kat). Yapısal düzeltmeden sonra gerçek rsync kapsam dışı bir
    silme bildiremez — ama bu, kapının gereksiz olduğu anlamına GELMEZ: kapı, yapının bir gün
    (başka bir rsync lehçesi, geri alınmış bir yama, `--relative`e dönüş) bozulduğu hâli
    yakalayan son savunmadır. Kapıyı ölçmenin tek yolu o hâli şimde ÜRETMEKTİR.

    `..` tırmanması bilerek seçildi: ön ek eklenmiş bir yol bile (`docs/../research/...`)
    kapsamdan çıkabilir; kapı yalnız ön-ek karşılaştırsaydı bunu kaçırırdı."""
    r = _kos(sahne, "--uygula", SIM_SIL_N="1", SIM_SIL_KACAK="1")
    _kilit_otmedi(r)
    assert r.returncode == 1, f"kapsam dışı silme DURDURMADI (rc={r.returncode})\n{r.stdout}"
    assert "DURDU: silme kapsamı dışı yol" in r.stdout
    assert "research/edgar_facts" in r.stdout, "hangi yolun kapsam dışı olduğu yazılmıyor"
    assert ">> EŞİTLEME TAMAM" not in r.stdout
    # ÖN-TARAMADA yakalandığı için TEK BAYT yazılmamış olmalı.
    assert list(sahne["uzak"].iterdir()) == [], \
        "kapsam ihlali ön-taramada yakalanmadı — uzak tarafa yazıldı"
    assert not any("-n" not in c for c in _iz(sahne, "rsync")), \
        "ön-tarama durdurmasına rağmen GERÇEK rsync koşmuş"


def test_E4_rsync_SIFIR_DISI_cikista_DURUR_ve_IZ_KORUNUR(sahne):
    """B5. Tur-1'de rsync 23 ile düşünce betik `set -e` ile 23 döndürüyordu (başlıktaki 0/1/2/3
    sözleşmesinin DIŞINDA), `trap` iz dosyasını siliyordu ve o ana kadar TAŞINMIŞ olan şeyin
    kaydı yok oluyordu. Kısmi bir yazımın izsiz kalması Yasa 6 sınıfı bir körlüktür."""
    r = _kos(sahne, "--uygula", SIM_RSYNC_RC="23")
    _kilit_otmedi(r)
    assert r.returncode == 1, f"belgesiz çıkış kodu (rc={r.returncode})\n{r.stdout}"
    assert "DURDU: rsync ÇIKIŞ 23" in r.stdout
    assert "izleri KORUNDU" in r.stdout, "kısmi aktarımın izi sessizce silindi"
    yol = re.search(r"kısmi aktarımın kaydı: ([^\s)]+) · ([^\s)]+)\)", r.stdout)
    assert yol, f"korunan iz dosyalarının YOLU basılmıyor:\n{r.stdout}"
    for g in yol.groups():
        assert pathlib.Path(g).exists(), f"iz dosyası basıldı ama YOK: {g}"
        pathlib.Path(g).unlink()
    assert ">> EŞİTLEME TAMAM" not in r.stdout


def test_E5_kullanilan_rsync_ve_SURUMU_basilir(sahne):
    """Bu turun bloker'ı bir rsync LEHÇESİ farkıyla iç içeydi (openrsync yerelde, GNU A1'de).
    Hangi ikilinin koştuğu raporda yazmazsa, bir sonraki tuhaf silme listesi 'hangi rsync?'
    sorusuyla başlayıp orada tıkanır."""
    r = _kos(sahne)
    _kilit_otmedi(r)
    assert r.returncode == 0, r.stdout + r.stderr
    m = re.search(r"^\s*rsync: (\S+) — (.+)$", r.stdout, re.M)
    assert m, f"kullanılan rsync ve sürümü basılmıyor:\n{r.stdout}"
    assert m.group(1).endswith("/rsync"), m.group(1)
    assert m.group(2).strip(), "sürüm satırı boş"


def test_E6_checksum_AYNI_boyut_AYNI_mtime_ICERIK_FARKLI_belgeyi_YAKALAR(sahne_gercek_rsync):
    """ROL-1 HÜKMÜ (A1 GNU rsync 3.2.7 ölçümü, 2026-09-08, `scratchpad/duzeltme/olcum_TSK177_gnu_rsync.md`).

    `-a`nın hızlı kıyası boyut+mtime'a bakar: kaynakta AYNI boyutta + AYNI mtime'da ama İÇERİĞİ
    değişen bir belge bu kıyasla SESSİZCE atlanır. `[3]`teki ROADMAP.md sha kıyası bunu YAKALARDI
    ama SADECE ROADMAP.md için — `docs/`/`research/cards/` altındaki diğer belgeler için hiçbir
    kıyas YOKTUR. `--checksum` aktarım fazına eklendi: boyut+mtime yerine İÇERİK karşılaştırılır.

    ÖN-KOŞUL ikisi de GERÇEKTEN ölçüldü (bu Mac, openrsync, 2026-09-08): `--checksum` OLMADAN aynı
    senaryoda hedef İÇERİĞİ DEĞİŞMİYOR (atlanıyor); `--checksum` İLE güncelleniyor. Bu test [E]
    desenidir — GERÇEK rsync, ŞEFFAF ssh — çünkü hızlı-kıyas atlaması yalnız gerçek rsync'in kendi
    davranışıdır, RSYNC_SIM'de modellenmez (şim boyut/mtime KIYASLAMAZ, listedeki her dosyayı
    KOŞULSUZ kopyalar)."""
    s = sahne_gercek_rsync
    kaynak = s["repo"] / "docs" / "RUNBOOK.md"
    hedef = s["uzak"] / "docs" / "RUNBOOK.md"

    kaynak.write_text("yeni-icerik\n", encoding="utf-8")     # 12 bayt (11 ascii + \n)
    s["git"]("add", "docs/RUNBOOK.md")
    s["git"]("commit", "-m", "RUNBOOK içeriği güncellendi (boyut aynı kalacak biçimde)")
    s["git"]("push", "-q", "origin", "main")

    hedef.parent.mkdir(parents=True, exist_ok=True)
    hedef.write_text("eski-metin2\n", encoding="utf-8")      # 12 bayt — AYNI boyut, FARKLI içerik
    assert kaynak.stat().st_size == hedef.stat().st_size, \
        "önkoşul çöktü: kaynak/hedef boyutları eşit olmalı (hızlı kıyasın kör noktasını kurmak için)"
    assert kaynak.read_bytes() != hedef.read_bytes(), "önkoşul çöktü: içerikler zaten eşit"

    _AYNI_MTIME = 1735689600   # 2025-01-01T00:00:00Z — rsync'in mtime kıyası saniye çözünürlüklü
    os.utime(kaynak, (_AYNI_MTIME, _AYNI_MTIME))
    os.utime(hedef, (_AYNI_MTIME, _AYNI_MTIME))

    r = _kos(s, "--uygula")
    _kilit_otmedi(r)
    assert r.returncode == 0, r.stdout + r.stderr
    assert hedef.read_text(encoding="utf-8") == "yeni-icerik\n", (
        "AYNI boyut + AYNI mtime + FARKLI içerikli belge AKTARILMADI — hızlı kıyas (boyut+mtime) "
        f"içerik değişikliğini kaçırdı (--checksum eksik olabilir):\n{r.stdout}"
    )


# =================================================================================================
# [F] AKTARIM LİSTESİ · BAĞ · SİLME TAVANI · MUTLAK YOL — tur 3'ün dört ölçümü
#
# Üçü GERÇEK rsync ile ölçülür: hepsi "rsync ne YAPAR" sorusudur, "betik ne YAZAR" değil.
# Dördüncüsü (F4) şim sahnesindedir çünkü ölçülen hâl gerçek rsync'te DOĞMAZ (openrsync
# `*deleting` yollarını her zaman hedefe göre basar — hedef mutlak yolla verildiğinde bile,
# ölçüldü 2026-09-08); kapıyı ölçmenin tek yolu o hâli üretmektir.
# =================================================================================================

def test_F1_YOK_SAYILAN_dosya_DURDURMAZ_ve_CANLIYA_GITMEZ(sahne_gercek_rsync):
    """TUR-2'NİN Y1'İ, GERÇEK rsync ile. İki iddia birden, ikisi de tur-2'de yanlıştı:

    1. `.gitignore`lu bir dosya operatörün İLK kuru koşumunu DURDURMAZ (tur-2'de durduruyordu:
       ana checkout'ta `docs/mutasyon/.*.ham.log` ölçüldü — "yazıldı ≠ çalışır").
    2. Ama canlıya da GİTMEZ. Bu ikisini aynı anda tutmanın tek yolu, aktarım listesini
       `git ls-files`ten türetmektir; `--files-from` kalkarsa gerçek rsync bu dosyayı
       taşır ve çivi kırmızıya döner (şim sahnesinde bu KIRILMAZDI — B4'ün ayağı ordadır)."""
    s = sahne_gercek_rsync
    (s["repo"] / "docs" / "gizli.gecici").write_text("yok sayılan — canlıya GİTMEMELİ\n",
                                                     encoding="utf-8")
    durum = subprocess.run(["git", "status", "--porcelain"], cwd=str(s["repo"]),
                           env=s["tam_ort"], capture_output=True, text=True, timeout=60)
    assert durum.stdout.strip() == "", "önkoşul çöktü: dosya yok sayılmıyor"

    kuru = _kos(s)
    _kilit_otmedi(kuru)
    assert kuru.returncode == 0, f"KURU koşum yok sayılan dosya yüzünden DURDU:\n{kuru.stdout}"
    assert "DURDU:" not in kuru.stdout
    assert "disk ≠ git" in kuru.stdout and "docs/gizli.gecici" in kuru.stdout

    r = _kos(s, "--uygula")
    _kilit_otmedi(r)
    assert r.returncode == 0, r.stdout + r.stderr
    assert not (s["uzak"] / "docs" / "gizli.gecici").exists(), \
        f"YOK SAYILAN DOSYA CANLIYA GİTTİ (aktarım listesi git'ten türemiyor):\n{r.stdout}"
    # NEGATİF EŞ: aktarımın kendisi gerçekten koştu (yoksa "gitmedi" iddiası boş olurdu).
    assert (s["uzak"] / "docs" / "RUNBOOK.md").exists(), "izli dosya da gitmemiş"


def test_F2_SEMBOLIK_BAG_hedefe_GITMEZ_ve_RAPOR_EDILIR(sahne_gercek_rsync):
    """TUR-2'NİN Y2'Sİ. Ölçülen kaza: `docs/mutlak.py -> /etc/passwd` ve `docs/kacak.env` dört
    kapının hepsini geçip A1'e BAĞ olarak gidiyordu (`cL+++++++`) — çünkü kapılar `find -type f`
    ile geziyordu ve bağ o taramada YOKTU. İki savunma ölçülür:

    * İZLİ bir bağ (`docs/BAGLI.md`) aktarım listesindedir ama `--no-links` onu ATLAR ve `[0d]`
      "atlandı: N bağ" diye RAPOR eder (durdurmaz — taşınmayan şey zarar veremez, ama sessiz
      kalırsa bir dahaki sefere kimse fark etmez).
    * İZLENMEYEN bir bağ (`docs/kacak.gecici`) zaten listede yoktur.
    """
    s = sahne_gercek_rsync
    (s["repo"] / "docs" / "BAGLI.md").symlink_to("/etc/hosts")
    (s["repo"] / "docs" / "kacak.gecici").symlink_to("../gizli.env")
    s["git"]("add", "docs/BAGLI.md")
    s["git"]("commit", "-m", "izli bağ")
    s["git"]("push", "-q", "origin", "main")

    r = _kos(s, "--uygula")
    _kilit_otmedi(r)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "atlandı: 1 bağ" in r.stdout, f"izli bağ RAPOR edilmiyor:\n{r.stdout}"
    assert "docs/BAGLI.md" in r.stdout, "hangi yolun bağ olduğu yazılmıyor"
    for bag in ("docs/BAGLI.md", "docs/kacak.gecici"):
        assert not os.path.lexists(s["uzak"] / bag), f"SEMBOLİK BAĞ CANLIYA GİTTİ: {bag}\n{r.stdout}"
    assert (s["uzak"] / "docs" / "RUNBOOK.md").exists(), "aktarım hiç koşmamış (negatif eş)"


def test_F3_SILME_TAVANI_bos_kaynakta_DURDURUR_ve_HEDEFTE_SILME_YOK(sahne_gercek_rsync):
    """SİLME TAVANI (Rol-1 hükmü). Kaynak `docs/` boşaldığında — git'ten silinmiş, ya da `--kok`
    yanlış/ince bir ağaca verilmiş — hedefteki HER dosya "fazlalık" olur ve kapsam kapısı bunu
    YAKALAYAMAZ (hepsi kapsam İÇİdir). Tavan bu sınıfın kapısıdır: `--max-delete=N`, N = izli yol
    sayısının %10'u, en az 5.

    ÖLÇÜLDÜ (openrsync, 2026-09-08): tavan ÖN-TARAMADA (`-n`) da rsync 25 verir ve hedefte tek
    bayt değişmez — yani ZORUNLU ön-tarama sayesinde hiçbir şey silinmeden durulur."""
    s = sahne_gercek_rsync
    # Dizin diskte KALSIN diye yok sayılan bir tutamak; sonra izli docs dosyalarının HEPSİ silinir.
    (s["repo"] / "docs" / ".tut.gecici").write_text("dizin dursun\n", encoding="utf-8")
    s["git"]("rm", "-q", "docs/RUNBOOK.md", "docs/alt/KARAR-2026-09-08-x.md")
    s["git"]("commit", "-m", "docs boşaltıldı")
    s["git"]("push", "-q", "origin", "main")

    hayaletler = [f"docs/hayalet-{i}.md" for i in range(8)]
    for rel in hayaletler:
        (s["uzak"] / rel).write_text("canlıda var, git'te yok\n", encoding="utf-8")
    once = sorted(p.relative_to(s["uzak"]).as_posix()
                  for p in s["uzak"].rglob("*") if p.is_file())

    r = _kos(s, "--uygula")
    _kilit_otmedi(r)
    assert r.returncode == 1, f"tavan aşıldı ama betik DURMADI (rc={r.returncode})\n{r.stdout}"
    assert "DURDU: silme tavanı aşıldı" in r.stdout
    assert "Tavan=5" in r.stdout, f"tavanın DEĞERİ yazılmıyor:\n{r.stdout}"
    assert ">> EŞİTLEME TAMAM" not in r.stdout
    sonra = sorted(p.relative_to(s["uzak"]).as_posix()
                   for p in s["uzak"].rglob("*") if p.is_file())
    assert once == sonra, f"TAVAN ÖTTÜ AMA HEDEF DEĞİŞTİ:\n{set(once) ^ set(sonra)}"
    # `_IZ_KORU`: tavan da kısmi bir silmenin izini bırakabilir; iz dosyaları korunup basılır.
    yol = re.search(r"kısmi aktarımın kaydı: ([^\s)]+) · ([^\s)]+)\)", r.stdout)
    assert yol, f"korunan iz dosyalarının YOLU basılmıyor:\n{r.stdout}"
    for g in yol.groups():
        pathlib.Path(g).unlink(missing_ok=True)


def test_F4_MUTLAK_deleting_yolu_DURDURUR_ve_ON_EK_ALMAZ(sahne):
    """TUR-2'NİN Y4'Ü. Kapının "mutlak yol" ayağı ÖLÜYDÜ ve sebebi ayağın kendisi değildi:
    rapor ön eki MUTLAK yola da ekleniyordu (`docs//etc/passwd`) ve o dize kapsam önekiyle
    BAŞLADIĞI için kapıyı GEÇİYORDU (incelemede ölçüldü: `/etc/passwd` geçti).

    Düzeltme ayağı canlandırmak değil, ön ek hatasını gidermekti: mutlak yola ön ek EKLENMEZ,
    böylece mutlak yol kapsam ayağına takılır (mutlak bir yol hiçbir zaman `docs/` ile
    başlayamaz). Ayrı bir "mutlak" ayağı bu yüzden KALDIRILDI — mutasyona kör kalıyordu.
    Bu çivi, ön ek hatası geri gelirse KIRILIR."""
    r = _kos(sahne, "--uygula", SIM_SIL_N="1", SIM_SIL_MUTLAK="1")
    _kilit_otmedi(r)
    assert r.returncode == 1, f"mutlak yol DURDURMADI (rc={r.returncode})\n{r.stdout}"
    assert "DURDU: silme kapsamı dışı yol" in r.stdout
    assert "/etc/passwd" in r.stdout
    assert "docs//etc/passwd" not in r.stdout, \
        "mutlak yola ön ek eklenmiş — kapsam ayağı onu 'kapsam içi' sanardı"
    assert list(sahne["uzak"].iterdir()) == [], "ön-taramada durmadı, uzak tarafa yazıldı"


# =================================================================================================
# [G] RSYNC İKİLİSİ SEÇİMİ — [00] gate'i (tur 4, TSK-177, CANLI BULGU 2026-09-08)
#
# ÖLÇÜLEN OLAY: Rol-1'in İLK `--kuru` koşumu A1'e karşı `protocol incompatibility (code 2)` ile
# çıkış 2 verdi (macOS `/usr/bin/rsync` = openrsync, A1 = GNU rsync 3.2.7). Betik o gün DOĞRU
# durdu (fail-closed), ama sebep bir LEHÇE farkıydı — [00] bu lehçeyi ÇALIŞMA ANINDA ölçer.
# =================================================================================================

def test_G1_RSYNC_BIN_verilince_O_IKILI_KULLANILIR(sahne, tmp_path):
    """(a) Seçim sırasının 1. ayağı: `RSYNC_BIN` verildiğinde betik gerçekten ONU çağırır — hem
    `--version` sorgusunda hem TÜM transfer çağrılarında. `sahne` zaten varsayılan olarak
    `RSYNC_BIN`i `kutu/rsync`e sabitliyor (aksi hâlde bu makinede KURULU GERÇEK
    `/opt/homebrew/bin/rsync` [00]'ın 2. ayağından sessizce seçilirdi ve ONLARCA şim tabanlı çivi
    körleşirdi); burada AYRI bir ikinci şimle override edilerek "verilen ikili KULLANILIYOR MU"
    sorusu doğrudan ölçülür."""
    ikili = sahne["kutu"] / "rsync-alt"
    _yaz_sim(sahne["kutu"], "rsync-alt", RSYNC_BIN_ALT_SIM)
    versiyon_iz = tmp_path / "rsync_bin_versiyon.iz"
    cagri_iz = tmp_path / "rsync_bin_cagri.iz"
    cagri_iz.touch()

    r = _kos(sahne, RSYNC_BIN=str(ikili),
              SIM_RSYNC_BIN_VERSIYON_IZ=str(versiyon_iz), SIM_RSYNC_BIN_IZ=str(cagri_iz))
    _kilit_otmedi(r)
    assert r.returncode == 0, r.stdout + r.stderr
    assert versiyon_iz.exists(), "RSYNC_BIN --version ile hiç SORGULANMADI"
    cagrilar = [s for s in cagri_iz.read_text(encoding="utf-8").splitlines() if s.strip()]
    assert len(cagrilar) == 6, f"kuru koşumda 6 çağrı bekleniyordu (C1 deseni): {cagrilar}"
    assert not _iz(sahne, "rsync"), \
        "VARSAYILAN şim (kutu/rsync) de çağrılmış — RSYNC_BIN göz ardı edilmiş"
    assert f"rsync: {ikili} —" in r.stdout, f"basılan yol RSYNC_BIN ile eşleşmiyor:\n{r.stdout}"


def test_G2_openrsync_SECILIRSE_KURU_KOSUMDA_DAHI_DURUR_ve_SIFIR_TRANSFER(sahne, tmp_path):
    """(b) CANLI BULGUNUN ÇİVİSİ. macOS'un openrsync'i A1 GNU rsync ile protokol uyumsuz —
    seçilen ikilinin `--version` ilk satırı `openrsync` içeriyorsa betik hiçbir transfer çağrısı
    yapmadan durmalı, VARSAYILAN modda (kuru) bile: yanlış lehçeyle 'ön-tarama temiz geçti'
    sanmak A1'de aynı `ABORTING`e kadar gizli kalırdı."""
    ikili = sahne["kutu"] / "rsync-openrsync"
    _yaz_sim(sahne["kutu"], "rsync-openrsync", RSYNC_OPENRSYNC_SIM)
    cagri_iz = tmp_path / "rsync_openrsync_cagri.iz"
    cagri_iz.touch()

    r = _kos(sahne, RSYNC_BIN=str(ikili), SIM_RSYNC_OPENRSYNC_IZ=str(cagri_iz))
    _kilit_otmedi(r)
    assert r.returncode == 1, f"openrsync KABUL EDİLDİ (rc={r.returncode})\n{r.stdout}"
    assert "DURDU:" in r.stdout and "openrsync" in r.stdout
    assert "brew install rsync" in r.stdout, "reçete basılmıyor"
    assert cagri_iz.read_text(encoding="utf-8").strip() == "", \
        f"openrsync REDDEDİLDİ ama transfer çağrısı yapılmış: {cagri_iz.read_text()!r}"
    assert not _iz(sahne, "rsync"), "varsayılan şim de çağrılmış"
    assert ">> KURU KOŞUM BİTTİ" not in r.stdout, "openrsync reddi kuru koşum başarısı gibi bitmiş"


def test_G3_gercek_sahnede_SECILEN_IKILI_GNU_ve_BASILIR(sahne_gercek_rsync):
    """(c) `sahne_gercek_rsync` GERÇEK sistemin `rsync`ini kullanır (RSYNC_BIN boşaltılmıştır —
    fikstüre bak). Bu Mac'te GNU rsync artık `/opt/homebrew/bin/rsync`tedir (Rol-1'in
    `brew install rsync`i, 2026-09-08); [00] onu seçmeli ve raporda basmalıdır — sistem
    varsayılanı `/usr/bin/rsync` (openrsync) DEĞİL."""
    s = sahne_gercek_rsync
    r = _kos(s)
    _kilit_otmedi(r)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "✓ GNU rsync seçildi:" in r.stdout, f"[00] gate'i geçmemiş:\n{r.stdout}"
    m = re.search(r"^\s*rsync: (\S+) — (.+)$", r.stdout, re.M)
    assert m, f"kullanılan rsync ve sürümü basılmıyor:\n{r.stdout}"
    assert "openrsync" not in m.group(2), f"GERÇEK sahnede openrsync seçilmiş: {m.group(2)}"
    homebrew = pathlib.Path("/opt/homebrew/bin/rsync")
    if homebrew.is_file() and os.access(homebrew, os.X_OK):
        assert m.group(1) == str(homebrew), (
            "[00] 2. ayağı (`/opt/homebrew/bin/rsync`) atlanmış, farklı bir ikili seçilmiş: "
            f"{m.group(1)}"
        )
