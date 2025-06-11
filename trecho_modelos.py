class Etapa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False)
    atividades = db.relationship('Atividade', backref='etapa', lazy=True)
    chamadas = db.relationship('Chamada', backref='etapa', lazy=True)

class Atividade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    pontuacao = db.Column(db.Integer, nullable=False)
    numero_dias = db.Column(db.Integer, nullable=False)  # dias/aulas para a etapa
    etapa_id = db.Column(db.Integer, db.ForeignKey('etapa.id'), nullable=False)

class Chamada(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date, nullable=False)
    turma_id = db.Column(db.Integer, db.ForeignKey('turma.id'), nullable=False)
    atividade_id = db.Column(db.Integer, db.ForeignKey('atividade.id'), nullable=False)
    etapa_id = db.Column(db.Integer, db.ForeignKey('etapa.id'), nullable=False)
    registros = db.relationship('Presenca', backref='chamada', lazy=True)
    atividade = db.relationship('Atividade')