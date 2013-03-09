#!/bin/bash

# Cj's Aliases!

alias redit='gksudo gedit ' #root editor
alias rfiles='gksudo nautilus' #root browser
alias ls='ls -a --color=auto'
alias la='ls -Fa --color=auto --group-directories-first'
alias ll='ls -alh --group-directories-first --color=auto'
alias lt='tree -a --dirsfirst | less -W'
alias .='pwd'
alias ..='cd ..'
alias ...='cd ../..'
alias ....='cd /'
alias mkdir='mkdir -p' #prevents "clobbering" files
alias pwd='pwd -P' #show actual directory (not symlink)
alias cdsym='cd `pwd -P`' #leave symlink to actual directory
alias xmsg='DISPLAY=:0 xmessage -center '
alias snoop='cat /var/log/auth.log | grep "snoopy" | cut -d\" \" -f12'
alias snoopall='cat /var/log/auth.log | grep "snoopy"'
alias sshscan="nmap -v --host-timeout 2000 -p22 192.168.0.10-16 | grep -A2 'Interesting'"
alias cjprops='cd /home/cj/workspace/menuprops/;ls | tail'
alias cjmenuprops='cjprops'
alias cjscripts='cd /home/cj/scripts/;ls | tail'
	# ------------------------- THIRD-PARTY FUNCTIONS ------------------------------	

	# Find a file with a pattern in name:
	function ff() { find . -type f -iname '*'$*'*' -ls ; }

	# Find a file with pattern $1 in name and Execute $2 on it:
	function fe()
	{ find . -type f -iname '*'${1:-}'*' -exec ${2:-file} {} \;  ; }

	# Change Filename to lowercase...
	function lowercase()
	{
	    for file ; do
		filename=${file##*/}
		case "$filename" in
		*/*) dirname==${file%/*} ;;
		*) dirname=.;;
		esac
		nf=$(echo $filename | tr A-Z a-z)
		newname="${dirname}/${nf}"
		if [ "$nf" != "$filename" ]; then
		    mv "$file" "$newname"
		    echo "lowercase: $file --> $newname"
		else
		    echo "lowercase: $file not changed."
		fi
	    done
	}

	#Extract archive file (.zip/.tar/etc...)
	function extract()      
	{
	     if [ -f $1 ] ; then
		 case $1 in
		     *.tar.bz2)   tar xvjf $1     ;;
		     *.tar.gz)    tar xvzf $1     ;;
		     *.bz2)       bunzip2 $1      ;;
		     *.rar)       unrar x $1      ;;
		     *.gz)        gunzip $1       ;;
		     *.tar)       tar xvf $1      ;;
		     *.tbz2)      tar xvjf $1     ;;
		     *.tgz)       tar xvzf $1     ;;
		     *.zip)       unzip $1        ;;
		     *.Z)         uncompress $1   ;;
		     *.7z)        7z x $1         ;;
		     *)           echo "'$1' cannot be extracted via >extract<" ;;
		 esac
	     else
		 echo "'$1' is not a valid file"
	     fi
	}
	# Get Local IP adresses.
	function my_ip() 
	{
	    MY_IP=$(/sbin/ifconfig wlan0 | awk '/inet/ { print $2 } ' | \
	sed -e s/addr://)
	    MY_ISP=$(/sbin/ifconfig wlan0 | awk '/P-t-P/ { print $3 } ' | \
	sed -e s/P-t-P://)
	}
	# Display Local IP Address
	function showmyip()
	{
		echo "Gathering IP Address..."
		my_ip
		echo "IP: ${MY_IP}"
	}

	# Get current host related info.
	function ii()   
	{
	    echo -e "\nYou are logged on ${RED}$HOST"
	    echo -e "\nAdditionnal information:$NC " ; uname -a
	    echo -e "\n${RED}Users logged on:$NC " ; w -h
	    echo -e "\n${RED}Current date :$NC " ; date
	    echo -e "\n${RED}Machine stats :$NC " ; uptime
	    echo -e "\n${RED}Memory stats :$NC " ; free
	    my_ip 2>&- ;
	    echo -e "\n${RED}Local IP Address :$NC" ; echo ${MY_IP:-"Not connected"}
	    echo -e "\n${RED}ISP Address :$NC" ; echo ${MY_ISP:-"Not connected"}
	    echo -e "\n${RED}Open connections :$NC "; netstat -pan --inet;
	    echo
	}

	# print a question, return 0 for Yes, 1 for No
	function ask()          
	{
	    echo -n "$@" '[y/n] ' ; read ans
	    case "$ans" in
		y*|Y*) return 0 ;;
		*) return 1 ;;
	    esac
	}

	#---------------------------- CJ's FUNCTIONS -------------------------------
	# define a word	
	function define () 
	{
		if [ "${1}" = "" ] ; then
			echo "Usage: define dog"
		else
			lynx -dump -nonumbers -width=160 "http://dictionary.reference.com/browse/${1}" | grep -A15 "World English Dictionary"
		fi
	}

	# translate to spanish
	function spanish ()
	{
		if [ "${1}" = "" ] ; then
			echo "Usage: spanish dog"
		else
			lynx -dump -nonumbers -width=160 "http://spanish.dictionary.com/definition/${1}?src=en" | grep "${1} / "
		fi
	}

	# show this weeks weather
	function weatherweek ()
	{
		if [ "${1}" = "" ] ; then
			# echo "Usage: weatherweek [Your ZipCode]"
			lynx -dump -nonumbers -width=160 "http://weather.unisys.com/forecast.php?Name=35501" | grep -A30 'Forecast Summary'
		else
			lynx -dump -nonumbers -width=160 "http://weather.unisys.com/forecast.php?Name=${1}" | grep -A30 'Forecast Summary'
		fi
	}

	# show current weather
	function weather ()
	{
		if [ "${1}" = "" ] ; then
			# echo "Usage: weather 90210"
			lynx -dump -nonumbers -width=160 "http://weather.unisys.com/forecast.php?Name=35501" | grep -A13 'Latest Observation'
		else
			lynx -dump -nonumbers -width=160 "http://weather.unisys.com/forecast.php?Name=${1}" | grep -A13 'Latest Observation'
		fi
	}

	# make a dir, and cd to it
	function mkdircd () 
	{ 
			# mkdir -p "$@" && eval cd "\"\$$#\"" 
		if [ "${1}" = "" ] ; then
			echo "Usage: mkdircd myDir"
		else
			mkdir -p ${1}
			cd ${1}
		fi
	}


	#connect to ssh server by telnet, and get version
	function sshver ()
	{
		telnet ${1} 22 | grep "SSH"
		close
	}

	# Check Installation of package
	function checkinstall ()
	{
		if [ "${1}" = "" ] ; then
			echo "Usage: checkinstall packagename"
		else
			aptitude show ${1} | grep "State:"
		fi


	}

	#search for apt package
	function aptsearch ()
	{
		if [ "${1}" = "" ] ; then
			echo "Usage: aptsearch packagename"
		else
			dpkg -l *${1}*
		fi
	}

	# Change Dir, Print Dir, and List Contents...
	function kd ()
	{	
		if [ "${1}" = "" ] ; then
			echo "Usage: kd directory_name"
		else
			cd "${1}"
			pwd
			ls -Fa --group-directories-first --color=auto
		fi
	
	}

	# List All Cj's Functions
	function cjfunctions ()
	{
		echo "Cj's Functions:"
		echo "------------------------------------------------------------------------------"
		echo "ask [question]        - ask a question, and return answer (for scripts)"
		echo "checkinstall [pkg]    - check if a package is installed"
		echo "define [word]         - show definition of a word"
		echo "extract [file]        - auto-extract compressed archives"
		echo "fe [name] [action]    - find a file (\$1), and execute (\$2) on it"
		echo "ff [name]             - find a file with a pattern in the name"
		echo "ii                    - shows current internet information"
		echo "kd [dirname]          - change dir (cd), print dir (pwd), and list contents"
		echo "lowercase             - convert filenames in current dir to lowercase"
		echo "mkdircd [dirname]     - make a dir, and cd to it"
		echo "my_ip                 - save local ip address to \$MY_IP"
		echo "showmyip              - show current ip address (\$MY_IP)"
		echo "spanish [word]        - translate a word to spanish"
		echo "sshver [hostname]     - connect to host, and display SSH version"
		echo "weather [zipcode]     - show today's weather for zipcode (default=35501)"
		echo "weatherweek [zipcode] - show this week's weather for zipcode (default=35501)"
		echo "cjtest [?]            - cj's test function before final named function is made"
		echo "cjfunctions           - shows cj's list of functions in bash.alias.sh"
		echo "------------------------------------------------------------------------------"

	}
	# cj's function to test things (without damaging anything) 
	function cjtest ()
	{
		if [ "${1}" = "" ] ; then
			echo "argument 0"
		else
		 	echo "argument: ${1}"
		fi
	}

#Export 3rd Party Functions
export ff
export fe
export lowercase
export extract
export my_ip
export showmyip
export ii
export ask

#Export Cj's Functions
export cjtest
export cjfunctions

export define
export spanish
export weatherweek
export weather
export mkdircd
export sshver
export checkinstall
export kd

echo "                          Set ../etc/bash.alias.sh"


