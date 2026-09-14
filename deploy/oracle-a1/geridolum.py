#!/usr/bin/env python3
"""EDG-066 geri-dolum sürücüsü — IEX HIST tick arşivini GERİYE DOĞRU doldurur.

Tetik: meridian-geridolum.timer (saatlik) → meridian-geridolum.service (oneshot, uzun koşum).
Kurulu yeri /opt/veri/geridolum.py; repo kaynağı deploy/oracle-a1/geridolum.py (F9 sınıfı).
Ayrıştırıcı: /opt/veri/pilot.py (repo kaynağı research/olcumler/edg066_tick_arsiv/pilot.py,
EDG-066 kart artefaktı) — --kapsam /opt/veri/kapsam.txt ile (662 sembol, kapsam_uret.py üretir).

Operatör kararları (2026-08-31, EDG-066 kartında kayıtlı): kapsam S&P500+NDX100 birleşimi ·
pencere 2020-01→bugün geriye doğru · tavan 120 GB (pencere ÇIKTIdır) · seyreltme 1/sn +
işlemler tam + işlem-anı anlık görüntü · meridian-learn program bitene dek KAPALI (2 CPU
bu işe dedike — İŞÇİ=2 oradan gelir; learn geri açılırsa İŞÇİ yeniden değerlendirilir).

Bekçiler (her turda, iş AÇILMADAN önce):
  · RTH penceresi: ABD seansı içinde (ve seansa <35 dk kala) yeni tur açılmaz — canlı döngü
    makinenin sahibidir. Koşan tur kesilmez; nice/ionice zaten geri planda tutar.
  · 120 GB tavan: tick kalıcı artefaktları (kotasyon_1s+islem+sayim) tavana ulaştıysa çık,
    TAVAN-DOLDU işareti bırak (dolunca eski gün silme kararı operatörün — panik kararı yok).
  · Disk payı: ham gz geçicileri için boş alan turun KİPİNE göre ölçülür — geri turda
    DISK_PAYI_BAYT, ileri turda ILERI_DISK_PAYI_BAYT; altına inildiyse KIRMIZI çık
    (ENOSPC'ye yürüme). Kip başına işçi sayısı da ayrıdır (ISCI / ILERI_ISCI). Bu kapı
    yalnız İŞ AÇILACAKSA ölçülür: aday gün kalmadığı turda ölçüm sahte KIRMIZI üretirdi.
  · flock tekilliği: iki sürücü aynı anda koşamaz (timer + elle koşum çakışması).

İşçi dayanıklılığı (TSK-087, 2026-09-02): rc≠0 veren gün AYNI koşumda BİR kez yeniden
denenir — öteki işçi sürerken, onun bitmiş işi kesilmeden. İkinci çöküşte koşum yine
KIRMIZI'dır; her düşüşlü tur bedel özeti basar (kaç gün düştü / 2. denemede geçti / kaldı).
Kalıcı-geçici arıza sınıfı ayrımı YALNIZ mesajdadır: sınıf rc'den ölçülemez, karar ona
bağlanmaz. Kilit/tavan/pencere/defter mantığı DEĞİŞMEDİ.

İLERİ dolum (TSK-188, 2026-09-14): arşiv 2026-09-03'te durdu — İKİ kök neden, ikisi de
ölçüldü (A1 journal + defter sayımı, 2026-09-13):
  (1) TAZE-BOŞ GÜN O KOŞUMDA BİR DAHA DENENMİYORDU. Atlanan günler bir SET idi. Tek koşum
      (PID 306299) 09-05→09-10 günlerce sürdü; her yeni iş günü 00:0xZ'de bir kez denendi,
      IEX pcap ~09:20Z'de yayımlandığı için "boş döndü" cevabı geldi ve gün sete girdi —
      yayımlandıktan sonra AÇILMADI. Kalıcı kayıt da yok (gecilen.jsonl'de değil): gün ne
      işlendi ne atlandı, kayboldu. Artık atlanan gün SAATİYLE tutulur ve TAZE_YENIDEN_SN
      dolunca AYNI koşumda yeniden denenir. Kalıcı defter dalı (yaş > TAZE_GUN → hist-boş)
      DEĞİŞMEDİ.
  (2) 120 GB TAVANI İLERİ GÜNLERİ DE KESİYORDU. Tavan kontrolü gün seçiminden önceydi, koşum
      gün SEÇMEDEN çıkıyordu; operatörün 09-12 kararı ("geri dolum dursun") böylece T-1
      dolumunu da durdurdu ve canlı tick arşivi 10 gün büyümedi. Artık tavan yalnız GERİ
      günleri keser; ileri günler yalnız DISK_PAYI_BAYT kapısına tabidir. TAVAN_BAYT ve
      TAZE_GUN DEĞİŞMEDİ — eşik kararı ayrı kalemdir (operatör 2026-09-12).
  İLERİ/GERİ SINIRI SABİTTİR, ÖLÇÜM DEĞİL (Rol-1 kararı 2026-09-14, tur 2): ILERI_PENCERE_BASI.
  İlk sürüm sınırı "defterin en büyük günü" diye ÖLÇÜYORDU ve boşluğu KAPATMIYORDU: T-1
  işlendiği an defterin tepesi oraya taşınıyor, arada kalan 09-04..T-2 "geri" sayılıp tavanla
  kesiliyordu — koşum ne kadar sürerse sürsün boşluğun yalnız en yeni ISCI günü doluyordu.
  Sabit sınırla 09-04..T-1 arasındaki TÜM eksik iş günleri, KESİNTİLİ koşumlarda da (defterde
  yalnız 09-11 varken 09-04..09-10 hâlâ ileridir), sırayla dolar; 09-03 ve öncesi geri
  dolumdur ve tavan onları keser.

İLERİ KİP KENDİ KAYNAK ÇİTİNİ TAŞIR (TSK-188 dilim-2, operatör kararı 2026-09-14 "tek işçi +
  pay 15 GB"): dilim-1'den sonra ileri dolum tavandan muaf kaldı ama DİSK kapısı ortaktı —
  iki işçi × ~10 GB ham pcap geçicisi 25 GB'lik payı bir hafta içinde KIRMIZI'ya düşürecekti
  (A1 ölçümü 2026-09-14: boş 27 GB, ileri gün başına KALICI artış ~100 MB). Artık bir tur YA
  ileri turdur (ILERI_ISCI işçi + ILERI_DISK_PAYI_BAYT kapısı, tavandan muaf) YA DA geri
  turdur (ISCI işçi + DISK_PAYI_BAYT kapısı, tavan keser); karışmazlar, çünkü karışık tur yine
  iki geçici demektir. BEDELİ: ileri gün ile geri gün aynı turda paralel koşmaz ve ileri dolum
  ~2× yavaşlar (bir turda iki iş günü yerine bir tanesi işlenir). Pay altına inildiğinde ileri
  dal da KIRMIZI'dır — sessizce beklemez, birim failed'a düşer ve operatör görür.

Hüküm/okuyucu (Yasa 6): stdout → journald (birim düşerse /api/infra 'arizali' sınıflar —
failed'in okuyucusu var); kalıcı defter /opt/veri/tick/manifest.jsonl (pilot yazar) +
gecilen.jsonl (tatil/veri-yok günleri, bu sürücü yazar).
"""
from __future__ import annotations

import datetime as dt
import fcntl
import json
import pathlib
import subprocess
import sys
import time

KOK = pathlib.Path("/opt/veri")
PY = KOK / "pilot-venv" / "bin" / "python"
PILOT = KOK / "pilot.py"
KAPSAM = KOK / "kapsam.txt"
TAVAN_BAYT = 120 * 1000**3          # kart: "120 GB" — GB, GiB değil
DISK_PAYI_BAYT = 25 * 1000**3       # ham gz geçicileri (yoğun gün ~15 GB) + emniyet
PENCERE_BASI = dt.date(2020, 1, 1)
ISCI = 2
# Operatör kararı 2026-09-01 ("geri dolum kesintisiz çalışmalı, seans içi dahil"): seans
# penceresi kilidi kapatıldı. Eski davranışa dönüş: True. Kaynak sınırları (ISCI=2, TAVAN,
# DISK_PAYI) AYNEN — kesintisizlik kaynak çitlerini gevşetmez.
SEANS_KILIDI = False
TAZE_GUN = 5                        # bundan yeni boş HIST cevabı "henüz yayımlanmadı" sayılır
# TSK-188 kök neden 1: taze-boş gün bu kadar bekledikten sonra AYNI koşumda yeniden denenir.
# 6 saat, ölçülmüş yayım gecikmesinden gelir: koşum turu 00:0xZ'de boş cevap alıyordu, pcap
# ~09:20Z'de yayımlanıyor (manifest ts örneği 2026-09-04T09:23Z) — 6 saatlik bekleme aynı iş
# gününde en az bir kez yayım SONRASINA denk gelir, ve HIST'i gereksiz dövmez.
TAZE_YENIDEN_SN = 6 * 3600
# TSK-188 tur 2 — İLERİ (canlı) pencerenin SABİT başı; TEK KAYNAK, defterden ÖLÇÜLMEZ.
# Operatörün 2026-09-12 "geri dolum dursun" kararı 120 GB tavanındaki GERİ pencereyi kapsar;
# 09-04 (son arşiv günü 2026-09-03 + 1) ve sonrası CANLI penceredir ve tavandan bağımsız
# (yalnız DISK_PAYI_BAYT kapısına tabi) doldurulur. Bir OPERATÖR SINIRIDIR, bir ayar değil:
# ileri kaydırmak 09-04..sınır arasını sessizce tavana geri verir (çivi: v483).
ILERI_PENCERE_BASI = dt.date(2026, 9, 4)
# TSK-188 dilim-2 — İLERİ KİPİN KENDİ KAYNAK ÇİTİ (operatör kararı 2026-09-14: "tek işçi +
# pay 15 GB"). ÖLÇÜM (A1, 2026-09-14): /opt/veri 147 GB, kullanılan 113 GB, boş 27 GB;
# ileri gün başına KALICI artış ~100 MB, ama ham pcap GEÇİCİSİ gün başına ~10 GB. İki işçi
# ~20 GB anlık geçici tutar; 25 GB'lik pay ileri dolumu bir hafta içinde KIRMIZI ile
# durduracaktı. Tek işçi = aynı anda TEK geçici, ve 15 GB = ~10 GB geçici + ~5 GB emniyet.
# GERİ kip DEĞİŞMEDİ (ISCI=2, DISK_PAYI_BAYT=25 GB): geçmiş SİLİNMEZ, TAVAN_BAYT'a dokunulmadı
# (operatör 2026-09-12). Bir tur YA ileri YA geri turdur — karışık tur yine iki geçici demektir
# ve 15 GB payın tek dayanağı "aynı anda tek geçici"dir (çivi: v483).
ILERI_ISCI = 1
ILERI_DISK_PAYI_BAYT = 15 * 1000**3


def _simdi_sn() -> float:
    """Bekleme ölçümünün TEK saat kaynağı (testler bunu sahteler).

    monotonic, duvar saati DEĞİL: koşum günlerce sürer ve bir NTP adımı duvar saatini geri
    alsa bekleyen gün ya erken dirilir ya da süresi hiç dolmaz. Takvim kararları (yaş,
    TAZE_GUN) duvar saatinde kalır — onlar TARİH sorar, SÜRE değil."""
    return time.monotonic()


def _isci_baslat(g: str) -> subprocess.Popen:
    print(f"başlıyor: {g}", flush=True)
    return subprocess.Popen(
        ["nice", "-n", "10", "ionice", "-c", "3", str(PY), str(PILOT),
         "--gun", g, "--kapsam", str(KAPSAM)],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)


def _ariza_sinifi(cikti: str) -> str:
    """YALNIZ MESAJ içindir — yeniden deneme kararı bundan TÜREMEZ (TSK-087).

    Sınıf rc'den ölçülemez, ancak çıktı metninden TAHMİN edilir; tahmine karar bağlanmaz,
    bu yüzden geçici de kalıcı da bir kez yeniden denenir. Ayrım operatörün okuduğu özette
    yaşar: "hep aynı sınıf" deseni gerçek kök nedene işaret eder."""
    if "kesik indirme" in cikti:
        return "kesik indirme (geçici)"
    if "EOFError" in cikti:
        return "gz akışı erken bitti (geçici)"
    return "sınıf bilinmiyor (kalıcı olabilir)"


def _sonuc_isle(g: str, p: subprocess.Popen, bugun: dt.date, atlanan: dict[str, float],
                simdi: float) -> tuple[str, str]:
    """Bir işçinin bitişini işler: 'tamam' | 'gecildi' | 'taze' | 'cokme' + ham çıktı.

    manifest.jsonl'i pilot yazar; gecilen.jsonl yazımı burada ve TSK-087'de DEĞİŞMEDİ —
    HIST boş-gün dalı çökme SAYILMAZ, dolayısıyla ANINDA yeniden denenmez.

    TSK-188: `atlanan` artık set değil `{gün: saat}` — atlanış anı TURUN başındaki `simdi`dir
    (işçinin bitiş anı değil): bekleme, günün en son DENENDİĞİ andan ölçülür."""
    cikti, _ = p.communicate()
    son = cikti.strip().splitlines()[-3:] if cikti.strip() else ["<çıktı yok>"]
    if p.returncode == 0:
        print(f"bitti: {g} · " + " | ".join(son), flush=True)
        return "tamam", cikti
    if "boş döndü" in cikti:
        yas = (bugun - dt.date.fromisoformat(g)).days
        if yas > TAZE_GUN:
            with (KOK / "tick" / "gecilen.jsonl").open("a") as f:
                f.write(json.dumps({
                    "ts": dt.datetime.now(dt.timezone.utc).isoformat(),
                    "gun": g, "neden": "hist-bos (tatil/yarım gün)"}) + "\n")
            print(f"geçildi: {g} — HIST boş, yaş {yas} gün (tatil sayıldı)", flush=True)
            return "gecildi", cikti
        atlanan[g] = simdi   # kalıcı kayıt YOK; TAZE_YENIDEN_SN dolunca bu koşum yine dener
        print(f"taze-boş: {g} — henüz yayımlanmamış olabilir, kalıcı kayıt yok; "
              f"{TAZE_YENIDEN_SN // 3600} saat sonra bu koşumda yeniden denenecek", flush=True)
        return "taze", cikti
    return "cokme", cikti


def _ozet(dusen: list[tuple[str, str]], gecen2: list[str], gecildi2: list[str],
          kalan: list[tuple[str, str]]) -> str:
    """Bedel yasası: yeniden deneme GÜRÜLTÜYÜ azaltır — ne kadarını yuttuğu ölçülmeden
    sessizleşmesi körlüktür. Bu özet her düşüşlü turda basılır (okuyucu: journald).

    'geçti' ile 'geçildi' AYRI sayılır (inceleme Minor-1, 2026-09-03): retry'de HIST 'boş
    döndü' cevabına denk gelen gün bir veri-yok günüdür, bir pilot başarısı değil."""
    satir = [f"ÖZET (işçi dayanıklılığı): {len(dusen)} gün 1. denemede düştü, "
             f"{len(gecen2)} gün 2. denemede geçti, "
             f"{len(gecildi2)} gün 2. denemede geçildi [veri-yok günü], "
             f"{len(kalan)} gün kaldı",
             "  1. deneme sınıfları: " + ", ".join(f"{g}={s}" for g, s in dusen)]
    if gecen2:
        satir.append("  2. denemede geçen: " + ", ".join(gecen2))
    if gecildi2:
        satir.append("  2. denemede geçildi [veri-yok günü]: " + ", ".join(gecildi2))
    if kalan:
        satir.append("  KALAN (2. deneme de düştü): " + ", ".join(f"{g}={s}" for g, s in kalan))
    return "\n".join(satir)


def rth_yakin(pay_dk: int = 35) -> bool:
    u = dt.datetime.now(dt.timezone.utc)
    if u.weekday() >= 5:
        return False
    dk = u.hour * 60 + u.minute + pay_dk
    # 13:20Z ön-pay ile 20:10Z: ABD seansı (yaz saati) + açılış/kapanış tamponu
    return 13 * 60 + 20 <= dk and u.hour * 60 + u.minute <= 20 * 60 + 10


def tick_bayt() -> int:
    return sum(f.stat().st_size
               for alt in ("kotasyon_1s", "islem", "sayim")
               for f in (KOK / "tick" / alt).glob("*") if f.is_file())


def bos_bayt() -> int:
    import shutil
    return shutil.disk_usage(KOK).free


def islenmis() -> set[str]:
    done = set()
    for ad in ("manifest.jsonl", "gecilen.jsonl"):
        y = KOK / "tick" / ad
        if y.exists():
            for satir in y.read_text().splitlines():
                try:
                    done.add(json.loads(satir)["gun"])
                except (ValueError, KeyError):
                    # sessiz-yutma: bozuk defter satırı tek günü düşürür, koşumu değil;
                    # gün yeniden denenir — kayıp değil yineleme üretir, KIRMIZI'ya gerek yok
                    print(f"UYARI: {ad} içinde çözülemeyen satır atlandı", flush=True)
    return done


def taze_bekleyen(atlanan: dict[str, float], simdi: float) -> set[str]:
    """Hâlâ bekleme süresindeki taze-boş günler — `done` kümesine bunlar eklenir.

    Süresi DOLAN gün kümeden düşer ve gün seçimine geri girer (TSK-188 kök neden 1). Filtreyi
    burada tutmanın sebebi tek-kaynak: `sonraki_gunler` bir günü yalnız `done` kümesi üzerinden
    dışlar — iki ayrı dışlama yolu olsaydı biri sessizce ötekinden ayrışırdı."""
    return {g for g, ts in atlanan.items() if simdi - ts < TAZE_YENIDEN_SN}


def ileri_gun(g: str) -> bool:
    """`g` CANLI (ileri) pencerede mi — yani ILERI_PENCERE_BASI ve sonrası mı.

    Tanım DEFTERE BAKMAZ: sınır sabittir (tek-kaynak yasası — sabit ile ölçüm yan yana
    dursaydı biri sessizce ötekinden ayrışırdı). Karşılaştırma ISO-8601 dizgesi üzerinde
    yapılır; o sıralama kronolojiktir. Sınır KAPSAYICIDIR: pencere başının kendisi ileri
    gündür, bir önceki iş günü (son arşiv günü) değil. Kesinti dayanıklılığı bundan gelir —
    defter yalnız 09-11'i taşısa bile 09-04..09-10 ileri kalır ve tavan onu kesmez."""
    return g >= ILERI_PENCERE_BASI.isoformat()


def sonraki_gunler(n: int, done: set[str]) -> list[str]:
    out: list[str] = []
    g = dt.date.today() - dt.timedelta(days=1)
    while len(out) < n and g >= PENCERE_BASI:
        if g.weekday() < 5 and g.isoformat() not in done:
            out.append(g.isoformat())
        g -= dt.timedelta(days=1)
    return out


def main() -> int:
    kilit = (KOK / "geridolum.kilit").open("w")
    try:
        fcntl.flock(kilit, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print("zaten koşuyor — çıkılıyor (flock)")
        return 0

    if not (PILOT.exists() and KAPSAM.exists()):
        print(f"KIRMIZI: {PILOT} ya da {KAPSAM} yok — kurulum eksik", flush=True)
        return 1

    # taze-boş günler → son atlanış saati; TAZE_YENIDEN_SN dolunca bu koşumda yeniden denenir
    atlanan: dict[str, float] = {}
    while True:
        bugun = dt.date.today()   # koşum günlerce sürebilir — her turda tazelenir
        simdi = _simdi_sn()
        if SEANS_KILIDI and rth_yakin():
            print("seans penceresi (ya da <35 dk kala) — tur açılmadı, çıkılıyor")
            return 0

        # TSK-188 kök neden 2: gün SEÇİMİ tavan kapısından ÖNCE gelir — "hangi günler ileri"
        # sorusu ancak seçimden sonra sorulabilir. Geri dalın mesajı DEĞİŞMEDİ; değişen,
        # tavanın artık ileri günleri kesmemesi. Kapı sırası tavan → boş-pencere → disk
        # (dilim-2 tur 2: disk kapısı iş AÇILACAKSA ölçülür — gerekçe aşağıda).
        kalici = islenmis()                       # manifest + gecilen: defterin kendisi
        done = kalici | taze_bekleyen(atlanan, simdi)
        # TSK-188 dilim-2: TUR TEK KİPLİDİR. Aday havuzu iki kipin BÜYÜK kotasından çekilir
        # (`max`: hangi kip kazanırsa kazansın yeterli aday gelsin — kotalar ayrışırsa kod
        # sessizce eksik gün seçmesin); ileri gün VARSA tur ileri kiptir ve kendi çitini
        # getirir. İleri günler geri günlerden her zaman YENİdir, bu yüzden `sonraki_gunler`
        # (yeniden → eskiye) sıralamasında önde gelirler: dilimleme onları kesmez.
        secilen = sonraki_gunler(max(ISCI, ILERI_ISCI), done)
        ileri = [g for g in secilen if ileri_gun(g)][:ILERI_ISCI]
        if ileri:
            gunler, disk_payi, kip = ileri, ILERI_DISK_PAYI_BAYT, "ileri"
        else:
            gunler, disk_payi, kip = secilen[:ISCI], DISK_PAYI_BAYT, "geri"

        kullanilan = tick_bayt()
        if kullanilan >= TAVAN_BAYT:
            (KOK / "tick" / "TAVAN-DOLDU").write_text(
                f"{dt.datetime.now(dt.timezone.utc).isoformat()} kullanılan={kullanilan}\n")
            if kip == "geri":
                print(f"TAVAN: {kullanilan / 1e9:.1f} GB >= 120 GB — çıkılıyor (karar operatörün)")
                return 0
            print(f"TAVAN aşıldı: yalnız ileri günler dolduruluyor ({', '.join(gunler)}) — "
                  f"{kullanilan / 1e9:.1f} GB, geri dolum durdu (karar operatörün)", flush=True)
        if not gunler:
            print("PENCERE-TAMAM: 2020-01-01'e kadar tüm iş günleri işlendi/geçildi")
            (KOK / "tick" / "PENCERE-TAMAM").write_text(
                dt.datetime.now(dt.timezone.utc).isoformat() + "\n")
            return 0

        # TSK-188 dilim-2 tur 2: disk kapısı boş-pencere kontrolünden SONRAdır. Kapının işi
        # ENOSPC'ye YÜRÜMEYİ engellemektir; iş AÇILMIYORSA engellenecek bir şey yoktur ve
        # ölçüm yalnız sahte bir KIRMIZI üretir (birim failed, operatör olmayan bir riski okur).
        # Eski sıra (tavan → disk → boş-pencere) dilim-1'e kadar zararsızdı çünkü boş alan hep
        # 25 GB'nin üstündeydi; ileri kip 15–25 GB aralığında çalışacağı için dal erişilebilir
        # hale geldi ve düzeltildi (Rol-1 kararı 2026-09-14, çivi: v483).
        if bos_bayt() < disk_payi:
            # Kip mesajda YAZILIDIR: iki farklı pay iki farklı hükümdür ve operatör journald'da
            # hangi kapının öttüğünü ayırt edebilmelidir (aynı sayı iki kez uydurulmaz, türetilir).
            print(f"KIRMIZI: disk payı < {disk_payi / 1e9:.0f} GB ({kip} kip) — "
                  f"ham geçiciler sığmaz", flush=True)
            return 1

        surecler = [(g, _isci_baslat(g)) for g in gunler]

        # TSK-087: çöken gün AYNI koşumda bir kez yeniden denenir. Eski davranış ilk rc≠0'da
        # `return 1` idi — öteki işçinin BİTMİŞ işi toplanmadan koşum ölüyor, saatlik timer'a
        # kadar bekleniyordu. Yeniden deneme, öteki işçi hâlâ sürerken başlatılır (ISCI=2
        # paralelliği korunur); ikinci çöküşte koşum yine KIRMIZI.
        dusen: list[tuple[str, str]] = []
        yeniden: list[tuple[str, subprocess.Popen]] = []
        for g, p in surecler:
            durum, cikti = _sonuc_isle(g, p, bugun, atlanan, simdi)
            if durum == "cokme":
                sinif = _ariza_sinifi(cikti)
                dusen.append((g, sinif))
                print(f"DÜŞTÜ (1. deneme): {g} rc={p.returncode} · {sinif} — aynı koşumda "
                      f"BİR kez yeniden deneniyor\n" + cikti[-2000:], flush=True)
                yeniden.append((g, _isci_baslat(g)))

        gecen2: list[str] = []      # retry'de pilot GERÇEKTEN geçti
        gecildi2: list[str] = []    # retry 'boş döndü'ye denk geldi — geçiş DEĞİL, atlama
        kalan: list[tuple[str, str]] = []
        for g, p in yeniden:
            durum, cikti = _sonuc_isle(g, p, bugun, atlanan, simdi)
            if durum == "cokme":
                sinif = _ariza_sinifi(cikti)
                kalan.append((g, sinif))
                print(f"KIRMIZI: {g} rc={p.returncode} (2. deneme de düştü) · {sinif}\n"
                      + cikti[-2000:], flush=True)
            elif durum == "tamam":
                gecen2.append(g)
            else:
                # inceleme Minor-1 (2026-09-03): 'gecildi'/'taze' bir pilot başarısı DEĞİLDİR;
                # "geçti" diye sayılırsa özet operatöre olmayan bir başarı gösterir.
                gecildi2.append(g)

        if dusen:
            print(_ozet(dusen, gecen2, gecildi2, kalan), flush=True)
        if kalan:
            return 1   # birim failed → panoda görünür; timer sonraki saatte yeniden dener
    # not: while True'dan tek çıkışlar yukarıdaki return'lerdir


if __name__ == "__main__":
    sys.exit(main())
