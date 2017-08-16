import re
import json
from utils import run_solc_compiler

class SourceMap:
    position_groups = {}
    filename = ""

    def __init__(self, cname, filename):
        self.cname = cname
        SourceMap.filename = filename
        self.source = self.__load_source()
        self.line_break_positions = self.__load_line_break_positions()
        if not SourceMap.position_groups:
            SourceMap.position_groups = self.__load_position_groups()
        self.positions = self.__load_positions()
        self.instr_positions = {}

    def set_instr_positions(self, pc, pos_idx):
        self.instr_positions[pc] = self.positions[pos_idx]

    def find_source_code(self, pc):
        pos = self.instr_positions[pc]
        begin = pos['begin']
        end = pos['end']
        return self.source[begin:end]

    def to_str(self, pc):
        position = self.__get_location(pc)
        source_code = self.find_source_code(pc).split("\n", 1)[0]
        s = "%s:%s:%s\n" % (self.cname, position['begin']['line'] + 1, position['begin']['column'] + 1)
        s += source_code + "\n"
        s += "^"
        return s

    def get_positions(self):
        return self.positions

    def reduce_same_position_pcs(self, pcs):
        d = {}
        for pc in pcs:
            pos = str(self.instr_positions[pc])
            if pos not in d:
                d[pos] = pc
        return d.values()

    def __load_source(self):
        source = ""
        with open(self.__get_filename(), 'r') as f:
            source = f.read()
        return source

    def __load_line_break_positions(self):
        return [i for i, letter in enumerate(self.source) if letter == '\n']

    @classmethod
    def __load_position_groups(cls):
        cmd = "solc --combined-json asm %s"
        out = run_solc_compiler(cmd, cls.filename)
        out = out[0]
        out = json.loads(out)
        return out['contracts']

    @classmethod
    def __extract_position_groups(cls, c_asm):
        for cname in c_asm:
            asm = json.loads(c_asm[cname])
            asm = asm[".code"]
            pattern = re.compile("^tag")
            asm = [instr for instr in asm if not pattern.match(instr["name"])]
            c_asm[cname] = asm
        return c_asm

    def __load_positions(self):
        return SourceMap.position_groups[self.cname]['asm']['.data']['0']['.code']

    def __get_location(self, pc):
        pos = self.instr_positions[pc]
        return self.__convert_offset_to_line_column(pos)

    def __convert_offset_to_line_column(self, pos):
        ret = {}
        ret['begin'] = None
        ret['end'] = None
        if pos['begin'] >= 0 and (pos['end'] - pos['begin'] + 1) >= 0:
            ret['begin'] = self.__convert_from_char_pos(pos['begin'])
            ret['end'] = self.__convert_from_char_pos(pos['end'])
        return ret

    def __convert_from_char_pos(self, pos):
        line = self.__find_lower_bound(pos, self.line_break_positions)
        if self.line_break_positions[line] != pos:
            line += 1
        begin_col = 0 if line == 0 else self.line_break_positions[line - 1] + 1
        col = pos - begin_col
        return {'line': line, 'column': col}

    def __find_lower_bound(self, target, array):
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

    def __get_filename(self):
        return self.cname.split(":")[0]
