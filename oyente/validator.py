class Validator:
    def __init__(self, source_map):
        self.source_map = source_map
        self.instructions_vulnerable_to_callstack = {}

    def remove_false_positives(self, pcs):
        new_pcs = [pc for pc in pcs if self.source_map.find_source_code(pc)]
        new_pcs = self.source_map.reduce_same_position_pcs(new_pcs)
        return new_pcs

    def remove_callstack_false_positives(self, pcs):
        new_pcs = []
        for pc in pcs:
            if pc in self.instructions_vulnerable_to_callstack and self.instructions_vulnerable_to_callstack[pc] or pc not in self.instructions_vulnerable_to_callstack:
                new_pcs.append(pc)
        return new_pcs
