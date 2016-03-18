from opcodes import *
from math import *
from z3 import *

# THIS IS TO DEFINE A SKELETON FOR ANALYSIS
# FOR NEW TYPE OF ANALYSIS: add necessary details to the skeleton functions


def init_analysis():
    analysis = {
        "gas": 0,
        "gas_mem": 0,
        "money_flow": [("Is", "Ia", "Iv")]  # (source, destination, amount)
    }
    return analysis

# Money flow: (source, destination, amount)

def display_analysis(analysis):
    # print "Gas paid for execution: %d" % analysis["gas"]
    # print "Gas paid for memory usage: %d" % analysis["gas_mem"]
    print "Money flow: " + str(analysis["money_flow"])


def update_analysis(analysis, opcode, stack, mem, global_state):
    gas_increment = get_ins_cost(opcode)
    if opcode in ("LOG0", "LOG1", "LOG2", "LOG3", "LOG4"):
        gas_increment += GCOST["Glogdata"] * stack[1]
    elif opcode == "EXP" and isinstance(stack[1], (int, long)) and stack[1] > 0:
        gas_increment += GCOST["Gexpbyte"] * (1 + floor(log(stack[1], 256)))
    elif opcode == "SSTORE":
        # TODO
        pass

    analysis["gas"] = analysis["gas"] + gas_increment

    # I DON'T THINK THIS FORMULA IS CORRECT YET
    length = len(mem.keys())
    analysis["gas_mem"] = GCOST["Gmemory"] * length + (length ** 2) // 512

    if opcode == "CALL":
        recipient = stack[1]
        transfer_amount = stack[2]
        if isinstance(transfer_amount, (int, long)) and transfer_amount == 0:
            return
        if not isinstance(recipient, (int, long)):
            recipient = simplify(recipient)
        analysis["money_flow"].append(("Ia", str(recipient), transfer_amount))
    elif opcode == "SUICIDE":
        recipient = stack[0]
        if not isinstance(recipient, (int, long)):
            recipient = simplify(recipient)
        analysis["money_flow"].append(("Ia", str(recipient), "all_remaining"))


