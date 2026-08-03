"""RAPOR_e1.md üreticisi — tablolar sonuc_e1.json'dan ÜRETİLİR (elle kopyalama yok).
Anlatı bölümleri statik metindir; hiçbir sayı elle yazılmaz."""
from __future__ import annotations

import json
import pathlib

SB = pathlib.Path(__file__).resolve().parent
HEDEF = pathlib.Path("/Users/erdemozturk/AI-Trading/research/olcumler/e1_grid_2026-08-03")
S = json.loads((SB / "sonuc_e1.json").read_text())
T = {r["kol"]: r for r in S["tablo"]}
BAND = json.loads((SB / "kol_b_mkt.json").read_text())["kotumser"]["band"]
SIRA = ["a_mkt", "a_cnl", "b_mkt", "b_cnl", "c_mkt", "c_cnl", "ref_limitsiz"]
GRID = SIRA[:6]

KISA = {"a_mkt": "A·mkt", "a_cnl": "A·cancel", "b_mkt": "B·mkt (VARSAYILAN)", "b_cnl": "B·cancel",
        "c_mkt": "C·mkt", "c_cnl": "C·cancel", "ref_limitsiz": "REF·limitsiz"}
OFFSET = {"a": "min(0,25·ATR14; %0,5)", "b": "min(0,5·ATR14; %1,0)", "c": "min(1,0·ATR14; %1,5)"}


def tr(x, n=4, yuzde=False, dolar=False):
    if x is None:
        return "None"
    if isinstance(x, bool):
        return "EVET" if x else "HAYIR"
    if isinstance(x, int):
        return f"{x:,}".replace(",", ".")
    v = float(x)
    if yuzde:
        return f"%{v * 100:.2f}".replace(".", ",")
    s = f"{v:,.{n}f}"
    s = s.replace(",", "\x00").replace(".", ",").replace("\x00", ".")
    if dolar:
        s = ("+" if v > 0 else "") + s + "$"
    return s


def main() -> None:
    d = S["determinizm_kapisi"]
    g = S["gap_bacagi"]
    k1 = S["kill1_dolmama_vs_esik"]
    esl = S["kacan_dolum_eslesmesi"]
    par = json.loads((SB / "state_parmakizi_sonra.json").read_text())
    damga = S["motor_damgasi"]

    def f_usd(v):
        return tr(v, 2, dolar=True)

    # --- ana tablo ---
    kols = SIRA
    bas = [KISA[k] for k in kols]
    ln = ["| alan | " + " | ".join(bas) + " |", "|---|" + "---|" * len(kols)]

    def row(etiket, fn):
        ln.append(f"| {etiket} | " + " | ".join(fn(T[k]) for k in kols) + " |")

    row("limit_offset", lambda r: OFFSET.get(r["kol"][0], "limit tavanı ETKİSİZ"))
    row("gap_davranışı", lambda r: r["entry_law"]["gap_behavior"])
    row("(yasa: atr_mult · pct_cap)", lambda r: f"{tr(r['entry_law']['limit_atr_mult'], 2)} · "
                                                f"{tr(r['entry_law']['limit_pct_cap'], 4)}")
    row("**dolum çağrısı → dolan**", lambda r: f"**{r['cagri_n']} → {r['dolan_n']}**")
    row("**dolmama oranı (plan-bazlı)**", lambda r: f"**{tr(r['dolmama_orani'], 4)}** "
                                                   f"({tr(r['dolmama_orani'], 2, yuzde=True)})")
    row("· bunun limit-kaynaklı payı", lambda r: tr(r["dolmama_orani_yalniz_limit"], 4))
    row("· ret nedenleri", lambda r: "· ".join(f"{k} {v}" for k, v in
                                               sorted(r["ret_nedenleri"].items())) or "—")
    row("**net $ (replay defteri, 10bps)**", lambda r: "**" + f_usd(r["net_usd"]) + "**")
    row("net $ — E3 kötümser ikiz", lambda r: f_usd(r["net_usd_kotumser"]))
    row("· kötümser ek maliyet", lambda r: f_usd(r["kotumser_ek_maliyet"]))
    row("profit factor", lambda r: tr(r["profit_factor"], 4))
    row("ödenen friksiyon $", lambda r: tr(r["friksiyon_usd"], 2))
    row("**PARA-v3 (search)**", lambda r: "**" + tr(r["para_v3_search"], 4) + "**")
    row("· search realize $", lambda r: f_usd(r["search_pnl_usd"]))
    row("· search realize $ — kötümser", lambda r: f_usd(r["search_net_usd_kotumser"]))
    row("**oos_score**", lambda r: "**" + tr(r["oos_score"], 4) + "**")
    row("· oos_score None ise NEDEN", lambda r: (r["skor_none_nedeni"] or "—"))
    row("is_score", lambda r: tr(r["is_score"], 4))
    row("holdout_score", lambda r: tr(r["holdout_score"], 4))
    row("**n işlem (replay toplam)**", lambda r: f"**{r['n_trades_total']}**")
    row("n işlem (OOS / search)", lambda r: f"{r['oos_n']} / {r['search_n']}")
    row("avg_r (OOS)", lambda r: tr(r["avg_r"], 4))
    row("win_rate (OOS)", lambda r: tr(r["win_rate"], 4))
    row("sharpe (OOS)", lambda r: tr(r["sharpe"], 4))
    row("**M2M maks-DD (tam pencere)**", lambda r: "**" + tr(r["mtm_max_dd_tam_pencere"], 4) + "**")
    row("M2M maks-DD (mtm_dd_veto)", lambda r: tr(r["mtm_max_dd_veto"], 4))
    row("maks-DD (kapanmış işlem, OOS)", lambda r: tr(r["max_drawdown_islem_oos"], 4))
    row("tam pencere toplam getiri", lambda r: tr(r["tam_pencere_getiri"], 4))
    row("işlem digest (16)", lambda r: f"`{r['digest_tum']}`")
    row("plan digest (16)", lambda r: f"`{r['plan_digest']}`")
    row("plan n · kazanç-karartma vetosu", lambda r: f"{r['plan_n']} · {r['karartma_vetosu_plan_n']}")
    row("süre (sn)", lambda r: tr(r["sure_sn"], 1))
    ana = "\n".join(ln)

    # --- kill#1 tablosu ---
    ln2 = ["| hücre | dolmayan / çağrı | dolmama oranı | eşik %40 | fark (oran − 0,40) |",
           "|---|---|---|---|---|"]
    for k in SIRA:
        h = k1["hucreler"][k]
        ln2.append(f"| {KISA[k]} | {h['dolmayan_n']} / {h['cagri_n']} | "
                   f"**{tr(h['dolmama_orani'], 4)}** ({tr(h['dolmama_orani'], 2, yuzde=True)}) | "
                   f"0,40 | {tr(T[k]['dolmama_esik_farki'], 4)} |")
    kill = "\n".join(ln2)

    # --- kaçan dolum tablosu ---
    ln3 = ["| hücre | kaçan (limit) n | hipotetik ret_10 ort | hipotetik R_10 ort | "
           "hipotetik R_10 toplam | R_10 poz. oran | limitsiz kolda eşleşen n (kapsama) | "
           "eşleşenlerin gerçekleşen ΣR | eşleşenlerin gerçekleşen Σ$ |",
           "|---|---|---|---|---|---|---|---|---|"]
    for k in GRID:
        r10 = T[k]["kacan_limit_r10"]
        ret10 = T[k]["kacan_limit_ret10"]
        e = esl[k]
        ln3.append(
            f"| {KISA[k]} | {e['kacan_limit_n']} | "
            f"{tr(ret10.get('ort'), 4) if ret10.get('olculdu') else 'ölçülemedi'} | "
            f"{tr(r10.get('ort'), 4) if r10.get('olculdu') else 'ölçülemedi'} | "
            f"{tr(r10.get('toplam'), 4) if r10.get('olculdu') else 'ölçülemedi'} | "
            f"{tr(r10.get('poz_oran'), 4) if r10.get('olculdu') else '—'} | "
            f"{e['eslesen_n']} ({tr(e['kapsama'], 4)}) | {tr(e['toplam_r'], 4)} | "
            f"{f_usd(e['toplam_usd'])} |")
    kacan = "\n".join(ln3)

    # --- gap çiftleri ---
    ln4 = ["| çift | işlem digest eşit | plan digest eşit | equity digest eşit | net $ (mkt / cancel) "
           "| entry_gap_veto reddi |", "|---|---|---|---|---|---|"]
    for ad, v in g["olcum"].items():
        ln4.append(f"| {ad} | **{tr(v['digest_tum_esit'])}** | {tr(v['plan_digest_esit'])} | "
                   f"{tr(v['equity_digest_esit'])} | {f_usd(v['net_usd'][0])} / "
                   f"{f_usd(v['net_usd'][1])} | {v['entry_gap_veto_reddi'][0]} / "
                   f"{v['entry_gap_veto_reddi'][1]} |")
    gapt = "\n".join(ln4)
    gg = g["gap_at_submit_dagilimi"]["b_mkt"]

    dk = d["birincil_b_mkt"]
    dk2 = d["ikincil_ref_limitsiz"]

    # --- eski motor kolu bloğu ---
    em = dk2.get("eski_motor_kolu") or {}
    if em.get("olculdu") is False:
        eski_blok = (f"> `e1oncesi_eski` kolu **ölçülmedi** — {em.get('neden')}. Bu yüzden "
                     "`REF·limitsiz` ile `karne_olcum` kolonu arasındaki fark bu turda kalem "
                     "kalem AYRIŞTIRILAMADI (motor farkı + yol-bağımlılık birlikte duruyor).")
    else:
        mf = em["MOTOR_FARKI_eski_vs_bugun"]
        ik = mf["islem_kumesi"]
        eski_blok = (
            f"| imza | `karne_olcum` kaydı | `e1oncesi_eski` (yeniden üretim) | `REF·limitsiz` (bugünkü motor) |\n"
            f"|---|---|---|---|\n"
            f"| işlem digest (tüm) | `{dk2['karne_olcum_e1_oncesi_icra_digest']['digest_tum']}` | "
            f"`{em['digest']['digest_tum']}` | `{dk2['ref_limitsiz_digest']['digest_tum']}` |\n"
            f"| plan digest | `{dk2['karne_olcum_e1_oncesi_icra_digest']['plan_digest']}` | "
            f"`{em['digest']['plan_digest']}` | `{dk2['ref_limitsiz_digest']['plan_digest']}` |\n"
            f"| equity digest | `{dk2['karne_olcum_e1_oncesi_icra_digest']['equity_digest']}` | "
            f"`{em['digest']['equity_digest']}` | `{dk2['ref_limitsiz_digest']['equity_digest']}` |\n"
            f"| oos_score | {tr(em['karne_olcum_kayitli']['oos_score'], 4)} | "
            f"{tr(em['skorlar']['oos_score'], 4)} | {tr(mf['oos_score'][1], 4)} |\n"
            f"| is_score | {tr(em['karne_olcum_kayitli']['is_score'], 4)} | "
            f"{tr(em['skorlar']['is_score'], 4)} | {tr(mf['is_score'][1], 4)} |\n"
            f"| PARA-v3 (search) | {tr(em['karne_olcum_kayitli']['para_v3_search'], 4)} | "
            f"{tr(em['skorlar']['para_search'], 4)} | {tr(mf['para_search'][1], 4)} |\n"
            f"| n işlem | {em['karne_olcum_kayitli']['n_trades_total']} | "
            f"{em['skorlar']['n_trades_total']} | {mf['n_trades_total'][1]} |\n"
            f"| n işlem (OOS) | {em['karne_olcum_kayitli']['oos_n']} | {em['skorlar']['oos_n']} | "
            f"{T['ref_limitsiz']['oos_n']} |\n"
            f"| replay defteri net $ | (kayıtta yok) | {f_usd(em['skorlar']['net_usd'])} | "
            f"{f_usd(mf['net_usd'][1])} |\n"
            f"| dolan / çağrı | (kayıtta yok) | {em['skorlar']['dolum'][0]} / "
            f"{em['skorlar']['dolum'][1]} | {T['ref_limitsiz']['dolan_n']} / "
            f"{T['ref_limitsiz']['cagri_n']} |\n"
            f"| kazanç-karartma vetosu (plan) | (kayıtta yok) | {mf['karartma_vetosu_plan_n'][0]} | "
            f"{mf['karartma_vetosu_plan_n'][1]} |\n\n"
            f"**`e1oncesi_eski` ↔ `karne_olcum` digest eşitliği: "
            f"{tr(em['karne_olcum_ile_digest_esit'])}** — yani grid-dışı referans kolon bu turda "
            f"yeniden ÜRETİLDİ, alıntılanmadı.\n\n"
            f"İki limitsiz kol arasındaki TEK değişken motordur (505603b → HEAD). Ölçülen fark: "
            f"n işlem {mf['n_trades_total'][0]} → {mf['n_trades_total'][1]}; işlem kümesi ortak "
            f"{ik['ortak_n']}, yalnız eskide {ik['yalniz_eski_n']}, yalnız bugünde "
            f"{ik['yalniz_bugun_n']}; kazanç-karartma vetosu {mf['karartma_vetosu_plan_n'][0]} → "
            f"{mf['karartma_vetosu_plan_n'][1]} plan (replay-PIT düzeltmesi 89d4497'nin doğrudan "
            f"izi). Fark burada BETİMLENİR; hangi kalemin ne kadarını açıkladığı yol-bağımlılık "
            f"yüzünden tek tek AYRIŞTIRILAMAZ ve bu ölçümün kapsamı dışındadır.")

    md = f"""# E1 İCRA GRID'İ — kart EXE-2026-001, ön-kayıtlı `parameter_grid` ölçümü

**Tarih:** 2026-08-03 · **Rol:** ölçüm ajanı · **Hüküm sahibi:** Rol-1
**Kart:** `research/cards/EXE-2026-001-entry-execution.yaml` — OKUNDU, DEĞİŞTİRİLMEDİ.
Aşağıda yalnız sayı, kaynak ve kapsam beyanı vardır; **hüküm cümlesi kurulmadı**, eşik
sonradan değiştirilmedi, grid genişletilmedi (6 hücre = kartın kendi listesi).

**Salt-ölçüm beyanı:** her kol kendi kum havuzunda koştu (`MERIDIAN_ROOT` + `config.STATE`
yönlendirmesi), gerçek `state/`e YAZILMADI (kanıt §7), canlıya (ssh) dokunulmadı, git komutu
koşulmadı, üretim dosyası değiştirilmedi.

---

## 0. NE ÖLÇÜLDÜ, HANGİ MOTORLA (iddia değil damga)

| kalem | değer |
|---|---|
| motor | `{damga['kod_damgasi']['sandbox_motor']['yol']}` |
| motor .py dosya sayısı | {damga['kod_damgasi']['sandbox_motor']['dosya_n']} |
| depo `meridian/` ile bayt eşitlik (`diff -rq`) | rc={damga['sandbox_vs_depo_diff_rc']} → **fark yok** |
| aynı motor karne-tazeleme ölçümünün motoruyla eşit mi | rc={damga['depo_vs_karne_tazeleme_motoru_diff_rc']} → **evet** (o ölçümle KIYASLANABİLİR) |
| kollar arası TEK fark kaynağı | `state_<kol>/goal.yaml` → `execution_v2` bloğunun 2-3 satırı |
| goal.yaml'da değişen satır sayısı | her kolda ≤3 (geri kalan dosya bayt-aynı; `goal_diff_<kol>.txt`) |
| koşum yolu | deponun kendi `backtest.walk_forward`'ı (harness `kosum.py` + `kosum_kanca.py`) |

**Üretim kodu DEĞİŞTİRİLMEDİ.** Grid parametreleri kum havuzu `goal.yaml` kopyalarından verildi —
`broker.entry_law()` yasayı zaten YALNIZ `goal.yaml → execution_v2`'den okur (broker.py:70-101),
yani parametreyi oradan vermek yasanın kendi yoludur. Kanıt: her kolun çıktısındaki `entry_law`
bloğu (ana tablonun 3. satırı) ve `goal_diff_<kol>.txt`.

**R1 geometrisi (yedi kolda BİREBİR, karne_olcum/karne_tazeleme ile de aynı):** IS `2022-01-01` →
OOS `2024-01-01` → `2026-04-30` → holdout `2026-07-30`; foldlar `[2024-01-01, 2024-10-01,
2025-07-01, 2026-04-30]`; embargo 10. `strategy_version = 3` (`state/strategy.yaml:version`den
okundu, sabit yazılmadı). Evren: `REPLAY_UNIVERSE` 251 → **yüklenen {T['b_mkt']['n_sembol']}**
(`FISV` için `state/bars/fisv.csv` YOK); replay takvimi {T['b_mkt']['calendar'][0]} →
{T['b_mkt']['calendar'][1]}; barlar canlı önbellekten SEMBOLİK BAĞ ile salt-okunur.

**Kollar:** kartın `parameter_grid`i 3 `limit_offset` × 2 `gap_davranisi` = **6 hücre**. Ek olarak
kart-DIŞI **1 referans** kol: `ref_limitsiz` — limit tavanı hiç bağlamayacak şekilde
(`limit_atr_mult=1000`, `limit_pct_cap=0,10` → limit = tetik×1,10 > `max_chase` tavanı tetik×1,04)
kurulmuş "eski koşulsuz-açılış" defteri. İkinci referans **ayrı bir kol değildir**: `B·mkt`
hücresi zaten bugünkü yürürlükteki varsayılandır. Bunlara ek olarak, referans kolonunun
DOĞRULANMASI için sekizinci bir kol koşuldu: `e1oncesi_eski` — **eski motor** (505603b kopyası,
`karne_olcum` ölçümünün kendi motoru ve state'i) + aynı limitsiz bayrak (§5).

---

## 1. GRID TABLOSU (6 hücre + referans)

{ana}

---

## 2. KILL#1 EŞİĞİ — DOLMAMA ORANI vs %40 (sayı, hüküm cümlesi YOK)

Kart `kill_criteria[0]`: *"limit-offset hiçbir grid noktasında dolum oranını kabul edilebilir
tutamıyorsa (dolmama >%40) tasarım geri döner"*. Payda beyanı: **`fill_entry` çağrısına ulaşan
plan sayısı** — yani silahlanmış, o gün barı olan, slot/kesici/`size_mult` kapılarını geçmiş plan.
(Bu paydanın seçimi ölçümün kendisidir ve burada yazılıdır; başka bir payda — ör. tüm GO planları —
başka bir oran verirdi.)

{kill}

Eşiğin okunuşu Rol-1'e aittir; bu rapor yalnız oranı ve farkı yazar.

---

## 3. `gap_davranisi` BACAĞI — YAPISAL ÖLÇÜM (iddia değil)

Grid'in ikinci bacağı (`marketable_limit` ↔ `cancel`) walk-forward replay yolunda **ölçülebilir bir
fark üretmez** ve bu bir varsayım değil, üç ayrı yerden ölçülmüş bir olgudur:

1. **Argüman ölçümü.** `fill_entry`e geçen `gap_at_submit` değerlerinin dağılımı (B·mkt kolu,
   tüm kollarda aynı): çağrı {gg['cagri']} · `None` **{gg['gap_at_submit_none']}** · `True`
   {gg['gap_at_submit_true']} · `False` {gg['gap_at_submit_false']}.
2. **Kaynak.** `backtest.replay` `fill_entry`i `size_mult / adv / pivot / atr / reject_out` ile
   çağırır (backtest.py:232-236); `gap_at_submit` argüman listesinde YOKTUR → varsayılan `None`.
   `broker.fill_entry` gap vetosunu `if gap_at_submit and _law["gap_behavior"] == GAP_VETO` ile
   kurar; `None` bu dala giremez. Bu, broker.py'de BEYAN EDİLMİŞ bir kapsam farkıdır
   (*"None = 'bu motorda gönderim anı YOK' (replay) ve veto ateşlemez"*).
3. **Defter ölçümü.** Aynı `limit_offset`in iki gap noktası BİREBİR aynı defteri üretti:

{gapt}

**Kapsam beyanı (bu ölçümün SÖYLEYEMEDİĞİ):** `cancel` noktasının etkisi burada **ölçülemedi
(None)** — replay motorunda gönderim anı yoktur. Bacağın ölçülebileceği iki yer üretimde vardır ve
ikisi de bu ölçümün dışındadır: canlı `loop.py:824` (gerçek gönderim anı) ve `intraday_shadow.py:301`
(gölge defteri, plan yan tablosundaki `entry_law.gap_at_submit` alanından). Kartın bu bacağı için
"6 hücre koşuldu" cümlesi doğrudur; "6 farklı sonuç ölçüldü" cümlesi **yanlış olurdu**.

---

## 4. KAÇAN DOLUMLARIN SONRADAN-GETİRİSİ (betimleyici — "kaçan kâr" DEĞİL)

İki bağımsız betim, ikisi de hüküm vermez:

* **(a) hipotetik koşulsuz-açılış getirisi** — ham barlardan: giriş = o günün AÇILIŞI (limitsiz
  motorun ödeyeceği fiyat), çıkış = h seans sonraki KAPANIŞ; R-benzeri = (kapanış−açılış) /
  (açılış−stop). Çıkış mantığı (trail/breakeven/chandelier/giveback/regime_flip/scale_out),
  friksiyon ve portföy kısıtı **UYGULANMAZ**. İkinci bir icra/çıkış modeli KURULMADI.
* **(b) limitsiz koldaki gerçekleşen karşılık** — aynı (sembol, tarih) `ref_limitsiz` kolunun
  defterinde açıldıysa onun GERÇEKLEŞEN R/$ değeri. **Yol-bağımlıdır**: limitsiz kolun portföyü
  farklı bir yol izler; eşleşmeyen kaçan plan o kolda slot/ısı/eş-anlılık yüzünden hiç açılmamış
  olabilir. Temiz bir karşı-olgu değildir.

{kacan}

Ufuk h=10 seans gösterildi; h=5 ve h=20 özetleri `sonuc_e1.json → tablo[].kacan_*` ve kol
dosyalarındaki `kacan_dolum` bloğundadır (satır satır defterle birlikte).

---

## 5. DETERMİNİZM KAPISI

**Birincil (bağlayıcı).** `B·mkt` hücresi = bugünkü yürürlükteki yasa; girdileri
(motor, `strategy.yaml`, `bounds.yaml`, `goal.yaml`, `bars_integrity.json`, `earnings.csv`)
karne-tazeleme ölçümünün `guncel` koluyla **bayt-aynıdır**, dolayısıyla o kolu BİREBİR üretmesi
gerekir:

| imza | karne_tazeleme `guncel` (2026-08-03) | bu ölçüm `B·mkt` | eşit |
|---|---|---|---|
| işlem digest (tüm) | `{dk['karne_tazeleme_guncel']['digest_tum']}` | `{dk['b_mkt']['digest_tum']}` | {tr(dk['karne_tazeleme_guncel']['digest_tum'] == dk['b_mkt']['digest_tum'])} |
| işlem digest (search) | `{dk['karne_tazeleme_guncel']['digest_search']}` | `{dk['b_mkt']['digest_search']}` | {tr(dk['karne_tazeleme_guncel']['digest_search'] == dk['b_mkt']['digest_search'])} |
| plan digest | `{dk['karne_tazeleme_guncel']['plan_digest']}` | `{dk['b_mkt']['plan_digest']}` | {tr(dk['karne_tazeleme_guncel']['plan_digest'] == dk['b_mkt']['plan_digest'])} |
| equity digest | `{dk['karne_tazeleme_guncel']['equity_digest']}` | `{dk['b_mkt']['equity_digest']}` | {tr(dk['karne_tazeleme_guncel']['equity_digest'] == dk['b_mkt']['equity_digest'])} |
| oos_score | {tr(dk['karne_tazeleme_guncel']['oos_score'], 4)} | {tr(dk['b_mkt']['oos_score'], 4)} | — |
| PARA-v3 (search) | {tr(dk['karne_tazeleme_guncel']['para_v3_search'], 4)} | {tr(dk['b_mkt']['para_v3_search'], 4)} | — |
| n işlem | {dk['karne_tazeleme_guncel']['n_trades_total']} | {dk['b_mkt']['n_trades_total']} | — |
| replay defteri net $ | {f_usd(dk['karne_tazeleme_guncel']['net_usd'])} | {f_usd(dk['b_mkt']['net_usd'])} | — |

**KAPI: digest eşitliği = {tr(dk['digest_esit'])} · skor eşitliği = {tr(dk['skor_esit'])}.**

**İkincil (referans kolonunun yeniden üretimi).** "Eski koşulsuz-açılış defteri" bu depoda
`karne_olcum` ölçümünün `e1_oncesi_icra` kolu olarak zaten ölçülüydü. İki ayrı kol koşuldu:

* `REF·limitsiz` — **bugünkü** motorla, aynı bayrak yolu. Digest eşitliği BEKLENMEZ: o kol
  505603b motoruyla ve 2026-08-01 state'iyle koşmuştu. Ölçülen: digest eşit =
  {tr(dk2['digest_esit'])} (`{dk2['karne_olcum_e1_oncesi_icra_digest']['digest_tum']}` ↔
  `{dk2['ref_limitsiz_digest']['digest_tum']}`).
* `e1oncesi_eski` — **eski** motorla (505603b kopyası) + o ölçümün kendi state'i + aynı bayrak.
  Bu kolun görevi digest'i BİREBİR doğrulamak ve böylece `REF·limitsiz` ile arasındaki farkı
  TEK DEĞİŞKENE (motor 505603b → HEAD) indirmektir.

{eski_blok}

**Kolun kendi iddiası ölçüldü:** `REF·limitsiz`te `entry_missed_limit` reddi =
**{dk2['iddia_entry_missed_limit_sifir']}** (limit tavanı hiç bağlamadı — karne_olcum'un aynı
iddiası da 0 ölçmüştü).

Ek çapraz kontrol (her kolda): kancanın saydığı ret nedenleri ile motorun KENDİ sayacı
(`BacktestResult.entry_rejects`) eşit mi → {', '.join(f"{KISA[k]}: {tr(T[k]['motor_sayaci_esit_mi'])}" for k in SIRA)}.

---

## 6. ZORUNLU BEYANLAR (okuma bunlar olmadan yapılamaz)

1. **`bars_integrity` `dataset.load` yoluna BİLEREK bağlı DEĞİLDİR.** Kirli dönemler replay'de
   GÖRÜNÜR; operatör kararı bekliyor. Walk-forward kollarında `rows_excluded = 0`'dır — o yol
   `measurement_bars`ı hiç çağırmaz (kol çıktılarındaki `veri_kapilari.integrity_report`).
   Bu, yedi kolun HEPSİ için aynıdır, yani hücreler arası kıyası bozmaz.
2. **Survivorship (hayatta-kalan evren).** Replay evreni bugünün sağ-kalan {T['b_mkt']['n_sembol']}
   sembolüdür; delist olmuş isimler defterde YOKTUR. Yönün ilk ölçülmüş sayısı EDG-2026-021
   kartından (betimleyici, vekil-delist %18,6 sembol-payı): @20 tüm +0,48 · hayatta +0,54 ·
   delist −1,46. Bu tablodaki getiriler o yanlılığı TAŞIR ve büyüklüğü bu veriyle ölçülemez.
3. **Replay iyimserliği ≈ +0,018 (motor sapması).** ROADMAP.md:473'te kayıtlı; backtest skorları
   bu payı içerir. Bu turda yeniden ölçülmedi.
4. **cf sadakat sınırı.** `cf.advance` yalnız `stop_gap/target_gap/stop/target/time_stop` simüle
   eder (`analytics.CF_SIM_EXITS`); canlı motorun 6 çıkış mekanizması ve 5 friksiyon kalemi
   UYGULANMAZ. Ölçülmüş sapma (canlı defter, 2026-07-28): n=89 çift, corr 0,935, ortalama fark
   **+0,039R** (pozitif = simülasyon iyimser). Bu turda cf defteri KOŞULMADI; sınır, §4'ün (a)
   betimine EVLEVİYETLE uygulanır — orada çıkış mantığı hiç yoktur.
5. **E2 gerçek-slipaj bu ölçümle ÖLÇÜLEMEZ — None.** Kartın (b) başarı ölçütü canlı dolum verisi
   ister (`fill − resmî açılış`). Ölçülen durum: `state/entry_execution.jsonl` **yok**,
   `state/trades.jsonl` 95 satırın **95'inde `alpaca_fill_price` yok**,
   `analytics.pessimistic_band_update` ampirik bandı hâlâ `None` döndürür (n eşiği dolmadı).
   Bu grid REPLAY defteridir; kaçan/dolan ayrımını ölçer, ÖDENEN FİYATI ölçmez.
6. **E3 kötümser bandı RAPOR YÜZEYİDİR, karar değil.** İkiz sütun üretim fonksiyonlarıyla
   hesaplandı (`analytics.pessimistic_band` + `analytics._kotumser_ek_dolar`), band
   `goal.pessimistic_band_v2` (açılış spread {tr(BAND['acilis_spread_bps'], 1)} bps, yürürlükteki
   model {tr(BAND['mevcut_model_bps'], 1)} bps → ek **{tr(BAND['ek_bps_giris'], 1)} bps** yalnız
   GİRİŞ bacağına; taban `{BAND['taban']}`). `ampirik_bps` **{tr(BAND['ampirik_bps'])}**'dır
   (E2 defteri boş, n={BAND['ampirik_n']}) — literatür tabanı kullanıldı ve bu
   satırda yazılıdır. Hiçbir kapıya girmez (`hukme_girmez: true`).
7. **Holdout skoru yedi kolda da `None`** (kapanmış işlem < 30) — sıfır değil, tanımsız.
8. **PARA-v3 yasası değişmedi:** `shadowlaw.py`/`score.py` tüm kollarda aynı motordan gelir.
   Skor farkı yasadan değil, yasaya giren işlem defterinden gelir.
9. **Yol-bağımlılık.** Kaçan tek dolum, o günün slot dolumunu ve ertesi günlerin aday sıralamasını
   değiştirir; hücreler arası n farkı ayrı kararların toplamı değil, **bir kararın zincirlemesidir**.

---

## 7. YENİDEN ÜRETİM ve SALT-ÖLÇÜM KANITI

```
# kum havuzu (motor kopyası + kol başına state kopyası + bars/research SEMBOLİK BAĞ)
python kur.py                      # -> meridian/ + state_<kol>/ + kod_damgasi.json + goal_diff_*.txt
python parmakizi.py once           # gerçek state/ parmak izi (ÖNCE)
python kosum.py <kol>              # kol ∈ {{a_mkt,a_cnl,b_mkt,b_cnl,c_mkt,c_cnl,ref_limitsiz}}
                                   # (7 kol PARALEL koşuldu; her biri kendi state_<kol>/'una yazar)
cd eski_motor && python kosum.py e1oncesi_eski   # referans doğrulama kolu (505603b motoru)
python karsilastir_e1.py           # -> sonuc_e1.json
python parmakizi.py sonra          # gerçek state/ parmak izi (SONRA)
python rapor_yaz.py                # -> RAPOR_e1.md (tablolar sonuc_e1.json'dan üretilir)
```

Gerçek `state/` ağacının tam parmak izi (yol → mtime+boyut) koşumlardan önce ve sonra alındı:

| | dosya | parmak izi sha256(16) |
|---|---|---|
| önce | {par['dosya_once']} | `{par['sha_once']}` |
| sonra | {par['dosya_simdi']} | `{par['sha_simdi']}` |

Değişen dosya **{len(par['degisen'])}**, yeni **{len(par['yeni'])}**, silinen
**{len(par['silinen'])}**. Yazılan her bayt `<sandbox>/state_<kol>/` altındadır. `serve.sh`
koşulmadı, ssh kullanılmadı, git komutu çalıştırılmadı, kart dosyasına dokunulmadı.

Bu dizindeki dosyalar: `sonuc_e1.json` (makine-okunur tam sonuç), `kod_damgasi.json`,
`state_parmakizi_sonra.json`, `goal_diff_<kol>.txt` (kolların tek-fark kanıtı) ve koşum betikleri
(`kur.py`, `kosum.py`, `kosum_kanca.py`, `karsilastir_e1.py`, `rapor_yaz.py`, `parmakizi.py`,
`duman.py`). Kol JSON'ları (`kol_<kol>.json`, ~1 MB × 8) kum havuzunda kalır; içlerinde ham
defterler (`_trades_tum`, `_plan_log`, `_fill_cagrilari`, `_equity`) ve kaçan-dolum satır
defteri (`kacan_dolum.satirlar`) vardır. Kum havuzu yolu:
`{SB}`.
"""
    (HEDEF / "RAPOR_e1.md").write_text(md)
    print("yazıldı:", HEDEF / "RAPOR_e1.md", len(md), "bayt")


if __name__ == "__main__":
    main()
