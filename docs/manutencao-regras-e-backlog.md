# Manutencao: Ruleset e Proximos Passos

Atualizado em: 2026-02-22

## Ruleset atual (branch padrao `master`)

Ruleset ativo: `Protect default branch (PR + conversation resolution)`

Regras aplicadas:

- Bloqueia exclusao da branch (`deletion`)
- Bloqueia force-push (`non_fast_forward`)
- Exige PR para merge (`pull_request`)
- Exige resolucao de conversas de review antes do merge
- Nao exige approvals (por enquanto)
- Nao exige status checks (por enquanto, sem CI)

Observacao:

- Sem bypass configurado (ate o owner precisa seguir PR + resolucao de conversas)

## Quando revisar esse ruleset

Rever quando:

- Adicionar CI/testes automatizados
- Comecar a receber contribuicoes externas
- Precisar acelerar hotfix (avaliar bypass admin)

## Proximas issues (ordem sugerida)

1. `#8` validar parametros do CLI (`--pages` e `--delay`)
2. `#1` validar execucao real do crawler (1 pagina)
3. `#2` adicionar testes de parsing e paginacao
4. `#5` melhorar documentacao (README / limitacoes / contribuicao)
5. `#3` atualizar dependencias e regenerar `poetry.lock`
6. `#4` adaptar parser ao HTML atual do Glassdoor

## Ajustes de ruleset (depois que tiver CI)

Quando houver workflow de testes:

1. Exigir status checks obrigatorios (ex.: testes)
2. Opcional: exigir `1` approval
3. Opcional: manter/ajustar regra de resolucao de conversas

## Dica de manutencao

Sempre que decidir algo de repositorio (ruleset, fluxo de PR, CI), registrar:

- O que foi decidido
- Motivo
- Data
- Quando revisar novamente

## Registros de decisao

- Ruleset da `master`: `docs/decisao-ruleset-master.md`
