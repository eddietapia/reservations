#!/usr/bin/env python3
"""
Test script for the soft deletion functionality.
This script creates a reservation, tests both soft and hard deletion scenarios.
"""
import json
import subprocess
import sys
import time
from datetime import datetime, timedelta

BASE_URL = "http://localhost:5001"

# ANSI color codes for better readability
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
BOLD = "\033[1m"
RESET = "\033[0m"

def run_curl(endpoint, method="GET", data=None, params=None):
    """Run curl command and return parsed JSON response"""
    url = f"{BASE_URL}/{endpoint}"
    
    if params:
        param_string = "&".join([f"{k}={v}" for k, v in params.items()])
        url = f"{url}?{param_string}"
    
    print(f"{YELLOW}Running:{RESET} curl", end=" ")
    if method.upper() != "GET":
        print(f"-X {method.upper()}", end=" ")
    
    if data:
        print(f"-H 'Content-Type: application/json' -d '{json.dumps(data)}'", end=" ")
    
    print(url)
    
    curl_cmd = ["curl", "-s"]
    
    if method.upper() != "GET":
        curl_cmd.extend(["-X", method.upper()])
    
    if data:
        curl_cmd.extend(["-H", "Content-Type: application/json", "-d", json.dumps(data)])
    
    curl_cmd.append(url)
    
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

def print_step(step_name):
    """Print a step name with formatting"""
    print(f"\n{BOLD}{BLUE}=== {step_name} ==={RESET}")

def print_response(response):
    """Print API response with nice formatting"""
    if response is None:
        print(f"{RED}No response received{RESET}")
        return
    
    status = response.get("status")
    message = response.get("message", "")
    
    if status == "success":
        print(f"{GREEN}✓ Success:{RESET} {message}")
        # Print any additional info
        for key, value in response.items():
            if key not in ["status", "message"]:
                print(f"  {key}: {value}")
    else:
        print(f"{RED}✗ Error:{RESET} {message}")

def test_soft_deletion():
    """Test the soft deletion feature"""
    print(f"{BOLD}{YELLOW}Testing Soft Deletion API{RESET}")
    print("=" * 50)
    
    # Step 1: Create a reservation for testing
    print_step("Create a new reservation")
    
    # Use tomorrow's date to avoid conflicts with other tests
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    # Create a reservation
    reservation_data = {
        "eater_id": 2,  # Jalen Hurts
        "restaurant_id": 2,  # Nong's
        "date": tomorrow,
        "time": "18:00",
        "guests_count": 1
    }
    
    response = run_curl("api/reserve", method="POST", data=reservation_data)
    print_response(response)
    
    if not response or response.get("status") != "success":
        print(f"{RED}Failed to create test reservation. Exiting.{RESET}")
        return
    
    # Store the reservation ID for later operations
    reservation_id = response.get("reservation", {}).get("id")
    print(f"{YELLOW}Created reservation with ID: {reservation_id}{RESET}")
    
    # Step 2: Test soft deletion
    print_step("Perform soft deletion")
    soft_delete_response = run_curl(f"api/reservations/{reservation_id}", 
                                    method="DELETE", 
                                    params={"soft_delete": "true"})
    print_response(soft_delete_response)
    
    # Step 3: Try to get the deleted reservation details
    print_step("Get soft-deleted reservation (should fail)")
    get_response = run_curl(f"api/reservations/{reservation_id}")
    print_response(get_response)
    
    # Step 4: Get the deleted reservation with include_inactive flag
    print_step("Get soft-deleted reservation with include_inactive=true")
    get_response = run_curl(f"api/reservations/{reservation_id}", 
                           params={"include_inactive": "true"})
    print_response(get_response)
    
    # Step 5: Create reservation again at the same time (should succeed since previous one was soft-deleted)
    print_step("Create another reservation at the same time (should succeed)")
    response = run_curl("api/reserve", method="POST", data=reservation_data)
    print_response(response)
    
    if response and response.get("status") == "success":
        new_reservation_id = response.get("reservation", {}).get("id")
        print(f"{YELLOW}Created new reservation with ID: {new_reservation_id}{RESET}")
        
        # Clean up - hard delete this reservation
        print_step("Clean up - Hard delete second reservation")
        delete_response = run_curl(f"api/reservations/{new_reservation_id}", method="DELETE")
        print_response(delete_response)
    
    # Summary
    print("\n" + "=" * 50)
    print(f"{BOLD}{GREEN}Soft deletion test completed!{RESET}")

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

    test_soft_deletion()
