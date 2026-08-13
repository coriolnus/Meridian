"""test_agent_provider_yonlendirme_v244.py — v244 KALEM 1+2: `--model` doğruydu, istek yanlış uca gidiyordu.

ÖLÇÜLEN ARIZA (canlı, 24 saat — docs/TESHIS-BEYIN-ZINCIRI-ERISILEMEZ-MODEL-2026-08-13.md):
`_agent_chat_cmd` CLI'ya YALNIZ `--model` geçiyordu; yerel hermes CLI'nın kendi yapılandırması
`model.provider: gemini` olduğu için bir OpenRouter slug'ı GEMINI ucuna gidip HTTP 404 alıyordu —
33 çağrının 33'ü boş, ~354 sn israf, tüm ajan çağrılarının %46'sı.

UCUZ YOL ÇÜRÜDÜ (2026-08-13 21:12Z canlı, karşı-sınamalı): `hermes config set model.provider auto`
hem tencent hem `gemini-flash-latest` için 401 verdi — yani ÇALIŞAN ayak da düştü, geri alındı.
Bu yüzden kural CLI yapılandırmasında değil KODDA yaşıyor ve `model.provider: gemini` DEĞİŞMİYOR.

BU DOSYA ÇİVİLER:
  (a) slug + kimlik VAR   → komutta `--provider openrouter`
  (b) çıplak ad + kimlik VAR → `--provider` YOK (bugünkü davranış BİT BİT korunur; gemini ayağı
      çalışıyor ve bu turun bozmaması gereken tek şey o)
  (c) slug + kimlik YOK   → `--provider` YOK (gerileme değil, BİLİNÇLİ: kimliksiz bayrak 404'ü
      "empty API key" hatasına çevirirdi — başka bir arıza, daha iyisi değil)
  (d) `--model` bayrağı ÜÇ hâlde de bugünkü gibi
  (e) diğer bayraklar (`--accept-hooks`, `-Q`, `-q`, `-s`) değişmedi
  (f) KALEM 2 — pano yardım metnindeki ölü örnek (`tencent/hy3:free`) app.js'te ARTIK YOK

KİMLİK YÜZEYİ (bu turun asıl kararı, kaynakta da çivili): soru "Meridian'ın anahtarı var mı" değil
"ALT SÜREÇ olarak koşan CLI bir anahtar GÖREBİLİYOR mu"dur. CLI iki yüzey görür — süreç ortamı
(`env={**os.environ, ...}` ile miras) ve kendi `~/.hermes/.env` dosyası. `secrets.get` BİLEREK
kullanılmadı: zinciri env'den sonra `state/secrets.json` + GCP'ye bakar ve o iki kaynak alt sürece
HİÇ GEÇMEZ — kasada anahtar varken True derdi, CLI ise anahtarsız kalırdı. Bu tam olarak bu turun
kapattığı sınıftır ("ayar yapıldı sanılıyor, ulaşılamıyor").
"""
from __future__ import annotations

import inspect
import pathlib

import pytest

from meridian import hermes

SLUG = "nvidia/nemotron-3-ultra-550b-a55b:free"   # ÖLÇÜLDÜ: canlıda dolu cevap (838 ms, tam JSON)
CIPLAK = "gemini-flash-latest"                    # slash YOK → CLI kendi varsayılanına gider
OLU_ORNEK = "tencent/hy3:free"                    # hiç var olmadı; metin bu adı ÖNERİYORDU


@pytest.fixture
def kimliksiz(tmp_path, monkeypatch):
    """HERMETİK TABAN: iki kimlik yüzeyi de ÖLÇÜLMÜŞ BOŞ.

    `_agent_env_path` tmp'ye çevrilir — aksi hâlde test operatörün GERÇEK `~/.hermes/.env`ini
    okurdu ve makineden makineye farklı sonuç veren bir test hiçbir şey kanıtlamaz (conftest'in
    `AGENT_CONFIG` sızıntısıyla aynı sınıf). `_quiet_flag_ok` de açıkça kurulur: süreç-içi öğrenme
    globali başka bir testte False'a düşmüş olabilir."""
    env = tmp_path / "hermes_env"
    monkeypatch.setattr(hermes, "_agent_env_path", lambda: str(env))
    monkeypatch.delenv(hermes.AGENT_SLUG_PROVIDER_ENV, raising=False)
    monkeypatch.setattr(hermes, "_quiet_flag_ok", True)
    return env


@pytest.fixture
def kimlikli(kimliksiz, monkeypatch):
    """Kimlik `~/.hermes/.env` yüzeyinde — canlıdaki kurulum yolu (kurulum belgesi Adım 1b)."""
    kimliksiz.write_text(f"GEMINI_API_KEY=g\n{hermes.AGENT_SLUG_PROVIDER_ENV}=or-xxxx\n")
    return kimliksiz


def _cmd(model):
    return hermes._agent_chat_cmd("/bin/hermes", "istem", ("beceri1", "beceri2"), model)


def _bayrak_degeri(cmd, bayrak):
    """Bayraktan SONRAKİ değer (yoksa None). Konumu da ölçer: bayrak varsa değeri hemen ardındadır."""
    return cmd[cmd.index(bayrak) + 1] if bayrak in cmd else None


def _govde(fn) -> str:
    """Fonksiyonun YALNIZ KODU — docstring ve `#` yorumları atılır.

    v122 dersi: YORUM DAVRANIŞ DEĞİLDİR. Bu dosyanın kaynak çivileri "şu çağrı yapılmıyor" diyor;
    gerekçeyi ANLATAN bir yorum satırı o iddiayı düşürmemeli (ve düşürseydi, gerekçe yazmak
    cezalandırılırdı). v235'in app.js çivisiyle aynı desen."""
    import ast
    import textwrap
    agac = ast.parse(textwrap.dedent(inspect.getsource(fn))).body[0]
    govde = agac.body[1:] if ast.get_docstring(agac) else agac.body
    return "\n".join(ast.unparse(d) for d in govde)


# ============================== (a) SLUG + KİMLİK VAR ============================================
def test_a_slug_kimlik_varken_provider_eklenir(kimlikli):
    cmd = _cmd(SLUG)
    assert "--provider" in cmd, "slug OpenRouter'a yönlendirilmiyor — 404 sınıfı aynen sürer"
    assert _bayrak_degeri(cmd, "--provider") == hermes.AGENT_SLUG_PROVIDER == "openrouter"


def test_a_kimlik_SUREC_ORTAMINDAN_da_sayilir(kimliksiz, monkeypatch):
    """Alt süreç `os.environ`ı MİRAS ALIR (`_agent_call._kos`: env={**os.environ, ...}) — yani env
    kolu CLI'nin gerçekten gördüğü ikinci yüzeydir ve tek başına yeterlidir."""
    monkeypatch.setenv(hermes.AGENT_SLUG_PROVIDER_ENV, "or-xxxx")
    assert _bayrak_degeri(_cmd(SLUG), "--provider") == "openrouter"


def test_a_bos_env_degeri_kimlik_SAYILMAZ(kimliksiz, monkeypatch):
    """Boş/boşluklu bir env değeri "ayarlı" değildir — CLI onunla auth başlığı kuramaz."""
    monkeypatch.setenv(hermes.AGENT_SLUG_PROVIDER_ENV, "   ")
    assert "--provider" not in _cmd(SLUG)


def test_a_env_satiri_bos_degerle_yazilmissa_kimlik_SAYILMAZ(kimliksiz):
    """`.env`de yer tutucu/boş satır: dosya "dolu görünür", anahtar YOKTUR (kurulum belgesinin
    açıkça uyardığı tuzak — maskeli değer gösterilir ama 401 alınır)."""
    kimliksiz.write_text(f"{hermes.AGENT_SLUG_PROVIDER_ENV}=\n")
    assert "--provider" not in _cmd(SLUG)


# ============================== (b) ÇIPLAK AD — BUGÜNKÜ DAVRANIŞ ================================
def test_b_ciplak_ad_kimlik_VARKEN_bile_provider_almaz(kimlikli):
    """EN KRİTİK ÇİVİ: gemini ayağı BUGÜN ÇALIŞIYOR (24 saatte 38 dolu cevap) ve bu tur onu
    bozamaz. Slash taşımayan ad CLI'nin kendi `model.provider: gemini` varsayılanına bırakılır."""
    cmd = _cmd(CIPLAK)
    assert "--provider" not in cmd
    assert hermes._agent_provider_for(CIPLAK) is None


def test_b_model_yokken_ne_model_ne_provider(kimlikli):
    """Model hiç verilmediyse komut BUGÜNKÜ gibi kalır — provider'ı tek başına eklemek, CLI'nin
    varsayılan modelini yabancı bir uca yollardı."""
    cmd = _cmd(None)
    assert "--model" not in cmd and "--provider" not in cmd


# ============================== (c) SLUG + KİMLİK YOK ===========================================
def test_c_kimliksiz_slug_yonlendirilmez(kimliksiz):
    """BİLİNÇLİ: kimliksiz `--provider` 404'ü "Provider resolver returned an empty API key"e
    çevirirdi — daha iyi değil, YALNIZ BAŞKA bir arıza; ve anahtarsız test/geliştirme ortamlarını
    kırardı."""
    assert "--provider" not in _cmd(SLUG)
    assert hermes._agent_provider_for(SLUG) is None


def test_c_env_dosyasi_okunamazsa_kimlik_YOK_sayilir(kimliksiz, monkeypatch):
    """Ölçülemeyen kimlik "var" sayılamaz: `_agent_env_has` None döndüğünde (dosya VAR, okunamadı)
    güvenli taraf bugünkü davranışı korumaktır."""
    monkeypatch.setattr(hermes, "_agent_env_has", lambda names: None)
    assert "--provider" not in _cmd(SLUG)


# ============================== (d) `--model` DEĞİŞMEDİ =========================================
@pytest.mark.parametrize("model", [SLUG, CIPLAK])
def test_d_model_bayragi_her_halde_aynen_gecer(kimlikli, model):
    assert _bayrak_degeri(_cmd(model), "--model") == model


def test_d_model_bayragi_kimliksiz_halde_de_aynen_gecer(kimliksiz):
    assert _bayrak_degeri(_cmd(SLUG), "--model") == SLUG


# ============================== (e) DİĞER BAYRAKLAR DEĞİŞMEDİ ===================================
@pytest.mark.parametrize("model", [SLUG, CIPLAK, None])
def test_e_diger_bayraklar_bit_bit_ayni(kimlikli, model):
    """`-q` (SORGU) ile `-Q` (SESSİZ) iki AYRI iştir ve karıştırılırsa arıza SESSİZDİR — 2026-08-02
    canlı vakası. Bu tur o ayrımı taşıyan komuta dokundu; ayrım burada kilitli."""
    cmd = _cmd(model)
    assert cmd[:3] == ["/bin/hermes", "chat", "--accept-hooks"]
    assert hermes.QUIET_FLAG in cmd and cmd[3] == hermes.QUIET_FLAG
    assert _bayrak_degeri(cmd, "-q") == "istem"
    assert [cmd[i + 1] for i, a in enumerate(cmd) if a == "-s"] == ["beceri1", "beceri2"]


def test_e_Q_bayragi_ogrenildiginde_dusme_yolu_korunur(kimlikli, monkeypatch):
    """`-Q` desteklenmediği ÖĞRENİLDİĞİNDE komut onsuz kurulur (geriye-uyum kolu) — provider
    yönlendirmesi bu kolu etkilemez."""
    monkeypatch.setattr(hermes, "_quiet_flag_ok", False)
    cmd = _cmd(SLUG)
    assert hermes.QUIET_FLAG not in cmd
    assert _bayrak_degeri(cmd, "--provider") == "openrouter"


# ============================== KAYNAK ÇİVİLERİ =================================================
def test_kaynak_saglayici_adi_SABITTE_yasar():
    """Sağlayıcı adı komutun içine çakılamaz: ikinci beyin başka bir toplayıcıya taşınırsa tek
    satır değişmeli, komut kurucusu değil."""
    kod = _govde(hermes._agent_chat_cmd)
    assert "openrouter" not in kod, "sağlayıcı adı komut kurucusuna sabit kodlanmış"
    assert "_agent_provider_for(model)" in kod


def test_kaynak_kimlik_yuzeyi_SECRETS_DEGIL():
    """SSoT KİLİDİ: `secrets.get` bu kapıda YANLIŞ CEVAP verir (kasa ve GCP alt sürece geçmez).
    Ölçülen iki yüzey — süreç ortamı + `~/.hermes/.env` — kaynakta kilitli."""
    kod = _govde(hermes._agent_slug_provider_ready)
    assert "secrets." not in kod, "kimlik CLI'nin GÖREMEDİĞİ bir yüzeyden okunuyor"
    assert "os.environ.get(AGENT_SLUG_PROVIDER_ENV)" in kod
    assert "_agent_env_has((AGENT_SLUG_PROVIDER_ENV,))" in kod
    # BEYAN: ad `secrets.ALLOWED`da YOK ve bu turda EKLENMEDİ — eklemek panodan
    # `state/secrets.json`a yazmayı açardı ama o dosya CLI'ya görünmez: operatör anahtarı girer,
    # "✓ ayarlı" görür ve çağrı YİNE düşerdi. Tam olarak bu turun kapattığı yanılsama.
    from meridian import secrets
    assert hermes.AGENT_SLUG_PROVIDER_ENV not in secrets.ALLOWED


def test_kaynak_chat_kurulumu_HALA_TEK_YERDE():
    """v169 çivisinin ikizi: provider kolu eklenirken komut ikinci bir yerde kurulmadı."""
    assert inspect.getsource(hermes).count('"chat", "--accept-hooks"') == 1


def test_kaynak_komut_kurucusu_SAF_kalir():
    """Kurucu bir çağrıda ÜÇ kez çağrılabilir (ilk deneme + iki onarım yeniden-koşumu). Buradan
    olay basmak tek çağrıyı deftere üç kez yazardı — `gap_scan` saflık dersiyle aynı sınıf."""
    kod = _govde(hermes._agent_chat_cmd)
    assert "obs." not in kod and "store." not in kod and "open(" not in kod


def test_kaynak_gemini_env_sozlesmesi_BOZULMADI():
    """`_agent_env_has_key` ad kümesi parametrelendi; SÖZLEŞMESİ (Gemini adları) aynen."""
    assert "GEMINI_API_KEY" in hermes.GEMINI_ENV_NAMES
    assert "_agent_env_has(GEMINI_ENV_NAMES)" in inspect.getsource(hermes._agent_env_has_key)


def test_kaynak_gemini_env_okumasi_calisiyor(tmp_path, monkeypatch):
    """DAVRANIŞ (kaynak değil): parametreleme sonrası iki soru da doğru cevaplanıyor."""
    env = tmp_path / "e"
    monkeypatch.setattr(hermes, "_agent_env_path", lambda: str(env))
    assert hermes._agent_env_has_key() is False              # dosya YOK = ölçülmüş yokluk
    env.write_text("export GEMINI_API_KEY='g'\n")
    assert hermes._agent_env_has_key() is True               # `export ` + tırnak soyma korundu
    assert hermes._agent_env_has((hermes.AGENT_SLUG_PROVIDER_ENV,)) is False


# ============================== (f) KALEM 2 — ÖLÜ ÖRNEK PANODAN KALKTI ==========================
def _app_js() -> str:
    return (pathlib.Path(__file__).resolve().parent.parent
            / "meridian" / "web" / "app.js").read_text()


def test_f_olu_model_adi_panoda_ARTIK_GECMIYOR():
    """BU METİN HATAYI ÜRETTİ: `NOUS_MODEL` yardım metni ölü bir adı ÖRNEK OLARAK öneriyordu ve
    operatör tam o satıra bakarak girdi. `tencent/hy3:free` OpenRouter'ın 411 modelinden HİÇBİRİ
    DEĞİL — hiç var olmadı. Yorumlarda da kalmamalı: bir sonraki okuyucu örneği yorumdan da alır."""
    assert OLU_ORNEK not in _app_js()


def test_f_yerine_OLCULMUS_model_ve_erisilebilirlik_uyarisi_var():
    """Yeni örnek TAHMİN DEĞİL ÖLÇÜM (canlıda dolu cevap) ve metin artık ölçütün yanıltıcılığını
    açıkça söylüyor: `same_model_ids`in boşalması bir ERİŞİLEBİLİRLİK kanıtı DEĞİLDİR."""
    js = _app_js()
    assert SLUG in js
    satir = next(l for l in js.splitlines() if '"NOUS_MODEL"' in l)
    assert SLUG in satir and "ERİŞİLEBİLİR" in satir
    assert "same_model_ids" in satir and "YETMEZ" in satir
