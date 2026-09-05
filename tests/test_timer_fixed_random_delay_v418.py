"""test_timer_fixed_random_delay_v418.py — RandomizedDelaySec taşıyan HER filo timer'ı
FixedRandomDelay=true da taşır (TSK-152, 2026-09-05).

VAKA: brief `dagit.sh`'nin [4] adımındaki `sudo systemctl daemon-reload`ın "RandomizedDelaySec
taşıyan timer'ları o saniye ateşliyor (3/3 ölçüldü)" iddiasıyla geldi. A1'de ÖLÇÜLDÜ (salt-okunur
ssh, journalctl + `systemctl show`): dağıtım #13/#14/#15'in dört reload anında (2026-09-04
20:02:55Z, 22:08:16Z, 22:36:11Z, 22:42:49Z) filodaki hiçbir RandomizedDelaySec timer'ı beklenmedik
ateşlemedi — günün TEK ateşleri (07:33/10:03/22:02/23:30) kendi OnCalendar penceresindeydi. Yani
"3/3" öncülü bu ölçümde DOĞRULANMADI. Buna rağmen `FixedRandomDelay=true` eklendi: `daemon-reload`
SİSTEM-GENELİDİR (yalnız dagit'in kendi $_BASLAT üçlüsünü değil, A1'de yüklü HER timer'ı yeniden
hesaplatır) ve systemd'nin belgelenmiş davranışı — `RandomizedDelaySec` varsayılanı her yeniden
hesaplamada rastgele payı YENİDEN ÇEKER, yeni pay eskisinden küçükse tetik erkene çekilir — ölçüm
göstermese bile zararsız ve ucuz bir kapatmadır (gerekçenin tamamı
deploy/oracle-a1/meridian-backup.timer başlığında; TEK KAYNAK, kalan beş dosya kısaltılmış
işaretçi taşır).

SÖZLEŞME (metin, AST değil — timer dosyaları basit INI, `systemd.syntax` ayrıştırıcı gerektirmez):
her `deploy/**/*.timer` dosyasında `[Timer]` bölümünde bir YÖNERGE satırı (yorum değil)
`RandomizedDelaySec=<pozitif-tamsayı>` varsa, aynı bölümde bir YÖNERGE satırı `FixedRandomDelay=
true` da bulunmalıdır. `RandomizedDelaySec` hiç yoksa ya da `0`sa (ör. meridian-geridolum.timer,
meridian-tick-watchdog.timer, hindsight-yedek.timer — ÖLÇÜLDÜ, A1 `systemctl show`:
RandomizedDelayUSec=0) kapı sessizdir; sıfır gecikmede reload'un yeniden-çekeceği bir pay yoktur.

YÖNTEM: gerçek dosyaları okuyan asıl test + saf metin üzerinde çalışan `_ihlal_var` fonksiyonunun
kendisini bir MUTASYONLA (bir dosyadan FixedRandomDelay satırını sökülmüş hâliyle) kırmızıya
çevirdiğini gösteren ayrı bir test — "çivi yeşili kanıt değildir" (CLAUDE.md §6).
"""
from __future__ import annotations

import pathlib
import re

REPO = pathlib.Path(__file__).resolve().parent.parent
DEPLOY = REPO / "deploy"

_YONERGE = re.compile(r"^[A-Za-z][A-Za-z0-9]*=", re.MULTILINE)


def _yonergeler(metin: str) -> dict[str, str]:
    """`[Timer]` bölümündeki `Anahtar=değer` yönergelerini sözlüğe çevirir (yorum satırları HARİÇ
    — timer dosyalarında `# ... RandomizedDelaySec=300 ...` biçiminde ANLATIM AMAÇLI geçen satırlar
    var, bunlar yönerge DEĞİL; ayraç satır başında `#` olmayan gerçek `Anahtar=değer` satırıdır).
    """
    sonuc: dict[str, str] = {}
    icinde_timer = False
    for satir in metin.splitlines():
        s = satir.strip()
        if s.startswith("["):
            icinde_timer = s == "[Timer]"
            continue
        if not icinde_timer or not s or s.startswith("#"):
            continue
        if _YONERGE.match(s):
            anahtar, _, deger = s.partition("=")
            sonuc[anahtar.strip()] = deger.strip()
    return sonuc


def _ihlal_var(metin: str) -> bool:
    """`RandomizedDelaySec` pozitif ama `FixedRandomDelay=true` YOK → İHLAL (True).

    Sayısal olmayan/boş bir `RandomizedDelaySec` değeri de "pozitif" sayılır (uydurma yasağı:
    ayrıştıramadığımız bir değeri sessizce 0'a indirgemek, riski olduğundan küçük göstermektir) —
    tek güvenli okuma sıfır-dışı her metni potansiyel gecikme kabul etmektir.
    """
    y = _yonergeler(metin)
    rds = y.get("RandomizedDelaySec", "0")
    rds_pozitif = rds != "0" and rds.strip() != ""
    if not rds_pozitif:
        return False
    return y.get("FixedRandomDelay", "").lower() != "true"


def _timer_dosyalari() -> list[pathlib.Path]:
    dosyalar = sorted(DEPLOY.glob("**/*.timer"))
    assert dosyalar, f"deploy/ altında hiç .timer bulunamadı — kapı ölçecek bir şey yok: {DEPLOY}"
    return dosyalar


def test_randomizeddelaysec_tasiyan_her_timer_fixedrandomdelay_tasir():
    ihlaller = []
    for f in _timer_dosyalari():
        if _ihlal_var(f.read_text(encoding="utf-8")):
            ihlaller.append(str(f.relative_to(REPO)))
    assert not ihlaller, (
        "RandomizedDelaySec taşıyan ama FixedRandomDelay=true TAŞIMAYAN timer(lar): "
        + ", ".join(ihlaller)
        + " — dagit'in [4] adımındaki sistem-geneli `daemon-reload` bu timer'ların rastgele "
        "payını yeniden çekip tetiği erkene çekebilir (TSK-152, gerekçe "
        "deploy/oracle-a1/meridian-backup.timer başlığında)."
    )


def test_randomizeddelaysec_olmayan_ya_da_sifir_olan_timer_serbest():
    """Negatif kontrol: RandomizedDelaySec'i hiç olmayan ya da 0 olan timer'lar bu kapıdan
    ETKİLENMEZ — reload'un yeniden çekeceği bir rastgele pay yoksa FixedRandomDelay anlamsızdır.
    ÖLÇÜLDÜ (A1 `systemctl show`, 2026-09-05): meridian-geridolum, meridian-tick-watchdog,
    hindsight-yedek RandomizedDelayUSec=0.
    """
    serbest_beklenen = {
        "meridian-geridolum.timer",
        "meridian-tick-watchdog.timer",
        "hindsight-yedek.timer",
    }
    bulunan = {f.name for f in _timer_dosyalari()}
    for ad in serbest_beklenen & bulunan:
        f = next(x for x in _timer_dosyalari() if x.name == ad)
        assert not _ihlal_var(f.read_text(encoding="utf-8")), (
            f"{ad}: RandomizedDelaySec yok/0 sayılıyordu ama kapı yine de ihlal buldu — "
            "beklenti (ve A1 ölçümü) değişmiş olabilir, dosyayı elle kontrol et."
        )


def test_mutasyon_fixedrandomdelay_satiri_sokulunce_kapi_kirmiziya_doner():
    """Çivi yeşili kanıt değildir (CLAUDE.md §6): `_ihlal_var` GERÇEKTEN FixedRandomDelay
    yokluğunu yakalıyor mu? meridian-backup.timer'ın GÜNCEL (düzeltilmiş) metninden
    `FixedRandomDelay=true` satırını sökülmüş bir KOPYA üretip fonksiyonu doğrudan sınar —
    dosyanın kendisine dokunulmaz.
    """
    orijinal = (DEPLOY / "oracle-a1" / "meridian-backup.timer").read_text(encoding="utf-8")
    assert not _ihlal_var(orijinal), "ön-koşul: düzeltilmiş dosya zaten temiz olmalı"

    mutasyon = "\n".join(
        satir for satir in orijinal.splitlines() if not satir.startswith("FixedRandomDelay=")
    )
    # Yönerge SATIRI söküldü mü diye ANLATIM YORUMLARINDAN (dosya `FixedRandomDelay=true`
    # ibaresini gerekçe metninde de geçiriyor) bağımsız ölç: _yonergeler yorum-kör, tam bunun için.
    assert "FixedRandomDelay" not in _yonergeler(mutasyon), "mutasyon yönerge satırını gerçekten sökmedi"
    assert _ihlal_var(mutasyon), "mutasyon FixedRandomDelay'i söktü ama kapı hâlâ SESSİZ — ölü çivi"


def test_yonergeler_yorum_satirini_yonerge_saymaz():
    """`_yonergeler`in yorum-farkındalığı: dosyalarda `# ... RandomizedDelaySec=300 var ...` gibi
    ANLATIM satırları geçiyor (ör. meridian-bekci.timer, meridian-karne.timer başlıkları) — bunlar
    [Timer] bölümü DIŞINDA (dosya başında, `[Unit]`den önce) oldukları için zaten `icinde_timer`
    kapısına girmiyor, ama burada AYRICA [Timer] içindeki bir yorumla da sınanır.
    """
    sahte = "[Timer]\n# RandomizedDelaySec=999 (bu bir anlatım, yönerge değil)\nOnCalendar=*-*-* 00:00:00 UTC\n"
    y = _yonergeler(sahte)
    assert "RandomizedDelaySec" not in y, "yorum satırı yönerge sayıldı — ayraç yorum-kör değil"


def test_bash_sozdizimi_gecerli():
    import subprocess

    p = subprocess.run(["bash", "-n", str(REPO / "dagit.sh")], capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
