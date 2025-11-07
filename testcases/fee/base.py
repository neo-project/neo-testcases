# Copyright (C) 2015-2025 The Neo Project.
#
# testcases/fee/base.py file belongs to the neo project and is free
# software distributed under the MIT software license, see the
# accompanying file LICENSE in the main directory of the
# repository or http://www.opensource.org/licenses/mit-license.php
# for more details.
#
# Redistribution and use in source and binary forms with or without
# modifications are permitted.


from neo.contract import POLICY_CONTRACT_HASH
from testcases.testing import Testing


class FeeTesting(Testing):

    def __init__(self, loggerName: str = "FeeTesting"):
        super().__init__(loggerName)
        self.exec_fee_factor = 30
        self.fee_per_byte = 1000

    def pre_test(self):
        # Step 0: super().pre_test()
        super().pre_test()

        # Step 1: get the exec_fee_factor
        result = self.client.invoke_function(POLICY_CONTRACT_HASH, "getExecFeeFactor", [])
        assert 'stack' in result and len(result['stack']) == 1, f"Expected 'stack' in result, got {result}"
        self.exec_fee_factor = int(result['stack'][0]['value'])

        # Step 2: get the fee_per_byte
        result = self.client.invoke_function(POLICY_CONTRACT_HASH, "getFeePerByte", [])
        assert 'stack' in result and len(result['stack']) == 1, f"Expected 'stack' in result, got {result}"
        self.fee_per_byte = int(result['stack'][0]['value'])
