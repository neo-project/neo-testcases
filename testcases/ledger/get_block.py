#
# testcases/ledger/get_block.py file belongs to the neo project and is free
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


# Operation: this case tests the getBlock method in Ledger contract.
# Method: GetBlock(byte[] indexOrHash) -> TrimmedBlock or null
#  1. The indexOrHash cannot be null.
#  2. If current-block-index - block-index < max-traceable-blocks, it will return null.
#  3. If the indexOrHash.length is 32, it will be treated as a block hash.
#  4. If the indexOrHash.length less than 32, it will be treated as a block index and must be in [0, uint32.MaxValue].
#  5. If the indexOrHash.length greater than 32, it will fail.
#  6. If the block is not found, it will return null.
#  7. If the block is found, it will return the trimmed block.
# Expect Result: The getBlock method is working as expected.
class GetBlock(Testing):
    def __init__(self):
        super().__init__("GetBlock")

    def _check_argument_null(self):
        # Step 1: check argument null with indexOrHash is null
        result = self.client.invoke_function(LEDGER_CONTRACT_HASH, "getBlock", [{'type': 'ByteArray'}])
        self.logger.info(f"GetBlock with null indexOrHash result: {result}")
        assert 'exception' in result and 'Object reference not set to an instance of an object' in result['exception']

    def _check_block_index_out_of_range(self):
        # Step 1: check block index out of range
        height = base64.b64encode(b'\x00\x00\x00\x00\x01').decode('utf-8')
        result = self.client.invoke_function(LEDGER_CONTRACT_HASH, "getBlock",
                                             [{'type': 'ByteArray', 'value': height}])
        self.logger.info(f"GetBlock with block index out of range result: {result}")
        assert 'exception' in result and 'Value was either too large or too small for a UInt32' in result['exception']

    def _check_block_hash_too_long(self):
        # Step 1: check block hash too long
        hash = base64.b64encode(b'0' * 33).decode('utf-8')
        result = self.client.invoke_function(LEDGER_CONTRACT_HASH, "getBlock",
                                             [{'type': 'ByteArray', 'value': hash}])
        self.logger.info(f"GetBlock with block hash too long result: {result}")
        assert 'exception' in result and 'Invalid indexOrHash length' in result['exception']

    def run_test(self):
        self._check_argument_null()
        self._check_block_index_out_of_range()
        self._check_block_hash_too_long()

        # TODO: check normal cases


# Run with: python3 -B -m testcases.ledger.get_block
if __name__ == "__main__":
    test = GetBlock()
    test.run()
