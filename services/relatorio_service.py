"""
Serviço de relatórios completo e profissional
Responsável pela lógica de negócio dos relatórios
"""
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
from collections import defaultdict
from app import db, Turma, Aluno, Chamada, Presenca, Atividade, Etapa


class RelatorioService:
    """Serviço principal para geração de relatórios"""
    
    @staticmethod
    def get_turma_statistics(turma_id: int, user_id: int, filtros: Dict = None) -> Dict[str, Any]:
        """
        Obtém estatísticas completas de uma turma
        """
        turma = Turma.query.filter_by(id=turma_id, user_id=user_id).first()
        if not turma:
            return None
            
        # Aplicar filtros
        query_chamadas = Chamada.query.filter_by(turma_id=turma_id)
        
        if filtros:
            if filtros.get('data_inicio'):
                query_chamadas = query_chamadas.filter(
                    Chamada.data >= datetime.strptime(filtros['data_inicio'], '%Y-%m-%d').date()
                )
            if filtros.get('data_fim'):
                query_chamadas = query_chamadas.filter(
                    Chamada.data <= datetime.strptime(filtros['data_fim'], '%Y-%m-%d').date()
                )
            if filtros.get('etapa_id'):
                query_chamadas = query_chamadas.filter_by(etapa_id=filtros['etapa_id'])
            if filtros.get('atividade_id'):
                query_chamadas = query_chamadas.filter_by(atividade_id=filtros['atividade_id'])
        
        chamadas = query_chamadas.order_by(Chamada.data).all()
        alunos = turma.alunos
        etapas = Etapa.query.all()
        
        # Calcular estatísticas por aluno
        resultados_alunos = []
        total_presencas = 0
        total_faltas = 0
        
        for aluno in alunos:
            pontuacao_total = 0
            pontuacao_por_etapa = {etapa.id: 0 for etapa in etapas}
            presencas_aluno = 0
            faltas_aluno = 0
            detalhes = []
            
            for chamada in chamadas:
                atividade = chamada.atividade
                etapa = chamada.etapa
                proporcao = atividade.pontuacao / atividade.numero_dias if atividade.numero_dias else 0
                
                presenca = Presenca.query.filter_by(
                    chamada_id=chamada.id, 
                    aluno_id=aluno.id
                ).first()
                
                if presenca and presenca.presente:
                    pontos = proporcao
                    presencas_aluno += 1
                    total_presencas += 1
                else:
                    pontos = 0
                    faltas_aluno += 1
                    total_faltas += 1
                
                pontuacao_total += pontos
                pontuacao_por_etapa[etapa.id] += pontos
                
                detalhes.append({
                    "data": chamada.data,
                    "atividade": atividade.nome,
                    "etapa": etapa.nome,
                    "pontuacao": pontos,
                    "presente": presenca.presente if presenca else False
                })
            
            percentual_presenca = (presencas_aluno / (presencas_aluno + faltas_aluno) * 100) if (presencas_aluno + faltas_aluno) > 0 else 0
            
            resultados_alunos.append({
                "aluno": aluno.nome,
                "aluno_id": aluno.id,
                "pontuacao_total": pontuacao_total,
                "pontuacao_por_etapa": pontuacao_por_etapa,
                "presencas": presencas_aluno,
                "faltas": faltas_aluno,
                "percentual_presenca": percentual_presenca,
                "detalhes": detalhes
            })
        
        # Calcular estatísticas gerais da turma
        if resultados_alunos:
            pontuacoes = [r["pontuacao_total"] for r in resultados_alunos]
            percentuais = [r["percentual_presenca"] for r in resultados_alunos]
            
            estatisticas_gerais = {
                "total_alunos": len(alunos),
                "total_chamadas": len(chamadas),
                "total_presencas": total_presencas,
                "total_faltas": total_faltas,
                "percentual_presenca_geral": (total_presencas / (total_presencas + total_faltas) * 100) if (total_presencas + total_faltas) > 0 else 0,
                "media_pontuacao": sum(pontuacoes) / len(pontuacoes) if pontuacoes else 0,
                "maior_pontuacao": max(pontuacoes) if pontuacoes else 0,
                "menor_pontuacao": min(pontuacoes) if pontuacoes else 0,
                "media_presenca": sum(percentuais) / len(percentuais) if percentuais else 0
            }
        else:
            estatisticas_gerais = {
                "total_alunos": 0,
                "total_chamadas": 0,
                "total_presencas": 0,
                "total_faltas": 0,
                "percentual_presenca_geral": 0,
                "media_pontuacao": 0,
                "maior_pontuacao": 0,
                "menor_pontuacao": 0,
                "media_presenca": 0
            }
        
        # Ranking dos alunos
        ranking = sorted(resultados_alunos, key=lambda x: x["pontuacao_total"], reverse=True)
        for i, aluno in enumerate(ranking):
            aluno["posicao"] = i + 1
        
        return {
            "turma": {
                "id": turma.id,
                "nome": turma.nome
            },
            "etapas": [{"id": e.id, "nome": e.nome} for e in etapas],
            "estatisticas_gerais": estatisticas_gerais,
            "resultados_alunos": resultados_alunos,
            "ranking": ranking,
            "chamadas": len(chamadas),
            "periodo": {
                "inicio": min([c.data for c in chamadas]) if chamadas else None,
                "fim": max([c.data for c in chamadas]) if chamadas else None
            }
        }
    
    @staticmethod
    def get_dados_grafico_barras(dados: Dict) -> Dict[str, Any]:
        """Prepara dados para gráfico de barras de pontuação por aluno"""
        if not dados.get("ranking"):
            return {"labels": [], "dados": []}
            
        labels = [aluno["aluno"] for aluno in dados["ranking"]]
        dados_pontuacao = [round(aluno["pontuacao_total"], 1) for aluno in dados["ranking"]]
        
        return {
            "labels": labels,
            "dados": dados_pontuacao,
            "cores": ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", 
                     "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"] * 10
        }
    
    @staticmethod
    def get_dados_grafico_pizza(dados: Dict) -> Dict[str, Any]:
        """Prepara dados para gráfico de pizza de presença/falta"""
        stats = dados.get("estatisticas_gerais", {})
        
        return {
            "labels": ["Presenças", "Faltas"],
            "dados": [stats.get("total_presencas", 0), stats.get("total_faltas", 0)],
            "cores": ["#28a745", "#dc3545"]
        }
    
    @staticmethod
    def get_dados_grafico_linhas(dados: Dict) -> Dict[str, Any]:
        """Prepara dados para gráfico de linhas - evolução temporal"""
        if not dados.get("resultados_alunos"):
            return {"labels": [], "datasets": []}
        
        # Agrupar dados por data
        datas_presenca = defaultdict(lambda: {"presencas": 0, "total": 0})
        
        for aluno in dados["resultados_alunos"]:
            for detalhe in aluno["detalhes"]:
                data_str = detalhe["data"].strftime("%d/%m")
                datas_presenca[data_str]["total"] += 1
                if detalhe["presente"]:
                    datas_presenca[data_str]["presencas"] += 1
        
        # Ordenar por data
        datas_ordenadas = sorted(datas_presenca.keys(), 
                                key=lambda x: datetime.strptime(x + "/2024", "%d/%m/%Y"))
        
        percentuais = []
        for data in datas_ordenadas:
            total = datas_presenca[data]["total"]
            presencas = datas_presenca[data]["presencas"]
            percentual = (presencas / total * 100) if total > 0 else 0
            percentuais.append(round(percentual, 1))
        
        return {
            "labels": datas_ordenadas,
            "datasets": [{
                "label": "% Presença por Dia",
                "data": percentuais,
                "borderColor": "#007bff",
                "backgroundColor": "rgba(0, 123, 255, 0.1)",
                "tension": 0.4
            }]
        }
    
    @staticmethod
    def preparar_dados_excel(dados: Dict) -> Dict[str, pd.DataFrame]:
        """Prepara dados para exportação em Excel"""
        sheets = {}
        
        # Aba 1: Resumo Geral
        resumo_data = []
        stats = dados.get("estatisticas_gerais", {})
        resumo_data.append(["Turma", dados["turma"]["nome"]])
        resumo_data.append(["Total de Alunos", stats.get("total_alunos", 0)])
        resumo_data.append(["Total de Chamadas", stats.get("total_chamadas", 0)])
        resumo_data.append(["Percentual de Presença Geral", f"{stats.get('percentual_presenca_geral', 0):.1f}%"])
        resumo_data.append(["Média de Pontuação", f"{stats.get('media_pontuacao', 0):.1f}"])
        resumo_data.append(["Maior Pontuação", f"{stats.get('maior_pontuacao', 0):.1f}"])
        resumo_data.append(["Menor Pontuação", f"{stats.get('menor_pontuacao', 0):.1f}"])
        
        sheets["Resumo"] = pd.DataFrame(resumo_data, columns=["Métrica", "Valor"])
        
        # Aba 2: Ranking dos Alunos
        ranking_data = []
        for aluno in dados.get("ranking", []):
            ranking_data.append({
                "Posição": aluno["posicao"],
                "Aluno": aluno["aluno"],
                "Pontuação Total": round(aluno["pontuacao_total"], 1),
                "Presenças": aluno["presencas"],
                "Faltas": aluno["faltas"],
                "% Presença": f"{aluno['percentual_presenca']:.1f}%"
            })
        
        sheets["Ranking"] = pd.DataFrame(ranking_data)
        
        # Aba 3: Detalhado por Etapa
        if dados.get("etapas"):
            detalhado_data = []
            for aluno in dados.get("resultados_alunos", []):
                row = {"Aluno": aluno["aluno"]}
                for etapa in dados["etapas"]:
                    etapa_id = etapa["id"]
                    pontuacao = aluno["pontuacao_por_etapa"].get(etapa_id, 0)
                    row[etapa["nome"]] = round(pontuacao, 1)
                row["Total"] = round(aluno["pontuacao_total"], 1)
                detalhado_data.append(row)
            
            sheets["Por Etapa"] = pd.DataFrame(detalhado_data)
        
        return sheets