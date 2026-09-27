"""v563 — SATIR ÇAPASI YASASI, BİRİM DÜNYASI: `deploy/**` systemd birim/drop-in/timer şerhleri
(TSK-231, 2026-09-27). Varlık yasağının ÜÇÜNCÜ eşi: `test_kovab_dilim_v382.py` `meridian/*.py`yi,
`test_tests_ops_satir_capasi_v401.py` `tests/`+`ops/` altındaki `.py`yi tarar; ikisi de birim
dosyasına HİÇ bakmıyordu, `codelaw`ın dört satır-çapası dünyası (py · tsx · docs · metin) da.

VAKA (TSK-228, 2026-09-26/27): `meridian-sprint@.service` şerhindeki iki satır çapası (hedefi
`meridian.service`) e0e54f1c'de ZATEN yanlış satırı gösteriyordu; düzeltme turu onları başlık
çapasına çevirdi (0013b8ed) ama SINIF açık kaldı — hiçbir tarayıcı birim dosyasını okumuyordu.

TUR BAŞI ÖLÇÜM (2026-09-27, taban 6ddb04a7, bu dosyanın tarayıcısıyla): `deploy/**` altında 67 birim
dosyası (30 `.service` · 22 `.conf` · 15 `.timer` · 0 `.path`), 7 dosyada 40 satır çapası — 28
BİTİŞİK biçim (dosya adı + iki nokta + sayı: 16 `.py` · 9 `.sh` · 3 `.go` hedefli) ve 12 DEVAM biçimi
(aynı satırda/önceki satırda anılan dosyayı süren yalın iki nokta + sayı). HEPSİ şerh satırındaydı,
ayar satırında 0. BAYATLIK (sınıfın gerçek olduğunun kanıtı): `.py` hedefli 16 bitişik çapanın 16'sı ve
12 devam çapasının 12'si bugün YANLIŞ satırı gösteriyordu (hedef modüller bu arada büyüdü); `.sh`
hedefli 9 çapanın 9'u hâlâ doğruydu (hedefler nadir değişiyor — doğru olması SANS, sözleşme değil);
3 `.go` çapası harici kaynağı (litestream v0.5.15) gösterdiği için ölçülemez. 40'ının tamamı bu turda
sembol/başlık/alıntı çapasına çevrildi (tam liste: TSK-231 raporu).

NEDEN AYRI ÇİVİ, `codelaw` YÜZEYİ DEĞİL (gerekçe):
  1. SORU FARKLI. `codelaw.stale_line_anchors` ailesi BAYATLIK ölçer ("gösterdiği satır bugün kod
     mu?") ve yalnız `.py` HEDEFİ çözebilir; taze bir satır çapası hüküm almaz. Birim şerhlerinin
     hedefleri `.py` ile sınırlı değil (`.sh`, `.service`, harici `.go`) — TSK-228'in iki çapası
     `.service` hedefliydi ve bayatlık ölçümü onları HİÇ göremezdi. v382/v401'in sorusu ise VARLIKtır
     ("beyansız satır çapası var mı?"): hedefi çözmeye ihtiyaç duymaz, CLAUDE.md §2'nin kuralını
     ("çapa SATIR değil SEMBOL olmalı") doğrudan zorlar. Bu dosya o sorunun birim dünyasındaki eşidir.
  2. MOTOR DEĞİŞMEZ. `codelaw` canlıda koşan kod ailesindedir; test tarafında kalan bir çivi Rol-1'e
     tam suite yükü bindirmez ve bekçinin `report()["ok"]`i gibi canlı bir yüzeye yeni hüküm eklemez.

TEK KAYNAK (v382 K1 dersi — kopya desen sessizce DARALIR):
  * Muafiyet işaretleri (`codelaw._CAPA_MUAFIYETI`, `codelaw._CAPA_SENTETIK_ISARETI`) codelaw'dan okunur.
  * Uzantı kümesi `codelaw._CAPA_UZANTILARI`ndan TÜRETİLİR (codelaw'ın "bu jeton bir dosya adıdır"
    listesi); birim dünyasına özgü dört ek (`_BIRIM_EK_UZANTILAR`) gerekçesiyle ayrı yazılır.
  * Desen İKİ codelaw deseninin (`codelaw._CAPA_DESENI`, `codelaw._TEXT_CAPA_DESENI`) ÜST KÜMESİdir ve
    bu bir AYRIŞMA ÇİVİSİYLE ölçülür (hem örnek dizgeler hem canlı birim korpusu üzerinde): codelaw'ın
    gördüğü bir çapayı bu dosya göremezse kırmızı.

DEVAM BİÇİMİ YALNIZ ŞERH SATIRINDA aranır: ayar satırında yalın iki nokta + sayı meşru bir sözdizimi
olabilir (ör. bir `ExecStart=` argümanında dinleme adresi); şerhte ise ölçülen 12 örneğin 12'si çapaydı.
Bitişik biçim her satırda aranır (ayar satırında bugün 0; `Description=` gibi insan metni taşıyan
ayarlar da kapsamda kalsın diye).

KAPSAM DIŞI — BEYAN (bedel yasası: kazanç ölçülüp bedel ölçülmezse körlük sessizdir). Aynı genişletilmiş
desenle `deploy/**` altında ÖLÇÜLDÜ (2026-09-27), bu dosya onları TARAMAZ:
  * `.md` — 99 çapa (88'i `deploy/HANDBOOK-PLAN.md`, bir plan belgesi; 10'u `deploy/oracle-a1/RUNBOOK.md`;
    1'i `deploy/hermes/skills/meridian-olcum/SKILL.md`de kuralın kendisini örnekleyen metin). `docs/`
    dışındaki `.md` hiçbir satır-çapası yasasının görüş alanında değil.
  * `.yml`/`.yaml` — 20 çapa (19'u `deploy/oracle-a1/litestream.yml`, çoğu harici litestream kaynağı).
  * `.sh` — 4 çapa (`cutover.sh`, `deploy.sh`, `litestream_kur.sh` ×2).
  * `.py` (`deploy/` altında 4 dosya) — 0 gerçek çapa (2 eşleşme bir `strftime` biçim dizgesi).
  Bu yüzeyler brief kapsamı dışında bırakıldı; TSK-236 onları `test_capa_pydisi_hedef_v571.py`de tarar.
"""
from __future__ import annotations

import pathlib
import re

import pytest

from meridian import codelaw

REPO = pathlib.Path(__file__).resolve().parents[1]
DEPLOY = REPO / "deploy"

#: Taranan birim uzantıları (brief kapsamı). `.path` bugün 0 dosya taşıyor ama kapsamdadır: ilk
#: `.path` birimi doğduğu gün görünür olsun (v401 `ops/` emsali — sıfır borç, sıfır tarama değildir).
BIRIM_UZANTILARI = ("service", "conf", "timer", "path")

#: `codelaw._CAPA_UZANTILARI`nda OLMAYAN, birim şerhlerinin gösterdiği ek hedef uzantıları:
#: `go` (harici litestream kaynağı — ölçülen 3 çapa), `path` (systemd birim türü), `hcl` (Vault
#: yapılandırması, `deploy/vault/`), `rules` (polkit kuralları, `deploy/oracle-a1/`).
_BIRIM_EK_UZANTILAR = ("go", "path", "hcl", "rules")


def _uzantilar() -> tuple[str, ...]:
    """Dosya-adı uzantıları — codelaw'ın listesi + birim eki, uzundan kısaya (alternasyon sırası)."""
    return tuple(sorted({*codelaw._CAPA_UZANTILARI, *_BIRIM_EK_UZANTILAR},
                        key=lambda u: (-len(u), u)))


#: BİTİŞİK biçim: isteğe bağlı yol öneki + ad + bilinen uzantı + iki nokta + sayı (+ aralık).
#: Ad `@` ve `-` taşıyabilir (`meridian-sprint@.service` gibi şablon birimleri); ilk karakter harf ya
#: da alt çizgi olmak ZORUNDA — `127.0.0.1:6379` gibi adres:port biçimi bu yüzden eşleşmez.
_BIRIM_CAPA_DESENI = re.compile(
    r"((?:[\w.@-]+/)*)([^\W\d][\w.@-]*\.(?:"
    + "|".join(re.escape(u) for u in _uzantilar())
    + r")):(\d+)(?:-(\d+))?")

#: DEVAM biçimi (yalnız şerh satırında): boşluk/parantez/virgül/noktalı virgül/orta nokta/backtick
#: ardından yalın iki nokta + sayı. Önceki karakter bir ad/sayı olamaz — saat (`23:32`) ve adres:port
#: (`127.0.0.1:8888`) bu yüzden eşleşmez.
_DEVAM_CAPA_DESENI = re.compile(r"(?<=[\s(\[,;·`]):(\d+)(?:-(\d+))?")


def _muafiyetler() -> tuple[str, str]:
    """İKİ muafiyet işareti — TEK KAYNAK codelaw (v382/v401 ile aynı: mezar taşı + sentetik)."""
    return codelaw._CAPA_MUAFIYETI, codelaw._CAPA_SENTETIK_ISARETI


def _serh_mi(satir: str) -> bool:
    """systemd şerh satırı: ilk boşluk-dışı karakter `#` ya da `;`."""
    return satir.lstrip().startswith(("#", ";"))


def _birim_capa_ihlalleri(metin: str):
    """Muafiyet işareti TAŞIMAYAN satırlardaki satır çapaları → (satır no, çapa metni).

    Bitişik biçim her satırda, devam biçimi yalnız şerh satırında aranır (gerekçe modül belgesinde)."""
    muaflar = _muafiyetler()
    for i, satir in enumerate(metin.splitlines(), 1):
        if any(m in satir for m in muaflar):
            continue
        for m in _BIRIM_CAPA_DESENI.finditer(satir):
            yield i, m.group(0)
        if _serh_mi(satir):
            for m in _DEVAM_CAPA_DESENI.finditer(satir):
                yield i, m.group(0)


def _birim_dosyalari() -> list[pathlib.Path]:
    """`deploy/` altındaki birim dosyaları, özyineli, ad sırasıyla."""
    return sorted(f for u in BIRIM_UZANTILARI for f in DEPLOY.rglob(f"*.{u}") if f.is_file())


# =================================================================================================
# A) TEK KAYNAK — işaretler ve uzantılar codelaw'dan, desen codelaw desenlerinin ÜST KÜMESİ
# =================================================================================================

def test_muafiyet_isaretleri_CODELAW_TEK_KAYNAGINDAN_gelir():
    assert _muafiyetler() == ("çapa-mezar-taşı", "çapa-sentetik")


def test_uzanti_kumesi_CODELAW_listesinden_TURETILIR():
    """Codelaw'ın dosya-adı uzantılarının HER biri bu tarayıcının kümesinde; ek dört uzantı ayrı."""
    kume = set(_uzantilar())
    assert set(codelaw._CAPA_UZANTILARI) <= kume
    assert kume - set(codelaw._CAPA_UZANTILARI) <= set(_BIRIM_EK_UZANTILAR)
    assert {"py", "sh", "service", "conf", "timer"} <= set(codelaw._CAPA_UZANTILARI)


@pytest.mark.parametrize("ornek", [
    "uydurma_modul.py:7",                    # çapa-sentetik: desen örneği, gerçek dosya değil (TSK-231)
    "uydurma_modul.py:412345",               # çapa-sentetik: desen örneği, gerçek dosya değil (TSK-231)
    "ops/uydurma_alt/uydurma.py:44",         # çapa-sentetik: yol önekli desen örneği (TSK-231)
    "uydurma.yaml:27",  # çapa-sentetik: desen örneği (TSK-236)
    "uydurma.sh:12-30",  # çapa-sentetik: desen örneği (TSK-236)
])
def test_desen_CODELAW_desenlerinin_UST_KUMESI_ornekler(ornek):
    """Ayrışma çivisi (örnek dizgeler): codelaw'ın iki deseninin yakaladığı her örneği bu desen de
    AYNI metinle yakalar. Kopya daralsaydı codelaw'ın gördüğünü bu dosya görmez, "temiz" derdi."""
    codelaw_gordu = [m.group(0) for d in (codelaw._CAPA_DESENI, codelaw._TEXT_CAPA_DESENI)
                     for m in d.finditer(ornek)]
    assert codelaw_gordu, f"örnek codelaw desenlerinde de eşleşmeli (yoksa çivi boşta): {ornek}"
    bizim = [m.group(0) for m in _BIRIM_CAPA_DESENI.finditer(ornek)]
    for c in codelaw_gordu:
        assert any(c in b for b in bizim), f"codelaw `{c}` görüyor, birim deseni görmüyor: {bizim}"


def test_desen_CODELAW_desenlerinin_UST_KUMESI_canli_korpus():
    """Ayrışma çivisi (canlı birim korpusu): codelaw'ın iki deseninin birim dosyalarında gördüğü HER
    eşleşme bu tarayıcının bir eşleşmesinin içinde kalır."""
    kacan = []
    for f in _birim_dosyalari():
        for i, satir in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            bizim = [m.group(0) for m in _BIRIM_CAPA_DESENI.finditer(satir)]
            for d in (codelaw._CAPA_DESENI, codelaw._TEXT_CAPA_DESENI):
                for m in d.finditer(satir):
                    if not any(m.group(0) in b for b in bizim):
                        kacan.append(f"{f.relative_to(REPO)} satır {i}: {m.group(0)}")
    assert not kacan, kacan


# =================================================================================================
# B) POZİTİF KONTROL — tarayıcı BOŞTA "temiz" demiyor; muafiyet ve yanlış-pozitif kapıları çalışıyor
# =================================================================================================

@pytest.mark.parametrize("satir,beklenen", [
    # TSK-228'in BİREBİR biçimi: `.service` hedefli çapa (bayatlık tarayıcısının göremediği sınıf)
    ("# Gürültü, sessizlikten iyidir (meridian.service:176).", ["meridian.service:176"]),  # çapa-sentetik: birim deseni fikstürü (TSK-236)
    ("# (meridian-sprint@.service:170 ile aynı küme)", ["meridian-sprint@.service:170"]),  # çapa-sentetik: birim deseni fikstürü (TSK-236)
    ("# PYTHONPATH=. — ops/uydurma-run.sh:45 ile AYNI", ["ops/uydurma-run.sh:45"]),  # çapa-sentetik: birim deseni fikstürü (TSK-236)
    ("#  · log — uydurma_modul.py:340-341 ROOT'a yazar", ["uydurma_modul.py:340-341"]),  # çapa-sentetik: desen örneği (TSK-231)
    ("# (v0.5.15 cmd/uydurma/main_notwindows.go:20", ["cmd/uydurma/main_notwindows.go:20"]),  # çapa-sentetik: birim deseni fikstürü (TSK-236)
    ("# drop-in (uydurma.conf:3, uydurma.timer:9)", ["uydurma.conf:3", "uydurma.timer:9"]),  # çapa-sentetik: birim deseni fikstürü (TSK-236)
    # devam biçimi (şerhte): bitişik çapanın ardından yalın iki nokta + sayı
    ("# YAZAR: uydurma_modul.py:1942 `.env` · :1956 yedek · (:96-99)",  # çapa-sentetik: desen örneği (TSK-231)
     ["uydurma_modul.py:1942", ":1956", ":96-99"]),  # çapa-sentetik: beklenen değer (TSK-231)
    ("#     :2072 config · :2215 skills/", [":2072", ":2215"]),
])
def test_tarayici_SENTETIK_ihlali_yakalar(satir, beklenen):
    assert [c for _i, c in _birim_capa_ihlalleri(satir)] == beklenen


@pytest.mark.parametrize("satir", [
    "Environment=REDIS=127.0.0.1:6379",
    "# Redis 127.0.0.1:6379 (AF_INET)",
    "ExecStart=/usr/bin/x -e URL=http://127.0.0.1:8888 \\",
    "OnCalendar=Mon..Fri *-*-* 13..19:00/5:00 UTC",
    "# her gece 23:32 UTC",
    "ExecStart=/usr/local/bin/uydurma --addr :9090",          # devam biçimi AYAR satırında aranmaz
    "# ssh -N -L 9999:127.0.0.1:9999 ubuntu@host",
    "# `hermes.py::sync_agent_skills` sembol çapası satır çapası DEĞİLDİR",
    "# IPv6 [::1]:8080 ve (::1)",
    "# bkz. api.anthropic.com:443",
])
def test_tarayici_YANLIS_POZITIF_uretmez(satir):
    assert list(_birim_capa_ihlalleri(satir)) == []


def test_MUAFIYETLI_satir_GECER_isaretsiz_YAKALANIR():
    """İki muafiyet işareti de geçer; aynı satır işaretsizken yakalanır (tek çivide — biri sessizce
    bozulamasın)."""
    mezar, sentetik = _muafiyetler()
    ham = "# eski çapa: meridian.service:176"  # çapa-sentetik: muafiyet fikstürü (TSK-236)
    assert [c for _i, c in _birim_capa_ihlalleri(ham)] == ["meridian.service:176"]  # çapa-sentetik: beklenen değer (TSK-236)
    assert list(_birim_capa_ihlalleri(f"{ham} ({mezar})")) == []
    assert list(_birim_capa_ihlalleri(f"{ham} ({sentetik}: fikstür)")) == []


# =================================================================================================
# C) KÖRLÜK ALARMI + KAPSAM — yanlış kök "temiz" diye ebediyen yeşil kalmasın
# =================================================================================================

def test_KORLUK_ALARMI_taranan_birim_dosyasi_TABANI_asiyor():
    """Bugün 67 dosya (2026-09-27). Taban 50: dosya sayısı düşebilir ama yanlış kök (cwd kayması,
    `deploy/` taşınması) 0-birkaç dosya döner ve bu çivi onu yakalar."""
    dosyalar = _birim_dosyalari()
    assert len(dosyalar) >= 50, f"taranan birim dosyası az ({len(dosyalar)}) — tarayıcı yanlış köke bakıyor olabilir"
    uzantilar = {f.suffix.lstrip(".") for f in dosyalar}
    assert {"service", "conf", "timer"} <= uzantilar, uzantilar


def test_drop_in_ALT_DIZINLERI_de_TARANIYOR():
    """Drop-in'ler `*.service.d/` alt dizinlerindedir; özyinelemesiz tarama onları kaçırırdı."""
    assert any(f.parent.name.endswith(".service.d") for f in _birim_dosyalari())


# =================================================================================================
# D) CANLI HÜKÜM — `deploy/**` birim şerhlerinde BEYANSIZ satır çapası KALMADI
# =================================================================================================

def test_deploy_birim_dosyalarinda_MUAFIYETSIZ_satir_capasi_YOK():
    """TSK-231'in hükmü: CLAUDE.md §2 — çapa SATIR değil SEMBOL. Kalan her satır çapası, hedef dosya
    büyüdükçe SESSİZCE yanlış satırı gösterir (tur başında `.py` hedefli 16 bitişik + 12 devam
    çapasının 28'i de yanlış satırı gösteriyordu)."""
    ihlal = [f"{f.relative_to(REPO)} satır {n}: {c}" for f in _birim_dosyalari()
             for n, c in _birim_capa_ihlalleri(f.read_text(encoding="utf-8"))]
    assert not ihlal, (
        "birim şerhinde beyansız satır çapası — sembol (`dosya.py::ad`) ya da başlık/alıntı çapasına "
        f"çevir: {ihlal}")


# =================================================================================================
# E) ÇEVRİLEN ÇAPALAR ÇÜRÜMEZ — sembol çapaları codelaw çekirdeğinden, başlık çapaları metinden
# =================================================================================================

def _birim_metinleri() -> list[tuple[str, str]]:
    return [(str(f.relative_to(REPO)), f.read_text(encoding="utf-8")) for f in _birim_dosyalari()]


def _sembol_hukmu() -> dict:
    """Birim şerhlerindeki sembol çapaları `codelaw.capa_uyusmasi` çekirdeğinden geçer (tek-kaynak:
    ikinci bir sembol çözücü YAZILMADI). Kökler MUTLAK — hüküm çalışma dizinine bağlı olmasın.

    `modul_bicimi=True`: birim şerhleri PYTHON TARAFININ biçimini de yazar (backtick içinde modül
    adı + nokta + sembol, ör. `storage.backup_to` ya da `config.STATE`). Codelaw bu biçimi yalnız Python-tarafı
    beslemelerde okur, çünkü panonun tsx düzyazısında aynı desen JSON ALAN adıdır; birim şerhlerinde
    öyle bir kullanım ÖLÇÜLMEDİ — 2026-09-27'de 46 eşleşmenin 46'sı gerçek sembole çözüldü, 0 çürük,
    0 çözülemeyen."""
    kokler = tuple(str(REPO / k) for k in ("meridian", *codelaw._EK_CAPA_KOKLERI))
    return codelaw.capa_uyusmasi(_birim_metinleri(), py_kokler=kokler, modul_bicimi=True)


def test_birim_SEMBOL_capalari_COZULUR_curuyen_YOK():
    """Sembol çapası da çürür ama SESLİ çürür — bu çivi o sesi çıkarır. `curuyen` = modül var,
    sembol yok; `cozulemeyen` = hüküm kurulamadı (hedef yok/ikircikli) — ikisi de boş olmalı."""
    h = _sembol_hukmu()
    assert h["curuyen"] == [], h["curuyen"]
    assert h["cozulemeyen"] == [], h["cozulemeyen"]


def test_birim_SEMBOL_capalari_KORLUK_ALARMI():
    """Çözülen sembol çapaları sayılır (ölçüldü 2026-09-27: 80 = 34 dosya-adı + iki nokta üst üste
    biçimi — 11'i tur öncesinden, 23'ü bu turda satır çapasından çevrilen — ve 46 modül-nokta
    biçimi). Alt sınırlar 30 / 70 — düşen sayı "temiz" DEĞİL "çapalar silinmiş ya da çözücü yanlış
    köke bakıyor" demektir (v382 `test_cevrilen_capa_KAYNAKTA_duruyor` emsali)."""
    cozulen = _sembol_hukmu()["cozulen"]
    assert sum(1 for c in cozulen if "::" in c["capa"]) >= 30
    assert len(cozulen) >= 70


#: BAŞLIK/ALINTI ÇAPALARI — `.sh`/`.go` hedefler sembol çözücüsüne girmez (çözücü yalnız `.py` okur).
#: (birim dosyası, birimdeki çapa metni, hedef dosya | None, hedefte bulunması ZORUNLU metinler)
#: Hedef `None` = repo DIŞI (harici litestream kaynağı) — doğrulanamaz, `False` ile dürüstçe işaretli
#: v382 hermes-agent ikilisi emsali; sürüm tanığı ayrıca çivili (aşağıda).
BASLIK_CAPALARI = [
    ("deploy/oracle-a1/meridian-backup.service",
     "bakim_h9.sh `[9] H3 sertleştirme drop-in'leri` adımı",
     "deploy/oracle-a1/bakim_h9.sh", ("[9] H3 sertleştirme drop-in'leri",)),
    ("deploy/oracle-a1/meridian-backup.service",
     "bakim_h9.sh `[12] son doğrulama paketi` adımındaki yedek unit provası",
     "deploy/oracle-a1/bakim_h9.sh", ("[12] son doğrulama paketi", "yedek unit provası")),
    ("deploy/oracle-a1/meridian.service",
     "bakim_h9.sh `[10] token rotasyonu` adımı",
     "deploy/oracle-a1/bakim_h9.sh", ("[10] token rotasyonu",)),
    ("deploy/oracle-a1/meridian.service",
     "bakim_h9.sh `[9] H3 sertleştirme drop-in'leri` adımı",
     "deploy/oracle-a1/bakim_h9.sh", ("[9] H3 sertleştirme drop-in'leri",)),
    ("deploy/oracle-a1/sertlestirme.conf",
     "bakim_h9.sh `[9] H3 sertleştirme drop-in'leri` adımı",
     "deploy/oracle-a1/bakim_h9.sh", ("[9] H3 sertleştirme drop-in'leri",)),
    ("deploy/oracle-a1/sertlestirme.conf",
     "bakim_h9.sh `[8] yedek unit düzeltmesi` adımı",
     "deploy/oracle-a1/bakim_h9.sh", ("[8] yedek unit düzeltmesi", "sertlestirme.conf")),
    ("deploy/oracle-a1/meridian-barsarchive.service",
     "ops/barsarchive-run.sh `start)` dalındaki `PYTHONPATH=. nohup` satırı",
     "ops/barsarchive-run.sh", ("start)", "PYTHONPATH=. nohup")),
    ("deploy/oracle-a1/meridian.service",
     "serve.sh'ın uvicorn `subprocess.Popen` satırı",
     "serve.sh", ("subprocess.Popen(['.venv/bin/python','-m','uvicorn'", "env=os.environ")),
    ("deploy/oracle-a1/meridian.service.d/50-dash-credential.conf",
     "serve.sh'ın uvicorn `subprocess.Popen` satırı",
     "serve.sh", ("subprocess.Popen(['.venv/bin/python','-m','uvicorn'", "env=os.environ")),
    ("deploy/oracle-a1/meridian-litestream.service",
     "v0.5.15 `cmd/litestream/main_notwindows.go` `defaultConfigPath`", None, ()),
    ("deploy/oracle-a1/meridian-litestream.service",
     "v0.5.15 `cmd/litestream/main_notwindows.go`,", None, ()),
    ("deploy/oracle-a1/meridian-litestream.service",
     "v0.5.15 `db.go` varsayılanı", None, ()),
]


@pytest.mark.parametrize("birim,capa,_hedef,_metinler", BASLIK_CAPALARI)
def test_baslik_capasi_BIRIMDE_duruyor(birim, capa, _hedef, _metinler):
    """Çapa metni ADIYLA çivilenir: satır-çapası tarayıcısı yeşilken çapa büsbütün SİLİNMİŞ de
    olabilirdi (v382 `test_cevrilen_capa_KAYNAKTA_duruyor` emsali)."""
    assert capa in (REPO / birim).read_text(encoding="utf-8"), f"{birim} içinde `{capa}` yok"


@pytest.mark.parametrize("birim,capa,hedef,metinler", [b for b in BASLIK_CAPALARI if b[2]])
def test_baslik_capasi_HEDEFTE_gercekten_var(birim, capa, hedef, metinler):
    """Başlık/alıntı çapası da çürür: hedef betikte adım başlığı ya da alıntılanan satır değişirse
    bu çivi öter (satır çapasının SESSİZ çürümesinin tersi)."""
    govde = (REPO / hedef).read_text(encoding="utf-8")
    eksik = [m for m in metinler if m not in govde]
    assert not eksik, f"{birim} çapası `{capa}` → {hedef} içinde bulunamadı: {eksik}"


def test_harici_litestream_capalari_SURUM_TANIGI_sabit():
    """`.go` çapaları litestream v0.5.15 kaynağını anlatır ve repo içinde doğrulanamaz. Sürüm tanığı:
    `litestream_kur.sh` aynı sürümü sabitler ve `litestream.yml` `defaultConfigPath` adını o sürümün
    kaynağından okuduğunu yazar. Sürüm yükseltilirse bu çivi öter — birim şerhindeki üç harici çapa
    yeni sürümün kaynağından YENİDEN okunmadan yeşile dönmemeli."""
    kur = (DEPLOY / "oracle-a1" / "litestream_kur.sh").read_text(encoding="utf-8")
    yml = (DEPLOY / "oracle-a1" / "litestream.yml").read_text(encoding="utf-8")
    assert 'LS_SURUM="0.5.15"' in kur
    assert "v0.5.15" in yml and "defaultConfigPath" in yml
