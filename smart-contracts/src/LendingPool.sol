// SPDX-License-Identifier: MIT
pragma solidity ^0.8.18;
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";

contract LendingPool {
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

    constructor(address lendingPoolAddress, address stablecoinAddress) {
        owner = msg.sender;
        lendingPool = LendingPool(lendingPoolAddress);
        stablecoin = IERC20(stablecoinAddress);
    }
}
