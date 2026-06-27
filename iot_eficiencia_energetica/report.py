"""Geracao de historico, resumo e relatorio CSV."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from config import DEFAULT_REPORT_FILENAME, SIMULATION_INTERVAL_SECONDS

CSV_COLUMNS = [
    "timestamp",
    "ciclo",
    "modo",
    "temperatura_c",
    "umidade_percent",
    "luminosidade_percent",
    "presenca",
    "iluminacao",
    "climatizacao",
    "consumo_atual_kw",
    "consumo_acumulado_kwh",
    "consumo_sem_automacao_kwh",
    "economia_kwh",
    "economia_percentual",
]


def history_to_dataframe(history: list[dict[str, Any]]) -> pd.DataFrame:
    """Converte o historico em um DataFrame do Pandas."""
    return pd.DataFrame(history, columns=CSV_COLUMNS)


def export_csv(
    history: list[dict[str, Any]],
    filename: str | Path = DEFAULT_REPORT_FILENAME,
) -> Path:
    """Exporta o historico para CSV e retorna o caminho gerado."""
    dataframe = history_to_dataframe(history)
    path = Path(filename)
    dataframe.to_csv(path, index=False, encoding="utf-8")
    return path


def generate_summary(history: list[dict[str, Any]]) -> dict[str, Any]:
    """Gera um resumo consolidado a partir do historico."""
    if not history:
        return {
            "total_ciclos": 0,
            "tempo_simulado_s": 0,
            "tempo_com_presenca_s": 0,
            "tempo_sem_presenca_s": 0,
            "consumo_acumulado_kwh": 0.0,
            "consumo_sem_automacao_kwh": 0.0,
            "economia_kwh": 0.0,
            "economia_percentual": 0.0,
            "temperatura_media_c": 0.0,
            "luminosidade_media_percent": 0.0,
            "ciclos_com_presenca": 0,
            "acionamentos_iluminacao": 0,
            "acionamentos_climatizacao": 0,
        }

    dataframe = history_to_dataframe(history)
    last = dataframe.iloc[-1]
    cycles = int(len(dataframe))
    presence_cycles = int(dataframe["presenca"].sum())

    return {
        "total_ciclos": cycles,
        "tempo_simulado_s": cycles * SIMULATION_INTERVAL_SECONDS,
        "tempo_com_presenca_s": presence_cycles * SIMULATION_INTERVAL_SECONDS,
        "tempo_sem_presenca_s": (cycles - presence_cycles) * SIMULATION_INTERVAL_SECONDS,
        "consumo_acumulado_kwh": float(last["consumo_acumulado_kwh"]),
        "consumo_sem_automacao_kwh": float(last["consumo_sem_automacao_kwh"]),
        "economia_kwh": float(last["economia_kwh"]),
        "economia_percentual": float(last["economia_percentual"]),
        "temperatura_media_c": round(float(dataframe["temperatura_c"].mean()), 2),
        "luminosidade_media_percent": round(
            float(dataframe["luminosidade_percent"].mean()),
            2,
        ),
        "ciclos_com_presenca": presence_cycles,
        "acionamentos_iluminacao": _count_activations(dataframe["iluminacao"], "OFF"),
        "acionamentos_climatizacao": _count_activations(dataframe["climatizacao"], "OFF"),
    }


def _count_activations(series: pd.Series, off_state: str) -> int:
    """Conta transicoes de desligado para ativo."""
    activations = 0
    previous_active = False
    for value in series:
        active = str(value) != off_state
        if active and not previous_active:
            activations += 1
        previous_active = active
    return activations
