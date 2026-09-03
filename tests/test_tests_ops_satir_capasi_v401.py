"""test_tests_ops_satir_capasi_v401.py — SATIR ÇAPASI YASASI, `tests/`+`ops/` DÜNYASI (TSK-119,
2026-09-03). `test_kovab_dilim_v382.py`nin `meridian/*.py` TEK-DÜNYASININ EŞİ.

NEDEN VAR — ÖLÇÜM (bugün, `_CAPA_DESENI` ile, muafiyet satırları hariç): `tests/`+`ops/` 76
`dosya.py:NNN` eşleşmesi taşıyordu / 30 dosyada. ROADMAP'in "59 satır / 28 dosya" sayısı
`63b64ab` commit mesajından (2026-09-03 10:51) devralınmıştı ve TSK-116/TSK-118 aynı gün eşzamanlı
`tests/*` dosyalarına dokunduğu için ESKİMİŞTİ — bu dosya sayıyı YENİDEN ÖLÇTÜ, 59'a GÜVENMEDİ.
`codelaw.report()["stale_line_anchors"]` bu kökleri (`_EK_CAPA_KOKLERI`) zaten SIFIR TOLERANSLA
tarıyordu (`ok`u etkiliyordu), ama v382'ninkine benzer, KAYNAK-METNİ okuyan ADANMIŞ bir çivi
YOKTU — `report()`in ölçtüğü "çürük mü" (menzil-dışı/boş/yorum) sorusundan AYRI bir soru: "hiç
BEYANSIZ mı" (v382'nin de sorduğu soru, `_capa_ihlalleri`nin özü).

76 eşleşme ÜÇ sınıfa ayrıldı (kesif notu, D1) — örneklerin biçimi burada BİLEREK `dosya-adı,
satır-numarası` gibi AYRIK yazılır, aksi hâlde bu dosyanın kendi metni kendi yasasını ihlal ederdi:
  (a) tarihsel/donmuş research çapası (`research/olcumler/<tarihli-dizin>/olcum.py`, satır 178
      gibi) → sembol mümkünse sembole (`_rampa_fn`/`kosum`), değilse `çapa-mezar-taşı` ile beyan
      (1 örnek, `test_provenance_v80.py` — 2026-07-22 tarihli, üretici bugün adıyla
      doğrulanamadı).
  (b) canlı `meridian/*.py`ye (ve iki durumda `tests/*.py`ye) şerh çapası → `dosya.py::sembol`
      (hedef `grep -n "def X\\|class X\\|^X ="` ve `meridian.codelaw._modul_adlari` İLE
      doğrulandı — aynı AST çekirdeği `capa_uyusmasi`nın kullandığı).
  (c) `_satir_no(...)` çalışma-zamanı ölçümü (`.sh` hedef) → `_CAPA_DESENI` `.py` hedef DIŞINDA
      hiçbir şeyi tanımadığı için ZATEN görünmez; dokunulmadı.
  (d) sentetik fikstür dizgesi (`tmp_path`e yazılan, `hedef.py`/`uydurma_modul.py` + uydurma satır
      numarası gibi) → `# çapa-sentetik: <gerekçe>` işareti (TEK KAYNAK:
      `codelaw._CAPA_SENTETIK_ISARETI`).
  (e) illüstratif örnek metni (yasağın KENDİSİNİ, dosya-adı artı satır-numarası biçimini,
      alıntılayan cümle) → cümle yeniden yazıldı, o biçim metinde KALMADI.

Tam dönüşüm listesi ve hedef-doğrulama komutları `.superpowers/sdd/2026-09-03-tsk119/report.md`de
(bu depoda git-izli DEĞİL, worktree salt-yerel rapor).

TEK KAYNAK (v384'ün v381'den ithal deseni, TSK-113): desen (`_satir_capasi_deseni`) ve mezar-taşı
muafiyeti (`_muafiyet`) `test_kovab_dilim_v382.py`den İTHAL edilir, buraya KOPYALANMAZ — kopya
daralırsa (v382'nin K1 dersi: `[0-9]{2,5}` gibi) bu dosya codelaw'ın gördüğü bir çapayı GÖRMEZ ve
"temiz" der. İKİNCİ muafiyet (`çapa-sentetik`) `codelaw._CAPA_SENTETIK_ISARETI`den — TEK KAYNAK
orada, `_capalari_olc` (dolayısıyla `stale_line_anchors`/`stale_tsx_line_anchors`/
`stale_docs_line_anchors`in üçü) de aynı işareti geçer (TSK-119, D3).

KAPSAM `tests/`+`ops/`, ÖZYİNELİ: `meridian/*.py` zaten v382'nin (`test_meridian_kaynaginda_
MUAFIYETSIZ_satir_capasi_YOK`). Aynı iddiayı iki dosyada tutmak, tek bir bayatlamayı iki
kırmızıya çevirirdi (v314 emsali)."""
from __future__ import annotations

import pathlib

from meridian import codelaw
from tests.test_kovab_dilim_v382 import _capa_ihlalleri, _muafiyet, _satir_capasi_deseni

REPO = pathlib.Path(__file__).resolve().parents[1]
KOKLER = ("tests", "ops")


def _sentetik_isareti() -> str:
    """İKİNCİ muafiyet — TEK KAYNAK `codelaw._CAPA_SENTETIK_ISARETI`de (TSK-119, D3, 2026-09-03).
    Buraya kopyalanmaz: kopya daralırsa bu dosya codelaw'ın muaf saydığı bir satırı MUAF SAYMAZ ve
    sahte-ihlal üretir (susturulan bekçinin TERSİ ama aynı sınıf: yanlış alarm)."""
    return codelaw._CAPA_SENTETIK_ISARETI


def _kaynaklar() -> list[pathlib.Path]:
    """`tests/`+`ops/` altındaki tüm `.py` dosyaları, özyineli, ad sırasıyla."""
    dosyalar: list[pathlib.Path] = []
    for k in KOKLER:
        kok = REPO / k
        if kok.exists():
            dosyalar.extend(sorted(kok.rglob("*.py")))
    return dosyalar


def _iki_muafiyetli_ihlaller(kaynak: str):
    """v382'nin `_capa_ihlalleri`sini (TEK ÇEKİRDEK: desen + mezar-taşı muafiyeti — İTHAL edilir,
    YENİDEN YAZILMAZ) ÇAĞIRIR ve İKİNCİ bir muafiyeti (`çapa-sentetik`) üstüne ince bir katman
    olarak ekler. `_capa_ihlalleri`nin kendi tarama döngüsü kopyalanmadı: yalnız SONUCU, ikinci
    işaretin de o satırda olup olmadığına göre süzülür."""
    satirlar = kaynak.splitlines()
    sentetik = _sentetik_isareti()
    for i, capa in _capa_ihlalleri(kaynak, _muafiyet()):
        if sentetik in satirlar[i - 1]:
            continue
        yield i, capa


# =================================================================================================
# TEK-KAYNAK DOĞRULAMASI — desen ve muafiyet(ler) KOPYALANMADI
# =================================================================================================

def test_muafiyet_v382DEN_ithal_edilir_KOPYALANMAZ():
    """v382'nin K1 dersi (2026-09-03 incelemesi): mezar-taşı işareti burada YENİDEN YAZILSAYDI,
    codelaw'ınkiyle sessizce ayrışabilirdi. İthal, ayrışmayı YAPISAL olarak imkânsız kılar."""
    assert _muafiyet() == codelaw._CAPA_MUAFIYETI == "çapa-mezar-taşı"


def test_desen_v382DEN_ithal_edilir_KOPYALANMAZ():
    """Aynı ders desen için de geçerli: `_satir_capasi_deseni()` codelaw'dan TÜRETİLİR, burada
    ikinci bir regex icat edilmedi."""
    assert _satir_capasi_deseni() is codelaw._CAPA_DESENI


def test_sentetik_isareti_CODELAW_TEK_KAYNAGINDAN_gelir():
    """İkinci muafiyet de TEK KAYNAKTAN: `codelaw._CAPA_SENTETIK_ISARETI`. Buraya kopyalanan bir
    dize sessizce ayrışabilirdi (v382'nin K1 dersinin ikinci örneği)."""
    assert _sentetik_isareti() == codelaw._CAPA_SENTETIK_ISARETI == "çapa-sentetik"


# =================================================================================================
# POZİTİF KONTROL — tarayıcı BOŞTA "temiz" demiyor, muafiyetleri GERÇEKTEN geçiyor
# =================================================================================================

def test_tarayici_SENTETIK_ihlali_yakalar():
    """Pozitif kontrol (v382/v214/v314 disiplini): sıfır iddiası ancak dedektör ÇALIŞIYORSA
    anlamlıdır. Muafiyetsiz bir satır GERÇEKTEN yakalanmalı."""
    yakalanan = list(_iki_muafiyetli_ihlaller("# bkz. uydurma_baska_modul.py:55 satırı\n"))  # çapa-sentetik: desen örneği, gerçek dosya değil (TSK-119, 2026-09-03)
    assert yakalanan == [(1, "uydurma_baska_modul.py:55")], yakalanan  # çapa-sentetik: yukarıdaki örneğin beklenen değeri, gerçek dosya değil (TSK-119, 2026-09-03)


def test_MEZAR_TASI_isaretli_satir_MUAF_gecer():
    """Birinci muafiyet (mezar taşı) burada da işler — v382'den ithal edildiği için ZATEN
    garanti, ama regresyona karşı adıyla çivilenir."""
    muaf = _muafiyet()
    assert list(_iki_muafiyetli_ihlaller(f"# uydurma_baska_modul.py:55 ({muaf})\n")) == []  # çapa-sentetik: desen örneği, gerçek dosya değil (TSK-119, 2026-09-03)


def test_SENTETIK_isaretli_satir_MUAF_gecer():
    """İkinci muafiyet (sentetik) — bu dosyanın kendi eklediği katman. İşaretsiz satır YAKALANIR,
    işaretli satır MUAF GEÇER; ikisi TEK çivide (aksi hâlde biri sessizce bozulabilir)."""
    sentetik = _sentetik_isareti()
    assert list(_iki_muafiyetli_ihlaller(
        f"# bkz. uydurma_baska_modul.py:55  # {sentetik}: fikstür, gerçek dosya değil\n")) == []  # çapa-sentetik: desen örneği, gerçek dosya değil (TSK-119, 2026-09-03)


def test_IKI_ISARET_de_TEK_satirda_calisir():
    """Bir satırda İKİ eşleşme + İKİ muafiyet birlikte: hiçbiri diğerini gizlemiyor mu?
    (v214'ün `çoklu eşleşme tek satır` desenine paralel bir pozitif kontrol.)"""
    sentetik = _sentetik_isareti()
    muaf = _muafiyet()
    satir = f'S = "a.py:1 ve b.py:2"  # {sentetik} + {muaf} (sentetik test, ikisi de burada)\n'  # çapa-sentetik: desen örneği, gerçek dosya değil (TSK-119, 2026-09-03)
    assert list(_iki_muafiyetli_ihlaller(satir)) == []


# =================================================================================================
# CANLI HÜKÜM — `tests/`+`ops/` içinde BEYANSIZ satır çapası KALMADI
# =================================================================================================

def test_KORLUK_ALARMI_taranan_dosya_TABANI_asiyor():
    """"0 ihlal" cümlesi ancak tarayıcı GERÇEKTEN çok sayıda dosyaya baktıysa anlamlıdır. Yanlış
    kök (ör. cwd kayması) az sayıda dosya döner ve "temiz" ebediyen yeşil kalırdı — bekçinin kendi
    körlüğünü yeşil sanması sınıfı (v314'ün `test_TARAMA_SESSIZCE_BOS_DEGIL` emsali).

    Taban 300: bugün ölçülen 494 (tests/+ops/, TSK-119 turu, 2026-09-03) — geniş pay, gelecekteki
    dosya sayımı düşse bile (silinen test dosyaları) çırçır değil sıfır tolerans burada; taban
    yalnız KÖRLÜĞÜ yakalar, borç saymaz."""
    dosyalar = _kaynaklar()
    assert len(dosyalar) >= 300, (
        f"taranan dosya sayısı beklenenden düşük ({len(dosyalar)}) — yasa yanlış köke bakıyor "
        "olabilir (körlük, ihlal DEĞİL)")


def test_tests_ops_kaynaginda_MUAFIYETSIZ_satir_capasi_YOK():
    """TSK-119'un asıl hükmü: v382'nin `meridian/*.py` hükmünün `tests/`+`ops/` EŞİ. Beyansız
    (ne mezar taşı ne sentetik) `dosya.py:NNN` çapası kalmadı — kalan her biri satır kayınca
    SESSİZCE yanlış yeri gösterir."""
    ihlal = [f"{yol.relative_to(REPO)}:{n} → {c}" for yol in _kaynaklar()
             for n, c in _iki_muafiyetli_ihlaller(yol.read_text(encoding="utf-8"))]
    assert not ihlal, (
        "beyansız `dosya.py:SATIR` çapası (tests/+ops/) — satır kayar, çapa SESSİZCE yanlış "
        f"satırı gösterir: {ihlal}")


def test_ops_KOKU_de_TARANIYOR():
    """Kapsam alarmı: `ops/` bugün 0 çapa taşıyor (ölçüldü) ama TARANMASI gerekiyor — kökü
    kaldırmak (ya da hiç eklememek) sessizce körlük üretirdi ve gelecekteki bir çapa doğduğu gün
    hiç görülmezdi. Bugünkü sıfır BORÇ YOKLUĞUdur, TARAMA YOKLUĞU değildir."""
    ops = REPO / "ops"
    assert ops.exists() and ops.is_dir(), "ops/ kökü bulunamadı — çivi ölçemez"
    assert any(True for _ in ops.rglob("*.py")), "ops/ altında hiç .py yok — kapsam boş görünüyor"
    assert "ops" in KOKLER


def test_tests_KOKU_de_TARANIYOR():
    """`tests/` kökünün kendisi de tarama kapsamında — bu dosyanın KENDİSİ dahil (öz-tarama,
    v382'nin `meridian/codelaw.py`yi de taraması ile aynı disiplin)."""
    assert "tests" in KOKLER
    assert any(str(y).endswith("test_tests_ops_satir_capasi_v401.py") for y in _kaynaklar())
