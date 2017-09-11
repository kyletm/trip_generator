'''
module3.py

Project: United States Trip File Generation - Module 3
Author: Garvey, Marocchini
version date: 9/17/2016
Python 3.5

Purpose: This is the executive function for Task 3 (Module 3) that assigns a school to every resident that is of a school age, or attends college. 

Dependencies: schoolCounty.py

Notes: The structure is inspired by Hill Wyrough's Module 3. The supporting modules
were originally written by Hill Wyrough, and were debugged in order to correctly
and efficiently process large state files (TX, CA). 
'''

from datetime import datetime
import module3classdump
import assignCounty
import schoolAssigner


'---------------GLOBAL DATA---------------'
'Index in an R object of type "data.frame":'
schoolCounty_Index = 31 
'-----------------------------------------'


'''
1.) assign all individuals in a state to a school county
2.) sort the individuals by school county
3.) assign all indivduals to a school
'''
def executive(state):
	startTime = datetime.now()
	print('assign all individuals in a state to a school county')
	assignCounty.executive(state)
	print('sort the individuals by school county')
	inputPath = 'D:/Data/Output/Module3/'
	outputPath = 'D:/Data/Output/Module3/'
	inputFile = state + 'Module3NN_AssignedSchoolCounty.csv'
	outputFile = state + 'Module3NN_AssignedSchoolCounty_SortedSchoolCounty.csv'
	sortColumn = schoolCounty_Index
	module3classdump.sort_ByInputColumn(inputPath, inputFile, sortColumn, outputPath, outputFile)
	print('assign all indivduals to a school')
	schoolAssigner.executive(state)
	print('School Assignments for the state of ' + str(state) + 'took this long: ' + str(datetime.now() - startTime))

def fakeExecutive(state):
#    print('assign all individuals in a state to a school county')
#    assignCounty.executive(state)
#    print('sort the individuals by school county')
#    inputPath = 'D:/Data/Output/Module3/'
#    outputPath = 'D:/Data/Output/Module3/'
#    inputFile = state + 'Module3NN_AssignedSchoolCounty.csv'
#    outputFile = state + 'Module3NN_AssignedSchoolCounty_SortedSchoolCounty.csv'
#    sortColumn = schoolCounty_Index
#    module3classdump.sort_ByInputColumn(inputPath, inputFile, sortColumn, outputPath, outputFile)
    print('assign all indivduals to a school')
    schoolAssigner.executive(state)

def read_states():
      M_PATH = "D:/Data"
      stateFileLocation = M_PATH + '/'
      fname = stateFileLocation + 'ListofStates.csv'
      lines = open(fname).read().splitlines()
      return lines

def module3runner():
    count = 1
    states = read_states()
    for state in states:
        print(state)
        count +=1
        executive(state.split(',')[0].replace(" ",""))
  
import sys
#exec('module3runner()')
#cProfile.run("exec('module3runner()')")
exec('executive(sys.argv[1])')
#exec('fakeExecutive(sys.argv[1])')