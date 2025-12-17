#
# testcases/ledger/get_tx
# .py file belongs to the neo project and is free
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


# Operation: this case tests the getTx method in Ledger contract.
# Method: GetTransaction(UInt256 txHash) -> Transaction or null
#  1. The txHash cannot be null.
#  2. If the txHash is not found or (current-height - the block height of the tx) > max-traceable-blocks, it will return null.
#  3. If the txHash is found, it will return the tx.
# Expect Result: The getTx method is working as expected.
class GetTx(Testing):
    def __init__(self):
        super().__init__("GetTx")

    def _check_argument_null(self):
        # Step 1: check argument null
        result = self.client.invoke_function(LEDGER_CONTRACT_HASH, "getTransaction", [{'type': 'ByteArray'}])
        self.logger.info(f"GetTx with null argument result: {result}")
        assert 'exception' in result and 'Object reference not set to an instance of an object' in result['exception']

    def _check_tx_hash_too_long(self):
        # Step 1: check tx hash too long
        hash = base64.b64encode(b'0' * 33).decode('utf-8')
        result = self.client.invoke_function(LEDGER_CONTRACT_HASH, "getTransaction",
                                             [{'type': 'ByteArray', 'value': hash}])
        self.logger.info(f"GetTx with tx hash too long result: {result}")
        assert 'exception' in result and 'Invalid UInt256 length' in result['exception']

    def _check_tx_not_found(self):
        # Step 1: check tx not found
        hash = base64.b64encode(b'1' * 32).decode('utf-8')
        result = self.client.invoke_function(LEDGER_CONTRACT_HASH, "getTransaction",
                                             [{'type': 'ByteArray', 'value': hash}])
        self.logger.info(f"GetTx with tx not found result: {result}")
        assert 'exception' not in result or result['exception'] is None
        assert result['stack'][0]['type'] == 'Any'
        assert 'value' not in result['stack'][0] or result['stack'][0]['value'] is None

    def run_test(self):
        self._check_argument_null()
        self._check_tx_hash_too_long()
        self._check_tx_not_found()

        # TODO: check normal cases


# Run with: python3 -B -m testcases.ledger.get_tx
if __name__ == "__main__":
    test = GetTx()
    test.run()
