/* ============================================================================
   KİMLİK EKSENİ — API GÖVDE TİPLERİ (`/api/session` + `/api/summary.ladder`)
   ----------------------------------------------------------------------------
   HER ALAN İSTEĞE BAĞLI ve bu bilerek (pano/tipler.ts sözleşmesinin aynısı):
   `x?: T` = "alan HİÇ gelmedi", `x: T | null` = "ölçüldü, sonuç yok". İkisini
   birleştirip varsayılan vermek, ölçülmemiş bir yetkiyi ölçülmüş göstermek olurdu
   — ve burada ölçülen şey YETKİDİR, yani en pahalı yalan sınıfı.

   `/api/session` bu deponun TEK yetkisiz /api ucu (api.py:1367) ve döndürdüğü üç
   alan, sistemin kimlik hakkında bildiği HER ŞEYDİR: oturum geçerli mi, parola
   kurulu mu, çerez Secure mi. Ad yok, e-posta yok, kullanıcı kimliği yok —
   `state/auth.json` yalnız `{salt, hash}` tutuyor (meridian/auth.py:150-152).
   ============================================================================ */

/** `GET /api/session` — açık uç; panonun açılışta sorduğu tek soru. */
export interface OturumGovdesi {
  readonly authenticated?: boolean;
  readonly password_set?: boolean;
  /** Çerez `Secure` işaretlenecek mi — yani bağlantı TLS üstünde mi. */
  readonly tls?: boolean;
}

/** `/api/summary.ladder.levels[]` — L0/L1/L2, adları `analytics.autonomy_ladder`ta yazılı. */
export interface MerdivenSeviyesi {
  readonly id?: string;
  readonly name?: string;
  readonly active?: boolean;
}

/** `/api/summary.ladder.l0_to_l1[]` — terfi ölçütü. `manual` = operatör/altyapı adımı. */
export interface MerdivenOlcutu {
  readonly label?: string;
  readonly met?: boolean;
  readonly detail?: string;
  readonly manual?: boolean;
}

export interface Merdiven {
  readonly current_level?: number;
  readonly levels?: readonly MerdivenSeviyesi[];
  readonly l0_to_l1?: readonly MerdivenOlcutu[];
  /** Yalnız OTOMATİK ölçütlerin sayacı — elle adımlar paydanın dışında (analytics.py:226-227). */
  readonly auto_progress?: { readonly met?: number; readonly total?: number };
}

/** `GET /api/summary` — bu yüzeyin okuduğu tek blok `ladder`; gerisi başka yüzeylerin. */
export interface OzetGovdesi {
  readonly mode?: string;
  readonly autonomy_level?: number | string | null;
  readonly ladder?: Merdiven;
}
