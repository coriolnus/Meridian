"""test_dagit_istenen_durum_v367.py — dagit bakım penceresi birim İSTENEN-DURUM koruması
(TSK-092/TSK-008; vaka ×2: 2026-08-31 + 2026-09-01 gecesi).

VAKA: operatör kararıyla `meridian-learn` geri-dolum bitene dek disabled+stopped; dagit'in
[4] bakım penceresi SABİT ÜÇLÜ `systemctl start` satırıyla onu her dağıtımda geri açtı —
iki gece üst üste elle yakalandı/durduruldu. "Her dağıtım sonrası learn kapalı mı" kontrolü
insana yaslanıyordu ve insan (Rol-1 dahil) atladı.

SÖZLEŞME: istenen durum systemd'nin KENDİ beyanıdır (`is-enabled`). Bakım penceresi:
  * aktif olanı DURDURUR (sabit aday listesi kalabilir — durdurmak güvenli yöndür; bedeli
    beyanlı: operatörün elle başlattığı disabled birim pencereden sonra kapalı kalır, isteyen
    enable eder),
  * yalnız `enabled` olanı GERİ BAŞLATIR — start satırında birim adı SABİTLENEMEZ,
  * atlananı ADIYLA raporlar (sessiz atlama, sessiz başlatmayla aynı sınıf körlüktür),
  * `meridian` çekirdek birimi başlatma listesinde DEĞİLSE dağıtım yüksek sesle durur
    (motoru kapalı bırakan pencere sessiz olamaz).

YÖNTEM (v266 ailesi): adımlar SSH ister, koşturulamaz — ölçülen katman yapı/sözleşmedir
(`bash -n` + metin çivileri, her biri bu docstring'deki maddeye çapalı).
"""
from __future__ import annotations

import pathlib
import re
import subprocess

DAGIT = pathlib.Path(__file__).resolve().parent.parent / "dagit.sh"
METIN = DAGIT.read_text(encoding="utf-8")
_BLOK = METIN.split("=== [4/5]")[1].split("=== [5/5]")[0]


def test_sozdizimi_gecerli():
    p = subprocess.run(["bash", "-n", str(DAGIT)], capture_output=True, text=True)
    assert p.returncode == 0, p.stderr


def test_start_satiri_birim_adi_sabitleyemez():
    # Vakanın kökü: `systemctl start meridian meridian-barsarchive meridian-learn` sabit paketi.
    for satir in _BLOK.splitlines():
        if "systemctl start" in satir and not satir.lstrip().startswith("#"):
            assert "meridian-learn" not in satir, f"start satırı birimi sabitliyor: {satir.strip()}"
            assert not re.search(r"systemctl start\s+meridian\b", satir), \
                f"start satırı birimi sabitliyor: {satir.strip()}"


def test_baslatma_listesi_is_enabled_ile_turetilir():
    assert "is-enabled" in _BLOK, "[4] bloğunda istenen-durum (is-enabled) türetimi yok"


def test_atlanan_birim_adiyla_raporlanir():
    assert "başlatılmadı" in _BLOK, "atlanan birim raporu yok (sessiz atlama)"


def test_cekirdek_birim_guvenlik_kapisi():
    # `meridian` başlatma listesinde değilse pencere yüksek sesle durmalı.
    assert re.search(r"meridian.*(baslat|BASLAT).*|(baslat|BASLAT).*meridian", _BLOK) and \
        "exit 1" in _BLOK, "çekirdek-birim kapısı ([4] içinde exit'li) bulunamadı"


def test_durdurma_sabit_kalabilir_ama_ucluyu_kapsar():
    stop = [s for s in _BLOK.splitlines()
            if "systemctl stop" in s and not s.lstrip().startswith("#")]
    assert stop, "durdurma satırı yok"
    assert all(x in stop[0] for x in ("meridian", "meridian-barsarchive", "meridian-learn")), \
        "durdurma aday kümesi daraltılmış — durdurmak güvenli yöndür, küme kalır"


def test_turetim_disabled_son_elemanla_SIFIR_cikar(tmp_path):
    """VAKA 2026-09-02 (sabah penceresi, ilk gerçek koşum): `[ … ] && printf` kalıbı döngünün
    SON elemanı disabled olunca uzak kabuğu 1 ile bitirdi; ssh 1 döndürdü, yerel `set -e`
    `_BASLAT=$( … )` atamasında dagit'i [4] başlığından hemen sonra SESSİZCE öldürdü — rsync
    inmiş, worker restart edilmemiş, beyan yazılmamıştı (iki gerçek: diskte yeni, süreçte eski
    kod). Betiğin kendi 132. satır doktrini tam bu sınıfı yasaklar; v367'nin metin çivileri
    türetmeyi KOŞMADIĞI için tuzak yeşilken yaşadı. Bu çivi türetme snippet'ini dagit.sh'nin
    GERÇEK metninden söküp sahte `systemctl` ile koşar: disabled son elemanla çıkış kodu 0
    ve liste yalnız enabled birimleri taşımalı."""
    m = re.search(r"_BASLAT=\"\$\(\"\$\{SSH\[@\]\}\" '(.+?)'\)\"", METIN, re.S)
    assert m, "_BASLAT türetim snippet'i dagit.sh'de bulunamadı (yapı değiştiyse çiviyi taşı)"
    snippet = m.group(1)

    stub = tmp_path / "systemctl"
    stub.write_text(
        "#!/bin/bash\n"
        "# sahte is-enabled: gerçek semantik — enabled→stdout'a 'enabled' + çıkış 0;\n"
        "# disabled→stdout'a 'disabled' + ÇIKIŞ 1 (vakanın tetiği tam bu koddur).\n"
        'case "$2" in\n'
        "  meridian|meridian-barsarchive) echo enabled; exit 0;;\n"
        "  meridian-learn) echo disabled; exit 1;;\n"
        "  *) echo unknown; exit 1;;\n"
        "esac\n", encoding="utf-8")
    stub.chmod(0o755)

    p = subprocess.run(["bash", "-c", snippet], capture_output=True, text=True,
                       env={"PATH": f"{tmp_path}:/usr/bin:/bin"})
    assert p.returncode == 0, (
        f"türetim snippet'i disabled-son-eleman dünyasında {p.returncode} ile çıktı — "
        f"set -e altındaki atama dagit'i yine sessizce öldürür (stderr: {p.stderr!r})")
    assert p.stdout.split() == ["meridian", "meridian-barsarchive"], \
        f"liste yanlış: {p.stdout!r} — enabled ikili beklenirdi, learn dışarıda"
