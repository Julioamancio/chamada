# ... (todo o seu código anterior igual) ...

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
    # Remove chamadas relacionadas à atividade (e presenças)
    for chamada in atividade.chamadas:
        Presenca.query.filter_by(chamada_id=chamada.id).delete()
        db.session.delete(chamada)
    db.session.delete(atividade)
    db.session.commit()
    flash('Atividade deletada com sucesso!', 'success')
    return redirect(url_for('atividades'))

# ... (restante do seu código igual) ...
