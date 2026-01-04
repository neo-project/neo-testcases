
import base64

from neo.contract import *
from testcases.testing import Testing


# Operation: this case tests the getTxVmState method in Ledger contract.
# Method: GetTransactionVmState(UInt256 txHash) -> VmState
#  1. The txHash cannot be null.
#  2. If the txHash is not found, it will return VmState.NONE.
#  3. If the txHash is found, it will return the VM state of the tx.
# Expect Result: The getTxVmState method is working as expected.
class GetTxVmState(Testing):
    def __init__(self):
        super().__init__("GetTxVmState")

    def _check_argument_null(self):
        # Step 1: check argument null
        result = self.client.invoke_function(LEDGER_CONTRACT_HASH, "getTransactionVMState", [{'type': 'ByteArray'}])
        self.logger.info(f"GetTxVmState with null argument result: {result}")
        assert 'exception' in result and 'Object reference not set to an instance of an object' in result['exception']

    def _check_tx_not_found(self):
        # Step 1: check tx not found
        hash = base64.b64encode(b'1' * 32).decode('utf-8')
        result = self.client.invoke_function(LEDGER_CONTRACT_HASH, "getTransactionVMState",
                                             [{'type': 'ByteArray', 'value': hash}])
        self.logger.info(f"GetTxVmState with tx not found result: {result}")
        assert result['stack'][0]['type'] == 'Integer' and result['stack'][0]['value'] == '0'

    def run_test(self):
        self._check_argument_null()
        self._check_tx_not_found()

        # TODO: check normal cases


# Run with: python3 -B -m testcases.ledger.get_tx_vm_state
if __name__ == "__main__":
    test = GetTxVmState()
    test.run()
