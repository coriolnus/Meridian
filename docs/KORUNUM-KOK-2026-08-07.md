# `conservation.unexplained = 14` — kök neden (Rol-1, 2026-08-07)

**Okuyucu:** bu bulguyu koda çevirecek ajan + operatör (§4'te operatör kararı var). (YASA 6)

**HÜKÜM TEK CÜMLE:** uyuyan-kurulum (`dormant_setup`) yolu **yazıp bırakıyor** — 31 plan
üretti, **0 işlem** çıktı, ve kapıda ölmeyen 14'ünün hiçbir terminal kaydı yok.
`unexplained = 31 − 17 NO_GO = 14`. Hesap tam kapanıyor.

---

## 0. Önce ÜÇ hipotezimin çürütülmesi

Bu bölüm silinmiyor: yanlış hipotezleri kaydetmek, onları koda çevirmemenin tek güvencesi.

**Hipotez 1 — "`universe_coverage` ile aynı kümülatif sayaç sınıfı".** ÇÜRÜTÜLDÜ.
`watchdog.py:423-524` okundu: `conservation_report()` bir sayaç değil, her koşuda sıfırdan
kurulan **nüfus sayımı**. Penceresi satır değil TARİH tabanlı ve en eski plana kadar açık;
`live_start` pencereden değil **defterin tamamından** okunuyor (C6, 2026-08-02); ölçüm
arızaları (`conservation_plan_date_unparsable`, `conservation_cf_fate_unavailable`) sessizce
yutulmuyor ve pencereyi **daraltmıyor, genişletiyor**. Rapor, ona yakıştırdığım kusurun
tam tersini yapacak biçimde yazılmış.

**Hipotez 2 — "iki kimlik şeması, iki yazıcı aynı anda canlı".** ÇÜRÜTÜLDÜ.
Tek yazıcı, tek koşul — `loop.py:1307-1308` ve `cf_backfill.py:101-102`:
```python
_pid = (f"P-{dstr}-{c['ticker']}-{c.get('setup','')}" if c.get("dormant_setup")
        else f"P-{dstr}-{c['ticker']}")
```
Ölçüm: uzun kimlikli plan **n=31**, bunların `dormant_setup` dolu olanı **31**. Yani
kimlik biçimi `dormant_setup`'ı kusursuz kodluyor. Şema dikişi YOK; uzun biçimin yalnız
2026-07/08'de görünmesi, özelliğin o tarihte doğmuş olmasından.

**Hipotez 3 — "K1'in BROKER_REJECT düzeltmesi 4'te 1 işliyor".** ÇÜRÜTÜLDÜ.
4 red KISA kimlikli (normal) planlara ait ve o planların **hiçbiri** açıklanamayanlar
listesinde değil — `broker_status: failed_broker_rejection` taşıyorlar ve açıklanıyorlar.
`watchdog.py:465-472` yorumu ölçümle çelişmiyor. **O bölüm bu belgeden kaldırıldı.**

---

## 1. Canlı ölçüm (A1, salt-okunur, 2026-08-07)

| alan | değer |
|---|---|
| `ok` | **False** |
| `plans` | 408 |
| `traded` | 95 |
| `no_fill` | 5 (meşru terminal) |
| `replay_era` | 242 (kayıt körlüğü, sızıntı değil) |
| `live_start` | 2026-07-10 |
| **`unexplained`** | **14** |

## 2. Kök neden — uyuyan yol yazıp bırakıyor

| | UYUYAN (`dormant_setup`) | NORMAL |
|---|---|---|
| plan sayısı | 31 | 377 |
| **işleme dönen** | **0 — %0,0** | 95 — %25,2 |
| olay taşıyan | 3 (%9,7) | 6 (%1,6) |
| `broker_status` alanı olan | 1 | 3 |
| hüküm dağılımı | NO_GO 17 · REVIEW 13 · **GO 1** | NO_GO 30 · REVIEW 245 · GO 102 |

**Hesap tam kapanıyor:** 31 uyuyan − 17 kapıda ölen (NO_GO, terminal ve kayıtlı)
= **14** = `unexplained`. Raporun gösterdiği 8 satırın **8'i de** uyuyan.

**En sert rakam:** uyuyan yolda **bir plan GO hükmü aldı ve yine de işleme dönmedi.**
Kapı onu geçirdi, arkasında onu tüketen bir şey yok.

Yani uyuyan-kurulum özelliği **önden bağlı, arkadan bağsız**: plan üretiliyor, kapıdan
hüküm alıyor, sonra hiçbir şey — silahlanma yok, emir yok, düşürüldü olayı yok, süre
dolumu olayı yok. Korunum bekçisi bunu **doğru yakalamış**; yanlış teşhis bendeydi.

### 2b. İkizler kopya DEĞİL

Üç ticker'da hem normal hem uyuyan plan var. Bunlar aynı planın iki kaydı değil,
**aynı isimde farklı kurulum hipotezi**:

| ticker | normal `setup` / stop | uyuyan `setup` / stop |
|---|---|---|
| MMM (07-21) | `breakout_vcp` / 160,97 | `episodic_pivot` / 167,78 |
| NSC (07-23) | `breakout_vcp` / 333,55 | `momentum_burst` / 341,13 |
| UNP (07-23) | `breakout_vcp` / 290,48 | `momentum_burst` / 301,09 |

Normal ikizler broker reddiyle terminal; uyuyan ikizler askıda. Kimlik ekinin varlık
sebebi tam bu çakışma — ve o iş görüyor.

## 3. Ne YAPILMAYACAK (operatör kararı, otonom uygulanmaz)

Uyuyan planları silahlanma/emir yoluna **bağlamak, sistemin NE ALIP SATTIĞINI değiştirir.**
31 planın 1'i GO hükmü almış; o yolu açmak canlı sermayeyi yeni bir sinyal ailesine maruz
bırakır. **Bu karar operatörde** — otonom yetki çerçevesi içinde değil.

Operatörün seçmesi gereken:
- **(a)** uyuyan planlar icraya bağlanacak → yeni sinyal ailesi canlıya girer, ön-kayıt
  kartı + kill-list + eşik gerekir (ölçüm disiplini, CLAUDE.md §3)
- **(b)** uyuyan planlar **tavsiye niteliğinde** kalacak → o zaman kapının GO vermesi
  yanıltıcı; ayrı bir hüküm ya da ayrı bir defter gerekir
- **(c)** özellik geri alınacak

## 4. Ne YAPILACAK (gözlemlenebilirlik — güvenli, otonom)

Hangi karar verilirse verilsin bunlar doğru:

1. **Uyuyan plana terminal kayıt.** Süresi dolan / tüketilmeyen uyuyan plan bir OLAY
   bırakmalı (`dormant_plan_lapsed` benzeri, `plan_id` ile). Şu an sessizce sönüyor
   ve bekçi bunu haklı olarak "sessiz kayıp" sayıyor.
2. **Bekçi uyuyan planı AYRI saysın.** `unexplained: 14` bugün "14 plan kayıtsız kayboldu"
   diye okunuyor; gerçek okuma "uyuyan yolun tüketilmeyen 14 planı". Aynı sayı, bambaşka
   hüküm — `universe_coverage`'ta düzelttiğimiz sınıfın kardeşi (v206): sayı doğru,
   **etiketi** yanlış. Rapor `dormant_unconsumed` kovasını ayrı döndürmeli.
3. **`0/31` panoda görünsün.** Bir özelliğin sıfır çıktı üretmesi, üretiyormuş gibi
   görünmesinden iyidir. Uyuyan yolun işleme-dönme oranı ölçülüp beyan edilmeli
   (payda-beyanlı: `0 / 31`).

## 5. Ölçüm izleri

- `watchdog.conservation_report()` — A1 `/opt/meridian/.venv`, salt-okunur
- `trade_plans.jsonl` (408) · `trades.jsonl` · `events.jsonl` (plan_id taşıyan 9 ayrık kimlik)
- Betikler: `scratchpad/{korunum_kok,ikiz,uyuyan,uyuyan_kader}.py` — stdin'den koşuldu,
  **canlıya dosya yazılmadı**, state'e dokunulmadı
- Erişim: `ssh -i ~/.ssh/oci-a1.key` (dagit.sh:16 kanonu). `~/Documents/OCI/...` yolu
  macOS gizlilik korumasına takılıyor — kullanma.
