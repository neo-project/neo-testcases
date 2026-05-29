
import base64

from neo import Hardforks
from neo.contract import STDLIB_CONTRACT_HASH
from testcases.stdlib.base import StdLibTesting


class HexEncode(StdLibTesting):

    def __init__(self):
        super().__init__("HexEncode")
        self.hardfork = Hardforks.HF_Faun

    def _check_argument_null(self):
        # Step 1: check hexEncode with null
        self.check_call_with_null("hexEncode", stack=[], exception="can't be null")

        # Step 2: check hexDecode with null
        self.check_call_with_null("hexDecode", stack=[], exception="can't be null")

    def _check_invalid_hex(self):
        encoded = "????"
        result = self.client.invoke_function(STDLIB_CONTRACT_HASH, "hexDecode",
                                             [{'type': 'String', 'value': encoded}])
        self.logger.info(f"Invoke 'hexDecode' with invalid hex encoded string result: {result}")
        assert 'exception' in result and 'The input is not a valid hex string' in result['exception']

    def _check_normal_cases(self):
        source_bytes = b'0123456789abcdef'
        source = base64.b64encode(source_bytes).decode('utf-8')

        result = self.client.invoke_function(STDLIB_CONTRACT_HASH, "hexEncode",
                                             [{'type': 'ByteArray', 'value': source}])
        self.logger.info(f"Invoke 'hexEncode' with normal data result: {result}")
        assert 'exception' not in result or result['exception'] is None

        encoded = source_bytes.hex()
        expected = base64.b64encode(encoded.encode('utf-8')).decode('utf-8')
        self.check_stack(result['stack'], [('ByteString', expected)])

        result = self.client.invoke_function(STDLIB_CONTRACT_HASH, "hexDecode",
                                             [{'type': 'String', 'value': encoded}])
        self.logger.info(f"Invoke 'hexDecode' with normal data result: {result}")
        assert 'exception' not in result or result['exception'] is None
        self.check_stack(result['stack'], [('ByteString', source)])

    def run_test(self):
        # Step 1: Check argument with null
        self._check_argument_null()

        # Step 2: Check invalid hex
        self._check_invalid_hex()

        # Step 3: Check `hexEncode` size limit
        self.check_size_limit("hexEncode", pramater_type='ByteArray')

        # Step 4: Check `hexDecode` size limit
        self.check_size_limit("hexDecode", pramater_type='String')

        # Step 5: Check normal cases
        self._check_normal_cases()


# Run with: python3 -B -m testcases.stdlib.hex_encode
if __name__ == "__main__":
    test = HexEncode()
    test.run()
