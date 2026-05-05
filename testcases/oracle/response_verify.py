
from neo.contract import *
from testcases.testing import Testing


# Operation: this case tests the verify in Oracle contract.
# 1. verify a tx that contracts OracleResponse attribute or not.
class OracleResponseVerify(Testing):
    def __init__(self):
        super().__init__("OracleResponseVerify")

    def _verify_with_tx(self):
        # Step 1: build the transaction
        block_index = self.client.get_block_index()
        script = ScriptBuilder().emit_dynamic_call(
            script_hash=ORACLE_CONTRACT_HASH,
            method='verify',
            call_flags=CallFlags.NONE,
            args=[],
        ).to_bytes()

        # Step 2: send the transaction
        tx = self.make_tx(self.env.validators[0], script, self.default_sysfee, self.default_netfee, block_index+10)
        tx_id = self.client.send_raw_tx(tx.to_array())['hash']
        self.logger.info(f"verify transaction sent: {tx_id}")

        # Step 3: wait for the next block
        block_index = self.client.get_block_index()
        self.wait_next_block(block_index)

        # Step 4: check the application log
        application_log = self.client.get_application_log(tx_id)
        self.logger.info(f"verify application log: {application_log}")
        execution = application_log['executions'][0]
        assert 'exception' not in execution or execution['exception'] is None
        self.check_execution_result(execution, stack=[('Boolean', False)])

    def _verify_with_invoke(self):
        # Step 1: invoke the verify function
        result = self.client.invoke_function(ORACLE_CONTRACT_HASH, "verify", [])
        self.logger.info(f"verify result: {result}")
        assert 'exception' not in result or result['exception'] is None
        self.check_stack(result['stack'], [('Boolean', False)])

    def run_test(self):
        # Step 1: verify with tx
        self._verify_with_tx()

        # Step 2: verify with invoke
        self._verify_with_invoke()


# Run with: python3 -B -m testcases.oracle.response_verify
if __name__ == "__main__":
    test = OracleResponseVerify()
    test.run()
