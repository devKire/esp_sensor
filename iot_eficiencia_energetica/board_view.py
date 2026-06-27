"""Renderizacao HTML/SVG da placa ESP32 e componentes conectados."""

from __future__ import annotations

from html import escape
from typing import Any

from config import (
    COMFORT_TEMP_MAX,
    COMFORT_TEMP_MIN,
    COMPONENT_NAMES,
    LOW_LIGHT_THRESHOLD,
    MEDIUM_LIGHT_THRESHOLD,
    PIN_MAP,
)


def render_esp32_board(state: dict[str, Any] | None) -> str:
    """Retorna o HTML/SVG completo da visualizacao da ESP32."""
    if not isinstance(state, dict):
        state = {}

    readings = _as_dict(state.get("readings", {}))
    actuators = _as_dict(state.get("actuators", {}))
    energy = _as_dict(state.get("energy", {}))
    pins = _as_dict(state.get("pins", PIN_MAP)) or PIN_MAP
    alerts = _as_dict(state.get("alerts", {}))
    dht_pin = pins.get("DHT22", PIN_MAP["DHT22"])
    ldr_pin = pins.get("LDR", PIN_MAP["LDR"])
    pir_pin = pins.get("PIR", PIN_MAP["PIR"])
    light_relay_pin = pins.get("LIGHT_RELAY", PIN_MAP["LIGHT_RELAY"])
    hvac_relay_pin = pins.get("HVAC_RELAY", PIN_MAP["HVAC_RELAY"])
    lcd_sda_pin = pins.get("LCD_SDA", PIN_MAP["LCD_SDA"])
    lcd_scl_pin = pins.get("LCD_SCL", PIN_MAP["LCD_SCL"])

    temperature = float(readings.get("temperature_c", 0.0))
    humidity = float(readings.get("humidity_percent", 0.0))
    light = float(readings.get("light_percent", 0.0))
    presence = bool(readings.get("presence", False))
    lighting = _as_dict(actuators.get("lighting", {}))
    hvac = _as_dict(actuators.get("hvac", {}))
    lighting_state = str(lighting.get("state", "OFF"))
    lighting_desc = str(lighting.get("description", ""))
    hvac_state = str(hvac.get("state", "OFF"))
    hvac_desc = str(hvac.get("description", ""))

    temp_color = _temperature_color(temperature)
    light_sensor_color = _light_sensor_color(light)
    presence_color = "#22c55e" if presence else "#94a3b8"
    lighting_color = _lighting_color(lighting_state)
    hvac_color = _hvac_color(hvac_state)
    light_wire = lighting_color if lighting_state != "OFF" else "#64748b"
    hvac_wire = hvac_color if hvac_state != "OFF" else "#64748b"

    lcd_lines = state.get("lcd", {}).get("lines", [])
    lcd_lines = list(lcd_lines)[:4] or ["LCD aguardando", "", "", ""]
    lcd_svg = _lcd_lines_svg(lcd_lines)
    pin_table = _pin_table_svg(pins)
    board_pins = _board_pins_svg()
    glow_filter = "filter='url(#glow)'" if lighting_state != "OFF" else ""

    presence_text = "Presenca detectada" if presence else "Sem presenca"
    temp_status = _temperature_status(temperature)
    light_status = "BAIXA" if light < LOW_LIGHT_THRESHOLD else "NORMAL"
    board_status = str(
        state.get("status") or ("online" if state.get("online", True) else "offline")
    ).upper()

    return f"""
<div class="esp32-visual-wrapper">
  <style>
    .esp32-visual-wrapper {{
      width: 100%;
      height: 700px;
      overflow: hidden;
      border: 1px solid #d7dde8;
      border-radius: 8px;
      background: #f8fafc;
      font-family: Arial, Helvetica, sans-serif;
    }}
    .esp32-visual-wrapper svg {{
      display: block;
      width: 100%;
      height: 700px;
    }}
    .label {{ font-size: 14px; fill: #0f172a; font-weight: 700; }}
    .small {{ font-size: 12px; fill: #334155; }}
    .tiny {{ font-size: 10px; fill: #475569; }}
    .card-title {{ font-size: 15px; fill: #0f172a; font-weight: 700; }}
    .card-text {{ font-size: 12px; fill: #334155; }}
    .lcd-text {{ font-family: Consolas, "Courier New", monospace; font-size: 17px; fill: #bbf7d0; }}
    .pin-text {{ font-size: 9px; fill: #e2e8f0; }}
  </style>
  <svg viewBox="0 0 1200 700" role="img" aria-label="Visualizacao da placa ESP32">
    <defs>
      <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
        <feGaussianBlur stdDeviation="6" result="coloredBlur"/>
        <feMerge>
          <feMergeNode in="coloredBlur"/>
          <feMergeNode in="SourceGraphic"/>
        </feMerge>
      </filter>
      <marker id="dot" markerWidth="8" markerHeight="8" refX="4" refY="4">
        <circle cx="4" cy="4" r="3" fill="#475569" />
      </marker>
    </defs>

    <rect x="0" y="0" width="1200" height="700" fill="#f8fafc"/>
    <text x="40" y="34" class="label">{escape(COMPONENT_NAMES["board"])} - simulacao em tempo real</text>
    <text x="40" y="56" class="small">Status: {escape(board_status)} | Ciclo: {state.get("cycle", 0)} | Modo: {escape(str(state.get("mode", "AUTOMATICO")))}</text>

    <path d="M300 130 C390 130 410 162 480 162" stroke="{temp_color}" stroke-width="4" fill="none" marker-end="url(#dot)"/>
    <path d="M300 300 C390 300 410 240 480 240" stroke="{light_sensor_color}" stroke-width="4" fill="none" marker-end="url(#dot)"/>
    <path d="M300 470 C390 470 410 318 480 318" stroke="{presence_color}" stroke-width="4" fill="none" marker-end="url(#dot)"/>
    <path d="M720 180 C800 180 810 110 900 110" stroke="{light_wire}" stroke-width="4" fill="none" marker-end="url(#dot)"/>
    <path d="M720 238 C800 238 810 250 900 250" stroke="{light_wire}" stroke-width="4" fill="none" marker-end="url(#dot)"/>
    <path d="M720 300 C800 300 810 390 900 390" stroke="{hvac_wire}" stroke-width="4" fill="none" marker-end="url(#dot)"/>
    <path d="M720 360 C805 360 810 525 900 525" stroke="{hvac_wire}" stroke-width="4" fill="none" marker-end="url(#dot)"/>
    <path d="M600 480 C600 505 600 525 600 540" stroke="#22c55e" stroke-width="4" fill="none" marker-end="url(#dot)"/>

    {_sensor_card(40, 78, "DHT22", dht_pin, f"{temperature:.1f} C | {humidity:.1f}%", temp_status, temp_color)}
    {_sensor_card(40, 248, "LDR", ldr_pin, f"{light:.1f}% luminosidade", light_status, light_sensor_color)}
    {_sensor_card(40, 418, "PIR", pir_pin, presence_text, "ATIVO" if presence else "INATIVO", presence_color)}

    <rect x="480" y="110" width="240" height="370" rx="18" fill="#102033" stroke="#0f172a" stroke-width="3"/>
    <rect x="528" y="132" width="144" height="42" rx="8" fill="#1f2937" stroke="#94a3b8"/>
    <text x="600" y="158" class="label" fill="#e5f0ff" text-anchor="middle">ESP32 DevKit</text>
    <rect x="545" y="224" width="110" height="104" rx="8" fill="#0f172a" stroke="#64748b"/>
    <text x="600" y="270" class="small" fill="#cbd5e1" text-anchor="middle">MCU</text>
    <text x="600" y="292" class="tiny" fill="#94a3b8" text-anchor="middle">WiFi + BLE</text>
    <rect x="560" y="392" width="80" height="40" rx="8" fill="#334155" stroke="#94a3b8"/>
    <text x="600" y="417" class="tiny" fill="#e2e8f0" text-anchor="middle">USB</text>
    <circle cx="688" cy="142" r="8" fill="#22c55e" filter="url(#glow)"/>
    <text x="600" y="462" class="tiny" fill="#e2e8f0" text-anchor="middle">GPIOs conectados aos modulos</text>
    {board_pins}

    {_actuator_card(900, 58, "Rele iluminacao", light_relay_pin, lighting_state, "Saida digital", lighting_color)}
    {_lamp_svg(900, 195, lighting_state, lighting_desc, light_relay_pin, lighting_color, glow_filter)}
    {_actuator_card(900, 338, "Rele climatizacao", hvac_relay_pin, hvac_state, "Saida digital", hvac_color)}
    {_hvac_svg(900, 475, hvac_state, hvac_desc, hvac_relay_pin, hvac_color)}

    <rect x="390" y="540" width="420" height="126" rx="10" fill="#0b3b2e" stroke="#166534" stroke-width="4"/>
    <text x="410" y="562" class="tiny" fill="#86efac">LCD I2C 20x4 | SDA {escape(lcd_sda_pin)} | SCL {escape(lcd_scl_pin)}</text>
    {lcd_svg}

    {pin_table}

    <rect x="820" y="600" width="330" height="66" rx="8" fill="#ffffff" stroke="#cbd5e1"/>
    <circle cx="840" cy="620" r="7" fill="#22c55e"/><text x="855" y="624" class="tiny">OK / ativo</text>
    <circle cx="940" cy="620" r="7" fill="#f59e0b"/><text x="955" y="624" class="tiny">alerta / acionado</text>
    <circle cx="1070" cy="620" r="7" fill="#94a3b8"/><text x="1085" y="624" class="tiny">desligado</text>
    <text x="840" y="648" class="tiny">Potencia atual: {energy.get("current_power_kw", 0.0)} kW | Economia: {energy.get("savings_percent", 0.0)}%</text>
  </svg>
</div>
"""


def _sensor_card(
    x: int,
    y: int,
    title: str,
    gpio: str,
    reading: str,
    status: str,
    color: str,
) -> str:
    return f"""
    <rect x="{x}" y="{y}" width="260" height="112" rx="8" fill="#ffffff" stroke="{color}" stroke-width="3"/>
    <circle cx="{x + 24}" cy="{y + 26}" r="10" fill="{color}"/>
    <text x="{x + 44}" y="{y + 30}" class="card-title">{escape(title)}</text>
    <text x="{x + 18}" y="{y + 58}" class="card-text">Pino: {escape(gpio)}</text>
    <text x="{x + 18}" y="{y + 80}" class="card-text">Leitura: {escape(reading)}</text>
    <text x="{x + 18}" y="{y + 102}" class="card-text">Status: {escape(status)}</text>
    """


def _as_dict(value: Any) -> dict[str, Any]:
    """Retorna um dicionario valido para estados incompletos."""
    return value if isinstance(value, dict) else {}


def _actuator_card(
    x: int,
    y: int,
    title: str,
    gpio: str,
    state: str,
    text: str,
    color: str,
) -> str:
    return f"""
    <rect x="{x}" y="{y}" width="250" height="96" rx="8" fill="#ffffff" stroke="{color}" stroke-width="3"/>
    <circle cx="{x + 24}" cy="{y + 25}" r="10" fill="{color}"/>
    <text x="{x + 44}" y="{y + 30}" class="card-title">{escape(title)}</text>
    <text x="{x + 18}" y="{y + 56}" class="card-text">GPIO: {escape(gpio)}</text>
    <text x="{x + 18}" y="{y + 78}" class="card-text">Estado: {escape(state)} - {escape(text)}</text>
    """


def _lamp_svg(
    x: int,
    y: int,
    state: str,
    description: str,
    gpio: str,
    color: str,
    glow_filter: str,
) -> str:
    fill = color if state != "OFF" else "#cbd5e1"
    return f"""
    <rect x="{x}" y="{y}" width="250" height="104" rx="8" fill="#ffffff" stroke="{color}" stroke-width="3"/>
    <circle cx="{x + 44}" cy="{y + 38}" r="24" fill="{fill}" stroke="#475569" stroke-width="2" {glow_filter}/>
    <rect x="{x + 30}" y="{y + 62}" width="28" height="14" rx="4" fill="#64748b"/>
    <text x="{x + 82}" y="{y + 30}" class="card-title">Lampada LED</text>
    <text x="{x + 82}" y="{y + 54}" class="card-text">GPIO: {escape(gpio)}</text>
    <text x="{x + 82}" y="{y + 76}" class="card-text">Estado: {escape(state)}</text>
    <text x="{x + 18}" y="{y + 96}" class="tiny">{escape(description)}</text>
    """


def _hvac_svg(
    x: int,
    y: int,
    state: str,
    description: str,
    gpio: str,
    color: str,
) -> str:
    active = state != "OFF"
    blade_color = color if active else "#94a3b8"
    return f"""
    <rect x="{x}" y="{y}" width="250" height="104" rx="8" fill="#ffffff" stroke="{color}" stroke-width="3"/>
    <circle cx="{x + 48}" cy="{y + 45}" r="32" fill="#e2e8f0" stroke="#64748b"/>
    <path d="M{x + 48} {y + 45} L{x + 72} {y + 28} A30 30 0 0 1 {x + 70} {y + 56} Z" fill="{blade_color}"/>
    <path d="M{x + 48} {y + 45} L{x + 24} {y + 30} A30 30 0 0 1 {x + 46} {y + 20} Z" fill="{blade_color}"/>
    <path d="M{x + 48} {y + 45} L{x + 42} {y + 73} A30 30 0 0 1 {x + 22} {y + 52} Z" fill="{blade_color}"/>
    <circle cx="{x + 48}" cy="{y + 45}" r="6" fill="#0f172a"/>
    <text x="{x + 92}" y="{y + 30}" class="card-title">Climatizacao</text>
    <text x="{x + 92}" y="{y + 54}" class="card-text">GPIO: {escape(gpio)}</text>
    <text x="{x + 92}" y="{y + 76}" class="card-text">Estado: {escape(state)}</text>
    <text x="{x + 18}" y="{y + 96}" class="tiny">{escape(description)}</text>
    """


def _lcd_lines_svg(lines: list[str]) -> str:
    output = []
    for index, line in enumerate(lines[:4]):
        output.append(
            f'<text x="420" y="{590 + (index * 22)}" class="lcd-text">'
            f"{escape(str(line))}</text>"
        )
    return "\n".join(output)


def _pin_table_svg(pins: dict[str, str]) -> str:
    rows = list(pins.items())
    texts = []
    for index, (name, gpio) in enumerate(rows):
        texts.append(
            f'<text x="58" y="{588 + (index * 14)}" class="tiny">'
            f"{escape(name)}: {escape(gpio)}</text>"
        )
    return f"""
    <rect x="40" y="560" width="285" height="106" rx="8" fill="#ffffff" stroke="#cbd5e1"/>
    <text x="58" y="578" class="small">Mapa de pinos ESP32</text>
    {"".join(texts)}
    """


def _board_pins_svg() -> str:
    left_labels = ["GPIO 4", "GPIO 34", "GPIO 27", "3V3", "GND"]
    right_labels = ["GPIO 26", "GPIO 25", "GPIO 21", "GPIO 22", "VIN"]
    parts = []

    for index, label in enumerate(left_labels):
        y = 154 + (index * 55)
        parts.append(
            f'<rect x="468" y="{y}" width="12" height="26" rx="3" fill="#94a3b8"/>'
            f'<text x="488" y="{y + 17}" class="pin-text">{escape(label)}</text>'
        )

    for index, label in enumerate(right_labels):
        y = 172 + (index * 48)
        parts.append(
            f'<rect x="720" y="{y}" width="12" height="26" rx="3" fill="#94a3b8"/>'
            f'<text x="664" y="{y + 17}" class="pin-text">{escape(label)}</text>'
        )

    return "\n".join(parts)


def _temperature_color(temperature: float) -> str:
    if temperature < COMFORT_TEMP_MIN:
        return "#f97316"
    if temperature > COMFORT_TEMP_MAX:
        return "#ef4444"
    return "#22c55e"


def _temperature_status(temperature: float) -> str:
    if temperature < COMFORT_TEMP_MIN:
        return "FRIO / HEATING"
    if temperature > COMFORT_TEMP_MAX:
        return "CALOR / COOLING"
    return "CONFORTO"


def _light_sensor_color(light: float) -> str:
    if light < LOW_LIGHT_THRESHOLD:
        return "#f59e0b"
    if light < MEDIUM_LIGHT_THRESHOLD:
        return "#38bdf8"
    return "#22c55e"


def _lighting_color(state: str) -> str:
    colors = {
        "OFF": "#94a3b8",
        "LOW": "#fde047",
        "MEDIUM": "#facc15",
        "HIGH": "#f59e0b",
    }
    return colors.get(state, "#94a3b8")


def _hvac_color(state: str) -> str:
    colors = {
        "OFF": "#94a3b8",
        "FAN": "#38bdf8",
        "COOLING": "#0ea5e9",
        "HEATING": "#f97316",
        "ECO": "#22c55e",
    }
    return colors.get(state, "#94a3b8")
