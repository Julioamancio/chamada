# Deploy no Render.com — Guia Completo

Este projeto já está preparado para deploy no Render usando `render.yaml` com ambiente Python e Gunicorn. Siga um dos métodos abaixo.

## Pré-requisitos

- Repositório no GitHub/GitLab com este código
- Conta no Render (gratuita ou paga)

## Método A — Blueprint (recomendado)

1. Faça push do repositório para GitHub/GitLab.
2. No Render: New → Blueprint → selecione o repositório.
3. Confirme as configurações do serviço criadas a partir do `render.yaml`:
   - Build: `pip install -r requirements.txt`
   - Start: `gunicorn -w 2 -k gthread -b 0.0.0.0:$PORT app:app`
   - Env Vars:
     - `SECRET_KEY` (gerada automaticamente)
     - `CHAMADA_DATA_DIR=/opt/render/project/src/instance` (padrão)
     - `BACKUP_INTERVAL_MIN=30` (opcional)
4. (Opcional, recomendado) Persistência do SQLite entre deploys:
   - Em Settings → Disks, adicione um Disk (ex.: 1GB) montado em `/data`.
   - Altere `CHAMADA_DATA_DIR` para `/data` no serviço.

## Método B — Serviço manual

1. New → Web Service → Environment: Python.
2. Build Command: `pip install -r requirements.txt`
3. Start Command: `gunicorn -w 2 -k gthread -b 0.0.0.0:$PORT app:app`
4. Defina as variáveis de ambiente:
   - `SECRET_KEY` (valor seguro)
   - `CHAMADA_DATA_DIR=/opt/render/project/src/instance` (ou `/data` se usar Disk)
   - `BACKUP_INTERVAL_MIN=30` (opcional)
5. (Opcional) Adicione um Disk em `/data` para persistência.

## Notas importantes

- O aplicativo expõe `app:app` a partir do módulo `app.py`, compatível com Gunicorn.
- `runtime.txt` fixa Python 3.11 no Render (`python-3.11.9`).
- Se for usar banco externo (ex.: Postgres), configure `DATABASE_URL` e ignore o SQLite.
- Por padrão, o app cria `instance/app.db`. Em produção, use um caminho persistente (`/data`).

## Teste local antes do deploy

1. `pip install -r requirements.txt`
2. `flask --app app.py init-db`
3. `python app.py` e acesse http://localhost:5000

Admin padrão: `admin@admin.com` / `admin123`

