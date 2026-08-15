"""sieve.py — eleme muhasebesi: her sessiz `continue`yi sayılı ve gerekçeli bir kayda çevirir.

Sessiz-hata sınıfının ortak biçimi şudur: `.get()` None döndü → satır çıplak bir `continue` ile
atlandı → bir sayı sessizce küçüldü → kimse fark etmedi (gerçek işlemlerin tamamının eksik alan
yüzünden kalibrasyondan elenmesi, takma ada dönüşen alan adları, rejimsiz kanıttan üretilen
rejim-tavsiyesi hep bu sınıftı; harmanlanmış tek sayı kaybı gizler). Amaç tek cümledir:
**"0 satır çıktı" bir daha asla "zaten satır yoktu" ile karıştırılamasın.**

ÇEKİRDEK FİKİR — NEDEN SINIFLANDIRMASI (modülün asıl değeri): `sema:*` = VERİ SÖZLEŞMESİ nedeni
(eksik alan, yanlış anahtar biçimi, takma ad uyuşmazlığı, çözülemeyen değer — bu bir HATADIR,
birinin kodu/defteri düzeltmesi gerekir) · `piyasa:*` = MEŞRU iş filtresi (eşik altı skor, yanlış
rejim, girilmemiş plan, kazanç ambargosu — bu BİLGİDİR, sistemin çalıştığının kanıtı). Sınıfsız
neden REDDEDİLİR (`classify` ValueError atar): cevapsızlığa geri dönüş yolu kapalıdır.

GİRİŞLER: `Sieve` (tek tüketim aşamasının defteri; bağlam yöneticisi — `keep`/`drop` sayar,
çıkışta `flush` aşamanın SON koşusunu state/sieve.json'a kilitli oku-değiştir-yaz ile işler),
`stages`/`report`/`ok` (dedektör + pano görünümü: girdisi olup çıktısı sıfır VE şema elemesi olan
aşama KRİTİK; her `sema:` eleme HATA; şema oranı eşiği aşarsa KRİTİK — `piyasa:` elemesi hiçbir
kural tetiklemez, dedektör kurt masalı anlatmaz), KÜNYE katmanı `provenance`/`provenance_of`
(hiçbir toplulaştırılmış sayı PAYDASIZ ve KAYNAKSIZ var olamaz; `_kaynak` alanı gerçek/simüle
kırılımını ve besleyen aşamaları taşır).

SIFIR YETKİ: burada hiçbir şey karar vermez, hiçbir işlem/portföy durumuna dokunmaz; yalnız sayar
ve rapor eder. Okur/yazar: yalnız state/sieve.json.
"""
from __future__ import annotations

import datetime as dt

from . import store

SIEVE_FILE = "sieve.json"

SEMA = "sema:"          # veri sözleşmesi nedeni → HATA
PIYASA = "piyasa:"      # meşru iş filtresi   → BİLGİ
CLASSES = (SEMA, PIYASA)

# Bir aşamanın girdisinin bu oranından fazlası ŞEMA yüzünden elendiyse mesele tek bir bozuk satır
# değildir: o aşamanın ürettiği HER sayı eksik kanıtla hesaplanmıştır → tırmandırılır.
SEMA_ESCALATE_FRAC = 0.10
SEMA_ESCALATE_MIN_N = 5     # bunun altında oran istatistik değil gürültüdür


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def classify(reason: str) -> str:
    """Nedenin sınıfı ('sema' | 'piyasa'). Sınıfsız neden KABUL EDİLMEZ."""
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("eleme nedeni boş olamaz — sessiz `continue`ye geri dönüş yok")
    for c in CLASSES:
        if reason.startswith(c):
            return c[:-1]
    raise ValueError(
        f"sınıfsız eleme nedeni: {reason!r} — 'sema:' (veri sözleşmesi hatası, yani BUG) ya da "
        f"'piyasa:' (meşru iş filtresi, yani BİLGİ) önekiyle başlamalı")


class Sieve:
    """Tek bir tüketim AŞAMASININ eleme defteri.

    Kullanım (bağlam yöneticisi — çıkışta kendini diske yazar):

        with Sieve("score_calibration.gercek") as sv:
            for t in rows:
                if t.get("score") is None:
                    sv.drop("sema:eksik_alan:score"); continue
                sv.keep()

    `in` = keep + bütün elemeler; `out` = kullanılan satır sayısı. İkisini AYNI yerde tutmak,
    "kaç girdi / kaç çıktı" sorusunun cevabını yorumdan değil sayaçtan almayı zorunlu kılar.
    """

    def __init__(self, stage: str, persist: bool = True):
        if not isinstance(stage, str) or not stage.strip():
            raise ValueError("aşama adı zorunlu — sahipsiz eleme muhasebesi olmaz")
        self.stage = stage
        self.persist = persist
        self.n_in = 0
        self.n_out = 0
        self.drops: dict[str, int] = {}

    # ---- sayaçlar ----
    def keep(self, n: int = 1) -> None:
        self.n_in += n
        self.n_out += n

    def drop(self, reason: str, n: int = 1, from_kept: bool = False) -> None:
        """Bir (ya da n) satırı GEREKÇESİYLE ele.

        from_kept=True: satır daha önce `keep()` edilmişti ama sonradan düştü (ör. son-100 taze
        pencere kırpması). Bu satırlar girdiye İKİNCİ kez sayılmaz; yalnız çıktıdan düşülür —
        yoksa `in` uydurma biçimde şişer ve muhasebe kendi kendine yalan söylemeye başlar."""
        classify(reason)                       # sınıfsızsa BURADA patlar (sessizliğe dönüş yok)
        if from_kept:
            self.n_out = max(0, self.n_out - n)
        else:
            self.n_in += n
        self.drops[reason] = self.drops.get(reason, 0) + n

    # ---- rapor / kalıcılık ----
    def snapshot(self) -> dict:
        return {"in": self.n_in, "out": self.n_out, "drops": dict(self.drops), "ts": _now()}

    def flush(self) -> dict:
        """Aşamanın son durumunu state/sieve.json'a KİLİTLİ oku-değiştir-yaz ile işler.
        Aşama başına SON koşu tutulur (kümülatif değil): "şu anda kaç satır eleniyor?" sorusu,
        aylar önceki bir koşunun toplamıyla sulandırılmamalı."""
        snap = self.snapshot()
        if not self.persist:
            return snap

        def _apply(doc):
            if not isinstance(doc, dict):
                doc = {}
            doc[self.stage] = snap
            return True

        try:
            store.update_json(SIEVE_FILE, _apply, {})
        except Exception as e:
            # muhasebe defteri yazılamazsa bu da SESSİZ kalmaz — ama okuma-modeli çağrısını
            # (pano/kalibrasyon) düşürmez: eleme sayacı bir kanıt katmanıdır, karar katmanı değil.
            try:
                from . import obs
                obs.warn("sieve_flush_failed", stage=self.stage, error=type(e).__name__)
            except Exception:  # sessiz-yutma: SON ÇARE — uyarı kanalının kendisi düştü; burada yapılacak tek şey muhasebenin ölçtüğü işi düşürmemektir
                pass
        return snap

    def __enter__(self) -> "Sieve":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        self.flush()          # istisna çıksa bile o ana kadarki muhasebe diske düşer
        return False          # istisnayı ASLA yutma


# ---------------------------------------------------------------- rapor / dedektör
def stages(doc: dict | None = None) -> dict:
    d = doc if doc is not None else (store.read_json(SIEVE_FILE, {}) or {})
    return d if isinstance(d, dict) else {}


def report(doc: dict | None = None) -> dict:
    """Dedektör + pano görünümü. `violations` operatöre gösterilecek Türkçe `detail` taşır.

    KURALLAR
      (a) `in > 0` ve `out == 0`  → KRİTİK. Aşama sıfır kanıtla çalışıyor; "veri yok" değil,
          "veri elendi". Canlıda tam bu oldu (gerçek 90 satır girdi, 0 çıktı).
      (b) herhangi bir `sema:` eleme → HATA. Veri sözleşmesi tutmuyor demektir.
      (c) `sema:` oranı eşiği aşarsa → KRİTİK (tek bozuk satır değil, sistematik bozukluk).
    `piyasa:` elemeleri hiçbir kural tetiklemez — dedektör kurt masalı anlatmamalı."""
    d = stages(doc)
    out_stages: dict[str, dict] = {}
    violations: list[dict] = []
    for name, st in sorted(d.items()):
        if not isinstance(st, dict):
            continue
        n_in = int(st.get("in") or 0)
        n_out = int(st.get("out") or 0)
        drops = {k: int(v) for k, v in (st.get("drops") or {}).items()}
        sema_n = sum(v for k, v in drops.items() if k.startswith(SEMA))
        piyasa_n = sum(v for k, v in drops.items() if k.startswith(PIYASA))
        frac = round(sema_n / n_in, 3) if n_in else 0.0
        out_stages[name] = {"in": n_in, "out": n_out, "drops": drops, "sema_drops": sema_n,
                            "piyasa_drops": piyasa_n, "sema_frac": frac, "ts": st.get("ts")}
        top = max(drops.items(), key=lambda kv: kv[1])[0] if drops else "—"
        # KURT MASALI YASAĞI: tamamı ELENDİ ama elemelerin HEPSİ `piyasa:` ise bu
        # "veri elendi" (bug) DEĞİL, "bu kanıt türü henüz yok" (bilgi) demektir — replay'de LLM
        # görüşü ya da canlı gölge-tahmin çifti bulunmaması gibi. Sınıfa bakmadan kırmızı yakmak,
        # tam olarak sieve'in engellemek için var olduğu şeydir: operatör kırmızıyı yok saymayı
        # öğrenir, sonra GERÇEK `sema:` ihlali de görünmez olur. `hepsi_elendi` yalnız en az bir
        # `sema:` eleme varsa kritiktir; saf `piyasa:` silinme aşama tablosunda görünür ama ihlal değil.
        if n_in > 0 and n_out == 0 and sema_n > 0:
            violations.append({
                "stage": name, "rule": "hepsi_elendi", "severity": "kritik",
                "detail": (f"'{name}': {n_in} satır girdi, HİÇBİRİ kullanılmadı ve elemede ŞEMA hatası "
                           f"var. Ekrandaki sayı 'veri yok' demek değil, 'veri vardı ama elendi' demek. "
                           f"En çok elenen neden: {top}.")})
        if sema_n:
            liste = ", ".join(f"{k}×{v}" for k, v in sorted(drops.items())
                              if k.startswith(SEMA))
            violations.append({
                "stage": name, "rule": "sema_elemesi", "severity": "hata",
                "detail": (f"'{name}': {sema_n} satır VERİ SÖZLEŞMESİ yüzünden elendi ({liste}). "
                           f"Bu bir piyasa filtresi DEĞİL, yazılım hatasıdır: satır beklenen alanı "
                           f"taşımıyor ve hesaptan sessizce düşüyor.")})
        if n_in >= SEMA_ESCALATE_MIN_N and frac > SEMA_ESCALATE_FRAC:
            violations.append({
                "stage": name, "rule": "sema_orani_yuksek", "severity": "kritik",
                "detail": (f"'{name}': giren {n_in} satırın %{frac * 100:.0f}'i şema yüzünden "
                           f"elendi (eşik %{SEMA_ESCALATE_FRAC * 100:.0f}). Tek bozuk satır değil, "
                           f"sistematik bir uyumsuzluk — bu aşamanın ürettiği HER sayı eksik "
                           f"kanıtla hesaplanmıştır.")})
    return {"generated": _now(), "n_stages": len(out_stages), "stages": out_stages,
            "violations": violations, "ok": not violations,
            "note": "sema: = veri sözleşmesi hatası (BUG) · piyasa: = meşru iş filtresi (BİLGİ)"}


def ok(doc: dict | None = None) -> bool:
    return bool(report(doc)["ok"])


# ---------------------------------------------------------------- KÜNYE (provenance)
# KURAL: hiçbir toplulaştırılmış sayı, PAYDASI ve KAYNAĞI olmadan var olamaz. "gerçek 0 / simüle 241"
# tam olarak bu kural olmadığı için görünmezdi: tek harmanlanmış rakam yayınlanıyordu.
PROV_KEY = "_kaynak"

SRC_MIXED = "gerçek+simüle"
SRC_REAL_ONLY = "yalnız-gerçek"
SRC_CF_ONLY = "yalnız-simüle"
SRC_INTERSECTION = "kesişim (her satır hem gerçek hem simüle)"
SRC_EMPTY = "veri yok"
SRC_UNKNOWN_INPUT = "dışarıdan verilen matris — kaynak bilinmiyor"

# NEDEN `n` DEĞİL `n_total`: künye bazı artefaktların (regime_edge.json) KÖKÜNE, yani "rejim adı →
# istatistik" haritasının içine giriyor. O haritayı okuyan iki tüketici (watchdog'un ölçülen-edge
# dedektörü ve hermes'in kanıt paketi) bir değeri "n'i olan sözlük" diye rejim sanıyor. Künyede `n`
# alanı olsaydı sahte bir rejim gibi sayılır ve watchdog'un "her rejimde edge negatif" alarmını
# SUSTURABİLİRDİ (len(neg) < len(meas) payda şişer). Ad farkı bu tuzağı yapısal olarak kapatıyor.
def provenance(n_total: int, n_real: int | None = None, n_cf: int | None = None,
               source: str | None = None, stages_: tuple | list = ()) -> dict:
    """Bir toplulaştırılmış artefaktın künyesi: PAYDA (n_total), gerçek/simüle kırılımı, üretim
    zamanı, kaynak beyanı ve muhasebesini tutan eleme aşamaları.

    Kırılımın anlamsız olduğu yerde SAYI UYDURULMAZ: `n_real`/`n_cf` verilmez ve `source` açıkça
    yazılır (ör. SRC_INTERSECTION)."""
    if source is None:
        if n_real is None or n_cf is None:
            raise ValueError("kırılım verilmediyse `source` AÇIKÇA beyan edilmeli — "
                             "künyesiz toplulaştırma yasak (bkz. 'gerçek 0 / simüle 241')")
        if not n_real and not n_cf:
            source = SRC_EMPTY
        elif n_real and n_cf:
            source = SRC_MIXED
        else:
            source = SRC_REAL_ONLY if n_real else SRC_CF_ONLY
    out = {"n_total": int(n_total), "generated": _now(), "source": source}
    if n_real is not None or n_cf is not None:
        out["n_real"] = int(n_real or 0)
        out["n_cf"] = int(n_cf or 0)
    if stages_:
        out["stages"] = list(stages_)
    return out


def provenance_of(artifact: dict | None) -> dict | None:
    """Artefaktın künyesini çıkar (kök `_kaynak`). Yoksa None — 'künyesiz' cevabı da bir cevaptır."""
    if not isinstance(artifact, dict):
        return None
    p = artifact.get(PROV_KEY)
    return p if isinstance(p, dict) else None
