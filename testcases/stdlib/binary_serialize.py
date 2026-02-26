
import base64
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
        exception = "can't be null"
        self.check_call_with_null("deserialize", stack=[], exception=exception)

    def run_test(self):
        # Step 1: Check argument with null
        self._check_argument_null()

        # TODO: check normal cases


# Run with: python3 -B -m testcases.stdlib.binary_serialize
if __name__ == "__main__":
    test = BinarySerialize()
    test.run()
