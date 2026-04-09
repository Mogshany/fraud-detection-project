# gateway/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
# Try this specific import style in gateway/main.py
try:
    from .encryption_logic import GatewayProtector
except ImportError:
    from encryption_logic import GatewayProtector
import os
from dotenv import load_dotenv

# Load keys from .env for security
load_dotenv()
FPE_KEY = os.getenv("FPE_KEY", "EF4359D8D580AA4F7F036D6F04FC6A94")
FPE_TWEAK = os.getenv("FPE_TWEAK", "D8E792A1B2C3D4") # <--- Changed to 14 characters

app = FastAPI(title="FinFlag Gateway Shield")
protector = GatewayProtector(FPE_KEY, FPE_TWEAK)

# Define the expected data structure from the Sensor
class TransactionRequest(BaseModel):
    sensor_id: str
    imsi_status: str
    hardware_risk_score: float
    raw_phone_number: str  # This is the sensitive PII
    amount: float
    currency: str = "KES"

@app.post("/shield/process")
async def process_transaction(request: TransactionRequest):
    try:
        # 1. Apply Format-Preserving Encryption to the phone number
        masked_phone = protector.encrypt_identifier(request.raw_phone_number)
        
        # 2. Construct the "Privacy-Safe" packet for the AI/Infrastructure
        safe_packet = {
            "metadata": {
                "sensor": request.sensor_id,
                "hardware_risk": request.hardware_risk_score,
                "imsi_anomaly": request.imsi_status
            },
            "payload": {
                "masked_identity": masked_phone,
                "amount": request.amount,
                "currency": request.currency
            },
            "compliance": "PII_MASKED_FF1"
        }
        
        # In a full system, you would now send 'safe_packet' to Member 3's Redis Queue
        return {"status": "SUCCESS", "data": safe_packet}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Encryption Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)