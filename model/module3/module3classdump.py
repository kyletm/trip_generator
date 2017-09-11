'''
module3classdump.py

author: Garvey, Marocchini
purpose: This module houses accessory functions that are used to produce the output in module3.
Python 3.5

'''

'---------------GLOBAL DATA---------------'
M_PATH = 'D:/Data'
'-----------------------------------------'

import subprocess

'Match State Code to State Abbrev'
def match_code_abbrev(states, code):
	for i, j in enumerate(states):
		splitter = j.split(',')
		if splitter[2] == code:
			return splitter[1]
	return None
'Match the state name to a state abbreviation'
def match_name_abbrev(states, state):
    if state[:3] == 'New':
        print(state)
        state = 'New '+state[3:]
        print(state)
    if state[:4] == 'West':
        state = 'West '+state[4:]
    if state[:5] == 'North':
        state = 'North '+state[5:]
    if state[:5] == 'South':
        state = 'South '+state[5:]
    if state[:5] == 'Rhode':
        state = 'Rhode '+state[5:]
    for i, j in enumerate(states):
        splitter = j.split(',')
        if splitter[0] == str(state):
            return splitter[1]
    return None
'READ IN ASSOCIATED STATE ABBREVIATIONS WITH STATE FIPS CODES'
def read_states():
	stateFileLocation = M_PATH + '/'
	fname = stateFileLocation + 'ListofStates.csv'
	lines = open(fname).read().splitlines()
	return lines

def sort_ByInputColumn(inputPath, inputFile, sortColumn, outputPath, outputFile):
    scriptPath = "/Users/Kyle/Documents/Rscript_SortByInputColumn.R"
    subprocess.call(["C:/R/R-3.3.1/bin/Rscript.exe", scriptPath, inputPath, inputFile,  str(sortColumn), outputPath, outputFile])