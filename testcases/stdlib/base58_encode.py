#
# testcases/stdlib/base58_encode.py file belongs to the neo project and is free
# software distributed under the MIT software license, see the
# accompanying file LICENSE in the main directory of the
# repository or http://www.opensource.org/licenses/mit-license.php
# for more details.
#
# Redistribution and use in source and binary forms with or without
# modifications are permitted.


from testcases.stdlib.base import StdLibTesting


class Base58Encode(StdLibTesting):

    def __init__(self):
        super().__init__("Base58Encode")

    def run_test(self):
        # Step 1: check base58Encode with null
        exception = 'Specified cast is not valid'  # Why 'Specified cast is not valid'?
        self.check_call_with_null("base58Encode", [], exception)

        # Step 2: check base58Decode with null
        self.check_call_with_null("base58Decode", [], exception)


# Run with: python3 -B -m testcases.stdlib.base58_encode
if __name__ == "__main__":
    test = Base58Encode()
    test.run()
