# System-wide .bashrc file for interactive bash(1) shells.

# To enable the settings / commands in this file for login shells as well,
# this file has to be sourced in /etc/profile.

# If not running interactively, don't do anything
[ -z "$PS1" ] && return

# check the window size after each command and, if necessary,
# update the values of LINES and COLUMNS.
shopt -s checkwinsize

# set variable identifying the chroot you work in (used in the prompt below)
if [ -z "$debian_chroot" ] && [ -r /etc/debian_chroot ]; then
    debian_chroot=$(cat /etc/debian_chroot)
fi

# --------------------------- INITIALIZE/ COLORS --------------------
	# Define some colors first:
		red='\e[0;31m'
		RED='\e[1;31m'
		blue='\e[0;34m'
		BLUE='\e[1;34m'
		cyan='\e[0;36m'
		CYAN='\e[1;36m'
		  NC='\e[0m'              # No Color
               black='\e[0;30m' 
	    DARKGRAY='\e[1;30m'
           LIGHTBLUE='\e[1;34m'
               green='\e[0;32m'
          LIGHTGREEN='\e[1;32m'
              purple='\e[0;35m'
         LIGHTPURPLE='\e[1;35m'
	      YELLOW='\e[1;33m'
           lightgray='\e[0;37m'
               WHITE='\e[1;37m'
	# --> Nice. Has the same effect as using "ansi.sys" in DOS.
	
	#Set Hilite Color for 3rd Party Prompts
	if [[ "${DISPLAY%%:0*}" != "" ]]; then  
	    HILIT=${red}   # remote machine: prompt will be partly red
	else
	    HILIT=${cyan}  # local machine: prompt will be partly cyan
	fi


# ----------------------------- WELCOME ------------------------------
# Looks best on a terminal with black background.....
	#Welcome, bash version
	echo -e "${BLUE}Bash ${RED}${BASH_VERSION%.*} ${CYAN}   Welcome! ${RED}${NC}\n"

	#Show Date
	date
	echo " "

	#Show fortune
	if [ -x /usr/games/fortune ]; then
	    /usr/games/fortune -a    # Makes our day a bit more fun.... :-)
	fi
	echo " "

	#Setup Exit Message
	function _exit()        # Function to run upon exit of shell.
	{
	    echo -e "${RED}Goodbye...${NC}"
	}
	#Trap/Set Exit Function
	trap _exit EXIT

# ---------------------------- PROMPT FUNCTIONS -------------------------

# v--------------------------------------------------ORIGINAL PROMPT HERE ----------------]
# set a fancy prompt (non-color, overwrite the one in /etc/profile)
#PS1='${debian_chroot:+($debian_chroot)}\u@\h:\w\$ '
# ^--------------------------------------------------ORIGINAL PROMPT HERE ----------------]


# Following simple/default prompt function from original simple/fancy prompts...
	function simpleprompt()
	{
		PS1='${debian_chroot:+($debian_chroot)}\u@\h:\w\$ '
	}

	function defaultprompt()
	{
		PS1='${debian_chroot:+($debian_chroot)}\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '

	}

# Following 3rd party 'Power Prompt' & 'Fast Prompt' added by Cj 
	function fastprompt()
	{
	    unset PROMPT_COMMAND
	    case $TERM in
 	       *term | rxvt )
		    PS1="${HILIT}[\h]$NC \W > \[\033]0;\${TERM} [\u@\h] \w\007\]" ;;
		linux )
		    PS1="${HILIT}[\h]$NC \W > " ;;
        	*)
		    PS1="[\h] \W > " ;;
	    esac
	}
	_powerprompt()
	{
    		LOAD=$(uptime|sed -e "s/.*: \([^,]*\).*/\1/" -e "s/ //g")
	}

	function powerprompt()
	{

	    PROMPT_COMMAND=_powerprompt
	    case $TERM in
	        *term | rxvt  )
	            PS1="${HILIT}[\A - \$LOAD]$NC\n[\u@\h \#] \W > \
	                 \[\033]0;\${TERM} [\u@\h] \w\007\]" ;;
	        linux )
	            PS1="${HILIT}[\A - \$LOAD]$NC\n[\u@\h \#] \W > " ;;
	        * )
	            PS1="[\A - \$LOAD]\n[\u@\h \#] \W > " ;;
	    esac
	}
# Following prompt created by Cj...
	function cjprompt()
	{
		#PROMPT_COMMAND = _powerprompt
	 	PS1="${LIGHTBLUE}\u${NC}:${BLUE}\W ${NC}\$ "
	}

# Use Cj's Preferred Prompt! <--------------------------------PROMPT CHOICE HERE ----------]
	cjprompt

# Commented out, don't overwrite xterm -T "title" -n "icontitle" by default.
# If this is an xterm set the title to user@host:dir
#case "$TERM" in
#xterm*|rxvt*)
#    PROMPT_COMMAND='echo -ne "\033]0;${USER}@${HOSTNAME}: ${PWD}\007"'
#    ;;
#*)
#    ;;
#esac

# enable bash completion in interactive shells
if [ -f /etc/bash_completion ] && ! shopt -oq posix; then
    . /etc/bash_completion
fi

# sudo hint
if [ ! -e "$HOME/.sudo_as_admin_successful" ]; then
    case " $(groups) " in *\ admin\ *)
    if [ -x /usr/bin/sudo ]; then
	cat <<-EOF
	To run a command as administrator (user "root"), use "sudo <command>".
	See "man sudo_root" for details.
	
	EOF
    fi
    esac
fi

# if the command-not-found package is installed, use it
if [ -x /usr/lib/command-not-found -o -x /usr/share/command-not-found ]; then
	function command_not_found_handle {
	        # check because c-n-f could've been removed in the meantime
                if [ -x /usr/lib/command-not-found ]; then
		   /usr/bin/python /usr/lib/command-not-found -- $1
                   return $?
                elif [ -x /usr/share/command-not-found ]; then
		   /usr/bin/python /usr/share/command-not-found -- $1
                   return $?
		else
		   return 127
		fi
	}
fi

# Add Cj's Aliases!
	if [ -f /etc/bash.alias.sh ]; then
	    echo "Cj's Functions/Aliases:"
	    . /etc/bash.alias.sh
 	else
	    echo "                        Not Set!"
	    echo "                        Can't Find: /etc/bash.alias.sh"
	fi

	


# Go Home Cj!
	echo "_____________________________________"
	echo " "
	echo " "
	cd /home/cj
