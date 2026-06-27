"""Calculos de consumo e economia de energia."""

from __future__ import annotations

from config import (
    BASELINE_POWER_KW,
    CONTROLLER_POWER_KW,
    HVAC_POWER_FACTORS,
    HVAC_POWER_KW,
    LIGHT_POWER_KW,
    LIGHTING_POWER_FACTORS,
)


def calculate_current_power_kw(lighting_state: str, hvac_state: str) -> float:
    """Calcula a potencia atual estimada em kW."""
    lighting_factor = LIGHTING_POWER_FACTORS.get(lighting_state, 0.0)
    hvac_factor = HVAC_POWER_FACTORS.get(hvac_state, 0.0)

    return (
        CONTROLLER_POWER_KW
        + (LIGHT_POWER_KW * lighting_factor)
        + (HVAC_POWER_KW * hvac_factor)
    )


def calculate_interval_energy_kwh(power_kw: float, interval_seconds: int) -> float:
    """Converte potencia em consumo para um intervalo de simulacao."""
    if interval_seconds <= 0:
        raise ValueError("O intervalo de simulacao deve ser positivo.")
    return power_kw * (interval_seconds / 3600)


def calculate_baseline_interval_energy_kwh(interval_seconds: int) -> float:
    """Calcula o consumo sem automacao para o mesmo intervalo."""
    return calculate_interval_energy_kwh(BASELINE_POWER_KW, interval_seconds)


def calculate_savings_kwh(
    baseline_energy_kwh: float,
    automation_energy_kwh: float,
) -> float:
    """Calcula a economia acumulada em kWh."""
    return max(0.0, baseline_energy_kwh - automation_energy_kwh)


def calculate_savings_percentage(
    baseline_energy_kwh: float,
    automation_energy_kwh: float,
) -> float:
    """Calcula a economia percentual acumulada."""
    if baseline_energy_kwh <= 0:
        return 0.0
    savings = calculate_savings_kwh(baseline_energy_kwh, automation_energy_kwh)
    return (savings / baseline_energy_kwh) * 100


def calculate_energy_snapshot(
    current_power_kw: float,
    automation_energy_kwh: float,
    baseline_energy_kwh: float,
) -> dict[str, float]:
    """Gera um resumo energetico pronto para dashboard e relatorio."""
    savings_kwh = calculate_savings_kwh(
        baseline_energy_kwh,
        automation_energy_kwh,
    )
    savings_percent = calculate_savings_percentage(
        baseline_energy_kwh,
        automation_energy_kwh,
    )

    return {
        "current_power_kw": round(current_power_kw, 4),
        "automation_energy_kwh": round(automation_energy_kwh, 6),
        "baseline_energy_kwh": round(baseline_energy_kwh, 6),
        "savings_kwh": round(savings_kwh, 6),
        "savings_percent": round(savings_percent, 2),
    }
