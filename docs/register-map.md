# Modbus register haritası

Her pano iki kaynak cihazı temsil eder. `AG-001` için MPR unit ID 1, TVOC unit ID 2’dir. Sonraki panoda unit ID’ler 3 ve 4 olarak devam eder. 100 panoda kullanılan son unit ID 200’dür.

## MPR-53CS kaynak adresleri

MPR değerleri 32 bit tamsayı olarak iki ardışık 16 bit register’a yazılır. Aşağıdaki adresler dokümandaki PDU adresleridir.

| PDU | Veri | Ölçek | Kodlama |
|---:|---|---:|---|
| 0, 2, 4 | L1/L2/L3 faz gerilimi | 0,1 V | unsigned 32 bit |
| 6, 8, 10 | L1/L2/L3 faz akımı | 0,001×CT A | unsigned 32 bit |
| 12 | Nötr akımı | 0,001×CT A | unsigned 32 bit |
| 14, 16, 18 | L1-L2/L2-L3/L3-L1 gerilimi | 0,1 V | unsigned 32 bit |
| 44 | Toplam import aktif güç | 0,1×CT×VT W | signed/positive demo |
| 52 | Toplam görünür güç | 0,1×CT×VT VA | unsigned 32 bit |
| 58 | Frekans | 0,01 Hz | unsigned 32 bit |
| 84 | Dijital çıkış durumu | bit alanı | 16 bit |
| 85 | Dijital giriş durumu | bit alanı | 16 bit |

Kod 2500/5 CT için `CT=500`, doğrudan gerilim ölçümü için `VT=1` kullanır.

## TVOC-2 kaynak adresleri

| PDU | Register no | Veri | Kodlama |
|---:|---:|---|---|
| 149 | 150 | Trip sayısı | 16 bit |
| 206 | 207 | Diagnostik trip durumu | bit alanı |
| 210 | 211 | Aktif trip detektör low | bit alanı |
| 211 | 212 | Aktif trip detektör high | bit alanı |
| 212 | 213 | Aktif trip rölesi | bit alanı |
| 222–225 | 223–226 | Sensör durumu ve ortam ışığı uyarısı | bit alanı; 1=OK |
| 1300 | 1301 | Sistem durumu | bit0 aktif trip, bit1 aktif hata, bit2 başlangıç, bit3 diagnostik |

TVOC-2 kaynağı PDU adreslerini kullanır; bazı SCADA ekranlarının gösterdiği 1 tabanlı register numarası bir fazladır.

### İki ark çalışma modunun kodlanması

| Durum | PDU 210 detektör | PDU 212 trip rölesi | PDU 1300 bit0 | GridUp 10011/10012 |
|---|---:|---:|---:|---:|
| Normal | 0 | 0 | 0 | 0 / 0 |
| Ark algılandı, kesici açtırılmadı | sensör biti | 0 | 1 | 1 / 0 |
| Ark algılandı, kesici açtırıldı | sensör biti | K4 biti | 1 | 0 / 1 |

PDU 1300 bit0 üretici kılavuzunda **active trip** durumudur; yalnızca röle fiziksel olarak
açtırdı anlamına gelmez. Bu nedenle iki ark modunda da 1 kalır. Kesici açtırma ayrımı
PDU 212 trip rölesi ve GridUp özel mod bitleriyle yapılır.

## GridUp özel demo bloğu

10.000’den başlayan blok MPR-53CS veya TVOC-2 üretici haritası değildir. SCADA’da ortak sensör/analitik görünümü göstermek için ayrılmıştır.

| PDU | Veri | Kodlama |
|---:|---|---|
| 10000 | Ortam sıcaklığı | `(°C + 50) × 10` |
| 10001 | Bağıl nem | `% × 10` |
| 10002–10004 | L1/L2/L3 bara sıcaklığı | `(°C + 50) × 10` |
| 10005 | Çiy noktası | `(°C + 50) × 10` |
| 10006 | Yoğuşma marjı | `(K + 50) × 10` |
| 10007 | Birleşik risk | `0–100 × 10` |
| 10008 | Durum | 0 normal, 1 izle, 2 uyarı, 3 kritik |
| 10009 | HFCT gerilim göstergesi | `mV × 10` |
| 10010 | En yüksek fider yük oranı | `oran × 1000` |
| 10011 | Ark algılandı, kesici açtırılmadı | 0/1 |
| 10012 | Ark algılandı, kesici açtırıldı | 0/1 |
| 10013 | Yardımcı besleme | `V × 10` |
| 10014 | Termal artık | `(K + 50) × 10` |
| 10015 | Residual Z-skoru | `z × 100` |
| 10016 | Residual anomali skoru | `0-100 × 10` |
| 10017 | Yarışma profili satır indeksi | `0-151` |
| 10018 | Kaynak sekonder akımı | `mA × 10` |
| 10019 | Profilde geçen süre | dakika |

SCADA içe aktarımı/incelemesi için aynı bilgiler makine okunur
[`modbus-map.csv`](modbus-map.csv) dosyasında verilmiştir.
