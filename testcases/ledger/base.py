import base64

from neo import OpCode, UInt256
from testcases.testing import Testing


class LedgerTesting(Testing):
    def __init__(self, logger_name: str):
        super().__init__(logger_name)

    def _to_base64(self, data: bytes) -> str:
        return base64.b64encode(data).decode("utf-8")

    def _encode_uint256_param(self, value: str) -> dict:
        return {'type': 'ByteArray', 'value': self._to_base64(UInt256.from_string(value).to_array())}

    def _encode_block_index(self, block_index: int) -> str:
        if block_index < 0:
            raise ValueError(f"Invalid block index: {block_index}")
        # NeoVM converts byte[] to BigInteger (signed little-endian), so keep it positive.
        size = max(1, (block_index.bit_length() + 7) // 8)
        raw = block_index.to_bytes(size, 'little', signed=False)
        if raw[-1] & 0x80:
            raw += b'\x00'
        return self._to_base64(raw)

    def _find_tx_in_recent_blocks(self, tx_id: str, max_backtrack: int = 30):
        latest = self.client.get_block_index()
        min_index = max(0, latest - max_backtrack)
        for block_index in range(latest, min_index - 1, -1):
            block = self.client.get_block(block_index, verbose=True)
            txs = block.get('tx', block.get('transactions', []))
            for tx_index, tx in enumerate(txs):
                hash_value = tx.get('hash') if isinstance(tx, dict) else tx
                if hash_value == tx_id:
                    return block_index, block['hash'], tx_index
        raise AssertionError(f"Cannot find tx {tx_id} in latest {max_backtrack} blocks")

    def submit_confirmed_tx(self) -> dict:
        sender = self.env.others[0]
        script = bytes([OpCode.RET.value])

        start_block_index = self.client.get_block_index()
        tx = self.make_tx(sender, script, self.default_sysfee, self.default_netfee, start_block_index + 10)
        tx_rsp = self.client.send_raw_tx(tx.to_array())
        assert isinstance(tx_rsp, dict) and 'hash' in tx_rsp, f"Unexpected sendrawtransaction response: {tx_rsp}"

        tx_id = tx_rsp['hash']
        self.logger.info(f"Transaction sent: {tx_id}")

        # Wait until the transaction is persisted in a block.
        block_index = start_block_index
        block_hash = None
        tx_index = None
        for _ in range(10):
            block_index = self.wait_next_block(block_index, wait_while=f"persisting tx {tx_id}")
            try:
                block_index, block_hash, tx_index = self._find_tx_in_recent_blocks(tx_id)
                break
            except AssertionError:
                continue

        assert block_hash is not None and tx_index is not None, f"Transaction not persisted: {tx_id}"
        return {
            'tx': tx,
            'tx_id': tx_id,
            'sender': sender,
            'tx_hash_b64': self._to_base64(UInt256.from_string(tx_id).to_array()),
            'sender_b64': self._to_base64(sender.script_hash.to_array()),
            'script_b64': self._to_base64(script),
            'block_index': block_index,
            'block_index_b64': self._encode_block_index(block_index),
            'block_hash': block_hash,
            'block_hash_b64': self._to_base64(UInt256.from_string(block_hash).to_array()),
            'tx_index': tx_index,
        }
