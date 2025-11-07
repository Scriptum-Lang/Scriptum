# Release checklist

Use estas etapas para preparar uma nova versao do Scriptum com artefatos funcionais em Windows, macOS e Linux.

1. **Atualizar versao**
   - Ajuste `src/scriptum/__init__.py`, `src/scriptum/driver.py` e `pyproject.toml`.
   - Atualize `README.md`, `docs/wiki` (especialmente `07_fluxo_compilador.md`) e `scripts/smoke_local.*` quando houver mudancas no CLI.
   - Acrescente uma secao correspondente em `CHANGELOG.md`.
   - Faca commit das mudancas e crie uma tag (`git tag vX.Y.Z`).

2. **Sincronizar dependencias**
   ```bash
   uv pip compile pyproject.toml -o requirements.txt
   uv sync --extra dev
   uv run pytest
   ```

3. **Gerar distribuicoes**
   ```bash
   uv build
   ls dist/
   ```

4. **Validar instalacao local**
   ```bash
   uv venv .release-check
   uv pip install --python .release-check/bin/python dist/scriptum-X.Y.Z-py3-none-any.whl          # Linux/macOS
   uv pip install --python .release-check/Scripts/python.exe dist/scriptum-X.Y.Z-py3-none-any.whl  # Windows

   # Linux/macOS
   .release-check/bin/scriptum --help
   .release-check/bin/scriptum dev lex examples/ok/loops_and_funcs.stm
   .release-check/bin/scriptum check examples/err/type_mismatch.stm --json
   .release-check/bin/scriptum -c "redde 42;"

   # Windows
   .release-check/Scripts/scriptum.exe --help
   .release-check/Scripts/scriptum.exe dev lex examples/ok/loops_and_funcs.stm
   .release-check/Scripts/scriptum.exe check examples/err/type_mismatch.stm --json
   .release-check/Scripts/scriptum.exe -c "redde 42;"
   ```

5. **Publicar release**
   - Crie uma release no GitHub anexando `dist/*.tar.gz` e `dist/*.whl` mais os hashes (`sha256sum dist/*`).
   - Assegure que o workflow `CI` executou com sucesso em `ubuntu`, `macos` e `windows`.
   - Opcional: publique no PyPI com `uv publish` (exige credenciais configuradas).

6. **Divulgar notas**
   - Copie os topicos de `CHANGELOG.md` para a descricao da release.
   - Informe que a release foi testada em Windows, macOS e Linux utilizando `uv` e `pipx`.
