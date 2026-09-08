"""test_dagit_istenen_durum_v367.py — dagit bakım penceresi birim İSTENEN-DURUM koruması
(TSK-092/TSK-008; vaka ×2: 2026-08-31 + 2026-09-01 gecesi).

VAKA: operatör kararıyla `meridian-learn` geri-dolum bitene dek disabled+stopped; dagit'in
[4] bakım penceresi SABİT ÜÇLÜ `systemctl start` satırıyla onu her dağıtımda geri açtı —
iki gece üst üste elle yakalandı/durduruldu. "Her dağıtım sonrası learn kapalı mı" kontrolü
insana yaslanıyordu ve insan (Rol-1 dahil) atladı.

SÖZLEŞME: istenen durum systemd'nin KENDİ beyanıdır (`is-enabled`), o ANKİ durum ise
`is-active`. Bakım penceresi:
  * yalnız PENCERE ÖNCESİ aktif olanı DURDURUR — aday kümesi (üçlü) kalır ama stop satırında
    birim adı SABİTLENEMEZ: zaten `inactive` olan birime stop GÖNDERİLMEZ (2026-09-03 kapsam
    genişlemesi, TSK-092 (a)). Ölçüt `!= inactive`: `activating`/`deactivating`/`failed`
    hâllerinde süreç ya da artık durum vardır, durdurmak güvenli YÖNDÜR; yalnız temiz
    `inactive` atlanır. Bedeli beyanlı: operatörün elle başlattığı disabled birim pencereden
    sonra kapalı kalır (start `is-enabled`'dan türer), isteyen enable eder,
  * yalnız `enabled` olanı GERİ BAŞLATIR — start satırında birim adı SABİTLENEMEZ,
  * atlananı ADIYLA raporlar (sessiz atlama, sessiz başlatmayla aynı sınıf körlüktür),
  * `meridian` çekirdek birimi başlatma listesinde DEĞİLSE dağıtım yüksek sesle durur
    (motoru kapalı bırakan pencere sessiz olamaz).

R-0 (düzeltme turu 1, 2026-09-03): SÖZLEŞMEYE ÜÇÜNCÜ MADDE — `enabled + inactive` bir ANOMALİDİR
ve dağıtımı DURDURUR ([F10] kapısı, `exit 3`, rsync'ten ve stop'tan ÖNCE, kuru koşumda da).
Gerekçe A1'de ölçüldü (2026-09-03 09:40Z): üç aday birim de `Type=simple` + `Restart=always`,
`TriggeredBy=` boş — yani bu hâl normal değil, ya elle `stop` edilmiştir (kalıcı niyet
`disable --now` ile beyan edilmeliydi) ya da start-limit'e çarpıp düşmüştür (arıza). İki hâlde de
pencere birimi `is-enabled`dan türetip sessizce diriltir ve bir olayı MASKELER. Bu kapı `_BASLAT`
türetiminin kopyası değildir: `_BASLAT` "ne başlatılmalı", [F10] "ölçülen dünya tutarlı mı" diye
sorar. Override bayrağı YOK.

YÖNTEM (v266 ailesi): adımlar A1 ister, koşturulamaz — ölçülen katman yapı/sözleşmedir, her
çivi bu docstring'deki bir maddeye çapalı. İSTİSNA: kapıların YÖNÜ metin araması değil GERÇEK
Jinja değerlendirmesiyle ölçülür (`!= 'inactive'` ile `== 'inactive'` aynı dizgeleri taşır;
metin çivisi yeşilken yaşayan bir tuzak ölçüldü — 2026-09-02 sabah penceresi).

TAŞIMA KAYDI (TSK-176 Faz A1 Task 3, 2026-09-08) — BU DOSYANIN TAMAMINI İLGİLENDİRİR.
[4] penceresi ve [F10] kapısı `dagit.sh`tan `deploy/ansible/dagit.yml`e taşındı; `dagit.sh` ince
bir sarmalayıcıya indi. Çivilerin HİÇBİRİ silinmedi ve hiçbirinin İDDİASI değişmedi — değişen tek
şey ölçülen kaynak ve yöntemdir:
  * kabuk türetme snippet'i (`_DURDUR`/`_BASLAT` + sahte `systemctl`) → görevlerin `when`
    ifadelerinin Jinja ile ÇÖZÜLMESİ. Sahte `systemctl` yerini senaryo tablosuna bıraktı:
    ölçülen dünya artık bir şim değil, ölçümün KENDİ olgu haritası (`pencere_aktif`/`pencere_etkin`).
  * `set -e` altındaki atama tuzağı (2026-09-02 vakası: disabled SON eleman uzak kabuğu 1 ile
    bitirdi ve dagit'i sessizce öldürdü) → `failed_when` sözleşmesinin ÖLÇÜMÜ: `is-enabled`in
    rc 1'i (disabled) ARIZA SAYILMAZ. Aynı sınıf, aracın dilinde.
  * kapı metninde `exit 3` → görevin `assert`i ve o assert'in YÖNÜ.
"""
from __future__ import annotations

import pathlib
import re
import subprocess

# TEK KAYNAK (Task 3): `dagit.yml` okuyucuları + Jinja değerlendiricisi v452'de yaşıyor.
from tests.test_ansible_dagit_v452 import (
    birim_adaylari,
    gorev_etiketleri,
    gorev_metni,
    gorevler,
    jinja_cozumle,
    kapi_indeksi,
    playbook_degiskenleri,
    systemd_durumu,
    when_degerlendir,
)

DAGIT = pathlib.Path(__file__).resolve().parent.parent / "dagit.sh"
ADAYLAR = ("meridian", "meridian-barsarchive", "meridian-learn")


def _kapi_gorevleri(etiket: str) -> list[dict]:
    return [g for g in gorevler() if etiket in gorev_etiketleri(g)]


def _blok(etiket: str) -> str:
    """Bir kapının bütün görevlerinin YAML dökümü (eski `_BLOK`un karşılığı)."""
    parcalar = [gorev_metni(g) for g in _kapi_gorevleri(etiket)]
    assert parcalar, f"dagit.yml'de `[{etiket}]` etiketli görev yok — çivi bayatlamış"
    return "\n".join(parcalar)


def _durum_gorevi(durum: str) -> dict:
    bulunan = [g for g in _kapi_gorevleri("4") if systemd_durumu(g) == durum]
    assert len(bulunan) == 1, \
        f"[4] içinde `state: {durum}` görevi TEK olmalı, {len(bulunan)} var"
    return bulunan[0]


def _pencere_degiskenleri(birim: str, enabled: dict, active: dict) -> dict:
    """Bir dünyayı (etkinlik/aktiflik haritaları) playbook değişkenlerine çevirir."""
    degiskenler = playbook_degiskenleri()
    degiskenler.update({"item": birim, "pencere_etkin": dict(enabled),
                        "pencere_aktif": dict(active)})
    return degiskenler


def test_sozdizimi_gecerli():
    p = subprocess.run(["bash", "-n", str(DAGIT)], capture_output=True, text=True)
    assert p.returncode == 0, p.stderr


def test_start_satiri_birim_adi_sabitleyemez():
    """Vakanın kökü: `systemctl start meridian meridian-barsarchive meridian-learn` sabit paketi.

    TAŞIMA: "satır birimi sabitleyemez" → "görev birimi sabitleyemez". Ölçü, görevin `name`
    argümanının bir DÖNGÜ değişkeni olması ve döngünün TEK KAYNAK listeden gelmesidir."""
    bas = _durum_gorevi("started")
    args = bas.get("ansible.builtin.systemd_service") or bas.get("systemd_service")
    assert str(args.get("name")).strip() in ("{{ item }}", "{{item}}"), (
        f"start görevi birimi SABİTLİYOR (name={args.get('name')!r}) — TSK-092: istenen durum "
        "systemd'nin kendi beyanıdır, sabit bir paket operatörün kararını bozar")
    assert "birim_adaylari" in str(bas.get("loop")), (
        f"start döngüsü aday listesinden gelmiyor: {bas.get('loop')!r}")


def test_baslatma_listesi_is_enabled_ile_turetilir():
    assert "is-enabled" in _blok("4"), "[4] bloğunda istenen-durum (is-enabled) türetimi yok"


def test_atlanan_birim_adiyla_raporlanir():
    assert "başlatılmadı" in _blok("4"), "atlanan birim raporu yok (sessiz atlama)"


def test_cekirdek_birim_guvenlik_kapisi():
    """`meridian` enabled değilse pencere yüksek sesle DURUR (motoru kapalı bırakan pencere
    sessiz olamaz). Kapının YÖNÜ Jinja ile çözülür, metinde aranmaz."""
    kapilar = [g for g in _kapi_gorevleri("4")
               if (g.get("ansible.builtin.assert") or g.get("assert"))
               and "meridian" in gorev_metni(g)]
    assert kapilar, "çekirdek-birim kapısı ([4] içinde `assert`li) bulunamadı"
    kosullar = (kapilar[0].get("ansible.builtin.assert")
                or kapilar[0].get("assert")).get("that")
    for etkinlik, gecmeli in (("enabled", True), ("disabled", False), ("static", False)):
        dunya = _pencere_degiskenleri(
            "meridian", {u: etkinlik for u in ADAYLAR}, {u: "active" for u in ADAYLAR})
        assert when_degerlendir(kosullar, dunya) is gecmeli, (
            f"çekirdek-birim kapısı yanlış yön: meridian={etkinlik} → geçmeli={gecmeli}")


def test_stop_satiri_birim_adi_sabitleyemez():
    """TSK-092 (a), 2026-09-03: stop satırı da sabit üçlü paket OLAMAZ — pencere öncesi
    `is-active` ölçülür, zaten inactive birime stop gönderilmez. (Önceki sözleşme "durdurma
    kümesi sabit kalabilir" diyordu; aday KÜMESİ hâlâ üçlü, sabitlenemeyen şey stop SATIRIdır.)"""
    dur = _durum_gorevi("stopped")
    args = dur.get("ansible.builtin.systemd_service") or dur.get("systemd_service")
    assert str(args.get("name")).strip() in ("{{ item }}", "{{item}}"), (
        f"stop görevi birimi SABİTLİYOR (name={args.get('name')!r})")
    assert "birim_adaylari" in str(dur.get("loop")), (
        f"stop döngüsü aday listesinden gelmiyor: {dur.get('loop')!r}")


def test_durdurma_aday_kumesi_ucluyu_kapsar():
    """Aday kümesi daralmadı: ölçüm hâlâ üç birimi de SORAR (biri unutulursa 2026-08-24
    `meridian-learn` unutma vakası tekrarlanır)."""
    assert "is-active" in _blok("4"), "[4] bloğunda o-anki-durum (is-active) türetimi yok"
    for u in ADAYLAR:
        assert u in birim_adaylari(), f"durdurma aday kümesinde {u} yok — küme daraltılmış"


def test_atlanan_stop_adiyla_raporlanir():
    assert "stop gönderilmedi" in _blok("4"), \
        "zaten inactive birim ADIYLA raporlanmıyor (sessiz atlama, sessiz start ile aynı sınıf)"


def test_stop_listesi_is_active_ten_turer():
    """TSK-092 (a) DAVRANIŞ çivisi. Tek dünyada üç hüküm:
      * `meridian` enabled+active                    → İKİSİNİ de alır,
      * `meridian-barsarchive` DISABLED ama AKTİF    → stop ALIR, start ALMAZ (beyanlı bedel:
        operatörün elle başlattığı disabled birim pencereden sağ çıkmaz — kalıcılık `enable`dır),
      * `meridian-learn` disabled ve inactive        → ne stop ne start ALIR.

    DÜNYA DEĞİŞTİ (R-0, düzeltme turu 1, 2026-09-03): önceki hâlde `meridian-barsarchive`
    `enabled + inactive` idi. O hâl artık bir ANOMALİdir ve [F10] kapısı dağıtımı durdurur
    (`test_enabled_ama_INAKTIF_birim_DAGITIMI_DURDURUR`) — yani pencereye HİÇ gelinmez.
    "inactive birime stop gönderilmez" hükmü burada `meridian-learn` üzerinden ölçülüyor."""
    enabled = {"meridian": "enabled", "meridian-barsarchive": "disabled",
               "meridian-learn": "disabled"}
    active = {"meridian": "active", "meridian-barsarchive": "active",
              "meridian-learn": "inactive"}
    dur, bas = _durum_gorevi("stopped"), _durum_gorevi("started")
    duracak = [u for u in ADAYLAR
               if when_degerlendir(dur.get("when"), _pencere_degiskenleri(u, enabled, active))]
    baslayacak = [u for u in ADAYLAR
                  if when_degerlendir(bas.get("when"), _pencere_degiskenleri(u, enabled, active))]
    assert duracak == ["meridian", "meridian-barsarchive"], (
        f"stop listesi yanlış: {duracak} — aktif ikili beklenirdi; inactive `meridian-learn` "
        f"stop ALMAZ, `is-enabled` stop tarafını HİÇ ilgilendirmez")
    assert baslayacak == ["meridian"], (
        f"start listesi yanlış: {baslayacak} — disabled iki birim de dışarıda kalmalıydı "
        f"(elle başlatılmış olması istenen durumu DEĞİŞTİRMEZ)")


def test_stop_listesi_temiz_olmayan_halleri_kapsar():
    """Ölçüt `= active` DEĞİL `!= inactive`: `activating`/`failed` hâllerinde süreç ya da
    artık durum vardır; atlanırsa eski bytecode pencereden sağ çıkar (2026-08-24 sınıfı)."""
    enabled = {"meridian": "enabled", "meridian-barsarchive": "enabled",
               "meridian-learn": "disabled"}
    active = {"meridian": "activating", "meridian-barsarchive": "failed",
              "meridian-learn": "inactive"}
    dur = _durum_gorevi("stopped")
    duracak = [u for u in ADAYLAR
               if when_degerlendir(dur.get("when"), _pencere_degiskenleri(u, enabled, active))]
    assert duracak == ["meridian", "meridian-barsarchive"], (
        f"stop listesi yanlış: {duracak} — activating/failed durdurulur, yalnız temiz "
        f"inactive atlanır")


# =================================================================================================
# [F10] İSTENEN-DURUM ANOMALİSİ — `enabled + inactive` = DAĞITIM DUR (R-0, düzeltme turu 1)
# -------------------------------------------------------------------------------------------------
# ÖLÇÜM (Rol-1, A1'de, 2026-09-03 09:40Z): üç aday birim de `Type=simple` + `Restart=always` ve
# `TriggeredBy=` BOŞ (hiçbir zamanlayıcı tetiklemiyor). Bu üç olgunun birlikte anlamı şudur:
# `enabled + inactive` bir SİMPLE birimin normal durumu DEĞİLDİR — ya elle `stop` edilmiştir
# (kalıcı niyet `disable --now` ile beyan edilmeliydi) ya da start-limit'e çarpıp DÜŞMÜŞTÜR
# (arıza). İki hâlde de [4] penceresi birimi `is-enabled`dan türetip sessizce DİRİLTİR ve bir
# olayı maskeler — TSK-092'nin kapattığı "sessiz geri açma" sınıfının ikinci yüzü.
# Bu kapı `_BASLAT` türetiminin KOPYASI DEĞİLDİR: `_BASLAT` "ne başlatılmalı" diye sorar, bu
# kapı "ölçülen dünya kendi içinde tutarlı mı" diye sorar (anomali). Override bayrağı YOK.
# =================================================================================================

#: TAŞIMA (Task 3): kapı artık bir kabuk bloğu değil, bir `set_fact` (anomali listesi) + bir
#: `assert` (hüküm). Sökücü de sahte `systemctl` de gerekmez: dünya doğrudan olgu haritası
#: olarak verilir ve ifade GERÇEKTEN çözülür.
def _f10_anomali_ifadesi() -> str:
    gorev = [g for g in _kapi_gorevleri("F10")
             if isinstance(g.get("ansible.builtin.set_fact") or g.get("set_fact"), dict)
             and "f10_anomali" in (g.get("ansible.builtin.set_fact") or g.get("set_fact"))]
    assert gorev, "[F10] anomali listesini kuran `set_fact` yok — çivi bayatlamış"
    args = gorev[0].get("ansible.builtin.set_fact") or gorev[0].get("set_fact")
    return str(args["f10_anomali"])


def _f10_kapisi() -> dict:
    kapilar = [g for g in _kapi_gorevleri("F10")
               if g.get("ansible.builtin.assert") or g.get("assert")]
    assert len(kapilar) == 1, f"[F10] tek bir `assert` kapısı olmalı, {len(kapilar)} var"
    return kapilar[0]


def _f10_kos(enabled, active):
    """Kapıyı GERÇEKTEN değerlendirir: (anomali listesi, kapı geçti mi)."""
    degiskenler = playbook_degiskenleri()
    degiskenler["birim_adaylari"] = list(ADAYLAR)
    degiskenler["f10_enabled"] = {
        "results": [{"stdout": enabled[u]} for u in ADAYLAR]}
    degiskenler["f10_active"] = {
        "results": [{"stdout": active[u]} for u in ADAYLAR]}
    anomali = jinja_cozumle(_f10_anomali_ifadesi(), degiskenler)
    degiskenler["f10_anomali"] = anomali
    kapi = _f10_kapisi().get("ansible.builtin.assert") or _f10_kapisi().get("assert")
    return anomali, when_degerlendir(kapi["that"], degiskenler)


def test_enabled_ama_INAKTIF_birim_DAGITIMI_DURDURUR():
    """R-0 ASIL ÇİVİSİ: `meridian-barsarchive` enabled ama inactive → kapı DURUR, birimi ADIYLA
    basar ve İKİ çareyi de adıyla söyler. Eskiden bu dünya "stop YOK / start VAR" diye sessizce
    geçiyordu; pencere birimi diriltir ve düşüşün nedeni hiç sorulmazdı.

    TAŞIMA (Task 3): `exit 3` yerine `assert`in YÖNÜ, sahte `systemctl` yerine olgu haritası."""
    enabled = {"meridian": "enabled", "meridian-barsarchive": "enabled",
               "meridian-learn": "disabled"}
    active = {"meridian": "active", "meridian-barsarchive": "inactive",
              "meridian-learn": "inactive"}
    anomali, gecti = _f10_kos(enabled, active)
    assert anomali == ["meridian-barsarchive"], (
        f"anomali listesi yanlış: {anomali} — enabled+inactive birim tam olarak budur")
    assert gecti is False, (
        "anomali kapısı DURMADI — enabled+inactive birim pencerede sessizce diriltilir")
    mesaj = str((_f10_kapisi().get("ansible.builtin.assert")
                 or _f10_kapisi().get("assert")).get("fail_msg", ""))
    assert "f10_anomali" in mesaj, "duran birim ADIYLA raporlanmıyor"
    assert "systemctl start" in mesaj, "ilk çare (start) adıyla basılmıyor"
    assert "systemctl disable --now" in mesaj, "ikinci çare (disable --now) adıyla basılmıyor"


def test_anomali_YOKKEN_kapi_gecirir():
    """BUGÜNKÜ CANLI DÜNYA (ölçüldü 2026-09-03 09:40Z): meridian enabled/active ·
    barsarchive enabled/active · learn disabled/inactive → DUR tetiklenmez. Kapı her dağıtımı
    durduran bir duvar olsaydı ilk gün devre dışı bırakılırdı."""
    enabled = {"meridian": "enabled", "meridian-barsarchive": "enabled",
               "meridian-learn": "disabled"}
    active = {"meridian": "active", "meridian-barsarchive": "active",
              "meridian-learn": "inactive"}
    anomali, gecti = _f10_kos(enabled, active)
    assert anomali == [], f"temiz dünyada anomali bulundu: {anomali}"
    assert gecti is True, "temiz dünyada kapı durdu"


def test_anomali_kapisi_STOPTAN_ve_RSYNCTEN_ONCE():
    """YER ÖLÇÜLÜR, VARSAYILMAZ: kapı rsync'ten sonra düşseydi yeni kod diske inmiş, süreç eski
    kodda kalmış olurdu ([5b]'nin kapattığı "iki gerçek" hâli); stop'tan sonra düşseydi worker
    zaten durdurulmuş olurdu. Kapı üçünden de ÖNCE."""
    i_kapi = gorevler().index(_f10_kapisi())
    i_rsync = kapi_indeksi("2")
    i_stop = gorevler().index(_durum_gorevi("stopped"))
    assert i_kapi < i_rsync < i_stop, (
        f"anomali kapısının yeri yanlış (kapı={i_kapi} rsync={i_rsync} stop={i_stop})")


def test_anomali_kapisi_kuru_kosumda_da_OLCULUR():
    """Kapı `--check`te de ÖLÇER: kuru koşum anomaliyi görmezse "erken gerçek" kaybolur.

    TAŞIMA (Task 3): eski karşılığı "kapı `--uygula` çıkışından ÖNCE duruyor mu" idi; playbook'ta
    kuru koşumda KOŞAN görevin işareti `check_mode: false`tur."""
    olcenler = [g for g in _kapi_gorevleri("F10")
                if (g.get("ansible.builtin.command") or g.get("command"))]
    assert olcenler, "[F10] hiçbir ölçüm görevi yok — kapı neye bakıyor?"
    kor = [g.get("name") for g in olcenler if g.get("check_mode") is not False]
    assert not kor, (
        f"[F10] ölçümü kuru koşumda ATLANIYOR ({kor}) — `--check` anomaliyi göremez ve kapı "
        "yalnız gerçek dağıtımda, yani en pahalı anda konuşur")


def test_anomali_kapisi_HICBIR_SEY_DEGISTIRMEZ_ve_OVERRIDE_TASIMAZ():
    """Kapı yalnız OKUR: [F10] görevlerinde durum değiştiren bir modül yok. Ve override bayrağı
    YOK — anomali, bilinçli bir hâle (start ya da disable --now) çevrilmeden geçilemez; bayrak
    eklenseydi "her seferinde geç" alışkanlığı kapıyı ilk haftada sessizleştirirdi."""
    for gorev in _kapi_gorevleri("F10"):
        assert systemd_durumu(gorev) is None, (
            f"{gorev.get('name')!r}: [F10] bir birimin DURUMUNU değiştiriyor — kapı yalnız OKUR")
        komut = str((gorev.get("ansible.builtin.command") or gorev.get("command") or {}))
        assert not re.search(r"systemctl\s+(stop|start|disable|enable|restart)\b", komut), (
            f"{gorev.get('name')!r}: [F10] ölçüm komutu durum DEĞİŞTİRİYOR: {komut}")
    # ŞERHLER SOYULUR (v286/v381 `soy` dersi): kararın gerekçesi YASAKLANAN ŞEYİ ALINTILAR —
    # `fail_msg` operatöre `systemctl start <birim>` ÇARESİNİ basar ve o bir çalıştırma değildir.
    kapi = _f10_kapisi()
    kosullar = str((kapi.get("ansible.builtin.assert") or kapi.get("assert")).get("that"))
    assert "f10_anomali" in kosullar, "kapı anomali listesini okumuyor"
    for bayrak in ("zorla", "force", "f10_gec", "anomali_gec", "atla"):
        assert bayrak not in gorev_metni(kapi), (
            f"anomali kapısında override bayrağı var ({bayrak}) — R-0 bunu yasaklıyor")


def test_stop_bos_listede_gonderilmez():
    """Üçü de inactive ise HİÇBİR stop gönderilmez.

    TAŞIMA (Task 3): kabukta bu bir `[[ -n "${_DURDUR// /}" ]]` korumasıydı (argümansız
    `systemctl stop` uzak kabuğu düşürür ve `set -e` pencereyi ortasından keserdi). Ansible'da
    koruma YAPISALDIR — görev bir DÖNGÜdür ve her öğe kendi `when`inden geçer; boş küme sıfır
    çağrı demektir. Ölçülen şey o yapının KORUNMASI: `when`i olmayan ya da döngüsüz bir stop
    görevi, aynı sınıfı geri açardı."""
    dur = _durum_gorevi("stopped")
    assert dur.get("loop") is not None, \
        "stop görevi DÖNGÜ değil — boş aday kümesinde bile bir çağrı üretirdi"
    assert dur.get("when") is not None, "stop görevinin `when`i yok — her aday stop alırdı"
    hepsi_inactive = {u: "inactive" for u in ADAYLAR}
    duracak = [u for u in ADAYLAR
               if when_degerlendir(dur.get("when"),
                                   _pencere_degiskenleri(u, {u2: "enabled" for u2 in ADAYLAR},
                                                         hepsi_inactive))]
    assert duracak == [], f"hepsi inactive iken stop gönderiliyor: {duracak}"


def test_olcum_DISABLED_birimi_ARIZA_SAYMAZ():
    """VAKA 2026-09-02 (sabah penceresi, ilk gerçek koşum): `[ … ] && printf` kalıbı döngünün
    SON elemanı disabled olunca uzak kabuğu 1 ile bitirdi; ssh 1 döndürdü, yerel `set -e`
    `_BASLAT=$( … )` atamasında dagit'i [4] başlığından hemen sonra SESSİZCE öldürdü — rsync
    inmiş, worker restart edilmemiş, beyan yazılmamıştı (iki gerçek: diskte yeni, süreçte eski
    kod).

    TAŞIMA (Task 3): aynı sınıf, aracın dilinde. `systemctl is-enabled` DISABLED bir birim için
    rc 1 döndürür ve Ansible bunu VARSAYILAN OLARAK ARIZA sayar — görev düşer, pencere hiç
    açılmaz. Koruma `failed_when` sözleşmesindedir ve bu çivi onu ölçer: rc 1 (disabled) ile
    rc 4 (birim yok) ARIZA DEĞİLDİR, rc 2 gibi sözleşme dışı bir kod ARIZADIR (sessizce
    yutulmaz — Yasa 4)."""
    olcumler = [g for g in gorevler()
                if ({"4", "F10"} & gorev_etiketleri(g))
                and "is-enabled" in str(g.get("ansible.builtin.command") or g.get("command") or {})]
    assert olcumler, "`is-enabled` ölçüm görevi bulunamadı — çivi bayatlamış"
    for gorev in olcumler:
        ifade = str(gorev.get("failed_when"))
        assert ifade and ifade != "None", (
            f"{gorev.get('name')!r}: `failed_when` YOK — disabled birimin rc 1'i pencereyi "
            "ortasından keser (2026-09-02 vakası)")
        register = str(gorev.get("register"))
        for rc, arizali in ((0, False), (1, False), (4, False), (2, True)):
            dunya = playbook_degiskenleri()
            dunya[register] = {"rc": rc}
            assert when_degerlendir(ifade, dunya) is arizali, (
                f"{gorev.get('name')!r}: rc={rc} için arıza hükmü yanlış "
                f"(beklenen arızalı={arizali}) — `failed_when`: {ifade!r}")


def test_recete_kalemi_readme_de_yasiyor():
    """TSK-092 (b): kural İKİ yerde duruyor — dagit.sh [4] yorumu (icra) ve operatör reçetesi
    (`deploy/README-oracle.md`, insan yolu). Tek-kaynak yasası kopyayı ancak AYRIŞMA ÇİVİSİYLE
    hoş görür: reçete kalemi silinir/kayarsa operatör pencerenin sözleşmesini betikten okumak
    zorunda kalır ve TSK-092 vakası (elle durdurulan birim dağıtımla geri açıldı) sessizce
    tekrarlanır. Ölçülen: iki türetim adının ve "başlatma" hükmünün reçetede geçmesi."""
    recete = (DAGIT.parent / "deploy" / "README-oracle.md").read_text(encoding="utf-8")
    for parca in ("is-enabled", "is-active", "BAŞLATMA", "TSK-092"):
        assert parca in recete, f"reçete kaleminde `{parca}` yok — kural betikte kaldı"
