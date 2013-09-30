#!/usr/bin/env python
# -*- coding: UTF-8 -*- #

# A minimal SQLite shell for experiments with SQL
# Based on example from http://docs.python.org/library/sqlite3.html
# Re-coded by Christopher Joseph Welborn
from __future__ import print_function
import sys
import sqlite3

# Globals
buffer = ""
sprompt = "sqlite : "
sprompt2 = "sqlite*: "
con = None
cur = None
str_file = ":memory:"
fetched = []

def print_fetched():
	if fetched == None:
		print(sprompt + "No data found!\n")
	else:
		# cycle thru fetched data items
		for itm in fetched:
			# cycle thru subitems of fetched data
			soutput = ""
			for subitm in range(len(itm)):
				# add space if first item
				if len(soutput) > 0:
					soutput = soutput + " "
				# build output line
				sdata = str(itm[subitm])
				soutput = soutput + str(sdata)
				
			# print output line
			print(sprompt + soutput)

def main():
	global buffer, smulti
	global con, cur
	global fetched

	# Use a file instead of memory?
	str_file = ":memory:"
	if len(sys.argv) > 1:
		str_file = sys.argv[1]


	try:
		print(" ")
		con = sqlite3.connect(str_file)
		if str_file == ":memory:":
			print(sprompt + "Connected to database using RAM!\n")
		else:
			print(sprompt + "Connected to database using " + str_file + "!\n")
	except:
		print(sprompt + "Cannot connect to " + str_file + "!")
		exit()

	con.isolation_level = None
	cur = con.cursor()
	print(sprompt + "Please add a ; after all SQL statements...\n")
	print(sprompt + "Type 'help' for a list of commands...\n")

# START LOOP
	while True:
		# Print PROMPT
		if len(buffer) == 0:
			print(sprompt, end="")
		else:
			print(sprompt2, end="")

		# Get Input
		line = raw_input()

		# EMPTY LINE?
		if line == "":
			break
		# COMMANDS/HELP
		elif line.upper() == "COMMANDS" or line.upper() == "HELP":
			print(" ")
			print("Current List of Commands:")
			print("	     COMMANDS/HELP : Show this message")
			print("		 QUIT/EXIT : Quit this sqlite shell")
			print("		 PRINTLAST : Print last fetched data")
			print("	            COMMIT : Commit changes to database")
			print("   COLUMNS tbl_name : Get column headers")
			print("  COLUMNS+ tbl_name : Get column names + types")
			print("	            TABLES : Get table names from database")
			print(" ")

		# QUIT/EXIT
		elif (line.upper() == "QUIT" or
			  line.upper() == "EXIT"):
		   break

		# CLEAR BUFFER
		elif line.upper() == "CLEAR":
			buffer = ""
			print(sprompt + "Buffer Cleared!\n")

		# LAST / PRINT ALL (From Last Statement)
		elif line.upper().endswith("LAST"):
			print_fetched()

		# COMMIT
		elif (line.upper().startswith("COMMIT") or
			  line.upper().startswith("SAVE")):
			con.commit()
			print(sprompt + "Commited to " + str_file.replace(":", "") + "!")

		# COLUMN NAMES
		elif (line.upper().startswith("COLUMNS") and
			  (not "COLUMNS+" in line.upper())):
			# Split line to get table name
			ssplit = line.split(" ")
			if len(ssplit) < 2:
				print(sprompt + "Expecting a table name like 'columns table1'!")
			else:
				stable = ssplit[1]
				print(sprompt + "Getting column names for " + stable + "...\n")
				squery = "PRAGMA table_info(" + stable + ");"
				 # Send query
				cur.execute(squery)
				# Get column names from query
				fetched = cur.fetchall()
				# Initialize final header string
				sheader = ""
				for itms in fetched:
					# add space if needed
					if len(sheader) > 0:
						sheader = sheader + " "
					# add column name to header string
					sheader = sheader + itms[1]
				# print header string
				print(sprompt + sheader)

		# COLUMN NAMES with TYPE
		elif line.upper().startswith("COLUMNS+"):
			ssplit = line.split(" ")
			if len(ssplit) < 2:
				print(sprompt + "Expecting a table name like 'columns+ table1'!")
			else:
				stable = ssplit[1]
				print(sprompt + "Getting column names/types for " + stable + "...\n")
				squery = "PRAGMA table_info(" + stable + ");"
				 # Send query
				cur.execute(squery)
				# Get column names from query
				fetched = cur.fetchall()
				for itms in fetched:
					# print column name and type
					print(sprompt + itms[1] + " " + itms[2])

		# TABLES (Get table names)
		elif line.upper().startswith("TABLES"):
			# status
			print(sprompt + "Getting list of table names...\n")
			# build query
			squery = "SELECT name FROM sqlite_master WHERE type = 'table';"
			# execute query
			cur.execute(squery)
			# get response to query
			fetched = cur.fetchall()
			# print data
			print_fetched()

		# SQL STATEMENT
		else:

			# add space if multiline statement
			if len(buffer) > 0:
				buffer = buffer + " " + line.strip('\n')
			else:
				buffer = buffer + line.strip('\n')

			# test buffer
			if sqlite3.complete_statement(buffer.strip()):
				try:
					buffer = buffer.strip()
					cur.execute(buffer)
					print(sprompt + "...")
					# SELECT/PRAGMA command used?
					if (buffer.lstrip().upper().startswith("SELECT") or
						buffer.lstrip().upper().startswith("PRAGMA")):
						# Get data from query...
						print(sprompt + "Fetching data...\n")
						# print fetched items
						fetched = cur.fetchall()
						print_fetched()

				except sqlite3.Error as e:
					print(sprompt + "An error occurred: " + e.args[0])

				# Clear Buffers
				buffer = ""

	# Out of LOOP
	con.close()

	print(sprompt + "Finished.")
	exit()

# RUN
if __name__ == "__main__":
	main()
