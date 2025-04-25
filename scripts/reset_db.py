"""
Reset and seed the database with sample data
"""
import os
import sys

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now we can import from the project root
from app import app, db
from models import (
    Eater, DietaryRestriction, Endorsement, Restaurant, 
    RestaurantHours, Table, Reservation
)

def reset_database():
    """Drop all tables and recreate the database schema"""
    with app.app_context():
        print("Dropping all tables...")
        db.drop_all()
        
        print("Creating all tables with new schema...")
        db.create_all()
        
        print("Database reset successful!")

if __name__ == '__main__':
    # Make sure SQLite db file is gone
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dev.db')
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            print(f"Removed existing database file: {db_path}")
        except Exception as e:
            print(f"Failed to remove database file: {e}")
    
    reset_database()
