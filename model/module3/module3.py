'''
module3.py

Project: United States Trip File Generation - Module 3
Author: Garvey, Marocchini
version date: 9/17/2016
Python 3.5

Purpose: This is the executive function for Task 3 (Module 3) that assigns
a school to every resident that is of a school age, or attends college.

Dependencies: schoolCounty.py

Notes: The structure is inspired by Hill Wyrough's Module 3. The supporting modules
were originally written by Hill Wyrough, and were debugged in order to correctly
and efficiently process large state files (TX, CA).
'''

from datetime import datetime
from ..utils import core
from . import assign_county, school_assigner

SCHOOL_COUNTY_INDEX = 31

def main(state):
    start_time = datetime.now()
    print('assign all individuals in a state to a school county')
    assign_county.main(state)
    print('sort the individuals by school county')
    input_path = 'D:/Data/Output/Module3/'
    output_path = 'D:/Data/Output/Module3/'
    input_file = state + 'Module3NN_AssignedSchoolCounty.csv'
    output_file = state + 'Module3NN_AssignedSchoolCounty_SortedSchoolCounty.csv'
    core.sort_by_input_column(input_path, input_file, str(SCHOOL_COUNTY_INDEX),
                              output_path, output_file)
    print('assign all indivduals to a school')
    school_assigner.main(state)
    print('School Assignments for the state of ' + str(state) + 'took this long: '
          + str(datetime.now() - start_time))