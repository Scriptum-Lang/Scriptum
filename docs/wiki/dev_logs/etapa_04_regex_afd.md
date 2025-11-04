# Etapa 04 — Construção de AFN, AFD e minimização

## Algoritmos adotados
- **Thompson**: cada expressão regular definida em `spec.TOKEN_PATTERNS` é convertida em AFN combinando fragmentos (sequência, alternância, quantificadores e classes de caracteres). Um nó inicial universal liga todos os padrões, preservando as prioridades para resolução de conflitos.
- **Subconjuntos + Hopcroft**: o AFN combinado é determinizado (construção por subconjuntos). Em seguida aplicamos a minimização de Hopcroft, depois de tornar o AFD total (inclusão de estado sumidouro), garantindo a estrutura mínima compatível com os diagramas históricos de identificadores e números.

## Geração do AFD
- Execute o gerador a partir da raiz do projeto Python (`scriptum/`):
  ```bash
  python scripts/build_afd.py --show
  ```
- O comando valida as ERs, monta o AFN, determina/minimiza o AFD e persiste `src/scriptum/lexer/tables.json`. Com `--show`, a tabela completa (estados, transições e token associado) é exibida no terminal.

## Verificação
- Testes unitários focados:
  ```bash
  pytest -q tests/test_lexer_tokens.py
  pytest -q tests/test_dfa_minimization.py
  ```
- O primeiro garante metadados consistentes e que todos os literais/keywords estão cobertos. O segundo valida o número mínimo de estados para identificadores e o comportamento aceitando/recusando literais numéricos conforme os diagramas `afd-identificador` e `afd-numero`.
