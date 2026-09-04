"""v397 — TSK-117 K-2: literal Tailwind renk sınıfları anlam jetonlarına göçer; sayım aile başına
YALNIZ DÜŞER (bedel yasası: her dilim önce/sonra). Tavanlar ölçüm günü (2026-09-03) değerleridir,
göç dilimi ailesini 0'a çeker. (TSK-117, 2026-09-03)"""
import pathlib, re
from meridian import config

UI = pathlib.Path(config.ROOT) / "ui" / "src"
DESEN = re.compile(r"\b(?:bg|text|border|ring|from|to|fill|stroke)-(amber|emerald|green|red|sky)-[0-9]{2,3}\b")
# Görev 3 sonrası: amber 0. Görev 4: green 0, emerald 4 (KAPANMADI — bilerek, aşağı bkz).
# Görev 5: red 0. Görev 6: sky 0.
#
# red İKİ AİLEYE BÖLÜNDÜ (Görev 5, TSK-117 K-2c, ölçüldü 2026-09-04): 31 kullanımın (5 konum,
# 9'u) `kritik` (hata/eşleşmedi/izin-yok/oturum-kapalı/risk anlamı — sev-1 bandı), (10 konum,
# 22'si) `--yon-eksi` (K/Z'nin NEGATİF ucu, `--yon-arti`nin zaten kurulu bracket eşi: `pnlRengi`/
# `kzSinifi`/`kzDolgusu`/`kzOrnegi`/`upl`/`sapmaYuzde`/`gross_loss` — hepsi pozitif dalında ZATEN
# `text-[var(--yon-arti)]` kullanıyordu, task-4-report.md §10'un öngördüğü simetrik liste).
# Tavan yine de 0: iki aile de literal `red-*` DEĞİL (task-5-6-report.md §"yön-eksi adayı").
#
# sky (Görev 6, TSK-117 K-2d, ölçüldü 2026-09-04): 12 kullanımın TAMAMI `bilgi` — 3 dosyanın
# ikisi ("kanal" tipi muhatap rozeti) kategorik-bilgi rozeti, biri (SohbetHatti.tsx sabitlenmiş
# ders kartı) bilgi çağrı-kutusu; "gezinme/aktif sekme" ya da veri serisi ANLAMI TAŞIYAN kullanım
# YOK (spec §2 S3 kararıyla 195° ailesi zaten BİLGİ rezervinde, gezinme 210°-232° ayrı bant).
#
# emerald KAPANDI (Görev 4 → K-4 tamamlama, TSK-117, ölçüldü 2026-09-04): Görev 4'te
# `SeansTakvimi.tsx` takvim lejantındaki `dongu` (gece döngüsü kaydı) işaretleyicisi BİLEREK
# `emerald-500`de bırakılmıştı — "kosu" (hat koşusu) kardeş işaretleyici `ring-primary` (nötr
# marka rengi) taşıyor, yani ikisi de "başarı/başarısızlık" değil YALNIZ İKİ KAYIT TÜRÜNÜ
# ayırt eden bir takvim lejantıydı (kategorik/dekoratif, S1 ilkesi) ve `basari`ye taşımak
# "gece döngüsü kaydı VAR" ile "iyi sonuçlandı" anlamlarını karıştırırdı. K-4 (palet turu,
# 2026-09-04) bu ayrımı `basari`ya değil VERİ jetonuna taşıyarak çözdü: `dongu` artık
# `var(--color-seri-6)` (teal, `ui/src/tema.css`in çok-serili rampası) kullanıyor — "kosu"nun
# akromatik `ring-primary`sinden ayırt edilebilir ama hiçbir rol anlamı (başarı/uyarı/kritik)
# taşımıyor; `tests/test_basari_seri9_ayrildi_v398.py::VERI_BILESENLERI` bu yüzden
# `SeansTakvimi.tsx`i de kapsar (seri jetonu artık orada da yaşıyor). Tavan bu yüzden 0'a
# çekildi — göç UYDURULMADI, kalan 4 kullanım GERÇEKTEN taşındı (ölçüldü, yukarıdaki `_sayim`).
LITERAL_TAVAN = {"amber": 0, "emerald": 0, "green": 0, "red": 0, "sky": 0}
ESLEME = {"amber": "uyari", "emerald": "basari", "green": "basari", "red": "kritik", "sky": "bilgi"}

def _sayim():
    s = {k: 0 for k in LITERAL_TAVAN}
    for p in UI.rglob("*.tsx"):
        for m in DESEN.finditer(p.read_text(encoding="utf-8")):
            s[m.group(1)] += 1
    return s

def test_literal_sinif_sayimi_tavani_asmaz():
    s = _sayim()
    asan = {k: (v, LITERAL_TAVAN[k]) for k, v in s.items() if v > LITERAL_TAVAN[k]}
    assert not asan, f"literal renk sınıfı geri geldi (aile: (bulunan, tavan)): {asan} — jeton: {ESLEME}"

def test_gocen_aileler_anlam_utility_kullaniyor():
    # 0'a çekilmiş her aile için en az bir dosya karşılık gelen utility'yi kullanmalı (göç silme değil dönüştürme)
    metin = "\n".join(p.read_text(encoding="utf-8") for p in UI.rglob("*.tsx"))
    for aile, tavan in LITERAL_TAVAN.items():
        if tavan == 0:
            assert re.search(rf"\b(?:bg|text|border|ring)-{ESLEME[aile]}(?:-t|-h)?\b", metin), \
                f"{aile} 0'a indi ama {ESLEME[aile]} utility'si hiç kullanılmıyor — sınıflar silinmiş, dönüştürülmemiş"


TARANAN_TABAN = 100  # ölçüldü 2026-09-03: 195 .tsx dosyası; taban körlüğü yakalayacak kadar gevşek (v398 emsali)


def test_taranan_govde_taban_alti_degil():
    """Körlük alarmı (G3 incelemesi KÜÇÜK → G4 incelemesi ÖNEMLİ; TSK-117, 2026-09-03): `UI.rglob`
    boş/az dönerse sayım {0,…} ile bütün tavanların altında kalır ve tavan çivisi SESSİZCE yeşil
    olur — az tarama kırmızı olmalı."""
    n = sum(1 for _ in UI.rglob("*.tsx"))
    assert n >= TARANAN_TABAN, (
        f"UI taraması yalnız {n} .tsx dosyası buldu (taban {TARANAN_TABAN}) — yol yanlış olabilir (`{UI}`)"
    )
