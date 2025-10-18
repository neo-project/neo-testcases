# Copyright (C) 2015-2025 The Neo Project.
#
# testcases/basics/gas_rpc_transfer.py file belongs to the neo project and is free
# software distributed under the MIT software license, see the
# accompanying file LICENSE in the main directory of the
# repository or http://www.opensource.org/licenses/mit-license.php
# for more details.
#
# Redistribution and use in source and binary forms with or without
# modifications are permitted.

from neo import CallFlags
from neo.contract import GAS_CONTRACT_HASH, ScriptBuilder
from testcases.basics.base import BasicsTesting


# Operation: this case creates a valid transaction, transfer 0.1 GAS from one account to another.
# and then check GAS balance and the transaction execution result.
# Expect Result: The transaction execution is OK, and GAS transfered as expected.
class GasRpcTransfer(BasicsTesting):
    def __init__(self):
        super().__init__(__class__.__name__)

    def run_test(self):
        # Step 1: Build the transfer script
        source160 = self.env.others[0].script_hash
        dest160 = self.env.others[1].script_hash
        amount = 1_0000000
        script = ScriptBuilder().emit_dynamic_call(
            script_hash=GAS_CONTRACT_HASH,
            method='transfer',
            call_flags=(CallFlags.STATES | CallFlags.ALLOW_CALL | CallFlags.ALLOW_NOTIFY),
            args=[source160, dest160, amount, None],  # transfer(from, to, 0.1 GAS, data)
        ).to_bytes()

        # Step 2: get Destination GAS balance
        source_balance = self.client.get_gas_balance(source160)
        self.logger.info(f"Source {source160} GAS balance: {source_balance}")

        dest_balance = self.client.get_gas_balance(dest160)
        self.logger.info(f"Destination {dest160} GAS balance: {dest_balance}")

        # Step 3: create a transaction
        block_index = self.client.get_block_index()
        tx = self.make_tx(self.env.others[0], script, self.default_sysfee, self.default_sysfee, block_index+10)

        # Step 4: send the transaction to the network
        tx_hash = self.client.send_raw_tx(tx.to_array())
        assert isinstance(tx_hash, dict), f"Expected dict, got {tx_hash}"
        assert 'hash' in tx_hash, f"Expected hash in tx_hash, got {tx_hash}"
        tx_id = tx_hash['hash']
        self.logger.info(f"Transaction sent: {tx_id}")

        # Step 5: check the mempool
        mempool = self.client.get_mempool(include_unverified=True)
        self.logger.info(f"Mempool: {mempool}")

        # The tx maybe have been executed, so not assert this.
        # assert tx_id in mempool['verified'], f"Expected tx_id in mempool['verified'], got {mempool}"
        assert tx_id not in mempool['unverified'], f"Expected tx_id not in mempool['unverified'], got {mempool}"

        # Step 6: wait for the next block
        block_index = self.client.get_block_index()
        self.wait_next_block(block_index)

        application_log = self.client.get_application_log(tx_id)
        self.logger.info(f"Application log: {application_log}")

        # Step 7: check the gas balance
        from_balance = self.client.get_gas_balance(source160)
        self.logger.info(f"Source {source160} GAS balance: {from_balance}, difference: {from_balance - source_balance}")
        expected = source_balance - amount - self.default_sysfee - self.default_netfee
        assert from_balance == expected, f"Expected from_balance == {expected}, got {from_balance}"

        to_balance = self.client.get_gas_balance(dest160)
        assert to_balance == dest_balance + amount, f"to_balance:{to_balance} != {dest_balance} + {amount}"

        # Step 8: check the application log
        assert 'txid' in application_log and tx_id == application_log['txid']
        assert 'executions' in application_log and len(application_log['executions']) == 1

        # Check the execution
        execution = application_log['executions'][0]
        assert 'trigger' in execution and execution['trigger'] == 'Application'
        assert 'vmstate' in execution and execution['vmstate'] == 'HALT'
        assert 'exception' in execution and execution['exception'] is None
        assert 'stack' in execution and len(execution['stack']) == 1

        # Check the stack
        stack_item = execution['stack'][0]
        assert 'type' in stack_item and stack_item['type'] == 'Boolean'
        assert 'value' in stack_item and stack_item['value'] == True

        # Check the notifications
        assert 'notifications' in execution and len(execution['notifications']) == 1
        notification = execution['notifications'][0]
        self._check_nep17_transfer_notification(notification, GAS_CONTRACT_HASH, source160, dest160, amount)


# Run with: python3 -B -m testcases.basics.gas_rpc_transfer
if __name__ == "__main__":
    test = GasRpcTransfer()
    test.run()
