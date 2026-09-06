# EDG-2026-067 — recall kıyası ölçüm çıktısı

Üretim: 2026-09-06T22:54:27Z · soru sayısı: 36 · kart: EDG-2026-067

> Bu belge yalnız SAYI taşır. Kart eşikleriyle karşılaştırma Rol-1'e aittir.

## Korpus / taban indeksi

- head_commit: `None`
- chunk sayısı: None
- taban indeks kurulum süresi: ölçülemedi
  - `head_commit` ölçülemedi — taban indeksi künyesi bu koşumda okunmadı (taban kolu koşmadı mı?)
  - `chunk_sayisi` ölçülemedi — taban indeksi künyesi bu koşumda okunmadı
  - `kurulum_suresi_s` ölçülemedi — taban indeksi bu koşumda kurulmadı; süre yalnız taban_indeks.py koşumunda ölçülür

## Kol özetleri

| kol | n | dosya-isabet@3 | bölüm-isabet@3 | tr bölüm@3 | en bölüm@3 | p50 ms | p95 ms | okunamayan |
|---|---|---|---|---|---|---|---|---|
| hindsight | 36 | 0.0% | 0.0% | 0.0% | 0.0% | 44238.2 | 45198.1 | 106 |

## Sınıf alt-kümeleri

| kol | arşiv | karar | reçete |
|---|---|---|---|
| hindsight | 0.0% | 0.0% | 0.0% |

## Soru başına

| id | dil | sınıf | kol | dosya-isabet | bölüm-isabet | dönen ilk-3 | ms |
|---|---|---|---|---|---|---|---|
| S-001 | tr | arsiv | hindsight | ✘ | ✘ | None, None, None | 45540.0 |
| S-002 | tr | recete | hindsight | ✘ | ✘ | None, None, None | 44467.2 |
| S-003 | en | arsiv | hindsight | ✘ | ✘ | None, None, None | 43895.1 |
| S-004 | tr | arsiv | hindsight | ✘ | ✘ | None, None, None | 42124.4 |
| S-005 | tr | karar | hindsight | ✘ | ✘ | None, None, None | 44391.1 |
| S-007 | en | karar | hindsight | ✘ | ✘ | None, None, None | 41721.9 |
| S-008 | tr | karar | hindsight | ✘ | ✘ | None, None, None | 37681.4 |
| S-009 | tr | karar | hindsight | ✘ | ✘ | None, None, None | 44743.5 |
| S-010 | tr | karar | hindsight | ✘ | ✘ | None, None, None | 44149.1 |
| S-012 | tr | arsiv | hindsight | ✘ | ✘ | None, None, None | 44486.1 |
| S-013 | tr | arsiv | hindsight | ✘ | ✘ | None, None, None | 44062.5 |
| S-014 | en | karar | hindsight | ✘ | ✘ | None, None, None | 44151.2 |
| S-016 | tr | recete | hindsight | ✘ | ✘ | None, None, None | 44211.8 |
| S-018 | tr | arsiv | hindsight | ✘ | ✘ | None, None, None | 44858.8 |
| S-020 | tr | recete | hindsight | ✘ | ✘ | None, None, None | 44411.7 |
| S-021 | tr | karar | hindsight | ✘ | ✘ | None, None, None | 44411.9 |
| S-022 | en | recete | hindsight | ✘ | ✘ | None, None, None | 44407.3 |
| S-023 | tr | karar | hindsight | ✘ | ✘ | None, None, None | 46650.8 |
| S-024 | tr | karar | hindsight | ✘ | ✘ | None, None, None | 44011.6 |
| S-025 | tr | arsiv | hindsight | ✘ | ✘ | None, None, None | 44247.9 |
| S-026 | tr | recete | hindsight | ✘ | ✘ | None, None, None | 44349.8 |
| S-027 | en | recete | hindsight | ✘ | ✘ | None, None, None | 45084.2 |
| S-028 | tr | arsiv | hindsight | ✘ | ✘ | None, None, None | 44168.9 |
| S-029 | tr | karar | hindsight | ✘ | ✘ | None, None, None | 44488.5 |
| S-031 | tr | karar | hindsight | ✘ | ✘ | None, None, None | 44484.3 |
| S-032 | tr | arsiv | hindsight | ✘ | ✘ | None, None, None | 44309.8 |
| S-034 | en | arsiv | hindsight | ✘ | ✘ | None, None, None | 44228.5 |
| S-035 | tr | arsiv | hindsight | ✘ | ✘ | None, None, None | 44287.7 |
| S-037 | tr | karar | hindsight | ✘ | ✘ | None, None, None | 43809.8 |
| S-039 | tr | recete | hindsight | ✘ | ✘ | None, None, None | 43864.6 |
| S-040 | tr | arsiv | hindsight | ✘ | ✘ | None, None, None | 42775.8 |
| S-042 | tr | arsiv | hindsight | ✘ | ✘ | None, None, None | 44043.8 |
| S-043 | tr | arsiv | hindsight | ✘ | ✘ | None, None, None | 44123.4 |
| S-044 | tr | arsiv | hindsight | ✘ | ✘ | None, None, None | 44201.2 |
| S-045 | tr | karar | hindsight | ✘ | ✘ | None, None, None | 44468.6 |
| S-047 | en | recete | hindsight | ✘ | ✘ | None, docs/SISTEM-DENETIMI-2026-08-02.md#3/10, docs/ARASTIRMA-SLIPAJ-AZALTMA-2026-08-13.md | 40605.7 |
