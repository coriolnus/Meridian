# Meridian — Oracle Cloud dağıtımı

Bu dosya panoyu genel bir IP'ye çıkarmadan önce yapılması gerekenleri sırayla anlatır.
**Sıra önemli:** TLS kurulmadan giriş ekranı eklemek parolayı açık metin gönderir.

---

## Tehdit modeli — neyi koruyoruz

Pano şunları yapabilir: hesap durumunu ve pozisyonları okumak, API anahtarlarının varlığını
görmek, **HALT / DEVAM**, **tüm pozisyonları kapatmak (Flatten)**, strateji mutasyonu tetiklemek.

Yerelde tek koruma `--host 127.0.0.1` idi. Genel bir IP'de o koruma yoktur. Bu yüzden:

| Katman | Ne yapar |
|---|---|
| Caddy + Let's Encrypt | Trafiği şifreler; parola ve oturum çerezi ağda açık gitmez |
| Oracle Security List | 80/443 dışında her şey kapalı; **8080 asla açılmaz** |
| uvicorn 127.0.0.1'de | Pano internete doğrudan hiç bağlanmaz, yalnız vekil erişir |
| `meridian.auth` | Parola (scrypt) + imzalı HttpOnly oturum çerezi |
| `api._auth` | Oturumsuz her `/api/*` isteği 401 |
| Açılış reddi | Loopback dışına parolasız bağlanma denenirse süreç açılmaz |

---

## 1 · Parolayı kur (dağıtımdan ÖNCE)

```bash
.venv/bin/python -m meridian.auth_cli set
```

En az 12 karakter. Parola diskte düz durmaz — `state/auth.json` içinde scrypt türetmesi olarak
tutulur, dosya 0600.

Durumu her zaman kontrol edebilirsin:

```bash
.venv/bin/python -m meridian.auth_cli status
```

Parolayı unutursan web üzerinden sıfırlama **yoktur** — bilinçli. Tek yol sunucuda yukarıdaki
`set` komutu. "Parolamı unuttum" akışı tek operatörlü bir sistemde saldırgan için ikinci bir kapı
olmaktan başka bir işe yaramaz.

Parola sızdığından şüpheleniyorsan parolayı değiştirmek **tek başına yetmez** — açık oturum
çerezleri geçerli kalır:

```bash
.venv/bin/python -m meridian.auth_cli logout-all   # imza anahtarını döndürür, tüm oturumlar düşer
```

---

## 2 · Dosya izinleri

```bash
chmod 600 state/auth.json state/secrets.json
chmod 700 state
ls -l state/auth.json state/secrets.json     # ikisi de -rw------- olmalı
```

`secrets.json` broker ve LLM anahtarlarını taşır. `auth.json` parola türetmesini ve oturum imza
anahtarını taşır — **o dosyayı okuyabilen biri kendine geçerli bir oturum üretebilir**, parolayı
bilmeden. İzin buranın tek savunması.

---

## 3 · Caddy (TLS)

`deploy/Caddyfile` içindeki `meridian.ORNEK-ALAN-ADIN.com` ve e-posta alanlarını doldur, sonra:

```bash
sudo cp deploy/Caddyfile /etc/caddy/Caddyfile && sudo systemctl reload caddy
```

**Alan adı şart.** Caddy çıplak bir IP için Let's Encrypt sertifikası alamaz. Alternatif
`tls internal`'dir ama o zaman tarayıcı her seferinde uyarı verir ve o uyarıyı tıklayıp geçme
alışkanlığı, gerçek bir ortadaki-adam saldırısını fark etme yeteneğini kalıcı olarak yok eder.

---

## 4 · Güvenlik duvarı

Oracle'da **iki** katman var ve ikisi de kapalı olmalı:

```bash
# 1) Konsol: VCN → Security List → Ingress
#    izin ver: 0.0.0.0/0 → TCP 80, 443
#    KALDIR : varsayılan gelen kuralların geri kalanı (özellikle 22'yi kendi IP'nle sınırla)
# 2) VM'in kendi iptables'ı (Oracle imajları kapalı gelir, açman gerekir):
sudo iptables -I INPUT -p tcp --dport 80  -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save
```

**8080'i asla açma.** Vekil aynı makinede, loopback üzerinden konuşuyor.

Doğrula — dışarıdan 8080 kapalı olmalı:

```bash
# başka bir makineden:
curl -m 5 http://VM_IP:8080/api/today     # bağlantı reddedilmeli / zaman aşımına uğramalı
curl -m 5 https://alan-adin/api/today     # 401 dönmeli (kimlik yok), 200 DEĞİL
```

---

## 5 · Başlat

`serve.sh` panoyu 127.0.0.1'de tutar; değiştirmene gerek yok. Bağlanma adresini yine de değiştirmek
istersen `MERIDIAN_BIND_HOST` ile yapılır ve parola kurulu değilse **süreç açılmayı reddeder**:

```
GÜVENLİK: pano loopback DIŞINDA bir arayüze bağlanıyor (0.0.0.0) ama operatör parolası
kurulu değil. Hesap durumu, HALT/DEVAM ve Flatten yüzeyi yetkisiz açık olurdu.
```

Bu bir uyarı değil, bir ret. Önceki hal `obs.warn` idi — ve uyarılar okunmaz.

---

## 6 · Dağıtım sonrası doğrulama listesi

```bash
D=https://alan-adin
curl -s -o /dev/null -w "%{http_code}\n" $D/api/today            # 401
curl -s -o /dev/null -w "%{http_code}\n" $D/api/today?token=x    # 401  (URL token'ı kaldırıldı)
curl -s -o /dev/null -w "%{http_code}\n" $D/                     # 200  (giriş ekranı)
curl -s -o /dev/null -w "%{http_code}\n" $D/healthz              # 200
curl -sI $D | grep -i 'strict-transport\|content-security\|x-frame'   # üçü de olmalı
curl -s -o /dev/null -w "%{http_code}\n" http://alan-adin/       # 308 → https
```

Giriş kilidini de dene: yanlış parolayla 9 kez POST at, 9.'da **429** ve kalan süre dönmeli.

---

## Bilerek açık bırakılanlar

| Yol | Neden |
|---|---|
| `GET /` `/landing` `/workflow` `/halt` | Statik sayfalar. `/` giriş ekranını servis eder; veri taşımaz. |
| `GET /healthz` | Vekil ve izleme sağlık kontrolü. |
| `GET /api/public/summary` | Tanıtım sayfası için **kasten** açık. Yalnız araştırma toplamları (hipotez sayıları, kurulum×rejim matrisi). Sermaye, pozisyon, hisse adı, broker ve anahtar **dışarı verilmez**. Bunu da kapatmak istersen `api.py` içinde `_auth(request)` eklemen yeter — ama o zaman `landing.html` canlı veriyi kaybeder ve uydurma rakama düşmemek için boş kalır. |

---

## Kapsam dışı — bilmen gerekenler

- **Tek parola, tek operatör.** Rol, kullanıcı listesi, denetim izi yok. Sistem tek kişilik
  tasarlandı; çok kullanıcılı hale gelirse bu katman yeniden yazılmalı.
- **Hız sınırı süreç-içi.** Tek uvicorn süreci için doğru. Yatay ölçeklenirse paylaşımlı bir
  depoya (Redis) taşınmalı.
- **İki faktör yok.** Parola + oturum çerezi seçildi. TOTP eklemek `meridian/auth.py` içinde
  ayrı bir doğrulama adımı demek; broker hesabına bakan bir yüzey için düşünmeye değer.
- **CSP `style-src` içinde `unsafe-inline` var.** `app.js` DOM'u satır içi stil taşıyan şablon
  dizgileriyle üretiyor; kaldırmak app.js'in yeniden yazılması demek. `script-src` temiz —
  asıl koruma orada.
