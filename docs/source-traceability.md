# Kaynak izlenebilirliği

İlk commit aşağıdaki yarışma girdileri incelenerek hazırlanmıştır. Kaynak dosyaların kendisi depoya kopyalanmaz; erişim sınıflandırması ve dosya sahipliği korunur.

| Kaynak | Kodda kullanılan bölüm |
|---|---|
| Grid Up Hackathon Proje Konusu.pdf | Problem, uçtan uca prototip, sentetik veri, Modbus, on-premise, bildirim ve 100 modül gereksinimleri |
| GridUp Hackathon.docx | Önceki çözüm mimarisi ve 1600 kVA AG pano odağı |
| AG Pano Teknik Çizim-1600kVA.pdf | 1600×1500×450 mm ön görünüş ve 2D SVG yerleşim oranları |
| 1600kVA AG Pano Teknik Özellikleri.pdf | 2×(100×10 mm²) bara, 2500/5 CT, 5+2 çıkış bilgisi |
| İstenen Veriler.xlsx | 100 mA/600 A örnek akım sensörü dönüşümü; ARC ve PD kaynak yönlendirmeleri |
| MPR-53CS_Modbus_Register_Map_EN.pdf | Gerilim, akım, nötr, güç, frekans ve dijital durum PDU adresleri/ölçekleri |
| DS_HFCT30_eng.pdf | HFCT 30 mm bant, hassasiyet, pC/gerilim örneği ve çalışma sıcaklığı |
| DS_HFCT50_eng.pdf | HFCT 50 mm bant, hassasiyet ve çalışma sıcaklığı |
| tvoc.pdf | TVOC-2 algılama/trip süreleri, çevre aralığı ve detektör yerleşim ilkeleri |
| 1SFC170017M0201_Rev_D_TVOC-2_Modbus_Manual.pdf | TVOC-2 Modbus ayarları, PDU/register ayrımı, trip/sensör/sistem durumu bit alanları |
| new_document-created_by_qwerpdf.docx | Önceki hibrit Python + FastAPI + React/SVG MVP kararı ve demo sırası |
| Platform jüri soru-cevapları, 15 Eylül 2026 | 24 V DC yardımcı güç; iki ark modu; Modbus/SCADA önceliği; kablosuzun opsiyonel oluşu; gerçek arıza verisi kısıtı; akım-sıcaklık-nem ve fider kapasitesi ilişkisi |

Kaynak dosyalarda bulunmayan eşikler ve ısıl parametreler [teknik temel](technical-baseline.md) içinde `model_assumption` olarak ayrılmıştır.
