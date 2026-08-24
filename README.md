# KeyBrox_TR — Instagram Otomatik Yayın

Günde iki kez (11:00 ve 19:00 Türkiye saati) sıradaki içerik setini Instagram'a yayınlar:
**1 carousel gönderi + 3 karelik hikaye.** Kuyrukta **12 set** var.

GitHub'ın sunucularında çalışır — bilgisayarın kapalı olabilir.

## Kuyruk

| Set | Seri | Konu |
|---|---|---|
| 1–9 | Tanıtım | KeyBrox lansmanı — platformun tamamı |
| 10 | Danışman & Ofis | Emeğin görünsün *(danışman)* |
| 11 | Danışman & Ofis | Ofisin tamamı tek panelde *(broker)* |
| 12 | Danışman & Ofis | Büyük oyuncuların araçları *(medya + AI)* |

Set 10–12'nin gönderi metinleri ve hikaye çıkartma notları → `METINLER.md`.
Görseller `_motor/keybrox-motor.mjs` ile üretilir; metni değiştirip motoru yeniden
çalıştırmak yeterlidir (bkz. `../../_motor/`).

**Günde bir gönderi istersen** `.github/workflows/yayinla.yml` içindeki
`- cron: '0 16 * * *'` satırını sil — yalnız 11:00 kalır.

---

## Ne nerede

| Dosya | İşi |
|---|---|
| `media/post/NN/` | Gönderi kareleri (JPEG, 1080×1350) |
| `media/story/NN/` | Hikaye kareleri (JPEG, 1080×1920) |
| `icerik.json` | Her setin görselleri ve açıklama metni |
| `state/durum.json` | Sıradaki set numarası + yayın kaydı |
| `publish.py` | Yayınlama betiği |
| `.github/workflows/yayinla.yml` | Zamanlama |

Aynı set asla iki kez yayınlanmaz: yayın başarılı olunca `durum.json` içindeki
`sonraki` bir artar ve depoya geri yazılır. Yayın başarısız olursa sayaç ilerlemez,
bir sonraki slotta aynı set tekrar denenir.

---

## Kurulum — bir kereye mahsus

### 1. Depoyu GitHub'a yükle

Depo **herkese açık (public)** olmalı. Meta, görselleri açık bir adresten indirmek
zorunda; kapalı depoda görseller görünmez ve yayın başarısız olur.

### 2. Meta erişim anahtarını üret

Facebook sayfasına **gerek yok** — "Instagram Login" yöntemi doğrudan Instagram
profesyonel hesabıyla çalışıyor.

1. `developers.facebook.com` → sağ üstten **My Apps** → **Create App**
2. Uygulama türü sorulduğunda **Other** → **Business** seç, bir isim ver.
3. Uygulama panelinde **Add products** → **Instagram** → **Set up**
4. Sol menüden **Instagram** → **API setup with Instagram login**
5. **1. adım: Generate access token** → Instagram hesabını ekle, giriş yap, izinleri onayla.
   - İstenen izin: `instagram_business_content_publish` ve `instagram_business_basic`
6. Ekranda çıkan **erişim anahtarını** ve **Instagram user ID** değerini kopyala.

Anahtar **60 gün** geçerli. 9 setlik seri 5 günde biteceği için bu fazlasıyla yeterli;
ama seriyi ileride tekrarlarsan anahtarı yenilemen gerekir.

### 3. Anahtarları GitHub'a gizli olarak gir

Depoda **Settings** → **Secrets and variables** → **Actions** → **New repository secret**:

| İsim | Değer |
|---|---|
| `IG_ACCESS_TOKEN` | 5. adımdaki erişim anahtarı |
| `IG_USER_ID` | Instagram user ID |

Bu değerler GitHub'da şifreli durur, kayıtlarda görünmez.

### 4. Deneme çalıştır

**Actions** sekmesi → **KeyBrox Instagram yayin** → **Run workflow** →
`Deneme modu` **açık** bırak → çalıştır.

Kayıtta 1 numaralı setin görsel adreslerini görürsün ama hiçbir şey yayınlanmaz.
Adresler doğru görünüyorsa aynı adımı `Deneme modu` **kapalı** olarak tekrarla —
ilk gerçek gönderi yayınlanır.

Bu andan sonra sistem kendi kendine 11:00 ve 19:00'da çalışır.

---

## Bilinmesi gerekenler

- **Hikaye çıkartmaları eklenemez.** Bağlantı, anket, geri sayım çıkartmalarını
  Meta'nın API'si desteklemiyor. `KeyBrox_TR/Hikayeler/*/hikaye-notlari.txt`
  dosyalarındaki öneriler duruyor; çıkartmaları yayından sonra elle ekleyebilirsin.
- **Saatler tam dakikasında olmayabilir.** GitHub zamanlayıcısı yoğunluğa göre
  5–20 dakika gecikebilir. Gönderi saatinin dakikası kritikse elle çalıştır.
- **Meta günde 100 yayın izni veriyor**, biz 2 kullanıyoruz.
- **Görseller JPEG.** Meta yalnızca JPEG kabul ediyor; kaynak PNG'ler dönüştürüldü,
  orijinaller ana klasörde duruyor.
- **Seri bitince** iş kendiliğinden durur; `durum.json` içindeki `sonraki` değeri
  9'u geçtiğinde betik hiçbir şey yapmadan çıkar.
