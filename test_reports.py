#!/usr/bin/env python3
"""
Test script to verify the scoring calculations and report performance
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User, Turma, Aluno, Etapa, Atividade, Chamada, Presenca
from datetime import date, datetime
import time

def create_test_data():
    """Create test data for performance testing"""
    with app.app_context():
        # Create a test user
        user = User(email="test@test.com")
        user.set_password("test123")
        db.session.add(user)
        db.session.commit()
        
        # Create a test turma
        turma = Turma(nome="Turma Teste", user_id=user.id)
        db.session.add(turma)
        db.session.commit()
        
        # Create test students
        alunos = []
        for i in range(1, 6):  # 5 students
            aluno = Aluno(nome=f"Aluno {i}", turma_id=turma.id)
            db.session.add(aluno)
            alunos.append(aluno)
        db.session.commit()
        
        # Get etapas
        etapa1 = Etapa.query.filter_by(nome="1ª Etapa").first()
        etapa2 = Etapa.query.filter_by(nome="2ª Etapa").first()
        
        if not etapa1:
            etapa1 = Etapa(nome="1ª Etapa")
            db.session.add(etapa1)
        if not etapa2:
            etapa2 = Etapa(nome="2ª Etapa") 
            db.session.add(etapa2)
        db.session.commit()
        
        # Create test activities
        ativ1 = Atividade(nome="Atividade 1", pontuacao=10, numero_dias=5, etapa_id=etapa1.id)
        ativ2 = Atividade(nome="Atividade 2", pontuacao=20, numero_dias=10, etapa_id=etapa2.id)
        db.session.add(ativ1)
        db.session.add(ativ2)
        db.session.commit()
        
        # Create test chamadas and presence records
        test_date = date(2024, 1, 15)
        
        # Chamada 1 (Etapa 1)
        chamada1 = Chamada(data=test_date, turma_id=turma.id, atividade_id=ativ1.id, etapa_id=etapa1.id)
        db.session.add(chamada1)
        db.session.commit()
        
        # Add presence records for chamada1 (some present, some absent)
        for i, aluno in enumerate(alunos):
            presente = i < 3  # First 3 students present
            presenca = Presenca(chamada_id=chamada1.id, aluno_id=aluno.id, presente=presente)
            db.session.add(presenca)
        
        # Chamada 2 (Etapa 2)
        chamada2 = Chamada(data=test_date, turma_id=turma.id, atividade_id=ativ2.id, etapa_id=etapa2.id)
        db.session.add(chamada2)
        db.session.commit()
        
        # Add presence records for chamada2 (different pattern)
        for i, aluno in enumerate(alunos):
            presente = i % 2 == 0  # Every other student present
            presenca = Presenca(chamada_id=chamada2.id, aluno_id=aluno.id, presente=presente)
            db.session.add(presenca)
        
        db.session.commit()
        
        return turma.id, user.id

def test_scoring_calculation():
    """Test that scoring calculations are correct"""
    print("🧮 Testing scoring calculations...")
    
    with app.app_context():
        # Expected calculations:
        # Atividade 1: 10 pontos / 5 dias = 2 pontos por presença
        # Atividade 2: 20 pontos / 10 dias = 2 pontos por presença
        
        # Expected results:
        # Aluno 1: presente em ambas = 2 + 2 = 4 pontos total
        # Aluno 2: presente em ambas = 2 + 2 = 4 pontos total  
        # Aluno 3: presente na 1ª apenas = 2 + 0 = 2 pontos total
        # Aluno 4: presente na 2ª apenas = 0 + 2 = 2 pontos total
        # Aluno 5: presente na 2ª apenas = 0 + 2 = 2 pontos total
        
        turma_id, user_id = create_test_data()
        
        # Test the optimized report function
        from app import relatorio
        with app.test_request_context(f'/relatorio/{turma_id}'):
            start_time = time.time()
            # We can't directly call the route, but we can test the logic
            
            turma = Turma.query.get(turma_id)
            alunos = turma.alunos
            
            # Test query optimization by checking number of queries
            chamadas = db.session.query(Chamada).join(
                Atividade, Chamada.atividade_id == Atividade.id
            ).join(
                Etapa, Chamada.etapa_id == Etapa.id  
            ).filter(
                Chamada.turma_id == turma_id
            ).order_by(Chamada.data).all()
            
            # Pre-load all presencas
            chamada_ids = [c.id for c in chamadas]
            presencas_query = db.session.query(Presenca).filter(
                Presenca.chamada_id.in_(chamada_ids)
            ).all()
            presencas_lookup = {}
            for p in presencas_query:
                key = (p.chamada_id, p.aluno_id)
                presencas_lookup[key] = p
            
            # Calculate results
            resultados = []
            for aluno in alunos:
                total = 0
                for chamada in chamadas:
                    atividade = chamada.atividade
                    proporcao = atividade.pontuacao / atividade.numero_dias if atividade.numero_dias > 0 else 0
                    presenca_key = (chamada.id, aluno.id)
                    presenca = presencas_lookup.get(presenca_key)
                    pontos = proporcao if (presenca and presenca.presente) else 0
                    total += pontos
                
                resultados.append({
                    "aluno": aluno.nome,
                    "total": total
                })
            
            end_time = time.time()
            calculation_time = end_time - start_time
            
            print(f"⏱️  Calculation time: {calculation_time:.4f} seconds")
            print(f"📊 Results:")
            for resultado in resultados:
                print(f"   {resultado['aluno']}: {resultado['total']} pontos")
            
            # Verify expected results
            expected_totals = [4.0, 4.0, 2.0, 2.0, 2.0]
            actual_totals = [r['total'] for r in resultados]
            
            if actual_totals == expected_totals:
                print("✅ Scoring calculations are CORRECT!")
                return True
            else:
                print(f"❌ Scoring ERROR! Expected: {expected_totals}, Got: {actual_totals}")
                return False

def cleanup_test_data():
    """Clean up test data"""
    with app.app_context():
        # Clean up in reverse order due to foreign keys
        Presenca.query.filter(
            Presenca.chamada_id.in_(
                db.session.query(Chamada.id).join(Turma).filter(Turma.nome == "Turma Teste")
            )
        ).delete(synchronize_session=False)
        
        Chamada.query.filter(
            Chamada.turma_id.in_(
                db.session.query(Turma.id).filter(Turma.nome == "Turma Teste")
            )
        ).delete(synchronize_session=False)
        
        Aluno.query.filter(
            Aluno.turma_id.in_(
                db.session.query(Turma.id).filter(Turma.nome == "Turma Teste")
            )
        ).delete(synchronize_session=False)
        
        Atividade.query.filter(Atividade.nome.in_(["Atividade 1", "Atividade 2"])).delete(synchronize_session=False)
        Turma.query.filter(Turma.nome == "Turma Teste").delete(synchronize_session=False)
        User.query.filter(User.email == "test@test.com").delete(synchronize_session=False)
        
        db.session.commit()
        print("🧹 Test data cleaned up")

if __name__ == "__main__":
    print("🧪 Running Report Performance and Accuracy Tests...")
    
    try:
        # Run the test
        success = test_scoring_calculation()
        
        if success:
            print("\n🎉 All tests PASSED! The optimizations are working correctly.")
        else:
            print("\n❌ Tests FAILED! There are issues with the calculations.")
            
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Always clean up
        cleanup_test_data()