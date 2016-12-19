#!/bin/bash

# Welborn Productions - Build
# ...A simpler build tool for js and sass.
# -Christopher Welborn 06-08-2015

appname="WpBuild"
appversion="0.3.0"
apppath="$(readlink -f "${BASH_SOURCE[0]}")"
appscript="${apppath##*/}"
appdir="${apppath%/*}"

# Allow null globs when iterating over file names.
shopt -s nullglob

# Whether to print extra information.
debug_mode=0
# Whether to ignore modification times.
forced_mode=0
# Force SASS when forced_mode is set, or trigger files are modified.
forced_mode_sass=0

dir_project="$appdir/.."
# Final home for minified files.
dir_out="$dir_project/built"
if [[ ! -e "$dir_out" ]]; then
    echo "Output directory is missing: $dir_out" 1>&2
    exit 1
fi
# Sub directories for each type of minified file.
dir_css="$dir_out/css"
dir_js="$dir_out/js"

# If a trigger file is newer than this file, it will trigger a rebuild.
trigger_ref="${dir_project}/build_trigger.txt"

# Build sass include paths
sass_includes=("$dir_project/wp_main/static/sass")
declare -a sass_include_args
for sassinclude in "${sass_includes[@]}"
do
    sass_include_args+=("-I" "$sassinclude")
done

# These files will not be built with sass.
sass_ignore=("_welbornprod.scss")
# Modifications to these files will trigger all SASS files to be rebuilt.
sass_triggers=("${dir_project}/wp_main/static/sass/_welbornprod.scss")

# Default sass args.
sass_args=("--style" "compressed" "--sourcemap=none")

# Path to closure.jar.
closure_path="$dir_project/scripts/external/closure.jar"
if [[ ! -e "$closure_path" ]]; then
    echo "Unable to locate closure compiler: $closure_path" 1>&2
    has_closure=0
else
    has_closure=1
fi

# These js files will not be minified.
js_ignore=('\.min\.' '-min\.' 'js/ace')
# Default closure args.
js_args=(
    "--compilation_level" "SIMPLE"
    "--warning_level" "QUIET"
    "--language_in" "ECMASCRIPT5"
)

# Pattern to recognize browserify input files.
browserify_prefix='_in-'
browserify_pat="^${browserify_prefix}.+\.js"

function build_browserify_file {
    # Browserify a file, and then build the output with build_js_file.
    local jsfile
    local relname
    local relshortname
    local browserify_outname
    local browserify_outrelname
    local browserify_outshortname
    jsfile=$1
    relname="${jsfile##*..}"
    relshortname="${relname##*/}"

    browserify_outname="$(get_browserify_outname "$jsfile")"
    browserify_outrelname="${browserify_outname##*..}"
    browserify_outshortname="${browserify_outrelname##*/}"
    if ! is_modified "$jsfile" "$browserify_outname" && (( ! forced_mode )); then
        debug_lbl "Skipping non-modified browserify file:" "$relshortname"
        return 0
    fi

    if (( debug_mode )); then
        echo_file_lbl "Would've browserified file:" "$relshortname" "$browserify_outshortname"
        return 0
    fi

    echo_file_lbl "Browserifying JS file:" "$relshortname" "$browserify_outshortname"
    if ! browserify "$jsfile" -o "$browserify_outname"; then
        echo_err "Browserifying failed for: $jsfile"
        return 1
    fi
    build_js_file "$browserify_outname" || return 1
    # Built browserified file successfully.
    return 0
}

function build_file {
    # Build a single file. File extension determines the builder.
    case "$1" in
        *.js)
            build_js_file "$1"
            ;;
        *.scss)
            build_sass_file "$1"
            ;;
        *.in.html)
            build_template_file "$1"
            ;;
        *)
            echo_err "Unknown file type: $1"
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
    (( has_closure )) || return 1

    if [[ ! -d "$dir_js" ]]; then
        echo_lbl "Creating JS directory:" "$dir_js"
        mkdir -p "$dir_js"
    fi
    local jsfile
    local jsfiles
    jsfiles=($dir_project/static/js/*.js $dir_project/*/static/js/*.js $dir_project/*/*/static/js/*.js)
    # Allow only files in static/, app/static, or app/subdir/static.
    for jsfile in "${jsfiles[@]}"
    do
        build_js_file "$jsfile"
    done
}

function build_js_file {
    # Build a single js file, passed in as an arg.
    (( has_closure )) || return 1

    local jsfile="$1"
    if [[ ! -e "$jsfile" ]]; then
        echo_err "File does not exist: $jsfile"
        return 1
    fi

    local relname
    relname="${jsfile##*..}"
    local relshortname
    relshortname="${relname##*/}"
    if is_ignored_js "$relshortname"; then
        debug_lbl "Skipping ignored:" "$relshortname"
        return 0
    fi

    if [[ "$relshortname" =~ $browserify_pat ]]; then
        # File needs to be browserified.
        build_browserify_file "$jsfile" || return 1
        return 0
    else
        if (( do_browserify )); then
            debug_lbl "Skipping non-browserify file:" "$relshortname"
            return 0
        fi
    fi

    local outname="${relshortname%.*}.min.js"
    local outpath="$dir_out/js/$outname"
    local outpathshort="${outpath##*..}"
    if ! is_modified "$jsfile" "$outpath" && (( ! forced_mode )); then
        debug_lbl "Skipping non-modified file:" "$relshortname"
        return 0
    fi
    if (( debug_mode )); then
        debug_lbl "Would've built js file:" "$relshortname -> $outpathshort"
        return 0
    fi

    echo_file_lbl "Building JS file:" "$relshortname" "$outpathshort"
    java -jar "$closure_path" "${js_args[@]}" --js "$jsfile" --js_output_file "$outpath"
}


function build_sass {

    if [[ ! -d "$dir_css" ]]; then
        echo "Creating CSS directory: $dir_css"
        mkdir -p "$dir_css"
    fi
    if is_triggered "${sass_triggers[@]}"; then
        echo "SASS trigger files have been modified, rebuilding SASS files."
        forced_mode_sass=1
        create_trigger_ref
    fi
    local sassfiles
    local sassfile
    sassfiles=($dir_project/static/sass/*.scss $dir_project/*/static/sass/*.scss $dir_project/*/*/static/sass/*.scss)
    # Allow only files in app/static, or app/subdir/static.
    for sassfile in "${sassfiles[@]}"
    do
        build_sass_file "$sassfile"
    done
}


function build_sass_file {
    # Build a single sass file, passed in as an arg.
    local sassfile="$1"
    if [[ ! -e "$sassfile" ]]; then
        echo_err "File does not exist: $sassfile"
        return 1
    fi

    local relname="${sassfile##*..}"
    local relshortname="${relname##*/}"
    if is_ignored_sass "$relshortname"; then
        debug_lbl "Skipping ignored:" "$relshortname"
        return 0
    fi
    local outname="${relshortname%.*}.min.css"
    local outpath="$dir_out/css/$outname"
    local outpathshort="${outpath##*..}"
    if ! is_modified "$sassfile" "$outpath" && (( ! forced_mode )) && (( ! forced_mode_sass )); then
        debug_lbl "Skipping non-modified file:" "$relshortname"
        return 0
    fi

    if (( debug_mode )); then
        debug_lbl "Would've built sass file:" "$relshortname -> $outpathshort"
        return 0
    fi

    echo_file_lbl "Building SASS file:" "$relshortname" "$outpathshort"
    sass "${sass_args[@]}" "${sass_include_args[@]}" "$sassfile" "$outpath"
}

function build_templates {
    # Build all template files using build_template.sh
    declare -a tmpargs=("--quiet")
    ((forced_mode)) && tmpargs=("--force")
    tmpargs+=("--all")
    "$appdir/build_template.sh" "${tmpargs[@]}"
}

function build_template_file {
    # Build a single template file using build_template.sh
    local tmpfile=$1
    declare -a tmpargs=("--quiet")
    ((forced_mode)) && tmpargs=("--force")
    tmpargs+=("$tmpfile")
    "$appdir/build_template.sh" "${tmpargs[@]}"
}

function create_trigger_ref {
    # Update the modification time for the trigger reference file.
    if ((debug_mode)) && [[ -e "$trigger_ref" ]]; then
        debug_lbl "Would've updated the trigger reference:" "$trigger_ref"
    else
        debug_lbl "Creating trigger ref.:" "$trigger_ref"
        date --utc +%s > "$trigger_ref"
    fi
}

function debug {
    if (( debug_mode )); then
        printf "%s\n" "$1"
    fi
}

function debug_lbl {
    # Print a formatted debug message with a label and a value.
    if (( debug_mode )); then
        echo_lbl "$@"
    fi
}

function echo_err {
    # Echo to stderr.
    echo "$@" 1>&2
}

function echo_file_lbl {
    # Echo a formatted file status message.
    # Example: echo_file_lbl "Building:" "inputfile" "outputfile"
    if [[ -n "$3" ]]; then
        printf "%-40s %-25s -> %s\n" "$1" "$2" "$3"
    else
        echo_lbl "$1" "$2"
    fi
}

function echo_lbl {
    # Echo a formatted label/value pair.
    printf "%-40s %s\n" "$1" "$2"
}

function ensure_trigger_ref {
    # Create the reference file for "is this a fresh file" triggers.
    [[ -e "$trigger_ref" ]] && return 0
    create_trigger_ref
}

function get_browserify_outname {
    local jsfile
    jsfile=$1
    local relname
    relname="${jsfile##*..}"
    local relshortname
    relshortname="${relname##*/}"

    local input_dir
    input_dir="${jsfile%/*}"
    local browserify_relshortname
    browserify_relshortname="${relshortname#$browserify_prefix*}"
    printf "%s/%s" "$input_dir" "$browserify_relshortname"
}

function is_fresh {
    # Determine if a file has been updated since the last build.
    if [[ ! -e "$1" ]]; then
        debug "File does not exist: $1"
        return 1
    fi
    ensure_trigger_ref
    debug_lbl "Checking for freshness:" "$1"
    is_modified "$1" "$trigger_ref"
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
    local oldsecs
    oldsecs=$(date --utc --reference="$1" +%s)
    local newsecs
    newsecs=$(date --utc --reference="$2" +%s)
    if [[ $oldsecs -gt $newsecs ]]; then
        debug_lbl "File has been modified:" "$1"
        return 0
    fi
    return 1
}

function is_triggered {
    # Returns a success exit status if any of the "trigger" files have been
    # modified since the last build.
    # Arguments:
    #     $@ : Trigger files to check.
    local fname
    local triggered
    let triggered=0
    debug "Checking trigger files..."
    for fname in "$@"; do
        is_fresh "$fname" && let triggered+=1
    done
    if ((triggered)); then
        debug_lbl "Trigger files modified:" "$triggered"
        return 0
    fi
    debug "Trigger files have not been modified."
    return 1
}

# shellcheck disable=SC2120
function print_usage {
    # Print usage reason if given.
    [[ -n "$1" ]] && echo -e "\n$1\n"

    echo "
$appname v. $appversion

    Usage:
        $appscript -h | -v
        $appscript [-f] [-b | -j | -s | -t]

    Options:
        -b,--browserify  : Build browserify files.
        -f,--force       : Ignore modification times, and force building.
        -h,--help        : Show this message and exit.
        -j,--js          : Build javascript files.
        -s,--sass        : Build sass files.
        -t,--template    : Build django template files.
        -v,--version     : Show version and exit.

    When no arguments are passed all recently modified files are built.
"
}


# Parse args
do_browserify=0
do_js=0
do_sass=0
do_template=0
do_all=0
declare -a infiles
for arg; do
    case "$arg" in
        "-b"|"--browserify" )
            do_browserify=1
            do_all=0
            ;;
        "-D"|"--debug" )
            debug_mode=1
            ;;
        "-f"|"--forced" )
            forced_mode=1
            debug "Forced mode, ignoring modification times."
            ;;
        "-h"|"--help" )
            print_usage ""
            exit 0
            ;;
        "-j"|"--js" )
            do_js=1
            do_all=0
            ;;
        "-s"|"--sass" )
            do_sass=1
            do_all=0
            ;;
        "-t"|"--template" )
            do_template=1
            do_all=0
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
            infiles=("${infiles[@]}" "$arg")
    esac
done

# Build individual files.
if (( ${#infiles[@]} > 0 )); then
    build_files "${infiles[@]}"
    exit
fi

if ((do_all)); then
    # Build all files (default behavior).
    build_js
    build_sass
    build_templates
    exit
fi

# Selective builds.
if (( do_js )) || (( do_browserify )); then
    build_js
fi

if (( do_sass )); then
    build_sass
fi

if ((do_template)); then
    build_templates
fi
