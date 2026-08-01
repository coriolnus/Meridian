"""v139 — PANO GÖRÜNÜM TURU: operatörün §3.0 bulgularının app.js tarafı.

Bu dosyanın ölçtüğü kusur sınıfı TEK: **panonun gördüğünü yanlış anlatması.** Üç biçimi var ve
üçü de canlıda görüldü:

  A) YANLIŞ-ETİKET  — bir sayı, BAŞKA bir sayının adıyla gösterilir (`inbox_count ?? pending_count`:
                      10 kurulan plan "10 bekleyen karar" diye okundu; canlı gerçek 0'dı).
  B) UYDURMA GEREKÇE — boş bir kart, ÖLÇÜLMEMİŞ bir sebep cümlesi yazar ("yeterli işlem birikince
                      çıkar" — oysa üreteç hiçbir üretim yolunda değildi, işlem birikse de çıkmazdı).
  C) SESSİZ YÜZEY   — arka uç alanı ÜRETİR, pano hiç okumaz (saglayicilar/ogrenme blokları; Faz-6
                      kilit zinciri merdiven kartında yoktu — "merdiven neden L0'da?" cevapsızdı).

Testler app.js KAYNAĞINA bakar (repo deseni: test_empty_gauge_honesty_v79) çünkü kusur da orada
yaşıyor: bir alanın API'de var olması onun PANODA okunduğu anlamına gelmez ve bu turun tamamı tam
olarak o boşluğun kapatılmasıdır. ÜRETİCİ/TÜKETİCİ PARİTESİ ayrıca zorlanır: Python bir kilit adı
ya da kova adı eklerse pano onu ham jetonla göstermesin diye iki taraf burada eşleşmeye zorlanır.
"""
from __future__ import annotations

import re
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent
APPJS = (SRC / "meridian" / "web" / "app.js").read_text()
HEALTH = (SRC / "meridian" / "health.py").read_text()
SKILLS = (SRC / "meridian" / "skills.py").read_text()
ANALYTICS = (SRC / "meridian" / "analytics.py").read_text()

# EMEKLİ METİN ARAMASI YORUM SATIRLARINI SAYMAZ: bu turun her düzeltmesi kaldırdığı yanlış cümleyi
# GEREKÇESİYLE birlikte yazıyor ("eski metin şuydu, neden yanlıştı"). O gerekçe kaynakta durmalı ama
# "hâlâ orada" diye okunmamalı — yoksa doğru davranan bir düzeltme kendi belgesi yüzünden düşer.
KOD = "\n".join(l for l in APPJS.splitlines() if not l.lstrip().startswith("//"))


# ---------------- 1) "BEKLEYEN KARAR" YANLIŞ-ETİKETİ ----------------
def test_inbox_count_pending_count_dususu_kalkti():
    """`inbox_count ?? pending_count` İKİ FARKLI GERÇEĞİ tek rozette birleştiriyordu. `inbox_count`
    senden İŞ isteyen kararların sayısıdır (api._inbox_count); `pending_count` o seans KURULAN
    PLAN sayısıdır (analytics.today: GO/REVIEW) ve kimseden bir şey istemez."""
    assert "today.inbox_count ?? today.pending_count" not in APPJS
    assert "(today.inbox_count ?? today.pending_count)" not in APPJS
    # Ölçülmemişlik ayrı bir hâl olarak taşınır: `null` = alan YOK, `0` = ölçüldü ve boş.
    assert "const inboxN = today.inbox_count == null ? null" in APPJS
    assert "const planN = today.pending_count == null ? null" in APPJS


def test_rozet_adlari_uc_ayri_sayiyi_uc_ayri_adla_soyler():
    """Rozetin ADI sayının NEYİ saydığını söylemek zorunda: dolgulu rozet YALNIZ ölçülmüş
    gelen kutusudur; ölçülmemişlikte rozet düşer ama adı da değişir."""
    assert 'ROZET_TR = { inbox: "bekleyen karar", plan: "kurulan plan", aday: "aday" }' in APPJS
    # Şerit özeti "bekleyen karar" cümlesini YALNIZ inbox dalında kurabilsin; ölçülmemişlikte
    # cümlenin kendisi değişir (sayı aynı kalsa bile).
    assert 'rozet === "inbox" ? `${inboxN} bekleyen karar`' in APPJS
    assert 'rozet === "plan" ? `${planN} kurulan plan · gelen kutusu ölçülmedi`' in APPJS


def test_dolgulu_rozet_yalniz_gercek_inbox_ile():
    assert 'const dolgulu = id === "adaylar" && rozet === "inbox"' in APPJS
    assert "class=\"pillc${dolgulu ? '' : ' q'}\"" in APPJS


# ---------------- 2) ARAÇ KÜTÜPHANESİ FİLTRESİ ----------------
def test_varsayilan_gorunum_yalniz_aktif_araclar():
    """Operatör panoda 67 skill görüyordu; kayıtta emeklilik damgası ZATEN vardı (`retired`,
    `merged_into`), panoda filtre yoktu. Kategori kartları artık YALNIZ aktiflerden kurulur."""
    assert "const aktif = tumu.filter(([, i]) => i.enabled)" in APPJS
    assert "const emekli = tumu.filter(([, i]) => !i.enabled)" in APPJS
    assert "aktif.forEach(([n, i]) => (byCat[" in APPJS


def test_emekli_raf_uc_hali_ayri_sayar_ve_gerekcesini_tasir():
    """"37 kapalı" tek sayıya katlanırsa "37'si anahtar bekliyor" diye okunur — oysa 36'sı emekli,
    biri stil dışı. Üç hâl AYRI sayılır ve her satır kendi `reason`unu taşır."""
    assert "const birlesenN = emekli.filter(([, i]) => i.merged_into).length" in APPJS
    assert "const emekliN = emekli.filter(([, i]) => i.retired && !i.merged_into).length" in APPJS
    assert "const kapaliN = emekli.length - birlesenN - emekliN" in APPJS
    assert "emekli / birleştirilmiş (${emekli.length})" in APPJS
    assert "birleşti · ${emekliN} emekli · ${kapaliN} kapalı" in APPJS
    assert "esc(i.merged_into)" in APPJS
    assert 'esc(i.reason || "gerekçe kaydedilmemiş")' in APPJS


def test_kategorisiz_kayit_undefined_adli_bolum_uretmez():
    """`pullback-screener` kaydında `category` yok — eski kod "undefined (1)" başlıklı bir bölüm
    çiziyordu. Eksik alan bir bölüm adı değildir."""
    assert 'i.category || "sınıfsız"' in APPJS


# ---------------- 3) BOŞ KARTLAR KENDİNİ AÇIKLAR ----------------
def test_karne_sayaclari_sifirken_gerekcesini_olcumden_turetir():
    """Sabit alt yazı ("gate'i geçen değişiklik") sayı 0 iken bir TANIM'dır, CEVAP değil.
    Alt yazı artık karnenin KENDİ alanlarından türer (status_counts, besleme, min_sample)."""
    assert "function karneAlt(L)" in APPJS
    assert "const sc = L.status_counts || {}" in APPJS
    assert "hiç ship yok — terfi ancak yayınlanmış bir sürümde ölçülür" in APPJS
    assert "hipotezin hiçbiri kapıyı geçmedi" in APPJS
    # sayaç doluyken tanım geri gelir (gürültü yaratmasın)
    assert 'L.shipped ? "gate\'i geçen değişiklik"' in APPJS


def test_beceri_onerisi_bos_karti_uydurma_vaat_etmez():
    """ESKİ METİN: "yeterli işlem birikince çıkar" — bu bir VAATTİ ve YANLIŞTI: üreteç hiçbir
    üretim yolunda değildi, işlem birikse de öneri çıkmazdı. Cümle artık ÖLÇÜMDEN gelir."""
    assert "yeterli işlem birikince çıkar" not in KOD
    assert "function eksen2Bos(eksen2, olcumVar)" in APPJS
    # üç hâl ayrı: ölçülemedi / hiç koşmadı / koştu-ama-eşik geçilmedi
    assert "Üretecin durumu ÖLÇÜLEMEDİ" in APPJS
    assert "Eksen-2 kadansı HİÇ koşmamış" in APPJS
    assert "eksen2.uretilen ?? 0} öneri üretti" in APPJS


def test_eksen2_kova_adlarinin_uretici_tuketici_paritesi():
    """ÜRETİCİ/TÜKETİCİ PARİTESİ (v79 dersi): skills.axis2_diagnosis bir kova adı yazar, app.js onu
    cümleye çevirir. Biri yeni kova eklerse öteki ham jeton gösterir ve "sebep" yeniden okunamaz
    hâle gelir. Panonun sözlüğü üreticinin ürettiği HER kovayı tanımalıdır."""
    blok = APPJS[APPJS.index("const KOVA_TR = {"):]
    blok = blok[:blok.index("\n};")]
    bilinen = set(re.findall(r"^\s*([a-z0-9_]+):", blok, re.M))
    assert bilinen, "pano kova sözlüğü boş"

    # Üretici adları iki parçadan kurulur: taban kova + "_cf_destekli" son eki (axis2_diagnosis).
    taban = set(re.findall(r'k = "([a-z0-9_]+)"', SKILLS))
    taban |= set(re.findall(r'k = \("([a-z0-9_]+)"', SKILLS))
    taban |= set(re.findall(r'else "([a-z0-9_]+)"\)', SKILLS))
    taban |= set(re.findall(r'"([a-z0-9_]+)" if \(s\["enabled"\]', SKILLS))
    taban |= set(re.findall(r'k = "([a-z0-9_]+)" if', SKILLS))
    assert taban, "üretici kova adları okunamadı — ayıklama deseni bozuldu"
    eksik = {t for t in taban if t not in bilinen}
    assert not eksik, f"pano bu kovaları tanımıyor (ham jeton gösterir): {sorted(eksik)}"


# ---------------- 4) OTONOMİ MERDİVENİ "NEDEN" ----------------
def test_merdiven_karti_faz6_kilit_zincirini_gosterir():
    """"Merdiven neden L0'da?" sorusunun cevabı panoda HİÇ yoktu. İKİ AYRI KAPI var ve
    karıştırılmaları yanılsamayı üretiyor: L0→L1 ölçütleri (guard.py) kâğıt provanın karnesidir,
    FAZ-6 beş kilidi ise gerçek-para/silahlanma ön koşuludur ve fail-closed'dır."""
    assert "function faz6Satiri(f)" in APPJS
    assert "ladderCard(L, faz6)" in APPJS
    assert "${faz6Satiri(faz6)}" in APPJS
    assert "((dg || {}).mlops || {}).faz6_kilitleri" in APPJS
    assert "fail-closed" in APPJS


def test_faz6_kilit_adlari_health_ile_eslesir():
    """`health.FAZ6_KILITLERI` beş adı TEK yerde tanımlar. Pano sözlüğü eksik kalırsa kilit adı
    ham jetonla ("dsr_gecer") görünür; fazla kalırsa olmayan bir kilit için metin taşır."""
    uretilen = set(re.findall(r'"([a-z0-9_]+)"',
                              HEALTH[HEALTH.index("FAZ6_KILITLERI = ("):HEALTH.index("FAZ6_KILITLERI = (") + 200]))
    assert uretilen, "health.FAZ6_KILITLERI okunamadı"
    blok = APPJS[APPJS.index("const FAZ6_TR = {"):]
    blok = blok[:blok.index("};")]
    bilinen = set(re.findall(r"([a-z0-9_]+):", blok))
    assert uretilen == bilinen, f"kilit sözlüğü ayrıştı: eksik={sorted(uretilen - bilinen)} fazla={sorted(bilinen - uretilen)}"


# ---------------- 5) KARAR AĞACI HÜCRE DETAYI ----------------
def test_karar_agaci_satiri_basilabilir_ve_kaydi_acar():
    """Zincir çipleri kapının ÖZETİdir; hangi ölçüt hangi değerle hangi eşiğe çarptı `gk.plans`
    paketinde ZATEN vardı ve hiçbir yüzeyde okunmuyordu. YENİ UÇ İCAT EDİLMEDİ."""
    assert 'const k = rec("gate", pln)' in APPJS
    assert "Karar ağacını aç" in APPJS
    assert "  gate(p) {" in APPJS
    # çekmece YALNIZ paketteki alanlardan kurulur
    for alan in ("p.setup", "p.score", "p.llm_opinion", "p.llm_veto", "p.reasons", "p.checks"):
        assert alan in APPJS, f"karar ağacı çekmecesi {alan} alanını okumuyor"


def test_karar_agaci_cekmecesi_eksik_kaydi_uydurmaz():
    assert "yapılandırılmış karar ağacı kaydı yok" in APPJS


# ---------------- 6) MUTABAKAT MASASI — GÖNDERİM OLAYLARI ----------------
def test_basarisiz_gonderimin_uc_hali_yuzeyde():
    """Kalıcı ret defteri (`failed_submissions`) YALNIZ brokerin geri çevirdiği emri taşır.
    `alpaca_submit_unreachable` (ağ) ve `alpaca_submit_failed` (istisna) o deftere HİÇ girmez —
    plan silahlı kalır ve masa "ret yok" der. Üçü de olay halkasından okunur."""
    assert 'j("/api/events").catch(() => null)' in APPJS
    for jeton in ("alpaca_submit_unreachable", "alpaca_submit_failed"):
        assert jeton in APPJS, f"{jeton} panoda okunmuyor"
    assert 'if (n === "alpaca_submit") return e.ok === false;' in APPJS


def test_olay_halkasinin_sinirini_beyan_eder():
    """Halka son 80 kayıtla sınırlıdır (obs.recent) — BOŞLUK KANIT DEĞİLDİR ve bu cümle yazılı
    olmazsa "başarısız gönderim yok" bir güvence gibi okunur."""
    assert "Halka son ${n80} olay" in APPJS
    assert "daha eski bir arıza bu pencerede görünmez" in APPJS


# ---------------- 7) SAĞLAYICI SAĞLIK KARTI ----------------
def test_saglayici_karti_bagli_ve_beyanini_tasir():
    assert "d.saglayicilar || null" in APPJS
    assert "Sağlayıcı sağlığı" in APPJS
    # ok üç değerlidir: true/false/null. null "çağrı yok"tur — ne yeşil ne kırmızı.
    assert '["çağrı yok", "t-vi"]' in APPJS
    assert "p.olculemedi" in APPJS
    assert "esc(blok.beyan" in APPJS


# ---------------- 8) ÖĞRENME BESLEME KARTI ----------------
def test_ogrenme_besleme_karti_dort_bloguyla_bagli():
    """/api/diagnostics `ogrenme` bloğu (antrenman · dolgu · eksen2 · nabız) öğrenme-otomasyonu
    turunda eklendi, tüketicisi yoktu."""
    assert "const o = d.ogrenme || null" in APPJS
    assert "Öğrenme beslemesi" in APPJS
    for alan in ("o.nabiz", "o.antrenman", "o.dolgu_kuyrugu", "o.eksen2", "o.son_kosu", "o.bekci_notu"):
        assert alan in APPJS, f"öğrenme besleme kartı {alan} okumuyor"


def test_nabiz_uc_degerli_okunur():
    """`hic_kosmadi` ile `bayat` AYRI hâllerdir: biri "kadans hiç koşmadı", öteki "koştu ama
    penceresi geçti". Tek etikete katlanırsa duruş taze görünür."""
    assert 'v.hic_kosmadi ? ["HİÇ KOŞMADI", "t-no"]' in APPJS
    assert 'v.bayat ? ["BAYAT", "t-rv"] : ["taze", "t-go"]' in APPJS


# ---------------- 9) SESSİZ YÜZEY, İKİNCİ DALGA (mikro-tur 2026-08-01) ----------------
# Kusur sınıfı yukarıdaki (C) ile AYNI: arka uç alanı ÜRETİR, pano hiç okumaz. Üç alan
# /api/diagnostics'te ZATEN vardı ve app.js'te tek bir okuma satırı yoktu — yani üçü de
# "yazılıyor ama kimse okumuyor" idi.
def test_tavan_durumu_sonuc_karnesinde_okunuyor():
    """`result_verdict.tavan_durumu` (← analytics.live_expectancy_ceiling) SONUÇ hükmü kartında.
    Canlı beklenti süspansiyon eşiğinin altına düşse panoda hiçbir şey değişmiyordu."""
    assert "rv.tavan_durumu" in APPJS
    assert "Canlı-beklenti tavanı" in APPJS
    # KOLON ≠ ÖLÇÜT: payda 4'te kalır ve satır bunu KENDİSİ söyler (rozet + açıklama).
    assert '_chip("HÜKME GİRMEZ", "t-rv")' in APPJS
    assert "bir ölçüt değil bir KOLONdur" in APPJS
    # Sunucunun kendi gerekçe cümlesi ekrana çıkar — pano ikinci bir hüküm metni YAZMAZ.
    assert "esc(tv.hukum" in APPJS


def test_tavan_durum_adlarinin_uretici_tuketici_paritesi():
    """ÜRETİCİ/TÜKETİCİ PARİTESİ (v79 dersi, FAZ6_KILITLERI ile aynı desen):
    `analytics.LIVE_CEILING_DURUMLAR` dört durumu TEK yerde tanımlar. Pano sözlüğü eksik kalırsa
    durum ham jetonla ("suspansiyon_degerlendirmesi") görünür; fazla kalırsa olmayan bir hâl için
    metin ve TON taşır — ve ton bu kartta bir uyarı sinyalidir."""
    i = ANALYTICS.index("LIVE_CEILING_DURUMLAR = (")
    uretilen = set(re.findall(r'"([a-z0-9_]+)"', ANALYTICS[i:i + 200]))
    assert uretilen, "analytics.LIVE_CEILING_DURUMLAR okunamadı"
    for sozluk in ("const TAVAN_TR = {", "const TAVAN_TON = {"):
        blok = APPJS[APPJS.index(sozluk):]
        blok = blok[:blok.index("};")]
        bilinen = set(re.findall(r"([a-z0-9_]+):", blok))
        assert uretilen == bilinen, \
            f"{sozluk} ayrıştı: eksik={sorted(uretilen - bilinen)} fazla={sorted(bilinen - uretilen)}"


def test_tavan_altinda_YESIL_boyanmaz():
    """TON KURALI: `tavan_altinda` sunucunun kendi cümlesiyle "iyi haber değil, kuralın BEKLEDİĞİ
    hâl"dir. Yeşile boyamak normal hâli bir başarı ilanına çevirirdi. `tavan_ustunde` ise bir
    başarı gibi GÖRÜNDÜĞÜ hâlde şüphe işaretidir ve süspansiyonla aynı uyarı tonunu alır."""
    blok = APPJS[APPJS.index("const TAVAN_TON = {"):]
    blok = blok[:blok.index("};")]
    assert '"pos"' not in blok, "tavan kolonunda yeşil ton var — normal hâl kutlanıyor"
    assert 'tavan_altinda: ""' in blok
    assert 'tavan_ustunde: "warn"' in blok and 'suspansiyon_degerlendirmesi: "warn"' in blok
    assert 'olculemedi: "mut"' in blok


def test_eb_sutunu_bilesen_ic_tablosunda_okunuyor():
    """2C `eb` bloğu: hücrede ham sayının ALTINDA sönük ikiz + tablo altında özet. Özet DIŞ
    okuyucudan (`shrunk_component_ic.tablo_ici_eb`) gelir — YASA 6."""
    assert "(cic.eb || {}).katmanlar" in APPJS and "const ebKatman = lay =>" in APPJS
    assert "`${c}@${h}`" in APPJS, "hücre anahtarı (bileşen@ufuk) kurulmuyor"
    assert "(ml.shrunk_component_ic || {}).tablo_ici_eb" in APPJS
    assert "${ebOzet}" in APPJS, "EB özeti tabloya eklenmemiş — tanımlı ama ölü"


def test_eb_blogu_yokken_UYDURMA_sifir_kucultme_demez():
    """"Blok yok"u "0 küçültme" diye raporlamak uydurma olurdu (analytics._tablo_ici_eb_ozeti'nin
    kendi gerekçesi). Pano da aynı ayrımı yapar ve sebebi dosyanın YAŞI olarak söyler."""
    assert "henüz üretilmedi" in APPJS
    assert "ölçülmemiş bir küçültmeyi 0 diye raporlamak uydurma olurdu" in APPJS
    # ham `ic` alanlarının değişmediği ekranda da yazılı — okur EB'yi yeni gerçek sanmasın
    assert "bit-bit değişmedi" in APPJS


def test_trend_kitabi_karti_bagli_ve_serh_METIN_olarak_gorunur():
    """TASARIM İLKESİ: şerh rakamdan ayrılamaz. `pit_serh` kitabın içinde taşınıyor ve panoda
    rakamlarla AYNI kartta METİN olarak çıkar — tooltip/çekmece değil."""
    assert "d.trend_kitabi" in APPJS
    assert "Trend kolu · canlı gölge-kitap" in APPJS
    assert "esc(tk.pit_serh)" in APPJS
    assert "PIT ŞERHİ (rakamdan ayrılamaz)" in APPJS
    for alan in ("tk.pozisyon", "tk.equity", "tk.nakit", "tk.kapanan", "tk.last_session"):
        assert alan in APPJS, f"trend kitabı kartı {alan} okumuyor"


def test_trend_kitabi_dogmamis_defter_ile_bos_defteri_AYIRIR():
    """"pozisyon 0" ile "defter yok" AYNI cümle değildir: kitap GEÇMİŞSİZ doğar ve ilk giriş ilk
    ay-sonundadır. İkisini tek boş karta katlamak, dürüst bir başlangıcı arıza gibi gösterirdi."""
    assert "if (!tk.var) return" in APPJS
    assert '_chip("DOĞMADI", "t-vi")' in APPJS
    assert "ilk giriş ilk AY-SONUNDA olur" in APPJS
    # Şerhin DÜŞMESİ bir görüntü kusuru değil defter kırılmasıdır — ayrı ve sert cümle.
    assert "PIT ŞERHİ DEFTERDEN DÜŞMÜŞ" in APPJS


# ---------------- ÇAPRAZ: UYDURMA METİN YASAĞI ----------------
def test_operasyon_altbasligi_sabit_panel_sayisi_iddia_etmez():
    """"Altı panel + üç kart" sayısı kartlar eklendikçe sessizce yalan oluyordu — panoda sabit
    yazılmış her sayı, bir sonraki turda uydurma metne dönüşen bir borçtur."""
    assert "Altı panel + üç kenar/öğrenme kartı" not in APPJS


def test_arac_kutuphanesi_basligi_sabit_sayi_yazmaz():
    """Başlık sayıyı API sayacından alır (`c.enabled`), gövdeye elle yazılmaz."""
    assert "${c.enabled ?? \"—\"} AKTİF ARAÇ" in APPJS
    assert not re.search(r"(?<!\$\{)\b(30|37|67) ARAÇ\b", APPJS)
