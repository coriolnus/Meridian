"""test_seed_boundary_sira_v411.py — TSK-035, 2026-09-04: `ledgerstamp.seed_boundary` SIRA ÇEVRİLDİ
(YOL-2 `trades.kaynak` > YOL-1 `reset_isareti`; YOL-1 çapraz-sağlama olarak KALIR).

BAĞLAM (ROADMAP TSK-035, brief `.superpowers/sdd/2026-09-04-tsk035/brief.md`): sınırın
sözleşmedeki anlamı "tohum defteri NEREDE BİTER" sorusudur. WP2-D bacak-1 (2026-08-14,
`test_wp2d_egri_kadansli_yazar_v245.py`) bu soruyu YOL-1'in (eğri zarfındaki SON reset işaretinin
DONMUŞ `egri_son_nokta` alanı) yanıtladığına karar vermişti — donmuşluk şartını sağlamak içindi
("eğriye nokta eklemek sınırı kaydırmasın"). Ama YOL-2 (`trades.kaynak`: `replay_seed` damgalı
satırların en geç `ts_close`u) AYNI donmuşluğu taşır (migrasyon bir satırı bir daha damgalamaz) ve
sözleşmenin sorduğu şeyi DOLAYLI değil DOĞRUDAN ölçer — bu tur sırayı çevirir: YOL-2 ÖNCE denenir,
YOL-1 yalnız YOL-2 hiç konuşamazsa ÇAPRAZ-SAĞLAMA olarak devreye girer. `yollar_ayrisik` bayrağının
hesabı AYNEN kalır (iki yol konuşup ANLAŞMADIYSA true) — değişen yalnız HANGİSİNİN KAZANDIĞI.

BU DOSYA İKİ DURUMU ÇİVİLER (brief D2/D3):
  (a) TAM DAMGALI dünya — reset YALNIZCA seed'in bittiği anda alınmış, yani iki yol ZATEN AYNI
      tarihi verir: sınır DEĞİŞMEZ (YOL-1 == YOL-2), yalnız `kaynak` alanı YOL-2'ye döner (D2a).
  (b) AYRIŞIK dünya — canlıda ÖLÇÜLEN gerçek örnek (2026-08-13): reset 2026-08-01'de donmuş ve
      O ANKİ son noktayı (2026-07-20) taşıyor; reset'ten SONRA yenilenen tohum defterine en geç
      2026-07-24 kapanışlı damgalı satırlar girmiş. Yeni sıra YOL-2'yi (2026-07-24) seçer,
      `yollar_ayrisik: true` (D2b).
  MUTASYON (bu oturumda ELLE doğrulandı, kalıcı test DEĞİL — CLAUDE.md §6 "çivi yeşili kanıt
  değildir"): `seed_boundary` içindeki `if d_damga / elif d_reset` sırası `if d_reset / elif
  d_damga`ya (ESKİ sıra) geri çevrildiğinde `test_B_ayrisik_YENI_SIRA_YOL2yi_secer` KIRMIZI oldu;
  geri alınıp `meridian/__pycache__/ledgerstamp.*.pyc` silindikten sonra tekrar YEŞİL doğrulandı.

Geri-açılış şartı (brief D2, modül başlığına da yazıldı): bu sıranın dayanağı canlı defterde
damgasız satır sayısının 0 olması (887/887, 2026-08-14 ölçümü) — o sayı > 0 çıkarsa bu kalem
YENİDEN AÇILIR. Canlı sayım bu turda ÖLÇÜLEMEDİ: rapora `None` + neden yazılıdır (pytest-dışı
koşum bu depoda yasak — CLAUDE.md §2 — canlı deftere ancak A1'de, pytest DIŞINDA bir betikle
bakılabilir ve öyle bir koşum `meridian.obs`'a ulaşıp canlı yerel deftere yazardı).

HİÇBİR TEST CANLI STATE'E YAZMAZ: hepsi `sandbox_state` üzerinden koşar.
"""
from __future__ import annotations

from meridian import ledgerstamp, sermaye, store

EQ = ledgerstamp.EQUITY


# =================================================================================================
# YARDIMCILAR (şekiller v245/v264 fikstürleriyle BİREBİR — aynı yazarın izini ölçüyoruz)
# =================================================================================================
def _islem(i: int, ts_close: str, kaynak: str | None = ledgerstamp.REPLAY_SEED) -> dict:
    r = {"id": f"T{i:05d}", "ts_open": "2023-01-10", "ts_close": ts_close, "ticker": "AAA",
         "side": "long", "entry": 100.0, "exit": 101.0, "qty": 10, "r_multiple": 0.5,
         "pnl_pct": 0.01, "pnl_dollars": -1000.0, "costs": 5.0, "exit_reason": "stop",
         "strategy_version": 4, "regime": "trend_up", "setup": "breakout_vcp", "bars_held": 5}
    if kaynak:
        r["kaynak"] = kaynak
    return r


def _isaret(egri_son: str, id_: str = "SR-20260801T151429") -> dict:
    """`sermaye.uygula`nın zarfa bastığı işaretin şekli (sermaye.py::uygula)."""
    return {"id": id_, "tarih": "2026-08-01T15:14:29+00:00", "tip": "paper_equity_reset",
            "onceki_deger": 94457.91, "yeni_deger": 100000.0,
            "egri_son_nokta": [egri_son, 94457.91], "gerekce": "fikstür TSK-035"}


def _egri(son: str, deger: float = 94457.91, *, isaret: bool = True,
          isaret_id: str = "SR-20260801T151429") -> None:
    eq = {"version": 4, "points": [["2023-01-12", 100000.0], [son, deger]]}
    if isaret:
        eq[sermaye.CURVE_MARK_KEY] = [_isaret(son, id_=isaret_id)]
    store.write_json(EQ, eq)


# =================================================================================================
# (a) TAM DAMGALI — iki yol ZATEN aynı tarihi verir: sınır DEĞİŞMEZ, kaynak YOL-2'ye döner
# =================================================================================================
def test_A_tam_damgali_dunyada_SINIR_DEGISMEZ_ama_kaynak_YOL2ye_doner(sandbox_state):
    """Reset, seed'in TAM BİTTİĞİ anda alınmış (canlıda "reset sonrası hiç canlı gün geçmemiş"
    hâlin fikstürü): işaretin `egri_son_nokta`sı ile damgalı satırların en geç `ts_close`u AYNI
    tarih (2023-02-03). D2a'nın ölçtüğü şey tam olarak bu: davranış-nötrlük — dışarıdan bakan
    `replay_end` KIPIRDAMAZ, yalnız İÇERİDE hangi yolun konuştuğu değişir.

    GÜVEN GÜNCELLENDİ (TSK-035 r1, Rol-1 hükmü 2026-09-04 ~20:35Z): bu senaryo TAM OLARAK (c)
    hâlidir — iki yol AYNI tarihi veriyor, yani çapraz-sağlama DOĞRULADI. Önceki tur `guven`i hep
    "orta" döndürüyordu (DOĞRUDAN ölçüm YEDEKTEN daha düşük güvenle etiketleniyordu); bu artık
    "yuksek"e çıkar. DEĞER (`kaynak`, `replay_end`) DEĞİŞMEDİ, yalnız güven etiketi düzeltildi."""
    store.write_jsonl(ledgerstamp.LEDGER, [_islem(i, f"2023-02-0{i+1}") for i in range(3)])
    _egri("2023-02-03")
    b = ledgerstamp.seed_boundary()
    # ÖN KOŞUL: iki yol GERÇEKTEN aynı tarihi veriyor (yoksa test D2a'yı ölçmüyor demektir)
    assert b["yollar"] == {ledgerstamp.KAYNAK_RESET: "2023-02-03",
                           ledgerstamp.KAYNAK_DAMGA: "2023-02-03"}
    assert b["yollar_ayrisik"] is False
    # D2a — DAVRANIŞ-NÖTRLÜK: dışarıdan görünen sınır DEĞİŞMEDİ
    assert b["replay_end"] == "2023-02-03"
    # YENİ SIRA görünür: kaynak artık YOL-2 (DOĞRUDAN ölçüm); güven (r1) çapraz-sağlama DOĞRULADI
    assert b["kaynak"] == ledgerstamp.KAYNAK_DAMGA and b["guven"] == "yuksek"


def test_A_YOL1_tek_basina_hala_calisir_reset_YOKKEN(sandbox_state):
    """Pozitif taraf: YOL-2 hiç konuşamıyorsa (damgalı satır yok) çapraz-sağlama yolu (YOL-1)
    hâlâ ÇALIŞIR — sıra çevrildi diye YOL-1 SİLİNMEDİ, sırası değişti."""
    _egri("2023-02-03")   # reset var, defter BOŞ (damgalı satır yok)
    store.write_jsonl(ledgerstamp.LEDGER, [])
    b = ledgerstamp.seed_boundary()
    assert b["yollar"] == {ledgerstamp.KAYNAK_RESET: "2023-02-03", ledgerstamp.KAYNAK_DAMGA: None}
    assert b["replay_end"] == "2023-02-03"
    assert b["kaynak"] == ledgerstamp.KAYNAK_RESET and b["guven"] == "yuksek"


# =================================================================================================
# (b) AYRIŞIK — canlıda ÖLÇÜLEN gerçek örnek: yeni sıra YOL-2'yi seçer
# =================================================================================================
def test_B_ayrisik_YENI_SIRA_YOL2yi_secer(sandbox_state):
    """CANLIDA ÖLÇÜLEN HÂLİN FİKSTÜRÜ (2026-08-14, `test_B_IKI_YOL_AYRISIRSA_beyan_edilir`'in
    AYNISI — bu kez YENİ sıranın hangi tarafı seçtiği çivileniyor): reset işareti 2026-08-01'de
    donmuş ve O ANKİ son noktayı (2026-07-20) taşıyor; reset'ten SONRA yenilenen tohum defterine
    en geç 2026-07-24 kapanışlı damgalı satırlar girmiş — iki yol AYRIŞIYOR.

    ESKİ sıra (YOL-1 önce) donmuş olanı (2026-07-20) seçerdi. YENİ sıra (TSK-035) DOĞRUDAN ölçümü
    (2026-07-24, YOL-2) seçer — `yollar_ayrisik` bayrağı (hesabı AYNEN) true kalır, fark
    `neden` metninde AYRIŞMA olarak beyanlıdır."""
    store.write_jsonl(ledgerstamp.LEDGER,
                      [_islem(0, "2023-02-01"), _islem(1, "2026-07-24")])
    _egri("2026-07-20")
    b = ledgerstamp.seed_boundary()
    # ÖN KOŞUL: iki yol GERÇEKTEN ayrışıyor (yoksa test D2b'yi ölçmüyor demektir)
    assert b["yollar"] == {ledgerstamp.KAYNAK_RESET: "2026-07-20",
                           ledgerstamp.KAYNAK_DAMGA: "2026-07-24"}
    assert b["yollar_ayrisik"] is True and "AYRIŞMA" in b["neden"]
    # D2b — YENİ SIRA: YOL-2 kazanır
    assert b["replay_end"] == "2026-07-24"
    assert b["kaynak"] == ledgerstamp.KAYNAK_DAMGA and b["guven"] == "orta"
    # YOL-1'in değeri KAYBOLMADI — çapraz-sağlama olarak `yollar`da görünür durur
    assert b["reset_isareti"]["isaret_id"] == "SR-20260801T151429"


def test_B_ayrisik_iken_YOL1_bilgi_olarak_HALA_GORUNUR(sandbox_state):
    """`yollar` sözleşmesi (D1: "dönen sözlüğün alanları AYNI") — kaybeden yol SİLİNMEZ, yan yana
    durur. Okuyucu tek bir tarihe bakıp iki kanıtın anlaştığını sanmasın diye."""
    store.write_jsonl(ledgerstamp.LEDGER, [_islem(0, "2026-07-24")])
    _egri("2026-07-20")
    b = ledgerstamp.seed_boundary()
    assert b["yollar"][ledgerstamp.KAYNAK_RESET] == "2026-07-20"
    assert b["yollar"][ledgerstamp.KAYNAK_DAMGA] == "2026-07-24"
    assert b["replay_end"] == b["yollar"][ledgerstamp.KAYNAK_DAMGA]


def test_B_yollar_AYNI_ise_bayrak_INER(sandbox_state):
    """Pozitif kontrol: iki yol AYNI sayıyı verdiğinde `yollar_ayrisik` False'a döner — bayrak ölü
    bir sabit değil, gerçekten AYRIŞMAYI ölçüyor."""
    store.write_jsonl(ledgerstamp.LEDGER, [_islem(0, "2026-07-20")])
    _egri("2026-07-20")
    b = ledgerstamp.seed_boundary()
    assert b["yollar_ayrisik"] is False and "AYRIŞMA" not in b["neden"]
    assert b["replay_end"] == "2026-07-20"


# =================================================================================================
# ÜÇÜNCÜ HÂL — hiçbiri konuşamazsa (sıra çevrilse de) hâlâ `yok`
# =================================================================================================
def test_C_hicbiri_konusamazsa_hala_YOK(sandbox_state):
    store.write_jsonl(ledgerstamp.LEDGER, [_islem(0, "2023-02-01", kaynak=None)])
    store.write_json(EQ, {"version": 4, "points": [["2023-01-12", 100000.0]]})
    b = ledgerstamp.seed_boundary()
    assert b["replay_end"] is None and b["kaynak"] == ledgerstamp.KAYNAK_YOK
    assert b["yollar"] == {ledgerstamp.KAYNAK_RESET: None, ledgerstamp.KAYNAK_DAMGA: None}
    assert b["yollar_ayrisik"] is False


# =================================================================================================
# TSK-035 r1 (Rol-1 hükmü, 2026-09-04 ~20:35Z): `guven` çapraz-sağlamayı YANSITSIN.
# KAYNAK_DAMGA (YOL-2) kazandığında: d_reset VE d_reset == d_damga ise "yuksek" (iki bağımsız
# kanıt ANLAŞTI), aksi hâlde (YOL-1 sessiz YA DA AYRIŞIK) "orta" (tek kanıt). KAYNAK_RESET ve
# KAYNAK_YOK dalları DEĞİŞMEDİ — yukarıdaki testler (test_A_YOL1_tek_basina_..., test_C_...)
# zaten bunu çiviliyor.
# =================================================================================================
def test_D_c_capraz_saglama_DOGRULARSA_guven_YUKSEK(sandbox_state):
    """(c) iki yol AYNI tarihi veriyor → çapraz-sağlama DOĞRULADI → `guven == "yuksek"`.
    `neden` metni doğrulama cümlesini AÇIKÇA taşır (okuyucu neden yükseldiğini görür)."""
    store.write_jsonl(ledgerstamp.LEDGER, [_islem(0, "2026-07-20")])
    _egri("2026-07-20")
    b = ledgerstamp.seed_boundary()
    assert b["yollar_ayrisik"] is False
    assert b["kaynak"] == ledgerstamp.KAYNAK_DAMGA
    assert b["guven"] == "yuksek"
    assert "çapraz-sağlama" in b["neden"] and "AYNI tarihi doğruladı" in b["neden"]


def test_D_d_ayrisikken_guven_ORTA(sandbox_state):
    """(d) iki yol AYRIŞIYOR (YOL-1 konuşuyor ama farklı tarih diyor) → çapraz-sağlama
    DOĞRULAMADI → `guven == "orta"` (tek kanıta mahkûm — donmuş reset işareti farklı bir tarihte
    kalmış olabilir, TSK-035 AYRIŞMA vakası)."""
    store.write_jsonl(ledgerstamp.LEDGER,
                      [_islem(0, "2023-02-01"), _islem(1, "2026-07-24")])
    _egri("2026-07-20")
    b = ledgerstamp.seed_boundary()
    assert b["yollar_ayrisik"] is True
    assert b["kaynak"] == ledgerstamp.KAYNAK_DAMGA
    assert b["guven"] == "orta"
    assert "çapraz-sağlama" in b["neden"] and "AYRIŞIK" in b["neden"]


def test_D_e_YOL1_sessizken_guven_ORTA(sandbox_state):
    """(e) YOL-1 (reset işareti) hiç YOK — eğride konuşabilen işaret yok, yalnız YOL-2 (damga)
    konuşuyor → çapraz-sağlama YAPILAMAZ → `guven == "orta"` (aynı senaryo
    `test_B_ISARET_YOKSA_YEDEK_YOL_trades_damgasindan_okur`da `tests/test_defter_kaynak_damgasi_
    v140.py`'de DEĞER olarak zaten çivili; burada `neden` metnindeki 'sessiz' beyanı ölçülüyor)."""
    store.write_jsonl(ledgerstamp.LEDGER, [_islem(0, "2023-02-01"), _islem(1, "2023-02-03")])
    _egri("2023-02-03", isaret=False)   # eğri var ama reset işareti YOK → d_reset None
    b = ledgerstamp.seed_boundary()
    assert b["yollar"] == {ledgerstamp.KAYNAK_RESET: None, ledgerstamp.KAYNAK_DAMGA: "2023-02-03"}
    assert b["yollar_ayrisik"] is False
    assert b["kaynak"] == ledgerstamp.KAYNAK_DAMGA
    assert b["guven"] == "orta"
    assert "çapraz-sağlama" in b["neden"] and "sessiz" in b["neden"]
