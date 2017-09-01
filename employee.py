import argparse
from datetime import datetime
import model.utils.paths as paths
import model.utils.reading as reading
import model.utils.writing as writing

class EmployerFileBuilder:

    def __init__(self, state):
        self.state = state
        self.build_data_storage()
        self.code = match_abbrev_code(self.states, self.state)
        self.zip_dict = {fips.split(',')[0]: fips.split(',')[1] for fips in self.zip_data}

    def build_data_storage(self):
        with open(paths.MAIN_DRIVE + 'ListofStates.csv') as state_file, \
        open(paths.ZIP_PATH + 'zipCountyDictionary.csv') as zip_file, \
        open(paths.PAT_PATH + 'epfile_' + self.state + '.csv') as pat_file, \
        open(paths.WORKFLOW_PATH + '/allCounties.csv') as county_file:

            self.states = reading.file_reader(state_file)
            self.zip_data = reading.file_reader(zip_file)

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

    'Return FIPS County code for a given zip code'
    def lookup_zip(self, zip_code):
        if len(zip_code) < 5:
            zip_code = '0' + zip_code
        return self.zip_dict[zip_code]

    'Match County Name from EMP file to County Name in FIPS Related Data'
    def lookup_name(self, county_name, code):
        for county in self.name_data:
            splitter = county_name.strip('"').split(' ')
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

    'Read in state employement file, parse it into county files'
    def state_employment_to_county_employment(self):
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
                row_fips = self.lookup_name(employer[5], self.code)
            if row_fips is None:
                print('none row_fips', employer)
                print(employer[5])
                break
            if row_fips not in seen_fips:
                seen_fips.add(row_fips)
                fips_data[row_fips] = []

            for _, fips in enumerate(seen_fips):
                if row_fips == fips:
                    fips_data[row_fips].append(employer)
                    break
            if count % 1000 is 0:
                print(count/len(self.patronage_data) * 100, 'percent complete')

        print(self.state + " is writing after this much time: " + str(datetime.now()-start_time))
        for fips in fips_data.keys():
            with open(paths.COUNTY_PATH + self.state + '/' + str(fips) + '_' + self.state
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
        print('Unable to correct FIPS for', city_name)
        fips = None
    return fips

def match_abbrev_code(states, abbrev):
    for _, state in enumerate(states):
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
