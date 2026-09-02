"""PLAN ÇEKMECESİ — sembole tıkla, tam gövdeyi gör, REVIEW'ü karara bağla (v311, 2026-08-25)

OPERATÖR İSTEĞİ (2026-08-25): "sembollerin üzerine tıklayıp bilgilerini görebilmeliyim,
ve review da ise onaylayabilmeliyim veya reddedebilmeliyim."

NEDEN ÇİVİ KAYNAK METNİ ÜZERİNDE. Bu depoda pano kaynağının koştuğu bir tarayıcı
testi yok; ölçülebilir tek zemin TSX kaynağının KENDİSİ. Bu yüzden her iddia
ÇAĞRI BİÇİMİYLE çivilenir (regex), "şu dize dosyada geçiyor mu" ile DEĞİL —
alt-dize tuzağı: bir uç adının yorumda geçmesi, o ucun ÇAĞRILDIĞI anlamına gelmez.
Yorumlar bu yüzden ölçümden önce SOYULUR.

ÇİVİLENEN SÖZLEŞME (istek + uçların gerçek yasası):
  1. Sembol hücresi TIKLANABİLİR ve çekmeceyi açar.
  2. İki uç da çağrı biçimiyle çağrılır: `/onayla` gövdesiz, `/reddet` `{gerekce}` ile.
  3. ONAY YALNIZ REVIEW'DE ÇİZİLİR. `loop.operator_onay_ver` NO_GO'yu MUTLAK reddeder
     (409) ve REVIEW dışını da reddeder; NO_GO'ya onay düğmesi çizmek, operatöre
     kapının ezilebileceğini söylemek olurdu.
  4. Ret NO_GO'da da mümkündür (görme kaydı) — ama ONAYLI planda değildir
     (`operator_ret_ver` 409: onay icra yetkisidir, ret onu geri almaz).
  5. Gerekçe ZORUNLU ve eşiği (`loop.RET_MIN_GEREKCE` = 12) EKRANDA yazılıdır.
  6. RET BİR DURDURMA DEĞİLDİR: onaylanmayan REVIEW zaten silahlanmaz. Ekran bunu
     yazmazsa, operatör bir şeyi durdurduğunu SANIR — bu testin en pahalı çivisi.
  7. Hata gövdesi (400/409) AYNEN gösterilir; sessiz "olmadı" yok.
  8. Başarılı istekten sonra veri YENİDEN OKUNUR (iyimser güncelleme yok) — VLO
     dersi: panonun "oldu herhâlde" diye çizdiği başarı, gitmemiş emri gitmiş gösterir.
  9. ONAY KAPISI = UCUN KAPISI, "REVIEW" DEĞİL. `loop.operator_onay_ver` REVIEW'ün
     ÜSTÜNE beş kapı daha koyar: tarihsiz plan · seansı geçmiş plan (`pdate < book_at`)
     · HALT aktif · sembol zaten açık pozisyon · slot tavanı. İlk ikisi plan satırından
     ÖLÇÜLEBİLİR (`date`, `expired` — `expired` tam olarak `pdate < book_at`tir, çünkü
     `_enrich_stale_plans`in `latest_session`ı da `portfolio.json.last_date`tir), o
     yüzden düğmeyi kesmek ZORUNDALAR. Kalan üçü plan satırından ölçülemez; ekran
     onları SUSARAK değil BEYAN EDEREK karşılar.
 10. GO PANELİNİN RET CÜMLESİ İCRAYA DARALTILMIŞTIR. "İkisi de hiçbir şeyi
     değiştirmezdi" YANLIŞTI: `operator_ret_ver` hükme HİÇ bakmaz — GO planına
     gönderilen ret 200 döner ve deftere gerekçeli bir GÖRME kaydı YAZAR. Ekran artık
     ucun ne yapacağını söyler ve düğmeyi neden ÇİZMEDİĞİNİ ayrıca gerekçelendirir.
 11. SATIR ÇAPASI YOK. `dosya.py:NNN` çapaları ilk düzenlemede bayatlar ve YANLIŞ yere
     işaret eder (çapa-mezar-taşı; ölçüldü: `api.py:5841` artık `_enrich_stale_plans`
     değil `api_approvals`). Çapa SEMBOL adıyla atılır.

MUAFİYET İŞARETİ SONRADAN KONDU (TSK-106 turu, 2026-09-02) ve nedeni tam da bu dosyanın
dersidir: bu üç satır bayat bir çapayı KANIT olarak alıntılıyor, yani `_CAPA_MUAFIYETI`nin
(`çapa-mezar-taşı`) tanımına birebir giriyorlar — ama işaret yoktu ve `codelaw` onları
İHLAL sayacaktı. Bugüne kadar geçmelerinin sebebi doğruluk değil KAZAydı:
çapa-mezar-taşı `api.py:5841` tesadüfen bir KOD satırına düşüyordu; api.py'de satır ekleyen
ilk değişiklikte (bu tur) çapa bir YORUM satırına kaydı ve üçü birden ötmeye başladı — yani
dosyanın 11. maddesi kendi gövdesinde ölçüldü (bu paragrafın kendisi de dördüncü kez ötürdü:
alıntının işaretsizi yoktur). Doğru tepki numarayı güncellemek DEĞİL
(çapa zaten mezar taşı), alıntıyı beyanlı muafiyetle işaretlemektir; `tests/conftest.py`
aynı sınıfı 2026-08-24'te aynı işaretle kapatmıştı.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

KOK = Path(__file__).resolve().parent.parent
BUGUN = KOK / "ui" / "src" / "pano" / "yuzeyler" / "bugun"
TABLO = BUGUN / "PlanTablosu.tsx"
CEKMECE = BUGUN / "PlanCekmecesi.tsx"

pytestmark = pytest.mark.skipif(not TABLO.exists(), reason="ui/ yok — pano kaynağı bu ağaçta değil")


def _soy(metin: str) -> str:
    """Yorumları atar. Bir kuralın YORUMDA geçmesi, uygulandığı anlamına gelmez —
    bu deponun tekrar eden ölçüm hatası (bkz. `test_pano_yuzey_kaydi_v288._soy`)."""
    metin = re.sub(r"\{/\*.*?\*/\}", "", metin, flags=re.S)
    metin = re.sub(r"/\*.*?\*/", "", metin, flags=re.S)
    metin = re.sub(r"^\s*//.*$", "", metin, flags=re.M)
    return metin


def _kaynak(p: Path) -> str:
    return _soy(p.read_text(encoding="utf-8"))


def _tek_dugme_etiketi(metin: str, isaret: str) -> str:
    """`isaret`i içeren `<Button …>` AÇILIŞ ETİKETİNİ (öznitelikleriyle) döndürür.

    NEDEN ETİKET, NEDEN DOSYA GENELİ DEĞİL: `disabled` sözcüğünün dosyada BİR YERDE
    geçmesi, o sözcüğün ŞU düğmede durduğunu kanıtlamaz. Denetçi tam bu deliği sömürdü
    (2026-08-25): "Reddet" ve "EVET, GÖNDER" düğmelerinden eşik kapısı SÖKÜLÜNCE test
    hâlâ yeşil kaldı, çünkü ölçüm yalnız `gerekceYetersiz` İFADESİNİN varlığına bakıyordu.
    """
    assert metin.count(isaret) == 1, (
        f"`{isaret}` {metin.count(isaret)} kez geçiyor — ölçüm hangi düğmeye baktığını "
        f"bilemez; tek geçiş olmalı"
    )
    i = metin.index(isaret)
    bas = metin.rfind("<Button", 0, i)
    assert bas != -1, f"`{isaret}` bir <Button> etiketinin içinde değil"
    return metin[bas:i]


def _kapi_kapanisi(metin: str, ad: str) -> str:
    """`const <ad> = …;` tanımını, İÇİNDE GEÇEN yerel bayrakların tanımlarıyla birleştirir.

    Ara bayrak yazmak okunabilirlik için meşrudur (`const seansiGecmis = plan.expired === true`),
    ama yalnız bayrağın ADINA bakan bir ölçüm, o bayrağı `false` yapan bir mutasyonu
    kaçırırdı — kapı adı yerinde durur, kapı açılır. Bu yüzden BİR SEVİYE açılır ve
    ölçüm birleşik metinde yapılır.
    """
    ana = re.search(rf"const {ad}\s*=([^;]*);", metin)
    assert ana is not None, f"`{ad}` kapısı tanımlı değil"
    parcalar = [ana.group(1)]
    for kimlik in sorted(set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", ana.group(1)))):
        alt = re.search(rf"const {kimlik}\s*=([^;]*);", metin)
        if alt is not None:
            parcalar.append(alt.group(1))
    return " ".join(parcalar)


def _sus_bloklar(metin: str, isaret: str) -> list[str]:
    """`isaret` ile başlayan HER JSX koşulunun süslü parantez bloğunu döndürür.

    Bir bayrağın TANIMLI olması, onay düğmesinin O BAYRAĞIN ALTINDA durduğunu
    kanıtlamaz. Blok çıkarımı bunu kanıtlar: düğmenin bloğun İÇİNDE olduğu ölçülür.

    NEDEN LİSTE, NEDEN İLK EŞLEŞME DEĞİL: aynı bayrak birden çok yerde koşul olabilir
    (uyarı şeridi + düğme). İlk bloğa bakan bir ölçüm, düğme ikinci bloktayken
    "kapının dışında" derdi — YALANCI POZİTİF, ve düzeltmesi kaynağı bozmak olurdu.
    """
    bloklar: list[str] = []
    bas = 0
    while True:
        i = metin.find(isaret, bas)
        if i == -1:
            break
        derinlik = 0
        kapandi = False
        for j in range(i, len(metin)):
            if metin[j] == "{":
                derinlik += 1
            elif metin[j] == "}":
                derinlik -= 1
                if derinlik == 0:
                    bloklar.append(metin[i : j + 1])
                    bas = j + 1
                    kapandi = True
                    break
        if not kapandi:
            raise AssertionError(f"blok kapanmadı: {isaret}")
    assert bloklar, f"işaret bulunamadı: {isaret}"
    return bloklar


# ==================================================================================================
# 1 · SEMBOL TIKLANABİLİR VE ÇEKMECEYİ AÇAR
# ==================================================================================================

def test_cekmece_dosyasi_var_ve_tablodan_cizilir():
    assert CEKMECE.exists(), "PlanCekmecesi.tsx yok — sembole tıklanınca açılacak yüzey yazılmamış"
    c = _kaynak(CEKMECE)
    assert re.search(r"export function PlanCekmecesi\(", c), "PlanCekmecesi dışa aktarılmıyor"
    t = _kaynak(TABLO)
    assert re.search(r'import \{ PlanCekmecesi \} from "\./PlanCekmecesi"', t), "tablo çekmeceyi import etmiyor"
    assert "<PlanCekmecesi" in t, "tablo çekmeceyi ÇİZMİYOR — import edilmiş ama kullanılmamış olabilir"


def test_sembol_hucresi_tiklanabilir_ve_secimi_cekmeceye_verir():
    """Sembol sütununun hücresi bir DÜĞMEdir ve tıklanınca satırın planını seçer."""
    t = _kaynak(TABLO)
    bas = t.find('id: "ticker"')
    son = t.find('id: "setup"')
    assert bas != -1 and son > bas, "sembol sütunu bulunamadı"
    hucre = t[bas:son]
    assert "<button" in hucre, "sembol hücresi düğme DEĞİL — tıklanabilirlik klavyeye de kapalı olurdu"
    assert re.search(r"onClick=\{\(\)\s*=>\s*sec\(row\.original\)\}", hucre), (
        "sembol hücresi seçim geri-çağrısını ÇAĞIRMIYOR (`onClick={() => sec(row.original)}` yok)"
    )
    assert re.search(r"function sutunlar\(\s*sec:", t), (
        "sütunlar modül sabiti kalmış — seçim geri-çağrısı sütun hücresine ulaşamaz"
    )


# ==================================================================================================
# 2 · İKİ UÇ DA ÇAĞRI BİÇİMİYLE ÇAĞRILIYOR
# ==================================================================================================

def test_onay_ucu_cagri_bicimiyle_cagriliyor():
    c = _kaynak(CEKMECE)
    assert re.search(r"krizPost\(\s*`/api/plan/\$\{[^`]*\}/onayla`\s*\)", c), (
        "`POST /api/plan/{id}/onayla` çağrı BİÇİMİYLE bulunamadı (uç gövde okumuyor, gövdesiz gider)"
    )


def test_ret_ucu_gerekce_govdesiyle_cagriliyor():
    c = _kaynak(CEKMECE)
    assert re.search(r"krizPost\(\s*`/api/plan/\$\{[^`]*\}/reddet`\s*,\s*\{\s*gerekce:", c), (
        "`POST /api/plan/{id}/reddet` `{gerekce}` gövdesiyle çağrılmıyor — uç gerekçesiz isteği 400'ler"
    )


# ==================================================================================================
# 3 · NO_GO'DA ONAY ÇİZİLMEZ (kapı ezilemez)
# ==================================================================================================

def test_onay_yalnizca_review_hukmunde_cizilir():
    c = _kaynak(CEKMECE)
    assert re.search(r'const onaylanabilir\s*=\s*hukum === "REVIEW"', c), (
        'onay kapısı REVIEW eşitliğiyle kurulmamış — `hukum !== "NO_GO"` gibi bir kapı, '
        "bilinmeyen hükümleri de onaylatırdı (uç 409 verir, ekran yalan söylerdi)"
    )
    bloklar = _sus_bloklar(c, "{onaylanabilir ? (")
    assert any('setNiyet("onayla")' in b for b in bloklar), (
        "onay düğmesi hiçbir `onaylanabilir` bloğunun İÇİNDE değil — NO_GO planında da çizilirdi"
    )
    assert c.count('setNiyet("onayla")') == 1, (
        "onay niyeti birden fazla yerde alınıyor — biri kapının dışında kalabilir"
    )


def test_no_go_nedeni_ekranda_yazili():
    c = _kaynak(CEKMECE)
    assert "NO_GO onaylanamaz" in c, "NO_GO'da onayın neden çizilmediği YAZILI değil"
    assert "disiplin kapısının sert reddi MUTLAKTIR" in c, (
        "reddin mutlaklığı yazılmamış — düğmenin yokluğu bir kusur gibi okunur"
    )


def test_no_go_da_ret_mumkun_ama_onay_kapisina_bagli_degil():
    """Ret NO_GO'da da çizilir (görme kaydı) — yani onay bayrağının bloğunda DURAMAZ."""
    c = _kaynak(CEKMECE)
    bloklar = _sus_bloklar(c, "{onaylanabilir ? (")
    assert all('setNiyet("reddet")' not in b for b in bloklar), (
        "ret düğmesi onay bloğunun içinde — NO_GO planında ret yolu kapanırdı"
    )
    tanim = re.search(r"const reddedilebilir\s*=([^;]*);", c)
    assert tanim is not None, "`reddedilebilir` kapısı tanımlı değil"
    g = tanim.group(1)
    assert '"REVIEW"' in g and '"NO_GO"' in g, "ret kapısı REVIEW ve NO_GO'yu birlikte tanımıyor"
    assert "zatenOnayli" in g, (
        "onaylı plan reddedilebilir görünüyor — uç 409 verir (`operator_ret_ver`) ve ekran "
        "operatöre durdurabileceği YANILSAMASI verirdi"
    )


def test_go_hukmunun_durumu_yazili_ve_karar_cizilmez():
    c = _kaynak(CEKMECE)
    assert re.search(r'hukum === "GO"', c), "GO dalı yok — GO planında ekran ne diyeceğini bilmiyor"
    # ETİKET METNİ 2026-08-26 SÖZLÜĞÜYLE GÜNCELLENDİ (docs/ARAYUZ-SOZLUGU.md):
    # "kapı"→"kontrol", "hüküm"→"karar", "silahlan"→"işleme hazırlan". Çivinin ölçtüğü
    # şey KELİME değil OLGU: "bu cümle ekranda YAZILI mı". Sözcük değişti, iddia aynı.
    assert "GO planı zaten işleme hazırlanır" in c, "GO planının durumu ekranda yazılı değil"


def test_go_panelinde_ret_yolunun_kapali_olma_sebebi_DURUST():
    """"İkisi de hiçbir şeyi değiştirmezdi" cümlesi RET için YANLIŞTI — ölçüldü.

    `loop.operator_ret_ver` gövdesinde `gate_verdict` hiçbir dalda OKUNMUYOR: kapılar
    gerekçe uzunluğu · planın defterde olması · onaylı olmaması. Yani GO planına gönderilen
    bir ret 200 döner ve deftere gerekçeli bir GÖRME kaydı YAZAR. Ekranın "hiçbir şeyi
    değiştirmezdi" demesi, ucun yaptığı bir şeyi yok saymaktı.

    SEÇİM (bu turda yapıldı): düğme AÇILMADI, cümle DARALTILDI. Gerekçe: GO planı ŞU AN
    icra ediliyor; buradaki bir "reddet" düğmesi operatöre durdurduğu YANILSAMASI verirdi
    ve bu çekmecenin var olma sebebi tam olarak o yanılsamayı önlemek (dosya başlığındaki
    "RET BİR DURDURMA DEĞİLDİR" bloğu). Ama ekran artık ucun ne YAPACAĞINI da söylüyor.
    """
    c = _kaynak(CEKMECE)
    assert "ikisi de hiçbir şeyi değiştirmezdi" not in c, (
        "GO paneli hâlâ FAZLA GENİŞ iddiada: ret ucu hükme bakmaz, GO planına ret 200 döner "
        "ve deftere kayıt yazar — 'hiçbir şeyi değiştirmezdi' ölçümle çelişiyor"
    )
    bloklar = _sus_bloklar(c, '{hukum === "GO" ? (')
    assert len(bloklar) == 1, f"GO dalı {len(bloklar)} kez kurulmuş — hangisinin okunduğu belirsiz"
    g = bloklar[0]
    assert "İCRAYI değiştirmezdi" in g, (
        "GO panelinde iddia icraya DARALTILMAMIŞ — onayın etkisizliği icra düzeyinde söylenmeli"
    )
    assert "operator_ret_ver" in g, (
        "GO panelinde ret ucunun ADI geçmiyor — ekran ucun ne yapacağını söylemiyor"
    )
    assert "GÖRME kaydı yazardı" in g, (
        "GO panelinde ret ucunun deftere kayıt YAZACAĞI söylenmiyor — düğmenin yokluğu "
        "'uç reddederdi' diye okunur, oysa uç kabul ederdi"
    )
    assert "kriz kolları" in g, "icrayı durduran gerçek kol GO panelinde adlandırılmamış"


def test_onay_kapisi_ucun_OLCULEBILEN_kapilarini_da_kapatiyor():
    """`onaylanabilir` ile `operator_onay_ver`in kapısı AYNI olmalı — ölçülebildiği kadarıyla.

    UÇ REVIEW'ÜN ÜSTÜNE BEŞ KAPI KOYAR (`loop.operator_onay_ver` gövdesi okundu):
    tarihsiz plan · `pdate < book_at` · HALT · sembol zaten açık pozisyon · slot tavanı.
    İlk ikisi PLAN SATIRINDAN ölçülebilir: `date` alanı ve `expired` damgası. `expired`
    ucun kapısının BİREBİR aynısıdır — `_enrich_stale_plans`in `latest_session`ı da
    `portfolio.json.last_date`tir, yani `operator_onay_ver`in `book_at`i ile aynı sayı.

    ÖLÇÜLEBİLEN KAPIYI ÇİZMEMEK BİR KUSURDUR: seansı geçmiş bir REVIEW planında düğme
    çizilirse operatör tıklar ve 409 yer. Dosyanın KENDİ gerekçesi bunu reddediyor
    ("bir düğme çizip 409 yedirmek, operatöre kapının ezilebileceğini söylerdi").
    """
    c = _kaynak(CEKMECE)
    kapi = _kapi_kapanisi(c, "onaylanabilir")
    assert '"REVIEW"' in kapi, "onay kapısı REVIEW eşitliğini kaybetmiş"
    assert "plan.expired" in kapi, (
        "onay kapısı `plan.expired`i OKUMUYOR — seansı geçmiş REVIEW planında düğme çizilir "
        "ve uç 409 verir (`seansı geçmiş plan onaylanamaz`)"
    )
    assert "plan.date" in kapi, (
        "onay kapısı `plan.date`i OKUMUYOR — tarihsiz planda düğme çizilir ve uç 409 verir "
        "(`planın tarihi yok — seans geçerliliği ÖLÇÜLEMİYOR`)"
    )


def test_onayi_olculen_kapi_kestiginde_ekran_SUSMUYOR():
    """REVIEW ama tarih/seans kapısı kapalıysa bölüm boş kalmaz: SEBEP yazılır."""
    c = _kaynak(CEKMECE)
    bloklar = _sus_bloklar(c, "{onayiOlculenKapiKesti ? (")
    assert any("Seansı geçmiş ya da tarihsiz REVIEW planı onaylanamaz" in b for b in bloklar), (
        "REVIEW olup da onay düğmesi çizilmeyen satırda sebep YAZILI değil — operatör "
        "düğmenin yokluğunu bir pano kusuru sanar"
    )
    kapi = _kapi_kapanisi(c, "onayiOlculenKapiKesti")
    assert '"REVIEW"' in kapi and "onaylanabilir" in kapi, (
        "sebep şeridinin koşulu hükümle VE onay kapısıyla kurulmamış — NO_GO'da da çizilirdi"
    )


def test_olculen_kapi_seridi_ONAYLI_planda_reti_ACIK_gostermiyor():
    """Seansı geçmiş AMA ONAYLI bir REVIEW planı gerçek bir durumdur — onayın ERTESİ GÜNÜ.

    `_enrich_stale_plans` bayat planları listeden atmıyor (var olma sebebi tam tersi:
    "süresi dolmuş sinyal taze karar gibi okunuyordu"), yani o satır ekranda kalır. O
    satırda `reddedilebilir` FALSE'tur — `operator_ret_ver` onaylıyı 409'lar — ve
    `zatenOnayli` şeridi zaten "Ret yolu kapalı" yazar. Aynı ekranda "RET YOLU AÇIK KALIR"
    demek iki cümlenin birbirini yalanlaması olurdu; operatör hangisine inanacağını bilemez.
    """
    c = _kaynak(CEKMECE)
    g = _sus_bloklar(c, "{onayiOlculenKapiKesti ? (")[0]
    i = g.find("RET YOLU AÇIK KALIR")
    assert i != -1, "ölçülen-kapı şeridinde ret yolunun durumu hiç söylenmiyor"
    assert "{reddedilebilir ? (" in g[:i], (
        "'RET YOLU AÇIK KALIR' cümlesi `reddedilebilir` kapısının ALTINDA değil — onaylı ve "
        "seansı geçmiş bir planda ekran hem 'ret yolu açık' hem 'ret yolu kapalı' derdi"
    )


def test_kapatilamayan_uc_kapilari_ekranda_BEYAN_ediliyor():
    """Plan satırından ÖLÇÜLEMEYEN üç kapı (HALT · açık pozisyon · slot) susarak geçilmez.

    Bu üçü `/api/today`in plan satırında YOK; çekmece yalnız plan satırını okuyor. Kapıyı
    kapatamıyoruz — ama sessiz kalmak, onayın tek kapısının REVIEW olduğunu söylemek olurdu.
    """
    c = _kaynak(CEKMECE)
    i = c.find("uç ayrıca şu kapıları koyar")
    assert i != -1, (
        "kapatılamayan uç kapıları ekranda BEYAN edilmiyor — operatör 409'u ancak "
        "gönderdikten sonra öğrenir ve sebebini panoda hiç görmez"
    )
    beyan = c[i : i + 600]
    for parca, ne in (("HALT", "HALT kapısı"),
                      ("zaten açık pozisyon", "aynı sembolde ikinci giriş kapısı"),
                      ("slot tavanı", "max_open_positions tavanı")):
        assert parca in beyan, f"beyanda `{ne}` yazılı değil"


# ==================================================================================================
# 4 · DÜRÜSTLÜK: ret bir durdurma DEĞİL; onay İCRA YETKİSİ
# ==================================================================================================

def test_retin_icra_etkisizligi_ekranda_yazili():
    c = _kaynak(CEKMECE)
    assert "onaylamazsan bu plan zaten icra EDİLMEZ" in c, (
        "retin icra etkisizliği yazılı değil — operatör bir şeyi durdurduğunu sanır"
    )
    assert "ret bir KAYITTIR" in c, "ret bir kayıt olduğunu ekranda söylemiyor"


def test_onayin_icra_yetkisi_oldugu_ve_ayna_emri_gidecegi_yazili():
    c = _kaynak(CEKMECE)
    assert "ONAY = İCRA YETKİSİDİR" in c, "onayın icra yetkisi olduğu yazılı değil"
    assert "aynaya emir" in c, "onay anında ayna emri gönderileceği yazılı değil"


def test_ucun_icra_yolu_beyani_ekrana_basiliyor():
    """`icra_yolu` ASIL HABERDİR: 'onaylandı' cümlesi emir gitti demek değildir (VLO vakası)."""
    c = _kaynak(CEKMECE)
    assert re.search(r"\{?\s*sonuc\.icra_yolu", c), "uçtan gelen `icra_yolu` ekrana basılmıyor"


# ==================================================================================================
# 5 · GEREKÇE ZORUNLULUĞU EKRANDA
# ==================================================================================================

def test_gerekce_esigi_ekranda_yazili_ve_dugmeyi_kilitliyor():
    """Testin adının İKİ yarısı da ölçülür: eşik EKRANDA yazılı, VE bir `disabled`a bağlı.

    DENETÇİ DELİĞİ (2026-08-25): bu çivinin ilk sürümü ikinci yarısını HİÇ ölçmüyordu.
    "Reddet" düğmesindeki `disabled` ile "EVET, GÖNDER" düğmesindeki kapı BİRLİKTE
    söküldüğünde suite 18/18 yeşil kalıyordu — çünkü ölçüm yalnız `gerekceYetersiz`
    İFADESİNİN dosyada var olduğuna bakıyordu, o ifadenin bir düğmeyi KİLİTLEDİĞİNE değil.
    """
    c = _kaynak(CEKMECE)
    assert re.search(r"const RET_MIN_GEREKCE\s*=\s*12", c), (
        "`RET_MIN_GEREKCE` sabiti yok ya da 12 değil — uç yasası (`loop.RET_MIN_GEREKCE`) ile ayrışır"
    )
    assert "en az {RET_MIN_GEREKCE} karakter" in c, (
        "eşik ekranda YAZILI değil — kullanıcı 400'ü ancak gönderdikten sonra öğrenirdi"
    )
    assert re.search(r"const gerekceYetersiz\s*=\s*gerekce\.trim\(\)\.length\s*<\s*RET_MIN_GEREKCE", c), (
        "eşik bayrağı `gerekce.trim().length < RET_MIN_GEREKCE` biçiminde kurulmamış — "
        "kısa gerekçe uca gidip 400 ile dönerdi"
    )
    # EŞİK BİR DÜĞMEYE BAĞLI OLMALI — ve iki düğmenin İKİSİNE de.
    for isaret, ad, niye in (
        ('setNiyet("reddet")', "birinci tık (Reddet…)",
         "kısa gerekçeyle niyet alınırsa ekran ikinci adıma geçer ve eşik ancak gönderimde öğrenilir"),
        ("void gonder(niyet)", "ikinci tık (EVET, GÖNDER)",
         "asıl gönderim kilitsiz kalır — 12 karakterin altındaki gerekçe uca gider ve 400 yer"),
    ):
        etiket = _tek_dugme_etiketi(c, isaret)
        assert re.search(r"disabled=\{[^}]*gerekceYetersiz", etiket), (
            f"{ad} düğmesinde `disabled={{… gerekceYetersiz …}}` YOK — {niye}"
        )


# ==================================================================================================
# 6 · HATA GÖVDESİ AYNEN, SESSİZLİK YOK
# ==================================================================================================

def test_hata_govdesi_aynen_gosteriliyor():
    c = _kaynak(CEKMECE)
    assert re.search(r"\{\s*hata\.detay", c), (
        "ucun `detail` metni ekrana basılmıyor — 400/409'un gerekçesi kaybolur"
    )
    assert "hata.kod" in c, "HTTP kodu gösterilmiyor — 0 (ağ) ile 409 (uç reddi) aynı görünürdü"


def test_olculemeyen_alan_sifir_ya_da_tire_ile_doldurulmuyor():
    """UYDURMA YASAĞI: ölçülemeyen alan `0` ya da `—` yazmaz; nedeniyle 'ölçülemedi' yazar."""
    c = _kaynak(CEKMECE)
    assert not re.search(r"\?\?\s*0\b", c), "ölçülemeyen alan `?? 0` ile dolduruluyor"
    assert not re.search(r'\?\?\s*"—"', c), "ölçülemeyen alan `?? \"—\"` ile dolduruluyor"
    assert c.count("neden=") >= 12, (
        "gövde alanlarının çoğu nedensiz — her ölçülemeyen alan NEDENİNİ taşımak zorunda"
    )


def test_planin_tam_govdesi_gosteriliyor():
    c = _kaynak(CEKMECE)
    # ETİKET METNİ 2026-08-26 SÖZLÜĞÜYLE GÜNCELLENDİ (docs/ARAYUZ-SOZLUGU.md):
    # "kapı"→"kontrol", "hüküm"→"karar", "silahlan"→"işleme hazırlan". Çivinin ölçtüğü
    # şey KELİME değil OLGU: "bu cümle ekranda YAZILI mı". Sözcük değişti, iddia aynı.
    for etiket in ("Kurulum", "Kontrol kararı", "Skor", "Sektör", "Giriş tetiği", "Stop", "Kâr hedefi",
                   "Kontrol gerekçeleri"):
        assert etiket in c, f"çekmecede `{etiket}` alanı yok — 'tam gövde' iddiası yalan olur"


# ==================================================================================================
# 7 · İYİMSER GÜNCELLEME YOK
# ==================================================================================================

def test_basarili_istekten_sonra_veri_yeniden_okunuyor():
    c = _kaynak(CEKMECE)
    son = c.rfind("krizPost(")
    assert son != -1, "hiç `krizPost` çağrısı yok"
    assert c.find("tazele()", son) != -1, (
        "gönderimden SONRA `tazele()` çağrılmıyor — ekran iyimser kalır, defter kıpırdadı mı bilinmez"
    )
    t = _kaynak(TABLO)
    assert "useBugun()" in t, "tablo paylaşılan nabzın tazeleyicisini almıyor"
    assert re.search(r"tazele=\{tazele\}", t), "tablo `tazele`yi çekmeceye geçirmiyor"


# ==================================================================================================
# 8 · ÇİFT ADIM
# ==================================================================================================

def test_karar_cift_adimli():
    """Tek tık icra tetiklemez: birinci tık NİYETİ alır, ikinci tık gönderir."""
    c = _kaynak(CEKMECE)
    assert re.search(r"const \[niyet, setNiyet\]", c), "niyet aşaması yok — karar tek tıkla giderdi"
    assert re.search(r"onClick=\{\(\)\s*=>\s*void gonder\(niyet\)\}", c), (
        "ikinci tık `gonder(niyet)` çağırmıyor — çift adım kurulmamış"
    )


# ==================================================================================================
# 9 · TANINMAYAN HÜKÜMDE EKRAN SUSMAZ
# ==================================================================================================

def test_taninmayan_hukumde_karar_bolumu_susmuyor():
    """GO/REVIEW/NO_GO dışında bir hüküm (ya da hiç hüküm) sessiz boş bir bölüm çizmemeli.

    `gate_verdict` yazılmamış bir plan defterde ölçüldü mü? HAYIR — ama tip onu opsiyonel
    tanımlıyor ve tablo sütunu bu yokluğu ZATEN çiziyor. Karar bölümünün o satırda üç dalın
    da tutmadığı için BOŞ kalması, operatöre "burada yapılacak bir şey yok" demenin sessiz
    hâli olurdu; oysa doğru cümle "hüküm okunamadı, karar yolu kapalı"dır.
    """
    c = _kaynak(CEKMECE)
    tanim = re.search(r"const hukumTanindi\s*=([^;]*);", c)
    assert tanim is not None, (
        "tanınan hüküm kümesi tanımlı değil — bilinmeyen hükümde bölüm sessizce boş kalır"
    )
    # KÜMENİN İÇİ ÖLÇÜLÜR, ADI DEĞİL: `const hukumTanindi = true` da bir tanımdır ve
    # dördüncü dalı tümden kapatır. Bu çivinin İLK sürümü tam bunu kaçırdı (mutasyon M22).
    g = tanim.group(1)
    for h in ('"GO"', '"REVIEW"', '"NO_GO"'):
        assert h in g, f"tanınan hüküm kümesi {h} hükmünü saymıyor: {g.strip()}"
    # ETİKET METNİ 2026-08-26 SÖZLÜĞÜYLE GÜNCELLENDİ (docs/ARAYUZ-SOZLUGU.md):
    # "kapı"→"kontrol", "hüküm"→"karar", "silahlan"→"işleme hazırlan". Çivinin ölçtüğü
    # şey KELİME değil OLGU: "bu cümle ekranda YAZILI mı". Sözcük değişti, iddia aynı.
    assert "Kontrol kararı okunamadı — karar yolu kapalı" in c, (
        "bilinmeyen hükmün cümlesi ekranda yazılı değil"
    )



# ==================================================================================================
# 10 · SATIR ÇAPASI YOK (çapa SEMBOLE atılır)
# ==================================================================================================

def test_bugun_yuzeyinde_dosya_satir_capasi_kalmadi():
    """`dosya.py:NNN` çapaları ilk düzenlemede bayatlar ve YANLIŞ yeri gösterir.

    ÖLÇÜLDÜ (2026-08-25; çapa-mezar-taşı): `PlanTablosu.tsx` içindeki `api.py:5841` çapası `drift_pct`
    yazımına işaret ettiğini iddia ediyordu; o satır artık `api_approvals` fonksiyonunun
    ilk satırı — yazım `_enrich_stale_plans`e taşınmış. Çapa YANLIŞ yere götürüyordu ve
    hiçbir şey ötmüyordu. Sembol adı taşındığında da doğru kalır; satır numarası kalmaz.

    ÖLÇÜM HAM METİNDE, SOYULMUŞTA DEĞİL: çapalar yorumda yaşar; soyulmuş metinde ölçmek
    hiçbir zaman ötmeyen bir çivi olurdu.
    """
    desenler = (
        re.compile(r"[A-Za-z_][A-Za-z0-9_]*\.py:\d+"),      # çapa-mezar-taşı: api.py:5841
        re.compile(r"sat[\u0131i]r\s+\d+"),                    # (satır 1611)
    )
    kusurlu: dict[str, list[str]] = {}
    dosyalar = sorted(p for p in BUGUN.iterdir() if p.suffix in (".ts", ".tsx"))
    assert dosyalar, "bugün yüzeyinde hiç kaynak dosya yok — ölçüm boşa koşuyor"
    for p in dosyalar:
        ham = p.read_text(encoding="utf-8")
        bulunan = [m.group(0) for d in desenler for m in d.finditer(ham)]
        if bulunan:
            kusurlu[p.name] = bulunan
    assert not kusurlu, (
        f"satır çapası kalmış (sembole çevrilmeli): {kusurlu}"
    )
