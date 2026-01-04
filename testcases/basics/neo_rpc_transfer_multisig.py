
from neo import CallFlags
from neo.contract import NEO_CONTRACT_HASH, ScriptBuilder
from testcases.basics.base import BasicsTesting


# Operation: this case creates a valid transaction, transfer 1000 NEO from the BFT account to the others[0] account.
# and then check the NEO balance and the transaction execution result.
# Expect Result: The transaction execution is OK, and the NEO balance is as expected.
class NeoRpcTransferMultiSign(BasicsTesting):

    def __init__(self):
        super().__init__("NeoRpcTransferMultiSign")

    def run_test(self):
        # Step 1: Build the transfer script
        source160 = self.bft_address()
        dest160 = self.env.others[0].script_hash
        amount = 1000  # 1000 NEO
        script = ScriptBuilder().emit_dynamic_call(
            script_hash=NEO_CONTRACT_HASH,
            method='transfer',
            call_flags=(CallFlags.STATES | CallFlags.ALLOW_CALL | CallFlags.ALLOW_NOTIFY),
            args=[source160, dest160, amount, None],  # transfer(from, to, 1000 NEO, data)
        ).to_bytes()

        # Step 2: get source and destination NEO balance
        source_balance = self.client.get_neo_balance(source160)
        source_gas = self.client.get_gas_balance(source160)
        self.logger.info(f"Source {source160} NEO balance: {source_balance}, GAS balance: {source_gas}")

        dest_balance = self.client.get_neo_balance(dest160)
        self.logger.info(f"Destination {dest160} NEO balance: {dest_balance}")

        # Step 3: create a transaction
        block_index = self.client.get_block_index()
        # 0.1 GAS system fee, 0.1 GAS network fee
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

        # Step 7: check the source and Destination NEO balance
        from_gas = self.client.get_gas_balance(source160)
        self.logger.info(f"Source {source160} GAS balance: {from_gas}, difference: {from_gas - source_gas}")

        from_balance = self.client.get_neo_balance(source160)
        assert from_balance == source_balance - amount, f"from balance:{from_balance} != {source_balance} - {amount}"

        to_balance = self.client.get_neo_balance(dest160)
        assert to_balance == dest_balance + amount, f"to balance:{to_balance} != {dest_balance} + {amount}"

        # Step 8: check the application log
        self._check_neo_transfer_application_log(tx_id, application_log, source160, dest160, str(amount))


# Run with: python3 -B -m testcases.basics.neo_rpc_transfer_multisig
if __name__ == "__main__":
    test = NeoRpcTransferMultiSign()
    test.run()
