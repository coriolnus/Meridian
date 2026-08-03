# OPS NOTU — canlı `state/earnings.csv`'deki `TEST` fikstür satırının temizliği

**Hazırlayan:** ölçüm ajanı (WP-D turu, 2026-08-03) · **Uygulayan:** Rol-1 / operatör
**Hedef:** A1 (Oracle, `ubuntu@130.61.126.87`) · **Pencere:** bakım penceresi (canlı worker koşarken
state'e YAZMA — CLAUDE.md §5)
**Bu ajan canlıya DOKUNMADI.** Aşağıdaki komutlar YEREL snapshot üzerinde prova edildi, A1'de
koşulmadı.

---

## 1. Bulgu ve neden önemli

`state/earnings.csv` içinde bir test fikstürü satırı var:

```
TEST,2025-06-24
```

Zararsız görünüyor ama **iki gerçek zararı ölçüldü**:

1. **`coverage()["max_date"]`i geriye çekiyor.** 2026-07-25 tarihli canlı alarmın metni —
   `MECHANISM_STALE … earnings_calendar — gelecek tarih yok (son: 2025-06-24) — karartma guard'ı
   fiilen kapalı (0 çıktı)` — **tam olarak bu satırı** gösteriyor. Yani operatörün gördüğü teşhis
   dizesi gerçek bir sembolü değil bir fikstürü işaret ediyordu.
2. **`known_tickers` sayacını 1 şişiriyor.** Evren 251, takvimde 193 sembol görünüyor ama biri
   evrende yok → gerçek kapsanan 192. Kapsam raporları bu bir satır yüzünden tutarsız.
3. **Yeni takvim-sağlığı kapısını da ilgilendirir** (2026-08-03'te indi): `calendar_untrustworthy()`
   `ileri_gun`u `max_date`ten türetir. Takvim gerçekten bayatladığında `TEST` satırı hükmü
   DEĞİŞTİRMEZ (ikisi de geçmiş tarih → `takvim_atil`), ama teşhis metnini kirletmeye devam eder.

**Silme neden güvenli:** `TEST` evrende (`REPLAY_UNIVERSE`) yok, hiçbir plan/işlem defterinde
geçmiyor, tarihi 13 aylık geçmiş — yani ne karartmaya ne PEAD çapasına girdi sağlıyor. Satırın
kaldırılması **hiçbir sembolün kapsamını değiştirmez**.

**Kalıcı çözüm değil, hijyen:** satır bir daha yazılırsa kaynağı `refresh_from_fmp`/fikstür sızıntısı
olarak ayrıca aranmalı (bu notun kapsamı dışı — ayrı bilet).

---

## 2. Uygulama (A1, bakım penceresi)

### 2.1 ÖNCE: worker durdu mu ve yedek alındı mı

```bash
# canlı worker KOŞARKEN state'e yazma — önce durum
systemctl --user status meridian-worker --no-pager | head -5

# zaman damgalı yedek (geri dönüş yolu)
cp -a ~/AI-Trading/state/earnings.csv \
      ~/AI-Trading/backups/earnings.csv.$(date -u +%Y%m%dT%H%M%SZ).bak
```

### 2.2 KURU KOŞU: ne silinecek, tam olarak

```bash
grep -n '^TEST,' ~/AI-Trading/state/earnings.csv
```
**Beklenen çıktı:** TEK satır, `TEST,2025-06-24` biçiminde. Birden fazla satır ya da farklı bir
tarih çıkarsa **DUR** — varsayım bozulmuştur, hüküm Rol-1'e döner.

```bash
# satır sayısı önce
wc -l < ~/AI-Trading/state/earnings.csv        # beklenen: 194 (başlık + 193)
```

### 2.3 UYGULA (tek satırlık sed)

```bash
sed -i.bak '/^TEST,/d' ~/AI-Trading/state/earnings.csv
```

`-i.bak` yerinde düzenler ve `earnings.csv.bak` bırakır (2.1'deki zaman damgalı yedeğe ek ikinci
ağ). Desen satır BAŞINA çapalı (`^TEST,`) — gövdesinde "TEST" geçen bir sembolü (yok, ama kural
kuraldır) vurmaz.

### 2.4 DOĞRULA

```bash
# (a) satır gitti mi
grep -c '^TEST,' ~/AI-Trading/state/earnings.csv        # beklenen: 0  (grep rc=1, normal)

# (b) BAŞKA hiçbir şey değişmedi mi — tam olarak 1 satır eksilmeli
wc -l < ~/AI-Trading/state/earnings.csv                 # beklenen: 193
diff <(sed '/^TEST,/d' ~/AI-Trading/state/earnings.csv.bak) \
     ~/AI-Trading/state/earnings.csv && echo "FARK YOK - yalnız TEST satırı düştü"

# (c) kapı hâlâ sağlıklı mı (max_date artık GERÇEK bir sembolün tarihi)
cd ~/AI-Trading && ./.venv/bin/python -c "
from meridian import earnings
from meridian.adapters import data
c = earnings.coverage(list(data.REPLAY_UNIVERSE))
print({k: c[k] for k in ('known_tickers','max_date','ileri_gun','inert','future_dates','unknown')})
print('takvim_guvenilmez:', earnings.calendar_untrustworthy())
"
```

**Kabul ölçütü:**
- `known_tickers` **193 → 192**
- `max_date` **2025-06-24 DEĞİL** (gerçek bir gelecek tarih, ör. 2026-08-13)
- `ileri_gun ≥ 5` ve `inert = False`
- `calendar_untrustworthy()` → **None** (kapı normal çalışıyor; bir sebep dönerse takvim ayrıca
  bayat demektir ve o AYRI bir arızadır — tazeleme koşturulmalı)

### 2.5 GERİ ALMA

```bash
cp -a ~/AI-Trading/backups/earnings.csv.<damga>.bak ~/AI-Trading/state/earnings.csv
```
Sonra 2.4(c)'yi tekrar koştur.

---

## 3. Notlar

- **Worker yeniden başlatma GEREKMEZ:** `earnings._load()` dosyayı **mtime ile önbellekler**;
  `sed` mtime'ı değiştirdiği için bir sonraki okuma taze dosyayı alır.
- **Bu değişiklik versiyonlanmaz:** `state/` git-izli değildir (istisnalar yalnız `goal.yaml` +
  `bounds.yaml`).
- **Ölçüm kaynağı:** `research/olcumler/wpd_earnings_failopen/RAPOR.md` §3e ve `sonuc.json`.
