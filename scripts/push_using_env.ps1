Param(
  [string]$Branch = $env:GIT_BRANCH
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
& "$ScriptDir\load_env.ps1"

if (-not $Branch) { $Branch = "main" }
$remote = $env:GIT_REMOTE_ALIAS
if (-not $remote) { $remote = "origin" }

if ($env:SSH_KEY_PRIV -and (Test-Path $env:SSH_KEY_PRIV)) {
  Write-Host "Fazendo push via SSH com chave: $($env:SSH_KEY_PRIV)"
  $env:GIT_SSH_COMMAND = "ssh -i `"$($env:SSH_KEY_PRIV)`" -o StrictHostKeyChecking=no"
  git push -u $remote $Branch
} elseif ($env:GITHUB_PAT) {
  $repo = $env:GITHUB_REPO
  if (-not $repo) { $repo = "Julioamancio/chamada" }
  Write-Host "Fazendo push via HTTPS com PAT para $repo"
  git push -u "https://x-access-token:$($env:GITHUB_PAT)@github.com/$repo.git" $Branch
} else {
  Write-Error "Nenhuma credencial encontrada. Informe SSH_KEY_PRIV ou GITHUB_PAT em chaves_gerais/.env"
  exit 1
}
