# stripe_service.py

import os
import stripe
import logging
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("stripe_service")

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

EUR_DAILY_LIMIT = 5000  # Daily payout limit in EUR

def create_stripe_payout(amount: float, currency: str):
    """
    Handles payouts:
    1. USD inflows → send as EUR (Stripe auto-converts).
    2. EUR payouts → obey EUR_DAILY_LIMIT, remainder to GBP.
    3. Other currencies → direct to their linked bank accounts.
    """
    try:
        currency = currency.upper()
        logger.info(f"Processing payout request: {amount} {currency}")

        # STEP 1: USD inflows → Stripe auto-converts to EUR
        if currency == "USD":
            logger.info(f"USD inflow detected. Sending {amount} USD as EUR for auto conversion.")
            return create_stripe_payout(amount, "EUR")

        # STEP 2: EUR payouts with daily limit
        if currency == "EUR":
            payouts = []
            eur_bank_id = os.getenv("EUR_BANK_ID")
            gbp_bank_id = os.getenv("GBP_BANK_ID")

            if amount <= EUR_DAILY_LIMIT:
                logger.info(f"{amount} EUR is within daily limit. Sending to EUR account.")
                payouts.append(_payout(amount, "eur", eur_bank_id))
            else:
                logger.info(f"{amount} EUR exceeds {EUR_DAILY_LIMIT} daily limit. Splitting payout.")
                payouts.append(_payout(EUR_DAILY_LIMIT, "eur", eur_bank_id))
                remaining_amount = amount - EUR_DAILY_LIMIT
                logger.info(f"Routing remaining {remaining_amount} EUR to GBP account.")
                payouts.append(_payout(remaining_amount, "gbp", gbp_bank_id))
            return payouts

        # STEP 3: Other currencies
        logger.info(f"Routing {amount} {currency} to linked account.")
        return _payout(amount, currency.lower(), os.getenv(f"{currency}_BANK_ID"))

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error during payout: {e}")
        return {"error": str(e)}


def _payout(amount, currency, destination=None):
    """
    Helper to create a Stripe payout.
    """
    amount_smallest_unit = int(amount * 100)
    payout_data = {
        "amount": amount_smallest_unit,
        "currency": currency,
        "method": "standard",
        "statement_descriptor": "Payouts"
    }

    if destination:
        payout_data["destination"] = destination
        logger.info(f"Using bank account ID: {destination}")
    else:
        logger.info(f"No destination set — using default payout account.")

    payout = stripe.Payout.create(**payout_data)
    logger.info(f"Payout created: ID={payout.id}, Status={payout.status}")
    return {
        "id": payout.id,
        "status": payout.status,
        "amount": payout.amount,
        "currency": payout.currency
    }
