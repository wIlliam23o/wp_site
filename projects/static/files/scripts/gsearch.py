#!/usr/bin/env python

# Google Command Line Search using Firefox
# ...opens results in New Tab
# ...If this script is ran as root, we will use su to try to run firefox
#    as the regular logged-on user, because if firefox is already
#    running it was probably ran by the regular user, and 
#    firefox -new-tab will not work correctly if ran by root when
#    normal user's firefox is already open. does that make sense?
#    (it opens a second firefox window, and we don't want that)
#    
# -Cjw 2012

# Imports
import urllib   # for making URL's compatible
import os       # for getting User ID
import sys      # for getting arguments
import commands # for getting logged in user (not user that ran the script)

# Get normally logged on user (hopefully not root)
sUser = os.environ["USER"]
# If we got root we need to try one more thing to get a normal user
if sUser == "root":
	# get output of shell command 'users'
	sUserCmd = commands.getoutput('users')
	# get list of all users logged into desktop
	sUsers = sUserCmd.split(" ")
	# go until we find one that is not root?
	for u in sUsers:
		if u != "root":
			# we found one that isn't root, so save it.
			sUser = u
	
# Pre Firefox Command (hopefully, to make sure we're not running as root)
sPreCmd = "su " + sUser + " -c "
# Initialize Search String
sSearchTerm = ""

#-----------------------------------------------------------------------		
# FIREFOX SEARCH                                                 FIREFOX
def searchFirefox():
	
	# build Shell command with URL and SearchTerm
	sCmd = "firefox -new-tab http://www.google.com/search?hl=en#q=\"" + sSearchTerm + "\""

	# Running as root? Fix the command to use SU to CJ...
	if os.geteuid() == 0:
		# Status
		print "Currently running as root, using su to " + sUser + "..."
		# Add SU to CJ, and enclose regular command in ' 's
		sCmd = sPreCmd + "'" + sCmd + "'"

	# Shell firefox with our google search URL
	try:
		iRet = os.system(sCmd)
	except:
		print "Error running command: " + sCmd
	
	# firefox exit status?
	if iRet > 0:
		print "Firefox exited with status: " + str(iRet)
	
	#Finished
	print "Finished..."
	return 0
#-----------------------------------------------------------------------		
# COMMAND-LINE SEARCH                                           CMD_LINE
def searchCMDLINE():
		pass
		
#-----------------------------------------------------------------------		
# START OF SCRIPT                                                  START
if __name__ == '__main__':
		
	# Check Arguments
	if len(sys.argv) < 2:
		print "No search term entered!"
		exit()
		
	# root warning...
	if sUser == "root":
		print "You are currently running as root," \
			  " this may not work properly."
			  
	# Get first search argument
	sSearchTerm = sys.argv[1]

	# Cycle thru all arguments	
	for i in range(len(sys.argv)):
		# don't count scriptname as argument ( >1)
		if i > 1:
			# insert space before everything but the first item
			sSearchTerm = sSearchTerm + " " + sys.argv[i]

	# Status
	print "Searching For \"" + sSearchTerm + "\"..."

	# Fix Search Term URL
	sSearchTerm = urllib.quote(sSearchTerm)

	# Do firefox Search, by default right now
	searchFirefox()
