from . import activity, findOtherTrips
from ..utils import reading, writing, paths, core
from datetime import datetime
import pandas as pd
import os

temp_name = 'Module5Temp.csv'

def write_rebuilt_headers(pW):
    pW.writerow(['Node Type'] + ['Node Predecessor'] + ['Node Successor']
                + ['Node Name'] + ['Node County'] + ['Node Lat'] + ['Node Lon']
                + ['Node Industry'] + ['XCoord'] + ['YCoord'] + ['Segment']
                + ['Row'] + ['IsComplete'] + ['D Node Name'] + ['D Node County']
                + ['D Node Lat'] + ['D Node Lon'] + ['D Node Industry']
                + ['D XCoord'] + ['D YCoord'])

def write_node_headers(pW):
    pW.writerow(['Node Type'] + ['Node Predecessor'] + ['Node Successor']
                + ['Node Name'] + ['Node County'] + ['Node Lat']
                + ['Node Lon'] + ['Node Industry'] + ['XCoord'] + ['YCoord']
                + ['Segment'] + ['Row'] + ['IsComplete'])

def write_headers_output(writer):
    header_types = ['Node %d Type'] + ['Node %d Predecessor'] + ['Node %d Successor'] \
                   + ['Node %d Name'] + ['Node %d County'] + ['Node %d Lat'] \
                   + ['Node %d Lon'] + ['Node %d Industry']
    node_headers = []
    for i in range(1, 8):
        node_headers += [header % i for header in header_types]
    writer.writerow(['Residence State'] + ['County Code'] + ['Tract Code']
                    + ['Block Code'] + ['HH ID'] + ['Person ID Number']
                    + ['Activity Pattern'] + node_headers)

def get_writer(base_path, fips, seen):
    """Determines file to write Module 5 output based on fips code.

    Args:
    output_path (str): Path to Module 5 output directory.
    state (str): State which current row's person resides in.
    fips (str): fips which current row's person resides in.
    seen (str): A list containing the fips codes we have seen.

    Returns:
    seen (list): List of all seen fips codes.
    person_writer (csv.writer): Opened file to write Module 5 output to.
    """
    #TODO - This process might be dangerous -  should refactor
    #opening of files to ensure we can use with...open() functionality
    # If we have seen this code before, it's an old file
    output_file = base_path + fips + '_' + 'Pass0' + '_' + temp_name
    if fips in seen:
        # Read with a+ as there is no chance of mixing data and we want to append
        # to what is currently there
        writer = writing.csv_writer(open(output_file, 'a+'))
    else:
        # Read with w+ to ensure old data doesn't mix with new data
        writer = writing.csv_writer(open(output_file, 'w+'))
        # Give the file a header
        write_node_headers(writer)
        # Add it to list  of seen so we don't write headers again
        seen.append(fips)
    return seen, writer

def construct_initial_trip_files(file_path, base_path, start_time):
    """ Converts all Module 4 Activity Patterns into the nodes they represent.

    Writes every row (with activity patterns) as a  node with geographic
    attributes from a specified trip based on the activity pattern.

    Ex. Activity Pattern 6
    Returns: Row H, Row W, Row O, Row H

    Every node is marked as complete or not complete based on
    whether sufficient information exists to describe the node's trip sequence.
    For all nodes departing from an other or ending in an other trip, this
    information does not exist, so 0 is marked. Otherwise, 1 is marked.

    Args:
    fileLocaton (str): Path to Module 4 input directory.
    output_path (str): Path to Module 5 output directory.
    state (str): State which current row's person resides in.
    start_time (datetime): Module 5 start time.

    Returns:
    seen (list): A list containing fips codes seen in the process of
        constructing the trips.
    """
    trailing_fips = ''
    seen = []
    count = 1
    valid_prev = ('S','H','W')
    valid_end = ('S','H','W','N')
    with open(file_path) as read:
        reader = reading.csv_reader(read)
        next(reader)
        for person in reader:
            # Left pad w/ 0s as valid State/County code
            person[0], person[1] = person[0].rjust(2, '0'), person[1].rjust(3, '0')
            curr_fips = core.correct_FIPS(person[0] + person[1])
            # Change output file if fips changes
            if curr_fips != trailing_fips:
                trailing_fips = curr_fips
                seen, writer = get_writer(base_path, trailing_fips, seen)
            # Get personal tours constructed for sorting
            tour = activity.Pattern(int(person[len(person) - 1]),
                                    person, count)
            for node in tour.activities:
                # Write any node that is not an NA node
                if 'NA' not in node[0]:
                    is_complete = 0
                    if len(node[5]) == 4:
                        node[5] = '0' + node[5]
                    # No other trips needed, so we have everything we need to write this trip down
                    if node[0] in valid_prev and node[3] in valid_end:
                        is_complete = 1
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

    Args:
    output_path: Path to files holding node information
    state: State which current row's person resides in
    seen: A list containing fips codes seen in the process of constructing
    the trips.
    iteration: Which iteration of passing we are on (1 or 2)
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
        print("Sorting Before Pass: ", fips, " on Iteration: ", iteration)
        reader = pd.read_csv(base_path + fips + '_' + 'Pass'
                             + past + '_' + temp_name, dtype = pandas_dtype)
        reader = reader.sort_values(by=['Node County', 'XCoord','YCoord',
                                        'Node Successor', 'Node Type'],
                                    ascending=[True, True, True, True, True])
        reader.to_csv(base_path + fips + '_' + 'Sort' + iteration + '_' + temp_name,
                      index=False, na_rep = 'NA')

def pass_over_files(base_path, seen, iteration, county_name_data):
    """
    Summary:
    This function sorts node files by County, XCoord, YCoord, Node Successor and Node
    Type prior to passing through the file to find the other trip locations. By
    sorting by Node, then (X,Y) coords, we are able to minimize the number of
    times we need to read in new data and maximize reuse for the patronageWarehouse
    objects.

    Args:
    output_path: Path to files holding node information
    state: State which current row's person resides in
    seen: A list containing fips codes seen in the process of constructing
    the trips.
    iteration: Which iteration of passing we are on (1 or 2)

    Returns:
    A sorted file as described above.
    """
    for fips in seen:
        print("Passing over: ", fips, " on Iteration: ", iteration, "at ", datetime.now())
        input_file = base_path + fips + '_' + 'Sort' + iteration + '_' + temp_name
        output_file = base_path + fips + '_' + 'Pass' + iteration + '_' + temp_name
        with open(input_file, 'r+') as read, open(output_file, 'w+') as write:
            reader = reading.csv_reader(read)
            writer = writing.csv_writer(write)
            write_rebuilt_headers(writer)
            findOtherTrips.get_other_trip(reader, writer, county_name_data, fips[:2], iteration)

def clean_files(base_path, seen, iteration):
    """
    Summary:
    This cleans out files from previous iterations that are no longer needed.

    Args:
    output_path: Path to files holding node information
    state: State which current row's person resides in
    seen: A list containing fips codes seen in the process of constructing
    the trips.
    iteration: Which iteration of passing we are on (1 or 2)

    Returns:
    Removes files as shown below.
    """
    past = str(int(iteration)-1)
    for fips in seen:
        if iteration == '4':
            try:
                os.remove(base_path + fips + '_' + 'Pass' + past + '_' + temp_name)
            except:
                print('Unable to remove PASS type folder for fips: ', fips)
        else:
            try:
                os.remove(base_path + fips + '_' + 'Sort' + iteration + '_' + temp_name)
            except:
                print('Unable to remove SORT type folder for fips: ', fips)
            try:
                os.remove(base_path + fips + '_' + 'Pass' + past + '_' + temp_name)
            except:
                print('Unable to remove PASS type folder for fips: ', fips)

def sort_files_after_pass(base_path, seen, iteration):
    """
    Summary:
    This function sorts node files by Row and Segment after passing through the
    file to find the other type node locations. This allows us to quickly reconstruct
    trip files for the next iteration/final output in rebuild_trips().

    Args:
    output_path: Path to files holding node information
    state: State which current row's person resides in
    seen: A list containing fips codes seen in the process of constructing
    the trips.
    iteration: Which iteration of passing we are on (1 or 2)

    Returns:
    A sorted file as described above.
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
        print("Sorting After Pass: ", fips, " on Iteration: ", iteration)
        reader = pd.read_csv(base_path + fips + '_' + 'Pass' + iteration
                             + '_' + temp_name, dtype = pandas_dtype)
        reader = reader.sort_values(by=['Row', 'Segment'], ascending=[True, True])
        reader.to_csv(base_path + fips + '_' + 'Sort' + future
                      + '_' + temp_name, index=False, na_rep = 'NA')
    clean_files(base_path, seen, iteration)

def rebuild_trips(base_path, seen, iteration):
    """Rebuilds trip files for after sorting and passing through files.

    This function rebuilds the trip files by taking nodes sorted by Row and Segment
    to fill in O destination nodes. get_other_trips() writes out the destination
    node information, if found, in the 7 columns following the initial is_complete
    boolean column from the initial trip file. The data following this column is
    taken and filled in for subsequent nodes that were previously marked as NA
    due to issues with a lack of O destination node or uncertainty on the O
    origin node.

    Args:
    output_path: Path to files holding node information
    state: State which current row's person resides in
    seen: A list containing fips codes seen in the process of constructing
    the trips.
    iteration: Which iteration of passing we are on (1 or 2)

    Returns:
    A file with newly gained information on the other type node destinations
    now filled in.
    """
    for fips in seen:
        input_file = base_path + fips + '_' + 'Sort' + iteration + '_' + temp_name
        output_file = base_path + fips + '_' + 'Pass' + iteration + '_' + temp_name
        with open(input_file, 'r+') as read, open(output_file, 'w+') as write:
            reader = reading.csv_reader(read)
            writer = writing.csv_writer(write)
            next(reader)
            write_node_headers(writer)
            trailing = ''
            for line in reader:
                # If it's incomplete, is an other-type node and isn't preceded
                # by an other type trip
                if line[12] == '0' and line[0] == 'O' and line[1] != 'O':
                    line[3:10] = trailing
                    if line[2] != 'O':
                        line[12] = '1'
                trailing = line[13:]
                writer.writerow(line[:13])

def construct_row_personal_info_dict(fips, state):
    input_file = paths.OUTPUT + 'Module4/' + state + 'Module4NN2ndRun.csv'
    with open(input_file) as read:
        reader = reading.csv_reader(read)
        next(reader)
        person_dict = dict()
        count = -1
        for line in reader:
            line[0], line[1] = line[0].rjust(2, '0'), line[1].rjust(3, '0')
            fips_code = line[0] + line[1]
            if fips == fips_code:
                person_dict[count] = line[:5] + [line[8]] + [line[11]]
            count += 1
    return person_dict

def rebuild_module_5_file(base_path, state, seen):
    for fips in seen:
        input_file = base_path + fips + '_' + 'Pass3' + '_' + temp_name
        print(input_file)
        output_file = base_path + fips + '_' + 'Module5NN1stRun.csv'
        with open(input_file, 'r+') as read, open(output_file, 'w+') as write:
            writer = writing.csv_writer(write)
            reader = reading.csv_reader(read)
            next(reader)
            write_headers_output(writer)
            row_dict = construct_row_personal_info_dict(fips, state)
            count = 0
            trailing = []
            curr_row = ''
            num_nodes = 7
            # TODO - Make this more obvious and readable...
            for line in reader:
                count += 1
                if line[11] != curr_row:
                    for _ in range(num_nodes+1 - len(trailing)):
                        trailing.append(['NA'] * 8)
                    final_row = [item for sublist in trailing for item in sublist]
                    if count != 1:
                        writer.writerow(final_row)
                    curr_row = line[11]
                    trailing = [row_dict[int(curr_row)]]
                trailing.append(line[:8])

def main(state):
    file_path = paths.OUTPUT + 'Module4/' + state + 'Module4NN2ndRun.csv'
    output_path = paths.OUTPUT + 'Module5/'
    base_path = output_path + state + '_'
    start_time = datetime.now()
    print(state + " started at: " + str(start_time))
    seen = construct_initial_trip_files(file_path, base_path, start_time)
    county_name_data = core.read_counties()

#    for i in range(1,3):
#        current = str(i)
#        future = str(i+1)
#        print('Began sorting before passing on iteration: ',
#              str(i), ' at', str(datetime.now()-start_time))
#        sort_files_before_pass(base_path, seen, current)
#        print('Finished sorting before passing on iteration: ',
#              str(i), ' at', str(datetime.now()-start_time))
#        pass_over_files(base_path, seen, current, county_name_data)
#        print('Finished passing over files on iteration: ', str(i),
#              ' at', str(datetime.now()-start_time))
#        sort_files_after_pass(base_path, seen, current)
#        print('Finished sorting files after passing on iteration: ',
#              str(i), ' at', str(datetime.now()-start_time))
#        rebuild_trips(base_path, seen, future)
#        print('Finished iteration: ', str(i))

    #clean_files(base_path, seen, '3')
    
    rebuild_module_5_file(base_path, state, seen)
    #clean_files(base_path, seen, '4')

    print(state + " took: " + str(datetime.now() - start_time))