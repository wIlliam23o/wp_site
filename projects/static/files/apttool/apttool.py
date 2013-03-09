'''
    apttool.py - APT Tools
    ..for working with/searching apt packages and returning information
    
    Created on Dec 30, 2012

    @author: Christopher Welborn
'''
from __future__ import print_function
import apt
import apt.cache
import sys

# list of args excluding scriptname
largs = sys.argv[1:]
# basename for all good args
largsbase = ["h", "s", "i", "r", "l", "f", "d", "name", "removeall",
                 "help", "search", "install", "remove", "installed", "files", 
                 "desc", "description"]
# build list of all possibly accepted args (with flags and all)
largsflags = []
for sarg in largsbase:
    largsflags.append(sarg)
    largsflags.append("-" + sarg)
    largsflags.append("--" + sarg)

    
def main(spackage = None):
    bsearch = (("-s" in largs) or ("search" in largs))
    binstall = (("-i" in largs) or ("install" in largs))
    bremove = (("-r" in largs) or ("remove" in largs))
    bremoveall = (("-a" in largs) or ("removeall" in largs))
    binstalled = (("-l" in largs) or ("installed" in largs))
    bfiles = (("-f" in largs) or ("files" in largs))
    bname = (("-n" in largs) or ("name" in largs))
    bdesc = (("-d" in largs) or ("desc" in largs) or ("description"in largs))
    # Search
    if bsearch:
        # package given?
        if spackage == None:
            printusage("no package name given!")
            exit(1)
        # What type of search?   
        if binstalled: 
            dosearch(spackage, "installed", bname, bdesc)
        elif bfiles:
            dosearch(spackage, "files", bname, bdesc)
        else:
            dosearch(spackage, "all", bname, bdesc)
        print("Finished with search.")
        exit(0)
        
    if spackage != None:
        print("package: " + spackage)
    pass
        
def printusage(sreason = None):
    if sreason != None:
        print(sreason + '\n')
    print("apttool usage:")
    print("    apttool [-help|-search|-install|-remove|-installed|-files] [-name|-removeall] <package>")
    print("\n")
    
def printhelp():
    printusage("apttool help:")
    print("        commands:")
    print("           h[elp] : shows this help message")
    print("         s[earch] : searches package name/info for string")
    print("        i[nstall] : installs package by name")
    print("        r[emove]  : removes package by name")
    print("    [remove]a[ll] : completely remove package by name")
    print("    [insta]l[led] : lists names of all packages installed")
    print("          f[iles] : list files installed with a package")
    print("\n        options:")
    print("             name : uses names only in search")
    print("             desc : shows full description in search results")
    print("\n        notes:")
    print("    ** search commands can be combined, like 'search installed' and 'search files'")
    print("       ..this will search only the areas you want to search")
    
def dosearch(stext, section, bnamesonly = False, bdescription = False):
    iresults = 0
    
    # Search all
    if section.lower() == "all":
        print("retrieving cache...")
        acache = apt.cache.Cache()
        acache.open()
        print("searching all...")
        if bnamesonly:
            print("names only...")
        for pkg in acache:
            if stext in pkg.name:
                # found match
                iresults += 1
                sdesc = pkg.description
                # Show full description?
                if bdescription:
                    print(pkg.name)
                    if '\n' in pkg.description:
                        ldesc = pkg.description.split('\n')
                        for sline in ldesc:
                            print("    " + sline)
                    else:
                        # only single line description anyway
                        print("    " + pkg.description)
                else:
                    # No Full Description
                    # Need to trim down to one liner?
                    if '\n' in sdesc:
                        sdesc = sdesc.split('\n')[0]
                    # Trim length if needed
                    if len(sdesc) > 60:
                        sdesc = sdesc[:60]
                    # print info
                    print(pkg.name + ": " + sdesc)

    
    # Finished search
    print("found " + str(iresults) + " results for: " + stext)
if __name__ == '__main__':
    spkg = None
    
    # no args
    if len(largs) == 0:
        printusage()
        exit(1)
    # get args
    for iarg in range(0, len(largs)):
        sarg = largs[iarg]
        # Check bad arg, package name/info
        if not sarg in largsflags:
            # package name?
            if iarg == (len(largs) - 1):
                spkg = largs[iarg]
            else:
                # bad arg, or package name passed prematurely
                printusage("bad argument passed: " + sarg)
                exit(1)
    
        # check help
        if ("-h" in sarg) or ("help" in sarg):
            printhelp()
            exit(0)
            
            
    # We're good, run main (spkg was either passed, or None)
    main(spkg)
    
           