from utils import run_command
from ast_walker import AstWalker
import json

class AstHelper:
    def __init__(self, filename, input_type):
        self.input_type = input_type
        if input_type == "solidity":
            self.source_list = self.get_source_list(filename)
        elif input_type == "standard json":
            self.source_list = self.get_source_list_standard_json(filename)
        else:
            raise Exception("There is no such type of input")
        self.contracts = self.extract_contract_definitions(self.source_list)

    def get_source_list_standard_json(self, filename):
        with open('standard_json_output', 'r') as f:
            out = f.read()
        out = json.loads(out)
        return out["sources"]

    def get_source_list(self, filename):
        cmd = "solc --combined-json ast %s" % filename
        out = run_command(cmd)
        out = json.loads(out)
        return out["sources"]

    def extract_contract_definitions(self, sourcesList):
        ret = {
            "contractsById": {},
            "contractsByName": {},
            "sourcesByContract": {}
        }
        walker = AstWalker()
        for k in sourcesList:
            if self.input_type == "solidity":
                ast = sourcesList[k]["AST"]
            else:
                ast = sourcesList[k]["legacyAST"]
            nodes = []
            walker.walk(ast, "ContractDefinition", nodes)
            for node in nodes:
                ret["contractsById"][node["id"]] = node
                ret["sourcesByContract"][node["id"]] = k
                ret["contractsByName"][k + ':' + node["attributes"]["name"]] = node
        return ret

    def get_linearized_base_contracts(self, id, contractsById):
        return map(lambda id: contractsById[id], contractsById[id]["attributes"]["linearizedBaseContracts"])

    def extract_state_definitions(self, c_name):
        node = self.contracts["contractsByName"][c_name]
        state_vars = []
        if node:
            base_contracts = self.get_linearized_base_contracts(node["id"], self.contracts["contractsById"])
            base_contracts = list(reversed(base_contracts))
            for contract in base_contracts:
                if "children" in contract:
                    for item in contract["children"]:
                        if item["name"] == "VariableDeclaration":
                            state_vars.append(item)
        return state_vars

    def extract_states_definitions(self):
        ret = {}
        for contract in self.contracts["contractsById"]:
            name = self.contracts["contractsById"][contract]["attributes"]["name"]
            source = self.contracts["sourcesByContract"][contract]
            full_name = source + ":" + name
            ret[full_name] = self.extract_state_definitions(full_name)
        return ret

    def extract_func_call_definitions(self, c_name):
        node = self.contracts["contractsByName"][c_name]
        walker = AstWalker()
        nodes = []
        if node:
            walker.walk(node, "FunctionCall", nodes)
        return nodes

    def extract_func_calls_definitions(self):
        ret = {}
        for contract in self.contracts["contractsById"]:
            name = self.contracts["contractsById"][contract]["attributes"]["name"]
            source = self.contracts["sourcesByContract"][contract]
            full_name = source + ":" + name
            ret[full_name] = self.extract_func_call_definitions(full_name)
        return ret

    def extract_state_variable_names(self, c_name):
        state_variables = self.extract_states_definitions()[c_name]
        var_names = []
        for var_name in state_variables:
            var_names.append(var_name["attributes"]["name"])
        return var_names

    def extract_func_call_srcs(self, c_name):
        func_calls = self.extract_func_calls_definitions()[c_name]
        func_call_srcs = []
        for func_call in func_calls:
            func_call_srcs.append(func_call["src"])
        return func_call_srcs
