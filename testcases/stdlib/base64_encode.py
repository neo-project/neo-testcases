
import base64

from neo.contract import STDLIB_CONTRACT_HASH
from testcases.stdlib.base import StdLibTesting


# Operation: this case tests the base64Encode method in StdLib contract.
# Method: Base64Encode(byte[] data) -> string
#  1. The data cannot be null, if the data is null, it will fail.
#  2. The data size cannot exceed 1024 bytes, if the data size exceeds 1024 bytes, it will fail.
#  3. If the data is not null, it will return the base64 encoded string.
# Method: Base64Decode(string data) -> byte[]
#  1. The data cannot be null, if the data is null, it will fail.
#  2. The data size cannot exceed 1024 bytes, if the data size exceeds 1024 bytes, it will fail.
#  3. If the data is not a valid base64 encoded string, it will fail.
#  4. If the data is not null and valid base64 encoded string, it will return the base64 decoded bytes.
# Expect Result: The base64Encode method is working as expected.
class Base64Encode(StdLibTesting):

    def __init__(self):
        super().__init__("Base64Encode")

    def _check_argument_null(self):
        # Step 1: check base64Encode with null
        self.check_call_with_null("base64Encode", stack=[], exception="can't be null")

        # Step 2: check base64Decode with null
        self.check_call_with_null("base64Decode", stack=[], exception="can't be null")

    def _check_invalid_base64(self):
        encoded = "????"
        result = self.client.invoke_function(STDLIB_CONTRACT_HASH, "base64Decode",
                                             [{'type': 'String', 'value': encoded}])
        self.logger.info(f"Invoke 'base64Decode' with invalid base64 encoded string result: {result}")
        assert 'exception' in result and 'The input is not a valid Base-64 string' in result['exception']

    def _check_normal_cases(self):
        source_bytes = b'0123456789abcdef'
        source = base64.b64encode(source_bytes).decode('utf-8')

        result = self.client.invoke_function(STDLIB_CONTRACT_HASH, "base64Encode",
                                             [{'type': 'ByteArray', 'value': source}])
        self.logger.info(f"Invoke 'base64Encode' with normal data result: {result}")
        assert 'exception' not in result or result['exception'] is None

        encoded = base64.b64encode(source_bytes)
        expected = base64.b64encode(encoded).decode('utf-8')
        self.check_stack(result['stack'], [('ByteString', expected)])

        result = self.client.invoke_function(STDLIB_CONTRACT_HASH, "base64Decode",
                                             [{'type': 'String', 'value': encoded.decode('utf-8')}])
        self.logger.info(f"Invoke 'base64Decode' with normal data result: {result}")
        assert 'exception' not in result or result['exception'] is None
        self.check_stack(result['stack'], [('ByteString', source)])

    def run_test(self):
        # Step 1: Check argument is null
        self._check_argument_null()

        # Step 2: Check invalid base64
        self._check_invalid_base64()

        # Step 3: Check length limit
        self.check_size_limit("base64Encode", pramater_type='ByteArray')

        # Step 4: Check normal cases
        self._check_normal_cases()


# Run with: python3 -B -m testcases.stdlib.base64_encode
if __name__ == "__main__":
    test = Base64Encode()
    test.run()
