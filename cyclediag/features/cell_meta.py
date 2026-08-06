"""Cell / protocol metadata helpers — avoid hard-coded currents and thresholds."""

from __future__ import annotations

from dataclasses import dataclass


DEFAULT_Q_RATED_AH = 72.0
DEFAULT_ROUTINE_C_RATE = 0.5
DEFAULT_RPT_C_RATE = 1.0 / 3.0
DEFAULT_DCIR_C_RATE = 1.0


@dataclass
class CellProtocolMeta:
    """Rated capacity and C-rates for derived thresholds."""

    q_rated_ah: float = DEFAULT_Q_RATED_AH
    routine_c_rate: float = DEFAULT_ROUTINE_C_RATE
    rpt_c_rate: float = DEFAULT_RPT_C_RATE
    dcir_c_rate: float = DEFAULT_DCIR_C_RATE

    @property
    def routine_current_a(self) -> float:
        return self.q_rated_ah * self.routine_c_rate

    @property
    def rpt_current_a(self) -> float:
        return self.q_rated_ah * self.rpt_c_rate

    @property
    def dcir_pulse_current_a(self) -> float:
        return self.q_rated_ah * self.dcir_c_rate

    @property
    def per_delta_i_a(self) -> float:
        """ΔI for PER = |I_routine − I_rpt| (same definition as lab 0.5C vs C/3)."""
        return abs(self.routine_current_a - self.rpt_current_a)

    @property
    def rest_current_max_a(self) -> float:
        """~0.7% of 1C — scales with cell size."""
        return max(0.01, 0.007 * self.q_rated_ah)


def rest_current_max_from_q_rated(q_rated_ah: float) -> float:
    return CellProtocolMeta(q_rated_ah=q_rated_ah).rest_current_max_a


def expected_pulse_current_from_q_rated(
    q_rated_ah: float,
    *,
    c_rate: float = DEFAULT_DCIR_C_RATE,
) -> float:
    return q_rated_ah * c_rate


def per_delta_i_from_rates(
    q_rated_ah: float,
    *,
    routine_c_rate: float = DEFAULT_ROUTINE_C_RATE,
    rpt_c_rate: float = DEFAULT_RPT_C_RATE,
) -> float:
    return abs(q_rated_ah * routine_c_rate - q_rated_ah * rpt_c_rate)
