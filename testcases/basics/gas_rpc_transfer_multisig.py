# Copyright (C) 2015-2025 The Neo Project.
#
# testcases/basics/gas_rpc_transfer_multisig.py file belongs to the neo project and is free
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


# Operation: this case creates a valid transaction, transfer 10000 GAS from the BFT account to the others[0] account.
# and then check the GAS balance and the transaction execution result.
# Expect Result: The transaction execution is OK, and the GAS balance is as expected.
class GasRpcTransferMultiSign(BasicsTesting):
    def __init__(self):
        super().__init__(__class__.__name__)

    def run_test(self):
        # Step 1: Build the transfer script
        source160 = self.bft_address()
        dest160 = self.env.others[0].script_hash
        amount = 10000_00000000  # 10000 GAS
        script = ScriptBuilder().emit_dynamic_call(
            script_hash=GAS_CONTRACT_HASH,
            method='transfer',
            call_flags=(CallFlags.STATES | CallFlags.ALLOW_CALL | CallFlags.ALLOW_NOTIFY),
            args=[source160, dest160, amount, None],  # transfer(from, to, 10000 GAS, None)
        ).to_bytes()

        # Step 2: get source and destination GAS balance
        source_balance = self.client.get_gas_balance(source160)
        self.logger.info(f"Source {source160} GAS balance: {source_balance}")

        dest_balance = self.client.get_gas_balance(dest160)
        self.logger.info(f"Destination {dest160} GAS balance: {dest_balance}")

        # Step 3: create a transaction
        block_index = self.client.get_block_index()
        tx = self.make_multisig_tx(script, self.default_sysfee, self.default_netfee, block_index+10)

        # Step 4: send the transaction to the network
        tx_hash = self.client.send_raw_tx(tx.to_array())
        assert isinstance(tx_hash, dict), f"Expected dict, got {tx_hash}"
        assert 'hash' in tx_hash, f"Expected hash in tx_hash, got {tx_hash}"
        tx_id = tx_hash['hash']
        self.logger.info(f"Transaction sent: {tx_id}")

        # Step 5: check the mempool
        mempool = self.client.get_mempool(include_unverified=True)
        self.logger.info(f"Mempool: {mempool}")

        # Step 6: wait for the next block
        block_index = self.client.get_block_index()
        self.wait_next_block(block_index)

        application_log = self.client.get_application_log(tx_id)
        self.logger.info(f"Application log: {application_log}")

        # Step 7: check the source and destination GAS balance
        from_balance = self.client.get_gas_balance(source160)
        self.logger.info(f"Source {source160} GAS balance: {from_balance}, difference: {from_balance - source_balance}")

        to_balance = self.client.get_gas_balance(dest160)
        assert to_balance == dest_balance + amount, f"Expected to_balance == {dest_balance + amount}, got {to_balance}"

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


# Run with: python3 -B -m testcases.basics.gas_rpc_transfer_multisig
if __name__ == "__main__":
    test = GasRpcTransferMultiSign()
    test.run()
