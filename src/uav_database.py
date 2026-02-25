"""
UAV Database - Validasyonlu UAV Bilesen Veritabani
=============================================

Bu modul, UAV (Insansiz Hava Araci) tasarimi icin gerekli olan
bileşen verilerini yonetir:

- Bataryalar (Lipo/Li-ion)
- Motorlar (Brushless DC)
- ESC (Electronic Speed Controller)
- Propeller'ler
- Kanat profilleri (Airfoil)

Veritabani yapisi:
-------------------
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
            "COST": USD,
            "VERIFIED": bool
        }
    },
    "ESC": {
        "esc_name": {
            "CONT_CURRENT": A,
            "PEAK_CURRENT": A,
            "VOLTAGE_MIN": V,
            "VOLTAGE_MAX": V,
            "Min_Cells": int,
            "Max_Cells": int,
            "WEIGHT": g,
            "EFFICIENCY": float,
            "COST": USD,
            "VERIFIED": bool
        }
    },
    "Propeller": {
        "prop_name": {
            "DIAMETER": mm,
            "PITCH": mm,
            "WEIGHT": g,
            "Thrust": N,
            "COST": USD
        }
    },
    "Wing": {
        "airfoil_name": {
            "CL_max": float,
            "CD_0": float,
            "k": float,
            "CM": float
        }
    }
}
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional


class UAVDatabase:
    """
    Validasyonlu UAV veritabanı yöneticisi

    Parameters
    ----------
    db_path : str or Path
        Veritabanı JSON dosyasının yolu

    Attributes
    ----------
    data : dict
        Ham veritabanı verisi
    batteries : dict
        Batarya verileri
    motors : dict
        Motor verileri
    propellers : dict
        Propeller verileri
    escs : dict
        ESC verileri
    wing : dict
        Kanat profili verileri
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Veritabanını yükle

        Parameters
        ----------
        db_path : str, optional
            Veritabanı dosya yolu. None varsayılan dosyayı kullanır
        """
        if db_path is None:
            # Varsayılan dosya yolu
            db_path = Path(__file__).parent.parent / "data" / "UAV_Database_v1.1.0_validated.json"

        with open(db_path, 'r') as f:
            self.data = json.load(f)

        self.batteries = self.data.get('Battery', {})
        self.motors = self.data.get('Motor', {})
        self.propellers = self.data.get('Propeller', {})
        self.escs = self.data.get('ESC', {})
        self.wing = self.data.get('Wing', {})

    def get_battery_list(self) -> List[Dict[str, Any]]:
        """
        Batarya listesini döndür

        Returns
        -------
        list
            [{
                'name': str,
                'capacity_mah': float,
                'voltage': float,
                'cells': int,
                'weight_kg': float,
                'c_rate': float,
                'cost_usd': float,
                'energy_wh': float,
                'power_w': float
            }, ...]
        """
        return [{
            'name': n,
            'capacity_mah': s.get('CAPACITY', 0),
            'voltage': s.get('VOLTAGE', 0),
            'cells': int(s.get('VOLTAGE', 0) / 3.7),
            'weight_kg': s.get('WEIGHT', 0) / 1000,  # g -> kg
            'c_rate': s.get('CONT_DISCHARGE_RATE', 0),
            'cost_usd': s.get('COST', 0),
            'energy_wh': (s.get('CAPACITY', 0) / 1000) * s.get('VOLTAGE', 0),
            'power_w': (s.get('CAPACITY', 0) / 1000) * s.get('VOLTAGE', 0) * s.get('CONT_DISCHARGE_RATE', 1)
        } for n, s in self.batteries.items()]

    def get_motor_list(self) -> List[Dict[str, Any]]:
        """
        Motor listesini döndür

        Returns
        -------
        list
            [{
                'name': str,
                'kv': float,
                'max_current_a': float,
                'max_power_w': float,
                'weight_kg': float,
                'min_cells': int,
                'max_cells': int,
                'cost_usd': float,
                'verified': bool
            }, ...]
        """
        return [{
            'name': n,
            'kv': s.get('KV', 0),
            'max_current_a': s.get('MAX_CURRENT', 0),
            'max_power_w': s.get('MAX_POWER', 0),
            'weight_kg': s.get('WEIGHT', 0) / 1000,  # g -> kg
            'min_cells': s.get('Min_Cells', 3),
            'max_cells': s.get('Max_Cells', 12),
            'cost_usd': s.get('COST', 100),
            'verified': s.get('VERIFIED', False)
        } for n, s in self.motors.items()]

    def get_esc_list(self) -> List[Dict[str, Any]]:
        """
        ESC listesini döndür

        Returns
        -------
        list
            [{
                'name': str,
                'cont_current': float,
                'peak_current': float,
                'voltage_min': float,
                'voltage_max': float,
                'cells_min': int,
                'cells_max': int,
                'weight_kg': float,
                'efficiency': float,
                'cost_usd': float,
                'verified': bool
            }, ...]
        """
        return [{
            'name': n,
            'cont_current': s.get('CONT_CURRENT', s.get('PEAK_CURRENT', 0) / 1.2),
            'peak_current': s.get('PEAK_CURRENT', s.get('CONT_CURRENT', 0) * 1.2),
            'voltage_min': s.get('VOLTAGE_MIN', s.get('Min_Cells', 3) * 3.7),
            'voltage_max': s.get('VOLTAGE_MAX', s.get('Max_Cells', 12) * 3.7),
            'cells_min': int(s.get('VOLTAGE_MIN', s.get('Min_Cells', 3) * 3.7) / 3.7) if 'VOLTAGE_MIN' in s else s.get('Min_Cells', 3),
            'cells_max': int(s.get('VOLTAGE_MAX', s.get('Max_Cells', 12) * 3.7) / 3.7) if 'VOLTAGE_MAX' in s else s.get('Max_Cells', 12),
            'weight_kg': s.get('WEIGHT', 0) / 1000,  # g -> kg
            'efficiency': s.get('EFFICIENCY', 0.95),
            'cost_usd': s.get('COST', 50),
            'verified': s.get('VERIFIED', False)
        } for n, s in self.escs.items()]

    def get_propeller_list(self) -> List[Dict[str, Any]]:
        """
        Propeller listesini döndür

        Returns
        -------
        list
            [{
                'name': str,
                'diameter_mm': float,
                'pitch_mm': float,
                'weight_kg': float,
                'cost_usd': float,
                'thrust_n': float
            }, ...]
        """
        return [{
            'name': n,
            'diameter_mm': s.get('DIAMETER', s.get('diameter', 0)),
            'pitch_mm': s.get('PITCH', s.get('pitch', 0)),
            'weight_kg': s.get('WEIGHT', s.get('weight', 0)) / 1000 if s.get('WEIGHT', s.get('weight', 0)) > 1 else s.get('WEIGHT', s.get('weight', 0)),
            'cost_usd': s.get('COST', 15),
            'thrust_n': s.get('Thrust', 0)
        } for n, s in self.propellers.items()]

    def get_wing_list(self) -> List[Dict[str, Any]]:
        """
        Kanat profili listesini döndür

        Returns
        -------
        list
            [{
                'name': str,
                'CL_max': float,
                'CD_0': float,
                'k': float,
                'CM': float
            }, ...]
        """
        return [{
            'name': n,
            'CL_max': s.get('CL_max', 1.5),
            'CD_0': s.get('CD_0', 0.02),
            'k': s.get('k', 0.05),
            'CM': s.get('CM', -0.1)
        } for n, s in self.wing.items()]

    def get_component(self, component_type: str, name: str) -> Optional[Dict[str, Any]]:
        """
        Belirli bir bileşeni al

        Parameters
        ----------
        component_type : str
            Bileşen tipi ('Battery', 'Motor', 'ESC', 'Propeller', 'Wing')
        name : str
            Bileşen adı

        Returns
        -------
        dict or None
            Bileşen verisi veya None
        """
        component_dict = getattr(self, component_type.lower() + 's', {})
        return component_dict.get(name)

    def get_statistics(self) -> Dict[str, Any]:
        """
        Veritabanı istatistiklerini döndür

        Returns
        -------
        dict
            İstatistik bilgileri
        """
        return {
            'num_batteries': len(self.batteries),
            'num_motors': len(self.motors),
            'num_escs': len(self.escs),
            'num_propellers': len(self.propellers),
            'num_wings': len(self.wing),
            'total_components': len(self.batteries) + len(self.motors) +
                               len(self.escs) + len(self.propellers) +
                               len(self.wing)
        }

    def __repr__(self) -> str:
        """String gösterimi"""
        stats = self.get_statistics()
        return (f"UAVDatabase(Batteries={stats['num_batteries']}, "
                f"Motors={stats['num_motors']}, ESCs={stats['num_escs']}, "
                f"Propellers={stats['num_propellers']}, Wings={stats['num_wings']})")


if __name__ == "__main__":
    # Test
    db = UAVDatabase()
    print(db)
    print("\nİstatistikler:")
    for k, v in db.get_statistics().items():
        print(f"  {k}: {v}")
