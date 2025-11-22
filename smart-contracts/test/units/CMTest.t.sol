// SPDX-License-Identifier: MIT
pragma solidity ^0.8.18;
import {Test, console} from "forge-std/Test.sol";
import {DeployLP} from "../../script/DeployLP.s.sol";
import {LendingPool} from "../../src/LendingPool.sol";
import {CreditManager} from "../../src/CreditManager.sol";
import {ERC20Mock} from "test/mocks/ERC20Mock.sol";

contract CMtest is Test {
    LendingPool public lendingPool;
    ERC20Mock public stablecoin;
    CreditManager public creditManager;
    address public USER = makeAddr("user");
    address public LIQUIDITY_PROVIDER = makeAddr("liquidityProvider");

    uint256 private constant INITIAL_CREDIT_SCORE = 800;

    event LoanRejected(address indexed borrower, uint256 loanId, string reason);

    function setUp() public {
        DeployLP deployLP = new DeployLP();
        (lendingPool, creditManager) = deployLP.run();
        stablecoin = ERC20Mock(address(lendingPool.stablecoin()));

        stablecoin.mint(LIQUIDITY_PROVIDER, 1000e18); // Mint 1 million tokens to USER
    }

    function testCMDeployment() public {
        assert(address(lendingPool) != address(0));
        assert(address(creditManager) != address(0));
        console.log("LendingPool deployed at:", address(lendingPool));
        console.log("LendingPool at:", address(creditManager.lendingPool()));
        // console.log("CreditManager deployed at:", creditManagerAddress);
        assert(address(creditManager.lendingPool()) == address(lendingPool));
        // assert(address(creditManager.stablecoin()) == address(stablecoin));
    }

    function testLoanIsRequested() public {
        vm.startPrank(LIQUIDITY_PROVIDER);
        ERC20Mock stablecoin = ERC20Mock(address(lendingPool.stablecoin()));
        uint256 depositAmount = 100e18;

        stablecoin.approve(address(lendingPool), depositAmount);
        lendingPool.deposit(depositAmount);

        vm.stopPrank();
        creditManager.requestLoan(USER, 10 ether);
        assertEq(creditManager.getUsers()[0], USER);
        assert(creditManager.getCreditScore(USER) < INITIAL_CREDIT_SCORE);
    }

    function testLoanRequestIsRevertedForLowCreditScore() public {
        creditManager._setCreditScore(USER, 600);
        vm.expectEmit(true, false, false, true);
        emit LoanRejected(USER, 1000 ether, "Insufficient credit score");

        creditManager.requestLoan(USER, 1000 ether);
    }

    function testLoanIsApprovedForHighCreditScore() public {
        vm.startPrank(LIQUIDITY_PROVIDER);
        ERC20Mock stablecoin = ERC20Mock(address(lendingPool.stablecoin()));
        uint256 depositAmount = 100e18;

        stablecoin.approve(address(lendingPool), depositAmount);
        lendingPool.deposit(depositAmount);

        vm.stopPrank();
        vm.startPrank(USER);
        creditManager._setCreditScore(USER, 750);
        creditManager.requestLoan(USER, 0.01 ether);
        vm.stopPrank();
        uint256 userBalance = stablecoin.balanceOf(USER);
        assertEq(userBalance, 0.01 ether);
    }

    function testCreditScoreUpdatedAfterLoanRequestApproval() public {
        vm.startPrank(LIQUIDITY_PROVIDER);
        ERC20Mock stablecoin = ERC20Mock(address(lendingPool.stablecoin()));
        uint256 depositAmount = 100e18;

        stablecoin.approve(address(lendingPool), depositAmount);
        lendingPool.deposit(depositAmount);

        vm.stopPrank();
        vm.startPrank(USER);
        creditManager._setCreditScore(USER, 750);
        creditManager.requestLoan(USER, 0.01 ether);
        vm.stopPrank();

        uint256 updatedScore = creditManager.getCreditScore(USER);
        assertEq(creditManager.s_totalBorrowed(USER), 0.01 ether);
        assert(updatedScore < 750); // Credit score should decrease after loan approval
    }

    function testCreditScoreIncreasesOnTimeRepayment() public {
        vm.startPrank(LIQUIDITY_PROVIDER);
        ERC20Mock stablecoin = ERC20Mock(address(lendingPool.stablecoin()));
        uint256 depositAmount = 100e18;

        stablecoin.approve(address(lendingPool), depositAmount);
        lendingPool.deposit(depositAmount);

        vm.stopPrank();

        vm.startPrank(USER);
        creditManager._setCreditScore(USER, 750);
        creditManager.requestLoan(USER, 0.01 ether);

        // Simulate repayment
        stablecoin.mint(USER, 100 ether); // Mint tokens to USER for repayment
        stablecoin.approve(address(creditManager), 1 ether);
        creditManager.repayLoan(USER, 0.01 ether, true); // onTime = true

        vm.stopPrank();

        uint256 updatedScore = creditManager.getCreditScore(USER);
        assert(updatedScore > 750); // Credit score should increase after on-time repayment
    }
}
