"""ÖLÇÜM ARACI: olay adı TAHMİN EDİLMEZ, KODDAN BULUNUR — v328 (2026-08-27)

ÖLÇÜLMÜŞ VAKA (2026-08-27). Canlı teşhis sırasında olay adı iki kez tahmin edildi:
    grep "pozisyon_adet_benimsendi"  → 0   (gerçek ad: `adet_benimsendi`)
    grep "position_drift"            → 0   (öyle bir OLAY yok, o bir ALAN)
Sahte sıfır, "arıza yok" diye okunur. Bu, deponun kayıtlı `olcum-baglami-tuzagi` dersinin
canlı tekrarıdır.

ÇARE ARAÇ: olay adları kaynaktaki `obs.log/warn/error/alarm` çağrılarından ÇIKARILIR.

SINIR (fix round 4, 2026-08-29): "tahmin edilecek bir şey kalmaz" CÜMLESİ BURADAN KALDIRILDI —
bir TAMLIK iddiasıydı ve YANLIŞTI. Araç `TARANAN_KOKLER` × `TARANAN_DOSYA_DESENI` kapsamını okur;
o kapsamın dışında basılan olay görünmez VE hiçbir sayaca düşmez. Araç bunu her koşumda beyan
eder; bu dosyanın son çivileri beyanın taramadan sürüklenmesini imkânsız kılar.
"""
from __future__ import annotations

import importlib.util
import pathlib

import pytest

yaml = pytest.importorskip("yaml")

KOK = pathlib.Path(__file__).resolve().parent.parent
BETIK = KOK / "ops/olcum.py"


def _yukle():
    assert BETIK.exists(), f"{BETIK} YOK"
    spec = importlib.util.spec_from_file_location("olcum", BETIK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_GERCEK_OLAY_ADINI_BULUR():
    """`benimse` desenini arayan, gerçek ad olan `adet_benimsendi`yi bulmalı."""
    mod = _yukle()
    adlar = mod.olay_adlari("benimse")
    assert "adet_benimsendi" in adlar, f"gerçek ad bulunamadı: {adlar}"


def test_OLMAYAN_ADI_UYDURMAZ():
    """`position_drift` bir ALAN adıdır, olay değil. Araç onu olay diye döndürmemeli."""
    mod = _yukle()
    assert "position_drift" not in mod.olay_adlari("drift")


def test_AYRISTIRICI_BAYAT_DEGIL():
    """Regex hiçbir şey görmezse yukarıdaki iki çivi de TRIVIAL geçer — nöbetçi bu."""
    mod = _yukle()
    assert len(mod.olay_adlari("")) >= 200, "olay adı ayrıştırıcısı bayat"


def test_SKILL_ARACA_YONLENDIRIYOR():
    """Skill, ajana 'tahmin etme' demeli — yoksa araç var ama kullanılmaz."""
    s = (KOK / "deploy/hermes/skills/meridian-olcum/SKILL.md").read_text(encoding="utf-8")
    assert "ops/olcum.py" in s, "skill aracı adıyla göstermiyor"
    assert "name:" in s and "description:" in s, "SKILL.md frontmatter eksik"


def test_SKILL_DIZINI_HERMESE_KAYITLI():
    """SKILL.md'nin bir OKUYUCUSU olmalı (YASA 6): hermes yalnız `~/.hermes/skills/`i ve
    config.yaml'daki `skills.external_dirs`i tarar. Depodaki skill dizini oraya kayıtlı
    değilse dosya var ama hiç yüklenmez — o zaman görev 3 tamamen dekoratiftir.

    Bu çivi STRING ARAMASI yapmaz: SKILL.md'nin GERÇEKTEN durduğu dizini diskten türetir
    (`skill_md.parent.parent`) ve config.yaml'daki kayıtlı dizin(ler)in GERÇEKTEN o dizine
    işaret edip etmediğini yol parçalarını karşılaştırarak sınar. `external_dirs` silinirse
    veya skill başka bir dizine taşınırsa (config güncellenmeden) bu çivi kırmızıya düşer.
    """
    skill_md = KOK / "deploy/hermes/skills/meridian-olcum/SKILL.md"
    assert skill_md.exists(), f"{skill_md} YOK"
    skills_koku = skill_md.parent.parent  # SKILL.md'nin GERÇEKTEN içinde durduğu skills kökü
    beklenen = skills_koku.relative_to(KOK).parts  # diskten türetildi, uydurulmadı

    cfg_yolu = KOK / "deploy/hermes/config.yaml"
    assert cfg_yolu.exists(), f"{cfg_yolu} YOK"
    cfg = yaml.safe_load(cfg_yolu.read_text(encoding="utf-8")) or {}
    kayitli = [str(d) for d in ((cfg.get("skills") or {}).get("external_dirs") or [])]

    def _ayni_dizin(yol: str) -> bool:
        parcalar = pathlib.PurePosixPath(yol).parts
        return parcalar[-len(beklenen):] == beklenen

    assert any(_ayni_dizin(d) for d in kayitli), (
        f"SKILL.md'nin gerçek dizini ({skills_koku}) config.yaml skills.external_dirs'te "
        f"kayıtlı değil: {kayitli!r} — hermes bu skill'i asla taramaz, dosya okuyucusuz kalır"
    )


# --- FIX ROUND 1 (2026-08-29, KRİTİK) --------------------------------------------------------
# İlk sürüm yalnız DÜZ DİZE LİTERALİNİ (`obs.warn("ad", …)`) yakalayan bir regex kullanıyordu.
# Bağımsız ölçüm: bu, canlının EN YÜKSEK ÖNCELİKLİ alarm sınıfında SAHTE SIFIR üretiyordu —
# `obs.alarm(obs.ALARM_MIRROR_DRIFT, …)` (8 çağrı yeri), `obs.alarm(obs.ALARM_NAKED_POSITION, …)`
# (2), `obs.alarm(obs.ALARM_TRAIL_DESYNC, …)` (1) hiçbiri regex'in gördüğü biçimde değildi —
# adlandırılmış SABİT, depodaki BASKIN alarm yazım biçimi. BROKER_REJECT durumu daha da
# kötüydü: araç sessizce YANLIŞ bir adla (`broker_rejects_acked`, gerçek ama AYRI bir olay)
# eşleşiyordu — temiz bir ıska değil, YANLIŞ kanıt. state/notify_undelivered.json canlıda bu
# ikisinden (MIRROR_DRIFT: 51, NAKED_POSITION: 9) teslim edilememiş alarm biriktiriyor — yani
# aracın kaçırdığı şey hipotetik değil, o an ATEŞLENMEKTE olan gerçek alarmlar.
#
# Her nail aşağıda AYRI bir çözümleme sınıfını sınar; hiçbiri diğerinin vekili değildir.


def test_SABIT_ALARM_ADI_COZULUR():
    """`obs.alarm(obs.ALARM_MIRROR_DRIFT, …)` — adlandırılmış ALARM_ sabiti. Bu çözülmezse
    canlının en yüksek öncelikli alarm sınıfı (8 çağrı yeri) sahte sıfır üretir."""
    mod = _yukle()
    adlar = mod.olay_adlari("mirror_drift")
    assert "MIRROR_DRIFT" in adlar, f"adlandırılmış ALARM_ sabiti çözülmedi: {adlar}"


def test_MODUL_SEVIYESI_SABIT_COZULUR():
    """`meridian/sermaye.py`: modül-seviyesi `EVENT = "paper_equity_reset"` + ayrı satırda
    `obs.warn(EVENT, …)`. Bu, adlandırılmış ALARM_ sabitinden FARKLI bir çözümleme yolu —
    `obs.py` dışında, çağrıyı yapan modülün KENDİ sabiti."""
    mod = _yukle()
    assert "paper_equity_reset" in mod.olay_adlari("paper_equity_reset")


def test_FSTRING_DESENI_GORUNUR():
    """`meridian/streamhealth.py`: `obs.warn(f"{prefix}_flag_decayed", …)` sessizce
    KAYBOLMAMALI — kesin bir ad çözülemese bile bir ARAMA DESENİ olarak yakalanmalı, yoksa
    `flag_decayed` arayan biri yine sahte sıfır alır."""
    mod = _yukle()
    assert mod.olay_adlari("flag_decayed"), "f-string olay deseni hiç yakalanmadı"


def test_COZULEMEYEN_SAYISI_API_UZERINDEN_GORULUR():
    """Statik olarak çözülemeyen çağrılar (ör. `obs.log(olay, …)` — `olay` bir fonksiyon
    parametresi) SESSİZCE YUTULMAMALI. Sayı PROGRAMATİK olarak erişilebilir olmalı — yalnız
    CLI stdout'una gömülü bir yan not değil (UYDURMA YASAĞI aracın kendisine de uygulanır)."""
    mod = _yukle()
    t = mod.tara()
    assert t.cozulemeyen > 0, "çözülemeyen çağrı sayısı API'den görünmüyor veya sıfır"


def test_MAIN_BULUNAN_OLAYDA_SIFIR_DONER_VE_ADI_BASAR(capsys):
    """`main()`in çıkış kodu artık YÜK TAŞIYOR (review notu) — kapsanmalı."""
    mod = _yukle()
    kod = mod.main(["olay", "benimse"])
    cikti = capsys.readouterr().out
    assert kod == 0
    assert "adet_benimsendi" in cikti


def test_MAIN_BULUNAMAYAN_DESENDE_BIR_DONER_VE_IKI_OLASILIGI_ADLANDIRIR(capsys):
    """Sıfır sonuç DÜRÜST olmalı: eskisi gibi TEK bir iddia ('bu bir ALAN adı olabilir')
    dayatmamalı — 'çözemedim' olasılığını da adlandırmalı ve çözülemeyen sayısını göstermeli.
    Boş liste tek başına 'arıza yok' kanıtı değildir."""
    mod = _yukle()
    kod = mod.main(["olay", "boyle_bir_olay_asla_var_olmayacak_zzz"])
    cikti = capsys.readouterr().out
    assert kod == 1
    assert "ALAN" in cikti, "ilk olasılık (alan adı) mesajdan kayboldu"
    assert "çözemedi" in cikti.lower() or "çözülemedi" in cikti.lower(), (
        "ikinci olasılık (statik çözümleyicinin sınırı) mesajda yok")
    assert "çözülemeyen" in cikti.lower(), "kalıntı kör nokta sayısı raporlanmıyor"


def test_MAIN_HER_KOSULDA_COZULEMEYEN_SAYISINI_RAPORLAR(capsys):
    """Bulgu olsa da olmasa da: kalıntı kör nokta her koşumda beyan edilir, yalnız sıfır
    sonuçta değil — aksi hâlde bulunan kısa bir liste 'tam liste' sanılabilir."""
    mod = _yukle()
    mod.main(["olay", "benimse"])
    cikti = capsys.readouterr().out
    assert "çözülemeyen çağrı yeri:" in cikti


# --- FIX ROUND 2 (2026-08-29, KRİTİK — üçüncü kör nokta) -------------------------------------
# Round 1'in çözümleyicisi ALICIYI hard-code ediyordu (`f.value.id == "obs"`). Bu depoda YAYGIN
# bir kalıp bunu atlıyor: `from . import obs as _obs` (çoğunlukla `except` blokları içinde —
# 44 çağrı yeri, düzinelerce takma ad: `_obs`, `_o`, `_o2`, `_obs_h`, `_obs0`, `_obsL`, `_od`,
# `_os2`, …). Bu çağrılar hem ÇÖZÜLEMİYORDU HEM SAYILMIYORDU — round-1'in kendi dürüstlük
# mekanizması (`cozulemeyen` SAYACI) bunları GÖRMÜYORDU, çünkü sayaç da yalnız "obs.X(" metnini
# arıyordu (bir ENUMERASYONDU, bilinmeyen bir biçimi YAKALAYAMAZDI). `ALARM_ARAMA_HAVUZU_OLU` —
# 2026-08-25'te TAM DA sessiz-arızayı kapatmak için eklenmiş bir jeton — bu yüzden görünmezdi:
# arızayı kapatmak için var olan alarmın KENDİSİ, arızaları kapatmak için var olan ARAÇ
# tarafından kaçırılıyordu. Çare: (1) takma adları importlardan TÜRET (hard-code YOK),
# (2) `cozulemeyen`i ÇIKARMA ile tanımla (tüm log/warn/error/alarm çağrıları − çözülenler) ki
# gelecekteki bilinmeyen bir biçim de OTOMATİK sayılsın, elle eklenmesi gerekmesin.


def test_ALIASLI_LITERAL_COZULUR():
    """`meridian/reflect.py`: `from . import obs as _obs` + `_obs.warn("arama_havuzu_zaman_asimi", …)`.
    Alıcı `obs` DEĞİL `_obs` — hard-code edilmiş bir alıcı adı bunu asla göremez."""
    mod = _yukle()
    assert "arama_havuzu_zaman_asimi" in mod.olay_adlari("arama_havuzu_zaman_asimi")


def test_ALIASLI_SABIT_COZULUR_CIFT_DOLAYLI():
    """`_obs.alarm(_obs.ALARM_ARAMA_HAVUZU_OLU, …)` — ÇİFT dolaylılık: hem ALICI (`_obs`) hem
    ARGÜMAN (`_obs.ALARM_ARAMA_HAVUZU_OLU`) takma ad üzerinden. Bu jeton 2026-08-25'te TAM DA
    sessiz bir arızayı kapatmak için eklenmişti — aracın onu kaçırması en ağır vakaydı."""
    mod = _yukle()
    assert "ARAMA_HAVUZU_OLU" in mod.olay_adlari("arama_havuzu_olu")


def test_COZULEMEYEN_YAPISAL_TAMDIR_BILINMEYEN_BICIME_TEPKI_VERIR(tmp_path):
    """Sayaç artık EL İLE BAKIMLI bir liste değil, ÇIKARMA ile türetilir: (metod adı
    log/warn/error/alarm olan TÜM çağrı yerleri) − (gerçekten çözülenler). Bunu kanıtlamak
    için gerçek depoda OLMAYAN, UYDURULMUŞ iki çağrı biçimi kuruyoruz (izole bir `tmp_path`
    içinde — repo'ya dokunmadan): sayaç bunları ÖNCEDEN TANIYARAK değil YAPISAL OLARAK
    yakalamalı, yoksa bu çivi anlamsız bir tautoloji olur (bkz. `test_AYRISTIRICI_BAYAT_DEGIL`
    ile aynı türden nöbetçi mantık)."""
    mod = _yukle()
    meridian_dizini = tmp_path / "meridian"
    meridian_dizini.mkdir()
    (meridian_dizini / "obs.py").write_text(
        '"""sahte obs modülü — yalnız import bağlamak için var."""\n', encoding="utf-8")
    (meridian_dizini / "sahte.py").write_text(
        "from . import obs\n"
        "import logging as ilgisiz\n"
        "\n"
        "def f(ad_getir):\n"
        "    obs.warn(ad_getir(), x=1)   # BİLİNMEYEN biçim: ilk arg bir Call — 4 sınıftan hiçbiri değil\n"
        "    ilgisiz.warn('mesaj')        # obs'a HİÇ BAĞLI DEĞİL — yine de metod adı eşleşiyor\n",
        encoding="utf-8",
    )
    t = mod.tara(tmp_path)
    assert t.toplam_cagri_sayisi == 2, f"toplam çağrı sayımı ALICIDAN bağımsız olmalı: {t}"
    assert t.cozulemeyen == 2, f"beklenmeyen çağrı biçimleri ÇIKARMA ile yakalanmadı: {t}"
    assert not t.adlar and not t.desenler, "uydurulmuş biçim yanlışlıkla bir ad/desen üretti"


# --- FIX ROUND 4 (2026-08-29, ASIL KUSUR) ----------------------------------------------------
# Round 1-3'ün her biri BİR MEKANİZMAYI düzeltti ve ardından TAMLIĞI YENİ SÖZCÜKLERLE YENİDEN
# İDDİA ETTİ. Round 3'ten sonra SKILL.md "her NE olursa olsun çözemediğimiz her şey" diyordu —
# bir dosya HİÇ OKUNMADIĞI anda bu iddia YANLIŞ olur. Ölçülmüş dördüncü delik:
#
#     ops/olcum.py olay oneri_brifingi_teslim        → OLAY YOK   (ops/oneri_brifingi.py)
#     ops/olcum.py olay alarm_backlog_digest_teslim  → OLAY YOK   (ops/alarm_backlog_digest.py)
#
# İkisi de CANLI, ikisi de mümkün olan EN DÜZ biçim (`obs.log("literal", …)`). Görünmezdiler
# çünkü `tara()` yalnız `meridian/`i glob'luyordu; `cozulemeyen` sayacı da KIPIRDAMIYORDU —
# okunmayan dosya HİÇBİR kovaya düşmez, "yapısal çıkarma" da onu göremez.
#
# DÜZELTİLEN ŞEY DÖRDÜNCÜ DELİK DEĞİL, DELİK ÜRETEN KALIP. Kurulan değişmez:
#     ARAÇ TAMLIK İDDİA ETMEZ. HER CEVABIN YANINDA KENDİ KAPSAMINI BEYAN EDER.
# Aşağıdaki çiviler bu değişmezi çakar; son ikisi POKA-YOKE'dir: BASILAN kapsam ile TARANAN
# kapsam tek kaynaktan gelmezse (biri güncellenip diğeri unutulursa) suite KIRMIZIYA düşer.


def test_OPS_KOKU_TARANIR_CANLI_OLAY_BULUNUR():
    """Dördüncü delik: `ops/` altındaki GERÇEK, CANLI olaylar. En düz biçim
    (`obs.log("literal", …)`) — çözümleyici sınıfı değil, KAPSAM eksikti."""
    mod = _yukle()
    assert "oneri_brifingi_teslim" in mod.olay_adlari("oneri_brifingi_teslim"), (
        "ops/oneri_brifingi.py'deki canlı olay görünmüyor — kapsam `ops/`i kapsamıyor")
    assert "alarm_backlog_digest_teslim" in mod.olay_adlari("alarm_backlog_digest_teslim"), (
        "ops/alarm_backlog_digest.py'deki canlı olay görünmüyor")


def test_MAIN_HER_KOSULDA_TARANAN_KAPSAMI_BASAR(capsys):
    """Kapsam BULGULU koşumda da BOŞ koşumda da basılmalı. Boş sonuç + görünür kapsam
    DÜRÜSTTÜR; boş sonuç + tamlık iması ARIZANIN KENDİSİDİR. Okuyucu kaynağı açmadan neye
    bakıldığını GÖREBİLMELİ."""
    mod = _yukle()
    t = mod.tara()

    mod.main(["olay", "benimse"])                       # BULGULU koşum
    dolu = capsys.readouterr().out
    mod.main(["olay", "boyle_bir_olay_asla_var_olmayacak_zzz"])   # BOŞ koşum
    bos = capsys.readouterr().out

    for ad, cikti in (("bulgulu", dolu), ("boş", bos)):
        satirlar = [s for s in cikti.splitlines() if s.startswith("# taranan kapsam:")]
        assert len(satirlar) == 1, f"{ad} koşumda kapsam satırı tam bir kez basılmalı: {cikti!r}"
        for k in t.taranan_kokler:
            assert f"{k}/" in satirlar[0], (
                f"{ad} koşumda taranan kök `{k}` beyanda yok: {satirlar[0]!r}")


def test_BEYAN_EDILEN_KAPSAM_GERCEKTEN_TARANANDIR():
    """POKA-YOKE (1/2) — İKİ YÖNLÜ: beyan edilen köklerin altındaki `*.py` sayısı, taramanın
    GERÇEKTEN açtığı dosya sayısına EŞİT olmalı.
      · Beyan edilmemiş bir kök gizlice taranırsa → taranan sayı BÜYÜR, eşitlik bozulur.
      · Beyan edilen bir kök taranmazsa           → taranan sayı KÜÇÜLÜR, eşitlik bozulur.
    Böylece `taranan_kokler` dekoratif bir literal OLAMAZ: gerçek yürüyüşle ölçülür."""
    mod = _yukle()
    t = mod.tara()
    assert t.taranan_kokler, "hiçbir kök taranmadığı beyan edildi — bu bir arıza"
    beklenen = sum(len(list((KOK / k).rglob("*.py"))) for k in t.taranan_kokler)
    assert t.taranan_dosya_sayisi == beklenen, (
        f"BEYAN ile TARAMA ayrıştı: beyan edilen kökler {t.taranan_kokler} altında {beklenen} "
        f"dosya var ama tarama {t.taranan_dosya_sayisi} dosya açtı")


def test_KAPSAM_BEYANI_TARAMAYLA_BIRLIKTE_HAREKET_EDER(monkeypatch, capsys):
    """POKA-YOKE (2/2): kök listesi DEĞİŞTİĞİNDE hem TARAMA hem BEYAN birlikte hareket etmeli.
    Kapsam cümlesi bir yere elle yazılmış olsaydı (`"meridian/, ops/"`), tarama daralırken
    beyan olduğu yerde kalırdı — round 1-3'ün tam kalıbı: mekanizma değişti, İDDİA eski kaldı.
    Bu çivi tek kaynağı kanıtlar: `TARANAN_KOKLER`."""
    mod = _yukle()
    monkeypatch.setattr(mod, "TARANAN_KOKLER", ("ops",))

    t = mod.tara()
    assert t.taranan_kokler == ("ops",), f"tarama tek kaynağı izlemiyor: {t.taranan_kokler}"
    assert "adet_benimsendi" not in mod.olay_adlari(""), (
        "kapsam `ops/`e daraltıldı ama `meridian/` olayı hâlâ dönüyor — tarama GERÇEKTEN daralmadı")

    mod.main(["olay", "teslim"])
    satir = [s for s in capsys.readouterr().out.splitlines() if s.startswith("# taranan kapsam:")]
    assert len(satir) == 1, "kapsam satırı basılmadı"
    assert "ops/" in satir[0], f"daraltılmış kapsam beyanda yok: {satir[0]!r}"
    assert "meridian/" not in satir[0], (
        f"BEYAN taramayı izlemiyor — artık taranmayan kök hâlâ beyan ediliyor: {satir[0]!r}")


def test_KAPSAM_DISI_KOK_NE_TARANIR_NE_BEYAN_EDILIR(tmp_path):
    """Kapsam gerçek bir SINIR olmalı, süs değil: listede olmayan bir dizindeki olay
    BULUNMAMALI (ve bu, sessiz bir kayıp değil — beyan onu kapsam dışı ilan eder). İkinci
    ağaç ters yönü sınar: var OLMAYAN bir kök 'taradım' diye BEYAN EDİLMEZ."""
    mod = _yukle()

    a = tmp_path / "a"
    for d in ("meridian", "ops", "baska"):
        (a / d).mkdir(parents=True)
    (a / "meridian/obs.py").write_text('"""sahte obs."""\n', encoding="utf-8")
    (a / "meridian/m.py").write_text(
        "from . import obs\ndef f():\n    obs.log('kapsam_ici_meridian')\n", encoding="utf-8")
    (a / "ops/o.py").write_text(
        "from meridian import obs\ndef f():\n    obs.log('kapsam_ici_ops')\n", encoding="utf-8")
    (a / "baska/b.py").write_text(
        "from meridian import obs\ndef f():\n    obs.log('kapsam_disi_baska')\n", encoding="utf-8")

    t = mod.tara(a)
    assert t.taranan_kokler == ("meridian", "ops"), t.taranan_kokler
    assert "kapsam_ici_meridian" in t.adlar and "kapsam_ici_ops" in t.adlar, t.adlar
    assert "kapsam_disi_baska" not in t.adlar, (
        "kapsam DIŞINDAKİ dizin taranmış — sınır gerçek değil")
    assert t.toplam_cagri_sayisi == 2, (
        f"kapsam dışı çağrı toplama karışmış: {t.toplam_cagri_sayisi}")

    b = tmp_path / "b"
    (b / "meridian").mkdir(parents=True)
    (b / "meridian/obs.py").write_text('"""sahte obs."""\n', encoding="utf-8")
    t2 = mod.tara(b)
    assert t2.taranan_kokler == ("meridian",), (
        f"var olmayan bir kök 'tarandı' diye beyan edildi: {t2.taranan_kokler}")


def test_SKILL_TAMLIK_IDDIA_ETMEZ_SINIRI_SOYLER():
    """SKILL.md okuyucuyu SAHTE SIFIRA karşı uyarmalı — ve bunu TAMLIK İDDİA ETMEDEN yapmalı.
    Round 3'ten sonra orada "her NE olursa olsun çözemediğimiz her şey" yazıyordu; tam da o
    cümle, okunmayan bir dosyanın (dördüncü delik) sessizce kaybolmasını 'kapsanmış' gibi
    gösteriyordu. Kökler ARACIN sabitinden türetilir: yeni bir kök eklenip belge
    güncellenmezse bu çivi kırmızıya düşer (poka-yoke belgeye kadar uzanır)."""
    mod = _yukle()
    s = (KOK / "deploy/hermes/skills/meridian-olcum/SKILL.md").read_text(encoding="utf-8")
    assert "her NE olursa olsun çözemediğimiz her şey" not in s, (
        "totalize eden iddia geri gelmiş — kapsam dışı her şey bu cümleyi YANLIŞ yapar")
    for k in mod.TARANAN_KOKLER:
        assert f"{k}/" in s, f"belge taranan kökü (`{k}/`) adlandırmıyor — okuyucu sınırı göremez"
    assert "taranan kapsam" in s.lower(), "belge kapsam satırının nasıl okunacağını söylemiyor"


def test_KAPSAM_BEYANI_DIZINI_DEGIL_DOSYA_DESENINI_SOYLER(capsys):
    """BEŞİNCİ DELİK SINIFI (bu turda avlandı, ölçüldü): `ops/keepalive.sh:46` CANLI bir alarmı
    kabuktan basıyor —

        .venv/bin/python -c "from meridian import obs; obs.alarm('MECHANISM_STALE', …)"

    Dosya `ops/` ALTINDA ama `.py` DEĞİL; araç onu asla açmaz. "taranan kapsam: ops/" cümlesi
    ise "ops/ altındaki her şey" diye okunur — yani dizin adı BAŞLI BAŞINA bir tamlık imasıdır.
    Beyan bu yüzden dizini değil DESENİ söylemeli, ve desen taramanın kullandığı desenin TA
    KENDİSİ olmalı (poka-yoke dosya türüne kadar uzanır)."""
    mod = _yukle()
    mod.main(["olay", "benimse"])
    satir = [s for s in capsys.readouterr().out.splitlines()
             if s.startswith("# taranan kapsam:")]
    assert len(satir) == 1, "kapsam satırı basılmadı"
    for k in mod.TARANAN_KOKLER:
        assert f"{k}/**/{mod.TARANAN_DOSYA_DESENI}" in satir[0], (
            f"beyan dosya desenini söylemiyor — `{k}/` çıplak dizin adı tamlık ima eder: "
            f"{satir[0]!r}")


# --- FIX ROUND 5 (2026-08-29, dal-sonu denetimi) ---------------------------------------------
# AYRIŞTIRILAMAYAN DOSYA = ROUND 4'ÜN ARIZASININ DOSYA GRANÜLERLİĞİNDEKİ HÂLİ. `tara()` bir
# `SyntaxError`ü `continue` ile yutuyordu; o dosya `taranan_dosya_sayisi`na SAYILIYOR (yani kapsam
# satırı "tarandı" diye beyan ediyor) ama içindeki çağrılar NE `toplam_cagri`ya NE `cozulen`e
# giriyordu — "hiçbir kovaya düşmeyen" tam da o şekil, ve yapısal ÇIKARMA onu göremez.


def test_AYRISTIRILAMAYAN_DOSYA_SAYILIR_HICBIR_KOVAYA_DUSMEDEN_KAYBOLMAZ(tmp_path):
    """Parse edilemeyen bir dosya SESSİZCE atlanamaz: kapsam satırı onu "taradım" diye sayarken
    çağrıları hiçbir sayaca düşmez. Sayı AYRI bir alanla beyan edilir (UYDURMA YASAĞI: ölçülemeyen
    şey `None`/sayı + neden olarak görünür, gizlenmez)."""
    mod = _yukle()
    m = tmp_path / "meridian"
    m.mkdir()
    (m / "obs.py").write_text('"""sahte obs."""\n', encoding="utf-8")
    (m / "saglam.py").write_text(
        "from . import obs\ndef f():\n    obs.log('saglam_olay')\n", encoding="utf-8")
    (m / "bozuk.py").write_text(
        "from . import obs\ndef f(:\n    obs.log('bu_olay_ASLA_GORULMEZ')\n", encoding="utf-8")

    t = mod.tara(tmp_path)
    assert t.taranan_dosya_sayisi == 3, t.taranan_dosya_sayisi
    assert t.ayristirilamayan_dosya == 1, (
        f"parse edilemeyen dosya sessizce yutuldu: {t}")
    assert "saglam_olay" in t.adlar
    assert "bu_olay_ASLA_GORULMEZ" not in t.adlar
    assert t.toplam_cagri_sayisi == 1, (
        f"ayrıştırılamayan dosyanın çağrıları toplama giremez (görülmediler): {t}")


def test_MAIN_HER_KOSULDA_AYRISTIRILAMAYAN_SAYISINI_RAPORLAR(capsys):
    """`cozulemeyen` gibi: bulgu olsun olmasın HER koşumda basılır. Bugün sıfır olması satırı
    gereksiz yapmaz — okuyucunun "0 sonuç" ile "1 dosya hiç okunamadı" arasını ayırabilmesi için
    sayının GÖRÜNMESİ gerekir, ve sıfır beyanı da bir ölçümdür."""
    mod = _yukle()
    mod.main(["olay", "benimse"])
    dolu = capsys.readouterr().out
    mod.main(["olay", "boyle_bir_olay_asla_var_olmayacak_zzz"])
    bos = capsys.readouterr().out
    for ad, cikti in (("bulgulu", dolu), ("boş", bos)):
        satirlar = [s for s in cikti.splitlines() if s.startswith("# ayrıştırılamayan dosya:")]
        assert len(satirlar) == 1, (
            f"{ad} koşumda ayrıştırılamayan-dosya satırı tam bir kez basılmalı: {cikti!r}")
