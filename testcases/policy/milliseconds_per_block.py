#
# testcases/policy/milliseconds_per_block.py file belongs to the neo project and is free
# software distributed under the MIT software license, see the
# accompanying file LICENSE in the main directory of the
# repository or http://www.opensource.org/licenses/mit-license.php
# for more details.
#
# Redistribution and use in source and binary forms with or without
# modifications are permitted.

from neo.contract import *
from testcases.testing import Testing


# Operation: this case tests the milliseconds_per_block(get/set MillisecondsPerBlock) policy.
#  1. Only committee has permission to update the milliseconds_per_block.
#  2. Rpc invoke_function cannot update the milliseconds_per_block, because the result cannot persist.
#  3. The milliseconds_per_block should in range [min_millis_per_block, max_millis_per_block].
#  4. The setMillisecondsPerBlock must called with CallFlags.STATES | CallFlags.ALLOW_NOTIFY.
# Expect Result: The milliseconds_per_block policy is working as expected.
class MillisecondsPerBlock(Testing):

    def __init__(self):
        super().__init__("MillisecondsPerBlock")
        self.original_millis_per_block = 15_000
        self.updated_millis_per_block = 10_000
        self.min_millis_per_block = 1
        self.max_millis_per_block = 30_000

    def _make_update_millis_per_block_tx(self, millis_per_block: int):
        block_index = self.client.get_block_index()
        script = ScriptBuilder().emit_dynamic_call(
            script_hash=POLICY_CONTRACT_HASH,
            method='setMillisecondsPerBlock',
            call_flags=CallFlags.STATES | CallFlags.ALLOW_NOTIFY,
            args=[millis_per_block],
        ).to_bytes()
        return self.make_multisig_tx(script, self.default_sysfee, self.default_netfee,
                                     block_index+10, is_committee=True)

    def _get_original_millis_per_block(self):
        # Step 1: get the default millis_per_block
        result = self.client.invoke_function(POLICY_CONTRACT_HASH, "getMillisecondsPerBlock", [])
        self.logger.info(f"Get original millis_per_block result: {result}")
        # self.check_stack(result['stack'], [('Integer', str(self.original_millis_per_block))])

        self.original_millis_per_block = int(result['stack'][0]['value'])
        self.updated_millis_per_block = self.original_millis_per_block + 5000

    def _check_invoke_function_update_millis_per_block(self):
        # Step 2: set the millis_per_block to updated_millis_per_block by rpc invoke_function.
        # But it cannot change the millis_per_block, because the result cannot persist.
        self.client.invoke_function(POLICY_CONTRACT_HASH, "setMillisecondsPerBlock",
                                    [ContractParameter(type="Integer", value=self.updated_millis_per_block)])

        # Step 3: get the millis_per_block again, it should be the default millis_per_block.
        result = self.client.invoke_function(POLICY_CONTRACT_HASH, "getMillisecondsPerBlock", [])
        self.check_stack(result['stack'], [('Integer', str(self.original_millis_per_block))])

    def _check_no_permission_update_millis_per_block(self):
        # Step 4: create a transaction to update the millis_per_block.
        block_index = self.client.get_block_index()
        script = ScriptBuilder().emit_dynamic_call(
            script_hash=POLICY_CONTRACT_HASH,
            method='setMillisecondsPerBlock',
            call_flags=CallFlags.STATES | CallFlags.ALLOW_NOTIFY,
            args=[self.updated_millis_per_block],
        ).to_bytes()

        # Step 5: send the transaction to the network
        tx = self.make_tx(self.env.others[0], script, self.default_sysfee, self.default_netfee, block_index+10)
        tx_hash = self.client.send_raw_tx(tx.to_array())
        tx_id = tx_hash['hash']
        self.logger.info(f"No permission update millis_per_block transaction sent: {tx_id}")

        # Step 6: wait for the next block
        block_index = self.client.get_block_index()
        self.wait_next_block(block_index)

        # Step 7: check the application log
        application_log = self.client.get_application_log(tx_id)
        self.logger.info(f"No permission update millis_per_block application log: {application_log}")
        assert 'txid' in application_log and tx_id == application_log['txid']
        assert 'executions' in application_log and len(application_log['executions']) == 1

        # Check the execution, others[0] don't have permission to update the millis_per_block.
        execution = application_log['executions'][0]
        self.check_execution_result(execution, exception='Invalid committee signature')

    def _check_committee_update_millis_per_block(self, millis_per_block: int):
        # Step 9: set the millis_per_block to `millis_per_block` by validators
        tx = self._make_update_millis_per_block_tx(millis_per_block)
        tx_hash = self.client.send_raw_tx(tx.to_array())
        tx_id = tx_hash['hash']
        self.logger.info(f"committee update millis_per_block transaction sent: {tx_id}")

        # Step 10: wait for the next block
        block_index = self.client.get_block_index()
        self.wait_next_block(block_index)

        # Step 11: check the application log
        application_log = self.client.get_application_log(tx_id)
        self.logger.info(f"Committee update millis_per_block application log: {application_log}")
        assert 'txid' in application_log and tx_id == application_log['txid']
        assert 'executions' in application_log and len(application_log['executions']) == 1

        # Check the execution, committee has permission to update the millis_per_block.
        execution = application_log['executions'][0]
        self.check_execution_result(execution, stack=[('Any', None)])

        # Step 12: get the millis_per_block again, it should be `millis_per_block`.
        result = self.client.invoke_function(POLICY_CONTRACT_HASH, "getMillisecondsPerBlock", [])
        self.logger.info(f"Get updated millis_per_block result: {result}")
        self.check_stack(result['stack'], [('Integer', str(millis_per_block))])

    def _check_millis_per_block_range(self):
        # Step 13: check the millis_per_block range
        tx = self._make_update_millis_per_block_tx(self.min_millis_per_block - 1)
        tx_hash = self.client.send_raw_tx(tx.to_array())
        tx_id = tx_hash['hash']
        self.logger.info(
            f"update millis_per_block to {self.min_millis_per_block - 1} transaction sent: {tx_id}")

        # Step 14: wait for the next block
        block_index = self.client.get_block_index()
        self.wait_next_block(block_index)

        # Step 15: check the application log
        application_log = self.client.get_application_log(tx_id)
        self.logger.info(
            f"Update millis_per_block to {self.min_millis_per_block - 1} application log: {application_log}")
        assert 'txid' in application_log and tx_id == application_log['txid']
        assert 'executions' in application_log and len(application_log['executions']) == 1

        # Check the execution, the millis_per_block is {self.min_millis_per_block - 1}, so the transaction is fault.
        execution = application_log['executions'][0]
        self.check_execution_result(
            execution, exception=f'MillisecondsPerBlock must be between [{self.min_millis_per_block}, {self.max_millis_per_block}]')

        tx = self._make_update_millis_per_block_tx(self.max_millis_per_block + 1)
        tx_hash = self.client.send_raw_tx(tx.to_array())
        tx_id = tx_hash['hash']
        self.logger.info(
            f"update millis_per_block to {self.max_millis_per_block + 1} transaction sent: {tx_id}")

        # Step 16: wait for the next block
        block_index = self.client.get_block_index()
        self.wait_next_block(block_index)

        # Step 17: check the application log
        application_log = self.client.get_application_log(tx_id)
        self.logger.info(
            f"Update millis_per_block to {self.max_millis_per_block + 1} application log: {application_log}")
        assert 'txid' in application_log and tx_id == application_log['txid']
        assert 'executions' in application_log and len(application_log['executions']) == 1

        # Check the execution, the millis_per_block is {self.max_millis_per_block + 1}, so the transaction is fault.
        execution = application_log['executions'][0]
        self.check_execution_result(
            execution, exception=f'MillisecondsPerBlock must be between [{self.min_millis_per_block}, {self.max_millis_per_block}]')

    def run_test(self):
        if self.env.neo4_enable:
            return  # Removed in neo4
        self._get_original_millis_per_block()
        self._check_invoke_function_update_millis_per_block()
        self._check_no_permission_update_millis_per_block()
        self._check_millis_per_block_range()
        self._check_committee_update_millis_per_block(self.updated_millis_per_block)

    # Post test: set the millis_per_block to original millis_per_block.
    def post_test(self):
        self._check_committee_update_millis_per_block(self.original_millis_per_block)


# Run with: python3 -B -m testcases.policy.milliseconds_per_block
if __name__ == "__main__":
    test = MillisecondsPerBlock()
    test.run()
