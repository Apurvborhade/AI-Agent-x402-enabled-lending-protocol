export class PaymentHandler {
    parseX402(header: string) {
        const json = JSON.parse(Buffer.from(header, 'base64').toString());
        return json;
    }

    isInsufficientFunds(payload: any): boolean {
        return payload?.error === 'insufficient_funds'
    }
    getRequiredAmount(payload: any) {
        const accept = payload.accepts?.[0];
        return accept?.maxAmountRequired ? BigInt(accept.maxAmountRequired) : null;
    }

    getPayTo(payload: any) {
        return payload.accepts?.[0]?.payTo;
    }

    getAsset(payload: any) {
        return payload.accepts?.[0]?.asset;
    }
}