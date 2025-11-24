import { LoanClient } from './loans/LoanClient'
import { PaymentHandler } from './payments/PaymentHandler'
import { ethers } from "ethers";

export class CredoraClient {
    loan: LoanClient;
    payments: PaymentHandler;
    signer: ethers.Wallet;

    constructor(config: {
        rpcUrl: string,
        privateKey: string,
        loanAddress: string,
        loanAbi: any
    }) {
        const provider = new ethers.JsonRpcProvider(config.rpcUrl);
        this.signer = new ethers.Wallet(config.privateKey, provider);

        this.loan = new LoanClient(
            this.signer,
            config.loanAddress,
            config.loanAbi
        );
        this.payments = new PaymentHandler();
    }

    async handlePayment(headers: any) {
        const xPayment = headers["x-payment"];

        if (!xPayment) return { ok: false, reason: "missing_payment_header" };

        const decoded = this.payments.parseX402(xPayment);

        if (decoded.error === "insufficient_funds") {
            return {
                ok: false,
                reason: "insufficient_funds",
                required: this.payments.getRequiredAmount(decoded),
                payTo: this.payments.getPayTo(decoded),
                asset: this.payments.getAsset(decoded),
            };
        }

        return { ok: true, payload: decoded };
    }

    async autoLoanAndRetryPayment(headers: any) {
        const result = await this.handlePayment(headers) as any;

        if (result.ok) return result;

        if (result.reason === "insufficient_funds") {
            console.log("Taking loan for:", result?.required.toString());

            await this.loan.takeLoan(result?.required);

            return { ok: true, loanTaken: true };
        }

        return result;
    }
}