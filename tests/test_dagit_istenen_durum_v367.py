"""test_dagit_istenen_durum_v367.py — dagit bakım penceresi birim İSTENEN-DURUM koruması
(TSK-092/TSK-008; vaka ×2: 2026-08-31 + 2026-09-01 gecesi).

VAKA: operatör kararıyla `meridian-learn` geri-dolum bitene dek disabled+stopped; dagit'in
[4] bakım penceresi SABİT ÜÇLÜ `systemctl start` satırıyla onu her dağıtımda geri açtı —
iki gece üst üste elle yakalandı/durduruldu. "Her dağıtım sonrası learn kapalı mı" kontrolü
insana yaslanıyordu ve insan (Rol-1 dahil) atladı.

SÖZLEŞME: istenen durum systemd'nin KENDİ beyanıdır (`is-enabled`), o ANKİ durum ise
`is-active`. Bakım penceresi:
  * yalnız PENCERE ÖNCESİ aktif olanı DURDURUR — aday kümesi (üçlü) kalır ama stop satırında
    birim adı SABİTLENEMEZ: zaten `inactive` olan birime stop GÖNDERİLMEZ (2026-09-03 kapsam
    genişlemesi, TSK-092 (a)). Ölçüt `!= inactive`: `activating`/`deactivating`/`failed`
    hâllerinde süreç ya da artık durum vardır, durdurmak güvenli YÖNDÜR; yalnız temiz
    `inactive` atlanır. Bedeli beyanlı: operatörün elle başlattığı disabled birim pencereden
    sonra kapalı kalır (start `is-enabled`'dan türer), isteyen enable eder,
  * yalnız `enabled` olanı GERİ BAŞLATIR — start satırında birim adı SABİTLENEMEZ,
  * atlananı ADIYLA raporlar (sessiz atlama, sessiz başlatmayla aynı sınıf körlüktür),
  * `meridian` çekirdek birimi başlatma listesinde DEĞİLSE dağıtım yüksek sesle durur
    (motoru kapalı bırakan pencere sessiz olamaz).

R-0 (düzeltme turu 1, 2026-09-03): SÖZLEŞMEYE ÜÇÜNCÜ MADDE — `enabled + inactive` bir ANOMALİDİR
ve dağıtımı DURDURUR ([F10] kapısı, `exit 3`, rsync'ten ve stop'tan ÖNCE, kuru koşumda da).
Gerekçe A1'de ölçüldü (2026-09-03 09:40Z): üç aday birim de `Type=simple` + `Restart=always`,
`TriggeredBy=` boş — yani bu hâl normal değil, ya elle `stop` edilmiştir (kalıcı niyet
`disable --now` ile beyan edilmeliydi) ya da start-limit'e çarpıp düşmüştür (arıza). İki hâlde de
pencere birimi `is-enabled`dan türetip sessizce diriltir ve bir olayı MASKELER. Bu kapı `_BASLAT`
türetiminin kopyası değildir: `_BASLAT` "ne başlatılmalı", [F10] "ölçülen dünya tutarlı mı" diye
sorar. Override bayrağı YOK.

YÖNTEM (v266 ailesi): adımlar SSH ister, koşturulamaz — ölçülen katman yapı/sözleşmedir
(`bash -n` + metin çivileri, her biri bu docstring'deki maddeye çapalı). İSTİSNA: türetim
snippet'leri ve [F10] kapısı dagit.sh'nin GERÇEK metninden SÖKÜLÜP sahte `systemctl` ile
KOŞULUR — metin çivisi yeşilken yaşayan bir tuzak ölçüldü (2026-09-02 sabah penceresi).
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


def test_stop_satiri_birim_adi_sabitleyemez():
    """TSK-092 (a), 2026-09-03: stop satırı da sabit üçlü paket OLAMAZ — pencere öncesi
    `is-active` ölçülür, zaten inactive birime stop gönderilmez. (Önceki sözleşme "durdurma
    kümesi sabit kalabilir" diyordu; aday KÜMESİ hâlâ üçlü, sabitlenemeyen şey stop SATIRIdır.)"""
    stop = [s for s in _BLOK.splitlines()
            if "systemctl stop" in s and not s.lstrip().startswith("#")]
    assert stop, "durdurma satırı yok"
    for satir in stop:
        assert "meridian-learn" not in satir, f"stop satırı birimi sabitliyor: {satir.strip()}"
        assert not re.search(r"systemctl stop\s+meridian\b", satir), \
            f"stop satırı birimi sabitliyor: {satir.strip()}"


def test_durdurma_aday_kumesi_ucluyu_kapsar():
    """Aday kümesi daralmadı: türetim döngüsü hâlâ üç birimi de SORAR (biri unutulursa
    2026-08-24 `meridian-learn` unutma vakası tekrarlanır)."""
    assert "is-active" in _BLOK, "[4] bloğunda o-anki-durum (is-active) türetimi yok"
    # SÖKÜCÜ TEK YERDE (düzeltme turu 1, inceleme K-2, 2026-09-03): aynı yapısal sözleşmenin
    # regex'i bu dosyada iki, v266'da bir kez yazılıydı — üçü ayrışırsa hangi çivinin haklı
    # olduğu belirsizleşir. `_snippet` tek kaynaktır; v266 da onu ithal eder.
    snippet = _snippet("_DURDUR")
    for u in ("meridian", "meridian-barsarchive", "meridian-learn"):
        assert re.search(rf"\b{re.escape(u)}\b", snippet), \
            f"durdurma aday kümesinde {u} yok — küme daraltılmış"


def test_atlanan_stop_adiyla_raporlanir():
    assert "stop gönderilmedi" in _BLOK, \
        "zaten inactive birim ADIYLA raporlanmıyor (sessiz atlama, sessiz start ile aynı sınıf)"


def _sahte_systemctl(tmp_path, enabled, active):
    """Gerçek semantikli sahte `systemctl`: is-enabled/is-active stdout'a durumu basar ve
    olumsuz hâlde ÇIKIŞ 1 döndürür (v367 vakasının tetiği tam bu çıkış kodudur)."""
    dallar = []
    for u in ("meridian", "meridian-barsarchive", "meridian-learn"):
        dallar.append(
            f'  {u}) case "$1" in\n'
            f'       is-enabled) echo {enabled[u]}; [ "{enabled[u]}" = enabled ]; exit $?;;\n'
            f'       is-active)  echo {active[u]};  [ "{active[u]}" = active ]; exit $?;;\n'
            f'       *) exit 1;; esac;;\n')
    stub = tmp_path / "systemctl"
    stub.write_text("#!/bin/bash\ncase \"$2\" in\n" + "".join(dallar)
                    + '  *) echo unknown; exit 1;;\nesac\n', encoding="utf-8")
    stub.chmod(0o755)
    return stub


def _snippet(ad):
    m = re.search(rf"{ad}=\"\$\(\"\$\{{SSH\[@\]\}}\" '(.+?)'\)\"", METIN, re.S)
    assert m, f"{ad} türetim snippet'i dagit.sh'de bulunamadı (yapı değiştiyse çiviyi taşı)"
    return m.group(1)


def test_stop_listesi_is_active_ten_turer(tmp_path):
    """TSK-092 (a) DAVRANIŞ çivisi (v367 sahte-systemctl ailesi). Tek dünyada üç hüküm:
      * `meridian` enabled+active                    → İKİSİNİ de alır,
      * `meridian-barsarchive` DISABLED ama AKTİF    → stop ALIR, start ALMAZ (beyanlı bedel:
        operatörün elle başlattığı disabled birim pencereden sağ çıkmaz — kalıcılık `enable`dır),
      * `meridian-learn` disabled ve inactive        → ne stop ne start ALIR.

    DÜNYA DEĞİŞTİ (R-0, düzeltme turu 1, 2026-09-03): önceki hâlde `meridian-barsarchive`
    `enabled + inactive` idi. O hâl artık bir ANOMALİdir ve [F10] kapısı dağıtımı durdurur
    (`test_enabled_ama_INAKTIF_birim_DAGITIMI_DURDURUR`) — yani pencereye HİÇ gelinmez.
    "inactive birime stop gönderilmez" hükmü burada `meridian-learn` üzerinden ölçülüyor."""
    enabled = {"meridian": "enabled", "meridian-barsarchive": "disabled",
               "meridian-learn": "disabled"}
    active = {"meridian": "active", "meridian-barsarchive": "active",
              "meridian-learn": "inactive"}
    _sahte_systemctl(tmp_path, enabled, active)
    ortam = {"PATH": f"{tmp_path}:/usr/bin:/bin"}

    d = subprocess.run(["bash", "-c", _snippet("_DURDUR")], capture_output=True, text=True,
                       env=ortam)
    assert d.returncode == 0, (
        f"_DURDUR türetimi {d.returncode} ile çıktı — set -e altındaki atama dagit'i sessizce "
        f"öldürür (stderr: {d.stderr!r})")
    assert d.stdout.split() == ["meridian", "meridian-barsarchive"], (
        f"stop listesi yanlış: {d.stdout!r} — aktif ikili beklenirdi; inactive `meridian-learn` "
        f"stop ALMAZ, `is-enabled` stop tarafını HİÇ ilgilendirmez")

    b = subprocess.run(["bash", "-c", _snippet("_BASLAT")], capture_output=True, text=True,
                       env=ortam)
    assert b.returncode == 0, f"_BASLAT türetimi {b.returncode} ile çıktı (stderr: {b.stderr!r})"
    assert b.stdout.split() == ["meridian"], (
        f"start listesi yanlış: {b.stdout!r} — disabled iki birim de dışarıda kalmalıydı "
        f"(elle başlatılmış olması istenen durumu DEĞİŞTİRMEZ)")


def test_stop_listesi_temiz_olmayan_halleri_kapsar(tmp_path):
    """Ölçüt `= active` DEĞİL `!= inactive`: `activating`/`failed` hâllerinde süreç ya da
    artık durum vardır; atlanırsa eski bytecode pencereden sağ çıkar (2026-08-24 sınıfı)."""
    enabled = {"meridian": "enabled", "meridian-barsarchive": "enabled",
               "meridian-learn": "disabled"}
    active = {"meridian": "activating", "meridian-barsarchive": "failed",
              "meridian-learn": "inactive"}
    _sahte_systemctl(tmp_path, enabled, active)
    d = subprocess.run(["bash", "-c", _snippet("_DURDUR")], capture_output=True, text=True,
                       env={"PATH": f"{tmp_path}:/usr/bin:/bin"})
    assert d.returncode == 0, f"_DURDUR türetimi {d.returncode} ile çıktı (stderr: {d.stderr!r})"
    assert d.stdout.split() == ["meridian", "meridian-barsarchive"], (
        f"stop listesi yanlış: {d.stdout!r} — activating/failed durdurulur, yalnız temiz "
        f"inactive atlanır")


# =================================================================================================
# [F10] İSTENEN-DURUM ANOMALİSİ — `enabled + inactive` = DAĞITIM DUR (R-0, düzeltme turu 1)
# -------------------------------------------------------------------------------------------------
# ÖLÇÜM (Rol-1, A1'de, 2026-09-03 09:40Z): üç aday birim de `Type=simple` + `Restart=always` ve
# `TriggeredBy=` BOŞ (hiçbir zamanlayıcı tetiklemiyor). Bu üç olgunun birlikte anlamı şudur:
# `enabled + inactive` bir SİMPLE birimin normal durumu DEĞİLDİR — ya elle `stop` edilmiştir
# (kalıcı niyet `disable --now` ile beyan edilmeliydi) ya da start-limit'e çarpıp DÜŞMÜŞTÜR
# (arıza). İki hâlde de [4] penceresi birimi `is-enabled`dan türetip sessizce DİRİLTİR ve bir
# olayı maskeler — TSK-092'nin kapattığı "sessiz geri açma" sınıfının ikinci yüzü.
# Bu kapı `_BASLAT` türetiminin KOPYASI DEĞİLDİR: `_BASLAT` "ne başlatılmalı" diye sorar, bu
# kapı "ölçülen dünya kendi içinde tutarlı mı" diye sorar (anomali). Override bayrağı YOK.
# =================================================================================================

_F10_BAS = 'echo "=== [F10]'
_KURU_CIKIS = 'if [[ "${1:-}" != "--uygula" ]]'


def _kapi_blogu() -> str:
    """[F10] kapısının dagit.sh'deki GERÇEK metni. Kesme noktası kuru-koşum çıkışıdır: kapı
    o çıkıştan ÖNCE durmak zorunda, yoksa `--dry-run` (argümansız koşum) anomaliyi görmez —
    "erken gerçek" tam olarak budur."""
    assert _F10_BAS in METIN, "[F10] istenen-durum anomali kapısı dagit.sh'de yok"
    kuyruk = METIN.split(_F10_BAS, 1)[1]
    assert _KURU_CIKIS in kuyruk, (
        "[F10] kapısı kuru-koşum çıkışından SONRA duruyor — kuru koşum anomaliyi göremez")
    return _F10_BAS + kuyruk.split(_KURU_CIKIS, 1)[0]


def _kapiyi_kos(tmp_path, enabled, active):
    """Kapıyı dagit.sh'nin GERÇEK metninden söküp koşar. `SSH=(bash -c)` uzak kabuğu yerele
    indirir; `set -euo pipefail` betiğin kendi ortamıdır (atama tuzağı burada da ölçülsün)."""
    _sahte_systemctl(tmp_path, enabled, active)
    betik = "set -euo pipefail\nSSH=(bash -c)\n" + _kapi_blogu()
    return subprocess.run(["bash", "-c", betik], capture_output=True, text=True,
                          env={"PATH": f"{tmp_path}:/usr/bin:/bin"})


def test_enabled_ama_INAKTIF_birim_DAGITIMI_DURDURUR(tmp_path):
    """R-0 ASIL ÇİVİSİ: `meridian-barsarchive` enabled ama inactive → kapı `exit 3` ile DURUR,
    birimi ADIYLA basar ve İKİ çareyi de adıyla söyler. Eskiden bu dünya "stop YOK / start VAR"
    diye sessizce geçiyordu; pencere birimi diriltir ve düşüşün nedeni hiç sorulmazdı."""
    enabled = {"meridian": "enabled", "meridian-barsarchive": "enabled",
               "meridian-learn": "disabled"}
    active = {"meridian": "active", "meridian-barsarchive": "inactive",
              "meridian-learn": "inactive"}
    p = _kapiyi_kos(tmp_path, enabled, active)
    assert p.returncode == 3, (
        f"anomali kapısı 3 ile DURMADI (rc={p.returncode}) — enabled+inactive birim pencerede "
        f"sessizce diriltilir (stdout: {p.stdout!r} stderr: {p.stderr!r})")
    assert "meridian-barsarchive" in p.stdout, "duran birim ADIYLA raporlanmıyor"
    assert "systemctl start meridian-barsarchive" in p.stdout, "ilk çare (start) adıyla basılmıyor"
    assert "systemctl disable --now meridian-barsarchive" in p.stdout, \
        "ikinci çare (disable --now) adıyla basılmıyor"


def test_anomali_YOKKEN_kapi_gecirir(tmp_path):
    """BUGÜNKÜ CANLI DÜNYA (ölçüldü 2026-09-03 09:40Z): meridian enabled/active ·
    barsarchive enabled/active · learn disabled/inactive → DUR tetiklenmez. Kapı her dağıtımı
    durduran bir duvar olsaydı ilk gün devre dışı bırakılırdı."""
    enabled = {"meridian": "enabled", "meridian-barsarchive": "enabled",
               "meridian-learn": "disabled"}
    active = {"meridian": "active", "meridian-barsarchive": "active",
              "meridian-learn": "inactive"}
    p = _kapiyi_kos(tmp_path, enabled, active)
    assert p.returncode == 0, (
        f"temiz dünyada kapı {p.returncode} ile durdu (stdout: {p.stdout!r} "
        f"stderr: {p.stderr!r})")


def test_anomali_kapisi_STOPTAN_ve_RSYNCTEN_ONCE():
    """YER ÖLÇÜLÜR, VARSAYILMAZ: kapı rsync'ten sonra düşseydi yeni kod diske inmiş, süreç eski
    kodda kalmış olurdu ([5b]'nin kapattığı "iki gerçek" hâli); stop'tan sonra düşseydi worker
    zaten durdurulmuş olurdu. Kapı üçünden de ÖNCE."""
    i_kapi = METIN.index(_F10_BAS)
    i_rsync = METIN.index('echo "=== [2/5] rsync')
    i_stop = METIN.index("systemctl stop $_DURDUR")
    assert i_kapi < i_rsync < i_stop, (
        f"anomali kapısının yeri yanlış (kapı={i_kapi} rsync={i_rsync} stop={i_stop})")


def test_anomali_kapisi_HICBIR_SEY_DEGISTIRMEZ_ve_OVERRIDE_TASIMAZ():
    """Kapı yalnız OKUR: içinde `stop`/`start`/`rsync` yok. Ve override bayrağı YOK — anomali,
    bilinçli bir hâle (start ya da disable --now) çevrilmeden geçilemez; bayrak eklenseydi
    "her seferinde geç" alışkanlığı kapıyı ilk haftada sessizleştirirdi."""
    # ŞERHLER SOYULUR (v286/v381 `soy` dersi): Meridian'ın belge geleneği kararın gerekçesini
    # yazarken YASAKLANAN ŞEYİ ALINTILAR — soymadan ölçen çivi kendi şerhini ihlal sanır.
    blok = "\n".join(s for s in _kapi_blogu().splitlines() if not s.lstrip().startswith("#"))
    assert "rsync" not in blok, "anomali kapısı rsync taşıyor — kapı yalnız OKUR"
    for satir in blok.splitlines():
        if re.search(r"systemctl (stop|start|disable|enable|restart)\b", satir):
            assert satir.lstrip().startswith("echo "), (
                f"anomali kapısında ÇALIŞAN bir durum değişikliği var (yalnız `echo` ile ÇARE "
                f"METNİ basılabilir): {satir.strip()}")
    assert "exit 3" in blok, "kapı DURMUYOR — `exit 3` yok"
    assert not re.search(r"--(zorla|force|gec|gecir|atla)\b", blok), \
        "anomali kapısında override bayrağı var — R-0 bunu yasaklıyor"


def test_stop_bos_listede_gonderilmez():
    """Üçü de inactive ise stop satırı HİÇ gönderilmez — `systemctl stop` argümansız çağrılırsa
    uzak kabuk hata döner ve `set -e` pencereyi ortasından keser."""
    assert re.search(r'if\s+\[\[\s+-n\s+"\$\{_DURDUR//\s*/}"\s+\]\]', _BLOK), \
        "boş _DURDUR koruması yok — argümansız `systemctl stop` pencereyi keser"


def test_turetim_disabled_son_elemanla_SIFIR_cikar(tmp_path):
    """VAKA 2026-09-02 (sabah penceresi, ilk gerçek koşum): `[ … ] && printf` kalıbı döngünün
    SON elemanı disabled olunca uzak kabuğu 1 ile bitirdi; ssh 1 döndürdü, yerel `set -e`
    `_BASLAT=$( … )` atamasında dagit'i [4] başlığından hemen sonra SESSİZCE öldürdü — rsync
    inmiş, worker restart edilmemiş, beyan yazılmamıştı (iki gerçek: diskte yeni, süreçte eski
    kod). Betiğin kendi 132. satır doktrini tam bu sınıfı yasaklar; v367'nin metin çivileri
    türetmeyi KOŞMADIĞI için tuzak yeşilken yaşadı. Bu çivi türetme snippet'ini dagit.sh'nin
    GERÇEK metninden söküp sahte `systemctl` ile koşar: disabled son elemanla çıkış kodu 0
    ve liste yalnız enabled birimleri taşımalı."""
    snippet = _snippet("_BASLAT")   # sökücü TEK yerde (K-2, düzeltme turu 1, 2026-09-03)

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


def test_recete_kalemi_readme_de_yasiyor():
    """TSK-092 (b): kural İKİ yerde duruyor — dagit.sh [4] yorumu (icra) ve operatör reçetesi
    (`deploy/README-oracle.md`, insan yolu). Tek-kaynak yasası kopyayı ancak AYRIŞMA ÇİVİSİYLE
    hoş görür: reçete kalemi silinir/kayarsa operatör pencerenin sözleşmesini betikten okumak
    zorunda kalır ve TSK-092 vakası (elle durdurulan birim dağıtımla geri açıldı) sessizce
    tekrarlanır. Ölçülen: iki türetim adının ve "başlatma" hükmünün reçetede geçmesi."""
    recete = (DAGIT.parent / "deploy" / "README-oracle.md").read_text(encoding="utf-8")
    for parca in ("is-enabled", "is-active", "BAŞLATMA", "TSK-092"):
        assert parca in recete, f"reçete kaleminde `{parca}` yok — kural betikte kaldı"
