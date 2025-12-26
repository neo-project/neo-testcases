#
# testcases/policy/max_valid_until_block_increment.py file belongs to the neo project and is free
# software distributed under the MIT software license, see the
# accompanying file LICENSE in the main directory of the
# repository or http://www.opensource.org/licenses/mit-license.php
# for more details.
#
# Redistribution and use in source and binary forms with or without
# modifications are permitted.

from neo import Hardforks
from neo.contract import *
from testcases.testing import Testing


# Operation: this case tests the max_valid_until_block_increment(get/set MaxValidUntilBlockIncrement) policy.
#  1. Only committee has permission to update the max_valid_until_block_increment.
#  2. Rpc invoke_function cannot update the max_valid_until_block_increment, because the result cannot persist.
#  3. The max_valid_until_block_increment should in range [min_max_valid_until_block_increment, max_max_valid_until_block_increment].
# Expect Result: The max_valid_until_block_increment policy is working as expected.
class MaxValidUntilBlockIncrement(Testing):

    def __init__(self):
        super().__init__("MaxValidUntilBlockIncrement")
        self.original_max_valid_until_block_increment = 5760
        self.updated_max_valid_until_block_increment = 5000
        self.min_max_valid_until_block_increment = 1
        self.max_max_valid_until_block_increment = 86400
        self.neo3_only = True
        self.hardfork = Hardforks.HF_Echidna

    def _make_update_max_valid_until_block_increment_tx(self, max_valid_until_block_increment: int):
        block_index = self.client.get_block_index()
        script = ScriptBuilder().emit_dynamic_call(
            script_hash=POLICY_CONTRACT_HASH,
            method='setMaxValidUntilBlockIncrement',
            call_flags=CallFlags.STATES,
            args=[max_valid_until_block_increment],
        ).to_bytes()
        return self.make_multisig_tx(script, self.default_sysfee, self.default_netfee,
                                     block_index+10, is_committee=True)

    def _get_original_max_valid_until_block_increment(self):
        # Step 1: get the default max_valid_until_block_increment
        result = self.client.invoke_function(POLICY_CONTRACT_HASH, "getMaxValidUntilBlockIncrement", [])
        self.logger.info(f"Get original max_valid_until_block_increment result: {result}")
        # self.check_stack(result['stack'], [('Integer', str(self.original_max_valid_until_block_increment))])

        self.original_max_valid_until_block_increment = int(result['stack'][0]['value'])
        self.updated_max_valid_until_block_increment = self.original_max_valid_until_block_increment + 1000

    def _check_invoke_function_update_max_valid_until_block_increment(self):
        # Step 2: set the max_valid_until_block_increment to UPDATED_MAX_VALID_UNTIL_BLOCK_INCREMENT by rpc invoke_function.
        # But it cannot change the max_valid_until_block_increment, because the result cannot persist.
        self.client.invoke_function(POLICY_CONTRACT_HASH, "setMaxValidUntilBlockIncrement", [
                                    ContractParameter(type="Integer", value=self.updated_max_valid_until_block_increment)])

        # Step 3: get the max_valid_until_block_increment again, it should be the default max_valid_until_block_increment.
        result = self.client.invoke_function(POLICY_CONTRACT_HASH, "getMaxValidUntilBlockIncrement", [])
        self.check_stack(result['stack'], [('Integer', str(self.original_max_valid_until_block_increment))])

    def _check_no_permission_update_max_valid_until_block_increment(self):
        # Step 4: create a transaction to update the max_valid_until_block_increment.
        block_index = self.client.get_block_index()
        script = ScriptBuilder().emit_dynamic_call(
            script_hash=POLICY_CONTRACT_HASH,
            method='setMaxValidUntilBlockIncrement',
            call_flags=CallFlags.STATES,
            args=[self.updated_max_valid_until_block_increment],
        ).to_bytes()

        # Step 5: send the transaction to the network
        tx = self.make_tx(self.env.others[0], script, self.default_sysfee, self.default_netfee, block_index+10)
        tx_hash = self.client.send_raw_tx(tx.to_array())
        tx_id = tx_hash['hash']
        self.logger.info(f"No permission update max_valid_until_block_increment transaction sent: {tx_id}")

        # Step 6: wait for the next block
        block_index = self.client.get_block_index()
        self.wait_next_block(block_index)

        # Step 7: check the application log
        application_log = self.client.get_application_log(tx_id)
        self.logger.info(f"No permission update max_valid_until_block_increment application log: {application_log}")
        assert 'txid' in application_log and tx_id == application_log['txid']
        assert 'executions' in application_log and len(application_log['executions']) == 1

        # Check the execution, others[0] don't have permission to update the max_valid_until_block_increment.
        execution = application_log['executions'][0]
        self.check_execution_result(execution, exception='Invalid committee signature')

    def _check_committee_update_max_valid_until_block_increment(self, max_valid_until_block_increment: int):
        # Step 9: set the max_valid_until_block_increment to `max_valid_until_block_increment` by validators
        tx = self._make_update_max_valid_until_block_increment_tx(max_valid_until_block_increment)
        tx_hash = self.client.send_raw_tx(tx.to_array())
        tx_id = tx_hash['hash']
        self.logger.info(f"committee update max_valid_until_block_increment transaction sent: {tx_id}")

        # Step 10: wait for the next block
        block_index = self.client.get_block_index()
        self.wait_next_block(block_index)

        # Step 11: check the application log
        application_log = self.client.get_application_log(tx_id)
        self.logger.info(f"Committee update max_valid_until_block_increment application log: {application_log}")
        assert 'txid' in application_log and tx_id == application_log['txid']
        assert 'executions' in application_log and len(application_log['executions']) == 1

        # Check the execution, committee has permission to update the max_valid_until_block_increment.
        execution = application_log['executions'][0]
        self.check_execution_result(execution, stack=[('Any', None)])

        # Step 12: get the max_valid_until_block_increment again, it should be `max_valid_until_block_increment`.
        result = self.client.invoke_function(POLICY_CONTRACT_HASH, "getMaxValidUntilBlockIncrement", [])
        self.logger.info(f"Get updated max_valid_until_block_increment result: {result}")
        self.check_stack(result['stack'], [('Integer', str(max_valid_until_block_increment))])

    def _check_max_valid_until_block_increment_range(self):
        # Step 13: check the max_valid_until_block_increment range
        tx = self._make_update_max_valid_until_block_increment_tx(self.min_max_valid_until_block_increment - 1)
        tx_hash = self.client.send_raw_tx(tx.to_array())
        tx_id = tx_hash['hash']
        self.logger.info(
            f"update max_valid_until_block_increment to {self.min_max_valid_until_block_increment - 1} transaction sent: {tx_id}")

        # Step 14: wait for the next block
        block_index = self.client.get_block_index()
        self.wait_next_block(block_index)

        # Step 15: check the application log
        application_log = self.client.get_application_log(tx_id)
        self.logger.info(
            f"Update max_valid_until_block_increment to {self.min_max_valid_until_block_increment - 1} application log: {application_log}")
        assert 'txid' in application_log and tx_id == application_log['txid']
        assert 'executions' in application_log and len(application_log['executions']) == 1

        # Check the execution, the max_valid_until_block_increment is {self.min_max_valid_until_block_increment - 1}, so the transaction is fault.
        execution = application_log['executions'][0]
        self.check_execution_result(
            execution, exception=f'MaxValidUntilBlockIncrement must be between [{self.min_max_valid_until_block_increment}, {self.max_max_valid_until_block_increment}]')

        tx = self._make_update_max_valid_until_block_increment_tx(self.max_max_valid_until_block_increment + 1)
        tx_hash = self.client.send_raw_tx(tx.to_array())
        tx_id = tx_hash['hash']
        self.logger.info(
            f"update max_valid_until_block_increment to {self.max_max_valid_until_block_increment + 1} transaction sent: {tx_id}")

        # Step 16: wait for the next block
        block_index = self.client.get_block_index()
        self.wait_next_block(block_index)

        # Step 17: check the application log
        application_log = self.client.get_application_log(tx_id)
        self.logger.info(
            f"Update max_valid_until_block_increment to {self.max_max_valid_until_block_increment + 1} application log: {application_log}")
        assert 'txid' in application_log and tx_id == application_log['txid']
        assert 'executions' in application_log and len(application_log['executions']) == 1

        # Check the execution, the max_valid_until_block_increment is {self.max_max_valid_until_block_increment + 1}, so the transaction is fault.
        execution = application_log['executions'][0]
        self.check_execution_result(
            execution, exception=f'MaxValidUntilBlockIncrement must be between [{self.min_max_valid_until_block_increment}, {self.max_max_valid_until_block_increment}]')

    def run_test(self):
        self._get_original_max_valid_until_block_increment()
        self._check_invoke_function_update_max_valid_until_block_increment()
        self._check_no_permission_update_max_valid_until_block_increment()
        self._check_max_valid_until_block_increment_range()
        self._check_committee_update_max_valid_until_block_increment(self.updated_max_valid_until_block_increment)

    # Post test: set the max_valid_until_block_increment to original max_valid_until_block_increment.
    def post_test(self):
        self._check_committee_update_max_valid_until_block_increment(self.original_max_valid_until_block_increment)


# Run with: python3 -B -m testcases.policy.max_valid_until_block_increment
if __name__ == "__main__":
    test = MaxValidUntilBlockIncrement()
    test.run()
