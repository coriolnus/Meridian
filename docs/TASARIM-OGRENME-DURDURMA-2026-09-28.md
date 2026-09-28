# TASARIM — Öğrenme durdurmasında yansıma turu ve tek walk-forward (TSK-248)

Durum: **ONAYLI** — operatör 2026-09-28 14:5xZ (AskUserQuestion: kesilen yansıma turu "Hiç sayılmasın"). Yazan: Rol-1, 2026-09-28 14:5xZ.
Girdi: salt-okur tasarım ajanı (kod okuması) + TSK-246 uygulayıcı raporu §8.1. hafıza: A1 recall (43,6 s, 8 sonuç) — benzer karar kaydı yok.
Önceki adım: TSK-246 (ana dalda d3165ad6) ısınma / incumbent ön-hesabı / arama sondalarına işbirlikçi iptal ekledi — ölçülen durdurma ~5 sn.

## 1. Ölçülmüş olgular (kod okuması, 2026-09-28)

- `meridian/hermes.py::reflect_once` → `meridian/hermes.py::_reflect_once_govde`; imzada durdurma yüklemi YOK.
- Tur sırası: öneri (yazım yok) → `meridian/reflect.py::submit` (guard reddi → hipotez defterine kayıt) → guard geçerse incumbent (`_wf_cached`, önbellekte yoksa
  tek, senkron) + aday walk-forward (`backtest.walk_forward`, her zaman taze) — bu iki hesap boyunca kontrol noktası YOK → `_gate_eval(record_erosion=True)` →
  `validation.record_candidate` (K/aşınma defteri) → kapı/teyit/DSR/PBO dalları (her red → `memory.record`) → hepsi geçerse ship.
- Öneri yoksa/ship etmezse `meridian/reflect.py::search_and_submit` çağrılır — o da durdurma yüklemini İLETMEZ; oysa içerdeki
  `meridian/reflect.py::coordinate_descent_search` yüklemi taşır ve kontrol noktaları vardır → bu yolda hep `None` gelir, arama durdurmayla hiç kesilmez.
- `meridian/hermes_runtime.py::_run` tur DÖNENE kadar bloklanır; `last_reflect_at` yalnız tur döndükten sonra (`_record`) ilerler.
- Bugün "yarım yazım" yok: tur ya TAM biter ya da `TimeoutStopSec` dolunca SIGKILL. SIGKILL'in iki gerçek riski: (i) K/aşınma defterine satır düşmüş ama
  hipotez defterinde karşılığı yok (asimetrik defter); (ii) karar yazılmış ama `last_reflect_at` eski → yeniden başlayan süreç aynı kanıtla hemen yeni tur açar.
- `meridian/backtest.py::replay` takvim günü başına tek döngü; üretim penceresinde tek yürüyüş ~90 sn; `walk_forward` `replay`i bir kez çağırır.

## 2. Karar (operatör ONAYLI: A) + teknik seçim (Rol-1: Seçenek 1)

**A — Kesilen tur SAYILMAZ.** Durdurma yüklemi `reflect_once` → `submit` ve `search_and_submit` → `coordinate_descent_search` zincirine iletilir
(`hermes_runtime._stop` — `_warmup_sprint` deseni; `reflect` `hermes_runtime`'ı import etmez, yüklem enjekte edilir). Kontrol noktası `_gate_eval`den ÖNCE:
durdurma görülürse K/aşınma defterine, hipotez defterine hiçbir şey yazılmaz, ship olmaz, `last_reflect_at` İLERLEMEZ; süreç yeniden başlayınca aynı kanıtla
yeniden dener (sonsuz tekrar riski yok — tekrar yalnız yeniden başlatmada). Uydurma yasağıyla tutarlı: yarım ölçüm kayıt değildir.
**Seçenek 1 — `replay` bar döngüsüne kontrol noktası** (varsayılan `None` opsiyonel kwarg; gün başına bir yüklem çağrısı): durdurmada özel istisna yukarı
taşınır, sonuç ÖNBELLEĞE YAZILMAZ (`_wf_cached` bar-revizyon dalı deseni), tamamlanan günler değişmez (determinizm korunur). Maliyet ölçülür (mikro-benchmark).
**Elenen:** tek işi havuzda koşmak (Seçenek 2) — soğuk havuz maliyeti ölçülmedi ve 2026-08-03'te havuz işçileri panoyu boğmuştu; ölçüm sonrası ayrı adım olabilir.

## 3. Kabul ölçütleri

Durdurma bir yansıma turunun herhangi bir noktasında gelirse ≤ ~30 sn içinde iniş; K/aşınma ve hipotez defterinde yarım satır YOK; `last_reflect_at` değişmez;
bayrak kurulu değilken davranış birebir aynı (pozitif kontrol); `replay` sonucu bayraksız yolda bit-özdeş; import sözleşmesi korunur (v549 + AST çivisi).
