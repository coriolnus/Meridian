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

import pathlib
import re
import subprocess

# TEK KAYNAK (düzeltme turu 1, inceleme K-2, 2026-09-03): `_X="$("${SSH[@]}" '…')"` yapısal
# sözleşmesinin sökücüsü v367'de yaşıyordu.
# TAŞIMA (TSK-176 Faz A1 Task 3, 2026-09-08): o kabuk sözleşmesi SİLİNDİ (dagit.sh sarmalayıcı) —
# [4] penceresinin aday kümesi artık `dagit_vars.yml::birim_adaylari`, türetimi de playbook'un
# `when` ifadeleri. v367 kendi çivilerini oraya taşıdı; sökücü ithali de onunla düştü.
#
# TEK KAYNAK (düzeltme turu 2, 2026-09-08 · Task 3'te yenilendi): [5b] çağrısının BİÇİMİ ve
# `dagit.yml` okuyucuları v452'de yaşıyor; buraya KOPYALANMAZ, ithal edilir. Düz `"<yol>" in kod`
# iddiası ısırmıyordu ve on ayrı YAML sökücüsü, ayrışabilen on kopya olurdu.
from tests.test_ansible_dagit_v452 import (
    KOD_TAZELIK_CAGRI,
    beyan_indeksi,
    birim_adaylari as _vars_birim_adaylari,
    dogrulama_uclari as _vars_dogrulama_uclari,
    f9_ciftleri,
    gorev_metni,
    gorevler,
    gorev_etiketleri,
    kapi_indeksi,
    script_cmdleri,
    son_kapi_indeksi,
)

REPO = pathlib.Path(__file__).resolve().parent.parent
DAGIT = REPO / "dagit.sh"
ORACLE = REPO / "deploy" / "oracle-a1"

# TAŞIMA KAYDI 1 (TSK-176 Faz A1 Task 1, 2026-09-08). [5a] ve [5b] kapılarının GÖVDELERİ
# dagit.sh'ın içinde gömülü uzak kabuk/python bloklarıydı ve bu dosya iddialarını o metinde
# arıyordu. Gövdeler DOSYAYA çıkarıldı (gömülü çok-satır gövde bir Ansible görevinde YASAK —
# A0 kuralı + 2026-07-30 IndentationError vakası).
#
# TAŞIMA KAYDI 2 (Task 3, 2026-09-08) — BU DOSYANIN TAMAMINI İLGİLENDİRİR. `dagit.sh` ince bir
# SARMALAYICIYA indi: on yedi kapının hepsi `deploy/ansible/dagit.yml`e, listeler
# `deploy/ansible/vars/dagit_vars.yml`e taşındı. Aşağıdaki çivilerin HİÇBİRİ silinmedi ve
# hiçbirinin İDDİASI değişmedi — değişen tek şey, iddianın hangi kaynakta ölçüldüğüdür:
#   * `F9_LISTE` dizgesi        → `dagit_vars.yml::f9_ciftleri` (sökücü v452'de, ithal edilir)
#   * kapı YERİ (`_satir_no`)   → `dagit.yml` görev SIRASI (`kapi_indeksi`)
#   * `exit 1` / `exit` yokluğu → görevin `assert`/`fail` taşıyıp taşımaması
#   * `printf` beyan şablonu    → `[B]` `set_fact` + `to_json` görevleri
# Kapının UYGULAMASI hâlâ betikte, ÇAĞRISI playbook'ta: iki taraf da çivili, aksi hâlde biri
# sessizce ötekinden koparabilirdi (çağrısız betik = ölü dosya; betiksiz çağrı = kırık kapı).
DOGRULAMA_ANAHTAR = ORACLE / "dogrulama_anahtar.py"
KOD_TAZELIK = ORACLE / "kod_tazelik.sh"


def _etiketli_metin(etiket: str) -> str:
    """Bir kapının BÜTÜN görevlerinin YAML dökümü — jeton/dal iddialarının aranacağı yer.

    TAŞIMA (Task 3): eski karşılığı dagit.sh'ta iki `echo "=== ["` başlığı arasındaki satır
    aralığıydı ve sınır bir kez kaymıştı ([F10] araya girince, R-0 2026-09-03). Etiketle
    seçim sınırı kaymaz: bir görev ya o kapıyı taşır ya taşımaz."""
    parcalar = [gorev_metni(g) for g in gorevler() if etiket in gorev_etiketleri(g)]
    assert parcalar, f"dagit.yml'de `[{etiket}]` etiketli görev yok — çivi bayatlamış"
    return "\n".join(parcalar)


def _etiketli_gorevler(etiket: str) -> list[dict]:
    return [g for g in gorevler() if etiket in gorev_etiketleri(g)]


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
    kume = set(f9_ciftleri())          # TAŞIMA (Task 3): kaynak `dagit_vars.yml::f9_ciftleri`
    for repo_yol, canli_yol in [
        ("deploy/oracle-a1/meridian-sprint@.service", "/etc/systemd/system/meridian-sprint@.service"),
        ("deploy/oracle-a1/50-meridian-sprint.rules", "/etc/polkit-1/rules.d/50-meridian-sprint.rules"),
        ("deploy/hermes/SOUL.md", "/home/ubuntu/.hermes/SOUL.md"),
        ("deploy/oracle-a1/meridian-tick-watchdog.service",
         "/etc/systemd/system/meridian-tick-watchdog.service"),
        ("deploy/oracle-a1/meridian-tick-watchdog.timer",
         "/etc/systemd/system/meridian-tick-watchdog.timer"),
    ]:
        assert (repo_yol, canli_yol) in kume, f"[F9] listesinde eksik/yanlış çift: {repo_yol}"
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

    ÖLÇÜ TAM REPO YOLUDUR — KOŞULSUZ (Faz 3, 2026-08-30). Önceki hâl KOŞULLUYDU: basename
    listede birden çok kez geçiyorsa tam yol, geçmiyorsa basename aranıyordu. O kural
    KENDİ ÖLÇTÜĞÜ VERİYE BAĞLIYDI ve gücü listeye göre değişiyordu — `distribution.yaml` tek
    profille TEKİLdi (yani zayıf eşleşme), ikinci profille ÇAKIŞTI (güçlü eşleşme), ve bir
    profil emekli edilse ZAYIFA GERİ DÖNERDİ. Bir çivinin gücü, koruduğu verinin o günkü
    şekline bağlı olamaz.

    ÖLÇÜLDÜ (simülasyon, 2026-08-30): sayıma dayalı kural, `@bekci`nin üç profil dosyası
    listeye girip başlığa girmediği senaryoda ZATEN kırmızı veriyordu — yani o senaryo açık
    değildi. Kapatılan şey senaryo değil KURALIN KENDİSİDİR: koşulsuz tam yol, aynı hükmü
    listenin bileşiminden BAĞIMSIZ hâle getirir.

    BEDELİ ÖDENDİ: `deploy.sh` başlığı artefaktları artık kısa adla değil REPO YOLUYLA anıyor
    (8 satır güncellendi). Okunurluk kaybı yok — operatörün kopyalayacağı yol zaten odur.
    Yön hâlâ TEK: başlıkta fazladan bir ad olması serbest (bağlam olabilir); listede olup
    başlıkta OLMAYAN yasaktır. TERS YÖN ayrı ölçülür (profil dosyalarının listeye GİRMESİ:
    tests/test_bot_profil_durusu_v329.py::test_F9_PROFILIN_UC_DOSYASINI_IZLIYOR).
    """
    # TAŞIMA (Task 3): kaynak `F9_LISTE` dizgesiydi, artık `dagit_vars.yml::f9_ciftleri`.
    yollar = [repo for repo, _ in f9_ciftleri()]
    assert yollar, "[F9] listesi boş — çivi kendi hedefini kaybetmiş"

    baslik = (ORACLE / "deploy.sh").read_text().split("set -euo pipefail", 1)[0]
    eksik = [y for y in yollar if y not in baslik]
    assert not eksik, (
        "`f9_ciftleri`de olup deploy.sh BAŞLIĞINDA TAM REPO YOLUYLA geçmeyen artefakt(lar): "
        + ", ".join(eksik)
        + " — dagit sürüklenmeyi raporlar ama operatörün okuduğu kurulum başlığı onlardan "
        "HİÇ söz etmiyor. Ölçü koşulsuz TAM YOLDUR: basename eşlemesi, aynı adı taşıyan "
        "kardeş dosyalar (config.yaml · SOUL.md · distribution.yaml her profilde bir kez) "
        "yüzünden birinin silinmesini gizler"
    )

def test_f9_CIKTISI_ARTEFAKTI_TEKIL_ADLANDIRIR():
    """KAPININ KENDİ ÇIKTISI, BAŞLIKTA KAPATILAN SINIFI AÇIK BIRAKMIŞTI (dal denetimi M3,
    2026-08-30).

    `test_f9_LISTESININ_TAMAMI_deploy_sh_BASLIGINDA_ADLANDIRILIR` başlığı TAM REPO YOLUNA
    bağladı — çünkü `config.yaml`, `SOUL.md` ve `distribution.yaml` her profilde bir kez geçiyor
    ve basename eşlemesi birinin silinmesini gizliyordu. Kapının KENDİ raporu ve `F9_AYRIK` /
    `F9_OLCULEMEDI` özetleri ise hâlâ basename basıyordu: iki profille `config.yaml` üç kez,
    `SOUL.md` üç kez listede. Operatör "⚠ config.yaml: AYRIK" satırından HANGİ profilin
    ayrıştığını okuyamaz — yani kapı sürüklenmeyi görür ama SÖYLEYEMEZ.

    TAŞIMA (Task 3, 2026-09-08): etiket eskiden dagit.sh'ın `_f9_ad="…"` ataması, üretim de bir
    kabuk döngüsüydü; çivi o atamanın BİÇİMİNİ tanıyordu. Playbook'ta etiketin iki yeri var ve
    ikisi de ölçülür: (a) `loop_control.label` — operatörün koşum sırasında GÖRDÜĞÜ satır, ve
    (b) `f9_ayrik` listesine EKLENEN değer — özetin bastığı ad. İkisi de TAM REPO YOLU olmalı;
    biri `basename`e düşerse rapor yine "hangi profil?" sorusunu cevaplayamaz. İddia aynı,
    ölçülen yüzey artık iki tane (eskiden bir kabuk değişkeniydi)."""
    yollar = [repo for repo, _ in f9_ciftleri()]
    assert yollar, "[F9] listesi boş — çivi kendi hedefini kaybetmiş"

    yinelenen = sorted({y for y in yollar if yollar.count(y) > 1})
    assert not yinelenen, (
        "[F9] raporu ve özeti artefaktları AYIRT EDİLEMEYEN adlarla anıyor: "
        + ", ".join(f"{y} ×{yollar.count(y)}" for y in yinelenen)
        + " — operatör hangi profilin ayrıştığını çıktıdan okuyamaz. Ölçü, başlıkta olduğu gibi "
        "TAM REPO YOLUDUR.")

    f9_gorevleri = _etiketli_gorevler("F9")
    etiketli = [g for g in f9_gorevleri if isinstance(g.get("loop_control"), dict)
                and "label" in g["loop_control"]]
    assert etiketli, ("[F9] döngülerinin hiçbiri `loop_control.label` taşımıyor — operatör "
                      "koşum sırasında hangi artefaktın ölçüldüğünü göremez")
    for gorev in etiketli:
        etiket = str(gorev["loop_control"]["label"])
        assert "basename" not in etiket and ".repo" in etiket, (
            f"{gorev.get('name')!r}: döngü etiketi TAM REPO YOLU değil ({etiket!r}) — "
            "aynı adı taşıyan kardeş dosyalar (config.yaml · SOUL.md · distribution.yaml her "
            "profilde bir kez) ayırt edilemez")
    ayrik = [g for g in f9_gorevleri if "f9_ayrik" in gorev_metni(g) and (
        g.get("ansible.builtin.set_fact") or g.get("set_fact"))]
    assert ayrik, "[F9] `f9_ayrik` listesini kuran görev yok — özet neyi basacak?"
    for gorev in ayrik:
        # ÖLÇÜ ARGÜMANDIR, AD DEĞİL: görevin kendi adı "basename DEĞİL" diye yazıyor ve adı da
        # tarayan bir çivi KENDİ gerekçesine takılıp her zaman kırmızı verirdi (yorum tarihçe,
        # kod hüküm — 2026-09-06).
        args = gorev.get("ansible.builtin.set_fact") or gorev.get("set_fact")
        assert "basename" not in str(args), (
            f"{gorev.get('name')!r}: ayrık listesine `basename` yazılıyor — özet artefaktı "
            "AYIRT EDİLEMEYEN adla anar")
        assert ".repo" in str(args), (
            f"{gorev.get('name')!r}: ayrık listesine TAM REPO YOLU yazılmıyor: {args}")


def test_f9_YERI_kuru_kosumda_da_gorunur():
    """YER YASASI: [F9] kuru koşumda da GÖRÜNÜR (operatör dağıtmadan önce görsün) ve [1c]'den
    SONRA koşar (birim-yönerge kapısının reçetesine atıf yapar, sıra ters dönerse anlatı kopar).

    TAŞIMA (Task 3): "kuru koşumdan önce" iddiasının taşıyıcısı dagit.sh'ın `--uygula` kapısıydı;
    playbook'ta kuru koşumun sınırı `--check`tir ve bir kapının kuru koşumda KOŞTUĞUNU söyleyen
    şey `check_mode: false`tur. İkisi de ölçülür: sıra ([1c] < [F9] < [2]) ve ölçüm görevlerinin
    check-mode'da GERÇEKTEN koştuğu."""
    bir_c = kapi_indeksi("1c")
    f9 = kapi_indeksi("F9")
    rsync = kapi_indeksi("2")
    assert bir_c < f9 < rsync, f"[F9] yanlış yerde (1c={bir_c}, F9={f9}, rsync={rsync})"
    olcenler = [g for g in _etiketli_gorevler("F9")
                if (g.get("ansible.builtin.stat") or g.get("stat")
                    or g.get("ansible.builtin.slurp") or g.get("slurp"))]
    assert olcenler, "[F9] hiçbir ölçüm görevi yok — kapı neye bakıyor?"
    kor = [g.get("name") for g in olcenler if g.get("check_mode") is not False]
    assert not kor, (
        f"[F9] ölçüm görevleri kuru koşumda ATLANIYOR ({kor}) — `check_mode: false` yok; "
        "sürüklenme yalnız gerçek dağıtımda görünürdü, yani dağıtmadan önce hiç")


def test_f9_RAPORLAR_engellemez():
    """[F9] bloğunda `exit` YOK: ayrıklık dağıtımı DURDURMAZ (artefaktlar dagit'in kopyalama
    kapsamında değil; engel, elle-kurulum akışını dagit'e kilitlerdi).

    BLOK SINIRI DARALDI (R-0, düzeltme turu 1, 2026-09-03): eski sınır "F9 başlığından `--uygula`
    kapısına kadar" idi ve o aralığa BAŞKA bir kapı ([F10] istenen-durum anomalisi, `exit 3`)
    girdi — çivi F9'un sözünü bozuldu sandı. Ölçülen şey F9'un KENDİ bloğudur; sınır artık bir
    sonraki `=== [` başlığıdır. Kapının BLOKLAMASI gereken bir gün gelirse yer değil söz değişir
    ve bu çivi yine kırmızıya düşer."""
    ihlal = [g.get("name") for g in _etiketli_gorevler("F9")
             if any(g.get(a) is not None for a in ("ansible.builtin.assert", "assert",
                                                   "ansible.builtin.fail", "fail"))]
    assert not ihlal, (
        f"[F9] görevlerinde `assert`/`fail` var — kapı 'raporlar, engellemez' sözünü bozdu: "
        f"{ihlal}")


def test_f9_OLCULEMEDI_dali_var():
    """UYDURMA YASAĞI: canlıdan okunamayan dosya ne 'aynı'dır ne 'ayrık' — kapının açık bir
    'ölçülemedi' dalı var ve nedeni ayrıştırıyor (dosya yok ↔ okunamadı: farklı iş kalemleri)."""
    metin = _etiketli_metin("F9")
    # İKİ AYRI OLGU (kabuktaki `F9_OLCULEMEDI` sayacının karşılığı): nedeni ayrıştırır.
    for olgu in ("f9_repo_yok", "f9_canli_yok"):
        assert olgu in metin, f"[F9] ölçülemedi dalı kayıp: {olgu}"
    assert "REPODA YOK" in metin, "liste-bayat dalı kayıp — kapı kendi kaynağına kör kalır"
    assert "CANLIDA YOK" in metin, "yok-dalı kayıp — 'hiç kurulmamış' hâli sessizleşir"


def test_f9_OZETI_dagitim_sonunda_tekrarlanir():
    """Kapı kuru-koşum tarafında konuşur; ayrıklık dağıtım ÖZETİNDE bir kez daha yazılır —
    raporlanan ama görülmeyen sürüklenme, hiç raporlanmamış gibidir. Özet 'DAĞITIM TAMAM'dan önce."""
    ozetler = [i for i, g in enumerate(gorevler())
               if "F9" in gorev_etiketleri(g) and (g.get("ansible.builtin.debug") or g.get("debug"))
               and "AYRIK" in gorev_metni(g)]
    assert len(ozetler) >= 2, (
        f"[F9] özeti yalnız {len(ozetler)} kez basılıyor — dağıtım sonu tekrarı düşmüş; "
        "raporlanan ama görülmeyen sürüklenme, hiç raporlanmamış gibidir")
    assert ozetler[-1] > son_kapi_indeksi("5b"), \
        "[F9] tekrar özeti [5b]'den ÖNCE — dağıtımın SONUNDA olmalı"
    assert ozetler[-1] < beyan_indeksi(), \
        "[F9] tekrar özeti [B] beyanından SONRA — beyan çıktının son sözü olmalı"
    # "--uygula TARAFINDA": tekrar yalnız GERÇEK dağıtımda basılır (kuru koşumda ilk özet zaten
    # birkaç satır yukarıdadır; orada tekrar, gürültüdür — bedel yasası).
    tekrar = gorevler()[ozetler[-1]]
    assert "not ansible_check_mode" in gorev_metni(tekrar), \
        "[F9] tekrar özeti kuru koşumda da basılıyor — dagit.sh kuru koşumda tekrar BASMIYORDU"


# =================================================================================================
# ② P0-b dağıtım-beyanı
# =================================================================================================
def test_beyan_DORT_ALAN_ve_hedef_yol():
    """Beyanın sözleşmesi (ENVANTER §4.2): dört alan + canlı hedef `state/dagitim.json`.
    Alan adları ortamlar-arası kıyasın okuyacağı API'dir — sessizce değişemez."""
    metin = _etiketli_metin("B")
    assert "state/dagitim.json" in metin, "beyanın canlı hedefi kayıp"
    assert "repo_kok" in metin, (
        "beyan hedefi canlı köke (`repo_kok` = /opt/meridian) bağlı değil — kontrolcüye yazan "
        "bir beyan, ortamlar-arası kıyasın ölçmek istediği ŞEYİ ölçmez")
    for alan in ("deployed_sha", "dagitildi_utc", "dagitan_host", "kirli_gec_kullanildi"):
        assert alan in metin, f"beyan alanı kayıp: {alan}"


def test_beyan_JSON_bicimi_GECERLI():
    """Beyanın TİPLERİ korunur: `kirli_gec_kullanildi` BOOL, `sandbox_eski_kod` DİZİ.

    TAŞIMA (Task 3, 2026-09-08): eski hâl dagit.sh'ın `printf` şablonunu söküp yuvalarını
    doldurarak `json.loads`tan geçiriyordu. Şablon silindi; JSON'u playbook `to_json` ile kurar
    (BAYT düzeyinde gerçek `ansible` ile ölçen çivi: v452 `test_B13_…`). Burada korunan iddia
    TİP iddiasıdır ve o iddia YAML'da yaşar: `| bool` filtresi düşerse `kirli_gec_kullanildi`
    `"False"` diye TIRNAKLI bir dizgeye döner ve `/api/diagnostics` okuyucusu (v274) onu her
    zaman DOĞRU sayar — sessiz yanlış hüküm.

    TSK-140 (2026-09-04): beşinci alan `sandbox_eski_kod` JSON DİZİSİDİR — kum-havuzu birimleri
    başlangıç kodunu taşırken beyan "bu sha canlıda" cümlesine dürüst dipnot düşer."""
    beyan = [g for g in _etiketli_gorevler("B")
             if isinstance(g.get("ansible.builtin.set_fact") or g.get("set_fact"), dict)
             and "dagitim_beyani" in (g.get("ansible.builtin.set_fact") or g.get("set_fact"))]
    assert beyan, "[B] beyanını kuran `set_fact` yok"
    alanlar = (beyan[0].get("ansible.builtin.set_fact")
               or beyan[0].get("set_fact"))["dagitim_beyani"]
    assert set(alanlar) >= {"deployed_sha", "dagitildi_utc", "dagitan_host",
                            "kirli_gec_kullanildi", "sandbox_eski_kod"}
    assert "| bool" in str(alanlar["kirli_gec_kullanildi"]), (
        "`kirli_gec_kullanildi` bool'a ÇEVRİLMİYOR — Jinja çıktısı dizgedir ve beyan "
        '"False" yazar; JSON okuyucusu onu HER ZAMAN doğru sayar')
    assert "default([])" in str(alanlar["sandbox_eski_kod"]).replace(" ", ""), (
        "`sandbox_eski_kod` boş dala düşünce TANIMSIZ kalır — 'yok' ile 'ölçülmedi' ayrımı "
        "kaybolur (uydurma yasağı)")
    # JSON'un KENDİSİ `to_json` ile kurulur (dizge birleştirme değil): elle kurulan bir JSON,
    # tırnak kaçışı gereken bir birim adında yarım dosya üretirdi.
    metin = _etiketli_metin("B")
    assert "to_json" in metin, "[B] JSON'u `to_json` ile kurmuyor — elle dizge birleştirme"
    # TAŞIMA (TSK-176 A1): ayrımı YAPAN satır artık `kod_tazelik.sh`ta, ayrımı BEYANA ÇEVİREN
    # satır dagit.sh'ta. İkisi de ölçülür — jeton (`BEKLENEN`) iki tarafta AYNI dizge olmazsa
    # kum-havuzu birimleri beyandan sessizce düşerdi (TSK-140 dipnotu boşalır, kimse görmez).
    assert '"kum havuzunda"' in KOD_TAZELIK.read_text(), \
        "[5b] kum-havuzu ayrımı birimin KENDİ beyanından (Description) türemiyor (TSK-140)"
    # JETON İKİ TARAFTA AYNI DİZGE: ayrımı YAPAN satır `kod_tazelik.sh`ta, ayrımı BEYANA
    # ÇEVİREN görev [5b]'de. Ayrışırlarsa kum-havuzu birimleri beyandan sessizce düşer
    # (TSK-140 dipnotu boşalır, kimse görmez).
    besb = _etiketli_metin("5b")
    assert "BEKLENEN" in KOD_TAZELIK.read_text() and "BEKLENEN" in besb, \
        "`BEKLENEN` jetonu iki tarafta aynı değil — beyan dipnotu sessizce boşalır"
    assert "sandbox_eski_kod" in besb, \
        "[5b] bulgusu beyanın `sandbox_eski_kod` alanına hiç bağlanmıyor"


def test_beyan_YERI_basarili_dagitimin_sonunda():
    """Beyan [5] doğrulamadan SONRA yazılır ('başarılı dağıtım' beyanı — [4]/[5]'ten önce yazılsa
    düşen bir dağıtım da beyan bırakır, beyan yalan söylerdi) ve sha [0a]'da DONDURULUR
    (660dc10 dersi: paralel oturum main'i dağıtım sırasında taşıyabilir)."""
    dondur = next((i for i, g in enumerate(gorevler())
                   if "0a" in gorev_etiketleri(g) and "dagit_sha" in gorev_metni(g)), None)
    assert dondur is not None, "`dagit_sha` [0a]'da hiç dondurulmuyor — çivi bayatlamış"
    kapi_0b = kapi_indeksi("0b")
    dogrulama = kapi_indeksi("5")
    beyan = beyan_indeksi()
    assert dondur < kapi_0b, "dagit_sha [0a]'da dondurulmuyor — beyan koşum-sonu tepesini söyler"
    assert dogrulama < beyan, "beyan [5]'ten önce — başarısız dağıtım da beyan bırakırdı"


def test_beyan_ATOMIK_ve_dogrulamali():
    """tmp + mv (atomik) ve yazım sonrası bayt-özdeş doğrulama ([1b] kopya disiplini). Doğrulama
    düşerse ENGEL DEĞİL uyarı: dağıtım o noktada zaten tamam, beyansızlık dağıtımı geri almaz."""
    metin = _etiketli_metin("B")
    assert ".dagitim.json.tmp" in metin, "geçici dosya yok — yazım atomik değil"
    assert "- mv" in metin, "`mv` ile yerine alma yok — yarım JSON okunabilir kalır"
    assert "BEYAN YAZILAMADI" in metin, "yazım arızası sessiz — uyarı dalı kayıp"
    ihlal = [g.get("name") for g in _etiketli_gorevler("B")
             if any(g.get(a) is not None for a in ("ansible.builtin.assert", "assert",
                                                   "ansible.builtin.fail", "fail"))]
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
    """(a) `meridian-learn` durdurma satırında VE başlatma-türetiminin aday kümesinde olmalı.

    SÖZLEŞME DEĞİŞTİ (TSK-092, 2026-09-02; vaka ×2): start satırı artık birim adı SABİTLEYEMEZ —
    başlatma listesi `is-enabled`dan türetilir (çivisi test_dagit_istenen_durum_v367). Bu çivinin
    2026-08-24 ruhu (learn'e dağıtım sessizce etkisiz kalmasın) yeni mekanizmada korunur:
    learn ENABLED iken türetim onu zaten başlatır (bayat bytecode imkânsız); DISABLED iken hiç
    koşmuyordur (bayatlayacak süreç yok).

    SÖZLEŞME İKİNCİ KEZ DEĞİŞTİ (TSK-092 (a), 2026-09-03): stop satırı da birim adı SABİTLEYEMEZ —
    durdurma listesi `is-active`ten türetilir (çivisi yine v367). Bu çivinin ruhu (learn pencereden
    tümden DÜŞMESİN) artık İKİ aday kümesinde ölçülür: `_DURDUR` (is-active) ve `_BASLAT`
    (is-enabled). Learn birinden düşerse pencere ona kör olur — 2026-08-24 unutma sınıfı geri gelir.

    SÖZLEŞME ÜÇÜNCÜ KEZ DEĞİŞTİ (TSK-176 Faz A1 Task 3, 2026-09-08): pencere artık dagit.sh'ta
    değil `deploy/ansible/dagit.yml`de. Aday KÜMESİ tek kaynağa (`dagit_vars.yml::birim_adaylari`)
    çıktı, türetim de iki `systemctl` ölçümü + iki `when` ifadesi oldu. Çivinin 2026-08-24 ruhu
    AYNEN korunur ve yine İKİ kümede ölçülür: learn aday listesinde OLMALI ve pencerenin hem
    durdurma hem başlatma kolu O LİSTEDEN türemeli. Kolların YÖNÜ ayrıca Jinja ile çözülerek
    ölçülür (v452 B9) — burada ölçülen şey KAPSAMdır."""
    adaylar = _vars_birim_adaylari()
    assert "meridian-learn" in adaylar, \
        "aday kümesinde meridian-learn yok — pencere learn'e kör (2026-08-24 unutma vakası)"
    for etiket, kaynak in (("4", "is-active"), ("4", "is-enabled")):
        metin = _etiketli_metin(etiket)
        assert kaynak in metin, f"[4] penceresi {kaynak} ölçümünü taşımıyor"
    # KAPSAM LİSTEDEN TÜRER: stop/start döngüleri sabit bir birim paketi üzerinde koşamaz.
    pencere = _etiketli_metin("4")
    assert "birim_adaylari" in pencere, \
        "[4] penceresi aday listesinden türemiyor — sabit paket, 2026-08-24 unutma sınıfını açar"


def test_kod_tazelik_kapisi_VAR_ve_BEYANDAN_ONCE():
    """(b) [5b] değişmezi ve YERİ.

    Kapı [B] dağıtım-beyanından ÖNCE düşmeli: beyan `state/dagitim.json`a "bu sha canlıda" yazar
    ve süreçlerden biri eski kodu koşuyorsa bu cümle YANLIŞTIR. Önce düşerse dosya eski sha'da
    kalır — koşan sistemin GERÇEK hâli odur (operatör kararı, 2026-08-24)."""
    # İDDİA ÇAĞRI BİÇİMİNE BAĞLI (düzeltme turu 2): metinde yolun GEÇMESİ bir çağrı değildir —
    # aynı yol onarım reçetesinde de geçiyordu ve gerçek çağrı bozulunca bu çivi YEŞİL kalıyordu
    # (mutasyonla ölçüldü 2026-09-08). TAŞIMA (Task 3): çağrı artık playbook'un `script:`
    # görevidir; YAML PARSE, metin aramasından güçlüdür — bir yorumdaki yol yapısal olarak
    # çağrı sayılamaz.
    assert any(KOD_TAZELIK_CAGRI.search(c) for c in script_cmdleri()), (
        "[5b] gövdesi bir `script:` görevinde çağrılmıyor — kapı adı duruyor, ölçüm yok "
        "(çıkarılan betik ölü dosya olur)")
    govde = KOD_TAZELIK.read_text()
    assert "ExecMainStartTimestamp" in govde, (
        "kapı süreç başlangıcını okumuyor — 'active' cümlesi bu kusuru göremez")
    # KAPSAM TÜRETİLİR, YAZILMAZ: birim adları elle sayılsaydı yarın eklenen birim unutulurdu.
    assert "ExecStart" in govde, "kapsam ExecStart'tan türetilmiyor — unutma sınıfı açık kalır"
    # ÇAPA ETİKETE BAĞLI (Task 3): eski hâl `echo "=== [5b/"` satırını arıyordu ve dosyanın
    # BAŞINDAKİ içindekiler yorumu bir kez sahte kırmızı vermişti. Görev etiketi kaymaz.
    i_kapi, i_beyan = kapi_indeksi("5b"), beyan_indeksi()
    assert i_kapi < i_beyan, (
        f"[5b] kapısı beyandan SONRA ({i_kapi} > {i_beyan}) — yarı-etkili bir dağıtım "
        f"'tamam' diye damgalanır")
    # Kapı ENGELLER (F9'un tersine): yarı-etkili dağıtım sessizce geçemez.
    engel = [g for g in _etiketli_gorevler("5b")
             if g.get("ansible.builtin.assert") or g.get("assert")
             or g.get("ansible.builtin.fail") or g.get("fail")]
    assert engel, "[5b] ihlalde DÜŞÜRMÜYOR (`assert`/`fail` yok) — kapı değil rapor olur"


# =================================================================================================
# §5d [5a] DOĞRULAMA-TOKEN ANAHTAR KONTROLÜ (TSK-148, 2026-09-05 — dağıtım #13 vakası)
# =================================================================================================
# VAKA (dağıtım #13, 2026-09-04 20:04Z): `--uygula` [5] yalnız `healthz: 200` okuyor. Rol-1 elle
# doğrularken token'sız `/api/alerts` çağırdı, `{"detail": …}` yetkisiz cevabı "pending None" diye
# okundu (sahte "boş"), hayalet sayacı yanlış uçta arandı. Sınıf: [5b]'nin "active ≠ yeni kod"unun
# uç-katmanı eşi — "200 döndü ≠ doğru gövde döndü". Üç çivi (brief D3): (1) `DOGRULAMA_UCLARI`
# sabiti TEK yerde + üç uç + sıra [5]→[5b]→[B] korunur, (2) token okuma `.dash.env`den ve `$T`
# hiçbir echo/printf/tee argümanında geçmez, (3) fail-open ("ölçülemedi") + fail-closed ("✗")
# dalları ikisi de metinde.
def test_dogrulama_uclari_UC_GIRDI_ve_SIRA_korunur():
    """(1) `DOGRULAMA_UCLARI` üç uç taşır (alarm/öğrenme/performans — D2: elle sayılmasın diye
    TEK sabitte durur) ve yeni blok healthz'in hemen ardına, [5b]/[B]'den ÖNCE girmiş — sıra
    [5] → [5b] → [B] bozulmamış."""
    # TAŞIMA (Task 3): sabit `dagit_vars.yml::dogrulama_uclari`; çağrı playbook `script:`inde.
    uclar = _vars_dogrulama_uclari()
    assert len(uclar) == 3, f"`dogrulama_uclari` üç uç taşımalı (bulunan: {len(uclar)}): {uclar}"
    assert any("deploy/oracle-a1/dogrulama_anahtar.py" in c for c in script_cmdleri()), \
        "[5a] gövdesi bir `script:` görevinde çağrılmıyor — uç listesi duruyor ama kimse ölçmüyor"
    assert "x-meridian-token" in DOGRULAMA_ANAHTAR.read_text(), \
        "kontrol x-meridian-token başlığını taşımıyor"

    dogrulama = kapi_indeksi("5")
    uc_kontrolu = kapi_indeksi("5a")
    kod_tazelik = kapi_indeksi("5b")
    beyan = beyan_indeksi()
    assert dogrulama < uc_kontrolu < kod_tazelik < beyan, (
        f"sıra bozuk: [5]={dogrulama}, [5a]={uc_kontrolu}, [5b]={kod_tazelik}, [B]={beyan}")


def test_dogrulama_token_degeri_ciktiya_BASILMAZ():
    """(2) Token okuma satırı `.dash.env`den okur; `$T` hiçbir echo/printf/tee argümanında GEÇMEZ.

    AST DEĞİL — SHELL METİN REGEX'İ (v266 ailesinin yöntemi): dagit çıktısı günlüğe kopyalanıyor
    ve sır süzgeci yalnız BEYAZ-LİSTE adlar basar — token değeri o listede DEĞİL, yani hiçbir
    çıktı satırına girmemesi gerekir (D1: "değer HİÇBİR ÇIKTIYA basılmaz")."""
    govde = DOGRULAMA_ANAHTAR.read_text()
    assert ".dash.env" in govde and "MERIDIAN_DASH_TOKEN" in govde, \
        "token okuma satırı .dash.env'den MERIDIAN_DASH_TOKEN okumuyor"
    # ÇAĞIRAN TARAFI (Task 3'te dagit.sh'tan playbook'a taşındı): token DEĞERİ hiçbir görev
    # argümanına girmez — betik onu A1'de kendisi okur. Playbook'un `[5a]` görevleri yalnız UÇ
    # LİSTESİNİ ve betik yolunu taşır; bir gün `.dash.env` değeri bir `-e`/`debug`a sızarsa
    # dagit çıktısı günlüğe kopyalandığı için sır süzgecinin BEYAZ LİSTESİ dışına düşerdi.
    besa = _etiketli_metin("5a")
    for sizinti in ("MERIDIAN_DASH_TOKEN", ".dash.env"):
        assert sizinti not in besa, (
            f"[5a] görevleri token kaynağını ({sizinti}) kendi argümanına almış — okuma A1'de, "
            "betiğin İÇİNDE kalmalı")
    # PYTHON TARAFI: token değeri hiçbir `print` argümanına girmiyor. Davranışsal ikizi
    # tests/test_ansible_dagit_v452.py içindeki A4c5 çivisidir — o çivi değeri GERÇEKTEN
    # koşturup çıktıda arar, bu çivi deseni metinde yasaklar.
    basim = [ln for ln in govde.splitlines() if re.search(r"\bprint\(.*\btoken\b", ln)]
    assert not basim, f"token değeri bir print argümanında geçiyor: {basim}"


def test_dogrulama_FAIL_OPEN_ve_FAIL_CLOSED_dallari_VAR():
    """(3) Token dosyası okunamazsa FAIL-OPEN (⚠ ölçülemedi, dağıtım DÜŞMEZ — token yerel
    geliştirme makinesinde de olmayabilir, uydurma yasağı: ölçülemeyen None + neden); anahtar
    eksikse FAIL-CLOSED (✗, [5b] gibi düşer — beyan yazılmaz). İkisi de metinde olmalı, aksi
    hâlde biri sessizce kaybolmuş demektir.

    ÖLÇÜM [5a] BLOĞUYLA SINIRLI (mutasyonla ölçüldü, TSK-148): dosya genelinde "ölçülemedi" ve
    "✗" ARAMAK yanlış-yeşil verir — [5b]/[5c] kendi "ölçülemedi"/"IHLAL" dallarını ZATEN taşıyor,
    onlardan biri kırılmasa bile bu çivi hedefine kör kalır ve yeşil kalırdı."""
    # BLOK SINIRI ETİKETTEN (Task 3): eski sınır iki `echo` başlığı arasıydı ve bir kez kaymıştı.
    blok = _etiketli_metin("5a")
    assert "ÖLÇÜLEMEDİ" in blok and "token yok" in blok, "[5a] fail-open dalı (ölçülemedi) yok"
    engel = [g for g in _etiketli_gorevler("5a")
             if g.get("ansible.builtin.assert") or g.get("assert")
             or g.get("ansible.builtin.fail") or g.get("fail")]
    assert engel, "[5a] anahtar eksikken DÜŞÜRMÜYOR — kapı değil rapor olur"
    # FAIL-OPEN DALI BETİKTE: token okunamazsa `OLCULEMEDI token yok` basılır ve ÇIKIŞ 0 verilir;
    # dagit.sh o jetonu TAM EŞİTLİKLE tanır ve dağıtımı sürdürür. İddia (dağıtım DÜŞMEZ) aynı,
    # iki parçası iki dosyada — ikisi de burada ölçülür, yoksa biri sessizce ötekinden kopar.
    govde = DOGRULAMA_ANAHTAR.read_text()
    assert "OLCULEMEDI token yok" in govde and "OLCULEMEDI token yok" in blok, \
        "[5a] fail-open jetonu iki tarafta AYNI dizge değil — sözleşme sessizce ayrıştı"
    assert "return 0" in govde, "[5a] betiği token okunamazken 0 (fail-open) döndürmüyor"


# =================================================================================================
# §5e [F9] YENİ ARTEFAKT — unattended-upgrades BEYANI (TSK-149, 2026-09-05)
# =================================================================================================
# ÖLÇÜLDÜ (A1, 2026-09-05 11:3xZ, keşif ajanı): unattended-upgrades reboot ayarları TANIMSIZ
# (varsayılan false) — A1'in duruşu Ubuntu'nun sessiz varsayılanına yaslanıyordu ve varsayılan
# yarın değişirse kimse fark etmezdi. HÜKÜM (Rol-1): Seçenek A — güvenlik yamaları KALSIN, reboot
# KAPALI; varsayılan BEYANLI dosyaya çıkar. Seçenek B (kara liste) ve C (kapat) REDDEDİLDİ.
#
# İKİ ÇİVİ, İKİ AYRI KATMAN: (1) yeni çift F9_LISTE'de + repo tarafı GERÇEKTEN var mı — genel
# desen zaten test_f9_LISTESININ_TAMAMI_deploy_sh_BASLIGINDA_ADLANDIRILIR ve
# test_f9_CIKTISI_ARTEFAKTI_TEKIL_ADLANDIRIR ile KOŞULSUZ (tüm F9_LISTE üzerinden) ölçülüyor —
# burada yalnız BU çiftin GERÇEKTEN eklendiği doğrulanır (ekleme unutulursa genel desenler bunu
# yakalayamaz, çünkü onlar F9_LISTE'nin KENDİSİNDEN türer, listeye hiç girmemiş bir artefaktı
# göremezler). (2) BEYAN DOSYASININ İÇERİĞİ — genel F9 çivileri yalnız EŞLEŞME/İSİMLENDİRME
# ölçer, dosya boş ya da yanlış anahtar taşısa bile yeşil kalırlardı.
def test_f9_unattended_upgrades_LISTEDE():
    """Yeni artefakt F9_LISTE'de doğru çiftle var; repo tarafı GERÇEKTEN dosya (uydurma yasağı:
    listeye var olmayan bir yol girerse kapı her dağıtımda 'ölçülemedi' gürültüsü üretir)."""
    cift = ("deploy/oracle-a1/52meridian-unattended-upgrades",
            "/etc/apt/apt.conf.d/52meridian-unattended-upgrades")
    assert cift in set(f9_ciftleri()), "[F9] listesinde unattended-upgrades beyanı eksik"
    assert (ORACLE / "52meridian-unattended-upgrades").is_file(), \
        "F9 repo tarafı yok: deploy/oracle-a1/52meridian-unattended-upgrades"


def test_unattended_upgrades_BEYAN_IKI_ANAHTARI_TASIYOR():
    """Beyan dosyası varsayılanı AÇIKÇA yazar: `Automatic-Reboot` ve
    `Automatic-Reboot-WithUsers` ikisi de "false" — brief'in çivilediği iki alan (davranış
    DEĞİŞMİYOR, yalnız varsayılana-yaslanma durumu beyana dönüşüyor).

    Dosya ölçüm özetinde `Allowed-Origins` sözcüğünden şerh olarak SÖZ EDEBİLİR (neden
    dokunulmadığını anlatmak için) ama bir YÖNERGE olarak set ETMEZ — SSoT `50unattended-
    upgrades`te kalır (tek-kaynak yasası, CLAUDE.md §4); aynı alanın iki dosyada YÖNERGE olarak
    tutulması sessizce ayrışabilirdi. Ölçü bu yüzden YÖNERGE SATIRI (`Unattended-Upgrade::
    Allowed-Origins ... ;`), düz metin geçişi değil."""
    beyan = (ORACLE / "52meridian-unattended-upgrades").read_text()
    assert re.search(r'^Unattended-Upgrade::Automatic-Reboot\s+"false";', beyan, re.M), \
        'Automatic-Reboot "false" AÇIKÇA yazılı değil'
    assert re.search(r'^Unattended-Upgrade::Automatic-Reboot-WithUsers\s+"false";', beyan, re.M), \
        'Automatic-Reboot-WithUsers "false" AÇIKÇA yazılı değil'
    assert not re.search(r'^\s*Unattended-Upgrade::Allowed-Origins\b', beyan, re.M), (
        "Allowed-Origins bu dosyada YÖNERGE olarak set edilmiş — SSoT 50unattended-upgrades'te "
        "kalmalıydı (tek-kaynak yasası)")


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
