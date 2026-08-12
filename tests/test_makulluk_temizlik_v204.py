"""MAKULLÜK dedektörünün iki GERÇEK bulgusunun kapanış testleri (v204, 2026-08-07).

Bu dosya iki bulguyu birden çiviler; ikisinin de ortak dersi aynıdır: **bir dedektörü susturmanın
iki yolu vardır ve yalnız biri dürüsttür.** Deseni gevşetmek (bekçiyi kör etmek) yasak; artığın ya
da yanlış sınıflamanın KAYNAĞINI onarmak şart.

BULGU 1 — `yeniden_hesap:orphan_state_files` canlıda 7 dosya sayıyordu.
  Kök: `dagit.sh` versiyonlu state kopyasının yedeğini `state/` İÇİNE yazıyordu, yani dedektörün
  taradığı dizine. Her dağıtım bir yetim daha doğuruyordu (6/7 dosya bu sınıftan). Onarım:
  yedek `backups/state/`e gider + `ops/state_yetim_temizle.sh` eski artıkları TAŞIR (silmez).
  7. dosya `auth.json`: dedektörün KÖR NOKTASI — okuyucusu ölçüldü, `DECLARED_SINKS`e beyanlı.

BULGU 2 — `eleme:component_ic.eslesme:sema_elemesi` + `eleme:threshold_curve.eslesme:sema_elemesi`.
  BEYANLI EK (v238, 2026-08-13): dedektörün ÜÇÜNCÜ sınıfı ölçüldü — DAMGALI GÖÇ ARŞİVİ
  (`state/scoreboard.json.migrated-20260812-201359-p192112`, 2026-08-12 dağıtım penceresi).
  Bu dosya bir yedek ARTIĞI değil, `store._bayat_defter_suzgeci`in çarpışma dalıdır ve düz
  `.migrated` ZATEN tanınıyordu; dedektör artık damgalı biçimi de TÜRETEREK tanır ve
  `migrasyon_artigi` adıyla SAYAR. Aşağıdaki `test_yedek_artigi_HALA_yetim_sayilir` bekçisi
  DEĞİŞMEDİ ve v238'de yeniden çivilendi — `.bak-` hâlâ yetimdir, desen GEVŞETİLMEDİ.
  Kapanış: `tests/test_ariza_turu_v238.py` [C] bölümü.

  Kök TEK: yedi satırın hepsi `DD`, hepsi cf katmanı, hepsi 2022-11-10…2024-07-31 arası. `DD`nin
  bütünlük kaydı `guvenli_baslangic: 2025-11-04` (2025-11-03 ölçek dikişi, K1) → `measurement_bars`
  o tarihten öncesini ölçüm çerçevesinden BİLEREK çıkarıyor. Yani `sema:` (= veri sözleşmesi hatası)
  YANLIŞ SINIFLAMAYDI: satır beklenen alanı taşıyor, çerçeve barı taşımıyor ve taşımaması KARAR.
"""
from __future__ import annotations

import json
import pathlib
import subprocess

import pytest

REPO = pathlib.Path(__file__).resolve().parent.parent
OLCUM = REPO / "research" / "olcumler" / "makulluk_2026-08-07"


# =================================================================================================
# A) dagit.sh — YEDEK ARTIK `state/` İÇİNE DÜŞMÜYOR
# =================================================================================================
def _dagit() -> str:
    return (REPO / "dagit.sh").read_text()


def test_dagit_yedegi_state_DISINA_yazar():
    """KÖK ONARIMI: `cp -p …/state/$_sf …/state/$_sf.bak-$_damga` satırı her dağıtımda dedektörün
    taradığı dizine bir dosya bırakıyordu. Yedek hâlâ alınır — yalnız yeri `backups/state/`."""
    src = _dagit()
    assert "/opt/meridian/backups/state" in src, "yedek dizini betikte geçmiyor"
    assert "mkdir -p $_yedek_dizin" in src, "hedef dizin oluşturulmuyor — ilk dağıtımda cp düşer"
    # ASIL ÇİVİ: state/ içine yedek yazan desen GERİ GELMESİN.
    assert "/opt/meridian/state/$_sf.bak-" not in src, \
        "yedek yine state/ içine yazılıyor — orphan dedektörü her dağıtımda bir satır daha sayar"


def test_dagit_mesajlari_YENİ_yolu_gosterir():
    """Mesaj eski yolu gösterirse operatör yedeği yanlış yerde arar; geri dönüş yolu kâğıt üstünde
    kalır. (Bu tur onarılan sınıfın kendisi: doğru iş, yanlış adres.)"""
    src = _dagit()
    assert "yedek: backups/state/$_sf.bak-$_damga" in src, "başarı mesajı eski yolu gösteriyor"
    assert src.count("yedek: backups/state/") >= 2, "hata dalında da yeni yol yazmalı"
    assert "cp -p $_yedek_dizin/$_sf.bak-$_damga /opt/meridian/state/$_sf" in src, \
        "GERİ DÖNÜŞ KOMUTU yazılı değil — yedek almak, geri koymayı bilmeden yarım bir güvencedir"


def test_backups_rsync_disinda_kalir():
    """Yedek dizini dağıtıma binmemeli: `rsync --delete` onları A1'de SİLERDİ (2026-08-01'de
    `.dash.env` tam olarak böyle gitti). Dışlama listesi bu güvencenin taşıyıcısı."""
    assert "--exclude 'backups'" in _dagit()


# =================================================================================================
# B) ops/state_yetim_temizle.sh — TAŞIR, SİLMEZ; CANLI ARTEFAKTA DOKUNMAZ
# =================================================================================================
BETIK = REPO / "ops" / "state_yetim_temizle.sh"

# Canlıda 2026-08-06'da ÖLÇÜLEN yetim listesi (dedektörün saydığı 7 dosyanın 6'sı).
CANLI_ARTIKLAR = ("goal.yaml.bak-202608021652", "goal.yaml.bak-202608030421",
                  "goal.yaml.bak-202608031627", "bounds.yaml.bak-202608021652",
                  "earnings.csv.20260803T100416Z.bak", "earnings.csv.sedbak")
# Aynı dizinde duran ve ASLA taşınmaması gereken CANLI dosyalar.
CANLI_DOSYALAR = ("auth.json", "goal.yaml", "bounds.yaml", "trades.jsonl", "component_ic.json")


@pytest.fixture
def kok(tmp_path):
    st = tmp_path / "state"
    st.mkdir()
    for f in CANLI_ARTIKLAR:
        (st / f).write_text(f"yedek-icerik:{f}\n")
    for f in CANLI_DOSYALAR:
        (st / f).write_text("{}\n")
    return tmp_path


def _kos(kok_dizin, *args):
    return subprocess.run(["bash", str(BETIK), "--yerel", str(kok_dizin), *args],
                          capture_output=True, text=True, timeout=120)


def test_betik_sozdizimi_gecerli():
    r = subprocess.run(["bash", "-n", str(BETIK)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def test_kuru_kosu_VARSAYILAN_ve_hicbir_seye_dokunmaz(kok):
    """Argümansız çağrı bir ŞEY YAPMAZ. Bir temizlik betiğinin varsayılanı 'uygula' olsaydı,
    yanlış kökle çalıştırılan tek bir çağrı geri dönüşü olmayan bir taşıma yapardı."""
    r = _kos(kok)
    assert r.returncode == 0, r.stderr
    assert "KURU KOŞU" in r.stdout
    for f in CANLI_ARTIKLAR:
        assert (kok / "state" / f).exists(), f"kuru koşu dosyayı taşıdı: {f}"
    assert not (kok / "backups").exists(), "kuru koşu hedef dizini bile oluşturmamalı"
    # Ne yapılacağını YAZAR (kuru koşu sessiz olmaz — operatör hükmü çıktıdan verir).
    for f in CANLI_ARTIKLAR:
        assert f in r.stdout, f"kuru koşu {f} dosyasını listelemiyor"


def test_uygula_yedekleri_TASIR_canliyi_BIRAKIR(kok):
    """Taşır (mv), silmez: bu dosyalar geri dönüş kopyalarıdır. Ve YALNIZ yedek sonekli olanlar —
    `auth.json` taşınsaydı operatör kendi panosuna giremezdi."""
    r = _kos(kok, "--uygula")
    assert r.returncode == 0, r.stderr
    for f in CANLI_ARTIKLAR:
        assert not (kok / "state" / f).exists(), f"{f} hâlâ state/ içinde"
        hedef = kok / "backups" / "state" / f
        assert hedef.exists(), f"{f} yedek dizinine TAŞINMAMIŞ — silinmiş olabilir"
        assert hedef.read_text() == f"yedek-icerik:{f}\n", f"{f} içeriği bozuldu"
    for f in CANLI_DOSYALAR:
        assert (kok / "state" / f).exists(), f"CANLI dosya taşındı: {f} — betik sınırını aştı"
    assert "state/ içinde yedek artığı KALMADI" in r.stdout


def test_var_olan_yedegin_UZERINE_yazmaz(kok):
    """Bir geri-dönüş kopyasını başka bir geri-dönüş kopyasıyla ezmek, temizliğin veri kaybına
    döndüğü andır. `mv -n`: hedefte aynı ad varsa dosya YERİNDE KALIR ve çıktı bunu söyler."""
    hedef = kok / "backups" / "state"
    hedef.mkdir(parents=True)
    (hedef / CANLI_ARTIKLAR[0]).write_text("ONCEKI-YEDEK\n")
    r = _kos(kok, "--uygula")
    assert r.returncode == 0, r.stderr
    assert (hedef / CANLI_ARTIKLAR[0]).read_text() == "ONCEKI-YEDEK\n", "eski yedek EZİLDİ"
    assert (kok / "state" / CANLI_ARTIKLAR[0]).exists(), "kaynak silinmiş ama hedefe yazılmamış"
    assert "HÂLÂ DURAN" in r.stdout, "taşınamayan dosya sessizce geçilmiş"


def test_dedektor_kosamadiginda_SAYI_UYDURULMAZ(kok):
    """UYDURMA YASAĞI: kök bir Meridian checkout'u değilse dedektör koşamaz. Cevap 'temiz' DEĞİL,
    'ölçülemedi + neden'dir — atlanan adım adıyla yazılır."""
    r = _kos(kok)
    assert "dedektör ADIMI ATLANDI" in r.stdout
    assert "Meridian checkout'u değil" in r.stdout


# =================================================================================================
# C) auth.json — DEDEKTÖRÜN KÖR NOKTASI, BEYANLA KAPATILDI
# =================================================================================================
def test_auth_json_DECLARED_SINKS_te_ve_gerekce_OKUYUCUYU_ADLANDIRIYOR():
    """Boş beyan yasak: `learning_loop_open.json` vakasında beyanın kendisi eksik tüketiciyi
    örtmüştü. Gerekçe HANGİ MODÜL NASIL OKUYOR sorusunu yazmalı."""
    from meridian import codelaw
    g = codelaw.DECLARED_SINKS.get("auth.json")
    assert g, "auth.json beyan edilmemiş — dedektör her turda gerçek olmayan bir yetim sayar"
    for terim in ("auth._read", "verify_session", "api.py", "auth_cli"):
        assert terim in g, f"gerekçe '{terim}' okuyucusunu adlandırmıyor: {g}"


def test_auth_json_GERCEKTEN_okunuyor(sandbox_state):
    """İDDİA DEĞİL ÖLÇÜM: beyan 'okuyucusu var' diyorsa bu FONKSİYONEL olarak gösterilebilmeli.
    Dosyayı sandbox'a yazıp `auth.password_set()` sormak, okuma zincirinin tamamını kanıtlar."""
    from meridian import auth
    assert auth.password_set() is False, "parola kurulmamışken True — auth başka bir dosyaya bakıyor"
    (sandbox_state / "auth.json").write_text(json.dumps({"salt": "eA==", "hash": "eA==",
                                                         "algo": "scrypt-n15-r8-p1"}))
    assert auth.password_set() is True, \
        "state/auth.json yazıldı ama auth okumadı — beyan yanlış olurdu"
    assert auth._auth_file() == sandbox_state / "auth.json"


def test_orphan_dedektoru_auth_json_icin_ARTIK_bagirmaz(sandbox_state):
    """Beyanın dedektördeki karşılığı: `recompute._orphan_state_files` `DECLARED_SINKS`i
    `known` kümesine katar. Dosya diskte dolu dursa bile satır ONU saymamalı."""
    from meridian import recompute
    (sandbox_state / "auth.json").write_text(json.dumps({"salt": "eA==", "key": "eA=="}))
    row = recompute._orphan_state_files()
    assert "auth.json" not in (row["detail"] or ""), row["detail"]


def test_yedek_artigi_HALA_yetim_sayilir(sandbox_state):
    """BEKÇİ ZAYIFLATILMADI: dedektörün deseni gevşetilmedi. Yarın `state/` içine yine bir
    `.bak-` düşerse satır ONU görmeye devam eder — onarım kaynakta, dedektörde değil."""
    from meridian import recompute
    (sandbox_state / "goal.yaml.bak-202608021652").write_text("goal: 1\nx: 2\n")
    recompute._CORPUS_CACHE.clear()
    row = recompute._orphan_state_files()
    assert row["ok"] is False and "goal.yaml.bak-202608021652" in row["detail"], row["detail"]


# =================================================================================================
# D) ŞEMA ELEMESİNİN KÖKÜ — BEYAN EDİLMİŞ DIŞLAMA, VERİ SÖZLEŞMESİ HATASI DEĞİL
# =================================================================================================
def _defter_yaz(sandbox, sembol: str, guvenli: str) -> None:
    (sandbox / "bars_integrity.json").write_text(json.dumps(
        {"rev": 1, "semboller": {sembol: {"guvenli_baslangic": guvenli, "ilk_bar": "2004-01-02",
                                          "dislanan_bar": 5172,
                                          "kirilma_listesi": [{"tarih": "2025-11-03",
                                                               "sinif": "olcek_dikisi",
                                                               "kural": "K1"}]}}}))


def test_butunluk_defterinin_disladigi_tarih_PIYASA_sinifi(sandbox_state):
    """ÖLÇÜLEN KÖK: `DD` için `guvenli_baslangic=2025-11-04`; yedi satırın hepsi bundan önce.
    Barlar ham önbellekte VAR — çerçeveden çıkaran `measurement_bars`ın KARARI. Bu bir yazılım
    hatası değil beyanlı bir dışlamadır → `piyasa:` (BİLGİ), `sema:` (BUG) değil."""
    from meridian import component_ic as cic, sieve
    _defter_yaz(sandbox_state, "DD", "2025-11-04")
    neden = cic.eslesme_nedeni("DD", "2024-07-31")
    assert neden == cic.DISLAMA_NEDENI
    assert sieve.classify(neden) == "piyasa"
    assert cic.butunluk_disladi("DD", "2024-07-31") is True
    # Sınırın ÖTESİ dışlanmaz: eşik `>=` (measurement_bars ile AYNI kural).
    assert cic.butunluk_disladi("DD", "2025-11-04") is False
    assert cic.eslesme_nedeni("DD", "2025-11-05") == "sema:bar_yok:tarih"


def test_defterde_kaydi_OLMAYAN_eksik_tarih_HALA_sema(sandbox_state):
    """BEKÇİNİN DİŞİ YERİNDE. Defterin AÇIKLAMADIĞI bir eksik bar — takvim boşluğu, hayalet seans,
    bozuk defter satırı — hâlâ veri sözleşmesi hatasıdır ve ihlal üretmeye devam eder. Aksi hâlde
    bu onarım, gerçek arıza sınıfını da susturan bir örtbas olurdu."""
    from meridian import component_ic as cic, sieve
    _defter_yaz(sandbox_state, "DD", "2025-11-04")
    neden = cic.eslesme_nedeni("ZZZZ", "2020-01-02")          # defterde kaydı yok
    assert neden == "sema:bar_yok:tarih"
    assert sieve.classify(neden) == "sema"


def test_iki_tuketici_AYNI_yasayi_kullanir():
    """TEK TANIM, İKİ TÜKETİCİ (`forward_returns` ile aynı gerekçe): eşleştirme sınıflaması iki
    dosyaya kopyalanırsa biri sessizce eski sınıfta kalır ve iki pano satırı ayrışır."""
    cic_src = (REPO / "meridian" / "component_ic.py").read_text()
    thr_src = (REPO / "meridian" / "threshold_curve.py").read_text()
    assert "cic.eslesme_nedeni(ticker, dstr)" in thr_src, "eşik eğrisi ortak yasayı çağırmıyor"
    assert 'sv.drop("sema:bar_yok:tarih")' not in thr_src, "sabit `sema:` sınıflaması geri gelmiş"
    assert 'sv.drop("sema:bar_yok:tarih")' not in cic_src, "sabit `sema:` sınıflaması geri gelmiş"
    assert "sv.drop(eslesme_nedeni(ticker, dstr))" in cic_src


def test_yeni_neden_SAYILIR_ama_ihlal_uretmez():
    """'Sessiz düşme'den çıktı demek, 'kayboldu' demek DEĞİL: satırlar eleme defterinde SAYILIR
    (`piyasa_drops`) ve panonun eleme tablosunda 'piyasa filtresi N' olarak görünür. Kaybolan tek
    şey, olmayan bir yazılım hatası için yakılan kırmızıdır."""
    from meridian import component_ic as cic, sieve
    doc = {"component_ic.eslesme": {"in": 2216, "out": 2209,
                                    "drops": {cic.DISLAMA_NEDENI: 7}, "ts": "2026-08-07T00:00:00+00:00"}}
    rep = sieve.report(doc)
    assert rep["violations"] == [], rep["violations"]
    st = rep["stages"]["component_ic.eslesme"]
    assert st["piyasa_drops"] == 7 and st["sema_drops"] == 0
    assert st["drops"][cic.DISLAMA_NEDENI] == 7, "neden defterde adıyla durmuyor"


def test_ESKI_hali_ihlal_uretiyordu_regresyon_civisi():
    """Bu testin varlık sebebi: aynı sayı `sema:` sınıfındayken pano İKİ ihlal bağırıyordu.
    Sınıflama geri alınırsa burası kırmızıya döner ve niçin değiştiği hatırlanır."""
    from meridian import sieve
    doc = {"component_ic.eslesme": {"in": 2216, "out": 2209,
                                    "drops": {"sema:bar_yok:tarih": 7}, "ts": "x"}}
    rep = sieve.report(doc)
    assert [v["rule"] for v in rep["violations"]] == ["sema_elemesi"]


# =================================================================================================
# E) ÖLÇÜMÜN KENDİSİ — kayıt dosyası iddiayı taşıyor mu?
# =================================================================================================
def test_olculen_yedi_satirin_hepsi_TEK_KOK():
    """UYDURMA YASAĞI'nın test tarafı: "7 satır DD" bir tahmin değil kayıtlı bir ölçümdür.
    Ölçüm dosyası (research/olcumler/makulluk_2026-08-07/bulgu.json) iddiayı taşımalı."""
    p = OLCUM / "bulgu.json"
    assert p.exists(), "ölçüm kaydı yok — iddia kanıtsız kalır"
    b = json.loads(p.read_text())
    dusen = b["dusenler"]
    assert b["n_bar_yok_tarih"] == 7 and len(dusen) == 7
    assert {r["ticker"] for r in dusen} == {"DD"}, "kök tek sembol değilmiş — rapor güncellenmeli"
    for r in dusen:
        assert r["ham_barda_var"] is True, "bar ham önbellekte YOK — o zaman sınıf gerçekten sema:"
        assert r["butunluk_kirpmasi_dusurdu"] is True
        assert r["tarih"] < r["guvenli_baslangic"]
