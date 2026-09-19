# Donanım ve saha entegrasyonu konsepti

Bu belge jüri cevaplarıyla doğrulanan gereksinimleri, kaynak dokümanlardan gelen cihaz
özelliklerini ve henüz saha doğrulaması gereken tasarım kararlarını ayırır.

## Güç ve haberleşme

| Konu | MVP kararı | Durum |
|---|---|---|
| Birincil besleme | Panodaki mevcut 24 V DC yardımcı hat | Jüri tarafından doğrulandı |
| Güç koşullandırma | Sigortalı, izole DIN-ray DC/DC ve giriş aşırı-gerilim koruması | Önerilen tasarım; ürün seçimi ve güç bütçesi bekliyor |
| Haberleşme | Endüstriyel modem üzerinden tesis ağı/SCADA | Jüri tarafından doğrulanan yaklaşım |
| Kablosuz | Zorunlu değil; saha koşullarında artı değer olabilir | Jüri cevabı |
| Enerji depolama/hasadı | Ana çözüm değil | 24 V DC mevcut olduğundan bakım gerektiren pil zorunlu değil |

24 V hattın kullanılabilir akımı, sigorta koordinasyonu, galvanik izolasyon ihtiyacı,
topraklama/EMC düzeni ve enerji kesildiğinde istenen çalışma süresi saha elektrik
projesiyle doğrulanmadan donanım seçimi kesinleştirilmez.

## Veri yolları

- MPR-53CS ve TVOC-2 kaynak alanları üretici Modbus adreslerinde korunur.
- Mevcut cihazların Modbus/RS-485 verisini yeniden kullanmak, her büyüklük için yeni
  bir saha kablosu çekmek yerine ortak ve adreslenmiş veri yolu yaklaşımı sağlar.
- Sıcaklık, nem, HFCT göstergesi ve birleşik risk üreticiden bağımsız özel blokta taşınır.
- SCADA entegrasyonunun teslim girdisi `modbus-map.csv` dosyasıdır.
- Yerel ark koruması ağ veya uygulama gecikmesine bağımlı değildir; yazılım yalnızca
  olay ve açma durumunu raporlar.
- Dashboard zorunlu değildir; demo ve mühendislik görünümü olarak opsiyoneldir.

## Kablo kalabalığı ve güvenli kurulum ilkesi

Şartname, pano içi küçük bir çalışmanın dahi hayati risk ve planlı kesinti doğurabileceğini
belirtir. Bu nedenle çözüm **enerjili panoda sıfır kesintiyle montaj** iddiasında bulunmaz.
Savunulan yaklaşım şudur:

- mevcut MPR-53CS ve TVOC-2 Modbus verisini mümkün olduğunca yeniden kullanmak,
- yeni modülü kontrol/modem bölgesindeki korumalı DIN-ray alanında tek gövde olarak
  konumlandırmak; kesin yer ve boşluk için enerjisiz saha keşfi yapmak,
- yeni analog/sıcaklık/HFCT hatlarını güç iletkenlerinden ayrılmış, etiketli ve sökülebilir
  terminallerle minimumda tutmak,
- kurulum ve bakım adımlarını kurum prosedürüne uygun planlı, enerjisiz çalışma olarak
  gerçekleştirmek,
- bir sensör veya haberleşme arızasının yerel TVOC koruma zincirini devre dışı bırakmamasını
  sağlamak.

Yarışma kaynakları, akım ölçümü için belirli bir split-core ürün veya bara sıcaklığı için
manyetik/IR ürün modeli vermemiştir. Bu seçenekler saha pilotunda değerlendirilebilir; mevcut
teslimde satın alınmış, doğrulanmış veya enerjili montaja uygun bileşen gibi sunulmaz.

## Örnekleme ve gecikme

Jüri sinyal sınıfı başına sayısal örnekleme veya raporlama gecikmesi hedefi
tanımlamamıştır. MVP çevrimi yapılandırılabilir ve demoda 1 saniyedir. TVOC'nin yaklaşık
1 ms'lik yerel trip süresi, bu yazılım çevriminin kabul kriteri değildir. Saha kabulünde
SCADA tarama süresi, modem gecikmesi ve olay zaman damgası ayrı ayrı ölçülmelidir.

## Fider kapasitesi sınırı

Kaynak teknik tabloda 250 A ve 400 A DSYA seçenekleri bulunur; MVP 400 A varyantını
seçer. Kablo kesiti tek başına kesin akım taşıma kapasitesi değildir: ürün, yalıtım,
döşeme şekli, ortam sıcaklığı, gruplanma ve koruma düzeni gerekir. Bu nedenle kod,
doğrulanmamış bir mm²→A tablosu üretmek yerine `current / nominal_current` oranını
kullanır ve saha konfigürasyonunda nominal değerin değiştirilmesini öngörür.
