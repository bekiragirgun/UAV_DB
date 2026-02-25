"""
Propeller Performance Model for HFRPP v07.0
Hybrid strategy: UIUC exact → Scaled → Simple fallback

Author: HFRPP Team
Date: 2026-02-24
"""

import numpy as np
import json
from pathlib import Path

# UIUC database path
UIUC_DB_PATH = Path(__file__).parent / "propeller_ct_cp_lookup.json"


class PropellerPerformanceModel:
    """
    Hybrid propeller performance model with 3-tier strategy:
    1. UIUC exact match (±5% accuracy)
    2. UIUC scaled by D/P ratio (±15% accuracy)
    3. Simple efficiency model (±30% accuracy)
    """

    # Accuracy levels
    ACCURACY_HIGH = 'high'      # UIUC exact
    ACCURACY_MEDIUM = 'medium'  # UIUC scaled
    ACCURACY_LOW = 'low'        # Simple model

    def __init__(self, uiuc_db_path=None):
        """Load UIUC propeller database"""
        self.uiuc_db = self._load_uiuc_db(uiuc_db_path or UIUC_DB_PATH)

        # Build index for faster lookup
        self._build_index()

        # Statistics
        self.stats = {
            'exact_match': 0,
            'scaled_match': 0,
            'simple_fallback': 0,
            'total': 0
        }

    def _load_uiuc_db(self, path):
        """Load UIUC CT/CP database"""
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: UIUC DB not found at {path}")
            return {}

    def _build_index(self):
        """Build lookup index by diameter and pitch"""
        self.by_diameter = {}
        self.by_ratio = {}

        for key, prop in self.uiuc_db.items():
            d = prop.get('d_mm', 0)
            p = prop.get('p_mm', 0)
            ratio = p / d if d > 0 else 0

            # Index by diameter (range ±10%)
            if d not in self.by_diameter:
                self.by_diameter[d] = []
            self.by_diameter[d].append(prop)

            # Index by pitch/diameter ratio
            ratio_key = round(ratio, 2)
            if ratio_key not in self.by_ratio:
                self.by_ratio[ratio_key] = []
            self.by_ratio[ratio_key].append(prop)

    def get_performance(self, diameter_mm, pitch_mm, brand=None):
        """
        Get propeller performance coefficients

        Args:
            diameter_mm: Propeller diameter in mm
            pitch_mm: Propeller pitch in mm
            brand: Manufacturer (optional, for exact match)

        Returns:
            dict with ct_coeffs, cp_coeffs, accuracy, method
        """
        self.stats['total'] += 1

        # Round to nearest mm for matching
        d = round(diameter_mm)
        p = round(pitch_mm)
        key = f"{d}x{p}"

        # Level 1: Exact match
        if key in self.uiuc_db:
            self.stats['exact_match'] += 1
            prop = self.uiuc_db[key]
            return {
                'method': 'uiuc_exact',
                'ct_coeffs': prop.get('ct_coeffs'),
                'cp_coeffs': prop.get('cp_coeffs'),
                'j_range': prop.get('j_range', [0.1, 0.8]),
                'accuracy': self.ACCURACY_HIGH,
                'r2_ct': prop.get('ct_r2'),
                'r2_cp': prop.get('cp_r2'),
                'source_prop': key
            }

        # Level 2: Scaled from closest UIUC
        closest = self._find_closest(d, p)
        if closest:
            pd_error = abs(closest['p_mm'] / closest['d_mm'] - p / d)
            if pd_error < 0.15:  # 15% tolerance
                self.stats['scaled_match'] += 1
                scaled = self._scale_performance(closest, d, p)
                return {
                    'method': 'uiuc_scaled',
                    'ct_coeffs': scaled['ct_coeffs'],
                    'cp_coeffs': scaled['cp_coeffs'],
                    'j_range': closest.get('j_range', [0.1, 0.8]),
                    'accuracy': self.ACCURACY_MEDIUM,
                    'source_prop': f"{closest['d_mm']}x{closest['p_mm']}",
                    'pd_error': pd_error
                }

        # Level 3: Simple model fallback
        self.stats['simple_fallback'] += 1
        return {
            'method': 'simple',
            'eta_total': 0.50,  # Conservative efficiency
            'accuracy': self.ACCURACY_LOW,
            'note': 'Using simplified efficiency model'
        }

    def _find_closest(self, d, p):
        """
        Find closest UIUC propeller by diameter and pitch/diameter ratio.

        SCALING VALIDATION: Only match when P/D ratio is within ±5%.
        Validation shows scaling errors exceed 40% when P/D differs by >5%.
        See: propeller_scaling_validation_report.md
        """
        target_pd = p / d if d > 0 else 0
        best = None
        min_score = float('inf')

        # STRICT TOLERANCE: P/D ratio must be within ±5%
        # Based on validation: scaling works ±5% P/D, fails beyond
        PD_TOLERANCE = 0.05

        for prop in self.uiuc_db.values():
            prop_d = prop.get('d_mm', 0)
            prop_p = prop.get('p_mm', 0)
            if prop_d == 0:
                continue

            prop_pd = prop_p / prop_d

            # P/D difference (normalized)
            pd_diff = abs(prop_pd - target_pd) / target_pd if target_pd > 0 else 1

            # STRICT: Skip if P/D ratio differs by more than 5%
            if pd_diff > PD_TOLERANCE:
                continue

            # Size difference (only criterion after P/D filter)
            size_diff = abs(prop_d - d) / d

            if size_diff < min_score:
                min_score = size_diff
                best = prop

        # Also require diameter within ±30% for physical similarity
        return best if min_score < 0.3 else None

    def _scale_performance(self, base_prop, target_d, target_p):
        """
        Scale CT/CP coefficients using NON-LINEAR Reynolds number correction.

        Scaling model (based on Deters et al. 2014):
        - Reynolds number: Re ∝ D × V × chord
        - CT correction: CT_new = CT_base × (Re_new/Re_base)^(-n(Re))
        - CP correction: CP_new = CP_base × (Re_new/Re_base)^(-m(Re))

        KEY: Reynolds exponent is NOT constant - varies with Re regime:
          - Re < 50k: n = 0.15 (laminar, separation bubble)
          - 50k < Re < 100k: n transitions 0.15 → 0.08
          - Re > 100k: n = 0.08 (turbulent)

        This captures the non-linear dependence of CT on Reynolds number.
        """
        base_d = base_prop.get('d_mm', 1)
        base_p = base_prop.get('p_mm', 1)

        # Estimate Reynolds numbers
        # Re = rho * omega * r^2 / mu ≈ rpm * D * (P/D) / const
        # We use relative Re, so constants cancel
        Re_base = self._estimate_reynolds(base_d, base_p)
        Re_target = self._estimate_reynolds(target_d, target_p)

        # NON-LINEAR: Re-dependent exponent
        n_ct = self._reynolds_exponent_ct(Re_base, Re_target)
        n_cp = self._reynolds_exponent_cp(Re_base, Re_target)

        # Scale coefficients with Re-dependent exponent
        re_ratio = Re_target / Re_base
        ct_scale = re_ratio ** (-n_ct)
        cp_scale = re_ratio ** (-n_cp)

        ct_coeffs = base_prop.get('ct_coeffs', [])
        cp_coeffs = base_prop.get('cp_coeffs', [])

        scaled_ct = [c * ct_scale for c in ct_coeffs]
        scaled_cp = [c * cp_scale for c in cp_coeffs]

        return {
            'ct_coeffs': scaled_ct,
            'cp_coeffs': scaled_cp,
            'scale_factor': ct_scale,
            're_base': Re_base,
            're_target': Re_target,
            'n_ct': n_ct,
            'n_cp': n_cp
        }

    def _estimate_reynolds(self, d_mm, p_mm):
        """
        Estimate Reynolds number (relative, for scaling only)

        Re ∝ D × V_tip × chord ∝ D × (rpm × D) × (P/D) ∝ rpm × P × D

        Since rpm is constant for scaling comparison:
        Re ∝ P × D
        """
        return p_mm * d_mm  # Relative Re, constants omitted

    def _reynolds_exponent_ct(self, Re1, Re2):
        """
        NON-LINEAR Reynolds exponent for CT scaling.

        Based on Deters et al. (2014) Figure 9:
        - Re < 50k: n = 0.15 (steep, laminar separation)
        - 50-100k: n transitions 0.15 → 0.08
        - Re > 100k: n = 0.08 (shallow, turbulent)

        This captures the non-linear CT dependence on Re.
        """
        Re_avg = (Re1 + Re2) / 2

        if Re_avg < 50000:
            return 0.15
        elif Re_avg < 100000:
            # Non-linear transition region
            # n decreases from 0.15 to 0.08
            fraction = (Re_avg - 50000) / 50000
            return 0.15 - 0.07 * fraction
        else:
            return 0.08

    def _reynolds_exponent_cp(self, Re1, Re2):
        """
        NON-LINEAR Reynolds exponent for CP scaling.

        CP is less sensitive to Re than CT.
        Based on Deters et al. (2014):
        - Re < 50k: m = 0.08
        - 50-100k: m transitions 0.08 → 0.04
        - Re > 100k: m = 0.04
        """
        Re_avg = (Re1 + Re2) / 2

        if Re_avg < 50000:
            return 0.08
        elif Re_avg < 100000:
            fraction = (Re_avg - 50000) / 50000
            return 0.08 - 0.04 * fraction
        else:
            return 0.04

    def compute_thrust(self, perf, J, rpm, diameter_m, rho=1.225):
        """
        Compute thrust using performance model

        Args:
            perf: Performance dict from get_performance()
            J: Advance ratio
            rpm: Propeller RPM
            diameter_m: Diameter in meters
            rho: Air density (kg/m³)

        Returns:
            Thrust in Newtons
        """
        if perf['method'] == 'simple':
            # Simple model: T = eta * P / V
            # Need power input - return placeholder
            return None

        n = rpm / 60.0  # rps
        CT = np.polyval(perf['ct_coeffs'], J)
        T = CT * rho * n**2 * diameter_m**4
        return T

    def compute_power(self, perf, J, rpm, diameter_m, rho=1.225):
        """
        Compute power using performance model

        Args:
            perf: Performance dict from get_performance()
            J: Advance ratio
            rpm: Propeller RPM
            diameter_m: Diameter in meters
            rho: Air density (kg/m³)

        Returns:
            Power in Watts
        """
        if perf['method'] == 'simple':
            return None

        n = rpm / 60.0  # rps
        CP = np.polyval(perf['cp_coeffs'], J)
        P = CP * rho * n**3 * diameter_m**5
        return P

    def compute_efficiency(self, perf, J):
        """Compute propeller efficiency eta = J * CT / CP"""
        if perf['method'] == 'simple':
            return perf.get('eta_total', 0.50)

        CT = np.polyval(perf['ct_coeffs'], J)
        CP = np.polyval(perf['cp_coeffs'], J)
        return J * CT / CP if CP > 0 else 0

    def get_statistics(self):
        """Get usage statistics"""
        total = self.stats['total'] or 1
        return {
            'exact_match_pct': 100 * self.stats['exact_match'] / total,
            'scaled_match_pct': 100 * self.stats['scaled_match'] / total,
            'simple_fallback_pct': 100 * self.stats['simple_fallback'] / total,
            'total_queries': total
        }

    def reset_statistics(self):
        """Reset usage counters"""
        self.stats = {
            'exact_match': 0,
            'scaled_match': 0,
            'simple_fallback': 0,
            'total': 0
        }


# Singleton instance
_model_instance = None


def get_propeller_model():
    """Get global propeller performance model instance"""
    global _model_instance
    if _model_instance is None:
        _model_instance = PropellerPerformanceModel()
    return _model_instance


# Convenience functions
def get_propeller_performance(diameter_mm, pitch_mm, brand=None):
    """Get propeller performance using global model"""
    return get_propeller_model().get_performance(diameter_mm, pitch_mm, brand)


def compute_thrust(perf, J, rpm, diameter_m, rho=1.225):
    """Compute thrust using global model"""
    return get_propeller_model().compute_thrust(perf, J, rpm, diameter_m, rho)


def compute_power(perf, J, rpm, diameter_m, rho=1.225):
    """Compute power using global model"""
    return get_propeller_model().compute_power(perf, J, rpm, diameter_m, rho)


def compute_efficiency(perf, J):
    """Compute efficiency using global model"""
    return get_propeller_model().compute_efficiency(perf, J)


# Example usage
if __name__ == "__main__":
    # Initialize model
    model = PropellerPerformanceModel()

    print("=" * 60)
    print("PROPELLER PERFORMANCE MODEL TEST")
    print("=" * 60)

    # Test cases
    test_props = [
        (330, 254, "APC 13x10"),      # Exact match
        (356, 229, "Master 14x9"),    # Close match
        (406, 203, "Unknown 16x8"),   # Close match
        (559, 254, "Generic 22x10"),  # Scaled
        (229, 102, "Unknown 9x4"),    # Scaled
        (254, 80,  "Unknown 10x3.2"), # Fallback
    ]

    for d, p, name in test_props:
        perf = model.get_performance(d, p)

        print(f"\n{name} ({d}x{p} mm):")
        print(f"  Method: {perf['method']}")
        print(f"  Accuracy: {perf['accuracy']}")

        if perf['method'] != 'simple':
            # Compute at cruise conditions
            V_cruise = 20  # m/s
            rpm = 8000
            D_m = d / 1000
            J = V_cruise / ((rpm/60) * D_m)

            T = model.compute_thrust(perf, J, rpm, D_m)
            P = model.compute_power(perf, J, rpm, D_m)
            eta = model.compute_efficiency(perf, J)

            print(f"  Source: {perf.get('source_prop', 'N/A')}")
            print(f"  J = {J:.3f}")
            print(f"  Thrust = {T:.1f} N ({T/9.81:.2f} kg)")
            print(f"  Power = {P:.1f} W")
            print(f"  Efficiency = {eta:.1%}")

            if 'pd_error' in perf:
                print(f"  P/D error: {perf['pd_error']*100:.1f}%")

    # Statistics
    print("\n" + "=" * 60)
    print("STATISTICS")
    print("=" * 60)
    stats = model.get_statistics()
    print(f"  Exact match: {stats['exact_match_pct']:.1f}%")
    print(f"  Scaled match: {stats['scaled_match_pct']:.1f}%")
    print(f"  Simple fallback: {stats['simple_fallback_pct']:.1f}%")
