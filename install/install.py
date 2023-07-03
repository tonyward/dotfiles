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

# Positions of useful information from lsblk command
# lsblk output: <NAME>  <MAJ:MIN>   <RM>    <SIZE>  <RO>    <TYPE>    <MOUNTPOINTS>
NAME_INDEX = 0
SIZE_INDEX = 3
TYPE_INDEX = 5

# Input string to create 2 partitions with sfdisk
# Format position is for efi partition size
# sfdisk stdin - 1 line per partition <start>, <size>, <type> - blank is default, U is efi 
SFDISK_PART = ", {}, U\n,,"

def main():
    log("[*] Install commencing")

    if not has_network():
        exit()
    time.sleep(1)

    install_disk = select_disk() 

    partition_disk_phys(install_disk)
    # Slight assumption, first volume made is <disk>+p1, second is <disk>+p2
    efi_partition = install_disk + "p1"
    luks_partition = install_disk + "p2"

    encrypt_partition(luks_partition)
    
    create_lvm_on_luks()
    
    partitions = {"root": "/dev/vg0/root", "home": "/dev/vg0/home", 
                  "swap": "/dev/vg0/swap", "efi": efi_partition}
    format_partitions(partitions)


def select_disk():
    # Get a list of all avaliable disks 
    proc = execute("lsblk -p")
    result = proc.stdout

    disks = []
    diskSizes = []
    for line in result.splitlines():
        line = line.split()
        if line[TYPE_INDEX] == "disk":
            disks.append(line[NAME_INDEX])
            diskSizes.append(line[SIZE_INDEX])

    # Display available disks and select disk to install to
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
    return install_disk

# Creates 2 partitions, efi and LUKS encrypted
def partition_disk_phys(disk, efi_size="512M"):
    # Create physical disk partitions
    log("[*] Clearing any existing partition table")
    execute("sfdisk --delete {}".format(disk))

    log("[*] Creating efi and LUKS partitions")
    cmd_input = SFDISK_PART.format(efi_size)
    execute("sfdisk {}".format(disk), input=cmd_input)

def encrypt_partition(partition, openas="cryptlvm"):
    log("[*] Encrpyting {}".format(partition))
    execute("cryptsetup luksFormat --type luks1 {}".format(partition))  # Use luks1 for grub compatability

    if openas != "":
        log("[*] Opening LUKS container to partition with LVM")
        execute("cryptsetup open {} {}".format(partition, openas))

def create_lvm_on_luks(luks="cryptlvm", vol_grp="vg0", swap_size="16G", root_size="128G"):
    log("[*] Creating LVM volumes")
    execute("pvcreate /dev/mapper/{}".format(luks))
    execute("vgcreate {} /dev/mapper/{}".format(vol_grp, luks))
    execute("lvcreate -L {} {} -n swap".format(swap_size, vol_grp))
    execute("lvcreate -L {} {} -n root".format(root_size, vol_grp))
    # home gets all space not used by swap or root
    execute("lvcreate -l 100%FREE {} -n home".format(vol_grp))

def format_partitions(partitions):
    log("[*] Formatting partitions")
    if not has_part_paths(partitions)
        exit()

    execute("mkfs.ext4 {}".format(partitions["root"]))
    execute("mkfs.ext4 {}".format(partitions["home"]))
    execute("mkswap {}".format(partitions["swap"]))
    execute("mkfs.fat -F32 {}".format(partitions["efi"]))

def mount_partitions(partitions, mnt_pnt="/mnt"):
    log("[*] Mounting partitions")
    if not has_part_paths(partitions)
        exit()
    
    execute("mount {} {}".format(partitions["root"], mnt_pnt))
    execute("mkdir {}/efi".format(mnt_pnt))
    execute("mkdir {}/home".format(mnt_pnt))
    execute("mount {} {}/efi".format(partitions["efi"], mnt_pnt))
    execute("mount {} {}/home".format(partitions["home"], mnt_pnt))
    execute("swapon {}".format(partitions["swap"]))

# Checks that partitions contains a path for root, home, swap and efi
def has_part_paths(partitions):
    for part in ["root", "home", "swap", "efi"]:
        if part not in partitions:
            log("[!] Path not provided for all partitions")
            return False
    return True

if __name__ == "__main__":
    main()

exit()

# Format partitions

# Mount partitions
log("[*] Mounting partitions")

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
