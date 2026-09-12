"""test_edg088_sayim_v461.py — EDG-2026-088 gölge pilot B1 / Task 3: SAYAÇ ÇİVİSİ.

NE ÇİVİLENİR (plan `docs/superpowers/plans/2026-09-08-golge-pilot-b1.md` Task 3):
`research/olcumler/edg088_golge_pilot/sayim.py` — kartın K=2 birincil ölçüsünü ve üç pozitif
kontrolünü `state/golge_icra.jsonl` şemasından sayar, HÜKÜM VERMEZ.

TEST NUMARASI — v458 DEĞİL v461. Task 1 ve Task 2 raporları Task 3'e **v458** devretmişti; o
numara bu tur açılmadan ÖNCE ana checkout'ta doldu (`test_roadmap_arsiv_sayimi_v458.py`), v459 ve
v460 da paralel worktree'lerde alındı (`test_arama_api_v459.py`, `test_arama_ui_v460.py`).
Ölçüm ana checkout + TÜM worktree'ler üzerinde yapıldı; ilk boş numara **v461**di. Numara
KİMLİKTİR ve tek worktree'de ölçülürse KÖRDÜR — Task 1 raporunun §2 dersi bu turda TEKRARLANDI.

PK (1) SENARYOSU İTHAL EDİLİR, KOPYALANMAZ (tek-kaynak yasası). Beş yolun barları, planları ve
koşum düzeni motorun kendi çivisinde (`tests/test_golge_icra_v456.py`) yaşıyor; ikinci bir kopya
yazmak "aynı gerçeğin iki kopyası sessizce ayrışır" sınıfının ta kendisi olurdu. Buradaki çivi o
senaryoyu ÇAĞIRIR ve sayacın onun ÜRETTİĞİ defterden aynı sayıyı çıkarmasını ister — yani ölçüm
zinciri motor → defter → sayaç boyunca UÇTAN UCA sınanır, sayacın kendi sentetik defteri üzerinde
değil.

PAYDA KURALI TEK YERDE (tur 2 düzeltmesi, 2026-09-12). `sayilir` / `olculdu` / `olculemeyen_neden`
artık motorda yaşıyor ve sayaç onları İTHAL ediyor; kopya kalktığı için ayrışma çivisi bir KİMLİK
sınamasına döndü (`test_A2_payda_yuklemi_MOTORDAN_ITHAL_edilir_ikinci_yazim_YOK`,
`sayim.sayilir is golge_icra.sayilir`). Uçtan uca ayrışma ölçümü
(`test_AYRISMA_motorun_ozeti_ile_sayac_AYNI_defterde_AYNI_sayiyi_verir`) KALDI: aynı defterde
motorun `ozet()`i ile sayaç aynı sayıyı ve aynı dağılımları vermek zorundadır.
K PAYDASI KOL SÜZER: `kol == dormant`. Kontrol kolu PK (2)'nin paydasıdır, hipotezin DEĞİL.

EŞİK SAYILARI BU DOSYADA DA YAZILMAZ. 30 / 0,0 / 0,40 / 120 / 0,05 hiçbir iddiada literal olarak
geçmez; hepsi `golge_icra` sabitlerinden ve kart YAML'ından OKUNUR. Literal yazsaydım kartın
donuk eşiği ÜÇÜNCÜ bir kopya kazanırdı.

KAPILAR: `sandbox_state` motoru koşturan çivilerde AÇIKÇA istenir (autouse DEĞİL, ölçüldü);
sayacın kendisi `config.STATE`e hiç dokunmaz ve yalnız `tmp_path` altında, `subprocess` ile,
operatörün koşacağı BİÇİMDE koşulur.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import subprocess
import sys

import pytest
import yaml

from meridian import golge_icra as gi
from tests.conftest import betikten_modul_yukle
# PK (1) SENARYOSUNUN TEK KAYNAĞI motorun çivisidir (docstring'deki gerekçe).
from tests.test_golge_icra_v456 import _pk1_kosusu

KOK = pathlib.Path(__file__).resolve().parents[1]
BETIK_YOLU = KOK / "research" / "olcumler" / "edg088_golge_pilot" / "sayim.py"
KART_YOLU = KOK / "research" / "cards" / "EDG-2026-088-uyuyan-kurulum-golge-pilot.yaml"
GOAL_YOLU = KOK / "state" / "goal.yaml"
PK3_ARTEFAKT = (KOK / "research" / "olcumler" / "edg049_dormant_2026-08-23"
                / "islemler_tam_dormant_acik.json")

#: PK (1)'in EL HESABI — motorun çivisiyle AYNI aritmetik, sayı olarak DEĞİL İFADE olarak yazılı:
#: AAA −1 · BBB +1,5 · CCC −0,5/6 · DDD +1/6 · EEE R=None. Toplam = 0,5 + 0,5/6.
PK1_TOPLAM_R = 0.5 + 0.5 / 6.0
PK1_N = 4

#: PK (2) SAHNESİNİN EL HESABI PAYI (türetimi `test_A3_friksiyon_payi_...` docstring'inde):
#: `_gercek_broker_satiri()` sahnesinde broker 16,17 $ sürtünme uygular ve R paydası 1000,169 $'dır
#: → 0,016167 R. SAYI BURADA BİR KEZ yazılıdır; formülü yeniden yazan bir "ayna" iddia, sayacın
#: kendi hesabını kendisiyle doğrulardı (inceleme M4-03).
PAY_R = 0.016167


def _sayim():
    return betikten_modul_yukle(BETIK_YOLU, "edg088_sayim")


def _kart() -> dict:
    return yaml.safe_load(KART_YOLU.read_text(encoding="utf-8")) or {}


def _defter_yaz(yol: pathlib.Path, satirlar: list[dict]) -> pathlib.Path:
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in satirlar),
                   encoding="utf-8")
    return yol


def _satir(plan_id, *, r, kol="dormant", kurulum="pullback", hukum="REVIEW",
           hash_="a" * 64, gun_once=1, cikis="2026-09-10", giris=101.0, stop=95.0,
           cikis_neden="stop", ticker=None):
    """Şemanın TAMAMINI taşıyan sentetik defter satırı — alan adları motordan OKUNUR.

    `gi.SATIR_ALANLARI` üzerinden kurulur: motora yeni bir alan eklenirse bu kurucu onu `None`
    ile taşır ve sayaç eksik anahtarla karşılaşmaz (şema kayması sessizce testin içinde ölmez).
    """
    ts = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=gun_once)).isoformat()
    dolu = {"ts": ts, "plan_id": plan_id, "ticker": (ticker or plan_id), "kurulum": kurulum,
            "hukum": hukum, "kol": kol, "ts_plan": "2026-09-09",
            "giris_ts": "2026-09-09", "giris_fiyat": giris, "stop": stop, "hedef": 110.0,
            "cikis_ts": cikis, "cikis_fiyat": 95.0,
            "cikis_neden": (gi.GIRIS_YOK if r is None else cikis_neden), "R": r, "bar_n": 3,
            "kaynak_bar_hash": hash_, "bar_kaynak": gi.BAR_KAYNAKLARI[0],
            "strategy_version": 3, "giris_reddi": (None if r is not None else "tetik_gelmedi"),
            "olculemedi": None}
    return {ad: dolu.get(ad) for ad in gi.SATIR_ALANLARI}


def _dolu_pencere(n: int | None = None) -> list[dict]:
    """Pencereyi DOLDURAN defter: n = kartın alt sınırı, hepsi taze (geçen gün ≪ üst sınır).

    Alternatif R'ler kazanma oranını 0,5'e sabitler; sayı ELLE değil kuralla doğar.
    """
    n = n or gi.N_ALT
    return [_satir(f"P-{i:03d}", r=(1.0 if i % 2 == 0 else -0.5), gun_once=1)
            for i in range(n)]


def _acik_yaz(dizin: pathlib.Path, gun_once: int) -> pathlib.Path:
    """Defterin YANINDAKİ `golge_icra_acik.json` — pencere BEYANININ evi (motor oraya yazar)."""
    kok = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=gun_once)).date().isoformat()
    yol = dizin / gi.ACIK
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text(json.dumps({"schema": gi.SEMA, "kart": gi.KART, "pencere_baslangic": kok,
                               "son_seans": None, "acik": {}, "bekleyen_giris": {},
                               "islenen": []}, ensure_ascii=False), encoding="utf-8")
    return yol


def _kosum(tmp_path, satirlar, pencere_gun_once=None, **kw):
    s = _sayim()
    defter = _defter_yaz(tmp_path / "state" / "golge_icra.jsonl", satirlar)
    if pencere_gun_once is not None:
        _acik_yaz(defter.parent, pencere_gun_once)
    kw.setdefault("kart", KART_YOLU)
    kw.setdefault("goal", GOAL_YOLU)
    return s, s.calistir(defter=defter, **kw), defter


# =================================================================================================
# ÇİVİ 1 — PK (1) KİMLİK KONTROLÜ: motorun ÜRETTİĞİ defterden el hesabı BİREBİR çıkar
# =================================================================================================
def test_civi1_PK1_motorun_defterinden_toplam_R_EL_HESABIYLA_birebir(sandbox_state, tmp_path):
    """Beş sentetik yol motorda koşar, defter sayaca verilir: toplam R = 0,5 + 0,5/6.

    `EEE` (tetik gelmedi, R=None) paydada DEĞİLDİR — n dörttür, beş değil.
    """
    _pk1_kosusu()
    from meridian import store
    satirlar = store.read_jsonl(gi.DEFTER)
    assert len(satirlar) == 5, "motor beş satır yazmadı — senaryo kaydı"

    s, sonuc, _ = _kosum(tmp_path, satirlar)
    assert sonuc["n"] == PK1_N, sonuc["n"]
    assert sonuc["toplam_r"] == pytest.approx(PK1_TOPLAM_R, abs=1e-6), sonuc["toplam_r"]
    assert sonuc["kazanma_orani"] == pytest.approx(0.5)
    # R'si ölçülmeyen satır TANIdır ve ADIYLA görünür (uydurma yasağı: 0 ile 'bilmiyorum' ayrı).
    assert any("P-e" in x and "tetik_gelmedi" in x for x in sonuc["olculemeyen"]), \
        sonuc["olculemeyen"]
    assert sonuc["cikis_neden_dagilimi"] == {"regime_flip": 1, "stop": 1, "target": 1,
                                             "time_stop": 1}, sonuc["cikis_neden_dagilimi"]


def test_civi1_MUTASYON_altinci_satir_toplami_DEGISTIRIR(sandbox_state, tmp_path):
    """Sayaç ölü değil: bir satır daha eklenince toplam R ve n DEĞİŞİR."""
    _pk1_kosusu()
    from meridian import store
    satirlar = store.read_jsonl(gi.DEFTER)
    _, once, _ = _kosum(tmp_path / "a", satirlar)
    _, sonra, _ = _kosum(tmp_path / "b", satirlar + [_satir("P-f", r=1.5)])
    assert sonra["n"] == once["n"] + 1
    assert sonra["toplam_r"] == pytest.approx(once["toplam_r"] + 1.5, abs=1e-6)


def test_AYRISMA_motorun_ozeti_ile_sayac_AYNI_defterde_AYNI_sayiyi_verir(sandbox_state, tmp_path):
    """Payda kuralı artık TEK YERDE (motor) — bu çivi uçtan uca ayrışmayı ölçmeye devam eder."""
    _pk1_kosusu()
    from meridian import store
    satirlar = store.read_jsonl(gi.DEFTER)
    ozet = gi.ozet()
    _, sonuc, _ = _kosum(tmp_path, satirlar)
    assert sonuc["n"] == ozet["n"]
    assert sonuc["toplam_r"] == pytest.approx(ozet["toplam_r"], abs=1e-6)
    assert sonuc["kazanma_orani"] == pytest.approx(ozet["kazanma_orani"], abs=1e-4)
    assert (sonuc["pf"] is None) == (ozet["pf"] is None)
    for alan in ("hukum_dagilimi", "kurulum_kirilimi", "kol_kirilimi", "cikis_neden_dagilimi",
                 "giren_n", "giren_hukum_dagilimi", "giren_kurulum_kirilimi"):
        assert sonuc[alan] == ozet[alan], (alan, sonuc[alan], ozet[alan])


def test_A2_payda_yuklemi_MOTORDAN_ITHAL_edilir_ikinci_yazim_YOK():
    """TEK-KAYNAK: kural kopyalanmaz, İTHAL edilir — kimlik sınaması (`is`) bunu mühürler.

    Kopya olsaydı iki gövde sessizce ayrışabilirdi; `is` ayrışmayı YAPISAL olarak imkânsız kılar.
    """
    s = _sayim()
    assert s.sayilir is gi.sayilir, "sayaç payda yüklemini ikinci kez yazmış"
    assert s.olculdu is gi.olculdu
    assert s.olculemeyen_neden is gi.olculemeyen_neden
    govde = BETIK_YOLU.read_text(encoding="utf-8")
    assert "def sayilir(" not in govde, "payda yüklemi sayaçta YENİDEN tanımlanmış"


def test_A2_KONTROL_kolu_K_paydasina_GIRMEZ(sandbox_state, tmp_path):
    """Kontrol satırı n/toplam_r'ye karışmaz; TANIda (`kol_kirilimi`, `giren_n`) ADIYLA durur."""
    golge = [_satir("P-d1", r=0.5, kol="dormant"), _satir("P-k1", r=2.0, kol="kontrol")]
    _, sonuc, _ = _kosum(tmp_path, golge)
    assert sonuc["n"] == 1, "kontrol kolu K paydasında"
    assert sonuc["toplam_r"] == pytest.approx(0.5, abs=1e-9)
    assert sonuc["giren_n"] == 2 and sonuc["kol_kirilimi"] == {"dormant": 1, "kontrol": 1}


# =================================================================================================
# ÇİVİ 2 — PK (2) KONTROL KOLU + KILL#5 (düşerse HİÇBİR SAYI YAYILMAZ)
# =================================================================================================
def _goal() -> dict:
    return yaml.safe_load(GOAL_YOLU.read_text(encoding="utf-8")) or {}


def _gercek_broker_satiri(*, plan_id="P-k1", tetik=100.0, acilis=101.0, stop=95.0,
                          ham_cikis=95.0, neden="stop", ticker="XXX") -> dict:
    """ÜRETİMİN KENDİ `PaperBroker`ı ile kapanmış GERÇEK işlem satırı.

    Sürtünmeyi (kayma + komisyon) bu satıra BROKER uygular: `entry` kaymalı dolum, `exit` kaymalı
    çıkış, `costs` broker'ın kendi topladığı toplam sürtünmedir. PK (2) payının doğruluğu bu
    satırın ALANLARINA karşı ölçülür — elle kurulmuş bir sözlüğe karşı değil (o, formülü kendi
    kendine doğrulayan bir ayna olurdu).
    """
    from meridian import broker as brk
    g = _goal()
    b = brk.PaperBroker(equity=100_000.0, slippage_bps=float(g["slippage_bps"]),
                        commission_per_share=float(g["commission_per_share"]))
    plan = {"id": plan_id, "ticker": ticker, "entry_trigger": tetik, "stop": stop,
            "profit_target": 110.0, "size_r": 1.0}
    poz = b.fill_entry(plan, next_open=acilis, ts="2026-09-09", equity=100_000.0)
    assert poz is not None, "broker giriş doldurmadı — sahne kurulamadı"
    row = b.close_position(ticker, raw_exit=ham_cikis, reason=neden, ts="2026-09-10")
    # KAYNAK DAMGASI YAZARIN İŞİDİR (`loop._persist_trade` → `live_paper`); broker onu BASMAZ.
    # Sayaç "GERÇEK işlem" ölçütünü bu damgadan okur, o yüzden sahne onu taşır.
    from meridian import ledgerstamp
    return {**row, "regime": "trend_up", "score": 80, "setup": "pullback",
            "strategy_version": 3, ledgerstamp.FIELD: ledgerstamp.LIVE_PAPER}


def _kontrol_defteri(fark: float):
    """Bir kontrol çifti: gölge R = gerçek R + `fark`. Gerçek taraf BROKER'ın ürettiği satırdır."""
    gercek_satir = _gercek_broker_satiri()
    golge = [_satir("P-k1", r=float(gercek_satir["r_multiple"]) + fark, kol="kontrol",
                    giris=101.0, stop=95.0),
             _satir("P-d1", r=0.5, kol="dormant")]
    return golge, [gercek_satir]


# ---- A3: PK (2) sürtünme payı ÜRETİMİN KENDİ uygulamasından türer -------------------------------
def test_A3_friksiyon_payi_URETIMIN_KENDI_surtunmesinden_turer(tmp_path):
    """M3-02: pay EL FORMÜLÜYLE değil, broker'ın uyguladığı sürtünmeden ölçülür.

    EL HESABI (broker'ın KENDİ sabitleriyle, `goal.yaml`: kayma 5 bps tek yön, komisyon 0):
      dolum   = 101 · (1 + 0,0005) = 101,0505 · qty = floor(1000 / 6,0505) = 165
      çıkış   = 95 · (1 − 0,0005)  = 94,9525
      sürtünme = 165·(101,0505 − 101) + 165·(95 − 94,9525) = 8,3325 + 7,8375 = 16,17 $
      R paydası = pnl_dollars / r_multiple = −1006,17 / −1,006 = 1000,169 $
      pay      = 16,17 / 1000,169 = 0,016167 R
    ÇIKIŞ BACAĞI ÇIKIŞ FİYATIYLA ölçeklenir (7,8375), giriş fiyatıyla DEĞİL (8,3325) — eski el
    formülü iki bacağı da girişten ölçüp 0,016833 veriyordu.
    """
    _, sonuc = _pk2_kosum(tmp_path, 0.001)
    k = sonuc["kontrol"]
    gercek = _gercek_broker_satiri()
    assert gercek["qty"] == 165 and gercek["costs"] == pytest.approx(16.17, abs=1e-9), gercek

    assert k["komisyon_kayma_payi"] == pytest.approx(PAY_R, abs=1e-6), k
    # BAĞIMSIZ ÇAPRAZ ÖLÇÜM: broker'ın KENDİ `costs` alanı ile aynı sayıyı vermeli (yeniden
    # kurma, üretimin sürtünme uygulamasının tersidir — taklidi değil).
    risk = float(gercek["pnl_dollars"]) / float(gercek["r_multiple"])
    assert k["komisyon_kayma_payi"] == pytest.approx(gercek["costs"] / risk, abs=1e-6)
    # ESKİ EL FORMÜLÜ (iki bacak da giriş fiyatından) BAŞKA bir sayıdır — ayrım ölçülüdür.
    g = _goal()
    eski = (2 * (float(g["slippage_bps"]) / 1e4) * 101.0
            + 2 * float(g["commission_per_share"])) / (101.0 - 95.0)
    assert abs(k["komisyon_kayma_payi"] - eski) > 1e-4, (k["komisyon_kayma_payi"], eski)
    # KAYNAK BEYANLIDIR: hangi formülün konuştuğu raporda ADIYLA durur.
    assert "PaperBroker" in (k["pay_kaynagi"] or ""), k["pay_kaynagi"]


def test_A3_surtunme_alani_YOKSA_pay_None_ve_NEDEN_adiyla(tmp_path):
    """Uydurma yasağı: gerçek satırda alan yoksa pay 0 değil `None` + adlı neden."""
    golge, gercek = _kontrol_defteri(0.001)
    eksik = {k: v for k, v in gercek[0].items() if k not in ("entry", "exit", "qty", "costs")}
    s = _sayim()
    defter = _defter_yaz(tmp_path / "state" / "golge_icra.jsonl", golge)
    _defter_yaz(tmp_path / "state" / "trades.jsonl", [eksik])
    sonuc = s.calistir(defter=defter, kart=KART_YOLU, goal=GOAL_YOLU)
    k = sonuc["kontrol"]
    assert k["komisyon_kayma_payi"] is None and k["gecti"] is None
    assert k["n_payi_olculemeyen"] == 1, k
    assert any("PK (2)" in x for x in sonuc["olculemeyen"]), sonuc["olculemeyen"]


def test_A3b_kucuk_R_paydasi_HASSASIYETSIZ_pay_None_ve_NEDEN_adiyla(tmp_path):
    """Rol-1 hükmü (tur-2 kaygı 4): |r_multiple| < R_MULTIPLE_ALT → payda türetilmez, pay None.

    Hangi üretim değişikliğinde kırılır: alt sınır kaldırılır ya da 0'a çekilirse — küçük-R çiftte
    3 ondalık yuvarlama paydayı şişirir ve uydurulmuş bir pay PK (2)'ye girer."""
    golge, gercek = _kontrol_defteri(0.001)
    kucuk = dict(gercek[0]); kucuk["r_multiple"] = 0.01; kucuk["pnl_dollars"] = 10.0   # payda 1000 $, |R| < R_MULTIPLE_ALT
    s = _sayim()
    assert 0 < s.R_MULTIPLE_ALT <= 0.1
    defter = _defter_yaz(tmp_path / "state" / "golge_icra.jsonl", golge)
    _defter_yaz(tmp_path / "state" / "trades.jsonl", [kucuk])
    sonuc = s.calistir(defter=defter, kart=KART_YOLU, goal=GOAL_YOLU)
    k = sonuc["kontrol"]
    assert k["komisyon_kayma_payi"] is None and k["gecti"] is None
    assert k["n_payi_olculemeyen"] == 1, k
    nedenler = k.get("pay_olculemeyen_nedenleri") or []
    assert any("R_MULTIPLE_ALT" in str(x) for x in nedenler), (nedenler, sonuc["olculemeyen"])


def _pk2_kosum(tmp_path, fark, ek_golge=(), ek_gercek=()):
    golge, gercek = _kontrol_defteri(fark)
    golge = list(golge) + list(ek_golge)
    s = _sayim()
    defter = _defter_yaz(tmp_path / "state" / "golge_icra.jsonl", golge)
    _defter_yaz(tmp_path / "state" / "trades.jsonl", list(gercek) + list(ek_gercek))
    return s, s.calistir(defter=defter, kart=KART_YOLU, goal=GOAL_YOLU)


# ---- E: SAYAÇ (M3-05/07/08/09, M4-08/16) --------------------------------------------------------
def test_E1_PK3_AYRISIRSA_yayin_ENGELLENIR(tmp_path):
    """Kart: PK (3) çıkmazsa "harness KÖR sayılır". Kör bir harness'in sayısı YAYILMAZ.

    `esles=None` (ölçülmedi) ENGELLEMEZ — "ölçülmedi" ile "ölçüldü ve tutmadı" aynı şey değildir.
    """
    idler = _pk3_plan_idler()
    ayrisan = [_satir(pid, r=+1.0) for pid in idler]
    _, sonuc, _ = _kosum(tmp_path / "a", ayrisan + _dolu_pencere(), pk3=PK3_ARTEFAKT,
                         pencere_gun_once=2)
    assert sonuc["pk3"]["esles"] is False
    assert any("PK (3)" in x for x in sonuc["yayin_engeli"]), sonuc["yayin_engeli"]
    assert sonuc["n"] is None and sonuc["toplam_r"] is None, "kör harness sayı yaydı"

    _, olculmedi, _ = _kosum(tmp_path / "b", _dolu_pencere(), pk3=PK3_ARTEFAKT,
                             pencere_gun_once=2)
    assert olculmedi["pk3"]["esles"] is None
    assert olculmedi["yayin_engeli"] == [] and olculmedi["n"] == gi.N_ALT, \
        "ölçülemeyen PK sayıyı BASTIRDI — körlük üretir"


def test_E2_KARTA_YENI_ESIK_eklenince_AYRISMA_oter(tmp_path):
    """M3-05: ayrışma döngüsü yalnız eşleşme tablosunun 5 anahtarını geziyordu; kartta doğan
    yeni bir eşik SESSİZ kalıyordu — oysa modül şerhi "ADIYLA söyler" diye yazıyordu."""
    kart = _kart()
    kart["esikler"]["pf_alt"] = 1.5
    sahte = tmp_path / "sahte_kart.yaml"
    sahte.write_text(yaml.safe_dump(kart, allow_unicode=True), encoding="utf-8")
    _, sonuc, _ = _kosum(tmp_path, _dolu_pencere(), kart=sahte, pencere_gun_once=2)
    assert any("pf_alt" in x for x in sonuc["esik_ayrismasi"]), sonuc["esik_ayrismasi"]
    assert sonuc["n"] is None, "eşleşmemiş kart eşiği yayını engellemedi"


def test_E2_TANI_anahtarlarinin_MUAFIYETI_ACIK_ve_gerekceli():
    """Muafiyet BEYANLA olur: hangi kart anahtarının neden eşleşme tablosu DIŞINDA olduğu yazılı."""
    s = _sayim()
    assert "ci_yontem" in s.ESIK_MUAFIYETI, "donuk yöntem alanı muafiyet listesinde yok"
    for ad, gerekce in s.ESIK_MUAFIYETI.items():
        assert isinstance(gerekce, str) and len(gerekce) >= 20, (ad, gerekce)


def test_E3_GIRIS_REDDI_dagilimi_GIREN_kumesinden_kurulur(tmp_path):
    """M3-08: kartın tanı maddesi GİREN nüfusu sorar; giriş reddi dağılımı hiç yoktu."""
    red = _satir("P-red", r=None)
    _, sonuc, _ = _kosum(tmp_path, _dolu_pencere() + [red], pencere_gun_once=2)
    assert sonuc["giris_reddi_dagilimi"] == {"tetik_gelmedi": 1}, sonuc["giris_reddi_dagilimi"]
    assert sonuc["giren_n"] == gi.N_ALT + 1 and sonuc["n"] == gi.N_ALT
    assert sonuc["giren_hukum_dagilimi"]["REVIEW"] == gi.N_ALT + 1


def test_E4_kontrol_kolundaki_GIRIS_YOK_sayisi_TANIda_durur(tmp_path):
    """M4-08: gölgesi `giris_yok` olan kontrol satırı PK (2) paydasına giremez — ama SAYILIR."""
    yok = _satir("P-k2", r=None, kol="kontrol")
    _, sonuc = _pk2_kosum(tmp_path, 0.001, ek_golge=[yok])
    k = sonuc["kontrol"]
    assert k["giris_yok_n"] == 1, k
    assert k["n_golge_kontrol"] == 1, "eşlemeye giren kontrol satırı sayısı değişti"


def test_E5_esik_LITERALI_denetimi_SOZCUK_SINIRLI_ve_CI_ALT_R_dahil():
    """M4-16: alt-dizge denetimi hem yanlış alarm veriyordu hem `CI_ALT_R` denetim DIŞINDAYDI."""
    import re as _re
    src = BETIK_YOLU.read_text(encoding="utf-8")
    kod = "\n".join(s for s in src.splitlines() if not s.lstrip().startswith("#"))
    govde = kod.split('"""', 2)[-1]           # modül başlığı BEYANdır, sayı anabilir
    for sabit in (gi.N_ALT, gi.CI_ALT_R, gi.KAZANMA_ALT, gi.PENCERE_GUN, gi.FARK_R_UST):
        desen = _re.compile(rf"(?<![\d.]){_re.escape(str(sabit))}(?![\d.])")
        assert not desen.search(govde), f"eşik sayısı sayaç GÖVDESİNE kopyalanmış: {sabit}"
    # POZİTİF KONTROL: desen gerçekten yakalıyor mu (sözcük sınırı ölü bir denetim değil)?
    assert _re.search(rf"(?<![\d.]){gi.N_ALT}(?![\d.])", f"n={gi.N_ALT} ")
    assert not _re.search(rf"(?<![\d.]){gi.N_ALT}(?![\d.])", f"n=1{gi.N_ALT}0 ")


def test_E6_PAY_ve_FARK_AYNI_paydadan_olculur(tmp_path):
    """M3-09: `pay_ort` payı ölçülen çiftlerin, `ort_mutlak` TÜM çiftlerin ortalamasıydı.

    İki sayı farklı paydalardan gelince kıyas ("fark payın içinde mi") anlamını kaybeder. Hüküm
    kümesi artık payı ÖLÇÜLEBİLEN çiftlerdir; tüm çiftlerin dağılımı `tum_ciftler`de kendi `n`si
    ile ayrıca durur.
    """
    eksik_gercek = {k: v for k, v in _gercek_broker_satiri(plan_id="P-k2", ticker="YYY").items()
                    if k not in ("entry", "exit", "qty", "costs")}
    golge_k2 = _satir("P-k2", r=float(eksik_gercek["r_multiple"]) + 0.04, kol="kontrol")
    _, sonuc = _pk2_kosum(tmp_path, 0.001, ek_golge=[golge_k2], ek_gercek=[eksik_gercek])
    k = sonuc["kontrol"]
    assert k["n_cift"] == 2 and k["n_payi_olculemeyen"] == 1, k
    assert k["n_hukum_cifti"] == 1, "hüküm kümesi payı ölçülemeyen çifti de almış"
    assert k["ort_mutlak_fark_r"] == pytest.approx(0.001, abs=1e-6), \
        "hüküm farkı payı ölçülemeyen çiftle karışmış"
    assert k["tum_ciftler"]["n"] == 2
    assert k["tum_ciftler"]["ort_mutlak_fark_r"] == pytest.approx((0.001 + 0.04) / 2, abs=1e-6)


def test_E6_REPLAY_SEED_damgali_gercek_satir_PK2_ye_GIRMEZ(tmp_path):
    """Kart "GERÇEK işlemler" der: tohum simülasyonu damgalı satır kontrol paydasına giremez."""
    from meridian import ledgerstamp
    tohum = {**_gercek_broker_satiri(), ledgerstamp.FIELD: ledgerstamp.REPLAY_SEED}
    golge, _ = _kontrol_defteri(0.001)
    s = _sayim()
    defter = _defter_yaz(tmp_path / "state" / "golge_icra.jsonl", golge)
    _defter_yaz(tmp_path / "state" / "trades.jsonl", [tohum])
    sonuc = s.calistir(defter=defter, kart=KART_YOLU, goal=GOAL_YOLU)
    k = sonuc["kontrol"]
    assert k["n_cift"] == 0 and k["gecti"] is None, k
    assert k["n_gercek_disi"] == 1, "tohum satırı sessizce elendi — sayısı raporlanmadı"


def test_civi2_PK2_fark_esigin_ALTINDA_ise_gecti_True_ve_sayilar_yayilir(tmp_path):
    """Fark eşiğin ALTINDA ve komisyon+kayma payının İÇİNDE → `gecti=True`, sayılar durur."""
    fark = min(gi.FARK_R_UST, PAY_R) / 2.0
    _, sonuc = _pk2_kosum(tmp_path, fark)
    assert sonuc["kontrol"]["n_cift"] == 1, sonuc["kontrol"]
    assert sonuc["kontrol"]["gecti"] is True, sonuc["kontrol"]
    assert sonuc["kontrol"]["komisyon_kayma_payi"] == pytest.approx(PAY_R, abs=1e-6)
    assert sonuc["yayin_engeli"] == [] and sonuc["bastirilan"] == []
    assert sonuc["n"] == 1 and sonuc["toplam_r"] is not None, "kontrol kolu K paydasına girdi"


def test_civi2_PK2_DUSERSE_hicbir_sayi_yayilmaz(tmp_path):
    """Kill#5: fark eşiğin ÜSTÜNE itilince `gecti=False` VE K blokunun tamamı BASTIRILIR."""
    _, sonuc = _pk2_kosum(tmp_path, gi.FARK_R_UST * 1.2)
    assert sonuc["kontrol"]["gecti"] is False, sonuc["kontrol"]
    for alan in ("n", "toplam_r", "kazanma_orani", "pf", "ci", "ci_toplam",
                 "kurulum_kirilimi", "hukum_dagilimi", "cikis_neden_dagilimi"):
        assert sonuc[alan] is None, f"{alan} bastırılmadı: {sonuc[alan]}"
    assert set(sonuc["bastirilan"]) >= {"n", "toplam_r", "kazanma_orani", "ci"}
    assert any("kill#5" in x for x in sonuc["yayin_engeli"]), sonuc["yayin_engeli"]


def test_A4_PK2_ORTA_BOLGE_iki_sarti_BIRDEN_ister(tmp_path):
    """M4-03: kart İKİ şart birden ister — |fark| ≤ eşik **∧** |fark| ≤ komisyon+kayma payı.

    Sınanan bölge tam olarak şartların AYRIŞTIĞI yerdir: `pay < |fark| ≤ FARK_R_UST`. Eşik şartı
    TUTAR, pay şartı DÜŞER → `gecti` False olmalıdır. Bu sahne olmadan `and → or` mutantı hayatta
    kalıyordu (iki uç da iki şarttan aynı cevabı alıyordu).
    """
    fark = (PAY_R + gi.FARK_R_UST) / 2.0
    assert PAY_R < fark <= gi.FARK_R_UST, "sahne orta bölgede değil"
    _, sonuc = _pk2_kosum(tmp_path, fark)
    k = sonuc["kontrol"]
    assert k["ort_mutlak_fark_r"] == pytest.approx(fark, abs=1e-5), k
    assert k["ort_mutlak_fark_r"] <= float(k["esik"]), "eşik şartı bu sahnede TUTMALIYDI"
    assert k["ort_mutlak_fark_r"] > float(k["komisyon_kayma_payi"]), "pay şartı DÜŞMELİYDİ"
    assert k["gecti"] is False, "tek şart yetmiş — kapı bir KONJONKSİYON değil"
    assert sonuc["n"] is None and any("kill#5" in x for x in sonuc["yayin_engeli"])


def test_civi2_PK2_dusunce_MARKDOWN_da_sayi_tasimaz(tmp_path):
    """Markdown "PK DÜŞTÜ — SAYI YAYILMAZ" başlığıyla çıkar ve K bölümlerini HİÇ üretmez."""
    s, sonuc = _pk2_kosum(tmp_path, gi.FARK_R_UST * 1.2)
    md = s.markdown_uret(sonuc)
    assert md.startswith("# EDG-2026-088") and "## PK DÜŞTÜ — SAYI YAYILMAZ" in md
    for baslik in ("## K ölçüleri", "## Tanı", "## Eşik karşılaştırması", "## Bedel"):
        assert baslik not in md, f"{baslik} bastırılmış raporda basıldı"
    assert "toplam R" not in md


def test_civi2_PK2_OLCULEMEDIYSE_None_dir_ve_sayilari_BASTIRMAZ(tmp_path):
    """`gecti is None` (defter yok / çift yok) BASTIRMAZ — ölçülmemiş ile düşmüş aynı şey değil."""
    _, sonuc, _ = _kosum(tmp_path, _dolu_pencere())
    assert sonuc["kontrol"]["gecti"] is None
    assert sonuc["kontrol"]["neden"], "PK (2) ölçülemedi ama nedeni yazılmadı"
    assert sonuc["yayin_engeli"] == [] and sonuc["n"] == gi.N_ALT
    assert any("PK (2)" in x for x in sonuc["olculemeyen"]), sonuc["olculemeyen"]


# ---- C: DEFTER BÜTÜNLÜĞÜ (sayaç tarafı) --------------------------------------------------------
def test_C1_sayac_MUKERRER_plan_id_TEKILLESTIRIR_son_satir_kazanir(tmp_path):
    """Çökme sonrası yeniden koşumun yazdığı ikinci satır K'yi ŞİŞİRMEZ; TANIda adıyla durur."""
    satirlar = _dolu_pencere()
    mukerrer = {**satirlar[0], "R": 9.0}
    _, sonuc, _ = _kosum(tmp_path, satirlar + [mukerrer], pencere_gun_once=2)
    assert sonuc["n"] == gi.N_ALT, "mükerrer satır paydayı şişirdi"
    beklenen = sum(r["R"] for r in satirlar) - satirlar[0]["R"] + 9.0
    assert sonuc["toplam_r"] == pytest.approx(beklenen, abs=1e-6), "son satır kazanmadı"
    assert sonuc["girdi"]["n_mukerrer"] == 1
    assert any("mukerrer_n" in x for x in sonuc["olculemeyen"]), sonuc["olculemeyen"]


def test_C5_sayac_KUME_DISI_bar_kaynagini_K_DISINDA_birakir(tmp_path):
    """`BAR_KAYNAKLARI` okuyucu tarafında da zorlanır: küme dışı kaynak K'ye giremez."""
    yad = {**_satir("P-yad", r=1.0), "bar_kaynak": "elle_yazilmis"}
    _, sonuc, _ = _kosum(tmp_path, _dolu_pencere() + [yad], pencere_gun_once=2)
    assert sonuc["n"] == gi.N_ALT, "beyanlı küme dışı kaynaklı satır K paydasına girdi"
    assert any("P-yad" in x and "bar_kaynak_bilinmiyor" in x for x in sonuc["olculemeyen"]), \
        sonuc["olculemeyen"]


# =================================================================================================
# ÇİVİ 3 — PK (3) SELEF (EDG-2026-049): referans + eşleşme, ayrışırsa "HARNESS KÖR"
# =================================================================================================
def _pk3_plan_idler() -> list[str]:
    ham = json.loads(PK3_ARTEFAKT.read_text(encoding="utf-8"))
    return sorted(str(r["plan_id"]) for r in ham if r.get("setup") == "pullback")


def test_civi3_PK3_referans_ARTEFAKTTAN_okunur_6_plan_6_kayip(tmp_path):
    """049'un uyuyan dilimi: TAM 6 satır, 6/6 kayıp, toplam R < 0 — sayı artefaktan TÜRER."""
    _, sonuc, _ = _kosum(tmp_path, _dolu_pencere(), pk3=PK3_ARTEFAKT)
    p = sonuc["pk3"]
    ham = json.loads(PK3_ARTEFAKT.read_text(encoding="utf-8"))
    beklenen = [r for r in ham if r.get("setup") == "pullback"]
    assert p["n"] == len(beklenen) == 6
    assert p["kayip"] == 6
    assert p["toplam_r"] == pytest.approx(sum(r["r_multiple"] for r in beklenen), abs=1e-6)
    assert p["toplam_r"] < 0


def test_civi3_PK3_golge_tarafi_YOKSA_esles_None_ve_HARNESS_KOR(tmp_path):
    """Yeniden doğum koşulmadıysa PK (3) ÖLÇÜLEMEZ — `esles=False` DEĞİL `None`."""
    _, sonuc, _ = _kosum(tmp_path, _dolu_pencere(), pk3=PK3_ARTEFAKT)
    p = sonuc["pk3"]
    assert p["esles"] is None, p
    assert "HARNESS KÖR" in (p["neden"] or ""), p["neden"]
    assert sorted(p["golge"]["eksik_plan_idler"]) == _pk3_plan_idler()
    assert any("PK (3)" in x for x in sonuc["olculemeyen"])


def test_civi3_PK3_golge_ISARETI_TUTARSA_esles_True(tmp_path):
    """Altı planın gölge eşleniği 6/6 kayıpsa işaret TUTAR (eşitlik değil, İŞARET ölçütü)."""
    idler = _pk3_plan_idler()
    golge = [_satir(pid, r=-0.7 - i * 0.1) for i, pid in enumerate(idler)]
    _, sonuc, _ = _kosum(tmp_path, golge + _dolu_pencere(), pk3=PK3_ARTEFAKT)
    p = sonuc["pk3"]
    assert p["golge"]["n"] == 6 and p["golge"]["kayip"] == 6
    assert p["esles"] is True, p
    assert p["fark_r"] is not None


def test_civi3_PK3_ISARET_AYRISIRSA_esles_False(tmp_path):
    """Gölge tarafı kâr yazarsa 049 ile AYRIŞMA vardır — `esles=False` (kartın 'harness kör'ü)."""
    idler = _pk3_plan_idler()
    golge = [_satir(pid, r=+1.0) for pid in idler]
    _, sonuc, _ = _kosum(tmp_path, golge + _dolu_pencere(), pk3=PK3_ARTEFAKT)
    assert sonuc["pk3"]["esles"] is False, sonuc["pk3"]


def test_civi3_PK3_EKSIK_dilim_KISMI_sayilir_uydurulmaz(tmp_path):
    """6'nın 3'ü varsa eşleşme ölçülmez: `esles=None` + eksik kimlikler ADIYLA."""
    idler = _pk3_plan_idler()
    golge = [_satir(pid, r=-1.0) for pid in idler[:3]]
    _, sonuc, _ = _kosum(tmp_path, golge + _dolu_pencere(), pk3=PK3_ARTEFAKT)
    p = sonuc["pk3"]
    assert p["esles"] is None and p["golge"]["n"] == 3
    assert sorted(p["golge"]["eksik_plan_idler"]) == idler[3:]
    assert "KISMİ" in (p["neden"] or ""), p["neden"]


def test_civi3_PK3_artefakt_dilimi_6_DEGILSE_olculemez(tmp_path):
    """Artefakt değişip dilim 6 olmazsa BAŞKA bir şey ölçülmez — PK ölçülemedi damgası."""
    sahte = tmp_path / "sahte_049.json"
    sahte.write_text(json.dumps([{"setup": "pullback", "plan_id": "X", "r_multiple": -1.0}]),
                     encoding="utf-8")
    _, sonuc, _ = _kosum(tmp_path, _dolu_pencere(), pk3=sahte)
    assert sonuc["pk3"]["n"] == 1 and sonuc["pk3"]["esles"] is None
    assert "ÖLÇÜLEMEDİ" in (sonuc["pk3"]["neden"] or "")


# =================================================================================================
# ÇİVİ 4 — PENCERE KAPISI: n<alt sınır ile HİÇBİR EŞİK CÜMLESİ YAZILMAZ
# =================================================================================================
# ---- B: PENCERE SAATİ AÇIK BEYANINDAN (M1-08 / M2-02 / M3-03 / M3-04) --------------------------
def test_B_sayac_pencere_KOKUNU_ACIK_BEYANINDAN_okur(tmp_path):
    """Saat DAĞITIMDAN sayılır: satırlar taze olsa bile pencere 10 gün önce açılmışsa geçen gün 10.

    `--baslangic` verilmediğinde kök defterin YANINDAKİ `golge_icra_acik.json`un beyanıdır; eski
    hâlde kök defterin ilk satırıydı ve saat sistematik olarak geç başlıyordu.
    """
    _, sonuc, _ = _kosum(tmp_path, _dolu_pencere(), pencere_gun_once=10)
    p = sonuc["pencere"]
    assert p["kok_kaynagi"] == "acik.pencere_baslangic", p
    assert p["gecen_gun"] == 10, p
    assert p["doldu"] is True and p["suresi_doldu"] is False


def test_B_BASLANGIC_bayragi_ACIK_ile_CELISIRSE_KAZANIR_ve_rapora_yazilir(tmp_path):
    """İki kaynak çelişirse operatörün bayrağı kazanır — ve çelişki SESSİZ kalmaz."""
    sinir = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=40)).isoformat()
    _, sonuc, _ = _kosum(tmp_path, _dolu_pencere(), pencere_gun_once=10, baslangic=sinir)
    p = sonuc["pencere"]
    assert p["kok_kaynagi"] == "--baslangic" and p["gecen_gun"] == 40, p
    assert p["cakisma"], "çelişki ölçüldü ama rapora yazılmadı"
    assert any("çakış" in x.lower() or "cakis" in x.lower() for x in sonuc["olculemeyen"]), \
        sonuc["olculemeyen"]


def test_B_KOK_YOKSA_pencere_None_ve_NEDEN_adiyla(tmp_path):
    """Ne bayrak ne beyan varsa saat UYDURULMAZ: `gecen_gun` None, `doldu` None + adlı neden."""
    _, sonuc, _ = _kosum(tmp_path, _dolu_pencere())
    p = sonuc["pencere"]
    assert p["kok"] is None and p["gecen_gun"] is None and p["doldu"] is None
    assert any("pencere" in x for x in sonuc["olculemeyen"]), sonuc["olculemeyen"]


def test_B_bedel_satir_gun_PAYI_pencere_ICI_satirdir(tmp_path):
    """M3-04: pay tüm defterdi, payda pencere içiydi — satır/gün şişiyordu."""
    eski = [_satir(f"E-{i}", r=5.0, gun_once=400) for i in range(3)]
    _, sonuc, _ = _kosum(tmp_path, eski + _dolu_pencere(), pencere_gun_once=10)
    assert sonuc["girdi"]["n_pencere_disi"] == 3, sonuc["girdi"]
    assert sonuc["bedel"]["satir_gun"] == pytest.approx(gi.N_ALT / 10.0, abs=1e-4), \
        "pay pencere DIŞI satırları da saymış"
    assert sonuc["bedel"]["n_pencere_satiri"] == gi.N_ALT


def test_civi4_pencere_dolmadan_markdown_HUKUM_YOK_basligi_tasir(tmp_path):
    s, sonuc, _ = _kosum(tmp_path, _dolu_pencere(gi.N_ALT - 1), pencere_gun_once=2)
    assert sonuc["pencere"]["doldu"] is False, sonuc["pencere"]
    md = s.markdown_uret(sonuc)
    assert "## HÜKÜM YOK (betimleyici ara-rapor)" in md
    assert "## Eşik karşılaştırması" not in md, "n<alt sınır iken eşik bölümü basıldı"
    # Betimleyici sayılar YİNE basılır (körlük üretmemek için) — yasak olan EŞİK KARŞILAŞTIRMASI.
    assert "## K ölçüleri" in md and str(sonuc["n"]) in md


def test_civi4_pencere_DOLUNCA_esik_bolumu_dogar_ve_HUKUM_KELIMESI_yoktur(tmp_path):
    s, sonuc, _ = _kosum(tmp_path, _dolu_pencere(), pencere_gun_once=2)
    assert sonuc["pencere"]["doldu"] is True, sonuc["pencere"]
    md = s.markdown_uret(sonuc)
    assert "## Eşik karşılaştırması" in md and "## HÜKÜM YOK" not in md
    # SAYAÇ HÜKÜM VERMEZ: geçti/kaldı sözcükleri hiçbir çıktıda YOKTUR.
    for kelime in ("GEÇER", "KALIR", "geçti", "kaldı", "GEÇTİ", "KALDI"):
        assert kelime not in md, f"sayaç hüküm cümlesi yazdı: {kelime}"


def test_civi4_pencere_SURESI_dolunca_doldu_False_kalir(tmp_path):
    """n yeterli ama geçen gün üst sınırı AŞTIYSA pencere dolmuş SAYILMAZ (kart eşiği donuk)."""
    eski = [_satir(f"P-{i:03d}", r=1.0, gun_once=gi.PENCERE_GUN + 5) for i in range(gi.N_ALT)]
    _, sonuc, _ = _kosum(tmp_path, eski, pencere_gun_once=gi.PENCERE_GUN + 5)
    assert sonuc["pencere"]["gecen_gun"] > gi.PENCERE_GUN
    assert sonuc["pencere"]["doldu"] is False and sonuc["pencere"]["suresi_doldu"] is True


# =================================================================================================
# ÇİVİ 5 — PIT ÇAPASI: hash'siz satır K paydasına GİRMEZ, `olculemeyen`e ADIYLA düşer
# =================================================================================================
def test_civi5_hashsiz_satir_paydaya_girmez_ve_ADIYLA_gorunur(tmp_path):
    saglam = _dolu_pencere()
    capasiz = _satir("P-capasiz", r=99.0, hash_=None)
    capasiz["olculemedi"] = "bar_eksik:2"
    _, sonuc, _ = _kosum(tmp_path, saglam + [capasiz])
    assert sonuc["n"] == gi.N_ALT, "PIT çapası yarım satır paydaya girdi"
    assert sonuc["toplam_r"] == pytest.approx(sum(r["R"] for r in saglam), abs=1e-6)
    assert any("P-capasiz" in x and "bar_eksik:2" in x for x in sonuc["olculemeyen"]), \
        sonuc["olculemeyen"]


def test_civi5_bos_hash_dizgesi_de_capa_SAYILMAZ(tmp_path):
    """Boş dizge bir çapa DEĞİLDİR — `""` ile `None` aynı hükmü alır."""
    _, sonuc, _ = _kosum(tmp_path, _dolu_pencere() + [_satir("P-bos", r=99.0, hash_="")])
    assert sonuc["n"] == gi.N_ALT and any("P-bos" in x for x in sonuc["olculemeyen"])


# =================================================================================================
# ÇİVİ 6 — BOOTSTRAP DONUK: tohum/B/blok ADIYLA çıktıda; IID REDDEDİLİR
# =================================================================================================
def test_civi6_bootstrap_tohum_B_blok_ciktida_ADIYLA_yazilidir(tmp_path):
    from meridian.olcum_araclari import BOOTSTRAP_N, BOOTSTRAP_TOHUM
    _, sonuc, _ = _kosum(tmp_path, _dolu_pencere())
    ci = sonuc["ci"]
    assert ci["tohum"] == BOOTSTRAP_TOHUM and ci["B"] == BOOTSTRAP_N
    assert ci["blok"] >= 2 and ci["blok_kaynagi"] == "n^(1/3) kuralı"
    assert "moving" in ci["yontem"] and str(ci["tohum"]) in ci["yontem"]
    assert sonuc["ci_kabul"] is True and ci["iid"] is False


def test_civi6_IID_bootstrap_REDDEDILIR(tmp_path):
    """n çok küçükken blok 1'e düşer: aralık IID'dir ve kartın donuk yöntemini SINAMAZ."""
    _, sonuc, _ = _kosum(tmp_path, _dolu_pencere(3))
    assert sonuc["ci"]["blok"] == 1 and sonuc["ci"]["iid"] is True
    assert sonuc["ci_kabul"] is False
    assert any("IID" in x and "REDDEDİLDİ" in x for x in sonuc["olculemeyen"]), \
        sonuc["olculemeyen"]


def test_civi6_CI_ayni_defterde_AYNI_araligi_verir_tekrarlanabilir(tmp_path):
    _, a, _ = _kosum(tmp_path / "a", _dolu_pencere())
    _, b, _ = _kosum(tmp_path / "b", _dolu_pencere())
    assert (a["ci"]["lo"], a["ci"]["hi"]) == (b["ci"]["lo"], b["ci"]["hi"])


def test_civi6_ci_toplam_bir_TURETMEDIR_ve_oyle_ADLANDIRILIR(tmp_path):
    _, sonuc, _ = _kosum(tmp_path, _dolu_pencere())
    t = sonuc["ci_toplam"]
    assert t["lo"] == pytest.approx(sonuc["ci"]["lo"] * sonuc["n"], abs=1e-6)
    assert "TÜRETİLMİŞ" in t["turetme"] and "ÖLÇÜLMEMİŞTİR" in t["turetme"]


def test_civi6_kartin_ci_yontemi_KULLANILAN_fonksiyonu_ADIYLA_soyler():
    """Kartın donuk `ci_yontem` alanı gerçekten çağrılan fonksiyonun adını taşımalı."""
    yontem = str(_kart()["esikler"]["ci_yontem"])
    assert "blok_bootstrap_ci" in yontem and "olcum_araclari" in yontem, yontem


# =================================================================================================
# EŞİK KAYNAĞI — kart ↔ motor sabitleri; kopya YOK, AYRIŞMA ölçülür
# =================================================================================================
def test_esikler_KART_ve_MOTOR_sabitlerinden_okunur_ayrisma_YOK(tmp_path):
    _, sonuc, _ = _kosum(tmp_path, _dolu_pencere())
    kart_esik = _kart()["esikler"]
    assert sonuc["esik_ayrismasi"] == [], sonuc["esik_ayrismasi"]
    assert sonuc["modul_sabitleri"]["N_ALT"] == gi.N_ALT == kart_esik["n_alt_plan"]
    assert sonuc["modul_sabitleri"]["PENCERE_GUN"] == gi.PENCERE_GUN \
        == kart_esik["pencere_gun_ust"]
    assert sonuc["esikler"] == kart_esik, "kart eşik bloğu olduğu gibi taşınmadı"


def test_kart_MOTORDAN_ayrisirsa_yayin_ENGELLENIR(tmp_path):
    """Sahte kartta eşik oynatılınca ayrışma ölçülür ve K bloğu BASTIRILIR (tek-kaynak yasası)."""
    kart = _kart()
    kart["esikler"]["kazanma_alt"] = float(gi.KAZANMA_ALT) + 0.1
    sahte = tmp_path / "sahte_kart.yaml"
    sahte.write_text(yaml.safe_dump(kart, allow_unicode=True), encoding="utf-8")
    _, sonuc, _ = _kosum(tmp_path, _dolu_pencere(), kart=sahte)
    assert any("kazanma_alt" in x for x in sonuc["esik_ayrismasi"]), sonuc["esik_ayrismasi"]
    assert sonuc["n"] is None and any("ayrışması" in x for x in sonuc["yayin_engeli"])


# NOT: "eşik sayısı gövdede literal yazılı değil" çivisinin ESKİ hâli (alt-dizge araması, dört
# sabit) burada duruyordu ve İKİ kusuru vardı (inceleme M4-16): `30` herhangi bir sayının içinde
# yanlış alarm verebiliyordu ve `CI_ALT_R` denetim DIŞINDAYDI. Yerini
# `test_E5_esik_LITERALI_denetimi_SOZCUK_SINIRLI_ve_CI_ALT_R_dahil` aldı (sözcük sınırlı regex,
# beş sabitin tamamı, deseni kendi pozitif kontrolüyle). İKİ ÇİVİ BIRAKILMADI: aynı gerçeğin iki
# denetimi, zayıf olanın yeşilliğine güven üretirdi.


# =================================================================================================
# ÇİVİ 7 — KOMUT SATIRI (ops sözleşmesi KOMUT SATIRIdır) + SALT OKUNURLUK
# =================================================================================================
def test_civi7_komut_satiri_operatorun_kosacagi_BICIMDE_kosar_ve_state_e_YAZMAZ(tmp_path):
    defter = _defter_yaz(tmp_path / "girdi" / "golge_icra.jsonl", _dolu_pencere())
    # PENCERE BEYANI DEFTERİN YANINDADIR: operatör `--baslangic` yazmadan koşar ve saat yine
    # dağıtımdan sayılır (`--acik` varsayılanı defter yolundan TÜRETİLİR).
    _acik_yaz(defter.parent, 2)
    onceki = defter.read_bytes()
    cikti, md = tmp_path / "out" / "sonuc.json", tmp_path / "out" / "sonuc.md"
    ortam = dict(os.environ, MERIDIAN_ROOT=str(tmp_path), PYTHONPATH=str(KOK))
    r = subprocess.run([sys.executable, str(BETIK_YOLU), "--defter", str(defter),
                        "--cikti", str(cikti), "--markdown", str(md),
                        "--kart", str(KART_YOLU), "--goal", str(GOAL_YOLU),
                        "--pk3", str(PK3_ARTEFAKT)],
                       capture_output=True, text=True, cwd=str(tmp_path), env=ortam)
    assert r.returncode == 0, (r.returncode, r.stdout, r.stderr)
    sonuc = json.loads(cikti.read_text(encoding="utf-8"))
    assert sonuc["n"] == gi.N_ALT and sonuc["kart"] == gi.KART
    assert md.exists() and "## Eşik karşılaştırması" in md.read_text(encoding="utf-8")
    assert defter.read_bytes() == onceki, "sayaç girdi defterini değiştirdi"
    assert not (tmp_path / "state").exists(), "sayaç state/ altına yazdı"
    # OPERATÖR PENCEREYİ VE PK DURUMUNU TERMİNALDE GÖRMELİ (sessiz sıfır rapor sınıfı).
    for parca in ("pencere_doldu=", "pencere_disi=", "pk2=", "pk3=", "yayin_engeli="):
        assert parca in r.stdout, r.stdout


def test_ithal_meridian_obs_u_TETIKLEMEZ_ve_state_ACMAZ(tmp_path):
    """Brief'in ölçüm kalemi: sabitleri ithal etmek canlı deftere yazan modülü YÜKLEMİYOR mu?"""
    ortam = dict(os.environ, MERIDIAN_ROOT=str(tmp_path), PYTHONPATH=str(KOK))
    kod = ("import sys, json, importlib.util;"
           f"spec=importlib.util.spec_from_file_location('s', r'{BETIK_YOLU}');"
           "m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m);"
           "print(json.dumps({'obs': 'meridian.obs' in sys.modules,"
           " 'loop': 'meridian.loop' in sys.modules,"
           " 'alpaca': 'meridian.adapters.alpaca' in sys.modules}))")
    r = subprocess.run([sys.executable, "-c", kod], capture_output=True, text=True,
                       cwd=str(tmp_path), env=ortam)
    assert r.returncode == 0, (r.stdout, r.stderr)
    olculen = json.loads(r.stdout.strip().splitlines()[-1])
    assert olculen == {"obs": False, "loop": False, "alpaca": False}, olculen
    assert not (tmp_path / "state").exists(), "ithal `state/` açtı"


def test_defter_verilmezse_hata(tmp_path):
    ortam = dict(os.environ, MERIDIAN_ROOT=str(tmp_path), PYTHONPATH=str(KOK))
    r = subprocess.run([sys.executable, str(BETIK_YOLU), "--cikti", str(tmp_path / "o.json")],
                       capture_output=True, text=True, cwd=str(tmp_path), env=ortam)
    assert r.returncode != 0
    assert "--defter" in (r.stderr or ""), r.stderr


def test_olmayan_defter_yolu_HATA_verir_bos_rapor_URETMEZ(tmp_path):
    s = _sayim()
    with pytest.raises(FileNotFoundError):
        s.calistir(defter=tmp_path / "yok.jsonl", kart=KART_YOLU, goal=GOAL_YOLU)


def test_bozuk_baslangic_DURDURUR_sessizce_bosaltmaz(tmp_path):
    s = _sayim()
    defter = _defter_yaz(tmp_path / "d.jsonl", _dolu_pencere())
    with pytest.raises(SystemExit):
        s.calistir(defter=defter, kart=KART_YOLU, goal=GOAL_YOLU, baslangic="dun")


# =================================================================================================
# PENCERE SÜZGECİ + BOZUK GİRDİ
# =================================================================================================
def test_baslangic_penceresi_ESKI_satirlari_disarida_birakir(tmp_path):
    taze = _dolu_pencere()
    eski = [_satir(f"E-{i}", r=5.0, gun_once=400) for i in range(3)]
    sinir = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=30)).isoformat()
    _, sonuc, _ = _kosum(tmp_path, eski + taze, baslangic=sinir)
    assert sonuc["girdi"]["n_pencere_disi"] == 3
    assert sonuc["n"] == gi.N_ALT and sonuc["toplam_r"] == pytest.approx(
        sum(r["R"] for r in taze), abs=1e-6)


def test_AYNI_ANI_gosteren_iki_damga_bicimi_AYNI_pencereyi_verir(tmp_path):
    an = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=30)
    _, a, _ = _kosum(tmp_path / "a", _dolu_pencere(), baslangic=an.isoformat())
    _, b, _ = _kosum(tmp_path / "b", _dolu_pencere(),
                     baslangic=an.isoformat().replace("+00:00", "Z"))
    assert a["girdi"]["n_pencere_disi"] == b["girdi"]["n_pencere_disi"] and a["n"] == b["n"]


def test_bozuk_satir_SAYILIR_ve_sayimi_dusurmez(tmp_path):
    defter = tmp_path / "state" / "golge_icra.jsonl"
    _defter_yaz(defter, _dolu_pencere())
    with defter.open("a", encoding="utf-8") as f:
        f.write("{bu json degil\n[1,2,3]\n")
    s = _sayim()
    sonuc = s.calistir(defter=defter, kart=KART_YOLU, goal=GOAL_YOLU)
    assert sonuc["girdi"]["n_bozuk_satir"] == 2 and sonuc["n"] == gi.N_ALT
    assert any("bozuk_satir" in x for x in sonuc["olculemeyen"])


def test_bos_defterde_sayilar_None_ve_NEDEN_sifir_DEGIL(tmp_path):
    """Kanıt yokken 'her şey yolunda' gösterilmez: toplam R 0 değil None."""
    _, sonuc, _ = _kosum(tmp_path, [])
    assert sonuc["n"] == 0 and sonuc["toplam_r"] is None and sonuc["kazanma_orani"] is None
    assert sonuc["pencere"]["doldu"] is None and sonuc["pencere"]["gecen_gun"] is None
    assert sonuc["ci"]["lo"] is None and sonuc["ci"]["neden"]
    assert any("pencere" in x for x in sonuc["olculemeyen"])


def test_bedel_satir_gun_ve_bayt_raporlanir(tmp_path):
    _, sonuc, defter = _kosum(tmp_path, _dolu_pencere(), pencere_gun_once=2)
    assert sonuc["bedel"]["bayt"] == defter.stat().st_size
    assert sonuc["bedel"]["n_ham_satir"] == gi.N_ALT
