"""
Rotas específicas para o sistema de relatórios
Gerencia todas as requisições relacionadas aos relatórios
"""
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, send_file, flash, redirect, url_for
from flask_login import login_required, current_user
import io
import json


# Criar blueprint para relatórios
relatorios_bp = Blueprint('relatorios', __name__, url_prefix='/relatorios')


@relatorios_bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard principal dos relatórios"""
    from app import Turma
    turmas = Turma.query.filter_by(user_id=current_user.id).all()
    return render_template('relatorios/dashboard.html', turmas=turmas)


@relatorios_bp.route('/configurar/<int:turma_id>')
@login_required
def configurar(turma_id):
    """Página de configuração de filtros para relatório"""
    from app import Turma, Etapa, Atividade
    turma = Turma.query.filter_by(id=turma_id, user_id=current_user.id).first_or_404()
    etapas = Etapa.query.all()
    atividades = Atividade.query.all()
    
    return render_template('relatorios/configurar.html', 
                         turma=turma, 
                         etapas=etapas, 
                         atividades=atividades)


@relatorios_bp.route('/detalhado/<int:turma_id>')
@login_required
def detalhado(turma_id):
    """Relatório detalhado com visualizações"""
    from app import Turma
    from services.relatorio_service import RelatorioService
    
    turma = Turma.query.filter_by(id=turma_id, user_id=current_user.id).first_or_404()
    
    # Obter filtros da query string
    filtros = {}
    if request.args.get('data_inicio'):
        filtros['data_inicio'] = request.args.get('data_inicio')
    if request.args.get('data_fim'):
        filtros['data_fim'] = request.args.get('data_fim')
    if request.args.get('etapa_id'):
        filtros['etapa_id'] = int(request.args.get('etapa_id'))
    if request.args.get('atividade_id'):
        filtros['atividade_id'] = int(request.args.get('atividade_id'))
    
    # Obter dados estatísticos
    dados = RelatorioService.get_turma_statistics(turma_id, current_user.id, filtros)
    
    if not dados:
        flash('Turma não encontrada!', 'error')
        return redirect(url_for('relatorios.dashboard'))
    
    # Preparar dados para gráficos
    grafico_barras = RelatorioService.get_dados_grafico_barras(dados)
    grafico_pizza = RelatorioService.get_dados_grafico_pizza(dados)
    grafico_linhas = RelatorioService.get_dados_grafico_linhas(dados)
    
    return render_template('relatorios/detalhado.html',
                         dados=dados,
                         grafico_barras=json.dumps(grafico_barras),
                         grafico_pizza=json.dumps(grafico_pizza),
                         grafico_linhas=json.dumps(grafico_linhas),
                         filtros=filtros)


@relatorios_bp.route('/api/dados/<int:turma_id>')
@login_required
def api_dados(turma_id):
    """API para obter dados da turma em formato JSON"""
    from app import Turma
    from services.relatorio_service import RelatorioService
    
    # Verificar se o usuário tem acesso à turma
    turma = Turma.query.filter_by(id=turma_id, user_id=current_user.id).first()
    if not turma:
        return jsonify({'error': 'Turma não encontrada'}), 404
    
    # Obter filtros
    filtros = {}
    if request.args.get('data_inicio'):
        filtros['data_inicio'] = request.args.get('data_inicio')
    if request.args.get('data_fim'):
        filtros['data_fim'] = request.args.get('data_fim')
    if request.args.get('etapa_id'):
        filtros['etapa_id'] = int(request.args.get('etapa_id'))
    if request.args.get('atividade_id'):
        filtros['atividade_id'] = int(request.args.get('atividade_id'))
    
    # Obter dados
    dados = RelatorioService.get_turma_statistics(turma_id, current_user.id, filtros)
    
    # Preparar resposta JSON
    if dados:
        # Converter datas para strings para serialização JSON
        for aluno in dados.get('resultados_alunos', []):
            for detalhe in aluno.get('detalhes', []):
                if detalhe.get('data'):
                    detalhe['data'] = detalhe['data'].strftime('%Y-%m-%d')
        
        if dados.get('periodo', {}).get('inicio'):
            dados['periodo']['inicio'] = dados['periodo']['inicio'].strftime('%Y-%m-%d')
        if dados.get('periodo', {}).get('fim'):
            dados['periodo']['fim'] = dados['periodo']['fim'].strftime('%Y-%m-%d')
        
        return jsonify(dados)
    else:
        return jsonify({'error': 'Dados não encontrados'}), 404


@relatorios_bp.route('/exportar/pdf/<int:turma_id>')
@login_required
def exportar_pdf(turma_id):
    """Exportar relatório em PDF profissional"""
    from app import Turma
    from services.relatorio_service import RelatorioService
    from utils.pdf_generator import PDFGenerator
    
    turma = Turma.query.filter_by(id=turma_id, user_id=current_user.id).first_or_404()
    
    # Obter filtros
    filtros = {}
    if request.args.get('data_inicio'):
        filtros['data_inicio'] = request.args.get('data_inicio')
    if request.args.get('data_fim'):
        filtros['data_fim'] = request.args.get('data_fim')
    if request.args.get('etapa_id'):
        filtros['etapa_id'] = int(request.args.get('etapa_id'))
    if request.args.get('atividade_id'):
        filtros['atividade_id'] = int(request.args.get('atividade_id'))
    
    tipo = request.args.get('tipo', 'completo')  # completo ou resumido
    
    # Obter dados
    dados = RelatorioService.get_turma_statistics(turma_id, current_user.id, filtros)
    
    if not dados:
        flash('Erro ao gerar relatório PDF!', 'error')
        return redirect(url_for('relatorios.detalhado', turma_id=turma_id))
    
    try:
        # Gerar PDF
        pdf_bytes = PDFGenerator.gerar_pdf(dados, tipo)
        
        # Criar arquivo em memória
        pdf_buffer = io.BytesIO(pdf_bytes)
        pdf_buffer.seek(0)
        
        # Nome do arquivo
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"relatorio_{turma.nome.replace(' ', '_')}_{timestamp}.pdf"
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        flash(f'Erro ao gerar PDF: {str(e)}', 'error')
        return redirect(url_for('relatorios.detalhado', turma_id=turma_id))


@relatorios_bp.route('/exportar/excel/<int:turma_id>')
@login_required
def exportar_excel(turma_id):
    """Exportar relatório em Excel com múltiplas abas"""
    from app import Turma
    from services.relatorio_service import RelatorioService
    from utils.excel_generator import ExcelGenerator
    
    turma = Turma.query.filter_by(id=turma_id, user_id=current_user.id).first_or_404()
    
    # Obter filtros
    filtros = {}
    if request.args.get('data_inicio'):
        filtros['data_inicio'] = request.args.get('data_inicio')
    if request.args.get('data_fim'):
        filtros['data_fim'] = request.args.get('data_fim')
    if request.args.get('etapa_id'):
        filtros['etapa_id'] = int(request.args.get('etapa_id'))
    if request.args.get('atividade_id'):
        filtros['atividade_id'] = int(request.args.get('atividade_id'))
    
    # Obter dados
    dados = RelatorioService.get_turma_statistics(turma_id, current_user.id, filtros)
    
    if not dados:
        flash('Erro ao gerar relatório Excel!', 'error')
        return redirect(url_for('relatorios.detalhado', turma_id=turma_id))
    
    try:
        # Gerar Excel
        excel_bytes = ExcelGenerator.gerar_excel(dados)
        
        # Criar arquivo em memória
        excel_buffer = io.BytesIO(excel_bytes)
        excel_buffer.seek(0)
        
        # Nome do arquivo
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"relatorio_{turma.nome.replace(' ', '_')}_{timestamp}.xlsx"
        
        return send_file(
            excel_buffer,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        flash(f'Erro ao gerar Excel: {str(e)}', 'error')
        return redirect(url_for('relatorios.detalhado', turma_id=turma_id))


@relatorios_bp.route('/api/graficos/<int:turma_id>')
@login_required
def api_graficos(turma_id):
    """API para obter dados dos gráficos"""
    from app import Turma
    from services.relatorio_service import RelatorioService
    
    turma = Turma.query.filter_by(id=turma_id, user_id=current_user.id).first()
    if not turma:
        return jsonify({'error': 'Turma não encontrada'}), 404
    
    # Obter filtros
    filtros = {}
    if request.args.get('data_inicio'):
        filtros['data_inicio'] = request.args.get('data_inicio')
    if request.args.get('data_fim'):
        filtros['data_fim'] = request.args.get('data_fim')
    if request.args.get('etapa_id'):
        filtros['etapa_id'] = int(request.args.get('etapa_id'))
    if request.args.get('atividade_id'):
        filtros['atividade_id'] = int(request.args.get('atividade_id'))
    
    # Obter dados
    dados = RelatorioService.get_turma_statistics(turma_id, current_user.id, filtros)
    
    if not dados:
        return jsonify({'error': 'Dados não encontrados'}), 404
    
    # Preparar dados dos gráficos
    resposta = {
        'barras': RelatorioService.get_dados_grafico_barras(dados),
        'pizza': RelatorioService.get_dados_grafico_pizza(dados),
        'linhas': RelatorioService.get_dados_grafico_linhas(dados)
    }
    
    return jsonify(resposta)


@relatorios_bp.route('/preview/pdf/<int:turma_id>')
@login_required
def preview_pdf(turma_id):
    """Preview do PDF no navegador (sem download)"""
    from app import Turma
    from services.relatorio_service import RelatorioService
    from utils.pdf_generator import PDFGenerator
    
    turma = Turma.query.filter_by(id=turma_id, user_id=current_user.id).first_or_404()
    
    # Obter filtros
    filtros = {}
    if request.args.get('data_inicio'):
        filtros['data_inicio'] = request.args.get('data_inicio')
    if request.args.get('data_fim'):
        filtros['data_fim'] = request.args.get('data_fim')
    if request.args.get('etapa_id'):
        filtros['etapa_id'] = int(request.args.get('etapa_id'))
    if request.args.get('atividade_id'):
        filtros['atividade_id'] = int(request.args.get('atividade_id'))
    
    tipo = request.args.get('tipo', 'completo')
    
    # Obter dados
    dados = RelatorioService.get_turma_statistics(turma_id, current_user.id, filtros)
    
    if not dados:
        flash('Erro ao gerar preview do relatório!', 'error')
        return redirect(url_for('relatorios.detalhado', turma_id=turma_id))
    
    try:
        # Gerar PDF
        pdf_bytes = PDFGenerator.gerar_pdf(dados, tipo)
        
        # Criar arquivo em memória
        pdf_buffer = io.BytesIO(pdf_bytes)
        pdf_buffer.seek(0)
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=False  # Para abrir no navegador
        )
        
    except Exception as e:
        flash(f'Erro ao gerar preview: {str(e)}', 'error')
        return redirect(url_for('relatorios.detalhado', turma_id=turma_id))