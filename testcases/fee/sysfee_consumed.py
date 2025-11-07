# Copyright (C) 2015-2025 The Neo Project.
#
# testcases/fee/sysfee_consumed.py file belongs to the neo project and is free
# software distributed under the MIT software license, see the
# accompanying file LICENSE in the main directory of the
# repository or http://www.opensource.org/licenses/mit-license.php
# for more details.
#
# Redistribution and use in source and binary forms with or without
# modifications are permitted.

from neo import OpCode
from neo.contract import *
from testcases.fee.base import FeeTesting


# Operation: Send a tx, the consumed sysfee depends on the opcode and operations.
# Expect Result: The consumed sysfee is correct.
class SystemFeeConsumed(FeeTesting):

    def __init__(self):
        super().__init__("SystemFeeConsumed")
        self.price_push1 = 1

    def run_test(self):
        # Step 2: build a tx with only a RET opcode or PUSH1 opcode
        block_index = self.client.get_block_index()
        script1 = ScriptBuilder().emit(OpCode.RET).to_bytes()
        tx1 = self.make_tx(self.env.others[0], script1, self.default_sysfee, self.default_netfee, block_index+10)

        script2 = ScriptBuilder().emit(OpCode.PUSH1).to_bytes()
        tx2 = self.make_tx(self.env.others[0], script2, self.default_sysfee, self.default_netfee, block_index+10)

        raw_tx1 = tx1.to_array()
        tx_id1 = self.client.send_raw_tx(raw_tx1)['hash']

        raw_tx2 = tx2.to_array()
        tx_id2 = self.client.send_raw_tx(raw_tx2)['hash']
        self.logger.info(f"Transaction sent: {tx_id1} and {tx_id2}")

        # Step 3: wait for the next block
        block_index = self.client.get_block_index()
        self.wait_next_block(block_index)

        # Step 4: check the application log
        log1 = self.client.get_application_log(tx_id1)
        self.logger.info(f"Application log for tx {tx_id1}: {log1}")
        assert 'txid' in log1 and tx_id1 == log1['txid']
        assert 'executions' in log1 and len(log1['executions']) == 1

        # Check the execution, the gasconsumed should be 0(only a RET opcode).
        execution = log1['executions'][0]
        sysfee_comsumed = int(execution['gasconsumed'])  # The `gasconsumed` is the comsumed sysfee.
        assert sysfee_comsumed == 0, f"Expected gasconsumed == 0, got {sysfee_comsumed}"
        self.check_execution_result(execution, stack=[])

        log2 = self.client.get_application_log(tx_id2)
        self.logger.info(f"Application log for tx {tx_id2}: {log2}")
        assert 'txid' in log2 and tx_id2 == log2['txid']
        assert 'executions' in log2 and len(log2['executions']) == 1

        # Check the execution, the gasconsumed should be 1(PUSH1 opcode).
        execution = log2['executions'][0]
        sysfee_comsumed = int(execution['gasconsumed'])  # The `gasconsumed` is the comsumed sysfee.
        assert sysfee_comsumed == self.exec_fee_factor * self.price_push1, \
            f"Expected gasconsumed == {self.exec_fee_factor * self.price_push1}, got {sysfee_comsumed}"
        self.check_execution_result(execution, stack=[('Integer', '1')])


# Run with: python3 -B -m testcases.fee.sysfee_comsumed
if __name__ == "__main__":
    test = SystemFeeConsumed()
    test.run()
