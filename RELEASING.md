# Releasing Scriptum 0.3.x

This guide documents the release process for the Scriptum toolchain.

## Pre-requisites

- Ensure `pyproject.toml` declares the target version (must remain within `0.3.x`).
- All tests (unit, integration, smoke) should be green locally.
- The Git repository should be clean (no uncommitted changes).

## Release Steps

1. **Update the changelog**  
   Document the new features, fixes, and any notable changes in `CHANGELOG.md`.

2. **Tag the release**  
   Replace `0.3.1` with the specific `0.3.x` version being released:
   ```bash
   git tag v0.3.x
   git push origin v0.3.x
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

## Adjusting Installer Script URLs

Ensure the installer scripts reference the correct GitHub repository. They currently point to `Scriptum-Lang/Scriptum`; update them if the project ever migrates.

- `scripts/install.sh`
- `scripts/install.ps1`

Adjust the embedded `owner/repo` strings as needed so the installers fetch binaries from the right release.
