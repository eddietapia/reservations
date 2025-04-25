"""
Database seed script to populate the database with sample data
based on the JavaScript example.
"""
import os
import sys
import subprocess
import json
import time

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now we can import from the project root
from app import app, db
from models import (
    Eater, DietaryRestriction, Endorsement, Restaurant, 
    RestaurantHours, Table, Reservation, 
    eater_dietary_restrictions, restaurant_endorsements, 
    restriction_endorsement_mappings
)
from datetime import datetime, date
from sqlalchemy.exc import IntegrityError

def seed_database():
    """Seed the database with sample data from the JavaScript example"""
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        
        print("Seeding database...")
        
        # Insert sample eaters
        eaters = [
            Eater(name='Eddie Tapia', email='eddie.tapia@example.com'),
            Eater(name='Jalen Hurts', email='jalen.hurts@example.com'),
            Eater(name='Selena Gomez', email='selena.gomez@example.com'),
            Eater(name='Rihanna', email='rihanna@example.com')
        ]
        add_to_db(eaters, "eaters")
        
        # Sample dietary restrictions
        dietary_restrictions = [
            DietaryRestriction(restriction_name='Gluten Free'),
            DietaryRestriction(restriction_name='Vegetarian'),
            DietaryRestriction(restriction_name='Paleo'),
            DietaryRestriction(restriction_name='Vegan')
        ]
        add_to_db(dietary_restrictions, "dietary restrictions")
        
        # Sample endorsements
        endorsements = [
            Endorsement(endorsement_name='Gluten Free Options'),
            Endorsement(endorsement_name='Vegetarian-Friendly'),
            Endorsement(endorsement_name='Vegan-Friendly'),
            Endorsement(endorsement_name='Paleo-friendly')
        ]
        add_to_db(endorsements, "endorsements")
        
        # Sample restaurants
        restaurants = [
            Restaurant(
                name='Tartine Bakery',
                average_rating=4.5,
                address='123 Main St',
                phone='555-1234',
                email='info@tartinebakery.com',
                website_url='http://tartinebakery.com',
                has_parking=True,
                accepts_reservations=True
            ),
            Restaurant(
                name='Tacos el Gordo',
                average_rating=4.6,
                address='456 Oak Ave',
                phone='555-5678',
                email='contact@tacoselgordo.com',
                website_url='http://tacoselgordo.com',
                has_parking=False,
                accepts_reservations=True
            ),
            Restaurant(
                name='Lardo',
                average_rating=4.1,
                address='789 Pine St',
                phone='555-9876',
                email='info@lardo.com',
                website_url='http://lardo.com',
                has_parking=True,
                accepts_reservations=True
            ),
            Restaurant(
                name='Panadería Rosetta',
                average_rating=4.3,
                address='101 Walnut St',
                phone='555-1010',
                email='info@panaderia.com',
                website_url='http://panaderia.com',
                has_parking=True,
                accepts_reservations=True
            ),
            Restaurant(
                name='Tetetlán',
                average_rating=4.4,
                address='202 Elm St',
                phone='555-2020',
                email='info@tetetlan.com',
                website_url='http://tetetlan.com',
                has_parking=True,
                accepts_reservations=True
            ),
            Restaurant(
                name='Falling Piano Brewing Co',
                average_rating=4.2,
                address='304 Oak St',
                phone='555-3040',
                email='info@fallingpiano.com',
                website_url='http://fallingpiano.com',
                has_parking=True,
                accepts_reservations=True
            ),
            Restaurant(
                name='u.to.pi.a',
                average_rating=4.5,
                address='456 Oak Ave',
                phone='555-5678',
                email='contact@utopiacafe.com',
                website_url='http://utopiacafe.com',
                has_parking=True,
                accepts_reservations=True
            )
        ]
        add_to_db(restaurants, "restaurants")
        
        # Sample restaurant hours
        from datetime import time
        
        restaurant_hours = []
        # Format: (restaurant_name, opening_hour, opening_minute, closing_hour, closing_minute)
        restaurant_hours_data = [
            ('Tartine Bakery', 8, 0, 20, 0),
            ('Tacos el Gordo', 11, 0, 22, 0),
            # For 24-hour restaurants, use 0:00 to 23:59:59
            ('Lardo', 0, 0, 23, 59),
            ('Panadería Rosetta', 0, 0, 23, 59),
            ('Tetetlán', 0, 0, 23, 59),
            ('Falling Piano Brewing Co', 0, 0, 23, 59),
            ('u.to.pi.a', 0, 0, 23, 59)
        ]
        
        for restaurant_name, open_hour, open_minute, close_hour, close_minute in restaurant_hours_data:
            restaurant = Restaurant.query.filter_by(name=restaurant_name).first()
            if restaurant:
                # Create time objects for opening and closing times
                opening_time = time(hour=open_hour, minute=open_minute)
                # For 24-hour restaurants, add seconds to make it 23:59:59
                closing_time = time(hour=close_hour, minute=close_minute, second=59 if close_hour == 23 and close_minute == 59 else 0)
                
                restaurant_hours.append(
                    RestaurantHours(
                        restaurant_id=restaurant.id,
                        opening_time=opening_time,
                        closing_time=closing_time
                    )
                )
        
        add_to_db(restaurant_hours, "restaurant hours")
        
        # Sample tables
        tables = []
        tables_data = [
            ('Tartine Bakery', [4, 4, 2, 2]),
            ('Tacos el Gordo', [6, 4, 4, 4, 4]),
            ('Lardo', [2, 2, 2, 2, 4, 4, 6]),
            ('Panadería Rosetta', [2, 2, 2, 4, 4]),
            ('Tetetlán', [2, 2, 2, 2, 4, 4, 6]),
            ('Falling Piano Brewing Co', [2, 2, 2, 2, 2, 4, 4, 4, 4, 4, 6, 6, 6, 6, 6]),
            ('u.to.pi.a', [2, 2])
        ]
        
        for restaurant_name, capacities in tables_data:
            restaurant = Restaurant.query.filter_by(name=restaurant_name).first()
            if restaurant:
                for capacity in capacities:
                    tables.append(
                        Table(
                            restaurant_id=restaurant.id,
                            capacity=capacity
                        )
                    )
        
        add_to_db(tables, "tables")
        
        # Sample eater dietary restrictions
        try:
            # Get eater and restriction IDs
            eddie = Eater.query.filter_by(email='eddie.tapia@example.com').first()
            jalen = Eater.query.filter_by(email='jalen.hurts@example.com').first()
            gluten_free = DietaryRestriction.query.filter_by(restriction_name='Gluten Free').first()
            vegetarian = DietaryRestriction.query.filter_by(restriction_name='Vegetarian').first()
            
            # Add dietary restrictions to eaters
            if eddie and gluten_free:
                eddie.dietary_restrictions.append(gluten_free)
            if jalen and vegetarian:
                jalen.dietary_restrictions.append(vegetarian)
            
            db.session.commit()
            print("Added eater dietary restrictions")
        except IntegrityError:
            db.session.rollback()
            print("Eater dietary restrictions already exist")
        
        # Sample restaurant endorsements
        endorsement_mappings = [
            ('Tartine Bakery', ['Vegetarian-Friendly', 'Gluten Free Options']),
            ('Tacos el Gordo', ['Gluten Free Options']),
            ('Lardo', ['Gluten Free Options']),
            ('Panadería Rosetta', ['Vegetarian-Friendly', 'Gluten Free Options']),
            ('Tetetlán', ['Paleo-friendly', 'Gluten Free Options']),
            ('u.to.pi.a', ['Vegetarian-Friendly', 'Vegan-Friendly'])
        ]
        
        for restaurant_name, endorsement_names in endorsement_mappings:
            restaurant = Restaurant.query.filter_by(name=restaurant_name).first()
            if restaurant:
                for endorsement_name in endorsement_names:
                    endorsement = Endorsement.query.filter_by(endorsement_name=endorsement_name).first()
                    if endorsement and endorsement not in restaurant.endorsements:
                        restaurant.endorsements.append(endorsement)
        
        try:
            db.session.commit()
            print("Added restaurant endorsements")
        except IntegrityError:
            db.session.rollback()
            print("Some restaurant endorsements already exist")
        
        # Sample restriction endorsement mappings
        mapping_data = [
            ('Gluten Free', 'Gluten Free Options'),
            ('Vegetarian', 'Vegetarian-Friendly'),
            ('Paleo', 'Paleo-friendly'),
            ('Vegan', 'Vegan-Friendly')
        ]
        
        for restriction_name, endorsement_name in mapping_data:
            restriction = DietaryRestriction.query.filter_by(restriction_name=restriction_name).first()
            endorsement = Endorsement.query.filter_by(endorsement_name=endorsement_name).first()
            
            if restriction and endorsement and endorsement not in restriction.endorsements:
                restriction.endorsements.append(endorsement)
        
        try:
            db.session.commit()
            print("Added restriction endorsement mappings")
        except IntegrityError:
            db.session.rollback()
            print("Some restriction endorsement mappings already exist")
        
        print("Database seeding completed successfully!")

def add_to_db(items, item_type):
    """Helper function to add items to the database with error handling"""
    for item in items:
        try:
            db.session.add(item)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            print(f"Item '{item}' already exists in {item_type}")
    
    print(f"Added {len(items)} {item_type}")

def create_reservations_via_api():
    """Create sample reservations by calling the API"""
    print("\nCreating sample reservations via API...")
    
    # Wait for the Flask server to be ready
    server_url = "http://localhost:5001/health"
    max_retries = 5
    retry_delay = 1
    
    for i in range(max_retries):
        try:
            result = subprocess.run(["curl", "-s", server_url], capture_output=True, text=True)
            if result.returncode == 0:
                print("Flask server is ready.")
                break
        except Exception as e:
            print(f"Error checking server: {e}")
        
        if i < max_retries - 1:
            print(f"Waiting for Flask server to be ready... (attempt {i+1}/{max_retries})")
            time.sleep(retry_delay)
        else:
            print("Warning: Could not connect to Flask server. Reservations may not be created.")
            return
    
    # Create first reservation
    print("\nCreating first reservation...")
    reservation1 = {
        "eater_id": 1,
        "restaurant_id": 1,
        "date": "2025-05-15",  # Using a future date to avoid conflicts
        "time": "18:00",
        "guests_count": 2
    }
    
    try:
        cmd = ["curl", "-s", "-X", "POST", "-H", "Content-Type: application/json", 
               "-d", json.dumps(reservation1), "http://localhost:5001/api/reserve"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            try:
                response = json.loads(result.stdout)
                if response.get("status") == "success":
                    print("✅ First reservation created successfully")
                else:
                    print(f"❌ API Error: {response.get('message', 'Unknown error')}")
            except json.JSONDecodeError:
                print(f"❌ Error parsing API response: {result.stdout}")
        else:
            print(f"❌ Error making API request: {result.stderr}")
    except Exception as e:
        print(f"❌ Exception during API call: {str(e)}")
    
    # Create second reservation
    print("\nCreating second reservation...")
    reservation2 = {
        "eater_id": 4,
        "restaurant_id": 3,
        "date": "2025-06-20",  # Using a different future date
        "time": "19:00",
        "attendee_ids": [2, 3],
        "guests_count": 0
    }
    
    try:
        cmd = ["curl", "-s", "-X", "POST", "-H", "Content-Type: application/json", 
               "-d", json.dumps(reservation2), "http://localhost:5001/api/reserve"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            try:
                response = json.loads(result.stdout)
                if response.get("status") == "success":
                    print("✅ Second reservation created successfully")
                else:
                    print(f"❌ API Error: {response.get('message', 'Unknown error')}")
            except json.JSONDecodeError:
                print(f"❌ Error parsing API response: {result.stdout}")
        else:
            print(f"❌ Error making API request: {result.stderr}")
    except Exception as e:
        print(f"❌ Exception during API call: {str(e)}")

if __name__ == '__main__':
    seed_database()
    create_reservations_via_api()
