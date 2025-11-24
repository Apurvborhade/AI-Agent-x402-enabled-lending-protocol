# Auto Loan & Retry Payment 

A fully modular Python SDK enabling AI agents and backend services to:

- Verify **x402 payment challenges**
- Automatically detect **insufficient funds**
- Request **on-chain loans** from Credora Protocol
- Automatically **retry x402 payments** once additional funds arrive
- Log all payment attempts and loan events for analytics

This SDK is built for automation, decentralised agents, and any system integrating x402 payments with crypto-based lending.

---

## ✨ Features

- 🔐 **Seamless x402 Client**
  - Challenge fetching
  - Signing & verification
  - Payment-response decoding

- 💰 **Auto Loan Request Flow**
  - Triggered when funds are insufficient
  - Requests loan via your smart contract

- 🔄 **Automatic Payment Retry**
  - Retries payment after loan confirmation
  - Optional backoff & timeout mechanisms

- 🧩 **Clean Modular Architecture**
  - Components are fully replaceable
  - Perfect for agents, microservices & automations

- 🗄️ **Built-in Storage Layer**
  - Saves payment attempts
  - Logs loan history & status changes

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```
### 2. Add .env
```
PRIVATE_KEY=your_private_key
RPC_URL=https://your-rpc
X402_API=https://your-x402-endpoint
LOAN_CONTRACT=0xYourLoanContract
DATABASE_URL=sqlite:///sdk.db

```

## SDK Architecture
### High-Level Diagram
                ┌───────────────────────────┐
                │     User Calls API         │
                └───────────┬───────────────┘
                            │
                            ▼
                ┌───────────────────────────┐
                │   x402 Challenge Created   │
                └───────────┬───────────────┘
                            │ verify()
                            ▼
         ┌────────────────────────────────────────┐
         │     Wallet Has Enough Funds?           │
         └───────────────┬────────────────────────┘
                         │ No
                         ▼
            ┌──────────────────────────────┐
            │ Request On-Chain Loan         │
            └──────────────┬───────────────┘
                           │ Loan received
                           ▼
                ┌──────────────────────────┐
                │  Retry x402 Payment       │
                └──────────────────────────┘








