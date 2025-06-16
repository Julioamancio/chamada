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
