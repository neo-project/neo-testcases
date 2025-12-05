#
# testcases/stdlib/itoa_atoi.py file belongs to the neo project and is free
# software distributed under the MIT software license, see the
# accompanying file LICENSE in the main directory of the
# repository or http://www.opensource.org/licenses/mit-license.php
# for more details.
#
# Redistribution and use in source and binary forms with or without
# modifications are permitted.


from testcases.stdlib.base import StdLibTesting


class ItoaAtoi(StdLibTesting):

    def __init__(self):
        super().__init__("ItoaAtoi")

    def run_test(self):
        # Step 1: check Itoa with null
        exception = 'Specified cast is not valid'  # Why 'Specified cast is not valid'?
        self.check_call_with_null("itoa", [], exception)

        # Step 2: check Atoi with null
        self.check_call_with_null("atoi", [], exception)


# Run with: python3 -B -m testcases.stdlib.itoa_atoi
if __name__ == "__main__":
    test = ItoaAtoi()
    test.run()
