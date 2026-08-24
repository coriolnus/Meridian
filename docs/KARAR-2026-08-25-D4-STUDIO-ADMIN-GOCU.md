# D4 — Pano tamamen studio-admin'e geçiyor

**Tarih:** 2026-08-25 · **Karar sahibi:** operatör · **Uygulayan:** Rol-1
**Öncül:** [D3 — shadcn/React pilotu](KARAR-2026-08-24-D3-SHADCN-UI-PILOT.md)

---

## 0. Karar

Operatör, uygulamanın arayüzünün **tamamen**
`next-shadcn-admin-dashboard.vercel.app` (paket adı: *studio-admin* v2.2.0)
şablonuna geçmesine karar verdi. İki ek talimat kararın kapsamını belirledi:

1. *"UI ile alakalı bütün kurallarını yok sayabilirsin"* — Meridian'ın kendi
   tasarım dili sözleşmesi (rol jeton katmanı, rezerve hue bantları, çip/yarıçap
   grameri) **emekli**; yerini şablonun jeton sistemi alıyor.
2. Bilgi mimarisi de şablonunki: tutulacak on beş yüzey adıyla sayıldı
   (7 pano + 8 sayfa). Meridian'ın yirmi iki bölümü bu on beşe eşlendi.

Bu bir üslup tercihi değil bir **ürün kararı**: D3'ün ölçtüğü "yarım göç"
hastalığının kalıcı çaresi, iki tasarım dilini uzlaştırmak değil, tek bir dili
bütünüyle benimsemek.

---

## 1. Substrat: Next DEĞİL, Vite — ve bu ölçümle verildi

Şablon Next 16 App Router. **Olduğu gibi alınamaz** ve gerekçe iki ölçümdür,
bir tercih değil.

### Ölçüm 1 — satır içi `<script>` × 3, CSP `script-src 'self'` altında ölü

Şablonun kendisi derlendi (`site/`, `npm run build`, exit 0) ve ön-render edilmiş
HTML incelendi:

```
.next/server/app/unauthorized.html
  toplam <script>: 17   ·   satır içi (src yok): 3
    1) (function(){ try { var root = document.documentElement; … })()   ← tema önyükleyicisi
    2) (self.__next_f=self.__next_f||[]).push([0])
    3) self.__next_f.push([1,"1:\"$Sreact.fragment\"\n9:I[168027,…              ← RSC yükü
```

Canlı politika (`meridian/api.py::CSP_POLITIKASI`):

```
default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; …
```

Üç blok da bloklanır. Sonuç **hata değil, yanlış sonuç**: sayfa çizilir, hiçbir
düğme iş görmez. Bu depoda birebir aynı arıza 2026-08-01'de yaşandı
(`landing.html` + `workflow.html` satır içi blokları) ve Caddyfile'ın kendi
şerhinde kayıtlı: *"o CSP dağıtılsaydı pano çizilir, hiçbir düğme iş görmezdi."*
Çaresi `'unsafe-inline'` eklemek olurdu — Caddyfile aynı yerde bunu adıyla
yasaklıyor ve HALT/Flatten düğmeleri taşıyan bir yüzeyde gevşetmek, güvenlik
duruşunu geri almak demek.

### Ölçüm 2 — statik dışa aktarım zaten mümkün değil

Derleme raporunda pano rotalarının **tamamı `ƒ` (Dynamic, server-rendered)**;
yalnız `/icon.svg` ve `/unauthorized` statik. Sebep: `dashboard/layout.tsx`
`await cookies()` okuyor. `output: "export"` bu hâlde doğrudan düşer — önce tüm
tercih sistemi çerezden koparılmalı.

### Karşı ölçüm — Next'e bağlılık ne kadar?

```
297 kaynak dosyada  next/* import satırı = 20
  next/link ×13 · next/navigation ×3 · next/headers ×2 · next/server ×1 · next/font/google ×1
```

Yani şablonun **%93'ü çerçeveden bağımsız React**. Tasarım sistemi (Tailwind v4 +
Radix + shadcn) zaten çerçeve tanımaz. **Taşınan şey o sistemdir; çerçeve değil.**

### Hüküm

Substrat **Vite + React 19** (depoda D3'ten beri var). Kazanç:

| | Next (statik) | Vite |
|---|---|---|
| Satır içi script | 3 → CSP bloklar | **0** (ölçüldü) |
| CSP değişikliği | `'unsafe-inline'` gerekir | **gerekmez** |
| Canlıda Node çalışması | gerekir ya da export zorlaması | **gerekmez** |
| Dağıtım hattı | yeniden kurulur | `dagit.sh` aynen |
| Parola kapısı | yeniden yazılır | FastAPI'de aynen |

---

## 2. Yüzey eşleşmesi — 22 bölüm → 15 yüzey

| Şablon yüzeyi | Meridian karşılığı | Taşınan bölümler |
|---|---|---|
| Default | Bugün | (tek ekran özeti) |
| Finance | Portföy | brifing · mutabakat · intraemir |
| Analytics | Analiz | topviews · performans |
| Productivity | Antrenman | sprint · hermes |
| Academy | Öğrenme | karne · golge · bilesenic · ajan · skiller |
| Infrastructure | Sistem sağlığı | operasyon · **mudahale** · veriboru · market · intraday |
| File Manager | Belgeler | hafiza · belgeler |
| Chat | Ajan | — |
| Calendar | Çizelge | cizelge |
| Kanban | Karar zinciri **+ ROADMAP** | adaylar · kapilar |
| Tasks | Onay kuyruğu | onaylar |
| Profile | Operatör | ayarlar · tercihler |
| Users | Kullanıcılar | *(2. aşama — çok kullanıcılı yapı)* |
| Roles | Roller ve yetkiler | *(2. aşama)* |
| Authentication | Giriş | *(mevcut parola kapısına bağlanıyor)* |

**Düşen bölüm YOK.** Users/Roles operatörün açık niyetiyle **gerçek çok-kullanıcı
kavramları**dır (2. aşama), Meridian'ın müdahale kollarının kılığı değil — kollar
bu yüzden alarm gelen kutusuyla aynı yüzeye (Infrastructure) taşındı: alarmı gören
operatörün bir sonraki hareketi kolu çekmektir.

**Eski yer imleri kırılmıyor.** `ROTA_TAKMA_ADLARI` eski panonun on yedi adresini
(`#karar`, `#adaylar`, `kosu#…`, RUNBOOK bağları, çekmece çipleri) yeni evine
yönlendiriyor — 35 takma ad.

---

## 3. Emekli olan çiviler ve gerekçeleri

| Çivi | Hüküm | Neden |
|---|---|---|
| `test_G1a_rol_jetonlari_BIREBIR_tasiniyor` (×12) | **emekli** | Ölçtüğü sözleşme (rol jeton katmanı) kararla kaldırıldı. Çivi kırmızı kalır, hiçbir şey öğretmezdi. |
| `test_G1b` Tailwind-skalası yarısı | **emekli** | Şablonun kendi 61 bileşeni bu skalayı kullanıyor; ihlal saymak benimsenen sistemi ihlal saymak olurdu. |
| `test_G1b` hex yarısı | **kapsamı daraldı** | `components/ui/*` satıcı kodu (shadcn `chart.tsx`te 5 çıplak hex var). Kendi kodumuzda kural aynen geçerli: hex tema anahtarını kırar. |
| dagit `[5c]` jeton köprüsü kontrolü | **düştü** | `jetonlar.css`in artık okuyucusu yok. Okuyucusuz dosyanın tazeliğini ölçmek, `[5b]`'nin düzelttiği hata sınıfının ta kendisi (YASA 6). Betik duruyor. |

Hiçbiri silinmedi; hepsi üstü çizili şerhle ve geri-getirme koşuluyla duruyor.

---

## 4. Bu turda ayakta olan

- Kabuk: kenar çubuğu (ikon rayına daralma, tercih deposu), üst bar, tema
  anahtarı, yerleşim denetimleri, ⌘K arama — şablonun kendi bileşenleri
- On beş yüzey, hash yönlendirmesi, derin bağ çapası (`#/dashboard/finance/mutabakat`)
- Durum hapı canlı `/api/today`e bağlı; **boş gövdeyi "sakin" okumuyor**
- Hesap kutusu (broker · sermaye · mod · nabız) canlı
- Sunum: `/pano`, `/pano-onyuk.js`, `/pano-assets/{ad}` — `StaticFiles` montajı YOK,
  sunulan ad kümesi **Vite manifestinin beyanından** okunuyor
- Ölçüldü: 0 satır içi script · 0 satır içi olay özniteliği · 0 dış köken

**Eski pano yerinde duruyor ve canlı olan hâlâ o (`/`).** Geçiş, bölüm gövdeleri
taşındıkça yapılacak; bugün her yüzey hangi bölümlerin taşınmadığını ekranda sayıyor.

---

## 5. Açık kalemler

1. **Kriz kolları** (HALT · Cancel-Open · Flatten · Halt-Learning) yeni panoda
   **yok** ve bu bilinçli: dördü de geri alınamaz icra emri veriyor. Kendi turunda,
   çift onay ve çiviyle gelecekler. Bugün eski panoda çalışıyorlar.
2. **Onay/red düğmeleri** aynı sebeple yok — kuyruk okunur, işlenmez.
3. `/` kökünün yeni panoya çevrilmesi göç bitince, ayrı bir turda.
4. Eski panonun emekliliği (`index.html` + `app.js` + `palette.js`) en son adım;
   87 test dosyası o yüzeylere bakıyor ve emeklilik onların hükmüyle birlikte verilir.
