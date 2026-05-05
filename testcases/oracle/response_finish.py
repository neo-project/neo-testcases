
from neo import *
from neo.contract import *
from testcases.testing import Testing


# Operation: this case tests the finish in Oracle contract.
# 1. finish a request and callback will be called.
class OracleResponseFinish(Testing):
    def __init__(self):
        super().__init__("OracleResponseFinish")

    def _check_invocation_counter(self):
        result = self.client.invoke_function(ORACLE_CONTRACT_HASH, "finish", [])
        self.logger.info(f"finish result: {result}")
        assert 'exception' in result  # Object reference not set to an instance of an object
        self.check_stack(result['stack'], [])

    def _check_tx_no_response(self):
        # Step 1: build the transaction
        block_index = self.client.get_block_index()
        script = ScriptBuilder().emit_dynamic_call(
            script_hash=ORACLE_CONTRACT_HASH,
            method='finish',
            call_flags=CallFlags.ALL,
            args=[],
        ).to_bytes()

        # Step 2: send the transaction
        tx = self.make_tx(self.env.validators[0], script, self.default_sysfee, self.default_netfee, block_index+10)
        tx_id = self.client.send_raw_tx(tx.to_array())['hash']
        self.logger.info(f"finish transaction sent: {tx_id}")

        # Step 3: wait for the next block
        block_index = self.client.get_block_index()
        self.wait_next_block(block_index)

        # Step 4: check the application log
        application_log = self.client.get_application_log(tx_id)
        self.logger.info(f"finish application log: {application_log}")
        execution = application_log['executions'][0]
        assert 'exception' in execution and 'Oracle response not found' in execution['exception']
        # self.check_execution_result(execution, stack=[])

    def _check_tx_with_invalid_response(self):
        # Step 1: build the transaction
        block_index = self.client.get_block_index()
        script = ScriptBuilder().emit_dynamic_call(
            script_hash=ORACLE_CONTRACT_HASH,
            method='finish',
            call_flags=CallFlags.ALL,
            args=[],
        ).to_bytes()

        # Step 2: send the transaction
        tx = self.make_tx(self.env.validators[0], script, self.default_sysfee, self.default_netfee, block_index+10)
        tx.attributes = [make_oracle_response(b'{}')]
        with BinaryWriter() as writer:
            tx.serialize_unsigned(writer)
            raw_tx = writer.to_array()
        sign = self.sign(self.env.validators[0].private_key, raw_tx)
        tx.witnesses = [self.make_witness(sign, self.env.validators[0].public_key)]
        try:
            tx_id = self.client.send_raw_tx(tx.to_array())['hash']
            self.logger.info(f"finish transaction sent: {tx_id}")
        except Exception as ex:
            self.logger.info(f"finish transaction failed: {ex}")
            'InvalidAttribute' in str(ex)

    def run_test(self):
        # Step 1: check the Invocation_counter
        self._check_invocation_counter()

        # Step 2: check the tx no response
        self._check_tx_no_response()

        # Step 3: check the tx with invalid response
        self._check_tx_with_invalid_response()

        # TODO: check the tx with valid response


# Run with: python3 -B -m testcases.oracle.response_finish
if __name__ == "__main__":
    test = OracleResponseFinish()
    test.run()
