import asyncio
import json
import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

import httpx # type: ignore
from dotenv import load_dotenv # type: ignore
from eth_account import Account # type: ignore
from x402.clients.httpx import x402HttpxClient  # type: ignore
from x402.clients.base import decode_x_payment_response, x402Client     # type: ignore
from web3.exceptions import ContractCustomError # type: ignore

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SDK_PATH = PROJECT_ROOT / "credora-sdk-python"
if SDK_PATH.exists() and str(SDK_PATH) not in sys.path:
    sys.path.append(str(SDK_PATH))

from credora_sdk import CredoraClient # type: ignore
from credora_sdk.utils import create_credora_client # type: ignore
from credora_sdk.utils import retry_with_credora # type: ignore

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
DEFAULT_ABI_PATH = (
    PROJECT_ROOT
    / "smart-contracts"
    / "out"
    / "CreditManager.sol"
    / "CreditManager.json"
)




async def call_premium_api():
    PRIVATE_KEY = os.getenv("PRIVATE_KEY")
    BASE_URL = os.getenv("BASE_URL")
    CRDORA_RPC_URL = os.getenv("CREDORA_RPC_URL")
    CREDORA_LOAN_ADDRESS = os.getenv("CREDORA_LOAN_ADDRESS")
    
    if not CRDORA_RPC_URL and not CREDORA_LOAN_ADDRESS:
        print("CREDORA_RPC_URL or CREDORA_LOAN_ADDRESS missing in .env")
        return
    
    if not PRIVATE_KEY:
        print("PRIVATE_KEY missing in .env")
        return

    if not BASE_URL:
        print("BASE_URL missing in .env")
        return

    credora_client = create_credora_client(
        PRIVATE_KEY,
        resolve_abi_path=_resolve_abi_path,
        load_abi=_load_abi,
        loan_tx_defaults=_loan_tx_defaults,
        credora_rpc_url=CRDORA_RPC_URL,
        credora_loan_address=CREDORA_LOAN_ADDRESS,
    )

    # Ethereum account for signing x402 payment
    account = Account.from_key(PRIVATE_KEY)

    print("Wallet:", account.address)
    print(f"Calling {BASE_URL}/premium using x402…")

    try:
        async with x402HttpxClient(
            account=account,
            base_url=BASE_URL,
            payment_requirements_selector=custom_payment_selector,
            
        ) as client:

            response = await client.get("/premium")
        
            response = await retry_with_credora(
                account,
                response,
                credora_client,
                BASE_URL,
                method="GET",
                endpoint="/premium",
                credora_fallback_loan_wei=None,
                custom_payment_selector=custom_payment_selector,
                request_kwargs=None,
            )
            
            print("Retried", response.status_code)
            await _log_payment_response(response)
    except Exception as e:
        print("ERROR during x402 request:", e)





@lru_cache()
def _resolve_abi_path() -> Path:
    custom_path = os.getenv("CREDORA_LOAN_ABI_PATH")
    if custom_path:
        path = Path(custom_path).expanduser()
        if path.exists():
            return path
        raise FileNotFoundError(f"CREDORA_LOAN_ABI_PATH not found: {path}")

    if DEFAULT_ABI_PATH.exists():
        return DEFAULT_ABI_PATH

    raise FileNotFoundError(
        "Could not find loan ABI. Provide CREDORA_LOAN_ABI_PATH or compile smart contracts."
    )


@lru_cache()
def _load_abi(path: Path) -> Any:
    with path.open() as fp:
        data = json.load(fp)
    abi = data.get("abi")
    if not abi:
        raise ValueError(f"ABI missing in {path}")
    return abi


def _loan_tx_defaults() -> Optional[Dict[str, Any]]:
    max_fee = os.getenv("CREDORA_MAX_FEE_PER_GAS")
    priority_fee = os.getenv("CREDORA_MAX_PRIORITY_FEE_PER_GAS")
    gas_price = os.getenv("CREDORA_GAS_PRICE")

    tx: Dict[str, Any] = {}
    if gas_price:
        tx["gasPrice"] = int(gas_price)
    if max_fee:
        tx["maxFeePerGas"] = int(max_fee)
    if priority_fee:
        tx["maxPriorityFeePerGas"] = int(priority_fee)

    return tx or None


async def _log_payment_response(response: httpx.Response):
    print("Status:", response.status_code)
    print("Body:", await response.aread())
    print("Body:", response.headers)

    if "X-Payment-Response" in response.headers:
        payment_response = decode_x_payment_response(
            response.headers["X-Payment-Response"]
        )
        print(f"Payment response transaction hash: {payment_response['transaction']}")
    else:
        print("Warning: No payment response header found")


# -----------------------------------------------------
# OPTIONAL: Allow running agent.py directly
# -----------------------------------------------------
if __name__ == "__main__":
    asyncio.run(call_premium_api())
