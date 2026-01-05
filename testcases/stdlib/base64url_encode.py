
import base64

from neo import Hardforks
from neo.contract import STDLIB_CONTRACT_HASH
from testcases.stdlib.base import StdLibTesting


# Operation: this case tests the Base64UrlEncode method in StdLib contract.
# Method: Base64UrlEncode(byte[] data) -> string
#  1. The data cannot be null, if the data is null, it will fail.
#  2. If the data is not null, it will return the base64url encoded string.
# Method: Base64UrlDecode(string data) -> byte[]
#  1. The data cannot be null, if the data is null, it will fail.
#  2. If the data is not a valid base64url encoded string, it will fail.
#  3. If the data is not null and valid base64url encoded string, it will return the base64url decoded bytes.
# Expect Result: The base64UrlEncode method is working as expected.
class Base64UrlEncode(StdLibTesting):

    def __init__(self):
        super().__init__("Base64UrlEncode")
        self.hardfork = Hardforks.HF_Echidna

    def _check_argument_null(self):
        # Step 1: check base64UrlEncode with null
        exception = 'Specified cast is not valid'  # Why 'Specified cast is not valid'?
        self.check_call_with_null("base64UrlEncode", stack=[], exception=exception)

        # Step 2: check base64UrlDecode with null
        self.check_call_with_null("base64UrlDecode", stack=[], exception=exception)

    def _check_invalid_base64url(self):
        encoded = "????"
        result = self.client.invoke_function(STDLIB_CONTRACT_HASH, "base64UrlDecode",
                                             [{'type': 'String', 'value': encoded}])
        self.logger.info(f"Invoke 'base64UrlDecode' with invalid base64url encoded string result: {result}")

        # Weird exception message
        assert 'exception' in result and 'Unable to decode' in result['exception']

    def _check_encode_normal_cases(self):
        # Step 1: check base64UrlEncode with normal data
        source = '0123456789abcdef'
        result = self.client.invoke_function(STDLIB_CONTRACT_HASH, "base64UrlEncode",
                                             [{'type': 'String', 'value': source}])
        self.logger.info(f"Invoke 'base64UrlEncode' with normal data result: {result}")
        assert 'exception' not in result or result['exception'] is None

        # encoded-twice, because the return value has another encoding
        expected = base64.b64encode(base64.urlsafe_b64encode(b'0123456789abcdef')).decode('utf-8')
        assert result['stack'][0]['type'] == 'ByteString'
        assert result['stack'][0]['value'] == expected, f"Expected {expected}, got {result['stack'][0]['value']}"

    def run_test(self):
        # Step 1: Check base64UrlEncode and base64UrlDecode with null
        self._check_argument_null()

        # Step 2: Check base64UrlDecode with invalid base64url encoded string
        self._check_invalid_base64url()

        # Step 3: Check length limit
        self.check_size_limit("base64UrlEncode", pramater_type='ByteArray')

        # Step 4: Check normal cases
        # self._check_encode_normal_cases() # TODO: fix this


# Run with: python3 -B -m testcases.stdlib.base64url_encode
if __name__ == "__main__":
    test = Base64UrlEncode()
    test.run()
