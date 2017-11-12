import csv
import activityPattern
import findOtherTrips
import classDumpModule5
from datetime import datetime
import pandas as pd
import os

'----------PATH DEFINITIONS---------------------'
#rootDrive = 'E'
rootFilePath = 'D:/Data/Output/'
inputFileNameSuffix = 'Module4NN2ndRun.csv'
tempSuffix = 'Module5Temp.csv'
outputFileNameSuffix = 'Module5NN1stRun.csv'

#dataDrive = 'E'
dataRoot = 'D:/Data/'
'-----------------------------------------------'


def writeHeaders3(pW):
    pW.writerow(['Node Type'] + ['Node Predecessor'] + ['Node Successor'] + ['Node Name']
                + ['Node County'] + ['Node Lat'] + ['Node Lon'] + ['Node Industry']
                + ['XCoord'] + ['YCoord'] + ['Segment'] + ['Row'] + ['IsComplete'] + ['D Node Name']
                + ['D Node County'] + ['D Node Lat'] + ['D Node Lon'] + ['D Node Industry']
                + ['D XCoord'] + ['D YCoord'])

def writeHeaders2(pW):
    pW.writerow(['Node Type'] + ['Node Predecessor'] + ['Node Successor'] + ['Node Name']
                + ['Node County'] + ['Node Lat'] + ['Node Lon'] + ['Node Industry']
                + ['XCoord'] + ['YCoord'] + ['Segment'] + ['Row'] + ['IsComplete'])
                
def writeHeaders1(pW):
    pW.writerow(['Residence State'] + ['County Code'] + ['Tract Code'] + ['Block Code'] + ['HH ID'] 
                + ['Person ID Number'] + ['Activity Pattern']
                + ['Node 1 Type'] + ['Node 1 Predecessor'] + ['Node 1 Successor'] + ['Node 1 Name'] + ['Node 1 County'] + ['Node 1 Lat'] + ['Node 1 Lon'] + ['Node 1 Industry']
                + ['Node 2 Type'] + ['Node 2 Predecessor'] + ['Node 2 Successor'] + ['Node 2 Name'] + ['Node 2 County'] + ['Node 2 Lat'] + ['Node 2 Lon'] + ['Node 2 Industry']
                + ['Node 3 Type'] + ['Node 3 Predecessor'] + ['Node 3 Successor'] + ['Node 3 Name'] + ['Node 3 County'] + ['Node 3 Lat'] + ['Node 3 Lon'] + ['Node 3 Industry']
                + ['Node 4 Type'] + ['Node 4 Predecessor'] + ['Node 4 Successor'] + ['Node 4 Name'] + ['Node 4 County'] + ['Node 4 Lat'] + ['Node 4 Lon'] + ['Node 4 Industry']
                + ['Node 5 Type'] + ['Node 5 Predecessor'] + ['Node 5 Successor'] + ['Node 5 Name'] + ['Node 5 County'] + ['Node 5 Lat'] + ['Node 5 Lon'] + ['Node 5 Industry']
                + ['Node 6 Type'] + ['Node 6 Predecessor'] + ['Node 6 Successor'] + ['Node 6 Name'] + ['Node 6 County'] + ['Node 6 Lat'] + ['Node 6 Lon'] + ['Node 6 Industry']
                + ['Node 7 Type'] + ['Node 7 Predecessor'] + ['Node 7 Successor'] + ['Node 7 Name'] + ['Node 7 County'] + ['Node 7 Lat'] + ['Node 7 Lon'] + ['Node 7 Industry'])

def correct_FIPS(state, county):
    """Corrects issues with FIPS codes.
    
    Left-padsFIPS when zeros are missing and adjusts for issues with
    2010 Census vs. Data with Hawaii FIPS 15009. Note that state and county
    merged into a single string is a FIPS code.
    
    Args:    
    state (str): A 2 digit state code, the first 2 digits of a FIPS code.
    county (str): A 3 digit county code, the last 3 digits of a FIPS code.
    
    Returns:
    state (str): Corrected 2 digit state code.
    county (str): Corrected 3 digit county code.

    """
    # Deal with 15005 vs 15009 FIPS Code
    if state == '15':
        if county == '5':
            county = '9'
    # Ensure State FIPS are left padded
    if len(state) == 1:
        state = '0' + state
    # Ensure County FIPS are left padded
    if len(county) == 1:
        county = '00' + county
    elif len(county) == 2:
        county = '0' + county
    return state, county

def get_file_to_write_to(output_path, state, FIPS, seen):
    """Determines file to write Module 5 output based on FIPS code.
    
    Args:    
    output_path (str): Path to Module 5 output directory.
    state (str): State which current row's person resides in.
    FIPS (str): FIPS which current row's person resides in.
    seen (str): A list containing the FIPS codes we have seen.
    
    Returns:
    seen (list): List of all seen FIPS codes.
    person_writer (csv.writer): Opened file to write Module 5 output to.
    """
    # If we have seen this code before, it's an old file
    if FIPS in seen:
        # Read with a+ as there is no chance of mixing data and we want to append
        # to what is currently there
        out = open(output_path + state + '_' + FIPS + '_' + 'Pass0' + '_' + tempSuffix, 'a+', encoding='utf8')
        person_writer = csv.writer(out, delimiter=',', lineterminator='\n')
    else:
        # Read with w+ to ensure old data doesn't mix with new data
        out = open(output_path + state + '_' + FIPS + '_' + 'Pass0' + '_' + tempSuffix, 'w+', encoding='utf8')
        person_writer = csv.writer(out, delimiter=',', lineterminator='\n')
        # Give the file a header
        writeHeaders2(person_writer)
        # Add it to list  of seen so we don't write headers again
        seen.append(FIPS)
    return seen, person_writer

def construct_initial_trip_files(fileLocation, output_path, state, startTime):
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
    startTime (datetime): Module 5 start time.
    
    Returns:
    seen (list): A list containing FIPS codes seen in the process of constructing
    the trips.
    """
    f = open(fileLocation, 'r')
    person_reader = csv.reader(f, delimiter=',')
    trailingFIPS = ''
    seen = []
    count = -1
    validPrev = ['S','H','W']
    validEnd = ['S','H','W','N']
    for person in person_reader:
        if count == -1: 
            count+=1 
            continue      
        count+=1
        
        # Correct FIPS Codes
        person[0], person[1] = correct_FIPS(person[0],person[1])
        newCounty = person[0] + person[1]
        # Change output file if FIPS changes
        if newCounty != trailingFIPS:
            trailingFIPS = newCounty
            seen, person_writer = get_file_to_write_to(output_path, state, trailingFIPS, seen)
        # Get personal tours constructed for sorting
        personalTour = activityPattern.activityPattern(int(person[len(person) - 1]), person, count)
        for node in personalTour.activities:
            # Write any node that is not an NA node
            if 'NA' not in node[0]:
                isComplete = 0
                if len(node[5]) == 4:
                    node[5] = '0' + node[5]
                # No other trips needed, so we have everything we need to write this trip down
                if node[0] in validPrev and node[3] in validEnd:
                    isComplete = 1
                person_writer.writerow([node[0]] + [node[2]] + [node[3]] + 
                                  [node[4]] + [node[5]] + [node[6]] + 
                                  [node[7]] + [node[8]] + [node[9]] +
                                  [node[10]] + [node[11]] + [node[12]] + [isComplete])
        if count % 100000 == 0:
            print(str(count) + ' Residents Completed and taken this much time: ' + str(datetime.now()-startTime))

    f.close()
    return seen

def sort_files_before_pass(output_path, state, seen, iteration):
    """Sort Module 5 files before passing over them.

    Sorts node files by County, XCoord, YCoord, Node Successor and Node
    Type prior to passing through the file to find the other trip locations. By
    sorting by Node, then (X,Y) coords, we are able to minimize the number of
    times we need to read in new data and maximize reuse for the patronageWarehouse
    objects.
    
    Args:   
    output_path: Path to files holding node information
    state: State which current row's person resides in
    seen: A list containing FIPS codes seen in the process of constructing
    the trips.
    iteration: Which iteration of passing we are on (1 or 2)
    """
    # If we're on iteration 1, we need to access the initial trip files, which
    # are named as 0. Otherwise, the name is based on the iteration number.
    past = iteration
    if iteration == '1':
        past = str(int(iteration)-1)
    for FIPS in seen:
        print("Sorting Before Pass: ", FIPS, " on Iteration: ", iteration)
        reader = pd.read_csv(output_path + state + '_' + FIPS + '_' + 'Pass' + past + '_' + tempSuffix,
                 dtype = {'Node Type': str, 'Node Predecessor': str, 'Node Successor': str,
                          'Node Name': str, 'Node County': str, 'Node Lat': str, 'Node Lon': str, 
                          'Node Industry': str, 'XCoord': int, 'YCoord': int, 'Segment': int, 'Row': int})
        reader = reader.sort_values(by=['Node County','XCoord','YCoord','Node Successor','Node Type'], ascending=[True,True,True,True,True])
        reader.to_csv(output_path + state + '_' + FIPS + '_' + 'Sort' + iteration + '_' + tempSuffix, index=False, na_rep = 'NA')

def pass_over_files(output_path, state, seen, iteration, countyNameData):
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
    seen: A list containing FIPS codes seen in the process of constructing
    the trips.
    iteration: Which iteration of passing we are on (1 or 2)
    
    Returns:
    A sorted file as described above.
    """
    for FIPS in seen:
        print("Passing over: ", FIPS, " on Iteration: ", iteration, "at ", datetime.now())
        f = open(output_path + state + '_' + FIPS + '_' + 'Sort' + iteration + '_' + tempSuffix, 'r+')
        person_reader = csv.reader(f, delimiter = ',')
        o = open(output_path + state + '_' + FIPS + '_' + 'Pass' + iteration + '_' + tempSuffix, 'w+', newline = '')
        person_writer = csv.writer(o, delimiter = ',')
        writeHeaders3(person_writer)
        findOtherTrips.get_other_trip(person_reader,person_writer, countyNameData, FIPS[:2], iteration)
        f.close()
        o.close()

def clean_files(output_path, state, seen, iteration):
    """ 
    Summary:
    This cleans out files from previous iterations that are no longer needed.
    
    Args:   
    output_path: Path to files holding node information
    state: State which current row's person resides in
    seen: A list containing FIPS codes seen in the process of constructing
    the trips.
    iteration: Which iteration of passing we are on (1 or 2)
    
    Returns:
    Removes files as shown below.
    """
    past = str(int(iteration)-1)
    for FIPS in seen:
        if iteration == '4':
            try:
                os.remove(output_path + state + '_' + FIPS + '_' + 'Pass' + past + '_' + tempSuffix)
            except:
                print('Unable to remove PASS type folder for FIPS: ', FIPS)
        else:
            try:
                os.remove(output_path + state + '_' + FIPS + '_' + 'Sort' + iteration + '_' + tempSuffix)
            except:
                print('Unable to remove SORT type folder for FIPS: ', FIPS)
            try:
                os.remove(output_path + state + '_' + FIPS + '_' + 'Pass' + past + '_' + tempSuffix)
            except:
                print('Unable to remove PASS type folder for FIPS: ', FIPS)

def sort_files_after_pass(output_path, state, seen, iteration):
    """ 
    Summary:
    This function sorts node files by Row and Segment after passing through the
    file to find the other type node locations. This allows us to quickly reconstruct
    trip files for the next iteration/final output in rebuild_trips().
    
    Args:   
    output_path: Path to files holding node information
    state: State which current row's person resides in
    seen: A list containing FIPS codes seen in the process of constructing
    the trips.
    iteration: Which iteration of passing we are on (1 or 2)
    
    Returns:
    A sorted file as described above.
    """
    future = str(int(iteration)+1)
    for FIPS in seen:
        print("Sorting After Pass: ", FIPS, " on Iteration: ", iteration)
        reader = pd.read_csv(output_path + state + '_' + FIPS + '_' + 'Pass' + iteration + '_' + tempSuffix,
                 dtype = {'Node Type': str, 'Node Predecessor': str, 'Node Successor': str,
                          'Node Name': str, 'Node County': str, 'Node Lat': str, 'Node Lon': str, 
                          'Node Industry': str, 'XCoord': int, 'YCoord': int, 'Segment': int, 'Row': int,
                          'IsComplete': str, 'D Node Name': str, 'D Node County': str, 'D Node Lat': str, 'D Node Lon': str, 
                          'D Node Industry': str, 'D XCoord': str, 'D YCoord': str})
        reader = reader.sort_values(by=['Row','Segment'], ascending=[True,True])
        reader.to_csv(output_path + state + '_' + FIPS + '_' + 'Sort' + future + '_' + tempSuffix, index=False, na_rep = 'NA')
    clean_files(output_path, state, seen, iteration)

def rebuild_trips(output_path, state, seen, iteration):    
    """ 
    Summary:
    This function rebuilds the trip files by taking nodes sorted by Row and Segment
    to fill in O destination nodes. get_other_trips() writes out the destination
    node information, if found, in the 7 columns following the initial isComplete
    boolean column from the initial trip file. The data following this column is
    taken and filled in for subsequent nodes that were previously marked as NA
    due to issues with a lack of O destination node or uncertainty on the O 
    origin node.
    
    Args:   
    output_path: Path to files holding node information
    state: State which current row's person resides in
    seen: A list containing FIPS codes seen in the process of constructing
    the trips.
    iteration: Which iteration of passing we are on (1 or 2)
    
    Returns:
    A file with newly gained information on the other type node destinations 
    now filled in.
    """
    for FIPS in seen:
        f = open(output_path + state + '_' + FIPS + '_' + 'Sort' + iteration + '_' + tempSuffix, 'r+')
        person_reader = csv.reader(f, delimiter = ',')
        o = open(output_path + state + '_' + FIPS + '_' + 'Pass' + iteration + '_' + tempSuffix, 'w+', newline = '')
        person_writer = csv.writer(o, delimiter = ',')
        writeHeaders2(person_writer)
        
        count = -1
        # Use trailing to get hold geographic attributes from previous node
        trailing = ''
        
        for line in person_reader:
            if count == -1:
                count +=1
                continue
            count +=1
            # If it's incomplete, is an other-type node and isn't preceded
            # by an other type trip
            if line[12] == '0' and line[0] == 'O' and line[1] != 'O':
                line[3:10] = trailing
                if line[2] != 'O':
                    line[12] = '1'
            trailing = line[13:]
            person_writer.writerow(line[:13])
            
        f.close()
        o.close()    

def construct_row_personal_info_dict(FIPS, state):
    fileLocation = rootFilePath + 'Module4/' + state + inputFileNameSuffix
    f = open(fileLocation, 'r')
    person_reader = csv.reader(f, delimiter=',')
    personDict = dict()
    count = -1
    for line in person_reader:
        if count == -1:
            count +=1
            continue
        count += 1
        state, county = correct_FIPS(line[0],line[1])
        if FIPS == state+county:
            personDict[count] = line[:5] + [line[8]] + [line[11]]
    f.close()
    return personDict

def rebuild_module_5_file(output_path, state, seen):    

    for FIPS in seen:
        o = open(output_path + state + '_' + FIPS + '_' + outputFileNameSuffix, 'w+', newline = '')
        person_writer = csv.writer(o, delimiter = ',')
        f = open(output_path + state + '_' + FIPS + '_' + 'Pass3' + '_' + tempSuffix, 'r+')
        person_reader = csv.reader(f, delimiter = ',')
        writeHeaders1(person_writer)
        rowDict = construct_row_personal_info_dict(FIPS, state)
        count = -1
        # Use trailing to get hold geographic attributes from previous node
        trailing = []
        currRow = ''
        nullNode = ['NA'] * 8
        numNodes = 7
        
        for line in person_reader:
            if count == -1:
                count +=1
                continue
            count +=1
            
            if line[11] != currRow:
                for i in range(numNodes+1 - len(trailing)):
                    trailing.append(nullNode)
                finalRow = [item for sublist in trailing for item in sublist]
                if count != 1:
                    person_writer.writerow(finalRow)
                currRow = line[11]
                trailing = [rowDict[int(currRow)]]
                
            trailing.append(line[:8])
            
        f.close()
        o.close()

def executive(state):
    # Module 4 Input Path
    fileLocation = rootFilePath + 'Module4/' + state + inputFileNameSuffix
    # Module 5 Output Path 
    output_path = rootFilePath + 'Module5/'

    startTime = datetime.now()
    print(state + " started at: " + str(startTime))
    
    seen = construct_initial_trip_files(fileLocation, output_path, state, startTime)
    
    countyNameData = classDumpModule5.read_counties()
    
    for i in range(1,3):
        
        current = str(i)
        future = str(i+1)
        
        print('Began sorting before passing on iteration: ', str(i), ' at', str(datetime.now()-startTime))
        sort_files_before_pass(output_path, state, seen, current)
        print('Finished sorting before passing on iteration: ', str(i), ' at', str(datetime.now()-startTime))        
        pass_over_files(output_path, state, seen, current, countyNameData)
        print('Finished passing over files on iteration: ', str(i), ' at', str(datetime.now()-startTime))    
        sort_files_after_pass(output_path, state, seen, current)
        print('Finished sorting files after passing on iteration: ', str(i), ' at', str(datetime.now()-startTime))
        rebuild_trips(output_path, state, seen, future)
        print('Finished iteration: ', str(i))
          
    clean_files(output_path, state, seen, '3')
    rebuild_module_5_file(output_path, state, seen)
    clean_files(output_path, state, seen, '4')
    
    print(state + " took: " + str(datetime.now() - startTime))
    
import sys
exec("executive(sys.argv[1])")
#exec('module5runner()')   