# Doğrulama sonucu

Bu sürüm 15 Eylül 2026 tarihinde aşağıdaki kontrollerden geçti.

| Kontrol | Sonuç |
|---|---|
| Python birim ve entegrasyon testleri | 21/21 geçti |
| Ruff biçim ve statik kontrol | Hata yok |
| TypeScript tip kontrolü | Geçti |
| Vite üretim derlemesi | Geçti |
| FastAPI yaşam döngüsü | Başlatma, istek ve temiz kapanış geçti |
| Modbus TCP gerçek istemci okuması | Detect-only: PDU 210=4, 212=0, 1300=1; trip: 210=4, 212=1, 1300=1 |
| İki ark modu | Her iki olay risk Kritik/100; trip rölesi ve kesici sayacı yalnız açtırmalı modda |
| Bildirim akışı | İki kritik geçiş için 4 SMS/WhatsApp simülasyon kaydı |
| SQLite | WAL modu ve toplu kayıt testi geçti |
| 100 pano mikro benchmark | 200 adım; medyan 4,744 ms, p95 13,909 ms |

Benchmark değeri bu çalışma ortamına aittir; saha sunucusu kapasite veya uçtan uca gecikme garantisi değildir. Gerçek etiketli arıza verisi bulunmadığı için model başarım metrikleri ölçülmemiştir. Docker Compose dosyası sözdizimi bu ortamda Docker bulunmadığı için çalıştırılarak doğrulanmadı. Backend ve frontend kendi yerel çalışma/derleme yollarında doğrulandı.
