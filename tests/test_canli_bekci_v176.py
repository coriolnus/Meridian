"""test_canli_bekci_v176.py — CANLI-STATE BEKÇİSİNİN İKİ ONARIMININ KAPSAM TESTLERİ.

VAKA (2026-08-02): `tests/conftest.py` KATMAN-2 bekçisi (`_no_live_state_writes`, mtime parmak izi)
`test_regime_patch::test_scheduler_flag_survives_publish_lag` teardown'unda `['bounds.yaml']` ile
düştü. Kök neden testler DEĞİLDİ — `state/bounds.yaml` ve `state/goal.yaml` GİT-İZLİ sözleşme
dosyalarıdır (dagit [1b] SSoT, c783442) ve ana checkout'ta paralel oturumların git işlemleri onları
REPO İÇERİĞİYLE BİREBİR yeniden yazıyordu (inode adliyesi: bounds.yaml doğum 18:01:21, yerinde
yeniden-yazım 18:06:34; son içerik .git/index blob'uyla birebir). mtime orada sızıntıyı değil git
trafiğini ölçüyordu. Testler ayrıca enstrümanlı tam tekrar koşumuyla aklandı (audit-hook + mtime
poller; 84 test ×2 yeşil, canlı bounds.yaml'a tek yazım denemesi yok). Avda ikinci gerçek açık
bulundu: aynı test gerçek kadans makinesini koşturup makinede KURULU gerçek hermes CLI'yi
başlatıyor, o da MERIDIAN_ROOT=ana-checkout sabitiyle bir MCP alt süreci doğuruyordu.

SINIFLAR: (1) "izli-dosya mtime yanlış-alarmı" — bekçiyi susturmaya götüren yanlış pozitif;
          (2) "gerçek-ajan-ikilisi kaçağı" — testin makinedeki kurulumu bulup süreç doğurması.
Bu dosya iki onarımın DAR olduğunu da ölçer: dedektör daraltılmadı (mtime kolu duruyor) ve
saplama testin kendi yamasının önüne geçmiyor.
"""
import os
import subprocess

import pytest

import tests.conftest as conftest
from meridian import hermes


def _fp_ile(monkeypatch, kok):
    """`_live_fingerprint`i SAHTE bir canlı köke bakacak şekilde koşturur.

    `_LIVE` modül GLOBALİDİR ve gerçek `state/`i gösterir: testin oraya dosya yazması, ölçmek
    istediği bekçiyi tam da ihlal etmek olurdu. `_LIVE_ROOT` (KATMAN-1 kancalarının kökü) BİLEREK
    değiştirilmez — tmp'ye yazım o kancalara zaten görünmez ve kanca davranışı bu dosyanın konusu
    değildir."""
    monkeypatch.setattr(conftest, "_LIVE", kok)
    return conftest._live_fingerprint()


# ================= (1) İZLİ SÖZLEŞME DOSYALARI: PARMAK İZİ İÇERİKTİR ==============================
def test_a_izli_dosyada_ayni_icerik_yeniden_yazimi_parmak_izini_oynatmaz(tmp_path, monkeypatch):
    """Git'in repo→state restorasyonunun birebir taklidi: içerik AYNI, mtime OYNAR → alarm YOK."""
    kok = tmp_path / "sahte_state"
    kok.mkdir()
    hedef = kok / "bounds.yaml"
    icerik = "entry:\n  min_score: [50, 80]\n"
    hedef.write_text(icerik)
    once = _fp_ile(monkeypatch, kok)
    mtime0 = hedef.stat().st_mtime_ns

    hedef.write_text(icerik)                      # git checkout/restore: aynı bayt, yeni damga
    os.utime(hedef, ns=(mtime0 + 5_000_000_000, mtime0 + 5_000_000_000))
    assert hedef.stat().st_mtime_ns != mtime0, "mtime OYNAMADI — test hiçbir şey ölçmüyor olurdu"

    sonra = _fp_ile(monkeypatch, kok)
    assert sonra["bounds.yaml"] == once["bounds.yaml"], (
        "izli dosyanın parmak izi mtime'la oynadı — yanlış alarm sınıfı geri döndü")
    assert sonra == once


def test_b_izli_dosyada_icerik_degisirse_parmak_izi_degisir(tmp_path, monkeypatch):
    """Onarımın SINIRI: bekçi gerçek bozulmayı hâlâ görmeli, yoksa iki izli dosya kör noktaya döner."""
    kok = tmp_path / "sahte_state"
    kok.mkdir()
    hedef = kok / "goal.yaml"
    hedef.write_text("hedef: 0.20\n")
    once = _fp_ile(monkeypatch, kok)
    hedef.write_text("hedef: 0.99\n")             # gerçek içerik farkı (bir testin yazımı gibi)
    sonra = _fp_ile(monkeypatch, kok)
    assert sonra["goal.yaml"] != once["goal.yaml"]


def test_c_izli_olmayan_dosyada_mtime_dedektoru_daraltilmadi(tmp_path, monkeypatch):
    """Onarım YALNIZ iki dosyaya özgüdür. Defterde içerik aynı kalıp mtime oynaması, dosyanın
    yeniden yazıldığı anlamına gelir ve bu sınıf (aynı satırı yeniden yazan bir sızıntı) elenirse
    KATMAN-2'nin asıl işi kaybolur — bu yüzden burada alarm BEKLENİR."""
    kok = tmp_path / "sahte_state"
    kok.mkdir()
    hedef = kok / "events.jsonl"
    hedef.write_text('{"event":"x"}\n')
    once = _fp_ile(monkeypatch, kok)
    st = hedef.stat()
    os.utime(hedef, ns=(st.st_mtime_ns + 5_000_000_000, st.st_mtime_ns + 5_000_000_000))
    sonra = _fp_ile(monkeypatch, kok)
    assert sonra["events.jsonl"] != once["events.jsonl"], (
        "mtime kolu da içeriğe çevrilmiş — dedektör onarımın kapsamı dışında daraltıldı")


def test_c2_izli_ad_alt_dizinde_muaf_degildir(tmp_path, monkeypatch):
    """Muafiyet GÖRELİ YOLA bağlıdır: `bars/bounds.yaml` git-izli değildir, mtime'la izlenir.
    Muafiyeti `p.name`e bağlamak, alt dizine düşen bir sızıntıya kalıcı kör nokta açardı."""
    kok = tmp_path / "sahte_state"
    (kok / "bars").mkdir(parents=True)
    hedef = kok / "bars" / "bounds.yaml"
    hedef.write_text("ayni\n")
    once = _fp_ile(monkeypatch, kok)
    hedef.write_text("ayni\n")
    st = hedef.stat()
    os.utime(hedef, ns=(st.st_mtime_ns + 5_000_000_000, st.st_mtime_ns + 5_000_000_000))
    sonra = _fp_ile(monkeypatch, kok)
    assert sonra["bars/bounds.yaml"] != once["bars/bounds.yaml"]


# ================= (2) GERÇEK AJAN İKİLİSİ: VARSAYILAN KAPALI =====================================
def test_d_yamasiz_testte_ikili_yok_ve_surec_dogmaz(sandbox_state, monkeypatch):
    """Bu test BİLEREK hiçbir `_hermes_bin` yaması yapmaz — ölçtüğü şey conftest'in varsayılanı.

    `subprocess.run` AssertionError atan bir saplamayla değiştirilir: "süreç doğmadı" iddiası ancak
    doğduğunda GÜRÜLTÜLÜ düşen bir dünyada bir şey ölçer (sessiz sayaç, kaçırılan doğumu yeşil
    gösterirdi). v169'un sahte-dünya kurulumundan yalnız İLGİLİ saplamalar alınmıştır: skill
    senkronu ve havuz okuması gerçek dosyalara/ağa gitmesin, sırlar makineden okunmasın."""
    monkeypatch.setattr(hermes, "sync_agent_skills", lambda: None)
    monkeypatch.setattr(hermes, "_pool_exhausted", lambda: None)
    monkeypatch.setattr(hermes.secrets, "get", lambda k: None)

    def _dogmasin(cmd, **kw):
        raise AssertionError(f"GERÇEK ALT SÜREÇ DOĞDU: {cmd}")

    monkeypatch.setattr(subprocess, "run", _dogmasin)
    assert hermes._hermes_bin() is None, "makinede kurulu gerçek hermes CLI testlere sızıyor"
    assert hermes._agent_call("soru", kind="t") is None      # dürüst fail-open, süreçsiz


def test_d2_yamasiz_testte_nous_yerel_degil_ve_anahtarsiz_hazir_degil(monkeypatch):
    """Kaçağın TÜREVLERİ: `_nous_local` ve `_provider_ready` ikiliye bakar. İkili makineye bağlı
    kalsaydı bu iki yanıt da makineye bağlı olurdu — geçtiğinde hiçbir şey kanıtlamayan testler."""
    monkeypatch.setattr(hermes.secrets, "get", lambda k: None)
    assert hermes._nous_local() is False
    assert hermes._provider_ready("nous") is False


def test_e_testin_kendi_yamasi_saplamanin_ustune_yazar(sandbox_state, monkeypatch):
    """v169/v13/v96 SÖZLEŞMESİ KIRILMADI: sahte ikili isteyen test onu alır ve `_agent_call` süreç
    kuruluşuna kadar ilerler. Autouse saplaması test-düzeyi monkeypatch'ten ÖNCE kurulduğu için
    testin yaması kazanır; bunu doğrulamak, onarımın komşu 20+ testi sessizce kısırlaştırmadığını
    doğrulamaktır."""
    monkeypatch.setattr(hermes, "_hermes_bin", lambda: "/sahte/hermes")
    monkeypatch.setattr(hermes, "sync_agent_skills", lambda: None)
    monkeypatch.setattr(hermes, "_pool_exhausted", lambda: None)
    monkeypatch.setattr(hermes.secrets, "get", lambda k: None)
    monkeypatch.setattr(hermes, "_quiet_flag_ok", True)      # süreç-içi bayrak öğrenmesi sızmasın
    assert hermes._hermes_bin() == "/sahte/hermes"

    cagrilar = []

    class _Sonuc:
        returncode = 0
        stdout = "cevap gövdesi\nMessages: 4 (1 user, 2 tool calls)"
        stderr = ""

    monkeypatch.setattr(subprocess, "run", lambda cmd, **kw: cagrilar.append(list(cmd)) or _Sonuc())
    assert hermes._agent_call("soru", kind="t") == _Sonuc.stdout
    assert len(cagrilar) == 1 and cagrilar[0][0] == "/sahte/hermes"


def test_e2_saplama_yalniz_kesif_kolunu_keser(tmp_path, monkeypatch):
    """Saplamanın DAR olduğu ölçülür: testin ENJEKTE ettiği `HERMES_LOCAL_BIN` onurlandırılır
    (üç mevcut test bu yolu kullanır ve beklentileri değişmedi), var olmayan yol reddedilir."""
    sahte = tmp_path / "hermes"
    sahte.write_text("#!/bin/sh\n")
    sahte.chmod(0o755)
    monkeypatch.setenv("HERMES_LOCAL_BIN", str(sahte))
    assert hermes._hermes_bin() == str(sahte)
    monkeypatch.setenv("HERMES_LOCAL_BIN", str(tmp_path / "yok"))
    assert hermes._hermes_bin() is None


def test_f_asil_cozumleyici_fikstur_uzerinden_erisilebilir(hermes_bin_cozumleyici_asil):
    """Bilinçli istisnanın kapısı: fikstür SAPLAMAYI değil ÜRETİM fonksiyonunu vermeli, yoksa
    çözümleyiciyi sınayan test kendi saplamasını ölçerdi (yanlış-yeşil sınıfı)."""
    assert hermes_bin_cozumleyici_asil is not hermes._hermes_bin
    assert getattr(hermes_bin_cozumleyici_asil, "__name__", "") == "_hermes_bin"
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(hermes, "_hermes_bin", hermes_bin_cozumleyici_asil)
        assert hermes._hermes_bin.__module__ == "meridian.hermes"
