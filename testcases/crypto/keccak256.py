# Copyright (C) 2015-2025 The Neo Project.
#
# testcases/crypto/keccak256.py file belongs to the neo project and is free
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


# Operation: this case tests the native contract CryptoLib.keccak256 hash function.
# Expect Result: The native contract CryptoLib.keccak256 hash function is working as expected.
class Keccak256Testing(Testing):

    def __init__(self):
        super().__init__("Keccak256Testing")

    def _check_invoke_keccak256(self):
        # Step 1: invoke the keccak256 hash function
        data = base64.b64encode(b"hello world").decode('utf-8')
        params = [ContractParameter(type="ByteArray", value=data)]
        result = self.client.invoke_function(CRYPTO_CONTRACT_HASH, "keccak256", params)
        self.logger.info(f"Invoke keccak256 result: {result}")

        stack = result['stack']
        assert len(stack) == 1, f"Expected 1 item in stack, got {len(stack)}"
        assert stack[0]['type'] == "ByteString", f"Expected ByteString, got {stack[0]['type']}"
        hash = base64.b64decode(stack[0]['value']).hex()
        expected = '47173285a8d7341e5e972fc677286384f802f8ef42a5ec5f03bbfa254cb01fad'
        assert hash == expected, f"Expected '{expected}', got {hash}"

        # Step 2: invoke the keccak256 hash function with null bytes
        params = [ContractParameter(type="ByteArray", value=None)]
        result = self.client.invoke_function(CRYPTO_CONTRACT_HASH, "keccak256", params)
        self.logger.info(f"Invoke keccak256 with null bytes result: {result}")

        stack = result['stack']
        assert len(stack) == 1, f"Expected 1 item in stack, got {len(stack)}"
        assert stack[0]['type'] == "ByteString", f"Expected ByteString, got {stack[0]['type']}"
        hash = base64.b64decode(stack[0]['value']).hex()
        expected = 'c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470'
        assert hash == expected, f"Expected '{expected}', got {hash}"

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
        hash = base64.b64decode(execution['stack'][0]['value']).hex()
        expected = '47173285a8d7341e5e972fc677286384f802f8ef42a5ec5f03bbfa254cb01fad'
        assert hash == expected, f"Expected '{expected}', got {hash}"

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
        hash = base64.b64decode(execution['stack'][0]['value']).hex()
        expected = 'c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470'
        assert hash == expected, f"Expected '{expected}', got {hash}"

    def run_test(self):
        self._check_invoke_keccak256()
        self._check_tx_invoke_keccak256()


# Run with: python3 -B -m testcases.crypto.keccak256
if __name__ == "__main__":
    testing = Keccak256Testing()
    testing.run()
