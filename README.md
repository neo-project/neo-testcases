# neo-testcases
This project contains the functional testcases for neo blockchain.

## Usage
* Step 1: Start a neo privatenet/localnet with 7 nodes(DBFT and RpcServer plugins required)

  Build neo with `dotnet build` and then start privatenet/localnet with `neo/scripts/run-localnet-nodes.sh`.

  `cd` to `neo` source directory and then run the following commands:
  ```bash
  dotnet build
  cd scripts
  ./run-localnet-nodes.sh  # or ./run-localnet-nodes.ps1 on Windows
  ```

* Step 2: Initialize testcase running environment

  `cd` to `neo-testcases` directory and then run the following commands:
  ```bash
  python3 -m venv venv  # Python3.12 and later is required
  source venv/bin/activate # or venv/bin/Activate.ps1 on Windows
  pip3 install -r requirements.txt
  ```

* Step 3: Set tested

  The default testbed is `testbed/localnet.json`, if you want to use other testbed, need to create a new testbed file.

* Step 4: Run the tests

  `cd` to `neo-testcases` directory and then run the following commands:
  ```bash
  ./run_tests.sh # or ./run_tests.ps1 on Windows
  ```


* After tests

  Stop the privatenet/localnet and clean the data.
  `cd` to `neo` source directory and then run the following commands:
  ```bash
  cd scripts
  ./run-localnet-nodes.sh stop  # or ./run-localnet-nodes.ps1 stop on Windows
  rm -rf localnet_nodes
  ```

  ## How to add a new testcase
  1. Create a new file in the `testcases/it's group` directory.
  2. Create a new class in the new file, inherit from the `Testing` class.
  3. Implement the `run_test` method, which contains the test steps.
  4. Implement the `pre_test`and `post_test` methods if needed, which contains the pre-test, test and post-test steps.
  5. If group is not in the `run_tests.sh` or `run_tests.ps1` file, add it to the file.
  6. Run the tests and check the results.
  7. Format the new file with pep8(with 120 characters per line) style.
  