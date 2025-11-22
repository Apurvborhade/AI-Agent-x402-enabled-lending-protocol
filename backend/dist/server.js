"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = __importDefault(require("express"));
const cors_1 = __importDefault(require("cors"));
const x402_express_1 = require("x402-express");
const app = (0, express_1.default)();
const PORT = process.env.PORT || 3000;
app.use((0, cors_1.default)());
app.use(express_1.default.json());
const premiumData = {
    plan: 'Gold',
    features: [
        'Ad-free experience',
        'Priority support',
        'Exclusive content drops',
    ],
    price: '$9.99/mo',
};
app.use((0, x402_express_1.paymentMiddleware)("0x4ec137a8be0466c166997bcfc56ffdafc542201b", // your receiving wallet address
{
    "GET /premium": {
        // USDC amount in dollars
        price: "$0.001",
        network: "base-sepolia",
    },
}, {
    url: "https://x402.org/facilitator", // Facilitator URL for Base Sepolia testnet.
}));
app.get('/premium', (req, res) => {
    res.json({
        status: 'success',
        data: premiumData,
    });
});
app.listen(PORT, () => {
    console.log(`Premium API listening on http://localhost:${PORT}`);
});
