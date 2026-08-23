# YEDİ KARAR — 2026-08-23 brainstorm turu (operatör + Rol-1; 7/7 sonuçlandı)

Kaynak: `docs/KARAR-MASASI-2026-08-23.md` §A. Her karar ayrı brainstorm'la alındı; bu belge
hükümlerin ve uygulama tasarımlarının tek kaydıdır. Uygulama sırası §Uygulama'da.

## K1 — Chop-bütçe (`B-CHOP-BUTCE`): KANITA BAĞLI AÇILIM
Kapanma "kazara-aritmetik" ilan edildi (politika değil); yeniden açılma kanıt-kapılı.
**Paket:** (a) hermes `@chop` hipotez üretimi DURAKLATILIR (bugünkü üretim yapısal israf;
notlandırma/teyit kapıları AYNEN) · (b) `EDG-2026-048` kartı: donmuş şaside chop-tabanı {45,60},
GO = Δ CI-alt>0; GO çıkarsa canlıya alma AYRI operatör kararı · (c) 28d @chop dilimi "kart
sonucuna bağlı" diline çekilir. — *Durum: SONUÇLANDI — NO-GO (Δ −18.266$, CI 0-içi; chop dilimi −26,3R + 99 iyi işlemi yerinden etti). Kapanma artık ölçülmüş politika; @chop duraklatması yürürlüğe girer, canlanma yalnız yeni kartla.*

## K2 — Pencere-kaydırma (`B-PENCERE-KAYDIR`): EVET, 042-HAKEMLİ SÜRESİZ
Canlı sabah tarama/emir tetiği 13:30→**13:45 UTC** (EDG-047 kanıtı: risk −%42,3, bedel medyan
+4,65 bps). **Raylar:** E2 icra defterine `pencere` damgası (`1330`/`1345`); EDG-042 K1 bundan
sonra iki alt-bant raporlar; **öneri tetiği (donuk):** sonrası-medyan CI'ı öncesininkinden
yüksek-AYRIK → haftalık rapor operatöre "geri-al önerisi" düşürür (geri alma otomatik değil).
Uygulama kart-önce (EXE-ailesi ön-kayıt) + pazartesi açılışından önce dağıtım.

## K3 — Limit bacağı (`B-E1-LIMIT`): YENİ DÜNYADA YENİDEN ÖLÇ
`EXE-2026-008`: EXE-006'nın grid'i BİREBİR (cap {0.005,0.01,0.02,0.03} × dolum {yalnız_açılış,
dinlenen_limit} = K8) — şasi edg032c, aynı maliyet bandı (045 stop-slip şerhi beyanlı taşınır),
kill listesi EXE-006'dan devir, H1/H2/H3 + asimetri beyanı aynen. Koşum 048 inince (ardışık).
Canlı bacak ölçüm sonuçlanana dek KAPALI. *Durum: SONUÇLANDI — üçüncü dal: iki dünyada da belirsiz (H1 kırık, H2+Ö3 tümü CI 0-içi); bacak kapalı, kalem 042 bandına park (043 askısıyla birlikte okunacak).*

## K4 — RUNBOOK kapsamı (`B-RUNBOOK-KAPSAM`): EVET
`ops/runbook_uret.py` BETIK_KUMESI'ne `dagit.sh` (kök) eklenir + sınır beyanı güncellenir;
belge yeniden üretilir; tipografi korpus ritüeli koşulur (v209 zinciri).

## K5 — 25a/c/d: BEKLET KALKTI, TAMAMI YAPILIR
25a KALDIR(14; `backtest_gate` + `kill_switch_file` öncelikli, mezar-taşı emsali) · 25c'nin
3 adayı için değerlendirme RAPORU (dirilt/damgala hükümleri operatöre döner — rapor karar
vermez) · 25d on ezilme zinciri damgalanır. Motor-sha değişimleri künye-tazelemeyle AYNI
turda koordine edilir (2026-08-23 gecesi dersi).

## K6 — Uyuyan kurulum: ÖNCE KARŞI-OLGU KARTI
`EDG-2026-049`: 31 planın (GO dahil) replay karşı-olgu getirisi donmuş şaside ölçülür.
GO → bağlama kararı kanıtla operatöre; NO-GO → yol "teşhis-katmanı" damgasıyla kapanır.

## K7 — ARSENAL: B1 KAPISI STANDART
Politika: her silahlanma/silahsızlanma/çıkış-değişikliği için ortak çıta — **kart-önce ölçüm +
confirm n≥30 ∧ CI-alt>0 (çift şart) + son imza operatörde.** `docs/POLITIKA-ARSENAL.md`
yazılır; B1 yeniden-silahlanma kapısı ilk örnek olarak atıflanır; 15d faktör adayları ve
29-ailesi çıkış işleri bu çıtaya bağlanır.

## Uygulama sırası (gece-kuyruğu)
1. K1 devam (048 künye-tazeleme + tam koşum → hüküm Rol-1)
2. K2 kartı + kod (pencere + damga + hakem raporu) — pazartesi-öncesi dağıtımın çekirdeği
3. K3 kartı yazılır; ölçüm 048 sonrası
4. K7 politika belgesi + K4 üretici-kapsam (hızlı, kod-hafif)
5. K5 paketi (25a/c/d — worktree, künye-koordineli) · K6 kartı + ölçüm
6. Konsolide suite → dağıtım (dagit) → canlı doğrulama → hükümler/tahta/günlük
Çıtalar/eşikler bu belgede DONDU; uygulama sırasında değişmez (değişiklik = yeni operatör turu).
