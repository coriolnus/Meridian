"""test_sprint_sir_yedegi_v523.py — TSK-208 (2026-09-21): sprint kum havuzu kopyası SIR YEDEKLERİNİ
de atlar; tam-ad kümesi sözleşmeyi tutmuyordu.

CANLI ARIZA (Rol-1 ölçümü, A1 salt-okur, 2026-09-21 06:2x–06:5xZ — bu testin varlık sebebi).
`sprint_cadence_failed` **283 kez**, ilk 2026-09-18T22:13:07Z, son 2026-09-21T05:56Z; journal
2026-07-30'a kadar gidiyor, yani 283 olay tarihçenin TAMAMIDIR (retention kesmesi değil). Hata metni
birebir:

    PermissionError: [Errno 13] Permission denied:
    '/opt/meridian/state/secrets.json.bak-20260915T073825Z-tsk189'

Son BAŞARILI `sprint_cadence_start` 2026-09-11T22:09:43Z. Yani öğrenme antrenmanı 09-18'den beri HİÇ
başlamadı. NEDEN TAM O AN: 09-18T22:03Z kaydı `sprint_cadence_skip · sebep="tetik_yok(gun=6<7,
taze=0<5)"` — haftalık tetik 7. günde doldu, ilk gerçek başlatma denemesi 22:13'te oldu ve İLK
denemede düştü. Dosya 09-08'den beri oradaydı; arıza dosyanın doğuşuyla değil TETİĞİN DOLMASIYLA
görünür oldu (bir kapının arkasında bekleyen arıza, kapı açılana kadar ölçülmez).

KÖK NEDEN (kodda). `sprint._kur_kum_havuzu` canlı `state/` kökünü gezip `item.name in SKIP_COPY`
dışındaki her şeyi `shutil.copy2` ile kopyalar. `SKIP_COPY` bir TAM AD kümesidir: `"secrets.json"`
üyedir ama `"secrets.json.bak-20260915T073825Z-tsk189"` DEĞİLDİR. Canlıda o kopya `root:root 0600`,
servis `User=ubuntu` → `copy2` `PermissionError` yükseltir → kurulum tamamen düşer.

SINIFIN ÜÇÜNCÜ TEKRARI. `SKIP_COPY`nin kendi şerhi sınıfı iki kez adlandırıyor ("denylist state'e
yeni gelen artefaktları sessizce kaçırır" — `bars_intraday` vakası, `meridian.db` vakası). Bu
üçüncüsü; farkı SESSİZ DEĞİL GÜRÜLTÜLÜ düşmesi (Yasa 4 doğru çalıştı, `sprint_cadence_failed`
bağırdı — ama 3 gün kimse dinlemedi).

DÜZELTME BİÇİMİ DEPODA ZATEN VARDI. TSK-197'de (2026-09-17) AYNI dosya ailesi gece yedeğinin
`tar`ını kırmıştı ve orada `--exclude="state/secrets.json.bak-*"` DESENİYLE çözülmüştü. Sprint
tarafı ondan habersizdi. Bu dosyanın son çivisi (7) o ayrışmayı ölçer: iki yer aynı sır-yedeği
ailesini artık AYNI tarif etmek zorundadır.

NE ÇİVİLENİR
  1. Sır yedeği VARKEN kurulum tamamlanır ve dosya kum havuzuna GİRMEZ.
  2. Sır yedeği OKUNAMAZKEN (0o000) kurulum yine tamamlanır — canlı arızanın birebir yeniden üretimi.
  3. Desen AİLESİ: `secrets.json`, `.tmp`, `.new` de girmez.
  4. ISIRIK: `SKIP_COPY_PATTERNS` boşaltılırsa kopya geri gelir (desen taşıyıcıdır, süs değil).
  5. DARALTMA YOK: sır olmayan normal defterler kum havuzuna GİRMEYE devam eder.
  6. `auth.json` girmez (B maddesi ölçümü — aşağıda).
  7. TSK-197 ile ayrışma çivisi (tek-kaynak: desen listesi v517'den İTHAL edilir, kopyalanmaz).
  8. Yasa 4: üretim kökünde işaretsiz `except` yok.

CANLIYA DOKUNMAZ: her şey `sandbox_state` altında tmp'de kurulur; `monkeypatch.undo()` YOKTUR.
"""
from __future__ import annotations

import os
import warnings

import pytest

from meridian import codelaw, config, sprint, store

# TSK-197 çivisinden İTHAL (tek-kaynak yasası — desen/örnek-ad listesinin ikinci kopyası doğmasın).
from tests.test_yedek_sir_kopyasi_disla_v517 import DISLANMALI, _desenler, _tar_dislar_mi

# Canlıda ölçülen (A1, 2026-09-21) sır yedeği kopyasının ADI. Tek kaynak v517'dir: oradaki
# `DISLANMALI` gece yedeği birimi için `state/` önekli ÜYE ADI tutar; sprint tarafı `state/`
# kökünü gezdiği için TABAN AD ile çalışır.
SIR_YEDEGI = os.path.basename(DISLANMALI[0])

# root olarak koşulursa 0o000 bacağı ölçülemez. BEYAN ederiz, `skip` ETMEYİZ (§5 uydurma yasağı:
# "ölçülmedi" ile "ölçtüm, temiz" aynı renge boyanmaz).
_ROOT = hasattr(os, "geteuid") and os.geteuid() == 0


def _canli_state_kur(ek_sir: bool = True, okunamaz: bool = False) -> dict[str, bytes]:
    """Sentetik CANLI `state/` ağacı kurar ve "kum havuzuna GİRMESİ gereken" dosyaları döndürür.

    `sandbox_state` fikstürü `config.STATE`i tmp'ye çevirmiş, `history/` + `bars/` dizinlerini ve
    depodaki `goal.yaml`/`bounds.yaml`ı oraya koymuştur; buraya yalnız bu turun ölçtüğü girdiler
    eklenir.

    NEDEN DÖNÜŞ `goal.yaml`/`bounds.yaml`/`events.jsonl` (portfolio/trades DEĞİL): daraltma çivisi
    (5) "normal defter hâlâ kopyalanıyor mu" diye sorar, ama `_kur_kum_havuzu` son adımda
    `_reset_sandbox_state`i çağırır ve O, `trades.jsonl`/`portfolio.json`/`scoreboard.json`/
    `hypotheses.jsonl`/`strategy.yaml` dosyalarını kum havuzunda SIFIRDAN yazar. Bu beş ad üzerinden
    "kopyalandı" ölçmek imkânsızdır: dosya her hâlükârda vardır ve içeriği kopyadan değil
    sıfırlamadan gelir — yeşil, ölçüden değil kurulum sırasından gelirdi. Sıfırlamanın ELLEMEDİĞİ
    gerçek canlı girdiler ölçülür."""
    live = config.STATE
    (live / "events.jsonl").write_text('{"event":"v523_isaret"}\n')
    girmeli = {ad: (live / ad).read_bytes()
               for ad in ("goal.yaml", "bounds.yaml", "events.jsonl")
               if (live / ad).exists()}
    assert girmeli, "kurulum çipası: sentetik canlı state'te kopyalanacak normal defter yok"
    # sır ailesi
    (live / "secrets.json").write_text('{"ALPACA_KEY":"sahte"}')
    (live / "secrets.json.tmp").write_text('{"ALPACA_KEY":"sahte-tmp"}')
    (live / "secrets.json.new").write_text('{"ALPACA_KEY":"sahte-new"}')
    if ek_sir:
        bak = live / SIR_YEDEGI
        bak.write_text('{"ALPACA_KEY":"sahte-bak"}')
        os.chmod(bak, 0o000 if okunamaz else 0o600)
    return girmeli


def _kum_havuzu(sid: str = "20990101-000000"):
    return sprint._kur_kum_havuzu(sid) / "state"


# ==================================================================================================
# 1 — sır yedeği VARKEN kurulum tamamlanır, dosya kum havuzuna girmez
# ==================================================================================================
def test_1_sir_yedegi_kum_havuzuna_girmez(sandbox_state):
    _canli_state_kur()
    sb = _kum_havuzu()
    assert not (sb / SIR_YEDEGI).exists(), (
        f"`{SIR_YEDEGI}` kum havuzuna kopyalandı — sözleşme 'sırlar kopyalanmaz' diyor ve bir sır "
        f"YEDEĞİ de sırdır (TSK-208)")


# ==================================================================================================
# 2 — OKUNAMAYAN sır yedeği: canlı arızanın birebir yeniden üretimi
# ==================================================================================================
def test_2_okunamayan_sir_yedegi_kurulumu_DUSURMEZ(sandbox_state):
    """09-18'den beri canlıda olan tam hâl: dosya orada, mod 0600, sahibi BAŞKA kullanıcı.

    Testte sahipliği değiştiremeyiz (root gerekir), ama ÖLÇÜLEN ŞEY sahiplik değil OKUNAMAZLIKtır:
    `shutil.copy2` dosyayı açamayınca `PermissionError` yükseltir ve kurulum düşer. `0o000` aynı
    kapıyı root OLMAYAN bir süreçte birebir üretir."""
    girmeli = _canli_state_kur(okunamaz=True)
    if _ROOT:
        warnings.warn(UserWarning(
            "v523/2: süreç root — 0o000 okuma kapısı root'u durdurmaz, bu testin ARIZA BACAĞI "
            "ÖLÇÜLMEDİ (atlanmadı: atlama iddiası da yeşil görünürdü). Düzeltmenin kendisi "
            "1. ve 3. çivilerle ölçülmeye devam ediyor."))
    try:
        sb = _kum_havuzu()          # düzeltme yoksa burası PermissionError ile düşer
    finally:
        os.chmod(config.STATE / SIR_YEDEGI, 0o600)      # tmp_path sökümü okuyabilsin
    assert not (sb / SIR_YEDEGI).exists(), f"`{SIR_YEDEGI}` okunamaz olmasına rağmen kopyalandı"
    for ad, icerik in girmeli.items():
        assert (sb / ad).read_bytes() == icerik, (
            f"`{ad}` kum havuzuna girmedi/bozuldu — kurulum yarıda kalmış olabilir")


# ==================================================================================================
# 3 — desen AİLESİ: secrets.json + geçici/yeni kopyalar
# ==================================================================================================
@pytest.mark.parametrize("ad", ["secrets.json", "secrets.json.tmp", "secrets.json.new"])
def test_3_sir_ailesinin_tamami_disarida_kalir(sandbox_state, ad):
    _canli_state_kur()
    assert not (_kum_havuzu() / ad).exists(), (
        f"`{ad}` kum havuzuna kopyalandı — sır dosyasının geçici/yeni kopyası da sırdır")


# ==================================================================================================
# 4 — ISIRIK: desen kümesi boşalırsa kopya geri gelir
# ==================================================================================================
def test_4_desen_kumesi_bosalirsa_sir_yedegi_kum_havuzuna_GERI_GELIR(sandbox_state, monkeypatch):
    """Çivi 1–3'ün yeşili DESENDEN mi geliyor, yoksa başka bir şey mi zaten engelliyor?

    `SKIP_COPY_PATTERNS` boşaltılır ve AYNI ağaç yeniden kurulur: kopya geri gelmiyorsa 1–3'ün
    yeşili ölçtüğünü sandığı mekanizmadan GELMİYOR demektir. Sır yedeği burada bilerek OKUNABİLİR
    (0600 + bizim sahipliğimiz): `PermissionError`suz da ısırığın görünmesi gerekir, yoksa çivi
    root altında sessizce anlamını kaybederdi."""
    _canli_state_kur()
    monkeypatch.setattr(sprint, "SKIP_COPY_PATTERNS", ())
    sb = _kum_havuzu("20990101-000001")
    assert (sb / SIR_YEDEGI).exists(), (
        "desen kümesi boşken bile sır yedeği kopyalanmadı — 1–3'ün yeşili `SKIP_COPY_PATTERNS`ten "
        "GELMİYOR, çiviler yanlış sebeple yeşil")


# ==================================================================================================
# 5 — DARALTMA YOK: normal defterler kopyalanmaya devam eder
# ==================================================================================================
def test_5_normal_defterler_kum_havuzuna_girmeye_devam_eder(sandbox_state):
    """Bedel yasasının bu turdaki ölçüsü: düzeltme KOPYALAMAYI DARALTMAMALI.

    `secrets*` yerine `*secret*` ya da `*.bak*` gibi geniş bir desen yazılsaydı hiçbir test
    kırmızıya dönmezdi — kum havuzu yalnız eksik doğar ve sprint sessizce yanlış ölçerdi (HALT
    vakasının sınıfı). Burada gerçek canlı girdiler bayt-bayt karşılaştırılır."""
    girmeli = _canli_state_kur()
    sb = _kum_havuzu()
    for ad, icerik in girmeli.items():
        assert (sb / ad).exists(), f"`{ad}` kum havuzuna GİRMEDİ — düzeltme kopyalamayı daralttı"
        assert (sb / ad).read_bytes() == icerik, f"`{ad}` kum havuzunda bozuldu"


def test_5b_desen_sir_olmayan_adlari_yakalamaz():
    """Desenin KENDİSİ üzerinde saf ölçüm (dosya sistemi yok): yanlış-pozitif yüzeyi."""
    for ad in ("portfolio.json", "trades.jsonl", "scoreboard.json", "goal.yaml", "bounds.yaml",
               "events.jsonl", "meridian.db.yedek", "meridian.db.20260913T211859Z.bak",
               "sprint_status.json", "hypotheses.jsonl"):
        assert not sprint._desen_atlar(ad), (
            f"`{ad}` DESENLE atlanıyor — desen geniş, kum havuzu eksik doğar ve sprint sessizce "
            f"yanlış ölçer")


# ==================================================================================================
# 6 — auth.json (B maddesi kararı: çocuk yolunda okuyucusu YOK → sözleşmeye girer)
# ==================================================================================================
def test_6_auth_json_kum_havuzuna_girmez(sandbox_state):
    """`state/auth.json` PANONUN kimlik kaydıdır (scrypt parola özeti + oturum imza anahtarı;
    `meridian/auth.py`, 0600). Sözleşme "sırlar kum havuzuna girmez" diyordu, bu kayıt sözleşmeye
    GİRER.

    ÖLÇÜM (TSK-208, grep + import kapanışı, 2026-09-21): `state/auth.json`ı okuyan TEK modül
    `meridian.auth` (`auth._auth_file` → `auth._read`/`auth._write`). `meridian.auth`ı import eden
    yalnız `meridian.auth_cli` (kabuk aracı) ve `meridian.api` (pano sunucusu). `sprint_run`dan
    başlayan meridian-içi import kapanışı 75 modüldür (sprint_run dâhil) ve İÇİNDE NE `auth` NE `api`
    VARDIR; kapanıştaki
    dinamik importların (`importlib`/`__import__`) hiçbiri de bu ikisini adlandırmaz. Yani sprint
    ÇOCUĞUNUN yolunda okuyucusu yoktur: kopya yalnız sır yüzeyi genişletiyordu."""
    _canli_state_kur()
    (config.STATE / "auth.json").write_text('{"algo":"scrypt","hash":"sahte","sign_key":"sahte"}')
    assert not (_kum_havuzu() / "auth.json").exists(), (
        "`auth.json` kum havuzuna kopyalandı — pano parola özeti ve oturum imza anahtarı her kum "
        "havuzu ağacında çoğalır; sprint çocuğunun yolunda okuyucusu YOK (ölçüldü)")


# ==================================================================================================
# 7 — TSK-197 ↔ TSK-208 AYRIŞMA ÇİVİSİ
# ==================================================================================================
def test_7_yedek_birimi_ve_sprint_ayni_sir_yedegi_ailesini_AYNI_tarif_eder(sandbox_state):
    """İKİ YER, AYNI DOSYA AİLESİ. `deploy/oracle-a1/meridian-backup.service` gece arşivinden
    `--exclude="state/secrets.json.bak-*"` ile dışlıyor (TSK-197, 2026-09-17); `meridian/sprint.py`
    kum havuzu kopyasından `SKIP_COPY_PATTERNS` ile atlıyor (TSK-208, 2026-09-21). İkisi de aynı
    gerçeği söyler: "elle bırakılmış sır yedekleri bu ağaca girmez".

    Tek-kaynak yasası burada TEK GÖVDEYİ MÜMKÜN KILMAZ (biri systemd `tar` argümanı, diğeri Python
    `fnmatch` sabiti), o yüzden yasanın istisnası uygulanır: kopya kaçınılmaz → AYRIŞMA ÇİVİSİ. Biri
    değişip diğeri değişmezse burası kırmızıya döner.

    TEK YÖNLÜDÜR — VE BU BİR TASARIM KARARIDIR. Ters yön ÇİVİLENMEZ, çünkü iki yüzeyin sözleşmesi
    BİLEREK ayrışır: gece yedeği canlı `state/secrets.json`ı arşive ALIR (yedeğin işi sırları
    kurtarmaktır), sprint onu ATAR (kum havuzunun işi sırdan uzak durmaktır). Simetri dayatan bir
    çivi bu beyanlı ayrımı ihlal gibi okur ve doğru kodu kırmızıya boyardı."""
    birim_desenleri = _desenler()
    for uye in DISLANMALI:
        assert _tar_dislar_mi(uye, birim_desenleri), (
            f"kurulum çipası: `{uye}` yedek biriminde dışlanmıyor — bu testin ölçtüğü ayrışma "
            f"karşılaştırması anlamsız (v517 ile birlikte okunmalı)")
        assert sprint._atlanir(os.path.basename(uye)), (
            f"İKİ YER AYNI SIR-YEDEĞİ AİLESİNİ AYRI TARİF EDİYOR: `meridian-backup.service` "
            f"`{uye}` üyesini gece arşivinden dışlıyor (TSK-197) ama `meridian/sprint.py` aynı "
            f"dosyayı kum havuzuna KOPYALIYOR (TSK-208 canlı arızası). Biri değişip diğeri "
            f"değişmemiş — `SKIP_COPY_PATTERNS` ile birim ExecStart'ı birlikte tartılmalı")


# ==================================================================================================
# 8 — Yasa 4: yeni kodda işaretsiz `except` yok
# ==================================================================================================
def test_8_yasa4_uretim_kokunde_isaretsiz_except_yok():
    ihlaller = codelaw.silent_handlers()
    assert ihlaller == [], (
        f"Yasa 4 — üretim kökünde işaretsiz `except`: {[h.get('file') for h in ihlaller]}")


# ==================================================================================================
# 9 — BEDEL YASASI: desenle atlanan girdi SESSİZ atlanmaz
# ==================================================================================================
def test_9_desenle_atlanan_girdi_obs_ile_ADIYLA_bildirilir(sandbox_state):
    """Gürültü/çıktı azaltan her değişiklik ne KAYBETTİĞİNİ de ölçer (bedel yasası). Bu turda
    kaybedilen şey GÖRÜNÜRLÜKTÜR: kopyalanmayan bir dosya hiçbir iz bırakmadan yok olur ve bir
    gün desen YANLIŞLIKLA bir defteri yakalarsa kimse fark etmez. Kurulum sonunda BİR bilgi
    satırı bu körlüğü kapatır.

    ALANLARDA YALNIZ AD: içerik, değer ya da hash YAZILMAZ — olay defteri panoya ve `ops/`
    sorgularına açıktır, bir sır dosyasının içeriği oraya sızmamalıdır."""
    _canli_state_kur()
    _kum_havuzu()
    olaylar = [e for e in store.read_jsonl("events.jsonl")
               if e.get("event") == "sprint_kum_havuzu_atlandi"]
    assert len(olaylar) == 1, (
        f"kurulum desenle dosya atladı ama `sprint_kum_havuzu_atlandi` bilgi olayı TAM BİR kez "
        f"yazılmadı ({len(olaylar)}) — atlama sessiz, körlük ölçülemez")
    kayit = olaylar[0]
    assert SIR_YEDEGI in kayit.get("adlar", []), f"atlanan ad olayda yok: {kayit!r}"
    assert kayit.get("adet") == len(kayit.get("adlar", [])), f"adet ↔ adlar ayrışık: {kayit!r}"
    dizge = str(kayit)
    for sizinti in ("sahte-bak", "sahte-tmp", "sahte-new", "ALPACA_KEY"):
        assert sizinti not in dizge, f"olay kaydı dosya İÇERİĞİ taşıyor ({sizinti}): {kayit!r}"
