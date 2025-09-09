from __future__ import annotations

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user

from . import db
from .models import User, Classroom

bp = Blueprint("admin", __name__, template_folder="templates")


def admin_required(func):
    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "admin":
            flash("Acesso restrito ao administrador.", "warning")
            return redirect(url_for("auth.login"))
        return func(*args, **kwargs)

    return wrapper


@bp.route("/")
@login_required
@admin_required
def dashboard():
    users = User.query.order_by(User.role.desc(), User.name).all()
    return render_template("admin/users_utf8.html", users=users)


@bp.route("/classes")
@login_required
@admin_required
def classes():
    classes = Classroom.query.order_by(Classroom.name).all()
    teachers = User.query.filter_by(role="teacher").order_by(User.name).all()
    return render_template("admin/classes.html", classes=classes, teachers=teachers)


@bp.route("/classes/create", methods=["POST"])
@login_required
@admin_required
def create_class_admin():
    name = (request.form.get("name") or "").strip()
    owner_id = request.form.get("owner_id", type=int)
    if not name or not owner_id:
        flash("Informe nome e professor.", "warning")
        return redirect(url_for("admin.classes"))
    teacher = User.query.get(owner_id)
    if not teacher or teacher.role != "teacher":
        flash("Selecione um professor válido.", "danger")
        return redirect(url_for("admin.classes"))
    c = Classroom(name=name, owner_id=owner_id)
    db.session.add(c)
    db.session.commit()
    flash("Turma criada e vinculada ao professor.", "success")
    return redirect(url_for("admin.classes"))


@bp.route("/classes/<int:class_id>/reassign", methods=["POST"])
@login_required
@admin_required
def reassign_class(class_id: int):
    c = Classroom.query.get_or_404(class_id)
    owner_id = request.form.get("owner_id", type=int)
    teacher = User.query.get(owner_id)
    if not teacher or teacher.role != "teacher":
        flash("Selecione um professor válido.", "danger")
        return redirect(url_for("admin.classes"))
    c.owner_id = owner_id
    db.session.commit()
    flash("Professor vinculado à turma.", "success")
    return redirect(url_for("admin.classes"))


@bp.route("/classes/<int:class_id>/rename", methods=["POST"])
@login_required
@admin_required
def rename_class_admin(class_id: int):
    c = Classroom.query.get_or_404(class_id)
    new_name = (request.form.get("name") or "").strip()
    if not new_name:
        flash("Informe o novo nome da turma.", "warning")
        return redirect(url_for("admin.classes"))
    c.name = new_name
    db.session.commit()
    flash("Turma renomeada.", "success")
    return redirect(url_for("admin.classes"))


@bp.route("/classes/<int:class_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_class_admin(class_id: int):
    c = Classroom.query.get_or_404(class_id)
    db.session.delete(c)
    db.session.commit()
    flash("Turma excluída.", "success")
    return redirect(url_for("admin.classes"))


@bp.route("/users/create", methods=["POST"])
@login_required
@admin_required
def create_user():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    role = request.form.get("role", "teacher")
    if not name or not email or not password:
        flash("Preencha nome, e-mail e senha.", "warning")
        return redirect(url_for("admin.dashboard"))
    if User.query.filter_by(email=email).first():
        flash("E-mail já existe.", "danger")
        return redirect(url_for("admin.dashboard"))
    u = User(name=name, email=email, role=role)
    u.set_password(password)
    db.session.add(u)
    db.session.commit()
    flash("Usuário criado.", "success")
    return redirect(url_for("admin.dashboard"))


@bp.route("/users/<int:user_id>/edit", methods=["POST"])
@login_required
@admin_required
def edit_user(user_id: int):
    u = User.query.get_or_404(user_id)
    name = (request.form.get("name") or "").strip()
    email = (request.form.get("email") or "").strip().lower()
    role = request.form.get("role") or u.role
    password = (request.form.get("password") or "").strip()
    if not name or not email:
        flash("Informe nome e e-mail.", "warning")
        return redirect(url_for("admin.dashboard"))
    existing = User.query.filter(User.email == email, User.id != u.id).first()
    if existing:
        flash("E-mail já está em uso.", "danger")
        return redirect(url_for("admin.dashboard"))
    u.name = name
    u.email = email
    u.role = role
    if password:
        u.set_password(password)
    db.session.commit()
    flash("Usuário atualizado.", "success")
    return redirect(url_for("admin.dashboard"))

@bp.route("/users/<int:user_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_user(user_id: int):
    if current_user.id == user_id:
        flash("Você não pode excluir a si mesmo.", "warning")
        return redirect(url_for("admin.dashboard"))
    u = User.query.get_or_404(user_id)
    db.session.delete(u)
    db.session.commit()
    flash("Usuário excluído.", "success")
    return redirect(url_for("admin.dashboard"))


# Branding (logo upload)
import os
from pathlib import Path
from flask import send_from_directory, send_file


@bp.route("/branding", methods=["GET", "POST"])
@login_required
def branding():
    if not current_user.is_authenticated or current_user.role != "admin":
        flash("Acesso restrito ao administrador.", "warning")
        return redirect(url_for("auth.login"))
    msg = None
    if request.method == "POST":
        f = request.files.get("logo")
        if not f or not f.filename:
            flash("Selecione um arquivo de imagem.", "warning")
            return redirect(url_for("admin.branding"))
        ext = os.path.splitext(f.filename.lower())[1]
        if ext not in {".png", ".jpg", ".jpeg", ".svg"}:
            flash("Formatos permitidos: .png, .jpg, .jpeg, .svg", "warning")
            return redirect(url_for("admin.branding"))
        folder = Path(current_app.instance_path) / "branding"
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / ("logo" + ext)
        # remove old logos
        for p in folder.glob("logo.*"):
            try: p.unlink()
            except Exception: pass
        f.save(path)
        flash("Logo atualizado.", "success")
        return redirect(url_for("admin.branding"))
    return render_template("admin/branding.html")


@bp.route("/branding/logo")
def brand_logo():
    folder = Path(current_app.instance_path) / "branding"
    for p in folder.glob("logo.*"):
        return send_from_directory(folder, p.name)
    return "", 404


# Settings page (logo upload, DB export, password change)
@bp.route("/settings", methods=["GET"])
@login_required
@admin_required
def settings():
    from pathlib import Path
    db_path = Path(current_app.instance_path) / "app.db"
    size = db_path.stat().st_size if db_path.exists() else 0
    return render_template("admin/settings.html", db_path=str(db_path), db_bytes=size)


@bp.route("/settings/logo", methods=["POST"])
@login_required
@admin_required
def settings_logo():
    f = request.files.get("logo")
    if not f or not f.filename:
        flash("Selecione um arquivo de imagem.", "warning")
        return redirect(url_for("admin.settings"))
    ext = os.path.splitext(f.filename.lower())[1]
    if ext not in {".png", ".jpg", ".jpeg", ".svg"}:
        flash("Formatos permitidos: .png, .jpg, .jpeg, .svg", "warning")
        return redirect(url_for("admin.settings"))
    folder = Path(current_app.instance_path) / "branding"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / ("logo" + ext)
    for p in folder.glob("logo.*"):
        try:
            p.unlink()
        except Exception:
            pass
    f.save(path)
    flash("Logo atualizado.", "success")
    return redirect(url_for("admin.settings"))


@bp.route("/export-db")
@login_required
@admin_required
def export_db():
    db_path = Path(current_app.instance_path) / "app.db"
    if not db_path.exists():
        flash("Banco de dados nao encontrado.", "danger")
        return redirect(url_for("admin.settings"))
    return send_file(db_path, as_attachment=True, download_name="backup-app.db")


@bp.route("/import-db", methods=["POST"])
@login_required
@admin_required
def import_db():
    """Importa um arquivo .db e substitui o banco atual com backup automático.

    Usa a API de backup do SQLite para copiar o conteúdo do arquivo enviado para o
    `instance/app.db` atual, evitando corrupção mesmo com o app em execução.
    """
    from pathlib import Path
    import sqlite3
    from datetime import datetime

    f = request.files.get("dbfile")
    if not f or not f.filename.lower().endswith(".db"):
        flash("Envie um arquivo .db válido.", "warning")
        return redirect(url_for("admin.settings"))
    inst = Path(current_app.instance_path)
    inst.mkdir(parents=True, exist_ok=True)
    tmp = inst / "_import_tmp.db"
    try:
        f.save(tmp)
    except Exception as e:
        flash(f"Falha ao salvar arquivo temporário: {e}", "danger")
        return redirect(url_for("admin.settings"))

    dest = inst / "app.db"
    # Backup do atual antes de importar
    try:
        backups = inst / "backups"
        backups.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        if dest.exists():
            backup_path = backups / f"before-import-{ts}.db"
            try:
                s = sqlite3.connect(dest)
                d = sqlite3.connect(backup_path)
                with d:
                    s.backup(d)
                s.close(); d.close()
            except Exception:
                from shutil import copy2
                copy2(dest, backup_path)
    except Exception:
        pass

    # Copiar conteúdo do arquivo enviado para o app.db
    try:
        src = sqlite3.connect(tmp)
        dst = sqlite3.connect(dest)
        with dst:
            src.backup(dst)
        src.close(); dst.close()
        flash("Banco importado com sucesso.", "success")
    except Exception as e:
        flash(f"Falha ao importar banco: {e}", "danger")
    finally:
        try:
            tmp.unlink(missing_ok=True)
        except Exception:
            pass
    return redirect(url_for("admin.settings"))


@bp.route("/settings/password", methods=["POST"])
@login_required
@admin_required
def change_password():
    new = (request.form.get("new_password") or "").strip()
    confirm = (request.form.get("confirm_password") or "").strip()
    if not new or not confirm:
        flash("Informe e confirme a nova senha.", "warning")
        return redirect(url_for("admin.settings"))
    if new != confirm:
        flash("As senhas nao coincidem.", "warning")
        return redirect(url_for("admin.settings"))
    current_user.set_password(new)
    db.session.commit()
    flash("Senha do administrador atualizada.", "success")
    return redirect(url_for("admin.settings"))


@bp.route("/settings/profile", methods=["POST"])
@login_required
@admin_required
def update_profile():
    from .models import User

    name = (request.form.get("name") or "").strip()
    email = (request.form.get("email") or "").strip().lower()
    if not name or not email:
        flash("Informe nome e e-mail.", "warning")
        return redirect(url_for("admin.settings"))
    # Email uniqueness
    existing = User.query.filter(User.email == email, User.id != current_user.id).first()
    if existing:
        flash("Este e-mail já está em uso.", "danger")
        return redirect(url_for("admin.settings"))
    current_user.name = name
    current_user.email = email
    db.session.commit()
    flash("Perfil atualizado.", "success")
    return redirect(url_for("admin.settings"))
