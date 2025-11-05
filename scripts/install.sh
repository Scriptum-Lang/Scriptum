#!/usr/bin/env bash
set -euo pipefail

# Scriptum installer for Linux and macOS users.
# Downloads the latest release binary and places it on your PATH.

REPO="Scriptum-Lang/Scriptum"

detect_platform() {
  local os arch
  os="$(uname -s)"
  arch="$(uname -m)"

  case "$os" in
    Linux) os="linux" ;;
    Darwin) os="macos" ;;
    *)
      echo "Unsupported operating system: $os" >&2
      exit 1
      ;;
  esac

  case "$arch" in
    x86_64 | amd64) arch="x86_64" ;;
    arm64 | aarch64) arch="arm64" ;;
    *)
      echo "Unsupported CPU architecture: $arch" >&2
      exit 1
      ;;
  esac

  PLATFORM="$os"
  ARCH="$arch"
  SUFFIX="$os"
}

download_binary() {
  local tmp download_url version py_cmd
  tmp="$(mktemp -d)"
  TMP_DIR="$tmp"
  TMP_FILE="${tmp}/scriptum"
  local api_url="https://api.github.com/repos/${REPO}/releases/latest"

  if command -v python3 >/dev/null 2>&1; then
    py_cmd="python3"
  elif command -v python >/dev/null 2>&1; then
    py_cmd="python"
  else
    echo "Python is required to resolve the latest release asset." >&2
    exit 1
  fi

  download_url="$(REPO="$REPO" SUFFIX="$SUFFIX" "$py_cmd" - <<'PY'
import json
import os
import sys
import urllib.request

repo = os.environ["REPO"]
suffix = os.environ["SUFFIX"]
api_url = f"https://api.github.com/repos/{repo}/releases/latest"
req = urllib.request.Request(api_url, headers={"User-Agent": "scriptum-installer", "Accept": "application/vnd.github+json"})
try:
    with urllib.request.urlopen(req) as response:
        data = json.load(response)
except Exception as exc:
    sys.exit(f"Failed to query latest release: {exc}")

tag = data.get("tag_name", "")
assets = data.get("assets", [])
target_url = None
for asset in assets:
    name = asset.get("name", "")
    if not name.startswith("scriptum-"):
        continue
    if name.endswith(f"-{suffix}") or name.endswith(f"-{suffix}.exe"):
        target_url = asset.get("browser_download_url")
        break

if not target_url:
    sys.exit(f"Unable to find Scriptum asset for suffix '{suffix}' in release {tag or 'latest'}")

print(target_url)
PY
)"

  if [ -z "$download_url" ]; then
    exit 1
  fi

  echo "Downloading Scriptum from ${download_url}..."
  local temp_file="${TMP_FILE}.download"
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL -o "$temp_file" "$download_url"
  elif command -v wget >/dev/null 2>&1; then
    wget -qO "$temp_file" "$download_url"
  else
    echo "Neither curl nor wget is available; cannot download binary." >&2
    exit 1
  fi

  mv "$temp_file" "$TMP_FILE"
  chmod +x "$TMP_FILE"
}

install_binary() {
  local target_dir target_path
  target_dir="${HOME}/.local/bin"
  if [ -d "$target_dir" ]; then
    target_path="${target_dir}/scriptum"
    mv "$TMP_FILE" "$target_path"
    echo "Installed Scriptum to ${target_path}"

    if [[ ":${PATH}:" != *":${target_dir}:"* ]]; then
      echo "Warning: ${target_dir} is not on your PATH."
      echo "Add the following to your shell profile (e.g., ~/.bashrc):"
      echo "  export PATH=\"\$PATH:${target_dir}\""
    fi
  else
    target_path="${PWD}/scriptum"
    mv "$TMP_FILE" "$target_path"
    echo "Saved Scriptum binary to ${target_path}"
    echo "Consider moving it to /usr/local/bin with:"
    echo "  sudo mv ${target_path} /usr/local/bin/"
  fi
}

cleanup() {
  if [ -n "${TMP_DIR:-}" ] && [ -d "$TMP_DIR" ]; then
    rm -rf "$TMP_DIR"
  fi
}

main() {
  trap cleanup EXIT
  detect_platform
  download_binary
  install_binary
  echo "Scriptum installation complete."
}

main "$@"
