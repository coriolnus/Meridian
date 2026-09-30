"""test_prescreen_kum_havuzu_tek_kaynak_v598.py — TSK-214 tur 2 (2026-09-30): ön-eleme kum havuzu
KÖK kararını sprint'ten TÜRETİR, yedek artıklarını ve okunamayan dosyaları kopyaya SOKMAZ, `meridian.db`yi
SQLite çevrimiçi yedeğiyle TUTARLI kopyalar.

ÖLÇÜLMÜŞ BOŞLUKLAR (Rol-1, A1 salt-okur; ROADMAP TSK-214 kaydı):
  * 2026-09-29: sprint kum havuzuna `meridian.db.20260913T211859Z.bak` (+`-wal`/`-shm`) ve
    `meridian.db.yedek` KOPYALANDI — `SKIP_COPY` yalnız tam `meridian.db*` adlarını tanıyordu. Aynı
    "denylist yeni artefaktı kaçırır" sınıfı ön-elemede de açıktı (o yüzey hiç sormuyordu).
  * 2026-09-28 (Kademe C Karar-3): ön-eleme `meridian.db`yi (+wal/shm) `shutil.copytree` ile kopyalıyor —
    canlı worker yazarken SICAK WAL veritabanının dosya kopyası tutarlı anlık görüntü DEĞİLDİR (ana dosya ile
    `-wal` ayrı anlarda okunur). Bu dosyadaki Y3 çivisinin negatif kontrolü aynı fikstürde ham dosya
    kopyasının WAL'daki satırı KAYBETTİĞİNİ testin içinde gösterir.
  * 2026-09-21 (vaka C00005): okunamayan TEK bir dosya (`[Errno 13]`) kum havuzu kurulumunu bütünüyle
    düşürdü. Sır yedeği sınıfı desenle kapandı (v533); ADI hiçbir desene uymayan root sahipli bir dosya
    aynı arızayı yeniden üretirdi — Y2 o dalı ölçer.

KARAR (Rol-1 NÜANS, brief 2026-09-30): ön-eleme DB'yi kopyalamaya DEVAM EDER (Kademe C'den beri iki öğrenme
defteri orada), ama tutarlı yoldan; `-wal`/`-shm` ayrıca kopyalanmaz. Kök kararı `sprint._atlanir`dır;
BEYANLI sapmalar yalnız iki addır: `bars` (ölçümün girdisi, içerik olarak kopyalanır — `symlinks=False`
davranışı aynen) ve `meridian.db` (tutarlı kopya). Ayrışma çivisi (Y4/Y4b) bu iki adın DIŞINDA sprint ile
ön-elemenin aynı ada aynı kararı verdiğini hem yüklem hem üretim yolu düzeyinde ölçer.

CANLIYA DOKUNMAZ: bütün dosya sistemi işi `tmp_path`/`sandbox_state` ağacındadır; `monkeypatch.undo()` YOK.
Sentetik "sır yedeği" sahte içerikli bir tmp dosyasıdır.
"""
from __future__ import annotations

import ast
import inspect
import os
import pathlib
import re
import shutil
import sqlite3

import pytest

from meridian import config, prescreen, sprint, storage, store

REPO = pathlib.Path(__file__).resolve().parents[1]

# --- A1'de ÖLÇÜLEN adlar (uydurma değil) ----------------------------------------------------------
SIR_VAKASI = "secrets.json.bak-20260915T073825Z-tsk189"          # TSK-208/209/214 vakası
DB_YEDEGI = "meridian.db.20260913T211859Z.bak"                     # 2026-09-29 yan gözlem
DB_YEDEK_YANLARI = (DB_YEDEGI + "-wal", DB_YEDEGI + "-shm")          # aynı gözlem (+shm/wal)
GECE_YEDEGI = "meridian.db.yedek"                                  # meridian-backup.service çıktısı
# v204'ün canlı yetim listesinden (2026-08-06 A1): dağıtım damgalı, tarihli ve `sed` yedekleri
DAGIT_YEDEGI = "goal.yaml.bak-202608021652"
TARIHLI_YEDEK = "earnings.csv.20260803T100416Z.bak"
SED_YEDEGI = "earnings.csv.sedbak"
YEDEK_ADLARI = (DB_YEDEGI, *DB_YEDEK_YANLARI, GECE_YEDEGI, DAGIT_YEDEGI, TARIHLI_YEDEK, SED_YEDEGI)

#: Alt dizinde yedek artığı — sınıf sorusu derinlikten bağımsızdır (sprint alt dizin süzgeciyle AYNI karar).
DERIN_YEDEK = "quarantine/portfolio.json.bak"

#: Meşru girdiler (BEDEL ölçümü): kopyalanmaya DEVAM etmeli.
MESRU = ("portfolio.json", "goal.yaml", "bounds.yaml", "template.json", "quarantine/mesru.json",
         "validation_ledger.jsonl" + storage.MIGRATED_SUFFIX)

NISAN = "v598-nisan-govdesi"


def _yaz(kok: pathlib.Path, rel: str, govde: str) -> None:
    p = kok / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(govde)


def _sicak_wal_db(yol: pathlib.Path) -> sqlite3.Connection:
    """CANLI YAZAN bağlantı taklidi: WAL modu, otomatik checkpoint KAPALI; satır 1 ana dosyada, satır 2
    YALNIZ `-wal`da (bağlantı açık kaldıkça checkpoint edilmez). Çağıran bağlantıyı KAPATIR."""
    w = sqlite3.connect(str(yol), isolation_level=None)
    w.execute("PRAGMA journal_mode=wal")
    w.execute("PRAGMA wal_autocheckpoint=0")
    w.execute("CREATE TABLE defter(x INTEGER)")
    w.execute("INSERT INTO defter VALUES (1)")
    w.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    w.execute("INSERT INTO defter VALUES (2)")
    return w


def _satirlar(db: pathlib.Path) -> list[int]:
    c = sqlite3.connect(str(db))
    try:
        return [r[0] for r in c.execute("SELECT x FROM defter ORDER BY x")]
    finally:
        c.close()


def _canli_taklidi(kok: pathlib.Path) -> pathlib.Path:
    """Sentetik CANLI `state/`: okunamaz sır yedeği + A1'de ölçülen yedek adları + derin yedek + meşru
    defterler. Kopyalanmaz gövdelerde NİŞAN durur: adın atlanması yetmez, gövde hiçbir yoldan girmemeli."""
    live = kok / "live"
    live.mkdir(parents=True)
    for rel in (SIR_VAKASI, *YEDEK_ADLARI, DERIN_YEDEK):
        _yaz(live, rel, '{"nisan":"%s"}' % NISAN)
    for rel in MESRU:
        _yaz(live, rel, '{"mesru":true}')
    # KURULUM ÇİPASI: sınıflandırma tek kaynaktan doğrulanır — türetme bozulursa çivi yanlış sebeple
    # yeşil kalmasın. Yedek adlarının hiçbiri SIR değildir (sınıflar ayrı raporlanır).
    for ad in YEDEK_ADLARI + (pathlib.PurePosixPath(DERIN_YEDEK).name,):
        assert config.yedek_artigi_mi(ad), f"kurulum çipası: `{ad}` yedek artığı SAYILMIYOR"
        assert not config.sir_dosyasi_mi(ad), f"kurulum çipası: `{ad}` sır sayılıyor — sınıflar karıştı"
    (live / SIR_VAKASI).chmod(0o000)
    return live


def _log_satiri(kayit: list[str], anahtar: str) -> str:
    satir = [s for s in kayit if anahtar in s]
    assert len(satir) == 1, f"`{anahtar}` içeren TEK satır beklenir, gelen: {kayit}"
    return satir[0]


# ==================================================================================================
# Y1 — YEDEK ARTIĞI + SIR YEDEĞİ kum havuzuna GİRMEZ, adıyla loglanır; meşru defter VAR
# ==================================================================================================
def test_Y1_yedek_artiklari_kopyalanmaz_ADIYLA_loglanir_mesru_kalir(sandbox_state, tmp_path):
    """BUGÜNKÜ KIRMIZI: A1'de ölçülen yedek adları (`meridian.db.<zaman>.bak` +yan dosyaları,
    `meridian.db.yedek`, dağıtım/`sed` yedekleri) ve ALT DİZİNDEKİ yedek kopyalanıyordu."""
    live = _canli_taklidi(tmp_path)
    kayit: list[str] = []
    hedef = prescreen._sandbox(tmp_path / "work", live, log=kayit.append)

    for rel in (SIR_VAKASI, *YEDEK_ADLARI, DERIN_YEDEK):
        assert not (hedef / rel).exists(), f"`{rel}` kum havuzuna kopyalandı — yedek/sır sınıfı süzülmüyor"
    govdeler = [p.read_bytes() for p in hedef.rglob("*") if p.is_file()]
    assert not any(NISAN.encode() in g for g in govdeler), "kopyalanmaz bir gövde kum havuzunda"
    for rel in MESRU:
        assert (hedef / rel).exists(), f"meşru `{rel}` GİRMEDİ — süzgeç ölçümün girdisini yiyor (bedel)"

    satir = _log_satiri(kayit, "kopyalanmayan")
    for rel in (SIR_VAKASI, *YEDEK_ADLARI, DERIN_YEDEK):
        assert rel in satir, f"`{rel}` log satırında yok — atlanan ADIYLA bildirilmeli: {satir}"


# ==================================================================================================
# Y2 — OKUNAMAYAN dosya/dizin kopyayı DÜŞÜRMEZ, adıyla loglanır
# ==================================================================================================
OKUNAMAZ_DOSYA = "ozel_defter.json"      # adı HİÇBİR desene uymaz — sınıf süzgeci onu göremez
OKUNAMAZ_DIZIN = "kilitli"


def test_Y2_okunamayan_dosya_ve_dizin_kopyayi_dusurmez(sandbox_state, tmp_path, monkeypatch):
    """C00005 arıza SINIFI (Errno 13) — ada bağlı değil. Adı desene uymayan root sahipli bir dosya ya da
    dizin, süzgeçten geçip `shutil.copytree`ı `shutil.Error` ile düşürürdü ve haftanın bileşik kalemi
    ölçülmeden yanardı. Karar: kopya DÜŞMEZ, dosya hedefte YOK, adı loga düşer."""
    live = tmp_path / "live"
    _yaz(live, "portfolio.json", '{"mesru":true}')
    _yaz(live, OKUNAMAZ_DOSYA, '{"nisan":"%s"}' % NISAN)
    _yaz(live, OKUNAMAZ_DIZIN + "/ic.json", '{"nisan":"%s"}' % NISAN)
    for ad in (OKUNAMAZ_DOSYA, OKUNAMAZ_DIZIN):
        assert not sprint._atlanir(ad) and not config.yedek_artigi_mi(ad), (
            f"kurulum çipası: `{ad}` bir desene uyuyor — çivi okunamazlık bacağını ölçmüyor")
    (live / OKUNAMAZ_DOSYA).chmod(0o000)
    (live / OKUNAMAZ_DIZIN).chmod(0o000)
    try:
        if os.geteuid() == 0:
            # ROOT KOŞUMU: chmod 000 root'u durdurmaz; okunamazlık enjekte edilir (çivi susmaz).
            gercek = prescreen._okunabilir
            monkeypatch.setattr(prescreen, "_okunabilir",
                                lambda yol: yol.name not in (OKUNAMAZ_DOSYA, OKUNAMAZ_DIZIN) and gercek(yol))
        else:
            # NEGATİF KONTROL (testin içinde): yalnız sınıf süzgeciyle aynı kopya GERÇEKTEN düşer.
            with pytest.raises(shutil.Error):
                shutil.copytree(live, tmp_path / "suzgecsiz", symlinks=False,
                                ignore=sprint._alt_dizin_suzgeci(live, []))
        kayit: list[str] = []
        hedef = prescreen._sandbox(tmp_path / "work", live, log=kayit.append)

        assert (hedef / "portfolio.json").exists(), "meşru defter düştü"
        assert not (hedef / OKUNAMAZ_DOSYA).exists()
        assert not (hedef / OKUNAMAZ_DIZIN).exists()
        satir = _log_satiri(kayit, "okunamayan")
        for ad in (OKUNAMAZ_DOSYA, OKUNAMAZ_DIZIN):
            assert ad in satir, f"`{ad}` okunamayan satırında yok: {satir}"
        assert not [s for s in kayit if "kopyalanmayan" in s], (
            f"okunamayan dosya SINIF satırına karıştı (sınıflar ayrı raporlanır): {kayit}")
    finally:
        (live / OKUNAMAZ_DIZIN).chmod(0o700)
        (live / OKUNAMAZ_DOSYA).chmod(0o600)


# ==================================================================================================
# Y3 — SICAK WAL DB tutarlı kopyalanır: WAL'daki satır hedefte VAR, yan dosyalar YOK, canlı DEĞİŞMEZ
# ==================================================================================================
def test_Y3_sicak_wal_db_tutarli_kopyalanir(sandbox_state, tmp_path):
    live = tmp_path / "live"
    live.mkdir()
    _yaz(live, "portfolio.json", '{"mesru":true}')
    yazan = _sicak_wal_db(live / storage.DB_NAME)
    try:
        for yan in ("-wal", "-shm"):
            assert (live / (storage.DB_NAME + yan)).exists(), f"kurulum çipası: canlı `{yan}` yok"
        # NEGATİF KONTROL: ham dosya kopyası WAL satırını KAYBEDER — fikstür gerçekten ısırıyor.
        shutil.copy2(live / storage.DB_NAME, tmp_path / "ham.db")
        assert _satirlar(tmp_path / "ham.db") == [1], "kurulum çipası: satır 2 WAL'da değil"
        canli_once = {p.name: (p.stat().st_size, p.stat().st_mtime_ns) for p in live.iterdir()}

        kayit: list[str] = []
        hedef = prescreen._sandbox(tmp_path / "work", live, log=kayit.append)

        canli_sonra = {p.name: (p.stat().st_size, p.stat().st_mtime_ns) for p in live.iterdir()}
        assert canli_sonra == canli_once, "tutarlı kopya CANLI state'te bir dosyayı değiştirdi"
        yanlar = sorted(p.name for p in hedef.iterdir() if p.name.startswith(storage.DB_NAME))
        assert yanlar == [storage.DB_NAME], f"hedefte DB yan dosyası/yedeği var: {yanlar}"
        assert _satirlar(hedef / storage.DB_NAME) == [1, 2], (
            "WAL'da bekleyen satır hedefte YOK — kopya tutarlı anlık görüntü değil")
        c = sqlite3.connect(str(hedef / storage.DB_NAME))
        try:
            assert c.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        finally:
            c.close()
        _log_satiri(kayit, "tutarlı kopya")
    finally:
        yazan.close()


def test_Y3b_tek_kaynak_storage_fonksiyonu_cagrilir_resume_de_cagrilmaz(sandbox_state, tmp_path,
                                                                        monkeypatch):
    """TEK KAYNAK (davranış): tutarlı kopya `storage`dadır, ön-eleme ÇAĞIRIR. `--resume` dalında (hedef
    VAR) kopya hiç koşmaz — önceki koşunun kum havuzu (ve DB'si) yeniden kullanılır."""
    live = tmp_path / "live"
    live.mkdir()
    yazan = _sicak_wal_db(live / storage.DB_NAME)
    try:
        cagri: list[tuple[pathlib.Path, pathlib.Path]] = []
        gercek = storage.tutarli_kopya

        def _sayan(kaynak, hedef):
            cagri.append((pathlib.Path(kaynak), pathlib.Path(hedef)))
            return gercek(kaynak, hedef)

        monkeypatch.setattr(storage, "tutarli_kopya", _sayan)
        wd = tmp_path / "work"
        hedef = prescreen._sandbox(wd, live, log=lambda s: None)
        # Kopya kardeş `.yarim` dizinine yazılır ve kurulum bitince `hedef`e taşınır (Y7, atomik kurulum).
        assert cagri == [(live / storage.DB_NAME, wd / "state.yarim" / storage.DB_NAME)], cagri
        assert (hedef / storage.DB_NAME).is_file() and not (wd / "state.yarim").exists()
        prescreen._sandbox(wd, live, log=lambda s: None)
        assert len(cagri) == 1, "hedef VARKEN tutarlı kopya yeniden koştu — `--resume` sözleşmesi bozuldu"
    finally:
        yazan.close()


def test_Y3c_kaynak_yoksa_yaratmaz_db_siz_kum_havuzu_duser_mez(sandbox_state, tmp_path):
    """Sigorta (`storage.connect` `create=False` emsali): salt-okur URI olmayan yolu YARATMAZ. DB'siz
    canlı kök (dosya kipi) kum havuzunu düşürmez ve hedefte DB doğurmaz."""
    with pytest.raises(sqlite3.OperationalError):
        storage.tutarli_kopya(tmp_path / "yok.db", tmp_path / "hedef.db")
    assert not (tmp_path / "yok.db").exists(), "salt-okur açılış olmayan kaynağı YARATTI"
    live = tmp_path / "live"
    _yaz(live, "portfolio.json", '{"mesru":true}')
    hedef = prescreen._sandbox(tmp_path / "work", live, log=lambda s: None)
    assert not (hedef / storage.DB_NAME).exists()


# ==================================================================================================
# Y4 — AYRIŞMA ÇİVİSİ (yüklem): kök kararı sprint'inkidir; beyanlı sapma YALNIZ iki ad
# ==================================================================================================
BEYANLI_SAPMALAR = {"bars": "kopyalanir", storage.DB_NAME: "tutarli_kopya"}


def _korpus() -> list[str]:
    """Kök ad korpusu: `SKIP_COPY`in TAMAMI + tek-kaynak desenlerden TÜRETİLEN örnekler + ölçülen adlar
    + meşru adlar. Desenler elle değil kaynaktan okunur: aileye yeni üye girdiği gün burası onu görür."""
    turetilen = [d.replace("*", "ab12").replace("?", "x")
                 for d in (config.SIR_DESENLERI + config.GECICI_ARTIK_DESENLERI
                           + config.YEDEK_ARTIK_DESENLERI)]
    return sorted(set(sprint.SKIP_COPY) | set(turetilen)
                  | {SIR_VAKASI, *YEDEK_ADLARI, "portfolio.json", "trades.jsonl", "goal.yaml",
                     "events.jsonl", "template.json", "tmp_notlar.md", "LEARN_HALT",
                     "validation_ledger.jsonl" + storage.MIGRATED_SUFFIX})


def test_Y4_kok_karari_sprint_ile_ayni_beyanli_sapmalar_haric():
    sapmalar = prescreen._sprint_kok_sapmalari()
    assert sapmalar == BEYANLI_SAPMALAR, (
        f"beyanlı sapma kümesi değişti: {sapmalar} — yeni bir sapma kartsız/gerekçesiz doğamaz, "
        f"bir sapmanın kaybı ise (ör. DB atlanırsa) öğrenme defterlerini kum havuzundan düşürür")
    # DOSYA/DİZİN TÜRÜ ELLE YAZILMAZ (tur 2, inceleme Minor 5): `SKIP_COPY` adlarının hangisinin dizin
    # olduğu kaynağın bilgisi değildir ve elle tutulan bir alt küme `SKIP_COPY` büyüdüğünde sessizce
    # bayatlardı. Sprint'in kök kararı TÜRDEN bağımsızdır (dizin de dosya da atlanır), o yüzden tam ad
    # kümesinin HER üyesi İKİ türle de sorulur. Desenden türeyen ve meşru adlar yalnız DOSYA olarak
    # sorulur: desene uyan DİZİNİ ön-eleme bilerek kopyalar (v533 T5, beyanlı fark — `_kok_atlar`).
    kontrol = [(ad, dizin) for ad in sorted(sprint.SKIP_COPY) for dizin in (True, False)]
    kontrol += [(ad, False) for ad in _korpus() if ad not in sprint.SKIP_COPY]
    assert {ad for ad, _ in kontrol} >= set(sprint.SKIP_COPY), "kurulum çipası: tam ad kümesi kapsanmıyor"
    for ad, dizin in kontrol:
        sprint_atlar = sprint._atlanir(ad)
        on_eleme_atlar = prescreen._kok_atlar(ad, dizin=dizin)
        if ad in BEYANLI_SAPMALAR:
            assert sprint_atlar, f"kurulum çipası: sprint `{ad}`ı atlamıyor — sapma beyanı anlamsız"
            hedefte = (not on_eleme_atlar) or sapmalar[ad] == "tutarli_kopya"
            assert hedefte, f"beyanlı sapma `{ad}` (dizin={dizin}) ön-eleme kum havuzunda YOK"
        else:
            assert on_eleme_atlar == sprint_atlar, (
                f"`{ad}` (dizin={dizin}): sprint atlar={sprint_atlar}, ön-eleme atlar={on_eleme_atlar} — "
                f"iki kum havuzu aynı ada farklı karar veriyor (tek-kaynak yasası)")


def test_Y4b_uretim_yolu_iki_kum_havuzu_ayni_adlari_tasir(sandbox_state):
    """Yüklem düzeyi yetmez: iki ÜRETİM yolu (`sprint._kur_kum_havuzu`, `prescreen._sandbox`) AYNI canlı
    köke karşı koşar ve korpustaki her ad için hedefteki VARLIK karşılaştırılır. `bars` iki tarafta da
    vardır (sprint: bağ, ön-eleme: içerik); DB bu fikstürde yoktur (sapması Y3'te ölçülür)."""
    live = config.STATE
    (live / "HALT").write_text("")
    _yaz(live, "bars_intraday/AAA.csv", "d,o\n")
    _yaz(live, "intraday_bars/AAA.json", "{}")
    _yaz(live, "sprint/eski-kum/state/x.json", "{}")
    _yaz(live, "events.jsonl", '{"event":"v598"}\n')
    _yaz(live, "template.json", "{}")
    _yaz(live, "bars/AAA.csv", "d,o\n")
    for rel in (SIR_VAKASI, *YEDEK_ADLARI, DERIN_YEDEK):
        _yaz(live, rel, '{"nisan":"%s"}' % NISAN)
    _yaz(live, "quarantine/mesru.json", "{}")
    (live / SIR_VAKASI).chmod(0o000)
    korpus = ("HALT", "bars", "bars_intraday", "intraday_bars", "sprint", "events.jsonl",
              "template.json", "goal.yaml", "bounds.yaml", "history", "quarantine",
              SIR_VAKASI, *YEDEK_ADLARI, DERIN_YEDEK, "quarantine/mesru.json")

    kayit: list[str] = []
    on_eleme = prescreen._sandbox(live.parent / "prescreen-work", live, log=kayit.append)
    kum = sprint._kur_kum_havuzu("20990101-000598") / "state"

    for rel in korpus:
        assert (kum / rel).exists() == (on_eleme / rel).exists(), (
            f"`{rel}`: sprint kum havuzunda={((kum / rel).exists())}, ön-elemede="
            f"{(on_eleme / rel).exists()} — iki kum havuzu aynı ada farklı karar verdi")
    assert (on_eleme / "bars" / "AAA.csv").exists(), "`bars` içeriği ön-eleme kum havuzunda yok"
    assert not (on_eleme / "bars").is_symlink(), "`bars` bağ olarak kopyalandı — `symlinks=False` bozuldu"

    # RAPOR PARİTESİ: sprint olayının adlarıyla ön-eleme log satırı aynı yedek adlarını taşır.
    olay = [e for e in store.read_jsonl("events.jsonl") if e.get("event") == "sprint_kum_havuzu_atlandi"]
    assert olay, "sprint atlama olayı basılmadı"
    satir = _log_satiri(kayit, "kopyalanmayan")
    for ad in YEDEK_ADLARI:
        assert ad in olay[-1]["adlar"], f"sprint olayı `{ad}` adını taşımıyor: {olay[-1]['adlar']}"
        assert ad in satir, f"ön-eleme log satırı `{ad}` adını taşımıyor: {satir}"
    assert DERIN_YEDEK in olay[-1]["alt_dizin_atlanan"] and DERIN_YEDEK in satir
    konum = _log_satiri(kayit, "sprint kök kümesi")
    for ad in ("HALT", "bars_intraday", "intraday_bars", "sprint"):
        assert ad in konum, f"konum adı `{ad}` log satırında yok: {konum}"


# ==================================================================================================
# Y5 — YEDEK DESENİNİN BEDELİ ve DIŞ KOPYALARLA AYRIŞMASI
# ==================================================================================================
@pytest.mark.parametrize("ad", ["portfolio.json", "trades.jsonl", storage.DB_NAME, "meridian.db-wal",
                                "validation_ledger.jsonl" + storage.MIGRATED_SUFFIX,
                                "hypotheses.jsonl.migrated-20260928T101500Z-p42", "bak.json",
                                "backup_plan.md", "yedekler.json", "yedek.json", "x.bakery",
                                "notlar.bak.md", "template.json"])
def test_Y5_yedek_deseni_mesru_adlari_yakalamaz(ad):
    """BEDEL (bedel yasası): geniş bir yedek deseni kum havuzunu EKSİK doğururdu ve ölçüm sessizce yanlış
    koşardı. Desen iki uca bağlıdır: yedek SONEKİ (`.bak`, `.bak-…`, `.sedbak`, `.yedek`) ada SONDAN
    çapalıdır — `bak`/`yedek` ile BAŞLAYAN ya da içinde geçen meşru adlar eşleşmez."""
    assert not config.yedek_artigi_mi(ad), f"`{ad}` yedek artığı sayılıyor — desen GENİŞ"


def test_Y5c_sir_ailesi_yedek_SAYILMAZ_siniflar_ayrik(monkeypatch):
    """SINIFLAR AYRIK. `secrets.json.bak-<damga>` `*.bak-*`e de uyar; yedek bacağı onu tutarsa sır
    deseninin kaybı kum havuzu çivilerinde maskelenir (v523 çivi 4 bunu 2026-09-30'da gösterdi) ve teşhis
    paketi — yedek bacağını hiç sormayan yüzey — sessizce sızardı. İkinci iddia davranışsaldır: sır deseni
    boşaltılınca o ad sprint'te ARTIK ATLANMAZ (tek taşıyıcı sır desenidir)."""
    assert config.sir_dosyasi_mi(SIR_VAKASI), "kurulum çipası: vaka adı sır sayılmıyor"
    assert any(re.fullmatch(d.replace(".", r"\.").replace("*", ".*"), SIR_VAKASI)
               for d in config.YEDEK_ARTIK_DESENLERI), "kurulum çipası: vaka adı yedek desenine uymuyor"
    assert not config.yedek_artigi_mi(SIR_VAKASI), "sır ailesi yedek artığı da sayılıyor — sınıflar örtüşüyor"
    monkeypatch.setattr(sprint, "SKIP_COPY_PATTERNS", ())
    assert not sprint._atlanir(SIR_VAKASI), (
        "sır deseni boşken vaka adı hâlâ atlanıyor — başka bir bacak onu tutuyor, sır deseninin kaybı maskeli")


def _dagit_artik_desenleri() -> set[str]:
    metin = (REPO / "deploy/ansible/dagit.yml").read_text()
    blok = metin.split("[5a] state/ artık kontrolü", 1)[1].split("file_type:", 1)[0]
    return set(re.findall(r'-\s*"([^"]+)"', blok))


def _yetim_betigi_desenleri() -> set[str]:
    satir = [s for s in (REPO / "ops/state_yetim_temizle.sh").read_text().splitlines()
             if s.startswith("DESEN=")]
    assert len(satir) == 1, "kurulum çipası: `DESEN=` satırı bulunamadı"
    return set(re.findall(r"-name '([^']+)'", satir[0]))


def test_Y5b_dagit_ve_yetim_betigi_desenleri_config_icinde():
    """AYRIŞMA (tek yön, tek-kaynak yasasının istisnası: YAML/kabuk Python sabitini import edemez).
    `state/` içindeki yedek artığı ailesini iki yüzey daha tanır — dağıtım bekçisi ([5a]) ve taşıma
    betiği. Onlara yeni bir sonek girip `config`e girmezse kum havuzu o yedeği kopyalamaya devam ederdi.
    TERS YÖN BİLEREK YOK: `.yedek` (gece yedeğinin tutarlı DB kopyası) `state/`te MEŞRUDUR; bekçi onu
    yetim saymaz, kum havuzu ise ona hiç ihtiyaç duymaz."""
    dagit, betik = _dagit_artik_desenleri(), _yetim_betigi_desenleri()
    assert dagit and betik, "kurulum çipası: desen listesi okunamadı"
    eksik = (dagit | betik) - set(config.YEDEK_ARTIK_DESENLERI)
    assert not eksik, f"`config.YEDEK_ARTIK_DESENLERI` şu yedek soneklerini tanımıyor: {sorted(eksik)}"


# ==================================================================================================
# Y6 — KAYNAK: ön-eleme yedek/sır sınıflandırmasını ve SQLite yedeğini KENDİSİ kurmaz
# ==================================================================================================
def test_Y6_prescreen_kodu_siniflandirma_ve_sqlite_kurmaz():
    """v533 T4b'nin kardeşi: yeni yedek bacağı ve tutarlı kopya da tek kaynaktan GEÇER. Ölçüm çalışan
    koda yapılır (AST); docstring'de adların anılması serbesttir."""
    agac = ast.parse(inspect.getsource(prescreen))
    adlar = {d.attr for d in ast.walk(agac) if isinstance(d, ast.Attribute)} | \
            {d.id for d in ast.walk(agac) if isinstance(d, ast.Name)} | \
            {(d.asname or d.name).split(".")[0] for d in ast.walk(agac) if isinstance(d, ast.alias)}
    for yasak in ("yedek_artigi_mi", "YEDEK_ARTIK_DESENLERI", "sqlite3", "backup"):
        assert yasak not in adlar, f"prescreen KODU `{yasak}` kullanıyor — karar tek kaynaktan geçmiyor"
    for gerekli in ("_atlanir", "SKIP_COPY", "_alt_dizin_suzgeci", "tutarli_kopya"):
        assert gerekli in adlar, f"prescreen tek kaynağı (`{gerekli}`) KODDA çağırmıyor"


# ==================================================================================================
# Y7 — ATOMİK KURULUM: yarım kum havuzu `hedef` olarak DOĞMAZ, `--resume` onu hazır SANMAZ (tur 2)
# ==================================================================================================
def test_Y7_yarida_kalan_kurulum_hedefi_dogurmaz_sonraki_kosum_tam_kurar(sandbox_state, tmp_path,
                                                                          monkeypatch):
    """İNCELEME Minor 1 → Rol-1: IMPORTANT (sessiz ölçüm bozulması). `hedef.exists()` erken dönüşü
    (`--resume`) `copytree`den SONRAKİ bir adım düşerse DB'siz yarım `workdir/state`i hazır sayardı;
    kum havuzunda DB açan kod BOŞ bir veritabanı görür, öğrenme defterleri boş okunur, ölçüm sessizce
    değişir. Sözleşme: kurulum kardeş bir `.yarim` dizininde yapılır ve YALNIZ bütün adımlar bitince
    `hedef`e atomik taşınır. Yarım kalan dizin SİLİNMEZ (kanıt): sonraki koşum onu zaman damgalı bir ada
    KENARA alır ve loglar."""
    live = tmp_path / "live"
    live.mkdir()
    _yaz(live, "portfolio.json", '{"mesru":true}')
    yazan = _sicak_wal_db(live / storage.DB_NAME)
    try:
        gercek = storage.tutarli_kopya
        patla = {"acik": True}

        def _ilk_kosumda_patlar(kaynak, hedef):
            if patla["acik"]:
                raise sqlite3.OperationalError("database is locked (v598 Y7 enjeksiyonu)")
            return gercek(kaynak, hedef)

        monkeypatch.setattr(storage, "tutarli_kopya", _ilk_kosumda_patlar)
        wd = tmp_path / "work"
        hedef = wd / "state"

        with pytest.raises(sqlite3.OperationalError):
            prescreen._sandbox(wd, live, log=lambda s: None)
        assert not hedef.exists(), (
            "tutarlı kopya düştüğü hâlde `hedef` DOĞDU — sonraki `--resume` DB'siz yarım kum havuzunu "
            "hazır sayar ve ölçüm sessizce boş öğrenme defterleriyle koşar")
        yarim = [p.name for p in wd.iterdir()]
        assert yarim == ["state.yarim"], f"yarım kurulum kanıt olarak kalmalı (silinmez): {yarim}"

        patla["acik"] = False
        kayit: list[str] = []
        donen = prescreen._sandbox(wd, live, log=kayit.append)
        assert donen == hedef and hedef.is_dir()
        assert _satirlar(hedef / storage.DB_NAME) == [1, 2], "ikinci koşumun kum havuzunda DB içeriği eksik"
        assert (hedef / "portfolio.json").exists()
        kenar = sorted(p.name for p in wd.iterdir() if p.name != "state")
        assert len(kenar) == 1 and kenar[0].startswith("state.yarim-"), (
            f"önceki yarım kurulum KENARA alınmalıydı (silinmeden, damgalı adla): {kenar}")
        assert not (wd / "state.yarim").exists()
        satir = _log_satiri(kayit, "yarım kurulum")
        assert kenar[0] in satir, f"kenara alma log satırı yeni adı taşımıyor: {satir}"

        # `--resume` sözleşmesi AYNEN: tam kurulmuş hedef yeniden kullanılır, kopya koşmaz.
        patla["acik"] = True
        assert prescreen._sandbox(wd, live, log=lambda s: None) == hedef
    finally:
        yazan.close()
