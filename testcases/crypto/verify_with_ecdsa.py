
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
        stack = execution['stack']
        if exception is not None:
            assert execution['vmstate'] == 'FAULT'
            assert 'exception' in execution and exception in execution['exception']
        else:
            assert execution['vmstate'] == 'HALT'
            assert len(stack) == 1 and stack[0]['type'] == 'Boolean' and stack[0]['value'] == result

    def _check_invalid_parameters(self):
        # Step 1: verify with invalid parameter number.
        self.logger.info("Test verifyWithECDsa with null parameter")
        self._check_verify_with_ecdsa([None], exception='with 1 parameter(s) doesn\'t exist in the contract')

        # Step 2: verify with invalid public key.
        data = b"hello world"
        self.logger.info("Test verifyWithECDsa with valid secp256k1SHA256")
        # Invalid ECPoint encoding format: unknown prefix byte 0x31. Expected 0x02, 0x03 (compressed), or 0x04 (uncompressed).
        self._check_verify_with_ecdsa([data, b'1' * 64, b'2' * 64, NamedCurveHash.SECP256K1_SHA256],
                                      exception='Invalid ECPoint encoding format')

        # Step 3: verify with null public key.
        self.logger.info("Test verifyWithECDsa with null public key")
        self._check_verify_with_ecdsa([data, None, b'2' * 64, NamedCurveHash.SECP256K1_SHA256],
                                      exception="can't be null")

        # Step 4: verify with invalid signature.
        self.logger.info("Test verifyWithECDsa with invalid signature")
        private_key = ecdsa.SigningKey.generate(curve=ecdsa.NIST256p)
        public_key = private_key.get_verifying_key().to_string('compressed')
        self._check_verify_with_ecdsa([data, public_key, b'2' * 63, NamedCurveHash.SECP256R1_SHA256], result=False)

        # Step 5: verify with null signature.
        self.logger.info("Test verifyWithECDsa with null signature")
        # The behavior of verifyWithECDsa API is changed in HF_Faun, it return false before HF_Faun.
        self._check_verify_with_ecdsa([data, public_key, None, NamedCurveHash.SECP256R1_SHA256],
                                      exception="can't be null")

        # Step 6: verify public key with wrong named curve hash.
        self.logger.info("Test verifyWithECDsa with public key with wrong named curve hash")
        secp256r1_pubkey = bytes.fromhex('0285265dc8859d05e1e42a90d6c29a9de15531eac182489743e6a947817d2a9f66')
        self._check_verify_with_ecdsa([data, secp256r1_pubkey, b'2' * 64, NamedCurveHash.SECP256K1_SHA256],
                                      exception='The point compression is invalid')

        # Step 7: verify with invalid named curve hash.
        self.logger.info("Test verifyWithECDsa with invalid named curve hash")
        # Arithmetic operation resulted in an overflow.
        self._check_verify_with_ecdsa([data, public_key, b'2' * 64, 0xFFff], exception='an overflow')

        # Step 8: verify with unknown named curve hash.
        self.logger.info("Test verifyWithECDsa with invalid named curve hash")
        # The given key '99' was not present in the dictionary.
        self._check_verify_with_ecdsa([data, public_key, b'2' * 64, 99], exception='not present in the dictionary')

    def _check_secp256k1(self):
        # Step 1: verify with valid secp256k1SHA256
        self.logger.info("Test verifyWithECDsa with valid secp256k1SHA256")

        data = b"hello world"
        private_key = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
        public_key = private_key.get_verifying_key().to_string('compressed')
        signature = private_key.sign(data, hashfunc=hashlib.sha256)
        self._check_verify_with_ecdsa([data, public_key, signature, NamedCurveHash.SECP256K1_SHA256], result=True)

        # Step 2: verify with valid secp256k1KECCAK256
        self.logger.info("Test verifyWithECDsa with valid secp256k1KECCAK256")
        signature = private_key.sign(data, hashfunc=sha3.keccak_256)
        self._check_verify_with_ecdsa([data, public_key, signature, NamedCurveHash.SECP256K1_KECCAK256], result=True)

        # Step 3: verify with mismatch signature.
        self.logger.info("Test verifyWithECDsa with mismatch signature")
        self._check_verify_with_ecdsa([data, public_key, b'2' * 64, NamedCurveHash.SECP256K1_SHA256], result=False)

        # step 4: verify with null message.
        self.logger.info("Test verifyWithECDsa with null message")
        signature = private_key.sign(b'', hashfunc=hashlib.sha256)
        # True even if the message is null.
        # self._check_verify_with_ecdsa([None, public_key, signature, NamedCurveHash.SECP256K1_SHA256], result=True)
        # The behavior of verifyWithECDsa API is changed in HF_Faun, OK even if the message is null before HF_Faun.
        self._check_verify_with_ecdsa([None, public_key, signature, NamedCurveHash.SECP256K1_SHA256],
                                      exception="can't be null")

    def _check_secp256r1(self):
        # Step 1: verify with valid secp256r1SHA256
        self.logger.info("Test verifyWithECDsa with valid secp256r1SHA256")

        data = b"hello world"
        private_key = ecdsa.SigningKey.generate(curve=ecdsa.NIST256p)
        public_key = private_key.get_verifying_key().to_string('compressed')
        signature = private_key.sign(data, hashfunc=hashlib.sha256)
        self._check_verify_with_ecdsa([data, public_key, signature, NamedCurveHash.SECP256R1_SHA256], result=True)

        # Step 2: verify with valid secp256r1KECCAK256
        self.logger.info("Test verifyWithECDsa with valid secp256r1KECCAK256")
        signature = private_key.sign(data, hashfunc=sha3.keccak_256)
        self._check_verify_with_ecdsa([data, public_key, signature, NamedCurveHash.SECP256R1_KECCAK256], result=True)

        # Step 3: verify with mismatch signature.
        self.logger.info("Test verifyWithECDsa with mismatch signature")
        self._check_verify_with_ecdsa([data, public_key, b'2' * 64, NamedCurveHash.SECP256R1_SHA256], result=False)

        # step 4: verify with null message.
        self.logger.info("Test verifyWithECDsa with null message")
        signature = private_key.sign(b'', hashfunc=hashlib.sha256)
        # self._check_verify_with_ecdsa([None, public_key, signature, NamedCurveHash.SECP256R1_SHA256], result=True)
        # The behavior of verifyWithECDsa API is changed in HF_Faun, OK even if the message is null before HF_Faun.
        self._check_verify_with_ecdsa([None, public_key, signature, NamedCurveHash.SECP256R1_SHA256],
                                      exception="can't be null")

    def run_test(self):
        self._check_invalid_parameters()
        self._check_secp256k1()
        self._check_secp256r1()


# Run with: python3 -B -m testcases.crypto.verify_with_ecdsa
if __name__ == "__main__":
    test = VerifyWithEcdsa()
    test.run()
