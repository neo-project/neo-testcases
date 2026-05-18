
from neo.contract import *
from testcases.testing import Testing


ROLE_STATE_VALIDATOR = 4
ROLE_ORACLE = 8
ROLE_NEOFS_ALPHABET_NODE = 16
ROLE_P2P_NOTARY = 32


# Operation: this case tests the role designation methods(getDesignatedByRole, designateAsRole).
#  1. getDesignatedByRole returns the designated role for the given role and block index.
#  2. designateAsRole updates role nodes only with committee signature and persists on-chain.
#  3. designateAsRole rejects duplicated public keys.
# Expect Result: Role designation methods are working as expected.
class DesignateRole(Testing):

    def __init__(self):
        super().__init__("DesignateRole")

    def _get_designated_by_role(self, role: int, block_index: int, expected: list = []):
        result = self.client.invoke_function(
            ROLE_MANAGEMENT_CONTRACT_HASH,
            "getDesignatedByRole",
            [
                ContractParameter(type="Integer", value=role),
                ContractParameter(type="Integer", value=block_index),
            ],
        )
        self.logger.info(f"getDesignatedByRole result: {result}")
        self.check_stack(result['stack'], expected)

    def _get_role_with_invalid_role(self, block_index: int):
        role = 255  # invalid role
        result = self.client.invoke_function(
            ROLE_MANAGEMENT_CONTRACT_HASH,
            "getDesignatedByRole",
            [
                ContractParameter(type="Integer", value=role),
                ContractParameter(type="Integer", value=block_index),
            ],
        )
        self.logger.info(f"getDesignatedByRole result: {result}")
        assert 'exception' in result and 'Role 255 is not valid' in result['exception']

    def _get_role_with_invalid_block_index(self, block_index: int):
        role = ROLE_STATE_VALIDATOR  # valid role
        result = self.client.invoke_function(
            ROLE_MANAGEMENT_CONTRACT_HASH,
            "getDesignatedByRole",
            [
                ContractParameter(type="Integer", value=role),
                ContractParameter(type="Integer", value=block_index),
            ],
        )
        self.logger.info(f"getDesignatedByRole result: {result}")
        assert 'exception' in result and 'exceeds current index' in result['exception']

    def _set_role_with_invalid_role(self):
        role = 255  # invalid role
        node = str(self.env.validators[0].public_key)
        result = self.client.invoke_function(
            ROLE_MANAGEMENT_CONTRACT_HASH,
            "designateAsRole",
            [
                ContractParameter(type="Integer", value=role),
                ContractParameter(type="Array", value=[ContractParameter(type="PublicKey", value=node)]),
            ],
        )
        self.logger.info(f"designateAsRole result: {result}")
        assert 'exception' in result and 'Role 255 is not valid' in result['exception']

    def _set_role_with_invalid_nodes(self):
        role = ROLE_STATE_VALIDATOR  # valid role
        result = self.client.invoke_function(
            ROLE_MANAGEMENT_CONTRACT_HASH,
            "designateAsRole",
            [
                ContractParameter(type="Integer", value=role),
                ContractParameter(type="Array", value=[]),
            ],
        )
        self.logger.info(f"designateAsRole result: {result}")
        assert 'exception' in result and 'must be between 1 and 32' in result['exception']

        nodes = [ContractParameter(type="PublicKey", value=str(self.env.validators[0].public_key)) for _ in range(33)]
        result = self.client.invoke_function(
            ROLE_MANAGEMENT_CONTRACT_HASH,
            "designateAsRole",
            [
                ContractParameter(type="Integer", value=role),
                ContractParameter(type="Array", value=nodes),
            ],
        )
        self.logger.info(f"designateAsRole result: {result}")
        assert 'exception' in result and 'must be between 1 and 32' in result['exception']

    def _set_role_with_not_committee(self):
        role = ROLE_STATE_VALIDATOR  # valid role
        nodes = [ContractParameter(type="PublicKey", value=str(self.env.validators[0].public_key))]
        result = self.client.invoke_function(
            ROLE_MANAGEMENT_CONTRACT_HASH,
            "designateAsRole",
            [
                ContractParameter(type="Integer", value=role),
                ContractParameter(type="Array", value=nodes),
            ],
        )
        self.logger.info(f"designateAsRole result: {result}")
        assert 'exception' in result and 'Invalid committee signature' in result['exception']

    def _designate_role_with_committee_tx(self, role: int, node_keys: list[ECPoint], expected_error: str | None = None):
        block_index = self.client.get_block_index()
        script = ScriptBuilder().emit_dynamic_call(
            script_hash=ROLE_MANAGEMENT_CONTRACT_HASH,
            method='designateAsRole',
            call_flags=CallFlags.STATES | CallFlags.ALLOW_NOTIFY,
            args=[role, node_keys],
        ).to_bytes()

        tx = self.make_multisig_tx(
            script, self.default_sysfee, self.default_netfee, block_index + 10, is_committee=True
        )
        tx_id = self.client.send_raw_tx(tx.to_array())['hash']
        self.logger.info(f"designateAsRole transaction sent: {tx_id}")

        block_index = self.client.get_block_index()
        self.wait_next_block(block_index)

        application_log = self.client.get_application_log(tx_id)
        self.logger.info(f"designateAsRole application log: {application_log}")
        execution = application_log['executions'][0]
        if expected_error is None:
            self.check_execution_result(execution, stack=[('Any', None)])
        else:
            self.check_execution_result(execution, exception=expected_error)

    def _set_role_with_duplicate_nodes(self):
        duplicated = [self.env.validators[0].public_key, self.env.validators[0].public_key]
        self._designate_role_with_committee_tx(
            ROLE_ORACLE,
            duplicated,
            expected_error='Duplicate publickeys are not allowed',
        )

    def _set_role_with_valid_nodes(self):
        block_index_before = self.client.get_block_index()
        expected_nodes = [self.env.validators[0].public_key, self.env.validators[1].public_key]

        # Querying at current height should still return the old designation.
        self._get_designated_by_role(ROLE_ORACLE, block_index_before, [('Array', [])])

        self._designate_role_with_committee_tx(ROLE_ORACLE, expected_nodes)

        block_index_after = self.client.get_block_index()
        result = self.client.invoke_function(
            ROLE_MANAGEMENT_CONTRACT_HASH,
            'getDesignatedByRole',
            [
                ContractParameter(type='Integer', value=ROLE_ORACLE),
                ContractParameter(type='Integer', value=block_index_after),
            ],
        )
        self.logger.info(f"getDesignatedByRole after designation: {result}")
        assert 'stack' in result and len(result['stack']) == 1
        assert result['stack'][0]['type'] == 'Array'
        designated = result['stack'][0]['value']
        assert len(designated) == len(expected_nodes), f"Expected {len(expected_nodes)} nodes, got {len(designated)}"

        got_keys = sorted([item['value'] for item in designated])
        expected_keys = sorted([str(node) for node in expected_nodes])
        assert got_keys == expected_keys, f"Expected designated nodes {expected_keys}, got {got_keys}"

    def run_test(self):
        # Step 1: get designated roles for all supported roles.
        block_index = self.client.get_block_index()
        self._get_designated_by_role(ROLE_STATE_VALIDATOR, block_index, [('Array', [])])
        self._get_designated_by_role(ROLE_ORACLE, block_index, [('Array', [])])
        self._get_designated_by_role(ROLE_NEOFS_ALPHABET_NODE, block_index, [('Array', [])])
        self._get_designated_by_role(ROLE_P2P_NOTARY, block_index, [('Array', [])])

        # Step 2: check getDesignatedByRole with invalid role.
        self._get_role_with_invalid_role(block_index)

        # Step 3: check getDesignatedByRole with invalid block index.
        self._get_role_with_invalid_block_index(block_index + 100)

        # Step 4: check designateAsRole with invalid role.
        self._set_role_with_invalid_role()

        # Step 5: check designateAsRole with invalid node list length.
        self._set_role_with_invalid_nodes()

        # Step 6: check designateAsRole without committee signature.
        self._set_role_with_not_committee()

        # Step 7: check designateAsRole with duplicate public keys.
        self._set_role_with_duplicate_nodes()

        # Step 8: check designateAsRole success path and persisted role lookup.
        self._set_role_with_valid_nodes()


if __name__ == "__main__":
    test = DesignateRole()
    test.run()
