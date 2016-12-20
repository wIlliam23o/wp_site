# Awk program to "build" django template files, basically minimizing them.
function debug(lbl, val)
{
    if (debugmode == 1) {
        printf "%-16s: %s\n", lbl, val
    }
}

BEGIN {
    # Add header to the file, set pre-tag flag.
    inpre=0
    # Set to 1 to debug the tests below.
    if (debugmode == "")
        debugmode=0
    debug("DEBUGMODE", debugmode)
    print "{# Generated using build_template.sh v. "build_template_ver" #}"
}
inpre==0 && /^<!--.+-->$/ {
    # Single line html comment.
    # Skip.
    if (debugmode == 1) {
        debug("SKIP HTML", $0)
    }
    next
}
inpre==0 && /\/\*.+\*\// {
    # Single line js block comment.
    # Skip.
    if (debugmode == 1) {
        debug("SKIP JS", $0)
    }
    next
}
inpre==0 && /\{\#.+\#\}/ {
    # Single line django template comment.
    # Skip.
    if (debugmode == 1) {
        debug("SKIP DJANGO", $0)
    }
    next
}
inpre==1 && /<\/pre>/ {
    # End of <pre> tag, leave the line alone.
    # Skip.
    inpre=0
    if (debugmode == 1) {
        debug("END PRE", $0)
    } else {
        print $0
    }
    next
}
inpre==0 && /<pre/ {
    # Start of <pre> tag.
    # Leave the line alone.
    inpre=1
    if (debugmode == 1) {
        debug("PRE", $0)
    } else {
        print $0
    }
    next
}
inpre==1 {
    # Any blank or non-blank line inside of a <pre></pre>.
    # Leave the line alone.
    if (debugmode == 1) {
        debug("IN PRE", $0)
    } else {
        print $0
    }
    next
}
inpre==0 && /./ {
    # Any non-blank, non-pre tag or comment line.
    # Trim the whitespace.
    gsub(/^[ \t]+/, "", $0)
    if (debugmode == 1) {
        debug("LINE", $0)
    } else {
        print $0
    }
    next
}
