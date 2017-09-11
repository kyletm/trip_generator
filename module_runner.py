'''
Module for running all project modules. Used to ensure all of the main functionality is
viewed as a separate module file, for relative imports, as well as separating
out code that isn't related to the core functionality behind Module 2.
'''

import importlib
import argparse
import model.utils.paths as paths
import model.utils.reading as reading

def dynamic_module_import(module):
    package = 'model'
    return importlib.import_module('.' + module + '.' + module, package)      

def module_runner(states, module):
    imported_module = dynamic_module_import(module)
    if states is None:
        count = 1
        with open(paths.MAIN_DRIVE + 'ListofStates.csv') as state_file:
            states = reading.file_reader(state_file)
        for state in states:
            print(count)
            imported_module.main(state.split(',')[0].replace(' ',''))
            count += 1
    else:
        for state in states:
            imported_module.main(state)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run modules within trip generator.')
    parser.add_argument('-m', '--module',
                        help='Module to run', metavar='MODULE')
    parser.add_argument('-s', '--states', nargs = '+',
                        help='States to run')
    args = parser.parse_args()
    module_runner(args.states, args.module)