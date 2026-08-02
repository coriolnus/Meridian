# research/cards — Ön-Kayıt Defteri
Kural (iş emri 2026-07-31): kartsız ölçüm kodu yazılamaz/koşulamaz. Her parametre grid'i K'ya
sayılır; eşikler ölçümden SONRA değiştirilemez. Şema: iş emri §5. Durumlar:
registered → measuring → promoted | archived.

## Aktif kartlar
- EDG-2026-017-rvol-form-revizyonu.yaml — rvol>=2.5 bölgesi form-şartsız + sürekli-rvol artığı (registered 2026-08-02; K+=2)
- KYS-2026-001-kiyas-kirlenmesi.yaml — olay-penceresi kıyas-yanlılığı nicelleştirme; ALTYAPI kartı, retro-hüküm yok (registered 2026-08-02; K+=2; WP-M şasi aracına bağımlı)
- EXE-2026-001-entry-execution.yaml — E1 icra mutabakatı + limit-offset grid (registered)
- EDG-2026-001-52wh-proximity.yaml — 52-hafta-zirvesi, YALNIZ large-cap alt-örnek (registered)
- EDG-2026-002-volume-shock.yaml — hacim-şoku persentili, bant tablosu revizyonu (registered)

## Retroaktif kayıt kuyruğu (S1 ajanı biçimlendirecek; ölçümler ÖNCE koşmuştu, K-defterine sayılı)
- EAP large-cap [-10,-1] — status: **archived** (2026-07-31: +9,0bps CI[−13,3·+31,9], eşik 30bps;
  12,6-yıl güç-yeterli genişletmede +6,8bps; PK-1 kesin geçti; eşik esnetilmedi)
- Insider CMP (EDGAR 62 çeyrek, opportunistic_frac dahil) — status: **archived** (pozitif-kontrollü 0)
- Short-interest (FINRA 24 ay) — status: **archived** (12 hücre 0; likidite-vekili otopsisi)
- Çıkış paketi P1/P2/P3 (K=3) — status: measured→shadow-accrual (kapı ret; imza doğrulandı)
- Uzun-ufuk mega-cap trend kolu (K=2) — status: **measured→ALIVE/refine** (2026-07-31: N=10
  +13,14p/yıl vs EŞİT-AĞIRLIK-evren [yanlılık-nötr çıta], t=3,69 Bonferroni-geçer; maxDD çıtası
  GEÇİLMEDİ; mekanizma düzeltmesi: medyan tutuş 63g [~3 ay, "yıllar" değil], edge SEÇİMDEN
  [chandelier kapatınca CAGR ARTIYOR — durak maliyet], 2021-26 sessiz. Sonraki ölçüm BULGU-1/2
  veri-onarımı SONRASI; tasarım: seçim-odaklı, ~3 ay tutuş, durak minimal)
- PEAD klasik / rekonstitüsyon / sektör-takvim — status: archived (kaynaklı; kill-list)

## Kart-adayı yeni bulgular (Rol 1 tasarımı bekliyor)
- **KIYAS KİRLENMESİ (EAP ölçümünün yan bulgusu, 2026-07-31):** herhangi bir olay penceresinde
  evrenin ort. %64'ü / medyan %74'ü KENDİ kazanç-öncesi penceresinde — "evren medyanına göre fazla
  getiri" kullanan TÜM ölçümler (component_ic, cf R-tabloları) sistematik sıkıştırılmış. Doğru
  kıyas tasarımı (olay-penceresi-dışı alt-küme) kendi ön-kaydını hak ediyor; düzeltilmiş EAP
  okuması bile (+21,1bps) eşiğin altında — EAP hükmünü değiştirmez, ölçüm-altyapısını iyileştirir.
