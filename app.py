from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import os
from datetime import datetime
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chave_secreta'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chamada.db'
app.config['UPLOAD_FOLDER'] = 'uploads'

# ---- CONFIG EMAIL (ajuste para seu provedor) ----
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'SEU_EMAIL@gmail.com'       # <-- Troque aqui
app.config['MAIL_PASSWORD'] = 'SENHA_DO_APP'              # <-- Troque aqui
mail = Mail(app)

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- Garante que a pasta de uploads existe (importante para Render/Heroku) ---
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# ---- MODELO DE USUÁRIO ----
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(128), nullable=False)
    reset_token = db.Column(db.String(128), nullable=True)
    turmas = db.relationship('Turma', backref='usuario', lazy=True)

    def set_password(self, senha):
        self.senha_hash = generate_password_hash(senha)
    def check_password(self, senha):
        return check_password_hash(self.senha_hash, senha)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---- MODELOS ----
class Turma(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    alunos = db.relationship('Aluno', backref='turma', lazy=True)
    chamadas = db.relationship('Chamada', backref='turma', lazy=True)

class Aluno(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    turma_id = db.Column(db.Integer, db.ForeignKey('turma.id'), nullable=False)

class Etapa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False)
    atividades = db.relationship('Atividade', backref='etapa', lazy=True)
    chamadas = db.relationship('Chamada', backref='etapa', lazy=True)

class Atividade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    pontuacao = db.Column(db.Integer, nullable=False)
    numero_dias = db.Column(db.Integer, nullable=False)
    etapa_id = db.Column(db.Integer, db.ForeignKey('etapa.id'), nullable=False)
    chamadas = db.relationship('Chamada', backref='atividade', lazy=True)

class Chamada(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date, nullable=False)
    turma_id = db.Column(db.Integer, db.ForeignKey('turma.id'), nullable=False)
    atividade_id = db.Column(db.Integer, db.ForeignKey('atividade.id'), nullable=False)
    etapa_id = db.Column(db.Integer, db.ForeignKey('etapa.id'), nullable=False)
    registros = db.relationship('Presenca', backref='chamada', lazy=True)

class Presenca(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chamada_id = db.Column(db.Integer, db.ForeignKey('chamada.id'), nullable=False)
    aluno_id = db.Column(db.Integer, db.ForeignKey('aluno.id'), nullable=False)
    presente = db.Column(db.Boolean, nullable=False)
    aluno = db.relationship('Aluno')

def criar_etapas():
    etapas_padrao = ["1ª Etapa", "2ª Etapa", "3ª Etapa"]
    for nome in etapas_padrao:
        if not Etapa.query.filter_by(nome=nome).first():
            db.session.add(Etapa(nome=nome))
    db.session.commit()

with app.app_context():
    db.create_all()
    criar_etapas()

# ---- ROTAS DE AUTENTICAÇÃO ----

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user and user.check_password(request.form['senha']):
            login_user(user)
            return redirect(url_for('index'))
        flash('E-mail ou senha inválidos!')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        if User.query.filter_by(email=request.form['email']).first():
            flash('E-mail já cadastrado!')
        else:
            user = User(email=request.form['email'])
            user.set_password(request.form['senha'])
            db.session.add(user)
            db.session.commit()
            flash('Usuário criado! Faça login.')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/reset', methods=['GET', 'POST'])
def reset_request():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user:
            token = secrets.token_urlsafe(32)
            user.reset_token = token
            db.session.commit()
            link = url_for('reset_token', token=token, _external=True)
            msg = Message("Recuperação de senha", recipients=[user.email],
                          body=f"Clique no link para redefinir sua senha: {link}")
            mail.send(msg)
            flash('E-mail enviado com instruções para redefinir sua senha!')
        else:
            flash('Se o e-mail existir, enviaremos um link de recuperação.')
    return render_template('reset_request.html')

@app.route('/reset/<token>', methods=['GET', 'POST'])
def reset_token(token):
    user = User.query.filter_by(reset_token=token).first()
    if not user:
        flash('Token inválido ou expirado!')
        return redirect(url_for('login'))
    if request.method == 'POST':
        user.set_password(request.form['senha'])
        user.reset_token = None
        db.session.commit()
        flash('Senha redefinida! Faça login.')
        return redirect(url_for('login'))
    return render_template('reset_token.html')

# ---- ROTAS DE TURMAS ----

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/inicio')
@login_required
def index():
    turmas = Turma.query.filter_by(user_id=current_user.id).all()
    return render_template('index.html', turmas=turmas)

@app.route('/turmas/add', methods=['GET', 'POST'])
@login_required
def turma_add():
    if request.method == 'POST':
        nome = request.form['nome']
        if nome:
            turma = Turma(nome=nome, user_id=current_user.id)
            db.session.add(turma)
            db.session.commit()
            return redirect(url_for('index'))
    return render_template('turma_form.html', turma=None)

@app.route('/turmas/<int:turma_id>')
@login_required
def turma_detail(turma_id):
    turma = Turma.query.filter_by(id=turma_id, user_id=current_user.id).first_or_404()
    chamadas = Chamada.query.filter_by(turma_id=turma_id).order_by(Chamada.data.desc()).all()
    return render_template('turma_detail.html', turma=turma, chamadas=chamadas)

@app.route('/turmas/<int:turma_id>/edit', methods=['GET', 'POST'])
@login_required
def turma_edit(turma_id):
    turma = Turma.query.filter_by(id=turma_id, user_id=current_user.id).first_or_404()
    if request.method == 'POST':
        nome = request.form['nome']
        if nome:
            turma.nome = nome
            db.session.commit()
            flash('Turma atualizada com sucesso!')
            return redirect(url_for('index'))
    return render_template('turma_form.html', turma=turma)

@app.route('/turmas/<int:turma_id>/delete', methods=['POST'])
@login_required
def turma_delete(turma_id):
    turma = Turma.query.filter_by(id=turma_id, user_id=current_user.id).first_or_404()
    for chamada in turma.chamadas:
        Presenca.query.filter_by(chamada_id=chamada.id).delete()
        db.session.delete(chamada)
    for aluno in turma.alunos:
        db.session.delete(aluno)
    db.session.delete(turma)
    db.session.commit()
    flash('Turma deletada com sucesso!')
    return redirect(url_for('index'))

@app.route('/turmas/<int:turma_id>/importar', methods=['GET', 'POST'])
@login_required
def importar_alunos(turma_id):
    turma = Turma.query.filter_by(id=turma_id, user_id=current_user.id).first_or_404()
    if request.method == 'POST':
        arquivo = request.files['arquivo']
        if not arquivo.filename.endswith('.xlsx'):
            flash('Envie um arquivo .xlsx')
            return redirect(request.url)
        caminho = os.path.join(app.config['UPLOAD_FOLDER'], arquivo.filename)
        try:
            arquivo.save(caminho)
        except Exception as e:
            flash(f"Erro ao salvar arquivo: {e}")
            return redirect(request.url)
        try:
            df = pd.read_excel(caminho, engine='openpyxl')
        except Exception as e:
            flash(f"Erro ao ler o arquivo Excel: {e}")
            return redirect(request.url)
        if 'Nome' not in df.columns:
            flash('Arquivo deve ter a coluna "Nome"')
            return redirect(request.url)
        for nome in df['Nome']:
            if isinstance(nome, str) and nome.strip():
                if not Aluno.query.filter_by(nome=nome.strip(), turma_id=turma.id).first():
                    aluno = Aluno(nome=nome.strip(), turma=turma)
                    db.session.add(aluno)
        db.session.commit()
        flash('Importação realizada!')
        return redirect(url_for('turma_detail', turma_id=turma_id))
    return render_template('importar_alunos.html', turma=turma)

@app.route('/turmas/<int:turma_id>/alunos', methods=['GET', 'POST'])
@login_required
def alunos(turma_id):
    turma = Turma.query.filter_by(id=turma_id, user_id=current_user.id).first_or_404()
    if request.method == 'POST':
        nome = request.form['nome']
        if nome and not Aluno.query.filter_by(nome=nome.strip(), turma_id=turma_id).first():
            aluno = Aluno(nome=nome.strip(), turma=turma)
            db.session.add(aluno)
            db.session.commit()
            flash('Aluno criado!')
    return render_template('alunos.html', turma=turma, alunos=turma.alunos)

@app.route('/alunos/edit/<int:aluno_id>', methods=['GET', 'POST'])
@login_required
def aluno_edit(aluno_id):
    aluno = Aluno.query.get_or_404(aluno_id)
    turma = Turma.query.filter_by(id=aluno.turma_id, user_id=current_user.id).first_or_404()
    if request.method == 'POST':
        nome = request.form['nome']
        if nome:
            aluno.nome = nome.strip()
            db.session.commit()
            flash('Aluno atualizado!')
            return redirect(url_for('alunos', turma_id=aluno.turma_id))
    return render_template('aluno_form.html', aluno=aluno)

@app.route('/alunos/delete/<int:aluno_id>', methods=['POST'])
@login_required
def aluno_delete(aluno_id):
    aluno = Aluno.query.get_or_404(aluno_id)
    turma = Turma.query.filter_by(id=aluno.turma_id, user_id=current_user.id).first_or_404()
    turma_id = aluno.turma_id
    db.session.delete(aluno)
    db.session.commit()
    flash('Aluno removido!')
    return redirect(url_for('alunos', turma_id=turma_id))

# --- ATIVIDADES ---
@app.route('/atividades')
@login_required
def atividades():
    atividades = Atividade.query.all()
    etapas = Etapa.query.all()
    return render_template('atividades.html', atividades=atividades, etapas=etapas)

@app.route('/atividades/add', methods=['GET', 'POST'])
@login_required
def atividade_add():
    etapas = Etapa.query.all()
    if request.method == 'POST':
        nome = request.form['nome']
        pontuacao = int(request.form['pontuacao'])
        numero_dias = int(request.form['numero_dias'])
        etapa_id = int(request.form['etapa_id'])
        if nome and pontuacao and numero_dias and etapa_id:
            atividade = Atividade(nome=nome, pontuacao=pontuacao, numero_dias=numero_dias, etapa_id=etapa_id)
            db.session.add(atividade)
            db.session.commit()
            flash('Atividade criada com sucesso!', 'success')
            return redirect(url_for('atividades'))
    return render_template('atividade_form.html', etapas=etapas, atividade=None)

@app.route('/atividades/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def atividade_edit(id):
    atividade = Atividade.query.get_or_404(id)
    etapas = Etapa.query.all()
    if request.method == 'POST':
        nome = request.form['nome']
        pontuacao = int(request.form['pontuacao'])
        numero_dias = int(request.form['numero_dias'])
        etapa_id = int(request.form['etapa_id'])
        if nome and pontuacao and numero_dias and etapa_id:
            atividade.nome = nome
            atividade.pontuacao = pontuacao
            atividade.numero_dias = numero_dias
            atividade.etapa_id = etapa_id
            db.session.commit()
            flash('Atividade atualizada com sucesso!', 'success')
            return redirect(url_for('atividades'))
    return render_template('atividade_form.html', etapas=etapas, atividade=atividade)

@app.route('/atividades/delete/<int:id>', methods=['POST'])
@login_required
def atividade_delete(id):
    atividade = Atividade.query.get_or_404(id)
    for chamada in atividade.chamadas:
        Presenca.query.filter_by(chamada_id=chamada.id).delete()
        db.session.delete(chamada)
    db.session.delete(atividade)
    db.session.commit()
    flash('Atividade deletada com sucesso!', 'success')
    return redirect(url_for('atividades'))

# --- CHAMADAS POR TURMA ---
@app.route('/chamada/<int:turma_id>', methods=['GET', 'POST'])
@login_required
def chamada(turma_id):
    turma = Turma.query.filter_by(id=turma_id, user_id=current_user.id).first_or_404()
    atividades = Atividade.query.all()
    etapas = Etapa.query.all()
    if request.method == 'POST':
        data_str = request.form['data']
        atividade_id = int(request.form['atividade_id'])
        etapa_id = int(request.form['etapa_id'])
        data = datetime.strptime(data_str, "%Y-%m-%d").date()
        chamada = Chamada.query.filter_by(data=data, turma_id=turma_id, atividade_id=atividade_id, etapa_id=etapa_id).first()
        if not chamada:
            chamada = Chamada(data=data, turma_id=turma_id, atividade_id=atividade_id, etapa_id=etapa_id)
            db.session.add(chamada)
            db.session.commit()
        atividade = Atividade.query.get(atividade_id)
        for aluno in turma.alunos:
            presente = f'presente_{aluno.id}' in request.form
            registro = Presenca.query.filter_by(chamada_id=chamada.id, aluno_id=aluno.id).first()
            if not registro:
                registro = Presenca(chamada_id=chamada.id, aluno_id=aluno.id, presente=presente)
                db.session.add(registro)
            else:
                registro.presente = presente
        db.session.commit()
        flash('Chamada salva!')
        return redirect(url_for('turma_detail', turma_id=turma_id))
    return render_template('chamada.html', turma=turma, atividades=atividades, etapas=etapas)

@app.route('/chamada/edit/<int:chamada_id>', methods=['GET', 'POST'])
@login_required
def chamada_edit(chamada_id):
    chamada = Chamada.query.get_or_404(chamada_id)
    turma = Turma.query.filter_by(id=chamada.turma_id, user_id=current_user.id).first_or_404()
    atividades = Atividade.query.all()
    etapas = Etapa.query.all()
    registros = {p.aluno_id: p for p in chamada.registros}
    if request.method == 'POST':
        data_str = request.form['data']
        atividade_id = int(request.form['atividade_id'])
        etapa_id = int(request.form['etapa_id'])
        chamada.data = datetime.strptime(data_str, "%Y-%m-%d").date()
        chamada.atividade_id = atividade_id
        chamada.etapa_id = etapa_id
        for aluno in turma.alunos:
            presente = f'presente_{aluno.id}' in request.form
            registro = registros.get(aluno.id)
            if registro:
                registro.presente = presente
            else:
                novo = Presenca(chamada_id=chamada.id, aluno_id=aluno.id, presente=presente)
                db.session.add(novo)
        db.session.commit()
        flash('Chamada editada!')
        return redirect(url_for('turma_detail', turma_id=turma.id))
    return render_template('chamada_edit.html', chamada=chamada, turma=turma, atividades=atividades, etapas=etapas, registros=registros)

@app.route('/chamada/delete/<int:chamada_id>', methods=['POST'])
@login_required
def chamada_delete(chamada_id):
    chamada = Chamada.query.get_or_404(chamada_id)
    turma = Turma.query.filter_by(id=chamada.turma_id, user_id=current_user.id).first_or_404()
    turma_id = chamada.turma_id
    Presenca.query.filter_by(chamada_id=chamada.id).delete()
    db.session.delete(chamada)
    db.session.commit()
    flash('Chamada removida!')
    return redirect(url_for('turma_detail', turma_id=turma_id))

@app.route('/relatorio/<int:turma_id>')
@login_required
def relatorio(turma_id):
    turma = Turma.query.filter_by(id=turma_id, user_id=current_user.id).first_or_404()
    tipo = request.args.get('tipo', 'detalhado')
    alunos = turma.alunos
    etapas = Etapa.query.all()
    chamadas = Chamada.query.filter_by(turma_id=turma_id).order_by(Chamada.data).all()
    resultados = []
    for aluno in alunos:
        total = 0
        por_etapa = {etapa.id: 0 for etapa in etapas}
        detalhes = []
        for chamada in chamadas:
            atividade = chamada.atividade
            etapa = chamada.etapa
            proporcao = atividade.pontuacao / atividade.numero_dias if atividade.numero_dias else 0
            presenca = Presenca.query.filter_by(chamada_id=chamada.id, aluno_id=aluno.id, presente=True).first()
            pontos = proporcao if presenca else 0
            total += pontos
            por_etapa[etapa.id] += pontos
            detalhes.append({
                "data": chamada.data,
                "atividade": atividade.nome,
                "etapa": etapa.nome,
                "pontuacao": pontos
            })
        resultados.append({
            "aluno": aluno.nome,
            "total": total,
            "por_etapa": por_etapa,
            "detalhes": detalhes
        })
    return render_template(
        'relatorio.html',
        turma=turma,
        resultados=resultados,
        etapas=etapas,
        tipo=tipo
    )

@app.route('/alunos/add/<int:turma_id>', methods=['GET', 'POST'])
@login_required
def aluno_add(turma_id):
    turma = Turma.query.filter_by(id=turma_id, user_id=current_user.id).first_or_404()
    if request.method == 'POST':
        nome = request.form['nome']
        if nome and not Aluno.query.filter_by(nome=nome.strip(), turma_id=turma_id).first():
            aluno = Aluno(nome=nome.strip(), turma=turma)
            db.session.add(aluno)
            db.session.commit()
            flash('Aluno criado!')
            return redirect(url_for('alunos', turma_id=turma_id))
    return render_template('aluno_form.html', turma=turma, aluno=None)

@app.route('/turmas/<int:turma_id>/copiar_atividades', methods=['GET', 'POST'])
@login_required
def copiar_atividades(turma_id):
    turma = Turma.query.filter_by(id=turma_id, user_id=current_user.id).first_or_404()
    atividades = Atividade.query.all()
    turmas = Turma.query.filter(Turma.id != turma_id, Turma.user_id == current_user.id).all()
    if request.method == 'POST':
        turmas_destino = [int(tid) for tid in request.form.getlist('turmas_destino')]
        atividades_ids = [int(aid) for aid in request.form.getlist('atividades_ids')]
        for tid in turmas_destino:
            for aid in atividades_ids:
                atividade = Atividade.query.get(aid)
                nova = Atividade(
                    nome=atividade.nome,
                    pontuacao=atividade.pontuacao,
                    numero_dias=atividade.numero_dias,
                    etapa_id=atividade.etapa_id
                )
                db.session.add(nova)
        db.session.commit()
        flash('Atividades copiadas com sucesso!')
        return redirect(url_for('turma_detail', turma_id=turma_id))
    return render_template('copiar_atividades.html', turma=turma, turmas=turmas, atividades=atividades)

@app.route('/turmas/<int:turma_id>/copiar_chamadas', methods=['GET', 'POST'])
@login_required
def copiar_chamadas(turma_id):
    turma = Turma.query.filter_by(id=turma_id, user_id=current_user.id).first_or_404()
    turmas = Turma.query.filter(Turma.id != turma_id, Turma.user_id == current_user.id).all()
    chamadas = Chamada.query.filter_by(turma_id=turma_id).all()
    if request.method == 'POST':
        turmas_destino = [int(tid) for tid in request.form.getlist('turmas_destino')]
        chamadas_ids = [int(cid) for cid in request.form.getlist('chamadas_ids')]
        for tid in turmas_destino:
            alunos_destino = Aluno.query.filter_by(turma_id=tid).all()
            for cid in chamadas_ids:
                chamada = Chamada.query.get(cid)
                nova_chamada = Chamada(
                    data=chamada.data,
                    turma_id=tid,
                    atividade_id=chamada.atividade_id,
                    etapa_id=chamada.etapa_id
                )
                db.session.add(nova_chamada)
                db.session.commit()
                for aluno in alunos_destino:
                    presenca = Presenca(
                        chamada_id=nova_chamada.id,
                        aluno_id=aluno.id,
                        presente=False
                    )
                    db.session.add(presenca)
                db.session.commit()
        flash('Chamadas copiadas com sucesso!')
        return redirect(url_for('turma_detail', turma_id=turma_id))
    return render_template('copiar_chamadas.html', turma=turma, turmas=turmas, chamadas=chamadas)

# Não inclua app.run() para produção.
