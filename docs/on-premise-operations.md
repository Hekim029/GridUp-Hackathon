# On-premise kurulum ve işletim yaklaşımı

## Dağıtım modeli

Uygulama FastAPI backend, React statik arayüz ve yerel SQLite veritabanından oluşur. Docker
Compose tek bir şirket içi sunucuda tekrarlanabilir kurulum sağlar. Modbus TCP hizmeti ve web
uygulaması kurum ağı içinde çalışır; Public Cloud bağımlılığı yoktur.

| Bileşen | Görev | Kalıcılık |
|---|---|---|
| Backend | simülasyon, risk, REST, WebSocket, Modbus | uygulama paketi |
| Frontend | opsiyonel demo ve mühendislik görünümü | statik dosyalar |
| SQLite | telemetri, alarm ve bildirim outbox | yerel disk/volume |
| SCADA | ana operasyon görünümü | kurumun mevcut sistemi |
| Bildirim geçidi | SMS/WhatsApp aktarımı | kurum içi veya onaylı ağ geçidi |

## İşletim kontrolleri

- Ortam değişkenleriyle pano sayısı, çevrim, veritabanı yolu ve Modbus portu belirlenir.
- `/health` servis durumu ve panel sayısını döndürür.
- Uygulama kapanırken simülasyon ve Modbus görevleri kontrollü sonlandırılır.
- Kritik seviye yükselmesi veritabanı outbox kaydı ve uygulama logu üretir.
- Yedekleme kapsamı SQLite ana dosyası ile WAL/SHM tutarlılığını koruyacak kurum prosedürüne
  bağlanmalıdır.

## Kurum entegrasyonunda tamamlanacaklar

Kullanıcı hesapları, ağ segmenti, TLS/sertifika, zaman sunucusu, log saklama süresi, yedekleme,
SMS/WhatsApp sağlayıcısı ve alarm alıcı listesi yarışma kaynaklarında tanımlanmamıştır. Bunlar
kurum güvenlik ve işletim politikasıyla belirlenir. MVP bunlar için sahte kimlik bilgisi veya
Public Cloud servisi eklemez.
