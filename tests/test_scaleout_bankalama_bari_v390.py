"""test_scaleout_bankalama_bari_v390.py — TSK-075: bankalama barında breakeven ratchet'i AYNI BAR
stop_gap üretmemeli (2026-09-03).

KUSURUN MEKANİĞİ (EDG-2026-029 kartında ÖLÇÜLDÜ, `research/cards/EDG-2026-029-scaleout-duzeltilmis.yaml`):
`PaperBroker.scale_out` `frac` kadar hisseyi bankalayınca kalanı breakeven'e ratchetliyordu
(`pos.trail_stop = max(pos.trail_stop, pos.entry)`) ve çağıranların HEPSİ (canlı `loop` INTRADAY(D),
`backtest.replay`, `shadow_lifecycle`) hemen ardından AYNI BAR için `_touch_exit` çağırıyordu. Barın
açılışı entry'nin ALTINDAysa (pozisyon önceki bardan taşınıyor ya da entry = open×(1+slip) > open),
o barın açılışı bir anda "yeni" stop'un altında kalıyor ve koşucu, bankalamayı doğuran yükselişi hiç
göremeden `stop_gap`le açılış fiyatından kesiliyordu. Ratchet GERİYE dönük uygulanıyordu: bar içinde
sonradan öğrenilen bir seviye, barın ZATEN basılmış ilk fiyatına karşı kullanılıyordu.

ÖLÇÜLMÜŞ BÜYÜKLÜK (EDG-2026-029, kart `verdict`): düzeltmenin KENDİ etkisi F1x−H1 = +0,0874R
CI[+0,034; +0,153]; `bars_held=0` ile kapanan scaled işlem 18 → 2; kusurun R imzası ≈0,7346
(ENPH sınıfı: +12,3R → 0,72R). Kavramın kendisi CI-negatif ölçüldüğü için `exit.scale_out_frac`
canlıda 0,0'dır — kusur LATENT'ti (893 işlemde `scaled_out` 0).

BU DOSYANIN SINADIĞI SÖZLEŞME (motor karşılığı, `meridian/broker.py`):
  1. Bankalama barında `_touch_exit` BANKALAMA-ÖNCESİ eff_stop ile çalışır → aynı-bar `stop_gap` YOK.
  2. Ratchet KAYBOLMAZ: `pos.trail_stop` bankalama anında breakeven'e çekilir (v24 k2b sözleşmesi)
     ve bir SONRAKİ bardan itibaren tam olarak etkir.
  3. İşaret TEK ATIMLIKtır: bankalama barının `_touch_exit`i onu tüketir, bar dışına taşmaz.
  4. `frac=0` yolunda davranış BİREBİR: işaret hiç kurulmaz, `eff_stop` bugünküyle aynı ifadedir.
"""
from __future__ import annotations

import dataclasses

import pytest

from meridian.broker import PaperBroker, Position

# EDG-2026-029 ölçüm şasisinin SENTETİK GİRDİLERİ (research/olcumler/edg029_scaleout_fix_2026-08-12/
# olcum.py `_poz`/`BAR_GIRIS`/`BAR_SASI`/`KOL` ile BİREBİR) — çivi, ölçümün kanıtladığı davranışı
# motor dosyasında arar; sayılar oradan gelir, uydurulmaz.
KOL = {"exit.scale_out_frac": 0.5, "exit.scale_out_r": 1.5}          # ½ @ 1.5R → level 107.5
# bankalama barı, KUSUR ŞEKLİ: açılış entry'nin ALTINDA (99.95 < 100), high 1.5R seviyesini görüyor
BAR_KUSUR = {"open": 99.95, "high": 108.0, "low": 99.9}
# bankalama barı, kusurun GÖRÜNMEDİĞİ şekil: açılış entry'nin ÜSTÜNDE
BAR_SASI = {"open": 101.0, "high": 108.0, "low": 100.5}
BANKED_BEKLENEN = round(50 * (107.5 * (1 - 0.0005) - 100.0), 2)      # 372.31 (kayma fiyatın İÇİNDE)
KUSUR_R_IMZASI = 0.7346                                              # kart: aynı-bar kesilen koşucunun R'ı


def _brk() -> PaperBroker:
    """Ölçüm şasisiyle aynı defter: 5 bps kayma, komisyon 0 (goal ile aynı)."""
    return PaperBroker(100_000.0, 5.0, 0.0)


def _poz(target: float = 112.5, trail: float = 95.0, scaled: bool = False) -> Position:
    """EDG-029 `_poz` ile birebir: giriş 100 / sert stop 95 / R 5 / 100 adet."""
    p = Position(plan_id="V390", ticker="_ST", side="long", entry=100.0, stop=95.0,
                 trail_stop=trail, target=target, qty=100, r_per_share=5.0,
                 risk_dollars=500.0, size_r=1.0, ts_open="2026-01-02")
    p.scaled_out = scaled
    return p


def _yuru(b: PaperBroker, pos: Position, bars: list[dict], params: dict):
    """Üç çağıranın (loop INTRADAY(D) · backtest.replay · shadow_lifecycle) BİREBİR çağrı dizisi:
    `scale_out` → `_touch_exit` → (çıkış yoksa) `bars_held++`. Sıra burada TAŞINMAZ; düzeltmenin
    çağıranları değiştirmeden çalışması gereken sözleşme tam olarak budur."""
    for bar in bars:
        b.scale_out(pos, bar, params)
        ex = b._touch_exit(pos, bar)
        if ex:
            return ex
        pos.bars_held += 1
    return None


# =================================================================================================
# K1 — KUSUR SENARYOSU: bankalama barında aynı-bar stop_gap ÜRETİLMEZ
# =================================================================================================

def test_k1_bankalama_bari_ayni_bar_stop_gap_uretmez():
    """ASIL ÇİVİ. Bankalama ateşler, ratchet kurulur, AMA aynı barın dokunuş kontrolü bankalama
    ÖNCESİ eff_stop (95) ile yapılır → açılış 99.95 stop'un altında DEĞİLDİR, koşucu YAŞAR.

    Kusurlu kodda: ratchet trail'i 100'e çeker, `_touch_exit` `o(99.95) <= eff_stop(100)` görür ve
    barın açılışından `stop_gap` yazar (ölçülmüş R imzası ≈0,7346)."""
    b = _brk()
    pos = _poz()
    assert b.scale_out(pos, BAR_KUSUR, KOL) is True, "kusur senaryosunda bankalama ateşlemedi"
    assert pos.scaled_out is True and pos.qty == 50, "bankalama muhasebesi (qty) bozuldu"
    assert pos.banked_pnl == pytest.approx(BANKED_BEKLENEN, abs=1e-9), "bankalanan P&L değişti"
    ex = b._touch_exit(pos, BAR_KUSUR)
    assert ex is None, f"KUSUR YAŞIYOR: bankalama barında koşucu kesildi ({ex})"


def test_k1b_kusurun_olculmus_r_imzasi_artik_uretilmiyor():
    """Kartın imzası (≈0,7346R) kusurun PARMAK İZİdir: bankalanan yarı + açılıştan kesilen yarı.
    Düzeltmeden sonra bu kapanış hiç DOĞMAZ; imzayı üretecek çıkış yoktur."""
    b = _brk()
    pos = _poz()
    assert b.scale_out(pos, BAR_KUSUR, KOL) is True
    if b._touch_exit(pos, BAR_KUSUR) is not None:
        exit_fill = BAR_KUSUR["open"] * (1 - 0.0005)
        r = (pos.banked_pnl + pos.qty * (exit_fill - pos.entry)) / pos.risk_dollars
        pytest.fail(f"kusurun R imzası yeniden üretildi: {r:.4f} (kart: ~{KUSUR_R_IMZASI})")


def test_k1c_kusurun_gorunmedigi_sasi_bari_da_yasar():
    """Açılış entry'nin ÜSTÜNDEyken kusur zaten görünmüyordu — düzeltme bu yolu DEĞİŞTİRMEMELİ."""
    b = _brk()
    pos = _poz()
    assert b.scale_out(pos, BAR_SASI, KOL) is True
    assert b._touch_exit(pos, BAR_SASI) is None, "şasi barında koşucu kesilmemeliydi"


# =================================================================================================
# K2 — RATCHET KAYBOLMADI: sonraki bardan itibaren breakeven TAM etkir
# =================================================================================================

def test_k2_bankalama_aninda_trail_breakevene_cekilir():
    """v24 `test_k2b_scale_out_ratchets_to_breakeven` sözleşmesi: ratchet ERTELENMEZ, `pos.trail_stop`
    bankalama anında entry'ye çekilir. Ertelenen tek şey ratchet'in AYNI BARA uygulanmasıdır —
    değerin kendisi anında yazılır, yani hiçbir okuyucu (pano, ayna, `manage_position`, serileştirme)
    bayat bir stop görmez ve ratchet bir kaydetme/yükleme arasında KAYBOLAMAZ."""
    b = _brk()
    pos = _poz()
    once = pos.trail_stop
    assert b.scale_out(pos, BAR_KUSUR, KOL) is True
    assert pos.trail_stop >= once and pos.trail_stop >= pos.entry, "ratchet kayboldu"
    assert pos.trail_stop == pytest.approx(100.0), "ratchet breakeven'e (entry) çekilmedi"


def test_k2b_sonraki_bar_bar_ici_dokunusta_stop_ateslenir():
    """SONRAKİ BAR: breakeven aktif. low entry'nin altına inince stop ateşler — ratchet gerçekten
    etkiyor, sadece bir bar GECİKMELİ (bankalama barının kendi açılışına uygulanmıyor)."""
    b = _brk()
    pos = _poz()
    b.scale_out(pos, BAR_KUSUR, KOL)
    assert b._touch_exit(pos, BAR_KUSUR) is None
    ex = b._touch_exit(pos, {"open": 100.5, "high": 101.0, "low": 99.0})
    assert ex == (100.0, "stop"), f"sonraki barda breakeven stop ateşlemedi: {ex}"


def test_k2c_sonraki_bar_gap_acilisinda_stop_gap_ateslenir():
    """Aynı ratchet, gap kolu: sonraki bar entry'nin ALTINDA açılırsa `stop_gap` — bu, bankalama
    barında YANLIŞ olan davranışın bir sonraki barda DOĞRU olan hâlidir."""
    b = _brk()
    pos = _poz()
    b.scale_out(pos, BAR_KUSUR, KOL)
    assert b._touch_exit(pos, BAR_KUSUR) is None
    ex = b._touch_exit(pos, {"open": 99.5, "high": 101.0, "low": 99.0})
    assert ex == (99.5, "stop_gap"), f"sonraki barda gap stop_gap ateşlemedi: {ex}"


def test_k2d_yuruyus_bankalama_barini_gecer_sonraki_barda_durur():
    """Üç çağıranın BİREBİR dizisiyle yürüyüş: bankalama barı geçilir (bars_held artar), stop bir
    SONRAKİ barda ateşler. Düzeltme çağıranların sırasını değiştirmeden çalışmalı."""
    b = _brk()
    pos = _poz()
    ex = _yuru(b, pos, [BAR_KUSUR, {"open": 100.6, "high": 101.4, "low": 99.8}], KOL)
    assert pos.bars_held == 1, "bankalama barı sayılmadı (koşucu o barda kesilmiş olmalı)"
    assert ex == (100.0, "stop"), f"sonraki barda stop beklenirdi: {ex}"


# =================================================================================================
# K3 — TEK ATIMLIK: işaret bankalama barının dışına TAŞMAZ
# =================================================================================================

def test_k3_bankalama_oncesi_taban_tek_atimliktir():
    """Bankalama-öncesi taban YALNIZ o barın dokunuş kontrolüne aittir. Aynı pozisyon üzerinde ikinci
    bir `_touch_exit` (sonraki bar) artık TAM ratchet'i görmeli — yoksa düzeltme kusuru kalıcılaştırır
    ve breakeven hiç etkimezdi."""
    b = _brk()
    pos = _poz()
    b.scale_out(pos, BAR_KUSUR, KOL)
    assert b._touch_exit(pos, BAR_KUSUR) is None                 # 1. çağrı: tabanı TÜKETİR
    ex = b._touch_exit(pos, BAR_KUSUR)                           # 2. çağrı: aynı bar, ama taban bitti
    assert ex == (99.95, "stop_gap"), f"taban bar dışına taştı — ratchet hiç etkimiyor: {ex}"


def test_k3b_ikinci_bankalama_denemesi_tabani_yeniden_kurmaz():
    """`scaled_out` pozisyonda `scale_out` ilk kapıdan False döner; taban YENİDEN kurulmamalı
    (idempotens — EDG-029 öz-sınaması (iv) ile aynı iddia)."""
    b = _brk()
    pos = _poz()
    b.scale_out(pos, BAR_KUSUR, KOL)
    assert b._touch_exit(pos, BAR_KUSUR) is None
    assert b.scale_out(pos, {"open": 100.6, "high": 112.0, "low": 100.2}, KOL) is False
    ex = b._touch_exit(pos, {"open": 99.5, "high": 101.0, "low": 99.0})
    assert ex == (99.5, "stop_gap"), f"ikinci bankalama denemesi ratchet'i sildi: {ex}"


# =================================================================================================
# K4 — `frac=0` YOLU BİREBİR + muhafızlar AYNI
# =================================================================================================

def test_k4_frac_sifir_scale_out_false_trail_degismez():
    """`frac<=0` ilk kapıda False döner: trail'e DOKUNULMAZ ve bankalama-öncesi taban KURULMAZ —
    canlı yapılandırma (`exit.scale_out_frac = 0.0`) bugünküyle bit-birebir kalır."""
    b = _brk()
    pos = _poz()
    kapali = {"exit.scale_out_frac": 0.0, "exit.scale_out_r": 2.0}
    assert b.scale_out(pos, BAR_KUSUR, kapali) is False
    assert pos.trail_stop == 95.0 and pos.scaled_out is False and pos.qty == 100
    assert b.scale_out(pos, BAR_SASI, kapali) is False
    assert pos.trail_stop == 95.0


def test_k4b_frac_sifir_yolunda_dokunus_bugunku_ifadeyle_aynidir():
    """`frac=0` iken `_touch_exit`in eff_stop'u `max(pos.stop, pos.trail_stop)` olmalı — düzeltmenin
    tabanı hiç devreye girmediği için ifade bugünküyle AYNIdır. Trail'i sert stop'un üstüne kurup
    hem gap hem bar-içi kolunu ölçer."""
    kapali = {"exit.scale_out_frac": 0.0, "exit.scale_out_r": 2.0}
    b = _brk()
    p1 = _poz(trail=104.0)                                        # bar-içi kol: açılış taban üstünde
    bar1 = {"open": 105.0, "high": 106.0, "low": 103.0}
    assert b.scale_out(p1, bar1, kapali) is False
    assert b._touch_exit(p1, bar1) == (104.0, "stop"), "eff_stop max(stop, trail) olmaktan çıktı"
    p2 = _poz(trail=104.0)                                        # gap kolu: açılış tabanın altında
    bar2 = {"open": 103.0, "high": 108.0, "low": 102.0}
    assert b.scale_out(p2, bar2, kapali) is False
    assert b._touch_exit(p2, bar2) == (103.0, "stop_gap"), "gap kolu bugünkü ifadeden ayrıştı"


def test_k4c_stop_once_muhafizi_davranisi_degismedi():
    """v24 `test_k2c_scale_out_refused_when_bar_breached_the_stop` sözleşmesi: bar low ZATEN eski
    stop'un altındaysa bankalama REDDEDİLİR ve `_touch_exit` barı muhafazakârca TAM stop çıkışı
    olarak çözer. Düzeltme bu yolu değiştirmemeli — reddedilen bankalama taban da kurmaz."""
    b = _brk()
    pos = _poz()
    bar = {"open": 108.0, "high": 112.0, "low": 90.0}
    assert b.scale_out(pos, bar, KOL) is False, "stop-önce muhafızı delindi"
    assert pos.trail_stop == 95.0 and pos.scaled_out is False
    assert b._touch_exit(pos, bar) == (95.0, "stop"), "muhafazakâr tam stop çıkışı kayboldu"


def test_k4d_hedef_once_ve_acilis_hedef_muhafizlari_tabani_kurmaz():
    """Diğer iki muhafız (`level >= target`, açılış hedefin üstünde) de False döner; hiçbiri
    bankalama-öncesi tabanı kurmamalı — kurarsa o bar için stop SESSİZCE gevşerdi."""
    b = _brk()
    p1 = _poz(target=107.0)                                       # level 107.5 >= target 107.0
    assert b.scale_out(p1, BAR_SASI, KOL) is False
    assert b._touch_exit(p1, {"open": 103.0, "high": 106.0, "low": 102.0}) is None, \
        "hedef-önce muhafızı tabanı kurdu — o bar için stop sessizce gevşedi"
    p2 = _poz(target=112.5, trail=104.0)                          # açılış hedefin ÜSTÜNDE
    assert b.scale_out(p2, {"open": 113.0, "high": 118.0, "low": 112.0}, KOL) is False
    assert b._touch_exit(p2, {"open": 105.0, "high": 108.0, "low": 103.0}) == (104.0, "stop"), \
        "açılış-hedef muhafızı tabanı kurdu — o bar için stop sessizce gevşedi"


# =================================================================================================
# K5 — ŞEMA: yeni alan serileştirme/yeniden-yükleme yolunu KIRMAZ
# =================================================================================================

def test_k5_position_yuvarlak_turu_asdict_ile_bozulmaz():
    """`loop._save_broker` `asdict(p)` yazar, `loop._load_broker` `Position(**p)` okur. Yeni alan
    bu yuvarlak turdan geçmeli."""
    pos = _poz()
    d = dataclasses.asdict(pos)
    geri = Position(**d)
    assert geri == pos, "Position yuvarlak turu bozuldu"


def test_k5b_eski_kayit_yeni_alansiz_yuklenir():
    """ESKİ state kayıtlarında yeni alan YOKTUR: varsayılanı olmalı ki yükleme `TypeError` atmasın
    (canlı `portfolio.json` bu turdan önce yazılmış pozisyonları taşıyabilir)."""
    d = dataclasses.asdict(_poz())
    yeni = [f.name for f in dataclasses.fields(Position)
            if f.name not in ("plan_id", "ticker", "side", "entry", "stop", "trail_stop",
                              "target", "qty", "r_per_share", "risk_dollars", "size_r", "ts_open")]
    for ad in yeni:
        d.pop(ad, None)
    geri = Position(**d)                                          # eski kayıt: yalnız zorunlu alanlar
    assert geri.entry == 100.0 and geri.trail_stop == 95.0


def test_k5c_shadow_lifecycle_alan_listesi_dinamik_kalir():
    """`shadow_lifecycle._POS_FIELDS` `dataclasses.fields`ten TÜRETİLİR (sabit liste DEĞİL): yeni
    alan gölge kitabın kaydet/yükle turunda da taşınmalı, yoksa gölge kolu ana kitaptan ayrışırdı."""
    from meridian import shadow_lifecycle as sl
    alanlar = tuple(f.name for f in dataclasses.fields(Position))
    assert sl._POS_FIELDS == alanlar, "gölge alan listesi Position şemasından ayrıştı"
    pos = _poz()
    kayit = {k: getattr(pos, k) for k in sl._POS_FIELDS}
    geri = Position(**{k: kayit[k] for k in sl._POS_FIELDS if k in kayit})
    assert geri == pos, "gölge kitap yuvarlak turu bozuldu"
