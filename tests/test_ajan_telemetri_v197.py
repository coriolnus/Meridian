"""test_ajan_telemetri_v197.py — AJAN ÇAĞRI TELEMETRİSİ + HAM İZ DEFTERİ (D3 modül 1/2, 2026-08-07).

Kaynak: `docs/PATTERN-ETUDU-2026-08-06.md` C2-1 (S) / C2-2 (M) · `docs/TASARIM-YONU-2026-08-07.md` §4.

ÖLÇÜLMÜŞ KÖRLÜK (canlı defter, 2026-08-04 yedeği — tahmin değil, satır):
    01:14:07  agent_call kind=system_eval model=gemini-3.5-flash attempt=1 empty=true tool_calls=-1
    01:14:17  agent_call kind=system_eval model=tencent/hy3:free  attempt=2 empty=true tool_calls=-1
    01:14:17  agent_call_empty ... cooldown_s=21600
Aradaki 10 saniye ÇIKARSAMADIR: içinde bütçe bekleyişi, skill senkronu ve İKİ ayrı süreç doğuşu
da vardır. "Gece koşusu neden 40 dk sürdü, hangi çağrı takıldı" sorusu bu yüzden cevapsızdı.

Bu dosya beş sözleşmeyi kilitler:
  1. KOŞAN HER ALT SÜREÇ ölçülür — onarım yeniden-koşumları dâhil, `alt` sayacıyla ayrışarak.
  2. Süre ÖLÇÜM ANINDA yazılır ve `agent_calls.jsonl`e iner (türetilmez).
  3. `arac_cagri_n=None` = ÖLÇÜLEMEDİ (0 DEĞİL) ve nedeni satırda yazılıdır.
  4. Ham iz AYRI deftere, SIR-MASKELİ, akış başına tavanlı ve halkasal budamalı iner; tavanlar
     doğuşta yazılıdır ve burada ÇİVİLENİR.
  5. Maskeleme TEK KAYNAKTIR: `hermes._ham_ozet` gövdesi `agent_telemetry`ye delege eder.

Alt süreç ve ağ SAPLIDIR; fikstürlerde gerçek anahtar/token YOKTUR.
"""
import subprocess

import pytest

from meridian import agent_telemetry as at, hermes, store


BIRINCI = "birincil-x"
YEDEK = "yedek-y"
DOLU_CIKTI = '{"reviews": []}\n'
SKILL_HATASI = "Error: Unknown skill(s): olmayan-skill\n"
# ÖLÇÜLMÜŞ ilk-koşum rehberi imzası (hermes_cli/setup.py; bkz. hermes.AGENT_UNCONFIGURED_SIGNS)
YAPILANDIRMASIZ = "It looks like Hermes isn't configured yet\nhermes config set model.default X\n"


class _Kosum:
    """subprocess.run sonucu taklidi — süreç YOK, ağ YOK."""

    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode, self.stdout, self.stderr = returncode, stdout, stderr


@pytest.fixture
def ajan(sandbox_state, monkeypatch):
    """Yerel ajan düzeneği (v193 fikstürünün ikizi) — sıralı saplı alt süreç + iki modelli zincir."""
    monkeypatch.setattr(hermes, "_hermes_bin", lambda: "/sahte/hermes")
    monkeypatch.setattr(hermes, "sync_agent_skills", lambda: None)
    monkeypatch.setattr(hermes.secrets, "get",
                        lambda k: {"NOUS_MODEL": BIRINCI, "NOUS_FALLBACK_MODEL": YEDEK}.get(k))

    class _Duzenek:
        runs: list = []
        sonuclar: list = [_Kosum(0, DOLU_CIKTI, "")]

        def _cagir(self, cmd, **kw):
            self.runs.append(list(cmd))
            i = min(len(self.runs) - 1, len(self.sonuclar) - 1)
            s = self.sonuclar[i]
            if isinstance(s, BaseException):
                raise s
            return s

    d = _Duzenek()
    monkeypatch.setattr(subprocess, "run", d._cagir)
    return d


def _telemetri() -> list:
    return store.read_jsonl(at.CAGRI_DEFTERI)


def _izler() -> list:
    return store.read_jsonl(at.IZ_DEFTERI)


# ============================================================ 1) SÜRE ÖLÇÜLÜR VE DEFTERE İNER

def test_her_cagri_bir_telemetri_satiri_yazar_ve_sure_olculur(ajan):
    """C2-1'in çekirdeği: süre TÜRETİLEMEZ, ölçüm anında yazılmalı."""
    assert hermes._agent_call("istem", kind="review") == DOLU_CIKTI
    rows = _telemetri()
    assert len(rows) == 1, "tek koşum → tek telemetri satırı"
    r = rows[0]
    assert r["kind"] == "review" and r["model"] == BIRINCI
    assert r["deneme"] == 1 and r["alt"] == 0
    assert r["sonuc_sinifi"] == at.SINIF_DOLU and r["returncode"] == 0
    assert isinstance(r["sure_ms"], float) and r["sure_ms"] >= 0.0
    assert r["tasiyici"] == at.TASIYICI_AJAN
    assert r["cikti_kr"] == len(DOLU_CIKTI) and r["hata_kr"] == 0
    assert r["iz_id"].startswith("AC-") and r["iz_id"].endswith("-review-1.0")


def test_sure_olay_defterine_de_dusuyor(ajan):
    """Canlı journal'ı takip eden operatör de süreyi görmeli — yoksa "iki damganın farkı = süre"
    hatası olay defterinde geri döner."""
    hermes._agent_call("istem", kind="review")
    ev = [e for e in store.read_jsonl("events.jsonl") if e.get("event") == "agent_call"][-1]
    assert "sure_ms" in ev and isinstance(ev["sure_ms"], float)
    assert ev["alt_kosum"] == 0


def test_model_zinciri_her_denemeyi_AYRI_satirla_yazar(ajan):
    """Canlı vakada iki deneme vardı ve ikisi de aynı hikâyeyi anlatıyordu; artık her denemenin
    KENDİ süresi ve KENDİ sonucu var."""
    ajan.sonuclar = [_Kosum(0, "", ""), _Kosum(0, "", "")]        # ikisi de boş
    assert hermes._agent_call("istem", kind="system_eval") is None
    rows = _telemetri()
    assert [r["deneme"] for r in rows] == [1, 2]
    assert [r["model"] for r in rows] == [BIRINCI, YEDEK]
    assert {r["sonuc_sinifi"] for r in rows} == {at.SINIF_BOS}


def test_onarim_yeniden_kosumu_AYRI_alt_satiri_olur(ajan):
    """Ön-uçuş skill hatası çağrıyı bir kez YENİDEN koşturur. İki koşum tek satıra katlanırsa
    "hangi koşum ne kadar sürdü" sorusu geri kaybolur — `alt` sayacı onu ayırır."""
    ajan.sonuclar = [_Kosum(1, SKILL_HATASI, ""), _Kosum(0, DOLU_CIKTI, "")]
    assert hermes._agent_call("istem", preload=("olmayan-skill",), kind="review") == DOLU_CIKTI
    rows = _telemetri()
    assert [(r["deneme"], r["alt"]) for r in rows] == [(1, 0), (1, 1)]
    assert rows[0]["sonuc_sinifi"] == at.SINIF_ON_UCUS_SKILL
    assert rows[0]["on_yukleme_n"] == 1, "DÜŞMEDEN ÖNCEKİ liste uzunluğu yazılır"
    assert rows[1]["sonuc_sinifi"] == at.SINIF_DOLU and rows[1]["on_yukleme_n"] == 0
    assert rows[0]["iz_id"] != rows[1]["iz_id"], "iki koşum iki ayrı ize bağlanır"


def test_yapilandirmasiz_cagri_kendi_sinifiyla_yazilir(ajan):
    """Yapılandırmasızlık kota DEĞİLDİR (v190 dersi) ve telemetride de kendi sınıfında durur."""
    ajan.sonuclar = [_Kosum(1, YAPILANDIRMASIZ, "")]
    assert hermes._agent_call("istem", kind="proposal") is None
    rows = _telemetri()
    assert len(rows) == 1 and rows[0]["sonuc_sinifi"] == at.SINIF_YAPILANDIRMASIZ
    assert rows[0]["deneme"] == 1, "zincir DENENMEZ — ikinci model için satır da olmamalı"


def test_zaman_asimi_deftere_yazilir_ve_istisna_AYNEN_yukari_gider(ajan):
    """Takılan çağrı tam da C2-1'in cevaplamak istediği soruydu; bugüne dek defterde HİÇ yoktu."""
    ajan.sonuclar = [subprocess.TimeoutExpired(cmd=["x"], timeout=300)]
    with pytest.raises(subprocess.TimeoutExpired):
        hermes._agent_call("istem", kind="review", timeout=300)
    rows = _telemetri()
    assert len(rows) == 1 and rows[0]["sonuc_sinifi"] == at.SINIF_ZAMAN_ASIMI
    assert rows[0]["zaman_asimi_s"] == 300 and rows[0]["returncode"] is None


def test_cagri_YAPILMADAN_donen_yollar_defter_yazmaz(ajan):
    """Süresi olmayan bir şeye 'çağrı süresi' satırı yazmak ortalamayı sessizce aşağı çeker."""
    hermes.brain_stand_down("agent", "test")
    assert hermes._agent_call("istem", kind="review") is None
    assert _telemetri() == [], "soğuma yolunda süreç doğmadı — telemetri satırı da olmamalı"


# ============================================================ 2) ARAÇ SAYISI: ÖLÇÜLEMEDİ ≠ 0

def test_arac_sayisi_olculemediginde_None_yazilir_ve_nedeni_satirda_durur(ajan):
    """`-Q` oturum özetini bastırır → araç sayısı ÖLÇÜLEMEZ. 0 yazmak "araç kullanılmadı" diye
    okunurdu; eksik alanın sıfır sanılması bu deponun baskın hata sınıfıdır."""
    hermes._agent_call("istem", kind="review")
    r = _telemetri()[0]
    assert r["arac_cagri_n"] is None
    assert len(r["arac_neden"]) >= 20 and "ÖLÇÜLEMEDİ" in r["arac_neden"]


def test_arac_sayisi_olculdugunde_gercek_sayi_yazilir(ajan):
    """Oturum özeti varsa sayı GERÇEKTİR ve None olamaz — ayrım ölçüme dayanır, tahmine değil."""
    ajan.sonuclar = [_Kosum(0, "Messages: 6 (2 user, 3 tool calls)\n" + DOLU_CIKTI, "")]
    hermes._agent_call("istem", kind="review")
    r = _telemetri()[0]
    assert r["arac_cagri_n"] == 3 and "arac_neden" not in r


def test_ozet_orani_YALNIZ_olculenin_icinde_hesaplar(sandbox_state):
    """Ölçülemeyenleri paydaya katmak oranı sessizce seyreltirdi (`agent_tooluse.json` dersi)."""
    at.kaydet(kind="a", model="m", deneme=1, alt=0, sure_ms=10.0,
              sonuc_sinifi=at.SINIF_DOLU, arac_cagri_n=4, stdout="x")
    at.kaydet(kind="b", model="m", deneme=1, alt=0, sure_ms=20.0,
              sonuc_sinifi=at.SINIF_DOLU, arac_cagri_n=None, stdout="x")
    o = at.ozet()
    assert o["arac"] == {"olculen": 1, "olculemeyen": 1, "toplam_arac": 4, "ort": 4.0}
    assert o["sure_ms"]["max"] == 20.0 and o["sure_ms"]["toplam"] == 30.0
    assert o["en_yavas"]["kind"] == "b"


def test_ozet_pencere_disini_SAYAR(sandbox_state):
    """Boş bir özet 'hiç çağrı olmadı' ile 'hepsi pencerenin dışında'yı ayırt edemezse yanlış
    güven üretir."""
    at.kaydet(kind="eski", model="m", deneme=1, alt=0, sure_ms=1.0, ts="2020-01-01T00:00:00+00:00",
              sonuc_sinifi=at.SINIF_DOLU, stdout="x")
    o = at.ozet(pencere_s=3600)
    assert o["n"] == 0 and o["pencere_disi"] == 1


# ============================================================ 3) HAM İZ DEFTERİ (modül 2)

def test_ham_iz_AYRI_deftere_tam_haliyle_yazilir(ajan):
    """200 karakterlik olay özeti bir traceback'i taşıyamaz; tam iz ayrı deftere iner."""
    uzun_hata = "Traceback (most recent call last):\n" + ("  satir\n" * 200)
    ajan.sonuclar = [_Kosum(3, "", uzun_hata), _Kosum(3, "", uzun_hata)]
    assert hermes._agent_call("istem", kind="review") is None
    izler = _izler()
    assert len(izler) == 2, "her koşumun kendi izi var"
    iz = izler[0]
    assert iz["ham_kr"]["stderr"] == len(uzun_hata)
    assert len(iz["stderr"]) > 200, "olay defterindeki 200 karakterlik özetten ÇOK daha uzun"
    assert "Traceback" in iz["stderr"]
    # telemetri ↔ iz birleşmesi
    assert {r["iz_id"] for r in _telemetri()} == {r["iz_id"] for r in izler}


def test_ham_iz_sir_sizdirmaz(ajan):
    """Alt sürecin ortamında GEMINI_API_KEY/MERIDIAN_DASH_TOKEN yaşıyor ve CLI onları
    YANKILAYABİLİR. Maskeleme DESENLEdir; gerçek sır değerleri OKUNMAZ."""
    sizinti = ("GEMINI_API_KEY=AIzaSyC0FFEEbabe1234567890abcdefghij\n"
               "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.PAYLOADPAYLOADPAYLOAD.SIGSIGSIGSIG\n")
    ajan.sonuclar = [_Kosum(1, sizinti, ""), _Kosum(1, sizinti, "")]
    hermes._agent_call("istem", kind="review")
    ham = "\n".join(r["stdout"] + r["stderr"] for r in _izler())
    for parca in ("AIzaSyC0FFEEbabe1234567890abcdefghij", "SIGSIGSIGSIG"):
        assert parca not in ham
    assert "«gizli»" in ham or "«uzun-jeton»" in ham


def test_istem_GOVDESI_deftere_girmez_kimligi_girer(ajan):
    """Gövde onlarca KB'dır (kanıt paketi); saklamak defteri 100 katına çıkarır ve tek kazanç
    okunabilirlik kaybı olurdu. Kimlik yeter: iki çağrı aynı istemi mi taşıyor?"""
    hermes._agent_call("ÇOK GİZLİ İSTEM GÖVDESİ", kind="review")
    r = _telemetri()[0]
    assert r["istem_kr"] == len("ÇOK GİZLİ İSTEM GÖVDESİ")
    assert r["istem_ozet"].startswith("sha256:")
    ham = "\n".join(str(x) for x in _izler())
    assert "ÇOK GİZLİ İSTEM GÖVDESİ" not in ham + str(r)


def test_akis_tavani_kirpar_ve_kirpma_BEYANLIDIR(ajan):
    """Beyansız bir kırpma, kısa bir hatayı kırpılmış uzun bir hatadan ayırt edilemez yapar."""
    dev = "x" * (at.IZ_AKIS_TAVANI_KR + 5_000)
    ajan.sonuclar = [_Kosum(1, dev, ""), _Kosum(1, dev, "")]
    hermes._agent_call("istem", kind="review")
    iz = _izler()[0]
    assert iz["kirpildi"] is True and iz["tavan_kr"] == at.IZ_AKIS_TAVANI_KR
    assert iz["ham_kr"]["stdout"] == len(dev), "kırpma ÖNCESİ gerçek uzunluk korunur"
    assert iz["stdout"].endswith("…(+5000 kr)")
    assert len(iz["stdout"]) <= at.IZ_AKIS_TAVANI_KR + 32


def test_halkasal_budama_tavani_asmaya_izin_vermez(sandbox_state, monkeypatch):
    """Disk patlaması bir arıza değil bir TASARIM hatasıdır: budama kuralı doğuşta yazıldı."""
    monkeypatch.setattr(at, "IZ_SATIR_TAVANI", 5)
    for i in range(9):
        at.kaydet(kind="k", model="m", deneme=1, alt=0, sure_ms=1.0,
                  sonuc_sinifi=at.SINIF_BOS, stdout=f"koşum-{i}", ts=f"2026-08-07T00:00:{i:02d}+00:00")
    izler = _izler()
    assert len(izler) == 5, "halka tavanda durur"
    assert [i["stdout"] for i in izler] == [f"koşum-{i}" for i in range(4, 9)], "EN ESKİ düşer"
    olaylar = [e for e in store.read_jsonl("events.jsonl") if e.get("event") == "agent_trace_pruned"]
    assert olaylar, "budama SESSİZ olamaz — teşhis penceresinin kayması duyurulur"


def test_telemetri_defterinin_de_tavani_var(sandbox_state, monkeypatch):
    monkeypatch.setattr(at, "CAGRI_SATIR_TAVANI", 3)
    for i in range(7):
        at.kaydet(kind="k", model="m", deneme=1, alt=0, sure_ms=float(i),
                  sonuc_sinifi=at.SINIF_DOLU, stdout="x")
    assert len(_telemetri()) == 3


def test_bos_iz_satiri_halkanin_yerini_calmaz(sandbox_state):
    """İki akış da boşsa taşınacak teşhis yoktur; satır yazmak 300'lük görüş alanını yer."""
    at.kaydet(kind="k", model="m", deneme=1, alt=0, sure_ms=1.0, sonuc_sinifi=at.SINIF_BOS)
    assert len(_telemetri()) == 1 and _izler() == []


def test_halka_dolduğunda_disk_TURETILEN_TAVANI_ASMAZ(sandbox_state, monkeypatch):
    """Tavan bir DİLEK değil bir ÜST SINIR olmalı: halka tam dolu ve iki akış da tavandayken
    dosya gerçekten formülün altında mı? (Tam ölçek 2026-08-07'de bir kez ölçüldü — 4.887.600
    bayt; burada küçültülmüş sabitlerle AYNI formül sınanır.)"""
    monkeypatch.setattr(at, "IZ_SATIR_TAVANI", 5)
    dev = "y" * at.IZ_AKIS_TAVANI_KR
    for i in range(9):
        at.kaydet(kind="k", model="m", deneme=1, alt=0, sure_ms=1.0,
                  sonuc_sinifi=at.SINIF_BOS, stdout=dev, stderr=dev)
    tavan = at.IZ_SATIR_TAVANI * (2 * at.IZ_AKIS_TAVANI_KR + at.IZ_USTBILGI_KR)
    bayt = at.iz_durum()["bayt"]
    assert 0 < bayt <= tavan, f"halka doluyken {bayt} bayt > türetilen tavan {tavan}"


def test_disk_tavani_TURETILMIS_ve_beyanli(sandbox_state):
    """Tavan bir tahmin değil bir HESAP; hesabın kendisi burada çivilidir (~5 MB)."""
    beklenen = round(at.IZ_SATIR_TAVANI * (2 * at.IZ_AKIS_TAVANI_KR + at.IZ_USTBILGI_KR) / 1e6, 2)
    assert at.IZ_DISK_TAVANI_MB == beklenen == 4.98
    d = at.iz_durum()
    assert d["satir_n"] is None and "ÖLÇÜLMEDİ" in d["beyan"], \
        "satır sayısı ölçülmüyor (defter ayrıştırılmıyor) — bunu beyan etmek zorundayız"
    assert d["disk_tavani_mb"] == at.IZ_DISK_TAVANI_MB


# ============================================================ 4) MASKELEME TEK KAYNAK

def test_hermes_ham_ozet_agent_telemetry_ye_DELEGE_eder():
    """İkinci bir maskeleme uygulaması YASAK: iki kopya sessizce ayrışır, ayrışan taraf sızdırır."""
    import inspect
    src = inspect.getsource(hermes._ham_ozet)
    assert "_at.maskele" in src
    # Desenler hermes'te ARTIK YAŞAMIYOR (kopya kalırsa sürüklenme kaçınılmaz)
    hsrc = inspect.getsource(hermes)
    assert "_GIZLI_DESENLER" not in hsrc and "_JETON_RE" not in hsrc
    assert hermes._ham_ozet("token=sk-proj-000111222333444555666777888999") == at.maskele(
        "token=sk-proj-000111222333444555666777888999")


def test_ciplak_jeton_sezgisi_YAPILANDIRILMIS_veride_KAPATILABILIR():
    """ÖLÇÜLMÜŞ YANLIŞ POZİTİF (2026-08-07, fikstür dondurucusunun ilk koşumu): canlı bir
    `plan_id` (32 karakter, harf+rakam) «uzun-jeton» diye maskelenmişti — maskeleme bir sırrı
    değil vakanın VERİSİNİ sildi. Sezgi serbest metinde GEREKLİ (sır adsız durabilir), sözlükte
    GEREKSİZ (her değerin bir anahtarı vardır) ve orada ZARARLI."""
    plan_id = "P-2026-07-23-TMO-momentum_burst"
    assert at.sirlari_maskele(plan_id) == "«uzun-jeton»", "serbest metin sezgisi AÇIK kalmalı"
    assert at.sirlari_maskele(plan_id, ciplak_jeton=False) == plan_id
    # ÇAPALI desenler her iki kipte de koşar — kapatılan şey YALNIZ üçüncü sezgidir.
    assert "«gizli»" in at.sirlari_maskele("GEMINI_API_KEY=abc123", ciplak_jeton=False)
    assert "«gizli»" in at.sirlari_maskele("Authorization: Bearer xyz", ciplak_jeton=False)
    # ad kümesi TEK KAYNAK: iki liste tutulsaydı biri sessizce eskirdi
    assert at.gizli_ad("GEMINI_API_KEY") and at.gizli_ad("dash_token") and at.gizli_ad("password")
    assert not at.gizli_ad("plan_id") and not at.gizli_ad("cash")


def test_sirlari_maskele_bicimi_BOZMAZ():
    """Fikstür dondurucusu satır sonlarını ve uzunluğu korumak zorunda; `maskele` katlar/kırpar,
    `sirlari_maskele` katlamaz — ikisi ayrı işlerdir ve sır mantığı yine TEKtir."""
    metin = "birinci satır\nGEMINI_API_KEY=AIzaSyC0FFEEbabe1234567890abcdefghij\nüçüncü satır"
    m = at.sirlari_maskele(metin)
    assert m.count("\n") == 2, "satır yapısı korunur"
    assert "AIzaSyC0FFEEbabe1234567890abcdefghij" not in m and "«gizli»" in m
    assert at.maskele(metin, 500).count("\n") == 0, "defter alanı TEK satırdır"


# ============================================================ 5) YASA 6: DIŞ OKUYUCU GERÇEK

def test_integrations_status_telemetri_ozetini_TASIYOR(ajan):
    """YASA 6'nın dış okuyucusu: `/api/hermes` gövdesine giren gerçek bir tüketici. Pano KARTI
    D3-UI dalgasında çizilir; veri bugün akıyor."""
    hermes._agent_call("istem", kind="review")
    st = hermes.integrations_status()
    assert st["agent_calls"]["n"] == 1
    assert st["agent_calls"]["sinif"] == {at.SINIF_DOLU: 1}
    assert "iz" in st["agent_calls"] and "beyan" in st["agent_calls"]


def test_codelaw_cagri_defterini_MUAF_saymaz_iz_defterini_beyanla_sayar():
    """Kaçış yolu (DECLARED_SINKS) kapatabildiğin yerde kullanılmaz: telemetri defterinin GERÇEK
    dış okuyucusu var, ham iz defterinin muafiyeti ise gerekçesiyle beyanlıdır."""
    from meridian import codelaw
    g = codelaw.artifact_graph()
    assert at.CAGRI_DEFTERI not in codelaw.DECLARED_SINKS
    assert "hermes.py" in g["artifacts"][at.CAGRI_DEFTERI]["external_readers"]
    assert at.IZ_DEFTERI in codelaw.DECLARED_SINKS
    assert len(codelaw.DECLARED_SINKS[at.IZ_DEFTERI]) >= 80
    assert g["violations"] == [] and g["stale_sinks"] == []


def test_iki_defter_de_SOZLESMELI_dogar():
    """2026-07-21'in yedi hatasının altısı 'sözleşmesiz defter' sınıfındandı ve o sınıf 4a/4b'de
    bir kez daha açılmıştı. Üçüncü kez açılmasın: alanlar ilk satır yazılmadan çivilendi."""
    from meridian import ledgers
    for ad in (at.CAGRI_DEFTERI, at.IZ_DEFTERI):
        assert ad in ledgers.CONTRACTS, f"{ad} sözleşmesiz"
        assert ledgers.CONTRACTS[ad].writers == ("agent_telemetry.py",)
    assert "sure_ms" in ledgers.CONTRACTS[at.CAGRI_DEFTERI].required, \
        "`sure_ms` bu defterin VAR OLMA sebebidir — isteğe bağlı olamaz"
    assert "arac_cagri_n" not in ledgers.CONTRACTS[at.CAGRI_DEFTERI].required, \
        "ÖLÇÜLEMEYEN alan zorunlu yapılamaz (uydurma yasağı)"
    assert ledgers.writer_violations() == {}


def test_yazilan_satirlar_kendi_sozlesmesine_UYAR(ajan):
    """Sözleşme yazmak yetmez: üretici GERÇEK bir satır üretip ona uymalı (ledgers.py §1)."""
    from meridian import ledgers
    ajan.sonuclar = [_Kosum(1, "hata", "iz")]
    hermes._agent_call("istem", kind="review")
    for ad in (at.CAGRI_DEFTERI, at.IZ_DEFTERI):
        rows = store.read_jsonl(ad)
        assert rows, f"{ad} boş — üretici testi ölçecek bir şey bulamadı"
        for r in rows:
            assert ledgers.validate_row(ad, r) == [], f"{ad}: {ledgers.validate_row(ad, r)}"


def test_telemetri_arizasi_CAGIRANI_dusurmez_ama_sessiz_de_kalmaz(ajan, monkeypatch):
    """Ölçümün arızası ölçülen işi öldürmemeli — ama sessiz bir telemetri arızası, 'defterde satır
    yok' ile 'mekanizma hiç koşmadı'yı ayırt edilemez yapar (YASA 4)."""
    asil = store.append_jsonl

    def _secici(ad, satir):           # YALNIZ telemetri defteri düşer; olay defteri sağlam kalır
        if ad == at.CAGRI_DEFTERI:
            raise OSError("disk dolu")
        return asil(ad, satir)

    monkeypatch.setattr(store, "append_jsonl", _secici)
    assert hermes._agent_call("istem", kind="review") == DOLU_CIKTI, "çağrı normal dönmeli"
    assert _telemetri() == []
    uyari = [e for e in store.read_jsonl("events.jsonl")
             if e.get("event") == "agent_telemetry_write_failed"]
    assert len(uyari) == 1 and "OSError" in uyari[0]["error"] and len(uyari[0]["detail"]) >= 20
    assert at.kaydet(kind="k", model="m", deneme=1, alt=0, sure_ms=1.0,
                     sonuc_sinifi=at.SINIF_DOLU, stdout="x") is None
