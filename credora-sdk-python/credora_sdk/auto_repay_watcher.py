import asyncio
import time
from credora_sdk.loans import LoanClient 

CHECK_INTERVAL = 5  # seconds

class AutoRepayer:
    def __init__(self,loan:LoanClient,token_contract, wallet)->None:
        self.loan = loan
        self.token_contract = token_contract
        self.wallet = wallet
        self.last_balance = 0
        
        self.loan_pending = False
        self.last_loan_time = 0
        self.GRACE_SECONDS = 10

    async def get_balance(self):
        return self.token_contract.functions.balanceOf(self.wallet).call()      
    
    async def watch_and_repay(self):
        print("Starting auto-repay watcher...")
        self.last_balance = await self.get_balance()
        
        while True:
            await asyncio.sleep(CHECK_INTERVAL) 
           
            # 1. If loan was just taken → skip
            if self.loan_pending:
                if time.time() - self.last_loan_time < self.GRACE_SECONDS:
                    print("⏳ Grace period active. Skipping auto-repay.")
                    continue
                else:
                    print("Grace window ended → watcher active again")
                    self.loan_pending = False
                    
                    
            print("Checking balance for auto-repay...")
            current_balance = await self.get_balance()
            
            print(f"Current balance: {current_balance}, Last balance: {self.last_balance}")
            if current_balance > self.last_balance:
                gained = current_balance - self.last_balance
                
                print(f"Detected balance increase of {gained}. Initiating auto-repay...")
                
                outstanding = self.loan.get_outstanding(self.wallet)
                print(f"Outstanding loan amount: {outstanding}")
                if outstanding > 0:
                    print(f"Outstanding loan amount: {outstanding}. Repaying...")
                    repay_amount = min(gained, outstanding)
                    
                    print(f"➡️ Repaying {repay_amount} tokens...")
                    
                    try:
                        self.loan.allow_repay(outstanding)
                        print("Approval for repay succeeded.")
                        receipt = self.loan.repay(repay_amount,borrower=self.wallet,on_time=True)
                        print("Loan repaid tx:", receipt.transactionHash.hex())

                    except Exception as e:
                        print("Repay failed:", e)
                else:
                    print("✔️ No outstanding loan.")
             # Update last balance
            self.last_balance = current_balance
            
            

        