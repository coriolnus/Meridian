/* Uygulama kimliği. Şablonun `packageJson.version` okuması DÜŞTÜ: Meridian'ın
   sürümü `ui/package.json`da değil, canlı nabızda yaşıyor (`heartbeat.version`)
   ve ikisini aynı ada bağlamak, arayüz paketinin sürümünü strateji sürümü diye
   okutan sessiz bir yanlış üretirdi. */
export const APP_CONFIG = {
  name: "Meridian",
  meta: {
    title: "Meridian — pano",
    description: "Algoritmik işlem sisteminin operatör panosu.",
  },
};
