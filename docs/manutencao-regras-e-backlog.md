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

## Status rapido do backlog (2026-02-22)

- `#8` concluida (PR `#14`, issue fechada)
- `#16` concluida (organizacao inicial de releases; PR `#15`, issue fechada)
- `#1` em andamento (`In Progress`) com diagnostico registrado (`403 Forbidden` na coleta)

## Proximas issues (ordem sugerida)

1. `#1` validar execucao real do crawler (1 pagina)
2. `#4` adaptar parser ao HTML atual do Glassdoor
3. `#2` adicionar testes de parsing e paginacao
4. `#13` configurar CI no GitHub Actions (pytest + checks basicos)
5. `#3` atualizar dependencias e regenerar `poetry.lock`
6. `#12` adicionar LICENSE e documentos de governanca
7. `#11` configurar Dependabot
8. `#10` remover artefato versionado da raiz e ajustar politica de outputs
9. `#5` melhorar documentacao (README / limitacoes / contribuicao)

## Classificacao de release (SemVer)

As issues agora usam labels `release:*` para indicar impacto de versao:

- `release:none`: docs/infra/processo/testes sem impacto funcional direto
- `release:patch`: correcoes/ajustes compativeis
- `release:minor`: mudancas relevantes compativeis
- `release:major`: mudancas incompativeis/importantes

Referencia detalhada: `docs/release-process.md`

## Separacao pratica para releases (resumo)

- Ciclo A (release funcional do crawler): `#1`, `#4`, `#3` + recomendados `#2`, `#13`
- Ciclo B (governanca/manutencao): `#12`, `#11`, `#10`, `#5`
- Concluidas relevantes para historico de release: `#6`, `#8`, `#16`

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
