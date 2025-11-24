"""Loan client wrapping the Credora smart contract."""

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional, Sequence

from eth_account.signers.local import LocalAccount
from web3 import Web3
from web3.types import TxReceipt

try:  # web3<7 exposed Contract* at web3.contract, web3>=7 moved them under web3.contract.contract
    from web3.contract import Contract, ContractFunction
except ImportError:  # pragma: no cover - defensive fallback for newer web3 builds
    from web3.contract.contract import Contract, ContractFunction


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

    def take_loan(self, borrower: str, amount_wei: int) -> TxReceipt:
        """Call requestLoan on the contract."""
        fn = self.contract.functions.requestLoan(borrower,amount_wei)
        print(f"Built function call: {fn}")
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
        print(f"Transaction parameters: {tx_params}")
        tx = fn.build_transaction(tx_params)
        print(f"Built transaction: {tx}")
        signed = self.account.sign_transaction(tx)
        print(f"Signed transaction: {signed}")
        tx_hash = self.web3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt is None:
            raise Exception("Timeout waiting for transaction to be mined")

        if receipt.get("blockNumber") is None:
            raise Exception("Transaction still pending after timeout")
        return receipt

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

