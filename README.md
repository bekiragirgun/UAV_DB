# UAV Database

UAV (İnsansız Hava Aracı) tasarımı için bileşen veritabanı.

## Amaç

Bu proje, NATO Class I Taktik Keşif UAV'ları için optimize edilmiş bir bileşen veritabanı sağlar. Veriler:

- **Bataryalar**: LiPo batarya özellikleri (kapasite, voltaj, ağırlık, maliyet)
- **Motorlar**: Fırçasız DC motorlar (KV, maksimum akım/güç, ağırlık)
- **ESC**: Elektronik hız kontrolcüler (akım kapasitesi, verimlilik)
- **Propeller'ler**: UIUC propeller veritabanından CT/CP katsayıları
- **Kanat Profilleri**: XFOIL ile analiz edilmiş havafoil verileri

## Veri Formatı

```json
{
  "Battery": {
    "battery_name": {
      "CAPACITY": mAh,
      "VOLTAGE": V,
      "WEIGHT": g,
      "CONT_DISCHARGE_RATE": C,
      "COST": USD
    }
  },
  "Motor": {
    "motor_name": {
      "KV": rpm/V,
      "MAX_CURRENT": A,
      "MAX_POWER": W,
      "WEIGHT": g,
      "Min_Cells": int,
      "Max_Cells": int,
      "VERIFIED": bool
    }
  },
  ...
}
```

## Kullanım

```python
from src.uav_database import UAVDatabase

# Veritabanını yükle
db = UAVDatabase("data/UAV_Database_v1.1.0_validated.json")

# Bileşen listelerini al
batteries = db.get_battery_list()
motors = db.get_motor_list()
escs = db.get_esc_list()
propellers = db.get_propeller_list()

# İstatistikler
print(db.get_statistics())
```

## Dosya Yapısı

```
UAV_DB_1/
├── data/                          # JSON veritabanı dosyaları
│   ├── UAV_Database_v1.0.0.json            # Orijinal veritabanı
│   ├── UAV_Database_v1.1.0.json            # Güncellenmiş
│   ├── UAV_Database_v1.1.0_validated.json  # Validasyonlu (önerilen)
│   ├── esc_database_v3.json                # ESC validasyon verileri
│   ├── airfoil_analysis_results.json        # Airfoil analiz sonuçları
│   └── propeller_ct_cp_lookup.json         # UIUC propeller CT/CP
├── src/                          # Python modülleri
│   ├── uav_database.py                     # Ana veritabanı sınıfı
│   ├── propeller_ct_cp_module.py           # Propeller performansı
│   ├── propeller_performance_model.py      # Propeller modeli
│   ├── esc_selection.py                    # ESC seçim kriterleri
│   └── airfoil_analysis.py                 # XFOIL airfoil analizi
├── validation/                   # Validasyon script'leri
│   └── integrate_validation_to_db.py        # Validasyon entegrasyonu
└── docs/                         # Dokümantasyon
    ├── AIRFOIL_DOWNLOAD_GUIDE.md            # Airfoil indirme rehberi
    └── SKYWALKER_X8_AIRFOIL_VERIFICATION.md # Doğrulama raporu
```

## Validasyon Durumu

| Bileşen | Validasyon Yöntemi | Güvenilirlik |
|---------|-------------------|--------------|
| ESC     | Web scraping + çapraz kontrol | Orta |
| Airfoil | XFOIL analiz + UIUC DB       | Yüksek |
| Propeller| UIUC DB (CT/CP)              | Yüksek |
| Motor   | Üretici verisi               | Orta |
| Battery | Üretici verisi               | Orta |

## Sürümler

| Versiyon | Tarih | Değişiklik |
|----------|-------|------------|
| v1.0.0 | 2025-02-23 | İlk versiyon |
| v1.1.0 | 2025-02-24 | Validasyon alanları eklendi |

## Referanslar

- UIUC Propeller Data Database: http://m-selig.ae.illinois.edu/props/propDB.html
- XFOIL: http://web.mit.edu/drela/Public/web/xfoil/
- Skywalker X8: Gryte et al. (2018)

## Lisans

MIT License
