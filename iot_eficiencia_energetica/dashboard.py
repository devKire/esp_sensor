"""Dashboard Streamlit da solucao IoT de eficiencia energetica."""

from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components

from board_view import render_esp32_board
from config import PROJECT_NAME, SIMULATION_INTERVAL_SECONDS
from controller import IoTController
from report import generate_summary, history_to_dataframe


def ensure_session_state() -> None:
    """Inicializa controlador, estado visual e controles do Streamlit."""
    if "controller" not in st.session_state:
        st.session_state.controller = IoTController()
        st.session_state.current_state = st.session_state.controller.get_current_state()

    defaults = {
        "simulation_mode_selector": "Automatico",
        "visual_speed_slider": SIMULATION_INTERVAL_SECONDS,
        "manual_temperature_slider": 24.0,
        "manual_humidity_slider": 55.0,
        "manual_light_slider": 35.0,
        "manual_presence_toggle": True,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)

    pending_mode = st.session_state.pop("_pending_simulation_mode_selector", None)
    if pending_mode is not None:
        st.session_state.simulation_mode_selector = pending_mode


def get_controller() -> IoTController:
    """Retorna o controlador armazenado na sessao."""
    return st.session_state.controller


def get_current_state() -> dict[str, Any]:
    """Retorna o estado visual atual, mesmo sem historico."""
    state = st.session_state.get("current_state")
    if state is None:
        state = get_controller().get_current_state()
        st.session_state.current_state = state
    return state


def get_manual_readings() -> dict[str, float | bool]:
    """Le os valores manuais atuais dos widgets."""
    return {
        "temperature_c": float(st.session_state.get("manual_temperature_slider", 24.0)),
        "humidity_percent": float(st.session_state.get("manual_humidity_slider", 55.0)),
        "light_percent": float(st.session_state.get("manual_light_slider", 35.0)),
        "presence": bool(st.session_state.get("manual_presence_toggle", True)),
    }


def get_csv_bytes() -> bytes:
    """Gera CSV em memoria, mesmo quando o historico esta vazio."""
    return get_dataframe().to_csv(index=False).encode("utf-8")


def run_steps(count: int) -> None:
    """Executa uma quantidade finita de ciclos, sem loop infinito."""
    controller = get_controller()
    controller.simulation_interval_seconds = int(st.session_state.visual_speed_slider)
    controller.set_mode(st.session_state.simulation_mode_selector == "Automatico")

    manual_readings = None
    if st.session_state.simulation_mode_selector == "Manual":
        manual_readings = get_manual_readings()

    for _ in range(count):
        st.session_state.current_state = controller.step(manual_readings)


def apply_manual_reading() -> None:
    """Aplica leitura manual e executa um ciclo."""
    st.session_state.simulation_mode_selector = "Manual"
    controller = get_controller()
    controller.set_mode(False)
    controller.simulation_interval_seconds = int(st.session_state.visual_speed_slider)
    st.session_state.current_state = controller.step(get_manual_readings())


def reset_simulation() -> None:
    """Limpa historico, consumo acumulado e estado atual."""
    get_controller().reset()
    st.session_state["_pending_simulation_mode_selector"] = "Automatico"
    st.session_state.current_state = get_controller().get_current_state()


def get_dataframe() -> pd.DataFrame:
    """Retorna o historico atual em DataFrame."""
    return history_to_dataframe(get_controller().history)


def main() -> None:
    """Renderiza o dashboard completo."""
    st.set_page_config(
        page_title="IoT Eficiência Energética",
        page_icon="⚡",
        layout="wide",
    )
    ensure_session_state()

    st.title(PROJECT_NAME)
    st.caption("Simulação academica de ESP32 com sensores, atuadores, LCD e dashboard.")

    tab_overview, tab_board, tab_charts, tab_history, tab_report = st.tabs(
        ["Visão Geral", "Placa ESP32", "Gráficos", "Histórico", "Relatório"]
    )

    with tab_overview:
        render_overview()

    with tab_board:
        render_board_tab()

    with tab_charts:
        render_charts()

    with tab_history:
        render_history()

    with tab_report:
        render_report()


def render_overview() -> None:
    """Aba de indicadores principais e comandos de simulacao."""
    state = st.session_state.current_state
    readings = state["readings"]
    actuators = state["actuators"]
    energy = state["energy"]

    controls = st.columns(4)
    if controls[0].button(
        "Gerar próxima leitura",
        use_container_width=True,
        key="legacy_overview_next_cycle",
    ):
        run_steps(1)
        st.rerun()
    if controls[1].button(
        "Rodar 10 ciclos",
        use_container_width=True,
        key="legacy_overview_run_10_cycles",
    ):
        run_steps(10)
        st.rerun()
    if controls[2].button(
        "Rodar 30 ciclos",
        use_container_width=True,
        key="legacy_overview_run_30_cycles",
    ):
        run_steps(30)
        st.rerun()
    if controls[3].button(
        "Resetar simulação",
        use_container_width=True,
        key="legacy_overview_reset_simulation",
    ):
        reset_simulation()
        st.rerun()

    metric_cols = st.columns(4)
    metric_cols[0].metric("Temperatura", f"{readings['temperature_c']:.1f} °C")
    metric_cols[1].metric("Umidade", f"{readings['humidity_percent']:.1f}%")
    metric_cols[2].metric("Luminosidade", f"{readings['light_percent']:.1f}%")
    metric_cols[3].metric(
        "Presença",
        "Detectada" if readings["presence"] else "Ausente",
    )

    status_cols = st.columns(4)
    status_cols[0].metric("Iluminação", actuators["lighting"]["state"])
    status_cols[1].metric("Climatização", actuators["hvac"]["state"])
    status_cols[2].metric("Consumo atual", f"{energy['current_power_kw']:.3f} kW")
    status_cols[3].metric("Economia estimada", f"{energy['savings_percent']:.2f}%")

    lcd_col, explanation_col = st.columns([1, 2])
    with lcd_col:
        st.subheader("LCD simulado")
        st.code(state["lcd"]["text"], language="text")
    with explanation_col:
        st.subheader("Estado do controlador")
        st.write(f"ESP32: {'online' if state['online'] else 'offline'}")
        st.write(f"Ciclo atual: {state['cycle']}")
        st.write(f"Modo: {state['mode']}")
        st.write(f"Lâmpada: {actuators['lighting']['description']}")
        st.write(f"Climatização: {actuators['hvac']['description']}")


def render_board_tab() -> None:
    """Aba com a placa ESP32 desenhada em SVG dinamico."""
    st.subheader("ESP32 DevKit com sensores e atuadores")
    html = render_esp32_board(st.session_state.current_state)
    components.html(html, height=690, scrolling=False)


def render_charts() -> None:
    """Aba de graficos historicos com Plotly."""
    dataframe = get_dataframe()
    if dataframe.empty:
        st.info("Sem dados suficientes para exibir graficos.")
        return

    dataframe = dataframe.copy()
    dataframe["presenca_int"] = dataframe["presenca"].astype(int)

    chart_cols = st.columns(2)
    with chart_cols[0]:
        fig_temp = px.line(
            dataframe,
            x="ciclo",
            y="temperatura_c",
            markers=True,
            title="Temperatura ao longo do tempo",
        )
        st.plotly_chart(fig_temp, use_container_width=True)

        fig_power = px.line(
            dataframe,
            x="ciclo",
            y=["consumo_acumulado_kwh", "consumo_sem_automacao_kwh"],
            markers=True,
            title="Consumo com automação vs sem automação",
        )
        st.plotly_chart(fig_power, use_container_width=True)

        fig_presence = px.line(
            dataframe,
            x="ciclo",
            y="presenca_int",
            title="Presença ao longo do tempo",
        )
        fig_presence.update_traces(line_shape="hv")
        fig_presence.update_yaxes(tickvals=[0, 1], ticktext=["Ausente", "Presente"])
        st.plotly_chart(fig_presence, use_container_width=True)

    with chart_cols[1]:
        fig_light = px.line(
            dataframe,
            x="ciclo",
            y="luminosidade_percent",
            markers=True,
            title="Luminosidade ao longo do tempo",
        )
        st.plotly_chart(fig_light, use_container_width=True)

        fig_savings = px.line(
            dataframe,
            x="ciclo",
            y="economia_percentual",
            markers=True,
            title="Economia percentual acumulada",
        )
        st.plotly_chart(fig_savings, use_container_width=True)

        fig_humidity = px.line(
            dataframe,
            x="ciclo",
            y="umidade_percent",
            markers=True,
            title="Umidade ao longo do tempo",
        )
        st.plotly_chart(fig_humidity, use_container_width=True)


def render_history() -> None:
    """Aba de tabela historica."""
    dataframe = get_dataframe()
    st.subheader("Histórico da simulação")
    st.dataframe(dataframe, use_container_width=True)


def render_report() -> None:
    """Aba de resumo, CSV e apoio para apresentacao academica."""
    dataframe = get_dataframe()
    summary = generate_summary(st.session_state.controller.history)

    st.subheader("Resumo da simulação")
    cols = st.columns(4)
    cols[0].metric("Ciclos", summary["total_ciclos"])
    cols[1].metric(
        "Consumo com automação",
        f"{summary['consumo_acumulado_kwh']:.6f} kWh",
    )
    cols[2].metric(
        "Consumo sem automação",
        f"{summary['consumo_sem_automacao_kwh']:.6f} kWh",
    )
    cols[3].metric("Economia", f"{summary['economia_percentual']:.2f}%")

    csv_bytes = dataframe.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Baixar relatório CSV",
        data=csv_bytes,
        file_name="relatorio_eficiencia_energetica.csv",
        mime="text/csv",
        use_container_width=True,
        key="legacy_report_download_csv",
    )

    st.subheader("Explicação da economia")
    st.write(
        "O consumo com automação soma apenas a potência usada pelo controlador, "
        "pela iluminação no nível necessário e pela climatização quando há presença. "
        "O consumo sem automação usa uma potência fixa de referência, simulando um "
        "ambiente comercial com cargas ligadas sem decisão inteligente."
    )

    st.subheader("Pontos para apresentação")
    st.write(
        "A solução mostra como uma ESP32 pode ler sensores DHT22, LDR e PIR, "
        "aplicar regras locais simples, acionar relés e registrar dados para "
        "análise energética. Em hardware real, o mesmo conceito pode ser levado "
        "para Arduino IDE, MicroPython, MQTT e dashboards corporativos."
    )


def inject_page_styles() -> None:
    """Adiciona estilos leves para cards de leitura."""
    st.markdown(
        """
        <style>
          .iot-card {
            border: 1px solid #d7dde8;
            border-radius: 8px;
            padding: 14px 16px;
            background: #ffffff;
            min-height: 96px;
          }
          .iot-card .label {
            color: #475569;
            font-size: 0.86rem;
            margin-bottom: 6px;
          }
          .iot-card .value {
            color: #0f172a;
            font-size: 1.45rem;
            font-weight: 700;
            line-height: 1.2;
          }
          .iot-card .hint {
            color: #64748b;
            font-size: 0.82rem;
            margin-top: 8px;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    """Renderiza o dashboard completo."""
    st.set_page_config(
        page_title="IoT Eficiencia Energetica",
        layout="wide",
    )
    ensure_session_state()
    inject_page_styles()

    st.title(PROJECT_NAME)
    st.caption(
        "Bancada IoT simulada com ESP32, sensores, atuadores, LCD, historico e CSV."
    )

    (
        tab_overview,
        tab_board,
        tab_simulator,
        tab_charts,
        tab_history,
        tab_report,
    ) = st.tabs(
        [
            "Visao Geral",
            "Placa ESP32",
            "Simulador",
            "Graficos",
            "Historico",
            "Relatorio",
        ]
    )

    with tab_overview:
        render_overview()
    with tab_board:
        render_board_tab()
    with tab_simulator:
        render_simulator()
    with tab_charts:
        render_charts()
    with tab_history:
        render_history()
    with tab_report:
        render_report()


def render_overview() -> None:
    """Aba de indicadores principais e comandos rapidos."""
    state = get_current_state()
    readings = state["readings"]
    actuators = state["actuators"]
    energy = state["energy"]

    controls = st.columns(5)
    if controls[0].button(
        "Gerar proxima leitura",
        use_container_width=True,
        key="overview_next_cycle",
    ):
        run_steps(1)
        st.rerun()
    if controls[1].button(
        "Rodar 10 ciclos",
        use_container_width=True,
        key="overview_run_10_cycles",
    ):
        run_steps(10)
        st.rerun()
    if controls[2].button(
        "Rodar 30 ciclos",
        use_container_width=True,
        key="overview_run_30_cycles",
    ):
        run_steps(30)
        st.rerun()
    if controls[3].button(
        "Resetar simulacao",
        use_container_width=True,
        key="overview_reset_simulation",
    ):
        reset_simulation()
        st.rerun()
    controls[4].download_button(
        "Baixar CSV",
        data=get_csv_bytes(),
        file_name="relatorio_eficiencia_energetica.csv",
        mime="text/csv",
        use_container_width=True,
        key="overview_download_csv",
    )

    cards = st.columns(4)
    render_card(cards[0], "Temperatura atual", f"{readings['temperature_c']:.1f} C")
    render_card(cards[1], "Umidade atual", f"{readings['humidity_percent']:.1f}%")
    render_card(cards[2], "Luminosidade atual", f"{readings['light_percent']:.1f}%")
    render_card(
        cards[3],
        "Presenca detectada",
        "Sim" if readings["presence"] else "Nao",
    )

    cards = st.columns(4)
    render_card(cards[0], "Iluminacao", actuators["lighting"]["state"])
    render_card(cards[1], "Climatizacao", actuators["hvac"]["state"])
    render_card(
        cards[2],
        "Consumo acumulado",
        f"{energy['automation_energy_kwh']:.6f} kWh",
    )
    render_card(cards[3], "Economia percentual", f"{energy['savings_percent']:.2f}%")

    lcd_col, status_col = st.columns([1, 2])
    with lcd_col:
        st.subheader("LCD simulado")
        st.code(state["lcd"]["text"], language="text")
    with status_col:
        st.subheader("Estado da ESP32")
        status_cards = st.columns(3)
        render_card(status_cards[0], "Ciclo atual", str(state["cycle"]))
        render_card(status_cards[1], "Modo atual", state["mode"].title())
        render_card(status_cards[2], "Status", state.get("status", "online").title())
        st.write(f"Lampada: {actuators['lighting']['description']}")
        st.write(f"Climatizacao: {actuators['hvac']['description']}")


def render_card(column: Any, label: str, value: str, hint: str = "") -> None:
    """Renderiza um card visual simples."""
    hint_html = f'<div class="hint">{hint}</div>' if hint else ""
    column.markdown(
        f"""
        <div class="iot-card">
          <div class="label">{label}</div>
          <div class="value">{value}</div>
          {hint_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_board_tab() -> None:
    """Aba com a placa ESP32 desenhada em SVG dinamico."""
    st.subheader("Bancada IoT com ESP32 DevKit")
    st.caption("Cores, fios, LCD e atuadores mudam conforme a simulacao.")
    components.html(
        render_esp32_board(get_current_state()),
        height=700,
        scrolling=False,
    )


def render_simulator() -> None:
    """Aba dedicada ao controle da simulacao."""
    state = get_current_state()

    st.subheader("Controle da simulacao")
    mode_col, speed_col, status_col = st.columns([1, 1, 2])
    with mode_col:
        st.radio(
            "Modo",
            ["Automatico", "Manual"],
            key="simulation_mode_selector",
            horizontal=True,
        )
        get_controller().set_mode(
            st.session_state.simulation_mode_selector == "Automatico"
        )
        st.session_state.current_state = get_controller().get_current_state()
    with speed_col:
        st.slider(
            "Intervalo simulado por ciclo (s)",
            min_value=1,
            max_value=10,
            value=int(st.session_state.visual_speed_slider),
            key="visual_speed_slider",
        )
    with status_col:
        state = get_current_state()
        st.info(
            f"Ciclo {state['cycle']} | Modo {state['mode'].title()} | "
            f"Status {state.get('status', 'online').title()}"
        )

    controls = st.columns(4)
    if controls[0].button(
        "Proximo ciclo",
        use_container_width=True,
        key="simulator_next_cycle",
    ):
        run_steps(1)
        st.rerun()
    if controls[1].button(
        "Rodar 10 ciclos",
        use_container_width=True,
        key="simulator_run_10_cycles",
    ):
        run_steps(10)
        st.rerun()
    if controls[2].button(
        "Rodar 30 ciclos",
        use_container_width=True,
        key="simulator_run_30_cycles",
    ):
        run_steps(30)
        st.rerun()
    if controls[3].button(
        "Resetar",
        use_container_width=True,
        key="simulator_reset",
    ):
        reset_simulation()
        st.rerun()

    st.divider()
    st.subheader("Leitura manual para demonstracao")
    st.caption(
        "Use este painel para forcar cenarios didaticos sem depender do sorteio dos sensores."
    )
    manual_cols = st.columns(4)
    manual_cols[0].slider(
        "Temperatura (C)",
        min_value=18.0,
        max_value=32.0,
        step=0.1,
        key="manual_temperature_slider",
    )
    manual_cols[1].slider(
        "Umidade (%)",
        min_value=30.0,
        max_value=80.0,
        step=0.5,
        key="manual_humidity_slider",
    )
    manual_cols[2].slider(
        "Luminosidade (%)",
        min_value=0.0,
        max_value=100.0,
        step=1.0,
        key="manual_light_slider",
    )
    manual_cols[3].toggle("Presenca", key="manual_presence_toggle")

    scenario_cols = st.columns(4)
    scenario_cols[0].button(
        "Sem presenca",
        use_container_width=True,
        on_click=set_manual_scenario,
        args=(24.0, 55.0, 65.0, False),
        key="simulator_scenario_no_presence",
    )
    scenario_cols[1].button(
        "Escuro com presenca",
        use_container_width=True,
        on_click=set_manual_scenario,
        args=(24.0, 55.0, 20.0, True),
        key="simulator_scenario_dark_with_presence",
    )
    scenario_cols[2].button(
        "Temperatura alta",
        use_container_width=True,
        on_click=set_manual_scenario,
        args=(28.5, 55.0, 55.0, True),
        key="simulator_scenario_high_temperature",
    )
    scenario_cols[3].button(
        "Conforto ECO",
        use_container_width=True,
        on_click=set_manual_scenario,
        args=(24.0, 55.0, 75.0, True),
        key="simulator_scenario_eco_comfort",
    )

    st.button(
        "Aplicar leitura manual",
        use_container_width=True,
        on_click=apply_manual_reading,
        key="simulator_apply_manual_reading",
    )


def set_manual_scenario(
    temperature: float,
    humidity: float,
    light: float,
    presence: bool,
) -> None:
    """Atualiza widgets manuais com um cenario de apresentacao."""
    st.session_state.manual_temperature_slider = temperature
    st.session_state.manual_humidity_slider = humidity
    st.session_state.manual_light_slider = light
    st.session_state.manual_presence_toggle = presence
    st.session_state.simulation_mode_selector = "Manual"
    controller = get_controller()
    controller.set_mode(False)
    controller.simulation_interval_seconds = int(st.session_state.visual_speed_slider)
    st.session_state.current_state = controller.step(
        {
            "temperature_c": temperature,
            "humidity_percent": humidity,
            "light_percent": light,
            "presence": presence,
        }
    )


def render_charts() -> None:
    """Aba de graficos historicos com Plotly."""
    dataframe = get_dataframe()
    if dataframe.empty:
        st.info("Gere alguns ciclos para visualizar os graficos.")
        return

    dataframe = dataframe.copy()
    dataframe["presenca_int"] = dataframe["presenca"].astype(int)

    chart_cols = st.columns(2)
    with chart_cols[0]:
        render_line_chart(
            dataframe,
            "temperatura_c",
            "Temperatura ao longo do tempo",
            "Temperatura (C)",
        )
        render_line_chart(
            dataframe,
            "luminosidade_percent",
            "Luminosidade ao longo do tempo",
            "Luminosidade (%)",
        )
        fig_power = px.line(
            dataframe,
            x="ciclo",
            y=["consumo_acumulado_kwh", "consumo_sem_automacao_kwh"],
            markers=True,
            title="Consumo com automacao vs sem automacao",
        )
        fig_power.update_layout(legend_title_text="Serie")
        st.plotly_chart(fig_power, use_container_width=True)

    with chart_cols[1]:
        render_line_chart(
            dataframe,
            "umidade_percent",
            "Umidade ao longo do tempo",
            "Umidade (%)",
        )
        fig_presence = px.line(
            dataframe,
            x="ciclo",
            y="presenca_int",
            title="Presenca ao longo do tempo",
        )
        fig_presence.update_traces(line_shape="hv")
        fig_presence.update_yaxes(tickvals=[0, 1], ticktext=["Ausente", "Presente"])
        st.plotly_chart(fig_presence, use_container_width=True)
        render_line_chart(
            dataframe,
            "economia_percentual",
            "Economia percentual acumulada",
            "Economia (%)",
        )


def render_line_chart(
    dataframe: pd.DataFrame,
    y_column: str,
    title: str,
    y_label: str,
) -> None:
    """Renderiza um grafico de linha tolerante a poucos pontos."""
    fig = px.line(
        dataframe,
        x="ciclo",
        y=y_column,
        markers=True,
        title=title,
        labels={y_column: y_label, "ciclo": "Ciclo"},
    )
    st.plotly_chart(fig, use_container_width=True)


def render_history() -> None:
    """Aba de tabela historica."""
    st.subheader("Historico da simulacao")
    dataframe = get_dataframe()

    if dataframe.empty:
        st.info("O historico esta vazio. Gere um ciclo para registrar dados.")
    else:
        st.dataframe(dataframe, use_container_width=True, hide_index=True)

    if st.button(
        "Limpar historico e resetar simulacao",
        use_container_width=True,
        key="history_reset_simulation",
    ):
        reset_simulation()
        st.rerun()


def render_report() -> None:
    """Aba de resumo, CSV e roteiro de apresentacao."""
    summary = generate_summary(get_controller().history)

    st.subheader("Resumo da simulacao")
    metric_cols = st.columns(4)
    metric_cols[0].metric("Total de ciclos", summary["total_ciclos"])
    metric_cols[1].metric(
        "Tempo simulado",
        format_seconds(summary["tempo_simulado_s"]),
    )
    metric_cols[2].metric(
        "Tempo com presenca",
        format_seconds(summary["tempo_com_presenca_s"]),
    )
    metric_cols[3].metric(
        "Tempo sem presenca",
        format_seconds(summary["tempo_sem_presenca_s"]),
    )

    metric_cols = st.columns(4)
    metric_cols[0].metric(
        "Consumo com automacao",
        f"{summary['consumo_acumulado_kwh']:.6f} kWh",
    )
    metric_cols[1].metric(
        "Consumo sem automacao",
        f"{summary['consumo_sem_automacao_kwh']:.6f} kWh",
    )
    metric_cols[2].metric("Economia", f"{summary['economia_kwh']:.6f} kWh")
    metric_cols[3].metric("Economia percentual", f"{summary['economia_percentual']:.2f}%")

    metric_cols = st.columns(4)
    metric_cols[0].metric(
        "Acionamentos da iluminacao",
        summary["acionamentos_iluminacao"],
    )
    metric_cols[1].metric(
        "Acionamentos da climatizacao",
        summary["acionamentos_climatizacao"],
    )
    metric_cols[2].metric("Temperatura media", f"{summary['temperatura_media_c']:.2f} C")
    metric_cols[3].metric(
        "Luminosidade media",
        f"{summary['luminosidade_media_percent']:.2f}%",
    )

    st.download_button(
        "Baixar relatorio CSV",
        data=get_csv_bytes(),
        file_name="relatorio_eficiencia_energetica.csv",
        mime="text/csv",
        use_container_width=True,
        key="report_download_csv",
    )

    st.subheader("Explicacao da economia")
    st.write(
        "O consumo com automacao soma a potencia da ESP32 simulada, da iluminacao "
        "no nivel necessario e da climatizacao apenas quando as regras indicam uso. "
        "O consumo sem automacao usa uma potencia fixa de referencia para comparar "
        "um edificio sem controle inteligente."
    )

    st.subheader("Como apresentar")
    st.markdown(
        """
        1. Mostrar o problema energetico de salas comerciais com cargas ligadas sem necessidade.
        2. Abrir a aba Placa ESP32 e explicar sensores, atuadores, GPIOs e LCD.
        3. Rodar ciclos automaticos para simular operacao normal.
        4. Usar o modo manual para demonstrar ambiente escuro, sem presenca e temperatura alta.
        5. Observar sensores, fios, lampada, climatizacao e LCD mudando.
        6. Abrir os graficos para comparar consumo com e sem automacao.
        7. Exportar o CSV e explicar que a logica pode migrar para uma ESP32 real.
        """
    )


def format_seconds(seconds: int | float) -> str:
    """Formata segundos simulados para exibicao curta."""
    seconds_int = int(seconds)
    minutes, remaining_seconds = divmod(seconds_int, 60)
    if minutes:
        return f"{minutes} min {remaining_seconds} s"
    return f"{remaining_seconds} s"


if __name__ == "__main__":
    main()
