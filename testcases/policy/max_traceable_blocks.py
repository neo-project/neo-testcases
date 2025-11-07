#
# testcases/policy/max_traceable_blocks.py file belongs to the neo project and is free
# software distributed under the MIT software license, see the
# accompanying file LICENSE in the main directory of the
# repository or http://www.opensource.org/licenses/mit-license.php
# for more details.
#
# Redistribution and use in source and binary forms with or without
# modifications are permitted.

from neo.contract import *
from testcases.testing import Testing


# Operation: this case tests the max_traceable_blocks(get/set MaxTraceableBlocks) policy.
#  1. Only committee has permission to update the max_traceable_blocks.
#  2. Rpc invoke_function cannot update the max_traceable_blocks, because the result cannot persist.
#  3. The max_traceable_blocks should be in range [min_max_traceable_blocks, max_max_traceable_blocks].
#  4. The new max_traceable_blocks should be less or equal to the original max_traceable_blocks.
#  5. The max_traceable_blocks should be greater than MaxValidUntilBlockIncrement(from getMaxValidUntilBlockIncrement).
# Expect Result: The max_traceable_blocks policy is working as expected.
class MaxTraceableBlocks(Testing):

    def __init__(self):
        super().__init__("MaxTraceableBlocks")
        self.original_max_traceable_blocks = 2102400
        self.updated_max_traceable_blocks = 2102400 - 1
        self.min_max_traceable_blocks = 1
        self.max_max_traceable_blocks = 2102400

    def _make_update_max_traceable_blocks_tx(self, max_traceable_blocks: int):
        block_index = self.client.get_block_index()
        script = ScriptBuilder().emit_dynamic_call(
            script_hash=POLICY_CONTRACT_HASH,
            method='setMaxTraceableBlocks',
            call_flags=CallFlags.STATES,
            args=[max_traceable_blocks],
        ).to_bytes()
        return self.make_multisig_tx(script, self.default_sysfee, self.default_netfee,
                                     block_index+10, is_committee=True)

    def _get_original_max_traceable_blocks(self):
        # Step 1: get the default max_traceable_blocks
        result = self.client.invoke_function(POLICY_CONTRACT_HASH, "getMaxTraceableBlocks", [])
        self.logger.info(f"Get original max_traceable_blocks result: {result}")
        # self.check_stack(result['stack'], [('Integer', str(self.original_max_traceable_blocks))])

        self.original_max_traceable_blocks = int(result['stack'][0]['value'])
        self.updated_max_traceable_blocks = self.original_max_traceable_blocks - 1

    def _check_invoke_function_update_max_traceable_blocks(self):
        # Step 2: set the max_traceable_blocks to UPDATED_MAX_TRACEABLE_BLOCKS by rpc invoke_function.
        # But it cannot change the max_traceable_blocks, because the result cannot persist.
        self.client.invoke_function(POLICY_CONTRACT_HASH, "setMaxTraceableBlocks",
                                    [ContractParameter(type="Integer", value=self.updated_max_traceable_blocks)])

        # Step 3: get the max_traceable_blocks again, it should be the default max_traceable_blocks.
        result = self.client.invoke_function(POLICY_CONTRACT_HASH, "getMaxTraceableBlocks", [])
        self.check_stack(result['stack'], [('Integer', str(self.original_max_traceable_blocks))])

    def _check_no_permission_update_max_traceable_blocks(self):
        # Step 4: create a transaction to update the max_traceable_blocks.
        block_index = self.client.get_block_index()
        script = ScriptBuilder().emit_dynamic_call(
            script_hash=POLICY_CONTRACT_HASH,
            method='setMaxTraceableBlocks',
            call_flags=CallFlags.STATES,
            args=[self.updated_max_traceable_blocks],
        ).to_bytes()

        # Step 5: send the transaction to the network
        tx = self.make_tx(self.env.others[0], script, self.default_sysfee, self.default_netfee, block_index+10)
        tx_hash = self.client.send_raw_tx(tx.to_array())
        tx_id = tx_hash['hash']
        self.logger.info(f"No permission update max_traceable_blocks transaction sent: {tx_id}")

        # Step 6: wait for the next block
        block_index = self.client.get_block_index()
        self.wait_next_block(block_index)

        # Step 7: check the application log
        application_log = self.client.get_application_log(tx_id)
        self.logger.info(f"No permission update max_traceable_blocks application log: {application_log}")
        assert 'txid' in application_log and tx_id == application_log['txid']
        assert 'executions' in application_log and len(application_log['executions']) == 1

        # Check the execution, others[0] don't have permission to update the max_traceable_blocks.
        execution = application_log['executions'][0]
        self.check_execution_result(execution, exception='Invalid committee signature')

    def _check_max_traceable_blocks_range(self):
        # Step 8: check the max_traceable_blocks range
        tx = self._make_update_max_traceable_blocks_tx(self.min_max_traceable_blocks - 1)
        tx_hash = self.client.send_raw_tx(tx.to_array())
        tx_id = tx_hash['hash']
        self.logger.info(
            f"update max_traceable_blocks to {self.min_max_traceable_blocks - 1} transaction sent: {tx_id}")

        # Step 9: wait for the next block
        block_index = self.client.get_block_index()
        self.wait_next_block(block_index)

        # Step 10: check the application log
        application_log = self.client.get_application_log(tx_id)
        self.logger.info(
            f"Update max_traceable_blocks to {self.min_max_traceable_blocks - 1} application log: {application_log}")
        assert 'txid' in application_log and tx_id == application_log['txid']
        assert 'executions' in application_log and len(application_log['executions']) == 1

        # Check the execution, the max_traceable_blocks is {self.min_max_traceable_blocks - 1}, so the transaction is fault.
        execution = application_log['executions'][0]
        self.check_execution_result(
            execution, exception=f'MaxTraceableBlocks must be between [{self.min_max_traceable_blocks}, {self.max_max_traceable_blocks}]')

        tx = self._make_update_max_traceable_blocks_tx(self.max_max_traceable_blocks + 1)
        tx_hash = self.client.send_raw_tx(tx.to_array())
        tx_id = tx_hash['hash']
        self.logger.info(
            f"update max_traceable_blocks to {self.max_max_traceable_blocks + 1} transaction sent: {tx_id}")

        # Step 11: wait for the next block
        block_index = self.client.get_block_index()
        self.wait_next_block(block_index)

        # Step 12: check the application log
        application_log = self.client.get_application_log(tx_id)
        self.logger.info(
            f"Update max_traceable_blocks to {self.max_max_traceable_blocks + 1} application log: {application_log}")
        assert 'txid' in application_log and tx_id == application_log['txid']
        assert 'executions' in application_log and len(application_log['executions']) == 1

        # Check the execution, the max_traceable_blocks is {self.max_max_traceable_blocks + 1}, so the transaction is fault.
        execution = application_log['executions'][0]
        self.check_execution_result(
            execution, exception=f'MaxTraceableBlocks must be between [{self.min_max_traceable_blocks}, {self.max_max_traceable_blocks}]')

    def _check_max_traceable_blocks_decrease_validation(self):
        # Step 13: check that max_traceable_blocks can only be decreased (condition 4)
        # Try to increase max_traceable_blocks - this should fail
        increased_value = self.updated_max_traceable_blocks + 1
        tx = self._make_update_max_traceable_blocks_tx(increased_value)
        tx_hash = self.client.send_raw_tx(tx.to_array())
        tx_id = tx_hash['hash']
        self.logger.info(f"update max_traceable_blocks to {increased_value} (increase) transaction sent: {tx_id}")

        # Step 14: wait for the next block
        block_index = self.client.get_block_index()
        self.wait_next_block(block_index)

        # Step 15: check the application log
        application_log = self.client.get_application_log(tx_id)
        self.logger.info(
            f"Update max_traceable_blocks to {increased_value} (increase) application log: {application_log}")
        assert 'txid' in application_log and tx_id == application_log['txid']
        assert 'executions' in application_log and len(application_log['executions']) == 1

        # Check the execution, increasing max_traceable_blocks should fail
        execution = application_log['executions'][0]
        self.check_execution_result(execution, exception='MaxTraceableBlocks can not be increased')

    def _check_max_traceable_blocks_greater_than_max_valid_until_block_increment(self):
        # Step 16: check that max_traceable_blocks must be greater than MaxValidUntilBlockIncrement (condition 5)
        # First get the current MaxValidUntilBlockIncrement
        result = self.client.invoke_function(POLICY_CONTRACT_HASH, "getMaxValidUntilBlockIncrement", [])
        max_valid_until_block_increment = int(result['stack'][0]['value'])
        self.logger.info(f"Current MaxValidUntilBlockIncrement: {max_valid_until_block_increment}")

        # Try to set max_traceable_blocks to a value less than MaxValidUntilBlockIncrement
        invalid_value = max_valid_until_block_increment - 1
        tx = self._make_update_max_traceable_blocks_tx(invalid_value)
        tx_hash = self.client.send_raw_tx(tx.to_array())
        tx_id = tx_hash['hash']
        self.logger.info(
            f"update max_traceable_blocks to {invalid_value} (less than MaxValidUntilBlockIncrement) transaction sent: {tx_id}")

        # Step 17: wait for the next block
        block_index = self.client.get_block_index()
        self.wait_next_block(block_index)

        # Step 18: check the application log
        application_log = self.client.get_application_log(tx_id)
        self.logger.info(
            f"Update max_traceable_blocks to {invalid_value} (less than MaxValidUntilBlockIncrement) application log: {application_log}")
        assert 'txid' in application_log and tx_id == application_log['txid']
        assert 'executions' in application_log and len(application_log['executions']) == 1

        # Check the execution, max_traceable_blocks must be greater than MaxValidUntilBlockIncrement
        execution = application_log['executions'][0]
        self.check_execution_result(
            execution, exception='MaxTraceableBlocks must be larger than MaxValidUntilBlockIncrement')

    def _check_committee_update_max_traceable_blocks(self, max_traceable_blocks: int):
        # Step 19: set the max_traceable_blocks to UPDATED_MAX_TRACEABLE_BLOCKS by validators
        tx = self._make_update_max_traceable_blocks_tx(max_traceable_blocks)
        tx_hash = self.client.send_raw_tx(tx.to_array())
        tx_id = tx_hash['hash']
        self.logger.info(f"committee update max_traceable_blocks transaction sent: {tx_id}")

        # Step 20: wait for the next block
        block_index = self.client.get_block_index()
        self.wait_next_block(block_index)

        # Step 21: check the application log
        application_log = self.client.get_application_log(tx_id)
        self.logger.info(f"Committee update max_traceable_blocks application log: {application_log}")
        assert 'txid' in application_log and tx_id == application_log['txid']
        assert 'executions' in application_log and len(application_log['executions']) == 1

        # Check the execution, committee has permission to update the max_traceable_blocks.
        execution = application_log['executions'][0]
        self.check_execution_result(execution, stack=[('Any', None)])

        # Step 22: get the max_traceable_blocks again, it should be UPDATED_MAX_TRACEABLE_BLOCKS.
        result = self.client.invoke_function(POLICY_CONTRACT_HASH, "getMaxTraceableBlocks", [])
        self.logger.info(f"Get updated max_traceable_blocks result: {result}")
        self.check_stack(result['stack'], [('Integer', str(max_traceable_blocks))])

    def run_test(self):
        self._get_original_max_traceable_blocks()
        self._check_invoke_function_update_max_traceable_blocks()
        self._check_no_permission_update_max_traceable_blocks()
        self._check_max_traceable_blocks_range()
        self._check_committee_update_max_traceable_blocks(self.updated_max_traceable_blocks)
        self._check_max_traceable_blocks_decrease_validation()
        self._check_max_traceable_blocks_greater_than_max_valid_until_block_increment()

    def post_test(self):
        pass  # Cannot set to original value, because the max_traceable_blocks is not allowed to be decreased.


# Run with: python3 -B -m testcases.policy.max_traceable_blocks
if __name__ == "__main__":
    test = MaxTraceableBlocks()
    test.run()
