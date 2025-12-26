#
# testcases/stdlib/hex_encode.py file belongs to the neo project and is free
# software distributed under the MIT software license, see the
# accompanying file LICENSE in the main directory of the
# repository or http://www.opensource.org/licenses/mit-license.php
# for more details.
#
# Redistribution and use in source and binary forms with or without
# modifications are permitted.


from neo import Hardforks
from neo.contract import STDLIB_CONTRACT_HASH
from testcases.stdlib.base import StdLibTesting


class HexEncode(StdLibTesting):

    def __init__(self):
        super().__init__("HexEncode")
        self.hardfork = Hardforks.HF_Faun

    def _check_argument_null(self):
        # Step 1: check hexEncode with null
        exception = 'Specified cast is not valid'  # Why 'Specified cast is not valid'?
        self.check_call_with_null("hexEncode", stack=[], exception=exception)

        # Step 2: check hexDecode with null
        self.check_call_with_null("hexDecode", stack=[], exception=exception)

    def _check_invalid_hex(self):
        encoded = "????"
        result = self.client.invoke_function(STDLIB_CONTRACT_HASH, "hexDecode",
                                             [{'type': 'String', 'value': encoded}])
        self.logger.info(f"Invoke 'hexDecode' with invalid hex encoded string result: {result}")
        assert 'exception' in result and 'The input is not a valid hex string' in result['exception']

    def run_test(self):
        # Step 1: Check argument with null
        self._check_argument_null()

        # Step 2: Check invalid hex
        self._check_invalid_hex()

        # Step 3: Check size limit
        self.check_size_limit("hexEncode", pramater_type='ByteArray')
        self.check_size_limit("hexDecode", pramater_type='String')

        # Step 3: Check normal cases
        # self._check_normal_cases()


# Run with: python3 -B -m testcases.stdlib.hex_encode
if __name__ == "__main__":
    test = HexEncode()
    test.run()
