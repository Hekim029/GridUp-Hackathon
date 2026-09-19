# Saha kurulumu bakım ve hata etki analizi

Şartname, mission critical yapı nedeniyle kurulum sırasında ve sonrasında oluşabilecek
hataların etkilerinin düşünülmesini ister. Bu belge hackathon prototipi için uygulanabilirlik
kanıtıdır; yetkili saha prosedürünün yerine geçmez.

## Kurulum sırası

1. Pano kimliği, çizim revizyonu, mevcut 24 V DC kapasitesi ve kontrol bölgesi boşluğu
   enerjisiz keşifte doğrulanır.
2. Modül, modem, terminal ve kablo güzergahı çizim üzerinde işaretlenir.
3. Sensör kabloları ve pluggable terminal demeti pano dışında hazırlanıp etiketlenir.
4. Planlı çalışma penceresinde DIN-ray modülü ve sensörler mekanik olarak yerleştirilir.
5. Güç vermeden önce polarite, süreklilik, ekran/toprak bağlantısı ve kablo sıkışması kontrol edilir.
6. Modül enerjilendirilir; heartbeat, sensör kalite durumları ve Modbus adresleri test edilir.
7. TVOC detect-only ve trip bilgileri gerçek kesiciye komut vermeden okuma yoluyla doğrulanır.
8. SCADA eşleme, alarm yönlendirme ve olay zaman damgası kabul tutanağına işlenir.

## Ön hata etki analizi

| Hata | Etki | MVP tespiti | Tasarım önlemi | Saha kabulü |
|---|---|---|---|---|
| 24 V DC kaybı | İzleme modülü susar | heartbeat kaybı | TVOC ve MPR zincirinden bağımsız bağlantı | Güç kesme/geri gelme testi |
| Ters polarite veya giriş aşımı | Kart hasarı | enerji yok / reset | sigorta, giriş koruması, izole DC/DC konsepti | kart elektrik testi |
| RS-485 A/B tersliği | Veri okunamaz | iletişim zaman aşımı | etiketli sökülebilir terminal | adres ve hat testi |
| Aynı Modbus ID | veri çakışması | tutarsız/yanıtsız cihaz | devreye alma adres listesi | 1-247 benzersizlik kontrolü |
| Sensör kopması | yanlış normal değer riski | kalite biti / aralık kontrolü | kopuk veriyi risk hesabına geçerli ölçüm olarak alma | kanal açma testi |
| Analog giriş taşması | hatalı akım | 0-100 mA aralık kontrolü | giriş sınırlama ve hata durumu | 0, 80 ve 100 mA nokta testi |
| HFCT hat/sonlandırma hatası | PD göstergesi güvenilmez | aktivite tabanı sapar | 50 ohm ön uç ve koaksiyel güzergah | analizörle karşılaştırma |
| TVOC algıladı, röle açtırmadı | koruma modu veya zincir sorunu | PDU 210 aktif, PDU 212 pasif | iki durumu ayrı alarm kodu | senaryo/olay kaydı testi |
| Ağ veya modem kaybı | merkeze rapor gecikir | sunucu heartbeat kaybı | yerel koruma ağdan bağımsız, olaylar yerelde tutulur | bağlantı kesme testi |
| SQLite yazma baskısı | geçmiş kaybı/gecikme | uygulama logu | WAL ve toplu yazım | 100 modül yük testi |
| Yanlış eşik/kalibrasyon | yanlış alarm veya kaçırma | kaynak/varsayım etiketi | eşikleri konfigürasyona taşıma ve saha kalibrasyonu | etiketli veri kabulü |
| Modül kablosu servis alanında | kopma veya çalışma riski | görsel kontrol | kontrol kanalında ayrı güzergah ve sabitleme | montaj kontrol listesi |

## Bakım yaklaşımı

| Periyot | Kontrol |
|---|---|
| Her yazılım çevrimi | sensör aralığı, iletişim, heartbeat, veri zaman damgası |
| Olay sonrası | TVOC detektör/röle kayıtları, bildirimler, saha bulgusu ve kök neden |
| Planlı pano bakımı | terminal sıkılığı, kablo ezilmesi, sensör sabitlemesi, muhafaza ve etiket |
| Yazılım güncellemesi | yedek, sürüm kaydı, test senaryoları, geri dönüş planı |

## Emniyet sınırı

Bu sistem erken uyarı ve raporlama katmanıdır. Kesici açtırma yetkisi TVOC-2'nin mevcut yerel
koruma zincirinde kalır. İzleme modülü arızası koruma rölesini bloke etmemeli, devre dışı
bırakmamalı veya geciktirmemelidir.
