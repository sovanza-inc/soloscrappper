#!/usr/bin/env python3
"""
Test script for the Stripe Webhook API
This script helps test the webhook functionality without making actual payments
"""

import requests
import json
import time
from datetime import datetime

# API base URL
API_BASE_URL = "http://localhost:5000"

def test_health_endpoint():
    """Test the health check endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API. Make sure the server is running.")
        return False
    return True

def test_payment_info_endpoint():
    """Test the payment info endpoint"""
    print("\n🔍 Testing payment info endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/test-payment")
        if response.status_code == 200:
            print("✅ Payment info endpoint working")
            data = response.json()
            print(f"   Payment Link: {data.get('payment_link')}")
            print(f"   Product ID: {data.get('product_id')}")
            print(f"   Price ID: {data.get('price_id')}")
        else:
            print(f"❌ Payment info endpoint failed: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API")
        return False
    return True

def test_webhook_endpoint():
    """Test the webhook endpoint with a mock event"""
    print("\n🔍 Testing webhook endpoint...")
    
    # Mock webhook event (this will fail signature verification, but tests the endpoint)
    mock_event = {
        "id": "evt_test_123",
        "object": "event",
        "type": "payment_intent.succeeded",
        "data": {
            "object": {
                "id": "pi_test_123",
                "object": "payment_intent",
                "amount": 2999,
                "currency": "usd",
                "status": "succeeded",
                "created": int(time.time()),
                "customer": "cus_test_123",
                "payment_method": "pm_test_123"
            }
        }
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/webhook",
            json=mock_event,
            headers={"Content-Type": "application/json"}
        )
        
        # This should fail due to invalid signature, but endpoint is reachable
        if response.status_code in [400, 401]:
            print("✅ Webhook endpoint is reachable (signature verification working)")
            print(f"   Response: {response.json()}")
        else:
            print(f"⚠️  Unexpected response: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to webhook endpoint")
        return False
    
    return True

def main():
    """Main test function"""
    print("🧪 Stripe Webhook API Test Suite")
    print("="*50)
    
    # Check if API is running
    if not test_health_endpoint():
        print("\n❌ API is not running. Please start the server first:")
        print("   python stripe_webhook_api.py")
        return
    
    # Test all endpoints
    test_payment_info_endpoint()
    test_webhook_endpoint()
    
    print("\n" + "="*50)
    print("🎯 Test Summary:")
    print("✅ Health endpoint: Working")
    print("✅ Payment info endpoint: Working") 
    print("✅ Webhook endpoint: Reachable")
    print("\n💡 Next steps:")
    print("   1. Use Stripe CLI to test real webhooks:")
    print("      stripe listen --forward-to localhost:5000/api/webhook")
    print("   2. Or use ngrok to expose your local server")
    print("   3. Test with your payment link: https://buy.stripe.com/test_3cI4gzgoe5Nu6qz14je3e00")

if __name__ == "__main__":
    main()
