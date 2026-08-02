"""test_h3_tur2_v174.py — WP-H/H3 TUR-2: systemd sertleştirmesini KAYNAĞA ÇİVİLER.

NEDEN BU TEST VAR. Bir systemd birim dosyası test edilmeyen tek dağıtım yüzeyiydi: yanlışı
`pytest` değil, CANLI SUNUCU söylüyordu. Bu turda beş sınıf çivileniyor:

  1. SERTLEŞTİRME GERİ GİTMESİN. `NoNewPrivileges`/`ProtectSystem=strict`/`CapabilityBoundingSet=`/
     `SystemCallFilter=@system-service` üç birimde de DURUR ve değerleri AYNIDIR. Ortak bir
     direktifin tek birimde sessizce ayrışması, "sertleştirildi" cümlesini yalana çevirirdi.

  2. TUR-1'İN SESSİZ KIRIKLIĞI GERİ DÖNMESİN. Tur-1 `ProtectHome=read-only` koydu ama
     `ReadWritePaths`e `~/.hermes`i KOYMADI — oysa süreç oraya yazar (`hermes.py`: ajan `.env`i,
     `config.yaml`ı, `skills/` symlink'leri). O yazımlar `except OSError: pass` altında olduğu için
     hata GÖRÜNMEDEN yutuldu. Test hem birimdeki yolu hem KAYNAKTAKİ yazma gerçeğini ölçer: yol
     "olsun diye" değil, kod oraya yazdığı için orada.

  3. SIR BİRİME GERİ SIZMASIN. `MERIDIAN_DASH_TOKEN` 2026-07-31'de 0644'lük birimden 0600'lük
     `.dash.env`e taşındı — ama YALNIZ CANLIDA (`bakim_h9.sh:59` sed'i); DEPODAKİ kopya
     CHANGEME'li kaldı. Depodaki birimi kopyalayan her prosedür (`deploy.sh:89`) rotasyonu geri
     alırdı. Artık `EnvironmentFile` düzeni depoda da çivili.

  4. `Environment=` SATIR-SONU YORUMU YASAK. systemd `#` ve sonrasını değerin/ayrı atamaların
     parçası sayar; journal'e "Invalid environment assignment" düşer ve değişken SESSİZCE boş
     kalır (2026-08-01 vakası).

  5. DIŞARIDA BIRAKILAN HER DİREKTİF GEREKÇE TAŞIR. `MemoryDenyWriteExecute` gibi ölçülmemiş
     kalemler ne sessizce eklenir ne sessizce atlanır: dosyada ADIYLA ve gerekçesiyle yazılıdır.

CANLI SİSTEME DOKUNMAZ: yalnız depo dosyaları okunur; ne SSH ne state yazımı vardır.
"""
from __future__ import annotations

import inspect
import pathlib
import re

import pytest

REPO = pathlib.Path(__file__).resolve().parent.parent
UNITS = REPO / "deploy" / "oracle-a1"

# H3 tur-2 setini TAŞIYAN birimler. `meridian-fail-notify.service` BİLEREK yok (gerekçesi kendi
# dosyasında + ayrı testte ölçülüyor); `.timer` birimlerinin `[Service]` bölümü olmaz.
SERTLESTIRILEN = ("meridian.service", "meridian-barsarchive.service", "meridian-backup.service")

# Üç birimde de BİREBİR AYNI olması gereken direktifler (ReadWritePaths BİLEREK dışarıda —
# her birimin yazma envanteri farklıdır ve ayrı testlerde ölçülür).
ORTAK_SET = {
    "NoNewPrivileges": "true",
    "CapabilityBoundingSet": "",              # boş = hiçbir yetenek
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
    "RestrictAddressFamilies": "AF_INET AF_INET6 AF_UNIX",
    "SystemCallArchitectures": "native",
    "SystemCallFilter": "@system-service",
}

# Ölçülmediği için BİLEREK dışarıda bırakılanlar. Kural çift yönlü: direktif olarak GEÇMEYECEK,
# ama adı bir YORUM satırında gerekçesiyle GEÇECEK (yasa: sessiz atlama yok).
DISARIDA_BIRAKILANLAR = (
    "MemoryDenyWriteExecute",
    "PrivateDevices",
    "PrivateUsers",
    "ProcSubset",
    "ProtectProc",
    "IPAddressDeny",
    "SystemCallErrorNumber",
)


# ==================================================================================================
# systemd birim ayrıştırıcısı — YORUM ≠ DİREKTİF
# ==================================================================================================
def _metin(ad: str) -> str:
    p = UNITS / ad
    assert p.exists(), f"birim dosyası yok: {p}"
    return p.read_text()


def _bolumler(metin: str) -> dict[str, list[tuple[str, str, int]]]:
    """`{bolum: [(anahtar, deger, satir_no), ...]}`. systemd'de yorum YALNIZ satır başındadır
    (baştaki boşluk serbest); satır-sonu `#` bir yorum DEĞİL, değerin parçasıdır — bu testin
    4. sınıfı tam olarak bunu ölçtüğü için ayrıştırıcı da `#`i kırpMAZ."""
    out: dict[str, list[tuple[str, str, int]]] = {}
    bolum = None
    for i, ham in enumerate(metin.splitlines(), start=1):
        s = ham.strip()
        if not s or s.startswith("#") or s.startswith(";"):
            continue
        if s.startswith("[") and s.endswith("]"):
            bolum = s[1:-1]
            out.setdefault(bolum, [])
            continue
        if bolum is None or "=" not in s:
            continue
        k, _, v = s.partition("=")
        out[bolum].append((k.strip(), v.strip(), i))
    return out


def _service(ad: str) -> list[tuple[str, str, int]]:
    b = _bolumler(_metin(ad))
    assert "Service" in b, f"{ad}: [Service] bölümü yok"
    return b["Service"]


def _deger(ad: str, anahtar: str) -> str | None:
    """systemd SKALER direktifte SON atamayı uygular — ayrıştırıcı da öyle yapar."""
    v = [d for k, d, _ in _service(ad) if k == anahtar]
    return v[-1] if v else None


def _yorumlar(ad: str) -> str:
    return "\n".join(l for l in _metin(ad).splitlines() if l.strip().startswith("#"))


# ==================================================================================================
# 1 — SERTLEŞTİRME SETİ ÜÇ BİRİMDE DE DURUYOR
# ==================================================================================================
@pytest.mark.parametrize("birim", SERTLESTIRILEN)
def test_sertlestirme_seti_birimde_duruyor(birim):
    for anahtar, beklenen in ORTAK_SET.items():
        gercek = _deger(birim, anahtar)
        assert gercek is not None, f"{birim}: `{anahtar}` YOK — H3 tur-2 seti eksik"
        assert gercek == beklenen, f"{birim}: {anahtar}={gercek!r}, beklenen {beklenen!r}"


@pytest.mark.parametrize("birim", SERTLESTIRILEN)
def test_capability_bounding_set_gercekten_bos(birim):
    """`CapabilityBoundingSet=` BOŞ olmalı. Bir değer yazılırsa (örn. CAP_NET_BIND_SERVICE)
    o yetenek geri gelir; süreç 8080 (>1024) dinlediği için hiçbirine ihtiyacı YOK."""
    satirlar = [d for k, d, _ in _service(birim) if k == "CapabilityBoundingSet"]
    assert satirlar == [""], f"{birim}: CapabilityBoundingSet={satirlar!r} — boş olmalı"


@pytest.mark.parametrize("birim", SERTLESTIRILEN)
def test_syscall_filtresi_bolumun_son_direktifi(birim):
    """ROADMAP H3: 'seccomp EN SON'. Sıra systemd için anlamlı değil ama OKUYUCU için sözleşmedir:
    filtre en riskli kalemdir ve dosyanın sonunda, gerekçe bloğunun ardında durur."""
    svc = _service(birim)
    assert svc[-1][0] == "SystemCallFilter", (
        f"{birim}: [Service]'in son direktifi {svc[-1][0]} — SystemCallFilter olmalı")


# ==================================================================================================
# 2 — ReadWritePaths: ÖLÇÜLMÜŞ ENVANTER (kırık ReadWritePaths canlıyı KIRAR)
# ==================================================================================================
def _rwp_ham(birim: str) -> list[str]:
    ham = [d for k, d, _ in _service(birim) if k == "ReadWritePaths"]
    assert ham, f"{birim}: ReadWritePaths YOK — ProtectSystem=strict altında hiçbir şey yazamaz"
    return [p for satir in ham for p in satir.split()]


def _rwp(birim: str) -> list[str]:
    """`-` öneki kırpılmış yollar. systemd'de `-` = 'yoksa yok say' (birim REDDEDİLMEZ)."""
    return [p.lstrip("-") for p in _rwp_ham(birim)]


@pytest.mark.parametrize("birim", SERTLESTIRILEN)
def test_readwritepaths_state_agacini_kapsiyor(birim):
    """Defter/strategy.yaml/SQLite `/opt/meridian/state` altında. Ağacın kökü açık olduğu için
    kapsanır; `state` hiçbir birimde ERİŞİLEMEZ kalmamalı."""
    yollar = _rwp(birim)
    assert any(p == "/opt/meridian" or p.startswith("/opt/meridian/state") for p in yollar), (
        f"{birim}: ReadWritePaths state'i kapsamıyor: {yollar}")


@pytest.mark.parametrize("birim", SERTLESTIRILEN)
def test_uv_onbellegi_acik(birim):
    """Üç birim de `uv run` ile başlar; `~/.cache` yazılabilir değilse servis BAŞLAMAZ
    (tur-1'de canlıda ölçüldü)."""
    assert "/home/ubuntu/.cache" in _rwp(birim), f"{birim}: uv önbelleği ReadWritePaths'te yok"


@pytest.mark.parametrize("birim", SERTLESTIRILEN)
def test_her_readwritepath_gerekce_tasiyor(birim):
    """YASA: her açılan yol dosyada ADIYLA gerekçelendirilir. Yol yorumlarda geçmiyorsa
    'neden açık' sorusunun cevabı yoktur ve bir sonraki tur onu güvenle daraltamaz."""
    yorum = _yorumlar(birim)
    for p in _rwp(birim):
        assert p in yorum, f"{birim}: `{p}` ReadWritePaths'te ama gerekçesi yorumda yok"


def test_meridian_hermes_dizini_yazilabilir_TUR1_REGRESYONU():
    """TUR-1'İN SESSİZ KIRIKLIĞI. `ProtectHome=read-only` + `~/.hermes` ReadWritePaths'te YOK =
    ajan config/env/skills yazımlarının hepsi EROFS — ve hepsi yutulan istisnaların altında."""
    yollar = _rwp("meridian.service")
    assert "/home/ubuntu/.hermes" in yollar, (
        "meridian.service: /home/ubuntu/.hermes ReadWritePaths'te YOK — tur-1 kırıklığı geri geldi "
        f"(mevcut: {yollar})")
    # `-` ÖNEKİ ŞART: hermes installer'ı düşmüş bir kurulumda dizin YOKTUR (RUNBOOK Bölüm D) ve
    # öneksiz yol systemd'ye birimi REDDETTİRİR → ajansız kurulumda worker HİÇ açılmazdı.
    assert "-/home/ubuntu/.hermes" in _rwp_ham("meridian.service"), (
        "meridian.service: `~/.hermes` yolu `-` öneksiz — ajanı kurulmamış bir makinede birim "
        "'Failed to set up mount namespacing' ile açılmaz; ajan Meridian için ŞART DEĞİLDİR")
    # Buna karşılık ÇEKİRDEK yollar öneksizdir: yoklukları GÜRÜLTÜLÜ olmalı.
    for zorunlu in ("/opt/meridian", "/home/ubuntu/.cache"):
        assert zorunlu in _rwp_ham("meridian.service"), (
            f"`{zorunlu}` `-` önekiyle yazılmış — o dizin yoksa servis zaten koşamaz, "
            "eksikliği sessizce yutulmamalı")


def test_hermes_yolu_kaynakla_dogrulaniyor_kargo_kult_degil():
    """Yol 'olsun diye' değil, KOD oraya yazdığı için açık — kaynak-çivili kanıt."""
    from meridian import hermes

    assert hermes.AGENT_SKILLS_DIR.endswith("/.hermes/skills")
    assert hermes.AGENT_CONFIG.endswith("/.hermes/config.yaml")

    gemini = inspect.getsource(hermes.sync_local_agent_gemini)
    assert 'os.path.expanduser("~/.hermes")' in gemini
    assert "mkstemp(dir=home)" in gemini and "os.replace(tmp, env_path)" in gemini, (
        "sync_local_agent_gemini artık ~/.hermes'e yazmıyorsa ReadWritePaths daraltılabilir — "
        "bu testi ve birim yorumunu birlikte güncelle")

    cfg = inspect.getsource(hermes.config_ensure_integrations)
    assert "AGENT_CONFIG" in cfg and "mkstemp" in cfg and "copy2" in cfg

    sk = inspect.getsource(hermes.sync_agent_skills)
    assert "makedirs(AGENT_SKILLS_DIR" in sk and "os.symlink" in sk

    # KIRILGANLIK SINIFININ KENDİSİ: yazımlar yutulan istisnaların altında → EROFS SESSİZDİR.
    assert "except OSError" in sk, (
        "sync_agent_skills artık hatayı yutmuyorsa bu testin gerekçe metni eskimiştir")


def test_barsarchive_dar_kalmis_hermes_yolu_YOK():
    """Arşivci ajanla konuşmaz — `~/.hermes` ona AÇILMAZ. Ölçü kaynakta: modül hermes'i import
    bile etmez ve tek yazdığı yer `config.STATE / bars_intraday`."""
    yollar = _rwp("meridian-barsarchive.service")
    assert "/home/ubuntu/.hermes" not in yollar, (
        "arşivciye gereksiz yere ~/.hermes açılmış — ölçülmeden genişletme yasak")

    from meridian import barsarchive
    kaynak = pathlib.Path(inspect.getfile(barsarchive)).read_text()
    assert "~/.hermes" not in kaynak and "import hermes" not in kaynak
    assert "config.STATE / ARCHIVE_DIR" in inspect.getsource(barsarchive.archive_dir)


def test_backup_birimi_yedek_hedefini_aciyor():
    """`meridian-backup.service` tar'ı `/home/ubuntu/backups` altına yazar; ProtectHome=read-only
    altında bu yol açık değilse yedek SESSİZCE durur (birimde OnFailure yok)."""
    yollar = _rwp("meridian-backup.service")
    assert "/home/ubuntu/backups" in yollar, f"yedek hedefi ReadWritePaths'te yok: {yollar}"
    metin = _metin("meridian-backup.service")
    assert "/home/ubuntu/backups" in metin and "tar -czf" in metin


def test_backup_kapsami_sprint_haric_bars_dahil():
    """YEDEK KAPSAMI İKİ YÖNLÜ ÇİVİLİ (2026-08-02). Ölçüm (A1): tar 112,5M; `--exclude=state/sprint`
    ile 40.497.179 bayt (~40,5M). state/sprint 438M'dir (4 kum havuzu × ~110M) ve tamamı
    YENİDEN-ÜRETİLEBİLİR — her `sprint.start()` canlı state'ten yeni kum havuzu kurar; onu yedeklemek
    72M'yi her gece boşuna yazmaktı.

    ASIL RİSK TERS YÖNDE: kapsam daraltması iştah açar. Sessiz bir "yedek yine büyüdü" turu bir gün
    `state/bars`ı (59M, WP-U: sağlayıcı geçmişi geri vermiyor) ya da seans-içi arşivleri
    (bars_intraday/intraday_bars — TTL'li Redis akışının TEK kalıcı arşivi) de dışlarsa, kayıp
    RESTORE ANINA kadar görünmez. O tur bu testi DÜŞÜRÜR: yeri doldurulamaz arşivler kapsamda kalır,
    dışlanacaklarsa gerekçe önce buraya yazılır."""
    exec_start = _deger("meridian-backup.service", "ExecStart")
    assert exec_start is not None, "meridian-backup.service: ExecStart yok"
    assert "--exclude=state/sprint" in exec_start, (
        "yedek kum havuzu alt-ağacını yine arşive alıyor (2026-08-02: 438M yeniden-üretilebilir): "
        f"{exec_start!r}")
    for yol in ("state/bars", "state/bars_intraday", "state/intraday_bars"):
        assert f"--exclude={yol}" not in exec_start, (
            f"{yol} yedekten dışlanmış — yeri doldurulamaz arşiv (bars: WP-U; seans-içi: TTL'li "
            f"Redis akışının tek kalıcı kopyası). Bilinçli bir karar ise ÖNCE bu testi ve birim "
            f"yorumunu gerekçesiyle güncelle: {exec_start!r}")


def test_backup_python_bacagi_tirnaksiz_ve_sessiz_degil():
    """BİRİMDE KABUK-SÖZDİZİMİ VARSAYIMI — bu ailenin ÜÇÜNCÜ vakası (öncekiler: fail-notify'ın
    çok-satırlı Python'u, `Environment=` satır-sonu yorumu). 2026-08-02 bakım penceresinde ELLE
    TEST-ATEŞLEME ile bulundu.

    ÖLÇÜM ZİNCİRİ. Eski ExecStart yolu python'a `backup_to(\\"/opt/...\\")` diye, TERS-BÖLÜLÜ
    tırnakla geçiriyordu. systemd TEK TIRNAK İÇİNDE DE C-kaçışlarını çözer → `sh`a ulaşan `-c`
    dizgisinde tırnaklar erken kapanır ve python `backup_to(/opt/...)` görür. Sonuç: H9'dan
    (2026-07-31) beri HER gece SyntaxError; journal'da 08-01 ve 08-02 kayıtları BİREBİR aynı;
    `state/meridian.db.yedek` HİÇ DOĞMAMIŞ; tar'da yedek üyesi 0. Ve arıza SESSİZDİ: `if ... fi;`
    zinciri python'un çıkışını yuttu, `rc` YALNIZ tar'ı ölçtüğü için birim `Result=success` dedi.
    WAL'lı canlı DB'nin ham tar kopyası yarışlıdır — yani sessizce YARIM yedek alıyorduk.

    ÇİVİLENEN İKİ ŞEY. (1) SÖZDİZİMİ: ExecStart'ta `\\"` dizisi GEÇMEZ — yol string-literal değil
    `sys.argv[1]` ile taşınır, böylece systemd'nin kaçış çözmesi bir varsayım olmaktan çıkar.
    (2) SESSİZLİK YASAĞI: python bacağı `|| ok=0` ile işaretlenir ve satır sonu `[ $$ok -eq 1 ]`
    ile birimi DÜŞÜRÜR (tar yine alınır — yedeksiz kalmaktansa eksik yedek + gürültü)."""
    exec_start = _deger("meridian-backup.service", "ExecStart")
    assert exec_start is not None, "meridian-backup.service: ExecStart yok"

    # (a) SINIF ÇİVİSİ: tek tırnak KORUMAZ; ters-bölülü tırnak systemd katmanında çözülür.
    assert '\\"' not in exec_start, (
        "ExecStart'ta ters-bölülü tırnak var — systemd tek-tırnak içinde de C-kaçışını çözer ve "
        f"sh'a bozuk dizgi ulaşır (2026-08-02: H9'dan beri her gece SyntaxError): {exec_start!r}")

    # (b) yol argv'de taşınır (string-literal DEĞİL).
    assert "sys.argv[1]" in exec_start, (
        "yedek yolu python'a argv yerine gömülü dizgiyle geçiyor — kaçış tuzağı geri gelmiş: "
        f"{exec_start!r}")

    # (c) SESSİZLİK YASAĞI: `_deger` HAM değeri döndürür, `$$` dosyadaki gibi çift dolar durur.
    assert "|| ok=0" in exec_start, (
        f"python bacağının arızası işaretlenmiyor — sessiz yedek kaybı sınıfı geri döner: {exec_start!r}")
    assert "[ $$ok -eq 1 ]" in exec_start, (
        "birim python bacağı düşse de `success` beyan ediyor — `rc` yalnız tar'ı ölçer "
        f"(2026-08-02 vakasının TAM kök nedeni): {exec_start!r}")


# ==================================================================================================
# 3 — SIR DÜZENİ: token birimde DEĞİL, `.dash.env`te
# ==================================================================================================
def test_dash_env_environmentfile_duzeni_korunmus():
    assert _deger("meridian.service", "EnvironmentFile") == "-/opt/meridian/.dash.env", (
        "meridian.service: `EnvironmentFile=-/opt/meridian/.dash.env` yok — depodaki birimi "
        "canlıya kopyalayan prosedür 2026-07-31 token rotasyonunu geri alır")


def test_token_birim_dosyasinda_duz_metin_DEGIL():
    for birim in ("meridian.service", "meridian-barsarchive.service",
                  "meridian-backup.service", "meridian-fail-notify.service"):
        for k, v, no in _service(birim):
            if k != "Environment":
                continue
            ad = v.split("=", 1)[0]
            assert "TOKEN" not in ad.upper() and "SECRET" not in ad.upper() \
                and "KEY" not in ad.upper() and "PASSWORD" not in ad.upper(), (
                f"{birim}:{no} birim dosyaları 0644'tür — sır `Environment=` ile taşınMAZ: {v!r}")
        # YORUMLARDA geçebilir (tarihçe anlatılır); DİREKTİF değerinde geçemez.
        for k, v, no in _service(birim):
            assert "CHANGEME" not in v, (
                f"{birim}:{no} CHANGEME yer tutucusu direktife geri gelmiş "
                f"(canlı birimde 2026-07-31'den beri yok): {k}={v!r}")


def test_barsarchive_env_dosyasi_duzeni_korunmus():
    """LoadCredential göçü AYRI penceredir; bu turda `.env` düzeni AYNEN KALIR."""
    assert _deger("meridian-barsarchive.service", "EnvironmentFile") == "-/opt/meridian/.env"
    assert _deger("meridian-barsarchive.service", "Environment") is not None


# ==================================================================================================
# 4 — `Environment=` SATIR-SONU YORUMU YASAK (2026-08-01 vakası)
# ==================================================================================================
@pytest.mark.parametrize("birim", sorted(p.name for p in UNITS.glob("*.service")))
def test_environment_satirinda_satir_sonu_yorumu_yok(birim):
    """systemd `Environment=` satırında `#`i yorum SAYMAZ: boşluklarla ayrı atamalara böler,
    geçersiz sayar ve değişken SESSİZCE boş kalır. Gerekçe AYRI satırda yazılır."""
    for k, v, no in _service(birim):
        if k in ("Environment", "EnvironmentFile"):
            assert "#" not in v, (
                f"{birim}:{no} `{k}=` satırında satır-sonu yorumu var → systemd atamayı düşürür "
                f"ve journal'e 'Invalid environment assignment' yazar: {v!r}")


@pytest.mark.parametrize("birim", sorted(p.name for p in UNITS.glob("*.timer")))
def test_timer_dosyalarinda_service_bolumu_yok(birim):
    """Sertleştirme direktifleri süreç yürütmeye aittir; timer'da geçersizdir. Bir timer'da
    `[Service]` görülmesi, sertleştirmenin YANLIŞ dosyaya yazıldığının işaretidir."""
    assert "Service" not in _bolumler(_metin(birim)), f"{birim}: timer'da [Service] bölümü var"


# ==================================================================================================
# 5 — ORTAK DİREKTİF TUTARLILIĞI + SESSİZ EKLEME/ATLAMA YASAĞI
# ==================================================================================================
def test_uc_birimin_ortak_direktifleri_ayrismiyor():
    """Aynı sertleştirme setini taşıyan birimler ayrışırsa 'sertleştirildi' cümlesi ölçülemez
    hâle gelir: hangi birimin neyi taşıdığı ancak canlıda anlaşılırdı."""
    for anahtar in ORTAK_SET:
        degerler = {b: _deger(b, anahtar) for b in SERTLESTIRILEN}
        assert len(set(degerler.values())) == 1, f"`{anahtar}` birimler arasında ayrışmış: {degerler}"


@pytest.mark.parametrize("birim", SERTLESTIRILEN)
def test_disarida_birakilanlar_sessizce_eklenmemis(birim):
    """Ölçülmemiş kalem eklenmez (kırılan canlı, sertleştirmemekten beterdir)."""
    anahtarlar = {k for k, _, _ in _service(birim)}
    for d in DISARIDA_BIRAKILANLAR:
        assert d not in anahtarlar, (
            f"{birim}: `{d}` ölçülmeden eklenmiş — gerekçeli yorumu var ama direktifi olmamalı")


def test_disarida_birakilan_her_kalem_gerekce_tasiyor():
    """YASA: sessiz atlama yok. Gerekçelerin TAM METNİ meridian.service'te durur; kardeş birimler
    oraya İSİMLE atıf yapar (aynı gerekçeyi üç yere kopyalamak, üçünün ayrışması demektir)."""
    ana = _yorumlar("meridian.service")
    for d in DISARIDA_BIRAKILANLAR:
        assert d in ana, f"meridian.service: `{d}` dışarıda ama gerekçesi yorumda YOK"
    # Gerekçe bir etiket değil, cümle olmalı (YASA 4 ruhu: ≥20 karakter gerekçe).
    blok = re.search(r"DIŞARIDA BIRAKILANLAR(.*?)\n# EN SON SATIR", ana, re.S)
    assert blok and len(blok.group(1)) > 600, "dışarıda-bırakma bloğu gerekçe taşımıyor"
    for kardes in ("meridian-barsarchive.service", "meridian-backup.service"):
        assert "meridian.service" in _yorumlar(kardes), f"{kardes}: gerekçe atfı yok"


def test_fail_notify_sertlestirilmedi_ama_gerekcesi_yazili():
    """Son katman BİLEREK sertleştirilmedi: kendi arızasını `exit 0`/`SuccessExitStatus=0 1` ile
    yutar, yani bir sertleştirme hatası TANIM GEREĞİ görünmez olurdu."""
    ad = "meridian-fail-notify.service"
    anahtarlar = {k for k, _, _ in _service(ad)}
    assert "SystemCallFilter" not in anahtarlar and "ProtectSystem" not in anahtarlar
    yorum = _yorumlar(ad)
    assert "BİLEREK" in yorum and "H3 SERTLEŞTİRME" in yorum, f"{ad}: dışarıda-bırakma gerekçesiz"
    assert _deger(ad, "SuccessExitStatus") == "0 1", "gerekçenin dayanağı (yutulan arıza) değişmiş"


def test_tur1_drop_in_emekli_hicbir_direktif_tasimiyor():
    """İKİ KAYNAK YASAK: drop-in skaler direktifi birim dosyasının üstüne SESSİZCE yazar ve
    dosyayı okuyan mühendis yürürlükteki ayarı yanlış okur."""
    metin = _metin("sertlestirme.conf")
    svc = _bolumler(metin).get("Service", [])
    assert svc == [], f"sertlestirme.conf hâlâ direktif taşıyor: {svc}"
    assert "EMEKLİ" in metin and "/home/ubuntu/.hermes" in metin, (
        "emeklilik gerekçesi (ve tur-1'in eksik yolu) dosyada yazılı olmalı")


# ==================================================================================================
# 6 — RUNBOOK: uygulama prosedürü GERİ-ALINABİLİR ve NÖBETLİ olmalı
# ==================================================================================================
def test_runbook_uygulama_proseduru_tam():
    rb = (UNITS / "RUNBOOK.md").read_text()
    for parca, neden in (
        ("H3 tur-2", "bölüm başlığı"),
        ("daemon-reload", "kopyalama sonrası yeniden yükleme"),
        ("systemctl restart meridian meridian-barsarchive", "yeniden başlatma"),
        ("h3-tur1-yedek", "GERİ-ALMA yedeği (eski birim geri konabilmeli)"),
        ("GERİ ALMA", "geri-alma adımı"),
        ("rm -f /etc/systemd/system/meridian.service.d/sertlestirme.conf", "tur-1 drop-in söküm"),
        ("systemd-analyze security", "beklenen-skor ölçümü"),
        ("healthz", "duman testi: pano"),
        ("HERMES-RW-OK", "duman testi: ~/.hermes yazma probu"),
        ("scheduler_status.json", "duman testi: tick akışı"),
        ("barsarchive --ozet", "duman testi: bar akışı"),
        ("meridian-backup.service", "yedek biriminin elle provası"),
        ("24 SAAT", "seccomp nöbeti"),
        ("SIGSYS", "seccomp arıza şekli"),
        ("SystemCallLog=@clock", "log-modu reçetesi"),
    ):
        assert parca in rb, f"RUNBOOK'ta eksik ({neden}): {parca!r}"

    assert "2,5–3,8" in rb and "TAHMİN" in rb, (
        "beklenen skor TAHMİN olarak işaretlenmeli — ölçülmemiş sayı ölçülmüş gibi yazılamaz")
    # Tarihçe anlatılabilir; ÖLÜ KOMUT reçete olarak duramaz. Birimde artık CHANGEME yok →
    # o `sed` sessizce 0 döner ve pano TOKEN'SIZ kalırdı.
    assert 'sed -i "s/CHANGEME' not in rb and "sed -i \"s/CHANGEME" not in rb, (
        "RUNBOOK hâlâ ölü `sed CHANGEME` reçetesini veriyor — token .dash.env'e taşındı")


def test_runbook_token_adimi_dash_env_uretiyor():
    rb = (UNITS / "RUNBOOK.md").read_text()
    assert "/opt/meridian/.dash.env" in rb and "chmod 600 /opt/meridian/.dash.env" in rb, (
        "kurulum prosedürü token'ı 0600 `.dash.env` olarak üretmeli")


# ==================================================================================================
# 7 — PrivateTmp'nin ÖLÇÜLMÜŞ yan etkisi belgelenmiş mi
# ==================================================================================================
def test_private_tmp_yan_etkisi_kaynakla_ve_belgeyle_ortusuyor():
    """`PrivateTmp=true` `/tmp/prescreen-*`i KIRMAZ ama operatörden GİZLER. Kaynakta gerçekten
    /tmp kullanılıyorsa, belge bunu anlatmak ZORUNDA."""
    from meridian import hermes_composite
    kaynak = pathlib.Path(inspect.getfile(hermes_composite)).read_text()
    if '"/tmp/prescreen-' not in kaynak and "f\"/tmp/prescreen-" not in kaynak:
        pytest.skip("kod artık /tmp kullanmıyor — belge notu da kaldırılabilir")
    assert "/tmp/prescreen-" in _yorumlar("meridian.service"), "birimde yan etki notu yok"
    assert "systemd-private-" in (UNITS / "RUNBOOK.md").read_text(), (
        "RUNBOOK özel /tmp'ye nasıl bakılacağını yazmıyor")
