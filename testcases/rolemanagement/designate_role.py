
import base64

from neo.contract import *
from testcases.testing import Testing


ROLE_STATE_VALIDATOR = 4
ROLE_ORACLE = 8
ROLE_NEOFS_ALPHABET_NODE = 16
ROLE_P2P_NOTARY = 32


# Operation: this case tests the role designation methods(getDesignatedByRole, designateAsRole).
#  1. the getDesignatedByRole returns the designated role for the given role.
#  2. the designateAsRole designates the given role to the given account.
# Expect Result: The role designation methods are working as expected.
class DesignateRole(Testing):

    def __init__(self):
        super().__init__("DesignateRole")

    def _get_designated_by_role(self, role: int, block_index: int, expected: list | None = None):
        result = self.client.invoke_function(ROLE_MANAGEMENT_CONTRACT_HASH, "getDesignatedByRole",
                                             [ContractParameter(type="Integer", value=role),
                                              ContractParameter(type="Integer", value=block_index)])
        self.logger.info(f"getDesignatedByRole result: {result}")
        if expected is None:
            assert 'exception' not in result or result['exception'] is None
            assert len(result['stack']) == 1 and result['stack'][0]['type'] == 'Array'
        else:
            self.check_stack(result['stack'], expected)
        return result['stack'][0]['value']

    def _get_role_with_invalid_role(self, block_index: int):
        role = 255  # invalid role
        result = self.client.invoke_function(ROLE_MANAGEMENT_CONTRACT_HASH, "getDesignatedByRole",
                                             [ContractParameter(type="Integer", value=role),
                                              ContractParameter(type="Integer", value=block_index)])
        self.logger.info(f"getDesignatedByRole result: {result}")
        assert 'exception' in result and 'Role 255 is not valid' in result['exception']

    def _get_role_with_invalid_block_index(self, block_index: int):
        role = ROLE_STATE_VALIDATOR  # valid role
        result = self.client.invoke_function(ROLE_MANAGEMENT_CONTRACT_HASH, "getDesignatedByRole",
                                             [ContractParameter(type="Integer", value=role),
                                              ContractParameter(type="Integer", value=block_index)])
        self.logger.info(f"getDesignatedByRole result: {result}")
        assert 'exception' in result and 'exceeds current index' in result['exception']

    def _set_role_with_invalid_role(self, block_index: int):
        role = 255  # invalid role
        node = str(self.env.validators[0].public_key)
        result = self.client.invoke_function(
            ROLE_MANAGEMENT_CONTRACT_HASH, "designateAsRole",
            [ContractParameter(type="Integer", value=role),
             ContractParameter(type="Array", value=[ContractParameter(type="PublicKey", value=node)])])
        self.logger.info(f"designateAsRole result: {result}")
        assert 'exception' in result and 'Role 255 is not valid' in result['exception']

    def _set_role_with_invalid_nodes(self, block_index: int):
        role = ROLE_STATE_VALIDATOR  # valid role
        result = self.client.invoke_function(ROLE_MANAGEMENT_CONTRACT_HASH, "designateAsRole",
                                             [ContractParameter(type="Integer", value=role),
                                              ContractParameter(type="Array", value=[])])
        self.logger.info(f"designateAsRole result: {result}")
        assert 'exception' in result and 'must be between 1 and 32' in result['exception']

        nodes = [ContractParameter(type="PublicKey", value=str(self.env.validators[0].public_key)) for _ in range(33)]
        result = self.client.invoke_function(ROLE_MANAGEMENT_CONTRACT_HASH, "designateAsRole",
                                             [ContractParameter(type="Integer", value=role),
                                              ContractParameter(type="Array", value=nodes)])
        self.logger.info(f"designateAsRole result: {result}")
        assert 'exception' in result and 'must be between 1 and 32' in result['exception']

    def _set_role_with_not_committee(self, block_index: int):
        role = ROLE_STATE_VALIDATOR  # valid role
        nodes = [ContractParameter(type="PublicKey", value=str(self.env.validators[0].public_key))]
        result = self.client.invoke_function(ROLE_MANAGEMENT_CONTRACT_HASH, "designateAsRole",
                                             [ContractParameter(type="Integer", value=role),
                                              ContractParameter(type="Array", value=nodes)])
        self.logger.info(f"designateAsRole result: {result}")
        assert 'exception' in result and 'Invalid committee signature' in result['exception']

    def _public_key_stack_item(self, public_key) -> dict:
        return {'type': 'ByteString', 'value': base64.b64encode(public_key.to_array()).decode('utf-8')}

    def _set_role_with_committee(self, role: int, nodes: list):
        # Step 1: build the committee transaction
        block_index = self.client.get_block_index()
        script = ScriptBuilder().emit_dynamic_call(
            script_hash=ROLE_MANAGEMENT_CONTRACT_HASH,
            method='designateAsRole',
            call_flags=CallFlags.STATES | CallFlags.ALLOW_NOTIFY,
            args=[role, [node.public_key for node in nodes]],
        ).to_bytes()
        tx = self.make_multisig_tx(script, self.default_sysfee, self.default_netfee,
                                   block_index + 10, is_committee=True)

        # Step 2: send the transaction
        tx_id = self.client.send_raw_tx(tx.to_array())['hash']
        self.logger.info(f"designateAsRole transaction sent: {tx_id}")

        # Step 3: wait for the next block
        block_index = self.client.get_block_index()
        persisted_index = self.wait_next_block(block_index, wait_while=f"waiting for designateAsRole tx {tx_id}")

        # Step 4: check the application log
        application_log = self.client.get_application_log(tx_id)
        self.logger.info(f"designateAsRole application log: {application_log}")
        assert 'txid' in application_log and tx_id == application_log['txid']
        assert 'executions' in application_log and len(application_log['executions']) == 1
        execution = application_log['executions'][0]
        self.check_execution_result(execution, stack=[('Any', None)])

        notifications = execution['notifications']
        assert len(notifications) == 1, f"Expected one notification, got {len(notifications)}"
        notification = notifications[0]
        assert notification['eventname'] == 'Designation'
        state = notification['state']['value']
        self.check_stack(state[:2], [('Integer', str(role)), ('Integer', str(persisted_index))])
        if len(state) == 4:
            self.check_stack(state[3]['value'],
                             [('ByteString', self._public_key_stack_item(nodes[0].public_key)['value'])])

        return persisted_index + 1

    def run_test(self):
        # Step 1: get the designated roles
        block_index = self.client.get_block_index()
        self._get_designated_by_role(ROLE_STATE_VALIDATOR, block_index)
        self._get_designated_by_role(ROLE_ORACLE, block_index)
        self._get_designated_by_role(ROLE_NEOFS_ALPHABET_NODE, block_index)
        self._get_designated_by_role(ROLE_P2P_NOTARY, block_index)

        # Step 2: check get role with invalid role
        self._get_role_with_invalid_role(block_index)

        # Step 3: check get role with invalid block index
        self._get_role_with_invalid_block_index(block_index + 100)  # out of range

        # Step 4: check set role with invalid role
        self._set_role_with_invalid_role(block_index)

        # Step 5: check set role with invalid public key
        self._set_role_with_invalid_nodes(block_index)

        # Step 6: check set role with not committee
        self._set_role_with_not_committee(block_index)

        # Step 7: check set role with valid nodes
        nodes = [self.env.validators[0]]
        effective_index = self._set_role_with_committee(ROLE_NEOFS_ALPHABET_NODE, nodes)
        self._get_designated_by_role(ROLE_NEOFS_ALPHABET_NODE, effective_index,
                                     [('Array', [self._public_key_stack_item(nodes[0].public_key)])])


if __name__ == "__main__":
    test = DesignateRole()
    test.run()
