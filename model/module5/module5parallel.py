# -*- coding: utf-8 -*-
"""
Created on Tue May  9 15:37:22 2017

@author: Kyle
"""

#!/usr/bin/env python
from ..utils import paths, reading, writing, core
from . import module5, findOtherTrips, activity
from datetime import datetime
import os
import os.path
import multiprocessing
import pandas as pd
import statistics


tempSuffix = 'Module5Temp.csv'

def construct_initial_trip_files(file_path, base_path, start_time):
    """
    Summary:
    This function takes in the Module4NN Trip files and writes every row as a
    node with geographic attributes from a specified trip based on the
    activity pattern.

    Ex. Activity Pattern 6
    Output: Row H, Row W, Row O, Row H

    Every node is marked as complete or not complete based on
    whether sufficient information exists to describe the node's trip sequence.
    For all nodes departing from an other or ending in an other trip, this
    information does not exist, so 0 is marked. Otherwise, 1 is marked.

    Input Arguments:
    fileLocaton: Path to Module 4 input directory
    outputLocation: Path to Module 5 output directory
    state: State which current row's person resides in
    start_time: Start time of Module 5, used for timing.

    Output:
    seen: A list containing FIPS codes seen in the process of constructing
    the trips.
    Additionally, a file detailing all the nodes written as described above.
    """
    trailing_fips = ''
    fips_seen = []
    count = 1
    valid_prev = ('S','H','W')
    valid_end = ('S','H','W','N')
    fips_hold = dict()
    fips_trip_count = 0
    with open(file_path) as read:
        reader = reading.csv_reader(read)
        next(reader)
        for person in reader:
            # Left pad w/ 0s as valid State/County code
            person[0], person[1] = person[0].rjust(2, '0'), person[1].rjust(3, '0')
            curr_fips = core.correct_FIPS(person[0] + person[1])
            person[0], person[1] = curr_fips[0:2], curr_fips[2:5]
            # Change output file if fips changes
            if curr_fips != trailing_fips:
                if trailing_fips in fips_hold:
                    fips_hold[trailing_fips] += fips_trip_count
                    fips_trip_count = 0
                    fips_hold[curr_fips] = fips_trip_count
                else:
                    if trailing_fips == '':
                        fips_trip_count = 0
                        fips_hold[curr_fips] = fips_trip_count
                    else:
                        fips_hold[trailing_fips] += fips_trip_count
                        fips_trip_count = 0
                        fips_hold[curr_fips] = fips_trip_count
                trailing_fips = curr_fips
                fips_seen, writer = module5.get_writer(base_path, trailing_fips, fips_seen, 'Pass0', tempSuffix)

            # Get personal tours constructed for sorting
            tour = activity.Pattern(int(person[len(person) - 1]),
                                    person, count)
            for node in tour.activities:
                # Write any node that is not an NA node
                if 'NA' not in node[0]:
                    is_complete = 0
                    node[5].rjust(5, '0')
                    # No other trips needed, so we have everything we need to write this trip down
                    if node[0] in valid_prev and node[3] in valid_end:
                        is_complete = 1
                    fips_trip_count += 1
                    writer.writerow([node[0]] + [node[2]] + [node[3]]
                                    + [node[4]] + [node[5]] + [node[6]]
                                    + [node[7]] + [node[8]] + [node[9]]
                                    + [node[10]] + [node[11]] + [node[12]]
                                    + [is_complete])
            count += 1
            if count % 100000 == 0:
                print(str(count) + ' Residents Completed and taken this much time: '
                      + str(datetime.now()-start_time))
    median_row = statistics.median(sorted([count for count in fips_hold.values()]))
    if median_row == 0:
        median_row = 500000
    if median_row < 50000:
        median_row = 50000
    return fips_seen, median_row

def construct_initial_files_splitter(output_path, state, seen, median_row):
    all_files = []
    for fips in seen:
        file_name = output_path + state + '_'  + fips + '_' + 'Pass0' + '_' + tempSuffix
        FIPSFiles = split_csv(file_name, output_name_template = state + '_' + fips
                              + '_' + 'Module5Temp' + '_' + 'Pass0', fips = fips,
                              row_limit = median_row, output_path = output_path)
        all_files.append(FIPSFiles)
        try:
            os.remove(output_path + state + '_'  + fips + '_' + 'Pass0' + '_' + tempSuffix)
        except:
            print('Unable to remove initial file @', fips)
    return [item for sublist in all_files for item in sublist]

def split_csv(file_name, output_name_template, fips, row_limit=10000, output_path='.'):
    """
    Splits a CSV file into multiple pieces.

    Arguments:
        `filehandler`: an open() object called on the file.
        `delimiter`: Delimiter used to separate entries. Comma used by default (.csv).
        `row_limit`: The number of rows you want in each output file. 10,000 by default.
        `output_name_template`: A %s-style template for the numbered output files by default.
        `output_path`: Where to write the output files.
    Example usage:

        >> from toolbox import csv_splitter;
        >> csv_splitter.split(open('/home/ben/input.csv', 'r'));

    """
    # Construct reader from filehandler
    seen_files = []
    current_piece = 1
    current_out_path = os.path.join(output_path, output_name_template + '_' + str(current_piece) + '.csv')
    with open(file_name, 'r+') as read:
        o = open(current_out_path, 'w+')
        reader = reading.csv_reader(read)
        writer = writing.csv_writer(o)
        seen_files.append([fips, str(current_piece)])
        current_limit = row_limit
        count = -1
        line_vec = []
        for r in reader:
            if count == -1:
                writer.writerow(r)
                count += 1
                continue
            if count - 1 > current_limit:
                if len(line_vec) == 0:
                    line_vec.append((r[8],r[9]))
                else:
                    valToConfirm = line_vec.pop()
                    if valToConfirm == (r[8],r[9]):
                        line_vec.append((r[8],r[9]))
                        writer.writerow(r)
                        continue
                    else:
                        current_piece += 1
                        current_limit = row_limit * current_piece
                        current_out_path = os.path.join(output_path, output_name_template + '_' + str(current_piece) + '.csv')
                        o.close()
                        o = open(current_out_path, 'w+', encoding='utf8')
                        seen_files.append([fips, str(current_piece)])
                        writer = writing.csv_writer(o)
                        module5.write_node_headers(writer)
            writer.writerow(r)
            count += 1
    o.close()
    return seen_files

def sort_files_before_splitter(base_path, seen):
    """
    Summary:
    This function sorts node files by County, XCoord, YCoord, Node Successor and Node
    Type prior to passing through the file to find the other trip locations. By
    sorting by County, then (X,Y) coords, we are able to minimize the number of
    times we need to read in new data and maximize reuse for the patronageWarehouse
    objects. This sorting is done before splitting the files, so it operates on
    county-wide files, not split county files.

    Input Arguments:
    outputLocation: Path to files holding node information
    state: State which current row's person resides in
    seen: A list containing FIPS codes seen in the process of constructing
    the trips.

    Output:
    A sorted file as described above.
    """
    # If we're on iteration 1, we need to access the initial trip files, which
    # are named as 0. Otherwise, the name is based on the iteration number.
    iteration = '0'
    past = iteration
    pandas_dtype = {'Node Type': str, 'Node Predecessor': str, 'Node Successor': str,
                    'Node Name': str, 'Node County': str, 'Node Lat': str,
                    'Node Lon': str, 'Node Industry': str, 'XCoord': int,
                    'YCoord': int, 'Segment': int, 'Row': int}
    for fips in seen:
        print("Sorting Before Splitter: ", fips, " on Iteration: ", iteration)
        reader = pd.read_csv(base_path + fips + '_' + 'Pass' + past + '_' + tempSuffix,
                             dtype = pandas_dtype)
        reader = reader.sort_values(by=['Node County', 'XCoord', 'YCoord',
                                        'Node Successor', 'Node Type'],
                                        ascending=[True, True, True, True, True])
        reader.to_csv(base_path + fips + '_' + 'Pass' + iteration + '_' + tempSuffix,
                      index=False, na_rep = 'NA')

def sort_files_before_pass(base_path, seen, iteration):
    """
    Summary:
    This function sorts node files by County, XCoord, YCoord, Node Successor and Node
    Type prior to passing through the file to find the other trip locations. By
    sorting by County, then (X,Y) coords, we are able to minimize the number of
    times we need to read in new data and maximize reuse for the patronageWarehouse
    objects.

    Input Arguments:
    outputLocation: Path to files holding node information
    state: State which current row's person resides in
    seen: A list containing FIPS codes seen in the process of constructing
    the trips.
    iteration: Which iteration of passing we are on (1 or 2)

    Output:
    A sorted file as described above.
    """
    # If we're on iteration 1, we need to access the initial trip files, which
    # are named as 0. Otherwise, the name is based on the iteration number.
    pandas_dtype = {'Node Type': str, 'Node Predecessor': str, 'Node Successor': str,
                    'Node Name': str, 'Node County': str, 'Node Lat': str,
                    'Node Lon': str, 'Node Industry': str, 'XCoord': int,
                    'YCoord': int, 'Segment': int, 'Row': int}
    for file in seen:
        prev_iter = str(iteration-1)
        curr_iter = str(iteration)
        file_input = file[0] + '_' + 'Module5Temp' + '_' + 'Pass' + prev_iter + '_' + file[1] + '.csv'
        file_output = file[0] + '_' + 'Module5Temp' + '_' + 'Sort' + curr_iter + '_' + file[1] + '.csv'
        print("Sorting Before Pass: ", file[0] + '_' + file[1], " on Iteration: ", iteration)
        reader = pd.read_csv(base_path + file_input, dtype = pandas_dtype)
        reader = reader.sort_values(by=['Node County','XCoord','YCoord','Node Successor','Node Type'],
                                    ascending=[True,True,True,True,True])
        reader.to_csv(base_path + file_output, index=False, na_rep = 'NA')

def pass_over_files(base_path, seen, iteration, countyNameData, numProcessors):
    pool = multiprocessing.Pool(numProcessors)
    # Build task list
    tasks = []
    processing_num = 0
    for file in seen:
        processing_num += 1
        curr_iter = str(iteration)
        fips_code = file[0]
        state_code = fips_code[:2]
        input_path = base_path + file[0] + '_' + 'Module5Temp' + '_' + 'Sort' + curr_iter + '_' + file[1] + '.csv'
        output_path = base_path + file[0] + '_' + 'Module5Temp' + '_' + 'Pass' + curr_iter + '_' + file[1] + '.csv'
        tasks.append((input_path, output_path, countyNameData, state_code, curr_iter, processing_num, fips_code))

    results = [pool.apply_async(findOtherTrips.get_other_trip, t) for t in tasks]

    for result in results:
        num, curr_fips = result.get()
        print(num ," at ", curr_fips, " finished at ", datetime.now())

    pool.close()
    pool.join()

def clean_files(base_path, seen, iteration):
    """
    Summary:
    This cleans out files from previous iterations that are no longer needed.

    Input Arguments:
    outputLocation: Path to files holding node information
    state: State which current row's person resides in
    seen: A list containing FIPS codes seen in the process of constructing
    the trips.
    iteration: Which iteration of passing we are on (1 or 2)

    Output:
    Removes files as shown below.
    """
    past_iter = str(iteration - 1)
    curr_iter = str(iteration)
    for file in seen:
        if iteration == 3:
            input_file_pass = file[0] + '_' + 'Module5Temp' + '_' + 'Pass' + past_iter + '_' + file[1] + '.csv'
            try:
                os.remove(base_path + input_file_pass)
            except:
                print('Unable to remove file', input_file_pass)
        elif iteration == 4:
            try:
                os.remove(base_path + file[1])
            except:
                print('Unable to remove file', file)
        else:
            input_file_pass = file[0] + '_' + 'Module5Temp' + '_' + 'Pass' + past_iter + '_' + file[1] + '.csv'
            input_file_sort = file[0] + '_' + 'Module5Temp' + '_' + 'Sort' + curr_iter + '_' + file[1] + '.csv'
            try:
                os.remove(base_path + input_file_sort)
            except:
                print('Unable to remove file', input_file_sort)
            try:
                os.remove(base_path + input_file_pass)
            except:
                print('Unable to remove file', input_file_pass)

def sort_files_after_pass(base_path, seen, iteration):
    """
    Summary:
    This function sorts node files by Row and Segment after passing through the
    file to find the other type node locations. This allows us to quickly reconstruct
    trip files for the next iteration/final output in rebuild_trips().

    Input Arguments:
    outputLocation: Path to files holding node information
    state: State which current row's person resides in
    seen: A list containing FIPS codes seen in the process of constructing
    the trips.
    iteration: Which iteration of passing we are on (1 or 2)

    Output:
    A sorted file as described above.
    """
    pandas_dtype = {'Node Type': str, 'Node Predecessor': str, 'Node Successor': str,
                    'Node Name': str, 'Node County': str, 'Node Lat': str,
                    'Node Lon': str, 'Node Industry': str, 'XCoord': int,
                    'YCoord': int, 'Segment': int, 'Row': int, 'IsComplete': str,
                    'D Node Name': str, 'D Node County': str, 'D Node Lat': str,
                    'D Node Lon': str, 'D Node Industry': str, 'D XCoord': str,
                    'D YCoord': str}
    for file in seen:
        print("Sorting After Pass: ", file, " on Iteration: ", iteration)
        curr_iter = str(iteration)
        file_input = file[0] + '_' + 'Module5Temp' + '_' + 'Pass' + curr_iter + '_' + file[1] + '.csv'
        file_output = file[0] + '_' + 'Module5Temp' + '_' + 'Sort' + curr_iter + '_' + file[1] + '.csv'
        reader = pd.read_csv(base_path + file_input, dtype = pandas_dtype)
        reader = reader.sort_values(by=['Row', 'Segment'], ascending=[True, True])
        reader.to_csv(base_path + file_output, index = False, na_rep = 'NA')

def rebuild_trips(base_path, seen, iteration):
    """
    Summary:
    This function rebuilds the trip files by taking nodes sorted by Row and Segment
    to fill in O destination nodes. get_other_trips() writes out the destination
    node information, if found, in the 7 columns following the initial isComplete
    boolean column from the initial trip file. The data following this column is
    taken and filled in for subsequent nodes that were previously marked as NA
    due to issues with a lack of O destination node or uncertainty on the O
    origin node.

    Input Arguments:
    outputLocation: Path to files holding node information
    state: State which current row's person resides in
    seen: A list containing FIPS codes seen in the process of constructing
    the trips.
    iteration: Which iteration of passing we are on (1 or 2)

    Output:
    A file with newly gained information on the other type node destinations
    now filled in.
    """
    for file in seen:
        print('Rebuilding ', file, 'at iteration ', iteration)
        curr_iter = str(iteration)
        file_input = file[0] + '_' + 'Module5Temp' + '_' + 'Sort' + curr_iter + '_' + file[1] + '.csv'
        file_output = file[0] + '_' + 'Module5Temp' + '_' + 'Pass' + curr_iter + '_' + file[1] + '.csv'
        with open(base_path + file_input, 'r+') as read, open(base_path + file_output, 'w+') as write:
            reader = reading.csv_reader(read)
            writer = writing.csv_writer(write)
            module5.write_node_headers(writer)
            next(reader)
            # Use trailing to get hold geographic attributes from previous node
            trailing = ''
            for line in reader:
                # If it's incomplete, is an other-type node and isn't preceded
                # by an other type trip
                if line[12] == '0' and line[0] == 'O' and line[1] != 'O' and iteration == 1:
                    line[3:10] = trailing
                    if line[2] != 'O':
                        line[12] = '1'
                elif line[12] == '0' and line[0] == 'O' and iteration == 2:
                    line[3:10] = trailing
                    if line[2] != 'O':
                        line[12] = '1'
                trailing = line[13:]
                writer.writerow(line[:13])
    clean_files(base_path, seen, iteration)

def merge_files(base_path, seen, fips_seen, current):
    merged_files = []
    pandas_dtype = {'Node Type': str, 'Node Predecessor': str, 'Node Successor': str,
                    'Node Name': str, 'Node County': str, 'Node Lat': str,
                    'Node Lon': str, 'Node Industry': str, 'XCoord': int,
                    'YCoord': int, 'Segment': int, 'Row': int}
    curr_iter = str(current)
    for fips in fips_seen:
        print('Merging FIPS code ', fips)
        output_file = fips + '_' + 'Merged' + '_' + tempSuffix
        with open(base_path + output_file, 'w+') as write:
            writer = writing.csv_writer(write)
            module5.write_node_headers(writer)
            for file in seen:
                if file[0] != fips:
                    continue
                input_file = file[0] + '_' + 'Module5Temp' + '_' + 'Pass' + curr_iter + '_' + file[1] + '.csv'
                with open(base_path + input_file, 'r+') as read:
                    reader = reading.csv_reader(read)
                    next(reader)
                    for line in reader:
                        writer.writerow(line)
        reader = pd.read_csv(base_path + output_file, dtype = pandas_dtype)
        reader = reader.sort_values(by=['Row', 'Segment'], ascending=[True, True])
        reader.to_csv(base_path + output_file, index=False, na_rep = 'NA')
        merged_files.append([fips, output_file])
    return merged_files

def rebuild_module_5_file(base_path, state, seen):
    for file in seen:
        output_file = file[0] + '_' + 'Module5NN1stRun.csv'
        input_file = file[1]
        with open(base_path + input_file, 'r+') as read, open(base_path + output_file, 'w+') as write:
            reader = reading.csv_reader(read)
            writer = writing.csv_writer(write)
            next(reader)
            module5.write_headers_output(writer)
            row_dict = module5.construct_row_personal_info_dict(file[0], state)
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

def main(state, num_processors):
    file_path = paths.OUTPUT + 'Module4/' + state + 'Module4NN2ndRun.csv'
    output_path = paths.OUTPUT + 'Module5/'
    base_path = output_path + state + '_'
    start_time = datetime.now()
    print(state + " started at: " + str(start_time))

    fips_seen, median_row = construct_initial_trip_files(file_path, base_path, start_time)
    sort_files_before_splitter(base_path, fips_seen)
    files_seen = construct_initial_files_splitter(output_path, state, fips_seen, median_row)
    countyNameData = core.read_counties()
    for i in range(1,3):

        current = i

        print('Began sorting before passing on iteration: ', str(i), ' at', str(datetime.now()-start_time))
        sort_files_before_pass(base_path, files_seen, current)
        print('Finished sorting before passing on iteration: ', str(i), ' at', str(datetime.now()-start_time))
        pass_over_files(base_path, files_seen, current, countyNameData, num_processors)
        print('Finished passing over files on iteration: ', str(i), ' at', str(datetime.now()-start_time))
        sort_files_after_pass(base_path, files_seen, current)
        print('Finished sorting files after passing on iteration: ', str(i), ' at', str(datetime.now()-start_time))
        rebuild_trips(base_path, files_seen, current)
        print('Finished iteration: ', str(i))

    print(datetime.now() - start_time)
    merged_files = merge_files(base_path, files_seen, fips_seen, current)
    clean_files(base_path, files_seen, current + 1)
    rebuild_module_5_file(base_path, state, merged_files)
    clean_files(base_path, merged_files, 4)

    print(state + " took: " + str(datetime.now() - start_time))
