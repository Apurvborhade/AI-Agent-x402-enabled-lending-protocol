import { ethers } from 'ethers'

export class LoanClient {
    private contract: ethers.Contract;

    constructor(private signer: ethers.Wallet, address: string, abi: any) {
        this.contract = new ethers.Contract(address, abi, signer);
    }

    async takeLoan(amount: bigint) {
        const tx = await this.contract.requestLoan!(amount);
        return await tx.wait();
    }

    async repay(amount: bigint) {
        const tx = await this.contract.repayLoan!(amount);
        return await tx.wait();
    }

    async getLoan(address: string) {
        return await this.contract.getLoan!(address);
    }

}