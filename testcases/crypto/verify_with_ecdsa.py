# Copyright (C) 2015-2025 The Neo Project.
#
# testcases/crypto/verify_with_ecdsa.py file belongs to the neo project and is free
# software distributed under the MIT software license, see the
# accompanying file LICENSE in the main directory of the
# repository or http://www.opensource.org/licenses/mit-license.php
# for more details.
#
# Redistribution and use in source and binary forms with or without
# modifications are permitted.

from neo import NamedCurveHash
from neo.contract import *
from testcases.testing import Testing

import ecdsa
import sha3


# Operation: this case tests the native contract CryptoLib.verifyWithECDsa function.
# 1. verifyWithECDsa has 4 parameters: message, publicKey, signature, namedCurveHash
# 2. The public key is a compressed or not compressed SECP256K1 or SECP256R1 ECPoint exception
#  if the public key is invalid(FormatException), empty(ArrayOutOfBounds) or null(ArrayOutOfBounds)
# 3. The signature is a 64 bytes signature, false if the signature is invalid
# Expect Result: The native contract CryptoLib.verifyWithECDsa function is working as expected.
class VerifyWithEcdsa(Testing):

    def __init__(self):
        super().__init__("VerifyWithEcdsa")

    def _check_verify_with_ecdsa(self, args: list[any], result: bool = True, exception: None | str = None):
        block_index = self.client.get_block_index()
        script = ScriptBuilder().emit_dynamic_call(CRYPTO_CONTRACT_HASH, "verifyWithECDsa",
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
        self.logger.info("Test verifyWithECDsa with null parameter")
        self._check_verify_with_ecdsa(
            [None], exception='"verifyWithECDsa" with 1 parameter(s) doesn\'t exist in the contract')

        # Step 2: verify with invalid public key.
        self.logger.info("Test verifyWithECDsa with valid secp256k1SHA256")
        # Invalid ECPoint encoding format: unknown prefix byte 0x31. Expected 0x02, 0x03 (compressed), or 0x04 (uncompressed).
        self._check_verify_with_ecdsa(
            [b"hello world", b'1' * 64, b'2' * 64, NamedCurveHash.SECP256K1_SHA256],
            exception='Invalid ECPoint encoding format')

        # Step 3: verify with null public key.
        self.logger.info("Test verifyWithECDsa with null public key")
        self._check_verify_with_ecdsa(
            [b"hello world", None, b'2' * 64, NamedCurveHash.SECP256K1_SHA256],
            exception='outside the bounds of the array')  # Index was outside the bounds of the array.

        # Step 4: verify with invalid signature.
        self.logger.info("Test verifyWithECDsa with invalid signature")

        private_key = ecdsa.SigningKey.generate(curve=ecdsa.NIST256p)
        public_key = private_key.get_verifying_key().to_string('compressed')
        self._check_verify_with_ecdsa([b"hello world", public_key, b'2' * 63, NamedCurveHash.SECP256R1_SHA256],
                                      result=False)

        # Step 5: verify with null signature.
        self.logger.info("Test verifyWithECDsa with null signature")
        self._check_verify_with_ecdsa([b"hello world", public_key, None, NamedCurveHash.SECP256R1_SHA256],
                                      result=False)

        # Step 6: verify public key with wrong named curve hash.
        self.logger.info("Test verifyWithECDsa with public key with wrong named curve hash")
        secp256r1_pubkey = bytes.fromhex('0285265dc8859d05e1e42a90d6c29a9de15531eac182489743e6a947817d2a9f66')
        self._check_verify_with_ecdsa([b"hello world", secp256r1_pubkey, b'2' * 64, NamedCurveHash.SECP256K1_SHA256],
                                      exception='The point compression is invalid')  # mismatch named curve hash.p

        # Step 7: verify with invalid named curve hash.
        self.logger.info("Test verifyWithECDsa with invalid named curve hash")
        self._check_verify_with_ecdsa([b"hello world", public_key, b'2' * 64, 0xFFff],
                                      exception='an overflow')  # Arithmetic operation resulted in an overflow.

        # Step 8: verify with unknown named curve hash.
        self.logger.info("Test verifyWithECDsa with invalid named curve hash")
        # The given key '99' was not present in the dictionary.
        self._check_verify_with_ecdsa([b"hello world", public_key, b'2' * 64, 99],
                                      exception='not present in the dictionary')

    def _check_secp256k1(self):
        # Step 1: verify with valid secp256k1SHA256
        self.logger.info("Test verifyWithECDsa with valid secp256k1SHA256")
        private_key = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
        public_key = private_key.get_verifying_key().to_string('compressed')
        signature = private_key.sign(b"hello world", hashfunc=hashlib.sha256)
        self._check_verify_with_ecdsa([b"hello world", public_key, signature, NamedCurveHash.SECP256K1_SHA256],
                                      result=True)

        # Step 2: verify with valid secp256k1KECCAK256
        self.logger.info("Test verifyWithECDsa with valid secp256k1KECCAK256")
        signature = private_key.sign(b"hello world", hashfunc=sha3.keccak_256)
        self._check_verify_with_ecdsa([b"hello world", public_key, signature, NamedCurveHash.SECP256K1_KECCAK256],
                                      result=True)

        # Step 3: verify with mismatch signature.
        self.logger.info("Test verifyWithECDsa with mismatch signature")
        self._check_verify_with_ecdsa([b"hello world", public_key, b'2' * 64, NamedCurveHash.SECP256K1_SHA256],
                                      result=False)

        # step 4: verify with null message.
        self.logger.info("Test verifyWithECDsa with null message")
        signature = private_key.sign(b'', hashfunc=hashlib.sha256)
        self._check_verify_with_ecdsa([None, public_key, signature, NamedCurveHash.SECP256K1_SHA256],
                                      result=True)  # True even if the message is null.

    def _check_secp256r1(self):
        # Step 1: verify with valid secp256r1SHA256
        self.logger.info("Test verifyWithECDsa with valid secp256r1SHA256")
        private_key = ecdsa.SigningKey.generate(curve=ecdsa.NIST256p)
        public_key = private_key.get_verifying_key().to_string('compressed')
        signature = private_key.sign(b"hello world", hashfunc=hashlib.sha256)
        self._check_verify_with_ecdsa([b"hello world", public_key, signature, NamedCurveHash.SECP256R1_SHA256],
                                      result=True)

        # Step 2: verify with valid secp256r1KECCAK256
        self.logger.info("Test verifyWithECDsa with valid secp256r1KECCAK256")
        signature = private_key.sign(b"hello world", hashfunc=sha3.keccak_256)
        self._check_verify_with_ecdsa([b"hello world", public_key, signature, NamedCurveHash.SECP256R1_KECCAK256],
                                      result=True)

        # Step 3: verify with mismatch signature.
        self.logger.info("Test verifyWithECDsa with mismatch signature")
        self._check_verify_with_ecdsa([b"hello world", public_key, b'2' * 64, NamedCurveHash.SECP256R1_SHA256],
                                      result=False)

        # step 4: verify with null message.
        self.logger.info("Test verifyWithECDsa with null message")
        signature = private_key.sign(b'', hashfunc=hashlib.sha256)
        self._check_verify_with_ecdsa([None, public_key, signature, NamedCurveHash.SECP256R1_SHA256],
                                      result=True)  # True even if the message is null.

    def run_test(self):
        self._check_invalid_parameters()
        self._check_secp256k1()
        self._check_secp256r1()


# Run with: python3 -B -m testcases.crypto.verify_with_ecdsa
if __name__ == "__main__":
    test = VerifyWithEcdsa()
    test.run()
