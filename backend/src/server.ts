import express from 'express';
import cors from 'cors'
import { paymentMiddleware } from "x402-express";

const app = express();
const PORT = process.env.PORT || 3000;

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
  "0x4ec137a8be0466c166997bcfc56ffdafc542201b", // your receiving wallet address
  {  // Route configurations for protected endpoints
      "GET /premium": {
        // USDC amount in dollars
        price: "$0.001",
        network: "base-sepolia",
      },
    },
  {
    url: "https://x402.org/facilitator", // Facilitator URL for Base Sepolia testnet.
  }
));

app.get('/premium', (req, res) => {
  res.json({
    status: 'success',
    data: premiumData,
  });
});

app.listen(PORT, () => {
  console.log(`Premium API listening on http://localhost:${PORT}`);
});
