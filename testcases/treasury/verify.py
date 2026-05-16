
from neo import Hardforks
from neo.contract import *
from testcases.testing import Testing


# Operation: this case tests the verify method in Treasury contract.
# Method: Verify() -> bool
#  1. Without a transaction witness, verify returns false.
#  2. With a non-committee transaction witness, verify returns false.
#  3. With the committee multisig transaction witness, verify returns true.
# Expect Result: Treasury verify is bound to the committee witness.
class TreasuryVerify(Testing):
    def __init__(self):
        super().__init__("TreasuryVerify")
        self.hardfork = Hardforks.HF_Faun

    def _verify_with_invoke(self):
        result = self.client.invoke_function(TREASURY_CONTRACT_HASH, "verify", [])
        self.logger.info(f"verify invoke result: {result}")
        assert "exception" not in result or result["exception"] is None
        self.check_stack(result["stack"], [("Boolean", False)])

    def _make_verify_script(self) -> bytes:
        return ScriptBuilder().emit_dynamic_call(
            script_hash=TREASURY_CONTRACT_HASH,
            method="verify",
            call_flags=CallFlags.NONE,
            args=[],
        ).to_bytes()

    def _send_verify_tx(self, committee: bool) -> str:
        block_index = self.client.get_block_index()
        script = self._make_verify_script()
        if committee:
            tx = self.make_multisig_tx(script, self.default_sysfee, self.default_netfee,
                                       block_index + 10, is_committee=True)
        else:
            tx = self.make_tx(self.env.others[0], script, self.default_sysfee, self.default_netfee, block_index + 10)

        tx_id = self.client.send_raw_tx(tx.to_array())["hash"]
        self.logger.info(f"Treasury verify transaction sent: {tx_id}")
        self.wait_next_block(block_index, wait_while=f"waiting for Treasury verify tx {tx_id}")
        return tx_id

    def _check_verify_tx(self, committee: bool, expected: bool):
        tx_id = self._send_verify_tx(committee)
        application_log = self.client.get_application_log(tx_id)
        self.logger.info(f"Treasury verify application log: {application_log}")
        assert "txid" in application_log and application_log["txid"] == tx_id
        assert "executions" in application_log and len(application_log["executions"]) == 1
        execution = application_log["executions"][0]
        self.check_execution_result(execution, stack=[("Boolean", expected)])

    def run_test(self):
        self._verify_with_invoke()
        self._check_verify_tx(committee=False, expected=False)
        self._check_verify_tx(committee=True, expected=True)


# Run with: python3 -B -m testcases.treasury.verify
if __name__ == "__main__":
    test = TreasuryVerify()
    test.run()
