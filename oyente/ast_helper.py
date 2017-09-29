from utils import run_command
from ast_walker import AstWalker
import json

class AstHelper:
    def extract_contract_definitions(self, sourcesList):
        ret = {
            "contractsById": {},
            "contractsByName": {},
            "sourcesByContract": {}
        }
        walker = AstWalker()
        for k in sourcesList:
            nodes = []
            walker.walk(sourcesList[k]["AST"], "ContractDefinition", nodes)
            for node in nodes:
                ret["contractsById"][node["id"]] = node
                ret["sourcesByContract"][node["id"]] = k
                ret["contractsByName"][k + ':' + node["attributes"]["name"]] = node
        return ret

    def get_linearized_base_contracts(self, id, contractsById):
        return map(lambda id: contractsById[id], contractsById[id]["attributes"]["linearizedBaseContracts"])

    def extract_state_definitions(self, contractName, sourcesList, contracts=None):
        if not contracts:
            contracts = self.extract_contract_definitions(sourcesList)
        node = contracts["contractsByName"][contractName]
        if node:
            stateVar = []
            baseContracts = self.get_linearized_base_contracts(node["id"], contracts["contractsById"])
            baseContracts = list(reversed(baseContracts))
            for ctr in baseContracts:
                if "children" in ctr:
                    for item in ctr["children"]:
                        if item["name"] == "VariableDeclaration":
                            stateVar.append(item)
            return stateVar

    def extract_states_definitions(self, sourcesList, contracts=None):
        if not contracts:
            contracts = self.extract_contract_definitions(sourcesList)
        ret = {}
        for contract in contracts["contractsById"]:
            name = contracts["contractsById"][contract]["attributes"]["name"]
            source = contracts["sourcesByContract"][contract]
            fullName = source + ":" + name
            state = self.extract_state_definitions(fullName, sourcesList, contracts)
            ret[fullName] = state
        return ret

    def extract_state_variable_names(self, filename, c_name):
        cmd = "solc --combined-json ast %s" % filename
        out = run_command(cmd)
        out = json.loads(out)
        state_variables = self.extract_states_definitions(out["sources"])[c_name]
        var_names = []
        for var_name in state_variables:
            var_names.append(var_name["attributes"]["name"])
        return var_names
