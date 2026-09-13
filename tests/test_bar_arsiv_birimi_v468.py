"""test_bar_arsiv_birimi_v468.py — meridian-bar-arsiv.{service,timer}: TSK-020 [UYGULA-3] haftalık parquet
arşivi tazeleme birimi (2026-09-13). Ölçülen: birim/timer dosyaları var, ExecStart aracın GERÇEK bayraklarını
taşır, sertleştirme kümesi referans birimden türetilip birebir, timer Pazar 22:00 UTC + Persistent, timer
`etkin_timerlar`da, [Install] bölümü serviste YOK (v327 dersi). Şablon: test_defter_ozeti_retain_v464.py g-bölümü."""
import pathlib
import re

KOK = pathlib.Path(__file__).resolve().parent.parent
DEPLOY = KOK / "deploy" / "oracle-a1"
BIRIM_ADI = "meridian-bar-arsiv"
ARAC = KOK / "ops" / "bar_arsivle.py"


def _servis() -> str:
    return (DEPLOY / f"{BIRIM_ADI}.service").read_text(encoding="utf-8")


def test_g1_birim_ve_timer_dosyalari_VAR():
    assert (DEPLOY / f"{BIRIM_ADI}.service").exists()
    assert (DEPLOY / f"{BIRIM_ADI}.timer").exists()


def test_g2_birim_ONESHOT_ExecStart_araci_ve_GERCEK_bayraklari_gosterir():
    metin = _servis()
    assert "Type=oneshot" in metin and "User=ubuntu" in metin
    assert "WorkingDirectory=/opt/meridian" in metin
    exec_satiri = [s for s in metin.splitlines() if s.startswith("ExecStart=")]
    assert len(exec_satiri) == 1, exec_satiri
    parcalar = exec_satiri[0].split("=", 1)[1].split()
    assert parcalar[:2] == ["/opt/meridian/.venv/bin/python", "/opt/meridian/ops/bar_arsivle.py"]
    assert "--uygula" in parcalar, "araç varsayılan KURU — --uygula olmadan hiçbir şey yazmaz"
    # bayraklar aracın argparse'ından TÜRETİLİR (elle liste ayrışırdı): her `--x` gerçekten tanımlı olmalı
    kaynak = ARAC.read_text(encoding="utf-8")
    tanimli = set(re.findall(r'add_argument\("(--[a-z-]+)"', kaynak))
    for bayrak in (p for p in parcalar[2:] if p.startswith("--")):
        assert bayrak in tanimli, f"ExecStart bayrağı araçta TANIMSIZ: {bayrak}"
    assert "--kaynak-dizin" in parcalar and "--hedef" in parcalar
    assert "TimeoutStartSec=600" in metin
    # DİREKTİF satırları ölçülür, şerh değil (şerh yokluğun gerekçesini ADIYLA anlatır ve anlatmalı)
    direktifler = [s.strip() for s in metin.splitlines() if s.strip() and not s.lstrip().startswith("#")]
    assert not [s for s in direktifler if s.startswith("SuccessExitStatus")], \
        "sıfır dışı her kod failed olmalı (5 = hedefe dokunulmadı)"
    assert not [s for s in metin.splitlines() if s.strip() == "[Install]"], "tetik YALNIZ timer (v327)"


def test_g3_sertlestirme_satirlari_REFERANS_ile_AYNI():
    referans = (DEPLOY / "meridian-defter-ozeti-retain.service").read_text(encoding="utf-8")
    yeni = _servis()
    onekler = ("NoNewPrivileges", "CapabilityBoundingSet", "ProtectSystem", "ProtectHome",
               "PrivateTmp", "ProtectKernelTunables", "ProtectKernelModules", "ProtectKernelLogs",
               "ProtectClock", "ProtectControlGroups", "ProtectHostname", "RestrictNamespaces",
               "RestrictSUIDSGID", "RestrictRealtime", "LockPersonality",
               "RestrictAddressFamilies", "SystemCallArchitectures", "SystemCallFilter",
               "ReadWritePaths")
    beklenen = [s.strip() for s in referans.splitlines() if s.strip().split("=")[0] in onekler]
    assert len(beklenen) == len(onekler), beklenen
    for satir in beklenen:
        assert satir in yeni, f"sertleştirme satırı EKSİK/AYRIK: {satir}"


def test_g4_timer_PAZAR_2200_UTC_PERSISTENT_ve_sabit_pay():
    metin = (DEPLOY / f"{BIRIM_ADI}.timer").read_text(encoding="utf-8")
    assert "OnCalendar=Sun *-*-* 22:00:00 UTC" in metin
    assert "Persistent=true" in metin and "FixedRandomDelay=true" in metin
    assert "WantedBy=timers.target" in metin


def test_g5_timer_ETKIN_LISTEDE_ve_A0_glob_kapsaminda():
    defaults = (KOK / "deploy" / "ansible" / "roles" / "meridian_a1" / "defaults" / "main.yml").read_text(encoding="utf-8")
    blok = defaults[defaults.index("etkin_timerlar:"):]
    blok = blok[:blok.index("\n\n")]
    assert f"{BIRIM_ADI}.timer" in blok, "timer etkin listede değil — haftalık tazeleme hiç açılmaz"
    assert "birim_kaynaklari" in defaults and ".timer" in defaults  # genel glob mekanizması kopyalar


def test_g6_arac_worker_kosarken_GUVENLI_beyanini_tasir():
    """Birim worker'a bağımlı değil (After/Requires=meridian.service YOK) — bu ancak aracın
    'CSV yalnız okunur + geçici ad + os.replace' beyanı doğruysa meşrudur; beyan araçta durmalı."""
    assert "WORKER KOŞARKEN GÜVENLİDİR" in ARAC.read_text(encoding="utf-8")
    assert "Requires=meridian.service" not in _servis()
