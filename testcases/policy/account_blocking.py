
import base64
from neo.contract import *
from testcases.testing import Testing


# Operation: this case tests the account blocking (blockAccount, unblockAccount, isBlocked, getBlockedAccounts) policy.
#  1. Only committee has permission to block/unblock the account.
#  2. BlockAccount method cannot block a native contract.
#   If the account is already blocked, return false, true otherwise.
#   If the account has votes, the votes will be revoked.
#  3. UnblockAccount returns false if the account is not blocked, true otherwise.
#   If the votes are revoked because of previous block action, votes will not be restored.
class AccountBlocking(Testing):

    def __init__(self):
        super().__init__("AccountBlocking")
        self.account_to_block = "0x0000000000000000000000000000000000000001"

    def _encode_hash(self, hash: str) -> str:
        hash = hash[2:] if hash.startswith('0x') else hash
        hash = bytes.fromhex(hash)
        return base64.b64encode(hash[::-1]).decode('utf-8')

    def _is_blocked(self, account: str, expected: bool):
        hash = self._encode_hash(account)
        result = self.client.invoke_function(POLICY_CONTRACT_HASH, "isBlocked",
                                             [ContractParameter(type='ByteArray', value=hash)])
        self.logger.info(f"isBlocked result: {result}")
        assert 'stack' in result and len(result['stack']) == 1, f"Expected 'stack' in result, got {result}"
        assert result['stack'][0]['value'] == expected, f"Expected {expected}, got {result['stack'][0]['value']}"

    def _is_blocked_null(self):
        result = self.client.invoke_function(POLICY_CONTRACT_HASH, "isBlocked",
                                             [ContractParameter(type='ByteArray', value=None)])
        self.logger.info(f"isBlocked result: {result}")
        assert 'exception' in result and "can't be null" in result['exception']

    def _block_account_no_permission(self, account: str):
        hash = self._encode_hash(account)
        result = self.client.invoke_function(POLICY_CONTRACT_HASH, "blockAccount",
                                             [ContractParameter(type='ByteArray', value=hash)])
        self.logger.info(f"blockAccount {account} result: {result}")
        assert 'exception' in result and "Invalid committee signature" in result['exception']

    def _block_account(self, account: str | None, expected: bool, exception: str | None = None):
        # Step 1: make the transaction to block the account
        account = None if account is None else UInt160.from_string(account)
        block_index = self.client.get_block_index()
        script = ScriptBuilder().emit_dynamic_call(
            script_hash=POLICY_CONTRACT_HASH,
            method='blockAccount',
            call_flags=(CallFlags.STATES | CallFlags.ALLOW_NOTIFY),
            args=[account],
        ).to_bytes()

        # Step 2: send the transaction to the network
        tx = self.make_multisig_tx(script, self.default_sysfee, self.default_netfee,
                                   block_index+10, is_committee=True)
        tx_id = self.client.send_raw_tx(tx.to_array())['hash']
        self.logger.info(f"blockAccount {account} transaction sent: {tx_id}")

        # Step 3: wait for the next block
        block_index = self.client.get_block_index()
        self.wait_next_block(block_index)

        # Step 4: check the application log
        application_log = self.client.get_application_log(tx_id)
        self.logger.info(f"blockAccount {account} application log: {application_log}")
        if exception is None:
            self.check_execution_result(application_log['executions'][0], stack=[('Boolean', expected)])
        else:
            self.check_execution_result(application_log['executions'][0], exception=exception)

    def _unblock_account(self, account: str | None, expected: bool | None, exception: str | None = None):
        # Step 1: make the transaction to unblock the account
        account = None if account is None else UInt160.from_string(account)
        block_index = self.client.get_block_index()
        script = ScriptBuilder().emit_dynamic_call(
            script_hash=POLICY_CONTRACT_HASH,
            method='unblockAccount',
            call_flags=(CallFlags.STATES | CallFlags.ALLOW_NOTIFY),
            args=[account],
        ).to_bytes()

        # Step 2: send the transaction to the network
        tx = self.make_multisig_tx(script, self.default_sysfee, self.default_netfee,
                                   block_index+10, is_committee=True)
        tx_id = self.client.send_raw_tx(tx.to_array())['hash']
        self.logger.info(f"unblockAccount {account} transaction sent: {tx_id}")

        # Step 3: wait for the next block
        block_index = self.client.get_block_index()
        self.wait_next_block(block_index)

        # Step 4: check the application log
        application_log = self.client.get_application_log(tx_id)
        self.logger.info(f"unblockAccount {account} application log: {application_log}")
        if exception is not None:
            self.check_execution_result(application_log['executions'][0], exception=exception)
        elif expected is not None:
            self.check_execution_result(application_log['executions'][0], stack=[('Boolean', expected)])
        else:
            pass  # not check the result

    def run_test(self):
        # Step 1: check the account is not blocked
        self._is_blocked(self.account_to_block, False)

        # Step 2: check the isAccount with null
        self._is_blocked_null()

        # Step 3: block the account with no permission
        self._block_account_no_permission(self.account_to_block)

        # Step 4: block the native contract
        self._block_account(POLICY_CONTRACT_HASH, False, "Cannot block a native contract")

        # Step 5: block the account
        self._block_account(self.account_to_block, True)

        # Step 6: check the account is blocked
        self._is_blocked(self.account_to_block, True)

        # Step 7: block the account again
        self._block_account(self.account_to_block, False)

        # Step 8: unblock the account
        self._unblock_account(self.account_to_block)

        # Step 9: check the account is not blocked
        self._is_blocked(self.account_to_block, False)

        # Step 10: unblock the account again
        self._unblock_account(self.account_to_block, False)

        # Step 11: block the account with null
        self._block_account(None, False, "can't be null")

        # Step 12: unblock the account with null
        self._unblock_account(None, False, "can't be null")

    def post_test(self):
        self._unblock_account(self.account_to_block, None)


# Run with: python3 -B -m testcases.policy.account_blocking
if __name__ == "__main__":
    test = AccountBlocking()
    test.run()
