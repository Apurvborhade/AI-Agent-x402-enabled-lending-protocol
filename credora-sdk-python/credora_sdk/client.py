"""High-level Credora client that mirrors the TypeScript SDK."""

from __future__ import annotations

from typing import Any, Dict, Mapping, MutableMapping, Optional, Sequence

from eth_account import Account
from eth_account.signers.local import LocalAccount
from web3 import Web3

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

    def handle_payment(self, headers: Mapping[str, str]) -> Dict[str, Any]:
        header_value = headers.get(self.payments.header_key)
        if not header_value:
            return {"ok": False, "reason": "missing_payment_header"}

        decoded = self.payments.parse_x402(header_value)
        if self.payments.is_insufficient_funds(decoded):
            details = self.payments.get_details(decoded)
            return {
                "ok": False,
                "reason": "insufficient_funds",
                "required": details.required,
                "payTo": details.pay_to,
                "asset": details.asset,
            }

        return {"ok": True, "payload": decoded}

    def auto_loan_and_retry_payment(
        self,
        headers: Mapping[str, str],
        *,
        fallback_amount_wei: Optional[int] = None,
    ) -> Dict[str, Any]:
        result = self.handle_payment(headers)
        if result.get("ok"):
            return result

        if result.get("reason") != "insufficient_funds":
            return result

        amount = result.get("required") or fallback_amount_wei
        if amount is None:
            return {**result, "loanTaken": False, "reason": "missing_required_amount"}

        receipt = self.loan.take_loan(int(amount))
        return {"ok": True, "loanTaken": True, "receipt": receipt}

