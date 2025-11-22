// SPDX-License-Identifier: MIT
pragma solidity ^0.8.18;
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";

error LendingPool__InvalidDepositAmount();
error LendingPool__InvalidWithdrawalAmount();
error LendingPool_OnlyCreditManager();
error LendingPool__NotEnoughLiquidity();
error LendingPool_OnlyOwner();
error LendingPool__EmergencyWithdrawFailed();

contract LendingPool {
    IERC20 public stablecoin;
    mapping(address => uint256) public s_deposits;
    uint256 public s_totalLiquidity;
    address public s_creditManager;
    address public s_owner;

    // Events
    event Deposited(address indexed lender, uint256 amount);
    event LiquidityProvided(uint256 amount);
    event Withdrawn(address indexed lender, uint256 amount);
    event LiquidityReduced(uint256 amount);
    event EmergencyWithdraw(address indexed admin, uint256 amount);

    modifier onlyCreditManager() {
        _onlyCreditManager();
        _;
    }

    function _onlyCreditManager() internal view {
        if (msg.sender != s_creditManager) {
            revert LendingPool_OnlyCreditManager();
        }
    }

    modifier onlyOwner() {
        _onlyOwner();
        _;
    }

    function _onlyOwner() internal {
        if (msg.sender != s_owner) {
            revert LendingPool_OnlyOwner();
        }
    }

    constructor(address stablecoinAddress, address creditManagerAddress) {
        stablecoin = IERC20(stablecoinAddress);
        s_creditManager = creditManagerAddress;
        s_owner = msg.sender;
    }

    function setCreditManager(address creditManagerAddress) external onlyOwner {
        s_creditManager = creditManagerAddress;
    }

    // Deposit function
    function deposit(uint256 amount) external {
        if (amount <= 0) {
            revert LendingPool__InvalidDepositAmount();
        }
        stablecoin.transferFrom(msg.sender, address(this), amount);
        s_deposits[msg.sender] += amount;
        s_totalLiquidity += amount;

        // Emit Deposited and LiquidityProvided events
        emit Deposited(msg.sender, amount);
        emit LiquidityProvided(amount);
    }

    // Withdraw function
    function withdraw(uint256 amount) external {
        if (amount <= 0 || amount > s_deposits[msg.sender]) {
            revert LendingPool__InvalidWithdrawalAmount();
        }
        s_deposits[msg.sender] -= amount;
        s_totalLiquidity -= amount;
        stablecoin.transfer(msg.sender, amount);

        emit Withdrawn(msg.sender, amount);
        emit LiquidityReduced(amount);
    }

    // Borrow function
    function provideLiquidityToLoan(address to, uint256 amount) external onlyCreditManager {
        if (s_totalLiquidity < amount) {
            revert LendingPool__NotEnoughLiquidity();
        }
        s_totalLiquidity -= amount;
        stablecoin.transfer(to, amount);

        emit LiquidityReduced(amount);
    }

    // Repay function
    function receiveRepayment(address borrower, uint256 amount) external onlyCreditManager {
        stablecoin.transferFrom(borrower, address(this), amount);
        s_totalLiquidity += amount;

        emit LiquidityProvided(amount);
    }

    // Emergency Withdraw function
    function emergencyWithdraw(uint256 amount) external onlyOwner {
        if (s_totalLiquidity < amount) {
            revert LendingPool__EmergencyWithdrawFailed();
        }
        s_totalLiquidity -= amount;
        stablecoin.transfer(s_owner, amount);

        emit EmergencyWithdraw(msg.sender, amount);
    }
}
