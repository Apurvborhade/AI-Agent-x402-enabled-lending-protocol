import asyncio
import json
import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

import httpx
from dotenv import load_dotenv
from eth_account import Account
from x402.clients.httpx import x402HttpxClient
from x402.clients.base import decode_x_payment_response, x402Client
from web3.exceptions import ContractCustomError

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SDK_PATH = PROJECT_ROOT / "credora-sdk-python"
if SDK_PATH.exists() and str(SDK_PATH) not in sys.path:
    sys.path.append(str(SDK_PATH))

from credora_sdk import CredoraClient

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


def pretty_error(err):
    # Case 1: Solidity Custom Error
    if isinstance(err, ContractCustomError):
        # err.args structure -> (message, data)
        # data contains the raw hex revert data
        message = err.args[0]
        data = err.args[1] if len(err.args) > 1 else None

        return {
            "type": "ContractCustomError",
            "message": message,
            "data": data,
        }

    # Case 2: inner tuple-like error
    if err.args and isinstance(err.args[0], tuple):
        inner = err.args[0]
        return {
            "type": "TupleError",
            "values": list(inner)
        }

    return {"type": "UnknownError", "message": str(err)}

async def call_premium_api():
    PRIVATE_KEY = os.getenv("PRIVATE_KEY")
    BASE_URL = os.getenv("BASE_URL")

    if not PRIVATE_KEY:
        print("PRIVATE_KEY missing in .env")
        return

    if not BASE_URL:
        print("BASE_URL missing in .env")
        return

    credora_client = _maybe_create_credora_client(PRIVATE_KEY)

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
        
            response = await _maybe_retry_with_credora(
                account,
                client,
                response,
                credora_client,
            )
            print("Retried", response.status_code)
            await _log_payment_response(response)
    except Exception as e:
        print("ERROR during x402 request:", pretty_error(e))


def _maybe_create_credora_client(private_key: str) -> Optional[CredoraClient]:
    rpc_url = os.getenv("CREDORA_RPC_URL")
    loan_address = os.getenv("CREDORA_LOAN_ADDRESS")
    abi_path = _resolve_abi_path()
    print(f"Creating CredoraClient with ABI path: {abi_path}")
    if not rpc_url or not loan_address:
        print("Credora SDK disabled: missing CREDORA_RPC_URL or CREDORA_LOAN_ADDRESS")
        return None

    try:
        abi = _load_abi(abi_path)
        loan_defaults = _loan_tx_defaults()
        return CredoraClient(
            rpc_url=rpc_url,
            private_key=private_key,
            loan_address=loan_address,
            loan_abi=abi,
            loan_tx_defaults=loan_defaults,
        )
    except Exception as exc:
        print(f"Failed to initialize Credora SDK: {exc}")
        return None


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


async def _maybe_retry_with_credora(
    account: Account,
    client: x402HttpxClient,
    response: httpx.Response,
    credora_client: Optional[CredoraClient],
) -> httpx.Response:
    if not credora_client or response.status_code != 402:
        return response

    if response.json()['error'] != "insufficient_funds":
        print("Payment required for unknown reason, not attempting Credora auto-loan.")
        return response
    print("402 Payment Required received from server.")
    fallback_amount = os.getenv("CREDORA_FALLBACK_LOAN_WEI")
    fallback_value = int(fallback_amount) if fallback_amount else None

    print("Payment requires additional funds. Attempting Credora auto-loan…")
    result = credora_client.auto_loan_and_retry_payment(
        account.address,response.json(), fallback_amount_wei=fallback_value
    )

    if not result.get("ok"):
        print(f"Credora auto-loan failed: {result}")
        return response

    if result.get("loanTaken"):
        receipt = result.get("receipt")
        tx_hash = receipt.transactionHash.hex() if receipt else "unknown"
        print(f"Credora loan executed. Tx hash: {tx_hash}")

    print("🔁 Retrying premium API call after funding wallet…")
    return await client.get("/premium")


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
