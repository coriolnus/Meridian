"""test_hermes_dayaniklilik_v169.py — HERMES-CLI YAPILANDIRMA DAYANIKLILIĞI (ROADMAP §1 (a)/(c)/(d)).

CANLI VAKA (2026-08-02, 6 gün sessiz ölüm): A1 taşınmasında `~/.hermes` yapılandırması taşınmadı
(hiçbir dağıtım kanalının parçası değildi). Yerel CLI her çağrıda ilk-koşum rehberini basıp
`exit(1)` etti — AĞA HİÇ ÇIKMADAN. Üç kusur birden görünmez kaldı:
  (a) senkron TEK ATIMLIKTI (yalnız operatör panodan anahtar girince koşar) → kendini onarmadı;
  (c) rehber çıktısı `agent_call_empty` sayıldı → "kota" ile "yapılandırmasız" tek satırda birleşti
      ve havuz soğuması (429-backoff) yapılandırmasızlıkla kirlendi;
  (d) RPD bütçesi ağa çıkmamış çağrıları saydı → ölü zincir 150/150'yi 06:19'da yaktı, GERÇEK Gemini
      kotası el değmemişken aday incelemesi tüm gün bütçe-reddi yedi.

İMZALAR UYDURULMADI, ÖLÇÜLDÜ (kurulu hermes-agent kaynağı, 2026-08-02):
  hermes_cli/main.py `cmd_chat` ilk-koşum bekçisi + hermes_cli/setup.py
  `print_noninteractive_setup_guidance`. Aşağıdaki `CANLI_REHBER` o metnin birebir iskeletidir.
`config get` sözleşmesi de ölçüldü (canlı CLI): ayarlı → stdout=çıplak değer/rc=0; ayarsız →
stdout BOŞ + stderr "Config key not set: <key>"/rc=1.

Ağ/gerçek alt süreç YOK: `subprocess.run` saplı, `_hermes_bin` sahte, state sandbox'ta.
"""
import inspect
import subprocess

import pytest

from meridian import hermes, hermes_runtime as hr, store

# Canlı CLI'nin yapılandırmasız çıktısının iskeleti (üç imzayı da taşır — canlıda böyle geldi).
CANLI_REHBER = (
    "\nIt looks like Hermes isn't configured yet -- no API keys or providers found.\n"
    "\n  Run:  hermes setup\n"
    "\n⚕ Hermes Setup — Non-interactive mode\n"
    "No interactive TTY detected for the first-run setup prompt.\n"
    "Configure Hermes using environment variables or config commands:\n"
    "  hermes config set model.provider custom\n"
    "  hermes config set model.default your-model-name\n"
    "\nOr set OPENROUTER_API_KEY / OPENAI_API_KEY in your environment.\n"
    "Run 'hermes setup' in an interactive terminal to use the full wizard.\n"
)
BOS_OTURUM = "╭─╮\n╰─╯\nMessages:       1 (1 user, 0 tool calls)"     # gerçek boş cevap (kota/arka uç)


class _Sonuc:
    def __init__(self, rc=0, stdout="", stderr=""):
        self.returncode, self.stdout, self.stderr = rc, stdout, stderr


def _olaylar(ad):
    return [r for r in store.read_jsonl("events.jsonl") if r.get("event") == ad]


def _butce():
    return store.read_json(hermes.AGENT_BUDGET_FILE, {})


@pytest.fixture
def ajan(sandbox_state, monkeypatch):
    """`_agent_call` için sahte dünya: ikili 'kurulu', skill senkronu ve havuz okuması saplı.

    `_pool_exhausted` BİLEREK "gemini" döndürür — yani havuz "tükendim" DİYOR. Yapılandırmasız
    yolun soğuma yazmadığını ancak havuz tükenmişken kanıtlayabiliriz: soğumanın olmadığı bir
    dünyada "soğuma yazılmadı" iddiası hiçbir şey ölçmez."""
    monkeypatch.setattr(hermes, "_hermes_bin", lambda: "/sahte/hermes")
    monkeypatch.setattr(hermes, "sync_agent_skills", lambda: None)
    monkeypatch.setattr(hermes, "_pool_exhausted", lambda: "gemini")
    monkeypatch.setattr(hermes.secrets, "get", lambda k: None)          # zincir tek elemanlı
    monkeypatch.setattr(hermes, "_quiet_flag_ok", True)                 # süreç-içi öğrenme sızmasın
    return sandbox_state


def _sap_surec(monkeypatch, sonuc):
    cagrilar = []
    monkeypatch.setattr(subprocess, "run",
                        lambda cmd, **kw: cagrilar.append(list(cmd)) or sonuc)
    return cagrilar


# ================= (c) YAPILANDIRMASIZ ≠ KOTA =====================================================
def test_c1_yapilandirmasiz_imza_ayri_olay_basar_soguma_yazmaz(ajan, monkeypatch):
    """Rehber çıktısı → `agent_unconfigured` (ayrı sınıf), `agent_call_empty` YOK, havuz soğuması
    YAZILMAZ (havuz tükenmiş dese bile: yapılandırmasızlık 429-backoff'unu kirletemez)."""
    _sap_surec(monkeypatch, _Sonuc(rc=1, stdout=CANLI_REHBER))
    assert hermes._agent_call("soru", kind="review") is None
    ev = _olaylar("agent_unconfigured")
    assert len(ev) == 1, f"tek olay bekleniyordu: {ev}"
    e = ev[0]
    assert e["level"] == "warn"
    assert e["imza"] in hermes.AGENT_UNCONFIGURED_SIGNS
    assert e["imza"] == "config set model.default"          # tuple sırasındaki ilk eşleşme
    assert e["kind"] == "review" and e["returncode"] == 1
    assert e["cooldown_yazildi"] is False and len(e["detail"]) >= 20
    assert _olaylar("agent_call_empty") == [], "yapılandırmasızlık kota gibi kaydedilemez"
    assert hermes.brain_cooldown("agent") == 0.0, "soğuma YAZILDI — 429-backoff kirlendi"


def test_c2_yalniz_openrouter_imzasi_da_yakalanir(ajan, monkeypatch):
    """Rehber metni değişse bile env-değişkeni kolu tek başına sınıflandırmaya yeter."""
    _sap_surec(monkeypatch, _Sonuc(rc=1, stderr="Or set OPENROUTER_API_KEY in your environment."))
    assert hermes._agent_call("soru", kind="proposal") is None
    assert _olaylar("agent_unconfigured")[0]["imza"] == "OPENROUTER_API_KEY"   # stderr de taranır


def test_c3_yapilandirmasiz_model_zincirini_tuketmez(sandbox_state, monkeypatch):
    """İki modelli zincirde bile TEK süreç doğar: yapılandırmasız bir CLI ikinci modelde de
    yapılandırmasızdır — denemek ikinci bir süreci ve ikinci bir bütçe birimini boşuna yakardı."""
    monkeypatch.setattr(hermes, "_hermes_bin", lambda: "/sahte/hermes")
    monkeypatch.setattr(hermes, "sync_agent_skills", lambda: None)
    monkeypatch.setattr(hermes, "_pool_exhausted", lambda: None)
    monkeypatch.setattr(hermes.secrets, "get",
                        lambda k: {"NOUS_MODEL": "birincil-x", "NOUS_FALLBACK_MODEL": "yedek-y"}.get(k))
    cagrilar = _sap_surec(monkeypatch, _Sonuc(rc=1, stdout=CANLI_REHBER))
    assert hermes._agent_call("soru", kind="t") is None
    assert len(cagrilar) == 1 and "birincil-x" in cagrilar[0]
    assert _butce().get("day", 0) == 0                      # iki değil, SIFIR birim harcandı


def test_c4_dolu_cevapta_imza_taramasi_yapilmaz(ajan, monkeypatch):
    """SINIRIN ÖTEKİ YÜZÜ: konuşan bir model yapılandırmadan söz edebilir. İmza taraması yalnız
    BOŞ-cevap yolundadır — dolu cevabı 'yapılandırmasız' ilan etmek modeli susturmak olurdu."""
    dolu = ('OPENROUTER_API_KEY hakkında sorduğun şey şu: ...\n'
            'Messages: 4 (1 user, 2 tool calls)')
    _sap_surec(monkeypatch, _Sonuc(rc=0, stdout=dolu))
    assert hermes._agent_call("soru", kind="t") == dolu
    assert _olaylar("agent_unconfigured") == []
    assert _butce()["day"] == 1                              # gerçek cevap bütçeden düşer


# ================= (d) BÜTÇE: AĞA ÇIKMAYAN ÇAĞRI SAYILMAZ ========================================
def test_d1_yapilandirmasiz_cagri_butceden_dusmez(ajan, monkeypatch):
    """RPD sayacı sağlayıcı kotasını korur; yapılandırmasız çağrı o kotaya HİÇ dokunmadı → iade.
    RPM damgası BİLEREK KALIR: o damga yerel süreç-doğurma hızının tek freni ve süreç GERÇEKTEN
    doğdu (ikisini birden iade etmek, ölü CLI'yi sınırsız çalıştırmanın önünü açardı)."""
    _sap_surec(monkeypatch, _Sonuc(rc=1, stdout=CANLI_REHBER))
    assert hermes._agent_call("soru", kind="t") is None
    st = _butce()
    assert st["day"] == 0, "ağa çıkmamış çağrı RPD sayacını yaktı"
    assert len(st["minute"]) == 1, "RPM damgası iade edilmemeli (süreç-doğurma freni)"
    assert _olaylar("agent_unconfigured")[0]["butce_iade"] is True


def test_d2_gercek_bos_cevap_ESKI_davranisi_korur(ajan, monkeypatch):
    """REGRESYON KAPISI: imzasız boş cevap (gerçek kota/arka uç arızası) hiç değişmedi —
    `agent_call_empty` + havuz soğuması + harcanmış bütçe."""
    _sap_surec(monkeypatch, _Sonuc(rc=0, stdout=BOS_OTURUM))
    assert hermes._agent_call("soru", kind="t") is None
    ev = _olaylar("agent_call_empty")
    assert len(ev) == 1 and ev[0]["pool_exhausted"] == "gemini"
    assert ev[0]["cooldown_s"] > 0 and hermes.brain_cooldown("agent") > 0
    assert _olaylar("agent_unconfigured") == []
    assert _butce()["day"] == 1, "gerçek ağ denemesi SAYILIR (kota koruması amaç)"


def test_d3_iade_sayaci_negatife_dusuremez(ajan, monkeypatch):
    """İade yarış-güvenli olduğu kadar TABANLI da olmalı: gün damgası bugüne ait değilken ya da
    sayaç sıfırken iade YOKTUR (dünün kaydını eksiye çekmek, bugünü iki kez muhasebe etmektir)."""
    store.write_json(hermes.AGENT_BUDGET_FILE, {"date": "1999-01-01", "day": 7, "minute": []})
    assert hermes._agent_budget_refund("test") is False
    assert _butce()["day"] == 7                              # dünün sayacına DOKUNULMADI
    import datetime as _dt
    store.write_json(hermes.AGENT_BUDGET_FILE,
                     {"date": str(_dt.date.today()), "day": 0, "minute": []})
    assert hermes._agent_budget_refund("test") is False
    assert _butce()["day"] == 0


# ================= (a) CLI YAPILANDIRMA ÖLÇÜMÜ ===================================================
@pytest.mark.parametrize("rc,out,err,bekleme", [
    (0, "gemini-3.5-flash\n", "", ("gemini-3.5-flash", "ayarli")),
    (1, "", "Config key not set: model.default\n", (None, "ayarsiz")),
    (1, "", "Traceback ... ImportError\n", (None, "olculemedi")),   # imzasız hata = BİLİNMİYOR
    (0, "", "", (None, "olculemedi")),
])
def test_a1_config_get_sozlesmesi_olculdu(monkeypatch, rc, out, err, bekleme):
    """CLI'nin ÖLÇÜLMÜŞ sözleşmesi kilitlenir. Kritik satır üçüncüsü: imzasız bir hata "ayarsız"
    sayılsaydı, bozuk bir kurulum "yapılandırmasız" diye okunur ve ÇALIŞAN bir config'i yeniden
    yazdırırdı — kapının önlemeye çalıştığı zararın ta kendisi."""
    monkeypatch.setattr(subprocess, "run", lambda cmd, **kw: _Sonuc(rc, out, err))
    assert hermes._agent_cfg_get("/sahte/hermes", "model.default") == bekleme


def test_a2_config_get_istisnasi_olculemedi_der(monkeypatch):
    def _patla(*a, **k):
        raise subprocess.TimeoutExpired(cmd="hermes", timeout=30)
    monkeypatch.setattr(subprocess, "run", _patla)
    assert hermes._agent_cfg_get("/sahte/hermes", "model.default") == (None, "olculemedi")


def _cli_durumu(monkeypatch, tmp_path, *, model_sonuc, env_satiri):
    home = tmp_path / ".hermes"
    home.mkdir(exist_ok=True)
    if env_satiri is not None:
        (home / ".env").write_text(env_satiri)
    import os as _os
    monkeypatch.setattr(_os.path, "expanduser",
                        lambda p: str(home) if p == "~/.hermes" else p)
    monkeypatch.setattr(hermes, "_hermes_bin", lambda: "/sahte/hermes")
    monkeypatch.setattr(subprocess, "run", lambda cmd, **kw: model_sonuc)
    return hermes.local_agent_config_state()


def test_a3_cli_modelsiz_ve_anahtarsiz_YAPILANDIRILMAMIS(monkeypatch, tmp_path):
    """Canlı vakanın tam hâli: config ayarsız + .env yok → False, ve NEDEN iki kanalı da adıyla sayar."""
    d = _cli_durumu(monkeypatch, tmp_path,
                    model_sonuc=_Sonuc(1, "", "Config key not set: model.default"), env_satiri=None)
    assert d["yapilandirilmis"] is False
    assert "model.default ayarsız" in d["neden"] and ".env" in d["neden"]
    assert d["env_anahtar"] is False and d["model"] is None


def test_a4_model_var_anahtar_yok_da_YAPILANDIRILMAMIS(monkeypatch, tmp_path):
    d = _cli_durumu(monkeypatch, tmp_path, model_sonuc=_Sonuc(0, "gemini-3.5-flash\n"),
                    env_satiri="BASKA_SATIR=1\nGEMINI_API_KEY=\n")     # BOŞ değer anahtar değildir
    assert d["yapilandirilmis"] is False and d["model"] == "gemini-3.5-flash"


def test_a5_iki_kanal_da_dolu_ise_YAPILANDIRILMIS(monkeypatch, tmp_path):
    d = _cli_durumu(monkeypatch, tmp_path, model_sonuc=_Sonuc(0, "gemini-3.5-flash\n"),
                    env_satiri="export GEMINI_API_KEY='gk-1'\n")       # export/tırnak biçimi de sayılır
    assert d["yapilandirilmis"] is True and d["neden"] is None and d["env_anahtar"] is True


def test_a6_olculemeyen_model_HUKUM_VERMEZ(monkeypatch, tmp_path):
    """UYDURMA YASAĞI: ölçüm düştüğünde hüküm None'dur — ne "bozuk" ne "sağlam"."""
    d = _cli_durumu(monkeypatch, tmp_path, model_sonuc=_Sonuc(1, "", "kernel panic"),
                    env_satiri="GEMINI_API_KEY=gk-1\n")
    assert d["yapilandirilmis"] is None and "olculemedi" in d["neden"]


def test_a7_ikili_yoksa_olculemedi(monkeypatch):
    monkeypatch.setattr(hermes, "_hermes_bin", lambda: None)
    d = hermes.local_agent_config_state()
    assert d["kurulu"] is False and d["yapilandirilmis"] is None and d["neden"]


# ================= (a) AÇILIŞ SENKRON-DOĞRULAMASI ================================================
@pytest.fixture
def acilis(sandbox_state, monkeypatch):
    """Açılış kapısının sahte dünyası: senkron çağrıları KAYDEDİLİR, hiçbir şey çalıştırılmaz."""
    cagrilar = []
    monkeypatch.setattr(hermes, "sync_local_agent_gemini",
                        lambda enable: cagrilar.append(enable) or
                        {"ok": True, "detail": "yerel ajan Gemini'a geçti · m",
                         "senkron_ts": "2026-08-02T06:00:00+00:00"})
    return cagrilar


def test_a8_anahtar_dolu_cli_modelsiz_RESENKRON_kosar(acilis, monkeypatch):
    monkeypatch.setattr(hr.secrets, "get", lambda k: "gk-1" if k == "GEMINI_API_KEY" else None)
    monkeypatch.setattr(hermes, "local_agent_config_state",
                        lambda: {"kurulu": True, "yapilandirilmis": False, "model": None,
                                 "model_durum": "ayarsiz", "env_anahtar": False,
                                 "neden": "model.default ayarsız"})
    res = hr._acilis_senkron_dogrula()
    assert acilis == [True], "yapılandırmasız CLI + dolu anahtar → senkron KOŞMALI"
    assert res["yapildi"] is True and res["ok"] is True
    ev = _olaylar("local_agent_resynced")
    assert len(ev) == 1 and ev[0]["neden"] == "model.default ayarsız"
    assert ev[0]["senkron_ts"] == res["senkron_ts"] == "2026-08-02T06:00:00+00:00"


def test_a9_anahtar_bos_ise_HIC_cagri_yok(acilis, monkeypatch):
    """Anahtarsız senkron, olmayan bir anahtarı taşımaya çalışmaktır: ölçüm bile yapılmaz."""
    monkeypatch.setattr(hr.secrets, "get", lambda k: None)
    olctu = []
    monkeypatch.setattr(hermes, "local_agent_config_state",
                        lambda: olctu.append(1) or {"yapilandirilmis": False})
    res = hr._acilis_senkron_dogrula()
    assert acilis == [] and olctu == []
    assert res["yapildi"] is False and res["sebep"] == "gemini_anahtari_yok"
    assert res["senkron_ts"]


def test_a10_cli_zaten_yapilandirilmissa_dokunulmaz(acilis, monkeypatch):
    monkeypatch.setattr(hr.secrets, "get", lambda k: "gk-1")
    monkeypatch.setattr(hermes, "local_agent_config_state",
                        lambda: {"kurulu": True, "yapilandirilmis": True, "model": "gemini-3.5-flash",
                                 "model_durum": "ayarli", "env_anahtar": True, "neden": None})
    res = hr._acilis_senkron_dogrula()
    assert acilis == [] and res["sebep"] == "cli_zaten_yapilandirilmis"
    assert res["model"] == "gemini-3.5-flash" and _olaylar("local_agent_resynced") == []


def test_a11_olculemedi_ONARMAZ_ama_SUSMAZ(acilis, monkeypatch):
    monkeypatch.setattr(hr.secrets, "get", lambda k: "gk-1")
    monkeypatch.setattr(hermes, "local_agent_config_state",
                        lambda: {"kurulu": True, "yapilandirilmis": None, "model": None,
                                 "model_durum": "olculemedi", "env_anahtar": None,
                                 "neden": "model ölçümü=olculemedi · env ölçümü=okunamadı"})
    res = hr._acilis_senkron_dogrula()
    assert acilis == [], "ölçülemeyen kurulum yeniden yapılandırılmaz"
    assert res["sebep"] == "olculemedi"
    ev = _olaylar("local_agent_config_olculemedi")
    assert len(ev) == 1 and ev[0]["level"] == "warn" and len(ev[0]["detail"]) >= 20


def test_a12_senkron_istisnasi_dongu_kirmaz_ve_sessiz_kalmaz(sandbox_state, monkeypatch):
    monkeypatch.setattr(hr.secrets, "get", lambda k: "gk-1")
    def _patla():
        raise OSError("~/.hermes okunamadı")
    monkeypatch.setattr(hermes, "local_agent_config_state", _patla)
    res = hr._acilis_senkron_dogrula()                      # istisna SIZMAZ
    assert res["yapildi"] is False and "OSError" in res["sebep"]
    assert len(_olaylar("local_agent_acilis_senkron_hatasi")) == 1


# ================= (b) SENKRON SONUCU ZAMAN DAMGALI ==============================================
def test_b1_senkron_HER_donuste_ts_tasir(sandbox_state, monkeypatch, tmp_path):
    """Damgasız bir durum satırı bayatladığını kendisi söyleyemez (canlı vaka: 6 gün eski OSError
    taze hüküm gibi okundu). Reddedilen yollar DA damgalanır — asıl bayatlayan onlardır."""
    monkeypatch.setattr(hermes, "_hermes_bin", lambda: None)
    yok = hermes.sync_local_agent_gemini(True)
    assert yok["ok"] is False and yok["senkron_ts"].startswith("20") and "T" in yok["senkron_ts"]

    home = tmp_path / ".hermes"; home.mkdir()
    import os as _os
    monkeypatch.setattr(_os.path, "expanduser", lambda p: str(home) if p == "~/.hermes" else p)
    monkeypatch.setattr(hermes, "_hermes_bin", lambda: "/sahte/hermes")
    monkeypatch.setattr(hermes.secrets, "get", lambda k: None)          # anahtar YOK
    bos = hermes.sync_local_agent_gemini(True)
    assert bos["ok"] is False and "GEMINI_API_KEY" in bos["detail"] and bos["senkron_ts"]

    monkeypatch.setattr(hermes.secrets, "get",
                        lambda k: {"GEMINI_API_KEY": "gk-1"}.get(k))
    monkeypatch.setattr(subprocess, "run", lambda cmd, **kw: _Sonuc(0, "nous\n"))
    ok = hermes.sync_local_agent_gemini(True)
    assert ok["ok"] is True and ok["senkron_ts"]
    assert (home / ".env").read_text().count("GEMINI_API_KEY=") == 1
    ev = _olaylar("local_agent_switched")
    assert ev and ev[-1]["senkron_ts"] == ok["senkron_ts"]              # olay ile dönüş aynı damga


# ================= EK İŞ: CLI SESSİZ MODU (`-Q`) =================================================
# KÖK NEDEN: `-q` SORGU bayrağıdır (`-q QUERY`), sessizlik AYRI bayraktır (`-Q/--quiet`). `-Q`suz
# stdout banner + "Query: <istem yankısı>" + oturum özeti taşır; `_extract_json` YANKININ içindeki
# bağlam-JSON'unu yakalar (canlı kanıt: candidate_review_empty_parse · parse_ok=true ·
# on_filtre_n=0 · ham_ilk="Query: You advise..."). Model doğru cevap verirken kayıt boş çıkıyordu.
def test_q1_chat_komutu_sessiz_bayragi_tasir(ajan, monkeypatch):
    """Komut satırı `-Q` TAŞIR ve `-q` istemi ayrı taşımaya devam eder (ikisi farklı iştir)."""
    cagrilar = _sap_surec(monkeypatch, _Sonuc(0, "cevap\nMessages: 2 (1 user, 0 tool calls)"))
    assert hermes._agent_call("İSTEM", preload=("vcp-screener",), kind="t")
    cmd = cagrilar[0]
    assert hermes.QUIET_FLAG == "-Q" and "-Q" in cmd
    assert cmd[cmd.index("-q") + 1] == "İSTEM"                 # -q hâlâ SORGU bayrağı
    assert cmd.index("-Q") < cmd.index("-q")
    assert "--accept-hooks" in cmd and "-s" in cmd             # eski bayraklar korundu


def test_q2_Q_tanimayan_CLI_de_bir_kez_uyarip_bayraksiz_yeniden_dener(ajan, monkeypatch):
    """GERİYE-UYUM: `-Q` bilinmeyen bayraksa TEK fallback — uyarı (sessiz değil) + bayraksız tekrar.
    Bayrak hatası argparse'ta düşer, yani AĞA ÇIKMAZ: net bütçe tüketimi 1 birimdir, 2 değil."""
    sonuclar = [_Sonuc(2, "", "hermes: error: unrecognized arguments: -Q"),
                _Sonuc(0, "İYİ CEVAP\nMessages: 2 (1 user, 0 tool calls)")]
    cagrilar = []
    monkeypatch.setattr(subprocess, "run",
                        lambda cmd, **kw: cagrilar.append(list(cmd)) or sonuclar[len(cagrilar) - 1])
    assert "İYİ CEVAP" in hermes._agent_call("soru", kind="t")
    assert "-Q" in cagrilar[0] and "-Q" not in cagrilar[1]     # ikinci deneme bayraksız
    ev = _olaylar("agent_cli_flag_unsupported")
    assert len(ev) == 1 and ev[0]["level"] == "warn" and ev[0]["flag"] == "-Q"
    assert "-Q" in ev[0]["stderr_ilk"] and len(ev[0]["detail"]) >= 20
    assert _butce()["day"] == 1, "bayrak hatası ağa çıkmadı — iki birim yakılamaz"


def test_q3_desteklenmedigi_OGRENILIR_uyari_tekrarlanmaz(ajan, monkeypatch):
    """Bir kez öğrenilir: sonraki çağrılar `-Q`suz başlar (her çağrıda çift süreç ödenmez) ve
    uyarı TEKRARLANMAZ (aynı olguyu poll başına bağırmak defteri kör eder)."""
    cagrilar = []

    def _run(cmd, **kw):
        cagrilar.append(list(cmd))
        if "-Q" in cmd:
            return _Sonuc(2, "", "hermes: error: unrecognized arguments: -Q")
        return _Sonuc(0, "cevap\nMessages: 2 (1 user, 0 tool calls)")
    monkeypatch.setattr(subprocess, "run", _run)
    assert hermes._agent_call("bir", kind="t")
    assert hermes._agent_call("iki", kind="t")
    assert [("-Q" in c) for c in cagrilar] == [True, False, False]
    assert len(_olaylar("agent_cli_flag_unsupported")) == 1


def test_q4_baska_bir_bilinmeyen_bayrak_Q_yu_SUCLAMAZ(ajan, monkeypatch):
    """Sınır: hata başka bir bayrağa aitse `-Q` devre dışı bırakılmaz — yanlış teşhis, çalışan bir
    sessiz modu sessizce kapatır ve canlı vakayı geri getirirdi."""
    _sap_surec(monkeypatch, _Sonuc(2, "", "hermes: error: unrecognized arguments: --sahte"))
    assert hermes._agent_call("soru", kind="t") is None        # boş cevap yolu (eski davranış)
    assert _olaylar("agent_cli_flag_unsupported") == []
    assert hermes._quiet_flag_ok is True


def test_q6_sessiz_modda_BOS_stdout_bos_cevaptir(ajan, monkeypatch):
    """`-Q` oturum özetini bastırır → `Messages: N` sinyali YOK. Boşluk ölçütü buna göre genişledi:
    rc=0 + boş stdout (hata stderr'e gider) artık BOŞ sayılır. Aksi hâlde cevapsız bir koşum 'dolu
    cevap' diye geri döner, `agent_call_empty` hiç yazılmaz ve ayrıştırıcı boş metinle uğraşırdı."""
    _sap_surec(monkeypatch, _Sonuc(0, "  \n", "Error: provider 4xx"))
    assert hermes._agent_call("soru", kind="t") is None
    assert len(_olaylar("agent_call_empty")) == 1


def test_q7_ozetsiz_dolu_cevap_telemetriyi_SEYRELTMEZ(ajan, monkeypatch):
    """Sessiz modda araç sayısı ölçülemez. Ölçülemeyen çağrı `calls`a katılmaz (oran seyrelmez) ama
    KAYBOLMAZ da: ayrı sayaçta durur ve `integrations_status` onu yayınlar."""
    _sap_surec(monkeypatch, _Sonuc(0, '{"ok": 1}'))          # özet satırı YOK → tool_calls = -1
    assert hermes._agent_call("soru", kind="t") == '{"ok": 1}'
    st = store.read_json("agent_tooluse.json", {})
    assert st["olculemeyen"] == 1 and st["calls"] == 0
    monkeypatch.setattr(hermes, "pool_health", lambda: {})
    monkeypatch.setattr(hermes, "_pool_exhausted", lambda: None)
    monkeypatch.setattr(hermes, "AGENT_CONFIG", "/olmayan/config.yaml")
    tu = hermes.integrations_status()["tool_use"]
    assert tu["olculemeyen"] == 1 and tu["rate"] is None      # oran UYDURULMAZ (payda 0)


def test_q5_chat_kurulumu_TEK_yerde():
    """Envanter kaynakta kilitli: CLI `chat` komutunu kuran TEK yer `_agent_chat_cmd`. İkinci bir
    kurulum yeri, bayrağın yarısını taşıyan ikinci bir davranış demektir (bu vakanın sınıfı)."""
    src = inspect.getsource(hermes)
    assert src.count('"chat", "--accept-hooks"') == 1
    assert '_agent_chat_cmd(bin_, prompt, preload, model)' in inspect.getsource(hermes._agent_call)


# ================= KAYNAK ÇİVİLERİ ===============================================================
def test_z1_run_acilis_senkronunu_BIR_KEZ_cagirir():
    """Kapı `_run`ın içinde ve tek-atımlık bayrakla korunuyor; `start()`ta DEĞİL (uygulama açılışı
    yavaş/asılı bir CLI tarafından rehin alınamaz)."""
    src = inspect.getsource(hr._run)
    assert "_acilis_senkron_dogrula()" in src and "_acilis_senkron_calisti" in src
    assert "_acilis_senkron_dogrula" not in inspect.getsource(hr.start)
    assert 'local_agent_sync' in src                       # pano hermes_status.json'dan okur


def test_z2_yapilandirmasiz_kol_soguma_ve_zincirden_ONCE_doner():
    """Sözleşme kaynakta: `agent_unconfigured` kolu `brain_stand_down`a giden yoldan ÖNCE `return`
    eder. Yarın eklenecek bir kol bu sırayı bozarsa soğuma yine kirlenir — sıra burada sabit."""
    src = inspect.getsource(hermes._agent_call)
    i_unconf, i_return = src.index('obs.warn("agent_unconfigured"'), src.index("return None\n        if not empty")
    i_stand = src.index("brain_stand_down")
    assert i_unconf < i_return < i_stand
    assert "_agent_budget_refund(" in src
