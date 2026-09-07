/* ============================================================================
   SOHBET ÖNERİSİNİN SÖZLÜĞÜ — tür → ekrandaki cümle (TSK-012 dalga-B, B2)
   ----------------------------------------------------------------------------
   `meridian/sohbet.py` OKUNARAK YAZILDI, TAHMİN EDİLMEDİ:
     · `ONERI_TURLERI = ("plan_onayi", "alarm_ack", "not")` — DONUK sözlük; yeni tür
       yeni bir KARARDIR, kod genişletemez (spec §2). Bu dosya o üçlünün kopyasını
       taşır ve ayrışması ÇİVİLİ (`tests/civiler/sohbet_civileri.mjs`): pano Python'u
       import edemez, ama kopyayı ölçüsüz bırakmak sessiz ayrışma olurdu.
     · `oneri_kimligi()` → `SO-<YYYYAAGGTSSDDSSZ>-<n>` ve İKİ NOKTA TAŞIMAZ (bilinçli:
       `POST /api/approvals/{id}` kimliği ilk `:`ten bölerek önek çıkarıyor).
     · İCRA `api.py::_sohbet_icra`DADIR ve onay ANINDA koşar: `plan_onayi` →
       `loop.operator_onay_ver` (bracket emir DENENİR), `alarm_ack` →
       `_alarm_ack_uygula(ack_by="operator")`, `not` → icra YOK.

   NEDEN AYRI DOSYA: `onaylar.ts` ve `onayEylem.ts` bu sözlüğün İKİ tüketicisi
   (biri satırı kurar, öteki karar hedefini çözer). İki yerde yazsaydık aynı gerçeğin
   iki kopyası sessizce ayrışırdı (tek-kaynak yasası). Ayrıca bu dosya React'e
   dokunmaz — node'da çağrılabiliyor, yani hükümleri gerçekten ölçülüyor.

   GLOBAL ETKİ EKRANDA SÖYLENİR (B1'in devrettiği kaygı): `alarm_ack` TEK bir alarmı
   değil, BEKLEYEN TÜM alarmları kapatır. Bunu yalnız kod yorumunda bırakmak, operatöre
   tek satırlık bir onay gibi göstermek olurdu.
   ============================================================================ */

/** DONUK sözlük — `sohbet.py::ONERI_TURLERI`nin kopyası, ayrışması çivili. */
export const SOHBET_ONERI_TURLERI = ["plan_onayi", "alarm_ack", "not"] as const;

export type SohbetOneriTuru = (typeof SOHBET_ONERI_TURLERI)[number];

/** `SO-20260907T193000Z-1`. Biçim `sohbet.py::_ONERI_ID_DESENI` ile AYNI. */
const KIMLIK_DESENI = /^SO-\d{8}T\d{6}Z-\d+$/;

export function sohbetKimligiMi(x: unknown): boolean {
  return typeof x === "string" && KIMLIK_DESENI.test(x);
}

/** Donuk sözlük dışını REDDEDER — tanısaydık donukluk ekranda anlamını yitirirdi. */
export function oneriTuruOku(x: unknown): SohbetOneriTuru | null {
  return typeof x === "string" && (SOHBET_ONERI_TURLERI as readonly string[]).includes(x)
    ? (x as SohbetOneriTuru)
    : null;
}

const ETIKET: Readonly<Record<SohbetOneriTuru, string>> = {
  plan_onayi: "Plan onayı önerisi",
  alarm_ack: "Alarm kapatma önerisi",
  not: "Kayıt notu",
};

export function oneriEtiketi(tur: SohbetOneriTuru | null): string {
  return tur === null ? "Tanınmayan öneri türü" : ETIKET[tur];
}

const BEKLEYEN: Readonly<Record<SohbetOneriTuru, string>> = {
  plan_onayi: "planı onayla ya da reddet — onay GERÇEK icra tetikler",
  alarm_ack: "alarmları kapat ya da reddet — onay BEKLEYEN TÜM alarmları kapatır",
  not: "kaydı kabul et ya da reddet — icrası yok, karar defterde kalır",
};

export function oneriBekleyen(tur: SohbetOneriTuru | null): string {
  return tur === null
    ? "karar ver — ama onayın NE yapacağı bu panoda ölçülemedi (tanınmayan tür)"
    : BEKLEYEN[tur];
}

const UYARI: Readonly<Record<SohbetOneriTuru, string>> = {
  plan_onayi:
    "Onay ANINDA icra eder: karar `approvals.jsonl`e yazılır VE aynı yanıt içinde mevcut plan " +
    "onay yolu koşar (api.py::_sohbet_icra → loop.operator_onay_ver) — plan işleme hazır kümeye " +
    "girer ve broker aynasına bracket emir gönderilmeye ÇALIŞILIR.",
  alarm_ack:
    "GLOBAL ETKİ: onay BEKLEYEN TÜM alarmları kapatır (api.py::_alarm_ack_uygula, ack_by=operator) " +
    "— yalnız bu satırdaki alarmı değil. Hedef alanı önerinin GEREKÇESİDİR, kapatma kapsamı değil.",
  not:
    "İCRA YOK: `not` türü bir kayıttır, yürürlüğe girecek eylem taşımaz (api.py::_sohbet_icra). " +
    "Onay da ret de sistemin davranışını DEĞİŞTİRMEZ; karar defterde durur.",
};

export function oneriUyarisi(tur: SohbetOneriTuru | null): string {
  return tur === null
    ? "Uç, bu panonun tanımadığı bir öneri türü yazdı — onayın NE yapacağı ölçülemedi. " +
        "Donuk sözlük (plan_onayi · alarm_ack · not) dışına düşen bir satır defterin elle " +
        "düzenlenmiş olabileceğini gösterir; karar vermeden önce satırı doğrula."
    : UYARI[tur];
}

/**
 * FAIL-CLOSED: yalnız `not` geri alınabilir sayılır. Tanınmayan tür de GERİ ALINAMAZ
 * kabul edilir — bilinmeyen bir etkiyi "zararsız" saymak, tam da bu deponun kapattığı
 * fail-open sınıfıdır.
 */
export function oneriGeriAlinamaz(tur: SohbetOneriTuru | null): boolean {
  return tur !== "not";
}

/** İki tık arasında okunan cümle: kimlik + hedef + ne olacağı. */
export function oneriNedir(kimlik: string, tur: SohbetOneriTuru | null, hedef: string | null): string {
  const h = hedef === null || hedef.trim() === "" ? "Hedef yok (bu tür hedef taşımıyor)" : `Hedef: ${hedef}`;
  return (
    `\`${kimlik}\` kimliğine bir karar satırı yazar (approvals.jsonl) — bu bir SOHBET ÖNERİSİDİR. ` +
    `${oneriEtiketi(tur)}. ${h}. ${oneriUyarisi(tur)}`
  );
}
