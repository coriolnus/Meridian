/* ============================================================================
   YAZAN İSTEKLER — kimlik kapısının dört ucu (`veri.ts` yalnız OKUYOR)
   ----------------------------------------------------------------------------
   `veri.ts::apiGet` bu panonun tek okuma kapısı ve BİLEREK yalnız GET yapıyor.
   Kimlik kapısı ise üç POST istiyor (`/api/login`, `/api/setup-password`,
   `/api/logout`) ve bunların hata yüzeyi bir GET'inkinden BAŞKA: burada 401
   "oturum düştü" DEĞİL "parola hatalı"dır, 409 "kurulum zaten yapılmış"tır ve
   429 "kaba-kuvvet kilidi"dir. Üçünü tek bir `hata: string` alanına ezmek,
   operatöre yanlış işi yaptırırdı (yeniden giriş / kabuktan sıfırlama / bekleme
   — üç ayrı çare).

   BU YÜZDEN DÖNÜŞ HTTP KODUNU TAŞIR. Çağıran koda göre dallanır; metni uydurmaz,
   sunucunun `detail`ini basar. Kod okunamadıysa (ağ düştü) `kod: 0` döner ve bu
   "sunucu bir şey söyledi" hâlinden AYRI durur — 0 bir HTTP kodu değildir, tam da
   bu yüzden seçildi.

   ÖLÇÜLEN SÖZLEŞME (`meridian/api.py`, okundu — tahmin değil):
     · POST /api/login          gövde {"password": str} → 200 {ok, expires_in}
                                401 {detail:"parola hatalı"} · 429 {detail:"cok fazla deneme — N sn sonra"}
     · POST /api/setup-password gövde {"password": str} → 200 {ok}
                                409 {detail:"parola zaten kurulu"} · 400 {detail:<ValueError metni>}
     · POST /api/logout         gövde YOK → 200 {ok:true}; yetki İSTEMEZ

   TANIM ARTIK `pano/gonder.ts`TE (genel yazma kapısı, `veri.ts`nin yazan
   kardeşi — tek-kaynak yasası, CLAUDE.md §4). BU DOSYA yalnız yukarıdaki
   sözleşme dokümantasyonunu taşır (o kimlik yüzeyinin bilgisidir, genel
   kapının değil) ve bir GEÇİŞ YÜZEYİdir: Giris.tsx, GirisFormu, KurulumFormu,
   SirGirisi buradan almaya devam edebilir.
   ============================================================================ */

export { apiPost, type GonderSonucu } from "../../gonder";
