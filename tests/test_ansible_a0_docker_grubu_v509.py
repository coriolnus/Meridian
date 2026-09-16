"""v509 · A0 rolü `docker` grubu üyeliği — TSK-195.

NUMARA KİMLİKTİR: `v509` bu turda ÖLÇÜLDÜ (2026-09-16): `ls tests/ | grep -oE '_v[0-9]{3}\\.py$'`
ana checkout'ta ve iki worktree'de (tsk194, tsk195) en büyük `v508` (`test_ag_kapisi_raporu_v508.py`)
veriyordu — `v509`/`v510` hiçbirinde YOK, çakışma ölçülmedi. Eşzamanlı başka bir worktree aynı
numarayı alırsa kural CLAUDE.md §2'dedir: az-çapalı taraf taşınır, kaydı dosya başlığına.

AİLE VE YER: `paketler.yml` yüzeyini ölçen çiviler ailesi — `tests/test_ansible_a0_v451.py`
(rolün tamamı) yanında, `tests/test_ansible_a0_terraform_v501.py`in EMSALİ ile AYRI dosya: o da
`paketler.yml`e eklenen yeni bir yeteneği (Terraform) kendi `vNNN` dosyasında ölçtü. Aynı desen,
aynı yöntem — ÇİVİ DOSYAYI OKUR, ANSIBLE KOŞMAZ, A1'e hiçbir bağlantı yoktur.

ÖLÇÜLEN SÖZLEŞME (TSK-195):
  (a) rol `meridian_kullanici`yı `docker` grubuna EKLEDİĞİNİ beyan eder — kullanıcı da grup da
      `defaults/main.yml`ten TÜRER, çiviye literal yazılmaz;
  (b) `append` davranışı kullanılır: mevcut ikincil gruplar EZİLMEZ (`append: false` `ubuntu`nun
      `sudo`/`adm`/… üyeliklerini tek koşumda silerdi — gerçek arıza sınıfı);
  (c) grup adı TEK KAYNAKTAN gelir: hem varlık ölçümü hem üyelik yazımı `docker_grubu`nu kullanır
      (iki literal ayrışırsa koşul hiç işlemez ve üyelik sessizce hiç yazılmazdı);
  (d) koşul ÖLÇÜLMÜŞ bir kayda dayanır (`getent`) ve YÖNÜ doğrudur: grup varken görev İŞLER,
      grup yokken ATLANIR — ifade jinja ile GERÇEKTEN değerlendirilerek ölçülür, metin eşleşmesiyle
      değil;
  (e) koşul KALICI bir sessiz atlama DEĞİLDİR: grubu yaratan `docker.io` paketi rolün kendi
      `apt_paketleri` listesindedir ve `paketler.yml` görev zincirinin İLK halkasıdır — yani gerçek
      koşumda grup üyelik görevine gelindiğinde vardır.

BİLİNEN SINIR, dürüst beyan: bu dosya üyeliğin A1'de GERÇEKTEN olduğunu ÖLÇMEZ (o soru yalnız
playbook koşumunda cevaplanır ve Rol-1'indir); ölçülen, rolün beyanı ve o beyanın davranışıdır.
"""
from __future__ import annotations

import pathlib

import jinja2
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
ROL = ROOT / "deploy/ansible/roles/meridian_a1"
PAKETLER_YML = ROL / "tasks/paketler.yml"
DEFAULTS_YML = ROL / "defaults/main.yml"

# Ansible'ın truthy yazımları — `append` için kabul edilen değerler.
_DOGRU_DEGERLER = {"true", "yes", "on", "1"}


def _yukle(p: pathlib.Path):
    return yaml.safe_load(p.read_text(encoding="utf-8"))


def _defaults() -> dict:
    return _yukle(DEFAULTS_YML)


def _gorevler() -> list[dict]:
    veri = _yukle(PAKETLER_YML)
    assert isinstance(veri, list) and veri, f"{PAKETLER_YML}: görev listesi boş ya da liste değil"
    return veri


def _modullu(modul: str) -> list[dict]:
    return [g for g in _gorevler() if modul in g]


def _tek(gorevler: list[dict], aciklama: str) -> dict:
    assert len(gorevler) == 1, f"{aciklama}: beklenen 1 görev, bulunan {len(gorevler)}"
    return gorevler[0]


def _uyelik_gorevi() -> dict:
    return _tek(_modullu("ansible.builtin.user"), "paketler.yml: grup üyeliği görevi")


def _olcum_gorevi() -> dict:
    return _tek(_modullu("ansible.builtin.getent"), "paketler.yml: grup varlığı ölçüm görevi")


def _coz(sablon: str, defaults: dict) -> str:
    ortam = jinja2.Environment(undefined=jinja2.StrictUndefined, keep_trailing_newline=True)
    return ortam.from_string(str(sablon)).render(**defaults)


def test_a_uyelik_beyani_var_ve_kullanici_grup_defaultstan_turer():
    """(a) Rol `meridian_kullanici`yı `docker_grubu`na ekler; iki değer de defaults'tan ÇÖZÜLÜR."""
    defaults = _defaults()
    assert defaults.get("docker_grubu") == "docker", (
        f"`docker_grubu` defaults'ta yok ya da `docker` değil: {defaults.get('docker_grubu')!r}"
    )
    args = _uyelik_gorevi()["ansible.builtin.user"]
    assert _coz(args.get("name", ""), defaults) == defaults["meridian_kullanici"], (
        f"üyelik görevi `meridian_kullanici`ya çözülmüyor: {args.get('name')!r}"
    )
    gruplar = [p.strip() for p in _coz(args.get("groups", ""), defaults).split(",") if p.strip()]
    assert defaults["docker_grubu"] in gruplar, (
        f"üyelik görevi `docker_grubu`nu içermiyor: {args.get('groups')!r} → {gruplar}"
    )


def test_b_append_ile_mevcut_gruplar_ezilmiyor():
    """(b) `append` truthy OLMALI.

    Modül varsayılanı `false`'tur ve `false` kullanıcının ikincil grup kümesini VERİLEN listeyle
    DEĞİŞTİRİR: `ubuntu` `sudo`/`adm`/`dialout` üyeliklerini kaybeder, yani hesap sudo'suz kalır ve
    makineye ancak konsoldan girilebilir. Bu yüzden bayrağın VARLIĞI da değeri de ölçülür —
    silinmesi (varsayılana düşmesi) bu çiviyi kırar.
    """
    args = _uyelik_gorevi()["ansible.builtin.user"]
    assert "append" in args, "`append` HİÇ verilmemiş — modül varsayılanı (false) mevcut grupları EZER"
    assert str(args["append"]).strip().lower() in _DOGRU_DEGERLER, (
        f"`append` truthy değil ({args['append']!r}) — mevcut ikincil gruplar silinir"
    )


def test_c_grup_adi_tek_kaynaktan_gelir():
    """(c) Hem varlık ölçümü hem üyelik yazımı AYNI değişkeni kullanır.

    İki yerde literal yazılsaydı biri değiştiğinde koşul artık üyelikle aynı grubu ölçmez: görev
    sessizce hiç işlemez ve üyelik ASLA yazılmazdı (sahte yeşil dağıtım).
    """
    olcum = _olcum_gorevi()["ansible.builtin.getent"]
    uyelik = _uyelik_gorevi()["ansible.builtin.user"]
    assert "docker_grubu" in str(olcum.get("key", "")), (
        f"varlık ölçümü grup adını değişkenden almıyor: {olcum.get('key')!r}"
    )
    assert "docker_grubu" in str(uyelik.get("groups", "")), (
        f"üyelik görevi grup adını değişkenden almıyor: {uyelik.get('groups')!r}"
    )
    assert olcum.get("database") == "group", f"ölçüm `group` veritabanına bakmıyor: {olcum!r}"
    assert olcum.get("fail_key") is False, (
        "`fail_key: false` yok — grup yokken ölçümün KENDİSİ düşer ve koşul hiç kurulamaz"
    )


def test_d_kosul_olculmus_kayda_dayanir_ve_yonu_dogru():
    """(d) `when` ölçüm kaydını okur ve YÖNÜ jinja ile GERÇEKTEN değerlendirilir.

    Metin eşleşmesi yetmez: koşul ters çevrilirse (`is none`) çivi metinle hâlâ yeşil kalırdı —
    tam da CLAUDE.md §6'nın "yanlış sebeple yeşil" sınıfı. Bu yüzden ifade iki senaryoda
    değerlendirilir: grup VARKEN işlemeli, YOKKEN atlanmalı.
    """
    defaults = _defaults()
    grup = defaults["docker_grubu"]
    kayit_adi = _olcum_gorevi().get("register")
    assert isinstance(kayit_adi, str) and kayit_adi, "varlık ölçümü hiçbir kayda yazmıyor"
    ifade = str(_uyelik_gorevi().get("when", ""))
    assert kayit_adi in ifade, f"üyelik koşulu ölçüm kaydını ({kayit_adi}) okumuyor: {ifade!r}"

    ortam = jinja2.Environment(undefined=jinja2.StrictUndefined)

    def _degerlendir(grup_kaydi) -> bool:
        ortak = dict(defaults)
        ortak[kayit_adi] = {"ansible_facts": {"getent_group": {grup: grup_kaydi}}}
        return ortam.from_string("{{ " + ifade + " }}").render(**ortak).strip() == "True"

    assert _degerlendir(["x", "999", "ubuntu"]) is True, (
        f"grup VARKEN üyelik görevi atlanıyor — koşul ters ya da kör: {ifade!r}"
    )
    assert _degerlendir(None) is False, (
        f"grup YOKKEN görev işliyor — `user` modülü 'Group does not exist' ile düşer: {ifade!r}"
    )


def test_e_kosul_kalici_sessiz_atlama_degil():
    """(e) Grubu yaratan paket rolün KENDİ listesindedir — yoksa koşul daimî bir sessiz atlamadır.

    Koşulun meşruiyeti buna bağlı: `docker.io` `apt_paketleri`nden çıkarsa grup hiç doğmaz, üyelik
    görevi HER koşumda atlanır ve rol "üyeliği taşıyorum" iddiasını sessizce boş bırakır. Ayrıca
    sıra ölçülür: üyelik, paketi kuran görevden SONRA gelmeli.
    """
    defaults = _defaults()
    assert "docker.io" in defaults["apt_paketleri"], (
        "`docker.io` `apt_paketleri`nde yok — `docker` grubunu yaratan bir şey kalmadı, koşul "
        "kalıcı sessiz atlamaya döner"
    )
    gorevler = _gorevler()
    apt_indeks = [
        i
        for i, g in enumerate(gorevler)
        if "apt_paketleri" in str(g.get("ansible.builtin.apt", {}).get("name", ""))
    ]
    assert len(apt_indeks) == 1, f"`apt_paketleri`ni kuran tek görev bekleniyordu: {apt_indeks}"
    uyelik_indeks = [i for i, g in enumerate(gorevler) if "ansible.builtin.user" in g]
    assert uyelik_indeks and uyelik_indeks[0] > apt_indeks[0], (
        "üyelik görevi `docker.io`yu kuran görevten ÖNCE — taze hostta grup henüz yoktur ve üyelik "
        f"ilk koşumda atlanır (apt={apt_indeks}, üyelik={uyelik_indeks})"
    )
