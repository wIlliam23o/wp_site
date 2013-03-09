#!/usr/bin/env python
    
""" 
* Counts: 
    code lines, comment lines, blank lines, inline comments, doc strings,
    doc string lines, imports, classes, functions, try statements, 
    exception catchers, print statements, if statements, variables, 
    variable assignments
       
* Reports count/percentage of each item on the console
* Provides lists of these items printed to console

* With use of argument flags i, v, e, s, and d:
*     Lists all imports, variables, docstrings, and exception catchers,
*     Lists can be sorted in the order of discovery, or alphabetical

@author: Christopher Welborn <cj@welbornproductions.net>
"""

# ---------------------------------------------------------------------

#(c) Copyright by Christopher J. Welborn, 2012, cjwelborn@gmail.com 

# Permission to use, copy, modify, and distribute this software and 
# its documentation without fee and for any purpose, except direct 
# commerial advantage, is hereby granted, provided that the above 
# copyright notice appear in all copies and that both that copyright
# notice and this permission notice appear in supporting documentation.
#
# THE AUTHOR CHRISTOPHER J. WELBORN DISCLAIMS ALL WARRANTIES WITH REGARD TO
# THIS SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
# FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL,
# INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING
# FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT,
# NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION
# WITH THE USE OR PERFORMANCE OF THIS SOFTWARE!

# -Christopher J. Welborn

# 1-2-2013
from __future__ import print_function
import sys          # for argument parsing
import os           # for listing directory contents, file/path stuff
#import re           # for trimming spaces from strings

class codecounter():
    def __init__(self):
        """ Initialize main code counter object """
        # Set App Name
        self.appname = "Code Counter"
        # Set Version
        self.version = "2.0.1"
        # Get script file name
        self.script = sys.argv[0]
        # Set spacing for reports
        self.spacing = "        "
        # Trim ./ from script file name
        if self.script.startswith("./"): 
            self.script = self.script[2:]
        # Placeholder for arguments
        self.args = []
        
    def main(self, lst_args):
        """ What to run if script is shelled from terminal,
            ...Also provides an example of how to use it
        """
        # Save args
        self.args = lst_args
        # Make sure filename is arg[1] if no other args are passed
        if len(self.args) < 2:
            if (not self.args[0] == "h") and (not self.args[0] == "-h"): 
                self.args.append(self.args[0])
                self.args[0] = "-"
            
        # Help?
        if "h" in self.args[0]:
            self.printhelp()
            exit(0)
            
        # File checker
        sfile = self.args[1]
        if os.path.isfile(sfile):
            #print("Checking file: " + sfile + "...")
            res = self.filechecker(self.args[1]) 
            lst_results = [res]
            
        elif os.path.isdir(sfile):
            # Directory checker
            lst_results = []
            
            lst_files = os.listdir(sfile)
            lst_py = []
            for filename in lst_files:
                if os.path.isfile(os.path.join(sfile, filename)) and filename.endswith(".py"):
                    lst_py.append(filename)
                
            for pyfile in lst_py:
                spath = os.path.join(sfile, pyfile)
                res = self.filechecker(spath)
                lst_results.append(res)
                
        else:
            self.printusage("Invalid file/dir given!: " + self.args[1])
            exit(1)
            
        # Finished gathering results, what type of report do we want?
        sopt = self.args[0]
        
        # Cycle thru all results gathered
        if len(lst_results) > 1:
            print("Found " + str(len(lst_results)) + " files to check...")
        elif len(lst_results) == 0:
            print("No files found to check!")
            
        for result in lst_results:
            print("\nResults for " + result.s_file + ":")
            if "i" in sopt:
                self.printimports(result)
            if "e" in sopt:
                self.printexceptions(result)
            if "v" in sopt:
                self.printvariables(result)
            if "s" in sopt:
                self.printdocstrings(result)
            if "t" in sopt:
                self.printtotals(result)
                print("")
            if sopt == "-":
                self.printreport(result)
        
        # Finished
        exit(0)
                
                
            
    def printusage(self, sreason = None):
        if sreason != None:
            print(sreason + '\n')
        print("\nUsage: ./" + self.script + " [-htdvie] script_to_analyze.py\n")
        
    def printhelp(self):
        print(self.appname +  " v." + self.version + " Help:")
        self.printusage()
        print("")
        print(" h : Show this help message")
        print(" v : Print all variables found")
        print(" i : Print all imports found")
        print(" e : Print all exceptions catchers found")
        print(" s : Print all docstrings found")
        print(" t : Print only basic totals")
        print(" d : Sorts variable/import lists in the order they were discovered,")
        print("      ...default is alphabetically.\n")
 
    def printtotals(self, res):
        """ Prints only the basic totals from results object """
        print("                        ")
        print("              Total Lines: " + str(res.itotal))
        print("                        ")
        print("               Code Lines: " + str(res.icode) + " (" + str(res.icodepercent)[:7] + "%)")
        print("              Blank Lines: " + str(res.iblank) + " (" + str(res.iblankpercent)[:7] + "%)")
        print("                        ")
        print("            Comment Lines: " + str(res.icommentline) + " (" + str(res.icommentpercent)[:7] + "%)")
        print("         Doc String Lines: " + str(res.idocstringline) + " (" + str(res.idocpercent)[:7] + "%)")
           
    def printreport(self, res):
        """ Prints results from results object """
        # Fix shortest stuff if their too long to print
        if len(res.s_shortest) > 20:
            res.s_shortest = res.s_shortest[:20] + "..."
        if len(res.s_shortestcomment) > 20:
            res.s_shortestcomment = res.s_shortestcomment[:20] + "..."
            
        # Report Information (Totals First)
        self.printtotals(res)
        # Print advanced info
        print("          Inline Comments: " + str(res.icomment))
        print("              Doc Strings: " + str(res.idocstring))
        print("           Total Comments: " + str(res.icommentline + res.icomment + res.idocstring))
        print("                        ")
        print("       Longest Code Line: " + str(res.ilongest)) # -1 because of newline char
        print("       Shortest Code Line: " + str(res.ishortest) + " [" + res.s_shortest + "]")
        print("                        ")
        print("     Longest Comment Line: " + str(res.ilongestcomment)) # -1 because of newline char
        print("    Shortest Comment Line: " + str(res.ishortestcomment) + " [" + res.s_shortestcomment + "]")
        print("                        ")
        print("                  Imports: " + str(len(res.imports)))
        print("                Functions: " + str(res.ifunction))
        print("                  Classes: " + str(res.iclass))
        print("            If Statements: " + str(res.iif))
        print("           Try Statements: " + str(res.itry))
        print("        Except Statements: " + str(res.iexcept))
        print("         Print Statements: " + str(res.iprint))
        print("              Assignments: " + str(res.iassignment))
        print("                Variables: " + str(len(res.variables)))
        print("")
    def printimports(self, res):
        """ print imports from results object """
        if len(res.imports) > 0:
            # sort imports?
            if not "d" in self.args[0]:
                res.imports = sorted(res.imports)
            # print imports
            print(" " + str(len(res.imports)) + " imports found in " + res.s_file + ":")
            for simp in res.imports:
                print(self.spacing + simp)

    def printexceptions(self, res):
        """ prints exceptions from results object """
        if len(res.exceptions) > 0:
            # sort exceptions?
            if not "d" in self.args[0]:
                res.exceptions = sorted(res.exceptions)
            # print Exceptions
            print(" " + str(len(res.exceptions)) + " of " + str(res.iexcept) +" unique exceptions found in " + res.s_file + ":")
            for sexc in res.exceptions:
                print(self.spacing + sexc)
                
        # No Exceptions Found!
        else:
            print(" No Caught Exceptions Found In " + res.s_file + "!")   

    def printvariables(self, res):
        """ print variables from results object """
        # Print Variables    
        if len(res.variables) > 0:
            # sort variables?
            if not "d" in self.args[0]:
                res.variables = sorted(res.variables)
            # print variables
            print(" " + str(len(res.variables)) + " " \
                  "variables (" + str(res.iassignment) + " " \
                  "assignments) found in " + res.s_file + ":")
            for svar in res.variables:
                print(self.spacing + svar)
        # No Variables Found!
        else:
            print(" No Variables Found In " + res.s_file + "!")

    def printdocstrings(self,res):
        """ print doc string from results object """
        # Print DocStrings
        if len(res.docstrings) > 0:
            # sort docstrings?
            if not "d" in self.args[0]:
                res.docstrings = sorted(res.docstrings)
            # print variables
            print(" " + str(len(res.docstrings)) + " " \
                  "docstrings found in " + res.s_file + ":")
            for sstr in res.docstrings:
                # Start of item/One Liner
                #if sStr.startswith('"""') or sStr.startswith("'''"):
                print(self.spacing + sstr.replace('"""', "").replace("'''", ""))
                # Continuation    
                #else:
                #    print (sSpacing * 2) + sStr
                
        # No DocStrings Found!
        else:
            print(" No DocStrings Found In " + res.s_file + "!")
                                
    def filechecker(self, sfile):
        # Test if valid file
        if not os.path.isfile(sfile):
            self.printusage("Invalid file given: " + sfile)
            exit(1)
        # Flag so we know we're in a docstring  
        bDocString = False
        
        # Initialize results object
        res = results()
        res.s_file = sfile
        
        # Get file lines
        try:
            ffile = open(sfile, 'r')
            slines = ffile.readlines()
            ffile.close()
        except IOError as exIO:
            print("Unable to open file: " + sfile)
            print("Error: " + str(exIO))
            return None
        except:
            print("Unable to open file: " + sfile)
            return None
        
        # Cycle thru lines in file
        for sline in slines:
            # trimmed versions of this line
            sline = sline.replace('\n', '')
            snotabs = sline.replace('\t', '')
            strim = snotabs.replace(' ', '')
            
            # Total
            res.itotal += 1
            
            # Inside of a DocString?
            if bDocString == True:
                res.idocstringline += 1
                # add to DocString list
                if strim != '"""' and strim != "'''":
                    res.docstrings.append(sline.replace("\n", ""))
                
                # Found end?
                if strim.endswith("'''") or strim.endswith('"""'):
                    # print "        STOP!"
                    bDocString = False
                    
            else:
                if strim.startswith('"""')or strim.startswith("'''"):
                    # Line has docstring content?
                    if (strim != '"""' and strim != "'''"):
                        # """ One Liner """
                        if ((strim.endswith('"""') or strim.endswith("'''")) and
                            (strim.startswith('"""') or strim.startswith("'''"))):
                            res.idocstring += 1
                            res.idocstringline  += 1
                            res.docstrings.append(sline.replace("\n", ""))
                            
                        # """ Start of DocString with some text
                        else:
                            res.idocstring += 1
                            res.idocstringline  +=1
                            res.docstrings.append(sline.replace("\n", ""))
                            bDocString = True
                            
                    else:
                        # Normal comments don't toggle the bDocString!
                        if not strim.startswith("#"):
                            # """, ''', """ this, or ''' this 
                            if bDocString == True:
                                bDocString = False
                            else:
                                bDocString = True
                                res.idocstring += 1
                                res.idocstringline += 1
                            
    
                # Empty Line?
                elif len(strim) == 0:
                    # Increment Blank Line Counter
                    res.iblank += 1
                    
                # Not Empty, Not DocString related:
                else:
                
                    # Doc String?
                    if bDocString:
                        res.docstrings.append(sline.replace("\n", ""))
                        
                    # Just a regular comment?:
                    elif strim.startswith("#") and strim[:2] != "#!":
                        # Increment Comment Count
                        res.icommentline += 1
                        # Longest Comment Yet?
                        if len(strim) > res.ilongestcomment:
                            res.ilongestcomment = len(sline)
                        # Shortest Comment Yet?
                        if (len(strim) < res.ishortestcomment) and (len(strim) > 1):
                            res.ishortestcomment = len(sline)
                            # Save Shortest Comment
                            res.s_shortestcomment = sline.strip()
                    # Quote Comment?
                    elif strim.startswith('"') and strim.endswith('"'):
                        # Increment Comment Count
                        res.icommentline += 1
                        # Longest Comment Yet?
                        if len(strim) > res.ilongestcomment:
                            res.ilongestcomment = len(sline)
                        # Shortest Comment Yet?
                        if (len(strim) < res.ishortestcomment) and (len(strim) > 1):
                            res.ishortestcomment = len(sline)
                            # Save Shortest Comment
                            res.s_shortestcomment = sline.strip()
                    
                            
                    # Actual Code?:
                    else:
                        # Increment Code Line Counter
                        res.icode += 1
                                
                        # Function?
                        if strim.startswith("def"):
                            res.ifunction += 1
                        # Class?
                        elif strim.startswith("class"):
                            res.iclass += 1
                        # Try?
                        elif strim.startswith("try"):
                            res.itry += 1
                        # Except?
                        elif strim.startswith("except"):
                            res.iexcept += 1
                            ssplit = sline.split(" ")
    
                            # Grab exception name if it exists
                            if len(ssplit) > 1:
                                sexc = ssplit[1].strip('\t')
                                sexc = sexc.strip('\n')
                                # If we still have an Exception, and its not added
                                # ... then add it.
                                if (len(sexc) > 0) and (sexc not in res.exceptions):
                                    res.exceptions.append(ssplit[1])
                            
                                # Grab variable name if it exists
                                if " as " in sline:
                                    # Get Variable Name
                                    svariable = ssplit[-1]
                                    # Strip junk chars
                                    svariable = svariable.strip('\n')
                                    svariable = svariable.strip(":")
                                    
                                    # Add to list of variables if not already there
                                    if ((len(svariable) > 0) and 
                                        (svariable not in res.variables)):
                                            res.variables.append(svariable)
                                        
                        # Import?
                        elif (strim.startswith("import") or 
                            (strim.startswith("from") and "import" in strim)):
                            # Initialize String
                            simport = sline
                            # Don't use the AS yet (maybe in the future)
                            if " as " in simport:
                                simport = simport.split(" as ")[0]
                                
                            # Strip comment
                            if "#" in simport:
                                simport = simport[:simport.index("#")]
                                
                            # Grab import name using "import [module]"
                            if strim.startswith("import"):
                                simport = simport[7:]
                                simport = simport.replace('\n', '')
    
                            # Grab import name using "from [module] import"
                            else:
                                simport = simport[5:].replace('\n', '')                            
                                sbase = simport.split(" ")[0]
                                ssubs = simport.replace(' ', '').split("import")[1]
                                if "," in ssubs:
                                    simportsubs = ""
                                    for subimport in ssubs.split(","):
                                        if simportsubs != "":
                                            simportsubs += ","
                                        simportsubs += sbase + "." + subimport.replace(' ', '')
                                    
                                    simport = simportsubs
                                else:
                                    # single sub import
                                    simport = sbase + "." + ssubs
                                
                                        
                                
                            # Add to list of imports
                            if "," in simport:
                                # Need to fix comma seperated values
                                lseperate = simport.split(",")
                                for simp in lseperate:
                                    if not simp in res.imports:
                                        res.imports.append(simp.replace(' ', ''))
                            else:
                                # Regular single import
                                if not simport in res.imports:
                                    res.imports.append(simport)
                        # Print?
                        elif strim.startswith("print"):
                            res.iprint += 1
                                
                        # If/ElseIf/Else?
                        elif (strim.startswith("if") or strim.startswith("elif") or
                              strim.startswith("else")):
                            res.iif += 1
                            
                        # Inline Code (Assignments / InlineComments / Variables)
                        else:
                            # Longest Line Yet?
                            if len(strim) > res.ilongest:
                                res.ilongest = len(sline)
                            # Shortest Line Yet?
                            if len(strim) < res.ishortest:
                                if len(strim) > 0:
                                    res.ishortest = len(sline)
                                    res.s_shortest = sline.strip()
                                 
                            # Inline Comments
                            if "#" in strim and (not '"' in strim):
                                res.icomment += 1
                            # Inline Comments vs. # Characters in "string"
                            elif "#" in strim and '"' in strim:
                                # Split string by " Character
                                ssplit = strim.split('"') # strings with "
                                            
                                # Simple Inline Comment?
                                if len(ssplit) == 1:
                                    res.icomment += 1
                                # Tricky Inline Comment?:(# in "string" or outside?)
                                else:
                                    # Get index for last section of string
                                    ilast = len(ssplit) - 1
                                
                                    # Get last section of string
                                    slast = ssplit[ilast]
                                
                                    # Comment in last section?
                                    if "#" in slast:
                                        res.icomment += 1
                            # Inline Comments vs. # Characters in 'string'
                            elif "#" in strim and "'" in strim:
                                # Split string by ' Character
                                ssplit = strim.split("'") # strings with '
                            
                                # Simple Inline Comment?
                                if len(ssplit) == 1:
                                    res.icomment += 1
                                    # Longest Comment Yet?
                                    if len(strim) > res.ilongestcomment:
                                        res.ilongestcomment = len(ssplit[0])
                                    # Shortest Comment Yet?
                                    if len(strim) < res.ishortestcomment:
                                        res.ishortestcomment = len(ssplit[0])
    
                                # Tricky Inline Comment?:(# in 'string' or outside?)
                                else:
                                    # Get index for last section of string
                                    ilast = len(ssplit) - 1
                                
                                    # Get last section of string
                                    slast = ssplit[ilast]
                                
                                    # Comment in last section?
                                    if "#" in slast:
                                        res.icomments += 1
                                        # Longest Comment Yet?
                                        if len(strim) > res.ilongestcomment:
                                            res.ilongestcomment = len(slast)
                                        # Shortest Comment Yet?
                                        if len(strim) < res.ishortestcomment:
                                            res.ishortestcomment = len(slast)
    
                            # Assignment Statements 
                            if "=" in sline:
                                # Found = sign, now weed outnon-assignment stuff
                                strimA = sline
                                if "==" in strimA: 
                                    strimA = strimA.replace('==','')
                                if "<=" in strimA: 
                                    strimA = strimA.replace('<=','')
                                if ">=" in strimA: 
                                    strimA = strimA.replace('>=','')
                                if "!=" in strimA: 
                                    strimA = strimA.replace('!=','')
                                # Do we still have a = sign after that?
                                if "=" in strimA:
                                    # Increment count (found kind of assignment)
                                    res.iassignment += 1
    
                                    # Grab Variable, to count variables when done.
                                
                                    # Get everything left of = character
                                    sleft = strimA[:strimA.index("=")]
                                    # Split by spaces
                                    ssplit = sleft.split(" ")
                                    
                                    # Get index of last section (to get variable name)
                                    ilast = len(ssplit) - 1
                                    # If last item is blank or ",',+,-,*,\,\\ char, 
                                    # use the next to last item
                                    if (ssplit[ilast] == "" or ssplit[ilast] == '"' or 
                                        ssplit[ilast] == '+' or ssplit[ilast] == "-" or 
                                        ssplit[ilast] == '*' or ssplit[ilast] == "/" or 
                                        ssplit[ilast] == "'" or ssplit[ilast] == "//"):
                                        ilast -= 1
                                        
                                    # "=" is inside string if " or ' is first or last char
                                    # ...doesn't count as variable. just a "#1 String"
                                    if ((not '"' in ssplit[ilast]) and 
                                        (not "'" in ssplit[ilast]) and 
                                        (ssplit[0] != "print") and 
                                        (ssplit[0] != "if")):
                                        # functions "def myfunc(data=None)" don't count...
                                        if (not ssplit[0] == "def"):
                                            
                                            # Get Variable Name
                                            svariable = ssplit[ilast].replace('\t', '')
                                            
                                            # remove ")" Char if found
                                            if svariable.endswith(")"):
                                                svariable = svariable.strip(")")
                                            # Add Variable to list IF:
                                            #   Not Already There
                                            #   Has length of at least 1
                                            #   is not a list like x[2] = 5
                                            #   is not a default parameter myfunc(x=5)
                                            if ((not svariable in res.variables) and
                                                (len(svariable) > 0) and 
                                                (not "[" in svariable) and
                                                (not "(" in svariable)):
                                                # variable passed all of our tests, append it
                                                res.variables.append(svariable)
                                                
                                            # Check for more variables declared on that line
                                            for sextra in ssplit:
                                                if len(sextra) > 1 and sextra.endswith(","):
                                                    # We found another variable on that line,
                                                    # ...so lets strip the junk characters and add it
                                                    sextra = sextra.strip("(")
                                                    sextra = sextra.strip(",")
                                                    # add it (if not already there)
                                                    if ((sextra not in res.variables) and
                                                        (len(sextra) > 0 )):
                                                        res.variables.append(sextra)
        # Finished with lines
        # Fix Shortest Variables (in case no comments were found)
        if res.ishortest == 999:
            res.ishortest = 0
        if res.ishortestcomment == 999:
            res.ishortestcomment = 0
        
        # Fix bad parsing of 'shortest' lines
        res.s_shortest = res.s_shortest.replace('\n', '').replace('\t', '')    
        while res.s_shortest.endswith(" "):
            res.s_shortest = res.s_shortest[:len(res.s_shortest) - 1]
        while res.s_shortest.startswith(" "):
            res.s_shortest = res.s_shortest[1:]
        res.s_shortestcomment = res.s_shortestcomment.replace('\n', '').replace('\t', '')    
        while res.s_shortestcomment.endswith(" "):
            res.s_shortestcomment = res.s_shortestcomment[:len(res.s_shortestcomment) - 1]
        while res.s_shortestcomment.startswith(" "):
            res.s_shortestcomment = res.s_shortestcomment[1:]
        res.ishortest = len(res.s_shortest)
        res.ishortestcomment = len(res.s_shortestcomment)
        
        # Find Percentage of Code Lines vs. Total
        res.icodepercent = (res.icode / float(res.itotal)) * 100
        # Find Percentage of Comment Lines vs. Total
        res.icommentpercent = (res.icommentline / float(res.itotal)) * 100
        # Find Percentage of Blank Lines vs. Total
        res.iblankpercent = (res.iblank / float(res.itotal)) * 100
        # Find Percentage of DocString Lines vs. Total
        res.idocpercent = (res.idocstringline / float(res.itotal)) * 100
        
        # Return Results Object
        return res
        
# ResultsClass -----------------------------
class results():
    def __init__(self):
        """ Build blank class for holding results """
        self.s_file = ""
        self.itotal = 0
        self.iblank = 0
        self.icode = 0
        self.icomment = 0
        self.icommentline = 0
        self.idocstring = 0
        self.idocstringline = 0
        self.ifunction = 0
        self.iclass = 0
        self.iif = 0
        self.itry = 0
        self.iprint = 0
        self.iassignment = 0
        self.iexcept = 0
        self.ilongest = 0
        self.ilongestcomment = 0
        self.ishortest = 999
        self.ishortestcomment = 999
        self.icodepercent = 0
        self.icommentpercent = 0
        self.iblankpercent = 0
        self.idocpercent = 0
        self.variables = []
        self.imports = []
        self.docstrings = []
        self.exceptions = []
        self.s_shortest = ""
        self.s_shortestcomment = ""
         
# Start.Of.Script --------------------------
if __name__ == '__main__':
    
    # Initialize code counter object  
    cc = codecounter()
    
    # Get args
    if len(sys.argv) < 2:
        cc.printusage("Not enough arguments!")
        exit(1)
    elif len(sys.argv) > 4:
        cc.printusage("Too many arguments!")
        exit(1)
    # Run Main with args
    cc.main(sys.argv[1:])
    