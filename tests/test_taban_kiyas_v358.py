"""EDG-2026-067 TABAN-KIYASI ÖLÇÜM KODU — ÇİVİLER (v358, 2026-09-01).

NE ÖLÇÜLÜYOR. Kart `research/cards/EDG-2026-067-hindsight-faz1-bgem3-recall.yaml`
Hindsight recall'unu MİNİMAL TABAN ÇİZGİye (sqlite-vec + kendi şemamız) karşı koyar.
Bu dosya o kıyasın İKİ betiğini çivi altına alır:

  * `research/olcumler/edg067_hindsight_faz1/taban_indeks.py` — korpus → chunk → bge-m3 ONNX
    gömme → sqlite-vec indeksi,
  * `research/olcumler/edg067_hindsight_faz1/kiyas_kos.py`    — donuk soru kümesiyle iki kolu
    sorgular, mekanik hakemle sayar, rapor üretir.

ÖLÇÜM KODU DA KODDUR VE YANLIŞ SAYABİLİR. Bu dosyadaki hiçbir çivi ürün davranışına dokunmaz;
hepsi ÖLÇÜM ARACININ kendi bütünlüğünü ölçer — deponun "yeşil ama yanlış" sınıfının ölçüm
tarafındaki karşılığı. Kıyasın hükmü (eşik geçti/kaldı) BURADA YOKTUR ve olmamalıdır: hüküm
Rol-1'in, kartın eşikleriyle.

GERÇEK MODEL VE GERÇEK AĞ YOKTUR. `onnxruntime`/`tokenizers`/`sqlite_vec` bu ağaçta kurulu
değildir (ve yerel `sqlite3` uzantı yüklemeyi hiç desteklemiyor — ölçüldü 2026-09-01). Bu
yüzden iki betik de o üç paketi TEMBEL import eder; buradaki §F1 çivisi tembelliğin geri
sızmasını yasaklar — sızarsa bu dosyanın TAMAMI toplama anında ölür ve "çivi yok" ile "çivi
yeşil" ayırt edilemez hâle gelir.

DONUK ARTEFAKT ÇAPASI. `sorular.yaml` kart gereği DONDURULMUŞTUR (2026-09-01) ve blob-sha'sı
kartın `olcum` bölümüne işlenir. §C1 dosyanın içerik-sha'sını çivi altına alır: EDG-059 dersi
(çalışma ağacına bağlanan girdi sessizce ölür) burada içerik-adresli çapayla kapatılır.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import struct
import sys

import pytest

from tests.conftest import betikten_modul_yukle

KOK = pathlib.Path(__file__).resolve().parent.parent
OLCUM = KOK / "research" / "olcumler" / "edg067_hindsight_faz1"
SORULAR = OLCUM / "sorular.yaml"

#: DONUK soru kümesinin içerik çapası. Kart `olcum` bölümüne blob-sha ile işlenir; buradaki iki
#: sayı da DOSYADAN ölçüldü (2026-09-01, N=36), UYDURULMADI. Dosya değişirse kıyas geçersizdir
#: (kill maddesi: "soru kümesi blob-donuk değilken koşulan kıyas geçersiz") — o yüzden bu çivi
#: "testi güncelle" değil "yeni kart aç" der.
SORULAR_SHA256 = "cf1c39bb054c4be686c2fcf339742bb36aad714d5eeeec8c8d2a6bf9584e51f4"
SORULAR_GIT_BLOB = "89cd1e0ce3ba1e02abf9fcff07057c9ac0e79594"


@pytest.fixture(scope="module")
def taban():
    """`taban_indeks.py` — KAYNAKTAN derlenmiş (bayat bytecode dersi, v334)."""
    return betikten_modul_yukle(OLCUM / "taban_indeks.py", "edg067_taban_indeks_v358")


@pytest.fixture(scope="module")
def kiyas():
    """`kiyas_kos.py` — KAYNAKTAN derlenmiş."""
    return betikten_modul_yukle(OLCUM / "kiyas_kos.py", "edg067_kiyas_kos_v358")


# =================================================================================================
# §A — CHUNK'LAMA: sınırlar, örtüşme, biçim ayrımı
# =================================================================================================
def test_a1_baslik_sinirlari_1_2_3_boluyor_4_bolmuyor(taban):
    """`#`/`##`/`###` bölüm sınırıdır; `####` DEĞİLDİR — kart korpusunda `####` 74 kez geçer
    (ROADMAP.md, ölçüldü) ve onları da bölmek her maddeyi bağlamsız bırakırdı."""
    metin = "önsöz\n\n# A\nx\n## B\ny\n#### C\nz\n### D\nw"
    bolumler = taban.bolumlere_ayir(metin)
    assert [b for b, _ in bolumler] == ["", "A", "B", "D"], bolumler
    # `#### C` KENDİ bölümünü açmaz, `## B`nin gövdesinde kalır.
    govde_b = dict((b, g) for b, g in bolumler)["B"]
    assert "#### C" in govde_b and "z" in govde_b, govde_b


def test_a2_baslik_satiri_govdenin_ICINDE_kalir(taban):
    """Başlık metni gövdeden ATILMAZ. Hakem kuralı (b) dönen sonucun METNİNDE bölüm başlığını
    arar; başlık gövdeden düşerse taban kolu o kriteri hiçbir zaman geçemezdi."""
    bolumler = taban.bolumlere_ayir("## Bölüm Başlığı\ngövde")
    assert bolumler == [("Bölüm Başlığı", "## Bölüm Başlığı\ngövde")], bolumler


def test_a3_kod_citindeki_diyez_baslik_SAYILMAZ(taban):
    """Çit içindeki `# ...` bir kabuk yorumudur, markdown başlığı değil. Ayrımı yapmayan bir
    bölücü kod bloklarının ortasından keser ve sahte bölüm başlıkları uydurur."""
    metin = "```bash\n# sahte baslik\nls -la\n```\n# gerçek\ngövde"
    bolumler = taban.bolumlere_ayir(metin)
    assert [b for b, _ in bolumler] == ["", "gerçek"], bolumler
    assert "# sahte baslik" in bolumler[0][1]


def test_a4_bassiz_metin_TEK_bolum(taban):
    metin = "başlıksız kısa dosya\nikinci satır"
    assert taban.bolumlere_ayir(metin) == [("", metin)]


def test_a5_bos_metin_HIC_bolum_uretmez(taban):
    assert taban.bolumlere_ayir("") == []
    assert taban.bolumlere_ayir("   \n\n  ") == []


def test_a6_kayan_pencere_ortusme_ve_son_sinir(taban):
    """1.500 karakter / 200 örtüşme. İKİ sözleşme birden: adım 1.300 OLMALI ve SON pencere
    metnin SONUNDA bitmeli (bitmezse kuyruk sessizce indekslenmez)."""
    metin = "".join(chr(97 + i % 26) for i in range(3000))
    parcalar = taban.kayan_pencere(metin, 1500, 200)
    assert len(parcalar) == 3, [len(p) for p in parcalar]
    assert parcalar[0] == metin[0:1500]
    assert parcalar[1] == metin[1300:2800]
    assert parcalar[2] == metin[2600:3000]
    assert metin.endswith(parcalar[-1]), "son pencere metnin sonuna DEĞMİYOR — kuyruk kayboldu"


def test_a7_kisa_bolum_bolunmez(taban):
    metin = "a" * 1500
    assert taban.kayan_pencere(metin, 1500, 200) == [metin]


def test_a8_ortusmeden_KISA_alinti_en_az_bir_pencerede_BUTUN_kalir(taban):
    """POZİTİF KONTROL — örtüşmenin VARLIK SEBEBİ. `sorular.yaml`daki en uzun `dogrulama`
    alıntısı 95 karakterdir (ölçüldü); 200 karakterlik örtüşme, sınırı kesen her alıntının
    komşu pencerede BÜTÜN kalmasını garanti eder. Bu çivi kırılırsa hakem kuralı (b) taban
    kolunda ölçüm hatasıyla düşer — model yüzünden değil."""
    igne = "X" * 95
    metin = "a" * 1450 + igne + "b" * (3000 - 1450 - 95)
    parcalar = taban.kayan_pencere(metin, 1500, 200)
    assert any(igne in p for p in parcalar), "sınırı kesen alıntı HİÇBİR pencerede bütün değil"
    assert igne not in parcalar[0], "kurulum bozuk: alıntı ilk pencereyi hiç kesmiyor"


@pytest.mark.parametrize("uzunluk", [1499, 1500, 1501, 1600, 2799, 2800, 2801, 2850, 3000, 4200])
def test_a6b_pencereler_metni_BOSLUKSUZ_ORTUYOR(taban, uzunluk):
    """§A6'NIN KÖR NOKTASI (ölçüldü 2026-09-01, mutasyon M25). Tek uzunlukla kurulan çivi,
    kuyruğu 100 karakter erken kesen bir mutasyonda HAYATTA KALDI: 3.000 karakterlik metinde
    o hata görünmüyordu. Kapsama SÖZLEŞME OLARAK çivilenir — pencere ofsetleri ve son
    pencerenin metnin SONUNDA bitmesi, birçok uzunlukta birden.

    Fazla pencere de ihlaldir: bir önceki pencere zaten sona değmişse yenisi üretilmemeli
    (aynı kuyruğu iki kez gömmek mesafe sıralamasını sessizce çarpıtır)."""
    metin = "".join(chr(97 + i % 26) for i in range(uzunluk))
    parcalar = taban.kayan_pencere(metin, 1500, 200)
    adim = 1500 - 200
    for i, parca in enumerate(parcalar):
        assert parca == metin[i * adim:i * adim + 1500], f"{i}. pencere ofseti kaymış"
        assert parca, "boş pencere üretildi"
    son_bas = (len(parcalar) - 1) * adim
    assert son_bas + len(parcalar[-1]) == uzunluk, (
        f"SON PENCERE METNİN SONUNA DEĞMİYOR: {son_bas + len(parcalar[-1])} != {uzunluk} — "
        f"kuyruk sessizce indekslenmiyor")
    if len(parcalar) >= 2:
        onceki_son = (len(parcalar) - 2) * adim + 1500
        assert onceki_son < uzunluk, "gereksiz fazladan pencere: önceki zaten sona değmişti"


def test_a9_ortusme_penceredem_kucuk_olmali(taban):
    with pytest.raises(ValueError):
        taban.kayan_pencere("abc", 100, 100)
    with pytest.raises(ValueError):
        taban.kayan_pencere("abc", 100, 200)


def test_a10_dokuman_taban_kesit_ekini_soyar(taban):
    """`manifest_uret.py` ROADMAP §7 kesitini `ROADMAP.md%237` document_id'siyle paketler
    (`%23` = `#`). Soru kümesi ise beklenen dosyayı `ROADMAP.md` diye yazar — 36 sorunun
    5'i (ölçüldü). Taban soyulmazsa o beş soru İKİ KOLDA DA sıfırlanırdı."""
    assert taban.dokuman_taban("ROADMAP.md%237") == "ROADMAP.md"
    assert taban.dokuman_taban("MERIDIAN_ENGINEERING_LOG.md") == "MERIDIAN_ENGINEERING_LOG.md"
    assert taban.dokuman_taban("research/cards/x.yaml") == "research/cards/x.yaml"


def test_a11_markdown_ayrimi_kesit_ekinden_SONRA_yapilir(taban):
    """`Path("ROADMAP.md%237").suffix` `.md%237`dir — ham uzantı bakışı kesitli belgeyi
    markdown SAYMAZ ve §7'yi tek bir 190 KB'lık bloğa çevirirdi."""
    assert taban.markdown_mi("ROADMAP.md%237") is True
    assert taban.markdown_mi("docs/KORUNUM-KOK-2026-08-07.md") is True
    assert taban.markdown_mi("research/cards/EDG-2026-067.yaml") is False


def test_a12_yaml_kart_baslik_kuralina_TABI_DEGIL(taban):
    """YAML'daki `# ...` satırı YORUMDUR. Kart dosyalarının başında 9 ardışık yorum satırı var
    (ölçüldü); markdown kuralı uygulanırsa her biri tek satırlık bir chunk olur ve TABAN KOLU
    kendi aleyhine zayıflar. Ölçümün yönü buna duyarlıdır: tabanı haksız zayıflatmak hükmü
    Hindsight lehine kaydırır."""
    metin = "# yorum bir\n# yorum iki\nanahtar: deger\n"
    parcalar = taban.chunkla("research/cards/x.yaml", metin, "deadbeef")
    assert len(parcalar) == 1, parcalar
    assert parcalar[0]["bolum_basligi"] == ""
    assert parcalar[0]["metin"] == metin


def test_a13_chunk_alanlari_ve_blob_tasiniyor(taban):
    parcalar = taban.chunkla("docs/A.md", "# B\ngövde", "cafe1234")
    assert len(parcalar) == 1
    p = parcalar[0]
    assert p["dosya_yolu"] == "docs/A.md"
    assert p["bolum_basligi"] == "B"
    assert p["blob_sha"] == "cafe1234"
    assert p["metin"] == "# B\ngövde"


def test_a14_bos_pencere_chunk_uretmez(taban):
    parcalar = taban.chunkla("docs/A.md", "# B\n\n\n", "x")
    assert all(p["metin"].strip() for p in parcalar), parcalar


def _paket_kur(tmp_path, dosyalar, head="abc123def"):
    """`manifest_uret.py` çıktısının minik ikizi: `korpus/` + `manifest.json`."""
    for yol, icerik in dosyalar.items():
        hedef = tmp_path / "korpus" / yol
        hedef.parent.mkdir(parents=True, exist_ok=True)
        hedef.write_bytes(icerik.encode("utf-8"))
    kayitlar = [{"yol": y, "blob": "blob-" + y,
                 "bayt": len(i.encode("utf-8"))} for y, i in dosyalar.items()]
    (tmp_path / "manifest.json").write_text(
        json.dumps({"head_commit": head, "dosyalar": kayitlar}), encoding="utf-8")
    return tmp_path


def test_a15_korpus_chunklari_manifesti_izler_ve_blob_tasir(taban, tmp_path):
    paket = _paket_kur(tmp_path, {"docs/A.md": "# B\ngövde",
                                  "research/cards/x.yaml": "# yorum\nanahtar: 1"})
    manifest, chunklar = taban.korpus_chunklari(paket)
    assert manifest["head_commit"] == "abc123def"
    assert {c["dosya_yolu"] for c in chunklar} == {"docs/A.md", "research/cards/x.yaml"}
    assert all(c["blob_sha"] == "blob-" + c["dosya_yolu"] for c in chunklar)


def test_a16_korpus_BAYT_AYRISMASI_yakalanir(taban, tmp_path):
    """Kart kill maddesi: "taban çizgi AYNI soru kümesi + AYNI korpusla koşmazsa kıyas
    geçersiz". Hindsight'a giden paket ile taban paketi ayrışırsa kıyas sessizce elmayla
    armudu karşılaştırır — manifest bayt sayısı bunu ÖLÇER."""
    paket = _paket_kur(tmp_path, {"docs/A.md": "# B\ngövde"})
    (paket / "korpus" / "docs" / "A.md").write_text("# B\ngövde DEĞİŞTİ", encoding="utf-8")
    with pytest.raises(ValueError, match="AYRIŞTI"):
        taban.korpus_chunklari(paket)


def test_a17_manifestte_var_diskte_YOK_hatasi(taban, tmp_path):
    paket = _paket_kur(tmp_path, {"docs/A.md": "# B\ngövde"})
    (paket / "korpus" / "docs" / "A.md").unlink()
    with pytest.raises(FileNotFoundError):
        taban.korpus_chunklari(paket)


def test_a18_head_commitsiz_manifest_REDDEDILIR(taban, tmp_path):
    """Provenanssız korpus kıyasa giremez: hangi HEAD'den çıktığı ölçülemeyen bir paket,
    "AYNI korpus" iddiasını taşıyamaz."""
    (tmp_path / "manifest.json").write_text(
        json.dumps({"dosyalar": [{"yol": "a", "blob": "b", "bayt": 1}]}), encoding="utf-8")
    with pytest.raises(ValueError, match="head_commit"):
        taban.manifest_oku(tmp_path)


def test_a19_eksik_alanli_manifest_kaydi_REDDEDILIR(taban, tmp_path):
    (tmp_path / "manifest.json").write_text(
        json.dumps({"head_commit": "x", "dosyalar": [{"yol": "a"}]}), encoding="utf-8")
    with pytest.raises(ValueError, match="blob|bayt"):
        taban.manifest_oku(tmp_path)


# =================================================================================================
# §B — HAKEM: (a) dosya-isabet ve (b) dosya+bölüm-isabet ayrımı
# =================================================================================================
def _beklenen(dosya="docs/A.md", bolum="§2 Ölçüm", dogrulama="tam bu cümle"):
    return {"dosya": dosya, "bolum": bolum, "dogrulama": dogrulama}


def test_b1_dogru_dosya_YANLIS_pasaj_yalniz_a_kriterini_gecer(kiyas):
    """(a) ile (b)'nin AYRIŞTIĞI hâl. Hindsight damıtılmış bellek döndürdüğünde alıntı birebir
    geçmeyebilir; iki sayım da rapora yazılır ve ana metrik (b)'dir."""
    sonuclar = [{"dosya": "docs/A.md", "metin": "başka bir paragraf"}]
    h = kiyas.hakem(sonuclar, _beklenen())
    assert h["dosya_isabet"] is True
    assert h["bolum_isabet"] is False


def test_b2_dogrulama_alintisi_b_kriterini_gecirir(kiyas):
    sonuclar = [{"dosya": "docs/A.md", "metin": "önce ... TAM BU CÜMLE ... sonra"}]
    h = kiyas.hakem(sonuclar, _beklenen())
    assert (h["dosya_isabet"], h["bolum_isabet"]) == (True, True)


def test_b3_bolum_basligi_da_b_kriterini_gecirir(kiyas):
    """(b) bir VEYA'dır: alıntı YA DA bölüm başlığı."""
    sonuclar = [{"dosya": "docs/A.md", "metin": "## §2 Ölçüm\nbambaşka gövde"}]
    h = kiyas.hakem(sonuclar, _beklenen())
    assert (h["dosya_isabet"], h["bolum_isabet"]) == (True, True)


def test_b4_normalizasyon_bosluk_dizisi_satirbasi_ve_casefold(kiyas):
    """Boşluk dizileri TEK boşluğa iner, `\\n` boşluk sayılır, karşılaştırma casefold'dur.
    Üç dönüşümün üçü de gerekli: markdown sarması alıntıyı satır sonuna böler."""
    sonuclar = [{"dosya": "docs/A.md", "metin": "... Tam   Bu\nCümle ..."}]
    h = kiyas.hakem(sonuclar, _beklenen())
    assert h["bolum_isabet"] is True, "normalizasyon üç dönüşümden birini yapmıyor"


def test_b5_yanlis_dosya_iki_kriteri_de_dusurur(kiyas):
    """Alıntı GEÇSE BİLE dosya yanlışsa (b) düşer — (b), (a)'yı İÇERİR."""
    sonuclar = [{"dosya": "docs/B.md", "metin": "tam bu cümle"}]
    h = kiyas.hakem(sonuclar, _beklenen())
    assert (h["dosya_isabet"], h["bolum_isabet"]) == (False, False)


def test_b6_yalniz_ILK_UC_sonuc_sayilir(kiyas):
    """isabet@3: dördüncü sonuç sayılmaz."""
    sonuclar = [{"dosya": "docs/Z.md", "metin": ""} for _ in range(3)]
    sonuclar.append({"dosya": "docs/A.md", "metin": "tam bu cümle"})
    h = kiyas.hakem(sonuclar, _beklenen())
    assert (h["dosya_isabet"], h["bolum_isabet"]) == (False, False)
    assert h["ilk3_dosyalar"] == ["docs/Z.md"] * 3


def test_b7_b_kriteri_ilk3_ICINDE_dosya_esleyen_HERHANGI_sonuctan_gecebilir(kiyas):
    """Aynı dosyadan iki chunk dönerse ilki alıntıyı taşımıyor diye (b) düşmez."""
    sonuclar = [{"dosya": "docs/A.md", "metin": "ilgisiz"},
                {"dosya": "docs/A.md", "metin": "tam bu cümle burada"}]
    h = kiyas.hakem(sonuclar, _beklenen())
    assert h["bolum_isabet"] is True


def test_b8_kesitli_document_id_beklenen_dosyayla_eslesir(kiyas):
    sonuclar = [{"dosya": "ROADMAP.md%237", "metin": "§7 KARAR GÜNLÜĞÜ"}]
    h = kiyas.hakem(sonuclar, _beklenen(dosya="ROADMAP.md", bolum="§7 KARAR GÜNLÜĞÜ"))
    assert (h["dosya_isabet"], h["bolum_isabet"]) == (True, True)


def test_b9_okunamayan_document_id_ISABETSIZLIK_DEGIL_olculemedi(kiyas):
    """UYDURMA YASAĞI. Şemadan document_id çıkarılamayan sonuç "ıskaladı" SAYILMAZ; ayrı
    sayaçta durur. İkisi karışırsa "%0 isabet" ile "şemayı okuyamadım" aynı görünür — ve kartın
    hükmü yanlış tarafa düşer."""
    sonuclar = [{"dosya": None, "metin": "tam bu cümle"}]
    h = kiyas.hakem(sonuclar, _beklenen())
    assert (h["dosya_isabet"], h["bolum_isabet"]) == (False, False)
    assert h["okunamayan"] == 1


def test_b10_bos_sonuc_listesi_cokmez(kiyas):
    h = kiyas.hakem([], _beklenen())
    assert (h["dosya_isabet"], h["bolum_isabet"], h["ilk3_dosyalar"]) == (False, False, [])


def test_b11_normalize_sozlesmesi(kiyas):
    assert kiyas.normalize("  A   B\n\tC  ") == "a b c"
    assert kiyas.normalize("İ") == "İ".casefold()
    assert kiyas.normalize("") == ""


# =================================================================================================
# §C — DONUK SORU KÜMESİ
# =================================================================================================
def test_c1_sorular_yaml_ICERIK_CAPASI_degismedi():
    """Kart kill maddesi: "soru kümesi blob-donuk değilken koşulan kıyas geçersiz". Çapa
    İÇERİKTEDİR (EDG-059 dersi), çalışma ağacı yolunda değil. git blob sha1'i de burada
    hashlib ile hesaplanır — ajan git koşmaz."""
    ham = SORULAR.read_bytes()
    assert hashlib.sha256(ham).hexdigest() == SORULAR_SHA256, (
        "DONUK soru kümesi DEĞİŞMİŞ. Bu bir test arızası değildir: kart gereği değişiklik = "
        "YENİ KART. Eski kart 'kaldı' diye kapatılır, sha buraya YENİ kartla birlikte yazılır.")
    blob = hashlib.sha1(b"blob %d\x00" % len(ham) + ham).hexdigest()
    assert blob == SORULAR_GIT_BLOB, f"git blob sha1 ayrıştı: {blob}"


def test_c2_donuk_kume_semaya_ve_kart_sartlarina_uyuyor(kiyas):
    """Kart: N>=30, dil tr/en, sınıf arsiv/karar/recete. Okuyucu ŞEMAYI da doğrular."""
    sorular = kiyas.sorulari_oku(SORULAR)
    assert len(sorular) == 36
    assert len({s["id"] for s in sorular}) == 36, "id çakışması"
    assert {s["dil"] for s in sorular} == {"tr", "en"}
    assert {s["sinif"] for s in sorular} <= {"arsiv", "karar", "recete"}
    tr = [s for s in sorular if s["dil"] == "tr"]
    assert len(tr) == 29, f"tr alt-kümesi 29 değil: {len(tr)}"


def test_c3_eksik_alan_SESSIZCE_gecmez(kiyas, tmp_path):
    """Yasa 4 sınıfı: eksik `dogrulama` sessizce boş dizgeye düşerse o soru (b) kriterini
    HİÇBİR ZAMAN geçemez ve kol haksız yere kaybeder."""
    yol = tmp_path / "eksik.yaml"
    yol.write_text(
        "sorular:\n"
        "  - id: S-900\n    dil: tr\n    soru: x\n    sinif: arsiv\n"
        "    beklenen:\n      dosya: a.md\n      bolum: b\n", encoding="utf-8")
    with pytest.raises(ValueError, match="dogrulama"):
        kiyas.sorulari_oku(yol)


def test_c4_id_cakismasi_reddedilir(kiyas, tmp_path):
    yol = tmp_path / "cakisan.yaml"
    govde = ("    dil: tr\n    soru: x\n    sinif: arsiv\n"
             "    beklenen:\n      dosya: a.md\n      bolum: b\n      dogrulama: c\n")
    yol.write_text("sorular:\n  - id: S-1\n" + govde + "  - id: S-1\n" + govde, encoding="utf-8")
    with pytest.raises(ValueError, match="S-1"):
        kiyas.sorulari_oku(yol)


def test_c5_bos_kume_reddedilir(kiyas, tmp_path):
    yol = tmp_path / "bos.yaml"
    yol.write_text("sorular: []\n", encoding="utf-8")
    with pytest.raises(ValueError):
        kiyas.sorulari_oku(yol)


# =================================================================================================
# §D — RAPOR: sayım, yüzdelik, ölçülemeyenin adı
# =================================================================================================
def test_d1_yuzdelik_bos_listede_None(kiyas):
    """UYDURMA YASAĞI: ölçüm yoksa 0 değil None."""
    assert kiyas.yuzdelik([], 50) is None
    assert kiyas.yuzdelik([12.0], 95) == 12.0


def test_d2_yuzdelik_ara_deger(kiyas):
    assert kiyas.yuzdelik([1, 2, 3, 4], 50) == pytest.approx(2.5)
    assert kiyas.yuzdelik([1, 2, 3, 4], 0) == 1
    assert kiyas.yuzdelik([1, 2, 3, 4], 100) == 4


def _satir(sid, kol, dil, sinif, dosya=True, bolum=True, gecikme=10.0):
    return {"id": sid, "kol": kol, "dil": dil, "sinif": sinif,
            "dosya_isabet": dosya, "bolum_isabet": bolum,
            "ilk3_dosyalar": ["docs/A.md"], "gecikme_ms": gecikme, "okunamayan": 0}


def test_d3_alt_kume_orani_tr_ve_en_AYRI_sayilir(kiyas):
    satirlar = [_satir("S-1", "taban", "tr", "arsiv", bolum=True),
                _satir("S-2", "taban", "tr", "arsiv", bolum=False),
                _satir("S-3", "taban", "en", "karar", bolum=True)]
    ozet = kiyas.kol_ozeti(satirlar)
    assert ozet["genel"]["n"] == 3
    assert ozet["genel"]["bolum_isabet_3"] == pytest.approx(2 / 3)
    assert ozet["tr"]["n"] == 2 and ozet["tr"]["bolum_isabet_3"] == pytest.approx(0.5)
    assert ozet["en"]["n"] == 1 and ozet["en"]["bolum_isabet_3"] == 1.0


def test_d4_bos_alt_kume_orani_None(kiyas):
    ozet = kiyas.kol_ozeti([_satir("S-1", "taban", "tr", "arsiv")])
    assert ozet["en"]["n"] == 0
    assert ozet["en"]["bolum_isabet_3"] is None, "boş alt-kümede oran 0 DEĞİL, ölçülemedi"


def test_d5_rapor_iki_kolu_ve_soru_satirlarini_tasiyor(kiyas):
    satirlar = [_satir("S-1", "taban", "tr", "arsiv"),
                _satir("S-1", "hindsight", "tr", "arsiv", bolum=False)]
    rapor = kiyas.rapor_kur(satirlar, kunye={"head_commit": "abc", "chunk_sayisi": 7,
                                             "kurulum_suresi_s": 12.5})
    assert set(rapor["kollar"]) == {"taban", "hindsight"}
    assert len(rapor["sorular"]) == 2
    assert rapor["korpus"]["kurulum_suresi_s"] == 12.5
    assert rapor["korpus"]["head_commit"] == "abc"


def test_d6_olculemeyen_kurulum_suresi_None_ve_NEDEN(kiyas):
    """Künyede süre yoksa rapor 0 yazmaz; None + neden yazar."""
    rapor = kiyas.rapor_kur([_satir("S-1", "taban", "tr", "arsiv")], kunye={})
    assert rapor["korpus"]["kurulum_suresi_s"] is None
    assert rapor["korpus"]["kurulum_suresi_s_neden"], "None'ın NEDENİ yazılmamış"


def test_d7_rapor_HUKUM_YAZMAZ(kiyas):
    """Eşik hükmü Rol-1'indir. Rapor ne "GEÇTİ" der ne "KALDI" — ne JSON'da ne markdown'da."""
    satirlar = [_satir("S-1", "taban", "tr", "arsiv"),
                _satir("S-1", "hindsight", "tr", "arsiv")]
    rapor = kiyas.rapor_kur(satirlar, kunye={})
    metin = (json.dumps(rapor, ensure_ascii=False) + kiyas.rapor_markdown(rapor)).casefold()
    for yasak in ("geçti", "kaldı", "eşiği aş", "başarılı", "hüküm:"):
        assert yasak not in metin, f"rapor HÜKÜM veriyor: {yasak!r}"


def test_d8_markdown_raporu_iki_sayimi_da_gosteriyor(kiyas):
    """Bedel yasası kardeşi: (b) ana metrik diye (a) sütunu SİLİNMEZ."""
    satirlar = [_satir("S-1", "taban", "tr", "arsiv"),
                _satir("S-1", "hindsight", "tr", "arsiv")]
    md = kiyas.rapor_markdown(kiyas.rapor_kur(satirlar, kunye={}))
    assert "dosya" in md.casefold() and "bölüm" in md.casefold()
    assert "taban" in md.casefold() and "hindsight" in md.casefold()
    assert "S-1" in md


# =================================================================================================
# §E — SIR SIZINTISI: anahtar hiçbir çıktıya düşmez
# =================================================================================================
def test_e1_sizinti_denetcisi_anahtari_YAKALAR(kiyas):
    with pytest.raises(RuntimeError, match="ANAHTAR"):
        kiyas.sizinti_denetle(["gövde ... hs_abc123 ... son"], "hs_abc123")


def test_e2_sizinti_denetcisi_temiz_metne_dokunmaz(kiyas):
    kiyas.sizinti_denetle(["temiz gövde"], "hs_abc123")


def test_e3_bos_anahtar_denetimi_HER_METNI_suclu_saymaz(kiyas):
    """`"" in metin` her zaman True'dur — boş sır ile denetim yapmak kapıyı sahte kırmızıya
    boğardı; boş/None sır DENETLENEMEZ, sessizce yeşil de sayılmaz."""
    kiyas.sizinti_denetle(["herhangi bir metin"], "")
    kiyas.sizinti_denetle(["herhangi bir metin"], None)


def test_e4_hindsight_kolu_anahtari_govdeye_YAZMAZ(kiyas, monkeypatch):
    """Anahtar YALNIZ Authorization başlığındadır; URL'de, gövdede, dönen kayıtta değil."""
    gorulen = {}

    class SahteCevap:
        status = 200

        def read(self):
            return json.dumps({"items": []}).encode()

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def sahte_urlopen(req, timeout=None):
        gorulen["url"] = req.full_url
        gorulen["govde"] = (req.data or b"").decode()
        gorulen["basliklar"] = dict(req.headers)
        return SahteCevap()

    monkeypatch.setattr(kiyas.urllib.request, "urlopen", sahte_urlopen)
    kiyas.hindsight_cagir("http://127.0.0.1:8888/v1/default", "GİZLİ-ANAHTAR",
                          "meridian-arsiv", "bir soru", 3)
    assert "GİZLİ-ANAHTAR" not in gorulen["url"]
    assert "GİZLİ-ANAHTAR" not in gorulen["govde"]
    assert any("GİZLİ-ANAHTAR" in str(v) for v in gorulen["basliklar"].values()), \
        "anahtar Authorization başlığında da YOK — çağrı yetkisiz giderdi"


def test_e5_anahtar_dosyadan_okunur_ve_kirpilir(kiyas, tmp_path):
    yol = tmp_path / "key"
    yol.write_text("  hs_secret_42\n", encoding="utf-8")
    assert kiyas.anahtar_oku(yol) == "hs_secret_42"


def test_e6_bos_anahtar_dosyasi_HATA(kiyas, tmp_path):
    yol = tmp_path / "key"
    yol.write_text("\n\n", encoding="utf-8")
    with pytest.raises(ValueError):
        kiyas.anahtar_oku(yol)


def test_e7_supheli_kisa_anahtar_REDDEDILIR(kiyas, tmp_path):
    """ÖLÇÜLMÜŞ VAKA (2026-09-01, bu çivinin ilk koşumu): tek harfli bir anahtarla sızıntı
    taraması RAPORUN KENDİSİNİ suçlu buldu (`"k" in "kart"`). İki arıza birden: kırpılmış
    anahtar dosyası sessizce kabul edilir, VE tarama sahte kırmızıya boğulur. Reçete kısa
    sırrı KAPIDA reddetmektir — taramayı gevşetmek değil (gevşetseydik gerçek bir sızıntıyı
    da yutardık)."""
    yol = tmp_path / "key"
    yol.write_text("k\n", encoding="utf-8")
    with pytest.raises(ValueError, match="KISA"):
        kiyas.anahtar_oku(yol)


# =================================================================================================
# §F — GÖMME KATMANI: tembel import, havuzlama, normalizasyon
# =================================================================================================
def test_f1_agir_paketler_MODUL_DUZEYINDE_import_EDILMIYOR(taban, kiyas):
    """`onnxruntime`/`tokenizers`/`sqlite_vec` bu ağaçta KURULU DEĞİL. Modül düzeyine çıkarlarsa
    bu dosyanın tamamı TOPLAMA anında ölür — ve "çivi yok" ile "çivi yeşil" ayırt edilemez.
    Ayrıca A1'de yalnız `--kollar hindsight` koşan bir tur model dizini olmadan da koşabilmeli."""
    import ast
    for mod_yol in (OLCUM / "taban_indeks.py", OLCUM / "kiyas_kos.py"):
        agac = ast.parse(mod_yol.read_text(encoding="utf-8"))
        for dugum in agac.body:                       # YALNIZ modül gövdesi (tembel olan içeride)
            adlar = []
            if isinstance(dugum, ast.Import):
                adlar = [a.name.split(".")[0] for a in dugum.names]
            elif isinstance(dugum, ast.ImportFrom) and dugum.level == 0:
                adlar = [(dugum.module or "").split(".")[0]]
            yasak = {"onnxruntime", "tokenizers", "sqlite_vec", "numpy", "meridian"}
            carpisan = set(adlar) & yasak
            assert not carpisan, f"{mod_yol.name} modül düzeyinde {carpisan} import ediyor"


def test_f2_cls_havuzlama_ILK_TOKENI_alir(taban):
    np = pytest.importorskip("numpy")
    son_gizli = np.arange(2 * 3 * 4, dtype="float32").reshape(2, 3, 4)
    havuz = taban.cls_havuzla(son_gizli)
    assert havuz.shape == (2, 4)
    assert list(havuz[0]) == [0, 1, 2, 3]
    assert list(havuz[1]) == [12, 13, 14, 15], "cls DEĞİL: ortalama/son-token havuzlaması yapılmış"


def test_f3_l2_normalize_birim_uzunluk(taban):
    np = pytest.importorskip("numpy")
    v = np.array([[3.0, 4.0], [0.0, 0.0]], dtype="float32")
    n = taban.l2_normalize(v)
    assert n[0].tolist() == pytest.approx([0.6, 0.8])
    assert all(abs(x) < 1e-6 for x in n[1].tolist()), "sıfır vektör NaN üretti (0'a bölme)"


def test_f4_boyut_uyusmazligi_SESSIZ_gecmez(taban):
    """Kart kill maddesi: "embedding boyutu 1024 doğrulanmadan başlayan ingest geçersiz".
    Tabanda da aynı disiplin — 1024 dışındaki bir çıktı vec0 şemasına sessizce sığmaz."""
    np = pytest.importorskip("numpy")
    with pytest.raises(ValueError, match="1024"):
        taban.boyut_dogrula(np.zeros((2, 768), dtype="float32"), 1024)
    taban.boyut_dogrula(np.zeros((2, 1024), dtype="float32"), 1024)


# =================================================================================================
# §G — SQLITE-VEC KATMANI
# =================================================================================================
def test_g1_paketle_kucuk_endian_float32(taban):
    v = [1.0, -2.5, 0.0]
    assert taban.paketle(v) == struct.pack("<3f", *v)
    assert len(taban.paketle([0.0] * 1024)) == 4096


class _SahteImlec:
    def __init__(self, satirlar):
        self._satirlar = satirlar

    def fetchall(self):
        return self._satirlar


class _SahteDB:
    """SQL'i KAYDEDEN sahte bağlantı — sqlite-vec uzantısı bu ağaçta yüklenemiyor
    (yerel `sqlite3` `enable_load_extension`'ı hiç tanımıyor, ölçüldü 2026-09-01)."""

    def __init__(self, satirlar=()):
        self.cagrilar = []
        self._satirlar = list(satirlar)

    def execute(self, sql, param=()):
        self.cagrilar.append((sql, param))
        return _SahteImlec(self._satirlar)

    def executemany(self, sql, params):
        params = list(params)
        self.cagrilar.append((sql, params))
        return _SahteImlec([])

    def commit(self):
        self.cagrilar.append(("COMMIT", ()))


def test_g2_en_yakin_KNN_sorgusu_ve_k_baglanmasi(taban):
    db = _SahteDB([(1, "docs/A.md", "B", "gövde", "sha", 0.12)])
    sonuc = taban.en_yakin(db, [0.1] * 4, k=3)
    sql, param = db.cagrilar[-1]
    assert "match" in sql.casefold(), "vec0 KNN sorgusu MATCH kullanmıyor"
    assert "k = ?" in sql.casefold().replace("k=?", "k = ?"), f"k parametre olarak bağlanmamış: {sql}"
    assert param == (taban.paketle([0.1] * 4), 3)
    assert sonuc == [{"id": 1, "dosya": "docs/A.md", "bolum": "B",
                      "metin": "gövde", "blob_sha": "sha", "mesafe": 0.12}]


def test_g3_en_yakin_ORDER_BY_mesafe(taban):
    db = _SahteDB([])
    taban.en_yakin(db, [0.0] * 4, k=3)
    sql = db.cagrilar[-1][0].casefold()
    assert "order by" in sql and "distance" in sql


def test_g4_indeks_kur_chunk_ve_vektor_SATIR_SAYISI_esit(taban):
    db = _SahteDB([])
    gomucu = lambda metinler: [[0.0, 1.0] for _ in metinler]  # noqa: E731
    chunklar = [{"dosya_yolu": "a.md", "bolum_basligi": "B", "metin": f"m{i}",
                 "blob_sha": "s"} for i in range(5)]
    ist = taban.indeks_kur(db, chunklar, gomucu, boyut=2, yigin=2)
    assert ist["chunk_sayisi"] == 5
    yazilan = [c for c in db.cagrilar if isinstance(c[1], list)]
    chunk_satiri = sum(len(p) for s, p in yazilan if "INTO chunk(" in s)
    vec_satiri = sum(len(p) for s, p in yazilan if "chunk_vec" in s)
    assert chunk_satiri == vec_satiri == 5, (chunk_satiri, vec_satiri)


def test_g5_vec_baglan_UZANTI_DESTEGI_YOKKEN_acik_hata(taban, monkeypatch, tmp_path):
    """Yerel `sqlite3` uzantı yüklemeyi desteklemiyor. Hata mesajı bunu SÖYLEMELİ — "sqlite-vec
    kurulu değil" ile "bu Python uzantı yükleyemiyor" farklı arızalardır."""
    class _Baglanti:
        pass

    monkeypatch.setattr(taban.sqlite3, "connect", lambda *a, **k: _Baglanti())
    with pytest.raises(RuntimeError, match="enable_load_extension"):
        taban.vec_baglan(tmp_path / "x.sqlite")


def test_g6_sema_vec0_ve_metadata_tablosunu_kuruyor(taban):
    db = _SahteDB([])
    taban.sema_kur(db, boyut=1024)
    sql = " ".join(s for s, _ in db.cagrilar).casefold()
    assert "using vec0" in sql
    assert "float[1024]" in sql, "vec0 boyutu şemaya YAZILMAMIŞ"
    assert "create table" in sql and "chunk" in sql
    assert "kunye" in sql, "künye tablosu yok — kurulum süresi/head_commit nereye yazılacak?"


def test_g7_gomucu_EKSIK_vektor_dondurunce_duser(taban):
    """Sessiz hizalama kayması: gömücü n metne n'den az vektör döndürürse `zip` fazlasını
    ATAR ve chunk'lar YANLIŞ vektörlerle eşleşir. Sonuç düşük isabet olur ve sebebi görünmez."""
    db = _SahteDB([])
    chunklar = [{"dosya_yolu": "a.md", "bolum_basligi": "", "metin": f"m{i}",
                 "blob_sha": "s"} for i in range(3)]
    with pytest.raises(RuntimeError, match="vektör"):
        taban.indeks_kur(db, chunklar, lambda metinler: [[0.0, 1.0]], boyut=2, yigin=3)


def test_g8_yanlis_BOYUTLU_vektor_yazilmaz(taban):
    db = _SahteDB([])
    chunklar = [{"dosya_yolu": "a.md", "bolum_basligi": "", "metin": "m", "blob_sha": "s"}]
    with pytest.raises(ValueError, match="boyut"):
        taban.indeks_kur(db, chunklar, lambda m: [[0.0] * 3 for _ in m], boyut=2)


def test_g9_kunye_JSON_gidis_donusu(taban):
    """Künye, kurulum süresinin ve head_commit'in TEK KAYNAĞIdır (rapor onu buradan okur).
    Yazma ile okuma ayrışırsa rapor sessizce "ölçülemedi" der ve sebebi bulunamaz."""
    import sqlite3 as _s
    db = _s.connect(":memory:")
    db.execute("CREATE TABLE kunye(anahtar TEXT PRIMARY KEY, deger TEXT NOT NULL)")
    kayit = {"head_commit": "abc123", "kurulum_suresi_s": 12.5, "chunk_sayisi": 7,
             "model_dir": "/opt/hindsight/models/bge-m3/onnx/model.onnx"}
    taban.kunye_yaz(db, kayit)
    assert taban.kunye_oku(db) == kayit


# =================================================================================================
# §H — UÇTAN UCA: sahte gömücü + sahte ağ ile rapor üretimi
# =================================================================================================
def test_h1_uctan_uca_iki_kol_rapor_uretiyor(kiyas, tmp_path, monkeypatch):
    """Ops aracı dersi (2026-08-30): teslimden önce aracı OPERATÖRÜN koşacağı biçimde bir kez
    koş. Burada gerçek model/ağ yok ama BÜTÜN boru hattı koşar: soru okuma → iki kol → hakem
    → JSON + markdown yazımı."""
    sorular = tmp_path / "s.yaml"
    sorular.write_text(
        "sorular:\n"
        "  - id: S-1\n    dil: tr\n    soru: birinci soru\n    sinif: arsiv\n"
        "    beklenen:\n      dosya: docs/A.md\n      bolum: '§2'\n      dogrulama: alıntı bir\n"
        "  - id: S-2\n    dil: en\n    soru: second question\n    sinif: karar\n"
        "    beklenen:\n      dosya: ROADMAP.md\n      bolum: '§7'\n      dogrulama: quote two\n",
        encoding="utf-8")
    anahtar = tmp_path / "key"
    anahtar.write_text("hs_test_key\n", encoding="utf-8")
    rapor_dizin = tmp_path / "rapor"

    monkeypatch.setattr(kiyas, "taban_hazirla",
                        lambda db_yolu, model_dir, **k: ({"head_commit": "abc123",
                                                          "chunk_sayisi": 9,
                                                          "kurulum_suresi_s": 3.5}, None, None))
    monkeypatch.setattr(kiyas, "taban_sorgu",
                        lambda ortam, soru, k: [{"dosya": "docs/A.md", "metin": "alıntı bir"}])

    def sahte_hindsight(base, key, bank, soru, k, ek=None):
        assert key == "hs_test_key"
        return [{"document_id": "ROADMAP.md%237", "content": "quote two"}]

    monkeypatch.setattr(kiyas, "hindsight_cagir", sahte_hindsight)

    rc = kiyas.main(["--db", str(tmp_path / "x.sqlite"), "--sorular", str(sorular),
                     "--model-dir", str(tmp_path), "--base", "http://127.0.0.1:8888/v1/default",
                     "--key-file", str(anahtar), "--rapor-dizin", str(rapor_dizin)])
    assert rc == 0
    jsonlar = sorted(rapor_dizin.glob("*.json"))
    mdler = sorted(rapor_dizin.glob("*.md"))
    assert jsonlar and mdler, list(rapor_dizin.iterdir())
    rapor = json.loads(jsonlar[0].read_text(encoding="utf-8"))
    assert rapor["kollar"]["taban"]["tr"]["bolum_isabet_3"] == 1.0
    assert rapor["kollar"]["hindsight"]["en"]["bolum_isabet_3"] == 1.0
    assert rapor["kollar"]["taban"]["gecikme_ms"]["p50"] is not None
    metin = jsonlar[0].read_text(encoding="utf-8") + mdler[0].read_text(encoding="utf-8")
    assert "hs_test_key" not in metin, "ANAHTAR RAPORA SIZDI"


def test_h2_hindsight_semasi_HIC_okunamazsa_kosum_DUSER(kiyas, tmp_path, monkeypatch):
    """"%0 isabet" ile "şemayı okuyamadım" AYNI ŞEY DEĞİLDİR. Hiçbir sonuçtan document_id
    çıkarılamıyorsa betik sıfır rapor etmez — düşer ve `--sema-ornek` koşulmasını söyler."""
    sorular = tmp_path / "s.yaml"
    sorular.write_text(
        "sorular:\n"
        "  - id: S-1\n    dil: tr\n    soru: x\n    sinif: arsiv\n"
        "    beklenen:\n      dosya: docs/A.md\n      bolum: b\n      dogrulama: c\n",
        encoding="utf-8")
    anahtar = tmp_path / "key"
    anahtar.write_text("hs_test_key\n", encoding="utf-8")
    monkeypatch.setattr(kiyas, "hindsight_cagir",
                        lambda *a, **k: [{"bilinmeyen_alan": "?", "metin": "?"}])
    with pytest.raises(RuntimeError, match="sema-ornek"):
        kiyas.main(["--kollar", "hindsight", "--sorular", str(sorular),
                    "--base", "http://x/v1/default", "--key-file", str(anahtar),
                    "--rapor-dizin", str(tmp_path / "r")])


def test_h7_recall_DUSERSE_yarim_sayim_RAPOR_EDILMEZ(kiyas, tmp_path, monkeypatch):
    """Ağ arızası ISKALA DEĞİLDİR. Düşen bir çağrı sessizce "0 sonuç"a çevrilseydi kol haksız
    yere kaybeder ve rapor bunu göstermezdi — kartın hükmü yanlış tarafa düşerdi."""
    sorular = tmp_path / "s.yaml"
    sorular.write_text(
        "sorular:\n"
        "  - id: S-1\n    dil: tr\n    soru: x\n    sinif: arsiv\n"
        "    beklenen:\n      dosya: docs/A.md\n      bolum: b\n      dogrulama: c\n",
        encoding="utf-8")
    anahtar = tmp_path / "key"
    anahtar.write_text("hs_test_key\n", encoding="utf-8")
    rapor_dizin = tmp_path / "r"

    def patlayan(*a, **k):
        raise OSError("bağlantı reddedildi")

    monkeypatch.setattr(kiyas, "hindsight_cagir", patlayan)
    with pytest.raises(RuntimeError, match="YARIM"):
        kiyas.main(["--kollar", "hindsight", "--sorular", str(sorular),
                    "--base", "http://x/v1/default", "--key-file", str(anahtar),
                    "--rapor-dizin", str(rapor_dizin)])
    assert not list(rapor_dizin.glob("*.json")), "yarım koşumdan rapor YAZILMIŞ"


def test_h3_kimlik_ve_metin_cikarici_KULLANDIGI_YOLU_bildiriyor(kiyas):
    """Şema tahmin EDİLMEZ, ÖLÇÜLÜR: hangi alandan okunduğu rapora yazılır (uydurma yasağı).
    A1'de gerçek şema farklı çıkarsa rapor bunu ADIYLA gösterir."""
    deger, yol = kiyas.dokuman_kimligi_cikar({"document_id": "a.md"})
    assert (deger, yol) == ("a.md", "document_id")
    deger, yol = kiyas.dokuman_kimligi_cikar({"metadata": {"document_id": "b.md"}})
    assert (deger, yol) == ("b.md", "metadata.document_id")
    assert kiyas.dokuman_kimligi_cikar({"foo": 1}) == (None, None)
    assert kiyas.metin_cikar({"content": "gövde"}) == ("gövde", "content")
    assert kiyas.metin_cikar({"foo": 1}) == (None, None)


def test_h4_taban_kolu_MODEL_DIZINI_yokken_acik_hata(kiyas, tmp_path):
    """"koşamıyorum" ile "kırmızı" karışmasın: model dizini yoksa mesaj bunu söyler."""
    with pytest.raises((FileNotFoundError, RuntimeError), match="model"):
        kiyas.taban_hazirla(tmp_path / "yok.sqlite", tmp_path / "olmayan-model")


def test_h5_kollar_secimi_hindsight_iken_MODEL_ISTENMEZ(kiyas, tmp_path, monkeypatch):
    sorular = tmp_path / "s.yaml"
    sorular.write_text(
        "sorular:\n"
        "  - id: S-1\n    dil: tr\n    soru: x\n    sinif: arsiv\n"
        "    beklenen:\n      dosya: docs/A.md\n      bolum: b\n      dogrulama: c\n",
        encoding="utf-8")
    anahtar = tmp_path / "key"
    anahtar.write_text("hs_test_key\n", encoding="utf-8")

    def patlayan(*a, **k):
        raise AssertionError("hindsight kolunda taban indeksi hazırlanmamalı")

    monkeypatch.setattr(kiyas, "taban_hazirla", patlayan)
    monkeypatch.setattr(kiyas, "hindsight_cagir",
                        lambda *a, **k: [{"document_id": "docs/A.md", "content": "c"}])
    rc = kiyas.main(["--kollar", "hindsight", "--sorular", str(sorular),
                     "--base", "http://x/v1/default", "--key-file", str(anahtar),
                     "--rapor-dizin", str(tmp_path / "r")])
    assert rc == 0


def test_h6_betikler_pytest_disinda_kosmadan_ICE_AKTARILABILIYOR(taban, kiyas):
    """İkisi de `main()` yan etkisiz içe aktarılmalı: `__main__` bloğu yalnız doğrudan koşumda
    ateşler. Aksi hâlde bu dosyanın her toplanışı bir ölçüm koşumu başlatırdı."""
    assert callable(taban.main) and callable(kiyas.main)
    assert "edg067_taban_indeks_v358" not in sys.modules
    assert "edg067_kiyas_kos_v358" not in sys.modules
