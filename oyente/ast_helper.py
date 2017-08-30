from utils import run_command
from ast_walker import AstWalker
import json

class AstHelper:
    def extractContractDefinitions(self, sourcesList):
        ret = {
            "contractsById": {},
            "contractsByName": {},
            "sourcesByContract": {}
        }
        walker = AstWalker()
        for k in sourcesList:
            node = walker.walk(sourcesList[k]["AST"], "ContractDefinition")
            ret["contractsById"][node["id"]] = node
            ret["sourcesByContract"][node["id"]] = k
            ret["contractsByName"][k + ':' + node["attributes"]["name"]] = node
        return ret

    def getLinearizedBaseContracts(self, id, contractsById):
        return map(lambda id: contractsById[id], contractsById[id]["attributes"]["linearizedBaseContracts"])

    def extractStateDefinitions(self, contractName, sourcesList, contracts=None):
        if not contracts:
            contracts = self.extractContractDefinitions(sourcesList)
        node = contracts["contractsByName"][contractName]
        if node:
            stateItems = []
            stateVar = []
            baseContracts = self.getLinearizedBaseContracts(node["id"], contracts["contractsById"])
            baseContracts = list(reversed(baseContracts))
            for ctr in baseContracts:
                for item in ctr["children"]:
                    stateItems.append(item)
                    if item["name"] == "VariableDeclaration":
                        stateVar.append(item)
            return {
                "stateDefinitions": stateItems,
                "stateVariables": stateVar
            }

    def extractStatesDefinitions(self, sourcesList, contracts=None):
        if not contracts:
            contracts = self.extractContractDefinitions(sourcesList)
        for contract in contracts["contractsById"]:
            name = contracts["contractsById"][contract]["attributes"]["name"]
            source = contracts["sourcesByContract"][contract]
            fullName = source + ":" + name
            state = self.extractStateDefinitions(fullName, sourcesList, contracts)
        return state

    def extractStateVariableNames(self, filename):
        cmd = "solc --combined-json ast %s" % filename
        out = run_command(cmd)
        out = json.loads(out)
        state = self.extractStatesDefinitions(out["sources"])
        var_names = []
        for var_name in state["stateVariables"]:
            var_names.append(var_name["attributes"]["name"])
        return var_names
