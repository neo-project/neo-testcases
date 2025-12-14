#
# testcases/ledger/current_index_hash.py file belongs to the neo project and is free
# software distributed under the MIT software license, see the
# accompanying file LICENSE in the main directory of the
# repository or http://www.opensource.org/licenses/mit-license.php
# for more details.
#
# Redistribution and use in source and binary forms with or without
# modifications are permitted.

import base64
from neo.contract import *
from testcases.testing import Testing


# Operation: this case tests the currentIndexHash method in Ledger contract.
# Method: CurrentIndex() -> uint, CurrentHash() -> UInt256
#  1. The current index or hash will be returned.
#  2. The current index must be in [0, uint32.MaxValue].
#  3. The current hash must be a valid UInt256.
# Expect Result: The current index hash method is working as expected.
class CurrentIndexHash(Testing):
    def __init__(self):
        super().__init__("CurrentIndexHash")

    def run_test(self):
        # Step 1: check current index
        result = self.client.invoke_function(LEDGER_CONTRACT_HASH, "currentIndex", [])
        self.logger.info(f"CurrentIndex result: {result}")
        assert len(result['stack']) == 1, f"Expected 1 item in stack, got {len(result['stack'])}"
        assert result['stack'][0]['type'] == "Integer", f"Expected Integer, got {result['stack'][0]['type']}"
        index = int(result['stack'][0]['value'])
        assert index > 0, f"Expected current index to be greater than 0, got {index}"
        assert index < 0xFFFFFFFF, f"Expected current index to be less than 0xFFFFFFFF, got {index}"

        result = self.client.invoke_function(LEDGER_CONTRACT_HASH, "currentHash", [])
        self.logger.info(f"CurrentHash result: {result}")
        assert len(result['stack']) == 1, f"Expected 1 item in stack, got {len(result['stack'])}"
        assert result['stack'][0]['type'] == "ByteString", f"Expected ByteString, got {result['stack'][0]['type']}"
        hash = base64.b64decode(result['stack'][0]['value']).hex()
        assert len(hash) == 64, f"Expected 64 characters, got {len(hash)}"


# Run with: python3 -B -m testcases.ledger.current_index_hash
if __name__ == "__main__":
    test = CurrentIndexHash()
    test.run()
