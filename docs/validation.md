# Doğrulama sonucu

Bu sürüm 18 Eylül 2026 tarihinde aşağıdaki kontrollerden geçti.

| Kontrol | Sonuç |
|---|---|
| Python birim ve entegrasyon testleri | 24/24 geçti |
| Ruff biçim ve statik kontrol | Hata yok |
| Taşınabilir firmware çekirdeği | C11, `-Wall -Wextra -Werror`; akım ve iki ark modu testleri geçti |
| TypeScript tip kontrolü | Geçti |
| Vite üretim derlemesi | Geçti |
| Canlı bildirim görünümü | SMS/WhatsApp outbox API'si web paneline bağlandı; üretim derlemesi geçti |
| FastAPI yaşam döngüsü | Başlatma, istek ve temiz kapanış geçti |
| Modbus TCP gerçek istemci okuması | Detect-only: PDU 210=4, 212=0, 1300=1; trip: 210=4, 212=1, 1300=1 |
| İki ark modu | Her iki olay risk Kritik/100; trip rölesi ve kesici sayacı yalnız açtırmalı modda |
| Bildirim akışı | İki kritik geçiş için 4 SMS/WhatsApp simülasyon kaydı |
| SQLite | WAL modu ve toplu kayıt testi geçti |
| Yarışma akım profili | XLSX satır 7-158 ile CSV'deki 152 mA/çarpan/primer üçlüsü birebir eşleşti |
| Replay ve residual | API, web telemetrisi ve Modbus özel bloğuna bağlandı; warm-up/Z-skor testleri geçti |
| 100 pano mikro benchmark | 200 adım; medyan 6,568 ms, p95 13,226 ms |
| Donanım çizimleri | 4 SVG XML olarak ayrıştırıldı ve PNG renderları görsel incelendi |
| Jüri sunumu | 12 slayt; paket ve yerleşim doğrulaması geçti, tüm slaytlar render edilip incelendi |

Benchmark değeri bu çalışma ortamına aittir; saha sunucusu kapasite veya uçtan uca gecikme garantisi değildir. Gerçek etiketli arıza verisi bulunmadığı için model başarım metrikleri ölçülmemiştir. Docker Compose dosyası sözdizimi bu ortamda Docker bulunmadığı için çalıştırılarak doğrulanmadı. Backend ve frontend kendi yerel çalışma/derleme yollarında doğrulandı.
