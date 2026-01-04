
from neo.contract import *
from testcases.testing import Testing


# Operation: this case tests the storage_price(get/set StoragePrice) policy.
#  1. Only committee has permission to update the storage_price.
#  2. Rpc invoke_function cannot update the storage_price, because the result cannot persist.
#  3. The storage_price should in range [min_storage_price, max_storage_price].
# Expect Result: The storage_price policy is working as expected.
class StoragePrice(Testing):

    def __init__(self):
        super().__init__("StoragePrice")
        self.original_storage_price = 100_000
        self.updated_storage_price = 50_000
        self.min_storage_price = 1
        self.max_storage_price = 10_000_000

    def _make_update_storage_price_tx(self, storage_price: int):
        block_index = self.client.get_block_index()
        script = ScriptBuilder().emit_dynamic_call(
            script_hash=POLICY_CONTRACT_HASH,
            method='setStoragePrice',
            call_flags=CallFlags.STATES,
            args=[storage_price],
        ).to_bytes()
        return self.make_multisig_tx(script, self.default_sysfee, self.default_netfee,
                                     block_index+10, is_committee=True)

    def _get_original_storage_price(self):
        # Step 1: get the default storage_price
        result = self.client.invoke_function(POLICY_CONTRACT_HASH, "getStoragePrice", [])
        self.logger.info(f"Get original storage_price result: {result}")
        # self.check_stack(result['stack'], [('Integer', str(self.original_storage_price))])

        self.original_storage_price = int(result['stack'][0]['value'])
        self.updated_storage_price = self.original_storage_price + 10000

    def _check_invoke_function_update_storage_price(self):
        # Step 2: set the storage_price to UPDATED_STORAGE_PRICE by rpc invoke_function.
        # But it cannot change the storage_price, because the result cannot persist.
        self.client.invoke_function(POLICY_CONTRACT_HASH, "setStoragePrice",
                                    [ContractParameter(type="Integer", value=self.updated_storage_price)])

        # Step 3: get the storage_price again, it should be the default storage_price.
        result = self.client.invoke_function(POLICY_CONTRACT_HASH, "getStoragePrice", [])
        self.check_stack(result['stack'], [('Integer', str(self.original_storage_price))])

    def _check_no_permission_update_storage_price(self):
        # Step 4: create a transaction to update the storage_price.
        block_index = self.client.get_block_index()
        script = ScriptBuilder().emit_dynamic_call(
            script_hash=POLICY_CONTRACT_HASH,
            method='setStoragePrice',
            call_flags=CallFlags.STATES,
            args=[self.updated_storage_price],
        ).to_bytes()

        # Step 5: send the transaction to the network
        tx = self.make_tx(self.env.others[0], script, self.default_sysfee, self.default_netfee, block_index+10)
        tx_hash = self.client.send_raw_tx(tx.to_array())
        tx_id = tx_hash['hash']
        self.logger.info(f"No permission update storage_price transaction sent: {tx_id}")

        # Step 6: wait for the next block
        block_index = self.client.get_block_index()
        self.wait_next_block(block_index)

        # Step 7: check the application log
        application_log = self.client.get_application_log(tx_id)
        self.logger.info(f"No permission update storage_price application log: {application_log}")
        assert 'txid' in application_log and tx_id == application_log['txid']
        assert 'executions' in application_log and len(application_log['executions']) == 1

        # Check the execution, others[0] don't have permission to update the storage_price.
        execution = application_log['executions'][0]
        self.check_execution_result(execution, exception='Invalid committee signature')

    def _check_committee_update_storage_price(self, storage_price: int):
        # Step 9: set the storage_price to `storage_price` by validators
        tx = self._make_update_storage_price_tx(storage_price)
        tx_hash = self.client.send_raw_tx(tx.to_array())
        tx_id = tx_hash['hash']
        self.logger.info(f"committee update storage_price transaction sent: {tx_id}")

        # Step 10: wait for the next block
        block_index = self.client.get_block_index()
        self.wait_next_block(block_index)

        # Step 11: check the application log
        application_log = self.client.get_application_log(tx_id)
        self.logger.info(f"Committee update storage_price application log: {application_log}")
        assert 'txid' in application_log and tx_id == application_log['txid']
        assert 'executions' in application_log and len(application_log['executions']) == 1

        # Check the execution, committee has permission to update the storage_price.
        execution = application_log['executions'][0]
        self.check_execution_result(execution, stack=[('Any', None)])

        # Step 12: get the storage_price again, it should be `storage_price`.
        result = self.client.invoke_function(POLICY_CONTRACT_HASH, "getStoragePrice", [])
        self.logger.info(f"Get updated storage_price result: {result}")
        self.check_stack(result['stack'], [('Integer', str(storage_price))])

    def _check_storage_price_range(self):
        # Step 13: check the storage_price range
        tx = self._make_update_storage_price_tx(self.min_storage_price - 1)
        tx_hash = self.client.send_raw_tx(tx.to_array())
        tx_id = tx_hash['hash']
        self.logger.info(f"update storage_price to {self.min_storage_price - 1} transaction sent: {tx_id}")

        # Step 14: wait for the next block
        block_index = self.client.get_block_index()
        self.wait_next_block(block_index)

        # Step 15: check the application log
        application_log = self.client.get_application_log(tx_id)
        self.logger.info(f"Update storage_price to {self.min_storage_price - 1} application log: {application_log}")
        assert 'txid' in application_log and tx_id == application_log['txid']
        assert 'executions' in application_log and len(application_log['executions']) == 1

        # Check the execution, the storage_price is {self.min_storage_price - 1}, so the transaction is fault.
        execution = application_log['executions'][0]
        self.check_execution_result(
            execution, exception=f'StoragePrice must be between [{self.min_storage_price}, {self.max_storage_price}]')

        tx = self._make_update_storage_price_tx(self.max_storage_price + 1)
        tx_hash = self.client.send_raw_tx(tx.to_array())
        tx_id = tx_hash['hash']
        self.logger.info(f"update storage_price to {self.max_storage_price + 1} transaction sent: {tx_id}")

        # Step 16: wait for the next block
        block_index = self.client.get_block_index()
        self.wait_next_block(block_index)

        # Step 17: check the application log
        application_log = self.client.get_application_log(tx_id)
        self.logger.info(f"Update storage_price to {self.max_storage_price + 1} application log: {application_log}")
        assert 'txid' in application_log and tx_id == application_log['txid']
        assert 'executions' in application_log and len(application_log['executions']) == 1

        # Check the execution, the storage_price is {self.max_storage_price + 1}, so the transaction is fault.
        execution = application_log['executions'][0]
        self.check_execution_result(
            execution, exception=f'StoragePrice must be between [{self.min_storage_price}, {self.max_storage_price}]')

    def run_test(self):
        self._get_original_storage_price()
        self._check_invoke_function_update_storage_price()
        self._check_no_permission_update_storage_price()
        self._check_storage_price_range()
        self._check_committee_update_storage_price(self.updated_storage_price)

    # Post test: set the storage_price to original storage_price.
    def post_test(self):
        self._check_committee_update_storage_price(self.original_storage_price)


# Run with: python3 -B -m testcases.policy.storage_price
if __name__ == "__main__":
    test = StoragePrice()
    test.run()
