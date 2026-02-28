
from neo.contract import *
from testcases.testing import Testing


class Deposit(Testing):
    def __init__(self):
        super().__init__("Deposit")

    def _get_deposit_balance(self, account: str, expected: str):
        result = self.client.invoke_function(NOTARY_CONTRACT_HASH, "balanceOf",
                                             [ContractParameter(type="Hash160", value=account)])
        self.logger.info(f"balanceOf result: {result}")
        self.check_stack(result['stack'], expected=[('Integer', expected)])
        assert 'exception' not in result or result['exception'] is None, f"Expected no exception, got {result}"

    def run_test(self):
        account = str(self.env.others[0].script_hash)
        self._get_deposit_balance(account, "0")


# Run with: python3 -B -m testcases.notary.deposit
if __name__ == "__main__":
    test = Deposit()
    test.run()
