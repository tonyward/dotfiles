########################################
#                                      #
#                                      #
#        install.py - Tony Ward        #
#                                      #
#   Installs Arch Linux how I like it  #
#                                      #
#                                      #
########################################

# Partition Scheme:
#       LVM on LUKS with encrypted efi partition
#       2 physical partitions - efi=512M, LUKS=rest of disk
#       3 LVM partitions on LUKS container - swap, root, home
#           Default, 16G, 128G, Rest of disk. Customisable

#!/usr/bin/python
from urllib import request
from install_util import *
import subprocess
import re
import time
import getpass

# String constants for log coloring
FG_WHITE='\u001b[37m'
FG_RED='\u001b[31m'

# Installation packages for pacstrap
BASE_PKG = "base base-devel linux linux-firmware lvm2 grub efibootmgr"
INTEL_PKG = "intel-ucode"
UTIL_PKG = "vim networkmanager git go"
DISP_PKG = "i3-gaps lightdm lightdm-gtk-greeter xorg-server"

# Configuration constants
TZ_REGION = "Australia"
TZ_CITY = "Sydney"
LOCALE = "en_US.UTF-8 UTF-8"
LANG="LANG=en_US.UTF-8"
HOST="lappy"
INITRAM_HOOKS = "HOOKS=(base udev autodetect keyboard keymap consolefont modconf block encrypt lvm2 filesystems fsck)"
INITRAM_FILES = "FILES=(/root/cryptlvm.keyfile)"
GRUB_CMDLINE = "GRUB_CMDLINE_LINUX=\"cryptdevice={}:cryptlvm cryptkey=rootfs:/root/cryptlvm.keyfile\"\n"
GRUB_CRYPT = "GRUB_ENABLE_CRYPTODISK=y\n"

# String to execute commangs in arch-chroot
CHROOT = "arch-chroot /mnt "



log("[*] Install commencing")

log("[*] Checking internet connection")
if not has_network():
    log("[!] No Internet!")
    log("Connect to internet first: iwctl station <wlan> connect <SSID>")
    exit()

log("[+] internet connection good!")
exit()


# Get a list of all avaliable disks for install 
cmd = 'lsblk -p'.split(' ')     # -p gives absolute path
proc = subprocess.run(cmd, stdout=subprocess.PIPE)
result = proc.stdout.decode('utf-8')
disks = []
diskSizes = []
for line in result.split('\n'):
    # Get name and size of each line that has "disk" as type
    # lsblk output: <NAME>  <MAJ:MIN>   <RM>    <SIZE>  <RO>    <TYPE>    <MOUNTPOINTS>
    m = re.match(r'^([^\s]*)\s*[^\s]*\s*[^\s]*\s*([^\s]*).*disk.*$', line)
    if m is not None:
        disks.append(m.group(1))
        diskSizes.append(m.group(2))

# Select install location
time.sleep(1)
subprocess.run('clear')
for i in range(len(disks)):
    print("{}\t{}".format(disks[i], diskSizes[i]))

valid = False
install_disk = ""
while not valid:
    install_disk = input("Please select a disk to install to: ")
    if install_disk in disks:
        valid = True
    else:
        log("[!] Invalid disk selected, please try again")

# Create physical disk partitions
subprocess.run('clear')
log("[*] Clearing any existing partition table")
cmd = "sfdisk --delete {}".format(install_disk).split(' ')
subprocess.run(cmd)
log("[*] Creating efi and LUKS partitions")
cmd = "sfdisk {}".format(install_disk).split(' ')
cmd_input = ", 512M, U\n,,"     # sfdisk stdin - 1 line per partition <start>, <size>, <type> - blank is default, U is efi 
subprocess.run(cmd, input=cmd_input, encoding='ascii') # 512M efi partition, LUKS uses rest of disk

# Slight assumpyion, first volume made is <disk>+p1, second is <disk>+p2
efi_partition = install_disk + "p1"
luks_partition = install_disk + "p2"

# Encrypt LUKS partition
time.sleep(1)
subprocess.run('clear')
log("[*] Encrpyting LUKS partition")
cmd = "cryptsetup luksFormat --type luks1 {}".format(luks_partition).split(' ')     # use luks1 for grub compatability
subprocess.run(cmd)
log("[*] Opening LUKS container to partition with LVM")
cmd = "cryptsetup open {} cryptlvm".format(luks_partition).split(' ')
subprocess.run(cmd)

# Below code is not working, calling cryptsetup and passing control works fine for now
#matching_codes = False
#while not matching_codes:
#    pass1 = input("Please enter your encryption key:")
#    pass2 = input("Please reenter your encryption key:")
#    if pass1 != pass2:
#        print("[!] Encryption keys do not match, try again")
#    else:
#        matching_codes = True
#subprocess.run(["cryptsetup", "luksFormat", "--type", "luks1", partitions["LUKS"]]
#                input="YES\n{}\n{}\n".format(pass1, pass1), encoding="ascii")     # Encrypt with LUKS1 for Grub compatability

# Get partition sizes from user
# Default to 16G swap, 128G root, remainder home
# This does not valid that the disk is large enough
time.sleep(1)
subprocess.run("clear")
log("[*] Creating LVM partitions")
swap_size = (input("Please eneter the size of the swap partition (default 16G): ") or "16G") 
root_size = (input("Please eneter the size of the root partition (default 128G): ") or "128G") 
home_size = "100%FREE"

# Create logical disk partitions
subprocess.run(["pvcreate", "/dev/mapper/cryptlvm"])
subprocess.run(["vgcreate", "vg0", "/dev/mapper/cryptlvm"])
subprocess.run(["lvcreate", "-L", swap_size, "vg0", "-n", "swap"])
subprocess.run(["lvcreate", "-L", root_size, "vg0", "-n", "root"])
subprocess.run(["lvcreate", "-l", "100%FREE", "vg0", "-n", "home"])     # home gets all space not used by swap or root

# Format partitions
log("[*] Formatting partitions")
subprocess.run(["mkfs.ext4", "/dev/vg0/root"])
subprocess.run(["mkfs.ext4", "/dev/vg0/home"])
subprocess.run(["mkswap", "/dev/vg0/swap"])
subprocess.run(["mkfs.fat", "-F32", efi_partition])

# Mount partitions
log("[*] Mounting partitions")
subprocess.run(["mount", "/dev/vg0/root", "/mnt"])
subprocess.run(["mkdir", "/mnt/efi"])
subprocess.run(["mkdir", "/mnt/home"])
subprocess.run(["mount", "/dev/vg0/home", "/mnt/home"])
subprocess.run(["mount", efi_partition, "/mnt/efi"])
subprocess.run(["swapon", "/dev/vg0/swap"])

# Install arch
packages = "{} {} {} {}".format(BASE_PKG, INTEL_PKG, UTIL_PKG, DISP_PKG)
cmd = "pacstrap /mnt {}".format(packages).split(' ')
subprocess.run(cmd)

log("[*] Generating fstab");
cmd = "genfstab -U /mnt"
execute(cmd, outfile="/mnt/etc/fstab")

log("[*] Setting timezone")
cmd = "ln -sf /usr/share/zoneinfo/{}/{}".format(TZ_REGION, TZ_CITY)
execute(cmd, chroot=True)
execute("hwclock --systohc", chroot=True)

log("[*] Configuring localization settings")
write_file(LOCALE, "/mnt/etc/locale.gen")
write_file(LANG, "/mnt/etc/locale.gen")
execute("locale-gen", chroot=True)

log("[*] Configuring network hosts")
write_file(HOST, "/mnt/etc/hostname")
hosts = "127.0.0.1\tlocalhost\n127.0.0.1\t{}".format(HOST)
write_file(hosts, "/mnt/etc/hosts")

log("[*] Configuring users")
log("[+] Set root password")
execute("passwd root", chroot=True)
sudo_user = input("Please enter username for sudo user: ")

execute("useradd -mG wheel {}".format(sudo_user), chroot=True)
log("[+] Set {} password".format(sudo_user))
execute("passwd {}".format(sudo_user), chroot=True)

sudoers = "root ALL=(ALL:ALL) ALL\n" + "%wheel ALL=(ALL:ALL) ALL\n" + "@includedir /etc/sudoers.d"
write_file(sudoers, "/mnt/etc/sudoers")

log("[*] Creating grub encryption key")
execute("dd bs=512 count=4 if=/dev/random of=/root/cryptlvm.keyfile iflag=fullblock", chroot=True)
execute("chmod 000 /root/cryptlvm.keyfile", chroot=True)
execute("cryptsetup -v luksAddKey {} /root/cryptlvm.keyfile".format(luks_partition), chroot=True)

log("[*] Configuring intram with encrypted boot")
write_file("{}\n{}".format(INITRAM_HOOKS, INITRAM_FILES), "/mnt/etc/mkinitcpio.conf")
execute("mkinitcpio -P", chroot=True)
execute("chmod 600 /mnt/boot/initramfs-linux*")

log("[*] Installing grub")
replace_in_file(".*GRUB_CMDLINE_LINUX=.*", GRUB_CMDLINE.format(luks_partition), "/mnt/etc/default/grub")
replace_in_file(".*GRUB_ENABLE_CRYPTODISK.*", GRUB_CRYPT, "/mnt/etc/default/grub")
execute("grub-install --target=x86_64-efi --efi-directory=/efi --bootloader-id=GRUB", chroot=True)
execute("grub-mkconfig -o /boot/grub/grub.cfg", chroot=True)

log("[*] Enabling services")
execute("systemctl enable lightdm", chroot=True)
execute("systemctl enable NetworkManager", chroot=True)

log("[#] All done!")
