
from typing import List, Optional
from datetime import datetime, date, time, timedelta
from models import Eater, Restaurant, RestaurantHours, DietaryRestriction, Table, Reservation
from models import db, Endorsement, restaurant_endorsements, restriction_endorsement_mappings
from sqlalchemy import func, and_, or_

# --- Helper Functions for find_available_restaurants (sorted alphabetically) ---

def aggregate_dietary_restrictions(eaters: List[Eater]) -> set:
    """Aggregate all unique dietary restriction IDs from eaters."""
    restrictions = set()
    for eater in eaters:
        for restriction in eater.dietary_restrictions:
            restrictions.add(restriction.id)
    return restrictions


def get_potential_restaurants(reservation_time: str, restrictions: set) -> List[Restaurant]:
    """Query restaurants open at the given time, filtered by dietary restrictions if any."""     
    # Convert reservation_time string to a time object
    try:
        res_time = datetime.strptime(reservation_time, "%H:%M").time()
    except ValueError:
        try:
            res_time = datetime.strptime(reservation_time, "%H:%M:%S").time()
        except ValueError:
            # If all parsing fails, return empty list
            return []
    if not restrictions:
        return Restaurant.query.filter(
            Restaurant.accepts_reservations == True
        ).join(RestaurantHours, Restaurant.id == RestaurantHours.restaurant_id).filter(
            RestaurantHours.opening_time <= res_time,
            RestaurantHours.closing_time >= res_time
        ).all()

    # If we have dietary restrictions find the matching endorsements.
    matching_endorsements = db.session.query(Endorsement.id).join(
        restriction_endorsement_mappings,
        and_(
            restriction_endorsement_mappings.c.endorsement_id == Endorsement.id,
            restriction_endorsement_mappings.c.restriction_id.in_(restrictions)
        )
    ).all()
    matching_endorsement_ids = [endorsement[0] for endorsement in matching_endorsements]
    restaurant_counts = db.session.query(
        restaurant_endorsements.c.restaurant_id,
        func.count(restaurant_endorsements.c.endorsement_id).label('endorsement_count')
    ).filter(
        restaurant_endorsements.c.endorsement_id.in_(matching_endorsement_ids)
    ).group_by(
        restaurant_endorsements.c.restaurant_id
    ).having(
        # Ensure the restaurant has at least all the required endorsements.
        func.count(restaurant_endorsements.c.endorsement_id) >= len(matching_endorsement_ids)
    ).subquery()
    return Restaurant.query.join(
        restaurant_counts,
        Restaurant.id == restaurant_counts.c.restaurant_id
    ).filter(
        Restaurant.accepts_reservations == True
    ).join(RestaurantHours, Restaurant.id == RestaurantHours.restaurant_id).filter(
        RestaurantHours.opening_time <= res_time,
        RestaurantHours.closing_time >= res_time
    ).all()


def get_reservation_end_time(reservation_time: str, date_obj: date, duration: timedelta) -> str:
    """Compute the end time string (HH:MM) for a reservation, fallback to +2h if parsing fails."""
    try:
        start_datetime = datetime.combine(date_obj, datetime.strptime(reservation_time, "%H:%M").time())
        end_datetime = start_datetime + duration
        return end_datetime.strftime("%H:%M")
    except ValueError:
        try:
            time_parts = reservation_time.split(':')
            hour = int(time_parts[0])
            minute = int(time_parts[1]) if len(time_parts) > 1 else 0
            end_hour = (hour + 2) % 24
            return f"{end_hour:02d}:{minute:02d}"
        except (ValueError, IndexError):
            # Fallback to using the current time + duration
            now = datetime.now()
            start_datetime = datetime.combine(date_obj, now.time())
            end_datetime = start_datetime + duration
            return end_datetime.strftime("%H:%M")


def is_time_available_for_reservation(restaurant: Restaurant, date_obj: date, start_time: str, end_time: str, num_of_eaters: int) -> bool:
    """Check if there is a suitable table available for the group in the time window.
    
    Args:
        restaurant: Restaurant object
        date_obj: Date to check
        start_time: Start time of reservation (HH:MM)
        end_time: End time of reservation (HH:MM)
        num_of_eaters: Number of people in the party
        
    Returns:
        Boolean indicating if there are suitable tables available
    """
    # Find tables that can accommodate the party size.
    suitable_tables = Table.query.filter(
        Table.restaurant_id == restaurant.id,
        Table.capacity >= num_of_eaters
    ).all()
    
    if not suitable_tables:
        return False
        
    suitable_table_ids = [table.id for table in suitable_tables]
    
    # Find all active reservations that would conflict with our time window
    # A conflict exists if: start_time < other.end_time AND end_time > other.start_time
    conflicting_reservations = Reservation.query.filter(
        Reservation.restaurant_id == restaurant.id,
        Reservation.table_id.in_(suitable_table_ids),
        Reservation.reservation_date == date_obj,
        Reservation.reservation_end_time > start_time,
        Reservation.reservation_start_time < end_time,
        Reservation.is_active == True  # Only consider active reservations
    ).all()
    
    # Get IDs of tables that already have bookings in our time window
    reserved_table_ids = set(r.table_id for r in conflicting_reservations)
    
    # Count tables that are available during our time window
    available_tables_count = len([t for t in suitable_tables if t.id not in reserved_table_ids])
    
    return available_tables_count > 0


def parse_reservation_date(reservation_date: Optional[str]) -> date:
    """Parse a date string in YYYY-MM-DD format, fallback to today on error or None."""
    if reservation_date:
        try:
            return datetime.strptime(reservation_date, "%Y-%m-%d").date()
        except ValueError:
            return date.today()
    return date.today()


def restaurant_has_table_for_group(restaurant: Restaurant, group_size: int) -> bool:
    """Check if the restaurant has at least one table that fits the group size."""
    return Table.query.filter(
        Table.restaurant_id == restaurant.id,
        Table.capacity >= group_size
    ).first() is not None


def find_available_restaurants(
    reservation_time: str,
    eaters: List[Eater],
    reservation_date: str = None,
    duration: timedelta = timedelta(hours=2),
    additional_guests: int = 0
) -> List[Restaurant]:
    """
    Get a list of available restaurants for a group of users at a specific time.
    
    Args:
        reservation_time: Time for reservation in format HH:MM
        eaters: List of registered Eater objects who will attend
        reservation_date: Date for reservation in format YYYY-MM-DD, defaults to today
        duration: Duration of the reservation, defaults to 2 hours
        additional_guests: Number of additional guests without accounts, defaults to 0
    
    Returns:
        List of available Restaurant objects
    """
    # Calculate total party size (registered eaters + additional guests)
    registered_eaters = len(eaters)
    total_party_size = registered_eaters + additional_guests
    
    reservation_date = parse_reservation_date(reservation_date)
    restrictions = aggregate_dietary_restrictions(eaters)
    potential_restaurants = get_potential_restaurants(reservation_time, restrictions)
    available_restaurants = []
    end_time = get_reservation_end_time(reservation_time, reservation_date, duration)
    
    for restaurant in potential_restaurants:
        if not restaurant_has_table_for_group(restaurant, total_party_size):
            continue
        if is_time_available_for_reservation(restaurant, reservation_date, reservation_time, end_time, total_party_size):
            available_restaurants.append(restaurant)
    return available_restaurants
