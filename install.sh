#!/bin/bash

if [ ! -f ./config ]; then
	echo -e "[!] ERROR: config file not found\nexiting..."
	exit
else
	echo "[+] config loaded - linking dotfiles"
	while IFS= read -r line
	do
		if [[ ! $line =~ ^# ]]; then
			src=`pwd`/`echo $line | cut -f1 -d' '`
			dst=`echo $line | cut -f2 -d' '`
			if [ ! -d $src ]; then
				echo "[-] Error linking $src to $dst - source directory not found"
			else
				if [ -d $dst ]; then
					echo "[-] $dst already exists - deleting first"
					rm -rf $dst
				fi
				ln -s $src $dst
				if [ ! -d $dst ]; then
					echo "[-] Error linking $src to $dst - destination directory does not exist after link"
				else
					echo "[+] Linked $src to $dst"
				fi
			fi

		fi
	done < ./config
fi
