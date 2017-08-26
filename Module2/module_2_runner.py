'''
Module for running module 2. Used to ensure all of the main functionality is
viewed as a separate module file, for relative imports, as well as separating
out code that isn't related to the core functionality behind Module 2.
'''

import module2

'READ IN ASSOCIATED STATE ABBREVIATIONS WITH STATE FIPS CODES'
def read_states():
    stateFileLocation = M_PATH + '/'
    fname = stateFileLocation + 'ListofStates.csv'
    lines = open(fname).read().splitlines()
    return lines

def module_2_runner():
    count = 1
    states = read_states()
    for state in states:
        print(count)
        module2.main_script(state.split(',')[0].replace(" ",""))
        count += 1

if __name__ == '__main__':
    module_2_runner()