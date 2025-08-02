### stripe_fastapi_receiver/main.py

import os
import hmac
import hashlib
import json
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Header, HTTPException
from pydantic import BaseModel

# Optional: ensure fallback if ssl is missing
try:
    import ssl
except ModuleNotFoundError:
    raise ImportError("Missing 'ssl' module. Ensure your Python environment includes SSL support.")

from stripe_service import create_stripe_payout
from database import init_db, record_transaction

load_dotenv()

app = FastAPI()

SHARED_SECRET = os.getenv("DWINSHAREDSECRET")
if not SHARED_SECRET:
    raise ValueError("DWINSHAREDSECRET not set in environment variables.")
SHARED_SECRET = SHARED_SECRET.encode()

init_db()

class Amount(BaseModel):
    Ccy: str
    value: str

class CreditTransfer(BaseModel):
    Amt: dict
    Cdtr: dict
    CdtrAcct: dict
    RmtInf: dict

class ISO20022Webhook(BaseModel):
    Document: dict

@app.post("/webhook")
async def receive_webhook(
    request: Request,
    x_dwin_signature: str = Header(None)
):
    raw_body = await request.body()
    expected_sig = hmac.new(SHARED_SECRET, raw_body, hashlib.sha256).hexdigest()
    if x_dwin_signature != expected_sig:
        raise HTTPException(status_code=401, detail="Invalid signature")

    data = await request.json()
    try:
        message = ISO20022Webhook(**data)
        transfers = message.Document["CstmrCdtTrfInitn"]["PmtInf"]["CdtTrfTxInf"]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid data format: {e}")

    for tx in transfers:
        amount = float(tx["Amt"]["InstdAmt"]["value"])
        currency = tx["Amt"]["InstdAmt"]["Ccy"]
        reference = tx["RmtInf"]["Ustrd"]
        recipient = tx["Cdtr"]["Nm"]

        record_transaction(reference, recipient, amount, currency)

        if currency == "USD":
            payout_response = create_stripe_payout(amount, currency)
            return {"status": "processed", "payout": payout_response}

    return {"status": "ignored"}
