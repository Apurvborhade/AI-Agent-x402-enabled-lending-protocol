"""Loan client wrapping the Credora smart contract."""

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional, Sequence

from eth_account.signers.local import LocalAccount
from web3 import Web3
from web3.contract import Contract, ContractFunction
from web3.types import TxReceipt


class LoanClient:
    """Send transactions to the Credora Loan contract."""

    def __init__(
        self,
        web3: Web3,
        account: LocalAccount,
        contract_address: str,
        abi: Sequence[Dict[str, Any]],
        tx_defaults: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.web3 = web3
        self.account = account
        self.contract: Contract = web3.eth.contract(
            address=Web3.to_checksum_address(contract_address),
            abi=abi,
        )
        self.tx_defaults = tx_defaults or {}

    def take_loan(self, amount_wei: int) -> TxReceipt:
        """Call requestLoan on the contract."""
        fn = self.contract.functions.requestLoan(amount_wei)
        return self._send_transaction(fn)

    def repay(self, amount_wei: int) -> TxReceipt:
        fn = self.contract.functions.repayLoan(amount_wei)
        return self._send_transaction(fn)

    def get_loan(self, borrower: str) -> Any:
        return self.contract.functions.getLoan(
            Web3.to_checksum_address(borrower)
        ).call()

    # internal helpers -----------------------------------------------------

    def _send_transaction(self, fn: ContractFunction) -> TxReceipt:
        tx_params = self._build_tx_params()
        tx = fn.build_transaction(tx_params)
        signed = self.account.sign_transaction(tx)
        tx_hash = self.web3.eth.send_raw_transaction(signed.rawTransaction)
        return self.web3.eth.wait_for_transaction_receipt(tx_hash)

    def _build_tx_params(self) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "from": self.account.address,
            "nonce": self.web3.eth.get_transaction_count(self.account.address),
            "chainId": self.web3.eth.chain_id,
        }

        if "maxFeePerGas" not in self.tx_defaults and "gasPrice" not in self.tx_defaults:
            params["gasPrice"] = self.web3.eth.gas_price

        params.update(self.tx_defaults)
        return params

