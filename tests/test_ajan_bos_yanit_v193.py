"""test_ajan_bos_yanit_v193.py — LLM HATTININ BOŞ-YANIT KÖRLÜĞÜ (canlı defter, 2026-08-06).

KANIT (canlı olay):
    agent_call kind=review model=gemini-3.5-flash attempt=1 empty=true tool_calls=-1
    agent_call kind=review model=tencent/hy3:free   attempt=2 empty=true tool_calls=-1
    review_fallback_empty

Bu üç satır BİRLİKTE hiçbir teşhis taşımıyordu ve nedeni yapısaldı:
  * `-Q` (sessiz mod) oturum özetini bastırır → `_agent_tool_calls` -1 döner ve
    `_agent_reply_missing` sinyalini KAYBEDER. Yani `empty` fiilen "rc != 0 ya da boş stdout"a iner.
  * O İKİ OLGUNUN HİÇBİRİ deftere yazılmıyordu: ne çıkış kodu, ne stdout, ne stderr.
  * Sınıflandırıcılar (`_agent_unconfigured_sign`, `_agent_quota_sign`) çıktıyı OKUYOR ama
    SAKLAMIYORdu → hiçbir imzaya uymayan bir arıza sonsuza dek görünmez kalırdı.

YEREL ÖLÇÜM (kurulu hermes-agent v0.18.2, 2026-08-06 — tahmin değil, koşum):
  a) `--model gemini-9.9-yok-boyle-model` → rc=0 + DOLU cevap. CLI bilinmeyen modeli SESSİZCE
     varsayılana düşürüyor; yani canlı `empty=true` imzasının kaynağı MODEL ADI OLAMAZ.
  b) `-s yok-boyle-bir-skill` → rc=1 · stdout "Error: Unknown skill(s): yok-boyle-bir-skill" ·
     0,9 sn · AĞA HİÇ ÇIKMAZ. İmza canlı satırla birebir uyar: rc!=0 → empty, `-Q` → tool_calls=-1,
     hata modelden ÖNCE olduğu için zincirin İKİNCİ modeli de aynen düşer, ve çıktıda ne kota ne
     yapılandırma imzası vardır.

EK VAKA (TSK-181(b), A1 canlı defter 09-08 15:44Z → 09-12): ham kanıt (2) DÜŞTÜ ama YETMEDİ —
her akşam `agent_call_empty kind=review cooldown_sinifi=fallback_empty cooldown_s=900
ham_stdout="HTTP 401: User not found."`. İptal edilmiş bir OpenRouter anahtarı (rotasyonun
atladığı GLOBAL hermes env kopyası). 401 metni yalnız `ham_stdout` alanının İÇİNDEydi ve olayın
SINIFI "yedek model sustu" diyordu; dört gün kimse görmedi, öz-inceleme/validation/nous_eval
sessizce atlandı. Yani "ham kanıtı sakla" sözleşmesinin kör noktası SINIFLANDIRMAdır: yanlış
sınıf, doğru ham veriyi görünmez kılar.

Bu dosya DÖRT sözleşmeyi kilitler:
  1. Ön-uçuş skill hatası KENDİ sınıfıdır: bütçe iade edilir, soğuma YAZILMAZ, düşen adlar
     listeden çıkarılıp çağrı BİR KEZ yeniden koşulur (ceza değil onarım).
  2. Boş çağrının HAM KANITI deftere düşer (rc + stdout/stderr özeti) — ve sır sızdırmadan.
  3. Regresyon: imza YOKSA davranış birebir eski (kurtarma yolu masum bir boşluğu ele geçirmez).
  4. 401/403 KENDİ SINIFIDIR (`cooldown_sinifi="yetki_reddi"`) ve KENDİ OLAYINI basar
     (`agent_yetki_reddi`) — `massive_yetki_reddi` deseninin ajan-hattı ikizi. Ceza düz
     penceredir (üstel DEĞİL) ve zincir uzunluğuna BAKMAZ; kod okunur, uydurulmaz; 5xx eski
     sınıfta kalır.

MUTASYON (TSK-181(b), 2026-09-12, ELLE — CLAUDE.md §6 "çivi yeşili kanıt değildir"):
  (a) `yetki = _agent_yetki_reddi(...)` → `yetki = None`: 401 olayı, 403 kodu ve tek-modelli
      zincir penceresi çivilerinin ÜÇÜ birden KIRMIZI.
  (b) `brain_pause(..., BRAIN_COOLDOWN_BASE_S)` → `brain_stand_down(...)`: düz-pencere çivisi
      `assert 1 == 0` (streak) ile KIRMIZI.
  (c) kod bulunamayınca `None` yerine `401` döndürmek: "kod uydurulmaz" çivisi KIRMIZI.
  Üç yama da YEDEK KOPYADAN geri alındı (sha256 eşit) ve `__pycache__` silinip yeniden YEŞİL.

Alt süreç ve ağ SAPLIDIR; fikstürlerde gerçek anahtar/token YOKTUR.
"""
import subprocess

import pytest

from meridian import hermes, store


BIRINCI = "birincil-x"
YEDEK = "yedek-y"

# Ölçülmüş ön-uçuş hatası (yerel koşum, v0.18.2): mesaj STDOUT'a düşer, rc=1.
SKILL_HATASI = "Error: Unknown skill(s): olmayan-skill\n"
DOLU_CIKTI = '{"reviews": []}\n'


class _Kosum:
    """subprocess.run sonucu taklidi — süreç YOK, ağ YOK."""

    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode, self.stdout, self.stderr = returncode, stdout, stderr


@pytest.fixture
def ajan(sandbox_state, monkeypatch):
    """Yerel ajan düzeneği: sahte ikili, iki modelli düşüş zinciri, SIRALI saplı alt süreç.

    `sonuclar` listesindeki koşumlar sırayla döner (son eleman tükenirse tekrarlanır); çalıştırılan
    komutlar `runs`ta birikir — hangi `-s` listesinin GERÇEKTEN gittiği ancak buradan ölçülür."""
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
            return self.sonuclar[i]

        def skills(self, i):
            """i. koşumun `-s` ile geçirdiği skill adları."""
            c = self.runs[i]
            return [c[j + 1] for j, t in enumerate(c) if t == "-s"]

    d = _Duzenek()
    monkeypatch.setattr(subprocess, "run", d._cagir)
    return d


def _events(event: str | None = None) -> list:
    rows = store.read_jsonl("events.jsonl")
    return [r for r in rows if event is None or r.get("event") == event]


# --------------------------------------------------------- 1) ÖN-UÇUŞ SKILL HATASI: ONAR, CEZALANDIRMA
def test_bilinmeyen_skill_listeden_dusurulur_ve_cagri_bir_kez_yeniden_kosar(ajan):
    """Ölçülmüş vaka: bayat bir symlink TÜM hattı susturuyordu. Artık düşen ad çıkarılır ve
    kalanla yeniden denenir — tek bir bozuk skill, çalışan yedisini rehin alamaz."""
    ajan.sonuclar = [_Kosum(1, SKILL_HATASI, ""), _Kosum(0, DOLU_CIKTI, "")]
    out = hermes._agent_call("istem", preload=("saglam-a", "olmayan-skill", "saglam-b"),
                             kind="review")
    assert out == DOLU_CIKTI, "kurtarma koşumunun cevabı çağırana DÖNMELİ"
    assert len(ajan.runs) == 2, "kurtarma TEK atımlıktır — sonsuz yeniden deneme yok"
    assert ajan.skills(0) == ["saglam-a", "olmayan-skill", "saglam-b"]
    assert ajan.skills(1) == ["saglam-a", "saglam-b"], "yalnız DÜŞEN ad çıkar; kalanlar korunur"
    ev = _events("agent_skill_preload_unknown")
    assert len(ev) == 1 and ev[0]["eksik"] == ["olmayan-skill"]
    assert ev[0]["returncode"] == 1 and len(ev[0]["detail"]) >= 20      # YASA 4


def test_on_ucus_hatasi_kota_degildir_soguma_yazilmaz_butce_iade_edilir(ajan):
    """AĞA ÇIKMAMIŞ bir çağrı kotadan bir şey harcamadı: RPD iadesi yapılır, havuz soğuması
    YAZILMAZ. `agent_unconfigured` yolunun aynı disiplini — iki arızayı tek cezaya katlamak,
    v188'de altı saatlik sahte kilidi üreten hatanın ta kendisiydi."""
    ajan.sonuclar = [_Kosum(1, SKILL_HATASI, ""), _Kosum(0, DOLU_CIKTI, "")]
    hermes._agent_call("istem", preload=("olmayan-skill",), kind="review")
    assert hermes.brain_cooldown("agent") == 0, "ön-uçuş hatası havuz soğuması YAZMAMALI"
    assert _events("agent_skill_preload_unknown")[0]["butce_iade"] is True
    # gün sayacı: 2 alım (ilk + kurtarma) − 1 iade = 1
    assert int(store.read_json(hermes.AGENT_BUDGET_FILE, {}).get("day", 0)) == 1


def test_kurtarma_da_bos_donerse_zincir_normal_akisina_doner(ajan):
    """Onarım bir GARANTİ değil bir DENEME'dir: kurtarma da boş dönerse yedek model denenir ve
    hattın mevcut boş-yanıt yasası (v188) aynen işler — kurtarma yolu ikinci bir kaçış deliği açmaz."""
    ajan.sonuclar = [_Kosum(1, SKILL_HATASI, ""), _Kosum(0, "", ""), _Kosum(0, "", "")]
    assert hermes._agent_call("istem", preload=("olmayan-skill",), kind="review") is None
    assert len(ajan.runs) == 3, "birincil + kurtarma + yedek"
    assert _events("agent_call_empty") and _events("review_fallback_empty")


def test_imza_yoksa_kurtarma_yoluna_girilmez_davranis_birebir_eski(ajan):
    """REGRESYON KAPISI. Ölçüldü: GEÇERSİZ MODEL ADI bile CLI'da sessizce varsayılana düşer, yani
    boş yanıtların çoğunun skill'le ilgisi yoktur. İmza yoksa fazladan tek bir süreç bile doğmamalı."""
    ajan.sonuclar = [_Kosum(0, "", "")]
    assert hermes._agent_call("istem", preload=("saglam-a",), kind="review") is None
    assert len(ajan.runs) == 2, "yalnız iki model denemesi — kurtarma koşumu YOK"
    assert _events("agent_skill_preload_unknown") == []


@pytest.mark.parametrize("metin,beklenen", [
    ("Error: Unknown skill(s): a\n", ["a"]),
    ("Error: Unknown skill(s): a, b, c", ["a", "b", "c"]),
    ("unknown skill(s): tek-ad.", ["tek-ad"]),
    ("her şey yolunda", []),
    ("", []),
])
def test_bilinmeyen_skill_ayristirmasi(metin, beklenen):
    """Adlar ÇIKTIDAN okunur, tahmin edilmez: hangi adın düştüğünü bilmeden listeyi komple
    boşaltmak, çalışan skill'leri de cezalandırıp ajanı bilgisiz bırakırdı."""
    assert hermes._agent_unknown_skills(metin, "") == beklenen


# --------------------------------------------------------------- 2) HAM KANIT DEFTERE DÜŞER
def test_agent_call_empty_ham_ciktiyi_ve_cikis_kodunu_tasir(ajan):
    """KÖRLÜĞÜN SONU: `empty=true` satırı artık NEDEN boş olduğunu da söyler."""
    ajan.sonuclar = [_Kosum(3, "", "Traceback: provider handshake failed\n")]
    assert hermes._agent_call("istem", kind="review") is None
    ev = _events("agent_call_empty")[-1]
    assert ev["returncode"] == 3
    assert "provider handshake failed" in ev["ham_stderr"]
    assert ev["ham_stdout"] == ""
    cagri = _events("agent_call")[-1]
    assert cagri["returncode"] == 3 and cagri["stdout_kr"] == 0 and cagri["stderr_kr"] > 0


def test_ham_ozet_ansi_soker_satirlari_katlar_ve_kirpma_beyanli(ajan):
    """Defter tek satırlıktır: ham ANSI ve satır sonları alanı okunmaz yapardı. Kırpma da BEYANLIDIR
    — "…(+N kr)" olmadan kısa bir hata, kırpılmış uzun bir hatadan ayırt edilemez."""
    assert hermes._ham_ozet("\x1b[33m⚠ uyarı\x1b[0m\nikinci satır") == "⚠ uyarı ⏎ ikinci satır"
    uzun = hermes._ham_ozet("x" * 500)
    assert uzun.startswith("x" * 200) and uzun.endswith("…(+300 kr)") and "\x1b" not in uzun


@pytest.mark.parametrize("ham", [
    "GEMINI_API_KEY=AIzaSyC0FFEEbabe1234567890abcdefghij",
    "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.PAYLOADPAYLOADPAYLOAD.SIGSIGSIGSIG",
    "token=sk-proj-000111222333444555666777888999aaa",
])
def test_ham_ozet_sir_sizdirmaz(ham):
    """Alt sürecin ortamında `GEMINI_API_KEY`/`MERIDIAN_DASH_TOKEN` yaşıyor (birim EnvironmentFile +
    devralınan ortam) ve bir CLI hata mesajı bunları YANKILAYABİLİR. Maskeleme DESENLEdir: gerçek
    sır değerlerini okumak (secrets.get), sızıntı yüzeyini teşhis uğruna genişletmek olurdu."""
    ozet = hermes._ham_ozet(ham)
    assert "«gizli»" in ozet or "«uzun-jeton»" in ozet
    for parca in ("AIzaSyC0FFEEbabe1234567890abcdefghij", "SIGSIGSIGSIG",
                  "sk-proj-000111222333444555666777888999aaa"):
        assert parca not in ozet


def test_ham_ozet_maskeleme_kirpmadan_once_kosar():
    """SIRA ÖNEMLİ: önce kırpsaydık 200. karakterde ikiye bölünen bir anahtarın ilk yarısı maskesiz
    kalırdı — yarım sır da sırdır (alfabe + uzunluk bilgisi verir)."""
    anahtar = "AIzaSy" + "Q7" * 20
    ozet = hermes._ham_ozet("dolgu " * 40 + anahtar)
    assert anahtar[:40] not in ozet and anahtar[:24] not in ozet


# ================================================================================================
# 4) TSK-181(b) — 401/403 YETKİ REDDİ KENDİ SINIFIDIR (görünür olay + düz pencere)
# ================================================================================================
# ÖLÇÜLEN (A1 canlı defter, 09-08 → 09-12): her akşam `agent_call_empty kind=review
# cooldown_sinifi=fallback_empty cooldown_s=900 ham_stdout="HTTP 401: User not found."`.
# İptal edilmiş bir OpenRouter anahtarı (rotasyonun atladığı global hermes env kopyası). 401 metni
# YALNIZ `ham_stdout` alanının içinde yaşıyordu; olayın sınıfı "yedek model sustu" diyordu ve
# 4 gün boyunca kimse görmedi — öz-inceleme/validation/nous_eval sessizce atlandı.
# EMSAL: `meridian/adapters/massive.py::_yetki_reddi_yaz` aynı olguyu (`massive_yetki_reddi`)
# KENDİ olayı + kendi hükmüyle basar ve bekçi brifingine `durum:` damgasıyla girer. Bu blok o
# deseni ajan hattına BİREBİR taşır.
YETKI_401 = "HTTP 401: User not found.\n"
YETKI_403 = "HTTP 403: Forbidden\n"
SUNUCU_500 = "HTTP 500: Internal Server Error\n"


def test_401_ayri_yetki_olayi_basar_ve_sinifi_yetki_reddidir(ajan):
    """401 bir PLAN/YETKİ HÜKMÜDÜR: aynı anahtarla atılan ikinci istek tanımı gereği aynı cevabı
    alır. `fallback_empty` ("hat çalıştı, model sustu") sınıfı bunu YANLIŞ anlatıyordu."""
    ajan.sonuclar = [_Kosum(1, YETKI_401, "")]
    assert hermes._agent_call("istem", kind="review") is None

    ev = _events("agent_yetki_reddi")
    assert len(ev) == 1, "yetki reddi KENDİ olayını basmalı — ham_stdout içinde gömülü kalmamalı"
    assert ev[0]["kind"] == "review" and ev[0]["http"] == 401 and ev[0]["returncode"] == 1
    assert len(ev[0]["detail"]) >= 20 and "geçici arıza DEĞİL" in ev[0]["detail"]   # YASA 4

    bos = _events("agent_call_empty")[-1]
    assert bos["cooldown_sinifi"] == "yetki_reddi"
    assert bos["ham_stdout"].startswith("HTTP 401"), "ham kanıt YERİNDE KALIR (v193 sözleşmesi)"

    # BEDEL ÖLÇÜLÜR (bedel yasası): `review_fallback_empty` bu turda ARTIK BASILMIYOR. Kaybedilen
    # satırın gerekçesi olgusal olarak yanlıştı ("hat çalıştı, model sustu" — oysa hat yetki
    # katmanında reddedildi); yerine geçen olay aynı alanların üstüne `http`/`imza`/`returncode`
    # taşır, yani bu dalda hiçbir teşhis bilgisi KAYBOLMAZ.
    assert _events("review_fallback_empty") == [], \
        "401 'yedek model sustu' DEĞİLDİR — yanlış anlatan satır basılmamalı"
    for alan in ("kind", "model", "chain", "cooldown_s"):
        assert alan in ev[0], f"kaybolan `review_fallback_empty` satırının `{alan}` alanı taşınmalı"


def test_403_ve_ciplak_forbidden_ayni_sinifa_duser_kod_uydurulmaz(ajan, monkeypatch):
    """403 aynı sınıftır. Kod OKUNUR, UYDURULMAZ: gövdede 401/403 sayısı yoksa `http` None olur —
    "Unauthorized" metnine bakıp 401 yazmak ölçülmemiş bir sayı basmak olurdu (uydurma yasağı)."""
    ajan.sonuclar = [_Kosum(1, YETKI_403, "")]
    assert hermes._agent_call("istem", kind="review") is None
    assert _events("agent_yetki_reddi")[-1]["http"] == 403

    assert hermes._agent_yetki_reddi("Error: Unauthorized", "") == (None, "unauthorized")
    assert hermes._agent_yetki_reddi("HTTP 401: User not found.", "") == (401, "http 401")
    assert hermes._agent_yetki_reddi("her şey yolunda", "") is None
    assert hermes._agent_yetki_reddi(SUNUCU_500, "") is None


def test_yetki_reddinde_soguma_DUZ_penceredir_ustel_merdivene_binmez(ajan):
    """Yeniden deneme fırtınası YOK, ama 6 saatlik kota kilidi de YOK: iptal edilmiş anahtar bir
    kota olgusu değildir, `streak` artmamalı. Düz pencere = `BRAIN_COOLDOWN_BASE_S`."""
    ajan.sonuclar = [_Kosum(1, YETKI_401, "")]
    assert hermes._agent_call("istem", kind="review") is None

    rem = hermes.brain_cooldown("agent")
    assert 0 < rem <= hermes.BRAIN_COOLDOWN_BASE_S, f"düz kısa pencere beklenir (kalan={rem})"
    satir = store.read_json(hermes.BRAIN_COOLDOWN_FILE, {})["agent"]
    assert satir["streak"] == 0, "yetki reddi üstel havuz merdivenine BİNMEZ"
    assert _events("agent_call_empty")[-1]["cooldown_s"] <= hermes.BRAIN_COOLDOWN_BASE_S


def test_tek_modelli_zincirde_de_pencere_kurulur_yeniden_deneme_firtinasi_yok(ajan, monkeypatch):
    """KÖR NOKTA, ÖLÇÜLDÜ: `fallback_empty` dalı `len(models) > 1` ister. Yedeği ayarlanmamış bir
    zincirde 401 alınca ESKİ kod HİÇBİR soğuma yazmıyordu (`cooldown_sinifi=None`) — her poll aynı
    iptal edilmiş anahtarla yeni bir süreç doğururdu. Yetki sınıfı zincir uzunluğuna BAKMAZ."""
    monkeypatch.setattr(hermes.secrets, "get", lambda k: {"NOUS_MODEL": BIRINCI}.get(k))
    ajan.sonuclar = [_Kosum(1, YETKI_401, "")]
    assert hermes._agent_call("istem", kind="review") is None

    assert len(ajan.runs) == 1, "önkoşul: zincir TEK modelli"
    assert _events("agent_call_empty")[-1]["cooldown_sinifi"] == "yetki_reddi"
    assert hermes.brain_cooldown("agent") > 0, "tek modelli zincirde de pencere kurulmalı"


def test_REGRESYON_500_eski_sinifta_kalir_yetki_olayi_BASILMAZ(ajan):
    """POZİTİF KONTROLÜN İKİZİ: yetki imzası YOKSA davranış BİREBİR eski. 5xx geçici bir arızadır;
    onu yetki hükmü sınıfına almak, bu turun düzelttiği hatanın AYNASI olurdu."""
    ajan.sonuclar = [_Kosum(1, SUNUCU_500, "")]
    assert hermes._agent_call("istem", kind="review") is None

    assert _events("agent_yetki_reddi") == [], "5xx yetki reddi DEĞİLDİR"
    bos = _events("agent_call_empty")[-1]
    assert bos["cooldown_sinifi"] == "fallback_empty", "eski sınıf aynen korunur"
    assert _events("review_fallback_empty"), "eski olay da aynen korunur"
