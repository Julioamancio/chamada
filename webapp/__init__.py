from __future__ import annotations

import os
from pathlib import Path
from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import threading
import time
import sqlite3
from shutil import copy2

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"


def create_app() -> Flask:
    # Choose a durable, user‑writable instance directory on Windows
    # Priority: env CHAMADA_DATA_DIR > %LOCALAPPDATA%\ChamadaEscolar > default
    default_data_dir = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "ChamadaEscolar"
    data_dir = Path(os.environ.get("CHAMADA_DATA_DIR", str(default_data_dir)))
    data_dir.mkdir(parents=True, exist_ok=True)
    app = Flask(__name__, instance_path=str(data_dir), instance_relative_config=False)

    # Config
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-secret-change-me"),
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "DATABASE_URL",
            "sqlite:///" + (Path(app.instance_path) / "app.db").as_posix(),
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass

    # Attempt automatic migration of legado instance/ DB (projeto raiz)
    def _maybe_migrate_legacy_db():
        try:
            dest = Path(app.instance_path) / "app.db"
            if dest.exists() and dest.stat().st_size > 0:
                return  # already have a DB
            candidates = []
            # projeto atual em desenvolvimento
            candidates.append(Path.cwd() / "instance" / "app.db")
            # raiz do pacote (../instance/app.db)
            candidates.append(Path(__file__).resolve().parent.parent / "instance" / "app.db")
            for src in candidates:
                if src.exists() and src.stat().st_size > 0:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    try:
                        # tente backup online do SQLite
                        import sqlite3

                        s = sqlite3.connect(src)
                        d = sqlite3.connect(dest)
                        with d:
                            s.backup(d)
                        s.close()
                        d.close()
                    except Exception:
                        from shutil import copy2

                        copy2(src, dest)
                    print(f"[migrate] Copiado DB legado de {src} para {dest}")
                    return
        except Exception:
            # nunca quebre o app por conta da migração
            pass

    _maybe_migrate_legacy_db()

    # Ensure a default logo is persisted on first run
    def _ensure_default_logo():
        """Ensure an initial branding logo is present.

        Priority:
        1) If user already uploaded any "logo.*" in instance/branding → keep it.
        2) Try to download the official Colégio Santo Antônio logo from the URL provided.
        3) Fallback to the embedded logo_default.svg bundled with the app.
        """
        try:
            from shutil import copy2 as _copy2
            from urllib.request import urlopen
            import ssl

            folder = Path(app.instance_path) / "branding"
            folder.mkdir(parents=True, exist_ok=True)
            # If there's already any logo file, keep it
            if any(folder.glob("logo.*")):
                return

            # Attempt to download the official logo once
            url = (
                "https://www.colegiosantoantonio.com.br/wp-content/uploads/2019/06/"
                "nova-logo-colegio-santo-antonio-logotipo.png"
            )
            try:
                # Some hosts may require an unverified context in constrained envs
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                with urlopen(url, timeout=6, context=ctx) as resp:
                    data = resp.read()
                    out = folder / "logo.png"
                    out.write_bytes(data)
                    return
            except Exception:
                # Fallback to embedded asset
                pass

            default_src = Path(__file__).resolve().parent / "static" / "logo_default.svg"
            if default_src.exists():
                _copy2(default_src, folder / "logo.svg")
        except Exception:
            # Never crash the app due to branding setup
            pass

    _ensure_default_logo()

    # Init extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Models
    from . import models  # noqa: F401

    # Blueprints
    from .auth import bp as auth_bp
    from .admin import bp as admin_bp
    from .teacher import bp as teacher_bp
    from .api import bp as api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(teacher_bp, url_prefix="/teacher")
    app.register_blueprint(api_bp, url_prefix="/api")

    # Branding context
    @app.context_processor
    def inject_branding():
        from pathlib import Path
        from flask import url_for
        folder = Path(app.instance_path) / "branding"
        # pick first matching logo
        logo = None
        for p in [*folder.glob("logo.*")]:
            logo = p.name
            break
        url = url_for("admin.brand_logo") if logo else None
        return {"brand_logo_url": url}

    # Idioma atual + função de tradução simples
    TRANSLATIONS = {
        "en": {
            "Chamada": "Attendance",
            "Minhas turmas": "My classes",
            "Admin": "Admin",
            "Turmas (Admin)": "Classes (Admin)",
            "Etapas": "Stages",
            "Atividades": "Activities",
            "Configurações": "Settings",
            "Configuracoes": "Settings",
            "Sair": "Sign out",
            "Voltar": "Back",
            "Chamadas": "Calls",
            "Data": "Date",
            "Presentes": "Present",
            "Ausentes": "Absent",
            "Etapa": "Stage",
            "Todas as aulas": "All classes",
            "Ver": "View",
            "Alunos": "Students",
            "Chamada": "Attendance",
            "Salvar chamada": "Save attendance",
            "Todos P": "All Present",
            "Todos A": "All Absent",
            "Calendário": "Calendar",
            "Idioma": "Language",
            "Português": "Portuguese",
            "English": "English",
            "中文": "Chinese",
            "Tema (claro/escuro)": "Theme (light/dark)",
            "Claro": "Light",
            "Escuro": "Dark",
            "Preferência salva neste navegador.": "Preference saved in this browser.",
            "Backup das minhas turmas": "Backup my classes",
            "Baixar backup (JSON)": "Download backup (JSON)",
            "Importar": "Import",
        },
        "zh": {
            "Chamada": "考勤",
            "Minhas turmas": "我的班级",
            "Admin": "管理员",
            "Turmas (Admin)": "班级（管理员）",
            "Etapas": "阶段",
            "Atividades": "活动",
            "Configurações": "设置",
            "Configuracoes": "设置",
            "Sair": "退出",
            "Voltar": "返回",
            "Chamadas": "点名记录",
            "Data": "日期",
            "Presentes": "到",
            "Ausentes": "缺",
            "Etapa": "阶段",
            "Todas as aulas": "全部课程",
            "Ver": "查看",
            "Alunos": "学生",
            "Chamada": "考勤",
            "Salvar chamada": "保存考勤",
            "Todos P": "全部到",
            "Todos A": "全部缺",
            "Calendário": "日历",
            "Idioma": "语言",
            "Português": "葡萄牙语",
            "English": "英语",
            "中文": "中文",
            "Tema (claro/escuro)": "主题（亮/暗）",
            "Claro": "亮色",
            "Escuro": "暗色",
            "Preferência salva neste navegador.": "偏好已保存在此浏览器。",
            "Backup das minhas turmas": "备份我的班级",
            "Baixar backup (JSON)": "下载备份（JSON）",
            "Importar": "导入",
        },
    }

    # Complementary translation maps (fallback for keys not present above)
    SUPP_EN = {
        "Usuários": "Users",
        "Área do Professor": "Teacher Area",
        "Salvar": "Save",
        "Salvar perfil": "Save profile",
        "Importar alunos": "Import students",
        "Atividades criadas": "Created activities",
        "Etapa (opcional)": "Stage (optional)",
        "Baixar DOCX da Turma": "Download class DOCX",
        "Nome da turma": "Class name",
        "Criar turma": "Create class",
        "Criar": "Create",
        "Nome": "Name",
        "E-mail": "Email",
        "Senha": "Password",
        "Perfil": "Role",
        "Professor": "Teacher",
        "Professor atual": "Current teacher",
        "Vincular a": "Assign to",
        "Vincular": "Assign",
        "Turmas": "Classes",
        "Turmas existentes": "Existing classes",
        "Turma": "Class",
        "Excluir turma": "Delete class",
        "Excluir turma e todos os dados?": "Delete class and all data?",
        "Excluir turma e registros?": "Delete class and records?",
        "Excluir": "Delete",
        "Entrar": "Sign in",
        "Mostrar/ocultar senha": "Show/hide password",
        "Feito por Júlio Amâncio": "Made by Júlio Amâncio",
        "Logo (PNG/JPG/SVG)": "Logo (PNG/JPG/SVG)",
        "Enviar": "Upload",
        "O logo será exibido no canto superior esquerdo.": "The logo will appear at the top-left.",
        "Logo da aplicação": "Application logo",
        "Arquivo (PNG/JPG/SVG)": "File (PNG/JPG/SVG)",
        "Backup do banco de dados": "Database backup",
        "Baixe uma cópia do arquivo SQLite atual.": "Download a copy of the current SQLite file.",
        "Baixar backup (app.db)": "Download backup (app.db)",
        "Importar banco (.db)": "Import database (.db)",
        "Importar e substituir": "Import and replace",
        "Alterar senha do administrador": "Change admin password",
        "Nova senha": "New password",
        "Confirmação da senha": "Confirm password",
        "Atualizar senha": "Update password",
        "Nenhuma turma cadastrada.": "No classes found.",
        "Nenhuma turma ainda. Crie a primeira acima.": "No classes yet. Create the first above.",
        "Etapas Globais": "Global stages",
        "Etapas globais cadastradas": "Registered global stages",
        "Etapas cadastradas": "Registered stages",
        "Excluir etapa?": "Delete stage?",
        "Excluir etapa global?": "Delete global stage?",
    }

    SUPP_ZH = {
        "Usuários": "用户",
        "Área do Professor": "教师区",
        "Salvar": "保存",
        "Salvar perfil": "保存资料",
        "Importar alunos": "导入学生",
        "Atividades criadas": "已创建的活动",
        "Etapa (opcional)": "阶段（可选）",
        "Baixar DOCX da Turma": "下载班级 DOCX",
        "Nome da turma": "班级名称",
        "Criar turma": "创建班级",
        "Criar": "创建",
        "Nome": "姓名",
        "E-mail": "邮箱",
        "Senha": "密码",
        "Perfil": "角色",
        "Professor": "教师",
        "Professor atual": "当前教师",
        "Vincular a": "关联到",
        "Vincular": "关联",
        "Turmas": "班级",
        "Turmas existentes": "已有班级",
        "Turma": "班级",
        "Excluir turma": "删除班级",
        "Excluir turma e todos os dados?": "删除班级及其所有数据？",
        "Excluir turma e registros?": "删除班级和记录？",
        "Excluir": "删除",
        "Entrar": "登录",
        "Mostrar/ocultar senha": "显示/隐藏密码",
        "Feito por Júlio Amâncio": "由 Júlio Amâncio 创建",
        "Logo (PNG/JPG/SVG)": "Logo (PNG/JPG/SVG)",
        "Enviar": "上传",
        "O logo será exibido no canto superior esquerdo.": "Logo 显示在左上角",
        "Logo da aplicação": "应用 Logo",
        "Arquivo (PNG/JPG/SVG)": "文件 (PNG/JPG/SVG)",
        "Backup do banco de dados": "数据库备份",
        "Baixe uma cópia do arquivo SQLite atual.": "下载当前 SQLite 文件副本",
        "Baixar backup (app.db)": "下载备份 (app.db)",
        "Importar banco (.db)": "导入数据库 (.db)",
        "Importar e substituir": "导入并替换",
        "Alterar senha do administrador": "修改管理员密码",
        "Nova senha": "新密码",
        "Confirmação da senha": "确认密码",
        "Atualizar senha": "更新密码",
        "Nenhuma turma cadastrada.": "暂无班级",
        "Nenhuma turma ainda. Crie a primeira acima.": "还没有班级，请在上方创建第一个",
        "Etapas Globais": "全局阶段",
        "Etapas globais cadastradas": "已注册的全局阶段",
        "Etapas cadastradas": "已注册的阶段",
        "Excluir etapa?": "删除阶段？",
        "Excluir etapa global?": "删除全局阶段？",
    }

    @app.context_processor
    def inject_lang():
        try:
            lang = session.get("lang", "pt-br")
        except Exception:
            lang = "pt-br"

        def _(text: str) -> str:
            if lang == "pt-br":
                return text
            base = TRANSLATIONS.get(lang, {})
            if text in base:
                return base[text]
            supp = SUPP_EN if lang == "en" else (SUPP_ZH if lang == "zh" else {})
            return supp.get(text, text)

        # Labels das opções de idioma
        if lang == "pt-br":
            langs = [("pt-br", "Português"), ("en", "Inglês"), ("zh", "中文")]
        elif lang == "en":
            langs = [("pt-br", "Portuguese"), ("en", "English"), ("zh", "中文")]
        else:  # zh → manter nomes PT/EN para facilitar troca
            langs = [("pt-br", "Português"), ("en", "English"), ("zh", "中文")]

        return {
            "current_lang": lang,
            "supported_langs": langs,
            "_": _,
        }

    # Auto-init DB on startup (and ensure a default admin exists)
    with app.app_context():
        from .models import User  # noqa: WPS433
        from werkzeug.security import generate_password_hash  # noqa: WPS433

        db.create_all()
        if not User.query.first():
            admin = User(
                email="admin@admin.com",
                name="Admin",
                role="admin",
                password_hash=generate_password_hash("admin123"),
            )
            db.session.add(admin)
            db.session.commit()

    # CLI: init-db
    @app.cli.command("init-db")
    def init_db_command():
        from .models import User
        from werkzeug.security import generate_password_hash

        db.create_all()
        if not User.query.first():
            admin = User(
                email="admin@admin.com",
                name="Admin",
                role="admin",
                password_hash=generate_password_hash("admin123"),
            )
            db.session.add(admin)
            db.session.commit()
            print("Initialized DB and created default admin: admin@admin.com / admin123")
        else:
            print("DB already initialized.")

    # Activity tracking for backup scheduler
    app._last_activity_ts = time.time()

    @app.before_request
    def _touch_activity():
        app._last_activity_ts = time.time()

    # Periodic backup thread (every 30 minutes when used)
    def _backup_worker():
        interval = int(os.environ.get("BACKUP_INTERVAL_MIN", "30")) * 60
        while True:
            try:
                time.sleep(60)  # check every minute
                # Only backup if app used in the last interval
                if time.time() - getattr(app, "_last_activity_ts", 0) > interval:
                    continue
                inst = Path(app.instance_path)
                db_path = inst / "app.db"
                if not db_path.exists():
                    continue
                backups = inst / "backups"
                backups.mkdir(parents=True, exist_ok=True)
                ts = time.strftime("%Y%m%d-%H%M")
                out = backups / f"app-{ts}.db"
                # Use SQLite online backup to avoid partial copies
                try:
                    src = sqlite3.connect(db_path)
                    dst = sqlite3.connect(out)
                    with dst:
                        src.backup(dst)
                    src.close()
                    dst.close()
                except Exception:
                    # fallback to file copy
                    try:
                        copy2(db_path, out)
                    except Exception:
                        pass
            except Exception:
                # never crash the app due to backup thread
                pass

    t = threading.Thread(target=_backup_worker, daemon=True)
    t.start()

    # Simple index redirect
    @app.route("/")
    def index():
        from flask import redirect, url_for
        return redirect(url_for("teacher.dashboard"))

    return app
