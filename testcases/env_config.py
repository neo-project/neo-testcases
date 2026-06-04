from env import Env


def _config(neo4_enable=None):
    data = {
        "rpc_endpoint": "127.0.0.1:10332",
        "network": 1234567890,
        "hardforks": {
            "HF_Aspidochelone": 1,
            "HF_Basilisk": 1,
            "HF_Cockatrice": 1,
            "HF_Domovoi": 1,
            "HF_Echidna": 1,
            "HF_Faun": 1,
        },
        "validators": [],
        "others": [],
    }
    if neo4_enable is not None:
        data["neo4_enable"] = neo4_enable
    return data


def _check_from_dict_reads_neo4_enable():
    assert Env.from_dict(_config(True)).neo4_enable is True
    assert Env.from_dict(_config(False)).neo4_enable is False
    assert Env.from_dict(_config()).neo4_enable is False


def _check_as_dict_keeps_neo4_enable():
    env = Env.from_dict(_config(True))
    data = env.as_dict()
    assert data["neo4_enable"] is True
    assert Env.from_dict(data).neo4_enable is True


def main():
    _check_from_dict_reads_neo4_enable()
    _check_as_dict_keeps_neo4_enable()


if __name__ == "__main__":
    main()
