"""test_mutborc_guard_validate_change_v148.py — H5 TEST-BORCU: guard.validate_change mutant kümesi.

NEDEN BU DOSYA VAR: `mutmut` bu tek fonksiyonda **163 hayatta-kalan mutant** saydı. Hayatta kalmak
demek "kodu bozdum, hiçbir test fark etmedi" demektir; yani guard'ın yasalarının çoğu YAZILI ama
KORUNMUYORDU. Guard bu deponun tek SERT kısıtı (Hard Rule 6: LLM'e verilen talimat öneridir,
validator kısıttır) — kısıtın kendisi ölçülmeden duruyorsa, kısıt yoktur.

Buradaki her test bir mutasyon SINIFINI hedefler, bir satırı değil. Sınıflar:
  A. bileşik (composite) yolu       — 2..26   (yön değiştirme, şekil hükmü, yetki-açılmadı yasası)
  B. "changes" sözlüğü / tek-değişken — 28..42
  C. eksik alan hükmü               — 51..60
  D. base@regime ayrıştırması       — 68..97
  E. değişmezlik bloğu (goal/limits) — 98..116
  F. bounds üyeliği                 — 119..124
  G. sayıya çevrilebilirlik         — 138..144
  H. NaN/sonsuz hükmü               — 145..160
  I. tip (int) hükmü                — 163..171
  J. aralık + adım sınırları        — 172..185
  K. `old` çözümü (rejim-etkin)     — 189..197
  L. no-op hükmü                    — 204
  M. daha önce denenip düşmüş öneri — 211..239
  N. aylık kota                     — 242..250
  O. Verdict alanlarının taşınması  — 251..271

TESTLERİN KESKİNLİK KURALI: bir mutant `Verdict(None, ...)` yazdığında `ok` None olur ve `not v.ok`
hâlâ doğrudur — bu yüzden her yerde `v.ok is False` / `v.ok is True` kullanılır. Aynı şekilde
`Verdict(False, None)` gibi mutantlar ancak `v.reasons[0]` OKUNURSA düşer; gerekçe metnine dokunmayan
bir test bu sınıfı hiç görmez.

ÖLÇÜLEN SONUÇ (iddia değil, ölçüm — 2026-08-01): 163 hayatta-kalan mutantın gövdesi
`mutants/meridian/guard.py`'den tek tek çıkarılıp gerçek modülün ad uzayına enjekte edildi ve bu
dosyadaki 64 test her biri için koşturuldu: **161 ÖLDÜ, 2 YAŞADI**. Yaşayan ikisi aşağıda eşdeğer
ilan edilen 150 ve 153'tür — yani bu kümede öldürülebilir mutant KALMADI. Ölçüm yerel bir koşum
düzeneğiyle yapıldı (`mutmut` yeniden koşulmadı; tam mutasyon turu Rol-1'in tek-otoriter işidir),
dolayısıyla resmî mutmut skorunun tazelenmesi hâlâ Rol-1'e ait bir adımdır.

EŞDEĞER — ÖLDÜRÜLEMEZ (YASA 4 ruhu: sessiz geçiştirme yok, gerekçesiyle kayda geçiyor):
  * mutant 150 — `float("inf")` → `float("INF")`
  * mutant 153 — `float("-inf")` → `float("-INF")`
    Gerekçe: CPython'un `float()` ayrıştırıcısı "inf"/"INF"/"Inf" ve "-inf"/"-INF" dizgilerini BÜYÜK-
    KÜÇÜK HARF DUYARSIZ okur (`float("INF") == float("inf")` → True). İki mutant da birebir aynı
    değeri üretir, dolayısıyla gözlemlenebilir hiçbir davranış farkı yoktur. Bunları "öldüren" bir
    test ancak `guard.py` kaynağını dizge olarak okuyup literal'e bakarak yazılabilirdi — bu bir
    DAVRANIŞ testi olmaz, kaynak kodun fotokopisi olur ve refactor'da yalancı kırmızı üretir.
  * mutant 125 — mutmut'ta `timeout` olarak damgalı (survived değil); bu dosyanın kapsamı dışında.

KAPSAM DIŞI (bilerek): `composite_shape_reasons` ve `_on_step` kendi mutant kümelerine sahip; burada
yalnız `validate_change`'in onlara verdiği argümanlar ve döndürdüğü hüküm sınanır.

Fikstürler tamamen SENTETİK ve saftır: validate_change defter/ağ/dosya kanalı olmayan bir fonksiyondur
(guard'ın SAF-KALMA yasası), dolayısıyla tmp-state'e bile ihtiyaç yoktur — canlı `state/` okunmaz,
yazılmaz.
"""
from __future__ import annotations

import math

import pytest

from meridian import config
from meridian.guard import validate_change


# --------------------------------------------------------------------------------------------
# SENTETİK FİKSTÜRLER — gerçek bounds.yaml'ın ŞEKLİNİ taklit eder, DEĞERLERİNİ değil.
# `sentetik.kaba_adim` bilerek uydurma bir düğmedir: int adım kuralının float toleransıyla
# ayrıştığı tek bölgeyi (adım ≥ 1e6) sınamak için var; adı "sentetik." önekiyle o niyeti beyan eder.
# --------------------------------------------------------------------------------------------
BOUNDS = {
    "entry.min_score": {"min": 50, "max": 100, "step": 1, "type": "int"},
    "exit.profit_target_r": {"min": 2.0, "max": 5.0, "step": 0.25, "type": "float"},
    "exit.trail_atr": {"min": 1.0, "max": 4.0, "step": 0.5, "type": "float"},
    "regime.adx_min": {"min": 10, "max": 40, "step": 1, "type": "int"},
    "sentetik.kaba_adim": {"min": 0, "max": 4_000_000, "step": 2_000_000, "type": "int"},
}

PARAMS = {
    "entry.min_score": 62,
    "exit.profit_target_r": 2.5,
    "regime.adx_min": 20,
    "sentetik.kaba_adim": 0,
    # DİKKAT: "exit.trail_atr" bilerek YOK — @regime override'ının sessizce düşeceği hâli sınar.
}

GOAL = {"max_accepted_changes_per_month": 8}


def _vc(proposal, *, params=None, bounds=None, goal=None, hypotheses=None,
        accepted=0, params_by_regime=None):
    """Tek çağrı sarmalayıcı — her testin YALNIZ değiştirdiği eksen okunur kalsın diye."""
    return validate_change(
        proposal,
        dict(PARAMS) if params is None else params,
        dict(BOUNDS) if bounds is None else bounds,
        dict(GOAL) if goal is None else goal,
        [] if hypotheses is None else hypotheses,
        accepted,
        params_by_regime,
    )


# ============================================================================================
# A. BİLEŞİK (composite) YOLU — mutant 2..26
# ============================================================================================
def test_a1_gecerli_bilesik_kuyruga_yonlendirilir_ama_YETKI_ACILMAZ():
    """Sınıf 2-5 (anahtar kayması), 8 (comp→None), 9-11 (argüman düşürme), 22-26 (Verdict alanları).

    Yasa: bileşik öneri REDDEDİLMEZ, kuyruğa YÖNLENDİRİLİR — ama dönüş yine ok=False'tur. Mutant 26
    (`Verdict(True, ...)`) tam olarak bu yetkiyi sessizce açardı: bileşik bir demet canlıya
    girebilirdi. `is False` şart; `not v.ok` mutant 22'yi (`ok=None`) kaçırır.
    """
    v = _vc({"composite": {"entry.min_score": 60, "exit.profit_target_r": 2.5}})
    assert v.ok is False
    assert v.reasons[0].startswith("composite_pending_queue: ")
    assert "2 düğme" in v.reasons[0]
    assert "YAPILMADI" in v.reasons[0]      # canlı değişiklik yok hükmü metinde DURUYOR


def test_a2_sekli_bozuk_bilesik_kuyruga_DEGIL_ret_hukmune_gider():
    """Sınıf 7 (`nedenler = None` → şekil hükmü yutulur), 12-21 (Verdict/gerekçe metni).

    İki düğme de sınır dışı → composite_shape_reasons İKİ gerekçe üretir; ayırıcı "; " mutant 21'de
    "XX; XX" olur, bu yüzden gerekçe dizgesinde "XX" ARANIR (mutmut'un dizge işareti).
    """
    v = _vc({"composite": {"entry.min_score": 999, "exit.profit_target_r": 99.0}})
    assert v.ok is False
    assert v.reasons[0].startswith("composite_rejected_shape: ")
    assert "XX" not in v.reasons[0]
    assert "entry.min_score" in v.reasons[0] and "exit.profit_target_r" in v.reasons[0]
    assert "; " in v.reasons[0]
    assert "composite_pending_queue" not in v.reasons[0]


def test_a3_tek_dugmeli_bilesik_bilesik_sayilmaz():
    """Şekil hükmünün ayrı bir dalı: 1 düğme bileşik değildir — kuyruğa DEĞİL, ret'e gider."""
    v = _vc({"composite": {"entry.min_score": 60}})
    assert v.ok is False
    assert v.reasons[0].startswith("composite_rejected_shape: ")
    assert "tek düğme" in v.reasons[0]


def test_a4_BOS_composite_alani_bilesik_yolunu_ACMAZ():
    """Sınıf 6: `isinstance(comp, dict) and comp` → `or`.

    Boş sözlük yanlıştır ama BİLEŞİK DEĞİLDİR; `or` mutantı boş bir alanı bile bileşik sayıp normal
    tek-değişken önerisini "composite_rejected_shape" ile çöpe atardı. Yani zararsız bir artık alan,
    geçerli bir hipotezi öldürürdü.
    """
    v = _vc({"variable": "entry.min_score", "new": 55, "composite": {}})
    assert v.ok is True
    assert v.reasons == []
    assert v.variable == "entry.min_score" and v.new == 55


# ============================================================================================
# B. "changes" SÖZLÜĞÜ / TEK-DEĞİŞKEN YASASI — mutant 28..42
# ============================================================================================
def test_b1_changes_sozlugundeki_tek_degisken_okunur():
    """Sınıf 28-29 (anahtar kayması → "proposal missing"), 31 (koşul tersine), 38-42 (unpack/anahtar)."""
    v = _vc({"changes": {"entry.min_score": 58}})
    assert v.ok is True
    assert v.reasons == []
    assert v.variable == "entry.min_score"
    assert v.old == 62 and v.new == 58


def test_b2_iki_degisken_tek_degisken_yasasini_dusurur():
    """Sınıf 31-32 (sayı sınırı: `!= 1` → `== 1` / `!= 2`), 33-37 (Verdict alanları).

    Mutant 32 iki düğmeli bir demeti sessizce kabul edip İLKİNİ ölçerdi: ölçülen ile önerilen ayrışır,
    defter yalan söyler.
    """
    v = _vc({"changes": {"entry.min_score": 58, "exit.profit_target_r": 3.0}})
    assert v.ok is False
    assert v.reasons[0] == "more than one variable changed (2); one_variable_only"


def test_b3_uc_degisken_de_ayni_hukme_carpar():
    """`!= 2` mutantının 2'de kalmadığını, sayının GENEL olduğunu çivi."""
    v = _vc({"changes": {"entry.min_score": 58, "exit.profit_target_r": 3.0, "exit.trail_atr": 2.0}})
    assert v.ok is False
    assert "more than one variable changed (3)" in v.reasons[0]


# ============================================================================================
# C. EKSİK ALAN HÜKMÜ — mutant 51..60
# ============================================================================================
def test_c1_new_eksikse_gerekce_EKSIK_ALAN_dir_sayi_hatasi_degil():
    """Sınıf 51 (`or` → `and`), 54-60 (Verdict/dizge).

    `and` mutantı eksik `new`i eksik alan olarak değil "sayı değil" olarak raporlardı — defterde
    yanlış terminal sınıf: LLM'in şema hatası, veri hatası gibi görünürdü.
    """
    v = _vc({"variable": "entry.min_score", "new": None})
    assert v.ok is False
    assert v.reasons == ["proposal missing variable/new"]


def test_c2_variable_eksikse_de_ayni_terminal():
    v = _vc({"new": 55})
    assert v.ok is False
    assert v.reasons == ["proposal missing variable/new"]


def test_c3_bos_oneri_de_ayni_terminal():
    v = _vc({})
    assert v.ok is False
    assert v.reasons == ["proposal missing variable/new"]


# ============================================================================================
# D. base@regime AYRIŞTIRMASI — mutant 68..97
# ============================================================================================
def test_d1_bilinmeyen_rejim_reddedilir_ve_variable_TAM_ADIYLA_tasinir():
    """Sınıf 73-79. `variable=` düşen mutantlar (78) Verdict'i kimliksiz bırakır: defter satırı
    hangi düğmenin reddedildiğini kaybeder."""
    v = _vc({"variable": "entry.min_score@bogus", "new": 55})
    assert v.ok is False
    assert v.reasons[0].startswith("unknown regime 'bogus'")
    assert str(config.VALID_REGIMES) in v.reasons[0]
    assert v.variable == "entry.min_score@bogus"


def test_d2_ikinci_at_isareti_COKME_degil_ret_uretir():
    """Sınıf 68 (`split("@")` maxsplit'siz), 69 (`rsplit`), 71 (`maxsplit=2`).

    'a@chop@trend_up' iki '@' taşır. maxsplit=1 yasası: SOLDAKİ ilk '@' böler, kalanın tamamı rejim
    ADIDIR ve geçersizdir. maxsplit'i kaldıran/2 yapan mutantlar unpack hatasıyla ÇÖKER; `rsplit`
    mutantı ise 'trend_up'u geçerli rejim sanıp bambaşka bir gerekçeye sapar.
    """
    v = _vc({"variable": "entry.min_score@chop@trend_up", "new": 55})
    assert v.ok is False
    assert v.reasons[0].startswith("unknown regime 'chop@trend_up'")


def test_d3_canli_paramlarda_olmayan_base_icin_override_reddedilir():
    """Sınıf 81-86. 'exit.trail_atr' bounds'ta VAR ama canlı params'ta YOK: override sessizce
    düşerdi, aday == mevcut olurdu, kapı reddederdi ve defter YALANCI bir çıkmaz sokak yazardı."""
    v = _vc({"variable": "exit.trail_atr@chop", "new": 2.0})
    assert v.ok is False
    assert "is not in the live strategy params" in v.reasons[0]
    assert "@chop" in v.reasons[0]
    assert v.variable == "exit.trail_atr@chop"


def test_d4_regime_onekli_dugmenin_override_u_YAPISAL_olarak_reddedilir():
    """Sınıf 89-97. Rejim tespiti rejim bilinmeden koşar → `regime.*` override'ı asla etki edemez."""
    v = _vc({"variable": "regime.adx_min@trend_up", "new": 25})
    assert v.ok is False
    assert "rejim tespitinin kendisini besler" in v.reasons[0]
    assert "@trend_up" in v.reasons[0]
    assert v.variable == "regime.adx_min@trend_up"


def test_d5_regime_oneki_DUZ_dugmede_engel_degildir():
    """89/90'ın (dizge kayması) ters yönü: "regime.adx_min" override anahtarı düz hâliyle ayarlanabilir bir düğmedir.
    Dizge mutantı bu yolu da bozmasın diye olumlu kontrol."""
    v = _vc({"variable": "regime.adx_min", "new": 25})
    assert v.ok is True and v.reasons == []
    assert v.old == 20 and v.new == 25


# ============================================================================================
# E. DEĞİŞMEZLİK BLOĞU — mutant 98..116
# ============================================================================================
@pytest.mark.parametrize("ad", ["min_sharpe", "max_drawdown", "execution_v2", "pessimistic_band_v2"])
def test_e1_goal_anahtarlari_degismezdir(ad):
    """Sınıf 100 (`or` → `and`, GOAL_KEYS dalını komple ölü bırakır), 112-116 (Verdict alanları)."""
    v = _vc({"variable": ad, "new": 3})
    assert v.ok is False
    assert "is immutable (goal/limits block)" in v.reasons[0]
    assert v.variable == ad


@pytest.mark.parametrize("ad", ["max_position_r", "autonomy_level", "heat_hard_r"])
def test_e2_limit_anahtarlari_degismezdir(ad):
    """Sınıf 99: `base in LIMIT_KEYS and base.startswith("limits.")` — limit adları önekli GELMEZ,
    yani `and` mutantı LIMIT_KEYS dalını tamamen kapatır ve ajan kendi risk tavanını önerebilirdi.
    (25a mezar taşı 2026-08-23: parametre `kill_switch_file` → `heat_hard_r` — ölü anahtar
    LIMIT_KEYS'ten ve goal.yaml'dan kaldırıldı; mutasyon kapsamı için herhangi bir LIMIT_KEYS
    üyesi eşdeğerdir.)"""
    v = _vc({"variable": ad, "new": 3})
    assert v.ok is False
    assert "is immutable (goal/limits block)" in v.reasons[0]
    assert v.variable == ad


@pytest.mark.parametrize("ad", ["limits.max_open_positions", "limits.max_daily_loss_pct"])
def test_e3_limits_onekli_her_sey_degismezdir(ad):
    """Sınıf 98 (`or` → `and`), 104-105 (önek dizgesi)."""
    v = _vc({"variable": ad, "new": 3})
    assert v.ok is False
    assert "is immutable (goal/limits block)" in v.reasons[0]


@pytest.mark.parametrize("ad", ["goal", "bounds"])
def test_e4_goal_ve_bounds_dosyalarinin_kendisi_degismezdir(ad):
    """Sınıf 107-110: demetin İKİ üyesi ayrı ayrı sınanır; tek üyeyi test etmek diğerini serbest
    bırakırdı (ajan 'bounds' düğmesini önerip sınırların kendisini genişletmeye kalkabilirdi)."""
    v = _vc({"variable": ad, "new": 3})
    assert v.ok is False
    assert "is immutable (goal/limits block)" in v.reasons[0]
    assert v.variable == ad


# ============================================================================================
# F. bounds ÜYELİĞİ — mutant 119..124
# ============================================================================================
def test_f1_bounds_disi_ad_ayarlanabilir_degildir():
    v = _vc({"variable": "tamamen.bilinmeyen_dugme", "new": 3})
    assert v.ok is False
    assert v.reasons[0] == "'tamamen.bilinmeyen_dugme' is not a tunable variable in bounds.yaml"
    assert v.variable == "tamamen.bilinmeyen_dugme"


# ============================================================================================
# G. SAYIYA ÇEVRİLEBİLİRLİK — mutant 138..144
# ============================================================================================
def test_g1_cop_deger_COKME_degil_GEREKCELI_RET_uretir():
    """Sınıf 138-144. Bu yolun tamamı 2026-07-22'de "istisna atmak hiçbir defter satırı bırakmıyordu"
    bulgusuyla eklendi; mutant 144 (`ok=True`) onu tam tersine çevirir: çöp değer canlıya geçerdi."""
    v = _vc({"variable": "entry.min_score", "new": "abc"})
    assert v.ok is False
    assert "sayı değil (reddedildi, çökme değil)" in v.reasons[0]
    assert "'abc'" in v.reasons[0]          # !r biçimi: tırnaklı ham değer defterde görünür
    assert v.variable == "entry.min_score"


def test_g2_sayiya_cevrilebilen_dizge_REDDEDILMEZ():
    """Olumlu kontrol: '58' bir sayıdır. Ret dalını genişleten bir mutasyon bunu da düşürürdü."""
    v = _vc({"variable": "entry.min_score", "new": "58"})
    assert v.ok is True and v.reasons == []
    assert v.new == 58 and isinstance(v.new, int)


# ============================================================================================
# H. NaN / SONSUZ HÜKMÜ — mutant 145..160
# ============================================================================================
def test_h1_NaN_sonlu_sayi_degildir():
    """Sınıf 145 (`or` → `and`): NaN aralık kontrolünü SESSİZCE geçer (nan<lo ve nan>hi ikisi de
    False); onu yakalayan tek şey adım kontrolünün TESADÜFEN çökmesiydi — yani bir kural değil, bir
    hataydı. `and` mutantı o hatalı hâle geri döndürür."""
    v = _vc({"variable": "exit.profit_target_r", "new": float("nan")})
    assert v.ok is False
    assert "sonlu bir sayı değil (NaN/sonsuz)" in v.reasons[0]
    assert v.variable == "exit.profit_target_r"


@pytest.mark.parametrize("deger", [float("inf"), float("-inf")])
def test_h2_sonsuzluk_aralik_gerekcesiyle_DEGIL_sonluluk_gerekcesiyle_duser(deger):
    """Sınıf 145 + 154-160. +inf aralık kontrolüne düşse de gerekçe 'out of range' OLMAMALI: sonsuz
    bir öneri bir sınır ihlali değil, bir TİP ihlalidir ve defterde öyle sınıflanmalıdır."""
    v = _vc({"variable": "exit.profit_target_r", "new": deger})
    assert v.ok is False
    assert "sonlu bir sayı değil (NaN/sonsuz)" in v.reasons[0]
    assert not any("out of range" in r for r in v.reasons)


# ============================================================================================
# I. TİP (int) HÜKMÜ — mutant 163..171
# ============================================================================================
def test_i1_int_dugmede_kesirli_deger_gerekce_uretir():
    """Sınıf 163-164 (tip dizgesi kayması → hüküm ölür), 166 (`reasons.append(None)`)."""
    v = _vc({"variable": "entry.min_score", "new": 55.5})
    assert v.ok is False
    assert v.reasons[0] == "entry.min_score=55.5 must be int"


def test_i2_int_dugmede_donen_deger_INT_TIPINDE_olur():
    """Sınıf 170-171: `new = int(_num) if typ == "int" else _num` dizgesi kayarsa Verdict 58.0 taşır.
    Aşağı akış (defter, prescreen, strateji yaması) bunu float olarak yazar — 58.0 ile 58 aynı sayıdır
    ama aynı KAYIT değildir; `isinstance` olmadan bu sınıf görünmez (58.0 == 58 zaten True)."""
    v = _vc({"variable": "entry.min_score", "new": 58.0})
    assert v.ok is True and v.reasons == []
    assert v.new == 58 and isinstance(v.new, int)


def test_i3_float_dugmede_kesirli_deger_dogaldir():
    """Olumlu kontrol: tip hükmü YALNIZ int düğmelere uygulanır."""
    v = _vc({"variable": "exit.profit_target_r", "new": 3.25})
    assert v.ok is True and v.reasons == []
    assert v.new == 3.25


# ============================================================================================
# J. ARALIK + ADIM SINIRLARI — mutant 172..185
# ============================================================================================
def test_j1_aralik_disi_deger_reddedilir_ve_old_new_TASINIR():
    """Sınıf 172 (`or` → `and`, aralık hükmünü komple ölü bırakır), 175 (gerekçe None),
    251-260 (gerekçeli dönüşün alan taşıması).

    DİKKAT: 10 değeri lo=50'ye göre TAM ADIM ÜSTÜNDEDİR (k=-40), yani `and` mutantı adım dalına da
    takılmaz ve ok=True döner — aralık dışı bir değer canlıya girerdi.
    """
    v = _vc({"variable": "entry.min_score", "new": 10})
    assert v.ok is False
    assert v.reasons[0] == "entry.min_score=10 out of range [50, 100]"
    assert v.variable == "entry.min_score"
    assert v.old == 62 and v.new == 10


def test_j2_ust_sinir_disi_da_reddedilir():
    v = _vc({"variable": "entry.min_score", "new": 101})
    assert v.ok is False
    assert "out of range [50, 100]" in v.reasons[0]


def test_j3_ALT_SINIRIN_KENDISI_gecerlidir():
    """Sınıf 173 (`new < lo` → `new <= lo`): sınırın KENDİSİ aralığın İÇİDİR. Bu mutant aramanın
    ulaşabileceği uzayı sessizce daraltır — bounds.yaml'da yazan minimum asla denenemezdi."""
    v = _vc({"variable": "entry.min_score", "new": 50})
    assert v.ok is True and v.reasons == []
    assert v.new == 50


def test_j4_UST_SINIRIN_KENDISI_de_gecerlidir():
    v = _vc({"variable": "entry.min_score", "new": 100})
    assert v.ok is True and v.reasons == []
    assert v.new == 100


def test_j5_adim_disi_deger_reddedilir():
    """Sınıf 185 (`reasons.append(None)`) + adım gerekçesinin metni."""
    v = _vc({"variable": "exit.profit_target_r", "new": 3.3})
    assert v.ok is False
    assert v.reasons[0] == "exit.profit_target_r=3.3 off-step (step=0.25 from 2.0)"


def test_j6_int_dugmenin_adim_hukmu_INT_kuraliyla_verilir():
    """Sınıf 180: `_on_step(new, lo, step, typ)` → `typ=None`.

    `_on_step`'in float dalı toleransı ADIMLA ÖLÇEKLER (`tol * max(1, |step|)`), int dalı ise mutlak
    1e-6 ister. İkisi ancak adım ~1e6'yı aştığında ayrışır: adım 2.000.000 iken float dalı 1 birimlik
    sapmayı "adım üstünde" sayar. Fikstür bilerek sentetiktir (bu tek ayrışma bölgesine nişan alır);
    sınanan yasa gerçektir: int düğmede adım hükmü ADIMIN BÜYÜKLÜĞÜYLE GEVŞEMEZ.
    """
    v = _vc({"variable": "sentetik.kaba_adim", "new": 1})
    assert v.ok is False
    assert "off-step (step=2000000 from 0)" in v.reasons[0]


# ============================================================================================
# K. `old` ÇÖZÜMÜ (rejim-etkin) — mutant 189..197
# ============================================================================================
def test_k1_duz_dugmede_no_op_yakalanir():
    """Sınıf 196-197 (`old = None` / `current_params.get(None)`): `old` kaybolursa no-op hükmü ölür
    ve hiçbir şeyi değiştirmeyen bir 'hipotez' backtest kuyruğuna girip ölçüm bütçesi yakar."""
    v = _vc({"variable": "entry.min_score", "new": 62})
    assert v.ok is False
    assert v.reasons[0] == "entry.min_score no-op: already 62"
    assert v.old == 62


@pytest.mark.parametrize("pbr", [None, {}, {"trend_up": {}}, {"chop": {"entry.min_score": 70}}])
def test_k2_override_YOKKEN_rejim_etkin_old_DUZ_degerdir(pbr):
    """Sınıf 189/191/195: `.get(base, current_params.get(base))` varsayılanı düşerse `old` None olur.

    O rejimde override yokken sürü DÜZ değerle işlem yapar; düz değeri yeniden önermek no-op'tur.
    Mutant bunu 'gerçek değişiklik' sayıp ölçüme yollardı — ve ölçüm aday==mevcut olduğu için
    kaçınılmaz olarak 'fark yok' derdi: defterde YALANCI bir çıkmaz sokak.
    """
    v = _vc({"variable": "entry.min_score@trend_up", "new": 62}, params_by_regime=pbr)
    assert v.ok is False
    assert v.reasons[0] == "entry.min_score@trend_up no-op: already 62"
    assert v.old == 62


def test_k3_override_VARKEN_rejim_etkin_old_OVERRIDE_degeridir():
    v = _vc({"variable": "entry.min_score@trend_up", "new": 70},
            params_by_regime={"trend_up": {"entry.min_score": 70}})
    assert v.ok is False
    assert v.reasons[0] == "entry.min_score@trend_up no-op: already 70"
    assert v.old == 70


def test_k4_override_u_DUZ_degere_geri_almak_no_op_DEGILDIR():
    """Yasanın asıl amacı: 70'lik bir override'ı 62'ye (düz değere) çekmek O REJİMDE gerçek bir
    davranış değişikliğidir. Düz-değerle kıyaslayan eski hâl bunu 'no-op' sayıp KÖTÜ BİR OVERRIDE'I
    GERİ ALINAMAZ yapıyordu."""
    v = _vc({"variable": "entry.min_score@trend_up", "new": 62},
            params_by_regime={"trend_up": {"entry.min_score": 70}})
    assert v.ok is True and v.reasons == []
    assert v.old == 70 and v.new == 62


# ============================================================================================
# L. NO-OP HÜKMÜNÜN TİP KURALI — mutant 204
# ============================================================================================
def test_l1_no_op_karsilastirmasi_DUGMENIN_TIPIYLE_yapilir():
    """Sınıf 204: `_equalish(old, new, typ)` → `typ=None`.

    int düğmede eşitlik TAM SAYI eşitliğidir: canlı değer 62.5 iken 62 önerisi motorun gözünde AYNI
    değerdir (ikisi de int(62)'ye iner) ve gerçek bir değişiklik değildir. `typ` düşünce karşılaştırma
    float'a kayar, 0.5'lik fark 'değişiklik' sanılır ve ölçüm bütçesi boşa yanar.
    """
    v = _vc({"variable": "entry.min_score", "new": 62}, params={"entry.min_score": 62.5})
    assert v.ok is False
    assert v.reasons[0] == "entry.min_score no-op: already 62.5"


# ============================================================================================
# M. DAHA ÖNCE DENENİP DÜŞMÜŞ ÖNERİ — mutant 211..239
# ============================================================================================
def test_m1_backtestte_reddedilmis_ayni_degisiklik_tekrar_denenmez():
    """Sınıf 211-229 + 232-239. Gerekçe metninin İÇİ de sınanır: hipotez kimliği ve durumu defterde
    görünmezse (mutant 233-238) operatör 'hangi denemede düştü' sorusunu cevaplayamaz.

    Sınıf 239 (`break` → `return`) özellikle sinsi: fonksiyon Verdict yerine None döndürür; `v.ok`
    okunmadıkça hiçbir test bunu görmez.
    """
    hyp = [{"id": "H7", "variable": "entry.min_score", "new": 55, "status": "rejected_by_backtest"}]
    v = _vc({"variable": "entry.min_score", "new": 55}, hypotheses=hyp)
    assert v.ok is False
    assert v.reasons[0] == ("entry.min_score=55 already tried and failed "
                            "(hyp H7, rejected_by_backtest)")


def test_m2_geri_alinmis_degisiklik_de_tekrar_denenmez():
    """Sınıf 230-231: durum demetinin İKİNCİ üyesi ayrı sınanır — yalnız 'rejected_by_backtest'
    testi yazmak 'rolled_back' dalını korumasız bırakırdı (canlıda geri alınmış bir değişiklik
    sınırsız kez yeniden önerilebilirdi)."""
    hyp = [{"id": "H9", "variable": "exit.profit_target_r", "new": 3.0, "status": "rolled_back"}]
    v = _vc({"variable": "exit.profit_target_r", "new": 3.0}, hypotheses=hyp)
    assert v.ok is False
    assert v.reasons[0] == ("exit.profit_target_r=3.0 already tried and failed "
                            "(hyp H9, rolled_back)")


def test_m3_eslesme_DUGMENIN_TIPIYLE_yapilir():
    """Sınıf 217: `_equalish(h["new"], new, typ)` → `typ=None`. int düğmede 55.5 ile 55 AYNI denemedir
    (ikisi de int(55)); tip düşünce geçmiş deneme görünmez olur ve aynı ölçüm tekrar tekrar koşar."""
    hyp = [{"id": "H11", "variable": "entry.min_score", "new": 55.5, "status": "rolled_back"}]
    v = _vc({"variable": "entry.min_score", "new": 55}, hypotheses=hyp)
    assert v.ok is False
    assert "already tried and failed (hyp H11, rolled_back)" in v.reasons[0]


def test_m4_BASKA_dugmenin_gecmisi_bu_oneriyi_engellemez():
    """Sınıf 214 (`==` → `!=`) ters yönden: eşleşme adı da GÖZETİR. `!=` mutantı ilgisiz bir
    hipotezle her öneriyi bloke ederdi — arama tamamen durur, kimse fark etmez."""
    hyp = [{"id": "H7", "variable": "exit.profit_target_r", "new": 55, "status": "rolled_back"}]
    v = _vc({"variable": "entry.min_score", "new": 55}, hypotheses=hyp)
    assert v.ok is True and v.reasons == []


def test_m5_TERMINAL_OLMAYAN_durum_engel_degildir():
    """Durum demeti bir BEYAZ listedir: 'accepted'/'measuring' geçmişi yeni öneriyi bloke etmez."""
    hyp = [{"id": "H7", "variable": "entry.min_score", "new": 55, "status": "accepted"},
           {"id": "H8", "variable": "entry.min_score", "new": 55, "status": "measuring"}]
    v = _vc({"variable": "entry.min_score", "new": 55}, hypotheses=hyp)
    assert v.ok is True and v.reasons == []


# ============================================================================================
# N. AYLIK KOTA — mutant 242..250
# ============================================================================================
def test_n1_kota_SINIRIN_KENDISINDE_dolar():
    """Sınıf 249 (`>=` → `>`): kota 3 iken 3. kabul zaten YAPILMIŞTIR; `>` mutantı ayda bir fazla
    değişikliğe izin verir — 'ayda en çok N' sözleşmesi sessizce N+1 olur.
    Ayrıca sınıf 242/246/247: anahtar kayarsa varsayılan 8'e düşer ve goal.yaml'ın kotası hiç okunmaz.
    """
    v = _vc({"variable": "entry.min_score", "new": 55},
            goal={"max_accepted_changes_per_month": 3}, accepted=3)
    assert v.ok is False
    assert v.reasons[0] == "monthly accepted-change quota spent (3/3)"


def test_n2_kota_altinda_engel_yok():
    v = _vc({"variable": "entry.min_score", "new": 55},
            goal={"max_accepted_changes_per_month": 3}, accepted=2)
    assert v.ok is True and v.reasons == []


def test_n3_goal_kotayi_soylemezse_VARSAYILAN_8_dir():
    """Sınıf 243/245 (varsayılan düşer → `int(None)` çöker), 248 (8 → 9).

    Varsayılanın DEĞERİ sözleşmedir: 9'a kayarsa kotasız bir goal.yaml ayda bir fazla değişikliğe
    izin verir. Sınırın kendisinde ölçülür, yoksa 8↔9 farkı görünmez.
    """
    v = _vc({"variable": "entry.min_score", "new": 55}, goal={}, accepted=8)
    assert v.ok is False
    assert v.reasons[0] == "monthly accepted-change quota spent (8/8)"


def test_n4_varsayilan_kotanin_bir_altinda_engel_yok():
    v = _vc({"variable": "entry.min_score", "new": 55}, goal={}, accepted=7)
    assert v.ok is True and v.reasons == []


# ============================================================================================
# O. Verdict ALANLARININ TAŞINMASI — mutant 251..271
# ============================================================================================
def test_o1_temiz_oneride_TUM_alanlar_dolu_doner():
    """Sınıf 263 (`reasons=None`), 265-266 (`old`/`new` None), 270-271 (kwarg düşürme).

    `ok=True` yeterli değildir: çağıran (memory.record_hypothesis / prescreen) old ve new'i DEFTERE
    yazar. Alan None gelirse hipotez 'neyden neye' bilgisi olmadan kaydedilir ve geri alma yolu
    kaybolur — hiçbir şey kırmızı yanmadan.
    """
    v = _vc({"variable": "exit.profit_target_r", "new": 3.0})
    assert v.ok is True
    assert v.reasons == []
    assert v.variable == "exit.profit_target_r"
    assert v.old == 2.5
    assert v.new == 3.0


def test_o2_gerekceli_donuste_de_TUM_alanlar_dolu_doner():
    """Sınıf 251/253/254/255/258/259/260 — reddedilen bir aday da 'neyden neye' bilgisiyle
    kaydedilir; reddin kendisi de bir ÖLÇÜMDÜR."""
    v = _vc({"variable": "exit.profit_target_r", "new": 9.0})
    assert v.ok is False
    assert v.variable == "exit.profit_target_r"
    assert v.old == 2.5
    assert v.new == 9.0
    assert "out of range" in v.reasons[0]


def test_o3_reasons_LISTEDIR_ve_ok_ile_tutarlidir():
    """Bütün mutant kümesinin üzerinden geçen çapraz çivi: ok=True ⇔ reasons boş."""
    for oneri, params_by_regime in [
        ({"variable": "entry.min_score", "new": 58}, None),
        ({"variable": "entry.min_score", "new": 62}, None),
        ({"variable": "entry.min_score", "new": 10}, None),
        ({"variable": "entry.min_score@trend_up", "new": 55}, {"trend_up": {}}),
        ({"composite": {"entry.min_score": 60, "exit.trail_atr": 2.0}}, None),
    ]:
        v = _vc(oneri, params_by_regime=params_by_regime)
        assert isinstance(v.reasons, list)
        assert all(isinstance(r, str) and r for r in v.reasons)
        assert v.ok is (len(v.reasons) == 0)


def test_o4_fonksiyon_SAFTIR_girdi_sozluklerini_degistirmez():
    """Guard'ın SERT ZARF yasası: verdict yalnız argümanlarının fonksiyonudur. Yan etki (girdi
    mutasyonu) bu yasanın en ucuz ihlalidir ve hiçbir gerekçe listesinde görünmez."""
    params = dict(PARAMS)
    bounds = {k: dict(v) for k, v in BOUNDS.items()}
    goal = dict(GOAL)
    hyp = [{"id": "H1", "variable": "entry.min_score", "new": 55, "status": "rolled_back"}]
    pbr = {"trend_up": {"entry.min_score": 70}}
    before = (dict(params), {k: dict(v) for k, v in bounds.items()}, dict(goal),
              [dict(h) for h in hyp], {k: dict(v) for k, v in pbr.items()})

    _vc({"variable": "entry.min_score@trend_up", "new": 55},
        params=params, bounds=bounds, goal=goal, hypotheses=hyp, params_by_regime=pbr)

    assert params == before[0]
    assert bounds == before[1]
    assert goal == before[2]
    assert hyp == before[3]
    assert pbr == before[4]


def test_o5_ayni_girdi_ayni_hukum():
    """Determinizm: kapı iki tarafı kıyaslıyor; guard gürültü üretirse kıyas anlamsızdır."""
    oneri = {"variable": "entry.min_score", "new": 55.5}
    a = _vc(oneri)
    b = _vc(oneri)
    assert (a.ok, a.reasons, a.variable, a.old, a.new) == (b.ok, b.reasons, b.variable, b.old, b.new)


def test_o6_NaN_hukmu_math_isnan_ile_de_dogrulanir():
    """`_num != _num` deyiminin NaN'ı gerçekten yakaladığının bağımsız çivisi (math.isnan ile)."""
    deger = float("nan")
    assert math.isnan(deger)
    v = _vc({"variable": "entry.min_score", "new": deger})
    assert v.ok is False
    assert "sonlu bir sayı değil" in v.reasons[0]
