
import base64

from neo.contract import NEO_CONTRACT_HASH
from testcases.testing import Testing


# Operation: this case gets the candidates from the RPC server.
# Expect Result: The candidates are as expected.
class GetCandidates(Testing):

    def __init__(self):
        super().__init__("GetCandidates")

    def _check_public_key(self, public_key: str):
        assert len(public_key) == 66, f"Expected compressed public key, got {public_key}"
        assert public_key[:2] in ('02', '03'), f"Expected compressed public key, got {public_key}"

    def _decode_contract_candidates(self, stack: list[dict]) -> list[tuple[str, str]]:
        assert len(stack) == 1 and stack[0]['type'] == 'Array'
        candidates = []
        for item in stack[0]['value']:
            assert item['type'] == 'Struct', f"Expected Struct, got {item['type']}"
            value = item['value']
            assert len(value) == 2
            assert value[0]['type'] == 'ByteString'
            assert value[1]['type'] == 'Integer'

            public_key = base64.b64decode(value[0]['value']).hex()
            self._check_public_key(public_key)
            candidates.append((public_key, value[1]['value']))
        return candidates

    def _decode_rpc_candidates(self, candidates: list[dict]) -> list[tuple[str, str]]:
        decoded = []
        for candidate in candidates:
            assert 'publickey' in candidate and 'votes' in candidate
            public_key = candidate['publickey'].lower()
            self._check_public_key(public_key)
            decoded.append((public_key, str(candidate['votes'])))
        return decoded

    def run_test(self):
        candidates1 = self.client.send("getcandidates", [])
        self.logger.info(f"RpcServer GetCandidates: {candidates1}")

        result = self.client.invoke_function(NEO_CONTRACT_HASH, "getCandidates", [])
        self.logger.info(f"Contract GetCandidates: {result}")
        assert 'exception' not in result or result['exception'] is None, f"Expected no exception, got {result}"

        rpc_candidates = self._decode_rpc_candidates(candidates1)
        contract_candidates = self._decode_contract_candidates(result['stack'])
        assert rpc_candidates == contract_candidates


# Note: This testcase must be run after the `governance.register_candidate` testcase.
# Run with: python3 -B -m testcases.plugins.rpcserver.get_candidates
if __name__ == "__main__":
    test = GetCandidates()
    test.run()
