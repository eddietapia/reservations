from config import config
from datetime import datetime
from flask import Flask, jsonify, render_template, request
from flask_migrate import Migrate
from helpers.availabilityHelpers import find_available_restaurants
from helpers.reservationHelpers import create_reservation, delete_reservation, get_reservation_details
from models import db, Eater, Reservation
import os

# Create Flask app and configure based on environment.
def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions.
    db.init_app(app)
    Migrate(app, db)
    
    return app

app = create_app(os.environ.get('FLASK_ENV', 'development'))

# Context processor to inject variables into all templates.
@app.context_processor
def inject_year():
    return {'year': datetime.now().year}

# Initialize database tables within app context.
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    reservations = Reservation.query.order_by(Reservation.created_at.desc()).limit(3).all()
    return render_template('index.html', reservations=reservations)

@app.route('/api/restaurants/available', methods=['GET'])
def get_available_restaurants_api():
    """Get a list of available restaurants for a group of users at a specific time"""
    # Get the time the users want to make a reservation.
    reservation_time = request.args.get('time', type=str)
    if not reservation_time:
        return jsonify({
            'status': 'error',
            'message': 'Reservation time is required'
        }), 400
        
    # Get the date for the reservation (optional)
    reservation_date = request.args.get('date', type=str)
        
    # Get eater IDs from query parameters.
    eater_ids = request.args.getlist('eater_id', type=int)
    if not eater_ids:
        return jsonify({
            'status': 'error',
            'message': 'At least one eater ID is required'
        }), 400
    
    # Get eater objects
    eaters = Eater.query.filter(Eater.id.in_(eater_ids)).all()
    if not eaters or len(eaters) != len(eater_ids):
        return jsonify({
            'status': 'error',
            'message': 'One or more eaters not found'
        }), 404
    
    # Get additional guests parameter (optional)
    additional_guests = request.args.get('additional_guests', type=int, default=0)
    
    # Use helper function to find available restaurants
    available_restaurants = find_available_restaurants(
        reservation_time=reservation_time, 
        eaters=eaters,
        reservation_date=reservation_date,
        additional_guests=additional_guests
    )
    
    # Format response
    restaurants_data = [{
        'id': restaurant.id,
        'name': restaurant.name,
        'average_rating': restaurant.average_rating,
        'address': restaurant.address,
        'phone': restaurant.phone,
        'hours': {
            'opening': restaurant.hours.opening_time.strftime('%H:%M') if restaurant.hours and restaurant.hours.opening_time else None,
            'closing': restaurant.hours.closing_time.strftime('%H:%M') if restaurant.hours and restaurant.hours.closing_time else None
        },
        'endorsements': [{
            'id': endorsement.id,
            'name': endorsement.endorsement_name
        } for endorsement in restaurant.endorsements],
        'has_parking': restaurant.has_parking,
        'accepts_reservations': restaurant.accepts_reservations
    } for restaurant in available_restaurants]
    
    return jsonify({
        'status': 'success',
        'count': len(restaurants_data),
        'restaurants': restaurants_data
    })

@app.route('/api/reserve', methods=['POST'])
def create_reservation_api():
    """Create a new reservation for a group of users at a specific time"""
    data = request.json
    
    # Validate required fields
    required_fields = ['eater_id', 'restaurant_id', 'date', 'time']
    for field in required_fields:
        if field not in data:
            return jsonify({
                'status': 'error',
                'message': f'Missing required field: {field}'
            }), 400
    
    # Get optional fields
    attendee_ids = data.get('attendee_ids', [])
    guests_count = data.get('guests_count', 0)
    
    success, message, reservation = create_reservation(
        eater_id=data['eater_id'],
        restaurant_id=data['restaurant_id'],
        reservation_date=data['date'],
        reservation_start_time=data['time'],
        attendee_ids=attendee_ids,
        guests_count=guests_count
    )
    
    if not success:
        return jsonify({
            'status': 'error',
            'message': message
        }), 400
    
    # Format response
    # Get attendee data
    attendees_data = [{
        'id': attendee.id,
        'name': attendee.name,
        'email': attendee.email
    } for attendee in reservation.attendees]
    
    reservation_data = {
        'id': reservation.id,
        'host_id': reservation.eater_id,
        'host_name': reservation.host.name,
        'restaurant_id': reservation.restaurant_id,
        'restaurant_name': reservation.restaurant.name,
        'table_id': reservation.table_id,
        'date': reservation.reservation_date.strftime('%Y-%m-%d'),
        'start_time': reservation.reservation_start_time,
        'end_time': reservation.reservation_end_time,
        'party_size': reservation.party_size,
        'attendees': attendees_data,
        'created_at': reservation.created_at.isoformat() if reservation.created_at else None
    }
    
    return jsonify({
        'status': 'success',
        'message': message,
        'reservation': reservation_data
    })

@app.route('/api/reservations/<int:reservation_id>', methods=['GET'])
def get_reservation_api(reservation_id):
    """Get details for a reservation
    
    Query Parameters:
        include_inactive: If set to 'true', returns details even for soft-deleted reservations
    """
    include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
    
    reservation_details = get_reservation_details(reservation_id, include_inactive=include_inactive)
    
    if not reservation_details:
        return jsonify({
            'status': 'error',
            'message': 'Reservation not found'
        }), 404
    
    return jsonify({
        'status': 'success',
        'reservation': reservation_details
    })


@app.route('/api/reservations/<int:reservation_id>', methods=['DELETE'])
def delete_reservation_api(reservation_id):
    """Deletes a reservation for a user
    
    Query Parameters:
        soft_delete: If set to 'true', performs a soft deletion instead of hard deletion
    """
    # Check if soft delete is requested
    soft_delete = request.args.get('soft_delete', 'false').lower() == 'true'
    
    success, message = delete_reservation(reservation_id, soft_delete=soft_delete)
    
    if not success:
        return jsonify({
            'status': 'error',
            'message': message
        }), 404
    
    return jsonify({
        'status': 'success',
        'message': message,
        'deletion_type': 'soft' if soft_delete else 'hard'
    })

if __name__ == '__main__':
    app.run(debug=True, port=5001)
