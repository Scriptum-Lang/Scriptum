# Analise semantica passo a passo

Este documento detalha como o modulo `sema` valida a AST produzida pelo parser e garante regras semanticas basicas de Scriptum.

## 1. Componentes principais

- `SemanticAnalyzer` (`sema/analyzer.py`): ponto de entrada da fase.
- `SymbolTable` (`sema/symbols.py`): pilha de escopos com declaracoes (`Symbol` guarda nome, tipo, mutabilidade e span).
- `types.py`: representa tipos primitivos (`PRIMITIVE_TYPES`), tipos derivados e funcoes utilitarias como `type_from_annotation`.
- `SemanticDiagnostic`: estrutura leve com mensagem e span opcional, usada para reportar problemas.

## 2. Inicializacao

- `SemanticAnalyzer.analyze(module)` limpa diagnosticos anteriores, reseta o escopo e percorre `module.declarations`.
- A cada funcao ou variavel global, decide qual rotina de analise chamar.

## 3. Analise de declaracoes

- **Funcoes** (`_analyze_function`):
  - Abre um novo escopo com `symbols.push_scope`.
  - Define `current_return_type` a partir de `return_type` ou assume `vacuum` (void) quando ausente.
  - Insere parametros na tabela de simbolos, validando nomes duplicados. Cada parametro sem anotacao recebe `quodlibet` (tipo dinamico).
  - Analisa o corpo bloco por bloco, reutilizando `_analyze_statement`.
  - Fecha o escopo ao final.
- **Variaveis** (`_analyze_variable`):
  - Determina o tipo declarado (ou `quodlibet` se nao houver anotacao).
  - Compara com o tipo do inicializador quando presente (obtido via `_analyze_expression`).
  - Garante que nomes nao sejam redeclarados no mesmo escopo e que variaveis imutaveis nao recebam atribuicoes inconsistentes.

## 4. Analise de instrucoes (`_analyze_statement`)

- `VariableDeclaration`: reaproveita `_analyze_variable` para tratar escopos locais.
- `ExpressionStatement`: avalia a expressao para verificar tipos e efeitos colaterais.
- `ReturnStatement`: verifica compatibilidade entre o tipo esperado e o tipo retornado.
- `BlockStatement`: abre um escopo temporario para as declaracoes internas.
- `IfStatement`, `WhileStatement`, `ForStatement`: avaliam condicoes e corpos, introduzindo escopos quando necessario.
- `BreakStatement` e `ContinueStatement`: hoje nao verificam contexto de loop, mas o ponto de extensao esta pronto.

## 5. Analise de expressoes (`_analyze_expression`)

- Literais retornam tipos primitivos (`numerus`, `textus`, `booleanum`) ou `quodlibet` quando o valor nao e inferivel.
- Identificadores consultam a `SymbolTable`; ausencia gera diagnostico.
- Operadores binarios aplicam regras simples:
  - Operacoes aritmeticas exigem `numerus`.
  - Comparacoes retornam `booleanum`.
  - `??` e `?:` combinam tipos preservando ordem de avaliacao.
- Atribuicoes validam mutabilidade do alvo e compatibilidade entre tipos.
- Chamadas (`CallExpression`) e acesso a membros ainda sao tratados como `quodlibet`, preparando terreno para uma fase de resolucao mais avançada.

## 6. Reporte de erros

- Qualquer violacao adiciona um `SemanticDiagnostic` com mensagem descritiva e, quando disponivel, o `span` do no problematico.
- O metodo `_error` centraliza a criacao de diagnosticos, facilitando localizacao e futura internacionalizacao.

## 7. Saida

- `analyze` retorna a lista de diagnosticos, mas a tabela de simbolos e mantida no objeto (permite consultas em testes).
- Nenhuma excecao eh levantada para erros do usuario; apenas `CompilerError` seria usado em situacoes internas.

Com esta base, novas verificacoes (checar loops, tipos compostos, inferencia) podem ser adicionadas incrementalmente sem alterar a estrutura central da fase semantica.
