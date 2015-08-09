#!/bin/bash

# Welborn Productions - Build
# ...A simpler build tool for js and sass.
# -Christopher Welborn 06-08-2015

# TODO: Modify /static/ dirs and builder.py so that a "git pull" requires
#       no building on production.
appname="WpBuild"
appversion="0.1.2"
apppath="$(readlink -f "${BASH_SOURCE[0]}")"
appscript="${apppath##*/}"
appdir="${apppath%/*}"

# Whether to print extra information.
debug_mode=false
# Whether to ignore modification times.
forced_mode=false

dir_project="$appdir/.."
# Final home for minified files.
dir_out="$dir_project/built"
if [[ ! -e "$dir_out" ]]; then
    echo "Output directory is missing: $dir_out"
    exit 1
fi
# Sub directories for each type of minified file.
dir_css="$dir_out/css"
dir_js="$dir_out/js"


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

# Path to closure.jar.
closure_path="$dir_project/scripts/external/closure.jar"
if [[ ! -e "$closure_path" ]]; then
    echo "Unable to locate closure compiler: $closure_path"
    has_closure=false
else
    has_closure=true
fi

# These js files will not be minified.
js_ignore=('\.min\.' '-min\.' 'js/ace')
# Default closure args.
js_args=(
    "--compilation_level" "SIMPLE"
    "--warning_level" "QUIET"
    "--language_in" "ECMASCRIPT5"
)


function build_file {
    # Build a single file. File extension determines the builder.
    case "$1" in
        *.js)
            build_js_file "$1"
            ;;
        *.scss)
            build_sass_file "$1"
            ;;
        *)
            echo "Unknown file type: $1"
            return 1
            ;;
    esac
}

function build_files {
    # Use file extension to build all files passed in.
    for filename in "${@}"
    do
        build_file "$filename"
    done
}

function build_js {
    [[ $has_closure == true ]] || return 1

    if [[ ! -d "$dir_js" ]]; then
        echo "Creating JS directory: $dir_js"
        mkdir -p "$dir_js"
    fi
    local jsfile
    # Allow only files in app/static, or app/subdir/static.
    for jsfile in $dir_project/*/static/js/*.js $dir_project/*/*/static/js/*.js
    do
        build_js_file "$jsfile"
    done
}

function build_js_file {
    # Build a single js file, passed in as an arg.
    [[ $has_closure == true ]] || return 1

    local jsfile="$1"
    if [[ ! -e "$jsfile" ]]; then
        echo "File does not exist: $jsfile"
        return 1
    fi

    local relname="${jsfile##*..}"
    local relshortname="${relname##*/}"
    if is_ignored_js "$relshortname"; then
        debug "    Skipping ignored: $relshortname"
        return 0
    fi
    local outname="${relshortname%.*}.min.js"
    local outpath="$dir_out/js/$outname"
    local outpathshort="${outpath##*..}"
    if ! is_modified "$jsfile" "$outpath" && [[ $forced_mode == false ]]; then
        debug "    Skipping non-modified file: $relshortname"
        return 0
    fi
    if [[ $debug_mode == true ]]; then
        debug "Would've built js file: $relshortname -> $outpathshort"
        return 0
    fi

    printf "Building JS file: %-25s -> %s\n" "$relshortname" "$outpathshort"
    java -jar "$closure_path" "${js_args[@]}" --js "$jsfile" --js_output_file "$outpath"
}


function build_sass {

    if [[ ! -d "$dir_css" ]]; then
        echo "Creating CSS directory: $dir_css"
        mkdir -p "$dir_css"
    fi
    local sassfile
    # Allow only files in app/static, or app/subdir/static.
    for sassfile in $dir_project/*/static/sass/*.scss $dir_project/*/*/static/sass/*.scss
    do
        build_sass_file "$sassfile"
    done
}


function build_sass_file {
    # Build a single sass file, passed in as an arg.
    local sassfile="$1"
    if [[ ! -e "$sassfile" ]]; then
        echo "File does not exist: $sassfile"
        return 1
    fi

    local relname="${sassfile##*..}"
    local relshortname="${relname##*/}"
    if is_ignored_sass "$relshortname"; then
        debug "    Skipping ignored: $relshortname"
        return 0
    fi
    local outname="${relshortname%.*}.min.css"
    local outpath="$dir_out/css/$outname"
    local outpathshort="${outpath##*..}"
    if ! is_modified "$sassfile" "$outpath" && [[ $forced_mode == false ]]; then
        debug "    Skipping non-modified file: $relshortname"
        return 0
    fi

    if [[ $debug_mode == true ]]; then
        debug "Would've built sass file: $relshortname -> $outpathshort"
        return 0
    fi

    printf "Building SASS file: %-25s -> %s\n" "$relshortname" "$outpathshort"
    sass "${sass_args[@]}" "${sass_include_args[@]}" "$sassfile" "$outpath"
}


function debug {
    if [[ $debug_mode == true ]]; then
        printf "%s\n" "$1"
    fi
}


function is_ignored_js {
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


function is_ignored_sass {
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

# Build individual files.
if (( ${#infiles[@]} > 0 )); then
    build_files "${infiles[@]}"
    exit
fi

# Build all files (default behavior).
if [[ $do_js == false ]] && [[ $do_sass == false ]]; then
    build_js
    build_sass
    exit
fi

# Selective builds.
if [[ $do_js == true ]]; then
    build_js
fi

if [[ $do_sass == true ]]; then
    build_sass
fi

