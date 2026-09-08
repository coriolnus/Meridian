"""v451 — TSK-176 Faz A0 Task 1: `deploy/ansible/` iskeleti + `meridian_a1` rolü çivileri.

NUMARA KİMLİKTİR: v451 planda (`docs/superpowers/plans/2026-09-08-ansible-a0.md`, Global
Constraints) SABİT olarak verildi; bu turda `tests/` altında `v45x` aralığında yalnız
`test_sprint_audit_v45.py` (farklı kimlik sınıfı — `v45`, `v451` değil) vardı, en büyük kullanılan
`vNNN` `v442`'ydi (2026-09-08 ölçümü) — çakışma YOK.

KAPSAM. Bu dosya A0'ın TAMAMINI (Task 1 iskeleti + Task 2 görev dosyaları) ölçer: depo
kökündeki `ansible.cfg` ile `deploy/ansible/` altındaki `inventory.ini`/`site.yml` +
`roles/meridian_a1/{defaults,handlers,tasks}/*.yml` gerçek YAML'dır ve `ansible-playbook
--syntax-check` ile açılır (Çivi 1); `defaults/main.yml`'deki `birim_kaynaklari`/
`dropin_dizinleri` envanteri `deploy/` ağacındaki GERÇEK dosyalarla EŞLEŞİR (Çivi 2); YASAK
DESENLER YAML PARSE EDİLEREK ölçülür ve uzun ömürlü birimlerin restart yasağı ŞABLONLU adları
(`name: "{{ item }}"` + `loop: "{{ etkin_birimler }}"`) defaults'tan ÇÖZEREK denetlenir (Çivi 3);
`ansible-lint deploy/ansible` production profiliyle temizdir (Çivi 4).

TUR 2 DÜZELTMESİ (2026-09-08, çekişmeli inceleme K6/K11): Çivi 3'ün restart taraması Task 2
teslim edildikten SONRA da 0 düğüm eşleştiriyordu — `name` değeri `{{ item }}` olduğu için
literal küme ile hiç kesişmiyordu ve bu dosyanın eski başlığı "7 birim × gerçek görevler üzerinde
koşuyor" diye ÖLÇÜLMEMİŞ bir kapsama iddia ediyordu. Tarama artık `tasks/*.yml` + `handlers/
main.yml`in TAMAMINI gezer ve `loop`/`with_*` ifadelerini `defaults/main.yml`ten çözer.

TSK-176 FAZ A1 TASK 2 DÜZENLEMESİ (2026-09-08) — `deploy/ansible/dagit.yml` doğdu ve bu dosyanın
taraması `deploy/ansible/` altındaki HER YAML'ı gezdiği için onu da kapsıyor. Üç değişiklik,
gerekçeleri `test_uzun_omurlu_birimler_restart_edilmiyor` docstring'inde AYRINTILI:
  (a) şablon/döngü çözümü artık `vars/dagit_vars.yml`i de okur (`_cozum_degiskenleri`) — yoksa
      `loop: "{{ birim_adaylari }}"` "çözülemedi" ile çiviyi HEDEFİ DIŞINDA kırıyordu;
  (b) birim adları kıyastan önce `.service`e normalize edilir — `birim_adaylari` uzantısız yazar
      ve normalize edilmeden kesişim HER ZAMAN boş çıkardı (sahte yeşil, K6/K11 sınıfı);
  (c) (b)'nin sonucu olarak `dagit.yml` bu ÇİVİDEN çıkarıldı (`RESTART_TARAMASI_DISI`): o dosya
      BAKIM PENCERESİDİR ve stop/start onun işidir; yüzeyi `tests/test_ansible_dagit_v452.py`
      B3 ile DAHA DAR ölçülür. Dışlama yalnız bu çividedir — Çivi 3a (yasak desenler),
      Çivi 1 (parse/syntax) ve Çivi 4 (ansible-lint) `dagit.yml`i aynen kapsar.
Mutasyonla ölçüldü (2026-09-08): rolün `etkin_birimler` görevine `state: started` eklendiğinde
çivi hâlâ KIRMIZI oluyor — düzenleme onu körleştirmedi.

ÖLÇÜLEMEYEN/BİLİNEN SINIR — dürüst beyan: `ansible-playbook`/`ansible-lint` önce KOŞAN
yorumlayıcının yanında (`Path(sys.executable).parent`, yani `.venv/bin` — pyproject/uv.lock'un
PİNLEDİĞİ sürüm), sonra PATH'te aranır; hiçbirinde yoksa çivi `pytest.fail` ile PATLAR
(CLAUDE.md §6: "koşamıyorum" ile "kırmızı" karıştırılmaz — bu çivi ikisini AYIRT EDEMEZ, ikisini
de kırmızı sayar; bilinçli tasarım). A1'e HİÇBİR bağlantı YOK — yalnız `--syntax-check` ve
`ansible-lint` statik analizdir.

ÖLÜ DOSYA BULGUSU (plan talimatının ÖTESİNDE, bu turda ölçüldü): `deploy/litestream.service` +
`deploy/litestream.yml` (üst dizin) planın kendisinde adı geçen ölü dosyalardı (A0 envanteri, Tek-
Kaynak Riski #3). Bu dosyayı yazarken `deploy/meridian.service` (üst dizin) diff'i ALINDI ve o da
eski GCP/docker-compose biriminin (`Type=oneshot`, `docker compose up`) AYNI sınıfta ölü bir
kopyası olduğu görüldü (canlı A1 `deploy/oracle-a1/meridian.service`yi — native uv/uvicorn —
kullanıyor). Rol dahil edilmedi: dışlanmazsa Çivi 2 deploy/meridian.service'i "kapsanmamış" diye
KIRMIZI yapardı — bu Task 1'in hedefiyle (iskelet doğruluğu) ilgisiz bir kırmızı olurdu. Bu yeni
bulgu README.md'ye "silinmeli" notuyla yazıldı; SİLİNMEDİ (git yok, dosya silme de bu turun
kapsamı DIŞINDA — karar Rol-1'e ait).
"""

from __future__ import annotations

import glob
import pathlib
import re
import shutil
import subprocess
import sys

import jinja2
import pytest
import yaml

REPO_KOK = pathlib.Path(__file__).resolve().parent.parent
DEPLOY_DIZIN = REPO_KOK / "deploy"
ANSIBLE_DIZIN = DEPLOY_DIZIN / "ansible"
SITE_YML = ANSIBLE_DIZIN / "site.yml"
INVENTORY_INI = ANSIBLE_DIZIN / "inventory.ini"
ROL_DIZIN = ANSIBLE_DIZIN / "roles" / "meridian_a1"
DEFAULTS_YML = ROL_DIZIN / "defaults" / "main.yml"
# TUR 2 (K7): `ansible.cfg` DEPO KÖKÜNDEDİR. Ölçüldü (2026-09-08, ansible-core 2.18.19, depo
# kökünden `ansible-config dump --only-changed`): dosya `deploy/ansible/` altındayken çıktı
# `CONFIG_FILE() = None` veriyordu — yani README'nin belgelediği HER komut (hepsi kökten
# çağrılıyor) cfg'siz koşuyordu ve `host_key_checking`/`interpreter_python`/`pipelining`
# ayarlarının HİÇBİRİ yürürlükte değildi. `.ansible-lint` ile aynı gerekçe: ansible da lint de
# yapılandırmayı CWD'den yukarı arar, target dizininden DEĞİL.
ANSIBLE_CFG = REPO_KOK / "ansible.cfg"
DAGIT_SH = REPO_KOK / "dagit.sh"

# TEK KAYNAK (Task 3, 2026-09-08): `dagit_vars.yml`/`dagit.yml` sökücüleri v452'de yaşıyor;
# buraya KOPYALANMAZ, ithal edilir (dagit.sh döneminde `F9_LISTE`nin DÖRT ayrı regex'i vardı).
from tests.test_ansible_dagit_v452 import (  # noqa: E402
    f9_ciftleri as _f9_ciftleri,
    gorev_etiketleri as _dagit_etiketleri,
    gorevler as _dagit_gorevleri,
)


# README.md "Bilinen ölü/silinmeli dosyalar" ile TEK KAYNAK: ikisi de üst dizinde (deploy/ altı,
# oracle-a1/hindsight/apisix DIŞI), rolün kaynağı DEĞİL. Silinmeleri bu turun kapsamı dışında.
OLU_BIRIM_DOSYALARI = {
    (DEPLOY_DIZIN / "litestream.service").resolve(),
    (DEPLOY_DIZIN / "meridian.service").resolve(),
}

UZUN_OMURLU_BIRIMLER = {
    "meridian.service",
    "meridian-barsarchive.service",
    "hindsight-api.service",
    "hindsight-cp.service",
    "apisix.service",
    "apisix-etcd.service",
    "meridian-litestream.service",
}
SYSTEMD_MODUL_ANAHTARLARI = (
    "systemd",
    "systemd_service",
    "ansible.builtin.systemd",
    "ansible.builtin.systemd_service",
)


def _yaml_dosyalari() -> list[pathlib.Path]:
    return sorted(set(ANSIBLE_DIZIN.rglob("*.yml")) | set(ANSIBLE_DIZIN.rglob("*.yaml")))


def _defaults_veri() -> dict:
    veri = yaml.safe_load(DEFAULTS_YML.read_text(encoding="utf-8"))
    assert isinstance(veri, dict), f"{DEFAULTS_YML}: kök düğüm dict değil"
    return veri


#: TSK-176 Faz A1 (Task 2): `deploy/ansible/` altında ARTIK İKİ değişken kaynağı var — A0 rolünün
#: defaults'ı ve `dagit.yml`in `vars/dagit_vars.yml`i. Şablon çözen çiviler ikisini birden okur;
#: yoksa yeni playbook'un `loop: "{{ birim_adaylari }}"` ifadesi "çözülemedi" ile ÇİVİYİ kırar
#: (hedefini değil). Dosya yoksa (A0-öncesi ağaç) sessizce atlanır — varlığı ayrıca v452 B0'da.
DAGIT_VARS_YML = ANSIBLE_DIZIN / "vars" / "dagit_vars.yml"

#: Uzun-ömürlü birim restart yasağının taranmayacağı dosyalar — GEREKÇE `_dongu_ogeleri`i
#: kullanan çivinin docstring'inde (c) maddesindedir: `dagit.yml` bakım penceresidir ve kendi
#: (daha dar) çivisini `tests/test_ansible_dagit_v452.py` B3'te taşır.
#: TUR 2 (inceleme, 2026-09-08): dışlama DOSYA ADINA değil TAM YOLA bağlıdır — ad bazlıyken
#: `deploy/ansible/` altında ileride doğacak HERHANGİ bir `dagit.yml` (ör. bir rolün kendi
#: görev dosyası) sessizce taranmaz olurdu; muafiyet tek ve ADRESLİ olmak zorundadır.
RESTART_TARAMASI_DISI = {"deploy/ansible/dagit.yml"}


def _cozum_degiskenleri() -> dict:
    """Şablon/döngü çözümü için birleşik değişken kümesi (rol defaults + dagit vars)."""
    veri = dict(_defaults_veri())
    if DAGIT_VARS_YML.is_file():
        veri.update(yaml.safe_load(DAGIT_VARS_YML.read_text(encoding="utf-8")) or {})
    return veri


def _yaml_govde_yorumsuz(dosya: pathlib.Path) -> str:
    """Yorum SATIRLARINI (lstrip sonrası `#` ile başlayan) çıkarır — yalnız gerçek YAML gövdesi.

    Bu dosyanın kendi başlık yorumları ("... `state: restarted/started` yok" gibi örnekler)
    aksi halde Çivi 3'ü kendi belgesine karşı YANLIŞ ALARM verdirirdi (metin araması yorumu
    koddan ayırt etmezse). Satır-içi (`kod  # yorum`) biçimi bu depoda YAML dosyalarında
    kullanılmıyor (ölçüldü: mevcut 4 dosyada tek örnek yok) — kapsam dışı bırakıldı.
    """
    satirlar = [
        satir
        for satir in dosya.read_text(encoding="utf-8").splitlines()
        if not satir.lstrip().startswith("#")
    ]
    return "\n".join(satirlar)


def _tum_dugumler(node):
    """Bir YAML belgesindeki HER dict düğümünü (task/handler/module-args dahil) düzleştirir."""
    sonuc: list[dict] = []

    def _gez(n):
        if isinstance(n, dict):
            sonuc.append(n)
            for v in n.values():
                _gez(v)
        elif isinstance(n, list):
            for item in n:
                _gez(item)

    _gez(node)
    return sonuc


def _ansible_ikili(ad: str) -> str:
    """`ansible-*` ikilisini ÖNCE koşan yorumlayıcının yanında, SONRA PATH'te arar (K13d).

    `.venv/bin/python -m pytest` çağrısı PATH'e `.venv/bin` EKLEMEZ (ölçüldü 2026-09-08): salt
    `shutil.which` kullanıldığında çivi her zaman `~/.local/bin`teki bağımsız `uv tool`
    kopyasını koşuyordu — yani pyproject/uv.lock'un PİNLEDİĞİ sürüm (`ansible-core>=2.17,<2.19`)
    değil, operatörün ayrıca kurduğu ikinci bir kopya doğruluyordu (iki kaynak, tek gerçek).
    Bulunamazsa `pytest.fail`: "koşamıyorum" ile "kırmızı" bu çivide bilerek AYIRT EDİLMEZ.
    """
    yanindaki = pathlib.Path(sys.executable).parent / ad
    if yanindaki.is_file():
        return str(yanindaki)
    yoldaki = shutil.which(ad)
    if yoldaki is None:
        pytest.fail(
            f"{ad} ne `{pathlib.Path(sys.executable).parent}` içinde ne de PATH'te bulundu. "
            'Kurulum: `uv sync` (dev grubu: ansible-core>=2.17,<2.19 + ansible-lint>=24). '
            "'koşamıyorum' bu çivi için 'kırmızı' sayılır."
        )
    return yoldaki


def _ansible_bool(a):
    """ansible-core 2.18.19 `ansible.plugins.filter.core.to_bool`un BİREBİR kopyası.

    KAYNAKTAN ALINDI, tahmin edilmedi (ölçüm 2026-09-08, uv tool ansible-core 2.18.19:
    `inspect.getsource(ansible.plugins.filter.core.to_bool)`). Kopya olmasının nedeni: ansible
    `.venv`e HENÜZ kurulu değil (Rol-1 `uv sync` yapacak) ve çivi bugün de koşmalı. Kopya
    olduğu için AYRIŞMA riski taşır — bu yüzden yalnız `| bool` süzgecinin SEMANTİĞİNİ ölçen
    testte kullanılır, davranışın kendisi playbook koşumunda gerçek süzgeçle sınanır.
    """
    if a is None or isinstance(a, bool):
        return a
    if isinstance(a, str):
        a = a.lower()
    if a in ("yes", "on", "1", "true", 1):
        return True
    return False


def _jinja_ortami() -> jinja2.Environment:
    """`when:` ifadelerini ÇÖZMEK için Jinja ortamı (ansible süzgeçlerinden yalnız gerekenler).

    Metin araması bir kapı ifadesinin YÖNÜNÜ ölçemez: `not (x | bool)` ile `(x | bool)` aynı
    dizgeleri taşır. Kapı bu yüzden Jinja ile GERÇEKTEN değerlendirilir (inceleme K2b).
    """
    ortam = jinja2.Environment(undefined=jinja2.ChainableUndefined, autoescape=False)
    ortam.filters["bool"] = _ansible_bool
    ortam.filters["basename"] = lambda p: pathlib.PurePosixPath(str(p)).name
    ortam.filters["dirname"] = lambda p: str(pathlib.PurePosixPath(str(p)).parent)
    ortam.filters["regex_replace"] = lambda s, desen, yerine="": re.sub(desen, yerine, str(s))
    return ortam


def _when_degerlendir(ifade: str, degiskenler: dict) -> bool:
    """Bir `when:` ifadesini (Jinja koşulu) verilen değişken kümesiyle değerlendirir."""
    sablon = _jinja_ortami().from_string("{{ (" + ifade + ") | bool }}")
    return sablon.render(**degiskenler) == "True"


# ---------------------------------------------------------------------------------------------
# Çivi 1 — YAML'lar açılır + ansible-playbook --syntax-check çıkış 0
# ---------------------------------------------------------------------------------------------


def test_ansible_dizini_var_ve_beklenen_dosyalari_tasir():
    """İskelet envanteri: Task 1'in üretmesi gereken dosyaların HEPSİ yerinde."""
    beklenen = [
        ANSIBLE_CFG,
        INVENTORY_INI,
        SITE_YML,
        ANSIBLE_DIZIN / "README.md",
        ROL_DIZIN / "defaults" / "main.yml",
        ROL_DIZIN / "handlers" / "main.yml",
        ROL_DIZIN / "tasks" / "main.yml",
    ]
    eksik = [str(p) for p in beklenen if not p.is_file()]
    assert not eksik, f"iskelet dosyaları eksik: {eksik}"


def test_yaml_dosyalari_safe_load_ile_acilir():
    """Çivi 1a: her `.yml` dosyası `yaml.safe_load` ile hatasız parse edilir."""
    dosyalar = _yaml_dosyalari()
    assert dosyalar, "deploy/ansible altında hiç YAML dosyası bulunamadı — iskelet eksik"
    for dosya in dosyalar:
        try:
            yaml.safe_load(dosya.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            pytest.fail(f"{dosya}: yaml.safe_load patladı: {exc}")


def test_ansible_playbook_syntax_check_gecer():
    """Çivi 1b: `ansible-playbook --syntax-check -i inventory.ini site.yml` çıkış 0.

    İkili önce `.venv/bin` (pinli sürüm), sonra PATH'te aranır — bkz. `_ansible_ikili`.
    """
    ikili = _ansible_ikili("ansible-playbook")
    sonuc = subprocess.run(
        [ikili, "--syntax-check", "-i", str(INVENTORY_INI), str(SITE_YML)],
        cwd=REPO_KOK,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert sonuc.returncode == 0, (
        f"ansible-playbook --syntax-check çıkış {sonuc.returncode}\n"
        f"--- stdout ---\n{sonuc.stdout}\n--- stderr ---\n{sonuc.stderr}"
    )


def test_ansible_cfg_depo_kokunden_yukleniyor():
    """K7: `ansible.cfg` depo KÖKÜNDE ve README'nin komut biçiminde GERÇEKTEN yükleniyor.

    Ansible yapılandırmayı `ANSIBLE_CONFIG` → `./ansible.cfg` (CWD) → `~/.ansible.cfg` →
    `/etc/ansible/ansible.cfg` sırasıyla arar; playbook'un YANINDAKİ dosyaya BAKMAZ. README'nin
    bütün komutları depo kökünden çağrıldığı için `deploy/ansible/ansible.cfg` HİÇ okunmuyordu
    (ölçüldü: `CONFIG_FILE() = None`). Bu çivi dosyanın yerini DEĞİL, YÜKLENDİĞİNİ ölçer —
    yolu düzeltip aynı hatayı başka bir dizinde tekrarlamak mümkün olmasın diye.
    """
    ikili = _ansible_ikili("ansible-config")
    sonuc = subprocess.run(
        [ikili, "dump", "--only-changed"],
        cwd=REPO_KOK,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert sonuc.returncode == 0, f"ansible-config dump çıkış {sonuc.returncode}: {sonuc.stderr}"
    eslesme = re.search(r"^CONFIG_FILE\(\)\s*=\s*(.+)$", sonuc.stdout, flags=re.MULTILINE)
    assert eslesme, f"CONFIG_FILE satırı yok:\n{sonuc.stdout}"
    yuklenen = eslesme.group(1).strip()
    assert yuklenen != "None", (
        "depo kökünden koşulan ansible HİÇBİR cfg yüklemiyor — `ansible.cfg` kökte değil "
        "(README'nin bütün komutları kökten çağrılır)"
    )
    assert pathlib.Path(yuklenen).resolve() == ANSIBLE_CFG.resolve(), (
        f"yüklenen cfg beklenenden farklı: {yuklenen!r} != {ANSIBLE_CFG}"
    )
    # Kökte cfg varken `deploy/ansible/ansible.cfg` de dursaydı iki kaynak olurdu (biri ölü,
    # ama okuyan onu canlı sanır) — tek-kaynak yasası.
    assert not (ANSIBLE_DIZIN / "ansible.cfg").exists(), (
        "deploy/ansible/ansible.cfg hâlâ duruyor: hiç yüklenmeyen ikinci bir kaynak"
    )
    # cfg'deki envanter yolu kökten çözülmeli, yoksa `-i` verilmeyen komutlar yanlış/boş
    # envanterle koşar.
    cfg_metni = ANSIBLE_CFG.read_text(encoding="utf-8")
    envanter = re.search(r"^\s*inventory\s*=\s*(.+)$", cfg_metni, flags=re.MULTILINE)
    assert envanter, f"{ANSIBLE_CFG}: `inventory =` satırı yok"
    assert (REPO_KOK / envanter.group(1).strip()).resolve() == INVENTORY_INI.resolve(), (
        f"cfg'deki envanter yolu kökten çözülmüyor: {envanter.group(1).strip()!r}"
    )


# ---------------------------------------------------------------------------------------------
# Çivi 2 — birim_kaynaklari / dropin_dizinleri envanteri deploy/ ağacıyla EŞİT
# ---------------------------------------------------------------------------------------------


def _gercek_birim_dosyalari() -> set[pathlib.Path]:
    """deploy/ altında (recursive) HER `*.service`/`*.timer`, bilinen ölüler HARİÇ."""
    bulunan = {p.resolve() for p in DEPLOY_DIZIN.rglob("*.service")}
    bulunan |= {p.resolve() for p in DEPLOY_DIZIN.rglob("*.timer")}
    return bulunan - OLU_BIRIM_DOSYALARI


def _glob_kapsami(desenler: list[str]) -> set[pathlib.Path]:
    kapsam: set[pathlib.Path] = set()
    for desen in desenler:
        cozulen = desen.replace("{{ playbook_dir }}", str(ANSIBLE_DIZIN))
        eslesenler = glob.glob(cozulen)
        assert eslesenler, f"glob deseni HİÇ eşleşmedi (bozuk yol?): {desen!r} -> {cozulen!r}"
        kapsam |= {pathlib.Path(y).resolve() for y in eslesenler}
    return kapsam


def test_birim_kaynaklari_deploy_agacini_tam_kapsar():
    """Çivi 2a: `birim_kaynaklari` glob'ları deploy/ altındaki HER `*.service`/`*.timer`'ı kapsar.

    Kümeler EŞİT olmalı: EKSİK → rol bir birimi hiç kopyalamaz (dagit `[1c]`'nin miras aldığı kör
    nokta — .timer/hindsight — burada TEKRARLANMAMALI); FAZLA → glob var-olmayan/yanlış bir yolu
    işaret ediyor demektir (sessiz ayrışma, tek-kaynak yasası).
    """
    desenler = _defaults_veri()["birim_kaynaklari"]
    kapsam = _glob_kapsami(desenler)
    gercek = _gercek_birim_dosyalari()
    eksik = gercek - kapsam
    fazla = kapsam - gercek
    assert not eksik, f"birim_kaynaklari EKSİK bırakıyor (kopyalanmayacak birim): {sorted(map(str, eksik))}"
    assert not fazla, f"birim_kaynaklari FAZLADAN kapsıyor (glob yanlış hedefte): {sorted(map(str, fazla))}"


def _gercek_dropin_dizinleri() -> set[str]:
    """deploy/ altında `*.service.d` olup en az bir `*.conf` içeren HER dizin (basename kümesi)."""
    isimler: set[str] = set()
    for yol in DEPLOY_DIZIN.rglob("*.service.d"):
        if yol.is_dir() and any(yol.glob("*.conf")):
            isimler.add(yol.name)
    return isimler


def test_dropin_dizinleri_deploy_agacini_tam_kapsar():
    """Çivi 2b: `dropin_dizinleri` deploy/ altındaki her `*.service.d/*.conf`'u (basename) kapsar."""
    beyan = set(_defaults_veri()["dropin_dizinleri"])
    gercek = _gercek_dropin_dizinleri()
    assert beyan == gercek, (
        f"dropin_dizinleri gerçek drop-in dizinleriyle AYRIŞTI.\n"
        f"eksik (beyanda yok, gerçekte var): {sorted(gercek - beyan)}\n"
        f"fazla (beyanda var, gerçekte yok/boş): {sorted(beyan - gercek)}"
    )


# ---------------------------------------------------------------------------------------------
# Çivi 3 — YAML gövdesinde yasak desen yok + uzun ömürlü birimler restart edilmiyor
# ---------------------------------------------------------------------------------------------

_YASAK_METIN_DESENLERI = {
    "openssl rand": re.compile(r"openssl\s+rand"),
    ".j2 şablonu": re.compile(r"\.j2\b"),
}

# Yasa 4 kaçışının YAML'daki bütün yazımları. Metin regex'i (`failed_when\s*:\s*false`) tırnaklı
# biçimi (`failed_when: "false"`) KAÇIRIYORDU (inceleme K13c, mutasyon M21 ile ölçüldü) — bu
# yüzden değer artık PARSE EDİLİP kıyaslanır: bool False de, dizge 'false'/'no'/'0' da kırmızıdır.
_YALANCI_DEGERLER = {"false", "no", "n", "off", "0"}

# Plan Global Constraints: "playbook YAML'ında `openssl rand`, `read`, `content:` ile sır adı
# geçen görev YOK". `content:` bir MODÜL ARGÜMANI olarak yasaktır (sır değerini satır içi yazmanın
# ve `.j2` olmadan içerik kopyası üretmenin yolu); `read` kabuk komutlarında yasaktır (bir sırrı
# dosyadan okuyup değişkene almanın klasik biçimi).
_KOMUT_MODULLERI = ("command", "shell", "ansible.builtin.command", "ansible.builtin.shell")


def _komut_metinleri(args: dict) -> list[str]:
    parcalar: list[str] = []
    for anahtar in ("cmd", "_raw_params", "argv"):
        deger = args.get(anahtar)
        if isinstance(deger, str):
            parcalar.append(deger)
        elif isinstance(deger, list):
            parcalar.extend(str(x) for x in deger)
    return parcalar


def test_yaml_govdesinde_yasak_desenler_yok():
    """Çivi 3a (TUR 2): yasak desenler METİN değil YAML PARSE ile ölçülür.

    Global Constraints iki ayrı yasak taşıyor: Yasa 4 (`ignore_errors`, `failed_when: false`) ve
    sır-üretmez ilkesi (`openssl rand`, `read`, `content:`, `.j2`). Metin araması ilkini tırnak
    yüzünden kaçırıyordu ve son ikisi hiç yazılmamıştı.
    """
    ihlaller: list[str] = []
    for dosya in _yaml_dosyalari():
        govde = _yaml_govde_yorumsuz(dosya)
        for etiket, desen in _YASAK_METIN_DESENLERI.items():
            eslesme = desen.search(govde)
            if eslesme:
                ihlaller.append(f"{dosya}: {etiket} → {eslesme.group(0)!r}")
        veri = yaml.safe_load(dosya.read_text(encoding="utf-8"))
        if veri is None:
            continue
        for dugum in _tum_dugumler(veri):
            if "ignore_errors" in dugum:
                ihlaller.append(f"{dosya}: `ignore_errors` YASAK (Yasa 4) → {dugum['ignore_errors']!r}")
            if "failed_when" in dugum:
                deger = dugum["failed_when"]
                yalanci = deger is False or (
                    isinstance(deger, str) and deger.strip().lower() in _YALANCI_DEGERLER
                )
                if yalanci:
                    ihlaller.append(f"{dosya}: `failed_when` sessiz-yutma değeri → {deger!r}")
            if "content" in dugum:
                ihlaller.append(f"{dosya}: modül argümanı `content:` YASAK (satır içi içerik/sır)")
            for modul in _KOMUT_MODULLERI:
                args = dugum.get(modul)
                if isinstance(args, dict):
                    for metin in _komut_metinleri(args):
                        if re.search(r"\bread\b", metin):
                            ihlaller.append(f"{dosya}: kabuk `read` deseni → {metin!r}")
                elif isinstance(args, str) and re.search(r"\bread\b", args):
                    ihlaller.append(f"{dosya}: kabuk `read` deseni → {args!r}")
    assert not ihlaller, "yasak desen(ler):\n" + "\n".join(ihlaller)


def _dongu_ogeleri(gorev: dict, defaults: dict):
    """Bir görevin `loop`/`with_*` ifadesini defaults'tan ÇÖZER; çözemezse None."""
    for anahtar in ("loop", "with_items", "with_list", "with_fileglob"):
        if anahtar not in gorev:
            continue
        ham = gorev[anahtar]
        if isinstance(ham, list):
            return list(ham)
        eslesme = re.fullmatch(r"\s*\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}\s*", str(ham))
        if eslesme and eslesme.group(1) in defaults:
            return list(defaults[eslesme.group(1)])
        return None
    return None


def test_uzun_omurlu_birimler_restart_edilmiyor():
    """Çivi 3b (TUR 2): restart yasağı ŞABLONLU adlarda da ölçülür.

    ESKİ HÂLİ KÖRDÜ (inceleme K6/K11, ölçüldü): `name: "{{ item }}"` hiçbir zaman literal birim
    adına eşit olmadığı için Task 2 teslim edildikten sonra da 0 düğüm eşleşiyordu — yani çivi
    "doğru sebeple" değil, rolün o an literal ad kullanmaması sayesinde yeşildi. Artık `loop`/
    `with_*` ifadeleri `defaults/main.yml`ten ÇÖZÜLÜR ve tarama `tasks/*.yml` + `handlers/
    main.yml` + `site.yml`in tamamını gezer.

    ÇÖZÜLEMEYEN ŞABLON = KIRMIZI: bir systemd görevinin adı şablonluysa ve döngüsü değişken
    kaynaklarından çözülemiyorsa çivi ölçemediğini SÖYLER (sessizce atlamaz — kör çivi yasağı).

    TSK-176 Faz A1 Task 2 (2026-09-08) — İKİ DÜZELTME, ikisi de çiviyi GÜÇLENDİRİR:

      (a) DEĞİŞKEN KAYNAĞI GENİŞLEDİ. `deploy/ansible/dagit.yml` döngülerini
          `vars/dagit_vars.yml`den okur (`birim_adaylari`); yalnız rol defaults'una bakan eski
          çözücü onu ÇÖZEMİYOR ve çivi "ölçemedim" ile kırmızı oluyordu — yani yeni bir
          playbook doğduğu gün çivi hedefini değil kendini kırıyordu.

      (b) BİRİM ADI NORMALİZE EDİLİYOR. `birim_adaylari` birimleri UZANTISIZ yazar
          (`meridian`), `UZUN_OMURLU_BIRIMLER` ise `.service` uzantılıdır. Normalize edilmeden
          kesişim HER ZAMAN boş çıkardı: çivi yeşil kalır ama YANLIŞ SEBEPLE — tam da bu
          dosyanın TUR 2'de kapattığı sahte-yeşil sınıfı (K6/K11). systemd'de uzantısız ad
          `.service` demektir; kıyas da o sözlükle yapılır.

    (b) doğrudan (c)'yi gerektirir: `dagit.yml` BAKIM PENCERESİDİR ve `[4]` adımında bu
    birimleri DURDURUP BAŞLATMAK onun İŞİdir (README: "Restart kararı bakım penceresi/dagit'e
    aittir"). Bu çivi A0 ROLÜNÜ ölçer; `dagit.yml`in stop/start yüzeyi
    `tests/test_ansible_dagit_v452.py` B3 çivisiyle DAHA DAR ölçülür (yalnız `birim_adaylari`,
    şablon ÇÖZÜLEREK). Dışlama YALNIZ BU çividedir — yasak-desen taraması (Çivi 3a:
    `ignore_errors` · `failed_when: false` · `content:` · `.j2`) `dagit.yml`i AYNEN kapsar.
    """
    degiskenler = _cozum_degiskenleri()
    ortam = _jinja_ortami()
    bulunanlar: list[str] = []
    olculemeyenler: list[str] = []
    for dosya in _yaml_dosyalari():
        if dosya.resolve().relative_to(REPO_KOK).as_posix() in RESTART_TARAMASI_DISI:
            continue
        veri = yaml.safe_load(dosya.read_text(encoding="utf-8"))
        if veri is None:
            continue
        for dugum in _tum_dugumler(veri):
            for anahtar in SYSTEMD_MODUL_ANAHTARLARI:
                modul_args = dugum.get(anahtar)
                if not isinstance(modul_args, dict):
                    continue
                ham_ad = modul_args.get("name") or modul_args.get("unit")
                durum = modul_args.get("state")
                if ham_ad is None:
                    continue
                ham_ad = str(ham_ad)
                if "{{" not in ham_ad:
                    adlar = {ham_ad}
                else:
                    ogeler = _dongu_ogeleri(dugum, degiskenler)
                    if ogeler is None:
                        olculemeyenler.append(f"{dosya}: name={ham_ad!r} — döngü çözülemedi")
                        continue
                    adlar = {ortam.from_string(ham_ad).render(item=o) for o in ogeler}
                adlar = {a if "." in a else f"{a}.service" for a in adlar}
                kesisim = adlar & UZUN_OMURLU_BIRIMLER
                if kesisim and durum in ("restarted", "started"):
                    bulunanlar.append(
                        f"{dosya}: {anahtar} name={ham_ad!r} → {sorted(kesisim)} state={durum}"
                    )
    assert not olculemeyenler, "çivi ölçemedi (kör kalmasın): " + "; ".join(olculemeyenler)
    assert not bulunanlar, "uzun ömürlü birim restart/start ediliyor: " + "; ".join(bulunanlar)


# ---------------------------------------------------------------------------------------------
# Çivi 4 — ansible-lint (production) temiz
# ---------------------------------------------------------------------------------------------


def test_ansible_lint_config_production_profilini_beyan_eder():
    """Repo-kökü `.ansible-lint`: `profile: production` — Çivi 4'ün sözleşmesi burada YAZILI.

    `ansible-lint` config dosyasını CWD'den YUKARI arar (target dizinden DEĞİL — ölçüldü:
    ansiblelint.cli.get_config_path `project_path or os.getcwd()`); `deploy/ansible/.ansible-lint`
    komut `ansible-lint deploy/ansible` repo KÖKÜNDEN çağrıldığında hiç BULUNMAZ. Bu yüzden config
    depo KÖKÜNDE — konum kendisi bir tuzak olduğu için burada ayrıca ölçülüyor.
    """
    config_yolu = REPO_KOK / ".ansible-lint"
    assert config_yolu.is_file(), f"{config_yolu} yok — ansible-lint 'production' profiline DÜŞMEZ"
    veri = yaml.safe_load(config_yolu.read_text(encoding="utf-8"))
    assert veri.get("profile") == "production", f"{config_yolu}: profile production DEĞİL: {veri.get('profile')!r}"


def test_ansible_lint_production_temiz():
    """Çivi 4: `ansible-lint deploy/ansible` (repo kökünden, Ops sözleşmesi komutunun AYNISI) temiz.

    İkili bulunamazsa pytest.fail (CLAUDE.md §6 — bkz. syntax-check testinin gerekçesi).
    """
    ikili = _ansible_ikili("ansible-lint")
    sonuc = subprocess.run(
        [ikili, "deploy/ansible"],
        cwd=REPO_KOK,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert sonuc.returncode == 0, (
        f"ansible-lint çıkış {sonuc.returncode} (production profili temiz DEĞİL)\n"
        f"--- stdout ---\n{sonuc.stdout}\n--- stderr ---\n{sonuc.stderr}"
    )


# =============================================================================================
# TASK 2 EKLERİ (2026-09-08) — görev dosyaları: paketler · dizinler · venv · birimler ·
# drop-in'ler · polkit · hermes · denetim.
#
# KAPSAM: plan `docs/superpowers/plans/2026-09-08-ansible-a0.md` Task 2 çivileri (a)-(e) + Rol-1
# hükümleri 1/3/4/5/6. Yukarıdaki Task 1 çivileri DEĞİŞMEDEN kalır ve artık gerçek görevleri
# ölçer: `test_uzun_omurlu_birimler_restart_edilmiyor` Task 1'de BOŞ kümede geçiyordu, Task 2'nin
# `birimler.yml`i geldiği için bugün 7 birim × gerçek systemd görevleri üzerinde koşuyor.
#
# TEK-KAYNAK: bu çivilerin hiçbiri birim/dosya adlarını KENDİ İÇİNDE yeniden listelemez (üç
# kadans birimi ve iki handler kimliği hariç — onlar plan/hüküm metninde SABİT olarak verilmiş
# sözleşmelerdir); geri kalan her şey `defaults/main.yml` ve `deploy/` ağacından TÜRETİLİR.
# =============================================================================================

TASKS_DIZIN = ROL_DIZIN / "tasks"
HANDLERS_YML = ROL_DIZIN / "handlers" / "main.yml"
TASKS_MAIN_YML = TASKS_DIZIN / "main.yml"

# Görev zinciri SIRASI sözleşmedir (tasks/main.yml başlığındaki gerekçe): venv birimlerden ÖNCE
# (ExecStart .venv'e bakar), SIR DENETİMİ drop-in'lerden ÖNCE (K1: `LoadCredential=` kaynağı
# yoksa credential drop-in'i meridian.service'i BAŞLATILAMAZ hâle getirir), sağlık EN SONDA.
GOREV_SIRASI = [
    "paketler.yml",
    "dizinler.yml",
    "venv.yml",
    "birimler.yml",
    "sir_denetimi.yml",
    "dropinler.yml",
    "polkit.yml",
    "hermes.yml",
    "saglik.yml",
]

# Plan Task 2 + Rol-1 hükmü 4: kadans kapısı TAM olarak bu üç birim içindir.
KADANS_BIRIMLERI = ["meridian-brifing", "meridian-bekci", "meridian-karne"]

# Rol-1 hükmü 5: handlers'ta YALNIZ bu iki bildirim kimliği olabilir.
HANDLER_KIMLIKLERI = {"daemon-reload", "polkit-yeniden-baslat"}

UV_NOBETCI_DEGER = "OLCULECEK"


def _gorevler(dosya: pathlib.Path) -> list[dict]:
    """Bir görev/handler dosyasını liste olarak açar (boş dosya = çivi kırmızı)."""
    veri = yaml.safe_load(dosya.read_text(encoding="utf-8"))
    assert isinstance(veri, list) and veri, f"{dosya}: görev listesi boş ya da liste değil"
    return veri


def _modullu(gorevler: list[dict], modul: str) -> list[dict]:
    return [g for g in gorevler if modul in g]


def _tek(gorevler: list[dict], aciklama: str) -> dict:
    assert len(gorevler) == 1, f"{aciklama}: beklenen 1 görev, bulunan {len(gorevler)}"
    return gorevler[0]


# ---------------------------------------------------------------------------------------------
# Görev zinciri
# ---------------------------------------------------------------------------------------------


def test_gorev_zinciri_tam_ve_sirali():
    """`tasks/main.yml` sekiz görev dosyasını SIRAYLA import eder ve hepsi diskte vardır.

    Sıra süs değil sözleşmedir: `venv` `birimler`den önce gelmezse enable edilen birim ilk
    atışta 203/EXEC ile düşer; `denetim` sonda değilse "kurulum bitti" hükmü kanıtsız kalır.
    """
    gorevler = _gorevler(TASKS_MAIN_YML)
    import_edilen = [g.get("ansible.builtin.import_tasks") for g in gorevler]
    assert import_edilen == GOREV_SIRASI, (
        f"görev zinciri beklenen sıradan ayrıştı.\nbeklenen: {GOREV_SIRASI}\nbulunan : {import_edilen}"
    )
    eksik = [ad for ad in GOREV_SIRASI if not (TASKS_DIZIN / ad).is_file()]
    assert not eksik, f"import edilen ama diskte olmayan görev dosyaları: {eksik}"


# ---------------------------------------------------------------------------------------------
# Çivi (a) + Rol-1 hükmü 4 — kadans kapısı
# ---------------------------------------------------------------------------------------------


def test_kadans_birimleri_defaultsta_uc_tane():
    """`kadans_birimleri` TAM olarak brifing/bekçi/karne (deploy.sh 6c-e/11a-c üçlüsü)."""
    assert _defaults_veri()["kadans_birimleri"] == KADANS_BIRIMLERI


def test_kadans_kapisi_is_enabled_ile_olculur():
    """Rol-1 hükmü 4: kapı `systemctl is-enabled <ad>.timer` ile ÖLÇÜLÜR.

    `service_facts` timer'ları vermeyebilir; ölçemediğimiz bir fact'e dayanan kapı sessizce
    hep-açık ya da hep-kapalı olurdu. Ayrıca `changed_when: false` (okuma değiştirmez) ve
    `failed_when` ELLE (rc tabanlı) yazılmış olmalı — `failed_when: false`/`ignore_errors`
    Yasa 4 gereği yasak (Çivi 3a bunu ayrıca tüm dosyalarda tarar).
    """
    gorevler = _gorevler(TASKS_DIZIN / "birimler.yml")
    olcum = _tek(
        [
            g
            for g in _modullu(gorevler, "ansible.builtin.command")
            if "is-enabled" in str(g["ansible.builtin.command"].get("cmd", ""))
        ],
        "birimler.yml: `systemctl is-enabled` ölçüm görevi",
    )
    assert olcum.get("loop") == "{{ kadans_birimleri }}", (
        f"ölçüm görevi `kadans_birimleri` üzerinde dönmüyor: {olcum.get('loop')!r} "
        "(üç birimden biri sessizce kapının dışında kalırdı)"
    )
    assert ".timer" in str(olcum["ansible.builtin.command"]["cmd"]), "kapı TIMER durumuna bakmalı"
    assert olcum.get("changed_when") is False, "okuma görevi `changed_when: false` taşımalı"
    failed_when = str(olcum.get("failed_when", ""))
    assert "rc" in failed_when and "not in" in failed_when, (
        f"failed_when rc tabanlı elle yazılmamış: {failed_when!r}"
    )
    assert "ignore_errors" not in olcum, "ignore_errors YASAK (Yasa 4)"


def _kapi_ifadesi_saglam(when_ifadesi: str) -> bool:
    """Kapı ifadesi üç şeyi de okumalı: birim listesi, devir bayrağı, ölçüm haritası."""
    return all(
        anahtar in when_ifadesi
        for anahtar in ("kadans_birimleri", "brifing_devri", "kadans_etkin")
    )


def test_kadans_kapisi_kopyalama_ve_enable_gorevlerinde_var():
    """Çivi (a): hem birim dosyası KOPYASI hem timer ENABLE'ı kapıya tabidir.

    İkisi ayrı eylemdir (deploy.sh 6c-e dosyayı, 11a-c kadansı korur) ve biri kapısız kalırsa
    ilgisiz bir sebeple koşan tek bir dağıtım, kimsenin karar vermediği bir Telegram teslimatını
    değiştirir ya da açar. Kapı ifadesi üç birimi ADIYLA saymaz, `kadans_birimleri`'ni OKUR —
    tek kaynak; listenin kendisi bir üstteki çivide sabitlenmiştir.
    """
    gorevler = _gorevler(TASKS_DIZIN / "birimler.yml")
    kopya = _tek(
        [g for g in _modullu(gorevler, "ansible.builtin.copy") if "with_fileglob" in g],
        "birimler.yml: glob'dan birim kopyalama görevi",
    )
    assert _kapi_ifadesi_saglam(str(kopya.get("when", ""))), (
        f"birim kopyalama görevinde kadans kapısı eksik: when={kopya.get('when')!r}"
    )
    timerlar = _tek(
        [
            g
            for g in _modullu(gorevler, "ansible.builtin.systemd_service")
            if g["ansible.builtin.systemd_service"].get("state") == "started"
        ],
        "birimler.yml: timer enable+started görevi",
    )
    assert timerlar.get("loop") == "{{ etkin_timerlar }}"
    assert _kapi_ifadesi_saglam(str(timerlar.get("when", ""))), (
        f"timer enable görevinde kadans kapısı eksik: when={timerlar.get('when')!r}"
    )


def test_uzun_omurlu_servis_gorevi_state_almaz():
    """F10 (TASARIM §4.4): enabled+inactive anomalisi Meridian'da bilerek DURDURULUR.

    `etkin_birimler` görevinde `state` anahtarı HİÇ olmamalı — `state: started` bile yazılırsa
    Ansible anomaliyi sessizce "düzeltir" ve F10'un yakalaması gereken durum hiç doğmaz.
    """
    gorevler = _gorevler(TASKS_DIZIN / "birimler.yml")
    servis = _tek(
        [
            g
            for g in _modullu(gorevler, "ansible.builtin.systemd_service")
            if g.get("loop") == "{{ etkin_birimler }}"
        ],
        "birimler.yml: uzun ömürlü servis enable görevi",
    )
    args = servis["ansible.builtin.systemd_service"]
    assert args.get("enabled") is True
    assert "state" not in args, f"`state` verilmiş ({args.get('state')!r}) — F10 kapısı körelir"


def test_etkin_birim_ve_timer_listeleri_deploy_agacindan_turer():
    """`etkin_birimler` + `etkin_timerlar` yalnız rolün KOPYALADIĞI birimlerden seçilebilir.

    Aksi hâlde playbook var olmayan bir birimi enable etmeye çalışır (koşumda kırmızı) ya da
    daha kötüsü: birim adı repoda yeniden adlandırılınca liste sessizce bayatlar.
    """
    defaults = _defaults_veri()
    kapsanan = {p.name for p in _glob_kapsami(defaults["birim_kaynaklari"])}
    for anahtar in ("etkin_birimler", "etkin_timerlar"):
        beyan = set(defaults[anahtar])
        fazla = beyan - kapsanan
        assert not fazla, f"{anahtar}: rolün kopyalamadığı birim(ler) enable ediliyor: {sorted(fazla)}"


# ---------------------------------------------------------------------------------------------
# Çivi (b) + Rol-1 hükmü 3 — uv sürüm pini
# ---------------------------------------------------------------------------------------------


def test_venv_ilk_gorev_uv_surum_kapisidir():
    """Rol-1 hükmü 3: `uv_surum` nöbetçi değerdeyken playbook DURUR.

    Sürümsüz installer URL'si her koşumda başka bir uv kurabilir (A0 envanteri Bulgu 5: tedarik
    kapısı yok). Ajan A1'e ssh yapamaz, uydurma yasağı tahmini de yasaklar — bu yüzden değer
    "ölçülmedi" işaretiyle doğar ve kapı onu canlıya geçirmez.
    """
    gorevler = _gorevler(TASKS_DIZIN / "venv.yml")
    ilk = gorevler[0]
    assert "ansible.builtin.assert" in ilk, f"venv.yml ilk görevi assert değil: {list(ilk)}"
    kosullar = " ".join(str(k) for k in ilk["ansible.builtin.assert"]["that"])
    assert "uv_surum" in kosullar and UV_NOBETCI_DEGER in kosullar, (
        f"nöbetçi değer kapısı yok: {kosullar!r}"
    )
    fail_msg = str(ilk["ansible.builtin.assert"].get("fail_msg", ""))
    assert "uv --version" in fail_msg, f"fail_msg reçeteyi vermiyor: {fail_msg!r}"


def test_uv_installer_url_surum_pinlidir():
    """Çivi (b): installer URL'si `uv_surum` taşır ve defaults'taki değer boş DEĞİL."""
    defaults = _defaults_veri()
    uv_surum = defaults["uv_surum"]
    assert isinstance(uv_surum, str) and uv_surum.strip(), "uv_surum boş bırakılamaz"
    gorevler = _gorevler(TASKS_DIZIN / "venv.yml")
    indir = _tek(_modullu(gorevler, "ansible.builtin.get_url"), "venv.yml: installer indirme görevi")
    url = str(indir["ansible.builtin.get_url"]["url"])
    assert "{{ uv_surum }}" in url, f"installer URL'si sürüm pinli değil: {url!r}"


# ---------------------------------------------------------------------------------------------
# Çivi (c) — sır dosyası denetimi
# ---------------------------------------------------------------------------------------------


def test_sir_stat_gorevi_no_log_ve_checksumsuz():
    """Çivi (c): sır dosyalarına dokunan görev `no_log: true`; içerik OKUNMAZ.

    `stat`'ın varsayılan `get_checksum: true`'su dosyayı BAŞTAN SONA okur — sır dosyasında bu,
    değeri ansible'ın bellek/log yoluna sokmaktır. Denetim yalnız metadata ister.
    """
    gorevler = _gorevler(TASKS_DIZIN / "sir_denetimi.yml")
    stat_gorevi = _tek(
        [g for g in _modullu(gorevler, "ansible.builtin.stat") if g.get("loop") == "{{ zorunlu_sir_dosyalari }}"],
        "sir_denetimi.yml: sır dosyası stat görevi",
    )
    assert stat_gorevi.get("no_log") is True, "sır dosyası görevinde `no_log: true` YOK"
    args = stat_gorevi["ansible.builtin.stat"]
    assert args.get("get_checksum") is False, "get_checksum kapatılmamış — dosya içeriği okunur"


def test_sir_kapisi_recete_veriyor():
    """Denetim düşerse operatör HANGİ betiği koşacağını okuyabilmeli (Yasa 6).

    Kapının `no_log` taşımaması BİLİNÇLİ: burada basılan yol/mod/sahip zaten `defaults`ta açık
    yazılıdır (DEĞER değildir); `no_log` koysaydık düşen assert'in tek çıktısı "output has been
    hidden" olurdu ve dosyanın hangisi olduğu ÖĞRENİLEMEZDİ.
    """
    gorevler = _gorevler(TASKS_DIZIN / "sir_denetimi.yml")
    kapi = _tek(
        [
            g
            for g in _modullu(gorevler, "ansible.builtin.assert")
            if "sir_stat" in str(g.get("loop", ""))
        ],
        "sir_denetimi.yml: sır dosyası assert kapısı",
    )
    assert kapi.get("no_log") is not True, "kapının fail_msg'i gizlenirse denetim okunamaz olur"
    fail_msg = str(kapi["ansible.builtin.assert"].get("fail_msg", ""))
    for betik in ("sir_credential_gecis.sh", "dash_token_credential.sh"):
        assert betik in fail_msg, f"fail_msg reçetesinde {betik} yok: {fail_msg!r}"


# ---------------------------------------------------------------------------------------------
# Çivi (d) — hermes: rol ikiliyi KURMAZ
# ---------------------------------------------------------------------------------------------


_INDIRME_DESENLERI = ("curl", "wget", "get_url", "pip install", "| sh", "|sh")


def test_hermes_gorevi_ikili_indirmez():
    """Çivi (d): `hermes.yml` hiçbir indirme/kurulum yolu içermez.

    deploy.sh 5 hermes'i ağdan indirdiği betiği doğrudan kabuğa borulayarak kuruyordu — sürüm
    pini yok, sha kapısı yok (A0 envanteri Bulgu 5). Rol ÖLÇER ve REÇETE basar; kurulum
    operatör kararıdır.
    """
    metin = (TASKS_DIZIN / "hermes.yml").read_text(encoding="utf-8")
    bulunan = [d for d in _INDIRME_DESENLERI if d in metin]
    assert not bulunan, f"hermes.yml indirme/kurulum deseni taşıyor: {bulunan}"


def test_hermes_ikili_olcumu_rapor_uretir():
    """Ölçüm var ve okunuyor (Yasa 6): stat + debug reçetesi."""
    gorevler = _gorevler(TASKS_DIZIN / "hermes.yml")
    assert any(
        g.get("loop") == "{{ hermes_ikili_yollari }}" for g in _modullu(gorevler, "ansible.builtin.stat")
    ), "hermes ikilisi hiç ölçülmüyor"
    assert _modullu(gorevler, "ansible.builtin.debug"), "ölçüm var ama okuyanı yok (Yasa 6)"


# ---------------------------------------------------------------------------------------------
# Çivi (e) + Rol-1 hükmü 5 — handler kümesi
# ---------------------------------------------------------------------------------------------


def test_handlerlar_yalniz_iki_tane():
    """Çivi (e): YALNIZ `daemon-reload` ve `polkit-yeniden-baslat`.

    Üçüncü bir handler eklemek, A0'ın "hiçbir uzun ömürlü servisi yeniden başlatmam" sözleşmesini
    sessizce delmenin en kolay yoludur (restart handler'ı çoğu zaman bir `notify` satırıyla
    gelir ve diff'te masum görünür). `listen` KİMLİKTİR: `notify:` satırları onu hedefler,
    `name` yalnız insan metnidir (ansible-lint `name[casing]` büyük harf ister).
    """
    handlerlar = _gorevler(HANDLERS_YML)
    assert len(handlerlar) == 2, f"handler sayısı 2 değil: {len(handlerlar)}"
    kimlikler = set()
    for h in handlerlar:
        kimlikler.add(h.get("listen") or h.get("name"))
    assert kimlikler == HANDLER_KIMLIKLERI, f"handler kimlikleri ayrıştı: {sorted(kimlikler)}"
    # Restart eden TEK handler polkit'tir (sistem servisi, kural değişikliği için şart).
    for h in handlerlar:
        args = h.get("ansible.builtin.systemd_service", {})
        if args.get("state") == "restarted":
            assert args.get("name") == "polkit", f"polkit dışında restart eden handler: {args}"


def test_notify_edilen_handlerlar_tanimlidir():
    """Tek-kaynak: her `notify:` bir handler kimliğine düşmeli (yazım hatası SESSİZ olurdu)."""
    kullanilan: set[str] = set()
    for dosya in sorted(TASKS_DIZIN.glob("*.yml")):
        for gorev in _gorevler(dosya):
            notify = gorev.get("notify")
            if isinstance(notify, str):
                kullanilan.add(notify)
            elif isinstance(notify, list):
                kullanilan.update(notify)
    assert kullanilan, "hiçbir görev handler tetiklemiyor — daemon-reload zinciri kopuk"
    assert kullanilan <= HANDLER_KIMLIKLERI, (
        f"tanımsız handler'a notify: {sorted(kullanilan - HANDLER_KIMLIKLERI)}"
    )


# ---------------------------------------------------------------------------------------------
# Rol-1 hükmü 6 — sağlık kapısı; timer'lar yalnız rapor
# ---------------------------------------------------------------------------------------------


def test_saglik_kapisi_healthz_ve_meridian_aktif():
    """Rol-1 hükmü 6: `uri healthz` + `assert meridian.service active`.

    "kurulu != çalışır": birim dosyasının yerinde olması sürecin koştuğunu kanıtlamaz.
    """
    gorevler = _gorevler(TASKS_DIZIN / "saglik.yml")
    saglik = _tek(_modullu(gorevler, "ansible.builtin.uri"), "saglik.yml: healthz görevi")
    args = saglik["ansible.builtin.uri"]
    # URL değişkenden gelir (tek kaynak: `defaults/main.yml::saglik_url`) — çivi hem göreve hem
    # değişkenin ÇÖZÜLEN değerine bakar, yoksa "healthz" dizgesi göreve elle gömülürdü.
    assert str(args["url"]) == "{{ saglik_url }}", f"sağlık URL'si defaults'tan gelmiyor: {args['url']!r}"
    assert "healthz" in str(_defaults_veri()["saglik_url"]), "saglik_url healthz ucunu göstermiyor"
    assert args.get("status_code") == 200
    assert "until" in saglik and "retries" in saglik and "delay" in saglik, "retry sözleşmesi eksik"
    aktiflik = _tek(
        [
            g
            for g in _modullu(gorevler, "ansible.builtin.assert")
            if "meridian_aktif" in str(g["ansible.builtin.assert"]["that"])
        ],
        "saglik.yml: meridian.service aktiflik kapısı",
    )
    assert "active" in str(aktiflik["ansible.builtin.assert"]["that"])


def test_timerlar_yalniz_raporlanir():
    """Rol-1 hükmü 6: timer envanteri KAPI DEĞİL, RAPOR.

    Kapalı bir kadans arıza değildir; timer listesini düşürmek yanlış alarm üretirdi.
    """
    gorevler = _gorevler(TASKS_DIZIN / "saglik.yml")
    timer_assertleri = [
        g
        for g in _modullu(gorevler, "ansible.builtin.assert")
        if "timer_envanteri" in str(g["ansible.builtin.assert"]["that"])
    ]
    assert not timer_assertleri, "timer envanteri kapıya çevrilmiş — yanlış alarm kaynağı"
    assert any(
        "timer_envanteri" in str(g["ansible.builtin.debug"].get("msg", ""))
        for g in _modullu(gorevler, "ansible.builtin.debug")
    ), "timer envanteri ölçülüyor ama okunmuyor (Yasa 6)"


# ---------------------------------------------------------------------------------------------
# Rol-1 hükmü 1 — envanter grup adı host adından AYRI
# ---------------------------------------------------------------------------------------------


def test_envanter_grup_meridian_host_a1():
    """Rol-1 hükmü 1: grup `meridian`, host `a1`; `hosts:` grubu hedefler.

    İkisi de `a1` iken ansible HER koşumda `[WARNING]: Found both group and host with same name`
    basıyordu; gürültü gerçek uyarıları gömer (bedel yasası: azaltılan gürültünün ne
    KAYBETTİRDİĞİ değil, burada tersi — eklenen gürültünün ne GİZLEDİĞİ).
    """
    metin = INVENTORY_INI.read_text(encoding="utf-8")
    gruplar = re.findall(r"^\[([^\]]+)\]", metin, flags=re.MULTILINE)
    assert gruplar == ["meridian"], f"envanter grupları beklenenden farklı: {gruplar}"
    hostlar = [
        s.split()[0]
        for s in metin.splitlines()
        if s.strip() and not s.lstrip().startswith(("#", "["))
    ]
    assert hostlar == ["a1"], f"envanter host satırları beklenenden farklı: {hostlar}"
    assert not (set(gruplar) & set(hostlar)), "grup ve host aynı adı taşıyor — uyarı geri gelir"
    site = yaml.safe_load(SITE_YML.read_text(encoding="utf-8"))
    assert site[0]["hosts"] == "meridian", f"site.yml grubu hedeflemiyor: {site[0]['hosts']!r}"


# ---------------------------------------------------------------------------------------------
# Drop-in kaynak ↔ hedef ayrışması
# ---------------------------------------------------------------------------------------------


def test_dropin_kaynaklari_hedef_dizinlerle_esit():
    """`dropin_kaynaklari` (KAYNAK glob) ile `dropin_dizinleri` (HEDEF dizin) ayrışamaz.

    Ayrışırsa rol ya boş bir `.d` dizini yaratır (hiçbir drop-in kopyalanmaz — sessiz) ya da
    var olmayan bir dizine yazmaya kalkar. `with_fileglob` ara dizinde `*` KABUL ETMEZ (fileglob
    lookup dizin adını `find_file_in_search_path` ile çözer; ölçüldü 2026-09-08) — bu yüzden
    kaynak listesi dizin başına bir desen taşır ve iki liste arasında bu çivi durur.
    """
    defaults = _defaults_veri()
    kaynak_dizinleri = {
        pathlib.PurePath(desen).parent.name for desen in defaults["dropin_kaynaklari"]
    }
    assert kaynak_dizinleri == set(defaults["dropin_dizinleri"]), (
        f"kaynak glob dizinleri ile hedef dizin listesi ayrıştı.\n"
        f"kaynakta: {sorted(kaynak_dizinleri)}\nhedefte : {sorted(defaults['dropin_dizinleri'])}"
    )
    cozulen = _glob_kapsami(defaults["dropin_kaynaklari"])
    gercek = {
        p.resolve()
        for p in DEPLOY_DIZIN.rglob("*.service.d/*.conf")
        if ANSIBLE_DIZIN not in p.parents
    }
    assert cozulen == gercek, (
        f"drop-in glob'ları deploy/ ağacıyla ayrıştı.\n"
        f"eksik: {sorted(map(str, gercek - cozulen))}\nfazla: {sorted(map(str, cozulen - gercek))}"
    )


def test_polkit_kaynaklari_gercek_dosyalar():
    """`polkit_kaynaklari` diskte GERÇEKTEN var (yolu bozuk bir kural sessizce kurulmazdı)."""
    for desen in _defaults_veri()["polkit_kaynaklari"]:
        yol = pathlib.Path(desen.replace("{{ playbook_dir }}", str(ANSIBLE_DIZIN)))
        assert yol.is_file(), f"polkit kaynağı yok: {yol}"


# =============================================================================================
# TUR 2 (2026-09-08) — çekişmeli incelemeden çıkan 14 kök. Her çivi kökün ADIYLA etiketli;
# hiçbiri birim/dosya/bayrak adını KENDİ İÇİNDE yeniden listelemez (tek-kaynak yasası):
# değerler `defaults/main.yml`, `dagit.sh`, `deploy/` ağacı ve birim dosyalarından TÜRETİLİR.
# =============================================================================================

SIR_DENETIMI_YML = TASKS_DIZIN / "sir_denetimi.yml"
SAGLIK_YML = TASKS_DIZIN / "saglik.yml"
BIRIMLER_YML = TASKS_DIZIN / "birimler.yml"
VENV_YML = TASKS_DIZIN / "venv.yml"

# systemd'nin birim/drop-in dizini ve polkit'in kural dizini — OS sabitleri, rolün tercihi değil.
SYSTEMD_BIRIM_DIZINI = "/etc/systemd/system"
POLKIT_KURAL_DIZINI = "/etc/polkit-1/rules.d"


def _yol_coz(metin: str) -> str:
    """`{{ playbook_dir }}`i gerçek dizine çevirir (site.yml'in bulunduğu dizin)."""
    return str(metin).replace("{{ playbook_dir }}", str(ANSIBLE_DIZIN))


# ---------------------------------------------------------------------------------------------
# K1 — sır denetimi credential drop-in'lerinden ÖNCE
# ---------------------------------------------------------------------------------------------


def test_sir_denetimi_dropinlerden_once_kosar():
    """K1: `LoadCredential=` drop-in'i, kaynak sır dosyası YOKKEN meridian.service'i öldürür.

    Drop-in dosyalarının kendi başlıkları bunu yazıyor: "LoadCredential= kaynak dosyası YOKSA
    systemd birimi BAŞLATMAZ" — yani sırsız bir hosta bu drop-in'leri koymak, çalışan (ya da
    çalışacak) bir servisi başlatılamaz hâle getirmektir. Bu yüzden sır DOSYASI denetimi zincirde
    `dropinler`den ÖNCE koşar; sağlık hükmü sonda kalır.
    """
    sira = [g.get("ansible.builtin.import_tasks") for g in _gorevler(TASKS_MAIN_YML)]
    assert "sir_denetimi.yml" in sira and "dropinler.yml" in sira, f"zincir eksik: {sira}"
    assert sira.index("sir_denetimi.yml") < sira.index("dropinler.yml"), (
        f"sır denetimi drop-in'lerden SONRA koşuyor — credential kapısı körelir: {sira}"
    )
    assert sira[-1] == "saglik.yml", f"sağlık hükmü sonda değil: {sira}"
    # İçerik de taşınmış olmalı: sır dosyası döngüsü gerçekten `sir_denetimi.yml`de.
    metin = SIR_DENETIMI_YML.read_text(encoding="utf-8")
    assert "zorunlu_sir_dosyalari" in metin, "sir_denetimi.yml sır listesini okumuyor"


# ---------------------------------------------------------------------------------------------
# K2 — kadans kapısı: rc=4, `| bool`, kapının YÖNÜ
# ---------------------------------------------------------------------------------------------


def test_kadans_rc_listesi_birim_yok_durumunu_kapsar():
    """K2: `systemctl is-enabled` OLMAYAN birimde rc=4 döner — bu 'etkin değil'dir, arıza değil.

    rc=4 kabul edilmezse playbook `birimler.yml`in İLK görevinde ölür: taze bir A1'de (yani
    rolün var oluş sebebi olan senaryoda) hiçbir birim kopyalanmaz ve README'nin verdiği kaçış
    yolu (`-e brifing_devri=true`) da erişilemez kalır.
    """
    olcum = _tek(
        [
            g
            for g in _modullu(_gorevler(BIRIMLER_YML), "ansible.builtin.command")
            if "is-enabled" in str(g["ansible.builtin.command"].get("cmd", ""))
        ],
        "birimler.yml: is-enabled ölçüm görevi",
    )
    failed_when = str(olcum.get("failed_when", ""))
    rc_listesi = re.search(r"\[([0-9,\s]+)\]", failed_when)
    assert rc_listesi, f"failed_when rc listesi okunamadı: {failed_when!r}"
    kabul = {int(x) for x in rc_listesi.group(1).replace(" ", "").split(",") if x}
    assert {0, 1, 4} <= kabul, f"rc kabul kümesi 'birim yok' (4) durumunu kapsamıyor: {sorted(kabul)}"


def test_brifing_devri_her_kullanimda_bool_suzgeci_tasir():
    """K2: `-e brifing_devri=false` ansible'da DİZGEdir ve boş-olmayan dizge TRUTHY'dir.

    Ölçülmüş sonuç (inceleme): bayrak `false` verildiğinde kapı AÇILIYORDU — operatör kapıyı
    kapalı tutmak için yazdığı komutla tam tersini yapıyordu. `| bool` süzgeci defaults'taki
    gerçek bool değeri etkilemez, dizgeyi doğru çevirir.
    """
    ihlaller: list[str] = []
    olculen = 0
    # Yalnız DEĞERLENDİRİLEN alanlar taranır: `debug.msg` içindeki düzyazı ("Devretmek için:
    # -e brifing_devri=true") bir ifade değil, belgedir — orada süzgeç aramak yanlış alarmdır.
    for dosya in sorted(TASKS_DIZIN.glob("*.yml")) + [SITE_YML]:
        veri = yaml.safe_load(dosya.read_text(encoding="utf-8"))
        if veri is None:
            continue
        for dugum in _tum_dugumler(veri):
            ifadeler: list[str] = []
            for anahtar in ("when", "failed_when", "changed_when", "until"):
                deger = dugum.get(anahtar)
                if isinstance(deger, str):
                    ifadeler.append(deger)
                elif isinstance(deger, list):
                    ifadeler.extend(str(x) for x in deger)
            for modul in ("set_fact", "ansible.builtin.set_fact", "assert", "ansible.builtin.assert"):
                args = dugum.get(modul)
                if isinstance(args, dict):
                    for deger in args.values():
                        if isinstance(deger, list):
                            ifadeler.extend(str(x) for x in deger)
                        else:
                            ifadeler.append(str(deger))
            for ifade in ifadeler:
                if "brifing_devri" not in ifade:
                    continue
                for eslesme in re.finditer(r"brifing_devri\s*(\|\s*bool)?", ifade):
                    olculen += 1
                    if eslesme.group(1) is None:
                        ihlaller.append(f"{dosya.name}: {ifade.strip()!r}")
    assert olculen >= 3, f"çivi yalnız {olculen} kullanım ölçebildi — kör kalmasın"
    assert not ihlaller, "`brifing_devri` `| bool` süzgeci olmadan kullanılıyor:\n" + "\n".join(ihlaller)


def test_kadans_kapisi_yonu_senaryo_tablosuyla_olculur():
    """K2b: kapının YÖNÜ ölçülür — ifade tersine çevrilirse çivi kırmızı olur.

    Metin araması bir kapıyı yalnız "üç adı da anıyor mu" diye yoklar; `not (x)` ile `(x)` aynı
    adları taşır. Bu yüzden `when:` ifadesi GERÇEKTEN değerlendirilir. Senaryo tablosu
    (timer durumu, `-e brifing_devri` değeri) → beklenen karar:
        ('enabled',  'false') → True   (kadans zaten açık: dosya kurulur)
        ('disabled', 'false') → False  (kapalı kadans korunur)
        ('',         'false') → False  (ölçülemedi: fail-closed)
        ('disabled', 'true')  → True   (operatör bilerek devretti)
    """
    defaults = _defaults_veri()
    kadans = defaults["kadans_birimleri"]
    gorevler = _gorevler(BIRIMLER_YML)
    kapili = [
        g
        for g in gorevler
        if isinstance(g.get("when"), str) and "kadans_etkin" in g["when"] and "brifing_devri" in g["when"]
    ]
    assert len(kapili) >= 2, f"kadans kapılı görev sayısı beklenenden az: {len(kapili)}"
    senaryolar = [("enabled", "false", True), ("disabled", "false", False), ("", "false", False), ("disabled", "true", True)]
    for gorev in kapili:
        ifade = gorev["when"]
        for durum, bayrak, beklenen in senaryolar:
            degiskenler = {
                "kadans_birimleri": kadans,
                "brifing_devri": bayrak,
                "kadans_etkin": {kadans[0]: durum},
                "birim_adi": kadans[0],
                "item": kadans[0] + ".timer",
            }
            olculen = _when_degerlendir(ifade, degiskenler)
            assert olculen is beklenen, (
                f"{gorev.get('name')!r}: ({durum!r}, brifing_devri={bayrak!r}) → {olculen}, "
                f"beklenen {beklenen}. İfade: {ifade!r}"
            )
    # Kapının ölçüm haritasını gerçekten okuduğunu göster: harita boşken kapı KAPALI olmalı.
    for gorev in kapili:
        assert not _when_degerlendir(
            gorev["when"],
            {"kadans_birimleri": kadans, "brifing_devri": False, "kadans_etkin": {}, "birim_adi": kadans[0], "item": kadans[0]},
        ), f"{gorev.get('name')!r}: ölçüm YOKKEN kapı açık (fail-open)"


def test_kadans_olcumu_devir_bayraginda_atlanir():
    """K2: devir bayrağı verildiğinde ölçüm hiç gerekmez — ve gerekmediği ADIYLA yazılıdır.

    Ölçüm görevi koşulsuzken, birimlerin hiç kurulmadığı bir hostta `-e brifing_devri=true`
    kaçış yolu ölçüm görevinin arkasında kalıyordu.
    """
    olcum = _tek(
        [
            g
            for g in _modullu(_gorevler(BIRIMLER_YML), "ansible.builtin.command")
            if "is-enabled" in str(g["ansible.builtin.command"].get("cmd", ""))
        ],
        "birimler.yml: is-enabled ölçüm görevi",
    )
    when = str(olcum.get("when", ""))
    assert "brifing_devri" in when and "not" in when, (
        f"ölçüm görevi devir bayrağına bakmıyor: when={when!r}"
    )
    assert not _when_degerlendir(when, {"brifing_devri": "true"}), "devir açıkken ölçüm yine koşuyor"
    assert _when_degerlendir(when, {"brifing_devri": False}), "devir kapalıyken ölçüm atlanıyor"
    # Ölçüm atlanınca harita üretimi de patlamamalı: set_fact `default([])` ile korunmuş olmalı.
    harita = _tek(_modullu(_gorevler(BIRIMLER_YML), "ansible.builtin.set_fact"), "birimler.yml: kadans haritası")
    ifade = " ".join(str(v) for v in harita["ansible.builtin.set_fact"].values())
    assert "default([])" in ifade.replace(" ", ""), (
        f"ölçüm atlandığında `kadans_durum.results` tanımsızdır; harita korumasız: {ifade!r}"
    )


# ---------------------------------------------------------------------------------------------
# K3 — `uv sync` bayrağı dagit.sh ile tek kaynak
# ---------------------------------------------------------------------------------------------


def test_uv_sync_bayragi_dagit_ile_tek_kaynak():
    """K3: `uv sync --frozen` (bayraksız) DEV GRUBUNU A1'e kurar — dağıtım `[3]`ünün tersi.

    Dağıtım dev grubunu bilerek eler (karar 2026-08-01): kazanç yalnız disk değil DENETİM
    YÜZEYİdir (tedarik-zinciri kapısı yalnız canlıda koşan koda ait CVE'lerle dağıtım
    bloklayabilir). Rol aynı hostta aynı venv'i yönetiyorsa aynı bayrağı taşımalıdır.

    TAŞIMA KAYDI (TSK-176 Faz A1 Task 3, 2026-09-08): kıyasın öteki ucu dagit.sh'ın
    `SYNC_BAYRAK="--no-dev"` ataması, yani İKİNCİ bir kaynaktı ve bu çivi ayrışmayı ölçüyordu.
    dagit.sh sarmalayıcıya indi; `deploy/ansible/dagit.yml` [3] adımı bayrağı ROLÜN KENDİ
    defaults'undan (`uv_sync_bayrak`) okur. İki kaynak TEKE indi — ama iddia düşmedi, GÜÇLENDİ:
    ayrışmanın ölçüldüğü yer artık "iki değer eşit mi" değil "dağıtım gerçekten O DEĞİŞKENİ mi
    kullanıyor" sorusudur. Literal bir bayrak yazılırsa (ör. `uv sync --frozen --no-dev`) iki
    kaynak sessizce geri doğar ve bu çivi kırmızıya düşer."""
    defaults = _defaults_veri()
    bayrak = defaults["uv_sync_bayrak"]
    assert re.fullmatch(r"--[a-z0-9-]+", str(bayrak)), \
        f"`uv_sync_bayrak` bir bayrak değil: {bayrak!r}"
    dagit_yml = (REPO_KOK / "deploy" / "ansible" / "dagit.yml").read_text(encoding="utf-8")
    uc_gorevleri = [g for g in _dagit_gorevleri()
                    if "3" in _dagit_etiketleri(g)
                    and (g.get("ansible.builtin.command") or g.get("command"))]
    assert uc_gorevleri, "dagit.yml'de [3] `uv sync` görevi bulunamadı — çivi kaynağını yitirdi"
    for gorev in uc_gorevleri:
        cmd = str((gorev.get("ansible.builtin.command") or gorev.get("command")))
        assert "uv_sync_bayrak" in cmd, (
            f"dağıtımın [3] adımı bayrağı defaults'tan almıyor: {cmd!r} — literal bir bayrak "
            "ikinci kaynaktır ve rolle sessizce ayrışır")
        assert str(bayrak) not in cmd, (
            f"dağıtımın [3] adımı bayrağı LİTERAL yazıyor ({bayrak!r}): {cmd!r}")
    assert "uv_sync_bayrak" in dagit_yml, "dagit.yml `uv_sync_bayrak` değişkenini hiç anmıyor"
    sync = _tek(
        [
            g
            for g in _modullu(_gorevler(VENV_YML), "ansible.builtin.command")
            if "sync --frozen" in str(g["ansible.builtin.command"].get("cmd", ""))
        ],
        "venv.yml: uv sync görevi",
    )
    cmd = str(sync["ansible.builtin.command"]["cmd"])
    assert "{{ uv_sync_bayrak }}" in cmd, f"uv sync bayrağı defaults'tan gelmiyor: {cmd!r}"


def test_uv_sync_degisimi_raporlanir():
    """K11: `uv sync` canlı venv'i değiştirdiğinde bunu OKUYAN bir çıktı olmalı (Yasa 6).

    Rol hiçbir şeyi restart etmez; koşan `meridian`/`meridian-barsarchive` süreçleri disk
    değişmiş olsa da eski kodla devam eder (kaldırma bacağında geç import doğrudan ImportError).
    Sessiz bir `changed=1` bu ayrışmayı görünmez kılardı.
    """
    gorevler = _gorevler(VENV_YML)
    okuyanlar = [
        g
        for g in _modullu(gorevler, "ansible.builtin.debug")
        if "uv_sync" in str(g.get("when", "")) or "uv_sync" in str(g["ansible.builtin.debug"].get("msg", ""))
    ]
    assert okuyanlar, "uv sync `changed` sonucunu okuyan bir rapor yok (Yasa 6)"
    metin = " ".join(str(g["ansible.builtin.debug"].get("msg", "")) for g in okuyanlar)
    assert "VENV DEĞİŞTİ" in metin, f"rapor ne olduğunu SÖYLEMİYOR: {metin!r}"


# ---------------------------------------------------------------------------------------------
# K12 — uv installer tedarik kapısı
# ---------------------------------------------------------------------------------------------


# TUR 3 (B2): installer dizini/dest'in dünyaya-yazılabilir bir kökte olmadığı ŞABLON ÇÖZÜLEREK
# ölçülür — ham dizge `startswith("/tmp/")` kontrolü `dest`in gerçek değeri
# `"{{ uv_installer_dizini }}/uv-install-{{ uv_surum }}.sh"` olduğu için hiçbir zaman ötemiyordu
# (inceleme F tur-2, M12/M29: `uv_installer_dizini: /tmp` ve dizin modu `0777` SESSİZ kaldı).
_DUNYAYA_YAZILABILIR_KOKLER = ("/tmp", "/var/tmp", "/dev/shm")


def _yasakli_kok_altinda_mi(yol: str) -> bool:
    parcalar = pathlib.PurePosixPath(yol).parts
    for kok in _DUNYAYA_YAZILABILIR_KOKLER:
        kok_parcalar = pathlib.PurePosixPath(kok).parts
        if parcalar[: len(kok_parcalar)] == kok_parcalar:
            return True
    return False


def test_uv_installer_guvenli_indirilir():
    """K12: installer dünyaya-yazılabilir dizine, checksum'sız ve `force`suz inmez.

    `get_url` checksum verilmediğinde ve `force` varsayılan (false) iken, dest VARSA koşullu GET
    atar ve 304 dönerse DİSKTEKİ DOSYAYI KORUR (ansible-core 2.18.19 `get_url.py` kaynağından
    ölçüldü). Yani dünyaya-yazılabilir bir köke tahmin edilebilir adla inen bir installer, herhangi
    bir yerel uid'in önceden koyduğu dosyayla değiştirilebilir ve o dosya `ubuntu` olarak
    ÇALIŞTIRILIR.

    TUR 3 DÜZELTMESİ (B1+B2, inceleme F tur-2): (1) `dest` artık ŞABLON ÇÖZÜLEREK (`uv_installer_
    dizini` defaults'tan render edilerek) ölçülüyor, ham dizge araması değil — `/tmp`, `/var/tmp`,
    `/dev/shm` ve altları YASAK, `/usr/local/lib/meridian`/`/root/…` gibi kökler kabul. (2) installer
    dizini görevinin `owner`i `root`, `mode`u `0755` ya da `0700` OLMAK ZORUNDA (`0777` KIRMIZI).
    (3) `uv_installer_sha256` nöbetçisi ARTIK EŞİTLİKLE değil BİÇİMLE denetleniyor — eski hâliyle
    (`== UV_NOBETCI_DEGER`) Rol-1 A1'de ölçüp gerçek bir 64-hex değer yazdığında çivi KIRMIZI
    oluyordu (M22): niyet "sha'yı uydurma" idi, kodlanan kural yanlışlıkla "sha'yı ASLA yazma"
    olmuştu. `uv_surum` için de AYNI simetri uygulanır (nöbetçi ya da semver biçimi).
    """
    gorevler = _gorevler(VENV_YML)
    defaults = _defaults_veri()
    ortam = _jinja_ortami()

    indir = _tek(_modullu(gorevler, "ansible.builtin.get_url"), "venv.yml: installer indirme")
    args = indir["ansible.builtin.get_url"]
    dest = ortam.from_string(str(args["dest"])).render(**defaults)
    assert not _yasakli_kok_altinda_mi(dest), f"installer dünyaya-yazılabilir dizine iniyor: {dest!r}"
    assert args.get("force") is True, "force verilmemiş — 304 yolunda diskteki dosya korunur"
    checksum = str(args.get("checksum", ""))
    assert checksum.startswith("sha256:"), f"sha256 kapısı yok: {checksum!r}"

    # Installer dizini görevi: root-dışı yazılamayan bir dizine iniyor mu — İZİN tarafı da ölçülür.
    dizin_gorevi = _tek(_modullu(gorevler, "ansible.builtin.file"), "venv.yml: installer dizini görevi")
    dizin_args = dizin_gorevi["ansible.builtin.file"]
    dizin_yolu = ortam.from_string(str(dizin_args.get("path", ""))).render(**defaults)
    assert not _yasakli_kok_altinda_mi(dizin_yolu), (
        f"installer dizini dünyaya-yazılabilir kökte: {dizin_yolu!r}"
    )
    assert dizin_args.get("owner") == "root", f"installer dizini root dışı sahipli: {dizin_args.get('owner')!r}"
    dizin_mod = str(dizin_args.get("mode", ""))
    assert dizin_mod in {"0755", "0700"}, f"installer dizini modu güvenli değil (0777 KIRMIZI): {dizin_mod!r}"

    # Nöbetçi DEĞERE KİLİTLENMEZ (B1): ya ölçülmemiş işaret ya da beklenen GERÇEK biçim.
    sha = str(defaults["uv_installer_sha256"])
    assert sha == UV_NOBETCI_DEGER or re.fullmatch(r"[0-9a-f]{64}", sha), (
        "uv_installer_sha256 ne nöbetçi ne geçerli sha256 biçiminde — uydurma değer olabilir "
        f"(bulunan: {sha!r})"
    )
    surum = str(defaults["uv_surum"])
    assert surum == UV_NOBETCI_DEGER or re.fullmatch(r"\d+\.\d+\.\d+", surum), (
        f"uv_surum ne nöbetçi ne semver biçiminde — uydurma değer olabilir (bulunan: {surum!r})"
    )

    kapi = gorevler[0]
    kosullar = " ".join(str(k) for k in kapi["ansible.builtin.assert"]["that"])
    assert "uv_installer_sha256" in kosullar, f"KAPI-0 sha nöbetçisini denetlemiyor: {kosullar!r}"
    assert "uv_surum" in kosullar, f"KAPI-0 sürüm nöbetçisini denetlemiyor: {kosullar!r}"


# ---------------------------------------------------------------------------------------------
# K4 + K5 — check-mode koruması ve koşullu sağlık kapısı
# ---------------------------------------------------------------------------------------------


def test_command_registerina_dayanan_assertler_check_mode_korumali():
    """K4: `--check --diff` kuru koşumu HER ZAMAN kırmızı bitiyordu.

    `command`/`shell` check-mode'da ATLANIR ve register'da `stdout` hiç doğmaz; ona dayanan bir
    `assert` boş dizgeyle karşılaşır ve "hiç ölçülmemiş bir şey hakkında" arıza beyan eder.
    README'nin İLK ops komutu tam olarak buydu.
    """
    denetlenen = 0
    for dosya in sorted(TASKS_DIZIN.glob("*.yml")):
        gorevler = _gorevler(dosya)
        komut_registerlari = {
            g["register"]
            for g in gorevler
            if isinstance(g.get("register"), str) and any(m in g for m in _KOMUT_MODULLERI)
        }
        if not komut_registerlari:
            continue
        for gorev in _modullu(gorevler, "ansible.builtin.assert"):
            that = " ".join(str(x) for x in gorev["ansible.builtin.assert"]["that"])
            kullanilan = {r for r in komut_registerlari if re.search(rf"\b{re.escape(r)}\b", that)}
            if not kullanilan:
                continue
            denetlenen += 1
            when = str(gorev.get("when", ""))
            assert "ansible_check_mode" in when, (
                f"{dosya.name}: {gorev.get('name')!r} check-mode'da atlanan {sorted(kullanilan)} "
                f"kaydına korumasız dayanıyor (when={when!r})"
            )
    assert denetlenen >= 1, "çivi hiçbir assert ölçemedi — kör kalmasın"


def test_saglik_kapisi_beklenen_aktif_ile_kosullu():
    """K5: hiçbir servisi BAŞLATMAYAN rol, servisin `active` olmasını KOŞULSUZ şart koşamaz.

    Taze bir A1'de (rolün ilan edilmiş birincil senaryosu) birimler yalnız `enabled` edilir,
    `state` VERİLMEZ (F10 kararı) — yani meridian.service inactive kalır ve kapı, yakınsama
    tamamen başarılıyken 'failed' beyan eder; rolün bunu düzeltmesi de kısıtı gereği imkânsızdır.
    Semantik netleşti: "servis çalışıyorsa sağlıklı olmalı". `-e beklenen_aktif=false` soğuk
    kurulum/bakım koşumunun yoludur ve atlandığı ADIYLA basılır.
    """
    defaults = _defaults_veri()
    assert defaults["beklenen_aktif"] is True, "beklenen_aktif defaults'ta true olmalı"
    gorevler = _gorevler(SAGLIK_YML)
    adlar = [g.get("name") for g in gorevler]
    aktiflik_olcum = [
        i
        for i, g in enumerate(gorevler)
        if "ansible.builtin.command" in g and "is-active" in str(g["ansible.builtin.command"].get("cmd", ""))
    ]
    healthz = [i for i, g in enumerate(gorevler) if "ansible.builtin.uri" in g]
    assert aktiflik_olcum and healthz, f"saglik.yml'de is-active/healthz görevleri yok: {adlar}"
    assert aktiflik_olcum[0] < healthz[0], (
        f"`is-active` healthz'den SONRA okunuyor — kapı ölçmeden karar veriyor: {adlar}"
    )
    kapilar = [gorevler[healthz[0]]] + [
        g
        for g in _modullu(gorevler, "ansible.builtin.assert")
        if "meridian_aktif" in str(g["ansible.builtin.assert"]["that"])
    ]
    for gorev in kapilar:
        when = str(gorev.get("when", ""))
        assert "beklenen_aktif" in when, f"{gorev.get('name')!r}: kapı `beklenen_aktif`e bakmıyor ({when!r})"
        assert not _when_degerlendir(
            when, {"beklenen_aktif": "false", "ansible_check_mode": False}
        ), f"{gorev.get('name')!r}: `-e beklenen_aktif=false` kapıyı KAPATMIYOR"
        assert _when_degerlendir(
            when, {"beklenen_aktif": True, "ansible_check_mode": False}
        ), f"{gorev.get('name')!r}: varsayılan koşumda kapı hiç işlemiyor"
    raporlar = [
        g
        for g in _modullu(gorevler, "ansible.builtin.debug")
        if "beklenen_aktif" in str(g.get("when", "")) or "beklenen_aktif" in str(g["ansible.builtin.debug"].get("msg", ""))
    ]
    assert raporlar, "kapı kapalıyken ATLANDIĞINI söyleyen bir rapor yok (sessiz atlama = körlük)"


# ---------------------------------------------------------------------------------------------
# K8 — üretilen her kaydın okuyucusu var (Yasa 6)
# ---------------------------------------------------------------------------------------------

# `service_facts`/`package_facts` register KULLANMAZ, `ansible_facts` altına yazar — okuyucusu
# ayrı bir adla (services/packages) aranır.
_FACT_MODULLERI = {
    "service_facts": "services",
    "ansible.builtin.service_facts": "services",
    "package_facts": "packages",
    "ansible.builtin.package_facts": "packages",
}


def _okuyucu_metinleri(dugum: dict) -> list[str]:
    """Yasa 6 anlamında OKUYUCU alanlar: when · assert.that/fail_msg · debug.msg · set_fact · until.

    `failed_when`/`changed_when` bilerek DIŞARIDA: onlar üreten görevin kendi denetim ifadesidir,
    üretilen değeri BİRİNE göstermezler.
    """
    parcalar: list[str] = []

    def _ekle(deger):
        if isinstance(deger, str):
            parcalar.append(deger)
        elif isinstance(deger, list):
            parcalar.extend(str(x) for x in deger)
        elif deger is not None:
            parcalar.append(str(deger))

    for anahtar in ("when", "until", "loop", "with_items", "with_list"):
        _ekle(dugum.get(anahtar))
    for modul in ("assert", "ansible.builtin.assert"):
        args = dugum.get(modul)
        if isinstance(args, dict):
            for alan in ("that", "fail_msg", "success_msg"):
                _ekle(args.get(alan))
    for modul in ("debug", "ansible.builtin.debug"):
        args = dugum.get(modul)
        if isinstance(args, dict):
            for alan in ("msg", "var"):
                _ekle(args.get(alan))
    for modul in ("set_fact", "ansible.builtin.set_fact"):
        args = dugum.get(modul)
        if isinstance(args, dict):
            for deger in args.values():
                _ekle(deger)
    return parcalar


def test_uretilen_her_kaydin_okuyucusu_var():
    """K8: `register`/fact üreten HER görevin en az bir okuyucusu olmalı (Yasa 6).

    site.yml `service_facts` topluyor ve HİÇBİR görev `ansible_facts.services`i okumuyordu;
    görevin adı ("kadans kapısı + F10 anomali kapısı için fact") var olmayan iki okuyucu iddia
    ediyordu — okunmayan artefakt üretilmemişten farksızdır, üstelik yanlış iddia taşıyordu.
    """
    ureticiler: list[tuple[pathlib.Path, str]] = []
    okuyucu_metinleri: list[str] = []
    for dosya in _yaml_dosyalari():
        veri = yaml.safe_load(dosya.read_text(encoding="utf-8"))
        if veri is None:
            continue
        for dugum in _tum_dugumler(veri):
            if isinstance(dugum.get("register"), str):
                ureticiler.append((dosya, dugum["register"]))
            for modul, fact_adi in _FACT_MODULLERI.items():
                if modul in dugum:
                    ureticiler.append((dosya, fact_adi))
            for modul in ("set_fact", "ansible.builtin.set_fact"):
                args = dugum.get(modul)
                if isinstance(args, dict):
                    ureticiler.extend((dosya, ad) for ad in args)
            okuyucu_metinleri.extend(_okuyucu_metinleri(dugum))
    assert ureticiler, "hiç üretici bulunamadı — çivi kör"
    tum_okuyucu = "\n".join(okuyucu_metinleri)
    okuyucusuz = [
        f"{dosya.name}: {ad}"
        for dosya, ad in ureticiler
        if not re.search(rf"\b{re.escape(ad)}\b", tum_okuyucu)
    ]
    assert not okuyucusuz, "okuyucusu olmayan üretim (Yasa 6): " + "; ".join(sorted(set(okuyucusuz)))


# ---------------------------------------------------------------------------------------------
# K9 — yedek dizini modu birim dosyasıyla tek kaynak
# ---------------------------------------------------------------------------------------------


def test_yedek_dizini_modu_birim_chmodu_ile_esit():
    """K9: rol 0755 yapıyor, `meridian-backup.service` her koşumda `chmod 700` ile geri çekiyordu.

    İki yazar, tek dizin: kalıcı salınım. Salınım yalnız "gürültü" değil, idempotency KANITINI
    (2. koşum changed=0) çürütür ve yedek arşivinin sır disiplinini (0700) her playbook koşumunda
    geçici olarak gevşetir. Beklenen değer birim dosyasından TÜRETİLİR, teste elle yazılmaz.
    """
    birim = DEPLOY_DIZIN / "oracle-a1" / "meridian-backup.service"
    metin = birim.read_text(encoding="utf-8")
    dizin_gorevi = None
    for gorev in _gorevler(TASKS_DIZIN / "dizinler.yml"):
        args = gorev.get("ansible.builtin.file", {})
        if "backups" in str(args.get("path", "")):
            dizin_gorevi = args
    assert dizin_gorevi is not None, "dizinler.yml'de yedek dizini görevi yok"
    yol = str(dizin_gorevi["path"]).replace("{{ meridian_kullanici }}", str(_defaults_veri()["meridian_kullanici"]))
    eslesme = re.search(rf"chmod\s+([0-7]{{3,4}})\s+{re.escape(yol)}\b", metin)
    assert eslesme, f"{birim.name}: `{yol}` için chmod satırı bulunamadı (çivi kaynağını yitirdi)"
    birim_modu = eslesme.group(1).lstrip("0") or "0"
    rol_modu = str(dizin_gorevi["mode"]).lstrip("0") or "0"
    assert rol_modu == birim_modu, (
        f"yedek dizini modu ayrıştı: rol={dizin_gorevi['mode']!r} ↔ birim `chmod {eslesme.group(1)}` "
        "— her koşumda birbirini geri alan iki yazar"
    )


# ---------------------------------------------------------------------------------------------
# K10 — dagit F9 beyanı ∖ rol kapsamı = BEYANLI küme
# ---------------------------------------------------------------------------------------------


def _rol_kapsami() -> set[str]:
    """Rolün hedefe TAŞIDIĞI depo dosyalarının repo-göreli yol kümesi (glob + literal src)."""
    defaults = _defaults_veri()
    kapsam: set[pathlib.Path] = set()
    for anahtar in ("birim_kaynaklari", "dropin_kaynaklari", "polkit_kaynaklari"):
        kapsam |= _glob_kapsami(defaults[anahtar])
    for _dosya, gorev, src in _src_gorevleri():
        if "with_fileglob" in gorev:
            continue
        for yol in _src_adaylari(gorev, src, defaults):
            kapsam.add(yol.resolve())
    return {str(p.relative_to(REPO_KOK)) for p in kapsam if REPO_KOK in p.parents}


def _f9_kaynaklari() -> set[str]:
    """[F9] listesinin REPO tarafı.

    TAŞIMA KAYDI (TSK-176 Faz A1 Task 3, 2026-09-08): kaynak dagit.sh'ın `F9_LISTE` dizgesiydi ve
    bu dosya onu KENDİ regex'iyle söküyordu (dört ayrı sökücüden biri). Liste
    `deploy/ansible/vars/dagit_vars.yml`e taşındı, sökücü de v452'de TEKLEŞTİ — burada ithal
    edilir, kopyalanmaz. İddia (rolün kapsamadığı her F9 dosyası BEYANLI olmalı) aynen durur."""
    return {repo for repo, _ in _f9_ciftleri()}


def test_f9_beyani_rol_kapsami_ve_beyanli_istisnalarla_ortusur():
    """K10: rol, config'i taşınmayan birimleri ENABLE ediyordu ve bunu hiçbir yerde beyan etmiyordu.

`f9_ciftleri` "canlıya giden repo dosyaları"nın TEK KAYNAĞIdır. Rolün kapsamadığı her F9
    dosyası bir kapsam boşluğudur; boşluk YASAK değildir ama BEYANLI olmak zorundadır
    (`defaults/main.yml::f9_rol_disi` + README gerekçesi). Beyansız boşluk = bedel yasası ihlali:
    kazanç (birim dosyaları tek kaynaktan) sayıldı, kayıp (config'siz enable) sayılmadı.
    """
    f9 = _f9_kaynaklari()
    kapsam = _rol_kapsami()
    beyan = set(_defaults_veri()["f9_rol_disi"])
    acik = f9 - kapsam
    assert acik == beyan, (
        "F9 ∖ rol kapsamı beyanla ayrıştı.\n"
        f"beyansız boşluk (rol taşımıyor, listede de yok): {sorted(acik - beyan)}\n"
        f"gereksiz beyan (rol zaten taşıyor): {sorted(beyan - acik)}"
    )
    # Beyan edilen her yol GERÇEKTEN var olmalı (bayat beyan da bir kopyadır).
    eksik = [y for y in beyan if not (REPO_KOK / y).exists()]
    assert not eksik, f"f9_rol_disi'de var olmayan yol(lar): {sorted(eksik)}"


# ---------------------------------------------------------------------------------------------
# K13 — kaynak (src) varlığı ve hedef (dest) ifadeleri
# ---------------------------------------------------------------------------------------------


def _src_gorevleri():
    for dosya in sorted(TASKS_DIZIN.glob("*.yml")):
        for gorev in _gorevler(dosya):
            for args in gorev.values():
                if isinstance(args, dict) and "src" in args:
                    yield dosya, gorev, str(args["src"])


def _src_adaylari(gorev: dict, src: str, defaults: dict) -> list[pathlib.Path]:
    ortam = _jinja_ortami()
    sablon = _yol_coz(src)
    if "{{" not in sablon:
        return [pathlib.Path(sablon)]
    ogeler = _dongu_ogeleri(gorev, defaults)
    assert ogeler is not None, f"şablonlu src'nin döngüsü çözülemedi: {src!r}"

    def _oge(o):
        # Döngü öğesi sözlük olabilir (`{ ad: …, mode: … }` — hermes.yml, öğe başına mod;
        # ölçüldü 2026-09-08 A1: SOUL.md 0644, config.yaml 0600): `item.ad` şablonu için
        # sözlük olduğu gibi verilir, dizge değerleri yol-çözümünden geçer.
        if isinstance(o, dict):
            return {k: (_yol_coz(str(v)) if isinstance(v, str) else v) for k, v in o.items()}
        return _yol_coz(str(o))

    return [pathlib.Path(ortam.from_string(sablon).render(item=_oge(o))) for o in ogeler]


def test_literal_src_kaynaklari_diskte_var():
    """K13a: `with_fileglob` DIŞINDAKİ her `src:` diskte gerçekten var.

    Glob'lu kopyalar zaten Çivi 2/drop-in çivileriyle kapsanıyordu; `hermes.yml` ve
    `paketler.yml`in literal/şablonlu kaynakları ise ölçüsüzdü — bozuk bir yol ancak A1'e karşı
    GERÇEK koşumda, hem de rol paketleri/venv'i/birimleri yakınsattıktan SONRA patlıyordu
    (yarım yakınsamış host). Tek çivi, üç dosya.
    """
    defaults = _defaults_veri()
    eksik: list[str] = []
    olculen = 0
    for dosya, gorev, src in _src_gorevleri():
        if "with_fileglob" in gorev:
            continue
        for yol in _src_adaylari(gorev, src, defaults):
            olculen += 1
            if not yol.is_file():
                eksik.append(f"{dosya.name}: {gorev.get('name')!r} → {yol}")
    assert olculen >= 3, f"çivi yalnız {olculen} kaynak ölçebildi — kör kalmasın"
    assert not eksik, "diskte olmayan kaynak(lar):\n" + "\n".join(eksik)


def test_dest_ifadeleri_gercek_hedefe_cozuluyor():
    """K13b: hedef yolları ölçülür — `dest` bozulsa çiviler yeşil kalıyordu.

    Planın hedef cümlesi "rolün KOPYALADIĞI dosya kümesi == deploy/ altındaki birim kümesi"
    idi; bugüne dek yalnız KAYNAK yarısı çiviliydi. Beklenen hedefler `deploy/` ağacından +
    systemd/polkit'in sabit dizinlerinden TÜRETİLİR (teste elle liste yazılmaz).
    """
    defaults = _defaults_veri()
    ortam = _jinja_ortami()

    def _dest(dosya: pathlib.Path, secici) -> tuple[dict, str]:
        gorev = _tek([g for g in _modullu(_gorevler(dosya), "ansible.builtin.copy") if secici(g)], f"{dosya.name}: copy görevi")
        return gorev, str(gorev["ansible.builtin.copy"]["dest"])

    # Birim dosyaları → /etc/systemd/system/<basename>
    _gorev, birim_dest = _dest(BIRIMLER_YML, lambda g: "with_fileglob" in g)
    birim_kaynaklari = _glob_kapsami(defaults["birim_kaynaklari"])
    cozulen = {ortam.from_string(birim_dest).render(item=str(p)) for p in birim_kaynaklari}
    beklenen = {f"{SYSTEMD_BIRIM_DIZINI}/{p.name}" for p in birim_kaynaklari}
    assert cozulen == beklenen, f"birim hedefleri ayrıştı.\nçözülen: {sorted(cozulen)[:3]}…\nbeklenen: {sorted(beklenen)[:3]}…"

    # Drop-in'ler → /etc/systemd/system/<kaynağın .d dizini>/<basename>
    _gorev, dropin_dest = _dest(TASKS_DIZIN / "dropinler.yml", lambda g: "with_fileglob" in g)
    dropin_kaynaklari = _glob_kapsami(defaults["dropin_kaynaklari"])
    cozulen = {ortam.from_string(dropin_dest).render(item=str(p)) for p in dropin_kaynaklari}
    beklenen = {f"{SYSTEMD_BIRIM_DIZINI}/{p.parent.name}/{p.name}" for p in dropin_kaynaklari}
    assert cozulen == beklenen, (
        "drop-in hedefleri ayrıştı (hepsi tek dizine yığılıyor olabilir).\n"
        f"çözülen: {sorted(cozulen)}\nbeklenen: {sorted(beklenen)}"
    )
    uretilen_dizinler = {pathlib.PurePosixPath(y).parent.name for y in cozulen}
    assert uretilen_dizinler == set(defaults["dropin_dizinleri"]), (
        f"dest'in ürettiği dizin kümesi `dropin_dizinleri` ile ayrıştı: {sorted(uretilen_dizinler)}"
    )

    # Polkit kuralları → /etc/polkit-1/rules.d/<basename>
    _gorev, polkit_dest = _dest(TASKS_DIZIN / "polkit.yml", lambda g: True)
    polkit_kaynaklari = _glob_kapsami(defaults["polkit_kaynaklari"])
    cozulen = {ortam.from_string(polkit_dest).render(item=str(p)) for p in polkit_kaynaklari}
    beklenen = {f"{POLKIT_KURAL_DIZINI}/{p.name}" for p in polkit_kaynaklari}
    assert cozulen == beklenen, f"polkit hedefleri ayrıştı: {sorted(cozulen)}"
