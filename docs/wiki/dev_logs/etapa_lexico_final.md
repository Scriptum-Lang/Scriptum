# Etapa – Implementação final do Analisador Léxico

## O que foi feito
- Criado `src/scriptum/lexer/afn_to_afd.py` implementando construção de subconjuntos (AFN?AFD) + minimização (Hopcroft) via pipeline oficial.
- Atualizado `scripts/build_afd.py` para gerar `src/scriptum/lexer/tables.json` e `docs/diagramas/afd_final.md` (Mermaid) a partir das ERs de `spec.py`.
- Validado `src/scriptum/lexer/lexer.py` consumindo o AFD final (maximal munch + prioridade) e adicionada mensagem para rodar `scriptum build-lexer` quando necessário.

## Como testar
```bash
# 1) gerar o AFD final + Mermaid
scriptum build-lexer

# 2) rodar o lexer num exemplo
scriptum lex examples/ok/basicos/variaveis.stm

# 3) ver o diagrama:
# abrir docs/diagramas/afd_final.md e checar o grafo mermaid
```

## Critérios da tarefa atendidos

* [x] Algoritmo de construção de subconjuntos (arquivo `src/scriptum/lexer/afn_to_afd.py`)
* [x] Analisador léxico (arquivo `src/scriptum/lexer/lexer.py`)
* [x] Diagrama Mermaid do AFD final (arquivo `docs/diagramas/afd_final.md`)
* [x] Commit único com tudo acima
