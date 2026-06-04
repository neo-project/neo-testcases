import base64

from neo import CallFlags, UInt160, UInt256
from neo.contract import ContractParameter, ScriptBuilder, NEO_CONTRACT_HASH


def _assert_same_push(contract_parameter: ContractParameter, raw_value):
    parameter_script = ScriptBuilder().emit_push(contract_parameter).to_bytes()
    raw_script = ScriptBuilder().emit_push(raw_value).to_bytes()
    assert parameter_script == raw_script, f"{parameter_script.hex()} != {raw_script.hex()}"


def _check_scalar_parameters():
    _assert_same_push(ContractParameter("Any", None), None)
    _assert_same_push(ContractParameter("Any", 3), 3)
    _assert_same_push(ContractParameter("Boolean", True), True)
    _assert_same_push(ContractParameter("Boolean", False), False)
    _assert_same_push(ContractParameter("Boolean", "false"), False)
    _assert_same_push(ContractParameter("Integer", 17), 17)
    _assert_same_push(ContractParameter("Integer", "-17"), -17)
    _assert_same_push(ContractParameter("String", "neo"), "neo")


def _check_bytes_parameters():
    data = b"neo"
    _assert_same_push(ContractParameter("ByteArray", base64.b64encode(data).decode("utf-8")), data)
    _assert_same_push(ContractParameter("ByteArray", data), data)
    _assert_same_push(ContractParameter("Signature", base64.b64encode(data).decode("utf-8")), data)


def _check_hash_and_public_key_parameters():
    hash160 = UInt160.from_string("0x0000000000000000000000000000000000000001")
    hash256 = UInt256.from_string("0x" + "01" * 32)
    public_key = "02" + "11" * 32

    _assert_same_push(ContractParameter("Hash160", str(hash160)), hash160)
    _assert_same_push(ContractParameter("Hash256", str(hash256)), hash256)
    _assert_same_push(ContractParameter("PublicKey", public_key), bytes.fromhex(public_key))


def _check_array_parameters():
    data = b"neo"
    parameter = ContractParameter("Array", [
        ContractParameter("Integer", 1),
        ContractParameter("Boolean", True),
        ContractParameter("ByteArray", base64.b64encode(data).decode("utf-8")),
    ])
    _assert_same_push(parameter, [1, True, data])


def _check_dynamic_call_parameters():
    raw_script = ScriptBuilder().emit_dynamic_call(
        NEO_CONTRACT_HASH,
        "balanceOf",
        CallFlags.READ_STATES,
        [UInt160.from_string("0x0000000000000000000000000000000000000001")],
    ).to_bytes()
    parameter_script = ScriptBuilder().emit_dynamic_call(
        NEO_CONTRACT_HASH,
        "balanceOf",
        CallFlags.READ_STATES,
        [ContractParameter("Hash160", "0x0000000000000000000000000000000000000001")],
    ).to_bytes()
    assert parameter_script == raw_script, f"{parameter_script.hex()} != {raw_script.hex()}"


def main():
    _check_scalar_parameters()
    _check_bytes_parameters()
    _check_hash_and_public_key_parameters()
    _check_array_parameters()
    _check_dynamic_call_parameters()


if __name__ == "__main__":
    main()
