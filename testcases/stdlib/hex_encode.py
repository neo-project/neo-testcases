#
# testcases/stdlib/hex_encode.py file belongs to the neo project and is free
# software distributed under the MIT software license, see the
# accompanying file LICENSE in the main directory of the
# repository or http://www.opensource.org/licenses/mit-license.php
# for more details.
#
# Redistribution and use in source and binary forms with or without
# modifications are permitted.


from testcases.stdlib.base import StdLibTesting


class HexEncode(StdLibTesting):

    def __init__(self):
        super().__init__("HexEncode")

    def run_test(self):
        # Step 1: check call with null
        exception = 'Specified cast is not valid'  # Why 'Specified cast is not valid'?
        self.check_call_with_null("hexEncode", [], exception)

        # Step 2: check hexDecode with null
        self.check_call_with_null("hexDecode", [], exception)


# Run with: python3 -B -m testcases.stdlib.hex_encode
if __name__ == "__main__":
    test = HexEncode()
    test.run()
