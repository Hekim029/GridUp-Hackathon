# GridUp taşınabilir saha modülü çekirdeği

Bu klasör, mikrodenetleyici kullanılması halinde şartnamenin istediği temel çalışma mantığı ve
kaynak kod için donanımdan bağımsız bir C referansı sağlar. Kod, 0-100 mA akım dönüşümünü,
TVOC iki mod ayrımını ve GridUp özel register görüntüsünü test eder.

```bash
make -C firmware test
```

Bu bir STM32 veya ESP32 kart desteği değildir. Seçilecek kartın ADC, UART/RS-485, watchdog,
zaman damgası ve sensör sürücüleri `gridup_edge_sample()` çevresindeki platform katmanına
bağlanmalıdır. Donanım hedefi kesinleşmeden uydurma pin veya çevrebirim adresi verilmemiştir.

## Çalışma sırası

1. Platform ADC ve dijital girişleri okur.
2. `gridup_edge_sample()` 0-100 mA değerini 0-600 A primer değere çevirir.
3. Detektör ve röle bitlerinden detect-only/trip durumu ayrılır.
4. `gridup_edge_custom_registers()` özel Modbus alanlarını üretir.
5. Platform katmanı registerları Modbus RTU üzerinden yayınlar ve heartbeat'i yeniler.
