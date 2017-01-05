#!/bin/bash

# ...Refreshes the entire application.
#    Builds files during local development using build.sh
#    Collects static files, admin css, and restarts apache using wprefresh.py
# -Christopher Welborn 06-08-2015
appname="restart"
appversion="0.0.2"
apppath="$(readlink -f "${BASH_SOURCE[0]}")"
appscript="${apppath##*/}"
appdir="${apppath%/*}"

wplogfile="$(readlink -f "${appdir}/../welbornprod.log")"
snd_success="/usr/share/sounds/KDE-Sys-App-Positive.ogg"
snd_failure="/usr/share/sounds/KDE-Sys-App-Negative.ogg"

if [[ "$(hostname)" =~ webfaction ]]; then
    production=true
else
    production=false
fi

function clear_log_file {
    # Clear the log file for welbornprod.
    [[ -e "$wplogfile" ]] || {
        echo_err "Log file not found: $wplogfile"
        return 1
    }
    echo "" > "$wplogfile" || {
        echo_err "Unable to write to log file: $wplogfile"
        return 1
    }
    echo "Log file cleared: $wplogfile"
    return 0
}

function echo_err {
    # Echo to stderr.
    echo -e "$@" 1>&2
}

function fail {
    # Print a message to stderr and exit with an error status code.
    echo_err "$@"
    exit 1
}

function fail_usage {
    # Print a usage failure message, and exit with an error status code.
    print_usage "$@"
    exit 1
}

function print_usage {
    # Show usage reason if first arg is available.
    [[ -n "$1" ]] && echo_err "\n$1\n"

    echo "$appname v. $appversion

    Usage:
        $appscript -h | -H | -L | -v
        $appscript [-L] [wprefresh_args...]

    Options:
        wprefresh_args  : Arguments for wprefresh.py.
        -h,--help       : Show this message and exit.
        -H,--HELP       : Show WpRefresh help and exit.
        -L,--clearlog   : Clear the log file before restarting.
        -Log--logonly   : Clear the log and exit.
        -v,--version    : Show version and exit.
    "
}


declare -a userargs
declare -a userflags

for arg; do
    case "$arg" in
        "-h" | "--help")
            print_usage ""
            exit 0
            ;;
        "-H" | "--HELP")
            python3 "${appdir}/wprefresh.py" --help
            exit
            ;;
        "-L" | "--clearlog")
            clear_log_file || exit 1
            ;;
        "-Log" | "--logonly")
            clear_log_file
            exit
            ;;
        "-v" | "--version")
            echo -e "$appname v. $appversion\n"
            exit 0
            ;;
        -*)
            userflags+=("$arg")
            ;;
        *)
            userargs+=("$arg")
    esac
done

if [[ $production == false ]]; then
    echo "Running build.sh for development..."
    bash "$appdir/build.sh"
fi

if python3 "$appdir/wprefresh.py" "${userflags[@]}" "${userargs[@]}"; then
    [[ -e "$snd_success" ]] && play "$snd_success" &>/dev/null
    printf "\nServer restarted: %s\n" "$(date '+%A, %b. %e [%I:%M:%S%P]')"
    exit 0
fi

[[ -e "$snd_failure" ]] && play "$snd_failure" &>/dev/null
exit 1
