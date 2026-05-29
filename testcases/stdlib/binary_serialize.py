
import base64

from neo.contract import STDLIB_CONTRACT_HASH
from testcases.stdlib.base import StdLibTesting


# Operation: this case tests the binarySerialize method in StdLib contract.
# Method: BinarySerialize(object data) -> byte[]
#  1. The data cannot be null, if the data is null, it will fail.
#  2. If the object is not null, but exceeds serialize limits(MaxItemSize, MaxStackSize), it will fail.
#  3. If the object contains cyclic reference, it will fail.
#  4. If the object is all OK, it will return the binary serialized bytes.
# Method: BinaryDeserialize(byte[] data) -> object
#  1. The data cannot be null, if the data is null, it will fail.
#  2. If the data is not a valid binary serialized bytes, it will fail.
#  3. If the data is not null and valid binary serialized bytes, it will return the binary deserialized object.
# Expect Result: The binarySerialize method is working as expected.
class BinarySerialize(StdLibTesting):

    def __init__(self):
        super().__init__("BinarySerialize")

    def _check_argument_null(self):
        # Step 1: check serialize with null
        self.logger.info(f"serialize null value: {base64.b64decode(b'AA==').hex()}")  # 00
        self.check_call_with_null("serialize", stack=[('ByteString', 'AA==')], exception=None)

        # Step 2: check deserialize with null
        self.check_call_with_null("deserialize", stack=[], exception="can't be null")

    def _check_round_trip(self, label: str, source: dict, expected_serialized: str, expected_stack: tuple[str, any]):
        result = self.client.invoke_function(STDLIB_CONTRACT_HASH, "serialize", [source])
        self.logger.info(f"Invoke 'serialize' with {label} result: {result}")
        assert 'exception' not in result or result['exception'] is None
        self.check_stack(result['stack'], [('ByteString', expected_serialized)])

        result = self.client.invoke_function(STDLIB_CONTRACT_HASH, "deserialize",
                                             [{'type': 'ByteArray', 'value': expected_serialized}])
        self.logger.info(f"Invoke 'deserialize' with {label} result: {result}")
        assert 'exception' not in result or result['exception'] is None
        self.check_stack(result['stack'], [expected_stack])

    def _check_normal_cases(self):
        self._check_round_trip("integer", {'type': 'Integer', 'value': 12345}, 'IQI5MA==', ('Integer', '12345'))
        self._check_round_trip("string", {'type': 'String', 'value': 'neo'}, 'KANuZW8=',
                               ('ByteString', base64.b64encode(b'neo').decode('utf-8')))
        self._check_round_trip("boolean", {'type': 'Boolean', 'value': True}, 'IAE=', ('Boolean', True))
        self._check_round_trip("array",
                               {'type': 'Array', 'value': [
                                   {'type': 'Integer', 'value': 1},
                                   {'type': 'String', 'value': 'two'},
                               ]},
                               'QAIhAQEoA3R3bw==',
                               ('Array', [
                                   {'type': 'Integer', 'value': '1'},
                                   {'type': 'ByteString', 'value': base64.b64encode(b'two').decode('utf-8')},
                               ]))

    def run_test(self):
        # Step 1: Check argument with null
        self._check_argument_null()

        # Step 2: Check normal cases
        self._check_normal_cases()


# Run with: python3 -B -m testcases.stdlib.binary_serialize
if __name__ == "__main__":
    test = BinarySerialize()
    test.run()
