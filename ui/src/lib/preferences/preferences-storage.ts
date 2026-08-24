"use client";

import { setClientCookie } from "../cookie.client";
import { setLocalStorageValue } from "../local-storage.client";
import {
  getPreferencePersistence,
  type PreferenceKey,
  type PreferencePersistence,
  type PreferenceValueMap,
} from "./preferences-config";

async function persistByMode(mode: PreferencePersistence, key: string, value: string): Promise<void> {
  switch (mode) {
    case "none":
      return;

    case "client-cookie":
      setClientCookie(key, value);
      return;

    // SUNUCU EYLEMİ YOK: şablonun bu dalı bir Next Server Action'a gidiyordu.
    // Bu uygulamada sunucu React render etmiyor (FastAPI statik dosya sunuyor),
    // yani "sunucu çerezi" ile "istemci çerezi" arasında GERÇEK bir fark kalmadı —
    // ikisi de aynı `document.cookie`e yazar. Dal SİLİNMEDİ ki tercih kaydındaki
    // `server-cookie` değeri sessizce hiçbir şey yapmasın; istemciye düşüyor.
    case "server-cookie":
      setClientCookie(key, value);
      return;

    case "localStorage":
      setLocalStorageValue(key, value);
      return;
  }
}

export function persistPreference<K extends PreferenceKey>(key: K, value: PreferenceValueMap[K]): Promise<void> {
  return persistByMode(getPreferencePersistence(key), key, value);
}
