/* ============================================================================
   YÜZEY KAYDI — studio-admin'in bilgi mimarisi, Meridian'ın içeriğiyle
   ----------------------------------------------------------------------------
   OPERATÖR KARARI (2026-08-25): pano tamamen studio-admin şablonuna geçiyor ve
   gezinme AĞACI ŞABLONUNKİDİR — Meridian'ın eski yedi yüzeyi (bugun/portfoy/
   karar/analiz/saglik/ogrenme/kilitler) artık bir gezinme birimi DEĞİL. Şablonun
   tuttuğumuz on beş yüzeyi (7 pano + 8 sayfa) ve Meridian'ın o günkü yirmi iki bölümü
   burada BİREBİR eşleşiyordu; eşleşmeyen bölüm YOK ve düşen bölüm YOK.

   KAYIT O GÜNDEN BERİ BÜYÜDÜ ve sayı burada DONDURULMAZ (bayat-beyan sınıfı): bugün
   17 yüzey · 40 bölüm (ölçüldü 2026-09-02). Şablonda karşılığı OLMAYAN iki yüzey var:
   `gateway` (Kapı, TSK-090) ve `memory` (Hafıza, TSK-091) — yukarıdaki "birebir
   eşleşme" cümlesi göç turunun ölçümüdür, bugünün sözleşmesi değil. İkisi de şablondan
   değil Meridian'ın kendi altyapısından doğduğu için `sablon` alanı bunu açıkça yazar.

   YOLLAR ŞABLONUNKİYLE AYNI (`/dashboard/finance` …) ve bu bilinçli: şablondan
   alınan arama iletişimi, kenar çubuğu ve gelecekte alınacak sayfa gövdeleri bu
   yolları okuyor. Kendi adlarımızı yazsaydık her şablon güncellemesinde elle
   çeviri yapmak gerekirdi.

   ESKİ YER İMLERİ KIRILMIYOR: `ROTA_TAKMA_ADLARI` eski panonun on yedi adresini
   (`#karar`, `#adaylar`, `kosu#…`, RUNBOOK bağları, çekmece çipleri) yeni evine
   yönlendiriyor.
   ============================================================================ */
import { bolumEtiketi } from "./yuzeyler/ajan/gramer";
import {
  Activity,
  BookOpen,
  Bot,
  Boxes,
  Brain,
  CalendarDays,
  CandlestickChart,
  ChartColumn,
  ClipboardCheck,
  Cpu,
  Database,
  DoorOpen,
  Eye,
  FileText,
  FlaskConical,
  Fingerprint,
  FolderOpen,
  Gauge,
  GaugeCircle,
  GraduationCap,
  Hammer,
  HeartPulse,
  Kanban,
  KeyRound,
  Landmark,
  Layers,
  LineChart,
  ListTodo,
  type LucideIcon,
  // `Map` küresel `Map` tipini gölgelemesin diye yeniden adlandırıldı.
  Map as HaritaIkonu,
  MessageSquare,
  MessagesSquare,
  Milestone,
  Radar,
  Scale,
  Send,
  Server,
  Settings2,
  ShieldAlert,
  Sparkles,
  Table2,
  UserPlus,
  UserRound,
  Users,
  Wallet,
  Waypoints,
} from "lucide-react";

export interface Bolum {
  /** Eski panodaki `.alan-bolum` kimliği. Yer imleri ve RUNBOOK bağları buna bağlı. */
  readonly kimlik: string;
  readonly baslik: string;
  /** Bölümün cevapladığı SORU. Başlık ne olduğunu, bu neden bakıldığını söyler. */
  readonly soru: string;
  readonly ikon: LucideIcon;
}

export interface Yuzey {
  /** Şablondaki adı — eşleşmenin hangi sayfadan geldiği KAYBOLMASIN diye duruyor. */
  readonly sablon: string;
  readonly baslik: string;
  readonly soru: string;
  readonly ikon: LucideIcon;
  readonly grup: "Panolar" | "Sayfalar";
  readonly bolumler: readonly Bolum[];
  /** KAYITTA DURAMAYAN BÖLÜMLERİN ETİKET ÇÖZÜCÜSÜ (2026-08-31, inceleme Ö-1).
   *
   *  `bolumler` STATİK bir listedir. Tüketicileri SAYILDI (2026-08-31, yeniden-inceleme
   *  Ö-1a — önceki "iki tüketici" cümlesi eksikti): `gezinme.ts` (kenar çubuğu ağacı;
   *  `nav-main.tsx` yalnız onun ürettiğini tüketir) · `komutlar.ts` (⌘K paleti) ·
   *  `kabuk/Ustbar.tsx` (kırıntı) · `yuzeyler/{GenelYuzey,AnalizYuzey,Operator}.tsx`
   *  (kendi yüzeylerinin gövdeleri; `chat` bunlara hiç uğramaz, gövdesi `Ajan.tsx`) ·
   *  `tests/test_pano_yuzey_kaydi_v288.py` (parite çivisi).
   *  SAYILMAYAN buydu — `kabuk/Ustbar.tsx` kırıntısı
   *  `rota.bolum`u kayıtlı `kimlik`lerle BİREBİR eşleştiriyor. Ajan yüzeyi bu turda
   *  bölüm adresini `<muhatap>.<sekme>` biçimine taşıdı: muhatap ROSTER'DAN türüyor
   *  (statik kayda sığmaz) ve ayraç `.` olduğu için v324'ün slug şartını da geçemez.
   *  Kayıt bu yüzden GENİŞLETİLDİ: bir yüzey, kaydedilemeyen bölümleri için kendi
   *  çözücüsünü verir ve kırıntı hiçbir derin bağda SESSİZCE düşmez.
   *
   *  `null` dönüşü "bu bölüm adının bir karşılığı yok" demektir; kırıntı o zaman
   *  ikinci seviyeyi bilerek çizmez (eski davranış). */
  readonly bolumCoz?: (bolum: string) => string | null;
}

/** Anahtar = şablon yolunun son parçası; yol `/dashboard/<anahtar>`. */
export const YUZEYLER = {
  // ---- PANOLAR ----------------------------------------------------------------
  default: {
    sablon: "Default",
    baslik: "Bugün",
    soru: "Şu an sakin mi, senden bir şey mi bekliyor?",
    ikon: GaugeCircle,
    grup: "Panolar",
    /* BÖLÜM YOK VE BU BİR EKSİK DEĞİL, SÖZLEŞME.
       Uzlaştırma turunda dört bölüm (kpi · egri · hukum · planlar) buraya eklenmişti;
       o turdaki çivi "ekranda çapası olan her blok kayıtta olmalı" diyordu. Çivinin o
       yönü sonradan EMEKLİ oldu (bir çapa gezinme durağı olmak zorunda değil — sayfa
       içi bir bloğun kendi kimliği de olabilir) ve girdiler GERİ ALINDI. İki sebep:

         1. GERİLEME, ölçüldü: `nav-main.tsx` alt maddesi OLAN bir maddeyi düz bağdan
            AÇILIR TETİĞE çeviriyor. "Bugün" açılış ekranıdır ve tek tıkla ulaşılmak
            zorundadır; dört girdiyle tıklama artık gitmiyor, menü AÇIYORDU.
         2. YÜZEYİN KENDİ SÖZLEŞMESİ: "tek ekran, her kart bir ÖZET; detay burada YOK,
            detayın yeri yüzeydir." Kendi içine dört durak koymak o cümleyi bozar.

       Çapalar gövdede DURUYOR (silinmedi): derin bağ `#/dashboard/default/planlar`
       çalışmaya devam eder, yalnız kenar çubuğu onu bir durak olarak ÜRETMEZ. */
    bolumler: [],
  },
  finance: {
    sablon: "Finance",
    baslik: "Portföy",
    soru: "Kitap nerede duruyor?",
    ikon: Wallet,
    grup: "Panolar",
    bolumler: [
      { kimlik: "brifing", baslik: "Brifing", soru: "Sermaye ve açık pozisyonlar ne durumda?", ikon: ClipboardCheck },
      { kimlik: "mutabakat", baslik: "Mutabakat masası", soru: "Bizim defter ile brokerin defteri tutuyor mu?", ikon: Scale },
      { kimlik: "intraemir", baslik: "Seans içi emir", soru: "İşleme hazırlık kontrolü açık mı, deneme icrası ne diyor?", ikon: Send },
    ],
  },
  analytics: {
    sablon: "Analytics",
    baslik: "Analiz",
    soru: "Biriken kararlar ne söylüyor?",
    ikon: LineChart,
    grup: "Panolar",
    bolumler: [
      { kimlik: "topviews", baslik: "En çok bakılanlar", soru: "Kararların birikimi nereye işaret ediyor?", ikon: Eye },
      { kimlik: "performans", baslik: "Para eğrisi", soru: "Sermaye eğrisi ne yapıyor?", ikon: LineChart },
    ],
  },
  productivity: {
    sablon: "Productivity",
    baslik: "Antrenman",
    soru: "Makine çalışıyor mu, yoksa yalnız duruyor mu?",
    ikon: Activity,
    grup: "Panolar",
    bolumler: [
      { kimlik: "sprint", baslik: "Antrenman turu", soru: "Antrenman koşuyor mu, kaç aday değerlendirildi?", ikon: Activity },
      { kimlik: "hermes", baslik: "Danışma", soru: "Değerlendirme hattı ne durumda, geri dolum nerede?", ikon: Sparkles },
    ],
  },
  academy: {
    sablon: "Academy",
    baslik: "Öğrenme",
    soru: "Öğreniyor mu, yoksa yalnız koşuyor mu?",
    ikon: GraduationCap,
    grup: "Panolar",
    bolumler: [
      { kimlik: "karne", baslik: "Dürüst karne", soru: "Öğrenme döngüsü gerçekten kapanıyor mu?", ikon: ClipboardCheck },
      { kimlik: "golge", baslik: "Deneme", soru: "Denenen kural ne gösteriyor?", ikon: FlaskConical },
      { kimlik: "bilesenic", baslik: "Bileşen içi", soru: "Hangi bileşen skoru taşıyor?", ikon: Boxes },
      { kimlik: "ajan", baslik: "Strateji sürümleri", soru: "v01'den bugüne ne değişti?", ikon: Cpu },
      { kimlik: "skiller", baslik: "Araçlar", soru: "Ajanın elinde hangi araçlar var?", ikon: Hammer },
    ],
  },
  infrastructure: {
    sablon: "Infrastructure",
    baslik: "Sistem sağlığı",
    soru: "Makine sağlam mı, veri temiz mi?",
    ikon: Server,
    grup: "Panolar",
    bolumler: [
      { kimlik: "operasyon", baslik: "Alarm gelen kutusu", soru: "Çalan bir alarm var mı?", ikon: ShieldAlert },
      // MÜDAHALE KOLLARI ALARMLA AYNI YÜZEYDE: alarmı gören operatörün bir sonraki
      // hareketi kolu çekmektir. İkisini ayrı yüzeylere koymak, en kötü anda bir
      // gezinme adımı eklemek olurdu. (Users/Roles bu turda gerçek çok-kullanıcı
      // kavramlarına ayrıldı — kollar oradan buraya taşındı.)
      { kimlik: "mudahale", baslik: "Müdahale kolları", soru: "Hangi durdurma kolu çekili?", ikon: Radar },
      { kimlik: "veriboru", baslik: "Veri borusu", soru: "Veri nereden geliyor, nerede tıkandı?", ikon: Database },
      { kimlik: "market", baslik: "Piyasa", soru: "Kaç bar bayat, evren taze mi?", ikon: CandlestickChart },
      { kimlik: "intraday", baslik: "Seans içi akış", soru: "Gün içi akış canlı mı?", ikon: Activity },
    ],
  },
  /* KAPI — TSK-090. ŞABLONDA KARŞILIĞI OLMAYAN İLK YÜZEY ve `sablon` alanı bunu SÖYLER.
     Buraya uydurma bir şablon adı ("Gateway") yazmak, kaydın kendi sözleşmesini ("eşleşmenin
     hangi sayfadan geldiği KAYBOLMASIN") tersine çevirirdi: alan tam da hangi eşleşmenin
     GERÇEK olduğunu tutuyor, ve burada gerçek olan eşleşme YOKLUĞUdur.

     SİSTEM SAĞLIĞININ HEMEN ARDINDA, ve sıra bir kaza değil: ikisi de "makine sağlam mı"
     sorusunun katmanları — biri kutuyu ve süreçleri, öteki kutunun ÖNÜNDEKİ kapıyı ölçer.
     Bir arıza triyajı yukarıdan aşağı okunur ve kapı, uygulamaya varmadan önceki duraktır.

     DÖRT BÖLÜM = EKRANDAKİ DÖRT `bolum-kapi-*` ÇAPASI (v288 paritesi). Kimlikler `kapi-`
     önekli çünkü kayıt sözlüğü bölüm kimliğini KÜRESEL tutuyor: çıplak `saglik`/`metrikler`
     bir gün başka bir yüzeyde de doğar ve biri ötekini sessizce ezerdi. */
  gateway: {
    sablon: "(şablonda karşılığı yok — Meridian'a özgü)",
    baslik: "Kapı",
    soru: "İstekler dışarı hangi kapıdan çıkıyor, kapı sağlam mı?",
    ikon: DoorOpen,
    grup: "Panolar",
    bolumler: [
      { kimlik: "kapi-saglik", baslik: "Kapının sağlığı", soru: "APISIX'in yönetim ve metrik yüzeyleri okunabiliyor mu?", ikon: HeartPulse },
      { kimlik: "kapi-rotalar", baslik: "LLM rotaları", soru: "Hangi model önce deneniyor, düşerse nereye geçiliyor?", ikon: Waypoints },
      { kimlik: "kapi-metrikler", baslik: "Kapıdan geçen trafik", soru: "Hangi rotadan kaç istek geçti, hangi durum koduyla döndü?", ikon: ChartColumn },
      { kimlik: "kapi-fazlar", baslik: "Kurulum fazları", soru: "Kapının hangi fazı canlı, hangisi hâlâ bekliyor?", ikon: Milestone },
    ],
  },
  /* HAFIZA — TSK-091. Kapı'nın KARDEŞİ: şablonda karşılığı olmayan İKİNCİ yüzey ve
     `sablon` alanı bunu yine SÖYLER (uydurma bir şablon adı, kaydın kendi sözleşmesini
     tersine çevirirdi — alan hangi eşleşmenin GERÇEK olduğunu tutuyor).

     KAPI'NIN HEMEN ARDINDA, ve sıra yine bir kaza değil: sistem sağlığı kutuyu, Kapı
     kutunun ÖNÜNDEKİ kapıyı, Hafıza da o kapıdan geçen bilginin NEREDE BİRİKTİĞİNİ
     ölçer. Üçü bir triyajın üç durağıdır ve yukarıdan aşağı okunur.

     KİMLİKLER `hafiza-` ÖNEKLİ, VE ÖNEK BİR SÜS DEĞİL: kayıt sözlüğü bölüm kimliğini
     KÜRESEL tutuyor (v288 tekillik çivisi) ve ÇIPLAK `hafiza` kimliği Belgeler
     yüzeyinde ZATEN DOLU. Önek olmasaydı iki kayıttan biri ötekini sessizce ezer ve
     bir bölüm derin bağda YANLIŞ yüzeye çözülürdü.

     DÖRT BÖLÜM = EKRANDAKİ DÖRT `bolum-hafiza-*` ÇAPASI (v288 paritesi). */
  memory: {
    sablon: "(şablonda karşılığı yok — Meridian'a özgü)",
    baslik: "Hafıza",
    soru: "Sistem ne hatırlıyor, bu bilgi nereden geldi?",
    ikon: Brain,
    grup: "Panolar",
    bolumler: [
      { kimlik: "hafiza-bankalar", baslik: "Hafıza bankaları", soru: "Hangi bankalar var, hafıza servisi ayakta mı?", ikon: Landmark },
      { kimlik: "hafiza-bellekler", baslik: "Kayıtlar", soru: "Bu bankada ne yazılı, tek tek ne diyor?", ikon: BookOpen },
      { kimlik: "hafiza-operasyon", baslik: "Yazma ve okuma hareketleri", soru: "Bankaya son günlerde ne işlendi?", ikon: Activity },
      { kimlik: "hafiza-kota", baslik: "Model çağrısı kullanımı", soru: "Hafıza servisi ne kadar model çağrısı harcadı?", ikon: Gauge },
    ],
  },
  "file-manager": {
    sablon: "File Manager",
    baslik: "Belgeler",
    soru: "Ne öğrenildi ve nereye yazıldı?",
    ikon: FolderOpen,
    grup: "Panolar",
    bolumler: [
      { kimlik: "hafiza", baslik: "Hafıza", soru: "Hangi dersler biriktirildi?", ikon: BookOpen },
      { kimlik: "belgeler", baslik: "Karar belgeleri", soru: "Hangi karar hangi turda verildi?", ikon: FileText },
    ],
  },

  // ---- SAYFALAR ---------------------------------------------------------------
  chat: {
    sablon: "Chat",
    baslik: "Ajan",
    soru: "Ajana ne sorabilirim, ne cevap verdi?",
    ikon: MessageSquare,
    grup: "Sayfalar",
    // DÖRT SEKME = DÖRT BÖLÜM ve derin bağ sekmeyi de SEÇİYOR (`Ajan.tsx::bolumSec`).
    // Çapalar gövdede zaten vardı; eksik olan kayıttı, yani kenar çubuğu üç sekmenin
    // hiçbirine bağ üretmiyordu. Sıra sekme çubuğundaki sıradır.
    // `filo` 2026-08-31'de eklendi: ilk üçü HİPOTEZ defterini okur (öneri üreteci),
    // dördüncüsü ajanların KENDİ oturum defterlerini (`/api/ajanlar`). İki ayrı
    // muhatap, iki ayrı kaynak — aynı sekmede birleştirmek onları tek gerçek sanmaktı.
    bolumler: [
      { kimlik: "sohbet", baslik: "Sohbet", soru: "Ajan ne önerdi, kontrol ne cevap verdi?", ikon: MessagesSquare },
      { kimlik: "defter", baslik: "Defter", soru: "Aynı kayıtlar sıralandığında hangi öneri öne çıkıyor?", ikon: Table2 },
      { kimlik: "olcum", baslik: "Ölçüm", soru: "Kim konuştu, kontrol ne dedi, tahmin tuttu mu?", ikon: Bot },
      { kimlik: "filo", baslik: "Filo", soru: "Botlar ve ana model ne konuştu, ne teslim etti?", ikon: Users },
    ],
    // Yeni kanonik adres `<muhatap>.<sekme>`; etiketi TEK kaynaktan (`SEKME_ETIKET`) gelir.
    bolumCoz: bolumEtiketi,
  },
  calendar: {
    sablon: "Calendar",
    baslik: "Çizelge",
    soru: "Hangi adım ne zaman koştu, sırada ne var?",
    ikon: CalendarDays,
    grup: "Sayfalar",
    bolumler: [{ kimlik: "cizelge", baslik: "Hattın adımları", soru: "Zamanlanmış işler zamanında koştu mu?", ikon: CalendarDays }],
  },
  kanban: {
    sablon: "Kanban",
    baslik: "Karar zinciri",
    soru: "Gece ne buldu, aday hangi kontrolde?",
    ikon: Kanban,
    grup: "Sayfalar",
    bolumler: [
      { kimlik: "adaylar", baslik: "Adaylar", soru: "Bu seans hangi planlar kuruldu?", ikon: Layers },
      { kimlik: "kapilar", baslik: "Kontroller", soru: "Aday hangi kontrolde düştü, hangisinden geçti?", ikon: Radar },
      // İKİNCİ SEKME, İKİNCİ TAHTA: `KanbanYuzey.tsx` çapayı kendisi tanımlamış ve
      // şerhinde "kayıt dosyası bana kapalı" diye not düşmüştü — o boşluk burada kapanıyor.
      { kimlik: "roadmap", baslik: "Yol haritası", soru: "Hangi iş hangi bölümde, hangi durumda?", ikon: HaritaIkonu },
    ],
  },
  tasks: {
    sablon: "Tasks",
    baslik: "Onay kuyruğu",
    soru: "Senden iş isteyen ne var?",
    ikon: ListTodo,
    grup: "Sayfalar",
    bolumler: [{ kimlik: "onaylar", baslik: "Onayını bekleyen planlar", soru: "Hangi karar senin onayında duruyor?", ikon: ClipboardCheck }],
  },
  profile: {
    sablon: "Profile",
    baslik: "Operatör",
    soru: "Hesabım nasıl bağlı, tercihlerim ne?",
    ikon: UserRound,
    grup: "Sayfalar",
    bolumler: [
      { kimlik: "ayarlar", baslik: "Broker ve sırlar", soru: "Alpaca hesabı ve anahtarlar ne durumda?", ikon: Settings2 },
      { kimlik: "tercihler", baslik: "Arayüz tercihleri", soru: "Tema, yüz ve yerleşim nasıl kayıtlı?", ikon: Settings2 },
    ],
  },
  /* KULLANICILAR VE ROLLER — 2. AŞAMA (operatör kararı, 2026-08-25).
     Meridian bugün TEK OPERATÖRLÜ: `auth` bir parola tutuyor, kullanıcı tablosu YOK
     (`meridian/api.py::api_login`). Bu iki yüzey çok-kullanıcılı yapının İSKELETİ ve
     ekranda bunu AÇIKÇA yazıyorlar — dolu görünen ama hiçbir kaydı olmayan bir
     kullanıcı tablosu çizmek, olmayan bir yeteneği var göstermek olurdu. */
  users: {
    sablon: "Users",
    baslik: "Kullanıcılar",
    soru: "Sisteme kimler erişebiliyor?",
    ikon: Users,
    grup: "Sayfalar",
    bolumler: [],
  },
  roles: {
    sablon: "Roles",
    baslik: "Roller ve yetkiler",
    soru: "Hangi rol neyi yapabilir?",
    ikon: Brain,
    grup: "Sayfalar",
    bolumler: [],
  },
  /* KİMLİK — şablonun giriş/kayıt ekranları, Meridian'ın parola kapısına bağlı.
     Kapı GERÇEK ve bugün canlıda çalışıyor: `/api/login`, `/api/setup-password`,
     `/api/session`, `/api/logout`. Kayıt ekranı 2. aşamanın ucu — bugün yalnız
     İLK PAROLAYI kurar (`password_set` false iken), yeni kullanıcı açmaz. */
  authentication: {
    sablon: "Authentication",
    baslik: "Giriş",
    soru: "Kimim, oturumum açık mı?",
    ikon: Fingerprint,
    grup: "Sayfalar",
    // İKİ SEKME İKİSİ BİRDEN KAYITTA, tek başına "kayit" DEĞİL. Gövdede yalnız kayıt
    // sekmesinin çapası vardı; yalnız onu kaydetseydik kenar çubuğu "Giriş"i açılır
    // bir başlığa çevirir ve TEK çocuğu, bugün hiçbir uca bağlı OLMAYAN kayıt formu
    // olurdu (`nav-main.tsx`: alt maddesi olan madde artık bağ değil, açılır tetiktir).
    // Yüzeyin asıl içeriği o zaman gezinmede hiç görünmezdi.
    bolumler: [
      { kimlik: "giris", baslik: "Panoya giriş", soru: "Parolayla nasıl giriş yapılır?", ikon: KeyRound },
      // KAYIT BUGÜN BAĞSIZ ve bunu kendi gövdesi yazıyor (alanlar `disabled`, gerekçe
      // ekranda). Kaydetmek onu "çalışıyor" ilan etmez; SORUSU zaten bu — cevabı hayır.
      { kimlik: "kayit", baslik: "Kayıt", soru: "Yeni kullanıcı açılabiliyor mu?", ikon: UserPlus },
    ],
  },
} as const satisfies Record<string, Yuzey>;

export type YuzeyAnahtari = keyof typeof YUZEYLER;

export const YUZEY_ANAHTARLARI = Object.keys(YUZEYLER) as YuzeyAnahtari[];

/** Şablonun kendi kökü. Hash yönlendirmesi de bu biçimi taşır (`#/dashboard/default`). */
export const YUZEY_KOKU = "/dashboard";

export const VARSAYILAN_YUZEY: YuzeyAnahtari = "default";

export function yuzeyYolu(anahtar: YuzeyAnahtari, bolum?: string): string {
  return bolum ? `${YUZEY_KOKU}/${anahtar}/${bolum}` : `${YUZEY_KOKU}/${anahtar}`;
}

/** Bir bölüm adresinin GÖRÜNEN adı — kırıntının tek sorgusu (2026-08-31, Ö-1).
 *
 *  ÖNCE kayıt (`bolumler`), SONRA yüzeyin kendi çözücüsü (`bolumCoz`). İkisi de
 *  susarsa `null` döner ve kırıntı ikinci seviyeyi bilerek çizmez. Aramanın burada
 *  durmasının sebebi TEK KAYNAK: adres biçimini bilen tek yer kayıt sistemidir,
 *  kırıntının kendisi değil — `Ustbar` bir `split(".")` yazsaydı aynı biçim iki
 *  yerde bilinir ve sessizce ayrışırdı. */
export function bolumBasligi(anahtar: YuzeyAnahtari, bolum: string): string | null {
  const a: Yuzey = YUZEYLER[anahtar];
  const kayitli = a.bolumler.find((x) => x.kimlik === bolum);
  if (kayitli !== undefined) return kayitli.baslik;
  return a.bolumCoz?.(bolum) ?? null;
}

/* ESKİ ADRESLER → YENİ EVİ.
   İki sınıf var ve ikisi de eski panodan geliyor (`app.js::ROUTE_ALIAS` + `VIEWS`):
     (a) eski YÜZEY adları — `#karar`, `#saglik`, `#ogrenme` …
     (b) eski BÖLÜM adları — `#adaylar`, `#market`, `#hafiza` … (bölüm çapasıyla birlikte)
   Bir yer imini kırmak sessiz bir kayıptır: operatörün RUNBOOK bağları, çekmece
   çipleri ve tarayıcı yer imleri hep bu adresleri yazıyor. */
export const ROTA_TAKMA_ADLARI: Readonly<Record<string, { yuzey: YuzeyAnahtari; bolum?: string }>> = {
  // (a) eski yedi yüzey + S2R öncesi beş ad
  bugun: { yuzey: "default" },
  genel: { yuzey: "default" },
  portfoy: { yuzey: "finance" },
  karar: { yuzey: "kanban" },
  kosu: { yuzey: "kanban" },
  analiz: { yuzey: "analytics" },
  saglik: { yuzey: "infrastructure" },
  veri: { yuzey: "infrastructure" },
  gozetim: { yuzey: "infrastructure" },
  ogrenme: { yuzey: "academy" },
  kilitler: { yuzey: "infrastructure", bolum: "mudahale" },
  // (b) eski bölüm adları — hedefte hem yüzey hem çapa var
  brifing: { yuzey: "finance", bolum: "brifing" },
  mutabakat: { yuzey: "finance", bolum: "mutabakat" },
  intraemir: { yuzey: "finance", bolum: "intraemir" },
  adaylar: { yuzey: "kanban", bolum: "adaylar" },
  kapilar: { yuzey: "kanban", bolum: "kapilar" },
  onaylar: { yuzey: "tasks", bolum: "onaylar" },
  topviews: { yuzey: "analytics", bolum: "topviews" },
  performans: { yuzey: "analytics", bolum: "performans" },
  operasyon: { yuzey: "infrastructure", bolum: "operasyon" },
  veriboru: { yuzey: "infrastructure", bolum: "veriboru" },
  market: { yuzey: "infrastructure", bolum: "market" },
  intraday: { yuzey: "infrastructure", bolum: "intraday" },
  cizelge: { yuzey: "calendar", bolum: "cizelge" },
  karne: { yuzey: "academy", bolum: "karne" },
  golge: { yuzey: "academy", bolum: "golge" },
  bilesenic: { yuzey: "academy", bolum: "bilesenic" },
  ajan: { yuzey: "academy", bolum: "ajan" },
  skiller: { yuzey: "academy", bolum: "skiller" },
  hermes: { yuzey: "productivity", bolum: "hermes" },
  hafiza: { yuzey: "file-manager", bolum: "hafiza" },
  mudahale: { yuzey: "infrastructure", bolum: "mudahale" },
  ayarlar: { yuzey: "profile", bolum: "ayarlar" },
};
