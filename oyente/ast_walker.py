class AstWalker:
    def walk(self, ast, node_name):
        node = self.managenode_name(ast, node_name)
        if node:
            return node
        if ast.has_key("children") and len(ast["children"]) > 0:
            for child in ast["children"]:
                node = self.walk(child, node_name)
                if node:
                    return node

    def managenode_name(self, node , node_name):
        if node["name"] in node_name:
            return node
        else:
            return None
