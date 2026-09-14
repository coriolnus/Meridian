"""test_vault_faz2_v485.py — TSK-064 Faz-2 (HashiCorp Vault) REPO TARAFININ ÇİVİSİ.

NE ÇAKIYOR. Bu tur A1'e HİÇ DOKUNMAZ: kurulum Rol-1'in bakım penceresinin işidir. Repo tarafı
yalnız DÖRT şey üretir ve dördü de burada çakılır —

  A-D  Vault sunucu birimleri + oto-unseal betiği  (Task 1)
  E-H  Tek kaynak: `deploy/sir_envanteri.yaml` içindeki `vault_kv` bölümü + ondan ÜRETİLEN
       politika/agent dosyaları                     (Task 2)
  I-K  A1 betikleri (`vault_kur` / `vault_sir_koy`) — sır sızdırmayan kabuk sözleşmesi (Task 3)
  L-N  Bekçi (`ops/vault_sagligi.py`) + alarm sınıfı + dağıtım listeleri  (Task 4)

NEDEN KAYNAK METNİ OKUYAN ÇİVİLER. Yerelde `vault` ikilisi YOKTUR ve ajan A1'e ssh yapmaz
(CLAUDE.md §3) — yani "unseal gerçekten oldu mu" sorusu bu turda ÖLÇÜLEMEZ ve ölçülemeyen bir
şeye yeşil demek uydurma yasağının ihlali olurdu. Bu yüzden iki ayrı kanıt sınıfı vardır ve
ikisi de ADIYLA ayrıdır:
  (1) KAYNAK METNİ çivileri — birim/betik dosyasının GERÇEKTEN hangi direktifi taşıdığı. Bu
      ölçülebilir ve mutasyonla ısırır (bir direktif bozulunca kırmızı).
  (2) DAVRANIŞ çivileri — `--kuru` yollarının sahte bir `vault` betiğiyle (PATH stub) koşumu.
      Gerçek bir kasa ile konuşmazlar; ölçtükleri şey "betik yazmadan önce ne YAPIYOR"dur.
Gerçek davranış (stdin unseal, AppRole login, template render) A1'de test-ateşlemesiyle
ölçülür — CLAUDE.md §9 "kurulu ≠ çalışır". Bu dosya o ölçümün YERİNE GEÇMEZ, önünü açar.

SIR DEĞERİ YASAĞI BU DOSYADA DA GEÇERLİ: hiçbir testte gerçek bir sır değeri yoktur; sahte
değerler `SAHTE-` önekiyle yazılır ve yalnız sha256 karşılaştırması için kullanılır.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import pathlib
import zipfile

import pytest
import yaml

REPO = pathlib.Path(__file__).resolve().parents[1]
VAULT_DIZIN = REPO / "deploy" / "vault"
HCL = VAULT_DIZIN / "vault.hcl"
BIRIM_VAULT = VAULT_DIZIN / "vault.service"
BIRIM_UNSEAL = VAULT_DIZIN / "vault-unseal.service"
BIRIM_AGENT = VAULT_DIZIN / "vault-agent.service"
BIRIM_SAGLIK = VAULT_DIZIN / "vault-sagligi.service"
TIMER_SAGLIK = VAULT_DIZIN / "vault-sagligi.timer"
UNSEAL_SH = VAULT_DIZIN / "vault_unseal.sh"

#: Dinleme adresi TEK KAYNAK: burada yazılı, her çivi buradan okur. `0.0.0.0` bu depoda bir
#: YASAKTIR (tasarım §6.1: "Dışa açılmaz"), bu yüzden ayrı bir sabit olarak değil bir NEGATİF
#: desen olarak ölçülür.
BEKLENEN_ADRES = "127.0.0.1:8200"

#: Sertleştirme ortak seti — `deploy/oracle-a1/meridian.service` ve kardeşlerinden alınan
#: (ölçüldü 2026-09-14) küme. `CapabilityBoundingSet` BİLEREK DIŞARIDA: Vault mlock için
#: CAP_IPC_LOCK ister ve boş küme onu da keserdi — o kalem kendi testinde ölçülür.
SERTLESTIRME_ORTAK = {
    "NoNewPrivileges": "true",
    "ProtectSystem": "strict",
    "ProtectHome": "read-only",
    "PrivateTmp": "true",
    "ProtectKernelTunables": "true",
    "ProtectKernelModules": "true",
    "ProtectKernelLogs": "true",
    "ProtectClock": "true",
    "ProtectControlGroups": "true",
    "ProtectHostname": "true",
    "RestrictNamespaces": "true",
    "RestrictSUIDSGID": "true",
    "RestrictRealtime": "true",
    "LockPersonality": "true",
    "SystemCallArchitectures": "native",
}


# =================================================================================================
# Yardımcılar — birim dosyası okuma (yorumlar AYIKLANIR; bir direktifin ŞERHTE geçmesi onu
# YÜRÜRLÜĞE koymaz ve bu ayrım bu depoda ölçülmüş bir tuzaktır)
# =================================================================================================

def _birim_satirlari(yol: pathlib.Path, bolum: str | None = None) -> list[tuple[str, str]]:
    """(anahtar, değer) çiftleri — yorum/boş satırlar DÜŞER.

    `bolum` verilirse YALNIZ o bölüm okunur. Bölüm ayrımı bir konfor değil ŞARTTIR: "sertleştirme
    bölümün SON direktifidir" iddiası bölümsüz okunduğunda `[Install]`daki `WantedBy=` yüzünden
    HER ZAMAN düşerdi — yani çivi doğru şeyi ölçmez, yalnız gürültü üretirdi."""
    out: list[tuple[str, str]] = []
    aktif: str | None = None
    for ham in yol.read_text(encoding="utf-8").splitlines():
        s = ham.strip()
        if not s or s.startswith("#"):
            continue
        if s.startswith("[") and s.endswith("]"):
            aktif = s[1:-1]
            continue
        if "=" not in s:
            continue
        if bolum is not None and aktif != bolum:
            continue
        k, _, v = s.partition("=")
        out.append((k.strip(), v.strip()))
    return out


def _degerler(yol: pathlib.Path, anahtar: str) -> list[str]:
    return [v for k, v in _birim_satirlari(yol) if k == anahtar]


def _deger(yol: pathlib.Path, anahtar: str) -> str | None:
    d = _degerler(yol, anahtar)
    return d[-1] if d else None


def _yorumsuz(metin: str) -> str:
    """Kabuk/HCL yorum satırları düşürülmüş metin — "şerhte geçiyor" ile "kodda var" ayrımı."""
    return "\n".join(s for s in metin.splitlines() if not s.strip().startswith("#"))


# =================================================================================================
# A) vault.hcl — dinleme yalnız loopback, TLS'siz, dosya deposu
# =================================================================================================

def test_A1_hcl_VAR_ve_dinleme_YALNIZ_loopback():
    """Tasarım §6.1'in tek sert kuralı: kasa DIŞA AÇILMAZ.

    `0.0.0.0` bir yazım hatası kadar kolaydır ve sonucu, A1'in genel IP'sinde mühürsüz bir sır
    kasasıdır. Çivi ADRESİ ölçer, "listener var mı"yı değil."""
    assert HCL.exists(), "deploy/vault/vault.hcl yok — Task 1 çıktısı üretilmedi"
    metin = _yorumsuz(HCL.read_text(encoding="utf-8"))
    assert 'listener "tcp"' in metin, "tcp listener bloğu yok"
    assert re.search(r'address\s*=\s*"' + re.escape(BEKLENEN_ADRES) + r'"', metin), (
        f"listener adresi {BEKLENEN_ADRES!r} değil: {metin!r}"
    )
    assert "0.0.0.0" not in metin, "YASAK: kasa dışa açık dinliyor (tasarım §6.1)"


def test_A2_tls_disable_BEYANLI():
    """TLS'sizlik bir KARARDIR (tasarım §6.1, bedel beyanlı) — sessiz bir varsayılan değil.
    Satır dosyada AÇIKÇA durur ki okuyan mühendis kararı görsün."""
    metin = _yorumsuz(HCL.read_text(encoding="utf-8"))
    assert re.search(r"tls_disable\s*=\s*true", metin), "tls_disable kararı beyan edilmemiş"


def test_A3_storage_file_ve_yolu():
    metin = _yorumsuz(HCL.read_text(encoding="utf-8"))
    assert 'storage "file"' in metin, "dosya deposu bloğu yok (tek düğüm, HA yok)"
    assert re.search(r'path\s*=\s*"/opt/vault/data"', metin), "depo yolu /opt/vault/data değil"


def test_A5_generate_root_JETONSUZ_ACIK_ve_YALNIZ_o_aile():
    """Kurtarma kökü (ölçülen arıza 2026-09-14): Vault 2.0+ `sys/generate-root/*`'ı varsayılan
    olarak kimlik doğrulamasına aldı (CVE-2026-5807). Kök jetonu iptal edildikten sonra yönetici
    jetonu kaybolursa unseal anahtarı tek başına hiçbir şey açamaz → kasa yeniden kurulur. Bu
    satır o yolu açık tutar; ama YALNIZ bu aile: "rekey" ve "generate-operation-token" kapalı
    kalır (liste TAM eşitlik, alt-küme değil)."""
    metin = _yorumsuz(HCL.read_text(encoding="utf-8"))
    m = re.search(r'enable_unauthenticated_access\s*=\s*\[([^\]]*)\]', metin)
    assert m, "enable_unauthenticated_access yok — generate-root kapalı, kurtarma yolu yok"
    aileler = re.findall(r'"([^"]+)"', m.group(1))
    assert aileler == ["generate-root"], (
        f"jetonsuz aile listesi TAM OLARAK ['generate-root'] olmalı: {aileler}")


def test_A4_MUTASYON_adres_disa_acilirsa_KIRMIZI():
    """Mutasyon: `127.0.0.1` → `0.0.0.0`. Çivi bunu GÖRMELİ, yoksa yasak yazılı ama ölçüsüzdür."""
    bozuk = HCL.read_text(encoding="utf-8").replace("127.0.0.1", "0.0.0.0")
    assert "0.0.0.0" in _yorumsuz(bozuk), "mutasyon uygulanamadı — çivi kör"


# =================================================================================================
# B) vault.service — sertleştirme + mlock yeteneği + ayrıcalıklı ExecStartPost
# =================================================================================================

def test_B1_sertlestirme_ortak_seti_duruyor():
    """Filo ortak seti (meridian.service emsali). Bir kasa sürecinin bu setten muaf olması
    düşünülemez — sır ORADA yaşıyor."""
    assert BIRIM_VAULT.exists(), "deploy/vault/vault.service yok"
    for anahtar, beklenen in SERTLESTIRME_ORTAK.items():
        assert _deger(BIRIM_VAULT, anahtar) == beklenen, (
            f"vault.service: {anahtar}={_deger(BIRIM_VAULT, anahtar)!r}, beklenen {beklenen!r}"
        )


def test_B2_adres_ailesi_ve_syscall_filtresi():
    """Plan Global Constraints: `RestrictAddressFamilies=AF_INET AF_UNIX` (IPv6 YOK — kasa
    yalnız 127.0.0.1 dinler) ve `SystemCallFilter=@system-service` bölümün SON direktifi."""
    assert _deger(BIRIM_VAULT, "RestrictAddressFamilies") == "AF_INET AF_UNIX"
    satirlar = _birim_satirlari(BIRIM_VAULT, bolum="Service")
    assert satirlar[-1][0] == "SystemCallFilter", (
        f"SystemCallFilter son direktif değil: {satirlar[-1]}"
    )
    assert satirlar[-1][1] == "@system-service"


def test_B3_mlock_yetenegi_TEK_ve_DAR():
    """Vault belleği diske sızdırmamak için mlock ister; bunun bedeli TEK bir yetenektir.
    `CapabilityBoundingSet` boş OLAMAZ (o zaman ambient de düşer) ama TEK kalemle sınırlıdır —
    "boş küme" kuralının bu birimde BEYANLI istisnası budur."""
    assert _deger(BIRIM_VAULT, "AmbientCapabilities") == "CAP_IPC_LOCK"
    assert _deger(BIRIM_VAULT, "CapabilityBoundingSet") == "CAP_IPC_LOCK"


def test_B4_yazma_yuzeyi_YALNIZ_depo_dizini():
    """`ProtectSystem=strict` altında tek yazılabilir yol depodur. Fazlası, kasanın kendi
    sandbox'ını delmek olurdu."""
    assert _deger(BIRIM_VAULT, "ReadWritePaths") == "/opt/vault/data"


def test_B5_execstartpost_AYRICALIKLI_onekli():
    """`+` ÖNEKİ ZORUNLU ve gerekçesi ölçülmüş bir çelişkidir: birim `User=vault` koşar, ama
    unseal anahtarı 0400 root:root'tur (tasarım §6.2). Önek olmadan ExecStartPost `vault`
    kullanıcısı olarak koşar ve anahtarı OKUYAMAZ — mühür her açılışta kapalı kalır ve arıza
    ancak ilk sır render'ında görülür."""
    post = _deger(BIRIM_VAULT, "ExecStartPost")
    assert post is not None, "ExecStartPost yok — oto-unseal bağlanmamış"
    assert post.startswith("+"), f"ExecStartPost ayrıcalıklı değil ('+' öneki yok): {post!r}"
    assert post.lstrip("+") == "/opt/vault/bin/vault_unseal.sh"


def test_B6_kullanici_ve_config_yolu():
    assert _deger(BIRIM_VAULT, "User") == "vault"
    exec_start = _deger(BIRIM_VAULT, "ExecStart")
    assert exec_start and "/etc/vault/vault.hcl" in exec_start, exec_start


def test_B7_MUTASYON_ayricalik_oneki_dusurse_KIRMIZI():
    """Mutasyon: `ExecStartPost=+/…` → `ExecStartPost=/…`. B5 bunu görmezse önek yazılı ama
    ölçüsüz olurdu (sessiz gevşeme sınıfı)."""
    bozuk = BIRIM_VAULT.read_text(encoding="utf-8").replace("ExecStartPost=+", "ExecStartPost=")
    satir = [s for s in bozuk.splitlines() if s.startswith("ExecStartPost=")]
    assert satir and not satir[0].split("=", 1)[1].startswith("+"), "mutasyon uygulanamadı"


# =================================================================================================
# C) vault_unseal.sh — değer argv'ye GİRMEZ, bekleme SINIRLI
# =================================================================================================

def test_C1_betik_sozdizimi_gecerli():
    assert UNSEAL_SH.exists(), "deploy/vault/vault_unseal.sh yok"
    r = subprocess.run(["bash", "-n", str(UNSEAL_SH)], capture_output=True, text=True)
    assert r.returncode == 0, f"bash -n düştü: {r.stderr}"


def test_C1b_betik_CALISTIRILABILIR():
    """Birim onu doğrudan ExecStartPost ile çağırır; çalıştırma biti yoksa systemd 203/EXEC
    ile düşer ve arıza "mühür açılmadı" diye okunurdu."""
    assert os.access(UNSEAL_SH, os.X_OK), "vault_unseal.sh çalıştırılabilir değil"


def test_C2_unseal_degeri_STDIN_den_gecer_argv_den_DEGIL():
    """`vault operator unseal $(cat …)` argv'ye sır koyar ve argv `/proc/<pid>/cmdline`de
    makinedeki HER kullanıcıya açıktır. Tek doğru biçim STDIN ve yönlendirmedir — ve stdin'i
    KABUL EDEN komutla: `write sys/unseal key=-`.

    TUR-3 (ölçülen arıza, A1 2026-09-14 09:5xZ): tur-1/2 `operator unseal -` yazıyordu ve bu
    çivi onu yeşil sayıyordu; A1'de komut "file descriptor 0 is not a terminal" ile düştü —
    `operator unseal` için `-` bir stdin işareti DEĞİL, anahtar sanılan bir argümandır ve TTY
    dışında (ExecStartPost, oneshot) stdin okumayı reddeder. Çivi kaynak metnini okuyordu,
    CLI'nin davranışını değil. Bu yüzden eski biçim artık AÇIKÇA YASAK: geri gelirse burada
    kırmızı olur (üçüncü assert), C5b mutasyonu bunu ısırır."""
    metin = _yorumsuz(UNSEAL_SH.read_text(encoding="utf-8"))
    assert re.search(r"write\s+sys/unseal\s+key=-(?![-\w])", metin), (
        "`write sys/unseal key=-` (stdin) biçimi yok — değer argv'ye giriyor olabilir"
    )
    assert not re.search(r"sys/unseal\s+key=[\"']?\$", metin), (
        "unseal değeri argv'ye konuyor (değişken genişletmesi)"
    )
    assert not re.search(r"operator\s+unseal", metin), (
        "`operator unseal` geri gelmiş — TTY dışında stdin'i reddeder (ölçülen arıza 2026-09-14)"
    )
    assert "$(cat" not in metin, "komut ikamesiyle anahtar okunuyor — argv sızıntısı"


def test_C3_betik_SIRRI_DEGISKENE_ALMAZ_ve_BASMAZ():
    """İki ayrı yasak, tek test — çünkü ikisi de AYNI arızayı üretir: anahtarın journal'a düşmesi.

    (a) `set -x` bütün komutları (yönlendirme hedefleri dahil) journal'a döker.
    (b) Anahtar İÇERİĞİ hiçbir değişkene ALINMAZ. Bu, "basmıyoruz" demekten daha güçlü bir
        iddiadır: değer bir değişkende yaşamıyorsa yanlışlıkla basılamaz da. Bu yüzden çivi
        `echo` satırlarını değil, İÇERİK OKUMA biçimlerini (`$(cat`, `$(<`, `read`) arar ve
        `echo`/`printf` gövdesinde hiçbir komut ikamesi olmadığını ölçer (kaçak yol).
        `$ANAHTAR_YOLU` bir YOLDUR ve basılması meşrudur — operatörün hangi dosyanın eksik
        olduğunu görmesi gerekir."""
    metin = _yorumsuz(UNSEAL_SH.read_text(encoding="utf-8"))
    assert not re.search(r"^\s*set\s+-[a-z]*x", metin, re.M), "set -x açık — sır journal'a düşer"
    assert "$(cat" not in metin and "$(<" not in metin, "anahtar içeriği komut ikamesiyle okunuyor"
    assert not re.search(r"^\s*read\b", metin, re.M), "anahtar `read` ile değişkene alınıyor olabilir"
    for m in re.finditer(r"^\s*(?:echo|printf)\s+[^\n]*", metin, re.M):
        assert "$(" not in m.group(0), f"çıktı satırında komut ikamesi var (kaçak yol): {m.group(0)!r}"


def test_C4_bekleme_SINIRLI_ve_sinir_KAYNAKTA_yazili():
    """Bu bir BEKLEYİCİ DÖNGÜSÜ DEĞİL, servis açılış yoklamasıdır (CLAUDE.md §7 ayrımı) — ve
    ayrımı yapan tek şey SINIRIN kendisidir. Sınırsız bir `while` A1'de bir birimi sonsuza dek
    `activating` bırakırdı."""
    metin = _yorumsuz(UNSEAL_SH.read_text(encoding="utf-8"))
    m = re.search(r"AYAKTA_DENEME\s*=\s*(\d+)", metin)
    assert m, "deneme sayısı adlandırılmış bir sabitte değil (sınır okunamıyor)"
    assert 1 <= int(m.group(1)) <= 60, f"deneme sayısı aralık dışı: {m.group(1)}"
    assert re.search(r"sleep\s+1\b", metin), "yoklama aralığı 1 sn değil"
    assert not re.search(r"while\s+true", metin), "sınırsız döngü — bekleyici yasağı (§7)"


def test_C5_MUTASYON_stdin_isareti_kalkinca_KIRMIZI():
    """Mutasyon: `sys/unseal key=-` → `sys/unseal key="$ANAHTAR"`. C2 bunu ısırmalı."""
    bozuk = _yorumsuz(UNSEAL_SH.read_text(encoding="utf-8")).replace(
        "sys/unseal key=-", 'sys/unseal key="$ANAHTAR"')
    assert not re.search(r"write\s+sys/unseal\s+key=-(?![-\w])", bozuk), "mutasyon uygulanamadı"
    assert re.search(r"sys/unseal\s+key=[\"']?\$", bozuk), "mutasyon C2'nin ikinci kolunu kurmadı"


def test_C5b_MUTASYON_eski_operator_unseal_bicimi_geri_gelince_KIRMIZI():
    """Mutasyon: `write sys/unseal key=-` → `operator unseal -` (tur-1'in A1'de düşen biçimi).
    C2'nin üçüncü kolu bunu ısırmalı — yoksa aynı arıza bir gün "temiz" bir yeniden yazımla geri
    gelir ve çivi yine yeşil kalır."""
    bozuk = _yorumsuz(UNSEAL_SH.read_text(encoding="utf-8")).replace(
        "write sys/unseal key=-", "operator unseal -")
    assert re.search(r"operator\s+unseal", bozuk), "mutasyon uygulanamadı"
    assert not re.search(r"write\s+sys/unseal\s+key=-(?![-\w])", bozuk), "mutasyon eksik kaldı"


# -------------------------------------------------------------------------------------------------
# C6-C9 — BOOTSTRAP SÖZLEŞMESİ (TUR 2, A1 ilk kurulumunda ÖLÇÜLEN arıza 2026-09-14 09:0xZ)
# -------------------------------------------------------------------------------------------------
# ÖLÇÜLEN ARIZA. `vault.service` betiği `ExecStartPost=+…` ile çağırır ve ExecStartPost servis
# AYAĞA KALKAR KALKMAZ koşar — yani `vault_kur.sh` adım 5'teki `operator init`ten ÖNCE. Betik o
# anda "anahtar dosyası yok/boş → exit 2" diyordu; ExecStartPost'un sıfır olmayan çıkışı BİRİMİ
# düşürür, birim `Restart=` ile yeniden dener ve kurulum yeniden-başlama döngüsüne girer
# (journal: `Control process exited, code=exited, status=2`). Kasa hiç init edilemez.
#
# YENİ SÖZLEŞME — "anahtar yok" İKİ AYRI OLGUDUR ve tek çıkış kodu ikisini karıştırıyordu:
#   · kasa HENÜZ INIT EDİLMEMİŞ + anahtar yok → BEKLENEN bootstrap hâli   → çıkış 0 (sessiz değil:
#     olgu ADIYLA basılır; `vault_kur.sh` adım 5 init eder, adım 6 bu betiği KENDİSİ çağırır)
#   · kasa INIT EDİLMİŞ + anahtar yok        → GERÇEK arıza (anahtar kayıp) → çıkış 2
# Ayrımı yapan tek ölçüm `vault status -format=json` içindeki `initialized` alanıdır; uydurulmuş
# bir varsayım (ör. "anahtar yoksa herhâlde init de yoktur") ikinci olguyu SESSİZCE yutardı.

def _sahte_vault_kur(tmp_path, *, initialized: bool, sealed: bool = True,
                     unseal_acar: bool = True):
    """PATH stub'ı DEĞİL, `VAULT_BIN` ile verilen sahte `vault`. Üç alt komutu tanır:

      · `status`                   → çıkış kodu (0 = açık, 2 = mühürlü/init-siz) — gerçek CLI böyle
      · `status -format=json`      → `initialized`/`sealed` alanları + AYNI çıkış kodu
      · `write sys/unseal key=-`   → STDIN'i dosyaya yazar (değer argv'ye GİRMEMELİ)

    `unseal_acar`: sahte kasa unseal isteğinden SONRA açık mı görünür (True — gerçek 1/1 kasa)
    yoksa mühürlü mü kalır (False — eşik >1 ya da yanlış-sınıf anahtar; C11/C12 bunu ölçer).
    Sahte kasa hiçbir şeyi mutasyona uğratmaz; ölçtüğü tek şey betiğin HANGİ DALA girdiğidir."""
    binler = tmp_path / "sahte-bin"
    binler.mkdir(exist_ok=True)
    argv_log = tmp_path / "argv.log"
    stdin_dosya = tmp_path / "unseal.stdin"
    ikili = binler / "vault"
    ikili.write_text(
        "#!/usr/bin/env bash\n"
        f'echo "$*" >> "{argv_log}"\n'
        'if [ "$1" = "status" ]; then\n'
        f'  MUHURLU="{str(sealed).lower()}"\n'
        f'  if [ -e "{stdin_dosya}" ] && [ "{str(unseal_acar).lower()}" = "true" ]; then MUHURLU=false; fi\n'
        '  if [ "$2" = "-format=json" ]; then\n'
        f'    printf \'{{"initialized":%s,"sealed":%s}}\\n\' "{str(initialized).lower()}" "$MUHURLU"\n'
        "  fi\n"
        '  [ "$MUHURLU" = "true" ] && exit 2\n'
        "  exit 0\n"
        "fi\n"
        'if [ "$1" = "write" ] && [ "$2" = "sys/unseal" ] && [ "$3" = "key=-" ]; then\n'
        f'  cat > "{stdin_dosya}"\n'
        "  exit 0\n"
        "fi\n"
        "exit 0\n",
        encoding="utf-8")
    ikili.chmod(0o755)
    return ikili, argv_log, stdin_dosya


def _unseal_kos(tmp_path, betik, *, initialized, sealed=True, anahtar=None, unseal_acar=True):
    """Betiği sahte kasayla koşar. `anahtar=None` → anahtar dosyası HİÇ yaratılmaz."""
    ikili, argv_log, stdin_dosya = _sahte_vault_kur(
        tmp_path, initialized=initialized, sealed=sealed, unseal_acar=unseal_acar)
    anahtar_yolu = tmp_path / "unseal.key"
    if anahtar is not None:
        anahtar_yolu.write_text(anahtar + "\n", encoding="utf-8")
    ortam = dict(os.environ, VAULT_BIN=str(ikili),
                 VAULT_UNSEAL_KEY_FILE=str(anahtar_yolu),
                 VAULT_ADDR="http://127.0.0.1:8200")
    r = subprocess.run(["bash", str(betik)], capture_output=True, text=True, env=ortam)
    return r, argv_log, stdin_dosya


def test_C6_INIT_EDILMEMIS_kasa_unseal_BEKLEMEZ_cikis_0(tmp_path):
    """(i) init YOK + anahtar YOK → çıkış 0 ve olgu ADIYLA basılır.

    Bu testin ölçtüğü şey bir KURULUM DÖNGÜSÜDÜR, bir konfor değil: sıfır olmayan her çıkış
    `vault.service`in ExecStartPost'unu düşürür ve kasa hiç init edilemez."""
    r, _, _ = _unseal_kos(tmp_path, UNSEAL_SH, initialized=False, anahtar=None)
    assert r.returncode == 0, (
        f"init edilmemiş kasada çıkış {r.returncode} — ExecStartPost birimi düşürür ve "
        f"kurulum yeniden-başlama döngüsüne girer:\n{r.stdout}\n{r.stderr}")
    assert "init edilmedi" in r.stdout, (
        f"bootstrap hâli SESSİZCE geçildi — olgu ADIYLA basılmalı:\n{r.stdout}")


def test_C7_INIT_EDILMIS_kasada_ANAHTAR_YOKSA_cikis_2(tmp_path):
    """(ii) init VAR + anahtar YOK → çıkış 2. Bu GERÇEK arızadır: kasa init edilmiş ama mührü
    açacak anahtar kayıp. Bootstrap muafiyeti buraya UZANMAZ — uzasaydı anahtar kaybı, kurulum
    yarımlığıyla aynı sessizliğe gömülürdü."""
    r, _, _ = _unseal_kos(tmp_path, UNSEAL_SH, initialized=True, anahtar=None)
    assert r.returncode == 2, (
        f"init edilmiş kasada anahtar kaybı çıkış {r.returncode} (2 bekleniyordu):"
        f"\n{r.stdout}\n{r.stderr}")


def test_C8_INIT_VAR_ANAHTAR_VAR_MUHURLU_ise_unseal_STDINden_CAGRILIR(tmp_path):
    """(iii) DAVRANIŞSAL kanıt: C2 kaynak metnini okur ("yazılmış mı"), bu test koşar
    ("oluyor mu"). İki şey birden ölçülür — (a) `write sys/unseal key=-` GERÇEKTEN çağrıldı ve
    değer stdin'den GELDİ, (b) değer argv log'unda HİÇ geçmiyor. Yalnız (a) ölçülseydi argv'ye yazan
    bir betik de geçerdi; yalnız (b) ölçülseydi hiç unseal etmeyen bir betik de geçerdi."""
    r, argv_log, stdin_dosya = _unseal_kos(
        tmp_path, UNSEAL_SH, initialized=True, anahtar=SAHTE_DEGER)
    assert r.returncode == 0, f"unseal yolu düştü:\n{r.stdout}\n{r.stderr}"
    assert stdin_dosya.exists(), "`write sys/unseal key=-` hiç çağrılmadı (mühür açılmazdı)"
    assert "mühür açıldı" in r.stdout, "açılan mühür operatöre ADIYLA söylenmiyor"
    assert stdin_dosya.read_text(encoding="utf-8").strip() == SAHTE_DEGER, (
        "anahtar stdin'den GELMEDİ ya da içerik bozuldu")
    assert SAHTE_DEGER not in argv_log.read_text(encoding="utf-8"), "DEĞER ARGV'YE SIZDI"
    assert SAHTE_DEGER not in r.stdout and SAHTE_DEGER not in r.stderr, "DEĞER TERMİNALE BASILDI"


def test_C9_TANINMAYAN_durum_cevabi_SESSIZCE_GECILMEZ(tmp_path):
    """`initialized` okunamazsa hüküm YOKTUR ve yokluğu çıkış 0'la örtmek uydurma yasağının
    ihlalidir ("ölçülemeyen değer `None` + neden"). Tanınmayan cevap GÖRÜNÜR bir arızadır."""
    binler = tmp_path / "sahte-bin"
    binler.mkdir(exist_ok=True)
    ikili = binler / "vault"
    ikili.write_text(
        "#!/usr/bin/env bash\n"
        'if [ "$1" = "status" ]; then echo "anlamsiz cikti"; exit 2; fi\n'
        "exit 0\n", encoding="utf-8")
    ikili.chmod(0o755)
    ortam = dict(os.environ, VAULT_BIN=str(ikili),
                 VAULT_UNSEAL_KEY_FILE=str(tmp_path / "yok.key"))
    r = subprocess.run(["bash", str(UNSEAL_SH)], capture_output=True, text=True, env=ortam)
    assert r.returncode == 1, (
        f"tanınmayan durum cevabında çıkış {r.returncode} (1 bekleniyordu) — "
        f"ölçülemeyen hüküm sessizce geçildi:\n{r.stdout}\n{r.stderr}")


@pytest.mark.parametrize("eski,yeni,ad", [
    ("exit 0   # bootstrap", "exit 2   # bootstrap", "bootstrap çıkışı 2'ye çevrildi"),
    ('"$INIT_DURUMU" in', '"true" in', "init ölçümü sabitlendi (kapı köreltildi)"),
])
def test_C10_MUTASYON_bootstrap_kapisi_bozulunca_KIRMIZI(tmp_path, eski, yeni, ad):
    """Çivi yeşili kanıt değildir (CLAUDE.md §6): iki mutasyon, iki ayrı dal.

    (1) Bootstrap çıkışı 2'ye dönerse C6 kırmızı olmalı — yani ölçtüğü şey gerçekten ÇIKIŞ KODU.
    (2) `initialized` ölçümü sabit `true`ya çevrilirse init-siz kasa da "init edilmiş" sayılır
        ve C6 yine kırmızı olmalı — yani kapı GERÇEKTEN kasanın durumunu okuyor."""
    ham = UNSEAL_SH.read_text(encoding="utf-8")
    assert eski in ham, f"mutasyon çapası kaynakta yok: {eski!r} ({ad})"
    bozuk = tmp_path / "vault_unseal_bozuk.sh"
    bozuk.write_text(ham.replace(eski, yeni), encoding="utf-8")
    bozuk.chmod(0o755)
    r, _, _ = _unseal_kos(tmp_path, bozuk, initialized=False, anahtar=None)
    assert not (r.returncode == 0 and "init edilmedi" in r.stdout), (
        f"MUTASYON ISIRMADI ({ad}): bozuk betik hâlâ C6'nın beklediği hükmü veriyor — "
        f"çivi yanlış sebeple yeşil:\n{r.stdout}\n{r.stderr}")

def test_C11_HUKUM_API_CEVABINDAN_DEGIL_DURUMDAN_verilir(tmp_path):
    """`write sys/unseal` çıkışı "istek kabul edildi" der, "mühür AÇILDI" demez: eşik >1 olan bir
    kasada ilk pay kabul edilir ama kasa mühürlü kalır; yanlış-sınıf bir anahtar da aynı
    görünebilir. Betik "açıldı"yı ancak `status` 0 dönünce söylemeli — aksi hâlde ExecStartPost
    başarı bildirir, birim `active` olur ve sırlar mühürlü bir kasadan İSTENİR (Agent düşer,
    alarm VAULT_SEALED'dan gelir, teşhis yanlış yerde başlar)."""
    r, argv_log, stdin_dosya = _unseal_kos(
        tmp_path, UNSEAL_SH, initialized=True, anahtar=SAHTE_DEGER, unseal_acar=False)
    assert stdin_dosya.exists(), "unseal isteği hiç gönderilmedi"
    assert r.returncode == 1, (
        f"kasa mühürlü kaldı ama çıkış {r.returncode} (1 bekleniyordu):\n{r.stdout}\n{r.stderr}")
    assert "BAŞARISIZ" in r.stdout, "mühürlü kalan kasa operatöre ADIYLA söylenmiyor"
    assert "mühür açıldı" not in r.stdout, "açılmamış mühür 'açıldı' diye raporlandı"
    assert SAHTE_DEGER not in argv_log.read_text(encoding="utf-8"), "DEĞER ARGV'YE SIZDI"


def test_C12_MUTASYON_durum_kontrolu_silinince_C11_KIRMIZI(tmp_path):
    """Çivi yeşili kanıt değildir: `&& [ "$(_durum_kodu)" = "0" ]` koşulu silinirse betik API
    cevabına güvenir ve mühürlü kasada "açıldı" der — C11 tam da bunu ısırmalı."""
    ham = UNSEAL_SH.read_text(encoding="utf-8")
    capa = ' && [ "$(_durum_kodu)" = "0" ]'
    assert capa in ham, "mutasyon çapası kaynakta yok"
    bozuk = tmp_path / "vault_unseal_bozuk.sh"
    bozuk.write_text(ham.replace(capa, ""), encoding="utf-8")
    bozuk.chmod(0o755)
    r, _, _ = _unseal_kos(tmp_path, bozuk, initialized=True, anahtar=SAHTE_DEGER, unseal_acar=False)
    assert r.returncode == 0 and "mühür açıldı" in r.stdout, (
        "MUTASYON ISIRMADI: durum kontrolü silinmiş betik hâlâ mühürlü kasayı yakalıyor — "
        f"C11 yanlış sebeple yeşil olurdu:\n{r.stdout}\n{r.stderr}")


# =================================================================================================
# D) vault-unseal.service · vault-agent.service · vault-sagligi.{service,timer}
# =================================================================================================

def test_D1_unseal_birimi_ONESHOT_ve_AYNI_betigi_cagirir():
    """Tek kaynak: elle/tekrar yolu ile ExecStartPost yolu AYNI betiği koşar. İki kopya olsaydı
    biri düzeltilir öteki bayatlardı."""
    assert BIRIM_UNSEAL.exists(), "deploy/vault/vault-unseal.service yok"
    assert _deger(BIRIM_UNSEAL, "Type") == "oneshot"
    assert _deger(BIRIM_UNSEAL, "ExecStart") == "/opt/vault/bin/vault_unseal.sh"
    assert _deger(BIRIM_VAULT, "ExecStartPost").lstrip("+") == _deger(BIRIM_UNSEAL, "ExecStart")


def test_D2_agent_ROOT_kosar_ve_SAPMA_beyanli():
    """SAPMA (Rol-1 kararı, plan Global Constraints): agent root koşar çünkü hedef dosyalar
    tasarım gereği 0400 root:root'tur; ayrı bir kullanıcıya vermek HEDEF DİZİNLERİ gevşetirdi.
    Sapma sessiz olamaz — birim dosyasının kendi şerhinde yazılıdır."""
    assert BIRIM_AGENT.exists(), "deploy/vault/vault-agent.service yok"
    kullanici = _deger(BIRIM_AGENT, "User")
    assert kullanici in (None, "root"), f"agent root koşmuyor: User={kullanici!r}"
    metin = BIRIM_AGENT.read_text(encoding="utf-8")
    assert "SAPMA" in metin, "root koşum sapması birim şerhinde beyan edilmemiş"


def test_D3_agent_yazma_yuzeyi_YALNIZ_hedef_dizinler():
    """Agent root koşuyor; `ProtectSystem=strict` + dar `ReadWritePaths` onun tek freni.
    Yol listesi sır hedeflerinin DİZİNLERİDİR, `/etc` değil."""
    yollar = (_deger(BIRIM_AGENT, "ReadWritePaths") or "").split()
    assert set(yollar) == {"/etc/meridian", "/etc/hindsight/creds"}, yollar


def test_D4_saglik_birimi_ve_timer_TEK_KADANS_kaynagi():
    """K7 sınıfı: kadans DEĞERİ yalnız timer'ın `OnUnitActiveSec=` satırında yaşar. Şerhte ya da
    `Description=`da tekrarlanan bir dakika değeri, kadans değişince sessizce YALAN olur."""
    assert BIRIM_SAGLIK.exists() and TIMER_SAGLIK.exists(), "sağlık birimi/timer yok"
    assert _deger(TIMER_SAGLIK, "OnUnitActiveSec") == "5min"
    ham = TIMER_SAGLIK.read_text(encoding="utf-8")
    serhler = [s for s in ham.splitlines()
               if s.strip().startswith("#") or s.strip().startswith("Description=")]
    for s in serhler:
        assert not re.search(r"\d+\s*(dk|min|dakika|sn|sa)\b", s), (
            f"kadans değeri şerhte/açıklamada tekrarlanıyor (K7): {s!r}"
        )


def test_D5_saglik_birimi_vault_KURULMADAN_atesleme_YAPMAZ():
    """Timer A0 rolüyle kurulduğu gün Vault henüz YOK olabilir. Koşulsuz bir bekçi o pencerede
    her tetikte VAULT_DOWN üretirdi — gerçek bir arıza değil, kurulum sırasının gürültüsü.
    `ConditionPathExists` birimi SESSİZCE değil, journal'a yazarak atlar."""
    kosul = _deger(BIRIM_SAGLIK, "ConditionPathExists")
    assert kosul == "/etc/vault/vault.hcl", f"kurulum kapısı yok/yanlış: {kosul!r}"


BIRIM_ADMIN_YENILE = VAULT_DIZIN / "vault-admin-yenile.service"
TIMER_ADMIN_YENILE = VAULT_DIZIN / "vault-admin-yenile.timer"
ADMIN_YENILE_SH = VAULT_DIZIN / "vault_admin_yenile.sh"


def test_D6_admin_yenileme_birimi_ve_timeri():
    """Yönetici jetonu PERİYODİK (`-period=720h`); yaşaması için periyot dolmadan `token renew`
    gerekir. Bu birim onu HAFTALIK yeniler (periyot 30 gün, haftalık = 4× emniyet); düşerse
    fail-notify alarmı (kurulu ≠ çalışır: kurulum günü elle test-ateşlenir)."""
    assert BIRIM_ADMIN_YENILE.exists(), "deploy/vault/vault-admin-yenile.service yok"
    assert TIMER_ADMIN_YENILE.exists(), "deploy/vault/vault-admin-yenile.timer yok"
    assert _deger(BIRIM_ADMIN_YENILE, "Type") == "oneshot"
    assert _deger(BIRIM_ADMIN_YENILE, "ExecStart") == "/opt/vault/bin/vault_admin_yenile.sh"
    assert _deger(BIRIM_ADMIN_YENILE, "ConditionFileNotEmpty") == "/etc/vault/admin.token", (
        "jeton dosyası yokken birim FAIL değil ATLANMALI (bootstrap öncesi yanlış alarm)")
    assert _deger(BIRIM_ADMIN_YENILE, "OnFailure") == "meridian-fail-notify.service"
    assert _deger(BIRIM_ADMIN_YENILE, "User") is None, "betik 0400 root dosyasını okur — root koşar"
    cal = _deger(TIMER_ADMIN_YENILE, "OnCalendar") or ""
    assert cal.startswith("Sun") or cal.startswith("weekly"), f"haftalık değil: {cal!r}"
    assert _deger(TIMER_ADMIN_YENILE, "Persistent") == "true", "kaçan tetik (kapalı makine) telafi edilmeli"
    assert _deger(TIMER_ADMIN_YENILE, "WantedBy") == "timers.target"


def test_D7_admin_yenileme_betigi_SIR_DISIPLINI():
    """Jeton STDIN'den (`login -no-print -`), argv/ortam YOK, `$(cat`/`read` YOK, `set -x` YOK,
    oturum yardımcısı çıkışta SİLİNİR (trap); yenileme `token renew` iledir ve HÜKÜM `renewable`+`ttl`
    ölçümünden gelir (yalnız sayı basılır)."""
    assert ADMIN_YENILE_SH.exists(), "deploy/vault/vault_admin_yenile.sh yok"
    assert os.access(ADMIN_YENILE_SH, os.X_OK), "çalıştırılabilir değil"
    r = subprocess.run(["bash", "-n", str(ADMIN_YENILE_SH)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    metin = _yorumsuz(ADMIN_YENILE_SH.read_text(encoding="utf-8"))
    assert re.search(r"login\s+-no-print\s+-\s*<", metin), "jeton stdin'den okunmuyor"
    assert "VAULT_TOKEN=" not in metin and "$(cat" not in metin and "$(<" not in metin
    assert not re.search(r"^\s*read\b", metin, re.M)
    assert not re.search(r"^\s*set\s+-[a-z]*x", metin, re.M)
    assert re.search(r"token\s+renew", metin), "yenileme komutu yok"
    assert re.search(r"trap\s+'rm -f \"\$\{HOME:-/root\}/\.vault-token\"'\s+EXIT", metin), "oturum çıkışta silinmiyor"
    for m_ in re.finditer(r"^\s*(?:echo|printf)\s+[^\n]*", metin, re.M):
        assert "$(" not in m_.group(0), f"çıktı satırında komut ikamesi: {m_.group(0)!r}"


def test_I16_kur_betigi_admin_yenileme_birimlerini_KURAR():
    """Adım 3 betiği (0750 root) ve iki birimi yerleştirir — aksi hâlde timer 'kurulu' görünür,
    A1'de dosya YOK olur (kurulu ≠ çalışır)."""
    metin = _yorumsuz(KUR_SH.read_text(encoding="utf-8"))
    assert "vault_admin_yenile.sh" in metin, "kur betiği yenileme betiğini kurmuyor"
    assert "vault-admin-yenile.service" in metin and "vault-admin-yenile.timer" in metin, (
        "kur betiği yenileme birim/timer'ını kurmuyor")


# =================================================================================================
# E) TEK KAYNAK — `deploy/sir_envanteri.yaml::vault_kv` (Task 2)
# =================================================================================================
# NEDEN ENVANTERE, KODA DEĞİL: Vault yolları, hedef dosyalar ve politikalar AYNI gerçeğin üç
# yüzüdür. Üçünü üç dosyaya elle yazmak, tek-kaynak yasasının ders kitabı ihlalidir (ve bu depo
# o dersi F9 başlık/liste vakasıyla zaten ödedi). Envanter VERİdir; politika ve agent
# yapılandırması ondan ÜRETİLİR.

ENVANTER = REPO / "deploy" / "sir_envanteri.yaml"
POLITIKA_DIZIN = VAULT_DIZIN / "policies"
POLITIKA_AGENT = POLITIKA_DIZIN / "meridian-agent.hcl"
POLITIKA_ADMIN = POLITIKA_DIZIN / "meridian-admin.hcl"
AGENT_HCL = VAULT_DIZIN / "agent.hcl"
URETICI = REPO / "ops" / "vault_politika_uret.py"

#: Dalga-1 kümesi (plan Global Constraints) — YEDİ tek-değer sırrı. Sayı burada ELLE durur ve
#: bu bilinçlidir: envanterden türetilseydi, envanterden bir satır düştüğünde çivi de onunla
#: birlikte küçülür ve "her şey uyuşuyor" derdi (v439 E0'ın pozitif-kontrol dersi).
DALGA1_SAYISI = 7


def _vault_kv() -> list[dict]:
    veri = yaml.safe_load(ENVANTER.read_text(encoding="utf-8"))
    assert "vault_kv" in veri, "deploy/sir_envanteri.yaml'da `vault_kv` bölümü yok (Task 2)"
    return veri["vault_kv"]


def test_E1_vault_kv_DALGA1_kumesini_tam_tasir():
    kv = _vault_kv()
    assert len(kv) == DALGA1_SAYISI, f"dalga-1 {DALGA1_SAYISI} sır bekliyordu, {len(kv)} var"
    for g in kv:
        assert set(g) == {"ad", "vault_yolu", "hedef", "mod", "sahip", "tuketici"}, (
            f"{g.get('ad')}: alan kümesi ayrışmış: {sorted(g)}"
        )


def test_E2_yol_ve_izin_semasi_TEK_BICIM():
    """Yol şeması `secret/meridian/<ad>` — istisnasız. Serbest yol yazımı, politika üretimini
    bir tahmin işine çevirirdi (politika `secret/data/meridian/<ad>` üretir ve KV-v2'de `data/`
    ara segmenti ZORUNLUDUR; şema bozulursa agent okuyamaz ama politika yine 'yazılmış' görünür).
    İzin 0400 root: hedef dosyaları systemd PID 1 olarak, sandbox'tan ÖNCE okur."""
    for g in _vault_kv():
        assert g["vault_yolu"] == f"secret/meridian/{g['ad']}", g
        assert g["mod"] == "0400", g
        assert g["sahip"] == "root", g
        assert g["hedef"].startswith("/etc/"), g


def test_E3_envanterde_DEGER_YOK_kurali_vault_kv_de_GECERLI():
    """v439 E4'ün aynı iddiası, yeni bölüm için: envanter yalnız AD ve YOL taşır. Çivi burada
    TEKRARLANIR çünkü v439 yalnız `dosyalar:` bloğunu geziyor — yeni bir blok onun kör noktası
    olurdu ve "envanterde değer yok" beyanı sessizce yarım kalırdı."""
    kv = _vault_kv()
    for g in kv:
        for alan, deger in g.items():
            assert not re.search(r"(?:^|[^A-Za-z])(sk-|hvs\.|Bearer\s)", str(deger)), (
                f"{g['ad']}.{alan} sır değeri taşıyor olabilir: {deger!r}"
            )


# =================================================================================================
# F) vault_kv ↔ mevcut `LoadCredential=` kaynakları — İKİ YÖNLÜ
# =================================================================================================

def _loadcredential_kaynaklari() -> set[str]:
    """deploy/ altındaki HER drop-in'den `LoadCredential=<kimlik>:<kaynak>` kaynaklarının kümesi.

    KAYNAKTAN ÖLÇÜLÜR, teste yazılmaz: Faz-1A/1B'nin ürettiği dosya kümesi bu depoda zaten
    YAZILIDIR ve ikinci bir liste sessizce ayrışırdı."""
    kaynaklar: set[str] = set()
    for conf in (REPO / "deploy").rglob("*.service.d/*.conf"):
        for satir in conf.read_text(encoding="utf-8").splitlines():
            s = satir.strip()
            if s.startswith("LoadCredential=") and ":" in s:
                kaynaklar.add(s.split("=", 1)[1].split(":", 1)[1].strip())
    return kaynaklar


def test_F1_her_LoadCredential_kaynagi_vault_kv_HEDEFIDIR():
    """YÖN 1: systemd'nin OKUDUĞU her dosya Vault'tan doldurulacak. Bir kaynak dışarıda kalırsa
    o sır Faz-2'den sonra da ELLE yönetiliyor demektir — ve bunu kimse fark etmezdi, çünkü
    dosya orada durmaya devam eder."""
    hedefler = {g["hedef"] for g in _vault_kv()}
    kaynaklar = _loadcredential_kaynaklari()
    assert kaynaklar, "hiç LoadCredential kaynağı bulunamadı — çivi kör"
    eksik = kaynaklar - hedefler
    assert not eksik, f"vault_kv'nin kapsamadığı LoadCredential kaynağı: {sorted(eksik)}"


def test_F2_LoadCredential_DISINDAKI_hedef_BEYANLI():
    """YÖN 2: bir hedef systemd'nin okuduğu bir kaynak DEĞİLSE, bunun sebebi `tuketici` alanında
    YAZILI olmalı. Beyansız bir hedef, "bu dosyayı kim okuyor" sorusunu cevapsız bırakırdı
    (Yasa 6). Bugün tek örnek APISIX yönetim anahtarıdır: onu bir birim değil, operatörün eliyle
    koştuğu bir ops aracı okur."""
    kaynaklar = _loadcredential_kaynaklari()
    for g in _vault_kv():
        if g["hedef"] in kaynaklar:
            assert "LoadCredential" in g["tuketici"], (
                f"{g['ad']}: systemd kaynağı ama tüketici beyanı bunu söylemiyor: {g['tuketici']!r}"
            )
        else:
            assert "LoadCredential" not in g["tuketici"], (
                f"{g['ad']}: LoadCredential beyanı var ama hiçbir drop-in bu dosyayı okumuyor "
                f"({g['hedef']}) — bayat beyan"
            )
            assert "ops/" in g["tuketici"], (
                f"{g['ad']}: systemd kaynağı DEĞİL ve okuyucusu beyan edilmemiş: {g['tuketici']!r}"
            )


def test_F3_agent_yazma_yuzeyi_envanterden_TURER():
    """`vault-agent.service` ReadWritePaths listesi, hedef dosyaların DİZİN kümesinden BİREBİR
    türemeli. Yeni bir sır başka bir dizine hedeflenip birim güncellenmezse Agent o dosyayı
    yazamaz — ve arıza, dosya ESKİ değerinde durduğu için ancak bir rotasyondan sonra görünür."""
    dizinler = {str(pathlib.PurePosixPath(g["hedef"]).parent) for g in _vault_kv()}
    beyan = set((_deger(BIRIM_AGENT, "ReadWritePaths") or "").split())
    assert beyan == dizinler, f"agent yazma yüzeyi envanterle ayrıştı: {beyan} ≠ {dizinler}"


# =================================================================================================
# G) ÜRETİLMİŞ DOSYALAR — üretici çıktısıyla BAYT EŞİT (Task 2)
# =================================================================================================
# `deploy/vault/policies/*.hcl` ve `deploy/vault/agent.hcl` ÜRETİLMİŞ dosyalardır. Elle
# düzenlenmiş bir üretilmiş dosya, bir sonraki üretimde sessizce geri alınır ve arada geçen
# sürede "değiştirdim" ile "yürürlükte" ayrışır. Emsal ve desen: `ops/jeton_css_uret.py` (v437).

def _uretici():
    from tests.conftest import betikten_modul_yukle
    return betikten_modul_yukle(URETICI, "vault_politika_uret")


def test_G1_uretici_VAR_ve_KOMUT_SATIRI_sozlesmesi():
    """Ops aracı sözleşmesi KOMUT SATIRIdır (CLAUDE.md §1). Çelişen bayrak çifti sessizce
    yutulmaz: `--kontrol --uygula` → çıkış 2 (ölçülmüş vaka sınıfı, 2026-08-30)."""
    assert URETICI.exists(), "ops/vault_politika_uret.py yok — Task 2 üreticisi üretilmedi"
    mod = _uretici()
    assert mod.main(["--kontrol", "--uygula"]) == 2, "çelişen bayrak çifti reddedilmiyor"


def test_G2_uc_dosya_da_URETICI_CIKTISIYLA_BAYT_ESIT():
    """Tazelik kapısının kendisi. Diskteki dosya üreticinin çıktısıyla BİREBİR aynı olmalı —
    'neredeyse aynı' diye bir hâl yoktur, çünkü üretim deterministiktir."""
    mod = _uretici()
    ayrisan = []
    for yol, icerik in mod.beklenen():
        if not yol.exists():
            ayrisan.append(f"{yol.name} (YOK)")
        elif yol.read_text(encoding="utf-8") != icerik:
            ayrisan.append(f"{yol.name} (BAYAT)")
    assert not ayrisan, (
        f"üretilmiş dosyalar üreticiyle ayrıştı: {ayrisan}. "
        "Yeniden üret: python ops/vault_politika_uret.py --uygula"
    )


def test_G3_kontrol_bayrak_GUNCEL_agacta_SIFIR_doner():
    assert _uretici().main(["--kontrol"]) == 0


def test_G4_uretilmis_dosyalar_BASLIK_ISARETI_tasir():
    """"Bu dosya üretilmiştir" beyanı DOSYANIN İÇİNDE durur. Yalnız testte durursa, dosyayı
    editörde açan mühendis onu elle düzenlemekten alıkonmaz."""
    for yol in (POLITIKA_AGENT, POLITIKA_ADMIN, AGENT_HCL):
        bas = yol.read_text(encoding="utf-8")[:600]
        assert "ÜRETİLDİ" in bas and "ops/vault_politika_uret.py" in bas, (
            f"{yol.name}: üretilmişlik işareti/kaynağı başlıkta yok"
        )


def test_G5_uretim_DETERMINISTIK_damgasiz():
    """İki koşum aynı baytı vermeli. Damga olsaydı `--kontrol` her koşumda 'bayat' derdi ve
    kapı gürültüye boğulup susturulurdu."""
    mod = _uretici()
    bir = {y.name: i for y, i in mod.beklenen()}
    iki = {y.name: i for y, i in mod.beklenen()}
    assert bir == iki
    for icerik in bir.values():
        assert not re.search(r"\b20\d{2}-\d{2}-\d{2}T", icerik), "çıktıda zaman damgası var"


# =================================================================================================
# H) ÜRETİLEN İÇERİK — politika ve şablonlar envanterle BİREBİR
# =================================================================================================

def test_H1_agent_politikasi_YALNIZ_envanter_yollarini_READ_eder():
    """İki yönlü: her sır bir `path` bloğu alır VE fazladan/joker bir yol YOKTUR. Joker bir
    politika, kasaya yarın konacak her sırrı da Agent'a açardı."""
    metin = POLITIKA_AGENT.read_text(encoding="utf-8")
    yollar = set(re.findall(r'^path\s+"([^"]+)"', metin, re.M))
    beklenen = {f"secret/data/meridian/{g['ad']}" for g in _vault_kv()}
    assert yollar == beklenen, f"agent politikası envanterle ayrıştı: {yollar ^ beklenen}"
    yetenekler = set(re.findall(r"capabilities\s*=\s*\[([^\]]*)\]", metin))
    assert yetenekler == {'"read"'}, f"agent politikasında okuma dışı yetenek: {yetenekler}"
    assert "*" not in metin.replace("*/", ""), "agent politikasında joker yol var"


def test_H2_admin_politikasi_YONETIM_yollarini_tasir():
    metin = POLITIKA_ADMIN.read_text(encoding="utf-8")
    yollar = set(re.findall(r'^path\s+"([^"]+)"', metin, re.M))
    assert "sys/health" in yollar, "sağlık okuması yok"
    assert "auth/approle/role/agent/secret-id" in yollar, "secret-id yenileme yolu yok"
    assert any(y.startswith("secret/data/meridian/") for y in yollar), "sır yazma yolu yok"
    assert any(y.startswith("secret/metadata/meridian/") for y in yollar), (
        "KV-v2 meta yolu yok — 'sildim ama duruyor' sınıfı"
    )


def test_H3_agent_sablon_HEDEFLERI_envanterle_BIREBIR():
    """Şablonun hedefi ile envanterin hedefi ayrışırsa Agent YANLIŞ dosyayı yazar — ve doğru
    dosya eski değerinde kalır. İki liste, tek gerçek: aralarında çivi."""
    metin = AGENT_HCL.read_text(encoding="utf-8")
    hedefler = re.findall(r'^\s*destination\s*=\s*"([^"]+)"', metin, re.M)
    beklenen = [g["hedef"] for g in _vault_kv()]
    assert hedefler == beklenen, f"şablon hedefleri envanterle ayrıştı: {hedefler} ≠ {beklenen}"
    modlar = re.findall(r"^\s*perms\s*=\s*(\S+)", metin, re.M)
    assert modlar == [g["mod"] for g in _vault_kv()], f"şablon izinleri ayrıştı: {modlar}"


def test_H4_agent_KASA_ADRESI_hcl_ile_TEK_KAYNAK():
    """Agent başka bir adrese bakarsa hiçbir zaman login olamaz — ve arıza "sır render
    edilmiyor" diye görünür, "yanlış adres" diye değil."""
    metin = AGENT_HCL.read_text(encoding="utf-8")
    m = re.search(r'address\s*=\s*"http://([^"]+)"', metin)
    assert m and m.group(1) == BEKLENEN_ADRES, f"agent kasa adresi: {m.group(1) if m else None!r}"


def test_H5_agent_APPROLE_bootstrap_dosyalari_ve_KALICILIK():
    """`remove_secret_id_file_after_reading = false` ZORUNLU: dosya silinirse Agent yeniden
    başladığında login EDEMEZ (secret_id_ttl=0 — kendiliğinden yenilenmez) ve sır render'ı
    sessizce durur (tasarım §6.3)."""
    metin = AGENT_HCL.read_text(encoding="utf-8")
    assert "/etc/vault/agent.role-id" in metin and "/etc/vault/agent.secret-id" in metin
    assert re.search(r"remove_secret_id_file_after_reading\s*=\s*false", metin), (
        "secret-id dosyası okunduktan sonra siliniyor — yeniden başlatmada login imkânsız"
    )


def test_H6_agent_BOS_RENDER_yapmaz():
    """Eksik anahtarda şablon BOŞ dosya yazsaydı, systemd o boş dosyayı "başarıyla yüklenmiş"
    bir credential sayardı ve tüketici 401 alırdı — arıza kasada değil uygulamada aranırdı."""
    metin = AGENT_HCL.read_text(encoding="utf-8")
    n = len(re.findall(r"error_on_missing_key\s*=\s*true", metin))
    assert n == len(_vault_kv()), f"eksik-anahtar kapısı {n} şablonda var, {len(_vault_kv())} olmalı"


def test_H7_agent_TUKETICIYI_YENIDEN_BASLATMAZ():
    """BİLEREK YOK: bir render'ın bakım penceresi dışında worker'ı düşürmesi hiçbir yerde
    verilmemiş bir yetkidir (tasarım §6.4 — restart operatörün reçetesinde)."""
    metin = AGENT_HCL.read_text(encoding="utf-8")
    for yasak in ("systemctl", "exec {", "command ="):
        assert yasak not in metin, f"agent yapılandırmasına emir yolu sızmış: {yasak!r}"


# =================================================================================================
# I) A1 BETİKLERİ — kaynak metni çivileri (Task 3)
# =================================================================================================
# Bu iki betik A1'de, `sudo` ile, bakım penceresinde koşar. Ajan onları YAZAR, KOŞTURMAZ
# (CLAUDE.md §3) — bu yüzden "gerçekten kurdu mu" burada ÖLÇÜLEMEZ. Ölçülebilen şey, betiğin
# SIR DİSİPLİNİDİR: değer argv'ye, ortama, journal'a girmiyor mu; kip bayrakları sessiz mi.

KUR_SH = VAULT_DIZIN / "vault_kur.sh"
KOY_SH = VAULT_DIZIN / "vault_sir_koy.sh"

#: Sahte sır — GERÇEK bir değer DEĞİL ve öyle görünmemeli. `SAHTE-` öneki bir konvansiyondur:
#: bir gün bu dize bir log'da görünürse, kimse onu döndürmeye koşmaz.
SAHTE_DEGER = "SAHTE-vault-faz2-degeri-0123456789"
#: Sahte yönetici jetonu — aynı konvansiyon; J4/J5/J6 bunu bir dosyaya yazar, betik stdin'den okur.
SAHTE_JETON = "SAHTE-vault-faz2-jetonu-9876543210"


def _sahte_jeton_dosyasi(tmp_path) -> pathlib.Path:
    """`VAULT_TOKEN_FILE` için tmp'de sahte yönetici jetonu (gerçek /etc/vault'a dokunulmaz)."""
    p = tmp_path / "admin.token"
    p.write_text(SAHTE_JETON + "\n", encoding="utf-8")
    return p


@pytest.mark.parametrize("betik", [KUR_SH, KOY_SH], ids=["vault_kur", "vault_sir_koy"])
def test_I1_betikler_sozdizimi_ve_calistirilabilir(betik):
    assert betik.exists(), f"{betik.name} yok — Task 3 çıktısı üretilmedi"
    assert os.access(betik, os.X_OK), f"{betik.name} çalıştırılabilir değil"
    r = subprocess.run(["bash", "-n", str(betik)], capture_output=True, text=True)
    assert r.returncode == 0, f"{betik.name}: bash -n düştü: {r.stderr}"


@pytest.mark.parametrize("betik", [KUR_SH, KOY_SH], ids=["vault_kur", "vault_sir_koy"])
def test_I2_set_x_YOK(betik):
    """`set -x` her komutu (yönlendirme hedefleri ve boru gövdeleri dahil) journal'a döker.
    Bu iki betik sır DOSYALARIYLA çalışır; izleme çıktısı bir sızıntı kanalıdır."""
    metin = _yorumsuz(betik.read_text(encoding="utf-8"))
    assert not re.search(r"^\s*set\s+-[a-z]*x", metin, re.M), f"{betik.name}: set -x açık"


def test_I3_kur_betigi_INIT_ciktisini_DEGISKENE_ALMAZ():
    """`operator init` çıktısı unseal anahtarını VE kök jetonunu taşır. Bir kabuk değişkenine
    alınsaydı değer betiğin geri kalanı boyunca yaşar; bir hata mesajı ya da sonradan eklenen
    bir `set -x` onu ifşa ederdi. Doğru biçim: BORU ile doğrudan yazıcıya."""
    metin = _yorumsuz(KUR_SH.read_text(encoding="utf-8"))
    # KURU KOŞUMUN ANLATIM SATIRI (`kuru "vault operator init …"`) BİR ÇAĞRI DEĞİLDİR ve onu
    # ölçmek çiviyi kör ederdi: metin eşleşir, davranış ölçülmez. GERÇEK çağrı `"$VAULT_BIN"`
    # ile başlar — ayrım budur.
    m = re.search(r'^[^\n#]*"\$VAULT_BIN"\s+operator\s+init[^\n]*', metin, re.M)
    assert m, "gerçek `operator init` çağrısı bulunamadı (yalnız anlatım satırı mı var?)"
    satir = m.group(0)
    assert "|" in satir or satir.rstrip().endswith("\\"), (
        f"init çıktısı boruya verilmiyor: {satir!r}"
    )
    assert not re.search(r"\w+\s*=\s*\$\(\s*[\"']?\$?\w*[\"']?\s*[^)]*operator\s+init", metin), (
        "init çıktısı bir değişkene atanıyor"
    )


def test_I4_kur_betigi_JETONU_STDIN_den_okur():
    """Kök jetonuyla oturum: `vault login -no-print -` jetonu STDIN'den alır. `VAULT_TOKEN=$(cat …)`
    biçimi onu alt sürecin ORTAMINA koyardı ve ortam `/proc/<pid>/environ`da yaşar."""
    metin = _yorumsuz(KUR_SH.read_text(encoding="utf-8"))
    assert re.search(r"login\s+-no-print\s+-", metin), "kök jetonu stdin'den okunmuyor"
    assert "VAULT_TOKEN=" not in metin, "jeton ortam değişkenine konuyor"


def test_I5_kur_betigi_DOSYALARI_0400_OLARAK_YARATIR():
    """`umask 377` dosyayı 0400 OLARAK YARATIR. Önce 0644 yaratıp sonra `chmod 0400` yapmak bir
    YARIŞ PENCERESİ açar: iki çağrı arasında dosya makinedeki herkese okunabilirdir."""
    metin = _yorumsuz(KUR_SH.read_text(encoding="utf-8"))
    for hedef in ("agent.role-id", "agent.secret-id", "admin.token"):
        satirlar = [s for s in metin.splitlines() if hedef in s and ">" in s]
        assert satirlar, f"{hedef} yazımı bulunamadı"
        for s in satirlar:
            assert "umask 377" in s, f"{hedef} 0400 olarak YARATILMIYOR: {s!r}"


VAULT_ZIP_SHA256_OLCULEN = "319b3eb7b0c2ad218453f5d1af5c23cac81a024db3a07ccd2494ecd31f2090c3"
# ÖLÇÜLDÜ 2026-09-14 (Rol-1, A1): releases.hashicorp.com/vault/2.1.0/vault_2.1.0_SHA256SUMS linux_arm64 satırı,
# A1'de `sha256sum -c` OK, `vault version` v2.1.0 (cb6a54fa…). Ajan nöbetçi değerde bırakmıştı (ağa çıkmaz);
# Rol-1 doldurdu. Sürüm/sha değişirse betik ve bu sabit BİRLİKTE (tek gerçek, iki kopya → ayrışma çivisi aşağıda).


def test_I6_kur_betigi_TEDARIK_KAPISI_olculen_sha_pinli():
    """Uydurma yasağının bu dosyadaki karşılığı: sha256 TAHMİN EDİLMEZ — ajan nöbetçi (`OLCULMEDI`)
    bırakmıştı, Rol-1 A1'de HashiCorp SHA256SUMS'tan ÖLÇÜP doldurdu (2026-09-14). Çivi: betikteki pin
    64 hex VE bu dosyadaki ölçülen değerle BİREBİR (iki kopya sessizce ayrışmasın); nöbetçi kapısı ve
    doldurma reçetesi betikte KALIR (sürüm yükseltmesinde yine nöbetçiden geçilir)."""
    metin = KUR_SH.read_text(encoding="utf-8")
    m = re.search(r'VAULT_ZIP_SHA256="\$\{VAULT_ZIP_SHA256:-([0-9a-f]{64})\}"', metin)
    assert m, "sha256 pini 64 hex değil — nöbetçi (OLCULMEDI) ya da bozuk değer"
    assert m.group(1) == VAULT_ZIP_SHA256_OLCULEN, "betikteki pin ölçülen değerden AYRIŞTI"
    assert 'if [ "$VAULT_ZIP_SHA256" = "OLCULMEDI" ]' in metin, "nöbetçi kapısı betikten silinmiş"
    assert "SHA256SUMS" in metin, "nöbetçiyi dolduracak REÇETE betikte yazılı değil"


def test_I7_koy_betigi_DEGERI_BORUDAN_gecirir():
    """`vault kv put <yol> value=-` değeri STDIN'den okur. `value="$X"` biçimi onu argv'ye
    koyardı ve argv `/proc/<pid>/cmdline`de makinedeki HER kullanıcıya açıktır."""
    metin = _yorumsuz(KOY_SH.read_text(encoding="utf-8"))
    assert re.search(r"kv\s+put\s+\"\$yol\"\s+value=-", metin), "değer stdin'den geçmiyor"
    assert not re.search(r"value=[\"']?\$(?!\{?yol)", metin), "değer argv'ye konuyor"


def test_I14_kur_betigi_YONETICI_JETONUNU_ORPHAN_yaratir():
    """Ölçülen arıza (A1 2026-09-14 10:10Z): kök jetonu iptal edilince (adım 11) Vault ÇOCUK jetonları
    da iptal eder; `-orphan`sız yaratılan yönetici jetonu kök iptaliyle gitti (lookup-self 403
    'invalid token') — kasa yönetimsiz kaldı; agent AppRole bağımsız olduğu için canlı etkilenmedi.
    Çivi: gerçek yaratma satırı VE kuru koşum satırı `-orphan` taşır (ikisi ayrışmasın)."""
    metin = _yorumsuz(KUR_SH.read_text(encoding="utf-8"))
    satirlar = [s for s in metin.splitlines() if "token create" in s]
    assert satirlar, "token create satırı yok"
    for s in satirlar:
        assert "-orphan" in s, f"yönetici jetonu -orphan DEĞİL (kök iptali onu da götürür): {s.strip()!r}"
        # TUR-4 (ölçüldü 2026-09-14 15:1xZ): `-ttl=720h` ile yaratılan jeton `token renew` ile en fazla
        # SİSTEM AZAMİ TTL'sine (varsayılan 768 sa, yaratılıştan itibaren) uzatılır — yani aylık yenileme
        # onu kurtarmaz, 32. gün ölür ve kasa yönetimsiz kalır. PERİYODİK jeton (`-period=720h`) her
        # yenilemede periyodu baştan alır: süresiz yaşar, yenileme timer'ı (vault-admin-yenile) yeter.
        assert "-period=720h" in s, f"yönetici jetonu PERİYODİK değil (`-period=720h` yok): {s.strip()!r}"
        assert "-ttl=" not in s, f"`-ttl=` ile yaratılan jeton azami TTL'de ölür — period kullan: {s.strip()!r}"


def test_I15_kok_iptali_ONCE_orphan_OLCER_SONRA_yonetici_oturumunu_SINAR():
    """Kök iptali bu kurulumun tek geri alınamaz adımıdır. İki kapı, iki ayrı arıza:
    (ön) yönetici jetonu orphan değilse iptal onu da götürür → iptalden ÖNCE `orphan` ölçülür;
    (son) iptalden SONRA yönetici jetonuyla oturum sınanır (kurulu ≠ çalışır). Sıra ölçülür:
    orphan ölçümü < revoke < iptal-sonrası oturum. Jeton her yerde stdin'den (I4 disiplini)."""
    metin = _yorumsuz(KUR_SH.read_text(encoding="utf-8"))
    i_orphan = metin.find('"orphan": *true')
    # GERÇEK komut satırı aranır ("$VAULT_BIN" önekli): kuru kipin `kuru "vault token revoke …"`
    # mesajı aynı metni daha ÖNCE taşır ve çıplak arama kapıyı yanlış sebeple kırmızı yapar (ölçüldü).
    i_revoke = metin.find('"$VAULT_BIN" token revoke -self')
    assert i_orphan != -1 and i_revoke != -1, "orphan ölçümü ya da revoke satırı yok"
    assert i_orphan < i_revoke, "orphan ölçümü revoke'tan SONRA — kapı işe yaramaz"
    son_login = metin.rfind('login -no-print - < "$ETC/admin.token"')
    assert son_login > i_revoke, "iptal sonrası yönetici oturumu sınanmıyor"
    assert re.search(r"token lookup -format=json \| grep -q", metin), "orphan alanı jetonu argv'ye koymadan ölçülmüyor"


def test_I13_koy_betigi_KIMLIGI_STDIN_den_kurar_ve_ORTAMA_KOYMAZ():
    """TUR-3 (ölçülen arıza, A1 2026-09-14 09:55Z): betik ortamdaki oturuma güveniyordu; kur betiği
    o oturumu sonunda sildiği için jetonsuz koştu ve `kv put` 403 aldı — I7/J4 yeşilken. Kimlik
    AÇIKÇA ve I4 ile aynı disiplinle kurulur: `login -no-print -` (stdin), `VAULT_TOKEN=` YOK,
    `$(cat` YOK; oturum çıkışta silinir (trap)."""
    metin = _yorumsuz(KOY_SH.read_text(encoding="utf-8"))
    assert re.search(r"login\s+-no-print\s+-\s*<", metin), "yönetici jetonu stdin'den okunmuyor"
    assert "VAULT_TOKEN=" not in metin, "jeton ortam değişkenine konuyor"
    assert "$(cat" not in metin and "$(<" not in metin, "jeton komut ikamesiyle okunuyor"
    assert re.search(r"trap\s+'rm -f \"\$\{HOME:-/root\}/\.vault-token\"'\s+EXIT", metin), (
        "oturum çıkışta silinmiyor (kalıcı yönetici oturumu)")


def test_I8_koy_betigi_LISTESINI_ENVANTERDEN_turetir():
    """İkinci bir liste, envantere eklenen bir sırrın bu betikte sessizce eksik kalması demektir."""
    metin = _yorumsuz(KOY_SH.read_text(encoding="utf-8"))
    assert "vault_kv" in metin and "sir_envanteri.yaml" in metin, (
        "betik envanteri okumuyor — liste elle yazılmış olabilir"
    )
    for g in _vault_kv():
        assert g["ad"] not in metin, f"{g['ad']} betiğe ELLE yazılmış (ikinci kaynak)"


# -------------------------------------------------------------------------------------------------
# I9-I11 — ZIP AÇICI: İKİ YOL (TUR 2, A1 ilk kurulumunda ÖLÇÜLEN eksik 2026-09-14)
# -------------------------------------------------------------------------------------------------
# ÖLÇÜLEN EKSİK: A1'de `unzip` KURULU DEĞİLDİ ve adım 1 tam da sha256'sı doğrulanmış zip'i
# açacağı yerde düştü (Rol-1 apt ile kurdu, kurulum elle ilerledi). Düzeltme ÇİFTTİR ve iki
# parçası AYRI sorunu çözer:
#   (a) A0 rolü paket listesine `unzip` girdi → bir dahaki TEMİZ kurulumda eksik DOĞMAZ;
#   (b) betik stdlib'e düşer (python3 zipfile) → kasa kurulumu bir BAKIM PENCERESİNDE koşar ve
#       orada "önce apt-get install" demek pencereyi uzatır.
# Yalnız (a) yapılsaydı rolü koşmamış bir makinede aynı arıza tekrarlardı; yalnız (b) yapılsaydı
# A1 kalıcı olarak fallback yolunda kalır ve eksik hiç görünmezdi.

#: `bash`in MUTLAK yolu — kısıtlı PATH'te `bash` aranamaz (çözüm yolu, test-only kolaylık değil:
#: kısıtlama ölçülen şeyin kendisidir, koşturucunun bulunabilirliği değil).
_BASH = shutil.which("bash") or "/bin/bash"


def _min_path(tmp_path, *, unzip: bool, python3: bool) -> str:
    """`--kuru` koşumunun ihtiyaç duyduğu komutlardan KÜRATE edilmiş bir PATH.

    Amaç `unzip`in VAR/YOK olduğu iki dünyayı ölçmek. Gerçek PATH'i kullanıp `unzip`i "yok
    saymak" mümkün değil: `command -v` PATH'i tarar ve gerçek ikiliyi bulurdu."""
    binler = tmp_path / "min-bin"
    binler.mkdir(exist_ok=True)
    gerekli = ["bash", "id", "install", "useradd", "systemctl", "sha256sum", "shasum", "tr",
               "grep", "sed", "cat", "rm", "mkdir", "chmod", "chown", "date", "sleep", "uname",
               "env", "dirname", "basename", "pwd", "ls", "cp", "mv", "printf", "echo", "test"]
    if unzip:
        gerekli.append("unzip")
    if python3:
        gerekli.append("python3")
    for ad in gerekli:
        kaynak = shutil.which(ad)
        if kaynak and not (binler / ad).exists():
            (binler / ad).symlink_to(kaynak)
    return str(binler)


@pytest.mark.parametrize("unzip,python3,beklenen,ad", [
    (True, True, "aç (unzip)", "unzip varsa BİRİNCİ yol"),
    (False, True, "aç (python3-zipfile)", "unzip yoksa stdlib"),
])
def test_I9_KURU_kosum_ACICIYI_ADIYLA_secer(tmp_path, unzip, python3, beklenen, ad):
    """Operatör bakım penceresinde HANGİ yolun koşacağını kuru koşumdan okumalı. "Açılır"
    demek yetmez: iki yolun arıza yüzeyi farklıdır ve hangisinin seçildiği görünmezse, düşen
    kurulumda yanlış araç aranır."""
    ortam = dict(os.environ, PATH=_min_path(tmp_path, unzip=unzip, python3=python3),
                 VAULT_BIN=str(tmp_path / "yok" / "vault"))
    r = subprocess.run([_BASH, str(KUR_SH), "--kuru"], capture_output=True, text=True, env=ortam)
    assert r.returncode == 0, f"kuru koşum düştü ({ad}):\n{r.stdout}\n{r.stderr}"
    assert beklenen in r.stdout, f"kuru koşum açıcıyı ADIYLA söylemiyor ({ad}):\n{r.stdout}"


def test_I10_IKISI_DE_YOKSA_kuru_kosum_EKSIGI_ve_RECETEYI_basar(tmp_path):
    """ÜÇÜNCÜ, SESSİZ BİR YOL YOKTUR. Kuru koşumun işi eksikleri GÖSTERMEKTİR (betiğin kendi
    başlığındaki kural) — ve bu eksik, `--uygula` kipinde betiği DURDURAN sınıftandır."""
    ortam = dict(os.environ, PATH=_min_path(tmp_path, unzip=False, python3=False),
                 VAULT_BIN=str(tmp_path / "yok" / "vault"))
    r = subprocess.run([_BASH, str(KUR_SH), "--kuru"], capture_output=True, text=True, env=ortam)
    assert "EKSİK" in r.stdout, f"açıcı eksikliği kuru koşumda GÖRÜNMÜYOR:\n{r.stdout}"
    assert "apt-get install -y unzip" in r.stdout, "reçete basılmıyor (operatör ne yapacak?)"
    metin = _yorumsuz(KUR_SH.read_text(encoding="utf-8"))
    assert re.search(r"\*\)\s*die[^\n]*(?:AÇILAMIYOR|acilamiyor)", metin), (
        "`--uygula` kipinde açıcısız dal DURDURMUYOR — yarım kurulum sessizce ilerlerdi")


def test_I11_PYTHON_KOLU_GERCEK_bir_zipi_ACAR(tmp_path):
    """Aracı OPERATÖRÜN KOŞACAĞI BİÇİMDE bir kez koş (CLAUDE.md §6, `--uygula` vakası).

    Fallback kolu bir tek satırdır ve tırnaklaması bozuksa arıza ANCAK bakım penceresinde,
    doğrulanmış zip elde dururken görünür. Bu yüzden çivi satırı KAYNAKTAN SÖKER ve gerçek bir
    zip'le koşar — "yazılmış mı" değil, "açıyor mu"."""
    metin = KUR_SH.read_text(encoding="utf-8")
    m = re.search(r"python3\s+-c\s+'([^']+)'", metin)
    assert m, "fallback tek satırı kaynakta bulunamadı (çivi hedefini kaybetmiş)"
    zip_yolu = tmp_path / "ornek.zip"
    with zipfile.ZipFile(zip_yolu, "w") as z:
        z.writestr("vault", "#!/bin/sh\necho sahte-vault\n")
    hedef = tmp_path / "acilan"
    r = subprocess.run([sys.executable, "-c", m.group(1), str(zip_yolu), str(hedef)],
                       capture_output=True, text=True)
    assert r.returncode == 0, f"fallback tek satırı düştü:\n{r.stdout}\n{r.stderr}"
    assert (hedef / "vault").is_file(), "fallback zip'i açmadı — `vault` çıkmadı"


def test_I12_MUTASYON_fallback_kolu_silinince_KIRMIZI(tmp_path):
    """Çivi yeşili kanıt değildir: fallback dalı kaldırılırsa I9(b) kırmızı olmalı — yani o
    test gerçekten ikinci yolu ölçüyor, yalnız metin eşleştirmiyor."""
    ham = KUR_SH.read_text(encoding="utf-8")
    capa = 'elif command -v python3'
    assert capa in ham, f"mutasyon çapası kaynakta yok: {capa!r}"
    bozuk = tmp_path / "vault_kur_bozuk.sh"
    bozuk.write_text(ham.replace(capa, 'elif command -v python3-YOK-EDILDI'), encoding="utf-8")
    ortam = dict(os.environ, PATH=_min_path(tmp_path, unzip=False, python3=True),
                 VAULT_BIN=str(tmp_path / "yok" / "vault"))
    r = subprocess.run([_BASH, str(bozuk), "--kuru"], capture_output=True, text=True, env=ortam)
    assert "aç (python3-zipfile)" not in r.stdout, (
        f"MUTASYON ISIRMADI: fallback kolu silinmiş betik hâlâ python3 yolunu SEÇİYOR — "
        f"çivi yanlış sebeple yeşil:\n{r.stdout}")
    assert "EKSİK" in r.stdout, (
        f"mutasyon sonrası betik ne fallback'e ne de EKSİK dalına düştü — ölçüm belirsiz:"
        f"\n{r.stdout}")

# =================================================================================================
# J) DAVRANIŞ ÇİVİLERİ — `--kuru` yolları, sahte `vault` ile (Task 3)
# =================================================================================================
# Yerelde `vault` ikilisi YOKTUR. Bu bölüm gerçek bir kasayla konuşmaz; ölçtüğü şey betiğin
# KENDİ davranışıdır: kuru koşum GERÇEKTEN hiçbir şey yapıyor mu, ve uygula yolunda değer
# GERÇEKTEN argv'ye girmiyor mu. İkincisi kaynak-metni çivisinin (I7) DAVRANIŞSAL kanıtıdır:
# regex "yazılmış mı" der, bu test "oluyor mu" der.

def _stub_kur(tmp_path, *adlar: str) -> tuple[pathlib.Path, pathlib.Path]:
    """PATH'e konacak sahte komutlar. Her çağrı `cagrilar.log`a ARGV'siyle yazılır.

    Sahte komut MUTASYON YAPMAZ; varlığının tek amacı "çağrıldı mı" sorusunu ölçmektir. Kuru
    koşumun iddiası tam olarak budur: hiçbiri çağrılmamalı."""
    binler = tmp_path / "sahte-bin"
    binler.mkdir(exist_ok=True)
    log = tmp_path / "cagrilar.log"
    for ad in adlar:
        betik = binler / ad
        betik.write_text(f'#!/usr/bin/env bash\necho "{ad} $*" >> "{log}"\nexit 0\n')
        betik.chmod(0o755)
    return binler, log


def test_J1_kur_KURU_kosumu_HICBIR_mutasyon_komutu_CAGIRMAZ(tmp_path):
    """Kuru koşumun tek iddiası: HİÇBİR ŞEY YAPMAM. Bunu "çıktıda (kuru) yazıyor" diye ölçmek
    yetmez — mutasyon yapan komutları PATH'te sahteleriyle değiştirip çağrılıp çağrılmadıklarına
    bakmak, iddiayı DAVRANIŞSAL olarak ölçer."""
    binler, log = _stub_kur(tmp_path, "systemctl", "useradd", "install", "unzip", "sha256sum")
    ortam = dict(os.environ, PATH=f"{binler}:{os.environ['PATH']}",
                 VAULT_BIN=str(tmp_path / "yok" / "vault"))
    r = subprocess.run([_BASH, str(KUR_SH), "--kuru"], capture_output=True, text=True, env=ortam)
    assert r.returncode == 0, f"kuru koşum düştü (rc={r.returncode}):\n{r.stdout}\n{r.stderr}"
    assert not log.exists(), f"kuru koşum mutasyon komutu çağırdı:\n{log.read_text()}"
    assert "(kuru)" in r.stdout, "kuru koşum ne yapacağını basmıyor"
    # sha pini ÖLÇÜLDÜ (Rol-1 2026-09-14, bkz. VAULT_ZIP_SHA256_OLCULEN): kuru koşum artık nöbetçi uyarısı
    # değil sha doğrulama adımını basar; nöbetçi dalı I6 çivisiyle korunur.
    assert "sha256" in r.stdout and "TEDARİK KAPISI AÇIK DEĞİL" not in r.stdout, (
        "kuru koşum sha doğrulama adımını basmıyor ya da nöbetçi dalına düşmüş")


def test_J2_kur_KIPSIZ_kosum_KULLANIM_hatasi(tmp_path):
    """Bu betik kip SEÇTİRİR. Varsayılan bir kip (hangisi olursa olsun) yanlış olurdu: `--kuru`
    varsayılsa operatör "kurdum" sanır, `--uygula` varsayılsa bir yazım hatası kasayı kurar."""
    r = subprocess.run(["bash", str(KUR_SH)], capture_output=True, text=True)
    assert r.returncode == 2, f"kipsiz koşum çıkış {r.returncode} (2 bekleniyordu)"
    r2 = subprocess.run(["bash", str(KUR_SH), "--kuru", "--uygula"], capture_output=True, text=True)
    assert r2.returncode != 0, "çelişen kip çifti kabul edildi"


def _gecici_envanter(tmp_path) -> tuple[pathlib.Path, pathlib.Path]:
    """Kaynak dosyaları tmp'de olan KÜÇÜK bir envanter — gerçek `/etc` yollarına dokunulmaz."""
    kaynak = tmp_path / "kaynaklar"
    kaynak.mkdir(exist_ok=True)
    hedef = kaynak / "dash_token"
    hedef.write_text(SAHTE_DEGER + "\n", encoding="utf-8")
    env = tmp_path / "envanter.yaml"
    env.write_text(yaml.safe_dump({"vault_kv": [{
        "ad": "dash_token", "vault_yolu": "secret/meridian/dash_token",
        "hedef": str(hedef), "mod": "0400", "sahip": "root", "tuketici": "test"}]}),
        encoding="utf-8")
    return env, hedef


def test_J3_koy_KURU_kosumu_KASAYA_HIC_DOKUNMAZ(tmp_path):
    """Kuru koşum kasaya tek bir çağrı bile yapmamalı: `--kuru` bir ÖN İZLEME'dir, yarım bir
    yazım değil."""
    binler, log = _stub_kur(tmp_path, "vault")
    env_yaml, _ = _gecici_envanter(tmp_path)
    ortam = dict(os.environ, PATH=f"{binler}:{os.environ['PATH']}",
                 VAULT_BIN=str(binler / "vault"), ENVANTER=str(env_yaml),
                 PYTHON_BIN=sys.executable)
    r = subprocess.run(["bash", str(KOY_SH), "--kuru"], capture_output=True, text=True, env=ortam)
    assert r.returncode == 0, f"kuru koşum düştü:\n{r.stdout}\n{r.stderr}"
    assert not log.exists(), f"kuru koşum kasaya çağrı yaptı:\n{log.read_text()}"
    assert "secret/meridian/dash_token" in r.stdout, "kuru koşum planı basmıyor"


def test_J4_koy_UYGULA_yolunda_DEGER_ARGV_ye_GIRMEZ(tmp_path):
    """BU TESTİN ÖLÇTÜĞÜ ŞEY BİR SIZINTIDIR, bir özellik değil.

    Sahte `vault` her çağrısını ARGV'siyle log'lar ve `kv put` için stdin'i saklar. Sonra İKİ
    şey ölçülür: (a) değer argv log'unda HİÇ geçmiyor, (b) buna rağmen kasaya GERÇEKTEN ulaşmış
    (stdin dosyasında). Yalnız (a) ölçülseydi, hiçbir şey göndermeyen bir betik de geçerdi."""
    binler = tmp_path / "sahte-bin"
    binler.mkdir(exist_ok=True)
    argv_log = tmp_path / "argv.log"
    kasa = tmp_path / "kasa.deger"
    (binler / "vault").write_text(f"""#!/usr/bin/env bash
echo "$*" >> "{argv_log}"
if [ "$1" = "kv" ] && [ "$2" = "put" ]; then cat > "{kasa}"; exit 0; fi
if [ "$1" = "kv" ] && [ "$2" = "get" ]; then cat "{kasa}"; exit 0; fi
exit 0
""")
    (binler / "vault").chmod(0o755)
    env_yaml, kaynak = _gecici_envanter(tmp_path)
    ortam = dict(os.environ, PATH=f"{binler}:{os.environ['PATH']}",
                 VAULT_BIN=str(binler / "vault"), ENVANTER=str(env_yaml),
                 PYTHON_BIN=sys.executable, HOME=str(tmp_path),
                 VAULT_TOKEN_FILE=str(_sahte_jeton_dosyasi(tmp_path)))
    r = subprocess.run(["bash", str(KOY_SH), "--uygula"], capture_output=True, text=True, env=ortam)
    assert r.returncode == 0, f"uygula düştü:\n{r.stdout}\n{r.stderr}"
    # (a) SIZINTI YOK — ne değer ne jeton argv'de; oturum İLK çağrı ve stdin'den (tur-3, I13'ün davranışı)
    argv = argv_log.read_text(encoding="utf-8")
    assert SAHTE_DEGER not in argv, "DEĞER ARGV'YE SIZDI"
    assert SAHTE_JETON not in argv, "JETON ARGV'YE SIZDI"
    assert argv.splitlines()[0] == "login -no-print -", (
        f"kasaya ilk çağrı oturum açma değil (jetonsuz kv put = ölçülen 403):\n{argv}")
    assert SAHTE_DEGER not in r.stdout and SAHTE_DEGER not in r.stderr, "DEĞER TERMİNALE BASILDI"
    # (b) AMA GERÇEKTEN GİTTİ — ve son satır sonu kırpılmış (kanonik biçim)
    assert kasa.read_text(encoding="utf-8") == SAHTE_DEGER, (
        "değer kasaya ulaşmadı ya da son satır sonu kırpılmadı"
    )
    assert "sha256 eşleşti" in r.stdout, "doğrulama kolu koşmadı"


def test_J5_koy_UYGULA_SHA_UYUSMAZSA_DURUR(tmp_path):
    """Doğrulama bir SÜS DEĞİL bir KAPIDIR: kasadaki değer kaynakla aynı değilse betik DURMALI.
    Yarım bir taşıma, Agent'ın YANLIŞ değeri render etmesi demektir — ve o arıza, bir sonraki
    restart'a kadar sessizdir."""
    binler = tmp_path / "sahte-bin"
    binler.mkdir(exist_ok=True)
    (binler / "vault").write_text("""#!/usr/bin/env bash
if [ "$1" = "kv" ] && [ "$2" = "put" ]; then cat > /dev/null; exit 0; fi
if [ "$1" = "kv" ] && [ "$2" = "get" ]; then echo "BASKA-DEGER"; exit 0; fi
exit 0
""")
    (binler / "vault").chmod(0o755)
    env_yaml, _ = _gecici_envanter(tmp_path)
    ortam = dict(os.environ, PATH=f"{binler}:{os.environ['PATH']}",
                 VAULT_BIN=str(binler / "vault"), ENVANTER=str(env_yaml),
                 PYTHON_BIN=sys.executable, HOME=str(tmp_path),
                 VAULT_TOKEN_FILE=str(_sahte_jeton_dosyasi(tmp_path)))
    r = subprocess.run(["bash", str(KOY_SH), "--uygula"], capture_output=True, text=True, env=ortam)
    assert r.returncode != 0, "sha256 uyuşmazlığı BETİĞİ DURDURMADI"
    assert "UYUŞMADI" in r.stdout, "uyuşmazlık operatöre ADIYLA söylenmiyor"


def test_J6_koy_UYGULA_JETON_DOSYASI_YOKSA_kasaya_DOKUNMADAN_durur(tmp_path):
    """Jetonsuz `--uygula`, tur-2'de tam olarak ölçülen arızadır (403). Şimdi betik kasaya tek çağrı
    yapmadan, ADIYLA durmalı — "permission denied" değil, "yönetici jetonu yok" demeli."""
    binler, log = _stub_kur(tmp_path, "vault")
    env_yaml, _ = _gecici_envanter(tmp_path)
    ortam = dict(os.environ, PATH=f"{binler}:{os.environ['PATH']}",
                 VAULT_BIN=str(binler / "vault"), ENVANTER=str(env_yaml),
                 PYTHON_BIN=sys.executable, HOME=str(tmp_path),
                 VAULT_TOKEN_FILE=str(tmp_path / "yok.token"))
    r = subprocess.run(["bash", str(KOY_SH), "--uygula"], capture_output=True, text=True, env=ortam)
    assert r.returncode != 0, "jetonsuz uygula DURMADI"
    assert "yönetici jetonu yok" in r.stderr, f"arıza ADIYLA söylenmiyor:\n{r.stderr}"
    assert not log.exists(), f"jetonsuz betik kasaya çağrı yaptı:\n{log.read_text()}"


# =================================================================================================
# L) BEKÇİ — `ops/vault_sagligi.py` DAVRANIŞI (Task 4)
# =================================================================================================
# Bu bölüm SAHTE BİR HTTP SUNUCUSUYLA konuşur, gerçek bir Vault ile değil. Ölçtüğü şey kasanın
# davranışı değil BEKÇİNİN HÜKMÜdür: hangi HTTP kodu hangi alarma çevriliyor. O eşleme bu
# turun tek yeni karar yüzeyidir ve yanlış eşleme, mühürlü bir kasayı "ulaşılamıyor" diye
# raporlamak demektir (operatör yanlış yerde arar).

BEKCI = REPO / "ops" / "vault_sagligi.py"


def _saglik_sunucusu(kod: int):
    """127.0.0.1'de, verilen kodu dönen tek uçlu bir sunucu. (adres, kapat) döner."""
    import http.server
    import threading

    class _H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):                                   # noqa: N802 (stdlib sözleşmesi)
            self.send_response(kod)
            self.send_header("Content-Length", "0")
            self.end_headers()

        def log_message(self, *a):                          # test çıktısını kirletmesin
            return

    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _H)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    return f"http://127.0.0.1:{srv.server_address[1]}", (lambda: (srv.shutdown(), srv.server_close()))


def _bekci():
    from tests.conftest import betikten_modul_yukle
    return betikten_modul_yukle(BEKCI, "vault_sagligi")


def _alarmlar(sandbox_kok) -> list[dict]:
    from meridian import obs
    return [o for o in obs.recent(200) if o.get("alarm")]


@pytest.mark.parametrize("kod", [200, 429])
def test_L1_SAGLIKLI_kodlar_cikis_0_ve_ALARM_YOK(kod, sandbox_state):
    """429 (standby) SAĞLIKLIDIR ve bu ölçülmüş bir karardır: Vault'un belgelenmiş sağlık
    kodudur. Onu arıza saymak yanlış alarm üretirdi — yasanın en pahalı arızası."""
    adres, kapat = _saglik_sunucusu(kod)
    try:
        assert _bekci().main(["--adres", adres]) == 0
    finally:
        kapat()
    assert not _alarmlar(sandbox_state), "sağlıklı kasada alarm yazıldı"


def test_L2_503_VAULT_SEALED_alarmi_yazar(sandbox_state):
    """503 = mühürlü. Bu, Faz-2'nin SESSİZ arıza sınıfıdır: Agent render'ı durur ama dosyalar
    yerinde kalır, yani hiçbir tüketici hata vermez. Alarm olmasaydı arıza ancak bir
    rotasyondan sonra görülürdü."""
    from meridian import obs
    adres, kapat = _saglik_sunucusu(503)
    try:
        assert _bekci().main(["--adres", adres]) == 1
    finally:
        kapat()
    jetonlar = [o["alarm"] for o in _alarmlar(sandbox_state)]
    assert obs.ALARM_VAULT_SEALED in jetonlar, f"VAULT_SEALED yazılmadı: {jetonlar}"


def test_L3_BAGLANTI_YOKSA_VAULT_DOWN(sandbox_state):
    """Kapalı bir portta ölçüm: hüküm DOWN olmalı, SEALED değil. İki jeton iki AYRI operatör
    eylemi ister; karıştırmak teşhisi yanlış yere gönderir."""
    from meridian import obs
    adres, kapat = _saglik_sunucusu(200)
    kapat()                                   # port artık kapalı — bağlantı reddedilir
    assert _bekci().main(["--adres", adres]) == 1
    jetonlar = [o["alarm"] for o in _alarmlar(sandbox_state)]
    assert obs.ALARM_VAULT_DOWN in jetonlar, f"VAULT_DOWN yazılmadı: {jetonlar}"


def test_L4_ALARM_GOVDESI_kendi_KANITINI_tasir(sandbox_state):
    """Teşhis için journal'a geri dönmek gerekmemeli: HTTP kodu ve adres olayın İÇİNDE."""
    adres, kapat = _saglik_sunucusu(503)
    try:
        _bekci().main(["--adres", adres])
    finally:
        kapat()
    kayit = _alarmlar(sandbox_state)[-1]
    assert kayit.get("http_kod") == 503, kayit
    assert kayit.get("adres") == adres, kayit


def test_L5_OLCULEMEYEN_KOD_None_kalir_SIFIR_OLMAZ(sandbox_state):
    """Uydurma yasağı: bağlantı kurulamadıysa HTTP kodu YOKTUR. `0` yazmak "sunucu 0 döndü"
    gibi okunur; `None` "ölçülemedi" der ve ikisi aynı şey değildir."""
    mod = _bekci()
    kod, hata = mod.health_kodu("http://127.0.0.1:1", 0.5)
    assert kod is None and hata, (kod, hata)
    saglikli, jeton, _ = mod.hukum(kod, hata)
    assert saglikli is False and jeton == "VAULT_DOWN"


def test_L6_HUKUM_TABLOSU_tam(sandbox_state):
    """Eşleme tablosu tek yerde ve TÜMÜ ölçülür — bir kod sınıfının sessizce "sağlıklı" dalına
    düşmesi, bekçiyi susturmanın en kolay yoludur."""
    mod = _bekci()
    assert mod.hukum(200, None)[0] is True
    assert mod.hukum(429, None)[0] is True
    assert mod.hukum(503, None)[1] == "VAULT_SEALED"
    assert mod.hukum(501, None)[1] == "VAULT_SEALED"     # init edilmemiş: cevap var, sır yok
    assert mod.hukum(418, None)[1] == "VAULT_DOWN"       # tanınmayan cevap


def test_L7_bekci_JETON_TASIMAZ(sandbox_state):
    """Bekçi kimlik İSTEMEYEN uca bakar. Jetonlu bir uç seçilseydi bekçinin kendisi bir sır
    taşımak zorunda kalırdı: bekçiyi korumak için bir sır daha (yeni yüzey, sıfır kazanç)."""
    metin = BEKCI.read_text(encoding="utf-8")
    assert "/v1/sys/health" in metin
    assert "VAULT_TOKEN" not in metin, "bekçi bir jeton okuyor/taşıyor"


# =================================================================================================
# M) ALARM SINIFI KAYDI — obs jetonları + bildirim zinciri + RUNBOOK (Task 4)
# =================================================================================================

def test_M1_jetonlar_NOTIFY_TOKENS_a_TURETMEYLE_girer(sandbox_state):
    """`NOTIFY_TOKENS` bir EL LİSTESİ değil TÜRETMEdir (obs modül başlığı): yeni bir ALARM_
    sabiti kendiliğinden bildirim kapsamına girer. Elle liste tam da en kritik alarmları
    sessizce dışarıda bırakarak eskimişti."""
    from meridian import obs
    assert obs.ALARM_VAULT_SEALED in obs.NOTIFY_TOKENS
    assert obs.ALARM_VAULT_DOWN in obs.NOTIFY_TOKENS


def test_M2_RUNBOOK_her_iki_jetona_da_BOLUM_acmis():
    """Üretilmiş belge zinciri: yeni alarm sınıfı → `ops/runbook_uret.py` → docs/RUNBOOK.md.
    Belge yeniden üretilmezse v154 zaten kırmızı olur; bu çivi HANGİ jetonun eksik olduğunu
    ADIYLA söyler."""
    md = (REPO / "docs" / "RUNBOOK.md").read_text(encoding="utf-8")
    for jeton in ("VAULT_SEALED", "VAULT_DOWN"):
        assert f"## {jeton}" in md, f"RUNBOOK'ta {jeton} bölümü yok — belge yeniden üretilmemiş"


# =================================================================================================
# N) DAĞITIM LİSTELERİ — rol + dagit tek kaynağı (Task 4)
# =================================================================================================

def _defaults() -> dict:
    yol = REPO / "deploy" / "ansible" / "roles" / "meridian_a1" / "defaults" / "main.yml"
    return yaml.safe_load(yol.read_text(encoding="utf-8"))


def _dagit_vars() -> dict:
    yol = REPO / "deploy" / "ansible" / "vars" / "dagit_vars.yml"
    return yaml.safe_load(yol.read_text(encoding="utf-8"))


def test_N1_rol_VAULT_birimlerini_kapsar():
    """v451 zaten "deploy/ altındaki HER birim kapsanmalı" diyor; bu çivi aynı gerçeği VAULT
    tarafından ölçer ve glob'un ŞEKLİNİ değil SONUCUNU sınar."""
    desenler = _defaults()["birim_kaynaklari"]
    assert any("/../vault/*.service" in d for d in desenler), "vault .service glob'u yok"
    assert any("/../vault/*.timer" in d for d in desenler), "vault .timer glob'u yok"


def test_N2_saglik_timeri_ENABLE_ediliyor_ama_KASA_birimleri_DEGIL():
    """Bekçi timer'ı enable edilir; `vault.service`/`vault-agent.service` EDİLMEZ ve bu bir
    KARARDIR: ikisi de kasa kurulmadan (init + unseal + AppRole) anlamlı değildir ve enable
    edilmiş ama açılamayan bir birim kurulum gününü "neden failed" sorusuyla açardı."""
    d = _defaults()
    assert "vault-sagligi.timer" in d["etkin_timerlar"]
    for birim in ("vault.service", "vault-agent.service", "vault-unseal.service"):
        assert birim not in d["etkin_birimler"], f"{birim} kasa kurulmadan enable ediliyor"


def test_N3_birim_OLMAYAN_vault_dosyalari_F9_da_ve_ROL_DISI_beyanli():
    """Üçü de rolün dışındadır (kurulum betiği koyar) ve bu BEYANLI olmak zorundadır — beyansız
    boşluk bedel yasası ihlalidir (v451 K10 aynı iddiayı tüm küme için ölçer)."""
    beyan = set(_defaults()["f9_rol_disi"])
    ciftler = {c["repo"] for c in _dagit_vars()["f9_ciftleri"]}
    for yol in ("deploy/vault/vault.hcl", "deploy/vault/agent.hcl", "deploy/vault/vault_unseal.sh"):
        assert yol in ciftler, f"{yol} [F9] içerik kapısında yok"
        assert yol in beyan, f"{yol} rol-dışı beyanında yok"


def test_N4_VAULT_BIRIMLERI_F9_iceriginde_de_izleniyor():
    """Birimler rol tarafından TAŞINIR ama [F9] onları ayrıca İÇERİK olarak kıyaslar: canlıda
    elle düzenlenmiş bir birim (dinleme adresi, sertleştirme satırı) ancak böyle görülür."""
    ciftler = {c["repo"]: c["canli"] for c in _dagit_vars()["f9_ciftleri"]}
    for ad in ("vault.service", "vault-unseal.service", "vault-agent.service",
               "vault-sagligi.service", "vault-sagligi.timer"):
        repo_yolu = f"deploy/vault/{ad}"
        assert ciftler.get(repo_yolu) == f"/etc/systemd/system/{ad}", repo_yolu


def test_N5_A0_ROLU_unzip_paketini_kuruyor():
    """Fallback bir ÖZÜR DEĞİLDİR (TUR 2, A1 ilk kurulumu 2026-09-14).

    `vault_kur.sh` artık `unzip` yoksa python3 stdlib'ine düşüyor — ama YALNIZ o yapılsaydı A1
    kalıcı olarak fallback yolunda kalır ve eksik HİÇ görünmezdi. Bu çivi düzeltmenin ÖTEKİ
    yarısını tutar: temiz bir makinede paket ROL tarafından kurulur, eksik DOĞMAZ. İki çivi
    birlikte iki ayrı arızayı kapatır ve biri ötekinin yerine geçemez (bkz. §I9-I12)."""
    paketler = _defaults()["apt_paketleri"]
    assert "unzip" in paketler, (
        "A0 rolü `unzip` kurmuyor — temiz bir A1'de vault_kur.sh adım 1 yine fallback yoluna "
        "düşer ve eksik görünmez hâle gelir (ölçülen arıza 2026-09-14)")


def test_M3_jetonlar_PANODA_bir_OLAY_YUZEYINE_bagli():
    """JETON EVSİZ KALAMAZ. `tests/test_uiux_s1b_v154.py` bu pariteyi TÜM jetonlar için ölçer;
    bu çivi aynı gerçeği VAULT tarafından ve ADIYLA ölçer — parite düştüğünde "hangi jeton"
    sorusu v154'ün küme farkından değil, buradan okunur.

    Evsiz bir jeton şu demektir: alarm YAZILIR, bildirim GİDER, ama panodaki "teşhis ↗" bağı
    hiçbir yüzey açmaz — operatör alarmı görür, ne yapacağını GÖREMEZ. Faz-2'de bunun bedeli
    normalden yüksek: bu sınıfın imzası zaten sessizliktir."""
    appjs = (REPO / "meridian" / "web" / "app.js").read_text(encoding="utf-8")
    blok = re.search(r"const OLAY_YUZEYLERI = \{(.*?)\n\};", appjs, re.S)
    assert blok, "OLAY_YUZEYLERI tanımlı değil"
    kapsanan: set[str] = set()
    for dizi in re.findall(r"jetonlar:\s*\[([^\]]*)\]", blok.group(1)):
        kapsanan |= set(re.findall(r'"([A-Z_]+)"', dizi))
    for jeton in ("VAULT_SEALED", "VAULT_DOWN"):
        assert jeton in kapsanan, f"{jeton} panoda EVSİZ — alarm görünür, teşhis yolu yok"
