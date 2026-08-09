"""WP-M M9 — K-cezası kalibrasyonuna Chen-2022 t-hurdle DENGELEME referans notu (v231, 2026-08-10).

NE ÇİVİLENİYOR. `meridian/analytics.py`'deki K-cezası okuma bölümüne (DSR n_trials tüketicisi
`validation_trio`nun hemen üstü) eklenen literatür referans NOTU. Not bir GEVŞETME değildir —
eşik/formül değişikliği taşımaz; K-cezası şeffaflığının metodoloji bacağıdır (keşif 2026-08-09
§WP-M M9; yüzey bacağı pano/F13, WP-UX'te ayrı).

NEDEN TESTLE ÇİVİLİ (YASA 6). Bir yorum bloğunun tek okuyucusu "bir sonraki mühendis"tir ve o
okuyucu yapısal değildir: gelecekte bir sadeleştirme turu bloğu sessizce süpürebilir. Depo deseni
(test_wpm_sasi_v173.test_D_prescreen_raporu_damgayi_TASIR, test_kovab_kucuk_v165'in birim-dosya
çivileri) beyanları KAYNAKTAN grep'le çiviler — aynı desen. Ayrıca notun İDDİASI da çivilenir:
"gevşetme değil" cümlesi ve künye-doğrulama şerhi (UYDURMA YASAĞI) nottan düşerse test kırmızıya
düşer — çünkü o iki cümle olmadan not, bir kalibrasyon tartışmasında yanlış tarafa (sessiz
gevşetme ruhsatına) okunabilir.
"""
import pathlib

SRC = pathlib.Path(__file__).resolve().parent.parent / "meridian"
ANALYTICS = (SRC / "analytics.py").read_text()


def test_m9_notu_VAR_ve_kunye_tam():
    """Künyenin üç parçası (yazar-soyadı / yıl / başlık) ayrı ayrı aranır: tek uzun dizgiyle
    aramak, satır kırılımı değişince sahte kırmızı üretirdi."""
    assert "Andrew Y. Chen" in ANALYTICS
    assert "Do t-Statistic Hurdles" in ANALYTICS
    assert "Chen (2022)" in ANALYTICS or "Chen 2022" in ANALYTICS


def test_m9_notu_GEVSETME_DEGIL_beyani_tasiyor():
    """Notun varlığı yetmez — "gevşetme değil" hükmü notun İÇİNDE yazılı olmalı. Referans, eşik
    tartışmasında tek başına "çıtayı indir" diye okunabilirdi; beyan bu okumayı kaynakta keser."""
    assert "GEVŞETME DEĞİL" in ANALYTICS
    assert "eşik sonradan değişmez" in ANALYTICS
    assert "kill-list dokunulmaz" in ANALYTICS


def test_m9_kunye_dogrulama_serhi_var():
    """UYDURMA YASAĞI şerhi: künye bellekten yazıldı; dergi/cilt bilgisi operatör doğrulaması
    olmadan EKLENMEZ. Şerh silinirse gelecekte birinin künyeye tahmini yayın yeri iliştirmesinin
    önünde yazılı engel kalmaz."""
    assert "operatör literatür doğrulaması" in ANALYTICS
    assert "UYDURMA YASAĞI şerhi" in ANALYTICS


def test_m9_notu_K_cezasi_tuketicisinin_BITISIGINDE():
    """Not, K-cezası okumalarının yaşadığı yerde durmalı: DSR n_trials tüketicisi `validation_trio`
    tanımından ÖNCE gelmeli (dosyanın ucuna savrulmuş bir not, ilgili kodu okuyana görünmez)."""
    not_konumu = ANALYTICS.index("Do t-Statistic Hurdles")
    trio_konumu = ANALYTICS.index("def validation_trio")
    assert not_konumu < trio_konumu, "M9 notu validation_trio'nun üstünde durmalı"
    # Not ile fonksiyon arasında başka bir fonksiyon tanımı OLMAMALI (bitişiklik iddiası).
    ara = ANALYTICS[not_konumu:trio_konumu]
    assert "\ndef " not in ara, "not ile validation_trio arasına başka tanım girmiş"
