#!/usr/bin/env python3
"""
Test script for the reservation API endpoints.
This script runs various test cases and validates the responses.
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
    if details and not passed:
        print(f"  {RED}Details: {details}{RESET}")
    print()


def validate_reservation_fields(reservation):
    """Validate that a reservation response has all required fields"""
    required_fields = [
        "id", "host_id", "host_name", "restaurant_id", "restaurant_name", 
        "table_id", "date", "start_time", "end_time", "party_size", 
        "attendees", "created_at"
    ]
    
    missing_fields = [field for field in required_fields if field not in reservation]
    
    if missing_fields:
        return False, f"Missing fields: {', '.join(missing_fields)}"
    
    # Validate attendees structure
    if not isinstance(reservation["attendees"], list):
        return False, "Attendees field is not a list"
    
    for attendee in reservation["attendees"]:
        attendee_fields = ["id", "name", "email"]
        missing_attendee_fields = [field for field in attendee_fields if field not in attendee]
        if missing_attendee_fields:
            return False, f"Attendee missing fields: {', '.join(missing_attendee_fields)}"
    
    return True, None


def run_tests():
    """Run a series of tests on the reservation API"""
    print(f"{BOLD}{YELLOW}Running Reservation API Tests{RESET}")
    print("=" * 50)
    
    # Store created reservation IDs for cleanup
    created_reservation_ids = []
    
    print(f"{BOLD}{GREEN}Starting reservation API tests...{RESET}\n")
    
    all_tests_passed = True
    
    # Test 1: Create a reservation with just host (no additional attendees)
    test_name = "Create Reservation (Host Only)"
    reservation_data = {
        "eater_id": 1,  # Eddie Tapia
        "restaurant_id": 1,  # Tartine Bakery
        "date": "2025-05-01",
        "time": "18:00",
        "guests_count": 1  # One additional unnamed guest
    }
    
    response = run_curl("api/reserve", method="POST", data=reservation_data)
    
    if not response:
        print_test_result(test_name, False, "No response received")
        all_tests_passed = False
    elif response.get("status") != "success":
        print_test_result(test_name, False, response.get("message", "Unknown error"))
        all_tests_passed = False
    else:
        # Validate reservation response
        reservation = response.get("reservation", {})
        valid, details = validate_reservation_fields(reservation)
        
        if not valid:
            print_test_result(test_name, False, details)
            all_tests_passed = False
        else:
            # Verify reservation data matches request
            passed = True
            errors = []
            
            if reservation["host_id"] != reservation_data["eater_id"]:
                passed = False
                errors.append(f"Host ID mismatch: {reservation['host_id']} vs {reservation_data['eater_id']}")
            
            if reservation["restaurant_id"] != reservation_data["restaurant_id"]:
                passed = False
                errors.append(f"Restaurant ID mismatch: {reservation['restaurant_id']} vs {reservation_data['restaurant_id']}")
            
            if reservation["date"] != reservation_data["date"]:
                passed = False
                errors.append(f"Date mismatch: {reservation['date']} vs {reservation_data['date']}")
            
            if reservation["start_time"] != reservation_data["time"]:
                passed = False
                errors.append(f"Time mismatch: {reservation['start_time']} vs {reservation_data['time']}")
            
            # Should be host (1) + guests (1) = 2
            if reservation["party_size"] != 2:
                passed = False
                errors.append(f"Party size incorrect: {reservation['party_size']} vs expected 2")
            
            # Should be just the host in attendees
            if len(reservation["attendees"]) != 1:
                passed = False
                errors.append(f"Expected 1 attendee (host), got {len(reservation['attendees'])}")
            
            print_test_result(test_name, passed, ", ".join(errors) if errors else None)
            all_tests_passed = all_tests_passed and passed
            
            # Save reservation ID for later tests
            if passed:
                reservation_id = reservation["id"]
                created_reservation_ids.append(reservation_id)
    
    # Test 2: Create a reservation with multiple attendees
    test_name = "Create Reservation (Multiple Attendees)"
    reservation_data = {
        "eater_id": 4,  # Rihanna
        "restaurant_id": 3,  # Lardo
        "date": "2025-05-04",
        "time": "19:00",
        "attendee_ids": [2, 3],  # Jalen and Selena
        "guests_count": 0  # No additional unnamed guests
    }
    
    response = run_curl("api/reserve", method="POST", data=reservation_data)
    
    if not response:
        print_test_result(test_name, False, "No response received")
        all_tests_passed = False
    elif response.get("status") != "success":
        print_test_result(test_name, False, response.get("message", "Unknown error"))
        all_tests_passed = False
    else:
        # Validate reservation response
        reservation = response.get("reservation", {})
        valid, details = validate_reservation_fields(reservation)
        
        if not valid:
            print_test_result(test_name, False, details)
            all_tests_passed = False
        else:
            # Verify reservation data
            passed = True
            errors = []
            
            # Check basic fields
            if reservation["host_id"] != reservation_data["eater_id"]:
                passed = False
                errors.append(f"Host ID mismatch: {reservation['host_id']} vs {reservation_data['eater_id']}")
                
            if reservation["restaurant_id"] != reservation_data["restaurant_id"]:
                passed = False
                errors.append(f"Restaurant ID mismatch: {reservation['restaurant_id']} vs {reservation_data['restaurant_id']}")
            
            # Should have 3 people in the party (host + 2 attendees, no guests)
            if reservation["party_size"] != 3:
                passed = False
                errors.append(f"Party size incorrect: {reservation['party_size']} vs expected 3")
            
            # Should have 3 attendees (host + 2 others)
            if len(reservation["attendees"]) != 3:
                passed = False
                errors.append(f"Expected 3 attendees, got {len(reservation['attendees'])}")
            else:
                # Check that all expected attendees are present
                attendee_ids = [a["id"] for a in reservation["attendees"]]
                expected_ids = [reservation_data["eater_id"]] + reservation_data["attendee_ids"]
                
                for expected_id in expected_ids:
                    if expected_id not in attendee_ids:
                        passed = False
                        errors.append(f"Expected attendee {expected_id} not found in reservation")
            
            print_test_result(test_name, passed, ", ".join(errors) if errors else None)
            all_tests_passed = all_tests_passed and passed
            
            if passed:
                reservation_id_2 = reservation["id"]
                created_reservation_ids.append(reservation_id_2)
    
    # Test 3: Try to create an overlapping reservation (time conflict)
    test_name = "Reservation Time Conflict Detection"
    # Try to book restaurant with limited tables (u.to.pi.a has only 2 small tables)
    # First, book both tables and then try a third reservation
    
    # Book first table
    first_booking = {
        "eater_id": 3,  # Selena Gomez
        "restaurant_id": 7,  # u.to.pi.a (only has 2 tables)
        "date": "2025-05-03", # Different date to avoid conflicts with other tests
        "time": "19:00",
        "guests_count": 1
    }
    first_response = run_curl("api/reserve", method="POST", data=first_booking)
    if first_response and first_response.get("status") == "success":
        created_reservation_ids.append(first_response.get("reservation", {}).get("id"))
    
    # Book second table
    second_booking = {
        "eater_id": 4,  # Another user
        "restaurant_id": 7,  # Same restaurant
        "date": "2025-05-03", # Same date
        "time": "19:30",      # Overlapping time
        "guests_count": 1
    }
    second_response = run_curl("api/reserve", method="POST", data=second_booking)
    if second_response and second_response.get("status") == "success":
        created_reservation_ids.append(second_response.get("reservation", {}).get("id"))
    
    # Now try a third booking - this should fail as all tables are booked
    reservation_data = {
        "eater_id": 2,  # Jalen Hurts
        "restaurant_id": 7,  # u.to.pi.a 
        "date": "2025-05-03", # Same date
        "time": "20:00",      # Overlapping with existing reservations
        "guests_count": 1
    }
    
    response = run_curl("api/reserve", method="POST", data=reservation_data)
    
    # This should fail with an appropriate error message
    if not response:
        print_test_result(test_name, False, "No response received")
        all_tests_passed = False
    else:
        # We expect this to fail with "No tables available" message
        expected_failed = response.get("status") == "error" and "No tables available" in response.get("message", "")
        
        print_test_result(test_name, expected_failed, 
                         "Expected reservation to be rejected due to time conflict" if not expected_failed else None)
        all_tests_passed = all_tests_passed and expected_failed
    
    # Test 4: Delete a reservation
    test_name = "Delete Reservation"
    
    # Use the ID from the first reservation test
    try:
        response = run_curl(f"api/reservations/{reservation_id}", method="DELETE")
        
        if not response:
            print_test_result(test_name, False, "No response received")
            all_tests_passed = False
        elif response.get("status") != "success":
            print_test_result(test_name, False, response.get("message", "Unknown error"))
            all_tests_passed = False
        else:
            print_test_result(test_name, True)
            # Remove this reservation from the cleanup list since we've already deleted it
            if reservation_id in created_reservation_ids:
                created_reservation_ids.remove(reservation_id)
    except:
        print_test_result(test_name, False, "Could not delete reservation")
        all_tests_passed = False
    
    # Clean up all reservations created during this test run
    print(f"\n{YELLOW}Cleaning up reservations created during testing...{RESET}")
    cleanup_success = True
    
    if not created_reservation_ids:
        print(f"{YELLOW}No reservations were created during testing.{RESET}")
    else:
        print(f"{YELLOW}Cleaning up {len(created_reservation_ids)} created reservations: {created_reservation_ids}{RESET}")
        for res_id in created_reservation_ids:
            try:
                response = run_curl(f"api/reservations/{res_id}", method="DELETE")
                if not response or response.get("status") != "success":
                    print(f"{YELLOW}Warning: Could not delete reservation {res_id}{RESET}")
                    cleanup_success = False
                else:
                    print(f"{GREEN}Successfully deleted reservation {res_id}{RESET}")
            except Exception as e:
                print(f"{YELLOW}Error during cleanup of reservation {res_id}: {str(e)}{RESET}")
                cleanup_success = False
        
        if cleanup_success:
            print(f"{GREEN}Successfully cleaned up all {len(created_reservation_ids)} reservations.{RESET}")
        else:
            print(f"{YELLOW}Some reservations could not be cleaned up.{RESET}")
    
    # Summary
    print("=" * 50)
    if all_tests_passed:
        print(f"{GREEN}{BOLD}All tests passed!{RESET}")
    else:
        print(f"{RED}{BOLD}Some tests failed.{RESET}")
    
    return all_tests_passed


if __name__ == "__main__":
    # First check if the Flask server is running
    try:
        result = subprocess.run(["curl", "-s", f"{BASE_URL}/health"], capture_output=True)
        if result.returncode != 0:
            print(f"{RED}Error: Flask server not running. Please start it with 'python app.py' before running tests.{RESET}")
            sys.exit(1)
    except:
        print(f"{RED}Error: Could not connect to Flask server. Please start it with 'python app.py' before running tests.{RESET}")
        sys.exit(1)

    success = run_tests()
    sys.exit(0 if success else 1)
