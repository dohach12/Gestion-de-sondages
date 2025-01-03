from app import app, db
from models import User

def init_db():
    with app.app_context():
        # Supprime toutes les tables existantes
        db.drop_all()
        
        # Crée toutes les tables
        db.create_all()
        
        # Crée un utilisateur admin
        admin = User(
            username='admin',
            email='admin@example.com',
            role='admin'
        )
        admin.password = 'admin123'  # Dans un environnement de production, utilisez un mot de passe plus sécurisé
        
        # Ajoute l'admin à la base de données
        db.session.add(admin)
        db.session.commit()
        
        print("Base de données initialisée avec succès!")

if __name__ == '__main__':
    init_db() 