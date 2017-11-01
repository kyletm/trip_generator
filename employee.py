import argparse
from datetime import datetime
import model.utils.paths as paths
import model.utils.reading as reading
import model.utils.writing as writing

class EmployerFileBuilder:
    """All functionality necessary to list every employer for every county.
    
    Attributes:    
        state (str): The two character abbrevation of the state for which we
            are building files (e.g. WY - Wyoming, NJ - New Jersey, etc)
        code (str): Two digit state code corresponding to state (e.g. 56 - WY, 
            34 - NJ)
        states (list): Information on each state, where each 
            element is a string of the form 'STATE_NAME, STATE_ABBREV, STATE_CODE'
        zip_dict (dict): An incomplete mapping of Zip Code to FIPS Code.
        name_data (list): Information on each county, where the first element 
            is a FIPS code, and a second element is a list with each element
            the space-split county name associated with the corresponding FIPS code.
        patronage_data (list): Information on every employer associated with
            the state.
    """
    def __init__(self, state):
        """Initializes all prerequisites to generate employee county files.
        
        Inputs:
            state (str): The two character abbrevation of the state for which we
                are building files (e.g. WY - Wyoming, NJ - New Jersey, etc)
        """
        self.state = state
        self.build_data_storage()
        self.code = match_abbrev_code(self.states, self.state)

    def build_data_storage(self):
        """Builds all data storage to generate employee county files.
        
        Note that to map zip codes to FIPS codes, we rely on an externally
        generated partial mapping from the above in a .json file. Wyrough
        initially tried to generate his own using the zipcty.txt files but
        left little to no documentation as to the source of these files. They
        have been removed as a dependency from this project. 
        
        More info on zip2fips.json can be found at: 
        https://github.com/bgruber/zip2fips
        """
        with open(paths.MAIN_DRIVE + 'ListofStates.csv') as state_file, \
        open(paths.ZIP + 'zip2fips.json') as zip_file, \
        open(paths.PAT + 'epfile_' + self.state + '.csv') as pat_file, \
        open(paths.WORKFLOW + '/allCounties.csv') as county_file:

            self.states = reading.file_reader(state_file)
            self.zip_dict = reading.json_reader(zip_file)

            self.name_data = []
            self.patronage_data = []

            reader = reading.csv_reader(pat_file)
            next(reader)
            for row in reader:
                self.patronage_data.append(row)

            county_data = reading.file_reader(county_file)
            for line in county_data:
                splitter = line.split(',')
                self.name_data.append([splitter[3], splitter[6].split(' ')])

    def lookup_zip(self, zip_code):
        """Return FIPS County code for a given zip code.
        
        Inputs:
            zip_code (str): A zip code for a county.
        
        Returns:
            fips_code (str): A FIPS code for a county.
        """
        if len(zip_code) < 5:
            zip_code = '0' + zip_code
        return self.zip_dict[zip_code]

    def lookup_name(self, county_name, code):
        """Match County Name from EMP file to County Name in FIPS Related Data.
        
        This string comparison is slow and should only be used when a mapping between
        zip code to fips code does not exist.
        
        Inputs:
            county_name (str): Name of the county.
            code (str): Two digit state code corresponding to state.
        
        Returns:
            fips_code (str): A FIPS code for a county.
        """
        splitter = county_name.strip('"').split(' ')
        for county in self.name_data:
            if splitter[0] == county[1][0] and len(splitter) == 1:
                if county[0][0:2] == code:
                    return county[0]
            elif splitter[0] == county[1][0] and splitter[1] == county[1][1] and len(splitter) == 2:
                if county[0][0:2] == code:
                    return county[0]
            elif len(county[1]) == 3 and len(splitter) > 2:
                if splitter[0] == county[1][0] and splitter[1] == county[1][1] and splitter[2] == county[1][2]:
                    if [0][0:2] == code:
                        return county[0]
            elif len(county[1]) > 3 and len(splitter) > 1:
                if splitter[0] == county[1][0] and splitter[1] == county[1][1]:
                    if county[0][0:2] == code:
                        return county[0]

    def state_employment_to_county_employment(self):
        """Read in state employement file and parse it into county files.
        
        This generates files that tell the employers for each county. It is
        of a similar format to the state files, except that each file is 
        identified by FIPS code and not State code.
        """
        seen_fips = set()
        fips_data = {}
        start_time = datetime.now()
        print(self.state + " started at " + str(datetime.now())
              + " duration: " + str(datetime.now()-start_time))

        print('Processing through', len(self.patronage_data), 'employers')
        count = 0
        for employer in self.patronage_data:
            count += 1
            #Look up county name to get FIPS code
            if employer[5] == 'NA':
                row_fips = guess_fips_from_city(employer[2])
            else:
                try:
                    row_fips = self.lookup_zip(employer[4])
                except KeyError:
                    row_fips = self.lookup_name(employer[5], self.code)
                    if row_fips is None:
                        raise ValueError('Unable to determine FIPS for' + str(employer))
            if row_fips not in seen_fips:
                seen_fips.add(row_fips)
                fips_data[row_fips] = []

            for _, fips in enumerate(seen_fips):
                if row_fips == fips:
                    fips_data[row_fips].append(employer)
                    break
            if count % 10000 is 0:
                print(count/len(self.patronage_data) * 100, 'percent complete')

        print(self.state + " is writing after this much time: " + str(datetime.now()-start_time))
        for fips in fips_data.keys():
            with open(paths.COUNTY + self.state + '/' + str(fips) + '_' + self.state
                      + '_EmpPatFile.csv', 'w+') as county_employment_file:
                writer = writing.csv_writer(county_employment_file)
                for k in fips_data[fips]:
                    writer.writerow([k[0].strip('"')] + [k[1].strip('"')] + [k[2].strip('"')]
                                    + [k[3].strip('"')] + [k[4].strip('"')] + [k[5].strip('"')]
                                    + [k[6].strip('"')] + [k[7].strip('"')] + [k[8].strip('"')]
                                    + [k[9].strip('"')] + [k[10].strip('"')] + [k[11].strip('"')]
                                    + [k[12].strip('"')] + [k[14].strip('"')] + [k[16].strip('"')]
                                    + [k[19].strip('"')] + [k[20].strip('"').strip('\n')])
        print(self.state + " took this much time: " + str(datetime.now()-start_time))

def guess_fips_from_city(city_name):
    """Guesses FIPS code based on city name.
    
    Mostly used for non-standard Alaskan Bourough FIPS code identification.
    
    Inputs:
        city_name (str): Name of the county by major city.
    
    Returns:
        fips (str): A FIPS code for a county.
    """
    if city_name in ['Hoonah', 'HOONAH', 'Angoon', 'ANGOON', 'PELICAN', 'TENAKEE SPRINGS']:
        fips = '02105'
    elif city_name in ['Petersburg', 'PETERSBURG', 'KAKE', 'PORT ALEXANDER']:
        fips = '02195'
    elif city_name in ['KLAWOCK', 'THORNE BAY', 'METLAKATLA', 'COFFMAN COVE', 'CRAIG']:
        fips = '02198'
    elif city_name in ['HYDABURG', 'POINT BAKER']:
        fips = '02198'
    elif city_name in ['GUSTAVUS', 'ELFIN COVE']:
        fips = '02198'
    elif city_name in ['SKAWGAY', 'SKAGWAY']:
        fips = '02230'
    elif city_name == 'WRANGELL':
        fips = '02275'
    else:
        print('Unable to guess FIPS for', city_name)
        fips = None
    return fips

def match_abbrev_code(states, abbrev):
    """Matches state abbrevation to state code.
    
    Inputs:
        states (list): Information on each state, where each 
            element is a string of the form 'STATE_NAME, STATE_ABBREV, STATE_CODE'
        abbrev (str): A state abbrevation.
    
    Returns:
        state_code (str): A state code for a state.
    """
    for state in states:
        splitter = state.split(',')
        if splitter[1] == abbrev:
            return splitter[2]

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate County Employee Files for a state.')
    parser.add_argument('-s', '--states', nargs='+', help='State(s) to run')
    args = parser.parse_args()
    for state in args.states:
        print('Generating all County Employee Files for state:', state)
        current_state_file = EmployerFileBuilder(state)
        current_state_file.state_employment_to_county_employment()
