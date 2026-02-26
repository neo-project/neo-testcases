
from neo import Hardforks
from neo.contract import *
from testcases.testing import Testing


# Operation: this case tests the exec_pico_fee_factor(get ExecPicoFeeFactor) policy.
#  1. getExecPicoFeeFactor available after HF_Faun, and 1 Datoshi = 10000 PicoGAS.
# Expect Result: The exec_pico_fee_factor policy is working as expected.
class ExecPicoFeeFactor(Testing):

    def __init__(self):
        super().__init__("ExecPicoFeeFactor")
        self.fee_factor = 10000  # 1 Datoshi = 10000 PicoGAS
        self.hardfork = Hardforks.HF_Faun

    def run_test(self):
        # Step 1: get the original exec_pico_fee_factor
        result = self.client.invoke_function(POLICY_CONTRACT_HASH, "getExecPicoFeeFactor", [])
        exec_pico_fee_factor = int(result['stack'][0]['value'])

        # Step 2: get the original exec_fee_factor
        result = self.client.invoke_function(POLICY_CONTRACT_HASH, "getExecFeeFactor", [])
        exec_fee_factor = int(result['stack'][0]['value'])

        # Step 3: check the exec_pico_fee_factor is working as expected
        assert exec_pico_fee_factor == exec_fee_factor * self.fee_factor


if __name__ == "__main__":
    test = ExecPicoFeeFactor()
    test.run_test()
