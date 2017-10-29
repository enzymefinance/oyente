import re
import ast
import json

import global_params

from utils import run_command
from ast_helper import AstHelper

class Source:
    def __init__(self, filename):
        self.filename = filename
        self.content = self.__load_content()
        self.line_break_positions = self.__load_line_break_positions()

    def __load_content(self):
        with open(self.filename, 'r') as f:
            content = f.read()
        return content

    def __load_line_break_positions(self):
        return [i for i, letter in enumerate(self.content) if letter == '\n']

class SourceMap:
    parent_filename = ""
    position_groups = {}
    sources = {}
    ast_helper = None

    def __init__(self, root_path, cname, parent_filename, input_type):
        self.root_path = root_path
        self.cname = cname
        self.input_type = input_type
        if not SourceMap.parent_filename:
            SourceMap.parent_filename = parent_filename
            if input_type == "solidity":
                SourceMap.position_groups = SourceMap.__load_position_groups()
            elif input_type == "standard json":
                SourceMap.position_groups = SourceMap.__load_position_groups_standard_json()
            else:
                raise Exception("There is no such type of input")
            SourceMap.ast_helper = AstHelper(SourceMap.parent_filename, input_type)
        self.source = self.__get_source()
        self.positions = self.__get_positions()
        self.instr_positions = {}
        self.var_names = self.__get_var_names()
        self.func_call_names = self.__get_func_call_names()

    def find_source_code(self, pc):
        try:
            pos = self.instr_positions[pc]
        except:
            return ""
        location = self.get_location(pc)
        begin = self.source.line_break_positions[location['begin']['line'] - 1] + 1
        end = pos['end']
        return self.source.content[begin:end]

    def get_location(self, pc):
        pos = self.instr_positions[pc]
        return self.__convert_offset_to_line_column(pos)

    def is_a_parameter_or_state_variable(self, var_name):
        try:
            names = [
                node.id for node in ast.walk(ast.parse(var_name))
                if isinstance(node, ast.Name)
            ]
            if names[0] in self.var_names:
                return True
        except:
            return False
        return False

    def __get_source(self):
        fname = self.get_filename()
        if SourceMap.sources.has_key(fname):
            return SourceMap.sources[fname]
        else:
            SourceMap.sources[fname] = Source(fname)
            return SourceMap.sources[fname]

    def __get_var_names(self):
        return SourceMap.ast_helper.extract_state_variable_names(self.cname)

    def __get_func_call_names(self):
        func_call_srcs = SourceMap.ast_helper.extract_func_call_srcs(self.cname)
        func_call_names = []
        for src in func_call_srcs:
            src = src.split(":")
            start = int(src[0])
            end = start + int(src[1])
            func_call_names.append(self.source.content[start:end])
        return func_call_names

    @classmethod
    def __load_position_groups_standard_json(cls):
        with open('standard_json_output', 'r') as f:
            output = f.read()
        output = json.loads(output)
        return output["contracts"]

    @classmethod
    def __load_position_groups(cls):
        cmd = "solc --combined-json asm %s" % cls.parent_filename
        out = run_command(cmd)
        out = json.loads(out)
        return out['contracts']

    def __get_positions(self):
        if self.input_type == "solidity":
            asm = SourceMap.position_groups[self.cname]['asm']['.data']['0']
        else:
            filename, contract_name = self.cname.split(":")
            asm = SourceMap.position_groups[filename][contract_name]['evm']['legacyAssembly']['.data']['0']
        positions = asm['.code']
        while(True):
            try:
                positions.append(None)
                positions += asm['.data']['0']['.code']
                asm = asm['.data']['0']
            except:
                break
        return positions

    def __convert_offset_to_line_column(self, pos):
        ret = {}
        ret['begin'] = None
        ret['end'] = None
        if pos['begin'] >= 0 and (pos['end'] - pos['begin'] + 1) >= 0:
            ret['begin'] = self.__convert_from_char_pos(pos['begin'])
            ret['end'] = self.__convert_from_char_pos(pos['end'])
        return ret

    def __convert_from_char_pos(self, pos):
        line = self.__find_lower_bound(pos, self.source.line_break_positions)
        if self.source.line_break_positions[line] != pos:
            line += 1
        begin_col = 0 if line == 0 else self.source.line_break_positions[line - 1] + 1
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

    def get_filename(self):
        return self.cname.split(":")[0]
