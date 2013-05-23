#!/usr/bin/env python

from sql_tokenizer import *
import time

import sys
sys.path.append('../swig/')
import kalashnikovDB as ak47
import test
import re



def initialize():
	ak47.AK_inflate_config()
	ak47.AK_init_disk_manager()
	ak47.AK_memoman_init()

## is_numeric
# returns int or float value based on input type
# @param lit the value to be checked
def is_numeric(lit):
    # Handle '0'
    if lit == '0': return 0
    # Hex/Binary
    litneg = lit[1:] if lit[0] == '-' else lit
    if litneg[0] == '0':
        if litneg[1] in 'xX':
            return int(lit,16)
        elif litneg[1] in 'bB':
            return int(lit,2)
        else:
            try:
                return int(lit,8)
            except ValueError:
                pass
    # Int/Float
    try:
        return int(lit)
    except ValueError:
        pass
    try:
        return float(lit)
    except ValueError:
        pass

## is_date
# returns true if the input value is in date format
# @param lit the value to be checked
def is_date(lit):
	try:
	  time.strptime(lit, '%Y-%m-%d')
	  return True
	except ValueError:
	  return False

## is_datetime
# returns true if the input value is in datetime format
# @param lit the value to be checked
def is_datetime(lit):
	returnVal = 2
	try:
		time.strptime(lit, '%Y-%m-%d %H:%M:%S')
		returnVal += 1
	except ValueError:
		returnVal -= 1
	try:
		time.strptime(lit, '%Y-%m-%d %H:%M:%S.%f')
		returnVal += 1
	except ValueError:
		returnVal -= 1
	if returnVal > 0:
		return True
	else:
		return False

## is_time
# returns true if the input value is in time format
# @param lit the value to be checked
def is_time(lit):
	try:
		time.strptime(lit, '%H:%M:%S')
		return True
	except ValueError:
		return False

## is_bool
# returns true if the input value is boolean
# @param lit the value to be checked
def is_bool(lit):
	return lit.lower() in ("true","false")

## get_attr_type
# returns value type code in ak47 notation defined in constants.c
# @param value the value to be checked
def get_attr_type(value):

	integer = type(is_numeric(value)) == int
	decimal = type(is_numeric(value)) == float
	varchar = isinstance(value,str)
	date = is_date(value.replace("'",""))
	datetime = is_datetime(value.replace("'",""))
	time = is_time(value.replace("'",""))
	boolean = is_bool(value.replace("'",""))

	if integer:
		return ak47.TYPE_INT
	elif decimal:
		return ak47.TYPE_FLOAT
	elif date:
		return ak47.TYPE_DATE
	elif datetime:
		return ak47.TYPE_DATETIME
	elif time:
		return ak47.TYPE_TIME
	elif boolean:
		return ak47.TYPE_BOOL
	elif varchar:
		return ak47.TYPE_VARCHAR
	else:
		print "UNDEFINED"

## get_type_name
# returns type name for supplied type code in ak47 notation defined in constants.c
# @param code the type code to be checked
def get_type_name(code):

	if code == ak47.TYPE_INT:
		return "int"
	elif code == ak47.TYPE_FLOAT:
		return "float"
	elif code == ak47.TYPE_DATE:
		return "date"
	elif code == ak47.TYPE_DATETIME:
		return "datetime"
	elif code == ak47.TYPE_TIME:
		return "time"
	elif code == ak47.TYPE_BOOL:
		return "boolean"
	elif code == ak47.TYPE_VARCHAR:
		return "varchar"
	else:
		return "UNDEFINED"

## akdbError
# prints expression expr and a pointer at the position of error item
# @param expr the expression to be printed
# @param item item where the error occured
def akdbError(expr,item):
	print expr
	print " " * expr.index(item) + "^"

## print_table_command
# defines the structure of print command and its execution
class Print_table_command:

	print_regex = r"^\\p\s+([a-zA-Z0-9_]+)\s*$"
	pattern = None
	matcher = None

	## matches method
	# checks whether given input matches print command syntax
	def matches(self, input):
		self.pattern = re.compile(self.print_regex)
		self.matcher = self.pattern.match(input)
		return self.matcher != None

	## execute method
	# defines what is called when print command is invoked
	def execute(self):
		ak47.AK_print_table(self.matcher.group(1))
		return "OK"

## table_derails_command
# defines the structure of table details command and its execution
class Table_details_command:

	table_details_regex = r"^\\d\s+([a-zA-Z0-9_]+)\s*$"
	pattern = None
	matcher = None

	## matches method
	# checks whether given input matches table_details command syntax
	def matches(self, input):
		self.pattern = re.compile(self.table_details_regex)
		self.matcher = self.pattern.match(input)
		return self.matcher != None

	## execute method
	# defines what is called when table_details command is invoked
	def execute(self):
		print "Printing out: "
		result = "Number of attributes: " + str(ak47.AK_num_attr(self.matcher.group(1)))
		result += "\nNumber od records: " + str(ak47.AK_get_num_records(self.matcher.group(1)))
		return result

class Table_exists_command:

	table_details_regex = r"^\\t\s+([a-zA-Z0-9_]+)\?\s*$"
	pattern = None
	matcher = None

	## matches method
	# checks whether given input matches table_exists command syntax
	def matches(self, input):
		self.pattern = re.compile(self.table_details_regex)
		self.matcher = self.pattern.match(input)
		return self.matcher != None

	## execute method
	# defines what is called when table_exists command is invoked
	def execute(self):
		if ak47.AK_table_exist(self.matcher.group(1)) == 0:
			result = "Table does not exist."
		else:
			result = "Table exists. You can see it by typing \p <table_name>."
		return result

## sql_executor
# contaions methods for sql operations
class sql_executor:

	##initialize classes for the available commands
	print_command =  Print_table_command()
	table_details_command = Table_details_command()
	table_exists_command = Table_exists_command()

	##add command instances to the commands array
	commands = [print_command, table_details_command, table_exists_command]

	## commands for input
	# checks whether received command matches any of the defined commands for kalashnikovdb, 
	# and call its execution if it matches
	def commands_for_input(self, command):
		for elem in self.commands:
			if elem.matches(command):
				return elem.execute()
		return "Wrong command."

	## execute method
	# called when a new command is received (from client)
	def execute(self, command):
		return self.commands_for_input(command)

	## insert
	# executes the insert expression
	# @param self object pointer
	# @parama expr the expression to be executed 
	def insert(self,expr):
		parser = sql_tokenizer()
		token = parser.AK_parse_insert_into(expr)
		if isinstance(token, str):
			print "Error: syntax error in expression"
			print expr
			print token
			return False
		table_name = str(token.tableName)
		# postoji li tablica
		if (ak47.AK_table_exist(table_name) == 0):
			print "Error: table '"+ table_name +"' does not exist"
			return False
		# vrijednosti podataka za unos
		insert_attr_values = map(lambda x: x.replace("'",""),list(token.columnValues[0]))
		# tipovi podataka za unos
		insert_attr_types = map(lambda x: get_attr_type(x.replace("'","")),list(token.columnValues[0]))
		#Dohvatiti listu atributa tablice
		table_attr_names = str(ak47.AK_rel_eq_get_atrributes_char(table_name)).split(";")
		#Dohvatiti tipove atributa tablice
		table_attr_types = str(ak47.AK_get_table_atribute_types(table_name)).split(";")
		# imena atributa za unos
		insert_attr_names = table_attr_names
		# navedeni su atributi za unos
		if(token.columns):
			insert_attr_names = []
			table_types_temp = table_attr_types
			table_attr_types = []
			insert_columns = list(token.columns[0])
			for index,col in enumerate(insert_columns):
				if col not in table_attr_names:
					print "\nError: table has no attribute '" + str(col) + "':"
					akdbError(expr,col)
					return False
			#provjera atributa za unos
			for ic,col in enumerate(insert_columns):
				for ia,tab in enumerate(table_attr_names):
					if col == tab:
						if tab not in insert_attr_names:
							insert_attr_names.append(tab)
							table_attr_types.append(int(table_types_temp[ia]))
						else:
							print "\nError: duplicate attribute " + tab + ":"
							akdbError(expr,tab)
							return False

			if (len(insert_columns) == len(insert_attr_values)):
				for index,tip in enumerate(insert_attr_types):
					if int(insert_attr_types[index]) != int(table_attr_types[index]):
						type_name = get_type_name(int(table_attr_types[index]))
						print "\nError: type error for attribute '" + insert_attr_names[index] + "':"
						akdbError(expr,insert_attr_values[index])
						print "Expected: " + type_name
						return False
			else:
				print "\nError: attribute names number not matching attribute values number supplied for table '" + table_name + "':"
				akdbError(expr,insert_columns[0])
				return False
		# navedene su samo vrijednosti za unos
		elif (len(table_attr_names) < len(insert_attr_values)):
			print "\nError: too many attibutes, table " + str(token.tableName) + " has " + str(len(table_attr_names)) 
			return False
		elif (len(table_attr_names) > len(insert_attr_values)):
			print "\nError: too few attibutes, table " + str(token.tableName) + " has " + str(len(table_attr_names))
			return False
		else:
			for index,tip in enumerate(insert_attr_types):
				if insert_attr_types[index] != int(table_attr_types[index]):
					type_name = get_type_name(int(table_attr_types[index]))
					print "\nError: type error for attribute '" + insert_attr_names[index] + "':"
					akdbError(expr,insert_attr_values[index])
					print "Expected: " + type_name
					return False
		if(ak47.insert_data_test(table_name,insert_attr_names,insert_attr_values,insert_attr_types) == ak47.EXIT_SUCCESS):
			return True
		else:
			return False
		return False