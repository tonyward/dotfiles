########################################
#                                      #
#                                      #
#      install_util.py - Tony Ward     #
#                                      #
#  Basic utilities used in install.py  #
#                                      #
#                                      #
########################################

from urllib import request

def has_network(timeout=5):
    try:
        request.urlopen('https://google.com', timeout=timeout)
        return True
    except:
        return False

def execute(cmd, outfile="", chroot=False):
    if chroot:
        cmd = CHROOT + cmd
    cmd = cmd.split(' ')
    proc = subprocess.run(cmd, stdout=subprocess.PIPE)
    if outfile != "":
        write_file(proc.stdout.decode("ascii"), outfile)
    return proc

def write_file(string, file_path):
    file = open(file_path, "w")
    file.write(string)
    file.close()

def replace_in_file(match_line, string, file_path):
    file = open(file_path, "r")
    lines = file.readlines()
    file.close()
    file = open(file_path, "w")
    for line in lines:
        if re.match(match_line, line):
            line = string
        file.write(line)
    file.close()

# Escape characters to format text color
FG_WHITE = '\u001b[37m'
FG_RED   = '\u001b[31m'
def log(string):
    print(FG_RED + string + FG_WHITE)

