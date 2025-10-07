# Etapa 01 — Contexto e Planejamento

## Propósito do compilador
- Implementar um pipeline completo em Python 3.11+ que traduza programas Scriptum (`.stm`) — linguagem com sintaxe estilo JS, tokens em latim e tipagem explícita — em representações internas, verificando programas e preparando-os para geração futura de código/execução.
- Cobrir as fases descritas em `docs/wiki/01_gramatica.md` a `06_ir_codegen.md`: análise léxica via DFA, parsing híbrido (descida recursiva + Pratt), construção da AST canônica, verificação semântica/contextual sensível ao escopo, lowering para IR estruturado e emissão de saída formatada.
- Respeitar a gramática formal de `docs/wiki/legacy/gramatica_formal.md`, garantindo aderência às decisões históricas (precedência, resolução de `aliter`, estruturas opcionais).

## Estrutura atual das pastas
- `docs/wiki/`: especificações principais do compilador (gramática, léxico, parser, AST, tipos e IR/codegen) e histórico em `legacy/`.
- `docs/diagrams/legacy/`: diagramas de apoio ao léxico (`afd-identificador`, `afd-numero`, `fluxo-analise-lexica`).
- `examples/ok/`: programas válidos (básicos, intermediários, avançados) usados como oráculos de sucesso.
- `examples/err/negativos/`: programas com falhas esperadas, úteis para testes de diagnóstico (`tipo_incompativel.stm`).
- `LICENSE`: referência de licenciamento.

## Artefatos a serem gerados em Python
- Pacote `scriptum` com submódulos: `lexer`, `parser`, `ast`, `types`, `ir`, `codegen`, `cli`.
- Estruturas imutáveis e com spans (ex.: tokens, nós da AST, IR) alinhadas às descrições existentes.
- Tabelas de símbolos, enumerações de tipos e diagnósticos modeladas conforme `05_tipos_semantica.md`.
- Rotinas de lowering e pretty printing seguindo `06_ir_codegen.md`, incluindo saída estruturada (`ModuleIr`, `CodegenOutput`).
- Ferramentas de suporte: interner simples, utilitários de spans, pipeline de compilação e ponto de entrada CLI (`scriptumc` ou similar).

## Estratégia geral (módulos, testes e logs)
- **Módulos**: implementar as fases na ordem do pipeline, consolidando contratos entre componentes antes de avançar. Cada módulo Python terá testes unitários focados nas garantias da fase (ex.: tokens para o lexer, árvores para o parser).
- **Testes**: automatizar execuções sobre `examples/ok` assegurando sucesso em todas as fases, e sobre `examples/err/negativos` confirmando diagnósticos específicos (por exemplo, atribuição tipada inválida). Sempre que possível, transformar casos em testes parametrizados.
- **Logs por etapa**: a cada bloco do cronograma, criar relatório em `docs/wiki/dev_logs/` detalhando decisões, estado do código e instruções de validação (comandos de teste, entradas esperadas). Este documento inaugura o diretório e serve como referência do plano.
- **Integração**: manter CLI que encadeia as fases, preservando `Span`/`NodeId` para inspeção e garantindo que falhas interrompam o pipeline de forma controlada.

## Como testar após esta etapa
- Verificar documentação consultada (`docs/wiki/*` e `docs/diagrams/legacy/*`), confirmando entendimento comum.
- Validar disponibilidade dos exemplos de entrada (`examples/ok` e `examples/err/negativos`) para futura automação de testes.
- Revisar este log como checklist inicial antes de iniciar a implementação das fases.
