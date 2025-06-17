from flask import Flask
import os
from config import Config
from models import db, User

def setup():
    print("Setting up application...")
    
    # Create Flask app
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize SQLAlchemy with the app
    db.init_app(app)
    
    # Ensure database directory exists
    os.makedirs(os.path.dirname(app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')), exist_ok=True)
    
    # Ensure session directory exists
    session_dir = os.path.join(app.instance_path, 'flask_session')
    os.makedirs(session_dir, exist_ok=True)
    
    # Create all tables and initialize admin user
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")
        
        try:
            # Check if admin user exists
            admin = User.query.filter_by(username='admin').first()
            
            if not admin:
                # Create admin user
                admin = User(
                    username='admin',
                    email='admin@example.com',
                    role='admin',
                    is_admin=True
                )
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                print("Admin user created successfully!")
            else:
                print("Admin user already exists.")
                
        except Exception as e:
            print(f"Error during setup: {str(e)}")
            raise

if __name__ == '__main__':
    setup() 