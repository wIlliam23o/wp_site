#!/bin/bash

# hopefully this saves some typing, instead of writing:
# python scripts/wprefresh.py arg1 arg2
# I can write: ./wrun wprefresh arg1 arg2
#     or just: ./wrun wpstats
#


# script directory to use
scriptdir="scripts/"

function print_usage () {
    printf "\nusage: %s <scriptname> [arguments]..." "${0}"
    printf "\n runs: python ${scriptdir}scriptname.py [arguments]...\n"
    exit 0
    }

function print_fail () {
	# prints a message and fails with exit code 1
	printf "$*"
	exit 1
	}

function list_script_type () {
	# list a certain file extension in the scripts dir.
	# ex: list_script_type ".py"
	for scriptname in ${scriptdir}*$1
	do
		if [ "${scriptname%__init__*}" != "${scriptdir}" ]; then
			scriptname="${scriptname#$scriptdir*}"
			printf "    %s\n" "$scriptname"
		fi
	done
}

function list_python_scripts () {
	printf "\ncurrent python scripts:\n"
	list_script_type ".py"
}

function list_bash_scripts () {
	printf "\ncurrent bash scripts:\n    (..incompatible with ${0})\n"
	list_script_type ".sh"
}

function list_scripts () {
	# list command. shows python and bash scripts in scripts dir.
	list_python_scripts
	echo
	list_bash_scripts
	echo
	exit 0
}


# test scriptdir
if [ ! -d "${scriptdir}" ]; then
    print_fail "\nscript dir not found!: ${scriptdir}\n"
fi

# save original scriptname passed for later
scriptarg="${1}"
if  [ -z $scriptarg ] || [ "${scriptarg}" == "-h" ] || [ "${scriptarg}" == "--help" ]; then
    print_usage
fi

# test for list command
if [ "${scriptarg}" == "list" ] || [ "${scriptarg}" == "-l" ] || [ "${scriptarg}" == "--list" ]; then
	list_scripts
fi

scriptname=$scriptarg
# fix scriptname extension if needed.
if [ "${scriptname#*.}" != "py" ]; then
    # add extension
    scriptname="${scriptname}.py"
fi
# fix script dir if needed
if [ "${scriptname%$scriptdir*}" != "" ]; then
    # add script dir
    scriptname="${scriptdir}${scriptname}"
fi

# TEST filename
if [ ! -f "${scriptname}" ]; then
    print_fail "\ncan't find the script: ${scriptname}\n"
fi

# Build argument string (remove previous scriptname)
args=""
for argument
do
    if [ "$argument" != "$scriptarg" ] && [ "$argument" != "${0}" ]; then
        if [ "${args}" == "" ]; then
            args="${argument}"
        else
            args="${args} ${argument}"
        fi
    fi
done

# run with or without args (dont add extra space with no args)
if [ "${args}" != "" ]; then
    scriptcmd="${scriptname} ${args}"
else
    scriptcmd="${scriptname}"
fi

# Run it
printf "running script: %s\n" "${scriptcmd}"
python3 ${scriptcmd}
