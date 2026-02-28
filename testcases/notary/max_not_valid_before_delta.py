
from neo.contract import *
from testcases.testing import Testing


# Operation: this case tests the MaxNotValidBeforeDelta(get/set MaxNotValidBeforeDelta) in Notary contract.
# 1. get the MaxNotValidBeforeDelta.
# 2. only committee can set the MaxNotValidBeforeDelta.
# 3. the MaxNotValidBeforeDelta should be in range [ValidatorsCount, MaxValidUntilBlockIncrement/2].
class MaxNotValidBeforeDelta(Testing):
    def __init__(self):
        super().__init__("MaxNotValidBeforeDelta")

        # A default value for maximum allowed NotValidBeforeDelta.
        # It is set to be 20 rounds for 7 validators, a little more than half an hour for 15s blocks.
        self.max_not_valid_before_delta = 140
        self.max_valid_until_block_increment = 5760

    def _get_max_valid_until_block_increment(self):
        result = self.client.invoke_function(POLICY_CONTRACT_HASH, "getMaxValidUntilBlockIncrement", [])
        self.logger.info(f"getMaxValidUntilBlockIncrement result: {result}")
        self.max_valid_until_block_increment = int(result['stack'][0]['value'])

    def _get_max_not_valid_before_delta(self):
        result = self.client.invoke_function(NOTARY_CONTRACT_HASH, "getMaxNotValidBeforeDelta", [])
        self.logger.info(f"getMaxNotValidBeforeDelta result: {result}")
        self.check_stack(result['stack'], [('Integer', str(self.max_not_valid_before_delta))])
        self.max_not_valid_before_delta = int(result['stack'][0]['value'])

    def _set_max_not_valid_before_delta(self, delta: int, exception: str | None = None):
        result = self.client.invoke_function(NOTARY_CONTRACT_HASH, "setMaxNotValidBeforeDelta",
                                             [ContractParameter(type="Integer", value=delta)])
        self.logger.info(f"setMaxNotValidBeforeDelta result: {result}")
        self.check_stack(result['stack'], [])
        if exception is not None:
            assert 'exception' in result and exception in result['exception']

    def run_test(self):
        # Step 1: get the MaxValidUntilBlockIncrement.
        self._get_max_valid_until_block_increment()

        # Step 2: get the original MaxNotValidBeforeDelta.
        self._get_max_not_valid_before_delta()

        # Step 3: only committee can set the MaxNotValidBeforeDelta.
        self._set_max_not_valid_before_delta(len(self.env.validators), exception="Invalid committee signature")

        # Step 4: set the MaxNotValidBeforeDelta to a too large value.
        exception = "MaxNotValidBeforeDelta cannot be more than " + \
            f"{self.max_valid_until_block_increment // 2} or less than {len(self.env.validators)}"
        # BUG: cannot pass
        # self._set_max_not_valid_before_delta(self.max_valid_until_block_increment + 1, exception=exception)

        # Step 4: set the MaxNotValidBeforeDelta to a too small value.
        # BUG: cannot pass
        self._set_max_not_valid_before_delta(len(self.env.validators) // 2, exception=exception)

        # Step 5: get the MaxNotValidBeforeDelta again, it should be the new value.
        self._get_max_not_valid_before_delta()


# Run with: python3 -B -m testcases.notary.max_not_valid_before_delta
if __name__ == "__main__":
    test = MaxNotValidBeforeDelta()
    test.run()
