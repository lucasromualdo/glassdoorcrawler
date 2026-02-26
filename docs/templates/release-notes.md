# Template de Release Notes

Use este modelo ao editar o texto de um GitHub Release (ex.: `v0.1.1`, `v0.2.0`).

## Versao curta (recomendada)

```md
## Resumo
[1-2 frases sobre o objetivo desta versao e o impacto principal.]

## Principais mudancas
- [Mudanca funcional 1]
- [Mudanca funcional 2]
- [Mudanca de infraestrutura/docs relevante para o release]
- [Compatibilidade / dependencias, se aplicavel]

## Validacao executada
- [Teste manual/automatizado 1]
- [Teste manual/automatizado 2]
- [Resultado resumido]

## Itens relacionados
- PR(s): #[numero], #[numero]
- Issues fechadas neste ciclo: #[numero], #[numero]

## Observacoes
- [Limitacao conhecida]
- [Proximo passo natural]
```

## Versao detalhada (SemVer)

```md
## Resumo
Release `vX.Y.Z` com foco em [correcao/estabilizacao/novas funcionalidades].

## Impacto de versao
- Tipo: `patch` | `minor` | `major`
- Compatibilidade: [sem quebra | com quebra - descrever]

## Principais mudancas
### Added
- ...

### Changed
- ...

### Fixed
- ...

### Removed
- ...

## Validacao executada
- ...
- ...

## Itens relacionados
- PR(s): ...
- Issues: ...

## Observacoes
- ...
```

## Dicas de uso

- Prefira descrever comportamento observado (o que melhorou) em vez de listar apenas implementacao interna.
- Se houver mudanca de dependencia/tooling, cite impacto para quem instala (`pip`, `poetry`, Python minimo, etc.).
- Mantenha links para PRs/issues em uma secao separada para facilitar leitura rapida.
- Se o release fechar milestone, cite o nome do milestone (ex.: `v0.1.0`).
