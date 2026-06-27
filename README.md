# esp_sensor

Projeto academico de simulacao IoT para eficiencia energetica com ESP32.

O codigo principal esta em `iot_eficiencia_energetica/`. A versao local usa
terminal e Streamlit. A versao de deploy para Vercel usa Flask em `api/`.

## Execucao local

Terminal:

```bash
cd iot_eficiencia_energetica
python main.py
```

Dashboard Streamlit local:

```bash
cd iot_eficiencia_energetica
python -m streamlit run dashboard.py
```

Versao Flask compativel com Vercel, a partir da raiz do repositorio:

```bash
python api/index.py
```

Abra:

```text
http://localhost:5000
```

## Versao Flask/Vercel

A Vercel usa `api/index.py` como entrypoint. Esse arquivo exporta a variavel
top-level `app`, exigida pelo runtime Python da Vercel, e carrega a aplicacao
completa definida em `api/web_app.py`.

Recursos disponiveis na versao Flask:

- Visao Geral com cards de sensores, atuadores, consumo, economia, ciclo e LCD.
- Placa ESP32 visual via HTML/SVG offline usando `render_esp32_board`.
- Simulador com proximo ciclo, 10 ciclos, 30 ciclos e ciclos personalizados.
- Modo automatico/manual com formulario de temperatura, umidade, luminosidade e presenca.
- Cenarios prontos para demonstracao.
- Graficos SVG offline para temperatura, umidade, luminosidade, presenca, consumo e economia.
- Historico com filtro de ultimas 10, 25, 50 linhas ou todos os registros.
- Relatorio com resumo de ciclos, tempo, consumo, economia e acionamentos.
- Download CSV e download do PDF academico quando o arquivo existir no deploy.
- Endpoints `/health` e `/api/state` para validacao/debug.

Rotas principais:

```text
/              dashboard Flask completo
/step          executa 1 ciclo
/run/10        executa 10 ciclos
/run/30        executa 30 ciclos
/run-custom    executa ciclos personalizados via POST
/manual        aplica leitura manual via POST
/mode          alterna automatico/manual via POST
/reset         reseta a simulacao
/csv           baixa o historico CSV
/pdf           baixa o relatorio PDF academico
/health        health check
/api/state     estado atual em JSON
```

## Deploy na Vercel

Este repositorio possui:

- `api/index.py`: entrypoint Flask que exporta `app`;
- `api/web_app.py`: aplicacao Flask completa;
- `vercel.json`: roteia todas as requisicoes para `api/index.py`;
- `requirements.txt`: dependencias para o deploy Flask.

Na Vercel, selecione a raiz do repositorio `esp_sensor`, nao a subpasta
`iot_eficiencia_energetica`.

Com Vercel CLI instalado:

```bash
vercel build
vercel deploy
```

## Observacao sobre serverless

A Vercel executa funcoes serverless. O estado em memoria pode reiniciar entre
invocacoes ou novas instancias. Para demonstracao academica, a simulacao funciona
durante a vida da instancia. Para persistencia real, use banco de dados ou
armazenamento externo.

A versao Streamlit continua disponivel para uso local. A versao Vercel usa Flask
porque a Vercel espera uma variavel top-level como `app`, `application` ou
`handler`.
