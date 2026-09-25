# EDG-2026-102 — replay stop kayması (tick) · ölçüm özeti

Araç: `research/olcumler/edg102_stop_kayma/olcum.py` sürüm 1 · sha256 `56da5e6cf1383e2a60f7fd726075daf84ba219016c40b0e99d5ac3fadf1c6548` · okuyucu pyarrow 25.0.1 · 2026-09-25T10:34:40+00:00

Bu belge HÜKÜM DEĞİLDİR: karar kuralının çıktısıdır; hükmü Rol-1 karta + K defterine işler.

## Girdi (içerik-adresli)
- trades (replay_seed ∧ stop): n=369 (SQL çapraz: 369) · sha256 `8245b83702fad84d63f4e97edb9d44da4c668753cd8239d4e1f86622775d4f02`
- plan satırı: 369 · sha256 `524a23de47c75d4bf19ea4c82bc38d2064c4ce7c7628db9c82e86a3773f5b93f` · extra_json bozuk: 0

## Öz-sınama (kill-1)
- tutarlı 278 / eşik 20 → GEÇTİ
- plan_ileri_esit=278 · plan_trailing_ustte=91 · plan_yakin_esit_degil=0 · plan_alti_ihlal=0 · islem_ici_tutarli=0 · islem_ici_trailing_ustte=0 · islem_ici_alti_ihlal=0 · kaynak_yok=0 · exit_okunamadi=0

## Sınıflar
- olculdu=335 · dokunus_yok=34 · sonraki_yok=0 · ters_red=0 · yon_disi=0 · tarih_okunamadi=0
- uygun=369 · ölçülen=335 · seans=227 · dokunus_yok oranı=%9.214 · tek seans payı=1.493%

## Sonuç
- DURUM: **KOSULLU_HUKUM**
- medyan kayma: **2.585 bps** · %95 CI [1.95, 3.074] (seans-kümeli, B=5000, seed=20260812)
- KARAR KURALI: **MODEL YETERLİ (stop bacağı)** (model varsayımı 5 bps)
- koşul: PK-2: --elle-ornek dilimleri Rol-1 tarafından parquet'ten elle doğrulanmadan hiçbir sayı yayılmaz (kart pozitif_kontrol 2)

## Pozitif kontrol
- PK-1 kimlik (çalışma anı): GEÇTİ
- PK-2 elle: ROL1_ELLE_DOGRULAMA_BEKLIYOR (5 örnek, aşağıda)
- PK-3 bar çaprazı: tutarsiz_satir_var · bar ayağı tutarsız 2 (ölçülemedi 0) · tik ayağı tutarsız 33 (ölçülemedi 1)

## Tanılar (hüküm değil)
- (a) kosul&0x20 dışı: 3.99 bps (n=326)
- (b) dokunuş anı spread: {"n": 246, "medyan": 227.399, "p25": 7.844, "p75": 785.884, "min": 0.592, "max": 2542.28, "kotasyon_yok_ya_da_tek_yanli_n": 89, "beyan": "(k_satis − k_alis) / eff_stop × 1e4, dokunuş kaydının işlem-anı kotasyonu"}
- (c) yıl: {"2022": {"n": 13, "medyan": 3.299, "p25": 1.648, "p75": 14.361, "min": -0.936, "max": 32.651}, "2023": {"n": 49, "medyan": 2.736, "p25": 1.271, "p75": 4.656, "min": -16.619, "max": 154.216}, "2024": {"n": 94, "medyan": 3.233, "p25": 0.643, "p75": 6.692, "min": -12.935, "max": 6604.715}, "2025": {"n": 92, "medyan": 2.187, "p25": 0.556, "p75": 7.142, "min": -32.886, "max": 133.361}, "2026": {"n": 87, "medyan": 1.872, "p25": 0.328, "p75": 6.168, "min": -58.929, "max": 116.379}}
- (c) fiyat kovası: {"[50,100)": {"n": 57, "medyan": 3.206, "p25": 1.407, "p75": 6.511, "min": -5.314, "max": 37.477}, "[250,inf)": {"n": 100, "medyan": 2.466, "p25": 0.655, "p75": 9.308, "min": -13.905, "max": 154.216}, "[25,50)": {"n": 33, "medyan": 1.738, "p25": -0.107, "p75": 5.503, "min": -16.619, "max": 59.911}, "[100,250)": {"n": 126, "medyan": 2.426, "p25": 0.644, "p75": 6.37, "min": -58.929, "max": 6604.715}, "[0,25)": {"n": 19, "medyan": 1.799, "p25": -0.132, "p75": 5.696, "min": -32.886, "max": 10.628}}
- (d) EDG-045 en yakın hücre: {"ek_bps": -2.415, "hucre": 5, "esit_uzak_hucreler": [5], "uzakliklar": {"5": 7.415, "10": 12.415, "20": 22.415}}
- (e) ölçek-uyumlu altküme: {"n_olculen": 334, "medyan_bps": 2.538, "olcek_uyumsuz_n": 1, "olcek_olculemedi_n": 0, "beyan": "KARTA EK TANI: bar split-düzeltmeli, tik ham; olcek_orani = bar close / tik seans son fiyatı, (0.9, 1.1) dışı → olcek_uyumsuz"}
- (f) saf ters (ızgara kilitsiz): {"n_olculen": 335, "medyan_bps": 2.585, "dokunus_degisen_n": 0, "beyan": "eff_stop her satırda exit/(1−s); ızgara kilidinin etkisini gösterir"}

## PK-2 elle doğrulama örnekleri
Her örnekte: dokunuş = seanstaki İLK fiyat ≤ eff_stop; dolum = hemen sonraki kayıt. Tarif satırı A1'de pilot-venv ile koşulur ve betik çıktısıyla karşılaştırılır.

### CLX 2023-05-08 · eff_stop 167.21830002087077 (plan_stop) · tick_fill 167.185 · kayma 1.991 bps · dokunuş öncesi seans min 167.22
```
  1559 14:53:39.925837545     167.2800 lot=1 kosul=32 
  1560 14:54:19.630486501     167.2600 lot=8 kosul=32 
  1561 14:54:42.380663968     167.2200 lot=2 kosul=32 
  1562 14:54:44.119556528     167.1900 lot=1 kosul=160 dokunus
  1563 14:54:45.342866146     167.1850 lot=4 kosul=32 dolum
  1564 14:54:57.301540683     167.1600 lot=100 kosul=0 
  1565 14:54:58.421555688     167.1300 lot=38 kosul=160 
  1566 14:55:07.324020964     167.1200 lot=200 kosul=0 
```
`python -c "import pyarrow.parquet as pq, pyarrow.compute as pc; t=pq.read_table('/opt/veri/tick/islem/2023-05-08.parquet', columns=['ts','sembol','fiyat','lot','kosul']); t=t.filter(pc.equal(t['sembol'], 'CLX')); t=t.filter(pc.and_(pc.greater_equal(t['ts'], 1683552600000000000), pc.less(t['ts'], 1683576000000000000))); t=t.sort_by('ts'); e=167.21830002087077*10000; i=next(j for j,v in enumerate(t['fiyat'].to_pylist()) if v<=e); print('dokunus', t.slice(i,1).to_pylist(), 'dolum', t.slice(i+1,1).to_pylist())"`

### ORCL 2023-06-29 · eff_stop 114.95153467091114 (plan_stop) · tick_fill 114.92 · kayma 2.743 bps · dokunuş öncesi seans min 114.98
```
    81 09:34:05.929491943     115.0000 lot=50 kosul=176 
    82 09:34:05.945573737     114.9800 lot=53 kosul=32 
    83 09:34:05.955312815     114.9850 lot=100 kosul=0 
    84 09:34:06.037949971     114.9100 lot=50 kosul=160 dokunus
    85 09:34:06.039778778     114.9200 lot=100 kosul=0 dolum
    86 09:34:06.044785011     114.9500 lot=100 kosul=128 
    87 09:34:06.044864826     114.9700 lot=200 kosul=128 
    88 09:34:06.206790333     114.9450 lot=100 kosul=0 
```
`python -c "import pyarrow.parquet as pq, pyarrow.compute as pc; t=pq.read_table('/opt/veri/tick/islem/2023-06-29.parquet', columns=['ts','sembol','fiyat','lot','kosul']); t=t.filter(pc.equal(t['sembol'], 'ORCL')); t=t.filter(pc.and_(pc.greater_equal(t['ts'], 1688045400000000000), pc.less(t['ts'], 1688068800000000000))); t=t.sort_by('ts'); e=114.95153467091114*10000; i=next(j for j,v in enumerate(t['fiyat'].to_pylist()) if v<=e); print('dokunus', t.slice(i,1).to_pylist(), 'dolum', t.slice(i+1,1).to_pylist())"`

### TSLA 2025-01-24 · eff_stop 405.90369 (plan_stop) · tick_fill 405.88 · kayma 0.584 bps · dokunuş öncesi seans min 405.91
```
  7966 15:41:34.655844236     405.9900 lot=3 kosul=160 
  7967 15:41:34.655858972     405.9900 lot=3 kosul=160 
  7968 15:41:34.693800541     405.9200 lot=25 kosul=32 
  7969 15:41:34.808175146     405.8800 lot=15 kosul=32 dokunus
  7970 15:41:34.808313757     405.8800 lot=85 kosul=160 dolum
  7971 15:41:37.856657453     406.1000 lot=29 kosul=160 
  7972 15:41:37.856995410     406.1000 lot=71 kosul=160 
  7973 15:41:39.651628677     406.1850 lot=1 kosul=32 
```
`python -c "import pyarrow.parquet as pq, pyarrow.compute as pc; t=pq.read_table('/opt/veri/tick/islem/2025-01-24.parquet', columns=['ts','sembol','fiyat','lot','kosul']); t=t.filter(pc.equal(t['sembol'], 'TSLA')); t=t.filter(pc.and_(pc.greater_equal(t['ts'], 1737729000000000000), pc.less(t['ts'], 1737752400000000000))); t=t.sort_by('ts'); e=405.90369*10000; i=next(j for j,v in enumerate(t['fiyat'].to_pylist()) if v<=e); print('dokunus', t.slice(i,1).to_pylist(), 'dolum', t.slice(i+1,1).to_pylist())"`

### UNH 2026-06-15 · eff_stop 400.61040520260127 (ters_formul) · tick_fill 400.16 · kayma 11.243 bps · dokunuş öncesi seans min 400.62
```
   155 09:34:37.168095348     400.9700 lot=2 kosul=32 
   156 09:34:57.289492982     400.6300 lot=2 kosul=32 
   157 09:35:04.706760113     400.6200 lot=15 kosul=32 
   158 09:35:15.863711100     400.1300 lot=2 kosul=32 dokunus
   159 09:35:30.633176053     400.1600 lot=50 kosul=0 dolum
   160 09:35:33.222699075     400.1100 lot=5 kosul=32 
   161 09:35:33.223317216     400.1100 lot=86 kosul=0 
   162 09:35:36.117137782     400.1100 lot=4 kosul=32 
```
`python -c "import pyarrow.parquet as pq, pyarrow.compute as pc; t=pq.read_table('/opt/veri/tick/islem/2026-06-15.parquet', columns=['ts','sembol','fiyat','lot','kosul']); t=t.filter(pc.equal(t['sembol'], 'UNH')); t=t.filter(pc.and_(pc.greater_equal(t['ts'], 1781530200000000000), pc.less(t['ts'], 1781553600000000000))); t=t.sort_by('ts'); e=400.61040520260127*10000; i=next(j for j,v in enumerate(t['fiyat'].to_pylist()) if v<=e); print('dokunus', t.slice(i,1).to_pylist(), 'dolum', t.slice(i+1,1).to_pylist())"`

### VMC 2026-07-08 · eff_stop 286.54317 (plan_stop) · tick_fill 286.26 · kayma 9.882 bps · dokunuş öncesi seans min 286.63
```
   375 10:41:30.047040493     287.1400 lot=1 kosul=32 
   376 10:41:38.160505628     286.9800 lot=1 kosul=160 
   377 10:41:43.028134161     286.6300 lot=2 kosul=32 
   378 10:42:24.372502490     286.4100 lot=1 kosul=32 dokunus
   379 10:43:10.348227044     286.2600 lot=25 kosul=160 dolum
   380 10:43:10.354271020     286.3750 lot=40 kosul=0 
   381 10:43:10.442442667     286.2200 lot=35 kosul=160 
   382 10:43:12.390667514     286.1100 lot=25 kosul=160 
```
`python -c "import pyarrow.parquet as pq, pyarrow.compute as pc; t=pq.read_table('/opt/veri/tick/islem/2026-07-08.parquet', columns=['ts','sembol','fiyat','lot','kosul']); t=t.filter(pc.equal(t['sembol'], 'VMC')); t=t.filter(pc.and_(pc.greater_equal(t['ts'], 1783517400000000000), pc.less(t['ts'], 1783540800000000000))); t=t.sort_by('ts'); e=286.54317*10000; i=next(j for j,v in enumerate(t['fiyat'].to_pylist()) if v<=e); print('dokunus', t.slice(i,1).to_pylist(), 'dolum', t.slice(i+1,1).to_pylist())"`
