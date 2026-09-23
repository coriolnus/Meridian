"""test_prescreen_kum_havuzu_sir_v533.py — TSK-214 (2026-09-23): bileşik ön-elemenin kum havuzu
kopyası sır/geçici-artık SINIFINI tek kaynaktan öğrenir.

ÖLÇÜLMÜŞ VAKA (A1, 2026-09-21 20:39:43Z). Haftanın TEK bileşik kalemi ölçülmeden yandı:
`python -m meridian.prescreen --composite … --queue-id C00005` → `prescreen._sandbox` →
`shutil.copytree(live, hedef, symlinks=False)` →
`shutil.Error: [('/opt/meridian/state/secrets.json.bak-20260915T073825Z-tsk189', …,
"[Errno 13] Permission denied")]`. Dosya root sahipli (0600), worker `ubuntu` — kum havuzu
kurulumu OKUYAMADIĞI BİR SIR YEDEĞİNDE çöktü. Kopyalanabilseydi de sır kum havuzuna GİRERDİ;
yani burada iki ayrı zarar var (ARIZA ve MARUZİYET) ve ikisini de aynı süzgeç kapatır.

AYNI DOSYA AYNI SINIFLA ÜÇÜNCÜ YÜZEYİ VURUYOR. Sprint kum havuzu (TSK-208) ve teşhis paketi/yedek
(TSK-209) oralarda TEK KAYNAĞA bağlanarak kapandı: `config.SIR_TAM_ADLAR` / `SIR_DESENLERI` /
`GECICI_ARTIK_DESENLERI` + bileşik yüklem `kopyalanmaz_mi`. Dördüncü bir liste yazmak TSK-209'da
ölçülen ayrışma sınıfını ("iki yüzey iki liste tuttu") geri getirirdi — bu yüzden bu yüzey aynı
yüklemi ÇAĞIRIR, kendi eşleştiricisini KURMAZ (çivi T4b kaynaktan ölçer).

`SKIP_COPY` BİLEREK UYGULANMAZ VE BU BİR DARALTMA KAÇINMASIDIR. O küme KONUMA bağlıdır (`bars`,
`sprint`, `HALT`, `meridian.db`; gerekçeleri BOYUT ve İZOLASYON) ve prescreen için ÖLÇÜLMEDİ.
Bu dilim yalnız SINIF sorusunu kapatır (sır + geçici artık); boyut/izolasyon ayrı bir kalemdir.

NEDEN `obs` DEĞİL `log`: `_sandbox` çağrıldığında `config.STATE` HENÜZ CANLI state'tir —
`run()` içindeki `config.STATE = state` ataması `_sandbox`tan SONRA gelir, yani `obs.log` canlı
deftere yazardı. Satır `log`a gider = `logs/composite-prescreen.log`. Yasa 6 okuyanı: bugün T1,
yarın TSK-215 (o dosyayı worker olayına bağlayacak kalem).

CANLIYA DOKUNMAZ: bütün dosya sistemi işi `sandbox_state`in tmp ağacındadır; `monkeypatch.undo()`
YOKTUR.
"""
from __future__ import annotations

import ast
import inspect
import os
import pathlib
import shutil

import pytest

from meridian import config, prescreen, sprint

# --- Kopyalanmaması GEREKEN yedi ad -------------------------------------------------------------
# Üçü kanonik/ölçülmüş sır (`SIR_TAM_ADLAR` + vakanın KENDİ dosyası), ikisi atomik yazım artığı,
# ikisi ALT DİZİNDE (derinlik: kök süzülüp alt ağaç süzülmezse bunlar sessizce girerdi).
VAKA_ADI = "secrets.json.bak-20260915T073825Z-tsk189"
KOPYALANMAZ_KOK = ("secrets.json", "auth.json", VAKA_ADI, "tmpab12.tmp", ".secrets_x1.tmp")
KOPYALANMAZ_DERIN = ("history/tmpzz.tmp", "quarantine/secrets.json.bak-1")
KOPYALANMAZ = KOPYALANMAZ_KOK + KOPYALANMAZ_DERIN

# --- Kopyalanması GEREKEN beş ad (BEDEL ölçümü) -------------------------------------------------
# `template.json` bir NEAR-MISS'tir: `temp` ≠ `tmp`. Süzgeç genişlerse ölçüm sessizce EKSİK
# state ile koşar ve ön-eleme yanlış ölçer — kazanç ölçülüp bedel ölçülmezse körlük sessizdir.
MESRU = ("portfolio.json", "bounds.yaml", "goal.yaml", "history/2024.jsonl", "template.json")

# Artık ADLI DİZİN: `tmp*.tmp`e UYAR ama DİZİNDİR → kopyalanır (sprint ile aynı bedel kararı;
# desene uyan bir dizini atlamak ALT AĞACIN TAMAMINI sessizce düşürürdü, canlıda örneği yok).
ARTIK_DIZIN = "tmpdir.tmp"
NISAN = "v533-nisan-govdesi"


def _canli_taklidi(kok: pathlib.Path) -> pathlib.Path:
    """Sentetik CANLI `state/` ağacı. Kopyalanmaz adların gövdesine NİŞAN konur: adın atlanması
    yetmez, gövdenin kum havuzunda HİÇBİR yoldan bulunmaması da ölçülür."""
    live = kok / "live"
    for alt in ("history", "quarantine", ARTIK_DIZIN):
        (live / alt).mkdir(parents=True)
    for rel in KOPYALANMAZ:
        (live / rel).write_text('{"nisan":"%s"}' % NISAN)
    for rel in MESRU:
        (live / rel).write_text('{"mesru":true}')
    (live / ARTIK_DIZIN / "icerik.json").write_text('{"mesru":true}')

    # KURULUM ÇİPASI: sınıflandırma tek kaynaktan DOĞRULANIR. Türetme bozulursa (desen düşerse,
    # ad değişirse) çivi yanlış sebeple yeşil kalmasın — kurulum burada kırmızıya döner.
    for rel in KOPYALANMAZ:
        ad = pathlib.PurePosixPath(rel).name
        assert config.kopyalanmaz_mi(ad), (
            f"kurulum çipası: `{ad}` tek kaynağa (`config.kopyalanmaz_mi`) göre kopyalanmaz "
            f"DEĞİL — çivi hiçbir şey ölçmüyor")
    for rel in MESRU:
        ad = pathlib.PurePosixPath(rel).name
        assert not config.kopyalanmaz_mi(ad), (
            f"kurulum çipası: meşru `{ad}` tek kaynağa göre kopyalanmaz SAYILIYOR — bedel "
            f"ölçümü anlamını yitirdi")
    assert config.kopyalanmaz_mi(ARTIK_DIZIN), (
        f"kurulum çipası: `{ARTIK_DIZIN}` desene UYMUYOR — dizin muafiyeti ölçümü anlamsız")

    # VAKANIN KENDİSİ: okunamaz sır yedeği. Root DEĞİLSEK gerçek `PermissionError`u bu üretir.
    (live / VAKA_ADI).chmod(0o000)
    return live


def _kopyala_vakayi_reddederek(src, dst, *, follow_symlinks=True):
    """ROOT KOŞUMU İÇİN okunamazlık enjeksiyonu (`pytest.skip` DEĞİL — root altında çivi susmaz).

    NEDEN `copy_function` PARAMETRESİ, NEDEN `monkeypatch.setattr(shutil, "copy2", …)` DEĞİL:
    `shutil.copytree`ın imzası `copy_function=copy2` VARSAYILANI TANIM ANINDA bağlar, yani modül
    özniteliğini oynatmak copytree'in kullandığı nesneyi DEĞİŞTİRMEZ ve mutasyon ısırmazdı."""
    if os.path.basename(str(src)) == VAKA_ADI:
        raise PermissionError(13, "Permission denied", str(src))
    return shutil.copy2(src, dst, follow_symlinks=follow_symlinks)


def _satirlar(kayit: list[str]) -> list[str]:
    return [s for s in kayit if "kopyalanmayan" in s]


# ==================================================================================================
# T1 — VAKA YENİDEN ÜRETİMİ: kum havuzu kurulur, sır/artık GİRMEZ, atlananlar ADIYLA bildirilir
# ==================================================================================================
def test_T1_sandbox_sir_ve_gecici_artigi_kopyalamaz_ve_hata_vermez(sandbox_state, tmp_path):
    """BUGÜNKÜ KIRMIZI. Süzgeçsiz `copytree` okunamaz sır yedeğinde `shutil.Error` fırlatıyordu
    (T2 o dalı ayrıca kanıtlar). Üç iddia birlikte: (1) kurulum HATA VERMEZ, (2) yedi kopyalanmaz
    ad ne ADIYLA ne GÖVDESİYLE kum havuzunda vardır, (3) atlama İZ bırakır."""
    live = _canli_taklidi(tmp_path)
    workdir = tmp_path / "prescreen-C00005"
    kayit: list[str] = []

    hedef = prescreen._sandbox(workdir, live, log=kayit.append)

    for rel in KOPYALANMAZ:
        assert not (hedef / rel).exists(), (
            f"`{rel}` kum havuzuna kopyalandı — sır/artık sınıfı süzülmüyor")
    govdeler = [p.read_bytes() for p in hedef.rglob("*") if p.is_file()]
    assert not any(NISAN.encode() in g for g in govdeler), (
        "kopyalanmaz bir dosyanın İÇERİĞİ kum havuzunda — ad atlandı, gövde başka yoldan sızdı")

    satir = _satirlar(kayit)
    assert len(satir) == 1, f"tam bir bildirim satırı beklenir, gelen: {kayit}"
    assert f": {len(KOPYALANMAZ)} " in satir[0], (
        f"satır atlanan SAYISINI taşımıyor ({len(KOPYALANMAZ)} beklenir): {satir[0]}")
    for rel in KOPYALANMAZ:
        assert rel in satir[0], (
            f"`{rel}` bildirim satırında yok — bildirilmeyen sürpriz izsiz yok olur: {satir[0]}")


def test_T1b_mesru_dosyalar_kopyalanmaya_DEVAM_eder(sandbox_state, tmp_path):
    """BEDEL ÖLÇÜMÜ. Geniş bir süzgeç hiçbir çiviyi kırmadan kum havuzunu EKSİK doğurur ve
    ön-eleme sessizce YANLIŞ ölçer. `template.json` near-miss'i (`temp` ≠ `tmp`) burada durur."""
    live = _canli_taklidi(tmp_path)
    hedef = prescreen._sandbox(tmp_path / "prescreen-C00005", live, log=lambda s: None)
    for rel in MESRU:
        assert (hedef / rel).exists(), (
            f"meşru `{rel}` kum havuzuna GİRMEDİ — süzgeç ölçümün girdisini yiyor")


# ==================================================================================================
# T2 — MUTASYON KANITI (negatif kontrol): süzgeç OLMADAN aynı fikstür vakayı yeniden üretir
# ==================================================================================================
def test_T2_suzgecsiz_kopya_olculen_vakayi_yeniden_uretir(sandbox_state, tmp_path):
    """"Çivi yeşili kanıt değildir": T1'in yeşili süzgeçten mi geliyor, yoksa fikstür zaten
    zararsız mı? Bu çivi fikstürün GERÇEKTEN ısırdığını testin KENDİ İÇİNDE gösterir —
    `ignore=None` ile çağrılan aynı kopya `shutil.Error` fırlatır ve hatada vakanın adı geçer."""
    live = _canli_taklidi(tmp_path)
    hedef = tmp_path / "suzgecsiz" / "state"
    hedef.parent.mkdir(parents=True)

    ek = {"copy_function": _kopyala_vakayi_reddederek} if os.geteuid() == 0 else {}
    with pytest.raises(shutil.Error) as hata:
        shutil.copytree(live, hedef, symlinks=False, ignore=None, **ek)

    assert VAKA_ADI in str(hata.value), (
        f"vaka OKUNAMAZ SIR YEDEĞİ üzerinden doğmalıydı, gelen hata: {hata.value}")


# ==================================================================================================
# T3 — `--resume` sözleşmesi: hedef varsa DOKUNULMAZ
# ==================================================================================================
def test_T3_resume_hedefi_yeniden_kullanir_suzgec_kosmaz(sandbox_state, tmp_path):
    """Yeniden kullanım `--resume`un ön şartıdır: yeni bir kopya önceki koşunun `inc_cache.json`ını
    silerdi ve "atlanan" adaylar aslında YENİDEN ölçülürdü. Süzgeç bu dalda hiç koşmaz → satır yok."""
    live = _canli_taklidi(tmp_path)
    workdir = tmp_path / "prescreen-C00005"
    hedef = workdir / "state"
    hedef.mkdir(parents=True)
    (hedef / "inc_cache.json").write_text('{"onceki":"kosum"}')
    kayit: list[str] = []

    donen = prescreen._sandbox(workdir, live, log=kayit.append)

    assert donen == hedef
    assert (hedef / "inc_cache.json").read_text() == '{"onceki":"kosum"}', (
        "önceki koşunun artan önbelleği ezildi — `--resume` sessizce yeniden ölçerdi")
    assert not (hedef / "portfolio.json").exists(), (
        "hedef VARKEN kopya yine de koştu — yeniden kullanım dalı düşmüş")
    assert _satirlar(kayit) == [], (
        f"süzgeç koşmadığı hâlde bildirim satırı yazıldı: {kayit}")


# ==================================================================================================
# T4 — TEK KAYNAK: süzgeç `sprint._alt_dizin_suzgeci`in KENDİSİDİR (davranış + kaynak)
# ==================================================================================================
def test_T4_suzgec_sprint_alt_dizin_suzgecinin_KENDISIDIR(sandbox_state, tmp_path, monkeypatch):
    """DAVRANIŞTAN ÖLÇÜM. Tek kaynağı oynatmak prescreen'in süzgecini de oynatmalı: yüzey kendi
    kopyasını kurmuş olsaydı bu yama ISIRMAZDI ve çivi kırmızıya dönerdi."""
    live = _canli_taklidi(tmp_path)
    cagrildi: list[pathlib.Path] = []
    gercek = sprint._alt_dizin_suzgeci

    def _sayan(live_arg, atlanan):
        cagrildi.append(live_arg)
        return gercek(live_arg, atlanan)

    monkeypatch.setattr(sprint, "_alt_dizin_suzgeci", _sayan)
    prescreen._sandbox(tmp_path / "prescreen-C00005", live, log=lambda s: None)

    assert cagrildi == [live], (
        "prescreen tek kaynağı ÇAĞIRMADI — süzgeç kararı ikinci bir yerde yaşıyor")


def _kod_jetonlari() -> tuple[list[str], set[str]]:
    """prescreen'in ÇALIŞAN KODUNDAN dizge sabitleri ve nitelik/ad jetonları.

    DOCSTRING'LER VE ŞERHLER BİLEREK DIŞARIDA. Düz metin grep'i bu çividen bir kez YANLIŞ kırmızı
    üretti: gövde tek kaynağa devrederken docstring gerekçeyi anlatmak için kaynağın ADINI anıyordu.
    Yasak olan ŞEY "adı anmak" değil, KODUN kendi eşleştiricisini kurmasıdır — o yüzden ölçüm
    AST üzerinden yapılır. Şerhler AST'ye hiç girmez, docstring'ler burada elenir."""
    agac = ast.parse(inspect.getsource(prescreen))
    docstring_dugumleri = set()
    for dugum in ast.walk(agac):
        if isinstance(dugum, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            govde = getattr(dugum, "body", None)
            if govde and isinstance(govde[0], ast.Expr) and isinstance(govde[0].value, ast.Constant) \
                    and isinstance(govde[0].value.value, str):
                docstring_dugumleri.add(id(govde[0].value))

    dizgeler, adlar = [], set()
    for dugum in ast.walk(agac):
        if isinstance(dugum, ast.Constant) and isinstance(dugum.value, str) \
                and id(dugum) not in docstring_dugumleri:
            dizgeler.append(dugum.value)
        elif isinstance(dugum, ast.Attribute):
            adlar.add(dugum.attr)
        elif isinstance(dugum, ast.Name):
            adlar.add(dugum.id)
        elif isinstance(dugum, ast.alias):
            adlar.add((dugum.asname or dugum.name).split(".")[0])
    return dizgeler, adlar


def test_T4b_prescreen_kendi_esletiricisini_KURMAZ(sandbox_state):
    """KAYNAKTAN ÖLÇÜM (davranış çivisinin tamamlayıcısı). TSK-209'da ölçülen ayrışmanın sebebi
    "iki yüzey iki liste tuttu"ydu; bu yüzeyin kendi desen/ad listesini KODDA kurması aynı sınıfı
    geri getirirdi. Karar `sprint` üzerinden `config`tedir; prescreen yalnız ÇAĞIRIR.

    Docstring'de kaynağın adını ANMAK serbesttir (gerekçe orada yaşar) — ölçüm çalışan kodadır."""
    dizgeler, adlar = _kod_jetonlari()

    for parca in ("secrets", "auth.json", "tmp", ".bak"):
        kirli = [d for d in dizgeler if parca in d]
        assert not kirli, (
            f"prescreen KODUNDA `{parca}` içeren dizge sabiti var ({kirli}) — sır/artık "
            f"sınıflandırması ikinci bir yerde kuruluyor, tek kaynak kırıldı")

    for ad in ("fnmatch", "SIR_DESENLERI", "SIR_TAM_ADLAR", "GECICI_ARTIK_DESENLERI",
               "kopyalanmaz_mi", "sir_dosyasi_mi", "gecici_artik_mi"):
        assert ad not in adlar, (
            f"prescreen KODU `{ad}` jetonunu doğrudan kullanıyor — süzgeç kararı `sprint` tek "
            f"kaynağından GEÇMEDEN kuruluyor")

    assert "_alt_dizin_suzgeci" in adlar, (
        "prescreen tek kaynağı KODDA çağırmıyor — devir zinciri koptu")


# ==================================================================================================
# T5 — DİZİN MUAFİYETİ: desene uyan bir DİZİN kopyalanır (yalnız DOSYA adları elenir)
# ==================================================================================================
def test_T5_artik_ADLI_DIZIN_kopyalanir(sandbox_state, tmp_path):
    """Süzgeç YALNIZ dosya adlarına bakar. Desene uyan bir dizini atlamak ALT AĞACIN TAMAMINI
    sessizce düşürürdü — canlıda böyle bir dizin ÖLÇÜLMEDİ, yani kazanç VARSAYIM, kayıp GERÇEK
    olurdu (bedel yasası; sprint ile AYNI karar)."""
    live = _canli_taklidi(tmp_path)
    kayit: list[str] = []
    hedef = prescreen._sandbox(tmp_path / "prescreen-C00005", live, log=kayit.append)

    assert (hedef / ARTIK_DIZIN).is_dir(), (
        f"`{ARTIK_DIZIN}/` DİZİNİ atlandı — süzgeç dosya adlarının ötesine geçti, alt ağaç düştü")
    assert (hedef / ARTIK_DIZIN / "icerik.json").exists(), (
        "artık adlı dizinin İÇERİĞİ düştü")
    satir = _satirlar(kayit)
    assert satir and ARTIK_DIZIN not in satir[0], (
        f"dizin adı atlananlar arasında bildirildi: {satir}")
