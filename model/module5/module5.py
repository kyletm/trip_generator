import statistics
import os
import multiprocessing
from datetime import datetime
import pandas as pd
from . import activity, find_other_trips
from ..utils import reading, writing, paths, core

TEMP_NAME = 'Module5Temp'
TEMP_FNAME = TEMP_NAME + '.csv'
ROW_SEGMENT_IND = 11
TRIP_SEGMENT_LENGTH = 8
VALID_PREV = ('S', 'H', 'W')
VALID_END = ('S', 'H', 'W', 'N')

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
        """Builds trip tour for traveller, beginning with personal info

        Inputs:
            row (int): Row number from Module 4 associated with traveller.
            personal_info (list): Personal attributes of traveller from
                Module 4.
        """
        self.row = row
        self.tour = [personal_info]

    def append_trip(self, trip):
        """Appends new trip to tour

        Inputs:
            trip (list): Trip taken by traveller in their trip tour.
        """
        self.tour.append(trip)

    def finalized_trip_tour(self, num_nodes):
        """Finalizes trip tour taken by traveller.

        NA nodes are appended to the end of the trip tour so that every
        trip tour has the same length.

        Inputs:
            num_nodes (int): Number of nodes in a trip tour.

        Returns:
            trip_tour (list): Flattened version of self.trip_tour, with
                fixed length.

        """
        empty_trip = ['NA'] * TRIP_SEGMENT_LENGTH
        for _ in range(num_nodes + 1 - len(self.tour)):
            self.tour.append(empty_trip)
        return [item for trip in self.tour for item in trip]

class TravellerCounter:
    """Counts the number of travellers residing in a FIPS code.

    This class primarily provides information for load balancing in the
    parallelized version of Module 5. Trips from Module 4 are split into
    different files and processed in parallel, each containing no more
    than the median number of travellers across all FIPS codes computed by
    this class.

    Attributes:
        fips_codes (dict): Associates a FIPS code with the number of travellers
            that originate from a FIPS code.
        traveller_count (int): Number of travellers counted for a FIPS code.
    """

    def __init__(self):
        """Initializes TravellerCounter object to begin counting"""
        self.fips_codes = dict()
        self.traveller_count = 0

    def reset_traveller_count(self):
        """Resets traveller count to 0 when changing FIPS code."""
        self.traveller_count = 0

    def update_counted_fips(self, old_fips, new_fips):
        """Updates FIPS code traveller counts when changing FIPS code

        Inputs:
            old_fips (str): Previous FIPS code that was being counted.
            new_fips (str): New FIPS code to be counted.
        """
        self.update_fips(old_fips)
        self.reset_traveller_count()
        self.update_fips(new_fips)

    def update_fips(self, fips):
        """Updates FIPS code traveller count using current traveller count.

        Inputs:
            fips (str): FIPS code to update.
        """
        if fips in self.fips_codes:
            self.fips_codes[fips] += self.traveller_count
        else:
            self.fips_codes[fips] = self.traveller_count

    def compute_median_travellers(self):
        """Computes current median number of travellers across all FIPS codes.

        Returns:
            median_trav (int): Median number of travellers across all FIPS
                codes. Refers only to those FIPS codes processed and the
                values associated with these codes at call time.
        """
        fips_trav_nums = [trav_num for trav_num in self.fips_codes.values()]
        median_trav = statistics.median(sorted(fips_trav_nums))
        return median_trav

class CSVSplitter:
    """Splits a .csv file into pieces, based on row limit and split key.

    If split key is used, then .csv file may be greater than row limit if
    a change in the criteria defined by split key is not observed. Thus,
    with a split key, the row limit is only a rough guarantee of the size
    of each split file.

    The .csv splitter is used to split the initial trip files for the
    load balancing process. If they are split at sufficient size, the
    amount of time to process each set of files should be roughly equal.
    Some files will be significantly smaller, but the worst case performance
    will take time roughly proportional to the row limit in practice.

    Attributes:
        files_generated (list): All files generated by the splitter. Each file
            is represented using the FIPS code and file piece.
        output_template (str): Template for the output file name. Each file
            is split and represented as "output_template_X.csv", where X is
            the current piece of the output file.
        output_path (str): Path for output files to be written to.
        split_key (list): Contains the columns in each row to examine for
            splitting. If any of the data in these columns change compared to
            the previous row and the row limit is exceeded, the splitter will
            split the .csv file on the current row and open a new split piece
            to write to. Otherwise, the csv splitter will wait for the data
            denoted by the split key to change.
        prev_key (set): Split key of the row previous to the current row.
        current_piece (int): Current split piece of the original file that
            is being written out.
        row_limit (int): Row limit for each split piece of the file
            to be split. Cannot be guaranteed to hold if a split_key
            is in place but in practice most files are reasonably close
            using the split keys for the model.
        current_limit (int): Translation of the row_limit with respect to
            the current piece that is being splitted. For example, if
            current_piece = 4 and row_limit = 1,000,000, then current_limit
            would be 4,000,000.
        current_out (Text IO or equivalent): Opened output file that is
            being split.
    """

    def __init__(self, row_limit=10000, output_path='.', split_key=None):
        """Initializes CSVSplitter object for use.

        Note that by default, no split key is assumed, soeach .csv file
        will be no larger than the row limit.

        Inputs:
            row_limit (int): Row limit for each split piece of the file
                to be split. Cannot be guaranteed to hold if a split_key
                is in place but in practice most files are reasonably close
                using the split keys for the model.
            output_path (str): Output path for all split output files.
            split_key (list): See class doc for info.
        """
        self.files_generated = []
        self.output_template = None
        self.output_path = output_path
        self.split_key = split_key
        self.prev_key = None
        self.current_piece = 1
        self.row_limit = row_limit
        self.current_limit = self.row_limit
        self.current_out = None

    def build_output_path(self):
        """Generates path to current split output piece."""
        output_file = self.output_template + '_' + str(self.current_piece) + '.csv'
        out_path = self.output_path + '/' + output_file
        return out_path

    def build_new_writer(self, fips):
        """Builds a new csv.writer object for a new split output.

        Input:
            fips (str): FIPS code associated with split piece.

        Returns:
            writer (csv.writer): CSV writer object for writing out the
                split piece.
        """
        if self.current_out is not None:
            self.current_out.close()
        self.current_limit = self.row_limit * self.current_piece
        current_out_path = self.build_output_path()
        self.current_out = open(current_out_path, 'w+')
        writer = writing.csv_writer(self.current_out)
        write_node_headers(writer)
        self.files_generated.append([fips, str(self.current_piece)])
        return writer

    def reset(self):
        """Resets state variables for splitting a new .csv file."""
        self.current_limit = self.row_limit
        self.current_piece = 1
        self.files_generated = []
        self.prev_key = None

    def gen_split(self, row):
        """Generates a split element using the class split key.

        Inputs:
            row (list): Current row of the .csv file to be split.

        Returns:
            split_element (set): Split element generated from current row
                of file to be split.
        """
        return {row[key] for key in self.split_key}

    def split_csv(self, file_name, output_template, fips):
        """Splits .csv file into smaller parts, based on row limit and split key.

        Inputs:
            file_name (str): File name of file to be splitted.
            output_template (str): Filename template for splitted output
                file pieces.
            fips (str): FIPS code associated with splitted file.

        """
        self.output_template = output_template
        with open(file_name) as read:
            reader = reading.csv_reader(read)
            next(reader)
            writer = self.build_new_writer(fips)
            for count, row in enumerate(reader):
                if count > self.current_limit:
                    if (self.split_key is not None
                            and self.prev_key is not None
                            and self.prev_key != self.gen_split(row)):
                        self.current_piece += 1
                        writer = self.build_new_writer(fips)
                self.prev_key = self.gen_split(row)
                writer.writerow(row)

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

def get_writer(base_path, fips, active_fips_codes, active_files, file_type):
    """Determines file to write Module 5 output based on FIPS code.

    Inputs:
        base_path (str): Partially completed path to Module 5 Output file,
            including state name.
        fips (str): fips which current row's person resides in.
        active_files (str): A list containing the FIPS codes we have active_files.
        file_type (str): The type (Sort or Pass) along with Iteration (0, 1, 2)

    Returns:
        active_fips_codes (list): List of all active_fips_codes fips codes.
        writer (csv.writer): Opened file to write Module 5 output to.
    """
    #TODO - This process might be dangerous -  should refactor
    #opening of files to ensure we can use with...open() functionality
    output_file = base_path + fips + '_' + TEMP_NAME + '_' + file_type + '_' + '1.csv'
    if fips in active_fips_codes:
        # Read with a+ as there is no chance of mixing data and we want to append
        # to what is currently there
        writer = writing.csv_writer(open(output_file, 'a+'))
    else:
        writer = writing.csv_writer(open(output_file, 'w+'))
        write_node_headers(writer)
        active_fips_codes.add(fips)
        active_files.append([fips, '1'])
    return writer

def build_initial_trip_files(file_path, base_path, start_time):
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
        active_fips_codes (list): A list containing FIPS codes seen in
            the process of constructing the trips.
    """
    trailing_fips = ''
    active_files = []
    active_fips_codes = set()
    traveller_counter = TravellerCounter()
    with open(file_path) as read:
        reader = reading.csv_reader(read)
        next(reader)
        for count, row in enumerate(reader):
            curr_fips = build_fips(row[0], row[1])
            row[0], row[1] = curr_fips[0:2], curr_fips[2:5]
            if curr_fips != trailing_fips:
                if trailing_fips != '':
                    traveller_counter.update_counted_fips(trailing_fips, curr_fips)
                trailing_fips = curr_fips
                writer = get_writer(base_path, trailing_fips, active_fips_codes, active_files, 'Pass0')
            # Get personal tours constructed for sorting
            tour = activity.Pattern(int(row[-1]), row, count)
            write_trip(tour, writer)
            traveller_counter.traveller_count += 1
            if count % 100000 == 0:
                print(str(count) + ' Residents Completed and taken this much time: '
                      + str(datetime.now()-start_time))
    traveller_counter.update_fips(curr_fips)
    median_traveller_count = traveller_counter.compute_median_travellers()
    return active_files, median_traveller_count


# TODO - the split key on this might be wrong, could be row instead of
# X Pix and Y Pix which might do a better job of balancing
def load_balance_files(output_path, state, active_fips_codes, median_row):
    """Splits input files to be roughly the same size for processing.

    Note that each file is split based on key corresponding to the X Pixel and
    Y Pixel of each node.

    Inputs:
        output_path (str): Output path for load balanced files.
        state (str): State

    """
    csv_splitter = CSVSplitter(output_path=output_path, row_limit=median_row, split_key=[8, 9])
    all_files = []
    for file_info in active_fips_codes:
        fips, piece = file_info[0], file_info[1]
        file_name = (output_path + state + '_'  + fips + '_' + TEMP_NAME
                     + '_' + 'Sort0' + '_' + piece + '.csv')
        output_name = state + '_' + fips + '_' + TEMP_NAME + '_' + 'Pass0'
        print(file_name)
        csv_splitter.split_csv(file_name, output_name, fips)
        all_files.extend(csv_splitter.files_generated)
        csv_splitter.reset()
    return all_files

def build_fips(state_code, county_code):
    """Uses state and county code of traveller to build their FIPS code.

    Inputs:
        state_code (str): State code for a traveller.
        county_code (str): County code for a traveller.

    Returns:
        fips_code (str): FIPS code corresponding to state and county code.
    """
    state_code, county_code = state_code.rjust(2, '0'), county_code.rjust(3, '0')
    fips_code = core.correct_FIPS(state_code + county_code)
    return fips_code

def write_trip(tour, writer):
    """Writes out all non-NA trips taken in a trip tour.

    Inputs:
        tour (TripTour): Trip tour for a traveller.
        writer (csv.writer): Output writer for initial trip files.
    """
    for node in tour.activities:
        if 'NA' not in node[0]:
            node[5].rjust(5, '0')
            # Does not involve trip with origin or destination that
            # hasn't already been computed
            if node[0] in VALID_PREV and node[3] in VALID_END:
                is_complete = 1
            else:
                is_complete = 0
            writer.writerow([node[0]] + [node[2]] + [node[3]]
                            + [node[4]] + [node[5]] + [node[6]]
                            + [node[7]] + [node[8]] + [node[9]]
                            + [node[10]] + [node[11]] + [node[12]]
                            + [is_complete])

def gen_file_names(file_info, iteration, process):
    """Generates input and output file names for sorting and procesing files.

    Inputs:
        file_info (str or list): Information to determine the file name.
            For the serial implementation, this is just a FIPS code. For
            the parallel implementation, this is a FIPS code and a file
            piece, represented as a list of two elements.
        iteration (int): Iteration of processing, either 1 or 2.

    Returns:
        input_fname (str): Input file name for iteration.
        output_fname (str): Output file name for iteration.
    """
    prev_iter = str(max(int(iteration)-1, 0))
    curr_iter = str(iteration)
    fips, piece = file_info[0], file_info[1]
    if process == 'sort_before':
        input_fname = (fips + '_' + TEMP_NAME + '_' + 'Pass'
                       + prev_iter + '_' + piece + '.csv')
        output_fname = (fips + '_' + TEMP_NAME + '_' + 'Sort'
                        + curr_iter + '_' + piece + '.csv')
    elif process == 'pass' or process == 'rebuild':
        input_fname = (fips + '_' + TEMP_NAME + '_' + 'Sort'
                       + curr_iter + '_' + piece + '.csv')
        output_fname = (fips + '_' + TEMP_NAME + '_' + 'Pass'
                        + curr_iter + '_' + piece + '.csv')
    elif process == 'sort_after':
        input_fname = (fips + '_' + TEMP_NAME + '_' + 'Pass'
                       + curr_iter + '_' + piece + '.csv')
        output_fname = (fips + '_' + TEMP_NAME + '_' + 'Sort'
                        + curr_iter + '_' + piece + '.csv')
    elif process == 'remove':
        input_fname = (fips + '_' + TEMP_NAME + '_' + 'Pass'
                       + prev_iter + '_' + piece + '.csv')
        output_fname = (fips + '_' + TEMP_NAME + '_' + 'Sort'
                        + prev_iter + '_' + piece + '.csv')
    elif process == 'trip_tour':
        input_fname = piece
        output_fname = fips + '_' + 'Module5NN1stRun.csv'
    return input_fname, output_fname

def sort_files_before_pass(base_path, active_files, iteration):
    """Sort Module 5 files before passing over them.

    Sorts node files by County, XCoord, YCoord, Node Successor and Node
    Type prior to passing through the file to find the other trip locations. By
    sorting by Node, then (X,Y) coords, we are able to minimize the number of
    times we need to read in new data and maximize reuse for the patronageWarehouse
    objects.

    Inputs:
        base_path (str): Partially completed path to Module 5 Output file,
            including state name.
        active_files (list): Files active_files in the process of constructing trips.
        iteration (int): Which iteration of passing we are on (1 or 2).
    """
    # If we're on iteration 1, we need to access the initial trip files, which
    # are named as 0. Otherwise, the name is based on the iteration number.
    pandas_dtype = {'Node Type': str, 'Node Predecessor': str, 'Node Successor': str,
                    'Node Name': str, 'Node County': str, 'Node Lat': str,
                    'Node Lon': str, 'Node Industry': str, 'XCoord': int,
                    'YCoord': int, 'Segment': int, 'Row': int}
    for file_info in active_files:
        input_fname, output_fname = gen_file_names(file_info, iteration, 'sort_before')
        print('Sorting', base_path + input_fname, 'before pass')
        reader = pd.read_csv(base_path + input_fname, dtype=pandas_dtype)
        reader = reader.sort_values(by=['Node County', 'XCoord', 'YCoord',
                                        'Node Successor', 'Node Type'],
                                    ascending=[True]*5)
        reader.to_csv(base_path + output_fname, index=False, na_rep='NA')

def pass_over_files(base_path, active_files, iteration, num_processors):
    """Determines destinations for which the origin is known for every trip in Module 5.

    This function sorts node files by County, XCoord, YCoord, Node Successor and Node
    Type prior to passing through the file to find the other trip locations. By
    sorting by Node, then (X,Y) coords, we are able to minimize the number of
    times we need to read in new data and maximize reuse for the patronageWarehouse
    objects.

    Inputs:
        base_path (str): Partially completed path to Module 5 Output file,
            including state name.
        active_files (list): Fips codes active_files in the process of constructing trips.
        iteration (int): Which iteration of passing we are on (1 or 2).
    """
    if num_processors == 1:
        for file_info in active_files:
            fips = file_info[0]
            input_fname, output_fname = gen_file_names(file_info, iteration, 'pass')
            input_file = base_path + input_fname
            output_file = base_path + output_fname
            print("Passing over:", fips, "on iteration:", iteration, "at", datetime.now())
            find_other_trips.get_other_trip(input_file, output_file, fips[:2], iteration)

    else:
        pool = multiprocessing.Pool(num_processors)
        tasks = []
        processing_num = 0
        for file_info in active_files:
            fips = file_info[0]
            input_fname, output_fname = gen_file_names(file_info, iteration, 'pass')
            input_file = base_path + input_fname
            output_file = base_path + output_fname
            processing_num += 1
            tasks.append((input_file, output_file, fips[:2], iteration,
                          processing_num, fips))

        results = [pool.apply_async(find_other_trips.get_other_trip, t) for t in tasks]

        for result in results:
            num, curr_fips = result.get()
            print(num, "at", curr_fips, "finished at", datetime.now())

        pool.close()
        pool.join()

    remove_prev_files(base_path, active_files, iteration)

def remove_prev_files(base_path, active_files, iteration):
    """Removes files from previous iterations that aren't needed anymore.

    Inputs:
        base_path (str): Partially completed path to Module 5 Output file,
            including state name.
        active_files (list): A list containing fips codes active_files in the process of constructing
            the trips.
        iteration (int): Which iteration of passing we are on (1 or 2).
    """
    for file_info in active_files:
        input_fname, output_fname = gen_file_names(file_info, iteration, 'remove')
        if iteration == '0' or iteration == '1':
            try:
                os.remove(base_path + input_fname)
            except FileNotFoundError:
                print(base_path + input_fname, 'does not exist')
            try:
                os.remove(base_path + output_fname)
            except FileNotFoundError:
                # Only one instance of sort type per FIPS
                # This is kinda hacky, maybe change later?
                continue
        else:
            try:
                os.remove(base_path + input_fname)
            except FileNotFoundError:
                print(base_path + input_fname, 'does not exist')
            try:
                os.remove(base_path + output_fname)
            except FileNotFoundError:
                print(base_path + output_fname, 'does not exist')

def remove_merged_files(base_path, merged_files):
    for file_info in merged_files:
        merged_file = file_info[1]
        try:
            os.remove(base_path + merged_file)
        except FileNotFoundError:
            print(base_path + merged_file, 'does not exist')

def sort_files_after_pass(base_path, active_files, iteration):
    """Sort files by row and segment after passing through files.

    Allows for quick reconstruction of trip files for the next iteration
    in rebuild_trips().

    Inputs:
        base_path (str): Partially completed path to Module 5 Output file,
            including state name.
        active_files (list): A list containing filess seen in the process of constructing
            the trips.
        iteration (int): Which iteration of passing we are on (1 or 2)
    """
    pandas_dtype = {'Node Type': str, 'Node Predecessor': str, 'Node Successor': str,
                    'Node Name': str, 'Node County': str, 'Node Lat': str,
                    'Node Lon': str, 'Node Industry': str, 'XCoord': int,
                    'YCoord': int, 'Segment': int, 'Row': int, 'IsComplete': str,
                    'D Node Name': str, 'D Node County': str, 'D Node Lat': str,
                    'D Node Lon': str, 'D Node Industry': str, 'D XCoord': str,
                    'D YCoord': str}
    for file_info in active_files:
        fips = file_info[0]
        input_fname, output_fname = gen_file_names(file_info, iteration, 'sort_after')
        print("Sorting after pass: ", fips, " on iteration: ", iteration)
        reader = pd.read_csv(base_path + input_fname, dtype=pandas_dtype)
        reader = reader.sort_values(by=['Row', 'Segment'], ascending=[True, True])
        reader.to_csv(base_path + output_fname, index=False, na_rep='NA')

def rebuild_trips(base_path, active_files, iteration):
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
        active_files (list): Contains FIPS codes seen in the process of constructing
            the trips.
        iteration (int): Which iteration of passing we are on (1 or 2).
    """
    for file_info in active_files:
        input_fname, output_fname = gen_file_names(file_info, iteration, 'rebuild')
        with open(base_path + input_fname) as read, open(base_path + output_fname, 'w+') as write:
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

def merge_files(base_path, active_files, fips_seen, curr_iter):
    merged_files = []
    pandas_dtype = {'Node Type': str, 'Node Predecessor': str, 'Node Successor': str,
                    'Node Name': str, 'Node County': str, 'Node Lat': str,
                    'Node Lon': str, 'Node Industry': str, 'XCoord': int,
                    'YCoord': int, 'Segment': int, 'Row': int}
    curr_iter = str(curr_iter)
    for fips in fips_seen:
        print('Merging FIPS code ', fips)
        output_file = fips + '_' + 'Merged' + '_' + 'Module5Temp.csv'
        with open(base_path + output_file, 'w+') as write:
            writer = writing.csv_writer(write)
            write_node_headers(writer)
            for file in active_files:
                if file[0] != fips:
                    continue
                input_file = (file[0] + '_' + TEMP_NAME + '_' + 'Pass'
                              + curr_iter + '_' + file[1] + '.csv')
                with open(base_path + input_file, 'r+') as read:
                    reader = reading.csv_reader(read)
                    next(reader)
                    for line in reader:
                        writer.writerow(line)
        reader = pd.read_csv(base_path + output_file, dtype=pandas_dtype)
        reader = reader.sort_values(by=['Row', 'Segment'], ascending=[True, True])
        reader.to_csv(base_path + output_file, index=False, na_rep='NA')
        merged_files.append([fips, output_file])
    return merged_files

def build_trip_tours(base_path, state, seen, iteration):
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
    for file_info in seen:
        fips = file_info[0]
        input_fname, output_fname = gen_file_names(file_info, iteration, 'trip_tour')
        with open(base_path + input_fname) as read, open(base_path + output_fname, 'w+') as write:
            writer = writing.csv_writer(write)
            reader = reading.csv_reader(read)
            next(reader)
            write_headers_output(writer)
            personal_info = construct_personal_info_dict(fips, state)
            num_nodes = 7
            # TODO - Better way of initializing to nothing?
            trip_tour = TripTour(-1, [])
            for count, row in enumerate(reader):

                curr_row = int(row[ROW_SEGMENT_IND])

                if curr_row != trip_tour.row:
                    if count != 0:
                        finalized_trip_tour = trip_tour.finalized_trip_tour(num_nodes)
                        writer.writerow(finalized_trip_tour)
                    trip_tour = TripTour(curr_row, personal_info[curr_row])
                trip_tour.append_trip(row[:TRIP_SEGMENT_LENGTH])

            finalized_trip_tour = trip_tour.finalized_trip_tour(num_nodes)
            writer.writerow(finalized_trip_tour)

def find_fips(active_files):
    fips_seen = set()
    for file in active_files:
        if file[0] not in fips_seen:
            fips_seen.add(file[0])
    return fips_seen

def main(state, num_processors=1):
    """Builds all trip tours for a U.S. State using Module 4 Output.

    Inputs:
        state (str): Module 4 Output state to process.
        num_processors (int): Number of processors to use.
    """
    input_path = paths.OUTPUT + 'Module4/' + state + 'Module4NN2ndRun.csv'
    output_path = paths.OUTPUT + 'Module5/'
    base_path = output_path + state + '_'
    start_time = datetime.now()
    print(state + " started at: " + str(start_time))
    if num_processors > 1:
        active_files, median_trip = build_initial_trip_files(input_path, base_path, start_time)
        sort_files_before_pass(base_path, active_files, '0')
        active_files = load_balance_files(output_path, state, active_files, median_trip)
    else:
        active_files = build_initial_trip_files(input_path, base_path, start_time)[0]

    for i in range(1, 3):
        current = str(i)
        print('Began sorting before passing on iteration:',
              current, 'at', str(datetime.now()-start_time))
        sort_files_before_pass(base_path, active_files, current)
        print('Finished sorting before passing on iteration:',
              current, 'at', str(datetime.now()-start_time))
        pass_over_files(base_path, active_files, current, num_processors)
        print('Finished passing over files on iteration:', current,
              'at', str(datetime.now()-start_time))
        sort_files_after_pass(base_path, active_files, current)
        print('Finished sorting files after passing on iteration:',
              current, 'at', str(datetime.now()-start_time))
        rebuild_trips(base_path, active_files, current)

    fips_seen = find_fips(active_files)
    merged_files = merge_files(base_path, active_files, fips_seen, current)
    build_trip_tours(base_path, state, merged_files, current)
    remove_prev_files(base_path, active_files, '3')
    remove_merged_files(base_path, merged_files)

    print(state + " took: " + str(datetime.now() - start_time))
