"""test_kart_hukum_damgasi_v251.py — HÜKÜM YAZILDI, KART HÂLÂ "ÖN-KAYIT" DİYOR (2026-08-17).

KAYIT ÇAPI — NEDEN BU DOSYA VAR. `EXE-2026-006` ölçümü TAM koşuldu (K=8, altı kill kriteri de
geçti) ve hükmü `research/olcumler/exe006_limit_bacagi_2026-08-17/HUKUM.md`e YAZILDI: *"E1 HÜKMÜ
YENİDEN AÇILIR"*. Hüküm commit'i (`a033256`) 24 dosya taşıdı ve **hepsi ölçüm artefaktıydı** —
kart dosyasına, `ROADMAP §2 TAHTA`ya, `§6` kart indeksine ve `§7` karar günlüğüne DOKUNMADI.
Sonuç: kart `status: registered` ("ölçüm bekliyor") derken hükmü diskte YAZILI duruyordu ve
`§2 TAHTA` kalemi "kart ÖN-KAYITLI · ölçüm bekliyor" satırında kalmıştı.

BU BİR İŞ BÖLÜMÜ KUSURU DEĞİL, TAM TERSİ: `research/cards/README.md` sözleşmesi (CLAUDE.md §3)
**"ölçüm ajanı karta DOKUNMAZ — hükmü Rol-1 işler"** der. Ölçüm ajanı DOĞRU davrandı; eksik olan,
Rol-1'in devralma adımının hiçbir yerde ÇİVİLİ olmamasıydı. Yani sözleşme, kendi devir noktasında
sessiz kalıyordu: hükmü yazan taraf karta dokunamaz, karta dokunacak taraf ise "hüküm hazır"
sinyalini yalnız HATIRLAYARAK alır. Bu dosya o sinyali ÖLÇÜLEBİLİR yapar.

NEDEN BU BİR HATA, BİR ÜSLUP MESELESİ DEĞİL — üç okuyucu birden yanılır:
  * `§6` indeksi "durumlar: registered → measuring → promoted | archived" diyor ve durumu KARTTAN
    okur; `registered` kalan bir kart, ölçülmüş hükmü indekse hiç taşımaz.
  * K defteri kart kimliğinden okunur (`test_kart_kimlik_v219` gerekçesi): `registered` bir kart
    K HARCAMAMIŞ görünür. `EXE-2026-006` **K=8 harcadı**; eksik K, eşiği HAK ETMEDEN geçme
    yönünde YANLIDIR — v219'un ölçtüğü yanlılığın birebir aynısı, farklı yüzeyden.
  * `§2 TAHTA`nın triyaj kuralı aşamayı "kart ÖN-KAYITLI mı" sorusundan türetir; kart yanlış
    durumda kalırsa kalem KAPANMIŞ olmasına rağmen "ölçüm bekliyor" kovasında görünür.

Sınıf adı zaten repoda var — `Ö-49 çapa/beyan çürümesi` ("yasa kuruldu, sınıf TAM kapanmadı",
`§2 TAHTA` H0). Bu çivi o sınıfın kart↔hüküm yüzeyini kapatır.

KAPSAM — BU DOSYA NEYİ ÖLÇER, NEYİ ÖLÇMEZ:
  * ÖLÇER: yazılı bir `HUKUM*.md` ile o hükmün adlandırdığı kartın `status` alanı arasındaki
    ÇELİŞKİ (hüküm var + kart `registered`), ve hükmün adlandırdığı kartın VAR olduğu.
  * ÖLÇMEZ: hükmün İÇERİĞİNİ, doğruluğunu, kartın `verdict` bloğunun eksiksizliğini ya da
    durumun `measured`/`measured_partial`/`archived` arasında DOĞRU seçildiğini. Bunlar Rol-1
    hükmüdür; bir test onları ölçemez ve ölçmeye kalkarsa var olmayan bir sözleşme uydurur
    (v219'un `trial_ids`i bilerek dışarıda bırakma gerekçesiyle AYNI disiplin).
  * ÖLÇMEZ: hükmü OLMAYAN bir kartın durumunu. `registered` kalmak, hüküm yazılmadıysa
    DOĞRUDUR — bugün dört kart (`EDG-2026-019`, `EDG-2026-040`, `EXE-2026-003`, `EXE-2026-005`)
    haklı olarak öyle duruyor. Çivi yalnız YAZILI hükmü olanı bağlar.

TEK YÖNLÜ OLMASI BİLİNÇLİ: "hüküm yok ama kart `measured`" TERS yönü burada sınanmaz, çünkü hüküm
`HUKUM.md` dışında da yazılabilir (kartın kendi `verdict` bloğu, `§7` kaydı, `BULGU-*.md`) ve
bugün 26 `measured` kartın yalnız birinin ayrı `HUKUM.md`si var. O yönü zorunlu kılmak, var olan
26 kartın hepsini yanlış-kırmızıya düşürürdü — yani ölçtüğü şey kusur değil BİÇİM olurdu.
"""
from __future__ import annotations

import pathlib
import re

KOK = pathlib.Path(__file__).resolve().parents[1]
KARTLAR = KOK / "research" / "cards"
OLCUMLER = KOK / "research" / "olcumler"

#: `HUKUM.md`in ilk başlığı hükmün SAHİBİNİ adlandırır: `# EXE-2026-006 — HÜKÜM (Rol-1, …)`.
#: Kimlik deseni `test_kart_kimlik_v219.AD_DESENI` ile AYNI gövdedir (`<AİLE>-<YIL>-<NNN>`).
HUKUM_SAHIBI_DESENI = re.compile(r"^#\s*(?P<kimlik>[A-Z]+-\d{4}-\d{3})\b", flags=re.M)
KIMLIK_DESENI = re.compile(r"^card_id:\s*(\S+)", flags=re.M)
DURUM_DESENI = re.compile(r"^status:\s*(\S+)", flags=re.M)

#: Ölçüm HENÜZ hükme bağlanmamış demek. Bu tek değer bağlayıcıdır; ilerisi Rol-1'in takdiridir.
ON_KAYIT = "registered"


def _hukum_belgeleri(kok: pathlib.Path) -> dict[str, str]:
    """`HUKUM*.md` yolu → adlandırdığı kart kimliği (adlandırmıyorsa dosya ATLANIR).

    ATLAMA BİLEREK SESSİZDİR: başlığında kart kimliği taşımayan bir hüküm belgesi bu çivinin
    konusu değildir (serbest-biçimli bir ölçüm notu olabilir). Çivinin iddiası "her HUKUM.md bir
    karta bağlanmalı" DEĞİL, "bir karta BAĞLANMIŞSA o kart ön-kayıtta kalamaz"dır."""
    out: dict[str, str] = {}
    if not kok.is_dir():
        return out
    for f in sorted(kok.rglob("HUKUM*.md")):
        m = HUKUM_SAHIBI_DESENI.search(f.read_text(encoding="utf-8"))
        if m:
            out[str(f.relative_to(kok.parent))] = m.group("kimlik")
    return out


def _kart_durumlari(dizin: pathlib.Path) -> dict[str, str | None]:
    """kart kimliği → `status` (kartta durum alanı yoksa None).

    AYRIŞTIRICI DEĞİL TARAYICI — gerekçe `test_kart_kimlik_v219._kimlikler` ile birebir aynı:
    bir kartın gövdesindeki yaml biçim hatası, durum denetimini düşürmemeli (bu depoda o vaka
    ÖLÇÜLDÜ — 2026-08-13'te dört kart ayrıştırılamıyordu, `EDG-2026-037` dahil)."""
    out: dict[str, str | None] = {}
    for f in sorted(dizin.glob("*.yaml")):
        metin = f.read_text(encoding="utf-8")
        k = KIMLIK_DESENI.search(metin)
        if not k:
            continue
        d = DURUM_DESENI.search(metin)
        out[k.group(1)] = d.group(1) if d else None
    return out


def _celiskiler(hukumler: dict[str, str], durumlar: dict[str, str | None]) -> list[dict]:
    """Hüküm YAZILI ama kart ön-kayıtta (ya da kart hiç yok) → çelişki satırları.

    İKİ AYRI KUSUR, TEK LİSTE: `sebep` alanı onları AYIRIR, çünkü çözümleri farklıdır — `on_kayitta`
    Rol-1'in devir adımını, `kart_yok` ise bir kimlik/ad kusurunu gösterir."""
    out: list[dict] = []
    for yol, kimlik in sorted(hukumler.items()):
        if kimlik not in durumlar:
            out.append({"hukum": yol, "kart": kimlik, "durum": None, "sebep": "kart_yok"})
        elif durumlar[kimlik] == ON_KAYIT:
            out.append({"hukum": yol, "kart": kimlik, "durum": ON_KAYIT, "sebep": "on_kayitta"})
    return out


# =================================================================================================
# GERÇEK AĞAÇ
# =================================================================================================

def test_hukum_belgesi_TARANABILIYOR_ve_en_az_biri_karta_baglaniyor():
    """DÜZENEK ÇİVİSİ: boş bir tarama, aşağıdaki çiviyi SESSİZ yeşile çevirirdi.

    `_hukum_belgeleri` desen kayarsa boş sözlük döner ve `test_yazili_hukum_…` hiçbir şey
    ölçmeden geçer. Bu yüzden taramanın kendisi ayrıca sınanır (v219'un
    `test_kart_dizini_okunabiliyor_ve_bos_degil` gerekçesiyle aynı: kurt masalı ANLATMAYAN bir
    dedektörün, gerçekten BAKTIĞI da kanıtlanmalı)."""
    hukumler = _hukum_belgeleri(OLCUMLER)
    assert hukumler, (
        f"{OLCUMLER} altında karta bağlanan HÜKÜM belgesi bulunamadı — desen kaymış olabilir "
        f"(beklenen ilk satır biçimi: '# EXE-2026-006 — HÜKÜM …'). Bu boşluk çiviyi sessizce "
        f"etkisizleştirir."
    )


def test_yazili_hukum_kartin_durumunu_ON_KAYITTAN_cikarmis_olmali():
    """ÇEKİRDEK ÇİVİ: hüküm diskte yazılıyken kart 'ölçüm bekliyor' diyemez.

    2026-08-17'de bu çivi KIRMIZI doğdu: `EXE-2026-006` hükmü `HUKUM.md`de yazılıydı, kart
    `status: registered` diyordu."""
    celiskiler = _celiskiler(_hukum_belgeleri(OLCUMLER), _kart_durumlari(KARTLAR))
    assert not celiskiler, (
        "HÜKÜM YAZILI ama kart onu TAŞIMIYOR — Rol-1 devir adımı atlanmış (CLAUDE.md §3: ölçüm "
        f"ajanı karta dokunmaz, hükmü Rol-1 işler):\n{celiskiler}"
    )


# =================================================================================================
# POZİTİF KONTROLLER — çivinin kendisi sınanır (sentetik ağaç, gerçek karta DOKUNULMAZ)
# =================================================================================================

def _sentetik(tmp_path: pathlib.Path, kartlar: dict[str, str], hukumler: dict[str, str]):
    """(kart dizini, ölçüm dizini) — `kartlar`: kimlik→durum, `hukumler`: alt-dizin→kimlik."""
    kd = tmp_path / "cards"
    od = tmp_path / "olcumler"
    kd.mkdir()
    od.mkdir()
    for kimlik, durum in kartlar.items():
        (kd / f"{kimlik}-sentetik.yaml").write_text(
            f"card_id: {kimlik}\nfamily: sentetik\nstatus: {durum}\n", encoding="utf-8")
    for altdizin, kimlik in hukumler.items():
        d = od / altdizin
        d.mkdir(parents=True)
        (d / "HUKUM.md").write_text(f"# {kimlik} — HÜKÜM (Rol-1, sentetik)\n", encoding="utf-8")
    return kd, od


def test_PK_hukum_varken_ON_KAYIT_kalan_kart_YAKALANIR(tmp_path):
    kd, od = _sentetik(tmp_path, {"EXE-9999-001": ON_KAYIT}, {"exe9999": "EXE-9999-001"})
    (bulgu,) = _celiskiler(_hukum_belgeleri(od), _kart_durumlari(kd))
    assert bulgu["kart"] == "EXE-9999-001" and bulgu["sebep"] == "on_kayitta"


def test_PK_hukum_islenmis_kart_SESSIZ(tmp_path):
    kd, od = _sentetik(tmp_path, {"EXE-9999-001": "measured"}, {"exe9999": "EXE-9999-001"})
    assert _celiskiler(_hukum_belgeleri(od), _kart_durumlari(kd)) == []


def test_PK_hukumu_OLMAYAN_on_kayitli_kart_SESSIZ(tmp_path):
    """Kapsam beyanının çivisi: hüküm yazılmadıysa `registered` DOĞRU durumdur."""
    kd, od = _sentetik(tmp_path, {"EXE-9999-002": ON_KAYIT}, {})
    assert _celiskiler(_hukum_belgeleri(od), _kart_durumlari(kd)) == []


def test_PK_var_olmayan_karti_adlandiran_hukum_YAKALANIR(tmp_path):
    kd, od = _sentetik(tmp_path, {"EXE-9999-001": "measured"}, {"hayalet": "EXE-9999-777"})
    (bulgu,) = _celiskiler(_hukum_belgeleri(od), _kart_durumlari(kd))
    assert bulgu["kart"] == "EXE-9999-777" and bulgu["sebep"] == "kart_yok"


def test_PK_kimlik_adlandirmayan_hukum_belgesi_ATLANIR(tmp_path):
    """Kapsam beyanı: başlığında kart kimliği olmayan hüküm belgesi bu çivinin konusu değil."""
    od = tmp_path / "olcumler"
    (od / "serbest").mkdir(parents=True)
    (od / "serbest" / "HUKUM.md").write_text("# Serbest ölçüm notu\n", encoding="utf-8")
    assert _hukum_belgeleri(od) == {}
