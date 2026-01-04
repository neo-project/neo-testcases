
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
