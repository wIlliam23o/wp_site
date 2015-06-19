#!/bin/bash

# ...Refreshes the entire application.
#    Builds files during local development using build.sh
#    Collects static files, admin css, and restarts apache using wprefresh.py
# -Christopher Welborn 06-08-2015
appname="WpRefresh"
appversion="0.0.1"
apppath="$(readlink -f "${BASH_SOURCE[0]}")"
appscript="${apppath##*/}"
appdir="${apppath%/*}"

if [[ "$(hostname)" =~ webfaction ]]; then
    production=true
else
    production=false
fi

function print_usage {
    echo "
$appname v. $appversion

    Usage:
        $appscript -h | -H | -v
        $appscript [wprefresh_args...]

    Options:
        wprefresh_args  : Arguments for wprefresh.py.
        -h,--help       : Show this message and exit.
        -H,--HELP       : Show WpRefresh help and exit.
        -v,--version    : Show version and exit.
"
}

# Parse args.
for arg
do
    if [[ "$arg" =~ ^(-h)|(--help)$ ]]; then
        print_usage
        exit 0
    elif [[ "$arg" =~ ^(-H)|(--HELP)$ ]]; then
        python3 "$appdir/wprefresh.py" --help
        exit 0
    elif [[ "$arg" =~ ^(-v)|(--version)$ ]]; then
        echo -e "\n$appname v. $appversion\n"
        exit 0
    fi
done

if [[ $production == false ]]; then
    echo "Running build.sh for development..."
    bash "$appdir/build.sh"
fi

python3 "$appdir/wprefresh.py" "$@"

