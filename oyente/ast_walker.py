class AstWalker:
    def walk(self, ast, node_name):
        node = self.find_node(ast, node_name)
        if node:
            return node
        if ast.has_key("children") and len(ast["children"]) > 0:
            for child in ast["children"]:
                node = self.walk(child, node_name)
                if node:
                    return node

    def find_node(self, node , node_name):
        if node["name"] in node_name:
            return node
        else:
            return None
