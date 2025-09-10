#!/usr/bin/env bash
set -euo pipefail

# Carrega variáveis de chaves_gerais ou .env (o que existir)
ENV_FILE=""
if [[ -f "chaves_gerais" ]]; then
  ENV_FILE="chaves_gerais"
elif [[ -f ".env" ]]; then
  ENV_FILE=".env"
else
  echo "Nenhum arquivo de variáveis encontrado (chaves_gerais ou .env)." >&2
  exit 1
fi

# shellcheck disable=SC2046
export $(grep -vE '^#|^$' "$ENV_FILE" | sed -E 's/\r$//' | xargs -I{} sh -c 'k="${1%%=*}"; v="${1#*=}"; printf %s="%s" "$k" "$v"' _ {}) >/dev/null 2>&1 || true

echo "Carregado: $ENV_FILE"
