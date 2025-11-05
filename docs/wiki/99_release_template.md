# Release checklist

Use estas etapas para preparar uma nova versão do Scriptum com artefatos funcionais em Windows, macOS e Linux.

1. **Atualizar versão**
   - Ajuste `src/scriptum/__init__.py` e `pyproject.toml` com a nova versão.
   - Acrescente uma seção correspondente em `CHANGELOG.md`.
   - Faça commit das mudanças e crie uma tag (`git tag vX.Y.Z`).

2. **Sincronizar dependências**
   ```bash
   uv pip compile pyproject.toml -o requirements.txt
   uv sync --extra dev
   uv run pytest
   ```

3. **Gerar distribuições**
   ```bash
   uv build
   ls dist/
   ```

4. **Validar instalação local**
   ```bash
   python -m venv .release-check
   .release-check/Scripts/activate       # Windows
   source .release-check/bin/activate    # macOS/Linux
   pip install dist/scriptum-X.Y.Z-py3-none-any.whl
   scriptum --help
   python -m scriptum lex examples/ok/loops_and_funcs.stm
   ```

5. **Publicar release**
   - Crie uma release no GitHub anexando `dist/*.tar.gz` e `dist/*.whl` mais os hashes (`sha256sum dist/*`).
   - Assegure que o workflow `CI` executou com sucesso em `ubuntu`, `macos` e `windows`.
   - Opcional: publique no PyPI com `uv publish` (exige credenciais configuradas).

6. **Divulgar notas**
   - Copie os tópicos de `CHANGELOG.md` para a descrição da release.
   - Informe que a release foi testada em Windows, macOS e Linux utilizando `uv` e `pipx`.
