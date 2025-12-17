#
# testcases/ledger/get_tx_height.py file belongs to the neo project and is free
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


# Operation: this case tests the getTxHeight method in Ledger contract.
# Method: GetTransactionHeight(UInt256 txHash) -> int
#  1. The txHash cannot be null.
#  2. If the txHash is not found or (current-height - the block height of the tx) > max-traceable-blocks, it will return -1.
#  3. If the txHash is found, it will return the block height of the tx.
# Expect Result: The getTxHeight method is working as expected.
class GetTxHeight(Testing):
    def __init__(self):
        super().__init__("GetTxHeight")

    def _check_argument_null(self):
        # Step 1: check argument null
        result = self.client.invoke_function(LEDGER_CONTRACT_HASH, "getTransactionHeight", [{'type': 'ByteArray'}])
        self.logger.info(f"GetTxHeight with null argument result: {result}")
        assert 'exception' in result and 'Object reference not set to an instance of an object' in result['exception']

    def _check_tx_hash_too_long(self):
        # Step 1: check tx hash too long
        hash = base64.b64encode(b'0' * 33).decode('utf-8')
        result = self.client.invoke_function(LEDGER_CONTRACT_HASH, "getTransactionHeight",
                                             [{'type': 'ByteArray', 'value': hash}])
        self.logger.info(f"GetTxHeight with tx hash too long result: {result}")
        assert 'exception' in result and 'Invalid UInt256 length' in result['exception']

    def run_test(self):
        self._check_argument_null()
        self._check_tx_hash_too_long()

        # TODO: check normal cases


# Run with: python3 -B -m testcases.ledger.get_tx_height
if __name__ == "__main__":
    test = GetTxHeight()
    test.run()
