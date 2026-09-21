"""test_edg089_sayim_araci_v527.py — EDG-2026-089 K1 SAYIM ARACI: TESLİM DEĞİL SONUÇ ölçülür.

ÖLÇÜLEN KUSUR (Rol-1, 2026-09-21, A1 Postgres salt-okur; kartın hüküm metnindeki "ARAÇ KUSURU"
paragrafı). `research/olcumler/edg089_retain_akisi/sayim.py` K1'i "betik `defter_ozeti_retain`
olayında sonuc∈{retain, zaten_var} bastı mı" diye ölçüyordu — yani betiğin TESLİMİNİ (submission).
Kartın `olcum_plani`'si K1'i BAŞKA bir şey diye tanımlıyor: "A1 hindsight DB async_operations
(operation_type retain, status) + memory_units günlük count; hedef 7/7 ∧ artış ≥1/gün". İki sayı
PENCERE İÇİNDE İKİ KEZ ÇELİŞTİ:

  · 2026-09-16 21:30:31Z — `retain` ve `batch_retain` op'ları FAILED (üst-akım sağlayıcı 404,
    "Fact extraction failed: 1/1 chunks failed"); o gün bankaya hiç yeni olgu girmedi. Araç yine de
    günü DOLU saydı ve pencere için `k1_dolu_gun` 7 bastı.
  · 2026-09-18 — op COMPLETED, ama sonuç meta'sı `unit_ids_count` 0 / `facts_committed` 0; banka
    yine BÜYÜMEDİ. Araç bu günü de DOLU saydı.

Kusurun YÖNÜ tek taraflıdır: araç eşiği HAK ETMEDEN GEÇME yönünde yanlıydı. Hüküm karta göre
verildi (K1 başarı 6/7, artış 5/7 → KALDI); araç halef kartta KULLANILMADAN ÖNCE düzeltildi
(2026-09-21).

BU ÇİVİ NE TUTAR (Rol-1 kararı, 2026-09-21). K1 ÜÇ BİLEŞENLİDİR ve üçü de raporda AYRI alandır:
  (a) `k1_teslim`     — betik o gün teslim etti mi (TANI kolonu; TEK BAŞINA gün DOLDURMAZ),
  (b) `k1_op_basari`  — o gün operation_type retain op'u status completed mi,
  (c) `k1_banka_artis`— o gün memory_units yeni satır sayısı ≥1 mi.
`k1_gun_dolu` = (b) ∧ (c). psql erişilemezse (b)/(c)/`k1_gun_dolu` None olur — "bilinmiyor" YEŞİL
SAYILMAZ (uydurma yasağı). Hüküm aracın işi değildir: `hukum` alanı None kalmaya devam eder.

ARAÇ `meridian`ı İTHAL ETMEZ (kendi başlığında beyanlı; A1'de ssh stdin ile salt-okur koşar) — bu
çivi de aracı YOLDAN yükler, `psql` yardımcısını monkeypatch'ler ve GERÇEK Postgres'e HİÇ dokunmaz.
Sahte olay defteri `tmp_path` altındadır; canlı ya da yerel `state/` OKUNMAZ.
"""
from __future__ import annotations

import json
import pathlib

import pytest

from tests.conftest import betikten_modul_yukle

KOK = pathlib.Path(__file__).resolve().parents[1]
BETIK_YOLU = KOK / "research" / "olcumler" / "edg089_retain_akisi" / "sayim.py"

#: Pencerenin ÖLÇÜLMÜŞ günleri. Damgalar GEÇMİŞTE sabittir (pencere 2026-09-13→09-20 kapandı),
#: bu yüzden `gecti_mi_takvim` dalı takvim ilerledikçe kaymaz.
GUN_09_16 = "2026-09-16"   # op FAILED  + banka artışı 0  → İKİ bileşen de düşük
GUN_09_18 = "2026-09-18"   # op COMPLETED + banka artışı 0 → yalnız (c) düşük
GUN_09_17 = "2026-09-17"   # op COMPLETED + banka artışı 10 → normal gün
PENCERE_BAS = "2026-09-13"


# =================================================================================================
# YARDIMCILAR — sahte defter + sahte psql
# =================================================================================================
def _sayim():
    return betikten_modul_yukle(BETIK_YOLU, "edg089_sayim")


def _olay(gun: str, *, sonuc: str = "retain", items: int = 1, saat: str = "21:30:20") -> dict:
    """`ops/defter_ozeti_retain.py`nin yazdığı olay satırının şekli (alanlar oradan okundu)."""
    return {"ts": f"{gun}T{saat}+00:00", "event": "defter_ozeti_retain", "level": "info",
            "gun": gun, "document_id": f"meridian-gunluk-ozet-{gun}", "sonuc": sonuc,
            "items": items, "karakter": 1516, "operation_id": "10d5d219"}


def _defter(tmp_path: pathlib.Path, satirlar: list[dict]) -> pathlib.Path:
    yol = tmp_path / "events.jsonl"
    yol.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in satirlar),
                   encoding="utf-8")
    return yol


def _sahte_psql(*, retain=None, tazeleme=None, banka_gunluk=None, banka_toplam=None,
                kayit: list[str] | None = None):
    """`psql` yardımcısının yerine geçer: SORGUYA GÖRE dağıtır, hiçbir süreç başlatmaz.

    Dağıtım anahtarları SÖZLEŞMEdir ve aşağıdaki `test_SOZLESME_*` çivileri onları ayrıca ölçer:
    anahtar aracın sorgusundan kaybolursa bu sahte `AssertionError` atar (sessiz None DEĞİL) —
    yoksa araç sorguyu değiştirdiğinde çivi "yeşil" kalırdı.
    """
    def _f(sql: str):
        if kayit is not None:
            kayit.append(sql)
        d = " ".join(sql.split())
        if "operation_type='refresh_mental_model'" in d:
            return tazeleme
        if "operation_type='retain'" in d:
            return retain
        if "from memory_units" in d and "group by" in d:
            return banka_gunluk
        if "from memory_units" in d:
            return banka_toplam
        raise AssertionError(f"sahte psql tanımadığı sorguyu aldı: {sql!r}")
    return _f


def _kos(monkeypatch, capsys, tmp_path, *, olaylar, psql_f, baslangic=PENCERE_BAS, gun_n=7):
    mod = _sayim()
    monkeypatch.setattr(mod, "psql", psql_f)
    yol = _defter(tmp_path, olaylar)
    rc = mod.main(["--events", str(yol), "--baslangic", baslangic, "--gun-n", str(gun_n)])
    ham = capsys.readouterr().out
    return json.loads(ham), rc


def _satir(cikti: dict, gun: str) -> dict:
    (t,) = [x for x in cikti["tablo"] if x["gun"] == gun]
    return t


# =================================================================================================
# 1 — 09-16: TESLİM VAR, OP DÜŞTÜ, BANKA BÜYÜMEDİ  →  GÜN DOLU DEĞİL
# =================================================================================================
def test_09_16_teslim_VAR_ama_op_DUSTU_ve_banka_artisi_0_gun_DOLU_DEGIL(
        monkeypatch, capsys, tmp_path):
    """Kartın 09-16 vakası birebir. Araç bu günü DOLU sayıyordu — düzeltmenin ilk kırmızısı."""
    cikti, _ = _kos(monkeypatch, capsys, tmp_path,
                    olaylar=[_olay(GUN_09_16)],
                    psql_f=_sahte_psql(retain=[f"{GUN_09_16}|failed|1"],
                                       tazeleme=[f"{GUN_09_16}|completed|7"],
                                       banka_gunluk=[],
                                       banka_toplam=["17259"]),
                    baslangic=GUN_09_16, gun_n=1)
    t = _satir(cikti, GUN_09_16)
    assert t["k1_teslim"] is True, "betik teslim etti — TANI kolonu bunu göstermeli"
    assert t["k1_op_basari"] is False, "retain op'u FAILED: başarı kolonu False olmalı"
    assert t["k1_banka_artis"] is False, "o gün bankaya yeni olgu girmedi"
    assert t["k1_banka_yeni"] == 0
    assert t["k1_gun_dolu"] is False, "TESLİM tek başına günü DOLDURMAZ (kartın K1 tanımı)"
    assert cikti["k1_dolu_gun"] == 0
    assert cikti["k1_teslim_gun"] == 1, "teslim sayısı ayrı alanda KORUNUR (tanı)"


# =================================================================================================
# 1b — YALNIZ (b) DÜŞÜK: op FAILED ama banka o gün BÜYÜDÜ  →  yine DOLU DEĞİL
# =================================================================================================
def test_op_DUSTU_ama_banka_BUYUMUS_gun_DOLU_DEGIL_b_bileseni_IZOLE(
        monkeypatch, capsys, tmp_path):
    """(b) bileşenini YALNIZ BAŞINA ısırtır: (c) doğruyken bile düşük (b) günü düşürmeli.

    Bu ayrık senaryo olmadan `k1_gun_dolu`dan (b)'yi silen bir mutasyon 09-16 vakasında yeşil
    kalırdı (orada (c) de düşüktü) — çivi kendi hedefini ıskalardı.
    """
    cikti, _ = _kos(monkeypatch, capsys, tmp_path,
                    olaylar=[_olay(GUN_09_16)],
                    psql_f=_sahte_psql(retain=[f"{GUN_09_16}|failed|1"],
                                       tazeleme=[],
                                       banka_gunluk=[f"{GUN_09_16}|4"],
                                       banka_toplam=["17259"]),
                    baslangic=GUN_09_16, gun_n=1)
    t = _satir(cikti, GUN_09_16)
    assert t["k1_op_basari"] is False
    assert t["k1_banka_artis"] is True and t["k1_banka_yeni"] == 4
    assert t["k1_gun_dolu"] is False
    assert cikti["k1_dolu_gun"] == 0


# =================================================================================================
# 2 — 09-18: OP COMPLETED ama BANKA BÜYÜMEDİ  →  GÜN DOLU DEĞİL  ((c) İZOLE)
# =================================================================================================
def test_09_18_op_BASARILI_ama_banka_artisi_0_gun_DOLU_DEGIL(monkeypatch, capsys, tmp_path):
    """Kartın 09-18 vakası: op başarılı, sonuç meta'sında hiç olgu yok → banka büyümedi."""
    cikti, _ = _kos(monkeypatch, capsys, tmp_path,
                    olaylar=[_olay(GUN_09_18)],
                    psql_f=_sahte_psql(retain=[f"{GUN_09_18}|completed|1"],
                                       tazeleme=[f"{GUN_09_18}|completed|0"],
                                       banka_gunluk=[],
                                       banka_toplam=["17316"]),
                    baslangic=GUN_09_18, gun_n=1)
    t = _satir(cikti, GUN_09_18)
    assert t["k1_teslim"] is True
    assert t["k1_op_basari"] is True
    assert t["k1_banka_artis"] is False and t["k1_banka_yeni"] == 0
    assert t["k1_gun_dolu"] is False, "başarı TEK BAŞINA yetmez — banka ARTMALI (kartın K1 tanımı)"
    assert cikti["k1_dolu_gun"] == 0


# =================================================================================================
# 3 — NORMAL GÜN: teslim + completed + artış  →  DOLU
# =================================================================================================
def test_normal_gun_teslim_BASARILI_op_ve_artis_VAR_gun_DOLU(monkeypatch, capsys, tmp_path):
    cikti, _ = _kos(monkeypatch, capsys, tmp_path,
                    olaylar=[_olay(GUN_09_17)],
                    psql_f=_sahte_psql(retain=[f"{GUN_09_17}|completed|1"],
                                       tazeleme=[f"{GUN_09_17}|completed|11"],
                                       banka_gunluk=[f"{GUN_09_17}|10"],
                                       banka_toplam=["17290"]),
                    baslangic=GUN_09_17, gun_n=1)
    t = _satir(cikti, GUN_09_17)
    assert (t["k1_teslim"], t["k1_op_basari"], t["k1_banka_artis"]) == (True, True, True)
    assert t["k1_banka_yeni"] == 10
    assert t["k1_gun_dolu"] is True
    assert cikti["k1_dolu_gun"] == 1
    assert cikti["k1_op_basari_gun"] == 1 and cikti["k1_banka_artis_gun"] == 1


# =================================================================================================
# 3b — TESLİM YOK ama OP + ARTIŞ VAR: gün DOLU, teslim kolonu False (tanı ayrık kalır)
# =================================================================================================
def test_teslim_YOK_ama_op_ve_artis_VAR_gun_DOLU_teslim_kolonu_AYRIK(
        monkeypatch, capsys, tmp_path):
    """K1'in ÖLÇÜSÜ sonuçtur: betik olayı yazmamış olsa bile banka büyüdüyse gün DOLUDUR.

    Teslim kolonu bunu gizlemez, `k1_teslim` False kalır — tanı sinyali KAYBOLMAZ (bedel yasası).
    """
    cikti, _ = _kos(monkeypatch, capsys, tmp_path,
                    olaylar=[],
                    psql_f=_sahte_psql(retain=[f"{GUN_09_17}|completed|1"],
                                       tazeleme=[],
                                       banka_gunluk=[f"{GUN_09_17}|3"],
                                       banka_toplam=["17290"]),
                    baslangic=GUN_09_17, gun_n=1)
    t = _satir(cikti, GUN_09_17)
    assert t["k1_teslim"] is False and t["k1_retain_olay_n"] == 0
    assert t["k1_gun_dolu"] is True
    assert cikti["k1_teslim_gun"] == 0 and cikti["k1_dolu_gun"] == 1


# =================================================================================================
# 4 — psql ERİŞİLEMEZ: (b)/(c)/`k1_gun_dolu` None, araç DÜŞMEZ
# =================================================================================================
def test_psql_ERISILEMEZ_bilesenler_NONE_ve_gun_dolu_NONE_arac_DUSMEZ(
        monkeypatch, capsys, tmp_path):
    """Uydurma yasağı: ölçülemeyen değer None + neden. "Bilinmiyor" YEŞİL sayılmaz."""
    cikti, rc = _kos(monkeypatch, capsys, tmp_path,
                     olaylar=[_olay(GUN_09_17)],
                     psql_f=_sahte_psql(retain=None, tazeleme=None,
                                        banka_gunluk=None, banka_toplam=None),
                     baslangic=GUN_09_17, gun_n=1)
    t = _satir(cikti, GUN_09_17)
    assert t["k1_teslim"] is True, "olay defteri okunabiliyor — teslim kolonu ÖLÇÜLÜR"
    assert t["k1_op"] is None and t["k1_op_basari"] is None
    assert t["k1_banka_yeni"] is None and t["k1_banka_artis"] is None
    assert t["k1_gun_dolu"] is None, "bilinmeyen gün DOLU da DEĞİL, DOLU DEĞİL de değildir"
    assert cikti["k1_dolu_gun"] is None
    assert isinstance(cikti["k1_neden"], str) and cikti["k1_neden"].strip()
    # Mevcut desen KORUNUR (K2 ve toplam memory_units).
    assert cikti["k2_dolu_gun"] is None and isinstance(cikti["k2_neden"], str)
    assert cikti["memory_units"] is None and isinstance(cikti["memory_units_neden"], str)
    assert rc is None, "araç None döner (çıkış 0) — psql yokluğu ARIZA DEĞİL ölçülemezliktir"


def test_psql_YALNIZ_banka_sorgusu_dususe_gun_dolu_NONE_op_kolonu_OLCULU(
        monkeypatch, capsys, tmp_path):
    """İki kaynak AYRI ayrı düşebilir: biri ölçülüp öbürü ölçülemezse gün YİNE bilinmez."""
    cikti, _ = _kos(monkeypatch, capsys, tmp_path,
                    olaylar=[_olay(GUN_09_17)],
                    psql_f=_sahte_psql(retain=[f"{GUN_09_17}|completed|1"],
                                       tazeleme=[f"{GUN_09_17}|completed|11"],
                                       banka_gunluk=None, banka_toplam=None),
                    baslangic=GUN_09_17, gun_n=1)
    t = _satir(cikti, GUN_09_17)
    assert t["k1_op_basari"] is True
    assert t["k1_banka_artis"] is None
    assert t["k1_gun_dolu"] is None
    assert cikti["k1_dolu_gun"] is None and cikti["k1_op_basari_gun"] == 1


# =================================================================================================
# 5 — K2 REGRESYONU: `refresh_mental_model` sayımı DEĞİŞMEDİ
# =================================================================================================
#: Kartın hüküm metnindeki ÖLÇÜLMÜŞ K2 dağılımı (pencere günleri): 09-18 ve 09-20 sıfır.
K2_OLCULEN = {"2026-09-13": 11, "2026-09-14": 11, "2026-09-15": 11,
              "2026-09-16": 7, "2026-09-17": 11, "2026-09-18": 0,
              "2026-09-19": 11}


def test_K2_refresh_mental_model_sayimi_DEGISMEDI(monkeypatch, capsys, tmp_path):
    """K1 düzeltmesi K2 koluna DOKUNMAMALI: aynı girdi → kartta yazan aynı 6/7."""
    tazeleme = [f"{g}|completed|{n}" for g, n in sorted(K2_OLCULEN.items()) if n]
    cikti, _ = _kos(monkeypatch, capsys, tmp_path,
                    olaylar=[_olay(g) for g in sorted(K2_OLCULEN)],
                    psql_f=_sahte_psql(retain=[], tazeleme=tazeleme,
                                       banka_gunluk=[], banka_toplam=["17329"]))
    assert cikti["k2_dolu_gun"] == 6, "kartın ölçtüğü 6/7 (09-13…09-19) AYNEN çıkmalı"
    assert cikti["k2_neden"] is None
    for g, n in K2_OLCULEN.items():
        t = _satir(cikti, g)
        # MEVCUT davranış AYNEN: K2 kolonu hiç satır görmeyen günü `None` bırakır (boş sözlük
        # DEĞİL). K1'in yeni `k1_op` alanı bilerek FARKLI davranır (`{}` = ölçüldü, satır yok;
        # `None` = psql erişilemedi) — ama K2'ye DOKUNULMADI; bu çivi o sınırı yerinde tutar.
        assert t["k2_tazeleme"] == ({"completed": n} if n else None)
        assert t["k2_gun_dolu"] is (n >= 1)


def test_K2_failed_op_gunu_DOLDURMAZ_mevcut_davranis(monkeypatch, capsys, tmp_path):
    """K2'nin `completed` şartı da KORUNUR — düzeltme K1'e ait, K2 gevşemedi."""
    cikti, _ = _kos(monkeypatch, capsys, tmp_path,
                    olaylar=[],
                    psql_f=_sahte_psql(retain=[], tazeleme=[f"{GUN_09_17}|failed|3"],
                                       banka_gunluk=[], banka_toplam=["1"]),
                    baslangic=GUN_09_17, gun_n=1)
    t = _satir(cikti, GUN_09_17)
    assert t["k2_tazeleme"] == {"failed": 3}
    assert t["k2_gun_dolu"] is False
    assert cikti["k2_dolu_gun"] == 0


# =================================================================================================
# 6 — ESKİ ALANLAR AYNEN (dosya okuyucusu Rol-1 ve günlük; alan SİLİNMEZ, EKLENİR)
# =================================================================================================
ESKI_UST_ALANLAR = ("kart", "uretim_utc", "pencere", "tablo", "k1_dolu_gun", "k1_gecen_gun",
                    "k2_dolu_gun", "k2_neden", "memory_units", "memory_units_neden",
                    "events_bozuk_satir", "hukum", "hukum_notu")
ESKI_TABLO_ALANLARI = ("gun", "gecti_mi_takvim", "k1_retain_olay_n", "k1_sonuclar",
                       "k1_gun_dolu", "k2_tazeleme", "k2_gun_dolu")


def test_ESKI_alanlarin_HEPSI_duruyor_ve_yenileri_EKLENDI(monkeypatch, capsys, tmp_path):
    cikti, _ = _kos(monkeypatch, capsys, tmp_path,
                    olaylar=[_olay(GUN_09_17, sonuc="zaten_var", items=0)],
                    psql_f=_sahte_psql(retain=[f"{GUN_09_17}|completed|1"],
                                       tazeleme=[f"{GUN_09_17}|completed|11"],
                                       banka_gunluk=[f"{GUN_09_17}|10"],
                                       banka_toplam=["17290"]),
                    baslangic=GUN_09_17, gun_n=1)
    for ad in ESKI_UST_ALANLAR:
        assert ad in cikti, f"eski üst alan SİLİNMİŞ: {ad}"
    t = _satir(cikti, GUN_09_17)
    for ad in ESKI_TABLO_ALANLARI:
        assert ad in t, f"eski tablo alanı SİLİNMİŞ: {ad}"
    assert t["k1_sonuclar"] == ["zaten_var"] and t["k1_retain_olay_n"] == 1
    assert t["k1_teslim"] is True, "`zaten_var` da TESLİMdir (mevcut sözlük korunur)"
    assert cikti["kart"] == "EDG-2026-089"
    assert cikti["memory_units"] == 17290, "TOPLAM memory_units alanı KALIR (Rol-1 kararı 2)"
    for ad in ("k1_teslim_gun", "k1_op_basari_gun", "k1_banka_artis_gun", "k1_neden"):
        assert ad in cikti, f"yeni üst alan YOK: {ad}"
    for ad in ("k1_teslim", "k1_op", "k1_op_basari", "k1_banka_yeni", "k1_banka_artis"):
        assert ad in t, f"yeni tablo alanı YOK: {ad}"


def test_HUKUM_alani_None_KALIR_arac_hukum_vermez(monkeypatch, capsys, tmp_path):
    """Hüküm Rol-1'indir (kart dosyası + K defteri) — araç SAYAR, hüküm VERMEZ."""
    cikti, _ = _kos(monkeypatch, capsys, tmp_path,
                    olaylar=[_olay(GUN_09_17)],
                    psql_f=_sahte_psql(retain=[f"{GUN_09_17}|completed|1"], tazeleme=[],
                                       banka_gunluk=[f"{GUN_09_17}|3"], banka_toplam=["1"]),
                    baslangic=GUN_09_17, gun_n=1)
    assert cikti["hukum"] is None and isinstance(cikti["hukum_notu"], str)


def test_GELECEK_gun_hicbir_K1_bileseni_uretmez(monkeypatch, capsys, tmp_path):
    """Takvimde GELMEMİŞ gün ölçülmez: bileşenler None, `k1_gecen_gun` onu saymaz."""
    import datetime as dt
    yarin = (dt.datetime.now(dt.timezone.utc).date() + dt.timedelta(days=1)).isoformat()
    cikti, _ = _kos(monkeypatch, capsys, tmp_path,
                    olaylar=[],
                    psql_f=_sahte_psql(retain=[], tazeleme=[],
                                       banka_gunluk=[], banka_toplam=["1"]),
                    baslangic=yarin, gun_n=1)
    t = _satir(cikti, yarin)
    assert t["gecti_mi_takvim"] is False
    assert (t["k1_teslim"], t["k1_op_basari"], t["k1_banka_artis"], t["k1_gun_dolu"]) == \
        (None, None, None, None)
    assert cikti["k1_gecen_gun"] == 0 and cikti["k1_dolu_gun"] == 0


# =================================================================================================
# SÖZLEŞME — sorgular kartın ADLANDIRDIĞI kaynaklara gider
# =================================================================================================
def test_SOZLESME_sorgular_async_operations_ve_memory_units_kaynaklarina_gider(
        monkeypatch, capsys, tmp_path):
    """Kartın `olcum_plani` K1 satırı iki kaynak adlandırır; sorgular ONLARA gitmeli.

    Sahte psql dağıtımı bu anahtarlara dayanır — anahtar kayarsa sahte `AssertionError` atar,
    yani bu çivi dağıtıcının KÖR kalmasını da engeller.
    """
    kayit: list[str] = []
    _kos(monkeypatch, capsys, tmp_path, olaylar=[],
         psql_f=_sahte_psql(retain=[], tazeleme=[], banka_gunluk=[], banka_toplam=["1"],
                            kayit=kayit),
         baslangic=GUN_09_17, gun_n=1)
    tek = [" ".join(s.split()) for s in kayit]
    retain_sorgu = [s for s in tek if "operation_type='retain'" in s]
    gunluk_sorgu = [s for s in tek if "from memory_units" in s and "group by" in s]
    toplam_sorgu = [s for s in tek if "from memory_units" in s and "group by" not in s]
    assert len(retain_sorgu) == 1, f"retain op sorgusu TEK olmalı: {tek}"
    assert "from async_operations" in retain_sorgu[0]
    assert "status" in retain_sorgu[0], "status kolonu (b) bileşeninin ta kendisidir"
    assert len(gunluk_sorgu) == 1, "memory_units GÜNLÜK sayımı (Rol-1 kararı 2) TEK sorgu"
    assert "at time zone 'UTC'" in gunluk_sorgu[0], "günlük kova UTC gününe göre (ölçülen şema)"
    assert len(toplam_sorgu) == 1, "TOPLAM memory_units alanı KALIR"


def test_SOZLESME_arac_meridian_ITHAL_ETMEZ(monkeypatch, capsys, tmp_path):
    """Araç A1'de ssh stdin ile koşar ve `obs`a ulaşmaz — ithal listesi bunu KORUMALI."""
    import ast
    agac = ast.parse(BETIK_YOLU.read_text(encoding="utf-8"))
    adlar: list[str] = []
    for d in ast.walk(agac):
        if isinstance(d, ast.Import):
            adlar += [a.name for a in d.names]
        elif isinstance(d, ast.ImportFrom):
            adlar.append(d.module or "")
    kirli = [a for a in adlar if a == "meridian" or a.startswith("meridian.")]
    assert not kirli, f"araç meridian ithal ediyor (obs'a ulaşır): {kirli}"


def test_SOZLESME_psql_yardimcisi_SUDO_POSTGRES_cagrisini_KORUR():
    """`psql` yardımcısının çağrı biçimi A1 reçetesidir; bu çivi onu yerinde tutar.

    (Çağrı ÇALIŞTIRILMAZ — kaynak metni okunur; bu makinede sudo/psql tetiklenmez.)
    """
    kaynak = BETIK_YOLU.read_text(encoding="utf-8")
    assert '"sudo", "-u", "postgres", "psql"' in kaynak
    assert '"-d", "hindsight"' in kaynak and '"-At"' in kaynak


@pytest.mark.parametrize("durumlar,beklenen", [
    (["completed|1"], True),
    (["failed|1"], False),
    (["failed|2", "completed|1"], True),     # aynı gün düşüp yeniden denenmiş → başarı VAR
    ([], False),                              # o gün hiç op yok → başarı YOK
])
def test_op_basari_status_dagilimindan_OKUNUR(monkeypatch, capsys, tmp_path,
                                              durumlar, beklenen):
    cikti, _ = _kos(monkeypatch, capsys, tmp_path, olaylar=[],
                    psql_f=_sahte_psql(retain=[f"{GUN_09_17}|{d}" for d in durumlar],
                                       tazeleme=[], banka_gunluk=[], banka_toplam=["1"]),
                    baslangic=GUN_09_17, gun_n=1)
    t = _satir(cikti, GUN_09_17)
    assert t["k1_op_basari"] is beklenen
    assert t["k1_op"] == {d.split("|")[0]: int(d.split("|")[1]) for d in durumlar}
