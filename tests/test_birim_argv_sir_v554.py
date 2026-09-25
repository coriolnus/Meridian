"""v554 — TSK-226: birim KOMUT satırında SIR DEĞİŞKENİ GENİŞLEMESİ sınıfı (argv görünürlüğü, 2026-09-25).

OLAY (Rol-1 ölçümü, A1 salt-okur, 2026-09-25 21:2xZ): TSK-064 argv dağıtımı doğrulanırken A1'de Hindsight
kiracı anahtarını komut satırında taşıyan TEK süreç bulundu — `hindsight-cp.service`in başlattığı root
`docker run` süreci (2026-09-15'ten beri). Birimin ExecStart'ı iki sırrı `-e AD=${AD}` biçiminde veriyordu:
systemd `EnvironmentFile=` değerlerini ExecStart'a GENİŞLETİR, yani iki sır `ps` ve `/proc/<pid>/cmdline`
ile makinedeki HER kullanıcıya açıktı. `deploy/sir_envanteri.yaml` bu tüketiciyi "docker env-file" diye
beyan ediyordu — gerçekle çelişen bir beyan; drop-in şerhi (`50-vault-yan-dosya.conf`) argv görünürlüğünü
hiç tartmamıştı.

NEDEN SINIF ÇİVİSİ: v552 (TSK-064 argv) sırrı BİR betiğin argv'sinden çıkardı; aynı sınıf bir birim
dosyasında yaşıyordu ve hiçbir çivi birim dosyalarının komut satırına bakmıyordu. Bu dosya örneği değil
SINIFI ölçer:

  A. Kapsam. Depodaki BÜTÜN systemd birim biçimli dosyalar (`*.service|socket|mount|swap` + aynı adlı
     `.d/*.conf` drop-in'leri; gizli dizinler ve `state/`·`backups/`·`node_modules/` budanır). A0 rolünün
     A1'e KURDUĞU küme (`birim_kaynaklari` + `dropin_kaynaklari` glob'ları, v553 deseniyle çözülür) bu
     kapsamın ALTINDA olmak zorundadır — rol yeni bir kaynak dizini eklerse ve tarama onu görmezse öter.
     Ayrıştırıcının kendisi de ölçülür: her `.service` en az bir komut yönergesi taşır; `Exec` ile
     başlayan tanınmayan bir anahtar (yazım hatası, yeni yönerge) sessizce atlanamaz.
  B. Kural. Komut yönergelerinde (`ExecStart`, `ExecStartPre/Post`, `ExecStop*`, `ExecReload`,
     `ExecCondition` … — hepsi bir süreç doğurur ve argv'si aynı görünürlüktedir; brief `ExecStart*`
     dedi, sınıf bütün komut yönergeleridir) adı SIR sınıfında olan bir değişkenin genişlemesi YASAK:
       · `${AD}` ve `$AD` — systemd (PID 1) genişletir, değer doğrudan argv'ye girer;
       · `$${AD}` ve `$$AD` — systemd düz `$` bırakır, `sh -c` kabuğu genişletir ve değer kabuğun
         koştuğu HARİCİ komutun argv'sine girer (kabuk yerleşiği ise girmez — ayrım statik yapılamaz,
         bu yüzden gürültülü yönde öter; meşru durum istisna sözlüğüne gerekçesiyle girer).
     Çare: docker için değersiz `-e AD` (istemci değeri kendi ortamından okur), systemd-doğal süreç için
     `LoadCredential`, betik için ortamdan/dosyadan okuyan sarmalayıcı.
  C. Sır adı sınıfı BEYANLIDIR ve ÇAPRAZ DOĞRULANIR. Brief kümesi KEY/SECRET/TOKEN/PASS/PAROLA/
     CREDENTIAL. İki bağımsız kaynak onun ALTINDA olmak zorundadır: `sir_rotasyon.sh`in sır adı sözlüğü
     (`_SIR_ADI_SONEKLERI`, betik metninden okunur) ve `sir_envanteri.yaml`daki BÜTÜN sır adları (dosya
     değişkenleri · rotasyon kopyaları · kasa KV · kasa yan dosyaları). Çapraz doğrulama 2026-09-25'te iki
     açık buldu — `OPENROUTER_AUTH` (auth başlığı) ve `HINDSIGHT_API_DATABASE_URL` (parola URL'ye gömülü;
     2026-09-02'de tam bu sınıf kara-liste süzgecinden kaçıp terminale düşmüştü) — ve küme ÖLÇÜLEREK
     genişledi (`SIR_AD_PARCALARI_OLCULEN`). Ölçülen her ek parça, brief parçalarının kaçırdığı en az bir
     bilinen adı yakalamak zorundadır (çürümez, gereksiz genişlemez). Bedel ters yönde de ölçülür: depodaki
     sır OLMAYAN genişlemeler (`MERIDIAN_BIND_HOST` · `MERIDIAN_SPRINT_SBROOT` · `MERIDIAN_SPRINT_CONF` ·
     `MAINPID` · kabuk `rc`/`ok`) ve envanterin `sir: false` adları süzgeçten GEÇMEZ — bugünkü yanlış-pozitif
     sayısı 0 (ölçüldü 2026-09-25).
  D. İstisna sözlüğü (`ARGV_ISTISNALARI`) gerekçeli (≥20 karakter) ve çürümez; BOŞ başlar.
  E. Pozitif kontrol: sentetik birim + drop-in ile her öten biçim ve her ötmeyen biçim ayrı ayrı sürülür.
  F. Çıktı disiplini: ihlal kaydı yalnız dosya + yönerge + değişken ADI taşır; satır metni, değer ve `=`
     hiçbir çıktıya girmez (kara-liste maskeleme bilinmeyen sırrı kaçırır — beyaz liste: yalnız ad).
  G. TSK-226 örneği: `hindsight-cp.service` sırları değersiz `-e AD` ile geçirir; sır olmayan sabitler
     aynen; `--env-file` yok (Rol-1 kararı); kasa yan dosyası (`EnvironmentFile=-…/.env-cp.vault`,
     drop-in) ORTAM yoluyla hâlâ kazanır — sistemd+docker birleşimi sentetik değerlerle modellenir ve
     eski biçimin argv'ye sızdırdığı, yenisinin sızdırmadığı AYNI modelde gösterilir.

MODELLENMEYEN (bilinçli): `EnvironmentFile=` İÇERİKLERİ (A1'de, depoda değil); betiklerin çalışma
anında yazdığı drop-in'ler (depoda Exec satırı yazan betik yok — ölçüldü 2026-09-25); birim dışı argv
(betikler — v552 ve kardeşleri); sır değerinin birim dosyasına LİTERAL yazılması (ayrı sınıf; envanter
çivisi v439 E4 değer alanını yasaklar). Genişleme ayrıştırıcısı systemd'nin kelime-konumu kuralını
(`$AD` yalnız tek başına kelimeyken genişler) MODELLEMEZ — her konumda öter (gürültülü yön).

Numara v554: ana checkout + worktree'lerde boş (ölçüldü 2026-09-25; v553 tsk225). Bu dosya hiçbir
`state/` yolu okumaz/yazmaz; sentetik birimler ve değerler `tmp_path` altında kurulur.
"""
from __future__ import annotations

import dataclasses
import glob
import os
import re
import shlex
from pathlib import Path

import pytest
import yaml

# Tek-kaynak: birim sözdizimi (yorum + `\\` devamı) ve yönerge ayrıştırması v553'te yaşar.
from tests.test_sertlesmis_birim_yazim_yolu_v553 import _yonergeler

KOK = Path(__file__).resolve().parent.parent
DEPLOY = KOK / "deploy"
ANSIBLE = DEPLOY / "ansible"
DEFAULTS = ANSIBLE / "roles" / "meridian_a1" / "defaults" / "main.yml"
ENVANTER = DEPLOY / "sir_envanteri.yaml"
ROTASYON = DEPLOY / "oracle-a1" / "sir_rotasyon.sh"
CP_BIRIM = DEPLOY / "hindsight" / "hindsight-cp.service"
CP_DROPIN = DEPLOY / "hindsight" / "hindsight-cp.service.d" / "50-vault-yan-dosya.conf"
CP_ENV = "/opt/hindsight/.env-cp"
CP_ENV_VAULT = "/opt/hindsight/.env-cp.vault"

#: Exec* yönergesi taşıyabilen birim türleri (systemd.service/socket/mount/swap(5)).
BIRIM_SONEKLERI: tuple[str, ...] = (".service", ".socket", ".mount", ".swap")
#: Tarama budaması — nokta ile başlayan her dizine EK olarak (`.git`, `.venv`, `.claude/worktrees` …).
BUDANAN_DIZINLER = frozenset({"node_modules", "state", "backups", "__pycache__"})

#: Bir SÜREÇ doğuran (argv'si olan) yönergeler — systemd.service/socket/mount/swap(5).
KOMUT_YONERGELERI = frozenset({
    "ExecCondition", "ExecStartPre", "ExecStart", "ExecStartPost", "ExecReload", "ExecStop",
    "ExecStopPre", "ExecStopPost", "ExecMount", "ExecUnmount", "ExecRemount", "ExecActivate",
    "ExecDeactivate",
})
#: `Exec` ile başlayan ama komut OLMAYAN yönergeler (yol listeleri; systemd bunlarda ortam genişletmez).
KOMUT_OLMAYAN_EXEC = frozenset({"ExecSearchPath", "ExecPaths"})

#: Sır adı sınıfı — brief kümesi (TSK-226).
SIR_AD_PARCALARI_BRIEF: tuple[str, ...] = ("KEY", "SECRET", "TOKEN", "PASS", "PAROLA", "CREDENTIAL")
#: Çapraz doğrulamanın ÖLÇTÜĞÜ ekler (2026-09-25) — parça → gerekçe. Her biri brief parçalarının
#: kaçırdığı en az bir bilinen sır adını yakalar (C3 bunu her koşumda yeniden ölçer).
SIR_AD_PARCALARI_OLCULEN: dict[str, str] = {
    "AUTH": "envanterde OPENROUTER_AUTH sır (kapı yetki başlığı); brief parçalarının hiçbirine uymuyordu",
    "DATABASE_URL": "HINDSIGHT_API_DATABASE_URL parolayı URL'ye GÖMÜLÜ taşır; 2026-09-02'de tam bu sınıf "
                    "kara-liste süzgecinden kaçıp terminale düştü",
}
SIR_AD_PARCALARI: tuple[str, ...] = (*SIR_AD_PARCALARI_BRIEF, *SIR_AD_PARCALARI_OLCULEN)

#: (depo-göreli dosya, değişken ADI) → gerekçe (≥20 karakter). BOŞ başlar (TSK-226).
ARGV_ISTISNALARI: dict[tuple[str, str], str] = {}

_AD_ARDI = re.compile(r"\{?([A-Za-z_][A-Za-z0-9_]*)")


# ================================================================================================
# Çekirdek — gerçek depo ve sentetik birimler AYNI fonksiyonlardan geçer
# ================================================================================================

def _sir_adi_mi(ad: str) -> bool:
    buyuk = ad.upper()
    return any(p in buyuk for p in SIR_AD_PARCALARI)


def _genislemeler(deger: str) -> list[tuple[str, str]]:
    """Komut değerindeki değişken genişlemeleri: [(biçim, AD)].

    systemd kuralı (systemd.service(5) "Command lines"): `$$` düz bir `$` olur; `${AD}` ve `$AD`
    PID 1 tarafından genişletilir. `$$` ardından bir ad geliyorsa o `$AD` kabuğa DÜZ gider ve `sh -c`
    içinde KABUK genişletir. `$$$AD` = düz `$` + systemd `$AD` (soldan sağa tüketim)."""
    cikti: list[tuple[str, str]] = []
    i, n = 0, len(deger)
    while i < n:
        if deger[i] != "$":
            i += 1
            continue
        if i + 1 < n and deger[i + 1] == "$":
            bicim, j = "kabuk", i + 2
        else:
            bicim, j = "systemd", i + 1
        m = _AD_ARDI.match(deger, j)
        if m:
            cikti.append((bicim, m.group(1)))
            i = m.end()
        else:
            i = j
    return cikti


@dataclasses.dataclass(frozen=True, order=True, repr=False)
class Ihlal:
    """YALNIZ ADLAR: dosya, yönerge, değişken adı, genişleme biçimi. Satır metni ve değer TAŞINMAZ."""
    kaynak: str
    yonerge: str
    ad: str
    bicim: str

    def __str__(self) -> str:
        return f"{self.kaynak} · {self.yonerge} · {self.ad} ({self.bicim} genişlemesi)"

    __repr__ = __str__


def _goreli(p: Path, kok: Path) -> str:
    try:
        return p.resolve().relative_to(kok.resolve()).as_posix()
    except ValueError:
        return p.name


def _tara(dosyalar: list[Path], *, kok: Path = KOK, istisnalar: dict | None = None
          ) -> tuple[list[Ihlal], set[tuple[str, str]]]:
    """B kuralı. Dönüş: (ihlaller, kullanılan istisna anahtarları)."""
    istisnalar = ARGV_ISTISNALARI if istisnalar is None else istisnalar
    ihlaller: set[Ihlal] = set()
    kullanilan: set[tuple[str, str]] = set()
    for p in dosyalar:
        kaynak = _goreli(p, kok)
        for _bolum, anahtar, deger in _yonergeler(p.read_text(encoding="utf-8")):
            if anahtar not in KOMUT_YONERGELERI:
                continue
            for bicim, ad in _genislemeler(deger):
                if not _sir_adi_mi(ad):
                    continue
                if (kaynak, ad) in istisnalar:
                    kullanilan.add((kaynak, ad))
                    continue
                ihlaller.add(Ihlal(kaynak, anahtar, ad, bicim))
    return sorted(ihlaller), kullanilan


def _kapsam(kok: Path = KOK) -> list[Path]:
    """Depodaki bütün birim biçimli dosyalar + drop-in'leri (A)."""
    dropin_sonekleri = tuple(s + ".d" for s in BIRIM_SONEKLERI)
    bulunan: list[Path] = []
    for dizin, altlar, dosyalar in os.walk(kok):
        altlar[:] = sorted(a for a in altlar if not a.startswith(".") and a not in BUDANAN_DIZINLER)
        ust = Path(dizin)
        dropin_dizini = ust.name.endswith(dropin_sonekleri)
        for ad in dosyalar:
            if ad.endswith(BIRIM_SONEKLERI) or (dropin_dizini and ad.endswith(".conf")):
                bulunan.append((ust / ad).resolve())
    return sorted(bulunan)


def _a0_kaynaklari() -> set[Path]:
    """A0 rolünün A1'e kurduğu birim + drop-in kaynakları (v553 `_depo_birimleri` deseni), Exec
    taşıyabilen türlere süzülmüş (`.timer` komut taşımaz)."""
    d = yaml.safe_load(DEFAULTS.read_text(encoding="utf-8"))
    cikti: set[Path] = set()
    for desen in [*d["birim_kaynaklari"], *d["dropin_kaynaklari"]]:
        cozulen = desen.replace("{{ playbook_dir }}", str(ANSIBLE))
        cikti |= {Path(p).resolve() for p in glob.glob(cozulen)}
    return {p for p in cikti if p.suffix in BIRIM_SONEKLERI or p.suffix == ".conf"}


def _bicimle(ihlaller) -> str:
    return "\n".join(f"  · {i}" for i in ihlaller)


# ================================================================================================
# A — kapsam ve ayrıştırıcı
# ================================================================================================

def test_A1_kapsam_A0_rolunun_kurdugu_birim_ve_dropinleri_KAPSAR():
    kapsam = set(_kapsam())
    a0 = _a0_kaynaklari()
    assert a0, "A0 glob'ları hiçbir dosya çözmedi — yol yanlış, çivi kör"
    eksik = sorted(_goreli(p, KOK) for p in a0 - kapsam)
    assert not eksik, f"A0 rolünün kurduğu dosya taramanın DIŞINDA: {eksik}"
    assert CP_BIRIM.resolve() in kapsam and CP_DROPIN.resolve() in kapsam, (
        "hindsight-cp birimi ya da drop-in'i kapsamda değil — tarama kör")


def test_A2_her_service_en_az_bir_KOMUT_yonergesi_tasir():
    """Ayrıştırıcı pozitif kontrolü: yönergeler okunamasaydı B1 "ihlal yok" diye yanlış sebeple yeşil
    kalırdı. Her `.service` bir süreç doğurur; komut yönergesi okunamayan servis ayrıştırıcı kırığıdır."""
    servisler = [p for p in _kapsam() if p.suffix == ".service"]
    assert len(servisler) >= 20, f"beklenenden az servis: {len(servisler)} — tarama budaması yanlış"
    komutsuz = sorted(_goreli(p, KOK) for p in servisler
                      if not any(a in KOMUT_YONERGELERI
                                 for _, a, _ in _yonergeler(p.read_text(encoding="utf-8"))))
    assert not komutsuz, f"komut yönergesi okunamayan servis: {komutsuz}"


def test_A3_Exec_ile_baslayan_TANINMAYAN_yonerge_YOK():
    """`ExecStartpre=` gibi bir yazım hatası ya da yeni bir komut yönergesi sessizce taramanın dışına
    düşmesin: `Exec` önekli her anahtar ya komut kümesinde ya komut-olmayan kümede olmalı."""
    taninmayan = sorted({f"{_goreli(p, KOK)} · {a}" for p in _kapsam()
                         for _, a, _ in _yonergeler(p.read_text(encoding="utf-8"))
                         if a.startswith("Exec") and a not in KOMUT_YONERGELERI | KOMUT_OLMAYAN_EXEC})
    assert not taninmayan, f"tanınmayan Exec yönergesi: {taninmayan}"


# ================================================================================================
# B — kural (gerçek depo)
# ================================================================================================

def test_B1_komut_satirinda_SIR_degiskeni_GENISLEMESI_YOK():
    ihlaller, _ = _tara(_kapsam())
    assert not ihlaller, (
        "birim komut satırı SIR değişkenini genişletiyor — değer argv'ye girer (`ps`, "
        "`/proc/<pid>/cmdline`: makinedeki HER kullanıcı okur):\n"
        f"{_bicimle(ihlaller)}\n"
        "ÇARE: docker için değersiz `-e AD` (istemci değeri kendi ortamından alır); systemd-doğal süreç "
        "için LoadCredential; betik için ortamdan/dosyadan okuyan sarmalayıcı. Meşru durum: "
        "ARGV_ISTISNALARI'na gerekçesiyle.")


# ================================================================================================
# C — sır adı sınıfı: çapraz doğrulama ve bedel
# ================================================================================================

def _rotasyon_sonekleri() -> list[str]:
    m = re.search(r'^_SIR_ADI_SONEKLERI="([^"]*)"', ROTASYON.read_text(encoding="utf-8"), re.M)
    assert m, "sir_rotasyon.sh sır adı sözlüğü (_SIR_ADI_SONEKLERI) bulunamadı — çapraz doğrulama kör"
    return m.group(1).split()


def _envanter() -> dict:
    return yaml.safe_load(ENVANTER.read_text(encoding="utf-8"))


def _envanter_sir_adlari() -> set[str]:
    """Envanterin DÖRT bloğundaki bütün sır adları (yer tutucu `<AD>` atılır)."""
    e = _envanter()
    adlar: set[str] = set()
    for d in e["dosyalar"]:
        adlar |= {v["ad"] for v in d["degiskenler"] if v["sir"]}
    for k in e["rotasyon_kopyalari"]["kopyalar"]:
        adlar.add(k["sir"])
        if k.get("alan"):
            adlar.add(k["alan"])
        if k["tur"] in ("dosya", "url"):
            son = k["yol"].rsplit("/", 1)[-1]
            if re.fullmatch(r"[A-Z][A-Z0-9_]*", son):
                adlar.add(son)
    for v in e["vault_kv"]:
        adlar.add(v["ad"])
        kaynaklar = [v.get("kaynak"), *(v.get("kopya_kaynaklari") or [])]
        adlar |= {k["alan"] for k in kaynaklar if isinstance(k, dict) and k.get("alan")}
    for d in e["vault_dosyalar"]:
        for s in d["satirlar"]:
            adlar |= {s["alan"], s["sir"]}
    return {re.sub(r"<[^>]*>", "", a) for a in adlar}


def _envanter_sir_olmayan_adlar() -> set[str]:
    return {v["ad"] for d in _envanter()["dosyalar"] for v in d["degiskenler"] if not v["sir"]}


def test_C1_rotasyon_sozlugu_sinifin_ALTINDA():
    sonekler = _rotasyon_sonekleri()
    assert len(sonekler) >= 4, f"rotasyon sözlüğü beklenenden dar: {sonekler}"
    kacan = [s for s in sonekler if not _sir_adi_mi("ORNEK" + s)]
    assert not kacan, f"rotasyon sözlüğünün yakaladığı ad biçimi bu sınıfa UYMUYOR: {kacan}"


def test_C2_envanterin_BUTUN_sir_adlari_sinifin_ALTINDA():
    adlar = _envanter_sir_adlari()
    assert len(adlar) >= 20, f"envanterden beklenenden az sır adı türedi: {len(adlar)} — türetme kör"
    assert {"HINDSIGHT_CP_ACCESS_KEY", "HINDSIGHT_CP_DATAPLANE_API_KEY",
            "HINDSIGHT_API_DATABASE_URL", "OPENROUTER_AUTH"} <= adlar, "türetme bilinen adları kaçırıyor"
    kacan = sorted(a for a in adlar if not _sir_adi_mi(a))
    assert not kacan, (
        f"envanterde SIR olan ama bu sınıfa UYMAYAN ad: {kacan} — birim komut satırında genişlerse "
        "çivi görmez. SIR_AD_PARCALARI_OLCULEN'e ölçülmüş gerekçesiyle ekle.")


def test_C3_olculen_ek_parcalar_CURUMEZ_ve_gerekceli():
    """Her ölçülmüş ek parça, brief parçalarının KAÇIRDIĞI en az bir bilinen sır adını yakalar."""
    bilinen = _envanter_sir_adlari()
    for parca, gerekce in SIR_AD_PARCALARI_OLCULEN.items():
        assert len(gerekce) >= 20, f"{parca}: gerekçe kısa"
        yakalanan = [a for a in bilinen
                     if parca in a.upper() and not any(b in a.upper() for b in SIR_AD_PARCALARI_BRIEF)]
        assert yakalanan, f"{parca}: brief parçalarının kaçırdığı hiçbir bilinen adı yakalamıyor — çürük ek"


def test_C4_BEDEL_sir_olmayan_bilinen_adlar_suzgecten_GECMEZ():
    """Bedel yasası: süzgecin yanlış-pozitifi ölçülür. Depodaki birimlerin genişlettiği sır-olmayan
    adlar ve envanterin `sir: false` adları sır sayılmamalı (bugün 0 — ölçüldü 2026-09-25)."""
    depo_adlari = {ad for p in _kapsam()
                   for _, a, d in _yonergeler(p.read_text(encoding="utf-8")) if a in KOMUT_YONERGELERI
                   for _, ad in _genislemeler(d)}
    assert {"MERIDIAN_BIND_HOST", "MAINPID"} <= depo_adlari, (
        "pozitif kontrol: depodaki bilinen sır-olmayan genişlemeler okunamadı — ayrıştırıcı kör")
    olcum = (depo_adlari - _envanter_sir_adlari()) | _envanter_sir_olmayan_adlar()
    yanlis_pozitif = sorted(a for a in olcum if _sir_adi_mi(a))
    assert not yanlis_pozitif, f"sır olmayan ad sır sayılıyor (gürültü): {yanlis_pozitif}"


# ================================================================================================
# D — istisna sözlüğü hijyeni
# ================================================================================================

def test_D1_istisna_sozlugu_CURUMEZ_ve_GEREKCELI():
    _, kullanilan = _tara(_kapsam())
    for anahtar, gerekce in ARGV_ISTISNALARI.items():
        assert len(gerekce.strip()) >= 20, f"{anahtar}: gerekçe ≥20 karakter olmalı"
        assert anahtar in kullanilan, f"{anahtar}: istisna hiçbir oluşumu karşılamıyor — çürük beyan"


# ================================================================================================
# E — pozitif kontrol (sentetik birim)
# ================================================================================================

def _sentetik(kok: Path, govde: str, *, dropin: str | None = None) -> list[Path]:
    """Sentetik birim (+ drop-in) kurar ve kapsamı GERÇEK tarayıcıyla (`_kapsam`) bulur — tarayıcının
    drop-in dizinini tanıması da böylece her pozitif kontrolde sürülür."""
    (kok / "sentetik.service").write_text(govde, encoding="utf-8")
    beklenen = 1
    if dropin is not None:
        d = kok / "sentetik.service.d"
        d.mkdir()
        (d / "50-x.conf").write_text(dropin, encoding="utf-8")
        beklenen = 2
    dosyalar = _kapsam(kok)
    assert len(dosyalar) == beklenen, f"tarayıcı sentetik kapsamı bulamadı: {[p.name for p in dosyalar]}"
    return dosyalar


OTEN = {
    "systemd_kume": ("[Service]\nExecStart=/usr/bin/docker run -e X_TOKEN=${X_TOKEN} img\n",
                     None, ("ExecStart", "X_TOKEN", "systemd")),
    "systemd_ciplak_kelime": ("[Service]\nExecStart=/usr/bin/araç --anahtar $X_API_KEY\n",
                              None, ("ExecStart", "X_API_KEY", "systemd")),
    "varsayilanli_kume": ("[Service]\nExecStart=/bin/x ${X_SECRET:-yedek}\n",
                          None, ("ExecStart", "X_SECRET", "systemd")),
    "onekli_pre": ("[Service]\nExecStartPre=-/bin/x --parola=${PANO_PAROLA}\nExecStart=/bin/y\n",
                   None, ("ExecStartPre", "PANO_PAROLA", "systemd")),
    "devam_satiri": ("[Service]\nExecStart=/usr/bin/docker run \\\n  -e A=1 \\\n"
                     "  -e X_CREDENTIAL=${X_CREDENTIAL} \\\n  img\n",
                     None, ("ExecStart", "X_CREDENTIAL", "systemd")),
    "stop_yonergesi": ("[Service]\nExecStart=/bin/y\nExecStop=/bin/x ${X_PASSWORD}\n",
                       None, ("ExecStop", "X_PASSWORD", "systemd")),
    "kabuk_kume": ("[Service]\nExecStart=/bin/sh -c 'curl -H \"A: $${X_AUTH}\" http://h'\n",
                   None, ("ExecStart", "X_AUTH", "kabuk")),
    "kabuk_ciplak": ("[Service]\nExecStart=/bin/sh -c 'x --k \"$$Y_KEY\"'\n",
                     None, ("ExecStart", "Y_KEY", "kabuk")),
    "uclu_dolar": ("[Service]\nExecStart=/bin/x $$$X_TOKEN\n",
                   None, ("ExecStart", "X_TOKEN", "systemd")),
    "dropin_icinde": ("[Service]\nExecStart=/bin/y\n",
                      "[Service]\nExecStart=\nExecStart=/bin/x ${VT_DATABASE_URL}\n",
                      ("ExecStart", "VT_DATABASE_URL", "systemd")),
}


@pytest.mark.parametrize("durum", sorted(OTEN))
def test_E1_POZITIF_KONTROL_oten_bicimler(tmp_path, durum):
    govde, dropin, (yonerge, ad, bicim) = OTEN[durum]
    ihlaller, _ = _tara(_sentetik(tmp_path, govde, dropin=dropin), kok=tmp_path, istisnalar={})
    assert [(i.yonerge, i.ad, i.bicim) for i in ihlaller] == [(yonerge, ad, bicim)], _bicimle(ihlaller)


OTMEYEN = {
    "degersiz_e": "[Service]\nExecStart=/usr/bin/docker run -e X_TOKEN -e X_API_KEY img\n",
    "sir_olmayan_genisleme": "[Service]\nExecStart=/bin/x --host ${MERIDIAN_BIND_HOST} --port ${PORT}\n",
    "kabuk_sir_olmayan": "[Service]\nExecStart=/bin/sh -c 'x; rc=$$?; [ $$rc -le 1 ]'\n",
    "yorum_satiri": "[Service]\n# ExecStart=/bin/x ${X_TOKEN}\n; ExecStart=/bin/x $X_TOKEN\nExecStart=/bin/y\n",
    "komut_olmayan_yonergeler": ("[Service]\nEnvironment=A=${X_TOKEN}\nEnvironmentFile=/etc/x/X_TOKEN\n"
                                 "LoadCredential=X_TOKEN:/etc/x/X_TOKEN\nExecStart=/bin/y\n"),
    "dolarsiz_ad": "[Service]\nExecStart=/bin/x --dosya /etc/meridian/X_TOKEN --ad X_SECRET\n",
    "ciftli_dolar_pid": "[Service]\nExecStart=/bin/sh -c 'echo $$$$ > /run/x.pid'\n",
    "komut_ikamesi": "[Service]\nExecStart=/bin/sh -c 'x-$$(date +%%F)'\n",
}


@pytest.mark.parametrize("durum", sorted(OTMEYEN))
def test_E2_POZITIF_KONTROL_otmeyen_bicimler(tmp_path, durum):
    ihlaller, _ = _tara(_sentetik(tmp_path, OTMEYEN[durum]), kok=tmp_path, istisnalar={})
    assert not ihlaller, _bicimle(ihlaller)


def test_E3_istisna_BASTIRIR_ve_KULLANILDI_sayilir(tmp_path):
    dosyalar = _sentetik(tmp_path, OTEN["systemd_kume"][0])
    ihlaller, kullanilan = _tara(dosyalar, kok=tmp_path,
                                 istisnalar={("sentetik.service", "X_TOKEN"): "sentetik gerekçe metni ≥20 karakter"})
    assert not ihlaller and kullanilan == {("sentetik.service", "X_TOKEN")}
    # aynı ad BAŞKA dosyada: istisna onu kapsamaz
    ihlaller, _ = _tara(dosyalar, kok=tmp_path, istisnalar={("baska.service", "X_TOKEN"): "x" * 20})
    assert [i.ad for i in ihlaller] == ["X_TOKEN"]


# ================================================================================================
# F — çıktı disiplini
# ================================================================================================

def test_F1_ihlal_kaydi_DEGER_ve_SATIR_METNI_tasimaz(tmp_path):
    isaretci = "SENTETIK-DEGER-v554-" + "a" * 12
    govde = f"[Service]\nExecStart=/bin/x --bayrak={isaretci} -e X_TOKEN=${{X_TOKEN}}\n"
    ihlaller, _ = _tara(_sentetik(tmp_path, govde), kok=tmp_path, istisnalar={})
    assert len(ihlaller) == 1
    metin = str(ihlaller) + repr(ihlaller) + _bicimle(ihlaller)
    sizdi = isaretci in metin
    esittir = "=" in metin
    assert not sizdi, "ihlal çıktısı satırdaki değeri taşıyor (yalnız AD basılır)"
    assert not esittir, "ihlal çıktısı `=` taşıyor — satır metni sızıyor"
    assert "sentetik.service" in metin and "X_TOKEN" in metin and "ExecStart" in metin
    assert {f.name for f in dataclasses.fields(Ihlal)} == {"kaynak", "yonerge", "ad", "bicim"}


# ================================================================================================
# G — TSK-226 örneği: hindsight-cp
# ================================================================================================

#: Sır olmayan sabitler — TSK-226 bunlara DOKUNMAZ (Rol-1 kararı: "aynen kalır"). Meşru bir değişiklik
#: bu sözlüğü de değiştirir; hata iletisi yalnız AD basar.
CP_SABITLERI = {
    "HINDSIGHT_CP_HOSTNAME": "localhost",
    "HINDSIGHT_CP_PORT": "9999",
    "HOSTNAME": "localhost",
    "PORT": "9999",
    "HINDSIGHT_CP_DATAPLANE_API_URL": "http://127.0.0.1:8888",
}


def _cp_execstart() -> list[str]:
    komutlar = [d for _, a, d in _yonergeler(CP_BIRIM.read_text(encoding="utf-8")) if a == "ExecStart" and d]
    assert len(komutlar) == 1, f"hindsight-cp ExecStart sayısı {len(komutlar)}"
    return shlex.split(komutlar[0])


def _docker_e(jetonlar: list[str]) -> list[str]:
    return [jetonlar[i + 1] for i, j in enumerate(jetonlar[:-1]) if j in ("-e", "--env")]


def _cp_envanter_sirlari() -> set[str]:
    d = next(x for x in _envanter()["dosyalar"] if x["yol"] == CP_ENV)
    return {v["ad"] for v in d["degiskenler"] if v["sir"]}


def test_G1_CP_sirlari_DEGERSIZ_e_AD_ile_gecer():
    e = _docker_e(_cp_execstart())
    sirli = [a for a in e if _sir_adi_mi(a.split("=", 1)[0])]
    degerli = sorted(a.split("=", 1)[0] for a in sirli if "=" in a)
    assert not degerli, f"sır `-e AD=…` biçiminde — değer argv'ye girer: {degerli}"
    assert sorted(sirli) == sorted(_cp_envanter_sirlari()), (
        "ExecStart'ın değersiz geçirdiği sır adları envanterin .env-cp sırlarıyla aynı değil")


def test_G2_CP_sir_olmayan_sabitler_AYNEN():
    e = [a for a in _docker_e(_cp_execstart()) if not _sir_adi_mi(a.split("=", 1)[0])]
    olculen = dict(a.split("=", 1) for a in e if "=" in a)
    degersiz = sorted(a for a in e if "=" not in a)
    assert not degersiz, f"sır olmayan değişken değersiz verilmiş: {degersiz}"
    farkli = sorted(ad for ad in CP_SABITLERI.keys() | olculen.keys()
                    if CP_SABITLERI.get(ad) != olculen.get(ad))
    assert not farkli, f"sabit değişmiş/eksik/fazla (yalnız AD): {farkli}"


def test_G3_CP_ExecStart_env_file_TASIMAZ():
    """Rol-1 kararı: `--env-file` EKLENMEZ — değersiz `-e AD` değeri systemd'nin iki EnvironmentFile ile
    doldurduğu istemci ortamından alır; ikinci kanal ExecStart kopyası (drop-in'de ExecStart= sıfırla +
    yeniden yaz) gerektirirdi."""
    jetonlar = _cp_execstart()
    assert not [j for j in jetonlar if j == "--env-file" or j.startswith("--env-file=")]


def _cp_environment_files() -> list[str]:
    """Birim + drop-in'ler systemd sırasıyla; boş atama listeyi SIFIRLAR."""
    kaynaklar = [CP_BIRIM, *sorted(CP_DROPIN.parent.glob("*.conf"), key=lambda p: p.name)]
    liste: list[str] = []
    for p in kaynaklar:
        for _, a, d in _yonergeler(p.read_text(encoding="utf-8")):
            if a == "EnvironmentFile":
                liste = [] if not d else [*liste, d]
    return liste


def test_G4_kasa_yan_dosyasi_ORTAM_yoluyla_KAZANIR():
    """Vault düzeni (`50-vault-yan-dosya.conf`) aynen çalışır: yan dosya ASIL dosyadan SONRA okunur
    (aynı anahtarda sonraki kazanır), opsiyoneldir (`-`), drop-in komut satırına DOKUNMAZ ve kasanın
    render ettiği adlar ExecStart'ın değersiz geçirdiği adlarla BİREBİR aynıdır — fazlası konteynere
    ulaşmaz, eksiği eski kanalda kalır."""
    assert _cp_environment_files() == [CP_ENV, "-" + CP_ENV_VAULT]
    assert not [a for _, a, _ in _yonergeler(CP_DROPIN.read_text(encoding="utf-8")) if a in KOMUT_YONERGELERI]
    yan = next(d for d in _envanter()["vault_dosyalar"] if d["yol"] == CP_ENV_VAULT)
    degersiz = {a for a in _docker_e(_cp_execstart()) if "=" not in a}
    assert {s["alan"] for s in yan["satirlar"]} == degersiz


# ---- systemd + docker birleşimi — MODEL (sentetik değerler; hiçbiri basılmaz) -------------------
# systemd: EnvironmentFile'lar sırayla, aynı anahtarda sonraki kazanır; `-` önekli yok dosya atlanır;
# komut satırında `$$` → `$`, `${AD}` → değer (tanımsız → boş), tek başına `$AD` kelimesi → değer.
# docker CLI (docker run belgesi, `--env`): `-e AD=DEGER` → DEGER; `-e AD` → değer İSTEMCİNİN kendi
# ortamından, orada yoksa konteynere hiç konmaz. Model A1'deki docker'ı ÖLÇMEZ; birimin kompozisyonunu
# (hangi değer hangi kanaldan) ölçer.

def _env_dosyasi_oku(p: Path) -> dict[str, str]:
    cikti: dict[str, str] = {}
    for satir in p.read_text(encoding="utf-8").splitlines():
        s = satir.strip()
        if not s or s[0] in "#;" or "=" not in s:
            continue
        k, v = s.split("=", 1)
        cikti[k.strip()] = v.strip().strip('"').strip("'")
    return cikti


def _systemd_ortami(env_dosyalari: list[str], kok: Path) -> dict[str, str]:
    ortam: dict[str, str] = {}
    for girdi in env_dosyalari:
        istege_bagli = girdi.startswith("-")
        yol = kok / Path(girdi.lstrip("-")).name
        if not yol.exists():
            assert istege_bagli, f"zorunlu EnvironmentFile yok: {Path(girdi.lstrip('-')).name}"
            continue
        ortam.update(_env_dosyasi_oku(yol))
    return ortam


def _systemd_argv(jetonlar: list[str], ortam: dict[str, str]) -> list[str]:
    argv: list[str] = []
    for j in jetonlar:
        tek = re.fullmatch(r"\$([A-Za-z_][A-Za-z0-9_]*)", j)
        if tek:
            argv.extend(ortam.get(tek.group(1), "").split())
            continue
        argv.append(re.sub(r"\$\$|\$\{([A-Za-z_][A-Za-z0-9_]*)\}",
                           lambda m: "$" if m.group(0) == "$$" else ortam.get(m.group(1), ""), j))
    return argv


def _konteyner_ortami(argv: list[str], istemci_ortami: dict[str, str]) -> dict[str, str]:
    cikti: dict[str, str] = {}
    for a in _docker_e(argv):
        if "=" in a:
            k, v = a.split("=", 1)
            cikti[k] = v
        elif a in istemci_ortami:
            cikti[a] = istemci_ortami[a]
    return cikti


def _cp_sahnesi(tmp_path: Path, *, kasa: bool) -> dict[str, dict[str, str]]:
    adlar = sorted(_cp_envanter_sirlari())
    (tmp_path / Path(CP_ENV).name).write_text(
        "".join(f"{a}=sentetik-eski-{i}\n" for i, a in enumerate(adlar)), encoding="utf-8")
    if kasa:
        (tmp_path / Path(CP_ENV_VAULT).name).write_text(
            "".join(f"{a}=sentetik-kasa-{i}\n" for i, a in enumerate(adlar)), encoding="utf-8")
    return {"eski": {a: f"sentetik-eski-{i}" for i, a in enumerate(adlar)},
            "kasa": {a: f"sentetik-kasa-{i}" for i, a in enumerate(adlar)}}


@pytest.mark.parametrize("kasa", [True, False], ids=["kasa_var", "kasa_yok_geri_alim"])
def test_G5_MODEL_argv_DEGERSIZ_konteyner_degeri_DOGRU_kanaldan(tmp_path, kasa):
    beklenen = _cp_sahnesi(tmp_path, kasa=kasa)
    ortam = _systemd_ortami(_cp_environment_files(), tmp_path)
    argv = _systemd_argv(_cp_execstart(), ortam)
    konteyner = _konteyner_ortami(argv, ortam)
    argv_metni = " ".join(argv)
    sizan = sorted(a for d in beklenen.values() for a, v in d.items() if v in argv_metni)
    assert not sizan, f"sentetik sır değeri argv'de (yalnız AD): {sizan}"
    kaynak = beklenen["kasa" if kasa else "eski"]
    yanlis = sorted(a for a, v in kaynak.items() if konteyner.get(a) != v)
    assert not yanlis, f"konteynere yanlış kanaldan/eksik ulaşan sır (yalnız AD): {yanlis}"
    sabit_farki = sorted(a for a, v in CP_SABITLERI.items() if konteyner.get(a) != v)
    assert not sabit_farki, f"sabit konteynere ulaşmadı (yalnız AD): {sabit_farki}"


def test_G6_MODEL_POZITIF_KONTROL_eski_bicim_argvye_SIZDIRIR(tmp_path):
    """Modelin kendisi ölçülür: sızıntıyı göremeyen bir model G5'i yanlış sebeple yeşil tutardı. Eski
    biçim (`-e AD=${AD}`) aynı sahnede argv'ye DEĞER koyar ve B kuralı onu öter."""
    beklenen = _cp_sahnesi(tmp_path, kasa=True)
    eski = [f"{a}=${{{a}}}" if a in beklenen["kasa"] else a for a in _cp_execstart()]
    ortam = _systemd_ortami(_cp_environment_files(), tmp_path)
    argv_metni = " ".join(_systemd_argv(eski, ortam))
    sizan = sorted(a for a, v in beklenen["kasa"].items() if v in argv_metni)
    assert sizan == sorted(beklenen["kasa"]), "model eski biçimin sızıntısını GÖRMÜYOR — G5 kör"
    sahne = tmp_path / "birim"
    sahne.mkdir()
    govde = "[Service]\nExecStart=" + " ".join(eski) + "\n"
    ihlaller, _ = _tara(_sentetik(sahne, govde), kok=sahne, istisnalar={})
    assert sorted(i.ad for i in ihlaller) == sorted(beklenen["kasa"]), _bicimle(ihlaller)
