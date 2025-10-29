#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
API Error Handling Test Script
Tests various error scenarios for the Flask API
"""

import requests
import time
import json
import sys
import io

# Set UTF-8 encoding for stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def print_test_header(test_name):
    print("\n" + "="*60)
    print(f"  {test_name}")
    print("="*60)

def test_normal_request():
    """Test 1: Normal API request"""
    print_test_header("Test 1: Normal API Request")

    url = "http://localhost:5000/api/reasoning"
    data = {
        "lat": 35.0,
        "lon": 135.0,
        "co2": 420.5,
        "deviation": 5.0,
        "date": "2023-06-01",
        "severity": "high",
        "zscore": 3.5
    }

    try:
        response = requests.post(url, json=data, timeout=30)

        if response.status_code == 200:
            result = response.json()
            print("✓ Test PASSED")
            print(f"Status Code: {response.status_code}")
            print(f"Cached: {result.get('cached', 'N/A')}")
            print(f"Reasoning Length: {len(result.get('reasoning', ''))} characters")
        else:
            print(f"✗ Test FAILED: Unexpected status code {response.status_code}")
            print(f"Response: {response.text}")

    except Exception as e:
        print(f"✗ Test FAILED: {type(e).__name__}: {e}")

def test_network_error():
    """Test 2: Network error (wrong port)"""
    print_test_header("Test 2: Network Error (Server Not Running)")

    url = "http://localhost:9999/api/reasoning"
    data = {
        "lat": 35.0,
        "lon": 135.0,
        "co2": 420.5,
        "deviation": 5.0,
        "date": "2023-06-01",
        "severity": "high",
        "zscore": 3.5
    }

    try:
        response = requests.post(url, json=data, timeout=5)
        print(f"✗ Test FAILED: Expected connection error but got response {response.status_code}")

    except requests.exceptions.ConnectionError as e:
        print("✓ Test PASSED: Network error correctly detected")
        print(f"Error Type: ConnectionError")
        print("Expected Behavior: Frontend should display 'サーバーに接続できませんでした'")

    except Exception as e:
        print(f"✓ Test PASSED: Network error detected")
        print(f"Error Type: {type(e).__name__}: {e}")

def test_timeout():
    """Test 3: Timeout (very short timeout)"""
    print_test_header("Test 3: Timeout Error")

    url = "http://localhost:5000/api/reasoning"
    data = {
        "lat": 35.0,
        "lon": 135.0,
        "co2": 420.5,
        "deviation": 5.0,
        "date": "2023-06-01",
        "severity": "high",
        "zscore": 3.5
    }

    try:
        # Set a very short timeout (0.01 seconds)
        response = requests.post(url, json=data, timeout=0.01)
        print(f"✗ Test FAILED: Expected timeout but got response {response.status_code}")
        print("Note: Server responded too quickly to trigger timeout")

    except requests.exceptions.Timeout as e:
        print("✓ Test PASSED: Timeout correctly detected")
        print(f"Error Type: Timeout")
        print("Expected Behavior: Frontend should display 'タイムアウトエラー' after 30 seconds")

    except Exception as e:
        print(f"Test Result: {type(e).__name__}: {e}")
        print("Note: May pass if server responds very quickly")

def test_404_error():
    """Test 4: 404 Not Found error"""
    print_test_header("Test 4: 404 Not Found Error")

    url = "http://localhost:5000/api/nonexistent"

    try:
        response = requests.get(url, timeout=5)

        if response.status_code == 404:
            print("✓ Test PASSED: 404 error correctly returned")
            print(f"Status Code: {response.status_code}")
            print("Expected Behavior: Frontend should display 'APIエンドポイントが見つかりません'")
        else:
            print(f"✗ Test FAILED: Expected 404 but got {response.status_code}")

    except Exception as e:
        print(f"✗ Test FAILED: {type(e).__name__}: {e}")

def test_400_bad_request():
    """Test 5: 400 Bad Request (missing required fields)"""
    print_test_header("Test 5: 400 Bad Request (Missing Fields)")

    url = "http://localhost:5000/api/reasoning"
    # Missing required fields
    data = {
        "lat": 35.0,
        "lon": 135.0
    }

    try:
        response = requests.post(url, json=data, timeout=5)

        if response.status_code == 400:
            print("✓ Test PASSED: 400 error correctly returned")
            print(f"Status Code: {response.status_code}")
            result = response.json()
            print(f"Error: {result.get('error', 'N/A')}")
            print(f"Missing Fields: {result.get('missing_fields', 'N/A')}")
            print("Expected Behavior: Frontend should display 'リクエストデータに問題があります'")
        else:
            print(f"✗ Test FAILED: Expected 400 but got {response.status_code}")

    except Exception as e:
        print(f"✗ Test FAILED: {type(e).__name__}: {e}")

def test_health_check():
    """Test 0: Health check endpoint"""
    print_test_header("Test 0: Health Check")

    url = "http://localhost:5000/api/health"

    try:
        response = requests.get(url, timeout=5)

        if response.status_code == 200:
            result = response.json()
            print("✓ Server is running")
            print(f"Status: {result.get('status', 'N/A')}")
            print(f"Message: {result.get('message', 'N/A')}")
        else:
            print(f"✗ Unexpected status code: {response.status_code}")

    except Exception as e:
        print(f"✗ Cannot connect to server: {type(e).__name__}: {e}")
        print("Please make sure Flask server is running on http://localhost:5000")
        return False

    return True

def main():
    print("\n" + "#"*60)
    print("  API Error Handling Test Suite")
    print("#"*60)

    # Check if server is running
    if not test_health_check():
        print("\n⚠️  Please start the Flask server before running tests")
        print("   Run: python app.py")
        return

    # Run all tests
    test_normal_request()
    test_network_error()
    test_timeout()
    test_404_error()
    test_400_bad_request()

    print("\n" + "#"*60)
    print("  Test Suite Complete")
    print("#"*60)
    print("\nNext Steps:")
    print("1. Open http://localhost:5000 in your browser")
    print("2. Select a year and month (e.g., 2023年6月)")
    print("3. Click on a marker to test the API integration")
    print("4. Stop the Flask server and click another marker to test network error")
    print("\n")

if __name__ == "__main__":
    main()
