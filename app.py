import os
import secrets
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, login_user, logout_user, login_required,
    current_user, UserMixin
)
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import pandas as pd
from sqlalchemy.exc import OperationalError

load_dotenv()  # Só tem efeito local

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'chave_secreta')
app.config['UPLOAD_FOLDER'] = 'uploads'

DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "$b4jtcSMm4B$vn_")
DB_HOST = os.getenv("DB_HOST", "db.kemhqlfhsjolmuhpgyrd.supabase.co")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "postgres")

app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() in ['true', '1', 'yes']
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', 'julioamancio2014@gmail.com')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', 'bbkdgkdekincbdlq')
mail = Mail(app)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route("/health")
def health():
    try:
        db.session.execute("SELECT 1")
        return "✅ Banco de dados conectado!"
    except OperationalError as e:
        return f"❌ Erro ao conectar ao banco: {e}", 500

# === [MODELOS E RESTANTE DAS ROTAS ABAIXO] ===
# ... (TODO O RESTANTE DO SEU CÓDIGO IGUAL AO ORIGINAL, NADA MUDA) ...
# NÃO execute db.create_all() automaticamente!
# Crie um create_db.py para rodar apenas uma vez a criação de tabelas:
# from app import db, criar_etapas, app
# with app.app_context():
#     db.create_all()
#     criar_etapas()
