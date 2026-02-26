
import base64

from testcases.stdlib.base import StdLibTesting


class JsonSerialize(StdLibTesting):

    def __init__(self):
        super().__init__("JsonSerialize")

    def _check_argument_null(self):
        # Step 1: check jsonSerialize with 'null' string
        value = base64.b64encode(b'null').decode('utf-8')
        self.check_call_with_null("jsonSerialize", stack=[('ByteString', value)], exception=None)

        # Step 2: check jsonDeserialize with null value
        exception = "can't be null"
        self.check_call_with_null("jsonDeserialize", stack=[], exception=exception)

    def run_test(self):
        # Step 1: Check jsonSerialize and jsonDeserialize with null
        self._check_argument_null()

        # TODO: check normal cases


# Run with: python3 -B -m testcases.stdlib.json_serialize
if __name__ == "__main__":
    test = JsonSerialize()
    test.run()
