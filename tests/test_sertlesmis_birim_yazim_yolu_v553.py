"""v553 — TSK-225: sertleşmiş birimde ORTAMLA VERİLEN YAZIM YOLU sınıfı (2026-09-25).

OLAY (Rol-1 ölçümü, A1 salt-okur): EDG-2026-085 pilotunun ilk canlı seansı 2026-09-25 — A1
`state/events.jsonl` 13:34:25Z `quote_capture_yazim_dustu` "OSError: [Errno 30] Read-only file system:
'/opt/veri/olcum/edg085/kayit'"; dizin A1'de YOK. `meridian.service` `ProtectSystem=strict` ile koşar ve
ad alanında yalnız `ReadWritePaths=/opt/meridian /home/ubuntu/.cache -/home/ubuntu/.hermes` yazılabilirdir;
pilot drop-in'i `55-edg085-quote.conf` kayıt dizinini `Environment=` ile veriyor ama `ReadWritePaths`
EKLEMİYORDU ve dizini hiçbir şey kurmuyordu. Seans kayıtsız geçti; tek işaret bir warn satırıydı.

NEDEN SINIF ÇİVİSİ: aynı hata 2026-09-16'da brifing birimlerinde (EDG-101 yakalama dizini) yaşandı ve
TEK ÖRNEKLE kapatıldı — v516 yalnız kendi üç drop-in'ini ölçer, dördüncü bir yazım yolu doğduğunda
susar. Bu dosya örneği değil SINIFI ölçer:

  B. Ortam ↔ izin. `ProtectSystem=strict` birimde (birim dosyası + `<ad>.service.d/*.conf` drop-in'leri
     systemd sırasıyla BİRLEŞTİRİLMİŞ hâlde) `Environment=` ile verilen her MUTLAK yol ya
       · YAZIM ADLIDIR (`YAZIM_AD_PARCALARI`) → bir `ReadWritePaths` girdisinin (önekli ya da öneksiz)
         kapsamında olmak ZORUNDADIR; ya da
       · `SALT_OKUR_BEYANI`nda gerekçesiyle SALT-OKUR beyan edilmiştir.
     İkisi de değilse "sınıflandırılmamış" diye öter: süzgecin tanımadığı bir adlandırma sessizce
     geçemez. Süzgeç bir KOLAYLIKTIR; güvenlik ağı bu sınıflandırma zorunluluğudur.
  C. İzin ↔ dizin. `ReadWritePaths`'teki her `/opt/veri` yolu için A0 rolünün `tasks/dizinler.yml`inde
     AYNI yolu kuran ve sahibi birimin `User=`'ı olan bir dizin görevi vardır (ya da
     `DIZIN_GOREVI_BEYANI`). "Drop-in var, dizin yok" sınıfı: `-` önekli izin dizin yoksa SESSİZCE
     düşer (yazım yine EROFS ile ölür), öneksiz izin dizin yoksa birimi HİÇ AÇMAZ.
  D. Beyan hijyeni. Beyanlar çürümez (her girdi bugün en az bir oluşumu karşılar); gerekçe ≥20
     karakter; yazım adlı bir değişken "*" ile KÜRESEL susturulamaz (yalnız birim kapsamlı).
  E. Pozitif kontrol. Sentetik birim + drop-in ile hem öten hem ötmeyen durumlar; systemd birleştirme
     kuralları (drop-in sırası, boş atama SIFIRLAR, skaler son-yazan-kazanır, yorum satırı devam
     zincirine katılmaz, `\\` devamı) ayrı ayrı sürülür.
  F. EDG-085 örneği: drop-in izni `-` önekli TEK yol = kayıt dizini; birimin kendi izni onu KAPSAMAZ
     (izin gerekli); A0 görevi aynı yol, sahip `meridian_kullanici`, 0700.

KAPSAM TEK KAYNAKTAN: birimler A0 rolünün `defaults/main.yml::birim_kaynaklari` glob'larından türer
(rolün A1'e KURDUĞU küme: oracle-a1 + hindsight + apisix + vault). Brief `deploy/oracle-a1/`i istedi;
türetilmiş küme onu kapsar (B0 guard) ve bugün öteki dizinlerde mutlak-yol `Environment=` YOK
(ölçüldü 2026-09-25) — genişlik bedelsiz, yeni bir dizin eklendiği gün kendiliğinden kapsama girer.

YAZIM ADI SÜZGECİ — DEPO TARAMASI (2026-09-25). Brief kümesi DIZIN/_DIR/KAYIT/YAZ/OUT/CIKTI. Depo
taranınca (`meridian/ ops/ research/ deploy/` altında `os.environ.get/getenv/environ[...]` okumaları +
`*_ENV = "…"` sabitleri + `.sh` gövdeleri) yazım hedefi taşıyan adlar: MERIDIAN_EDG085_KAYIT_DIZIN ·
MERIDIAN_EDG101_YAKALAMA_DIZIN · HERMES_HOME · HERMES_WRITE_SAFE_ROOT · MERIDIAN_ROOT ·
MERIDIAN_SPRINT_SBROOT · MERIDIAN_STATE · MERIDIAN_DB → HOME/ROOT/STATE/_DB eklendi. Süzgecin ÇALIŞAN
doğrulaması B'nin kendisidir: birimlerin set ettiği HER mutlak-yol değişkeni süzgeçle ya da beyanla
sınıflanmak zorunda — tarama bir kez yapılıp donmaz, her koşumda depodaki gerçek birimlerle tekrarlanır.
"OUT" alt dizgesi TIMEOUT'u da yakalar; zararsızdır, çünkü yalnız MUTLAK YOL değerli atamalar ölçülür.

MODELLENMEYEN (bilinçli; hepsi YANLIŞ-POZİTİF yönünde, yani gürültülü): PrivateTmp /tmp ve
StateDirectory= gibi ReadWritePaths DIŞI yazılabilir kökler; `%h` gibi belirteçler (mutlak değil
sayılır, ölçülmez); önek drop-in'leri (`meridian-.service.d/`). KAPSAM DIŞI yüzey (bu çivinin
göremediği): `EnvironmentFile=` içerikleri (A1'de, depoda değil) ve ExecStart argümanlarındaki yollar.

Numara v553: ana checkout + worktree'lerde boş (ölçüldü 2026-09-25; v551 tsk224, v552 tsk064-argv).
Bu dosya hiçbir `state/` yolu okumaz/yazmaz; sentetik birimler `tmp_path` altında kurulur.
"""
from __future__ import annotations

import dataclasses
import glob
import posixpath
import re
import shlex
from pathlib import Path

import pytest
import yaml

KOK = Path(__file__).resolve().parent.parent
DEPLOY = KOK / "deploy"
ANSIBLE = DEPLOY / "ansible"
ROL = ANSIBLE / "roles" / "meridian_a1"
DEFAULTS = ROL / "defaults" / "main.yml"
DIZINLER = ROL / "tasks" / "dizinler.yml"
EDG085_DROPIN = DEPLOY / "oracle-a1" / "meridian.service.d" / "55-edg085-quote.conf"

VERI_KOKU = "/opt/veri"

#: Adında bu parçalardan biri geçen ortam değişkeninin MUTLAK YOL değeri bir YAZIM hedefidir.
YAZIM_AD_PARCALARI: tuple[str, ...] = (
    # brief (TSK-225)
    "DIZIN", "_DIR", "KAYIT", "YAZ", "OUT", "CIKTI",
    # depo taraması 2026-09-25 (modül docstring'i): HERMES_HOME · *_ROOT · MERIDIAN_STATE · MERIDIAN_DB
    "HOME", "ROOT", "STATE", "_DB",
)

#: Mutlak yol taşıyan ama SALT-OKUR kullanılan değişkenler. `birimler`: "*" (her birim) ya da birim
#: adları (uzantısız dosya adı). Yazım adlı bir değişken "*" alamaz (D2).
SALT_OKUR_BEYANI: dict[str, dict] = {
    "PATH": {
        "birimler": "*",
        "gerekce": "komut arama yolu — ikililer buradan ÇALIŞTIRILIR, hiçbirine yazılmaz",
    },
    "PYTHONPATH": {
        "birimler": "*",
        "gerekce": "Python ithal yolu — modüller buradan OKUNUR; barsarchive'da /opt/meridian izninin "
                   "onu kapsaması tesadüftür, gerekçe değildir",
    },
    "MERIDIAN_SPRINT_SYSTEMCTL": {
        "birimler": ("meridian",),
        "gerekce": "sprint tetiğinin systemctl İKİLİSİ (meridian.service şerhi, sprint.py `_tetik_komutu`) "
                   "— çalıştırılır, yazılmaz",
    },
    "MERIDIAN_STATE": {
        "birimler": ("meridian-aylik-bucket-kopya",),
        "gerekce": "birim SÖZLEŞMESİ: `ReadWritePaths=` BİLEREK YOK (birim şerhi 'YEREL SİLME YOK — "
                   "YAPISAL'); state yalnız OKUNUR, tar PrivateTmp'te doğar — izin vermek sözleşmeyi bozar",
    },
}

#: `ReadWritePaths`'teki /opt/veri yolu için dizinler.yml görevi OLMAYAN, bilinen durumlar. Anahtar yol,
#: `birimler` o yolu izinle alan birimler (başka bir birim aynı yolu alırsa bu beyan onu KAPSAMAZ).
DIZIN_GOREVI_BEYANI: dict[str, dict] = {
    "/opt/veri": {
        "birimler": ("meridian-geridolum",),
        "gerekce": "AÇIK BULGU (TSK-225 taraması, 2026-09-25) — Rol-1 kararı bekliyor. Birim F9 elle-kurulum "
                   "sınıfı (betik + pilot-venv /opt/veri'ye elle kopyalanır) ama A0 rolü birimi "
                   "`birim_kaynaklari` glob'uyla KOPYALAR ve timer'ını enable eder; izin ÖNEKSİZ → dizin "
                   "yoksa birim açılmaz. A1'de dizin VAR (ubuntu:ubuntu 0755, 2026-09-16 ölçümü); taze bir "
                   "hostta bugün yalnız EDG-101/085 yaprak görevlerinin ARA DİZİNİ olarak yaprağın 0700 "
                   "moduyla doğar — tesadüfi bağ. Seçenek: dizinler.yml görevi ya da kalıcı gerekçe.",
    },
    "/opt/veri/olcum": {
        "birimler": ("meridian-edg085-taban",),
        "gerekce": "AÇIK BULGU (TSK-225 taraması, 2026-09-25) — Rol-1 kararı bekliyor. İzin ÖNEKSİZ ve A0 "
                   "rolü `meridian-edg085-taban.timer`ı enable eder; dizin yoksa birim 'namespace' "
                   "hatasıyla düşer (taban örneklemi kaybolur). A1'de dizin VAR (ubuntu:ubuntu 0755, "
                   "2026-09-16 ölçümü) ama onu adıyla kuran görev yok; taze hostta yalnız EDG-101/085 "
                   "yaprak görevlerinin ara dizini olarak doğar — o görevler emekli olunca kurulmaz.",
    },
}


# ================================================================================================
# systemd birim sözdizimi (systemd.syntax(7)) ve birleştirme (systemd.unit(5) drop-in'ler)
# ================================================================================================

def _mantiksal_satirlar(metin: str) -> list[str]:
    """Yorum/boş satırları atar, `\\` devamlarını birleştirir.

    systemd kuralı (conf-parser): `#`/`;` ile başlayan satır ÖNCE elenir — yani yorum satırı `\\` ile
    bitse bile bir devam zinciri BAŞLATMAZ ve zincirin ortasındaki yorum satırı atlanır. Kaçışsız
    sondaki `\\` satırı sonrakiyle birleştirir ve boşluğa döner; dosya sonunda bekleyen zincir satırdır."""
    satirlar: list[str] = []
    devam: str | None = None
    for ham in metin.splitlines():
        if ham.strip()[:1] in ("#", ";"):
            continue
        parca = ham if devam is None else devam + ham
        kacis = False
        for ch in parca:
            if kacis:
                kacis = False
            elif ch == "\\":
                kacis = True
        if kacis:
            devam = parca[:-1] + " "
            continue
        devam = None
        if parca.strip():
            satirlar.append(parca.strip())
    if devam is not None and devam.strip():
        satirlar.append(devam.strip())
    return satirlar


def _yonergeler(metin: str) -> list[tuple[str | None, str, str]]:
    """(bölüm, anahtar, değer) üçlüleri, dosya sırasıyla. Bölüm başlığı yönerge değildir."""
    bolum: str | None = None
    cikti: list[tuple[str | None, str, str]] = []
    for s in _mantiksal_satirlar(metin):
        if s.startswith("[") and s.endswith("]"):
            bolum = s[1:-1].strip()
            continue
        if "=" not in s:
            continue
        anahtar, deger = s.split("=", 1)
        cikti.append((bolum, anahtar.strip(), deger.strip()))
    return cikti


@dataclasses.dataclass
class _Etkin:
    """Bir birimin BİRLEŞTİRİLMİŞ [Service] görünümü (yalnız bu çivinin baktığı yönergeler)."""
    ad: str
    protect_system: str = ""
    rwp: list[tuple[str, Path]] = dataclasses.field(default_factory=list)   # (ham girdi, kaynak)
    ortam: dict[str, tuple[str, Path]] = dataclasses.field(default_factory=dict)  # ad → (değer, kaynak)
    kullanici: str = "root"

    @property
    def rwp_girdileri(self) -> list[str]:
        return [g for g, _ in self.rwp]


def _dropinler(birim: Path) -> list[Path]:
    """`<ad>.service.d/*.conf` — systemd bunları dosya ADINA göre sıralı, birim dosyasından SONRA uygular."""
    return sorted((birim.parent / f"{birim.name}.d").glob("*.conf"), key=lambda p: p.name)


def _birlestir(ad: str, kaynaklar: list[Path]) -> _Etkin:
    """Kaynakları sırayla uygular. Liste yönergeleri (`ReadWritePaths`, `Environment`) BİRİKİR, boş atama
    SIFIRLAR; skaler yönergelerde (`ProtectSystem`, `User`) son yazan kazanır, boş atama varsayılana döner."""
    e = _Etkin(ad=ad)
    for kaynak in kaynaklar:
        for bolum, anahtar, deger in _yonergeler(kaynak.read_text(encoding="utf-8")):
            if bolum != "Service":
                continue
            if anahtar == "ProtectSystem":
                e.protect_system = deger
            elif anahtar == "User":
                e.kullanici = deger or "root"
            elif anahtar == "ReadWritePaths":
                if not deger:
                    e.rwp = []
                else:
                    e.rwp += [(g, kaynak) for g in shlex.split(deger)]
            elif anahtar == "Environment":
                if not deger:
                    e.ortam = {}
                    continue
                for atama in shlex.split(deger):
                    if "=" in atama:
                        isim, deg = atama.split("=", 1)
                        e.ortam[isim] = (deg, kaynak)
    return e


def _etkin_birim(birim: Path) -> _Etkin:
    return _birlestir(birim.name.removesuffix(".service"), [birim, *_dropinler(birim)])


def _onek_at(girdi: str) -> str:
    """`-` (yoksa atla) ve `+` (RootDirectory'ye göreli) önekleri kapsamı değiştirmez."""
    return girdi.lstrip("-+")


def _kapsar(rwp_girdileri: list[str], yol: str) -> bool:
    """YOL bir girdinin kendisi ya da ALTINDAYSA kapsanır — dizgi öneki DEĞİL, yol öneki
    (`/opt/veri/olcum/edg08` `/opt/veri/olcum/edg085`i KAPSAMAZ)."""
    yol = posixpath.normpath(yol)
    for g in rwp_girdileri:
        kok = posixpath.normpath(_onek_at(g))
        if yol == kok or yol.startswith(kok.rstrip("/") + "/"):
            return True
    return False


def _yazim_anlamli(ad: str) -> bool:
    return any(p in ad.upper() for p in YAZIM_AD_PARCALARI)


def _goreli(p: Path) -> str:
    try:
        return str(p.relative_to(KOK))
    except ValueError:
        return p.name


# ================================================================================================
# Denetçiler — gerçek depo ve sentetik birimler AYNI fonksiyondan geçer
# ================================================================================================

def _ortam_bulgulari(birimler: list[Path], beyan: dict | None = None
                     ) -> tuple[list[dict], set[tuple[str, str]]]:
    """B kuralı. Dönüş: (bulgular, kullanılan beyanlar {(değişken, birim)})."""
    beyan = SALT_OKUR_BEYANI if beyan is None else beyan
    bulgular: list[dict] = []
    kullanilan: set[tuple[str, str]] = set()
    for birim in birimler:
        e = _etkin_birim(birim)
        if e.protect_system != "strict":
            continue
        for ad, (deger, kaynak) in sorted(e.ortam.items()):
            if not deger.startswith("/"):
                continue
            b = beyan.get(ad)
            if b and (b["birimler"] == "*" or e.ad in b["birimler"]):
                kullanilan.add((ad, e.ad))
                continue
            ortak = {"birim": e.ad, "degisken": ad, "deger": deger, "kaynak": _goreli(kaynak),
                     "rwp": e.rwp_girdileri}
            if not _yazim_anlamli(ad):
                bulgular.append({"tur": "siniflandirilmamis_yol", **ortak})
                continue
            kapsanmayan = [p for p in deger.split(":") if p.startswith("/")
                           and not _kapsar(e.rwp_girdileri, p)]
            if kapsanmayan:
                bulgular.append({"tur": "kapsamsiz_yazim_yolu", "kapsanmayan": kapsanmayan, **ortak})
    return bulgular, kullanilan


def _sablon_coz(metin: str, degiskenler: dict[str, str]) -> str:
    return re.sub(r"\{\{\s*(\w+)\s*\}\}",
                  lambda m: str(degiskenler.get(m.group(1), m.group(0))), metin)


def _dizin_gorevleri(yml: Path, degiskenler: dict[str, str]) -> dict[str, dict[str, str]]:
    """dizinler.yml'deki `file: state=directory` görevleri: normalize yol → çözülmüş owner/group/mode.
    Şablonlu yol (döngü) atlanır — /opt/veri görevleri literal yazılır; şablona kaçan bir görev
    "görev yok" diye öter (gürültülü yön)."""
    gorevler = yaml.safe_load(yml.read_text(encoding="utf-8")) or []
    sonuc: dict[str, dict[str, str]] = {}
    for g in gorevler:
        arg = g.get("ansible.builtin.file") or g.get("file")
        if not isinstance(arg, dict) or arg.get("state") != "directory":
            continue
        yol = str(arg.get("path", ""))
        if "{{" in yol:
            continue
        sonuc[posixpath.normpath(yol)] = {k: _sablon_coz(str(arg.get(k, "")), degiskenler)
                                          for k in ("owner", "group", "mode")}
    return sonuc


def _dizin_bulgulari(birimler: list[Path], gorevler: dict[str, dict[str, str]],
                     beyan: dict | None = None) -> tuple[list[dict], set[tuple[str, str]]]:
    """C kuralı. ProtectSystem'den BAĞIMSIZ: öneksiz izin, dizin yoksa her birimi açılmaz kılar."""
    beyan = DIZIN_GOREVI_BEYANI if beyan is None else beyan
    bulgular: list[dict] = []
    kullanilan: set[tuple[str, str]] = set()
    for birim in birimler:
        e = _etkin_birim(birim)
        for girdi, kaynak in e.rwp:
            yol = posixpath.normpath(_onek_at(girdi))
            if not (yol == VERI_KOKU or yol.startswith(VERI_KOKU + "/")):
                continue
            ortak = {"birim": e.ad, "girdi": girdi, "kaynak": _goreli(kaynak)}
            gorev = gorevler.get(yol)
            if gorev is None:
                b = beyan.get(yol)
                if b and e.ad in b["birimler"]:
                    kullanilan.add((yol, e.ad))
                    continue
                bulgular.append({"tur": "dizin_gorevi_yok", **ortak})
            elif gorev["owner"] != e.kullanici:
                bulgular.append({"tur": "dizin_sahibi_birim_kullanicisi_degil",
                                 "gorev_sahibi": gorev["owner"], "birim_kullanicisi": e.kullanici,
                                 **ortak})
    return bulgular, kullanilan


# ================================================================================================
# Depo girdileri (tek kaynak: A0 rolü)
# ================================================================================================

def _defaults() -> dict:
    return yaml.safe_load(DEFAULTS.read_text(encoding="utf-8"))


def _depo_birimleri() -> list[Path]:
    """A0 rolünün KURDUĞU `.service` dosyaları — `birim_kaynaklari` glob'larından türer."""
    bulunan: set[Path] = set()
    for desen in _defaults()["birim_kaynaklari"]:
        if not desen.endswith(".service"):
            continue
        cozulen = desen.replace("{{ playbook_dir }}", str(ANSIBLE))
        bulunan |= {Path(p).resolve() for p in glob.glob(cozulen)}
    return sorted(bulunan)


def _depo_gorevleri() -> dict[str, dict[str, str]]:
    d = _defaults()
    return _dizin_gorevleri(DIZINLER, {"meridian_kullanici": d["meridian_kullanici"]})


def _bicimle(bulgular: list[dict]) -> str:
    return "\n".join(f"  · {b}" for b in bulgular)


# ================================================================================================
# B — ortam ↔ izin (gerçek depo)
# ================================================================================================

def test_B0_kapsam_A0_rolunden_turer_ve_oracle_a1i_tam_kapsar():
    birimler = _depo_birimleri()
    oracle = {p.resolve() for p in (DEPLOY / "oracle-a1").glob("*.service")}
    assert oracle, "deploy/oracle-a1 altında birim yok — yol yanlış, çivi kör"
    eksik = oracle - set(birimler)
    assert not eksik, f"birim_kaynaklari oracle-a1 birimlerini kapsamıyor: {sorted(map(str, eksik))}"
    strict = [b for b in birimler if _etkin_birim(b).protect_system == "strict"]
    assert (DEPLOY / "oracle-a1" / "meridian.service").resolve() in strict, (
        "meridian.service strict görünmüyor — birleştirme ya da ayrıştırma kırık, çivi kör")


def test_B1_strict_birimde_ortamla_verilen_YAZIM_yolu_ReadWritePaths_kapsaminda():
    bulgular, _ = _ortam_bulgulari(_depo_birimleri())
    assert not bulgular, (
        "ProtectSystem=strict birimde Environment= ile verilen yol yazılamaz ya da sınıflanmamış:\n"
        f"{_bicimle(bulgular)}\n"
        "ÇARE: yazım yoluysa drop-in'e `ReadWritePaths=-<yol>` (emsal 60-edg101-yakalama.conf) + "
        "dizinler.yml görevi; salt-okursa SALT_OKUR_BEYANI'na gerekçesiyle.")


# ================================================================================================
# C — izin ↔ dizin (gerçek depo)
# ================================================================================================

def test_C1_ReadWritePaths_opt_veri_yolu_icin_dizinler_yml_gorevi_var():
    bulgular, _ = _dizin_bulgulari(_depo_birimleri(), _depo_gorevleri())
    assert not bulgular, (
        "ReadWritePaths ile izin verilen /opt/veri yolunu A0 rolü KURMUYOR (ya da yanlış sahiple):\n"
        f"{_bicimle(bulgular)}\n"
        "ÇARE: deploy/ansible/roles/meridian_a1/tasks/dizinler.yml'e aynı yolu kuran görev "
        "(owner/group {{ meridian_kullanici }}) ya da DIZIN_GOREVI_BEYANI'na gerekçe.")


# ================================================================================================
# D — beyan hijyeni
# ================================================================================================

def test_D1_SALT_OKUR_BEYANI_curumez_her_girdi_bugun_bir_olusumu_karsilar():
    _, kullanilan = _ortam_bulgulari(_depo_birimleri())
    curuk: list[str] = []
    for ad, b in SALT_OKUR_BEYANI.items():
        birimler = {birim for (a, birim) in kullanilan if a == ad}
        if b["birimler"] == "*":
            if not birimler:
                curuk.append(f"{ad} (*): hiçbir strict birimde mutlak-yol ataması yok")
        else:
            eksik = set(b["birimler"]) - birimler
            if eksik:
                curuk.append(f"{ad}: {sorted(eksik)} birim(ler)inde karşılanan oluşum yok")
    assert not curuk, "çürük salt-okur beyanı (sil ya da düzelt):\n  " + "\n  ".join(curuk)


def test_D1b_DIZIN_GOREVI_BEYANI_curumez():
    _, kullanilan = _dizin_bulgulari(_depo_birimleri(), _depo_gorevleri())
    curuk: list[str] = []
    for yol, b in DIZIN_GOREVI_BEYANI.items():
        eksik = set(b["birimler"]) - {birim for (y, birim) in kullanilan if y == yol}
        if eksik:
            curuk.append(f"{yol}: {sorted(eksik)} birim(ler)inde karşılanan oluşum yok")
    assert not curuk, (
        "çürük dizin beyanı — görev eklendiyse ya da izin kalktıysa beyanı SİL:\n  " + "\n  ".join(curuk))


def test_D2_beyan_bicimi_gerekceli_ve_yazim_adli_degisken_KURESEL_susturulamaz():
    for ad, b in SALT_OKUR_BEYANI.items():
        assert len(b["gerekce"].strip()) >= 20, f"{ad}: gerekçe kısa"
        assert b["birimler"] == "*" or (isinstance(b["birimler"], tuple) and b["birimler"]), ad
        if _yazim_anlamli(ad):
            assert b["birimler"] != "*", (
                f"{ad} yazım adlı — '*' ile küresel susturmak sınıfı her birimde kör eder; birim kapsamlı yaz")
    for yol, b in DIZIN_GOREVI_BEYANI.items():
        assert len(b["gerekce"].strip()) >= 20, f"{yol}: gerekçe kısa"
        assert isinstance(b["birimler"], tuple) and b["birimler"], yol
        assert yol == VERI_KOKU or yol.startswith(VERI_KOKU + "/"), yol


# ================================================================================================
# E — pozitif kontrol: sentetik birim + drop-in
# ================================================================================================

_TABAN = """[Unit]
Description=sentetik

[Service]
User=ubuntu
{govde}
"""

_YOL = "/opt/veri/olcum/ornek/kayit"


def _birim_kur(tmp_path: Path, govde: str, dropinler: dict[str, str] | None = None,
               ad: str = "ornek") -> Path:
    birim = tmp_path / f"{ad}.service"
    birim.write_text(_TABAN.format(govde=govde), encoding="utf-8")
    if dropinler:
        d = tmp_path / f"{ad}.service.d"
        d.mkdir()
        for dosya, metin in dropinler.items():
            (d / dosya).write_text(metin, encoding="utf-8")
    return birim


# (kimlik, birim gövdesi, drop-in'ler, beklenen bulgu türleri)
ORTAM_DURUMLARI = [
    ("oten_kapsamsiz",
     f"ProtectSystem=strict\nReadWritePaths=/opt/meridian\nEnvironment=ORNEK_KAYIT_DIZIN={_YOL}", None,
     ["kapsamsiz_yazim_yolu"]),
    ("dropin_onekli_izin_kapsar",
     f"ProtectSystem=strict\nReadWritePaths=/opt/meridian\nEnvironment=ORNEK_KAYIT_DIZIN={_YOL}",
     {"60-x.conf": f"[Service]\nReadWritePaths=-{_YOL}\n"}, []),
    ("ust_dizin_izni_kapsar",
     f"ProtectSystem=strict\nReadWritePaths=/opt/veri\nEnvironment=ORNEK_KAYIT_DIZIN={_YOL}", None, []),
    ("dizgi_oneki_KAPSAMAZ",
     f"ProtectSystem=strict\nReadWritePaths=-/opt/veri/olcum/orn\nEnvironment=ORNEK_KAYIT_DIZIN={_YOL}",
     None, ["kapsamsiz_yazim_yolu"]),
    ("strict_degil_olculmez",
     f"ProtectSystem=full\nEnvironment=ORNEK_KAYIT_DIZIN={_YOL}", None, []),
    ("strict_yalniz_dropinde",
     f"Environment=ORNEK_KAYIT_DIZIN={_YOL}", {"10-s.conf": "[Service]\nProtectSystem=strict\n"},
     ["kapsamsiz_yazim_yolu"]),
    ("strict_dropinde_SIFIRLANIR",
     f"ProtectSystem=strict\nEnvironment=ORNEK_KAYIT_DIZIN={_YOL}",
     {"10-s.conf": "[Service]\nProtectSystem=\n"}, []),
    ("izin_listesi_dropinde_SIFIRLANIR",
     f"ProtectSystem=strict\nReadWritePaths=/opt/veri\nEnvironment=ORNEK_KAYIT_DIZIN={_YOL}",
     {"20-r.conf": "[Service]\nReadWritePaths=\nReadWritePaths=/opt/meridian\n"},
     ["kapsamsiz_yazim_yolu"]),
    ("ortam_dropinde_SIFIRLANIR",
     f"ProtectSystem=strict\nEnvironment=ORNEK_KAYIT_DIZIN={_YOL}",
     {"20-e.conf": "[Service]\nEnvironment=\n"}, []),
    ("ortam_son_yazan_kazanir",
     f"ProtectSystem=strict\nReadWritePaths=/opt/meridian\nEnvironment=ORNEK_KAYIT_DIZIN=/opt/meridian/x",
     {"20-e.conf": f"[Service]\nEnvironment=ORNEK_KAYIT_DIZIN={_YOL}\n"}, ["kapsamsiz_yazim_yolu"]),
    ("dropin_sirasi_ada_gore",
     f"ProtectSystem=strict\nReadWritePaths=/opt/meridian",
     {"90-son.conf": f"[Service]\nEnvironment=ORNEK_KAYIT_DIZIN=/opt/meridian/x\n",
      "10-ilk.conf": f"[Service]\nEnvironment=ORNEK_KAYIT_DIZIN={_YOL}\n"}, []),
    ("tek_satirda_coklu_atama",
     f'ProtectSystem=strict\nEnvironment="A=1" ORNEK_DIZIN={_YOL}', None, ["kapsamsiz_yazim_yolu"]),
    ("yazim_adsiz_beyansiz_SINIFLANMAMIS",
     "ProtectSystem=strict\nEnvironment=ORNEK_ARSIV=/srv/arsiv", None, ["siniflandirilmamis_yol"]),
    ("yazim_adsiz_ama_KAPSANMIS_da_siniflanmali",
     "ProtectSystem=strict\nReadWritePaths=/srv\nEnvironment=ORNEK_ARSIV=/srv/arsiv", None,
     ["siniflandirilmamis_yol"]),
    ("mutlak_olmayan_deger_olculmez",
     "ProtectSystem=strict\nEnvironment=ORNEK_KAYIT_DIZIN=olcum/x", None, []),
    ("yorum_satiri_devami_SONRAKINI_YUTMAZ",
     f"ProtectSystem=strict\nEnvironment=ORNEK_KAYIT_DIZIN={_YOL}\n# not \\\nReadWritePaths=-{_YOL}",
     None, []),
    ("ters_bolu_devami_birlestirir",
     f"ProtectSystem=strict\nEnvironment=ORNEK_KAYIT_DIZIN={_YOL}\nReadWritePaths=/opt/meridian \\\n"
     f"# zincir ortasında yorum atlanır\n    -{_YOL}", None, []),
    ("baska_bolumdeki_yonerge_sayilmaz",
     f"Environment=ORNEK_KAYIT_DIZIN={_YOL}\n[Install]\nProtectSystem=strict", None, []),
]


@pytest.mark.parametrize("kimlik, govde, dropinler, beklenen", ORTAM_DURUMLARI,
                         ids=[d[0] for d in ORTAM_DURUMLARI])
def test_E1_pozitif_kontrol_ORTAM_kurali(tmp_path, kimlik, govde, dropinler, beklenen):
    birim = _birim_kur(tmp_path, govde, dropinler)
    bulgular, _ = _ortam_bulgulari([birim], beyan={})
    assert [b["tur"] for b in bulgular] == beklenen, f"{kimlik}:\n{_bicimle(bulgular)}"


def test_E1b_beyan_yalniz_ADI_gecen_birimi_susturur(tmp_path):
    govde = "ProtectSystem=strict\nEnvironment=ORNEK_ARSIV=/srv/arsiv"
    birim = _birim_kur(tmp_path, govde)
    beyan_bu = {"ORNEK_ARSIV": {"birimler": ("ornek",), "gerekce": "sentetik salt-okur arşiv yolu"}}
    beyan_baska = {"ORNEK_ARSIV": {"birimler": ("baska",), "gerekce": "sentetik salt-okur arşiv yolu"}}
    assert _ortam_bulgulari([birim], beyan=beyan_bu) == ([], {("ORNEK_ARSIV", "ornek")})
    assert [b["tur"] for b in _ortam_bulgulari([birim], beyan=beyan_baska)[0]] == ["siniflandirilmamis_yol"]


@pytest.mark.parametrize("ad", ["MERIDIAN_EDG085_KAYIT_DIZIN", "MERIDIAN_EDG101_YAKALAMA_DIZIN",
                                "HERMES_HOME", "HERMES_WRITE_SAFE_ROOT", "MERIDIAN_ROOT",
                                "MERIDIAN_SPRINT_SBROOT", "MERIDIAN_STATE", "MERIDIAN_DB",
                                "ORNEK_CIKTI", "ORNEK_OUT", "OUTPUT_DIR", "YAZIM_YERI"])
def test_E2_suzgec_depodaki_yazim_adlarini_TANIR(ad):
    assert _yazim_anlamli(ad), f"{ad} yazım adı sayılmadı — süzgeç depodaki adlandırmayı kaçırıyor"


@pytest.mark.parametrize("ad", ["PATH", "PYTHONPATH", "MERIDIAN_SPRINT_SYSTEMCTL", "MERIDIAN_BIND_HOST"])
def test_E2b_suzgec_salt_okur_adlari_yazim_SAYMAZ(ad):
    assert not _yazim_anlamli(ad), f"{ad} yazım sayıldı — süzgeç çok geniş"


def test_E2c_suzgec_sabitleri_kaynak_modullerle_ayni_adi_tasir():
    """Yukarıdaki iki gerçek ad kaynaktan da doğrulanır: modül sabiti yeniden adlandırılırsa E2 bayat
    bir adı ölçüyor olurdu."""
    from meridian import quotecapture
    from ops import soul_denetimi
    assert _yazim_anlamli(quotecapture.DIZIN_ENV), quotecapture.DIZIN_ENV
    assert _yazim_anlamli(soul_denetimi.EDG101_YAKALAMA_ENV), soul_denetimi.EDG101_YAKALAMA_ENV


# (kimlik, birim gövdesi, dizinler.yml, beklenen)
_GOREV = """- name: sentetik
  ansible.builtin.file:
    path: {yol}
    state: directory
    owner: "{sahip}"
    group: "{{{{ meridian_kullanici }}}}"
    mode: "0700"
"""

DIZIN_DURUMLARI = [
    ("oten_gorev_yok", f"ReadWritePaths=-{_YOL}", "[]\n", ["dizin_gorevi_yok"]),
    ("gorev_var_sahip_dogru", f"ReadWritePaths=-{_YOL}",
     _GOREV.format(yol=_YOL, sahip="{{ meridian_kullanici }}"), []),
    ("gorev_var_sahip_ROOT", f"ReadWritePaths=-{_YOL}", _GOREV.format(yol=_YOL, sahip="root"),
     ["dizin_sahibi_birim_kullanicisi_degil"]),
    ("gorev_UST_dizinde_yetmez", f"ReadWritePaths=-{_YOL}",
     _GOREV.format(yol="/opt/veri/olcum", sahip="{{ meridian_kullanici }}"), ["dizin_gorevi_yok"]),
    ("opt_veri_disi_olculmez", "ReadWritePaths=/opt/meridian /opt/verix", "[]\n", []),
    ("oneksiz_ve_strictsiz_de_olculur", f"ReadWritePaths={_YOL}", "[]\n", ["dizin_gorevi_yok"]),
]


@pytest.mark.parametrize("kimlik, govde, yml, beklenen", DIZIN_DURUMLARI, ids=[d[0] for d in DIZIN_DURUMLARI])
def test_E3_pozitif_kontrol_DIZIN_kurali(tmp_path, kimlik, govde, yml, beklenen):
    birim = _birim_kur(tmp_path, govde)
    dosya = tmp_path / "dizinler.yml"
    dosya.write_text(yml, encoding="utf-8")
    gorevler = _dizin_gorevleri(dosya, {"meridian_kullanici": "ubuntu"})
    bulgular, _ = _dizin_bulgulari([birim], gorevler, beyan={})
    assert [b["tur"] for b in bulgular] == beklenen, f"{kimlik}:\n{_bicimle(bulgular)}"


# ================================================================================================
# F — EDG-085 örneği
# ================================================================================================

def _edg085_dizini() -> str:
    from meridian import quotecapture
    env = [d for b, a, d in _yonergeler(EDG085_DROPIN.read_text(encoding="utf-8"))
           if a == "Environment" and d.startswith(f"{quotecapture.DIZIN_ENV}=")]
    assert len(env) == 1, f"kayıt dizini Environment satırı tek değil: {env}"
    return env[0].split("=", 1)[1]


def test_F1_edg085_dropin_izni_TEK_onekli_yol_KAYIT_DIZINI_ve_skaler_yok():
    yon = _yonergeler(EDG085_DROPIN.read_text(encoding="utf-8"))
    dizin = _edg085_dizini()
    rwp = [d for _, a, d in yon if a == "ReadWritePaths"]
    assert rwp == [f"-{dizin}"], (
        f"izin `-` önekli TEK yol olarak kayıt dizinini göstermiyor: {rwp} ↔ {dizin} — öneksiz izin dizin "
        "yokken MOTORU açılmaz kılar; boş atama birimin kendi iznini SIFIRLAR")
    assert {b for b, _, _ in yon} == {"Service"}, yon
    assert {a for _, a, _ in yon} <= {"Environment", "ReadWritePaths"}, (
        f"drop-in skaler direktif taşıyor ({sorted({a for _, a, _ in yon})}) — birimin sertleştirmesini "
        "sessizce ezer (meridian.service H3 tur-2 şerhi)")
    assert dizin.startswith(VERI_KOKU + "/") and "/state" not in dizin, dizin


def test_F2_meridian_service_kendi_izni_kayit_dizinini_KAPSAMAZ_izin_gerekli():
    birim = DEPLOY / "oracle-a1" / "meridian.service"
    kendi = _birlestir("meridian", [birim])
    assert kendi.protect_system == "strict", "ön koşul: strict değilse izin gerekçesi çürür"
    dizin = _edg085_dizini()
    assert not _kapsar(kendi.rwp_girdileri, dizin), (
        f"meridian.service zaten {dizin} yazabiliyor — drop-in izni gereksiz; gerekçeyi yeniden düşün")
    assert _kapsar(_etkin_birim(birim).rwp_girdileri, dizin), "birleştirilmiş birim dizini kapsamıyor"


def test_F3_dizinler_yml_edg085_gorevi_ayni_yol_meridian_kullanicisi_0700():
    gorevler = yaml.safe_load(DIZINLER.read_text(encoding="utf-8"))
    dizin = _edg085_dizini()
    eslesen = [g["ansible.builtin.file"] for g in gorevler
               if str(g.get("ansible.builtin.file", {}).get("path", "")) == dizin]
    assert len(eslesen) == 1, f"{dizin} için dizin görevi tek değil: {eslesen}"
    a = eslesen[0]
    assert a["state"] == "directory" and str(a["mode"]) == "0700", a
    assert a["owner"] == a["group"] == "{{ meridian_kullanici }}", a
