
import base64

from neo.contract import STDLIB_CONTRACT_HASH
from testcases.stdlib.base import StdLibTesting


class JsonSerialize(StdLibTesting):

    def __init__(self):
        super().__init__("JsonSerialize")

    def _check_argument_null(self):
        # Step 1: check jsonSerialize with 'null' string
        value = base64.b64encode(b'null').decode('utf-8')
        self.check_call_with_null("jsonSerialize", stack=[('ByteString', value)], exception=None)

        # Step 2: check jsonDeserialize with null value
        self.check_call_with_null("jsonDeserialize", stack=[], exception="can't be null")

    def _check_round_trip(self, label: str, source: dict, expected_json: bytes, expected_stack: tuple[str, any]):
        expected_serialized = base64.b64encode(expected_json).decode('utf-8')

        result = self.client.invoke_function(STDLIB_CONTRACT_HASH, "jsonSerialize", [source])
        self.logger.info(f"Invoke 'jsonSerialize' with {label} result: {result}")
        assert 'exception' not in result or result['exception'] is None
        self.check_stack(result['stack'], [('ByteString', expected_serialized)])

        result = self.client.invoke_function(STDLIB_CONTRACT_HASH, "jsonDeserialize",
                                             [{'type': 'ByteArray', 'value': expected_serialized}])
        self.logger.info(f"Invoke 'jsonDeserialize' with {label} result: {result}")
        assert 'exception' not in result or result['exception'] is None
        self.check_stack(result['stack'], [expected_stack])

    def _check_normal_cases(self):
        self._check_round_trip("integer", {'type': 'Integer', 'value': 12345}, b'12345', ('Integer', '12345'))
        self._check_round_trip("string", {'type': 'String', 'value': 'neo'}, b'"neo"',
                               ('ByteString', base64.b64encode(b'neo').decode('utf-8')))
        self._check_round_trip("boolean", {'type': 'Boolean', 'value': True}, b'true', ('Boolean', True))
        self._check_round_trip("array",
                               {'type': 'Array', 'value': [
                                   {'type': 'Integer', 'value': 1},
                                   {'type': 'String', 'value': 'two'},
                               ]},
                               b'[1,"two"]',
                               ('Array', [
                                   {'type': 'Integer', 'value': '1'},
                                   {'type': 'ByteString', 'value': base64.b64encode(b'two').decode('utf-8')},
                               ]))

    def run_test(self):
        # Step 1: Check jsonSerialize and jsonDeserialize with null
        self._check_argument_null()

        # Step 2: Check normal cases
        self._check_normal_cases()


# Run with: python3 -B -m testcases.stdlib.json_serialize
if __name__ == "__main__":
    test = JsonSerialize()
    test.run()
