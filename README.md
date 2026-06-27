# esp_sensor

Projeto acadêmico de simulação IoT para eficiência energética com ESP32.

O código principal está na pasta `iot_eficiencia_energetica/`.

## Execução local

Terminal:

```bash
cd iot_eficiencia_energetica
python main.py
```

Dashboard Streamlit:

```bash
cd iot_eficiencia_energetica
python -m streamlit run dashboard.py
```

Versão Flask compatível com Vercel:

```bash
python api/index.py
```

## Deploy na Vercel

Este repositório possui:

- `api/index.py`: entrypoint Flask que exporta `app`;
- `vercel.json`: roteia todas as requisições para `api/index.py`;
- `requirements.txt`: dependências mínimas para o deploy Flask.

Na Vercel, selecione a raiz do repositório `esp_sensor`, não a subpasta `iot_eficiencia_energetica`.

## Observação

A versão Streamlit continua disponível para uso local. A versão Vercel usa Flask porque a Vercel executa funções serverless Python e espera uma variável top-level como `app`, `application` ou `handler`.
