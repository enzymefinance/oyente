import shlex
import subprocess
import os
import re
import regex
import json

class SourceMapping:
    source = ""
    c_name = ""
    positions = {}
    instr_positions = {}
    position_groups = []
    line_break_positions = []

    @classmethod
    def load_source(cls, c_name):
        cls.c_name = c_name
        with open(c_name, 'r') as f:
            cls.source = f.read()
        cls.line_break_positions = cls.get_line_break_positions()
        cls.position_groups = cls.get_position_groups()

    @classmethod
    def get_position_groups(cls):
        solc_cmd = "solc --optimize --asm-json %s"

        FNULL = open(os.devnull, 'w')

        solc_p = subprocess.Popen(shlex.split(solc_cmd % cls.c_name), stdout=subprocess.PIPE, stderr=FNULL)
        solc_out = solc_p.communicate()

        reg = r"======= .*? =======\nEVM assembly:\n"
        out = re.compile(reg).split(solc_out[0])

        list_asm = []
        for asm in out[1:]:
            try:
                idx = asm.index("}{") + 1
                list_asm.append(asm[:idx])
            except:
                pass
        list_asm = [json.loads(asm) for asm in list_asm]
        list_asm = [asm[".code"] for asm in list_asm if asm.has_key('.auxdata')]
        pattern = re.compile("^tag")

        ret = []
        for asm in list_asm:
            asm = [instr for instr in asm if not pattern.match(instr["name"])]
            ret.append(asm)
        return ret

    @classmethod
    def get_line_break_positions(cls):
        return [i for i, letter in enumerate(cls.source) if letter == '\n']

    @classmethod
    def convert_offset_to_line_column(cls, pos):
        ret = {}
        ret['begin'] = None
        ret['end'] = None
        if pos['begin'] >= 0 and (pos['end'] - pos['begin'] + 1) >= 0:
            ret['begin'] = cls.convert_from_char_pos(pos['begin'])
            ret['end'] = cls.convert_from_char_pos(pos['end'])
        return ret

    @classmethod
    def convert_from_char_pos(cls, pos):
        line = cls.find_lower_bound(pos, cls.line_break_positions)
        if cls.line_break_positions[line] != pos:
            line += 1
        begin_col = 0 if line == 0 else cls.line_break_positions[line - 1] + 1
        col = pos - begin_col
        return {'line': line, 'column': col}

    @classmethod
    def find_lower_bound(cls, target, array):
        start = 0
        length = len(array)
        while length > 0:
            half = length >> 1
            middle = start + half
            if array[middle] <= target:
                length = length - 1 - half
                start = middle + 1
            else:
                length = half
        return start - 1

    @classmethod
    def get_position(cls, pc):
        pos = cls.instr_positions[pc]
        return cls.convert_offset_to_line_column(pos)

    @classmethod
    def convert_pos_to_source_code(cls, pc):
        pos = cls.instr_positions[pc]
        begin = pos['begin']
        end = pos['end']
        return cls.source[begin:end]

    @classmethod
    def to_str(cls, pc):
        position = cls.get_position(pc)
        source_code = cls.convert_pos_to_source_code(pc)
        s = "%s:%s:%s\n" % (cls.c_name, position['begin']['line'], position['begin']['column'])
        s += source_code + "\n"
        s += "^"
        return s


