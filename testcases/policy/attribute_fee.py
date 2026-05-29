
from neo import Hardforks
from neo.contract import *
from testcases.testing import Testing


ATTR_HIGH_PRIORITY = 0x01
ATTR_NOT_VALID_BEFORE = 0x20
ATTR_CONFLICTS = 0x21
ATTR_NOTARY_ASSISTED = 0x22
INVALID_ATTRIBUTE = 0xFF
MAX_ATTRIBUTE_FEE = 10_0000_0000
DEFAULT_ATTRIBUTE_FEE = 0
DEFAULT_NOTARY_ASSISTED_ATTRIBUTE_FEE = 1000_0000


# Operation: this case tests getAttributeFee/setAttributeFee in Policy contract.
#  1. getAttributeFee returns expected default values for supported attributes.
#  2. setAttributeFee requires committee signature for state persistence.
#  3. getAttributeFee/setAttributeFee reject unsupported attribute type.
#  4. setAttributeFee validates upper bound for fee value.
class AttributeFee(Testing):

    def __init__(self):
        super().__init__("AttributeFee")
        self.hardfork = Hardforks.HF_Echidna
        self.new_high_priority_fee = 12345
        self.new_notary_assisted_fee = 23456
        self.original_high_priority_fee = DEFAULT_ATTRIBUTE_FEE
        self.original_notary_assisted_fee = DEFAULT_NOTARY_ASSISTED_ATTRIBUTE_FEE

    def _get_attribute_fee(self, attribute_type: int) -> int:
        result = self.client.invoke_function(
            POLICY_CONTRACT_HASH,
            'getAttributeFee',
            [ContractParameter(type='Integer', value=attribute_type)],
        )
        self.logger.info(f"getAttributeFee({attribute_type}) result: {result}")
        assert 'stack' in result and len(result['stack']) == 1
        return int(result['stack'][0]['value'])

    def _set_attribute_fee_invoke(self, attribute_type: int, fee: int, expected_error: str | None = None):
        result = self.client.invoke_function(
            POLICY_CONTRACT_HASH,
            'setAttributeFee',
            [
                ContractParameter(type='Integer', value=attribute_type),
                ContractParameter(type='Integer', value=fee),
            ],
        )
        self.logger.info(f"setAttributeFee({attribute_type}, {fee}) invoke result: {result}")
        if expected_error is None:
            self.check_stack(result['stack'], [])
        else:
            assert 'exception' in result and expected_error in result['exception']

    def _set_attribute_fee_tx(self, attribute_type: int, fee: int, expected_error: str | None = None):
        block_index = self.client.get_block_index()
        script = ScriptBuilder().emit_dynamic_call(
            script_hash=POLICY_CONTRACT_HASH,
            method='setAttributeFee',
            call_flags=CallFlags.STATES,
            args=[attribute_type, fee],
        ).to_bytes()
        tx = self.make_multisig_tx(
            script, self.default_sysfee, self.default_netfee, block_index + 10, is_committee=True
        )
        tx_id = self.client.send_raw_tx(tx.to_array())['hash']
        self.logger.info(f"setAttributeFee tx sent: {tx_id}")

        block_index = self.client.get_block_index()
        self.wait_next_block(block_index)

        application_log = self.client.get_application_log(tx_id)
        self.logger.info(f"setAttributeFee tx application log: {application_log}")
        execution = application_log['executions'][0]
        if expected_error is None:
            self.check_execution_result(execution, stack=[('Any', None)])
        else:
            self.check_execution_result(execution, exception=expected_error)

    def run_test(self):
        # Step 1: verify default attribute fees.
        self.original_high_priority_fee = self._get_attribute_fee(ATTR_HIGH_PRIORITY)
        self.original_notary_assisted_fee = self._get_attribute_fee(ATTR_NOTARY_ASSISTED)
        assert self.original_high_priority_fee == DEFAULT_ATTRIBUTE_FEE
        assert self.original_notary_assisted_fee == DEFAULT_NOTARY_ASSISTED_ATTRIBUTE_FEE

        # Step 2: verify unsupported attribute type is rejected by getter.
        result = self.client.invoke_function(
            POLICY_CONTRACT_HASH,
            'getAttributeFee',
            [ContractParameter(type='Integer', value=INVALID_ATTRIBUTE)],
        )
        self.logger.info(f"getAttributeFee({INVALID_ATTRIBUTE}) result: {result}")
        assert 'exception' in result and 'is not supported' in result['exception']

        # Step 3: verify committee signature is required.
        self._set_attribute_fee_invoke(
            ATTR_HIGH_PRIORITY, self.new_high_priority_fee, expected_error='Invalid committee signature'
        )

        # Step 4: set and verify a non-notary attribute fee.
        self._set_attribute_fee_tx(ATTR_HIGH_PRIORITY, self.new_high_priority_fee)
        assert self._get_attribute_fee(ATTR_HIGH_PRIORITY) == self.new_high_priority_fee

        # Step 5: set and verify NotaryAssisted attribute fee.
        self._set_attribute_fee_tx(ATTR_NOTARY_ASSISTED, self.new_notary_assisted_fee)
        assert self._get_attribute_fee(ATTR_NOTARY_ASSISTED) == self.new_notary_assisted_fee

        # Step 6: verify fee upper bound validation.
        self._set_attribute_fee_tx(
            ATTR_HIGH_PRIORITY,
            MAX_ATTRIBUTE_FEE + 1,
            expected_error=f'AttributeFee must be less than {MAX_ATTRIBUTE_FEE}',
        )

        # Step 7: verify unsupported attribute type is rejected by setter.
        self._set_attribute_fee_tx(
            INVALID_ATTRIBUTE,
            self.new_high_priority_fee,
            expected_error=f'Attribute type {INVALID_ATTRIBUTE} is not supported',
        )

    def post_test(self):
        self._set_attribute_fee_tx(ATTR_HIGH_PRIORITY, self.original_high_priority_fee)
        self._set_attribute_fee_tx(ATTR_NOTARY_ASSISTED, self.original_notary_assisted_fee)


# Run with: python3 -B -m testcases.policy.attribute_fee
if __name__ == "__main__":
    test = AttributeFee()
    test.run()
