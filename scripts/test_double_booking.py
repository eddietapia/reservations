#!/usr/bin/env python3
"""
Test script for the double booking prevention feature.
This script tests that a user cannot have overlapping reservations at different restaurants.
"""
import json
import subprocess
import sys
from datetime import datetime, timedelta

BASE_URL = "http://localhost:5001"
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"
YELLOW = "\033[93m"

def run_curl(endpoint, method="GET", data=None, params=None):
    """Run curl command and return parsed JSON response"""
    url = f"{BASE_URL}/{endpoint}"
    
    if params:
        param_string = "&".join([f"{k}={v}" if not isinstance(v, list) else "&".join([f"{k}={item}" for item in v]) 
                               for k, v in params.items()])
        url = f"{url}?{param_string}"
    
    curl_cmd = ["curl", "-s"]
    
    if method.upper() != "GET":
        curl_cmd.extend(["-X", method.upper()])
    
    if data:
        curl_cmd.extend(["-H", "Content-Type: application/json", "-d", json.dumps(data)])
    
    curl_cmd.append(url)
    
    print(f"{YELLOW}Running:{RESET} {' '.join(curl_cmd)}")
    
    try:
        result = subprocess.run(curl_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"{RED}Error running curl command: {result.stderr}{RESET}")
            return None
        
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            print(f"{RED}Error parsing JSON response: {result.stdout}{RESET}")
            return None
    except Exception as e:
        print(f"{RED}Exception occurred: {str(e)}{RESET}")
        return None


def print_test_result(test_name, passed, details=None):
    """Print test result with formatted output"""
    status = f"{GREEN}PASSED{RESET}" if passed else f"{RED}FAILED{RESET}"
    print(f"{BOLD}{test_name}:{RESET} {status}")
    if details:
        print(f"  {'Details: ' + details}")
    print()

def validate_reservation_fields(reservation):
    """Check if reservation has all required fields"""
    required_fields = [
        "id", "eater_id", "restaurant_id", "table_id", 
        "reservation_date", "reservation_start_time", "reservation_end_time",
        "party_size"
    ]
    
    missing_fields = [field for field in required_fields if field not in reservation]
    
    if missing_fields:
        return False, f"Missing fields: {', '.join(missing_fields)}"
    
    return True, ""

def main():
    """Run all tests"""
    print("Testing Double Booking Prevention")
    print("==================================================")
    
    all_tests_passed = True
    reservation_ids = []
    
    # Test 1: Create first reservation for user 1 at restaurant 1
    test_name = "Create First Reservation"
    reservation_data = {
        "eater_id": 1,  # Eddie
        "restaurant_id": 1,  # Tartine Bakery
        "date": "2025-06-01",
        "time": "18:00",
        "guests_count": 1
    }
    
    response = run_curl("api/reserve", method="POST", data=reservation_data)
    
    if not response:
        print_test_result(test_name, False, "No response received")
        all_tests_passed = False
    elif response.get("status") != "success":
        print_test_result(test_name, False, response.get("message", "Unknown error"))
        all_tests_passed = False
    else:
        reservation = response.get("reservation", {})
        valid, details = validate_reservation_fields(reservation)
        
        if not valid:
            print_test_result(test_name, False, details)
            all_tests_passed = False
        else:
            print_test_result(test_name, True, f"Reservation created at {reservation['reservation_start_time']} - {reservation['reservation_end_time']}")
            reservation_ids.append(reservation["id"])
    
    # Test 2: Try to create an overlapping reservation at a different restaurant for the same user
    test_name = "Prevent Double Booking (Different Restaurant)"
    reservation_data = {
        "eater_id": 1,  # Eddie again
        "restaurant_id": 2,  # Tacos el Gordo (different restaurant)
        "date": "2025-06-01",  # Same date
        "time": "19:00",  # Within the 2-hour window of previous reservation
        "guests_count": 1
    }
    
    response = run_curl("api/reserve", method="POST", data=reservation_data)
    
    if not response:
        print_test_result(test_name, False, "No response received")
        all_tests_passed = False
    else:
        # We expect this to fail with a message about already having a reservation
        expected_failed = response.get("status") == "error" and "You already have a reservation" in response.get("message", "")
        
        if expected_failed:
            print_test_result(test_name, True, response.get("message"))
        else:
            print_test_result(test_name, False, "Expected to prevent double booking, but reservation was created")
            if response.get("status") == "success":
                reservation = response.get("reservation", {})
                reservation_ids.append(reservation["id"])
            all_tests_passed = False
    
    # Test 3: Test being an attendee at a restaurant while hosting at another
    test_name = "Prevent Double Booking (As Attendee)"
    reservation_data = {
        "eater_id": 2,  # Jalen
        "restaurant_id": 3,  # Lardo
        "date": "2025-06-01",  # Same date
        "time": "19:30",  # Within the window
        "attendee_ids": [1],  # Try to add Eddie who already has a reservation
        "guests_count": 0
    }
    
    response = run_curl("api/reserve", method="POST", data=reservation_data)
    
    if not response:
        print_test_result(test_name, False, "No response received")
        all_tests_passed = False
    else:
        # Should fail with message about attendee already having a reservation
        expected_failed = response.get("status") == "error" and "Attendee" in response.get("message", "") and "already have a reservation" in response.get("message", "")
        
        if expected_failed:
            print_test_result(test_name, True, response.get("message"))
        else:
            print_test_result(test_name, False, "Expected to prevent adding attendee with conflict, but reservation was created")
            if response.get("status") == "success":
                reservation = response.get("reservation", {})
                reservation_ids.append(reservation["id"])
            all_tests_passed = False
    
    # Clean up: Delete all reservations created
    print("Cleaning up test reservations...")
    for res_id in reservation_ids:
        run_curl(f"api/reservations/{res_id}", method="DELETE")
    
    print("==================================================")
    print(f"All tests {'passed' if all_tests_passed else 'failed'}")
    print("==================================================")

if __name__ == "__main__":
    main()
