"""test_kilit_budamasi_v234.py — `.locks` budaması (ROADMAP §2-5).

NE ÖLÇER: budayıcının TEK tehlikeli hatası yanlış silmedir — tutulan kilidi silmek dışlamayı
kırar (yol silinince sonraki `open(O_CREAT)` YENİ inode yaratır; iki "sahip" aynı anda içeride
olur). İki yönlü kanıt zorunlu: (1) tutulan kilit — ayrı fd'den de, `store._FileLock` üzerinden
de — BUDANMAZ; (2) aynı dosya serbest kalınca BUDANIR. Ek çiviler: yaş eşiği (genç serbest dosya
kalır), kapsam (`.lock` uzantısız dosyaya ve alt dizine dokunulmaz), dizin yoksa sıfır rapor,
budayıcı dosya YARATMAZ.
"""
from __future__ import annotations

import fcntl
import os
import time

from meridian import store


def _kilit_dosyasi(d, ad="x.lock", yas_saat=48.0):
    d.mkdir(parents=True, exist_ok=True)
    p = d / ad
    p.touch()
    t = time.time() - yas_saat * 3600.0
    os.utime(p, (t, t))
    return p


# ---- 1. İKİ YÖNLÜ KANIT: tutulurken KALIR, serbest kalınca GİDER -------------------------------
def test_tutulan_kilit_budanmaz_serbest_kalinca_budanir(tmp_path):
    d = tmp_path / ".locks"
    p = _kilit_dosyasi(d, "canli.lock")
    fd = os.open(str(p), os.O_RDWR)
    fcntl.flock(fd, fcntl.LOCK_EX)
    try:
        r = store.kilit_budamasi(d, max_yas_saat=24.0)
        assert p.exists(), "TUTULAN kilit silindi — dışlama kırıldı"
        assert r["tutulan"] == 1 and r["budandi"] == [] and r["tarandi"] == 1
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)
    r2 = store.kilit_budamasi(d, max_yas_saat=24.0)
    assert not p.exists() and r2["budandi"] == ["canli.lock"]


def test_ayni_surecte_FileLock_tutarken_budanmaz(tmp_path):
    """flock(2) iddiasının ÖLÇÜMÜ (docstring'e güven yok): aynı süreçte AYRI open'lar birbirini
    dışlar — yani budayıcının non-blocking flock'u, bu süreçteki `store._FileLock`un tuttuğu
    kilidi de doğru biçimde 'canlı' görür. Bu tutmasaydı budayıcı kendi sürecinin kilidini
    silerdi ve süreçler-arası dışlama sessizce kırılırdı."""
    d = tmp_path / ".locks"
    lk = store._FileLock("defter.json", d)
    lk.acquire()
    try:
        p = d / "defter.json.lock"
        assert p.exists()                      # _FileLock kilidi flock'la tutuyor
        t = time.time() - 48 * 3600.0
        os.utime(p, (t, t))                    # eski görünse bile...
        r = store.kilit_budamasi(d, max_yas_saat=24.0)
        assert p.exists() and r["tutulan"] == 1 and r["budandi"] == []
    finally:
        lk.release()
    r2 = store.kilit_budamasi(d, max_yas_saat=24.0)
    assert r2["budandi"] == ["defter.json.lock"] and not (d / "defter.json.lock").exists()


# ---- 2. YAŞ EŞİĞİ + KAPSAM ----------------------------------------------------------------------
def test_genc_serbest_kilit_kalir_eski_gider(tmp_path):
    d = tmp_path / ".locks"
    eski = _kilit_dosyasi(d, "eski.lock", yas_saat=48.0)
    genc = _kilit_dosyasi(d, "genc.lock", yas_saat=0.0)
    r = store.kilit_budamasi(d, max_yas_saat=24.0)
    assert not eski.exists() and genc.exists()
    assert r["budandi"] == ["eski.lock"] and r["genc"] == 1 and r["tarandi"] == 2


def test_kapsam_yalniz_lock_uzantili_duz_dosyalar(tmp_path):
    """`.locks` altında kilit olmayan bir şey durmamalı ama durursa da budayıcı ona KARIŞMAZ:
    uzantı ve düz-dosya süzgeci, yanlış hedefe karşı yapısal sınırdır."""
    d = tmp_path / ".locks"
    veri = _kilit_dosyasi(d, "veri.json", yas_saat=48.0)          # .lock değil
    altd = d / "alt.lock"
    altd.mkdir()                                                  # .lock ADLI dizin
    r = store.kilit_budamasi(d, max_yas_saat=24.0)
    assert veri.exists() and altd.is_dir()
    assert r["tarandi"] == 0 and r["budandi"] == []


def test_dizin_yoksa_sifir_rapor_ve_yaratmaz(tmp_path):
    d = tmp_path / "yok" / ".locks"
    r = store.kilit_budamasi(d, max_yas_saat=24.0)
    assert r["tarandi"] == 0 and r["budandi"] == [] and not d.exists()


def test_budayici_dosya_yaratmaz_ve_rapor_sayimlari_tutar(tmp_path):
    """O_CREAT bilinçli yok: budayıcı koşusu `.locks` içeriğini ancak AZALTABİLİR. Rapor
    sayaçları da okuyucusu olan bir yüzeydir (conftest özet satırı) — uydurma olmasın."""
    d = tmp_path / ".locks"
    adlar = [f"k{i}.lock" for i in range(3)]
    for ad in adlar:
        _kilit_dosyasi(d, ad, yas_saat=30.0)
    _kilit_dosyasi(d, "taze.lock", yas_saat=1.0)
    once = {p.name for p in d.iterdir()}
    r = store.kilit_budamasi(d, max_yas_saat=24.0)
    sonra = {p.name for p in d.iterdir()}
    assert sonra == {"taze.lock"} and once - sonra == set(adlar)
    assert sorted(r["budandi"]) == adlar
    assert r == {"dizin": str(d), "tarandi": 4, "budandi": r["budandi"],
                 "tutulan": 0, "genc": 1, "degisen": 0, "hata": 0}
