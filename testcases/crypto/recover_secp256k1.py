# Copyright (C) 2015-2025 The Neo Project.
#
# testcases/crypto/recover_secp256k1.py file belongs to the neo project and is free
# software distributed under the MIT software license, see the
# accompanying file LICENSE in the main directory of the
# repository or http://www.opensource.org/licenses/mit-license.php
# for more details.
#
# Redistribution and use in source and binary forms with or without
# modifications are permitted.

import base64
import ecdsa
import hashlib

from neo import Hardforks
from neo.contract import *
from testcases.testing import Testing


# Operation: this case tests the native contract CryptoLib.recoverSecp256k1 function.
# Expect Result: The native contract CryptoLib.recoverSecp256k1 function is working as expected.
class RecoverSecp256k1(Testing):
    def __init__(self):
        super().__init__("RecoverSecp256k1")
        self.secp256k1_private_key = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
        self.SECP256K1_SHA256 = 22
        self.hardfork = Hardforks.HF_Echidna

    def _check_recover_secp256k1_failed_result(self, result: dict):
        assert 'exception' not in result or result['exception'] is None

        stack = result['stack']
        assert len(stack) == 1, f"Expected 1 item in stack, got {len(stack)}"
        assert stack[0]['type'] == "Any", f"Expected Any, got {stack[0]['type']}"
        assert 'value' not in stack[0]

    def _check_recover_secp256k1_ok_result(self, result: dict, expected_public_key: str):
        assert 'exception' not in result or result['exception'] is None

        stack = result['stack']
        assert len(stack) == 1, f"Expected 1 item in stack, got {len(stack)}"
        assert stack[0]['type'] == "ByteString", f"Expected ByteString, got {stack[0]['type']}"

        public_key = base64.b64decode(stack[0]['value']).hex()
        self.logger.info(f"RecoverSecp256k1 public key: {public_key}")
        assert public_key == expected_public_key, f"Expected {expected_public_key}, got {public_key}"

    def _check_recover_secp256k1_null_checking(self):
        signature = self.secp256k1_private_key.sign(b"hello world", hashfunc=hashlib.sha256)
        signature = base64.b64encode(signature).decode('utf-8')

        message_hash = hashlib.sha256(b"hello world").digest()
        message_hash = base64.b64encode(message_hash).decode('utf-8')

        # Step 1: invoke the recoverSecp256k1 function with null message hash
        result = self.client.invoke_function(CRYPTO_CONTRACT_HASH, "recoverSecp256K1",
                                             [{'type': 'ByteArray', 'value': None},
                                              {'type': 'ByteArray', 'value': signature}])
        self.logger.info(f"Invoke recoverSecp256k1 with null message hash result: {result}")
        self._check_recover_secp256k1_failed_result(result)

        # Step 2: invoke the recoverSecp256k1 function with null signature
        result = self.client.invoke_function(CRYPTO_CONTRACT_HASH, "recoverSecp256K1",
                                             [{'type': 'ByteArray', 'value': message_hash},
                                              {'type': 'ByteArray', 'value': None}])
        self.logger.info(f"Invoke recoverSecp256k1 with null signature result: {result}")
        self._check_recover_secp256k1_failed_result(result)

        # Step 3: invoke the recoverSecp256k1 function with null message hash and signature
        result = self.client.invoke_function(CRYPTO_CONTRACT_HASH, "recoverSecp256K1",
                                             [{'type': 'ByteArray'}, {'type': 'ByteArray', 'value': signature}])
        self.logger.info(f"Invoke recoverSecp256k1 with null message hash result: {result}")
        self._check_recover_secp256k1_failed_result(result)

        # Step 4: invoke the recoverSecp256k1 function with null signature
        result = self.client.invoke_function(CRYPTO_CONTRACT_HASH, "recoverSecp256K1",
                                             [{'type': 'ByteArray', 'value': message_hash}, {'type': 'ByteArray'}])
        self.logger.info(f"Invoke recoverSecp256k1 with null signature result: {result}")
        self._check_recover_secp256k1_failed_result(result)

    def _check_recover_secp256k1_invalid_parameters(self):
        signature = self.secp256k1_private_key.sign(b"hello world", hashfunc=hashlib.sha256)
        signature = base64.b64encode(signature).decode('utf-8')

        message_hash = hashlib.sha256(b"hello world").digest()
        message_hash = base64.b64encode(message_hash).decode('utf-8')

        # Step 1: invoke the recoverSecp256k1 function with invalid message hash
        invalid_hash = base64.b64encode(b'1' * 32).decode('utf-8')
        result = self.client.invoke_function(CRYPTO_CONTRACT_HASH, "recoverSecp256K1",
                                             [{'type': 'ByteArray', 'value': invalid_hash},
                                              {'type': 'ByteArray', 'value': signature}])
        self.logger.info(f"Invoke recoverSecp256k1 with invalid message hash result: {result}")
        # Cannot know whether it will succeed or failed. Maybe failed or recover a random public key.
        if 'type' in result['stack'][0] and result['stack'][0]['type'] != "Any":
            assert result['stack'][0]['type'] == "ByteString", f"Expected ByteString, got {result['stack'][0]['type']}"
            public_key = base64.b64decode(result['stack'][0]['value']).hex()
            assert len(public_key) == 66, f"Expected 33(i.e. 66 hex) compressed public key bytes, got {len(public_key)}"

        # Step 2: invoke the recoverSecp256k1 function with invalid signature
        invalid_sign = base64.b64encode(b'2' * 64).decode('utf-8')
        result = self.client.invoke_function(CRYPTO_CONTRACT_HASH, "recoverSecp256K1",
                                             [{'type': 'ByteArray', 'value': message_hash},
                                              {'type': 'ByteArray', 'value': invalid_sign}])
        self.logger.info(f"Invoke recoverSecp256k1 with invalid signature result: {result}")
        # Can get a publick even if the signature is random, because there might be a public key that can recover the message hash.
        public_key = '02dd6daf85f6df5ff8d3034ec9a586e9a4d8f4ea8f73eda82e27d3f417172a392c'
        self._check_recover_secp256k1_ok_result(result, public_key)

    def _check_recover_secp256k1_examples(self):
        message_hash = bytes.fromhex('5ae8317d34d1e595e3fa7247db80c0af4320cce1116de187f8f7e2e099c0d8d0')
        signature = bytes.fromhex('45c0b7f8c09a9e1f1cea0c25785594427b6bf8f9f878a8af0b1abbb48e16d092' +
                                  '0d8becd0c220f67c51217eecfd7184ef0732481c843857e6bc7fc095c4f6b78801')

        result = self.client.invoke_function(
            CRYPTO_CONTRACT_HASH, "recoverSecp256K1",
            [{'type': 'ByteArray', 'value': base64.b64encode(message_hash).decode('utf-8')},
             {'type': 'ByteArray', 'value': base64.b64encode(signature).decode('utf-8')}])
        self.logger.info(f"Invoke recoverSecp256k1 with example1 result: {result}")
        self._check_recover_secp256k1_ok_result(
            result, '034a071e8a6e10aada2b8cf39fa3b5fb3400b04e99ea8ae64ceea1a977dbeaf5d5')

        message_hash = bytes.fromhex('586052916fb6f746e1d417766cceffbe1baf95579bab67ad49addaaa6e798862')
        signature = bytes.fromhex('4e0ea79d4a476276e4b067facdec7460d2c98c8a65326a6e5c998fd7c6506114' +
                                  '0e45aea5034af973410e65cf97651b3f2b976e3fc79c6a93065ed7cb69a2ab5a01')
        result = self.client.invoke_function(
            CRYPTO_CONTRACT_HASH, "recoverSecp256K1",
            [{'type': 'ByteArray', 'value': base64.b64encode(message_hash).decode('utf-8')},
             {'type': 'ByteArray', 'value': base64.b64encode(signature).decode('utf-8')}])
        self.logger.info(f"Invoke recoverSecp256k1 with example2 result: {result}")
        self._check_recover_secp256k1_ok_result(
            result, '02dbf1f4092deb3cfd4246b2011f7b24840bc5dbedae02f28471ce5b3bfbf06e71')

    def _check_recover_secp256k1(self):
        # Step 1: invoke the recoverSecp256k1 function with sign_deterministic
        message = b"hello world"
        message_hash = hashlib.sha256(message).digest()
        message_hash = base64.b64encode(message_hash).decode('utf-8')

        private_key = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
        public_key = private_key.get_verifying_key().to_string('compressed')  # bytes
        self.logger.info(f"RecoverSecp256k1 keypair: {private_key.to_string().hex()}, {public_key.hex()}")

        # Step 1.1: invoke verifyWithECDsa to verify the signature
        signature = private_key.sign_deterministic(message, hashfunc=hashlib.sha256)
        result = self.client.invoke_function(
            CRYPTO_CONTRACT_HASH, "verifyWithECDsa",
            [{'type': 'ByteArray', 'value': base64.b64encode(message).decode('utf-8')},
             {'type': 'ByteArray', 'value': base64.b64encode(public_key).decode('utf-8')},
             {'type': 'ByteArray', 'value': base64.b64encode(signature).decode('utf-8')},
             {'type': 'Integer', 'value': self.SECP256K1_SHA256}])
        self.logger.info(f"Invoke verifyWithECDsa with sign_deterministic result: {result}")
        assert result['stack'][0]['type'] == 'Boolean' and result['stack'][0]['value'] == True

        # Step 1.2: invoke recoverSecp256K1 to recover the public key
        count1, count2 = 0, 0
        for x in [0x00, 0x01]:
            encoded_sign = signature + x.to_bytes(1, 'big')
            encoded_sign = base64.b64encode(encoded_sign).decode('utf-8')
            result = self.client.invoke_function(CRYPTO_CONTRACT_HASH, "recoverSecp256K1",
                                                 [{'type': 'ByteArray', 'value': message_hash},
                                                  {'type': 'ByteArray', 'value': encoded_sign}])
            self.logger.info(f"Invoke recoverSecp256k1 with sign_deterministic result: {result}")
            recovered_pubkey = base64.b64decode(result['stack'][0]['value']).hex()
            count1 += (1 if recovered_pubkey == public_key.hex() else 0)

            # r, s = int.from_bytes(signature[:32], 'big'), int.from_bytes(signature[32:], 'big')
            # s = s | (x << 255)
            # encoded_sign = r.to_bytes(32, 'big') + s.to_bytes(32, 'big')
            # encoded_sign = base64.b64encode(encoded_sign).decode('utf-8')
            # result = self.client.invoke_function(CRYPTO_CONTRACT_HASH, "recoverSecp256K1",
            #                                      [{'type': 'ByteArray', 'value': message_hash},
            #                                       {'type': 'ByteArray', 'value': encoded_sign}])
            # self.logger.info(f"Invoke recoverSecp256k1 with sign_deterministic result: {result}")
            # recovered_pubkey = base64.b64decode(result['stack'][0]['value']).hex()
            # count2 += (1 if recovered_pubkey == public_key.hex() else 0)
        assert count1 == 1, f"Expected 1 recovered public key, got {count1}"
        # assert count2 == 0, f"Expected 1 recovered public key, got {count2}"

        # Step 2: invoke verifyWithECDsa to verify the signature
        signature = private_key.sign(message, hashfunc=hashlib.sha256)
        result = self.client.invoke_function(
            CRYPTO_CONTRACT_HASH, "verifyWithECDsa",
            [{'type': 'ByteArray', 'value': base64.b64encode(message).decode('utf-8')},
             {'type': 'ByteArray', 'value': base64.b64encode(public_key).decode('utf-8')},
             {'type': 'ByteArray', 'value': base64.b64encode(signature).decode('utf-8')},
             {'type': 'Integer', 'value': self.SECP256K1_SHA256}])
        self.logger.info(f"Invoke verifyWithECDsa with sign result: {result}")
        assert result['stack'][0]['type'] == 'Boolean' and result['stack'][0]['value'] == True

        # Step 2.1: invoke recoverSecp256K1 to recover the public key
        count1, count2 = 0, 0
        for x in [0x00, 0x01]:
            encoded_sign = signature + x.to_bytes(1, 'big')
            encoded_sign = base64.b64encode(encoded_sign).decode('utf-8')
            result = self.client.invoke_function(CRYPTO_CONTRACT_HASH, "recoverSecp256K1",
                                                 [{'type': 'ByteArray', 'value': message_hash},
                                                  {'type': 'ByteArray', 'value': encoded_sign}])
            self.logger.info(f"Invoke recoverSecp256k1 with sign result: {result}")
            recovered_pubkey = base64.b64decode(result['stack'][0]['value']).hex()
            count1 += (1 if recovered_pubkey == public_key.hex() else 0)

            # r, s = int.from_bytes(signature[:32], 'big'), int.from_bytes(signature[32:], 'big')
            # s = s | (x << 255)
            # encoded_sign = r.to_bytes(32, 'big') + s.to_bytes(32, 'big')
            # encoded_sign = base64.b64encode(encoded_sign).decode('utf-8')
            # result = self.client.invoke_function(CRYPTO_CONTRACT_HASH, "recoverSecp256K1",
            #                                      [{'type': 'ByteArray', 'value': message_hash},
            #                                       {'type': 'ByteArray', 'value': encoded_sign}])
            # self.logger.info(f"Invoke recoverSecp256k1 with sign result: {result}")
            # recovered_pubkey = base64.b64decode(result['stack'][0]['value']).hex()
            # count2 += (1 if recovered_pubkey == public_key.hex() else 0)
        assert count1 == 1, f"Expected 1 recovered public key, got {count1}"
        # assert count2 == 0, f"Expected 1 recovered public key, got {count2}"

    def run_test(self):
        self._check_recover_secp256k1_null_checking()
        self._check_recover_secp256k1_invalid_parameters()
        self._check_recover_secp256k1_examples()
        self._check_recover_secp256k1()


# Run with: python3 -B -m testcases.crypto.recover_secp256k1
if __name__ == "__main__":
    testing = RecoverSecp256k1()
    testing.run_test()
