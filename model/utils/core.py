import os
import subprocess
from . import paths, reading

def sort_by_input_column(input_path, input_file, sort_column, output_path, output_file):
   """Sort a file by a specified column.

   Inputs:
       input_path (str): Path to input file.
       input_file (str): Input file name.
       sort_column (str): Numeric column to sort.
       output_path (str): Path to output file.
       output_file: Output file name.
   """
   base_module_path = os.path.dirname(os.path.realpath(__file__))
   script_path = base_module_path + '/' + 'sort_by_input_column.r'
   subprocess.call([paths.R_SCRIPT_EXE, script_path,
                     input_path, input_file, sort_column,
                     output_path, output_file])

def correct_FIPS(fips, is_work_county_fips=False):
    """Corrects common FIPS code errors.

    Inputs:
        fips (str): FIPS code for a county.
        is_work_county_fips (bool): Provides extended functionality for
            FIPS codes used for the WorkingCounty class.

    Returns:
        fips (str): Corrected FIPS code for a county.
    """
    if len(fips) != 5:
        if is_work_county_fips:
            if fips != '-1' and fips != '-2':
                fips = '0' + fips
                if len(fips) != 5:
                    raise ValueError('FIPS does not have a length of'
                                     + ' five after zero was left padded')
        else:
            fips = '0' + fips
            if len(fips) != 5:
                raise ValueError('FIPS does not have a length of'
                                 + ' five after zero was left padded')
    if fips == '15005':
        fips = '15009'
    return fips

def read_states():
    """Reads in state data.
    
    Returns:
        states (list): Information on each state, where each 
            element is a list of the form 'STATE_NAME', 
            'STATE_ABBREV', 'STATE_CODE'.
    """
    file_path = paths.MAIN_DRIVE + '/'
    file = file_path + 'ListofStates.csv'
    with open(file) as file:
       reader = reading.csv_reader(file)
       lines = []
       for row in reader:
           lines.append(row)
    return lines
 
def match_code_abbrev(states, code):
    """Matches state code to state abbrevation.
    
    Inputs:
        states (list): Information on each state, where each 
            element is a list of the form 'STATE_NAME', 
            'STATE_ABBREV', 'STATE_CODE'.
        code (str): A 2 digit state code.
    
    Returns:
        state_abbrev (str): A state abbrevation.
    """
    for state_row in states:
        if state_row[2] == code:
            return state_row[1]
    raise ValueError('No state found for this code')
    
def match_name_abbrev(states, state):
    """Matches state name to state abbrevation.
    
    Inputs:
        states (list): Information on each state, where each 
            element is a list of the form 'STATE_NAME', 
            'STATE_ABBREV', 'STATE_CODE'.
        state (str): The name of the state.
    
    Returns:
        state_abbrev (str): A state abbrevation.
    """
    # TODO - Investigate if ListOfStates.csv can rewritten so that
    # there is no need to check spacing in state names as below...
    if state[:3] == 'New':
        state = 'New '+state[3:]
    if state[:4] == 'West':
        state = 'West '+state[4:]
    if state[:5] == 'North':
        state = 'North '+state[5:]
        state = 'South '+state[5:]
    if state[:5] == 'Rhode':
        state = 'Rhode '+state[5:]
    for state_row in states:
        if state_row[0] == state:
            return state_row[1]
    raise ValueError('No state found for this name')

def cdf(weights):
    """Create CDF of weighted list.
    
    Inputs:
        weights (list): A list of numeric weights. For example, one weight
            is the number of employees in a county's industry for a given
            gender divided by the sum of the squared difference of a worker's
            income from the median income for all industries in a county for
            that worker's gender.
     
    Returns:
        cdf (list): A CDF of this weighted list.
    """
    total = sum(weights)
    cdf = []
    cumsum = 0
    for w in weights:
        cumsum += w
        cdf.append(cumsum/total)
    return cdf

def state_county_dict():
    """Creates state-county-fips dictionary mapping.
     
    Returns:
        state_county_dict (dict): Each key is a state abbrevation, that 
            maps to another dictionary with every county for that state,
            with key as county name and value county FIPS code.
    """
    file = paths.MAIN_DRIVE + '/' + 'ListofStates.csv'
    with open(file) as read:
        reader = reading.csv_reader(read)
        states = []
        county_dicts = []
        for row in reader:
            county_dicts.append(county_dict(row[1]))
            states.append(row[1])
    return dict(zip(states, county_dicts))

def county_dict(abbrev):
    """Creates county-fips dictionary mapping.
     
    Inputs: 
        abbrev (str): A 2 character state abbrevation.
     
    Returns:
        county-fips (dict): Each key is a county name, with value the
            FIPS code for that county.
    """
    file = paths.MAIN_DRIVE + '/' + 'countyfips.csv'
    with open(file) as read:
        reader = reading.csv_reader(read)
        counties = []
        county_codes = []
        for row in reader:
            if row[0] == abbrev:
                if abbrev == 'DC':
                    counties.append(row[3])
                    county_codes.append(row[1]+row[2])
                if abbrev == 'AK':
                    if 'Census Area' in row[3]:
                        counties.append(row[3].partition(' Census Area')[0])
                        county_codes.append(row[1]+row[2])
                    elif 'Borough' in row[3]:
                        if 'City and Borough' in row[3]:
                            counties.append(row[3].partition(' City and Borough')[0])
                            county_codes.append(row[1]+row[2])
                        else:
                            counties.append(row[3].partition(' Borough')[0])
                            county_codes.append(row[1]+row[2])
                    elif 'Municipality' in row[3]:
                        counties.append(row[3].partition(' Municipality')[0])
                        county_codes.append(row[1]+row[2])
                if abbrev == 'FL':
                    if 'DeSoto' in row[3]:
                        counties.append('De Soto')
                        county_codes.append(row[1]+row[2])
                    else:
                        counties.append(row[3].partition(' County')[0])
                        county_codes.append(row[1]+row[2])
                if abbrev == 'GA':
                    if 'DeKalb' in row[3]:
                        counties.append('De Kalb')
                        county_codes.append(row[1]+row[2])
                    else:
                        counties.append(row[3].partition(' County')[0])
                        county_codes.append(row[1]+row[2])
                if abbrev == 'MD':
                    if 'Baltimore City' in row[3]:
                        counties.append('Baltimore City')
                        county_codes.append(row[1]+row[2])
                    else:
                        counties.append(row[3].partition(' County')[0])
                        county_codes.append(row[1]+row[2])
                if abbrev == 'LA':
                    if 'Parish' in row[3]:
                        counties.append(row[3].partition(' Parish')[0])
                        county_codes.append(row[1]+row[2])
                    else:
                        counties.append(row[3].partition(' County')[0])
                        county_codes.append(row[1]+row[2])
                if abbrev == 'VA':
                    if 'City' in row[3]:
                        counties.append(row[3])
                        county_codes.append(row[1]+row[2])
                    else:
                        counties.append(row[3].partition(' County')[0])
                        county_codes.append(row[1]+row[2])
                else:
                    counties.append(row[3].partition(' County')[0])
                    county_codes.append(row[1]+row[2])
    return dict(zip(counties, county_codes))