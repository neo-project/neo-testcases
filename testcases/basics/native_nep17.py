# Copyright (C) 2015-2025 The Neo Project.
#
# testcases/basics/nep17.py file belongs to the neo project and is free
# software distributed under the MIT software license, see the
# accompanying file LICENSE in the main directory of the
# repository or http://www.opensource.org/licenses/mit-license.php
# for more details.
#
# Redistribution and use in source and binary forms with or without
# modifications are permitted.


import base64

from neo.contract import GAS_CONTRACT_HASH, NEO_CONTRACT_HASH
from testcases.basics.base import BasicsTesting


# Operation: check the NEO and GAS token basics.
#  1. The NEO token symbol should be NEO,
#    totalSupply should be 100000000,
#    decimals should be 0.
#  2. The GAS token symbol should be GAS,
#   totalSupply should be dynamic, and increased by the gas per block each block(current policy, maybe changed in the future),
#   decimals should be 8.
#
# Run this testcase cannot concurrently with other testcases.
# Expect Result: The NEO and GAS token basics are correct.
class NativeNep17(BasicsTesting):
    def __init__(self):
        super().__init__("NativeNep17")
        self.claimed_gas_per_block = 5 * 1000_0000  # 0.5 GAS per block

    def _check_neo_token_basics(self):
        # Step 1: check the NEO token symbol
        result = self.client.invoke_function(NEO_CONTRACT_HASH, 'symbol', [])
        self.logger.info(f"NEO token symbol: {result}")

        symbol = base64.b64decode(result['stack'][0]['value']).decode('utf-8')
        assert symbol == 'NEO', f"Expected NEO, got {symbol}"

        # Step 2: check the NEO token totalSupply
        result = self.client.invoke_function(NEO_CONTRACT_HASH, 'totalSupply', [])
        self.logger.info(f"NEO token totalSupply: {result}")

        totalSupply = result['stack'][0]['value']
        assert totalSupply == '100000000', f"Expected 100000000, got {totalSupply}"

        # Step 3: check the NEO token decimals
        result = self.client.invoke_function(NEO_CONTRACT_HASH, 'decimals', [])
        self.logger.info(f"NEO token decimals: {result}")

        decimals = result['stack'][0]['value']
        assert decimals == '0', f"Expected 0, got {decimals}"

        # Step 4: check the NEO token name
        result = self.client.invoke_function(NEO_CONTRACT_HASH, 'name', [])
        self.logger.info(f"NEO token name: {result}")

    def _check_gas_token_basics(self):
        # Step 1: check the GAS token symbol
        result = self.client.invoke_function(GAS_CONTRACT_HASH, 'symbol', [])
        self.logger.info(f"GAS token symbol: {result}")

        symbol = base64.b64decode(result['stack'][0]['value']).decode('utf-8')
        assert symbol == 'GAS', f"Expected GAS, got {symbol}"

        # Step 2: check the GAS token totalSupply
        result = self.client.invoke_function(GAS_CONTRACT_HASH, 'totalSupply', [])
        self.logger.info(f"GAS token totalSupply: {result}")

        # Cannot assert the totalSupply now, because it is dynamic.
        # totalSupply = result['stack'][0]['value']

        # Step 3: check the GAS token decimals
        result = self.client.invoke_function(GAS_CONTRACT_HASH, 'decimals', [])
        self.logger.info(f"GAS token decimals: {result}")

        decimals = result['stack'][0]['value']
        assert decimals == '8', f"Expected 8, got {decimals}"

    def _check_claimed_gas_per_block(self):
        # Step 1: check the GAS token totalSupply
        block_index = self.client.get_block_index()
        result = self.client.invoke_function(GAS_CONTRACT_HASH, 'totalSupply', [])
        self.logger.info(f"GAS token totalSupply in block {block_index}: {result}")

        total_supply = int(result['stack'][0]['value'])

        # Step 2: wait for the next block
        block_index = self.wait_next_block(block_index)

        # Step 3: check the GAS token totalSupply
        result = self.client.invoke_function(GAS_CONTRACT_HASH, 'totalSupply', [])
        self.logger.info(f"GAS token totalSupply in block {block_index}: {result}")

        total_supply_next = int(result['stack'][0]['value'])
        assert total_supply_next == total_supply + self.claimed_gas_per_block, \
            f"Expected {total_supply + self.claimed_gas_per_block}, got {total_supply_next}"

    def run_test(self):
        self._check_neo_token_basics()
        self._check_gas_token_basics()
        self._check_claimed_gas_per_block()


# Run with: python3 -B -m testcases.basics.native_nep17
if __name__ == "__main__":
    test = NativeNep17()
    test.run()
