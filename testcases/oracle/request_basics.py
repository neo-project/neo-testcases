
from neo.contract import *
from testcases.testing import Testing


# Operation: this case tests the Request in Oracle contract.
# 1. method: void Request(string url, string filter, string callback, object userData, long gasForResponse);
# 2. send an async task to the oracle contract, and the task will be executed by oracle nodes.
#  2.1. The 'url' is null or length exceeds MaxUrlLength(the default value is 256 bytes).
#  2.2. The 'filter' length exceeds MaxFilterLength(the default value is 128 bytes).
#  2.3. The 'callback' is null or length exceeds MaxCallbackLength(the default value is 32 bytes) or starts with '_'.
#  2.4. The 'userData' length exceeds MaxUserDataLength(the default value is 512 bytes).
#  2.5. The 'gasForResponse' is less than 0.1 GAS.
#  2.6. Too many pending responses for the specified URL.
#  2.7. The calling source(CallingScriptHash) is not a contract.
class OracleRequestBasics(Testing):

    def __init__(self):
        super().__init__("OracleRequestBasics")
        self.min_gas_for_response = 1_000_0000  # 0.1 GAS
        self.test_url = "https://not-found-domain-url.xyz"
        self.url_max_size = 256
        self.filter_max_size = 128
        self.callback_max_size = 32
        self.userdata_max_size = 512

    def _request_url_null(self):
        result = self.client.invoke_function(ORACLE_CONTRACT_HASH, "request",
                                             [ContractParameter(type="String", value=None),
                                              ContractParameter(type="String", value=""),
                                              ContractParameter(type="String", value="callback"),
                                              ContractParameter(type="Any", value=None),
                                              ContractParameter(type="Integer", value=self.min_gas_for_response)])
        self.logger.info(f"Request result: {result}")
        assert 'exception' in result and "can't be null" in result['exception']

    def _request_url_exceeds_max_size(self):
        result = self.client.invoke_function(ORACLE_CONTRACT_HASH, "request",
                                             [ContractParameter(type="String", value="a" * (self.url_max_size + 1)),
                                              ContractParameter(type="String", value=""),
                                              ContractParameter(type="String", value="callback"),
                                              ContractParameter(type="Any", value=None),
                                              ContractParameter(type="Integer", value=self.min_gas_for_response)])
        self.logger.info(f"Request result: {result}")
        assert 'exception' in result and 'URL size' in result['exception'] \
            and "exceeds maximum allowed size" in result['exception']

    def _request_filter_exceeds_max_size(self):
        result = self.client.invoke_function(ORACLE_CONTRACT_HASH, "request",
                                             [ContractParameter(type="String", value=self.test_url),
                                              ContractParameter(type="String", value="a" * (self.filter_max_size + 1)),
                                              ContractParameter(type="String", value="callback"),
                                              ContractParameter(type="Any", value=None),
                                              ContractParameter(type="Integer", value=self.min_gas_for_response)])
        self.logger.info(f"Request result: {result}")
        assert 'exception' in result and 'Filter size' in result['exception'] \
            and "exceeds maximum allowed size" in result['exception']

    def _request_callback_null(self):
        result = self.client.invoke_function(ORACLE_CONTRACT_HASH, "request",
                                             [ContractParameter(type="String", value=self.test_url),
                                              ContractParameter(type="String", value=""),
                                              ContractParameter(type="String", value=None),
                                              ContractParameter(type="Any", value=None),
                                              ContractParameter(type="Integer", value=self.min_gas_for_response)])
        self.logger.info(f"Request result: {result}")
        assert 'exception' in result and "can't be null" in result['exception']

    def _request_callback_exceeds_max_size(self):
        long_callback = "a" * (self.callback_max_size + 1)
        result = self.client.invoke_function(ORACLE_CONTRACT_HASH, "request",
                                             [ContractParameter(type="String", value=self.test_url),
                                              ContractParameter(type="String", value=""),
                                              ContractParameter(type="String", value=long_callback),
                                              ContractParameter(type="Any", value=None),
                                              ContractParameter(type="Integer", value=self.min_gas_for_response)])
        self.logger.info(f"Request result: {result}")
        assert 'exception' in result and 'Callback size' in result['exception'] \
            and "exceeds maximum allowed size" in result['exception']

    def _request_callback_starts_with_underscore(self):
        result = self.client.invoke_function(ORACLE_CONTRACT_HASH, "request",
                                             [ContractParameter(type="String", value=self.test_url),
                                              ContractParameter(type="String", value=""),
                                              ContractParameter(type="String", value="_callback"),
                                              ContractParameter(type="Any", value=None),
                                              ContractParameter(type="Integer", value=self.min_gas_for_response)])
        self.logger.info(f"Request result: {result}")
        assert 'exception' in result and "Callback cannot start with underscore" in result['exception']

    def _request_userdata_null(self):
        result = self.client.invoke_function(ORACLE_CONTRACT_HASH, "request",
                                             [ContractParameter(type="String", value=self.test_url),
                                              ContractParameter(type="String", value=""),
                                              ContractParameter(type="String", value="callback"),
                                              ContractParameter(type="Any", value=None),
                                              ContractParameter(type="Integer", value=self.min_gas_for_response)])
        self.logger.info(f"Request result: {result}")
        # Only contract can call `request` method, so the exception is "Operation is not valid".
        # TODO: test contract call this method.
        assert 'exception' in result and "Operation is not valid" in result['exception']

    def _request_userdata_exceeds_max_size(self):
        long_userdata = "a" * (self.userdata_max_size + 1)
        result = self.client.invoke_function(ORACLE_CONTRACT_HASH, "request",
                                             [ContractParameter(type="String", value=self.test_url),
                                              ContractParameter(type="String", value=""),
                                              ContractParameter(type="String", value="callback"),
                                              ContractParameter(type="String", value=long_userdata),
                                              ContractParameter(type="Integer", value=self.min_gas_for_response)])
        self.logger.info(f"Request result: {result}")
        # Only contract can call `request` method, so the exception is "Operation is not valid".
        # TODO: test contract call this method.
        assert 'exception' in result and "Operation is not valid" in result['exception']

    def _request_gas_for_response_null(self):
        result = self.client.invoke_function(ORACLE_CONTRACT_HASH, "request",
                                             [ContractParameter(type="String", value=self.test_url),
                                              ContractParameter(type="String", value=""),
                                              ContractParameter(type="String", value="callback"),
                                              ContractParameter(type="Any", value=None),
                                              ContractParameter(type="Integer", value=None)])
        self.logger.info(f"Request result: {result}")
        assert 'exception' in result and "can't be null" in result['exception']

    def _request_gas_for_response_too_small(self):
        result = self.client.invoke_function(ORACLE_CONTRACT_HASH, "request",
                                             [ContractParameter(type="String", value=self.test_url),
                                              ContractParameter(type="String", value=""),
                                              ContractParameter(type="String", value="callback"),
                                              ContractParameter(type="Any", value=None),
                                              ContractParameter(type="Integer", value=self.min_gas_for_response - 1)])
        self.logger.info(f"Request result: {result}")
        assert 'exception' in result and "must be at least" in result['exception']  # TODO: fix exception message

    def run_test(self):
        # Step 1: request with null url
        self._request_url_null()

        # Step 2: request with null callback
        self._request_callback_null()

        # Step 3: request with callback starts with underscore
        self._request_callback_starts_with_underscore()

        # Step 4: request with null userdata
        self._request_userdata_null()  # userdata is nullable

        # Step 5: request with gas for response null
        self._request_gas_for_response_null()

        # Step 6: request with gas for response less than 0.1 GAS
        self._request_gas_for_response_too_small()

        # Step 7: request with url length exceeds max size
        self._request_url_exceeds_max_size()

        # Step 8: request with filter length exceeds max size
        self._request_filter_exceeds_max_size()

        # Step 9: request with callback length exceeds max size
        self._request_callback_exceeds_max_size()

        # Step 10: request with userdata length exceeds max size
        self._request_userdata_exceeds_max_size()


# Run with: python3 -B -m testcases.oracle.request_basics
if __name__ == "__main__":
    test = OracleRequestBasics()
    test.run()
