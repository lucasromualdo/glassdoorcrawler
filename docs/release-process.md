# Processo de Release

Guia rapido para padronizar tags, changelog e GitHub Releases do `glassdoorcrawler`.

## Convencoes

- Versionamento: SemVer (`MAJOR.MINOR.PATCH`)
- Tags Git: prefixo `v` (ex.: `v0.1.1`)
- Fonte da versao do pacote: `pyproject.toml` (`tool.poetry.version`)
- Changelog manual: `CHANGELOG.md`
- Release notes do GitHub: geradas com base em PRs/labels (config em `.github/release.yml`)

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

## Versoes sugeridas para este projeto (fase atual)

- `PATCH` (`0.1.1`): correcoes pequenas (ex.: CLI, docs, infra sem mudar comportamento principal)
- `MINOR` (`0.2.0`): ajustes relevantes de parser/fluxo/CLI
- `MAJOR` (`1.0.0`): somente quando houver comportamento minimamente estavel e validado
