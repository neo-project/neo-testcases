# Copyright (C) 2015-2025 The Neo Project.
#
# env.py file belongs to the neo project and is free
# software distributed under the MIT software license, see the
# accompanying file LICENSE in the main directory of the
# repository or http://www.opensource.org/licenses/mit-license.php
# for more details.
#
# Redistribution and use in source and binary forms with or without
# modifications are permitted.

import json
import os
from typing import Self

from dataclasses import asdict, dataclass, field
from dataclasses_json import dataclass_json

from neo import Account


# Hardfork config, all hardforks are enabled in default.
@dataclass_json
@dataclass
class Hardfork:
    HF_Aspidochelone: int = 1
    HF_Basilisk: int = 1
    HF_Cockatrice: int = 1
    HF_Domovoi: int = 1
    HF_Echidna: int = 1
    HF_Faun: int = 1


# It contains the environment variables for the tests.
# If run the tests on the different environment, the default values should be overridden.
# For testing, the RpcServer, DBFT and ApplicationLog plugins must be installed.
@dataclass
class Env:
    # The RpcServer plugin endpoint, the default value is localnet endpoint
    rpc_endpoint: str = "127.0.0.1:10332"

    # The default value is localnet testing network id
    network: int = 1234567890

    # The hardforks, the default value from localnet testing network
    hardforks: Hardfork = field(default_factory=Hardfork)

    # The accounts of the validators. Add hex-encoded private key to the testbed to declare a validator.
    # The validators should be 7 accounts.
    validators: list[Account] = field(default_factory=list)

    # Other accounts for testing. Add hex-encoded private key to the testbed json file to add a new account.
    # The others should be at least 3 accounts.
    others: list[Account] = field(default_factory=list)

    # Whether to enable neo4 features
    neo4_enable: bool = False

    def is_hardfork_enabled(self, hardfork: str, block_index: int) -> bool:
        return hasattr(self.hardforks, hardfork) and getattr(self.hardforks, hardfork) >= block_index

    def as_dict(self) -> dict:
        return {
            "rpc_endpoint": self.rpc_endpoint,
            "network": self.network,
            "hardforks": asdict(self.hardforks),
            "validators": ['0x' + v.private_key[::-1].to_hex() for v in self.validators],
            "others": ['0x' + o.private_key[::-1].to_hex() for o in self.others]
        }

    @classmethod
    def from_testbed(cls, testbed: str = os.getenv('NEO_TESTBED', 'testbed/localnet.json')) -> Self:
        with open(testbed, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        return cls(
            rpc_endpoint=data['rpc_endpoint'],
            network=data['network'],
            hardforks=data['hardforks'] if isinstance(data['hardforks'], Hardfork) else Hardfork(**data['hardforks']),
            validators=[Account(private_key=int(v, 16).to_bytes(32, 'big')) for v in data['validators']],
            others=[Account(private_key=int(o, 16).to_bytes(32, 'big')) for o in data['others']]
        )
