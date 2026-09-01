"""tests/test_roadmap_standart_v351.py — ROADMAP.md madde standardı zorlama çivisi (2026-09-01).

KAYIT ÇAPI. Operatör kararı (2026-09-01 gece): ROADMAP.md'deki HER kalemin isimlendirmesi,
durumu, sahibi, boyutu tek şemaya uysun — `docs/TASARIM-ROADMAP-STANDART-2026-09-01.md` (§1
şema, §4 zorlama-1). Göç üç ajan turunda (FAZ A: §4/§5 · FAZ B: §0/§2/§3/§∞ · FAZ B2: §6) tüm
YAŞAYAN bölümleri şemaya çevirdi; bu dosya o şemayı MEKANİK olarak zorlar — spec §4.1'in
öngördüğü "yeni çivi dosyası (vNNN)". Numara REZERVE edildi (2026-09-01 taramasında boştu).

KAPSAM — "MADDE" TANIMI (FAZ A/B/B2'nin FİİLÎ çıktısından türetildi, uydurulmadı):
  Bu dosya YALNIZ `- **[<KİMLİK>] <Ad>** — <alan1>: … · <alan2>: … · …` biçimindeki BULLET
  başlık satırlarını "madde" sayar (`- **[` öneki pratik çapa — FAZ A/B/B2'nin üç turu da
  İCRA SIRASI/§4 HAVUZ/§5 MASA/§6 KART ENDEKSİ'nin tümünde AYNI bullet biçimini kullandı; bu
  gerçek, uydurulmuş bir varsayım değil, `ROADMAP.md`'nin kendisinden ölçüldü).
  §2 TAHTA'nın (H1/H0/DİK DURUM) markdown TABLO satırları BAŞKA bir yüzeydir (FAZ B raporu
  §2 maddesi 2: "TAHTA tabloları ... `id · name · status · owner · size · trigger` şemasına
  çevrildi" — pipe-tablo, bullet DEĞİL) ve zaten `tests/test_yol_haritasi_tablo_yuzeyi_v343.py`
  tarafından ayrı ölçülüyor. Onu burada YİNELEMEK tek-kaynak yasasını (CLAUDE.md §4) çiğnerdi —
  bilinçli bir kapsam dışı bırakma, bir atlama değil.

BÖLÜM SÜZGECİ — "§0, §2, §3, §4, §5, §6" YAŞAYAN + "§1/§7/§8/§∞" MUAF (görev brief'i, spec §3
Kapsam ile birebir): sınırlar HARDCODE SATIR NUMARASI DEĞİL `^## §(\\S+)` başlık deseninden
DİNAMİK çıkarılır (CLAUDE.md: "çapa SATIR değil SEMBOL olmalı — satır kayar, CI kırar"). §1 HAT
kendi metninde zaten "BU BÖLÜM KALEM TAŞIMAZ" diyor (kalem yok, dokunmaya gerek yok); §7/§8/§∞
operatör onaylı MUAF (spec §3, tarihçe-koru).

§6 KART-AİLESİ KİMLİĞİ — SPEC METNİNDEN SAPMA (dürüstçe belgeli). Spec §2 tarihli eki yalnız
"[EDG-2026-0NN] YA DA [EXE-2026-0NN]" der ("iki kart sınıfı da meşru"). Ama ROADMAP.md'nin
FİİLÎ §6'sı (`git show` ile doğrulandı, satır 3016/3076) `[KYS-2026-001]` ve `[BASE-2026-001]`
de taşıyor — FAZ B2 bu iki kartı da AYNI başlık gramerine çevirmiş (research/cards/ dizininde
gerçekten var: `KYS-2026-00{1,2}-*.yaml`, `BASE-2026-001-*.yaml`). Kart ailesi öneki için
TEK gerçek kaynak `tests/test_kart_kimlik_v219.py::AD_DESENI`dir (dosya-adı deseni,
`[A-Z]+-\\d{4}-\\d{3}` — EDG/EXE'ye ÖZEL değil, herhangi bir büyük-harf aileye açık). Bu dosya
o deseni buradan YENİDEN İCAT ETMEZ, `AD_DESENI`nin `onek` grubunu türetir (tek-kaynak yasası):
spec'in "iki sınıf" örneklemesi tam değildi, v219 esas alınır — brief'in kendi talimatı da
buydu ("gerçek sayıyı dosyadan öğren").

ÖLÇÜLEN GERÇEK İHLALLER — TARİHÇE (FAZ C ilk taraması 21 ihlal bulmuştu, aynı gece Rol-1
tarafından giderildi; bu bölüm GÜNCEL DURUMU değil o turun kaydını taşır):
  - `status-ciplak-parantezli` (4, GİDERİLDİ): TSK-001/058/060/066 — ACTIVE/QUEUED gibi ÇIPLAK
    durum değerlerine eklenmiş açıklayıcı parantezler gövdeye (`What:` satırı başına
    `(status notu: …)`) taşındı; içerik SİLİNMEDİ, yalnız doğru alana indi.
  - `size-sozluk-disi` (16, spec EKİYLE GİDERİLDİ): TSK-021 `size: karta bağlı` (serbest
    metin) → `size: — (boyut seçilecek yola bağlı — ölçülemez, beyanlı)`; diğer 15
    (TSK-023/025/026/027/028/031/032/033/034/036/037/038/039/040/041) zaten `size: —`
    kullanıyordu ve DOKUNULMADI — spec §1'e 2026-09-01 tarihli ek geldi (Rol-1, FAZ C
    bulgusu): boyut ÖLÇÜLEMİYORSA `—` meşrudur (uydurma yasağı S/M/L uydurtmaktan üstündür);
    bu 15 satırın gövdesi zaten gerekçeyi taşıyordu (ör. "WP6-E'ye taşındı"), yeni ihlal
    değil retroaktif meşruiyet kazandılar.
  - `done-tarih-eksik` (1, GİDERİLDİ): TSK-022 `DONE(v249·…)` → `DONE(2026-08-17·v249: …)` —
    tarih git kanıtından (commit `29d3ce1`) geri kondu.
  ÇİVİ KENDİSİ o turdan sonra GÜNCELLENDİ (bu commit): `r04_size_sozlugu` artık `—` ve
  `— (beyan)` biçimlerini MEŞRU sayıyor (`SIZE_BELIRSIZ_DESENI`); üç sınıfın gerçek-dosya
  testleri İSİMLİ pin'den sıfır-ihlal iddiasına döndü (`test_gercek_dosya_toplam_ihlal_
  envanteri_sifir`). Diğer 11 kural sınıfı zaten ilk turdan beri 0 ihlal ölçüyordu.

MUTASYON KANITI (madde 7, brief). Her çivi fonksiyonu SAF'tır: metni PARAMETRE alır, dosyayı
kendi İÇİNDE okumaz. Böylece aynı fonksiyon hem gerçek `ROADMAP.md` metniyle (şu an TÜM 14
kural sınıfında 0 ihlal — `test_gercek_dosya_toplam_ihlal_envanteri_sifir`) hem de bu dosyanın
İÇİNDEKİ sentetik ihlal metinleriyle (her kural için ayrı, minimal, `- **[TSK-900] ...**`
biçiminde tek satırlık kurgu) iki ayrı testte koşar — sentetik test çivinin GERÇEKTEN
ısırdığını (yanlış-negatif üretmediğini) kanıtlar, gerçek-dosya testi de şemanın gerçek metne
tam uyduğunu DOĞRU RAPORLAR (yanlış-pozitif üretmez). Gerçek dosyada gelecekte yeni bir ihlal
doğarsa bu testler KIRMIZI olur — o an beklenen, istenen davranıştır (bir hata değil).
"""
from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

import pytest

from tests.test_kart_kimlik_v219 import AD_DESENI

ROADMAP_YOLU = Path(__file__).resolve().parents[1] / "ROADMAP.md"

# --- tek-kaynak: kart ailesi deseni v219'un dosya-adı deseninden türetilir -------------------
_ONEK_ALT = AD_DESENI.pattern.split("(?P<onek>", 1)[1].split(")", 1)[0]
KART_KIMLIK_DESENI = re.compile(rf"^{_ONEK_ALT}$")

TSK_KIMLIK_DESENI = re.compile(r"^TSK-\d+$")
BOLUM_BASLIK_DESENI = re.compile(r"^## §(\S+)")
MADDE_SATIRI_DESENI = re.compile(r"^- \*\*\[([^\]]+)\] ([^*]*)\*\* — (.*)$")
PRG_BASLIK_DESENI = re.compile(r"^### (PRG-\d+) — (.+)$", re.MULTILINE)

YASAYAN_BOLUMLER = frozenset({"0", "2", "3", "4", "5", "6"})

OWNER_SOZLUGU = frozenset({"operator", "rol1", "agent"})
SIZE_SOZLUGU = frozenset({"S", "M", "L", "S-M", "M-L"})
# tarihli ek 2026-09-01 (spec §1, Rol-1/FAZ C bulgusu): boyut ÖLÇÜLEMİYORSA `—` meşrudur —
# ya çıplak ya da yanına parantezli beyanla (gövdede neden beyanı ayrı bir denetim, bu regex
# yalnız HEADER alanının biçimini sınar). Örnek gerçek veri: TSK-021
# `size: — (boyut seçilecek yola bağlı — ölçülemez, beyanlı)`.
SIZE_BELIRSIZ_DESENI = re.compile(r"^—(\s*\(.+\))?$")
CIPLAK_STATUS_SOZLUGU = frozenset({"ACTIVE", "QUEUED", "INTERIM", "OPERATOR"})
PARANTEZLI_STATUS_ANAHTARLARI = frozenset({"GATED", "DONE", "DROPPED"})
KART_CIPLAK_STATUS_SOZLUGU = frozenset({"ACTIVE", "OPERATOR"})
KART_VERDICT_SOZLUGU = frozenset({"GEÇTİ", "KALDI", "NO-GO"})

TSK_ALAN_SIRASI = ("status", "born", "owner", "size", "trigger")
KART_ALAN_SIRASI = ("status", "owner", "size", "trigger")


# ======================================================================================
# ayrıştırma yardımcıları — SAF fonksiyonlar, dosya OKUMAZ, metin PARAMETRE alır
# ======================================================================================


def _bolum_sinirlari(satirlar: list[str]) -> dict[str, tuple[int, int]]:
    """`^## §X ...` başlıklarından [start, end) yarı-açık satır aralığı (0-index) çıkarır.

    Çapa SEMBOLDÜR (başlık deseni), satır numarası değil — ROADMAP.md büyüdükçe/küçüldükçe
    bu fonksiyon kendini yeniden hizalar."""
    imler: list[tuple[int, str | None]] = []
    for i, satir in enumerate(satirlar):
        m = BOLUM_BASLIK_DESENI.match(satir)
        if m:
            imler.append((i, m.group(1)))
    imler.append((len(satirlar), None))
    sonuc: dict[str, tuple[int, int]] = {}
    for (start, anahtar), (bitis, _) in zip(imler, imler[1:]):
        if anahtar is not None:
            sonuc[anahtar] = (start, bitis)
    return sonuc


def _hangi_bolum(idx: int, sinirlar: dict[str, tuple[int, int]]) -> str | None:
    for anahtar, (a, b) in sinirlar.items():
        if a <= idx < b:
            return anahtar
    return None


def _derinlik_farkinda_bol(s: str, ayrac: str = " · ") -> list[str]:
    """Parantez DERİNLİĞİNE duyarlı bölme.

    Gerçek veri `status: DONE(2026-08-31/09-01 · \\`ops/akibet.py\\`, commit "...", v349, 28
    çivi) · born: ...` gibi satırlar taşıyor — DONE(...) İÇİNDEKİ '·' üst-düzey alan ayracıyla
    karışırsa (naif `split(" · ")`) alan sayımı bozulur ve tamamen sağlam satırlar yanlış
    ihlal sayılır. Bu fonksiyon yalnız parantez derinliği 0 iken ayraçta böler."""
    parcalar: list[str] = []
    derinlik = 0
    tampon: list[str] = []
    i = 0
    n = len(s)
    while i < n:
        ch = s[i]
        if ch == "(":
            derinlik += 1
            tampon.append(ch)
            i += 1
        elif ch == ")":
            derinlik -= 1
            tampon.append(ch)
            i += 1
        elif derinlik == 0 and s[i : i + len(ayrac)] == ayrac:
            parcalar.append("".join(tampon))
            tampon = []
            i += len(ayrac)
        else:
            tampon.append(ch)
            i += 1
    parcalar.append("".join(tampon))
    return parcalar


def _alan_anahtarlari_ve_sozlugu(govde: str) -> tuple[list[str], dict[str, str]]:
    """(sırayla anahtar listesi, anahtar->değer sözlüğü) — sıra grameri sınamak için ayrı
    tutulur (dict de Python 3.7+'ta sıralı ama niyeti okuyucuya açıkça yazmak için)."""
    anahtarlar: list[str] = []
    sozluk: dict[str, str] = {}
    for parca in _derinlik_farkinda_bol(govde):
        if ":" in parca:
            anahtar, deger = parca.split(":", 1)
            anahtar = anahtar.strip()
            anahtarlar.append(anahtar)
            sozluk[anahtar] = deger.strip()
    return anahtarlar, sozluk


def _yasayan_madde_satirlari(metin: str) -> list[tuple[int, str, str, str, str]]:
    """(satır_no[1-index], bölüm_anahtarı, kimlik, ad, alan-gövdesi) — yalnız YAŞAYAN
    bölümlerdeki `- **[...]**` bullet başlıkları. Muaf bölümler (§1/§7/§8/§∞) burada SESSİZCE
    elenir — bu elemenin kendisi de ayrı bir testle (bölüm muafiyeti) sınanır."""
    satirlar = metin.splitlines()
    sinirlar = _bolum_sinirlari(satirlar)
    sonuc: list[tuple[int, str, str, str, str]] = []
    for idx, satir in enumerate(satirlar):
        m = MADDE_SATIRI_DESENI.match(satir)
        if not m:
            continue
        bolum = _hangi_bolum(idx, sinirlar)
        if bolum not in YASAYAN_BOLUMLER:
            continue
        kimlik, ad, govde = m.groups()
        sonuc.append((idx + 1, bolum, kimlik, ad, govde))
    return sonuc


# ======================================================================================
# çivi fonksiyonları — SAF, metin alır, ihlal sözlüğü döner (boş = tam uyum)
# ======================================================================================


def madde_ihlallerini_bul(metin: str) -> dict[str, list[str]]:
    """Ana çivi: YAŞAYAN bölümlerdeki her madde başlığını spec §1/§2/§4'e karşı sınar.

    Dönen: ihlal-sınıfı -> [açıklama, ...]. Sınıf anahtarları test fonksiyonu adlarıyla
    birebir eşlenir (aşağıdaki `test_r*` fonksiyonlarına bakınız)."""
    ihlaller: dict[str, list[str]] = defaultdict(list)
    ad_kayitlari: dict[str, set[str]] = defaultdict(set)

    for lineno, bolum, kimlik, ad, govde in _yasayan_madde_satirlari(metin):
        konum = f"satır {lineno} [{kimlik}]"
        anahtarlar, alanlar = _alan_anahtarlari_ve_sozlugu(govde)

        if bolum == "6":
            # --- §6 KART ENDEKSİ: farklı alan seti (born YOK), farklı kimlik/durum sözlüğü ---
            if anahtarlar != list(KART_ALAN_SIRASI):
                ihlaller["r01_madde_grameri"].append(
                    f"{konum}: §6 alan sırası {KART_ALAN_SIRASI} bekleniyordu, bulunan: {anahtarlar}"
                )
            if TSK_KIMLIK_DESENI.match(kimlik):
                ihlaller["r10_kimlik_sizmasi"].append(
                    f"{konum}: TSK kimliği §6 kart endeksinde GEÇEMEZ (spec §2 tarihli ek)"
                )
            elif not KART_KIMLIK_DESENI.match(kimlik):
                ihlaller["r11_kart_kimlik_bicimi"].append(
                    f"{konum}: '{kimlik}' kart-ailesi deseniyle (v219 AD_DESENI onek) eşleşmiyor"
                )
            status = alanlar.get("status", "")
            if status not in KART_CIPLAK_STATUS_SOZLUGU and not status.startswith("DONE("):
                ihlaller["r12_kart_status_sozlugu"].append(
                    f"{konum}: status '{status}' {{ACTIVE,OPERATOR,DONE(...)}} sözlüğünde değil"
                )
            elif status.startswith("DONE("):
                ic = status[len("DONE(") : -1] if status.endswith(")") else None
                if ic is None or not re.match(
                    rf"^\d{{4}}-\d{{2}}-\d{{2}}·({'|'.join(KART_VERDICT_SOZLUGU)})$", ic
                ):
                    ihlaller["r07_done_dropped_tarih"].append(
                        f"{konum}: §6 DONE(...) 'tarih·{{GEÇTİ,KALDI,NO-GO}}' biçiminde değil: '{status}'"
                    )
            owner = alanlar.get("owner")
            if owner not in OWNER_SOZLUGU:
                ihlaller["r03_owner_sozlugu"].append(f"{konum}: owner '{owner}' sözlükte değil")
            continue

        # --- §0/§2/§3/§4/§5: TSK madde şeması ------------------------------------------------
        if anahtarlar != list(TSK_ALAN_SIRASI):
            ihlaller["r01_madde_grameri"].append(
                f"{konum}: alan sırası {TSK_ALAN_SIRASI} bekleniyordu, bulunan: {anahtarlar}"
            )

        if KART_KIMLIK_DESENI.match(kimlik):
            ihlaller["r10_kimlik_sizmasi"].append(
                f"{konum}: kart-ailesi kimliği ('{kimlik}') §6 DIŞINDA başlıkta GEÇEMEZ"
            )
        elif not TSK_KIMLIK_DESENI.match(kimlik):
            ihlaller["r09_tanimasiz_kimlik"].append(
                f"{konum}: kimlik '{kimlik}' TSK deseniyle eşleşmiyor"
            )
        else:
            ad_kayitlari[kimlik].add(ad)

        status = alanlar.get("status", "")
        temel = status.split("(", 1)[0].strip()
        if temel in CIPLAK_STATUS_SOZLUGU:
            if status != temel:
                ihlaller["r02_status_ciplak_parantezli"].append(
                    f"{konum}: '{temel}' parantezsiz olmalı, bulundu: '{status}'"
                )
        elif temel in PARANTEZLI_STATUS_ANAHTARLARI:
            m = re.match(rf"^{re.escape(temel)}\((.+)\)$", status)
            if not m or not m.group(1).strip():
                ihlaller["r06_parantezli_status_icerik_eksik"].append(
                    f"{konum}: '{temel}(...)' içi boş/eksik: '{status}'"
                )
            else:
                ic = m.group(1).strip()
                if temel in ("DONE", "DROPPED") and not re.match(r"^\d{4}-\d{2}-\d{2}", ic):
                    ihlaller["r07_done_dropped_tarih"].append(
                        f"{konum}: {temel}(...) parantez içi tarihle BAŞLAMIYOR: '{status}'"
                    )
                if temel == "GATED":
                    trig = alanlar.get("trigger", "")
                    if trig.strip() in ("", "—"):
                        ihlaller["r06_gated_trigger_alani_bos"].append(
                            f"{konum}: GATED ama trigger alanı somut değil: '{trig}'"
                        )
        else:
            ihlaller["r02_status_sozluk_disi"].append(f"{konum}: status '{status}' sözlükte yok")

        if temel != "GATED":
            trig = alanlar.get("trigger", "")
            if trig.strip() != "—":
                ihlaller["r08_gated_disi_trigger_dolu"].append(
                    f"{konum}: GATED değilken trigger '—' değil: '{trig}'"
                )

        owner = alanlar.get("owner")
        if owner not in OWNER_SOZLUGU:
            ihlaller["r03_owner_sozlugu"].append(f"{konum}: owner '{owner}' sözlükte değil")

        size = alanlar.get("size", "")
        if size not in SIZE_SOZLUGU and not SIZE_BELIRSIZ_DESENI.match(size):
            ihlaller["r04_size_sozlugu"].append(
                f"{konum}: size '{size}' {{S,M,L,S-M,M-L}} sözlüğünde DEĞİL ve "
                "belirsiz-boyut deseniyle ('—' ya da '— (...)') de eşleşmiyor"
            )

        born = alanlar.get("born", "")
        if not re.match(r"^\d{4}-\d{2}-\d{2}", born.strip()):
            ihlaller["r05_born_tarih_formati"].append(
                f"{konum}: born '{born}' YYYY-AA-GG ile başlamıyor"
            )

    for kimlik, adlar in ad_kayitlari.items():
        if len(adlar) > 1:
            ihlaller["r09_kimlik_tekilligi"].append(
                f"{kimlik}: birden fazla farklı ada bağlı: {sorted(adlar)}"
            )

    return dict(ihlaller)


def prg_tekillik_ihlallerini_bul(metin: str) -> list[str]:
    """PRG cephe kimliklerinin tekilliği: aynı `PRG-NN` numarası iki FARKLI cephe adına
    bağlanamaz. PRG bullet biçiminde DEĞİL `### PRG-NN — Ad` üst-başlık biçiminde yaşıyor
    (FAZ B raporu madde 3) — bu yüzden `madde_ihlallerini_bul`'dan AYRI, kendi tarayıcısı var."""
    kayitlar: dict[str, set[str]] = defaultdict(set)
    for satir in metin.splitlines():
        m = PRG_BASLIK_DESENI.match(satir)
        if m:
            kayitlar[m.group(1)].add(m.group(2).strip())
    ihlaller = []
    for kimlik, adlar in kayitlar.items():
        if len(adlar) > 1:
            ihlaller.append(f"{kimlik}: birden fazla farklı cephe adına bağlı: {sorted(adlar)}")
    return ihlaller


# ======================================================================================
# ortak sabitler — testler
# ======================================================================================


def _roadmap_metni() -> str:
    return ROADMAP_YOLU.read_text(encoding="utf-8")


def _tek_satirlik_sentetik(govde: str, kimlik: str = "TSK-900", bolum: str = "4") -> str:
    """Tek bir madde satırını, doğru bölüm içine sarılmış minimal bir ROADMAP parçası olarak
    üretir — böylece `_yasayan_madde_satirlari`nin bölüm-süzgeci gerçek koşulları taklit eder
    (yalnız satırı tek başına vermek `_hangi_bolum` None döndürür ve satır sessizce elenir)."""
    return f"## §{bolum} TEST BÖLÜMÜ\n\n- **[{kimlik}] test maddesi** — {govde}\n"


# ======================================================================================
# R01 — madde grameri: alan sırası/isimleri
# ======================================================================================


def test_r01_madde_grameri_gercek_dosya():
    ihlaller = madde_ihlallerini_bul(_roadmap_metni())
    assert ihlaller.get("r01_madde_grameri", []) == []


def test_r01_madde_grameri_sentetik_ihlal():
    metin = _tek_satirlik_sentetik("status: ACTIVE · owner: rol1 · size: S · trigger: —")
    ihlaller = madde_ihlallerini_bul(metin)  # born alanı eksik
    assert len(ihlaller.get("r01_madde_grameri", [])) == 1
    assert "TSK-900" in ihlaller["r01_madde_grameri"][0]


# ======================================================================================
# R02 — status sözlüğü: çıplak değer parantezsiz + tanımsız değer reddi
# ======================================================================================


def test_r02_status_ciplak_parantezli_gercek_dosya():
    # GÜNCELLEME 2026-09-01 (Rol-1 hükmü): TSK-001/058/060/066'nın açıklayıcı parantezleri
    # gövdeye ("What:" satırının başına `(status notu: ...)`) taşındı — header artık çıplak
    # ACTIVE/QUEUED. Önceki tur bu 4 satırı İSİMLİ pinlemişti (bilinen-ihlal); onarım
    # tamamlandığı için pin KALDIRILDI, sıfır-ihlal iddiasına dönüldü.
    ihlaller = madde_ihlallerini_bul(_roadmap_metni())
    assert ihlaller.get("r02_status_ciplak_parantezli", []) == []


def test_r02_status_ciplak_parantezli_sentetik_ihlal():
    metin = _tek_satirlik_sentetik(
        "status: ACTIVE (ek açıklama) · born: 2026-09-01 · owner: rol1 · size: S · trigger: —"
    )
    ihlaller = madde_ihlallerini_bul(metin)
    assert len(ihlaller.get("r02_status_ciplak_parantezli", [])) == 1


def test_r02_status_sozluk_disi_gercek_dosya():
    ihlaller = madde_ihlallerini_bul(_roadmap_metni())
    assert ihlaller.get("r02_status_sozluk_disi", []) == []


def test_r02_status_sozluk_disi_sentetik_ihlal():
    metin = _tek_satirlik_sentetik(
        "status: BLOKE · born: 2026-09-01 · owner: rol1 · size: S · trigger: —"
    )
    ihlaller = madde_ihlallerini_bul(metin)
    assert len(ihlaller.get("r02_status_sozluk_disi", [])) == 1


# ======================================================================================
# R03 — owner sözlüğü
# ======================================================================================


def test_r03_owner_sozlugu_gercek_dosya():
    ihlaller = madde_ihlallerini_bul(_roadmap_metni())
    assert ihlaller.get("r03_owner_sozlugu", []) == []


def test_r03_owner_sozlugu_sentetik_ihlal():
    metin = _tek_satirlik_sentetik(
        "status: ACTIVE · born: 2026-09-01 · owner: takim · size: S · trigger: —"
    )
    ihlaller = madde_ihlallerini_bul(metin)
    assert len(ihlaller.get("r03_owner_sozlugu", [])) == 1


# ======================================================================================
# R04 — size sözlüğü: {S,M,L,S-M,M-L} VEYA belirsiz-boyut deseni (`—` ya da `— (beyan)`).
# Spec §1 tarihli ek 2026-09-01 (Rol-1, FAZ C bulgusu → aynı gece giderildi): boyut
# ÖLÇÜLEMİYORSA `—` meşrudur — uydurma yasağı S/M/L uydurtmaktan üstündür.
# ======================================================================================


def test_r04_size_sozlugu_gercek_dosya():
    # GÜNCELLEME 2026-09-01 (Rol-1 hükmü): önceki tur bu kuralı spec'in ESKİ hâline göre
    # yazmıştı (yalnız §6'da "—" meşru) ve 16 satırı (TSK-021 + 15×"size: —") İSİMLİ
    # pinlemişti. Spec §1'e aynı gece tarihli ek geldi: "—" artık TÜM yaşayan bölümlerde
    # meşru. Kural buna göre genişletildi (SIZE_BELIRSIZ_DESENI); pin KALDIRILDI.
    ihlaller = madde_ihlallerini_bul(_roadmap_metni())
    assert ihlaller.get("r04_size_sozlugu", []) == []


def test_r04_size_sozlugu_sentetik_ihlal():
    """Hâlâ ihlal SAYILAN biçim: serbest metin, em-dash öneki OLMADAN (eski TSK-021 hâli:
    `size: karta bağlı`) — spec'in meşru kıldığı YALNIZ `—` ve `— (beyan)`, keyfi metin değil."""
    metin = _tek_satirlik_sentetik(
        "status: ACTIVE · born: 2026-09-01 · owner: rol1 · size: karta bağlı · trigger: —"
    )
    ihlaller = madde_ihlallerini_bul(metin)
    assert len(ihlaller.get("r04_size_sozlugu", [])) == 1


def test_r04_size_sozlugu_ara_deger_kabul_edilir():
    """Pozitif kontrol: `S-M`/`M-L` gibi tire'li ara değerler sözlükte VAR — reddedilmemeli."""
    metin = _tek_satirlik_sentetik(
        "status: ACTIVE · born: 2026-09-01 · owner: rol1 · size: S-M · trigger: —"
    )
    ihlaller = madde_ihlallerini_bul(metin)
    assert ihlaller.get("r04_size_sozlugu", []) == []


def test_r04_size_belirsiz_ciplak_kabul_edilir():
    """Pozitif kontrol (spec eki 2026-09-01): çıplak `—` artık TSK maddelerinde de meşru."""
    metin = _tek_satirlik_sentetik(
        "status: ACTIVE · born: 2026-09-01 · owner: rol1 · size: — · trigger: —"
    )
    ihlaller = madde_ihlallerini_bul(metin)
    assert ihlaller.get("r04_size_sozlugu", []) == []


def test_r04_size_belirsiz_parantezli_beyan_kabul_edilir():
    """Pozitif kontrol — gerçek TSK-021 biçimi: `— (boyut seçilecek yola bağlı — ölçülemez,
    beyanlı)`. Parantez içindeki ikinci bir '—' (tire, gerekçe metninde) desenle çakışmamalı."""
    metin = _tek_satirlik_sentetik(
        "status: ACTIVE · born: 2026-09-01 · owner: rol1 · "
        "size: — (boyut seçilecek yola bağlı — ölçülemez, beyanlı) · trigger: —"
    )
    ihlaller = madde_ihlallerini_bul(metin)
    assert ihlaller.get("r04_size_sozlugu", []) == []


# ======================================================================================
# R05 — born alanı YYYY-AA-GG ile başlar (trailing açıklama serbest — uydurma yasağı
# gereği FAZ A'nın "born tahmini: ..." dürüst-işaretli 11 satırı MEŞRU sayılır)
# ======================================================================================


def test_r05_born_tarih_formati_gercek_dosya():
    ihlaller = madde_ihlallerini_bul(_roadmap_metni())
    assert ihlaller.get("r05_born_tarih_formati", []) == []


def test_r05_born_tarih_formati_sentetik_ihlal():
    metin = _tek_satirlik_sentetik(
        "status: ACTIVE · born: eylül 2026 · owner: rol1 · size: S · trigger: —"
    )
    ihlaller = madde_ihlallerini_bul(metin)
    assert len(ihlaller.get("r05_born_tarih_formati", [])) == 1


def test_r05_born_trailing_aciklama_ihlal_SAYILMAZ():
    """Pozitif kontrol: `born: 2026-08-23 (born tahmini: ...)` gerçek dosyada 11 kez geçen
    DÜRÜST bir örüntü (uydurma yasağı: tahmin AÇIKÇA işaretlenmiş) — reddedilmemeli."""
    metin = _tek_satirlik_sentetik(
        "status: ACTIVE · born: 2026-08-23 (born tahmini: iz satırında tarih yok) "
        "· owner: rol1 · size: S · trigger: —"
    )
    ihlaller = madde_ihlallerini_bul(metin)
    assert ihlaller.get("r05_born_tarih_formati", []) == []


# ======================================================================================
# R06 — GATED: status içi parantez dolu + trigger alanı somut
# ======================================================================================


def test_r06_gated_trigger_alani_bos_gercek_dosya():
    ihlaller = madde_ihlallerini_bul(_roadmap_metni())
    assert ihlaller.get("r06_gated_trigger_alani_bos", []) == []


def test_r06_gated_trigger_alani_bos_sentetik_ihlal():
    metin = _tek_satirlik_sentetik(
        "status: GATED(operatör onayı) · born: 2026-09-01 · owner: rol1 · size: S · trigger: —"
    )
    ihlaller = madde_ihlallerini_bul(metin)
    assert len(ihlaller.get("r06_gated_trigger_alani_bos", [])) == 1


def test_r06_parantezli_status_icerik_eksik_gercek_dosya():
    ihlaller = madde_ihlallerini_bul(_roadmap_metni())
    assert ihlaller.get("r06_parantezli_status_icerik_eksik", []) == []


def test_r06_parantezli_status_icerik_eksik_sentetik_ihlal():
    metin = _tek_satirlik_sentetik(
        "status: GATED() · born: 2026-09-01 · owner: rol1 · size: S · trigger: bir şey"
    )
    ihlaller = madde_ihlallerini_bul(metin)
    assert len(ihlaller.get("r06_parantezli_status_icerik_eksik", [])) == 1


# ======================================================================================
# R07 — DONE/DROPPED: parantez içi tarihle başlar (§0-§5 VE §6, iki ayrı kod yolu)
# ======================================================================================


def test_r07_done_dropped_tarih_gercek_dosya():
    # GÜNCELLEME 2026-09-01 (Rol-1 hükmü): TSK-022 `DONE(v249·...)` → `DONE(2026-08-17·v249:
    # ...)` oldu — tarih git kanıtından (29d3ce1). Önceki tur bu tek satırı İSİMLİ pinlemişti;
    # onarım tamamlandı, pin KALDIRILDI.
    ihlaller = madde_ihlallerini_bul(_roadmap_metni())
    assert ihlaller.get("r07_done_dropped_tarih", []) == []


def test_r07_done_dropped_tarih_sentetik_ihlal_tsk():
    metin = _tek_satirlik_sentetik(
        "status: DONE(v351·her şey yolunda) · born: 2026-09-01 · owner: rol1 · size: S · trigger: —"
    )
    ihlaller = madde_ihlallerini_bul(metin)
    assert len(ihlaller.get("r07_done_dropped_tarih", [])) == 1


def test_r07_done_dropped_tarih_sentetik_ihlal_dropped():
    metin = _tek_satirlik_sentetik(
        "status: DROPPED(sürüm-yok-gerekçe-var) · born: 2026-09-01 · owner: rol1 · size: S · trigger: —"
    )
    ihlaller = madde_ihlallerini_bul(metin)
    assert len(ihlaller.get("r07_done_dropped_tarih", [])) == 1


def test_r07_kart_done_tarih_hukum_gercek_dosya():
    ihlaller = madde_ihlallerini_bul(_roadmap_metni())
    # §6 kod yolu da aynı sınıf anahtarını kullanır; gerçek dosyada sınıf artık boş (yukarıdaki
    # test zaten bunu doğruluyor) — bu test özellikle §6 payının da sıfır olduğunu isimli
    # kalıntı bırakmadan sabitler.
    assert all("EDG" not in s and "EXE" not in s and "KYS" not in s and "BASE" not in s
               for s in ihlaller.get("r07_done_dropped_tarih", []))


def test_r07_kart_done_tarih_hukum_sentetik_ihlal():
    metin = _tek_satirlik_sentetik(
        "status: DONE(GEÇTİ) · owner: rol1 · size: — · trigger: —",
        kimlik="EDG-2026-999",
        bolum="6",
    )
    ihlaller = madde_ihlallerini_bul(metin)
    assert len(ihlaller.get("r07_done_dropped_tarih", [])) == 1


def test_r07_kart_done_verdict_sozlugu_disi_sentetik_ihlal():
    metin = _tek_satirlik_sentetik(
        "status: DONE(2026-09-01·BELKİ) · owner: rol1 · size: — · trigger: —",
        kimlik="EDG-2026-998",
        bolum="6",
    )
    ihlaller = madde_ihlallerini_bul(metin)
    assert len(ihlaller.get("r07_done_dropped_tarih", [])) == 1


# ======================================================================================
# R08 — GATED DIŞINDA trigger tam olarak "—" olmalı
# ======================================================================================


def test_r08_gated_disi_trigger_dolu_gercek_dosya():
    ihlaller = madde_ihlallerini_bul(_roadmap_metni())
    assert ihlaller.get("r08_gated_disi_trigger_dolu", []) == []


def test_r08_gated_disi_trigger_dolu_sentetik_ihlal():
    metin = _tek_satirlik_sentetik(
        "status: ACTIVE · born: 2026-09-01 · owner: rol1 · size: S · trigger: bir gün olur"
    )
    ihlaller = madde_ihlallerini_bul(metin)
    assert len(ihlaller.get("r08_gated_disi_trigger_dolu", [])) == 1


# ======================================================================================
# R09 — TSK kimlik tekilliği (aynı numara ≠ farklı ad) + tanımsız kimlik biçimi
# ======================================================================================


def test_r09_kimlik_tekilligi_gercek_dosya():
    ihlaller = madde_ihlallerini_bul(_roadmap_metni())
    assert ihlaller.get("r09_kimlik_tekilligi", []) == []


def test_r09_kimlik_tekilligi_sentetik_ihlal():
    metin = (
        _tek_satirlik_sentetik(
            "status: ACTIVE · born: 2026-09-01 · owner: rol1 · size: S · trigger: —",
            kimlik="TSK-901",
        )
        + "\n- **[TSK-901] BAMBAŞKA bir ad** — status: QUEUED · born: 2026-09-01 · owner: rol1 · size: S · trigger: —\n"
    )
    ihlaller = madde_ihlallerini_bul(metin)
    assert len(ihlaller.get("r09_kimlik_tekilligi", [])) == 1


def test_r09_tanimasiz_kimlik_gercek_dosya():
    ihlaller = madde_ihlallerini_bul(_roadmap_metni())
    assert ihlaller.get("r09_tanimasiz_kimlik", []) == []


def test_r09_tanimasiz_kimlik_sentetik_ihlal():
    metin = _tek_satirlik_sentetik(
        "status: ACTIVE · born: 2026-09-01 · owner: rol1 · size: S · trigger: —",
        kimlik="ABC-1",
    )
    ihlaller = madde_ihlallerini_bul(metin)
    assert len(ihlaller.get("r09_tanimasiz_kimlik", [])) == 1


def test_r09_ayni_numara_ayni_ad_tekrari_ihlal_SAYILMAZ():
    """Pozitif kontrol: spec §2'nin bilinçli geri-bağlantı deseni (TSK-061/062/065/069 örneği,
    FAZ B raporu) — AYNI numara AYNI adla İCRA SIRASI'nda ve TAHTA'da tekrar edebilir."""
    metin = (
        "## §4 TEST BÖLÜMÜ\n\n"
        "- **[TSK-902] aynı ad** — status: ACTIVE · born: 2026-09-01 · owner: rol1 · size: S · trigger: —\n"
        "- **[TSK-902] aynı ad** — status: QUEUED · born: 2026-09-01 · owner: rol1 · size: S · trigger: —\n"
    )
    ihlaller = madde_ihlallerini_bul(metin)
    assert ihlaller.get("r09_kimlik_tekilligi", []) == []


# ======================================================================================
# R10 — kimlik biçimi §6 sızıntısı (kart-ailesi §6 dışında / TSK §6 içinde geçemez)
# ======================================================================================


def test_r10_kimlik_sizmasi_gercek_dosya():
    ihlaller = madde_ihlallerini_bul(_roadmap_metni())
    assert ihlaller.get("r10_kimlik_sizmasi", []) == []


def test_r10_kart_kimligi_disi_bolgede_sentetik_ihlal():
    metin = _tek_satirlik_sentetik(
        "status: ACTIVE · born: 2026-09-01 · owner: rol1 · size: S · trigger: —",
        kimlik="EDG-2026-777",
        bolum="4",
    )
    ihlaller = madde_ihlallerini_bul(metin)
    assert len(ihlaller.get("r10_kimlik_sizmasi", [])) == 1


def test_r10_tsk_kimligi_alti_bolgede_sentetik_ihlal():
    metin = _tek_satirlik_sentetik(
        "status: ACTIVE · owner: rol1 · size: — · trigger: —",
        kimlik="TSK-903",
        bolum="6",
    )
    ihlaller = madde_ihlallerini_bul(metin)
    assert len(ihlaller.get("r10_kimlik_sizmasi", [])) == 1


# ======================================================================================
# R11 — §6 kart kimlik biçimi (v219 AD_DESENI onek deseniyle eşleşmeli)
# ======================================================================================


def test_r11_kart_kimlik_bicimi_gercek_dosya():
    ihlaller = madde_ihlallerini_bul(_roadmap_metni())
    assert ihlaller.get("r11_kart_kimlik_bicimi", []) == []


def test_r11_kart_kimlik_bicimi_sentetik_ihlal():
    metin = _tek_satirlik_sentetik(
        "status: ACTIVE · owner: rol1 · size: — · trigger: —",
        kimlik="edg-2026-1",  # küçük harf + eksik basamak — desenle eşleşmez
        bolum="6",
    )
    ihlaller = madde_ihlallerini_bul(metin)
    assert len(ihlaller.get("r11_kart_kimlik_bicimi", [])) == 1


def test_r11_dort_kart_ailesi_de_meşru_gercek_dosya():
    """Pozitif kontrol — bu dosyanın kendi sapma kaydı: spec metni yalnız EDG/EXE der ama
    fiilî §6 BASE ve KYS de taşıyor; v219 tabanlı desen ikisini de kabul etmeli (0 ihlal)."""
    metin = _roadmap_metni()
    satirlar = metin.splitlines()
    sinirlar = _bolum_sinirlari(satirlar)
    aileler = set()
    for idx, satir in enumerate(satirlar):
        m = MADDE_SATIRI_DESENI.match(satir)
        if m and _hangi_bolum(idx, sinirlar) == "6":
            aileler.add(m.group(1).split("-", 1)[0])
    assert aileler == {"EDG", "EXE", "KYS", "BASE"}
    ihlaller = madde_ihlallerini_bul(metin)
    assert ihlaller.get("r11_kart_kimlik_bicimi", []) == []


# ======================================================================================
# R12 — §6 status sözlüğü {ACTIVE, OPERATOR, DONE(...)}
# ======================================================================================


def test_r12_kart_status_sozlugu_gercek_dosya():
    ihlaller = madde_ihlallerini_bul(_roadmap_metni())
    assert ihlaller.get("r12_kart_status_sozlugu", []) == []


def test_r12_kart_status_sozlugu_sentetik_ihlal():
    metin = _tek_satirlik_sentetik(
        "status: QUEUED · owner: rol1 · size: — · trigger: —",
        kimlik="EDG-2026-996",
        bolum="6",
    )
    ihlaller = madde_ihlallerini_bul(metin)
    assert len(ihlaller.get("r12_kart_status_sozlugu", [])) == 1


# ======================================================================================
# R03 tekrarı §6 için (owner sözlüğü zaten aynı fonksiyon üzerinden hem TSK hem kart yolunda
# çalışıyor — burada yalnız §6 koluna özel bir sentetik kanıt ekleniyor)
# ======================================================================================


def test_r03_kart_owner_sozlugu_sentetik_ihlal():
    metin = _tek_satirlik_sentetik(
        "status: ACTIVE · owner: herkes · size: — · trigger: —",
        kimlik="EDG-2026-995",
        bolum="6",
    )
    ihlaller = madde_ihlallerini_bul(metin)
    assert len(ihlaller.get("r03_owner_sozlugu", [])) == 1


# ======================================================================================
# R13 — bölüm muafiyeti: §1/§7/§8/§∞ hiç taranmaz (yanlış-pozitif kaynağı olabilirdi)
# ======================================================================================


def test_r13_bolum_muafiyeti_gercek_dosya_disi_bolumler_madde_uretmez():
    """§1/§7/§8/§∞ içindeki HERHANGİ bir `- **[` biçimli satır (varsa) ihlal üretmemeli —
    çünkü bu bölümler hiç taranmıyor. Dolaylı doğrulama: `_yasayan_madde_satirlari` yalnız
    YAŞAYAN bölüm anahtarlarını döndürür (aşağıdaki sentetik test bunu doğrudan sınar)."""
    metin = _roadmap_metni()
    satirlar = metin.splitlines()
    sinirlar = _bolum_sinirlari(satirlar)
    for idx, satir in enumerate(satirlar):
        if MADDE_SATIRI_DESENI.match(satir):
            bolum = _hangi_bolum(idx, sinirlar)
            if bolum in ("1", "7", "8", "∞"):
                pytest.fail(
                    f"satır {idx + 1}: muaf bölüm §{bolum} içinde madde-biçimli satır bulundu "
                    "— bu, muafiyet varsayımını çürütür, kapsam yeniden değerlendirilmeli"
                )


def test_r13_bolum_muafiyeti_sentetik_ihlal_yakalanmaz():
    """Aynı bozuk madde satırı §7 (muaf) içine konursa çivi SESSİZ kalmalı; §4 (yaşayan)
    içine konursa YAKALAMALI — muafiyet süzgecinin iki yönünü de kanıtlar."""
    bozuk_govde = "status: BLOKE · born: kötü-tarih · owner: kimse · size: XL · trigger: dolu"
    muaf_metin = _tek_satirlik_sentetik(bozuk_govde, kimlik="TSK-904", bolum="7")
    yasayan_metin = _tek_satirlik_sentetik(bozuk_govde, kimlik="TSK-905", bolum="4")

    muaf_ihlaller = madde_ihlallerini_bul(muaf_metin)
    yasayan_ihlaller = madde_ihlallerini_bul(yasayan_metin)

    assert muaf_ihlaller == {}, f"§7 muaf olmalıydı ama ihlal üretti: {muaf_ihlaller}"
    assert yasayan_ihlaller != {}, "§4 yaşayan bölüm aynı satırı yakalamalıydı"


# ======================================================================================
# R14 — PRG cephe kimlik tekilliği (### başlık biçimi, bullet DEĞİL)
# ======================================================================================


def test_r14_prg_tekilligi_gercek_dosya():
    ihlaller = prg_tekillik_ihlallerini_bul(_roadmap_metni())
    assert ihlaller == []


def test_r14_prg_tekilligi_gercek_dosya_on_bir_cephe_var():
    """Pozitif kontrol: FAZ B raporunun beyan ettiği 11 cephe (`PRG-01`..`PRG-11`) fiilen
    dosyada tanımlı — sıfır satır kalırsa test kendi kapsamının çürüdüğünü haber verir."""
    metin = _roadmap_metni()
    kimlikler = {m.group(1) for m in PRG_BASLIK_DESENI.finditer(metin)}
    assert kimlikler == {f"PRG-{n:02d}" for n in range(1, 12)}


def test_r14_prg_tekilligi_sentetik_ihlal():
    metin = (
        "### PRG-99 — İlk Ad\n\nbir şeyler\n\n### PRG-99 — Farklı bir Ad\n\ndaha fazla şey\n"
    )
    ihlaller = prg_tekillik_ihlallerini_bul(metin)
    assert len(ihlaller) == 1
    assert "PRG-99" in ihlaller[0]


# ======================================================================================
# Genel pozitif kontrol — tam uyumlu sentetik madde SIFIR ihlal üretir
# ======================================================================================


def test_tam_uyumlu_sentetik_madde_sifir_ihlal_uretir():
    metin = _tek_satirlik_sentetik(
        "status: GATED(operatör kararı) · born: 2026-09-01 · owner: rol1 · size: M · trigger: operatör onayı"
    )
    assert madde_ihlallerini_bul(metin) == {}


def test_tam_uyumlu_sentetik_kart_satiri_sifir_ihlal_uretir():
    metin = _tek_satirlik_sentetik(
        "status: DONE(2026-09-01·GEÇTİ) · owner: rol1 · size: — · trigger: —",
        kimlik="EDG-2026-994",
        bolum="6",
    )
    assert madde_ihlallerini_bul(metin) == {}


# ======================================================================================
# Toplam gerçek-dosya envanteri — brief'in "ihlal sayısı (varsa sınıflarıyla)" raporu
# ======================================================================================


def test_gercek_dosya_toplam_ihlal_envanteri_sifir():
    """TÜM kural sınıflarının gerçek dosyadaki toplamı — FAZ C taramasının kaydı.

    GÜNCELLEME 2026-09-01 (Rol-1 hükmü): FAZ C'nin ilk taraması 21 ihlal bulmuştu (3 sınıf:
    r02_status_ciplak_parantezli=4, r04_size_sozlugu=16, r07_done_dropped_tarih=1) ve bu test
    o kümeyi İSİMLİ pinliyordu. Rol-1 aynı gece üçünü de giderdi: (1) TSK-001/058/060/066'nın
    çıplak-status parantezleri gövdeye taşındı, (2) spec §1'e tarihli ek geldi — ölçülemeyen
    boyutta `size: —` artık MEŞRU (TSK-021 `— (beyanlı)` oldu, diğer 15 zaten body'de gerekçe
    taşıyordu), (3) TSK-022 → `DONE(2026-08-17·v249: …)` (tarih git kanıtı 29d3ce1). Taban
    0'a indi — bu sayı YÜKSELİRSE (yeni ihlal) test KIRILIR; düşmez çünkü zaten taban."""
    ihlaller = madde_ihlallerini_bul(_roadmap_metni())
    toplam = sum(len(v) for v in ihlaller.values())
    assert toplam == 0, f"beklenen taban 0 idi, ölçülen: {toplam} — sınıflar: {ihlaller}"
