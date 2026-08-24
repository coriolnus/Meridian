#!/usr/bin/env python3
"""olc.py — EDG-2026-055 "earnings fail-open gerçekleşmiş bedeli" RETRO SAYIM (tek hücre).

ROL: ölçüm. Bu betik SAYI üretir, HÜKÜM ÜRETMEZ. Kart (`research/cards/
EDG-2026-055-earnings-fail-open.yaml`) ön-kayıtlı ve eşikleri donmuştur; hüküm Rol-1'e aittir.

NE ÖLÇER (kartın tek hücresi `failopen_retro_sayim`, K += 1):
  Her CANLI girişte, o giriş ANINDA sembol earnings takvimi kapsamı DIŞINDA mıydı (= fail-open
  damgası)  ×  sonradan öğrenilen GERÇEK rapor tarihi girişten ≤ BLACKOUT_DAYS(5) gün sonra mıydı.
  Her iki soru da PIT (point-in-time) anlık görüntüleriyle sorulur; BUGÜNKÜ takvim hüküm yolunda
  HİÇ KULLANILMAZ (kart kill #1).

R1 ŞERHİ (kart `r1_pit_derinligi_serhi_2026_08_24`) — ZORUNLU ÖN-SAYIM:
  Karar kuralına girmeden önce `N_giris` (PIT penceresinde canlı giriş sayısı) ve
  `N_failopen_kapsam` (bunların kaçı fail-open damgası taşıyor) sayılır ve raporlanır.
  Dal 1: N_giris = 0            → hüküm YOK ("ölçülemedi — pencerede canlı giriş yok")
  Dal 2: N_giris≥1, kapsam = 0  → BETİMLEYİCİ (ölçülmüş-ret DEĞİL)
  Dal 3: N_failopen_kapsam ≥ 1  → success_metric AYNEN (vaka N + toplam R)
  Bu betik dalı yalnız ADLANDIRIR; damgayı/hükmü karta Rol-1 işler.

VERİ TABANI (salt-okuma, tek kaynak):
  `backups/a1/state-2026-08-22.tar.gz` — A1'in (canlı sistem) günlük state yedeği, bu Mac'e
  `ops/pull-a1-backups.sh` ile çekilmiş VM-dışı kopya. Yerel `state/` KULLANILMAZ (bayat ayna,
  çoğu dosya 2026-07-30) ve hiçbir şey `state/` altına YAZILMAZ. Yedekten yalnız üç üye açılır:
    state/history/earnings_snapshots.jsonl  → PIT takvim arşivi (hüküm yolu)
    state/meridian.db                       → canlı defter: trades + portfolio (açık pozisyonlar)
    state/earnings.csv                      → yalnız HÜKÜMSÜZ maruziyet vekili için
  Üyeler geçici bir dizine açılır ve koşum sonunda silinir; repoya ikili dosya bırakılmaz.

DETERMİNİZM: `datetime.now()` / rastgelelik YOK. Ölçüm tarihi ve kaynak yedek LİTERALdir. Çıktı
`sonuc.json` sort_keys ile yazılır → aynı girdi, bayt-özdeş çıktı.
"""
from __future__ import annotations

import ast
import datetime as dt
import hashlib
import json
import os
import shutil
import sqlite3
import tarfile
import tempfile

# --------------------------------------------------------------------------------------------------
# SABİTLER — hepsi literal (zamana bağlı çağrı yok)
# --------------------------------------------------------------------------------------------------
KART = "EDG-2026-055"
HUCRE = "failopen_retro_sayim"
OLCUM_TARIHI = "2026-08-24"          # literal: koşum gününden BAĞIMSIZ (determinizm)
BLACKOUT_DAYS = 5                     # meridian/earnings.py:BLACKOUT_DAYS — kapının kendi eşiği

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
YEDEK = os.path.join(REPO, "backups", "a1", "state-2026-08-22.tar.gz")
UYELER = ["state/history/earnings_snapshots.jsonl", "state/meridian.db", "state/earnings.csv"]
CIKTI = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sonuc.json")
DATA_PY = os.path.join(REPO, "meridian", "adapters", "data.py")


def _sha256(yol: str) -> str:
    h = hashlib.sha256()
    with open(yol, "rb") as f:
        for blok in iter(lambda: f.read(1 << 20), b""):
            h.update(blok)
    return h.hexdigest()


def _gun(a: str, b: str) -> int:
    """(a - b) gün farkı; iki tarih de 'YYYY-MM-DD'."""
    return (dt.date.fromisoformat(a) - dt.date.fromisoformat(b)).days


def _evren() -> list[str]:
    """REPLAY_UNIVERSE'ü meridian.adapters.data KAYNAĞINDAN ast ile okur.

    NEDEN import DEĞİL: modülü içe aktarmak ağ/state yan etkisi olan bir zinciri uyandırır; ölçüm
    ajanı motoru koşturmaz, yalnız sabiti okur."""
    agac = ast.parse(open(DATA_PY, encoding="utf-8").read())
    for d in agac.body:
        if isinstance(d, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "REPLAY_UNIVERSE" for t in d.targets):
            return [str(x) for x in ast.literal_eval(d.value)]
    raise RuntimeError("REPLAY_UNIVERSE bulunamadı")


# --------------------------------------------------------------------------------------------------
# 1) GİRDİLERİ AÇ
# --------------------------------------------------------------------------------------------------
def _uyeleri_ac(hedef: str) -> dict:
    with tarfile.open(YEDEK, "r:gz") as tf:
        kalan = set(UYELER)
        for uye in tf:
            if uye.name in kalan:
                tf.extract(uye, hedef, filter="data")
                kalan.discard(uye.name)
                if not kalan:
                    break
        if kalan:
            raise RuntimeError(f"yedekte bulunamayan üye(ler): {sorted(kalan)}")
    return {u: os.path.join(hedef, u) for u in UYELER}


def _pit_arsiv(yol: str) -> list[dict]:
    """PIT takvim arşivi: her satır bir tazeleme anlık görüntüsü (fetch_date + kayitlar)."""
    ham = [json.loads(s) for s in open(yol, encoding="utf-8") if s.strip()]
    cikti = []
    for r in ham:
        tarih = {}
        for t, d, _saat in r["kayitlar"]:
            tarih.setdefault(t.upper(), set()).add(d)
        cikti.append({"fetch_date": r["fetch_date"], "fetched_at": r["fetched_at"],
                      "source": r.get("source"), "digest": r.get("digest"),
                      "tickers": r["tickers"], "rows": r["rows"],
                      "max_date": max(d for _, d, _ in r["kayitlar"]),
                      "tarih": tarih})
    cikti.sort(key=lambda r: (r["fetch_date"], r["fetched_at"]))
    return cikti


def _canli_girisler(db: str) -> list[dict]:
    """PENCEREDEN BAĞIMSIZ tüm canlı girişler: kapanmış `live_paper` işlemler + AÇIK pozisyonlar.

    AÇIK POZİSYONLAR NEDEN SAYILIR: kaynak damgası (`ledgerstamp`) işlem KAPANIRKEN basılır; açık
    bir pozisyonun damgası henüz yoktur ama GİRİŞİ olmuştur. Paydayı yalnız kapanmışlardan kurmak
    örneklemi sessizce küçültürdü (R1 şerhinin uyardığı 'kuraklığı kanıt sanmak' hatasının ikizi).
    İkisi ayrı ayrı da raporlanır."""
    c = sqlite3.connect("file:" + db + "?mode=ro", uri=True)
    c.row_factory = sqlite3.Row
    out = []
    for t in c.execute("select * from trades where kaynak='live_paper' order by ts_open, id"):
        out.append({"kimlik": t["id"], "ticker": t["ticker"].upper(), "ts_open": t["ts_open"],
                    "ts_close": t["ts_close"], "durum": "kapali", "kaynak_damgasi": t["kaynak"],
                    "plan_id": t["plan_id"], "r_multiple": t["r_multiple"],
                    "pnl_dollars": t["pnl_dollars"]})
    pf = json.loads(c.execute("select doc_json from portfolio").fetchone()[0])
    for tic, p in sorted(pf.get("positions", {}).items()):
        out.append({"kimlik": f"ACIK-{tic}", "ticker": tic.upper(), "ts_open": p.get("ts_open"),
                    "ts_close": None, "durum": "acik", "kaynak_damgasi": None,
                    "plan_id": p.get("plan_id"), "r_multiple": None, "pnl_dollars": None})
    c.close()
    out.sort(key=lambda r: (r["ts_open"] or "", r["ticker"]))
    return out


def _plan_kapsam_damgasi(db: str, plan_id: str | None) -> str | None:
    """Planın KENDİ kaydettiği `earnings_blackout.coverage` damgası ('known'/'no_calendar_data').

    Defterde plan yoksa None döner — UYDURULMAZ. (`trade_plans` 500 satırlık dönen bir defter;
    eski planlar düşer.) Bu alan PIT yeniden kurulumunun ÇAPRAZ DOĞRULAMASIdır, hüküm yolu değil."""
    if not plan_id:
        return None
    c = sqlite3.connect("file:" + db + "?mode=ro", uri=True)
    r = c.execute("select extra_json from trade_plans where id=?", (plan_id,)).fetchone()
    c.close()
    if not r or not r[0]:
        return None
    for chk in (json.loads(r[0]).get("gate_checks") or []):
        if chk.get("check") == "earnings_blackout":
            return chk.get("coverage")
    return None


# --------------------------------------------------------------------------------------------------
# 2) PIT MANTIĞI
# --------------------------------------------------------------------------------------------------
# Tüm anlık görüntüler seans KAPANIŞINDAN sonra (≈20:1x UTC) alınır; canlı girişler ise açılışta
# (≈13:30 UTC) olur. Dolayısıyla bir X günü girişinde kapının elindeki takvim, `fetch_date < X`
# olan SON anlık görüntüdür. `fetch_date == X` olanı kullanmak GELECEĞİ SIZDIRIRDI.
def _asof(arsiv: list[dict], gun: str) -> dict | None:
    onceki = [s for s in arsiv if s["fetch_date"] < gun]
    return onceki[-1] if onceki else None


# Sonradan öğrenilen GERÇEK rapor tarihi: girişten SONRA (veya aynı gün, akşam) alınmış anlık
# görüntülerin birleşimi. Bugünkü `state/earnings.csv` burada KULLANILMAZ.
def _sonradan_ogrenilen(arsiv: list[dict], ticker: str, gun: str) -> dict:
    sonrakiler = [s for s in arsiv if s["fetch_date"] >= gun]
    tarihler = sorted({d for s in sonrakiler for d in s["tarih"].get(ticker, ())})
    ufuk = max((s["max_date"] for s in sonrakiler), default=None)
    return {"snapshot_n": len(sonrakiler), "rapor_tarihleri": tarihler, "bilgi_ufku": ufuk}


def main() -> int:
    tmp = tempfile.mkdtemp(prefix="edg055_")
    try:
        yollar = _uyeleri_ac(tmp)
        arsiv = _pit_arsiv(yollar["state/history/earnings_snapshots.jsonl"])
        db = yollar["state/meridian.db"]

        pencere_bas, pencere_son = arsiv[0]["fetch_date"], arsiv[-1]["fetch_date"]
        girisler = _canli_girisler(db)
        icerde = [g for g in girisler if g["ts_open"] and pencere_bas <= g["ts_open"] <= pencere_son]

        satirlar = []
        for g in icerde:
            tic, gun = g["ticker"], g["ts_open"]
            snap = _asof(arsiv, gun)
            sonra = _sonradan_ogrenilen(arsiv, tic, gun)
            s = {**g,
                 "asof_snapshot": snap["fetch_date"] if snap else None,
                 "plan_kayitli_kapsam_damgasi": _plan_kapsam_damgasi(db, g["plan_id"])}
            if snap is None:
                # PIT körlüğü: girişten önce anlık görüntü yok → kapsam SORULAMAZ (uydurma yok)
                s.update({"kapsam_asof": None, "fail_open": None,
                          "olculemedi_neden": "girişten ÖNCE PIT anlık görüntüsü yok — "
                                              "o gün takvimde ne olduğu arşivden bilinemez"})
            else:
                asof_tarihler = sorted(snap["tarih"].get(tic, ()))
                kapsam = bool(asof_tarihler)
                s.update({"kapsam_asof": "known" if kapsam else "no_calendar_data",
                          "asof_rapor_tarihleri": asof_tarihler,
                          "asof_ileri_capa_var": any(d >= gun for d in asof_tarihler),
                          "fail_open": not kapsam, "olculemedi_neden": None})

            # VAKA: fail-open × sonradan öğrenilen rapor tarihi [giriş, giriş+5] içinde
            s["sonradan_ogrenilen_rapor_tarihleri"] = sonra["rapor_tarihleri"]
            s["gercek_bilgi_ufku"] = sonra["bilgi_ufku"]
            pencere_ici = [d for d in sonra["rapor_tarihleri"] if 0 <= _gun(d, gun) <= BLACKOUT_DAYS]
            if s["fail_open"] is None:
                s["vaka"] = None
            elif not s["fail_open"]:
                s["vaka"] = False
                s["vaka_neden"] = "fail-open damgası YOK (giriş anında sembol kapsam içindeydi)"
            elif pencere_ici:
                s["vaka"] = True
                s["vaka_rapor_tarihi"] = pencere_ici[0]
            elif sonra["bilgi_ufku"] and _gun(sonra["bilgi_ufku"], gun) >= BLACKOUT_DAYS:
                s["vaka"] = False
                s["vaka_neden"] = ("fail-open AMA sonradan öğrenilen takvim giriş+5 ufkunu KAPSIYOR "
                                   "ve o aralıkta rapor yok")
            else:
                s["vaka"] = None
                s["olculemedi_neden"] = ("fail-open; sonradan öğrenilen takvimin ufku giriş+5'e "
                                         "YETMİYOR — rapor olup olmadığı arşivden bilinemez")
            satirlar.append(s)

        # ---------- ZORUNLU ÖN-SAYIM (R1) ----------
        n_giris = len(satirlar)
        n_failopen = sum(1 for s in satirlar if s["fail_open"] is True)
        n_kapsam_olculemedi = sum(1 for s in satirlar if s["fail_open"] is None)
        if n_giris == 0:
            dal = "R1-dal-1: N_giris=0 → hüküm YOK (ölçülemedi, pencerede canlı giriş yok)"
        elif n_failopen == 0:
            dal = "R1-dal-2: N_giris>=1 ve N_failopen_kapsam=0 → BETİMLEYİCİ (ölçülmüş-ret DEĞİL)"
        else:
            dal = "R1-dal-3: N_failopen_kapsam>=1 → success_metric AYNEN (vaka N + toplam R)"

        # ---------- HÜCRE ----------
        vakalar = [s for s in satirlar if s["vaka"] is True]
        vaka_olculemedi = [s for s in satirlar if s["vaka"] is None]
        vaka_r = [s["r_multiple"] for s in vakalar if s["r_multiple"] is not None]
        hucre = {
            "hucre": HUCRE,
            "vaka_n": len(vakalar),
            "vaka_toplam_r": (round(sum(vaka_r), 4) if vakalar and vaka_r else None),
            "vaka_toplam_pnl_dolar": (round(sum(s["pnl_dollars"] for s in vakalar
                                                if s["pnl_dollars"] is not None), 2)
                                      if vakalar else None),
            "vaka_r_olculemeyen_n": len(vakalar) - len(vaka_r),
            "vaka_olculemedi_n": len(vaka_olculemedi),
            "toplam_r_neden": (None if (vakalar and vaka_r) else
                               "vaka kümesi BOŞ — toplanacak R yok; 0.0 yazmak yokluğu ölçüm "
                               "gibi gösterirdi"),
            "vaka_listesi": [{"kimlik": s["kimlik"], "ticker": s["ticker"], "ts_open": s["ts_open"],
                              "rapor": s.get("vaka_rapor_tarihi"), "r": s["r_multiple"]}
                             for s in vakalar],
        }

        # ---------- BETİMLEYİCİ (hükümsüz) ----------
        kapali = [s for s in satirlar if s["durum"] == "kapali"]
        kapali_r = [s["r_multiple"] for s in kapali if s["r_multiple"] is not None]
        # bayat çapa: kapsam VAR ama bilinen tek tarih GEÇMİŞTE → kapı "known" der, ileri çapa yok
        bayat_capa = [s["ticker"] for s in satirlar
                      if s.get("kapsam_asof") == "known" and s.get("asof_ileri_capa_var") is False]
        evren = _evren()
        bugun_takvim = set()
        with open(yollar["state/earnings.csv"], encoding="utf-8") as f:
            for i, satir in enumerate(f):
                p = satir.strip().split(",")
                if i == 0 and p and p[0].lower() in ("ticker", "symbol"):
                    continue
                if p and p[0]:
                    bugun_takvim.add(p[0].upper())
        kapsam_disi_bugun = sorted(set(evren) - bugun_takvim)
        c = sqlite3.connect("file:" + db + "?mode=ro", uri=True)
        toplam_islem = c.execute("select count(*) from trades").fetchone()[0]
        kd_islem = c.execute(
            "select count(*) from trades where upper(ticker) in (%s)"
            % ",".join("?" * len(kapsam_disi_bugun)), kapsam_disi_bugun).fetchone()[0]
        c.close()

        sonuc = {
            "kart": KART,
            "hucre_sayisi_K_katkisi": 1,
            "olcum_tarihi": OLCUM_TARIHI,
            "rol_beyani": "ÖLÇÜM — bu dosya SAYI taşır, HÜKÜM taşımaz; damgayı Rol-1 işler",
            "kaynak": {
                "yedek": os.path.relpath(YEDEK, REPO),
                "yedek_sha256": _sha256(YEDEK),
                "uye_sha256": {u: _sha256(y) for u, y in sorted(yollar.items())},
                "not": "A1 (canlı) günlük state yedeği, VM-dışı yerel kopya; yerel state/ "
                       "KULLANILMADI (bayat) ve hiçbir şey state/ altına YAZILMADI",
            },
            "pit_arsiv": {
                "snapshot_n": len(arsiv),
                "pencere": [pencere_bas, pencere_son],
                "fetch_date_listesi": [s["fetch_date"] for s in arsiv],
                "kaynaklar": sorted({s["source"] for s in arsiv if s["source"]}),
                "son_snapshot_bilgi_ufku": arsiv[-1]["max_date"],
                "asof_kurali": "giriş günü X için kapının elindeki takvim = fetch_date < X olan SON "
                               "anlık görüntü (tazelemeler ≈20:1x UTC, girişler ≈13:30 UTC)",
            },
            "on_sayim_R1": {
                "N_giris": n_giris,
                "N_giris_kapali_live_paper": sum(1 for s in satirlar if s["durum"] == "kapali"),
                "N_giris_acik_pozisyon": sum(1 for s in satirlar if s["durum"] == "acik"),
                "N_failopen_kapsam": n_failopen,
                "N_kapsam_olculemedi": n_kapsam_olculemedi,
                "pencere": [pencere_bas, pencere_son],
                "snapshot_n": len(arsiv),
                "ateslenen_dal": dal,
                "kapsam_damgasi_capraz_dogrulama": {
                    "plan_defterinde_bulunan": sum(
                        1 for s in satirlar if s["plan_kayitli_kapsam_damgasi"] is not None),
                    "plan_defterinde_bulunmayan": sum(
                        1 for s in satirlar if s["plan_kayitli_kapsam_damgasi"] is None),
                    "celiski": [s["kimlik"] for s in satirlar
                                if s["plan_kayitli_kapsam_damgasi"] is not None
                                and s["plan_kayitli_kapsam_damgasi"] != s["kapsam_asof"]],
                    "not": "plan defteri 500 satırlık DÖNEN defter; düşen planın damgası None "
                           "kalır ve UYDURULMAZ — hüküm yolu PIT yeniden kurulumudur",
                },
            },
            "hucre_sonucu": hucre,
            "giris_tablosu": satirlar,
            "betimleyici_hukumsuz": {
                "beyan": "aşağıdakiler karar kuralına GİRMEZ; yalnız paydayı ve bağlamı gösterir",
                "pencere_kapali_islem_n": len(kapali),
                "pencere_kapali_toplam_r": round(sum(kapali_r), 4) if kapali_r else None,
                "bayat_capa_girisler": sorted(bayat_capa),
                "bayat_capa_not": "kapsam 'known' AMA giriş anında bilinen tek rapor tarihi "
                                  "GEÇMİŞTE — kapı sembolü tanıyor ama ileri çapası yok; bu "
                                  "kartın fail-open ekseninden AYRI bir olgudur, sayılır ve "
                                  "hüküm taşımaz",
                "maruziyet_vekili": {
                    "evren": len(evren),
                    "takvimde_bugun": len(set(evren) & bugun_takvim),
                    "kapsam_disi_bugun_n": len(kapsam_disi_bugun),
                    "kapsam_disi_bugun": kapsam_disi_bugun,
                    "tarihsel_islem_toplam": toplam_islem,
                    "tarihsel_islem_kapsam_disi_sembolde": kd_islem,
                    "pay_yuzde": round(100 * kd_islem / max(1, toplam_islem), 2),
                    "uyari": "bu blok BUGÜNKÜ takvimi kullanır ve bilerek HÜKÜMSÜZDÜR — geçmiş "
                             "bir girişin kazanç gününe denk gelip gelmediğini SORMAZ, yalnız "
                             "bugün kapsam dışı olan sembollerin defterdeki payını sayar "
                             "(kartın 'maruziyet vekili' kalemi). Hüküm yolu SALT PIT'tir.",
                },
            },
            "kill_kontrolleri": {
                "bugunku_takvimle_gecmis_yargilandi_mi": {
                    "sonuc": "HAYIR",
                    "kanit": "hüküm yolundaki iki soru da yalnız earnings_snapshots.jsonl'dan "
                             "yanıtlandı: kapsam = fetch_date<giriş olan son anlık görüntü, "
                             "gerçek rapor = fetch_date>=giriş anlık görüntüleri. "
                             "state/earnings.csv YALNIZ hükümsüz maruziyet vekilinde okundu.",
                },
                "damgasiz_islem_vakaya_sayildi_mi": {
                    "sonuc": "HAYIR",
                    "kanit": "vaka yüklemi `fail_open is True` şartına bağlı; fail_open False ya "
                             "da None olan satır vakaya GİREMEZ (None ayrı sayılır).",
                },
                "kapi_tasarimina_dokunuldu_mu": {
                    "sonuc": "HAYIR",
                    "kanit": "bu betik yalnız okur; meridian/ altında hiçbir dosya değişmedi, "
                             "meridian import bile edilmedi (REPLAY_UNIVERSE ast ile okundu).",
                },
                "ikinci_eksen_alt_dilim_eklendi_mi": {
                    "sonuc": "HAYIR",
                    "kanit": "hükümlü hücre TEK: failopen_retro_sayim (K += 1). Diğer her sayı "
                             "`betimleyici_hukumsuz` altında ve eşiksizdir.",
                },
            },
            "olculemeyenler": [s for s in
                               ({"kimlik": x["kimlik"], "neden": x.get("olculemedi_neden")}
                                for x in satirlar) if s["neden"]],
        }
        with open(CIKTI, "w", encoding="utf-8") as f:
            json.dump(sonuc, f, ensure_ascii=False, indent=2, sort_keys=True)
            f.write("\n")
        print(f"N_giris={n_giris}  N_failopen_kapsam={n_failopen}  "
              f"pencere={pencere_bas}..{pencere_son}  snapshot_n={len(arsiv)}")
        print(f"vaka_n={hucre['vaka_n']}  vaka_toplam_r={hucre['vaka_toplam_r']}  "
              f"vaka_olculemedi_n={hucre['vaka_olculemedi_n']}")
        print(dal)
        print(f"yazildi: {CIKTI}")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
