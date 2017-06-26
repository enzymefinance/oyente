class Assertion:
    def __init__(self, block_from, block_yes, block_no):
        # Block that contains the test (assertion)
        self.block_from = block_from

        # Block that is executed when the assertion is true
        self.block_yes = block_yes

        # Block that contains INVALID
        # This block should fall to INVALOD
        self.block_no = block_no

        # Was the assertion violated?
        self.violated = False

        # If the assertion was violated,
        # store the counterexample
        self.model = None

        # SMT2 query to decide the assertion
        self.query = None

    def get_block_from(self):
        return self.block_from

    def get_block_yes(self):
        return self.block_yes
    
    def get_block_no(self):
        return self.block_no

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

    def display(self):
        print "================"
        print "Assertion from block %d" % self.block_from
        print "SMT2 query: %s" % str(self.query)
        print "Violated: %s" % str(self.violated)
        if self.violated:
            print "Model:\n"
            for decl in self.model.decls():
                print "%s = %s" % (decl.name(), str(self.model[decl]))
