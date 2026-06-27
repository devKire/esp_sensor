"""Entrypoint Flask compativel com Vercel para o simulador IoT ESP32."""

try:
    from .web_app import app
except ImportError:
    from web_app import app


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)


_LEGACY_BODY_NOT_EXECUTED = r'''
from __future__ import annotations

import csv
import io
import sys
from pathlib import Path
from typing import Any

from flask import Flask, Response, redirect, render_template_string, url_for

ROOT = Path(__file__).resolve().parents[1]
PROJECT_DIR = ROOT / "iot_eficiencia_energetica"

if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from board_view import render_esp32_board  # noqa: E402
from config import PROJECT_NAME, SIMULATION_INTERVAL_SECONDS  # noqa: E402
from controller import IoTController  # noqa: E402
from report import CSV_COLUMNS, generate_summary  # noqa: E402

app = Flask(__name__)

controller = IoTController()


def get_current_state() -> dict[str, Any]:
    """Retorna o estado atual, criando um estado visual se necessário."""
    return controller.get_current_state()


def run_cycles(count: int) -> None:
    """Executa ciclos finitos da simulação."""
    safe_count = max(1, min(count, 30))
    for _ in range(safe_count):
        controller.step()


@app.get("/")
def index() -> str:
    """Página principal da versão Flask para Vercel."""
    state = get_current_state()
    readings = state["readings"]
    actuators = state["actuators"]
    energy = state["energy"]
    summary = generate_summary(controller.history)
    board_html = render_esp32_board(state)
    history_rows = list(reversed(controller.history[-12:]))

    return render_template_string(
        PAGE_TEMPLATE,
        project_name=PROJECT_NAME,
        state=state,
        readings=readings,
        actuators=actuators,
        energy=energy,
        summary=summary,
        board_html=board_html,
        history_rows=history_rows,
        history_count=len(controller.history),
        interval=SIMULATION_INTERVAL_SECONDS,
    )


@app.get("/step")
def step() -> Response:
    """Executa um ciclo e volta para a página inicial."""
    controller.step()
    return redirect(url_for("index"))


@app.get("/run/<int:count>")
def run_many(count: int) -> Response:
    """Executa 10 ou 30 ciclos e volta para a página inicial."""
    run_cycles(count)
    return redirect(url_for("index"))


@app.get("/reset")
def reset() -> Response:
    """Reseta a simulação e volta para a página inicial."""
    controller.reset()
    return redirect(url_for("index"))


@app.get("/csv")
def csv_download() -> Response:
    """Retorna o histórico atual em CSV."""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=CSV_COLUMNS)
    writer.writeheader()
    writer.writerows(controller.history)

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=relatorio_eficiencia_energetica.csv"
        },
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
        --bg: #f8fafc;
        --text: #0f172a;
        --muted: #64748b;
        --line: #d7dde8;
        --card: #ffffff;
        --blue: #0ea5e9;
        --green: #22c55e;
        --orange: #f59e0b;
        --red: #ef4444;
      }
      * { box-sizing: border-box; }
      body {
        margin: 0;
        font-family: Arial, Helvetica, sans-serif;
        background: var(--bg);
        color: var(--text);
      }
      header {
        padding: 28px clamp(18px, 4vw, 48px) 18px;
        border-bottom: 1px solid var(--line);
        background: #ffffff;
      }
      h1 {
        margin: 0 0 8px;
        font-size: clamp(24px, 3vw, 36px);
        letter-spacing: 0;
      }
      p { line-height: 1.55; }
      main {
        width: min(1220px, calc(100% - 28px));
        margin: 22px auto 46px;
      }
      .toolbar {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin: 18px 0;
      }
      .button {
        display: inline-block;
        padding: 10px 14px;
        border-radius: 7px;
        border: 1px solid #cbd5e1;
        background: #ffffff;
        color: var(--text);
        text-decoration: none;
        font-weight: 700;
        font-size: 14px;
      }
      .button.primary {
        background: #0f172a;
        color: #ffffff;
        border-color: #0f172a;
      }
      .button.warn {
        background: #fff7ed;
        border-color: #fed7aa;
        color: #9a3412;
      }
      .grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 12px;
      }
      .card {
        background: var(--card);
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 14px;
      }
      .card .label {
        color: var(--muted);
        font-size: 13px;
        margin-bottom: 6px;
      }
      .card .value {
        font-size: 24px;
        font-weight: 800;
      }
      .section {
        margin-top: 24px;
      }
      .section h2 {
        margin: 0 0 12px;
        font-size: 20px;
      }
      .lcd {
        font-family: Consolas, "Courier New", monospace;
        white-space: pre;
        background: #052e1d;
        color: #bbf7d0;
        border: 2px solid #166534;
        border-radius: 8px;
        padding: 14px;
        overflow: auto;
      }
      .two-col {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 14px;
      }
      table {
        width: 100%;
        border-collapse: collapse;
        background: #ffffff;
        border: 1px solid var(--line);
        border-radius: 8px;
        overflow: hidden;
      }
      th, td {
        border-bottom: 1px solid var(--line);
        padding: 9px;
        text-align: left;
        font-size: 13px;
      }
      th {
        background: #e2e8f0;
        font-weight: 800;
      }
      .note {
        color: var(--muted);
        font-size: 14px;
      }
      .status-online { color: var(--green); }
      .status-off { color: var(--muted); }
      .status-alert { color: var(--orange); }
      @media (max-width: 900px) {
        .grid, .two-col { grid-template-columns: 1fr; }
      }
    </style>
  </head>
  <body>
    <header>
      <h1>{{ project_name }}</h1>
      <p>
        Versão Flask compatível com Vercel para a simulação IoT com ESP32,
        sensores ambientais, atuadores, LCD e cálculo de economia energética.
      </p>
      <p class="note">
        Observação: em ambiente serverless, o estado em memória pode reiniciar entre requisições.
        A interface continua funcional e recria a simulação quando necessário.
      </p>
    </header>

    <main>
      <nav class="toolbar" aria-label="Controles da simulação">
        <a class="button primary" href="/step">Gerar próxima leitura</a>
        <a class="button" href="/run/10">Rodar 10 ciclos</a>
        <a class="button" href="/run/30">Rodar 30 ciclos</a>
        <a class="button warn" href="/reset">Resetar simulação</a>
        <a class="button" href="/csv">Baixar CSV</a>
      </nav>

      <section class="grid">
        <div class="card">
          <div class="label">Temperatura</div>
          <div class="value">{{ "%.1f"|format(readings.temperature_c) }} °C</div>
        </div>
        <div class="card">
          <div class="label">Umidade</div>
          <div class="value">{{ "%.1f"|format(readings.humidity_percent) }}%</div>
        </div>
        <div class="card">
          <div class="label">Luminosidade</div>
          <div class="value">{{ "%.1f"|format(readings.light_percent) }}%</div>
        </div>
        <div class="card">
          <div class="label">Presença</div>
          <div class="value">{{ "Detectada" if readings.presence else "Ausente" }}</div>
        </div>
      </section>

      <section class="grid section">
        <div class="card">
          <div class="label">Iluminação</div>
          <div class="value">{{ actuators.lighting.state }}</div>
        </div>
        <div class="card">
          <div class="label">Climatização</div>
          <div class="value">{{ actuators.hvac.state }}</div>
        </div>
        <div class="card">
          <div class="label">Consumo acumulado</div>
          <div class="value">{{ "%.6f"|format(energy.automation_energy_kwh) }} kWh</div>
        </div>
        <div class="card">
          <div class="label">Economia</div>
          <div class="value">{{ "%.2f"|format(energy.savings_percent) }}%</div>
        </div>
      </section>

      <section class="two-col section">
        <div class="card">
          <h2>LCD simulado</h2>
          <div class="lcd">{{ state.lcd.text }}</div>
        </div>
        <div class="card">
          <h2>Resumo</h2>
          <p><b>Ciclo atual:</b> {{ state.cycle }}</p>
          <p><b>Modo:</b> {{ state.mode }}</p>
          <p><b>Status ESP32:</b> {{ state.status }}</p>
          <p><b>Histórico:</b> {{ history_count }} registros</p>
          <p><b>Intervalo padrão:</b> {{ interval }} segundos simulados por ciclo</p>
        </div>
      </section>

      <section class="section">
        <h2>Placa ESP32 e componentes conectados</h2>
        {{ board_html|safe }}
      </section>

      <section class="section">
        <h2>Histórico recente</h2>
        {% if history_rows %}
          <table>
            <thead>
              <tr>
                <th>Ciclo</th>
                <th>Temperatura</th>
                <th>Umidade</th>
                <th>Luminosidade</th>
                <th>Presença</th>
                <th>Iluminação</th>
                <th>Climatização</th>
                <th>Economia</th>
              </tr>
            </thead>
            <tbody>
              {% for row in history_rows %}
                <tr>
                  <td>{{ row.ciclo }}</td>
                  <td>{{ row.temperatura_c }} °C</td>
                  <td>{{ row.umidade_percent }}%</td>
                  <td>{{ row.luminosidade_percent }}%</td>
                  <td>{{ "Sim" if row.presenca else "Não" }}</td>
                  <td>{{ row.iluminacao }}</td>
                  <td>{{ row.climatizacao }}</td>
                  <td>{{ row.economia_percentual }}%</td>
                </tr>
              {% endfor %}
            </tbody>
          </table>
        {% else %}
          <div class="card">
            <p>Nenhum ciclo foi registrado ainda. Clique em <b>Gerar próxima leitura</b> para iniciar a simulação.</p>
          </div>
        {% endif %}
      </section>

      <section class="section card">
        <h2>Como interpretar</h2>
        <p>
          Sem presença, iluminação e climatização são desligadas. Com presença, a luminosidade define a lâmpada
          e a temperatura define o modo de climatização. O consumo com automação é comparado com um cenário base
          sem automação para estimar a economia.
        </p>
      </section>
    </main>
  </body>
</html>
"""


try:
    from .web_app import app as app  # type: ignore[import-not-found]  # noqa: E402,F811
except ImportError:
    from web_app import app as app  # type: ignore[no-redef]  # noqa: E402,F811


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
'''
