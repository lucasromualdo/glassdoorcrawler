# Registro de Decisao

Data: 2026-02-22

## Decisao

Criar e ativar um ruleset para a branch padrao (`master`) exigindo PR para merge, bloqueando exclusao da branch e force-push.

Tambem foi habilitada a exigencia de resolucao de conversas de review antes do merge.

## Motivo

O repositorio nao tinha ruleset nem protecao de branch. Como o projeto passou a usar issues/PRs para organizar a revisao, a `master` precisava de protecoes minimas para evitar push direto acidental e merges sem revisao explicita.

## Impacto

- Merge na `master` passa a exigir PR
- Nao e possivel fazer force-push na `master`
- Nao e possivel excluir a `master`
- Conversas de review abertas precisam ser resolvidas antes do merge
- Ainda nao ha status checks obrigatorios (CI nao configurado)
- Ainda nao ha approvals obrigatorios (mantido fluxo leve)
- Sem bypass configurado no ruleset (owner tambem segue as regras)

## Revisar em

Revisar apos configurar CI/testes automatizados (issues `#1` e `#2`) para avaliar:

- exigir status checks
- exigir 1 approval
- permitir bypass administrativo (se necessario)

## Referencias

- Ruleset: `Protect default branch (PR + conversation resolution)`
- `docs/manutencao-regras-e-backlog.md`
- Issue `#8`
- PR `#7`
