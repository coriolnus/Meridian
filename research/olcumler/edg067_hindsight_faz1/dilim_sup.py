# EDG-2026-067 SÜPÜRME dilimleyicisi — CLI'si EMEKLİ (TSK-115 düzeltme turu 1, ruling KRİTİK-2,
# 2026-09-03; bkz. alttaki "CLI SUPURME EMEKLI" bloğu). Bu dosya artık yalnız KÜTÜPHANE: saf
# dilimleme çekirdeği (`dilimle`/`_bloklar`/`_zorla_bol`/`_ilk_baslik`/`dilim_kimlikleri`) —
# `ingest067.py` bunu İTHAL eder (kopya değil). İçerik bayt-kayıpsızdır (dilimlerin birleşimi ==
# belge; çivi v366) — bu sözleşme DEĞİŞMEDİ, yalnız CLI (`main`) fail-closed hâle geldi.
import sys

ESIK_DILIM = 40_000   # bayt — dilim hedef tavanı (~10K token; başarıyla geçen en büyük sınıfın altı)


# ---- saf çekirdek (çivi: tests/test_edg067_dilim_v366.py) --------------------------------------

def _bloklar(metin: str) -> list[str]:
    """Metni önsöz + `## ` bölümlerine ayırır; ``` fence içindeki `## ` başlık SAYILMAZ.
    Blokların birleşimi girdiye bayt bayt eşittir (kayıpsızlık çekirdeği burada başlar)."""
    parcalar: list[str] = []
    mevcut: list[str] = []
    fence = False
    for satir in metin.splitlines(keepends=True):
        if satir.lstrip().startswith("```"):
            fence = not fence
        if satir.startswith("## ") and not fence and mevcut:
            parcalar.append("".join(mevcut))
            mevcut = []
        mevcut.append(satir)
    if mevcut:
        parcalar.append("".join(mevcut))
    return parcalar


def _zorla_bol(blok: str, esik: int) -> list[str]:
    """Tek başına eşiği aşan bloğu boş-satır (paragraf) sınırlarından böler; eşiği tek başına
    aşan paragraf kalırsa bayt düzeyinde kesilir (esnek tavan garantisi)."""
    paragraflar = blok.split("\n\n")
    # split birleştirilirken ayraçlar geri konur — kayıpsızlık için ayraçlı yeniden kurulum
    parcalar: list[str] = []
    for i, p in enumerate(paragraflar):
        parcalar.append(p + ("\n\n" if i < len(paragraflar) - 1 else ""))
    cikti: list[str] = []
    mevcut = ""
    for p in parcalar:
        while len(p.encode()) > esik:  # tek paragraf bile eşik üstü — kaba bayt kesimi
            if mevcut:
                cikti.append(mevcut)
                mevcut = ""
            kes = esik
            while kes > 0 and (p[:kes].encode() != p.encode()[:len(p[:kes].encode())]
                               or len(p[:kes].encode()) > esik):
                kes -= 1
            cikti.append(p[:kes])
            p = p[kes:]
        if mevcut and len((mevcut + p).encode()) > esik:
            cikti.append(mevcut)
            mevcut = p
        else:
            mevcut += p
    if mevcut:
        cikti.append(mevcut)
    return cikti


def _ilk_baslik(parca: str) -> str:
    for satir in parca.splitlines():
        if satir.startswith("## "):
            return satir[3:].strip()
    return ""


def dilimle(metin: str, esik: int = ESIK_DILIM) -> list[dict]:
    """Bölüm bloklarını eşiği aşmadan açgözlü paketler; dev bloğu paragraftan zorla böler.
    Dönen dilimlerin `metin` birleşimi girdiye EŞİTTİR; her dilim ilk bölüm başlığını taşır."""
    dilimler: list[str] = []
    mevcut = ""
    for blok in _bloklar(metin):
        if len(blok.encode()) > esik:
            if mevcut:
                dilimler.append(mevcut)
                mevcut = ""
            dilimler.extend(_zorla_bol(blok, esik))
            continue
        if mevcut and len((mevcut + blok).encode()) > esik:
            dilimler.append(mevcut)
            mevcut = blok
        else:
            mevcut += blok
    if mevcut:
        dilimler.append(mevcut)
    return [{"metin": d, "bolum": _ilk_baslik(d)} for d in dilimler]


def dilim_kimlikleri(yol: str, n: int) -> list[str]:
    """ROADMAP %237 emsali: URL-kodlu `#` + 1-tabanlı sıra."""
    return [f"{yol}%23dilim-{i}" for i in range(1, n + 1)]


# ---- CLI SUPURME EMEKLI (duzeltme turu 1, ruling KRITIK-2, 2026-09-03) -------------------------
# NEDEN: bu betigin `bitenler` kumesi durum alanina BAKMADAN `yol` isaretliyordu — ana yolun
# (ingest067.py) D4 gundemiyle yazdigi `basarisiz`/`dur` satirlarini da "bitmis" sayardi ve
# GERCEKTEN kalici basarisiz belgeleri bir daha asla denemezdi. AYRICA kendi kimlik semasi
# (`yol%23dilim-i`) ana yolun yeni semasindan (`yol#k/n`) FARKLI — ikisi birlikte kosarsa ayni
# icerik iki AYRI kimlikle iki kez LLM'e gonderilir (cift maliyet — EDG-067 kartinin tam
# amacinin tersi). Ana yol artik ESIK_DEV'in (50.000B) ALTINDA kalan --dilim-bayt varsayilaniyla
# (32.000B) devleri KENDISI diliyor; bu CLI'nin var olma nedeni (devleri ayri turda yakalamak)
# byuk olcude ana yola tasindi. BEDEL BEYANI: ESIK_DEV ile --dilim-bayt (32.000) arasinda kalan
# BOYUT BANDI (32.000B-50.000B) artik AYRI bir sifirlama turu almiyor — ana yolun kendi
# --dilim-bayt'i o bandi zaten 32K'lik dilimlere bolerek kapsiyor (ESIK_DEV=50.000 > 32.000).
# `dilimle()`/`_bloklar()`/`_zorla_bol()`/`_ilk_baslik()`/`dilim_kimlikleri()` KUTUPHANE olarak
# KALIR (yukaridaki saf cekirdek, v366 civileri degismedi, HALA YESIL). Yalniz CLI (`main`)
# fail-closed: `--kuru` DAHIL, hicbir bayrakla calismaz — kuru-kosum bile cakisan kimlik semasi
# uretebileceginden guvenli sayilmiyor.

def main(argv: list[str] | None = None) -> int:
    """SUPURME EMEKLI — HER ZAMAN 2 doner, ag/dosya G/C'sine HIC dokunmaz (TSK-115, 2026-09-03)."""
    sys.stderr.write("süpürme emekli (TSK-115): dilimleme ana yolda — ingest067.py kullan\n")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
