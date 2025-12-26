#
# testcases/stdlib/base64_encode.py file belongs to the neo project and is free
# software distributed under the MIT software license, see the
# accompanying file LICENSE in the main directory of the
# repository or http://www.opensource.org/licenses/mit-license.php
# for more details.
#
# Redistribution and use in source and binary forms with or without
# modifications are permitted.


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
        exception = 'Specified cast is not valid'  # Why 'Specified cast is not valid'?
        self.check_call_with_null("base64Encode", stack=[], exception=exception)

        # Step 2: check base64Decode with null
        self.check_call_with_null("base64Decode", stack=[], exception=exception)

    def _check_invalid_base64(self):
        encoded = "????"
        result = self.client.invoke_function(STDLIB_CONTRACT_HASH, "base64Decode",
                                             [{'type': 'String', 'value': encoded}])
        self.logger.info(f"Invoke 'base64Decode' with invalid base64 encoded string result: {result}")
        assert 'exception' in result and 'The input is not a valid Base-64 string' in result['exception']

    def run_test(self):
        # Step 1: Check argument is null
        self._check_argument_null()

        # Step 2: Check invalid base64
        self._check_invalid_base64()

        # Step 3: Check length limit
        self.check_size_limit("base64Encode", pramater_type='ByteArray')

        # TODO: check normal cases


# Run with: python3 -B -m testcases.stdlib.base64_encode
if __name__ == "__main__":
    test = Base64Encode()
    test.run()
