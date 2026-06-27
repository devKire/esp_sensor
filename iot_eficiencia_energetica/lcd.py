"""Display LCD simulado para terminal, dashboard e placa visual."""

from __future__ import annotations


class LCDDisplay:
    """Representa um LCD 20x4 conectado por I2C ao ESP32."""

    def __init__(self, width: int = 20, line_count: int = 4) -> None:
        self.width = width
        self.line_count = line_count
        self.lines = [" " * width for _ in range(line_count)]

    def update(self, state: dict) -> list[str]:
        """Atualiza as linhas do LCD a partir do estado atual do sistema."""
        readings = state.get("readings", {})
        actuators = state.get("actuators", {})
        energy = state.get("energy", {})

        temperature = float(readings.get("temperature_c", 0.0))
        humidity = float(readings.get("humidity_percent", 0.0))
        light_state = str(actuators.get("lighting", {}).get("state", "OFF"))
        hvac_state = str(actuators.get("hvac", {}).get("state", "OFF"))
        presence = "SIM" if readings.get("presence", False) else "NAO"
        savings = float(energy.get("savings_percent", 0.0))
        current_power = float(energy.get("current_power_kw", 0.0))

        raw_lines = [
            f"TEMP:{temperature:04.1f}C UM:{humidity:02.0f}%",
            f"LUZ:{light_state:<4} PRES:{presence}",
            f"AR:{self._short_hvac(hvac_state):<5} ECO:{savings:04.1f}%",
            f"POT:{current_power:04.2f}kW CIC:{state.get('cycle', 0):03}",
        ]
        self.lines = [self._fit(line) for line in raw_lines[: self.line_count]]
        return self.lines

    def to_terminal(self) -> str:
        """Retorna uma representacao em texto para o terminal."""
        border = "+" + ("-" * self.width) + "+"
        body = "\n".join(f"|{line:<{self.width}}|" for line in self.lines)
        return f"{border}\n{body}\n{border}"

    def as_dict(self) -> dict[str, list[str] | str]:
        """Retorna o conteudo do LCD em formatos uteis para a UI."""
        return {
            "lines": self.lines,
            "text": "\n".join(self.lines),
            "terminal": self.to_terminal(),
        }

    def _fit(self, text: str) -> str:
        """Corta ou preenche a linha para caber no LCD."""
        return text[: self.width].ljust(self.width)

    @staticmethod
    def _short_hvac(state: str) -> str:
        aliases = {
            "OFF": "OFF",
            "FAN": "FAN",
            "COOLING": "COOL",
            "HEATING": "HEAT",
            "ECO": "ECO",
        }
        return aliases.get(state, state[:5])
