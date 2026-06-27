"""Atuadores simulados controlados pela ESP32."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from config import PIN_MAP

LightingState = Literal["OFF", "LOW", "MEDIUM", "HIGH"]
HVACState = Literal["OFF", "FAN", "COOLING", "HEATING", "ECO"]


@dataclass
class LightingActuator:
    """Representa o rele e a carga de iluminacao."""

    gpio: str = PIN_MAP["LIGHT_RELAY"]
    state: LightingState = "OFF"

    _allowed_states = ("OFF", "LOW", "MEDIUM", "HIGH")

    def set_state(self, state: LightingState) -> None:
        """Atualiza o nivel da iluminacao simulada."""
        if state not in self._allowed_states:
            raise ValueError(f"Estado de iluminacao invalido: {state}")
        self.state = state

    @property
    def is_on(self) -> bool:
        """Indica se a lampada esta ligada."""
        return self.state != "OFF"

    @property
    def description(self) -> str:
        """Retorna uma descricao amigavel do estado atual."""
        descriptions = {
            "OFF": "lampada desligada",
            "LOW": "lampada ligada em baixa intensidade",
            "MEDIUM": "lampada ligada em media intensidade",
            "HIGH": "lampada ligada em alta intensidade",
        }
        return descriptions[self.state]

    def to_dict(self) -> dict[str, str | bool]:
        """Converte o atuador para um dicionario serializavel."""
        return {
            "name": "Lampada",
            "state": self.state,
            "gpio": self.gpio,
            "is_on": self.is_on,
            "description": self.description,
        }


@dataclass
class HVACActuator:
    """Representa o rele e a carga de climatizacao."""

    gpio: str = PIN_MAP["HVAC_RELAY"]
    state: HVACState = "OFF"

    _allowed_states = ("OFF", "FAN", "COOLING", "HEATING", "ECO")

    def set_state(self, state: HVACState) -> None:
        """Atualiza o modo da climatizacao simulada."""
        if state not in self._allowed_states:
            raise ValueError(f"Estado de climatizacao invalido: {state}")
        self.state = state

    @property
    def is_active(self) -> bool:
        """Indica se a climatizacao esta consumindo energia."""
        return self.state != "OFF"

    @property
    def description(self) -> str:
        """Retorna uma descricao amigavel do estado atual."""
        descriptions = {
            "OFF": "climatizacao desligada",
            "FAN": "ventilacao simples",
            "COOLING": "resfriando ambiente",
            "HEATING": "aquecendo ambiente",
            "ECO": "mantendo conforto em modo economico",
        }
        return descriptions[self.state]

    def to_dict(self) -> dict[str, str | bool]:
        """Converte o atuador para um dicionario serializavel."""
        return {
            "name": "Climatizacao",
            "state": self.state,
            "gpio": self.gpio,
            "is_active": self.is_active,
            "description": self.description,
        }
