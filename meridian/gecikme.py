"""gecikme.py — süreç-içi, sıfır bağımlılıklı gecikme histogramları + Prometheus metin ifadesi (TSK-020 UYGULA-9 Faz B).

NE YAPAR. Sabit kovalı, iş parçacığı güvenli (kilitli) bir `Histogram` ve onu saran `sure_olc` bağlam yöneticisi
verir; `ifade(*histogramlar)` Prometheus metin biçimini (0.0.4) üretir: `# HELP` + `# TYPE … histogram`,
BİRİKİMLİ `_bucket{le=…}` satırları (`le` küçük-eşittir), `le="+Inf"` = `_count`, ardından `_sum` ve `_count`.
`prometheus_client` BİLEREK kullanılmaz — tedarik zinciri kapısının (`[0b]`) yüzeyi büyümesin; `api.metrics`in
elle yazılmış gauge deseninin histogram karşılığıdır (tasarım T4).

SINIR (tasarım §2, bağlayıcı): telemetri GÖZLEMDİR. Hiçbir kapı/kill kararı bu histogramlardan okumaz; tek
okuyucu `api.metrics` ucudur (Prometheus kazır, Grafana gösterir). KILL#1'in canlı çapası ayrı karttır (Faz C).

DEĞİŞMEZLER.
  * Kardinalite beyanlıdır: etiketli histogramın değer kümesi kurulumda verilir ve ÖNCEDEN kurulur (sıfır sayımla
    yayınlanır — ilk gözlem `increase()`te kaybolmasın). Beyan dışı bir değer `DIGER` ("other") serisine düşer;
    yani seri sayısı en çok beyan + 1'dir. Etiket değerleri kullanıcı girdisinden türemez.
  * `gozlemle` ÇAĞIRANI DÜŞÜRMEZ: `finally` yollarında çağrılır — orada yükselen bir hata özgün istisnanın yerine
    geçerdi. Geçersiz gözlem (sayı değil / sonlu değil / negatif) kaydedilmez; `reddedilen` sayacına düşer ve ifade
    bir `# NOTE` satırıyla görünür (sessiz değil). Tanım hataları ise KURULUMDA `ValueError`dır (modül yüklenirken).
  * Durum yalnız kilit altında okunur/yazılır; kilit altındayken dışarı çağrı yapılmaz (kilitlenme yok — `store`un
    `_record_io`su da buraya yazar ve `obs` oradan döner).
  * Süreç-içidir: yeniden başlatmada sıfırlanır; Prometheus `rate`/`increase`/`histogram_quantile` bunu tolere eder.

SAF YAPRAK: yalnız standart kütüphane; hiçbir `meridian` modülünü içe aktarmaz (v585 D6). Okuyucu: `api.metrics`.
Yazıcılar (gözlem noktaları): `intraday_cycle.IntradayConsumer` (olay turu), `skills.pipeline_run` (faz),
`store._record_io` (atomik yazım)."""
from __future__ import annotations

import bisect
import math
import re
import threading
import time

DIGER = "other"                  # beyan dışı etiket değerinin düştüğü tek seri (kardinalite tavanı: beyan + 1)

# Saat — `time.perf_counter` (monoton, yüksek çözünürlük). Modül adı üzerinden çözülür ki çiviler deterministik
# süre için onu değiştirebilsin; üretimde hiçbir kod bu adı yeniden bağlamaz.
_saat = time.perf_counter

_AD = re.compile(r"^[a-zA-Z_:][a-zA-Z0-9_:]*$")
_ETIKET_ADI = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
_ETIKET_DEGERI = re.compile(r"^[A-Za-z0-9_.\-]+$")   # kaçış gerektirmeyen küme: tırnak/ters bölü/satır sonu YOK


def _sayi_metni(x: float) -> str:
    """Kova sınırı ve toplam için kısa, gidiş-dönüşlü ondalık gösterim (`repr`); Prometheus bunu float okur."""
    return repr(float(x))


class _Seri:
    """Tek etiket değerinin durumu: kova başına (BİRİKİMSİZ) sayımlar + taşma kovası, toplam süre, gözlem sayısı."""

    __slots__ = ("kova_sayilari", "toplam", "sayi")

    def __init__(self, kova_n: int):
        """`kova_n` sonlu kova + 1 taşma (`+Inf`) hücresiyle sıfır durum."""
        self.kova_sayilari = [0] * (kova_n + 1)
        self.toplam = 0.0
        self.sayi = 0


class Histogram:
    """Sabit kovalı süreç-içi histogram. Birim saniyedir (ad `_seconds` ile biter — Prometheus adlandırması).

    `etiket` verilirse (tek etiket adı) `etiket_degerleri` beyanlı ve boş olmayan kümedir; değerler önceden kurulur.
    `etiket` yoksa tek seri vardır ve gözlemdeki etiket değeri yok sayılır."""

    def __init__(self, ad: str, aciklama: str, kovalar, etiket: str | None = None, etiket_degerleri=()):
        """Tanımı doğrular (geçersizse `ValueError` — kurulum anında, çağrı yolunda DEĞİL) ve serileri kurar."""
        if not isinstance(ad, str) or not _AD.match(ad):
            raise ValueError(f"geçersiz metrik adı: {ad!r}")
        kv = tuple(float(k) for k in kovalar)
        if not kv:
            raise ValueError("kova listesi boş")
        if any((not math.isfinite(k)) or k <= 0 for k in kv):
            raise ValueError(f"kova sınırları sonlu ve pozitif olmalı: {kv}")
        if any(b <= a for a, b in zip(kv, kv[1:])):
            raise ValueError(f"kova sınırları kesin artan olmalı: {kv}")
        degerler = tuple(etiket_degerleri)
        if etiket is not None:
            if not _ETIKET_ADI.match(etiket) or etiket == "le" or etiket.startswith("__"):
                raise ValueError(f"geçersiz etiket adı: {etiket!r}")
            if not degerler:
                raise ValueError("etiketli histogramın etiket değer kümesi boş (kardinalite beyanı zorunlu)")
            if len(set(degerler)) != len(degerler):
                raise ValueError(f"etiket değerleri tekrarlı: {degerler}")
            for d in degerler + (DIGER,):
                if not isinstance(d, str) or not _ETIKET_DEGERI.match(d):
                    raise ValueError(f"geçersiz etiket değeri: {d!r}")
        elif degerler:
            raise ValueError("etiket adı yokken etiket değeri verildi")
        self.ad = ad
        self.aciklama = str(aciklama).replace("\\", "\\\\").replace("\n", "\\n")
        self.kovalar = kv
        self.etiket = etiket
        self.etiket_degerleri = degerler
        self.reddedilen = 0
        self._kilit = threading.Lock()
        self._seriler: dict = {}
        for d in (degerler if etiket is not None else (None,)):
            self._seriler[d] = _Seri(len(kv))

    def gozlemle(self, saniye, etiket_degeri=None) -> None:
        """Bir süreyi (saniye) kaydeder. ÇAĞIRANI DÜŞÜRMEZ: geçersiz değer kaydedilmez, `reddedilen` sayılır.

        Etiketli histogramda beyan dışı (ya da `None`) değer `DIGER` serisine düşer; o seri ilk ihtiyaçta kurulur."""
        gecerli = (isinstance(saniye, (int, float)) and not isinstance(saniye, bool)
                   and math.isfinite(saniye) and saniye >= 0)
        if self.etiket is None:
            anahtar = None
        else:
            anahtar = etiket_degeri if etiket_degeri in self.etiket_degerleri else DIGER
        with self._kilit:
            if not gecerli:
                self.reddedilen += 1
                return
            seri = self._seriler.get(anahtar)
            if seri is None:
                seri = self._seriler[anahtar] = _Seri(len(self.kovalar))
            seri.kova_sayilari[bisect.bisect_left(self.kovalar, saniye)] += 1
            seri.toplam += saniye
            seri.sayi += 1

    def _kesit(self) -> tuple[dict, int]:
        """TEK kilit alımında seriler + reddedilen sayacı — ifade içi tutarlılık (`+Inf` = `_count` = kesit anı)."""
        with self._kilit:
            return ({d: {"kova_sayilari": list(s.kova_sayilari), "toplam": s.toplam, "sayi": s.sayi}
                     for d, s in self._seriler.items()}, self.reddedilen)

    def anlik(self) -> dict:
        """Kilit altında tutarlı kesit: {etiket değeri (etiketsizde None): {"kova_sayilari": [...], "toplam", "sayi"}}.

        `kova_sayilari` BİRİKİMSİZDİR ve son hücresi taşmadır; birikimli hâli `ifade` hesaplar (tek kaynak)."""
        return self._kesit()[0]

    def ifade(self) -> str:
        """Bu histogramın Prometheus metin ifadesi (HELP, TYPE, seriler; gerekirse reddedilen gözlem notu)."""
        kesit, reddedilen = self._kesit()
        satirlar = [f"# HELP {self.ad} {self.aciklama}", f"# TYPE {self.ad} histogram"]
        sirali = ([d for d in self.etiket_degerleri if d in kesit] + [d for d in kesit if d not in self.etiket_degerleri]
                  if self.etiket is not None else [None])
        for d in sirali:
            s = kesit[d]
            on = f'{self.etiket}="{d}",' if self.etiket is not None else ""
            yalin = f'{{{self.etiket}="{d}"}}' if self.etiket is not None else ""
            birikimli = 0
            for sinir, n in zip(self.kovalar, s["kova_sayilari"]):
                birikimli += n
                satirlar.append(f'{self.ad}_bucket{{{on}le="{_sayi_metni(sinir)}"}} {birikimli}')
            birikimli += s["kova_sayilari"][-1]
            satirlar.append(f'{self.ad}_bucket{{{on}le="+Inf"}} {birikimli}')
            satirlar.append(f"{self.ad}_sum{yalin} {_sayi_metni(s['toplam'])}")
            satirlar.append(f"{self.ad}_count{yalin} {s['sayi']}")
        if reddedilen:
            satirlar.append(f"# NOTE {self.ad} reddedilen_gozlem {reddedilen}")
        return "\n".join(satirlar) + "\n"


class Olcum:
    """`sure_olc`un döndürdüğü bağlam yöneticisi. Çıkışta (normal YA DA istisna yolunda) geçen süreyi
    `etiket_degeri` ile kaydeder ve istisnayı ASLA yutmaz (`__exit__` False döner). Gövde, `with … as` ile aldığı
    nesnenin `etiket_degeri` alanını çıkıştan önce değiştirebilir (ör. olayın sonucu gövde bitince bilinir)."""

    __slots__ = ("histogram", "etiket_degeri", "_t0")

    def __init__(self, histogram: Histogram, etiket_degeri=None):
        """Ölçülecek histogram ve başlangıç etiketi (istisna yolunda geçerli kalacak değer)."""
        self.histogram = histogram
        self.etiket_degeri = etiket_degeri
        self._t0 = None

    def __enter__(self) -> "Olcum":
        """Saati başlatır."""
        self._t0 = _saat()
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        """Süreyi kaydeder; istisna varsa AYNEN yükselmesi için False döner."""
        self.histogram.gozlemle(_saat() - self._t0, self.etiket_degeri)
        return False


def sure_olc(histogram: Histogram, etiket_degeri=None) -> Olcum:
    """`with gecikme.sure_olc(H, "etiket") as olcum:` — gövdenin süresini H'ye işler (istisna yolunda da)."""
    return Olcum(histogram, etiket_degeri)


def ifade(*histogramlar: Histogram) -> str:
    """Verilen histogramların Prometheus metin ifadelerini sırayla birleştirir (`api.metrics` tam setinin sonu)."""
    return "".join(h.ifade() for h in histogramlar)
