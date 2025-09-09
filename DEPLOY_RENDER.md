# Deploy no Render.com

Este projeto já está preparado para o Render com o arquivo `render.yaml` e execução via Gunicorn.
O arquivo `runtime.txt` fixa o Python em 3.11 no ambiente do Render.

## Opção A — Blueprint (recomendado)

1) Faça push do repositório para GitHub/GitLab.
2) No Render, escolha: New → Blueprint → selecione o repositório.
3) O serviço será criado com:
   - Build: `pip install -r requirements.txt`
   - Start: `gunicorn -w 2 -k gthread -b 0.0.0.0:$PORT app:app`
4) Variáveis de ambiente previstas no blueprint:
   - `SECRET_KEY` (gerada automaticamente)
   - `CHAMADA_DATA_DIR=/opt/render/project/src/instance` (ephemeral)
   - `BACKUP_INTERVAL_MIN=30`
5) Para persistência do banco SQLite entre deploys, adicione um Disk ao serviço e mude `CHAMADA_DATA_DIR` para `/data`:
   - Name: `data`, Mount path: `/data`, Size: 1GB+ (Settings → Disks).

## Opção B — Serviço manual

1) New → Web Service (Environment: Python).
2) Build Command: `pip install -r requirements.txt`
3) Start Command: `gunicorn -w 2 -k gthread -b 0.0.0.0:$PORT app:app`
4) Defina env vars:
   - `SECRET_KEY` (valor seguro)
   - `CHAMADA_DATA_DIR=/opt/render/project/src/instance` (ou `/data` se usar Disk)
   - `BACKUP_INTERVAL_MIN=30` (opcional)
5) (Opcional) Adicione um Disk montado em `/data` para persistência.

Observação: O app cria/usa `instance/app.db` (SQLite) por padrão. Em produção, prefira apontar `CHAMADA_DATA_DIR` para um volume persistente (ex.: `/data`).
