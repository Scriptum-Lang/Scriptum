# Releasing Scriptum 4.x

This guide documents the release process for the Scriptum toolchain.

## Pre-requisites

- Ensure `pyproject.toml` declares the target version (must remain within `4.x`).
- All tests (unit, integration, smoke) should be green locally.
- The Git repository should be clean (no uncommitted changes).

## Release Steps

1. **Update the changelog**  
   Document the new features, fixes, and any notable changes in `CHANGELOG.md`.

2. **Tag the release**  
   Replace `4.0.3` with the specific `4.x` version being released:
   ```bash
   git tag v4.x
   git push origin v4.x
   ```

3. **CI builds artifacts**  
   GitHub Actions (`.github/workflows/release.yml`) will automatically build:
   - Standalone binaries for Linux, macOS, and Windows.
   - Platform-specific archives (`tar.gz` for Unix, `.zip` for Windows).
   - Combined `SHA256SUMS`.
   The workflow also publishes a GitHub Release containing all artifacts.

4. **Smoke-test the published binaries**  
   Download the artifacts (binary or archive) for your platform and run:
   ```bash
   scripts/smoke_local.sh    # Linux/macOS
   scripts/smoke_local.ps1   # Windows PowerShell
   ```

   These scripts exercise `--version`, `--help`, `lex`, `parse`, and (when available) `sema`.

## v4.0.3 Checklist (Bytecode + LLVM C++)

In addition to the generic steps above, releasing **4.0.3** requires validating the new backends:

1. **Version bump**  
   - Set `project.version = "4.0.3"` in `pyproject.toml`.
   - Update the `[4.0.3]` section in `CHANGELOG.md` with the final date/notes.

2. **Backend sanity checks**  
   - Run the regular test suite: `python -m pytest`.
   - Exercise the new backends locally:
     ```bash
     scriptum run --backend=bytecode examples/hello.stm
     scriptum run --backend=llvm examples/hello.stm
     scriptum run --backend=llvm-cpp examples/hello.stm  # expect VM fallback when bindings estão ausentes
     ```
   - Compile the C++ backend when LLVM está instalado:
     ```bash
     python scripts/build_cpp_backend.py --skip-tests  # opcionalmente remova --skip-tests para rodar o GoogleTest
     ```
     The command ensures `cpp/llvm_codegen` compiles cleanly and produces `scriptum_codegen_llvm_cpp_py.*`. This is optional for CI (runners usually não possuem LLVM), but deve ser feito localmente antes de cortar a tag.

3. **Tag and push**  
   - `git tag v4.0.3 && git push origin v4.0.3`.

4. **Monitor the pipeline**  
   - GitHub Actions `Release` workflow compila as três plataformas usando PyInstaller.
   - Não é necessário alterar o pipeline: o novo bytecode backend é coberto por `python -m pytest`, e o backend C++ recai para a VM quando o módulo não existir.

5. **Post-release verification**  
   - Baixe os binários da release 4.0.3 e execute `scripts/smoke_local.[sh|ps1]`.
   - Para testar o backend C++ em uma máquina real com LLVM instalado, rode `python scripts/build_cpp_backend.py` e em seguida `scriptum run --backend=llvm-cpp examples/hello.stm`.

## Adjusting Installer Script URLs

Ensure the installer scripts reference the correct GitHub repository. They currently point to `Scriptum-Lang/Scriptum`; update them if the project ever migrates.

- `scripts/install.sh`
- `scripts/install.ps1`

Adjust the embedded `owner/repo` strings as needed so the installers fetch binaries from the right release.
