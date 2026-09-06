"""tests/test_edg082_olcum_v428.py — EDG-2026-082 ÖLÇÜM betiğinin çivisi (TSK-159 S2, 2026-09-06).

NE ÖLÇER. `research/olcumler/edg082_pit_tohum/olcum.py` — kartın (`EDG-2026-082-tohum-pit-uyelik-
suzgeci-kiyasi.yaml`) TABAN/A/B kıyasını üreten betiğin DOĞRU ÖLÇTÜĞÜNÜ kanıtlar. AĞSIZ, OBS'SUZ:
bu dosya `meridian.obs`a hiç yazmaz — motor çağrıları `sandbox_state` fikstürüyle sarılır (`config.
STATE` tmp'e yönlenir, `backtest.replay`in nadir `obs.warn` yolları — varsa — CANLI deftere değil
sandbox'a düşer). Betiğin KENDİSİ de ayrıca `sanitize_bars`/`measurement_bars`i HİÇ ÇAĞIRMAZ
(`temiz_bar_oku`) — bu dosyanın testleri o beyanı da ölçer.

SENTETİK SAHNE (motor gerektiren testler): 4 sembol + endeks, ~90 seans. `VMRK`/`AAA`/`MEM` GÜNCEL
listede; `SPOT` hiç-üye (gerçek `data.HIC_UYE_BEYANLI`nin bir üyesi — sentetik bir kayıt İCAT
EDİLMEDİ); `MEM` bir "Added" satırıyla geç katılır; `VMRK`→`EQR` GERÇEK `constituents.
SEMBOL_YENIDEN_ADLANDIRMA` (rename tarihi 2026-08-18, sahne 2022'de — yani rename HER sorgu
tarihinde GERİ ALINIR, ölçüm penceresi boyunca EQR "üye" olarak GÖRÜNÜR). `strategy.scan_entry`
`test_replay_uyelik_suzgeci_v427.py`deki desenle AYNI şekilde deterministik bir saplamayla
değiştirilir (MEM/EQR/SPOT sinyal alır, AAA hiç almaz — dekor).

MUTASYON KANITLARI (CLAUDE.md §6):
  MUTASYON 1 (brief): `sizinti_kontrolu`ya A sonucu yerine TABAN sonucu verilirse ("A koşumunda
  uyelik hiç uygulanmamış" hatasının simülasyonu) "A'da 0 kaldı" iddiası ÇÜRÜR —
  `test_MUTASYON1_a_sonucu_taban_ile_ayniysa_sizinti_kalir_0_olmaz` bunu doğrudan gösterir; ayrıca
  gerçek motor sahnesinde `fonksiyonlar["A"]` GERÇEKTEN kullanılmazsa (örn. yanlışlıkla `None`
  geçirilirse) SPOT'un A'da düşmesi gereken beklenti bozulur — `test_gec_katilan_hic_uye_ve_rename`
  bunu motor SEVİYESİNDE de sınar.
  MUTASYON 2 (brief): `SEMBOL_YENIDEN_ADLANDIRMA` kaldırılınca (monkeypatch → boş tuple) rename'li
  sembol `pit_as_of`ta artık GÖRÜNMEZ — `test_pit_as_of_rename_MUTASYON_kaldirilinca_kirmizi` bunu
  hem düzeltilmiş hem MUTASYONLU haliyle karşılaştırarak kanıtlar.

KAPSAM DIŞI: kartın hükmü (Rol-1 verir). `backtest.replay/walk_forward`in `uyelik` süzgecinin
KENDİSİNİN doğruluğu (özdeşlik/tam-kapalı/açık-pozisyon-yönetimi süzülmez vb.) BU dosyanın konusu
DEĞİL — o `tests/test_replay_uyelik_suzgeci_v427.py`de ZATEN çivili; burada YALNIZ bu ölçüm
betiğinin o süzgeci DOĞRU KULLANDIĞI (PIT `as_of` kurulumu, rename, hiç-üye birleşimi, sızıntı
sınıflandırması, kapı-hüküm sınıfı sayımı) ölçülür."""
from __future__ import annotations

import json
import pathlib

import pandas as pd
import pytest

from meridian import backtest, config, validation
from meridian import strategy as strategy_mod
from meridian.strategy import EntrySignal
from meridian.adapters.constituents import SEMBOL_YENIDEN_ADLANDIRMA
from tests.conftest import betikten_modul_yukle, make_bars

KOK = pathlib.Path(__file__).resolve().parents[1]
BETIK_YOLU = KOK / "research" / "olcumler" / "edg082_pit_tohum" / "olcum.py"
KART_YOLU = KOK / "research" / "cards" / "EDG-2026-082-tohum-pit-uyelik-suzgeci-kiyasi.yaml"


def _olcum():
    return betikten_modul_yukle(BETIK_YOLU, "edg082_olcum")


# =================================================================================================
# KART — eşikler gerçek karttan okunuyor (ajan karta DOKUNMADI, yalnız OKUR)
# =================================================================================================

def test_esikler_gercek_karttan_okunur():
    o = _olcum()
    e = o.esikleri_karttan_oku(KART_YOLU)
    assert e["kart_id"] == "EDG-2026-082"
    assert e["k1_gecti"] and e["k2_gecti"]


def test_esik_alani_eksikse_UYDURMAZ_value_error_atar(tmp_path):
    o = _olcum()
    bozuk = tmp_path / "kart.yaml"
    bozuk.write_text("card_id: X\n", encoding="utf-8")
    with pytest.raises(ValueError, match="esikler"):
        o.esikleri_karttan_oku(bozuk)


# =================================================================================================
# BAR OKUMA — dosya adı formülü + minimal temizlik + ATLANAN adımların beyanı
# =================================================================================================

def test_bar_dosya_yolu_kucuk_harf_ve_nokta_tire(tmp_path):
    o = _olcum()
    assert o.bar_dosya_yolu(tmp_path, "BRK.B").name == "brk-b.csv"
    assert o.bar_dosya_yolu(tmp_path, "mem").name == "mem.csv"


def test_temiz_bar_oku_nan_negatif_dusurur_dedup_eder_ve_atlanan_adimlari_beyan_eder(tmp_path):
    o = _olcum()
    df = pd.DataFrame({
        "date": ["2022-01-03", "2022-01-04", "2022-01-04", "2022-01-05"],
        "open": [10.0, 11.0, 11.5, -1.0], "high": [9.0, 12.0, 12.0, 5.0],
        "low": [8.0, 10.5, 10.5, 4.0], "close": [10.5, 11.8, 11.9, None],
        "volume": [1000, 1000, 1200, 1000],
    })
    (tmp_path / "mem.csv").write_text(df.to_csv(index=False), encoding="utf-8")
    df_temiz, meta = o.temiz_bar_oku(tmp_path, "MEM")
    assert meta["bulundu"] is True
    # satır 4 (negatif open + NaN close) düşer, yinelenen 2022-01-04 SONUNCUSU (11.5 open) kalır
    assert meta["n_dropped_nan_negatif"] == 1
    assert meta["n_dedup"] == 1
    assert len(df_temiz) == 2
    assert list(o.ATLANAN_TEMIZLIK_ADIMLARI) == meta["atlanan_temizlik_adimlari"]
    # high/low OHLC zarfına kenetlenmiş olmalı (satır 1: high=9 < open=10 idi → 10'a çekilir)
    assert df_temiz.iloc[0]["high"] >= max(df_temiz.iloc[0]["open"], df_temiz.iloc[0]["close"])
    assert df_temiz.iloc[0]["low"] <= min(df_temiz.iloc[0]["open"], df_temiz.iloc[0]["close"])


def test_temiz_bar_oku_dosya_yoksa_None(tmp_path):
    o = _olcum()
    df, meta = o.temiz_bar_oku(tmp_path, "YOK")
    assert df is None and meta["bulundu"] is False


# =================================================================================================
# MANİFEST KONTROLÜ — eşit/farklı
# =================================================================================================

def test_manifest_kontrol_esit(tmp_path):
    o = _olcum()
    onceki = tmp_path / "onceki_sonuc.json"
    manifest = {"mem.csv": "aaa", "idx.csv": "bbb"}
    onceki.write_text(json.dumps({"girdi_kimligi": {"bar_manifesti": manifest}}), encoding="utf-8")
    sonuc = o.manifest_kontrol(manifest, onceki)
    assert sonuc["gecerli"] is True and sonuc["n_fark"] == 0


def test_manifest_kontrol_farkli_sha_gecersiz(tmp_path):
    o = _olcum()
    onceki = tmp_path / "onceki_sonuc.json"
    onceki.write_text(json.dumps({"girdi_kimligi": {"bar_manifesti": {"mem.csv": "aaa"}}}), encoding="utf-8")
    sonuc = o.manifest_kontrol({"mem.csv": "DEGISTI"}, onceki)
    assert sonuc["gecerli"] is False
    assert sonuc["n_fark"] == 1
    assert sonuc["fark_dosyalar"] == ["mem.csv"]


# =================================================================================================
# PIT `as_of` — geç katılan (rewind) + RENAME (gerçek SEMBOL_YENIDEN_ADLANDIRMA) + MUTASYON 2
# =================================================================================================

def _degisiklikler_mem_gec_katilir():
    return [{"tarih": "2022-02-01", "eklenen": "MEM", "cikan": None, "neden": "test-join"}]


def test_pit_as_of_gec_katilan_oncesi_dislanir_sonrasi_dahil():
    o = _olcum()
    degisiklikler = _degisiklikler_mem_gec_katilir()
    guncel = {"AAA", "MEM"}
    once = o.pit_as_of(degisiklikler, guncel, "2022-01-15")
    sonra = o.pit_as_of(degisiklikler, guncel, "2022-02-01")
    assert "MEM" not in once, "geç-katılan sembol katılım ÖNCESİ üye sayıldı"
    assert "MEM" in sonra, "geç-katılan sembol katılım gününde/sonrasında üye SAYILMADI"
    assert "AAA" in once and "AAA" in sonra, "hep-üye sembol yanlışlıkla düştü"


def test_pit_as_of_rename_gercek_defterle_eski_ad_donuyor():
    """`SEMBOL_YENIDEN_ADLANDIRMA` GERÇEK sabiti (EQR/VMRK, tarih 2026-08-18) — sahne tarihi bu
    tarihten ÖNCE olduğu için rename HER ZAMAN geri alınır: guncel listede VMRK varken `pit_as_of`
    EQR döndürmeli."""
    o = _olcum()
    assert SEMBOL_YENIDEN_ADLANDIRMA[0]["eski"] == "EQR"
    assert SEMBOL_YENIDEN_ADLANDIRMA[0]["yeni"] == "VMRK"
    sonuc = o.pit_as_of([], {"VMRK"}, "2022-06-01")
    assert sonuc == {"EQR"}, f"rename son-işlemi çalışmadı: {sonuc}"


def test_pit_as_of_rename_MUTASYON_kaldirilinca_kirmizi(monkeypatch):
    """MUTASYON 2 (brief): rename eşlemesi kaldırılınca rename'li sembol `pit_as_of`ta artık
    GÖRÜNMEZ — bu, `test_pit_as_of_rename_gercek_defterle_eski_ad_donuyor`nun DÜZELTİLMİŞ
    davranışını KIRMIZI yapan mutasyonun ta kendisidir (burada doğrudan uygulanıp ölçülüyor)."""
    o = _olcum()
    monkeypatch.setattr(o, "SEMBOL_YENIDEN_ADLANDIRMA", ())
    sonuc = o.pit_as_of([], {"VMRK"}, "2022-06-01")
    assert sonuc == {"VMRK"}, "rename kaldırıldığında ESKİ davranış (EQR) hâlâ görünüyor — çivi kör"
    assert "EQR" not in sonuc, "MUTASYON uygulanmasına RAĞMEN EQR görünüyor — test bu dalı ısırmıyor"


def test_uyelik_fonksiyonlarini_kur_A_ve_B_ortak_onbellek_paylasir():
    o = _olcum()
    fonksiyonlar = o.uyelik_fonksiyonlarini_kur(_degisiklikler_mem_gec_katilir(), ["VMRK", "AAA", "MEM"],
                                                hic_uye={"SPOT"})
    assert fonksiyonlar["TABAN"] is None
    a1 = fonksiyonlar["A"]("2022-03-01")
    assert a1 == {"EQR", "AAA", "MEM"}
    b1 = fonksiyonlar["B"]("2022-01-10")
    assert b1 == {"EQR", "AAA", "SPOT"}          # MEM henüz katılmadı, SPOT hiç-üye ama B'de var
    # A ve B AYNI tarihe İKİNCİ kez sorulduğunda önbellek YENİDEN HESAPLAMAZ (kanıt: nesne kimliği
    # aynı `pit_as_of` çağrısına gitmeden döner — dolaylı kanıt: sonuç DEĞİŞMEZ, çağrı sayaçları artar)
    fonksiyonlar["A"]("2022-01-10")
    assert len(fonksiyonlar["_onbellek"]) == 2          # yalnız 2 FARKLI tarih kuruldu (03-01, 01-10)
    assert len(fonksiyonlar["_cagrilar_a"]) == 2 and len(fonksiyonlar["_cagrilar_b"]) == 1


# =================================================================================================
# GERÇEK MOTOR SAHNESİ — geç-katılan + hiç-üye + rename, TABAN/A/B (koşum_calistir)
# =================================================================================================

def _valid_ohlc(df):
    df = df.copy()
    df["high"] = df[["open", "high", "close"]].max(axis=1)
    df["low"] = df[["open", "low", "close"]].min(axis=1)
    return df


N_BARS = 90
D_MEM = "2022-03-01"          # MEM bu tarihte "Added" — öncesi TABAN'da var, A/B'de yok beklenir


def _sinyal_yap(sinyal_alan):
    """`strategy.scan_entry` saplaması ÜRETİCİSİ — YALNIZ `sinyal_alan` kümesindeki sembol(ler)
    sinyal alır. Testler bunu KENDİ TEK-SEMBOLLÜK kümesiyle çağırır: `test_replay_uyelik_suzgeci_
    v427.py`nin dersi AYNEN uygulanır — MEM/EQR/SPOT'un HEPSİ AYNI ANDA GERÇEK işlem üretirse
    PAYLAŞILAN portföy etkileri (heat/sector-cap/sermaye eğrisi, hepsi sentetik sembollerde AYNI
    '?' sektör kovasına düşer) bir sembolün işlem listesini DİĞERİNİN filtrelenmesinden ETKİLER —
    bu bir kusur DEĞİL (v427 `_kimlik` şerhinin AYNISI), ama "TABAN'la BİREBİR" iddiasını YANLIŞ
    kılar. Her izole test bu yüzden TEK bir sembolü GERÇEK trader yapar, kalanı DEKOR bırakır."""
    def _stub(bars_df, params, rs_rating_value, ticker="?"):
        if ticker not in sinyal_alan:
            return None
        close = float(bars_df["close"].iloc[-1])
        entry = close * 1.001
        stop = entry * 0.95
        r_per_share = entry - stop
        target = entry + 3.0 * r_per_share
        return EntrySignal(ticker=ticker, setup="momentum_breakout", entry_trigger=entry, pivot=entry,
                           stop=stop, atr=r_per_share / 2.0, rs_rating=80, score=80,
                           profit_target=target, size_r=0.5, r_per_share=r_per_share,
                           notes="v428-sentetik-sinyal")
    return _stub


@pytest.fixture
def sahne(sandbox_state, monkeypatch, tmp_path):
    """Bar/HTML/güncel-liste FİKSTÜRLERİNİ kurar — `strategy.scan_entry`i BURADA YAMAMAZ (testler
    kendi TEK-SEMBOLLÜ `sinyal_alan` kümesiyle `monkeypatch.setattr(strategy_mod, 'scan_entry',
    _sinyal_yap({...}))` çağırır, paylaşılan-portföy karışmasın diye)."""
    idx = _valid_ohlc(make_bars(N_BARS, seed=7, trend=0.0006))
    bars = {"MEM": _valid_ohlc(make_bars(N_BARS, seed=2, trend=0.0009)),
            "EQR": _valid_ohlc(make_bars(N_BARS, seed=3, trend=0.0009)),
            "SPOT": _valid_ohlc(make_bars(N_BARS, seed=5, trend=0.0009)),
            "AAA": _valid_ohlc(make_bars(N_BARS, seed=11, trend=0.0004))}
    bars_dir = tmp_path / "bars"
    bars_dir.mkdir()
    for t, df in {**bars, "IDX": idx}.items():
        o = _olcum()
        df.to_csv(o.bar_dosya_yolu(bars_dir, t), index=False)
    html = ('<table><tr><th>Effective Date</th><th>Added</th><th>Removed</th><th>Reason</th></tr>'
           f'<tr><td>{D_MEM}</td><td>MEM</td><td></td><td>test-join</td></tr></table>')
    html_yolu = tmp_path / "degisiklikler.html"
    html_yolu.write_text(html, encoding="utf-8")
    guncel_yolu = tmp_path / "guncel.json"
    guncel_yolu.write_text(json.dumps(["VMRK", "AAA", "MEM"]), encoding="utf-8")
    params = config.default_strategy()["params"]
    goal = config.goal()
    dates = [str(x.date()) for x in idx["date"]]
    return {"bars": bars, "idx": idx, "params": params, "goal": goal,
           "start": dates[0], "end": dates[-1], "bars_dir": bars_dir,
           "html_yolu": html_yolu, "guncel_yolu": guncel_yolu}


def _kosumlar(sahne, monkeypatch, sinyal_alan):
    """TEK sembollü `sinyal_alan` ile `scan_entry`i yamar, TABAN/A/B'yi koşar — üçü de AYNI
    (izole) portföy dinamiğini görür, çapraz-sembol karışması YOK."""
    o = _olcum()
    monkeypatch.setattr(strategy_mod, "scan_entry", _sinyal_yap(sinyal_alan))
    degisiklikler, _, _ = o.degisiklikleri_yukle(sahne["html_yolu"])
    guncel_liste = o.guncel_liste_oku(sahne["guncel_yolu"])
    fonksiyonlar = o.uyelik_fonksiyonlarini_kur(degisiklikler, guncel_liste)
    ort = {}
    for ad in ("TABAN", "A", "B"):
        ort[ad] = o.koşum_calistir(fonksiyonlar[ad], sahne["params"], sahne["bars"], sahne["idx"],
                                   sahne["goal"], sahne["start"], sahne["end"], strategy_version=1)
    return fonksiyonlar, ort


def _kimlik(trades):
    """İşlemin YOL KİMLİĞİ (`test_replay_uyelik_suzgeci_v427.py::_kimlik` İLE AYNI gerekçe): bir
    ÖNCEKİ işlemin süzülüp süzülmediği aynı koşumda BİLEŞİK sermaye eğrisini (payın tam sayı
    hisseye yuvarlanması) değiştirir — `qty`/`pnl_dollars`/`r_multiple` gibi BÜYÜKLÜK alanları bu
    yüzden BİLEREK dışarıda bırakılır. Süzgecin doğruluğu YOL kimliğinde ölçülür (bu betiğin işi
    zaten üyelik SINIRINI doğru çizmek, motorun kompozit sermaye muhasebesi DEĞİL — o `v427`nin
    konusu)."""
    return [(t["ticker"], t["ts_open"], t["ts_close"], t["exit_reason"]) for t in trades]


def test_gec_katilan_MEM_erken_islemleri_A_ve_B_de_duser(sahne, monkeypatch):
    """MEM TEK trader (izole — EQR/SPOT/AAA dekor): katılım-ÖNCESİ (`< D_MEM`) işlemleri A/B'de
    DÜŞER, katılım-SONRASI işlemlerin YOL KİMLİĞİ (`_kimlik` — ticker/ts_open/ts_close/exit_reason)
    BOZULMADAN kalır. Büyüklük alanları (qty/pnl/r_multiple) BİLEREK KIYASLANMAZ: erken işlemin
    düşmesi kompozit sermaye eğrisini kaydırır (v427 `_kimlik` şerhiyle AYNI, tek sembol bile
    olsa) — süzgecin doğruluğu burada YOL kimliğinde ölçülür."""
    _, ort = _kosumlar(sahne, monkeypatch, {"MEM"})
    taban, a, b = ort["TABAN"]["trades"], ort["A"]["trades"], ort["B"]["trades"]
    assert taban, "sahne hiç MEM işlemi üretmedi — kıyas VACUOUS olurdu"
    assert any(t["ts_open"] < D_MEM for t in taban), (
        f"sahne varsayımı bozuldu: MEM'in {D_MEM} öncesi hiç TABAN işlemi yok "
        f"({[t['ts_open'] for t in taban]})")
    taban_sonrasi_kimlik = _kimlik([t for t in taban if t["ts_open"] >= D_MEM])

    assert not any(t["ts_open"] < D_MEM for t in a), "A'da MEM'in katılım-öncesi işlemi KALDI"
    assert _kimlik(a) == taban_sonrasi_kimlik, "A'da MEM'in katılım-SONRASI işlemleri (yol kimliği) bozuldu"
    assert not any(t["ts_open"] < D_MEM for t in b), "B'de MEM'in katılım-öncesi işlemi KALDI"
    assert _kimlik(b) == taban_sonrasi_kimlik, "B'de MEM'in katılım-SONRASI işlemleri (yol kimliği) bozuldu"


def test_hic_uye_SPOT_A_da_tamamen_duser_B_de_TABANla_birebir_kalir(sahne, monkeypatch):
    """SPOT TEK trader (izole): `data.HIC_UYE_BEYANLI` üyesi — hiçbir zaman `as_of`ta yok, A'da
    TÜM işlemleri düşer; B onu KOŞULSUZ üye saydığı için TABAN'la BİREBİR (tek-sembol, izole)."""
    _, ort = _kosumlar(sahne, monkeypatch, {"SPOT"})
    taban, a, b = ort["TABAN"]["trades"], ort["A"]["trades"], ort["B"]["trades"]
    assert taban, "sahne hiç SPOT işlemi üretmedi — kıyas VACUOUS olurdu"
    assert a == [], f"hiç-üye SPOT A'da (yalnız as_of) düşmedi: {a}"
    assert b == taban, "hiç-üye SPOT B'de TABAN'dan SAPTI (B onu koşulsuz üye saymalı)"


def test_rename_EQR_A_ve_B_de_TABANla_birebir_kalir(sahne, monkeypatch):
    """EQR TEK trader (izole): güncel listede `VMRK`, GERÇEK `SEMBOL_YENIDEN_ADLANDIRMA` (tarih
    2026-08-18, sahne 2022'de) EQR'yi HER sorgu tarihinde geri getirir — yani EQR hiçbir zaman
    süzülmemeli, A/B TABAN'la BİREBİR (tek-sembol, izole) kalmalı."""
    fonksiyonlar, ort = _kosumlar(sahne, monkeypatch, {"EQR"})
    taban, a, b = ort["TABAN"]["trades"], ort["A"]["trades"], ort["B"]["trades"]
    assert taban, "sahne hiç EQR işlemi üretmedi — kıyas VACUOUS olurdu"
    tarihler = [str(x.date()) for x in sahne["idx"]["date"]]
    assert all("EQR" in fonksiyonlar["A"](d) for d in tarihler), "EQR bazı tarihlerde as_of'tan DÜŞTÜ"
    assert a == taban, "rename ile hep-üye sayılması gereken EQR A'da TABAN'dan SAPTI"
    assert b == taban, "rename ile hep-üye sayılması gereken EQR B'de TABAN'dan SAPTI"


def test_adim0_a_b_tam_acik_birebir_ve_bos_kume_sifir_islem(sahne, monkeypatch):
    """Kart pozitif_kontrol + adım-0(a)(b): `uyelik=<tüm evren>` TABAN'la BİREBİR, `uyelik=<boş
    küme>` sıfır işlem verir. Bu iki koşum AYNI süzgeç yapılandırmasını (tüm-evren/boş-küme)
    kıyaslar — çapraz-sembol paylaşılan-portföy etkisi burada bir SORUN DEĞİL (TABAN'ın kendisiyle
    kıyaslanıyor), o yüzden üç sembol BİRDEN sinyal alabilir (daha güçlü sahne)."""
    o = _olcum()
    monkeypatch.setattr(strategy_mod, "scan_entry", _sinyal_yap({"MEM", "EQR", "SPOT"}))
    degisiklikler, _, _ = o.degisiklikleri_yukle(sahne["html_yolu"])
    guncel_liste = o.guncel_liste_oku(sahne["guncel_yolu"])
    fonksiyonlar = o.uyelik_fonksiyonlarini_kur(degisiklikler, guncel_liste)
    taban = o.koşum_calistir(fonksiyonlar["TABAN"], sahne["params"], sahne["bars"], sahne["idx"],
                             sahne["goal"], sahne["start"], sahne["end"], strategy_version=1)
    sonuc = o.adim0_fizibilite(taban, sahne["params"], sahne["bars"], sahne["idx"], sahne["goal"],
                               sahne["start"], sahne["end"], strategy_version=1,
                               degisiklikler=degisiklikler, guncel_liste=guncel_liste)
    assert sonuc["a_tam_acik_birebir"] is True, "uyelik=<tüm evren> TABAN'la BİREBİR eşleşmedi"
    assert sonuc["b_tam_kapali_sifir_islem"] is True, "uyelik=<boş küme> sıfır işlem VERMEDİ"
    assert sonuc["c_kuramama_orani"] == 0.0, "sahne tarihlerinin hepsinde as_of kurulabilmeli"
    assert sonuc["gecerli"] is True


# =================================================================================================
# KAPI HÜKÜMLERİ — walk_forward'a uyelik geçer, DSR/PBO yapısal None, ledger'a DOKUNMAZ
# =================================================================================================

def test_kapi_hukumleri_uyelik_walk_forwarda_gecer_ve_dsr_pbo_yapisal_olculemedi(sahne, monkeypatch):
    o = _olcum()
    yakalanan_pbo_rows = {}
    orijinal_pbo_cscv = validation.pbo_cscv

    def casus_pbo_cscv(rows=None, **kw):
        yakalanan_pbo_rows["rows"] = rows
        return orijinal_pbo_cscv(rows=rows, **kw)

    monkeypatch.setattr(validation, "pbo_cscv", casus_pbo_cscv)

    yakalanan_wf = {}
    orijinal_wf = backtest.walk_forward

    def casus_wf(*args, **kwargs):
        yakalanan_wf.update(kwargs)
        return orijinal_wf(*args, **kwargs)

    monkeypatch.setattr(backtest, "walk_forward", casus_wf)

    sonuc = o.kapi_hukumleri(lambda d: {"MEM"}, sahne["params"], sahne["bars"], sahne["idx"],
                             sahne["goal"], strategy_version=1)

    assert callable(yakalanan_wf.get("uyelik")), "walk_forward'a uyelik fonksiyonu GEÇMEDİ"
    assert yakalanan_pbo_rows.get("rows") == [], (
        "pbo_cscv rows=[] İLE ÇAĞRILMADI — varsayılan None çağrısı GERÇEK validation_ledger.jsonl'i okurdu")
    assert sonuc["dsr_kapi"]["dsr_durum"] == "olculemedi"
    assert sonuc["pbo_kapi"]["durum"] == "olculemedi"
    assert sonuc["dsr_neden"] and sonuc["pbo_neden"]


# =================================================================================================
# KAPI HÜKÜM SINIFI KIYASI — payda n/1 (DSR/PBO paydaya girmez)
# =================================================================================================

def _kapi(oos_durum, dsr_durum="olculemedi", pbo_durum="olculemedi"):
    return {"oos_durum": oos_durum, "dsr_kapi": {"dsr_durum": dsr_durum},
            "pbo_kapi": {"durum": pbo_durum}}


def test_kapi_sinifi_kiyasla_ayni_oos_payda_bir_ayni():
    o = _olcum()
    sonuc = o.kapi_sinifi_kiyasla(_kapi("olculdu"), _kapi("olculdu"))
    assert sonuc["oos_ayni_mi"] is True
    assert sonuc["olculebilen_kapi_sayisi"] == 1
    assert sonuc["olculebilen_kapi_ayni_sayisi"] == 1
    assert sonuc["hukum_sinifi_n"] == "1/1"


def test_kapi_sinifi_kiyasla_farkli_oos_payda_bir_farkli():
    o = _olcum()
    sonuc = o.kapi_sinifi_kiyasla(_kapi("olculdu"), _kapi("olculemedi"))
    assert sonuc["oos_ayni_mi"] is False
    assert sonuc["hukum_sinifi_n"] == "0/1"


# =================================================================================================
# SIZINTI KONTROLÜ — hiç-üye (data.HIC_UYE_BEYANLI) sınıflandırması + MUTASYON 1
# =================================================================================================

def _sizanlar_edg079_bicimi(*ciftler):
    return {"k1_tohum": {"n": 100,
                         "sizanlar": [{"ticker": t, "ts_open": d, "r_multiple": 0.0} for t, d in ciftler]}}


def _islem(ticker, ts_open):
    return {"ticker": ticker, "ts_open": ts_open, "ts_close": ts_open, "r_multiple": 0.1}


def test_sizinti_kontrolu_hic_uye_siniflandirmasi_ve_beklenen_sifir():
    o = _olcum()
    taban_trades = [_islem("SPOT", "2022-01-05"), _islem("MEM", "2022-01-10"),
                   _islem("AAA", "2022-01-20")]        # AAA sızıntı listesinde YOK — eslesmemeli
    a_trades = [_islem("AAA", "2022-01-20")]            # SPOT/MEM düştü (beklenen)
    b_trades = [_islem("SPOT", "2022-01-05"), _islem("AAA", "2022-01-20")]   # SPOT kaldı (hiç-üye)
    edg079 = _sizanlar_edg079_bicimi(("SPOT", "2022-01-05"), ("MEM", "2022-01-10"))

    sonuc = o.sizinti_kontrolu(taban_trades, a_trades, b_trades, edg079, hic_uye={"SPOT"})
    assert sonuc["n_edg079_sizinti"] == 2
    assert sonuc["n_eslesen_tabanda"] == 2
    assert sonuc["n_hic_uye_esen"] == 1 and sonuc["n_diger_esen"] == 1
    assert sonuc["n_kalan_a"] == 0
    assert sonuc["n_kalan_b_hic_uye"] == 1 and sonuc["n_kalan_b_diger"] == 0
    assert sonuc["beklenen"] == {"kalan_a": 0, "kalan_b_hic_uye": 1, "kalan_b_diger": 0}
    assert sonuc["tutarli"] is True


def test_MUTASYON1_a_sonucu_taban_ile_ayniysa_sizinti_kalir_0_olmaz():
    """MUTASYON 1 (brief): A koşumunda `uyelik` hiç uygulanmamış gibi (A == TABAN) verilirse
    '0 kaldı' iddiası ÇÜRÜMELİ — bu test doğru davranışın (yukarıdaki test) TERSİNİ doğrudan
    ölçerek çivinin bu dalı GERÇEKTEN ısırdığını kanıtlar."""
    o = _olcum()
    taban_trades = [_islem("SPOT", "2022-01-05"), _islem("MEM", "2022-01-10")]
    edg079 = _sizanlar_edg079_bicimi(("SPOT", "2022-01-05"), ("MEM", "2022-01-10"))

    sonuc_mutasyonlu = o.sizinti_kontrolu(taban_trades, taban_trades, taban_trades, edg079, hic_uye={"SPOT"})
    assert sonuc_mutasyonlu["n_kalan_a"] == 2, (
        "MUTASYON (A==TABAN) uygulandığında bile n_kalan_a beklenen 0'da KALDI — bu çivi kör")
    assert sonuc_mutasyonlu["tutarli"] is False, "MUTASYONLU sonuç yine de 'tutarlı' göründü — çivi kör"


def test_sizinti_kontrolu_edg079de_olmayan_cift_eslesmez():
    o = _olcum()
    taban_trades = [_islem("AAA", "2022-01-20")]
    edg079 = _sizanlar_edg079_bicimi(("SPOT", "2022-01-05"))
    sonuc = o.sizinti_kontrolu(taban_trades, [], [], edg079, hic_uye={"SPOT"})
    assert sonuc["n_eslesen_tabanda"] == 0
    assert sonuc["eslesme_orani"] == 0.0


# =================================================================================================
# TABAN SAPMA KONTROLÜ — kill-list #2 (>%25 sapma)
# =================================================================================================

def test_taban_sapma_kontrolu_esik_alti_kill_yok():
    o = _olcum()
    sonuc = o.taban_sapma_kontrolu([{"ticker": "X"}] * 90, {"k1_tohum": {"n": 100}})
    assert sonuc["calisti"] is True
    assert sonuc["sapma_orani"] == pytest.approx(0.10)
    assert sonuc["kill_tetiklendi"] is False


def test_taban_sapma_kontrolu_esik_ustu_kill_tetiklenir():
    o = _olcum()
    sonuc = o.taban_sapma_kontrolu([{"ticker": "X"}] * 60, {"k1_tohum": {"n": 100}})
    assert sonuc["sapma_orani"] == pytest.approx(0.40)
    assert sonuc["kill_tetiklendi"] is True
    assert sonuc["neden"]


def test_taban_sapma_kontrolu_n_eski_yoksa_calismadi_neden_tasir():
    o = _olcum()
    sonuc = o.taban_sapma_kontrolu([], {"k1_tohum": {}})
    assert sonuc["calisti"] is False and sonuc["neden"]


# =================================================================================================
# SÜRE KURALI — adım-0(d): A/B ≤ 2×TABAN
# =================================================================================================

def test_sure_kurali_tavan_asilmadi():
    o = _olcum()
    sonuc = o.sure_kurali_uygula(1.0, 1.5, 1.9)
    assert sonuc["a_tavan_asilmadi"] is True and sonuc["b_tavan_asilmadi"] is True
    assert sonuc["kill_tetiklendi"] is False


def test_sure_kurali_tavan_asilinca_kill():
    o = _olcum()
    sonuc = o.sure_kurali_uygula(1.0, 1.5, 2.5)
    assert sonuc["b_tavan_asilmadi"] is False
    assert sonuc["kill_tetiklendi"] is True


# =================================================================================================
# CLI UÇTAN UCA + MANİFEST-KİLL YOLU
# =================================================================================================

def test_cli_olc_uctan_uca_sonuc_semasi(sahne, monkeypatch, tmp_path):
    o = _olcum()
    monkeypatch.setattr(strategy_mod, "scan_entry", _sinyal_yap({"MEM"}))
    cikti = tmp_path / "sonuc.json"
    rc = o.ana(["--olc", "--bars-dir", str(sahne["bars_dir"]), "--girdi-html", str(sahne["html_yolu"]),
               "--guncel-liste", str(sahne["guncel_yolu"]), "--kart", str(KART_YOLU),
               "--baslangic", sahne["start"], "--bitis", sahne["end"], "--cikti", str(cikti),
               "--evren", "MEM,EQR,SPOT,AAA", "--index-symbol", "IDX"])
    assert cikti.exists()
    sonuc = json.loads(cikti.read_text(encoding="utf-8"))
    for anahtar in ("kart", "girdi_kimligi", "adim_0", "taban", "a", "b", "kiyas",
                   "sizinti_kontrolu", "taban_sapma_kontrolu", "pozitif_kontrol", "esikler", "beyan"):
        assert anahtar in sonuc, f"sonuc.json şeması '{anahtar}' alanını KAYBETTİ"
    assert "trades" not in sonuc["taban"], "ham işlem listesi sonuc.json'a SIZDI (Yasa 6 — büyük ara veri)"
    assert rc in (0, 1)


def test_calistir_A_ve_B_gercekten_FARKLI_uyelik_fonksiyonuyla_calisir(sahne, monkeypatch):
    """`calistir()`in KENDİSİNİN her koşuma DOĞRU `uyelik` fonksiyonunu geçirdiğinin kanıtı
    (MUTASYON 1'in `calistir()` düzeyindeki hâli): `koşum_calistir`i doğrudan çağıran diğer
    testler `calistir()`i BYPASS eder — bu test etmez. MEM+SPOT AYNI ANDA sinyal alır: A'nın
    `uyelik` YANLIŞLIKLA `None`a (TABAN'a) düşürülseydi (`fonksiyonlar['A']` yerine
    `fonksiyonlar['TABAN']`) `n_islem` TABAN'la EŞİT çıkardı — aşağıdaki KESİN EŞİTSİZLİK bu
    regresyonu YAKALAR (ısırdığı kanıtlanmıştır: rapora bkz., bu satır kaynağı GERÇEKTEN mutasyona
    uğratılıp bir kez kırmızı koşuldu)."""
    monkeypatch.setattr(strategy_mod, "scan_entry", _sinyal_yap({"MEM", "SPOT"}))
    o = _olcum()
    sonuc = o.calistir(bars_dir=sahne["bars_dir"], girdi_html=sahne["html_yolu"],
                       guncel_liste_yolu=sahne["guncel_yolu"], kart_yolu=KART_YOLU,
                       baslangic=sahne["start"], bitis=sahne["end"],
                       evren=["MEM", "EQR", "SPOT", "AAA"], index_symbol="IDX")
    assert sonuc["taban"]["n_islem"] > 0, "sahne hiç işlem üretmedi — kıyas VACUOUS olurdu"
    assert sonuc["a"]["n_islem"] < sonuc["taban"]["n_islem"], (
        "A'nın işlem sayısı TABAN'dan FARKLI değil — calistir() 'A' koşumuna doğru uyelik "
        "fonksiyonunu GEÇİRMİYOR OLABİLİR (MUTASYON 1 hedefi)")
    assert sonuc["b"]["n_islem"] > sonuc["a"]["n_islem"], (
        "B'nin işlem sayısı A'dan fazla değil — hiç-üye SPOT B'de geri gelmiyor olabilir")


def test_calistir_bars_uyusmuyorsa_ValueError(tmp_path):
    """`calistir` çözülemeyen bir `--bars-dir`de endeks barı bulamazsa (girdi eksik) UYDURMAZ,
    ValueError atar."""
    o = _olcum()
    bos_dir = tmp_path / "bos"
    bos_dir.mkdir()
    guncel = tmp_path / "guncel.json"
    guncel.write_text("[]", encoding="utf-8")
    html = tmp_path / "h.html"
    html.write_text("<table><tr><th>Effective Date</th><th>Added</th><th>Removed</th></tr></table>",
                    encoding="utf-8")
    with pytest.raises(ValueError, match="endeks barı"):
        o.calistir(bars_dir=bos_dir, girdi_html=html, guncel_liste_yolu=guncel, kart_yolu=KART_YOLU,
                  evren=["AAA"], index_symbol="IDX")


def test_calistir_manifest_degistiyse_gecerli_false_ve_kosumlar_yok(sahne):
    o = _olcum()
    onceki = sahne["bars_dir"].parent / "onceki_sonuc.json"
    onceki.write_text(json.dumps({"girdi_kimligi": {"bar_manifesti": {"BASKA": "sha"}}}), encoding="utf-8")
    sonuc = o.calistir(bars_dir=sahne["bars_dir"], girdi_html=sahne["html_yolu"],
                       guncel_liste_yolu=sahne["guncel_yolu"], kart_yolu=KART_YOLU,
                       baslangic=sahne["start"], bitis=sahne["end"],
                       manifest_kontrol_yolu=onceki, evren=["MEM", "EQR", "SPOT", "AAA"],
                       index_symbol="IDX")
    assert sonuc["gecerli"] is False
    assert sonuc["manifest_kontrolu"]["gecerli"] is False
    assert "taban" not in sonuc
