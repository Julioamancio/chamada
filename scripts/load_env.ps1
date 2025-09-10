# Carrega variáveis do arquivo chaves_gerais ou .env (o que existir)
Param(
  [string]$Path1 = "chaves_gerais",
  [string]$Path2 = ".env"
)

function Load-EnvFile([string]$file) {
  if (-not (Test-Path $file)) { return $false }
  Get-Content $file | ForEach-Object {
    $line = $_.Trim()
    if (-not $line -or $line.StartsWith('#')) { return }
    $kv = $line -split '=', 2
    if ($kv.Count -eq 2) {
      $key = $kv[0].Trim()
      $val = $kv[1].Trim()
      [Environment]::SetEnvironmentVariable($key, $val)
    }
  }
  Write-Host "Carregado: $file"
  return $true
}

if (-not (Load-EnvFile $Path1)) {
  if (-not (Load-EnvFile $Path2)) {
    Write-Error "Nenhum arquivo de variáveis encontrado (chaves_gerais ou .env)."
    exit 1
  }
}
