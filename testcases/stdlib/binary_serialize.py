#
# testcases/stdlib/binary_serialize.py file belongs to the neo project and is free
# software distributed under the MIT software license, see the
# accompanying file LICENSE in the main directory of the
# repository or http://www.opensource.org/licenses/mit-license.php
# for more details.
#
# Redistribution and use in source and binary forms with or without
# modifications are permitted.


import base64
from testcases.stdlib.base import StdLibTesting


class BinarySerialize(StdLibTesting):

    def __init__(self):
        super().__init__("BinarySerialize")

    def run_test(self):
        # Step 1: check serialize with null
        self.logger.info(f"serialize null value: {base64.b64decode(b'AA==').hex()}")  # 00
        self.check_call_with_null("serialize", [('ByteString', 'AA==')], exception=None)

        # Step 2: check deserialize with null
        message = 'Position 0 + Wanted 1 is exceeded boundary(0)'
        self.check_call_with_null("deserialize", [], exception=message)


# Run with: python3 -B -m testcases.stdlib.binary_serialize
if __name__ == "__main__":
    test = BinarySerialize()
    test.run()
