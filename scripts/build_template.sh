#!/bin/bash

# "Builds" a template, by removing leading whitespace, blank lines, and
# comments.
# -Christopher Welborn 12-19-2016
appname="Wp Template Builder"
appversion="0.0.1"
apppath="$(readlink -f "${BASH_SOURCE[0]}")"
appscript="${apppath##*/}"
appdir="${apppath%/*}"

shopt -s nullglob

# This can be set with --debug.
debug_mode=0

# Sed program to "build" templates.
awkprogramfile="$appdir/build_template.awk"

# Count of non-modified template files found when running.
non_modified_templates=0

# Extension for raw templates (unbuilt).
template_ext=".in.html"
template_extpat='\.in\.html$'
# Subdir in templates where raw templates can be found.
template_subdir="in"

function build_template {
    # Build a single template file.
    # Arguments:
    #   $1  : Input file name (*.in.html)
    #   $2  : Optional output file name.
    local filename=$1 outfile=$2
    declare -a awkargs=(
        "-v" "build_template_ver=$appversion"
        "-f" "$awkprogramfile"
    )
    # ((debug_mode)) && { do_stdin=1; awkargs+=("-v" "debugmode=1"); }

    if [[ -z "$filename" ]]; then
        echo_err "No filename given to \`build_template\`!"
        return 1
    fi
    if ((do_stdout)) || [[ -z "$outfile" ]]; then
        # Build to stdout.
        awk "${awkargs[@]}" "$filename" && return 0
    else
        # Build to file if
        if ((do_forced)) || is_modified "$filename" "$outfile"; then
            awk "${awkargs[@]}" "$filename" > "$outfile" || return 1
            echo -e "Built template: $outfile"
        else
            let non_modified_templates+=1
            debug_lbl "Skipping non-modified file:" "${filename##*/}"
        fi
        return 0
    fi
    return 1

}

function build_templates {
    local errs=0 outfile outdir filebase filepath
    for filepath in "$@"; do
    filepath="$(readlink -f "$filepath")"
        if [[ ! -e "$filepath" ]]; then
            echo_err "File does not exist: $filepath"
            let errs+=1
            continue
        elif [[ ! "$filepath" =~ $template_extpat ]]; then
            echo_err "Not a template file: $filepath"
            let errs+=1
            continue
        fi
        outdir="${filepath%/*}/.."
        filename="${filepath##*/}"
        filebase="${filename%.*.*}"
        outfile="$(readlink -f "${outdir}/${filebase}.html")"
        if ((do_dryrun)) && { ((do_forced)) || is_modified "$filepath" "$outfile"; }; then
            echo -e "Would've built: $outfile"
            continue
        fi
        # Remove blank lines, remove html comments, remove leading whitespace
        if ! build_template "$filepath" "$outfile"; then
            echo_err "Failed to build template: $filepath"
            let errs+=1
            continue
        fi

    done
    return $errs
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
    echo -e "$@" 1>&2
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

function echo_status {
    # echo if do_quiet is not set.
    ((!do_quiet)) && echo -e "$@"
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

function move_old_templates {
    # Moves old template files in templates/ to templates/in/
    local errs=0 outfile filename
    for filepath in "$@"; do
        filepath="$(readlink -f "$filepath")"
        if [[ ! -e "$filepath" ]]; then
            echo_err "File does not exist: $filepath"
            let errs+=1
            continue
        elif [[ "$filepath" != *.in.html ]]; then
            echo_err "Not a template file: $filepath"
            let errs+=1
            continue
        fi
        outdir="${filepath%/*}/$template_subdir"
        if [[ ! -d "$outdir" ]]; then
            if ((do_dryrun)); then
                echo -e "Would've created dir: $outdir"
            else
                if ! mkdir -p "$outdir"; then
                    echo_err "Failed to create directory: $outdir"
                    let errs+=1
                    continue
                fi
            fi
        fi
        filename="${filepath##*/}"
        outfile="$(readlink -f "${outdir}/${filename}")"

        if ((do_dryrun)); then
            printf "Would've moved: %s\n" "${filepath##*/}"
            continue
        fi
        # Remove the file.
        if mv "$filepath" "$outfile"; then
            echo -e "Moved to: $outfile"
        else
            echo_err "Failed to move: ${filepath##*/}"
            let errs+=1
            continue
        fi
    done
    return $errs
}

function print_usage {
    # Show usage reason if first arg is available.
    [[ -n "$1" ]] && echo_err "\n$1\n"

    echo "$appname v. $appversion

    Usage:
        $appscript -h | -v
        $appscript [-d | -f] [-q] [-m |-r | -R] [-s] (-a | FILE...) [-D]

    Options:
        FILE          : Template file to build.
        -a,--all      : Build all template files in current directory,
                        recursively.
        -d,--dryrun   : Just show the files that would be built.
        -D,--debug    : Print some debugging info while running.
        -f,--force    : Force build of all template files, not just the
                        modified files.
        -h,--help     : Show this message.
        -m,--move     : Move old template files to new dir:
                            templates/$template_subdir
        -q,--quiet    : Don't print header/footer messages.
        -r,--rename   : Rename old .html files to .in.html.
                        Does no overwrite existing .in.html files.
        -R,--remove   : Remove built templates (all templates/*.html).
        -s,--stdout   : Output to stdout, instead of a file.
        -v,--version  : Show $appname version and exit.
    "
}

function rename_old_templates {
    # Renames old .html files to .in.html files.
    local errs=0 outfile filepath tmpext=".in.html"
    for filepath in "$@"; do
    filepath="$(readlink -f "$filepath")"
        if [[ ! -e "$filepath" ]]; then
            echo_err "File does not exist: $filepath"
            let errs+=1
            continue
        elif [[ "$filepath" != *.html ]]; then
            echo_err "Not a template base file: $filepath"
            let errs+=1
            continue
        elif [[ "$filepath" == *"$tmpext" ]]; then
            echo_err "Already a template file: $filepath"
            let errs+=1
            continue
        fi
        outfile="$(readlink -f "${filepath%.*}.in.html")"
        if [[ -e "$outfile" ]]; then
            echo_err "Template file already exists: $outfile"
            let errs+=1
            continue
        fi
        if ((do_dryrun)); then
            printf "Would've renamed: %-35s -> %s\n" "${filepath##*/}" "${outfile##*/}"
            continue
        fi
        # Rename the file.
        if mv "$filepath" "$outfile"; then
            echo -e "Renamed: $outfile"
        else
            echo_err "Failed to rename: ${filepath##*/} -> ${outfile##*/}"
            let errs+=1
            continue
        fi
    done
    return $errs
}

function remove_old_templates {
    # Renames old .html files to .in.html files.
    local errs=0 outfile filepath
    for filepath in "$@"; do
    filepath="$(readlink -f "$filepath")"
        if [[ ! -e "$filepath" ]]; then
            echo_err "File does not exist: $filepath"
            let errs+=1
            continue
        elif [[ "$filepath" != *.html ]]; then
            echo_err "Not a template file: $filepath"
            let errs+=1
            continue
        elif [[ "$filepath" =~ $template_extpat ]]; then
            echo_err "Raw template file, skipping: $filepath"
            continue
        fi
        if ((do_dryrun)); then
            printf "Would've deleted: %s\n" "${filepath##*/}"
            continue
        fi
        # Remove the file.
        if rm "$filepath"; then
            echo -e "Removed: $filepath"
        else
            echo_err "Failed to remove: ${filepath##*/}"
            let errs+=1
            continue
        fi
    done
    return $errs
}

(( $# > 0 )) || fail_usage "No arguments!"

declare -a filenames
do_all=0
do_dryrun=0
do_forced=0
do_move=0
do_rename=0
do_remove=0
do_quiet=0
do_stdout=0

for arg; do
    case "$arg" in
        "-a" | "--all")
            do_all=1
            ;;
        "-d" | "--dryrun")
            do_dryrun=1
            ;;
        "-D" | "--debug")
            debug_mode=1
            ;;
        "-f" | "--force")
            do_forced=1
            ;;
        "-h" | "--help")
            print_usage ""
            exit 0
            ;;
        "-m" | "--move")
            do_move=1
            ;;
        "-q" | "--quiet")
            do_quiet=1
            ;;
        "-r" | "--rename")
            do_rename=1
            ;;
        "-R" | "--remove")
            do_remove=1
            ;;
        "-s" | "--stdout")
            do_stdout=1
            ;;
        "-v" | "--version")
            echo -e "$appname v. $appversion\n"
            exit 0
            ;;
        -*)
            fail_usage "Unknown flag argument: $arg"
            ;;
        *)
    filenames+=("$arg")
    esac
done

fileext=$template_ext
((do_rename || do_remove)) && fileext=".html"
subdir="$template_subdir/"
((do_rename || do_remove || do_move)) && subdir=""

if ((do_all)); then
    filenames=(
        "$appdir"/../*/templates/*/"$subdir"*"$fileext"
        "$appdir"/../*/*/templates/*/"$subdir"*"$fileext"
    )
    ((${#filenames[@]})) || fail "No template files found!"
else
    ((${#filenames[@]})) || fail_usage "No file names provided!"
fi

if ((do_move)); then
    move_old_templates "${filenames[@]}"
    errfiles=$?
elif ((do_rename)); then
    rename_old_templates "${filenames[@]}"
    errfiles=$?
elif ((do_remove)); then
    remove_old_templates "${filenames[@]}"
    errfiles=$?
else
    ((do_all)) && echo_status "\nBuilding template files...\n"
    build_templates "${filenames[@]}"
    errfiles=$?
fi

successfiles="$((${#filenames[@]} - errfiles - non_modified_templates))"
if ((do_dryrun)); then
    lbl="Template files"
    ((do_rename)) && lbl="New template files"
    echo_status "\n$lbl found: $successfiles"
else
    runtype="built"
    ((do_rename)) && runtype="renamed"
    ((do_remove)) && runtype="removed"
    ((do_move)) && runtype="moved"
    lbl="Templates $runtype: $successfiles ($errfiles failed)"
    if ((!do_forced)) && ((!do_rename)) && ((!do_remove)) && ((!do_move)); then
        lbl="${lbl} ($non_modified_templates not modified)"
    fi
    echo_status "\n$lbl"
fi
exit $errfiles
