
import base64

from neo.contract import *
from testcases.ledger.base import LedgerTesting


# Operation: this case tests the getTxHeight method in Ledger contract.
# Method: GetTransactionHeight(UInt256 txHash) -> int
#  1. The txHash cannot be null.
#  2. If the txHash is not found or (current-height - the block height of the tx) > max-traceable-blocks, it will return -1.
#  3. If the txHash is found, it will return the block height of the tx.
# Expect Result: The getTxHeight method is working as expected.
class GetTxHeight(LedgerTesting):
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

    def _check_normal_case(self):
        context = self.submit_confirmed_tx()
        result = self.client.invoke_function(LEDGER_CONTRACT_HASH, "getTransactionHeight",
                                             [self._encode_uint256_param(context['tx_id'])])
        self.logger.info(f"GetTxHeight with valid tx hash result: {result}")
        self.check_stack(result['stack'], [('Integer', str(context['block_index']))])

    def run_test(self):
        self._check_argument_null()
        self._check_tx_hash_too_long()
        self._check_normal_case()


# Run with: python3 -B -m testcases.ledger.get_tx_height
if __name__ == "__main__":
    test = GetTxHeight()
    test.run()
