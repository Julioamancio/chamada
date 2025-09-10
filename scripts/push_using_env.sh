#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 1) Carrega variáveis
"$SCRIPT_DIR/load_env.sh"

REMOTE_ALIAS="${GIT_REMOTE_ALIAS:-origin}"
BRANCH="${GIT_BRANCH:-main}"

# 2) Decide método: SSH > HTTPS com PAT
if [[ -n "${SSH_KEY_PRIV:-}" && -f "${SSH_KEY_PRIV/#~/$HOME}" ]]; then
  KEY_PATH="${SSH_KEY_PRIV/#~/$HOME}"
  echo "Fazendo push via SSH com chave: $KEY_PATH"
  GIT_SSH_COMMAND="ssh -i $KEY_PATH -o StrictHostKeyChecking=no" git push -u "$REMOTE_ALIAS" "$BRANCH"
elif [[ -n "${GITHUB_PAT:-}" ]]; then
  REPO_SLUG="${GITHUB_REPO:-Julioamancio/chamada}"
  echo "Fazendo push via HTTPS com PAT (uma vez) para $REPO_SLUG"
  git push -u "https://x-access-token:${GITHUB_PAT}@github.com/${REPO_SLUG}.git" "$BRANCH"
else
  echo "Nenhuma credencial encontrada. Informe SSH_KEY_PRIV ou GITHUB_PAT em chaves_gerais/.env" >&2
  exit 1
fi
