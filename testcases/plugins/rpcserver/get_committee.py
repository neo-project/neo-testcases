import base64

from neo.contract import NEO_CONTRACT_HASH
from testcases.testing import Testing


# Operation: this case compares committee views exposed by RpcServer and NEO native contract.
# Expect Result: RpcServer committee output is consistent with NEO.getCommittee, and validators are well-formed.
class GetCommittee(Testing):

    def __init__(self):
        super().__init__("GetCommittee")

    def _decode_public_key(self, item: dict) -> str:
        assert item['type'] == 'ByteString', f"Expected ByteString, got {item['type']}"
        public_key = base64.b64decode(item['value']).hex()
        assert len(public_key) == 66, f"Expected compressed public key, got {public_key}"
        assert public_key[:2] in ('02', '03'), f"Expected compressed public key, got {public_key}"
        return public_key

    def _invoke_public_key_array(self, method: str) -> list[str]:
        result = self.client.invoke_function(NEO_CONTRACT_HASH, method, [])
        self.logger.info(f"Contract {method}: {result}")
        assert 'exception' not in result or result['exception'] is None, f"Expected no exception, got {result}"

        stack = result['stack']
        assert len(stack) == 1 and stack[0]['type'] == 'Array'
        return [self._decode_public_key(item) for item in stack[0]['value']]

    def _check_rpc_committee(self, expected: list[str]):
        committee = self.client.get_committee()
        self.logger.info(f"RpcServer getcommittee: {committee}")
        assert [item.lower() for item in committee] == expected

    def run_test(self):
        committee = self._invoke_public_key_array("getCommittee")
        assert len(committee) > 0
        assert committee == sorted(committee)
        self._check_rpc_committee(committee)

        validators = self._invoke_public_key_array("getNextBlockValidators")
        assert len(validators) > 0
        assert validators == sorted(validators)
        assert set(validators).issubset(set(committee))


# Run with: python3 -B -m testcases.plugins.rpcserver.get_committee
if __name__ == "__main__":
    test = GetCommittee()
    test.run()
