/* ============================================================================
   ONAY KUYRUĞUNUN NORMALLEŞTİRİLMESİ — dört kaynak, tek görev listesi
   ----------------------------------------------------------------------------
   GELEN KUTUSU TEK UÇTAN GELMİYOR ve bu bir kaza değil, ölçülmüş bir gerçek:

     · `/api/approvals.inbox`  → silahlanma ölçümü · skill revizyonu · Eksen-2 önerisi
     · `/api/today.todays_plans[onay_bekliyor]` → operatörün onayını bekleyen REVIEW planı
       (api.py::_onay_bekleyen_damgala — SUNUCU damgalar, pano yalnız bayrağı okur;
       ölçütü burada yeniden yazmak, aynı sorunun iki cevabını üretmek olurdu)

   İkisini AYRI ekranlarda göstermek, sunucunun `inbox_count`unu (`api.py::_inbox_count`) dört
   kaynaktan toplayıp tek rozete basmasıyla çelişirdi: rozet "4 bekleyen" derken
   operatör bu sayfada yalnız 1 görürdü.

   GELİŞ ZAMANI BU UÇTAN GELMİYOR — İKİNCİ KAYNAKTAN OKUNUYOR. `api_approvals`
   (api.py::api_approvals) her öğeyi ELDEN kuruyor ve damgayı taşımıyor: revizyon kaydının
   `at` alanı ve öneri satırının `ts` alanı gelen kutusu sözlüğüne HİÇ girmiyor.
   Damga yine de ölçülebilir, çünkü aynı ham satırlar `/api/skills`ten
   (`recommendations` / `revisions`, api.py::api_skills) HAM hâlleriyle çıkıyor;
   silahlanmanınki ise `/api/diagnostics.gatekeeper.arming.checked_at`. Eşleşme
   anahtarı `skill` (öneri/revizyon) ve kurulum adı (silahlanma). İkinci uç
   düşerse damga "ölçülemedi + neden" olur; UYDURULMAZ.

   "İŞ İSTİYOR" SUNUCUNUN ÖLÇÜTÜYLE HESAPLANIR (`api.py::_inbox_count`):
   karar verilmiş (`approve`/`reject`) bir kayıt-önerisi gelen kutusunda DURUR ama
   iş İSTEMEZ. Bu ayrımı ekranda yapmazsak, kuyruk hiç azalmayan bir liste olur ve
   okunmayan bir liste alınmamış karar demektir.
   ============================================================================ */
import type {
  KararKaydi,
  OnayGovdesi,
  OnayOgesi,
  PlanOzeti,
  SilahlanmaOlcumu,
  SilahlanmaRaporu,
  SkillGovdesi,
  SkillOnerisi,
  SkillRevizyonu,
} from "./tipler";

export type KuyrukTuru = "silahlanma" | "revizyon" | "oneri" | "plan" | "bilinmeyen";

export const TUR_ETIKET: Record<KuyrukTuru, string> = {
  silahlanma: "Silahlanma",
  revizyon: "Skill revizyonu",
  oneri: "Eksen-2 önerisi",
  plan: "Plan onayı",
  bilinmeyen: "Bilinmeyen tür",
};

/** Çekmecenin türe özel yükü. Ham gövdeler BİLEREK taşınır: çekmece uydurmaz, gösterir. */
export type KuyrukAyrinti =
  | {
      readonly cesit: "silahlanma";
      readonly oge: OnayOgesi;
      readonly olcum: SilahlanmaOlcumu | null;
      readonly cf: { readonly n?: number; readonly win_rate?: number; readonly avg_r?: number } | null;
      readonly olcumNeden: string | null;
    }
  | { readonly cesit: "revizyon"; readonly oge: OnayOgesi; readonly kayit: SkillRevizyonu | null }
  | { readonly cesit: "oneri"; readonly oge: OnayOgesi; readonly kayit: SkillOnerisi | null; readonly karar: KararKaydi | null }
  | { readonly cesit: "plan"; readonly plan: PlanOzeti }
  | { readonly cesit: "bilinmeyen"; readonly oge: OnayOgesi };

export interface KuyrukOgesi {
  /** Tablo satır kimliği. Gelen kutusu kimliği varsa O; plan için `plan:{id}`. */
  readonly kimlik: string;
  readonly tur: KuyrukTuru;
  readonly baslik: string;
  /** Kalemin KONUSU: sembol · skill adı · kurulum adı. Ölçülemezse `null`. */
  readonly konu: string | null;
  readonly konuNeden: string;
  /** ISO geliş damgası — ikinci uçtan joinlenir; `null` ise `gelisNeden` doludur. */
  readonly gelisIso: string | null;
  /**
   * Damga SAAT taşıyor mu? Plan satırlarının kaynağı yalnız `YYYY-MM-DD` (seans tarihi);
   * onu gün başı ISO'suna çevirmek sıralamayı mümkün kılar AMA ekrana saat basmak
   * UYDURMA olurdu. Bayrak, biçimleyicinin hangi çözünürlükte yazacağını söyler.
   */
  readonly gelisSaatli: boolean;
  readonly gelisNeden: string;
  /** Tek satır kanıt (uç ne yazdıysa). Boş dizge de bir cevaptır: uç kanıt yazmamış. */
  readonly kanit: string;
  /** Ne bekliyor — kısa emir cümlesi. */
  readonly bekleyen: string;
  /** Sunucunun `inbox_count` ölçütüyle: bu kalem hâlâ senden İŞ istiyor mu? */
  readonly isIstiyor: boolean;
  /** İş istemiyorsa NEDEN (karar damgası). İstiyorsa `null`. */
  readonly durgunNeden: string | null;
  readonly eylemler: readonly string[];
  readonly not: string | null;
  readonly ayrinti: KuyrukAyrinti;
}

export interface KuyrukOzeti {
  readonly ogeler: readonly KuyrukOgesi[];
  /** `isIstiyor` sayısı — panonun kendi ölçümü. Sunucunun `inbox_count`u ile KARŞILAŞTIRILIR. */
  readonly isIsteyen: number;
  readonly turSayim: ReadonlyMap<KuyrukTuru, number>;
  /** Gelen kutusu ucu okunamadıysa dolu; kuyruğun "boş" görünmesi o zaman BİR YALANDIR. */
  readonly inboxNeden: string | null;
  /** Plan tarafı okunamadıysa dolu. */
  readonly planNeden: string | null;
  /** Geliş damgalarının kaynağı okunamadıysa dolu (damgalar "ölçülemedi" olur). */
  readonly damgaNeden: string | null;
}

/** `arming:momentum_burst` → `momentum_burst`. Önek yoksa `null` (kimlik biçimi değişmiş olabilir). */
export function silahlanmaAdi(kimlik: string | undefined): string | null {
  if (!kimlik) return null;
  const i = kimlik.indexOf(":");
  if (i < 0 || i === kimlik.length - 1) return null;
  return kimlik.slice(i + 1);
}

function turCoz(tip: string | undefined): KuyrukTuru {
  if (tip === "arming") return "silahlanma";
  if (tip === "skill_revision") return "revizyon";
  if (tip === "skill_rec") return "oneri";
  return "bilinmeyen";
}

/** Bir Eksen-2 önerisi hâlâ iş istiyor mu? Ölçüt `api.py::_inbox_count` ile AYNI. */
function oneriIsIstiyor(oge: OnayOgesi): { readonly istiyor: boolean; readonly durgunNeden: string | null } {
  if (oge.uygulanabilir === true) return { istiyor: true, durgunNeden: null };
  const karar = oge.karar_kaydi?.karar;
  if (karar === "approve" || karar === "reject") {
    return {
      istiyor: false,
      durgunNeden: `karar verilmiş: ${karar === "approve" ? "KABUL" : "RET"} — satır kayıt olarak duruyor, iş istemiyor`,
    };
  }
  // `uygulanabilir` HİÇ GELMEDİYSE (undefined) iş istiyor sayılır: fail-open değil fail-loud —
  // "ölçemedim" diyerek bir kararı kuyruktan düşürmek, kaybolan karar demektir.
  return { istiyor: true, durgunNeden: null };
}

/** Plan satırının okunur konusu: `AAPL · breakout_vcp`. */
function planKonusu(p: PlanOzeti): string | null {
  const t = p.ticker ?? null;
  if (!t) return null;
  return p.setup ? `${t} · ${p.setup}` : t;
}

export function kuyrugaCevir(
  onay: OnayGovdesi | null,
  onayHata: string | null,
  skiller: SkillGovdesi | null,
  skillerHata: string | null,
  silahlanma: SilahlanmaRaporu | null,
  silahlanmaHata: string | null,
  planlar: readonly PlanOzeti[] | null,
  planHata: string | null,
): KuyrukOzeti {
  const ogeler: KuyrukOgesi[] = [];

  // --- DAMGA SÖZLÜKLERİ (ikinci uçtan) --------------------------------------
  const oneriDamga = new Map<string, SkillOnerisi>();
  for (const r of skiller?.recommendations ?? []) {
    if (r.skill) oneriDamga.set(r.skill, r);
  }
  const revizyonDamga = new Map<string, SkillRevizyonu>();
  for (const r of skiller?.revisions ?? []) {
    if (r.skill) revizyonDamga.set(r.skill, r);
  }
  const damgaNeden =
    skillerHata !== null
      ? `geliş damgaları /api/skills'ten okunuyor ve o istek düştü — ${skillerHata}`
      : skiller === null
        ? "/api/skills henüz okunmadı"
        : null;

  // SİLAHLANMANIN DAMGASI TEK: rapor bir bütün olarak `checked_at` taşıyor, öğe başına damga YOK.
  // Yani "bu kurulum ne zaman kapıyı geçti" DEĞİL, "bu ölçüm ne zaman koştu" ölçülebiliyor —
  // ikisi aynı şey değil ve ekranda öyle yazıyor.
  const silahlanmaDamga = silahlanma?.checked_at ?? null;
  const silahlanmaDamgaNeden =
    silahlanmaHata !== null
      ? `silahlanma damgası /api/diagnostics'ten okunuyor ve o istek düştü — ${silahlanmaHata}`
      : silahlanma === null
        ? "/api/diagnostics.gatekeeper.arming henüz okunmadı"
        : silahlanmaDamga === null
          ? "silahlanma raporu `checked_at` yazmıyor"
          : null;

  // --- GELEN KUTUSU ---------------------------------------------------------
  for (const [i, oge] of (onay?.inbox ?? []).entries()) {
    const tur = turCoz(oge.type);
    const kimlik = oge.id ?? `${tur}#${i}`;
    const baslik = oge.title ?? "(uç bu öğeye başlık yazmadı)";
    const kanit = oge.evidence ?? "";
    const eylemler = oge.actions ?? [];

    if (tur === "silahlanma") {
      const ad = silahlanmaAdi(oge.id);
      const olcum = ad ? (silahlanma?.measurements?.[ad] ?? null) : null;
      const cf = ad ? (silahlanma?.cf_report?.[ad] ?? null) : null;
      ogeler.push({
        kimlik,
        tur,
        baslik,
        konu: ad,
        konuNeden: "kimlik `arming:{kurulum}` biçiminde değil — kurulum adı çıkarılamadı",
        gelisIso: silahlanmaDamga,
        gelisSaatli: true,
        gelisNeden:
          silahlanmaDamgaNeden ??
          "damga ÖLÇÜMÜN koşma anı (`arming_report.checked_at`), kalemin kuyruğa DÜŞME anı değil",
        kanit,
        bekleyen: "kod değişikliği (ARMED_SETUPS) — Claude'a söylenmeli",
        isIstiyor: true,
        durgunNeden: null,
        eylemler,
        not: oge.note ?? null,
        ayrinti: {
          cesit: "silahlanma",
          oge,
          olcum,
          cf,
          olcumNeden:
            olcum === null
              ? (silahlanmaHata ??
                "silahlanma ölçümü /api/diagnostics.gatekeeper.arming.measurements içinde bu adla bulunamadı")
              : null,
        },
      });
      continue;
    }

    if (tur === "revizyon") {
      const kayit = oge.skill ? (revizyonDamga.get(oge.skill) ?? null) : null;
      ogeler.push({
        kimlik,
        tur,
        baslik,
        konu: oge.skill ?? null,
        konuNeden: "gelen kutusu bu öğede `skill` alanı taşımıyor",
        gelisIso: kayit?.at ?? null,
        gelisSaatli: true,
        gelisNeden:
          damgaNeden ??
          (oge.skill
            ? `/api/skills.revisions içinde "${oge.skill}" için \`at\` damgası yok`
            : "eşleşme anahtarı (`skill`) yok — damga aranamadı"),
        kanit,
        bekleyen: "taslağı uygula ya da reddet",
        isIstiyor: true,
        durgunNeden: null,
        eylemler,
        not: oge.note ?? null,
        ayrinti: { cesit: "revizyon", oge, kayit },
      });
      continue;
    }

    if (tur === "oneri") {
      const kayit = oge.skill ? (oneriDamga.get(oge.skill) ?? null) : null;
      const { istiyor, durgunNeden } = oneriIsIstiyor(oge);
      ogeler.push({
        kimlik,
        tur,
        baslik,
        konu: oge.skill ? (oge.action ? `${oge.skill} → ${oge.action}` : oge.skill) : null,
        konuNeden: "gelen kutusu bu öğede `skill` alanı taşımıyor",
        gelisIso: kayit?.ts ?? null,
        gelisSaatli: true,
        gelisNeden:
          damgaNeden ??
          (oge.skill
            ? `/api/skills.recommendations içinde "${oge.skill}" için \`ts\` damgası yok`
            : "eşleşme anahtarı (`skill`) yok — damga aranamadı"),
        kanit,
        bekleyen: oge.uygulanabilir === false ? "kayıt kararı (kabul/ret) — davranış DEĞİŞMEZ" : "öneriyi uygula",
        isIstiyor: istiyor,
        durgunNeden,
        eylemler,
        not: oge.note ?? null,
        ayrinti: { cesit: "oneri", oge, kayit, karar: oge.karar_kaydi ?? null },
      });
      continue;
    }

    // BİLİNMEYEN TÜR SESSİZCE DÜŞÜRÜLMEZ: uç yarın dördüncü bir tür ekleyebilir ve o gün
    // kuyruk onu göstermezse operatör bekleyen bir kararı hiç görmez.
    ogeler.push({
      kimlik,
      tur,
      baslik,
      konu: oge.skill ?? null,
      konuNeden: `bu pano \`type=${String(oge.type)}\` türünü tanımıyor — konu alanı çıkarılamadı`,
      gelisIso: null,
      gelisSaatli: true,
      gelisNeden: `tanınmayan tür (\`${String(oge.type)}\`) — damga kaynağı bilinmiyor`,
      kanit,
      bekleyen: "bilinmiyor — uç yeni bir tür döndürdü",
      isIstiyor: true,
      durgunNeden: null,
      eylemler,
      not: oge.note ?? null,
      ayrinti: { cesit: "bilinmeyen", oge },
    });
  }

  // --- ONAY BEKLEYEN REVIEW PLANLARI ---------------------------------------
  for (const p of planlar ?? []) {
    if (!p.onay_bekliyor) continue;
    ogeler.push({
      kimlik: `plan:${p.id ?? p.ticker ?? "?"}`,
      tur: "plan",
      baslik: `REVIEW planı onay bekliyor: ${p.ticker ?? "(sembolsüz)"}`,
      konu: planKonusu(p),
      konuNeden: "plan satırı `ticker` taşımıyor",
      // PLANIN DAMGASI SEANS TARİHİ, SAAT DEĞİL: `date` alanı `YYYY-MM-DD` ve saat taşımıyor.
      // Gün başına çevirmek uydurma olurdu; ekranda tarih olarak, saatsiz gösteriliyor.
      gelisIso: p.date ? `${p.date}T00:00:00Z` : null,
      // SAATSİZ: plan yalnız seans TARİHİ taşıyor. Gün başı ISO'su SIRALAMA içindir;
      // ekrana saat basmak, kaynağın hiç ölçmediği bir değeri yazmak olurdu.
      gelisSaatli: false,
      gelisNeden: p.date
        ? "plan yalnız SEANS TARİHİ taşıyor (saat yok) — gün başı olarak sıralanıyor"
        : "plan satırı `date` taşımıyor",
      kanit:
        p.gate_reasons && p.gate_reasons.length > 0
          ? `kapı: ${p.gate_reasons.join(" · ")}`
          : "kapı gerekçesi yazılmamış",
      bekleyen: "planı onayla — GERİ ALINAMAZ icra (İncele → çift adımlı karar)",
      isIstiyor: true,
      durgunNeden: null,
      eylemler: [],
      // `eylemler` UÇTAN GELEN eylem listesidir (`inbox.actions`) ve plan öğesi gelen kutusundan
      // GELMİYOR (kaynağı /api/today) — boş kalması doğru. Panonun kendi "İncele" düğmesi bu
      // listeden çizilmez; oraya elle bir dizge yazmak, eylemin uçtan geldiğini iddia etmek olurdu.
      not:
        "Onay ANINDA aynaya gönderim denenir (POST /api/plan/{id}/onayla) — kontrol kararı DEĞİŞMEZ, " +
        "plan işleme hazır planlara girer ve bracket emir gönderilmeye çalışılır. Bu yüzden karar satır " +
        "sonunda değil, kanıtın ALTINDA ve çift adımlı (KararPaneli).",
      ayrinti: { cesit: "plan", plan: p },
    });
  }

  const turSayim = new Map<KuyrukTuru, number>();
  let isIsteyen = 0;
  for (const o of ogeler) {
    turSayim.set(o.tur, (turSayim.get(o.tur) ?? 0) + 1);
    if (o.isIstiyor) isIsteyen += 1;
  }

  return {
    ogeler,
    isIsteyen,
    turSayim,
    inboxNeden:
      onayHata !== null
        ? onayHata
        : onay === null
          ? "/api/approvals henüz okunmadı"
          : onay.inbox === undefined
            ? "/api/approvals `inbox` alanını döndürmedi — boş kuyruk DEĞİL, ölçülemedi"
            : null,
    planNeden:
      planHata !== null
        ? planHata
        : planlar === null
          ? "/api/today henüz okunmadı — onay bekleyen REVIEW planları bu listede YOK"
          : null,
    damgaNeden,
  };
}
