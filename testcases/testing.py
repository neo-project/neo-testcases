# Copyright (C) 2015-2025 The Neo Project.
#
# testcases/testing.py file belongs to the neo project and is free
# software distributed under the MIT software license, see the
# accompanying file LICENSE in the main directory of the
# repository or http://www.opensource.org/licenses/mit-license.php
# for more details.
#
# Redistribution and use in source and binary forms with or without
# modifications are permitted.

import hashlib
import random
import logging
import time

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
from cryptography.hazmat.backends import default_backend

from neo import *
from neo.contract import ScriptBuilder
from neo.rpc import RpcClient
from env import Env

logging.basicConfig(level=logging.INFO)

TX_VERSION_V0 = 0


class Testing:

    def __init__(self, loggerName: str = "Testing"):
        self.env = Env.from_testbed()
        self.client = RpcClient(self.env.rpc_endpoint)
        self.logger = logging.getLogger(loggerName)
        self.default_sysfee = 1_0000000  # 0.1 GAS
        self.default_netfee = 1_0000000  # 0.1 GAS

    def wait_next_block(self, current_block_index: int, wait_while: str = '', max_wait_seconds: int = 5*60):
        start_time = time.time()
        while True:
            block_index = self.client.get_block_index()
            if block_index > current_block_index:
                break
            if time.time() - start_time > max_wait_seconds:
                raise TimeoutError(f"Timeout waiting for next block of {current_block_index} after {max_wait_seconds}s")
            time.sleep(2)

            elapsed = time.time() - start_time
            self.logger.info(f"Waiting {elapsed:.2f}s for next block of {current_block_index} while {wait_while}")

        elapsed = time.time() - start_time
        self.logger.info(f"Waited {elapsed:.2f}s for next block of {current_block_index} while {wait_while}")
        return block_index

    def bft_address(self) -> UInt160:
        m = len(self.env.validators) - (len(self.env.validators) - 1) // 3
        script = create_multisig_redeemscript(m, [v.public_key for v in self.env.validators])
        return to_script_hash(script)

    def sign(self, private_key: int | bytes, data: bytes) -> bytes:
        private_key = int.from_bytes(private_key, 'big') if isinstance(private_key, bytes) else private_key
        sign_data = self.env.network.to_bytes(4, 'little') + hashlib.sha256(data).digest()
        sk = ec.derive_private_key(private_key, ec.SECP256R1(), default_backend())
        der = sk.sign(sign_data, ec.ECDSA(hashes.SHA256()))
        (r, s) = decode_dss_signature(der)
        return r.to_bytes(32, 'big') + s.to_bytes(32, 'big')

    def make_witness(self, sign: bytes, public_key: ECPoint) -> Witness:
        return Witness(
            invocation_script=ScriptBuilder().emit_push_bytes(sign).to_bytes(),
            verification_script=create_signature_redeemscript(public_key)
        )

    def make_multisig_witness(self, key_sign_pairs: list[tuple[ECPoint, bytes]]) -> Witness:
        key_sign_pairs.sort(key=lambda x: x[0])
        m = len(key_sign_pairs) - (len(key_sign_pairs) - 1) // 3
        invocation = ScriptBuilder()
        for i in range(m):  # Must be len(keys) - (len(keys) - 1) // 3
            invocation.emit_push_bytes(key_sign_pairs[i][1])
        return Witness(
            invocation_script=invocation.to_bytes(),
            verification_script=create_multisig_redeemscript(m, [k for (k, _) in key_sign_pairs])
        )

    def make_tx(self, account: Account, script: bytes, sysfee: int, netfee: int, valid_until_block: int):
        tx = Transaction(
            version=TX_VERSION_V0,
            nonce=random.randint(0, 0xFFFFFFFF),
            system_fee=sysfee,
            network_fee=netfee,
            valid_until_block=valid_until_block,
            signers=[Signer(account=account.script_hash, scope=WitnessScope.CALLED_BY_ENTRY)],
            attributes=[],
            script=script,
            witnesses=[],
            protocol_magic=self.env.network,
        )

        with BinaryWriter() as writer:
            tx.serialize_unsigned(writer)
            raw_tx = writer.to_array()
        sign = self.sign(account.private_key, raw_tx)
        tx.witnesses = [self.make_witness(sign, account.public_key)]
        return tx

    def make_multisig_tx(self, script: bytes, sysfee: int, netfee: int, valid_until_block: int):
        account = self.bft_address()
        tx = Transaction(
            version=TX_VERSION_V0,
            nonce=random.randint(0, 0xFFFFFFFF),
            system_fee=sysfee,
            network_fee=netfee,
            valid_until_block=valid_until_block,
            signers=[Signer(account=account, scope=WitnessScope.CALLED_BY_ENTRY)],
            attributes=[],
            script=script,
            witnesses=[],
            protocol_magic=self.env.network,
        )

        with BinaryWriter() as writer:
            tx.serialize_unsigned(writer)
            raw_tx = writer.to_array()
        pairs = [(v.public_key, self.sign(int.from_bytes(v.private_key, 'big'), raw_tx)) for v in self.env.validators]
        tx.witnesses = [self.make_multisig_witness(pairs)]
        return tx

    def run(self):
        # Step 0: wait for creating block 1.
        block_index = self.wait_next_block(1)
        self.logger.info(f"Current block index: {block_index}")

        self.pre_test()
        try:
            self.run_test()
        finally:
            self.post_test()

    def pre_test(self):
        pass

    def run_test(self):
        pass

    def post_test(self):
        pass
