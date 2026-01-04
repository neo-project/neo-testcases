
from neo3.contracts.callflags import CallFlags
from neo3.contracts.contract import CONTRACT_HASHES
from neo3.contracts.utils import create_signature_redeemscript, create_multisig_redeemscript
from neo3.core.cryptography.ecc import ECPoint
from neo3.core.serialization import BinaryWriter
from neo3.core.types import UInt160, UInt256
from neo3.core.utils import to_script_hash
from neo3.network.payloads.transaction import Transaction
from neo3.network.payloads.verification import Signer, Witness, WitnessScope
from neo3.wallet.account import Account
from neo3.vm import OpCode


class Hardforks:
    HF_Aspidochelone = "HF_Aspidochelone"
    HF_Basilisk = "HF_Basilisk"
    HF_Cockatrice = "HF_Cockatrice"
    HF_Domovoi = "HF_Domovoi"
    HF_Echidna = "HF_Echidna"
    HF_Faun = "HF_Faun"
    HHF_Gorgon = "HF_Gorgon"

class NamedCurveHash:
    SECP256K1_SHA256 = 22
    SECP256R1_SHA256 = 23
    SECP256K1_KECCAK256 = 122
    SECP256R1_KECCAK256 = 123
