import asyncio
import os
from dotenv import load_dotenv
from eth_account import Account
from x402.clients.httpx import x402HttpxClient

load_dotenv()  # Load PRIVATE_KEY

async def main():
    PRIVATE_KEY = os.getenv("PRIVATE_KEY")

    if not PRIVATE_KEY:
        print("❌ PRIVATE_KEY missing in .env")
        return

    # Create Ethereum account (x402 uses normal ETH signatures)
    account = Account.from_key(PRIVATE_KEY)

    # Create x402 client
    async with x402HttpxClient(
        account=account,
        base_url="http://localhost:3000"
    ) as client:

        print("➡️ Calling /premium with x402…")

        response = await client.get("/premium")

        print("📡 Status:", response.status_code)
        print("📦 Body:", await response.aread())

if __name__ == "__main__":
    asyncio.run(main())
