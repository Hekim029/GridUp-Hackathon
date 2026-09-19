# Yarışma teslim uygunluk matrisi

Bu matris, `Grid Up Hackathon Proje Konusu.pdf` içindeki yedi teknik çıktı ile sunum ve
demo beklentilerini mevcut teslimlere bağlar. `Tamamlandı` hackathon prototip kapsamını
ifade eder; saha sertifikasyonu veya enerjili pano kurulumu anlamına gelmez.

| No | Beklenen çıktı | Durum | Kanıt / teslim | Saha öncesi kalan |
|---:|---|---|---|---|
| 1 | Kabin içi fiziksel modül / prototip | Tamamlandı | `physical-module-design.md`, pano yerleşim SVG'si | Enerjisiz keşif, kesin ölçü ve muhafaza seçimi |
| 2 | Elektronik tasarım dokümantasyonu | Tamamlandı, konsept seviye | `electronic-design.md`, blok şema, PCB yerleşim konsepti, `bom.csv` | Şematik/PCB CAD, üretim dosyaları ve uygunluk testleri |
| 3 | Yazılım mimarisi ve kaynak kod | Tamamlandı | FastAPI, React, 152 noktalık yarışma verisi replay, fizik-artık Z-skoru, Modbus sunucu, `software-architecture.md`; taşınabilir firmware çekirdeği | Seçilecek MCU'ya özel HAL sürücüleri |
| 4 | Monitoring, SCADA, on-premise, alarm | Tamamlandı | Web izleme, Modbus haritası, SQLite, bildirim paneli ve outbox | Gerçek ADM/GDZ SCADA ve mesaj geçidi kabul testi |
| 5 | En az 100 modül ve kaynak kullanımı | Tamamlandı | 100 pano benchmark ve `scalability-and-cost.md` | Hedef saha sunucusunda uzun süreli yük testi |
| 6 | Public Cloud içermeyen özel altyapı | Tamamlandı | Docker Compose, yerel veritabanı, `on-premise-operations.md` | Kurum ağ, yedekleme ve erişim politikalarının uygulanması |
| 7 | Alarm ve acil bildirim | Tamamlandı, simüle | SMS/WhatsApp outbox, canlı log, API ve web bildirim paneli | Gerçek sağlayıcı kimliği ve alıcı listesi |
| Demo | Fiziksel modül, veri akışı, SCADA, senaryo, alarm, mimari, ölçek | Tamamlandı | `demo-runbook.md` ve final jüri sunumu | Ekip provası ve demo bilgisayarında kurulum |

## Kaynakta zorunlu olmayanlar

- Gerçek sensör, endüstriyel ekipman satın alma veya gerçek panoda kurulum zorunlu değildir.
- Tüm veri türlerini kullanmak zorunlu değildir.
- Gerçek RTU/SCADA bağlantısı yerine Modbus haritalama yaklaşımı yeterlidir.
- Mikrodenetleyici kaynak kodu yalnız mikrodenetleyici kullanılması durumunda istenir.
- Dashboard jüri cevabına göre zorunlu değildir; demo görünürlüğü için projede tutulmuştur.
- Kablosuz iletişim zorunlu değildir; jüri bunu artı değer olarak tanımlamıştır.

## Tamamlanmış sayılmayan saha işleri

Hackathon teslimi ile saha ürünü birbirinden ayrılmalıdır. Gerçek etiketli arıza verisi,
enerjili pano testi, elektronik kart üretimi, koruma koordinasyonu, EMC/izolasyon doğrulaması,
ürün sertifikasyonu ve kurum kabulü bu projenin mevcut kanıtları arasında değildir. Sunumda
bu maddeler tamamlanmış gibi anlatılmamalıdır.
