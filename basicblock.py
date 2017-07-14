class BasicBlock:
    def __init__(self, start_address, end_address):
        self.start = start_address
        self.end = end_address
        self.instructions = []  # each instruction is a string
        self.jump_target = 0
        self.function = None

    def set_function(self, function):
        self.function = function

    def get_function(self):
        return self.function

    def is_callvalue(self):
        if len(self.instructions) < 5:
            return False
        instrs = ["JUMPDEST", "CALLVALUE", "ISZERO", "PUSH", "JUMPI"]
        for i in range(0, 5):
            if not self.instructions[i].startswith(instrs[i]):
                return False
        return True

    def get_start_address(self):
        return self.start

    def get_end_address(self):
        return self.end

    def add_instruction(self, instruction):
        self.instructions.append(instruction)

    def get_instructions(self):
        return self.instructions

    def set_block_type(self, type):
        self.type = type

    def get_block_type(self):
        return self.type

    def set_falls_to(self, address):
        self.falls_to = address

    def get_falls_to(self):
        return self.falls_to

    def set_jump_target(self, address):
        if isinstance(address, (int, long)):
            self.jump_target = address
        else:
            self.jump_target = -1

    def get_jump_target(self):
        return self.jump_target

    def set_branch_expression(self, branch):
        self.branch_expression = branch

    def get_branch_expression(self):
        return self.branch_expression

    def display(self):
        print "================"
        print "start address: %d" % self.start
        print "end address: %d" % self.end
        print "end statement type: " + self.type
        for instr in self.instructions:
            print instr
