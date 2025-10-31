# Copyright (C) 2015-2025 The Neo Project.
#
# testcases/fee/netfee_size_fee.py file belongs to the neo project and is free
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


# Operation: Send a tx, the netfee depends on the tx size, verification cost and tx-attributes fee.
#  1. The netfee should be increased when the tx size is increased.
# Expect Result: The checking netfee is correct.
class NetworkFeeSizeFee(FeeTesting):
    def __init__(self, loggerName: str = "NetworkFeeSizeFee"):
        super().__init__(loggerName)

        self.update_fee_per_byte = self.fee_per_byte + 100

    def pre_test(self):
        super().pre_test()
        self.update_fee_per_byte = self.fee_per_byte + 100

    def _update_fee_per_byte(self, fee_per_byte: int):
        # Step 1: update the fee_per_byte
        block_index = self.client.get_block_index()
        script = ScriptBuilder().emit_dynamic_call(
            script_hash=POLICY_CONTRACT_HASH,
            method='setFeePerByte',
            call_flags=CallFlags.STATES,
            args=[fee_per_byte],
        ).to_bytes()
        tx = self.make_multisig_tx(script, self.default_sysfee, self.default_netfee,
                                   block_index+10, is_committee=True)
        tx_id = self.client.send_raw_tx(tx.to_array())['hash']
        self.logger.info(f"Transaction sent: {tx_id}")

        block_index = self.client.get_block_index()
        self.wait_next_block(block_index)

        log = self.client.get_application_log(tx_id)
        self.logger.info(f"Application log for update fee_per_byte: {log}")
        self.check_execution_result(log['executions'][0], stack=[('Any', None)])

    def run_test(self):
        # Step 1: build a tx with PUSH1 opcode and a tx with PUSH1 opcode and RET opcode
        block_index = self.client.get_block_index()
        script = ScriptBuilder().emit(OpCode.PUSH1).to_bytes()
        tx1 = self.make_tx(self.env.others[0], script, 0, 0, block_index+10)

        result = self.client.calculate_network_fee(tx1.to_array())
        self.logger.info(f"Calculate network fee: {result}")
        network_fee1 = int(result['networkfee'])

        script = ScriptBuilder().emit(OpCode.PUSH1).emit(OpCode.RET).to_bytes()
        tx2 = self.make_tx(self.env.others[0], script, 0, 0, block_index+10)

        result = self.client.calculate_network_fee(tx2.to_array())
        self.logger.info(f"Calculate network fee: {result}")
        network_fee2 = int(result['networkfee'])

        # Step 2: check the network fee, tx2.size == tx1.size + 1, so the network fee should be networkfee1 + fee_per_byte.
        assert network_fee2 == network_fee1 + self.fee_per_byte, \
            f"Expected networkfee2 == networkfee1 + fee_per_byte, got {network_fee2} != {network_fee1 + self.fee_per_byte}"

        # Step 3: update the fee_per_byte, to check setFeePerByte works as expected.
        self._update_fee_per_byte(self.update_fee_per_byte)

        # Step 4: recalculate the network fee
        result = self.client.calculate_network_fee(tx1.to_array())
        self.logger.info(f"Calculate network fee: {result}")
        network_fee3 = int(result['networkfee'])

        result = self.client.calculate_network_fee(tx2.to_array())
        self.logger.info(f"Calculate network fee: {result}")
        network_fee4 = int(result['networkfee'])

        assert network_fee4 == network_fee3 + self.update_fee_per_byte, \
            f"Expected networkfee4 == networkfee3 + update_fee_per_byte, got {network_fee4} != {network_fee3 + self.update_fee_per_byte}"

    def post_test(self):
        # Step 5: set the fee_per_byte to original fee_per_byte
        self._update_fee_per_byte(self.fee_per_byte)


# Run with: python3 -B -m testcases.fee.netfee_size_fee
if __name__ == "__main__":
    test = NetworkFeeSizeFee()
    test.run()
