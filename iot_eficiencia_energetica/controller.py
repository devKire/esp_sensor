"""Controlador central que representa a logica embarcada no ESP32."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from actuators import HVACActuator, HVACState, LightingActuator, LightingState
from config import (
    COMFORT_TEMP_MAX,
    COMFORT_TEMP_MIN,
    LOW_LIGHT_THRESHOLD,
    MEDIUM_LIGHT_THRESHOLD,
    PIN_MAP,
    SIMULATION_INTERVAL_SECONDS,
)
from energy import (
    calculate_baseline_interval_energy_kwh,
    calculate_current_power_kw,
    calculate_energy_snapshot,
    calculate_interval_energy_kwh,
)
from lcd import LCDDisplay
from sensors import HumiditySensor, LightSensor, PresenceSensor, TemperatureSensor


class IoTController:
    """Coordena sensores, regras de automacao, atuadores, LCD e historico."""

    def __init__(self, simulation_interval_seconds: int = SIMULATION_INTERVAL_SECONDS) -> None:
        if simulation_interval_seconds <= 0:
            raise ValueError("O intervalo de simulacao deve ser maior que zero.")

        self.simulation_interval_seconds = simulation_interval_seconds
        self.temperature_sensor = TemperatureSensor()
        self.humidity_sensor = HumiditySensor()
        self.light_sensor = LightSensor()
        self.presence_sensor = PresenceSensor()
        self.lighting = LightingActuator()
        self.hvac = HVACActuator()
        self.lcd = LCDDisplay()
        self.history: list[dict[str, Any]] = []
        self.cycle = 0
        self.automation_energy_kwh = 0.0
        self.baseline_energy_kwh = 0.0
        self.automatic_mode = True
        self.board_status = "aguardando leitura"
        self.current_state: dict[str, Any] | None = self._build_idle_state(
            self.board_status,
        )

    def step(self, manual_readings: dict[str, float | bool] | None = None) -> dict[str, Any]:
        """Executa um ciclo de leitura, decisao, atuacao e registro."""
        if manual_readings is not None:
            self.automatic_mode = False
        self.board_status = "processando"
        self.cycle += 1
        readings = self._get_cycle_readings(manual_readings)
        lighting_state, hvac_state = self._decide_actuators(readings)
        self.lighting.set_state(lighting_state)
        self.hvac.set_state(hvac_state)

        current_power_kw = calculate_current_power_kw(
            self.lighting.state,
            self.hvac.state,
        )
        self.automation_energy_kwh += calculate_interval_energy_kwh(
            current_power_kw,
            self.simulation_interval_seconds,
        )
        self.baseline_energy_kwh += calculate_baseline_interval_energy_kwh(
            self.simulation_interval_seconds,
        )
        energy = calculate_energy_snapshot(
            current_power_kw,
            self.automation_energy_kwh,
            self.baseline_energy_kwh,
        )

        self.board_status = "online"
        state = self._build_state(readings, energy, self.board_status)

        self.lcd.update(state)
        state["lcd"] = self.lcd.as_dict()
        self.current_state = state
        self.history.append(self._build_history_record(state))
        return state

    def set_mode(self, automatic: bool) -> None:
        """Alterna entre modo automatico e modo manual de leituras."""
        self.automatic_mode = automatic
        self.board_status = "aguardando leitura"
        if self.current_state is not None:
            self.current_state["mode"] = self._mode_label()
            self.current_state["status"] = self.board_status

    def get_current_state(self) -> dict[str, Any]:
        """Retorna o estado atual, criando um estado ocioso se necessario."""
        if self.current_state is None:
            self.current_state = self._build_idle_state(self.board_status)
        return self.current_state

    def reset(self) -> None:
        """Reinicia historico, ciclos e consumo acumulado."""
        self.history.clear()
        self.cycle = 0
        self.automation_energy_kwh = 0.0
        self.baseline_energy_kwh = 0.0
        self.automatic_mode = True
        self.lighting.set_state("OFF")
        self.hvac.set_state("OFF")
        self.board_status = "resetada"
        self.current_state = self._build_idle_state(self.board_status)

    def generate_summary(self) -> dict[str, Any]:
        """Gera um resumo simples para terminal ou dashboard."""
        if not self.history:
            return {
                "cycles": 0,
                "automation_energy_kwh": 0.0,
                "baseline_energy_kwh": 0.0,
                "savings_kwh": 0.0,
                "savings_percent": 0.0,
                "average_temperature_c": 0.0,
                "average_light_percent": 0.0,
                "presence_cycles": 0,
            }

        last = self.history[-1]
        cycles = len(self.history)
        average_temperature = sum(row["temperatura_c"] for row in self.history) / cycles
        average_light = sum(row["luminosidade_percent"] for row in self.history) / cycles
        presence_cycles = sum(1 for row in self.history if row["presenca"])

        return {
            "cycles": cycles,
            "automation_energy_kwh": last["consumo_acumulado_kwh"],
            "baseline_energy_kwh": last["consumo_sem_automacao_kwh"],
            "savings_kwh": last["economia_kwh"],
            "savings_percent": last["economia_percentual"],
            "average_temperature_c": round(average_temperature, 2),
            "average_light_percent": round(average_light, 2),
            "presence_cycles": presence_cycles,
        }

    def _read_sensors(self) -> dict[str, float | bool]:
        """Le todos os sensores simulados."""
        return {
            "temperature_c": self.temperature_sensor.read(),
            "humidity_percent": self.humidity_sensor.read(),
            "light_percent": self.light_sensor.read(),
            "presence": self.presence_sensor.read(),
        }

    def _get_cycle_readings(
        self,
        manual_readings: dict[str, float | bool] | None,
    ) -> dict[str, float | bool]:
        """Escolhe leituras automaticas ou leituras manuais de demonstracao."""
        if self.automatic_mode and manual_readings is None:
            return self._read_sensors()

        if manual_readings is not None:
            readings = self._sanitize_manual_readings(manual_readings)
            self._sync_sensor_values(readings)
            return readings

        current = self.get_current_state().get("readings", {})
        readings = self._sanitize_manual_readings(current)
        self._sync_sensor_values(readings)
        return readings

    def _sanitize_manual_readings(
        self,
        readings: dict[str, float | bool],
    ) -> dict[str, float | bool]:
        """Normaliza leituras manuais para evitar valores None ou fora de faixa."""
        return {
            "temperature_c": self._clamp_float(
                readings.get("temperature_c", 24.0),
                18.0,
                32.0,
            ),
            "humidity_percent": self._clamp_float(
                readings.get("humidity_percent", 55.0),
                30.0,
                80.0,
            ),
            "light_percent": self._clamp_float(
                readings.get("light_percent", 65.0),
                0.0,
                100.0,
            ),
            "presence": bool(readings.get("presence", False)),
        }

    def _sync_sensor_values(self, readings: dict[str, float | bool]) -> None:
        """Mantem os sensores simulados coerentes apos uma leitura manual."""
        self.temperature_sensor.value = float(readings["temperature_c"])
        self.humidity_sensor.value = float(readings["humidity_percent"])
        self.light_sensor.value = float(readings["light_percent"])
        self.presence_sensor.detected = bool(readings["presence"])

    def _decide_actuators(
        self,
        readings: dict[str, float | bool],
    ) -> tuple[LightingState, HVACState]:
        """Aplica regras academicas simples de eficiencia energetica."""
        presence = bool(readings["presence"])
        temperature = float(readings["temperature_c"])
        light = float(readings["light_percent"])

        # Sem pessoas no ambiente, as cargas principais sao desligadas.
        if not presence:
            return "OFF", "OFF"

        if light < LOW_LIGHT_THRESHOLD:
            lighting_state: LightingState = "HIGH"
        elif light < MEDIUM_LIGHT_THRESHOLD:
            lighting_state = "LOW"
        else:
            lighting_state = "OFF"

        if temperature > COMFORT_TEMP_MAX:
            hvac_state: HVACState = "COOLING"
        elif temperature < COMFORT_TEMP_MIN:
            hvac_state = "HEATING"
        else:
            hvac_state = "ECO"

        return lighting_state, hvac_state

    def _build_alerts(self, readings: dict[str, float | bool]) -> dict[str, bool]:
        """Indica alertas relevantes para a visualizacao da placa."""
        temperature = float(readings["temperature_c"])
        light = float(readings["light_percent"])
        return {
            "temperature": temperature < COMFORT_TEMP_MIN or temperature > COMFORT_TEMP_MAX,
            "light": light < LOW_LIGHT_THRESHOLD,
            "presence": bool(readings["presence"]),
        }

    def _build_state(
        self,
        readings: dict[str, float | bool],
        energy: dict[str, float],
        status: str,
    ) -> dict[str, Any]:
        """Monta o estado completo usado por dashboard, LCD e SVG."""
        return {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "cycle": self.cycle,
            "mode": self._mode_label(),
            "online": True,
            "status": status,
            "readings": readings,
            "actuators": {
                "lighting": self.lighting.to_dict(),
                "hvac": self.hvac.to_dict(),
            },
            "energy": energy,
            "pins": PIN_MAP,
            "alerts": self._build_alerts(readings),
        }

    def _build_idle_state(self, status: str) -> dict[str, Any]:
        """Cria um estado visual inicial ou resetado sem registrar historico."""
        readings: dict[str, float | bool] = {
            "temperature_c": round(self.temperature_sensor.value, 1),
            "humidity_percent": round(self.humidity_sensor.value, 1),
            "light_percent": round(self.light_sensor.value, 1),
            "presence": self.presence_sensor.detected,
        }
        energy = calculate_energy_snapshot(
            current_power_kw=calculate_current_power_kw(
                self.lighting.state,
                self.hvac.state,
            ),
            automation_energy_kwh=self.automation_energy_kwh,
            baseline_energy_kwh=self.baseline_energy_kwh,
        )
        state = self._build_state(readings, energy, status)
        self.lcd.update(state)
        state["lcd"] = self.lcd.as_dict()
        return state

    def _mode_label(self) -> str:
        """Retorna o nome do modo de operacao atual."""
        return "AUTOMATICO" if self.automatic_mode else "MANUAL"

    def _build_history_record(self, state: dict[str, Any]) -> dict[str, Any]:
        """Achata o estado atual no formato usado pelo CSV."""
        readings = state["readings"]
        energy = state["energy"]
        return {
            "timestamp": state["timestamp"],
            "ciclo": state["cycle"],
            "modo": state["mode"],
            "temperatura_c": readings["temperature_c"],
            "umidade_percent": readings["humidity_percent"],
            "luminosidade_percent": readings["light_percent"],
            "presenca": readings["presence"],
            "iluminacao": state["actuators"]["lighting"]["state"],
            "climatizacao": state["actuators"]["hvac"]["state"],
            "consumo_atual_kw": energy["current_power_kw"],
            "consumo_acumulado_kwh": energy["automation_energy_kwh"],
            "consumo_sem_automacao_kwh": energy["baseline_energy_kwh"],
            "economia_kwh": energy["savings_kwh"],
            "economia_percentual": energy["savings_percent"],
        }

    @staticmethod
    def _clamp_float(value: object, min_value: float, max_value: float) -> float:
        """Converte para float e limita dentro de uma faixa segura."""
        try:
            number = float(value)
        except (TypeError, ValueError):
            number = min_value
        return round(max(min_value, min(max_value, number)), 1)
