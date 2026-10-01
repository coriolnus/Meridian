"""v602 — TELEGRAM DİNLEYİCİSİNİN HİZMET HÂLİ (konuşan filo Parça 1b G4 Görev 3, 2026-09-30).

`meridian.telegram_dinleyici` G1'de bir çekirdekti (v592: yetki, yönlendirme, yanıt, yoklama); bu dosya onu bir
HİZMETE çeviren beş parçayı çiviler:

  * BİRİM — `deploy/oracle-a1/meridian-telegram.service`: `Type=simple`, `User=ubuntu`, `WorkingDirectory=/opt/meridian`,
    ExecStart modülün KENDİ adından türer (`python -m <td.__name__>`), `Restart=on-failure`, filo ortak sertleştirme seti
    (v174 `SERTLESTIRILEN`), `ReadWritePaths` TAM OLARAK `/opt/meridian`, `After=` bot ağ geçidini (`ops/sohbet_profili_uret.py
    ::BOT_BIRIMI`) SIRALAR ama ona bağımlılık KURMAZ, `[Install]` VAR ama `etkin_birimler`de YOK. CREDENTIAL — G3b Task 2
    (2026-10-01) ile GELDİ (G4'ün beyanlı ertelemesi KAPANDI): `API_SERVER_KEY` (bota_sor → `HermesTasiyici`, 55 drop-in) ve
    Hindsight kiracı anahtarı (dönüş kaydı, 54 drop-in) rotasyon tablosuyla AYNI dilimde; `test_credential_G3b_drop_in_ciftleri`
    TAM listeyi çiviler. Birim bir
    rapor profili DEĞİLDİR: `ops/filo.py` onu bot saymaz (v348 — `HERMES_HOME` taşımaz).
  * `main()` — `python -m meridian.telegram_dinleyici` → `dongu(bota_sor=bot_kanal.bota_sor)`; sır yoksa `dongu`nun
    `SystemExit`i aynen; bilinmeyen argüman argparse çıkışı (2).
  * 4096 BÖLME (plan Review Focus 3) — Telegram `sendMessage` metin tavanı. Sayım UTF-16 KOD BİRİMİYLE (BMP dışı karakter
    iki sayılır — Telegram'ın karakter mi UTF-16 birimi mi saydığı ÖLÇÜLMEDİ, güvenli taraf); satır sınırında, tek satır
    tavanı aşarsa karakter sınırında (Python `str` birimi — bir kod noktası asla ikiye bölünmez). Tur 2 (Rol-1, K2): imza
    HER parçanın ilk satırı, çok parçalıda sonunda ` (i/n)` — `_SOHBET_IMZA` eki tanır, oturumu eksiz yakalar; hangi parçaya
    yanıt verilirse aynı bot + aynı oturum. Tavan imza satırını ve eki SAYAR. `reply_to` YALNIZ ilk parçada; tek parça
    bugünkü biçimde (eksiz). Bölme `notify.scrub`'DAN SONRA: sınırı ortadan kesen bir anahtar iki yarım hâlinde desenden kaçmaz ve
    scrub'ın UZATTIĞI metin (`://u:p@` → `://***:***@`) tavanı sonradan aşmaz. Teslim edilemeyen parça
    `telegram_parca_teslim_hatasi` (parça no/toplam) ve kalan parçalar YİNE denenir.
  * ARA BİLDİRİM (Review Focus 4) — `bota_sor` `ARA_BILDIRIM_ESIGI_S` (8 sn) içinde dönmezse enjekte `bildir` ile BİR kez
    ara bildirim (1. satır sohbet imzası EKSİZ, 2. satır "⏳ düşünüyor…" — Tur 2: ona yanıt da aynı bota/oturuma gider;
    operatörün mesajına yanıt). Zamanlayıcı cevaptan ÖNCE kapanır (kilit + bayrak + iptal):
    cevap gittikten sonra ara bildirim ASLA gitmez. Zamanlayıcı enjekte edilir — bu dosyada gerçek `sleep` YOK. ÜÇ gerçek
    iplik çivisi var: varsayılan `threading.Timer` yolu (eşik 0, `Event` bekler) ve iki yarış çivisi (uçuştaki
    ara bildirim ↔ `kapat()`, uçuştayken ikinci ateşleme); üçü de sınırlı `Event.wait`/`join` ile bekler, yoklama döngüsü
    değil.
  * İLK KOŞUM OFSETİ — `telegram_ofset.json` YOKSA ilk (bloklamayan, `timeout: 0`) yoklamada BİRİKMİŞ güncellemeler
    İŞLENMEZ: en yüksek `update_id + 1` yazılır, `telegram_ilk_ofset` olayı atlanan sayısıyla. Sayfa dolu gelirse
    (`GUNCELLEME_SAYFASI`) birikim sürüyor olabilir — atlama bir tur daha sürer. Dosya varsa bugünkü davranış.

CANLIYA DOKUNMAZ: birim çivileri yalnız depo dosyalarını okur; davranış çivileri `sandbox_state` altında sahte yoklama/
gönderici/zamanlayıcıyla koşar. Numara v602 (ana checkout + worktree'de boş, 2026-09-30; plan G4 Global Constraints).
"""
from __future__ import annotations

import ast
import glob
import pathlib
import threading

import pytest

from meridian import bot_kanal, notify, obs, store, telegram_dinleyici as td
from tests.conftest import betikten_modul_yukle
from tests.test_ansible_a0_v451 import UZUN_OMURLU_BIRIMLER, _yol_coz
from tests.test_bot_agi_gecidi_v601 import _baglam, _bolum, _credential_yonergeleri, _defaults, _ortam, _tek
from tests.test_h3_tur2_v174 import SERTLESTIRILEN
from tests.test_sertlesmis_birim_yazim_yolu_v553 import _kapsar

KOK = pathlib.Path(__file__).resolve().parent.parent
BIRIM_DIZINI = KOK / "deploy" / "oracle-a1"
BIRIM_ADI = "meridian-telegram.service"
YETKILI = "4242"


def _birim() -> pathlib.Path:
    return BIRIM_DIZINI / BIRIM_ADI


def _ur():
    return betikten_modul_yukle(KOK / "ops/sohbet_profili_uret.py", "sohbet_profili_uret_v602")


# =================================================================================================
# BİRİM — yönergeler
# =================================================================================================

def test_birim_dosyasi_depoda_ve_execstart_modulun_kendi_adindan():
    # ExecStart modül yolunu ELLE taşır; modül yeniden adlandırılırsa birim var olmayan bir modülü koşar,
    # `Restart=on-failure` onu 10 sn arayla yeniden dener ve 300 sn'de beş başarısız başlatmada başlatma sınırı birimi
    # `failed`e düşürür — dinleyici hiç çalışmaz, `reset-failed` olmadan geri de gelmez. Ad `td.__name__`den türetilerek
    # kıyaslanır.
    assert _birim().is_file(), f"deploy/oracle-a1/{BIRIM_ADI} yok"
    assert _tek(_birim(), "Service", "ExecStart") == f"/opt/meridian/.venv/bin/python -m {td.__name__}"


@pytest.mark.parametrize("anahtar, beklenen", [
    ("Type", "simple"),
    ("User", "ubuntu"),
    # Kardeş Python birimlerinin normu; dinleyici bağlam dosyası OKUMAZ (ağ geçidinin `/` gerekçesi burada yok).
    ("WorkingDirectory", "/opt/meridian"),
    # `always` DEĞİL: operatörün `systemctl stop`u arıza değildir; çökme (sıfırdışı çıkış, sinyal) geri getirir.
    ("Restart", "on-failure"),
    ("RestartSec", "10"),
], ids=["Type", "User", "WorkingDirectory", "Restart", "RestartSec"])
def test_birim_service_yonergesi(anahtar, beklenen):
    assert _tek(_birim(), "Service", anahtar) == beklenen


def test_readwritepaths_tam_olarak_opt_meridian():
    # Dinleyicinin ve `bota_sor`un yazımları hep `/opt/meridian/state/` altında: ofset, bot_sohbet defteri, unut bekleyen
    # kaydı + kilitleri, olay defteri; import anında `__pycache__`. Ev dizini AÇILMAZ (ExecStart `uv` değil, Hermes kökü yok).
    rwp = _tek(_birim(), "Service", "ReadWritePaths").split()
    assert rwp == ["/opt/meridian"], rwp
    assert _kapsar(rwp, "/opt/meridian/state/telegram_ofset.json")
    assert _kapsar(rwp, "/opt/meridian/state/.locks")


def test_after_bot_ag_gecidini_siralar_ama_bagimlilik_kurmaz():
    # Açılışta ağ geçidi dinleyiciden ÖNCE kalksın (ilk soru bağlantı hatası almasın) — ama ağ geçidinin durması ya da
    # yeniden başlaması dinleyiciyi DÜŞÜRMEMELİ: o anki soru "cevap veremiyor" alır, dinleyici ayakta kalır.
    bot_birimi = _ur().BOT_BIRIMI
    assert (BIRIM_DIZINI / bot_birimi).is_file(), bot_birimi
    unit = _bolum(_birim(), "Unit")
    after = {ad for a, d in unit if a == "After" for ad in d.split()}
    assert {"network-online.target", bot_birimi} <= after, after
    wants = [d for a, d in unit if a == "Wants"]
    assert wants == ["network-online.target"], wants
    bagimlilik = {ad for a, d in unit if a in {"Wants", "Requires", "BindsTo", "Requisite", "PartOf"}
                  for ad in d.split()}
    assert bot_birimi not in bagimlilik, bagimlilik


def test_install_bolumu_var_multi_user():
    assert _tek(_birim(), "Install", "WantedBy") == "multi-user.target"


def _baslatma_siniri(birim: pathlib.Path) -> tuple[int, int, int]:
    """(StartLimitIntervalSec, StartLimitBurst, RestartSec) — ilk ikisi `[Unit]`dan, sonuncusu `[Service]`den."""
    return (int(_tek(birim, "Unit", "StartLimitIntervalSec")), int(_tek(birim, "Unit", "StartLimitBurst")),
            int(_tek(birim, "Service", "RestartSec")))


def test_baslatma_siniri_kalici_yapilandirma_hatasini_failed_e_dusurur():
    # Tur 3, görev incelemesi M-2: sır yoksa / sohbet kimliği pozitif değilse `dongu` `SystemExit` (çıkış 1) ile çıkar.
    # systemd varsayılan sınırı (5 başlatma / 10 sn) `RestartSec=10` ile ASLA dolmaz → birim `failed`e düşmeden günde
    # binlerce kez yeniden başlar (görünmez arıza). 300 sn'de 5 başarısız başlatma → `failed`. Sınırın ETKİLİ olması
    # için `Burst × RestartSec` pencereye sığmalı — biri değişip sınırı sessizce etkisiz kılarsa çivi öter.
    aralik, patlama, yeniden_s = _baslatma_siniri(_birim())
    assert (aralik, patlama) == (300, 5)
    assert patlama * yeniden_s < aralik, (patlama, yeniden_s, aralik)
    # Yönerge `[Unit]`a aittir (systemd'nin `[Service]` yerleşimi yalnız geriye uyumluluktur) — tek yer, tek değer.
    assert not [a for a, _ in _bolum(_birim(), "Service") if a.startswith("StartLimit")]


def test_birim_filo_sertlestirme_ve_uzun_omur_listelerinde():
    # Liste çivileri ELLE listedir: birim kurulduğu turda iki listeye de girer (bekçi dersi, v174 şerhi). Buradaki çivi
    # listeden sessizce düşmeyi yakalar — sertleştirme seti v174'te, "rol asla yeniden başlatmaz" v451'de ölçülür.
    assert BIRIM_ADI in SERTLESTIRILEN
    assert BIRIM_ADI in UZUN_OMURLU_BIRIMLER


# =================================================================================================
# CREDENTIAL — G3b sır dilimine BEYANLI olarak ertelendi (Rol-1 kararı 2026-09-30, G4)
# =================================================================================================

def test_credential_G3b_drop_in_ciftleri():
    # G3b Task 2 (2026-10-01) — G4'teki BEYANLI ERTELEME ÇEVRİLDİ. `bota_sor` üretimde `HermesTasiyici` (anahtar
    # `API_SERVER_KEY`) ve `HindsightHafiza` (kiracı anahtarı) kurar; ikisi de anahtarı YALNIZ credential kanalından okur.
    # İddia TAM LİSTE eşitliğidir: hafıza (54) + API sunucu (55) — iki ayrı dosya, iki ayrı rotasyon alt komutu
    # (`--tenant` · `--api-sunucu`, v447 P6). Kimlikler KODDAN (`secrets.HAFIZA_KRED_ADI` · `HermesTasiyici`nın okuduğu
    # literal), kaynaklar envanterin `vault_kv` `hedef`inden TÜRER. `TELEGRAM_*` sırları bugünkü zincirle okunur.
    import inspect
    import re
    import yaml
    from meridian import secrets
    kv = {g["ad"]: g for g in yaml.safe_load(
        (pathlib.Path(__file__).resolve().parents[1] / "deploy/sir_envanteri.yaml").read_text(encoding="utf-8"))["vault_kv"]}
    api = re.findall(r'credential_oku\("([A-Z_]+)"\)', inspect.getsource(bot_kanal.HermesTasiyici))
    assert len(set(api)) == 1, api
    ad = secrets.HAFIZA_KRED_ADI
    assert _credential_yonergeleri(_birim()) == [
        ("54-hafiza-credential.conf", "LoadCredential", f"{ad}:{kv[ad]['hedef']}"),
        ("55-api-sunucu-credential.conf", "LoadCredential", f"{api[0]}:{kv['api_server_key']['hedef']}")]


def test_credential_denetcisi_bu_birimin_metnine_eklenen_yonergeyi_gorur(tmp_path):
    # POZİTİF KONTROL — kör denetçinin boşluğu yeşil sayılmasın: GERÇEK birim metnine bir satır eklenince denetçi görür.
    kopya = tmp_path / BIRIM_ADI
    kopya.write_text(_birim().read_text(encoding="utf-8").replace(
        "[Service]\n", "[Service]\nLoadCredential=API_SERVER_KEY:/etc/meridian/creds/API_SERVER_KEY\n", 1),
        encoding="utf-8")
    assert _credential_yonergeleri(kopya) == [
        (BIRIM_ADI, "LoadCredential", "API_SERVER_KEY:/etc/meridian/creds/API_SERVER_KEY")]


# =================================================================================================
# A0 ROLÜ — kopya evet, etkinleştirme hayır
# =================================================================================================

def test_birim_rolun_kaynaklarinda_ama_etkin_degil_ve_bakim_penceresinde_yok():
    birimler = {pathlib.Path(p).resolve() for desen in _defaults()["birim_kaynaklari"]
                for p in glob.glob(_yol_coz(desen))}
    assert _birim().resolve() in birimler
    baglam = _baglam()
    assert BIRIM_ADI not in baglam["etkin_birimler"]
    assert not {BIRIM_ADI, BIRIM_ADI.removesuffix(".service")} & set(baglam["birim_adaylari"])


def test_filo_araci_dinleyiciyi_bot_saymaz():
    # v348 sözleşmesi: bot eşlemesi `HERMES_HOME=…/.hermes/profiles/<ad>` satırından ölçülür. Dinleyici bir rapor profili
    # DEĞİL — `HERMES_HOME` taşımaz, eşlemeye girmez, sahte "timer yok" satırı üretmez.
    assert "HERMES_HOME" not in _ortam(_birim())
    filo = betikten_modul_yukle(KOK / "ops/filo.py", "filo_v602")
    assert BIRIM_ADI not in {b["birim"] for b in filo.profiller().values()}
    assert filo.eksik_timerlar() == [], filo.eksik_timerlar()


# =================================================================================================
# main()
# =================================================================================================

def test_main_dongu_yu_uretim_bota_soru_ile_kosar(monkeypatch):
    gorulen = {}
    monkeypatch.setattr(td, "dongu", lambda **kw: gorulen.update(kw))
    assert td.main([]) == 0
    assert gorulen.get("bota_sor") is bot_kanal.bota_sor, gorulen


def test_main_sir_yoksa_dongunun_systemexiti_aynen(sandbox_state, monkeypatch):
    monkeypatch.setattr(td.secrets, "get", lambda ad: None)
    with pytest.raises(SystemExit) as exc:
        td.main([])
    assert "TELEGRAM_BOT_TOKEN" in str(exc.value.code)


def test_main_bilinmeyen_argumani_reddeder(capsys):
    with pytest.raises(SystemExit) as exc:
        td.main(["--bilinmeyen"])
    assert exc.value.code == 2


def test_pano_sohbet_kimligi_yonergesi_dinleyiciyle_celismez():
    # TEK KAYNAK: kural `dongu`dadır (`_POZITIF_TAMSAYI` — grup/kanal kimliğiyle başlamaz); eski panonun (`/eski`,
    # `meridian/web/app.js`) sır alanı yönergesi onun KOPYASIDIR → ayrışma çivisi. Eski metin "negatif olabilir … eksi
    # işareti DAHİL" diyordu: operatör onu izleseydi dinleyici hiç başlamazdı. getUpdates tek okuyucuya izin verir —
    # dinleyici çalışırken tarayıcıdan çağrı 409 üretir, yönerge bunu söylemeli.
    js = (KOK / "meridian/web/app.js").read_text(encoding="utf-8")
    bas = js.index('["TELEGRAM_CHAT_ID", "Telegram chat ID",')
    alan = js[bas:js.index('["MERIDIAN_WEBHOOK_URL"', bas)]
    assert "POZİTİF" in alan and "409" in alan and "getUpdates ÇAĞIRMA" in alan
    assert "negatif olabilir" not in alan and "eksi işareti DAHİL" not in alan
    assert td._POZITIF_TAMSAYI.fullmatch("123456789") and not td._POZITIF_TAMSAYI.fullmatch("-1001234567890")


def test_modul_python_m_ile_main_i_kosar():
    # `python -m meridian.telegram_dinleyici` ancak modül sonundaki `if __name__ == "__main__":` koruması `main()`i
    # çağırırsa hizmettir; koruma yoksa birim başlar, hiçbir şey yapmadan 0 ile çıkar ve `Restart=on-failure` onu geri
    # getirmez — sessiz ölü birim.
    agac = ast.parse(pathlib.Path(td.__file__).read_text(encoding="utf-8"))
    korumalar = [n for n in agac.body if isinstance(n, ast.If) and ast.unparse(n.test) == "__name__ == '__main__'"]
    assert korumalar, "__main__ koruması yok"
    assert ast.unparse(korumalar[-1].body[0]) == "raise SystemExit(main())"


# =================================================================================================
# 4096 BÖLME
# =================================================================================================

def _u16(s: str) -> int:
    return len(s.encode("utf-16-le")) // 2


def test_parcala_sinira_dek_tek_parca_asinca_iki():
    assert td.TELEGRAM_TAVANI == 4096
    assert td.parcala("a" * 4096, ilk_butce=4096) == ["a" * 4096]
    assert td.parcala("a" * 4097, ilk_butce=4096) == ["a" * 4096, "a"]


def test_parcala_satir_sinirinda_boler():
    satirlar = [f"{i:03d} " + "x" * 95 for i in range(60)]          # 99 karakterlik 60 satır
    metin = "\n".join(satirlar)
    parcalar = td.parcala(metin, ilk_butce=4096)
    assert len(parcalar) == 2 and all(_u16(p) <= 4096 for p in parcalar)
    # Her parça TAM satırlardan oluşur: hiçbir satır iki parçaya bölünmez.
    assert all(set(p.split("\n")) <= set(satirlar) for p in parcalar)
    assert "\n".join(parcalar) == metin


def test_parcala_tek_satir_tavani_asarsa_karakter_sinirinda():
    assert [len(p) for p in td.parcala("x" * 10000, ilk_butce=4096)] == [4096, 4096, 1808]
    # İlk parçanın bütçesi imza kadar kısalır; sonrakiler tam tavan.
    assert [len(p) for p in td.parcala("x" * 5000, ilk_butce=4000)] == [4000, 1000]


def test_parcala_bmp_disi_karakteri_iki_sayar_ve_bolmez():
    # Emoji UTF-16'da iki kod birimidir: 2048 emoji = 4096 birim. Python `str` dilimi bir kod noktasını bölemez; sayım
    # yine de birimle yapılır (Telegram'ın birimi ölçülmedi — güvenli taraf).
    emoji = "😀"
    parcalar = td.parcala(emoji * 3000, ilk_butce=4096)
    assert [len(p) for p in parcalar] == [2048, 952]
    assert "".join(parcalar) == emoji * 3000
    # Tek birimlik bir karakter sınırı tek birim açık bırakır: sonraki emoji (2 birim) SIĞMAZ, taşar.
    assert [_u16(p) for p in td.parcala("a" + emoji * 2048, ilk_butce=4096)] == [4095, 2]
    # BMP içi çok baytlı harf (UTF-8'de 2 bayt) BİR birimdir — bayt saymak metni gereksiz bölerdi.
    assert td.parcala("ş" * 4096, ilk_butce=4096) == ["ş" * 4096]


def test_parcala_bos_parca_uretmez():
    # Telegram boş metni reddeder: tavana tam oturan satırdan sonraki boş satır ayrı (boş) bir mesaj olmamalı.
    assert td.parcala("a" * 4096 + "\n", ilk_butce=4096) == ["a" * 4096]
    assert td.parcala("", ilk_butce=4096) == [""]


def _m(metin, mid=7):
    return {"message_id": mid, "chat": {"id": int(YETKILI), "type": "private"}, "from": {"id": int(YETKILI)},
            "text": metin}


def _isle(cevap, gonder=None, **kw):
    gidenler = []

    def varsayilan(t, r):
        gidenler.append((t, r))
        return True

    neden = td.isle({"update_id": 1, "message": _m("@bekci durum?")}, yetkili_sohbet=YETKILI,
                    bota_sor=lambda *a: cevap, gonder=gonder or varsayilan, bugun="20260929", **kw)
    return neden, gidenler


IMZA = "💬 @bekci · tg-bekci-20260929"


UZUN_CEVAP = "\n".join(f"satır {i:04d} " + "y" * 90 for i in range(120))      # ~12k karakter → 3+ parça


def test_isle_uzun_cevap_her_parca_imzali_ve_sirali_reply_to_yalniz_ilk_parcada(sandbox_state):
    # Tur 2 (Rol-1 kararı, K2): imza HER parçanın ilk satırı — operatör hangi parçaya yanıt verirse versin yönlendirme
    # aynı bota ve aynı oturuma gider. Çok parçalıda imza satırının sonunda ` (i/n)`; `reply_to` YALNIZ ilk parçada.
    _, gidenler = _isle(UZUN_CEVAP)
    n = len(gidenler)
    assert n >= 3
    assert [t.split("\n", 1)[0] for t, _ in gidenler] == [f"{IMZA} ({i}/{n})" for i in range(1, n + 1)]
    assert [r for _, r in gidenler] == [7] + [None] * (n - 1)
    assert all(_u16(t) <= td.TELEGRAM_TAVANI for t, _ in gidenler)
    assert "\n".join(t.split("\n", 1)[1] for t, _ in gidenler) == UZUN_CEVAP


def test_ikinci_parcaya_yanit_ayni_bota_ve_ayni_oturuma_gider(sandbox_state):
    # Yanıt GÜNÜ farklı (20261001): oturum yanıtlanan parçanın imzasından SÜRER, bugünden türetilmez.
    _, gidenler = _isle(UZUN_CEVAP)
    yanit = {"message_id": 50, "chat": {"id": int(YETKILI), "type": "private"}, "from": {"id": int(YETKILI)},
             "text": "bu kısmı aç", "reply_to_message": {"message_id": 41, "text": gidenler[1][0]}}
    y = td.yonlendir(yanit, YETKILI)
    assert (y.bot, y.neden) == ("bekci", "sohbet_imza")
    assert td.oturum_kimligi("bekci", yanit, "20261001") == "tg-bekci-20260929"
    cagrilar = []
    td.isle({"update_id": 2, "message": yanit}, yetkili_sohbet=YETKILI,
            bota_sor=lambda bot, m, k, o: cagrilar.append((bot, o)) or "tamam", gonder=lambda t, r: True,
            bugun="20261001")
    assert cagrilar == [("bekci", "tg-bekci-20260929")]


def test_ikinci_parcaya_govdesiz_unut_yaniti_imza_satirini_atlar(sandbox_state):
    # `(i/n)` ekli imza da İÇERİK değildir: gövdesiz `unut:` sorgusu parçanın ilk içerik satırı olur, imza satırı değil.
    _, gidenler = _isle(UZUN_CEVAP)
    ikinci_icerik = gidenler[1][0].split("\n")[1]
    yanit = {"message_id": 51, "chat": {"id": int(YETKILI), "type": "private"}, "from": {"id": int(YETKILI)},
             "text": "unut:", "reply_to_message": {"message_id": 41, "text": gidenler[1][0]}}
    cagrilar = []
    td.isle({"update_id": 3, "message": yanit}, yetkili_sohbet=YETKILI,
            bota_sor=lambda bot, m, k, o: cagrilar.append((bot, m)) or "tamam", gonder=lambda t, r: True,
            bugun="20260929")
    # Sorgu `bot_kanal.alinti_icerik_satiri` tavanıyla kesilir (tek kaynak; v592 gövdesiz `unut:` çivileri).
    assert cagrilar == [("bekci", f"unut: {ikinci_icerik[:bot_kanal.KAYNAK_ETIKETI_TAVANI]}")]
    assert not ikinci_icerik.startswith("💬")


@pytest.mark.parametrize("satir, bot, oturum", [
    ("💬 @bekci", "bekci", None),                                       # bugünkü eski biçimler AYNEN tanınır
    ("💬 @bekci · tg-bekci-20260929", "bekci", "tg-bekci-20260929"),
    ("💬 @karne · tg-karne-r55", "karne", "tg-karne-r55"),
    ("💬 @bekci · tg-bekci-20260929 (2/3)", "bekci", "tg-bekci-20260929"),   # parça eki: oturum grubu EKSİZ
    ("💬 @karne · tg-karne-r55 (12/13)", "karne", "tg-karne-r55"),
])
def test_sohbet_imza_deseni_parca_ekini_tanir_oturum_eksiz(satir, bot, oturum):
    s = td._SOHBET_IMZA.match(satir)
    assert s and (s.group(1), s.group(2)) == (bot, oturum)


def test_sohbet_imza_deseni_bozuk_eki_tanimaz():
    for satir in ("💬 @bekci · tg-bekci-20260929 (2/)", "💬 @bekci · tg-bekci-20260929 (2/3) fazla",
                  "💬 @bekci · tg-bekci-20260929(2/3)"):
        assert td._SOHBET_IMZA.match(satir) is None, satir


def test_imzali_parca_tavani_asmaz_ek_dahil(sandbox_state):
    # Tavan imza satırını VE ` (i/n)` ekini sayar. Tek satırlık dev cevap parçaları tavana kadar DOLDURUR (sınır testi);
    # 13 parçada ek iki haneye çıkar — ek uzunluğu parça sayısıyla büyür. 36560: eksiz bütçeyle 9 parça, tek haneli ek
    # ayrılınca 10'a çıkar → ek İKİ haneye büyür; bölme hane sayısı sabitlenene dek yinelenmezse tavan 1 birim aşılırdı.
    # Beklenen EN UZUN mesaj: dolu parçalar bütçeyi tam doldurur; 36560'ta dolu parçaların eki tek hanelidir (`(i/10)`,
    # i<10) ama bütçe iki haneli ek için ayrıldı → 4095. Diğer ikisinde tavana TAM oturur (sınır gerçekten sınandı).
    for uzunluk, beklenen_n, en_uzun in ((10000, 3, 4096), (36560, 10, 4095), (50000, 13, 4096)):
        _, gidenler = _isle("x" * uzunluk)
        n = len(gidenler)
        assert n == beklenen_n, n
        assert all(_u16(t) <= td.TELEGRAM_TAVANI for t, _ in gidenler), max(_u16(t) for t, _ in gidenler)
        assert max(_u16(t) for t, _ in gidenler) == en_uzun
        assert "".join(t.split("\n", 1)[1] for t, _ in gidenler) == "x" * uzunluk


def test_isle_kisa_cevap_bugunku_tek_mesaj(sandbox_state):
    _, gidenler = _isle("tamam")
    assert gidenler == [(IMZA + "\ntamam", 7)]


def test_isle_bolme_scrubdan_sonra_sinirdaki_anahtar_yarim_kalmaz(sandbox_state):
    # Bölme ÖNCE yapılsaydı sınırı ortadan kesen anahtar iki yarım hâlinde gönderilirdi ve `yanitla`nın parça başına
    # scrub'ı yarımları desene uyduramazdı. Sahte gönderici scrub ETMEZ — maskeyi yalnız dinleyicinin kendisi koyabilir.
    anahtar = "sk-or-v1-" + "d" * 64
    ilk_butce = td.TELEGRAM_TAVANI - _u16(IMZA) - 1
    cevap = "z" * (ilk_butce - 20) + anahtar + " son"
    _, gidenler = _isle(cevap)
    birlesik = "".join(t for t, _ in gidenler)
    assert "sk-or-v1-" not in birlesik and "d" * 20 not in birlesik and "***" in birlesik


def test_isle_scrubin_uzattigi_metin_tavani_asmaz(sandbox_state):
    # `url_kimlik` maskesi metni UZATIR (`://u:p@` 7 → `://***:***@` 11). Ham cevap tek parçaya sığıyor; scrub'lı hâli
    # sığmıyor. Tavan scrub'lı metne göre ölçülmeli — ve `yanitla` parçayı yeniden scrub'ladığında BÜYÜMEMELİ.
    cevap = "://u:p@\n" * 480
    assert _u16(IMZA) + 1 + _u16(cevap) <= td.TELEGRAM_TAVANI < _u16(notify.scrub(cevap))
    _, gidenler = _isle(cevap)
    assert len(gidenler) == 2
    assert all(_u16(notify.scrub(t)) <= td.TELEGRAM_TAVANI for t, _ in gidenler)


def test_isle_parca_teslim_edilemezse_olay_ve_kalan_parcalar_denenir(sandbox_state):
    cagrilar = []

    def gonder(t, r):
        cagrilar.append(r)
        if len(cagrilar) == 1:
            raise OSError("ağ yok")
        return len(cagrilar) != 2

    cevap = "\n".join("q" * 3000 for _ in range(3))
    _isle(cevap, gonder=gonder)
    assert len(cagrilar) == 3
    olaylar = [e for e in obs.recent(50) if e.get("event") == "telegram_parca_teslim_hatasi"]
    assert [(e.get("parca"), e.get("toplam"), e.get("sinif")) for e in olaylar] == [
        (1, 3, "OSError"), (2, 3, "teslim_edilemedi")]
    assert all(e.get("bot") == "bekci" and "q" * 10 not in str(e) for e in olaylar)


# =================================================================================================
# ARA BİLDİRİM — sahte zamanlayıcı (gerçek bekleme YOK)
# =================================================================================================

class _SahteZamanlayici:
    """`threading.Timer` ikizi: süre/işlev kaydedilir; `ates()` gerçek Timer'ın bekleme sonu davranışıdır (iptal
    edilmediyse işlevi koşar). `fn`i DOĞRUDAN çağırmak yarışı taklit eder: iplik beklemeyi bitirmiş, iptal ona yetişmemiş."""

    def __init__(self, kayit, sure, fn):
        self.sure, self.fn, self.basladi, self.iptal, self.daemon = sure, fn, False, False, None
        kayit.append(self)

    def start(self):
        self.basladi = True

    def cancel(self):
        self.iptal = True

    def ates(self):
        if not self.iptal:
            self.fn()


def _ara_isle(bota_sor, bildir_sonuc=True):
    olay, zamanlayicilar = [], []

    def bildir(t, r):
        olay.append(("bildir", t, r))
        if isinstance(bildir_sonuc, BaseException):
            raise bildir_sonuc
        return bildir_sonuc

    def gonder(t, r):
        olay.append(("gonder", t, r))
        return True

    td.isle({"update_id": 1, "message": _m("@bekci durum?")}, yetkili_sohbet=YETKILI,
            bota_sor=lambda *a: bota_sor(zamanlayicilar), gonder=gonder, bildir=bildir, bugun="20260929",
            _zamanlayici=lambda sure, fn: _SahteZamanlayici(zamanlayicilar, sure, fn))
    return olay, zamanlayicilar


# Tur 2 (Rol-1, K2): ara bildirim imza satırıyla başlar (EKSİZ) — ona verilen yanıt da aynı bota ve oturuma gider.
ARA = IMZA + "\n⏳ düşünüyor…"


def test_ara_bildirim_esik_altinda_gitmez_ve_zamanlayici_iptal_edilir(sandbox_state):
    olay, zs = _ara_isle(lambda zs: "hızlı cevap")
    assert len(zs) == 1
    z = zs[0]
    assert (z.sure, z.basladi, z.daemon) == (td.ARA_BILDIRIM_ESIGI_S, True, True) and td.ARA_BILDIRIM_ESIGI_S == 8
    assert z.iptal is True, "cevap geldi ama zamanlayıcı iptal edilmedi — iplik eşiğe dek boşuna yaşar"
    z.ates()
    assert [o[0] for o in olay] == ["gonder"]


def test_ara_bildirim_esik_ustunde_bir_kez_ve_cevaptan_once_gider(sandbox_state):
    def yavas(zs):
        zs[0].ates()
        zs[0].fn()          # ikinci ateşleme (iplik yeniden tetiklense bile) ikinci bildirim DEĞİLDİR
        return "geç cevap"

    olay, _ = _ara_isle(yavas)
    assert olay == [("bildir", ARA, 7), ("gonder", IMZA + "\ngeç cevap", 7)]


def test_ara_bildirime_yanit_ayni_bota_ve_ayni_oturuma_gider(sandbox_state):
    def yavas(zs):
        zs[0].ates()
        return "geç cevap"

    olay, _ = _ara_isle(yavas)
    ara_metni = olay[0][1]
    assert olay[0][0] == "bildir" and ara_metni == ARA
    yanit = {"message_id": 60, "chat": {"id": int(YETKILI), "type": "private"}, "from": {"id": int(YETKILI)},
             "text": "acele etme", "reply_to_message": {"message_id": 8, "text": ara_metni}}
    y = td.yonlendir(yanit, YETKILI)
    assert (y.bot, y.neden) == ("bekci", "sohbet_imza")
    assert td.oturum_kimligi("bekci", yanit, "20261001") == "tg-bekci-20260929"


def test_ara_bildirim_cevap_gittikten_sonra_asla_gitmez_yaris(sandbox_state):
    # YARIŞ: zamanlayıcı ipliği beklemeyi bitirmiş, iptal ona yetişmemiş — işlev cevaptan SONRA koşar. Kilit altındaki
    # "kapandı" bayrağı onu susturur.
    olay, zs = _ara_isle(lambda zs: "cevap")
    zs[0].fn()
    assert [o[0] for o in olay] == ["gonder"]


def _ucusta_tutan_bildir(kayit):
    """Uçuşta TUTULAN sahte gönderim: girince `icerde` kurulur, `serbest` gelene dek döner DEĞİL (sınırlı bekleme)."""
    icerde, serbest = threading.Event(), threading.Event()

    def bildir(t, r):
        icerde.set()
        assert serbest.wait(10), "test düzeneği: uçuştaki ara bildirim hiç serbest bırakılmadı"
        kayit.append("ara")
        return True
    return bildir, icerde, serbest


def test_ara_bildirim_ucustayken_kapat_bekler_cevap_ondan_sonra_gider(sandbox_state):
    # Tur 3, görev incelemesi I-1 — GERÇEK İKİ İPLİK. Zamanlayıcı ipliği "kapandı mı?" denetimini GEÇMİŞ ve gönderim
    # UÇUŞTA (HTTP'de) iken cevap yolu `kapat()`a girer. `kapat()`taki kilit gönderimi BEKLER: sıra kaydı ara → cevap.
    # Kilit olmasaydı `kapat()` hemen döner, cevap yola çıkar ve uçuştaki ara bildirim CEVAPTAN SONRA iner (Review Focus
    # 4'ün yasakladığı sıra). `time.sleep` YOK: tek zaman bağımlı adım `Event.wait(0.3)` — kilit varken sonucu DEĞİŞTİRMEZ
    # (kapat zaten bekler), yalnız kilitsiz mutasyonun cevap ipliğine koşma fırsatı verir.
    kayit, zs = [], []
    bildir, icerde, serbest = _ucusta_tutan_bildir(kayit)
    ab = td._AraBildirim(bildir, "bekci", ARA, 7, td.ARA_BILDIRIM_ESIGI_S,
                         lambda sure, fn: _SahteZamanlayici(zs, sure, fn))
    zamanlayici_ipligi = threading.Thread(target=zs[0].fn, daemon=True)     # eşik doldu: iplik işlevi koşar
    zamanlayici_ipligi.start()
    assert icerde.wait(10), "ara bildirim uçuşa hiç girmedi"
    cevap_gitti = threading.Event()

    def cevap_yolu():                                   # `isle`in sırası: kapat() → cevabı gönder
        ab.kapat()
        kayit.append("cevap")
        cevap_gitti.set()

    cevap_ipligi = threading.Thread(target=cevap_yolu, daemon=True)
    cevap_ipligi.start()
    erken = cevap_gitti.wait(0.3)
    serbest.set()
    zamanlayici_ipligi.join(10)
    cevap_ipligi.join(10)
    assert not erken, "kapat() uçuştaki ara bildirimi BEKLEMEDEN döndü — cevap ara bildirimden önce yola çıktı"
    assert kayit == ["ara", "cevap"], f"sıra kaydı {kayit}: ara bildirim cevaptan SONRA indi"


def test_ara_bildirim_ucustayken_ikinci_atesleme_ikinci_bildirim_degildir(sandbox_state):
    # İKİNCİ İPLİK aynı işlevi koşarsa (yeniden tetiklenen zamanlayıcı) kilidi bekler; uçuştaki gönderim bittikten sonra
    # "gitti" bayrağını görüp SUSAR. Sonuç zamanlamadan bağımsızdır: bayrak gönderimden ÖNCE kurulur, ikinci iplik kilide
    # ne zaman varırsa varsın. Bayrak denetimi olmasaydı ara bildirim İKİ kez giderdi.
    kayit, zs = [], []
    bildir, icerde, serbest = _ucusta_tutan_bildir(kayit)
    ab = td._AraBildirim(bildir, "bekci", ARA, 7, td.ARA_BILDIRIM_ESIGI_S,
                         lambda sure, fn: _SahteZamanlayici(zs, sure, fn))
    birinci = threading.Thread(target=zs[0].fn, daemon=True)
    birinci.start()
    assert icerde.wait(10), "ara bildirim uçuşa hiç girmedi"
    ikinci = threading.Thread(target=zs[0].fn, daemon=True)
    ikinci.start()
    serbest.set()
    birinci.join(10)
    ikinci.join(10)
    assert not (birinci.is_alive() or ikinci.is_alive()), "iplik 10 sn içinde bitmedi (kilitlenme?)"
    ab.kapat()
    assert kayit == ["ara"], f"ara bildirim {kayit.count('ara')} kez gitti — BİR kez olmalıydı"


def test_ara_bildirim_bota_sor_hatasinda_da_kapanir(sandbox_state):
    def hata(zs):
        raise TimeoutError("zaman aşımı")

    olay, zs = _ara_isle(hata)
    zs[0].fn()
    assert zs[0].iptal is True
    assert [o[0] for o in olay] == ["gonder"] and "cevap veremiyor" in olay[0][1]


def test_ara_bildirim_hatasi_sessiz_degil_ve_cevabi_dusurmez(sandbox_state):
    def yavas(zs):
        zs[0].ates()
        return "cevap"

    olay, _ = _ara_isle(yavas, bildir_sonuc=OSError("ağ yok"))
    assert [o[0] for o in olay] == ["bildir", "gonder"]
    olay2, _ = _ara_isle(yavas, bildir_sonuc=False)
    assert [o[0] for o in olay2] == ["bildir", "gonder"]
    siniflar = [e.get("sinif") for e in obs.recent(50) if e.get("event") == "telegram_ara_bildirim_hatasi"]
    assert siniflar == ["OSError", "teslim_edilemedi"], siniflar


def test_bildir_verilmezse_zamanlayici_kurulmaz(sandbox_state):
    kurulan = []
    td.isle({"update_id": 1, "message": _m("@bekci durum?")}, yetkili_sohbet=YETKILI, bota_sor=lambda *a: "x",
            gonder=lambda t, r: True, bugun="20260929", _zamanlayici=lambda *a: kurulan.append(a))
    assert kurulan == []


def test_ara_bildirim_kurulamazsa_soru_yine_sorulur(sandbox_state):
    # Bekleme işareti cevabın önünü KESMEZ: iplik açılamazsa (kaynak tükenmesi) olay yazılır, soru ara bildirimsiz sorulur.
    def kurulamaz(sure, fn):
        raise RuntimeError("can't start new thread")

    gidenler = []
    td.isle({"update_id": 1, "message": _m("@bekci durum?")}, yetkili_sohbet=YETKILI, bota_sor=lambda *a: "cevap",
            gonder=lambda t, r: gidenler.append((t, r)) or True, bildir=lambda t, r: True, bugun="20260929",
            _zamanlayici=kurulamaz)
    assert gidenler == [(IMZA + "\ncevap", 7)]
    olay = [e for e in obs.recent(20) if e.get("event") == "telegram_ara_bildirim_hatasi"]
    assert olay and (olay[-1].get("sinif"), olay[-1].get("kurulamadi")) == ("RuntimeError", True)


def test_ara_bildirim_gercek_zamanlayiciyla_eslesir(sandbox_state, monkeypatch):
    # GERÇEK ZAMANLAYICI ÇİVİSİ (üç gerçek iplik çivisinden biri — ötekiler yukarıdaki iki yarış çivisi): varsayılan
    # `threading.Timer` imzası ve iplik yolu, enjekte zamanlayıcısız TEK çivi. Eşik 0 — bekleme yok; `bota_sor`
    # ara bildirimin GELDİĞİNİ `Event` ile bekler (sınırlı, yoklama döngüsü değil).
    monkeypatch.setattr(td, "ARA_BILDIRIM_ESIGI_S", 0)
    geldi, olay = threading.Event(), []

    def bildir(t, r):
        olay.append(("bildir", t, r))
        geldi.set()
        return True

    def bota_sor(*a):
        assert geldi.wait(10), "ara bildirim gerçek zamanlayıcıyla gelmedi"
        return "cevap"

    td.isle({"update_id": 1, "message": _m("@bekci durum?")}, yetkili_sohbet=YETKILI, bota_sor=bota_sor,
            gonder=lambda t, r: olay.append(("gonder", t, r)) or True, bildir=bildir, bugun="20260929")
    assert olay == [("bildir", ARA, 7), ("gonder", IMZA + "\ncevap", 7)]


# =================================================================================================
# İLK KOŞUM OFSETİ + dongu varsayılanları
# =================================================================================================

def _sirlar(monkeypatch):
    monkeypatch.setattr(td.secrets, "get", lambda ad: {"TELEGRAM_BOT_TOKEN": "J" * 20,
                                                        "TELEGRAM_CHAT_ID": YETKILI}.get(ad))


def _yoklama(sonuclar, govdeler):
    it = iter(sonuclar)

    def cagir(url, govde, zaman_asimi):
        govdeler.append(dict(govde))
        s = next(it)
        if isinstance(s, BaseException):
            raise s
        return {"ok": True, "result": s}
    return cagir


def _g(uid, metin="@bekci durum?"):
    return {"update_id": uid, "message": _m(metin, mid=uid)}


def test_ilk_kosumda_birikmis_guncellemeler_islenmez(sandbox_state, monkeypatch):
    _sirlar(monkeypatch)
    cagrilar, govdeler = [], []
    td.dongu(bota_sor=lambda bot, m, k, o: cagrilar.append(m) or "ok", tur_sayisi=2,
             _cagir=_yoklama([[_g(10, "eski soru"), _g(11, "@karne eski")], [_g(12, "yeni soru")]], govdeler),
             gonder=lambda t, r: True, _uyku=lambda s: None)
    assert cagrilar == ["yeni soru"]
    # İlk yoklama BLOKLAMAZ: yalnız ZATEN birikmiş olanı alır — uzun yoklama operatörün ilk TAZE mesajını da "birikmiş"
    # sayıp yutardı.
    assert [(g["offset"], g["timeout"]) for g in govdeler] == [(0, 0), (12, 50)]
    assert store.read_json(td.OFSET_DOSYASI, {}).get("ofset") == 13
    olay = [e for e in obs.recent(50) if e.get("event") == "telegram_ilk_ofset"]
    assert len(olay) == 1 and (olay[0].get("atlanan"), olay[0].get("ofset")) == (2, 12)


def test_ofset_dosyasi_varsa_ilk_yoklama_islenir(sandbox_state, monkeypatch):
    _sirlar(monkeypatch)
    store.write_json(td.OFSET_DOSYASI, {"ofset": 10})
    cagrilar, govdeler = [], []
    td.dongu(bota_sor=lambda bot, m, k, o: cagrilar.append(m) or "ok", tur_sayisi=1,
             _cagir=_yoklama([[_g(10, "soru")]], govdeler), gonder=lambda t, r: True, _uyku=lambda s: None)
    assert cagrilar == ["soru"] and [(g["offset"], g["timeout"]) for g in govdeler] == [(10, 50)]
    assert not [e for e in obs.recent(50) if e.get("event") == "telegram_ilk_ofset"]


def test_ilk_yoklama_bossa_ofset_yazilir_ve_sonraki_mesaj_islenir(sandbox_state, monkeypatch):
    _sirlar(monkeypatch)
    cagrilar, govdeler = [], []
    td.dongu(bota_sor=lambda bot, m, k, o: cagrilar.append(m) or "ok", tur_sayisi=2,
             _cagir=_yoklama([[], [_g(5, "ilk taze soru")]], govdeler), gonder=lambda t, r: True,
             _uyku=lambda s: None)
    assert cagrilar == ["ilk taze soru"]
    assert [g["timeout"] for g in govdeler] == [0, 50]
    olay = [e for e in obs.recent(50) if e.get("event") == "telegram_ilk_ofset"]
    assert len(olay) == 1 and olay[0].get("atlanan") == 0


def test_ilk_yoklama_hatasinda_atlama_bir_sonraki_basarili_turda(sandbox_state, monkeypatch):
    _sirlar(monkeypatch)
    cagrilar, govdeler = [], []
    td.dongu(bota_sor=lambda bot, m, k, o: cagrilar.append(m) or "ok", tur_sayisi=3,
             _cagir=_yoklama([OSError("ağ"), [_g(20, "birikmiş")], [_g(21, "taze")]], govdeler),
             gonder=lambda t, r: True, _uyku=lambda s: None)
    assert cagrilar == ["taze"] and [g["timeout"] for g in govdeler] == [0, 0, 50]


def test_ilk_yoklama_sayfasi_doluysa_atlama_surer(sandbox_state, monkeypatch):
    # Telegram bir yoklamada en çok `GUNCELLEME_SAYFASI` güncelleme verir: dolu sayfa birikimin BİTTİĞİNİ söylemez.
    _sirlar(monkeypatch)
    n = td.GUNCELLEME_SAYFASI
    cagrilar, govdeler = [], []
    td.dongu(bota_sor=lambda bot, m, k, o: cagrilar.append(m) or "ok", tur_sayisi=3,
             _cagir=_yoklama([[_g(i) for i in range(n)], [_g(n, "birikim son")], [_g(n + 1, "taze")]], govdeler),
             gonder=lambda t, r: True, _uyku=lambda s: None)
    assert cagrilar == ["taze"]
    assert all(g.get("limit") == n for g in govdeler)
    assert [(g["offset"], g["timeout"]) for g in govdeler] == [(0, 0), (n, 0), (n + 1, 50)]
    olay = [e.get("atlanan") for e in obs.recent(50) if e.get("event") == "telegram_ilk_ofset"]
    assert olay == [n, 1]


def test_dongu_varsayilan_bildirimi_notify_yanitla(sandbox_state, monkeypatch):
    _sirlar(monkeypatch)
    store.write_json(td.OFSET_DOSYASI, {"ofset": 0})
    giden = []
    monkeypatch.setattr(td.notify, "yanitla", lambda t, reply_to=None: giden.append((t, reply_to)) or True)

    class Hemen(_SahteZamanlayici):
        def start(self):
            self.basladi = True
            self.fn()

    zs = []
    td.dongu(bota_sor=lambda *a: "ok", tur_sayisi=1, _cagir=_yoklama([[_g(3, "merhaba")]], []),
             _uyku=lambda s: None, _zamanlayici=lambda sure, fn: Hemen(zs, sure, fn))
    assert len(giden) == 2 and giden[0][1] == 3
    assert giden[0][0].startswith("💬 @sef · tg-sef-") and giden[0][0].endswith("\n⏳ düşünüyor…")
    assert giden[1][1] == 3 and giden[1][0].startswith("💬 @sef · tg-sef-") and giden[1][0].endswith("\nok")
