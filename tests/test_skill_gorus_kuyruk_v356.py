"""EDG-2026-019 KILL#1 KÖK ÇÖZÜMÜ — ÜRETİM KADANSTAN ÇIKTI (v356, 2026-09-01).

ÖLÇÜLMÜŞ KUSUR. Kartın kill#1'i "görüş üretimi canlı döngü p95 süresini +%10'dan fazla artırırsa
katman KAPATILIR" der; canlı kayıt `p95_pay 6.57 > 0.10` (2026-08-21'den beri) ve katman
`config.SKILL_GORUS_URETIM_ACIK=False` mandalıyla kapatıldı. Kapatma HÜKÜMDÜ ama çözüm değildi:
kapalı katman kanıt biriktirmez, kanıt birikmeyince kartın yeniden açılışı için gereken ölçüm de
hiç koşamaz. Kök neden mandalda değil MİMARİDEYDİ — `topla()` + `rapor()` öğrenme kadansının
İÇİNDE senkron koşuyordu.

BU DOSYANIN ÇİVİLEDİĞİ ŞEY EŞİK DEĞİL MİMARİDİR (eşikler kartta donmuş, burada yalnız OKUNUR):
  A. kadans yolu ÜRETİM YÜZEYLERİNİ ÇAĞIRMAZ (sembol düzeyinde, geçişli),
  B. kadans yolu yalnız KUYRUK + DURUM defterine dokunur,
  C. bayrak kapalıyken kuyruk yolu da ÖLÜDÜR (+ pozitif kontrol),
  D. t-ÇİTİ: satırın damgası SNAPSHOT anıdır ve kesitte OLMAYAN veri üretime SIZAMAZ,
  E. üretim İDEMPOTENTtir; tavana çarpan kesit İŞARETLENMEZ,
  F. kuyruğun DIŞ okuyucusu vardır (YASA 6) — beyanla değil okuyucuyla,
  G. BEDEL: kuyruk yolunun süresi tam koşuyla KIYASLANARAK ölçülür (kazanç iddiası ölçülür).
"""
import ast
import json
import os
import pathlib
import subprocess
import sys
import time

import pytest

from meridian import api, codelaw, config, skill_gorus as sg, skills, store

REPO = pathlib.Path(__file__).resolve().parents[1]
BETIK = REPO / "ops" / "skill_gorus_uret.py"


# EDG-2026-019 KILL#1: katman canlıda KAPALI. Bu dosyanın çivileri MEKANİZMAYI ölçer; kapanış
# hükmünün kendi çivisi tests/test_e_partisi_v278.py'dedir. Bayrak SÜREÇ-YEREL açılır (monkeypatch),
# üretim varsayılanına DOKUNULMAZ — C bölümü bunu ayrıca ölçer.
@pytest.fixture(autouse=True)
def _uretim_test_icin_acik(monkeypatch):
    from meridian import config as _cfg
    monkeypatch.setattr(_cfg, "SKILL_GORUS_URETIM_ACIK", True)


@pytest.fixture
def kayit(sandbox_state, tmp_path, monkeypatch):
    """v218'in `kayit` fikstürünün küçük kardeşi: evren kaynaktan türesin, gerçek `skills/` sızmasın."""
    from meridian import analytics
    monkeypatch.setattr(analytics, "skill_attribution", lambda: {"skills": []})
    kok = tmp_path / "skills"
    for ad in ("vcp-screener", "theme-detector"):
        (kok / ad).mkdir(parents=True)
        (kok / ad / "SKILL.md").write_text(f"---\nname: {ad}\ndescription: {ad} amacı.\n---\n")
    monkeypatch.setattr(config, "SKILLS", kok)
    monkeypatch.setattr(skills, "_DESC_CACHE", None)
    store.write_json("skills_registry.json", {"skills": {
        "vcp-screener": {"category": "swing", "enabled": True, "mode": "active",
                         "pipeline": "P2_SCREEN"},
        "theme-detector": {"category": "research", "enabled": True, "mode": "active",
                           "pipeline": "P2_SCREEN"},
    }})
    yield sandbox_state
    skills._DESC_CACHE = None


def _cf(n: int = 40, *, ilk: int = 0, screener: str = "vcp-screener"):
    """Gerçek şemalı cf defteri (çözücülerin canlı yolu koşsun)."""
    rows = []
    for i in range(ilk, ilk + n):
        r = float(i) * 0.01
        rows.append({"id": f"CF-x-{i}", "date": f"2026-06-{i % 10 + 1:02d}", "ticker": "AAA",
                     "setup": "breakout_vcp", "score": float(i), "screener": screener,
                     "entered": True, "status": "closed", "exit_reason": "target",
                     "r_multiple": r, "mfe_r": r + 0.2})
    return rows


def _defterler(n: int = 40):
    store.write_jsonl("counterfactuals.jsonl", _cf(n))
    store.write_json("exit_efficiency.json", {"n": n, "avg_left_r": 0.2})


# =================================================================================================
# A — KADANS YOLU ÜRETİM YÜZEYLERİNİ ÇAĞIRMAZ (SEMBOL DÜZEYİ, GEÇİŞLİ)
# =================================================================================================
def _fonksiyonlar(yol: pathlib.Path) -> dict:
    tree = ast.parse(yol.read_text(encoding="utf-8"))
    return {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}


def _cagrilan(fn: ast.FunctionDef) -> set:
    out = set()
    for n in ast.walk(fn):
        if isinstance(n, ast.Call):
            f = n.func
            if isinstance(f, ast.Attribute):
                out.add(f.attr)
            elif isinstance(f, ast.Name):
                out.add(f.id)
    return out


def _gecisli(fnler: dict, kok: str) -> set:
    """`kok`tan ulaşılan TÜM çağrı adları — aynı modül içinde geçişli kapanış.

    NEDEN GEÇİŞLİ: "kadans `rapor` çağırmıyor" tek başına bir şey kanıtlamaz; çağırdığı yardımcı
    çağırıyorsa maliyet aynen kadanstadır. Ölçülen şey ÇAĞRI GRAFİĞİDİR, tek satır değil."""
    gorulen, yigin, hepsi = set(), [kok], set()
    while yigin:
        ad = yigin.pop()
        if ad in gorulen:
            continue
        gorulen.add(ad)
        if ad not in fnler:
            continue
        for c in _cagrilan(fnler[ad]):
            hepsi.add(c)
            if c in fnler:
                yigin.append(c)
    return hepsi


URETIM_YUZEYLERI = {"topla", "rapor", "kadans", "defter", "bootstrap_p", "bh_fdr",
                    "cozucu_siralayici", "cozucu_cikis", "_ci", "_girdi_bekcisi",
                    "_rank_ic_ayristir", "_gorusleri_tureti", "deftere_yaz"}


def test_A1_ogrenme_kadansi_URETIM_yuzeylerini_CAGIRMAZ():
    """Kök çözümün tek cümlesi: gece döngüsü artık görüş ÜRETMİYOR, kesit YAZIYOR."""
    fnler = _fonksiyonlar(REPO / "meridian" / "scheduler.py")
    adlar = _cagrilan(fnler["_learning_cadence"])
    assert "kuyruk_kadansi" in adlar, "kadans adımı kuyruk yoluna bağlanmamış"
    sizan = adlar & (URETIM_YUZEYLERI | {"kuyruktan_uret"})
    assert not sizan, f"öğrenme kadansı hâlâ üretim yüzeyi çağırıyor: {sorted(sizan)}"


def test_A2_kuyruk_kadansi_gecisli_olarak_da_URETIM_yapmaz():
    """A1'in derin hâli: kuyruk yolunun ULAŞTIĞI hiçbir sembol üretim/hüküm yüzeyi olmamalı."""
    fnler = _fonksiyonlar(REPO / "meridian" / "skill_gorus.py")
    ulasilan = _gecisli(fnler, "kuyruk_kadansi")
    sizan = ulasilan & URETIM_YUZEYLERI
    assert not sizan, (
        f"kuyruk yolu geçişli olarak üretim yüzeyine ulaşıyor: {sorted(sizan)} — kill#1'in "
        f"maliyeti kadansa geri sızmış olur")
    # POZİTİF KONTROL: aynı ölçüm TAM koşu için ÇALIŞMALI, yoksa ölçüt hiçbir şey ayırt etmiyordur.
    assert URETIM_YUZEYLERI & _gecisli(fnler, "kadans"), "ölçüt kör: tam koşuda da üretim görmüyor"


# =================================================================================================
# B — KADANS YOLU YALNIZ KUYRUK + DURUM DEFTERİNE DOKUNUR
# =================================================================================================
def test_B1_kuyruk_kadansi_yalnizca_iki_dosyaya_dokunur(kayit):
    _defterler()
    kok = pathlib.Path(kayit)
    dosyalar = lambda: {p.name for p in kok.rglob("*") if p.is_file() and p.suffix != ".lock"}
    once = dosyalar()
    reg_once = json.dumps(store.read_json("skills_registry.json", {}), sort_keys=True)
    sg.kuyruk_kadansi(apply=True, oncesi_ms=1000.0)
    assert dosyalar() - once == {sg.KUYRUK_DEFTERI, sg.DURUM_DEFTERI}, \
        "kadans adımı kendi iki defteri DIŞINDA bir dosyaya dokundu"
    assert store.read_jsonl(sg.GORUS_DEFTERI) == [], "kadans adımı GÖRÜŞ yazdı — üretim çıkmamış"
    assert json.dumps(store.read_json("skills_registry.json", {}), sort_keys=True) == reg_once


def test_B2_p95_olcumu_kuyruk_yolu_icin_AYRI_birikir(kayit):
    """Ölçüm düzeneği KALIR (iddia ölçülür) ama iki yolun payı tek halkada KARIŞMAZ."""
    _defterler()
    k = sg.kuyruk_kadansi(apply=True, oncesi_ms=1000.0)
    assert k["yol"] == sg.KUYRUK_YOLU and k["pay"] == pytest.approx(k["sure_ms"] / 1000.0, abs=1e-4)
    assert k["kill_p95"]["durum"] == "ÖLÇÜLÜYOR" and k["kill_p95"]["n_ornek"] == 1
    sg.kadans(apply=True, oncesi_ms=1000.0)          # TAM koşu aynı halkaya yazar...
    k2 = sg.kuyruk_kadansi(apply=True, oncesi_ms=1000.0)
    assert k2["kill_p95"]["n_ornek"] == 2, "tam koşunun örneği kuyruk p95'ine karışmış"
    assert k2["kill_p95"]["yol"] == sg.KUYRUK_YOLU
    yollar = {o.get("yol") for o in k2["ornekler"]}
    assert yollar == {sg.KUYRUK_YOLU, sg.KADANS_YOLU}, "örnekler yol künyesi taşımıyor"


def test_B3_sure_OLCULEMEDIGINDE_pay_SIFIR_SAYILMAZ(kayit):
    _defterler()
    k = sg.kuyruk_kadansi(apply=True, oncesi_ms=None)
    assert k["pay"] is None and k["kill_p95"]["durum"] == "ÖLÇÜLEMEDİ"
    assert "0 SAYILMAZ" in k["kill_p95"]["neden"]


# =================================================================================================
# C — BAYRAK KAPALIYKEN KUYRUK YOLU DA ÖLÜ (MUTASYON HEDEFİ #1)
# =================================================================================================
def test_C1_bayrak_KAPALIYKEN_kuyruk_yolu_OLU(kayit, monkeypatch):
    """Kapatma hükmü 'YAZIM durur' der ve kuyruk yazımı da yazımdır: bayrağı yalnız üretim
    tarafına uygulamak, kapalı bir katmanın her gece dosya büyütmesi olurdu (v278 kardeşi)."""
    _defterler()
    monkeypatch.setattr(sg, "_KAPATMA_OLAYI_BASILDI", False)
    monkeypatch.setattr(config, "SKILL_GORUS_URETIM_ACIK", False)
    k = sg.kuyruk_kadansi(apply=True, oncesi_ms=1000.0)
    assert k["kapali"] is True and k["uygulandi_mi"] is False and k["pay"] is None
    assert "EDG-2026-019" in k["neden"] and len(k["neden"]) >= 20
    u = sg.kuyruktan_uret(apply=True)
    assert u["kapali"] is True and u["yazilan"] == 0
    assert not (pathlib.Path(kayit) / sg.KUYRUK_DEFTERI).exists(), "kapalıyken kuyruk yazıldı"
    assert not (pathlib.Path(kayit) / sg.DURUM_DEFTERI).exists(), "kapalıyken durum yazıldı"
    olaylar = [e for e in store.read_jsonl("events.jsonl")
               if e.get("event") == "skill_gorus_katmani_kapatildi"]
    assert len(olaylar) == 1, f"kapanış sessiz ya da tekrarlı: {len(olaylar)}"


def test_C2_POZITIF_KONTROL_bayrak_acikken_kuyruk_GERCEKTEN_yazilir(kayit):
    """C1'i anlamlı kılan çivi: yol zaten hiçbir koşulda yazmıyor olabilirdi."""
    _defterler()
    k = sg.kuyruk_kadansi(apply=True, oncesi_ms=1000.0)
    assert k.get("kapali") is None and k["uygulandi_mi"] is True
    kuyruk = sg.kuyruk_oku()
    assert len(kuyruk) == 1 and kuyruk[0]["n_gozlem"] == 40
    assert kuyruk[0]["evren"] == ["vcp-screener"] and kuyruk[0]["islendi"] is False


def test_C3_kuru_kosu_kuyruga_YAZMAZ(kayit):
    _defterler()
    k = sg.kuyruk_kadansi(apply=False, oncesi_ms=1000.0)
    assert k["kuyruk"]["n_gozlem"] == 40 and k["uygulandi_mi"] is False
    assert not (pathlib.Path(kayit) / sg.KUYRUK_DEFTERI).exists()


def test_C4_KAPALIYKEN_de_kuru_kosu_OLCUM_araci_olarak_acik(kayit, monkeypatch):
    """K4 hizalaması: mandal `apply` biçiminde. Kapatılan şey YAZIMDIR, ÖLÇÜM DEĞİL — kartın
    yeniden açılışı için gereken ölçüm, kapının kendisi tarafından imkânsız kılınamaz (`topla`nın
    kapısıyla aynı hüküm, v278 9e)."""
    _defterler(n=7)
    monkeypatch.setattr(sg, "_KAPATMA_OLAYI_BASILDI", False)
    monkeypatch.setattr(config, "SKILL_GORUS_URETIM_ACIK", False)
    k = sg.kuyruk_kadansi(apply=False, oncesi_ms=1000.0)
    assert k.get("kapali") is None, "kuru koşu kapalı katmanda da ÖLÇMELİ"
    assert k["kuyruk"]["n_gozlem"] == 7 and k["uygulandi_mi"] is False
    assert not (pathlib.Path(kayit) / sg.KUYRUK_DEFTERI).exists()
    assert not (pathlib.Path(kayit) / sg.DURUM_DEFTERI).exists()


# =================================================================================================
# C5 — KUYRUK BİRİKİMİ SESSİZ KALMAZ (Ö1)
# =================================================================================================
def _kuyruk_doldur(n: int):
    """n işlenmemiş kesit — üretici hiç koşmamış bir hattın hâli."""
    store.write_jsonl(sg.KUYRUK_DEFTERI,
                      [{"ts": f"2026-08-{i + 1:02d}T22:00:00+00:00", "sema": sg.KUYRUK_SEMA,
                        "islendi": False, "evren": ["vcp-screener"], "n_gozlem": 0,
                        "gozlemler": [], "atlanan": {}} for i in range(n)])


def test_C5_kuyruk_BIRIKINCE_alarm_oter(kayit):
    """Üretim kadanstan çıktı: "kadans koştu" ARTIK "görüş üretildi" DEMEK DEĞİL. Üretici
    koşmazsa kuyruk sessizce birikir ve defter donuk kalır — birikmenin KENDİSİ alarmdır
    (dormant_setup dersi: önden bağlı arkadan bağsız yüzey)."""
    from meridian import obs
    _defterler(n=2)
    _kuyruk_doldur(sg.KUYRUK_BIRIKIM_TAVANI)          # tavanda: HENÜZ alarm yok
    k = sg.kuyruk_kadansi(apply=True, oncesi_ms=1000.0)
    assert k["kuyruk"]["bekleyen"] == sg.KUYRUK_BIRIKIM_TAVANI + 1   # az önce eklenen de sayılır
    olaylar = [e for e in store.read_jsonl("events.jsonl")
               if e.get("alarm") == obs.ALARM_MECHANISM_STALE]
    assert olaylar, "tavan aşıldı ama alarm ötmedi"
    a = olaylar[0]
    # ALAN ADI `mechanism` (TSK-101, 2026-09-03): ilk yazımda TÜRKÇE `mekanizma=` idi ve
    # tüketicilerin hiçbiri (`selfreview._olay_mekanizma`, `notify._signature`) o adı okumuyordu.
    assert a["mechanism"] == "skill_gorus_kuyruk" and a["kart"] == sg.KART
    assert a["bekleyen"] == sg.KUYRUK_BIRIKIM_TAVANI + 1 and a["tavan"] == sg.KUYRUK_BIRIKIM_TAVANI
    assert obs.ALARM_MECHANISM_STALE in a["event"], "jeton satır metnine girmemiş (izleyici arar)"


def test_C6_POZITIF_KONTROL_kuyruk_birikmemisken_alarm_YOK(kayit):
    """C5'i anlamlı kılan çivi: alarm her koşumda ötüyorsa dedektör değil gürültüdür."""
    from meridian import obs
    _defterler(n=2)
    sg.kuyruk_kadansi(apply=True, oncesi_ms=1000.0)
    olaylar = [e for e in store.read_jsonl("events.jsonl")
               if e.get("mechanism") == "skill_gorus_kuyruk"]
    assert olaylar == [], f"tek kesitte yanlış alarm: {olaylar}"
    assert obs.ALARM_MECHANISM_STALE     # jeton gerçekten var (yanlış ada alarm basılmasın)


def test_C7_birikim_olcumu_KADANSIN_olculen_maliyetine_GIRMEZ(kayit):
    """Bedel yasası: gözetim icrayı yavaşlatamaz. Birikim okuması `sure_ms` KAPANDIKTAN sonra
    yapılır — kaynak düzeyinde ölçülür, süre kıyasıyla değil (zamanlama kırılgandır)."""
    fn = _fonksiyonlar(REPO / "meridian" / "skill_gorus.py")["kuyruk_kadansi"]
    govde = ast.get_source_segment((REPO / "meridian" / "skill_gorus.py").read_text(), fn)
    assert govde.index("sure_ms = round(") < govde.index("bekleyen = sum("), \
        "birikim okuması süre ölçümünün İÇİNDE — kadansın maliyeti gözetimle şişer"


def test_C8_gozetim_maliyeti_AYRI_alanla_OLCULUR(kayit):
    """Bedel yasası (Rol-1 hükmü 2026-09-01): ölçüm penceresinin DIŞINDA olmak "bedava" demek
    değildir. Kuyruk her gece uzuyor ve birikim okuması dosyanın tamamını ayrıştırıyor —
    `gozetim_ms` o maliyeti ADIYLA taşır; `sure_ms`/`pay`/p95 tanımı DEĞİŞMEZ."""
    _defterler(n=5)
    _kuyruk_doldur(30)
    k = sg.kuyruk_kadansi(apply=True, oncesi_ms=1000.0)
    assert isinstance(k["gozetim_ms"], (int, float)), "gözetim maliyeti sayısız — bedel ölçülmemiş"
    assert k["gozetim_ms"] >= 0.0
    # AYRI alan: kill hükmünün payı YALNIZ `sure_ms`ten türer — gözetim ona katılsaydı eşitlik
    # bozulurdu (p95 tanımının değişmediğinin ölçüsü, zamanlama kıyası değil).
    assert k["pay"] == round(k["sure_ms"] / 1000.0, 4)
    # KALICI OKUYUCU (Yasa 6, alan düzeyi): pano yüzeyi alanı taşır.
    from meridian import api
    assert api._eksen2_gorus()["son_kadans"]["gozetim_ms"] == k["gozetim_ms"]


def test_C9_TAM_KOSU_mandali_da_apply_biciminde(kayit, monkeypatch):
    """K4'ün ikinci yarısı (Rol-1 hükmü 2026-09-01): `kadans` mandalı diğer dört fonksiyonla ve
    kendi docstring vaadiyle hizalanır. Kapalı katmanda TAM koşunun süresi hâlâ ölçülebilmeli —
    kartın yeniden açılışı "tam koşu ne kadar sürüyor" sayısını ister ve o sayıyı kapının kendisi
    imkânsız kılarsa katman bir daha ÖLÇÜLEREK açılamaz."""
    _defterler(n=8)
    monkeypatch.setattr(sg, "_KAPATMA_OLAYI_BASILDI", False)
    monkeypatch.setattr(config, "SKILL_GORUS_URETIM_ACIK", False)
    kuru = sg.kadans(apply=False, oncesi_ms=1000.0)
    assert kuru.get("kapali") is None, "kapalı katmanda kuru TAM koşu ölçüm aracı olarak açık olmalı"
    assert isinstance(kuru["sure_ms"], (int, float)) and kuru["uygulandi_mi"] is False
    assert not (pathlib.Path(kayit) / sg.DURUM_DEFTERI).exists(), "kuru koşu durum defterine yazdı"
    assert not (pathlib.Path(kayit) / sg.GORUS_DEFTERI).exists(), "kuru koşu görüş defterine yazdı"
    # ÖTEKİ YÖN: apply=True kapalı katmanda hâlâ ÖLÜ (mandal gevşetilmedi, `apply`ye taşındı).
    kapali = sg.kadans(apply=True, oncesi_ms=1000.0)
    assert kapali["kapali"] is True and kapali["sure_ms"] is None
    assert not (pathlib.Path(kayit) / sg.GORUS_DEFTERI).exists()


# =================================================================================================
# D — t-ÇİTİ (MUTASYON HEDEFİ #2)
# =================================================================================================
def test_D1_gorus_damgasi_SNAPSHOT_anidir_uretim_ani_DEGIL(kayit):
    """KESİT ANI GERİYE ÇEKİLİR ve ölçüm ONUN ÜSTÜNDEN yapılır.

    İLK YAZIMDA BU ÇİVİ KÖRDÜ (mutasyon turu, 2026-09-01): kesit ile üretim aynı SANİYE içinde
    koştuğu ve `_now()` saniye çözünürlüklü olduğu için, `ts=None` mutasyonu (yani t-çitinin
    kaldırılması) AYNI damgayı üretiyordu ve çivi yeşil kalıyordu. Ölçülen fark, ölçüldüğü
    çözünürlükten küçük olamaz — kesit üç ay geriye alınır ve fark ölçülebilir olur."""
    _defterler()
    sg.kuyruk_kadansi(apply=True, oncesi_ms=1000.0)
    ESKI = "2026-06-01T22:00:00+00:00"
    store.update_jsonl(sg.KUYRUK_DEFTERI, lambda rows: rows[0].update({"ts": ESKI}) or True)
    sg.kuyruktan_uret(apply=True)
    satirlar = sg.defter()
    assert satirlar, "kuyruktan hiç görüş üretilmedi"
    assert {s["ts"] for s in satirlar} == {ESKI}, (
        "görüş satırı ÜRETİM anını damgalamış — t-çiti yok; geciken bir üretici görüşü "
        f"gözlenmediği bir ana bağlardı (ölçülen: {sorted({s['ts'] for s in satirlar})})")
    assert {s["uretici"] for s in satirlar} == {sg.URETICI_DET}


def test_D2_SNAPSHOT_SONRASI_canli_defter_degisirse_URETIME_GIRMEZ(kayit):
    """Sızma denemesi #1: kesit alındıktan sonra KAYNAK defter değişir. Üretici onu GÖRMEMELİ."""
    _defterler(n=10)
    sg.kuyruk_kadansi(apply=True, oncesi_ms=1000.0)
    store.write_jsonl("counterfactuals.jsonl", _cf(10) + _cf(5, ilk=900))   # 5 YENİ gözlem
    u = sg.kuyruktan_uret(apply=True)
    hedefler = {s["hedef"] for s in sg.defter()}
    sonradan = {f"CF-x-{i}" for i in range(900, 905)}
    assert not (hedefler & sonradan), \
        f"snapshot SONRASI eklenen satır üretime sızdı: {sorted(hedefler & sonradan)}"
    assert u["yazilan"] == 20        # 10 gözlem × 2 yüzey


def test_D3_snapshota_SONRADAN_eklenen_alan_URETIME_SIZAMAZ(kayit):
    """Sızma denemesi #2: kesit satırına yeni alan eklenir ve kanonik alan silinir.

    Beklenen: yeni alan SAYILIR ve düşürülür (`cit_disi_alan`); kanonik alanı olmayan gözlem
    ONARILMAZ — kendi kovasına ADIYLA düşer (uydurma yasağı)."""
    _defterler(n=3)
    sg.kuyruk_kadansi(apply=True, oncesi_ms=1000.0)

    def _kirlet(rows):
        g = rows[0]["gozlemler"]
        g[0]["skor_v2"] = 999.0            # kesit sonrası eklenmiş alan
        g[0]["skor"] = None                # kanonik alan YOK → onarılmamalı
        g[1]["r"] = None                   # çıkış ölçüsü YOK
        g[2]["hedef"] = ""                 # kimliksiz gözlem
        return True
    store.update_jsonl(sg.KUYRUK_DEFTERI, _kirlet)

    u = sg.kuyruktan_uret(apply=True)
    assert u["atlanan"]["cit_disi_alan"] == 1, "sonradan eklenen alan sayılmadı"
    assert u["atlanan"]["skorsuz"] == 1 and u["atlanan"]["cikis_olcusuz"] == 1
    assert u["atlanan"]["kimliksiz"] == 1
    for s in sg.defter():
        assert s["skor"] != 999.0, "kaçak alan görüşe sızdı"
    # 3 gözlemden: #0 yalnız çıkış, #1 yalnız sıralayıcı, #2 hiç → 2 satır
    assert u["yazilan"] == 2


def test_D4_SNAPSHOT_ALANLARI_gozlem_semasiyla_AYRISMAZ(kayit):
    """Beyaz liste `_gozlemler()`in ürettiği alanların TAM kopyasıdır; ayrışırsa çit ya çok
    şey keser (ölçüm kaybı) ya çok şey geçirir (çit teatral olur)."""
    _defterler(n=2)
    uretilen = set(sg._gozlemler()["satirlar"][0])
    assert uretilen == set(sg.SNAPSHOT_ALANLARI), (
        f"gözlem şeması ile snapshot beyaz listesi ayrıştı: "
        f"fazla={sorted(uretilen - set(sg.SNAPSHOT_ALANLARI))} "
        f"eksik={sorted(set(sg.SNAPSHOT_ALANLARI) - uretilen)}")


# =================================================================================================
# E — İDEMPOTENS VE TAVAN
# =================================================================================================
def test_E1_ikinci_kosum_MUKERRER_yazmaz_ve_snapshot_ISARETLENIR(kayit):
    _defterler(n=5)
    sg.kuyruk_kadansi(apply=True, oncesi_ms=1000.0)
    ilk = sg.kuyruktan_uret(apply=True)
    assert ilk["yazilan"] == 10 and ilk["islenen_snapshot"] == 1 and ilk["bekleyen"] == 0
    satir = sg.kuyruk_oku()[0]
    assert satir["islendi"] is True and satir["uretilen"] == 10 and satir["islendi_ts"]
    assert "gozlemler" not in satir, "işlenen kesitin yükü düşmedi — kuyruk sonsuza dek büyür"
    assert len(satir["gozlem_ozeti"]) == 16, "işlenen kesitin içerik damgası yok"
    ikinci = sg.kuyruktan_uret(apply=True)
    assert ikinci["yazilan"] == 0 and ikinci["islenen_snapshot"] == 0
    assert len(sg.defter()) == 10, "ikinci koşum defteri şişirdi"


def test_E2_ISARET_dusse_bile_ANAHTAR_tekillestirmesi_MUKERRERI_engeller(kayit, monkeypatch):
    """İdempotensin İKİNCİ katı: işaretleme düşse de aynı görüş iki kez yazılmaz."""
    _defterler(n=5)
    sg.kuyruk_kadansi(apply=True, oncesi_ms=1000.0)
    # İŞARETLEME ÖLDÜRÜLÜR (monkeypatch KAPSAM SONUNDA geri alınır — `monkeypatch.undo()` YASAK:
    # autouse fixture'ları da geri alır, vaka 2026-08-30).
    monkeypatch.setattr(store, "update_jsonl", lambda *a, **k: [])
    assert sg.kuyruktan_uret(apply=True)["yazilan"] == 10
    assert sg.kuyruk_oku()[0].get("islendi") is False, "işaretleme gerçekten ölmedi, çivi kör"
    assert sg.kuyruktan_uret(apply=True)["yazilan"] == 0, "işaret düşünce mükerrer satır yazıldı"
    assert len(sg.defter()) == 10


def test_E3_tavana_carpan_snapshot_ISARETLENMEZ(kayit):
    """Yarım işlenmiş kesit 'işlendi' damgası alsaydı kalan gözlemler sessizce kaybolurdu."""
    _defterler(n=5)
    sg.kuyruk_kadansi(apply=True, oncesi_ms=1000.0)
    u = sg.kuyruktan_uret(apply=True, tavan=3)
    assert u["kirpildi"] is True and u["yazilan"] == 0 and u["islenen_snapshot"] == 0
    assert sg.kuyruk_oku()[0]["islendi"] is False and "gozlemler" in sg.kuyruk_oku()[0]
    assert sg.kuyruktan_uret(apply=True, tavan=None)["yazilan"] == 10


def test_E4_sema_uyumsuz_snapshot_ONARILMAZ_ve_ISARETLENMEZ(kayit):
    _defterler(n=3)
    sg.kuyruk_kadansi(apply=True, oncesi_ms=1000.0)
    store.update_jsonl(sg.KUYRUK_DEFTERI, lambda rows: rows[0].update({"sema": 99}) or True)
    u = sg.kuyruktan_uret(apply=True)
    assert u["atlanan"]["sema_uyumsuz_snapshot"] == 1 and u["yazilan"] == 0
    assert sg.kuyruk_oku()[0]["islendi"] is False, "tanınmayan kesit işlenmiş sayıldı"


def test_E5_kuru_kosu_URETIMI_gosterir_ama_YAZMAZ(kayit):
    _defterler(n=4)
    sg.kuyruk_kadansi(apply=True, oncesi_ms=1000.0)
    u = sg.kuyruktan_uret(apply=False)
    assert u["hazirlanan"] == 8 and u["yazilan"] == 0 and u["islenen_snapshot"] == 0
    assert sg.defter() == [] and sg.kuyruk_oku()[0]["islendi"] is False


# =================================================================================================
# F — YASA 6: KUYRUĞUN DIŞ OKUYUCUSU VAR
# =================================================================================================
def test_F1_kuyrugun_DIS_okuyucusu_artefakt_grafinda_GORUNUR():
    g = codelaw.artifact_graph()
    kayit_ = g["artifacts"].get(sg.KUYRUK_DEFTERI)
    assert kayit_, f"{sg.KUYRUK_DEFTERI} artefakt grafında ÇÖZÜLEMEDİ"
    assert kayit_["writers"] == ["skill_gorus.py"], f"beklenmeyen yazar: {kayit_['writers']}"
    assert "api.py" in kayit_["external_readers"], "kuyruk dış okuyucusuz — YASA 6"
    assert kayit_["unread"] is False
    # KAPSAM KENDİ DOSYALARIMIZ (kırılgan çivi ayıklaması 2026-09-01): repo-geneli
    # `violations == []` iddiası bu dosyanın ölçtüğü şey DEĞİLDİR — başka bir turda doğan
    # ilgisiz bir ihlal bu çiviyi kırar ve kuyruk hakkında hiçbir şey söylemez. Repo geneli
    # `test_codelaw_v59` ve `test_codelaw_kor_nokta_v214`'ün işidir; burada yalnız BİZİM
    # artefaktlarımızın ihlal listesinde OLMADIĞI ölçülür.
    bizim = {sg.KUYRUK_DEFTERI, sg.GORUS_DEFTERI, sg.DURUM_DEFTERI}
    assert not (bizim & set(g["violations"])), f"kendi artefaktımız ihlalde: {g['violations']}"
    assert not (bizim & set(g["stale_sinks"]))


def test_F2_pano_alani_kuyruk_derinligini_TASIR(kayit):
    _defterler(n=6)
    sg.kuyruk_kadansi(apply=True, oncesi_ms=1000.0)
    y = api._eksen2_gorus()
    assert y["kuyruk"]["bekleyen"] == 1 and y["kuyruk"]["bekleyen_gozlem"] == 6
    assert y["kuyruk"]["en_eski_bekleyen_ts"] == sg.kuyruk_oku()[0]["ts"]
    assert y["son_kadans"]["yol"] == sg.KUYRUK_YOLU
    assert y["son_kadans"]["yazilan"] is None, "kuyruk yolu görüş yazmaz — 0 demek yanıltıcı olurdu"
    assert y["son_kadans"]["kuyruk_n_gozlem"] == 6
    sg.kuyruktan_uret(apply=True)
    y2 = api._eksen2_gorus()
    assert y2["kuyruk"] == {**y2["kuyruk"], "bekleyen": 0, "islenmis": 1, "uretilen_toplam": 12}
    # HAM KESİT TAŞIMAZ: uç yükü kuyrukla birlikte büyüyemez.
    assert "gozlemler" not in json.dumps(y2["kuyruk"])


# =================================================================================================
# G — BEDEL ÖLÇÜMÜ (bedel yasası: kazanç iddiası ölçülür)
# =================================================================================================
def test_G1_kuyruk_yolu_TAM_KOSUDAN_olculebilir_bicimde_ucuz(kayit, capsys):
    """'Ucuzladı' bir İDDİADIR. İki yol AYNI defter üzerinde ölçülür ve sayı rapora yazılır."""
    _defterler(n=800)
    t0 = time.perf_counter()
    sg.kuyruk_kadansi(apply=True, oncesi_ms=1000.0)
    kuyruk_ms = (time.perf_counter() - t0) * 1000.0
    t0 = time.perf_counter()
    sg.kadans(apply=True, oncesi_ms=1000.0)
    kadans_ms = (time.perf_counter() - t0) * 1000.0
    with capsys.disabled():
        print(f"\nBEDEL-OLCUMU v356 (n_gozlem=800): kuyruk_append={kuyruk_ms:.1f} ms · "
              f"tam_kosu={kadans_ms:.1f} ms · oran={kadans_ms / max(kuyruk_ms, 1e-6):.1f}×")
    # MUTLAK ms EŞİĞİ YOK (kırılgan çivi ayıklaması 2026-09-01): "tam koşu > 5 ms" iddiası
    # makinenin hızına bağlıdır ve bir gün daha hızlı bir makinede ayrışmayı DEĞİL donanımı
    # ölçerdi. Çivinin sözü ORANDIR: kadanstan çıkarmanın ölçülmüş bir kazancı var mı?
    assert kuyruk_ms * 3 < kadans_ms, (
        f"kuyruk yolu tam koşunun üçte birinden ucuz değil (kuyruk={kuyruk_ms:.1f} ms, "
        f"tam={kadans_ms:.1f} ms) — kadanstan çıkarmanın ölçülmüş bir kazancı yok")


# =================================================================================================
# H — OPS BETİĞİ: SÖZLEŞME KOMUT SATIRIDIR (main() DEĞİL)
# =================================================================================================
def _kum(tmp_path: pathlib.Path) -> pathlib.Path:
    """İzole MERIDIAN_ROOT — betik GERÇEKTEN koşsun ama canlı `state/`e dokunmasın."""
    (tmp_path / "state").mkdir()
    for f in ("goal.yaml", "bounds.yaml"):
        src = REPO / "state" / f
        if src.exists():
            (tmp_path / "state" / f).write_bytes(src.read_bytes())
    return tmp_path


def _kos(kok: pathlib.Path, *bayrak: str, acik: bool = False, kapali: bool = False):
    ort = {**os.environ, "MERIDIAN_ROOT": str(kok), "MERIDIAN_DB": "off"}
    if acik or kapali:
        # BAYRAK SÜREÇ-YEREL AÇILIR/KAPANIR ve GİRİŞ NOKTASI YİNE KOMUT SATIRIDIR (`runpy` +
        # `sys.argv`): `main([...])` çağırmak API'yi sınardı, operatörün koştuğu yolu değil
        # (vaka SD10, v331). `kapali` 2026-09-01 açılışıyla geldi: üretim varsayılanı artık
        # AÇIK, kapalı-katman çivileri kapalılığı KURARAK koşar (v278 sg_kapali ile aynı ilke).
        kod = ("import runpy, sys; import meridian.config as c; "
               f"c.SKILL_GORUS_URETIM_ACIK = {bool(acik)}; "
               f"sys.argv = ['skill_gorus_uret.py', {', '.join(repr(b) for b in bayrak)}]; "
               f"runpy.run_path({str(BETIK)!r}, run_name='__main__')")
        return subprocess.run([sys.executable, "-c", kod], capture_output=True, text=True,
                              env=ort, cwd=str(REPO))
    return subprocess.run([sys.executable, str(BETIK), *bayrak],
                          capture_output=True, text=True, env=ort, cwd=str(REPO))


def test_H1_CLI_durum_kosar_ve_hicbir_sey_YAZMAZ(tmp_path):
    kok = _kum(tmp_path)
    r = _kos(kok, "--durum")
    assert r.returncode == 0, f"çıkış {r.returncode}\n{r.stdout}\n{r.stderr}"
    assert '"bekleyen": 0' in r.stdout
    assert not (kok / "state" / sg.GORUS_DEFTERI).exists()


def test_H2_CLI_uygula_KAPALI_katmanda_SESSIZCE_basarili_olmaz(tmp_path):
    """Ölçülmüş sınıf (vaka 2026-08-30): 18 çivi yeşilken `--uygula` sessizce yok sayılıyordu.
    Açılıştan (2026-09-01) beri kapalılık süreç-yerel KURULUR — çivinin sözü değişmedi:
    kapalı katman sessizce başarılı olmaz."""
    kok = _kum(tmp_path)
    r = _kos(kok, "--uygula", kapali=True)
    assert r.returncode == 1, f"kapalı katmanda --uygula 0 döndü: {r.stdout}"
    assert "KATMAN KAPALI" in r.stderr and "SKILL_GORUS_URETIM_ACIK" in r.stderr
    assert not (kok / "state" / sg.GORUS_DEFTERI).exists()


def test_H3_CLI_uygula_bayrak_ACIKKEN_GERCEKTEN_yazar(tmp_path):
    """H2'yi anlamlı kılan çivi + operatörün koşacağı biçimde uçtan uca koşum."""
    kok = _kum(tmp_path)
    kuyruk = {"ts": "2026-08-30T22:00:00+00:00", "sema": sg.KUYRUK_SEMA, "islendi": False,
              "evren": ["vcp-screener"], "n_gozlem": 2,
              "gozlemler": [{"skill": "vcp-screener", "tarih": "2026-06-01", "hedef": "CF-a",
                             "skor": 10.0, "karar": "target", "r": 0.5, "mfe_r": 0.7,
                             "kaynak": "cf"},
                            {"skill": "vcp-screener", "tarih": "2026-06-02", "hedef": "CF-b",
                             "skor": 20.0, "karar": "stop", "r": -0.2, "mfe_r": 0.3,
                             "kaynak": "cf"}],
              "atlanan": {}}
    (kok / "state" / sg.KUYRUK_DEFTERI).write_text(json.dumps(kuyruk) + "\n", encoding="utf-8")
    r = _kos(kok, "--uygula", acik=True)
    assert r.returncode == 0, f"çıkış {r.returncode}\n{r.stdout}\n{r.stderr}"
    satirlar = [json.loads(x) for x in
                (kok / "state" / sg.GORUS_DEFTERI).read_text(encoding="utf-8").splitlines() if x]
    assert len(satirlar) == 4, f"CLI --uygula yazmadı ya da eksik yazdı: {r.stdout}"
    assert {s["ts"] for s in satirlar} == {"2026-08-30T22:00:00+00:00"}   # t-çiti CLI'da da geçerli
    assert json.loads((kok / "state" / sg.KUYRUK_DEFTERI).read_text())["islendi"] is True


if __name__ == "__main__":                                  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-v"]))
