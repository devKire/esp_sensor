"""Gera o relatório acadêmico em PDF do projeto IoT com ESP32."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from config import (
    BASELINE_POWER_KW,
    COMFORT_TEMP_MAX,
    COMFORT_TEMP_MIN,
    CONTROLLER_POWER_KW,
    HVAC_POWER_FACTORS,
    HVAC_POWER_KW,
    LIGHT_POWER_KW,
    LIGHTING_POWER_FACTORS,
    LOW_LIGHT_THRESHOLD,
    MEDIUM_LIGHT_THRESHOLD,
    PIN_MAP,
    SIMULATION_INTERVAL_SECONDS,
)
from report import CSV_COLUMNS

PROJECT_ROOT = Path(__file__).resolve().parent
PDF_PATH = PROJECT_ROOT / "RELATORIO_SOLUCAO_IOT_ESP32.pdf"


def build_styles() -> dict[str, ParagraphStyle]:
    """Cria estilos usados no relatório."""
    base = getSampleStyleSheet()
    styles = {
        "title": ParagraphStyle(
            "ReportTitle",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=28,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#0f172a"),
            spaceAfter=18,
        ),
        "subtitle": ParagraphStyle(
            "ReportSubtitle",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=12,
            leading=17,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#334155"),
            spaceAfter=10,
        ),
        "section": ParagraphStyle(
            "SectionTitle",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=19,
            textColor=colors.HexColor("#0f172a"),
            spaceBefore=14,
            spaceAfter=8,
        ),
        "subsection": ParagraphStyle(
            "SubsectionTitle",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#1e293b"),
            spaceBefore=10,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=14,
            alignment=TA_JUSTIFY,
            textColor=colors.HexColor("#111827"),
            spaceAfter=7,
        ),
        "bullet": ParagraphStyle(
            "Bullet",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.3,
            leading=13,
            leftIndent=12,
            bulletIndent=4,
            textColor=colors.HexColor("#111827"),
            spaceAfter=4,
        ),
        "code": ParagraphStyle(
            "Code",
            parent=base["Code"],
            fontName="Courier",
            fontSize=8.2,
            leading=11,
            backColor=colors.HexColor("#f1f5f9"),
            borderColor=colors.HexColor("#cbd5e1"),
            borderWidth=0.5,
            borderPadding=6,
            spaceBefore=4,
            spaceAfter=8,
        ),
        "small": ParagraphStyle(
            "Small",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#475569"),
        ),
    }
    return styles


def p(text: str, styles: dict[str, ParagraphStyle], style: str = "body") -> Paragraph:
    """Cria um parágrafo com o estilo solicitado."""
    return Paragraph(text, styles[style])


def bullets(items: list[str], styles: dict[str, ParagraphStyle]) -> list[Paragraph]:
    """Cria lista de bullets."""
    return [Paragraph(item, styles["bullet"], bulletText="•") for item in items]


def table(
    rows: list[list[Any]],
    col_widths: list[float] | None = None,
    header: bool = True,
) -> Table:
    """Cria tabela formatada."""
    formatted_rows = [
        [Paragraph(str(cell), getSampleStyleSheet()["BodyText"]) for cell in row]
        for row in rows
    ]
    result = Table(formatted_rows, colWidths=col_widths, hAlign="LEFT")
    style = [
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#cbd5e1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    if header:
        style.extend(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
            ]
        )
    result.setStyle(TableStyle(style))
    return result


def section(story: list[Any], styles: dict[str, ParagraphStyle], title: str) -> None:
    """Adiciona título de seção."""
    story.append(p(title, styles, "section"))


def subsection(story: list[Any], styles: dict[str, ParagraphStyle], title: str) -> None:
    """Adiciona subtítulo."""
    story.append(p(title, styles, "subsection"))


def add_footer(canvas: Any, doc: SimpleDocTemplate) -> None:
    """Adiciona rodapé com número de página."""
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#64748b"))
    footer = f"Relatório Técnico - Solução IoT ESP32 | Página {doc.page}"
    canvas.drawRightString(A4[0] - 1.7 * cm, 1.0 * cm, footer)
    canvas.restoreState()


def build_story() -> list[Any]:
    """Monta o conteúdo completo do relatório."""
    styles = build_styles()
    story: list[Any] = []
    generated_at = datetime.now().strftime("%d/%m/%Y %H:%M")

    story.append(
        p(
            "Relatório Técnico - Solução IoT para Eficiência Energética em Edifícios Comerciais",
            styles,
            "title",
        )
    )
    story.append(
        p(
            "Simulação com ESP32, sensores ambientais, atuadores, dashboard e controle automático de iluminação e climatização",
            styles,
            "subtitle",
        )
    )
    story.append(Spacer(1, 0.6 * cm))
    story.append(p("<b>Nome da solução:</b> Imersão 2 - Solução IoT para Eficiência Energética com ESP32", styles))
    story.append(p("<b>Tecnologias principais:</b> Python, Streamlit, ESP32 simulada, Plotly, Pandas e ReportLab", styles))
    story.append(p(f"<b>Data de geração:</b> {generated_at}", styles))
    story.append(p("<b>Tipo de entrega:</b> Projeto acadêmico com simulação funcional e documentação técnica.", styles))
    story.append(PageBreak())

    section(story, styles, "1. Resumo executivo")
    story.append(
        p(
            "O projeto apresenta uma solução IoT simulada para reduzir desperdício de energia em edifícios comerciais. "
            "A proposta considera ambientes em que luzes e climatização podem permanecer ligadas mesmo sem presença de pessoas "
            "ou sem necessidade real. Para resolver esse cenário, a solução usa sensores simulados de temperatura, umidade, "
            "luminosidade e presença, uma ESP32 simulada como controlador, atuadores de iluminação e climatização, LCD, dashboard "
            "visual e relatórios de consumo.",
            styles,
        )
    )
    story.append(
        p(
            "A automação oferece benefícios como redução de consumo, melhoria de conforto, rastreabilidade de decisões, "
            "visualização em tempo real e possibilidade de migração futura para hardware real. No software foram implementados "
            "dashboard Streamlit, visualização SVG da bancada ESP32, modo automático, modo manual, histórico, gráficos e exportação CSV.",
            styles,
        )
    )

    section(story, styles, "2. Contexto e problema")
    story += bullets(
        [
            "Edifícios comerciais podem desperdiçar energia com iluminação ligada sem ocupação.",
            "Sistemas de climatização podem operar sem presença ou fora da necessidade térmica real.",
            "A ausência de monitoramento ambiental reduz a capacidade de tomada de decisão.",
            "Sem histórico e relatórios, fica difícil demonstrar consumo, economia e comportamento do sistema.",
            "Sensores e automação local permitem agir no momento certo e desligar cargas desnecessárias.",
        ],
        styles,
    )

    section(story, styles, "3. Objetivos do projeto")
    subsection(story, styles, "Objetivo geral")
    story.append(
        p(
            "Criar uma solução IoT simulada para monitorar e controlar iluminação e climatização em edifícios comerciais, "
            "utilizando uma ESP32 como referência de microcontrolador.",
            styles,
        )
    )
    subsection(story, styles, "Objetivos específicos")
    story += bullets(
        [
            "Monitorar temperatura, umidade, luminosidade e presença.",
            "Controlar iluminação de forma automática.",
            "Controlar climatização conforme faixa de conforto.",
            "Simular uma ESP32 DevKit com sensores, atuadores, fios, pinos e LCD.",
            "Calcular consumo atual e acumulado.",
            "Estimar economia de energia em kWh e percentual.",
            "Gerar dashboard, gráficos, histórico e relatório CSV.",
            "Permitir apresentação acadêmica com modo manual e cenários demonstrativos.",
        ],
        styles,
    )

    section(story, styles, "4. Visão geral da solução")
    story.append(
        p(
            "A arquitetura segue o fluxo: sensores simulados → ESP32 simulada/controlador → regras de decisão → atuadores → "
            "dashboard, LCD e relatórios. O controlador lê sensores, decide ações, atualiza iluminação e climatização, calcula "
            "energia, atualiza o LCD e registra histórico.",
            styles,
        )
    )
    story += bullets(
        [
            "ESP32 DevKit simulada como placa central.",
            "Sensores DHT22/DHT11, LDR e PIR.",
            "Relé de iluminação, lâmpada, relé de climatização e ar-condicionado/ventilador.",
            "Display LCD I2C 20x4.",
            "Dashboard Streamlit com seis abas.",
            "Histórico e CSV para análise e apresentação.",
        ],
        styles,
    )

    section(story, styles, "5. Componentes simulados")
    subsection(story, styles, "Sensores")
    sensor_rows = [
        ["Componente", "Medição", "Uso na automação"],
        ["TemperatureSensor", "Temperatura em °C", "Define COOLING, HEATING ou ECO quando há presença."],
        ["HumiditySensor", "Umidade relativa", "Enriquece monitoramento ambiental e LCD."],
        ["LightSensor", "Luminosidade de 0 a 100%", "Define intensidade da iluminação quando há presença."],
        ["PresenceSensor", "Presença True/False", "Prioriza desligamento de iluminação e climatização quando não há pessoas."],
    ]
    story.append(table(sensor_rows, [4.0 * cm, 4.2 * cm, 8.0 * cm]))
    story.append(Spacer(1, 0.25 * cm))

    subsection(story, styles, "Atuadores")
    actuator_rows = [
        ["Atuador", "Estados", "Contribuição para economia"],
        ["LightingActuator", "OFF, LOW, MEDIUM, HIGH", "Evita iluminação quando há luz suficiente ou ausência."],
        ["HVACActuator", "OFF, FAN, COOLING, HEATING, ECO", "Evita climatização sem presença e mantém conforto com ECO."],
    ]
    story.append(table(actuator_rows, [4.0 * cm, 5.2 * cm, 7.0 * cm]))
    story.append(Spacer(1, 0.25 * cm))

    subsection(story, styles, "Display LCD")
    story.append(
        p(
            "O LCD simulado apresenta temperatura, umidade, estado da iluminação, presença, modo da climatização, economia, "
            "potência atual e ciclo. Exemplo: TEMP:24.5C UM:55%, LUZ:HIGH PRES:SIM, AR:COOL ECO:18%.",
            styles,
        )
    )

    subsection(story, styles, "ESP32 simulada")
    story.append(
        p(
            "A ESP32 simulada é representada pela classe IoTController. Ela realiza leitura dos sensores, tomada de decisão, "
            "controle dos atuadores, atualização do LCD, cálculo de consumo e armazenamento do histórico.",
            styles,
        )
    )

    section(story, styles, "6. Mapa de pinos da ESP32")
    pin_rows = [["Componente", "Pino", "Função"]]
    pin_descriptions = {
        "DHT22": "Leitura de temperatura e umidade.",
        "LDR": "Entrada analógica de luminosidade.",
        "PIR": "Entrada digital de presença.",
        "LIGHT_RELAY": "Saída para relé de iluminação.",
        "HVAC_RELAY": "Saída para relé de climatização.",
        "LCD_SDA": "Linha de dados I2C do LCD.",
        "LCD_SCL": "Linha de clock I2C do LCD.",
    }
    for component, pin in PIN_MAP.items():
        pin_rows.append([component, pin, pin_descriptions[component]])
    story.append(table(pin_rows, [4.2 * cm, 3.0 * cm, 8.8 * cm]))

    section(story, styles, "7. Lógica de automação")
    logic = (
        f"Se não houver presença: iluminação = OFF e climatização = OFF.<br/>"
        f"Se houver presença e luminosidade &lt; {LOW_LIGHT_THRESHOLD}: iluminação = HIGH.<br/>"
        f"Se houver presença e luminosidade entre {LOW_LIGHT_THRESHOLD} e {MEDIUM_LIGHT_THRESHOLD}: iluminação = LOW.<br/>"
        f"Se houver presença e luminosidade &gt;= {MEDIUM_LIGHT_THRESHOLD}: iluminação = OFF.<br/>"
        f"Se houver presença e temperatura &gt; {COMFORT_TEMP_MAX}: climatização = COOLING.<br/>"
        f"Se houver presença e temperatura &lt; {COMFORT_TEMP_MIN}: climatização = HEATING.<br/>"
        f"Se houver presença e temperatura entre {COMFORT_TEMP_MIN} e {COMFORT_TEMP_MAX}: climatização = ECO."
    )
    story.append(p(logic, styles, "code"))
    story.append(
        p(
            "A presença é prioridade porque cargas principais não devem operar sem pessoas no ambiente. A luminosidade controla "
            "a lâmpada para aproveitar luz natural. A temperatura controla a climatização para manter conforto térmico sem consumo "
            "desnecessário.",
            styles,
        )
    )

    section(story, styles, "8. Cálculo de consumo e economia")
    calc_rows = [
        ["Parâmetro", "Valor"],
        ["Potência da iluminação", f"{LIGHT_POWER_KW} kW"],
        ["Potência da climatização", f"{HVAC_POWER_KW} kW"],
        ["Potência do controlador", f"{CONTROLLER_POWER_KW} kW"],
        ["Potência base sem automação", f"{BASELINE_POWER_KW} kW"],
        ["Intervalo padrão", f"{SIMULATION_INTERVAL_SECONDS} s"],
        ["Fatores da iluminação", str(LIGHTING_POWER_FACTORS)],
        ["Fatores da climatização", str(HVAC_POWER_FACTORS)],
    ]
    story.append(table(calc_rows, [5.2 * cm, 10.8 * cm]))
    story.append(Spacer(1, 0.25 * cm))
    story.append(
        p(
            "Consumo do intervalo = potência atual × intervalo em horas. "
            "Economia em kWh = consumo sem automação - consumo com automação. "
            "Economia percentual = economia / consumo sem automação × 100.",
            styles,
        )
    )

    section(story, styles, "9. Interface visual da ESP32")
    story.append(
        p(
            "A aba Placa ESP32 exibe uma bancada técnica desenhada em HTML/SVG. A ESP32 fica no centro, sensores aparecem à esquerda, "
            "atuadores à direita, LCD na região inferior e fios conectam os componentes aos GPIOs. A visualização muda em tempo real "
            "conforme o estado da simulação.",
            styles,
        )
    )
    story += bullets(
        [
            "PIR verde quando há presença e cinza quando não há presença.",
            "LDR em alerta quando a luminosidade está baixa.",
            "Lâmpada acesa quando a regra de iluminação exige acionamento.",
            "Climatização azul em COOLING e laranja em HEATING.",
            "LCD exibe temperatura, umidade, iluminação, presença, HVAC, consumo e economia.",
        ],
        styles,
    )

    section(story, styles, "10. Dashboard em Streamlit")
    dashboard_rows = [
        ["Aba", "Finalidade"],
        ["Visão Geral", "Mostra cards, LCD, status da ESP32 e controles rápidos."],
        ["Placa ESP32", "Mostra a bancada visual com sensores, atuadores, GPIOs, fios e LCD."],
        ["Simulador", "Permite rodar ciclos, resetar, alternar modo e aplicar leituras manuais."],
        ["Gráficos", "Exibe séries de temperatura, umidade, luminosidade, presença, consumo e economia."],
        ["Histórico", "Mostra tabela Pandas com registros de cada ciclo e botão de reset."],
        ["Relatório", "Mostra resumo consolidado, métricas, roteiro de apresentação e download CSV."],
    ]
    story.append(table(dashboard_rows, [4.0 * cm, 12.0 * cm]))

    section(story, styles, "11. Controles da simulação")
    story += bullets(
        [
            "Gerar próxima leitura ou Próximo ciclo: executa um ciclo.",
            "Rodar 10 ciclos e Rodar 30 ciclos: executam blocos finitos sem loop infinito.",
            "Resetar simulação: limpa ciclo, histórico, consumo acumulado e atuadores.",
            "Baixar CSV: exporta o histórico atual.",
            "Modo manual: permite ajustar temperatura, umidade, luminosidade e presença.",
            "Aplicar leitura manual: registra um ciclo com os valores definidos pelo usuário.",
        ],
        styles,
    )
    story.append(
        p(
            "O Streamlit usa st.session_state para manter controlador, estado atual e widgets. A solução evita loop infinito ao executar "
            "apenas ciclos finitos disparados por botões.",
            styles,
        )
    )

    section(story, styles, "12. Histórico e relatório CSV")
    story.append(
        p(
            "O histórico grava as leituras e decisões de cada ciclo. Ele alimenta a tabela do dashboard, os gráficos, o resumo e o CSV. "
            "Isso permite auditoria, análise de consumo e demonstração acadêmica.",
            styles,
        )
    )
    csv_rows = [["Colunas do CSV", "Descrição"]]
    csv_descriptions = {
        "timestamp": "Data e hora do ciclo.",
        "ciclo": "Número sequencial do ciclo.",
        "modo": "AUTOMATICO ou MANUAL.",
        "temperatura_c": "Temperatura medida.",
        "umidade_percent": "Umidade medida.",
        "luminosidade_percent": "Luminosidade medida.",
        "presenca": "Presença detectada.",
        "iluminacao": "Estado da iluminação.",
        "climatizacao": "Estado do HVAC.",
        "consumo_atual_kw": "Potência atual estimada.",
        "consumo_acumulado_kwh": "Energia acumulada com automação.",
        "consumo_sem_automacao_kwh": "Energia acumulada no cenário base.",
        "economia_kwh": "Economia acumulada.",
        "economia_percentual": "Economia percentual acumulada.",
    }
    for column in CSV_COLUMNS:
        csv_rows.append([column, csv_descriptions[column]])
    story.append(table(csv_rows, [6.0 * cm, 10.0 * cm]))

    section(story, styles, "13. Testes e validação")
    story.append(p("Comandos recomendados para validação:", styles))
    story.append(
        p(
            "python -m compileall .<br/>"
            "python main.py --cycles 3 --sleep 0.1 --output teste_relatorio.csv<br/>"
            "python -m streamlit run dashboard.py",
            styles,
            "code",
        )
    )
    story += bullets(
        [
            "compileall valida sintaxe dos módulos Python.",
            "main.py valida execução em terminal, LCD, ciclos e geração de CSV.",
            "streamlit run valida abertura do dashboard, botões, visual da ESP32, gráficos e histórico.",
        ],
        styles,
    )

    section(story, styles, "14. Resultados obtidos")
    story += bullets(
        [
            "Sistema funcional no terminal.",
            "Dashboard visual em Streamlit.",
            "Placa ESP32 simulada com componentes conectados.",
            "Sensores e atuadores com estados dinâmicos.",
            "LCD simulado atualizado a cada ciclo.",
            "Economia estimada em kWh e percentual.",
            "Histórico gerado e CSV exportável.",
            "Projeto pronto para demonstração acadêmica.",
        ],
        styles,
    )

    section(story, styles, "15. Como a solução resolve o problema")
    story.append(
        p(
            "A solução reduz desperdício ao desligar iluminação e climatização quando não há presença. Ela ajusta iluminação conforme "
            "a luz natural e ajusta climatização conforme temperatura. Além disso, melhora visibilidade sobre consumo por meio de gráficos, "
            "histórico e relatório CSV, permitindo comparar o cenário automatizado com o cenário base sem automação.",
            styles,
        )
    )

    section(story, styles, "16. Possível aplicação real")
    story.append(
        p(
            "A simulação pode evoluir para hardware real com uma ESP32 física, sensor DHT22, LDR, PIR, módulo relé, display LCD I2C, "
            "MQTT, banco de dados e dashboard em nuvem.",
            styles,
        )
    )
    story.append(
        p(
            "Em uma aplicação física, é necessário considerar segurança elétrica, relés adequados à carga, isolamento, validação dos sensores, "
            "aterramento, proteção contra sobrecorrente e normas técnicas aplicáveis.",
            styles,
        )
    )

    section(story, styles, "17. Conclusão")
    story.append(
        p(
            "O projeto demonstra a importância da IoT na eficiência energética. A combinação de sensores, regras de decisão, atuadores e "
            "dashboard cria uma solução clara para monitoramento e automação predial. O uso de uma ESP32 simulada facilita o aprendizado "
            "sobre microcontroladores, sensores, LCD, controle de cargas e análise de dados. A solução tem valor acadêmico e pode servir "
            "como base para uma implementação física em edifícios comerciais.",
            styles,
        )
    )

    return story


def generate_pdf() -> Path:
    """Gera o PDF e retorna o caminho do arquivo."""
    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=A4,
        rightMargin=1.7 * cm,
        leftMargin=1.7 * cm,
        topMargin=1.6 * cm,
        bottomMargin=1.5 * cm,
        title="Relatório Técnico - Solução IoT ESP32",
        author="Projeto Acadêmico",
    )
    doc.build(build_story(), onFirstPage=add_footer, onLaterPages=add_footer)
    return PDF_PATH


def main() -> None:
    """Ponto de entrada do script."""
    pdf_path = generate_pdf()
    print(f"PDF gerado: {pdf_path}")


if __name__ == "__main__":
    main()
