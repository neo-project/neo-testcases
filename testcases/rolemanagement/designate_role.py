
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

    def _get_designated_by_role(self, role: int, block_index: int, expected: list = []):
        result = self.client.invoke_function(ROLE_MANAGEMENT_CONTRACT_HASH, "getDesignatedByRole",
                                             [ContractParameter(type="Integer", value=role),
                                              ContractParameter(type="Integer", value=block_index)])
        self.logger.info(f"getDesignatedByRole result: {result}")
        self.check_stack(result['stack'], expected)

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

    def _set_role_by_committee(self, role: int, nodes: list):
        block_index = self.client.get_block_index()
        script = ScriptBuilder().emit_dynamic_call(
            script_hash=ROLE_MANAGEMENT_CONTRACT_HASH,
            method='designateAsRole',
            call_flags=(CallFlags.STATES | CallFlags.ALLOW_NOTIFY),
            args=[role, nodes],
        ).to_bytes()
        tx = self.make_multisig_tx(script, self.default_sysfee, self.default_netfee, block_index + 10, is_committee=True)
        tx_hash = self.client.send_raw_tx(tx.to_array())
        tx_id = tx_hash['hash']
        self.logger.info(f"designateAsRole transaction sent: {tx_id}")

        block_index = self.client.get_block_index()
        self.wait_next_block(block_index, wait_while=f"persisting role designation tx {tx_id}")

        application_log = self.client.get_application_log(tx_id)
        self.logger.info(f"designateAsRole application log: {application_log}")
        assert 'txid' in application_log and tx_id == application_log['txid']
        assert 'executions' in application_log and len(application_log['executions']) == 1
        self.check_execution_result(application_log['executions'][0], stack=[])

    def _set_role_with_valid_nodes(self):
        role = ROLE_NEOFS_ALPHABET_NODE
        nodes = [self.env.validators[0].public_key]
        self._set_role_by_committee(role, nodes)

        query_index = self.client.get_block_index() + 1
        result = self.client.invoke_function(ROLE_MANAGEMENT_CONTRACT_HASH, "getDesignatedByRole",
                                             [ContractParameter(type="Integer", value=role),
                                              ContractParameter(type="Integer", value=query_index)])
        self.logger.info(f"getDesignatedByRole result after designateAsRole: {result}")
        assert 'exception' not in result or result['exception'] is None
        assert len(result['stack']) == 1 and result['stack'][0]['type'] == 'Array'
        designated_nodes = result['stack'][0]['value']
        assert len(designated_nodes) == 1, f"Expected 1 designated node, got {len(designated_nodes)}"
        assert designated_nodes[0]['type'] == 'ByteString'
        expected = base64.b64encode(nodes[0].to_array()).decode('utf-8')
        assert designated_nodes[0]['value'] == expected, f"Unexpected designated node: {designated_nodes[0]['value']}"

    def run_test(self):
        # Step 1: get the designated roles
        block_index = self.client.get_block_index()
        self._get_designated_by_role(ROLE_STATE_VALIDATOR, block_index, [('Array', [])])
        self._get_designated_by_role(ROLE_ORACLE, block_index, [('Array', [])])
        self._get_designated_by_role(ROLE_NEOFS_ALPHABET_NODE, block_index, [('Array', [])])
        self._get_designated_by_role(ROLE_P2P_NOTARY, block_index, [('Array', [])])

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
        self._set_role_with_valid_nodes()


if __name__ == "__main__":
    test = DesignateRole()
    test.run()
