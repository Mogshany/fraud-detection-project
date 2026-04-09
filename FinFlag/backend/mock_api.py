from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
import json
from datetime import datetime, timedelta
import random
from typing import List

app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data
MOCK_USER = {
    "id": "user_001",
    "username": "demo",
    "email": "demo@finflag.io",
    "role": "analyst",
    "organization": "FinFlag"
}

def generate_mock_transactions(limit: int = 100) -> List[dict]:
    """Generate mock transaction data"""
    transactions = []
    locations = ["Nairobi", "Juja", "Mombasa", "Kisumu", "Nakuru"]
    
    for i in range(limit):
        timestamp = datetime.now() - timedelta(minutes=random.randint(0, 1440))
        transactions.append({
            "id": f"txn_{i:06d}",
            "sensor_id": f"edge_{random.randint(1, 5):03d}",
            "masked_id": f"mask_{random.randint(100000, 999999)}",
            "behavioral_hash": f"hash_{random.randint(100000, 999999)}",
            "amount": random.randint(100, 50000),
            "timestamp": timestamp.isoformat(),
            "location": random.choice(locations),
            "imsi_status": random.choice(["valid", "invalid", "roaming"]),
            "hardware_risk": round(random.uniform(0, 1), 2)
        })
    
    return sorted(transactions, key=lambda x: x['timestamp'], reverse=True)

def generate_mock_predictions(transactions: List[dict]) -> List[dict]:
    """Generate mock fraud predictions"""
    predictions = []
    
    for tx in transactions:
        fraud_prob = random.uniform(0, 1)
        predictions.append({
            "transaction_id": tx["id"],
            "fraud_probability": round(fraud_prob, 3),
            "status": "BLOCK" if fraud_prob > 0.7 else "PASS",
            "explanation_weights": {
                "location_anomaly": round(random.uniform(0, 1), 2),
                "velocity_check": round(random.uniform(0, 1), 2),
                "device_risk": round(random.uniform(0, 1), 2),
                "time_anomaly": round(random.uniform(0, 1), 2)
            },
            "confidence": round(random.uniform(0.7, 1), 2),
            "timestamp": tx["timestamp"]
        })
    
    return predictions

# ============ ENDPOINTS ============

@app.post("/auth/login")
async def login(username: str, password: str):
    """Mock login endpoint"""
    if username == "demo" and password == "123456":
        return {
            "token": "mock_token_12345",
            "user": MOCK_USER
        }
    return JSONResponse(
        status_code=401,
        content={"message": "Invalid credentials"}
    )

@app.post("/auth/logout")
async def logout():
    """Mock logout endpoint"""
    return {"message": "Logged out"}

@app.get("/transactions")
async def get_transactions(limit: int = 100):
    """Get mock transactions"""
    return generate_mock_transactions(limit)

@app.get("/transactions/{transaction_id}")
async def get_single_transaction(transaction_id: str):
    """Get single mock transaction"""
    transactions = generate_mock_transactions(100)
    tx = next((t for t in transactions if t["id"] == transaction_id), None)
    if not tx:
        return JSONResponse(status_code=404, content={"message": "Not found"})
    return tx

@app.get("/predictions")
async def get_predictions(timeRange: str = "24h"):
    """Get mock predictions"""
    transactions = generate_mock_transactions(100)
    return generate_mock_predictions(transactions)

@app.get("/predictions/{transaction_id}")
async def get_prediction(transaction_id: str):
    """Get single prediction"""
    transactions = generate_mock_transactions(100)
    predictions = generate_mock_predictions(transactions)
    pred = next((p for p in predictions if p["transaction_id"] == transaction_id), None)
    if not pred:
        return JSONResponse(status_code=404, content={"message": "Not found"})
    return pred

@app.get("/stats")
async def get_stats():
    """Get dashboard statistics"""
    transactions = generate_mock_transactions(100)
    predictions = generate_mock_predictions(transactions)
    frauds = [p for p in predictions if p["status"] == "BLOCK"]
    
    return {
        "total_transactions": len(transactions),
        "frauds_detected": len(frauds),
        "fraud_rate": len(frauds) / len(transactions) if transactions else 0,
        "avg_processing_time_ms": round(random.uniform(10, 100), 2),
        "system_uptime": 99.9
    }

@app.get("/alerts")
async def get_alerts(status: str = "active"):
    """Get mock alerts"""
    return []

@app.post("/alerts/{alert_id}/dismiss")
async def dismiss_alert(alert_id: str):
    """Dismiss alert"""
    return {"message": f"Alert {alert_id} dismissed"}

@app.post("/alerts/{alert_id}/investigate")
async def investigate_alert(alert_id: str, notes: str = ""):
    """Investigate alert"""
    return {"message": f"Alert {alert_id} under investigation"}

@app.websocket("/ws/fraud_alerts")
async def websocket_endpoint(websocket):
    """Mock WebSocket for real-time fraud alerts"""
    await websocket.accept()
    
    try:
        while True:
            # Send mock fraud alert every 10 seconds
            await asyncio.sleep(10)
            
            fraud_alert = {
                "type": "fraud_alert",
                "data": {
                    "id": f"alert_{random.randint(10000, 99999)}",
                    "fraud_prob": round(random.uniform(0.7, 1), 2),
                    "masked_id": f"mask_{random.randint(100000, 999999)}",
                    "reason": random.choice([
                        "High location anomaly detected",
                        "Velocity check failed",
                        "Unusual device risk pattern",
                        "Time-based anomaly detected"
                    ]),
                    "timestamp": datetime.now().isoformat(),
                    "actions": "dismiss"
                }
            }
            
            await websocket.send_json(fraud_alert)
    
    except Exception as e:
        print(f"WebSocket error: {e}")

@app.get("/")
async def root():
    """Health check"""
    return {"message": "FinFlag Mock API is running", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)