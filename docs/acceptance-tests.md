# MVP deney ve kabul ölçütleri

Bu tablo yazılım doğrulaması ile cihaz/saha doğrulamasını ayırır. Yarışma kaynakları sayısal yazılım toleransı vermediği yerde ölçüt “MVP demo kabulü” olarak belirtilmiştir.

| Test | Girdi | Kabul ölçütü | Tür |
|---|---|---|---|
| 1600 kVA anma akımı | 1,6 MVA, 400 V | `2309,401 A`, bağıl hata ≤10⁻⁶ | Türetilmiş fizik kontrolü |
| Excel sensör dönüşümü | 100 mA, 600/100 oranı | 600 A; 53 mA için 318 A | Kaynak veri kontrolü |
| Paralel bara kesiti | 2×100×10 mm² | Toplam 0,002 m² | Kaynak/geometri kontrolü |
| Isıl yön | Akım var/yok | Yük altında sıcaklık artar; yüksüz sıcak bara soğur | Fiziksel değişmez |
| Dengeli faz nötrü | 100/100/100 A | Hesaplanan temel bileşen nötr akımı ≈0 A | Fazör kontrolü |
| Normal senaryo | Varsayılan profil | Kritik durum ve TVOC trip oluşmaz | MVP demo kabulü |
| Gevşek temas | L1 temas direnci rampası | L1 ölçülen-beklenen sıcaklık artığı >10 K ve `THERMAL_RESIDUAL` bulgusu | MVP demo kabulü |
| Nem girişi | RH→%95, soğuk yüzey offseti→−2 K | Çiy noktası marjı <3 K ve çevre bulgusu oluşur | MVP demo kabulü |
| HFCT aktivitesi | Bağımsız sentetik PD rampası | >53,33 pC seviyesinde `HFCT_INDICATOR` tetiklenir | Model iç tutarlılık kontrolü |
| Yalnız algılamalı ark | TVOC detektör 3 aktif, röle pasif | PDU 210 bit2=1, PDU 212=0, PDU 1300 bit0=1, risk=100/Kritik | Kaynak register + jüri cevabı |
| Kesici açtırmalı ark | TVOC detektör 3 ve K4 aktif | PDU 210 bit2=1, PDU 212 bit0=1, PDU 1300 bit0=1, risk=100/Kritik | Kaynak register + jüri cevabı |
| Yarışma verisi replay | CSV'nin ilk satırı etkin | 53 mA × 6000 / 1000 = 318 A; profil 152 nokta | İstenen Veriler.xlsx |
| Replay zaman ekseni | Profil son satırı | indeks 151, geçen süre 2265 dakika, saat 13:45 | İstenen Veriler.xlsx |
| Residual ısınma | ≥12 normal örnek sonrası gevşek temas | Z-skoru ve istatistiksel skor yükselir; fiziksel artık riskte görünür | Açıklanabilir demo kuralı |
| Risk seyrelmeme | Tek uzman skoru ≥80, diğerleri düşük | Birleşik skor en yüksek tekil skorun altına düşmez | Güvenlik değişmezi |
| Fider nominal aşımı | Aktif fider akımı >400 A | `FEEDER_OVERLOAD` ve yük oranı >1 | Jüri cevabı + seçili DSYA varyantı |
| MPR akım round-trip | PDU 6, CT=500 | Çözülen değer ile simülasyon farkı ≤0,25 A | Kaynak ölçek kontrolü |
| 100 modül ölçeği | 100 pano, bir simülasyon adımı | 100 benzersiz snapshot ve Modbus unit ID 1–200 | Yarışma gereksinimi |
| Bildirim | Uyarı/Kritik seviyeye yükselme | Bir sonraki backend çevriminde SMS ve WhatsApp simüle outbox kaydı | MVP demo kabulü |
| SQLite eşzamanlılık | Veritabanı başlatma | `journal_mode=WAL`, toplu telemetri/bildirim yazımı | Yazılım dayanıklılığı |

## Zamanlama sınırı

TVOC-2 veri sayfasındaki yaklaşık 1 ms trip, 10 ms’den kısa gösterim ve 0,4 ms’den kısa current-condition aktarımı cihaz özellikleridir. Bu MVP, işletim sistemi üzerinde çalışan Python/WebSocket katmanıyla bu donanım sürelerini sert gerçek zaman testi olarak doğrulamaz. Jüri raporlama gecikmesi için sayısal üst sınır vermemiştir. Geçici yazılım kabulü, ark durumunun en geç bir sonraki yapılandırılmış çevrimde SCADA ve bildirim katmanına yansımasıdır; varsayılan demo çevrimi 1 saniyedir.

## Veri doğrulama sınırı

Gerçek etiketli arıza kayıtları gizlilik nedeniyle paylaşılmamıştır. Bu nedenle mevcut
testler fizik değişmezlerini, senaryo ayrışmasını ve veri taşıma sözleşmesini doğrular;
model duyarlılığı, özgüllüğü, precision/recall veya F1 skoru ölçmez.

## Çalıştırma

```bash
pytest
PYTHONPATH=backend python scripts/benchmark_100_panels.py
```
