#
# testcases/stdlib/base58check_encode.py file belongs to the neo project and is free
# software distributed under the MIT software license, see the
# accompanying file LICENSE in the main directory of the
# repository or http://www.opensource.org/licenses/mit-license.php
# for more details.
#
# Redistribution and use in source and binary forms with or without
# modifications are permitted.


from testcases.stdlib.base import StdLibTesting


class Base58CheckEncode(StdLibTesting):

    def __init__(self):
        super().__init__("Base58CheckEncode")

    def run_test(self):
        # Step 1: check base58CheckEncode with null
        exception = 'Specified cast is not valid'  # Why 'Specified cast is not valid'?
        self.check_call_with_null("base58CheckEncode", [], exception)

        # Step 2: check base58CheckDecode with null
        self.check_call_with_null("base58CheckDecode", [], exception)


# Run with: python3 -B -m testcases.stdlib.base58check_encode
if __name__ == "__main__":
    test = Base58CheckEncode()
    test.run()
