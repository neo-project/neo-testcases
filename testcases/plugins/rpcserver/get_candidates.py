
import base64

from neo.contract import NEO_CONTRACT_HASH
from testcases.testing import Testing


# Operation: this case gets the candidates from the RPC server.
# Expect Result: The candidates are as expected.
class GetCandidates(Testing):

    def __init__(self):
        super().__init__("GetCandidates")

    def run_test(self):
        candidates1 = self.client.send("getcandidates", [])
        self.logger.info(f"RpcServer GetCandidates: {candidates1}")

        result = self.client.invoke_function(NEO_CONTRACT_HASH, "getCandidates", [])
        self.logger.info(f"Contract GetCandidates: {result}")

        stack = result['stack']
        assert len(stack) == 1 and stack[0]['type'] == 'Array'

        candidates2 = stack[0]['value']
        assert len(candidates1) == len(candidates2)

        for i in range(len(candidates1)):
            assert candidates2[i]['type'] == 'Struct'
            value = candidates2[i]['value']
            assert len(value) == 2
            assert value[0]['type'] == 'ByteString'
            assert value[1]['type'] == 'Integer'

            public_key = base64.b64decode(value[0]['value']).hex()
            assert public_key == candidates1[i]['publickey']
            assert value[1]['value'] == candidates1[i]['votes']


# Note: This testcase must be run after the `governance.register_candidate` testcase.
# Run with: python3 -B -m testcases.plugins.rpcserver.get_candidates
if __name__ == "__main__":
    test = GetCandidates()
    test.run()
