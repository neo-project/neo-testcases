
from neo.contract import STDLIB_CONTRACT_HASH
from testcases.stdlib.base import StdLibTesting


class StringOps(StdLibTesting):

    def __init__(self):
        super().__init__("StringOps")

    def _check_string_split_with_null(self):
        # Step 1: check StringSplit(value, separator) with null value
        exception = "can't be null"
        result = self.client.invoke_function(STDLIB_CONTRACT_HASH, "stringSplit",
                                             [{'type': 'String'}, {'type': 'String', 'value': ','}])
        self.logger.info(f"Invoke 'stringSplit' with null value result: {result}")
        assert 'exception' in result and exception in result['exception']

        # Step 2: check StringSplit(value, separator) with null separator
        result = self.client.invoke_function(STDLIB_CONTRACT_HASH, "stringSplit",
                                             [{'type': 'String', 'value': 'hello,world'}, {'type': 'String'}])
        self.logger.info(f"Invoke 'stringSplit' with null separator result: {result}")
        assert 'exception' in result and exception in result['exception']

    def _check_string_len_with_null(self):
        # Step 1: check StringLen(value) with null value
        exception = "can't be null"
        result = self.client.invoke_function(STDLIB_CONTRACT_HASH, "strLen", [{'type': 'String'}])
        self.logger.info(f"Invoke 'strLen' with null value result: {result}")
        assert 'exception' in result and exception in result['exception']

    def _check_string_split_size_limit(self):
        # Step 1: check StringSplit(value, separator) with size limit
        self.check_size_limit('stringSplit', pramater_type='String', arg_2nd={'type': 'String', 'value': 'hello'})

    def run_test(self):
        # Step 1: Check string split with null
        self._check_string_split_with_null()

        # Step 2: Check string len with null
        self._check_string_len_with_null()

        # Step 3: Check string split size limit
        self._check_string_split_size_limit()

        # Step 4: Check string len size limit
        self.check_size_limit('strLen', pramater_type='String')


# Run with: python3 -B -m testcases.stdlib.string_ops
if __name__ == "__main__":
    test = StringOps()
    test.run()
