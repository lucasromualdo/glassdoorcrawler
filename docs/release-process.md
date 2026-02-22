# Processo de Release

Guia rapido para padronizar tags, changelog e GitHub Releases do `glassdoorcrawler`.

## Convencoes

- Versionamento: SemVer (`MAJOR.MINOR.PATCH`)
- Tags Git: prefixo `v` (ex.: `v0.1.1`)
- Fonte da versao do pacote: `pyproject.toml` (`tool.poetry.version`)
- Changelog manual: `CHANGELOG.md`
- Release notes do GitHub: geradas com base em PRs/labels (config em `.github/release.yml`)
- Labels de impacto de release:
  - `release:none` (sem impacto funcional direto: docs/infra/processo/testes)
  - `release:patch` (correcao/ajuste sem mudanca relevante de comportamento)
  - `release:minor` (nova capacidade ou mudanca compativel relevante)
  - `release:major` (mudanca incompativel/importante)

## Politica de classificacao (issues e PRs)

Objetivo: facilitar decisao de versao (`PATCH`/`MINOR`/`MAJOR`) olhando backlog e PRs concluidos.

Regras praticas:

- Toda issue relevante para entrega deve ter um label `release:*`
- PRs devem herdar (ou refletir) o mesmo impacto de release da issue relacionada
- Itens de docs/infra/processo/teste sem impacto funcional direto usam `release:none`
- Em caso de duvida, prefira `release:patch` e revise antes da tag

Exemplos no projeto:

- `#1`, `#3`, `#4`, `#8` -> `release:patch`
- `#6` -> `release:minor`
- `#2`, `#5`, `#10`, `#11`, `#12`, `#13`, `#16` -> `release:none`

## Quando criar release

Recomendado apos um conjunto coerente de correcoes/melhorias, com branch `master` estavel.

Antes do primeiro fluxo de release "regular", priorize:

- validacao de execucao real do crawler
- ajuste do parser ao HTML atual
- testes automatizados minimos
- CI no GitHub Actions

## Checklist de pre-release

1. Garantir que a `master` local esta atualizada:
   - `git switch master`
   - `git pull --ff-only`
2. Confirmar PRs relevantes mergeados e sem mudancas locais pendentes:
   - `git status`
   - revisar labels `release:*` das issues/PRs que entraram no ciclo
3. Atualizar `CHANGELOG.md`:
   - mover itens de `Unreleased` para a nova versao
   - adicionar data (`YYYY-MM-DD`)
4. Atualizar a versao em `pyproject.toml`
5. Validar o projeto localmente (comandos disponiveis no momento)
6. Commitar a preparacao do release:
   - `git add CHANGELOG.md pyproject.toml`
   - `git commit -m "chore(release): prepara vX.Y.Z"`

## Criar tag e publicar

1. Criar tag anotada:
   - `git tag -a vX.Y.Z -m "release: vX.Y.Z"`
2. Enviar branch e tag:
   - `git push origin master`
   - `git push origin vX.Y.Z`
3. Criar GitHub Release (com notas geradas):
   - `gh release create vX.Y.Z --generate-notes`

Opcional (titulo customizado):

- `gh release create vX.Y.Z --title "vX.Y.Z" --generate-notes`

## Checklist de pos-release

1. Confirmar que o release apareceu no GitHub
2. Validar que as notas estao classificadas corretamente (labels)
3. Abrir ciclo novo mantendo `CHANGELOG.md` com secao `Unreleased`
4. (Opcional) revisar se houve issue/PR sem label `release:*` e corrigir para o proximo ciclo

## Estado atual (2026-02-22)

- Base de release criada e mergeada:
  - `CHANGELOG.md`
  - `docs/release-process.md`
  - `.github/release.yml`
- Labels `release:*` criados e aplicados nas issues do backlog atual
- Ainda nao existem tags Git nem GitHub Releases publicados

## Separacao do backlog por release (issues)

### 1) Impacto direto de release (mudanca funcional)

Entram no calculo de versao (`PATCH`/`MINOR`/`MAJOR`):

- `release:patch` (abertas): `#1`, `#3`, `#4`
- `release:patch` (concluida): `#8`
- `release:minor` (concluida): `#6`
- `release:major`: nenhuma issue no momento

### 2) Suporte ao release (nao muda versao, mas melhora qualidade)

Usam `release:none`, mas ajudam a estabilizar/publicar:

- `#2` testes de parsing e paginacao
- `#13` CI no GitHub Actions
- `#5` documentacao de limites e fluxo de contribuicao

### 3) Organizacao/infra que pode rodar em paralelo (sem bloquear release funcional)

Tambem `release:none`:

- `#10` limpeza de artefato e politica de outputs
- `#11` Dependabot
- `#12` LICENSE + governanca (CONTRIBUTING/SECURITY/CODEOWNERS)
- `#16` organizacao de release (ja concluida)

## Proposta de separacao por ciclos

### Ciclo A - Estabilizacao do crawler (release funcional)

Objetivo: publicar um release com execucao real validada e parser ajustado.

- Core (impacta release): `#1`, `#4`, `#3`
- Qualidade minima recomendada antes de publicar: `#2`, `#13`
- Ja concluido e incluso no historico do ciclo: `#8`

Observacao:

- Como `#6` (estrutura do projeto/CLI) ja foi mergeada e esta classificada como `release:minor`, o primeiro release publicado pode ser tratado como `MINOR` (ex.: `v0.2.0`) se voce quiser refletir essa evolucao acumulada.
- Alternativa conservadora: publicar `v0.1.0` como baseline e usar os labels apenas para releases seguintes.

### Ciclo B - Governanca e manutencao de release

Objetivo: melhorar operacao/manutencao sem alterar comportamento principal.

- `#12` governanca/licenca
- `#11` Dependabot
- `#10` outputs/artefatos
- `#5` documentacao complementar

## Versoes sugeridas para este projeto (fase atual)

- `PATCH` (`0.1.1`): correcoes pequenas (ex.: CLI, docs, infra sem mudar comportamento principal)
- `MINOR` (`0.2.0`): ajustes relevantes de parser/fluxo/CLI
- `MAJOR` (`1.0.0`): somente quando houver comportamento minimamente estavel e validado
