class AstWalker:
    def walk(self, node, node_name, nodes):
        if node["name"] == node_name:
            nodes.append(node)
        else:
            if "children" in node and node["children"]:
                for child in node["children"]:
                    self.walk(child, node_name, nodes)
