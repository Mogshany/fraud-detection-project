# test_shield.py
import requests
import json

def test_gateway():
    # The URL where your FastAPI server is running
    url = "http://127.0.0.1:8001/shield/process"

    # Simulated Raw Data from the 'Sensor'
    payload = {
        "sensor_id": "JKUAT-SN-001",
        "imsi_status": "CHANGED",
        "hardware_risk_score": 0.88,
        "raw_phone_number": "0722123456",  # Sensitive Data
        "amount": 5000.0,
        "currency": "KES"
    }

    print("🚀 Sending Transaction to Sharon's Gateway...")
    
    try:
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ SUCCESS!")
            print(f"Status: {result['status']}")
            print(f"Compliance: {result['data']['compliance']}")
            
            original = payload['raw_phone_number']
            encrypted = result['data']['payload']['masked_identity']
            
            print(f"\n🔐 Encryption Check:")
            print(f"   Original Number:  {original}")
            print(f"   Masked Identity:  {encrypted}")
            
            if original != encrypted:
                print("\n✨ Privacy Verified: Data is successfully masked.")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Connection Failed: Is the Uvicorn server running? ({e})")

if __name__ == "__main__":
    test_gateway()