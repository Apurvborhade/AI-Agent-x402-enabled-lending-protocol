// SPDX-License-Identifier: MIT
pragma solidity ^0.8.18;

import {LendingPool} from "src/LendingPool.sol";
import {HelperConfig} from "script/HelperConfig.s.sol";
import {Test, console} from "forge-std/Test.sol";
import {DeployLP} from "script/DeployLP.s.sol";
import {ERC20Mock} from "test/mocks/ERC20Mock.sol";

error LendingPool__InvalidDepositAmount();
error LendingPool__InvalidWithdrawalAmount();
error LendingPool_OnlyCreditManager();
error LendingPool__NotEnoughLiquidity();
error LendingPool_OnlyOwner();
error LendingPool__EmergencyWithdrawFailed();

contract LPTest is Test {
    LendingPool public lendingPool;
    ERC20Mock public stablecoin;
    address public USER = makeAddr("user");

    function setUp() public {
        DeployLP deployLP = new DeployLP();
        (lendingPool,) = deployLP.run();

        stablecoin = ERC20Mock(address(lendingPool.stablecoin()));
        stablecoin.mint(USER, 1000e18); // Mint 1 million tokens to USER
    }

    function testDeployment() public {
        HelperConfig helperConfig = new HelperConfig();
        (address stablecoin, uint256 deployerKey) = helperConfig.activeNetworkConfig();
        vm.startPrank(USER);
        LendingPool deployedLendingPool = new LendingPool(stablecoin, address(0));

        assert(address(deployedLendingPool.stablecoin()) == stablecoin);
        assert(deployedLendingPool.s_creditManager() == address(0));
        assert(deployedLendingPool.s_owner() == USER);
        assert(deployedLendingPool.s_totalLiquidity() == 0);
        vm.stopPrank();
    }

    function testDepositRevertsIfAmountIsZero() public {
        vm.startPrank(USER);
        ERC20Mock stablecoin = ERC20Mock(address(lendingPool.stablecoin()));
        stablecoin.approve(address(lendingPool), 100e18);

        vm.expectRevert(LendingPool__InvalidDepositAmount.selector);
        lendingPool.deposit(0);
        vm.stopPrank();
    }

    function testUserCanDepositSuccessfully() public {
        vm.startPrank(USER);
        ERC20Mock stablecoin = ERC20Mock(address(lendingPool.stablecoin()));
        uint256 depositAmount = 100e18;

        stablecoin.approve(address(lendingPool), depositAmount);
        lendingPool.deposit(depositAmount);
        uint256 userDeposit = lendingPool.s_deposits(USER);
        uint256 totalLiquidity = lendingPool.s_totalLiquidity();

        assert(userDeposit == depositAmount);
        assert(totalLiquidity == depositAmount);

        vm.stopPrank();
    }

    function testWithdrawIfWithdrawAmountIsZero() public {
        vm.startPrank(USER);
        vm.expectRevert(LendingPool__InvalidWithdrawalAmount.selector);
        lendingPool.withdraw(0);
        vm.stopPrank();
    }

    function testWithdrawIfWithdrawAmountExceedsDeposit() public {
        vm.startPrank(USER);
        uint256 depositAmount = 100e18;
        uint256 withdrawAmount = 150e18;

        stablecoin.approve(address(lendingPool), depositAmount);
        lendingPool.deposit(depositAmount);

        vm.expectRevert(LendingPool__InvalidWithdrawalAmount.selector);
        lendingPool.withdraw(withdrawAmount);
        vm.stopPrank();
    }

    function testUserCanWithdrawSuccessfully() public {
        vm.startPrank(USER);
        uint256 depositAmount = 100e18;
        uint256 withdrawAmount = 60e18;

        stablecoin.approve(address(lendingPool), depositAmount);
        lendingPool.deposit(depositAmount);

        lendingPool.withdraw(withdrawAmount);
        uint256 userDeposit = lendingPool.s_deposits(USER);
        uint256 totalLiquidity = lendingPool.s_totalLiquidity();

        assert(userDeposit == (depositAmount - withdrawAmount));
        assert(totalLiquidity == (depositAmount - withdrawAmount));

        vm.stopPrank();
    }

    function testProvideLiquidityToLoanRevertsIfNotCreditManager() public {
        vm.startPrank(USER);
        vm.expectRevert(LendingPool_OnlyCreditManager.selector);
        lendingPool.provideLiquidityToLoan(address(1), 50e18);
        vm.stopPrank();
    }

    function testProvideLiquidityToLoanRevertsIfAmountExceedsLiquidity() public {
        vm.startPrank(lendingPool.s_creditManager());
        uint256 depositAmount = 100e18;
        stablecoin.mint(lendingPool.s_creditManager(), depositAmount); // Ensure lending pool has zero liquidity
        stablecoin.approve(address(lendingPool), depositAmount);
        lendingPool.deposit(depositAmount);
        vm.expectRevert(LendingPool__NotEnoughLiquidity.selector);
        lendingPool.provideLiquidityToLoan(address(1), 150e18);

        vm.stopPrank();
    }

    function testProvideLiquidityToLoanSuccessfully() public {
        vm.startPrank(USER);
        uint256 depositAmount = 200e18;
        stablecoin.approve(address(lendingPool), depositAmount);
        lendingPool.deposit(depositAmount);
        vm.stopPrank();

        vm.startPrank(lendingPool.s_creditManager());
        uint256 borrowAmount = 120e18;
        lendingPool.provideLiquidityToLoan(address(1), borrowAmount);

        uint256 totalLiquidity = lendingPool.s_totalLiquidity();
        assert(totalLiquidity == (depositAmount - borrowAmount));

        vm.stopPrank();
    }

    /*
              5. receiveRepayment Tests
              -------------------------
              ✓ Successful Repayment:
              - Only creditManager can call.
              - s_totalLiquidity increases by amount.
              - stablecoin.transferFrom called on creditManager.
              - Should emit LiquidityProvided event.

              ✗ Reverts:
              - Called by non-creditManager → LendingPool_OnlyCreditManager.

    */
    function testRecieveRepaymentRevertsIfNotCreditManager() public {
        vm.startPrank(USER);
        vm.expectRevert(LendingPool_OnlyCreditManager.selector);
        lendingPool.receiveRepayment(USER, 50e18);
        vm.stopPrank();
    }

    function testRecieveRepaymentSuccessfully() public {
        vm.startPrank(USER);
        uint256 depositAmount = 200e18;
        stablecoin.approve(address(lendingPool), depositAmount);
        lendingPool.deposit(depositAmount);
        vm.stopPrank();

        vm.startPrank(lendingPool.s_creditManager());
        uint256 borrowAmount = 120e18;
        lendingPool.provideLiquidityToLoan(address(1), borrowAmount);

        // Now test repayment
        stablecoin.mint(lendingPool.s_creditManager(), borrowAmount); // Mint tokens to credit manager for repayment
        stablecoin.approve(address(lendingPool), borrowAmount);
        lendingPool.receiveRepayment(lendingPool.s_creditManager(), borrowAmount);

        uint256 totalLiquidity = lendingPool.s_totalLiquidity();
        assert(totalLiquidity == depositAmount); // Liquidity should be back to initial deposit

        vm.stopPrank();
    }
    /*

          8. Event Emission Tests
          -----------------------
          - deposit → Deposited + LiquidityProvided.
          - withdraw → Withdrawn + LiquidityReduced.
          - borrow → LiquidityReduced.
          - repay → LiquidityProvided.
          - emergency withdraw → EmergencyWithdraw.
          */

    function testDepositEmitsEvents() public {
        vm.startPrank(USER);
        uint256 amount = 100e18;

        stablecoin.approve(address(lendingPool), amount);

        // Expect Deposited event
        vm.expectEmit(true, false, false, true);
        emit LendingPool.Deposited(USER, amount);

        // Expect LiquidityProvided event
        vm.expectEmit(false, false, false, true);
        emit LendingPool.LiquidityProvided(amount);

        lendingPool.deposit(amount);

        vm.stopPrank();
    }

    function testWithdrawEmitsEvents() public {
        vm.startPrank(USER);
        uint256 amount = 100e18;
        stablecoin.approve(address(lendingPool), amount);
        lendingPool.deposit(amount);

        uint256 withdrawAmount = 60e18;

        // Expect Withdrawn event
        vm.expectEmit(true, false, false, true);
        emit LendingPool.Withdrawn(USER, withdrawAmount);

        // Expect LiquidityReduced event
        vm.expectEmit(false, false, false, true);
        emit LendingPool.LiquidityReduced(withdrawAmount);

        lendingPool.withdraw(withdrawAmount);

        vm.stopPrank();
    }

    function testBorrowEmitsLiquidityReducedEvent() public {
        // User deposits first
        vm.startPrank(USER);
        uint256 depositAmount = 200e18;
        stablecoin.approve(address(lendingPool), depositAmount);
        lendingPool.deposit(depositAmount);
        vm.stopPrank();

        // Borrow from credit manager
        vm.startPrank(lendingPool.s_creditManager());
        uint256 borrowAmount = 120e18;

        // Expect LiquidityReduced event
        vm.expectEmit(false, false, false, true);
        emit LendingPool.LiquidityReduced(borrowAmount);

        lendingPool.provideLiquidityToLoan(address(1), borrowAmount);

        vm.stopPrank();
    }

    function testRepaymentEmitsLiquidityProvidedEvent() public {
        // User deposits
        vm.startPrank(USER);
        uint256 depositAmount = 200e18;
        stablecoin.approve(address(lendingPool), depositAmount);
        lendingPool.deposit(depositAmount);
        vm.stopPrank();

        // Borrow & repay
        vm.startPrank(lendingPool.s_creditManager());
        uint256 borrowAmount = 120e18;

        lendingPool.provideLiquidityToLoan(address(1), borrowAmount);

        // Mint & approve repayment tokens
        stablecoin.mint(lendingPool.s_creditManager(), borrowAmount);
        stablecoin.approve(address(lendingPool), borrowAmount);

        // Expect LiquidityProvided event
        vm.expectEmit(false, false, false, true);
        emit LendingPool.LiquidityProvided(borrowAmount);

        lendingPool.receiveRepayment(lendingPool.s_creditManager(),borrowAmount);

        vm.stopPrank();
    }

    function testEmergencyWithdrawEmitsEvent() public {
        // User deposits
        vm.startPrank(USER);
        uint256 amount = 150e18;
        stablecoin.approve(address(lendingPool), amount);
        lendingPool.deposit(amount);
        vm.stopPrank();

        // Owner withdraws
        vm.startPrank(lendingPool.s_owner());
        uint256 withdrawAmount = 100e18;

        // Expect EmergencyWithdraw event
        vm.expectEmit(true, false, false, true);
        emit LendingPool.EmergencyWithdraw(lendingPool.s_owner(), withdrawAmount);

        lendingPool.emergencyWithdraw(withdrawAmount);

        vm.stopPrank();
    }
}
