#!/bin/bash

# A 'pastebin_helper' command for BPython.
# Pastes to welbornprod.com/paste using the wppaste tool, with some
# custom settings (title, author, private, etc.)
# -Christopher Welborn 01-04-2016
appname="WpPaste - BPython Helper"
appversion="0.0.1"
apppath="$(readlink -f "${BASH_SOURCE[0]}")"
appscript="${apppath##*/}"
appdir="${apppath%/*}"


function print_usage {
    # Show usage reason if first arg is available.
    [[ -n "$1" ]] && echo -e "\n$1\n"

    echo "$appname v. $appversion

    Usage:
        $appscript -h | -v

    Options:
        -h,--help     : Show this message.
        -v,--version  : Show $appname version and exit.
    "
}


declare -a nonflags

for arg; do
    case "$arg" in
        "-h"|"--help" )
            print_usage ""
            exit 0
            ;;
        "-v"|"--version" )
            echo -e "$appname v. $appversion\n"
            exit 0
            ;;
        -*)
            print_usage "Unknown flag argument: $arg"
            exit 1
            ;;
        *)
            nonflags=("${nonflags[@]}" "$arg")
    esac
done

# wppaste will accept stdin input from bpython for the paste.
# see wppaste --help for options.
wppaste -p -t "BPython Session" -a "Cj" -l "Python"
