"""KÖK ÇEVRİMİ — `/` yeni panoya geçti, eskisi ÖKSÜZ KALMADI · v298 (2026-08-25)

OPERATÖR KARARI: "yeni panoya geçelim". Kök (`/`) artık studio-admin panosunu sunuyor.

ÇEVRİMİN TEK GERÇEK RİSKİ ÖKSÜZ BIRAKMAKTIR. Eski pano bu depoda hâlâ canlı bir
yüzeydir: `app.js` 12.600 satır, on iki bölümün gövdesi orada ve yeni panoda henüz
karşılığı olmayan yollar var (ajana mesaj, belge arşivi, oturum ömrü). Kökü çevirip
eskisini adressiz bırakmak, o gövdeyi diskte tutup ulaşılamaz kılmak olurdu — dağıtıma
binen ama erişilemeyen ölü bayt, bu turda `pilot-workflow.html`de tam olarak yaşandı.

ÜÇ ADRES DE YAŞAMAK ZORUNDA:
  · `/`      → yeni pano (operatörün varsayılanı)
  · `/pano`  → yeni pano (bu turda operatöre VERİLEN adres; yer imi kırılmaz)
  · `/eski`  → eski pano (gövdesi hâlâ tek kaynak olan bölümler için)
"""
from __future__ import annotations

import re
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
API = (KOK / "meridian" / "api.py").read_text(encoding="utf-8")


def _rota_govdesi(yol: str) -> str:
    """`@app.get("<yol>"...)` ile başlayan uç fonksiyonunun gövdesini döndürür."""
    m = re.search(rf'@app\.get\("{re.escape(yol)}"[^)]*\)\s*\ndef\s+\w+\([^)]*\):(.*?)(?=\n@app\.|\n\ndef )',
                  API, re.S)
    assert m, f"`{yol}` rotası kaynakta bulunamadı"
    return m.group(1)


def test_kok_YENI_panoyu_sunuyor():
    assert "pano.html" in _rota_govdesi("/"), (
        "`/` hâlâ eski panoyu sunuyor — kök çevrimi geri alınmış olabilir")


def test_pano_adresi_KIRILMADI():
    """Operatöre bu turda `/pano` adresi verildi; çevrim onu geçersiz kılamaz."""
    assert "pano.html" in _rota_govdesi("/pano"), "`/pano` yer imi kırıldı"


def test_ESKI_pano_hala_ulasilabilir():
    """Öksüz bırakmama kuralı: eski gövde diskte duruyorsa bir adresi de OLMALI."""
    assert (KOK / "meridian" / "web" / "index.html").exists(), (
        "eski pano diskten silinmiş — bu çivinin varsayımı değişti, kararı gözden geçir")
    assert "index.html" in _rota_govdesi("/eski"), (
        "`/eski` eski panoyu sunmuyor — 12.600 satırlık gövde adressiz kaldı. "
        "Dağıtıma binen ama erişilemeyen bayt, bu depoda `pilot-workflow.html` vakasıdır.")


def test_eski_panonun_BETIKLERI_de_sunuluyor():
    """Sayfa ulaşılabilir olup betiği 404 alırsa yüzey ÖLÜ açılır — yarım erişim, erişim değildir."""
    for betik in ("/app.js", "/palette.js", "/theme.js"):
        assert f'@app.get("{betik}")' in API, (
            f"`{betik}` rotası yok — `/eski` çizilir ama iş görmez")
