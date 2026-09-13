"""pk3_selef.py — EDG-2026-088 POZİTİF KONTROL (3) "SELEF": EDG-2026-049'un 6 uyuyan (dormant)
pullback planını GÖLGE MOTORUNDAN geçirir ve 049'un işaretiyle (6/6 kayıp) kıyaslar.

SORU. Kart `EDG-2026-088` `pozitif_kontrol` (3): "EDG-049'un 6 dormant planı gölgede yeniden
yürütülür → aynı işaret (6/6 kayıp) çıkmalı; çıkmazsa gölge motoru ile 049 karşı-olgusu ayrışıyor
demektir → harness kör sayılır." Bu betik o kontrolün ŞASİ KOŞUMUDUR (kart notu 2026-09-08: "şasi
koşumu TSK-179 alt kalemi olarak pencere hükmünden ÖNCE yapılır").

NİÇİN BİR ŞASİ GEREKTİ. B1 teslimindeki ilk deneme (Task 3) 6 planı sayaç/çivi ölçeğinde yeniden
DOĞURAMADI: `strategy.evaluate_pullback` `rs_rating_value` kapısı KESİTSELdir (bir günün göreli
güç sıralaması TÜM evrenden türer), 049 artefaktında `rs` alanı YOK ve tek-sembollü bir çağrı o
kapıyı ölçemez. Rol-1 hükmü (3) bu yüzden seçenek (c)'dir: üçlü (tarih, sembol, kurulum) DONMUŞ
`edg032c` parametreleriyle `strategy.scan_all`dan YENİDEN DOĞURULUR; doğmazsa PK (3) "ölçülemedi
— harness kör"dür. `r_multiple`dan stop TÜRETİLMEZ (049 satırlarında stop/profit_target yoktur;
türetmek ölçülen şeyi uydurulan şeye çevirirdi — UYDURMA YASAĞI).

ÜÇ AŞAMA, ÜÇÜ DE İTHAL EDİLMİŞ ÜRETİM YOLU (kopya değil):
  1. DOĞUM — `cf_backfill._plans_for_session`. Bu fonksiyon canlı `loop.daily_cycle`ın P2+P3
     bloklarının tarihsel kardeşidir ve `backtest.replay`in de kardeşidir: kesitsel `rs_map`
     (`indicators.rs_rating`, `strategy.RS_LOOKBACK`), rejim (`regime.build_regime_json`), etkin
     parametreler (`config.resolve_params` + `earnings.pit_arsiv`), `strategy.scan_all` ve
     `guard.classify_gate` AYNI çağrı zincirinden geçer. Uyuyan plan sözlüğünün alan kümesi de
     oradan gelir (`dormant_setup=True`, `gate_verdict`, `entry_trigger`/`stop`/`profit_target`) —
     bu betik plan sözlüğünü KENDİSİ KURMAZ.
  2. GÖLGE — `golge_icra.adim`, seans seans, D+1'den kapanışa. Giriş/çıkış yasaları motorun
     kendisinindir (`broker.entry_limit_price`, `broker.PaperBroker._touch_exit`,
     `strategy.manage_position`); bu betik yalnız takvimi, barları ve rejimi besler.
  3. KIYAS — 6 gölge satırının R İŞARETİ ile 049 satırlarının işareti. Eşik YOKTUR: kart PK'sı bir
     İŞARET kontrolüdür, bir büyüklük sınaması değil. Toplam R farkı BETİMLEYİCİ olarak raporlanır.

BEYANLI SAPMALAR (ölçüldü — sessiz değil, yazılı; raporun `sapmalar` bloğunda da durur):
  (a) PLAN KİMLİĞİ. 049 planları pullback'in HÂLÂ SİLAHLI olduğu dünyada (edg032b) doğdu, o yüzden
      kimlikleri normal şemadadır (`P-<tarih>-<sembol>`). Bugün pullback `strategy.ARMED_SETUPS`
      dışındadır ve `cf_backfill._plans_for_session` uyuyan planlara kurulum ekli kimlik verir
      (`P-<tarih>-<sembol>-<kurulum>`). AYNI plan, FARKLI ad; eşleştirme (tarih, sembol) üzerinden
      yapılır ve her iki kimlik de raporda yan yana durur.
  (b) İCRA SEMANTİĞİ. 049 bir PORTFÖY replay'idir (boyutlandırma, slot, kayma/komisyon, açılıştan
      koşulsuz dolum); gölge defteri PLAN düzeyindedir ve girişi "ilk uygun bar + stop-al dolumu"
      kuralıyla yapar (`golge_icra` beyanlı sapma 1 ve 3). Yani iki R'nin BÜYÜKLÜĞÜ birebir
      eşleşmez ve eşleşmesi de BEKLENMEZ — PK (3)'ün sorduğu şey İŞARETTİR.
  (c) EVREN. `edg032c` künyesi 251 sembol kaydeder; bugünkü `state/bars` önbelleği 248 sembol
      veriyor (aradaki fark emekli edilen semboller — `adapters.data.RETIRED_SYMBOLS`). Kesitsel
      `rs_map`in PAYDASI bu yüzden 049'unkiyle BİREBİR AYNI DEĞİLDİR; ölçülen sapma raporda
      `evren` bloğunda ADIYLA durur. Bu, doğan planın `rs_rating` kapısını teorik olarak
      çevirebilir — doğmayan plan sessizce düşmez, "ölçülemedi" olarak raporlanır.
  (d) BAR KAYNAĞI. Kart (Rol-1 hükmü 2) tarihsel yolda `state/barlar/` parquet arşivini ister;
      yerelde o arşiv YOKTUR (ölçüldü) ve `state/bars/*.csv` KABUL edilir (`bar_kaynak`
      alanı `"state/bars"`). Beyan raporun `bar_kaynagi` bloğundadır.

PIT (tarihsel yeniden yürütme — SIFIR TOLERANS). Her aşama D'den SONRAKİ barı D'de göremez ve bu
MEKANİKTİR, güvene dayalı değildir: doğum çağrısına evren `.loc[:D]` ile KIRPILMIŞ verilir, gölge
adımında `bars_of` o seansın kendi kırpığını döndürür, rejim `idx.loc[:d]` ile kurulur. `pitlaw`
kapı sözleşmesine BU BETİK GİRMEZ: hiçbir fonksiyonu kapı vokabülerinden bir karar sabiti
(GO/NO_GO/REVIEW) döndürmez ve yeni bir tarayıcı yüzeyi açmaz — ölçümdür, karar yüzeyi değildir
(`golge_icra` modül başlığındaki aynı beyan).

OKUR: 049 ölçüm artefaktı, `state/bars` CSV önbelleği (SALT-OKUNUR), GİT-İZLİ donmuş sözleşme
kopyası (`pk3_selef/params_donmus/`), `edg032c` taban künyesi. YAZAR: yalnız `--cikti-dizin`
altındaki iki artefakt
(`sonuc_<utc>.json` + `rapor_<utc>.md`) ve `--state-dizin` altındaki GEÇİCİ gölge defteri. Canlı
`state/` altına HİÇBİR ŞEY yazmaz — `--state-dizin` deponun `state/` ağacının altındaysa betik
başlamadan durur.

KOŞUM (operatörün koşacağı biçim) — `--params` VERİLMEZ: varsayılanı git-izli donmuş kopyadır,
o yüzden reçete taze bir klonda da olduğu gibi koşar.
  .venv/bin/python research/olcumler/edg088_golge_pilot/pk3_selef.py \\
      --kaynak research/olcumler/edg049_dormant_2026-08-23/islemler_tam_dormant_acik.json \\
      --bars-dizin state/bars \\
      --state-dizin <tmp> --cikti-dizin research/olcumler/edg088_golge_pilot/pk3_selef
ÇIKIŞ: 0 eşleşti · 2 ayrıştı ya da ölçülemedi (harness kör) · 1 hata.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import pathlib
import shutil
import sys

import pandas as pd
import yaml

KART = "EDG-2026-088"
PK = 3
KURULUM = "pullback"          # PK (3)'ün dilimi — kart ve Rol-1 hükmü ile DONUK
BEKLENEN_N = 6                # 049'un dormant pullback dilimi: TAM 6 satır (Rol-1 hükmü 3)
BEKLENEN_TOPLAM_R = -4.725    # aynı dilimin 049'daki toplam R'si (kıyas çapası)
BAR_KAYNAK = "state/bars"     # `golge_icra.BAR_KAYNAKLARI` kapalı kümesinden; parquet arşivi yerelde yok

#: SEANS TAVANI — gölge takibinin BEYANLI üst sınırı. `exit.time_stop_days` (donmuş sözleşmede 15)
#: her açık pozisyonu er geç kapatır; tavan o yasanın YEDEĞİDİR, yerine geçmez. Tavana çarpan plan
#: "kapanmadi" ile ÖLÇÜLEMEDİ sayılır ve sessizce düşmez.
SEANS_TAVANI = 120

#: DONMUŞ TABANIN KÜNYESİ — parametrelerin kimliği BURADAN doğrulanır, elle yazılmaz. `--params`
#: ile verilen dosyanın sha256'sı künyenin kendi kaydıyla (`config_sha256.sandbox_kaynagi_edg022`)
#: karşılaştırılır; tutmazsa betik BAŞLAMAZ. Hücre değerleri (slot / boyut / ısı zarfı) de
#: künyenin `hucre` bloğundan OKUNUR — ikinci bir kopya sessizce ayrışırdı (TEK-KAYNAK YASASI).
KUNYE_ADI = "edg032c_taban_2026-08-22/TABAN_KUNYESI.json"

#: Donmuş sözleşme dosyaları: `--params`in yanında DURURLAR (üçü birlikte taşınır).
#: `config.goal()`u okuyan üretim yolları (`broker.derisk_ramp`, `broker.entry_law`) sandbox
#: state'ten okusun diye state dizinine kopyalanırlar.
SOZLESME_DOSYALARI = ("goal.yaml", "strategy.yaml", "bounds.yaml")

#: DONMUŞ PARAMETRE KOPYASININ DİZİNİ — `--params` VARSAYILANI, betiğin KENDİ dizinine göreli.
#: Kopya GİT-İZLİdir ve bu kasıtlıdır: kartın dondurduğu girdi çalışma ağacına değil depoya
#: bağlanır (EDG-2026-059 — ağaca bağlı girdi, ağaç değişince kartı sessizce öldürür). Kopyanın
#: doğduğu EDG-022 ölçüm dizini `.gitignore`ludur (`research/olcumler/*/state/`) ve taze bir
#: klonda YOKTUR; oraya bağlı kalmak ölçümü bu makineye bağlar, yani tekrarlanamaz yapardı.
#: Kopyanın SOYU kaybolmaz: künyenin kaydı `config_sha256.sandbox_kaynagi_edg022` adını taşır.
#: Bayt-eşlik İKİ BAĞIMSIZ kayıtla ölçülür: yanındaki `SHA256SUMS` manifestosu (çivi v469 A5) ve
#: `edg032c` künyesinin `config_sha256` bloğu (`donmus_parametreler` KAPI 1) — biri kayarsa öteki
#: söyler.
PARAMS_DONMUS_ADI = "pk3_selef/params_donmus"


class Blok(Exception):
    """Ölçüm ön şartı tutmadı — koşum BAŞLAMAZ (çıkış 1). Sessiz devam etmek, ölçülmemiş bir
    tabanı ölçülmüş gibi raporlamak olurdu."""


# ==================================================================================================
# KÜNYE / PARAMETRE — donmuş taban kimliğiyle doğrulanır
# ==================================================================================================
def sha256(yol: pathlib.Path) -> str:
    """Dosyanın tam sha256'sı. Dosya yoksa `Blok` — "ölçemedim" ile "eşleşmedi" karışmasın."""
    if not yol.exists():
        raise Blok(f"dosya yok: {yol}")
    return hashlib.sha256(yol.read_bytes()).hexdigest()


def kunye_yolu(betik: pathlib.Path | None = None) -> pathlib.Path:
    """`edg032c` taban künyesinin yolu — bu betiğin KENDİ konumundan türetilir (kardeş ölçüm
    dizini). Mutlak yol gömmek, deponun başka bir checkout'unda sessizce yanlış dosyayı okurdu."""
    kok = (betik or pathlib.Path(__file__)).resolve().parent.parent
    return kok / KUNYE_ADI


def params_varsayilan(betik: pathlib.Path | None = None) -> pathlib.Path:
    """`--params` VARSAYILANI: git-izli donmuş `strategy.yaml` — bu betiğin KENDİ konumundan
    türetilir (`kunye_yolu` ile aynı desen, mutlak yol gömülmeden). Mutlak bir yol, deponun başka
    bir checkout'unda (worktree, taze klon, cloud) ya sessizce yanlış dosyayı okurdu ya da hiç
    okuyamazdı — ikisi de "ölçüldü" görünen bir koşum üretirdi."""
    kok = (betik or pathlib.Path(__file__)).resolve().parent
    return kok / PARAMS_DONMUS_ADI / "strategy.yaml"


def _depo_goreli(yol: pathlib.Path, kok: pathlib.Path) -> str | None:
    """Yolun depo köküne göreli hâli — sonuç künyesine MUTLAK yol yazmak artefaktı bu makineye
    bağlardı (bugünkü worktree yolu yarın başka bir checkout'ta anlamsızdır). Kök DIŞINDAysa
    `None` döner: uydurulmuş bir göreli yol yazmaktansa "ölçemedim" demek yeğdir."""
    try:
        return str(yol.resolve().relative_to(kok))
    except ValueError:
        return None


def donmus_parametreler(params_yolu: pathlib.Path, kunye_p: pathlib.Path | None = None) -> dict:
    """DONMUŞ `edg032c` parametre seti + kimlik kanıtı. Dönüş: params/by_regime/version/goal/künye.

    ÜÇ KAPI, ÜÇÜ DE MEKANİK:
      1. `--params` dosyasının sha256'sı künyenin `config_sha256.sandbox_kaynagi_edg022` kaydıyla
         AYNI olmalı (goal/bounds kardeşleri de aynı kayıttan doğrulanır).
      2. Künyenin `hucre` bloğu (slot 20 · position_size_r 0,5 · heat_hard_r 5,0) enjeksiyon
         değerlerinin TEK KAYNAĞIdır — bu dosyada sayı olarak yazılı DEĞİLDİR.
      3. `params_by_regime` dört rejimde de BOŞ olmalı (künyenin kendi `params_by_regime: false`
         beyanı); dolu bir override, `config.resolve_params` üzerinden ölçülen tabanı sessizce
         kaydırırdı.
    """
    kunye_p = kunye_p or kunye_yolu()
    if not kunye_p.exists():
        raise Blok(f"taban künyesi yok: {kunye_p} — donmuş parametre kimliği doğrulanamaz")
    kunye = json.loads(kunye_p.read_text())
    beklenen = (kunye.get("config_sha256") or {}).get("sandbox_kaynagi_edg022") or {}
    if not beklenen:
        raise Blok(f"künyede config_sha256.sandbox_kaynagi_edg022 yok: {kunye_p}")

    donmus_dizin = params_yolu.resolve().parent
    olculen = {}
    for ad in SOZLESME_DOSYALARI:
        olculen[ad] = sha256(donmus_dizin / ad)
        if ad in beklenen and olculen[ad] != beklenen[ad]:
            raise Blok(f"donmuş sözleşme sha uyuşmuyor ({ad}): "
                       f"ölçülen {olculen[ad][:16]} ≠ künye {beklenen[ad][:16]}")

    stg = yaml.safe_load(params_yolu.read_text())
    params = dict(stg["params"])
    by_regime = stg.get("params_by_regime") or None
    for rejim, ovr in (by_regime or {}).items():
        if ovr:
            raise Blok(f"params_by_regime[{rejim}] dolu ({sorted(ovr)}) — künye 'boş' beyan ediyor")
    hucre = kunye.get("hucre") or {}
    for alan in ("slot", "position_size_r", "heat_hard_r"):
        if alan not in hucre:
            raise Blok(f"künyenin hucre bloğunda '{alan}' yok — enjeksiyon değeri uydurulamaz")
    # ENJEKSİYON 2 (strateji params) — künyeden. Slot ve ısı zarfı goal'e, `goal_enjekte` ile.
    params["position_size_r"] = float(hucre["position_size_r"])
    return {"params": params, "by_regime": by_regime,
            "version": int(stg.get("version", 1)),
            "hucre": {k: hucre[k] for k in ("slot", "position_size_r", "heat_hard_r")},
            "sha256": olculen, "kunye_yolu": str(kunye_p),
            "kunye_taban": kunye.get("taban"), "kunye_dondurma": kunye.get("dondurma_tarihi_utc")}


def goal_enjekte(goal: dict, hucre: dict) -> dict:
    """`edg032c` merkez hücresinin goal tarafı: slot tavanı ve sert ısı zarfı (ENJEKSİYON 1 ve 3).

    Sözlük YERİNDE değiştirilir ve bu güvenlidir: `config.goal()` her çağrıda DERİN KOPYA döndürür,
    yani dosyaya ya da önbelleğe sızma yoktur (donmuş şasinin kendi beyanı)."""
    goal["limits"]["max_open_positions"] = int(hucre["slot"])
    goal["limits"]["heat_hard_r"] = float(hucre["heat_hard_r"])
    return goal


# ==================================================================================================
# 049 DİLİMİ — süzgeç DONUK
# ==================================================================================================
def suz_049(satirlar: list[dict], kurulum: str | None = None,
            beklenen_n: int | None = None) -> list[dict]:
    """049 işlem defterinden PK (3) dilimi: `setup == kurulum` olan satırlar, TAM `beklenen_n` tane.

    SAYI BİR KAPIDIR, bir gözlem değil: Rol-1 hükmü dilimi "TAM 6 satır" diye dondurdu. Süzgeç
    gevşerse (başka kurulum sızarsa) ya da artefakt değişirse koşum BAŞLAMAZ — sessizce başka bir
    popülasyon ölçmek, kartın PK'sını adı aynı kalan başka bir sınamaya çevirirdi.

    İKİ VARSAYILAN DA ÇAĞRI ANINDA MODÜL SABİTİNDEN ÇÖZÜLÜR (imza varsayılanı olarak DEĞİL):
    imzada dondurulsalardı, sabiti yamalayan bir çivi (sentetik 2-planlık mini-vaka) eski değeri
    okumaya devam eder ve testin ne ölçtüğü belirsizleşirdi. Üretim yolu sabiti hiç geçmez, yani
    kapı KOMUT SATIRINDAN gevşetilemez.
    """
    kurulum = KURULUM if kurulum is None else kurulum
    beklenen_n = BEKLENEN_N if beklenen_n is None else beklenen_n
    dilim = [s for s in satirlar if s.get("setup") == kurulum]
    if len(dilim) != beklenen_n:
        raise Blok(f"049 dilimi beklenen boyutta değil: setup=={kurulum!r} → {len(dilim)} satır "
                   f"(beklenen {beklenen_n})")
    return dilim


def dogum_gunu(plan_id: str) -> str:
    """`P-YYYY-MM-DD-TICKER` kimliğinden PLANIN DOĞDUĞU SEANS (D). Girişi D+1'dedir.

    Tarih `ts_open`dan (giriş günü) DEĞİL kimlikten okunur: giriş günü doluma bağlıdır, doğum günü
    ise planın tarama seansıdır ve PK (3) tam olarak o seansı yeniden koşar.
    """
    parca = str(plan_id or "").split("-")
    if len(parca) < 4 or parca[0] != "P":
        raise Blok(f"plan kimliği çözümlenemedi: {plan_id!r}")
    return "-".join(parca[1:4])


# ==================================================================================================
# 1. DOĞUM — `cf_backfill._plans_for_session` (üretim zinciri, kopya değil)
# ==================================================================================================
def dogur(d: pd.Timestamp, per: dict, idx: pd.DataFrame, taban: dict, goal: dict,
          ticker: str, kurulum: str = KURULUM) -> tuple[dict | None, dict]:
    """D seansını yeniden koş ve `ticker`ın `kurulum` planını DOĞUR. Dönüş: (plan | None, tanı).

    EVREN D'DE KIRPILIR (PIT, mekanik): `per`/`idx` buraya `.loc[:d]` ile verilir — çağrılan
    fonksiyon zaten kendi içinde dilimliyor, ama "zaten dilimliyor" bir GÜVENDİR; kırpmak bir
    KANITTIR. D'den sonraki bir bar bu çağrının görüş alanına yapısal olarak giremez.

    Plan doğmazsa `None` döner ve tanı o seansta NE OLDUĞUNU söyler (kaç plan doğdu, sembolün
    barı var mıydı, rejim neydi) — "doğmadı" adsız bırakılmaz.
    """
    from meridian import cf_backfill

    dstr = str(pd.Timestamp(d).date())
    perk = {t: df.loc[:d] for t, df in per.items() if d in df.index}
    plans, _armed, _dsig, _nm, rj = cf_backfill._plans_for_session(
        d, dstr, perk, idx.loc[:d], taban["params"], taban["by_regime"], goal, taban["version"])
    tani = {"seans": dstr, "plan_n": len(plans), "evren_n": len(perk),
            "sembol_bari_var": bool(ticker in perk),
            "rejim": (rj or {}).get("regime"),
            "exposure_budget_pct": (rj or {}).get("exposure_budget_pct"),
            "seansta_dogan_kurulumlar": sorted({p.get("setup") for p in plans})}
    esles = [p for p in plans if p.get("ticker") == ticker and p.get("setup") == kurulum]
    if not esles:
        return None, tani
    if len(esles) > 1:                       # tek seans + tek sembol + tek kurulum = tek plan
        raise Blok(f"{dstr} {ticker} {kurulum}: {len(esles)} plan doğdu — şema beklentisi bozuk")
    return esles[0], tani


# ==================================================================================================
# 2. GÖLGE — `golge_icra.adim`, seans seans
# ==================================================================================================
def rejim_of(idx: pd.DataFrame, d: pd.Timestamp, params: dict) -> tuple[dict, bool]:
    """O seansın rejim belgesi ve KÜRESEL `regime_ok` kapısı.

    İKİSİ DE ÜRETİMDEN İTHAL EDİLİR, KOPYALANMAZ: `regime.build_regime_json` belgeyi,
    `regime.regime_ok` kapıyı verir. BEYANIN TARİHÇESİ: 2026-09-13'e (TSK-184) kadar `regime_ok`
    motorda bir FONKSİYON değil bir İFADEydi ve üç üreticide (`backtest.replay`,
    `loop.daily_cycle`, `shadow_lifecycle._seed`) birebir yazılıydı; ithal edilecek tek kaynağı
    olmadığı için bu betik onu BEYANLA yeniden yazmıştı (4. kopya). TSK-184 yüklemi
    `regime.regime_ok` gövdesine taşıdı — beyan DÜŞTÜ, kopya KALKTI; ölçüm artık motorun
    kararını birebir aynı gövdeden okur (ayrışma çivisi
    `tests/test_regime_ok_tek_kaynak_v471.py` bu betiği de tarar).

    Kapı SIKIDIR: keşif sondasının gevşek dalı gölgeye uygulanmaz (`golge_icra` beyanlı sapma 5)
    — o dal `loop.daily_cycle`ın kendi hükmüdür, küresel yüklemin bir varyantı değil.
    """
    from meridian import regime as regime_mod

    dstr = str(pd.Timestamp(d).date())
    rj = regime_mod.build_regime_json(idx.loc[:d].reset_index(), params, dstr)
    return rj, regime_mod.regime_ok(rj)


def golgeden_gecir(plan: dict, d0: pd.Timestamp, per: dict, idx: pd.DataFrame, taban: dict,
                   state_dizin: pathlib.Path, donmus_dizin: pathlib.Path,
                   seans_tavani: int = SEANS_TAVANI) -> tuple[dict | None, dict]:
    """Planı D'den itibaren seans seans gölgeden geçir. Dönüş: (defter satırı | None, tanı).

    TAKVİM barlarındır: endeks (`SPY`) seansları D'den ileriye. D'nin KENDİSİ ilk adımdır — plan o
    seansın KAPANIŞINDA yakalanır (`golge_icra.adim` faz 3b) ve girişi D+1 açılışında denenir.
    Sonraki adımlara plan VERİLMEZ: aynı planı iki kez beslemek onu ikinci kez kuyruğa alırdı.

    HER PLAN KENDİ DEFTERİNDE koşar (`state_dizin` altında plana özel bir alt dizin). Ortak defter
    kullanılsaydı `adim`in idempotens kapısı (`dstr <= son_seans`) ikinci planın GEÇMİŞ seanslarını
    sessizce atlardı — 6 planın tarihleri ardışıktır ve bir sonrakine geçerken takvim geriye
    SARMAZ, ama tek bir defterde plan başına "atlanan seans" izi de birbirine karışırdı.

    `bars_of` O SEANSIN KIRPIĞINI döndürür (PIT, mekanik): motor zaten `df.loc[:d]` ile
    dilimliyor, kırpma o davranışı bir güvenceden bir yapıya çevirir.
    """
    from meridian import config, golge_icra

    _state_kur(state_dizin, donmus_dizin)
    takvim = [t for t in idx.index if t >= d0][:max(1, int(seans_tavani))]
    if not takvim:
        return None, {"neden": "takvim_bos", "seans_n": 0}

    onceki = len(golge_icra.kayit_al())
    adimlar = []
    for i, d in enumerate(takvim):
        dstr = str(pd.Timestamp(d).date())
        rj, regime_ok = rejim_of(idx, d, taban["params"])
        eff = config.resolve_params(taban["params"], taban["by_regime"], rj["regime"])
        ozet = golge_icra.adim(
            dstr, planlar=([plan] if i == 0 else []),
            bars_of=lambda t, _d=d: (per[t].loc[:_d] if t in per else None),
            regime_ok=regime_ok, params=eff, bar_kaynak=BAR_KAYNAK)
        adimlar.append({"seans": dstr, "rejim": rj["regime"], "regime_ok": regime_ok,
                        "yeni_satir": ozet.get("yeni_satir"), "acik": ozet.get("acik")})
        satirlar = golge_icra.kayit_al()
        if len(satirlar) > onceki:
            return satirlar[-1], {"seans_n": i + 1, "adimlar": adimlar,
                                  "atlanan_seanslar": (golge_icra.acik_kayit()
                                                       .get("atlanan_seanslar") or [])}
    return None, {"neden": f"kapanmadi:{len(takvim)}_seans", "seans_n": len(takvim),
                  "adimlar": adimlar}


def _state_kur(state_dizin: pathlib.Path, donmus_dizin: pathlib.Path) -> pathlib.Path:
    """Gölge defterinin GEÇİCİ state kökü: `config.STATE`/`HISTORY` oraya çevrilir ve donmuş
    sözleşme dosyaları kopyalanır.

    MEKANİZMA ÖLÇÜLDÜ, TAHMİN EDİLMEDİ: `tests/conftest.py::sandbox_state` fikstürü tam olarak
    bunu yapar (`config.STATE`/`HISTORY`/`BARS` atanır + `config.goal`/`bounds` lru önbellekleri
    boşaltılır); `store._state` ve `storage.db_path` her çağrıda `config.STATE`ten türer, yani
    defter de SQLite arka ucu da bu köke bağlanır. `config.BARS` BURADA DEĞİŞTİRİLMEZ — barlar
    koşum başında bir kez okunur ve salt-okunurdur.
    """
    from meridian import config

    state_dizin.mkdir(parents=True, exist_ok=True)
    (state_dizin / "history").mkdir(exist_ok=True)
    for ad in ("goal.yaml", "bounds.yaml"):
        hedef = state_dizin / ad
        if not hedef.exists():
            shutil.copyfile(donmus_dizin / ad, hedef)
    config.STATE = state_dizin
    config.HISTORY = state_dizin / "history"
    config.goal.cache_clear()
    config.bounds.cache_clear()
    return state_dizin


# ==================================================================================================
# 3. KIYAS — İŞARET (eşik yok)
# ==================================================================================================
def kayip_mi(r) -> bool | None:
    """R'nin İŞARETİ: kayıp mı? Ölçülemeyen R için `None` — sıfır ile "bilmiyorum" AYNI DEĞİLDİR."""
    return None if r is None else float(r) < 0.0


def kiyasla(ref: list[dict], golge: dict) -> dict:
    """049 satırları ile gölge satırlarını yan yana koy ve PK (3) hükmünü kur.

    HÜKÜM ÜÇ DEĞERLİDİR:
      `eslesti`    — 6/6 gölge satırı ÖLÇÜLDÜ ve HEPSİ kayıp (049'un işareti birebir).
      `ayristi`    — 6/6 ölçüldü ama işaret tutmadı → gölge motoru ile 049 karşı-olgusu AYRIŞIYOR
                     (kartın "harness kör" dediği hâl).
      `olculemedi` — en az bir plan doğmadı ya da R'si ölçülemedi → PK (3) KOŞULMADI; kör DEĞİL,
                     ölçülemedi (kart notu 2026-09-08 bu iki hâli ayırmayı şart koşar).
    Toplam R farkı BETİMLEYİCİDİR (icra semantiği sapması b) ve hiçbir hükme girmez.
    """
    satirlar = []
    for r in ref:
        pid = r["plan_id"]
        g = golge.get(pid) or {}
        gs = g.get("satir") or {}
        ref_r = r.get("r_multiple")
        gr = gs.get("R")
        satirlar.append({
            "plan_id_049": pid, "ticker": r.get("ticker"), "dogum_gunu": dogum_gunu(pid),
            "plan_id_golge": (g.get("plan") or {}).get("id"),
            "r_049": ref_r, "r_golge": gr,
            "kayip_049": kayip_mi(ref_r), "kayip_golge": kayip_mi(gr),
            "cikis_neden_049": r.get("exit_reason"), "cikis_neden_golge": gs.get("cikis_neden"),
            "giris_ts_049": r.get("ts_open"), "giris_ts_golge": gs.get("giris_ts"),
            "cikis_ts_049": r.get("ts_close"), "cikis_ts_golge": gs.get("cikis_ts"),
            "skor_049": r.get("score"), "skor_golge": (g.get("plan") or {}).get("score"),
            "isaret_esit": (kayip_mi(ref_r) == kayip_mi(gr)) if gr is not None else None,
            "kaynak_bar_hash": gs.get("kaynak_bar_hash"),
            "bar_kaynak": gs.get("bar_kaynak"),
            "olculemedi": g.get("olculemedi") or gs.get("olculemedi"),
        })
    olculen = [s for s in satirlar if s["r_golge"] is not None]
    tam = len(olculen) == len(ref)
    hepsi_kayip = bool(olculen) and all(s["kayip_golge"] for s in olculen)
    if not tam:
        durum, esles = "olculemedi", None
    elif hepsi_kayip:
        durum, esles = "eslesti", True
    else:
        durum, esles = "ayristi", False
    toplam_049 = round(sum(float(s["r_049"]) for s in satirlar if s["r_049"] is not None), 4)
    toplam_golge = round(sum(float(s["r_golge"]) for s in olculen), 6) if olculen else None
    return {"satirlar": satirlar, "durum": durum, "esles": esles,
            "n_ref": len(ref), "n_olculen": len(olculen),
            "n_kayip_049": sum(1 for s in satirlar if s["kayip_049"]),
            "n_kayip_golge": sum(1 for s in olculen if s["kayip_golge"]),
            "toplam_r_049": toplam_049, "toplam_r_golge": toplam_golge,
            "toplam_r_fark": (None if toplam_golge is None
                              else round(toplam_golge - toplam_049, 6))}


# ==================================================================================================
# KOŞUM
# ==================================================================================================
def kos(kaynak: pathlib.Path, bars_dizin: pathlib.Path, params_yolu: pathlib.Path,
        state_dizin: pathlib.Path, seans_tavani: int = SEANS_TAVANI,
        kunye_p: pathlib.Path | None = None) -> dict:
    """PK (3)'ün tamamı: doğum → gölge → kıyas. Dönüş: rapora ve JSON'a giden sonuç sözlüğü.

    `--cikti-dizin`e YAZMAZ (yazım `main`in işidir): bu fonksiyon testlerden de çağrılır ve bir
    ölçüm fonksiyonunun yan etkisi, testi dosya sistemine bağlamaktan başka bir şey yapmazdı.
    """
    from meridian import config

    kok = pathlib.Path(__file__).resolve().parents[3]
    if state_dizin.resolve() == (kok / "state") or (kok / "state") in state_dizin.resolve().parents:
        raise Blok(f"--state-dizin deponun state/ ağacının altında: {state_dizin} — canlı deftere "
                   f"yazım yasak, geçici bir dizin ver")

    taban = donmus_parametreler(params_yolu, kunye_p)
    donmus_dizin = params_yolu.resolve().parent
    ref = suz_049(json.loads(kaynak.read_text()))

    # STATE ÖNCE ÇEVRİLİR, BAR SONRA OKUNUR: `dataset.load_cached` bozuk bir satır gördüğünde
    # `obs.warn` yazar ve o yazım `config.STATE`e düşer — sıra ters olsaydı ilk uyarı CANLI
    # deftere giderdi (vaka sınıfı: ajanın pytest dışı koşumu canlı state'e yazıyor).
    _state_kur(state_dizin / "_yukleme", donmus_dizin)
    config.BARS = bars_dizin.resolve()
    from meridian import dataset
    from meridian.adapters import data as data_adapter

    bars, index = dataset.load_cached()
    if index is None or getattr(index, "empty", True):
        raise Blok(f"endeks barı ({data_adapter.INDEX_SYMBOL}) okunamadı: {bars_dizin}")
    per = {t: df.set_index("date").sort_index() for t, df in bars.items()}
    idx = index.set_index("date").sort_index()
    goal = goal_enjekte(config.goal(), taban["hucre"])

    golge: dict[str, dict] = {}
    for i, r in enumerate(ref):
        pid, ticker = r["plan_id"], r["ticker"]
        dstr = dogum_gunu(pid)
        d = pd.Timestamp(dstr)
        kayit: dict = {"plan_id_049": pid, "ticker": ticker, "dogum_gunu": dstr}
        if d not in idx.index:
            kayit["olculemedi"] = f"endeks_seansi_yok:{dstr}"
            golge[pid] = kayit
            continue
        plan, dogum_tani = dogur(d, per, idx, taban, goal, ticker)
        kayit["dogum_tani"] = dogum_tani
        if plan is None:
            kayit["olculemedi"] = "dogmadi"
            golge[pid] = kayit
            continue
        kayit["plan"] = plan
        satir, golge_tani = golgeden_gecir(plan, d, per, idx, taban,
                                           state_dizin / f"plan{i:02d}_{ticker}",
                                           donmus_dizin, seans_tavani)
        kayit["golge_tani"] = golge_tani
        if satir is None:
            kayit["olculemedi"] = golge_tani.get("neden") or "satir_yok"
        else:
            kayit["satir"] = satir
            if satir.get("R") is None:
                kayit["olculemedi"] = satir.get("olculemedi") or satir.get("giris_reddi") or "R_yok"
        golge[pid] = kayit

    sonuc = kiyasla(ref, golge)
    sonuc.update({
        "kart": KART, "pozitif_kontrol": PK, "kurulum": KURULUM,
        "olculdu_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "kaynak": {"yol": str(kaynak), "sha256": sha256(kaynak),
                   "beklenen_toplam_r_049": BEKLENEN_TOPLAM_R},
        "parametre_kaynagi": {"yol": str(params_yolu),
                              "yol_goreli": _depo_goreli(params_yolu, kok),
                              "sha256": taban["sha256"],
                              "kunye": taban["kunye_yolu"], "taban": taban["kunye_taban"],
                              "dondurma_utc": taban["kunye_dondurma"], "hucre": taban["hucre"],
                              "strategy_version": taban["version"],
                              "params_by_regime_bos": True},
        "bar_kaynagi": {"dizin": str(bars_dizin.resolve()), "etiket": BAR_KAYNAK,
                        "arsiv_parquet": None,
                        "beyan": ("kart Rol-1 hükmü 2 tarihsel yolda state/barlar parquet arşivini "
                                  "ister; yerelde o dizin YOK (ölçüldü) → state/bars CSV kabul")},
        "evren": {"n_sembol": len(per), "endeks": data_adapter.INDEX_SYMBOL,
                  "kunye_n_sembol": 251,
                  "beyan": ("edg032c künyesi 251 sembol kaydeder; bugünkü önbellek farkı emekli "
                            "semboller (adapters.data.RETIRED_SYMBOLS) — kesitsel rs_map paydası "
                            "049'unkiyle BİREBİR AYNI DEĞİLDİR")},
        "sapmalar": ["plan kimliği: uyuyan planda kurulum ekli (P-<tarih>-<sembol>-<kurulum>)",
                     "icra semantiği: 049 portföy replay'i (kayma/komisyon, açılıştan dolum) — "
                     "gölge plan düzeyinde, stop-al dolumu; büyüklük değil İŞARET kıyaslanır",
                     "evren: 248 ≠ 251 (emekli semboller) — rs_map paydası ayrışabilir"],
        "seans_tavani": int(seans_tavani),
        "golge": golge,
    })
    return sonuc


def rapor_metni(sonuc: dict) -> str:
    """Sonuç sözlüğünün insan okuru için Markdown karşılığı. TEK KAYNAK sözlüktür: bu fonksiyon
    hiçbir sayıyı yeniden hesaplamaz, yalnız biçimlendirir."""
    d = sonuc
    hk = {"eslesti": "EŞLEŞTİ", "ayristi": "AYRIŞTI", "olculemedi": "ÖLÇÜLEMEDİ"}[d["durum"]]
    sat = ["| plan (049) | sembol | D | 049 R | gölge R | 049 çıkış | gölge çıkış | işaret |",
           "|---|---|---|---|---|---|---|---|"]
    for s in d["satirlar"]:
        isaret = ("—" if s["isaret_esit"] is None
                  else ("eşit" if s["isaret_esit"] else "AYRI"))
        sat.append("| {} | {} | {} | {} | {} | {} | {} | {} |".format(
            s["plan_id_049"], s["ticker"], s["dogum_gunu"],
            s["r_049"], "ölçülemedi" if s["r_golge"] is None else s["r_golge"],
            s["cikis_neden_049"], s["cikis_neden_golge"] or (s["olculemedi"] or "—"), isaret))
    pk = d["parametre_kaynagi"]
    return "\n".join([
        f"# {d['kart']} — PK ({d['pozitif_kontrol']}) SELEF: 049'un {d['n_ref']} uyuyan "
        f"{d['kurulum']} planı gölge motorunda",
        "",
        f"**HÜKÜM: {hk}** (`esles={d['esles']}`) — ölçüm {d['olculdu_utc']}",
        "",
        f"- ölçülen gölge satırı: {d['n_olculen']}/{d['n_ref']} · "
        f"kayıp işareti: gölge {d['n_kayip_golge']}/{d['n_olculen']} · 049 {d['n_kayip_049']}/{d['n_ref']}",
        f"- toplam R — 049: {d['toplam_r_049']} · gölge: {d['toplam_r_golge']} · "
        f"fark: {d['toplam_r_fark']} (BETİMLEYİCİ; eşik yok, PK bir İŞARET kontrolüdür)",
        "",
        "## Satır satır",
        "",
        *sat,
        "",
        "## Kimlik",
        "",
        f"- **049 artefaktı**: `{d['kaynak']['yol']}` sha256 `{d['kaynak']['sha256'][:16]}…` "
        f"(dilim süzgeci `setup=={d['kurulum']!r}` → TAM {d['n_ref']} satır, toplam R "
        f"{d['kaynak']['beklenen_toplam_r_049']})",
        f"- **donmuş parametreler**: `{pk.get('yol_goreli') or pk['yol']}` (GİT-İZLİ kopya) "
        f"sha256 `{pk['sha256']['strategy.yaml'][:16]}…` "
        f"— `{pk['taban']}` ({pk['dondurma_utc']}), künye `{pk['kunye']}`",
        f"  - goal.yaml sha256 `{pk['sha256']['goal.yaml'][:16]}…` · "
        f"bounds.yaml sha256 `{pk['sha256']['bounds.yaml'][:16]}…`",
        f"  - hücre (künyeden): slot {pk['hucre']['slot']} · position_size_r "
        f"{pk['hucre']['position_size_r']} · heat_hard_r {pk['hucre']['heat_hard_r']} · "
        f"strategy_version {pk['strategy_version']} · params_by_regime BOŞ",
        f"- **bar kaynağı**: `{d['bar_kaynagi']['dizin']}` (`bar_kaynak=\"{d['bar_kaynagi']['etiket']}\"`) "
        f"— {d['bar_kaynagi']['beyan']}",
        f"- **evren**: {d['evren']['n_sembol']} sembol + endeks {d['evren']['endeks']} "
        f"(künye {d['evren']['kunye_n_sembol']}) — {d['evren']['beyan']}",
        f"- **seans tavanı**: {d['seans_tavani']} (exit.time_stop_days yasasının YEDEĞİ)",
        "",
        "## Beyanlı sapmalar",
        "",
        *[f"- {x}" for x in d["sapmalar"]],
        "",
        "## PIT çapası",
        "",
        "Her satırın `kaynak_bar_hash`i TÜKETİLEN OHLCV kesitlerinden türer "
        "(`golge_icra.bar_hash`); doğum ve gölge adımlarının ikisinde de evren `.loc[:D]` ile "
        "KIRPILARAK verilir — D+1'den sonraki bir bar D'nin görüş alanına yapısal olarak giremez.",
        "",
        *[f"- `{s['plan_id_049']}` → `{s['kaynak_bar_hash']}`" for s in d["satirlar"]],
        "",
    ])


def main(argv: list[str] | None = None) -> int:
    """KOMUT SATIRI sözleşmesi. Çıkış: 0 eşleşti · 2 ayrıştı/ölçülemedi · 1 hata."""
    ap = argparse.ArgumentParser(description=f"{KART} PK ({PK}) selef — 049'un uyuyan "
                                             f"{KURULUM} planları gölge motorunda")
    ap.add_argument("--kaynak", required=True, type=pathlib.Path,
                    help="049 tam işlem defteri (islemler_tam_dormant_acik.json)")
    ap.add_argument("--bars-dizin", required=True, type=pathlib.Path,
                    help="bar önbelleği (state/bars) — SALT-OKUNUR")
    ap.add_argument("--params", type=pathlib.Path, default=None,
                    help=f"donmuş edg032c parametre kaynağı — VARSAYILAN git-izli kopya "
                         f"({PARAMS_DONMUS_ADI}/strategy.yaml, betiğin dizinine göreli)")
    ap.add_argument("--state-dizin", required=True, type=pathlib.Path,
                    help="GEÇİCİ state kökü — gölge defteri buraya yazılır (canlı state YASAK)")
    ap.add_argument("--cikti-dizin", required=True, type=pathlib.Path,
                    help="sonuc_<utc>.json + rapor_<utc>.md buraya yazılır")
    ap.add_argument("--seans-tavani", type=int, default=SEANS_TAVANI,
                    help=f"gölge takibinin beyanlı üst sınırı (varsayılan {SEANS_TAVANI})")
    a = ap.parse_args(argv)

    try:
        sonuc = kos(a.kaynak, a.bars_dizin, a.params or params_varsayilan(),
                    a.state_dizin, a.seans_tavani)
    except Blok as e:
        print(f"BLOKLANDI: {e}", file=sys.stderr)
        return 1

    a.cikti_dizin.mkdir(parents=True, exist_ok=True)
    damga = sonuc["olculdu_utc"].replace(":", "").replace("-", "")
    (a.cikti_dizin / f"sonuc_{damga}.json").write_text(
        json.dumps(sonuc, ensure_ascii=False, indent=1, default=str))
    (a.cikti_dizin / f"rapor_{damga}.md").write_text(rapor_metni(sonuc))
    print(f"{KART} PK({PK}): {sonuc['durum']} (esles={sonuc['esles']}) · "
          f"ölçülen {sonuc['n_olculen']}/{sonuc['n_ref']} · "
          f"kayıp gölge {sonuc['n_kayip_golge']}/{sonuc['n_olculen']} · "
          f"toplam R 049 {sonuc['toplam_r_049']} / gölge {sonuc['toplam_r_golge']}")
    print(f"çıktı: {a.cikti_dizin}/sonuc_{damga}.json + rapor_{damga}.md")
    return 0 if sonuc["esles"] is True else 2


if __name__ == "__main__":
    raise SystemExit(main())
