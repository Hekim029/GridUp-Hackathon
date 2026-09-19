# Yarışma Akım Verisi Replay ve Hibrit Artık (Residual) Analizi

Bu doküman, jüri tarafından paylaşılan akım profili verisinin sisteme entegrasyonunu, per-unit ölçekleme mantığını ve fizik motoru ile birlikte çalışan hibrit anomali tespit mimarisini açıklar.

---

## 1. Kaynak Akım Profili (`İstenen Veriler.xlsx`)

Yarışma kapsamında sağlanan `İstenen Veriler.xlsx` dosyasındaki **Akım Sensörü** sekmesi (7–158. satırlar) baz alınmıştır.

* **Zaman Serisi:** 15 dakikalık aralıklarla kaydedilmiş **152 ölçüm noktası** (toplam 0 – 2265 dakika / yaklaşık 37.7 saat).
* **Dönüştürücü Özelliği:** 0–100 mA sekonder çıkışlı sensör, 600 A primer tam ölçeğine (Full-Scale) dönüştürülür:
  $$\text{I}_{\text{primer}} [\text{A}] = \text{I}_{\text{sekonder}} [\text{mA}] \times \frac{6000}{1000}$$
* **Pano Yük Ölçeklemesi (Per-Unit Mapping):** Kaynak verideki primer akım (90–540 A), 600 A tam ölçek üzerinden per-unit ($I_{\text{pu}} \in [0.0, 1.0]$) yük oranına çevrilir. Bu oran 1600 kVA panonun anma akımı olan **2309.4 A** ile çarpılarak ana baraya uygulanır:
  $$I_{\text{bara}} = I_{\text{pu}} \times I_{\text{anma}} = \left(\frac{I_{\text{primer}}}{600.0}\right) \times 2309.4\text{ A}$$
* **Kayıpsız Depolama:** Ham verinin işlenmiş kopyası `resources/competition_current_profile.csv` altında yer alır.

### Doğrulama ve Denetim Yüzeyleri

| Denetim Yüzeyi | Erişim / Adres | Açıklama |
| :--- | :--- | :--- |
| **REST API** | `GET /api/v1/current-profile` | 152 noktalık zaman serisinin tamamı |
| **Sistem Konfigürasyonu** | `GET /api/v1/config` | Replay durumu, CT oranı ve örnek sayısı |
| **Operatör Paneli** | Web Arayüzü (Header) | Anlık profil satırı, saat, sekonder mA ve çarpan |
| **Modbus SCADA** | Holding Register `10017–10019` | Profil indisi, sekonder akım (x10) ve geçen dakika |

---

## 2. Fizik Bilgili Artık ve Anomali Modeli (Residual Z-Score)

Sistem, kara kutu yapay zeka yerine fizik motorunun çıktısıyla istatistiği birleştiren deterministik ve açıklanabilir bir model kullanır.

Lumped termal model eşzamanlı olarak iki sıcaklık durumu hesaplar:
* **$T_{\text{actual}}$:** Çalışma koşullarında ölçülen gerçek bara sıcaklığı (gevşek temas ve arızaları içerir).
* **$T_{\text{expected}}$:** Sağlıklı referans ($I^2R$ kaybı ve Newton soğuma modeli çözümü).

### Matematiksel Bağıntılar

**1. Termal Artık (Residual):**
$$e_t = \max(T_{\text{actual}, \phi} - T_{\text{expected}, \phi})$$

**2. Gürültü Kestirimi (First Differences):**  
Sağlıklı bir sistemde beklenen artık sıfırdır ($E[e] = 0$). Gelişen bir aşırı ısınmanın referans pencereyi yapay olarak kaydırıp arızayı "yeni normal" kabul etmesini (adaptasyon tuzağı) önlemek için ardışık farklar üzerinden gürültü hesaplanır:
$$\Delta e_t = e_t - e_{t-1}$$
$$\sigma_{\text{measured}} = \frac{\text{std}(\Delta e)}{\sqrt{2}}$$
$$\sigma = \max(\sigma_{\text{noise}}, \sigma_{\text{measured}}) \quad (\sigma_{\text{noise}} = 1.5\text{ K})$$

**3. Z-Skor ve Normalize Risk:**
$$z_t = \frac{\max(0, e_t)}{\sigma}$$
$$\text{Score}_z = \min\left(100.0, \frac{z_t}{4.0} \times 100.0\right)$$

> **Referans Pencere Kuralı:**  
> Referans geçmişe yalnızca $\text{Score}_z < 25.0$ (sağlıklı rejim) olan veriler eklenir. Bir arıza başladığında referans pencerenin güncellenmesi dondurulur; böylece arıza sürdüğü müddetçe Z-skoru yüksek kalmaya devam eder.

---

## 3. Mimari ve Saha Notları

* **Etiketli Veri Bağımsızlığı:** Sahadan geçmiş arıza etiketi bulunmadığı için denetimli makine öğrenmesi yerine fizik kurallarına dayalı artık analizi tercih edilmiştir.
* **Açıklanabilirlik:** Üretilen risk skoru operatöre doğrudan fiziksel kanıtlarıyla (Kelvin cinsinden artık, Z-skor değeri ve örnek sayısı) sunulur.