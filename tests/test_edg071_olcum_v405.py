"""tests/test_edg071_olcum_v405.py — EDG-2026-071 RESMÎ ÖLÇÜM betiğinin çivisi (EDG-071, 2026-09-04).

NE ÖLÇER. `research/olcumler/edg071_hayalet_suzgec/olcum.py` — kartın (`EDG-2026-071-hayalet-
dugme-oneri-suzgeci.yaml`) K1 (tarihsel hayalet payı, git blob arkeolojisi) + K2 (sandbox, bugünkü
bounds + gerçek `propose_virgin_knob` + fail-open) + PK (yol-tutarlı) bileşenlerini doğru ölçtüğünü
kanıtlar. Bu dosya AŞAĞIDAKİLERİ ölçer:
  (a) eşikler kartın YAPILANDIRILMIŞ `esikler:` alanından doğru okunuyor mu, eksikse UYDURMUYOR mu;
  (b) girdi şeması dedektörü ve donmuş girdi dosyasının kendisi (60 satır, ihlalsiz);
  (c) `_sabitler_metinlerden` (reflect'ten türetilen AST çekirdeği) docstring'i HARİÇ TUTUYOR,
      gerçek sabiti SAYIYOR, eksik modülü sıfır katkı sayıyor, parse hatasında None dönüyor mu;
  (d) K1'İN GÜN-BAZLI ÇÖZÜMLEME REGRESYONU: bu betiğin İLK sürümü aynı güne düşen iki farklı `ts`yi
      günün EN ERKEN ts'siyle TEK commit'e çözüyordu — gerçek veride (2026-07-31) bir satır repo-
      öncesi, bir satır repo-sonrasıydı ve İKİNCİSİ BİRİNCİSİNİN "ölçülemedi" hükmünü MİRAS ALDI.
      Bu betiğin KENDİ turunda ÖLÇÜLEREK bulunan ve düzeltilen kusur; bu test o düzeltmeyi çivi
      YAPAR (sentetik, gün sınırından bağımsız);
  (e) K1'in oran/üretici-kırılımı aritmetiği (sentetik, git'siz);
  (f) ÖZ-SINAMA: HEAD'de git-blob türevi == canlı `reflect.motor_okunan_sabitler()`;
  (g) K2: bugünkü bounds'ta yanlış-pozitif SIFIR + fail-open sessizleşmiyor;
  (h) POZİTİF KONTROL yol-tutarlı: sentetik hayalet düğme yakalanır/kablolu geçer — VE MUTASYON
      (CLAUDE.md §6 "çivi yeşili kanıt değildir"): `reflect.hayalet_suzgeci` her şeyi 'temiz' sayan
      bir saplamaya döndürülürse PK GERÇEKTEN kırmızıya döner mi;
  (i) SANDBOX KANITI: `k2_olc`/`pk_yol_tutarli` GERÇEK repo `state/*.jsonl`sine YAZMAZ (varsayılmaz,
      betiğin kendi mtime+satır izi yardımcılarıyla ÖLÇÜLÜR).

KAPSAM DIŞI: kartın hükmü (Rol-1 verir, CLAUDE.md §3/§5) — bu dosya betiğin DOĞRU ÖLÇTÜĞÜNÜ
kanıtlar, "süzgeç uygulanır/uygulanmaz" kararı vermez. `meridian/*.py` bu dosyada da DEĞİŞTİRİLMEZ
— (h)'nin mutasyonu `monkeypatch.setattr(reflect, ...)` ile BELLEKTE yapılır, pytest testin sonunda
geri alır.
"""
from __future__ import annotations

import pathlib

import pytest
import yaml

from tests.conftest import betikten_modul_yukle

KOK = pathlib.Path(__file__).resolve().parents[1]
BETIK_YOLU = KOK / "research" / "olcumler" / "edg071_hayalet_suzgec" / "olcum.py"
KART_YOLU = KOK / "research" / "cards" / "EDG-2026-071-hayalet-dugme-oneri-suzgeci.yaml"


def _olcum():
    return betikten_modul_yukle(BETIK_YOLU, "edg071_olcum")


# ==================================================================================
# (a) eşikler karttan okunuyor (yapılandırılmış alan, regex GEREKMEZ)
# ==================================================================================

def test_esikler_kartin_yapilandirilmis_alanindan_okunur():
    o = _olcum()
    esikler = o.esikleri_karttan_oku(KART_YOLU)
    assert esikler["hayalet_payi_alt_anlamli"] == pytest.approx(0.10)
    assert esikler["yanlis_pozitif_ust"] == 0
    assert esikler["kart_id"] == "EDG-2026-071"


def test_esik_eksikse_UYDURMAZ_value_error_atar(tmp_path):
    o = _olcum()
    bozuk = tmp_path / "bozuk-kart.yaml"
    bozuk.write_text("card_id: SENTETIK-2026-000\nesikler:\n  hayalet_payi_alt_anlamli: 0.10\n",
                     encoding="utf-8")
    with pytest.raises(ValueError, match="yanlis_pozitif_ust"):
        o.esikleri_karttan_oku(bozuk)


def test_esikler_alani_sozluk_degilse_UYDURMAZ_value_error_atar(tmp_path):
    o = _olcum()
    bozuk = tmp_path / "bozuk2.yaml"
    bozuk.write_text("card_id: SENTETIK-2026-001\nesikler: metin-sozluk-degil\n", encoding="utf-8")
    with pytest.raises(ValueError, match="esikler"):
        o.esikleri_karttan_oku(bozuk)


# ==================================================================================
# (b) girdi şeması
# ==================================================================================

def test_donmus_girdi_dosyasi_60_satir_ihlalsiz():
    o = _olcum()
    satirlar = o.gozlem_satirlarini_oku(o.GIRDI_VARSAYILAN)
    assert len(satirlar) == 60
    assert o.sema_ihlallerini_bul(satirlar) == []


def test_sema_ihlali_eksik_alan_adiyla_yakalanir():
    o = _olcum()
    ihlaller = o.sema_ihlallerini_bul([{"variable": "x", "ts": "2026-01-01T00:00:00+00:00"}])
    assert len(ihlaller) == 1 and "source" in ihlaller[0]


def test_ana_kuru_modu_gecerli_girdiyle_0_doner(capsys):
    o = _olcum()
    rc = o.main(["--girdi", str(o.GIRDI_VARSAYILAN), "--kart", str(KART_YOLU), "--kuru"])
    assert rc == 0
    assert "GÜNCEL-ŞEMA" in capsys.readouterr().out


def test_ana_kuru_modu_bozuk_girdiyle_1_doner(tmp_path, capsys):
    o = _olcum()
    bozuk = tmp_path / "bozuk.jsonl"
    bozuk.write_text('{"variable": "x", "ts": "2026-01-01T00:00:00+00:00"}\n', encoding="utf-8")
    rc = o.main(["--girdi", str(bozuk), "--kart", str(KART_YOLU), "--kuru"])
    assert rc == 1
    assert "BOZUK-ŞEMA" in capsys.readouterr().err


# ==================================================================================
# (c) AST çekirdeği (reflect'ten türetildi) — docstring hariç, eksik modül sıfır katkı, parse hatası
# ==================================================================================

def test_sabitler_metinlerden_docstring_haric_gercek_sabit_dahil():
    o = _olcum()
    metin = (
        '"""Modul docstring: GIZLI_SABIT_ASLA_SAYILMAZ."""\n\n'
        "def f():\n"
        '    """fonksiyon docstring: BU_DA_SAYILMAZ"""\n'
        '    return "GERCEK_SABIT_SAYILIR"\n'
    )
    sabitler, neden = o._sabitler_metinlerden({"m": metin})
    assert neden is None
    assert "GERCEK_SABIT_SAYILIR" in sabitler
    assert "GIZLI_SABIT_ASLA_SAYILMAZ" not in sabitler
    assert "BU_DA_SAYILMAZ" not in sabitler


def test_sabitler_metinlerden_eksik_modul_sifir_katki():
    o = _olcum()
    sabitler, neden = o._sabitler_metinlerden({"var_olan": 'x = "A"\n', "yok_olan": None})
    assert neden is None
    assert sabitler == frozenset({"A"})


def test_sabitler_metinlerden_parse_hatasi_None_ve_neden_doner():
    o = _olcum()
    sabitler, neden = o._sabitler_metinlerden({"bozuk": "def f(:\n"})
    assert sabitler is None
    assert neden is not None and len(neden) >= 5


# ==================================================================================
# (d) K1 REGRESYON ÇİVİSİ: aynı gün + farklı ts → BAĞIMSIZ çözüm (gün-bazlı pooling YOK)
# ==================================================================================

def test_K1_ayni_gun_farkli_ts_BAGIMSIZ_cozulur(monkeypatch):
    """Bu betiğin İLK sürümü günün EN ERKEN ts'siyle TEK commit çözüyordu; gerçek veride
    (2026-07-31: 02:52 UTC repo-öncesi, 11:34 UTC repo-sonrası) ikinci satır birincinin
    'ölçülemedi' hükmünü MİRAS ALIYORDU — ölçülerek bulunan bir kusur. Sentetik: aynı gün iki ts,
    biri commit BULAMAZ biri BULUR; ikisi de KENDİ ts'sine göre bağımsız sonuç almalı."""
    o = _olcum()
    monkeypatch.setattr(o, "ilk_commit_zamani", lambda: "2020-01-01T00:00:00+00:00")

    cagrilar: list[str] = []

    def sahte_commit_oncesi(ts):
        cagrilar.append(ts)
        return None if ts.endswith("T01:00:00+00:00") else "c" * 40

    monkeypatch.setattr(o, "commit_oncesi", sahte_commit_oncesi)
    monkeypatch.setattr(o, "blob_metni", lambda sha, m: (f'x = "aile.{m}"\n', None))

    satirlar = [
        {"id": "S1", "variable": "aile.strategy", "ts": "2026-07-31T01:00:00+00:00", "source": "t"},
        {"id": "S2", "variable": "aile.strategy", "ts": "2026-07-31T23:00:00+00:00", "source": "t"},
    ]
    esikler = {"hayalet_payi_alt_anlamli": 0.10, "yanlis_pozitif_ust": 0}
    k1 = o.k1_tarihsel(satirlar, esikler)
    durumlar = {r["id"]: r["durum"] for r in k1["satirlar"]}

    assert len(cagrilar) == 2, "iki BENZERSİZ ts iki AYRI commit_oncesi çağrısı almalı"
    assert durumlar["S1"] == "OLCULEMEDI"
    assert durumlar["S2"] != "OLCULEMEDI", (
        "aynı gündeki İKİNCİ satır BİRİNCİNİN (çözülemeyen) sonucunu miras aldı — regresyon geri geldi")
    assert durumlar["S2"] == "TEMIZ"


# ==================================================================================
# (e) K1 oran + üretici kırılımı aritmetiği (sentetik, git'siz)
# ==================================================================================

def test_K1_hayalet_orani_ve_uretici_kirilimi_dogru_hesaplanir(monkeypatch):
    o = _olcum()
    monkeypatch.setattr(o, "ilk_commit_zamani", lambda: "2020-01-01T00:00:00+00:00")
    monkeypatch.setattr(o, "commit_oncesi", lambda ts: "d" * 40)

    def sahte_blob(sha, m):
        return ('x = "gercek.dugme"\n' if m == "strategy" else ""), None

    monkeypatch.setattr(o, "blob_metni", sahte_blob)

    satirlar = [
        {"id": "A", "variable": "gercek.dugme", "ts": "2026-01-01T00:00:00+00:00", "source": "kaynakX"},
        {"id": "B", "variable": "hayalet.dugme", "ts": "2026-01-02T00:00:00+00:00", "source": "kaynakX"},
        {"id": "C", "variable": "hayalet.dugme", "ts": "2026-01-03T00:00:00+00:00", "source": "kaynakY"},
    ]
    esikler = {"hayalet_payi_alt_anlamli": 0.10, "yanlis_pozitif_ust": 0}
    k1 = o.k1_tarihsel(satirlar, esikler)

    assert k1["olculen_oneri"] == 3
    assert k1["hayalet_oneri"] == 2
    assert k1["hayalet_orani_olculenden"] == pytest.approx(2 / 3, abs=1e-4)
    assert k1["esik_karsilastirma"]["esigi_gecti_mi"] is True
    assert k1["uretici_kirilimi"]["kaynakX"] == {
        "toplam": 2, "olculen": 2, "hayalet": 1, "olculemedi": 0,
        "hayalet_orani_olculenden": pytest.approx(0.5)}
    assert k1["uretici_kirilimi"]["kaynakY"] == {
        "toplam": 1, "olculen": 1, "hayalet": 1, "olculemedi": 0,
        "hayalet_orani_olculenden": pytest.approx(1.0)}


def test_K1_git_tarihi_oncesi_satir_ayri_sayilir_UYDURULMAZ(monkeypatch):
    """repo git tarihinden önceki gün için `commit_oncesi` None dönerse satır HAYALET/TEMIZ diye
    UYDURULMAZ — OLCULEMEDI diye AYRI sayılır ve oran hesabına GİRMEZ."""
    o = _olcum()
    monkeypatch.setattr(o, "ilk_commit_zamani", lambda: "2026-01-01T00:00:00+00:00")
    monkeypatch.setattr(o, "commit_oncesi", lambda ts: None)
    satirlar = [{"id": "A", "variable": "her.hangi", "ts": "2020-01-01T00:00:00+00:00", "source": "t"}]
    esikler = {"hayalet_payi_alt_anlamli": 0.10, "yanlis_pozitif_ust": 0}
    k1 = o.k1_tarihsel(satirlar, esikler)
    assert k1["olculemedi_oneri"] == 1
    assert k1["olculen_oneri"] == 0
    assert k1["hayalet_orani_olculenden"] is None
    assert k1["satirlar"][0]["durum"] == "OLCULEMEDI"


# ==================================================================================
# (f) ÖZ-SINAMA: HEAD blob türevi == canlı reflect.motor_okunan_sabitler()
# ==================================================================================

def test_oz_sinama_HEAD_de_gecer():
    o = _olcum()
    sonuc = o.oz_sinama_head()
    assert sonuc["gecti"] is True, sonuc
    assert sonuc["n_turetilen"] == sonuc["n_gercek"]


# ==================================================================================
# (g) K2 — bugünkü bounds, yanlış-pozitif SIFIR, fail-open sessizleşmiyor
# ==================================================================================

def test_K2_bugunku_bounds_yanlis_pozitif_sifir_ve_fail_open_sessizlesmiyor():
    o = _olcum()
    k2 = o.k2_olc()
    assert k2["n_bounds"] >= 30
    assert k2["yanlis_pozitif_sayisi"] == 0
    assert k2["yanlis_pozitif_liste"] == []
    assert k2["temiz_sayisi"] == k2["n_bounds"]
    fo = k2["fail_open"]
    assert fo["hayalet_none_mu"] is True
    assert fo["temiz_tum_anahtarlari_kapsadi_mi"] is True
    assert fo["olay_yazildi_mi"] is True
    assert fo["sessizlesmedi_mi"] is True


# ==================================================================================
# (h) POZİTİF KONTROL yol-tutarlı + MUTASYON (çivi yeşili kanıt değildir, CLAUDE.md §6)
# ==================================================================================

def test_PK_yol_tutarli_gecer():
    o = _olcum()
    pk = o.pk_yol_tutarli()
    assert pk["pk_gecti"] is True
    assert pk["izole_suzgec"]["hayalet_yakalandi"] is True
    assert pk["izole_suzgec"]["kablolu_gecti"] is True
    assert pk["secenek_a_bilesimi"]["ghost_candidate_loopta_gorundu_mu"] is False
    assert pk["secenek_a_bilesimi"]["real_candidate_loopta_gorundu_mu"] is True
    assert pk["oneri_hayalet_mi"] is False
    assert pk["oneri"] is not None and pk["oneri"]["variable"] == o.REAL_KNOB


def test_PK_MUTASYON_suzgec_devre_disi_birakilirsa_KIRMIZIYA_DONER(monkeypatch):
    """NEGATİF KONTROL: `reflect.hayalet_suzgeci` her anahtarı 'temiz' sayan bir saplamaya
    dönerse (süzgeç YOKMUŞ gibi) PK artık YEŞİL KALMAMALI — yoksa PK süzgeci değil başka bir şeyi
    ölçüyor demektir (CLAUDE.md §6: "çivi yeşili kanıt değildir")."""
    o = _olcum()
    from meridian import reflect

    def sahte_suzgec_hicbirsey_yakalamaz(bounds, kaynak):
        return list(bounds.keys()), []

    monkeypatch.setattr(reflect, "hayalet_suzgeci", sahte_suzgec_hicbirsey_yakalamaz)
    pk = o.pk_yol_tutarli()
    assert pk["pk_gecti"] is False
    assert pk["izole_suzgec"]["hayalet_yakalandi"] is False
    assert pk["secenek_a_bilesimi"]["ghost_candidate_loopta_gorundu_mu"] is True


def test_PK_govde_kontrolu_bozuk_fikstürde_patlar(monkeypatch):
    """v263 N0 deseni: GHOST_KNOB literali motor kaynağında GEÇERSE PK fikstürü bozuktur ve bu
    ADIYLA patlamalı — süzgecin kendisi suçlanmamalı."""
    o = _olcum()
    monkeypatch.setattr(o, "GHOST_KNOB", "entry.min_score")   # gerçek, motorda okunan bir literal
    with pytest.raises(AssertionError, match="entry.min_score"):
        o._pk_govde_kontrolu()


# ==================================================================================
# (i) SANDBOX KANITI: gerçek repo state/*.jsonl'e YAZILMAZ (ölçülür, varsayılmaz)
# ==================================================================================

def test_sandbox_gercek_repo_stateine_YAZMAZ():
    o = _olcum()
    once = o._state_jsonl_izi()
    o.k2_olc()
    o.pk_yol_tutarli()
    sonra = o._state_jsonl_izi()
    karsilastirma = o._state_izi_karsilastir(once, sonra)
    assert karsilastirma["temiz_mi"] is True, karsilastirma["degisen"]


def test_sandbox_baglami_config_STATE_geri_alir():
    """`_sandbox()` bağlamı kapanınca `config.STATE` başlangıçtaki değerine GERİ ALINMALI —
    yoksa bu betikten SONRA koşan her şey (aynı süreçte) yanlış state'e bakar."""
    o = _olcum()
    from meridian import config
    eski = config.STATE
    with o._sandbox() as yeni:
        assert config.STATE == yeni
        assert config.STATE != eski
    assert config.STATE == eski


# ==================================================================================
# (kart ↔ girdi tutarlılığı) — ADIM-0(a): üretici/kaynak etiketi okunabiliyor mu
# ==================================================================================

def test_girdi_uretici_etiketi_ADIM0_okunabiliyor():
    o = _olcum()
    satirlar = o.gozlem_satirlarini_oku(o.GIRDI_VARSAYILAN)
    kaynaklar = {s["source"] for s in satirlar}
    assert kaynaklar, "ADIM-0(a) düşerdi: hiçbir satırda okunabilir 'source' yok"
    assert all(isinstance(k, str) and k for k in kaynaklar)


def test_kart_kill_list_yanlis_pozitif_sinama_esigi_sifir():
    """Kart kill-list'i: 'K2 yanlış-pozitif > 0 → TASARIM GEÇERSİZ'. Eşiğin kendisi 0 mı?"""
    kart = yaml.safe_load(KART_YOLU.read_text(encoding="utf-8"))
    assert kart["esikler"]["yanlis_pozitif_ust"] == 0
