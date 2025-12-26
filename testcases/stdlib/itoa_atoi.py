#
# testcases/stdlib/itoa_atoi.py file belongs to the neo project and is free
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


class ItoaAtoi(StdLibTesting):

    def __init__(self):
        super().__init__("ItoaAtoi")

    def _check_argument_null(self):
        # Step 1: check Itoa with null
        exception = 'Specified cast is not valid'  # Why 'Specified cast is not valid'?
        self.check_call_with_null("itoa", stack=[], exception=exception)

        # Step 2: check Atoi with null
        self.check_call_with_null("atoi", stack=[], exception=exception)

        # Step 2: check Itoa with null string
        result = self.client.invoke_function(STDLIB_CONTRACT_HASH, 'itoa', [{'type': 'String'}])
        self.logger.info(f"Invoke 'itoa' with null string result: {result}")
        assert 'exception' in result and 'Specified cast is not valid' in result['exception']

    def _check_atoi_base10(self):
        # Step 1: check Atoi with '0' string
        result = self.client.invoke_function(STDLIB_CONTRACT_HASH, 'atoi', [{'type': 'String', 'value': '0'}])
        self.logger.info(f"Invoke 'atoi' with '0' string result: {result}")
        assert 'exception' not in result or result['exception'] is None
        assert result['stack'][0]['type'] == 'Integer' and result['stack'][0]['value'] == '0'

        # Step 2: check Atoi with '00' string
        result = self.client.invoke_function(STDLIB_CONTRACT_HASH, 'atoi', [{'type': 'String', 'value': '00'}])
        self.logger.info(f"Invoke 'atoi' with '00' string result: {result}")
        assert 'exception' not in result or result['exception'] is None
        assert result['stack'][0]['type'] == 'Integer' and result['stack'][0]['value'] == '0'

        # Step 3: check Atoi with '01' string
        result = self.client.invoke_function(STDLIB_CONTRACT_HASH, 'atoi', [{'type': 'String', 'value': '01'}])
        self.logger.info(f"Invoke 'atoi' with '01' string result: {result}")
        assert 'exception' not in result or result['exception'] is None
        assert result['stack'][0]['type'] == 'Integer' and result['stack'][0]['value'] == '1'

    def _check_atoi_base16(self):
        # Step 1: check Atoi with '0' string
        result = self.client.invoke_function(STDLIB_CONTRACT_HASH, 'atoi',
                                             [{'type': 'String', 'value': '0'}, {'type': 'Integer', 'value': 16}])
        self.logger.info(f"Invoke 'atoi' with '0x0' string result: {result}")
        assert 'exception' not in result or result['exception'] is None
        assert result['stack'][0]['type'] == 'Integer' and result['stack'][0]['value'] == '0'

        # Step 2: check Atoi with 'FF' string
        result = self.client.invoke_function(STDLIB_CONTRACT_HASH, 'atoi',
                                             [{'type': 'String', 'value': 'FF'}, {'type': 'Integer', 'value': 16}])
        self.logger.info(f"Invoke 'atoi' with '0x01' string result: {result}")
        assert 'exception' not in result or result['exception'] is None
        assert result['stack'][0]['type'] == 'Integer' and result['stack'][0]['value'] == '-1'  # NOTE: -1

        # Step 3: check Atoi with '7F' string
        result = self.client.invoke_function(STDLIB_CONTRACT_HASH, 'atoi',
                                             [{'type': 'String', 'value': '7F'}, {'type': 'Integer', 'value': 16}])
        self.logger.info(f"Invoke 'atoi' with '0x7F' string result: {result}")
        assert 'exception' not in result or result['exception'] is None
        assert result['stack'][0]['type'] == 'Integer' and result['stack'][0]['value'] == '127'

    def run_test(self):
        # Step 1: check Itoa and Atoi with null
        self._check_argument_null()

        # Step 2: check Atoi base10
        self._check_atoi_base10()

        # Step 3: check Atoi base16
        self._check_atoi_base16()

        # Step 4: check Atoi size limit
        self.check_size_limit('atoi', pramater_type='String')


# Run with: python3 -B -m testcases.stdlib.itoa_atoi
if __name__ == "__main__":
    test = ItoaAtoi()
    test.run()
