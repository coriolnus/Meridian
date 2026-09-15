"""v503 · Durum sözlüğü TÜM ailelere (TSK-070 A8, tasarım §9.1).

ÖLÇÜM TABANI: `docs/TASARIM-F8-DURUM-SOZLUGU-2026-08-22.md` §4b + §9 (2026-09-15 eki). Kelime
kümesi çivisi belgeyi DOSYADAN okur — tek-kaynak yasası: kanonik kelime ya belgede ya kodda
değil, İKİSİNDE BİRDEN aynı olmalıdır ve ayrışma burada kırmızıya döner.

ÇAPA NOTU: bu dosya hiçbir `dosya.py:NNN` satır çapası taşımaz (satır kayar, çivi sessizce
yanlış yeri gösterir); atıflar `modül.sembol` biçimindedir.
"""
import pathlib
import re

from meridian import durum_sozlugu as D

ROOT = pathlib.Path(__file__).resolve().parents[1]
TASARIM = ROOT / "docs/TASARIM-F8-DURUM-SOZLUGU-2026-08-22.md"

# §4b + §9.1 tablolarındaki kanonik kelimelerin ADAY kümesi. Sınır koşulu `\b` DEĞİL
# lookaround'dur ve bu bilinçlidir: `\b` bir ")" ile boşluk arasında SINIR GÖRMEZ, dolayısıyla
# "DURDU (orphan)" gibi parantezle biten kelimeleri sessizce düşürürdü — çivi o iki kelimeyi hiç
# ölçmeden yeşil kalırdı (plan taslağındaki desenin ölçülmüş kusuru).
_ADAYLAR = ("PENCEREDE|GECİKTİ|HİÇ KOŞMADI|ASKIDA|BASTIRILDI|TEMİZ|İHLAL|ÖLÇÜLEMEDİ|"
            r"KAPSAM DIŞI|DEDEKTÖR DÜŞTÜ|KOŞUYOR|DURDU \((?:orphan|stall)\)|DEĞİŞİM YOK|"
            "DAMGALI DEĞİŞİM|İÇERİK-AYNI YENİDEN YAZIM|DAMGASIZ YAZIM|İLK GÖZLEM|KAPALI|ÇEKİLİ|"
            "İLK ALARM|MANDALLI|YENİDEN|DÜŞTÜ|SEANS DIŞI|PENCERE ÖNCESİ|HALT|BAYAT|BAR YOK")


def _belge_kelimeleri() -> set:
    """Tasarım belgesindeki büyük-harfli kanonik kelimeler (tek kaynak = belge)."""
    m = TASARIM.read_text(encoding="utf-8")
    return set(re.findall(rf"(?<!\w)({_ADAYLAR})(?!\w)", m))


# =============================================================================================
# A — KELİME KÜMESİ TEK KAYNAKTAN
# =============================================================================================

def test_a_pano_kelime_kumesi_belgeyle_birebir():
    belge = _belge_kelimeleri()
    assert belge, "belge taranamadı — çivi ölçemedi (yol ya da başlık değişti mi?)"
    assert set(D.PANO_KELIME.values()) == belge, (
        "PANO_KELIME ile tasarım §4b/§9.1 AYRIŞTI — "
        f"kodda fazla: {sorted(set(D.PANO_KELIME.values()) - belge)} · "
        f"belgede fazla: {sorted(belge - set(D.PANO_KELIME.values()))}")


def test_a2_bosta_kelimesi_UYDURULMAZ():
    """§9.1 hükmü: "BOŞTA" üretici ölçmüyor → sözlükte de YOKTUR (uydurma yasağı)."""
    assert "BOŞTA" not in set(D.PANO_KELIME.values())


# =============================================================================================
# B — KADANS (17 mekanizma, EXPECTED ile birebir)
# =============================================================================================

def test_b_kadans_17_satir_expected_ile_birebir():
    from meridian import watchdog as W
    rapor = {"stale": ["cf_advance"], "never": ["y4_collect"], "askida": ["shadow_fit"],
             "ok": None, "n_ok": 14, "total": 17}
    s = D.kadans_satirlari(rapor, W.EXPECTED)
    assert len(s) == 17 and {x["kimlik"] for x in s} == set(W.EXPECTED)
    k = {x["kimlik"]: x for x in s}
    assert k["cf_advance"]["kelime"] == "GECİKTİ" and k["cf_advance"]["ok"] is False
    assert k["y4_collect"]["kelime"] == "HİÇ KOŞMADI" and k["y4_collect"]["ok"] is False
    assert k["shadow_fit"]["kelime"] == "ASKIDA" and k["shadow_fit"]["ok"] is None
    assert k["shadow_fit"]["askida"] is True
    assert k["scheduler_poll"]["kelime"] == "PENCEREDE" and k["scheduler_poll"]["ok"] is True
    assert all(x["aile"] == "kadans" for x in s)


def test_b2_kadans_canli_sekil_de_okunur():
    """`watchdog.report()` stale/askida listelerini SÖZLÜK olarak döndürür (`{name, gap_h…}`);
    adaptör düz ad ve sözlük şekillerinin İKİSİNİ de okur — yoksa canlı yük sessizce 17/17
    PENCEREDE görünürdü (sahte yeşil)."""
    from meridian import watchdog as W
    rapor = {"stale": [{"name": "cf_advance", "gap_h": 120.0, "expected_h": 96.0}],
             "never": ["y4_collect"], "askida": [], "ok": False, "n_ok": 15, "total": 17}
    k = {x["kimlik"]: x for x in D.kadans_satirlari(rapor, W.EXPECTED)}
    assert k["cf_advance"]["kelime"] == "GECİKTİ" and k["cf_advance"]["ok"] is False
    assert "120.0" in k["cf_advance"]["beyan"], "gecikme beyanı satıra taşınmadı"


def test_b3_bastirilan_alarm_gorunur_kalir():
    """Bastırılan alarm SAYILIR ve GÖRÜNÜR (alarm hijyeni): geciken mekanizmanın günlük tavana
    takılmış alarmı BASTIRILDI kelimesini taşır, sayısı `n`de durur, hüküm hâlâ ihlaldir."""
    from meridian import watchdog as W
    rapor = {"stale": ["cf_advance"], "never": [], "askida": [], "n_ok": 16, "total": 17}
    k = {x["kimlik"]: x for x in
         D.kadans_satirlari(rapor, W.EXPECTED, {"cf_advance": 4, "scheduler_poll": 0})}
    assert k["cf_advance"]["kelime"] == "BASTIRILDI" and k["cf_advance"]["ok"] is False
    assert k["cf_advance"]["n"] == 4 and k["cf_advance"]["neden"] == "stale"
    # bastırılmamış/penceresindeki mekanizma kelimesini DEĞİŞTİRMEZ
    assert k["scheduler_poll"]["kelime"] == "PENCEREDE"


# =============================================================================================
# C — KİLİTLER (ters işaret + kademesiz devre kesici)
# =============================================================================================

def test_c_kilit_ters_isaret_ve_devre_kesici_kademesiz():
    s = {x["kimlik"]: x
         for x in D.kilit_satirlari({"halted": False, "learn_halted": True},
                                    {"breaker_tripped": None})}
    assert set(s) == {"soft_halt", "halt_learning", "devre_kesici"}
    assert s["soft_halt"]["kelime"] == "KAPALI" and s["soft_halt"]["ok"] is True
    assert s["halt_learning"]["kelime"] == "ÇEKİLİ" and s["halt_learning"]["ok"] is False
    assert "Kademe 4" in s["halt_learning"]["beyan"]
    assert s["devre_kesici"]["kelime"] == "ÖLÇÜLEMEDİ" and s["devre_kesici"]["ok"] is None
    assert s["devre_kesici"]["olculemedi"] is True
    assert "Kademe" not in s["devre_kesici"]["beyan"], "kademe numarası UYDURULDU"
    assert all(x["aile"] == "kilit" for x in s.values())


# =============================================================================================
# D — CANLILIK ("BOŞTA" üretilmez · orphan/stall ayrı kelime)
# =============================================================================================

def test_d_canlilik_bosta_uretilmez_ve_orphan_stall():
    s = {x["kimlik"]: x for x in D.canlilik_satirlari(
        {"sprint": {"ok": False, "beyan": "x"}, "learning": {"ok": True, "beyan": "y"}})}
    assert s["sprint"]["kelime"] == "DURDU (orphan)" and s["sprint"]["ok"] is False
    assert s["learning"]["kelime"] == "KOŞUYOR" and s["learning"]["ok"] is True
    assert "BOŞTA" not in {x["kelime"] for x in s.values()}
    # öğrenme bacağı durduğunda AYRI kelime (orphan ile aynı sayfaya yazılmaz)
    d = {x["kimlik"]: x for x in D.canlilik_satirlari({"learning": {"ok": False}})}
    assert d["learning"]["kelime"] == "DURDU (stall)"


def test_d2_olculmeyen_bacak_SATIR_URETMEZ():
    """Üretici bir bacağı hiç ölçmediyse satır YOKTUR — "BOŞTA" da "ÖLÇÜLEMEDİ" de uydurulmaz."""
    s = D.canlilik_satirlari({"sprint": {"ok": True}})
    assert [x["kimlik"] for x in s] == ["sprint"]
    assert D.canlilik_satirlari({}) == [] and D.canlilik_satirlari(None) == []


# =============================================================================================
# E — INTRADAY ATLAMALARI (null ≠ 0)
# =============================================================================================

def test_e_intraday_null_olculemedi_sifir_degil():
    s = {x["kimlik"]: x for x in D.intraday_satirlari({"session": 3, "pencere": None})}
    assert s["session"]["kelime"] == "SEANS DIŞI" and s["session"]["n"] == 3
    assert s["pencere"]["kelime"] == "ÖLÇÜLEMEDİ" and s["pencere"]["n"] is None
    assert s["pencere"]["olculemedi"] is True
    assert len(s) == 5, "atlama ailesi §9.1'de BEŞ anahtardır (eksik anahtar 0 basmaz)"
    assert all(x["aile"] == "intraday" for x in s.values())


def test_e2_sifir_sayac_OLCULDU_sayilir():
    """0 ile None AYRI: ölçülmüş sıfır atlamanın kelimesi vardır, ölçülmemiş olanın YOKTUR."""
    s = {x["kimlik"]: x for x in D.intraday_satirlari({"halt": 0})}
    assert s["halt"]["n"] == 0 and s["halt"]["kelime"] == "HALT"
    assert s["halt"]["olculemedi"] is False and s["stale"]["olculemedi"] is True


# =============================================================================================
# F — MANDAL YÜZEYİ (Yasa-6 boşluğu: yüzey ÖNCE açılır)
# =============================================================================================

def test_f_mandal_yuzeyi_dosyadan_ve_yoksa_olculemedi(sandbox_state):
    m = D.mandal_yuzeyi()            # store.read_json ile; sandbox'ta defter yok
    assert m["alarm_mandal"] is None and m["watchdog_alarmed"] is None
    assert m["integrity_alarmed"] is None
    s = D.mandal_satirlari(m)
    assert s and all(x["kelime"] == "ÖLÇÜLEMEDİ" and x["ok"] is None for x in s)
    assert all(x["aile"] == "mandal" and x["olculemedi"] is True for x in s)


def test_f2_mandal_defteri_dolunca_kelime_defterden_turer(sandbox_state):
    from meridian import store
    store.write_json("alarm_mandal.json",
                     {"MIRROR_DRIFT|a": {"token": "MIRROR_DRIFT", "n": 3, "bastirilan": 2,
                                         "yeniden": False}})
    store.write_json("watchdog_alarmed.json", [])
    store.write_json("integrity_alarmed.json", ["parity:artifact_unread"])
    m = D.mandal_yuzeyi()
    assert m["alarm_mandal"]["n"] == 1 and m["alarm_mandal"]["jetonlar"] == ["MIRROR_DRIFT"]
    s = {x["kimlik"]: x for x in D.mandal_satirlari(m)}
    assert s["alarm_mandal"]["kelime"] == "MANDALLI" and s["alarm_mandal"]["n"] == 1
    assert s["watchdog_alarmed"]["kelime"] == "DÜŞTÜ" and s["watchdog_alarmed"]["n"] == 0
    assert s["integrity_alarmed"]["kelime"] == "MANDALLI"
    # ENVANTER, ALARM DEĞİL: mandal satırı kırmızıya dönmez (bkz. watchdog'un kendi
    # `alarm_mandal` satırı — mandallı durum İLK görüşte zaten alarmlandı).
    assert all(x["ok"] is True for x in s.values() if x["kimlik"] != "koruma_alarmed")
    assert s["koruma_alarmed"]["kelime"] == "ÖLÇÜLEMEDİ", "süreç-içi mandal ölçülmüş gibi basıldı"
    # ALAN ADI SÖZLEŞMESİ: `neden` her defterin KENDİ beyan edilmiş alanından gelir — alarm
    # mandalı `jetonlar`dan, ad listesi defterleri `adlar`dan. Takas yok (bkz. test_f4).
    assert s["alarm_mandal"]["neden"] == "MIRROR_DRIFT"
    assert s["integrity_alarmed"]["neden"] == "parity:artifact_unread"
    assert s["watchdog_alarmed"]["neden"] is None, "boş defterde olmayan ad basıldı"


def test_f3_ilk_alarm_ve_yeniden_ayri_kelimelerdir(sandbox_state):
    from meridian import store
    store.write_json("alarm_mandal.json", {"X|a": {"token": "X", "n": 1, "yeniden": False}})
    s = {x["kimlik"]: x for x in D.mandal_satirlari(D.mandal_yuzeyi())}
    assert s["alarm_mandal"]["kelime"] == "İLK ALARM"
    store.write_json("alarm_mandal.json", {"X|a": {"token": "X", "n": 5, "yeniden": True}})
    s = {x["kimlik"]: x for x in D.mandal_satirlari(D.mandal_yuzeyi())}
    assert s["alarm_mandal"]["kelime"] == "YENİDEN"


def test_f4_neden_yalniz_beyan_edilen_alandan_okunur(sandbox_state):
    """ALAN ADI SÖZLEŞMESİ — v56 şema-takası dersi (2026-09-15, suite #58).

    İki defter sınıfı İKİ AYRI şekil üretir: `alarm_mandal` imza sözlüğünden JETON kümesi
    (`jetonlar`), ötekiler düpedüz AD listesi (`adlar`). Hangi defterin hangi alanı taşıdığı
    `durum_sozlugu._MANDAL_OGE_ALANI`da TEK KAYNAKtır ve satır üreticisi YALNIZ onu okur.
    Eskiden iki ad birbirine `or` ile yedekleniyordu; o ifade yanlış şekli SESSİZ geçirirdi ve
    v56 dedektörü onu beyan edilmemiş şema takası olarak ötüyordu. Yanlış şekilde doğru hüküm:
    sayı (`n`) ÖLÇÜLMÜŞTÜR ama öğe adları ÖLÇÜLMEMİŞTİR → `neden` None (uydurma yasağı)."""
    assert D._MANDAL_OGE_ALANI["alarm_mandal"] == "jetonlar"
    assert D._MANDAL_OGE_ALANI["watchdog_alarmed"] == "adlar"
    assert D._MANDAL_OGE_ALANI["integrity_alarmed"] == "adlar"
    # Beyan tablosu defter listesiyle AYRIŞMAZ: yeni defter alanını beyan etmeden eklenemez.
    assert set(D._MANDAL_OGE_ALANI) == set(D.MANDAL_DEFTERLERI)
    # Defterler KARŞI şekli taşırsa öğe adı okunmaz — takas olsaydı ikisi de dolu basardı.
    y = {"watchdog_alarmed": {"n": 2, "jetonlar": ["A", "B"]},
         "alarm_mandal": {"n": 1, "ilk_n": 1, "adlar": ["C"]}}
    s = {x["kimlik"]: x for x in D.mandal_satirlari(y)}
    assert s["watchdog_alarmed"]["n"] == 2 and s["watchdog_alarmed"]["neden"] is None
    assert s["alarm_mandal"]["n"] == 1 and s["alarm_mandal"]["neden"] is None


def test_f5_jetonsuz_imza_satiri_atlanir(sandbox_state):
    """İmza satırı `token` taşımıyorsa JETON ÜRETİLMEZ: `n` imzaları sayar, `jetonlar` yalnız
    gerçekten okunan jetonları taşır — eksik alan "None" diye basılmaz (uydurma yasağı)."""
    from meridian import store
    store.write_json("alarm_mandal.json", {"A|a": {"token": "REAL", "n": 2},
                                           "B|b": {"n": 2}})          # token ALANI YOK
    m = D.mandal_yuzeyi()
    assert m["alarm_mandal"]["n"] == 2, "imza sayımı jeton eksikliğinden etkilenmemeli"
    assert m["alarm_mandal"]["jetonlar"] == ["REAL"]
    s = {x["kimlik"]: x for x in D.mandal_satirlari(m)}
    assert s["alarm_mandal"]["neden"] == "REAL"


# =============================================================================================
# G — HERMES ISINMA (skip kodu `neden` ailesine, kol adına DEĞİL)
# =============================================================================================

def test_g_hermes_isinma_skip_neden_ailesinde():
    s = D.hermes_satiri({"last_result": "halt_learning", "skip": "lock_busy"})
    assert s["kelime"] == "ASKIDA" and s["neden"] == "isinma:lock_busy" and s["ok"] is None
    assert s["askida"] is True and s["aile"] == "hermes"
    assert D.hermes_satiri({"last_result": "error: RuntimeError", "skip": None})["kelime"] == "İHLAL"
    assert D.hermes_satiri({"last_result": "accepted", "skip": None})["kelime"] == "KOŞUYOR"
    assert D.hermes_satiri({})["kelime"] == "ÖLÇÜLEMEDİ"


# =============================================================================================
# H — SERVİS YÜZEYİ: dokuz aile tek sözlükte
# =============================================================================================

def _sahte_teshis():
    """`/api/diagnostics` gövdesinin `_durum_sozlugu`nun okuduğu DİLİMİ (sahte, sabit)."""
    return {
        "integrity": {ad: {"ok": True} for ad in
                      ("production", "conservation", "determinism", "coherence",
                       "monotonicity", "ownership", "parity", "divergence")},
        "liveness": {"sprint": {"ok": True}, "learning": {"ok": None, "olculemedi": True}},
        "watchdog": {"stale": [], "never": [], "askida": [], "ok": True,
                     "n_ok": 17, "total": 17},
        "alarm_gunluk": {"mekanizmalar": {}},
        "hud": {"halted": False, "learn_halted": False},
        "heartbeat": {"breaker_tripped": False},
        "mlops": {"warmup": {"last_result": "accepted", "skip": None}},
        "intraday": {"skipped": {"session": 1, "pencere": 0, "halt": 0, "stale": 0, "no_bars": 2}},
        "mandallar": {"alarm_mandal": None, "watchdog_alarmed": None,
                      "integrity_alarmed": None, "koruma_alarmed": None},
    }


def _sahte_bd():
    return {"goal_failure": {"ok": True, "beyan": "hedef ihlali yok"},
            "kitap_damga": {"ok": True, "rows": [{"ad": "portfolio.json", "sinif": "degisim_yok",
                                                  "neden": "içerik ve damga aynı"}]},
            "mutabakat_tazelik": {"ok": None, "olculemedi": True, "neden": "kayıt yok"},
            "onayli_gonderim": {"ok": True}}


def test_h_api_durum_sozlugu_tum_aileleri_tasir(sandbox_state):
    from meridian import api
    dz = api._durum_sozlugu(_sahte_bd(), _sahte_teshis())
    assert dz["aileler"] == {"bekci": 4, "dedektor": 8, "canlilik": 2, "kadans": 17,
                             "kitap": 1, "kilit": 3, "mandal": 4, "hermes": 1, "intraday": 5}
    satirlar = dz["satirlar"]
    assert len(satirlar) == sum(dz["aileler"].values()) == 45
    kelimeler = set(D.PANO_KELIME.values())
    for s in satirlar:
        assert set(s) >= {"aile", "kimlik", "kelime", "ok", "olculemedi", "kapsam_disi",
                          "askida", "neden", "beyan", "kaynak_alan", "n"}, s["kimlik"]
        assert s["kelime"] in kelimeler, f"kanonik olmayan kelime: {s['kimlik']}={s['kelime']}"
    # mevcut sözleşme alanları AYNEN (v271/v499 okuyucuları kırılmaz)
    for alan in ("kanonik", "esanlamli_okumalar", "pencere", "sayac_rejimi", "beyan"):
        assert alan in dz, f"{alan} alanı DÜŞTÜ"


def test_h2_teshis_verilmezse_ESKI_DAVRANIS(sandbox_state):
    """`teshis` yoksa uç yalnız dört bekçi satırını taşır — v261/v271 okuyucuları dokunulmadan
    yeşil kalır (imza genişledi, sözleşme daralmadı)."""
    from meridian import api
    dz = api._durum_sozlugu(_sahte_bd())
    assert {s["kimlik"] for s in dz["satirlar"]} == set(_sahte_bd())
    assert dz["aileler"] == {"bekci": 4}


def test_h3_uydurma_yasagi_olculemeyen_govde_satir_uretmez(sandbox_state):
    """Teşhis gövdesi boşsa: sayı UYDURULMAZ (n None), hüküm UYDURULMAZ (ok None), ölçülmeyen
    canlılık/bekçi/dedektör aileleri SATIR AÇMAZ — ve bekçi raporu gelmeyen 17 kadans
    mekanizması "PENCEREDE" diye YEŞİLE BOYANMAZ (sahte yeşilin ta kendisi olurdu)."""
    from meridian import api
    dz = api._durum_sozlugu({}, {"mandallar": {}})
    assert dz["aileler"] == {"kadans": 17, "kilit": 3, "mandal": 4, "hermes": 1, "intraday": 5}
    for s in dz["satirlar"]:
        assert s["kelime"] == "ÖLÇÜLEMEDİ", f"{s['aile']}/{s['kimlik']} hüküm UYDURDU"
        assert s["ok"] is None and s["n"] is None and s["olculemedi"] is True


def test_h4_canli_uc_dokuz_aileyi_TASIR(sandbox_state):
    """KABLOLAMA KANITI: sahte gövde `_durum_sozlugu`nun İÇİNİ ölçer, bu test /api/diagnostics'in
    o gövdeyi gerçekten BESLEDİĞİNİ ölçer. İkisi ayrı sorudur — uç yanlış dilimi geçirseydi
    (örn. `hud` yerine boş sözlük) yukarıdaki testlerin hepsi yeşil kalırdı."""
    from fastapi.testclient import TestClient

    from meridian import api
    d = TestClient(api.app).get("/api/diagnostics").json()
    assert set(d["mandallar"]) == {"alarm_mandal", "watchdog_alarmed", "integrity_alarmed",
                                   "koruma_alarmed"}
    aile = d["durum_sozlugu"]["aileler"]
    assert set(aile) == set(D.AILE_SIRASI), f"aile kümesi §9.1 ile ayrıştı: {sorted(aile)}"
    assert aile["kadans"] == 17 and aile["dedektor"] == 8 and aile["canlilik"] == 2
    assert aile["bekci"] == 4 and aile["kilit"] == 3 and aile["mandal"] == 4
    assert aile["hermes"] == 1 and aile["intraday"] == 5 and aile["kitap"] >= 1
    kelimeler = set(D.PANO_KELIME.values())
    assert all(s["kelime"] in kelimeler for s in d["durum_sozlugu"]["satirlar"])
    # BOŞ SANDBOX'TA KADANS ÖLÇÜLDÜ VE HİÇ KOŞMADI DER — "PENCEREDE" diye yeşile boyanmaz
    kad = [s for s in d["durum_sozlugu"]["satirlar"] if s["aile"] == "kadans"]
    assert {s["kelime"] for s in kad} == {"HİÇ KOŞMADI"}
    # KİLİT DİLİMİ GERÇEKTEN BAĞLI MI: `hud` boş geçirilseydi üç kol da ÖLÇÜLEMEDİ olurdu ve
    # sayım (3) yine tutardı — hüküm okunmadan sayı tek başına kablolamayı KANITLAMAZ.
    kilit = {s["kimlik"]: s for s in d["durum_sozlugu"]["satirlar"] if s["aile"] == "kilit"}
    assert kilit["soft_halt"]["kelime"] == "KAPALI" and kilit["soft_halt"]["ok"] is True
    assert kilit["halt_learning"]["kelime"] == "KAPALI"
    # nabız defteri yok → devre kesici ÖLÇÜLEMEDİ (fail-open "kapalı" UYDURULMAZ)
    assert kilit["devre_kesici"]["kelime"] == "ÖLÇÜLEMEDİ"


# =============================================================================================
# I — YASA 6: yeni alanların okuyucusu ADIYLA kayıtlı
# =============================================================================================

def test_i_yeni_alanlarin_okuyucusu_beyanli():
    """`mandallar` ve `satirlar[].kelime` okuyucusuz doğmaz: modül docstring'i okuyucu zincirini
    ADIYLA taşır (Yasa 6 — fonksiyon-düzeyi yüzeyleri codelaw statik olarak göremez)."""
    kaynak = (ROOT / "meridian/durum_sozlugu.py").read_text(encoding="utf-8")
    for okuyucu in ("api._durum_sozlugu", "DurumSozlugu.tsx",
                    "test_durum_sozlugu_aileler_v503"):
        assert okuyucu in kaynak, f"okuyucu beyanı yok: {okuyucu}"
    api_kaynak = (ROOT / "meridian/api.py").read_text(encoding="utf-8")
    assert '"mandallar"' in api_kaynak, "mandal yüzeyi /api/diagnostics'te servis edilmiyor"
