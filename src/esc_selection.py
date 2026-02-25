"""
ESC Selection Module for HFRPP v07.0
Matches motors with ESCs based on current, voltage, and weight constraints

Extended parameters (v2.0):
- BEC voltage/current for avionics power
- Internal resistance for voltage drop calculation
- Cost for optimization

Author: HFRPP Team
Date: 2026-02-24
"""

import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# ESC database path
ESC_DB_PATH = Path(__file__).parent / "esc_database_v2.json"


class ESCDatabase:
    """
    ESC Database with selection and matching functionality
    """

    SAFETY_MARGIN = 0.20  # 20% current margin
    HC4_FACTOR = 0.80     # I_motor ≤ 0.8 × I_ESC

    # Avionics power requirement (typical)
    AVIONICS_VOLTAGE = 5.0  # V
    AVIONICS_CURRENT = 2.0  # A (servos, receiver, telemetry)
    AVIONICS_POWER = AVIONICS_VOLTAGE * AVIONICS_CURRENT  # 10W

    def __init__(self, db_path=None):
        """Load ESC database"""
        self.db_path = db_path or ESC_DB_PATH
        self.esc_db = self._load_database()
        self._build_indexes()

    def _load_database(self) -> Dict:
        """Load ESC database from JSON"""
        try:
            with open(self.db_path, 'r') as f:
                data = json.load(f)
                return data['ESC_Database']
        except FileNotFoundError:
            print(f"Warning: ESC database not found at {self.db_path}")
            return {}
        except KeyError:
            print(f"Warning: Invalid ESC database format")
            return {}

    def _build_indexes(self):
        """Build lookup indexes for fast queries"""
        self.by_current = {}  # current_cont -> list of ESCs
        self.by_size = {}     # size_class -> list of ESCs
        self.by_cells = {}    # cell_count -> list of ESCs
        self.by_bec = {}      # has_bec -> list of ESCs

        for esc_id, esc in self.esc_db.items():
            # Index by continuous current
            curr = esc.get('CONT_CURRENT', 0)
            if curr not in self.by_current:
                self.by_current[curr] = []
            self.by_current[curr].append(esc_id)

            # Index by size class
            size = esc.get('size_class', '')
            if size not in self.by_size:
                self.by_size[size] = []
            self.by_size[size].append(esc_id)

            # Index by cell compatibility
            cells_min = esc.get('CELLS_MIN', 0)
            cells_max = esc.get('CELLS_MAX', 0)
            for c in range(cells_min, cells_max + 1):
                if c not in self.by_cells:
                    self.by_cells[c] = []
                self.by_cells[c].append(esc_id)

            # Index by BEC availability
            has_bec = esc.get('BEC_VOLTAGE', 0) > 0
            bec_key = 'with_bec' if has_bec else 'opto_only'
            if bec_key not in self.by_bec:
                self.by_bec[bec_key] = []
            self.by_bec[bec_key].append(esc_id)

    def get_compatible_escs(self,
                           motor_current: float,
                           battery_cells: int,
                           weight_limit: Optional[float] = None,
                           require_bec: bool = True) -> List[str]:
        """
        Get list of compatible ESC IDs for given motor and battery

        Args:
            motor_current: Motor max current (A)
            battery_cells: Battery cell count (2-12S typical)
            weight_limit: Maximum ESC weight (kg), optional
            require_bec: Require BEC for avionics power

        Returns:
            List of compatible ESC IDs
        """
        required_current = motor_current * (1 + self.SAFETY_MARGIN)
        compatible = []

        for esc_id, esc in self.esc_db.items():
            # Current check
            if esc.get('CONT_CURRENT', 0) < required_current:
                continue

            # Cell count check
            cells_min = esc.get('CELLS_MIN', 0)
            cells_max = esc.get('CELLS_MAX', 0)
            if not (cells_min <= battery_cells <= cells_max):
                continue

            # Weight check
            if weight_limit is not None:
                if esc.get('WEIGHT', 0) > weight_limit:
                    continue

            # BEC check
            has_bec = esc.get('BEC_VOLTAGE', 0) > 0
            if require_bec and not has_bec:
                # OPTO ESC requires separate UBEC
                # Add weight penalty for UBEC (~20g)
                if weight_limit is not None:
                    if esc.get('WEIGHT', 0) + 0.020 > weight_limit:
                        continue

            compatible.append(esc_id)

        return compatible

    def select_optimal_esc(self,
                          motor_current: float,
                          battery_cells: int,
                          weight_limit: Optional[float] = None,
                          require_bec: bool = True) -> Optional[str]:
        """
        Select optimal ESC based on efficiency, weight, and cost

        Scoring: efficiency (2x) - weight penalty (1x per 100g) - cost penalty (0.1x per $)

        Args:
            motor_current: Motor max current (A)
            battery_cells: Battery cell count
            weight_limit: Maximum ESC weight (kg)
            require_bec: Require BEC for avionics

        Returns:
            Best ESC ID or None if no compatible ESC
        """
        compatible = self.get_compatible_escs(motor_current, battery_cells,
                                               weight_limit, require_bec)

        if not compatible:
            return None

        # Score: prioritize efficiency, penalize weight and cost
        best_esc = None
        best_score = float('-inf')

        for esc_id in compatible:
            esc = self.esc_db[esc_id]
            eff = esc.get('EFFICIENCY', 0.90)
            weight = esc.get('WEIGHT', 0.100) * 1000  # kg to g
            cost = esc.get('COST', 100)

            # Check if UBEC needed
            has_bec = esc.get('BEC_VOLTAGE', 0) > 0
            if require_bec and not has_bec:
                weight += 20  # UBEC weight penalty
                cost += 25    # UBEC cost penalty

            score = eff * 2 - weight / 100 - cost / 1000

            if score > best_score:
                best_score = score
                best_esc = esc_id

        return best_esc

    def get_esc(self, esc_id: str) -> Optional[Dict]:
        """Get ESC data by ID"""
        return self.esc_db.get(esc_id)

    def verify_hc4_constraint(self,
                             motor_current: float,
                             esc_id: str) -> Tuple[bool, float]:
        """
        Verify HC-4 constraint: I_motor ≤ 0.8 × I_ESC

        Args:
            motor_current: Motor operating current (A)
            esc_id: ESC identifier

        Returns:
            (satisfied, margin) where margin = (0.8*I_ESC - I_motor) / I_motor
        """
        esc = self.get_esc(esc_id)
        if esc is None:
            return False, -1.0

        i_limit = self.HC4_FACTOR * esc.get('CONT_CURRENT', 0)
        margin = (i_limit - motor_current) / motor_current if motor_current > 0 else 1.0

        return motor_current <= i_limit, margin

    def compute_voltage_drop(self, motor_current: float, esc_id: str) -> float:
        """
        Compute voltage drop across ESC

        V_drop = I_motor × R_esc

        Args:
            motor_current: Motor current (A)
            esc_id: ESC identifier

        Returns:
            Voltage drop (V)
        """
        esc = self.get_esc(esc_id)
        if esc is None:
            return 0.0

        resistance = esc.get('RESISTANCE', 2.0) / 1000  # mΩ to Ω
        return motor_current * resistance

    def compute_power_loss(self, motor_current: float, esc_id: str) -> float:
        """
        Compute power loss in ESC

        P_loss = I² × R

        Args:
            motor_current: Motor current (A)
            esc_id: ESC identifier

        Returns:
            Power loss (W)
        """
        esc = self.get_esc(esc_id)
        if esc is None:
            return 0.0

        resistance = esc.get('RESISTANCE', 2.0) / 1000  # mΩ to Ω
        return motor_current ** 2 * resistance

    def check_bec_capability(self, esc_id: str,
                           avionics_voltage: float = None,
                           avionics_current: float = None) -> Tuple[bool, str]:
        """
        Check if ESC BEC can power avionics

        Args:
            esc_id: ESC identifier
            avionics_voltage: Required voltage (default: 5V)
            avionics_current: Required current (default: 2A)

        Returns:
            (capable, message)
        """
        if avionics_voltage is None:
            avionics_voltage = self.AVIONICS_VOLTAGE
        if avionics_current is None:
            avionics_current = self.AVIONICS_CURRENT

        esc = self.get_esc(esc_id)
        if esc is None:
            return False, "ESC not found"

        bec_voltage = esc.get('BEC_VOLTAGE', 0)
        bec_current = esc.get('BEC_CURRENT', 0)

        if bec_voltage == 0:
            return False, "OPTO ESC - requires separate UBEC (~25g, $25)"

        if abs(bec_voltage - avionics_voltage) > 0.5:
            return False, f"BEC voltage {bec_voltage}V ≠ required {avionics_voltage}V"

        if bec_current < avionics_current:
            return False, f"BEC current {bec_current}A < required {avionics_current}A"

        return True, f"BEC OK: {bec_voltage}V/{bec_current}A"

    def get_statistics(self) -> Dict:
        """Get database statistics"""
        if not self.esc_db:
            return {}

        currents = [e.get('CONT_CURRENT', 0) for e in self.esc_db.values()]
        weights = [e.get('WEIGHT', 0) for e in self.esc_db.values()]
        effs = [e.get('EFFICIENCY', 0) for e in self.esc_db.values()]
        costs = [e.get('COST', 0) for e in self.esc_db.values()]
        becs = [e for e in self.esc_db.values() if e.get('BEC_VOLTAGE', 0) > 0]

        return {
            'total_escs': len(self.esc_db),
            'current_range': f"{min(currents)}-{max(currents)} A",
            'weight_range': f"{min(weights)*1000:.0f}-{max(weights)*1000:.0f} g",
            'avg_efficiency': f"{sum(effs)/len(effs)*100:.1f}%",
            'cost_range': f"${min(costs):.0f}-${max(costs):.0f}",
            'with_bec': len(becs),
            'opto_only': len(self.esc_db) - len(becs),
            'by_size_class': {
                size: len(escs) for size, escs in self.by_size.items()
            }
        }


# Singleton instance
_esc_instance = None


def get_esc_database() -> ESCDatabase:
    """Get global ESC database instance"""
    global _esc_instance
    if _esc_instance is None:
        _esc_instance = ESCDatabase()
    return _esc_instance


# Convenience functions
def get_compatible_escs(motor_current: float, battery_cells: int,
                        weight_limit=None, require_bec=True) -> List[str]:
    """Get compatible ESCs using global database"""
    return get_esc_database().get_compatible_escs(motor_current, battery_cells,
                                                   weight_limit, require_bec)


def select_optimal_esc(motor_current: float, battery_cells: int,
                      weight_limit=None, require_bec=True) -> Optional[str]:
    """Select optimal ESC using global database"""
    return get_esc_database().select_optimal_esc(motor_current, battery_cells,
                                                weight_limit, require_bec)


def verify_hc4(motor_current: float, esc_id: str) -> Tuple[bool, float]:
    """Verify HC-4 constraint using global database"""
    return get_esc_database().verify_hc4_constraint(motor_current, esc_id)


# Example usage and test
if __name__ == "__main__":
    # Initialize
    db = ESCDatabase()

    print("=" * 70)
    print("ESC DATABASE v2.0 TEST")
    print("=" * 70)

    # Statistics
    stats = db.get_statistics()
    print(f"\nDatabase Statistics:")
    print(f"  Total ESCs: {stats['total_escs']}")
    print(f"  Current range: {stats['current_range']}")
    print(f"  Weight range: {stats['weight_range']}")
    print(f"  Avg efficiency: {stats['avg_efficiency']}")
    print(f"  Cost range: {stats['cost_range']}")
    print(f"  With BEC: {stats['with_bec']}")
    print(f"  OPTO only: {stats['opto_only']}")
    print(f"  Size classes: {stats['by_size_class']}")

    # Test scenarios
    print("\n" + "=" * 70)
    print("SELECTION TESTS (with BEC requirement)")
    print("=" * 70)

    test_cases = [
        # (motor_current, battery_cells, description)
        (15, 3, "Small motor, 3S battery"),
        (35, 4, "Medium motor, 4S battery"),
        (60, 6, "Large motor, 6S battery"),
        (90, 8, "XLarge motor, 8S battery"),
    ]

    for motor_curr, cells, desc in test_cases:
        print(f"\n{desc} ({motor_curr}A, {cells}S):")

        # Get compatible ESCs (require BEC)
        compatible = db.get_compatible_escs(motor_curr, cells, require_bec=True)
        print(f"  Compatible (with BEC): {len(compatible)}")

        if compatible:
            # Select optimal
            optimal = db.select_optimal_esc(motor_curr, cells, require_bec=True)
            if optimal:
                esc = db.get_esc(optimal)
                print(f"  → Optimal: {optimal}")
                print(f"     {esc['CONT_CURRENT']}A, {esc['WEIGHT']*1000:.0f}g, {esc['EFFICIENCY']*100:.0f}%")

                # Check BEC
                capable, msg = db.check_bec_capability(optimal)
                print(f"     BEC: {msg}")

                # Voltage drop
                v_drop = db.compute_voltage_drop(motor_curr, optimal)
                p_loss = db.compute_power_loss(motor_curr, optimal)
                print(f"     V_drop: {v_drop:.3f}V, P_loss: {p_loss:.2f}W")

                # Verify HC-4
                satisfied, margin = db.verify_hc4_constraint(motor_curr, optimal)
                print(f"     HC-4: {'✓ OK' if satisfied else '✗ FAIL'} (margin: {margin*100:.1f}%)")

    # BEC analysis
    print("\n" + "=" * 70)
    print("BEC CAPABILITY ANALYSIS")
    print("=" * 70)

    for esc_id in ['T_Motor_P50A', 'T_Motor_V60A', 'KDE_ESC_100A']:
        capable, msg = db.check_bec_capability(esc_id)
        status = "✓" if capable else "✗"
        print(f"{status} {esc_id}: {msg}")

    # Cost comparison
    print("\n" + "=" * 70)
    print("COST COMPARISON (50A ESCs)")
    print("=" * 70)

    esc_50a = [e for e in db.esc_db.keys() if '50A' in e or db.esc_db[e]['CONT_CURRENT'] == 50]
    for esc_id in esc_50a:
        esc = db.get_esc(esc_id)
        print(f"  {esc_id:20s}: ${esc['COST']:.0f} ({esc['WEIGHT']*1000:.0f}g, {esc['EFFICIENCY']*100:.0f}%)")
