"""test_kart_kimlik_v219.py — ÖN-KAYIT KARTI KİMLİK TEKİLLİĞİ (2026-08-09).

KAYIT ÇAPI — NEDEN BU DOSYA VAR. Rol-1 tek gecede İKİ KEZ çakışan kart kimliği verdi ve iki elle
kontrol ikisini de kaçırdı (ölçüm: 2026-08-09, W3 turu):

  1. kart `EDG-2026-012` olarak doğdu — o kimlik `EDG-2026-012-net-issuance.yaml`da ZATEN vardı;
  2. elle düzeltme `EDG-2026-013`e taşıdı — o da `EDG-2026-013-mom-turnover.yaml`da ZATEN vardı,
     üstelik o kart ARŞİVLENMİŞ olmasına rağmen K HARCAMIŞTI (iki `trial_id`), yani çakışma boş
     bir numarayla değil ÖDENMİŞ bir K'yla oluyordu;
  3. üçüncü seferde numara grep'lendi → `EDG-2026-019` (o an gerçekten boştu).

Ve kusurun İKİNCİ YÜZÜ aynı gece ölçüldü: `mv` erken indekslendiği için dosya adı `EDG-2026-019-…`
oldu ama METİN içindeki `card_id` bir süre `EDG-2026-013` kaldı (93ae96a; düzeltmesi 6c41e8d).
Yani ad ile kimlik AYRI AYRI kayabiliyor ve dosya adına bakan bir okuyucu ile `card_id`ye bakan
bir okuyucu FARKLI karta gider.

NEDEN BU BİR HATA, BİR ÜSLUP MESELESİ DEĞİL: K defteri (çoklu-sınama cezası) kart kimliğinden
okunur. İki ayrı deneme tek kimliğe düşerse K sessizce EKSİK sayılır — ve eksik K, eşiği HAK
ETMEDEN geçme yönünde YANLIDIR. `research/cards/README.md` sözleşmesi "K grid'de ÇARPILARAK
sayılır" der; çakışan kimlik o çarpımı bozar.

KAPSAM — BU DOSYA NEYİ ÖLÇER, NEYİ ÖLÇMEZ:
  * ÖLÇER: kart DİZİNİNİN TAMAMINDA kimlik tekilliği + dosya adı ↔ `card_id` özdeşliği.
  * ÖLÇMEZ: kartın İÇERİĞİNİ (tez, eşik, kill-list) — o Rol-1'in hükmüdür ve ölçüm ajanı karta
    dokunmaz. `k_registry.trial_ids` içindeki numara da BİLEREK dışarıda: 6c41e8d'de o alan da
    kaymıştı, ama serbest-biçimli bir alandır (ölçüldü: `EDG-2026-011` `[inplay_olcum/ASKI …]`,
    `KYS-2026-001` `[kys_olcum/component_ic_temiz …]` taşıyor) ve ona kimlik önekini ZORUNLU
    kılmak var olmayan bir sözleşme uydurmak olurdu.

`tests/test_skill_gorus_v218.py::test_KART_sabiti_TEK_karta_cozulur_kimlik_cakismasi_YOK` ile
ÇAKIŞMAZ, ONU TAMAMLAR: orası TEK bir kod sabitinin (`skill_gorus.KART`) tek karta çözüldüğünü
sınar ve kapsam beyanında "kart dizininin TAMAMININ tekilliğini DEĞİL" der. Burası tam olarak o
beyanla açık bırakılan sınıfı kapatır — bu yüzden ayrı dosya: ikisinin sahibi ve ömrü ayrıdır
(oradaki çivi skill görüş katmanıyla birlikte yaşar, burası kart kaydının kendisiyle).
"""
from __future__ import annotations

import pathlib
import re

KARTLAR = pathlib.Path(__file__).resolve().parents[1] / "research" / "cards"

#: Kart dosyası adı: `<AİLE>-<YIL>-<NNN>-<slug>.yaml`. Ön ek `card_id` ile BİREBİR aynı olmalı.
AD_DESENI = re.compile(r"^(?P<onek>[A-Z]+-\d{4}-\d{3})-.+\.yaml$")
KIMLIK_DESENI = re.compile(r"^card_id:\s*(\S+)", flags=re.M)


def _kimlikler(dizin: pathlib.Path) -> dict[str, str | None]:
    """dosya adı → `card_id` (yoksa None).

    AYRIŞTIRICI DEĞİL TARAYICI: `card_id` kartın ilk satırıdır ve bu sınama için yaml yüklemek
    gereksiz bir kırılganlık olurdu (bir kartın gövdesindeki biçim hatası, kimlik denetimini
    düşürmemeli — teşhis edilen şey kimlik, gövde değil). `test_skill_gorus_v218._kart_kimlikleri`
    ile AYNI desen; o okuyucu kimliksiz kartı sessizce atlar, bu okuyucu None ile GÖRÜNÜR tutar
    çünkü buranın sorusu "hepsinde var mı"yı da içerir."""
    out: dict[str, str | None] = {}
    for f in sorted(dizin.glob("*.yaml")):
        m = KIMLIK_DESENI.search(f.read_text())
        out[f.name] = m.group(1) if m else None
    return out


def _cakisanlar(kimlikler: dict[str, str | None]) -> dict[str, list[str]]:
    """kimlik → onu taşıyan BİRDEN FAZLA dosya. Boş sözlük = tekillik sağlam."""
    ters: dict[str, list[str]] = {}
    for dosya, kimlik in kimlikler.items():
        if kimlik is not None:
            ters.setdefault(kimlik, []).append(dosya)
    return {k: v for k, v in ters.items() if len(v) > 1}


def _ad_kimlik_ayrismasi(kimlikler: dict[str, str | None]) -> list[tuple[str, str | None, str]]:
    """(dosya, card_id, dosya adı öneki) — üçlüsü yalnız AYRIŞANLAR için döner."""
    out = []
    for dosya, kimlik in sorted(kimlikler.items()):
        m = AD_DESENI.match(dosya)
        onek = m.group("onek") if m else "<ad deseni tutmuyor>"
        if kimlik != onek:
            out.append((dosya, kimlik, onek))
    return out


# =================================================================================================
# 1 · GERÇEK KART DİZİNİ
# =================================================================================================
def test_kart_dizini_okunabiliyor_ve_bos_degil():
    """Sıfır iddiasının şartı: boş bir dizinde "çakışma yok" cümlesi BOŞ bir cümledir. Kart
    dizini taşınır ya da glob deseni bozulursa aşağıdaki iki test sessizce yeşile döner — bu
    test o sessizliği kapatır."""
    assert KARTLAR.is_dir(), f"kart dizini yok: {KARTLAR}"
    kimlikler = _kimlikler(KARTLAR)
    assert len(kimlikler) >= 20, f"kart dizini şüpheli derecede küçük: {sorted(kimlikler)}"
    kimliksiz = sorted(d for d, k in kimlikler.items() if k is None)
    assert not kimliksiz, f"`card_id` satırı olmayan kart: {kimliksiz} — kimliksiz kart K harcayamaz"


def test_hicbir_card_id_CIFT_DEGIL():
    """SINIF KAPAMASI. İki kart aynı kimliği taşıyorsa iki AYRI deneme tek K'ya katlanır ve
    çokluk düzeltmesi eksik sayar — eşiği hak etmeden geçme yönünde yanlı bir hata."""
    cakisan = _cakisanlar(_kimlikler(KARTLAR))
    assert not cakisan, (
        "çift kullanılmış card_id(ler): "
        + " · ".join(f"{k} → {', '.join(v)}" for k, v in sorted(cakisan.items()))
        + ". K defteri kart kimliğinden okunur; çakışan kimlik iki denemeyi tek K'ya katlar. "
        + f"Boştaki numaralar: {bos_numaralar(_kimlikler(KARTLAR))}")


def test_dosya_adi_ONEKI_card_id_ILE_AYNI():
    """İKİNCİ YÜZ (93ae96a vakası): `mv` indekslenip metin ağaçta kaldığında dosya adı 019, kimlik
    013 oldu. Tekillik testi bunu YAKALAMAZDI — 013 o an tek kalmıştı bile denemez, ÇAKIŞIYORDU
    ama sınıf olarak ayrıdır: burada ölçülen şey çokluk değil, İKİ OKUYUCUNUN farklı karta
    gitmesidir (dosya adına bakan biri ile `card_id`ye bakan biri)."""
    ayrisan = _ad_kimlik_ayrismasi(_kimlikler(KARTLAR))
    assert not ayrisan, (
        "dosya adı ile card_id ayrışmış: "
        + " · ".join(f"{d}: card_id={k} ≠ ad öneki={o}" for d, k, o in ayrisan)
        + ". İkisi de bir okuyucusu olan kimliktir; ayrıştıklarında hangisinin doğru olduğu "
          "ölçülemez — düzeltme kartın KENDİ tarihçesine yazılır (Rol-1 hükmü).")


def bos_numaralar(kimlikler: dict[str, str | None], n: int = 4) -> list[str]:
    """Sıradaki KULLANILMAYAN EDG numaraları — hata mesajı bir sonraki adımı da söylesin
    (test_skill_gorus_v218._bos_kimlikler ile aynı yardım deseni)."""
    kullanilan = {int(m.group(1)) for k in kimlikler.values()
                  if k and (m := re.match(r"EDG-2026-(\d+)$", k))}
    return [f"EDG-2026-{i:03d}" for i in range(1, max(kullanilan or [0]) + n + 1)
            if i not in kullanilan][:n]


# =================================================================================================
# 2 · POZİTİF KONTROL — dedektörün ÇALIŞTIĞI kanıtlanır (test_codelaw_v59 disiplini)
# =================================================================================================
# Yeşilin anlamı olması için tarayıcının kırmızıya DÖNEBİLDİĞİ gösterilmelidir. Bu turun tam
# olarak kaçırdığı şey buydu: "elle baktım, temiz" iki kez yeşil dedi ve iki kez yanıldı.

def _sentetik(tmp_path: pathlib.Path, kartlar: dict[str, str]) -> pathlib.Path:
    d = tmp_path / "cards"
    d.mkdir()
    for ad, kimlik in kartlar.items():
        (d / ad).write_text(f"card_id: {kimlik}\nfamily: sentetik\nstatus: registered\n")
    return d


def test_PK_cakisan_kimlik_YAKALANIR(tmp_path):
    """Vakanın 1. ve 2. adımı: yeni kart, ZATEN kullanılan bir numarayla doğuyor."""
    d = _sentetik(tmp_path, {"EDG-2026-013-mom-turnover.yaml": "EDG-2026-013",
                             "EDG-2026-013-yeni-kart.yaml": "EDG-2026-013"})
    cakisan = _cakisanlar(_kimlikler(d))
    assert cakisan == {"EDG-2026-013": ["EDG-2026-013-mom-turnover.yaml",
                                        "EDG-2026-013-yeni-kart.yaml"]}


def test_PK_ad_ile_kimlik_ayrismasi_YAKALANIR(tmp_path):
    """Vakanın 3. adımı (93ae96a): dosya adı taşındı, metin taşınmadı."""
    d = _sentetik(tmp_path, {"EDG-2026-019-skill-gorus-defteri.yaml": "EDG-2026-013"})
    assert _ad_kimlik_ayrismasi(_kimlikler(d)) == [
        ("EDG-2026-019-skill-gorus-defteri.yaml", "EDG-2026-013", "EDG-2026-019")]
    # Ve tekillik testi bunu TEK BAŞINA yakalamazdı — iki sınıfın ayrı olmasının kanıtı.
    assert _cakisanlar(_kimlikler(d)) == {}


def test_PK_temiz_dizin_SESSIZ(tmp_path):
    """Negatif kontrol: dedektör her şeye kırmızı yakan bir alarm değil."""
    d = _sentetik(tmp_path, {"EDG-2026-001-a.yaml": "EDG-2026-001",
                             "EXE-2026-002-b.yaml": "EXE-2026-002"})
    assert _cakisanlar(_kimlikler(d)) == {} and _ad_kimlik_ayrismasi(_kimlikler(d)) == []


def test_PK_bos_numara_yardimcisi_SIRADAKINI_soyler(tmp_path):
    """Hata mesajının işe yaraması da bir sözleşmedir: çakışmayı bildiren satır, bir sonraki
    boş numarayı da vermelidir (aksi hâlde düzeltme yine elle grep'e döner — kusurun kökü)."""
    d = _sentetik(tmp_path, {"EDG-2026-001-a.yaml": "EDG-2026-001",
                             "EDG-2026-003-c.yaml": "EDG-2026-003"})
    assert bos_numaralar(_kimlikler(d), n=2)[:2] == ["EDG-2026-002", "EDG-2026-004"]
