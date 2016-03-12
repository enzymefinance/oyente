import sys, tokenize
import json
import types
from tokenize import NUMBER, STRING, NAME, OP, NEWLINE
from neo4jrestclient.client import GraphDatabase

#Code - solc <source_file> --asm-json > <json_filename>

# source_file = "contracts/35_coin_flipper.sol"
# json_filename = "test2.txt"
neo4j_map = False
 
gdb = GraphDatabase("http://localhost:7474", username="neo4j", password="1.66Planck")
gdb.query("MATCH (n) DETACH DELETE n")
suicide_node = gdb.nodes.create(text="SUICIDE")
out_node = gdb.nodes.create(text="OUT")

benchmark = True
benchmark_file = "benchmark.txt"
missed_jump_counter = 0

term_instructions = ["JUMP", "SUICIDE", "RETURN", "STOP"]
jump_instructions = ["JUMP", "JUMPI"]

def load_source(filename):
    s_label = gdb.labels.create("Source Line")
    source_lines = []
    line_no=0
    characters=0
    with open(filename, 'r') as f:
        for line in f:
            line_no+=1
            n = gdb.nodes.create(start=characters, end=characters+len(line), content=line, text=str(line_no))
            s_label.add(n)
            characters+=len(line)
            if(len(source_lines) > 0): source_lines[len(source_lines)-1].relationships.create("next line", n)
            source_lines.append(n)
            
    return source_lines

def remove_whitespace(f):
    f.readline()
    f.readline()
    f.readline()

def load_json(f):
    return json.load(f)

def load_codeblocks(json_d):
    try: 
        load_codeblocks.cb_list
    except:
        load_codeblocks.cb_list = []
    if(type(json_d) is list):
        return
    for key, value in json_d.iteritems():
        if key == ".code":
            load_codeblocks.cb_list.append(value)
        else:
            load_codeblocks(value)

def connect_sourcelines(inode, source_lines, start, end):
    for line in source_lines:
        if int(line['start']) > int(end): break
        if int(start) >= int(line['start']) and int(start) <= int(line['end']): 
            line.relationships.create("source begin", inode)
        if int(end) >= int(line['start']) and int(end) <= int(line['end']):
            line.relationships.create("source end", inode)

def create_tags(cb, tag_label, source_lines):
    global out_node
    global suicide_node
    global missed_jump_counter
    tags = {}
    last_i = {}
    last_t = gdb.nodes.create(text="0", start=0)
    tag_label.add(last_t)
    tags["0"] = last_t
    jumps = []
    ino = 0
    for instruction in cb:
        ino+=1
        if "name" in instruction:
            if "value" in instruction and instruction['name']=="tag":
                n = gdb.nodes.create(text=instruction['value'], start = ino)
                if last_t != None:
                    last_t['end'] = ino-1
                if "name" in last_i and not (last_i["name"] in term_instructions) and last_t != None:
                    last_t.relationships.create("falls_to", n)
                if "begin" in instruction and "end" in instruction:
                    connect_sourcelines(n, source_lines, instruction['begin'], instruction['end'])
                tag_label.add(n)
                tags[instruction['value']] = n
                last_t = n
            elif instruction['name'] in jump_instructions:
                # print "Jump found. Last instruction: %s" % (last_i['name'] if 'name' in last_i else "Nothing")
                if "value" in instruction and instruction["value"] == "[out]" and last_t != None:
                    last_t.relationships.create("jumps out", out_node)
                elif "name" in last_i and last_i["name"] == "PUSH [tag]":
                    jumps.append((last_t['text'],last_i['value'],instruction['name']))
                else:
                    missed_jump_counter+=1

            elif instruction['name'] == "SUICIDE":
                if "begin" in instruction and "end" in instruction:
                    connect_sourcelines(suicide_node, source_lines, instruction['begin'], instruction['end'])
                    suicide_node['begin'] = instruction['begin']
                    suicide_node['end'] = instruction['end']
                    if "name" in last_i and not (last_i["name"] in term_instructions) and last_t != None:
                        last_t.relationships.create("suicides", suicide_node)                        
        last_i = instruction
    if last_t != None:
        last_t['end'] = ino-1
    if(neo4j_map is True):
        map_jumps(tags, jumps)
    return tags

def map_jumps(tags, jumps):
    for jump_s, jump_d, jump_t in jumps:
        # print "Jump created from %d to %d" % (int(jump_s), int(jump_d))
        if jump_s in tags and jump_d in tags:
            tags[jump_s].relationships.create(jump_t, tags[jump_d])
        else:
            print "Jump elements not found."

def process_cb(cb, source_lines):
    tag_label = gdb.labels.create("Tag")
    cb_tags = create_tags(cb, tag_label, source_lines)


def main():
    if len(sys.argv) < 4:
        print "Usage: python v2.py <source file> <json_file> <bench_file>"
        return
    print "Running..."
    raw_file = open(sys.argv[2],'r')
    remove_whitespace(raw_file)
    raw_json =  load_json(raw_file)
    load_codeblocks(raw_json)
    cb = load_codeblocks.cb_list
    source_lines = load_source(sys.argv[1])
    for i in xrange(0, len(cb)):
        process_cb(cb[i], source_lines)
    with open(sys.argv[3], "a") as bfile:
        bfile.write("%s, %d\n" % (sys.argv[2], missed_jump_counter))

if __name__ == '__main__':
    main()
