
import base64

from neo.contract import *
from testcases.ledger.base import LedgerTesting


# Operation: this case tests the getTransactionFromBlock method in Ledger contract.
# Method:GetTransactionFromBlock(byte[] blockIndexOrHash, int txIndex) -> Transaction or null
#  1. The blockIndexOrHash cannot be null.
#  2. The txIndex must between [0, block.transactions.length).
#  3. If current-height - block-height < max-traceable-blocks, it will return null.
#  4. If the block is not found, it will return null.
#  5. If the blockIndexOrHash.length is 32, it will be treated as a block hash.
#  6. If the blockIndexOrHash.length less than 32, it will be treated as a block index and must be in [0, uint32.MaxValue].
#  7. If the blockIndexOrHash.length greater than 32, it will fail.
# Expect Result: The getTransactionFromBlock method is working as expected.
class TxFromBlock(LedgerTesting):
    def __init__(self):
        super().__init__("TxFromBlock")

    def _check_argument_null(self):
        # Step 1: check argument null with blockIndexOrHash is null
        result = self.client.invoke_function(LEDGER_CONTRACT_HASH, "getTransactionFromBlock",
                                             [{'type': 'ByteArray'}, {'type': 'Integer', 'value': 0}])
        self.logger.info(f"GetTransactionFromBlock with null blockIndexOrHash result: {result}")
        self._check_null_argument_exception(result)

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

    def _check_block_not_found(self):
        future_index = self.client.get_block_index() + 100
        height = self._block_index_to_base64(future_index)
        result = self.client.invoke_function(LEDGER_CONTRACT_HASH, "getTransactionFromBlock",
                                             [{'type': 'ByteArray', 'value': height}, {'type': 'Integer', 'value': 0}])
        self.logger.info(f"GetTransactionFromBlock with block not found result: {result}")
        self._check_null_stack_item(result)

    def _check_normal_cases(self):
        marker = self._send_marker_tx()

        result = self.client.invoke_function(LEDGER_CONTRACT_HASH, "getTransactionFromBlock",
                                             [{'type': 'ByteArray', 'value': marker["block_index_base64"]},
                                              {'type': 'Integer', 'value': marker["tx_index"]}])
        self.logger.info(f"GetTransactionFromBlock with block index result: {result}")
        self._check_tx_stack(result, marker)

        result = self.client.invoke_function(LEDGER_CONTRACT_HASH, "getTransactionFromBlock",
                                             [{'type': 'ByteArray', 'value': marker["block_hash_base64"]},
                                              {'type': 'Integer', 'value': marker["tx_index"]}])
        self.logger.info(f"GetTransactionFromBlock with block hash result: {result}")
        self._check_tx_stack(result, marker)

        result = self.client.invoke_function(LEDGER_CONTRACT_HASH, "getTransactionFromBlock",
                                             [{'type': 'ByteArray', 'value': marker["block_index_base64"]},
                                              {'type': 'Integer', 'value': marker["tx_index"] + 1_000_000}])
        self.logger.info(f"GetTransactionFromBlock with missing tx index result: {result}")
        assert 'exception' in result and 'argument was out of the range of valid values' in result['exception']

    def run_test(self):
        self._check_argument_null()
        self._check_block_index()
        self._check_block_hash_too_long()
        self._check_block_not_found()
        self._check_normal_cases()


# Run with: python3 -B -m testcases.ledger.get_tx_from_block
if __name__ == "__main__":
    test = TxFromBlock()
    test.run()
