"""
industryReader.py

Project: United States Trip File Generation - Module 2
Author: A.P. matthewgarvey Wyrough
version date: 3/23/14
Python 3.3f

PURPOSE: This set of methods and classes provides operations enabling the
selection of an industry of work for a particular worker. It used by
workplace.py. It reads in the ACS Industry Participation by Sex by
Median Income and prepares that dataset for operations, extracting the
 relevant information.

Relies on access to the ACS Industry data.

DEPENDENCIES: None

Note: None of this code is taken from Mufti's Module 2 Synthesizer
which performs all of these tasks in an entirely different way.

"""
import random
import bisect
from ..utils import paths, reading, core

class IncomeEmployment:
    """Income and Employment data encapsulation functionality.
    
    Note that 0 refers to female, 1 refers to male.    
    
    Attributes:    
        all_inc (dict): Income related data for each county by gender, with each 
            key as a gender and value a list of lists, with each list containing
            information on income statistics for a specific county.
        all_emp (dict): Employment related data for each county by gender, with each 
            key as a gender and value a list of lists, with each list containing
            information on employment statistics for a specific county.
        id_inds (list): List of indices for row identifier information.
        emp_inc_inds (list): List of indices for employment and income related data.
        FIPS_index_dict (dict): Associates a FIPS code with an index.
    """
    def __init__(self):
        """Initializes all prerequisites to obtain income and employment data."""
        # 0 = Women, 1 = Male
        self.all_inc = {0: [], 1: []}
        self.all_emp = {0: [], 1: []}   
        self.id_inds = [0, 1, 2]
        self.emp_inc_inds = [29, 41, 53, 65, 77, 89, 113, 125, 137, 161, 
                             173, 197, 209, 221, 245, 257, 281, 293, 305, 317]
        self.FIPS_index_dict = {}
        
    def get_row_inc_emp_data(self, row):
        """Functionality for getting income and employment data from a specific row.
        
        Inputs:
            row (list): Row from file, usually of form 'SexByIndustryByCounty_MOD.csv'.
        """
        row_inc = {0: [], 1: []}
        row_emp = {0: [], 1: []}
        #Create Men Employment By Industry, Women Employment, Men Median Income By Industry, Women Med Income
        _get_row_identifiers(row_inc, row, self.id_inds)
        _get_row_identifiers(row_emp, row, self.id_inds)
        _get_row_emp_percents(row_emp, row, self.emp_inc_inds)
        _get_row_inc_data(row_inc, row, [ind + 6 for ind in self.emp_inc_inds])
        
        for key in self.all_emp:
            self.all_emp[key].append(row_emp[key])
        for key in self.all_inc:
            self.all_inc[key].append(row_inc[key])
        
        self._create_FIPS_index_dict()
        
    def _create_FIPS_index_dict(self):
        """Creates mapping from FIPS code to index in employment and income dictionary."""
        for index, county_data in enumerate(self.all_emp[1]):    
            self.FIPS_index_dict[county_data[1]] = index
    
    def get_county_index(self, work_county):
        """Get county index for a work county.
        
        Inputs:
            work_county (str): County FIPS code.
        
        Returns:
            county_idx (int): County Index of Income and Employment data 
                in IncomeEmployment.
        """
        return self.FIPS_index_dict[work_county]
        
def _get_row_identifiers(dictionary, row, indices):
    """Gets row identifier information from income and employment data.
    
    Inputs:
        dictionary (dict): Data dictionary for income and employment data.
        row (list): Row from file, usually of form 'SexByIndustryByCounty_MOD.csv'.
        indices (list): Indexes of interest from file row.
    """
    for key in dictionary:
        for index in indices:
            dictionary[key].append(row[index])

def _get_row_emp_percents(dictionary, row, indices):
    """Gets percentage information for employment data.
    
    Inputs:
        dictionary (dict): Data dictionary for income and employment data.
        row (list): Row from file, usually of form 'SexByIndustryByCounty_MOD.csv'.
        indices (list): Indexes of interest from file row.
    """
    for key in dictionary:
        for index in indices:
            total = float(row[index-2])
            if key == 0:
                index += 2 
            dictionary[key].append(float(row[index]) * total / 100.0)
                
def _get_row_inc_data(dictionary, row, indices):
    """Gets information for income data.
    
    Inputs:
        dictionary (dict): Data dictionary for income and employment data.
        row (list): Row from file, usually of form 'SexByIndustryByCounty_MOD.csv'.
        indices (list): Indexes of interest from file row.
    """
    for key in dictionary:
        for index in indices:
            if key == 0:
                index += 2 
            dictionary[key].append(float(row[index]))

def match_code_abbrev(states, code):
    """Matches state code to state abbrevation.
    
    Inputs:
        states (list): Information on each state, where each 
            element is a string of the form 'STATE_NAME, STATE_ABBREV, STATE_CODE'
        code (str): A 2 digit state code.
    
    Returns:
        state_abbrev (str): A state abbrevation.
    """
    for state_row in states:
        splitter = state_row.split(',')
        if splitter[2] == code:
            return splitter[1]
    return None

def match_name_abbrev(states, state):
    """Matches state name to state abbrevation.
    
    Inputs:
        states (list): Information on each state, where each 
            element is a string of the form 'STATE_NAME, STATE_ABBREV, STATE_CODE'
        state (str): A state name.
    
    Returns:
        state_abbrev (str): A state abbrevation.
    """
    for state_row in states:
        splitter = state_row.split(',')
        if splitter[0] == str(state):
            return splitter[1]
    return None

def read_county_employment(fips):
    """Read in county employment/patronage file and get list of all employers.
    
    Inputs:
        fips (str): FIPS code for county.
    
    Returns:
        employer_list (list): List of all employers associated with county.
    """
    with open(paths.MAIN_DRIVE + 'ListOfStates.csv') as state_file:
        states = reading.file_reader(state_file)
    code = fips[0:2]
    abbrev = match_code_abbrev(states, code)
    file_path = paths.COUNTY + abbrev + '/' + fips + '_' + abbrev + '_EmpPatFile.csv'
    with open(file_path) as file:
        return list(reading.csv_reader(file))

def dist_index_to_naisc_code(index):
    """Returns NAISC Code Corresponding to index of distribution.
    
    Inputs:
        index (int): Index of industry distribution.
    
    Returns:
        naisc_code (int): 2 Digit NAISC Code.
    """
    indextocode = [(0, 11), (1, 21), (2, 23), (3, 31), (4, 42), (5, 44),
                   (6, 48), (7, 22), (8, 51), (9, 52), (10, 53), (11, 54),
                   (12, 55), (13, 56), (14, 61), (15, 62), (16, 71), (17, 72),
                   (18, 81), (19, 92)]
    return str(indextocode[index][1])

def read_employment_income_by_industry():
    """Returns employment and income data by gender by industry for every county.
     
    Returns:
        inc_emp (IncomeEmployment): Object containing income and employment data 
            as well as functions to interact with this data.
    """
    with open(paths.EMPLOYMENT + 'SexByIndustryByCounty_MOD.csv') as empl_file:
        reader = reading.csv_reader(empl_file)
        next(reader)
        inc_emp = IncomeEmployment()
        for row in reader:
            inc_emp.get_row_inc_emp_data(row)
        return inc_emp

def get_work_industry(work_county, gender, income, inc_emp, markers):
    """Returns the industry of work given information about a worker.
    
    Inputs:
        work_county (str): The FIPS code for a given county.
        gender (int): 0 for Female, 1 for Male.
        income (float): Worker's income.
        inc_emp (IncomeEmployment): Income Employment data for a given county.
        markers (list): Each element describes if an NAISC industry does not have
            any employers of this type in the county. See dist_index_to_naisc_code
            for index -> NAISC mapping.
     
    Returns:
        industry (str): 2 Digit NAISC Industry Code.
        idx (int): Index of this NAISC Industry Code in index list.
    """
    #Non-Worker.
    if work_county == '-1':
        return -1, -1
    #International Worker
    if work_county == '-2':
        return -2, -2
    #Normal In-Country Worker
    county_idx = inc_emp.get_county_index(work_county)
    #Grab Distributions According to Gender of Worker'
    empdata = inc_emp.all_emp[gender][county_idx][3:]
    incdata = inc_emp.all_inc[gender][county_idx][3:]
    #Zero Out Industries If No Employers Exist Within Actual Employment Data
    _zero_industries(markers, empdata, incdata)
    #Create distribution
    incdata[:] = [(x - income)**2 for x in incdata]
    try:
        draw_list = [x / y for x, y in zip(empdata, incdata)]
    except:
        #Issue where income is equal to x - rare, but possible
        #Overcome it by perturbing income
        incdata[:] = [(x - (income+0.01))**2 for x in incdata]
        draw_list = [x / y for x, y in zip(empdata, incdata)]
    weights = core.cdf(draw_list)
    x = random.random()
    idx = bisect.bisect(weights, x)
    #Get Industry Code
    industry = dist_index_to_naisc_code(idx)
    return industry, idx

def _zero_industries(markers, empdata, incdata):
    """Zeros out industries types that do not have any employers in a county.
    
    Inputs:
        markers (list): Each element describes if an NAISC industry does not have
            any employers of this type in the county. See dist_index_to_naisc_code
            for index -> NAISC mapping.
        empdata (list):
        incdata (list):
     
    Returns:
        industry (str): 2 Digit NAISC Industry Code.
        idx (int): Index of this NAISC Industry Code in index list.
    """
    count = 0
    for j in markers:
        if markers[count]:
            empdata[count] = 0.0
            incdata[count] = 200000
        count += 1
        