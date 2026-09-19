# GridUp 1600 kVA AG Pano Dijital İkizi

Bu depo, ADM/GDZ Grid Up Hackathon kapsamındaki **Pano/Hücre İçi Anomali Erken Uyarı Sistemi** için çalışan MVP'dir. İlk varlık modeli, yarışma girdilerindeki 1600 kVA AG panodur. Akım, bara sıcaklığı, nem/yoğuşma marjı, HFCT göstergesi ve iki ark çalışma modunu üretir; veriyi öncelikle mevcut SCADA'ya Modbus TCP üzerinden, demo ve mühendislik gözlemi için REST/WebSocket üzerinden sunar.

## Güncel kapsam

- 1600 kVA, 400 V üç faz için anma akımı kontrolü: 2309,4 A
- 2×(100×10 mm²) ana bara ve 2500/5 akım trafosu bilgileri
- Akıma bağlı bara/temas direnci ve birinci dereceden ısıl model
- `İstenen Veriler.xlsx` dosyasından kayıpsız aktarılan 152 noktalık sentetik akım profili ve varsayılan replay modu
- Fiziksel sıcaklık artığı üzerinde 30 örneklik, açıklanabilir çevrimiçi Z-skoru
- Nem, çiy noktası ve yüzey sıcaklığı marjı
- Normal, aşırı yük, faz dengesizliği, gevşek temas, nem girişi, HFCT aktivitesi, yalnız algılamalı ark ve kesici açtırmalı ark senaryoları
- 5×400 A aktif ve 2 yedek DSYA fideri için akım/nominal akım yük oranı
- MPR-53CS ve TVOC-2 kaynak haritalarına bağlı Modbus register görünümü
- Tekil kritik bulguyu seyreltmeyen, açıklanabilir ve maksimumu koruyan risk birleşimi
- SQLite WAL, toplu telemetri yazımı, olay geçmişi ve loglanan simüle SMS/WhatsApp outbox kaydı
- Mevcut pano 24 V DC yardımcı hattı ve endüstriyel modemle uyumlu donanım konsepti
- Resmi 1600 kVA pano çizimine bağlı DIN-ray yerleşim, elektronik blok ve PCB konsepti
- Taşınabilir C firmware çekirdeği, I/O tablosu, BOM ve hata-etki analizi
- Web arayüzünde canlı SMS/WhatsApp simülasyon outbox görünümü
- 10 pano ile görsel demo, yapılandırma üzerinden 100 modüle çıkabilme

## Hızlı başlatma

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
cp .env.example .env
uvicorn gridup.api:app --app-dir backend --reload --port 8000
```

Başka bir terminalde:

```bash
cd frontend
npm install
npm run dev
```

- Arayüz: `http://localhost:5173`
- API: `http://localhost:8000/docs`
- Modbus TCP: `localhost:1502` (demo portu; üretimde ağ/politika değerlendirmesi gerekir)

## Test

```bash
pytest
make -C firmware test
cd frontend && npm run build
```

## Kaynak ve varsayım disiplini

Kod içindeki her sayısal değer `source`, `derived` veya `model_assumption` olarak sınıflandırılmıştır. Gerçek etiketli arıza verisi gizlilik nedeniyle paylaşılmadığından bu sürüm doğruluk, duyarlılık veya F1 iddiasında bulunamaz. Yarışma dosyalarının vermediği temas direnci, ısıl kapasite, ısıl direnç ve alarm eşikleri **kalibre edilmemiş model varsayımıdır**.

Teslimlerin tamamı [uygunluk matrisi](docs/deliverable-compliance.md) içinde izlenir. Donanım tarafı için [fiziksel modül](docs/physical-module-design.md), [elektronik tasarım](docs/electronic-design.md), [BOM](docs/bom.csv) ve [saha FMEA](docs/field-deployment-fmea.md); yazılım için [mimari](docs/software-architecture.md), [register haritası](docs/register-map.md), [SCADA eşleme tablosu](docs/modbus-map.csv) ve [kabul testleri](docs/acceptance-tests.md) sağlanmıştır. Final gösterimi [demo çalışma planını](docs/demo-runbook.md) izler.

Yarışma verisinin kodla bağlantısı ve residual metriği [replay ve residual belgesinde](docs/dataset-replay-and-residual.md), son iki günlük kapanış sırası ise [yol haritasında](docs/two-day-roadmap.md) açıklanır.

Jüri anlatımı için 12 slaytlık [final sunum](output/presentation/GridUp-Juri-Sunumu-v0.3.1.pptx) hazırdır.

## Mimari

```text
Fizik tabanlı simülatör -> uzman risk modülleri -> orkestratör
              |                       |
      Modbus TCP/SCADA           SQLite WAL/olaylar
              |                       |
              +------ FastAPI/WebSocket ------ Opsiyonel demo ekranı
```

Bu MVP Public Cloud servisine ihtiyaç duymaz. Dashboard jüri gereksinimi değildir; yalnızca demo ve mühendislik görünürlüğü için korunmuştur. Bildirim katmanı gerçek kişilere mesaj göndermek yerine yerel outbox kaydı ve canlı uygulama logu üretir.
