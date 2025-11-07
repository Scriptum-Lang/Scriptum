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
   python -m venv .release-check
   .release-check/Scripts/activate       # Windows
   source .release-check/bin/activate    # macOS/Linux
   pip install dist/scriptum-X.Y.Z-py3-none-any.whl
   scriptum --help
   scriptum dev lex examples/ok/loops_and_funcs.stm
   scriptum check examples/err/type_mismatch.stm --json
   scriptum -c "redde 42;"
   ```

5. **Publicar release**
   - Crie uma release no GitHub anexando `dist/*.tar.gz` e `dist/*.whl` mais os hashes (`sha256sum dist/*`).
   - Assegure que o workflow `CI` executou com sucesso em `ubuntu`, `macos` e `windows`.
   - Opcional: publique no PyPI com `uv publish` (exige credenciais configuradas).

6. **Divulgar notas**
   - Copie os topicos de `CHANGELOG.md` para a descricao da release.
   - Informe que a release foi testada em Windows, macOS e Linux utilizando `uv` e `pipx`.
