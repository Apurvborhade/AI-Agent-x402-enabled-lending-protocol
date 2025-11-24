## Credora Python SDK

This package mirrors the TypeScript SDK and wraps the Credora smart-contract
loan workflow together with helper utilities for handling the `x-payment`
header during Lightning-style payment retries.

### Installation

```bash
pip install .  # from the repo root
```

### Quickstart

```python
from credora_sdk import CredoraClient

client = CredoraClient(
    rpc_url="https://sepolia.infura.io/v3/<key>",
    private_key="<hex private key>",
    loan_address="0x1234...",
    loan_abi=json.load(open("Loan.json"))["abi"],
)

result = client.auto_loan_and_retry_payment(request.headers)
if not result["ok"]:
    raise RuntimeError(result["reason"])
```

### Local Development

```
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

### Features

- `LoanClient` for `requestLoan`, `repayLoan`, and `getLoan`
- `PaymentHandler` to decode and inspect `x-payment` payloads
- `CredoraClient` orchestrator that retries failed payments by taking a loan automatically

