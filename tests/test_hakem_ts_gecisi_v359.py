"""EXE-2026-009 · P-2 UYGULAMASI — HAKEMİN BÖLME ANAHTARI `pencere` DAMGASINDAN `ts`YE GEÇTİ.

Sözleşme (bu çivilerin OTORİTESİ, kod değil):
  · research/cards/EXE-2026-009-pencere-kaydirma.yaml → `p2_kapanis_2026_09_01`
  · research/cards/EDG-2026-042-gercek-friksiyon-tahmini.yaml → `p3_karar_ayrik_ts_2026_08_31`
    (kol adlarının TEK SÖZLÜĞÜ + sınır + "ts okunamazsa hiçbir kola atanmaz" kuralı)

Hedef: research/olcumler/edg042_hakem_2026-09-01/{pencere_altbant.py, pencere_cek.py}.
edg042_kosum_2026-08-22/ TARİHÇEDİR ve bu turda TEK BAYT değişmedi — oradaki hakem (`pencere`
damgasıyla bölen) `tests/test_pencere_kaydirma_v272.py` §6 ile çivili kalır; iki dosya iki AYRI
şeyi ölçer, biri diğerinin regresyonu değildir.

NEDEN BU ÇİVİ SETİ (ölçülmüş kusur sınıfı, kart `p2_kapanis` NEDEN bloğu): `pencere="1330"`
damgalı satır bir daha ÜRETİLMEYECEK — damga anahtarıyla kontrol kolu sonsuza dek n=2'de kalır
ve öneri tetiği İNŞAEN erişilemez olur. Çivilerin koruduğu şey bir sayı değil, tetiğin
ERİŞİLEBİLİR kalmasıdır.

ÇİVİLER: (a) tarihli taban kol sayıları · (b) `ts` okunamayan satır kola GİRMEZ · (c) damga↔ts
ayrışma sütunu · (d) İTHAL — bölücünün ikinci kopyası YOK · (e) öneri tetiği eşiği değişmedi ·
(f) çekim alan listesi = eski liste + `ts` (başka alan yok).
"""
import ast
from pathlib import Path

import pytest

from tests.conftest import betikten_modul_yukle

REPO = Path(__file__).resolve().parents[1]
OLCUM = REPO / "research" / "olcumler"
HAKEM_DIZIN = OLCUM / "edg042_hakem_2026-09-01"
HAKEM = HAKEM_DIZIN / "pencere_altbant.py"
CEK = HAKEM_DIZIN / "pencere_cek.py"
RECETE = OLCUM / "edg042_recete_ayrik_2026-08-31" / "olcum.py"
DONUK_HAKEM = OLCUM / "edg042_kosum_2026-08-22" / "pencere_altbant.py"      # SALT-OKUNUR tarihçe
DONUK_CEK = OLCUM / "edg042_kosum_2026-08-22" / "pencere_cek.py"            # SALT-OKUNUR tarihçe

_YOK = object()          # "alan HİÇ YOK" ile "alan None" ayrımı: ikisi de sınanır


def _hakem():
    return betikten_modul_yukle(HAKEM, "pencere_altbant_ts_test")


def _recete():
    return betikten_modul_yukle(RECETE, "edg042_recete_ayrik_test")


def _sabit(yol: Path, ad: str):
    """Modül sabitini KOŞMADAN oku (ast). Donuk betiği içe aktarmak onu ÇALIŞTIRIRDI —
    `pencere_cek.py` içe aktarıldığında `meridian.store`a uzanır ve stdout'a JSON basardı."""
    for d in ast.walk(ast.parse(yol.read_text(encoding="utf-8"))):
        if not isinstance(d, ast.Assign):
            continue
        for hedef in d.targets:
            if isinstance(hedef, ast.Name) and hedef.id == ad:
                return ast.literal_eval(d.value)
            if isinstance(hedef, ast.Tuple):                  # `B, SEED = 5000, 20260812`
                for i, el in enumerate(hedef.elts):
                    if isinstance(el, ast.Name) and el.id == ad:
                        return ast.literal_eval(d.value.elts[i])
    raise AssertionError(f"{ad} sabiti bulunamadı: {yol}")


def _satir(ticker, tarih, bps, ts=_YOK, pencere=_YOK):
    """K1 filtresinden GEÇEN bir E2 satırı (motor=ayna ∧ karar=submitted ∧ fill dolu)."""
    r = {"ticker": ticker, "date": tarih, "plan_id": f"P-{ticker}-{tarih}", "motor": "ayna",
         "karar": "submitted", "fill": 100.0, "fill_vs_resmi_acilis_bps": bps}
    if ts is not _YOK:
        r["ts"] = ts
    if pencere is not _YOK:
        r["pencere"] = pencere
    return r


# ── TARİHLİ TABAN SENTETİĞİ (kart `p2_kapanis` + EDG-042 `p3_karar` sayımı) ────────────────────
# 13 damgasız (kaydırma ÖNCESİ, `pencere` alanı defterde HİÇ yok) + P-1 düzeltmeli dörtlü.
# Dörtlünün `ts`leri kartta ÖLÇÜLMÜŞ değerlerdir (canlı defter salt-okuma, 2026-08-31).
_DAMGASIZ_GUNLER = ["2026-08-05", "2026-08-06", "2026-08-07", "2026-08-08", "2026-08-11",
                    "2026-08-12", "2026-08-13", "2026-08-13", "2026-08-14", "2026-08-14",
                    "2026-08-18", "2026-08-19", "2026-08-19"]


def _tarihli_taban():
    satirlar = [_satir(f"E{i}", g, 10.0 + i, ts=f"{g}T20:30:0{i % 10}+00:00")
                for i, g in enumerate(_DAMGASIZ_GUNLER)]
    satirlar += [
        _satir("DE", "2026-08-21", 80.699, ts="2026-08-21T20:32:22Z", pencere="1330"),
        _satir("PANW", "2026-08-21", 87.148, ts="2026-08-21T20:32:22Z", pencere="1330"),
        _satir("ECL", "2026-08-25", 175.107, ts="2026-08-26T13:45:01Z", pencere="1345"),
        _satir("CRM", "2026-08-27", 245.034, ts="2026-08-28T13:45:00Z", pencere="1345"),
    ]
    return satirlar


def _kol(bps_liste, *, once: bool, gun0=1):
    """n satırlık kol; her satır AYRI seans (kümeli bootstrap'a gerçekçi girdi)."""
    ay, saat = ("07", "20:30:00+00:00") if once else ("09", "13:45:00+00:00")
    return [_satir(f"{'O' if once else 'Y'}{i}", f"2026-{ay}-{gun0 + i:02d}", b,
                   ts=f"2026-{ay}-{gun0 + i:02d}T{saat}")
            for i, b in enumerate(bps_liste)]


# ══ (a) TARİHLİ TABAN — `ts` anahtarıyla kol sayıları 15 / 2 ══════════════════════════════════
def test_a_tarihli_taban_kol_sayilari_15_ve_2():
    rapor = _hakem().altbant_raporu(_tarihli_taban())
    assert rapor["kollar"]["giris_once"]["n"] == 15          # 13 damgasız + DE + PANW
    assert rapor["kollar"]["giris_1345"]["n"] == 2           # ECL + CRM
    assert rapor["olculemedi"]["n"] == 0


def test_a_damgasiz_satirlar_ARTIK_kola_girer_ve_sayilir():
    """P-2'nin çekirdeği: damgasız 13 satır ts ile ölçülerek kola girer (kill#3 İHLAL DEĞİL —
    etiket YAZILMIYOR, defterde kayıtlı iki olgu kıyaslanıyor; kart p2_kapanis)."""
    rapor = _hakem().altbant_raporu(_tarihli_taban())
    assert rapor["damga_ts_caprazi"]["damgasiz"] == 13
    assert rapor["kollar"]["giris_once"]["n"] - 13 == 2      # damgasızlar KOLDA, dışarıda değil


def test_a_kontrol_kolu_esigi_gecmis_tedavi_kolu_bekliyor():
    """Tetik artık İNŞAEN erişilemez DEĞİL: kontrol kolu (n=15) eşiği geçti, bekleyen tedavi
    kolu (n=2). Damga anahtarında bu ilişki TERSİNE dönüktü — kontrol kolu sonsuza dek n=2."""
    rapor = _hakem().altbant_raporu(_tarihli_taban())
    assert rapor["kollar"]["giris_once"]["ci"] is not None
    assert rapor["kollar"]["giris_1345"]["ci"] is None
    assert rapor["oneri_tetigi"]["sonuc"] == "orneklem_birikimde"


# ══ (b) `ts` OKUNAMAYAN SATIR HİÇBİR KOLA GİRMEZ ══════════════════════════════════════════════
@pytest.mark.parametrize("ts,etiket", [
    (_YOK, "alan yok"), (None, "None"), ("", "boş"), ("   ", "boşluk"),
    ("dun aksam", "biçimsiz"), ("2026-08-20T10:00:00", "saat dilimsiz"),
])
def test_b_ts_okunamayan_satir_kola_girmez_nedenle_olculemedi(ts, etiket):
    rapor = _hakem().altbant_raporu([_satir("X", "2026-08-20", 42.0, ts=ts)])
    assert rapor["kollar"]["giris_once"]["n"] == 0, f"{etiket}: kola SIZDI"
    assert rapor["kollar"]["giris_1345"]["n"] == 0, f"{etiket}: kola SIZDI"
    assert rapor["olculemedi"]["n"] == 1
    neden = rapor["olculemedi"]["satirlar"][0]["neden"]
    assert "ts" in neden and "kol" in neden.lower()          # nedensiz kova YASAK


def test_b_olculemedi_bps_bos_nedeni_042_kill_ile_ayri_kalir():
    """İki AYRI olculemedi nedeni birbirine karışmaz: bps boş (042 kill#1/#2) ≠ ts okunamadı."""
    rapor = _hakem().altbant_raporu(
        [_satir("A", "2026-08-20", None, ts="2026-08-20T20:30:00+00:00"),
         _satir("B", "2026-08-20", 5.0, ts="")])
    nedenler = [s["neden"] for s in rapor["olculemedi"]["satirlar"]]
    assert rapor["olculemedi"]["n"] == 2
    assert sum("fill_vs_resmi_acilis_bps" in n for n in nedenler) == 1
    assert sum("`ts`" in n for n in nedenler) == 1


# ══ (c) DAMGA↔TS ÇAPRAZ SÜTUNU ════════════════════════════════════════════════════════════════
def test_c_capraz_sutun_tarihli_tabanda_ayrisma_YOK():
    """Kart tarihli tabanı: damgalı 4 satırın 4'ünde iki anahtar AYNI kolu gösteriyor."""
    capraz = _hakem().altbant_raporu(_tarihli_taban())["damga_ts_caprazi"]
    assert capraz["kiyaslanan"] == 4
    assert capraz["ayrisan"]["n"] == 0 and capraz["ayrisan"]["satirlar"] == []


def test_c_kasitli_ayrik_satir_sayilir_VE_listelenir():
    """`ts` kaydırma ÖNCESİ ama damga "1345": iki anahtar ZIT kol söylüyor → ayrışma."""
    satirlar = _tarihli_taban() + [
        _satir("ZZ", "2026-08-20", 9.9, ts="2026-08-20T20:30:00+00:00", pencere="1345")]
    capraz = _hakem().altbant_raporu(satirlar)["damga_ts_caprazi"]
    assert capraz["ayrisan"]["n"] == 1
    (ayrik,) = capraz["ayrisan"]["satirlar"]
    assert ayrik["ticker"] == "ZZ"
    assert ayrik["damga_kolu"] == "giris_1345" and ayrik["ts_kolu"] == "giris_once"
    assert capraz["kiyaslanan"] == 5                          # damgalı satır sayısı


def test_c_damgasiz_satir_AYRISMA_DEGIL():
    """Damgasız satır çapraz sütunda `damgasiz` sayılır; ayrışma sayılırsa 13 sahte alarm doğar."""
    capraz = _hakem().altbant_raporu(_tarihli_taban())["damga_ts_caprazi"]
    assert capraz["damgasiz"] == 13 and capraz["ayrisan"]["n"] == 0


def test_c_bilinmeyen_damga_ayrisma_DEGIL_adiyla_raporlanir():
    """Sözlükte olmayan damga kıyaslanamaz — "ayrışma" demek UYDURMA olurdu."""
    satirlar = [_satir("Q", "2026-08-20", 3.0, ts="2026-08-20T20:30:00+00:00", pencere="1400")]
    capraz = _hakem().altbant_raporu(satirlar)["damga_ts_caprazi"]
    assert capraz["ayrisan"]["n"] == 0 and capraz["kiyaslanan"] == 0
    assert capraz["damga_bilinmeyen"]["n"] == 1
    assert capraz["damga_bilinmeyen"]["satirlar"][0]["pencere"] == "1400"


# ══ (d) İTHAL — BÖLÜCÜNÜN İKİNCİ KOPYASI YOK ══════════════════════════════════════════════════
def test_d_hakem_kendi_gonderim_kolu_TANIMLAMAZ():
    """Kart p2_kapanis: "`gonderim_kolu()` ... İTHAL edilir (ikinci kopya YAZILMAZ)".
    İki kopya sessizce ayrışır ve hakem reçeteden BAŞKA bir kolu ölçmeye başlar."""
    agac = ast.parse(HAKEM.read_text(encoding="utf-8"))
    tanimlar = [d.name for d in ast.walk(agac) if isinstance(d, ast.FunctionDef)]
    assert "gonderim_kolu" not in tanimlar


def test_d_bolucunun_KODU_recete_dosyasindan_gelir():
    """Nesne KİMLİĞİ sınanamaz — `kaynaktan_yukle` her çağrıda kaynaktan DERLER, iki bağımsız
    yükleme iki ayrı nesne verir (tasarım: bayat pyc yolu kapalı). Sınanan şey daha güçlüsüdür:
    fonksiyonun kod nesnesi hangi DOSYADAN derlendi. Gövde hakeme kopyalanırsa bu yol hakem
    dosyasına döner ve çivi ısırır."""
    m, r = _hakem(), _recete()
    assert m.gonderim_kolu.__code__.co_filename == str(RECETE)
    assert m.gonderim_kolu.__code__.co_filename == r.gonderim_kolu.__code__.co_filename
    assert m.yuzdelik.__code__.co_filename == str(RECETE)      # `yuzdelik` de kopyalanmadı
    assert m.PENCERE_SINIRI == r.PENCERE_SINIRI


def test_d_sinir_sabiti_hakem_kaynaginda_LITERAL_olarak_YOK():
    """Sınır metni hakem dosyasına yazılırsa reçete sınırı değiştiğinde ikisi sessizce ayrışır."""
    assert "14:53:43" not in HAKEM.read_text(encoding="utf-8")


# ══ (e) ÖNERİ TETİĞİ EŞİĞİ — TEK KARAKTERİ DEĞİŞMEDİ ══════════════════════════════════════════
def test_e_esik_ve_bootstrap_kunyesi_donuk_hakemle_AYNI():
    for ad in ("ALT_BANT_N_ESIK", "B", "SEED"):
        assert _sabit(HAKEM, ad) == _sabit(DONUK_HAKEM, ad), f"{ad} değişti (kart kill#2)"


def test_e_iki_kol_da_esik_ustundeyken_tetik_degerlendirmesi_KOSAR():
    rapor = _hakem().altbant_raporu(
        _kol([4, 5, 6, 5, 4, 6, 5, 5, 4, 6, 5, 5], once=True)
        + _kol([5, 6, 4, 5, 6, 4, 5, 5, 6, 4, 5, 5], once=False))
    assert rapor["oneri_tetigi"]["sonuc"] == "tetiklenmedi"
    assert rapor["kollar"]["giris_once"]["ci"] is not None
    assert rapor["kollar"]["giris_1345"]["ci"] is not None


def test_e_1345_kolu_yuksek_yonde_ayrikken_geri_al_onerisi():
    rapor = _hakem().altbant_raporu(
        _kol([4, 5, 6, 5, 4, 6, 5, 5, 4, 6, 5, 5], once=True)
        + _kol([104, 105, 106, 105, 104, 106, 105, 105, 104, 106, 105, 105], once=False))
    assert rapor["oneri_tetigi"]["sonuc"] == "geri_al_onerisi"
    beyan = rapor["oneri_tetigi"]["beyan"]
    assert "GERİ-AL" in beyan and "otomatik" in beyan.lower()  # geri alma OTOMATİK DEĞİL


def test_e_n_10un_altinda_orneklem_birikimde():
    rapor = _hakem().altbant_raporu(
        _kol([4, 5, 6, 5, 4, 6, 5, 5, 4, 6, 5, 5], once=True)
        + _kol([104, 105, 106, 105, 104], once=False))        # n=5 < 10
    assert rapor["oneri_tetigi"]["sonuc"] == "orneklem_birikimde"
    assert rapor["kollar"]["giris_1345"]["ci"] is None


def test_e_bant_adlandirmasi_1330_1345_birakildi():
    """Kart p2_kapanis: "hakem raporu '1330/1345' bant adlarını bırakır"."""
    rapor = _hakem().altbant_raporu(_tarihli_taban())
    assert set(rapor["kollar"]) == {"giris_once", "giris_1345"}
    assert "bantlar" not in rapor


# ══ (f) ÇEKİM ALAN LİSTESİ — ESKİ LİSTE + `ts`, BAŞKA HİÇBİR DEĞİŞİKLİK ═══════════════════════
def test_f_cekim_alan_listesi_eskisi_arti_ts():
    """P-1'in görünmezlik zehiri: hakem kendi bölme anahtarını ÇEKMİYORDU. `ts` eklenir —
    ve YALNIZ o: alan çıkarmak damga çapraz sütununu ya da K1 filtresini kör ederdi."""
    eski, yeni = _sabit(DONUK_CEK, "E2_ALAN"), _sabit(CEK, "E2_ALAN")
    assert "ts" not in eski and "ts" in yeni
    assert tuple(yeni) == tuple(eski) + ("ts",)


def test_f_damga_alani_cekimde_KALIR():
    """`pencere` artık bölmez ama çapraz sütunun girdisidir — çekilmezse sütun ölür."""
    assert "pencere" in _sabit(CEK, "E2_ALAN")


# ══ (g) OPERATÖRÜN KOŞACAĞI GİRİŞ NOKTASI ═════════════════════════════════════════════════════
# CLAUDE.md §6 dersi (2026-08-30): 18 çivi yeşilken betik komut satırından HİÇBİR ŞEY yapmıyordu.
# `main()`in özet anahtarları hiçbir davranış çivisinden geçmez — kol adları değişti, o satırlar
# eski sözlüğe bakıyor olsaydı çivi setinin tamamı yeşil kalır, operatör KeyError görürdü.
# Koşum GERÇEKTİR ama YALITILMIŞTIR: DIZIN/HAM tmp_path'e çevrilir, depoya da state/'e de tek
# bayt yazılmaz (modül zaten `meridian`e hiç uzanmaz — obs'a erişimi yoktur).
def _yalitilmis_main(tmp_path, monkeypatch, ham_govde):
    m = _hakem()
    (tmp_path / "pencere_ham.json").write_text(__import__("json").dumps(ham_govde),
                                               encoding="utf-8")
    monkeypatch.setattr(m, "DIZIN", tmp_path)
    monkeypatch.setattr(m, "HAM", tmp_path / "pencere_ham.json")
    return m


def test_g_main_ozeti_kol_adlariyla_konusur_ve_json_yazar(tmp_path, monkeypatch, capsys):
    import json as _json
    m = _yalitilmis_main(tmp_path, monkeypatch,
                         {"cekim_zamani": "2026-09-01T00:00:00+00:00", "makine": "A1 (canli)",
                          "yururluk_rejimi": "1345",
                          "entry_execution": {"n": 17, "satirlar": _tarihli_taban()}})
    m.main()
    ozet = _json.loads(capsys.readouterr().out.strip())
    assert ozet["n_giris_once"] == 15 and ozet["n_giris_1345"] == 2
    assert ozet["damgasiz"] == 13 and ozet["damga_ts_ayrisan"] == 0
    assert ozet["oneri_tetigi"] == "orneklem_birikimde"
    yazilan = _json.loads((tmp_path / "pencere_altbant.json").read_text(encoding="utf-8"))
    assert yazilan["kollar"]["giris_once"]["n"] == 15          # rapor dosyası da kol sözlüğünde
    assert yazilan["yururluk_rejimi"] == "1345"


def test_g_cekim_yoksa_rapor_URETILMEZ_nedenle_cikar(tmp_path, monkeypatch, capsys):
    """UYDURMA YASAĞI: girdi yokken boş/varsayılan rapor üretmek sessiz bir yalandır."""
    m = _hakem()
    monkeypatch.setattr(m, "DIZIN", tmp_path)
    monkeypatch.setattr(m, "HAM", tmp_path / "pencere_ham.json")     # dosya YOK
    with pytest.raises(SystemExit) as e:
        m.main()
    assert e.value.code == 2
    assert __import__("json").loads(capsys.readouterr().out.strip())["olculemedi"] is True
    assert not (tmp_path / "pencere_altbant.json").exists()
