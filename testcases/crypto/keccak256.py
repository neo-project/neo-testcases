
import base64

from neo import Hardforks
from neo.contract import *
from testcases.testing import Testing


# Operation: this case tests the native contract CryptoLib.keccak256 hash function.
# Expect Result: The native contract CryptoLib.keccak256 hash function is working as expected.
class Keccak256Testing(Testing):

    def __init__(self):
        super().__init__("Keccak256Testing")
        self.hardfork = Hardforks.HF_Cockatrice

    def _check_keccak256_result_stack(self, stack: list, expected_hash: str):
        assert len(stack) == 1, f"Expected 1 item in stack, got {len(stack)}"
        assert stack[0]['type'] == "ByteString", f"Expected ByteString, got {stack[0]['type']}"

        hash = base64.b64decode(stack[0]['value']).hex()
        assert hash == expected_hash, f"Expected {expected_hash}, got {hash}"

    def _check_keccak256_null_checking(self):
        # Step 1: invoke the keccak256 hash function with null bytes
        params = [ContractParameter(type="ByteArray", value=None)]
        result = self.client.invoke_function(CRYPTO_CONTRACT_HASH, "keccak256", params)
        self.logger.info(f"Invoke keccak256 with null bytes result: {result}")

        expected = 'c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470'
        self._check_keccak256_result_stack(result['stack'], expected)

        # Step 2: invoke the keccak256 hash function with null
        result = self.client.invoke_function(CRYPTO_CONTRACT_HASH, "keccak256", [{'type': 'ByteArray'}])
        self.logger.info(f"Invoke keccak256 with null result: {result}")
        self._check_keccak256_result_stack(result['stack'], expected)

    def _check_invoke_keccak256(self):
        # Step 1: invoke the keccak256 hash function
        data = base64.b64encode(b"hello world").decode('utf-8')
        params = [ContractParameter(type="ByteArray", value=data)]
        result = self.client.invoke_function(CRYPTO_CONTRACT_HASH, "keccak256", params)
        self.logger.info(f"Invoke keccak256 result: {result}")

        expected = '47173285a8d7341e5e972fc677286384f802f8ef42a5ec5f03bbfa254cb01fad'
        self._check_keccak256_result_stack(result['stack'], expected)

    def _check_tx_invoke_keccak256(self):
        # Step 1: create a transaction to invoke the keccak256 hash function
        script = ScriptBuilder().emit_dynamic_call(
            CRYPTO_CONTRACT_HASH, "keccak256", CallFlags.READ_STATES, [b"hello world"]).to_bytes()
        source = self.env.validators[0]
        block_index = self.client.get_block_index()
        tx = self.make_tx(source, script, self.default_sysfee, self.default_netfee, block_index + 10)
        tx_id = self.client.send_raw_tx(tx.to_array())['hash']
        self.logger.info(f"Tx invoke keccak256 transaction sent: {tx_id}")

        block_index = self.client.get_block_index()
        self.wait_next_block(block_index)

        application_log = self.client.get_application_log(tx_id)
        self.logger.info(f"Application log with valid bytes: {application_log}")

        execution = application_log['executions'][0]
        assert 'trigger' in execution and execution['trigger'] == 'Application'
        assert execution['vmstate'] == 'HALT'

        expected = '47173285a8d7341e5e972fc677286384f802f8ef42a5ec5f03bbfa254cb01fad'
        self._check_keccak256_result_stack(execution['stack'], expected)

        # Step 2: create a transaction to invoke the keccak256 hash function with null bytes
        script = ScriptBuilder().emit_dynamic_call(
            CRYPTO_CONTRACT_HASH, "keccak256", CallFlags.READ_STATES, [None]).to_bytes()
        tx = self.make_tx(source, script, self.default_sysfee, self.default_netfee, block_index + 10)
        tx_id = self.client.send_raw_tx(tx.to_array())['hash']
        self.logger.info(f"Tx invoke keccak256 with null bytes transaction sent: {tx_id}")

        block_index = self.client.get_block_index()
        self.wait_next_block(block_index)

        application_log = self.client.get_application_log(tx_id)
        self.logger.info(f"Application log with null bytes: {application_log}")

        execution = application_log['executions'][0]
        assert 'trigger' in execution and execution['trigger'] == 'Application'
        assert execution['vmstate'] == 'HALT'

        expected = 'c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470'
        self._check_keccak256_result_stack(execution['stack'], expected)

    def run_test(self):
        self._check_keccak256_null_checking()
        self._check_invoke_keccak256()
        self._check_tx_invoke_keccak256()


# Run with: python3 -B -m testcases.crypto.keccak256
if __name__ == "__main__":
    testing = Keccak256Testing()
    testing.run()
