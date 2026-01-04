
from neo.contract import *
from testcases.testing import Testing


# Operation: this case tests the fee_per_byte(get/set FeePerByte) policy.
#  1. Only committee has permission to update the fee_per_byte.
#  2. Rpc invoke_function cannot update the fee_per_byte, because the result cannot persist.
#  3. The fee_per_byte should in range [min_fee_per_byte, max_fee_per_byte].
# Expect Result: The fee_per_byte policy is working as expected.
class FeePerByte(Testing):

    def __init__(self):
        super().__init__("FeePerByte")
        self.original_fee_per_byte = 1000
        self.updated_fee_per_byte = 500
        self.min_fee_per_byte = 0
        self.max_fee_per_byte = 1_00_000_000

    def _make_update_fee_per_byte_tx(self, fee_per_byte: int):
        block_index = self.client.get_block_index()
        script = ScriptBuilder().emit_dynamic_call(
            script_hash=POLICY_CONTRACT_HASH,
            method='setFeePerByte',
            call_flags=CallFlags.STATES,
            args=[fee_per_byte],
        ).to_bytes()
        return self.make_multisig_tx(script, self.default_sysfee, self.default_netfee,
                                     block_index+10, is_committee=True)

    def _get_original_fee_per_byte(self):
        # Step 1: get the default fee_per_byte
        result = self.client.invoke_function(POLICY_CONTRACT_HASH, "getFeePerByte", [])
        self.logger.info(f"Get original fee_per_byte  result: {result}")
        # self.check_stack(result['stack'], [('Integer', str(self.original_fee_per_byte))])

        self.original_fee_per_byte = int(result['stack'][0]['value'])
        self.updated_fee_per_byte = self.original_fee_per_byte + 500

    def _check_invoke_function_update_fee_per_byte(self):
        # Step 2: set the fee_per_byte to FEE_PER_BYTE_V2 by rpc invoke_function.
        # But it cannot change the fee_per_byte, because the result cannot persist.
        self.client.invoke_function(POLICY_CONTRACT_HASH, "setFeePerByte",
                                    [ContractParameter(type="Integer", value=self.updated_fee_per_byte)])

        # Step 3: get the fee_per_byte again, it should be the default fee_per_byte.
        result = self.client.invoke_function(POLICY_CONTRACT_HASH, "getFeePerByte", [])
        self.check_stack(result['stack'], [('Integer', str(self.original_fee_per_byte))])

    def _check_no_permission_update_fee_per_byte(self):
        # Step 4: create a transaction to update the fee_per_byte.
        block_index = self.client.get_block_index()
        script = ScriptBuilder().emit_dynamic_call(
            script_hash=POLICY_CONTRACT_HASH,
            method='setFeePerByte',
            call_flags=CallFlags.STATES,
            args=[self.updated_fee_per_byte],
        ).to_bytes()

        # Step 5: send the transaction to the network
        tx = self.make_tx(self.env.others[0], script, self.default_sysfee, self.default_netfee, block_index+10)
        tx_hash = self.client.send_raw_tx(tx.to_array())
        tx_id = tx_hash['hash']
        self.logger.info(f"No permission update fee_per_byte transaction sent: {tx_id}")

        # Step 6: wait for the next block
        block_index = self.client.get_block_index()
        self.wait_next_block(block_index)

        # Step 7: check the application log
        application_log = self.client.get_application_log(tx_id)
        self.logger.info(f"No permission update fee_per_byte application log: {application_log}")
        assert 'txid' in application_log and tx_id == application_log['txid']
        assert 'executions' in application_log and len(application_log['executions']) == 1

        # Check the execution, others[0] don't have permission to update the fee_per_byte .
        execution = application_log['executions'][0]
        self.check_execution_result(execution, exception='Invalid committee signature')

    def _check_committe_update_fee_per_byte(self, fee_per_byte: int):
        # Step 9: set the fee_per_byte to FEE_PER_BYTE_V2 by validators
        tx = self._make_update_fee_per_byte_tx(fee_per_byte)
        tx_hash = self.client.send_raw_tx(tx.to_array())
        tx_id = tx_hash['hash']
        self.logger.info(f"committee update fee_per_byte transaction sent: {tx_id}")

        # Step 10: wait for the next block
        block_index = self.client.get_block_index()
        self.wait_next_block(block_index)

        # Step 11: check the application log
        application_log = self.client.get_application_log(tx_id)
        self.logger.info(f"Committee update fee_per_byte application log: {application_log}")
        assert 'txid' in application_log and tx_id == application_log['txid']
        assert 'executions' in application_log and len(application_log['executions']) == 1

        # Check the execution, committee has permission to update the fee_per_byte.
        execution = application_log['executions'][0]
        self.check_execution_result(execution, stack=[('Any', None)])

        # Step 12: get the fee_per_byte again, it should be FEE_PER_BYTE_V2.
        result = self.client.invoke_function(POLICY_CONTRACT_HASH, "getFeePerByte", [])
        self.logger.info(f"Get updated fee_per_byte result: {result}")
        self.check_stack(result['stack'], [('Integer', str(fee_per_byte))])

    def _check_fee_per_byte_range(self):
        # Step 13: check the fee_per_byte  range
        tx = self._make_update_fee_per_byte_tx(self.min_fee_per_byte - 1)
        tx_hash = self.client.send_raw_tx(tx.to_array())
        tx_id = tx_hash['hash']
        self.logger.info(f"update fee_per_byte to {self.min_fee_per_byte - 1} transaction sent: {tx_id}")

        # Step 14: wait for the next block
        block_index = self.client.get_block_index()
        self.wait_next_block(block_index)

        # Step 15: check the application log
        application_log = self.client.get_application_log(tx_id)
        self.logger.info(f"Update fee_per_byte to {self.min_fee_per_byte - 1} application log: {application_log}")
        assert 'txid' in application_log and tx_id == application_log['txid']
        assert 'executions' in application_log and len(application_log['executions']) == 1

        # Check the execution, the fee_per_byte is {self.min_fee_per_byte - 1}, so the transaction is fault.
        execution = application_log['executions'][0]
        self.check_execution_result(
            execution, exception=f'FeePerByte must be between [{self.min_fee_per_byte}, {self.max_fee_per_byte}]')

        tx = self._make_update_fee_per_byte_tx(self.max_fee_per_byte + 1)
        tx_hash = self.client.send_raw_tx(tx.to_array())
        tx_id = tx_hash['hash']
        self.logger.info(f"update fee_per_byte to {self.max_fee_per_byte + 1} transaction sent: {tx_id}")

        # Step 16: wait for the next block
        block_index = self.client.get_block_index()
        self.wait_next_block(block_index)

        # Step 17: check the application log
        application_log = self.client.get_application_log(tx_id)
        self.logger.info(f"Update fee_per_byte to {self.max_fee_per_byte + 1} application log: {application_log}")
        assert 'txid' in application_log and tx_id == application_log['txid']
        assert 'executions' in application_log and len(application_log['executions']) == 1

        # Check the execution, the fee_per_byte is {self.max_fee_per_byte + 1}, so the transaction is fault.
        execution = application_log['executions'][0]
        self.check_execution_result(
            execution, exception=f'FeePerByte must be between [{self.min_fee_per_byte}, {self.max_fee_per_byte}]')

    def run_test(self):
        self._get_original_fee_per_byte()
        self._check_invoke_function_update_fee_per_byte()
        self._check_no_permission_update_fee_per_byte()
        self._check_fee_per_byte_range()
        self._check_committe_update_fee_per_byte(self.updated_fee_per_byte)

    # Post test: set the fee_per_byte to original fee_per_byte.
    def post_test(self):
        self._check_committe_update_fee_per_byte(self.original_fee_per_byte)


# Run with: python3 -B -m testcases.policy.fee_per_byte
if __name__ == "__main__":
    test = FeePerByte()
    test.run()
