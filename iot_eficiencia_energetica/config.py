"""Configuracoes globais da simulacao IoT com ESP32."""

from __future__ import annotations

from typing import Final

PROJECT_NAME: Final[str] = (
    "Imersao 2 - Solucao IoT para Eficiencia Energetica"
)

SIMULATION_INTERVAL_SECONDS: Final[int] = 2
DEFAULT_TERMINAL_CYCLES: Final[int] = 20
DEFAULT_REPORT_FILENAME: Final[str] = "relatorio_eficiencia_energetica.csv"

COMFORT_TEMP_MIN: Final[float] = 22.0
COMFORT_TEMP_MAX: Final[float] = 25.0
LOW_LIGHT_THRESHOLD: Final[int] = 40
MEDIUM_LIGHT_THRESHOLD: Final[int] = 70

LIGHT_POWER_KW: Final[float] = 0.4
HVAC_POWER_KW: Final[float] = 1.5
CONTROLLER_POWER_KW: Final[float] = 0.02
BASELINE_POWER_KW: Final[float] = 2.2

PIN_MAP: Final[dict[str, str]] = {
    "DHT22": "GPIO 4",
    "LDR": "GPIO 34",
    "PIR": "GPIO 27",
    "LIGHT_RELAY": "GPIO 26",
    "HVAC_RELAY": "GPIO 25",
    "LCD_SDA": "GPIO 21",
    "LCD_SCL": "GPIO 22",
}

COMPONENT_NAMES: Final[dict[str, str]] = {
    "board": "ESP32 DevKit",
    "temperature_humidity_sensor": "Sensor DHT22",
    "light_sensor": "Sensor LDR",
    "presence_sensor": "Sensor PIR",
    "lighting_relay": "Rele de iluminacao",
    "lighting_load": "Lampada LED",
    "hvac_relay": "Rele da climatizacao",
    "hvac_load": "Ar-condicionado",
    "lcd": "LCD I2C 20x4",
}

SENSOR_LIMITS: Final[dict[str, tuple[float, float]]] = {
    "temperature": (18.0, 32.0),
    "humidity": (30.0, 80.0),
    "light": (0.0, 100.0),
}

ALERT_LIMITS: Final[dict[str, float]] = {
    "temperature_low": COMFORT_TEMP_MIN,
    "temperature_high": COMFORT_TEMP_MAX,
    "humidity_low": 35.0,
    "humidity_high": 70.0,
    "light_low": float(LOW_LIGHT_THRESHOLD),
}

LIGHTING_POWER_FACTORS: Final[dict[str, float]] = {
    "OFF": 0.0,
    "LOW": 0.35,
    "MEDIUM": 0.65,
    "HIGH": 1.0,
}

HVAC_POWER_FACTORS: Final[dict[str, float]] = {
    "OFF": 0.0,
    "FAN": 0.2,
    "COOLING": 1.0,
    "HEATING": 0.9,
    "ECO": 0.25,
}
