
import base64

from neo.contract import STDLIB_CONTRACT_HASH
from testcases.stdlib.base import StdLibTesting


class MemoryOps(StdLibTesting):

    def __init__(self):
        super().__init__("MemoryOps")

    def _check_memory_compare_with_null(self):
        # Step 1: check MemoryCompare(value1, value2) with null value1
        exception = "can't be null"
        value2 = base64.b64encode(b'hello').decode('utf-8')
        result = self.client.invoke_function(STDLIB_CONTRACT_HASH, "memoryCompare",
                                             [{'type': 'ByteArray'}, {'type': 'ByteArray', 'value': value2}])
        self.logger.info(f"Invoke 'memoryCompare' with null value1 result: {result}")
        assert 'exception' in result and exception in result['exception']

        # Step 2: check MemoryCompare(value1, value2) with null value2
        value1 = base64.b64encode(b'hello').decode('utf-8')
        result = self.client.invoke_function(STDLIB_CONTRACT_HASH, "memoryCompare",
                                             [{'type': 'ByteArray', 'value': value1}, {'type': 'ByteArray'}])
        self.logger.info(f"Invoke 'memoryCompare' with null value2 result: {result}")
        assert 'exception' in result and exception in result['exception']

    def _check_memory_search_with_null(self):
        # Step 1: check MemorySearch(value, pattern) with null value
        exception = "can't be null"
        pattern = base64.b64encode(b'hello').decode('utf-8')
        result = self.client.invoke_function(STDLIB_CONTRACT_HASH, "memorySearch",
                                             [{'type': 'ByteArray'}, {'type': 'ByteArray', 'value': pattern}])
        self.logger.info(f"Invoke 'memorySearch' with null value result: {result}")
        assert 'exception' in result and exception in result['exception']

        # Step 2: check MemorySearch(value, pattern) with null pattern
        value = base64.b64encode(b'hello').decode('utf-8')
        result = self.client.invoke_function(STDLIB_CONTRACT_HASH, "memorySearch",
                                             [{'type': 'ByteArray', 'value': value}, {'type': 'ByteArray'}])
        self.logger.info(f"Invoke 'memorySearch' with null pattern result: {result}")
        assert 'exception' in result and exception in result['exception']

    def _check_memory_compare_size_limit(self):
        data = base64.b64encode(b'01234').decode('utf-8')
        # Step 1: check MemoryCompare(value1, value2) with size limit
        self.check_size_limit('memoryCompare', pramater_type='ByteArray', arg_2nd={'type': 'ByteArray', 'value': data})

        # Step 2: check MemoryCompare(value1, value2) with size limit
        invalid = base64.b64encode(b'0' * (self.max_size_limit + 1)).decode('utf-8')
        result = self.client.invoke_function(STDLIB_CONTRACT_HASH, 'memoryCompare',
                                             [{'type': 'ByteArray', 'value': data},
                                              {'type': 'ByteArray', 'value': invalid}])
        self.logger.info(f"Invoke 'memoryCompare' with size limit result: {result}")
        assert 'exception' in result and 'The input exceeds the maximum length' in result['exception']

    def _check_memory_search_size_limit(self):
        data = base64.b64encode(b'01234').decode('utf-8')
        # Step 1: check MemorySearch(value, pattern) with size limit
        self.check_size_limit('memorySearch', pramater_type='ByteArray', arg_2nd={'type': 'ByteArray', 'value': data})

        # Step 2: check MemorySearch(value, pattern) with size limit
        invalid = base64.b64encode(b'0' * (self.max_size_limit + 1)).decode('utf-8')
        result = self.client.invoke_function(STDLIB_CONTRACT_HASH, 'memorySearch',
                                             [{'type': 'ByteArray', 'value': data},
                                              {'type': 'ByteArray', 'value': invalid}])
        self.logger.info(f"Invoke 'memorySearch' with size limit result: {result}")
        assert 'exception' not in result or result['exception'] is None
        assert result['stack'][0]['type'] == 'Integer' and result['stack'][0]['value'] == '-1'

    def run_test(self):
        # Step 1: Check memory compare with null
        self._check_memory_compare_with_null()

        # Step 2: Check memory search with null
        self._check_memory_search_with_null()

        # Step 3: Check 'memoryCompare' size limit
        self._check_memory_compare_size_limit()

        # Step 4: Check 'memorySearch' size limit
        self._check_memory_search_size_limit()


# Run with: python3 -B -m testcases.stdlib.memory_ops
if __name__ == "__main__":
    test = MemoryOps()
    test.run()
