import mmap
import os
import re
from subprocess import call
import sys
import string
import ntpath
import re
import lxml.html

# Using GNU Parallel - O. Tange (2011): GNU Parallel - The Command-Line Power Tool,
# ;login: The USENIX Magazine, February 2011:42-47.

def strip_html(x):
    return lxml.html.fromstring(x).text_content() if x else ''

def path_leaf(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)

core_url = "https://etherscan.io/txsInternal?valid=false&p=%d"
core_url2 = "https://etherscan.io/txsInternal?p=%s"
txinfo_headers = ["transaction","from","to","gas","gas used","cumulative gas used","transaction value"]
cinfo_headers = ["contract code url","contract value"]

def download_txs(dirn):
    # Load the first page
    print "Downloading transactions..."
    os.system("wget https://etherscan.io/txsInternal?valid=false -O tmp.html")
    max_p = run_re_file(r"Page <b>1<\/b> of <b>(\d+)<\/b><\/span>", "tmp.html")[0]
    print "Max pages = %d" % (int(max_p)) 
    os.system("curl 'https://etherscan.io/txsInternal?valid=false&p=[1-%d]'' -o %stxs#1.html" % (max_p,dirn))
    print "Download complete."
    os.system("rm tmp.html")

def download_txs_all(dirn):
    # Load the first page
    print "Downloading transactions..."
    os.system("wget https://etherscan.io/txsInternal -O tmp.html")
    max_p = run_re_file(r"Page <b>1<\/b> of <b>(\d+)<\/b><\/span>", "tmp.html")[0]
    print "Max pages = %d" % (int(max_p)) 
    os.system("curl 'https://etherscan.io/txsInternal?p=[1-%d]' -o %stxs#1.html" % (int(max_p),dirn))
    print "Download complete."
    os.system("rm tmp.html")


def get_tx_from_dir(dirn):
    txs = []
    print ""
    for filen in os.listdir(dirn):
        sys.stdout.write("Loaded File %s.\r" % filen)
        txs += get_tx_from_file(dirn+"/"+filen)
    print ""
    return txs

def get_contracts_info(contracts, clean):
    print "Getting info for contracts..."
    tmp_dir = "contracts_tmp"
    tmp_tmp_dir = tmp_dir+"/tmp"
    tmp_file = tmp_dir+"/contracts.txt"
    template = "https://etherscan.io/address/%s"
    os.system("mkdir "+tmp_dir)
    with open(tmp_file, 'w') as tfile:
        for contract in contracts:
            if( not os.path.isfile(tmp_tmp_dir+"/"+contract)):
                tfile.write((template % contract)+"\n")
            else:
                sys.stdout.write("Skipped contract %s\r" % contract)
    print " "
    os.system("cat %s | parallel --will-cite --progress --bar -j 60 wget --quiet --directory-prefix=%s" % (tmp_file, tmp_tmp_dir))
    print "Loading values..."
    values = []
    for i in xrange(0, len(contracts)):
        sys.stdout.write("%0.2f percent done.\r" % (float(i)/len(contracts))*100)
        values.append(load_contractfile(tmp_tmp_dir+"/"+contracts[i]))
    print " "    
    # for contract in contracts:
    #     values.append(load_contractfile(tmp_tmp_dir+"/"+contract))
    # for filen in os.listdir(tmp_tmp_dir):
    #     if(filen.find('.') != -1): continue

    #     values.append(load_contractfile(tmp_tmp_dir+"/"+filen))
    if(clean):
        os.system("rm -r "+tmp_dir)
    return values

def process_value(inp):
    inp = string.join(string.split(strip_html(inp),","),"")
    units = ["wei","Kwei","Mwei","Gwei","szabo","finney","ether","Kether","Mether","Gether","Tether"]
    conv_ratio = [1.0/1000000000000000000.0, 1.0/1000000000000000.0,1.0/1000000000000.0,1.0/1000000000.0,1.0/1000000000.0,1.0/1000.0,1,1000,1000000,1000000000,1000000000000]
    re_digit = r"([\d.]+)"
    unit_conv_ratio = 1
    for i in xrange(0, len(units)):
        if re.search(units[i], inp, re.IGNORECASE):
            unit_conv_ratio = conv_ratio[i]
            break
    number = float(re.match(re_digit, inp).group(0))
    return str(number*unit_conv_ratio)


def load_contractfile(fn):
    code_dir = "contract_code"
    re_code_value = r"<pre class='wordwrap' id='js-copytextarea' style='max-height: 250px; margin-top: 5px;'>([\s\S]+?)<\/pre>"
    re_code_url = r"<a href='(.+?)' target='_blank' title='Please set the corresponding CompilerVersion and Optimization in the Online Compiler'><b>Click To View<\/b><\/a>"
    re_str_value = r"<td>ETH Balance:\n<\/td>\n<td>\n(.+?)\n<\/td>"

    if(len(run_re_file(re_str_value, fn)) < 1):
        print "Balance retrieval failed for file %s" % fn
        print "Downloading again..."
        os.system("rm %s"+fn)
        os.system("wget -O %s https://etherscan.io/address/%s" % (fn, path_leaf(fn)))
        if(len(run_re_file(re_str_value, fn)) < 1):
            print "Balance retrieval failed hopelessly for file %s" % fn

    if(not os.path.exists(code_dir)):   
        os.system("mkdir %s" % code_dir)
    code_url = run_re_file(re_code_url, fn)    
    retval = []
    try:
        if(len(code_url) < 1):
            code_url = ['']
        code = run_re_file(re_code_value, fn)
        if(len(code) > 0):
            with open(code_dir+"/"+path_leaf(fn),'w') as cfile:
                cfile.write(code[0])
        retval = [code_url[0], process_value(run_re_file(re_str_value, fn)[0])]
    except IndexError:
        print "IndexError in transaction %s" % (path_leaf(fn))
        retval = ['', '']
    return retval


def load_txfile(fn):
    re_str_from = r"From:\n<\/td>\n<td>\n<a href='\/address\/(0x[\da-f]+?)'>"
    re_str_to = r"Contract <a href='\/address\/(0x[\da-f]+?)'>"
    re_str_gasgiven = r"<span title=\"The amount of GAS supplied for this transaction to happen\">\n(\d+?)\n<\/td>"
    re_str_gasused = r"<span title=\"The amount of gas used by this specific transaction alone\">\n(\d+?)<\/span><\/td>"
    re_str_cumgas = r"span title=\"The total amount of gas used when this transaction was executed in the block\. If being used with a smart contact, this would show the total amount of gas that has been used to interact with it\">\n(\d+?)<\/span><\/td>"
    re_str_value = r"<span title=\"The amount of ETH to be transferred to the recipient with the transaction\">\n(.+?)<\/span>"

    return [run_re_file(re_str_from, fn)[0], run_re_file(re_str_to, fn)[0], run_re_file(re_str_gasgiven, fn)[0], run_re_file(re_str_gasused, fn)[0], run_re_file(re_str_cumgas, fn)[0], process_value(run_re_file(re_str_value, fn)[0])]

def get_txinfo(txs, fn, dirn, clean):
    with open(fn, 'w') as urlfile:
        for tx in txs:
            if not os.path.isfile(dirn+"/"+tx):
                urlfile.write("https://etherscan.io/tx/%s\n" % tx)
            else:
                sys.stdout.write("Skipping file %s\r" % tx)
    os.system("mkdir %s" % dirn)
    os.system("cat %s | parallel --will-cite --progress --bar -j 60 wget --quiet --directory-prefix=%s" % (fn, dirn))
    print "downloaded files. reading data..."
    tx_data = []
    to_contracts = []
    for filen in os.listdir(dirn):
        if(filen.find('.') != -1): continue
        sys.stdout.write("Reading file %s\r" % (filen))
        try:
            tx_data_file = [filen] + (load_txfile(dirn+"/"+filen))
        except IndexError:
            print "IndexError in file %s\t\t\t." % filen
            continue
        tx_data.append(tx_data_file)
        to_contracts.append(tx_data_file[txinfo_headers.index("to")])
    print ""
    if(clean):
        os.system("rm -r %s" % dirn)  
    print "loading contract info..."
    cinfo = get_contracts_info(to_contracts, clean)
    return (tx_data, cinfo)


def save_csv(data, headers, filen):
    for i in xrange(1, len(data)):
        if(len(data[i]) != len(data[i-1])):
            print "Unequal lists"
            return
    with open(filen, 'w') as csvfile:
        final_header = []
        for header in headers:
            final_header += header
            csvfile.write(string.join(final_header, ",")+"\n")
        for i in xrange(0, len(data[0])):
            row = []
            for j in xrange(0, len(data)):
                row += data[j][i]
            csvfile.write(string.join(row, ",")+"\n")


def run(clean=False):
    txs = get_tx_from_dir("test")
    txinfo, cinfo = get_txinfo(txs, "urls.txt", "tx_dir", clean)
    save_csv([txinfo, cinfo], [txinfo_headers, cinfo_headers], "output3.csv")
    return txinfo,cinfo

# def load_txfiles(dirn)

def get_tx_from_file(fn):
    re_str = r"<a class='address-tag' href='\/tx\/(0x[0-9a-f]+?)'>"
    return run_re_file(re_str, fn)

def run_re_file(re_str, fn):
    size = os.stat(fn).st_size
    with open(fn, 'r') as tf:
        data = mmap.mmap(tf.fileno(), size, access=mmap.ACCESS_READ)
        return re.findall(re_str, data)