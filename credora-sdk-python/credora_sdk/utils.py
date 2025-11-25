import time
from credora_sdk import CredoraClient
from typing import Any, Dict, Mapping, MutableMapping, Optional, Sequence
from functools import lru_cache
from pathlib import Path

import httpx # type: ignore
from eth_account import Account # type: ignore
from x402.clients.httpx import x402HttpxClient # type: ignore
from web3.exceptions import ContractCustomError # type: ignore


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

def create_credora_client(
    private_key: str,
    resolve_abi_path,
    load_abi,
    loan_tx_defaults,
    credora_rpc_url:str,
    credora_loan_address:str,
) -> Optional[CredoraClient]:
    rpc_url = credora_rpc_url
    loan_address = credora_loan_address
    abi_path = resolve_abi_path()
    print(f"Creating CredoraClient with ABI path: {abi_path}")
    if not rpc_url or not loan_address:
        print("Credora SDK disabled: missing CREDORA_RPC_URL or CREDORA_LOAN_ADDRESS")
        return None

    try:
        abi = load_abi(abi_path)
        loan_defaults = loan_tx_defaults()
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


async def retry_with_credora(
    account: Account,
    response: httpx.Response,
    credora_client: Optional[CredoraClient],
    BASE_URL: str,
    method: str = "GET",
    endpoint: str = "",
    credora_fallback_loan_wei: Optional[int] = None,
    custom_payment_selector=Any,
    request_kwargs: Optional[Dict[str, Any]] = None,
    repay_watcher: Optional[Any] = None,
) -> httpx.Response:
    if not credora_client or response.status_code != 402:
        return response

    if not response.json().get('error'):
        print("402 Payment Required received from server, but no error details found.")
        return response
    
    if response.json()['error'] != "insufficient_funds":
        print("Payment required for unknown reason, not attempting Credora auto-loan.")
        return response
    
    print("402 Payment Required received from server.")
    
    fallback_amount = credora_fallback_loan_wei
    fallback_value = int(fallback_amount) if fallback_amount else None

    print("Payment requires additional funds. Attempting Credora auto-loan…")
    result = credora_client.auto_loan_and_retry_payment(
        account.address, response.json(), fallback_amount_wei=fallback_value
    )

    if not result.get("ok"):
        print(f"Credora auto-loan failed: {result}")
        return response

    if result.get("loanTaken"):
        receipt = result.get("receipt")
        tx_hash = receipt.transactionHash.hex() if receipt else "unknown"
        print(f"Credora loan executed. Tx hash: {tx_hash}")

        
        if repay_watcher:
            repay_watcher.loan_pending = True
            repay_watcher.last_loan_time = time.time()
            print("Watcher temporarily paused after loan; allowing API retry.")
            
    print("🔁 Retrying premium API call after funding wallet…")
    
    
    try:
        async with x402HttpxClient(
            account=account,
            base_url=BASE_URL,
            payment_requirements_selector=custom_payment_selector,
        ) as client:
            request_kwargs = request_kwargs or {}
            method = method.upper()
            
            if method == "GET":
                return await client.get(endpoint, **request_kwargs)
            elif method == "POST":
                return await client.post(endpoint, **request_kwargs)
            elif method == "PUT":
                return await client.put(endpoint, **request_kwargs)
            elif method == "DELETE":
                return await client.delete(endpoint, **request_kwargs)
            elif method == "PATCH":
                return await client.patch(endpoint, **request_kwargs)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
    except Exception as e:
        print("ERROR during x402 request:", pretty_error(e))





if __name__ == "__main__":
    # Example usage
    print("Testing utility functions...")
    
   
