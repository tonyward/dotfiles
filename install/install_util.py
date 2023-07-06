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
from configparser import ConfigParser
import subprocess
import re
import os


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

def load_config(config_path):
    if not os.path.isfile(config_path):
        log("[!] No config file found - {}".format(config_path))
        exit()

    config = ConfigParser(allow_no_value=True)
    config.read(config_path)

    pkg_sects = [re.match("Pkgs.*", sect) for sect in config.sections()]
    if not any(pkg_sect):
        log("[!] No installation packages in config")
        exit()

    if not "Timezone" in config.sections():
        log("[!] No timezone specified in config")
        exit()

    if not "Network" in config.section():
        log("[!] No network settings in config")
        exit()
    
    return config

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

