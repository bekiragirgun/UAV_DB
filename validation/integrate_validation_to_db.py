#!/usr/bin/env python3
"""
Validasyon verilerini UAV_Database'a entegre etmek için script
ESC v3 ve Airfoil analiz sonuçlarını ana veritabanına birleştirir
"""

import json
from pathlib import Path
from datetime import datetime

# Dosya yolları
db_path = Path('/Users/bekiragirgun/Downloads/UAV_Database_v1.1.0_validated.json')
esc_v3_path = Path('/Users/bekiragirgun/Projects/001_Makale02_literatur_review/HFRPP/data/esc_database_v3.json')
airfoil_analysis_path = Path('/Users/bekiragirgun/Projects/001_Makale02_literatur_review/HFRPP/data/airfoil_analysis_results.json')
output_path = Path('/Users/bekiragirgun/Downloads/UAV_Database_v1.1.0_validated.json')

# Mevcut veritabanını yükle
print("Ana veritabanı yükleniyor...")
with open(db_path, 'r') as f:
    db = json.load(f)

# ESC v3 veritabanını yükle
print("ESC v3 veritabanı yükleniyor...")
with open(esc_v3_path, 'r') as f:
    esc_v3 = json.load(f)

# Airfoil analiz sonuçlarını yükle
print("Airfoil analiz sonuçları yükleniyor...")
with open(airfoil_analysis_path, 'r') as f:
    airfoil_analysis = json.load(f)

# ============================================================================
# 1. ESC VERİLERİNİ GÜNCELLE
# ============================================================================
print("\n[1/3] ESC verileri güncelleniyor...")

# Mevcut ESC'leri al
current_escs = db.get('ESC', {})

# Her ESC modeli için güncelle
for esc_name, esc_data in current_escs.items():
    # ESC v3'de karşılık gelen modeli ara
    v3_name = None
    for v3_key in esc_v3['ESC_Database'].keys():
        # Benzer isim kontrolü (var olan değişiklikleri eşleştir)
        if esc_name.replace('_', ' ').replace(' ', '_') == v3_key or \
           esc_name == v3_key or \
           v3_key in esc_name or \
           esc_name in v3_key:
            v3_name = v3_key
            break

    # Eşleşme varsa verileri güncelle
    if v3_name:
        v3_data = esc_v3['ESC_Database'][v3_name]

        # VERIFIED alanını ekle
        if 'VERIFIED' in v3_data:
            esc_data['VERIFIED'] = v3_data['VERIFIED']

        # SOURCE alanını ekle
        if 'SOURCE' in v3_data and v3_data['SOURCE']:
            esc_data['SOURCE'] = v3_data['SOURCE']

        # NOTES alanını ekle
        if 'notes' in v3_data and v3_data['notes']:
            esc_data['notes'] = v3_data['notes']

        # Parametre düzeltmeleri (varsa)
        param_mapping = {
            'PEAK_CURRENT': 'PEAK_CURRENT',
            'CELLS_MIN': 'Min_Cells',
            'CELLS_MAX': 'Max_Cells',
            'WEIGHT': 'WEIGHT',
            'EFFICIENCY': 'EFFICIENCY'
        }

        for v3_param, db_param in param_mapping.items():
            if v3_param in v3_data and v3_data[v3_param] is not None:
                # Sadece mevcut değer None veya eksikse güncelle
                if db_param not in esc_data or esc_data[db_param] is None:
                    esc_data[db_param] = v3_data[v3_param]

        # VOLTAGE_MIN ve VOLTAGE_MAX hesapla
        if 'CELLS_MIN' in v3_data and v3_data['CELLS_MIN'] is not None:
            esc_data['VOLTAGE_MIN'] = v3_data['CELLS_MIN'] * 3.7
        if 'CELLS_MAX' in v3_data and v3_data['CELLS_MAX'] is not None:
            esc_data['VOLTAGE_MAX'] = v3_data['CELLS_MAX'] * 3.7

        print(f"  ✓ {esc_name} güncellendi (VERIFIED={esc_data.get('VERIFIED', False)})")

# Model değişikliklerini not et
if 'model_replacements' not in db:
    db['model_replacements'] = {}
db['model_replacements'].update(esc_v3.get('model_replacements', {}))

# ============================================================================
# 2. AIRFOIL VERİLERİNİ GÜNCELLE
# ============================================================================
print("\n[2/3] Airfoil verileri güncelleniyor...")

# Mevcut airfoil'ları al
current_airfoils = db.get('Wing', {}).get('AIRFOILS', {})

# Her airfoil için güncelle
for airfoil_name, airfoil_data in current_airfoils.items():
    # Analiz sonuçlarında karşılık ara
    if airfoil_name in airfoil_analysis:
        analysis_data = airfoil_analysis[airfoil_name]

        # CONFIDENCE alanını ekle
        airfoil_data['CONFIDENCE'] = analysis_data.get('confidence', 'medium')

        # METHOD bilgisini ekle
        airfoil_data['METHOD'] = analysis_data.get('method', 'computed')

        # REYNOLDS bilgisini güncelle
        if 'Reynolds' in analysis_data:
            airfoil_data['REYNOLDS_VALIDATED'] = analysis_data['Reynolds']

        # Kaynak doğrulama
        source_map = {
            'literature': 'Abbott & von Doenhoff (1959)',
            'Skywalker_X8': 'Gryte et al. (2018) - ICUAS 2018',
            'computed': 'UIUC Airfoil Database'
        }
        if 'method' in analysis_data:
            airfoil_data['SOURCE_VALIDATED'] = source_map.get(
                analysis_data['method'],
                analysis_data['method']
            )

        print(f"  ✓ {airfoil_name} güncellendi (CONFIDENCE={airfoil_data['CONFIDENCE']})")

# ============================================================================
# 3. METADATA EKLE
# ============================================================================
print("\n[3/3] Metadata ekleniyor...")

# Veritabanı versiyon bilgisi
db['_metadata'] = {
    'version': 'v1.1.0',
    'description': 'UAV Database with Validated ESC and Airfoil Data',
    'date': datetime.now().isoformat(),
    'validation_date': '2026-02-24',
    'changes': [
        'ESC: Added VERIFIED field from web scraping validation',
        'ESC: Added SOURCE field with datasheet URLs',
        'ESC: Added notes for model replacements and corrections',
        'Airfoil: Added CONFIDENCE field (high/medium/low)',
        'Airfoil: Added METHOD field (literature/computed)',
        'Airfoil: Validated against Abbott & von Doenhoff (1959)',
        'Airfoil: Skywalker X8 validated against Gryte 2018'
    ],
    'validation_summary': {
        'esc': {
            'total': len(current_escs),
            'verified': sum(1 for e in current_escs.values() if e.get('VERIFIED') == True),
            'unverified': sum(1 for e in current_escs.values() if not e.get('VERIFIED'))
        },
        'airfoil': {
            'total': len(current_airfoils),
            'high_confidence': sum(1 for a in current_airfoils.values() if a.get('CONFIDENCE') == 'high'),
            'medium_confidence': sum(1 for a in current_airfoils.values() if a.get('CONFIDENCE') == 'medium'),
            'low_confidence': sum(1 for a in current_airfoils.values() if a.get('CONFIDENCE') == 'low')
        }
    },
    'sources': {
        'ESC': 'T-Motor, HobbyWing, KDE Direct official websites and distributors',
        'Airfoil': 'Abbott & von Doenhoff (1959), Gryte et al. (2018), UIUC Airfoil Database',
        'Validation': 'HFRPP v07.0 Data Validation Project'
    }
}

# ============================================================================
# 4. KAYDET
# ============================================================================
print(f"\nKaydediliyor: {output_path}")
with open(output_path, 'w') as f:
    json.dump(db, f, indent=2)

print("\n✓ Validasyon entegrasyonu tamamlandı!")

# Özet
print("\n" + "="*60)
print("ENTEGRASYON ÖZETİ")
print("="*60)
print(f"\nESC Modelleri:")
print(f"  Toplam: {db['_metadata']['validation_summary']['esc']['total']}")
print(f"  Doğrulanmış: {db['_metadata']['validation_summary']['esc']['verified']}")
print(f"  Doğrulanmamış: {db['_metadata']['validation_summary']['esc']['unverified']}")

print(f"\nAirfoil Modelleri:")
print(f"  Toplam: {db['_metadata']['validation_summary']['airfoil']['total']}")
print(f"  Yüksek güvenilirlik: {db['_metadata']['validation_summary']['airfoil']['high_confidence']}")
print(f"  Orta güvenilirlik: {db['_metadata']['validation_summary']['airfoil']['medium_confidence']}")
print(f"  Düşük güvenilirlik: {db['_metadata']['validation_summary']['airfoil']['low_confidence']}")

print(f"\nModel Değişiklikleri:")
for old, new in db['model_replacements'].items():
    print(f"  {old} → {new}")

print("\n" + "="*60)
