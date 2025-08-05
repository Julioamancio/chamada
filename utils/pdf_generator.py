"""
Gerador de PDFs profissionais para relatórios
Utiliza WeasyPrint para gerar PDFs com alta qualidade
"""
import os
import io
import base64
from datetime import datetime
from typing import Dict, Any
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend
import matplotlib.pyplot as plt
import pandas as pd
from weasyprint import HTML, CSS
from matplotlib.figure import Figure
import numpy as np


class PDFGenerator:
    """Gerador de PDFs profissionais com gráficos incorporados"""
    
    @staticmethod
    def gerar_grafico_barras(dados: Dict[str, Any]) -> str:
        """Gera gráfico de barras em base64 para incorporar no PDF"""
        if not dados.get("labels") or not dados.get("dados"):
            return ""
            
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Criar gráfico de barras
        bars = ax.bar(dados["labels"], dados["dados"], 
                     color=dados.get("cores", ["#1f77b4"] * len(dados["labels"])))
        
        # Personalizar aparência
        ax.set_title("Pontuação por Aluno", fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel("Alunos", fontsize=12)
        ax.set_ylabel("Pontuação", fontsize=12)
        
        # Rotacionar labels do eixo x se necessário
        if len(dados["labels"]) > 8:
            plt.xticks(rotation=45, ha='right')
        
        # Adicionar valores nas barras
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                   f'{height:.1f}', ha='center', va='bottom', fontsize=10)
        
        # Melhorar layout
        plt.tight_layout()
        
        # Converter para base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close(fig)
        
        return f"data:image/png;base64,{image_base64}"
    
    @staticmethod
    def gerar_grafico_pizza(dados: Dict[str, Any]) -> str:
        """Gera gráfico de pizza em base64 para incorporar no PDF"""
        if not dados.get("labels") or not dados.get("dados"):
            return ""
            
        fig, ax = plt.subplots(figsize=(8, 8))
        
        # Criar gráfico de pizza
        wedges, texts, autotexts = ax.pie(
            dados["dados"], 
            labels=dados["labels"],
            colors=dados.get("cores", ["#28a745", "#dc3545"]),
            autopct='%1.1f%%',
            startangle=90,
            textprops={'fontsize': 12}
        )
        
        # Personalizar aparência
        ax.set_title("Distribuição de Presenças vs Faltas", 
                    fontsize=16, fontweight='bold', pad=20)
        
        # Melhorar aparência dos textos
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        # Converter para base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close(fig)
        
        return f"data:image/png;base64,{image_base64}"
    
    @staticmethod
    def gerar_html_relatorio(dados: Dict[str, Any], tipo: str = "completo") -> str:
        """Gera HTML formatado para conversão em PDF"""
        
        # Gerar gráficos
        grafico_barras = PDFGenerator.gerar_grafico_barras(
            PDFGenerator._preparar_dados_grafico_barras(dados)
        )
        grafico_pizza = PDFGenerator.gerar_grafico_pizza(
            PDFGenerator._preparar_dados_grafico_pizza(dados)
        )
        
        # Template HTML profissional
        html_template = f"""
        <!DOCTYPE html>
        <html lang="pt-br">
        <head>
            <meta charset="UTF-8">
            <title>Relatório - {dados['turma']['nome']}</title>
            <style>
                @page {{
                    size: A4;
                    margin: 2cm;
                    @bottom-center {{
                        content: "Página " counter(page) " de " counter(pages);
                        font-size: 10px;
                        color: #666;
                    }}
                }}
                
                body {{
                    font-family: 'Arial', sans-serif;
                    line-height: 1.6;
                    color: #333;
                    margin: 0;
                    padding: 0;
                }}
                
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                    padding: 20px;
                    background: linear-gradient(135deg, #1476f2, #0d47a1);
                    color: white;
                    border-radius: 8px;
                }}
                
                .header h1 {{
                    margin: 0;
                    font-size: 24px;
                    font-weight: bold;
                }}
                
                .header p {{
                    margin: 5px 0 0 0;
                    font-size: 14px;
                    opacity: 0.9;
                }}
                
                .stats-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 15px;
                    margin: 20px 0;
                }}
                
                .stat-card {{
                    background: #f8f9fa;
                    padding: 15px;
                    border-radius: 8px;
                    border-left: 4px solid #1476f2;
                    text-align: center;
                }}
                
                .stat-card h4 {{
                    margin: 0 0 10px 0;
                    color: #1476f2;
                    font-size: 14px;
                    text-transform: uppercase;
                }}
                
                .stat-card .value {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #333;
                }}
                
                .chart-container {{
                    text-align: center;
                    margin: 30px 0;
                    page-break-inside: avoid;
                }}
                
                .chart-container img {{
                    max-width: 100%;
                    height: auto;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                
                .table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                    background: white;
                    border-radius: 8px;
                    overflow: hidden;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                
                .table th {{
                    background: #1476f2;
                    color: white;
                    padding: 12px;
                    text-align: left;
                    font-weight: bold;
                    font-size: 12px;
                }}
                
                .table td {{
                    padding: 10px 12px;
                    border-bottom: 1px solid #eee;
                    font-size: 11px;
                }}
                
                .table tr:nth-child(even) td {{
                    background: #f8f9fa;
                }}
                
                .ranking-badge {{
                    display: inline-block;
                    width: 25px;
                    height: 25px;
                    line-height: 25px;
                    text-align: center;
                    border-radius: 50%;
                    color: white;
                    font-weight: bold;
                    font-size: 12px;
                }}
                
                .ranking-1 {{ background: #ffd700; color: #333; }}
                .ranking-2 {{ background: #c0c0c0; color: #333; }}
                .ranking-3 {{ background: #cd7f32; }}
                .ranking-other {{ background: #6c757d; }}
                
                .section-title {{
                    font-size: 18px;
                    color: #1476f2;
                    border-bottom: 2px solid #1476f2;
                    padding-bottom: 5px;
                    margin: 30px 0 15px 0;
                }}
                
                .watermark {{
                    position: fixed;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%) rotate(-45deg);
                    font-size: 60px;
                    color: rgba(20, 118, 242, 0.05);
                    z-index: -1;
                    pointer-events: none;
                }}
            </style>
        </head>
        <body>
            <div class="watermark">RELATÓRIO ESCOLAR</div>
            
            <div class="header">
                <h1>📊 Relatório de Chamada Escolar</h1>
                <p>Turma: {dados['turma']['nome']}</p>
                <p>Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}</p>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <h4>Total de Alunos</h4>
                    <div class="value">{dados['estatisticas_gerais']['total_alunos']}</div>
                </div>
                <div class="stat-card">
                    <h4>Total de Chamadas</h4>
                    <div class="value">{dados['estatisticas_gerais']['total_chamadas']}</div>
                </div>
                <div class="stat-card">
                    <h4>Presença Geral</h4>
                    <div class="value">{dados['estatisticas_gerais']['percentual_presenca_geral']:.1f}%</div>
                </div>
                <div class="stat-card">
                    <h4>Média da Turma</h4>
                    <div class="value">{dados['estatisticas_gerais']['media_pontuacao']:.1f}</div>
                </div>
            </div>
        """
        
        # Adicionar gráficos se disponíveis
        if grafico_barras:
            html_template += f"""
            <h2 class="section-title">📈 Pontuação por Aluno</h2>
            <div class="chart-container">
                <img src="{grafico_barras}" alt="Gráfico de Barras - Pontuação por Aluno">
            </div>
            """
        
        if grafico_pizza:
            html_template += f"""
            <h2 class="section-title">🥧 Distribuição de Presenças</h2>
            <div class="chart-container">
                <img src="{grafico_pizza}" alt="Gráfico de Pizza - Distribuição de Presenças">
            </div>
            """
        
        # Tabela de ranking
        if dados.get("ranking"):
            html_template += """
            <h2 class="section-title">🏆 Ranking dos Alunos</h2>
            <table class="table">
                <thead>
                    <tr>
                        <th>Pos.</th>
                        <th>Aluno</th>
                        <th>Pontuação Total</th>
                        <th>Presenças</th>
                        <th>Faltas</th>
                        <th>% Presença</th>
                    </tr>
                </thead>
                <tbody>
            """
            
            for aluno in dados["ranking"]:
                posicao = aluno["posicao"]
                badge_class = f"ranking-{posicao}" if posicao <= 3 else "ranking-other"
                
                html_template += f"""
                    <tr>
                        <td><span class="ranking-badge {badge_class}">{posicao}</span></td>
                        <td>{aluno['aluno']}</td>
                        <td>{aluno['pontuacao_total']:.1f}</td>
                        <td>{aluno['presencas']}</td>
                        <td>{aluno['faltas']}</td>
                        <td>{aluno['percentual_presenca']:.1f}%</td>
                    </tr>
                """
            
            html_template += """
                </tbody>
            </table>
            """
        
        # Detalhes por etapa se solicitado
        if tipo == "completo" and dados.get("etapas"):
            html_template += """
            <h2 class="section-title">📋 Pontuação por Etapa</h2>
            <table class="table">
                <thead>
                    <tr>
                        <th>Aluno</th>
            """
            
            for etapa in dados["etapas"]:
                html_template += f"<th>{etapa['nome']}</th>"
            
            html_template += """
                        <th>Total</th>
                    </tr>
                </thead>
                <tbody>
            """
            
            for aluno in dados.get("resultados_alunos", []):
                html_template += f"<tr><td>{aluno['aluno']}</td>"
                
                for etapa in dados["etapas"]:
                    pontuacao = aluno["pontuacao_por_etapa"].get(etapa["id"], 0)
                    html_template += f"<td>{pontuacao:.1f}</td>"
                
                html_template += f"<td><strong>{aluno['pontuacao_total']:.1f}</strong></td></tr>"
            
            html_template += """
                </tbody>
            </table>
            """
        
        html_template += """
        </body>
        </html>
        """
        
        return html_template
    
    @staticmethod
    def gerar_pdf(dados: Dict[str, Any], tipo: str = "completo") -> bytes:
        """Gera arquivo PDF a partir dos dados"""
        html_content = PDFGenerator.gerar_html_relatorio(dados, tipo)
        
        # CSS adicional para melhor impressão
        css_content = CSS(string="""
            @page {
                size: A4;
                margin: 2cm;
            }
            
            .chart-container {
                page-break-inside: avoid;
            }
            
            .table {
                page-break-inside: avoid;
            }
            
            .stats-grid {
                page-break-inside: avoid;
            }
        """)
        
        # Gerar PDF
        pdf_file = HTML(string=html_content).write_pdf(stylesheets=[css_content])
        return pdf_file
    
    @staticmethod
    def _preparar_dados_grafico_barras(dados: Dict) -> Dict[str, Any]:
        """Prepara dados para gráfico de barras (compatível com matplotlib)"""
        if not dados.get("ranking"):
            return {"labels": [], "dados": []}
            
        # Limitar a 10 alunos para melhor visualização
        ranking_top = dados["ranking"][:10]
        
        labels = [aluno["aluno"] for aluno in ranking_top]
        dados_pontuacao = [round(aluno["pontuacao_total"], 1) for aluno in ranking_top]
        
        return {
            "labels": labels,
            "dados": dados_pontuacao,
            "cores": ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", 
                     "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"]
        }
    
    @staticmethod
    def _preparar_dados_grafico_pizza(dados: Dict) -> Dict[str, Any]:
        """Prepara dados para gráfico de pizza (compatível com matplotlib)"""
        stats = dados.get("estatisticas_gerais", {})
        
        return {
            "labels": ["Presenças", "Faltas"],
            "dados": [stats.get("total_presencas", 0), stats.get("total_faltas", 0)],
            "cores": ["#28a745", "#dc3545"]
        }