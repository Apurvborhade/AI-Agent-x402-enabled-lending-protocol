// SPDX-License-Identifier: MIT
pragma solidity ^0.8.18;

import {Script} from "forge-std/Script.sol";
import {ERC20Mock} from "test/mocks/ERC20Mock.sol";

contract HelperConfig is Script {
    uint256 public constant LOCAL_BLOCKCHAIN_ID = 31337;
    uint256 public constant BASE_CHAIN_ID = 84531;

    uint256 public constant DEFAULT_ANVIL_KEY =
        uint256(uint160(address(0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266)));

    struct NetworkConfig {
        address stablecoin;
        uint256 deployerKey;
    }

    NetworkConfig public activeNetworkConfig;

    constructor() {
        if (block.chainid == LOCAL_BLOCKCHAIN_ID) {
            activeNetworkConfig = getLocalNetworkConfig();
        } else if (block.chainid == BASE_CHAIN_ID) {
            activeNetworkConfig = getBaseNetworkConfig();
        } else {
            revert("Unsupported chain ID");
        }
    }

    function getLocalNetworkConfig() internal returns (NetworkConfig memory) {
        vm.startBroadcast(DEFAULT_ANVIL_KEY);
        ERC20Mock mockStablecoin =
            new ERC20Mock("Mock Stablecoin", "mUSD", msg.sender, 1e24);
        vm.stopBroadcast();

        return NetworkConfig({
            stablecoin: address(mockStablecoin),
            deployerKey: DEFAULT_ANVIL_KEY
        });
    }

    function getBaseNetworkConfig() internal view returns (NetworkConfig memory) {
        return NetworkConfig({
            stablecoin: 0xE3F5a90F9cb311505cd691a46596599aA1A0AD7D, // real Base USDC.e
            deployerKey: vm.envUint("BASE_PRIVATE_KEY")
        });
    }
}
