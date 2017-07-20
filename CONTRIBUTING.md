Find a bug, a way to improve the documentation or have a feature request? Open an [issue](https://github.com/melonproject/oyente/issues/new).

Or even better, send us a PR :)

# Before you send PRs
- Follow the [instructions](https://github.com/melonproject/oyente#full-install) to get a locally working version of oyente
- Make your awesome change
- Make sure the code adheres to the coding style. We use pylint with the [following configuration](https://github.com/melonproject/oyente/blob/master/pylintrc)
- Make sure that the tests pass
- Write a [good commit message](http://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html)

# Running the tests

There are two options to run the tests, which are concrete execution and symbolic execution.
Before running the test you have to choose an option. There is a global variable named `UNIT_TEST` in `global_test_params.py` to set the type of the tests.

```
# Testing concrete execution
UNIT_TEST = 2
# Testing symbolic execution
UNIT_TEST = 3
```

```
# Start testing
$ python test_evm.py
```

After running the testing program, the result would display a status for each testcase:
- ```PASS```: the testcase passes
- ```FAIL```: an opcode implements incorrectly
- ```TIME_OUT```: it takes too long to run the testcase (set ```GLOBAL_TIMEOUT_TEST``` in ```global_params.py```)
- ```UNKNOWN_INSTRUCTION```: there is an unknown opcode in the testcase
- ```EXCEPTION```: the program encounters an exception while running the testcase
- ```EMPTY_RESULT``` the result is invalid
- ```INCORRECT_GAS``` the gas is calculated incorrectly

