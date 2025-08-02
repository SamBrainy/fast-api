# stripe_service.py

import os
import stripe
from dotenv import load_dotenv

load_dotenv()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

def create_stripe_payout(amount_usd: float, currency: str = "USD"):
    """
    Creates a Stripe payout to the default external account (your linked bank).
    Stripe requires the amount in cents.
    """
    try:
        # Convert to smallest currency unit (e.g. cents)
        amount_cents = int(amount_usd * 100)

        payout = stripe.Payout.create(
            amount=amount_cents,
            currency=currency.lower(),  # e.g., "usd"
            method="standard",          # or "instant" if available
            statement_descriptor="PrivateLedgerPayout"
        )
        return {"id": payout.id, "status": payout.status, "amount": payout.amount}
    except stripe.error.StripeError as e:
        return {"error": str(e)}
