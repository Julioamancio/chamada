from __future__ import annotations

import os
from pathlib import Path
from flask import Flask
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
