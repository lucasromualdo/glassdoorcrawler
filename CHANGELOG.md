# Changelog

Todas as mudancas relevantes deste projeto devem ser registradas aqui.

Este arquivo segue um formato simples inspirado em "Keep a Changelog" e usa versionamento SemVer.
Enquanto o projeto estiver em `0.x`, mudancas podem acontecer com mais frequencia.

## [Unreleased]

### Added
- Placeholder para novas funcionalidades ainda nao lancadas.
- Opcao de CLI `--no-proxy` para ignorar proxies do ambiente na coleta.
- Suite de testes automatizados para parsing e paginacao em `tests/test_scraper.py`.
- Workflow de CI no GitHub Actions (`.github/workflows/ci.yml`) com execucao em push/PR para `master`, checks basicos e `pytest`.

### Changed
- Placeholder para ajustes de comportamento ainda nao lancados.
- Coleta passa a tentar fallback automatico via `curl_cffi` ao detectar bloqueio de seguranca do Cloudflare.

### Fixed
- Placeholder para correcoes ainda nao lancadas.
- Parsing de links da busca atualizado para URLs `/job-listing/` do HTML atual.
- Parsing de detalhes da vaga adiciona fallback via `JSON-LD` (`JobPosting`) quando `initialState` nao existe.

### Removed
- Placeholder para remocoes ainda nao lancadas.

## [0.1.0] - 2026-02-26

### Added
- Opcao de CLI `--no-proxy` para ignorar proxies do ambiente na coleta.

### Changed
- Coleta passa a tentar fallback automatico via `curl_cffi` ao detectar bloqueio de seguranca do Cloudflare.
- Paginacao de resultados para `--pages > 1` usa endpoint BFF do Glassdoor (`jobSearchResultsQuery`) com cursor extraido do payload Next.js.
- `poetry.lock` regenerado e dependencia `curl_cffi` adicionada com marker de Python `>=3.10`.

### Fixed
- Parsing de links da busca atualizado para URLs `/job-listing/` do HTML atual.
- Parsing de detalhes da vaga adiciona fallback via `JSON-LD` (`JobPosting`) quando `initialState` nao existe.

### Removed
- Nenhuma remocao nesta versao.

## Como usar

- Registre mudancas em `Unreleased` durante o desenvolvimento.
- Use os labels `release:*` das issues/PRs para ajudar a decidir a versao do proximo release.
- No release, mova os itens para uma secao versionada (`## [0.1.1] - YYYY-MM-DD`).
- Crie a tag Git correspondente (`v0.1.1`) e publique o GitHub Release.
