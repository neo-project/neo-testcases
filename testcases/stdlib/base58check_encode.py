
from neo.contract import STDLIB_CONTRACT_HASH
from testcases.stdlib.base import StdLibTesting


# Operation: this case tests the base58CheckEncode method in StdLib contract.
# Method: Base58CheckEncode(byte[] data) -> string
#  1. The data cannot be null, if the data is null, it will fail.
#  2. If the data is not null, it will return the base58Check encoded string.
# Method: Base58CheckDecode(string data) -> byte[]
#  1. The data cannot be null, if the data is null, it will fail.
#  2. If the data is not a valid base58Check encoded string, it will fail.
#  3. If the data is not null and valid base58Check encoded string, it will return the base58Check decoded bytes.
# Expect Result: The base58CheckEncode method is working as expected.
class Base58CheckEncode(StdLibTesting):

    def __init__(self):
        super().__init__("Base58CheckEncode")

    def _check_argument_null(self):
        # Step 1: check base58CheckEncode with null
        exception = 'Specified cast is not valid'  # Why 'Specified cast is not valid'?
        self.check_call_with_null("base58CheckEncode", stack=[], exception=exception)

        # Step 2: check base58CheckDecode with null
        self.check_call_with_null("base58CheckDecode", stack=[], exception=exception)

    def _check_invalid_base58check(self):
        encoded = "0000"
        result = self.client.invoke_function(STDLIB_CONTRACT_HASH, "base58CheckDecode",
                                             [{'type': 'String', 'value': encoded}])
        self.logger.info(f"Invoke 'base58CheckDecode' with invalid base58Check encoded string result: {result}")
        assert 'exception' in result and 'Invalid Base58' in result['exception']

    def run_test(self):
        # Step 1: Check base58CheckEncode and base58CheckDecode with null
        self._check_argument_null()

        # Step 2: Check base58CheckDecode with invalid base58Check encoded string
        self._check_invalid_base58check()

        # Step 3: Check length limit
        self.check_size_limit("base58Encode", pramater_type='ByteArray')

        # TODO: check normal cases


# Run with: python3 -B -m testcases.stdlib.base58check_encode
if __name__ == "__main__":
    test = Base58CheckEncode()
    test.run()
