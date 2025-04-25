"""
Complete Database Visualization Script
This script visualizes all tables in the reservation system database,
including the many-to-many relationships between eaters and reservations.
"""
import sys
import os
from tabulate import tabulate

# Add the parent directory to the path so we can import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Color definitions for pretty terminal output
class Colors:
    """Color definitions for pretty printing."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text):
    """Print a formatted header with the given text."""
    print("\n" + Colors.BLUE + "╔" + "═" * 78 + "╗" + Colors.ENDC)
    title_line = f" {text} ".center(78)
    print(Colors.BLUE + "║" + Colors.ENDC + Colors.BOLD + Colors.CYAN + title_line + Colors.ENDC + Colors.BLUE + "║" + Colors.ENDC)
    print(Colors.BLUE + "╚" + "═" * 78 + "╝" + Colors.ENDC)

def print_table_data(data, headers, title):
    """Print data in tabular format."""
    print_header(title)
    if data:
        print(tabulate(data, headers=headers, tablefmt="grid"))
        print(Colors.GREEN + f"Total: {len(data)} records" + Colors.ENDC + "\n")
    else:
        print(Colors.YELLOW + "No data found." + Colors.ENDC)

def view_all_tables():
    """Display all database tables including complex relationships."""
    # Print title banner with color
    print("\n" + Colors.BOLD + Colors.CYAN + "╔" + "═" * 78 + "╗" + Colors.ENDC)
    print(Colors.BOLD + Colors.CYAN + "║" + Colors.ENDC + 
          Colors.BOLD + Colors.GREEN + "  📊 RESERVATION SYSTEM DATABASE VISUALIZATION 📊".center(78) + 
          Colors.ENDC + Colors.BOLD + Colors.CYAN + "║" + Colors.ENDC)
    print(Colors.BOLD + Colors.CYAN + "╚" + "═" * 78 + "╝" + Colors.ENDC)
    from app import app
    from models import (
        db, Eater, DietaryRestriction, Endorsement, Restaurant, 
        RestaurantHours, Table, Reservation, 
        eater_dietary_restrictions, restaurant_endorsements, 
        restriction_endorsement_mappings, reservation_attendees
    )
    from sqlalchemy import select, func, text
    from sqlalchemy.orm import joinedload
    
    with app.app_context():
        # View reservation attendees (which demonstrates the many-to-many relationship)
        print_header("RESERVATION ATTENDEES")
        
        # Direct query of the junction table - using SQLAlchemy's text() for raw SQL
        query = text("""
        SELECT 
            ra.reservation_id, 
            r.eater_id as host_id,
            host.name as host_name,
            res.name as restaurant_name,
            r.table_id,
            t.capacity as table_capacity,
            ra.eater_id as attendee_id, 
            e.name as attendee_name,
            r.reservation_date,
            r.reservation_start_time,
            r.reservation_end_time,
            r.party_size,
            r.is_active,
            res.average_rating
        FROM reservation_attendees ra
        JOIN reservations r ON ra.reservation_id = r.id
        JOIN eaters e ON ra.eater_id = e.id
        JOIN eaters host ON r.eater_id = host.id
        JOIN restaurants res ON r.restaurant_id = res.id
        LEFT JOIN tables t ON r.table_id = t.id
        ORDER BY ra.reservation_id
        """)
        
        result = db.session.execute(query)
        data = []
        for row in result:
            role = "Host" if row.attendee_id == row.host_id else "Attendee"
            role_colored = Colors.BOLD + Colors.GREEN + role + Colors.ENDC if role == "Host" else Colors.YELLOW + role + Colors.ENDC
            
            # Format restaurant rating with stars
            rating = float(row.average_rating) if row.average_rating else 0
            stars = "★" * int(rating) + "☆" * (5 - int(rating))
            rating_colored = Colors.YELLOW + stars + Colors.ENDC
            
            # Format time with color
            time_str = f"{row.reservation_start_time} → {row.reservation_end_time}"
            time_colored = Colors.CYAN + time_str + Colors.ENDC
            
            # Format active status with color
            active_status = "Active" if row.is_active else "Deleted"
            active_colored = Colors.GREEN + active_status + Colors.ENDC if row.is_active else Colors.RED + active_status + Colors.ENDC
            
            data.append([
                row.reservation_id,
                Colors.BOLD + row.host_name + Colors.ENDC,
                Colors.BOLD + Colors.CYAN + row.restaurant_name + Colors.ENDC,
                Colors.HEADER + f"Table #{row.table_id} ({row.table_capacity} seats)" + Colors.ENDC if row.table_id else "No table",
                row.attendee_id,
                Colors.BOLD + row.attendee_name + Colors.ENDC if row.attendee_id == row.host_id else row.attendee_name,
                role_colored,
                Colors.GREEN + str(row.reservation_date) + Colors.ENDC,
                time_colored,
                row.party_size,
                active_colored,
                rating_colored
            ])
        
        print_table_data(
            data,
            ["Res ID", "Host", "Restaurant", "Table", "Attendee ID", "Attendee Name", 
             "Role", "Date", "Time", "Party Size", "Status", "Rating"],
            "RESERVATION ATTENDEES"
        )
        
        # View all tables to show the complete database state - using SQLAlchemy's text()
        tables = [
            ("Eaters", text("SELECT id, name, email FROM eaters")),
            ("Dietary Restrictions", text("SELECT id, restriction_name FROM dietary_restrictions")),
            ("Endorsements", text("SELECT id, endorsement_name FROM endorsements")),
            ("Restaurants", text("SELECT id, name, average_rating FROM restaurants")),
            ("Tables", text("SELECT id, restaurant_id, capacity FROM tables")),
            ("Reservations", text("SELECT id, eater_id, restaurant_id, table_id, reservation_date, reservation_start_time, reservation_end_time, party_size, is_active FROM reservations"))
        ]
        
        for title, query in tables:
            result = db.session.execute(query)
            headers = result.keys()
            data = [list(row) for row in result]
            print_table_data(data, headers, title)

if __name__ == "__main__":
    try:
        view_all_tables()
        print("\n" + Colors.BOLD + Colors.GREEN + "╔" + "═" * 78 + "╗" + Colors.ENDC)
        print(Colors.BOLD + Colors.GREEN + "║" + 
            "  ✨ Database visualization completed successfully! ✨  ".center(78) + 
            Colors.BOLD + Colors.GREEN + "║" + Colors.ENDC)
        print(Colors.BOLD + Colors.GREEN + "╚" + "═" * 78 + "╝" + Colors.ENDC)
    except Exception as e:
        import traceback
        print(Colors.RED + f"\n\nERROR: {e}" + Colors.ENDC)
        print(Colors.YELLOW + "\nTraceback:" + Colors.ENDC)
        traceback.print_exc()
        sys.exit(1)
