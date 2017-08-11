class Assertion:
    def __init__(self, block_from):
        # Block that contains the test (assertion)
        self.block_from = block_from

        # Was the assertion violated?
        self.violated = False

        # If the assertion was violated,
        # store the counterexample
        self.model = None

        # SMT2 query to decide the assertion
        self.query = None

        # Program counter of the ASSERTFAIL
        self.pc = -1

    def set_pc(self, pc):
        self.pc = pc

    def get_pc(self):
        return self.pc

    def get_block_from(self):
        return self.block_from

    def is_violated(self):
        return self.violated

    def set_violated(self, violated):
        self.violated = violated

    def get_model(self):
        return self.model

    def set_model(self, model):
        self.model = model

    def get_query(self):
        return self.query

    def set_query(self, query):
        self.query = query

    def get_log(self):
        s = ""
        #s += "SMT2 query:\n" + str(self.query) + "\n"
        #s += "Violated: " + str(self.violated) + "\n"
        #if self.violated:
        #    s += "Model:\n"
        #    for decl in self.model.decls():
        #        s += str(decl.name()) + " = " + str(self.model[decl]) + ", "
        return s

    def __str__(self):
        s = ""
        return s
