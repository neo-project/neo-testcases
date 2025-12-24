#
# testcases/stdlib/base58_encode.py file belongs to the neo project and is free
# software distributed under the MIT software license, see the
# accompanying file LICENSE in the main directory of the
# repository or http://www.opensource.org/licenses/mit-license.php
# for more details.
#
# Redistribution and use in source and binary forms with or without
# modifications are permitted.


from neo.contract import STDLIB_CONTRACT_HASH
from testcases.stdlib.base import StdLibTesting


# Operation: this case tests the base58Encode method in StdLib contract.
# Method: Base58Encode(byte[] data) -> string
#  1. The data cannot be null, if the data is null, it will fail.
#  2. If the data is not null, it will return the base58 encoded string.
# Method: Base58Decode(string data) -> byte[]
#  1. The data cannot be null, if the data is null, it will fail.
#  2. If the data is not a valid base58 encoded string, it will fail.
#  3. If the data is not null and valid base58 encoded string, it will return the base58 decoded bytes.
# Expect Result: The base58Encode method is working as expected.
class Base58Encode(StdLibTesting):

    def __init__(self):
        super().__init__("Base58Encode")

    def _check_argument_null(self):
        # Step 1: check base58Encode with null
        exception = 'Specified cast is not valid'  # Why 'Specified cast is not valid'?
        self.check_call_with_null("base58Encode", [], exception)

        # Step 2: check base58Decode with null
        self.check_call_with_null("base58Decode", [], exception)

    def _check_invalid_base58(self):
        encoded = "0000"
        result = self.client.invoke_function(STDLIB_CONTRACT_HASH, "base58Decode",
                                             [{'type': 'String', 'value': encoded}])
        self.logger.info(f"Invoke 'base58Decode' with invalid base58 encoded string result: {result}")
        assert 'exception' in result and 'nvalid Base58' in result['exception']

    def run_test(self):
        self._check_argument_null()
        self._check_invalid_base58()

        # TODO: check normal cases


# Run with: python3 -B -m testcases.stdlib.base58_encode
if __name__ == "__main__":
    test = Base58Encode()
    test.run()
