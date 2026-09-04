"""v398 — TSK-117 K-3: 'başarı' anlamı seri rampasından (--color-seri-9) ayrıldı; seri jetonları yalnız
grafik/veri bileşenlerinde geçer. (TSK-117, 2026-09-03)

KÖRLÜK ALARMI (G3 incelemesinin bulgusu): tarama BOŞ dönerse -- `UI` yolu yanlış ya da glob hiç
dosya bulmuyorsa -- ihlal listesi de boş çıkar ve test SESSİZCE yeşil olur; bu, "seri jetonu hiçbir
yerde yok" ile "hiç dosya taranmadı" ayrımını kaybeder. Bu yüzden taranan dosya sayısı ölçülür ve
bir TABANLA karşılaştırılır (2026-09-03 ölçümü: ui/src altında 195 .tsx dosyası var; 100 tavanı bu
sayının yarısından azına düşerse -- bir dizin taşınır/yeniden adlandırılırsa -- kırmızı olsun diye
bilerek gevşek seçildi).
"""
import pathlib, re
from meridian import config

UI = pathlib.Path(config.ROOT) / "ui" / "src"
TARANAN_TABAN = 100  # ölçüldü 2026-09-03: 195 .tsx dosyası var; tavan körlüğü yakalayacak kadar gevşek
# seri jetonu izinli dosyalar (ölç, genişletme raporla):
#  - takimyildizi.tsx, Huni.tsx: G4 brief'inin verdiği örnekler (yıldız haritası + huni grafiği)
#  - "grafik"/"chart": genel isim deseni (bu turda TAM eşleşen dosya yok — `PozisyonGrafigi.tsx`,
#    `Grafikler.tsx` gibi Türkçe/köksüz varyantlar bu alt-dizgeyi TAŞIMIYOR; ölçüldü, aşağıya
#    açıkça eklendi, bu iki desen ileri kullanım/İngilizce adlandırma için tutuluyor)
#  - anasayfakartlari.tsx: TSK-117 K-3 turunda GENİŞLETİLDİ (ölçüldü) — `IslemlerKarti` bileşeni
#    (banka arka-plan işleri dağılımı) `processing`/`pending` durumlarını seri-6/seri-7 kimliğiyle
#    boyuyor; dosyanın "başarı" anlamlı DÖRT yeri (completed dahil) bu turda `basari`ye taşındı,
#    kalan seri-6/7 kategorik/veri kimliğidir (bkz. task-4-report.md §"anlam dışı" listesi).
#  - PozisyonSeyri.tsx: TSK-117 K-3 turunda GENİŞLETİLDİ (ölçüldü) — açık pozisyonların "giriş
#    yüzdesi" çizgi grafiği, her sembolü `var(--color-seri-N)` ile ayırt ediyor (`RAMPA_N=10`,
#    onda döner ve ekranda yazar); bu göç kapsamı DIŞINDA, dosyada emerald/green literal YOK.
#  - SeansTakvimi.tsx: TSK-117 K-4 turunda GENİŞLETİLDİ (ölçüldü, 2026-09-04) — takvim lejantının
#    `dongu` (gece döngüsü kaydı) işaretleyicisi `emerald-500`den `var(--color-seri-6)`e taşındı
#    (`tests/test_literal_renk_gocu_v397.py` emerald tavanı 4→0). "kosu" (hat koşusu) kardeş
#    işaretleyici akromatik `ring-primary` kalıyor — ikisi "başarı/başarısızlık" değil YALNIZ İKİ
#    KAYIT TÜRÜNÜ ayırt eden kategorik/dekoratif bir lejant (S1 ilkesi, VERİ kimliği — rol değil).
VERI_BILESENLERI = (
    "takimyildizi.tsx", "Huni.tsx", "grafik", "chart", "anasayfakartlari.tsx",
    "PozisyonSeyri.tsx", "SeansTakvimi.tsx",
)

def _tsx_dosyalari():
    return list(UI.rglob("*.tsx"))

def test_taranan_govde_taban_alti_degil():
    n = len(_tsx_dosyalari())
    assert n >= TARANAN_TABAN, (
        f"UI taraması yalnız {n} .tsx dosyası buldu (taban {TARANAN_TABAN}) — "
        f"yol yanlış olabilir (`{UI}`); boş/az tarama testi SESSİZCE yeşil yapar, kırmızı olması gerekir"
    )

def test_seri_jetonu_veri_disi_bilesende_yok():
    ihlal = []
    for p in _tsx_dosyalari():
        if any(k in str(p) for k in VERI_BILESENLERI): continue
        for m in re.finditer(r"var\(--color-seri-\d+\)|\bseri-\d+\b", p.read_text(encoding="utf-8")):
            ihlal.append(f"{p.relative_to(UI)}:{m.group(0)}")
    assert not ihlal, f"seri (veri kimliği) jetonu anlam taşıyan yüzeyde: {ihlal}"
