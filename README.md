# glassdoorcrawler

Crawler para coletar dados de vagas no Glassdoor e exportar para Excel.

## Estrutura do projeto

- `glassdoorcrawler/scraper.py`: logica de coleta e parsing
- `glassdoorcrawler/cli.py`: interface de linha de comando
- `main.py`: ponto de entrada compativel com o script antigo

## Instalacao

### Com `pip`

```bash
pip install -r requirements.txt
```

### Com `poetry`

```bash
poetry install
```

## Uso

```bash
python main.py --pages 1 --output belohorizonte_vagas.xlsx
```

Ou via `poetry`:

```bash
poetry run glassdoorcrawler --pages 1
```

## Observacoes

- O HTML do Glassdoor muda com frequencia; ajustes no parsing podem ser necessarios.
- O crawler usa atraso entre requisicoes (`--delay`) para reduzir bloqueios.
