"""test_dagit_f9_beyan_v266.py — WP6 üç kalem: [F9] içerik kapısı + P0-b dağıtım-beyanı +
H3 tur-2 drop-in hazırlığı (2026-08-23).

NEDEN BU ÇİVİLER — üç kalem, tek sınıf ailesi: "kurulu ≠ çalışır / dağıtıldı ≠ beyan edildi":

  ① [F9] İÇERİK KAPISI (denetim §F9, 2026-08-13): dört canlı artefakt (sprint@ birimi · polkit
     kuralı · SOUL.md · tick-watchdog service+timer) dagit'in rsync kapsamı DIŞINDA elle kurulur
     ve dagit'te bu dosyalara SIFIR atıf vardı — repo ilerler, canlı yerinde sayar, kimse bağırmaz
     (OB-2'yi doğuran sınıf). Kapı artık beş dosyanın tam içeriğini kıyaslar; RAPORLAR, engellemez.

  ② P0-b DAĞITIM-BEYANI (ENVANTER §4.2): ortamlar-arası #2 ("iki ağaç hangi tepede?") dedektörün
     yapısal kör noktası — kapısı, dagit'in başarılı dağıtım sonunda canlıya yazdığı
     `state/dagitim.json` beyanıdır (deployed_sha [0a]'da dondurulur — 660dc10 dersi).

  ③ H3 TUR-2 HAZIRLIK: tick-watchdog + fail-notify filoda sertleştirmesiz kalan iki birimdi;
     fazlı drop-in dosyaları (faz1 = temel küme, faz2 = seccomp + yetenek sıfırlama) depoda hazır,
     kurulum bakım penceresine (h3_tur2_sertlestir.sh) bırakıldı. Mevcut birim dosyaları
     DEĞİŞTİRİLMEDİ — bu da bir çividir (sertleştirmenin birim içine sessizce sızması ayrı,
     bilinçli bir turdur; fail-notify'da ayrıca ölçülen bir ön-şartın konusudur).

YÖNTEM (v172'nin dagit bölümüyle aynı gerekçe): adımlar A1'e SSH ister, testte KOŞTURULAMAZ.
Ölçülen katman YAPI'dır — kapının YERİ (kuru koşumda da görünür; --uygula kapısından ÖNCE),
sözdizimi (`bash -n`), engel-yasağı (F9 bloğunda `exit` yok) ve alan/dosya varlığı. Metin çivisi
kırılgandır ama burada doğru araçtır: korunan şey davranıştan önce SÖZLEŞMEDİR (hangi dosyalar,
hangi alanlar, hangi sıra) ve sözleşmenin her maddesi bir vaka/denetim kaydına çapalıdır.
"""
from __future__ import annotations

import json
import pathlib
import re
import subprocess

REPO = pathlib.Path(__file__).resolve().parent.parent
DAGIT = REPO / "dagit.sh"
ORACLE = REPO / "deploy" / "oracle-a1"


def _satirlar() -> list[str]:
    return DAGIT.read_text().splitlines()


def _satir_no(iz: str) -> int:
    for i, s in enumerate(_satirlar()):
        if iz in s:
            return i
    raise AssertionError(f"dagit.sh'ta bulunamadı: {iz!r} — çivi bayatlamış")


# =================================================================================================
# ① [F9] içerik kapısı
# =================================================================================================
def test_dagit_sozdizimi_TEMIZ():
    """`bash -n`: kapı eklendi diye betik açılışta patlamamalı — dağıtım betiğinin sözdizimi
    hatası, bakım penceresinin ortasında öğrenilecek en pahalı şeydir (v172 çivisinin ikizi;
    o çivi de duruyor, bu dosya tek başına koşulduğunda da ölçüm kaybolmasın diye burada da var)."""
    r = subprocess.run(["bash", "-n", str(DAGIT)], capture_output=True, text=True)
    assert r.returncode == 0, f"dagit.sh sözdizimi bozuk:\n{r.stderr}"


def test_f9_KURUCU_ARTEFAKTLAR_hala_listede():
    """Kapının KURULUŞUNDAKİ artefaktlar listeden hiç düşmemeli — bu bir TABAN, tavan değil.

    Aşağıdaki beş dosya 2026-08-02 denetiminde sayılanlardır; biri listeden düşerse kapı o
    artefakta karşı sessizleşir ve tam olarak kapatılan körlük geri gelir. Liste o günden beri
    BÜYÜDÜ (bugün 11 çift) ve büyümesi burada sayılmaz: güncel kapsamayı `F9_LISTE`den TÜRETEN
    ayrı çivi ölçer (test_f9_LISTESININ_TAMAMI_deploy_sh_BASLIGINDA_ADLANDIRILIR). Eski ad ve
    docstring "DÖRT ARTEFAKT / BEŞ dosya" diyordu — düzyazıya gömülü bir sayım, hem de sayım
    gömmeyi yasaklayan çivinin yanıbaşında (denetim 2026-08-29).
    """
    metin = DAGIT.read_text()
    for repo_yol, canli_yol in [
        ("deploy/oracle-a1/meridian-sprint@.service", "/etc/systemd/system/meridian-sprint@.service"),
        ("deploy/oracle-a1/50-meridian-sprint.rules", "/etc/polkit-1/rules.d/50-meridian-sprint.rules"),
        ("deploy/hermes/SOUL.md", "/home/ubuntu/.hermes/SOUL.md"),
        ("deploy/oracle-a1/meridian-tick-watchdog.service",
         "/etc/systemd/system/meridian-tick-watchdog.service"),
        ("deploy/oracle-a1/meridian-tick-watchdog.timer",
         "/etc/systemd/system/meridian-tick-watchdog.timer"),
    ]:
        assert f"{repo_yol}|{canli_yol}" in metin, f"[F9] listesinde eksik/yanlış çift: {repo_yol}"
        # Repo tarafı GERÇEKTEN var — listeye uydurma bir yol girmesin (kapı kendi "REPODA YOK"
        # dalına düşer ve her dağıtımda ölçülemedi gürültüsü üretirdi).
        assert (REPO / repo_yol).is_file(), f"[F9] repo tarafı yok: {repo_yol}"



def test_f9_LISTESININ_TAMAMI_deploy_sh_BASLIGINDA_ADLANDIRILIR():
    """`F9_LISTE`deki HER artefakt `deploy.sh` başlığında da ADIYLA geçer.

    NEDEN BU ÇİVİ VAR (ölçülmüş sürüklenme, 2026-08-29). `deploy.sh` başlığı "DAGİT KAPSAMI DIŞI
    DÖRT CANLI ARTEFAKT" diyordu ve dört tanesini sayıyordu; `F9_LISTE` bu arada 11 çifte
    çıkmıştı. İki yerde tutulan bir liste, birini bayatlatmaktır — ve bayat olan taraf tam da
    operatörün ELLE KURULUM adımlarını okuduğu yerdi: listede olup başlıkta olmayan bir artefakt
    (litestream.yml, aylık bucket kopyası) için dagit sürüklenme RAPORLAR ama kurulum yönergesi
    HİÇBİR YERDE yazmaz. Kapının gördüğü ile operatörün okuduğu ayrışır.

    Çivi SAYI DEĞİL KAPSAMA ölçer: düzyazıya gömülü bir sayım (kaç tane) yine bayatlar, ama
    "listedeki her ad başlıkta geçiyor mu" sorusu `F9_LISTE`den TÜRETİLİR ve bayatlayamaz.
    Yön TEK: başlıkta fazladan bir ad olması serbest (bağlam olabilir); listede olup başlıkta
    OLMAYAN yasaktır.

    BASENAME ÇAKIŞMASI AYRI ÖLÇÜLÜR (denetim 2026-08-30 — çivi kendi ölçtüğünü sanmıyordu).
    Faz 2'yle birlikte listede AYNI BASENAME'İ taşıyan çiftler doğdu: `config.yaml` iki kez
    (ana profil + `@sef`), `SOUL.md` iki kez. Yalnız basename eşleyen bir çivi, `@sef`in
    satırları başlıktan SİLİNSE bile ANA profilin satırları yüzünden YEŞİL kalırdı — yani
    listede olup başlıkta olmayan artefakt gizlenirdi. Çakışan basename'ler için ölçü
    BASENAME DEĞİL TAM REPO YOLUDUR; çakışmayanlar için basename yeter (başlık onları kısa
    adla anıyor ve bu okunurluk tercihi meşru).
    """
    dagit = DAGIT.read_text()
    govde = dagit.split('F9_LISTE="', 1)[1].split('"', 1)[0]
    yollar = [ln.split("|")[0].strip() for ln in govde.strip().splitlines() if "|" in ln]
    assert yollar, "F9_LISTE ayrıştırılamadı — çivi kendi hedefini kaybetmiş"

    baslik = (ORACLE / "deploy.sh").read_text().split("set -euo pipefail", 1)[0]
    import collections
    sayim = collections.Counter(pathlib.Path(y).name for y in yollar)
    # Çakışan basename → TAM YOL aranır; tekil basename → basename yeter.
    def _aranan(y: str) -> str:
        return y if sayim[pathlib.Path(y).name] > 1 else pathlib.Path(y).name

    eksik = [f"{y} (aranan: {_aranan(y)})" for y in yollar if _aranan(y) not in baslik]
    assert not eksik, (
        "F9_LISTE'de olup deploy.sh BAŞLIĞINDA adı geçmeyen artefakt(lar): "
        + ", ".join(eksik)
        + " — dagit sürüklenmeyi raporlar ama operatörün okuduğu kurulum başlığı onlardan "
        "HİÇ söz etmiyor (çakışan basename'ler TAM YOLLA aranır: `config.yaml` ve `SOUL.md` "
        "listede iki kez geçiyor ve basename eşlemesi birinin silinmesini gizlerdi)"
    )

def test_f9_YERI_kuru_kosumda_da_gorunur():
    """YER YASASI: [F9] `--uygula` kapısından ÖNCE koşar — sürüklenme raporu kuru koşumda da
    görünmeli (operatör dağıtmadan önce görsün), ve [1c]'den SONRA (birim-yönerge kapısının
    reçetesine atıf yapar, sıra ters dönerse anlatı kopar)."""
    bir_c = _satir_no("[1c/5] sistem birimi ayrıklığı")
    f9 = _satir_no("[F9] dagit-kapsamı-dışı canlı artefaktlar (içerik kapısı)")
    kapi = _satir_no('!= "--uygula" ]]')
    assert bir_c < f9 < kapi, f"[F9] yanlış yerde (1c={bir_c}, F9={f9}, uygula-kapısı={kapi})"


def test_f9_RAPORLAR_engellemez():
    """[F9] bloğunda `exit` YOK: ayrıklık dağıtımı DURDURMAZ (artefaktlar dagit'in kopyalama
    kapsamında değil; engel, elle-kurulum akışını dagit'e kilitlerdi). Blok sınırı: kapının
    kendi `===` satırından `--uygula` kapısına kadar."""
    satirlar = _satirlar()
    bas = _satir_no("[F9] dagit-kapsamı-dışı canlı artefaktlar (içerik kapısı)")
    son = _satir_no('!= "--uygula" ]]')
    blok = satirlar[bas:son]
    ihlal = [s for s in blok if re.search(r"\bexit\s+\d", s) and not s.lstrip().startswith("#")]
    assert not ihlal, f"[F9] bloğunda engel var — kapı 'raporlar, engellemez' sözünü bozdu: {ihlal}"


def test_f9_OLCULEMEDI_dali_var():
    """UYDURMA YASAĞI: canlıdan okunamayan dosya ne 'aynı'dır ne 'ayrık' — kapının açık bir
    'ölçülemedi' dalı var ve nedeni ayrıştırıyor (dosya yok ↔ okunamadı: farklı iş kalemleri)."""
    metin = DAGIT.read_text()
    assert "F9_OLCULEMEDI" in metin
    assert "canlıda DOSYA YOK" in metin, "yok-dalı kayıp — 'hiç kurulmamış' hâli sessizleşir"
    assert "VAR ama OKUNAMADI" in metin, "izin-dalı kayıp — sudo/izin arızası 'yok' sanılır"


def test_f9_OZETI_dagitim_sonunda_tekrarlanir():
    """Kapı kuru-koşum tarafında konuşur; ayrıklık dağıtım ÖZETİNDE bir kez daha yazılır —
    raporlanan ama görülmeyen sürüklenme, hiç raporlanmamış gibidir. Özet 'DAĞITIM TAMAM'dan önce."""
    ozet = _satir_no("[F9] dagit-kapsamı-dışı artefakt özeti")
    tamam = _satir_no('echo "=== DAĞITIM TAMAM ===')   # yorum satırındaki geçiş değil, basılan satır
    kapi = _satir_no('!= "--uygula" ]]')
    assert kapi < ozet < tamam, "özet yanlış yerde — --uygula tarafında ve TAMAM'dan önce olmalı"


# =================================================================================================
# ② P0-b dağıtım-beyanı
# =================================================================================================
def test_beyan_DORT_ALAN_ve_hedef_yol():
    """Beyanın sözleşmesi (ENVANTER §4.2): dört alan + canlı hedef `state/dagitim.json`.
    Alan adları ortamlar-arası kıyasın okuyacağı API'dir — sessizce değişemez."""
    metin = DAGIT.read_text()
    assert "/opt/meridian/state/dagitim.json" in metin, "beyanın canlı hedefi kayıp"
    for alan in ("deployed_sha", "dagitildi_utc", "dagitan_host", "kirli_gec_kullanildi"):
        assert alan in metin, f"beyan alanı kayıp: {alan}"


def test_beyan_JSON_bicimi_GECERLI():
    """Beyan printf şablonu GERÇEKTEN koşturulur (kopyası değil kendisi — v172 dersi) ve çıktı
    json.loads'tan geçer: yarım/bozuk JSON, ortamlar-arası kapıyı yanlış hükme götürürdü."""
    satir = next(s for s in _satirlar() if s.strip().startswith("printf '{"))
    sablon = satir.split("printf ")[1].split("' ")[0].strip("'")
    if sablon.endswith("\\n"):
        sablon = sablon[:-2]                                     # printf kaçışı JSON'un parçası değil
    ornek = sablon.replace("%s", "X", 3).replace("%s", "false")   # son %s bool yuvası
    veri = json.loads(ornek)
    assert set(veri) == {"deployed_sha", "dagitildi_utc", "dagitan_host", "kirli_gec_kullanildi"}
    assert veri["kirli_gec_kullanildi"] is False, "bool yuvası tırnaklı — beyan tipi bozuk"


def test_beyan_YERI_basarili_dagitimin_sonunda():
    """Beyan [5] doğrulamadan SONRA yazılır ('başarılı dağıtım' beyanı — [4]/[5]'ten önce yazılsa
    düşen bir dağıtım da beyan bırakır, beyan yalan söylerdi) ve sha [0a]'da DONDURULUR
    (660dc10 dersi: paralel oturum main'i dağıtım sırasında taşıyabilir)."""
    dondur = _satir_no('DAGIT_SHA="$(git rev-parse HEAD)"')
    kapi_0a = _satir_no("[0b/5] uv audit")
    dogrulama = _satir_no("[5/5] doğrulama")
    beyan = _satir_no("[B] dağıtım-beyanı (state/dagitim.json")
    assert dondur < kapi_0a, "DAGIT_SHA [0a]'da dondurulmuyor — beyan betik-sonu tepesini söyler"
    assert dogrulama < beyan, "beyan [5]'ten önce — başarısız dağıtım da beyan bırakırdı"


def test_beyan_ATOMIK_ve_dogrulamali():
    """tmp + mv (atomik) ve yazım sonrası bayt-özdeş doğrulama ([1b] kopya disiplini). Doğrulama
    düşerse ENGEL DEĞİL uyarı: dağıtım o noktada zaten tamam, beyansızlık dağıtımı geri almaz."""
    metin = DAGIT.read_text()
    assert ".dagitim.json.tmp" in metin and "mv /opt/meridian/state/.dagitim.json.tmp" in metin
    assert "BEYAN YAZILAMADI" in metin, "yazım arızası sessiz — uyarı dalı kayıp"
    bas = _satir_no("[B] dağıtım-beyanı (state/dagitim.json")
    blok = _satirlar()[bas:]
    ihlal = [s for s in blok if re.search(r"\bexit\s+1", s) and not s.lstrip().startswith("#")]
    assert not ihlal, f"beyan bloğu dağıtımı düşürüyor — beyan kayıt içindir, kapı değil: {ihlal}"


def test_beyan_yerel_STATE_dosyasi_uretmez():
    """Beyan repoya/yerele state dosyası olarak YAZILMAZ (konsola basılır + canlıya gider):
    yerel bir dagitim.json, [1b]'nin kapattığı repo↔canlı ayrışmasını başka bir adla geri açardı."""
    assert not (REPO / "state" / "dagitim.json").exists(), \
        "repo'da state/dagitim.json var — beyan yerel dosya olarak birikmemeli"


# =================================================================================================
# ③ H3 tur-2 drop-in hazırlığı
# =================================================================================================
_BIRIMLER = ("meridian-tick-watchdog", "meridian-fail-notify")


def test_dropin_FAZ1_dosyalari_temel_kumeyi_tasiyor():
    """Faz 1 = ROADMAP sırasının 'önce' yarısı: NoNewPrivileges/ProtectSystem=strict/PrivateTmp
    (+ProtectHome). Seccomp faz 1'de OLMAMALI — 'EN SON ve dikkatli' sırası dosya düzeyinde çivili."""
    for birim in _BIRIMLER:
        p = ORACLE / f"{birim}.service.d" / "10-sertlestirme-faz1.conf"
        assert p.is_file(), f"faz-1 drop-in yok: {p}"
        m = p.read_text()
        for y in ("NoNewPrivileges=true", "ProtectSystem=strict", "PrivateTmp=true"):
            assert re.search(rf"^{re.escape(y)}$", m, re.M), f"{p.name} ({birim}): {y} kayıp"
        assert re.search(r"^ProtectHome=(true|read-only)$", m, re.M), \
            f"{p.name} ({birim}): ProtectHome kayıp"
        assert "SystemCallFilter" not in [s.split("=")[0] for s in m.splitlines()
                                          if s and not s.startswith("#")], \
            f"{birim} faz-1'e seccomp sızmış — 'seccomp EN SON' sırası bozuldu"


def test_dropin_FAZ2_seccomp_ve_yetenek_sifirlama():
    """Faz 2 = seccomp satırı + boş CapabilityBoundingSet — brief'in çivisi: drop-in dosyaları
    mevcut VE seccomp satırı taşıyor."""
    for birim in _BIRIMLER:
        p = ORACLE / f"{birim}.service.d" / "20-sertlestirme-faz2.conf"
        assert p.is_file(), f"faz-2 drop-in yok: {p}"
        m = p.read_text()
        assert re.search(r"^SystemCallFilter=@system-service$", m, re.M), \
            f"{p.name} ({birim}): seccomp satırı kayıp"
        # 2026-08-23 CANLI ÖLÇÜMLE DÜZELTİLDİ (tetik-testi bulgusu): "boş küme" beklentisi
        # root-koşan tick-watchdog'da OKUMAYI kırdı (ubuntu-0600 state dosyasına EACCES) —
        # çivi artık birime göre: root birimi YALNIZ salt-okuma DAC yeteneği taşır (yazma
        # yetenekleri geri gelirse kırmızı), User=ubuntu birimi boş küme taşır.
        beklenen = (r"^CapabilityBoundingSet=CAP_DAC_READ_SEARCH$"
                    if birim == "meridian-tick-watchdog" else r"^CapabilityBoundingSet=$")
        assert re.search(beklenen, m, re.M), \
            f"{p.name} ({birim}): CapabilityBoundingSet satırı beklenenden farklı ({beklenen})"


def test_MEVCUT_birim_dosyalari_DEGISMEDI():
    """'Yalnız drop-in' sözleşmesi: iki birimin dosyasında sertleştirme YÖNERGESİ hâlâ yok
    (fail-notify'ın 'bilinçli sertleştirilmedi' bloğu ve tur ayrıklığı — sertleştirme birime
    taşınırsa bu çivi bilerek güncellenir, sessizce değil)."""
    for birim in _BIRIMLER:
        m = (ORACLE / f"{birim}.service").read_text()
        yonergeler = [s for s in m.splitlines() if s and not s.lstrip().startswith("#")]
        for y in ("SystemCallFilter", "CapabilityBoundingSet", "NoNewPrivileges"):
            assert not any(s.startswith(f"{y}=") for s in yonergeler), \
                f"{birim}.service içine {y} yazılmış — sertleştirme drop-in'de kalmalıydı"


def test_h3_uygulama_betigi_VAR_ve_runbook_bolumu_uretildi():
    """Uygulama adımları RUNBOOK'a ELLE yazılamaz (üretilmiş dosya — kaynağı betik başlıklarıdır);
    kanal: h3_tur2_sertlestir.sh başlığı → runbook_uret.py. İki uç da ölçülür: kaynak betik
    (sözdizimi + başlık cümlesi) ve üretilmiş RUNBOOK'taki bölüm."""
    betik = ORACLE / "h3_tur2_sertlestir.sh"
    assert betik.is_file(), "h3_tur2_sertlestir.sh yok"
    r = subprocess.run(["bash", "-n", str(betik)], capture_output=True, text=True)
    assert r.returncode == 0, f"h3_tur2_sertlestir.sh sözdizimi bozuk:\n{r.stderr}"
    assert "H3 tur-2 uygulama adımları (bakım penceresi)" in betik.read_text()
    runbook = (REPO / "docs" / "RUNBOOK.md").read_text()
    assert "H3 tur-2 uygulama adımları (bakım penceresi" in runbook, \
        "RUNBOOK bölümü yok — `python ops/runbook_uret.py` koşulmamış"
    # ÇAPA CÜMLESİ SAYI TAŞIMAZ (2026-08-29): eskiden "Bu dört dosya dagit kapsamı dışıdır"
    # aranıyordu; liste 11'e çıkınca başlıktaki o sayı yalan oldu ve düzeltmesi bu çiviyi de
    # kırdı. Yeni çapa başlığın DEĞİŞMEZ kısmıdır — kapsamı `F9_LISTE`den türeten ayrı çivi
    # ölçer (test_f9_LISTESININ_TAMAMI_deploy_sh_BASLIGINDA_ADLANDIRILIR).
    assert "DAGİT KAPSAMI DIŞI CANLI ARTEFAKTLAR (F9)" in runbook, \
        "F9 notu RUNBOOK'ta yok — deploy.sh başlığı + yeniden üretim zinciri kopuk"


# =================================================================================================
# ④ [5b] KOD-TAZELİK DEĞİŞMEZİ — "active" ≠ "yeni kodu koşuyor"  (2026-08-24)
# =================================================================================================
# ÖLÇÜLEN VAKA. 2026-08-24 12:30Z dağıtımı `meridian-learn`i HİÇ yeniden başlatmadı: betiğin
# bakım penceresi yalnız `meridian meridian-barsarchive` durduruyordu ve dosyada `learn` kelimesi
# HİÇ geçmiyordu (birim 2026-08-17'de doğdu, betik güncellenmedi — bilinçli dışlama DEĞİL, unutma).
# Sonuç: ısınma telemetrisi diske indi ama süreç 00:34:40'tan beri ESKİ bytecode'u koşuyordu ve
# doğrulama adımı "iki birim de active" dedi — DOĞRU ama ANLAMSIZ bir cümle. Ölçülen fark:
# süreç 00:34:40, en yeni kaynak 11:53:16 → 11 sa 19 dk.
#
# Bu çivi İKİ şeyi birden korur ve ikisi de ayrı sınıftır:
#   (a) LİSTE — learn bakım penceresinde. Bugünkü örneği kapatır.
#   (b) DEĞİŞMEZ — süreç başlangıcı ≥ en yeni kaynak mtime'ı, ve kapsam ExecStart'tan TÜRETİLİR.
#       (a) tek başına yeterli olsaydı, yarın eklenen bir birim aynı sessizlikle unutulurdu;
#       türetilmiş kapsam unutma sınıfını kapatır.
def test_bakim_penceresi_ogrenme_birimini_KAPSAR():
    """(a) `meridian-learn` durdur VE başlat satırlarında olmalı.

    Öğrenme birimini dağıtımdan uzak tutmayı gerektiren bir şey YOK — ölçüldü: sonda önbelleği
    diske yazılıyor (`reflect.PROBE_DISK_FILE`), döngü 300 sn'de bir uyanıyor ve birim
    `Restart=always`. Restart'ın bedeli en fazla o anki turun taze hesabıdır."""
    metin = DAGIT.read_text()
    for eylem in ("systemctl stop", "systemctl start"):
        satir = next((s for s in _satirlar() if eylem in s and "meridian" in s), None)
        assert satir, f"{eylem} satırı bulunamadı — çivi bayatlamış"
        assert "meridian-learn" in satir, (
            f"`{eylem}` satırı `meridian-learn` taşımıyor — öğrenme tarafına yapılan her dağıtım "
            f"biri ELLE restart edene kadar sessizce etkisiz kalır (2026-08-24 vakası). Satır: {satir.strip()}")
    assert metin.count("meridian-learn") >= 2


def test_kod_tazelik_kapisi_VAR_ve_BEYANDAN_ONCE():
    """(b) [5b] değişmezi ve YERİ.

    Kapı [B] dağıtım-beyanından ÖNCE düşmeli: beyan `state/dagitim.json`a "bu sha canlıda" yazar
    ve süreçlerden biri eski kodu koşuyorsa bu cümle YANLIŞTIR. Önce düşerse dosya eski sha'da
    kalır — koşan sistemin GERÇEK hâli odur (operatör kararı, 2026-08-24)."""
    metin = DAGIT.read_text()
    assert "[5b/" in metin, "kod-tazelik kapısı [5b] yok"
    assert "ExecMainStartTimestamp" in metin, (
        "kapı süreç başlangıcını okumuyor — 'active' cümlesi bu kusuru göremez")
    # KAPSAM TÜRETİLİR, YAZILMAZ: birim adları elle sayılsaydı yarın eklenen birim unutulurdu.
    assert "ExecStart" in metin, "kapsam ExecStart'tan türetilmiyor — unutma sınıfı açık kalır"
    # ÇAPA `echo` SATIRINA BAĞLI: düz `"[B] dağıtım-beyanı"` dizgisi dosyanın BAŞINDAKİ
    # içindekiler yorumunda da geçiyor (satır ~15) ve çivi orayı bulup sahte kırmızı verdi
    # (2026-08-24, ilk yazımda). Aranan şey adımın KENDİSİ, ondan söz eden satır değil.
    i_kapi, i_beyan = _satir_no("[5b/"), _satir_no('echo "=== [B] dağıtım-beyanı')
    assert i_kapi < i_beyan, (
        f"[5b] kapısı beyandan SONRA (satır {i_kapi} > {i_beyan}) — yarı-etkili bir dağıtım "
        f"'tamam' diye damgalanır")
    # Kapı ENGELLER (F9'un tersine): yarı-etkili dağıtım sessizce geçemez.
    blok = "\n".join(_satirlar()[i_kapi:i_beyan])
    assert "exit 1" in blok, "[5b] ihlalde exit 1 vermiyor — kapı değil rapor olur"


# =================================================================================================
# SOUL.md — AJANIN KALICI BRİFİNGİNDE MAKİNEYE ÖZGÜ YOL OLAMAZ (2026-08-26 vakası)
# =================================================================================================
def _enjekte_edilen_soullar() -> list[pathlib.Path]:
    """Ajan sistem istemine giren TÜM `SOUL.md`ler — ana profilinki VE her bot profilininki.

    KÜME TÜRETİLİR, YAZILMAZ (2026-08-29, Faz 2). Çivi bir zamanlar tek bir literal yol
    (`deploy/hermes/SOUL.md`) taşıyordu; o gün doğru, bugün EKSİKTİ: `deploy/hermes/profiles/
    <bot>/SOUL.md` dosyaları da AYNI şekilde enjekte edilir (`agent/system_prompt.py`: SOUL
    yüklenirse `stable_parts`a O konur) ve AYNI şekilde canlıya dağıtılır. İkinci bir literal
    eklemek sınıfı kapatmaz — üçüncü bot geldiğinde çivi yine sessizce kör kalırdı.
    """
    return sorted((REPO / "deploy" / "hermes").rglob("SOUL.md"))


def test_SOUL_makineye_ozgu_yol_TASIMIYOR():
    """Ajanın HER çağrısına enjekte edilen kalıcı brifinglerinin HİÇBİRİ makineye özgü yol
    taşımaz. Bir ev dizini yolu oraya yazılırsa, dosya BAŞKA makineye dağıtıldığında yanlış bir
    OLGU taşır.

    ÖLÇÜLMÜŞ VAKA: brifing ajana deponun `~/Documents/Claude/AI-Trading`ta olduğunu söylüyordu.
    A1'de o yol YOK (`ls: cannot access`), ve bu depo bile artık orada değil — yol iki
    makinede de yanlıştı. `dagit` F9 kapısı "canlı ile repo BİREBİR" diyordu ve HAKLIYDI:
    aynı yanlış her iki tarafta duruyordu. Kimlik kapısı doğruluk kapısı DEĞİLDİR.

    ÇARE, kuralın kendisi: brifing yol BEYAN ETMEZ. Ajanın deponun kökünü öğrendiği yer
    `meridian` MCP sunucusudur (`MERIDIAN_ROOT`) — tek kaynak, makineden bağımsız.
    """
    import re
    soullar = _enjekte_edilen_soullar()
    assert (REPO / "deploy/hermes/SOUL.md") in soullar, (
        "ana brifing türetilen kümede YOK — glob bozulmuş olabilir ve bozuk bir glob bu çiviyi "
        "SESSİZCE boşa çıkarır (sıfır dosya, sıfır ihlal)")
    for yol in soullar:
        soul = yol.read_text(encoding="utf-8")
        # `~/...` ve `/home/<kullanıcı>/...` ve `/Users/<kullanıcı>/...` — üç ev-dizini biçimi
        yasak = re.findall(
            r"(?:~|/home/[A-Za-z0-9._-]+|/Users/[A-Za-z0-9._-]+)/[A-Za-z0-9._/-]+", soul)
        assert not yasak, (
            f"{yol.relative_to(REPO)}: kalıcı brifingte makineye özgü yol(lar): {yasak}\n"
            "Bu dosya birden çok makineye dağıtılır; ev-dizini yolu bir tarafta MUTLAKA yanlış "
            "olur ve ajan her çağrıda o yanlışı okur. Depo kökünü MCP sunucusu (MERIDIAN_ROOT) "
            "verir.")
