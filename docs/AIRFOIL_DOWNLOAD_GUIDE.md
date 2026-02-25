# UIUC Airfoil Database - Download Guide

**Date:** 2026-02-24
**Purpose:** Instructions for downloading airfoil coordinates from UIUC database

---

## 1. UIUC AIRFOIL COORDINATES DATABASE

**Main URL:** https://m-selig.ae.illinois.edu/ads/coord_database.html

**Contents:**
- ~1,650 airfoil coordinate files (.dat format)
- Airfoils listed alphabetically by filename
- Each airfoil has .dat (coordinates) and .gif (visualization) files

---

## 2. DIRECT DOWNLOAD URLS

### URL Pattern
```
https://m-selig.ae.illinois.edu/ads/coord_database/[filename].dat
```

### Available Airfoils for UAV_Database

| Airfoil | File | Direct URL |
|---------|------|------------|
| NACA 0012 | naca0012.dat | https://m-selig.ae.illinois.edu/ads/coord_database/naca0012.dat |
| NACA 0015 | naca0015.dat | https://m-selig.ae.illinois.edu/ads/coord_database/naca0015.dat |
| NACA 2412 | naca2412.dat | https://m-selig.ae.illinois.edu/ads/coord_database/naca2412.dat |
| NACA 2415 | naca2415.dat | https://m-selig.ae.illinois.edu/ads/coord_database/naca2415.dat |
| NACA 4412 | naca4412.dat | https://m-selig.ae.illinois.edu/ads/coord_database/naca4412.dat |
| NACA 4415 | naca4415.dat | https://m-selig.ae.illinois.edu/ads/coord_database/naca4415.dat |
| NACA 4418 | naca4418.dat | https://m-selig.ae.illinois.edu/ads/coord_database/naca4418.dat |
| NACA 6412 | naca6412.dat | https://m-selig.ae.illinois.edu/ads/coord_database/naca6412.dat |
| Eppler 387 | e387.dat | https://m-selig.ae.illinois.edu/ads/coord_database/e387.dat |
| Eppler 214 | e214.dat | https://m-selig.ae.illinois.edu/ads/coord_database/e214.dat |
| MH 60 | mh60.dat | https://m-selig.ae.illinois.edu/ads/coord_database/mh60.dat |
| MH 78 | mh78.dat | https://m-selig.ae.illinois.edu/ads/coord_database/mh78.dat |
| LS 0413 | ls0413.dat | https://m-selig.ae.illinois.edu/ads/coord_database/ls0413.dat |
| Clark Y | clarky.dat | https://m-selig.ae.illinois.edu/ads/coord_database/clarky.dat |
| Clark Y (smoothed) | clarkysm.dat | https://m-selig.ae.illinois.edu/ads/coord_database/clarkysm.dat |

**NOT Available in UIUC:**
- Selerowitsch_Rowan (not found in database)

---

## 3. COORDINATE FILE FORMAT

### Typical .dat File Format

```
# Line 1: Airfoil name and description
# Subsequent lines: x y coordinates (chord-normalized)

# Example: NACA 4415
NACA 4415
 1.0000  0.0000
 0.9975  0.0022
 0.9950  0.0031
 ...
 0.0000  0.0000
 ...
 0.9975 -0.0011
 1.0000  0.0000
```

**Format Notes:**
- First line: airfoil name/description
- Coordinates start from upper surface trailing edge
- Wrap around leading edge to lower surface
- Counterclockwise direction
- x, y normalized to chord (0 to 1)

---

## 4. BULK DOWNLOAD

### Option 1: coord_seligFmt.zip
- **URL:** Available on UIUC website (check Archives section)
- **Contents:** ~1,650 airfoils in standard format
- **Last updated:** 2/23/2026 (per website)

### Option 2: Individual Downloads
- Use curl or wget for each file
- Script example below

---

## 5. DOWNLOAD SCRIPT (Python)

```python
import urllib.request

# Airfoil files for UAV_Database
airfoils = [
    'naca0012.dat', 'naca0015.dat', 'naca2412.dat', 'naca2415.dat',
    'naca4412.dat', 'naca4415.dat', 'naca4418.dat', 'naca6412.dat',
    'e387.dat', 'e214.dat', 'mh60.dat', 'mh78.dat',
    'ls0413.dat', 'clarky.dat'
]

base_url = "https://m-selig.ae.illinois.edu/ads/coord_database/"
download_dir = "./airfoil_coordinates/"

for airfoil in airfoils:
    url = base_url + airfoil
    filename = download_dir + airfoil
    print(f"Downloading {airfoil}...")
    try:
        urllib.request.urlretrieve(url, filename)
        print(f"  ✓ Saved to {filename}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
```

---

## 6. XFOIL ANALYSIS

After downloading coordinates, analyze with XFOIL for CL_MAX, CD_0:

```
# XFOIL command sequence
LOAD naca4415.dat
OPER
VISC 200000     # Set Reynolds number
PACC
polar_naca4415.dat
ASEQ 0 16 0.5   # Angle of attack sweep
PACC
quit
```

---

## 7. ONLINE ALTERNATIVES

### AirfoilTools.com
- **URL:** https://airfoiltools.com
- **Features:**
  - Interactive plots
  - XFOIL-generated polars
  - Direct comparison tool
  - CSV export

### Martin Hepperle's Site
- **URL:** https://www.mh-aerotools.de/airfoils/
- **Features:**
  - MH series airfoils
  - JavaFoil online tool
  - Coordinate downloads

---

## 8. FILE NAMING CONVENTIONS

| Airfoil | UIUC Filename | Alternative Names |
|---------|---------------|-------------------|
| NACA 4415 | naca4415.dat | NACA4415.dat, NACA-4415.dat |
| Eppler 387 | e387.dat | E387.dat, eppler387.dat |
| Clark Y | clarky.dat | ClarkY.dat, clark_y.dat |

**Note:** UIUC uses lowercase with underscores. Alternative sources may vary.

---

## 9. SUMMARY

| Airfoil | UIUC Available | URL | Notes |
|---------|----------------|-----|-------|
| NACA_0012 | Yes | naca0012.dat | Standard symmetric |
| NACA_0015 | Yes | naca0015.dat | Thick symmetric |
| NACA_2412 | Yes | naca2412.dat | 2% camber |
| NACA_2415 | Yes | naca2415.dat | 2% camber, thick |
| NACA_4412 | Yes | naca4412.dat | 4% camber |
| NACA_4415 | Yes | naca4415.dat | Skywalker X8 base |
| NACA_4418 | Yes | naca4418.dat | Thick high-lift |
| NACA_6412 | Yes | naca6412.dat | STOL |
| Skywalker_X8 | N/A | Use naca4415.dat | See Gryte 2018 |
| Eppler_387 | Yes | e387.dat | Low-Re specialist |
| Eppler_214 | Yes | e214.dat | Sailplane |
| Selerowitsch_Rowan | **NO** | Not found | Unknown source |
| MH_60 | Yes | mh60.dat | Flying wing |
| MH_78 | Yes | mh78.dat | Hang glider |
| LS_0413 | Yes | ls0413.dat | Low-speed |
| Clark_Y | Yes | clarky.dat | Classic |

**Success Rate:** 15/16 airfoils available (93.75%)

---

**Guide prepared:** 2026-02-24
**For:** HFRPP UAV_Database integration
