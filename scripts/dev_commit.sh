#!/usr/bin/env bash
# Convenience script for creating development commits during the Scriptum build.

set -euo pipefail

MESSAGE=${1:-"chore: development checkpoint"}

git add -A
git commit -m "${MESSAGE}"
