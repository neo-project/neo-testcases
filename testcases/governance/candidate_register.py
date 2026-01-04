
import base64

from neo import Account, CallFlags
from neo.contract import NEO_CONTRACT_HASH, ScriptBuilder
from testcases.testing import Testing


# Operation: this case registers candidates(self.env.others[0,1]).
# Method: RegisterCandidate(byte[] publicKey) -> bool
#  1. The publickey cannot be null.
#  2. The system fee must greater than the register price + original system fee.
#  3. Only can register self.
#  4. The vote is zero after initial registration.
# Expect Result: The candidate is registered successfully.
class CandidateRegister(Testing):

    def __init__(self):
        super().__init__("CandidateRegister")
        self.register_price = 1000_00000000  # 1000 GAS

    def _get_register_price(self):
        result = self.client.invoke_function(NEO_CONTRACT_HASH, "getRegisterPrice", [])
        self.logger.info(f"GetRegisterPrice result: {result}")
        self.register_price = int(result['stack'][0]['value'])

    def _check_register_notification(self, public_key: bytes, notification: list[dict]):
        assert len(notification) == 1

        # notification[0] is base64 encoded public key
        assert 'type' in notification[0] and notification[0]['type'] == 'ByteString'
        assert 'value' in notification[0] and notification[0]['value'] == base64.b64encode(public_key).decode('utf-8')

        # notification[1] is True
        assert 'type' in notification[1] and notification[1]['type'] == 'Boolean'
        assert 'value' in notification[1] and notification[1]['value'] == True

        # notification[2] is Vote count. 0 because no vote yet.
        assert 'type' in notification[2] and notification[2]['type'] == 'Integer'
        assert 'value' in notification[2] and notification[2]['value'] == 0

    def _register_with_null(self):
        block_index = self.client.get_block_index()
        script = ScriptBuilder().emit_dynamic_call(
            script_hash=NEO_CONTRACT_HASH,
            method="registerCandidate",
            call_flags=(CallFlags.STATES | CallFlags.ALLOW_NOTIFY),
            args=[None],
        ).to_bytes()

        # Step 1: check register with null and insufficient GAS
        sysfee = self.default_sysfee
        tx = self.make_tx(self.env.others[0], script, sysfee, self.default_netfee, block_index + 10)
        tx_id = self.client.send_raw_tx(tx.to_array())['hash']
        self.logger.info(f"Transaction sent: {tx_id}")

        block_index = self.client.get_block_index()
        self.wait_next_block(block_index)

        application_log = self.client.get_application_log(tx_id)
        self.logger.info(f"Application log: {application_log}")

        execution = application_log['executions'][0]
        assert 'trigger' in execution and execution['trigger'] == 'Application'
        assert execution['vmstate'] == 'FAULT'
        assert 'exception' in execution and 'Insufficient GAS' in execution['exception']

        # Step 2: check register with null and sufficient GAS
        sysfee = self.default_sysfee + self.register_price
        tx = self.make_tx(self.env.others[0], script, sysfee, self.default_netfee, block_index + 10)
        tx_id = self.client.send_raw_tx(tx.to_array())['hash']
        self.logger.info(f"Transaction sent: {tx_id}")

        block_index = self.client.get_block_index()
        self.wait_next_block(block_index)
        application_log = self.client.get_application_log(tx_id)
        self.logger.info(f"Application log: {application_log}")

        execution = application_log['executions'][0]
        assert 'trigger' in execution and execution['trigger'] == 'Application'
        assert execution['vmstate'] == 'FAULT'
        assert 'Object reference not set to an instance of an object' in execution['exception']

    def _get_candidate_votes(self, public_key: bytes):
        public_key = base64.b64encode(public_key).decode('utf-8')
        result = self.client.invoke_function(NEO_CONTRACT_HASH, "getCandidateVote",
                                             [{'type': 'ByteArray', 'value': public_key}])
        self.logger.info(f"GetCandidateVote result: {result}")
        return int(result['stack'][0]['value'])

    def _register_with_ok(self, account: Account, another_public_key: bytes | None = None):
        public_key = another_public_key if another_public_key is not None else account.public_key.encode_point(True)
        candidate_votes = self._get_candidate_votes(public_key)
        if candidate_votes >= 0:
            self.logger.info(f"Candidate {public_key.hex()} has {candidate_votes} votes. Skip registration.")
            return

        # Step 1: check register with public key and sufficient GAS
        block_index = self.client.get_block_index()
        script = ScriptBuilder().emit_dynamic_call(
            script_hash=NEO_CONTRACT_HASH,
            method="registerCandidate",
            call_flags=(CallFlags.STATES | CallFlags.ALLOW_NOTIFY),
            args=[public_key],
        ).to_bytes()
        sysfee = self.default_sysfee + self.register_price
        tx = self.make_tx(account, script, sysfee, self.default_netfee, block_index + 10)
        tx_id = self.client.send_raw_tx(tx.to_array())['hash']
        self.logger.info(f"Transaction sent: {tx_id}")

        block_index = self.client.get_block_index()
        self.wait_next_block(block_index)
        application_log = self.client.get_application_log(tx_id)
        self.logger.info(f"Application log: {application_log}")

        execution = application_log['executions'][0]
        assert 'trigger' in execution and execution['trigger'] == 'Application'
        assert execution['vmstate'] == 'HALT'
        assert 'exception' not in execution or execution['exception'] is None

        # Step 6: check the success of the registration. Not OK if register with another public key.
        success = True if another_public_key is None else False
        self.check_stack(execution['stack'], [('Boolean', success)])

    def run_test(self):
        # Step 1: get the register price
        self._get_register_price()

        # Step 2: register with null
        self._register_with_null()

        # Step 3: register with public key 1
        self._register_with_ok(self.env.others[0])

        # Step 4: register with another public key
        self._register_with_ok(self.env.others[0], self.env.others[1].public_key.encode_point(True))

        # Step 5: register with public key 2
        self._register_with_ok(self.env.others[1])


# Run with: python3 -B -m testcases.governance.candidate_register
if __name__ == "__main__":
    test = CandidateRegister()
    test.run()
