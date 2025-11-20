# Copyright (C) 2015-2025 The Neo Project.
#
# testcases/crypto/murmur32.py file belongs to the neo project and is free
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


# Operation: this case tests the native contract CryptoLib.murmur32 hash function.
# Expect Result: The native contract CryptoLib.murmur32 hash function is working as expected.
class Murmur32Testing(Testing):

    def __init__(self):
        super().__init__("Murmur32Testing")

    def _check_invoke_murmur32(self):
        # Step 1: invoke the murmur32 hash function
        data = base64.b64encode(b"hello world").decode('utf-8')
        params = [ContractParameter(type="ByteArray", value=data), ContractParameter(type="Integer", value=0)]
        result = self.client.invoke_function(CRYPTO_CONTRACT_HASH, "murmur32", params)
        self.logger.info(f"Invoke murmur32 result: {result}")

        stack = result['stack']
        assert len(stack) == 1, f"Expected 1 item in stack, got {len(stack)}"
        assert stack[0]['type'] == "ByteString", f"Expected ByteString, got {stack[0]['type']}"

        hash = base64.b64decode(stack[0]['value']).hex()
        assert hash == '0f8f925e', f"Expected '0f8f925e', got {hash}"

        # Step 2: invoke the murmur32 hash function with null bytes
        params = [ContractParameter(type="ByteArray", value=None), ContractParameter(type="Integer", value=0)]
        result = self.client.invoke_function(CRYPTO_CONTRACT_HASH, "murmur32", params)

        stack = result['stack']
        assert len(stack) == 1, f"Expected 1 item in stack, got {len(stack)}"
        assert stack[0]['type'] == "ByteString", f"Expected ByteString, got {stack[0]['type']}"

        hash = base64.b64decode(stack[0]['value']).hex()
        assert hash == '00000000', f"Expected '00000000', got {hash}"

    def _check_tx_invoke_murmur32(self):
        # Step 1: create a transaction to invoke the sha256 hash function with null bytes
        script = ScriptBuilder().emit_dynamic_call(
            CRYPTO_CONTRACT_HASH, "murmur32", CallFlags.READ_STATES, [None, 0]).to_bytes()

        source = self.env.validators[0]
        block_index = self.client.get_block_index()
        tx = self.make_tx(source, script, self.default_sysfee, self.default_netfee, block_index + 10)
        tx_id = self.client.send_raw_tx(tx.to_array())['hash']
        self.logger.info(f"Tx null-bytes murmur32 transaction sent: {tx_id}")

        block_index = self.client.get_block_index()
        self.wait_next_block(block_index)

        application_log = self.client.get_application_log(tx_id)
        self.logger.info(f"Application log with null bytes and 0: {application_log}")

        # Murmur32 OK if the argument is null or 0.
        execution = application_log['executions'][0]
        assert 'trigger' in execution and execution['trigger'] == 'Application'
        assert execution['vmstate'] == 'HALT'
        hash = base64.b64decode(execution['stack'][0]['value']).hex()
        assert hash == '00000000', f"Expected '00000000', got {hash}"

        # Step 2: create a transaction to invoke the murmur32 hash function with valid bytes
        script = ScriptBuilder().emit_dynamic_call(
            CRYPTO_CONTRACT_HASH, "murmur32", CallFlags.READ_STATES, [b"hello world", 0]).to_bytes()
        tx = self.make_tx(source, script, self.default_sysfee, self.default_netfee, block_index + 10)
        tx_id = self.client.send_raw_tx(tx.to_array())['hash']
        self.logger.info(f"Tx invoke valid murmur32 transaction sent: {tx_id}")

        block_index = self.client.get_block_index()
        self.wait_next_block(block_index)

        application_log = self.client.get_application_log(tx_id)
        self.logger.info(f"Application log with valid bytes and 0: {application_log}")

        execution = application_log['executions'][0]
        assert 'trigger' in execution and execution['trigger'] == 'Application'
        assert execution['vmstate'] == 'HALT'
        hash = base64.b64decode(execution['stack'][0]['value']).hex()
        assert hash == '0f8f925e', f"Expected '0f8f925e', got {hash}"

    def run_test(self):
        self._check_invoke_murmur32()
        self._check_tx_invoke_murmur32()


# Run with: python3 -B -m testcases.crypto.murmur32
if __name__ == "__main__":
    testing = Murmur32Testing()
    testing.run()
