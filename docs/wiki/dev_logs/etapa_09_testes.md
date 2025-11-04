# Etapa 09 — Testes e validação geral

## Suite executada
- `tests/test_parser_smoke.py`: valida parsing básico em exemplos `variaveis.stm`, `condicionais.stm`, `classes.stm`, `sistema_bancario.stm`, assegurando presença de declarações e estruturas principais.
- `tests/test_semantics.py`: verifica que exemplos válidos não produzem diagnósticos e que `tipo_incompativel.stm` emite erro de incompatibilidade de tipos.

## Resultados
- `pytest -q` ? `20 passed` (inclui smoke e semântica).
- Casos negativos reportam `Type mismatch` com `Span` associado.

## Como replicar
```bash
pytest -q
```
