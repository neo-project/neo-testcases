# Copyright (C) 2015-2025 The Neo Project.
#
# testcases/crypto/ripemd160.py file belongs to the neo project and is free
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


# Operation: this case tests the native contract CryptoLib.ripemd160 hash function.
# Expect Result: The native contract CryptoLib.ripemd160 hash function is working as expected.
class Ripemd160Testing(Testing):

    def __init__(self):
        super().__init__("Ripemd160Testing")

    def _check_ripemd160_result_stack(self, stack: list, expected_hash: str):
        assert len(stack) == 1, f"Expected 1 item in stack, got {len(stack)}"
        assert stack[0]['type'] == "ByteString", f"Expected ByteString, got {stack[0]['type']}"

        hash = base64.b64decode(stack[0]['value']).hex()
        assert hash == expected_hash, f"Expected {expected_hash}, got {hash}"

    def _check_ripemd160_null_checking(self):
        # Step 1: invoke the ripemd160 hash function with null bytes
        result = self.client.invoke_function(CRYPTO_CONTRACT_HASH, "ripemd160",
                                             [ContractParameter(type="ByteArray", value=None)])
        self.logger.info(f"Invoke ripemd160 with null bytes result: {result}")
        assert 'exception' in result and result['exception'] is not None

        # Step 2: invoke the ripemd160 hash function with null
        result = self.client.invoke_function(CRYPTO_CONTRACT_HASH, "ripemd160", [{'type': 'ByteArray'}])
        self.logger.info(f"Invoke ripemd160 with null result: {result}")
        assert 'exception' in result and result['exception'] is not None

    def _check_invoke_ripemd160(self):
        # Step 1: invoke the ripemd160 hash function
        data = base64.b64encode(b"hello world").decode('utf-8')
        result = self.client.invoke_function(CRYPTO_CONTRACT_HASH, "ripemd160",
                                             [ContractParameter(type="ByteArray", value=data)])
        self.logger.info(f"Invoke ripemd160 result: {result}")
        self._check_ripemd160_result_stack(result['stack'], '98c615784ccb5fe5936fbc0cbe9dfdb408d92f0f')

    def _check_tx_invoke_ripemd160(self):
        # Step 1: create a transaction to invoke the ripemd160 hash function with null bytes
        script = ScriptBuilder().emit_dynamic_call(
            CRYPTO_CONTRACT_HASH, "ripemd160", CallFlags.READ_STATES, [None]).to_bytes()

        source = self.env.validators[0]
        block_index = self.client.get_block_index()
        tx = self.make_tx(source, script, self.default_sysfee, self.default_netfee, block_index + 10)
        tx_id = self.client.send_raw_tx(tx.to_array())['hash']
        self.logger.info(f"Tx null-bytes ripemd160 transaction sent: {tx_id}")

        block_index = self.client.get_block_index()
        self.wait_next_block(block_index)

        application_log = self.client.get_application_log(tx_id)
        self.logger.info(f"Application log: {application_log}")

        # RIPEMD160 failed if the argument is null.
        execution = application_log['executions'][0]
        assert 'trigger' in execution and execution['trigger'] == 'Application'
        assert execution['vmstate'] == 'FAULT'
        assert 'exception' in execution and execution['exception'] is not None

        # Step 2: create a transaction to invoke the ripemd160 hash function with valid bytes
        script = ScriptBuilder().emit_dynamic_call(
            CRYPTO_CONTRACT_HASH, "ripemd160", CallFlags.READ_STATES, [b"hello world"]).to_bytes()
        tx = self.make_tx(source, script, self.default_sysfee, self.default_netfee, block_index + 10)
        tx_id = self.client.send_raw_tx(tx.to_array())['hash']
        self.logger.info(f"Tx invoke valid ripemd160 transaction sent: {tx_id}")

        block_index = self.client.get_block_index()
        self.wait_next_block(block_index)

        application_log = self.client.get_application_log(tx_id)
        self.logger.info(f"Application log: {application_log}")

        execution = application_log['executions'][0]
        assert 'trigger' in execution and execution['trigger'] == 'Application'
        assert execution['vmstate'] == 'HALT'
        self._check_ripemd160_result_stack(execution['stack'], '98c615784ccb5fe5936fbc0cbe9dfdb408d92f0f')

    def run_test(self):
        self._check_ripemd160_null_checking()
        self._check_invoke_ripemd160()
        self._check_tx_invoke_ripemd160()


# Run with: python3 -B -m testcases.crypto.ripemd160
if __name__ == "__main__":
    testing = Ripemd160Testing()
    testing.run_test()
