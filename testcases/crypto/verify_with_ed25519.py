# Copyright (C) 2015-2025 The Neo Project.
#
# testcases/crypto/verify_with_ed25519.py file belongs to the neo project and is free
# software distributed under the MIT software license, see the
# accompanying file LICENSE in the main directory of the
# repository or http://www.opensource.org/licenses/mit-license.php
# for more details.
#
# Redistribution and use in source and binary forms with or without
# modifications are permitted.

from neo.contract import *
from testcases.testing import Testing

import ecdsa


# Operation: this case tests the native contract CryptoLib.verifyWithEd25519 function.
# 1. verifyWithEd25519 has 3 parameters: message, publicKey, signature
# 2. The public key is a 32 bytes ed25519 public key, exception if the public key is null, and always false if the public key is invalid
# 3. The signature is a 64 bytes signature, false if the signature is invalid, exception if the signature is null
# 4. The message is a bytes, result is always false if the message is null even if the public key and signature are valid
# Expect Result: The native contract CryptoLib.verifyWithEd25519 function is working as expected.
class VerifyWithEd25519(Testing):
    def __init__(self):
        super().__init__("VerifyWithEd25519")

    def _check_verify_with_ed25519(self, args: list[any], result: bool = True, exception: None | str = None):
        block_index = self.client.get_block_index()
        script = ScriptBuilder().emit_dynamic_call(CRYPTO_CONTRACT_HASH, "verifyWithEd25519",
                                                   CallFlags.READ_STATES, args).to_bytes()
        tx = self.make_tx(self.env.validators[0], script, self.default_sysfee, self.default_netfee, block_index+10)
        tx_id = self.client.send_raw_tx(tx.to_array())['hash']
        self.logger.info(f"Transaction sent: {tx_id}")

        block_index = self.client.get_block_index()
        self.wait_next_block(block_index)

        application_log = self.client.get_application_log(tx_id)
        self.logger.info(f"Application log: {application_log}")

        execution = application_log['executions'][0]
        assert 'trigger' in execution and execution['trigger'] == 'Application'
        if exception is not None:
            assert execution['vmstate'] == 'FAULT'
            assert 'exception' in execution and exception in execution['exception']
        else:
            assert execution['vmstate'] == 'HALT'
            stack = execution['stack']
            assert len(stack) == 1
            assert stack[0]['type'] == 'Boolean'
            assert stack[0]['value'] == result

    def _check_invalid_parameters(self):
        # Step 1: verify with invalid parameter number.
        self.logger.info("Test verifyWithEd25519 with null parameter")
        self._check_verify_with_ed25519(
            [None], exception='"verifyWithEd25519" with 1 parameter(s) doesn\'t exist in the contract')

        # Step 2: verify with invalid public key.
        self.logger.info("Test verifyWithEd25519 with invalid public key")
        self._check_verify_with_ed25519([b"hello world", b'1' * 33, b'2' * 64],
                                        result=False)

        # Step 3: verify with invalid signature.
        self.logger.info("Test verifyWithEd25519 with invalid signature")
        self._check_verify_with_ed25519([b"hello world", b'1' * 32, b'2' * 63],
                                        result=False)

        # Step 4: verify with null signature.
        self.logger.info("Test verifyWithEd25519 with null signature")
        self._check_verify_with_ed25519([b"hello world", b'1' * 32, None],
                                        exception='not set to an instance of an object')

        # Step 5: verify with null public key.
        self.logger.info("Test verifyWithEd25519 with null public key")
        self._check_verify_with_ed25519([b"hello world", None, b'2' * 64],
                                        exception='not set to an instance of an object')

        # Step 6: verify with null message.
        self.logger.info("Test verifyWithEd25519 with null message")
        self._check_verify_with_ed25519([None, b'1' * 32, b'2' * 64],
                                        result=False)

    def _check_ed25519(self):
        # Step 1: verify with valid ed25519SHA256
        self.logger.info("Test verifyWithEd25519 with valid ed25519SHA256")
        private_key = ecdsa.SigningKey.generate(curve=ecdsa.Ed25519)
        public_key = private_key.get_verifying_key().to_string('raw')
        signature = private_key.sign(b"hello world", hashfunc=hashlib.sha256)
        self._check_verify_with_ed25519([b"hello world", public_key, signature], result=True)

        # Step 2: verify with empty message.
        self.logger.info("Test verifyWithEd25519 with empty message")
        signature = private_key.sign(b"", hashfunc=hashlib.sha256)
        self._check_verify_with_ed25519([b"", public_key, signature], result=True)

        # Step 3: verify with mismatch signature.
        self.logger.info("Test verifyWithEd25519 with mismatch signature")
        self._check_verify_with_ed25519([b"hello world", public_key, b'2' * 64],
                                        result=False)

        self.logger.info("Test verifyWithEd25519 with null message")
        signature = private_key.sign(b'', hashfunc=hashlib.sha256)
        self._check_verify_with_ed25519([None, public_key, signature], result=False)

    def run_test(self):
        self._check_invalid_parameters()
        self._check_ed25519()


# Run with: python3 -B -m testcases.crypto.verify_with_ed25519
if __name__ == "__main__":
    test = VerifyWithEd25519()
    test.run()
