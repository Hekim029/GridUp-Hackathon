# Yazılım mimarisi ve çalışma akışı

## Katmanlar

```mermaid
flowchart TB
    A["Sensörler ve mevcut cihazlar"] --> B["Saha modülü veya simülatör"]
    B --> C["Modbus RTU TCP eşleme"]
    C --> D["FastAPI veri ve risk servisi"]
    D --> E["SQLite olay geçmişi"]
    D --> F["Mevcut SCADA"]
    D --> G["Opsiyonel demo ekranı"]
    D --> H["SMS WhatsApp outbox"]
```

Koruma kararı yerel TVOC-2 üzerinde kalır. Merkezi yazılım arkın algılandığını ve trip
rölesinin çalışıp çalışmadığını ayrı alanlarda taşır.

## Bir çevrimin çalışma sırası

```mermaid
flowchart TD
    S["Zaman adımını başlat"] --> R["Senaryo ve fizik modelini güncelle"]
    R --> T["Telemetri üret"]
    T --> X["Üç uzman bulguyu hesapla"]
    X --> O["Maksimumu koruyan risk birleştirme"]
    O --> M["Modbus registerlarını güncelle"]
    M --> P["SQLite toplu kayıt"]
    P --> N{"Seviye yükseldi mi"}
    N -->|Evet| A["SMS WhatsApp outbox ve canlı log"]
    N -->|Hayır| W["Sonraki çevrimi bekle"]
    A --> W
```

## Uzman modüller

| Modül | Girdiler | Başlıca çıktılar |
|---|---|---|
| Termal ve yük | Faz akımı, fider nominali, ölçülen/beklenen sıcaklık | aşırı yük, dengesizlik, termal artık |
| Çevre ve izolasyon | ortam sıcaklığı, nem, en soğuk yüzey | çiy noktası ve yoğuşma marjı |
| Dielektrik güvenlik | HFCT göstergesi, TVOC detektör/röle | PD aktivite göstergesi, detect-only, trip |

En yüksek tekil risk skoru birleşik skorda korunur. Diğer bulgular yalnız yukarı yönlü sınırlı
katkı sağlar. Bu kural, kritik bir termal bulgunun normal çevresel değerlerle seyrelmesini önler.

## Kaynak kodu eşlemesi

| İşlev | Dosya |
|---|---|
| Fizik ve çevre denklemleri | `backend/gridup/physics.py` |
| Senaryo motoru | `backend/gridup/simulator.py` |
| Uzman kuralları ve risk | `backend/gridup/risk.py` |
| Modbus kaynak ve özel blok | `backend/gridup/modbus.py` |
| REST, WebSocket, yaşam döngüsü | `backend/gridup/api.py` |
| WAL, toplu kayıt ve outbox | `backend/gridup/repository.py` |
| 2D pano ve demo kontrolü | `frontend/src/` |
| Taşınabilir MCU mantık çekirdeği | `firmware/` |
