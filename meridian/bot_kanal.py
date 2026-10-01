"""bot_kanal.py — konuşan bot filosunun ORTAK GİRİŞ NOKTASI: `bota_sor(bot, mesaj, kanal, oturum) -> str`
(spec docs/superpowers/specs/2026-09-29-konusan-bot-filosu-design.md §3.4, §3.5, §3.7, §4).

NE YAPAR. Üç kanal (Telegram dinleyicisi, pano, Claude uygulaması) bir bota soruyu YALNIZ buradan
sorar. Sıra DONUKTUR: (1) kanal `KANALLAR` içinde mi; (2) bot kadroda VE `aktif` mi
(`kadro.bot_bul`); (3) komut öneki mi (`hatırla:` · `unut:` · `onayla:` · `geri al:` — `KOMUTLAR`) — öyleyse
MODELE GİTMEZ, deterministik işlenir;
(4) bot başına UTC günlük kota (kadro satırının `gunluk_tavan` alanı; `None` = tavan yok ama SAYILIR);
(5) taşıyıcı çağrısı (`Tasiyici` protokolü; varsayılan `HermesTasiyici` = Hermes api_server) — modele giden metin
`notify.scrub`'lı; (6) araçsız-veri uyarısı (aşağıda); (7) sohbet dönüşünün hafıza kaydı (`Hafiza.donus_yaz`;
varsayılan `bot_hafiza.HindsightHafiza`); (8) her dönüş `state/bot_sohbet.jsonl` defterine bir satır.

DEĞİŞMEZLER.
  * GEÇERSİZ GİRDİ SESSİZ VARSAYILANA DÜŞMEZ: bilinmeyen kanal, kadroda olmayan ya da `aktif`
    olmayan bot → `ValueError`. Saat dilimsiz `simdi` de `ValueError` — kota günü UTC'dir ve
    dilimsiz bir an yerel saat sanılıp günü sessizce kaydırırdı.
  * KOMUTLAR (Türkçe harf katlamalı, büyük/küçük harf duyarsız — `kadro.ad_katla`; iki kelimeli `geri al` `_` ile
    `geri_al` olur) modele GİTMEZ. `hatırla` gövdesi `notify.scrub`'dan geçip `Hafiza.yaz`a gider (etiket
    `sabit_not`, `bot:<ad>`, `kanal:<kanal>`). Gövdesiz komut hafızaya GİTMEZ ("neyi?" diye sorulur) — boş sorgu
    rastgele bellek döndürürdü. Hafıza istisnası "YAZILAMADI"/"ARANAMADI"/"UNUTULAMADI"/"GERİ ALINAMADI" + olay olur
    (olaylar kapalı-küme `neden` taşır, `bot_hafiza.hata_nedeni`), sohbet hatasına dönmez. Kalıcı silme bu modülde
    YOK. Tespitin TEK kaynağı `komut_oneki`dir; Telegram dinleyicisi de onu çağırır (yanıt kipinde komut, VERİ çitinin
    arkasında kaybolmasın diye çit kurulmadan ÖNCE — Tur 2, inceleme I-1).
  * `unut:` İKİ ADIMLIDIR (Parça 1b G4 Görev 2; plan Review Focus 2). İLK ADIM HİÇBİR ŞEYİ DEĞİŞTİRMEZ: scrub'lı gövde
    `Hafiza.unut_adaylari`na (salt-okur recall) gider, en fazla `bot_hafiza.UNUT_TAVANI` aday kısa listeyle ve 6 hex
    kısa KODLA operatöre söylenir; aday kaydı `UNUT_BEKLEYEN`e `bekliyor` olarak yazılır (ömür `UNUT_ONAY_OMRU`).
    `onayla: unut <kod>` YALNIZ kodu üreten AYNI bot, `bekliyor` durumu ve süre içinde geçer — aksi hâlde ret +
    `bot_unut_onay_reddi` (`neden` ∈ `bilinmeyen_kod` · `baska_bot` · `suresi_doldu` · `zaten_uygulandi` ·
    `zaten_geri_alindi`); geçerse
    `Hafiza.unut_uygula` adayları GERİ ALINABİLİR biçimde emekliye ayırır (`state: invalidated`) ve kayıt `uygulandi`
    olur. `geri al: <kod>` YALNIZ aynı bot + `uygulandi` → denenen kimliklere `Hafiza.geri_al` (`state: valid`) →
    `geri_alindi` (ret `bot_unut_geri_al_reddi`: `bilinmeyen_kod` · `baska_bot` · `uygulanmadi` ·
    `zaten_geri_alindi`). Durum geçişleri kilit altında TEK işlemdir (talep ÖNCE, istek SONRA — çift onay iki kez
    PATCH atamaz); kayıt SİLİNMEZ, durumu değişir. Kısmi PATCH hatasında `unutulan_idler`/`denenen`/`kalan` deftere
    girer (`denenen` hata vereni de taşır: zaman aşımına uğrayan PATCH sunucuda uygulanmış olabilir); hiçbir istek
    atılmadıysa kod `bekliyor`a döner (yeniden denenebilir). Tur 2 (görev incelemesi, Rol-1 2026-09-30): BOT BAŞINA
    TEK CANLI KOD — yeni aday listesi verilirken aynı botun `bekliyor` kaydı aynı kilitli yazımda `suresi_doldu` olur
    (`yerine_gecen` alanı yeni kodu gösterir; kayıt silinmez). SÜRE DENETİMİ FAIL-CLOSED: `ts`/`son`u okunamayan
    `bekliyor` kaydı `suresi_doldu` sayılır. Bilinmeyen kod cevabı kodun yanlış yazılmış ya da budanmış
    (`UNUT_BEKLEYEN_SAKLAMA`dan eski) olabileceğini söyler.
  * KOTA SESSİZ DEĞİL: tavan doluysa bot "bugünlük kotam doldu (n/tavan)" der, taşıyıcı ÇAĞRILMAZ,
    defter `tur: kota_doldu` satırı alır. Sayım defterin `tur == "sohbet"` satırlarından
    (`gunluk_sayim`); tavan sayısı Parça 0 (g) ölçümünden gelir — burada UYDURULMAZ.
  * TAŞIYICI HATASI YUTULMAZ: defter `tur: hata` + sınıf adı, istisna YUKARI fırlar (Telegram
    dinleyicisi `bot_sohbet_hatasi` yolunda yakalar ve operatöre sınıf adıyla söyler).
  * HAFIZA ÜRETİMDE BAĞLIDIR (Parça 1b G4 Görev 1): `hafiza` verilmezse `bot_hafiza.HindsightHafiza()` kurulur —
    "bağlı olmayan hafıza" dalı YOKTUR. Credential yoksa hafıza işlemi HTTP'den ÖNCE `anahtar_yok` ile düşer ve
    aşağıdaki hata yolları bunu operatöre/deftere SÖYLER (sessiz kalınmaz). Testler sahtelerini AÇIKÇA verir.
  * DÖNÜŞ KAYDI (spec §3.4, 2026-09-30 düzeltmesi: Hermes `auto_retain` KAPALI, dönüşü YALNIZ bu katman yazar):
    başarılı her `tur: sohbet` turu `Hafiza.donus_yaz(bot, scrub(operatör sözleri), scrub(cevap), etiketler)` çağırır —
    Telegram yanıt kipinde yanıtlanan metnin VERİ çiti hafızaya GİTMEZ, yerine `(yanıt: <ilk İÇERİK satırı>)` kaynak
    etiketi (`_hafiza_mesaji`; sohbet imzası ve araçsız-veri uyarısı içerik sayılmaz — tek kural
    `alinti_icerik_satiri`; modele giden metin alıntıyı TAŞIR); `cevap` operatörün gördüğü ÖNEKLİ metindir (araçsız-veri
    uyarısı hafızada da kalır); etiketler `bot:<ad>`, `kanal:<kanal>`, `DONUS_ETIKETI` + `arac_siz_veri is True`
    ise `arac_siz_veri`, sayı ölçülemediyse `arac_olculemedi`. Defter sohbet satırı: `hafiza_durumu: kabul_edildi`
    (async KABUL — bankaya işlendi DEĞİL), `hafiza_islem_kimligi`, `hafiza_sure_s`. HAFIZA CEVABI DÜŞÜRMEZ: istisna →
    `hafiza_durumu: yazilamadi` + `bot_hafiza_donus_hatasi` olayı (`sinif` + kapalı-küme `neden`,
    `bot_hafiza.hata_nedeni`; sonuç `kabul`/`islem_kimligi` taşımıyorsa da bu yol); `success: false` → `yazilamadi` +
    `bot_hafiza_donus_yazilamadi`. Kota/hata turunda dönüş YAZILMAZ (`hafiza_durumu: atlandi`); komut turları kendi
    `hafiza_durumu`nu taşır. Kayıt SENKRONDUR ama retain `async: true`dur (Hindsight çıkarımı arka planda);
    Hindsight asılırsa cevabın gecikmesi soket İŞLEMİ başına `bot_hafiza.DONUS_ZAMAN_ASIMI_S` ile sınırlıdır
    (bağlanma + okuma; duvar saati değil) — cevap düşmez.
  * DEFTER YAZIMI CEVABI DÜŞÜRMEZ: `store.append_jsonl` düşerse `bot_defter_yazim_hatasi` olayı
    (sinyalli) — operatörün cevabı yine döner.
  * SIR MODELE/HAFIZAYA/DEFTERE/İSTİSNAYA DÜŞMEZ: taşıyıcıya giden `mesaj` `notify.scrub`'lıdır (Rol-1 hükmü, plan
    2026-09-30 G4: operatörün yapıştırdığı sır DIŞ MODELE gitmez); dönüş kaydı da scrub'lı parçalar alır. Defterdeki
    `mesaj`/`cevap` `notify.scrub`'dan ÖNCE geçer, SONRA
    `cevap` `CEVAP_TAVANI`na kesilir (ters sıra yarım kesilmiş bir anahtarı desenin dışına itip
    sızdırırdı); `kesildi` alanı her satırda. `API_SERVER_KEY` yalnız `Authorization` başlığındadır;
    HTTP hatası yalnız DURUM KODUYLA `RuntimeError`a çevrilir, zincir bastırılır (`from None`).
  * ARAÇSIZ VERİ İŞARETLENİR, MODELE GÜVENİLMEZ (Parça 0 EN AĞIR BULGU, 2026-09-29: araç katmanı bağlı
    olmayan bot bir araç çağrısı VE sonucunu uydurup gerçek veri gibi sundu; oturumda `tool_calls` yoktu).
    Taşıyıcı bu turun GERÇEK araç SONUCU sayısını (hizalı oturum dökümünden) `TasiyiciSonuc.arac_cagrilari`na
    koyar; sayı 0 iken cevap veri taşıyorsa (`veri_isareti`, defter `veri_isareti` alanı hangi işaretin
    eşleştiğini yazar) `UYARI_ARACSIZ` öneki + defter `arac_siz_veri: true`; sayı ÖLÇÜLEMEDİYSE
    (`None`) `UYARI_OLCULEMEDI` öneki + `arac_olculemedi: true` ve `arac_siz_veri: None` (0 ile "bilmiyorum"
    aynı şey değildir — uydurma yasağı). Önek cevap zaten onunla başlıyorsa eklenmez; defterdeki `cevap`
    operatörün gördüğü (önekli) metindir. Uyarı taşıyıcıdan BAĞIMSIZ burada uygulanır.

YASA 6 — OKUYUCU BEYANI. `bot_sohbet.jsonl`in bugünkü tek okuyucusu bu modülün kendi
`gunluk_sayim`idir (kota); aynı modül olduğu için statik graf dış tüketiciyi göremez. Planlı
okuyucular (@ayna, @butce, pano bot sayacı, EDG ölçüm kartı) Parça 1 dağıtımında gelir — beyan
`codelaw.DECLARED_SINKS`te gerekçesiyle durur. `bot_unut_bekleyen.json` (`UNUT_BEKLEYEN`) bu modülün KENDİ işletim
durumudur: yazan ve okuyan `_bekleyen_ekle` / `_gecis_talebi` / `_bekleyen_guncelle` (hepsi `store.update_json`
kilitli oku-değiştir-yaz) — beyanı aynı yerde. Durum dosyasıdır, defter değil: 7 günden eski
SONUÇLANMIŞ kayıt yazımda budanır (`UNUT_BEKLEYEN_SAKLAMA`; bedel: o kod artık `geri al` ile bulunamaz — tam iz
`bot_sohbet.jsonl`dedir). Dönüş kaydının okuyucuları Hindsight tarafındadır (sohbet
profillerinin `auto_recall`u, `bot_hafizasi_ara`) — `bot_hafiza` modül başlığı.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import secrets as _std_secrets
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Protocol

from . import bot_hafiza, kadro as _kadro, notify, obs, secrets, skill_gorus_llm, store

KANALLAR = ("telegram", "pano", "claude")
DEFTER = "bot_sohbet.jsonl"
CEVAP_TAVANI = 4000
#: Komut öneki: BİR ya da İKİ kelime (yalnız harf; kelimeler arası boşluk/sekme — satır sonu DEĞİL) + isteğe bağlı
#: boşluk + `:`. Kelimeler `kadro.ad_katla` ile katlanıp `_` ile birleşir (`Geri Al` → `geri_al`) ve `KOMUTLAR` ile
#: kıyaslanır — GÖVDE katlanmaz (not operatörün yazdığı gibi kalır).
_KOMUT = re.compile(r"^([^\W\d_]+(?:[ \t]+[^\W\d_]+)?)\s*:(.*)$", re.S)
#: Deterministik komutlar (katlanmış ad). Tespit YALNIZ `komut_oneki`de (G4 Görev 2: `onayla`, `geri_al`).
KOMUTLAR = ("hatirla", "unut", "onayla", "geri_al")
_HATIRLA_BOS = "Neyi hatırlayayım? `hatırla: <not>` biçiminde yaz."
_HAFIZA_YAZILAMADI = "Not YAZILAMADI (hafıza hatası), kayda geçti."
_UNUT_BOS = "Neyi unutayım? `unut: <ifade>` biçiminde yaz."
_UNUT_ESLESME_YOK = "Eşleşen bir not bulamadım; hiçbir şey unutulmadı."
#: İlk adım salt-okurdur: burada "hiçbir şey unutulmadı" DOĞRUDUR (PATCH atılmadı).
_UNUT_ARANAMADI = "Unutulacak not ARANAMADI (hafıza hatası); hiçbir şey unutulmadı, kayda geçti."
_UNUT_KAYDEDILEMEDI = "Aday listesi KAYDEDİLEMEDİ; hiçbir şey unutulmadı, kayda geçti."
_ONAY_BOS = "Neyi onaylayayım? `onayla: unut <kod>` biçiminde yaz."
_GERI_AL_BOS = "Neyi geri alayım? `geri al: <kod>` biçiminde yaz."
#: Talep kilit altında düştü: hiçbir PATCH atılmadı.
_BEKLEYEN_OKUNAMADI = "Bekleyen unutma kaydı OKUNAMADI; hiçbir şey değişmedi, kayda geçti."
#: "hiçbir şey unutulmadı" DENMEZ: zaman aşımına uğrayan bir PATCH sunucuda yine de uygulanmış olabilir.
_UNUTULAMADI = "UNUTULAMADI (hafıza hatası), kayda geçti."
_GERI_ALINAMADI = "GERİ ALINAMADI (hafıza hatası), kayda geçti."
#: `unut:` iki adımının bekleyen aday kaydı (Rol-1 kararı 1, 2026-09-30) — ALANLARIN TEK TAM LİSTESİ burasıdır
#: (`codelaw.DECLARED_SINKS` gerekçesi buraya gösterir; ayrışma çivisi v608 alanları koddan ölçer):
#: `{kod: {bot, idler, kesitler, ifade, ts, son, durum}}`; aynı botun yeni aday listesi `bekliyor` kaydı düşürünce o
#: kayda `yerine_gecen` (yeni kod); onaydan sonra `unutulan_idler`/`denenen`/`kalan`; `geri al` denendikten sonra
#: `geri_alinan_idler`. Yazım `store.update_json` (kilitli, atomik).
UNUT_BEKLEYEN = "bot_unut_bekleyen.json"
#: Kısa kodun ömrü: `onayla: unut <kod>` bu süre içinde gelmezse kayıt `suresi_doldu` olur.
UNUT_ONAY_OMRU = timedelta(minutes=15)
#: SONUÇLANMIŞ kaydın saklama süresi (`ts`ten); daha eskisi yazımda budanır (modül başlığı, YASA 6).
UNUT_BEKLEYEN_SAKLAMA = timedelta(days=7)
#: Kayıt durumları (DONUK): `bekliyor` → `uygulandi` → `geri_alindi`; `bekliyor` → `suresi_doldu`. İlki dışındakiler
#: SONUÇLANMIŞTIR (budanabilir); `uygulandi` → `geri_alindi` dışında sonuçlanmış kayıt geçiş yapmaz.
UNUT_DURUMLARI = ("bekliyor", "uygulandi", "geri_alindi", "suresi_doldu")
_SONUCLANMIS = UNUT_DURUMLARI[1:]
_KOD_DESENI = re.compile(r"[0-9a-f]{6}")
#: Kod çakışmasında yeniden üretim hakkı (16,7 milyon kod, en çok yedi günlük kayıt).
_KOD_DENEME = 8
#: Araçsız-veri uyarıları — DONUK (plan 2026-09-29 Parça 1b-ön): ölçüm kartı ve operatör bu metinleri tanır.
UYARI_ARACSIZ = "⚠️ Bu cevap hiçbir araç çağrısına dayanmıyor — içindeki veri doğrulanmadı."
UYARI_OLCULEMEDI = "⚠️ Bu cevabın araç kullanımı doğrulanamadı."
#: "Veri içeriyor" DETERMİNİSTİK (`veri_isareti`; ilk eşleşen işaret, bu sırayla): rakam · `%` · katlanmış metinde
#: kaynak jetonu (`.json`, `.jsonl`yi kapsar) · alan sözlüğü (kelime başında kök öneki) · büyük harfli sembol
#: (`SEMBOL_DISI` hariç).
_RAKAM = re.compile(r"\d")
_VERI_JETONLARI = ("kaynak", "source", ".json")
#: Alan sözlüğü — Rol-1 kararları 2026-09-30 (inceleme I-3 genişletme; Tur 3 kök öneki; Tur 4 `getiri`/`hisset`).
#: Katlanmış (`kadro.ad_katla`) metinde KELİME BAŞINDA KÖK ÖNEKİ eşleşir: Türkçe eklemeli — tam-kelime kuralı 10
#: çekimli alan cümlesinin 1'ini yakalıyordu. Kökler ≥4 harf. DÜŞENLER: `kar` (karar/karne/kardeş çakışması),
#: `getiri` ("getirmek" fiili: depo Türkçe belgelerinde `getiri*` isabetlerinin 41/137'si; getiri iddiaları rakam
#: ya da `%` taşır, onlar ayrı işarettir). BİLİNEN GÜRÜLTÜ (ölçüldü, bilerek bırakıldı): `zarar` → "zararlı",
#: `plan`/`stop` → İngilizce "plane"/"planner"/"stopped", `hisse` → "hissediyorum"/"hissederim" (`hissed` öneki
#: "hissedar"la ortak). Yanlış pozitif yalnız bir uyarı satırıdır; defter `veri_isareti` alanından ölçülür ve kart
#: `sozluk:*` isabetlerini inceleme sınıfı sayar (Rol-1).
VERI_SOZLUGU = ("rejim", "maruziyet", "pozisyon", "stop", "alarm", "emir", "zarar", "butce",
                "sinyal", "plan", "fiyat", "hisse", "portfoy", "dolum", "tetik")
_SOZLUK_DESENI = re.compile(r"\b(" + "|".join(VERI_SOZLUGU) + r")\w*")
#: Kök önekine takılan ama açıkça veri OLMAYAN katlanmış TAM kelimeler — yalnız ÖLÇÜLMÜŞ çakışmalar: `emirhan`
#: (Rol-1, özel ad), `zararsiz` (SOUL'da "nedeni zararsız görünüyor" = masum). Ayrışma çivisi: v593 SOUL taraması.
SOZLUK_DISI = frozenset({"emirhan", "zararsiz"})
#: Kök önekine takılan ama açıkça veri olmayan kelimelerin ÖNEKLERİ (Rol-1 Tur 4): `hisset` = "hissetmek" fiili
#: (hissettirdi, hissetmek, hissettim). `hissed` BİLEREK YOK: "hissedar" (hissedar) ve "hisseler" veri kalır.
SOZLUK_DISI_ONEK = ("hisset",)
_SEMBOL_DESENI = re.compile(r"\b[A-Z]{2,5}\b")
#: Sembol SAYILMAYAN büyük harfli jetonlar: Rol-1 listesi + kendi SOUL/uyarı metinlerimizde ÖLÇÜLEN vurgu
#: kelimeleri (2026-09-30; `deploy/hermes/**/SOUL*.md` — ayrışma çivisi v593 SOUL taraması). BEDEL: `GO`,
#: `OOS`, `KALDI`, `GECTI` gibi hüküm kelimeleri bu işarete takılmaz.
SEMBOL_DISI = frozenset({
    "OK", "UTC", "API", "JSON", "PDF", "AI", "TL", "USD",
    "ANLAM", "ANMAK", "ARIZA", "ARTIK", "AYNI", "AZ", "BU", "CAGRI", "DURAN", "EN", "GECTI", "GO", "HAFTA",
    "HAZIR", "HER", "IZI", "KALDI", "KALEM", "KEZ", "KIL", "MCP", "NE", "NEDEN", "OKUMA", "OOS", "SADE", "SANA",
    "SATIR", "SIRA", "SKILL", "SON", "SONRA", "TEK", "VERI", "YA", "YAZMA", "YOK", "ZORLA",
})
#: Sohbet dönüşü kaydının sabit etiketi (dönüş kaydını `sabit_not`tan ayırır; plan 2026-09-30 G4 Görev 1).
DONUS_ETIKETI = "sohbet_donusu"
#: Telegram yanıt kipinde yanıtlanan mesajın bota giden VERİ çitinin adı — TEK KAYNAK burası (G4 Görev 1 Tur 3,
#: inceleme I-1): üretici `telegram_dinleyici._bota_giden` ithal eder, dönüş kaydı (`_hafiza_mesaji`) çözer.
ALINTI_CIT_ADI = "yanitlanan_mesaj"
#: Yanıt kaynak etiketinin (yanıtlanan mesajın ilk İÇERİK satırı) karakter tavanı — `alinti_icerik_satiri`.
KAYNAK_ETIKETI_TAVANI = 80
#: Telegram SOHBET İMZASI — bot cevabının her parçasının ve ara bildirimin İLK satırı: `💬 @<bot> · <oturum>`, çok
#: parçalıda sonunda `PARCA_EKI` (` (i/n)`). TEK KAYNAK burası (G4 kalıntıları M-2, 2026-10-01): Telegram dinleyicisi
#: üretirken de yönlendirirken de bunları İTHAL eder; alıntının içerik satırı (`alinti_icerik_satiri`) imzayı AYNI
#: tanıyıcıyla atlar. İki kopya ayrışsaydı yönlendirme ile hafıza etiketi farklı satırı "imza" sayardı. Dinleyiciden
#: buraya TAŞINDI: dinleyici bu modülü ithal eder, ters yön döngüsel ithal olurdu.
SOHBET_IMZA = "💬 @{ad}"
#: İmza satırında bot ile oturum arasındaki ayraç — yanıt zincirinin oturumu cevabın KENDİSİNDE taşınır.
OTURUM_AYRACI = " · "
#: Çok parçalı cevapta her parçanın imza satırının sonuna eklenen sıra eki; tek parçada YOK (eski biçim aynen).
PARCA_EKI = " ({no}/{toplam})"
#: Sohbet imza satırının TANIYICISI. Bot adı [a-z_] — kadro bunu ZORLAR (`kadro.AD_DESENI`). Oturum `tg-<ad>-r<N>` ya da
#: `tg-<ad>-<YYYYAAGG>`. Desen `PARCA_EKI`ni TANIR ama oturum grubuna KATMAZ (G4 Görev 3 Tur 2): hangi parçaya yanıt
#: verilirse verilsin aynı bot + aynı oturum. Elle yazılmış bir kopyadır; üreticiye gidiş-dönüş çivisiyle bağlı (v602).
_SOHBET_IMZA = re.compile(r"^💬 @([a-z_]+)(?: · (tg-[a-z_]+-r?\d+))?(?: \([1-9]\d*/[1-9]\d*\))?\s*$")
#: Telegram ARA BİLDİRİM balonunun 2. satırı (1. satırı eksiz sohbet imzası): `bota_sor` eşiği aşınca dinleyici BİR kez
#: gönderir (`telegram_dinleyici._AraBildirim`; eşik dinleyicinin `ARA_BILDIRIM_ESIGI_S`i). TEK KAYNAK burası (G4
#: kalıntıları Tur 2, inceleme M-1, 2026-10-01): dinleyici İTHAL eder; içerik kuralı bu satırı da atlar — balona yanıt
#: Tur 2 kararıyla aynı bota/oturuma gider ve "⏳ düşünüyor…" etiket ya da `unut:` sorgusu olmamalı. İmza sabitleriyle
#: aynı nedenle buraya taşındı (dinleyici bu modülü ithal eder; ters yön döngüsel ithal olurdu).
ARA_BILDIRIM = "⏳ düşünüyor…"
#: Alıntıda İÇERİK SAYILMAYAN tam satırlar: araçsız-veri uyarıları (`_onekle` onları cevabın başına koyar; Telegram'da
#: imzanın hemen altında durur) ve ara bildirim satırı. Metin kopyalanmaz, sabitlerin kendisi kullanılır (G4 kalıntıları
#: M-3; ara bildirim Tur 2).
_ICERIK_DISI_SATIRLAR = (UYARI_ARACSIZ, UYARI_OLCULEMEDI, ARA_BILDIRIM)
#: Monotonik saat — taşıyıcı (`sure_s`) ve dönüş kaydı (`hafiza_sure_s`) süreleri. Modül düzeyinde ki çiviler sahte
#: saatle süre alanlarını ölçebilsin.
_saat = time.monotonic
#: `HermesTasiyici` zaman aşımı varsayılanı (sn; soket İŞLEMİ başına). Hermes bir model çağrısını en kötü
#: `SOHBET_API_DENEME × SOHBET_ISTEK_ZAMAN_ASIMI_SN` bekler (`ops/sohbet_profili_uret.py`); taşıyıcı bundan KISA
#: bekleseydi model hâlâ çalışırken düşerdi — çapraz çivi v593 `test_hermes_zaman_asimi_sohbet_cagri_butcesini_kapsar`.
HERMES_ZAMAN_ASIMI_S = 300.0
#: Oturum kimliği oturum dökümü GET'inde URL YOLUNA girer (bot adıyla aynı sınıf): `/`, `..`, `?`, `#`
#: yolu başka bir uca taşırdı. Desene uymayan kimlikte GET ATILMAZ, sayım ölçülemedi (`None`) olur.
_OTURUM_DESENI = re.compile(r"[A-Za-z0-9_-]{1,128}")


@dataclass(frozen=True)
class TasiyiciSonuc:
    metin: str
    arac_cagrilari: int | None = None
    model_cagrilari: int | None = None


class Tasiyici(Protocol):
    def sor(self, bot: str, mesaj: str, oturum: str) -> TasiyiciSonuc: ...


class SayimOlculemedi(ValueError):
    """Bu turun araç sonucu sayısı ölçülemedi — kendi denetimlerimizin kapalı-küme `neden`i (`oturum_kimligi` ·
    `bicim` · `tur_hizasiz`). İçerik, URL ya da anahtar TAŞIMAZ."""

    def __init__(self, neden: str):
        super().__init__(neden)
        self.neden = neden


class Hafiza(Protocol):
    def yaz(self, bot: str, metin: str, etiketler: tuple[str, ...]) -> bool: ...

    def unut_adaylari(self, bot: str, ifade: str) -> list[tuple[str, str]]:
        """`unut:` ilk adımı — SALT-OKUR: `(bellek_id, metin_kesiti)` aday listesi (boş = eşleşme yok)."""
        ...

    def unut_uygula(self, bot: str, idler: list[str], ifade: str) -> list[str]:
        """Onaylanan kimlikleri geri alınabilir biçimde emekliye ayırır; emekliye ayrılan kimlikleri döner. Hata
        istisnası `unutulanlar` / `denenen` / `kalan` taşır."""
        ...

    def geri_al(self, bot: str, memory_id: str) -> bool:
        """`unut_uygula`nın tersi (bellek yeniden hatırlanır); hata istisnadır."""
        ...

    def donus_yaz(self, bot: str, mesaj: str, cevap: str,
                  etiketler: tuple[str, ...]) -> bot_hafiza.DonusSonucu:
        """Sohbet dönüşü kaydı (operatör sözleri + botun önekli cevabı); `DonusSonucu(kabul, islem_kimligi)` döner,
        hata istisnadır."""
        ...


class HermesTasiyici:
    """Hermes api_server (v0.19.0, A1 kaynağında ölçüldü): `POST {taban}/p/<bot>/v1/chat/completions`,
    `Authorization: Bearer <API_SERVER_KEY>`, oturum sürekliliği `X-Hermes-Session-Id`. Anahtar HER
    çağrıda `secrets.credential_oku` ile okunur (LoadCredential kanalı; argv/ortam/log'a düşmez) —
    yoksa istek HİÇ atılmaz. Zaman aşımı ZORUNLUDUR: asılı bir api_server Telegram döngüsünü de
    asardı — kurucu sonlu ve > 0 olmayan değeri (`None`, 0, negatif, inf, nan, bool, dizge) `ValueError`
    ile REDDEDER; `urlopen(timeout=None)` soketi sonsuz bloklardı (Tur 3, son inceleme I-1). Sınır soket
    İŞLEMİ başınadır, duvar saati değil (park: son inceleme M-4). `arac_cagrilari` sohbet çağrısından SONRA
    `GET {taban}/p/<bot>/api/sessions/<oturum>/messages` dökümünden ölçülür (`_bu_turun_arac_sonuclari`: hizalı
    döküm, dönen araç SONUÇLARI; AYNI zaman aşımı ve anahtar hijyeni); okunamaz, hizasız ya da biçimi tanınmazsa
    `None` + `bot_arac_sayimi_olculemedi` olayı (`sinif` + kapalı-küme `neden`) — sohbet cevabı düşmez.
    `model_cagrilari` bu yolda ÖLÇÜLMÜYOR (`None`): api_server cevabının bu sayıyı taşıyıp taşımadığı
    Parça 0 (b)/(g) ölçümünü bekler (uydurma yasağı)."""

    def __init__(self, taban_url: str = "http://127.0.0.1:8642", zaman_asimi_s: float = HERMES_ZAMAN_ASIMI_S,
                 _cagir=None, _anahtar=None):
        # bool bir int alt sınıfıdır: `True` 1 sn diye sessizce okunmasın (kadro `gunluk_tavan` emsali).
        if (isinstance(zaman_asimi_s, bool) or not isinstance(zaman_asimi_s, (int, float))
                or not math.isfinite(zaman_asimi_s) or zaman_asimi_s <= 0):
            raise ValueError(f"HermesTasiyici: zaman_asimi_s sonlu ve > 0 olmalı, gelen {zaman_asimi_s!r} — "
                             "sınırsız çağrı Telegram döngüsünü süresiz kilitler")
        self.taban_url = taban_url.rstrip("/")
        self.zaman_asimi_s = zaman_asimi_s
        self._cagir = _cagir or self._cagir_varsayilan
        self._anahtar = _anahtar or (lambda: secrets.credential_oku("API_SERVER_KEY"))

    @staticmethod
    def _cagir_varsayilan(url: str, govde: dict | None, basliklar: dict, zaman_asimi: float) -> dict:
        """`govde` varsa JSON POST (sohbet), `None` ise gövdesiz GET (oturum dökümü)."""
        if govde is None:
            istek = urllib.request.Request(url, method="GET", headers=dict(basliklar))
        else:
            istek = urllib.request.Request(url, data=json.dumps(govde).encode(), method="POST",
                                           headers={"Content-Type": "application/json", **basliklar})
        try:
            with urllib.request.urlopen(istek, timeout=zaman_asimi) as y:
                return json.load(y)
        except urllib.error.HTTPError as e:  # sinyalli: yalnız HTTP KODU yukarı gider; e.url/e.msg/str(e) BASILMAZ, zincir bastırılır
            hata = RuntimeError(f"api_server HTTP {e.code}")
            hata.http_kod = e.code  # sayım olayının `neden`i için (M-2) — tamsayı; URL/mesaj/anahtar taşımaz
            raise hata from None

    def sor(self, bot: str, mesaj: str, oturum: str) -> TasiyiciSonuc:
        if not _kadro.AD_DESENI.fullmatch(bot or ""):
            raise ValueError("HermesTasiyici: bot adı [a-z_] olmalı (URL yoluna girer)")
        anahtar = self._anahtar()
        if not anahtar:
            raise RuntimeError("API_SERVER_KEY credential yok")
        d = self._cagir(f"{self.taban_url}/p/{bot}/v1/chat/completions",
                        {"model": "hermes-agent", "messages": [{"role": "user", "content": mesaj}]},
                        {"Authorization": f"Bearer {anahtar}", "X-Hermes-Session-Id": oturum},
                        self.zaman_asimi_s)
        try:
            metin = d["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as e:  # sinyalli: biçim hatası sınıf adıyla yukarı; gövde basılmaz
            raise RuntimeError(f"api_server cevabı beklenmeyen biçimde ({type(e).__name__})") from None
        if not isinstance(metin, str):
            raise RuntimeError("api_server cevabında metin yok")
        return TasiyiciSonuc(metin, arac_cagrilari=self._arac_sayisi(bot, oturum, anahtar, metin))

    def _arac_sayisi(self, bot: str, oturum: str, anahtar: str, cevap: str) -> int | None:
        """Bu turun GERÇEK araç SONUCU sayısı (hizalı Hermes oturum dökümü); ölçülemezse `None` — 0 UYDURULMAZ."""
        try:
            if not _OTURUM_DESENI.fullmatch(oturum or ""):
                raise SayimOlculemedi("oturum_kimligi")
            d = self._cagir(f"{self.taban_url}/p/{bot}/api/sessions/{oturum}/messages", None,
                            {"Authorization": f"Bearer {anahtar}"}, self.zaman_asimi_s)
            return _bu_turun_arac_sonuclari(d, cevap)
        except Exception as e:  # sinyalli: olay (sınıf adı + kapalı-küme neden) + None → bota_sor UYARI_OLCULEMEDI ekler; sohbet cevabı düşmez
            obs.warn("bot_arac_sayimi_olculemedi", bot=bot, sinif=type(e).__name__, neden=_olculemedi_nedeni(e))
            return None


def _olculemedi_nedeni(e: Exception) -> str:
    """`bot_arac_sayimi_olculemedi` olayının `neden`i (inceleme M-2) — KAPALI küme, `str(e)` kullanılmaz:
    `oturum_kimligi` · `bicim` · `tur_hizasiz` (kendi denetimlerimiz, `SayimOlculemedi`) · `http_<kod>` ·
    `ag` (bağlantı/zaman aşımı, `OSError` ailesi) · `bicim` (JSON çözülemedi, `ValueError`) · `beklenmeyen`."""
    if isinstance(e, SayimOlculemedi):
        return e.neden
    kod = getattr(e, "http_kod", None)
    if isinstance(kod, int) and not isinstance(kod, bool):
        return f"http_{kod}"
    if isinstance(e, OSError):
        return "ag"
    if isinstance(e, ValueError):
        return "bicim"
    return "beklenmeyen"


def _bu_turun_arac_sonuclari(dokum, cevap: str) -> int:
    """Hermes oturum dökümünden (`{"data": [{"role", "content", "tool_calls"}, ...]}`) BU turun araç SONUCU sayısı.

    HİZA (inceleme I-1): döküm ancak SON mesajı `role == "assistant"` ve içeriği az önce alınan sohbet cevabına
    (`.strip()` sonrası) EŞİTSE bu turundur; değilse (bu tur henüz yazılmamış, sayfalanmış ya da devrilmiş oturum)
    `tur_hizasiz`. Hizasız döküm sayılsaydı önceki turun araç sonuçları bu turun araçsız cevabını SESSİZCE
    susturabilirdi (plan Review Focus 1).
    SAYIM (inceleme I-2): SON `role == "user"` mesajından sonraki `role == "tool"` mesajları — DÖNEN sonuçlar.
    `tool_calls` öğeleri (denemeler) SAYILMAZ: yanıtsız bir yapılandırılmış çağrı uyarıyı susturamaz.
    BİLİNEN SINIR: HATA dönen bir araç da sonuç sayılır (sayım içeriğe bakmaz) — ölçüm kartı kill-list'i bu
    sınırı yazar; "`arac_siz_veri` sıfır" her cevabın başarılı bir araca dayandığı anlamına GELMEZ.
    Biçim tanınmazsa ya da tur bulunamazsa `SayimOlculemedi` (içerik basılmaz) — çağıran `None`a çevirir."""
    mesajlar = dokum.get("data") if isinstance(dokum, dict) else None
    if not isinstance(mesajlar, list) or not mesajlar or not all(isinstance(m, dict) for m in mesajlar):
        raise SayimOlculemedi("bicim")
    son = mesajlar[-1]
    icerik = son.get("content")
    if son.get("role") != "assistant" or not isinstance(icerik, str) or icerik.strip() != cevap.strip():
        raise SayimOlculemedi("tur_hizasiz")
    son_kullanici = max((i for i, m in enumerate(mesajlar) if m.get("role") == "user"), default=None)
    if son_kullanici is None:
        raise SayimOlculemedi("bicim")
    return sum(1 for m in mesajlar[son_kullanici + 1:] if m.get("role") == "tool")


def veri_isareti(metin: str) -> str | None:
    """Cevabın veri taşıdığını gösteren İLK işaret — DETERMİNİSTİK, modele sorulmaz. Sıra: `"rakam"` · `"yuzde"` ·
    `"kaynak"` (katlanmış metinde `kaynak`/`source`/`.json`) · `"sozluk:<kök>"` (`VERI_SOZLUGU`, kelime başında
    kök öneki; `SOZLUK_DISI` kelimeleri ve `SOZLUK_DISI_ONEK` önekli kelimeler atlanır; metindeki ilk eşleşme) ·
    `"sembol:<X>"` (özgün metinde `[A-Z]{2,5}`, `SEMBOL_DISI` hariç) · `None`.
    Bilerek geniş: yanlış pozitif yalnız bir uyarı satırıdır ve defterin `veri_isareti` alanından ÖLÇÜLÜR;
    yanlış negatif operatöre doğrulanmamış veri demektir."""
    metin = metin or ""
    if _RAKAM.search(metin):
        return "rakam"
    if "%" in metin:
        return "yuzde"
    katli = _kadro.ad_katla(metin)
    if any(j in katli for j in _VERI_JETONLARI):
        return "kaynak"
    for kelime in _SOZLUK_DESENI.finditer(katli):
        if kelime.group(0) not in SOZLUK_DISI and not kelime.group(0).startswith(SOZLUK_DISI_ONEK):
            return f"sozluk:{kelime.group(1)}"
    for sembol in _SEMBOL_DESENI.findall(metin):
        if sembol not in SEMBOL_DISI:
            return f"sembol:{sembol}"
    return None


def veri_iceriyor(metin: str) -> bool:
    """`veri_isareti(metin) is not None` (brief arayüzü)."""
    return veri_isareti(metin) is not None


def _onekle(metin: str, onek: str | None) -> str:
    """`onek + "\\n" + metin`; önek yoksa ya da cevap zaten onunla başlıyorsa metin olduğu gibi."""
    if onek is None or metin.startswith(onek):
        return metin
    return f"{onek}\n{metin}"


def _utc(simdi: datetime | None) -> datetime:
    if simdi is None:
        return datetime.now(timezone.utc)
    if simdi.tzinfo is None:
        raise ValueError("bota_sor: `simdi` saat dilimli olmalı (kota günü UTC)")
    return simdi.astimezone(timezone.utc)


def gunluk_sayim(bot: str, gun: str) -> int:
    """`bot`un `gun` (UTC `YYYY-MM-DD`) içindeki `tur == "sohbet"` defter satırı sayısı. Defterin
    TAMAMI okunur: kuyruk okuması (`limit`) yoğun bir günde eksik sayıp kotayı sessizce aşardı."""
    return sum(1 for s in store.read_jsonl(DEFTER)
               if s.get("bot") == bot and s.get("tur") == "sohbet" and str(s.get("ts", "")).startswith(gun))


def _defter_yaz(satir: dict) -> None:
    try:
        store.append_jsonl(DEFTER, satir)
    except Exception as e:  # sinyalli: olay + cevap düşmez — defter kaybı görünür, operatörün cevabı kaybolmaz
        obs.warn("bot_defter_yazim_hatasi", bot=satir.get("bot"), tur=satir.get("tur"), sinif=type(e).__name__)


def _satir(an: datetime, bot: str, kanal: str, oturum: str, tur: str, mesaj: str,
           cevap: str | None, **ek) -> dict:
    temiz_mesaj = notify.scrub(mesaj)
    temiz_cevap = notify.scrub(cevap) if cevap is not None else None
    return {
        "ts": an.isoformat(timespec="seconds"), "bot": bot, "kanal": kanal, "oturum": oturum, "tur": tur,
        "mesaj": temiz_mesaj, "mesaj_sha": hashlib.sha256(temiz_mesaj.encode()).hexdigest()[:16],
        "cevap": temiz_cevap[:CEVAP_TAVANI] if temiz_cevap is not None else None,
        "cevap_uzunluk": len(cevap) if cevap is not None else None,
        "kesildi": temiz_cevap is not None and len(temiz_cevap) > CEVAP_TAVANI,
        **ek,
    }


def komut_oneki(metin: str) -> tuple[str, str] | None:
    """Komut TESPİTİNİN TEK KAYNAĞI: `(ad, gövde)` — `ad` ∈ `KOMUTLAR` (katlanmış; `geri al` → `geri_al`) — ya da `None`.

    Hem `bota_sor` (dağıtım) hem Telegram dinleyicisi (`telegram_dinleyici.isle`, VERİ çiti
    kurulmadan ÖNCE operatörün kendi sözleri üzerinde) BUNU çağırır — iki ayrı regex ayrışır ve bir
    girdi bir yerde komut, öbüründe soru sayılır (Tur 2, inceleme I-1). Önek metnin BAŞINDA aranır;
    çit burada AYRIŞTIRILMAZ: sahte bir çit, alıntılanan veriden komut enjekte etmenin kapısı olurdu."""
    m = _KOMUT.match((metin or "").strip())
    if not m:
        return None
    ad = "_".join(_kadro.ad_katla(kelime) for kelime in m.group(1).split())
    return (ad, m.group(2).strip()) if ad in KOMUTLAR else None


def _komut(bot: str, mesaj: str, kanal: str, oturum: str, an: datetime, hafiza: Hafiza) -> str | None:
    """Komut dalı (`KOMUTLAR`). Komut değilse `None` (soru modele gider)."""
    komut = komut_oneki(mesaj)
    if komut is None:
        return None
    ad, govde = komut
    if ad == "unut":
        return _unut(bot, mesaj, govde, kanal, oturum, an, hafiza)
    if ad == "onayla":
        return _onayla(bot, mesaj, govde, kanal, oturum, an, hafiza)
    if ad == "geri_al":
        return _geri_al(bot, mesaj, govde, kanal, oturum, an, hafiza)
    if not govde:
        cevap, durum = _HATIRLA_BOS, "bos_govde"
    else:
        temiz = notify.scrub(govde)
        try:
            yazildi = bool(hafiza.yaz(bot, temiz, ("sabit_not", f"bot:{bot}", f"kanal:{kanal}")))
        except Exception as e:  # sinyalli: olay + "YAZILAMADI" cevabı; hafıza istisnası sohbet hatasına dönmez
            obs.warn("bot_hafiza_yazim_hatasi", bot=bot, sinif=type(e).__name__, neden=bot_hafiza.hata_nedeni(e))
            yazildi = False
        if yazildi:
            cevap, durum = f"Not aldım: {temiz}", "yazildi"
        else:
            obs.warn("bot_hafiza_yazilamadi", bot=bot, kanal=kanal)
            cevap, durum = _HAFIZA_YAZILAMADI, "yazilamadi"
    _defter_yaz(_satir(an, bot, kanal, oturum, "hatirla", mesaj, cevap, hafiza_durumu=durum))
    return cevap


def _liste(kesitler) -> str:
    """`1) kesit 2) kesit` — kesit hafızadan gelir, operatöre gitmeden ÖNCE `notify.scrub`'dan geçer."""
    return " ".join(f"{i}) {notify.scrub(str(kesit))}" for i, kesit in enumerate(kesitler, 1))


def _kod_uret() -> str:
    """6 hex kısa kod (standart kütüphane `token_hex(3)`: tahmin edilemez; operatör elle yazar)."""
    return _std_secrets.token_hex(3)


def _kod_ayikla(parca: str) -> str | None:
    """Operatörün yazdığı kod: 6 hex (harf büyüklüğü duyarsız, küçük harfe indirilir); değilse `None`."""
    kod = parca.lower()
    return kod if _KOD_DESENI.fullmatch(kod) else None


def _onay_kodu(govde: str) -> str | None:
    """`onayla:` gövdesi TAM OLARAK `unut <kod>` olmalı (bugün onaylanan tek iş unutmadır); değilse `None`."""
    parcalar = govde.split()
    if len(parcalar) != 2 or _kadro.ad_katla(parcalar[0]) != "unut":
        return None
    return _kod_ayikla(parcalar[1])


def _id_listesi(deger) -> list[str] | None:
    """İstisnanın taşıdığı kimlik listesi; taşımıyorsa ya da tanınmazsa `None` ("hiçbiri" UYDURULMAZ)."""
    if isinstance(deger, (list, tuple)) and all(isinstance(k, str) for k in deger):
        return list(deger)
    return None


def _dilimli_an(deger) -> datetime:
    an = datetime.fromisoformat(deger)
    if an.tzinfo is None:
        raise ValueError("bekleyen kayıtta dilimsiz an")
    return an


def _bekleyen_bakim(doc, an: datetime) -> bool:
    """Her yazımda: süresi geçen `bekliyor` → `suresi_doldu` (SÜRE DENETİMİNİN TEK YERİ); `UNUT_BEKLEYEN_SAKLAMA`dan
    eski SONUÇLANMIŞ kayıt budanır. Belge değiştiyse `True`. Nesne olmayan belge `ValueError` (dış hasar).
    FAIL-CLOSED (Tur 2, inceleme M-1): `ts`/`son`u okunamayan (eksik, biçimsiz, dilimsiz) kayıt olayla bildirilir ve
    `bekliyor`sa `suresi_doldu` olur — süresi ölçülemeyen kod onaylanamaz; yaşı ölçülemediği için budanmaz."""
    if not isinstance(doc, dict):
        raise ValueError(f"{UNUT_BEKLEYEN} bir nesne değil")
    degisti = False
    for kod in list(doc):
        kayit = doc[kod]
        try:
            ts, son = _dilimli_an(kayit["ts"]), _dilimli_an(kayit["son"])
        except (KeyError, TypeError, ValueError) as e:  # sinyalli: bozuk (dış hasar) kayıt olayla bildirilir; FAIL-CLOSED
            obs.warn("bot_unut_bekleyen_bozuk_kayit", kod=str(kod)[:16], sinif=type(e).__name__)
            if isinstance(kayit, dict) and kayit.get("durum") == "bekliyor":
                kayit["durum"], degisti = "suresi_doldu", True
            continue
        if kayit.get("durum") == "bekliyor" and an >= son:
            kayit["durum"], degisti = "suresi_doldu", True
        if kayit.get("durum") in _SONUCLANMIS and an - ts > UNUT_BEKLEYEN_SAKLAMA:
            del doc[kod]
            degisti = True
    return degisti


def _bekleyen_ekle(bot: str, adaylar: list, ifade: str, an: datetime) -> str:
    """Aday listesini `bekliyor` olarak yazar, kısa kodu döner (çakışırsa `_KOD_DENEME` kez yeniden üretilir). AYNI
    botun önceki `bekliyor` kayıtları aynı yazımda `suresi_doldu` olur ve `yerine_gecen` yeni kodu taşır (Tur 2, inceleme
    M-2: bot başına tek canlı kod — eski listeyi yanlışlıkla onaylamak, kayıt şişmesi ve tahmin yüzeyi kapanır)."""
    sonuc = {}

    def degistir(doc):
        _bekleyen_bakim(doc, an)
        for _ in range(_KOD_DENEME):
            kod = _kod_uret()
            if kod not in doc:
                break
        else:
            raise RuntimeError("bekleyen unutma kodu üretilemedi (çakışma)")
        for eski in doc.values():
            if isinstance(eski, dict) and eski.get("bot") == bot and eski.get("durum") == "bekliyor":
                eski["durum"], eski["yerine_gecen"] = "suresi_doldu", kod
        doc[kod] = {"bot": bot, "idler": [k for k, _ in adaylar], "kesitler": [s for _, s in adaylar],
                    "ifade": ifade, "ts": an.isoformat(timespec="seconds"),
                    "son": (an + UNUT_ONAY_OMRU).isoformat(timespec="seconds"), "durum": "bekliyor"}
        sonuc["kod"] = kod
        return True

    store.update_json(UNUT_BEKLEYEN, degistir, {})
    return sonuc["kod"]


def _gecis_talebi(kod: str, bot: str, an: datetime, islem: str) -> tuple[str | None, dict]:
    """Kilit altında TEK geçiş (talep ÖNCE, hafıza isteği SONRA — iki eşzamanlı onay aynı kodu iki kez uygulayamaz).
    `islem` `onay`: `bekliyor` → `uygulandi`; `geri_al`: `uygulandi` → `geri_alindi`. Dönüş `(ret_nedeni, bilgi)`:
    ret yoksa `bilgi["kayit"]` talep edilen kaydın kopyası; `baska_bot` retinde `bilgi["sahip"]`; onay retinde
    `bilgi["yerine_gecen"]` (kodu yeni bir liste düşürdüyse). Bot eşitliği DURUMDAN ÖNCE sınanır: yabancı bot kodun
    hâlini de öğrenemez. Sahibi okunamayan kayıt da `baska_bot`tur (fail-closed)."""
    bilgi: dict = {}

    def degistir(doc):
        degisti = _bekleyen_bakim(doc, an)
        kayit = doc.get(kod)
        durum = kayit.get("durum") if isinstance(kayit, dict) else None
        if not isinstance(kayit, dict):
            bilgi["neden"] = "bilinmeyen_kod"
        elif kayit.get("bot") != bot:
            bilgi["neden"], bilgi["sahip"] = "baska_bot", kayit.get("bot")
        elif islem == "onay" and durum != "bekliyor":
            bilgi["neden"] = {"suresi_doldu": "suresi_doldu", "geri_alindi": "zaten_geri_alindi"}.get(
                durum, "zaten_uygulandi")
            bilgi["yerine_gecen"] = kayit.get("yerine_gecen")
        elif islem == "geri_al" and durum != "uygulandi":
            bilgi["neden"] = "zaten_geri_alindi" if durum == "geri_alindi" else "uygulanmadi"
        else:
            kayit["durum"] = "uygulandi" if islem == "onay" else "geri_alindi"
            bilgi["kayit"] = dict(kayit)
            degisti = True
        return degisti

    store.update_json(UNUT_BEKLEYEN, degistir, {})
    return bilgi.get("neden"), bilgi


def _bekleyen_guncelle(kod: str, **alanlar) -> None:
    """Talep edilmiş kaydın sonucunu yazar (durum geri dönüşü dahil). Kayıt kaybolduysa `ValueError` (dış hasar)."""
    def degistir(doc):
        kayit = doc.get(kod) if isinstance(doc, dict) else None
        if not isinstance(kayit, dict):
            raise ValueError(f"bekleyen unutma kaydı talepten sonra kayboldu ({UNUT_BEKLEYEN})")
        kayit.update(alanlar)
        return True

    store.update_json(UNUT_BEKLEYEN, degistir, {})


def _unut(bot: str, mesaj: str, govde: str, kanal: str, oturum: str, an: datetime, hafiza: Hafiza) -> str:
    """`unut:` İLK ADIMI — HİÇBİR ŞEYİ DEĞİŞTİRMEZ: salt-okur aday listesi + kısa kod (modül başlığı). Defter satırı
    `unut_kodu` + `aday_idler` taşır."""
    adaylar: list = []
    kod = None
    if not govde:
        cevap, durum = _UNUT_BOS, "bos_govde"
    else:
        ifade = notify.scrub(govde)
        try:
            adaylar = [(k, notify.scrub(str(s)))
                       for k, s in list(hafiza.unut_adaylari(bot, ifade))[:bot_hafiza.UNUT_TAVANI]]
        except Exception as e:  # sinyalli: olay (sınıf + kapalı-küme neden) + "ARANAMADI"; hiçbir şey değişmedi
            obs.warn("bot_hafiza_unut_hatasi", bot=bot, kanal=kanal, adim="aday", sinif=type(e).__name__,
                     neden=bot_hafiza.hata_nedeni(e))
            adaylar = []
            cevap, durum = _UNUT_ARANAMADI, "aranamadi"
        else:
            if not adaylar:
                cevap, durum = _UNUT_ESLESME_YOK, "eslesme_yok"
            else:
                try:
                    kod = _bekleyen_ekle(bot, adaylar, ifade, an)
                except Exception as e:  # sinyalli: olay + kod VERİLMEZ (kaydı olmayan kod onaylanamazdı)
                    obs.warn("bot_unut_bekleyen_hatasi", bot=bot, kanal=kanal, adim="aday", sinif=type(e).__name__)
                    cevap, durum = _UNUT_KAYDEDILEMEDI, "kayit_yazilamadi"
                else:
                    dk = int(UNUT_ONAY_OMRU.total_seconds() // 60)
                    cevap = (f"Unutmaya aday ({len(adaylar)}): {_liste(s for _, s in adaylar)}. HENÜZ hiçbir şey "
                             f"unutulmadı — onaylamak için {dk} dk içinde AYNI bota (@{bot}) `onayla: unut {kod}` yaz.")
                    durum = "onay_bekliyor"
    _defter_yaz(_satir(an, bot, kanal, oturum, "unut", mesaj, cevap, hafiza_durumu=durum, unut_kodu=kod,
                       aday_idler=[k for k, _ in adaylar]))
    return cevap


def _ret_cevabi(islem: str, neden: str, kod: str | None, bot: str, bilgi: dict) -> str:
    """Ret metni — her birinde neyin DEĞİŞMEDİĞİ açıkça söylenir. Bilinmeyen kod yanlış yazılmış ya da budanmış
    (`UNUT_BEKLEYEN_SAKLAMA`dan eski) olabilir: operatör bunu öğrenir (Tur 2, inceleme M-4)."""
    degismedi = "hiçbir şey unutulmadı" if islem == "onay" else "hiçbir şey değişmedi"
    if neden == "baska_bot":
        sahip = bilgi.get("sahip")
        kime = f"@{sahip}" if isinstance(sahip, str) and sahip else "başka bir bot"
        fiil = "onaylayamaz" if islem == "onay" else "geri alamaz"
        return f"Bu kod {kime} için; @{bot} {fiil} — {degismedi}."
    if neden == "bilinmeyen_kod":
        return (f"Kod bulunamadı — yanlış yazılmış ya da {UNUT_BEKLEYEN_SAKLAMA.days} günden eski (budanmış) olabilir; "
                f"{degismedi}.")
    if (islem, neden) == ("onay", "suresi_doldu") and bilgi.get("yerine_gecen"):
        return ("Bu kodun yerini aynı bota yazılan daha yeni bir aday listesi aldı; hiçbir şey unutulmadı — en son "
                "listedeki kodu kullan.")
    return {
        ("onay", "suresi_doldu"): f"Kodun süresi doldu ({int(UNUT_ONAY_OMRU.total_seconds() // 60)} dk); hiçbir "
                                  "şey unutulmadı — yeniden `unut: <ifade>` yaz.",
        ("onay", "zaten_uygulandi"): f"Bu kod zaten onaylandı (geri almak için `geri al: {kod}`); yeni bir şey "
                                     "unutulmadı.",
        ("onay", "zaten_geri_alindi"): "Bu kod onaylanmış ve sonra geri alındı; yeni bir şey unutulmadı — yeniden "
                                       "unutmak için yeni bir `unut: <ifade>` yaz.",
        ("geri_al", "uygulanmadi"): "Bu kod hiç onaylanmadı (ya da süresi doldu); geri alınacak bir şey yok.",
        ("geri_al", "zaten_geri_alindi"): "Bu kod zaten geri alındı; hiçbir şey değişmedi.",
    }[(islem, neden)]


def _onayla(bot: str, mesaj: str, govde: str, kanal: str, oturum: str, an: datetime, hafiza: Hafiza) -> str:
    """`onayla: unut <kod>` — YALNIZ aynı bot, `bekliyor`, süre içinde (modül başlığı). Defter satırı `unut_onay`
    (Rol-1 kararı 4): `unut_kodu`, `ret_nedeni`; uygulama denendiyse `unutulan_idler` / `denenen` / `kalan`."""
    kod = _onay_kodu(govde) if govde else None
    alanlar: dict = {"unut_kodu": kod, "ret_nedeni": None}
    if not govde:
        cevap, durum = _ONAY_BOS, "bos_govde"
    else:
        try:
            neden, bilgi = _gecis_talebi(kod, bot, an, "onay") if kod else ("bilinmeyen_kod", {})
        except Exception as e:  # sinyalli: olay + PATCH ATILMAZ (talep düştü, hiçbir şey değişmedi)
            obs.warn("bot_unut_bekleyen_hatasi", bot=bot, kanal=kanal, adim="onay", sinif=type(e).__name__)
            neden, bilgi = None, None
        if bilgi is None:
            cevap, durum = _BEKLEYEN_OKUNAMADI, "kayit_hatasi"
        elif neden is not None:
            obs.warn("bot_unut_onay_reddi", bot=bot, kanal=kanal, neden=neden)
            cevap, durum = _ret_cevabi("onay", neden, kod, bot, bilgi), "reddedildi"
            alanlar["ret_nedeni"] = neden
        else:
            cevap, durum = _unut_uygula(bot, kod, bilgi["kayit"], kanal, hafiza, alanlar)
    _defter_yaz(_satir(an, bot, kanal, oturum, "unut_onay", mesaj, cevap, hafiza_durumu=durum, **alanlar))
    return cevap


def _unut_uygula(bot: str, kod: str, kayit: dict, kanal: str, hafiza: Hafiza, alanlar: dict) -> tuple[str, str]:
    """Talep edilmiş (`uygulandi`) kaydın adaylarını `Hafiza.unut_uygula` ile emekliye ayırır; sonucu kayda ve
    `alanlar`a (defter) yazar. Hiçbir istek atılmadıysa (`denenen == []`) kod `bekliyor`a döner."""
    idler = list(kayit.get("idler") or [])
    kesit = dict(zip(idler, kayit.get("kesitler") or []))
    hata = None
    try:
        unutulanlar = [k for k in hafiza.unut_uygula(bot, idler, kayit.get("ifade") or "")]
        denenen, kalan = list(idler), []
    except Exception as e:  # sinyalli: olay (sınıf + kapalı-küme neden) + "UNUTULAMADI"; kısmi sonuç deftere ve kayda
        obs.warn("bot_hafiza_unut_hatasi", bot=bot, kanal=kanal, adim="onay", sinif=type(e).__name__,
                 neden=bot_hafiza.hata_nedeni(e))
        hata = e
        unutulanlar = _id_listesi(getattr(e, "unutulanlar", None))
        denenen = _id_listesi(getattr(e, "denenen", None))
        kalan = _id_listesi(getattr(e, "kalan", None))
    alanlar.update(unutulan_idler=unutulanlar, denenen=denenen, kalan=kalan)
    geri_don = hata is not None and denenen == []
    try:
        if geri_don:
            _bekleyen_guncelle(kod, durum="bekliyor")
        else:
            _bekleyen_guncelle(kod, unutulan_idler=unutulanlar, denenen=denenen, kalan=kalan)
    except Exception as e:  # sinyalli: olay; kayıt `uygulandi` kalır → `geri al` TÜM adayları dener (güvenli yön)
        obs.warn("bot_unut_bekleyen_hatasi", bot=bot, kanal=kanal, adim="sonuc", sinif=type(e).__name__)
    if hata is None:
        return (f"Unuttum (geri alınabilir — `geri al: {kod}`): "
                f"{_liste(kesit.get(k, '(metin yok)') for k in unutulanlar)}"), "unutuldu"
    cevap = _UNUTULAMADI
    if unutulanlar:
        cevap += (f" Yine de unutulanlar (geri alınabilir — `geri al: {kod}`): "
                  f"{_liste(kesit.get(k, '(metin yok)') for k in unutulanlar)}")
    elif geri_don:
        cevap += f" Hiçbir istek atılmadı; yeniden denemek için `onayla: unut {kod}`."
    else:
        cevap += f" Yarım kalan işlemi geri almak için `geri al: {kod}`."
    return cevap, "unutulamadi"


def _geri_al(bot: str, mesaj: str, govde: str, kanal: str, oturum: str, an: datetime, hafiza: Hafiza) -> str:
    """`geri al: <kod>` — YALNIZ aynı bot + `uygulandi`; onayda DENENEN kimliklere (bilinmiyorsa tüm adaylara) `valid`.
    Kısmi hatada kayıt `uygulandi`ya döner (yeniden denenebilir: `valid` PATCH'i geçerli bellekte zararsız). Defter
    satırı `geri_al`: `unut_kodu`, `ret_nedeni`; denendiyse `geri_alinan_idler` / `denenen` / `kalan`."""
    kod = _kod_ayikla(govde) if govde and len(govde.split()) == 1 else None
    alanlar: dict = {"unut_kodu": kod, "ret_nedeni": None}
    if not govde:
        cevap, durum = _GERI_AL_BOS, "bos_govde"
    else:
        try:
            neden, bilgi = _gecis_talebi(kod, bot, an, "geri_al") if kod else ("bilinmeyen_kod", {})
        except Exception as e:  # sinyalli: olay + PATCH ATILMAZ (talep düştü, hiçbir şey değişmedi)
            obs.warn("bot_unut_bekleyen_hatasi", bot=bot, kanal=kanal, adim="geri_al", sinif=type(e).__name__)
            neden, bilgi = None, None
        if bilgi is None:
            cevap, durum = _BEKLEYEN_OKUNAMADI, "kayit_hatasi"
        elif neden is not None:
            obs.warn("bot_unut_geri_al_reddi", bot=bot, kanal=kanal, neden=neden)
            cevap, durum = _ret_cevabi("geri_al", neden, kod, bot, bilgi), "reddedildi"
            alanlar["ret_nedeni"] = neden
        else:
            kayit = bilgi["kayit"]
            idler = list(kayit.get("idler") or [])
            kesit = dict(zip(idler, kayit.get("kesitler") or []))
            onceki = _id_listesi(kayit.get("denenen"))
            hedef = onceki if onceki else idler
            geri_alinanlar: list[str] = []
            denenen: list[str] = []
            hata = None
            try:
                for kimlik in hedef:
                    denenen.append(kimlik)
                    hafiza.geri_al(bot, kimlik)
                    geri_alinanlar.append(kimlik)
            except Exception as e:  # sinyalli: olay (sınıf + kapalı-küme neden) + "GERİ ALINAMADI"; kod `uygulandi`ya döner
                obs.warn("bot_hafiza_geri_al_hatasi", bot=bot, kanal=kanal, sinif=type(e).__name__,
                         neden=bot_hafiza.hata_nedeni(e))
                hata = e
            alanlar.update(geri_alinan_idler=geri_alinanlar, denenen=denenen, kalan=hedef[len(denenen):])
            try:
                if hata is None:
                    _bekleyen_guncelle(kod, geri_alinan_idler=geri_alinanlar)
                else:
                    _bekleyen_guncelle(kod, durum="uygulandi", geri_alinan_idler=geri_alinanlar)
            except Exception as e:  # sinyalli: olay; geri alma sonucu defter satırında yine kayıtlı
                obs.warn("bot_unut_bekleyen_hatasi", bot=bot, kanal=kanal, adim="sonuc", sinif=type(e).__name__)
            liste = _liste(kesit.get(k, "(metin yok)") for k in geri_alinanlar)
            if hata is None:
                cevap, durum = f"Geri aldım (yeniden hatırlanır): {liste}", "geri_alindi"
            else:
                cevap = _GERI_ALINAMADI + (f" Geri alınanlar: {liste}." if geri_alinanlar else "")
                cevap, durum = cevap + f" Yeniden denemek için `geri al: {kod}`.", "geri_alinamadi"
    _defter_yaz(_satir(an, bot, kanal, oturum, "geri_al", mesaj, cevap, hafiza_durumu=durum, **alanlar))
    return cevap


def alinti_icerik_satiri(alinti: str) -> str:
    """Yanıtlanan mesajın ilk İÇERİK satırı — TEK KURAL (G4 kalıntıları M-2/M-3, 2026-10-01). Baştan atlananlar: boş
    satırlar, sohbet imza satırı (`_SOHBET_IMZA`, parça ekli dahil — bot cevabının her parçası ve ara bildirim onunla
    başlar) ve araçsız-veri uyarıları (`_ICERIK_DISI_SATIRLAR`; satırın TAMAMI eşleşirse). İlk kalan satır ÖNCE
    `notify.scrub`, SONRA `KAYNAK_ETIKETI_TAVANI` (ters sıra yarım anahtarı süzgeçten kaçırırdı). Rapor alıntısında ilk
    satır (rapor başlığı) İÇERİKTİR — rapor imzası sohbet imzası değildir. İçerik satırı yoksa `""`: imza ya da uyarı
    içerik diye UYDURULMAZ. TÜKETİCİLER (hepsi bu kuraldan geçer — iki kural ayrışıyordu, inceleme M-2):
    `kaynak_etiketi` (Telegram `hatırla:` yanıtı + dönüş kaydı) ve Telegram'ın gövdesiz `unut:` sorgusu
    (`telegram_dinleyici._komut_giden`, G4 Görev 2 — Rol-1 kararı 5)."""
    for satir in str(alinti).split("\n"):
        satir = satir.strip()
        if satir and not _SOHBET_IMZA.match(satir) and satir not in _ICERIK_DISI_SATIRLAR:
            return notify.scrub(satir)[:KAYNAK_ETIKETI_TAVANI]
    return ""


def kaynak_etiketi(alinti: str) -> str | None:
    """`(yanıt: <yanıtlanan mesajın ilk İÇERİK satırı>)` — satır `alinti_icerik_satiri`ndan (tek kural; scrub SONRA
    tavan). İçerik satırı yoksa `None`: etiket UYDURULMAZ (imza ya da uyarı etikete girmez, boş `(yanıt: )` de yazılmaz)
    ve çağıran etiketsiz sürer. TEK KAYNAK: Telegram `hatırla:` yanıtı (`telegram_dinleyici._komut_giden`) ve dönüş
    kaydı (`_hafiza_mesaji`) aynı etiketi buradan alır."""
    satir = alinti_icerik_satiri(alinti)
    return f"(yanıt: {satir})" if satir else None


def _hafiza_mesaji(mesaj: str) -> str:
    """Dönüş kaydına giden OPERATÖR metni (inceleme I-1) — KANALDAN BAĞIMSIZ: `mesaj` metnin BAŞINDA `ALINTI_CIT_ADI`
    adlı bir VERİ çiti taşıyorsa (bugün onu yalnız Telegram yanıt kipi üretir, ama hangi kanaldan gelirse gelsin aynı
    işlem uygulanır) çit bir ALINTIDIR: hafızaya "Operatör:" diye girerse alıntı (rapor ya da botun eski cevabı)
    yanlış atfedilir ve uzun alıntıda operatörün sorusu `bot_hafiza.DONUS_TAVANI`nın dışına düşer. Çit çıkarılır,
    yerine `kaynak_etiketi` kalır (alıntının içerik satırı yoksa etiket de yoktur — yalnız sözler gider). Çit grameri
    `skill_gorus_llm.veri_bloku_ayir`dan çözülür (jetonlar elle yazılmaz). Başka adlı ya da metnin ortasındaki çit
    OLDUĞU GİBİ kalır (anlamı uydurulmaz). Modele ve deftere giden metin DEĞİŞMEZ."""
    ayrik = skill_gorus_llm.veri_bloku_ayir(mesaj, ALINTI_CIT_ADI)
    if ayrik is None:
        return mesaj
    alinti, sozler = ayrik
    return "\n".join(p for p in (kaynak_etiketi(alinti), sozler) if p)


def _donus_kaydi(bot: str, mesaj: str, cevap: str, kanal: str, arac_siz_veri: bool | None,
                 arac_olculemedi: bool, hafiza: Hafiza) -> dict:
    """Sohbet dönüşünü hafızaya yazar; defter alanlarını döner: `hafiza_durumu` (`kabul_edildi` | `yazilamadi`),
    `hafiza_islem_kimligi` (Hindsight işlem kimliği ya da `None`), `hafiza_sure_s` (çağrının duvar saati süresi,
    3 ondalık — async kabul gecikmesi G3c'de buradan ölçülür). Hafıza istisnası (sonuç nesnesi tanınmazsa da istisna
    yolu), `success: false` CEVABI DÜŞÜRMEZ — olay yazılır (modül başlığı, DÖNÜŞ KAYDI)."""
    etiketler = (f"bot:{bot}", f"kanal:{kanal}", DONUS_ETIKETI)
    if arac_siz_veri is True:
        etiketler += ("arac_siz_veri",)
    if arac_olculemedi:
        etiketler += ("arac_olculemedi",)
    kimlik = None
    t0 = _saat()
    try:
        sonuc = hafiza.donus_yaz(bot, notify.scrub(_hafiza_mesaji(mesaj)), notify.scrub(cevap), etiketler)
        kabul, kimlik = sonuc.kabul is True, sonuc.islem_kimligi
    except Exception as e:  # sinyalli: olay (sınıf adı + kapalı-küme neden) + defter `yazilamadi`; hafıza istisnası cevabı düşürmez
        obs.warn("bot_hafiza_donus_hatasi", bot=bot, kanal=kanal, sinif=type(e).__name__,
                 neden=bot_hafiza.hata_nedeni(e))
        durum = "yazilamadi"
    else:
        if kabul:
            durum = "kabul_edildi"
        else:
            obs.warn("bot_hafiza_donus_yazilamadi", bot=bot, kanal=kanal)
            durum = "yazilamadi"
    return {"hafiza_durumu": durum, "hafiza_islem_kimligi": kimlik if isinstance(kimlik, str) else None,
            "hafiza_sure_s": round(_saat() - t0, 3)}


def bota_sor(bot: str, mesaj: str, kanal: str, oturum: str, *, tasiyici: Tasiyici | None = None,
             hafiza: Hafiza | None = None, simdi=None, kadro=None) -> str:
    """Kanal → bot → komut → kota → taşıyıcı → dönüş kaydı → defter (modül başlığındaki DONUK sıra). `tasiyici` /
    `hafiza` verilmezse ÜRETİM varsayılanları (`HermesTasiyici`, `bot_hafiza.HindsightHafiza`)."""
    if kanal not in KANALLAR:
        raise ValueError(f"bota_sor: kanal {kanal!r} izinli değil {KANALLAR}")
    b = _kadro.bot_bul(bot, kadro)
    if b is None or b.durum != "aktif":
        raise ValueError(f"bota_sor: {bot!r} kadroda aktif bir bot değil")
    an = _utc(simdi)
    if hafiza is None:
        hafiza = bot_hafiza.HindsightHafiza()
    komut_cevabi = _komut(b.ad, mesaj, kanal, oturum, an, hafiza)
    if komut_cevabi is not None:
        return komut_cevabi
    n = gunluk_sayim(b.ad, an.strftime("%Y-%m-%d"))
    if b.gunluk_tavan is not None and n >= b.gunluk_tavan:
        cevap = f"@{b.ad} bugünlük kotam doldu ({n}/{b.gunluk_tavan}); yarın (UTC) yeniden."
        _defter_yaz(_satir(an, b.ad, kanal, oturum, "kota_doldu", mesaj, cevap, kota_bugun=n,
                           hafiza_durumu="atlandi"))
        return cevap
    tasiyici = tasiyici or HermesTasiyici()
    giden = notify.scrub(mesaj)
    t0 = _saat()
    try:
        sonuc = tasiyici.sor(b.ad, giden, oturum)
    except Exception as e:  # sinyalli: defter `tur: hata` + sınıf adı, istisna YUKARI fırlar
        _defter_yaz(_satir(an, b.ad, kanal, oturum, "hata", mesaj, None, hata=type(e).__name__,
                           sure_s=round(_saat() - t0, 3), kota_bugun=n, hafiza_durumu="atlandi"))
        raise
    arac = sonuc.arac_cagrilari
    arac_olculemedi = arac is None
    # Sayı ölçülemediyse "araçsız veri mi" de BİLİNMEZ: False yazmak "temiz" demek olurdu (uydurma yasağı).
    isaret = veri_isareti(sonuc.metin)
    arac_siz_veri = None if arac_olculemedi else (arac == 0 and isaret is not None)
    cevap = _onekle(sonuc.metin, UYARI_OLCULEMEDI if arac_olculemedi else UYARI_ARACSIZ if arac_siz_veri else None)
    # `sure_s` taşıyıcı turunu ölçer — dönüş kaydının süresi ona KARIŞMAZ (model gecikmesi hafıza gecikmesinden
    # ayrı okunabilsin).
    sure_s = round(_saat() - t0, 3)
    donus = _donus_kaydi(b.ad, mesaj, cevap, kanal, arac_siz_veri, arac_olculemedi, hafiza)
    _defter_yaz(_satir(an, b.ad, kanal, oturum, "sohbet", mesaj, cevap,
                       sure_s=sure_s, arac_cagrilari=arac,
                       arac_siz_veri=arac_siz_veri, arac_olculemedi=arac_olculemedi, veri_isareti=isaret,
                       model_cagrilari=sonuc.model_cagrilari, kota_bugun=n + 1, **donus))
    return cevap
