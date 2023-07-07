########################################
#                                      #
#                                      #
#       configure.py - Tony Ward       #
#                                      #
#    Links / copies all config files   #
#       to where they need to be       #
#                                      #
#                                      #
########################################

#!/usr/bin/python
from configparser import ConfigParser
import os

# Load config file
config = ConfigParser()
config.read("config")

# Check all required sections are present
if "base" not in config:
    print("[!] ERROR: [base] missing from config")
    exit()
if "files" not in config:
    print("[!] ERROR: [files] missing from config")
    exit()
if "dirs" not in config:
    print("[!] ERROR: [dirs] missing from config")
    exit()

# Load base directory
if "base" not in config["base"]:
    print("[!] ERROR: [base] is missing definition for base")
    exit()
base = config["base"]["base"]
print("[+] Base folder loaded as - {}".format(base))

# Symlink files
for src in config["files"]:
    # Use absolute paths
    dst = base + config["files"][src]
    src = os.getcwd() + "/" + src
    if os.path.isfile(src):
        if os.path.isfile(dst):
            print("[-] {} already exists - deleting".format(dst))
            os.remove(dst)
        print("[+] Linking {} to {}".format(src, dst))
        try:
            os.symlink(src, dst)
        except:
            print("[!] ERROR: Could not link {} to {}, folder structure and permissions".format(src, dst))
    else:
        print("[!] ERROR: Cannot link {} - file not found".format(src))

# Symlink directories
for src in config["dirs"]:
    # Use absolute paths
    dst = base + config["dirs"][src]
    src = os.getcwd() + "/" + src
    if os.path.isdir(src):
        if os.path.isdir(dst):
            print("[-] {} already exists - deleting".format(dst))
            # Symlinks make this a mess
            try:
                os.rmdir(dst)
            except:
                try:
                    os.remove(dst)
                except:
                    print("ERROR: Could not delete {} for unknown reason".format(dst))            
        print("[+] Linking {} to {}".format(src, dst))
        try:
            os.symlink(src, dst)
        except:
            print("[!] ERROR: Could not link {} to {}, folder structure and permissions".format(src, dst))
    else:
        print("[!] ERROR: Cannot link {} - dir not found".format(src))
