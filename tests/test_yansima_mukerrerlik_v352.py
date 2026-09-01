"""test_yansima_mukerrerlik_v352.py — YANSIMA MÜKERRERLİK KAPISI (2026-09-01).

ÖLÇÜM (ilk akıbet karar turu, 2026-09-01): 22 önerinin ~%45'i BELLEK-YOKLUĞU İSRAFIydı — üç
sınıf: (a) daha önce doğmuş bir öneriyi yeniden doğuran MÜKERRER, (b) zaten var olan bir şeyi
isteyen, (c) çözülmüş bir kalemi yeniden isteyen. Üçü de aynı kök nedene bakar: öneri doğarken
akıbet defterine HİÇ BAKILMIYOR. Kapının başarı ölçüsü donuk ve plana yazılı: israf %45 → ≤%10,
bir sonraki karar turunda ölçülür.

KAPININ YERİ — TEŞHİSLE SEÇİLDİ, VARSAYILMADI. `improvement_proposals.jsonl`in TEK yazarı
`nous_eval._oneri_kaydet`tir (ledgers sözleşmesi `writers=("nous_eval.py",)`, statik tarama
`test_nous_eval_v131::test_E2` ile çivili; `hermes.py:~4483` yalnız TÜKETİCİ yorumudur, yazmaz).
Ama o append noktası ÜÇ tüketicinin ORTAK atası DEĞİLDİR: `koprule` (H4 kuyruğu) ondan ÖNCE,
`boru` (fiş) ondan SONRA koşar ve fiş satırı `_oneri_kaydet`in ürettiği `id`yi taşır. Kapı yalnız
append'e konsaydı mükerrer öneri (i) yine bir H4 ölçüm sırası harcar, (ii) `id: None` taşıyan —
hiçbir öneriye işaret etmeyen — bir fiş doğururdu. Bu yüzden kapı ÜÇ YOLUN AYRIM NOKTASINA,
`ayristir`dan hemen sonrasına konur: mükerrer öneri kalite kapısından düşen bir öneri gibi
davranır ve düşüşü SAYILI + GEREKÇELİdir (`dusme_nedenleri`, koşu kaydında ve panoda görünür).

FAIL-OPEN, BEYANLA: defter okunamıyorsa bastırma YOKTUR. Ölçülemeyen bir benzerlikle öneri
bastırmak, sahte bir hüküm vermek olurdu (uydurma yasağı: `mukerrer=None` + neden loglanır).

TEK-KAYNAK: defterin taban adı iki yerde yaşamak ZORUNDA — motor `store` üzerinden görece adla
okur, `ops/akibet.py` A1'deki MUTLAK yolu taşır (meridian'i ithal edemez). Kopya kaçınılmaz olduğu
için AYRIŞMA ÇİVİSİ yazılır (bkz. `test_defter_adi_ops_akibet_ile_AYRISMAZ`).

HİÇBİR TEST LLM ÇAĞIRMAZ (`chain_text` enjekte edilir) ve HİÇBİR TEST CANLI STATE'E YAZMAZ.
"""
from __future__ import annotations

import ast
import json
import pathlib
import re

import pytest

from meridian import hermes, mukerrerlik, nous_eval, obs, store

_KNOB_A = "stop_loss_atr_mult"      # GERÇEK bounds düğmesi (min 0.8 · max 4.0 · step 0.1)
_KNOB_B = "exit.time_stop_days"     # min 3 · max 40 · step 1

# ---- GERÇEK VAKA SINIFININ SENTETİK ÇİFTLERİ ----------------------------------------------------
# Defter İÇERİĞİ UYDURULMAZ: aşağıdaki metinler testin KENDİ fikstürüdür; gerçek vakaya (2026-09-01
# karar turu, "aynı şeyi ikinci kez isteyen" sınıfı) yalnız ATIF yapılır. Çiftler o sınıfın iki
# tipik biçimini taşır: (1) aynı istek, EK BİR CÜMLECİKLE genişletilmiş; (2) aynı istek, EŞ ANLAMLI
# fiille yeniden yazılmış.
_ESKI_1 = "sef brifingine acik onerilerin yas listesi eklensin"
_YENI_1 = "sef brifingine acik onerilerin yas listesi eklensin — her brifingde tek satir"
_ESKI_2 = "reddedilen onerilerin gerekcesi karar satirinda tutulsun"
_YENI_2 = "reddedilen onerilerin gerekcesi karar satirinda saklansin"
_ALAKASIZ = "gunluk alarm sayaci panoda kirmizi rozetle gosterilsin"


def _tohumla(st):
    """`sandbox_state` boş state verir; köprünün bounds/goal'a ihtiyacı var (v125/v131 ile aynı not)."""
    for f in ("bounds.yaml", "goal.yaml"):
        p = st / f
        if not p.exists():
            p.write_text(pathlib.Path("state").joinpath(f).read_text())
    return st


def _dogum(oneri_id: str, metin: str) -> dict:
    """`olay=oneri` doğum satırı — şema `ops/akibet.py` modül docstring'indeki DEFTER ŞEMASI."""
    return {"ts": "2026-08-30T10:00:00+00:00", "olay": "oneri", "oneri_id": oneri_id,
            "kaynak": "operator", "oneri": metin}


def _karar(oneri_id: str, karar: str) -> dict:
    return {"ts": "2026-08-31T10:00:00+00:00", "olay": "karar", "oneri_id": oneri_id,
            "karar": karar, "karar_veren": "rol1", "gerekce": "kapsam disi"}


def _defter(*satirlar: dict) -> None:
    store.write_jsonl(mukerrerlik.DEFTER, list(satirlar))


def _dogum_satiri(oneri_id: str, metin: str) -> dict:
    """N-serisi DOĞUM satırı (`improvement_proposals.jsonl`) — kapının İKİNCİ kaynağı."""
    return {"ts": "2026-08-24T10:00:00+00:00", "id": oneri_id, "hafta": "2026-W30",
            "alan": "kar_selalesi", "gozlem": "net_r -0.0421", "oneri": metin,
            "beklenen_etki": "x", "onerilen_olcum": "y", "oncelik": "yuksek",
            "sekil": "tasarim", "kanit_atifi": ["net_r"]}


def _dogumlar(*satirlar: dict) -> None:
    store.write_jsonl(nous_eval.PROPOSALS_FILE, list(satirlar))


def _iki_kaynagi_patlat(monkeypatch, *, defter: bool = True, dogum: bool = True) -> None:
    """Seçilen kaynak(lar)ın okunmasını `OSError`la düşürür. NOT: `nous_eval` doğum defterini
    KENDİ yolunda da okur (`_next_seq`, `onceki_akibet`) — bu yüzden entegrasyon testlerinde
    yalnız `dogum=False` ile çağrılır; birim testleri ikisini birden düşürebilir."""
    _asil = store.read_jsonl
    hedef = ({mukerrerlik.DEFTER} if defter else set()) | \
            ({nous_eval.PROPOSALS_FILE} if dogum else set())

    def _patla(name, *a, **k):
        if name in hedef:
            raise OSError("izin yok")
        return _asil(name, *a, **k)

    monkeypatch.setattr(store, "read_jsonl", _patla)


def _tel(**ek) -> dict:
    """Küçük ama GERÇEKÇİ telemetri paketi (v131 emsali): atıf jetonları gerçek alan/sayılardır."""
    from meridian import analytics
    t = {"hafta": "2026-W31",
         "bolum_adlari": list(analytics.TELEMETRY_SECTIONS),
         "bolumler": {
             "kar_selalesi": {"n": 95, "genel": {"net_r": -0.0421, "sinyal_mfe_r": 0.9648}},
             "veto_istatistigi": {"islem_kapisi": {"n_plan": 390}},
         },
         "bounds_dugmeleri": [_KNOB_A, _KNOB_B, "entry.min_score"]}
    t.update(ek)
    return t


def _oneri(**ek) -> dict:
    o = {"alan": "kar_selalesi",
         "gozlem": "kar_selalesi bölümünde net_r -0.0421 iken sinyal_mfe_r 0.9648 — çıkış "
                   "sunulan hareketin neredeyse tamamını geri veriyor",
         "oneri": _ALAKASIZ,
         "beklenen_etki": "net_r +0.10 yönünde",
         "onerilen_olcum": "profit_waterfall geri_verilen_r yeniden ölçülür",
         "oncelik": "yuksek", "sekil": "tasarim"}
    o.update(ek)
    return o


def _cevap(oneriler: list) -> str:
    return json.dumps({"oneriler": oneriler}, ensure_ascii=False)


def _zincir(monkeypatch, oneriler: list) -> None:
    monkeypatch.setattr(hermes, "chain_text", lambda *a, **k: {
        "text": _cevap(oneriler), "beyin": "nous", "model": "test-model", "neden": {}})


@pytest.fixture
def olaylar(monkeypatch):
    kayit: list[dict] = []
    monkeypatch.setattr(obs, "log", lambda ev, **kw: kayit.append({"ev": ev, **kw}) or {})
    return kayit


# =================================================================================================
# ① NORMALİZASYON — büyük harf/noktalama/aksan YUTULUR, SAYILAR KORUNUR
# =================================================================================================
def test_jetonlama_buyuk_harf_noktalama_ve_TURKCE_aksani_yutar(sandbox_state):
    """Aynı istek iki kez, biri aksanlı biri aksansız yazıldığında AYNI jeton kümesini vermeli —
    yoksa "eşiği" ile "esigi" iki ayrı fikir sayılır ve kapı en sık mükerrer biçimini kaçırır."""
    assert mukerrerlik.jetonla("Eşiği 0.6'ya ÇEK!") == mukerrerlik.jetonla("esigi 0.6 ya cek")


def test_jetonlama_SAYIYI_korur_farkli_sayi_farkli_jeton(sandbox_state):
    """SAYI SİLİNMEZ: "eşiği 0.6 yap" ile "eşiği 0.9 yap" AYNI öneri DEĞİLDİR. Noktalama silici bir
    normalize `0.6`yı `0` ve `6` diye ikiye bölerdi — sayı korunuyor demek, TAM olarak korunuyor
    demektir."""
    a = mukerrerlik.jetonla("esigi 0.6 yap")
    b = mukerrerlik.jetonla("esigi 0.9 yap")
    assert "0.6" in a and "0.9" in b, f"sayı jetonu bölünmüş: {a} / {b}"
    assert a != b


# =================================================================================================
# ② mukerrer_mi — HÜKÜM
# =================================================================================================
def test_ayni_metin_MUKERRER_ve_eslesen_id_ile_donar(sandbox_state):
    _defter(_dogum("AKB-0001", _ESKI_1))
    h = mukerrerlik.mukerrer_mi(_ESKI_1)
    assert h["mukerrer"] is True
    assert h["eslesen_id"] == "AKB-0001"
    assert h["benzerlik"] == 1.0
    assert h["eslesen_kaynak"] == mukerrerlik.KAYNAK_DEFTER
    assert h["neden"] and str(mukerrerlik.ESIK) in h["neden"], \
        "bastırma gerekçesi eşiği ADIYLA söylemiyor — hüküm denetlenemez olur"


def test_yeniden_yazilmis_ayni_istek_MUKERRER(sandbox_state):
    """GERÇEK VAKA SINIFI (2026-09-01 karar turu): aynı istek eş anlamlı fiille yeniden doğdu."""
    _defter(_dogum("AKB-0002", _ESKI_2))
    h = mukerrerlik.mukerrer_mi(_YENI_2)
    assert h["mukerrer"] is True and h["eslesen_id"] == "AKB-0002"
    assert mukerrerlik.ESIK <= h["benzerlik"] < 1.0, \
        "çift ya eşiğin altında ya birebir aynı — ölçülen şey yeniden-yazım DEĞİL"


def test_genisletilmis_ayni_istek_MUKERRER(sandbox_state):
    """GERÇEK VAKA SINIFI: aynı istek, ek bir cümlecikle genişletilerek yeniden doğdu."""
    _defter(_dogum("AKB-0003", _ESKI_1))
    h = mukerrerlik.mukerrer_mi(_YENI_1)
    assert h["mukerrer"] is True and h["eslesen_id"] == "AKB-0003"


def test_farkli_oneri_MUKERRER_DEGIL_ama_benzerlik_OLCULUR(sandbox_state):
    """Hüküm "hayır" olduğunda da benzerlik ölçülmüş bir SAYIDIR: eşiğin ne kadar altında
    kalındığı, eşiğin ölçümle ayarlanabilmesinin tek girdisidir (kart yolu)."""
    _defter(_dogum("AKB-0004", _ESKI_1))
    h = mukerrerlik.mukerrer_mi(_ALAKASIZ)
    assert h["mukerrer"] is False and h["eslesen_id"] is None
    assert isinstance(h["benzerlik"], float) and h["benzerlik"] < mukerrerlik.ESIK
    assert h["neden"] is None


def test_REDDEDILMIS_oneriye_benzeyen_de_MUKERRER(sandbox_state):
    """Karşılaştırma kümesi AÇIK + KARARLI önerilerin TAMAMIDIR. Reddedilmiş bir fikri
    "artık açık değil" diye kümeden çıkarmak, aynı fikrin her turda yeniden doğmasına izin
    vermek olurdu — israfın ölçülen ikinci biçimi tam budur."""
    _defter(_dogum("AKB-0005", _ESKI_2), _karar("AKB-0005", "reddedildi"))
    h = mukerrerlik.mukerrer_mi(_YENI_2)
    assert h["mukerrer"] is True and h["eslesen_id"] == "AKB-0005"


def test_idsiz_satir_karsilastirma_kumesine_GIRMEZ(sandbox_state):
    """Kimliksiz bir satırla eşleşme, DENETLENEMEZ bir bastırma üretirdi: obs satırı "neye
    benzedi" sorusunu cevaplayamazdı. `akibet_turet` de kimliksiz satırı `olculemeyen` sayar —
    aynı disiplin, aynı yönde (fail-open)."""
    _defter({"ts": "2026-08-30T10:00:00+00:00", "olay": "oneri", "oneri": _ESKI_1})
    h = mukerrerlik.mukerrer_mi(_ESKI_1)
    assert h["mukerrer"] is False, "kimliksiz satırla eşleşip denetlenemez bastırma üretti"


def test_defter_BOS_iken_bastirma_YOK_ve_benzerlik_OLCULEMEZ(sandbox_state):
    """Boş defter MEŞRU bir hâldir (ilk koşu) — hüküm "mükerrer değil"dir. Ama benzerlik
    ÖLÇÜLMEMİŞTİR: karşılaştırma kümesi yokken 0.0 yazmak, ölçülmemiş bir sayıyı ölçülmüş
    göstermek olurdu (sıfır ile "bilmiyorum" aynı şey değildir)."""
    h = mukerrerlik.mukerrer_mi(_ESKI_1)
    assert h["mukerrer"] is False and h["benzerlik"] is None
    assert h["neden"] == mukerrerlik.NEDEN_DEFTER_BOS


def test_IKI_KAYNAK_da_okunamazsa_bastirma_YOK_hukum_None(sandbox_state, monkeypatch):
    """FAIL-OPEN, BEYANLA: ölçülemeyen benzerlikle öneri bastırmak sahte hüküm olurdu. Hüküm
    `None` YALNIZ hiçbir kaynak okunamadığında verilir — kısmi körlük ayrı sınıftır."""
    _iki_kaynagi_patlat(monkeypatch)
    h = mukerrerlik.mukerrer_mi(_ESKI_1)
    assert h["mukerrer"] is None and h["benzerlik"] is None
    assert h["neden"] and "izin yok" in h["neden"], \
        "ölçülemedi hâli SEBEBİNİ taşımıyor — 'neden' alanı boş bir beyandır"
    assert set(h["olculemeyen"]) == {mukerrerlik.KAYNAK_DEFTER, mukerrerlik.KAYNAK_DOGUM}


def test_metin_BOSSA_hukum_None(sandbox_state):
    """Jetonsuz metnin benzerliği ölçülemez (payda sıfır). 0.0 yazmak "ölçtüm, benzemiyor"
    derdi — oysa ölçülen bir şey yok."""
    _defter(_dogum("AKB-0006", _ESKI_1))
    h = mukerrerlik.mukerrer_mi("   !!!   ")
    assert h["mukerrer"] is None and h["neden"] == mukerrerlik.NEDEN_METIN_YOK
    assert h["olculemeyen"] == {}, "kaynak arızası YOKKEN körlük kaydı uydurulmuş"


# =================================================================================================
# ②b İKİNCİ KAYNAK — N-SERİSİ DOĞUM DEFTERİ (Rol-1 hükmü 2026-09-01)
# =================================================================================================
# NEDEN GENİŞLEDİ: ölçülen %45 israfın ANA sınıfı, hermes'in KENDİ eski önerilerini yeniden
# üretmesiydi. O önerilerin doğum metinleri akıbet defterinde DEĞİL `improvement_proposals.jsonl`da
# yaşar (akıbet defteri N-serisinin yalnız karar/sonuç satırlarını taşır, kopya yok — bkz.
# `ops/akibet.py` DEFTER ŞEMASI). Tek kaynaklı kapı tam da bu bacağa kördü.
def test_DOGUM_defterindeki_eski_hermes_onerisi_de_MUKERRER(sandbox_state):
    """Kapının var oluş sebebinin ta kendisi: geçen haftanın N-serisi önerisi bu hafta yeniden
    doğmaya çalışıyor. Akıbet defteri BOŞ — eşleşme YALNIZ doğum defterinden gelebilir."""
    _dogumlar(_dogum_satiri("N00017", _ESKI_1))
    h = mukerrerlik.mukerrer_mi(_YENI_1)
    assert h["mukerrer"] is True
    assert h["eslesen_id"] == "N00017"
    assert h["eslesen_kaynak"] == mukerrerlik.KAYNAK_DOGUM


def test_akibet_eslesmesi_kaynak_ETIKETINI_defter_tasir(sandbox_state):
    """İki kaynak iki AYRI kimlik uzayı kullanıyor (`AKB-####` · `N#####`). Etiket olmadan
    "eşleşen id" hangi deftere bakılacağını söylemez — denetim yolu kırılırdı."""
    _defter(_dogum("AKB-0011", _ESKI_1))
    h = mukerrerlik.mukerrer_mi(_YENI_1)
    assert h["mukerrer"] is True and h["eslesen_id"] == "AKB-0011"
    assert h["eslesen_kaynak"] == mukerrerlik.KAYNAK_DEFTER


def test_iki_kaynakta_da_aday_varsa_EN_YAKIN_secilir(sandbox_state):
    """Kaynak sırası değil BENZERLİK karar verir. Sıraya göre seçen bir kapı, daha uzak bir
    eşleşmeyi rapor eder ve operatör yanlış kaydı açardı."""
    _defter(_dogum("AKB-0012", _ESKI_2))          # _YENI_2 ile ~0.71
    _dogumlar(_dogum_satiri("N00023", _YENI_2))   # _YENI_2 ile 1.0
    h = mukerrerlik.mukerrer_mi(_YENI_2)
    assert h["eslesen_id"] == "N00023" and h["eslesen_kaynak"] == mukerrerlik.KAYNAK_DOGUM
    assert h["benzerlik"] == 1.0


def test_dogum_satirinda_kimlik_yoksa_kumeye_GIRMEZ(sandbox_state):
    """Kimliksiz satır kuralı İKİ kaynakta da aynıdır — asimetri, kapının bir yarısını
    denetlenemez bırakırdı."""
    _dogumlar({"ts": "2026-08-24T10:00:00+00:00", "oneri": _ESKI_1})
    assert mukerrerlik.mukerrer_mi(_ESKI_1)["mukerrer"] is False


def test_kaynaklardan_BIRI_okunamazsa_otekiyle_DEVAM_eder(sandbox_state, monkeypatch):
    """KISMİ KÖRLÜK TAM KÖRLÜK DEĞİLDİR. Akıbet defteri okunamıyor diye doğum defterindeki
    apaçık mükerreri geçirmek, ölçülebilen bir bilgiyi çöpe atmak olurdu. Ama körlük SESSİZ de
    kalmaz: `olculemeyen` okunamayan kaynağı ADIYLA taşır."""
    _dogumlar(_dogum_satiri("N00031", _ESKI_1))
    _iki_kaynagi_patlat(monkeypatch, dogum=False)
    h = mukerrerlik.mukerrer_mi(_YENI_1)
    assert h["mukerrer"] is True and h["eslesen_kaynak"] == mukerrerlik.KAYNAK_DOGUM
    assert set(h["olculemeyen"]) == {mukerrerlik.KAYNAK_DEFTER}
    assert "izin yok" in h["olculemeyen"][mukerrerlik.KAYNAK_DEFTER]


def test_kismi_korlukte_hukum_HAYIR_ise_de_korluk_TASINIR(sandbox_state, monkeypatch):
    """"Benzemiyor" hükmü kısmi körlükte de verilir (okunabilen kümeyle), ama hükmün YANINDA
    neyin okunamadığı durur — yoksa eksik taramaya dayanan bir "temiz" iddiası doğardı."""
    _dogumlar(_dogum_satiri("N00032", _ALAKASIZ))
    _iki_kaynagi_patlat(monkeypatch, dogum=False)
    h = mukerrerlik.mukerrer_mi(_YENI_1)
    assert h["mukerrer"] is False
    assert set(h["olculemeyen"]) == {mukerrerlik.KAYNAK_DEFTER}


def test_dogum_defteri_adi_nous_eval_den_TURETILIR_literal_kopya_YOK(sandbox_state):
    """TEK-KAYNAK. Defteri YAZAN sabit `nous_eval.PROPOSALS_FILE`dır; kapı onu ikinci bir
    literal olarak kopyalarsa, yazarın defteri ile okuyanın defteri sessizce ayrışabilir.
    Türetme gecikmeli ithalle yapılır (üst düzeyde karşılıklı ithal döngü olurdu).

    ÖLÇÜ AST'DİR, METİN DEĞİL: yorum/docstring'de defterin adını ANMAK kopya değildir (aksine
    okunabilirlik); ayrışmayı doğuran şey aynı adın ikinci bir string SABİTİ olarak yaşamasıdır."""
    tree = ast.parse(pathlib.Path("meridian/mukerrerlik.py").read_text(encoding="utf-8"))
    kopya = [n.lineno for n in ast.walk(tree) if isinstance(n, ast.Constant)
             and n.value == nous_eval.PROPOSALS_FILE]
    assert kopya == [], f"doğum defterinin adı literal olarak kopyalanmış (satır {kopya})"
    assert mukerrerlik._dogum_defteri() == nous_eval.PROPOSALS_FILE


# =================================================================================================
# ③ TEK KAYNAK — eşik TEK sabit, defter adı ops/akibet.py ile AYRIŞMAZ
# =================================================================================================
def test_esik_TEK_SABIT_ve_gerekce_yorumu_tasir():
    """Eşik bir KARARDIR: sayının yanında niçin o sayı olduğu yazmazsa, sonraki tur onu ölçümsüz
    oynatır (kart yolu yerine his yolu). Yorum ≥20 karakter — CLAUDE.md'nin işaretli-kaçış
    disipliniyle aynı asgari."""
    src = pathlib.Path("meridian/mukerrerlik.py").read_text(encoding="utf-8")
    assert mukerrerlik.ESIK == 0.6
    sayilar = re.findall(r"^([A-Z_]+)(?:\s*:[^=]*)?\s*=\s*0\.\d+\s*$", src, flags=re.M)
    assert sayilar == ["ESIK"], f"ikinci bir eşik sabiti doğmuş: {sayilar}"
    m = re.search(r"((?:^#.*\n)+)ESIK", src, flags=re.M)
    assert m and len(m.group(1)) >= 20, "ESIK sabitinin ÜSTÜNDE ≥20 karakterlik gerekçe yorumu yok"


def test_defter_adi_ops_akibet_ile_AYRISMAZ():
    """AYRIŞMA ÇİVİSİ (tek-kaynak yasası). Motor deftere GÖRECE adla (`store` çözer), `ops/akibet.py`
    A1'deki MUTLAK yolla erişir — `ops` `meridian`i ithal EDEMEZ (obs'a ulaşırdı), yani kopya
    kaçınılmazdır. İki taraf ayrıştığı gün kapı BAŞKA bir defteri okur ve sessizce hiçbir şey
    bastırmaz: bu çivi o sessizliği sese çevirir."""
    src = pathlib.Path("ops/akibet.py").read_text(encoding="utf-8")
    m = re.search(r'^DEFTER\s*=\s*"([^"]+)"', src, flags=re.M)
    assert m, "ops/akibet.py içinde DEFTER sabiti bulunamadı (ad değişmiş olabilir)"
    assert m.group(1).rsplit("/", 1)[-1] == mukerrerlik.DEFTER, \
        f"defter adı ayrıştı: ops={m.group(1)!r} · motor={mukerrerlik.DEFTER!r}"


# =================================================================================================
# ④ ENTEGRASYON — nous_eval haftalık koşusu
# =================================================================================================
def test_mukerrer_oneri_DEFTERE_YAZILMAZ_yenisi_yazilir(sandbox_state, monkeypatch, olaylar):
    _tohumla(sandbox_state)
    _defter(_dogum("AKB-0007", _ESKI_1))
    _zincir(monkeypatch, [_oneri(alan="kar_selalesi", oneri=_YENI_1),
                          _oneri(alan="veto_istatistigi", oneri=_ALAKASIZ,
                                 gozlem="veto_istatistigi bölümünde n_plan 390 ölçüldü")])
    nous_eval.haftalik_degerlendirme(telemetri=_tel())
    rows = store.read_jsonl(nous_eval.PROPOSALS_FILE)
    assert [r["oneri"] for r in rows] == [_ALAKASIZ], \
        f"mükerrer öneri deftere yazıldı ya da yenisi düştü: {[r['oneri'] for r in rows]}"


def test_bastirma_OBS_ile_KAYDEDILIR_eslesen_id_ve_benzerlikle(sandbox_state, monkeypatch, olaylar):
    """YASA 6: bastırma sessiz olamaz. Olay satırı NEYE benzediğini (id) ve NE KADAR benzediğini
    (sayı) taşımazsa, eşiğin doğru yerde olup olmadığı hiçbir zaman ölçülemez."""
    _tohumla(sandbox_state)
    _defter(_dogum("AKB-0008", _ESKI_1))
    _zincir(monkeypatch, [_oneri(oneri=_YENI_1)])
    nous_eval.haftalik_degerlendirme(telemetri=_tel())
    ev = [e for e in olaylar if e["ev"] == mukerrerlik.OLAY_BASTIRILDI]
    assert len(ev) == 1, f"bastırma olayı yok/çift: {[e['ev'] for e in olaylar]}"
    assert ev[0]["eslesen_id"] == "AKB-0008"
    assert isinstance(ev[0]["benzerlik"], float) and ev[0]["benzerlik"] >= mukerrerlik.ESIK


def test_mukerrer_KUYRUGA_da_girmez(sandbox_state, monkeypatch, olaylar):
    """KAPI KÖPRÜDEN ÖNCEDİR. Kapı yalnız `_oneri_kaydet`in append'ine konsaydı mükerrer bir
    `sekil=parametre` önerisi yine bir H4 ölçüm sırası harcardı — deftere yazılmayan ama bütçe
    yiyen bir hayalet. Bu test kapının YERİNİ ölçer, davranışını değil."""
    _tohumla(sandbox_state)
    _defter(_dogum("AKB-0009", _ESKI_1))
    _zincir(monkeypatch, [_oneri(oneri=_YENI_1, sekil="parametre",
                                 parametreler={_KNOB_A: 2.0, _KNOB_B: 10})])
    out = nous_eval.haftalik_degerlendirme(telemetri=_tel())
    assert store.read_jsonl("composite_queue.jsonl") == [], "mükerrer öneri kuyruğa girdi"
    assert out["kosu"]["n_kuyruk"] == 0


def test_dusme_KOSU_KAYDINDA_sayili_ve_gerekceli(sandbox_state, monkeypatch, olaylar):
    """BEDEL YASASI: gürültüyü azaltan değişiklik ne KAYBETTİĞİNİ de ölçer. Bastırılan öneri
    sayısı koşu kaydında (dolayısıyla panoda) durmazsa, kapı bir gün fazla ısırdığında belirti
    HİÇBİR ŞEY olurdu."""
    _tohumla(sandbox_state)
    _defter(_dogum("AKB-0010", _ESKI_1))
    _zincir(monkeypatch, [_oneri(oneri=_YENI_1)])
    out = nous_eval.haftalik_degerlendirme(telemetri=_tel())
    kosu = out["kosu"]
    assert kosu["n_kabul"] == 0 and kosu["n_uretilen"] == 1
    assert kosu["dusme_nedenleri"].get(mukerrerlik.DUSME_NEDENI) == 1, \
        f"düşme nedeni sayılmamış: {kosu['dusme_nedenleri']}"
    assert kosu["n_dusen"] == 1


def test_akibet_okunamazsa_oneri_GECER_ve_KISMI_korluk_loglanir(sandbox_state, monkeypatch,
                                                                olaylar):
    """UÇTAN UCA: akıbet defteri erişilemezken sistem öneri üretmeyi BIRAKMAZ (doğum defteri
    okunabiliyor ve boş → eşleşme yok), ama körlüğünü ADIYLA kaydeder. `tam_korluk=False`,
    çünkü kaynaklardan biri okunabildi — iki hâli aynı olaya çöktürmek "ne kadar kör kaldık"
    sorusunu cevaplanamaz yapardı."""
    _tohumla(sandbox_state)
    _iki_kaynagi_patlat(monkeypatch, dogum=False)
    _zincir(monkeypatch, [_oneri(oneri=_YENI_1)])
    nous_eval.haftalik_degerlendirme(telemetri=_tel())
    assert len(store.read_jsonl(nous_eval.PROPOSALS_FILE)) == 1, \
        "ölçülemeyen benzerlik yüzünden öneri bastırıldı — sahte hüküm"
    ev = [e for e in olaylar if e["ev"] == mukerrerlik.OLAY_OLCULEMEDI]
    assert len(ev) == 1 and "izin yok" in str(ev[0].get("neden"))
    assert ev[0]["kaynak"] == mukerrerlik.KAYNAK_DEFTER and ev[0]["tam_korluk"] is False


def test_hermesin_ONCEKI_haftaki_onerisi_yeniden_DOGMAZ(sandbox_state, monkeypatch, olaylar):
    """ROL-1 HÜKMÜNÜN UÇTAN UCA KANITI (2026-09-01): ölçülen %45 israfın ana sınıfı buydu —
    hermes kendi geçen haftaki önerisini yeniden üretiyordu. Akıbet defteri BOŞ; kapı YALNIZ
    doğum defterinden bilebilir."""
    _tohumla(sandbox_state)
    _dogumlar(_dogum_satiri("N00017", _ESKI_1))
    _zincir(monkeypatch, [_oneri(oneri=_YENI_1)])
    nous_eval.haftalik_degerlendirme(telemetri=_tel())
    rows = store.read_jsonl(nous_eval.PROPOSALS_FILE)
    assert [r["id"] for r in rows] == ["N00017"], \
        f"eski öneri yeniden doğdu: {[r.get('id') for r in rows]}"
    ev = [e for e in olaylar if e["ev"] == mukerrerlik.OLAY_BASTIRILDI]
    assert len(ev) == 1 and ev[0]["eslesen_id"] == "N00017"
    assert ev[0]["eslesen_kaynak"] == mukerrerlik.KAYNAK_DOGUM


def test_yeni_oneri_KENDISIYLE_eslesmez(sandbox_state, monkeypatch, olaylar):
    """SIRA TAŞIYICIDIR. Doğum defteri artık karşılaştırma kümesinde olduğu için, kapı
    `_oneri_kaydet`ten SONRA koşsaydı her öneri kendi yeni satırıyla 1.0 benzerlik yakalar ve
    SİSTEM HİÇBİR ÖNERİ ÜRETEMEZDİ. Bu test o çöküşü davranışla ölçer."""
    _tohumla(sandbox_state)
    _zincir(monkeypatch, [_oneri(oneri=_ALAKASIZ)])
    nous_eval.haftalik_degerlendirme(telemetri=_tel())
    assert len(store.read_jsonl(nous_eval.PROPOSALS_FILE)) == 1, \
        "yepyeni öneri kendi kaydıyla eşleşip bastırıldı"
    assert [e for e in olaylar if e["ev"] == mukerrerlik.OLAY_BASTIRILDI] == []


def test_kapi_KOPRUDEN_ve_DEFTER_YAZIMINDAN_once_kosar_AST():
    """SIRANIN YAPISAL ÇİVİSİ (davranış çivisinin kardeşi). Kapı `koprule`den sonraya kayarsa
    mükerrer öneri H4 bütçesi yer; `_oneri_kaydet`ten sonraya kayarsa kendi kaydıyla eşleşir.
    İkisi de sessiz kayma — bu çivi sırayı KAYNAKTAN ölçer."""
    tree = ast.parse(pathlib.Path("meridian/nous_eval.py").read_text(encoding="utf-8"))
    fn = next(n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "haftalik_degerlendirme")

    def _satirlar(ad: str) -> list[int]:
        return [n.lineno for n in ast.walk(fn) if isinstance(n, ast.Call)
                and isinstance(n.func, ast.Name) and n.func.id == ad]

    kapi, kopru, yazim = _satirlar("_mukerrer_ele"), _satirlar("koprule"), _satirlar("_oneri_kaydet")
    assert kapi and kopru and yazim, f"çağrılar bulunamadı: {kapi} {kopru} {yazim}"
    assert max(kapi) < min(kopru), "mükerrerlik kapısı köprüden SONRA koşuyor"
    assert max(kapi) < min(yazim), "mükerrerlik kapısı defter yazımından SONRA koşuyor"
