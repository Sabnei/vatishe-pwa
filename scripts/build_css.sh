#!/usr/bin/env bash
# Compila el CSS de Tailwind (tema VATISHE Core).
# Uso:  ./scripts/build_css.sh          -> compila una vez (minificado)
#       ./scripts/build_css.sh --watch  -> recompila al guardar
set -euo pipefail
cd "$(dirname "$0")/.."

if [[ "${1:-}" == "--watch" ]]; then
  ./bin/tailwindcss -i static/src/input.css -o static/css/vatishe.css --watch
else
  ./bin/tailwindcss -i static/src/input.css -o static/css/vatishe.css --minify
fi
