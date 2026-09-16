"""v513 · HAM düşüş dalları kendi nedenlerini MESAJDA söyler; teslim olayı dalı TAŞIR — TSK-201.

NUMARA KİMLİKTİR: `v513` Rol-1 tarafından REZERVE EDİLDİ (2026-09-17). Bu çalışma kopyasında ne
dosya adı ne metin olarak geçiyordu (ölçüldü).

ÖLÇÜLEN SORUN (Rol-1 ölçümü, bu turda YENİDEN ölçülmedi): üç botun sıralama/sunum yolunda kural
denetimine HİÇ varmadan HAM teslime düşen dallar var. Hiçbiri MODEL metni teslim etmez — giden şey
betiğin deterministik yazdığı liste/karnedir; kural denetimi model metnini denetler, yani bu
dallarda DENETİM ÇAĞIRMAK YANLIŞ HEDEFTİR (bu dosya o yüzden denetim çağrısını ÖLÇMEZ, beyanı ölçer).
Asıl sorun operatörün MESAJDA farkı görememesiydi: "ham + 2/2 ihlal" gövdesi `ℹ kural denetimi: …`
taşıyor, "ham + yakın ıska" HİÇBİR ŞEY taşımıyordu — ayırt edici tek işaret bir satırın YOKLUĞUYDU,
ve yokluk okunamaz. İkinci yarısı defterdi: `<bot>_brifingi_teslim` hangi daldan gelindiğini
taşımıyordu; dal yalnız AYNI dakikadaki ayrı dal olayıyla EŞLEŞTİRİLEREK bulunabiliyordu.

ÇİVİLER (brief TSK-201):
  K1 — her ham dal, beyan satırını operatöre GİDEN gövdeye koyar (dal başına ayrı koşum, uçtan uca
       `main --uygula`; dalın GERÇEKTEN ateşlendiği kendi olayıyla AYRICA doğrulanır — yanlış dala
       düşüp yeşil kalmasın).
  K2 — beyan dalın NEDENİNİ taşır ve dallar birbirinden ayırt edilir.
  K3 — politika kapıları "arıza" demez; arıza dalları der (vakum-yeşile karşı pozitif kontrol).
  K4 — `sessizlik_tavani_asildi`: mevcut ZORLA TESLİM cümlesi KORUNUR, çift/çelişkili cümle yok.
  K5 — teslim olayı `dal` alanı taşır; denetim yolundan gelen teslimde değer ham dallardan AYRIŞIR.
  K6 — üç bot aynı davranışı TEK KAYNAKTAN alır (kaynak taraması + sarmalayıcı eşitliği).

BEKLENEN KÜMELER BU DOSYADA LİTERALDİR ve bu BİLİNÇLİDİR: dal listesi ve sınıflandırma Rol-1'in
KARARIDIR (brief tablosu) — üretimden türetilseydi, üretimdeki bir sınıf kayması çiviyi de
kaydırır ve K3 hiçbir şey ölçmezdi. Beyan METNİ ise üretimden okunur (kopyalanmaz): metin bir
cila, sınıf bir sözleşmedir.

SANDBOX HER UÇTAN UCA ÇİVİDE: `main` `obs.log` yazar ve damgaya dokunur.
"""
from __future__ import annotations

import ast
import importlib
import pathlib

import pytest

from tests.test_soul_denetimi_v385 import (_bot_kur, _ihlalli_cevap, _Kuyruk, _sef_kur,
                                           _temiz_cevap)

KOK = pathlib.Path(__file__).resolve().parent.parent

#: Bot başına ham düşüş dalları — Rol-1 kararı (brief TSK-201 tablosu + karne taraması).
DALLAR = {
    "sef": ("llm_dustu", "llm_bos", "cevap_makul_degil", "sessizlik_jetonu_yakin_iska",
            "sessiz_hukmu_gecersiz", "sessizlik_tavani_asildi"),
    "bekci": ("llm_dustu", "llm_bos", "cevap_makul_degil", "sessizlik_jetonu_yakin_iska",
              "sessiz_hukmu_gecersiz", "sessizlik_tavani_asildi"),
    # `hukum_yok`: brief'in "ölçümde OKUNMAYAN" karne dönüşü (`sun` başındaki `not ham["hukumler"]`).
    "karne": ("llm_dustu", "llm_bos", "cevap_makul_degil", "sessizlik_jetonu_anomalisi",
              "hukum_yok"),
}

#: NORMAL AKIŞ (politika kapısı) — "arıza" DEMEZ. Geri kalan her dal ARIZA sınıfıdır.
POLITIKA_DALLARI = frozenset({"sessiz_hukmu_gecersiz", "sessizlik_tavani_asildi", "hukum_yok"})

#: Kendi `obs.log` olayı OLMAYAN dal: model hiç çağrılmaz, arıza zorunlu başta ⚠ ile zaten basılır.
OLAYSIZ_DALLAR = frozenset({"hukum_yok"})

#: K2'nin anlam çapası: her dalın nedeninde geçmesi GEREKEN sözcük. Yalnız "birbirinden farklı"
#: demek, iki nedenin YER DEĞİŞTİRMESİNİ yakalamazdı.
NEDEN_ANAHTARI = {
    "llm_dustu": "düştü",
    "llm_bos": "boş",
    "cevap_makul_degil": "makul",
    "sessizlik_jetonu_yakin_iska": "tam değil",
    "sessizlik_jetonu_anomalisi": "susma yetkisi",
    "sessiz_hukmu_gecersiz": "ölçülemeyen",
    "sessizlik_tavani_asildi": "tavan",
    "hukum_yok": "hüküm yok",
}

SIRALAMA_FN = {"sef": "sirala", "bekci": "sirala", "karne": "sun"}
#: Teslim olayında sıralama kaynağının alan adı — karne'de `sunum` (üretimin kendi adı).
KAYNAK_ALANI = {"sef": "siralama", "bekci": "siralama", "karne": "sunum"}

#: Mevcut zorla-teslim cümlesinin iki botta ORTAK çekirdeği (K4: korunur).
ZORLA_CEKIRDEGI = "Bu mesaj bir öncelik yargısı DEĞİL, sıralanmamış"

_TR_KATLA = str.maketrans({"İ": "I", "ı": "I", "i": "I"})


def _katla(s: str) -> str:
    return s.translate(_TR_KATLA).upper()


def _soul():
    return importlib.import_module("ops.soul_denetimi")


# ================================================================================================
# KURULUM
# ================================================================================================

def _kur(bot, tmp_path, monkeypatch, request):
    """Botu sahte profil evine bağlar; kaynakları TESLİM EDİLECEK bir şey taşıyacak biçimde saplar.
    Kurulum komşu çivi dosyalarından İTHAL edilir (v385 emsali) — ikinci bir kopya eskirdi."""
    if bot == "sef":
        m, _ = _sef_kur(tmp_path, monkeypatch, request)
    else:
        m, _ = _bot_kur(tmp_path, monkeypatch, request, bot)
        if bot == "bekci":
            from tests import test_bekci_brifingi_v332 as v332
            v332._zaman_kur(monkeypatch, m)
            v332._tarama_kur(monkeypatch, m, takili=[v332._duvar()])
        else:
            from tests import test_karne_brifingi_v338 as v338
            v338._zaman_kur(monkeypatch, m)
            v338._hesap_kur(monkeypatch, m)
    # WORKTREE PYTHONPATH TUZAĞI: modül BU ağaçtan yüklenmediyse çivi başka bir kodu ölçer.
    assert pathlib.Path(m.__file__).resolve().is_relative_to(KOK), (
        f"modül bu ağaçtan yüklenmedi: {m.__file__} (kök {KOK})")
    return m


def _patlat(*_a, **_kw):
    raise RuntimeError("sahte düşüş (v513)")


def _dali_kur(bot, dal, m, monkeypatch):
    """Dalı ÜRETİMDEKİ tetikleyicisiyle kurar. Model cevabı sahte; dal kararı üretimin."""
    cevap = {"llm_bos": "  \n  ",
             "cevap_makul_degil": "... !!! ---",
             "sessizlik_jetonu_yakin_iska": "SESSIZ (bugün bir şey yok)",
             "sessizlik_jetonu_anomalisi": "SESSIZ",
             "sessiz_hukmu_gecersiz": "SESSIZ",
             "sessizlik_tavani_asildi": "SESSIZ"}.get(dal)
    if dal == "llm_dustu":
        monkeypatch.setattr(m, "_profili_cagir", _patlat)
    elif dal == "hukum_yok":
        # Model ÇAĞRILMAMALI: boş kuyruk ilk çağrıda açık bir AssertionError ile patlar.
        monkeypatch.setattr(m, "_hesap", _patlat)
        monkeypatch.setattr(m, "_profili_cagir", _Kuyruk())
    else:
        monkeypatch.setattr(m, "_profili_cagir", _Kuyruk(cevap))
    if dal == "sessiz_hukmu_gecersiz":
        if bot == "sef":
            monkeypatch.setattr(m, "_alarm_ozeti", _patlat)
        else:
            monkeypatch.setattr(m, "_tarama", _patlat)
    if dal == "sessizlik_tavani_asildi":
        for _ in range(m.ARDISIK_SESSIZ_TAVANI - 1):
            m._sessiz_sayaci_artir()


def _uygula(bot, m, monkeypatch):
    """GERÇEK teslim yolu: `main --uygula` → (gönderilen gövde, teslim olayı, olay adları)."""
    from meridian import store
    gonderilen: list = []
    monkeypatch.setattr(m.notify, "configured", lambda: True)
    monkeypatch.setattr(m.notify, "send", lambda t: (gonderilen.append(t), True)[1])
    assert m.main(["--uygula"]) == 0
    assert len(gonderilen) == 1, f"tek mesaj beklenirdi: {gonderilen!r}"
    olaylar = list(store.read_jsonl("events.jsonl"))
    teslim = [e for e in olaylar if e.get("event") == f"{bot}_brifingi_teslim"]
    assert len(teslim) == 1, f"tek teslim olayı beklenirdi: {teslim!r}"
    return gonderilen[0], teslim[0], [str(e.get("event")) for e in olaylar]


def _dal_kosumu(bot, dal, tmp_path, monkeypatch, request):
    m = _kur(bot, tmp_path, monkeypatch, request)
    _dali_kur(bot, dal, m, monkeypatch)
    govde, teslim, olaylar = _uygula(bot, m, monkeypatch)
    # POZİTİF KONTROL — dal GERÇEKTEN ateşlendi mi? Aksi hâlde çivi başka bir dalı ölçerek yeşil
    # kalabilirdi (bir turda dört çivi tam bu sebeple yanlış yeşildi).
    if dal not in OLAYSIZ_DALLAR:
        assert f"{bot}_brifingi_{dal}" in olaylar, (
            f"@{bot} `{dal}` dalına DÜŞMEDİ — kurulum yanlış dalı ölçüyor: {olaylar}")
    assert teslim.get(KAYNAK_ALANI[bot]) == "ham", f"ham teslim beklenirdi: {teslim!r}"
    return m, govde, teslim


def _beyan_satirlari(m, govde: str) -> list[str]:
    isaret = m.soul_denetimi.DENETIM_UYGULANMADI
    return [s for s in govde.splitlines() if isaret in s]


_VAKALAR = [(bot, dal) for bot, dallar in DALLAR.items() for dal in dallar]


# ================================================================================================
# K1 — her dal beyanı operatöre giden gövdeye koyar
# ================================================================================================

@pytest.mark.parametrize("bot,dal", _VAKALAR)
def test_K1_HAM_DAL_BEYANI_GOVDEYE_GIRER(bot, dal, tmp_path, monkeypatch, sandbox_state, request):
    """Beyan ZORUNLU parça kanalından (`kural_beyani`) girer — yeni bir yüzey açılmadı. Metin
    üretimin tek kaynağından okunur; gövdede TAM satır olarak ve TEK kez durmalıdır."""
    m, govde, _ = _dal_kosumu(bot, dal, tmp_path, monkeypatch, request)
    beklenen = m.soul_denetimi.ham_dal_beyani(dal, katman=m.HAM_KATMAN, urun=m.HAM_URUN)
    satirlar = _beyan_satirlari(m, govde)
    assert satirlar == [f"ℹ {beklenen}"], (
        f"@{bot} `{dal}`: beyan satırı gövdede yok ya da çift — {satirlar!r}\n{govde}")


# ================================================================================================
# K2 — beyan dalın nedenini taşır, dallar ayırt edilir
# ================================================================================================

@pytest.mark.parametrize("bot", sorted(DALLAR))
def test_K2_BEYAN_DALIN_NEDENINI_TASIR_VE_DALLAR_AYRISIR(bot):
    m = importlib.import_module(f"ops.{bot}_brifingi")
    sd = m.soul_denetimi
    beyanlar = {d: sd.ham_dal_beyani(d, katman=m.HAM_KATMAN, urun=m.HAM_URUN) for d in DALLAR[bot]}
    assert len(set(beyanlar.values())) == len(beyanlar), (
        f"@{bot}: iki dal AYNI beyanı basıyor — operatör farkı göremez: {beyanlar!r}")
    for dal, beyan in beyanlar.items():
        assert dal in sd.HAM_DALLARI, f"`{dal}` beyan tablosunda yok (TANIMSIZ yedeğine düşer)"
        assert sd.HAM_DALLARI[dal].neden in beyan, f"`{dal}` nedeni beyanda yok: {beyan!r}"
        assert NEDEN_ANAHTARI[dal] in beyan, (
            f"`{dal}` beyanı dalın NEDENİNİ söylemiyor ('{NEDEN_ANAHTARI[dal]}' yok): {beyan!r}")
        assert sd.DENETIM_UYGULANMADI in beyan, f"`{dal}` denetimin yokluğunu söylemiyor: {beyan!r}"


def test_K2_TABLO_DISI_DAL_TESLIMATI_DUSURMEZ():
    """Tanımsız bir dal adı İSTİSNA ATMAZ (atsaydı `sirala` içinden `main`e yürür ve o günkü mesaj
    hiç gitmezdi) ve bir neden UYDURMAZ — yokluğu ADIYLA söyler."""
    sd = _soul()
    beyan = sd.ham_dal_beyani("boyle_bir_dal_yok", katman="sıralama", urun="ham liste")
    assert "TANIMSIZ" in beyan and "boyle_bir_dal_yok" in beyan, beyan


# ================================================================================================
# K3 — politika kapıları "arıza" demez
# ================================================================================================

@pytest.mark.parametrize("bot", sorted(DALLAR))
def test_K3_POLITIKA_KAPISI_ARIZA_DEMEZ(bot):
    m = importlib.import_module(f"ops.{bot}_brifingi")
    sd = m.soul_denetimi
    for dal in DALLAR[bot]:
        beyan = _katla(sd.ham_dal_beyani(dal, katman=m.HAM_KATMAN, urun=m.HAM_URUN))
        if dal in POLITIKA_DALLARI:
            assert "ARIZA" not in beyan, f"@{bot} `{dal}` normal akış ama 'arıza' diyor: {beyan!r}"
            assert "POLITIKA" in beyan, f"@{bot} `{dal}` politika dilini kullanmıyor: {beyan!r}"
        else:
            # POZİTİF KONTROL: sözcük arıza dallarında VAR — yoksa üstteki `not in` vakum-yeşildi.
            assert "ARIZA" in beyan, f"@{bot} `{dal}` arıza dalı ama sınıfını söylemiyor: {beyan!r}"


# ================================================================================================
# K4 — zorla teslim cümlesi korunur, çift/çelişkili cümle yok
# ================================================================================================

@pytest.mark.parametrize("bot", ["sef", "bekci"])
def test_K4_TAVAN_DALINDA_ZORLA_CUMLESI_KORUNUR_TEK_CUMLE(bot, tmp_path, monkeypatch,
                                                          sandbox_state, request):
    """İki satır birden basılır ama TEKRARLAMAZLAR: ZORLA TESLİM satırı "sıralanmamış" ve "neden"i
    zaten söylüyor; beyan yalnız EKSİK olanı (denetimin yokluğu) ekler ve yukarıyı gösterir."""
    m, govde, _ = _dal_kosumu(bot, "sessizlik_tavani_asildi", tmp_path, monkeypatch, request)
    zorla = [s for s in govde.splitlines() if s.startswith("⚠ ZORLA TESLİM")]
    assert len(zorla) == 1 and ZORLA_CEKIRDEGI in zorla[0], (
        f"@{bot}: mevcut ZORLA TESLİM cümlesi korunmadı: {zorla!r}\n{govde}")
    beyan = _beyan_satirlari(m, govde)
    assert len(beyan) == 1, f"@{bot}: beyan tek satır olmalı: {beyan!r}"
    assert govde.index(zorla[0]) < govde.index(beyan[0]), "beyan 'yukarıda' diyor ama üstte duruyor"
    assert govde.count("ZORLA TESLİM") == 1, f"@{bot}: ZORLA TESLİM iki kez basıldı:\n{govde}"
    assert govde.count("sıralanmamış") == 1, (
        f"@{bot}: 'sıralanmamış' iki kez — beyan zorla cümlesini TEKRARLIYOR:\n{govde}")
    assert m.HAM_URUN not in beyan[0], f"@{bot}: beyan ürün cümlesini tekrarlıyor: {beyan[0]!r}"


# ================================================================================================
# K5 — teslim olayı dalı taşır; denetim yolu ayrışır
# ================================================================================================

@pytest.mark.parametrize("bot,dal", _VAKALAR)
def test_K5_TESLIM_OLAYI_DAL_ALANI_TASIR(bot, dal, tmp_path, monkeypatch, sandbox_state, request):
    _, _, teslim = _dal_kosumu(bot, dal, tmp_path, monkeypatch, request)
    assert "dal" in teslim, f"@{bot} teslim olayında `dal` ANAHTARI yok: {teslim!r}"
    assert teslim["dal"] == dal, f"@{bot} teslim olayı yanlış dalı taşıyor: {teslim!r}"


def _denetim_yolu_kur(bot, tmp_path, monkeypatch, request, *, ihlal: bool):
    m = _kur(bot, tmp_path, monkeypatch, request)
    ilk = ("Bu hafta çekilme tavanı aşıldı; getiri ve sharpe geçti." if bot == "karne"
           else "- MECHANISM_STALE 5 kez: danışma katmanı ölü, bugün bak")
    if ihlal:
        kuyruk = _Kuyruk(ilk, _ihlalli_cevap(), ilk + " yine", _ihlalli_cevap())
    else:
        kuyruk = _Kuyruk(ilk, _temiz_cevap())
    monkeypatch.setattr(m, "_profili_cagir", kuyruk)
    return m


@pytest.mark.parametrize("bot", sorted(DALLAR))
def test_K5_DENETIM_YOLU_DAL_DEGERI_HAM_DALLARDAN_AYRISIR(bot, tmp_path, monkeypatch,
                                                          sandbox_state, request):
    """Denetim yoluna varılan teslimde değer `DAL_KURAL_GECISI`dir: None ("ölçülmedi") DEĞİL, bir
    ham dal adı DEĞİL. Hükmün kendisi bu alanda değil, kural denetimi olayındadır."""
    m = _denetim_yolu_kur(bot, tmp_path, monkeypatch, request, ihlal=False)
    govde, teslim, _ = _uygula(bot, m, monkeypatch)
    sd = m.soul_denetimi
    assert sd.DAL_KURAL_GECISI and sd.DAL_KURAL_GECISI not in sd.HAM_DALLARI
    assert teslim.get("dal") == sd.DAL_KURAL_GECISI, f"@{bot} denetim yolu: {teslim!r}"
    assert teslim.get(KAYNAK_ALANI[bot]) == "llm", f"pozitif kontrol — model metni gitmeli: {teslim!r}"
    assert not _beyan_satirlari(m, govde), f"denetlenen metinde 'uygulanmadı' beyanı:\n{govde}"


@pytest.mark.parametrize("bot", sorted(DALLAR))
def test_K5_HAM_IHLAL_ILE_HAM_DAL_MESAJDA_VE_DEFTERDE_AYRISIR(bot, tmp_path, monkeypatch,
                                                              sandbox_state, request):
    """Brief'in çekirdek örneği: "ham + denetim ihlali" ile "ham + ham dal" artık hem METİNDE hem
    DEFTERDE ayrışır — beyanın YOKLUĞU ayırt edici işaret olmaktan çıkar."""
    m = _denetim_yolu_kur(bot, tmp_path, monkeypatch, request, ihlal=True)
    govde, teslim, _ = _uygula(bot, m, monkeypatch)
    sd = m.soul_denetimi
    assert teslim.get(KAYNAK_ALANI[bot]) == "ham", f"pozitif kontrol — 2/2 ihlal ham gider: {teslim!r}"
    assert teslim.get("dal") == sd.DAL_KURAL_GECISI, f"@{bot} ihlal yolu: {teslim!r}"
    assert "ℹ kural denetimi:" in govde, f"denetim beyanı gövdede yok:\n{govde}"
    assert not _beyan_satirlari(m, govde), f"denetlenmiş ham gövdede 'uygulanmadı' beyanı:\n{govde}"


# ================================================================================================
# K6 — üç bot, tek kaynak
# ================================================================================================

def _ham_donusu_mu(node: ast.Return) -> bool:
    """`return <metin>, "ham"` — metin `None` DEĞİLSE (None = teslimat yok, beyan gerekmez)."""
    v = node.value
    return (isinstance(v, ast.Tuple) and len(v.elts) == 2
            and isinstance(v.elts[1], ast.Constant) and v.elts[1].value == "ham"
            and not (isinstance(v.elts[0], ast.Constant) and v.elts[0].value is None))


def _govde_listeleri(fn: ast.FunctionDef):
    """Fonksiyonun HER deyim listesi, bir kez. `ast.walk` `ExceptHandler` düğümlerini de gezer,
    yani `except` gövdeleri `body` alanından gelir — ayrıca `handlers` gezilirse çift sayılırdı."""
    for n in ast.walk(fn):
        for alan in ("body", "orelse", "finalbody"):
            liste = getattr(n, alan, None)
            if isinstance(liste, list) and liste and isinstance(liste[0], ast.stmt):
                yield liste


def _cagri_adi(stmt) -> str | None:
    if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
        return ast.unparse(stmt.value.func)
    return None


@pytest.mark.parametrize("bot", sorted(DALLAR))
def test_K6_HER_HAM_DONUSU_BEYANLI_VE_OLAY_ADIYLA_ESLESIR(bot):
    """KAYNAK TARAMASI — yarın eklenen YEDİNCİ bir ham dönüş beyansız doğarsa burada öter. Dal adı
    kendi `obs.log` olayının sonekiyle AYNIDIR (eşleştirme anahtarı ayrışmasın)."""
    src = (KOK / "ops" / f"{bot}_brifingi.py").read_text(encoding="utf-8")
    agac = ast.parse(src)
    fn = next(n for n in agac.body
              if isinstance(n, ast.FunctionDef) and n.name == SIRALAMA_FN[bot])
    bulunan: list[str] = []
    kural_gecisi_donusu = 0
    for liste in _govde_listeleri(fn):
        for i, stmt in enumerate(liste):
            if not isinstance(stmt, ast.Return):
                continue
            onceki = liste[:i]
            if _ham_donusu_mu(stmt):
                dallar = [s.value.args[1].value for s in onceki if _cagri_adi(s) == "_ham_dali"]
                assert len(dallar) == 1, (
                    f"@{bot} satır {stmt.lineno}: ham dönüş `_ham_dali` beyanı taşımıyor")
                dal = dallar[0]
                bulunan.append(dal)
                if dal in OLAYSIZ_DALLAR:
                    continue
                olay = [s.value.args[0].value for s in onceki if _cagri_adi(s) == "obs.log"]
                assert olay == [f"{bot}_brifingi_{dal}"], (
                    f"@{bot} `{dal}`: dal adı olay adıyla eşleşmiyor: {olay!r}")
            elif (isinstance(stmt.value, ast.Call)
                  and ast.unparse(stmt.value.func) == "_kural_gecisi"):
                kural_gecisi_donusu += 1
                atamalar = [ast.unparse(s) for s in onceki if isinstance(s, ast.Assign)]
                assert "ham['dal'] = soul_denetimi.DAL_KURAL_GECISI" in atamalar, (
                    f"@{bot}: denetim yoluna giden dönüş dalı işaretlemiyor: {atamalar!r}")
    assert sorted(bulunan) == sorted(DALLAR[bot]), (
        f"@{bot}: beyanlı ham dal kümesi beklenenden farklı: {sorted(bulunan)}")
    assert kural_gecisi_donusu == 1, f"@{bot}: `_kural_gecisi` dönüşü {kural_gecisi_donusu}"


def test_K6_UC_BOT_AYNI_BEYANI_TEK_KAYNAKTAN_URETIR():
    """Her botun `_ham_dali` sarmalayıcısı ORTAK fonksiyona devreder: ortak dallarda üç beyan,
    bot adları (katman/ürün) çıkarıldığında BİREBİR aynıdır. Bir bot kendi metnini yazarsa öter."""
    ortak = set(DALLAR["sef"]) & set(DALLAR["bekci"]) & set(DALLAR["karne"])
    assert ortak, "ortak dal yok — çivi vakumda"
    sd = _soul()
    for dal in sorted(ortak):
        normal = {}
        for bot in sorted(DALLAR):
            m = importlib.import_module(f"ops.{bot}_brifingi")
            ham: dict = {}
            m._ham_dali(ham, dal)
            assert ham.get("dal") == dal, f"@{bot} `_ham_dali` dalı yazmadı: {ham!r}"
            assert ham.get("kural_beyani") == sd.ham_dal_beyani(
                dal, katman=m.HAM_KATMAN, urun=m.HAM_URUN), f"@{bot} kendi metnini yazıyor: {ham!r}"
            normal[bot] = ham["kural_beyani"].replace(m.HAM_URUN, "<ÜRÜN>").replace(
                m.HAM_KATMAN, "<KATMAN>")
        assert len(set(normal.values())) == 1, f"`{dal}` üç botta ayrışıyor: {normal!r}"
