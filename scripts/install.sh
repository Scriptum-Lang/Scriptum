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
}

download_binary() {
  local asset url tmp
  asset="scriptum-${PLATFORM}-${ARCH}" # Adjust to match release asset names.
  url="https://github.com/${REPO}/releases/latest/download/${asset}"

  tmp="$(mktemp -d)"
  TMP_DIR="$tmp"
  TMP_FILE="${tmp}/scriptum"

  echo "Downloading Scriptum from ${url}..."
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL -o "$TMP_FILE" "$url"
  elif command -v wget >/dev/null 2>&1; then
    wget -qO "$TMP_FILE" "$url"
  else
    echo "Neither curl nor wget is available; cannot download binary." >&2
    exit 1
  fi

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
