"""Sensores simulados para o projeto IoT com ESP32."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

from config import SENSOR_LIMITS


def _clamp(value: float, min_value: float, max_value: float) -> float:
    """Mantem um valor dentro dos limites fisicos do sensor."""
    return max(min_value, min(max_value, value))


@dataclass
class TemperatureSensor:
    """Simula a leitura de temperatura de um DHT22/DHT11."""

    min_value: float = SENSOR_LIMITS["temperature"][0]
    max_value: float = SENSOR_LIMITS["temperature"][1]
    value: float = 24.0
    drift: float = 0.0

    def read(self) -> float:
        """Retorna a temperatura atual em graus Celsius."""
        self.drift = _clamp(self.drift + random.uniform(-0.08, 0.08), -0.8, 0.8)
        variation = random.uniform(-0.35, 0.45) + (self.drift * 0.12)

        if random.random() < 0.08:
            variation += random.uniform(-0.9, 1.1)

        self.value = _clamp(self.value + variation, self.min_value, self.max_value)
        return round(self.value, 1)


@dataclass
class HumiditySensor:
    """Simula a leitura de umidade relativa de um DHT22/DHT11."""

    min_value: float = SENSOR_LIMITS["humidity"][0]
    max_value: float = SENSOR_LIMITS["humidity"][1]
    value: float = 55.0

    def read(self) -> float:
        """Retorna a umidade relativa atual em percentual."""
        variation = random.uniform(-1.4, 1.4)
        if random.random() < 0.06:
            variation += random.uniform(-3.0, 3.0)

        self.value = _clamp(self.value + variation, self.min_value, self.max_value)
        return round(self.value, 1)


@dataclass
class LightSensor:
    """Simula um sensor LDR com ciclo natural de luz e pequenas sombras."""

    min_value: float = SENSOR_LIMITS["light"][0]
    max_value: float = SENSOR_LIMITS["light"][1]
    value: float = 65.0
    cycle: int = 0

    def read(self) -> float:
        """Retorna a luminosidade atual em uma escala de 0 a 100."""
        self.cycle += 1
        daylight_wave = 55.0 + 34.0 * math.sin(self.cycle / 7.0)
        shadow_noise = random.uniform(-18.0, 12.0)
        target = _clamp(daylight_wave + shadow_noise, self.min_value, self.max_value)

        self.value = (self.value * 0.68) + (target * 0.32)
        self.value = _clamp(self.value, self.min_value, self.max_value)
        return round(self.value, 1)


@dataclass
class PresenceSensor:
    """Simula um sensor PIR para deteccao de pessoas no ambiente."""

    detected: bool = False
    enter_probability: float = 0.38
    leave_probability: float = 0.18

    def read(self) -> bool:
        """Retorna True quando ha presenca detectada."""
        if self.detected and random.random() < self.leave_probability:
            self.detected = False
        elif not self.detected and random.random() < self.enter_probability:
            self.detected = True

        return self.detected
