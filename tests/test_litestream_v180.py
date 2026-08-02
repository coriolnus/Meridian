"""test_litestream_v180.py — WP-H/H10 AŞAMA-1: Litestream dosya-replica'sını DEPOYA ÇİVİLER.

NEDEN BU TEST VAR. H10 aşama-1'in tamamı **dağıtım yüzeyidir**: bir YAML, bir systemd birimi ve bir
kurulum betiği. Üçünün de yanlışını bugüne dek yalnız CANLI SUNUCU söylerdi — ve bu birimin
söylemesi en geç olanıdır, çünkü çoğaltmanın durduğu bir gün **ancak restore gerektiğinde** fark
edilir (birimde `OnFailure=` yok; gerekçesi birim dosyasında yazılı). Çivilenen sınıflar:

  1. YAPILANDIRMA AYRIŞIYOR VE TEK DB'Yİ HEDEFLİYOR. Bozuk bir YAML `systemctl start`ta patlar;
     YANLIŞ YOLDAKİ geçerli bir YAML ise SESSİZCE boş çoğaltır — asıl tehlike ikincisidir.
     Yol, `meridian.storage`ten TÜRETİLEREK doğrulanır (kargo-kült değil, kaynak-çivili).

  2. YAPILANDIRMADAKİ HER YAZILABİLİR YOL, BİRİMİN `ReadWritePaths`İNDE OLMALI. `ProtectSystem=
     strict` + `ProtectHome=read-only` altında eksik bir yol = birimin AÇILIŞTA reddi ya da ilk
     yazımda EROFS. İki dosya AYRI AYRI doğru olup BİRLİKTE yanlış olabilir; ölçülen bu.

  3. H3 TUR-2 SETİ GERİ GİTMESİN. Sertleştirme değerleri `test_h3_tur2_v174.ORTAK_SET`ten
     İTHAL EDİLİR — ikinci bir liste yazmak, iki listenin ayrışması demekti.

  4. TEDARİK ZİNCİRİ KAPISI GERÇEKTEN KAPI OLSUN. Sürüm sabiti + sha256 sabiti + doğrulamanın
     BAŞARISIZLIKTA DURDURDUĞU (yalnız uyarı yazmadığı) ölçülür. `latest` yasak.

  5. `Environment=` SATIR-SONU YORUMU YASAK (2026-08-01 vakası; systemd `#`i değerin parçası
     sayar, atamayı düşürür ve değişken SESSİZCE boş kalır).

  6. DÜRÜSTLÜK BEYANLARI BELGEDE DURSUN: (a) replica AYNI DİSKTEdir → medya arızası kapsam dışı;
     (b) litestream canlı deftere YAZAR (iki tablo yaratır) → salt-okuma yetmez. İkisi de bu turda
     ÖLÇÜLDÜ; belgeden düşerlerse bir sonraki tur onları yeniden keşfetmek zorunda kalır.

CANLI SİSTEME DOKUNMAZ: yalnız depo dosyaları okunur; ne SSH ne state yazımı ne ağ vardır.
"""
from __future__ import annotations

import pathlib
import re
import shutil
import subprocess

import pytest
import yaml

# systemd AYRIŞTIRICISI + SERTLEŞTİRME SETİ TEK KAYNAKTAN İTHAL EDİLİR. Kopyalamak, "yorum ≠
# direktif" kuralını (satır-sonu `#` KIRPILMAZ) ikinci kez yazmak ve iki ayrıştırıcının bir gün
# ayrışması demekti. H3 testi o kuralın SAHİBİDİR; burası tüketicisi.
from tests.test_h3_tur2_v174 import (  # noqa: E402
    ORTAK_SET,
    _deger,
    _metin,
    _rwp,
    _rwp_ham,
    _service,
    _yorumlar,
)

REPO = pathlib.Path(__file__).resolve().parent.parent
UNITS = REPO / "deploy" / "oracle-a1"

BIRIM = "meridian-litestream.service"
YAPILANDIRMA = UNITS / "litestream.yml"
KUR = UNITS / "litestream_kur.sh"
RUNBOOK = UNITS / "RUNBOOK.md"
MACPULL = REPO / "ops" / "pull-a1-backups.sh"

# A1 gerçeği (2026-08-02 salt-okuma keşfi): depo /opt/meridian, defter state/ altında.
A1_KOK = "/opt/meridian"


def _cfg() -> dict:
    assert YAPILANDIRMA.exists(), f"yapılandırma yok: {YAPILANDIRMA}"
    return yaml.safe_load(YAPILANDIRMA.read_text())


def _kod(yol: pathlib.Path) -> str:
    """Kabuk betiğinin KOD satırları — yorumlar ATILIR. H3 testinin 'yorum ≠ direktif' dersinin
    kabuk karşılığı: bu dosyada gerekçeler uzun ve `--delete`/`latest` gibi YASAKLARI ADIYLA
    anlatıyorlar. Yasakları ham metinde aramak, betiğin kendini suçlamasına yol açardı."""
    return "\n".join(l for l in yol.read_text().splitlines() if not l.strip().startswith("#"))


def _sure_sn(s: str) -> float:
    """Go süre dizgisi ('10s', '12h', '5s') → saniye. Litestream `time.ParseDuration` kullanır;
    burada YALNIZ bu dosyada geçen birimler desteklenir — desteklenmeyen bir birim görülürse test
    SESSİZCE geçmez, DÜŞER (yeni bir birim yazıldıysa bu testin de güncellenmesi gerekir)."""
    m = re.fullmatch(r"(\d+(?:\.\d+)?)(ms|s|m|h)", str(s).strip())
    assert m, f"süre dizgisi ayrıştırılamadı: {s!r} (bu testin desteklediği birimler: ms/s/m/h)"
    kat = {"ms": 0.001, "s": 1.0, "m": 60.0, "h": 3600.0}[m.group(2)]
    return float(m.group(1)) * kat


# ==================================================================================================
# 1 — YAPILANDIRMA: AYRIŞIYOR + DOĞRU DEFTERİ HEDEFLİYOR
# ==================================================================================================
def test_yapilandirma_gecerli_yaml_ve_tek_db():
    c = _cfg()
    assert isinstance(c, dict), "litestream.yml bir eşleme (mapping) olmalı"
    assert isinstance(c.get("dbs"), list) and len(c["dbs"]) == 1, (
        f"tam olarak BİR db beklenir (H9 defter çekirdeği): {c.get('dbs')!r}")


def test_db_yolu_KAYNAKTAN_tureniyor_kargo_kult_degil():
    """Yol 'olsun diye' değil, `meridian.storage`in gerçekten kullandığı ad olduğu için orada."""
    from meridian import storage

    db = _cfg()["dbs"][0]
    assert storage.DB_NAME == "meridian.db", (
        "storage.DB_NAME değişmiş — litestream.yml'deki yol da değişmeli")
    beklenen = f"{A1_KOK}/state/{storage.DB_NAME}"
    assert db["path"] == beklenen, f"db yolu {db['path']!r}, beklenen {beklenen!r}"
    # A1 kökü uydurulmuş bir sabit DEĞİL: canlı birimlerin WorkingDirectory'siyle aynı olmalı.
    assert _deger("meridian.service", "WorkingDirectory") == A1_KOK, (
        "meridian.service'in WorkingDirectory'si değişmiş — litestream.yml yolları eskimiş olabilir")


def test_deprecated_replicas_ANAHTARI_KULLANILMIYOR():
    """v0.5 `replicas:` listesini EMEKLİ etti (cmd/litestream/main.go: 'Deprecated'; birden fazla
    replica artık hata). Eski biçimi yazmak, yükseltmede sessizce kırılacak bir yapılandırmadır."""
    db = _cfg()["dbs"][0]
    assert "replicas" not in db, "eski `replicas:` listesi kullanılmış — v0.5 biçimi `replica:`"
    assert isinstance(db.get("replica"), dict), "`replica:` bloğu yok"


def test_sync_interval_SANİYELER_mertebesinde():
    """H10 hükmü: 'RPO günler→dakikalar'. Saniyeler mertebesi o hedefi fazlasıyla karşılar; dakika
    ÜSTÜ bir değer hedefi ölçülemez hâle getirirdi."""
    sn = _sure_sn(_cfg()["dbs"][0]["replica"]["sync-interval"])
    assert 0 < sn <= 60, f"sync-interval {sn}sn — saniyeler mertebesinde olmalı (<=60sn)"


def test_snapshot_penceresi_HAFTA_SONUNU_kapsiyor():
    """CUMA akşamı bozulan defter en erken PAZARTESİ fark edilir = ~72 saat. Pencere 72'de BİTERSE
    fark etme anı ile pencerenin bitişi aynı güne düşer; 72'nin ÜSTÜ şart."""
    snap = _cfg()["snapshot"]
    ret = _sure_sn(snap["retention"])
    itv = _sure_sn(snap["interval"])
    assert ret > 72 * 3600, f"snapshot.retention {ret/3600:g}sa — hafta sonu + bir işlem günü için 72sa'ten BÜYÜK olmalı"
    assert itv < ret, "snapshot.interval retention'dan küçük olmalı (yoksa pencerede tek snapshot bile kalmayabilir)"
    assert ret / itv >= 4, (
        f"pencerede yalnız {ret/itv:g} snapshot kalır — tek bozuk snapshot geri sarmayı bitirmemeli")


def test_busy_timeout_MERIDIANIN_KENDI_PRAGMASIYLA_esit():
    """Ayrışan iki timeout, journal'i 'database is locked' ile doldurup gerçek arızayı gömerdi."""
    from meridian import storage

    pragma = dict(storage.PRAGMAS)
    assert "busy_timeout" in pragma, "storage.PRAGMAS'ta busy_timeout yok — bu testin dayanağı değişmiş"
    beklenen_sn = float(pragma["busy_timeout"]) / 1000.0
    gercek = _sure_sn(_cfg()["dbs"][0]["busy-timeout"])
    assert gercek == beklenen_sn, (
        f"litestream busy-timeout {gercek}sn, Meridian PRAGMA'sı {beklenen_sn}sn — eşit olmalı")


def test_meta_dizini_STATE_AGACININ_DISINDA():
    """Varsayılan meta konumu DB'nin yanıdır (`.meridian.db-litestream`). Orada bırakılsaydı
    `state/` tar'ına girer ve o tar'dan yapılan bir GERİ YÜKLEME, yeni DB'nin yanına BAYAT bir meta
    dizini bırakırdı → `auto-recover` kapalı olduğu için çoğaltma sessizce DURURDU."""
    meta = _cfg()["dbs"][0].get("meta-path")
    assert meta, "`meta-path` ayarlanmamış — varsayılan konum state/ ağacının içindedir"
    assert not meta.startswith(f"{A1_KOK}/state"), (
        f"meta dizini state ağacının İÇİNDE: {meta} — tar/restore tuzağı geri geldi")


def test_kontrol_soketi_kapali():
    """Açık olsaydı `/var/run/litestream.sock` yazımı `ProtectSystem=strict` altında AÇILIŞTA
    öldürürdü. Varsayılan zaten kapalı; AÇIK YAZILMASI okunabilirlik kararıdır."""
    assert _cfg().get("socket", {}).get("enabled") is False, "socket.enabled açıkça false olmalı"


# ==================================================================================================
# 2 — YAPILANDIRMA ↔ BİRİM TUTARLILIĞI (iki dosya ayrı ayrı doğru, birlikte yanlış olabilir)
# ==================================================================================================
def _yazilabilir_dizinler() -> dict[str, str]:
    """Yapılandırmanın YAZMAYI GEREKTİRDİĞİ dizinler → hangi ayardan geldiği."""
    db = _cfg()["dbs"][0]
    return {
        # DB dizini: `-wal`/`-shm` yan dosyaları + litestream'in tablo yazımları (db.go:1083/1089)
        str(pathlib.PurePosixPath(db["path"]).parent): "dbs[0].path",
        str(pathlib.PurePosixPath(db["replica"]["path"]).parent): "dbs[0].replica.path",
        str(pathlib.PurePosixPath(db["meta-path"]).parent): "dbs[0].meta-path",
    }


def test_yapilandirmadaki_her_yazilabilir_yol_birimde_ACIK():
    yollar = _rwp(BIRIM)
    for dizin, kaynak in _yazilabilir_dizinler().items():
        assert any(dizin == p or dizin.startswith(p.rstrip("/") + "/") for p in yollar), (
            f"{kaynak} → `{dizin}` ReadWritePaths'te YOK ({yollar}) — birim ya açılmaz "
            "ya ilk yazımda EROFS alır")


def test_readwritepaths_GEREKSIZ_GENIS_DEGIL():
    """Bu birim `uv run` KOŞMAZ: venv/`__pycache__`/`.env` yazma ihtiyacı yoktur. `/opt/meridian`
    ağacının tamamını açmak, diğer üç birimin gerekçesini buraya KOPYALAMAK olurdu."""
    yollar = _rwp(BIRIM)
    assert A1_KOK not in yollar, (
        f"`{A1_KOK}` ağacının tamamı açılmış — bu birime yalnız `state` gerekir: {yollar}")
    assert f"{A1_KOK}/state" in yollar, f"`{A1_KOK}/state` ReadWritePaths'te yok: {yollar}"
    for yasak in ("/home/ubuntu/.cache", "/home/ubuntu/.hermes"):
        assert yasak not in yollar, f"`{yasak}` bu birime gereksiz yere açılmış (uv de ajan da yok)"


def test_readwritepaths_ONEKSIZ_yokluk_gurultulu_olsun():
    """Üç yol da bu birimin ÇALIŞMASI için şarttır: `-` öneki, eksikliği sessizce yutardı ve birim
    'aktif ama hiçbir şey çoğaltmıyor' hâline düşerdi."""
    for p in _rwp_ham(BIRIM):
        assert not p.startswith("-"), (
            f"`{p}` `-` önekli — bu birimde üç yol da ŞART, yoklukları GÜRÜLTÜLÜ olmalı")


def test_her_readwritepath_gerekce_tasiyor():
    yorum = _yorumlar(BIRIM)
    for p in _rwp(BIRIM):
        assert p in yorum, f"`{p}` ReadWritePaths'te ama gerekçesi yorumda yok"


# ==================================================================================================
# 3 — H3 TUR-2 SERTLEŞTİRME SETİ (tek kaynaktan ithal; ayrışma yasak)
# ==================================================================================================
def test_h3_tur2_seti_BIREBIR_ayni():
    for anahtar, beklenen in ORTAK_SET.items():
        gercek = _deger(BIRIM, anahtar)
        assert gercek is not None, f"{BIRIM}: `{anahtar}` YOK — H3 tur-2 seti eksik"
        assert gercek == beklenen, f"{BIRIM}: {anahtar}={gercek!r}, beklenen {beklenen!r}"


def test_syscall_filtresi_bolumun_SON_direktifi():
    svc = _service(BIRIM)
    assert svc[-1][0] == "SystemCallFilter", (
        f"{BIRIM}: [Service]'in son direktifi {svc[-1][0]} — SystemCallFilter olmalı (H3 sözleşmesi)")


def test_environment_satirinda_satir_sonu_yorumu_YOK():
    """2026-08-01 vakası. (H3 testi bunu `*.service` glob'uyla zaten tarıyor; burada AÇIKÇA
    tekrarlanıyor çünkü bu turun dosyası o glob'a bugün girdi, yarın taşınabilir.)"""
    for k, v, no in _service(BIRIM):
        if k in ("Environment", "EnvironmentFile"):
            assert "#" not in v, (
                f"{BIRIM}:{no} `{k}=` satırında satır-sonu yorumu — systemd atamayı düşürür: {v!r}")


def test_birim_calisma_sozlesmesi():
    assert _deger(BIRIM, "Type") == "simple"
    assert _deger(BIRIM, "User") == "ubuntu"
    assert _deger(BIRIM, "Restart") == "always"
    exec_start = _deger(BIRIM, "ExecStart")
    assert exec_start and exec_start.startswith("/usr/local/bin/litestream replicate"), (
        f"ExecStart beklenmedik: {exec_start!r}")
    assert "-config /etc/litestream.yml" in exec_start, (
        "yapılandırma yolu ÖRTÜK bırakılmış — birimi okuyan mühendis hangi dosyanın yürürlükte "
        "olduğunu systemd'nin kaynağından okuyabilmeli")
    # Kapanışta bekleyen senkron bütçesi (litestream varsayılanı 30sn) TimeoutStopSec'ten KÜÇÜK
    # olmalı; değilse systemd litestream'i son senkronunun ortasında öldürür.
    assert float(_deger(BIRIM, "TimeoutStopSec")) > 30, (
        "TimeoutStopSec, litestream'in 30sn'lik shutdown-sync bütçesinden büyük olmalı")


def test_birim_worker_a_ZINCIRLENMEMIS():
    """`Requires=`/`BindsTo=` olsaydı `systemctl stop meridian` çoğaltmayı DA durdururdu — oysa
    bakım penceresinin en riskli anı tam orasıdır (geri sarılabilir nokta olmazdı)."""
    anahtarlar = {k for k, _, _ in _service(BIRIM)}
    metin = _metin(BIRIM)
    for yasak in ("Requires=", "BindsTo=", "PartOf="):
        assert not re.search(rf"^\s*{yasak}", metin, re.M), (
            f"{BIRIM}: `{yasak}` var — worker durunca çoğaltma da durardı")
    assert "Requires" not in anahtarlar
    assert "multi-user.target" in metin, "[Install] WantedBy eksik — reboot'ta çoğaltma geri gelmez"


def test_onfailure_YOKLUGU_gerekcesiyle_yazili():
    """Sessiz atlama yasak: alarm bağlanmadıysa NEDEN bağlanmadığı ve ölçünün ne olduğu yazılı."""
    anahtarlar = {k for k, _, _ in _service(BIRIM)}
    assert "OnFailure" not in anahtarlar
    yorum = _yorumlar(BIRIM)
    assert "OnFailure" in yorum and "fail-notify" in yorum, (
        f"{BIRIM}: OnFailure yokluğu gerekçesiz — yanlış alarm mı, unutulmuş mu ayırt edilemez")
    assert "is-active" in yorum, "ölçünün `is-active` OLMADIĞI birimde yazılı değil"


# ==================================================================================================
# 4 — KURULUM BETİĞİ: TEDARİK-ZİNCİRİ KAPISI GERÇEKTEN KAPI MI
# ==================================================================================================
def test_betik_sozdizimi_gecerli():
    bash = shutil.which("bash")
    assert bash, "bash bulunamadı — betik sözdizimi ölçülemedi"
    p = subprocess.run([bash, "-n", str(KUR)], capture_output=True, text=True)
    assert p.returncode == 0, f"bash -n düştü:\n{p.stderr}"


def test_betik_calistirilabilir():
    assert KUR.stat().st_mode & 0o111, f"{KUR.name} çalıştırma bitine sahip değil"


def test_betik_SURUM_SABIT_latest_yasak():
    kod = _kod(KUR)
    assert re.search(r'^LS_SURUM="([0-9]+\.[0-9]+\.[0-9]+)"', kod, re.M), (
        "LS_SURUM anlamlı-sürüm biçiminde sabitlenmemiş")
    assert "latest" not in kod, (
        "kodda `latest` geçiyor — dünkü denetimden geçmemiş bir ikiliyi yarınki koşum canlıya sokar")
    url = re.search(r'^LS_URL="([^"]+)"', kod, re.M)
    assert url, "LS_URL yok"
    assert "${LS_SURUM}" in url.group(1), (
        f"indirme URL'i sabitlenen sürüm değişkenini kullanmıyor: {url.group(1)!r}")


def test_betik_SHA256_SABIT_ve_gercek_bir_ozet():
    m = re.search(r'^LS_SHA256="([0-9a-f]{64})"', KUR.read_text(), re.M)
    assert m, "LS_SHA256 64 haneli onaltılık bir sha256 olarak sabitlenmemiş"


def test_betik_sha256_kapisi_BASARISIZLIKTA_DURDURUYOR():
    """Bir 'doğrulama' yalnız UYARI yazıyorsa kapı değildir. Ölçü: eşleşmezse arşiv SİLİNİR ve
    betik ÇIKAR; `install` satırına asla ulaşılmaz."""
    kod = _kod(KUR)
    assert "sha256sum -c" in kod, "sha256 doğrulaması yapılmıyor"
    assert "command -v sha256sum" in kod, "sha256sum yokluğu ön koşul olarak ölçülmemiş"
    # Doğrulama ile arşivin AÇILMASI arasındaki blok: uyuşmazlıkta hem SİLMELİ hem DURDURMALI.
    kapi = kod[kod.index("sha256sum -c"):kod.index("tar -xzf")]
    assert "rm -f" in kapi, "uyuşmazlıkta bozuk arşiv diskte bırakılıyor"
    assert re.search(r"\bdie ", kapi), (
        "uyuşmazlık dalı `die` ile durdurmuyor — 'doğrulama' yalnız uyarı yazıyorsa kapı değildir")
    # Sıra bağlayıcı: doğrulama, ikilinin /usr/local/bin'e kurulmasından ÖNCE gelmeli.
    assert kod.index("sha256sum -c") < kod.index("sudo install -o root"), (
        "sha256 kapısı `install`dan SONRA — doğrulanmamış ikili canlıya girerdi")


def test_betik_MIMARI_kapisi():
    metin = KUR.read_text()
    assert "aarch64" in metin and "uname -m" in metin, (
        "mimari kapısı yok — yanlış ikili 'exec format error' ile ölür ve nedeni journal'da aranır")


def test_betik_IDEMPOTENT():
    metin = KUR.read_text()
    assert "İDEMPOTENT" in metin.upper() or "IDEMPOTENT" in metin.upper()
    assert "litestream version" in metin or '"$IKILI" version' in metin, (
        "kurulu sürüm ölçülmüyor — betik her koşumda yeniden indirirdi")
    assert "cmp -s" in metin, "yapılandırma/birim değişmediyse dokunmama ölçüsü yok"
    assert "is-enabled" in metin, (
        "`systemctl enable` zaten etkinken de 0 döner — durum okunmadan '✓ enable' demek yalandır")


def test_betik_VARSAYILAN_BASLATMAZ():
    """İlk `start` canlı defterin ŞEMASINA iki tablo ekler (db.go:1083/1089) — geri alınması en zor
    adım. Betiğin varsayılanı bunu operatör kararı bırakmalı."""
    metin = KUR.read_text()
    assert "--baslat" in metin, "başlatma ayrı bir bayrağa bağlanmamış"
    assert "enable --now" not in metin, (
        "`enable --now` var — betik bayraksız koşumda canlı deftere yazmaya başlardı")


def test_betik_KURU_DOGRULAMA_yapiyor_ve_DB_ACMIYOR():
    """`litestream databases` YALNIZ config'i ayrıştırır (cmd/litestream/databases.go: NewDBFromConfig,
    Open YOK) — bozuk YAML'ı `start`tan ÖNCE yakalar ve canlı deftere dokunmaz."""
    metin = KUR.read_text()
    assert "databases -config" in metin, "yapılandırmanın kuru doğrulaması yok"


# ==================================================================================================
# 5 — RUNBOOK: PROSEDÜR GERİ-ALINABİLİR, NÖBETLİ VE DÜRÜST OLMALI
# ==================================================================================================
def test_runbook_h10_bolumu_tam():
    rb = RUNBOOK.read_text()
    for parca, neden in (
        ("Bölüm B4", "bölüm başlığı"),
        ("litestream_kur.sh", "kurulum adımı"),
        ("systemctl start meridian-litestream", "başlatma adımı"),
        ("h10-oncesi", "GERİ-ALMA yedeği (defterin çevrimiçi tutarlı kopyası)"),
        ("systemd-analyze security meridian-litestream", "beklenen-skor ölçümü"),
        ("litestream restore", "restore tatbikatı"),
        ("-integrity-check full", "tatbikatın SQLite doğrulaması"),
        ("-timestamp", "geri sarma (point-in-time) tatbikatı"),
        ("H7 ritüeline eklenen adım", "tatbikatın ritüele bağlanması"),
        ("GERİ ALMA", "geri-alma adımı"),
        ("disable --now meridian-litestream", "geri-almanın ilk komutu"),
        ("SIGSYS", "seccomp arıza şekli"),
        ("24 SAAT", "seccomp nöbeti"),
        ("NRestarts", "sessiz restart çırpınmasının ölçüsü"),
        ("üçüncü kopya", "WP-U değerlendirmesi"),
        ("KARAR OPERATÖRE", "hükmün operatörde olduğu"),
    ):
        assert parca in rb, f"RUNBOOK'ta eksik ({neden}): {parca!r}"
    assert "2,5–3,8" in rb and "TAHMİN" in rb, (
        "beklenen skor TAHMİN olarak işaretlenmeli — ölçülmemiş sayı ölçülmüş gibi yazılamaz")


def test_runbook_AYNI_DISK_durustlugu_yazili():
    """Bu turun en kolay yalanı: 'yedeğimiz artık sürekli' deyip aynı diskte durduğunu yazmamak."""
    rb = RUNBOOK.read_text()
    assert "ikinci fiziksel disk" in rb.lower(), "aynı-disk sınırı beyan edilmemiş"
    assert "aynı blok cihaz" in rb.lower(), "replica ile defterin aynı cihazda olduğu yazılmamış"
    assert "AŞAMA-2" in rb.upper() and "bucket" in rb.lower(), (
        "medya korumasının aşama-2'ye (bucket) ait olduğu yazılmamış")
    assert "lsblk" in rb, "sınır İDDİA olarak değil ÖLÇÜM olarak yazılmalı (keşif komutu adıyla)"


def test_runbook_ucuncu_kopya_TABLOSU_veri_tasiyor():
    """Hüküm operatörde; ama tablo KARAR İÇİN GEREKEN VERİYİ taşımazsa hüküm de veriye dayanmaz."""
    rb = RUNBOOK.read_text()
    blok = rb.split("ÜÇÜNCÜ KOPYA", 1)
    assert len(blok) > 1, "üçüncü-kopya bölümü yok"
    tablo = blok[1]
    assert tablo.count("\n|") >= 6, "seçenek tablosu en az 5 satır + başlık taşımalı"
    for parca in ("Object Storage", "Mac-pull", "59M", "617M", "112M"):
        assert parca in tablo, f"tabloda eksik (ölçülmüş sayı ya da seçenek): {parca!r}"
    assert "yeniden-üretilemez" in tablo or "KALINTI" in tablo, (
        "bar arşivinin neden kritik olduğu (WP-U bulgusu) tabloda yazılı değil")


def test_runbook_CANLI_DBYE_YAZMA_gercegini_soyluyor():
    rb = RUNBOOK.read_text()
    assert "_litestream_seq" in rb and "_litestream_lock" in rb, (
        "litestream'in canlı deftere iki tablo eklediği belgede yazılı değil — bir sonraki tur "
        "onları 'bu nereden geldi' diye arardı")
    assert "db.go:" in rb, "iddia kaynak satırıyla desteklenmemiş (uydurma yasağı)"


# ==================================================================================================
# 6 — AYNI GERÇEKLER YAPILANDIRMA + BİRİM DOSYALARINDA DA YAZILI (belge tek yerde yaşamaz)
# ==================================================================================================
def test_yapilandirma_dosyasi_olculmus_gercekleri_tasiyor():
    metin = YAPILANDIRMA.read_text()
    for parca, neden in (
        ("_litestream_seq", "canlı DB'ye yazım gerçeği"),
        ("db.go:1030", "DB yoksa YARATMAZ ölçümü (MERIDIAN_DB=off güvenliği)"),
        ("İKİNCİ FİZİKSEL DİSK YOK", "aynı-disk sınırı"),
        ("lsblk", "sınırın ölçümle desteklenmesi"),
        ("storage.py:139", "busy_timeout eşitlemesinin kaynağı"),
        ("auto-recover", "dokunulmayan varsayılanın beyanı"),
    ):
        assert parca in metin, f"litestream.yml'de eksik ({neden}): {parca!r}"


def test_birim_dosyasi_salt_okuma_YETMEDIGINI_yaziyor():
    yorum = _yorumlar(BIRIM)
    assert "Salt-okuma YETMEZ" in yorum or "salt-okuma yetmez" in yorum.lower(), (
        "birim, state'i neden YAZILABİLİR açtığını söylemiyor — bir sonraki tur onu 'gereksiz "
        "geniş' sanıp daraltır ve çoğaltmayı kırardı")


# ==================================================================================================
# 7 — MAC-PULL GENİŞLETMESİ (VM-dışı replica kopyası)
# ==================================================================================================
def test_macpull_sozdizimi_gecerli():
    bash = shutil.which("bash")
    assert bash, "bash bulunamadı"
    p = subprocess.run([bash, "-n", str(MACPULL)], capture_output=True, text=True)
    assert p.returncode == 0, f"bash -n düştü:\n{p.stderr}"


def test_macpull_replica_bacagi_var_ve_SILMIYOR():
    metin = MACPULL.read_text()
    replica_yolu = str(pathlib.PurePosixPath(_cfg()["dbs"][0]["replica"]["path"]).parent)
    assert replica_yolu in metin, (
        f"Mac-pull replica bacağı yapılandırmadaki yolu ({replica_yolu}) kullanmıyor")
    bacak = _kod(MACPULL).split("rc_rep=0", 1)
    assert len(bacak) > 1, "replica bacağı bölümü yok"
    assert "--delete" not in bacak[1], (
        "replica bacağında `--delete` var — A1'de saklama penceresi dolduğu için budanan bir "
        "dosya, VM-dışı kopyadan da silinirdi (tar bacağının yasasıyla çelişir)")


def test_macpull_kurulmamis_durumu_BEYANLI_no_op():
    """H10 canlıya inmeden uzak dizin YOKTUR ve bu bir arıza değildir — ama sessiz de olamaz
    (YASA 4). rsync'in 23/24 kodu ikisini aynı torbaya atardı; sonda ÖNCE sorulmalı."""
    metin = MACPULL.read_text()
    assert "test -d" in metin, "uzak dizin varlığı sondayla ölçülmüyor"
    assert "BEYANLI" in metin, "kurulmamış durumun beyanlı no-op olduğu yazılmamış"


def test_macpull_iki_bacagin_cikis_kodu_MASKELENMIYOR():
    metin = MACPULL.read_text()
    assert "rc_rep" in metin, "replica bacağının çıkış kodu ayrı tutulmuyor"
    son = metin.rstrip().splitlines()[-1]
    assert son.strip() == 'exit "$rc_rep"', (
        f"son satır beklenmedik ({son!r}) — replica bacağının hatası launchd raporunda görünmeli")
