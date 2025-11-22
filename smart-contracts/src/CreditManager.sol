// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import {LendingPool} from "./LendingPool.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";

contract CreditManager {
    // Placeholder state variable
    address public owner;
    LendingPool public lendingPool;
    IERC20 public stablecoin;

    mapping(address => uint256) private s_creditScore;
    mapping(address => uint256) public s_totalBorrowed;
    mapping(address => uint256) public s_totalRepaid;
    mapping(address => uint256) private s_lateRepayments;
    address[] private s_users;

    uint256 private constant INITIAL_CREDIT_SCORE = 800;
    uint256 private constant LOAN_CREDIT_THRESHOLD = 700;

    // ------------------------------------------------
    //                 EVENTS REQUIRED
    // ------------------------------------------------
    event CreditScoreUpdated(address indexed user, uint256 newScore);
    event LoanApproved(address indexed borrower, uint256 loanId);
    event LoanRejected(address indexed borrower, uint256 loanId, string reason);
    event ReputationPenalty(address indexed borrower, uint256 newScore);
    event ReputationBoost(address indexed borrower, uint256 newScore);

    constructor(address lendingPoolAddress, address stablecoinAddress) {
        owner = msg.sender;
        lendingPool = LendingPool(lendingPoolAddress);
        stablecoin = IERC20(stablecoinAddress);
    }

    function requestLoan(address borrower, uint256 amount) external {
        s_users.push(borrower);

        if (s_creditScore[borrower] == 0) {
            s_creditScore[borrower] = INITIAL_CREDIT_SCORE;
        }

        bool approved = evaluateLoan(borrower, amount);
        if (approved) {
            onLoanTaken(borrower, amount);
        }
    }

    function evaluateLoan(
        address borrower,
        uint256 loanAmount
    ) internal returns (bool) {
        uint256 score = s_creditScore[borrower];
        // Simple evaluation logic based on credit score
        if (score >= LOAN_CREDIT_THRESHOLD) {
            lendingPool.provideLiquidityToLoan(borrower, loanAmount);
            emit LoanApproved(borrower, loanAmount);
            return true;
        } else {
            emit LoanRejected(
                borrower,
                loanAmount,
                "Insufficient credit score"
            );
            return false;
        }
    }

    function repayLoan(address borrower, uint256 amount, bool onTime) external {
        stablecoin.transferFrom(msg.sender, address(this), amount);

        stablecoin.approve(address(lendingPool), amount);
        lendingPool.receiveRepayment(address(this), amount);

        onLoanRepaid(borrower, amount, onTime);
    }

    function onLoanTaken(address borrower, uint256 amount) internal {
        s_totalBorrowed[borrower] += amount;
        // Decrease credit score slightly for taking a loan
        s_creditScore[borrower] = s_creditScore[borrower] > 10
            ? s_creditScore[borrower] - 10
            : 0;

        emit CreditScoreUpdated(borrower, s_creditScore[borrower]);
    }

    function onLoanRepaid(
        address borrower,
        uint256 amount,
        bool onTime
    ) internal {
        s_totalRepaid[borrower] += amount;
        if (onTime) {
            // Increase credit score for on-time repayment
            s_creditScore[borrower] += 20;
            emit ReputationBoost(borrower, s_creditScore[borrower]);
        } else {
            // Decrease credit score for late repayment
            s_lateRepayments[borrower] += 1;
            s_creditScore[borrower] = s_creditScore[borrower] > 30
                ? s_creditScore[borrower] - 30
                : 0;
            emit ReputationPenalty(borrower, s_creditScore[borrower]);
        }
        emit CreditScoreUpdated(borrower, s_creditScore[borrower]);
    }

    function _setCreditScore(address user, uint256 score) external {
        s_creditScore[user] = score;
    }

    function getUsers() external view returns (address[] memory) {
        return s_users;
    }

    function getCreditScore(address user) external view returns (uint256) {
        return s_creditScore[user];
    }
}
