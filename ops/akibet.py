#!/usr/bin/env python3
# akibet.py — öneri akıbet defteri: doğum→karar→sonuç zincirini A1'de TEK append-only defterde
# tutan komut-satırı aracı (listele · oneri · karar · sonuc). Emsal: ops/filo.py (saf-kurucu +
# tek `_kos` + kimlik CLI>env>sabit + `--komut-yaz` + nişancı-testli sözleşme) — desen BİREBİR
# izlenir, yeniden icat edilmez.
# Koşum: .venv/bin/python ops/akibet.py <altkomut> — meridian İTHAL ETMEZ (obs'a ulaşamaz).
# R1 düzeltme turu (inceleme 2026-08-31, task-1-review.md): okunamayan/boş defter ayrımı (K1),
# `sonuc` satırlarının listele'de yüzeye çıkması (Ö1), AKB id tahsisinin flock içine alınması
# (Ö2), zaman kıyasının gerçek datetime ile yapılması (Ö5), naive damganın UTC sayılması + geniş
# `except`in kaldırılması (Ö6). Ayrıntı: task-1-report.md "R1 düzeltmeleri".
"""akibet.py — öneri akıbet defterini TEK komut-satırı sözleşmesinden oku/yaz. LLM yok, tahmin yok.

NEDEN VAR (plan: docs/superpowers/plans/2026-08-31-akibet-defteri.md; karar kaydı: ROADMAP §7
"AKIBET DEFTERİ TASARIM KARARLARI"). Dört kaynaktan (hermes N-serisi önerileri · Rol-1 önerileri ·
operatör fikirleri · bot teslim kalemleri) doğan önerilerin doğum→karar→sonuç zinciri bugüne kadar
HİÇBİR YERDE tutulmuyordu: `state/improvement_proposals.jsonl` yalnız DOĞUMU taşır (N-serisi),
akıbeti (kabul/red/erteleme/sonuç) hiçbir defter kaydetmiyordu. Sef her brifingde "16 yeni öneri"
diye tekrar ediyordu çünkü karara bağlanmış bir önerinin bunu SÖYLEYECEK hiçbir yeri yoktu.

YAPI — SAF KURUCU + İNCE KABUK (filo.py deseniyle BİREBİR). ssh'a giden komut DİZGESİNİ kuran
fonksiyonlar saftır; alt-süreci koşan TEK yer `filo._kos`dur (`filo._ssh_kos` üzerinden çağrılır —
bkz. aşağıda) — bu araç kendi `subprocess.run` çağrısını YAPMAZ, filo'nunkini ÖDÜNÇ alır (üçüncü
bir alt-süreç noktası tek-kaynak yasasını ihlal ederdi). `akibet_turet` ise tamamen SAF bir
çekirdektir: hiçbir ssh/dosya erişimi yapmaz, zaten-okunmuş satırlardan türetim yapar — bu yüzden
T2 (`ops/oneri_brifingi.py`, A1'de koşan ve `meridian`i İTHAL EDEBİLEN taraf) onu doğrudan içe
aktarıp yerel dosya okumasıyla besleyebilir.

`meridian` İTHAL EDİLMEZ (filo.py'deki gibi): ithal edilseydi `meridian.obs` erişilebilir olurdu
ve bu araç pytest DIŞINDA, operatörün elinde koşuyor — canlı YEREL deftere yazardı (3 vaka,
2026-08-30, CLAUDE.md §2). Kimlik/ssh kurucuları (`varsayilan_host`, `varsayilan_anahtar`,
`ssh_sarmali`, `_kos`, `_ssh_kos`) `ops/filo.py`den İTHAL EDİLİR — ops/ paket DEĞİLDİR, bu yüzden
dosyanın KENDİ dizini `sys.path`e eklenip düz `import filo` yapılır (üçüncü bir A1-kimlik kopyası
YASAK).

DEFTER ŞEMASI (plan §Global Constraints, BAĞLAYICI) — `/opt/meridian/state/oneri_akibet.jsonl`,
append-only, UTF-8, satır=JSON, üç olay türü:
  `olay=oneri` : doğum satırı — `oneri_id` (AKB-#### öneki, yalnız N-serisi DIŞI kaynaklar için),
                 `kaynak` (rol1|operator), `oneri` (metin).
  `olay=karar` : `oneri_id`, `karar` (uygulandi|reddedildi|ertelendi), `gerekce`, `karar_veren`.
                 Aynı `oneri_id` için SON karar satırı geçerlidir (düzeltme = yeni satır, silme yok).
  `olay=sonuc` : `oneri_id`, `ozet`, opsiyonel `ref`. `akibet_turet`in DÖNÜŞÜNDE YÜZEYE ÇIKMAZ
                 (brief'in beyan ettiği şema `acik/kararlar/sayilar/olculemeyen`dir); `listele`
                 bunu KENDİ okuma katmanında ayrıca yüzeye çıkarır (bkz. `sonuclar`, Ö1 düzeltmesi).
N-serisi (`state/improvement_proposals.jsonl`, `id` alanı `N#####`) doğum kaydı KENDİ defterinde
KALIR — kopyalanmaz; akıbet defteri yalnız N-serisi DIŞI kaynakların doğumunu VE tüm kaynakların
karar/sonuç satırlarını taşır. AÇIK tanımı TÜRETİLİR: iki dosyanın doğurduğu id'ler kümesinden,
akıbet defterinde herhangi bir `karar` satırı taşıyan id'ler ÇIKARILIR (`ertelendi` dahil — bir
öneri ertelendiğinde AÇIK SAYILMAZ ama `sayilar`da görünür, plan md).

UZAK OKUMA — HER DOSYA KENDİ DURUM İŞARETİNİ TAŞIR (K1 düzeltmesi, inceleme 2026-08-31). Eski
şekil `cat ... 2>/dev/null; ...; true` idi: bu, "dosya yok" (meşru boş defter) ile "dosya var ama
okunamıyor" (izin/bozukluk — ÖLÇÜLEMEDİ) durumlarını AYNI sessiz boşluğa çöktürüyordu, ve
`sonraki_akb_id` bu sahte boşluğu "hiç öneri yok" sanıp sayacı SIFIRLIYORDU — yani bir izin hatası
yinelenen `AKB-0001` doğurabilirdi. Artık her `cat` `[ -e dosya ]` ile ÖNCE varlığı sorar, sonra
KENDİ çıkış kodunu bir işaretle basar (`_dosya_blogu`); `_ayir`/`_blok_ayikla` bunu üç duruma
ayrıştırır ("yok"=meşru boş, "ok"=okundu, "hata"=ÖLÇÜLEMEDİ) ve `_fetch_hukmu` "hata" durumunda
KIRMIZI döner — sıfır ile bilmiyorum burada ayrılır.

UZAK YAZIM (`karar`/`sonuc`) — TEK ŞABLON, ÇİFT `shlex.quote` (plan §Global Constraints):
  `flock <kilit> sh -c '<printf ile append + tail -1 ile geri-oku>'`
`flock <kilit> sh -c '...'` REMOTE kabuk tarafından BİR KEZ ayrıştırılır (dıştaki tek-tırnak
burada çözülür ve `sh`e TEK bir argv argümanı olarak gider); o argümanı `sh -c` İKİNCİ KEZ
ayrıştırır. Tek `shlex.quote` yalnız BİRİNCİ katmanı doğru kaçışlardı — JSON metnindeki bir `'`
(örn. bir önerinin içindeki kesme işareti, ya da v348 enjeksiyon çivisi sınıfının `"; DROP`
metni) ikinci katmanın sarmalını BÖLERDİ. Bu yüzden JSON önce kendi `sh -c` argümanı için
`shlex.quote`lanır, sonra o TÜM argüman (kendi kaçışlarıyla birlikte) OUTER `sh -c` argümanı
için bir KEZ DAHA `shlex.quote`lanır. YAZIM DOĞRULANIR: append sonrası `tail -1` ile geri okunan
satır, yazılmak istenen JSON ile BAYT BAYT kıyaslanır — RC'ye güvenilmez (v348'in "sahte başarı"
sınıfı: RC=0 dönüp de hiçbir şey yazmamış bir zincir buradan da geçebilirdi).

UZAK YAZIM (`oneri`) — AYNI flock kapsamında AKB İD TAHSİSİ (Ö2 düzeltmesi, inceleme 2026-08-31).
Eski şekil İKİ ayrı ssh çağrısıydı (fetch → yerel `sonraki_akb_id` → append): okuma ile yazma
arasındaki pencere korumasızdı, iki eşzamanlı `oneri` aynı max'ı okuyup AYNI id'yi üretebilirdi.
`oneri_ekleme_komutu` bunun yerine TEK ssh çağrısında, `flock`un İÇİNDE, uzak bir `python3 -c`
betiğiyle id hesaplar + JSON satırını yazar + geri okur. Kullanıcı metni ham Python kaynağına
KARIŞMAZ: `json.dumps` ile ASCII-kaçışlı TEK bir dize literaline gömülür, uzak taraf `json.loads`
ile geri çözer (aynı disiplin, farklı sarmal — shell yerine Python string literal güvenliği).

SAPMA BEYANI (Y6, yeniden-inceleme 2026-08-31 — KABUL-BEYANLA, koordinatör hükmü). Plan
(docs/superpowers/plans/2026-08-31-akibet-defteri.md §Global Constraints) uzak append için
**tek şablon** der ve o şablonu `printf … && tail -1` (yalnız `sh/flock/tail/cat/date` — sistem
araçları) olarak yazar. `oneri_ekleme_komutu` bunun DIŞINA çıkıyor: (a) İKİNCİ bir uzak append
şablonu getiriyor (`python3 -c '<program>'`, `printf`+`tail` DEĞİL) ve (b) planın listelemediği
bir uzak `python3` bağımlılığı ekliyor. Bu SESSİZE GEÇİLMEMELİ: iki gerekçeyle KABUL edilir —
(1) EMSAL zaten var: `ops/filo.py` A1'e `python3 -c '<program>'` gönderen bir yol taşıyor (durum
sorgusu için), yani A1'in interaktif-olmayan ssh PATH'inde `python3`ün var olduğu varsayımı bu
depoda YENİ değil; (2) R1 incelemesinin Ö2 kapatma yönü ("max hesabını da kilidin içine al") bunu
zaten YETKİLENDİRİYOR — `printf`+`tail` ile AKB id hesaplaması (regex/max tarama) TEK ssh çağrısı
İÇİNDE atomik biçimde YAPILAMAZ, sistem araçlarıyla bu iş İKİ ayrı ssh çağrısı (Ö2'nin tam
kapatmak istediği yarış durumu) gerektirirdi. Ölçülmemiş kalan: A1'in GERÇEK interaktif-olmayan
ssh PATH'inde `python3`ün çözüldüğü bu dalgada DOĞRULANMADI (yalnız filo.py emsali dolaylı kanıt)
— Rol-1'in kapanış kalemi #23 (`listele`yi operatör biçiminde bir kez gerçekten koşmak) `oneri
--komut-yaz` çıktısını da elle koşarak bunu kapatır.

Gerçek ssh testte HİÇ ÇAĞRILMAZ (v348'in nişancı deseni): PATH'e gerçek bir `ssh` betiği konur,
davranış ÖLÇÜLÜR, iddia EDİLMEZ.

ÇIKIŞ KODLARI (sözleşme): 0=başarı · 1=doğrulama kırmızısı · 2=kullanım hatası (argparse'ın
kendisi verir: `choices=`/`required=` ihlalleri). Dispatch'in KENDİSİ artık geniş bir
`except (ValueError, TypeError)` ile SARILMAZ (Ö6 düzeltmesi): eskiden bu, offset'siz-ama-geçerli
bir ISO-8601 damgasından doğan bir `TypeError`ı "kullanım hatası" diye YANLIŞ etiketliyordu — oysa
hiçbir CLI argümanı burada sayısal ayrıştırma GEÇİRMİYOR (filo'nun `-n` bayrağının aksine); bu
modülde `except`in koruyacağı gerçek bir "kullanıcı argümanı argparse'ı atlattı" yolu YOK. Bir
internal hata artık ÇIPLAK bir traceback olarak görünür — bu, "araç çöktü" ile "kullanım hatalı"yı
birbirine KARIŞTIRMAMAK için daha dürüst bir sessizlik-yok disiplinidir.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import sys
from datetime import datetime, timezone

# ops/ PAKET DEĞİL: `filo.py`nin kimlik/ssh kurucularını (varsayilan_host/varsayilan_anahtar/
# ssh_sarmali/_kos/_ssh_kos) İTHAL etmek için dosyanın KENDİ dizinini sys.path'e ekleyip düz
# `import filo` yapıyoruz — göreli import paket bağı gerektirirdi, ops/ bir paket değil. ÜÇÜNCÜ
# bir A1-kimlik kopyası YASAK (filo.py zaten ikinci kopyayı iki kardeş betikle
# (`pull-a1-backups.sh`, `state_yetim_temizle.sh`) paylaşan env adlarını taşıyor; burası
# üçüncüsünü YARATMAZ).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import filo  # noqa: E402

#: DEFTERİN TEK KAYNAĞI — A1'deki mutlak yol (plan §Global Constraints, BAĞLAYICI). Görece bir
#: ad `config.STATE`e bağlı olurdu; bu araç `meridian`i ithal edemediği için mutlak yazılır.
DEFTER = "/opt/meridian/state/oneri_akibet.jsonl"
#: `flock` KİLİDİ — defterin YANINDA, `.lock` soneki: aynı isim gövdesinden türer, ikinci bir
#: sabit isim uydurmaz.
KILIT = DEFTER + ".lock"
#: N-serisi (hermes) önerilerinin DOĞUM defteri — buraya YAZILMAZ, yalnız `listele`/`karar`/
#: `sonuc` türetim için OKUR.
PROPOSALS = "/opt/meridian/state/improvement_proposals.jsonl"

#: Uzak `cat` çıktısında iki dosyayı ayıran işaret — `durum_ayristir`in `AYRAC`ıyla AYNI sınıf
#: (filo.py): sıra varsayımı yerine AÇIK bir ayraç, biri boşsa öteki onun alanlarını devralmaz.
FETCH_AYRAC = "@@AKIBET-DEFTER@@"
#: Her dosyanın KENDİ okunabilirlik durumunu taşıyan işaretler (K1 düzeltmesi). "yok" (dosya hiç
#: yok — MEŞRU boş) ile "var ama okunamadı" (izin/bozukluk — ÖLÇÜLEMEDİ) AYRI sınıflardır.
PROPOSALS_ISARET = "@@PROPOSALS-DURUM"
DEFTER_ISARET = "@@DEFTER-DURUM"

#: Karar sözlüğünün TEK KAYNAĞI — hem CLI `choices=`ı hem `akibet_turet`in geçerlilik denetimi
#: BURADAN türer; ikinci bir liste ikinci bir gerçek yaratırdı.
KARARLAR = ("uygulandi", "reddedildi", "ertelendi")
#: `--kaynak` (oneri doğum kaynağı) — plan satır şeması altı değer sayıyor (hermes_reflect
#: hariç, N-serisi dışı: rol1/operator/sef/bekci/karne); bu dalga yalnız ilk ikisini AÇAR.
ONERI_KAYNAKLARI = ("rol1", "operator")
#: `karar_veren`/`--veren` (kararı VEREN taraf) — plan bunu AYRI ve YALNIZ iki değerle tanımlıyor
#: (Ö4 düzeltmesi, inceleme 2026-08-31). Bugün `ONERI_KAYNAKLARI` ile AYNI değerleri taşısa da
#: TESADÜFİDİR: bot teslim kalemleri `ONERI_KAYNAKLARI`na eklendiğinde `KARAR_VERENLER` SESSİZCE
#: genişlemesin diye ayrı sabitlenir — tek sabitte birleştirmek tek-kaynak yasasının TERSİYDİ
#: (iki gerçeği bir kopyaya sıkıştırmak).
KARAR_VERENLER = ("operator", "rol1")

#: Gerekçesiz "uygulandi" bir sonraki okuyucuya hiçbir şey anlatmaz (Yasa 4 disiplini karar
#: satırına da taşınır). Eşik burada TEK SAYI: CLI denetimi ve testler AYNI sabitten okur.
GEREKCE_ASGARI = 20

#: `oneri_id` biçimi — yalnız N-serisi DIŞI kaynaklar (rol1/operator) için üretilir.
AKB_ONEKI = "AKB-"
_AKB_DESENI = re.compile(rf"^{re.escape(AKB_ONEKI)}(\d+)$")


# ─────────────────────────────────────────────────────────────────────────────
#  zaman
# ─────────────────────────────────────────────────────────────────────────────

def _simdi() -> str:
    """ÇAĞRI ANINDA hesaplanır — modül yüklenirken DEĞİL, aksi hâlde tüm bir CLI koşumu tek bir
    donmuş ana bağlanırdı."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _ts_ayristir(ts) -> datetime | None:
    """ISO8601 → tz-aware `datetime`. Ayrıştırılamazsa `None` — UYDURMA YASAĞI: bir yaş İCAT
    ETMEZ. Naive (dilimsiz) ama GEÇERLİ bir damga UTC SAYILIR (Ö6 düzeltmesi, inceleme
    2026-08-31): eskiden naive sonuç ÇIPLAK dönüyordu ve `simdi - dogum_ts` (biri aware biri
    naive) `TypeError` atıyordu — modülün TEK üreticisi (`nous_eval.py`) zaten aware yazıyor;
    delik yalnız elle düzenlenmiş/ikinci-üreticili bir defterde açılırdı."""
    if not isinstance(ts, str) or not ts:
        return None
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


def _ts_sira_anahtari(ts) -> tuple:
    """`(cozulebildi_mi, datetime)` — GERÇEK zaman kıyası için (Ö5 düzeltmesi, inceleme
    2026-08-31). Eskiden `str(ts)` DİZGE olarak kıyaslanıyordu: `+03:00` ve `+00:00` offsetli iki
    damga aynı GERÇEK anı farklı yerel saatlerle gösterebilir ve dizge sırası GERÇEK kronolojiyle
    ÇELİŞEBİLİR (`"...T10...+03:00"` dizgesel BÜYÜK görünür ama `"...T08...+00:00"` GERÇEKTE daha
    GEÇtir). Ayrıştırılamayan ts EN ESKİ sayılır — uydurma yasağı: bilinmeyen an 'en yeni'
    SAYILAMAZ, `son_karar` seçimini ya da `kararlar` sırasını haksız yere ELE GEÇİREMEZ.

    Y2 DÜZELTMESİ (yeniden-inceleme 2026-08-31): İLK sürüm `(dt is None, ...)` döndürüyordu —
    kutbu docstring'in TAM TERSİYDİ: `True > False` olduğundan ayrıştırılamayan `ts` (anahtarı
    `(True, datetime.min)`) artan sıralamada EN SONA düşüyordu, yani "EN YENİ" sayılıyor ve
    `son_karar` karşılaştırmasında (>=) HER ZAMAN kazanıyordu — tam da docstring'in yasakladığı
    şey. Artık `(dt is not None, ...)`: ayrıştırılamayan `ts` `(False, min)` ile EN KÜÇÜK anahtarı
    taşır, `>=` karşılaştırmasında GEÇERLİ damgalı hiçbir satıra karşı ASLA kazanamaz — giriş
    sırasından BAĞIMSIZ (bkz. `test_b17`, iki sırayı da dener).

    KARAR (beyan, koordinatör istegi): bozuk-ts taşıyan bir `karar` satırı `olculemeyen`e
    SAYILMAZ — `kararlar`da KALIR, yalnız sıralama/`son_karar` yarışını HER ZAMAN kaybeder. Bu,
    doğum satırları için ZATEN kurulu olan emsalle (`test_b9`: ts-ayrıştırılamayan bir `oneri`
    doğumu `acik`ten DÜŞMEZ, yalnız `yas_gun=None` olur) TUTARLIDIR — ts-ayrıştırılamazlığı bu
    modülde hiçbir yerde YAPISAL bir bozukluk (`olculemeyen`in ölçütü: gerekli alan YOK) SAYILMAZ,
    yalnız o alanı KULLANAN türetimi (yaş, sıralama) `None`/en-düşük-öncelik yapar. `oneri_id`,
    `karar`, `karar_veren`, `gerekce` hâlâ geçerliyse satırın KENDİSİ tam bir karardır — yalnız
    ONU NE ZAMAN verildiği bilinmiyor."""
    dt = _ts_ayristir(ts)
    return (dt is not None, dt or datetime.min.replace(tzinfo=timezone.utc))


# ─────────────────────────────────────────────────────────────────────────────
#  jsonl ayrıştırma — SAF, ssh'sız
# ─────────────────────────────────────────────────────────────────────────────

def _jsonl_satirlari(metin: str) -> list[dict]:
    """Ham JSONL metni → sözlük listesi. Boş satır atlanır (dosyanın doğal biçimi, bozukluk
    DEĞİL). Çözülemeyen/sözlük-olmayan satır DÜŞÜRÜLMEZ: yerine BOŞ sözlük `{}` konur —
    `akibet_turet` boş sözlüğü zaten 'gerekli alan yok' diye ölçülemez sayar ve POZİSYONUNU
    `olculemeyen`e ekler (v347 emsali: sessiz `continue` yerine İZLİ, konumu koruyan bir yer
    tutucu; bkz. `meridian/api.py::_ajan_teslimleri`'nin aynı sınıf 'bozuk satır TÜM defteri
    düşürmez' disiplini)."""
    satirlar: list[dict] = []
    for satir in metin.splitlines():
        if not satir.strip():
            continue
        try:
            ham = json.loads(satir)
        except ValueError:
            ham = {}
        satirlar.append(ham if isinstance(ham, dict) else {})
    return satirlar


def _dosya_blogu(yol: str, isaret: str) -> str:
    """Tek dosya için: varsa `cat` + KENDİ çıkış kodu işareti, yoksa `YOK` işareti (K1 düzeltmesi).
    RC'ye değil `cat`ın KENDİ çıkış koduna bakılır — dosya var ama izinsizse de `cat` RC≠0 verir
    ve bu "yok" (meşru boş) DEĞİL "hata" (ÖLÇÜLEMEDİ) sayılmalıdır."""
    y = shlex.quote(yol)
    return (f"if [ -e {y} ]; then cat {y}; rc=$?; printf '\\n{isaret} rc=%s\\n' \"$rc\"; "
            f"else printf '{isaret} YOK\\n'; fi")


def okuma_komutu() -> str:
    """Tek uzak komut, salt-okuma: PROPOSALS + `FETCH_AYRAC` + DEFTER — HER İKİSİ de kendi durum
    işaretini taşır (bkz. `_dosya_blogu`, `_blok_ayikla`, `_fetch_hukmu` — K1 düzeltmesi). Eski
    şekil (`2>/dev/null; ...; true`) "dosya yok" ile "dosya var ama okunamadı"yı AYNI sessiz
    boşluğa çöktürüyordu; artık ikisi AYRI işaretlerle döner."""
    return (f"{_dosya_blogu(PROPOSALS, PROPOSALS_ISARET)}; "
            f"echo {shlex.quote(FETCH_AYRAC)}; "
            f"{_dosya_blogu(DEFTER, DEFTER_ISARET)}")


def _blok_ayikla(metin: str, isaret: str) -> tuple[str, str]:
    """(içerik, durum) — durum ∈ {"ok","yok","hata"}. İşaret satırı hiç yoksa (ölçülmemiş bir
    uzak çıktı biçimi) `"hata"` sayılır: doğrulanamayan bir okuma BAŞARILI sayılmaz."""
    satirlar = metin.splitlines()
    for i in range(len(satirlar) - 1, -1, -1):
        if satirlar[i].startswith(isaret):
            kalan = satirlar[i][len(isaret):].strip()
            # `splitlines()` + `"\n".join(...)` TAM TERSİNİ alır: orijinal `cat` çıktısı
            # (trailing newline dahil, `_dosya_blogu`'nun `printf '\n...'` öneki sayesinde ARADA
            # her zaman bir satır kalır) BAYT BAYT geri kurulur — ayrıca bir `"\n"` EKLEMEK
            # burada FAZLADAN bir boş satır üretirdi (ölçüldü, düzeltildi).
            icerik = "\n".join(satirlar[:i])
            if kalan == "YOK":
                return icerik, "yok"
            m = re.match(r"rc=(\d+)$", kalan)
            if m and m.group(1) == "0":
                return icerik, "ok"
            return icerik, "hata"
    return metin, "hata"


def _ayir(cikti: str) -> dict:
    """Uzak birleşik çıktıyı `FETCH_AYRAC`tan böler ve HER iki bölümü kendi işaretiyle ayrıştırır
    → `{"proposals_metin","proposals_durum","defter_metin","defter_durum"}` (K1 düzeltmesi;
    eskiden `tuple[str, str]` dönerdi ve durum bilgisi YOKTU)."""
    if FETCH_AYRAC in cikti:
        once, sonra = cikti.split(FETCH_AYRAC, 1)
        sonra = sonra.split("\n", 1)[1] if "\n" in sonra else ""
    else:
        once, sonra = cikti, ""
    p_metin, p_durum = _blok_ayikla(once, PROPOSALS_ISARET)
    d_metin, d_durum = _blok_ayikla(sonra, DEFTER_ISARET)
    return {"proposals_metin": p_metin, "proposals_durum": p_durum,
           "defter_metin": d_metin, "defter_durum": d_durum}


def _fetch_hukmu(ayrilmis: dict) -> tuple[bool, str]:
    """`(ok, neden)` — herhangi bir dosya "hata" durumundaysa KIRMIZI (K1 düzeltmesi, inceleme
    2026-08-31 KRİTİK bulgusu): "sıfır" ile "bilmiyorum" burada ayrılır. Bu hüküm KIRMIZIYSA
    çağıran hiçbir sayaç/karar/açık hesaplamasını bu okumaya DAYANDIRMAZ — AKB sayacı ASLA bir
    okuma hatasından `AKB-0001`e sıfırlanmaz."""
    sorunlu = [ad for ad in ("proposals", "defter") if ayrilmis[f"{ad}_durum"] == "hata"]
    if sorunlu:
        return False, (f"ÖLÇÜLEMEDİ: {', '.join(sorunlu)} okunamadı (dosya var ama erişilemedi ya "
                       "da beklenmeyen biçimde döndü) — sıfır SAYILMAZ, hiçbir sayaç/karar bu "
                       "okumaya dayanarak ilerletilmez")
    return True, "ok"


# ─────────────────────────────────────────────────────────────────────────────
#  SAF ÇEKİRDEK — T2 (`ops/oneri_brifingi.py`) BUNU İTHAL EDER
# ─────────────────────────────────────────────────────────────────────────────

def akibet_turet(proposals_satirlari: list[dict], defter_satirlari: list[dict],
                 simdi_ts: str) -> dict:
    """→ {"acik": [{"oneri_id","kaynak","yas_gun","ozet"}...],   # yaş = doğumdan bugüne, tam gün
         "kararlar": [{"oneri_id","karar","karar_veren","ts","gerekce"}...],  # ts sıralı, TÜM tarihçe
         "sayilar": {"acik": n, "uygulandi": n, "reddedildi": n, "ertelendi": n}}
    Bozuk satır DÜŞÜRÜLMEZ: {"olculemeyen": [satir_no...]} alanına sayılır (v347 emsali).

    SAF: hiçbir dosya/ssh erişimi yapmaz — girdi ZATEN ayrıştırılmış satır listeleridir.

    "Bozuk" TEK ÖLÇÜTLE tanımlanır: satırı işlemek için gereken alanlar YOK. Bu, hem JSON
    çözme hatasından gelen `{}` yer tutucularını (bkz. `_jsonl_satirlari`) HEM DE sözdizimsel
    olarak geçerli ama semantik olarak eksik bir satırı (örn. `oneri_id`siz bir `karar`) AYNI
    çatı altında yakalar — iki ayrı "bozukluk" sınıfı icat etmek ikinci bir gerçek yaratırdı.

    `satir_no`, satırın KENDİ listesindeki 1-tabanlı POZİSYONUDUR (proposals ve defter ayrı
    numaralanır, `olculemeyen` ikisini TEK listede birleştirir) — çağıran hangi dosyadan
    geldiğini bağlamdan bilir (`listele` iki fetch'i ayrı ayrı besler).

    `olay=sonuc` satırları GEÇERLİ sayılır ama bu türetimin DÖNÜŞÜNDE yer ALMAZ: brief'in beyan
    ettiği şema `acik/kararlar/sayilar/olculemeyen`dir, sonuç metni ledger'da durur (`listele`
    onu KENDİ okuma katmanında ayrıca yüzeye çıkarır — bkz. `sonuclar`, Ö1 düzeltmesi).

    ZAMAN KIYASI GERÇEK `datetime` İLEDİR (Ö5 düzeltmesi): `son_karar` seçimi ve `kararlar`
    sıralaması `_ts_sira_anahtari` kullanır — DİZGE kıyası farklı UTC-offsetli iki damgada
    KRONOLOJİYLE ÇELİŞEBİLİRDİ.
    """
    simdi = _ts_ayristir(simdi_ts)
    if simdi is None:
        raise ValueError(f"simdi_ts ayrıştırılamadı: {simdi_ts!r}")

    dogumlar: dict[str, dict] = {}   # oneri_id -> {"kaynak","ts","ozet"}
    olculemeyen: list[int] = []

    for i, row in enumerate(proposals_satirlari, start=1):
        if not isinstance(row, dict) or "id" not in row or "ts" not in row:
            olculemeyen.append(i)
            continue
        dogumlar[row["id"]] = {"kaynak": "hermes_reflect", "ts": row["ts"],
                               "ozet": row.get("oneri")}

    kararlar: list[dict] = []
    son_karar: dict[str, dict] = {}   # oneri_id -> EN SON karar satırı (gerçek zaman sırasıyla)

    for i, row in enumerate(defter_satirlari, start=1):
        if not isinstance(row, dict) or "ts" not in row or "olay" not in row:
            olculemeyen.append(i)
            continue
        olay = row["olay"]
        if olay == "oneri":
            if "oneri_id" not in row:
                olculemeyen.append(i)
                continue
            dogumlar[row["oneri_id"]] = {"kaynak": row.get("kaynak"), "ts": row["ts"],
                                         "ozet": row.get("oneri")}
        elif olay == "karar":
            if "oneri_id" not in row or row.get("karar") not in KARARLAR:
                olculemeyen.append(i)
                continue
            girdi = {"oneri_id": row["oneri_id"], "karar": row["karar"],
                     "karar_veren": row.get("karar_veren"), "ts": row["ts"],
                     "gerekce": row.get("gerekce")}
            kararlar.append(girdi)
            onceki = son_karar.get(row["oneri_id"])
            if onceki is None or _ts_sira_anahtari(row["ts"]) >= _ts_sira_anahtari(onceki["ts"]):
                son_karar[row["oneri_id"]] = girdi
        elif olay == "sonuc":
            if "oneri_id" not in row:
                olculemeyen.append(i)
            # geçerli `sonuc` satırı: BİLİNÇLİ OLARAK hiçbir şey biriktirilmez (dönüş şeması yok)
        else:
            olculemeyen.append(i)

    kararlar.sort(key=lambda k: (_ts_sira_anahtari(k["ts"]), str(k["oneri_id"])))

    acik = []
    for oneri_id, dogum in dogumlar.items():
        if oneri_id in son_karar:
            continue
        dogum_ts = _ts_ayristir(dogum["ts"])
        yas_gun = (simdi - dogum_ts).days if dogum_ts is not None else None
        acik.append({"oneri_id": oneri_id, "kaynak": dogum["kaynak"], "yas_gun": yas_gun,
                     "ozet": dogum["ozet"]})
    # AZALAN yaş sırası (en eski önce) — bilinmeyen yaş (None) EN SONA düşer, uydurulmaz.
    acik.sort(key=lambda a: (a["yas_gun"] is None, -(a["yas_gun"] or 0), a["oneri_id"]))

    sayilar = {"acik": len(acik), "uygulandi": 0, "reddedildi": 0, "ertelendi": 0}
    for k in son_karar.values():
        sayilar[k["karar"]] += 1

    return {"acik": acik, "kararlar": kararlar, "sayilar": sayilar, "olculemeyen": olculemeyen}


def sonuclar(defter_satirlari: list[dict]) -> list[dict]:
    """`olay=sonuc` satırlarının ts sıralı özeti (Ö1 düzeltmesi, inceleme 2026-08-31 — Yasa 6
    bulgusu). `sonuc` alt komutu `ozet`/`ref` yazıyordu ama `akibet_turet`in dönüşünde YOKTUR ve
    hiçbir yüzey okumuyordu. `akibet_turet`in ŞEMASINI GENİŞLETMEDEN (brief'in beyan ettiği dönüş
    sabit kalır): `listele`nin KENDİ okuma katmanında, ham defter satırlarından ayrıca süzülür —
    yeni alt komut yok, kapsam genişletme yok."""
    out = []
    for row in defter_satirlari:
        if isinstance(row, dict) and row.get("olay") == "sonuc" and "oneri_id" in row:
            out.append({"oneri_id": row["oneri_id"], "ozet": row.get("ozet"),
                       "ref": row.get("ref"), "ts": row.get("ts")})
    out.sort(key=lambda s: _ts_sira_anahtari(s["ts"]))
    return out


# ─────────────────────────────────────────────────────────────────────────────
#  AKB kimlik sayacı — SAF, çakışmasız (referans; uzak script AYNI algoritmayı taşır)
# ─────────────────────────────────────────────────────────────────────────────

def sonraki_akb_id(defter_satirlari: list[dict]) -> str:
    """Defterdeki EN BÜYÜK `AKB-####` + 1. Boş defterde `AKB-0001`den başlar.

    TÜM satırlardaki `oneri_id` alanı taranır (yalnız `olay=oneri` DEĞİL): bozuk bir defterde
    doğum satırı kaybolmuş olsa bile (örn. yalnız karar/sonuç satırı hayatta kaldıysa) numara
    GERİYE gitmez — `max+1` GAP'LERİ de doğru ele alır (numaralandırma sıralı değil, en büyüğe
    bağlıdır: `AKB-0005` tek başına bulunsa bile sıradaki `AKB-0006`dır, `AKB-0002` DEĞİL).

    CLI BUNU ARTIK DOĞRUDAN ÇAĞIRMAZ (Ö2 düzeltmesi, inceleme 2026-08-31): id tahsisi
    `oneri_ekleme_komutu`nun REMOTE python betiğine taşındı (aynı flock kapsamında, eşzamanlılık
    çakışmasını kapatmak için). Bu fonksiyon REFERANS/spesifikasyon olarak kalır ve uzak betiğin
    AYNI algoritmayı taşıdığı çapraz-çivi ile denetlenir (kaçınılmaz kopya — iki ayrı çalışma
    zamanı, tek-kaynak yasasının izin verdiği istisna sınıfı, bkz. testler)."""
    en_buyuk = 0
    for row in defter_satirlari:
        if not isinstance(row, dict):
            continue
        m = _AKB_DESENI.match(str(row.get("oneri_id", "")))
        if m:
            en_buyuk = max(en_buyuk, int(m.group(1)))
    return f"{AKB_ONEKI}{en_buyuk + 1:04d}"


def gerekce_gecerli_mi(gerekce: str) -> bool:
    """Yasa 4 disiplini karar satırına taşınır: `GEREKCE_ASGARI`nin altı bir sonraki okuyucuya
    hiçbir şey anlatmaz ('tamam', 'ok' gibi)."""
    return len((gerekce or "").strip()) >= GEREKCE_ASGARI


# ─────────────────────────────────────────────────────────────────────────────
#  uzak şablonlar — SAF (argv/dizge kurar, KOŞMAZ)
# ─────────────────────────────────────────────────────────────────────────────

def ekleme_komutu(satir: dict) -> str:
    """`flock <kilit> sh -c '<printf-append + tail-1-doğrulama>'` — TEK ŞABLON (plan, BAĞLAYICI).
    `karar`/`sonuc` için kullanılır (id ÖNCEDEN bilinir, yalnız kullanıcı içeriği kaçışlanır).

    ÇİFT `shlex.quote` ZORUNLU (modül docstring'inde ayrıntılı gerekçe): JSON önce `sh -c`nin
    KENDİ argümanı olarak kaçışlanır (`ic`), sonra TÜM `ic` (kendi kaçış dizgileriyle birlikte)
    OUTER kabuk için bir KEZ DAHA kaçışlanır. Tek katman, JSON içinde bir `'` (kesme işareti ya
    da v348 enjeksiyon çivisi sınıfının `"; DROP` metni) taşıyan bir öneride sarmalı BÖLERDİ.

    Biçim dizgesi TEK TIRNAKLIDIR: kabuk dışında çıplak yazılsaydı POSIX kaçış kuralı ters eğik
    çizgiyi YUTAR ve printf'e yalnız harf giderdi — biçim dizgesindeki satır-sonu kaçışı
    kaybolurdu.
    """
    json_metin = json.dumps(satir, ensure_ascii=False, sort_keys=True)
    ic = (f"printf '%s\\n' {shlex.quote(json_metin)} >> {shlex.quote(DEFTER)} "
          f"&& tail -1 {shlex.quote(DEFTER)}")
    return f"flock {shlex.quote(KILIT)} sh -c {shlex.quote(ic)}"


def oneri_ekleme_komutu(kaynak: str, metin: str, ts: str) -> str:
    """`oneri` için TEK ssh çağrısı: AKB id tahsisi + JSON satırı + append + geri-okuma doğrulaması
    AYNI `flock` kapsamında (Ö2 düzeltmesi, inceleme 2026-08-31 ÖNEMLİ bulgusu). Eski akış
    (fetch → yerel `sonraki_akb_id` → `ekleme_komutu`) İKİ ayrı ssh çağrısıydı; okuma ile yazma
    arasındaki pencere KORUMASIZDI — iki eşzamanlı `oneri` aynı max'ı okuyup AYNI id'yi
    üretebilirdi. Burada id hesaplaması da REMOTE `python3` içinde, kilidin İÇİNDE yapılır.

    Kullanıcı metni (kaynak/oneri/ts) LOKAL olarak TEK bir JSON dizgesine kodlanıp, o dizge
    KENDİSİ `json.dumps` ile (ASCII-kaçışlı) bir Python dize LİTERALİ olarak uzak kaynağa gömülür
    — kullanıcı metni asla ham Python kaynağına karışmaz, uzak taraf `json.loads` ile tek parça
    geri çözer. Uzak scriptin çıktısı `sys.stdout.buffer` üzerinden HAM BAYT olarak yazılır (metin
    modunda `print` değil): uzak `python3` C-locale altında koşarsa metin-modu `print` ASCII dışı
    içerikte `UnicodeEncodeError` ile ölür (filo.py'nin ayrı python3 betiklerinde belgelenen aynı
    tuzak) — bayt yazımı locale'den bağımsızdır, `cat`/`tail` gibi.

    Algoritma `sonraki_akb_id` ile AYNIDIR (max+1, `oneri_id` tüm satırlarda taranır) — iki ayrı
    çalışma zamanında (yerel Python / uzak Python) kaçınılmaz bir kopya; ayrışması çapraz-çivi ile
    denetlenir (testler).
    """
    yuk_json = json.dumps({"ts": ts, "kaynak": kaynak, "oneri": metin}, ensure_ascii=False)
    program = "\n".join([
        "import json, re, sys",
        f"yuk = json.loads({json.dumps(yuk_json)})",
        f"defter = {json.dumps(DEFTER)}",
        "try:",
        "    ham = open(defter, encoding='utf-8').read()",
        "except FileNotFoundError:",
        "    ham = ''",
        "en_buyuk = 0",
        "for satir in ham.splitlines():",
        "    satir = satir.strip()",
        "    if not satir:",
        "        continue",
        "    try:",
        "        row = json.loads(satir)",
        "    except ValueError:",
        "        continue",
        "    if isinstance(row, dict):",
        "        m = re.match(r'^AKB-(\\d+)$', str(row.get('oneri_id', '')))",
        "        if m:",
        "            en_buyuk = max(en_buyuk, int(m.group(1)))",
        "yeni_id = 'AKB-%04d' % (en_buyuk + 1)",
        "satir_dict = {'ts': yuk['ts'], 'olay': 'oneri', 'oneri_id': yeni_id, "
        "'kaynak': yuk['kaynak'], 'oneri': yuk['oneri']}",
        "satir_json = json.dumps(satir_dict, ensure_ascii=False, sort_keys=True)",
        "with open(defter, 'a', encoding='utf-8') as f:",
        "    f.write(satir_json + chr(10))",
        "with open(defter, encoding='utf-8') as f:",
        "    son = [x for x in f.read().splitlines() if x.strip()][-1]",
        "sys.stdout.buffer.write((son + chr(10)).encode('utf-8'))",
    ])
    ic = "python3 -c " + shlex.quote(program)
    return f"flock {shlex.quote(KILIT)} sh -c {shlex.quote(ic)}"


def yazim_dogrulandi(cikti: str, satir: dict) -> tuple[bool, str]:
    """Geri okunan (`tail -1`) son satır, YAZILMAK İSTENEN JSON ile BAYT BAYT eşleşmeli.
    RC'YE GÜVENİLMEZ (v348 sahte-başarı sınıfı): `flock`/`printf` zinciri RC=0 dönüp de hiçbir
    şey yazmamış olabilir (disk dolu, izin, kesik boru) — hüküm ÇIKTIDAN verilir. `karar`/`sonuc`
    için: id ÖNCEDEN bilindiğinden TAM EŞİTLİK ölçülür (`oneri` için bkz. `oneri_yazim_dogrulandi`,
    orada id ÖNCEDEN bilinmez)."""
    beklenen = json.dumps(satir, ensure_ascii=False, sort_keys=True)
    satirlar = [s for s in cikti.splitlines() if s.strip()]
    son = satirlar[-1] if satirlar else ""
    if son != beklenen:
        return False, (f"YAZIM DOĞRULANAMADI: geri okunan son satır beklenenle eşleşmiyor — "
                       f"beklenen={beklenen!r} geri-okunan={son!r}")
    return True, "yazım doğrulandı: geri okunan satır beklenenle bayt bayt eşleşti"


def oneri_yazim_dogrulandi(cikti: str, kaynak: str, metin: str) -> tuple[bool, str, str | None]:
    """(ok, neden, atanan_id). `oneri`de id ÖNCEDEN BİLİNMEZ (kilidin içinde REMOTE hesaplanır) —
    doğrulama tam eşitlik DEĞİL: geri okunan son satırın BEKLENEN alanları (olay/kaynak/oneri)
    taşıdığı VE `oneri_id`sinin `AKB-####` biçiminde olduğudur."""
    satirlar = [s for s in cikti.splitlines() if s.strip()]
    son = satirlar[-1] if satirlar else ""
    try:
        row = json.loads(son)
    except ValueError:
        return False, f"YAZIM DOĞRULANAMADI: geri okunan son satır JSON değil: {son!r}", None
    if not isinstance(row, dict):
        return False, f"YAZIM DOĞRULANAMADI: geri okunan satır sözlük değil: {son!r}", None
    atanan_id = row.get("oneri_id")
    if (row.get("olay") != "oneri" or row.get("kaynak") != kaynak or row.get("oneri") != metin
            or not _AKB_DESENI.match(str(atanan_id))):
        return False, (f"YAZIM DOĞRULANAMADI: geri okunan satır beklenen alanları taşımıyor: "
                       f"{row!r}"), None
    return True, "yazım doğrulandı: geri okunan satır beklenen alanları taşıyor", atanan_id


# ─────────────────────────────────────────────────────────────────────────────
#  çıktı biçimi — SAF (CLI yalnız BASAR)
# ─────────────────────────────────────────────────────────────────────────────

def listele_metni(turev: dict, sonuc_satirlari: list[dict] = ()) -> str:
    """(basılacak_metin) — SAF, filo.py::durum_raporu ile AYNI ayrım: tablo + özet TEK yerde
    birleşir ki çivi CLI'ın gerçekten ne bastığını ölçebilsin. `sonuc_satirlari` opsiyoneldir
    (Ö1 düzeltmesi) — `akibet_turet`in şemasını genişletmeden `sonuclar()` çıktısını basar."""
    parca = []
    if not turev["acik"]:
        parca.append("(açık öneri yok)")
    else:
        basliklar = ("oneri_id", "kaynak", "yas_gun", "ozet")
        satirlar = [basliklar]
        for a in turev["acik"]:
            satirlar.append((a["oneri_id"], str(a["kaynak"] or "ÖLÇÜLEMEDİ"),
                             str(a["yas_gun"]) if a["yas_gun"] is not None else "ÖLÇÜLEMEDİ",
                             # `None` ile "özet gerçekten boş" AYNI DEĞİLDİR (Kü4 düzeltmesi):
                             # `kaynak`/`yas_gun` ile TUTARLI olarak "ÖLÇÜLEMEDİ" basılır.
                             str(a["ozet"]) if a["ozet"] is not None else "ÖLÇÜLEMEDİ"))
        genislik = [max(len(s[i]) for s in satirlar) for i in range(len(basliklar))]
        for s in satirlar:
            parca.append("  ".join(str(h).ljust(genislik[i]) for i, h in enumerate(s)))
    parca.append("")
    parca.append("son 5 karar:")
    son5 = list(reversed(turev["kararlar"][-5:]))
    if not son5:
        parca.append("  (hiç karar yok)")
    for k in son5:
        parca.append(f"  {k['ts']} · {k['oneri_id']} · {k['karar']} · {k['karar_veren']} "
                     f"· {k['gerekce']}")
    parca.append("")
    parca.append("son sonuçlar:")
    son_sonuc5 = list(reversed(list(sonuc_satirlari)[-5:]))
    if not son_sonuc5:
        parca.append("  (hiç sonuç yok)")
    for s in son_sonuc5:
        ref_parcasi = f" · ref={s['ref']}" if s.get("ref") is not None else ""
        # Y4 düzeltmesi (yeniden-inceleme 2026-08-31): açık tablosundaki Kü4 disiplini burada
        # TEKRARLANMAMIŞTI — `sonuclar()` yalnız `oneri_id`yi zorunlu tutar, `ts`/`ozet` eksik
        # olabilir; eskiden bu satır `None`u OLDUĞU GİBİ basardı ("alan yok" ile "gerçekten None
        # metni" karışırdı). Artık AYNI "ÖLÇÜLEMEDİ" sözleşmesi burada da geçerli.
        ts_metni = s["ts"] if s["ts"] is not None else "ÖLÇÜLEMEDİ"
        ozet_metni = s["ozet"] if s["ozet"] is not None else "ÖLÇÜLEMEDİ"
        parca.append(f"  {ts_metni} · {s['oneri_id']} · {ozet_metni}{ref_parcasi}")
    if turev["olculemeyen"]:
        parca.append("")
        parca.append(f"ÖLÇÜLEMEYEN satır sayısı: {len(turev['olculemeyen'])} "
                     f"(pozisyon: {turev['olculemeyen']})")
    parca.append("")
    parca.append(f"AKIBET: {turev['sayilar']['acik']} açık")
    return "\n".join(parca)


# ─────────────────────────────────────────────────────────────────────────────
#  CLI
# ─────────────────────────────────────────────────────────────────────────────

SON_SOZ = ("çıkış kodları: 0=başarı · 1=doğrulama kırmızısı · 2=kullanım hatası\n"
           "not: `--komut-yaz` HİÇBİR daldan ssh çalıştırmaz (`--zorla` dahil), kurulan komutu BASAR.")


def _listele(a) -> int:
    sonuc = filo._ssh_kos(okuma_komutu(), a)
    if sonuc is None:
        return 0
    rc, cikti, hata = sonuc
    if rc != 0:
        print(f"[akibet] defter ÖLÇÜLEMEDİ (ssh RC={rc}): {hata.strip() or 'stderr boş'}",
              file=sys.stderr)
        return 1
    ayrilmis = _ayir(cikti)
    ok, neden = _fetch_hukmu(ayrilmis)
    if not ok:
        # Y5 düzeltmesi (yeniden-inceleme 2026-08-31): `_fetch_hukmu`nun genel cümlesi TEK BAŞINA
        # basılıyordu — ÖLÇÜLMÜŞ uzak stderr (`cat: …: Permission denied` gibi) elde olduğu hâlde
        # atılıyordu. Operatör "ÖLÇÜLEMEDİ" görürdü ama NEDENİNİ görmezdi.
        ek = f" — uzak stderr: {hata.strip()}" if hata.strip() else ""
        print(f"[akibet] {neden}{ek}", file=sys.stderr)
        return 1
    defter_satirlari = _jsonl_satirlari(ayrilmis["defter_metin"])
    turev = akibet_turet(_jsonl_satirlari(ayrilmis["proposals_metin"]), defter_satirlari, _simdi())
    print(listele_metni(turev, sonuclar(defter_satirlari)))
    return 0


def _oneri(a) -> int:
    komut = oneri_ekleme_komutu(a.kaynak, a.metin, _simdi())
    sonuc = filo._ssh_kos(komut, a)
    if sonuc is None:
        return 0
    rc, cikti, hata = sonuc
    if rc != 0:
        print(f"[akibet] ekleme ÖLÇÜLEMEDİ (ssh RC={rc}): {hata.strip() or 'stderr boş'}",
              file=sys.stderr)
        return 1
    ok, neden, yeni_id = oneri_yazim_dogrulandi(cikti, a.kaynak, a.metin)
    if not ok:
        print(neden, file=sys.stderr)
        return 1
    print(f"{yeni_id}: {neden}")
    print(f"doğdu: {yeni_id} ({a.kaynak})")
    return 0


def _defter_ve_turev(a) -> tuple[int, dict | None]:
    """`karar`/`sonuc` ortak ön-koşum: fetch + türetim. `(rc_hata, turev)` — `turev` `None`
    ise `rc_hata` zaten basılmış bir hata YA DA `--komut-yaz`ın kendi 0-dönüşüdür (çağıran
    doğrudan döner)."""
    sonuc = filo._ssh_kos(okuma_komutu(), a)
    # Y7 düzeltmesi (yeniden-inceleme 2026-08-31): `_listele`/`_oneri` bu guard'ı taşıyordu,
    # burası taşımıyordu — bugün ULAŞILAMAZ (`_karar`/`_sonuc` `komut_yaz` dalında ÖNCE dönüyor)
    # ama asimetri LATENTTİ: o sıralama değişirse burası çıplak `TypeError` ile çökerdi (ve R1
    # tam da bunu yakalayacak geniş `except`i haklı olarak kaldırmıştı). `--komut-yaz`ın kendi
    # sözleşmesiyle TUTARLI: `filo._ssh_kos` zaten komutu bastı, burada 0/`None` ile sessizce
    # çıkılır.
    if sonuc is None:
        return 0, None
    rc, cikti, hata = sonuc
    if rc != 0:
        print(f"[akibet] defter ÖLÇÜLEMEDİ (ssh RC={rc}): {hata.strip() or 'stderr boş'}",
              file=sys.stderr)
        return 1, None
    ayrilmis = _ayir(cikti)
    ok, neden = _fetch_hukmu(ayrilmis)
    if not ok:
        # Y5 düzeltmesi (yeniden-inceleme 2026-08-31): bkz. `_listele`'deki aynı düzeltme —
        # ÖLÇÜLMÜŞ uzak stderr artık atılmıyor.
        ek = f" — uzak stderr: {hata.strip()}" if hata.strip() else ""
        print(f"[akibet] {neden}{ek}", file=sys.stderr)
        return 1, None
    turev = akibet_turet(_jsonl_satirlari(ayrilmis["proposals_metin"]),
                         _jsonl_satirlari(ayrilmis["defter_metin"]), _simdi())
    return 0, turev


def _karar(a) -> int:
    if not gerekce_gecerli_mi(a.gerekce):
        print(f"[akibet] gerekçe en az {GEREKCE_ASGARI} karakter olmalı "
              f"(şu an {len(a.gerekce.strip())}): {a.gerekce!r}", file=sys.stderr)
        return 1
    satir = {"ts": _simdi(), "olay": "karar", "oneri_id": a.id, "karar": a.karar,
             "karar_veren": a.veren, "gerekce": a.gerekce}
    if a.komut_yaz:
        print(shlex.join(filo.ssh_sarmali(ekleme_komutu(satir), host=a.host, anahtar=a.anahtar)))
        return 0
    hata_rc, turev = _defter_ve_turev(a)
    if turev is None:
        return hata_rc
    acik_idler = {x["oneri_id"] for x in turev["acik"]}
    # "doğmuş" küme = açık ∪ karar-taşıyan id'ler — akibet_turet dönüşü doğum kümesini AYRI bir
    # alan olarak taşımaz (brief şeması sabit); bu, sağlıklı bir defterde "hiç doğmamış" ile
    # "zaten kapalı"yı doğru ayırt eder (bkz. akibet_turet docstring'i).
    karar_idler = {k["oneri_id"] for k in turev["kararlar"]}
    if a.id not in acik_idler and a.id not in karar_idler:
        print(f"[akibet] {a.id}: defterde/önerilerde HİÇ doğmamış — karar yazılmaz",
              file=sys.stderr)
        return 1
    if a.id not in acik_idler:
        eski = next((k for k in reversed(turev["kararlar"]) if k["oneri_id"] == a.id), None)
        eski_karar = eski["karar"] if eski else "ÖLÇÜLEMEDİ"
        if not a.zorla:
            print(f"[akibet] {a.id}: ZATEN kapalı (son karar: {eski_karar}) — değiştirmek "
                  "için --zorla gerekir", file=sys.stderr)
            return 1
        print(f"[akibet] UYARI: {a.id} zaten {eski_karar} kararını taşıyordu — --zorla ile "
              "ÜZERİNE yeni karar ekleniyor")
    sonuc2 = filo._ssh_kos(ekleme_komutu(satir), a)
    rc2, cikti2, hata2 = sonuc2
    if rc2 != 0:
        print(f"[akibet] ekleme ÖLÇÜLEMEDİ (ssh RC={rc2}): {hata2.strip() or 'stderr boş'}",
              file=sys.stderr)
        return 1
    ok, neden = yazim_dogrulandi(cikti2, satir)
    if not ok:
        # Kü6 düzeltmesi: yazım-doğrulama KIRMIZISI de diğer TÜM hata yolları gibi stderr'e
        # gider — eskiden stdout'a gidiyordu ve `>> log` gibi bir yönlendirmede terminalden
        # kaybolabiliyordu (en kritik arıza en görünmez olan olurdu).
        print(f"{a.id}: {neden}", file=sys.stderr)
        return 1
    print(f"{a.id}: {neden}")
    print(f"karar yazıldı: {a.id} → {a.karar} ({a.veren})")
    return 0


def _sonuc(a) -> int:
    satir = {"ts": _simdi(), "olay": "sonuc", "oneri_id": a.id, "ozet": a.ozet}
    if a.ref is not None:
        satir["ref"] = a.ref
    if a.komut_yaz:
        print(shlex.join(filo.ssh_sarmali(ekleme_komutu(satir), host=a.host, anahtar=a.anahtar)))
        return 0
    hata_rc, turev = _defter_ve_turev(a)
    if turev is None:
        return hata_rc
    karar_idler = {k["oneri_id"] for k in turev["kararlar"]}
    if a.id not in karar_idler:
        print(f"[akibet] {a.id}: defterde HİÇ karar taşımıyor — sonuç karardan ÖNCE gelmez",
              file=sys.stderr)
        return 1
    sonuc2 = filo._ssh_kos(ekleme_komutu(satir), a)
    rc2, cikti2, hata2 = sonuc2
    if rc2 != 0:
        print(f"[akibet] ekleme ÖLÇÜLEMEDİ (ssh RC={rc2}): {hata2.strip() or 'stderr boş'}",
              file=sys.stderr)
        return 1
    ok, neden = yazim_dogrulandi(cikti2, satir)
    if not ok:
        print(f"{a.id}: {neden}", file=sys.stderr)  # Kü6 düzeltmesi (bkz. _karar)
        return 1
    print(f"{a.id}: {neden}")
    print(f"sonuç yazıldı: {a.id}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="akibet.py", description=__doc__.splitlines()[0], epilog=SON_SOZ,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ortak = argparse.ArgumentParser(add_help=False)
    ortak.add_argument("--host", default=None,
                       help=f"ssh hedefi (env {filo.ENV_KULLANICI}/{filo.ENV_IP}; "
                            f"şu an: {filo.varsayilan_host()})")
    ortak.add_argument("--anahtar", default=None,
                       help=f"ssh özel anahtarı (env {filo.ENV_ANAHTAR}; "
                            f"şu an: {filo.varsayilan_anahtar()})")
    ortak.add_argument("--komut-yaz", dest="komut_yaz", action="store_true",
                       help="kurulan ssh komutunu BAS, KOŞMA")
    alt = ap.add_subparsers(dest="komut", required=True)

    alt.add_parser("listele", parents=[ortak],
                   help="açık öneriler yaşlarıyla + son 5 karar + son sonuçlar (salt-okuma)")

    o = alt.add_parser("oneri", parents=[ortak], help="yeni öneri doğum satırı ekler")
    o.add_argument("metin", help="öneri metni")
    o.add_argument("--kaynak", choices=ONERI_KAYNAKLARI, required=True)

    k = alt.add_parser("karar", parents=[ortak], help="bir öneriye karar satırı ekler")
    k.add_argument("id", help="öneri kimliği (N##### ya da AKB-####)")
    k.add_argument("karar", choices=KARARLAR)
    k.add_argument("--gerekce", required=True, help=f"en az {GEREKCE_ASGARI} karakter")
    k.add_argument("--veren", choices=KARAR_VERENLER, required=True)
    k.add_argument("--zorla", action="store_true",
                   help="zaten kapalı bir öneriye YENİ karar yazmayı beyanla izin ver")

    s = alt.add_parser("sonuc", parents=[ortak], help="kararlı bir öneriye sonuç satırı ekler")
    s.add_argument("id", help="öneri kimliği")
    s.add_argument("--ozet", required=True)
    s.add_argument("--ref", default=None, help="commit/kart/yol (opsiyonel)")

    a = ap.parse_args(argv)
    return {"listele": _listele, "oneri": _oneri, "karar": _karar, "sonuc": _sonuc}[a.komut](a)


if __name__ == "__main__":
    raise SystemExit(main())
