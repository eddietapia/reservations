from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, date, time, timedelta
from typing import Tuple, Optional
from models import db, Reservation, Restaurant, Table, Eater
from sqlalchemy import and_, func


#################################
# Validation Helper Functions   #
#################################

def validate_restaurant(restaurant_id: int) -> Tuple[bool, str, Optional[Restaurant]]:
    """Validate a restaurant exists and accepts reservations
    
    Args:
        restaurant_id: ID of the restaurant to validate
    
    Returns:
        Tuple of (success, error_message, restaurant_object)
    """
    restaurant = Restaurant.query.get(restaurant_id)
    if not restaurant:
        return False, "Restaurant not found", None
        
    if not restaurant.accepts_reservations:
        return False, "Restaurant does not accept reservations", None
        
    return True, "", restaurant


def validate_host(eater_id: int) -> Tuple[bool, str, Optional[Eater]]:
    """Validate the eater exists
    
    Args:
        eater_id: ID of the eater to validate
    
    Returns:
        Tuple of (success, error_message, eater_object)
    """
    eater = Eater.query.get(eater_id)
    if not eater:
        return False, f"Eater with ID {eater_id} not found", None
    return True, "", eater
    

def check_eater_availability(eater_id: int, date_obj: datetime.date, start_time: str, end_time: str) -> Tuple[bool, str]:
    """Check if an eater already has a reservation at any restaurant during the specified time window
    
    Args:
        eater_id: ID of the eater to check
        date_obj: Date object for the reservation
        start_time: Start time of reservation (HH:MM)
        end_time: End time of reservation (HH:MM)
    
    Returns:
        Tuple of (is_available, error_message)
    """
    # Convert string times to time objects for comparison
    success, error_msg, req_start = parse_time_string(start_time)
    if not success:
        return False, error_msg
        
    success, error_msg, req_end = parse_time_string(end_time)
    if not success:
        return False, error_msg
    
    # Find all active reservations for this eater on the given date
    # This includes both reservations where the eater is the host and where they are an attendee
    host_reservations = Reservation.query.filter(
        Reservation.eater_id == eater_id,
        Reservation.reservation_date == date_obj,
        Reservation.is_active == True
    ).all()
    
    # Also check active reservations where the eater is an attendee but not the host
    # We need to query through the many-to-many relationship
    attending_reservations = Reservation.query.join(Reservation.attendees).filter(
        Eater.id == eater_id,
        Reservation.reservation_date == date_obj,
        Reservation.is_active == True
    ).all()
    
    # Combine both sets of reservations.
    all_eater_reservations = list(set(host_reservations + attending_reservations))
    
    # Check for overlaps
    for reservation in all_eater_reservations:
        # Convert reservation times to time objects
        success, _, res_start = parse_time_string(reservation.reservation_start_time)
        success2, _, res_end = parse_time_string(reservation.reservation_end_time)
        
        # Skip this reservation if we can't parse the times
        if not success or not success2:
            continue
        
        # Check if there's an overlap using the standard overlap formula:
        # start1 < end2 AND end1 > start2
        if req_start < res_end and req_end > res_start:
            restaurant = Restaurant.query.get(reservation.restaurant_id)
            restaurant_name = restaurant.name if restaurant else f"Restaurant ID {reservation.restaurant_id}"
            return False, f"You already have a reservation at {restaurant_name} from {reservation.reservation_start_time} to {reservation.reservation_end_time} on this date."
    
    return True, ""


def validate_attendees(attendee_ids: List[int]) -> Tuple[bool, str, List[Eater]]:
    """Validate all attendees exist
    
    Args:
        attendee_ids: List of eater IDs to validate
    
    Returns:
        Tuple of (success, error_message, list_of_eaters)
    """
    attendees = []
    if not attendee_ids:
        return True, "", attendees
        
    for attendee_id in attendee_ids:
        attendee = Eater.query.get(attendee_id)
        if not attendee:
            return False, f"Attendee with ID {attendee_id} not found", []
        attendees.append(attendee)
    
    return True, "", attendees


def validate_reservation_time(
    restaurant: Restaurant,
    reservation_date: str,
    reservation_start_time: str
) -> Tuple[bool, str, Optional[datetime.date]]:
    """Validate the reservation date and time
    
    Args:
        restaurant: Restaurant object
        reservation_date: Date of reservation in YYYY-MM-DD format
        reservation_start_time: Start time of reservation (HH:MM)
    
    Returns:
        Tuple of (success, error_message, date_object)
    """
    # Convert date string to date object
    try:
        date_obj = datetime.strptime(reservation_date, "%Y-%m-%d").date()
    except ValueError:
        return False, "Invalid date format. Use YYYY-MM-DD", None
        
    restaurant_hours = restaurant.hours
    if not restaurant_hours:
        return False, "Restaurant hours not available", None
    
    # Convert reservation_start_time string to time object for comparison
    success, error_msg, reservation_time_obj = parse_time_string(reservation_start_time)
    if not success:
        return False, error_msg, None
        
    # Now compare the time objects
    if restaurant_hours.opening_time > reservation_time_obj or restaurant_hours.closing_time < reservation_time_obj:
        return False, f"Restaurant is not open at {reservation_start_time}", None
        
    return True, "", date_obj


#################################
# Helper Functions              #
#################################

def parse_time_string(time_str: str) -> Tuple[bool, str, Optional[time]]:
    """Convert a time string to a time object.
    
    Supports multiple formats:
    - HH:MM (e.g., "19:30")
    - H:MM (e.g., "9:30")
    - Just hours (e.g., "19" or "9")
    
    Args:
        time_str: Time string to parse
        
    Returns:
        Tuple of (success, error_message, time_object)
        If successful, error_message will be empty and time_object will be populated
        If unsuccessful, success will be False, error_message will explain the issue, and time_object will be None
    """
    if not time_str:
        return False, "Time string cannot be empty", None
        
    try:
        # Handle format with just hours
        if ":" not in time_str:
            hours = int(time_str)
            return True, "", time(hours, 0)
            
        # Handle HH:MM format
        time_parts = time_str.split(':')
        hours = int(time_parts[0])
        minutes = int(time_parts[1]) if len(time_parts) > 1 else 0
        
        # Validate hours and minutes
        if hours < 0 or hours > 23:
            return False, f"Invalid hours value: {hours}. Must be between 0-23.", None
        if minutes < 0 or minutes > 59:
            return False, f"Invalid minutes value: {minutes}. Must be between 0-59.", None
            
        return True, "", time(hours, minutes)
    except (ValueError, IndexError) as e:
        return False, f"Invalid time format: {time_str}. Use HH:MM format. Error: {str(e)}", None


#################################
# Business Logic Functions      #
#################################

def calculate_end_time(start_time: str, duration_hours: int = 2) -> str:
    """Calculate the end time given a start time and duration
    
    Args:
        start_time: Start time in format 'HH:MM'
        duration_hours: Duration in hours (default: 2)
        
    Returns:
        End time in format 'HH:MM'
    """
    try:
        time_parts = start_time.split(':')
        hour = int(time_parts[0])
        minute = int(time_parts[1]) if len(time_parts) > 1 else 0
        end_hour = (hour + duration_hours) % 24
        return f"{end_hour:02d}:{minute:02d}"
    except (ValueError, IndexError):
        # Fallback
        now = datetime.now()
        hour = now.hour
        minute = now.minute
        end_hour = (hour + duration_hours) % 24
        return f"{end_hour:02d}:{minute:02d}"


def check_table_availability(restaurant_id: int, party_size: int, date_obj: datetime.date, start_time: str, end_time: Optional[str] = None) -> Tuple[bool, str, Optional[Table]]:
    """Check table availability and find a suitable table for the given time range
    
    Args:
        restaurant_id: ID of the restaurant
        party_size: Number of people in the party
        date_obj: Date object for the reservation
        start_time: Start time of reservation (HH:MM)
        end_time: End time of reservation (HH:MM), calculated from start if None
        
    Returns:
        Tuple of (success, error_message, table_object)
        If no table is available, table_object will be None
    """
    # Calculate end_time if not provided (default 2 hour reservation)
    if not end_time:
        end_time = calculate_end_time(start_time)
    
    # Find tables that can accommodate the party size
    # Sort by capacity in ascending order to minimize under-seating.
    suitable_tables = Table.query.filter(
        Table.restaurant_id == restaurant_id,
        Table.capacity >= party_size
    ).order_by(Table.capacity).all()
    
    if not suitable_tables:
        return False, "No tables available for that party size", None
    
    # Get all reservations that overlap with our time window
    # For proper comparison, we need to ensure we're comparing the same type of values
    # A conflict exists if: start_time < other.end_time AND end_time > other.start_time
    
    # Query for all active reservations on that date at that restaurant
    day_reservations = Reservation.query.filter(
        Reservation.restaurant_id == restaurant_id,
        Reservation.reservation_date == date_obj,
        Reservation.is_active == True  # Only consider active reservations
    ).all()
    
    # Convert request times to time objects
    success, error_msg, req_start = parse_time_string(start_time)
    if not success:
        return False, error_msg, None
        
    success, error_msg, req_end = parse_time_string(end_time)
    if not success:
        return False, error_msg, None
    
    # Manually filter for time overlaps to ensure proper comparison
    conflicting_reservations = []
    for res in day_reservations:
        # Convert reservation times to time objects
        success1, _, res_start = parse_time_string(res.reservation_start_time)
        success2, _, res_end = parse_time_string(res.reservation_end_time)
        
        # Skip this reservation if we can't parse the times
        if not success1 or not success2:
            continue
        
        # Check for overlap: start1 < end2 AND end1 > start2
        if req_start < res_end and req_end > res_start:
            conflicting_reservations.append(res)
    
    # Get IDs of tables that already have bookings in our time window
    reserved_table_ids = set(r.table_id for r in conflicting_reservations)
    
    # Find tables that are available during our time window
    available_tables = [t for t in suitable_tables if t.id not in reserved_table_ids]
    
    if not available_tables:
        return False, "No tables available for that party size at the requested time", None
    
    # Return the smallest available table that can fit the party
    smallest_table = min(available_tables, key=lambda t: t.capacity)
    return True, "", smallest_table


def find_available_table(restaurant_id: int, party_size: int, date_obj: datetime.date, reservation_start_time: str) -> Tuple[bool, str, Optional[Table]]:
    """Find an available table for the reservation
    
    Args:
        restaurant_id: ID of the restaurant
        party_size: Number of people in the party
        date_obj: Date object for the reservation
        reservation_start_time: Start time of reservation (HH:MM)
    
    Returns:
        Tuple of (success, error_message, table_object)
    """
    # Calculate end time (default 2 hours after start)
    end_time = calculate_end_time(reservation_start_time)
    
    # Use the unified check_table_availability function
    return check_table_availability(
        restaurant_id=restaurant_id,
        party_size=party_size,
        date_obj=date_obj,
        start_time=reservation_start_time,
        end_time=end_time
    )


def create_reservation_object(
    eater_id: int,
    restaurant_id: int,
    table_id: int,
    date_obj: datetime.date,
    reservation_start_time: str,
    party_size: int,
    host: Eater,
    attendees: List[Eater],
    reservation_end_time: Optional[str] = None
) -> Reservation:
    """Create a reservation object and add attendees
    
    Args:
        eater_id: ID of the host eater
        restaurant_id: ID of the restaurant
        table_id: ID of the reserved table
        date_obj: Date object for the reservation
        reservation_start_time: Start time of reservation
        party_size: Number of people in the party
        host: Host eater object
        attendees: List of attendee eater objects
        reservation_end_time: End time of reservation, calculated if None
    
    Returns:
        Newly created reservation object
    """
    # Calculate end time if not provided (default 2 hour reservation)
    if not reservation_end_time:
        reservation_end_time = calculate_end_time(reservation_start_time)
        
    # Create the reservation
    new_reservation = Reservation(
        eater_id=eater_id,
        restaurant_id=restaurant_id,
        table_id=table_id,
        reservation_date=date_obj,
        reservation_start_time=reservation_start_time,
        reservation_end_time=reservation_end_time,
        party_size=party_size,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    # Add host and attendees to the reservation_attendees table
    # First add the host as an attendee
    new_reservation.attendees.append(host)
    
    # Then add any additional attendees
    if attendees:
        for attendee in attendees:
            if attendee.id != host.id:  # Avoid duplicating the host
                new_reservation.attendees.append(attendee)
                
    return new_reservation


######################################
# Main Functions - Primary API Calls #
######################################

def create_reservation(
    eater_id: int, 
    restaurant_id: int, 
    reservation_date: str,
    reservation_start_time: str, 
    attendee_ids: Optional[List[int]] = None,
    guests_count: int = 0
) -> Tuple[bool, str, Optional[Reservation]]:
    """Create a new reservation
    
    Args:
        eater_id: ID of the eater making the reservation (host)
        restaurant_id: ID of the restaurant
        reservation_date: Date of reservation in YYYY-MM-DD format
        reservation_start_time: Start time of reservation (HH:MM)
        attendee_ids: List of eater IDs who will attend the reservation
        guests_count: Number of additional unnamed guests (not in the system)
        
    Returns:
        Tuple of (success, message, reservation_object)
    """
    # Step 1: Validate restaurant.
    success, message, restaurant = validate_restaurant(restaurant_id)
    if not success:
        return False, message, None
    
    # Step 2: Validate host.
    success, message, host = validate_host(eater_id)
    if not success:
        return False, message, None
    
    # Step 3: Validate attendees.
    attendee_ids = attendee_ids or []
    success, message, attendees = validate_attendees(attendee_ids)
    if not success:
        return False, message, None
    
    # Step 4: Calculate party size - make sure host is included in the count
    # We need to add the host to the attendees count if they're not already in the list
    # This ensures the host is always counted in the party size,
    host_included = host in attendees
    party_size = (len(attendees) + (0 if host_included else 1)) + guests_count
    
    # Step 5: Validate reservation time.
    success, message, date_obj = validate_reservation_time(restaurant, reservation_date, reservation_start_time)
    if not success:
        return False, message, None
        
    # Step 6: Calculate reservation end time (we need it for availability check)
    end_time = calculate_end_time(reservation_start_time)
    
    # Step 7: Check if the host is already booked at another restaurant during this time
    success, message = check_eater_availability(eater_id, date_obj, reservation_start_time, end_time)
    if not success:
        return False, message, None
        
    # Step 8: Check if any attendees are already booked elsewhere during this time.
    for attendee in attendees:
        if attendee.id != eater_id:  # Skip host as we already checked
            success, message = check_eater_availability(attendee.id, date_obj, reservation_start_time, end_time)
            if not success:
                return False, f"Attendee {attendee.name}: {message}", None
    
    # Step 9: Find available table
    success, message, available_table = find_available_table(restaurant_id, party_size, date_obj, reservation_start_time)
    if not success:
        return False, message, None
    
    # Step 10: Create reservation object
    new_reservation = create_reservation_object(
        eater_id=eater_id,
        restaurant_id=restaurant_id,
        table_id=available_table.id,
        date_obj=date_obj,
        reservation_start_time=reservation_start_time,
        reservation_end_time=end_time,
        party_size=party_size,
        host=host,
        attendees=attendees
    )
    
    # Step 8: Save to database
    try:
        db.session.add(new_reservation)
        db.session.commit()
        return True, "Reservation created successfully", new_reservation
    except Exception as e:
        db.session.rollback()
        return False, f"Error creating reservation: {str(e)}", None


def delete_reservation(reservation_id: int, soft_delete: bool = False) -> Tuple[bool, str]:
    """Delete a reservation
    
    Args:
        reservation_id: ID of the reservation to delete
        soft_delete: If True, marks the reservation as inactive instead of actually deleting it
        
    Returns:
        Tuple of (success, message)
    """
    reservation = Reservation.query.get(reservation_id)
    if not reservation:
        return False, "Reservation not found"
    
    try:
        if soft_delete:
            # Soft delete - just mark as inactive
            reservation.is_active = False
            db.session.commit()
            return True, "Reservation marked as deleted"
        else:
            # Hard delete - remove from database
            db.session.delete(reservation)
            db.session.commit()
            return True, "Reservation permanently deleted"
    except Exception as e:
        db.session.rollback()
        return False, f"Error deleting reservation: {str(e)}"


def get_reservation_details(reservation_id: int, include_inactive: bool = False) -> Optional[Dict[str, Any]]:
    """Get details of a reservation
    
    Args:
        reservation_id: ID of the reservation
        include_inactive: If True, returns details even if reservation is soft-deleted
        
    Returns:
        Dictionary with reservation details or None if not found
    """
    reservation = Reservation.query.get(reservation_id)
    if not reservation or (not include_inactive and not reservation.is_active):
        return None
        
    return {
        "id": reservation.id,
        "host_id": reservation.eater_id,
        "host_name": reservation.host.name,
        "restaurant": {
            "id": reservation.restaurant.id,
            "name": reservation.restaurant.name
        },
        "table_id": reservation.table_id,
        "date": reservation.reservation_date.strftime("%Y-%m-%d"),
        "start_time": reservation.reservation_start_time,
        "end_time": reservation.reservation_end_time,
        "party_size": reservation.party_size,
        "is_active": reservation.is_active,
        "created_at": reservation.created_at.isoformat() if reservation.created_at else None,
        "attendees": [
            {
                "id": attendee.id,
                "name": attendee.name,
                "email": attendee.email
            } for attendee in reservation.attendees
        ]
    }
