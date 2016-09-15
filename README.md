# Oyente

**Note: The tool is currently under development, please report any bugs you may find.**

## Dependencies

1. solc and disasm from [go-ethereum](https://github.com/ethereum/go-ethereum)
2. [z3](https://github.com/Z3Prover/z3/releases) Thorem Prover

## Evaluating Ethereum Contracts

```python oyente.py <contract filename>```

And that's it! Run ```python oyente.py --help``` for a list of options.

## Paper

The accompanying paper explaining the bugs detected by the tool can be found [here](http://www.comp.nus.edu.sg/~loiluu/papers/oyente.pdf).

## Miscellaneous Utilities

A collection of the utilities that were developed for the paper are in `Misc_Utils`. Use them at your own risk - they have mostly been disposable.

1. `generate-graphs.py` - Contains a number of functions to get statistics from contracts.
2. `get_source.py` - The *get_contract_code* function can be used to retrieve contract source from [EtherScan](https://etherscan.io)
3. `transaction_scrape.py` - Contains functions to retrieve up-to-date transaction information for a particular contract.

#### Known Issues
If you encounter the `unhashable instance` error, please add the following to your `class AstRef(Z3PPObject):` in `/usr/lib/python2.7/dist-packages/z3.py`:
```
def __hash__(self):
        return self.hash()
```
The latest version of Z3 does support this, but some previous version does not.
