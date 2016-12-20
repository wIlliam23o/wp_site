#!/bin/bash

# Runs `vulture` on non templatetags/settings files.
# -Christopher Welborn 12-19-2016
appname="vulture_test"
appversion="0.0.1"
apppath="$(readlink -f "${BASH_SOURCE[0]}")"
appscript="${apppath##*/}"
# appdir="${apppath%/*}"

if ! hash vulture; then
    printf "\nCannot find \`vulture\` executable, install it with \`pip\`.\n" 1>&2
    exit 1
fi

script_paths=(*.py */*.py **/*.py)
exclude_paths=(
    "wp_main/settings.py"
    "projects/static/files"
    "misc/static/files"
    "wp_main/templatetags"
)

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

function get_exclude_arg {
    # Build a vulture --exclude string from $exclude_paths.
    local excludestr
    excludestr="$(printf "%s," "${exclude_paths[@]}")"
    # Remove last comma.
    printf "%s" "${excludestr:0:-1}"
}

function print_usage {
    # Show usage reason if first arg is available.
    [[ -n "$1" ]] && echo_err "\n$1\n"

    echo "$appname v. $appversion

    Runs \`vulture\` on WelbornProd scripts.

    Usage:
        $appscript -h | -v
        $appscript [-a] [-m] [-M] [-n] [-s] [-u] [FILE...]

    Options:
        FILE             : File to test with vulture.
                           Default: All
        -a,--admin       : Test admin-related files.
        -h,--help        : Show this message.
        -m,--models      : Test model files.
        -M,--middleware  : Test middleware files.
        -n,--normal      : Test normal files.
        -s,--scripts     : Test utility script files.
        -u,--urls        : Test urls files.
        -v,--version     : Show $appname version and exit.

    The default action is to list all file types.
    "
}

declare -a userpaths
do_admin=0
do_middleware=0
do_models=0
do_normal=0
do_scripts=0
do_urls=0
do_all=1
for arg; do
    case "$arg" in
        "-a" | "--admin")
            do_admin=1
            do_all=0
            ;;
        "-h" | "--help")
            print_usage ""
            exit 0
            ;;
        "-m" | "--models")
            do_models=1
            do_all=0
            ;;
        "-M" | "--middleware")
            do_middleware=1
            do_all=0
            ;;
        "-n" | "--normal")
            do_normal=1
            do_all=0
            ;;
        "-s" | "--scripts")
            do_scripts=1
            do_all=0
            ;;
        "-u" | "--urls")
            do_urls=1
            do_all=0
            ;;
        "-v" | "--version")
            echo -e "$appname v. $appversion\n"
            exit 0
            ;;
        -*)
            fail_usage "Unknown flag argument: $arg"
            ;;
        *)
            userpaths+=("$arg")
    esac
done

((${#userpaths[@]} == 0)) && userpaths+=("${script_paths[@]}")
((${#userpaths[@]} == 0)) && fail "No script files found."

total=0
while IFS= read -r line; do
    is_admin=0
    [[ "$line" =~ /admin.py: ]] && is_admin=1
    is_middleware=0
    [[ "$line" =~ middleware/ ]] && is_middleware=1
    is_models=0
    [[ "$line" =~ /models.py: ]] && is_models=1
    is_script=0
    [[ "$line" =~ scripts/ ]] && is_script=1
    is_urls=0
    [[ "$line" =~ /urls.py: ]] && is_urls=1
    is_normal="$((!is_admin && !is_models && !is_urls))"
    print_it=0
    if ((do_all)); then
        print_it=1
    elif ((do_admin && is_admin)); then
        print_it=1
    elif ((do_middleware && is_middleware)); then
        print_it=1
    elif ((do_models && is_models)); then
        print_it=1
    elif ((do_scripts && is_script)); then
        print_it=1
    elif ((do_urls && is_urls)); then
        print_it=1
    elif ((do_normal && is_normal)); then
        print_it=1
    fi
    if ((print_it)); then
        printf "%s\n" "$line"
        let total+=1
    fi
done < <(vulture "--exclude=$(get_exclude_arg)" "${userpaths[@]}")

printf "\nErrors found: %s\n" "$total"
# No lines means no errors.
exit $total
