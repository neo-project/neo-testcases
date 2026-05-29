
import base64

from neo.contract import *
from testcases.testing import Testing


class NotaryDepositN3(Testing):
    def __init__(self):
        super().__init__("NotaryDepositN3")
        self.neo3_only = True  # NEO4 has different GAS contract.
        self.default_sysfee = 2_0000000  # 0.2 GAS
        self.default_netfee = 2_0000000  # 0.2 GAS

    def _get_deposit_balance(self, account: str, expected: str):
        result = self.client.invoke_function(NOTARY_CONTRACT_HASH, "balanceOf",
                                             [ContractParameter(type="Hash160", value=account)])
        self.logger.info(f"balanceOf result: {result}")
        self.check_stack(result['stack'], expected=[('Integer', expected)])
        assert 'exception' not in result or result['exception'] is None, f"Expected no exception, got {result}"

    def _get_expiration_of(self, account: str):
        result = self.client.invoke_function(NOTARY_CONTRACT_HASH, "expirationOf",
                                             [ContractParameter(type="Hash160", value=account)])
        self.logger.info(f"expirationOf result: {result}")
        assert 'exception' not in result or result['exception'] is None, f"Expected no exception, got {result}"
        return int(result['stack'][0]['value'])

    def _check_gas_transfer_notification(self, notification: dict, source: UInt160, dest: UInt160, amount: int):
        assert 'contract' in notification and notification['contract'] == GAS_CONTRACT_HASH
        assert 'eventname' in notification and notification['eventname'] == 'Transfer'
        assert 'state' in notification and notification['state']['type'] == 'Array'

        state = notification['state']['value']
        assert len(state) == 3
        assert state[0]['type'] == 'ByteString'
        assert state[0]['value'] == base64.b64encode(source.to_array()).decode('utf-8')
        assert state[1]['type'] == 'ByteString'
        assert state[1]['value'] == base64.b64encode(dest.to_array()).decode('utf-8')
        assert state[2]['type'] == 'Integer'
        assert state[2]['value'] == str(amount)

    def _deposit(self, account: UInt160, amount: int, exception: str | None = None) -> int:
        # Step 1: build the deposit script
        dest160 = UInt160.from_string(NOTARY_CONTRACT_HASH)
        block_index = self.client.get_block_index()
        expiration = block_index + 5
        script = ScriptBuilder().emit_dynamic_call(
            script_hash=GAS_CONTRACT_HASH,
            method='transfer',
            call_flags=(CallFlags.STATES | CallFlags.ALLOW_CALL | CallFlags.ALLOW_NOTIFY),
            args=[account, dest160, amount, [None, expiration]],
        ).to_bytes()
        tx = self.make_tx(self.env.others[0], script, self.default_sysfee, self.default_netfee, expiration)

        # Step 2: send the transaction
        tx_id = self.client.send_raw_tx(tx.to_array())['hash']
        self.logger.info(f"Transaction sent: {tx_id}")

        # Step 3: wait for the next block
        block_index = self.client.get_block_index()
        self.wait_next_block(block_index)

        # Step 4: check the application log
        application_log = self.client.get_application_log(tx_id)
        self.logger.info(f"Application log: {application_log}")
        execution = application_log['executions'][0]
        if exception is not None:
            assert 'exception' in execution and exception in execution['exception']
        else:
            assert 'exception' not in execution or execution['exception'] is None
            self.check_execution_result(execution, stack=[('Boolean', True)])
            assert 'notifications' in execution and len(execution['notifications']) == 1
            self._check_gas_transfer_notification(execution['notifications'][0], account, dest160, amount)
        return expiration

    def _withdraw(self, account: UInt160, expected: bool):
        # Step 1: build the withdraw script
        block_index = self.client.get_block_index()
        script = ScriptBuilder().emit_dynamic_call(
            script_hash=NOTARY_CONTRACT_HASH,
            method='withdraw',
            call_flags=CallFlags.ALL,
            args=[account, None],
        ).to_bytes()
        tx = self.make_tx(self.env.others[0], script, self.default_sysfee, self.default_netfee, block_index+5)
        tx_id = self.client.send_raw_tx(tx.to_array())['hash']
        self.logger.info(f"Transaction sent: {tx_id}")

        # Step 2: wait for the next block
        block_index = self.client.get_block_index()
        self.wait_next_block(block_index)

        # Step 3: check the application log
        application_log = self.client.get_application_log(tx_id)
        self.logger.info(f"Application log: {application_log}")
        execution = application_log['executions'][0]
        assert 'exception' not in execution or execution['exception'] is None
        self.check_execution_result(execution, stack=[('Boolean', expected)])

    def run_test(self):
        account = self.env.others[0].script_hash
        balance = self.client.get_gas_balance(account)
        self.logger.info(f"Source {account} GAS balance: {balance}")

        # Step 1: withdraw the previous deposit
        self._withdraw(account, expected=False)

        # Step 2: check the deposit balance
        self._get_deposit_balance(str(account), "0")

        # Step 3: deposit 0.1 GAS, at least 0.2 GAS
        self._deposit(account, 10_000_000, exception='first deposit can not be less than 20000000')

        # Step 4: deposit 0.2 GAS
        expiration = self._deposit(account, 20_000_000)

        # Step 5: check the expiration
        assert self._get_expiration_of(str(account)) == expiration, \
            f"Expected expiration == {expiration}, got {self._get_expiration_of(str(account))}"

        # Step 6: check the deposit balance
        self._get_deposit_balance(str(account), "20000000")

        # Step 7: withdraw the deposit. Not allowed to withdraw before expiration.
        self._withdraw(account, expected=False)

        # Step 8: wait for the expiration
        self.wait_next_block(expiration)

        # Step 9: withdraw the deposit
        self._withdraw(account, expected=True)

        # Step 10: check the deposit balance
        self._get_deposit_balance(str(account), "0")


# Run with: python3 -B -m testcases.notary.deposit_n3
if __name__ == "__main__":
    test = NotaryDepositN3()
    test.run()
