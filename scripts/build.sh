#!/bin/bash

# Welborn Productions - Build
# ...A simpler build tool for js and sass.
# -Christopher Welborn 06-08-2015

# TODO: Modify /static/ dirs and builder.py so that "git pull" requires
#       no building on production.
appname="WpBuild"
appversion="0.0.1"
apppath="$(realpath "${BASH_SOURCE[0]}")"
appscript="${apppath##*/}"
appdir="${apppath%/*}"

# Whether to print extra information.
debug_mode=false
# Whether to ignore modification times.
forced_mode=false

dir_project="$appdir/.."
# Final home for minified files.
dir_out=~/dump/buildtest
dir_css="$dir_out/css"
dir_js="$dir_out/js"

# Path to closure.jar.
# TODO: Use this newer version always, no building will take place on the server.
closure_path="$dir_project/scripts/external/closure-v20150505.jar"

# Build sass include paths
sass_includes=("$dir_project/wp_main/static/sass")
declare -a sass_include_args
for sassinclude in "${sass_includes[@]}"
do
    sass_include_args+=("-I" "$sassinclude")
done

# These files will not be built with sass.
sass_ignore=("_welbornprod.scss")

# Default sass args.
sass_args=("--style" "compressed")

# These js files will not be minified.
js_ignore=('\.min\.' '-min\.' 'js/ace')
# Default closure args.
js_args=(
    "--compilation_level" "SIMPLE"
    "--warning_level" "QUIET"
    "--language_in" "ECMASCRIPT5"
)




function debug {
    if [[ $debug_mode == true ]]; then
        printf "%s\n" "$1"
    fi
}

function file_build {
    # Build a single file. File extension determines the builder.
    if [[ "$1" =~ \.js$ ]]; then
        js_build_file "$1"
    elif [[ "$1" =~ \.scss$ ]]; then
        sass_build_file "$1"
    else
        echo "Unknown file type: $1"
        return 1
    fi
}

function files_build {
    # Use file extension to build all files passed in.
    for filename in "${@}"
    do
        file_build "$filename"
    done
}

function is_modified {
    # Compare two files to see if the old one has been modified.
    if [[ ! -e "$2" ]]; then
        debug "File is new: $1"
        return 0
    fi
    local oldsecs=$(date --utc --reference="$1" +%s)
    local newsecs=$(date --utc --reference="$2" +%s)
    if [[ $oldsecs -gt $newsecs ]]; then
        debug "File has been modified: $1"
        return 0
    fi
    return 1
}

function js_build {
    if [[ ! -e "$closure_path" ]]; then
        echo "Unable to locate closure: $closure_path"
        return 1
    fi

    if [[ ! -d "$dir_js" ]]; then
        echo "Creating JS directory: $dir_js"
        mkdir -p "$dir_js"
    fi

    for jsfile in $dir_project/*/static/js/*.js
    do
        js_build_file "$jsfile"
    done
}

function js_build_file {
    # Build a single js file, passed in as an arg.
    local jsfile="$1"
    if [[ ! -e "$jsfile" ]]; then
        echo "File does not exist: $jsfile"
        return 1
    fi

    local relname="${jsfile##*..}"
    local relshortname="${relname##*/}"
    if js_is_ignored "$relshortname"; then
        debug "    Skipping ignored: $relshortname"
        return 0
    fi
    local outname="${relshortname%.*}.min.js"
    local outpath="$dir_out/js/$outname"
    if ! is_modified "$jsfile" "$outpath" && [[ $forced_mode == false ]]; then
        debug "    Skipping non-modified file: $relshortname"
        return 0
    fi
    if [[ $debug_mode == true ]]; then
        debug "Would've built js file: $relshortname -> $outpath"
        return 0
    fi

    printf "Building JS file: %-25s -> %s\n" "$relshortname" "$outpath"
    java -jar "$closure_path" "${js_args[@]}" --js "$jsfile" --js_output_file "$outpath"
}

function js_is_ignored {
    # Check to see if this is an ignored js file.
    local ignored
    for ignored in "${js_ignore[@]}"
    do
        if [[ "$1" =~ $ignored ]]; then
            return 0
        fi
    done
    return 1
}


# shellcheck disable=SC2120
function print_usage {
    if [[ -n "$1" ]]; then
        echo -e "\n$1\n"
    fi
    echo "
$appname v. $appversion

    Usage:
        $appscript -h | -v
        $appscript [-f] [-j | -s]

    Options:
        -f,--force    : Ignore modification times, and force building.
        -h,--help     : Show this message and exit.
        -j,--js       : Build javascript files.
        -s,--sass     : Build sass files.
        -v,--version  : Show version and exit.

    When no arguments are passed '-j -s' is used.
"
}


function sass_build {

    if [[ ! -d "$dir_css" ]]; then
        echo "Creating CSS directory: $dir_css"
        mkdir -p "$dir_css"
    fi

    for sassfile in $dir_project/*/static/sass/*.scss
    do
        sass_build_file "$sassfile"
    done
}

function sass_build_file {
    # Build a single sass file, passed in as an arg.
    local sassfile="$1"
    if [[ ! -e "$sassfile" ]]; then
        echo "File does not exist: $sassfile"
        return 1
    fi

    local relname="${sassfile##*..}"
    local relshortname="${relname##*/}"
    if sass_is_ignored "$relshortname"; then
        debug "    Skipping ignored: $relshortname"
        return 0
    fi
    local outname="${relshortname%.*}.min.css"
    local outpath="$dir_out/css/$outname"
    if ! is_modified "$sassfile" "$outpath" && [[ $forced_mode == false ]]; then
        debug "    Skipping non-modified file: $relshortname"
        return 0
    fi

    if [[ $debug_mode == true ]]; then
        debug "Would've built sass file: $relshortname -> $outpath"
        return 0
    fi

    printf "Building SASS file: %-25s -> %s\n" "$relshortname" "$outpath"
    sass "${sass_args[@]}" "${sass_include_args[@]}" "$sassfile" "$outpath"
}

function sass_is_ignored {
    # Check to see if this is an ignored sass file.
    local ignored
    for ignored in "${sass_ignore[@]}"
    do
        if [[ "$1" =~ $ignored ]]; then
            return 0
        fi
    done
    return 1
}

# Parse args
do_js=false
do_sass=false
declare -a infiles
for arg
do
    if [[ "$arg" =~ ^(-D)|(--debug)$ ]]; then
        debug_mode=true
    elif [[ "$arg" =~ ^(-f)|(--forced)$ ]]; then
        forced_mode=true
        debug "Forced mode, ignoring modification times."
    elif [[ "$arg" =~ ^(-h)|(--help)$ ]]; then
        print_usage # shellcheck disable=SC2119
        exit 0
    elif [[ "$arg" =~ ^(-v)|(--version)$ ]]; then
        echo -e "\n$appname v. $appversion\n"
        exit 0
    elif [[ "$arg" =~ ^(-j)|(--js)$ ]]; then
        do_js=true
    elif [[ "$arg" =~ ^(-s)|(--sass)$ ]]; then
        do_sass=true
    elif [[ "$arg" =~ ^[^-] ]]; then
        # Non argument, treat as file.
        infiles+=("$arg")
    fi
done

let infilelen=${#infiles[@]}
if [[ $infilelen -gt 0 ]]; then
    files_build "${infiles[@]}"
    exit
fi

if [[ $do_js == false ]] && [[ $do_sass == false ]]; then
    js_build
    sass_build
    exit
fi


if [[ $do_js == true ]]; then
    js_build
fi

if [[ $do_sass == true ]]; then
    sass_build
fi

