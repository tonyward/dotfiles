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
			if [ ! -f $src ]; then
				echo "[-] Error linking $src to $dst - source file not found"
			else
				if [ -f $dst ]; then
					echo "[-] $dst already exists - deleting first"
					rm $dst
				fi
				ln -s $src $dst
				if [ ! -f $dst ]; then
					echo "[-] Error linking $src to $dst - destination file does not exist after link"
				else
					echo "[+] Linked $src to $dst"
				fi
			fi

		fi
	done < ./config
fi
