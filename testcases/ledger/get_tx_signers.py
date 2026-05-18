
import base64

from neo.contract import *
from testcases.ledger.base import LedgerTesting


# Operation: this case tests the getTxSigners method in Ledger contract.
# Method: GetTransactionSigners(UInt256 txHash) -> Signer[]
#  1. The txHash cannot be null.
#  2. If the txHash is not found or (current-height - the block height of the tx) > max-traceable-blocks, it will return null.
#  3. If the txHash is found, it will return the signers of the tx.
# Expect Result: The getTxSigners method is working as expected.
class GetTxSigners(LedgerTesting):
    def __init__(self):
        super().__init__("GetTxSigners")

    def _check_argument_null(self):
        # Step 1: check argument null
        result = self.client.invoke_function(LEDGER_CONTRACT_HASH, "getTransactionSigners", [{'type': 'ByteArray'}])
        self.logger.info(f"GetTxSigners with null argument result: {result}")
        assert 'exception' in result and 'Object reference not set to an instance of an object' in result['exception']

    def _check_tx_not_found(self):
        # Step 1: check tx not found
        hash = base64.b64encode(b'1' * 32).decode('utf-8')
        result = self.client.invoke_function(LEDGER_CONTRACT_HASH, "getTransactionSigners",
                                             [{'type': 'ByteArray', 'value': hash}])
        self.logger.info(f"GetTxSigners with tx not found result: {result}")
        assert 'exception' not in result or result['exception'] is None
        assert result['stack'][0]['type'] == 'Any'
        assert 'value' not in result['stack'][0] or result['stack'][0]['value'] is None

    def _check_normal_case(self):
        context = self.submit_confirmed_tx()
        result = self.client.invoke_function(LEDGER_CONTRACT_HASH, "getTransactionSigners",
                                             [self._encode_uint256_param(context['tx_id'])])
        self.logger.info(f"GetTxSigners with valid tx hash result: {result}")

        assert 'exception' not in result or result['exception'] is None
        assert len(result['stack']) == 1
        assert result['stack'][0]['type'] == 'Array'
        signers = result['stack'][0]['value']
        assert len(signers) == 1, f"Expected 1 signer, got {len(signers)}"

        signer = signers[0]
        assert signer['type'] == 'Array'
        values = signer['value']
        assert len(values) == 5, f"Expected 5 signer fields, got {len(values)}"
        assert values[0]['type'] == 'ByteString' and values[0]['value'] == context['sender_b64']
        assert values[1]['type'] == 'Integer' and values[1]['value'] == '1'
        for i in range(2, 5):
            assert values[i]['type'] == 'Array'
            assert len(values[i]['value']) == 0

    def run_test(self):
        self._check_argument_null()
        self._check_tx_not_found()
        self._check_normal_case()


# Run with: python3 -B -m testcases.ledger.get_tx_signers
if __name__ == "__main__":
    test = GetTxSigners()
    test.run()
