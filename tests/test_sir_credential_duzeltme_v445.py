"""test_sir_credential_duzeltme_v445 — 2026-09-07 CANLI OLAYININ ÇİVİLERİ (TSK-064 Faz-1B).

NE OLDU (2026-09-07 ~21:4xZ, A1). Operatör `--faz1 NOUS_API_KEY` ve `--faz1 KAPI_APIKEY`'i
"YENİ değer" istemine BOŞ geçerek koştu — betiğin KENDİ belgelediği varsayılan akış ("boş =
.env icindeki mevcut degeri tasi"). `_deger_dosyala` `.env`in 1. SATIRINI okuyordu (satır ADRESİ),
`^<ad>=` DESENİNİ değil; canlı `.env`in 1. satırı boştu, dolayısıyla:
  1. credential dosyaları 1 baytlık "\\n" ile yazıldı — `[ -s "$tmp" ]` kapısı bunu GEÇTİ;
  2. `_env_satiri_yaz` gerçek `.env` satırlarının yerine `<ad>=` (değersiz) yazdı — iki sır da
     her iki kanaldan birden düştü;
  3. `--faz2` farksal ölçümü SAHTE geçti: kanıtın ANAHTARA bağlı olduğu hiç ölçülmüyordu;
  4. NOUS faz-1 yedeği (`$ENVF.bak-%Y%m%d%H%M`, DAKİKA çözünürlüklü, adsız) KAPI faz-1 tarafından
     aynı dakika içinde EZİLDİ.
Bağımsız inceleme (bulgular_B_sir.json) 1. ve 4. maddeleri olaydan ÖNCE bulmuştu; v439'un G
bölümü `faz1`i hiç koşturmadığı için çiviler yeşildi. Bu dosya o kör noktayı kapatır.

NEDEN AYRI DOSYA. v439 "geçiş nasıl çalışır"ı ölçer; burası "geçiş nasıl KIRILDI"yı ölçer ve her
çivi bugünkü (düzeltme öncesi) betikte KIRMIZI olacak biçimde yazılmıştır — düzeltmeyi ısırdığı
mutasyonla ayrıca gösterilir. Numara KİMLİKTİR (v445), taşınmaz.

BÖLÜMLER (brief B1..B6 ile birebir)
  B1. `_deger_dosyala` ADI ARAR, 1. satırı değil — iki biçim (`ad=değer` / çıplak) ayrı ayrı.
  B2. faz1 boş-değer kapısı: boşluk/satır-sonu DEĞER DEĞİLDİR; reddedilirse HİÇBİR yazım olmaz.
  B3. Yedek adı çakışmaz: ad + saniye çözünürlüklü damga, asla üstüne yazmaz.
  B4. faz2 NEGATİF KONTROL: kanıt anahtara bağlı değilse ölçüm YAPILMADI sayılır (uydurma yasağı).
  B5. `geri_al` PAYLAŞILAN drop-in'i kaldırmadan önce HER adın ortam satırını geri yazar.
  B6. Sertleştirmeler: `-K` config'inde token kaçışı · `SIR_GECIS_KOK` doluysa BÜYÜK uyarı.

TUR 2 (2026-09-08) — B1..B6'nın ÇEKİŞMELİ İNCELEMESİNDEN çıkan yedi kök. Tur-1 düzeltmesi
"boş değer değer değildir" ve "negatif kontrol" hükümlerini getirdi, ama ikisi de YENİ yüzeyler
açtı: negatif kontrolün `.olcum-yedek`leri (gerçek değerin diskteki TEK kopyası) ve genişleyen
`geri_al`. Bölümler brief B-2'nin kökleriyle birebir:
  K1. faz2/geri_al girişinde `.olcum-yedek` VARSA hiçbir şey yazılmaz, ÇIKIŞ 2 — kurtarma
      komutları basılır. Eski kod o iki dosyayı ilk iş olarak SİLİYORDU.
  K2. `geri_al`: başta yedek · öteki adın YERİNDE duran satırına dokunma · `$ad` geri
      yazılamadıysa drop-in KALDIRILMADAN dur.
  K3. `test -s` kalıntıları (`faz1` drop-in döngüsü · `durum` · `faz1_hafiza`) → `_dolu_mu`;
      `durum` boş kaynağı "BOŞ (N bayt)" diye söyler.
  K4. `_deger_dosyala` env kipi: `^ad=` satırı BİRDEN ÇOKSA dur (systemd SONuncuyu okur).
  K5. `.env` yedekleri servis kullanıcısının okuyamayacağı yere (`/root/meridian-env-yedek`,
      0700 dizin / 0400 dosya) yazılır — düz metin sır `.env`in yanında bırakılmaz.
  K6. faz2 girişinde POZİTİF TABAN: kanıt ucu daha başta OK demiyorsa negatif kontrolün "YOK"u
      hiçbir şey kanıtlamaz (hep-YOK deliği).
  K7. Ölçümün ölçülmemiş kalan yüzeyleri: ortam kanalı okunuyorsa durma · negatif kontrol
      penceresinde servis düşerse trap'in DEĞERLERİ GERİ GETİRMESİ · `--faz2 KAPI_APIKEY`
      (kapı kilidi 401 / kilit yok / uç okunamıyor).

SIR DEĞERİ YOK: buradaki her değer SAHTEDİR ve adında öyle yazar. Betik A1'de koşar; bu dosya
A1'e HİÇ dokunmaz — her şey `SIR_GECIS_KOK` sahte kökü + PATH şimleri (sudo/systemctl/curl/date)
ile ölçülür (v439'un G bölümündeki desen).
"""
from __future__ import annotations

import os
import pathlib
import re
import subprocess

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
BETIK = REPO / "deploy" / "oracle-a1" / "sir_credential_gecis.sh"
DROPIN = REPO / "deploy" / "oracle-a1" / "meridian.service.d" / "53-nous-kapi-credential.conf"

#: Olaydaki `.env`in ŞEKLİ: hedef değişken 1. SATIRDA DEĞİL. Değerler sahte.
DASH_SAHTE = "SAHTE-DASH-TOKEN-1"
NOUS_SAHTE = "SAHTE-NOUS-DEGERI-3"
KAPI_SAHTE = "SAHTE-KAPI-DEGERI-4"
#: `_kapi_kilidi_olc` kapı ucunu `.env`ten okur — uç fikstürde YAŞAR, koda gömülmez (K7).
KAPI_UC = "https://sahte.example/gw"
ENV_COK_SATIR = (
    f"MERIDIAN_DASH_TOKEN={DASH_SAHTE}\n"
    "NOUS_MODEL=sahte-model\n"
    f"NOUS_API_KEY={NOUS_SAHTE}\n"
    f"KAPI_APIKEY={KAPI_SAHTE}\n"
    f"NOUS_ENDPOINT={KAPI_UC}\n"
    "MERIDIAN_FMP_BASE=https://sahte.example/api\n"
)
#: `.env` yedeklerinin K5 sonrası yeri — sahte kökün ALTINDA (`$KOK/root/meridian-env-yedek`).
YEDEK_ALT = "root/meridian-env-yedek"

#: `sudo` şimi `chown`u KOŞMAZ (tmp'de root yok) ama ÇAĞRIYI DEFTERE YAZAR: K5'in "root:root"
#: hükmü sahte kökte ancak çağrının kendisiyle ölçülebilir (dosya sahipliği değişmez).
_SUDO_SIM = ('#!/bin/sh\ncase "$1" in\n'
             '  chown) if [ -n "$SAHTE_SUDO_DEFTERI" ]; then\n'
             '           printf "%s\\n" "$*" >> "$SAHTE_SUDO_DEFTERI"; fi\n'
             '         exit 0 ;;\n'
             '  *) exec "$@" ;;\nesac\n')


def _systemctl_sim(servis: str) -> str:
    """`systemctl` şimi. `servis="dusuk"` ise `is-active` DÜŞER — faz-2'nin negatif kontrol
    penceresinde (iki kanal da SAHTEYKEN) servisin açılmaması hâli K7'nin trap çivisidir."""
    dusuk = '  is-active*) exit 3 ;;\n' if servis == "dusuk" else ""
    return ('#!/bin/sh\ncase "$*" in\n'
            '  "--version") echo "systemd 255 (255.4-1ubuntu8.4)"; exit 0 ;;\n'
            f'{dusuk}'
            '  *) exit 0 ;;\nesac\n')


#: Şimin İÇİNDEKİ çözüm sırası MOTORUN sözleşmesidir (`secrets._fetch`): credential kanalı ÖNCE,
#: boşsa ortam. `credential_oku` boş dosyaya None der (v439 A4) — şim de öyle davranır.
_COZ_FN = (
    '_coz() {\n'
    '  D=""\n'
    '  if [ -f "$2" ]; then D=$(cat "$2" 2>/dev/null | tr -d " \\t\\r\\n"); fi\n'
    '  if [ -z "$D" ]; then D=$(_envd "$1"); fi\n'
    '  printf "%s" "$D"\n'
    '}\n'
    '_envd() { sed -n "s/^$1=//p" "$SIR_GECIS_KOK/opt/meridian/.env" 2>/dev/null '
    '| head -1 | tr -d " \\t\\r\\n"; }\n'
    '_ok() { printf \'{"ok": true}\\n\'; }\n'
    '_yok() { printf \'{"ok": false}\\n\'; }\n'
    'NK="$SIR_GECIS_KOK/etc/meridian/nous_api_key"\n'
    'KK="$SIR_GECIS_KOK/etc/meridian/kapi_apikey"\n'
)

_KANIT_GOVDESI = {
    # Kanıt anahtardan BAĞIMSIZ — olaydaki sahte geçişin ta kendisi.
    "hep_ok": '_ok',
    # Motorun sözleşmesi: NOUS anahtarı credential'dan, yoksa ortamdan.
    "anahtar": 'if [ -n "$SAHTE_GERCEK" ] && [ "$(_coz NOUS_API_KEY "$NK")" = "$SAHTE_GERCEK" ];'
               ' then _ok; else _yok; fi',
    # Faz-2'nin ASIL hükmü: uygulama HÂLÂ ortam kanalını okuyorsa credential'daki gerçek değer
    # kanıtı kurtarmaz — betik durmalı ve iki kanalı da gerçek bırakmalıdır (K7).
    "ortam": 'if [ -n "$SAHTE_GERCEK" ] && [ "$(_envd NOUS_API_KEY)" = "$SAHTE_GERCEK" ];'
             ' then _ok; else _yok; fi',
    # `--faz2 KAPI_APIKEY` yolu: kanıt ucu APISIX'ten geçer, yani KAPI anahtarı da yanlışsa
    # (kapı kilidi yürürlükteyken) 401 döner ve kanıt YOK olur.
    "iki_anahtar": 'if [ "$(_coz NOUS_API_KEY "$NK")" = "$SAHTE_GERCEK" ] &&'
                   ' [ "$(_coz KAPI_APIKEY "$KK")" = "$SAHTE_GERCEK_KAPI" ];'
                   ' then _ok; else _yok; fi',
}


def _curl_sim(kip: str, dokum: pathlib.Path, kilit: str = "401") -> str:
    """`curl` şimi. ÜÇ çağrı yeri ayrılır: `-K <cfg>` → `_kanit_nous` (gövde döner),
    `apikey:` başlıklı → `_kapi_kilidi_olc` (`kilit` kodu), kalanı → `_servis_ayakta` (200).

    `-K` dalı cfg dosyasını `dokum`a KOPYALAR: `_kanit_nous` cfg'yi hemen siler, oysa B6'nın
    ölçtüğü şey tam olarak o dosyanın İÇERİĞİDİR (token kaçışı).

    `kilit="200"` kapı key-auth kilidinin YÜRÜRLÜKTE OLMADIĞI hâldir: yanlış apikey ile de 200
    gelir, yani "motor çalışıyor" hangi kanalın okunduğunu KANITLAMAZ (K7)."""
    return ('#!/bin/sh\n'
            f'{_COZ_FN}'
            'case "$*" in\n'
            '  "-K "*)\n'
            f'    cat "$2" > "{dokum}" 2>/dev/null\n'
            f'    {_KANIT_GOVDESI[kip]} ;;\n'
            f'  *apikey:*) echo {kilit} ;;\n'
            '  *) echo 200 ;;\nesac\n')


def _sahte_ortam(tmp_path: pathlib.Path, *, curl_kip: str | None = None,
                 damga: str | None = None, gercek: str = "", gercek_kapi: str = "",
                 kilit: str = "401", servis: str = "ayakta") -> tuple[pathlib.Path, dict]:
    """Betiğin dokunduğu üç kökü tmp'de kurar ve dış komutları şimler (v439 G bölümü deseni).

    `damga` verilirse `date` de şimlenir: "aynı saniyede iki çağrı" senaryosu (B3) hıza değil
    ÖLÇÜLEBİLİR bir sabite bağlanır — yarış koşuluyla ölçülen çivi bazen yeşil olur."""
    kok = tmp_path / "kok"
    (kok / "etc/systemd/system/meridian.service.d").mkdir(parents=True)
    (kok / "etc/meridian").mkdir(parents=True)
    (kok / "opt/meridian").mkdir(parents=True)
    binn = tmp_path / "bin"
    binn.mkdir()
    (binn / "sudo").write_text(_SUDO_SIM)
    (binn / "systemctl").write_text(_systemctl_sim(servis))
    if curl_kip:
        (binn / "curl").write_text(_curl_sim(curl_kip, tmp_path / "kanit-cfg.txt", kilit))
    else:
        (binn / "curl").write_text("#!/bin/sh\necho 200\n")
    simler = ["sudo", "systemctl", "curl"]
    if damga:
        (binn / "date").write_text(f'#!/bin/sh\nprintf "%s\\n" "{damga}"\n')
        simler.append("date")
    for f in simler:
        (binn / f).chmod(0o755)
    ortam = dict(os.environ, PATH=f"{binn}:{os.environ['PATH']}",
                 SIR_GECIS_KOK=str(kok), SAHTE_GERCEK=gercek, SAHTE_GERCEK_KAPI=gercek_kapi,
                 SAHTE_SUDO_DEFTERI=str(tmp_path / "sudo-defteri.txt"))
    return kok, ortam


def _kos(tmp_path: pathlib.Path, ortam: dict, *arg: str,
         girdi: str = "") -> subprocess.CompletedProcess:
    return subprocess.run(["bash", str(BETIK), *arg], capture_output=True, text=True,
                          env=ortam, cwd=str(tmp_path), input=girdi)


def _agac(kok: pathlib.Path) -> set[str]:
    return {str(p.relative_to(kok)) for p in kok.rglob("*")}


# =================================================================================================
# B1) `_deger_dosyala` ADI ARAR — dosyanın 1. satırını DEĞİL
# =================================================================================================

def test_B1_faz1_bos_girdide_ENVDEN_DOGRU_satiri_tasir(tmp_path):
    """OLAYIN KÖKÜ. `.env` çok satırlıdır ve hedef değişken 1. satırda DEĞİLDİR; eski kod
    `sed -n "1{s/^${ad}=//;p;}"` ile HER ZAMAN 1. satırı basıyordu. Burada hedef 3. satırdadır:
    credential kaynağına da `.env`e de TAM O DEĞER yazılmalı ve 1. satırın değeri (dash token)
    HİÇBİR yere sızmamalı — sızsaydı bir sır ikinci bir ad altında ikinci kez saklanırdı."""
    kok, ortam = _sahte_ortam(tmp_path)
    envf = kok / "opt/meridian/.env"
    envf.write_text(ENV_COK_SATIR, encoding="utf-8")

    r = _kos(tmp_path, ortam, "--faz1", "NOUS_API_KEY")
    assert r.returncode == 0, r.stdout + r.stderr

    kred = kok / "etc/meridian/nous_api_key"
    assert kred.exists(), "credential kaynağı yazılmadı: " + r.stdout + r.stderr
    assert kred.read_text(encoding="utf-8").strip() == NOUS_SAHTE, "YANLIŞ değer taşındı"
    assert DASH_SAHTE not in kred.read_text(encoding="utf-8"), ".env'in 1. satırı SIZDI"

    icerik = envf.read_text(encoding="utf-8")
    assert f"NOUS_API_KEY={NOUS_SAHTE}\n" in icerik, icerik
    assert icerik.count("NOUS_API_KEY=") == 1, icerik
    assert f"MERIDIAN_DASH_TOKEN={DASH_SAHTE}\n" in icerik, "komşu satır yendi"
    assert f"KAPI_APIKEY={KAPI_SAHTE}\n" in icerik, "öteki sırrın satırı yendi"
    assert NOUS_SAHTE not in (r.stdout + r.stderr), "SIR DEĞERİ basıldı"


def test_B1b_faz1_ikinci_ad_da_KENDI_satirini_alir(tmp_path):
    """Aynı hata KAPI_APIKEY için de vardı ve olayda İKİ sır birden düştü. 1. satırla eşleşen
    tesadüf tek adı kurtarır, ötekini kurtarmaz — iki adı da ayrı ayrı ölçmek gerekir."""
    kok, ortam = _sahte_ortam(tmp_path)
    envf = kok / "opt/meridian/.env"
    envf.write_text(ENV_COK_SATIR, encoding="utf-8")

    r = _kos(tmp_path, ortam, "--faz1", "KAPI_APIKEY")
    assert r.returncode == 0, r.stdout + r.stderr
    kred = kok / "etc/meridian/kapi_apikey"
    assert kred.read_text(encoding="utf-8").strip() == KAPI_SAHTE
    assert DASH_SAHTE not in kred.read_text(encoding="utf-8")


def test_B1d_IKI_ad_da_faz1den_gecince_dropin_KURULUR(tmp_path):
    """OPS ARACI TESLİM KAPISI (§6): aracı operatörün koşacağı BİÇİMDE bir kez koştur. Bakım
    penceresinin gerçek dizisi `--faz1 NOUS_API_KEY` + `--faz1 KAPI_APIKEY`tir; drop-in ancak İKİ
    kaynak da hazırken kurulur (kaynağı olmayan `LoadCredential=` birimi HİÇ açtırmaz). Bugüne
    kadar bu dizinin tamamı hiç koşturulmadı — 2026-09-07'de canlıda ilk kez koştu."""
    kok, ortam = _sahte_ortam(tmp_path)
    envf = kok / "opt/meridian/.env"
    envf.write_text(ENV_COK_SATIR, encoding="utf-8")
    dropin = kok / "etc/systemd/system/meridian.service.d/53-nous-kapi-credential.conf"

    r1 = _kos(tmp_path, ortam, "--faz1", "NOUS_API_KEY")
    assert r1.returncode == 0, r1.stdout + r1.stderr
    assert not dropin.exists(), "tek kaynak hazırken drop-in KURULDU (birim açılmazdı)"

    r2 = _kos(tmp_path, ortam, "--faz1", "KAPI_APIKEY")
    assert r2.returncode == 0, r2.stdout + r2.stderr
    assert dropin.exists(), "iki kaynak da hazırken drop-in kurulmadı: " + r2.stdout + r2.stderr
    assert dropin.read_text(encoding="utf-8") == DROPIN.read_text(encoding="utf-8")

    assert (kok / "etc/meridian/nous_api_key").read_text(encoding="utf-8").strip() == NOUS_SAHTE
    assert (kok / "etc/meridian/kapi_apikey").read_text(encoding="utf-8").strip() == KAPI_SAHTE
    icerik = envf.read_text(encoding="utf-8")
    assert f"NOUS_API_KEY={NOUS_SAHTE}\n" in icerik and f"KAPI_APIKEY={KAPI_SAHTE}\n" in icerik
    for gizli in (NOUS_SAHTE, KAPI_SAHTE, DASH_SAHTE):
        assert gizli not in (r1.stdout + r1.stderr + r2.stdout + r2.stderr), "SIR DEĞERİ basıldı"


def test_B1c_geri_al_CIPLAK_credential_dosyasini_da_ADLI_bicimi_de_okur(tmp_path):
    """İKİ BİÇİM SÖZLEŞMESİ, `secrets.credential_oku` ile AYNI: credential kaynağı ya çıplak
    değerdir ya da operatörün `.env` alışkanlığıyla `<ad>=<değer>`dir. B1'in düzeltmesi desen
    aramaya geçtiği için ÇIPLAK biçimi düşürme riski doğar — iki biçim de burada ölçülür."""
    for etiket, icerik in (("ciplak", f"{NOUS_SAHTE}\n"),
                           ("adli", f"NOUS_API_KEY={NOUS_SAHTE}\n")):
        kok, ortam = _sahte_ortam(tmp_path / etiket)
        (kok / "etc/meridian/nous_api_key").write_text(icerik, encoding="utf-8")
        envf = kok / "opt/meridian/.env"
        envf.write_text("NOUS_MODEL=sahte-model\n", encoding="utf-8")
        r = _kos(tmp_path, ortam, "--geri-al", "NOUS_API_KEY")
        assert r.returncode == 0, r.stdout + r.stderr
        assert f"NOUS_API_KEY={NOUS_SAHTE}\n" in envf.read_text(encoding="utf-8"), etiket


# =================================================================================================
# B2) BOŞ DEĞER KAPISI — "1 bayt" değer değildir
# =================================================================================================

def test_B2_faz1_bos_deger_HICBIR_YAZIM_yapmadan_DURUR(tmp_path):
    """OLAYIN İKİNCİ YARISI. Canlı `.env`in 1. satırı BOŞTU: eski `sed` "" + `\\n` bastı, `[ -s ]`
    1 baytı DOLU saydı ve betik credential dosyasını da `.env` satırını da BOŞ yazdı. Doğru hüküm:
    boşluk/satır-sonu dışı en az 1 karakter yoksa `die` — ve die'dan önce hiçbir şey yazılmamış
    olmalı (sıfır ile "bilmiyorum" aynı şey değildir; uydurma yasağı)."""
    kok, ortam = _sahte_ortam(tmp_path)
    envf = kok / "opt/meridian/.env"
    olay_env = "\nMERIDIAN_DASH_TOKEN=" + DASH_SAHTE + "\nNOUS_MODEL=sahte-model\n"
    envf.write_text(olay_env, encoding="utf-8")
    once = _agac(kok)

    r = _kos(tmp_path, ortam, "--faz1", "NOUS_API_KEY")

    assert r.returncode != 0, "BOŞ değerle faz1 GEÇTİ: " + r.stdout + r.stderr
    assert envf.read_text(encoding="utf-8") == olay_env, ".env DEĞİŞTİ (die'dan önce yazım)"
    assert not (kok / "etc/meridian/nous_api_key").exists(), "BOŞ credential dosyası yazıldı"
    assert _agac(kok) == once, f"kök ağacı değişti: {_agac(kok) - once}"


def test_B2b_faz1_YALNIZ_BOSLUK_karakteri_girilse_de_REDDEDILIR(tmp_path):
    """Aynı kapı öteki uçta. `read -r` IFS boşluğunu kırpar, ama `\\r`yi KIRPMAZ: Windows/terminal
    panosundan yapıştırılan bir satır sonu `_girilen`i "dolu" yapar, `printf` onu `$tmp`ye yazar
    ve eski `[ -s ]` kapısı 2 baytı DEĞER sayardı — credential kaynağı bir taşıma karakteriyle
    doldurulurdu. Kapı uzunluğu değil, boşluk DIŞI karakteri ölçmeli."""
    kok, ortam = _sahte_ortam(tmp_path)
    (kok / "opt/meridian/.env").write_text(ENV_COK_SATIR, encoding="utf-8")
    r = _kos(tmp_path, ortam, "--faz1", "NOUS_API_KEY", girdi="\r\n")
    assert r.returncode != 0, "boşluk-dışı karakteri olmayan değer KABUL EDİLDİ: " + r.stdout
    assert not (kok / "etc/meridian/nous_api_key").exists()


# =================================================================================================
# B3) YEDEK ADI ÇAKIŞMAZ
# =================================================================================================

def test_B3_ayni_saniyedeki_iki_faz1_IKI_AYRI_yedek_birakir(tmp_path):
    """Olayda NOUS faz-1'in `.env` yedeği KAPI faz-1 tarafından EZİLDİ: ad `$ENVF.bak-%Y%m%d%H%M`
    idi — DAKİKA çözünürlüklü ve ADSIZ. Yedek, geri dönüşün TEK dayanağıdır; ezilen yedek
    "yedek var" yanılsamasından daha kötüdür. `date` şimlenerek iki çağrı AYNI damgaya zorlanır."""
    kok, ortam = _sahte_ortam(tmp_path, damga="20260907T214500Z")
    envf = kok / "opt/meridian/.env"
    envf.write_text(ENV_COK_SATIR, encoding="utf-8")

    r1 = _kos(tmp_path, ortam, "--faz1", "NOUS_API_KEY")
    assert r1.returncode == 0, r1.stdout + r1.stderr
    ara = envf.read_text(encoding="utf-8")
    r2 = _kos(tmp_path, ortam, "--faz1", "NOUS_API_KEY")
    assert r2.returncode == 0, r2.stdout + r2.stderr

    yd = kok / YEDEK_ALT                      # K5: yedekler artık `.env`in YANINDA DEĞİL
    yedekler = sorted(p.name for p in yd.glob(".env.bak-*"))
    assert len(yedekler) == 2, f"yedek EZİLDİ: {yedekler}"
    for ad in yedekler:
        assert re.match(r"^\.env\.bak-NOUS_API_KEY-\d{8}T\d{6}Z(\.\d+)?$", ad), ad
    icerikler = {(yd / ad).read_text(encoding="utf-8") for ad in yedekler}
    assert ENV_COK_SATIR in icerikler, "İLK yedeğin içeriği kayboldu"
    assert ara in icerikler, "İKİNCİ yedek ilkinin kopyası — durum kaydedilmemiş"


# =================================================================================================
# B4) FAZ-2 NEGATİF KONTROL — kanıt ANAHTARA bağlı mı?
# =================================================================================================

def _faz2_kok(tmp_path: pathlib.Path, *, curl_kip: str, kred_icerik: str,
              gercek: str, kapi_kred_icerik: str | None = None,
              env_metni: str | None = None,
              **kw) -> tuple[pathlib.Path, dict, pathlib.Path]:
    """Faz-2'nin ön koşullarını kurar: drop-in KURULU, credential kaynağı VAR, `.env`te iki sır
    da duruyor, pano token'ı okunabilir (`_kanit_nous` cfg'yi onunla yazar).

    `kapi_kred_icerik` verilirse KAPI kaynağı da yazılır (`--faz2 KAPI_APIKEY` yolu, K7);
    `env_metni` `.env`i tümden değiştirir (uç satırı OLMAYAN `.env` senaryosu)."""
    kok, ortam = _sahte_ortam(tmp_path, curl_kip=curl_kip, gercek=gercek, **kw)
    (kok / "etc/systemd/system/meridian.service.d/53-nous-kapi-credential.conf").write_text(
        DROPIN.read_text(encoding="utf-8"), encoding="utf-8")
    (kok / "etc/meridian/dash_token").write_text(f"{DASH_SAHTE}\n", encoding="utf-8")
    kred = kok / "etc/meridian/nous_api_key"
    kred.write_text(kred_icerik, encoding="utf-8")
    if kapi_kred_icerik is not None:
        (kok / "etc/meridian/kapi_apikey").write_text(kapi_kred_icerik, encoding="utf-8")
    envf = kok / "opt/meridian/.env"
    envf.write_text(ENV_COK_SATIR if env_metni is None else env_metni, encoding="utf-8")
    return kok, ortam, envf


def test_B4a_faz2_kanit_ANAHTARA_BAGLI_DEGILSE_OLCULEMEDI_der(tmp_path):
    """OLAYDA FAZ-2 SAHTE GEÇTİ. Farksal ölçümün mantığı "sahte ortam + gerçek credential → hâlâ
    OK ⇒ okunan kanal credential'dır"; ama OK'nin ANAHTARA bağlı olduğu hiç ölçülmüyordu — uç
    her koşulda OK derse ölçüm bir tiyatrodur. Negatif kontrol: İKİ kanal da sahteyken kanıt YOK
    gelmeli. OK gelirse ölçüm YAPILAMAMIŞTIR ve betik durur (uydurma yasağı) — ortam satırı
    SİLİNMEZ, iki kanal da olduğu gibi kalır."""
    kok, ortam, envf = _faz2_kok(tmp_path, curl_kip="hep_ok",
                                 kred_icerik=f"{NOUS_SAHTE}\n", gercek=NOUS_SAHTE)
    r = _kos(tmp_path, ortam, "--faz2", "NOUS_API_KEY")

    assert r.returncode != 0, "kanıt anahtardan bağımsızken faz2 GEÇTİ: " + r.stdout + r.stderr
    cikti = r.stdout + r.stderr
    assert "ÖLÇÜLEMEDİ" in cikti, cikti
    assert f"NOUS_API_KEY={NOUS_SAHTE}\n" in envf.read_text(encoding="utf-8"), \
        "ortam satırı ölçülemeyen bir kanıtla KAPATILDI"
    assert (kok / "etc/meridian/nous_api_key").read_text(encoding="utf-8").strip() == NOUS_SAHTE, \
        "negatif kontrolün sahte değeri credential kaynağında KALDI"
    assert NOUS_SAHTE not in cikti, "SIR DEĞERİ basıldı"


def test_B4b_faz2_kanit_ANAHTARA_BAGLIYSA_gecer(tmp_path):
    """POZİTİF KONTROL (kill-list'in öteki ucu): negatif kontrol eklenince mutlu yol da ölçülmeli,
    yoksa "hep durduran" bir kapı da bu çiviyi yeşil bırakırdı. Kanıt anahtara bağlıyken faz-2
    tamamlanır: ortam satırı gider, credential kaynağı ve komşu satırlar durur."""
    kok, ortam, envf = _faz2_kok(tmp_path, curl_kip="anahtar",
                                 kred_icerik=f"{NOUS_SAHTE}\n", gercek=NOUS_SAHTE)
    r = _kos(tmp_path, ortam, "--faz2", "NOUS_API_KEY")

    assert r.returncode == 0, r.stdout + r.stderr
    icerik = envf.read_text(encoding="utf-8")
    assert "NOUS_API_KEY=" not in icerik, icerik
    assert f"KAPI_APIKEY={KAPI_SAHTE}\n" in icerik, "öteki sırrın satırı yendi"
    assert "NOUS_MODEL=sahte-model\n" in icerik, "yapılandırma satırı yendi"
    assert (kok / "etc/meridian/nous_api_key").read_text(encoding="utf-8").strip() == NOUS_SAHTE, \
        "ölçüm sahte değeri credential kaynağında BIRAKTI"
    assert NOUS_SAHTE not in (r.stdout + r.stderr), "SIR DEĞERİ basıldı"


def test_B4c_faz2_BOS_credential_kaynagini_OLCUMDEN_ONCE_reddeder(tmp_path):
    """`sudo test -s "$kred"` 1 baytlık "\\n"i DOLU saydı — olayda credential dosyaları tam olarak
    o hâldeydi. Faz-2 bu hâlde ortam satırını silerse sır HİÇBİR kanaldan okunamaz. Kapı ölçümden
    ÖNCE düşmeli: restart'lı farksal ölçüme hiç girilmez."""
    kok, ortam, envf = _faz2_kok(tmp_path, curl_kip="anahtar",
                                 kred_icerik="\n", gercek=NOUS_SAHTE)
    r = _kos(tmp_path, ortam, "--faz2", "NOUS_API_KEY")
    cikti = r.stdout + r.stderr

    assert r.returncode != 0, cikti
    assert "boş" in cikti.lower() or "BOŞ" in cikti, cikti
    assert "farksal ölçüm" not in cikti, "BOŞ kaynakla farksal ölçüme GİRİLDİ: " + cikti
    assert f"NOUS_API_KEY={NOUS_SAHTE}\n" in envf.read_text(encoding="utf-8")


# =================================================================================================
# B5) GERİ ALMA — paylaşılan drop-in, iki sır
# =================================================================================================

def test_B5_geri_al_dropini_kaldirmadan_HER_adin_satirini_geri_yazar(tmp_path):
    """Drop-in İKİ adı birden taşır; tek ad için `--geri-al` onu kaldırınca ÖTEKİ sır credential
    kanalını da kaybeder — ve faz-2 sonrası onun `.env` satırı zaten yoktur. Sonuç: `secrets.get`
    None döner, `hermes._nous_headers` sessizce kırılır ve `_servis_ayakta` (kimlik doğrulaması
    İSTEMEYEN /healthz) bunu göremez. Geri alma DROP-IN kadar GENİŞ olmalı."""
    kok, ortam = _sahte_ortam(tmp_path)
    birim = kok / "etc/systemd/system/meridian.service.d"
    (birim / "53-nous-kapi-credential.conf").write_text(
        DROPIN.read_text(encoding="utf-8"), encoding="utf-8")
    (kok / "etc/meridian/nous_api_key").write_text(f"{NOUS_SAHTE}\n", encoding="utf-8")
    (kok / "etc/meridian/kapi_apikey").write_text(f"{KAPI_SAHTE}\n", encoding="utf-8")
    envf = kok / "opt/meridian/.env"
    envf.write_text("NOUS_MODEL=sahte-model\n", encoding="utf-8")   # faz-2 İKİ satırı da sildi

    r = _kos(tmp_path, ortam, "--geri-al", "NOUS_API_KEY")
    assert r.returncode == 0, r.stdout + r.stderr

    icerik = envf.read_text(encoding="utf-8")
    assert f"NOUS_API_KEY={NOUS_SAHTE}\n" in icerik, icerik
    assert f"KAPI_APIKEY={KAPI_SAHTE}\n" in icerik, "ÖTEKİ sır kanalsız bırakıldı: " + icerik
    assert "NOUS_MODEL=sahte-model\n" in icerik
    assert not (birim / "53-nous-kapi-credential.conf").exists(), "drop-in kaldırılmadı"
    assert "geri yazılan ad sayısı: 2" in r.stdout, "sayım raporlanmadı: " + r.stdout
    for gizli in (NOUS_SAHTE, KAPI_SAHTE):
        assert gizli not in (r.stdout + r.stderr), "SIR DEĞERİ basıldı"


def test_B5b_geri_al_KAYNAGI_OLMAYAN_adi_UYDURMAZ(tmp_path):
    """Genişleyen geri alma, credential kaynağı OLMAYAN ad için satır UYDURMAMALI: kaynağı yoksa
    değer bilinmiyordur ve boş bir `<ad>=` satırı "ayarlı ama değersiz" yalanını üretirdi."""
    kok, ortam = _sahte_ortam(tmp_path)
    birim = kok / "etc/systemd/system/meridian.service.d"
    (birim / "53-nous-kapi-credential.conf").write_text(
        DROPIN.read_text(encoding="utf-8"), encoding="utf-8")
    (kok / "etc/meridian/nous_api_key").write_text(f"{NOUS_SAHTE}\n", encoding="utf-8")
    envf = kok / "opt/meridian/.env"
    envf.write_text("NOUS_MODEL=sahte-model\n", encoding="utf-8")

    r = _kos(tmp_path, ortam, "--geri-al", "NOUS_API_KEY")
    assert r.returncode == 0, r.stdout + r.stderr
    icerik = envf.read_text(encoding="utf-8")
    assert f"NOUS_API_KEY={NOUS_SAHTE}\n" in icerik
    assert "KAPI_APIKEY=" not in icerik, "kaynaksız ad için BOŞ satır uyduruldu: " + icerik


# =================================================================================================
# B6) SERTLEŞTİRMELER
# =================================================================================================

def test_B6a_kanit_config_TOKENDEKI_TIRNAK_ve_TERS_BOLU_kacirir(tmp_path):
    """`curl -K` config grameri `"` ile sınırlı dizge kullanır ve `\\` bir KAÇIŞTIR. Kaçırılmamış
    bir token satırı bozar: başlık ya yanlış gider ya da curl config'i reddeder — ve arıza
    "anahtar yanlış" gibi görünür (ölçüm yanlış yerde aranır). Kaçış cfg'nin İÇİNDE ölçülür:
    metin taraması "kaçırıyor gibi görünen" bir kodu da yeşil bırakırdı."""
    kok, ortam, _ = _faz2_kok(tmp_path, curl_kip="anahtar",
                              kred_icerik=f"{NOUS_SAHTE}\n", gercek=NOUS_SAHTE)
    (kok / "etc/meridian/dash_token").write_text(
        'MERIDIAN_DASH_TOKEN=ab"cd\\ef\n', encoding="utf-8")

    _kos(tmp_path, ortam, "--faz2", "NOUS_API_KEY")

    cfg = tmp_path / "kanit-cfg.txt"
    assert cfg.exists(), "_kanit_nous hiç çağrılmadı"
    metin = cfg.read_text(encoding="utf-8")
    assert 'header = "x-meridian-token: ab\\"cd\\\\ef"' in metin, metin


def test_B6b_TEST_KOKU_doluyken_BUYUK_uyari_basar(tmp_path):
    """`SIR_GECIS_KOK` bir ÇİVİ kancasıdır: üretimde yanlışlıkla ayarlıysa betik gerçek yollara
    HİÇ dokunmadan "başarılı" raporlar ve operatör geçişi yaptığını sanır. Kanca görünür olmalı."""
    kok, ortam = _sahte_ortam(tmp_path)
    r = _kos(tmp_path, ortam)
    assert r.returncode == 0, r.stdout + r.stderr
    cikti = r.stdout + r.stderr
    assert "TEST KÖKÜ AKTİF" in cikti, cikti
    assert str(kok) in cikti, cikti


def test_B6c_TEST_KOKU_BOSKEN_uyari_YOK(tmp_path):
    """BEDEL ÖLÇÜMÜ (§4): uyarının kazancı ölçüldü, bedeli de ölçülür — üretimde (kanca boşken)
    bu satır HİÇ basılmamalı, yoksa her operatör koşumu bir yalan uyarıyla açılırdı.
    `durum` salt-okunurdur; systemctl/curl şimli olduğu için bu koşum ağa/servise dokunmaz."""
    _, ortam = _sahte_ortam(tmp_path)
    ortam["SIR_GECIS_KOK"] = ""
    r = _kos(tmp_path, ortam)
    assert "TEST KÖKÜ AKTİF" not in (r.stdout + r.stderr), r.stdout + r.stderr


def test_B6d_betik_sozdizimi_gecerli():
    """`bash -n` — düzeltmeden sonraki en ucuz kapı (v439 G0'ın bu dosyadaki kardeşi): betik A1'de
    bakım penceresinde koşar, sözdizimi hatası orada bulunursa pencere yanar."""
    r = subprocess.run(["bash", "-n", str(BETIK)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


@pytest.mark.parametrize("kalip", ['1{s/^${ad}=//;p;}', '$ENVF.bak-$(date -u +%Y%m%d%H%M)'])
def test_B6e_OLAYIN_kaliplari_betikte_KALMADI(kalip):
    """AYRIŞMA ÇİVİSİ: iki kalıp da olayın doğrudan sebebiydi. Davranış çivileri (B1/B3) esas
    hükümdür; bu çivi kalıbın bir rebase/geri-alma ile sessizce geri gelmesini yakalar."""
    assert kalip not in BETIK.read_text(encoding="utf-8"), f"olay kalıbı geri geldi: {kalip}"


# =================================================================================================
# TUR 2 — B1..B6'nın açtığı yeni yüzeyler (çekişmeli inceleme, 2026-09-08)
# =================================================================================================
#: Kesintiye uğramış bir ölçüm turunun diskte BIRAKTIĞI tek gerçek-değer kopyası.
KURTARMA_NOUS = "SAHTE-KURTARMA-DEGERI-9"


def _kalinti_birak(kok: pathlib.Path, envf: pathlib.Path) -> tuple[pathlib.Path, pathlib.Path]:
    """SIGKILL'lenmiş bir faz-2'nin bıraktığı hâli kurar: iki kanal da SAHTE, gerçek değerin
    diskteki TEK kopyası iki `.olcum-yedek` dosyasıdır (betiğin journal'a yazdığı kurtarma yolu)."""
    kred = kok / "etc/meridian/nous_api_key"
    kred.write_text("sahte-deadbeefdeadbeef\n", encoding="utf-8")
    envf.write_text(ENV_COK_SATIR.replace(NOUS_SAHTE, "sahte-deadbeefdeadbeef"), encoding="utf-8")
    ky = kok / "etc/meridian/nous_api_key.olcum-yedek"
    ky.write_text(f"{KURTARMA_NOUS}\n", encoding="utf-8")
    ey = envf.parent / ".env.olcum-yedek"
    ey.write_text(ENV_COK_SATIR.replace(NOUS_SAHTE, KURTARMA_NOUS), encoding="utf-8")
    return ky, ey


# =================================================================================================
# K1) YARIDA KALMIŞ ÖLÇÜM TURU — `.olcum-yedek` SİLİNMEZ, ÇIKIŞ 2
# =================================================================================================

def test_K1a_faz2_KALINTI_yedekleri_SILMEZ_ve_CIKIS_2_ile_durur(tmp_path):
    """EN YÜKSEK KÖK (5 bağımsız inceleme). Negatif kontrol iki kanalı da sahteye çeker; süreç o
    pencerede SIGKILL alırsa gerçek değerin diskteki TEK kopyası `.olcum-yedek`lerdir — betiğin
    KENDİ journal satırı da kurtarma yolu olarak onları gösterir. Eski kod faz-2'nin ilk işi
    olarak o iki dosyayı `rm -f` ediyordu: operatörün "aynı komutu bir daha koş" refleksi sırrı
    diskten TÜMÜYLE siliyordu. Hüküm: silme, DUR — ve kurtarma komutlarını bas. Çıkış 2, çünkü
    bu hâl "geçiş başarısız" (1) değil, "önce elle kurtar"dır."""
    kok, ortam, envf = _faz2_kok(tmp_path, curl_kip="anahtar",
                                 kred_icerik=f"{NOUS_SAHTE}\n", gercek=NOUS_SAHTE)
    ky, ey = _kalinti_birak(kok, envf)
    once = (_agac(kok), envf.read_text(encoding="utf-8"),
            ky.read_text(encoding="utf-8"), ey.read_text(encoding="utf-8"))

    r = _kos(tmp_path, ortam, "--faz2", "NOUS_API_KEY")
    cikti = r.stdout + r.stderr

    assert r.returncode == 2, f"çıkış kodu {r.returncode} (2 bekleniyordu): {cikti}"
    assert ky.exists() and ey.exists(), "KURTARMA KOPYALARI SİLİNDİ: " + cikti
    assert (_agac(kok), envf.read_text(encoding="utf-8"),
            ky.read_text(encoding="utf-8"), ey.read_text(encoding="utf-8")) == once, \
        "kalıntı varken faz-2 diske YAZDI"
    assert f'sudo mv -f "{ey}" "{envf}"' in cikti, cikti
    assert f'sudo mv -f "{ky}" "{kok / "etc/meridian/nous_api_key"}"' in cikti, cikti
    assert KURTARMA_NOUS not in cikti, "SIR DEĞERİ basıldı"


def test_K1b_geri_al_da_KALINTI_varken_HICBIR_SEY_yapmaz(tmp_path):
    """AYNI KAPI GERİ ALMADA. Kesinti sonrası refleks komut `--geri-al`dır; o hâlde `.env` ve
    credential kaynağı ölçümün SAHTE değerini taşır ve genişleyen geri alma o sahte değeri
    "gerçek" diye `.env`e yazardı (üstelik ✓ raporlayarak). Kurtarma kopyaları dururken tek
    doğru davranış hiçbir şey yapmamaktır."""
    kok, ortam, envf = _faz2_kok(tmp_path, curl_kip="anahtar",
                                 kred_icerik=f"{NOUS_SAHTE}\n", gercek=NOUS_SAHTE)
    ky, ey = _kalinti_birak(kok, envf)
    dropin = kok / "etc/systemd/system/meridian.service.d/53-nous-kapi-credential.conf"
    once = _agac(kok)

    r = _kos(tmp_path, ortam, "--geri-al", "NOUS_API_KEY")
    cikti = r.stdout + r.stderr

    assert r.returncode == 2, f"çıkış kodu {r.returncode}: {cikti}"
    assert dropin.exists(), "kalıntı varken drop-in KALDIRILDI"
    assert _agac(kok) == once, f"kalıntı varken geri alma diske yazdı: {_agac(kok) ^ once}"
    assert ky.exists() and ey.exists()


def test_K1c_KURTARMADAN_SONRA_faz2_normal_calisir(tmp_path):
    """KAPININ ÖTEKİ UCU (kill-list). "Her hâlde dur" diyen bir kapı da K1a/K1b'yi yeşil bırakır;
    ölçülmesi gereken şey kapının operatörün YOLUNU AÇIK bıraktığıdır. Burada betiğin BASTIĞI
    kurtarma komutları uygulanır (iki `mv`) ve aynı komut ikinci kez koşulduğunda faz-2 sonuna
    kadar gider — yani gerçek değer geri gelmiş, kalıntı tüketilmiştir."""
    kok, ortam, envf = _faz2_kok(tmp_path, curl_kip="anahtar",
                                 kred_icerik=f"{NOUS_SAHTE}\n", gercek=KURTARMA_NOUS)
    ky, ey = _kalinti_birak(kok, envf)
    kred = kok / "etc/meridian/nous_api_key"

    assert _kos(tmp_path, ortam, "--faz2", "NOUS_API_KEY").returncode == 2

    ky.replace(kred)                                  # betiğin bastığı: sudo mv -f <yedek> <asıl>
    ey.replace(envf)

    r = _kos(tmp_path, ortam, "--faz2", "NOUS_API_KEY")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "NOUS_API_KEY=" not in envf.read_text(encoding="utf-8"), envf.read_text(encoding="utf-8")
    assert kred.read_text(encoding="utf-8").strip() == KURTARMA_NOUS
    assert KURTARMA_NOUS not in (r.stdout + r.stderr), "SIR DEĞERİ basıldı"


# =================================================================================================
# K2) GERİ ALMA — yedek, "satır yerinde", ve `$ad` yazılamazsa DROP-IN DURUR
# =================================================================================================

def test_K2a_geri_al_BASTA_yedek_alir(tmp_path):
    """Geri alma `.env`i DEĞİŞTİREN bir yoldur ve tur-1'de tek yedeksiz yazım yolu buydu:
    yanlış bir geri alma sonrası dönülecek hiçbir nokta yoktu. `_env_yedekle` faz-1/faz-2 ile
    aynı sözleşmeyi taşır (ad + saniye damgası, ezmez)."""
    kok, ortam = _sahte_ortam(tmp_path)
    birim = kok / "etc/systemd/system/meridian.service.d"
    (birim / "53-nous-kapi-credential.conf").write_text(
        DROPIN.read_text(encoding="utf-8"), encoding="utf-8")
    (kok / "etc/meridian/nous_api_key").write_text(f"{NOUS_SAHTE}\n", encoding="utf-8")
    (kok / "etc/meridian/kapi_apikey").write_text(f"{KAPI_SAHTE}\n", encoding="utf-8")
    envf = kok / "opt/meridian/.env"
    once = "NOUS_MODEL=sahte-model\n"
    envf.write_text(once, encoding="utf-8")

    r = _kos(tmp_path, ortam, "--geri-al", "NOUS_API_KEY")
    assert r.returncode == 0, r.stdout + r.stderr

    yedekler = sorted((kok / YEDEK_ALT).glob(".env.bak-gerial-NOUS_API_KEY-*"))
    assert len(yedekler) == 1, f"geri alma yedeksiz yazdı: {sorted((kok / YEDEK_ALT).iterdir())}"
    assert yedekler[0].read_text(encoding="utf-8") == once, "yedek geri almadan SONRA alınmış"


def test_K2b_geri_al_OTEKI_adin_YERINDE_duran_satirini_EZMEZ(tmp_path):
    """BAYAT DEĞERLE EZME. Genişleyen geri alma (B5) öteki adın satırını da yazıyordu — ama
    credential kaynağı ROTASYON sonrası BAYAT olabilir: operatör `.env`teki taze KAPI değerini
    kaybeder ve kayıp SESSİZDİR (`/healthz` kimlik doğrulamaz). Satır YERİNDEYSE dokunulmaz;
    yazım yalnız satırın OLMADIĞI (faz-2'yi geçmiş) ad için yapılır."""
    kok, ortam = _sahte_ortam(tmp_path)
    birim = kok / "etc/systemd/system/meridian.service.d"
    (birim / "53-nous-kapi-credential.conf").write_text(
        DROPIN.read_text(encoding="utf-8"), encoding="utf-8")
    (kok / "etc/meridian/nous_api_key").write_text(f"{NOUS_SAHTE}\n", encoding="utf-8")
    (kok / "etc/meridian/kapi_apikey").write_text("SAHTE-KAPI-BAYAT-ESKI\n", encoding="utf-8")
    envf = kok / "opt/meridian/.env"
    envf.write_text(f"NOUS_MODEL=sahte-model\nKAPI_APIKEY={KAPI_SAHTE}\n", encoding="utf-8")

    r = _kos(tmp_path, ortam, "--geri-al", "NOUS_API_KEY")
    assert r.returncode == 0, r.stdout + r.stderr
    icerik = envf.read_text(encoding="utf-8")
    assert f"KAPI_APIKEY={KAPI_SAHTE}\n" in icerik, "TAZE ortam satırı bayat değerle EZİLDİ"
    assert "SAHTE-KAPI-BAYAT-ESKI" not in icerik, icerik
    assert f"NOUS_API_KEY={NOUS_SAHTE}\n" in icerik, "asıl adın satırı geri yazılmadı"
    assert "satır yerinde" in r.stdout, "dokunulmayan ad raporlanmadı: " + r.stdout


def test_K2c_geri_al_ADIN_satirini_yazamazsa_DROPINI_KALDIRMAZ(tmp_path):
    """SESSİZ TAM KAYIP. Kaynağı boş olan ad için satır yazılamaz (uydurma yasağı, B5b) — ama
    tur-1'de betik yine de drop-in'i kaldırıp ✓ + RC 0 dönüyordu: credential kanalı da kapanır,
    sır HİÇBİR kanaldan okunamaz ve `_servis_ayakta` bunu göremez. Drop-in ancak `$ad` gerçekten
    geri yazıldıysa kaldırılır; aksi hâlde operatör yedekten elle yükler."""
    kok, ortam = _sahte_ortam(tmp_path)
    birim = kok / "etc/systemd/system/meridian.service.d"
    dropin = birim / "53-nous-kapi-credential.conf"
    dropin.write_text(DROPIN.read_text(encoding="utf-8"), encoding="utf-8")
    (kok / "etc/meridian/nous_api_key").write_text("\n", encoding="utf-8")     # 1 bayt = BOŞ
    (kok / "etc/meridian/kapi_apikey").write_text(f"{KAPI_SAHTE}\n", encoding="utf-8")
    envf = kok / "opt/meridian/.env"
    envf.write_text("NOUS_MODEL=sahte-model\n", encoding="utf-8")

    r = _kos(tmp_path, ortam, "--geri-al", "NOUS_API_KEY")
    cikti = r.stdout + r.stderr

    assert r.returncode != 0, "kanalsız kalan sır için geri alma ✓ dedi: " + cikti
    assert dropin.exists(), "credential kanalı da kapatıldı — sır iki kanaldan da düştü"
    assert "NOUS_API_KEY=" not in envf.read_text(encoding="utf-8"), "boş satır uyduruldu"
    assert str(kok / YEDEK_ALT) in cikti, "elle geri yükleme yolu SÖYLENMEDİ: " + cikti


# =================================================================================================
# K3) `test -s` KALINTILARI — "1 bayt = dolu" hükmü her yüzeyde aynı olmalı
# =================================================================================================

def test_K3a_faz1_OTEKI_kaynak_1_BAYTKEN_dropini_KURMAZ(tmp_path):
    """B2 kapısı yalnız GİRİLEN değeri ölçüyordu; drop-in döngüsü hâlâ `test -s` idi. Öteki adın
    kaynağı 1 baytlık satır sonuysa "iki kanal da canlı" yeşili basılır, oysa o ad credential
    kanalından BOŞ okunur — ve faz-2 sırası geldiğinde ortam satırı silinip sır tümden düşer."""
    kok, ortam = _sahte_ortam(tmp_path)
    (kok / "opt/meridian/.env").write_text(ENV_COK_SATIR, encoding="utf-8")
    (kok / "etc/meridian/kapi_apikey").write_text("\n", encoding="utf-8")
    dropin = kok / "etc/systemd/system/meridian.service.d/53-nous-kapi-credential.conf"

    r = _kos(tmp_path, ortam, "--faz1", "NOUS_API_KEY")
    assert r.returncode == 0, r.stdout + r.stderr
    assert not dropin.exists(), "1 baytlık kaynakla drop-in KURULDU: " + r.stdout
    assert "KAPI_APIKEY" in r.stdout and "eksik" in r.stdout, r.stdout


def test_K3b_durum_1_BAYTLIK_kaynagi_BOS_diye_raporlar(tmp_path):
    """Operatörün koşacağı İLK komut `durum`dur ve olay günü `test -s` orada da 1 baytı DOLU
    saydı: rapor "kaynak hazır" diyordu. Rapor, kapıların ölçtüğü şeyle AYNI şeyi ölçmeli
    (tek-kaynak); boyut da basılır, çünkü "boş" ile "yok" farklı arızalardır."""
    kok, ortam = _sahte_ortam(tmp_path)
    (kok / "etc/meridian/kapi_apikey").write_text("\n", encoding="utf-8")
    r = _kos(tmp_path, ortam)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "BOŞ (1 bayt)" in r.stdout, r.stdout
    assert "YOK" in r.stdout, "hiç olmayan kaynak YOK demeli: " + r.stdout


def test_K3c_faz1_hafiza_1_BAYTLIK_kaynakla_dropini_KURMAZ(tmp_path):
    """MOTORU DÜŞÜREN SINIF (v439 I11'in boş-dosya ucu). `LoadCredential=` kaynağı 1 baytlık
    satır sonuysa birim AÇILIR ama vekil TENANT anahtarını boş okur; daha kötüsü, aynı `test -s`
    kapısı dosyanın gerçekten dolu olduğunu ölçmediği için arıza restart sonrası çıkar."""
    kok, ortam = _sahte_ortam(tmp_path)
    (kok / "etc/hindsight/creds").mkdir(parents=True)
    (kok / "etc/hindsight/creds/HINDSIGHT_API_TENANT_API_KEY").write_text("\n", encoding="utf-8")
    r = _kos(tmp_path, ortam, "--faz1-hafiza")
    assert r.returncode != 0, "1 baytlık kaynakla 54 drop-in KURULDU: " + r.stdout + r.stderr
    assert not (kok / "etc/systemd/system/meridian.service.d"
                      "/54-hafiza-credential.conf").exists()


# =================================================================================================
# K4) ÇİFT `^ad=` SATIRI — systemd SONuncuyu okur, `sed ...;q` İLKİNİ
# =================================================================================================

def test_K4_env_de_CIFT_satir_varsa_faz1_DURUR(tmp_path):
    """`.env` iki `NOUS_API_KEY=` satırı taşıyorsa yürürlükteki değer SONuncudur (EnvironmentFile
    üzerine yazar), oysa `_deger_dosyala` `;q` ile İLKİNİ alır. Bu hâlde faz-1 credential
    kaynağına YÜRÜRLÜKTE OLMAYAN değeri yazar ve faz-2 farksal ölçümü onu "gerçek" sanar. Hangi
    değerin yürürlükte olduğu belirsizken tahmin etmek uydurmadır — betik durur."""
    kok, ortam = _sahte_ortam(tmp_path)
    envf = kok / "opt/meridian/.env"
    ikili = ENV_COK_SATIR + "NOUS_API_KEY=SAHTE-IKINCI-SATIR-7\n"
    envf.write_text(ikili, encoding="utf-8")
    once = _agac(kok)

    r = _kos(tmp_path, ortam, "--faz1", "NOUS_API_KEY")
    cikti = r.stdout + r.stderr

    assert r.returncode != 0, "çift satırla faz-1 GEÇTİ: " + cikti
    assert "ÇİFT SATIR" in cikti, cikti
    assert envf.read_text(encoding="utf-8") == ikili, ".env DEĞİŞTİ"
    assert _agac(kok) == once, f"kök ağacı değişti: {_agac(kok) - once}"
    assert NOUS_SAHTE not in cikti and "SAHTE-IKINCI-SATIR-7" not in cikti, "SIR DEĞERİ basıldı"


# =================================================================================================
# K5) YEDEKLER SERVİS KULLANICISINDAN UZAKTA
# =================================================================================================

def test_K5_env_yedegi_KOK_DIZINDE_0400_ve_ENVIN_YANINDA_DEGIL(tmp_path):
    """`.env.bak-*` `.env` ile aynı dizinde ve `cp -p` ile 0600 `ubuntu:ubuntu` doğuyordu: sır
    faz-2'den SONRA bile (ortam kanalı kapandığı hâlde) servis kullanıcısının okuyabildiği düz
    metin bir kopyada yaşamaya devam ediyordu — geçişin amacını sessizce geri alan bir kalıntı.
    Yedekler 0700 bir kök dizinine, 0400 ve root:root yazılır; yol operatöre BASILIR."""
    kok, ortam = _sahte_ortam(tmp_path)
    envf = kok / "opt/meridian/.env"
    envf.write_text(ENV_COK_SATIR, encoding="utf-8")

    r = _kos(tmp_path, ortam, "--faz1", "NOUS_API_KEY")
    assert r.returncode == 0, r.stdout + r.stderr

    assert not list((kok / "opt/meridian").glob(".env.bak-*")), "yedek hâlâ .env'in YANINDA"
    yd = kok / YEDEK_ALT
    yedekler = sorted(yd.glob(".env.bak-*"))
    assert len(yedekler) == 1, f"yedek yok/çok: {yedekler}"
    assert yedekler[0].read_text(encoding="utf-8") == ENV_COK_SATIR
    assert oct(yd.stat().st_mode & 0o777) == "0o700", oct(yd.stat().st_mode & 0o777)
    assert oct(yedekler[0].stat().st_mode & 0o777) == "0o400", \
        oct(yedekler[0].stat().st_mode & 0o777)
    assert str(yedekler[0]) in r.stdout, "yedek yolu basılmadı: " + r.stdout

    defter = (tmp_path / "sudo-defteri.txt").read_text(encoding="utf-8")
    assert f"chown root:root {yd}" in defter, defter
    assert f"chown root:root {yedekler[0]}" in defter, defter
    assert NOUS_SAHTE not in r.stdout + r.stderr, "SIR DEĞERİ basıldı"


# =================================================================================================
# K6) POZİTİF TABAN — negatif kontrolün "YOK"u ancak taban OK ise anlamlıdır
# =================================================================================================

def test_K6_faz2_BASLANGICTA_kanit_OK_degilse_OLCULEMEDI_der(tmp_path):
    """HEP-YOK DELİĞİ. Negatif kontrol "iki kanal da sahteyken kanıt YOK demeli" der; ama uç
    ZATEN YOK diyorsa (pano token'ı bozuk, servis yarım, uç 500) o YOK anahtar hakkında hiçbir
    şey söylemez — ve ardından gelen farksal ölçüm de YOK döner, betik "faz-2 erken, sürümü
    dağıt" diye YANLIŞ teşhis basar. Taban hiçbir şeye dokunmadan, ölçüm turundan ÖNCE ölçülür."""
    kok, ortam, envf = _faz2_kok(tmp_path, curl_kip="anahtar",
                                 kred_icerik=f"{NOUS_SAHTE}\n", gercek="SAHTE-BASKA-ANAHTAR-8")
    once = (_agac(kok), envf.read_text(encoding="utf-8"))

    r = _kos(tmp_path, ortam, "--faz2", "NOUS_API_KEY")
    cikti = r.stdout + r.stderr

    assert r.returncode != 0, "taban ölçülmeden faz-2 ilerledi: " + cikti
    assert "ÖLÇÜLEMEDİ" in cikti and "BAŞLANGIÇTA" in cikti, cikti
    assert "negatif kontrol: İKİ kanal da sahte" not in cikti, "tabansız ölçüme GİRİLDİ: " + cikti
    assert (_agac(kok), envf.read_text(encoding="utf-8")) == once, "taban düşerken diske yazıldı"


# =================================================================================================
# K7) ÖLÇÜM YÜZEYİNİN KALANI — ortam kanalı · trap · KAPI_APIKEY
# =================================================================================================

def test_K7a_faz2_uygulama_ORTAM_kanalini_okuyorsa_DURUR_ve_degerler_GERCEK_kalir(tmp_path):
    """FAZ-2'NİN ASIL HÜKMÜ, ilk kez ölçülüyor. Tur-1'in `anahtar` şimi "motor credential'ı önce
    okur"u SABİTLİYORDU; yani "uygulama hâlâ ortamı okuyor" dalına hiçbir çivi giremiyordu. Bu
    kip motorun ESKİ sürümünü taklit eder (yalnız `.env`). Betik durmalı VE iki kanalı da gerçek
    değere geri getirmelidir — yarım bırakılan bir ölçüm sırrı sahte bırakırdı."""
    kok, ortam, envf = _faz2_kok(tmp_path, curl_kip="ortam",
                                 kred_icerik=f"{NOUS_SAHTE}\n", gercek=NOUS_SAHTE)
    kred = kok / "etc/meridian/nous_api_key"

    r = _kos(tmp_path, ortam, "--faz2", "NOUS_API_KEY")
    cikti = r.stdout + r.stderr

    assert r.returncode == 1, cikti
    assert "ORTAM KANALINI OKUYOR" in cikti, cikti
    assert f"NOUS_API_KEY={NOUS_SAHTE}\n" in envf.read_text(encoding="utf-8"), "ortam SAHTE kaldı"
    assert kred.read_text(encoding="utf-8").strip() == NOUS_SAHTE, "credential SAHTE kaldı"
    assert not list((kok / "etc/meridian").glob("*.olcum-yedek")), "ölçüm kalıntısı bırakıldı"
    assert not list((kok / "opt/meridian").glob(".env.olcum-yedek")), "ölçüm kalıntısı bırakıldı"


def test_K7b_negatif_kontrolde_servis_dusunce_DEGERLER_GERI_GELIR(tmp_path):
    """EN TEHLİKELİ PENCERE. Negatif kontrol sırasında İKİ kanal da sahtedir; o anda `restart`
    sonrası servis açılmazsa betik durur — ama durmadan ÖNCE sahte değerleri geri almalıdır.
    Tur-1'de o pencerenin trap'i `trap "true"` idi: betik "servis açılmadı" deyip çıkıyor ve
    sistemi İKİ KANALI DA SAHTE bırakıyordu. Kurtarma yükü operatöre kalmamalı."""
    kok, ortam, envf = _faz2_kok(tmp_path, curl_kip="anahtar", kred_icerik=f"{NOUS_SAHTE}\n",
                                 gercek=NOUS_SAHTE, servis="dusuk")
    kred = kok / "etc/meridian/nous_api_key"

    r = _kos(tmp_path, ortam, "--faz2", "NOUS_API_KEY")
    cikti = r.stdout + r.stderr

    assert r.returncode != 0, cikti
    assert "negatif kontrol sırasında servis açılmadı" in cikti, cikti
    assert f"NOUS_API_KEY={NOUS_SAHTE}\n" in envf.read_text(encoding="utf-8"), \
        "ortam kanalı SAHTE değerle bırakıldı: " + envf.read_text(encoding="utf-8")
    assert kred.read_text(encoding="utf-8").strip() == NOUS_SAHTE, \
        "credential kaynağı SAHTE değerle bırakıldı"
    assert not list((kok / "etc/meridian").glob("*.olcum-yedek"))


def test_K7c_faz2_KAPI_APIKEY_kilit_yururlukteyken_TAMAMLANIR(tmp_path):
    """İKİNCİ AD HİÇ KOŞTURULMAMIŞTI. `--faz2 KAPI_APIKEY` ayrı bir kod yolundan geçer
    (`_kapi_kilidi_olc`) ve kanıt ucu APISIX'in ARDINDADIR: kapı kilidi yürürlükteyken yanlış
    KAPI anahtarı 401 verir, yani `_kanit_nous` KAPI anahtarına da duyarlıdır. Bakım penceresi
    bu komutu koşacak — teslimden önce operatörün koşacağı BİÇİMDE bir kez koşulur (§6)."""
    kok, ortam, envf = _faz2_kok(tmp_path, curl_kip="iki_anahtar", kred_icerik=f"{NOUS_SAHTE}\n",
                                 kapi_kred_icerik=f"{KAPI_SAHTE}\n",
                                 gercek=NOUS_SAHTE, gercek_kapi=KAPI_SAHTE)

    r = _kos(tmp_path, ortam, "--faz2", "KAPI_APIKEY")
    assert r.returncode == 0, r.stdout + r.stderr
    icerik = envf.read_text(encoding="utf-8")
    assert "KAPI_APIKEY=" not in icerik, icerik
    assert f"NOUS_API_KEY={NOUS_SAHTE}\n" in icerik, "ÖTEKİ sırrın satırı yendi"
    assert f"NOUS_ENDPOINT={KAPI_UC}\n" in icerik, "yapılandırma satırı yendi"
    assert (kok / "etc/meridian/kapi_apikey").read_text(encoding="utf-8").strip() == KAPI_SAHTE
    assert "kapı kilidi yürürlükte" in r.stdout, r.stdout
    for gizli in (NOUS_SAHTE, KAPI_SAHTE):
        assert gizli not in (r.stdout + r.stderr), "SIR DEĞERİ basıldı"


def test_K7d_faz2_KAPI_APIKEY_kilit_YOKKEN_hicbir_sey_yapmadan_durur(tmp_path):
    """Kapı key-auth kilidi kapalıyken yanlış anahtarla da 200 gelir; o hâlde "motor çalışıyor"
    hangi kanalın okunduğu hakkında HİÇBİR ŞEY söylemez ve farksal ölçüm bir tiyatrodur. Kapı
    ölçümden ÖNCE düşer: restart'lı ölçüm turuna hiç girilmez."""
    kok, ortam, envf = _faz2_kok(tmp_path, curl_kip="iki_anahtar", kred_icerik=f"{NOUS_SAHTE}\n",
                                 kapi_kred_icerik=f"{KAPI_SAHTE}\n", gercek=NOUS_SAHTE,
                                 gercek_kapi=KAPI_SAHTE, kilit="200")
    once = (_agac(kok), envf.read_text(encoding="utf-8"))

    r = _kos(tmp_path, ortam, "--faz2", "KAPI_APIKEY")
    cikti = r.stdout + r.stderr

    assert r.returncode != 0, "kilitsiz kapıda faz-2 ilerledi: " + cikti
    assert "ÖLÇÜLEMEZ" in cikti and "kilit" in cikti, cikti
    assert (_agac(kok), envf.read_text(encoding="utf-8")) == once, "kilitsiz kapıda diske yazıldı"


def test_K7e_faz2_KAPI_APIKEY_UC_okunamazsa_durur(tmp_path):
    """`_kapi_kilidi_olc` kapı ucunu `.env`ten okur; satır yoksa kilidi ölçemez. Ölçemediği bir
    şeye "geçti" demek uydurmadır — ve `${uc%/}/models` boş uçla `/models`e, yani YEREL bir yola
    curl atardı (ölçüm sessizce başka bir şeyi ölçerdi)."""
    kok, ortam, envf = _faz2_kok(
        tmp_path, curl_kip="iki_anahtar", kred_icerik=f"{NOUS_SAHTE}\n",
        kapi_kred_icerik=f"{KAPI_SAHTE}\n", gercek=NOUS_SAHTE, gercek_kapi=KAPI_SAHTE,
        env_metni=ENV_COK_SATIR.replace(f"NOUS_ENDPOINT={KAPI_UC}\n", ""))
    once = (_agac(kok), envf.read_text(encoding="utf-8"))

    r = _kos(tmp_path, ortam, "--faz2", "KAPI_APIKEY")
    cikti = r.stdout + r.stderr

    assert r.returncode != 0, cikti
    assert "NOUS_ENDPOINT okunamadı" in cikti, cikti
    assert (_agac(kok), envf.read_text(encoding="utf-8")) == once, "uç yokken diske yazıldı"


# =================================================================================================
# TUR 3 — YENİDEN İNCELEMENİN İKİ KOD BLOKLAYICISI + kalıntı kapısının görünürlüğü (2026-09-08)
# =================================================================================================

def test_K2d_geri_al_SATIR_YERINDE_ve_DEGERLIYKEN_dropini_KALDIRIR(tmp_path):
    """K2c'NİN İKİZİ — ÇIKIŞSIZ DÖNGÜNÜN KAPANIŞI (yeniden inceleme YB-2, ölçüldü).

    K2c'nin lafzi uygulaması "`$ad`ın satırı BU KOŞUMDA yazılmadıysa dur" diyordu; oysa hüküm
    "sır bir kanaldan okunabilsin"dir. Kaynaklar 1 baytken ve `.env` satırı ELLE geri yüklenmişken
    (A1'in 2026-09-07 sonrası muhtemel hâli) araç, VAR OLMA SEBEBİ olan durumda sonsuza dek
    reddediyordu: die "yedekten `^NOUS_API_KEY=` satırını `.env`e kopyala, sonra tekrarla" diyor,
    satır ZATEN orada, operatör tekrarlıyor, AYNI die. Tek çıkış betiği atlayıp drop-in'i elle
    silmekti ve betik bunu SÖYLEMİYORDU. Burada: ortam kanalı çalışıyor → drop-in KALKAR, rc 0.

    Bu bir hüküm GEVŞETMESİ DEĞİLDİR: K2c (satır YOK + kaynak boş → dur, drop-in DURUR) aynı
    dosyada yeşil kalır; ayrılan tek şey satırın YERİNDE ve DEĞERLİ olduğu dal."""
    kok, ortam = _sahte_ortam(tmp_path)
    birim = kok / "etc/systemd/system/meridian.service.d"
    dropin = birim / "53-nous-kapi-credential.conf"
    dropin.write_text(DROPIN.read_text(encoding="utf-8"), encoding="utf-8")
    # İKİ kaynak da 1 bayt = BOŞ (olayın bıraktığı hâl), `.env` ise TAM ve DEĞERLİ.
    (kok / "etc/meridian/nous_api_key").write_text("\n", encoding="utf-8")
    (kok / "etc/meridian/kapi_apikey").write_text("\n", encoding="utf-8")
    envf = kok / "opt/meridian/.env"
    envf.write_text(ENV_COK_SATIR, encoding="utf-8")

    r = _kos(tmp_path, ortam, "--geri-al", "NOUS_API_KEY")
    cikti = r.stdout + r.stderr

    assert r.returncode == 0, f"ortam kanalı çalışırken geri alma REDDETTİ: {cikti}"
    assert not dropin.exists(), "drop-in kaldırılmadı — çıkışsız döngü sürüyor: " + cikti
    assert "satır yerinde (ortam kanalı)" in r.stdout, cikti
    assert envf.read_text(encoding="utf-8") == ENV_COK_SATIR, \
        "boş kaynaktan `.env` EZİLDİ: " + envf.read_text(encoding="utf-8")
    for gizli in (NOUS_SAHTE, KAPI_SAHTE, DASH_SAHTE):
        assert gizli not in cikti, "SIR DEĞERİ basıldı"


def test_K2e_geri_al_OTEKI_adin_DEGERSIZ_satirini_DEGERLE_DOLDURUR(tmp_path):
    """KÖR ÇİVİNİN KAPANIŞI (yeniden inceleme YB-1): `_env_satiri_dolu_mu`nun DEĞER yarısı.

    K2b yalnız "satır VAR mı"yı ısırıyordu: gövde `grep -qs "^${ad}="`e indirildiğinde 35 çivinin
    35'i de yeşil kalıyordu. Oysa olayın bıraktığı `.env` şekli tam olarak `KAPI_APIKEY=`
    (DEĞERSİZ satır) idi; "satır var" diye dokunulmasa KAPI ortam kanalından da düşer, drop-in de
    kalkar — sır İKİ kanaldan birden gider ve `/healthz` bunu göremez. Tur-1'in bütün tezi
    ("değersiz satır 'ayarlı' DEĞİLDİR") tek satırlık bir geri dönüşle sessizce geçerdi."""
    kok, ortam = _sahte_ortam(tmp_path)
    birim = kok / "etc/systemd/system/meridian.service.d"
    (birim / "53-nous-kapi-credential.conf").write_text(
        DROPIN.read_text(encoding="utf-8"), encoding="utf-8")
    (kok / "etc/meridian/nous_api_key").write_text(f"{NOUS_SAHTE}\n", encoding="utf-8")
    (kok / "etc/meridian/kapi_apikey").write_text(f"{KAPI_SAHTE}\n", encoding="utf-8")
    envf = kok / "opt/meridian/.env"
    envf.write_text("NOUS_MODEL=sahte-model\nKAPI_APIKEY=\n", encoding="utf-8")

    r = _kos(tmp_path, ortam, "--geri-al", "NOUS_API_KEY")
    cikti = r.stdout + r.stderr

    assert r.returncode == 0, cikti
    icerik = envf.read_text(encoding="utf-8")
    assert f"KAPI_APIKEY={KAPI_SAHTE}\n" in icerik, \
        "DEĞERSİZ satır 'ayarlı' sayıldı ve KAPI ortam kanalından düştü: " + icerik
    assert icerik.count("KAPI_APIKEY=") == 1, icerik
    assert f"NOUS_API_KEY={NOUS_SAHTE}\n" in icerik, "asıl adın satırı geri yazılmadı: " + icerik
    assert "satır yerinde" not in r.stdout, "değersiz satır 'yerinde' raporlandı: " + r.stdout
    for gizli in (NOUS_SAHTE, KAPI_SAHTE):
        assert gizli not in cikti, "SIR DEĞERİ basıldı"


def test_K1d_faz1_ve_faz1_hafiza_da_KALINTI_varken_CIKIS_2_ile_durur(tmp_path):
    """KALINTI KAPISI YAZAN HER ALT KOMUTTA (yeniden inceleme YB-3, ölçüldü).

    Kapı yalnız faz-2 ve geri almadaydı; oysa betiğin KENDİ die'ları operatörü faz-1'e yolluyor
    ("Önce `--faz1 $ad` ile kaynak yeniden yazılır"). Kalıntı dururken `.env` ölçümün ATILACAK
    sahte değerini taşır ve boş geçilen istem O DEĞERİ credential kaynağına taşırdı: rc 0 +
    "iki kanal da canlı", oysa iki kanal da çöp anahtar. `--faz1-hafiza` ise motoru RESTART eder
    ve iki kanalı da sahte olan motoru "sağlıklı" gösterir. İkisi de K1'in sınıfıdır."""
    kok, ortam = _sahte_ortam(tmp_path)
    envf = kok / "opt/meridian/.env"
    envf.write_text(ENV_COK_SATIR, encoding="utf-8")
    (kok / "etc/hindsight/creds").mkdir(parents=True)
    (kok / "etc/hindsight/creds/HINDSIGHT_API_TENANT_API_KEY").write_text(
        "SAHTE-TENANT-DEGERI-5\n", encoding="utf-8")
    ky, ey = _kalinti_birak(kok, envf)
    once = (_agac(kok), envf.read_text(encoding="utf-8"),
            ky.read_text(encoding="utf-8"), ey.read_text(encoding="utf-8"))

    r1 = _kos(tmp_path, ortam, "--faz1", "NOUS_API_KEY")
    c1 = r1.stdout + r1.stderr
    assert r1.returncode == 2, f"faz-1 kalıntıya rağmen koştu (rc {r1.returncode}): {c1}"
    assert f'sudo mv -f "{ey}" "{envf}"' in c1, c1

    r2 = _kos(tmp_path, ortam, "--faz1-hafiza")
    c2 = r2.stdout + r2.stderr
    assert r2.returncode == 2, f"faz-1A kalıntıya rağmen koştu (rc {r2.returncode}): {c2}"
    assert not (kok / "etc/systemd/system/meridian.service.d"
                      "/54-hafiza-credential.conf").exists(), "kalıntı varken 54 drop-in kuruldu"

    assert (_agac(kok), envf.read_text(encoding="utf-8"),
            ky.read_text(encoding="utf-8"), ey.read_text(encoding="utf-8")) == once, \
        "kalıntı varken diske YAZILDI"
    assert KURTARMA_NOUS not in (c1 + c2), "SIR DEĞERİ basıldı"


def test_K1e_durum_OLCUM_KALINTISINI_raporlar(tmp_path):
    """RAPOR, KAPILARIN ÖLÇTÜĞÜ ŞEYİ ÖLÇER (tek-kaynak; yeniden inceleme YB-3 ölçüm A).

    Operatörün koşacağı İLK komut `durum`dur (betiğin kendi başlığı öyle diyor), ama kalıntı
    dururken rapor rc 0 veriyor ve `olcum-yedek` kelimesi çıktıda HİÇ geçmiyordu: kapı biliyor,
    rapor bilmiyordu (Yasa 6). `durum` SALT-OKUNURDUR — durmaz, SÖYLER.

    İki uç da ölçülür (bedel yasası): kalıntı yokken satır "yok" der, yani her koşumu bir yalan
    alarmla açmaz."""
    kok, ortam = _sahte_ortam(tmp_path)
    envf = kok / "opt/meridian/.env"
    envf.write_text(ENV_COK_SATIR, encoding="utf-8")

    temiz = _kos(tmp_path, ortam)
    assert temiz.returncode == 0, temiz.stdout + temiz.stderr
    assert "ölçüm kalıntısı: yok" in temiz.stdout, temiz.stdout

    ky, ey = _kalinti_birak(kok, envf)
    once = _agac(kok)
    r = _kos(tmp_path, ortam)
    cikti = r.stdout + r.stderr

    assert r.returncode == 0, "durum kalıntıda DURDU (salt-okunur rapor durmaz): " + cikti
    assert "ölçüm kalıntısı: VAR" in r.stdout, r.stdout
    assert str(ey) in r.stdout and str(ky) in r.stdout, r.stdout
    assert _agac(kok) == once, "durum diske yazdı"
    assert KURTARMA_NOUS not in cikti, "SIR DEĞERİ basıldı"
