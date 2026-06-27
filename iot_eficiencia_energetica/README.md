# Imersão 2 - Solução IoT para Eficiência Energética com ESP32

Aplicação acadêmica em Python que simula uma solução IoT com ESP32 para eficiência energética em edifícios comerciais. O sistema monitora ambiente, controla iluminação e climatização, exibe um LCD simulado, calcula consumo de energia, estima economia, registra histórico, exporta CSV e apresenta uma bancada visual da ESP32 funcionando em tempo real no Streamlit.

O projeto não exige hardware físico. Sensores, atuadores, placa, LCD e conexões são simulados em software para facilitar apresentação, testes e entendimento da lógica de automação predial.

## Objetivo

Demonstrar como uma ESP32 pode ser usada para reduzir desperdício de energia em salas comerciais.

O sistema busca:

- monitorar temperatura, umidade, luminosidade e presença;
- ligar iluminação apenas quando há presença e pouca luz natural;
- ligar climatização apenas quando há presença e desconforto térmico;
- comparar consumo com automação contra consumo base sem automação;
- mostrar sensores, atuadores, LCD e GPIOs de forma visual;
- gerar histórico e relatório CSV para análise.

## Funcionalidades Implementadas

- Simulação de sensores DHT22/DHT11, LDR e PIR.
- Controle automático de iluminação.
- Controle automático de climatização.
- Modo manual para forçar leituras de demonstração.
- Cenários prontos: sem presença, escuro com presença, temperatura alta e conforto ECO.
- Cálculo de potência atual em kW.
- Cálculo de consumo acumulado com automação.
- Cálculo de consumo estimado sem automação.
- Cálculo de economia em kWh e percentual.
- LCD simulado 20x4 para terminal, dashboard e placa visual.
- Dashboard em Streamlit.
- Aba visual da ESP32 em HTML/SVG inline.
- Sensores e atuadores conectados visualmente à ESP32.
- Mapa de pinos GPIO.
- Botões para gerar próxima leitura, rodar ciclos e resetar.
- Gráficos com Plotly.
- Histórico com Pandas.
- Exportação CSV.
- Execução pelo terminal com argumentos.

## Estrutura do Projeto

```text
iot_eficiencia_energetica/
  main.py
  dashboard.py
  sensors.py
  actuators.py
  controller.py
  lcd.py
  energy.py
  report.py
  board_view.py
  config.py
  requirements.txt
  README.md
```

Arquivos CSV como `relatorio.csv` e `relatorio_eficiencia_energetica.csv` podem aparecer após executar a simulação. Eles são relatórios gerados, não módulos do sistema.

## Arquitetura da Solução

| Arquivo | Responsabilidade |
| --- | --- |
| `config.py` | Configurações globais, limites, potências, nomes de componentes e mapa de pinos. |
| `sensors.py` | Classes dos sensores simulados: temperatura, umidade, luminosidade e presença. |
| `actuators.py` | Classes dos atuadores simulados: iluminação e climatização. |
| `controller.py` | Cérebro do sistema. Lê sensores, aplica regras, atualiza atuadores, calcula energia, LCD e histórico. |
| `lcd.py` | Gera o texto do LCD 20x4 para terminal, dashboard e visual da placa. |
| `energy.py` | Calcula potência atual, consumo por intervalo, consumo base e economia. |
| `report.py` | Converte histórico em DataFrame, exporta CSV e gera resumo da simulação. |
| `board_view.py` | Renderiza a placa ESP32 e componentes em HTML/SVG inline. |
| `dashboard.py` | Interface Streamlit com abas, controles, gráficos, histórico e relatório. |
| `main.py` | Execução simples via terminal, com ciclos e exportação CSV. |

## Componentes Simulados

### Sensores

| Sensor | Classe | Leitura |
| --- | --- | --- |
| DHT22/DHT11 - temperatura | `TemperatureSensor` | Temperatura em °C, com variação gradual e limites de 18 a 32 °C. |
| DHT22/DHT11 - umidade | `HumiditySensor` | Umidade relativa em %, com limites de 30 a 80%. |
| LDR | `LightSensor` | Luminosidade de 0 a 100%, com simulação de ciclo de luz e sombras. |
| PIR | `PresenceSensor` | Presença detectada ou ausente, com probabilidades de entrada e saída. |

### Atuadores

| Atuador | Classe | Estados |
| --- | --- | --- |
| Relé/lâmpada de iluminação | `LightingActuator` | `OFF`, `LOW`, `MEDIUM`, `HIGH` |
| Relé/climatização | `HVACActuator` | `OFF`, `FAN`, `COOLING`, `HEATING`, `ECO` |
| LCD I2C 20x4 | `LCDDisplay` | Texto com temperatura, umidade, luz, presença, HVAC, consumo e economia. |

## Mapa de Pinos da ESP32

Mapa real definido em `config.py`:

```python
PIN_MAP = {
    "DHT22": "GPIO 4",
    "LDR": "GPIO 34",
    "PIR": "GPIO 27",
    "LIGHT_RELAY": "GPIO 26",
    "HVAC_RELAY": "GPIO 25",
    "LCD_SDA": "GPIO 21",
    "LCD_SCL": "GPIO 22",
}
```

## Lógica de Automação

Valores reais configurados:

- Temperatura confortável mínima: `22.0 °C`
- Temperatura confortável máxima: `25.0 °C`
- Limite de baixa luminosidade: `40%`
- Limite de luminosidade média: `70%`
- Potência estimada da iluminação: `0.4 kW`
- Potência estimada da climatização: `1.5 kW`
- Potência simulada da ESP32/controlador: `0.02 kW`
- Potência base sem automação: `2.2 kW`
- Intervalo padrão de simulação: `2 s`

Regras implementadas no `IoTController`:

```text
Se não houver presença:
  iluminação = OFF
  climatização = OFF

Se houver presença e luminosidade < 40:
  iluminação = HIGH

Se houver presença e luminosidade >= 40 e < 70:
  iluminação = LOW

Se houver presença e luminosidade >= 70:
  iluminação = OFF

Se houver presença e temperatura > 25:
  climatização = COOLING

Se houver presença e temperatura < 22:
  climatização = HEATING

Se houver presença e temperatura entre 22 e 25:
  climatização = ECO
```

## Cálculo de Consumo e Economia

O consumo com automação considera:

- potência do controlador;
- potência da iluminação multiplicada pelo fator do estado;
- potência da climatização multiplicada pelo fator do modo.

O consumo sem automação usa `BASELINE_POWER_KW = 2.2`.

```text
economia_kWh = consumo_sem_automacao - consumo_com_automacao
economia_percentual = economia_kWh / consumo_sem_automacao * 100
```

## Dashboard

Execute:

```bash
streamlit run dashboard.py
```

ou:

```bash
python -m streamlit run dashboard.py
```

O dashboard possui as abas reais abaixo.

### 1. Visão Geral

Mostra temperatura, umidade, luminosidade, presença, iluminação, climatização, consumo acumulado, economia percentual, LCD simulado, ciclo atual, modo atual e status da ESP32.

Controles:

- `Gerar proxima leitura`
- `Rodar 10 ciclos`
- `Rodar 30 ciclos`
- `Resetar simulacao`
- `Baixar CSV`

### 2. Placa ESP32

Mostra a bancada visual da ESP32 renderizada por `board_view.py` com HTML/SVG inline, sem imagens externas.

### 3. Simulador

Centraliza os controles:

- seleção `Automatico` ou `Manual`;
- slider de intervalo simulado por ciclo;
- `Proximo ciclo`;
- `Rodar 10 ciclos`;
- `Rodar 30 ciclos`;
- `Resetar`;
- sliders de temperatura, umidade e luminosidade;
- toggle de presença;
- `Aplicar leitura manual`;
- cenários prontos.

O dashboard não usa loop infinito. Cada botão executa uma quantidade finita de ciclos.

### 4. Gráficos

Exibe gráficos Plotly:

- temperatura;
- umidade;
- luminosidade;
- presença;
- consumo com automação vs sem automação;
- economia percentual.

O gráfico de presença usa linha em degrau com `line_shape="hv"`.

### 5. Histórico

Mostra tabela Pandas com:

- `timestamp`
- `ciclo`
- `modo`
- `temperatura_c`
- `umidade_percent`
- `luminosidade_percent`
- `presenca`
- `iluminacao`
- `climatizacao`
- `consumo_atual_kw`
- `consumo_acumulado_kwh`
- `consumo_sem_automacao_kwh`
- `economia_kwh`
- `economia_percentual`

Também possui `Limpar historico e resetar simulacao`.

### 6. Relatório

Mostra total de ciclos, tempo simulado, tempo com presença, tempo sem presença, consumo com automação, consumo sem automação, economia, acionamentos, médias e download CSV.

## Interface Visual da ESP32

A visualização está em `board_view.py`:

```python
render_esp32_board(state: dict | None) -> str
```

Na tela aparecem:

- ESP32 DevKit no centro;
- pinos GPIO visíveis;
- DHT22, LDR e PIR à esquerda;
- relé de iluminação, lâmpada, relé HVAC e climatização à direita;
- LCD I2C 20x4;
- fios coloridos;
- mapa de pinos;
- legenda de cores;
- consumo atual e economia.

### Interpretação das cores

| Cor | Significado |
| --- | --- |
| Verde | Normal, ativo, presença detectada ou modo econômico. |
| Cinza | Inativo, desligado, sem presença ou fio sem acionamento. |
| Amarelo/laranja | Luz baixa, iluminação acionada ou aquecimento. |
| Azul | Climatização em resfriamento (`COOLING`). |
| Vermelho | Temperatura acima do limite de conforto. |

## Controles da Simulação

| Controle | Onde fica | Ação |
| --- | --- | --- |
| `Gerar proxima leitura` | Visão Geral | Executa 1 ciclo. |
| `Rodar 10 ciclos` | Visão Geral e Simulador | Executa 10 ciclos finitos. |
| `Rodar 30 ciclos` | Visão Geral e Simulador | Executa 30 ciclos finitos. |
| `Resetar simulacao` / `Resetar` | Visão Geral, Simulador e Histórico | Limpa histórico, ciclo, consumo e atuadores. |
| `Aplicar leitura manual` | Simulador | Registra 1 ciclo com valores dos sliders. |
| `Baixar CSV` / `Baixar relatorio CSV` | Visão Geral e Relatório | Exporta o histórico atual. |

## Modo Manual

Na aba `Simulador`, o usuário pode ajustar:

- temperatura (`18.0` a `32.0 °C`);
- umidade (`30.0` a `80.0%`);
- luminosidade (`0.0` a `100.0%`);
- presença (`ligado/desligado`).

Cenários prontos:

- `Sem presenca`
- `Escuro com presenca`
- `Temperatura alta`
- `Conforto ECO`

## Gráficos e Histórico

Os gráficos explicam a evolução da simulação. O histórico é a base do CSV e dos relatórios. Cada chamada de `step()` registra uma linha com leituras, estados dos atuadores e dados de energia.

## Relatório CSV

O relatório pode ser gerado pelo terminal ou pelo dashboard.

Nome padrão:

```text
relatorio_eficiencia_energetica.csv
```

Colunas:

```text
timestamp
ciclo
modo
temperatura_c
umidade_percent
luminosidade_percent
presenca
iluminacao
climatizacao
consumo_atual_kw
consumo_acumulado_kwh
consumo_sem_automacao_kwh
economia_kwh
economia_percentual
```

## Relatório Acadêmico em PDF

O projeto inclui um script para gerar um relatório técnico acadêmico completo em PDF:

```bash
python generate_report.py
```

O arquivo gerado fica na raiz do projeto:

```text
RELATORIO_SOLUCAO_IOT_ESP32.pdf
```

O relatório explica o problema de eficiência energética, a arquitetura da solução, os sensores e atuadores simulados, a ESP32, o LCD, o dashboard, a lógica de automação, o cálculo de consumo/economia, os testes e a possibilidade de migração para hardware real.

## Instalação

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Linux/macOS

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Instalação direta:

```bash
pip install -r requirements.txt
```

Dependências:

```text
streamlit
pandas
plotly
```

## Como Executar

### Terminal

```bash
python main.py
```

Com opções:

```bash
python main.py --cycles 30 --sleep 0.2 --output relatorio.csv
```

### Dashboard

```bash
streamlit run dashboard.py
```

ou:

```bash
python -m streamlit run dashboard.py
```

Abra:

```text
http://localhost:8501
```

### Versão Flask para Vercel

A versão de deploy para Vercel fica em `api/index.py`, na raiz do repositório, e exporta a variável top-level `app` exigida pelo runtime Python da Vercel.

Para testar localmente a versão Flask a partir da raiz do repositório:

```bash
python api/index.py
```

Depois abra:

```text
http://localhost:5000
```

Rotas disponíveis na versão Flask:

- `/`: página principal com cards, LCD, ESP32 visual, controles e histórico recente;
- `/step`: executa 1 ciclo;
- `/run/10`: executa 10 ciclos;
- `/run/30`: executa 30 ciclos;
- `/reset`: reseta a simulação;
- `/csv`: baixa o histórico em CSV.

Na Vercel, selecione a raiz do repositório `esp_sensor`. O arquivo `vercel.json` direciona as requisições para `api/index.py`, evitando que o `main.py` de terminal seja usado como entrypoint web.

## Como Apresentar em Sala

1. Explique o desperdício de energia em salas comerciais.
2. Abra o dashboard.
3. Mostre a aba `Placa ESP32` e explique sensores, atuadores, GPIOs e LCD.
4. Rode ciclos automáticos.
5. Use o modo manual para demonstrar sem presença, ambiente escuro e temperatura alta.
6. Mostre a iluminação e climatização mudando.
7. Abra `Graficos` para comparar consumo com e sem automação.
8. Abra `Historico` para mostrar os dados registrados.
9. Exporte o CSV em `Relatorio`.
10. Explique como migrar a lógica para uma ESP32 real.

## Testes e Validação

```bash
python -m compileall .
python main.py --cycles 3 --sleep 0.1 --output teste_relatorio.csv
python -m streamlit run dashboard.py
```

O arquivo `teste_relatorio.csv` é apenas um artefato de validação e pode ser apagado depois.

## Observações Técnicas

- O Streamlit usa `st.session_state` para manter controlador, estado atual e controles.
- O reset limpa histórico, consumo acumulado, ciclo e atuadores.
- Os botões executam ciclos finitos.
- A placa visual funciona offline com SVG/HTML inline.
- O gráfico de presença usa `px.line(...).update_traces(line_shape="hv")`.

## Melhorias Futuras

- Integração com ESP32 física.
- Firmware em Arduino IDE.
- Firmware em MicroPython.
- Comunicação MQTT.
- Persistência em SQLite.
- Persistência temporal em InfluxDB.
- Cálculo de custo em reais por tarifa.
- Controle direto manual dos atuadores.
- Autenticação no dashboard.
- Alertas por Telegram, e-mail ou webhook.
- Sensores DHT22, LDR e PIR reais.
- Dashboard em nuvem.
