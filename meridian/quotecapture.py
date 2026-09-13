"""quotecapture.py — EDG-2026-085 Senaryo-A: icra-anı IEX quote kaydı (halka · pencere · abone · yazıcı).

NE YAPAR: marketstream'in TEK data soketine bayrakla eklenen `quotes` aboneliğinden gelen `q`
çerçevelerini sembol başına HALKA tamponunda (son HALKA_S sn) tutar; mirror_stream'den gelen emir
olaylarıyla pencere açar (new/accepted → sürekli kayıt; fill → dolum işareti + PAY_S sn kuyruk;
terminal → kapat) ve YALNIZ pencere içindeki quote'ları günlük JSONL'e yazar (`edg085_<gün>.jsonl`), ham
çerçeveyi ayrı dosyaya (`edg085_ham_<gün>.jsonl`, PK-2 ikinci kaynak). Abone kümesi: açık pozisyonlar ∪
bekleyen emir sembolleri ∪ bu süreçte dolum görmüş semboller (bracket bacağı hâlâ canlıdır),
≤ ABONE_TAVAN, öncelikli.

DEĞİŞMEZLER: kayıt dizini YALNIZ MERIDIAN_EDG085_KAYIT_DIZIN'den (kill#4: state/ ve defterlere
ASLA — yol MUTLAKtır, `store` mutlak adı state/ altına bağlamaz); hiçbir sinyalsiz except (Yasa 4:
yazım arızası quote_capture_yazim_dustu, dakikada bir); her motor dolumu işaret satırı alır —
quote yoksa kayip_nedeni dolu (kill#3); q çerçevesi hotstate'e ASLA gitmez (look-ahead: bu modülün
`hotstate` ile hiçbir teması yoktur). Bayrak MERIDIAN_QUOTE_CAPTURE varsayılan "0" — kapalıyken bu
modül hiçbir şey yapmaz (bit-özdeş davranış).

OKUR: portfolio.json (pozisyonlar), mirror_orders.json (açılış tohumu) — `store` üzerinden,
salt-okur; bekleyen durum sözlüğü `mirror_stream.PENDING`ten İTHAL edilir (kopya yok; ithal GEÇtir
— `mirror_stream` bu modülü modül düzeyinde ithal ettiği için erken ithal döngü olurdu).
YAZAR: yalnız kayıt dizinine, `store.append_jsonl` üzerinden (tek yazma kapısı; yazım yeri
`codelaw` desen katmanında ölçülebilsin diye ham `open` KULLANILMAZ).
OKUYUCU: research/olcumler/edg085_icra_ani_quote/rapor.py (Rol-1, salt-okur) —
`codelaw.DECLARED_SINK_PATTERNS` içindeki desen beyanı bu okuyucuyu adıyla taşır.
"""
from __future__ import annotations

import asyncio
import collections
import datetime as dt
import os

from . import obs, store
from .adapters.alpaca import ENGINE_COID_PREFIX

AKTIF_ENV = "MERIDIAN_QUOTE_CAPTURE"          # "1" → aktif; varsayılan "0"
DIZIN_ENV = "MERIDIAN_EDG085_KAYIT_DIZIN"     # boş/yok → dosya yazımı yok (aktifse bir kez warn)
HALKA_S = 90            # halka tamponu derinliği (sn)
PAY_S = 30              # pencere payı (kart: ±30 sn)
PENCERE_TAVAN_S = 1800  # sürekli kayıt tavanı (sn)
ABONE_TAVAN = 30        # t/q kanal tavanı
MOTOR_COID_ONEKI = ENGINE_COID_PREFIX   # "P-" — adaptörle TEK kaynak, kopyalanmaz
YAZIM_UYARI_ARALIK_S = 60               # yazım arızası uyarısı: dakikada en çok bir

#: Emir olayı sınıfları. `replaced` KAPANIŞ tarafındadır: yeni coid yeni pencere açar, eskisi
#: kapanır — aksi hâlde değiştirilmiş emrin penceresi tavan dolana dek açık kalırdı.
ACILIS_OLAYLARI = frozenset({"new", "accepted", "pending_new"})
DOLUM_OLAYLARI = frozenset({"fill"})
KISMI_OLAYLARI = frozenset({"partial_fill"})
KAPANIS_OLAYLARI = frozenset({"canceled", "cancelled", "expired", "rejected", "replaced",
                              "done_for_day"})


def aktif() -> bool:
    """Pilot bayrağı AÇIK mı? Varsayılan KAPALI — kapalıyken motorun davranışı bit-özdeştir."""
    return os.environ.get(AKTIF_ENV, "0") == "1"


def _dizin_env() -> str | None:
    """Kayıt dizini (kill#4: YALNIZ ortam değişkeninden; boşsa hiçbir dosya yazılmaz).

    YOL MUTLAK OLMAK ZORUNDADIR: `store._path` mutlak bir adı OLDUĞU GİBİ bırakır, ama GÖRELİ adı
    `state/` ALTINA bağlar — yani göreli bir değer (ansible değişkeni, `systemctl set-environment`)
    quote kaydını SESSİZCE canlı deftere düşürürdü; kill#4'ün tam yasakladığı şey budur. Göreli
    değer REDDEDİLİR ve dizin YOKMUŞ gibi davranılır (yazım durur) — ama sessizce değil: uyarı
    adıyla düşer, çünkü "yapılandırma yanlış" ile "yapılandırma yok" ayrı gerçeklerdir."""
    d = (os.environ.get(DIZIN_ENV) or "").strip()
    if d and not os.path.isabs(d):
        obs.warn("quote_capture_dizin_goreli", dizin=d,
                 detail="kayıt dizini MUTLAK olmalı — göreli değer state/ altına bağlanırdı "
                        "(kill#4); yazım DEVRE DIŞI")
        return None
    return d or None


def _iso(t: dt.datetime) -> str:
    """UTC saniye çözünürlüklü ISO damgası, `Z` ekli (satır `alindi` alanının tek biçimi)."""
    return t.astimezone(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _ts_coz(s) -> dt.datetime | None:
    """RFC3339 damgasını UTC datetime'a çevirir. Alpaca `t` alanı NANOSANİYE taşıyabilir; kesir
    6 haneye kırpılır (`fromisoformat` 7+ haneyi reddeder). Çözülemeyen damga UYDURULMAZ: None."""
    if not s:
        return None
    t = str(s).strip()
    if t.endswith("Z"):
        t = t[:-1] + "+00:00"
    tam, nokta, kalan = t.partition(".")
    if nokta:
        kesir = ""
        i = 0
        while i < len(kalan) and kalan[i].isdigit():
            kesir += kalan[i]
            i += 1
        t = f"{tam}.{kesir[:6]}{kalan[i:]}"
    try:
        d = dt.datetime.fromisoformat(t)
    except ValueError:  # sessiz-yutma: bozuk damga ÇÖZÜLEMEDİ — uydurma yasağı gereği None döner ve çağıran onu `..._neden` ile kaydeder
        return None
    return d if d.tzinfo else d.replace(tzinfo=dt.timezone.utc)


def _f(x) -> float | None:
    """Sayıya çevrilemeyen değer UYDURULMAZ: None (çağıran nedeni satıra yazar)."""
    try:
        return float(x)
    except (TypeError, ValueError):  # sessiz-yutma: fiyat alanı sayı DEĞİL — 0.0 yazmak ölçülmemişi ölçülmüş gösterirdi, None dürüst olan
        return None


class QuoteCapture:
    """Halka tamponu · emir pencereleri · abone kümesi · günlük JSONL yazıcı.

    Zaman ENJEKTE EDİLEBİLİR (`simdi`): pencere sınırları saat aritmetiğidir ve gerçek uykuyla
    sınanamaz. Kilit YOK — tek yazar süreç (uvicorn); iki akış da aynı event loop'unda koşar."""

    def __init__(self, dizin: str | None, simdi=None):
        """Kayıt dizinini (None = yazım yok), saati ve boş halkaları kurar; açılış tohumunu
        mirror_orders.json'dan okur (restart sonrası bekleyen emirler abone kümesinde kalsın)."""
        self._dizin = str(dizin) if dizin else None
        self._simdi = simdi or (lambda: dt.datetime.now(dt.timezone.utc))
        self._halka: dict[str, collections.deque] = {}
        self._pencereler: dict[str, dict] = {}     # coid -> pencere kaydı
        self._bekleyen: dict[str, str] = {}        # coid -> sembol (bekleyen emirler)
        self._dolan: list[str] = []                # dolum görmüş semboller (pozisyon vekili)
        self._abone: list[str] = []
        self._tavan_disi: set[str] = set()
        self._olay = asyncio.Event()
        # VARSAYILAN KAPALI (K7, dal-sonu incelemesi): ilk KANITLI canlılığa kadar soketin
        # kurulduğu BİLİNMEZ. True başlamak, worker açılışında auth'a takılan bir oturumda gelen
        # quote'suz dolumu "sembol sessizdi" diye YANLIŞ sınıflardı. marketstream kanıtlı olayda
        # True'ya çeker, oturum bitince False'a düşürür.
        self._baglanti_ok = False
        self._gun: str | None = None
        self._satir_bugun = 0
        self._ham_bugun = 0
        self._son_q_at: str | None = None
        self._yazim_hata_n = 0
        self._bilinmeyen_olay_n = 0
        self._dizin_uyarildi = False
        self._son_yazim_uyarisi: dt.datetime | None = None
        self._tohumla()

    # ---------------- tohum + abone kümesi ----------------
    def _tohumla(self) -> None:
        """Açılış tohumu: mirror_orders.json'daki BEKLEYEN emirler abone kümesine girer. PENDING
        sözlüğü `mirror_stream`ten İTHAL (kopya yok); ithal GEÇtir çünkü `mirror_stream` bu modülü
        modül düzeyinde ithal eder — erken ithal döngü olurdu."""
        from .mirror_stream import PENDING, STATE_FILE
        st = store.read_json(STATE_FILE, {}) or {}
        for coid, v in (st.get("orders") or {}).items():
            if str((v or {}).get("status", "")).lower() in PENDING and (v or {}).get("symbol"):
                self._bekleyen[str(coid)] = str(v["symbol"])

    def istenen_abonelik(self) -> list[str]:
        """Abone olunacak semboller, ÖNCELİK sırasıyla ve ABONE_TAVAN ile kırpılmış:
        açık pozisyon > motor öneki (`P-`) taşıyan bekleyen emir > diğer bekleyen emir > bu
        süreçte dolum görmüş sembol (bracket bacağı hâlâ canlı). Kırpılanlar `_tavan_disi`ne
        düşer ve o sembolün dolumu `tavan_asimi` ile işaretlenir — sessiz düşme yok (kill#3)."""
        pf = store.read_json("portfolio.json", {}) or {}
        motor = [s for c, s in self._bekleyen.items() if str(c).startswith(MOTOR_COID_ONEKI)]
        diger = [s for c, s in self._bekleyen.items() if not str(c).startswith(MOTOR_COID_ONEKI)]
        sirali: list[str] = []
        gorulen: set[str] = set()
        for s in list((pf.get("positions") or {}).keys()) + motor + diger + self._dolan:
            s = str(s).strip().upper()
            if s and s not in gorulen:
                gorulen.add(s)
                sirali.append(s)
        self._abone = sirali[:ABONE_TAVAN]
        self._tavan_disi = set(sirali[ABONE_TAVAN:])
        return list(self._abone)

    def abonelik_degisti(self) -> asyncio.Event:
        """marketstream eşlik görevinin beklediği olay: abone kümesi DEĞİŞMİŞ olabilir."""
        return self._olay

    def baglanti(self, ok: bool) -> None:
        """Data soketinin KANITLI durumu (marketstream yazar). Dolum işareti bunu okur: quote'suz
        bir dolum 'sembol sessizdi' mi yoksa 'soket kopuktu' mu — ikisi ayrı gerçektir ve ayrı
        `kayip_nedeni` alır (kill#3: sessiz düşürme yok)."""
        self._baglanti_ok = bool(ok)

    # ---------------- yazıcı ----------------
    def _yaz(self, ad: str, satir: dict) -> bool:
        """Kayıt dizinindeki `edg085_<ad>.jsonl` dosyasına tek satır ekler. TEK YAZMA KAPISI: iki
        dosya (kayıt + ham) da buradan geçer, dolayısıyla `codelaw` desen katmanında TEK çağrı yeri
        görünür. Dizin yoksa bir kez uyarır; yazım düşerse Yasa 4 gereği sinyal verir.

        `edg085_` ÖNEKİ LİTERALDİR ve f-string İÇİNDE kalmalıdır: `codelaw._joined_glob` sabit
        parçaları AYNEN korur, dolayısıyla türetilen desen anahtarı `*/edg085_*.jsonl` olur —
        öneksiz hâli `*/*.jsonl` idi ve beyanın altına düşebilecek yüzey çok daha genişti. Önek
        bir değişkene ya da yol bir yerel ada taşınırsa bu daralma KAYBOLUR (D2/v214 çivileri kırılır)."""
        if not self._dizin:
            if not self._dizin_uyarildi:
                self._dizin_uyarildi = True
                obs.warn("quote_capture_dizin_yok", env=DIZIN_ENV,
                         detail="EDG-085 kayıt dizini ayarlanmamış — quote kaydı diske YAZILMIYOR")
            return False
        try:
            store.append_jsonl(f"{self._dizin}/edg085_{ad}.jsonl", satir)
        except OSError as e:
            self._yazim_hata_n += 1
            simdi = self._simdi()
            son = self._son_yazim_uyarisi
            if son is None or (simdi - son).total_seconds() >= YAZIM_UYARI_ARALIK_S:
                self._son_yazim_uyarisi = simdi
                obs.warn("quote_capture_yazim_dustu", error=f"{type(e).__name__}: {e}"[:120],
                         yol=f"{self._dizin}/edg085_{ad}.jsonl", hata_n=self._yazim_hata_n)
            return False
        return True

    def _gun_tazele(self, simdi: dt.datetime) -> str:
        """Gün defteri adı (`alindi` UTC günü); gün dönünce günlük sayaçlar sıfırlanır."""
        gun = simdi.astimezone(dt.timezone.utc).strftime("%Y-%m-%d")
        if gun != self._gun:
            self._gun = gun
            self._satir_bugun = 0
            self._ham_bugun = 0
        return gun

    def _kayit_yaz(self, simdi: dt.datetime, satir: dict) -> None:
        """Kayıt defterine (`edg085_<gün>.jsonl`) bir satır."""
        if self._yaz(self._gun_tazele(simdi), satir):
            self._satir_bugun += 1

    def _ham_yaz(self, simdi: dt.datetime, m: dict) -> None:
        """Ham defterine (`edg085_ham_<gün>.jsonl`) gelen çerçeveyi OLDUĞU GİBİ (süzgeç/halka öncesi)."""
        if self._yaz(f"ham_{self._gun_tazele(simdi)}", m):
            self._ham_bugun += 1

    # ---------------- pencere yaşam döngüsü ----------------
    def _pencere_satiri(self, simdi, coid, sembol, olay, neden) -> None:
        """Pencere açılış/kapanış işareti — pencere yaşam döngüsü kayıttan OKUNABİLİR olmalı."""
        self._kayit_yaz(simdi, {"tur": "pencere", "alindi": _iso(simdi), "sembol": sembol,
                                "coid": coid, "olay": olay, "neden": neden})

    def _pencere_ac(self, simdi, coid, sembol, order, neden) -> dict:
        """Yeni pencere: işaret satırı + halka_geri dökümü (son PAY_S sn)."""
        p = {"sembol": sembol, "yon": order.get("side"), "baslangic": simdi,
             "dolum_ts": None, "kapanis": None, "faz": "pencere", "quote_n": 0}
        self._pencereler[coid] = p
        self._pencere_satiri(simdi, coid, sembol, "ac", neden)
        self._halka_geri_dok(simdi, coid, p)
        return p

    def _pencere_kapat(self, simdi, coid, neden) -> None:
        """Pencereyi kapatır ve NEDENİNİ yazar — kapanış sessiz olamaz."""
        p = self._pencereler.pop(coid, None)
        if p is not None:
            self._pencere_satiri(simdi, coid, p["sembol"], "kapat", neden)

    def _halka_geri_dok(self, simdi, coid, p) -> None:
        """Pencere açılışından ÖNCEKİ son PAY_S sn'lik quote'ları `halka_geri` fazıyla döker."""
        esik = simdi - dt.timedelta(seconds=PAY_S)
        for t, m in list(self._halka.get(p["sembol"]) or ()):
            if t >= esik:
                self._quote_yaz(t, coid, p, m, "halka_geri")

    def _quote_yaz(self, t, coid, p, m, faz) -> None:
        """Bir quote satırı (kayıt defteri) + ham çerçeve (ham defteri); pencere sayacı artar."""
        self._kayit_yaz(t, {"tur": "quote", "alindi": _iso(t), "ts": m.get("t"),
                            "sembol": m.get("S"), "coid": coid, "faz": faz,
                            "bid": m.get("bp"), "ask": m.get("ap"),
                            "bid_lot": m.get("bs"), "ask_lot": m.get("as"),
                            "bx": m.get("bx"), "ax": m.get("ax"), "kosul": m.get("c")})
        self._ham_yaz(t, m)
        p["quote_n"] += 1

    def _acik_pencere(self, sembol, simdi) -> tuple[str, dict] | None:
        """Sembolün AÇIK penceresi (en son açılan). Süresi dolmuşsa burada KAPATILIR ve None
        döner: pencere tavanı (`pencere_tavani`) ve dolum-sonrası kuyruğu (`fill+30s`) tek yerde."""
        for coid in reversed(list(self._pencereler)):
            p = self._pencereler[coid]
            if p["sembol"] != sembol:
                continue
            if p["faz"] == "pencere" and p["baslangic"] is not None \
                    and (simdi - p["baslangic"]).total_seconds() > PENCERE_TAVAN_S:
                self._pencere_kapat(simdi, coid, "pencere_tavani")
                return None
            if p["kapanis"] is not None and simdi > p["kapanis"]:
                self._pencere_kapat(simdi, coid, "fill+30s")
                return None
            return coid, p
        return None

    # ---------------- giriş yüzeyleri ----------------
    def q_geldi(self, m: dict) -> None:
        """marketstream'den gelen `q` çerçevesi: halkaya ekle, AÇIK pencere varsa kaydet.
        Pencere yoksa TEK BAYT yazılmaz — halka yalnız süreç-içi bellektir."""
        if not aktif():
            return
        sembol = m.get("S")
        if not sembol:
            return
        simdi = self._simdi()
        self._son_q_at = _iso(simdi)
        halka = self._halka.setdefault(sembol, collections.deque())
        halka.append((simdi, m))
        esik = simdi - dt.timedelta(seconds=HALKA_S)
        while halka and halka[0][0] < esik:
            halka.popleft()
        acik = self._acik_pencere(sembol, simdi)
        if acik is None:
            return
        coid, p = acik
        self._quote_yaz(simdi, coid, p, m, p["faz"])

    def olay(self, event: str, order: dict) -> None:
        """mirror_stream'den gelen trade_updates olayı: pencere aç / dolum işaretle / kapat."""
        if not aktif():
            return
        coid = order.get("client_order_id")
        sembol = order.get("symbol")
        if not coid or not sembol:
            return
        coid, sembol = str(coid), str(sembol).strip().upper()
        ev = str(event or "").lower()
        simdi = self._simdi()
        if ev in ACILIS_OLAYLARI:
            self._bekleyen[coid] = sembol
            self._olay.set()
            if coid.startswith(MOTOR_COID_ONEKI) and coid not in self._pencereler:
                self._pencere_ac(simdi, coid, sembol, order, ev)
        elif ev in DOLUM_OLAYLARI:
            self._dolum(simdi, coid, sembol, order)
        elif ev in KISMI_OLAYLARI:
            # KISMİ DOLUM: işaret satırı YAZILMAZ (tek işaret son `fill`de) — pencere açık kalır
            # ve quote sayımı sürer. Sessiz değil: son dolum satırı bütün pencereyi sayar.
            self._olay.set()
        elif ev in KAPANIS_OLAYLARI:
            self._bekleyen.pop(coid, None)
            self._olay.set()
            if coid in self._pencereler:
                self._pencere_kapat(simdi, coid, ev)
        else:
            self._bilinmeyen_olay_n += 1

    def _dolum(self, simdi, coid, sembol, order) -> None:
        """Dolum işareti: her motor dolumu BİR satır alır ve quote yakalanamadıysa `kayip_nedeni`
        ADIYLA doludur (kill#3). Sıra önemlidir: kayıp nedeni, bekleyen/dolan kümeleri
        GÜNCELLENMEDEN ÖNCE ölçülür — aksi hâlde emrin kendi dolumu onu 'abone değil' yapardı."""
        p = self._pencereler.get(coid)
        dolum_ts = order.get("filled_at") or _iso(simdi)
        kapanis = (_ts_coz(dolum_ts) or simdi) + dt.timedelta(seconds=PAY_S)
        if p is None:
            # BRACKET BACAĞI (uuid coid): pencere hiç açılmadı — halka_geri + dolum_sonrasi kuyruğu
            p = {"sembol": sembol, "yon": order.get("side"), "baslangic": None,
                 "dolum_ts": dolum_ts, "kapanis": kapanis, "faz": "dolum_sonrasi", "quote_n": 0}
            self._pencereler[coid] = p
            self._pencere_satiri(simdi, coid, sembol, "ac", "fill_bracket")
            self._halka_geri_dok(simdi, coid, p)
        else:
            p["dolum_ts"] = dolum_ts
            p["kapanis"] = kapanis
            p["faz"] = "dolum_sonrasi"
        abone = self.istenen_abonelik()
        fiyat = _f(order.get("filled_avg_price"))
        son = (self._halka.get(sembol) or None)
        son_q = None
        if son:
            _t, sm = son[-1]
            son_q = {"ts": sm.get("t"), "bid": sm.get("bp"), "ask": sm.get("ap")}
        if sembol in self._tavan_disi:
            neden = "tavan_asimi"
        elif sembol not in abone:
            neden = "abone_degil"
        elif p["quote_n"] == 0 and not self._baglanti_ok:
            neden = "baglanti_yok"
        elif p["quote_n"] == 0:
            neden = "sembol_sessiz"
        else:
            neden = None
        self._kayit_yaz(simdi, {"tur": "dolum", "alindi": _iso(simdi), "sembol": sembol,
                                "coid": coid, "yon": order.get("side"), "dolum_ts": dolum_ts,
                                "dolum_fiyat": fiyat,
                                "dolum_fiyat_neden": None if fiyat is not None
                                else "filled_avg_price sayıya çevrilemedi",
                                "quote_n_pencere": p["quote_n"], "son_quote": son_q,
                                "kayip_nedeni": neden})
        self._bekleyen.pop(coid, None)
        if sembol not in self._dolan:
            self._dolan.append(sembol)
        self._olay.set()

    def snapshot(self) -> dict:
        """Sağlık anlık görüntüsü — marketstream `/api/diagnostics` altında yayınlar."""
        return {"aktif": aktif(), "dizin": self._dizin, "abone_n": len(self._abone),
                "abone": list(self._abone), "pencere_acik": len(self._pencereler),
                "satir_bugun": self._satir_bugun, "ham_bugun": self._ham_bugun,
                "son_q_at": self._son_q_at, "yazim_hata_n": self._yazim_hata_n,
                "tavan_asimi_n": len(self._tavan_disi),
                "bilinmeyen_olay_n": self._bilinmeyen_olay_n,
                "baglanti_ok": self._baglanti_ok}


_KAYIT: QuoteCapture | None = None


def get() -> QuoteCapture:
    """Süreç-içi TEKİL kayıtçı (test fikstürü `quotecapture._KAYIT = None` ile sıfırlar).
    ÇİFT KAPI BİLİNÇLİ: bayrak kapalıyken de nesne döner, ama `olay`/`q_geldi` no-op'tur —
    modül kendi kendini de korur, çağıranın kapısına güvenmez."""
    global _KAYIT
    if _KAYIT is None:
        _KAYIT = QuoteCapture(_dizin_env())
    return _KAYIT
