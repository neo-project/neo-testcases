
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
        # TODO: add test case


if __name__ == "__main__":
    test = DesignateRole()
    test.run_test()
