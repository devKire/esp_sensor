"""Aplicacao Flask completa para deploy serverless na Vercel."""

from __future__ import annotations

import csv
import io
import sys
from html import escape
from pathlib import Path
from typing import Any

from flask import (
    Flask,
    Response,
    jsonify,
    redirect,
    render_template_string,
    request,
    send_file,
    url_for,
)

ROOT = Path(__file__).resolve().parents[1]
PROJECT_DIR = ROOT / "iot_eficiencia_energetica"

if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from board_view import render_esp32_board  # noqa: E402
from config import (  # noqa: E402
    BASELINE_POWER_KW,
    COMFORT_TEMP_MAX,
    COMFORT_TEMP_MIN,
    CONTROLLER_POWER_KW,
    HVAC_POWER_KW,
    LIGHT_POWER_KW,
    LOW_LIGHT_THRESHOLD,
    MEDIUM_LIGHT_THRESHOLD,
    PIN_MAP,
    PROJECT_NAME,
    SENSOR_LIMITS,
    SIMULATION_INTERVAL_SECONDS,
)
from controller import IoTController  # noqa: E402
from report import CSV_COLUMNS, generate_summary  # noqa: E402

app = Flask(__name__)

controller = IoTController()
manual_defaults: dict[str, float | bool] = {
    "temperature_c": 24.0,
    "humidity_percent": 55.0,
    "light_percent": 35.0,
    "presence": True,
}

PDF_PATH = PROJECT_DIR / "RELATORIO_SOLUCAO_IOT_ESP32.pdf"


def get_current_state() -> dict[str, Any]:
    """Retorna o estado atual, criando um estado visual se necessario."""
    return controller.get_current_state()


def run_cycles(count: int) -> None:
    """Executa ciclos finitos da simulacao sem loop persistente."""
    safe_count = max(1, min(int(count), 120))
    for _ in range(safe_count):
        controller.step()


def parse_float(value: object, default: float, min_value: float, max_value: float) -> float:
    """Converte e limita um numero vindo de formulario."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = default
    return round(max(min_value, min(max_value, number)), 1)


def parse_int(value: object, default: int, min_value: int, max_value: int) -> int:
    """Converte e limita inteiro vindo de formulario."""
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = default
    return max(min_value, min(max_value, number))


def get_manual_readings_from_form() -> dict[str, float | bool]:
    """Valida a leitura manual enviada pela interface Flask."""
    readings: dict[str, float | bool] = {
        "temperature_c": parse_float(
            request.form.get("temperature_c"),
            float(manual_defaults["temperature_c"]),
            SENSOR_LIMITS["temperature"][0],
            SENSOR_LIMITS["temperature"][1],
        ),
        "humidity_percent": parse_float(
            request.form.get("humidity_percent"),
            float(manual_defaults["humidity_percent"]),
            SENSOR_LIMITS["humidity"][0],
            SENSOR_LIMITS["humidity"][1],
        ),
        "light_percent": parse_float(
            request.form.get("light_percent"),
            float(manual_defaults["light_percent"]),
            SENSOR_LIMITS["light"][0],
            SENSOR_LIMITS["light"][1],
        ),
        "presence": request.form.get("presence") in {"on", "true", "True", "1", "sim"},
    }
    manual_defaults.update(readings)
    return readings


def get_history_rows(limit: str) -> list[dict[str, Any]]:
    """Retorna historico filtrado por quantidade exibida."""
    history = controller.history
    if limit == "all":
        return history
    row_count = parse_int(limit, 25, 10, 500)
    return history[-row_count:]


def format_seconds(seconds: int | float) -> str:
    """Formata segundos simulados para exibicao curta."""
    seconds_int = int(seconds)
    minutes, remaining_seconds = divmod(seconds_int, 60)
    if minutes:
        return f"{minutes} min {remaining_seconds} s"
    return f"{remaining_seconds} s"


def format_value(value: object, digits: int = 2) -> str:
    """Formata numeros de forma tolerante a valores ausentes."""
    if isinstance(value, bool):
        return "Sim" if value else "Nao"
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def get_metric_cards(state: dict[str, Any], summary: dict[str, Any]) -> list[dict[str, str]]:
    """Monta cards da visao geral."""
    readings = state.get("readings", {})
    actuators = state.get("actuators", {})
    energy = state.get("energy", {})
    lighting = actuators.get("lighting", {})
    hvac = actuators.get("hvac", {})
    return [
        {
            "label": "Temperatura atual",
            "value": f"{format_value(readings.get('temperature_c'), 1)} C",
            "hint": f"Conforto: {COMFORT_TEMP_MIN:.0f} a {COMFORT_TEMP_MAX:.0f} C",
        },
        {
            "label": "Umidade atual",
            "value": f"{format_value(readings.get('humidity_percent'), 1)}%",
            "hint": "DHT22/DHT11 simulado",
        },
        {
            "label": "Luminosidade",
            "value": f"{format_value(readings.get('light_percent'), 1)}%",
            "hint": f"Baixa < {LOW_LIGHT_THRESHOLD}% | Alta >= {MEDIUM_LIGHT_THRESHOLD}%",
        },
        {
            "label": "Presenca",
            "value": "Detectada" if readings.get("presence") else "Ausente",
            "hint": "Sensor PIR simulado",
        },
        {
            "label": "Iluminacao",
            "value": str(lighting.get("state", "OFF")),
            "hint": str(lighting.get("description", "lampada desligada")),
        },
        {
            "label": "Climatizacao",
            "value": str(hvac.get("state", "OFF")),
            "hint": str(hvac.get("description", "climatizacao desligada")),
        },
        {
            "label": "Consumo atual",
            "value": f"{format_value(energy.get('current_power_kw'), 3)} kW",
            "hint": "Potencia estimada no ciclo",
        },
        {
            "label": "Consumo acumulado",
            "value": f"{format_value(energy.get('automation_energy_kwh'), 6)} kWh",
            "hint": "Cenario com automacao",
        },
        {
            "label": "Consumo sem automacao",
            "value": f"{format_value(energy.get('baseline_energy_kwh'), 6)} kWh",
            "hint": f"Referencia: {BASELINE_POWER_KW:.1f} kW",
        },
        {
            "label": "Economia em kWh",
            "value": f"{format_value(energy.get('savings_kwh'), 6)} kWh",
            "hint": "Baseline - automacao",
        },
        {
            "label": "Economia percentual",
            "value": f"{format_value(energy.get('savings_percent'), 2)}%",
            "hint": "Economia acumulada",
        },
        {
            "label": "Ciclos registrados",
            "value": str(summary.get("total_ciclos", 0)),
            "hint": f"Tempo simulado: {format_seconds(summary.get('tempo_simulado_s', 0))}",
        },
    ]


def chart_empty_message() -> str:
    """Mensagem padrao para graficos sem dados."""
    return '<div class="empty-box">Gere alguns ciclos para visualizar os graficos.</div>'


def scale_points(
    history: list[dict[str, Any]],
    column: str,
    width: int,
    height: int,
    pad_x: int,
    pad_y: int,
) -> tuple[list[tuple[float, float, float, float]], float, float]:
    """Converte serie historica em pontos SVG."""
    values: list[tuple[float, float, float]] = []
    for index, row in enumerate(history):
        raw_value = row.get(column, 0)
        if isinstance(raw_value, bool):
            value = 1.0 if raw_value else 0.0
        else:
            try:
                value = float(raw_value)
            except (TypeError, ValueError):
                value = 0.0
        try:
            cycle = float(row.get("ciclo", index + 1))
        except (TypeError, ValueError):
            cycle = float(index + 1)
        values.append((cycle, value, float(index)))

    if not values:
        return [], 0.0, 0.0

    min_x = min(item[0] for item in values)
    max_x = max(item[0] for item in values)
    min_y = min(item[1] for item in values)
    max_y = max(item[1] for item in values)

    if min_x == max_x:
        min_x -= 1
        max_x += 1
    if min_y == max_y:
        min_y -= 1
        max_y += 1

    plot_width = width - (pad_x * 2)
    plot_height = height - (pad_y * 2)
    points = []
    for cycle, value, index in values:
        x = pad_x + ((cycle - min_x) / (max_x - min_x)) * plot_width
        y = height - pad_y - ((value - min_y) / (max_y - min_y)) * plot_height
        points.append((x, y, value, index))
    return points, min_y, max_y


def render_line_chart_svg(
    history: list[dict[str, Any]],
    column: str,
    title: str,
    unit: str,
    color: str,
    stepped: bool = False,
) -> str:
    """Renderiza grafico de linha SVG sem depender de CDN."""
    if not history:
        return chart_empty_message()

    width, height, pad_x, pad_y = 640, 260, 48, 38
    points, min_y, max_y = scale_points(history, column, width, height, pad_x, pad_y)
    if not points:
        return chart_empty_message()

    if stepped and len(points) > 1:
        path_parts = [f"M {points[0][0]:.1f} {points[0][1]:.1f}"]
        for previous, current in zip(points, points[1:]):
            path_parts.append(f"L {current[0]:.1f} {previous[1]:.1f}")
            path_parts.append(f"L {current[0]:.1f} {current[1]:.1f}")
        path = " ".join(path_parts)
    else:
        path = " ".join(
            f"{'M' if index == 0 else 'L'} {x:.1f} {y:.1f}"
            for index, (x, y, _value, _row_index) in enumerate(points)
        )

    circles = "\n".join(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="{color}">'
        f"<title>{escape(title)}: {value:.2f}</title></circle>"
        for x, y, value, _row_index in points
    )
    last_value = points[-1][2]
    return f"""
    <div class="chart-card">
      <div class="chart-title">{escape(title)}</div>
      <svg viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}">
        <rect x="0" y="0" width="{width}" height="{height}" rx="8" fill="#ffffff"/>
        <line x1="{pad_x}" y1="{height - pad_y}" x2="{width - pad_x}" y2="{height - pad_y}" stroke="#cbd5e1"/>
        <line x1="{pad_x}" y1="{pad_y}" x2="{pad_x}" y2="{height - pad_y}" stroke="#cbd5e1"/>
        <line x1="{pad_x}" y1="{pad_y}" x2="{width - pad_x}" y2="{pad_y}" stroke="#eef2f7"/>
        <line x1="{pad_x}" y1="{(height / 2):.1f}" x2="{width - pad_x}" y2="{(height / 2):.1f}" stroke="#eef2f7"/>
        <text x="{pad_x}" y="24" class="axis-label">min {min_y:.2f} {escape(unit)}</text>
        <text x="{width - pad_x}" y="24" text-anchor="end" class="axis-label">max {max_y:.2f} {escape(unit)}</text>
        <path d="{path}" fill="none" stroke="{color}" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"/>
        {circles}
        <text x="{pad_x}" y="{height - 12}" class="axis-label">ciclos: {len(history)}</text>
        <text x="{width - pad_x}" y="{height - 12}" text-anchor="end" class="axis-label">ultimo: {last_value:.2f} {escape(unit)}</text>
      </svg>
    </div>
    """


def render_energy_chart_svg(history: list[dict[str, Any]]) -> str:
    """Renderiza grafico de consumo com duas series."""
    if not history:
        return chart_empty_message()

    width, height, pad_x, pad_y = 640, 260, 48, 38
    columns = [
        ("consumo_acumulado_kwh", "#0ea5e9", "com automacao"),
        ("consumo_sem_automacao_kwh", "#f97316", "sem automacao"),
    ]
    all_values = []
    for row in history:
        for column, _color, _label in columns:
            try:
                all_values.append(float(row.get(column, 0.0)))
            except (TypeError, ValueError):
                all_values.append(0.0)
    min_y = min(all_values) if all_values else 0.0
    max_y = max(all_values) if all_values else 1.0
    if min_y == max_y:
        max_y += 1

    cycles = [float(row.get("ciclo", index + 1)) for index, row in enumerate(history)]
    min_x = min(cycles) if cycles else 0.0
    max_x = max(cycles) if cycles else 1.0
    if min_x == max_x:
        min_x -= 1
        max_x += 1

    plot_width = width - (pad_x * 2)
    plot_height = height - (pad_y * 2)
    series_paths: list[str] = []
    labels: list[str] = []
    for column, color, label in columns:
        point_strings = []
        for index, row in enumerate(history):
            try:
                value = float(row.get(column, 0.0))
            except (TypeError, ValueError):
                value = 0.0
            cycle = cycles[index]
            x = pad_x + ((cycle - min_x) / (max_x - min_x)) * plot_width
            y = height - pad_y - ((value - min_y) / (max_y - min_y)) * plot_height
            point_strings.append(f"{'M' if index == 0 else 'L'} {x:.1f} {y:.1f}")
        series_paths.append(
            f'<path d="{" ".join(point_strings)}" fill="none" stroke="{color}" '
            f'stroke-width="3" stroke-linejoin="round" stroke-linecap="round"/>'
        )
        labels.append(
            f'<span class="legend-dot" style="background:{color}"></span>{escape(label)}'
        )

    return f"""
    <div class="chart-card">
      <div class="chart-title">Consumo com automacao vs sem automacao</div>
      <div class="chart-legend">{" ".join(labels)}</div>
      <svg viewBox="0 0 {width} {height}" role="img" aria-label="Consumo acumulado">
        <rect x="0" y="0" width="{width}" height="{height}" rx="8" fill="#ffffff"/>
        <line x1="{pad_x}" y1="{height - pad_y}" x2="{width - pad_x}" y2="{height - pad_y}" stroke="#cbd5e1"/>
        <line x1="{pad_x}" y1="{pad_y}" x2="{pad_x}" y2="{height - pad_y}" stroke="#cbd5e1"/>
        <line x1="{pad_x}" y1="{pad_y}" x2="{width - pad_x}" y2="{pad_y}" stroke="#eef2f7"/>
        <line x1="{pad_x}" y1="{(height / 2):.1f}" x2="{width - pad_x}" y2="{(height / 2):.1f}" stroke="#eef2f7"/>
        <text x="{pad_x}" y="24" class="axis-label">min {min_y:.6f} kWh</text>
        <text x="{width - pad_x}" y="24" text-anchor="end" class="axis-label">max {max_y:.6f} kWh</text>
        {"".join(series_paths)}
        <text x="{pad_x}" y="{height - 12}" class="axis-label">ciclos: {len(history)}</text>
      </svg>
    </div>
    """


def build_charts(history: list[dict[str, Any]]) -> dict[str, str]:
    """Monta todos os graficos da versao Flask."""
    return {
        "temperature": render_line_chart_svg(
            history, "temperatura_c", "Temperatura ao longo do tempo", "C", "#ef4444"
        ),
        "humidity": render_line_chart_svg(
            history, "umidade_percent", "Umidade ao longo do tempo", "%", "#0ea5e9"
        ),
        "light": render_line_chart_svg(
            history, "luminosidade_percent", "Luminosidade ao longo do tempo", "%", "#f59e0b"
        ),
        "presence": render_line_chart_svg(
            history, "presenca", "Presenca ao longo do tempo", "", "#22c55e", stepped=True
        ),
        "energy": render_energy_chart_svg(history),
        "savings": render_line_chart_svg(
            history, "economia_percentual", "Economia percentual acumulada", "%", "#16a34a"
        ),
    }


@app.get("/")
def index() -> str:
    """Pagina principal da versao Flask para Vercel."""
    state = get_current_state()
    summary = generate_summary(controller.history)
    history_limit = request.args.get("limit", "25")
    return render_template_string(
        PAGE_TEMPLATE,
        project_name=PROJECT_NAME,
        state=state,
        readings=state.get("readings", {}),
        actuators=state.get("actuators", {}),
        energy=state.get("energy", {}),
        summary=summary,
        metric_cards=get_metric_cards(state, summary),
        board_html=render_esp32_board(state),
        charts=build_charts(controller.history),
        history_rows=get_history_rows(history_limit),
        history_count=len(controller.history),
        history_limit=history_limit,
        csv_columns=CSV_COLUMNS,
        manual=manual_defaults,
        interval=SIMULATION_INTERVAL_SECONDS,
        pin_map=PIN_MAP,
        pdf_available=PDF_PATH.exists(),
        constants={
            "comfort_min": COMFORT_TEMP_MIN,
            "comfort_max": COMFORT_TEMP_MAX,
            "low_light": LOW_LIGHT_THRESHOLD,
            "medium_light": MEDIUM_LIGHT_THRESHOLD,
            "light_power_kw": LIGHT_POWER_KW,
            "hvac_power_kw": HVAC_POWER_KW,
            "controller_power_kw": CONTROLLER_POWER_KW,
            "baseline_power_kw": BASELINE_POWER_KW,
        },
    )


@app.get("/step")
def step() -> Response:
    """Executa um ciclo e volta para a pagina inicial."""
    controller.step()
    return redirect(url_for("index", _anchor="visao-geral"))


@app.get("/run/<int:count>")
def run_many(count: int) -> Response:
    """Executa uma quantidade finita de ciclos e volta para a pagina inicial."""
    run_cycles(count)
    return redirect(url_for("index", _anchor="simulador"))


@app.post("/run-custom")
def run_custom() -> Response:
    """Executa quantidade personalizada de ciclos."""
    run_cycles(parse_int(request.form.get("cycles"), 1, 1, 120))
    return redirect(url_for("index", _anchor="simulador"))


@app.post("/mode")
def set_mode() -> Response:
    """Alterna entre modo automatico e modo manual."""
    controller.set_mode(request.form.get("mode", "automatic") == "automatic")
    return redirect(url_for("index", _anchor="simulador"))


@app.get("/reset")
def reset() -> Response:
    """Reseta a simulacao e volta para a pagina inicial."""
    controller.reset()
    return redirect(url_for("index", _anchor="visao-geral"))


@app.post("/manual")
def manual() -> Response:
    """Aplica leitura manual enviada pelo formulario."""
    readings = get_manual_readings_from_form()
    controller.set_mode(False)
    controller.step(readings)
    return redirect(url_for("index", _anchor="simulador"))


@app.get("/csv")
def csv_download() -> Response:
    """Retorna o historico atual em CSV, mesmo quando estiver vazio."""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=CSV_COLUMNS)
    writer.writeheader()
    writer.writerows(controller.history)
    return Response(
        output.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": "attachment; filename=relatorio_eficiencia_energetica.csv"
        },
    )


@app.get("/pdf")
def pdf_download() -> Response:
    """Baixa o relatorio PDF academico quando o arquivo existe no projeto."""
    if not PDF_PATH.exists():
        return Response("Relatorio PDF nao encontrado no deploy.", status=404)
    return send_file(
        PDF_PATH,
        mimetype="application/pdf",
        as_attachment=True,
        download_name="RELATORIO_SOLUCAO_IOT_ESP32.pdf",
    )


@app.get("/health")
def health() -> Response:
    """Endpoint simples para health check."""
    return jsonify(
        {
            "status": "ok",
            "app": "iot-esp32-flask",
            "cycle": controller.cycle,
            "history_count": len(controller.history),
        }
    )


@app.get("/api/state")
def api_state() -> Response:
    """Retorna o estado atual em JSON para debug e evolucao futura."""
    state = get_current_state()
    return jsonify(
        {
            "cycle": state.get("cycle", 0),
            "mode": state.get("mode", "AUTOMATICO"),
            "status": state.get("status", "online"),
            "readings": state.get("readings", {}),
            "actuators": state.get("actuators", {}),
            "energy": state.get("energy", {}),
            "history_count": len(controller.history),
        }
    )


PAGE_TEMPLATE = """
<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{{ project_name }}</title>
    <style>
      :root {
        --bg: #f4f7fb;
        --panel: #ffffff;
        --panel-soft: #f8fafc;
        --text: #0f172a;
        --muted: #64748b;
        --line: #d7dde8;
        --dark: #0f172a;
        --green: #16a34a;
        --blue: #0ea5e9;
        --orange: #f59e0b;
      }
      * { box-sizing: border-box; }
      html { scroll-behavior: smooth; }
      body {
        margin: 0;
        font-family: Arial, Helvetica, sans-serif;
        background: var(--bg);
        color: var(--text);
      }
      a { color: inherit; }
      header {
        background: #ffffff;
        border-bottom: 1px solid var(--line);
        padding: 26px clamp(18px, 4vw, 48px) 18px;
        position: sticky;
        top: 0;
        z-index: 10;
      }
      h1 {
        margin: 0 0 8px;
        font-size: clamp(24px, 3vw, 36px);
        letter-spacing: 0;
      }
      h2 { margin: 0 0 14px; font-size: 22px; }
      h3 { margin: 0 0 10px; font-size: 17px; }
      p { line-height: 1.55; }
      .subtitle { margin: 0; max-width: 1020px; color: var(--muted); }
      .top-nav, .toolbar, .form-row {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        align-items: end;
      }
      .top-nav { margin-top: 18px; }
      .top-nav a, .button, button {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-height: 38px;
        padding: 9px 13px;
        border-radius: 7px;
        border: 1px solid #cbd5e1;
        background: #ffffff;
        color: var(--text);
        text-decoration: none;
        font-weight: 700;
        font-size: 14px;
        cursor: pointer;
      }
      .button.primary, button.primary { background: var(--dark); color: #ffffff; border-color: var(--dark); }
      .button.warn, button.warn { background: #fff7ed; color: #9a3412; border-color: #fed7aa; }
      .button.success, button.success { background: #dcfce7; color: #166534; border-color: #86efac; }
      main { width: min(1280px, calc(100% - 28px)); margin: 22px auto 60px; }
      section.dashboard-section { padding: 22px 0; scroll-margin-top: 160px; }
      .section-head {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 16px;
        margin-bottom: 14px;
      }
      .section-head p { margin: 4px 0 0; color: var(--muted); }
      .grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; }
      .grid.two { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .card, .metric-card, .panel, .chart-card {
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 14px;
      }
      .metric-card { min-height: 116px; }
      .metric-label { color: var(--muted); font-size: 13px; margin-bottom: 7px; }
      .metric-value {
        font-size: 24px;
        font-weight: 800;
        line-height: 1.15;
        overflow-wrap: anywhere;
      }
      .metric-hint { margin-top: 8px; color: var(--muted); font-size: 12px; }
      .lcd {
        font-family: Consolas, "Courier New", monospace;
        white-space: pre;
        background: #052e1d;
        color: #bbf7d0;
        border: 2px solid #166534;
        border-radius: 8px;
        padding: 14px;
        overflow: auto;
        min-height: 126px;
      }
      .status-list { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
      .status-item {
        background: var(--panel-soft);
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 10px;
      }
      .status-item strong { display: block; margin-bottom: 4px; }
      label {
        display: grid;
        gap: 5px;
        font-size: 13px;
        color: #334155;
        font-weight: 700;
      }
      input, select {
        border: 1px solid #cbd5e1;
        border-radius: 7px;
        min-height: 38px;
        padding: 8px 10px;
        background: #ffffff;
        color: var(--text);
        font: inherit;
      }
      input[type="checkbox"] { width: 22px; min-height: 22px; }
      .manual-grid { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 10px; align-items: end; }
      .scenario-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; }
      .chart-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
      .chart-title { font-weight: 800; margin-bottom: 7px; }
      .chart-card svg { width: 100%; height: auto; display: block; }
      .axis-label { font-size: 11px; fill: #64748b; }
      .chart-legend { display: flex; gap: 12px; flex-wrap: wrap; color: var(--muted); font-size: 12px; margin-bottom: 5px; }
      .legend-dot { display: inline-block; width: 10px; height: 10px; border-radius: 999px; margin-right: 5px; }
      .table-wrap { overflow: auto; border: 1px solid var(--line); border-radius: 8px; background: #ffffff; }
      table { width: 100%; border-collapse: collapse; min-width: 1040px; }
      th, td {
        border-bottom: 1px solid var(--line);
        padding: 9px;
        text-align: left;
        font-size: 13px;
        white-space: nowrap;
      }
      th { background: #e2e8f0; font-weight: 800; }
      .badge {
        display: inline-flex;
        align-items: center;
        border-radius: 999px;
        padding: 4px 8px;
        font-size: 12px;
        font-weight: 800;
        background: #e2e8f0;
        color: #334155;
      }
      .badge.on { background: #dcfce7; color: #166534; }
      .badge.off { background: #f1f5f9; color: #475569; }
      .badge.warn { background: #ffedd5; color: #9a3412; }
      .badge.cool { background: #e0f2fe; color: #075985; }
      .empty-box {
        background: #ffffff;
        border: 1px dashed #cbd5e1;
        color: var(--muted);
        border-radius: 8px;
        padding: 18px;
      }
      .note { color: var(--muted); font-size: 14px; }
      .pin-list { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }
      .pin-list code {
        display: block;
        background: #f1f5f9;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 7px;
      }
      @media (max-width: 980px) {
        header { position: static; }
        section.dashboard-section { scroll-margin-top: 20px; }
        .grid, .grid.two, .chart-grid, .manual-grid, .scenario-grid {
          grid-template-columns: 1fr;
        }
        .status-list, .pin-list { grid-template-columns: 1fr; }
      }
    </style>
  </head>
  <body>
    <header>
      <h1>{{ project_name }}</h1>
      <p class="subtitle">
        Versao Flask para Vercel com simulacao IoT de eficiencia energetica, ESP32 visual,
        sensores, atuadores, LCD, graficos, historico, relatorio, CSV e modo manual.
      </p>
      <nav class="top-nav" aria-label="Navegacao do dashboard">
        <a href="#visao-geral">Visao Geral</a>
        <a href="#placa">Placa ESP32</a>
        <a href="#simulador">Simulador</a>
        <a href="#graficos">Graficos</a>
        <a href="#historico">Historico</a>
        <a href="#relatorio">Relatorio</a>
        <a href="#sobre">Sobre</a>
      </nav>
    </header>

    <main>
      <section id="visao-geral" class="dashboard-section">
        <div class="section-head">
          <div>
            <h2>Visao Geral</h2>
            <p>Estado atual da bancada IoT simulada.</p>
          </div>
          <div class="toolbar">
            <a class="button primary" href="/step">Gerar proxima leitura</a>
            <a class="button" href="/run/10">Rodar 10 ciclos</a>
            <a class="button" href="/run/30">Rodar 30 ciclos</a>
            <a class="button warn" href="/reset">Resetar simulacao</a>
            <a class="button success" href="/csv">Baixar CSV</a>
          </div>
        </div>

        <div class="grid">
          {% for card in metric_cards %}
            <article class="metric-card">
              <div class="metric-label">{{ card.label }}</div>
              <div class="metric-value">{{ card.value }}</div>
              <div class="metric-hint">{{ card.hint }}</div>
            </article>
          {% endfor %}
        </div>

        <div class="grid two" style="margin-top: 12px;">
          <article class="panel">
            <h3>LCD simulado</h3>
            <div class="lcd">{{ state.lcd.text }}</div>
          </article>
          <article class="panel">
            <h3>Status da ESP32</h3>
            <div class="status-list">
              <div class="status-item"><strong>Ciclo atual</strong>{{ state.cycle }}</div>
              <div class="status-item"><strong>Modo atual</strong>{{ state.mode }}</div>
              <div class="status-item"><strong>Status</strong>{{ state.status }}</div>
              <div class="status-item"><strong>Historico</strong>{{ history_count }} registros</div>
              <div class="status-item"><strong>Tempo simulado</strong>{{ summary.tempo_simulado_s }} s</div>
              <div class="status-item"><strong>Intervalo</strong>{{ interval }} s por ciclo</div>
            </div>
          </article>
        </div>
      </section>

      <section id="placa" class="dashboard-section">
        <div class="section-head">
          <div>
            <h2>Placa ESP32</h2>
            <p>Visual HTML/SVG offline com sensores, atuadores, fios, GPIOs e LCD.</p>
          </div>
        </div>
        {{ board_html|safe }}
      </section>

      <section id="simulador" class="dashboard-section">
        <div class="section-head">
          <div>
            <h2>Simulador</h2>
            <p>Execute ciclos finitos ou force cenarios manuais para apresentacao.</p>
          </div>
        </div>

        <div class="grid two">
          <article class="panel">
            <h3>Controles de ciclos</h3>
            <div class="toolbar" style="margin-bottom: 12px;">
              <a class="button primary" href="/step">Proximo ciclo</a>
              <a class="button" href="/run/10">Rodar 10 ciclos</a>
              <a class="button" href="/run/30">Rodar 30 ciclos</a>
              <a class="button warn" href="/reset">Resetar</a>
            </div>
            <form method="post" action="/run-custom" class="form-row">
              <label>
                Quantidade personalizada
                <input type="number" name="cycles" value="5" min="1" max="120">
              </label>
              <button class="primary" type="submit">Rodar ciclos</button>
            </form>
          </article>

          <article class="panel">
            <h3>Modo de operacao</h3>
            <form method="post" action="/mode" class="form-row">
              <label>
                Modo
                <select name="mode">
                  <option value="automatic" {% if state.mode == "AUTOMATICO" %}selected{% endif %}>Automatico</option>
                  <option value="manual" {% if state.mode == "MANUAL" %}selected{% endif %}>Manual</option>
                </select>
              </label>
              <button type="submit">Aplicar modo</button>
            </form>
            <p class="note">
              No modo manual, os ciclos repetem a ultima leitura manual ate que novos valores sejam aplicados.
            </p>
          </article>
        </div>

        <article class="panel" style="margin-top: 12px;">
          <h3>Leitura manual</h3>
          <form method="post" action="/manual">
            <div class="manual-grid">
              <label>
                Temperatura (C)
                <input type="number" step="0.1" min="18" max="32" name="temperature_c" value="{{ manual.temperature_c }}">
              </label>
              <label>
                Umidade (%)
                <input type="number" step="0.5" min="30" max="80" name="humidity_percent" value="{{ manual.humidity_percent }}">
              </label>
              <label>
                Luminosidade (%)
                <input type="number" step="1" min="0" max="100" name="light_percent" value="{{ manual.light_percent }}">
              </label>
              <label>
                Presenca
                <input type="checkbox" name="presence" {% if manual.presence %}checked{% endif %}>
              </label>
              <button class="primary" type="submit">Aplicar leitura manual</button>
            </div>
          </form>

          <h3 style="margin-top: 16px;">Cenarios prontos</h3>
          <div class="scenario-grid">
            <form method="post" action="/manual">
              <input type="hidden" name="temperature_c" value="24">
              <input type="hidden" name="humidity_percent" value="55">
              <input type="hidden" name="light_percent" value="65">
              <input type="hidden" name="presence" value="false">
              <button type="submit">Sem presenca</button>
            </form>
            <form method="post" action="/manual">
              <input type="hidden" name="temperature_c" value="24">
              <input type="hidden" name="humidity_percent" value="55">
              <input type="hidden" name="light_percent" value="20">
              <input type="hidden" name="presence" value="true">
              <button type="submit">Escuro com presenca</button>
            </form>
            <form method="post" action="/manual">
              <input type="hidden" name="temperature_c" value="28.5">
              <input type="hidden" name="humidity_percent" value="55">
              <input type="hidden" name="light_percent" value="55">
              <input type="hidden" name="presence" value="true">
              <button type="submit">Temperatura alta</button>
            </form>
            <form method="post" action="/manual">
              <input type="hidden" name="temperature_c" value="24">
              <input type="hidden" name="humidity_percent" value="55">
              <input type="hidden" name="light_percent" value="75">
              <input type="hidden" name="presence" value="true">
              <button type="submit">Conforto ECO</button>
            </form>
          </div>
        </article>
      </section>

      <section id="graficos" class="dashboard-section">
        <div class="section-head">
          <div>
            <h2>Graficos</h2>
            <p>Series SVG geradas no servidor, sem CDN e sem dependencias de internet.</p>
          </div>
        </div>
        {% if history_count == 0 %}
          <div class="empty-box">Gere alguns ciclos para visualizar os graficos.</div>
        {% else %}
          <div class="chart-grid">
            {{ charts.temperature|safe }}
            {{ charts.humidity|safe }}
            {{ charts.light|safe }}
            {{ charts.presence|safe }}
            {{ charts.energy|safe }}
            {{ charts.savings|safe }}
          </div>
        {% endif %}
      </section>

      <section id="historico" class="dashboard-section">
        <div class="section-head">
          <div>
            <h2>Historico</h2>
            <p>Registros completos usados no CSV, graficos e relatorio.</p>
          </div>
          <form method="get" action="/" class="form-row">
            <label>
              Linhas exibidas
              <select name="limit">
                <option value="10" {% if history_limit == "10" %}selected{% endif %}>Ultimos 10</option>
                <option value="25" {% if history_limit == "25" %}selected{% endif %}>Ultimos 25</option>
                <option value="50" {% if history_limit == "50" %}selected{% endif %}>Ultimos 50</option>
                <option value="all" {% if history_limit == "all" %}selected{% endif %}>Todos</option>
              </select>
            </label>
            <button type="submit">Atualizar</button>
            <a class="button warn" href="/reset">Limpar historico</a>
          </form>
        </div>

        {% if history_rows %}
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  {% for column in csv_columns %}
                    <th>{{ column }}</th>
                  {% endfor %}
                </tr>
              </thead>
              <tbody>
                {% for row in history_rows %}
                  <tr>
                    {% for column in csv_columns %}
                      <td>
                        {% if column == "presenca" %}
                          <span class="badge {{ 'on' if row[column] else 'off' }}">{{ "Sim" if row[column] else "Nao" }}</span>
                        {% elif column == "iluminacao" %}
                          <span class="badge {{ 'off' if row[column] == 'OFF' else 'warn' }}">{{ row[column] }}</span>
                        {% elif column == "climatizacao" %}
                          <span class="badge {{ 'off' if row[column] == 'OFF' else 'cool' }}">{{ row[column] }}</span>
                        {% else %}
                          {{ row[column] }}
                        {% endif %}
                      </td>
                    {% endfor %}
                  </tr>
                {% endfor %}
              </tbody>
            </table>
          </div>
        {% else %}
          <div class="empty-box">O historico esta vazio. Gere um ciclo para registrar dados.</div>
        {% endif %}
      </section>

      <section id="relatorio" class="dashboard-section">
        <div class="section-head">
          <div>
            <h2>Relatorio</h2>
            <p>Resumo consolidado para apresentacao e auditoria academica.</p>
          </div>
          <div class="toolbar">
            <a class="button success" href="/csv">Baixar CSV</a>
            {% if pdf_available %}
              <a class="button" href="/pdf">Baixar PDF academico</a>
            {% endif %}
          </div>
        </div>

        <div class="grid">
          <article class="metric-card"><div class="metric-label">Total de ciclos</div><div class="metric-value">{{ summary.total_ciclos }}</div></article>
          <article class="metric-card"><div class="metric-label">Tempo simulado</div><div class="metric-value">{{ summary.tempo_simulado_s }} s</div></article>
          <article class="metric-card"><div class="metric-label">Tempo com presenca</div><div class="metric-value">{{ summary.tempo_com_presenca_s }} s</div></article>
          <article class="metric-card"><div class="metric-label">Tempo sem presenca</div><div class="metric-value">{{ summary.tempo_sem_presenca_s }} s</div></article>
          <article class="metric-card"><div class="metric-label">Consumo com automacao</div><div class="metric-value">{{ "%.6f"|format(summary.consumo_acumulado_kwh) }} kWh</div></article>
          <article class="metric-card"><div class="metric-label">Consumo sem automacao</div><div class="metric-value">{{ "%.6f"|format(summary.consumo_sem_automacao_kwh) }} kWh</div></article>
          <article class="metric-card"><div class="metric-label">Economia total</div><div class="metric-value">{{ "%.6f"|format(summary.economia_kwh) }} kWh</div></article>
          <article class="metric-card"><div class="metric-label">Economia percentual</div><div class="metric-value">{{ "%.2f"|format(summary.economia_percentual) }}%</div></article>
          <article class="metric-card"><div class="metric-label">Acionamentos iluminacao</div><div class="metric-value">{{ summary.acionamentos_iluminacao }}</div></article>
          <article class="metric-card"><div class="metric-label">Acionamentos climatizacao</div><div class="metric-value">{{ summary.acionamentos_climatizacao }}</div></article>
          <article class="metric-card"><div class="metric-label">Temperatura media</div><div class="metric-value">{{ "%.2f"|format(summary.temperatura_media_c) }} C</div></article>
          <article class="metric-card"><div class="metric-label">Luminosidade media</div><div class="metric-value">{{ "%.2f"|format(summary.luminosidade_media_percent) }}%</div></article>
        </div>

        <article class="panel" style="margin-top: 12px;">
          <h3>Como apresentar</h3>
          <ol>
            <li>Explique o desperdicio de energia em ambientes comerciais.</li>
            <li>Mostre a placa ESP32 e os componentes conectados.</li>
            <li>Rode ciclos automaticos e observe sensores, atuadores e LCD.</li>
            <li>Use cenarios manuais: sem presenca, escuro com presenca e temperatura alta.</li>
            <li>Abra os graficos e compare consumo com automacao e sem automacao.</li>
            <li>Exporte o CSV ou baixe o PDF academico.</li>
          </ol>
        </article>
      </section>

      <section id="sobre" class="dashboard-section">
        <div class="section-head">
          <div>
            <h2>Sobre o Projeto</h2>
            <p>Arquitetura, regras e limitacoes da versao Vercel.</p>
          </div>
        </div>
        <div class="grid two">
          <article class="panel">
            <h3>Problema resolvido</h3>
            <p>
              A solucao reduz desperdicio ao desligar cargas quando nao ha presenca,
              ajustar iluminacao conforme luz natural e acionar climatizacao apenas quando
              a temperatura sai da faixa de conforto.
            </p>
            <h3>Arquitetura</h3>
            <p>
              Sensores simulados -> IoTController como ESP32 -> regras de decisao ->
              atuadores -> LCD, historico, graficos e relatorios.
            </p>
            <h3>Calculo de energia</h3>
            <p>
              O consumo com automacao usa potencia do controlador, iluminacao e climatizacao.
              O consumo sem automacao usa a potencia base de {{ constants.baseline_power_kw }} kW.
            </p>
          </article>
          <article class="panel">
            <h3>Mapa de pinos</h3>
            <div class="pin-list">
              {% for name, gpio in pin_map.items() %}
                <code>{{ name }}: {{ gpio }}</code>
              {% endfor %}
            </div>
            <h3 style="margin-top: 16px;">Limites da versao Vercel</h3>
            <p class="note">
              A Vercel executa funcoes serverless. O estado em memoria pode reiniciar entre
              invocacoes ou novas instancias. Para demonstracao academica, a simulacao funciona
              durante a vida da instancia. Para persistencia real, use banco de dados ou storage externo.
            </p>
            <p class="note">
              A versao local em Streamlit continua disponivel para apresentacoes com widgets
              mais ricos. A versao Flask prioriza compatibilidade com Vercel e funcionamento offline.
            </p>
          </article>
        </div>
      </section>
    </main>
  </body>
</html>
"""
