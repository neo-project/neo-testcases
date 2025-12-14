#
# testcases/ledger/get_tx_from_block.py file belongs to the neo project and is free
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


# Operation: this case tests the getTransactionFromBlock method in Ledger contract.
# Method:GetTransactionFromBlock(byte[] blockIndexOrHash, int txIndex) -> Transaction or null
#  1. The blockIndexOrHash cannot be null.
#  2. The txIndex must between [0, block.transactions.length).
#  3. If current-block-index - block-index < max-traceable-blocks, it will return null.
#  4. If the block is not found, it will return null.
#  5. if the blockIndexOrHash.length is 32, it will be treated as a block hash.
#  6. if the blockIndexOrHash.length less than 32, it will be treated as a block index and must be in [0, uint32.MaxValue].
#  7. If the blockIndexOrHash.length greater than 32, it will fail.
# Expect Result: The getTransactionFromBlock method is working as expected.
class TxFromBlock(Testing):
    def __init__(self):
        super().__init__("TxFromBlock")

    def _check_argument_null(self):
        # Step 1: check argument null with blockIndexOrHash is null
        result = self.client.invoke_function(LEDGER_CONTRACT_HASH, "getTransactionFromBlock",
                                             [{'type': 'ByteArray'}, {'type': 'Integer', 'value': 0}])
        self.logger.info(f"GetTransactionFromBlock with null blockIndexOrHash result: {result}")
        assert 'exception' in result and 'Object reference not set to an instance of an object' in result['exception']

        # Step 2: check argument null with txIndex is null
        block_index = base64.b64encode(b'\x01').decode('utf-8')
        result = self.client.invoke_function(LEDGER_CONTRACT_HASH, "getTransactionFromBlock",
                                             [{'type': 'ByteArray', 'value': block_index}, {'type': 'Integer'}])
        self.logger.info(f"GetTransactionFromBlock with null txIndex result: {result}")
        assert 'exception' in result and 'Specified cast is not valid' in result['exception']

    def _check_block_index(self):
        # Step 1: check block index out of range
        height = base64.b64encode(b'\x01').decode('utf-8')
        result = self.client.invoke_function(LEDGER_CONTRACT_HASH, "getTransactionFromBlock",
                                             [{'type': 'ByteArray', 'value': height}, {'type': 'Integer', 'value': -1}])
        self.logger.info(f"GetTransactionFromBlock with txIndex out of range result: {result}")
        assert 'exception' in result and 'argument was out of the range of valid values' in result['exception']

        height = base64.b64encode(b'\x00\x00\x00\x00\x01').decode('utf-8')
        result = self.client.invoke_function(LEDGER_CONTRACT_HASH, "getTransactionFromBlock",
                                             [{'type': 'ByteArray', 'value': height}, {'type': 'Integer', 'value': 0}])
        self.logger.info(f"GetTransactionFromBlock with txIndex out of range result: {result}")
        assert 'exception' in result and 'Value was either too large or too small for a UInt32' in result['exception']

    def _check_block_hash_too_long(self):
        # Step 1: check block hash too long
        hash = base64.b64encode(b'0' * 33).decode('utf-8')
        result = self.client.invoke_function(LEDGER_CONTRACT_HASH, "getTransactionFromBlock",
                                             [{'type': 'ByteArray', 'value': hash}, {'type': 'Integer', 'value': 0}])
        self.logger.info(f"GetTransactionFromBlock with block hash too long result: {result}")
        assert 'exception' in result and 'Invalid indexOrHash length' in result['exception']

    def run_test(self):
        self._check_argument_null()
        self._check_block_index()
        self._check_block_hash_too_long()

        # TODO: check normal cases


# Run with: python3 -B -m testcases.ledger.get_tx_from_block
if __name__ == "__main__":
    test = TxFromBlock()
    test.run()
