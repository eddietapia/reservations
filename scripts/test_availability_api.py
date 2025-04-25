#!/usr/bin/env python3
"""
Test script for the restaurant availability API endpoint.
This script runs various test cases and validates the responses.
"""
import json
import subprocess
import sys
from datetime import datetime

BASE_URL = "http://localhost:5001"
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"
YELLOW = "\033[93m"

def run_curl(endpoint, params):
    """Run curl command and return parsed JSON response"""
    param_string = "&".join([f"{k}={v}" if not isinstance(v, list) else "&".join([f"{k}={item}" for item in v]) 
                           for k, v in params.items()])
    url = f"{BASE_URL}/{endpoint}?{param_string}"
    print(f"{YELLOW}Running:{RESET} curl \"{url}\"")
    
    try:
        result = subprocess.run(["curl", "-s", url], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"{RED}Error running curl command: {result.stderr}{RESET}")
            return None
        
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            print(f"{RED}Invalid JSON response:{RESET}\n{result.stdout}")
            return None
    except Exception as e:
        print(f"{RED}Exception running curl command: {e}{RESET}")
        return None

def print_test_result(test_name, passed, details=None):
    """Print test result with formatting"""
    status = f"{GREEN}PASSED{RESET}" if passed else f"{RED}FAILED{RESET}"
    print(f"{BOLD}Test:{RESET} {test_name} - {status}")
    if details and not passed:
        print(f"  {details}")
    print()

def validate_restaurant_fields(restaurant):
    """Validate that a restaurant has all required fields"""
    required_fields = [
        "id", "name", "average_rating", "address", "phone", 
        "hours", "endorsements", "has_parking", "accepts_reservations"
    ]
    missing = [field for field in required_fields if field not in restaurant]
    if missing:
        return False, f"Missing fields: {', '.join(missing)}"
    
    if "hours" in restaurant:
        if not isinstance(restaurant["hours"], dict):
            return False, "Hours should be a dict"
        if "opening" not in restaurant["hours"] or "closing" not in restaurant["hours"]:
            return False, "Hours missing opening/closing times"
    
    if "endorsements" in restaurant:
        if not isinstance(restaurant["endorsements"], list):
            return False, "Endorsements should be a list"
        for endorsement in restaurant["endorsements"]:
            if "id" not in endorsement or "name" not in endorsement:
                return False, "Endorsement missing id/name"
    
    return True, None

def run_tests():
    """Run a series of tests on the availability API"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    tests = [
        {
            "name": "Basic availability - Single eater",
            "params": {
                "time": "19:00",
                "date": today,
                "eater_id": 1
            },
            "validation": lambda resp: (
                resp["status"] == "success" and
                isinstance(resp["restaurants"], list) and
                len(resp["restaurants"]) > 0 and
                resp["count"] == len(resp["restaurants"])
            )
        },
        {
            "name": "Basic availability - Multiple eaters",
            "params": {
                "time": "19:00",
                "date": today,
                "eater_id": [1, 2]
            },
            "validation": lambda resp: (
                resp["status"] == "success" and
                isinstance(resp["restaurants"], list)
            )
        },
        {
            "name": "Missing time parameter",
            "params": {
                "date": today,
                "eater_id": 1
            },
            "validation": lambda resp: (
                resp["status"] == "error" and
                "time" in resp["message"].lower()
            )
        },
        {
            "name": "Missing eater_id parameter",
            "params": {
                "time": "19:00",
                "date": today
            },
            "validation": lambda resp: (
                resp["status"] == "error" and
                "eater" in resp["message"].lower()
            )
        },
        {
            "name": "Invalid eater_id",
            "params": {
                "time": "19:00",
                "date": today,
                "eater_id": 999  # Non-existent eater ID
            },
            "validation": lambda resp: (
                resp["status"] == "error" and
                "not found" in resp["message"].lower()
            )
        },
        {
            "name": "Early morning availability",
            "params": {
                "time": "07:00",
                "date": today,
                "eater_id": 1
            },
            "validation": lambda resp: (
                resp["status"] == "success"
                # Note: Could be empty if no restaurants are open this early
            )
        },
        {
            "name": "Late night availability",
            "params": {
                "time": "22:00",
                "date": today,
                "eater_id": 1
            },
            "validation": lambda resp: (
                resp["status"] == "success"
                # Note: Could be empty if no restaurants are open this late
            )
        },
        {
            "name": "Availability with 0 additional guests",
            "params": {
                "time": "19:00",
                "date": today,
                "eater_id": 1,
                "additional_guests": 0
            },
            "validation": lambda resp: (
                resp["status"] == "success" and
                isinstance(resp["restaurants"], list)
            )
        },
        {
            "name": "Availability with 1 additional guest",
            "params": {
                "time": "19:00",
                "date": today,
                "eater_id": 1,
                "additional_guests": 1
            },
            "validation": lambda resp: (
                resp["status"] == "success" and
                isinstance(resp["restaurants"], list)
            )
        },
        {
            "name": "Availability with 3 additional guests",
            "params": {
                "time": "19:00",
                "date": today,
                "eater_id": 1,
                "additional_guests": 3
            },
            "validation": lambda resp: (
                resp["status"] == "success" and
                isinstance(resp["restaurants"], list)
            )
        },
        {
            "name": "Multiple eaters with additional guests",
            "params": {
                "time": "19:00",
                "date": today,
                "eater_id": [1, 2],
                "additional_guests": 2
            },
            "validation": lambda resp: (
                resp["status"] == "success" and
                isinstance(resp["restaurants"], list)
            )
        },
        {
            "name": "Large group with 10 additional guests",
            "params": {
                "time": "19:00",
                "date": today,
                "eater_id": 1,
                "additional_guests": 10
            },
            "validation": lambda resp: (
                resp["status"] == "success" and
                isinstance(resp["restaurants"], list) and
                len(resp["restaurants"]) == 0 and
                resp["count"] == 0
            )
        },
        {
            "name": "One user with 5 additional guests (should have results)",
            "params": {
                "time": "19:00",
                "date": today,
                "eater_id": 1,
                "additional_guests": 5
            },
            "validation": lambda resp: (
                resp["status"] == "success" and
                isinstance(resp["restaurants"], list) and
                len(resp["restaurants"]) > 0 and
                resp["count"] > 0
            )
        },
        {
            "name": "Two users with 5 additional guests (no tables this large)",
            "params": {
                "time": "19:00",
                "date": today,
                "eater_id": [1, 2],
                "additional_guests": 5
            },
            "validation": lambda resp: (
                resp["status"] == "success" and
                isinstance(resp["restaurants"], list) and
                len(resp["restaurants"]) == 0 and
                resp["count"] == 0
            )
        },
        {
            "name": "Two users with no dietary restrictions plus 4 additional guests",
            "params": {
                "time": "19:00",
                "date": today,
                "eater_id": [3, 4],
                "additional_guests": 4
            },
            "validation": lambda resp: (
                resp["status"] == "success" and
                isinstance(resp["restaurants"], list) and
                len(resp["restaurants"]) > 0
            )
        },
    ]
    
    print(f"{BOLD}{YELLOW}Running API Tests for Restaurant Availability{RESET}")
    print(f"Date: {today}")
    print("=" * 60)
    print()
    
    total_tests = len(tests)
    passed_tests = 0
    
    for test in tests:
        print(f"{BOLD}{test['name']}{RESET}")
        
        # Run the test
        response = run_curl("api/restaurants/available", test["params"])
        
        if response is None:
            print_test_result(test["name"], False, "No valid response received")
            continue
        
        # Validate the response
        try:
            passed = test["validation"](response)
            if passed and response.get("status") == "success" and "restaurants" in response:
                # Additional validation for successful responses with restaurants
                for restaurant in response["restaurants"]:
                    valid, error = validate_restaurant_fields(restaurant)
                    if not valid:
                        passed = False
                        print_test_result(test["name"], False, f"Restaurant validation failed: {error}")
                        break
            
            if passed:
                passed_tests += 1
            
            print_test_result(test["name"], passed)
            
            # Print the response summary
            if response.get("status") == "success" and "restaurants" in response:
                print(f"  Found {response['count']} restaurants")
                for restaurant in response["restaurants"]:
                    endorsements = ", ".join([e["name"] for e in restaurant["endorsements"]])
                    print(f"  - {restaurant['name']} (ID: {restaurant['id']}, Rating: {restaurant['average_rating']})")
                    print(f"    Hours: {restaurant['hours']['opening']} - {restaurant['hours']['closing']}")
                    print(f"    Endorsements: {endorsements}")
            else:
                print(f"  Response: {response.get('status', 'unknown')} - {response.get('message', 'No message')}")
            
            print("-" * 60)
            
        except Exception as e:
            print_test_result(test["name"], False, f"Exception during validation: {e}")
    
    # Print summary
    print()
    print("=" * 60)
    print(f"{BOLD}Test Summary:{RESET}")
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    
    if passed_tests == total_tests:
        print(f"{GREEN}{BOLD}All tests passed!{RESET}")
    else:
        print(f"{RED}{BOLD}Some tests failed.{RESET}")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
