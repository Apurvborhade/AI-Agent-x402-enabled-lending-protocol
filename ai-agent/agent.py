import asyncio
import os
from dotenv import load_dotenv
from eth_account import Account
from x402.clients.httpx import x402HttpxClient
from x402.clients.base import decode_x_payment_response, x402Client

load_dotenv()  # Load PRIVATE_KEY and BASE_URL

def custom_payment_selector(
    accepts, network_filter=None, scheme_filter=None, max_value=None
):
    """Custom payment selector that filters by network."""
    # Ignore the network_filter parameter for this example - we hardcode base-sepolia
    _ = network_filter

    # NOTE: In a real application, you'd want to dynamically choose the most
    # appropriate payment requirement based on user preferences, available funds,
    # network conditions, or other business logic rather than hardcoding a network.

    # Filter by base-sepolia network (testnet)
    return x402Client.default_payment_requirements_selector(
        accepts,
        network_filter="base-sepolia",
        scheme_filter=scheme_filter,
        max_value=max_value,
    )
# -----------------------------------------------------
# ASYNC: real API call using x402 payment protocol
# -----------------------------------------------------
async def call_premium_api():
    PRIVATE_KEY = os.getenv("PRIVATE_KEY")
    BASE_URL = os.getenv("BASE_URL")

    if not PRIVATE_KEY:
        print("❌ PRIVATE_KEY missing in .env")
        return

    if not BASE_URL:
        print("❌ BASE_URL missing in .env")
        return

    # Ethereum account for signing x402 payment
    account = Account.from_key(PRIVATE_KEY)

    print("🏦 Wallet:", account.address)
    print(f"➡️ Calling {BASE_URL}/premium using x402…")

    try:
        async with x402HttpxClient(
            account=account,
            base_url=BASE_URL,
            payment_requirements_selector=custom_payment_selector,
            
        ) as client:

            response = await client.get("/premium")

            print("📡 Status:", response.status_code)
            print("📦 Body:", await response.aread())

             # Check for payment response header
            if "X-Payment-Response" in response.headers:
                payment_response = decode_x_payment_response(
                    response.headers["X-Payment-Response"]
                )
                print(
                    f"Payment response transaction hash: {payment_response['transaction']}"
                )
            else:
                print("Warning: No payment response header found")
    except Exception as e:
        print("❌ ERROR during x402 request:", e)



# -----------------------------------------------------
# OPTIONAL: Allow running agent.py directly
# -----------------------------------------------------
if __name__ == "__main__":
    asyncio.run(call_premium_api())
