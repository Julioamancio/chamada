from app import db, criar_etapas, app

if __name__ == "__main__":
    with app.app_context():
        print("🛠️ Criando tabelas no banco de dados...")
        db.create_all()
        print("✅ Tabelas criadas com sucesso!")
        criar_etapas()
        print("✅ Etapas padrão inseridas!")
        print("🎉 Banco de dados pronto para uso!")
