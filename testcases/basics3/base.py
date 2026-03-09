
import base64

from neo import UInt160
from neo.contract import GAS_CONTRACT_HASH, NEO_CONTRACT_HASH
from testcases.testing import Testing


class BasicsTesting(Testing):

    def __init__(self, loggerName: str = "BasicsTesting"):
        super().__init__(loggerName)

    def _check_nep17_transfer_notification(self, notification: dict, contract_hash: str, source: UInt160 | None,
                                           dest: UInt160 | None, amount: str | None):
        assert 'contract' in notification and notification['contract'] == contract_hash, \
            f"Expected {contract_hash}, got {notification['contract']}"
        assert 'eventname' in notification and notification['eventname'] == 'Transfer', \
            f"Expected Transfer, got {notification['eventname']}"
        assert 'state' in notification, f"Expected state, got {notification}"

        state = notification['state']
        assert 'type' in state and state['type'] == 'Array', f"Expected Array, got {state['type']}"
        assert 'value' in state and len(state['value']) == 3, f"Expected 3 items in value, got {len(state['value'])}"

        # Check the state[0] is from address
        from_address = state['value'][0]
        if source is not None:
            assert 'type' in from_address and from_address['type'] == 'ByteString'
            assert 'value' in from_address and base64.b64decode(from_address['value']) == source.to_array()
        else:
            assert 'type' in from_address and from_address['type'] == 'Any', f"Expected Any, got {from_address['type']}"

        # Check the state[1] is to address
        to_address = state['value'][1]
        if dest is not None:
            assert 'type' in to_address and to_address['type'] == 'ByteString'
            assert 'value' in to_address and base64.b64decode(to_address['value']) == dest.to_array()
        else:
            assert 'type' in to_address and to_address['type'] == 'Any', f"Expected Any, got {to_address['type']}"

        # Check the state[2] is transfered amount
        transfered = state['value'][2]
        assert 'type' in transfered and transfered['type'] == 'Integer'
        assert 'value' in transfered
        if amount is not None:
            assert transfered['value'] == str(amount), f"transfered:{transfered['value']} != {amount}"

    def _check_neo_transfer_application_log(
            self, tx_id: str, application_log: dict, source: UInt160, dest: UInt160, amount: str | None):
        assert 'txid' in application_log and tx_id == application_log['txid']
        assert 'executions' in application_log and len(application_log['executions']) == 1

        # Check the execution
        execution = application_log['executions'][0]
        self.check_execution_result(execution, stack=[('Boolean', True)])

        # Check the notifications
        assert 'notifications' in execution
        # Maybe 2 or 3 notifications, because the GAS transfer to the from address and to the to address are optional.
        assert len(execution['notifications']) == 3 or len(execution['notifications']) == 2

        # Check the notifications[0] is NEO transfer
        notification = execution['notifications'][0]
        self._check_nep17_transfer_notification(notification, NEO_CONTRACT_HASH, source, dest, amount)

        # Check the notifications[1] is GAS transfer to the from address
        notification = execution['notifications'][1]
        self._check_nep17_transfer_notification(notification, GAS_CONTRACT_HASH, None, source, None)

        # Check the notifications[2] is GAS transfer to the to address
        if len(execution['notifications']) == 3:
            notification = execution['notifications'][2]  # TODO: check GAS amount
            self._check_nep17_transfer_notification(notification, GAS_CONTRACT_HASH, None, dest, None)


if __name__ == "__main__":
    test = BasicsTesting()
    test.run()
