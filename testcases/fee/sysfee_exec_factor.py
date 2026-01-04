
from neo import OpCode
from neo.contract import *
from testcases.fee.base import FeeTesting


# Operation: Send a tx, the consumed sysfee depends on the opcode and operations and exec_fee_factor.
# 1. The consumed sysfee is the exec_fee_factor * the price of the opcode or operation.
# 2. If the exec_fee_factor changed, the consumed sysfee should be changed.
# Expect Result: The consumed sysfee is correct.
class SystemFeeExecFactor(FeeTesting):

    def __init__(self):
        super().__init__("SystemFeeExecFactor")
        self.price_push1 = 1
        self.updated_exec_fee_factor = self.exec_fee_factor + 10

    def pre_test(self):
        super().pre_test()
        self.updated_exec_fee_factor = self.exec_fee_factor + 10

    def _execute_tx_with_push1_opcode(self, exec_fee_factor: int):
        # Step 2: build a tx with PUSH1 opcode
        block_index = self.client.get_block_index()
        script = ScriptBuilder().emit(OpCode.PUSH1).to_bytes()
        tx = self.make_tx(self.env.others[0], script, self.default_sysfee, self.default_netfee, block_index+10)
        tx_id = self.client.send_raw_tx(tx.to_array())['hash']
        self.logger.info(f"Transaction sent: {tx_id}")

        # Step 3: wait for the next block
        block_index = self.client.get_block_index()
        self.wait_next_block(block_index)

        # Step 4: check the application log
        log = self.client.get_application_log(tx_id)
        self.logger.info(f"Application log: {log}")
        sysfee_comsumed = int(log['executions'][0]['gasconsumed'])
        assert sysfee_comsumed == exec_fee_factor * self.price_push1, \
            f"Expected gasconsumed == {self.exec_fee_factor * self.price_push1}, got {sysfee_comsumed}"
        return tx_id

    def _update_exec_fee_factor(self, exec_fee_factor: int):
        # Step 5: update the exec_fee_factor
        block_index = self.client.get_block_index()
        script = ScriptBuilder().emit_dynamic_call(
            script_hash=POLICY_CONTRACT_HASH,
            method='setExecFeeFactor',
            call_flags=CallFlags.STATES,
            args=[exec_fee_factor],
        ).to_bytes()
        tx = self.make_multisig_tx(script, self.default_sysfee, self.default_netfee,
                                   block_index+10, is_committee=True)
        tx_id = self.client.send_raw_tx(tx.to_array())['hash']
        self.logger.info(f"Transaction sent: {tx_id}")

        block_index = self.client.get_block_index()
        self.wait_next_block(block_index)

        log = self.client.get_application_log(tx_id)
        self.logger.info(f"Application log for update exec fee factor: {log}")
        self.check_execution_result(log['executions'][0], stack=[('Any', None)])

    def run_test(self):
        # Step 2: execute a tx with PUSH1 opcode with the original exec_fee_factor
        _ = self._execute_tx_with_push1_opcode(self.exec_fee_factor)

        # Step 3: update the exec_fee_factor
        self._update_exec_fee_factor(self.updated_exec_fee_factor)

        # Step 4: execute a tx with PUSH1 opcode with the updated exec_fee_factor
        _ = self._execute_tx_with_push1_opcode(self.updated_exec_fee_factor)

    def post_test(self):
        # Step 5: set the exec_fee_factor to original exec_fee_factor
        self._update_exec_fee_factor(self.exec_fee_factor)


# Run with: python3 -B -m testcases.fee.sysfee_exec_factor
if __name__ == "__main__":
    test = SystemFeeExecFactor()
    test.run()
