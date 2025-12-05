#
# testcases/stdlib/string_ops.py file belongs to the neo project and is free
# software distributed under the MIT software license, see the
# accompanying file LICENSE in the main directory of the
# repository or http://www.opensource.org/licenses/mit-license.php
# for more details.
#
# Redistribution and use in source and binary forms with or without
# modifications are permitted.


import base64
from neo.contract import STDLIB_CONTRACT_HASH
from testcases.stdlib.base import StdLibTesting


class StringOps(StdLibTesting):

    def __init__(self):
        super().__init__("StringOps")

    def _check_string_split(self):
        # Step 1: check StringSplit(value, separator) with null value
        message = 'Specified cast is not valid'
        result = self.client.invoke_function(STDLIB_CONTRACT_HASH, "stringSplit",
                                             [{'type': 'String'}, {'type': 'String', 'value': ','}])
        self.logger.info(f"Invoke 'stringSplit' with null value result: {result}")
        assert 'exception' in result and message in result['exception']

        # Step 2: check StringSplit(value, separator) with null separator
        result = self.client.invoke_function(STDLIB_CONTRACT_HASH, "stringSplit",
                                             [{'type': 'String', 'value': 'hello,world'}, {'type': 'String'}])
        self.logger.info(f"Invoke 'stringSplit' with null separator result: {result}")
        assert 'exception' in result and 'Value cannot be null' in result['exception']

    def _check_string_len(self):
        # Step 1: check StringLen(value) with null value
        message = 'Specified cast is not valid'
        result = self.client.invoke_function(STDLIB_CONTRACT_HASH, "strLen", [{'type': 'String'}])
        self.logger.info(f"Invoke 'strLen' with null value result: {result}")
        assert 'exception' in result and message in result['exception']

    def run_test(self):
        self._check_string_split()
        self._check_string_len()


# Run with: python3 -B -m testcases.stdlib.string_ops
if __name__ == "__main__":
    test = StringOps()
    test.run()
