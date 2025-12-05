#
# testcases/stdlib/json_serialize.py file belongs to the neo project and is free
# software distributed under the MIT software license, see the
# accompanying file LICENSE in the main directory of the
# repository or http://www.opensource.org/licenses/mit-license.php
# for more details.
#
# Redistribution and use in source and binary forms with or without
# modifications are permitted.


import base64
from testcases.stdlib.base import StdLibTesting


class JsonSerialize(StdLibTesting):

    def __init__(self):
        super().__init__("JsonSerialize")

    def run_test(self):
        # Step 1: check JsonSerialize with null
        value = base64.b64encode(b'null').decode('utf-8')
        self.check_call_with_null("jsonSerialize", [('ByteString', value)], exception=None)

        # Step 2: check jsonDeserialize with null
        self.check_call_with_null("jsonDeserialize", [], exception='The input does not contain any JSON tokens')


# Run with: python3 -B -m testcases.stdlib.json_serialize
if __name__ == "__main__":
    test = JsonSerialize()
    test.run()
