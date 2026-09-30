"""v601 — BOT AĞ GEÇİDİ BİRİMİ (konuşan filo Parça 1b G3 Task 2, 2026-09-30).

`meridian-botlar.service` tek bir Hermes ağ geçidini AYRI bir Hermes kökünde çoklu profil kipinde koşar; sohbet
profilleri `/p/<ad>/` altında sunulur. Kökün ve profillerin dosyaları üretilmiştir (`ops/sohbet_profili_uret.py`,
depo aynası `deploy/hermes/sohbet/`) ve A0 rolü onları köke kopyalar. Bu dosya ÜÇ şeyi çiviler:

  * BİRİM — `Type=simple`, `User=ubuntu`, Rol-1'in A1'de ölçtüğü ExecStart, durdurma (`KillMode=mixed` +
    `TimeoutStopSec=30`), `Restart=on-failure`, `[Install]` VAR; `ReadWritePaths` TAM OLARAK iki yol (MCP
    çocuğunun yazdığı `/opt/meridian` + `-` önekli Hermes kökü). CREDENTIAL YOK — BEYANLI ERTELEME (Rol-1 kararı
    2026-09-30, Tur 2): MCP `bot_hafizasi_ara`nın Hindsight kiracı anahtarı drop-in'i G3b sır diliminde rotasyon
    tablosuyla (`deploy/oracle-a1/sir_rotasyon.sh` — uzun ömürlü tablo + restart haritası, "yalnız aktifse yeniden
    başlat") TEK dilimde gelir; bugün birimde de drop-in'de de `*Credential*` yönergesi YOKTUR. G3b drop-in'i eklediği
    gün `test_credential_G3b_dilimine_ertelendi_bugun_hicbir_credential_yok` ve v447 P6 birlikte kırmızıya döner ve
    bilinçli güncellenir.
  * TEK KAYNAK — üretecin üç sabiti (`BOT_BIRIMI`, `KOK_DIZIN`, `BOT_KUM_HAVUZU`) birim dosyasının ADIYLA, birimin
    `HERMES_HOME`/`HERMES_WRITE_SAFE_ROOT` değerleriyle ve A0 rolünün dizin/kopya hedefleriyle eşittir. Birim
    yeniden adlandırılıp credential yolu unutulursa `bot_hafizasi_ara` SESSİZCE "credential yok" döner (G3 planı
    Review Focus 3); kum havuzu ayrışırsa birim var olmayan bir dizine kısıtlanır.
  * A0 ROLÜ — birim kopyalanır ama ETKİN EDİLMEZ (`etkin_birimler`de yok; dagit bakım penceresinin adayları
    değişmez); sohbet dizinleri AYRI değişkenlerle (`bot_adlari`na eklenmeden) 0700 ubuntu kurulur ve ata dizin
    torundan önce gelir; kopyalanan dosya kümesi üretecin çıktısına EŞİTTİR (eksik de fazla da kırmızı) ve
    görev gövdesinde `.env` HİÇ geçmez (profil `.env`leri rotasyon aracınındır, rol onlara dokunmaz).

CANLIYA DOKUNMAZ: yalnız depo dosyaları okunur; ansible koşulmaz — görevler YAML olarak ayrıştırılır, şablonlar
v451'in Jinja ortamıyla çözülür. Numara v601 (v600 TSK-257'ye ayrıldı; ana checkout + worktree'de boş, 2026-09-30).
"""
from __future__ import annotations

import glob
import pathlib
import posixpath
import re

import pytest
import yaml

from meridian import kadro
from tests.conftest import betikten_modul_yukle
from tests.test_ansible_a0_v451 import _dongu_ogeleri, _jinja_ortami, _yol_coz
from tests.test_sertlesmis_birim_yazim_yolu_v553 import _kapsar, _yonergeler

KOK = pathlib.Path(__file__).resolve().parent.parent
BIRIM_DIZINI = KOK / "deploy" / "oracle-a1"
ANSIBLE = KOK / "deploy" / "ansible"
ROL = ANSIBLE / "roles" / "meridian_a1"
DEFAULTS = ROL / "defaults" / "main.yml"
DIZINLER = ROL / "tasks" / "dizinler.yml"
HERMES_YML = ROL / "tasks" / "hermes.yml"
DAGIT_VARS = ANSIBLE / "vars" / "dagit_vars.yml"
#: Rol-1'in A1'de ölçtüğü çağrı biçimi (2026-09-30): `~/.local/bin/hermes` ubuntu sahipli sarmalayıcı;
#: `--accept-hooks` `gateway` alt ayrıştırıcısının bayrağıdır ve `run`dan ÖNCE gelir.
EXECSTART = "/home/ubuntu/.local/bin/hermes gateway --accept-hooks run"


def _ur():
    return betikten_modul_yukle(KOK / "ops/sohbet_profili_uret.py", "sohbet_profili_uret_v601")


def _birim_yolu() -> pathlib.Path:
    return BIRIM_DIZINI / _ur().BOT_BIRIMI


def _bolum(yol: pathlib.Path, bolum: str) -> list[tuple[str, str]]:
    """Bir birim/drop-in dosyasının `bolum` yönergeleri (yorumlar ayıklanmış, `\\` devamları birleşik)."""
    return [(a, d) for b, a, d in _yonergeler(yol.read_text(encoding="utf-8")) if b == bolum]


def _tek(yol: pathlib.Path, bolum: str, anahtar: str) -> str:
    degerler = [d for a, d in _bolum(yol, bolum) if a == anahtar]
    assert len(degerler) == 1, f"{yol.name} [{bolum}] {anahtar}: tek atama beklenirdi, {degerler!r}"
    return degerler[0]


def _ortam(yol: pathlib.Path) -> dict[str, str]:
    cikti: dict[str, str] = {}
    for anahtar, deger in _bolum(yol, "Service"):
        if anahtar == "Environment":
            ad, _, deg = deger.partition("=")
            cikti[ad] = deg
    return cikti


def _defaults() -> dict:
    return yaml.safe_load(DEFAULTS.read_text(encoding="utf-8"))


def _baglam() -> dict:
    """Rol değişkenleri + dagit değişkenleri, `playbook_dir` depo içindeki ansible dizinine bağlı."""
    baglam = dict(_defaults())
    baglam.update(yaml.safe_load(DAGIT_VARS.read_text(encoding="utf-8")) or {})
    baglam["playbook_dir"] = str(ANSIBLE)
    return baglam


def _coz(deger, baglam: dict, item=None) -> str:
    """Şablonu değişmeyene dek çözer (defaults kendi içinde şablon taşır: `{{ repo_kok }}/…`)."""
    ortam = _jinja_ortami()
    metin = str(deger)
    for _ in range(6):
        yeni = ortam.from_string(metin).render(**baglam, item=item)
        if yeni == metin:
            break
        metin = yeni
    assert "{{" not in metin, f"şablon çözülemedi: {deger!r} → {metin!r}"
    return metin


def _dizin_gorevleri() -> dict[str, dict]:
    """dizinler.yml `file state=directory` görevlerinin ÇÖZÜLMÜŞ hâli: yol → sahip/grup/mod/sıra/döngü kaynağı.

    Sıra `(görev no, öğe no)`dur: ansible döngü öğelerini sırayla işler, görevleri dosya sırasıyla."""
    baglam = _baglam()
    sonuc: dict[str, dict] = {}
    for gno, gorev in enumerate(yaml.safe_load(DIZINLER.read_text(encoding="utf-8"))):
        arg = gorev.get("ansible.builtin.file")
        if not isinstance(arg, dict) or arg.get("state") != "directory":
            continue
        ogeler = _dongu_ogeleri(gorev, baglam)
        for ono, oge in enumerate(ogeler if ogeler is not None else [None]):
            item = _coz(oge, baglam) if isinstance(oge, str) else oge
            yol = posixpath.normpath(_coz(arg["path"], baglam, item))
            sonuc[yol] = {"owner": _coz(arg.get("owner", ""), baglam), "group": _coz(arg.get("group", ""), baglam),
                          "mode": str(arg.get("mode", "")), "sira": (gno, ono), "dongu": gorev.get("loop")}
    return sonuc


def _sohbet_kopyalari() -> tuple[set[tuple[str, str]], list[dict]]:
    """hermes.yml'de hedefi Hermes bot köküne düşen `copy` görevlerinin (depo-göreli kaynak, etkin hedef) çiftleri
    ve o görevlerin argümanları. Hedef `/` ile bitiyorsa copy modülü dosyayı o dizine kaynağın adıyla yazar."""
    u, baglam = _ur(), _baglam()
    ciftler: set[tuple[str, str]] = set()
    gorevler: list[dict] = []
    for gorev in yaml.safe_load(HERMES_YML.read_text(encoding="utf-8")):
        arg = gorev.get("ansible.builtin.copy")
        if not isinstance(arg, dict):
            continue
        ogeler = _dongu_ogeleri(gorev, baglam)
        for oge in ogeler if ogeler is not None else [None]:
            item = _coz(oge, baglam) if isinstance(oge, str) else oge
            hedef = _coz(arg["dest"], baglam, item)
            if not (hedef == u.KOK_DIZIN or hedef.startswith(u.KOK_DIZIN + "/")):
                continue
            kaynak = pathlib.Path(_coz(_yol_coz(arg["src"]), baglam, item)).resolve()
            etkin = posixpath.join(hedef, kaynak.name) if hedef.endswith("/") else hedef
            ciftler.add((str(kaynak.relative_to(KOK)), posixpath.normpath(etkin)))
            if arg not in gorevler:
                gorevler.append(arg)
    return ciftler, gorevler


# =================================================================================================
# BİRİM — yönergeler
# =================================================================================================

def test_birim_dosyasi_uretecin_adiyla_depoda():
    # `BOT_BIRIMI` credential yolunu TÜRETİR (`/run/credentials/<ad>`): dosya adı ayrışırsa systemd başka bir
    # dizine yazar ve MCP araçları sessizce "credential yok" döner.
    u = _ur()
    assert _birim_yolu().is_file(), f"deploy/oracle-a1/{u.BOT_BIRIMI} yok"
    assert u.BOT_CREDENTIAL_DIZINI == f"/run/credentials/{_birim_yolu().name}"


@pytest.mark.parametrize("anahtar, beklenen", [
    ("Type", "simple"),
    ("User", "ubuntu"),
    ("ExecStart", EXECSTART),
    # Parça 0 v3: ağ geçidi SIGTERM'i yok saydı → SIGKILL gerekti. `mixed`: SIGTERM ana sürece, kalan
    # çocuklara (MCP stdio süreçleri) SIGKILL; tavan G3c'de ölçülür.
    ("KillMode", "mixed"),
    ("TimeoutStopSec", "30"),
    ("Restart", "on-failure"),
    ("RestartSec", "10"),
], ids=lambda x: x if x in {"Type", "User", "ExecStart", "KillMode", "TimeoutStopSec", "Restart", "RestartSec"} else "deger")
def test_birim_service_yonergesi(anahtar, beklenen):
    assert _tek(_birim_yolu(), "Service", anahtar) == beklenen


def test_birim_ortami_uretec_sabitleriyle_ayni():
    u, ortam = _ur(), _ortam(_birim_yolu())
    assert ortam.get("HERMES_HOME") == u.KOK_DIZIN
    assert ortam.get("HERMES_WRITE_SAFE_ROOT") == u.BOT_KUM_HAVUZU


def test_readwritepaths_tam_olarak_mcp_agaci_ve_onekli_hermes_koku():
    # `/opt/meridian`: MCP çocuğunun yazımları (onay kaydı, kilitler, olay defteri, iş istekleri) + ortak kum havuzu.
    # `-<kök>`: Hermes kökü, A0 kurmadan yoktur — öneksiz yol birimi reddettirirdi. Başka yol AÇILMAZ (ana `~/.hermes`
    # açılsaydı rapor profillerinin duruşu ve model anahtarları bu süreçten yazılabilir olurdu).
    u = _ur()
    rwp = _tek(_birim_yolu(), "Service", "ReadWritePaths").split()
    assert rwp == ["/opt/meridian", f"-{u.KOK_DIZIN}"], rwp
    assert _kapsar(rwp, u.KOK_DIZIN) and _kapsar(rwp, u.BOT_KUM_HAVUZU)


def test_baglam_dizini_kok_terminal_cwd_kum_havuzu_birim_ve_a0_ile_ayni():
    # GİZLİLİK KORUMASI — YÜK TAŞIYAN EKSEN (G3 dal sonu I1; A1 Hermes v0.19.0 Rol-1 ölçümü, yerel v0.18.2 aynı): ağ
    # geçidi bağlam dosyalarını (`AGENTS.md`/`CLAUDE.md`…) `TERMINAL_CWD`den arar ve onu açılışta kök config'in
    # `terminal.cwd`sinden köprüler; yoksa `MESSAGING_CWD`, yoksa ev dizini `/home/ubuntu`. Dağıtılan kök config'te
    # değer ortak kum havuzudur — A0'nun kurduğu BOŞ dizin, birimin yazma kökü ile AYNI yol.
    u, baglam = _ur(), _baglam()
    kok = yaml.safe_load((KOK / u.SOHBET_EV / "config.yaml").read_text(encoding="utf-8"))
    cwd = (kok.get("terminal") or {}).get("cwd")
    assert cwd == u.BOT_KUM_HAVUZU, cwd
    assert cwd == _ortam(_birim_yolu()).get("HERMES_WRITE_SAFE_ROOT")
    assert cwd == _coz(baglam["sohbet_kum_havuzu"], baglam) and cwd in _dizin_gorevleri()


def test_calisma_dizini_kok_opt_meridian_degil():
    # İKİNCİ KATMAN (Tur 3 inceleme M1; eksen G3 dal sonu I1'de düzeltildi): bağlam dizinini `terminal.cwd` belirler
    # (v0.19 ölçümü, üstteki çivi) — ama o dizin YOKSA Hermes bağlam keşfini süreç cwd'sine (`WorkingDirectory`)
    # düşürür. `/opt/meridian`de `CLAUDE.md`/`AGENTS.md` var (A1 host'u, ssh yolu, dağıtım disiplini); kardeş
    # birimlerin normu `/opt/meridian` olduğundan bir "tutarlılık" düzenlemesi bu ikinci katmanı sessizce açardı
    # (brifing birimindeki emsal v330).
    deger = _tek(_birim_yolu(), "Service", "WorkingDirectory")
    assert deger == "/" and deger != "/opt/meridian", deger


def test_after_kapi_ve_hafiza_birimlerini_siralar_ama_bagimlilik_kurmaz():
    # Tur 3, inceleme M5: model kapısı ve hafıza açılışta ağ geçidinden ÖNCE kalksın (ilk istekler bağlantı hatası
    # almasın). Adlar depodaki birim DOSYALARINDAN türer (rolün A1'e kurduğu adlar). Yalnız SIRALAMA: o birimlerden
    # birinin durması ağ geçidini düşürmemeli — `Wants=`/`Requires=`/`BindsTo=`/`Requisite=`/`PartOf=`de YOK.
    adlar = {p.name for desen in ("deploy/apisix/apisix.service", "deploy/hindsight/hindsight-api.service")
             for p in KOK.glob(desen)}
    assert adlar == {"apisix.service", "hindsight-api.service"}, adlar
    unit = _bolum(_birim_yolu(), "Unit")
    after = {ad for a, d in unit if a == "After" for ad in d.split()}
    assert adlar <= after, after
    bagimlilik = {ad for a, d in unit if a in {"Wants", "Requires", "BindsTo", "Requisite", "PartOf"}
                  for ad in d.split()}
    assert not adlar & bagimlilik, bagimlilik


def test_baslatma_siniri_kalici_arizayi_failed_e_dusurur():
    # G4 Görev 3 Tur 3 (görev incelemesi M-2, Rol-1 kararı): `Restart=on-failure` + `RestartSec=10` ile systemd'nin
    # varsayılan başlatma sınırı (5 / 10 sn) ASLA dolmaz — kalıcı bir arıza (bozuk kök config, eksik ikili) birimi `failed`e
    # düşürmeden sonsuz yeniden başlatır (görünmez arıza). 300 sn'de 5 başarısız başlatma → `failed`. Sınırın ETKİLİ olması
    # için `Burst × RestartSec` pencereye sığmalı. Telegram dinleyicisinde eşi v602.
    aralik = int(_tek(_birim_yolu(), "Unit", "StartLimitIntervalSec"))
    patlama = int(_tek(_birim_yolu(), "Unit", "StartLimitBurst"))
    assert (aralik, patlama) == (300, 5)
    assert patlama * int(_tek(_birim_yolu(), "Service", "RestartSec")) < aralik
    assert not [a for a, _ in _bolum(_birim_yolu(), "Service") if a.startswith("StartLimit")]


def test_install_bolumu_var_multi_user():
    # Uzun ömürlü servis: `[Install]` var ki ayrı değişikliğin `systemctl enable`ı çalışsın (enable BU turda yok).
    assert _tek(_birim_yolu(), "Install", "WantedBy") == "multi-user.target"


# =================================================================================================
# CREDENTIAL — G3b sır dilimine BEYANLI olarak ertelendi (Rol-1 kararı 2026-09-30, Tur 2)
# =================================================================================================

def _credential_yonergeleri(birim: pathlib.Path) -> list[tuple[str, str, str]]:
    """Birim dosyası + yanındaki `<birim>.d/*.conf` drop-in'lerinde adı `Credential` içeren yönergeler: (kaynak dosya
    adı, anahtar, değer). `LoadCredential` · `LoadCredentialEncrypted` · `SetCredential*` · `ImportCredential` aynı
    sınıftır — sırrı birime taşıyan her yönerge."""
    kaynaklar = [birim, *sorted((birim.parent / f"{birim.name}.d").glob("*.conf"), key=lambda p: p.name)]
    return [(k.name, a, d) for k in kaynaklar for b, a, d in _yonergeler(k.read_text(encoding="utf-8"))
            if b == "Service" and "Credential" in a]


def test_credential_G3b_dilimine_ertelendi_bugun_hicbir_credential_yok():
    # MCP `bot_hafizasi_ara`nın Hindsight kiracı anahtarı drop-in'i G3b sır diliminde `sir_rotasyon.sh` tablosuyla
    # (uzun ömürlü tablo + restart haritası, "yalnız aktifse yeniden başlat") TEK dilimde gelir: rotasyon tablosu
    # olmadan eklenen bir `LoadCredential=` rotasyondan sonra ESKİ değerde kalırdı (v447 P6'nın yakaladığı sınıf). O
    # güne dek araç "credential yok" döner ve birim zaten etkin değil. Bu çivi G3b drop-in'i eklediği gün KIRMIZIYA
    # döner ve v447 P6 ile birlikte BİLİNÇLİ güncellenir — erteleme sessizce "yapıldı"ya dönüşmesin.
    assert _credential_yonergeleri(_birim_yolu()) == []


def test_credential_denetcisi_birimi_ve_dropini_gorur(tmp_path):
    # POZİTİF KONTROL: yukarıdaki boş liste kör bir denetçinin boşluğu olmasın. Depoda bu birimin drop-in dizini
    # bugün YOK — drop-in dalı yalnız burada, sentetik birimle ısırtılır (yorum satırı yönerge sayılmaz).
    birim = tmp_path / "ornek.service"
    birim.write_text("[Service]\nType=simple\nLoadCredential=A:/etc/a\n", encoding="utf-8")
    (tmp_path / "ornek.service.d").mkdir()
    (tmp_path / "ornek.service.d" / "54-x.conf").write_text(
        "# LoadCredential=YORUM:/etc/y\n[Service]\nLoadCredential=B:/etc/b\n", encoding="utf-8")
    assert _credential_yonergeleri(birim) == [("ornek.service", "LoadCredential", "A:/etc/a"),
                                              ("54-x.conf", "LoadCredential", "B:/etc/b")]


# =================================================================================================
# A0 ROLÜ — kopya evet, etkinleştirme hayır
# =================================================================================================

def test_birim_rolun_kaynaklarinda():
    birimler = {pathlib.Path(p).resolve() for desen in _defaults()["birim_kaynaklari"]
                for p in glob.glob(_yol_coz(desen))}
    assert _birim_yolu().resolve() in birimler


def test_birim_etkin_edilmez_ve_bakim_penceresine_girmez():
    # A0 kuralı: uzun ömürlü birim AYRI değişiklikle etkin olur (Vault/telemetri emsali) — G3c test-ateşlemesinden
    # sonra. dagit'in bakım penceresi (`birim_adaylari`, v452 A3b DONUK) bu birimi durdurup başlatmaz.
    u, baglam = _ur(), _baglam()
    assert u.BOT_BIRIMI not in baglam["etkin_birimler"]
    taban = u.BOT_BIRIMI.removesuffix(".service")
    assert not {taban, u.BOT_BIRIMI} & set(baglam["birim_adaylari"])


def test_a0_degiskenleri_uretec_sabitleriyle_ayni():
    u, baglam = _ur(), _baglam()
    assert _coz(baglam["sohbet_kok_dizini"], baglam) == u.KOK_DIZIN
    assert _coz(baglam["sohbet_kum_havuzu"], baglam) == u.BOT_KUM_HAVUZU
    # Birimin kullanıcısı dizinlerin sahibidir — ayrışırsa birim kendi kökine SESSİZCE yazamaz.
    assert _coz(baglam["meridian_kullanici"], baglam) == _tek(_birim_yolu(), "Service", "User")


def test_sohbet_profil_adlari_depo_dizinleri_ve_kadroyla_esit():
    # Elle liste (rol envanter okumaz) — ama iki yönlü eşit: depo aynasının profil dizinleri ve kadronun aktif botları.
    # `bot_adlari` (rapor kum havuzları + rapor profil raporu) sohbete KARIŞMAZ.
    u, d = _ur(), _defaults()
    ayna = sorted(p.name for p in (KOK / u.SOHBET_KOK).iterdir() if p.is_dir())
    assert sorted(d["sohbet_profil_adlari"]) == ayna == sorted(b.ad for b in kadro.aktif_botlar())
    assert "sohbet" not in d["bot_adlari"]


def test_dizin_gorevleri_kum_havuzu_kok_ve_profiller_0700_birim_kullanicisi():
    u, d, baglam = _ur(), _defaults(), _baglam()
    kullanici = _coz(baglam["meridian_kullanici"], baglam)
    beklenen = [u.BOT_KUM_HAVUZU, u.KOK_DIZIN, f"{u.KOK_DIZIN}/profiles"]
    for ad in d["sohbet_profil_adlari"]:
        beklenen += [f"{u.KOK_DIZIN}/profiles/{ad}", f"{u.KOK_DIZIN}/profiles/{ad}/hindsight"]
    gorevler = _dizin_gorevleri()
    eksik = [y for y in beklenen if y not in gorevler]
    assert not eksik, f"dizinler.yml bu dizinleri kurmuyor: {eksik}"
    for yol in beklenen:
        g = gorevler[yol]
        assert (g["owner"], g["group"], g["mode"]) == (kullanici, kullanici, "0700"), (yol, g)
        # Rapor listesi (`bot_adlari`) üzerinden dönen bir görev sohbet dizinini kuramaz — liste AYRI.
        assert g["dongu"] != "{{ bot_adlari }}", yol


def test_dizin_gorevleri_ata_torundan_once():
    # `file state=directory` YENİ yarattığı ara dizinlere yaprağın sahip/modunu uygular; ata sonra gelirse taze
    # hostta ara dizin önce yaprağın ayarıyla doğar (v553 G gerekçesi). Burada hepsi 0700 — sıra yine sözleşmedir.
    u, d = _ur(), _defaults()
    g = _dizin_gorevleri()
    for ad in d["sohbet_profil_adlari"]:
        zincir = [u.KOK_DIZIN, f"{u.KOK_DIZIN}/profiles", f"{u.KOK_DIZIN}/profiles/{ad}",
                  f"{u.KOK_DIZIN}/profiles/{ad}/hindsight"]
        siralar = [g[y]["sira"] for y in zincir]
        assert siralar == sorted(siralar) and len(set(siralar)) == len(siralar), dict(zip(zincir, siralar))


def test_kopyalanan_dosyalar_uretecin_ciktisina_esit():
    # Tek kaynak üreteçtir: `uret()`in her dosyası köke kopyalanır, başka hiçbir dosya kopyalanmaz. Eksik = Hermes
    # kökü bayat kalır; fazla = üretilmemiş (elle) bir dosya köke taşınır.
    u = _ur()
    ciftler, _gorevler = _sohbet_kopyalari()
    beklenen = {(goreli, f"{u.KOK_DIZIN}/{goreli.removeprefix(u.SOHBET_EV + '/')}") for goreli in u.uret()}
    assert ciftler == beklenen, (f"eksik: {sorted(beklenen - ciftler)}\nfazla: {sorted(ciftler - beklenen)}")


def test_kopya_gorevi_0600_yedekli_birim_kullanicisinin():
    # Hermes canlıda bu dosyalara yazabilir (`hermes config set`, profil işlemleri) — `backup: true` kaybı önler.
    # Hedef `/` ile biterse copy modülü eksik dizini KENDİSİ yaratır (taze hostun `--check`i): o dizin de 0700.
    baglam = _baglam()
    kullanici = _coz(baglam["meridian_kullanici"], baglam)
    _ciftler, gorevler = _sohbet_kopyalari()
    assert gorevler, "hermes.yml'de Hermes bot köküne kopyalayan görev yok"
    for arg in gorevler:
        assert (str(arg.get("mode")), arg.get("backup")) == ("0600", True), arg
        assert (_coz(arg.get("owner", ""), baglam), _coz(arg.get("group", ""), baglam)) == (kullanici, kullanici)
        if str(arg["dest"]).endswith("/"):
            assert str(arg.get("directory_mode")) == "0700", arg


def test_hermes_gorev_govdesinde_env_yok():
    # Profil `.env`leri (kapı anahtarı, Hindsight anahtarı) ve kökün `.env`i (dinleyici anahtarı) rotasyon aracının
    # işidir; rolün görev gövdesinde (yorum satırları dışı) `.env` dizgesi HİÇ geçmez — kopya listesine girmesinin
    # ilk adımı da budur.
    govde = "\n".join(s for s in HERMES_YML.read_text(encoding="utf-8").splitlines()
                      if not s.lstrip().startswith("#"))
    assert not re.search(r"\.env\b", govde)
    assert not [y for y in _defaults()["sohbet_dosyalari"] if re.search(r"(^|/)\.env\b", y)]
