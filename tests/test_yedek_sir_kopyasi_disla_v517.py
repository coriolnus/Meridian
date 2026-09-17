"""test_yedek_sir_kopyasi_disla_v517.py — TSK-197 (2026-09-17): gece yedek birimi ELLE bırakılmış
sır yedeği kopyalarını (`state/secrets.json.bak-*`) arşivden BEYANLI ve DAR biçimde hariç tutar.

NEDEN BU TEST VAR (ölçülmüş, Rol-1 A1 triyajı + ölçümü). `meridian-backup.service` 2026-09-15'ten
beri HER GECE `failed` dönüyordu. Kök neden: TSK-189 sır rotasyonunda ELLE bırakılmış tek seferlik
kopya `state/secrets.json.bak-20260915T073825Z-tsk189` root:root 0600; birim `User=ubuntu` → tar
"Cannot open" → tar çıkışı 2 → ExecStart kapısı `[ $$rc -le 1 ]` düşer. Arşiv yine yazılıyordu
(veri kaybı yok) ama birim kırmızı olduğu için ExecStartPost'un 7 günlük silmesi koşmuyordu ve
kalıcı kırmızı gerçek bir arızayı körleştiriyordu. Ölçüm (A1, GNU tar 1.35, `ubuntu` olarak, diske
arşiv yazılmadan boruyla): bugünkü komut tar çıkışı 2 / "Cannot open" 1; desen eklenince 0 / 0.

ÇİVİLENEN ALTI ŞEY — hepsi birim dosyasını METİN olarak okur (canlıya dokunmaz):
  1. tar çağrısı sır kopyası desenini TAM BİR kez taşır; `*` taşıyan her desen sh katmanında ÇİFT
     TIRNAKLIDIR (gerekçe ilgili testin docstring'inde).
  2. `--exclude=state/sprint` (2026-08-02 kapsam kararı) yerinde.
  3. `--ignore-failed-read` YOK — sessiz yedek kaybı sınıfının (birim şerhindeki H9 vakası) kapısı.
  4. Kapı aynen: `rc=$$?` tar'ı ölçer, `[ $$rc -le 1 ]` ve `[ $$ok -eq 1 ]` duruyor.
  5. DAR DESEN: yalnız elle bırakılan kopya dışlanır; canlı sır dosyası ve defter yedekleri içeride.
  6. Birim başlığında TSK-197 beyanı BEDEL ve REDDEDİLEN kalemleriyle var (varlık çivisi).

AYRIŞTIRICI TEK KAYNAK: systemd birim ayrıştırıcısı `test_h3_tur2_v174` dosyasından İTHAL edilir
(yorum ≠ direktif, satır-sonu `#` kırpılmaz, skaler direktifte son atama) — kopyası burada yok.

5. ÇİVİ BİR YAKLAŞIK ÖLÇÜDÜR, tar'ın kendisi DEĞİLDİR. GNU tar `--exclude` varsayılanı: joker AÇIK,
`*` eğik çizgiyi de eşler, desen ÇAPASIZ (herhangi bir `/` sonrasından başlayarak eşleşebilir) ve
dizin eşleşmesi alt ağacı da kapsar. Burada bu davranış Python `fnmatch.fnmatchcase` ile, üye adının
bileşen sınırlarında başlayan ve biten HER alt yolu denenerek taklit edilir — gerçek tar'dan GENİŞ
(daha çok dışlayan) yöndedir, yani "dışlanmamalı" iddiası için muhafazakârdır. Kesin hüküm A1
ölçümüdür (birim şerhindeki tablo).
"""
from __future__ import annotations

import fnmatch
import re

from tests.test_h3_tur2_v174 import _deger, _metin, _service

BIRIM = "meridian-backup.service"
SIR_KOPYA_DESENI = "state/secrets.json.bak-*"

# A1'de ölçülen gerçek üye adları (Rol-1, 2026-09-17). Yeni desenle arşive girmeye DEVAM etmesi
# gereken yedek adlı üyeler BİLEREK listede: desen onları dışlarsa canlı sır ya da defter yedeği
# sessizce arşivden düşer.
DISLANMALI = ("state/secrets.json.bak-20260915T073825Z-tsk189",)
DISLANMAMALI = (
    "state/secrets.json",
    "state/meridian.db.yedek",
    "state/meridian.db.20260913T211859Z.bak",
    "state/meridian.db.20260913T211859Z.bak-wal",
    "state/meridian.db.20260913T211859Z.bak-shm",
)

# `--exclude=desen` ya da `--exclude="desen"`; eşleşmeyen tırnak çiftini desen SAYMAZ (bozuk tırnak
# çivi 1'i düşürür, sessizce "var" demez).
_EXCLUDE = re.compile(r'--exclude=("?)([^"\s]+)\1(?=\s|$)')
_JOKER = re.compile(r"[*?\[]")


def _exec_start() -> str:
    deger = _deger(BIRIM, "ExecStart")
    assert deger is not None, f"{BIRIM}: ExecStart yok"
    return deger


def _tar_cagrisi_ve_sonrasi() -> tuple[str, str]:
    """ExecStart'ın `sh -c` dizgisinden tar komutunu (`tar -czf` → ilk `;`) ve ARDINDAN geleni keser."""
    e = _exec_start()
    i = e.find("tar -czf")
    assert i >= 0, f"{BIRIM}: ExecStart'ta `tar -czf` yok: {e!r}"
    j = e.find(";", i)
    assert j > i, f"{BIRIM}: tar çağrısı `;` ile kapanmıyor: {e!r}"
    return e[i:j], e[j:]


def _desenler() -> list[str]:
    tar, _ = _tar_cagrisi_ve_sonrasi()
    return [m.group(2) for m in _EXCLUDE.finditer(tar)]


def _tar_dislar_mi(uye: str, desenler: list[str]) -> bool:
    """GNU tar exclude davranışının YAKLAŞIĞI (modül docstring'i): bileşen sınırında başlayıp biten
    her alt yol, her desenle joker eşleşmesine sokulur."""
    parcalar = uye.split("/")
    adaylar = {"/".join(parcalar[i:j])
               for i in range(len(parcalar)) for j in range(i + 1, len(parcalar) + 1)}
    return any(fnmatch.fnmatchcase(aday, desen) for aday in adaylar for desen in desenler)


# ==================================================================================================
# 1 — desen tar çağrısında TAM BİR kez; joker sh katmanında tırnaklı
# ==================================================================================================
def test_tar_sir_kopyasi_desenini_tam_bir_kez_tasir():
    desenler = _desenler()
    assert desenler.count(SIR_KOPYA_DESENI) == 1, (
        f"tar çağrısı `--exclude` ile `{SIR_KOPYA_DESENI}` desenini tam bir kez taşımıyor — elle "
        f"bırakılan root 0600 sır kopyası tar'ı çıkış 2 ile düşürür (TSK-197): {desenler!r}")
    assert _exec_start().count("secrets.json.bak-") == 1, (
        f"sır kopyası deseni ExecStart'ta birden çok yerde geçiyor: {_exec_start()!r}")


def test_joker_tasiyan_exclude_deseni_sh_katmaninda_cift_tirnakli():
    """KATMAN ZİNCİRİ. systemd ExecStart'ın dış TEK tırnağını SÖKER ve `sh`a `-c` dizgisini TIRNAKSIZ
    verir. `sh` o dizgide çıplak `--exclude=state/secrets.json.bak-*` kelimesine yol-adı
    genişletmesi UYGULAR; bugün `WorkingDirectory` altında `--exclude=state` adlı dizin olmadığı için
    kelime aynen kalırdı — yani güvence bir tesadüfe dayanırdı. Çift tırnak genişletmeyi `sh`
    katmanında kapatır ve tar'a A1'de ölçülen argümanı birebir ulaştırır. Düz `"` systemd tek
    tırnağından SAĞLAM geçer (aynı satırdaki python bacağı bu biçimi 2026-08-02'den beri canlıda
    taşıyor); YASAK olan ters-bölülü tırnaktır, o ayrıca `test_h3_tur2_v174`te çivili."""
    tar, _ = _tar_cagrisi_ve_sonrasi()
    jokerli = [m.group(0) for m in _EXCLUDE.finditer(tar) if _JOKER.search(m.group(2))]
    assert jokerli, f"tar çağrısında joker taşıyan `--exclude` yok: {tar!r}"
    tirnaksiz = [arg for arg in jokerli if not arg.startswith('--exclude="')]
    assert not tirnaksiz, (
        f"joker taşıyan `--exclude` deseni sh katmanında tırnaksız — `sh` yol-adı genişletmesi "
        f"uygular, desen tar'a ancak eşleşme yoksa aynen ulaşır: {tirnaksiz!r}")


# ==================================================================================================
# 2 — sprint dışlaması yerinde
# ==================================================================================================
def test_sprint_dislamasi_yerinde():
    assert "state/sprint" in _desenler(), (
        f"`--exclude=state/sprint` tar çağrısından düşmüş (2026-08-02 kapsam kararı): {_desenler()!r}")


# ==================================================================================================
# 3 — sessiz yedek kaybı kapısı: --ignore-failed-read YOK
# ==================================================================================================
def test_ignore_failed_read_hicbir_direktifte_yok():
    """`--ignore-failed-read` okunamayan HER dosyayı sessizce atlar: bugünkü tek kopya yerine yarın
    okunamaz hâle gelen gerçek bir veri dosyası da arşivden düşer ve birim `success` der — bu birimin
    şerhindeki H9 "sessiz yedek kaybı" sınıfı. Yalnız direktif değerleri taranır; şerhte REDDEDİLEN
    olarak adıyla geçmesi beklenen bir şeydir (çivi 6)."""
    ihlaller = [(k, satir) for k, v, satir in _service(BIRIM) if "--ignore-failed-read" in v]
    assert not ihlaller, (
        f"{BIRIM}: `--ignore-failed-read` direktifte — okunamayan her dosya sessizce atlanır "
        f"(TSK-197 REDDEDİLEN): {ihlaller!r}")


# ==================================================================================================
# 4 — kapı sıkılığı aynen
# ==================================================================================================
def test_kapi_rc_tar_i_olcer_ve_esikler_aynen():
    e = _exec_start()
    _, sonrasi = _tar_cagrisi_ve_sonrasi()
    assert sonrasi.startswith("; rc=$$?;"), (
        f"`rc` tar çağrısının hemen ardından ölçülmüyor — kapı tar'ın çıkışını görmez: {sonrasi!r}")
    assert "[ $$rc -le 1 ]" in e, f"tar kapısı `[ $$rc -le 1 ]` değişmiş/gevşemiş: {e!r}"
    assert "[ $$ok -eq 1 ]" in e, f"python bacağı kapısı `[ $$ok -eq 1 ]` düşmüş: {e!r}"
    assert e.endswith("[ $$rc -le 1 ] && [ $$ok -eq 1 ]'"), (
        f"ExecStart'ın son ifadesi iki kapı değil — birim sonucu başka bir komuttan gelir: {e!r}")


# ==================================================================================================
# 5 — dar desen: yalnız elle bırakılan kopya dışlanır
# ==================================================================================================
def test_dar_desen_yalniz_sir_kopyasini_dislar():
    desenler = _desenler()
    for uye in DISLANMALI:
        assert _tar_dislar_mi(uye, desenler), (
            f"`{uye}` dışlanmıyor — okunamayan kopya tar'ı çıkış 2 ile düşürmeye devam eder: {desenler!r}")
    for uye in DISLANMAMALI:
        assert not _tar_dislar_mi(uye, desenler), (
            f"`{uye}` dışlanıyor — desen GENİŞ; canlı sır dosyası ya da defter yedeği sessizce "
            f"arşivden düşer: {desenler!r}")


# ==================================================================================================
# 6 — birim başlığında TSK-197 beyanı (varlık çivisi)
# ==================================================================================================
def test_birim_basliginda_tsk197_beyani_bedel_ve_reddedilen_ile():
    basliklar = []
    for satir in _metin(BIRIM).splitlines():
        if satir.strip() == "[Unit]":
            break
        basliklar.append(satir)
    baslik = "\n".join(basliklar)
    assert "TSK-197" in baslik, f"{BIRIM}: `[Unit]` öncesi başlıkta TSK-197 beyanı yok"
    beyan = baslik[baslik.index("TSK-197"):]
    for sozcuk in ("BEDEL", "REDDEDİLEN", "--ignore-failed-read"):
        assert sozcuk in beyan, f"{BIRIM}: TSK-197 beyanı `{sozcuk}` kalemini taşımıyor"
