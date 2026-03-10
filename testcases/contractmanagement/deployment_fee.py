
from neo.contract import *
from testcases.testing import Testing


# Operation: this case tests the deployment fee(get/set MinimumDeploymentFee).
#  1. Only committee has permission to update the deployment fee.
#  2. The getDeploymentFee returns the current deployment fee in Datoshi.
# Expect Result: The deployment fee is working as expected.
class DeploymentFee(Testing):
    def __init__(self):
        super().__init__("DeploymentFee")
        self.default_deployment_fee = 10_00000000  # 10 GAS
        self.deployment_fee = 1_00000000  # 1 GAS

    def _get_deployment_fee(self, expected: int):
        result = self.client.invoke_function(CONTRACT_MANAGEMENT_CONTRACT_HASH, "getMinimumDeploymentFee", [])
        self.logger.info(f"getMinimumDeploymentFee result: {result}")
        self.check_stack(result['stack'], [('Integer', str(expected))])

    def _set_deployment_fee_no_permission(self, deployment_fee: int):
        result = self.client.invoke_function(CONTRACT_MANAGEMENT_CONTRACT_HASH, "setMinimumDeploymentFee",
                                             [ContractParameter(type="Integer", value=deployment_fee)])
        self.logger.info(f"setMinimumDeploymentFee result: {result}")
        assert 'exception' in result and 'Invalid committee signature' in result['exception']

    def _set_deployment_fee_negative(self):
        result = self.client.invoke_function(CONTRACT_MANAGEMENT_CONTRACT_HASH, "setMinimumDeploymentFee",
                                             [ContractParameter(type="Integer", value=-1)])
        self.logger.info(f"setMinimumDeploymentFee result: {result}")
        assert 'exception' in result and 'cannot be negative' in result['exception']

    def _set_deployment_fee(self, deployment_fee: int):
        # Step 1: create a transaction to set the deployment fee.
        block_index = self.client.get_block_index()
        script = ScriptBuilder().emit_dynamic_call(
            script_hash=CONTRACT_MANAGEMENT_CONTRACT_HASH,
            method='setMinimumDeploymentFee',
            call_flags=CallFlags.STATES,
            args=[deployment_fee],
        ).to_bytes()
        tx = self.make_multisig_tx(script, self.default_sysfee, self.default_netfee,
                                   block_index+10, is_committee=True)

        # Step 2: send the transaction to the network
        tx_hash = self.client.send_raw_tx(tx.to_array())
        tx_id = tx_hash['hash']
        self.logger.info(f"setMinimumDeploymentFee transaction sent: {tx_id}")

        # Step 3: wait for the next block
        block_index = self.client.get_block_index()
        self.wait_next_block(block_index)

        # Step 4: check the application log
        application_log = self.client.get_application_log(tx_id)
        self.logger.info(f"setMinimumDeploymentFee application log: {application_log}")
        assert 'txid' in application_log and tx_id == application_log['txid']
        assert 'executions' in application_log and len(application_log['executions']) == 1

        # Check the execution, committee has permission to update the deployment fee.
        execution = application_log['executions'][0]
        self.check_execution_result(execution, stack=[('Any', None)])

    def run_test(self):
        # Step 1: get the deployment fee
        self._get_deployment_fee(self.default_deployment_fee)

        # Step 2: set the deployment fee. Only committee has permission to update the deployment fee.
        self._set_deployment_fee_no_permission(self.deployment_fee)

        # Step 3: set the deployment fee by committee
        self._set_deployment_fee(self.deployment_fee)

        # Step 4: set the deployment fee to negative
        self._set_deployment_fee_negative()

        # Step 5: get the deployment fee again
        self._get_deployment_fee(self.deployment_fee)

    def post_test(self):
        self.logger.info("Post test: set the deployment fee to original value")
        self._set_deployment_fee(self.default_deployment_fee)
        self._get_deployment_fee(self.default_deployment_fee)


# Run with: python3 -B -m testcases.contractmanagement.deployment_fee
if __name__ == "__main__":
    test = DeploymentFee()
    test.run()
