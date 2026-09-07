"""BRİFİNG SOUL DENETÇİSİ — ŞEMA DIŞI CEVABIN TEŞHİS ENSTRÜMANTASYONU (v434, TSK-138 dilim-1,
2026-09-07).

BU DOSYA BİR DÜZELTME ÇİVİLEMEZ, BİR ÖLÇÜM ALETİ ÇİVİLER. Canlıda ölçülen arıza şu (A1
`events.jsonl`, olay `brifing_kural_denetimi`, 2026-09-06 22:04Z): `hukum=denetlenemedi ·
kaynak=llm_dustu · cagri_n=2 · gerekce='denetçi cevabı JSON değil (şema dışı)'`. Kapıda 429/502
YOK, yani kota değil. Ama HANGİ MODEL cevap verdi ve CEVABIN METNİ neydi — ikisi de defterde YOK.
Teşhis o iki alan olmadan yapılamaz; systematic-debugging Faz-1 bitmeden çözüm yazılmaz, o yüzden
bu turda denetçi istemi, profil kurulumu ve JSON zorlaması HİÇ DEĞİŞMEZ.

ÜÇ SINIF ÇİVİLENİR:
  1. `Hukum.cevap_bas` — ŞEMA DIŞI cevabın boşlukları katlanmış İLK 200 karakteri. `None` ile `""`
     AYRI BİLGİDİR ve ayrımı bir üslup tercihi değil UYDURMA YASAĞIdır: `None` "ölçemedim"
     (cevap hiç gelmedi / çağrı düştü), `""` "ÖLÇTÜM, cevap boştu". İkisini tek değere katlamak,
     susan bir modelle düşen bir çağrıyı aynı satıra yazmak olurdu.
  2. Model kimliği — denetçiyi HANGİ model cevapladı. Değer UYDURULMAZ, profilin KENDİ
     `config.yaml`ından ÖLÇÜLÜR; okunamıyorsa `None` + ADIYLA olay (Yasa 4).
  3. Yasa 6 — iki yeni alanın OKUYUCUSU. Operatörün HER koşumda (kuru koşum dâhil) gördüğü durum
     satırı son olayın `model`/`cevap_bas` alanlarını basar; okunmayan bir alan üretilmemiştir.

SIR SÜZGECİ ÇİVİLENİR (Yasa 4'ün egress yarısı): `cevap_bas` bir MODEL ÇIKTISIDIR ve o çıktı bir
hata dizgesini (`?apikey=…`) taşıyabilir. Defter de bir veri yüzeyidir — süzgeç atlanırsa sır
`events.jsonl`e YAZILIR. Çivi SAHTE bir sır kullanır; gerçek sır değeri hiçbir yere girmez.

YARDIMCILAR v385'TEN İTHAL EDİLİR, KOPYALANMAZ (tek-kaynak yasası): sahte profil evi, `_Kuyruk`
ve `_sef_kur` iki dosyada ayrı ayrı dursaydı sessizce ayrışırlardı — v385'in sözleşmesi değişince
bu dosya ölçtüğünü sandığı şeyi ölçmez olurdu.

ÖLÇÜLMEDİ, BEYAN EDİLİYOR: gerçek `sef` profili ÇAĞRILMADI (ajan canlıya dokunmaz). Buradaki her
LLM davranışı sapla ölçülür — sınanan MODELİN cevabı değil, KOŞUMUN o cevaba verdiği tepkidir.
"""
from __future__ import annotations

import importlib
import json
import pathlib

import pytest

from tests.test_soul_denetimi_v385 import (  # tek-kaynak: sahte profil/kuyruk/kurulum TEK yerde
    _Kuyruk, _olaylar, _profil_evi, _sef_kur, _temiz_cevap)

KOK = pathlib.Path(__file__).resolve().parent.parent

# GERÇEK PROFİL DOSYASI — ÇİVİ ONU OKUR, ŞEMASINI KOPYALAMAZ. Alan adları (`model.provider` /
# `model.default`) 2026-09-07'de bu dosyadan ÖLÇÜLDÜ; buraya bir kopya yazılsaydı profil bir gün
# alan adını değiştirdiğinde çivi yine yeşil kalır, canlıda kimlik sessizce `None` olurdu.
GERCEK_SEF_PROFILI = KOK / "deploy" / "hermes" / "profiles" / "sef"

# SAHTE SIR — GERÇEK DEĞİL. İzin listesindeki bir ADA bağlanır (`secrets.get` saplanır), çünkü
# `notify.scrub` yalnız `secrets.ALLOWED` adlarını tarar; uydurma bir ad süzgeci hiç çalıştırmaz
# ve çivi süzgeci ölçtüğünü sanarak yeşil kalırdı.
SAHTE_SIR_ADI = "FMP_API_KEY"
SAHTE_SIR = "SAHTE-SIR-DEGERI-1234567890"


@pytest.fixture
def sd():
    return importlib.import_module("ops.soul_denetimi")


class _ObsYakala:
    """`obs.log` saplaması — olay adını ve TÜM kwarg'ları saklar.

    NEDEN SAPLAMA, defter okuması DEĞİL: bu çiviler `gecir`in obs'a NE GEÇTİĞİNİ ölçer; defterden
    okumak aradaki serileştirmeyi de ölçerdi ve bir alan `None` iken yazılmadığında çivi sebebi
    yanlış anlardı."""

    def __init__(self):
        self.cagrilar: list[tuple[str, dict]] = []

    def __call__(self, olay, **alanlar):
        self.cagrilar.append((str(olay), dict(alanlar)))
        return {}

    def alan(self, olay_adi: str, ad: str):
        for o, alanlar in self.cagrilar:
            if o == olay_adi:
                return alanlar.get(ad)
        raise AssertionError(f"`{olay_adi}` olayı hiç yazılmadı: {[o for o, _ in self.cagrilar]}")

    def var_mi(self, olay_adi: str) -> bool:
        return any(o == olay_adi for o, _ in self.cagrilar)


# ================================================================================================
# 1) `cevap_bas` — ŞEMA DIŞI CEVABIN İLK 200 KARAKTERİ
# ================================================================================================

def test_SEMA_DISI_DUZ_METIN_CEVAP_BASI_YAZILIR(sd):
    """Canlıda ölçülen arızanın ta kendisi: denetçi düz metin yazdı, hüküm `llm_dustu` oldu ve
    METİN hiçbir yere düşmedi. Artık düşer — teşhisin tek girdisi budur."""
    h = sd.ayristir("SESSIZ\n\n  bugün  eklenecek\tbir şey yok")
    assert h.kaynak == "llm_dustu", f"düz metin cevap şemayı tuttu sayıldı: {h!r}"
    assert h.cevap_bas == "SESSIZ bugün eklenecek bir şey yok", (
        f"cevap başı yazılmadı ya da boşluklar katlanmadı: {h.cevap_bas!r}")


def test_CEVAP_BASI_ONCE_KATLANIR_SONRA_KIRPILIR(sd):
    """SIRA ÖLÇÜLÜR, VARSAYILMAZ. Önce kırpıp sonra katlamak 200 karakterlik bir pencereyi
    boşluklara harcar ve teşhis metnini KISALTIR — 400 karakterlik bu girdide iki sıra 200'e
    karşı 149 karakter verir, yani fark ölçülebilir."""
    ham = "ab  " * 100                       # 400 karakter, her jetondan sonra ÇİFT boşluk
    h = sd.ayristir(ham)
    assert h.cevap_bas is not None and len(h.cevap_bas) == 200, (
        f"kırpma katlamadan ÖNCE yapıldı (pencere boşluğa gitti): {len(h.cevap_bas or '')}")
    assert "  " not in h.cevap_bas, f"boşluklar katlanmadı: {h.cevap_bas!r}"


def test_UZUN_CEVAP_200_KARAKTERE_KIRPILIR(sd):
    """250 karakterlik bir cevap deftere OLDUĞU GİBİ girseydi, bir gün 64 KB'lık bir düşüş cevabı
    `events.jsonl`i şişirirdi — teşhis alanı bir sızıntı yüzeyi olamaz."""
    h = sd.ayristir("A" * 250)
    assert h.cevap_bas == "A" * 200, f"200 karakter tavanı tutmadı: {len(h.cevap_bas or '')}"


def test_BOS_CEVAP_NONE_DEGIL_BOS_DIZGE(sd):
    """UYDURMA YASAĞININ TA KENDİSİ: `""` = ÖLÇTÜM, cevap boştu; `None` = ölçemedim. İkisi tek
    değere katlansaydı susan bir modelle düşen bir çağrı defterde AYNI görünürdü."""
    for ham in ("", "   \n\t ", None):
        h = sd.ayristir(ham)
        assert h.kaynak == "llm_dustu", f"boş cevap şemayı tuttu sayıldı: {ham!r}"
        assert h.cevap_bas == "", f"boş cevap `None` yazıldı (ölçüldü ≠ ölçülemedi): {ham!r}"


def test_GECERLI_JSON_CEVAP_BASI_YAZMAZ(sd):
    """Alan YALNIZ teşhis içindir. Geçerli hükümde de dolsaydı, her başarılı koşum deftere
    modelin cevabının bir kopyasını yazardı — okuyucusu olmayan bir yazım (Yasa 6)."""
    h = sd.ayristir(_temiz_cevap())
    assert h.kaynak == "llm" and h.cevap_bas is None, f"geçerli hükümde cevap başı doldu: {h!r}"


def test_SEMA_ALANLARI_TUTMAYAN_JSON_DA_CEVAP_BASI_YAZAR(sd):
    """Şema dışı olmanın İKİNCİ biçimi: cevap JSON ama alanlar tutmuyor. Teşhis girdisi aynı
    ölçüde gereklidir — hangi fazla/eksik alanın geldiği metinden okunur."""
    ham = json.dumps({"sade_ozet": True, "uydurma": []}, ensure_ascii=False)
    h = sd.ayristir(ham)
    assert h.kaynak == "llm_dustu" and h.cevap_bas == ham, (
        f"alanları tutmayan JSON için cevap başı yok: {h!r}")


def test_MEKANIK_HUKUMDE_CEVAP_BASI_NONE_VE_LLM_CAGRILMAZ(sd, tmp_path, sandbox_state):
    """Mekanik dalda cevap DİYE BİR ŞEY yoktur: LLM hiç çağrılmadı, o yüzden `None` (ölçülemedi)
    doğru değerdir — `""` yazmak "modeli sordum, susmuş" demek olurdu."""
    kuyruk = _Kuyruk(_temiz_cevap())
    h = sd.denetle(_profil_evi(tmp_path), "boş metin", ["MECHANISM_STALE"], cagir=kuyruk)
    assert h.kaynak == "mekanik" and h.cevap_bas is None, f"mekanik hükümde cevap başı: {h!r}"
    assert kuyruk.n == 0, "mekanik ihlal varken denetçi çağrıldı"


def test_CAGRI_DUSTUGUNDE_CEVAP_BASI_NONE(sd, tmp_path, sandbox_state):
    """`llm_dustu` hükümlerinin HEPSİ ayrıştırma kaynaklı değildir. Çağrı patladığında cevap HİÇ
    GELMEDİ — `""` yazmak "boş cevap aldık" yanlış teşhisini deftere yazardı."""
    def _patla(_istem):
        raise RuntimeError("upstream 502")

    h = sd.denetle(_profil_evi(tmp_path), "bir metin", [], cagir=_patla)
    assert h.kaynak == "llm_dustu" and h.cevap_bas is None, f"düşen çağrıda cevap başı: {h!r}"


def test_SOUL_OKUNAMAZSA_CEVAP_BASI_NONE(sd, tmp_path, sandbox_state):
    """Aynı sınıfın ikinci yarısı: SOUL bloğu yoksa denetçi HİÇ çağrılmaz."""
    bos_ev = tmp_path / "sef"
    bos_ev.mkdir()
    h = sd.denetle(bos_ev, "bir metin", [], cagir=_Kuyruk(_temiz_cevap()))
    assert h.kaynak == "llm_dustu" and h.cevap_bas is None, f"SOUL yokken cevap başı: {h!r}"


# ================================================================================================
# 2) OLAY KAYDI — `model` + `cevap_bas` YALNIZ OLAYA, DAMGAYA DEĞİL
# ================================================================================================

def _gecir_dustu(sd, tmp_path, monkeypatch, cevap, **kw):
    """Şema dışı bir denetçi cevabıyla TEK bir `gecir` koşumu; obs yakalayıcıyı döndürür."""
    yakala = _ObsYakala()
    monkeypatch.setattr(sd.obs, "log", yakala)
    g = sd.gecir(profil_evi=_profil_evi(tmp_path), ilk_metin="- bugün bir kalem var",
                 ilk_istem="### kaynak\n", veri_terimleri=[], cagir=_Kuyruk(cevap),
                 bot="sef", **kw)
    return g, yakala


def test_OLAYA_MODEL_VE_CEVAP_BASI_GIDER(sd, tmp_path, monkeypatch, sandbox_state):
    """Canlıdaki kayıt bu iki alanı taşımıyordu ve teşhis tam bu yüzden yapılamadı."""
    g, yakala = _gecir_dustu(sd, tmp_path, monkeypatch, "SESSIZ",
                             model_kimligi="custom:kapi/sahte-model:free")
    assert g.hukum.kaynak == "llm_dustu", f"kurulum yanlış, hüküm düşmedi: {g.hukum!r}"
    assert yakala.alan(sd.OLAY, "model") == "custom:kapi/sahte-model:free", (
        f"olayda model kimliği yok: {yakala.cagrilar!r}")
    assert yakala.alan(sd.OLAY, "cevap_bas") == "SESSIZ", (
        f"olayda cevap başı yok: {yakala.cagrilar!r}")


def test_MODEL_KIMLIGI_GECILMEZSE_OLAYDA_NONE(sd, tmp_path, monkeypatch, sandbox_state):
    """GERİYE UYUM: `bekci`/`karne` çağıranları bu turda DEĞİŞMEDİ ve kwarg'ı geçmiyor. Alan
    `None` olmalı — 'ölçülmedi'; boş dizge ya da alanın hiç olmaması ikisi de yanlış olurdu."""
    _, yakala = _gecir_dustu(sd, tmp_path, monkeypatch, "SESSIZ")
    # ALAN VARLIĞI + DEĞERİ BİRLİKTE: yalnız `.get(...) is None` sorulsaydı çivi alanın HİÇ
    # YAZILMADIĞI (yani bu turdan ÖNCEKİ) hâlde de yeşil kalırdı — ölçtüğünü sanan bir çivi.
    alanlar = dict(yakala.cagrilar[0][1])
    assert "model" in alanlar, f"olayda `model` alanı HİÇ yok: {sorted(alanlar)}"
    assert alanlar["model"] is None, f"kwarg'sız koşumda model: {alanlar['model']!r}"


def test_OLAYDAKI_CEVAP_BASI_SIR_SUZGECINDEN_GECER(sd, tmp_path, monkeypatch, sandbox_state):
    """MODEL ÇIKTISI DA BİR VERİ ÇIKIŞIDIR. Denetçinin düz-metin cevabı bir istisna dizgesi
    taşıyabilir (`?apikey=…`); defter süzgeçsizse sır `events.jsonl`e YAZILIR ve orada kalır."""
    from meridian import secrets as _sirlar
    monkeypatch.setattr(_sirlar, "get", lambda ad, *a, **k: SAHTE_SIR
                        if ad == SAHTE_SIR_ADI else None)
    cevap = f"HTTPStatusError: https://ornek/v1?apikey={SAHTE_SIR} 401"
    _, yakala = _gecir_dustu(sd, tmp_path, monkeypatch, cevap)
    bas = yakala.alan(sd.OLAY, "cevap_bas")
    assert SAHTE_SIR not in str(bas), f"SIR DEĞERİ deftere yazıldı: {bas!r}"
    assert "***" in str(bas), f"süzgeç hiç koşmadı (maske yok): {bas!r}"


def test_YENI_ALANLAR_DAMGAYA_GIRMEZ(sd, tmp_path, monkeypatch, sandbox_state):
    """O4 disiplini (v385 emsali): `Gecis.kayit()` damgaya da akar ve damganın okuyucusu bu iki
    alanı bilmez. Olay defteri ile damga AYNI sözlük değildir ve olmamalıdır."""
    g, _ = _gecir_dustu(sd, tmp_path, monkeypatch, "SESSIZ", model_kimligi="a/b")
    kayit = g.kayit("sef")
    assert "model" not in kayit and "cevap_bas" not in kayit, (
        f"okunmayacak alan damgaya yazıldı: {sorted(kayit)}")


# ================================================================================================
# 3) MODEL KİMLİĞİ — PROFİLDEN ÖLÇÜLÜR, UYDURULMAZ
# ================================================================================================

def test_PROFIL_MODEL_KIMLIGI_CONFIGDEN_OKUNUR(tmp_path, monkeypatch, sandbox_state, request):
    """Kimlik `provider/model` biçiminde BİRLEŞTİRİLİR: yalnız model adı yazılsaydı kapı
    değiştiğinde (openrouter → custom:kapi) defterdeki kimlik AYNI kalır, oysa çağrının gittiği
    yer değişmiş olurdu."""
    m, ev = _sef_kur(tmp_path, monkeypatch, request)
    (ev / "config.yaml").write_text(
        "model:\n  provider: custom:kapi\n  default: saglayici/model-x:free\n  max_tokens: 8000\n",
        encoding="utf-8")
    assert m._profil_model_kimligi(ev) == "custom:kapi/saglayici/model-x:free", (
        f"kimlik yanlış: {m._profil_model_kimligi(ev)!r}")


def test_PROFIL_MODEL_KIMLIGI_OKUNAMAZSA_NONE_VE_OLAY(tmp_path, monkeypatch, sandbox_state,
                                                      request):
    """Yasa 4: okunamayan kimlik SESSİZCE yutulmaz. `None` + ADIYLA olay — tahmin edilmiş bir
    model adı, teşhisi yanlış yöne çevirirdi (uydurma yasağı)."""
    m, ev = _sef_kur(tmp_path, monkeypatch, request)
    yakala = _ObsYakala()
    monkeypatch.setattr(m.obs, "log", yakala)
    assert m._profil_model_kimligi(ev) is None, "config.yaml YOKKEN kimlik uyduruldu"
    assert yakala.var_mi("sef_brifingi_profil_modeli_olculemedi"), (
        f"ölçülemeyen kimlik sessizce yutuldu: {yakala.cagrilar!r}")
    assert yakala.alan("sef_brifingi_profil_modeli_olculemedi", "neden"), "olayda `neden` yok"


def test_GERCEK_SEF_PROFILI_KIMLIK_VERIR(tmp_path, monkeypatch, sandbox_state, request):
    """AYRIŞMA ÇİVİSİ — alan adı kopyalanmaz, GERÇEK dosyadan okunur. Profil bir gün
    `model.default` yerine başka bir alan kullanırsa kimlik canlıda sessizce `None` olurdu;
    bu çivi o günü kırmızı yapar."""
    m, _ = _sef_kur(tmp_path, monkeypatch, request)
    kimlik = m._profil_model_kimligi(GERCEK_SEF_PROFILI)
    assert isinstance(kimlik, str) and "/" in kimlik, (
        f"gerçek profil kimliği okunamadı (alan adı ayrıştı mı?): {kimlik!r}")


def test_SEF_KURAL_GECISI_MODELI_OLCEREK_GECIRIR(tmp_path, monkeypatch, sandbox_state, request):
    """Bağlama çivisi: `sef` yolu kimliği GERÇEKTEN geçiriyor mu. Yardımcı doğru çalışsa bile
    `gecir`e bağlanmadığı sürece defterde hiçbir şey değişmez."""
    m, ev = _sef_kur(tmp_path, monkeypatch, request)
    (ev / "config.yaml").write_text(
        "model:\n  provider: custom:kapi\n  default: baglama-modeli\n", encoding="utf-8")
    yakala = _ObsYakala()
    monkeypatch.setattr(m.obs, "log", yakala)
    monkeypatch.setattr(m, "_profili_cagir",
                        _Kuyruk("- MECHANISM_STALE 5 kez: danışma katmanı ölü", "SESSIZ"))
    m.sirala(m.topla())
    olay_adi = importlib.import_module("ops.soul_denetimi").OLAY
    assert yakala.alan(olay_adi, "model") == "custom:kapi/baglama-modeli", (
        f"sef yolu model kimliğini geçirmedi: {yakala.cagrilar!r}")
    assert yakala.alan(olay_adi, "cevap_bas") == "SESSIZ", (
        f"sef yolu cevap başını geçirmedi: {yakala.cagrilar!r}")


# ================================================================================================
# 4) YASA 6 — YENİ ALANLARIN OKUYUCUSU
# ================================================================================================

def test_DURUM_SATIRI_SON_OLAYIN_MODEL_VE_CEVAP_BASINI_BASAR(tmp_path, monkeypatch,
                                                             sandbox_state, request):
    """Yalnız `events.jsonl`e yazmak, operatörün hiç bakmadığı bir yere yazmaktır. Durum satırı
    HER koşumda (kuru koşum dâhil) basılır ve bu turun ürettiği iki alanın OKUYUCUSUDUR."""
    m, _ = _sef_kur(tmp_path, monkeypatch, request)
    sd_ = importlib.import_module("ops.soul_denetimi")
    m.obs.log(sd_.OLAY, bot="sef", hukum="denetlenemedi", kaynak="llm_dustu",
              model="custom:kapi/olculen-model", cevap_bas="SESSIZ bugun bir sey yok")
    satir = m._durum_satiri(m.topla())
    assert "custom:kapi/olculen-model" in satir, f"model OKUNMUYOR: {satir!r}"
    assert "SESSIZ bugun bir sey yok" in satir, f"cevap başı OKUNMUYOR: {satir!r}"


def test_DURUM_SATIRI_OLCULEN_BOSU_OLCULEMEYENDEN_AYIRIR(tmp_path, monkeypatch, sandbox_state,
                                                         request):
    """Okuyucu tarafında da `""` ≠ `None`. Satır ikisini AYNI yazsaydı, alanın taşıdığı ayrım
    tam okunduğu yerde kaybolurdu — Yasa 6'nın "okundu" iddiası sözde kalırdı."""
    m, _ = _sef_kur(tmp_path, monkeypatch, request)
    sd_ = importlib.import_module("ops.soul_denetimi")
    m.obs.log(sd_.OLAY, bot="sef", kaynak="llm_dustu", model=None, cevap_bas="")
    bos_satir = m._durum_satiri(m.topla())
    m.obs.log(sd_.OLAY, bot="sef", kaynak="llm_dustu", model=None, cevap_bas=None)
    yok_satir = m._durum_satiri(m.topla())
    assert bos_satir != yok_satir, (
        f"ölçülen boş cevap ile ölçülemeyen cevap AYNI basıldı: {bos_satir!r}")
    assert "BOŞ" in bos_satir, f"ölçülen boş cevap adıyla basılmadı: {bos_satir!r}"
    assert "ÖLÇÜLEMEDİ" in yok_satir, f"ölçülemeyen cevap adıyla basılmadı: {yok_satir!r}"


def test_DURUM_SATIRI_KARDES_BOTUN_KUNYESINI_GOSTERMEZ(tmp_path, monkeypatch, sandbox_state,
                                                       request):
    """Defter ÜÇ botun ORTAK yeridir ve üçü de AYNI olay adını yazar. Süzgeçsiz bir okuma
    `@karne`nin model künyesini `@sef`in durum satırında gösterirdi — yanlış modele yüklenen bir
    kök neden, teşhisi hiç yapmamaktan beterdir (operatör 'ölçüldü' sanır)."""
    m, _ = _sef_kur(tmp_path, monkeypatch, request)
    sd_ = importlib.import_module("ops.soul_denetimi")
    m.obs.log(sd_.OLAY, bot="sef", kaynak="llm_dustu", model="sef/dogru-model", cevap_bas="x")
    m.obs.log(sd_.OLAY, bot="karne", kaynak="llm_dustu", model="karne/yanlis-model",
              cevap_bas="y")
    satir = m._durum_satiri(m.topla())
    assert "sef/dogru-model" in satir, f"kendi künyesi okunmadı: {satir!r}"
    assert "karne/yanlis-model" not in satir, f"KARDEŞ BOTUN künyesi basıldı: {satir!r}"


def test_DURUM_SATIRI_OLAY_YOKKEN_DE_BASILIR(tmp_path, monkeypatch, sandbox_state, request):
    """Okuyucunun kendisi teslimatı düşüremez: defter boşken satır patlamaz, YOKLUĞU söyler."""
    m, _ = _sef_kur(tmp_path, monkeypatch, request)
    satir = m._durum_satiri(m.topla())
    assert "teslim edilecek kaynak" in satir, f"durum satırı bozuldu: {satir!r}"
    assert "denetçi teşhisi" in satir, f"teşhis okuyucusu satırdan düştü: {satir!r}"


def test_TESLIM_SONRASI_OLAY_YENI_ALANLARI_TASIR(tmp_path, monkeypatch, sandbox_state, request):
    """UÇTAN UCA: sapsız hiçbir yol yok — gerçek `main(['--uygula'])` koşumu defterde iki alanı
    da bırakır. Saplarla ölçülen bir zincirin uçları bağlı olmayabilir."""
    m, ev = _sef_kur(tmp_path, monkeypatch, request)
    (ev / "config.yaml").write_text(
        "model:\n  provider: custom:kapi\n  default: uctan-uca-model\n", encoding="utf-8")
    monkeypatch.setattr(m, "_profili_cagir",
                        _Kuyruk("- MECHANISM_STALE 5 kez: danışma katmanı ölü", "duz metin cevap"))
    monkeypatch.setattr(m.notify, "configured", lambda: True)
    monkeypatch.setattr(m.notify, "send", lambda t: True)
    assert m.main(["--uygula"]) == 0, "teslimat düştü"
    olaylar = _olaylar()
    assert olaylar, "kural denetimi olayı hiç yazılmadı"
    assert olaylar[-1].get("model") == "custom:kapi/uctan-uca-model", f"{olaylar[-1]!r}"
    assert olaylar[-1].get("cevap_bas") == "duz metin cevap", f"{olaylar[-1]!r}"
    assert "model" not in m._son_kural_denetimi(), "yeni alan damgaya sızdı"
