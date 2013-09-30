#!/Python27/python.exe
#-------------------------------------------------------------------------------
# Name:        dnstimer.py
# Purpose:
#
# Author:      Christopher Welborn
#
# Created:     15/11/2012
# Copyright:   (c) Welborn Productions 2012
# Licence:     Free
#-------------------------------------------------------------------------------
from __future__ import print_function
import sys
import os.path
import time
import subprocess
import shlex
import dns.resolver

# Script info
sversion = "1.0"

# Location of nslookup.exe?
cmd = "c:\Windows\System32\\nslookup.exe"
if (not os.path.isfile(cmd)):
    cmd = "/usr/bin/nslookup"
if (not os.path.isfile(cmd)):
    print("Cannot locate nslookup!\n")
    print("In Windows, it should be located in C:\\Windows\\System32\\...")
    print("In Linux, it should be in /usr/bin/...")

"""
  These variables (bVerbose, bSilent, bIgnoreError, bShowAll, bUseWinNS,
                    iRuns, imax_length) can be set by the command line
                    arguments passed...
"""
#   Flag for verbose output, shows dns responses
bVerbose = False
#   Flag for no output (except average/winner/loser)
bSilent = False
#   Flag for Ignoring Domain Response Errors if user chooses
bIgnoreError = False
#   Flag for showing ALL output from server response (instead of just IP's)
bShowAll = False
#   Flag for using window's nslookup.exe
bUseWinNS = False
#   Number of tests to perform
iRuns = 1
#   Maximum number of digits to show in report (including '0.')
imax_length = 7

"""
  These variables (sDefaultTestDomain, valid_doms, servers) need to be manually
  edited if you want to customize this script. servers could be read from a file,
  but i thought this would be easier, and I don't use it enough to have multiple
  server-list files stored and used.
"""
# Default site to use for test
sDefaultTestDomain = "www.google.com"
#   Valid test domain name prefixes/extensions
#   ...(for looking at arguments & detecting which is the test domain if any)
#   ...add more if you like, i'm not gonna check for EVERY single extension,
#   ...just the popular ones..
valid_doms = ["www.", ".com", ".org", ".edu", ".net", ".gov",
               "ftp.", ".biz", ".info", ".mil", ".mobi", ".us"]
#   The DNS servers to compare, put ["NAME", "IP ADDRESS"], to  add more..
servers = [
                ["Charter", "24.177.176.38"],
                ["OpenDNS", "208.67.222.222"],
                ["Google 1", "8.8.8.8"],
                ["Google 2", "8.8.4.4"]
          ]
# Sort list automagically by alphabetical order (you can delete/comment out)
servers = sorted(servers)

# Initialize dns.resolver (None incase the nslookup method is used)
dns_resolver = None

"""
  Setup Lists for use with main()...
"""
# Results,  Fastest, & Slowest Lists to keep track of results...
lst_results = []
lst_fastest = []
lst_slowest = []
# Must have same item count as servers list, so we'll build them here..
for ibuild in range(0, len(servers)):
    # Setup each list with some default values...
    lst_results.append([])
    lst_fastest.append(999)
    lst_slowest.append(0)

# ---------------------------- PRINT HELP ------------------------------------ #
def print_help():
    print("\ndnstimer.py " + sversion + " Usage:")
    print("    python dnstimer.py " + \
          "[--v|--s] [--i] [--a] [--w] [--h] [--l] [testdomain.com]\n")
    print("Example:")
    print("    python dnstimer.py --v --r5 www.google.com")
    print("    ...this runs 5 tests in verbose mode using www.google.com as the domain\n")
    print("Options:")
    print("       --a : While verbose (--v): show ALL of the server response")
    print("       --h : Show this help message")
    print("       --i : Ignore any errors in server response (if possible)")
    print("       --l : Length of overall digits to use in time, can also use (--length)")
    print("             Use one of these formats (--l5, \"--l 5\", --l=5, --l:5)")
    print("       --s : Silent mode: only returns the results, no responses.")
    print("       --v : Verbose: show server responses, cannot mix with --s.")
    print("       --w : Use windows nslookup.exe, not python lib dns.resolver")
    print("       --r : Number of tests to run (can also use --runs)")
    print("             Use one of these formats (--r5, \"--r 5\", --r=5, --r:5)")
    print("\n** The options can be placed in any order, as long as --r & --l are formatted correctly. **\n")

# ------------------------------ IS IP? -------------------------------------- #
def is_ip(sIp):
    """
        Determines if given string is the right format for an ip address
    """
    # Try splitting string by '.', we should have exactly 4 items
    if not len(sIp.split(".")) == 4:
        return False
    # Check if everything except '.' are numbers like they should be
    try:
        ltest = long(sIp.replace(".", ""))
    except:
        return False

    # Both tests passed, I think we have an IP...
    return True


# ------------------------------- LOOKUP nslookup.exe ------------------------ #
def win_nslookup(sServer, sDomain):
    """
        Runs & Times nslookup.exe with given DNS Server & Test Domain Name
    """
    # Build command
    cmdlook = cmd + " " + sDomain + " " + sDNS
    # split into acceptable subprocess list[] format
    cmdlist = cmdlook.split(" ")
    # Get start time
    tStart = time.clock()
    # Run command
    sRes = subprocess.check_output(cmdlist, stderr=subprocess.STDOUT)
    # Strip NewLine, and ugly "non-authoratative" stuff
    sRes = sRes.strip('\n').replace("Non-authoritative answer:", "")
    # Return [DNS Server Response, Time it took to run]
    return [sRes, (time.clock() - tStart)]
# --------------------------------- LOOKUP dns.resolver -----------------------#
def dns_lookup(sDNS, sDomain):
    global dns_resolver
    """ Connects to server using dns.resolver, queries Domain """
    # Initialize dns.resolver object if it's not already done.
    if dns_resolver == None:
        dns_resolver = dns.resolver.Resolver()
    dns_resolver.nameservers = [sDNS]
    # Start timer
    tStart = time.clock()
    # Get raw response from dns.resolver
    sresponse = dns_resolver.query(sDomain)
    # Stop timer immediately after response is received
    tTime = (time.clock() - tStart)
    # Convert just the server's response to text
    dnsmsg = sresponse.response.to_text()
    # Error? If not return [the response, time it took]
    if "NOERROR" in dnsmsg.upper():
        # Trim out all the other stuff, we just want the IP's for now
        if (not bShowAll):
            sres = dnsmsg.split(";ANSWER")[1].split(";AUTHORITY")[0]
        else:
            # Show ALL output from server response
            sres = dnsmsg
        return [sres, tTime]
    else:
        # Error occured
        return [dnsmsg, tTime]


# --------------------------------- MAIN ------------------------------------- #
def main(sTestDomain):
    """
        Main program, runs single or multiple tests on server list/test domain
    """
    global bIgnoreError

    # Run Multiple Tests?
    for itestnum in range(0, iRuns):
        # Print test number in normal mode -------------------------------------
        if (not bSilent):
            print("\nTest #" + str(itestnum + 1) + ": " + ("-" * 37) + "\n")
        else:
            # Print Status dot during multiple runs
            if iRuns > 1:
                # newline every 10th test in Silent Mode
                if (itestnum % 10) == 0:
                    print(" ")
                # Print status dots
                print(".", end=" ")

        # Run test on each server ----------------------------------------------
        for isrv in range(0, len(servers)):
            # Setup for possible domain name error
            bDomainError = False
            # Run Test, retrieves: sRes[0] = Response, sRes[1] = Time
            # Use dns.resolver or Window's nslookup.exe?
            if (not bUseWinNS):
                # Using dns.resolver may be quicker, and allow for more accuracy
                try:
                    sRes = dns_lookup(servers[isrv][1], sTestDomain)
                except dns.resolver.NXDOMAIN as exDomain:
                    # Catch bad domain name error
                    sRes[0] = "dns.resolver found bad domain name!: " + \
                               sTestDomain + "\n" + \
                               "Exception:\n" + str(exDomain) + "\n"
                    bDomainError = True

            else:
                # this may make times seem a bit longer, because we're really
                # ...querying the whole process nslookup.exe
                sRes = win_nslookup(servers[isrv][1], sTestDomain)
            # Append time result to current server's time results
            lst_results[isrv].append(sRes[1])
            # Domain not found?
            if (("NOT FOUND" in sRes[0].upper()) or
                ("CAN'T FIND" in sRes[0].upper()) or
                ("NON-EXISTENT" in sRes[0].upper()) or
                ("ERROR" in sRes[0].upper())):
                bDomainError = True
            # Fastest time yet for this server?
            if (lst_results[isrv][itestnum] < lst_fastest[isrv]):
                lst_fastest[isrv] = lst_results[isrv][itestnum]
            # Slowest time yet for this server?
            if (lst_results[isrv][itestnum] > lst_slowest[isrv]):
                lst_slowest[isrv] = lst_results[isrv][itestnum]
            # Print Server name in Normal/Verbose mode
            if (not bSilent):
                print("Name: " + servers[isrv][0])
            # Print results from test in Verbose/Error mode
            if (not bSilent):
                # Print results from DNS Server
                if bVerbose or bDomainError:
                    # no Error? print results..
                    if not bDomainError:
                        print(sRes[0])
                    # Error? print warning (even in non-verbose mode)
                    else:
                        if (not bIgnoreError):
                            print(sRes[0])
                            print("\nPossible error found in server response!:")
                            scon = raw_input("\n[C]ontinue, [I]gnore All, or [Q]uit: ")
                            if "Q" in scon.upper():
                                print("\nUser quit on possible error, goodbye!\n")
                                quit()
                            elif "I" in scon.upper():
                                print("\nIgnoring any remaining errors...\n")
                                bIgnoreError = True

                # Print time (no longer than imax_length digits)
                print("Time: " + str(sRes[1])[:imax_length])
                # Use seperator for verbose mode/newline otherwise
                if bVerbose:
                    print("." * 45)
                else:
                    print(" ")

    # TESTS COMPLETE -----------------------------------------------------------
    # Print divider in normal mode, newline in silent mode
    if (not bSilent) and (not bVerbose):
        print("-" * 45)
    elif (bSilent):
        print(" ")


    # Get averages -------------------------------------------------------------
    lst_average = []
    for isrv in range(0, len(servers)):
        isum = 0
        iaverage = 0
        # Get sum of all runs for this server
        for itestnum in range(0, iRuns):
            isum = isum + lst_results[isrv][itestnum]
        # Get average for this server
        iaverage = isum / iRuns
        sname = servers[isrv][0]
        # Append name & average to list for reporting later
        lst_average.append([sname, iaverage])

    # Get best/worst average ---------------------------------------------------
    iBestAvr = 999
    iWorstAvr = 0
    for isrv in range(0, len(servers)):
        # Best?
        if (lst_average[isrv][1] < iBestAvr):
            iBestAvr = lst_average[isrv][1]
            iWinner = isrv
        # Worst?
        if (lst_average[isrv][1] > iWorstAvr):
            iWorstAvr = lst_average[isrv][1]
            iLoser = isrv


    # Print average time results -----------------------------------------------
    print("\nAverage from " + str(iRuns) + " runs: (+ Best Average, - Worst Average)\n")
    # Cycle thru list of servers/results
    for isrv in range(0, len(servers)):
        sname = lst_average[isrv][0]
        iaverage = lst_average[isrv][1]
        # Prepare Best/Worst data if more than 1 run
        if iRuns > 1:
            sdata = " [Best: " + str(lst_fastest[isrv])[:imax_length] + \
                       " , Worst: " + str(lst_slowest[isrv])[:imax_length] + "]"
        else:
            sdata = ""
        # Was this server the best single run? mark it with +
        if isrv == iWinner:
            sname = sname + "  +"
        # Was this server the worst single run? mark it with -
        elif isrv == iLoser:
            sname = sname + "  -"
        # Not winner or loser
        else:
            sname = sname + "   "
         # Print server name/average/best/worst
        print((" " * (19 - len(sname))) + sname + ": " + \
               str(iaverage)[:imax_length] + sdata)

    # FINISHED -----------------------------------------------------------------
    # Ran in silent mode but errors were found?
    if (bSilent) and (bDomainError):
        print("\nServer returned possible error, please run in verbose mode (--v).\n")
    # EXIT
    print("\nFinished!")
    exit(0)


# ------------------------ START OF SCRIPT ----------------------------------- #
if __name__ == '__main__':
    # Site that will be used, if no argument passed, it gets set to the default
    sDom = ""

    # Arguments? ---------------------------------------------------------------
    for iarg in sys.argv:
        # get HELP?
        if ("--H" in iarg.upper()):
            print_help()
            quit()

        # get test domain
        #if ((".org" in iarg) or (".com" in iarg) or
        #    (".net" in iarg) or (".edu" in iarg) or
        #    ("www." in iarg)):
        # Does argument contain valid ip address/domain name to test?
        if ((iarg[:4] in valid_doms) or (iarg[len(iarg)-3:] in valid_doms) or
            (iarg[len(iarg)-4:] in valid_doms) or
            (iarg[len(iarg)-5:] in valid_doms) or (is_ip(iarg))):
            sDom = iarg
            print("Using custom lookup: " + sDom + "\n")

        # get silent? (Silent mode also ignores all errors!)
        if "--S" in iarg.upper():
            bSilent = True

        # get verbose?
        if "--V" in iarg.upper():
            # Already in silent mode?
            if bSilent:
                print("Verbose & Silent Mode cannot be mixed!\n")
                quit()
            bVerbose = True

        # get ignore domain errors?
        if "--I" in iarg.upper():
            bIgnoreError = True

        # get show all output?
        if "--A" in iarg.upper():
            bShowAll = True

        # get use windows nslookup?
        if "--W" in iarg.upper():
            bUseWinNS = True

        # get maximum length of digits in time results?
        if "--L" in iarg.upper():
            """  Length argument can be passed several ways like this:
                 --l=5, --l:5, "--l 5", --l5,
                 ...also using the word 'len' or 'length' [not case sensative]
            """
            # Trim --l[[en]gth] to get number (l, len, or length)
            iargl = iarg.upper().replace("--L", "").replace("EN", "").replace("GTH", "")
            # Trim =, :, or ' ' to get number
            iargl = iargl.replace("=", "").replace(":", "").replace(" ", "")
            try:
                imax_length = int(iargl)
                # minimum length allowed is 3 (less than that would not help you)
                if imax_length < 3:
                    print("Minimum length of digits is 3 including '0.', " + \
                    "Now using 3...\n")
                    # set to default minimum
                    imax_length = 3
            except:
                print("\nInvalid number for --length!\n")
                print_help()
                quit()

        # get number of runs
        if ("--R" in iarg.upper()):
            """  Run argument can be passed several ways like this:
                 --r=5, --r:5, "--r 5", --r5,
                 ...also using the word 'runs' [not case sensative]
            """
            # Trim --r[uns] to get number
            iargr = iarg.upper().replace("--R", "").replace("UNS", "")
            # Trim =, :, or ' ' to get number
            iargr = iargr.replace("=", "").replace(":", "").replace(" ", "")
            try:
                iRuns = int(iargr)
            except:
                print("\nInvalid number for --runs!\n")
                print_help()
                quit()

    # Use Default Test Domain? -------------------------------------------------
    if sDom == "":
        sDom = sDefaultTestDomain
        print("Using default lookup: " + sDom + "\n")
    # Report run mode/s --------------------------------------------------------
    if (bIgnoreError):
        print("Ignoring any server errors...\n")
     # Report number of runs...
    print("Running " + str(iRuns) + " tests...")
    # run program with test domain, catching CTRL+C (interrupt) ----------------
    try:
        main(sDom)
    except KeyboardInterrupt:
        print("\nUser Interrupted, goodbye!\n")
        quit()
    except Exception as ex:
        print("Sorry, an unknown error occurred:")
        print(str(ex))
