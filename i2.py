########################################
# Second half of install script, will be merged
# Performs basic configuration and bootloader installation
#
########################################

#!/usr/bin/python
from urllib import request
import subprocess
import re
import time
import getpass

FG_WHITE='\u001b[37m'
FG_RED='\u001b[31m'
CHROOT = "arch-chroot /mnt "     # arch-chroot /mnt <cmd> to run commands in context of new install
TZ_REGION = "Australia"
TZ_CITY = "Sydney"
LOCALE = "en_US.UTF-8 UTF-8"
LANG="LANG=en_US.UTF-8"
HOST="lappy"
INITRAM_HOOKS = "HOOKS=(base udev autodetect keyboard keymap consolefont modconf block encrypt lvm2 filesystems fsck)"
INITRAM_FILES = "FILES=(/root/cryptlvm.keyfile)"
GRUB_CMDLINE = "GRUB_CMDLINE_LINUX=\"cryptdevice={}:cryptlvm cryptkey=rootfs:/root/cryptlvm.keyfile\"\n"
GRUB_CRYPT = "GRUB_ENABLE_CRYPTODISK=y\n"


def log(string):
    print(FG_RED + string + FG_WHITE)

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

enc_disk = input("Please enter the path to the encrypted partition: ")      # Not validated

log("[*] Installation commencing");
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
execute("cryptsetup -v luksAddKey {} /root/cryptlvm.keyfile".format(enc_disk), chroot=True)

log("[*] Configuring intram with encrypted boot")
write_file("{}\n{}".format(INITRAM_HOOKS, INITRAM_FILES), "/mnt/etc/mkinitcpio.conf")
execute("mkinitcpio -P", chroot=True)
execute("chmod 600 /mnt/boot/initramfs-linux*")

log("[*] Installing grub")
replace_in_file(".*GRUB_CMDLINE_LINUX=.*", GRUB_CMDLINE.format(enc_disk), "/mnt/etc/default/grub")
replace_in_file(".*GRUB_ENABLE_CRYPTODISK.*", GRUB_CRYPT, "/mnt/etc/default/grub")
execute("grub-install --target=x86_64-efi --efi-directory=/efi --bootloader-id=GRUB", chroot=True)
execute("grub-mkconfig -o /boot/grub/grub.cfg", chroot=True)

log("[*] Enabling services")
execute("systemctl enable lightdm", chroot=True)
execute("systemctl enable NetworkManager", chroot=True)

log("[#] All done!")
