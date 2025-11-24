import express from 'express';
import cors from 'cors'
import { paymentMiddleware } from "x402-express";
import { exact } from 'x402/dist/cjs/schemes';
import {
  Network,
  PaymentPayload,
  PaymentRequirements,
  Price,
  Resource,
  settleResponseHeader,
} from 'x402/dist/cjs/types/index'
import { useFacilitator } from 'x402/dist/cjs/verify'
import { processPriceToAtomicAmount, findMatchingPaymentRequirements } from "x402/dist/cjs/shared";
import dotenv from 'dotenv';


dotenv.config();
const app = express();
const PORT = process.env.PORT || 3000;

const facilitatorUrl = process.env.FACILITATOR_URL as Resource;
const payTo = process.env.ADDRESS as `0x${string}`;

app.use(cors())
app.use(express.json())



const premiumData = {
  plan: 'Gold',
  features: [
    'Ad-free experience',
    'Priority support',
    'Exclusive content drops',
  ],
  price: '$9.99/mo',
};

app.use(paymentMiddleware(
  payTo, // your receiving wallet address
  {  // Route configurations for protected endpoints
    "GET /premium": {
      // USDC amount in dollars
      price: "$10.001",
      network: "base-sepolia",
    },
  },
  {
    url: facilitatorUrl, // Facilitator URL for Base Sepolia testnet.
  }
));

app.get('/premium', (req: any, res) => {
  console.log(req.payment)
  res.json({
    status: 'success',
    data: premiumData,
  });
});

app.listen(PORT, () => {
  console.log(`Premium API listening on http://localhost:${PORT}`);
});
