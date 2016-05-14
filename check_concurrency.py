import os, sys
import json
import csv
import threading

class MyThread(threading.Thread):
    def __init__(self, file_name):
        threading.Thread.__init__(self)
        self.filename = file_name

    def run(self):
        # json file will contain all contracts in this format
        # {contract address: [Input, Code, TX hash that creates the contract]}
        temp_file = "stats/tmp_"

        with open(self.filename) as json_file:
            c = json.load(json_file)

            # Find and write the source code to disk for disassembly
            for contract, data in c.iteritems():
                evm_file = temp_file + contract +".evm"
                # code_file = temp_file + contract + ".code"
                # with open(code_file, 'w') as tfile:
                #     tfile.write(data[1][2:])
                #     tfile.write("\n")
                #     tfile.close()

                sys.stdout.write("\tRunning disassembly on contract %s...\t\r" % (contract))
                sys.stdout.flush()
                # os.system("cat %s | disasm > %s" % (code_file, evm_file))
                os.system("python symExec.py %s" % evm_file)
                # os.system("rm -rf %s*" % temp_file)
        return


def parse_code (filename):
    temp_file = "stats/tmp_"
    with open(filename) as json_file:
        c = json.load(json_file)

        # Find and write the source code to disk for disassembly
        for contract, data in c.iteritems():
            evm_file = temp_file + contract +".evm"
            code_file = temp_file + contract + ".code"
            with open(code_file, 'w') as tfile:
                tfile.write(data[1][2:])
                tfile.write("\n")
                tfile.close()

            sys.stdout.write("\tRunning disassembly on contract %s...\t\r" % contract)
            sys.stdout.flush()
            os.system("cat %s | disasm > %s" % (code_file, evm_file))
            sys.stdout.flush()

def main():
    if (len(sys.argv) < 2):
        print "Usage: python check_concurrency.py <list of contract.json>"
        print "Example: python check_concurrency.py contract.json"
        return

    list_threads = []
    #for i in range(1, len(sys.argv)):
    #    parse_code(sys.argv[i])
    for i in range(1, len(sys.argv)):
        new_thread = MyThread(sys.argv[i])
        list_threads.append(new_thread)
    for my_thread in list_threads:
        my_thread.start()


def collect_stats():
    with open("stats.csv", "w") as stats_file:
        fp = csv.writer(stats_file, delimiter=',')
        fp.writerow(["Contract address", "No. of paths", "No. of concurrency pairs", "False Positive", "Error"])
        for a_file in os.listdir("stats"):
            # read all report files
            if a_file.endswith(".report"):
                # print(a_file)
                address = a_file.split(".")[0].split("_")[1]
                with open("stats/" + a_file, "r") as f:
                    no_paths = int(f.readline())
                    no_concurrency = int(f.readline())
                    f.readline()
                    no_fp = int(f.readline())
                    a_log_file = a_file.replace ("report", "log")
                    with open("stats/" + a_log_file, "r") as lf:
                        fp.writerow([address, no_paths, no_fp, no_concurrency, lf.readlines()])


if __name__ == '__main__':
    main()
