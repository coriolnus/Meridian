"""test_wph_dash_credential_v184 — pano token'ı systemd credential kanalından okunuyor mu?

BAĞLAM (WP-H/H3 tur-3): token 0644'lük birimden 0600'lük `.dash.env`e taşındı (tur-1/2), ama
KALAN YÜZEY süreç ORTAMIDIR: bu depoda ortam çocuklara akar (`serve.sh` uvicorn'u `env=os.environ`
ile, `hermes_composite` ajan alt süreçlerini devralınan ortamla doğurur), yani token pano
sürecinin VE her LLM ajan sürecinin `/proc/<pid>/environ`ında duruyor. systemd `LoadCredential=`
sırrı ortama HİÇ koymaz. Geçiş iki fazlıdır ve FAZ 2 (ortam kanalının kapatılması) BU DOSYANIN
ölçtüğü davranış canlıda olmadan yapılamaz — `dash_token_credential.sh --faz2` içindeki farksal
ölçüm tam olarak bunu arar (sahte ortam + gerçek credential → 200 gelmezse faz 2 REDDEDİLİR).

NEDEN `_read_dash_token()` DOĞRUDAN ÇAĞRILIYOR (modül yeniden yüklenmiyor): `api.DASH_TOKEN` süreç
açılışında BİR KEZ hesaplanır; `importlib.reload(api)` ise FastAPI uygulamasını, rota sınıfını ve
tüm rotaları yeniden kurar — yani ölçüm, ölçtüğü şeyden çok daha büyük bir yan etki üretirdi (ve
aynı süreçte koşan öteki testlerin tuttuğu `api.app` referansını bayatlatırdı). Okuyucu saf bir
fonksiyondur; sözleşmesi de tam olarak "hangi kanaldan ne döner"dir. Modül düzeyindeki bağın
KOPMADIĞI ayrıca sınanır (test 8).

YEDİ SENARYO — davranış tablosunun TAMAMI (brief, 2026-08-03):
  1. yalnız ortam           → bugünkü davranışla BİREBİR
  2. çıplak credential      → dosyadaki değer
  3. KEY=VALUE credential   → önek tanınır, değer döner
  4. ikisi de var           → credential KAZANIR
  5. boş credential         → ortama düşülür
  6. dizin var, dosya yok   → ortama düşülür
  7. hiçbiri yok            → None (zorunlu-token kapısı birebir korunur)
"""
from __future__ import annotations

import os

import pytest

from meridian import api


@pytest.fixture()
def kred(tmp_path, monkeypatch):
    """`CREDENTIALS_DIRECTORY`yi kuran ve içine dosya yazan yardımcı — systemd'nin yaptığının
    testteki karşılığı. Dizini KURAR ama dosyayı YAZMAZ (senaryo 6 tam olarak o hâli ölçer)."""
    d = tmp_path / "credentials"
    d.mkdir()
    monkeypatch.setenv("CREDENTIALS_DIRECTORY", str(d))
    return d


# ---- 1) YALNIZ ORTAM: bugünkü davranış birebir --------------------------------------------------
def test_1_yalniz_ortam_bugunku_davranisla_birebir(monkeypatch):
    """Credential dizini YOKKEN okuyucu, değiştirdiği satırın ta kendisi olmalı: os.environ.get."""
    monkeypatch.delenv("CREDENTIALS_DIRECTORY", raising=False)
    monkeypatch.setenv("MERIDIAN_DASH_TOKEN", "ortam-token-abc")
    assert api._read_dash_token() == "ortam-token-abc"
    # BİREBİRLİK İDDİASI TAHMİN DEĞİL, KARŞILAŞTIRMA: eski ifadeyle aynı değeri döndürdüğü ölçülür.
    assert api._read_dash_token() == os.environ.get("MERIDIAN_DASH_TOKEN")


# ---- 2) ÇIPLAK CREDENTIAL -----------------------------------------------------------------------
def test_2_ciplak_credential_okunur(kred, monkeypatch):
    """Sözleşmedeki biçim: dosya YALNIZ token'ı içerir, sondaki yeni satır serbest.
    Sondaki `\\n` KIRPILMALI — kırpılmazsa `hmac.compare_digest` hep yanlış döner ve token
    'ayarlı ama çalışmıyor' hâline gelir (arıza ağda aranır)."""
    monkeypatch.delenv("MERIDIAN_DASH_TOKEN", raising=False)
    (kred / "dash_token").write_text("kred-token-123\n", encoding="utf-8")
    assert api._read_dash_token() == "kred-token-123"


# ---- 3) KEY=VALUE CREDENTIAL --------------------------------------------------------------------
def test_3_key_value_bicimli_credential_toleransli(kred, monkeypatch):
    """`.dash.env` alışkanlığıyla yazılmış bir credential kaynağı ÖNGÖRÜLEBİLİR bir kazadır.
    Önek sessizce yutulmaz, TANINIR — aksi hâlde okunan değer `MERIDIAN_DASH_TOKEN=xyz` olurdu."""
    monkeypatch.delenv("MERIDIAN_DASH_TOKEN", raising=False)
    (kred / "dash_token").write_text("MERIDIAN_DASH_TOKEN=kred-token-456\n", encoding="utf-8")
    assert api._read_dash_token() == "kred-token-456"


# ---- 4) İKİSİ DE VAR → CREDENTIAL KAZANIR -------------------------------------------------------
def test_4_ikisi_varsa_credential_kazanir(kred, monkeypatch):
    """Geçişin FAZ 1'i tam olarak bu hâldir (iki kanal aynı anda canlı). Öncelik credential'da
    olmazsa faz 2'de ortam kapandığında davranış SESSİZCE değişirdi — ve `--faz2`nin farksal
    ölçümü (sahte ortam + gerçek credential) 401 alıp geçişi haklı olarak reddederdi."""
    monkeypatch.setenv("MERIDIAN_DASH_TOKEN", "sahte-ortam-degeri")
    (kred / "dash_token").write_text("gercek-kred-degeri\n", encoding="utf-8")
    assert api._read_dash_token() == "gercek-kred-degeri"


# ---- 5) BOŞ CREDENTIAL → ORTAM ------------------------------------------------------------------
@pytest.mark.parametrize("icerik", ["", "\n", "   \n\n", "MERIDIAN_DASH_TOKEN=\n"])
def test_5_bos_credential_ortama_duser(kred, monkeypatch, icerik):
    """Boş/yalnız-boşluk dosya bir DEĞER değildir. Buradan boş string dönmesi en kötü hâl olurdu:
    `_auth` için 'token ayarlı DEĞİL' (falsy) demektir ve kimlik doğrulaması SESSİZCE no-op'a
    düşerdi — yani ortamda geçerli bir token dururken kapı açılırdı. Ortama düşmek doğru davranış.
    Önekli-ama-değersiz biçim de (`MERIDIAN_DASH_TOKEN=`) aynı kovadadır."""
    monkeypatch.setenv("MERIDIAN_DASH_TOKEN", "ortam-yedegi")
    (kred / "dash_token").write_text(icerik, encoding="utf-8")
    assert api._read_dash_token() == "ortam-yedegi"


# ---- 6) DİZİN VAR, DOSYA YOK → ORTAM ------------------------------------------------------------
def test_6_dizin_var_dosya_yok_ortama_duser(kred, monkeypatch):
    """systemd BAŞKA bir credential yüklediğinde `CREDENTIALS_DIRECTORY` kurulur ama `dash_token`
    içinde OLMAZ. Bu bir arıza değildir ve patlamamalıdır (uygulama açılmamak yerine ortamı okur).
    Gerçekten zorunlu olduğu kurulumda sessiz kalmayan yer systemd'dir: kaynak yoksa birim başlamaz."""
    monkeypatch.setenv("MERIDIAN_DASH_TOKEN", "ortam-yedegi-2")
    assert not (kred / "dash_token").exists()
    assert api._read_dash_token() == "ortam-yedegi-2"


def test_6b_okunamayan_credential_ortama_duser(kred, monkeypatch):
    """Aynı sınıfın izin ayağı: dosya VAR ama okunamıyor (0000). `# sessiz-yutma:` işaretinin
    gerekçesi budur — ve yutmanın yolu ÖLÇÜLÜR, varsayılmaz.
    (root olarak koşan bir ortamda izin kapısı işlemez; o hâlde test dürüstçe atlanır.)"""
    monkeypatch.setenv("MERIDIAN_DASH_TOKEN", "ortam-yedegi-3")
    f = kred / "dash_token"
    f.write_text("okunamayan-token\n", encoding="utf-8")
    f.chmod(0o000)
    try:
        if os.access(f, os.R_OK):  # root / izin uygulamayan dosya sistemi
            pytest.skip("izinler uygulanmıyor (root ya da izin-duyarsız dosya sistemi) — ölçülemez")
        assert api._read_dash_token() == "ortam-yedegi-3"
    finally:
        f.chmod(0o600)


# ---- 7) HİÇBİRİ → None --------------------------------------------------------------------------
def test_7_hicbiri_yoksa_none(monkeypatch):
    """Mevcut zorunlu-token kapısı BİREBİR korunur: `_auth_posture_check` uyarısı ve `_auth`ın
    no-op dalı `DASH_TOKEN is None` üzerine kuruludur; boş string ya da atılan bir istisna o
    yasayı sessizce değiştirirdi."""
    monkeypatch.delenv("CREDENTIALS_DIRECTORY", raising=False)
    monkeypatch.delenv("MERIDIAN_DASH_TOKEN", raising=False)
    assert api._read_dash_token() is None


def test_7b_credential_dizini_hic_var_olmasa_bile_patlamaz(tmp_path, monkeypatch):
    """`CREDENTIALS_DIRECTORY` ayarlı ama dizin DİSKTE YOK (bayat ortam / elle export).
    Okuyucu istisna atarsa uygulama HİÇ açılmaz — token okuma bir açılış kapısı DEĞİLDİR."""
    monkeypatch.setenv("CREDENTIALS_DIRECTORY", str(tmp_path / "yok-boyle-bir-dizin"))
    monkeypatch.delenv("MERIDIAN_DASH_TOKEN", raising=False)
    assert api._read_dash_token() is None


# ---- 8) MODÜL BAĞI: DASH_TOKEN gerçekten bu okuyucudan geliyor mu? ------------------------------
def test_8_modul_duzeyi_dash_token_okuyucuya_bagli():
    """Yedi senaryo saf fonksiyonu ölçer; bu test fonksiyonun GERÇEKTEN kablolu olduğunu ölçer.
    Aksi hâlde okuyucu kusursuz çalışır ve `api.DASH_TOKEN` yine eski satırdan gelirdi — ölçüm
    yeşil, canlı davranış değişmemiş olurdu (bu depodaki en pahalı yanlış-yeşil sınıfı)."""
    import inspect

    src = inspect.getsource(api)
    assert "DASH_TOKEN = _read_dash_token()" in src, \
        "modül düzeyindeki DASH_TOKEN okuyucuya bağlı değil — kanal eklendi ama kablolanmadı"
    assert "os.environ.get(\"MERIDIAN_DASH_TOKEN\")" not in \
        src.split("DASH_TOKEN = _read_dash_token()")[1].split("def _autostart")[0], \
        "atamadan sonra eski doğrudan-ortam okuması artakalmış"
