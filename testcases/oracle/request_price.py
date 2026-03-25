
from neo.contract import *
from testcases.testing import Testing


# Operation: this case tests the RequestPrice(get/set Price) in Oracle contract.
# 1. get the Price.
# 2. only committee can set the Price, and the price cannot be negative.
class OracleRequestPrice(Testing):
    def __init__(self):
        super().__init__("OracleRequestPrice")
        self.original_price = 5000_0000  # 0.5 GAS
        self.update_price = 1000_0000   # 0.1 GAS

    def _get_price(self):
        result = self.client.invoke_function(ORACLE_CONTRACT_HASH, "getPrice", [])
        self.logger.info(f"getPrice result: {result}")
        assert 'stack' in result and len(result['stack']) == 1, f"Expected 'stack' in result, got {result}"
        return int(result['stack'][0]['value'])

    def _set_price_no_permission(self, price: int):
        result = self.client.invoke_function(ORACLE_CONTRACT_HASH, "setPrice", [
                                             ContractParameter(type="Integer", value=price)])
        self.logger.info(f"setPrice result: {result}")
        assert 'exception' in result and 'Invalid committee signature' in result['exception']

    def _set_price_negative(self):
        result = self.client.invoke_function(ORACLE_CONTRACT_HASH, "setPrice", [
                                             ContractParameter(type="Integer", value=-1)])
        self.logger.info(f"setPrice result: {result}")
        assert 'exception' in result and 'must be positive' in result['exception']

    def _set_price(self, price: int):
        # Step 1: make the transaction to set the price
        block_index = self.client.get_block_index()
        script = ScriptBuilder().emit_dynamic_call(
            script_hash=ORACLE_CONTRACT_HASH,
            method='setPrice',
            call_flags=(CallFlags.STATES | CallFlags.ALLOW_NOTIFY),
            args=[price],
        ).to_bytes()

        tx = self.make_multisig_tx(script, self.default_sysfee, self.default_netfee,
                                   block_index+10, is_committee=True)

        # Step 2: send the transaction to the network
        tx_id = self.client.send_raw_tx(tx.to_array())['hash']
        self.logger.info(f"setPrice {price} transaction sent: {tx_id}")

        # Step 3: wait for the next block
        block_index = self.client.get_block_index()
        self.wait_next_block(block_index)

        # Step 4: check the application log
        application_log = self.client.get_application_log(tx_id)
        self.logger.info(f"setPrice {price} application log: {application_log}")
        assert 'txid' in application_log and tx_id == application_log['txid']
        assert 'executions' in application_log and len(application_log['executions']) == 1

        # Check the execution, committee has permission to set the price.
        execution = application_log['executions'][0]
        self.check_execution_result(execution, stack=[('Any', None)])

    def run_test(self):
        # Step 1: get the original price
        self.original_price = self._get_price()

        # Step 2: set the price with no permission
        self._set_price_no_permission(self.original_price)

        # Step 3: set the price with negative value
        self._set_price_negative()

        # Step 4: set the price with positive value
        self._set_price(self.update_price)

        # Step 5: get the price again
        updated_price = self._get_price()

        # Step 6: check the price is updated
        assert updated_price == self.update_price, f"Expected price to be {self.update_price}, got {updated_price}"

    def post_test(self):
        self._set_price(self.original_price)

# Run with: python3 -B -m testcases.oracle.request_price
if __name__ == "__main__":
    test = OracleRequestPrice()
    test.run()
