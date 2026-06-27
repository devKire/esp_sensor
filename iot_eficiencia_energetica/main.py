"""Execucao em terminal da simulacao IoT para eficiencia energetica."""

from __future__ import annotations

import argparse
import time

from config import DEFAULT_REPORT_FILENAME, DEFAULT_TERMINAL_CYCLES
from controller import IoTController
from report import export_csv


def parse_args() -> argparse.Namespace:
    """Processa argumentos opcionais de linha de comando."""
    parser = argparse.ArgumentParser(
        description="Simulacao IoT com ESP32 para eficiencia energetica.",
    )
    parser.add_argument(
        "--cycles",
        type=int,
        default=DEFAULT_TERMINAL_CYCLES,
        help="Quantidade de ciclos da simulacao.",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=0.0,
        help="Pausa real entre ciclos em segundos.",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_REPORT_FILENAME,
        help="Arquivo CSV de saida.",
    )
    return parser.parse_args()


def main() -> None:
    """Executa a simulacao no terminal e exporta o relatorio CSV."""
    args = parse_args()
    if args.cycles <= 0:
        raise ValueError("A quantidade de ciclos deve ser maior que zero.")

    controller = IoTController()

    print("Simulacao IoT - ESP32 para eficiencia energetica")
    print(f"Ciclos: {args.cycles}\n")

    for _ in range(args.cycles):
        state = controller.step()
        lighting = state["actuators"]["lighting"]
        hvac = state["actuators"]["hvac"]
        readings = state["readings"]

        print(f"Ciclo {state['cycle']} | {state['timestamp']}")
        print(state["lcd"]["terminal"])
        print(
            "Presenca: "
            f"{'SIM' if readings['presence'] else 'NAO'} | "
            f"Iluminacao: {lighting['state']} ({lighting['gpio']}) | "
            f"Climatizacao: {hvac['state']} ({hvac['gpio']})"
        )
        print(
            f"Consumo acumulado: {state['energy']['automation_energy_kwh']:.6f} kWh | "
            f"Economia: {state['energy']['savings_percent']:.2f}%\n"
        )

        if args.sleep > 0:
            time.sleep(args.sleep)

    csv_path = export_csv(controller.history, args.output)
    summary = controller.generate_summary()

    print("Resumo final")
    print(f"Ciclos executados: {summary['cycles']}")
    print(f"Consumo com automacao: {summary['automation_energy_kwh']:.6f} kWh")
    print(f"Consumo sem automacao: {summary['baseline_energy_kwh']:.6f} kWh")
    print(f"Economia estimada: {summary['savings_kwh']:.6f} kWh")
    print(f"Economia percentual: {summary['savings_percent']:.2f}%")
    print(f"Temperatura media: {summary['average_temperature_c']:.2f} C")
    print(f"Luminosidade media: {summary['average_light_percent']:.2f}%")
    print(f"Relatorio CSV exportado: {csv_path}")


if __name__ == "__main__":
    main()
