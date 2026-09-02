"""test_codelaw_tsx_capa_v314.py — SATIR ÇAPASI YASASININ TSX KÖR NOKTASI (2026-08-25).

İki denetçi bağımsız olarak aynı boşluğu buldu: `codelaw.stale_line_anchors` yalnız `*.py`
tarıyordu (`meridian` + `tests` + `ops` kökleri). `ui/src` altındaki `.ts`/`.tsx` dosyalarında
yaşayan `dosya.py:NNN` çapalarını HİÇBİR çivi görmüyordu — yani panonun kaynağı, Python
tarafında yasayla kapatılmış bir çürüme sınıfının açık kaldığı ikinci bir dünyaydı.

ÖLÇÜM (bu tur, `ui/src`, 210 dosya): turun başında 200 çapa · 40 BAYAT; aynı turda başka iş
kolları kendi çapalarını sembole çevirdikçe kapanışta 161 çapa · 35 BAYAT (22 `yorum`,
13 `bos_satir`) · 0 çözülemeyen. Yüzlerce çapayı sembole çevirmek bu turun işi DEĞİL; tsx tarafı SIFIR
TOLERANSLA değil ÇIRÇIRLA (`codelaw.TSX_CAPA_TABANI`) kapanır: borcun BÜYÜMESİ ihlaldir,
varlığı kayıtlı bir borçtur. Python tarafının sıfır toleransı DEĞİŞMEZ ve bu dosya iki dünyanın
birbirine karışmadığını da ölçer.

Her sıfır/eşik iddiasının yanında POZİTİF KONTROL var (test_codelaw_v59 disiplini): sentetik
bayat bir tsx çapası verilir ve tarayıcının onu YAKALAMASI beklenir — yoksa "taban aşılmadı"
cümlesi, taramanın sessizce boş dönmesiyle aynı şeye benzerdi.
"""
from __future__ import annotations

import pathlib

from meridian import codelaw

#: Bu turda ÖLÇÜLEN bayat tsx çapası sayısı — çırçırın TAVANI. Kaynaktaki
#: `codelaw.TSX_CAPA_TABANI` bu değerin ALTINA inebilir (temizlik yapıldıkça inmeli), ama
#: ÜSTÜNE ÇIKAMAZ: tabanı yükseltmek, borcu ödemek yerine borcu meşrulaştırmak olurdu
#: (kill-list disiplini — `test_ihlal_seti_GERILEMEDI`nin `SINK_TABANI` deseni).
#:
#: 32 → 0 (TSK-094, ölçüldü 2026-09-02): `ui/src` altındaki 141 satır çapasının TAMAMI
#: `dosya.py::sembol` biçimine taşındı ve ağaçta bayatlayabilecek satır çapası KALMADI.
#: Çırçır bu yüzden emekli DEĞİL, KAPANDI: bundan sonra `ui/src`e yazılan bir satır çapası
#: bayatladığı gün TEK BAŞINA `report()["ok"]`i düşürür — borç sıfırlandığı için tolerans da
#: sıfırdır. Bu dosyanın geri kalanı (sentetik pozitif kontroller) DEĞİŞMEDEN duruyor: tarayıcı
#: hâlâ ölçülüyor, yalnız canlı ağaçta ölçecek borç kalmadı.
OLCULEN_TAVAN = 0


def _sentetik_agac(kok: pathlib.Path, tsx_govde: str, ad: str = "Kart.tsx") -> None:
    """Bir tmp ağacına tek satırlık bir Python hedefi ve ona çapa atan bir tsx dosyası yazar.

    `sentetik_hedef.py` adı BİLEREK depoda bulunmayan bir addır: bu dosyanın kendi metnindeki
    çapa metinleri, canlı ağacı tarayan `stale_line_anchors` tarafından `hedef_yok` (hüküm
    kurulamayan) olarak sayılır — ihlal olarak DEĞİL."""
    (kok / "sentetik_hedef.py").write_text("x = 1\n", encoding="utf-8")
    (kok / ad).write_text(tsx_govde, encoding="utf-8")


# ---------------------------------------------------------------------------
# (a) ÇAPA ARTIK GÖRÜLÜYOR
# ---------------------------------------------------------------------------

def test_tsx_capasi_ARTIK_GORULUYOR(tmp_path):
    """`.tsx` içindeki menzil-dışı çapa yakalanır. Kör noktanın kendisi budur: aynı metin bir
    `.py` dosyasında olsaydı yasa onu bugün de görüyordu."""
    _sentetik_agac(tmp_path, '// kaynak: sentetik_hedef.py:999\nexport const K = 1;\n')
    curuk = codelaw.stale_tsx_line_anchors(str(tmp_path), py_kokler=(str(tmp_path),))
    assert [(c["capa"], c["neden"]) for c in curuk] == [("sentetik_hedef.py:999", "menzil_disi")], curuk


def test_ts_uzantisi_da_taranir(tmp_path):
    """Kapsam `.tsx` ile sınırlı DEĞİL: ölçülen bayatların en yoğun kaynağı düz `.ts` dosyaları
    (`krizUclari.ts` 4, `tipler.ts` 3, `onayEylem.ts` 3)."""
    _sentetik_agac(tmp_path, 'export const U = "sentetik_hedef.py:999";\n', ad="uclar.ts")
    curuk = codelaw.stale_tsx_line_anchors(str(tmp_path), py_kokler=(str(tmp_path),))
    assert [c["kaynak"] for c in curuk] == ["uclar.ts:1"], curuk


def test_tsx_capasi_YORUM_ve_BOS_SATIRI_da_curuk_sayar(tmp_path):
    """Çürüme sınıfı `.py` tarafındakinin AYNISI: menzil-dışı · boş satır · yorum. Canlı ağaçta
    ölçülen 35 bayatın hepsi son iki sınıftan (22 `yorum`, 13 `bos_satir`) — yalnız menzil-dışıyı
    gören bir tarayıcı bugünkü borcun TAMAMINI kaçırırdı."""
    (tmp_path / "sentetik_hedef.py").write_text("# yorum satiri\n\nx = 1\n", encoding="utf-8")
    (tmp_path / "Kart.tsx").write_text(
        "// sentetik_hedef.py:1\n// sentetik_hedef.py:2\n// sentetik_hedef.py:3\n", encoding="utf-8")
    curuk = codelaw.stale_tsx_line_anchors(str(tmp_path), py_kokler=(str(tmp_path),))
    assert [c["neden"] for c in curuk] == ["yorum", "bos_satir"], curuk


def test_tsx_capasi_MEZAR_TASINI_muaf_tutar(tmp_path):
    """Beyanlı muafiyet iki dünyada da AYNI işaretle çalışır: bayat çapayı KANIT olarak alıntılayan
    satır bulgu değildir. İki ayrı muafiyet işareti icat etmek, `.tsx`e taşınan bir dersi sessizce
    ihlale çevirirdi."""
    _sentetik_agac(tmp_path, '// sentetik_hedef.py:999 bayatladı  // çapa-mezar-taşı\n')
    assert codelaw.stale_tsx_line_anchors(str(tmp_path), py_kokler=(str(tmp_path),)) == []


def test_tsx_COZULEMEYENI_SESSIZCE_ATMAZ(tmp_path):
    """Hükmü kurulamayan tsx çapası SAYILIR (py tarafındaki `line_anchor_unresolved` disiplini):
    "0 çürük" cümlesi, kaçının hakkında hüküm KURULAMADIĞI bilinmeden okunamaz."""
    _sentetik_agac(tmp_path, '// yok_boyle_bir_dosya.py:12 ve sentetik_hedef.py:1\n')
    kor: list[dict] = []
    assert codelaw.stale_tsx_line_anchors(str(tmp_path), py_kokler=(str(tmp_path),),
                                          cozulemeyen_out=kor) == []
    assert [(k["neden"], k["capa"]) for k in kor] == [("hedef_yok", "yok_boyle_bir_dosya.py:12")], kor


def test_KOK_YOKSA_KORLUK_KAYDA_GECER(tmp_path):
    """Kök bulunamazsa (yanlış çalışma dizini, kaynağı olmayan kurulum) yasa SESSİZ YEŞİL vermez:
    körlük `UNSCANNED`e düşer ve `report()["ok"]`i oradan düşürür. "0 bayat çapa" ile "hiç
    bakmadım" aynı görünseydi, taşınan tek bir dizin çivinin tamamını iptal ederdi."""
    codelaw.UNSCANNED.clear()
    try:
        assert codelaw.stale_tsx_line_anchors(str(tmp_path / "yok_boyle_bir_kok")) == []
        assert [k["phase"] for k in codelaw.UNSCANNED] == ["stale_tsx_line_anchors"], codelaw.UNSCANNED
    finally:
        codelaw.UNSCANNED.clear()


def test_TARAMA_SESSIZCE_BOS_DEGIL():
    """POZİTİF KONTROL: "taban aşılmadı" hükmü ancak tarayıcı gerçekten dosya buluyorsa anlamlı.
    Yanlış bir kök (ya da yanlış uzantı süzgeci) sıfır dosya döner ve çırçır ebediyen yeşil
    kalırdı — bekçinin kendi körlüğünü yeşil sanması sınıfı."""
    dosyalar = list(codelaw._ts_files(codelaw.TSX_CAPA_KOKU))
    assert len(dosyalar) >= 100, f"{codelaw.TSX_CAPA_KOKU} altında yalnız {len(dosyalar)} dosya görüldü"
    assert any(d.suffix == ".tsx" for d in dosyalar) and any(d.suffix == ".ts" for d in dosyalar)


# ---------------------------------------------------------------------------
# (b) ÇIRÇIR: taban aşılınca öter, altında susar
# ---------------------------------------------------------------------------

def test_taban_ASILINCA_OTER():
    """Çırçırın ötme yönü. Taban ALTINDAKİ sayı ihlal değildir; taban ÜSTÜ ihlaldir."""
    capalar = [{"kaynak": "A.tsx:1"}, {"kaynak": "B.tsx:2"}]
    assert codelaw.tsx_capa_nuksu(capalar, taban=1) is True


def test_taban_ALTINDA_ve_TABANDA_SUSAR():
    """İki yön birden çivilenir: TABANIN KENDİSİ ihlal değildir (`>` , `>=` değil) ve DÜŞÜŞ
    serbesttir — başka ajanlar aynı turda kendi `.tsx` dosyalarındaki çapaları sembole çeviriyor,
    yani sayı tur sonunda tabanın altına inebilir ve bu bir kırmızı OLMAMALI."""
    capalar = [{"kaynak": "A.tsx:1"}, {"kaynak": "B.tsx:2"}]
    assert codelaw.tsx_capa_nuksu(capalar, taban=2) is False
    assert codelaw.tsx_capa_nuksu(capalar, taban=9) is False
    assert codelaw.tsx_capa_nuksu([], taban=0) is False


def test_TABAN_YUKSELTILEMEZ():
    """Kill-list disiplini: taban DÜŞEBİLİR (temizlik), YÜKSELEMEZ. Tavanı bu dosya tutar —
    kaynaktaki sabiti büyüterek kırmızıyı susturmak, borcu ödemek yerine borcu meşrulaştırmaktır
    ve o hamle burada kırmızıya çarpar."""
    assert codelaw.TSX_CAPA_TABANI <= OLCULEN_TAVAN, (
        f"taban YÜKSELTİLMİŞ ({codelaw.TSX_CAPA_TABANI} > {OLCULEN_TAVAN}) — çırçır tersine "
        f"çevrilemez; çapaları sembole çevir, tabanı değil")


def test_CANLI_AGACTA_taban_ASILMADI():
    """Yasanın canlı hükmü: bugünkü bayat tsx çapası sayısı tabanın ÜSTÜNE çıkmadı."""
    curuk = codelaw.stale_tsx_line_anchors()
    assert not codelaw.tsx_capa_nuksu(curuk), (
        f"tsx çapa borcu BÜYÜDÜ: {len(curuk)} > taban {codelaw.TSX_CAPA_TABANI}. Yeni çapa "
        f"eklendi ya da bir Python dosyası kaydı; doğru tepki numarayı güncellemek değil, "
        f"çapayı SEMBOLE çevirmektir. Örnekler: {[c['kaynak'] for c in curuk[:5]]}")


# ---------------------------------------------------------------------------
# (d) İKİ DÜNYA, İKİ KURAL — ve karışmıyorlar
# ---------------------------------------------------------------------------

def test_PY_TARAFI_TSX_capasini_GORMEZ(tmp_path):
    """`stale_line_anchors` `.tsx` dosyalarını TARAMAZ ve bu bilinçli: iki tarayıcı iki farklı
    hüküm veriyor (py = sıfır tolerans, tsx = çırçır). `.tsx`i py tarayıcısına eklemek 35 bayatı
    anında sıfır-tolerans kapısına sokar ve tam suite kırmızıya dönerdi."""
    _sentetik_agac(tmp_path, '// sentetik_hedef.py:999\n')
    assert codelaw.stale_line_anchors(str(tmp_path)) == []
    assert len(codelaw.stale_tsx_line_anchors(str(tmp_path), py_kokler=(str(tmp_path),))) == 1


def test_PY_TARAFINDA_TEK_CAPA_BILE_DUSURUR(tmp_path, monkeypatch):
    """Python tarafında TABAN YOK: tek bir bayat çapa `report()["ok"]`i düşürür. Çırçır yalnız
    tsx dünyasına aittir; py hükmünü gevşetseydi bu tur, ölçülmüş bir borcu kapatmak yerine
    kapalı bir sınıfı yeniden açardı.

    Deney TEK DEĞİŞKENLİDİR (aynı ağaç, tek eklenen çapa) ve `stale_claims` yalıtılır — gerekçesi
    `test_TSX_NUKSU_report_OKUNU_DUSURUR`de yazılı.

    (Canlı ağacın py çapaları BURADA ölçülmez — o `test_satir_capalari_CURUK_DEGIL`in işidir ve
    aynı iddiayı iki dosyada tutmak, tek bir bayatlamayı iki kırmızıya çevirirdi.)"""
    codelaw.UNSCANNED.clear()
    monkeypatch.setattr(codelaw, "stale_claims", lambda *a, **k: [])
    (tmp_path / "sentetik_hedef.py").write_text("x = 1\n", encoding="utf-8")
    r = codelaw.report(str(tmp_path))
    assert r["stale_line_anchors"] == [] and r["ok"] is True, r
    assert r["tsx_line_anchors"] is None, "sentetik kökte tsx ÖLÇÜLMEZ"
    (tmp_path / "beyan.py").write_text('S = "sentetik_hedef.py:999"\n', encoding="utf-8")
    r = codelaw.report(str(tmp_path))
    assert len(r["stale_line_anchors"]) == 1, r["stale_line_anchors"]
    assert r["ok"] is False, "py tarafında TEK çapa bile düşürmeli — orada taban YOK"


# ---------------------------------------------------------------------------
# RAPOR YÜZEYİ — YASA 6: yazılan her alanın okuyucusu var
# ---------------------------------------------------------------------------

def test_report_TSX_CIRCIRINI_disari_verir():
    """Çırçırın sayısı ve hükmü `report()`ten okunur (YASA 6: bu alanların okuyucusu bu dosya).

    `ok` BURADA sınanmaz: canlı ağaçtaki `ok`, py çapaları ve `UNSCANNED` dahil altı bileşenin
    birleşimidir; başka bir bileşen kırmızıyken buradaki `ok is True` iddiası tsx hakkında hiçbir
    şey kanıtlamaz. Çırçırın `ok`a BAĞLI olduğu, aşağıdaki sentetik testte tek değişken
    oynatılarak ölçülür."""
    r = codelaw.report()
    assert r["tsx_line_anchor_taban"] == codelaw.TSX_CAPA_TABANI
    assert len(r["tsx_line_anchors"]) <= r["tsx_line_anchor_taban"]
    assert r["tsx_line_anchor_nuks"] is False
    assert isinstance(r["tsx_line_anchor_unresolved"], list)


def test_TSX_NUKSU_report_OKUNU_DUSURUR(tmp_path, monkeypatch):
    """ÇİVİNİN ASIL ÖLÇÜMÜ: aynı ağaç, tek değişen taban. Taban 1'ken (borç kayıtlı) `ok` yeşil,
    taban 0'ken (aynı çapa artık NÜKS) `ok` kırmızı. Sayıyı rapora yazıp `ok`a bağlamamak,
    çırçırı çivi değil süs yapardı.

    TEK DEĞİŞKENLİ DENEY İÇİN `stale_claims` YALITILIR: o terim sentetik bir ağaçta HER ZAMAN
    doludur (depo sabitlerindeki beyanlar boş ağaçta doğrulanamaz), yani yalıtılmasaydı `ok`
    ikisinde de False çıkar ve deney tsx hakkında hiçbir şey ölçmezdi."""
    codelaw.UNSCANNED.clear()
    monkeypatch.setattr(codelaw, "stale_claims", lambda *a, **k: [])
    _sentetik_agac(tmp_path, '// sentetik_hedef.py:999\n')
    monkeypatch.setattr(codelaw, "TSX_CAPA_TABANI", 1)
    r = codelaw.report(str(tmp_path), tsx_kok=str(tmp_path))
    assert [c["neden"] for c in r["tsx_line_anchors"]] == ["menzil_disi"], r["tsx_line_anchors"]
    assert r["tsx_line_anchor_nuks"] is False and r["ok"] is True, r
    monkeypatch.setattr(codelaw, "TSX_CAPA_TABANI", 0)
    r = codelaw.report(str(tmp_path), tsx_kok=str(tmp_path))
    assert r["tsx_line_anchor_nuks"] is True and r["ok"] is False, r


def test_report_SENTETIK_KOKTE_TSX_ALANINI_UYDURMAZ(tmp_path):
    """UYDURMA YASAĞI: sentetik bir `root` ile çağrıldığında deponun `ui/src`i ÖLÇÜLMEZ (testin
    kendi ağacını ölçmesi bozulurdu) — ölçülmeyen alan `None`dır, boş liste DEĞİL. Boş liste
    "baktım, temiz" derdi; doğru cevap "bakmadım"."""
    r = codelaw.report(str(tmp_path))
    assert r["tsx_line_anchors"] is None
    assert r["tsx_line_anchor_nuks"] is None
    assert r["tsx_line_anchor_unresolved"] is None
