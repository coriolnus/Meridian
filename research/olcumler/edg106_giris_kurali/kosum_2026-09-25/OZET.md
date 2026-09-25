# EDG-2026-106 — replay girişi ↔ koda sadık canlı giriş kuralı, bölünme yeniden ölçekli (tick) · ölçüm özeti

Araç: `research/olcumler/edg106_giris_kurali/olcum.py` sürüm 1 · kip stdin · sha256 `None` · beyan `7e381a68a50cc7a7286ef3c7b73cbd9c5b76d7e0ea454abf6dba9d3cd15dba62` · okuyucu pyarrow 25.0.1 · 2026-09-25T18:26:33+00:00
Parmak izi (iç sonuç): `91222887425fce71035d9d156422019c767e15b8b7a09e4559a668b95f01bd78` · gizlilik {'h1': False, 'h2': False}

Bu belge HÜKÜM DEĞİLDİR: iki karar kuralının çıktısıdır; hükmü Rol-1 karta + K defterine işler.

## Girdi (içerik-adresli)
- trades (kaynak=replay_seed): n=843 (SQL çapraz: 843; tüm trades 871) · sha256 `8c61ee885d2615dd4e1e97da42a1172c8c7803b954495bbfb19b9202a3e3aa3c`
- plan satırı: 843 · sha256 `e74d252225e733c8fda324d70c82b84fb0cbe5f3120df927e64fc64c671a0ece` · extra_json bozuk: 0 · strategy_version {'91': 843}

## Paydalar
- **aday**: tik aşamasına giren satır = replay_seed girdisi − tik-öncesi sınıflar (yon_disi, tarih_okunamadi, giris_okunamadi, plan_yok, plan_belirsiz, tetik_okunamadi, erken_kapanis); bu sınıflar ayrıca sayılır
- **erken_kapanis**: EDG-105 listesindeki XNYS 13:00 ET günlerinin girişleri birincilden DIŞLANIR ve sayılır; aday değildir, kill-2/kill-3/PK-3 paylarına girmez
- **olcek_eslem**: r = bar açılışı / ilk normal-seans tik; f = F'de |r/f − 1| ölçüsüyle en yakın öğe, ≤ %2 (dahil) ise; hepsi Fraction ile TAM (plan fiyatı ondalık gösteriminden). f ≠ 1 satırlarda plan tarafı ÷ f ile ham birime, L ham birimde canlı çift yuvarlamayla
- **kill1_oz_sinama**: SAYIM: |trades.entry − bar_açılış × (1 + 5 bps)| / entry × 1e4 ≤ 1 bps satır ≥ 20 (plan biriminde — ölçekten bağımsız)
- **kill2_akis_yok**: akis_yok / aday; > %10 → iki birincil YAYIMLANMAZ
- **kill3_olcek**: (olcek_eslenemez + olcek_parite_disi + olcek_olculemedi) / (aday − akis_yok); > %5 → YAYIMLANMAZ. Sınıf sırası: akis_yok → ref_yok / bar_acilis_yok (olculemedi) → kesir_disi (eslenemez) → kapanis_tetik (parite_disi) → monotonluk_ihlali (eslenemez, ticker düzeyinde sonradan)
- **kill4_monoton**: ticker başına f'ler tarih sırasıyla tek yönlü (hep ≤ ya da hep ≥) olmalı; değilse o ticker'ın TÜM f ≠ 1 satırları (sınıfı ne olursa olsun) olcek_eslenemez olur ve sonuç alanları silinir
- **kill5_tek_seans**: her birincil KENDİ paydasında en kalabalık seansın payı > %10 → CI şerhli (düşürülmez)
- **kill6_kosul**: yapısal: öykünücü zaman-tabanlı, kosul yalnız tanı (e)'de okunur — birincilde süzgeç YOK
- **kill7_tip**: yapısal: emir tipi YALNIZ plan günü bar kapanışından (`emir_tipi`) — kill_list.tip_kaynagi
- **kill8_pk**: PK-1 çalışma anı kimlik (ölçek kimliği dahil; düşerse exit 4) · PK-2 Rol-1 elle (koşul) · PK-3 tutarsız / (ölçeği çözülmüş, paritede, ayakları ölçülebilen aday); > %20 ya da payda 0 → GECERSIZ
- **h1**: DOLMAZ / (DOLMAZ + DOLAN) × 100 — akis_yok, ölçek ve erken kapanış dışlamaları paydada YOK
- **h2**: DOLAN satırlarda fark_bps = (canli_dolum − entry_tik) / entry_tik × 1e4 medyanı (aleyhte +, birimsiz)
- **n_esigi**: her birincil KENDİ paydasında ≥ 300 satır ∧ ≥ 100 seans (H1: DOLAN + DOLMAZ; H2: DOLAN)
- **gizlilik**: bir birincil yayımlanmıyorsa satır sonuç alanları yazılmaz; H1 yayımlanmıyorsa DOLAN/DOLMAZ sınıfları maskelenir ve özette yalnız birincil_aday_n kalır; stdout/OZET.md yalnız engel nedenini basar

## Öz-sınama (kill-1)
- tutarlı 838 / eşik 20 (≤ 1.0 bps) → GEÇTİ · ölçülen 843 · ölçülemedi 0

## Sınıflar
- yon_disi=0 · tarih_okunamadi=0 · giris_okunamadi=0 · plan_yok=0 · plan_belirsiz=0 · tetik_okunamadi=0 · erken_kapanis=6 · DOLAN=827 · DOLMAZ=5 · akis_yok=1 · olcek_eslenemez=0 · olcek_parite_disi=4 · olcek_olculemedi=0
- akis_yok alt nedenleri: {'seansta_sembol_kaydi_yok': 1} · DOLMAZ nedenleri: {'limit_ici_kayit_yok': 5}

## Ölçek (kill-3 · kill-4)
- dışlanan %0.478 (eşik %5) · eşlenemez 0 · parite dışı 4 · ölçülemedi 0 · alt nedenler {'kapanis_tetik': 4} · monotonluk ihlali []

## Kill-list
- oz_sinama_gecti=True · akis_yok_pct=0.119 · akis_yok_asimi=False · olcek_dislanan_pct=0.478 · olcek_asimi=False · olcek_eslenemez_n=0 · olcek_parite_disi_n=4 · olcek_olculemedi_n=0 · olcek_alt_nedenleri={'kapanis_tetik': 4} · olcek_tolerans_pct=2 · monotonluk_ihlali_tickerlar=[] · kosul_birincilde=False · tip_kaynagi=plan_gunu_kapanisi · erken_kapanis_n=6 · pk1_gecti=True · pk3_dustu=False · pk2=ROL1_ELLE_DOGRULAMA_BEKLIYOR

## Sonuç (iki hüküm AYRI)
- DURUM: **KOSULLU_HUKUM**
- H1 [DOLMAZ + DOLAN] n=832 seans=412 · durum KOSULLU_HUKUM · oran %0.601 · CI [0.122, 1.175] · KARAR DOLUM EŞDEĞER
- H2 [DOLAN] n=827 seans=411 · durum KOSULLU_HUKUM · medyan -5.011 bps · CI [-13.237, 3.783] · KARAR BELİRSİZ
- koşul: PK-2: --elle-ornek dilimleri Rol-1 tarafından parquet'ten elle doğrulanmadan hiçbir sayı yayılmaz (kart pozitif_kontrol 2)

## Pozitif kontrol
- PK-1 kimlik (çalışma anı, ölçek kimliği dahil): GEÇTİ
- PK-2 elle: ROL1_ELLE_DOGRULAMA_BEKLIYOR (0 örnek, kota {'GAP': 0, 'STOP_LIMIT': 0, 'DOLMAZ': 0, 'f_1_disi': 0}, karşılandı None)
- PK-3 bar çaprazı (ölçekli birim): tutarsız 16 / 832 (%1.923, eşik %20) → GEÇTİ · yüksek koşulu 16 · düşük koşulu (GAP) 0 · ölçülemedi 5

## Tanılar (hüküm değil)
- **a_dal_kirilimi**: {"GAP": {"n": 832, "dolmaz_n": 5, "dolan_n": 827, "dolmaz_pct": 0.601, "fark_medyan_bps": -5.011, "digeri_n": 0}}
- **b_0930_varyanti**: {"n": 832, "dolmaz_n": 0, "dolan_n": 832, "dolmaz_pct": 0.0, "fark_medyan_bps": -5.014, "digeri_n": 0, "dal_sayimi": {"GAP": 832}, "beyan": "aynı koda sadık öykünücü (tip plan günü kapanışından, ölçek aynı), t0 = 09:30 ET ilk kayıt — replay'in açılış varsayımının ilk IEX işleminden farkı; 9:45 penceresinin payını ayırır"}
- **c_gecikme_dk**: {"dolum": {"n": 827, "medyan": 0.013, "p25": 0.0, "p75": 0.122, "min": 0.0, "max": 140.208}, "aktivasyon": null, "beyan": "t0 kaydından dakika"}
- **d_yil**: {"2022": {"n": 37, "dolmaz_n": 1, "dolan_n": 36, "dolmaz_pct": 2.703, "fark_medyan_bps": -33.964, "digeri_n": 0}, "2023": {"n": 172, "dolmaz_n": 0, "dolan_n": 172, "dolmaz_pct": 0.0, "fark_medyan_bps": 5.082, "digeri_n": 0}, "2024": {"n": 245, "dolmaz_n": 3, "dolan_n": 242, "dolmaz_pct": 1.224, "fark_medyan_bps": -7.953, "digeri_n": 0}, "2025": {"n": 198, "dolmaz_n": 1, "dolan_n": 197, "dolmaz_pct": 0.505, "fark_medyan_bps": -1.496, "digeri_n": 0}, "2026": {"n": 180, "dolmaz_n": 0, "dolan_n": 180, "dolmaz_pct": 0.0, "fark_medyan_bps": -14.63, "digeri_n": 0}}
- **d_fiyat_kovasi**: {"[0,25)": {"n": 31, "dolmaz_n": 0, "dolan_n": 31, "dolmaz_pct": 0.0, "fark_medyan_bps": -5.046, "digeri_n": 0}, "[100,250)": {"n": 324, "dolmaz_n": 3, "dolan_n": 321, "dolmaz_pct": 0.926, "fark_medyan_bps": -0.541, "digeri_n": 0}, "[25,50)": {"n": 78, "dolmaz_n": 0, "dolan_n": 78, "dolmaz_pct": 0.0, "fark_medyan_bps": -19.171, "digeri_n": 0}, "[250,inf)": {"n": 220, "dolmaz_n": 1, "dolan_n": 219, "dolmaz_pct": 0.455, "fark_medyan_bps": -8.099, "digeri_n": 0}, "[50,100)": {"n": 179, "dolmaz_n": 1, "dolan_n": 178, "dolmaz_pct": 0.559, "fark_medyan_bps": 3.273, "digeri_n": 0}}
- **e_kosul_0x20_disi**: {"n": 832, "dolmaz_n": 5, "dolan_n": 827, "dolmaz_pct": 0.601, "fark_medyan_bps": -5.015, "digeri_n": 0, "beyan": "kosul & 0x20 kayıtları seanstan çıkarılıp öykünücü (t0 dahil) YENİDEN koşuldu; digeri_n = akis_yok"}
- **f_dolum_ani_spread_bps**: {"n": 598, "medyan": 220.781, "p25": 11.359, "p75": 809.69, "min": 0.86, "max": 29670.619, "kotasyon_yok_ya_da_tek_yanli_n": 229, "beyan": "(k_satis − k_alis) / canli_dolum × 1e4 (ham birimde, birimsiz), dolum kaydının işlem-anı kotasyonu"}
- **g_dolmaz_replay_sonucu**: {"n": 5, "exit_reason": {"regime_flip": 2, "target": 2, "time_stop": 1}, "r_multiple": {"n": 5, "medyan": 0.684, "p25": 0.172, "p75": 1.392, "min": -0.173, "max": 1.532}, "dolan_karsilastirma": {"exit_reason": {"regime_flip": 159, "stop": 362, "stop_gap": 51, "target": 91, "target_gap": 23, "time_stop": 141}, "r_multiple": {"n": 827, "medyan": -0.169, "p25": -1.005, "p75": 0.527, "min": -2.6, "max": 19.349}}, "beyan": "yalnız BETİMLEYİCİ — P&L etkisi ayrı kartın işidir"}
- **h_acilis_tetik_isareti**: {"acilis_alti": {"n": 388, "dolmaz_n": 0, "dolan_n": 388, "dolmaz_pct": 0.0, "fark_medyan_bps": -9.164, "digeri_n": 0, "fark_dagilimi": {"n": 388, "medyan": -9.164, "p25": -72.76, "p75": 60.732, "min": -555.481, "max": 484.764}}, "acilis_ustu": {"n": 428, "dolmaz_n": 5, "dolan_n": 423, "dolmaz_pct": 1.168, "fark_medyan_bps": -1.163, "digeri_n": 0, "fark_dagilimi": {"n": 423, "medyan": -1.163, "p25": -60.067, "p75": 62.502, "min": -459.923, "max": 381.775}}, "acilis_yakin": {"n": 16, "dolmaz_n": 0, "dolan_n": 16, "dolmaz_pct": 0.0, "fark_medyan_bps": -9.259, "digeri_n": 0, "fark_dagilimi": {"n": 16, "medyan": -9.259, "p25": -52.237, "p75": 12.834, "min": -286.179, "max": 110.89}}}
- **i_f1_disi_haric**: {"n": 776, "dolmaz_n": 5, "dolan_n": 771, "dolmaz_pct": 0.644, "fark_medyan_bps": -4.983, "digeri_n": 0, "dislanan_f1_disi_n": 56, "beyan": "f ≠ 1 (yeniden ölçeklenmiş) satırlar DIŞLANINCA iki birincil (nokta) — ölçeklemenin sonucu sürüklemediğinin gösterimi"}
- **j_olcek_tablosu**: {"f_dagilimi": {"1": 779, "1/10": 38, "1/15": 1, "1/2": 8, "1/25": 3, "1/5": 5, "1/6": 1, "3": 1}, "ticker_f": {"AVGO": {"1": 9, "1/10": 9}, "BKNG": {"1/25": 3}, "DD": {"3": 1}, "DECK": {"1/6": 1}, "KLAC": {"1": 2, "1/10": 8}, "LRCX": {"1": 8, "1/10": 7}, "MNST": {"1/2": 2}, "NFLX": {"1/10": 6}, "NOW": {"1/5": 5}, "NVDA": {"1": 6, "1/10": 8}, "ORLY": {"1/15": 1}, "PANW": {"1": 2, "1/2": 6}}, "eslenemez_ticker": {}, "parite_disi_ticker": {"GE": 3, "MNST": 1}}

## PK-2 elle doğrulama örnekleri
