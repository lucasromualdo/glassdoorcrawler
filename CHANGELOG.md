# Changelog

Todas as mudancas relevantes deste projeto devem ser registradas aqui.

Este arquivo segue um formato simples inspirado em "Keep a Changelog" e usa versionamento SemVer.
Enquanto o projeto estiver em `0.x`, mudancas podem acontecer com mais frequencia.

## [Unreleased]

### Added
- Placeholder para novas funcionalidades ainda nao lancadas.
- Opcao de CLI `--no-proxy` para ignorar proxies do ambiente na coleta.

### Changed
- Placeholder para ajustes de comportamento ainda nao lancados.
- Coleta passa a tentar fallback automatico via `curl_cffi` ao detectar bloqueio de seguranca do Cloudflare.

### Fixed
- Placeholder para correcoes ainda nao lancadas.
- Parsing de links da busca atualizado para URLs `/job-listing/` do HTML atual.
- Parsing de detalhes da vaga adiciona fallback via `JSON-LD` (`JobPosting`) quando `initialState` nao existe.

### Removed
- Placeholder para remocoes ainda nao lancadas.

## Como usar

- Registre mudancas em `Unreleased` durante o desenvolvimento.
- Use os labels `release:*` das issues/PRs para ajudar a decidir a versao do proximo release.
- No release, mova os itens para uma secao versionada (`## [0.1.1] - YYYY-MM-DD`).
- Crie a tag Git correspondente (`v0.1.1`) e publique o GitHub Release.
