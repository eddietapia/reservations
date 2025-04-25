from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Initialize SQLAlchemy
db = SQLAlchemy()

# Association tables for many-to-many relationships
eater_dietary_restrictions = db.Table(
    'eater_dietary_restrictions',
    db.Column('eater_id', db.Integer, db.ForeignKey('eaters.id'), primary_key=True),
    db.Column('restriction_id', db.Integer, db.ForeignKey('dietary_restrictions.id'), primary_key=True)
)

restaurant_endorsements = db.Table(
    'restaurant_endorsements',
    db.Column('restaurant_id', db.Integer, db.ForeignKey('restaurants.id'), primary_key=True),
    db.Column('endorsement_id', db.Integer, db.ForeignKey('endorsements.id'), primary_key=True)
)

restriction_endorsement_mappings = db.Table(
    'restriction_endorsement_mappings',
    db.Column('restriction_id', db.Integer, db.ForeignKey('dietary_restrictions.id'), primary_key=True),
    db.Column('endorsement_id', db.Integer, db.ForeignKey('endorsements.id'), primary_key=True)
)

# Junction table for reservation attendees
reservation_attendees = db.Table(
    'reservation_attendees',
    db.Column('reservation_id', db.Integer, db.ForeignKey('reservations.id'), primary_key=True),
    db.Column('eater_id', db.Integer, db.ForeignKey('eaters.id'), primary_key=True)
)

class Eater(db.Model):
    """Eater model for customers."""
    __tablename__ = 'eaters'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    dietary_restrictions = db.relationship('DietaryRestriction', secondary=eater_dietary_restrictions,
                                         backref=db.backref('eaters', lazy='dynamic'))
    # The reservations where this eater is the host (creator)
    reservations = db.relationship('Reservation', back_populates='host', cascade='all, delete-orphan')
    # Reservations this eater is attending (may or may not be the primary contact)
    attending_reservations = db.relationship('Reservation', secondary=reservation_attendees,
                                           backref=db.backref('attendees', lazy='dynamic'))
    
    def __repr__(self):
        return f'<Eater {self.name}>'

class DietaryRestriction(db.Model):
    """Dietary restrictions model."""
    __tablename__ = 'dietary_restrictions'
    
    id = db.Column(db.Integer, primary_key=True)
    restriction_name = db.Column(db.String(50), nullable=False, unique=True)
    
    # Mapped endorsements via association table
    endorsements = db.relationship('Endorsement', secondary=restriction_endorsement_mappings,
                                 backref=db.backref('dietary_restrictions', lazy='dynamic'))
    
    def __repr__(self):
        return f'<DietaryRestriction {self.restriction_name}>'

class Endorsement(db.Model):
    """Endorsements for restaurants."""
    __tablename__ = 'endorsements'
    
    id = db.Column(db.Integer, primary_key=True)
    endorsement_name = db.Column(db.String(50), nullable=False, unique=True)
    
    def __repr__(self):
        return f'<Endorsement {self.endorsement_name}>'

class Restaurant(db.Model):
    """Restaurant model."""
    __tablename__ = 'restaurants'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    average_rating = db.Column(db.Float)
    address = db.Column(db.String(255))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    website_url = db.Column(db.String(255))
    has_parking = db.Column(db.Boolean, default=False)
    accepts_reservations = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    hours = db.relationship('RestaurantHours', back_populates='restaurant', uselist=False, cascade='all, delete-orphan')
    tables = db.relationship('Table', back_populates='restaurant', cascade='all, delete-orphan')
    reservations = db.relationship('Reservation', back_populates='restaurant', cascade='all, delete-orphan')
    endorsements = db.relationship('Endorsement', secondary=restaurant_endorsements,
                                 backref=db.backref('restaurants', lazy='dynamic'))
    
    def __repr__(self):
        return f'<Restaurant {self.name}>'

class RestaurantHours(db.Model):
    """Restaurant operating hours."""
    __tablename__ = 'restaurant_hours'
    
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False, unique=True)
    opening_time = db.Column(db.Time, nullable=False)  # e.g., datetime.time(8, 0)
    closing_time = db.Column(db.Time, nullable=False)  # e.g., datetime.time(20, 0)
    
    # Relationships
    restaurant = db.relationship('Restaurant', back_populates='hours')
    
    def __repr__(self):
        return f'<RestaurantHours {self.restaurant.name if self.restaurant else "None"}: {self.opening_time}-{self.closing_time}>'

class Table(db.Model):
    """Restaurant tables."""
    __tablename__ = 'tables'
    
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    
    # Relationships
    restaurant = db.relationship('Restaurant', back_populates='tables')
    reservations = db.relationship('Reservation', back_populates='table')
    
    def __repr__(self):
        return f'<Table {self.id} at {self.restaurant.name if self.restaurant else "None"}: Capacity {self.capacity}>'

class Reservation(db.Model):
    """Reservation model."""
    __tablename__ = 'reservations'
    
    id = db.Column(db.Integer, primary_key=True)
    eater_id = db.Column(db.Integer, db.ForeignKey('eaters.id'), nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False)
    table_id = db.Column(db.Integer, db.ForeignKey('tables.id'))
    reservation_date = db.Column(db.Date, nullable=False)
    reservation_start_time = db.Column(db.String(10), nullable=False)  # e.g., "17:00"
    reservation_end_time = db.Column(db.String(10), nullable=True)  # e.g., "19:00"
    party_size = db.Column(db.Integer, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)  # For soft deletion
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    host = db.relationship('Eater', back_populates='reservations')
    restaurant = db.relationship('Restaurant', back_populates='reservations')
    table = db.relationship('Table', back_populates='reservations')
    # Attendees are defined via the reservation_attendees association table
    # and can be accessed via reservation.attendees
    
    def __repr__(self):
        return f'<Reservation {self.id} for {self.host.name if self.host else "Unknown"} at {self.restaurant.name if self.restaurant else "Unknown"}>'
