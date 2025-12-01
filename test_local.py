#!/usr/bin/env python3
"""
Simple test script to verify the local backend is working.
Run this after starting the server with run_local.sh or run_local.bat
"""
import requests
import json
import sys

API_URL = "http://localhost:8080"

def test_health():
    """Test the health endpoint."""
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health check passed!")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Is it running?")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_plan():
    """Test the meal planning endpoint with a simple prompt."""
    print("\nTesting meal plan endpoint...")
    test_prompt = "Create a 2-day meal plan with simple recipes."
    
    try:
        response = requests.post(
            f"{API_URL}/plan",
            json={"prompt": test_prompt},
            headers={"Content-Type": "application/json"},
            timeout=300  # 5 minutes for agent processing
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Meal plan request successful!")
            print(f"   Summary length: {len(data.get('summary', ''))} characters")
            print(f"   Days found: {len(data.get('structured_data', {}).get('days', []))}")
            return True
        else:
            print(f"❌ Meal plan request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except requests.exceptions.Timeout:
        print("⏱️  Request timed out (this is normal for first request)")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing My Meal Planner Backend")
    print("=" * 40)
    
    # Check if requests is installed
    try:
        import requests
    except ImportError:
        print("❌ 'requests' library not found.")
        print("   Install it with: pip install requests")
        print("   Or add it to requirements.txt for testing")
        sys.exit(1)
    
    health_ok = test_health()
    
    if health_ok:
        print("\n⚠️  Note: Full meal plan test may take several minutes.")
        print("   This test will timeout after 5 minutes.")
        user_input = input("\nRun full meal plan test? (y/n): ")
        if user_input.lower() == 'y':
            test_plan()
    else:
        print("\n❌ Server is not running. Please start it first:")
        print("   ./run_local.sh  (Mac/Linux)")
        print("   run_local.bat   (Windows)")

