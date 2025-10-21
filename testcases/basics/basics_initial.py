# Copyright (C) 2015-2025 The Neo Project.
#
# testcases/basics/basics_initial.py file belongs to the neo project and is free
# software distributed under the MIT software license, see the
# accompanying file LICENSE in the main directory of the
# repository or http://www.opensource.org/licenses/mit-license.php
# for more details.
#
# Redistribution and use in source and binary forms with or without
# modifications are permitted.

from testcases.basics.gas_rpc_transfer_multisig import GasRpcTransferMultiSign
from testcases.basics.neo_rpc_transfer_multisig import NeoRpcTransferMultiSign
from testcases.basics.base import BasicsTesting


# Operation: this case initializes the NEO and GAS balance of the others[0] account.
# Expect Result: The NEO and GAS balance of the others[0] account are initialized as expected.
class BasicsInitial(BasicsTesting):

    def __init__(self):
        super().__init__(__class__.__name__)

    def run_test(self):
        neo_initial = NeoRpcTransferMultiSign()
        neo_initial.run()

        gas_initial = GasRpcTransferMultiSign()
        gas_initial.run()


# Run with: python3 -B -m testcases.basics.basics_initial
if __name__ == "__main__":
    test = BasicsInitial()
    test.run()
