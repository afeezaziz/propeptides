from app import app
from models import db

def init_database():
    """Initialize the database with all tables"""
    with app.app_context():
        # Create all tables
        db.create_all()
        print("Database tables created successfully!")

        # Verify tables were created
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"Tables in database: {tables}")

if __name__ == "__main__":
    init_database()