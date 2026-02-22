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

## Manutencao

- Regras do repositorio e ordem sugerida de backlog: `docs/manutencao-regras-e-backlog.md`
- Registro de decisao do ruleset da branch `master`: `docs/decisao-ruleset-master.md`
- Processo de release e checklist: `docs/release-process.md`
- Historico de mudancas por versao: `CHANGELOG.md`
- Classificacao de impacto de release (`release:*`) registrada em issues/PRs para apoiar SemVer
