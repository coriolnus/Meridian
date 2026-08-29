"""BRİFİNG KADANSI: hesaplanan teslim edilir, boşken SESSİZ — v327 (2026-08-27)

ÖLÇÜM (2026-08-27, canlı A1):
    notify_undelivered.json   toplam 310 · MECHANISM_STALE 208 · MIRROR_DRIFT 51 · NAKED_POSITION 9
    ops/alarm_backlog_digest.py  YAZILMIŞ, çalışıyor, ama HİÇBİR KADANSA ASILI DEĞİL
    improvement_proposals.jsonl  16 öneri, teslimat yolu YOK

Yani sistem hesaplıyor ve kimse okumuyor — bu deponun ölçülmüş hastalığı (`candidate_review.json`
günde 23 bin karakter üretiyor ve karar hattında okuyucusu yok).

SESSİZLİK ŞARTI PAZARLIĞA KAPALI: karar döndürmeyen zamanlanmış iş bildirim spam'idir. Yeni
bir şey yoksa mesaj YOKTUR.
"""
from __future__ import annotations

import importlib.util
import pathlib
import shlex
import subprocess

import pytest

KOK = pathlib.Path(__file__).resolve().parent.parent
BETIK = KOK / "ops/oneri_brifingi.py"
DIGEST_BETIK = KOK / "ops/alarm_backlog_digest.py"
SERVICE = KOK / "deploy/oracle-a1/meridian-brifing.service"
TIMER = KOK / "deploy/oracle-a1/meridian-brifing.timer"


def _yukle():
    assert BETIK.exists(), f"{BETIK} YOK"
    spec = importlib.util.spec_from_file_location("oneri_brifingi", BETIK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _yukle_digest():
    """Kadansın İKİNCİ teslimatı. Ayrı bir betiktir ve ayrı bir damga dosyası tutar; iki betiğin
    çivileri de bu dosyada durur çünkü ikisini de AYNI birim koşturur (biri kırılırsa kadansın
    yarısı sessizce ölür)."""
    assert DIGEST_BETIK.exists(), f"{DIGEST_BETIK} YOK"
    spec = importlib.util.spec_from_file_location("alarm_backlog_digest", DIGEST_BETIK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_BOSKEN_SESSIZ(monkeypatch, sandbox_state):
    """Okunmamış öneri yoksa mesaj ÜRETİLMEZ. Karar döndürmeyen bildirim spam'dir."""
    mod = _yukle()
    from meridian import store
    store.write_jsonl("improvement_proposals.jsonl", [])
    o = mod.ozet_kur()
    assert o["yeni"] == 0
    assert not o["mesaj"], f"boş defterde mesaj üretildi: {o['mesaj']!r}"


def test_YENI_ONERI_MESAJA_GIRER(monkeypatch, sandbox_state):
    """Okunmamış öneri varsa mesajda kimliği ve alanı geçer."""
    mod = _yukle()
    from meridian import store
    store.write_jsonl("improvement_proposals.jsonl", [
        {"ts": "2026-08-27T10:00:00+00:00", "id": "N00017", "alan": "coverage_ariza.hotstate",
         "oneri": "watchdog hotstate sayacını harici süreçten okunur yap", "oncelik": "yuksek"},
    ])
    o = mod.ozet_kur()
    assert o["yeni"] == 1
    assert "N00017" in o["mesaj"] and "coverage_ariza.hotstate" in o["mesaj"]


def test_TESLIMDEN_SONRA_TEKRARLAMAZ(monkeypatch, sandbox_state):
    """Damga basıldıktan sonra aynı öneri ikinci kez bildirilmez."""
    mod = _yukle()
    from meridian import store
    store.write_jsonl("improvement_proposals.jsonl", [
        {"ts": "2026-08-27T10:00:00+00:00", "id": "N00017", "alan": "x", "oneri": "y"},
    ])
    gonderilen = []
    monkeypatch.setattr(mod.notify, "configured", lambda: True)
    monkeypatch.setattr(mod.notify, "send", lambda t: gonderilen.append(t) or True)
    assert mod.main(["--uygula"]) == 0
    assert len(gonderilen) == 1
    assert mod.ozet_kur()["yeni"] == 0, "damga basılmamış — aynı öneri yeniden bildirilir"


def test_KURU_KOSUM_VARSAYILAN(monkeypatch, sandbox_state):
    """`--uygula` olmadan HİÇBİR ŞEY gönderilmez ve damga basılmaz."""
    mod = _yukle()
    from meridian import store
    store.write_jsonl("improvement_proposals.jsonl", [
        {"ts": "2026-08-27T10:00:00+00:00", "id": "N00018", "alan": "x", "oneri": "y"},
    ])
    gonderilen = []
    monkeypatch.setattr(mod.notify, "configured", lambda: True)
    monkeypatch.setattr(mod.notify, "send", lambda t: gonderilen.append(t) or True)
    assert mod.main([]) == 0
    assert not gonderilen, "kuru koşumda gönderdi"
    assert mod.ozet_kur()["yeni"] == 1, "kuru koşumda damga bastı"


def _execstart_satirlari() -> list[str]:
    """Birimin `ExecStart` satırları (yorum/boş satır değil)."""
    return [ln.strip() for ln in SERVICE.read_text(encoding="utf-8").splitlines()
            if ln.strip().startswith("ExecStart")]


def _cagri_kuyruklari(betik: str) -> list[str]:
    """`betik`in ExecStart içindeki HER çağrısını, O ÇAĞRIYA AİT argüman kuyruğuyla döndürür
    (bir sonraki komut ayıracına — `;` `||` `&&` `|` ya da satır sonuna — kadar).

    NEDEN KUYRUK: eski çivi `--uygula`yı DOSYANIN HERHANGİ BİR YERİNDE arıyordu. İki çağrı var ve
    bayrak "teslim eder" ile "sessiz kuru koşum" arasındaki TEK farktır — birinden düşerse dosyada
    hâlâ bir `--uygula` görünür, çivi yeşil kalır ve o teslimat KALICI OLARAK SESSİZ olur."""
    import re
    exec_metni = "\n".join(_execstart_satirlari())
    kuyruklar = []
    for m in re.finditer(re.escape(betik), exec_metni):
        kalan = exec_metni[m.end():]
        kes = re.search(r"[;\n|&]", kalan)
        kuyruklar.append(kalan[:kes.start()] if kes else kalan)
    return kuyruklar


def test_BIRIM_ALARM_DIGESTINI_DE_KOSUYOR():
    """Kadans iki teslimatı da tetiklemeli; biri unutulursa 310'luk yığın orada kalır.

    `--uygula` HER ÇAĞRIDA ayrı ayrı aranır (denetim 2026-08-29): bayrak bir çağrıdan düşerse o
    betik kuru koşuma iner — hiçbir şey göndermez, hiçbir hata da vermez. Kayıp KALICI olarak
    SESSİZDİR, yani tam da bu kadansın kapatmak için var olduğu arıza sınıfı."""
    assert SERVICE.exists() and TIMER.exists(), "systemd birimleri yok"
    for betik in ("alarm_backlog_digest.py", "oneri_brifingi.py"):
        kuyruklar = _cagri_kuyruklari(betik)
        assert kuyruklar, f"{betik} birimin ExecStart'ında hiç çağrılmıyor"
        for k in kuyruklar:
            assert "--uygula" in k, (
                f"{betik} çağrısında `--uygula` YOK ({k!r}) — o teslimat sessiz KURU KOŞUM olur")


def test_BIRIM_ARIZAYI_YUTMAZ_VE_IKISINI_DE_KOSAR(tmp_path):
    """İKİ ŞART BİRDEN, ve ikisi de DAVRANIŞLA sınanır (metin araması değil): birimin kabuk
    komutu gerçek bir `/bin/sh` altında sahte betiklerle koşturulur.

      (a) İlk betik DÜŞSE BİLE ikincisi KOŞAR — biri sussa öteki teslim etsin.
      (b) HERHANGİ biri düşerse birim BAŞARISIZ biter (çıkış kodu != 0).

    NEDEN TEK ExecStart: ayrı `ExecStart=` satırları bu ikisini AYNI ANDA sağlayamaz. `-` öneksiz
    systemd ilk başarısızlıkta durur (b sağlanır, a düşer); `-` önekiyle hata YUTULUR ve birim
    ASLA `failed` olmaz (a sağlanır, b düşer). Eski hâl ikincisiydi: iki betik de "kanal
    yapılandırılmamış"ta 2, "gönderim düştü"de sıfırdan farklı (digest 1, öneri brifingi 2)
    dönüyor — yani Telegram kırılırsa iş HER GÜN sessizce düşer ve bunu bildirecek tek mekanizma
    zaten gönderemeyen işin ta kendisidir."""
    satirlar = _execstart_satirlari()
    assert len(satirlar) == 1, (
        f"tek bir ExecStart sarmalayıcı bekleniyordu, {len(satirlar)} satır var: {satirlar!r}")
    assert not satirlar[0].startswith("ExecStart=-"), (
        "`ExecStart=-` çıkış kodunu YUTAR — birim hiçbir zaman `failed` olmaz")
    parcalar = shlex.split(satirlar[0].split("=", 1)[1])
    assert parcalar[:2] == ["/bin/sh", "-c"], f"beklenmeyen ExecStart biçimi: {parcalar!r}"
    # KAÇIŞ BÜTÜNLÜĞÜ ÖNCE ÖLÇÜLÜR (denetim 2026-08-29). Aşağıdaki `.replace` systemd'nin işini
    # BURADA yapıyor; tek başına bırakılsaydı çivi kendi çözümünü sınardı: birim `exit $rc` diye
    # TEK dolarla yazılsa bu test yine YEŞİL kalır, oysa systemd `$rc`yi BOŞ geçirir ve argümansız
    # `exit` BİR ÖNCEKİ komutun durumunu döndürür — yani tam olarak kapatılan "arıza yutulur"
    # hatası geri gelir, hem de sessizce. Kardeş çivi bunu zaten biliyordu
    # (tests/test_kucuk_kuyruk_v179.py: `assert "$" not in satir`). Burada koşul daha ince:
    # `$$` MEŞRU, tek `$` DEĞİL — çiftleri düşürüp kalan tek dolar var mı diye bakılır.
    assert "$" not in parcalar[2].replace("$$", ""), (
        "ExecStart yükünde KAÇIRILMAMIŞ tek `$` var — systemd onu boşaltır ve argümansız `exit` "
        f"bir önceki komutun durumunu döndürür (arıza yutulur): {parcalar[2]!r}")
    # systemd `$$` ile `$`i kaçırır (meridian-backup.service ile aynı idiom) — gerçek kabuğa
    # verirken çözülür, yoksa burada sınadığımız şey birimin koştuğu şey OLMAZDI.
    yuk_sablonu = parcalar[2].replace("$$", "$")

    gunluk = tmp_path / "kosanlar.txt"
    sahte_python = tmp_path / "sahte-python"
    sahte_python.write_text(
        "#!/bin/sh\n"
        f'basename "$1" >> "{gunluk}"\n'
        'exit "$(cat "$1")"\n', encoding="utf-8")
    sahte_python.chmod(0o755)

    def _kos(alarm_rc: int, oneri_rc: int) -> tuple[int, list[str]]:
        gunluk.write_text("", encoding="utf-8")
        (tmp_path / "alarm_backlog_digest.py").write_text(f"{alarm_rc}\n", encoding="utf-8")
        (tmp_path / "oneri_brifingi.py").write_text(f"{oneri_rc}\n", encoding="utf-8")
        yuk = (yuk_sablonu
               .replace("/opt/meridian/.venv/bin/python", str(sahte_python))
               .replace("/opt/meridian/ops/", f"{tmp_path}/"))
        p = subprocess.run(["/bin/sh", "-c", yuk], capture_output=True, text=True)
        return p.returncode, gunluk.read_text(encoding="utf-8").split()

    kod, kosanlar = _kos(0, 0)
    assert kod == 0, f"ikisi de başarılıyken birim düştü (rc={kod})"
    assert kosanlar == ["alarm_backlog_digest.py", "oneri_brifingi.py"], kosanlar

    kod, kosanlar = _kos(2, 0)   # kanal düştü → digest 2 döner
    assert "oneri_brifingi.py" in kosanlar, (
        f"ilk betik düşünce ikincisi HİÇ KOŞMADI: {kosanlar}")
    assert kod != 0, "ilk betik düştü ama birim BAŞARILI bitti — arıza görünmez"

    kod, kosanlar = _kos(0, 2)   # ikinci teslimat düştü
    assert kosanlar == ["alarm_backlog_digest.py", "oneri_brifingi.py"], kosanlar
    assert kod != 0, "ikinci betik düştü ama birim BAŞARILI bitti — arıza görünmez"


def test_TIMER_GUNLUK():
    t = TIMER.read_text(encoding="utf-8")
    assert "OnCalendar=" in t, "timer takvim tanımı yok"
    assert "Persistent=true" in t, (
        "Persistent yok — makine kapalıyken kaçan tetik telafi edilmez")


def test_TIMER_KIS_SAATINDE_DE_KAPANISTAN_SONRA():
    """DST TUZAĞI (denetim 2026-08-29). ABD kapanışı 16:00 ET SABİTTİR ama UTC karşılığı DEĞİL:
    EDT'de 20:00 UTC, EST'de (Kasım–Mart, yılın BEŞ AYI) 21:00 UTC. 21:00 UTC'lik bir tetik kış
    boyunca TAM KAPANIŞ ZİLİNDE, EOD turundan ÖNCE ateşlerdi — ve birim yorumu bunun tersini
    iddia ediyordu. Kapı: tetik saati her iki rejimde de kapanıştan SONRA olmalı, yani
    >= 22:00 UTC (EST kapanışı 21:00 UTC + EOD turu için pay). Emsal ve gerekçe biçimi:
    `meridian-backup.timer` (23:30 UTC = 18:30/19:30 NY)."""
    import re
    t = TIMER.read_text(encoding="utf-8")
    m = re.search(r"^OnCalendar=\S+ (\d{2}):(\d{2}):(\d{2}) UTC\s*$", t, re.M)
    assert m, f"OnCalendar açıkça UTC saatiyle yazılmalı (sunucu TZ'sine güvenilmez): {t!r}"
    saat = int(m.group(1))
    assert saat >= 22, (
        f"{saat:02d}:00 UTC — EST rejiminde (Kasım–Mart) ABD kapanışı 21:00 UTC'dir; bu tetik "
        f"kapanış zilinde ya da öncesinde ateşler, EOD turu daha bitmemiştir")


def test_dagit_F9_birimleri_IZLIYOR():
    metin = (KOK / "dagit.sh").read_text(encoding="utf-8")
    for ad in ("meridian-brifing.service", "meridian-brifing.timer"):
        assert f"deploy/oracle-a1/{ad}|/etc/systemd/system/{ad}" in metin, f"F9 {ad}'i izlemiyor"


# ---- DÜZELTME TURU 1 (2026-08-29 denetimi) — iki çivi, ikisi de "öneri KALICI kaybolabilir" ----

def test_TS_SIZ_SATIR_SESSIZCE_DUSMEZ(monkeypatch, sandbox_state):
    """ts alanı olmayan/boş bir öneri sessizce dışlanamaz: `"" > ""` her zaman False olduğu için
    eski kod böyle bir satırı NE İLK TURDA NE DE HİÇBİR ZAMAN bildirmiyordu — `toplam`a sayılmaya
    devam ederken mesajda hiç görünmüyordu (kalıcı sessiz dışlama). Düzeltme: ts'siz satır
    KOŞULSUZ `yeni`ye girer ve mesajda ölçülemediği açıkça işaretlenir (UYDURMA YASAĞI: eksik
    alan gizlenmez, beyan edilir; ts UYDURULMAZ)."""
    mod = _yukle()
    from meridian import store
    store.write_jsonl("improvement_proposals.jsonl", [
        {"id": "N00099", "alan": "ts_eksik.alani", "oneri": "ts alanı olmadan üretilmiş satır"},
    ])
    o = mod.ozet_kur()
    assert o["yeni"] == 1, f"ts'siz satır sessizce düşürüldü: {o}"
    assert "N00099" in o["mesaj"] and "ts_eksik.alani" in o["mesaj"]


def test_GONDERIM_PENCERESINDE_EKLENEN_SATIR_KACIRILMAZ(monkeypatch, sandbox_state):
    """Gönderim SIRASINDA (network POST penceresinde) deftere düşen bir satır, mesaj zaten
    KURULDUKTAN sonra geldiği için o turun mesajında YOKTUR. Eski kod damgayı `notify.send`
    DÖNDÜKTEN SONRA yapılan İKİNCİ bir okumadan hesaplıyordu — bu ikinci okuma pencere
    içinde eklenen satırı da görüyor ve damga onu "gördüm" sayıyordu, hiç bildirmemiş olarak.
    Düzeltme: damga yalnız GÖNDERİLEN mesajı üreten enstantaneden ilerler; gönderim sonrası
    ikinci bir defter okuması YOK."""
    mod = _yukle()
    from meridian import store
    store.write_jsonl("improvement_proposals.jsonl", [
        {"ts": "2026-08-27T10:00:00+00:00", "id": "N00020", "alan": "x", "oneri": "ilk satır"},
    ])

    def _sahte_gonder(text):
        # notify.send'in GERÇEK ağ çağrısı sırasında BAŞKA bir yazar (nous_eval.py gibi) deftere
        # yeni bir satır ekliyor — bu satır gönderilen `text`te YOKTUR.
        store.write_jsonl("improvement_proposals.jsonl", [
            {"ts": "2026-08-27T10:00:00+00:00", "id": "N00020", "alan": "x", "oneri": "ilk satır"},
            {"ts": "2026-08-27T10:05:00+00:00", "id": "N00021", "alan": "y",
             "oneri": "gönderim sırasında eklendi"},
        ])
        return True

    monkeypatch.setattr(mod.notify, "configured", lambda: True)
    monkeypatch.setattr(mod.notify, "send", _sahte_gonder)
    assert mod.main(["--uygula"]) == 0

    o2 = mod.ozet_kur()
    assert o2["yeni"] == 1, (
        f"gönderim penceresinde eklenen satır bir sonraki turda KAÇIRILDI: {o2}")
    assert "N00021" in o2["mesaj"]


def test_DIGEST_GONDERIM_PENCERESINDE_ARTAN_SAYAC_KACIRILMAZ(monkeypatch, sandbox_state):
    """`test_GONDERIM_PENCERESINDE_EKLENEN_SATIR_KACIRILMAZ`ın İKİZİ — bu kez alarm yığını için.
    Aynı kusur (2026-08-29 denetiminde ayrı kalem olarak kaydedilmişti, bu turda kapatıldı).

    `alarm_backlog_digest.py` damgayı `_damgala` İÇİNDE, kilitli güncellemenin TAZE okumasından
    hesaplıyordu (`int(d.get("_toplam"))`) — GÖNDERİLEN mesajı üreten enstantaneden değil. Mesajın
    kurulmasıyla damganın basılması arasında tam bir `events.jsonl` taraması VE 8 saniyelik bir ağ
    POST'u var. O pencerede `obs._maybe_notify`ın sayaca yazdığı her alarm, kendisinden hiç söz
    ETMEYEN bir mesajla "kapsandı" damgası yerdi. Ve sayaçlar ASLA azalmadığı için
    (`yeni = toplam - kapsanan`) o alarm bir daha HİÇBİR özete giremezdi — kalıcı sessiz kayıp,
    üstelik alarm yığınının kendi teslimat mekanizmasında.

    Düzeltme: damga `o` enstantanesinden basılır. Kardeş betikteki (`oneri_brifingi.py`) çözümün
    birebir aynısı."""
    mod = _yukle_digest()
    from meridian import store
    store.write_json("notify_undelivered.json", {"_toplam": 5, "MECHANISM_STALE": 5})

    def _sahte_gonder(text):
        # notify.send'in ağ POST'u sürerken canlı worker yeni bir alarmı sayaca yazıyor. Bu
        # alarm gönderilen `text`te YOKTUR — mesaj çoktan kurulmuştu.
        assert "MIRROR_DRIFT" not in text, "kurgu hatası: yeni alarm mesajda görünmemeli"
        store.write_json("notify_undelivered.json",
                         {"_toplam": 8, "MECHANISM_STALE": 5, "MIRROR_DRIFT": 3})
        return True

    monkeypatch.setattr(mod.notify, "configured", lambda: True)
    monkeypatch.setattr(mod.notify, "send", _sahte_gonder)
    assert mod.main(["--uygula"]) == 0

    o2 = mod.ozet_kur()
    assert o2["yeni"] == 3, (
        f"gönderim penceresinde biriken alarmlar 'kapsandı' damgası yedi ve KALICI olarak "
        f"kayboldu: {o2}")
    assert "MIRROR_DRIFT" in o2["mesaj"]


def test_BIRIM_YANLISLIKLA_ENABLE_EDILEMEZ():
    """Servis birimi `[Install]` TAŞIMAZ — tetiği YALNIZ timer'dır.

    NEDEN. `deploy.sh` bilerek yalnız `meridian-brifing.timer`ı enable eder (birimin kendisini
    DEĞİL, yorumunda da yazılı). Ama serviste bir `[Install] WantedBy=multi-user.target`
    dururken `systemctl enable meridian-brifing.service` SESSİZCE başarılı olur ve birime
    kimsenin istemediği bir AÇILIŞ KOŞUMU ekler — timer'ın kadansının dışında, `Persistent`
    telafisiyle karışan ikinci bir tetik. `[Install]` yokken aynı komut "no installation config"
    diye DÜŞER: operatör hatası sessiz davranış değişikliği değil, görünür bir hata olur.

    FİLO ÖLÇÜMÜ (varsayılmadı): timer-tetikli oneshot kardeşlerden `meridian-backup.service` ve
    `meridian-tick-watchdog.service` `[Install]` TAŞIMIYOR. `meridian-aylik-bucket-kopya.service`
    taşıyor — konvansiyon filoda AYRIK, bu yüzden çivi sınıf değil BU birime kapsanmıştır;
    çalışan dağıtılmış bir birimi bu turda değiştirmek kapsam dışıdır.
    """
    # BÖLÜM BAŞLIĞI aranır, ALT-DİZGE DEĞİL: dosyanın kendisi bölümün NEDEN olmadığını yorumda
    # anlatıyor ve o yorum "[Install]" dizgesini İÇERİYOR. Alt-dizge araması bu çiviyi, bölüm
    # gerçekten kaldırıldıktan SONRA bile kırmızı tutardı — ölçtüğünü sandığı şeyi ölçmeyen
    # çivi sınıfı. systemd bölüm başlığı satırın TAMAMIDIR; `#`/`;` ile başlayan satır yorumdur.
    satirlar = [ln.strip() for ln in SERVICE.read_text(encoding="utf-8").splitlines()]
    bolumler = [ln for ln in satirlar if ln and not ln.startswith(("#", ";"))]
    assert "[Install]" not in bolumler, (
        "meridian-brifing.service bir `[Install]` BÖLÜMÜ taşıyor — `systemctl enable "
        "meridian-brifing.service` sessizce geçer ve timer'dan bağımsız bir açılış koşumu ekler; "
        "tetik YALNIZ meridian-brifing.timer olmalı"
    )


def test_deploy_sh_BIRIMLERI_KURAR_ama_KADANSI_ACMAZ():
    """`deploy.sh` iki birimi + hermes config'ini KURAR, ama kadansı KOŞULSUZ AÇMAZ.

    İKİ AYRI ARIZA, tek çivi. (a) Kurulum adımının unutulması: bulgu 6'nın kendisi buydu ve
    emsali `test_kucuk_kuyruk_v179.py::test_deploy_sh_bekciyi_KURAR` — bekçi 2026-07-31'de
    CANLIDA elle doğmuş, depoya hiç girmemişti. (b) Kurulumun ETKİNLEŞTİRME ile aynı eylem
    olması: `cutover.sh` adım 4 `deploy.sh`i çağırır, yani ilgisiz bir sebeple koşan tek bir
    dağıtım operatöre GÜNLÜK TELEGRAM kadansı açardı — kimse karar vermeden. Kurulum zararsız,
    teslimat değil; kapı `is-enabled` üstünde ve İLK açılışa bakar (sonrası idempotent).
    """
    d = (KOK / "deploy/oracle-a1/deploy.sh").read_text(encoding="utf-8")
    for parca in ("meridian-brifing.service       /etc/systemd/system/",
                  "meridian-brifing.timer         /etc/systemd/system/",
                  'cp deploy/hermes/config.yaml "$HOME/.hermes/config.yaml"'):
        assert parca in d, f"deploy.sh kurmuyor: {parca}"

    # KOŞULSUZ enable YASAK: `enable --now meridian-brifing.timer` geçen HER satır bir `if`
    # gövdesinin İÇİNDE olmalı. Girinti ölçülür — kardeş timer'lar sütun 0'da, bu değil.
    satirlar = [ln for ln in d.splitlines()
                if "enable --now meridian-brifing.timer" in ln and not ln.lstrip().startswith(("#", "echo"))]
    assert satirlar, "deploy.sh brifing timer'ını hiç enable etmiyor — açıldıktan sonra dağıtımlar onu kapatır"
    for ln in satirlar:
        assert ln.startswith((" ", "\t")), (
            "brifing timer'ı KOŞULSUZ enable ediliyor — ilgisiz bir deploy.sh koşumu günlük "
            f"Telegram kadansını operatör kararı olmadan açar: {ln!r}")
    assert "is-enabled meridian-brifing.timer" in d, \
        "kapı `is-enabled` üstünde kurulmamış — 'zaten açıksa açık tut' davranışı ölçülemez"
    # Kapalı dalda operatöre TAM komut verilir: 'bir yerde yazılıdır' yetmez, ekranda olmalı.
    assert "sudo systemctl enable --now meridian-brifing.timer" in d, \
        "kapalı dal operatöre açma komutunu BASMIYOR"


def test_DAMGA_SAYACI_ASARSA_IYI_HUYLU_HICLIK_GIBI_GORUNMEZ(sandbox_state):
    """`kapsanan > toplam` İMKÂNSIZ bir durumdur ve İMKÂNSIZ diye rapor edilmeli.

    NEDEN. Damga artık `o["toplam"]`dan basılıyor (denetimin CRITICAL'ı) ve bu doğru: `_toplam`
    yalnız ARTAN bir sayaçtır (`meridian/obs.py` `_bump`/`_bump_fail`: `int(...) + 1`, azaltan
    tek bir yol yok). Ama sözleşme bir gün kırılırsa — sayaç sıfırlanır, dosya elle düzenlenir,
    bir geri yükleme eski `notify_undelivered.json`u koyar — `yeni = toplam - kapsanan` NEGATİF
    olur ve eski kod `yeni <= 0` dalına düşüp *"damgadan beri yeni birikme yok"* derdi. Yani
    özet KALICI OLARAK susar ve sustuğunu **iyi huylu bir idempotens** diye rapor eder.

    Bu, bu depoda adı konmuş sınıftır: ölçülemeyen bir durum iyi huylu bir hiçlik gibi
    görünemez (UYDURMA YASAĞI; aynı turda `_mutabakat_bayatligi` da bu yüzden `None + neden`
    döndürecek şekilde yazıldı). Sıfır ile 'bilmiyorum' aynı şey değildir.
    """
    from meridian import store as _store
    import importlib
    m = importlib.import_module("ops.alarm_backlog_digest")
    importlib.reload(m)

    # Damga sayacı AŞIYOR: 5 kapsanmış, ama toplam 3 (sayaç geri gitmiş).
    _store.write_json(m.UNDELIVERED, {
        "_toplam": 3, "MECHANISM_STALE": 3,
        m.DAMGA: {"ts": "2026-08-29T00:00:00Z", "toplam_kapsanan": 5},
    })
    o = m.ozet_kur()
    assert o.get("hata"), (
        "kapsanan(5) > toplam(3) İMKÂNSIZ durumu hata olarak raporlanmadı — özet sessizce "
        f"'yeni birikme yok' diyor ve bir daha hiç konuşmaz: {o!r}")
    assert "3" in str(o["hata"]) and "5" in str(o["hata"]), \
        f"hata mesajı iki sayıyı da taşımalı (teşhis edilemez hata işe yaramaz): {o['hata']!r}"
