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
import subprocess
import re

# Chroot string for execute
CHROOT = "arch-chroot"

# Escape characters to format text color in log
FG_WHITE = '\u001b[37m'
FG_RED   = '\u001b[31m'

def has_network(timeout=5):
    log("[*] Checking internet connection")
    try:
        request.urlopen('https://google.com', timeout=timeout)
        log("[+] Internet connection good!")
        return True
    except:
        log("[!] No internet!")
        log("Connect to internet using: iwctl station <wlan> connect <SSID>")
        return False

def execute(cmd, stdin="", outfile="", chroot_dir="", interactive=False):
    if outfile != "" and interactive:
        log("[!] Cannot execute in interactive mode and save output to file")

    if chroot_dir != "":
        cmd = "{} {} {}".format(CHROOT, chroot_dir, cmd)
    cmd = cmd.split(' ')

    args = {"encoding": "utf-8"}
    if stdin != "":
        args["input"] = stdin
    if not interactive:
        args["stdout"] = subprocess.PIPE    # in non-interactive mode output can be processed

    proc = subprocess.run(cmd, **args)

    if outfile != "":
        write_file(proc.stdout, outfile)

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

def log(string):
    print(FG_RED + string + FG_WHITE)

