
import base64

from neo.contract import *
from testcases.testing import Testing


class LedgerTesting(Testing):
    def _hash256_to_base64(self, value: str) -> str:
        value = value[2:] if value.startswith("0x") else value
        return base64.b64encode(bytes.fromhex(value)[::-1]).decode("utf-8")

    def _uint160_to_base64(self, value) -> str:
        return base64.b64encode(value.to_array()).decode("utf-8")

    def _block_index_to_base64(self, index: int) -> str:
        length = max(1, (index.bit_length() + 7) // 8)
        return base64.b64encode(index.to_bytes(length, "little")).decode("utf-8")

    def _send_marker_tx(self, marker: int = 42) -> dict:
        start_index = self.client.get_block_index()
        script = ScriptBuilder().emit_push_int(marker).to_bytes()
        valid_until_block = start_index + 10
        sender = self.env.validators[0]
        tx = self.make_tx(sender, script, self.default_sysfee, self.default_netfee, valid_until_block)

        tx_id = self.client.send_raw_tx(tx.to_array())["hash"]
        self.logger.info(f"Ledger marker transaction sent: {tx_id}")
        self.wait_next_block(start_index, wait_while=f"waiting for marker tx {tx_id}")

        current_index = self.client.get_block_index()
        block_index, tx_index, block_hash = self._find_tx_in_blocks(tx_id, start_index + 1, current_index)

        application_log = self.client.get_application_log(tx_id)
        self.logger.info(f"Ledger marker application log: {application_log}")
        assert "txid" in application_log and application_log["txid"] == tx_id
        assert "executions" in application_log and len(application_log["executions"]) == 1
        self.check_execution_result(application_log["executions"][0], stack=[("Integer", str(marker))])

        return {
            "tx_id": tx_id,
            "tx_hash_base64": self._hash256_to_base64(tx_id),
            "block_index": block_index,
            "block_index_base64": self._block_index_to_base64(block_index),
            "block_hash": block_hash,
            "block_hash_base64": self._hash256_to_base64(block_hash),
            "tx_index": tx_index,
            "sender_base64": self._uint160_to_base64(sender.script_hash),
            "script_base64": base64.b64encode(script).decode("utf-8"),
            "valid_until_block": valid_until_block,
        }

    def _find_tx_in_blocks(self, tx_id: str, start_index: int, end_index: int) -> tuple[int, int, str]:
        for block_index in range(end_index, start_index - 1, -1):
            block = self.client.get_block(block_index, True)
            transactions = block.get("tx", [])
            for tx_index, tx in enumerate(transactions):
                tx_hash = tx.get("hash") if isinstance(tx, dict) else tx
                if tx_hash == tx_id:
                    return block_index, tx_index, block["hash"]
        raise AssertionError(f"Transaction {tx_id} was not found in blocks {start_index}..{end_index}")

    def _check_null_stack_item(self, result: dict):
        assert "exception" not in result or result["exception"] is None
        self.check_stack(result["stack"], [("Any", None)])

    def _check_null_argument_exception(self, result: dict):
        assert "exception" in result
        assert "can't be null" in result["exception"] \
            or "Object reference not set to an instance of an object" in result["exception"]

    def _check_block_stack(self, result: dict, marker: dict):
        assert "exception" not in result or result["exception"] is None
        assert len(result["stack"]) == 1 and result["stack"][0]["type"] == "Array"
        block = result["stack"][0]["value"]
        assert len(block) == 10, f"Expected trimmed block with 10 fields, got {len(block)}"
        self.check_stack(
            [block[0], block[6]],
            [
                ("ByteString", marker["block_hash_base64"]),
                ("Integer", str(marker["block_index"])),
            ],
        )
        assert block[9]["type"] == "Integer"
        assert int(block[9]["value"]) > marker["tx_index"]

    def _check_tx_stack(self, result: dict, marker: dict):
        assert "exception" not in result or result["exception"] is None
        assert len(result["stack"]) == 1 and result["stack"][0]["type"] == "Array"
        tx = result["stack"][0]["value"]
        assert len(tx) == 8, f"Expected transaction with 8 fields, got {len(tx)}"
        self.check_stack(
            [tx[0], tx[1], tx[3], tx[6], tx[7]],
            [
                ("ByteString", marker["tx_hash_base64"]),
                ("Integer", "0"),
                ("ByteString", marker["sender_base64"]),
                ("Integer", str(marker["valid_until_block"])),
                ("ByteString", marker["script_base64"]),
            ],
        )

    def _check_signers_stack(self, result: dict, marker: dict):
        assert "exception" not in result or result["exception"] is None
        assert len(result["stack"]) == 1 and result["stack"][0]["type"] == "Array"
        signers = result["stack"][0]["value"]
        assert len(signers) == 1, f"Expected one signer, got {len(signers)}"
        assert signers[0]["type"] == "Array"
        signer = signers[0]["value"]
        assert len(signer) == 5, f"Expected signer with 5 fields, got {len(signer)}"
        self.check_stack(
            [signer[0], signer[1], signer[2], signer[3], signer[4]],
            [
                ("ByteString", marker["sender_base64"]),
                ("Integer", "16"),
                ("Array", []),
                ("Array", []),
                ("Array", []),
            ],
        )

    def _check_vm_state_halt(self, result: dict):
        assert "exception" not in result or result["exception"] is None
        self.check_stack(result["stack"], [("Integer", "1")])
