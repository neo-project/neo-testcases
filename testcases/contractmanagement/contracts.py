
import base64
from neo.contract import *
from testcases.testing import Testing


# Operation: this case tests the contract management methods(getContract, getContractCount).
#  1. the getContract returns the deployed contract information with the specified hash, null if not found.
#   format: [Id, UpdateCounter, Hash, Nef Manifest]
#  2. the isContract returns true if the specified hash is a deployed contract, false otherwise.
#  3. the getContractById returns the deployed contract information with the specified id, null if not found.
#  4. the hasMethod returns true if the specified method with specified parameters count is implemented
#    by the specified contract, false otherwise.
# Expect Result: The contract management methods are working as expected.
class Contracts(Testing):
    def __init__(self):
        super().__init__("Contracts")

    def _decode_hash(self, hash: str) -> str:
        hash = hash[2:] if hash.startswith('0x') else hash
        hash = bytes.fromhex(hash)[::-1]  # reverse the hash and then encode to base64
        return base64.b64encode(hash).decode('utf-8')

    def _check_contract_state(self, result: dict, contract_hash: str | None, contract_id: int | None):
        stack = result['stack']
        if contract_id is not None and contract_hash is not None:
            assert len(stack) == 1 and stack[0]['type'] == 'Array', f"Expected Array, got {stack[0]['type']}"
            value = stack[0]['value']
            assert len(value) == 5, f"Expected 5 item in value, got {len(value)}"
            self.check_stack(value[:3],
                             [('Integer', str(contract_id)), ('Integer', str(1)), ('ByteString', contract_hash)])
        else:
            assert len(stack) == 1, f"Expected 1 item in stack, got {len(stack)}"
            assert stack[0]['type'] == 'Any', f"Expected Any, got {stack[0]['type']}"

    def _get_contract(self, contract_hash: str, contract_id: int | None):
        contract_hash = self._decode_hash(contract_hash)
        result = self.client.invoke_function(CONTRACT_MANAGEMENT_CONTRACT_HASH, "getContract",
                                             [ContractParameter(type="ByteArray", value=contract_hash)])
        self.logger.info(f"getContract result: {result}")
        self._check_contract_state(result, contract_hash, contract_id)

    def _is_contract(self, contract_hash: str, expected: bool):
        contract_hash = self._decode_hash(contract_hash)
        result = self.client.invoke_function(CONTRACT_MANAGEMENT_CONTRACT_HASH, "isContract",
                                             [ContractParameter(type="ByteArray", value=contract_hash)])
        self.logger.info(f"isContract result: {result}")
        self.check_stack(result['stack'], [('Boolean', expected)])

    def _get_contract_by_id(self, contract_id: int, contract_hash: str | None):
        result = self.client.invoke_function(CONTRACT_MANAGEMENT_CONTRACT_HASH, "getContractById",
                                             [ContractParameter(type="Integer", value=contract_id)])
        self.logger.info(f"getContractById result: {result}")
        self._check_contract_state(result, contract_hash, contract_id)

    def _has_method(self, contract_hash: str, method: str, pcount: int, expected: bool):
        contract_hash = self._decode_hash(contract_hash)
        result = self.client.invoke_function(CONTRACT_MANAGEMENT_CONTRACT_HASH, "hasMethod",
                                             [ContractParameter(type="ByteArray", value=contract_hash),
                                              ContractParameter(type="String", value=method),
                                              ContractParameter(type="Integer", value=pcount)])
        self.logger.info(f"hasMethod result: {result}")
        self.check_stack(result['stack'], [('Boolean', expected)])

    def run_test(self):
        # Step 1: get the contract
        self._get_contract(STDLIB_CONTRACT_HASH, -2)  # STDLIB contract id is -2
        self._get_contract('0x0000000000000000000000000000000000000000', None)

        # Step 2: is the contract
        self._is_contract(STDLIB_CONTRACT_HASH, True)
        self._is_contract('0x0000000000000000000000000000000000000000', False)

        # Step 3: get the contract by id
        self._get_contract_by_id(-1, self._decode_hash(CONTRACT_MANAGEMENT_CONTRACT_HASH))
        self._get_contract_by_id(-1024, None)

        # Step 4: has the method. Note: -1 means any parameters count
        self._has_method(CONTRACT_MANAGEMENT_CONTRACT_HASH, "getContract", -1, True)
        self._has_method(CONTRACT_MANAGEMENT_CONTRACT_HASH, "getContractById", 1, True)

        # Step 5: has the method with multiple parameters
        self._has_method(CONTRACT_MANAGEMENT_CONTRACT_HASH, "hasMethod", 1, False)
        self._has_method(CONTRACT_MANAGEMENT_CONTRACT_HASH, "hasMethod", 3, True)
        self._has_method(CONTRACT_MANAGEMENT_CONTRACT_HASH, "hasMethod", -1, True)


# Run with: python3 -B -m testcases.contractmanagement.contracts
if __name__ == "__main__":
    contracts = Contracts()
    contracts.run()
