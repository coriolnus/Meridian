"""v511 · SESSİZ koşumun durum satırı ÖNCEKİ hükmü kendi hükmü gibi göstermez — TSK-198.

NUMARA KİMLİKTİR — VE BU DOSYA BİR KEZ TAŞINDI (2026-09-16). İlk ölçüm `v510` demişti: `ls tests/`
bu worktree'de (tsk198) en büyük `v509`u (`test_ansible_a0_docker_grubu_v509.py`) veriyordu ve
`v510` bu çalışma kopyasının hiçbir dosya adında, hiçbir belgesinde GEÇMİYORDU (tek eşleşme
v509'un kendi başlığındaki "çakışma ölçülmedi" notuydu). Ölçüm doğruydu ama KÖRDÜ: `v510`u
PARALEL bir dilim (massive hacim kapısı) AYRI bir worktree'de çoktan almıştı ve ayrı çalışma
kopyaları birbirinin yeni dosyasını GÖREMEZ — rezervasyon yapılmadığı sürece `ls` bunu ölçemez.
Rol-1 uyarısı üzerine dosya `v511`e taşındı (CLAUDE.md §2: çakışmada az-çapalı taraf taşınır,
kaydı dosya başlığına; bu dosya o an sıfır dış çapa taşıyordu). `v511` taşımadan önce aynı
yöntemle ÖLÇÜLDÜ: ne dosya adı ne de metin olarak hiçbir yerde geçmiyordu.

DERS (bu satır bir gelecek turun bedelini kapatır): eşzamanlı worktree'lerde `vNNN` ölçümü
gerekli ama YETERLİ değildir — numarayı Rol-1 rezerve etmezse iki dilim aynı sayıyı ölçerek
alabilir ve ikisi de haklı olur.

NEDEN AYRI DOSYA, NEDEN `test_sef_brifingi_v330.py`ye EKLENMEDİ: v330 "üç kaynak TEK brifinge
iner ve LLM düşerse teslimat DÜŞMEZ" sözleşmesini ölçer — bu dosyanın sorusu ORASI değil, ÇIKTI
SÖZLEŞMESİdir: operatörün okuduğu satır hangi koşuma ait? Deponun emsali de budur —
`test_soul_denetimi_teshis_v434.py` tam bu sınıf için (durum satırının yeni alanları okuması)
v385'ten AYRILMIŞTI, `test_ansible_a0_terraform_v501.py` de aynı gerekçeyle v451'den. Ayrıca v330
1400 satırın üstünde ve ölçtüğü sözleşme bu turda DEĞİŞMEDİ.

ÖLÇÜLEN SORUN (kök neden, Rol-1 ölçümü): `main()` ilk iş `_durum_satiri`yi basar ve bu basım DAL
KARARINDAN ÖNCEDİR — yani satır, o koşumda kural denetimi olup olmayacağını BİLMEZ. Satırın iki
hüküm alanı da GEÇMİŞİ okur: `kural denetimi:` damga dosyasından (`sef_brifingi_damga.json`, yalnız
teslimattan SONRA yazılır), `denetçi teşhisi:` olay defterinin son N olayından. Denetime hiç
varılmayan İKİ sessiz dalda (iki kaynak da boş · model `SESSIZ` dedi) satır yine tarihli bir hüküm
basıyor ve etiket yüzünden operatör bunu O KOŞUMUN hükmü sanıyordu.

BASILAN DEĞER UYDURMA DEĞİLDİR ve bu tur onu BOZMAZ: tarihli, son BİLİNEN hüküm; tarih basımı da
bilinçli bir inceleme kalemiydi (Ö-4, 2026-09-03 — tarihsiz satır bayat hükmü TAZE gösterirdi).
Eklenen tek şey BAĞLAMDIR, ve K4 tarihin yerinde durduğunu ayrıca çivi ile tutar.

BİÇİM SEÇİMİ ÖLÇÜMLE VERİLDİ: satırı ikiye bölme ("bu koşum: …" / "son teslim edilen hüküm: …")
alternatifi ARANDI ve biçime bağlı okuyucu BULUNDU — `test_soul_denetimi_v385.py` ve
`test_soul_denetimi_teshis_v434.py` `kural denetimi: <hüküm>/<kaynak>` dizgesini ADIYLA arıyor.
Bölme, çözdüğü belirsizlikten geniş bir yüzeyi kırardı. Onun yerine dal kararından SONRA İKİNCİ
bir satır basılır; etiketler literal değil TEK KAYNAKTAN (`ETIKET_KURAL_DENETIMI` /
`ETIKET_DENETCI_TESHISI`) gelir, yoksa uyarı bir gün var olmayan bir alanı işaret ederdi.

KAPSAM TARAMASI BU DOSYADA DA VAR (K5): `@bekci` ve `@karne` ÖLÇÜLDÜ (2026-09-16) ve bu okuyucu
sınıfını HİÇ TAŞIMIYORLAR — durum satırları yalnız O KOŞUMUN topladığı sayıları basıyor, damga
hükmü ya da defter olayı okumuyorlar. Düzeltilecek bir şey YOK; K5 bu yüzden bir DÜZELTME çivisi
değil İMA çivisidir: okuyucu eklendiği gün bağlam satırı da eklenmiş olmalı. Bugünkü ısırığını
`@sef` üzerinden alır (pozitif kontrol), yani vakum-yeşil değildir.

SANDBOX HER ÇİVİDE: koşumlar `obs.log` yazar ve damga dosyasına dokunur — `sandbox_state`
olmadan canlı `state/`e test artefaktı düşerdi.
"""
from __future__ import annotations

import importlib
import pathlib

import pytest

from tests.test_soul_denetimi_v385 import _sef_kur, _temiz_cevap, _Kuyruk

KOK = pathlib.Path(__file__).resolve().parent.parent

#: Bayat hüküm uyarısının DEĞİŞMEZ çekirdeği. Metnin tamamı değil, operatörün gözünün takılacağı
#: iddia aranır — tam dizge aranırsa çivi ifadenin cilasına bağlanır, ölçtüğü sözleşmeye değil.
UYARI_CEKIRDEGI = "BU KOŞUMDA KURAL DENETİMİ YOK"

#: `@sef`in GEÇMİŞ okuyucuları — K5'in tarama sözlüğü. Adlar burada literal durur ama ÇÜRÜMEZ:
#: K5 önce üretim modülünde var olduklarını doğrular (`hasattr`), sonra kardeşlerde arar.
GECMIS_OKUYUCULARI = ("_kural_denetimi_satiri", "_denetci_teshis_satiri")

#: Bağlam satırını basan yardımcı — K5 kardeşlerde BUNU arar.
BAGLAM_YARDIMCISI = "_denetimsiz_kosum_satiri"


def _damgaya_bayat_hukum_yaz(m, ts="2026-01-01T00:00:00+00:00"):
    """Damgaya TARİHLİ ve BAYAT bir hüküm koyar — sessiz dalların yanlış okunma zemini tam budur.

    Gerçek teslimatla yazdırmak yerine doğrudan yazılır: ölçülen şey damganın NASIL oluştuğu değil,
    damga DOLUYKEN sessiz bir koşumun operatöre ne söylediğidir."""
    from meridian import store
    store.write_json(m.DAMGA_DOSYA, {m.KURAL_DENETIMI: {
        "hukum": "temiz", "kaynak": "llm", "cagri_n": 2, "yeniden_uretim": False,
        "ihlal": [], "gerekce": "denetçi hükmü", "ts": ts}})
    return ts


def _bos_kaynaklar(m, monkeypatch):
    """İki kaynak da ÖLÇÜLDÜ ve ikisi de BOŞ — `ham["bos"]` dalının kurulumu."""
    monkeypatch.setattr(m, "_alarm_ozeti", lambda: {"toplam": 0, "yeni": 0, "mesaj": None})
    monkeypatch.setattr(m, "_oneri_ozeti",
                        lambda: {"toplam": 0, "yeni": 0, "en_yeni": "", "mesaj": None})


# ================================================================================================
# K1 — BOŞLUK DALI: model hiç çağrılmadı
# ================================================================================================

def test_K1_BOS_DALDA_SATIR_BU_KOSUMDA_DENETIM_YOK_DER(tmp_path, monkeypatch, capsys,
                                                       sandbox_state, request):
    """İki kaynak da boşken model ÇAĞRILMAZ, yani denetim akışına hiç varılmaz — ama durum satırı
    yine tarihli bir hüküm basar. Operatör o hükmü bu koşuma ait sanmamalı."""
    m, _ = _sef_kur(tmp_path, monkeypatch, request)
    ts = _damgaya_bayat_hukum_yaz(m)
    _bos_kaynaklar(m, monkeypatch)
    cagrildi: list = []
    monkeypatch.setattr(m, "_profili_cagir", lambda p: cagrildi.append(p) or "x")

    assert m.main([]) == 0
    cikti = capsys.readouterr().out
    assert not cagrildi, "boş dalda model çağrıldı — dalın ön şartı bozuk, çivi yanlış şeyi ölçüyor"
    assert UYARI_CEKIRDEGI in cikti, f"sessiz koşum bağlamı basmadı: {cikti!r}"
    assert ts in cikti, f"uyarı hükmün TARİHİNİ taşımıyor — 'hangi koşum' cevapsız: {cikti!r}"


def test_K1_UYARI_IKI_HUKUM_ALANINI_DA_ADIYLA_ANAR(tmp_path, monkeypatch, capsys, sandbox_state,
                                                   request):
    """İki alan İKİ AYRI kaynağı okur (damga ↔ olay defteri) ve farklı koşumlara ait olabilir.
    Yalnız birini uyarmak, ötekini örtük olarak "bu koşumun" saydırırdı.

    ETİKETLER ÜRETİMDEN OKUNUR, bu dosyaya KOPYALANMAZ: kopya, etiket değiştiği gün sessizce
    eskir ve çivi var olmayan bir alanı doğrulamış olurdu (tek-kaynak yasası)."""
    m, _ = _sef_kur(tmp_path, monkeypatch, request)
    _damgaya_bayat_hukum_yaz(m)
    _bos_kaynaklar(m, monkeypatch)
    monkeypatch.setattr(m, "_profili_cagir", lambda p: "x")

    assert m.main([]) == 0
    cikti = capsys.readouterr().out
    for etiket in (m.ETIKET_KURAL_DENETIMI, m.ETIKET_DENETCI_TESHISI):
        assert etiket in cikti.split(UYARI_CEKIRDEGI)[1], (
            f"`{etiket}` uyarıda anılmıyor — o alan örtük olarak bu koşumun sayılır: {cikti!r}")


def test_K1_DAMGA_BOSKEN_UYARI_YOKLUGU_ADIYLA_SOYLER(tmp_path, monkeypatch, capsys,
                                                     sandbox_state, request):
    """UYDURMA YASAĞI okuyucu tarafında da geçerli: damgada hüküm yokken uyarı bir tarih
    UYDURMAZ, yokluğu ADIYLA basar. `ts` alanı bugünün tarihiyle doldurulsaydı, hiç koşmamış bir
    denetim "bugün koştu" diye okunurdu — düzeltmenin kendisi kapattığı sınıfı üretirdi."""
    m, _ = _sef_kur(tmp_path, monkeypatch, request)
    _bos_kaynaklar(m, monkeypatch)
    monkeypatch.setattr(m, "_profili_cagir", lambda p: "x")

    assert m.main([]) == 0
    cikti = capsys.readouterr().out
    assert UYARI_CEKIRDEGI in cikti, f"damga boşken uyarı hiç basılmadı: {cikti!r}"
    assert "damgada hüküm YOK" in cikti, f"yokluk adıyla basılmadı: {cikti!r}"


# ================================================================================================
# K2 — MODEL `SESSIZ` DEDİ: sıralama çağrıldı, denetim ÇAĞRILMADI
# ================================================================================================

def test_K2_MODEL_SESSIZ_DALINDA_DA_BAGLAM_BASILIR(tmp_path, monkeypatch, capsys, sandbox_state,
                                                   request):
    """İKİNCİ sessiz dal ve K1'inkinden FARKLI: burada model GERÇEKTEN çağrıldı — düşen şey
    denetim katmanıdır (`SESSIZ` hükmü `_kural_gecisi`e hiç varmadan döner). İki katmanı
    karıştırmamak için uyarı bu dalda da basılmak ZORUNDA."""
    m, _ = _sef_kur(tmp_path, monkeypatch, request)
    ts = _damgaya_bayat_hukum_yaz(m)
    kuyruk = _Kuyruk("SESSIZ")
    monkeypatch.setattr(m, "_profili_cagir", kuyruk)

    assert m.main([]) == 0
    cikti = capsys.readouterr().out
    assert kuyruk.n == 1, f"sıralama çağrısı yapılmadı — dalın ön şartı bozuk: {kuyruk.n}"
    assert "BOT `SESSIZ` DEDİ" in cikti, f"dal değişmiş, çivi yanlış dalı ölçüyor: {cikti!r}"
    assert UYARI_CEKIRDEGI in cikti, f"`SESSIZ` dalında bağlam basılmadı: {cikti!r}"
    assert ts in cikti, f"uyarı hükmün TARİHİNİ taşımıyor: {cikti!r}"


def test_K2_UYGULA_DALINDA_DA_BASILIR(tmp_path, monkeypatch, capsys, sandbox_state, request):
    """Kuru koşum ile `--uygula` AYNI dalı paylaşır; zamanlanmış koşum `--uygula` ile gider, yani
    operatörün systemd günlüğünde GÖRECEĞİ hâl budur. Yalnız kuru koşumda basılan bir uyarı, tam
    da okunacağı yerde yok olurdu."""
    m, _ = _sef_kur(tmp_path, monkeypatch, request)
    _damgaya_bayat_hukum_yaz(m)
    monkeypatch.setattr(m, "_profili_cagir", _Kuyruk("SESSIZ"))
    monkeypatch.setattr(m.notify, "configured", lambda: True)
    gonderilen: list = []
    monkeypatch.setattr(m.notify, "send", lambda t: (gonderilen.append(t), True)[1])

    assert m.main(["--uygula"]) == 0
    cikti = capsys.readouterr().out
    assert not gonderilen, "`SESSIZ` hükmüne rağmen mesaj gitti — dal bozuk"
    assert UYARI_CEKIRDEGI in cikti, f"`--uygula` dalında bağlam basılmadı: {cikti!r}"


# ================================================================================================
# K3 — YANLIŞ-POZİTİF YOK: denetim GERÇEKTEN koştuysa uyarı BASILMAZ
# ================================================================================================

def test_K3_DENETIM_KOSTUYSA_UYARI_BASILMAZ(tmp_path, monkeypatch, capsys, sandbox_state,
                                            request):
    """UYARI HER KOŞUMDA BASILSAYDI HİÇBİR ŞEY SÖYLEMEZDİ. Denetimin gerçekten koştuğu ve
    teslimatın gittiği turda satır olduğu gibi kalır — ve damgadaki hüküm ARTIK bu koşumundur."""
    m, _ = _sef_kur(tmp_path, monkeypatch, request)
    gercek = "- MECHANISM_STALE 5 kez: danışma katmanı ölü, bugün bak"
    monkeypatch.setattr(m, "_profili_cagir", _Kuyruk(gercek, _temiz_cevap()))
    monkeypatch.setattr(m.notify, "configured", lambda: True)
    gonderilen: list = []
    monkeypatch.setattr(m.notify, "send", lambda t: (gonderilen.append(t), True)[1])

    assert m.main(["--uygula"]) == 0 and gonderilen, "teslimat düştü — çivi yanlış dalı ölçüyor"
    cikti = capsys.readouterr().out
    assert UYARI_CEKIRDEGI not in cikti, (
        f"denetim KOŞTUĞU hâlde 'denetim yok' uyarısı basıldı — yanlış alarm: {cikti!r}")
    assert m._son_kural_denetimi().get("hukum") == "temiz", "denetim hükmü damgaya yazılmadı"


def test_K3_KURU_KOSUMDA_TESLIMAT_DALINDA_DA_BASILMAZ(tmp_path, monkeypatch, capsys,
                                                      sandbox_state, request):
    """Kuru koşum teslim etmez ama denetim KOŞAR (`sirala` tam yolu yürür). Uyarı "teslimat yok"a
    değil "denetim yok"a bağlıdır; ikisini karıştıran bir kapı kuru koşumda her gün öterdi."""
    m, _ = _sef_kur(tmp_path, monkeypatch, request)
    kuyruk = _Kuyruk("- MECHANISM_STALE 5 kez: danışma katmanı ölü, bugün bak", _temiz_cevap())
    monkeypatch.setattr(m, "_profili_cagir", kuyruk)

    assert m.main([]) == 0
    cikti = capsys.readouterr().out
    assert kuyruk.n == 2, f"denetim çağrısı yapılmadı — dalın ön şartı bozuk: {kuyruk.n}"
    assert "KURU KOŞU" in cikti, f"kuru koşum dalı değişmiş: {cikti!r}"
    assert UYARI_CEKIRDEGI not in cikti, f"denetim koştuğu hâlde uyarı basıldı: {cikti!r}"


# ================================================================================================
# K4 — 2026-09-03 KALEMİ BOZULMADI: damgadan okunan hükmün `ts`i YERİNDE
# ================================================================================================

def test_K4_DURUM_SATIRI_HUKMU_VE_TARIHINI_AYNEN_TASIR(tmp_path, monkeypatch, sandbox_state,
                                                       request):
    """Ö-4 (2026-09-03) kalemi: damga YALNIZ teslimattan sonra yazılır, tarihsiz basılan bir satır
    bayat hükmü TAZE gösterirdi. Bu tur BAĞLAM ekledi, hükmü ya da tarihi SİLMEDİ — satır hâlâ
    hem hükmü hem tarihi taşır.

    MUTASYON HEDEFİ: `ts` satırdan çıkarılırsa ya da hüküm alanı bağlam uğruna kaldırılırsa bu
    çivi öter."""
    m, _ = _sef_kur(tmp_path, monkeypatch, request)
    ts = _damgaya_bayat_hukum_yaz(m)
    satir = m._durum_satiri(m.topla())
    assert f"{m.ETIKET_KURAL_DENETIMI}: temiz/llm" in satir, (
        f"hüküm alanı etiketiyle birlikte basılmıyor: {satir!r}")
    assert ts in satir, f"satır TARİH taşımıyor — bayat hüküm taze görünür: {satir!r}"
    assert "denetçi hükmü" in satir, f"gerekçe okunmuyor: {satir!r}"


def test_K4_ETIKETLER_TEK_KAYNAKTAN_GELIR(tmp_path, monkeypatch, sandbox_state, request):
    """Uyarı, durum satırındaki alanları ADIYLA işaret eder. İki yerde ayrı literal dursaydı biri
    değiştiği gün uyarı var olmayan bir alanı gösterirdi — yanlış adrese bakan bir uyarı, uyarı
    olmamaktan beterdir.

    ÖLÇÜ: sabitin DEĞERİ değiştirilir ve İKİ üretici de (satır + uyarı) yeni değeri basar mı?"""
    m, _ = _sef_kur(tmp_path, monkeypatch, request)
    _damgaya_bayat_hukum_yaz(m)
    monkeypatch.setattr(m, "ETIKET_KURAL_DENETIMI", "ZIPZIP-ETIKET")
    satir = m._durum_satiri(m.topla())
    uyari = m._denetimsiz_kosum_satiri("çivi")
    assert "ZIPZIP-ETIKET" in satir, f"durum satırı sabiti kullanmıyor (literal): {satir!r}"
    assert "ZIPZIP-ETIKET" in uyari, f"uyarı sabiti kullanmıyor (literal): {uyari!r}"


# ================================================================================================
# K5 — KAPSAM TARAMASI: kardeş botlar (ÖLÇÜLDÜ 2026-09-16)
# ================================================================================================

@pytest.mark.parametrize("bot", ["sef", "bekci", "karne"])
def test_K5_GECMIS_OKUYUCUSU_OLAN_BOT_BAGLAM_SATIRINI_DA_BASAR(bot):
    """TEK-KAYNAK KAPISI: üç kopya sessizce ayrışır. Bir bot durum satırında GEÇMİŞ okuyorsa
    (damga hükmü ya da defter olayı), sessiz dalında o hükmün bu koşuma ait olmadığını da
    söylemek ZORUNDA.

    ÖLÇÜLEN HÂL (2026-09-16): `@bekci` ve `@karne` bu okuyucu sınıfını HİÇ taşımıyor — durum
    satırları yalnız O KOŞUMUN topladığı sayıları basıyor (`bildirilecek`/`bastırılan`/`tarama
    hatası` ve `hüküm dağılımı`/`değişim`/`hesap hatası`). Yani düzeltilecek bir desen YOKTU ve
    bu çivi onlar için bugün bir İMA'dır: okuyucu eklendiği gün ateşler.

    VAKUM-YEŞİL DEĞİLDİR: `@sef` parametresi bugün İKİ tarafı da dolu olan gerçek koşuldur, yani
    çivi `_denetimsiz_kosum_satiri` `main`den kaldırılırsa BUGÜN öter."""
    sef = importlib.import_module("ops.sef_brifingi")
    for ad in GECMIS_OKUYUCULARI + (BAGLAM_YARDIMCISI,):
        assert hasattr(sef, ad), (
            f"tarama sözlüğü çürüdü: `{ad}` `@sef`te YOK — liste güncellenmeden bu çivi "
            "hiçbir şey ölçmez")

    src = (KOK / "ops" / f"{bot}_brifingi.py").read_text(encoding="utf-8")
    okuyan = [ad for ad in GECMIS_OKUYUCULARI if ad in src]
    if not okuyan:
        assert bot != "sef", "pozitif kontrol düştü: `@sef` geçmiş okuyucusunu kaybetti"
        return
    assert BAGLAM_YARDIMCISI in src, (
        f"@{bot} durum satırında GEÇMİŞ okuyor ({', '.join(okuyan)}) ama sessiz koşumda bunu "
        f"söyleyen `{BAGLAM_YARDIMCISI}` yok — TSK-198'in kapattığı desen burada açık")


@pytest.mark.parametrize("bot", ["bekci", "karne"])
def test_K5_KARDESLERIN_DURUM_SATIRI_YALNIZ_BU_KOSUMU_BASAR(bot, monkeypatch, sandbox_state):
    """Taramanın POZİTİF hâli: kardeşlerin satırı gerçekten bu koşumun `ham`ından mı geliyor?
    Sembol taraması "okuyucu yok" der; bu çivi satırın KENDİSİNİ kurarak aynı şeyi ÇIKTIDAN
    ölçer — sembol adı değişirse taramanın kör kaldığı yeri burası yakalar.

    GİRDİLER SAPLANIR ve saplar KARDEŞ ÇİVİ DOSYALARINDAN ithal edilir (tek-kaynak: hüküm/kapsam
    şeması burada YENİDEN yazılsaydı, şema değiştiği gün bu çivi ölçtüğünü sanır ve patlardı).
    Gerçek tarama/hesap ÇAĞRILMAZ: ölçülen şey çıktı sözleşmesidir, veri değil."""
    m = importlib.import_module(f"ops.{bot}_brifingi")
    if bot == "bekci":
        monkeypatch.setattr(m, "_tarama", lambda bilinen=frozenset(): {})
    else:
        from tests.test_karne_brifingi_v338 import _sonuc
        monkeypatch.setattr(m, "_hesap", lambda: _sonuc())
    satir = m._durum_satiri(m.topla())
    sef = importlib.import_module("ops.sef_brifingi")
    for yasak in (sef.ETIKET_KURAL_DENETIMI, sef.ETIKET_DENETCI_TESHISI, UYARI_CEKIRDEGI):
        assert yasak not in satir, (
            f"@{bot} durum satırı geçmiş hüküm taşıyor ({yasak!r}) — TSK-198 deseni buraya da "
            f"geldi, bağlam satırı gerekiyor: {satir!r}")
