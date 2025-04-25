# Flask Reservation System

A simple Flask application for managing reservations.

## Installation

1. Clone this repository:

```
git clone <repository-url>
cd reservations
```

2. Create a virtual environment (optional but recommended):

```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required dependencies:

```
pip install -r requirements.txt
```

## Running the Application

1. Start the Flask development server:

```
python app.py
```

## Technology Stack

- Python 3.x
- Flask: Web framework
- SQLAlchemy: ORM for database operations
- PostgreSQL/SQLite: Database backends

## Running Tests

Video here: https://screen.studio/share/oKNlrzZF

1. Make sure you have activated your virtual environment:

```
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install the testing dependencies if you haven't already:

```
pip install pytest
```

3. Run all tests:

```
python -m pytest
```

4. Run a specific test file:

```
python -m pytest tests/test_availability_helpers.py
```

5. Run tests with verbose output:

```
python -m pytest tests/test_availability_helpers.py -v
```

6. Run a specific test function:

```
python -m pytest tests/test_availability_helpers.py::test_aggregate_dietary_restrictions
```

## Utility Scripts

The `/scripts` folder contains several utility scripts to help you interact with and test the reservation system:

### Database Management Scripts

1. **Reset Database** - Initialize or reset the database to a clean state:

```
python scripts/reset_db.py
```

2. **Seed Data** - Populate the database with sample restaurants, eaters, and reservations:

```
python scripts/seed_data.py
```

### Database Visualization Scripts

3. **View Database** - Visualize all database tables with colorful formatting:

```
python scripts/view_db.py
```

This provides a comprehensive view of the entire database, including the many-to-many relationships between eaters and reservations, restaurant details, and more.

4. **View Reservations** - Focus specifically on reservations and their attendees:

```
python scripts/view_reservations.py
```

This script shows all reservations with their start and end times, hosts, and all attendees (showcasing the many-to-many relationship between eaters and reservations).

Video: https://screen.studio/share/tvIwTIoc
![Viewing the state of the database](image.png)

## API Testing

The project includes a comprehensive API testing script for the restaurant availability endpoint.

1. Make sure the Flask server is running in one terminal:

```
python app.py
```

2. In another terminal, run the API test script:

```
python scripts/test_availability_api.py
```

This script will:

- Test the `/api/restaurants/available` endpoint with multiple scenarios
- Validate responses for various inputs including:
  - Single and multiple eaters
  - Missing or invalid parameters
  - Time edge cases (early morning, late night)
  - 24-hour restaurant availability
- Verify restaurant field structure and content
- Output colorful, formatted test results

The script is useful for quickly verifying that the API returns correct responses after code changes or database updates.

Video: https://screen.studio/share/jPpfyIDl
![Running API Tests](./running-api-tests.gif)

### API Testing Scripts

3. **Test Availability API** - Test the restaurant availability searching API:

```
python scripts/test_availability_api.py
```

4. **Test Double-Booking Prevention** - Test the system's ability to prevent double-bookings:

```
python scripts/test_double_booking.py
```

This script verifies that the system properly prevents users from having overlapping reservations at different restaurants and checks time window validations.

## Future Improvements

- Giving restaurants ability to customize their hours at the day level.
- Custom error codes
  - Right now just defaulted to custom http error codes, but in practice, we'd want more specific error codes so we can monitor and handle them more effectively.

## Database Schema

```sql
-- Eaters (Users) table
CREATE TABLE eaters (
    eater_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Dietary Restrictions table (for many-to-many relationship)
CREATE TABLE dietary_restrictions (
    restriction_id SERIAL PRIMARY KEY,
    restriction_name VARCHAR(50) UNIQUE NOT NULL
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Eater Dietary Restrictions (junction table)
CREATE TABLE eater_dietary_restrictions (
    eater_id INTEGER REFERENCES eaters(eater_id),
    restriction_id INTEGER REFERENCES dietary_restrictions(restriction_id),
    PRIMARY KEY (eater_id, restriction_id)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Restaurants table
CREATE TABLE restaurants (
    restaurant_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL
    average_rating DECIMAL(3,2),
    address TEXT NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(255),
    website_url VARCHAR(255),
    has_parking BOOLEAN DEFAULT FALSE,
    accepts_reservations BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Operating hours table
CREATE TABLE restaurant_hours (
    restaurant_id INTEGER REFERENCES restaurants(restaurant_id),
    day_of_week INTEGER CHECK (day_of_week BETWEEN 0 AND 6),
    opening_time TIME,
    closing_time TIME,
    PRIMARY KEY (restaurant_id, day_of_week)
);

-- Restaurant Endorsements table (for many-to-many relationship)
CREATE TABLE endorsements (
    endorsement_id SERIAL PRIMARY KEY,
    endorsement_name VARCHAR(50) UNIQUE NOT NULL
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Restaurant Endorsements (junction table)
CREATE TABLE restaurant_endorsements (
    restaurant_id INTEGER REFERENCES restaurants(restaurant_id),
    endorsement_id INTEGER REFERENCES endorsements(endorsement_id),
    PRIMARY KEY (restaurant_id, endorsement_id)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Tables table
CREATE TABLE tables (
    table_id SERIAL PRIMARY KEY,
    restaurant_id INTEGER REFERENCES restaurants(restaurant_id),
    capacity INTEGER NOT NULL CHECK (capacity > 0)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);


-- Reservations table
CREATE TABLE reservations (
    reservation_id SERIAL PRIMARY KEY,
    table_id INTEGER REFERENCES tables(table_id),
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
    -- Add constraint to ensure end_time is after start_time
    CONSTRAINT valid_reservation_times CHECK (end_time > start_time)
);

-- Reservation Attendees (junction table for diners in a reservation)
CREATE TABLE reservation_attendees (
    reservation_id INTEGER REFERENCES reservations(reservation_id),
    eater_id INTEGER REFERENCES eaters(eater_id),
    PRIMARY KEY (reservation_id, eater_id)
);

-- Create mapping table between dietary restrictions and restaurant endorsements
CREATE TABLE restriction_endorsement_mappings (
    restriction_id INTEGER REFERENCES dietary_restrictions(restriction_id),
    endorsement_id INTEGER REFERENCES endorsements(endorsement_id),
    PRIMARY KEY (restriction_id, endorsement_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```
