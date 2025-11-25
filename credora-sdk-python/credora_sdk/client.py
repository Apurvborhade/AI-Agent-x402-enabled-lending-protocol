"""High-level Credora client that mirrors the TypeScript SDK."""

from __future__ import annotations

from typing import Any, Dict, Mapping, Optional, Sequence

from eth_account import Account # type: ignore
from eth_account.signers.local import LocalAccount # type: ignore
from web3 import Web3 # type: ignore

from .loans import LoanClient
from .payments import PaymentHandler


class CredoraClient:
    """Aggregate client bundling blockchain + payment helpers."""

    def __init__(
        self,
        rpc_url: str,
        private_key: str,
        loan_address: str,
        loan_abi: Sequence[Dict[str, Any]],
        *,
        request_timeout: int = 10,
        loan_tx_defaults: Optional[Dict[str, Any]] = None,
    ) -> None:
        provider = Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": request_timeout})
        self.web3 = Web3(provider)
        if not self.web3.is_connected():
            raise ConnectionError(f"Unable to reach RPC provider at {rpc_url}")

        self.account: LocalAccount = Account.from_key(private_key)


        self.loan = LoanClient(
            web3=self.web3,
            account=self.account,
            contract_address=loan_address,
            abi=loan_abi,
            tx_defaults=loan_tx_defaults,
        )
        self.payments = PaymentHandler()

    def handle_payment(self, response) -> Dict[str, Any]:
        error = response['error']
        accepts = response['accepts']

        if error != "insufficient_funds":
            return {"ok": False, "reason": "unexpected_payment_error", "error": error}


        if self.payments.is_insufficient_funds(response):
            details = self.payments.get_details(accepts[0])
            return {
                "ok": False,
                "reason": "insufficient_funds",
                "required": details.required,
                "payTo": details.pay_to,
                "asset": details.asset,
            }

        return {"ok": True, "payload": accepts}

    def auto_loan_and_retry_payment(
        self,
        borrower: str,
        headers: Mapping[str, str],
        *,
        fallback_amount_wei: Optional[int] = None,
    ) -> Dict[str, Any]:
        result = self.handle_payment(headers)
        
        print("Auto loan and retry payment result:", result)
        if result.get("ok"):
            return result

        if result.get("reason") != "insufficient_funds":
            return result

        amount = result.get("required") or fallback_amount_wei
        if amount is None:
            return {**result, "loanTaken": False, "reason": "missing_required_amount"}

        print(f"Taking loan of {amount} wei from Credora Loan contract...")
        receipt = self.loan.take_loan(borrower,int(amount))
        return {"ok": True, "loanTaken": True, "receipt": receipt}

