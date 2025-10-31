#
# testcases/policy/exec_fee_factor.py file belongs to the neo project and is free
# software distributed under the MIT software license, see the
# accompanying file LICENSE in the main directory of the
# repository or http://www.opensource.org/licenses/mit-license.php
# for more details.
#
# Redistribution and use in source and binary forms with or without
# modifications are permitted.

from neo.contract import *
from testcases.testing import Testing


# Operation: this case tests the exec_fee_factor(get/set ExecFeeFactor) policy.
#  1. Only committee has permission to update the exec_fee_factor.
#  2. Rpc invoke_function cannot update the exec_fee_factor, because the result cannot persist.
#  3. The exec_fee_factor should in range [min_exec_fee_factor, max_exec_fee_factor].
# Expect Result: The exec_fee_factor policy is working as expected.
class ExecFeeFactor(Testing):
    def __init__(self, loggerName: str = "ExecFeeFactor"):
        super().__init__(loggerName)
        self.original_exec_fee_factor = 30
        self.updated_exec_fee_factor = 20
        self.min_exec_fee_factor = 1
        self.max_exec_fee_factor = 100

    def _make_update_exec_fee_factor_tx(self, exec_fee_factor: int):
        block_index = self.client.get_block_index()
        script = ScriptBuilder().emit_dynamic_call(
            script_hash=POLICY_CONTRACT_HASH,
            method='setExecFeeFactor',
            call_flags=CallFlags.STATES,
            args=[exec_fee_factor],
        ).to_bytes()
        return self.make_multisig_tx(script, self.default_sysfee, self.default_netfee,
                                     block_index+10, is_committee=True)

    def _get_original_exec_fee_factor(self):
        # Step 1: get the default exec fee factor
        result = self.client.invoke_function(POLICY_CONTRACT_HASH, "getExecFeeFactor", [])
        self.logger.info(f"Get original exec fee factor result: {result}")
        # self.check_stack(result['stack'], [('Integer', str(self.original_exec_fee_factor))])

        self.original_exec_fee_factor = int(result['stack'][0]['value'])
        self.updated_exec_fee_factor = self.original_exec_fee_factor + 10

    def _check_invoke_function_update_exec_fee_factor(self):
        # Step 2: set the exec fee factor to UPDATED_EXEC_FEE_FACTOR by rpc invoke_function.
        # But it cannot change the exec fee factor, because the result cannot persist.
        self.client.invoke_function(POLICY_CONTRACT_HASH, "setExecFeeFactor",
                                    [ContractParameter(type="Integer", value=self.updated_exec_fee_factor)])

        # Step 3: get the exec fee factor again, it should be the default exec fee factor.
        result = self.client.invoke_function(POLICY_CONTRACT_HASH, "getExecFeeFactor", [])
        self.check_stack(result['stack'], [('Integer', str(self.original_exec_fee_factor))])

    def _check_no_permission_update_exec_fee_factor(self):
        # Step 4: create a transaction to update the exec fee factor.
        block_index = self.client.get_block_index()
        script = ScriptBuilder().emit_dynamic_call(
            script_hash=POLICY_CONTRACT_HASH,
            method='setExecFeeFactor',
            call_flags=CallFlags.STATES,
            args=[self.updated_exec_fee_factor],
        ).to_bytes()

        # Step 5: send the transaction to the network
        tx = self.make_tx(self.env.others[0], script, self.default_sysfee, self.default_netfee, block_index+10)
        tx_hash = self.client.send_raw_tx(tx.to_array())
        tx_id = tx_hash['hash']
        self.logger.info(f"No permission update exec_fee_factor transaction sent: {tx_id}")

        # Step 6: wait for the next block
        block_index = self.client.get_block_index()
        self.wait_next_block(block_index)

        # Step 7: check the application log
        application_log = self.client.get_application_log(tx_id)
        self.logger.info(f"No permission update exec_fee_factor application log: {application_log}")
        assert 'txid' in application_log and tx_id == application_log['txid']
        assert 'executions' in application_log and len(application_log['executions']) == 1

        # Check the execution, others[0] don't have permission to update the exec fee factor.
        execution = application_log['executions'][0]
        self.check_execution_result(execution, exception='Invalid committee signature')

    def _check_committe_update_exec_fee_factor(self, exec_fee_factor: int):
        # Step 9: set the exec fee factor to UPDATED_EXEC_FEE_FACTOR by validators
        tx = self._make_update_exec_fee_factor_tx(exec_fee_factor)
        tx_hash = self.client.send_raw_tx(tx.to_array())
        tx_id = tx_hash['hash']
        self.logger.info(f"committee update exec_fee_factor transaction sent: {tx_id}")

        # Step 10: wait for the next block
        block_index = self.client.get_block_index()
        self.wait_next_block(block_index)

        # Step 11: check the application log
        application_log = self.client.get_application_log(tx_id)
        self.logger.info(f"Committee update exec_fee_factor application log: {application_log}")
        assert 'txid' in application_log and tx_id == application_log['txid']
        assert 'executions' in application_log and len(application_log['executions']) == 1

        # Check the execution, committee has permission to update the exec fee factor.
        execution = application_log['executions'][0]
        self.check_execution_result(execution, stack=[('Any', None)])

        # Step 12: get the exec fee factor again, it should be UPDATED_EXEC_FEE_FACTOR.
        result = self.client.invoke_function(POLICY_CONTRACT_HASH, "getExecFeeFactor", [])
        self.logger.info(f"Get updated exec fee factor result: {result}")
        self.check_stack(result['stack'], [('Integer', str(exec_fee_factor))])

    def _check_exec_fee_factor_range(self):
        # Step 13: check the exec fee factor range
        tx = self._make_update_exec_fee_factor_tx(self.min_exec_fee_factor - 1)
        tx_hash = self.client.send_raw_tx(tx.to_array())
        tx_id = tx_hash['hash']
        self.logger.info(f"update exec_fee_factor to {self.min_exec_fee_factor - 1} transaction sent: {tx_id}")

        # Step 14: wait for the next block
        block_index = self.client.get_block_index()
        self.wait_next_block(block_index)

        # Step 15: check the application log
        application_log = self.client.get_application_log(tx_id)
        self.logger.info(f"Update exec_fee_factor to {self.min_exec_fee_factor - 1} application log: {application_log}")
        assert 'txid' in application_log and tx_id == application_log['txid']
        assert 'executions' in application_log and len(application_log['executions']) == 1

        # Check the execution, the exec fee factor is {self.min_exec_fee_factor - 1}, so the transaction is fault.
        execution = application_log['executions'][0]
        self.check_execution_result(
            execution, exception=f'ExecFeeFactor must be between [{self.min_exec_fee_factor}, {self.max_exec_fee_factor}]')

        tx = self._make_update_exec_fee_factor_tx(self.max_exec_fee_factor + 1)
        tx_hash = self.client.send_raw_tx(tx.to_array())
        tx_id = tx_hash['hash']
        self.logger.info(f"update exec_fee_factor to {self.max_exec_fee_factor + 1} transaction sent: {tx_id}")

        # Step 16: wait for the next block
        block_index = self.client.get_block_index()
        self.wait_next_block(block_index)

        # Step 17: check the application log
        application_log = self.client.get_application_log(tx_id)
        self.logger.info(f"Update exec_fee_factor to {self.max_exec_fee_factor + 1} application log: {application_log}")
        assert 'txid' in application_log and tx_id == application_log['txid']
        assert 'executions' in application_log and len(application_log['executions']) == 1

        # Check the execution, the exec fee factor is {self.max_exec_fee_factor + 1}, so the transaction is fault.
        execution = application_log['executions'][0]
        self.check_execution_result(
            execution, exception=f'ExecFeeFactor must be between [{self.min_exec_fee_factor}, {self.max_exec_fee_factor}]')

    def run_test(self):
        self._get_original_exec_fee_factor()
        self._check_invoke_function_update_exec_fee_factor()
        self._check_no_permission_update_exec_fee_factor()
        self._check_exec_fee_factor_range()
        self._check_committe_update_exec_fee_factor(self.updated_exec_fee_factor)

    # Post test: set the exec fee factor to original exec fee factor.
    def post_test(self):
        self._check_committe_update_exec_fee_factor(self.original_exec_fee_factor)


# Run with: python3 -B -m testcases.policy.exec_fee_factor
if __name__ == "__main__":
    test = ExecFeeFactor()
    test.run()
