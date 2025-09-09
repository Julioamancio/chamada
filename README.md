# Chamada (Flask) — Web Service moderno

Aplicação web com Flask para administrar presenças, com perfis de administrador e professor, e importação de alunos via Excel (coluna A).

## Requisitos

- Python 3.10+
- Dependências: ver `requirements.txt`

## Instalação rápida

1) Criar e ativar venv (opcional, recomendado)
2) Instalar deps: `pip install -r requirements.txt`
3) Inicializar DB e admin: `flask --app app.py init-db`
4) Rodar: `python app.py` (acessa em http://localhost:5000)

Usuário admin padrão após init-db:
- email: `admin@example.com`
- senha: `admin123`

## Funcionalidades

- Admin: gerencia usuários (admin/professor)
- Professor: cria turmas, adiciona/remove alunos
- Chamada do dia: marca presentes/ausentes e salva
- Importar alunos via Excel `.xlsx` (nomes na coluna A)
- Exportar presenças em CSV
- API JSON: CRUD de turmas/alunos e presença
 - Calendário: gerar datas por período e dia(s) da semana, excluindo feriados nacionais (Carnaval, Sexta-feira Santa, Corpus Christi e feriados fixos)

## Estrutura

- `app.py`: entrypoint Flask (factory `create_app`).
- `webapp/__init__.py`: cria app, registra blueprints e CLI `init-db`.
- `webapp/models.py`: SQLAlchemy (User, Classroom, Student, Session, AttendanceEntry).
- `webapp/auth.py`: login/logout com Flask-Login.
- `webapp/admin.py`: área administrativa (criar/excluir usuários).
- `webapp/teacher.py`: área do professor (turmas, alunos, chamada, import, export).
- `webapp/excel.py`: leitura de Excel (openpyxl) da coluna A.
- `webapp/templates/…`: HTML com Bootstrap via CDN.
- `webapp/api.py`: endpoints REST JSON.

## Observações

- Banco SQLite em `instance/app.db` (criado automaticamente).
- Para produção, configure `SECRET_KEY` e `DATABASE_URL` via variável de ambiente.

## API JSON (exemplos)

Autenticação por sessão (faça login pelo navegador ou envie cookie).

- Listar turmas:
  - `GET /api/classes`
- Criar turma:
  - `POST /api/classes` body: `{ "name": "2º ano A" }`
- Renomear turma:
  - `PATCH /api/classes/<id>` body: `{ "name": "novo nome" }`
- Excluir turma:
  - `DELETE /api/classes/<id>`
- Listar alunos:
  - `GET /api/classes/<id>/students`
- Adicionar alunos (um ou vários):
  - `POST /api/classes/<id>/students` body: `{ "name": "João" }` ou `{ "names": ["Ana", "Carlos"] }`
- Renomear aluno:
  - `PATCH /api/students/<id>` body: `{ "name": "Novo Nome" }`
- Excluir aluno:
  - `DELETE /api/students/<id>`
- Obter presença do dia (ou data):
  - `GET /api/classes/<id>/attendance?date=YYYY-MM-DD`
- Gravar presença:
  - `PUT /api/classes/<id>/attendance` body: `{ "date": "YYYY-MM-DD", "present_ids": [1,2,3] }`
Windows: Executável e backup automático

- Gerar executável (one-folder):
  1) Instale Python 3.11+ e Git (se necessário)
  2) Abra o Prompt de Comando na pasta do projeto
  3) Rode: `scripts\build_windows.bat`
  4) Inicie: `dist\ChamadaEscolar\ChamadaEscolar.exe` (abre o servidor local em 127.0.0.1:5000)

- Backup automático (a cada 30 minutos quando usado):
  - O app faz cópias do banco `instance\app.db` em `instance\backups\app-YYYYMMDD-HHMM.db`.
  - Ajuste o intervalo com `BACKUP_INTERVAL_MIN` (variável de ambiente).

