#
# testcases/stdlib/base58_encode.py file belongs to the neo project and is free
# software distributed under the MIT software license, see the
# accompanying file LICENSE in the main directory of the
# repository or http://www.opensource.org/licenses/mit-license.php
# for more details.
#
# Redistribution and use in source and binary forms with or without
# modifications are permitted.


import base64
from typing import Union

from neo.contract import STDLIB_CONTRACT_HASH, CallFlags, ScriptBuilder
from testcases.testing import Testing


class StdLibTesting(Testing):

    def __init__(self, loggerName: str = "StdLibTesting"):
        super().__init__(loggerName)
        self.max_size_limit = 1024

    def check_call_with_null(self, method: str,
                             pramater_type: str = 'ByteArray',
                             stack: list[tuple[str, str]] = [],
                             exception: str | None = None):
        # Step 1: check invoke with null
        result = self.client.invoke_function(STDLIB_CONTRACT_HASH, method, [{'type': pramater_type}])
        self.logger.info(f"Invoke '{method}' with null result: {result}")

        if exception is not None:
            assert 'exception' in result and exception in result['exception']
        else:
            assert 'exception' not in result or result['exception'] is None
            self.check_stack(result['stack'], stack)

        # Step 2: send a transaction with null
        script = ScriptBuilder().emit_dynamic_call(STDLIB_CONTRACT_HASH,
                                                   method, CallFlags.READ_STATES, [None]).to_bytes()
        tx = self.make_tx(self.env.validators[0], script, self.default_sysfee,
                          self.default_netfee, self.client.get_block_index() + 10)
        tx_id = self.client.send_raw_tx(tx.to_array())['hash']
        self.logger.info(f"Tx '{method}' null transaction sent: {tx_id}")

        block_index = self.client.get_block_index()
        self.wait_next_block(block_index)

        application_log = self.client.get_application_log(tx_id)
        self.logger.info(f"Application log with '{method}' null: {application_log}")
        execution = application_log['executions'][0]
        assert 'trigger' in execution and execution['trigger'] == 'Application'

        if exception is not None:
            assert execution['vmstate'] == 'FAULT'
            assert 'exception' in execution and exception in execution['exception']
        else:
            assert execution['vmstate'] == 'HALT'
            assert 'exception' not in execution or execution['exception'] is None
            self.check_stack(execution['stack'], stack)

    def check_size_limit(self, method: str, pramater_type: str = 'ByteArray',
                         arg_2nd: Union[dict[str, str], None] = None):
        if pramater_type == 'ByteArray':
            source = base64.b64encode(b'0' * (self.max_size_limit + 1)).decode('utf-8')
        elif pramater_type == 'String':
            source = '0' * (self.max_size_limit + 1)
        else:
            raise ValueError(f"Invalid parameter type: {pramater_type}")

        args = [{'type': pramater_type, 'value': source}]
        if arg_2nd is not None:
            args.append(arg_2nd)
        result = self.client.invoke_function(STDLIB_CONTRACT_HASH, method, args)
        self.logger.info(f"Invoke '{method}' with size limit result: {result}")
        assert 'exception' in result and 'The input exceeds the maximum length' in result['exception']
