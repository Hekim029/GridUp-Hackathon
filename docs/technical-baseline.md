# Teknik temel ve model sınırları

## Kaynakla doğrulanan pano modeli

| Parametre | Değer | Sınıf | Dayanak |
|---|---:|---|---|
| Görünür güç | 1600 kVA | source | 1600kVA AG Pano Teknik Özellikleri.pdf |
| Hat gerilimi | 400 V | source/plan | Yarışma pano odağı ve önceki teknik plan |
| Hesaplanan anma akımı | 2309,4 A | derived | `I = S / (√3 U_LL)` |
| Ana bara | 2×(100×10 mm²) | source | 1600kVA AG Pano Teknik Özellikleri.pdf |
| Akım trafosu | 2500/5 | source | 1600kVA AG Pano Teknik Özellikleri.pdf |
| Pano ölçüleri | 1600×1500×450 mm | source | AG Pano Teknik Çizim-1600kVA.pdf |
| Besleme çıkışı | 5 + 2 yedek | source | 1600kVA AG Pano Teknik Özellikleri.pdf |
| Seçili DSYA varyantı | 400 A | source/model selection | Teknik tabloda 250 A ve 400 A seçenekleri; MVP 400 A'yı seçer |
| Örnek sensör dönüşümü | 100 mA → 600 A | source | İstenen Veriler.xlsx |
| Yarışma akım profili | 152 nokta, 15 dakika, 90-540 A | source | İstenen Veriler.xlsx / `Akım Sensörü`, satır 7-158 |
| Yardımcı güç | 24 V DC | jury_answer | Modem beslemesi için panoda mevcut olduğu doğrulandı |

## Fizik modeli

Üç faz anma akımı:

`I_rated = S / (√3 U_LL)`

Bakır baranın sıcaklığa bağlı direnci:

`R_b(T) = ρ20 [1 + α(T - 20)] L / A`

Toplam elektriksel direnç ve Joule kaybı:

`R_e = R_b + R_contact`

`P_loss = I_RMS² R_e`

Birinci dereceden ısıl model:

`C_th dT/dt = I_RMS² R_e - (T - T_ambient) / R_th`

Nem ve çiy noktası:

`e_s = 6.112 exp(17.67 T / (243.5 + T))`

`e = RH e_s / 100`

`T_dew = 243.5 ln(e / 6.112) / (17.67 - ln(e / 6.112))`

`M = T_cold_surface - T_dew`

Fazlar 120° aralıklı kabul edilerek temel bileşen nötr akımı fazör toplamından hesaplanır. Harmonik nötr akımı bu ilk sürümün kapsamına dahil değildir.

## Kaynak cihaz özellikleri

- HFCT 30 mm: 1–60 MHz bant genişliği, 42 MHz/50 Ω koşulunda 17 mV/mA azami hassasiyet, PD frekansında 100 pC için 0,4 Vpp, −20…+70 °C çalışma sıcaklığı.
- HFCT 50 mm: 1–80 MHz bant genişliği, 42 MHz/50 Ω koşulunda 17 mV/mA azami hassasiyet, −20…+70 °C çalışma sıcaklığı.
- TVOC-2: ışık algılamadan K4/K5/K6 trip çıkışına yaklaşık 1 ms; gösterim 10 ms’den kısa; current-condition girişinden çıkışına 0,4 ms’den kısa. Bunlar cihaz veri sayfası özellikleridir.
- TVOC-2 Modbus: 03/04 okuma, 06/16 yazma fonksiyonları; PDU adresi ile dokümandaki register numarası arasında `register = PDU + 1` ilişkisi.

## Kalibrasyon gerektiren varsayımlar

Yarışma dosyaları aşağıdaki sayıları vermediği için kod bunları açıkça `model_assumption` olarak taşır:

| Parametre | İlk demo değeri | Neden geçici |
|---|---:|---|
| Etkin ısınan iletken uzunluğu | 1,0 m | Gerçek akım yolu/ek geometrisi verilmedi |
| Normal temas direnci | 2 µΩ | Saha mikro-ohm ölçümü yok |
| Gevşek temas hedef direnci | 80 µΩ | Arıza örneği için senaryo parametresi |
| Isıl kapasite | 15 kJ/K | Eklem ve çevresinin etkin kütlesi bilinmiyor |
| Isıl direnç | 0,15 K/W | Pano hava akışı/kurulum verisi yok |
| Risk bantları | 25/55/80 | Yarışma girdilerinde kabul eşiği tanımlanmamış |
| Yoğuşma izleme/uyarı bandı | 10 K / 3 K | Demo kuralı; gerçek saha kabul eşiği değil |
| Simülasyon zaman hızı | 120× | 10 saniyelik jüri demosunda termal gecikmeyi görünür kılmak için |
| Fider yük eşiği | 0,80/1,00 oranı | Demo izleme/aşım kuralı; kablo ürün kapasitesi değildir |
| HFCT aktivite senaryosu | taban + 60 pC | Gösterge kuralını tetikleyen sentetik demo; kalibre ölçüm değildir |

Bu değerler veritabanı veya model çıktısı olarak “ölçülmüş gerçek” diye sunulmaz. Gerçek pano üzerinde termal kamera, ortam sensörü ve mikro-ohm ölçümüyle kalibrasyon yapıldığında yapılandırmaya taşınmalıdır.

## Risk orkestrasyonu

İlk sürüm üç açıklanabilir uzman sonucu üretir:

1. `thermal_load`: yük oranı, faz dengesizliği ve ölçülen-beklenen sıcaklık farkı.
2. `environment_insulation`: bağıl nem, çiy noktası ve en soğuk yüzey marjı.
3. `dielectric_safety`: TVOC yalnız algılama/trip ayrımı ve kalibrasyonsuz HFCT göstergesi.

Hem yalnız algılamalı ark hem kesici açtırmalı ark birleşik riski 100/Kritik yapar. Diğer durumlarda en yüksek tekil skor taban alınır; ikincil bulgular yalnızca yukarı yönlü sınırlı katkı verir. Böylece tek başına kritik bir termal veya çevresel bulgu ağırlıklı ortalama içinde seyrelmez.

HFCT aktivitesi nem girişinin zorunlu sonucu sayılmaz. Nem senaryosu yalnızca küçük bir sentetik korelasyon taşır; eşik davranışı bağımsız `pd_activity` senaryosuyla test edilir. Etiketli gerçek arıza verisi gizlilik nedeniyle bulunmadığından Isolation Forest gibi öğrenen modeller ve doğruluk/F1 iddiaları kalibrasyon fazına bırakılmıştır.

Termal uzman ayrıca önceki 30 fiziksel sıcaklık artığına göre çevrimiçi Z-skoru üretir.
En az 12 geçmiş örnek olmadan istatistiksel skor devreye girmez; standart sapma alt sınırı
0,1 K ve dört Z-skorunda 100 puan seçimi `model_assumption` değerleridir. Bu, eğitilmiş
bir sınıflandırıcı değil açıklanabilir residual istatistiğidir.

## Jüri cevaplarıyla netleşen sınırlar

- Mevcut SCADA'ya entegrasyon esastır; dashboard zorunlu değildir.
- Kablosuz iletişim zorunlu değildir. Uygun saha koşullarında ek değer olabilir.
- Sıcaklık ve akım ana etkenlerdir; fider riski nominal akıma göre değerlendirilir.
- Kablo akım taşıma kapasitesi yalnız kesitten türetilmez. Ürün ve kurulum bilgisi gelene kadar
  400 A DSYA nominali kullanılır.
- Sayısal örnekleme, raporlama gecikmesi ve demo başarı eşiği verilmemiştir; yazılım
  çevrimi konfigüre edilebilir ve bu sürümde 1 saniyedir.
