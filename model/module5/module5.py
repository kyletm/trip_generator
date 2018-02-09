from . import activity, findOtherTrips
from ..utils import reading, writing, paths, core
from datetime import datetime
import pandas as pd
import os

TEMP_FNAME = 'Module5Temp.csv'
ROW_SEGMENT_IND = 11
TRIP_SEGMENT_LENGTH = 8

class TripTour:
    """Represents a traveller's daily trip tour.

    Trip tours are represented using the order of trips taken by a given
    person. Each trip comprising a trip tour is a list of eight elements,
    containing information about origin and destination nodes (e.g. node
    type, node location, etc) comprising a trip.

    Attributes:
        row (int): Row number from Module 4 output associated with traveller.
        trip_tour (list): Trip tour taken by the person.
    """
    def __init__(self, row, personal_info):
        '''Builds trip tour for traveller, beginning with personal info

        Inputs:
            row (int): Row number from Module 4 associated with traveller.
            personal_info (list): Personal attributes of traveller from
                Module 4.
        '''
        self.row = row
        self.tour = [personal_info]

    def append_trip(self, trip):
        '''Appends new trip to tour

        Inputs:
            trip (list): Trip taken by traveller in their trip tour.
        '''
        self.tour.append(trip)

    def finalized_trip_tour(self, num_nodes):
        '''Finalizes trip tour taken by traveller.

        NA nodes are appended to the end of the trip tour so that every
        trip tour has the same length.

        Inputs:
            num_nodes (int): Number of nodes in a trip tour.

        Returns:
            trip_tour (list): Flattened version of self.trip_tour, with
                fixed length.

        '''
        empty_trip = ['NA'] * TRIP_SEGMENT_LENGTH
        for _ in range(num_nodes + 1 - len(self.tour)):
            self.tour.append(empty_trip)
        return [item for trip in self.tour for item in trip]

def write_node_headers(writer):
    """Writes headers for trips comprising trip tours."""
    writer.writerow(['Node Type'] + ['Node Predecessor'] + ['Node Successor']
                    + ['Node Name'] + ['Node County'] + ['Node Lat']
                    + ['Node Lon'] + ['Node Industry'] + ['XCoord'] + ['YCoord']
                    + ['Segment'] + ['Row'] + ['IsComplete'])

def write_headers_output(writer):
    """Writes headers for final Module 5 Output file."""
    header_types = ['Node %d Type'] + ['Node %d Predecessor'] + ['Node %d Successor'] \
                   + ['Node %d Name'] + ['Node %d County'] + ['Node %d Lat'] \
                   + ['Node %d Lon'] + ['Node %d Industry']
    node_headers = []
    for i in range(1, 8):
        node_headers += [header % i for header in header_types]
    writer.writerow(['Residence State'] + ['County Code'] + ['Tract Code']
                    + ['Block Code'] + ['HH ID'] + ['Person ID Number']
                    + ['Activity Pattern'] + node_headers)

def get_writer(base_path, fips, seen, file_type):
    """Determines file to write Module 5 output based on FIPS code.

    Inputs:
        base_path (str): Partially completed path to Module 5 Output file,
            including state name.
        fips (str): fips which current row's person resides in.
        seen (str): A list containing the FIPS codes we have seen.
        file_type (str): The type (Sort or Pass) along with Iteration (0, 1, 2)

    Returns:
        seen (list): List of all seen fips codes.
        writer (csv.writer): Opened file to write Module 5 output to.
    """
    #TODO - This process might be dangerous -  should refactor
    #opening of files to ensure we can use with...open() functionality
    output_file = base_path + fips + '_' + file_type + '_' + TEMP_FNAME
    if fips in seen:
        # Read with a+ as there is no chance of mixing data and we want to append
        # to what is currently there
        writer = writing.csv_writer(open(output_file, 'a+'))
    else:
        writer = writing.csv_writer(open(output_file, 'w+'))
        write_node_headers(writer)
        seen.append(fips)
    return seen, writer

def construct_initial_trip_files(file_path, base_path, start_time):
    """Converts all Module 4 Activity Patterns into the nodes they represent.

    Writes every row (with activity patterns) as a  node with geographic
    attributes from a specified trip based on the activity pattern.

    Ex. Activity Pattern 6
    Generates: Row H, Row W, Row O, Row H

    Every node is marked as complete or not complete based on
    whether sufficient information exists to describe the node's trip sequence.
    For all nodes departing from an other or ending in an other trip, this
    information does not exist, so 0 is marked. Otherwise, 1 is marked.

    Inputs:
        input_path (str): Completed file path to Module 4 input file.
        base_path (str): Partially completed path to Module 5 output file,
            including state name.
        start_time (datetime): Module 5 start time.

    Returns:
        seen (list): A list containing FIPS codes seen in the process of
            constructing the trips.
    """
    trailing_fips = ''
    seen = []
    count = 1
    valid_prev = ('S', 'H', 'W')
    valid_end = ('S', 'H', 'W', 'N')
    with open(file_path) as read:
        reader = reading.csv_reader(read)
        next(reader)
        for person in reader:
            person[0], person[1] = person[0].rjust(2, '0'), person[1].rjust(3, '0')
            curr_fips = core.correct_FIPS(person[0] + person[1])
            person[0], person[1] = curr_fips[0:2], curr_fips[2:5]
            if curr_fips != trailing_fips:
                trailing_fips = curr_fips
                seen, writer = get_writer(base_path, trailing_fips, seen, 'Pass0')
            # Get personal tours constructed for sorting
            tour = activity.Pattern(int(person[len(person) - 1]), person, count)
            for node in tour.activities:
                if 'NA' not in node[0]:
                    node[5].rjust(5, '0')
                    # Does not involve trip with origin or destination that
                    # hasn't already been computed
                    if node[0] in valid_prev and node[3] in valid_end:
                        is_complete = 1
                    else:
                        is_complete = 0
                    writer.writerow([node[0]] + [node[2]] + [node[3]]
                                    + [node[4]] + [node[5]] + [node[6]]
                                    + [node[7]] + [node[8]] + [node[9]]
                                    + [node[10]] + [node[11]] + [node[12]]
                                    + [is_complete])
            count += 1
            if count % 100000 == 0:
                print(str(count) + ' Residents Completed and taken this much time: '
                      + str(datetime.now()-start_time))
    return seen

def sort_files_before_pass(base_path, seen, iteration):
    """Sort Module 5 files before passing over them.

    Sorts node files by County, XCoord, YCoord, Node Successor and Node
    Type prior to passing through the file to find the other trip locations. By
    sorting by Node, then (X,Y) coords, we are able to minimize the number of
    times we need to read in new data and maximize reuse for the patronageWarehouse
    objects.

    Inputs:
        base_path (str): Partially completed path to Module 5 Output file,
            including state name.
        seen (list): FIPS codes seen in the process of constructing trips.
        iteration (int): Which iteration of passing we are on (1 or 2)
    """
    # If we're on iteration 1, we need to access the initial trip files, which
    # are named as 0. Otherwise, the name is based on the iteration number.
    if iteration == '1':
        past = str(int(iteration)-1)
    else:
        past = iteration
    pandas_dtype = {'Node Type': str, 'Node Predecessor': str, 'Node Successor': str,
                    'Node Name': str, 'Node County': str, 'Node Lat': str,
                    'Node Lon': str, 'Node Industry': str, 'XCoord': int,
                    'YCoord': int, 'Segment': int, 'Row': int}
    for fips in seen:
        print("Sorting Before Pass: ", fips, " on iteration: ", iteration)
        reader = pd.read_csv(base_path + fips + '_' + 'Pass'
                             + past + '_' + TEMP_FNAME, dtype=pandas_dtype)
        reader = reader.sort_values(by=['Node County', 'XCoord', 'YCoord',
                                        'Node Successor', 'Node Type'],
                                    ascending=[True, True, True, True, True])
        reader.to_csv(base_path + fips + '_' + 'Sort' + iteration + '_' + TEMP_FNAME,
                      index=False, na_rep='NA')

def pass_over_files(base_path, seen, iteration):
    """Determines destinations for which the origin is known for every trip in Module 5.

    This function sorts node files by County, XCoord, YCoord, Node Successor and Node
    Type prior to passing through the file to find the other trip locations. By
    sorting by Node, then (X,Y) coords, we are able to minimize the number of
    times we need to read in new data and maximize reuse for the patronageWarehouse
    objects.

    Inputs:
        base_path (str): Partially completed path to Module 5 Output file,
            including state name.
        seen (list): Fips codes seen in the process of constructing trips.
        iteration (int): Which iteration of passing we are on (1 or 2).
    """
    for fips in seen:
        print("Passing over: ", fips, " on iteration: ", iteration, "at ", datetime.now())
        input_file = base_path + fips + '_' + 'Sort' + iteration + '_' + TEMP_FNAME
        output_file = base_path + fips + '_' + 'Pass' + iteration + '_' + TEMP_FNAME
        findOtherTrips.get_other_trip(input_file, output_file, fips[:2], iteration)

def remove_prev_files(base_path, seen, iteration):
    """Removes files from previous iterations that aren't needed anymore.

    Inputs:
        base_path (str): Partially completed path to Module 5 Output file,
            including state name.
        seen (list): A list containing fips codes seen in the process of constructing
            the trips.
        iteration (int): Which iteration of passing we are on (1 or 2).
    """
    past = str(int(iteration)-1)
    for fips in seen:
        if iteration == '4':
            try:
                os.remove(base_path + fips + '_' + 'Pass' + past + '_' + TEMP_FNAME)
            except FileNotFoundError:
                print('Pass type file for FIPS: ', fips, ' does not exist')
        else:
            try:
                os.remove(base_path + fips + '_' + 'Sort' + iteration + '_' + TEMP_FNAME)
            except FileNotFoundError:
                print('Sort type file for FIPS: ', fips, ' does not exist')
            try:
                os.remove(base_path + fips + '_' + 'Pass' + past + '_' + TEMP_FNAME)
            except FileNotFoundError:
                print('Pass type file for FIPS: ', fips, ' does not exist')

def sort_files_after_pass(base_path, seen, iteration):
    """Sort files by row and segment after passing through files.

    Allows for quick reconstruction of trip files for the next iteration
    in rebuild_trips().

    Inputs:
        base_path (str): Partially completed path to Module 5 Output file,
            including state name.
        seen (list): A list containing fips codes seen in the process of constructing
            the trips.
        iteration (int): Which iteration of passing we are on (1 or 2)
    """
    future = str(int(iteration)+1)
    pandas_dtype = {'Node Type': str, 'Node Predecessor': str, 'Node Successor': str,
                    'Node Name': str, 'Node County': str, 'Node Lat': str,
                    'Node Lon': str, 'Node Industry': str, 'XCoord': int,
                    'YCoord': int, 'Segment': int, 'Row': int, 'IsComplete': str,
                    'D Node Name': str, 'D Node County': str, 'D Node Lat': str,
                    'D Node Lon': str, 'D Node Industry': str, 'D XCoord': str,
                    'D YCoord': str}
    for fips in seen:
        print("Sorting After Pass: ", fips, " on iteration: ", iteration)
        reader = pd.read_csv(base_path + fips + '_' + 'Pass' + iteration
                             + '_' + TEMP_FNAME, dtype=pandas_dtype)
        reader = reader.sort_values(by=['Row', 'Segment'], ascending=[True, True])
        reader.to_csv(base_path + fips + '_' + 'Sort' + future
                      + '_' + TEMP_FNAME, index=False, na_rep='NA')
    remove_prev_files(base_path, seen, iteration)

def rebuild_trips(base_path, seen, iteration):
    """Rebuilds trip files for after sorting and passing through files.

    This function rebuilds the trip files by taking nodes sorted by Row and Segment
    to fill in Other type destination nodes. get_other_trips() writes out
    the destination node information, if found, in the 7 columns following
    the initial is_complete column from the initial trip file. This
    destination node information is then written as the origin for the next
    trip taken by the traveller.

    Inputs:
        base_path (str): Partially completed path to Module 5 Output file,
            including state name.
        seen (list): Contains FIPS codes seen in the process of constructing
            the trips.
        iteration (int): Which iteration of passing we are on (1 or 2).
    """
    for fips in seen:
        input_file = base_path + fips + '_' + 'Sort' + iteration + '_' + TEMP_FNAME
        output_file = base_path + fips + '_' + 'Pass' + iteration + '_' + TEMP_FNAME
        with open(input_file, 'r+') as read, open(output_file, 'w+') as write:
            reader = reading.csv_reader(read)
            writer = writing.csv_writer(write)
            next(reader)
            write_node_headers(writer)
            trailing = ''
            for row in reader:
                # If it's incomplete, is an other-type node and isn't preceded
                # by an other type trip
                if row[12] == '0' and row[0] == 'O' and row[1] != 'O':
                    row[3:10] = trailing
                    if row[2] != 'O':
                        row[12] = '1'
                trailing = row[13:]
                writer.writerow(row[:13])

def construct_personal_info_dict(fips, state):
    """Constructs dictionary of traveller (row) with personal attributes.

    Used to fill in personal information for Module 5 output files in
    traveller trip tours. Contains personal information for travellers
    who reside in a particular FIPS code and a particular state.

    Inputs:
        fips (str): Traveller FIPS code residence.
        state (str): Traveller state residence.

    Returns:
        person_dict (dict): Associates a row number (count) with traveller's
            personal attributes.
    """
    input_file = paths.OUTPUT + 'Module4/' + state + 'Module4NN2ndRun.csv'
    with open(input_file) as read:
        reader = reading.csv_reader(read)
        next(reader)
        person_dict = dict()
        for count, row in enumerate(reader):
            row[0], row[1] = row[0].rjust(2, '0'), row[1].rjust(3, '0')
            fips_code = core.correct_FIPS(row[0] + row[1])
            if fips == fips_code:
                person_dict[count] = row[:5] + [row[8]] + [row[11]]
    return person_dict

def build_trip_tours(base_path, state, seen):
    """Builds finalized trip tours for each traveller.

    Trip tours are built as rows for each traveller and detail the daily
    travel taken by the traveller throughout the day. Also includes personal
    attributes of that traveller.

    Inputs:
        base_path (str): Partially completed path to Module 5 Output file,
            including state name.
        state (str): Traveller state residence.
        seen (list): Contains FIPS codes seen in the process of constructing
            the trips.
    """
    for fips in seen:
        input_file = base_path + fips + '_' + 'Pass3' + '_' + TEMP_FNAME
        print('Building trip tours for file: ', input_file)
        output_file = base_path + fips + '_' + 'Module5NN1stRun.csv'
        with open(input_file, 'r+') as read, open(output_file, 'w+') as write:
            writer = writing.csv_writer(write)
            reader = reading.csv_reader(read)
            next(reader)
            write_headers_output(writer)
            personal_info = construct_personal_info_dict(fips, state)
            num_nodes = 7
            for row in reader:
                trip_tour = TripTour(row[ROW_SEGMENT_IND], personal_info[row])
                if row[ROW_SEGMENT_IND] != trip_tour.row:
                    finalized_trip_tour = trip_tour.finalized_trip_tour(num_nodes)
                    writer.writerow(finalized_trip_tour)
                else:
                    trip_tour.append_trip(row[:TRIP_SEGMENT_LENGTH])

def main(state):
    """Builds all trip tours for a U.S. State using Module 4 Output.

    Inputs:
        state (str): Module 4 Output state to process.
    """
    input_path = paths.OUTPUT + 'Module4/' + state + 'Module4NN2ndRun.csv'
    output_path = paths.OUTPUT + 'Module5/'
    base_path = output_path + state + '_'
    start_time = datetime.now()
    print(state + " started at: " + str(start_time))
    seen = construct_initial_trip_files(input_path, base_path, start_time)

    for i in range(1, 3):
        current = str(i)
        future = str(i+1)
        print('Began sorting before passing on iteration: ',
              current, ' at', str(datetime.now()-start_time))
        sort_files_before_pass(base_path, seen, current)
        print('Finished sorting before passing on iteration: ',
              current, ' at', str(datetime.now()-start_time))
        pass_over_files(base_path, seen, current)
        print('Finished passing over files on iteration: ', current,
              ' at', str(datetime.now()-start_time))
        sort_files_after_pass(base_path, seen, current)
        print('Finished sorting files after passing on iteration: ',
              current, ' at', str(datetime.now()-start_time))
        rebuild_trips(base_path, seen, future)

    remove_prev_files(base_path, seen, '3')
    build_trip_tours(base_path, state, seen)
    remove_prev_files(base_path, seen, '4')

    print(state + " took: " + str(datetime.now() - start_time))
