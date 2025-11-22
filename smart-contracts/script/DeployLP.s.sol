// SPDX-License-Identifier: MIT
pragma solidity ^0.8.18;

import {Script} from "forge-std/Script.sol";
import {LendingPool} from "../src/LendingPool.sol";
import {CreditManager} from "../src/CreditManager.sol";
import {ERC20Mock} from "../test/mocks/ERC20Mock.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {HelperConfig} from "./HelperConfig.s.sol";

contract DeployLP is Script {
    function run() external returns (LendingPool, CreditManager) {
        HelperConfig helperConfig = new HelperConfig();

        (address stablecoinAddress, uint256 deployerKey) = helperConfig.activeNetworkConfig();

        vm.startBroadcast(deployerKey);

        // Deploy mock stablecoin
        IERC20 stablecoin =  IERC20(stablecoinAddress);

        // STEP 1 — Deploy LendingPool with placeholder
        LendingPool lendingPool = new LendingPool(stablecoinAddress, address(0));

        // STEP 2 — Deploy CreditManager with the real lendingPool address
        CreditManager creditManager = new CreditManager(address(lendingPool), stablecoinAddress);

        // STEP 3 — Update LendingPool with real CreditManager
        lendingPool.setCreditManager(address(creditManager));

        vm.stopBroadcast();

        return (lendingPool, creditManager);
    }
}
