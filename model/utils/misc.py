'''
Module for miscellaneous shared functions. 
'''
from . import paths

def read_states():
    state_file_path = paths.MAIN_DRIVE + 'ListofStates.csv'
    lines = open(state_file_path).read().splitlines()
    return lines