'''
=========================================================================

    Code coverage analysis tool: 
    Log parsing program.

    Usage:

        coverage_parse.py <log_file_path> [options]

    ... where:

        <log_file_path> - Path to the log file, that has been generated by
        Coverager.dll (PIN toolkit instrumentation module).

    Walid options are:

        --outfile <output_file_path> - Write output into the text file,
        instead console.

        --dump-blocks - Parse basic blocks information.

        --dump-routines - Parse functions calls information.

        --order-by-names - Sort output by symbol name (default mode).

        --order-by-calls - Sort output by number of function/block calls.

        --modules <module_name> - Print information only for the specified modules.

        --skip-symbols - Don't use PDB loading and parsing for executable modules.

    You must specify --dump-blocks or --dump-routines option, but not a both.

    Example:

        coverage_parse.py Coverager.log --dump-routines --modules "ieframe,iexplore" --outfile routines.txt


    Developed by:

    Oleksiuk Dmitry, eSage Lab
    mailto:dmitry@esagelab.com
    http://www.esagelab.com/

=========================================================================
'''

import sys, os, time

ver = sys.version[:3]

# load python specified version of symlib module
if ver == "2.5":

    from symlib25 import *

elif ver == "2.6":

    from symlib import *

else:

    print "[!] Only Python 2.5 and 2.6 are supported by symlib module"

# if end

APP_NAME = '''
Code Coverage Analysis Tool for PIN
by Oleksiuk Dmitry, eSage Lab (dmitry@esagelab.com)
'''

def sortproc_names(a, b):

    a = a['name'].lower()
    b = b['name'].lower()

    if a > b:

        return 1

    if a < b:

        return -1

    return 0

# def end  

def sortproc_calls(a, b):

    a = a['calls']
    b = b['calls']

    if a > b:

        return -1

    if a < b:

        return 1

    return 0

# def end  

m_modules_list = {}
m_logfile = None
m_sortproc = sortproc_names
m_modules_to_process = []
m_skip_symbols = False

def log_write(text):

    global m_logfile

    if m_logfile:

        m_logfile.write(text + "\r\n")

    else:

        print text

# def end    

def read_modules_list(file_name):

    global m_modules_list

    # open input file
    f = open(file_name)
    content = f.readline()

    # read file contents line by line
    while content != "":
        
        content = content.replace("\n", "")
        entry = content.split(":") 

        if content[:1] != "#" and len(entry) >= 3:

            module_path = ":".join(entry[2:])
            module_name = os.path.basename(module_path).lower()

            m_modules_list[module_name] = { 'path': module_path, 'processed_items': 0 }

        # if end

        # read the next line
        content = f.readline()        

    # while end    

    f.close()

# def end    

def parse_symbol(string):

    global m_modules_list, m_modules_to_process, m_skip_symbols

    # parse 'name+offset' string
    info = string.split("+")
    if len(info) >= 2:

        info[1] = int(info[1], 16)
        module_path = info[0].lower()

        if m_modules_list.has_key(module_path):

            m_modules_list[module_path]['processed_items'] += 1            

        # if end        

        skip_module = False

        if len(m_modules_to_process) > 0:

            skip_module = True

            for module_flt in m_modules_to_process:

                if module_path.find(module_flt) >= 0:

                    # don't skip this module
                    skip_module = False

                # if end
            # for end        
        # if end

        if skip_module:

            return False

        if m_skip_symbols:

            return string
                
        if m_modules_list.has_key(module_path):

            module_path = m_modules_list[module_path]['path']

        # if end

        # lookup debug symbol for address
        symbol = bestbyaddr(module_path, info[1])
        if symbol != None:

            addr_s = "%s!%s" % (info[0], symbol[0])

            if symbol[1] > 0:

                addr_s += "+0x%x" % symbol[1]

            return addr_s

        # if end

    elif string[0] == "?" and len(m_modules_to_process) > 0:

        if "?" not in m_modules_to_process:

            return False

    # if end

    return string

# def end    

def print_routines(file_name):

    global m_sortproc

    # open input file
    f = open(file_name)
    content = f.readline()

    print "[+] Parsing routines list, please wait...\n"    

    info_list = []
    i = 0

    # read file contents line by line
    while content != "":
        
        sys.stdout.write(["-", "\\", "|", "/"][i])
        sys.stdout.write("\r")
        i = (i + 1) & 3
        
        content = content.replace("\n", "")        
        entry = content.split(":") 

        if content[:1] != "#" and len(entry) >= 3:

            rtn_addr = int(entry[0], 16) # routinr virtual address
            rtn_calls = int(entry[2])
            
            # parse symbol name
            rtn_name = parse_symbol(entry[1])

            if rtn_name != False:

                info_list.append({'addr': rtn_addr, 'name': rtn_name, 'calls': rtn_calls })

        # if end

        # read the next line
        content = f.readline()

    # while end    

    # sort entries list
    info_list.sort(m_sortproc)

    log_write("#")
    log_write("# %13s -- %s" % ("Calls count", "Function Name"))
    log_write("#")

    for entry in info_list:

        # print single log file entry information
        log_write("%15d -- %s" % (entry['calls'], entry['name']))

    # for end

    f.close()

# def end

def print_blocks(file_name):

    global m_sortproc

    # open input file
    f = open(file_name)
    content = f.readline()

    print "[+] Parsing basic blocks list, please wait...\n"    

    info_list = []    
    instructions = 0
    i = 0    

    # read file contents line by line
    while content != "":

        sys.stdout.write(["-", "\\", "|", "/"][i])
        sys.stdout.write("\r")
        i = (i + 1) & 3
        
        content = content.replace("\n", "")
        entry = content.split(":")        

        if content[:1] != "#" and len(entry) >= 4:

            # parse log entry
            bb_addr = int(entry[0], 16) # block virtual address
            bb_size = int(entry[1], 16) # block size
            bb_calls = int(entry[4]) # calls count
            bb_insts = int(entry[2]) # instructions count

            # parse symbol name
            bb_name = parse_symbol(entry[3])

            if bb_name != False:

                info_list.append({'addr': bb_addr, 'name': bb_name, 'calls': bb_calls, 'size': bb_size }) 
                instructions += bb_insts * bb_calls

        # if end

        # read the next line
        content = f.readline()        

    # while end   

    # sort entries list
    info_list.sort(m_sortproc)
    
    log_write("#")
    log_write("# %13s -- Block Size -- %s" % ("Calls count", "Function Name"))
    log_write("#")

    for entry in info_list:

        # print single log file entry information
        log_write("%15d -- 0x%.8x -- %s" % (entry['calls'], entry['size'], entry['name']))

    # for end

    log_write("#")
    log_write("# %d total instructions executed in given basic blocks" % instructions)
    log_write("#")

    f.close()

# def end   

if __name__ == "__main__":

    print APP_NAME

    if len(sys.argv) < 2:

        print "USAGE: coverage_parse.py <LogFilePath> [options]"
        sys.exit()

    # if end

    dump_blocks = False
    dump_routines = False
    logfile = None    

    fname = sys.argv[1]
    fname_blocks = fname + ".blocks"
    fname_routines = fname + ".routines"
    fname_modules = fname + ".modules"

    # parse command line arguments
    if len(sys.argv) > 2:
        
        for i in range(2, len(sys.argv)):    
        
            if sys.argv[i] == "--outfile" and i < len(sys.argv) - 1:
        
                # save information into the logfile   
                logfile = sys.argv[i + 1]                                

            elif sys.argv[i] == "--modules" and i < len(sys.argv) - 1:
        
                # filter by module name is specified
                modlist = sys.argv[i + 1].split(",")

                for mod in modlist:

                    mod = mod.lstrip()
                    m_modules_to_process.append(mod.lower())

                    print "Filtering by module name \"%s\"" % (mod)

                # for end
            
            elif sys.argv[i] == "--dump-blocks":

                # parse basic blocks log file
                dump_blocks = True

            elif sys.argv[i] == "--dump-routines":
                
                # parse routines log file
                dump_routines = True

            elif sys.argv[i] == "--order-by-names":
                
                print "[+] Ordering list by symbol name"
                m_sortproc = sortproc_names

            elif sys.argv[i] == "--order-by-calls":
                
                print "[+] Ordering list by number of calls"
                m_sortproc = sortproc_calls

            elif sys.argv[i] == "--skip-symbols":
                
                m_skip_symbols = True

            # if end
        # for end
    # if end    

    if (not dump_blocks) and (not dump_routines):

        print "[!] You must specify '--dump-blocks' or '--dump-routines' option"
        sys.exit()

    # if end

    if dump_blocks and dump_routines:

        print "[!] You must specify only '--dump-blocks' or '--dump-routines' option (not both)"
        sys.exit()

    # if end

    if not os.path.isfile(fname):

        print "[!] Error while opening input file"
        sys.exit(-1)

    # if end

    if not os.path.isfile(fname_modules):

        print "[!] Error while opening modules log"
        sys.exit(-1)

    # if end    

    if logfile:

        # create output file
        m_logfile = open(logfile, "wb+")
        print "[+] Output file: \"%s\"" % (logfile)

    # if end

    # read target application modules list
    read_modules_list(fname_modules)

    if dump_blocks:

        if not os.path.isfile(fname_blocks):

            print "[!] Error while opening basic blocks log"
            sys.exit(-1)

        # if end

        print_blocks(fname_blocks)

    # if end

    if dump_routines:

        if not os.path.isfile(fname_routines):

            print "[!] Error while opening routines log"
            sys.exit(-1)

        # if end    
        
        print_routines(fname_routines)

    # if end

    if logfile:

        m_logfile.close()

    # print processed modules information
    print "\n[+] Processed modules list:\n"
    print "#"
    
    if dump_routines:        
        
        print "# %13s -- %s" % ("Routines count", "Module Name")

    elif dump_blocks:

        print "# %13s -- %s" % ("Basic blocks count", "Module Name")
    
    print "#"

    for module_name in m_modules_list:

        count = m_modules_list[module_name]['processed_items']
        print "%15d -- %s" % (count, module_name)

    # for end

    print "\n[+] DONE\n"

# if end    

#
# EoF
#
