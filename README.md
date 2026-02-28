# UAV Component Database

Component database for NATO Class I Tactical Reconnaissance UAV design optimization.

## Purpose

This project provides a validated component database for UAV design optimization using the HFRPP (Hybrid Fuzzy-Rough Physical Programming) framework. The database covers:

- **Batteries**: LiPo battery specifications (capacity, voltage, weight, cost)
- **Motors**: Brushless DC motors (KV, max current/power, weight)
- **ESC**: Electronic Speed Controllers (current rating, efficiency, BEC)
- **Propellers**: UIUC propeller database CT/CP coefficients
- **Airfoils**: XFOIL-analyzed airfoil profiles

## Data Format

```json
{
  "Battery": {
    "battery_name": {
      "CAPACITY": "mAh",
      "VOLTAGE": "V",
      "WEIGHT": "g",
      "CONT_DISCHARGE_RATE": "C",
      "COST": "USD"
    }
  },
  "Motor": {
    "motor_name": {
      "KV": "rpm/V",
      "MAX_CURRENT": "A",
      "MAX_POWER": "W",
      "WEIGHT": "g",
      "Min_Cells": "int",
      "Max_Cells": "int",
      "VERIFIED": "bool"
    }
  }
}
```

## Usage

```python
from src.uav_database import UAVDatabase

# Load database
db = UAVDatabase("data/UAV_Database_v1.1.0_validated.json")

# Get component lists
batteries = db.get_battery_list()
motors = db.get_motor_list()
escs = db.get_esc_list()
propellers = db.get_propeller_list()

# Statistics
print(db.get_statistics())
```

## Directory Structure

```
UAV_DB/
├── data/                          # JSON database files
│   ├── UAV_Database_v1.0.0.json            # Original database
│   ├── UAV_Database_v1.1.0.json            # Updated version
│   ├── UAV_Database_v1.1.0_validated.json  # Validated (recommended)
│   ├── esc_database.json                   # ESC database v3.1 (14 models, all verified)
│   ├── airfoil_analysis_results.json       # Airfoil analysis results
│   └── propeller_ct_cp_lookup.json         # UIUC propeller CT/CP
├── src/                           # Python modules
│   ├── uav_database.py                     # Main database class
│   ├── propeller_ct_cp_module.py           # Propeller performance
│   ├── propeller_performance_model.py      # Propeller model
│   ├── esc_selection.py                    # ESC selection criteria
│   └── airfoil_analysis.py                 # XFOIL airfoil analysis
├── validation/                    # Validation scripts
│   └── integrate_validation_to_db.py       # Validation integration
└── docs/                          # Documentation
    ├── AIRFOIL_DOWNLOAD_GUIDE.md           # Airfoil download guide
    └── SKYWALKER_X8_AIRFOIL_VERIFICATION.md # Verification report
```

## Component Coverage

| Component | Count | Source | Validation |
|-----------|-------|--------|------------|
| Battery | 56 | Manufacturer datasheets | Medium |
| Motor | 146 | T-Motor (119) + KDE Direct (27) | Medium |
| Propeller | 348 | Physical specs (4.1-27.0 inch) | High |
| Propeller Aero | 29 | UIUC database (CT/CP) | High |
| ESC | 14 | Manufacturer datasheets (14/14 verified) | High |
| Airfoil | 16 | NACA reports + XFOIL + UIUC | High |

## ESC Database (v3.1)

14 fully verified ESC models covering 20-125A continuous current:

| Category | Current Range | Models |
|----------|--------------|--------|
| Micro | 20 A | T-Motor AIR 20A, HobbyWing SkyWalker 20A |
| Small | 40-55 A | T-Motor ALPHA 40A, T-Motor AT55A, HobbyWing SkyWalker 50A |
| Medium | 60-70 A | T-Motor FLAME 70A, HobbyWing SkyWalker 60A, HobbyWing XRotor H60A, T-Motor Alpha 60A HV |
| Large | 80-100 A | T-Motor ALPHA 80A, HobbyWing XRotor Pro 100A |
| XLarge | 120-125 A | T-Motor Thunder 120A, HobbyWing XRotor Pro 120A, KDE UAS125UVC-HE |

## Versions

| Version | Date | Changes |
|---------|------|---------|
| v1.0.0 | 2025-02-23 | Initial database |
| v1.1.0 | 2025-02-24 | Added validation fields |
| v1.1.1 | 2026-02-28 | ESC database v3.1: consolidated to 14 verified models, English-only, replaced hypothetical entries with real manufacturer specs |

## References

- UIUC Propeller Data Database: http://m-selig.ae.illinois.edu/props/propDB.html
- XFOIL: http://web.mit.edu/drela/Public/web/xfoil/
- Skywalker X8: Gryte et al. (2018) - ICUAS, DOI: 10.1109/ICUAS.2018.8453370
- HFRPP Paper: https://github.com/bekiragirgun/HRFPP

## License

MIT License
